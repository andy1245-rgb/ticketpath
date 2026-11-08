"""The off-chain scoring rule for a forecast logged on chain.

A forecast commits a band and `scoring_rule_hash` before the outcome is known. This module is
the rule that hash names: the Winkler interval score, scaled to integer micro-lamports. The
same number is what `ScoreForecast` carries, and the score account is create-once, so a rule
cannot be swapped after the realised price is seen.

Standard library only, no network: `hashlib` for the rule hash, and integer arithmetic for
the score. No float is ever used in the calculation, because a score that differs by one
micro-lamport between two machines is not a score.

The choice of alpha
-------------------
`alpha = 1/5`, an 80% central interval, is the default and the only value the on-chain rule
is specified with. It is stated here rather than left to a caller: a forecast is a statement
about a range a model believes with 80% confidence, which is wide enough to be honest about a
cold ticket market and narrow enough that a useless 0-to-infinity band is penalised for its
width. Alpha is a parameter so a test can show the rule is not accidentally fixed, but a
forecast whose committed `scoring_rule_hash` is `SCORING_RULE_HASH` is scored at 1/5.

The score
---------
For realised `y`, band `[l, u]`, and the closed interval (inclusive at both ends):

    S = (u - l)
        + (2 / alpha) * (l - y)  if y < l
        + (2 / alpha) * (y - u)  if y > u

`interval_score_micro` is `floor(S * 1_000_000)`, an integer in micro-lamports. The penalty
is zero at either bound, so a covered outcome scores exactly the width of the band. The
score is not a probability and is not bounded: a forecast that misses by a lot is meant to
score badly, and a narrow band that misses scores worse than a wide one that covers.

A refusal is not a score
------------------------
The engine refuses to price some events (no resale history, no band). A refusal has no
interval to score, so `scored_forecast` raises `ForecastRefused` instead of returning a
number. It never returns an infinite or maximum score for a missing forecast: that would
turn "we did not know" into the worst forecast, which is a different and false claim.

The field's domain, and what the chain cannot check
---------------------------------------------------
`interval_score_micro` is stored in a `u64` on chain and this rule multiplies lamports by
1,000,000, so two limits follow from the layout:

* the band's width alone must fit: `(high - low) <= MAX_BAND_WIDTH_LAMPORTS`, which is
  `u64::MAX // 1_000_000` = 18,446,744,073,709 lamports, about 18,446.7 SOL. `LogForecast`
  refuses a wider band with `6031` on chain, so a forecast that can be logged can always be
translated into a score instruction.
* the score itself must fit: a miss large enough that `width + 10 * miss` exceeds
  `18,446,744,073,709` lamports (about 1,844 SOL of miss at `alpha = 1/5`) gives a number the
  field cannot hold. `scored_forecast` raises `ForecastRefused` there rather than handing a
  caller a `ValueError` from the wire packer: there is no on-chain number that means it.

The chain checks one side of the number and only one. `ScoreForecast` recomputes `covered`
from the forecast's ends and refuses a score below the band's width (`6030`), which no honest
score can be. It does **not** recompute the penalty, because it has no rule text to run, so an
**overstated** error is stored on the authority's word. This module is the rule that hash
names; a consumer that wants the true number runs it, and the account records what was
claimed.
"""

from __future__ import annotations

import hashlib
import math

__all__ = [
    "DEFAULT_ALPHA",
    "ForecastRefused",
    "MAX_BAND_WIDTH_LAMPORTS",
    "MAX_SCORE_MICRO",
    "SCORE_MICRO_SCALE",
    "SCORING_RULE",
    "SCORING_RULE_HASH",
    "interval_score_micro",
    "scored_forecast",
]

#: The one canonical text the hash commits. Changing a character changes the rule.
SCORING_RULE = (
    "ticketpath-forecast-score-v1: Winkler interval score, alpha=1/5 (80% central "
    "interval); y=realised lamports, [l,u]=forecast band lamports; "
    "S=(u-l)+(2/alpha)*(l-y)*1{y<l}+(2/alpha)*(y-u)*1{y>u}; "
    "interval_score_micro=floor(S*1_000_000), stored as u64 micro-lamports; "
    "covered=1 iff l<=y<=u"
)

#: `sha256` of `SCORING_RULE.encode("utf-8")`. This is the value `LogForecast` commits.
SCORING_RULE_HASH = hashlib.sha256(SCORING_RULE.encode("utf-8")).digest()

#: An 80% central interval. See the module docstring for why this is the fixed choice.
#: It is a decimal, and `_alpha_ratio` parses it exactly as 1/5 rather than as a binary float.
DEFAULT_ALPHA = 0.2

_SCALE = 1_000_000

#: The largest value the on-chain `interval_score_micro` field can hold.
MAX_SCORE_MICRO = 2**64 - 1

#: The widest band whose width term (`width * _SCALE`) still fits that field. 18,446.7 SOL.
#: `state.rs::MAX_BAND_WIDTH_LAMPORTS` is the same number and `LogForecast` enforces it (6031).
MAX_BAND_WIDTH_LAMPORTS = MAX_SCORE_MICRO // _SCALE

#: The rule's scale, stated for callers that check the two limits themselves.
SCORE_MICRO_SCALE = _SCALE


class ForecastRefused(ValueError):
    """The forecast cannot be scored. Reported as a refusal, never as a number.

    `reason` is a short sentence suitable for a console line. The exception is a
    `ValueError` so a caller that already refuses malformed rows catches it, but the message
    distinguishes "we refused to price this" from "the bytes were wrong".
    """

    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def _alpha_ratio(alpha) -> tuple[int, int]:
    """Alpha as an exact `(numerator, denominator)`.

    `0.2` is parsed from its decimal text as 1/5, not from the binary float, so the same
    alpha a caller writes is the same alpha this function computes with. A `(num, den)`
    tuple and an `"a/b"` string are accepted as the exact forms; an int is `n/1`.
    """
    if isinstance(alpha, bool):
        raise TypeError("alpha must be a number, not a bool")
    if isinstance(alpha, tuple) and len(alpha) == 2:
        numerator, denominator = alpha
        if not all(isinstance(part, int) and not isinstance(part, bool) for part in alpha):
            raise TypeError("alpha: a tuple must be two ints")
    elif isinstance(alpha, int):
        numerator, denominator = alpha, 1
    else:
        text = alpha if isinstance(alpha, str) else str(alpha)
        text = text.strip()
        if "/" in text:
            left, _, right = text.partition("/")
            try:
                numerator, denominator = int(left), int(right)
            except ValueError as exc:
                raise ValueError(f"alpha {alpha!r} is not a fraction") from exc
        else:
            sign = -1 if text.startswith("-") else 1
            if text[:1] in "+-":
                text = text[1:]
            whole, _, fraction = text.partition(".")
            if not whole and not fraction:
                raise ValueError(f"alpha {alpha!r} is not a number")
            digits = (whole or "0") + fraction
            try:
                numerator = sign * int(digits)
            except ValueError as exc:
                raise ValueError(f"alpha {alpha!r} is not a number") from exc
            denominator = pow(10, len(fraction))

    if denominator == 0:
        raise ValueError("alpha's denominator cannot be zero")
    if not 0 < numerator < denominator:
        raise ValueError(f"alpha must be between 0 and 1 (exclusive), got {alpha!r}")
    divisor = math.gcd(numerator, denominator)
    return numerator // divisor, denominator // divisor


def _require_lamports(value, what: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{what}: expected an int number of lamports, got {type(value).__name__}")
    if value < 0:
        raise ValueError(f"{what}: lamports cannot be negative, got {value}")
    return value


def interval_score_micro(realised: int, low: int, high: int, alpha=DEFAULT_ALPHA) -> int:
    """The Winkler interval score of `[low, high]` at `realised`, in micro-lamports.

    The interval is closed: `realised == low` and `realised == high` both have zero penalty
    and score exactly `(high - low) * 1_000_000`. `low > high` is refused here rather than
    scored: an inverted band is not a forecast, and there is no finite number that means it.

    The result is an integer, floored once at the end. With `alpha = 1/5` the factor
    `2/alpha` is exactly 10 and no rounding occurs at all; a different alpha still uses
    exact rational arithmetic.
    """
    realised = _require_lamports(realised, "realised")
    low = _require_lamports(low, "low")
    high = _require_lamports(high, "high")
    if low > high:
        raise ValueError(f"low {low} is above high {high}: an inverted band is not a forecast")

    numerator, denominator = _alpha_ratio(alpha)
    penalty = (low - realised) if realised < low else max(realised - high, 0)
    # S = (high-low) + (2/alpha)*penalty. With alpha = n/d, that is
    # ((high-low)*n + 2*d*penalty) / n. Multiply by 1e6 and floor once.
    scaled_numerator = ((high - low) * numerator + 2 * denominator * penalty) * _SCALE
    return scaled_numerator // numerator


def _band_from(forecast) -> tuple[int, int]:
    """The two ends of a forecast, or a refusal. Never invents a band from a missing one."""
    if forecast is None:
        raise ForecastRefused("no forecast exists for this as-of; nothing can be scored")

    if isinstance(forecast, dict):
        low = forecast.get("low")
        high = forecast.get("high")
        refused = forecast.get("refused", 0)
    else:
        low = getattr(forecast, "low", None)
        high = getattr(forecast, "high", None)
        refused = getattr(forecast, "refused", 0)

    if refused:
        raise ForecastRefused("the forecast refused to price the event; a refusal is not a score")
    if low is None or high is None:
        raise ForecastRefused("the forecast has no band; a refusal is not a score")
    return _require_lamports(low, "low"), _require_lamports(high, "high")


def scored_forecast(realised_lamports: int, forecast, *, alpha=DEFAULT_ALPHA) -> dict:
    """The `ScoreForecast` arguments for `forecast`, plus whether the band covered.

    `forecast` is a `v2.Forecast`, a `v2.Band`, or any mapping with `low`/`high` (and an
    optional `refused`). `None`, a missing band, or a refusal flag raises `ForecastRefused`,
    which is the caller's signal to report a refusal rather than to write a score.

    The returned dict is exactly what the instruction takes, plus `covered`:

        {"realised_lamports": ..., "interval_score_micro": ..., "covered": bool}

    `covered` is recomputed on chain from the forecast's own ends, so it is a cross-check
    here, not an input. A score that does not fit the on-chain `u64` (a band wider than
    `MAX_BAND_WIDTH_LAMPORTS`, or a miss so large that the penalty term overflows the field) is
    a `ForecastRefused` and not a number: the instruction has no field for it, and the honest
    report is that this forecast cannot be scored on chain rather than a wrapped value.
    """
    realised = _require_lamports(realised_lamports, "realised_lamports")
    low, high = _band_from(forecast)
    if high - low > MAX_BAND_WIDTH_LAMPORTS:
        raise ForecastRefused(
            "the band is wider than the score field can hold; LogForecast refuses it 6031 on "
            f"chain (at most {MAX_BAND_WIDTH_LAMPORTS} lamports wide)"
        )
    score = interval_score_micro(realised, low, high, alpha=alpha)
    if score > MAX_SCORE_MICRO:
        raise ForecastRefused(
            f"the interval score {score} does not fit the u64 field ({MAX_SCORE_MICRO}); "
            "the miss is too large for this rule to be recorded on chain"
        )
    return {
        "realised_lamports": realised,
        "interval_score_micro": score,
        "covered": low <= realised <= high,
    }

"""Small formatting helpers for the console: escape, badge, number, money, percent.

One rule: a number reaches the page only through `num()`, which puts the badge in the
same text run as the value, first. That is what makes "every number carries its badge"
checkable by stripping tags and reading text, and what makes it survive a screenshot, a
projector and a colour-blind judge.

A sentence from `labels` may contain counts -- A19 says "8 of 9 recorded resales (88.9%)"
and A1 says "records 9 sales" -- and each of those counts is rendered by this function and
substituted into the sentence as its own span, so the badge travels with the number rather
than with the panel. `blocks._sentence` does the substitution; a sentence whose count is a
word (`one sale`, `no sale`) needs none.
"""

from __future__ import annotations

from html import escape

from ticketpath.core import labels


def esc(value: object) -> str:
    return escape(str(value), quote=True)


def badge(name: str) -> str:
    return f'<span class="badge">{esc(labels.badge(name))}</span>'


# What a number carries when no badge would be true of it. A badge names where a number came
# from and how much assurance it carries; a field the artefact's quote hash does not cover has
# no assurance to badge, so the page prints the writer's own status instead (feature 2, the
# forged-signature finding). The words are the page's, not a ninth badge: the badge vocabulary
# is the frontend legend's, and a new one there would be a claim the frontend does not gloss.
STATED = "the file states"


def num(wrapper: dict | None, kind: str = "count", *, trim: bool = True, mark: str | None = None) -> str:
    """Render a payload number wrapper as `<span class="n">[BADGE] value unit</span>`.

    `trim` is the one place a precision is chosen per call site: two parts of the same
    measure (the median and the mean markup, say) are printed through the same trim so the
    row cannot read "1.2%" beside "3%". The value is never touched, only its digits.

    `mark` replaces the badge with those words. It exists for the one case where the wrapper's
    badge would be a provenance claim the file cannot back -- a value the quote hash does not
    cover -- so the number keeps its formatting and loses the claim (`STATED`).
    """
    if wrapper is None:
        return '<span class="n">[REFUSED] not stated</span>'
    value = wrapper.get("value")
    name = wrapper.get("badge")
    if value is None:
        return '<span class="n">[REFUSED] not stated</span>'
    if kind == "money":
        text = _sol(value)
    elif kind == "lamports":
        # An exact integer sum of lamports, with separators, for a sentence a reader is
        # meant to check by eye. The same digits as `lamports_text`, carrying its badge.
        text = f"{int(round(value)):,}"
    elif kind == "integer":
        # An exact integer that is not money: a basis-point policy, with its own unit, so the
        # file's "2500 bps" and the page's "1500 bps" can be read side by side.
        text = f"{int(round(value)):,}"
    elif kind == "percent":
        text = _pct(value)
    elif kind == "bps":
        text = _bps(value, trim)
    elif kind == "rate":
        text = f"{value:.1f}"
    elif kind == "log":
        text = f"{value:+.4f}" if isinstance(value, float) else str(value)
    elif kind == "float":
        text = f"{value:.1f}" if isinstance(value, float) else str(value)
    else:
        text = str(int(round(value))) if isinstance(value, float) else str(value)
    unit = wrapper.get("unit")
    suffix = ""
    if kind == "money":
        suffix = " SOL"
    elif kind == "lamports":
        suffix = " lamports"
    elif kind == "rate":
        suffix = " per 1,000 ticket-days"
    elif unit and kind in ("float", "count", "integer"):
        suffix = f" {unit}"
    prefix = esc(mark) if mark is not None else esc(labels.badge(name))
    return f'<span class="n">{prefix} {esc(text)}{esc(suffix)}</span>'


def _sol(lamports: float) -> str:
    value = float(lamports) / 1e9
    if abs(value) >= 0.01:
        return f"{value:.2f}"
    if value == 0:
        return "0.00"
    return f"{value:.6f}"


def _pct(share: float) -> str:
    return f"{100.0 * float(share):.1f}%"


def _bps(bps: float, trim: bool = True) -> str:
    value = float(bps) / 100.0
    text = f"{value:.1f}"
    if trim and text.endswith(".0"):
        text = text[:-2]
    return f"{text}%"


def money(wrapper: dict | None) -> str:
    return num(wrapper, "money")


def money_exact(wrapper: dict | None) -> str:
    """SOL at its exact value, for a band end that is a ceiling rather than a width.

    Two decimals round 1.725 up to 1.73, which reads as a band whose top is above the
    ceiling it was just cut at. The same rule the recommendation band already follows: a
    top that is a limit is printed at the limit's own digits, not at a rounding of them.
    """
    if wrapper is None or wrapper.get("value") is None:
        return '<span class="n">[REFUSED] not stated</span>'
    return (
        f'<span class="n">{esc(labels.badge(wrapper["badge"]))} '
        f'{esc(sol_exact(wrapper["value"]))} SOL</span>'
    )


def percent(wrapper: dict | None) -> str:
    return num(wrapper, "percent")


def bps_text(wrapper: dict | None, *, trim: bool = True) -> str:
    return num(wrapper, "bps", trim=trim)


def plural(count, singular: str, many: str | None = None) -> str:
    """The noun a count takes in the page's own prose: one ticket, no tickets, two tickets.

    A count of one reads as singular; anything else, including zero and an absent count,
    reads as plural. Registry sentences carry their own singular variants, because their
    wording is fixed; this helper is for the strip labels the page writes itself.
    """
    return singular if count == 1 else (many or singular + "s")


def value_of(wrapper: dict | None):
    """The raw value behind a payload number, for a sentence's fields."""
    if isinstance(wrapper, dict) and "value" in wrapper:
        return wrapper["value"]
    return None


def sol_text(lamports: int | float | None) -> str:
    """A number for inside a registry sentence. The sentence's block carries the badge."""
    if lamports is None:
        return "—"
    return _sol(lamports)


def sol_exact(lamports: int | float | None) -> str:
    """SOL at its exact value, for a bound or an equality.

    `_sol` rounds to two decimals, which turns 1,125,000,000 lamports into `1.12` and makes
    `1.12 = 0.90 x 1.25` false. A floor or an equality may not be rounded, so this trims
    trailing zeros from the exact decimal instead: 1.125 stays 1.125, 1.38 stays 1.38.
    """
    if lamports is None:
        return "—"
    value = int(round(float(lamports)))
    sign = "-" if value < 0 else ""
    whole, fraction = divmod(abs(value), 1_000_000_000)
    if fraction == 0:
        return f"{sign}{whole}"
    return f"{sign}{whole}." + f"{fraction:09d}".rstrip("0")


def lamports_text(value: int | float | None) -> str:
    """Integer lamports with thousands separators, so an [EXACT] equality can be checked."""
    if value is None:
        return "—"
    return f"{int(round(float(value))):,}"


def pct_text(share: float | None) -> str:
    if share is None:
        return "—"
    return f"{100.0 * float(share):.1f}"

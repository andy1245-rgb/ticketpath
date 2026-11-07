"""Integer arithmetic for price, markup and the contract's markup buckets.

Pure: no clock, no network, no floats. Money is an integer count of lamports and
markup is integer basis points, so every function here works on ints and rounds
the same way in both directions.
"""

from __future__ import annotations

from typing import Iterable, Sequence

# The six buckets are frozen by API_CONTRACT.md: lower bound inclusive, upper
# bound exclusive, toBps None means open-ended. The range labels carry U+2013
# EN DASH between the bounds, exactly as the contract's table prints them and
# as the frontend's own fixtures write them; they are escaped here so a hyphen
# cannot creep back in unnoticed.
MARKUP_BUCKETS: tuple[tuple[str, int, int | None], ...] = (
    ("At or below face", -10_000, 1),
    ("0\u201325%", 1, 2_500),
    ("25\u201350%", 2_500, 5_000),
    ("50\u2013100%", 5_000, 10_000),
    ("100\u2013200%", 10_000, 20_000),
    ("Over 200%", 20_000, None),
)


def _round_half_away_from_zero(numerator: int, denominator: int) -> int:
    """Round an integer fraction, halves away from zero.

    Python's built-in round() is half-to-even, which would make the same markup
    round differently depending on the neighbouring values. The contract's
    worked example (a sale at +8% read as +164% when measured against the wrong
    face value) is about which face value you divide by, not about rounding, but
    the number has to be stable either way.
    """
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


def markup_bps(price_lamports: int, face_value_lamports: int) -> int:
    """Basis points of price over face value. Signed: below face is negative."""
    if not isinstance(price_lamports, int) or isinstance(price_lamports, bool):
        raise TypeError("price_lamports must be an int")
    if not isinstance(face_value_lamports, int) or isinstance(face_value_lamports, bool):
        raise TypeError("face_value_lamports must be an int")
    if face_value_lamports <= 0:
        raise ValueError("face_value_lamports must be positive")
    return _round_half_away_from_zero(
        (price_lamports - face_value_lamports) * 10_000, face_value_lamports
    )


def mean_int(values: Sequence[int]) -> int | None:
    """Arithmetic mean of integers, rounded half away from zero. None if empty."""
    if not values:
        return None
    return _round_half_away_from_zero(sum(values), len(values))


def median_int(values: Sequence[int]) -> int | None:
    """Median of integers. Even counts average the two middle values. None if empty."""
    if not values:
        return None
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return _round_half_away_from_zero(ordered[middle - 1] + ordered[middle], 2)


def bucket_of(markup: int) -> str:
    """Label of the bucket a markup in basis points falls into."""
    for label, from_bps, to_bps in MARKUP_BUCKETS:
        if markup >= from_bps and (to_bps is None or markup < to_bps):
            return label
    # The first bucket's lower bound is -10000, so a markup below -100% has no
    # bucket. It still belongs to "At or below face" in spirit, and the contract
    # gives that bucket no lower bound, so clamp rather than invent a seventh.
    return MARKUP_BUCKETS[0][0]


def markup_distribution(markups: Iterable[int]) -> list[dict]:
    """All six buckets, in contract order, including zero-count ones."""
    counts = {label: 0 for label, _, _ in MARKUP_BUCKETS}
    for value in markups:
        counts[bucket_of(value)] += 1
    return [
        {"label": label, "fromBps": from_bps, "toBps": to_bps, "count": counts[label]}
        for label, from_bps, to_bps in MARKUP_BUCKETS
    ]

"""ISO-8601 parsing and UTC day bucketing for the contract's timestamps.

Every timestamp on the wire is an ISO-8601 UTC string. Parsing is strict enough
to reject nonsense (a 500 from a malformed fixture row would be better found in
a test than in front of a judge) and lenient about the two spellings that appear
in practice: a trailing `Z` and a `+00:00` offset.
"""

from __future__ import annotations

from datetime import datetime, timezone


class TimestampError(ValueError):
    """Raised when a string is not an ISO-8601 timestamp this system understands."""


def parse(timestamp: str) -> datetime:
    """Parse an ISO-8601 string into an aware datetime. Naive input is read as UTC."""
    if not isinstance(timestamp, str) or not timestamp:
        raise TimestampError("timestamp must be a non-empty ISO-8601 string")
    text = timestamp.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise TimestampError(f"not an ISO-8601 timestamp: {timestamp!r}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def to_iso(moment: datetime) -> str:
    """Format as the contract spells it: UTC, millisecond precision, trailing Z."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    utc = moment.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{utc.microsecond // 1000:03d}Z"


def day_bucket(timestamp: str) -> str:
    """The UTC calendar day of an ISO-8601 timestamp, as YYYY-MM-DD."""
    return parse(timestamp).strftime("%Y-%m-%d")


def sort_key(timestamp: str) -> tuple[datetime, str]:
    """Chronological sort key. The raw string breaks ties so order is deterministic."""
    return (parse(timestamp), timestamp)

"""Cursor pagination for the contract's Page<T> envelope.

The cursor is the offset of the next item as a decimal string, which is what the
frontend's own fixture backend uses, so a switching frontend sees no change in
cursor shape. An offset cursor is honest only while the underlying collection is
stable: if rows are inserted in the middle, a caller can skip or repeat one. That
is recorded in records/CONTRACT-MAP.md rather than hidden.
"""

from __future__ import annotations

from typing import Sequence

DEFAULT_LIMIT = 50
MAX_LIMIT = 200


class CursorError(ValueError):
    """Raised when a cursor or limit is not usable."""


def parse_cursor(cursor: str | None) -> int:
    """Offset encoded by a cursor. Missing means the start. Negative is refused."""
    if cursor is None or cursor == "":
        return 0
    try:
        offset = int(cursor, 10)
    except (TypeError, ValueError) as exc:
        raise CursorError(f"cursor is not an offset: {cursor!r}") from exc
    if offset < 0:
        raise CursorError("cursor must not be negative")
    return offset


def parse_limit(limit: str | int | None, default: int = DEFAULT_LIMIT) -> int:
    """Limit coerced and clamped to 1..MAX_LIMIT."""
    if limit is None or limit == "":
        return default
    try:
        value = int(limit)
    except (TypeError, ValueError) as exc:
        raise CursorError(f"limit is not an integer: {limit!r}") from exc
    if value < 1:
        raise CursorError("limit must be at least 1")
    return min(value, MAX_LIMIT)


def paginate(items: Sequence, cursor: str | None = None, limit: int = DEFAULT_LIMIT) -> dict:
    """Slice a sequence into the contract's {items, nextCursor} envelope."""
    offset = parse_cursor(cursor)
    window = items[offset : offset + limit]
    following = offset + limit
    return {
        "items": list(window),
        "nextCursor": str(following) if following < len(items) else None,
    }

"""GET /api/events and GET /api/events/:idOrSlug.

Allowed values come from the contract's unions in lib/types.ts. An unknown filter
value is a 400 rather than a silent empty page, because an empty list would read
as "no events" when it means "you asked wrong".
"""

from __future__ import annotations

from ticketpath.core import pagination
from ticketpath.errors import ApiError, bad_request

EVENT_STATUSES = ("draft", "on_sale", "sold_out", "completed", "cancelled")


def _status(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in EVENT_STATUSES:
        raise bad_request(
            f"status must be one of {', '.join(EVENT_STATUSES)}; got {value!r}", "status_invalid"
        )
    return value


def list_events(orchestrator, query: dict) -> tuple[int, dict]:
    """Page<Event>, sorted by startsAt ascending."""
    try:
        limit = pagination.parse_limit(query.get("limit"))
    except pagination.CursorError as exc:
        raise bad_request(str(exc), "limit_invalid") from exc
    try:
        payload = orchestrator.list_events(
            status=_status(query.get("status")),
            city=query.get("city") or None,
            text=query.get("q") or None,
            cursor=query.get("cursor") or None,
            limit=limit,
        )
    except pagination.CursorError as exc:
        raise bad_request(str(exc), "cursor_invalid") from exc
    return 200, payload


def get_event(orchestrator, id_or_slug: str) -> tuple[int, dict]:
    """Event by opaque id or slug, 404 when absent."""
    if not id_or_slug:
        raise ApiError(400, "event id or slug is required", "id_missing")
    return 200, orchestrator.get_event(id_or_slug)

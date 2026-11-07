"""GET /api/events/:eventId/analytics — the organizer roll-up."""

from __future__ import annotations

from ticketpath.errors import ApiError


def get_event_analytics(orchestrator, event_id: str) -> tuple[int, dict]:
    """EventAnalytics. 404 when the event is absent, never an empty roll-up."""
    if not event_id:
        raise ApiError(400, "event id is required", "id_missing")
    return 200, orchestrator.event_analytics(event_id)

"""GET /api/tickets, GET /api/tickets/:ticketId and its resale-history route.

`ownerWallet` filters on the ticket's current on-chain owner, which in this store
is the `ownerWallet` column. It is not the original issuee.
"""

from __future__ import annotations

from ticketpath.core import pagination
from ticketpath.errors import ApiError, bad_request

TICKET_STATUSES = ("valid", "listed", "redeemed", "revoked")


def _status(value: str | None) -> str | None:
    if value is None or value == "":
        return None
    if value not in TICKET_STATUSES:
        raise bad_request(
            f"status must be one of {', '.join(TICKET_STATUSES)}; got {value!r}", "status_invalid"
        )
    return value


def list_tickets(orchestrator, query: dict) -> tuple[int, dict]:
    """Page<Ticket>."""
    try:
        limit = pagination.parse_limit(query.get("limit"))
    except pagination.CursorError as exc:
        raise bad_request(str(exc), "limit_invalid") from exc
    try:
        payload = orchestrator.list_tickets(
            event_id=query.get("eventId") or None,
            owner_wallet=query.get("ownerWallet") or None,
            status=_status(query.get("status")),
            cursor=query.get("cursor") or None,
            limit=limit,
        )
    except pagination.CursorError as exc:
        raise bad_request(str(exc), "cursor_invalid") from exc
    return 200, payload


def get_ticket(orchestrator, ticket_id: str) -> tuple[int, dict]:
    """Ticket by id or by mint address, 404 when absent."""
    if not ticket_id:
        raise ApiError(400, "ticket id or mint address is required", "id_missing")
    return 200, orchestrator.get_ticket(ticket_id)


def get_resale_history(orchestrator, ticket_id: str) -> tuple[int, dict]:
    """ResaleHistory: every LedgerEntryKind, oldest first, plus computed stats."""
    if not ticket_id:
        raise ApiError(400, "ticket id is required", "id_missing")
    return 200, orchestrator.resale_history(ticket_id)

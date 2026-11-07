"""Compose a contract Ticket from a store row, its tier and its ledger trail.

Fields are either taken from the store, derived from the ledger, or derived from
whether the on-chain restriction is actually enforced right now. Nothing is
invented: `transferRestricted` comes from the RPC adapter, which today says no
program is deployed, so it is false.
"""

from __future__ import annotations

from typing import Mapping, Sequence

TRANSFER_KINDS = ("sale", "transfer")


def issuance_time(entries: Sequence[Mapping]) -> str:
    """Timestamp of the ticket's `issue` entry. A ticket without one is a bug, not a guess."""
    for entry in entries:
        if entry["kind"] == "issue":
            return entry["occurredAt"]
    raise ValueError("ticket has no issue entry")


def build(
    ticket_row: Mapping,
    tier_row: Mapping,
    entries: Sequence[Mapping],
    transfer_restricted: bool,
) -> dict:
    """Contract Ticket for one row. `entries` must be chronological, oldest first."""
    sales = [entry for entry in entries if entry["kind"] == "sale" and entry["priceLamports"] is not None]
    transfers = [entry for entry in entries if entry["kind"] in TRANSFER_KINDS]
    last_sale_price = sales[-1]["priceLamports"] if sales else None
    return {
        "id": ticket_row["id"],
        "eventId": ticket_row["eventId"],
        "tierId": ticket_row["tierId"],
        "mintAddress": ticket_row["mintAddress"],
        "serial": ticket_row["serial"],
        "ownerWallet": ticket_row["ownerWallet"],
        "issuedToWallet": ticket_row["issuedToWallet"],
        "faceValueLamports": tier_row["faceValueLamports"],
        "lastSalePriceLamports": last_sale_price,
        "transferCount": len(transfers),
        "status": ticket_row["status"],
        "transferRestricted": transfer_restricted,
        "issuedAt": issuance_time(entries),
        "redeemedAt": ticket_row.get("redeemedAt"),
    }

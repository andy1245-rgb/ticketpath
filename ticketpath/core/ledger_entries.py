"""Shape raw ledger rows into the contract's LedgerEntry, oldest first.

Markup is computed here, per row, from that row's own ticket face value. That is
the whole point of the split: the store holds prices, the contract holds markup,
and no caller can accidentally measure a balcony sale against the floor price.
"""

from __future__ import annotations

from typing import Iterable, Mapping

from ticketpath.core.markup import markup_bps
from ticketpath.core.timeutil import sort_key

KINDS = ("issue", "sale", "transfer", "redeem", "revoke")


def priced(row: Mapping) -> bool:
    """True when the row records money changing hands."""
    return row["kind"] == "sale" and row.get("priceLamports") is not None


def to_entries(
    rows: Iterable[Mapping],
    face_by_ticket: Mapping[str, int],
) -> list[dict]:
    """Contract LedgerEntry list, chronological oldest first.

    `priceLamports` and `markupBps` are null together for unpriced moves (gifts,
    reissues, redemptions), which is what makes the custody trail readable.
    """
    shaped: list[tuple[tuple, dict]] = []
    for row in rows:
        ticket_id = row["ticketId"]
        try:
            face = face_by_ticket[ticket_id]
        except KeyError as exc:
            raise KeyError(f"ledger row {row.get('id')} references unknown ticket {ticket_id}") from exc
        price = row.get("priceLamports")
        if price is None:
            markup = None
        else:
            if not isinstance(price, int) or isinstance(price, bool):
                raise TypeError(f"ledger row {row.get('id')} has a non-integer price")
            markup = markup_bps(price, face)
        shaped.append(
            (
                sort_key(row["occurredAt"]),
                {
                    "id": row["id"],
                    "ticketId": ticket_id,
                    "kind": row["kind"],
                    "fromWallet": row.get("fromWallet"),
                    "toWallet": row.get("toWallet"),
                    "priceLamports": price,
                    "markupBps": markup,
                    "signature": row.get("signature"),
                    "slot": row.get("slot"),
                    "occurredAt": row["occurredAt"],
                },
            )
        )
    shaped.sort(key=lambda pair: pair[0])
    return [entry for _, entry in shaped]

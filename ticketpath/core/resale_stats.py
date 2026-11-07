"""ResaleHistory: the full trail for one ticket plus the contract's stats block.

Stats rules that are easy to get wrong, taken from API_CONTRACT.md:
  - `saleCount` counts priced sales only.
  - `transferCount` counts sale + transfer, and excludes issue/redeem/revoke.
  - `avgMarkupBps` is the mean of each sale's own markup, null when nothing sold.
  - `totalVolumeLamports` sums sale prices, unpriced moves add nothing.
  - `uniqueWallets` counts distinct wallets anywhere in the trail, including the
    issuee and any redeem destination, not only current holders.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from ticketpath.core.markup import mean_int


def stats(entries: Sequence[Mapping]) -> dict:
    """The contract's ResaleStats for a chronological entry list."""
    sales = [entry for entry in entries if entry["kind"] == "sale" and entry["priceLamports"] is not None]
    prices = [entry["priceLamports"] for entry in sales]
    markups = [entry["markupBps"] for entry in sales if entry["markupBps"] is not None]
    wallets: set[str] = set()
    for entry in entries:
        for side in ("fromWallet", "toWallet"):
            wallet = entry.get(side)
            if wallet:
                wallets.add(wallet)
    return {
        "saleCount": len(sales),
        "transferCount": sum(1 for entry in entries if entry["kind"] in ("sale", "transfer")),
        "avgMarkupBps": mean_int(markups),
        "peakPriceLamports": max(prices) if prices else None,
        "lastPriceLamports": prices[-1] if prices else None,
        "totalVolumeLamports": sum(prices),
        "uniqueWallets": len(wallets),
    }


def build(ticket_row: Mapping, face_value_lamports: int, entries: Sequence[Mapping]) -> dict:
    """Contract ResaleHistory for one ticket."""
    return {
        "ticketId": ticket_row["id"],
        "faceValueLamports": face_value_lamports,
        "entries": list(entries),
        "stats": stats(entries),
    }

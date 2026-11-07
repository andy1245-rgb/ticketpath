"""EventAnalytics: the organizer roll-up.

The contract's warning is structural here. `priceSeries[].avgMarkupBps` is the
mean of per-sale markups, each already computed against its own ticket's face in
`ledger_entries.to_entries`. Nothing in this file divides a markup by the
event's lowest face value, which is the mistake API_CONTRACT.md calls out (a
1.1 SOL orchestra seat measured against a 0.45 SOL balcony face reads as +164%
instead of +8%).
"""

from __future__ import annotations

from typing import Mapping, Sequence

from ticketpath.core.event_records import lowest_face
from ticketpath.core.markup import markup_distribution, mean_int, median_int
from ticketpath.core.timeutil import day_bucket

TOP_DESTINATION_ROWS = 12


def price_series(entries: Sequence[Mapping]) -> list[dict]:
    """Day-bucketed average sale price and mean per-sale markup, UTC, ascending."""
    by_day: dict[str, dict] = {}
    for entry in entries:
        if entry["kind"] != "sale" or entry["priceLamports"] is None:
            continue
        day = day_bucket(entry["occurredAt"])
        slot = by_day.setdefault(day, {"prices": [], "markups": []})
        slot["prices"].append(entry["priceLamports"])
        if entry["markupBps"] is not None:
            slot["markups"].append(entry["markupBps"])
    series: list[dict] = []
    for day in sorted(by_day):
        slot = by_day[day]
        series.append(
            {
                "date": day,
                "avgPriceLamports": mean_int(slot["prices"]),
                "saleCount": len(slot["prices"]),
                "avgMarkupBps": mean_int(slot["markups"]),
            }
        )
    return series


def top_destinations(
    tickets: Sequence[Mapping],
    regions: Mapping[str, str],
) -> list[dict]:
    """Current holders by ticket count, descending, capped at 12.

    `acquiredOnSecondary` is true when the holder is not the original issuee.
    `region` is null unless the wallet volunteered one, which in this build is
    never: no wallet has.
    """
    holdings: dict[str, dict] = {}
    for ticket in tickets:
        owner = ticket["ownerWallet"]
        slot = holdings.setdefault(owner, {"count": 0, "secondary": False})
        slot["count"] += 1
        if owner != ticket["issuedToWallet"]:
            slot["secondary"] = True
    rows = [
        {
            "wallet": wallet,
            "ticketCount": slot["count"],
            "region": regions.get(wallet),
            "acquiredOnSecondary": slot["secondary"],
        }
        for wallet, slot in holdings.items()
    ]
    rows.sort(key=lambda row: (-row["ticketCount"], row["wallet"]))
    return rows[:TOP_DESTINATION_ROWS]


def build(
    event_row: Mapping,
    tickets: Sequence[Mapping],
    entries: Sequence[Mapping],
    regions: Mapping[str, str],
) -> dict:
    """Contract EventAnalytics for one event.

    `tickets` are the store's ticket rows for the event, so `resoldShare` is
    measured over issued ticket rows. API_CONTRACT.md says "share of issued
    tickets that have been resold at least once"; the adapter refuses to load a
    store whose issuedCount disagrees with its ticket rows, so the two readings
    coincide.
    """
    sales = [entry for entry in entries if entry["kind"] == "sale" and entry["priceLamports"] is not None]
    prices = [entry["priceLamports"] for entry in sales]
    markups = [entry["markupBps"] for entry in sales if entry["markupBps"] is not None]
    resold_tickets = {entry["ticketId"] for entry in sales}
    holders = {ticket["ownerWallet"] for ticket in tickets}
    issued = len(tickets)
    return {
        "eventId": event_row["id"],
        "faceValueLamports": lowest_face(event_row),
        "totalVolumeLamports": sum(prices),
        "saleCount": len(sales),
        "avgMarkupBps": mean_int(markups),
        "medianResalePriceLamports": median_int(prices),
        "resoldShare": (len(resold_tickets) / issued) if issued else 0.0,
        "uniqueHolders": len(holders),
        "priceSeries": price_series(entries),
        "markupDistribution": markup_distribution(markups),
        "topDestinations": top_destinations(tickets, regions),
    }

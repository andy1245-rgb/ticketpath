"""Independent arithmetic over the synthetic fixture store, for tests to assert against.

These helpers deliberately do not import `ticketpath.core`. Every number the server
serves is recomputed here a second way, straight from `fixtures/synthetic_store.json`
and the contract's own definitions, so a disagreement means the server and this
arithmetic differ rather than that a fixture value was retyped into a test.

Nothing in this file is evidence about any market: the store it reads is synthetic
and says so in its own `meta` block.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, Mapping

STORE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic_store.json"

# The contract's six buckets: lower bound inclusive, upper bound exclusive, and
# the labels exactly as API_CONTRACT.md's table prints them, which is U+2013 EN
# DASH between the bounds rather than a hyphen. Escaped so the character is not
# lost to an editor or a font.
BUCKETS = (
    ("At or below face", -10_000, 1),
    ("0\u201325%", 1, 2_500),
    ("25\u201350%", 2_500, 5_000),
    ("50\u2013100%", 5_000, 10_000),
    ("100\u2013200%", 10_000, 20_000),
    ("Over 200%", 20_000, None),
)


def load(path: Path | None = None) -> dict:
    return json.loads((path or STORE_PATH).read_text(encoding="utf-8"))


def half_away(numerator: int, denominator: int) -> int:
    """Integer division rounding halves away from zero, as the contract requires."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    return sign * quotient


def mean_int(values: Iterable[int]) -> int | None:
    values = list(values)
    return half_away(sum(values), len(values)) if values else None


def median_int(values: Iterable[int]) -> int | None:
    ordered = sorted(values)
    if not ordered:
        return None
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return half_away(ordered[middle - 1] + ordered[middle], 2)


def markup_bps(price_lamports: int, face_lamports: int) -> int:
    return half_away((price_lamports - face_lamports) * 10_000, face_lamports)


def short_address(address: str) -> str:
    """What the frontend's shortAddress() prints: first four, ellipsis, last four."""
    return f"{address[:4]}\u2026{address[-4:]}"


def events(store: Mapping) -> list[dict]:
    return list(store["events"])


def event(store: Mapping, event_id: str) -> dict:
    return next(row for row in store["events"] if row["id"] == event_id)


def event_by_regime(store: Mapping, regime: str) -> dict:
    found = [row for row in store["events"] if row.get("demoRegime") == regime]
    if len(found) != 1:
        raise AssertionError(f"expected one event for regime {regime!r}, found {len(found)}")
    return found[0]


def tickets(store: Mapping) -> list[dict]:
    return list(store["tickets"])


def ticket(store: Mapping, ticket_id: str) -> dict:
    return next(row for row in store["tickets"] if row["id"] == ticket_id)


def tickets_for_event(store: Mapping, event_id: str) -> list[dict]:
    return [row for row in store["tickets"] if row["eventId"] == event_id]


def tier_of(store: Mapping, ticket_row: Mapping) -> dict:
    for tier in event(store, ticket_row["eventId"])["tiers"]:
        if tier["id"] == ticket_row["tierId"]:
            return tier
    raise AssertionError(f"ticket {ticket_row['id']} references a tier of another event")


def face_of(store: Mapping, ticket_row: Mapping) -> int:
    return tier_of(store, ticket_row)["faceValueLamports"]


def lowest_face(event_row: Mapping) -> int:
    return min(tier["faceValueLamports"] for tier in event_row["tiers"])


def entries_for(store: Mapping, ticket_id: str) -> list[dict]:
    rows = [row for row in store["ledger"] if row["ticketId"] == ticket_id]
    rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
    return rows


def entries_for_event(store: Mapping, event_id: str) -> list[dict]:
    ids = {row["id"] for row in tickets_for_event(store, event_id)}
    rows = [row for row in store["ledger"] if row["ticketId"] in ids]
    rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
    return rows


def sales_for(store: Mapping, ticket_id: str) -> list[dict]:
    return [row for row in entries_for(store, ticket_id) if row["kind"] == "sale"]


def sales_for_event(store: Mapping, event_id: str) -> list[dict]:
    return [row for row in entries_for_event(store, event_id) if row["kind"] == "sale"]


def markups_for_event(store: Mapping, event_id: str) -> list[int]:
    return [
        markup_bps(row["priceLamports"], face_of(store, ticket(store, row["ticketId"])))
        for row in sales_for_event(store, event_id)
    ]


def ticket_stats(store: Mapping, ticket_id: str) -> dict:
    """The contract's ResaleStats, recomputed from the raw rows."""
    rows = entries_for(store, ticket_id)
    sales = [row for row in rows if row["kind"] == "sale" and row["priceLamports"] is not None]
    face = face_of(store, ticket(store, ticket_id))
    prices = [row["priceLamports"] for row in sales]
    markups = [markup_bps(price, face) for price in prices]
    wallets: set[str] = set()
    for row in rows:
        for side in ("fromWallet", "toWallet"):
            if row[side]:
                wallets.add(row[side])
    return {
        "saleCount": len(sales),
        "transferCount": sum(1 for row in rows if row["kind"] in ("sale", "transfer")),
        "avgMarkupBps": mean_int(markups),
        "peakPriceLamports": max(prices) if prices else None,
        "lastPriceLamports": prices[-1] if prices else None,
        "totalVolumeLamports": sum(prices),
        "uniqueWallets": len(wallets),
    }


def ticket_totals(store: Mapping, ticket_id: str) -> dict:
    """The ledger-derived fields of a contract Ticket, recomputed."""
    row = ticket(store, ticket_id)
    rows = entries_for(store, ticket_id)
    sales = [entry for entry in rows if entry["kind"] == "sale"]
    issue = next(entry for entry in rows if entry["kind"] == "issue")
    moves = [entry for entry in rows if entry["kind"] in ("sale", "transfer")]
    return {
        "faceValueLamports": face_of(store, row),
        "lastSalePriceLamports": sales[-1]["priceLamports"] if sales else None,
        "transferCount": len(moves),
        "issuedAt": issue["occurredAt"],
    }


def bucket_of(bps: int) -> str:
    for label, low, high in BUCKETS:
        if bps >= low and (high is None or bps < high):
            return label
    return BUCKETS[0][0]


def event_analytics(store: Mapping, event_id: str) -> dict:
    """The contract's EventAnalytics, recomputed from the raw rows."""
    event_row = event(store, event_id)
    tickets_here = tickets_for_event(store, event_id)
    rows = entries_for_event(store, event_id)
    sales = [row for row in rows if row["kind"] == "sale" and row["priceLamports"] is not None]
    prices = [row["priceLamports"] for row in sales]
    markups = [
        markup_bps(row["priceLamports"], face_of(store, ticket(store, row["ticketId"])))
        for row in sales
    ]

    by_day: dict[str, dict] = {}
    for row, markup in zip(sales, markups):
        day = row["occurredAt"][:10]
        slot = by_day.setdefault(day, {"prices": [], "markups": []})
        slot["prices"].append(row["priceLamports"])
        slot["markups"].append(markup)
    price_series = [
        {
            "date": day,
            "avgPriceLamports": mean_int(slot["prices"]),
            "saleCount": len(slot["prices"]),
            "avgMarkupBps": mean_int(slot["markups"]),
        }
        for day, slot in sorted(by_day.items())
    ]

    counts = {label: 0 for label, _, _ in BUCKETS}
    for markup in markups:
        counts[bucket_of(markup)] += 1
    distribution = [
        {"label": label, "fromBps": low, "toBps": high, "count": counts[label]}
        for label, low, high in BUCKETS
    ]

    holdings: dict[str, dict] = {}
    for row in tickets_here:
        slot = holdings.setdefault(row["ownerWallet"], {"count": 0, "secondary": False})
        slot["count"] += 1
        if row["ownerWallet"] != row["issuedToWallet"]:
            slot["secondary"] = True
    destinations = [
        {
            "wallet": wallet,
            "ticketCount": slot["count"],
            "region": None,
            "acquiredOnSecondary": slot["secondary"],
        }
        for wallet, slot in holdings.items()
    ]
    destinations.sort(key=lambda row: (-row["ticketCount"], row["wallet"]))

    resold = {row["ticketId"] for row in sales}
    return {
        "eventId": event_id,
        "faceValueLamports": lowest_face(event_row),
        "totalVolumeLamports": sum(prices),
        "saleCount": len(sales),
        "avgMarkupBps": mean_int(markups),
        "medianResalePriceLamports": median_int(prices),
        "resoldShare": (len(resold) / len(tickets_here)) if tickets_here else 0.0,
        "uniqueHolders": len(holdings),
        "priceSeries": price_series,
        "markupDistribution": distribution,
        "topDestinations": destinations[:12],
    }


def first_event_with_sales(store: Mapping, minimum: int = 1) -> dict:
    for event_row in sorted(store["events"], key=lambda row: row["startsAt"]):
        if len(sales_for_event(store, event_row["id"])) >= minimum:
            return event_row
    raise AssertionError(f"no event has {minimum} sale rows")


def first_ticket_with_sales(store: Mapping, minimum: int = 1) -> dict:
    for row in sorted(store["tickets"], key=lambda row: row["id"]):
        if len(sales_for(store, row["id"])) >= minimum:
            return row
    raise AssertionError(f"no ticket has {minimum} sale rows")


def first_ticket_without_sales(store: Mapping) -> dict:
    for row in sorted(store["tickets"], key=lambda row: row["id"]):
        if not sales_for(store, row["id"]):
            return row
    raise AssertionError("every ticket has a sale row")


def ticket_with_own_tier_face_above_lowest(store: Mapping) -> tuple[dict, dict]:
    """A ticket on a non-cheapest tier whose sale prices above the cheapest face.

    Measuring that sale against the event's lowest face inflates the markup, which
    is the contract's stated mistake. This is the pair of rows a test uses to prove
    the server does not make it.
    """
    for event_row in store["events"]:
        lowest = lowest_face(event_row)
        for row in sorted(sales_for_event(store, event_row["id"]), key=lambda r: r["id"]):
            ticket_row = ticket(store, row["ticketId"])
            face = face_of(store, ticket_row)
            if face > lowest and row["priceLamports"] > lowest:
                return ticket_row, row
    raise AssertionError("no sale prices a non-cheapest tier above the lowest face")


def addresses(store: Mapping) -> list[str]:
    found = [row["walletAddress"] for row in store["organizers"]]
    for row in store["tickets"]:
        found += [row["mintAddress"], row["issuedToWallet"], row["ownerWallet"]]
    for row in store["ledger"]:
        for side in ("fromWallet", "toWallet"):
            if row[side]:
                found.append(row[side])
    return found

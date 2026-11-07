"""Compose a contract Event from a store row and its organizer.

Event totals are summed from the tiers rather than read from a separate stored
total, so the two can never drift. The ledger adapter refuses to load a store
whose stored totals disagree with the tiers, which is the check that makes that
safe.
"""

from __future__ import annotations

from typing import Mapping, Sequence


def tier_row_to_contract(tier_row: Mapping) -> dict:
    return {
        "id": tier_row["id"],
        "name": tier_row["name"],
        "faceValueLamports": tier_row["faceValueLamports"],
        "totalSupply": tier_row["totalSupply"],
        "issuedCount": tier_row["issuedCount"],
    }


def build(event_row: Mapping, organizer_row: Mapping) -> dict:
    tiers = [tier_row_to_contract(tier) for tier in event_row["tiers"]]
    return {
        "id": event_row["id"],
        "slug": event_row["slug"],
        "name": event_row["name"],
        "description": event_row["description"],
        "venue": event_row["venue"],
        "city": event_row["city"],
        "startsAt": event_row["startsAt"],
        "endsAt": event_row.get("endsAt"),
        "imageUrl": event_row.get("imageUrl"),
        "organizer": {
            "id": organizer_row["id"],
            "name": organizer_row["name"],
            "walletAddress": organizer_row["walletAddress"],
            "verified": organizer_row["verified"],
        },
        "status": event_row["status"],
        "tiers": tiers,
        "totalSupply": sum(tier["totalSupply"] for tier in tiers),
        "issuedCount": sum(tier["issuedCount"] for tier in tiers),
        "resaleEnabled": event_row["resaleEnabled"],
        "resalePriceCapBps": event_row.get("resalePriceCapBps"),
        "requiresVerifiedWallet": event_row["requiresVerifiedWallet"],
    }


def face_by_tier(event_row: Mapping) -> dict[str, int]:
    return {tier["id"]: tier["faceValueLamports"] for tier in event_row["tiers"]}


def lowest_face(event_row: Mapping) -> int:
    """The event's "from" price: the cheapest tier, not a single event-wide face."""
    faces = [tier["faceValueLamports"] for tier in event_row["tiers"]]
    return min(faces) if faces else 0


def matches_query(
    event_row: Mapping,
    status: str | None,
    city: str | None,
    text: str | None,
) -> bool:
    """The contract's event filters: status, city, and free text over name + venue."""
    if status is not None and event_row["status"] != status:
        return False
    if city is not None and event_row["city"].lower() != city.lower():
        return False
    if text:
        needle = text.lower()
        haystack = f"{event_row['name']} {event_row['venue']}".lower()
        if needle not in haystack:
            return False
    return True


def sort_key_by_start(event_row: Mapping) -> tuple[str, str]:
    """Contract order: startsAt ascending, id breaking ties deterministically."""
    return (event_row["startsAt"], event_row["id"])


def find(event_rows: Sequence[Mapping], id_or_slug: str) -> Mapping | None:
    """Resolve an opaque id or a URL slug, the way the frontend routes on slug."""
    for row in event_rows:
        if row["id"] == id_or_slug or row["slug"] == id_or_slug:
            return row
    return None

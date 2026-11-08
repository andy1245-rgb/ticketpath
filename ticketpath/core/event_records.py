"""Compose a contract Event from a store row and its organizer.

Event totals are summed from the tiers rather than read from a separate stored
total, so the two can never drift. The ledger adapter refuses to load a store
whose stored totals disagree with the tiers, which is the check that makes that
safe.
"""

from __future__ import annotations

from typing import Mapping, Sequence

from ticketpath.core import region_caps


def tier_row_to_contract(tier_row: Mapping) -> dict:
    return {
        "id": tier_row["id"],
        "name": tier_row["name"],
        "faceValueLamports": tier_row["faceValueLamports"],
        "totalSupply": tier_row["totalSupply"],
        "issuedCount": tier_row["issuedCount"],
    }


def _law(event_row: Mapping) -> tuple[dict | None, dict | None, dict | None, list | None]:
    """The event's jurisdiction, its resolved policy, and the ceiling the chain would hold.

    Three additive keys, not contract fields (`lib/types.ts` is unchanged and this repository
    does not edit it). They are derived, never stored: the jurisdiction is the input, the
    policy is `region_caps.resolve` against the event's own start date, and the ceiling
    combines that with the organiser's configured cap.

    `Event.resalePriceCapBps` keeps its existing meaning — the platform's configured cap. The
    enforced number is `enforcedCap.enforcedCapBps`, and the two differ exactly when a law is
    stricter. Saying so is the point: a screen must not display a cap the chain will not hold.
    """
    code = event_row.get("jurisdiction")
    if not code:
        return None, None, None, None
    starts = str(event_row.get("startsAt") or "")
    if len(starts) < 10 or not region_caps.DATE_RE.match(starts[:10]):
        # No date, no resolution. `resalePolicy: null` is "not computed", which is a different
        # statement from `unresolved` and must not be dressed up as one.
        return code, None, None, None
    policy = region_caps.resolve(
        [code],
        on_date=starts[:10],
        declared_event=event_row.get("declaredEvent"),
    )
    # One ceiling per tier, because a cap is a multiple of the ticket's own face and an
    # event-wide number is wrong by the tier ratio. `enforcedCap` is emitted only when every
    # tier resolves to the same ceiling; otherwise the per-tier list is the only honest shape.
    per_tier = []
    for tier in event_row["tiers"]:
        ceiling = region_caps.effective_ceiling(
            face_lamports=tier["faceValueLamports"],
            fee_lamports=event_row.get("feeLamports"),
            law=policy,
            platform_cap_bps=event_row.get("resalePriceCapBps"),
        )
        per_tier.append(
            {"tierId": tier["id"], **(ceiling.as_dict() if ceiling else {"enforcedCap": None})}
        )
    uniform = (
        len({tuple(sorted({k: v for k, v in row.items() if k != "tierId"}.items())) for row in per_tier}) == 1
        if per_tier
        else False
    )
    single = None
    if uniform and per_tier and "enforcedCapBps" in per_tier[0]:
        single = {k: v for k, v in per_tier[0].items() if k != "tierId"}
    return code, policy.as_dict(), single, per_tier


def build(event_row: Mapping, organizer_row: Mapping) -> dict:
    tiers = [tier_row_to_contract(tier) for tier in event_row["tiers"]]
    jurisdiction, policy, ceiling, per_tier = _law(event_row)
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
        # Additive keys for the region-aware cap (`records/REGION-CAPS-DESIGN.md` §11). Null
        # when the event declares no jurisdiction, which is every event in the synthetic
        # fixture today: a synthetic venue is not in any jurisdiction and must not be given one.
        "jurisdiction": jurisdiction,
        "resalePolicy": (policy or {}).get("resalePolicy"),
        "resalePolicyReason": (policy or {}).get("lawReason"),
        "lawTableVersion": (policy or {}).get("lawTableVersion"),
        "lawAsOf": (policy or {}).get("lawAsOf"),
        "lawBasis": [
            {
                "jurisdiction": row["jurisdiction"],
                "citation": row["citation"],
                "url": row["url"],
                "confidence": row["confidence"],
                "status": row["status"],
            }
            for row in (policy or {}).get("lawBasis", [])
        ],
        "enforcedCap": ceiling,
        "enforcedCapByTier": per_tier or [],
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

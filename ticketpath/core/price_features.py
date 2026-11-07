"""Features with a mandatory cut: one filter at the top, counts after it, nothing else.

Every field here is either a raw value from a wire row or a count over rows that are
at or before `as_of`. Nothing is read from `EventAnalytics` or `ResaleStats` (whole
history, no stated as-of: 03-b section 4 T2), from `Ticket.status`,
`.ownerWallet`, `.lastSalePriceLamports`, `.transferCount` or `.redeemedAt`
(current-state or whole-life fields that leak the future into a past cut).

`as_of` has no default. That is checklist row 1 of 03-b section 7 and it is the one
thing a test can check by reading a signature.

The cap is read at the event level because the contract puts it there
(`Event.resalePriceCapBps`), and `atCeiling` is judged against the cap in force when
the sale was recorded -- never against the candidate cap a judge sets, which is a rule
about the future. `capBpsRecorded is None` is its own branch, never a comparison
against zero.
"""

from __future__ import annotations

import math
from datetime import datetime
from typing import Mapping, Sequence

from ticketpath.core.timeutil import parse

SECONDS_PER_DAY = 86400.0


class FeatureError(ValueError):
    """A ledger row the engine cannot price.

    Raised at feature-build time and translated by the orchestrator into a typed refusal,
    so a store the loader accepts but the engine cannot price renders a page with a reason
    instead of taking the connection down. `code` is stable and appears on the page.
    """

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _markup_bps(price: int, face: int) -> int:
    """(price-face)/face in basis points, rounded half away from zero, integer only.

    Integer arithmetic because the fixture built every price from an integer markup
    (fixtures/meta.computedFields) and a float round-trip would make an on-the-ceiling
    sale miss its own ceiling on a face that does not divide evenly.
    """
    numerator = (price - face) * 10000
    if numerator >= 0:
        return (numerator + face // 2) // face
    return -((-numerator + face // 2) // face)


def _truncate(ledger: Sequence[Mapping], as_of: datetime) -> tuple[list[dict], int]:
    """The one filter. `occurredAt <= as_of`, then a chronological sort.

    `slot` breaks ties within one instant; it is not the primary key because no row in
    this store carries one (meta.missingOnChain), and the count of null slots is
    returned so the fallback is visible rather than silent (03-b row 3).
    """
    kept: list[dict] = []
    null_slots = 0
    for row in ledger:
        if parse(row["occurredAt"]) > as_of:
            continue
        if row.get("slot") is None:
            null_slots += 1
        kept.append(dict(row))
    kept.sort(key=lambda row: (row["occurredAt"], -1 if row.get("slot") is None else row["slot"], row["id"]))
    previous: str | None = None
    for row in kept:  # row 4: no negative durations, asserted rather than printed
        if previous is not None and row["occurredAt"] < previous:
            raise AssertionError(f"ledger rows are out of order at {row['id']}")
        previous = row["occurredAt"]
    return kept, null_slots


def _marks_for(
    rows: Sequence[Mapping],
    tickets: Sequence[Mapping],
    tier_id: str,
    face_by_ticket: Mapping[str, int],
    starts_at: datetime,
    cap_bps: int | None,
) -> list[dict]:
    """Priced sales in one tier, as marks. Priced only: a transfer carries no money."""
    marks: list[dict] = []
    tier_tickets = {ticket["id"] for ticket in tickets if ticket["tierId"] == tier_id}
    for row in rows:
        if row["kind"] != "sale" or row["priceLamports"] is None:
            continue
        if row["ticketId"] not in tier_tickets:
            continue
        face = face_by_ticket[row["ticketId"]]
        price = int(row["priceLamports"])
        if price <= 0:
            # `sale` with no money is a row the engine cannot turn into a price: log(0/face)
            # is undefined, and a zero mark would drag every ratio it enters.
            raise FeatureError(
                "sale_not_priced",
                f"ledger row {row['id']} is a sale recorded at {price} lamports; "
                "a sale must carry money, so this store cannot be priced",
            )
        occurred = parse(row["occurredAt"])
        days = (starts_at - occurred).total_seconds() / SECONDS_PER_DAY
        if days < 0:
            raise FeatureError(
                "sale_after_event_start",
                f"ledger row {row['id']} is a sale {abs(days):.2f} days after the event "
                "started; a negative time-to-event cannot be priced",
            )
        markup = _markup_bps(price, face)
        marks.append(
            {
                "ticketId": row["ticketId"],
                "priceLamports": price,
                "markupBps": markup,
                "occurredAt": row["occurredAt"],
                "daysToEvent": days,
                "atCeiling": cap_bps is not None and abs(markup - cap_bps) <= 1,
                "tierFaceLamports": face,
            }
        )
    return marks


def _exposure_ticket_days(
    rows: Sequence[Mapping],
    tickets: Sequence[Mapping],
    tier_id: str,
    as_of: datetime,
    ends_at: datetime | None,
) -> tuple[float, int]:
    """Sum of min(as_of, event end, redeem) - issue over the tier's tickets, in days.

    Reads the `issue` and `redeem` rows only. `Ticket.redeemedAt` is on the forbidden
    list; the row is the same fact with a timestamp the cut can act on.

    Exposure is time at risk, and a ticket is not at risk after the event it admits to is
    over. The denominator therefore stops at `endsAt` as well as at the cut and at the
    redeem row: without that floor a cut moved past the event grew the denominator on a
    record that had not changed, and the measured rate fell with the clock (4.3 against
    16.3 per 1,000 ticket-days for the same 9 sales). An event with no recorded end has no
    such floor, and the cut is the only stop.
    """
    by_ticket: dict[str, list[dict]] = {}
    for row in rows:
        by_ticket.setdefault(row["ticketId"], []).append(row)
    total = 0.0
    not_issued = 0
    for ticket in tickets:
        if ticket["tierId"] != tier_id:
            continue
        entries = by_ticket.get(ticket["id"], [])
        issue = next((entry for entry in entries if entry["kind"] == "issue"), None)
        if issue is None:  # issued after the cut, or not issued at all
            not_issued += 1
            continue
        issued_at = parse(issue["occurredAt"])
        redeem = next((entry for entry in entries if entry["kind"] == "redeem"), None)
        stops = [as_of]
        if ends_at is not None:
            stops.append(ends_at)
        if redeem is not None:
            stops.append(parse(redeem["occurredAt"]))
        days = (min(stops) - issued_at).total_seconds() / SECONDS_PER_DAY
        total += max(0.0, days)
    return total, not_issued


def _exits(rows: Sequence[Mapping], tickets: Sequence[Mapping], tier_id: str) -> dict[str, int]:
    """Cause-specific exits for the tier: the competing risks, counted separately."""
    tier_tickets = {ticket["id"] for ticket in tickets if ticket["tierId"] == tier_id}
    counts = {"sale": 0, "transfer": 0, "redeem": 0, "revoke": 0}
    for row in rows:
        if row["ticketId"] in tier_tickets and row["kind"] in counts:
            counts[row["kind"]] += 1
    return counts


def build(
    *,
    events: Sequence[Mapping],
    tickets: Sequence[Mapping],
    ledger: Sequence[Mapping],
    tier_faces: Mapping[str, int],
    event_id: str,
    as_of: datetime,
    use_own_rows: bool = True,
) -> dict:
    """EventFeatures for one event at one cut instant.

    `use_own_rows=False` withholds this event's own ledger and ticket rows: the features are
    then the event's metadata (tiers, faces, cap, dates) and nothing it did. That is the
    before-on-sale mode, and it is the only way a prior event count can enter without this
    event's own record entering with it.
    """
    event = next((row for row in events if row["id"] == event_id), None)
    if event is None:
        raise KeyError(f"unknown event {event_id!r}")
    starts_at = parse(event["startsAt"])
    # The end of the event is the last instant a ticket can be at risk; an event with no
    # recorded end has none, and the cut alone stops the denominator (N3, 10-final-review).
    ends_at = parse(event["endsAt"]) if event.get("endsAt") else None
    cap_bps = event.get("resalePriceCapBps")
    event_tickets = [
        ticket for ticket in tickets if ticket["eventId"] == event_id
    ] if use_own_rows else []
    rows, null_slots = _truncate(ledger, as_of)
    tickets_at_cut = {t["id"] for t in event_tickets}
    rows = [row for row in rows if row["ticketId"] in tickets_at_cut]
    # A ticket exists at the cut only when its `issue` row is at or before it. Counting
    # `event_tickets` instead put a ticket issued in September on a page cut in August.
    issued_at_cut = {row["ticketId"] for row in rows if row["kind"] == "issue"}

    tiers: list[dict] = []
    for tier in event["tiers"]:
        marks = _marks_for(rows, event_tickets, tier["id"], tier_faces, starts_at, cap_bps)
        exposure, not_issued = _exposure_ticket_days(rows, event_tickets, tier["id"], as_of, ends_at)
        at_ceiling = sum(1 for mark in marks if mark["atCeiling"])
        face = int(tier["faceValueLamports"])
        tier_tickets = [ticket for ticket in event_tickets if ticket["tierId"] == tier["id"]]
        issued = sum(1 for ticket in tier_tickets if ticket["id"] in issued_at_cut)
        total_supply = int(tier["totalSupply"])
        tiers.append(
            {
                "tierId": tier["id"],
                "name": tier["name"],
                "faceValueLamports": face,
                "totalSupply": total_supply,
                "issuedCount": issued,
                "sellThrough": (issued / total_supply) if total_supply else 0.0,
                "capBpsRecorded": cap_bps,
                "capCeilingLamportsRecorded": None if cap_bps is None else face * (10000 + cap_bps) // 10000,
                "marks": marks,
                "atCeilingCount": at_ceiling,
                "belowCeilingCount": len(marks) - at_ceiling,
                "highestRecordedLamports": max((mark["priceLamports"] for mark in marks), default=None),
                "lowestRecordedLamports": min((mark["priceLamports"] for mark in marks), default=None),
                "exposureTicketDays": exposure,
                "ticketsNotIssuedAtCut": not_issued,
                "firstMarkAt": marks[0]["occurredAt"] if marks else None,
                "lastMarkAt": marks[-1]["occurredAt"] if marks else None,
                "daysToEventAtFirstMark": marks[0]["daysToEvent"] if marks else None,
                "daysToEventAtLastMark": marks[-1]["daysToEvent"] if marks else None,
                "timeSpreadDays": (
                    max(mark["daysToEvent"] for mark in marks) - min(mark["daysToEvent"] for mark in marks)
                )
                if len(marks) >= 2
                else 0.0,
                "exits": _exits(rows, event_tickets, tier["id"]),
            }
        )

    all_marks = [mark for tier in tiers for mark in tier["marks"]]
    all_marks.sort(key=lambda mark: mark["occurredAt"])
    return {
        "eventId": event_id,
        "asOf": as_of.isoformat(),
        "startsAt": event["startsAt"],
        "endsAt": event.get("endsAt"),
        "name": event["name"],
        "city": event.get("city"),
        "status": event.get("status"),
        "capBpsRecorded": cap_bps,
        "tiers": tiers,
        "event": {
            "sales": len(all_marks),
            "tickets": sum(tier["issuedCount"] for tier in tiers),
            "storeTickets": len([t for t in tickets if t["eventId"] == event_id]) if use_own_rows else 0,
            "exposureTicketDays": sum(tier["exposureTicketDays"] for tier in tiers),
            "atCeiling": sum(1 for mark in all_marks if mark["atCeiling"]),
            "firstSaleAt": all_marks[0]["occurredAt"] if all_marks else None,
            "lastSaleAt": all_marks[-1]["occurredAt"] if all_marks else None,
        },
        "provenance": {
            "nullSlotRows": null_slots,
            "rowsConsidered": len(ledger),
            "rowsAfterCut": len(rows),
            "slotFallback": "occurredAt (no row in this store carries a slot)",
        },
    }


def tier(features: Mapping, tier_id: str) -> dict:
    for row in features["tiers"]:
        if row["tierId"] == tier_id:
            return row
    raise KeyError(f"unknown tier {tier_id!r} on event {features['eventId']!r}")


def mean_log_ratio(marks: Sequence[Mapping]) -> tuple[float | None, float, int]:
    """Mean and variance of log(price/face) over a set of marks, and their count."""
    values = []
    for mark in marks:
        if mark["tierFaceLamports"] > 0 and mark["priceLamports"] > 0:
            values.append(math.log(mark["priceLamports"] / mark["tierFaceLamports"]))
    if not values:
        return None, 0.0, 0
    mean = sum(values) / len(values)
    if len(values) < 2:
        return mean, 0.0, 1
    var = sum((value - mean) ** 2 for value in values) / (len(values) - 1)
    return mean, var, len(values)


def cross_section(
    *,
    events: Sequence[Mapping],
    tickets: Sequence[Mapping],
    ledger: Sequence[Mapping],
    tier_faces: Mapping[str, int],
    as_of: datetime,
    own_record_excluded: str | None = None,
) -> list[dict]:
    """One row per event at the same cut: the counts, the regime, and the pooling input.

    The pooling input is the event's mean log resale-price-to-face ratio, its within
    variance and its sale count -- exactly what a normal-normal partial pool needs, and
    nothing that a `ResaleStats` field would have supplied.

    `own_record_excluded` builds that one event from its metadata only, so it contributes
    nothing to the pool. That is how the before-on-sale decision sees other events' records
    and this event's own metadata, and nothing else.
    """
    rows: list[dict] = []
    for event in events:
        features = build(
            events=events,
            tickets=tickets,
            ledger=ledger,
            tier_faces=tier_faces,
            event_id=event["id"],
            as_of=as_of,
            use_own_rows=event["id"] != own_record_excluded,
        )
        marks = [mark for row in features["tiers"] for mark in row["marks"]]
        mean, var, n = mean_log_ratio(marks)
        cap = features["capBpsRecorded"]
        at_ceiling = sum(1 for mark in marks if mark["atCeiling"])
        if not marks:
            regime = "no_resale"
        elif cap is not None and at_ceiling > 0:
            regime = "capped_and_binding"
        elif cap is not None:
            regime = "capped_no_mass_point"
        else:
            regime = "uncapped"
        # Completed, not started: a completed event is one whose run has ended by the cut.
        ends = event.get("endsAt") or event["startsAt"]
        rows.append(
            {
                "eventId": event["id"],
                "name": event["name"],
                "status": event.get("status"),
                "capBps": cap,
                "sales": len(marks),
                "tickets": features["event"]["tickets"],
                "atCeiling": at_ceiling,
                "shareAtCeiling": (at_ceiling / len(marks)) if marks else 0.0,
                "regime": regime,
                "startedAtCut": parse(event["startsAt"]) <= as_of,
                "completedAtCut": parse(ends) <= as_of,
                "meanLogRatio": mean,
                "withinVar": var,
                "n": n,
                "tiers": [
                    {
                        "tierId": row["tierId"],
                        "name": row["name"],
                        "faceValueLamports": row["faceValueLamports"],
                        "sales": len(row["marks"]),
                        "atCeiling": row["atCeilingCount"],
                        "shareAtCeiling": (row["atCeilingCount"] / len(row["marks"])) if row["marks"] else 0.0,
                    }
                    for row in features["tiers"]
                ],
            }
        )
    return rows


def default_selection(rows: Sequence[Mapping]) -> tuple[str, str | None]:
    """The event the page opens on: the strongest cap-binding evidence.

    Highest share of sales at the ceiling, ties broken by the most sales, then by id so
    the choice is deterministic. Within that event, the tier with the highest at-ceiling
    share. This is the case the product exists for (spec section 1.1 step 2).

    An event with no tiers cannot be opened on: it has nothing to price, and dereferencing
    `tiers[0]` there used to take the page out. It is skipped when any other event has a
    tier, and when none does the choice falls back to the first row and the orchestrator
    refuses with a typed reason.
    """
    candidate_rows = [row for row in rows if row.get("tiers")] or list(rows)
    ranked = sorted(candidate_rows, key=lambda row: (-row["shareAtCeiling"], -row["sales"], row["eventId"]))
    chosen = ranked[0]
    if not chosen["tiers"]:
        return chosen["eventId"], None
    best_tier = sorted(
        chosen["tiers"],
        key=lambda row: (-row["shareAtCeiling"], -row["sales"], row["tierId"]),
    )[0]
    return chosen["eventId"], (best_tier["tierId"] if best_tier["sales"] else None)

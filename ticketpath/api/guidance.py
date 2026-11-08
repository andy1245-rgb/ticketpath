"""Marshal the engine's output into the console payload. Attach badges; compute nothing.

Every number in the payload is a `num()` wrapper carrying the three things the payload
walker and the page both need: the badge (which of the eight), the basis (which names the
record and the count, never "data"), and the label id (the sentence the page must print
beside it). A bare int or float anywhere is a test failure, with `STRUCTURAL_KEYS` the
only exemption -- HTTP-ish status numbers and simulation error codes are identifiers, not
measurements.

`build` performs no arithmetic. If a number does not arrive computed, it does not
appear.
"""

from __future__ import annotations

from typing import Mapping, Sequence

CONSOLE_VERSION = "console-2026-11-07"

# Keys whose value is an identifier rather than a measurement.
STRUCTURAL_KEYS = frozenset({"code", "status", "consoleVersion", "simulated", "selected", "selectedTier"})


def num(
    value,
    badge: str,
    basis: str,
    label_id: str | None,
    unit: str | None = None,
    covered_by_quote_hash: bool | None = None,
) -> dict:
    """A measured number with its badge, its basis and the label sentence that must print.

    `covered_by_quote_hash` is set only for numbers read out of a recorded artefact, and only
    the six fields the quote hash covers are `True`. It travels beside the badge because the
    badge names the source and this names the assurance: the page prints the second one, and
    a payload consumer that renders the first as chain evidence is quoting half the record
    (feature 2 review, the forged-signature finding).
    """
    wrapper = {
        "value": value,
        "badge": badge,
        "basis": basis,
        "labelId": label_id,
        "unit": unit,
    }
    if covered_by_quote_hash is not None:
        wrapper["coveredByQuoteHash"] = covered_by_quote_hash
    return wrapper


def county(value, sales: int, at_ceiling: int, events: int, label_id: str | None = None) -> dict:
    """A fixture count, with the basis string P6 requires: the record and the count."""
    basis = f"{sales} sales, {at_ceiling} at the ceiling, {events} events with resale"
    return num(value, "FIXTURE", basis, label_id)


def build(
    *,
    event: Mapping,
    tiers: Sequence[Mapping],
    features: Mapping,
    bands: Mapping[str, Mapping],
    paths: Mapping[str, Mapping],
    intensities: Mapping[str, Mapping],
    recommendations: Mapping[str, Mapping],
    as_of: str,
    data_source: Mapping,
    params: Mapping,
    events_index: Sequence[Mapping],
    selected_tier: str | None,
    pooled: Mapping,
    fixture_sha: str,
    chain: Mapping,
    sim: Sequence[Mapping],
    canonical_url: str,
    decision_mode: str = "counterfactual",
    record_state: str = "ended_with_resales",
    excluded: Mapping | None = None,
    held_back: Mapping | None = None,
) -> dict:
    """The whole console payload. Shape is the spec's; every leaf is labelled.

    `excluded` is what the before-on-sale mode left out of the features: this event's own
    ticket rows and priced sale rows at the cut, counted from the store. It is a count, not
    an input -- the estimator never sees it -- and it exists so the page can say the rows are
    excluded instead of saying there are none.

    `record_state` is which record the decision instant actually has, measured by the
    orchestrator from the store at the cut: `before_first_ticket`, `issued_no_resale`,
    `issued_no_resale_yet`, `in_market`, `ended_no_resale`, `ended_no_ticket`,
    `ended_with_resales` or `cancelled`. It selects the mode sentence, so `completed record`
    and `hindsight` are printed only where the event's run has ended at the instant
    (12-final-audit, property (d)).

    `held_back` is what the loader refused to serve at all, by event id, each with its typed
    reason. The served count and the store's own count differ by exactly this, so both travel
    to the page: `7 events in the store` was a store total printed from the served list (N6,
    10-final-review), and the noun could only be made true by naming what was withheld.
    """
    sales = features["event"]["sales"]
    at_ceiling = features["event"]["atCeiling"]
    events_with_resale = int(pooled.get("eventsWithResale", 0))
    events_completed = int(pooled.get("eventsCompleted", pooled.get("eventsInWindow", 0)))
    fee_present = params.get("feeLamports") is not None
    held_back = dict(held_back or {})
    events_served = len(events_index)
    tier_payloads = []
    for tier in tiers:
        tier_id = tier["tierId"]
        band = bands[tier_id]
        recommendation = recommendations[tier_id]
        path = paths[tier_id]
        intensity = intensities[tier_id]
        tier_payloads.append(
            {
                "tierId": tier_id,
                "name": tier["name"],
                "selected": tier_id == selected_tier,
                "faceValueLamports": num(
                    tier["faceValueLamports"],
                    "FIXTURE",
                    f"tier face from the store: {tier['name']}",
                    "A2",
                    "lamports",
                ),
                "regime": band["regime"],
                "band": _band(
                    band,
                    tier,
                    sales,
                    at_ceiling,
                    events_with_resale,
                    in_force_bps=params.get("capBpsCandidate"),
                ),
                "recommendation": _recommendation(recommendation, sales, at_ceiling, events_with_resale),
                "market": _market(
                    tier,
                    features,
                    intensity,
                    sales,
                    at_ceiling,
                    events_with_resale,
                    event_tickets=features["event"]["tickets"],
                ),
                "path": _path(path, sales, at_ceiling, events_with_resale),
                "refusal": {
                    "code": recommendation["refusalCode"] or band.get("labelId"),
                    "refused": recommendation["refused"],
                    "refusals": recommendation["refusals"],
                    "saleProbability": None,
                    "saleProbabilityReason": "not_identified",
                    "labelId": "A15",
                },
            }
        )

    chosen = next((row for row in tier_payloads if row["selected"]), tier_payloads[0] if tier_payloads else None)
    labels_shown = _labels_shown(chosen)
    return {
        "consoleVersion": CONSOLE_VERSION,
        "asOf": as_of,
        "fixtureBuild": {"sha256": fixture_sha, "labelId": "T1"},
        "event": {
            "id": event["id"],
            # The slug is not printed by the page, and `/guidance.json` needs the same
            # event a reader would click from the grid. Reading it here keeps the two
            # surfaces projections of one payload rather than two lookups of one store.
            "slug": event.get("slug"),
            "name": event["name"],
            "status": event.get("status"),
            "startsAt": event["startsAt"],
            "city": event.get("city"),
            "capBps": num(
                event.get("resalePriceCapBps"), "FIXTURE", "the cap in force when each sale was recorded", "A10", "bps"
            ),
        },
        "events": [
            {
                "id": row["eventId"],
                "name": row["name"],
                "regime": row["regime"],
                "selected": row["eventId"] == event["id"],
                "sales": county(row["sales"], row["sales"], row["atCeiling"], events_with_resale, "A1"),
                "atCeiling": county(
                    row["atCeiling"], row["sales"], row["atCeiling"], events_with_resale, "A16"
                ),
            }
            for row in events_index
        ],
        "selection": {
            "tierId": selected_tier,
            "mode": decision_mode,
            "tau": num(
                params.get("tau"), "DECLARED", "a width a person set, not estimated from the record", "A8", "log units"
            ),
            "capBpsCandidate": num(
                params.get("capBpsCandidate"), "DECLARED", "a forward policy, never a reclassification of the past", "A10", "bps"
            ),
            "feeLamports": num(
                params.get("feeLamports"),
                "DECLARED",
                "a parameter a person set; no fee field exists in the contract",
                "A6",
                "lamports",
            ),
        },
        "decisionMode": _decision_mode(
            event,
            as_of,
            decision_mode,
            events_with_resale,
            events_completed,
            excluded,
            selected_tier,
            next((tier["name"] for tier in tiers if tier["tierId"] == selected_tier), None),
            record_state,
        ),
        "evidence": {
            "resales": county(sales, sales, at_ceiling, events_with_resale, "A1"),
            "tickets": num(
                features["event"]["tickets"],
                "FIXTURE",
                (
                    f"tickets with an issue row at or before the cut; {excluded['tickets']} ticket rows "
                    "exist in the store and the decision mode excludes them"
                    if excluded is not None
                    else f"tickets with an issue row at or before the cut; {features['event']['storeTickets']} ticket rows exist in the store"
                ),
                "A1",
            ),
            "atCeiling": county(at_ceiling, sales, at_ceiling, events_with_resale, "A16"),
            "eventsOnPlatform": county(events_served, sales, at_ceiling, events_with_resale, "A17"),
            # The store's own total is served plus withheld, and it is the only number the
            # noun `in the store` may carry. Zero held back is the normal case and the page
            # prints the one number it always printed.
            "eventsInStore": county(
                events_served + len(held_back), sales, at_ceiling, events_with_resale, "A17"
            ),
            "eventsHeldBack": num(
                len(held_back),
                "FIXTURE",
                "event rows the loader held back at load, each with its own typed reason",
                "A17",
            ),
            "heldBackReasons": [
                {"eventId": event_id, "code": reason.get("code") or reason.get("labelId")}
                for event_id, reason in sorted(held_back.items())
            ],
            "eventsWithResale": county(events_with_resale, sales, at_ceiling, events_with_resale, "A13"),
            "onchainTransactions": dict(
                # Measured from the file's own grammar by `chain_client` and built once in the
                # orchestrator, so the strip and the chain slot count the same transactions.
                # It used to be `1 if verified else 0` while the page printed three signatures
                # (feature 2 review).
                chain.get("signaturesRecorded")
                or num(
                    0,
                    "DEVNET",
                    "the artefact file did not verify, so no signature in it is counted",
                    "devnet_unverified",
                )
            ),
        },
        "tiers": tier_payloads,
        "decision": chosen["recommendation"] if chosen else None,
        "market": chosen["market"] if chosen else None,
        "refusals": _refusals(chosen, pooled, fee_present),
        "saleProbability": {"value": None, "reason": "not_identified", "labelId": "A15"},
        "chain": dict(chain),
        "sim": [dict(line) for line in sim],
        "pooled": {
            "muLogRatio": num(pooled.get("mu"), "UNVALIDATED", f"pooled across {events_with_resale} events with resale", "A11"),
            "tau": num(
                pooled.get("tau"),
                "UNVALIDATED" if pooled.get("method") == "dersimonian_laird" else "DECLARED",
                f"{pooled.get('method')} on {events_with_resale} events with resale",
                "A11",
            ),
            "eventsWithResale": county(events_with_resale, sales, at_ceiling, events_with_resale, "A13"),
            "eventsInWindow": county(
                int(pooled.get("eventsInWindow", 0)), sales, at_ceiling, events_with_resale, "A17"
            ),
            "eventsCompleted": county(events_completed, sales, at_ceiling, events_with_resale, "A17"),
            "method": pooled.get("method"),
        },
        "labelsShown": labels_shown,
        "dataSource": dict(data_source),
        "canonicalUrl": canonical_url,
    }


# The mode sentence is chosen by the record the decision instant has, not by a fixed word.
# `P_MODE_COUNTERFACTUAL` keeps the `completed record` wording, and it is reachable only from
# `ended_with_resales`; every other state gets a sentence that is true of it. The two
# before-on-sale maps below do the same for the premise sentence: `P_MODE_BEFORE` claims the
# decision is taken before this event's first ticket, so it may only be printed where no
# ticket has been issued at or before the instant.
_COUNTERFACTUAL_BY_STATE: Mapping[str, str] = {
    "cancelled": "P_MODE_COUNTERFACTUAL_CANCELLED",
    "ended_with_resales": "P_MODE_COUNTERFACTUAL",
    "ended_no_resale": "P_MODE_COUNTERFACTUAL_ENDED_EMPTY",
    "ended_no_ticket": "P_MODE_COUNTERFACTUAL_ENDED_EMPTY",
    "in_market": "P_MODE_COUNTERFACTUAL_OPEN",
    "before_first_ticket": "P_MODE_COUNTERFACTUAL_NOT_STARTED",
    "issued_no_resale": "P_MODE_COUNTERFACTUAL_NO_RESALE_AT_ALL",
    "issued_no_resale_yet": "P_MODE_COUNTERFACTUAL_NO_SALE_YET",
}

_BEFORE_BY_STATE: Mapping[str, str] = {
    "cancelled": "P_MODE_BEFORE_CANCELLED",
    "before_first_ticket": "P_MODE_BEFORE",
    "ended_no_ticket": "P_MODE_BEFORE_NOTHING",
    # tickets on the record, no resale at or before the instant: the issued sentence may not
    # claim a resale the record does not hold
    "issued_no_resale": "P_MODE_BEFORE_NO_RESALE",
    "issued_no_resale_yet": "P_MODE_BEFORE_NO_RESALE",
    "ended_no_resale": "P_MODE_BEFORE_NO_RESALE",
}
# in_market and ended_with_resales: tickets and resales on the record at the instant.
_BEFORE_DEFAULT = "P_MODE_BEFORE_ISSUED"


def _decision_mode(
    event: Mapping,
    as_of: str,
    mode: str,
    events_with_resale: int,
    events_completed: int,
    excluded: Mapping | None = None,
    selected_tier: str | None = None,
    tier_name: str | None = None,
    record_state: str = "ended_with_resales",
) -> dict:
    """The decision instant, on the payload so the page cannot print a number without it.

    Two modes and no third: the real before-on-sale decision, and the labelled recomputation
    from the event's own record. The event's status and dates travel with it, because a
    hindsight number beside a completed event is a different object from a decision. What
    the mode excluded travels with it too, in the same two nouns the strip prints, so `0
    resales enter this decision` can never be read as `this event has no resales`.
    """
    out = {
        "mode": mode,
        "labelId": (
            _COUNTERFACTUAL_BY_STATE.get(record_state, "P_MODE_COUNTERFACTUAL")
            if mode == "counterfactual"
            else _BEFORE_BY_STATE.get(record_state, _BEFORE_DEFAULT)
        ),
        # The state travels with the label so a reader of the payload can check the sentence
        # against the fact that chose it, and so the console does not have to re-derive it.
        "recordState": record_state,
        "usesOwnRecord": mode == "counterfactual",
        "pooledOtherEvents": num(
            events_with_resale, "FIXTURE", f"{events_with_resale} events with a resale record at the cut", "A13_POOLED"
        ),
        "eventsCompleted": num(
            events_completed, "FIXTURE", f"{events_completed} events ended at or before the cut", "A17"
        ),
        "eventStatus": event.get("status"),
        "eventStartsAt": event["startsAt"],
        "eventEndsAt": event.get("endsAt"),
        "asOf": as_of,
        "excludedResales": None,
        "excludedTickets": None,
    }
    if excluded is not None:
        out["excludedResales"] = num(
            excluded["resales"],
            "FIXTURE",
            f"{excluded['resales']} priced sale rows on this event at or before the cut, excluded by the before-on-sale mode",
            "A1",
        )
        out["excludedTickets"] = num(
            excluded["tickets"],
            "FIXTURE",
            f"{excluded['tickets']} ticket rows on this event with an issue row at or before the cut, excluded by the before-on-sale mode",
            "A1",
        )
        # The same exclusion, scoped to the tier the market block prints. Without it the block
        # said `0 sales of 0 on this event` inside a sentence that is the tier's, while the
        # strip above it said 12 rows were being excluded: two scopes, one zero, no clause
        # saying which zero is which (11-final, item 5).
        tier_rows = (excluded.get("byTier") or {}).get(selected_tier or "", {})
        out["excludedTierResales"] = num(
            tier_rows.get("resales", 0),
            "FIXTURE",
            (
                f"{tier_rows.get('resales', 0)} priced sale rows in this tier at or before the cut, "
                "excluded by the before-on-sale mode"
            ),
            "A1",
        )
        out["excludedTierId"] = selected_tier
        out["excludedTierName"] = tier_name
    else:
        out["excludedTierResales"] = None
    return out


def _band(
    band: Mapping,
    tier: Mapping,
    sales: int,
    at_ceiling: int,
    events: int,
    in_force_bps: int | None = None,
) -> dict:
    """The band block, with the interval the page prints scoped to the ceilings it states.

    Two ceilings can be in play on one page: the recorded cap, which the sales were made
    under, and the cap in force, which is what the page prices against. The band's upper end
    may not sit above either of them -- a band printed above a ceiling stated in the same
    block is the contradiction three reviews have now found, once in the recommendation band
    and twice in the prior band.

    So the printed interval is `shownLoLamports`..`shownHiLamports`: the band, cut at the
    lowest ceiling the page states, with `ceilingAppliedLamports` and its source named so the
    sentence can say which cap cut it. `loLamports` and `hiLamports` keep the computed band
    unchanged, so the declared prior's own extent is still on the payload and the page can
    print it beside the cut rather than instead of it.
    """
    basis = f"{len(tier['marks'])} sales in this tier, {tier['atCeilingCount']} at the ceiling, {events} events with resale"
    lo = band["band"]["loLamports"]
    hi = band["band"]["hiLamports"]
    face = tier["faceValueLamports"]
    ceilings: list[tuple[int, str, int | None]] = []
    if band["band"].get("boundCeilingLamports") is not None:
        ceilings.append(
            (band["band"]["boundCeilingLamports"], "band_bound", band["band"].get("boundCeilingCapBps"))
        )
    if tier["capCeilingLamportsRecorded"] is not None:
        ceilings.append((tier["capCeilingLamportsRecorded"], "recorded_cap", band.get("capBpsRecorded")))
    if in_force_bps is not None:
        ceilings.append((face * (10_000 + int(in_force_bps)) // 10_000, "cap_in_force", int(in_force_bps)))
    shown_lo, shown_hi, applied, applied_source, applied_cap = lo, hi, None, None, None
    if hi is not None and ceilings:
        # The lowest ceiling binds; on a tie the cap in force is the one to name, because it is
        # the cap the page prices against and the one the reader is holding in their hand.
        limit, source, cap_used = min(
            ceilings, key=lambda row: (row[0], 0 if row[1] == "cap_in_force" else 1)
        )
        if hi > limit:
            shown_hi = limit
            shown_lo = limit if (lo is not None and lo > limit) else lo
            applied, applied_source = limit, source
            applied_cap = cap_used
    out = {
        "regime": band["regime"],
        "available": band.get("available", True),
        "refusalCode": band.get("refusalCode"),
        "loLamports": (
            None
            if lo is None
            else num(lo, "UNVALIDATED", basis, band["labelId"], "lamports")
        ),
        "hiLamports": (
            None
            if band["band"]["hiLamports"] is None
            else num(band["band"]["hiLamports"], "UNVALIDATED", basis, band["labelId"], "lamports")
        ),
        "noUpperBound": band["band"]["noUpperBound"],
        "topIsCeiling": band["band"]["topIsCeiling"],
        # The interval the page prints. Equal to the computed band unless a ceiling the page
        # states is below its top, in which case the cut is named here and said in words.
        "shownLoLamports": None
        if shown_lo is None
        else num(shown_lo, "UNVALIDATED", basis, band["labelId"], "lamports"),
        "shownHiLamports": None
        if shown_hi is None
        else num(shown_hi, "UNVALIDATED", basis, band["labelId"], "lamports"),
        "ceilingAppliedLamports": None
        if applied is None
        else num(
            applied,
            "EXACT",
            f"face {face} x (10,000 + {applied_cap}) / 10,000, integer arithmetic",
            None,
            "lamports",
        ),
        "ceilingAppliedSource": applied_source,
        "ceilingAppliedCapBps": None
        if applied_cap is None
        else num(
            applied_cap,
            "DECLARED" if applied_source == "cap_in_force" else "FIXTURE",
            "the cap that produced the ceiling this band stops at",
            "A10" if applied_source == "cap_in_force" else None,
            "bps",
        ),
        # The ceiling the band's upper end was actually stopped at, and the cap that put it
        # there. The page prints it wherever the band's top is a ceiling rather than a width,
        # so the reader is told which limit the band stops at instead of meeting a number
        # with no stated source.
        "boundCeilingLamports": None
        if band["band"].get("boundCeilingLamports") is None
        else num(
            band["band"]["boundCeilingLamports"],
            "EXACT",
            f"face {tier['faceValueLamports']} x (10,000 + {band['band'].get('boundCeilingCapBps')}) / 10,000, integer arithmetic",
            None,
            "lamports",
        ),
        "widenedToFloor": band["band"]["widenedToFloor"],
        "tau": num(band["band"]["tau"], "DECLARED", "the declared width; it enters the width only", "A8"),
        # The cap that produced `boundCeilingLamports`, so the sentence that names the ceiling
        # names its actual source: `the ceiling the cap in force puts on this tier` was printed
        # at a number computed from the recorded cap.
        "boundCeilingCapBps": None
        if band["band"].get("boundCeilingCapBps") is None
        else num(
            band["band"]["boundCeilingCapBps"],
            "DECLARED" if band["band"].get("boundCeilingCapBps") == in_force_bps else "FIXTURE",
            "the cap that produced the ceiling the band's upper end stops at",
            "A10",
            "bps",
        ),
        "boundCeilingSource": (
            None
            if band["band"].get("boundCeilingLamports") is None
            else (
                "cap_in_force"
                if band["band"].get("boundCeilingCapBps") == in_force_bps
                else "recorded_cap"
            )
        ),
        "widthSource": band["band"]["widthSource"],
        "ceilingLamports": None
        if tier["capCeilingLamportsRecorded"] is None
        else num(
            tier["capCeilingLamportsRecorded"],
            "EXACT",
            f"face {tier['faceValueLamports']} x (1 + cap_bps/10000), integer arithmetic",
            None,
            "lamports",
        ),
        "sensitivity": [
            {
                "tau": num(row["tau"], "DECLARED", "a declared width, swept", "A8"),
                "loLamports": None
                if row["loLamports"] is None
                else num(row["loLamports"], "UNVALIDATED", basis, band["labelId"], "lamports"),
                "hiLamports": None
                if row["hiLamports"] is None
                else num(row["hiLamports"], "UNVALIDATED", basis, band["labelId"], "lamports"),
                "applicable": row["applicable"],
                "reason": row["reason"],
            }
            for row in band["sensitivity"]
        ],
        "labelId": band["labelId"],
        "extraLabelIds": list(band.get("extraLabelIds", [])),
        "capViolations": {
            "count": num(
                band["capViolations"]["count"],
                "FIXTURE",
                f"{band['capViolations']['count']} of {band['capViolations']['of']} recorded sales above the candidate cap",
                "cap_would_refuse",
            )
            if band["capViolations"].get("candidateCapBps") is not None
            else num(0, "FIXTURE", "no candidate cap was applied; nothing to violate", "A10"),
            "of": num(
                band["capViolations"]["of"],
                "FIXTURE",
                f"{band['capViolations']['of']} recorded sales in this tier",
                "A1",
            ),
        },
    }
    return out


def _recommendation(recommendation: Mapping, sales: int, at_ceiling: int, events: int) -> dict:
    basis = f"{sales} sales, {at_ceiling} at the ceiling, {events} events with resale"
    value = recommendation["recommendedLamports"]
    ceiling = recommendation.get("candidateCeilingLamports")
    return {
        "refused": recommendation["refused"],
        "refusalCode": recommendation["refusalCode"],
        "recommendedLamports": None if value is None else num(value, "UNVALIDATED", basis, recommendation["labelId"], "lamports"),
        "recommendedIsFloor": recommendation["recommendedIsFloor"],
        "bandLoLamports": None
        if recommendation["bandLamports"][0] is None
        else num(recommendation["bandLamports"][0], "UNVALIDATED", basis, recommendation["labelId"], "lamports"),
        "bandHiLamports": None
        if recommendation["bandLamports"][1] is None
        else num(recommendation["bandLamports"][1], "UNVALIDATED", basis, recommendation["labelId"], "lamports"),
        "noUpperBound": recommendation["noUpperBound"],
        "basis": recommendation["basis"],
        "labelId": recommendation["labelId"],
        "candidateCeilingLamports": None
        if ceiling is None
        else num(
            ceiling,
            "EXACT",
            f"face x (10,000 + {int(recommendation.get('candidateCapBps'))}) / 10,000, integer arithmetic",
            None,
            "lamports",
        ),
        "extraLabelIds": list(recommendation.get("extraLabelIds", [])),
        "consequence": [
            {
                "candidateLamports": num(row["candidateLamports"], "EXACT", "addition and division only", None, "lamports"),
                "requiredSellThrough": num(row["requiredSellThrough"], "EXACT", "face x observed sell-through / candidate", None),
            }
            for row in recommendation["consequence"]
        ],
        "netRevenue": None
        if recommendation["netRevenue"] is None
        else {
            "perTicket": num(recommendation["netRevenue"]["perTicket"], "EXACT", "the recommendation less the declared fee, integer arithmetic", None, "lamports"),
            "perTier": num(recommendation["netRevenue"]["perTier"], "EXACT", "per ticket x the tickets issued at the cut", None, "lamports"),
            "negative": bool(recommendation["netRevenue"].get("negative", False)),
        },
        "sellThroughObserved": num(
            recommendation.get("sellThroughObserved"), "FIXTURE", "issuedCount / totalSupply at the cut", "A14"
        )
        if recommendation.get("sellThroughObserved") is not None
        else None,
    }


def _market(
    tier: Mapping,
    features: Mapping,
    intensity: Mapping,
    sales: int,
    at_ceiling: int,
    events: int,
    event_tickets: int,
) -> dict:
    marks = tier["marks"]
    basis = f"{len(marks)} sales in this tier, {events} events with resale"
    markups = sorted(mark["markupBps"] for mark in marks)
    median = None
    if markups:
        mid = len(markups) // 2
        median = markups[mid] if len(markups) % 2 else (markups[mid - 1] + markups[mid]) / 2
    mean = (sum(markups) / len(markups)) if markups else None
    # Zero sales: the number is the posterior mean of a declared prior, so it may not be
    # badged as a fixture measurement and its basis must name the prior it came from.
    # That is the difference between a rate and a prior dressed as one.
    prior_rate = intensity.get("basis") == "gamma_poisson_posterior"
    if prior_rate:
        rate_badge = "DECLARED"
        rate_basis = (
            f"0 sales over {intensity['exposureTicketDays']:.1f} ticket-days at risk; "
            "posterior mean of the declared Gamma(1, 1) prior on the transaction rate"
        )
    else:
        rate_badge = "FIXTURE"
        rate_basis = f"{intensity['sales']} sales over {intensity['exposureTicketDays']:.1f} ticket-days at risk"
    return {
        "medianMarkupBps": None if median is None else num(median, "FIXTURE", basis, "A1", "bps"),
        "meanMarkupBps": None if mean is None else num(mean, "FIXTURE", basis, "A1", "bps"),
        "sales": county(len(marks), sales, at_ceiling, events, "A1"),
        "atCeilingCount": county(tier["atCeilingCount"], sales, at_ceiling, events, "A16"),
        "salesPerTicketDay": None
        if intensity.get("salesPerTicketDay") is None
        else num(
            intensity["salesPerTicketDay"],
            rate_badge,
            rate_basis,
            "A1_ZERO" if prior_rate else "A1",
            "sales per ticket-day",
        ),
        "per1000TicketDays": None
        if intensity.get("per1000TicketDays") is None
        else num(
            intensity["per1000TicketDays"],
            rate_badge,
            rate_basis,
            "A1_ZERO" if prior_rate else "A1",
            "per 1,000 ticket-days",
        ),
        "salesPerTicketDayIsPrior": prior_rate,
        "eventSales": county(sales, sales, at_ceiling, events, "A1"),
        "eventTickets": num(
            event_tickets,
            "FIXTURE",
            f"tickets with an issue row at or before the cut",
            "A1",
        ),
        "exposureTicketDays": num(
            intensity["exposureTicketDays"], "FIXTURE", f"{intensity['sales']} sales over this denominator", "A1", "ticket-days"
        ),        "causeSpecific": {
            name: county(count, sales, at_ceiling, events, "A9") for name, count in intensity["causeSpecific"].items()
        },
        "repeatSale": _repeat_sale(features),
    }


def _repeat_sale(features: Mapping) -> dict | None:
    """A18 when one ticket sold twice. One pair is a fact, not an index."""
    by_ticket: dict[str, list[dict]] = {}
    for tier in features["tiers"]:
        for mark in tier["marks"]:
            by_ticket.setdefault(mark["ticketId"], []).append(mark)
    for ticket_id, marks in sorted(by_ticket.items()):
        if len(marks) >= 2:
            first, second = marks[0], marks[1]
            days = (second["daysToEvent"] - first["daysToEvent"]) * -1.0
            return {
                "ticketId": ticket_id,
                "p1Lamports": num(first["priceLamports"], "FIXTURE", f"ticket {ticket_id}, first sale", "A18", "lamports"),
                "p2Lamports": num(second["priceLamports"], "FIXTURE", f"ticket {ticket_id}, second sale", "A18", "lamports"),
                "days": num(days, "FIXTURE", f"ticket {ticket_id}, between its two sales", "A18", "days"),
                "labelId": "A18",
            }
    return None


def _path(path: Mapping, sales: int, at_ceiling: int, events: int) -> dict:
    basis = f"{sales} sales, {at_ceiling} at the ceiling, {events} events with resale"
    return {
        "available": path["available"],
        "fitted": path.get("fitted", False),
        "reason": path["reason"],
        "labelId": path["labelId"],
        "theta": None
        if path.get("theta") is None
        else num(path["theta"], "UNVALIDATED", basis, "A8", "log units per log day"),
        "identification": path["identification"],
        "spreadDays": num(path.get("spreadDays"), "FIXTURE", basis, "A8", "days"),
        "supportDays": None
        if not path.get("supportDays")
        else [
            num(path["supportDays"][0], "FIXTURE", basis, "A8", "days"),
            num(path["supportDays"][1], "FIXTURE", basis, "A8", "days"),
        ],
        "anchorLamports": num(
            path["anchorLamports"], "UNVALIDATED", "the tier's most recent recorded price", "A8", "lamports"
        ),
        "points": [
            {
                "days": num(row["days"], "DECLARED", "a declared horizon, not an estimate", "A8", "days"),
                "lamportsLower": None
                if row["lamportsLower"] is None
                else num(row["lamportsLower"], "UNVALIDATED", basis, "A8", "lamports"),
                "lamportsUpper": None
                if row["lamportsUpper"] is None
                else num(row["lamportsUpper"], "UNVALIDATED", basis, "A8", "lamports"),
                "outsideSupport": row["outsideSupport"],
            }
            for row in path["points"]
        ],
    }


def _refusals(chosen: Mapping | None, pooled: Mapping, fee_present: bool = False) -> list[dict]:
    """The refused block: always present, never empty, each line naming the missing observation."""
    lines = [
        {"code": "not_identified", "labelId": "A15", "reason": None},
        {"code": "no_demand_response", "labelId": "no_demand_response", "reason": None},
    ]
    if not fee_present:
        # Only when no fee is configured. With a fee the net line is computed and rendered,
        # so printing "no fee model is configured" beside it was false on its face.
        lines.append({"code": "no_fee_model", "labelId": "no_fee_model", "reason": None})
    if chosen is not None:
        path = chosen["path"]
        lines.append({"code": path["reason"] or "path_answered", "labelId": path["labelId"], "reason": path["reason"]})
        if chosen["recommendation"]["noUpperBound"]:
            lines.append({"code": "no_upper_bound", "labelId": "no_upper_bound", "reason": None})
        if chosen["recommendation"].get("refusalCode") == "recommendation_above_cap":
            # The cap the page carries sits below the price this record supports, so the
            # recommendation is refused and the panel says why, in the same sentence the
            # decision block prints.
            lines.append(
                {"code": "recommendation_above_cap", "labelId": "recommendation_above_cap", "reason": None}
            )
        if chosen["band"].get("refusalCode") == "before_on_sale_no_pool":
            lines.append(
                {"code": "before_on_sale_no_pool", "labelId": "before_on_sale_no_pool", "reason": "nothing_to_pool"}
            )
    if int(pooled.get("eventsWithResale", 0)) < 9:
        lines.append({"code": "insufficient_events", "labelId": "A17", "reason": None})
    return lines


def _labels_shown(chosen: Mapping | None) -> list[str]:
    ids = ["T1", "T2", "T3", "T4", "T5", "A15"]
    if chosen is not None:
        ids.extend(chosen["band"]["extraLabelIds"])
        ids.extend(chosen["recommendation"]["extraLabelIds"])
        ids.append(chosen["band"]["labelId"])
        ids.append(chosen["recommendation"]["labelId"])
        ids.append(chosen["path"]["labelId"])
    return sorted(set(ids))

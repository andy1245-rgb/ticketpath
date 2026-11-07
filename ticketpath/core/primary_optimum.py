"""The recommendation: a boundary, an exact consequence table, and four refusals.

There is no code path here that returns an interior optimum, and that is not modesty.
`T4b`/`T5` say the primary demand response is not identified from this record, so the
best price is a boundary question: the highest price at which the house still fills on
the evidence available (02-d sections 2.4 and 6, no-elasticity branch). A grid search
over a demand curve the engine does not have would be a fabricated likelihood with a
maximum on top of it, so there is no grid.

What the engine adds instead is exact arithmetic that carries no uncertainty: for any
candidate price, the sell-through the tier would have to achieve to match the revenue
it observes now, `face * sellThrough / candidate`. That is a definition, it is badged
`[EXACT]`, and it is not a forecast.

By regime, in this order: no resale refuses outright; capped-and-binding recommends the
floor and says "at least", with no upper end (`02-b` section 3.4); everything else
recommends the level inside its band. A level that came only from the prior is refused,
because a prior is not a record and may not be printed as a primary price
(`02-e` section 6.2(4)).

One rule sits across all of them: the cap in force on the page is a hard ceiling on the
recommendation (`face * (10000 + cap) // 10000`, the same integer arithmetic the store
uses). A cap below the price this record supports is refused with a typed reason, because
the recommendation would then be a number the policy forbids -- and the ceiling is not
printed in its place, since the cap is a floor on value, not a target for a primary price.
"""

from __future__ import annotations

from typing import Mapping, Sequence

INTERIOR_REQUIRED_INPUTS = ("eta", "q_min", "a completed sell-through series")


def _tier(features: Mapping, tier_id: str) -> dict:
    for row in features["tiers"]:
        if row["tierId"] == tier_id:
            return row
    raise KeyError(f"unknown tier {tier_id!r}")


def _consequence(face: int, sell_through: float, candidates: Sequence[int]) -> list[dict]:
    """Sell-through required at each candidate price to hold observed per-seat revenue.

    `required = face * sellThrough / candidate` at a per-seat level: the observed
    revenue per offered seat, divided by the candidate price. Exact, no uncertainty.
    """
    per_seat = face * sell_through
    rows = []
    for candidate in candidates:
        if candidate <= 0:
            continue
        rows.append(
            {
                "candidateLamports": candidate,
                "requiredSellThrough": per_seat / candidate,
                "observedRevenuePerSeatLamports": per_seat,
            }
        )
    return rows


def recommend(
    *,
    features: Mapping,
    tier_id: str,
    band: Mapping,
    intensity: Mapping,
    fee: Mapping | None,
    sell_through_floor: float | None,
    cap_bps_candidate: int | None = None,
    candidates: Sequence[int] | None = None,
) -> dict:
    row = _tier(features, tier_id)
    face = row["faceValueLamports"]
    regime = band["regime"]
    refusals: list[dict] = [
        {
            "code": "no_demand_response",
            "requiredInputs": list(INTERIOR_REQUIRED_INPUTS),
            "labelId": "no_demand_response",
        }
    ]

    if regime == "no_resale":
        return {
            "refused": True,
            "regime": regime,
            "recommendedLamports": None,
            "recommendedIsFloor": False,
            "bandLamports": [None, None],
            "noUpperBound": False,
            "basis": "no_resale_record",
            "refusalCode": "no_resale_record",
            "requiredInputs": ["a completed resale on this event"],
            "refusals": refusals
            + [
                {
                    "code": "no_resale_record",
                    "requiredInputs": ["a completed resale on this event"],
                    "labelId": "no_resale_record",
                }
            ],
            "consequence": [],
            "netRevenue": None,
            "sellThroughFloor": sell_through_floor,
            "labelId": "no_resale_record",
            "extraLabelIds": ["A13", "A17"],
        }

    if regime == "capped_and_binding":
        floor = band["floorLamports"]
        recommended = floor
        band_lo, band_hi = floor, None
        basis = "lower_bound_at_cap"
        label = "A19"
        is_floor = True
        refused = False
        refusal_code = None
    elif band["level"]["available"]:
        recommended = band["level"]["lamports"]
        band_lo, band_hi = band["band"]["loLamports"], band["band"]["hiLamports"]
        basis = band["level"]["basis"]
        label = "A2"
        is_floor = False
        refused = False
        refusal_code = None
    else:  # a prior-only level: not a record, so not a price
        return {
            "refused": True,
            "regime": regime,
            "recommendedLamports": None,
            "recommendedIsFloor": False,
            "bandLamports": [None, None],
            "noUpperBound": False,
            "basis": "prior_only",
            "refusalCode": "no_resale_record",
            "requiredInputs": ["a completed resale on this tier or this event"],
            "refusals": refusals
            + [
                {
                    "code": "no_resale_record",
                    "requiredInputs": ["a completed resale on this tier or this event"],
                    "labelId": "no_resale_record",
                }
            ],
            "consequence": [],
            "netRevenue": None,
            "sellThroughFloor": sell_through_floor,
            "labelId": "no_resale_record",
            "extraLabelIds": ["A13", "A17"],
        }

    # The cap in force is a rule on the recommendation, not only on the recorded sales. It
    # is the same integer ceiling the store uses, `face * (10000 + cap) // 10000`, and when
    # it sits below the price this record supports, the recommendation is a price the policy
    # forbids. The ceiling is not offered in its place: a cap is a ceiling on the resale
    # price and a floor on value, never a target for the primary price (A10). So the engine
    # refuses with a typed reason instead of printing a number the cap forbids.
    if cap_bps_candidate is not None:
        candidate_ceiling = face * (10000 + int(cap_bps_candidate)) // 10000
        if recommended > candidate_ceiling:
            return {
                "refused": True,
                "regime": regime,
                "recommendedLamports": None,
                "recommendedIsFloor": False,
                "bandLamports": [None, None],
                "noUpperBound": False,
                "basis": "cap_below_recommendation",
                "refusalCode": "recommendation_above_cap",
                "requiredInputs": ["a cap at or above the price this record supports"],
                "refusals": refusals
                + [
                    {
                        "code": "recommendation_above_cap",
                        "requiredInputs": ["a cap at or above the price this record supports"],
                        "labelId": "recommendation_above_cap",
                    }
                ],
                "consequence": [],
                "netRevenue": None,
                "sellThroughFloor": sell_through_floor,
                "candidateCapBps": int(cap_bps_candidate),
                "candidateCeilingLamports": candidate_ceiling,
                "labelId": "recommendation_above_cap",
                "extraLabelIds": ["A10"],
            }

    sell_through = float(row["sellThrough"])
    chosen = list(candidates) if candidates else [recommended, face]
    if recommended not in chosen:
        chosen.insert(0, recommended)

    if fee is None:
        net_revenue = None
        refusals.append(
            {"code": "no_fee_model", "requiredInputs": ["perTicketLamports or adValoremBps"], "labelId": "no_fee_model"}
        )
    else:
        # Integer arithmetic, because this is money. The ad-valorem part is rounded half up
        # on the integer product, so a one-lamport price cannot drift into a different net
        # through a float round-trip.
        ad_valorem = int(fee.get("adValoremBps", 0) or 0)
        gross = (recommended * (10000 - ad_valorem) + 5000) // 10000
        per_ticket = gross - int(fee.get("perTicketLamports", 0) or 0)
        net_revenue = {
            "perTicket": per_ticket,
            "perTier": per_ticket * int(row["issuedCount"]),
            "fee": dict(fee),
            "negative": per_ticket < 0,
        }

    return {
        "refused": refused,
        "regime": regime,
        "recommendedLamports": recommended,
        "recommendedIsFloor": is_floor,
        "bandLamports": [band_lo, band_hi],
        "noUpperBound": regime == "capped_and_binding",
        "basis": basis,
        "refusalCode": refusal_code,
        "requiredInputs": [],
        "refusals": refusals,
        "consequence": _consequence(face, sell_through, [int(value) for value in chosen]),
        "sellThroughObserved": sell_through,
        "netRevenue": net_revenue,
        "labelId": label,
        "extraLabelIds": ["A14"] if regime != "capped_and_binding" else ["A19", "T2"],
    }

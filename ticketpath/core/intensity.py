"""The composite transaction intensity: the one rate this record identifies.

It is *not* a sale hazard and it is not a probability. Every ticket-day counts in the
denominator whether or not the ticket was ever offered, so the object is the rate of a
composite process -- offered, then bought -- marginalised over the unrecorded offering
state (02-c sections 1.2 and 1.3). The name is on the field, the label is A1, and the
page prints A1 and T4 next to the number. A reader who plugs it into
`1 - exp(-rate * horizon)` will be told the probability their ticket sells, which it
does not answer, which is why the ban exists.

The exposure denominator is built from the raw `issue` and `redeem` rows in
`price_features`, never from `Ticket.redeemedAt`: that is a current-state field and a
cut cannot act on it (03-b section 4 T2).

At zero sales the zero is evidence, not missing data (02-c section 6.1): the estimate
is the gamma-Poisson posterior mean `a / (b + E)`, not the prior mean `a / b`. The
prior `a, b` is declared, and it is declared in this file rather than fitted, because
there is nothing on this platform to fit it to.
"""

from __future__ import annotations

from typing import Mapping, Sequence

GAMMA_PRIOR = {"a": 1.0, "b": 1.0}  # Gamma(a, b) on lambda in transactions per ticket-day
COMPETING_RISKS = ("sale", "transfer", "redeem", "revoke")
EVENTS_FOR_DISPERSION = 3  # 03-b section 6.4: below this the word is `insufficient`

OBJECT_NAME = "composite transaction intensity: offered, then bought"


def _tier(features: Mapping, tier_id: str) -> dict:
    for row in features["tiers"]:
        if row["tierId"] == tier_id:
            return row
    raise KeyError(f"unknown tier {tier_id!r}")


def estimate(*, features: Mapping, tier_id: str, prior: Mapping | None = None, pool: Sequence[Mapping] | None = None) -> dict:
    """The rate, its exact denominator, and the competing exits."""
    row = _tier(features, tier_id)
    sales = len(row["marks"])
    exposure = float(row["exposureTicketDays"])
    exits = {name: int(row["exits"].get(name, 0)) for name in COMPETING_RISKS}
    events_with_resale = sum(1 for entry in (pool or []) if entry.get("n", 0) >= 1)
    dispersion = "available" if events_with_resale >= EVENTS_FOR_DISPERSION else "insufficient"

    if exposure <= 0.0:
        return {
            "available": False,
            "reason": "no_exposure",
            "objectName": OBJECT_NAME,
            "sales": sales,
            "exposureTicketDays": exposure,
            "salesPerTicketDay": None,
            "per1000TicketDays": None,
            "causeSpecific": exits,
            "basis": "no_exposure",
            "dispersion": dispersion,
            "eventsWithResale": events_with_resale,
            "labelId": "no_exposure",
        }

    if sales == 0:
        prior = prior or GAMMA_PRIOR
        rate = float(prior["a"]) / (float(prior["b"]) + exposure)
        basis = "gamma_poisson_posterior"
    else:
        rate = sales / exposure
        basis = "composite_intensity"

    return {
        "available": True,
        "reason": None,
        "objectName": OBJECT_NAME,
        "sales": sales,
        "exposureTicketDays": exposure,
        "salesPerTicketDay": rate,
        "per1000TicketDays": 1000.0 * rate,
        "causeSpecific": exits,
        "basis": basis,
        "dispersion": dispersion,
        "eventsWithResale": events_with_resale,
        "priorMeanPerTicketDay": (float((prior or GAMMA_PRIOR)["a"]) / float((prior or GAMMA_PRIOR)["b"])),
        "labelId": "A1",
        "extraLabelIds": ["T4", "not_identified"],
    }

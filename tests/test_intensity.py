"""The composite intensity: an exact denominator, competing exits, and the zero as evidence.

Ticket-days are counted by hand in the docstring of each test. The rate is `sales /
exposure` and nothing else; the zero-sale branch is the gamma-Poisson posterior mean
`a / (b + E)` with the declared prior a = b = 1, which is 1 / (1 + E).
"""

from __future__ import annotations

import datetime as dt
import unittest

from ticketpath.core import intensity, price_features

UTC = dt.timezone.utc
CUT = dt.datetime(2026, 1, 5, 0, 0, 0, tzinfo=UTC)
FACE = 1_000_000_000


def event(issued=3):
    return {
        "id": "evt",
        "name": "e",
        "city": "c",
        "status": "on_sale",
        "startsAt": "2026-02-01T00:00:00.000Z",
        "resalePriceCapBps": 1500,
        "tiers": [{"id": "t", "name": "T", "faceValueLamports": FACE, "totalSupply": 10, "issuedCount": issued}],
    }


def ticket(ticket_id):
    return {"id": ticket_id, "eventId": "evt", "tierId": "t", "mintAddress": "SYN" + ticket_id}


def row(row_id, ticket_id, kind, occurred_at, price=None):
    return {
        "id": row_id,
        "ticketId": ticket_id,
        "kind": kind,
        "fromWallet": None,
        "toWallet": "SYNw",
        "priceLamports": price,
        "signature": None,
        "slot": None,
        "occurredAt": occurred_at,
    }


ISSUES = [
    row("l1", "a", "issue", "2026-01-01T00:00:00.000Z"),
    row("l2", "b", "issue", "2026-01-02T00:00:00.000Z"),
    row("l3", "c", "issue", "2026-01-03T00:00:00.000Z"),
]


def build(ledger, tickets=None, issued=3):
    return price_features.build(
        events=[event(issued)],
        tickets=tickets or [ticket("a"), ticket("b"), ticket("c")],
        ledger=ledger,
        tier_faces={"a": FACE, "b": FACE, "c": FACE},
        event_id="evt",
        as_of=CUT,
    )


class TestDenominator(unittest.TestCase):
    """a: 4 days (01-01 to 01-05), b: 3 days, c: 2 days -> 9.0 ticket-days."""

    def test_the_denominator_is_exact_on_three_tickets(self) -> None:
        features = build(ISSUES)
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], 9.0)
        estimated = intensity.estimate(features=features, tier_id="t")
        self.assertEqual(estimated["exposureTicketDays"], 9.0)
        self.assertEqual(estimated["sales"], 0)

    def test_the_rate_is_sales_over_exposure(self) -> None:
        # one sale over 9.0 ticket-days = 0.1111 per ticket-day = 111.1 per 1,000.
        ledger = ISSUES + [row("l4", "a", "sale", "2026-01-04T00:00:00.000Z", price=1_100_000_000)]
        estimated = intensity.estimate(features=build(ledger), tier_id="t")
        self.assertEqual(estimated["sales"], 1)
        self.assertEqual(estimated["exposureTicketDays"], 9.0)
        self.assertAlmostEqual(estimated["salesPerTicketDay"], 1 / 9.0, places=12)
        self.assertAlmostEqual(estimated["per1000TicketDays"], 1000 / 9.0, places=9)

    def test_a_redeemed_ticket_stops_contributing_at_its_redeem_row(self) -> None:
        # a is redeemed on 01-03, so it contributes 2 days: 2 + 3 + 2 = 7.0
        ledger = ISSUES + [row("l4", "a", "redeem", "2026-01-03T00:00:00.000Z")]
        features = build(ledger)
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], 7.0)

    def test_a_ticket_issued_after_the_cut_contributes_nothing(self) -> None:
        ledger = ISSUES + [row("l9", "d", "issue", "2026-01-09T00:00:00.000Z")]
        features = build(ledger, tickets=[ticket("a"), ticket("b"), ticket("c"), ticket("d")])
        self.assertEqual(features["tiers"][0]["exposureTicketDays"], 9.0)
        self.assertEqual(features["tiers"][0]["ticketsNotIssuedAtCut"], 1)

    def test_zero_exposure_is_refused_with_a_reason(self) -> None:
        features = build([], tickets=[ticket("a")], issued=0)
        features["tiers"][0]["exposureTicketDays"] = 0.0
        estimated = intensity.estimate(features=features, tier_id="t")
        self.assertFalse(estimated["available"])
        self.assertEqual(estimated["reason"], "no_exposure")
        self.assertIsNone(estimated["salesPerTicketDay"])


class TestZeroIsEvidence(unittest.TestCase):
    def test_a_zero_over_exposure_updates_the_rate_downward(self) -> None:
        # gamma(1, 1) prior; 9 ticket-days of exposure with no transaction:
        # posterior mean = a / (b + E) = 1 / (1 + 9) = 0.1 per ticket-day, not the prior 1.0.
        features = build(ISSUES)
        estimated = intensity.estimate(features=features, tier_id="t")
        self.assertEqual(estimated["basis"], "gamma_poisson_posterior")
        self.assertAlmostEqual(estimated["salesPerTicketDay"], 0.1, places=12)
        self.assertAlmostEqual(estimated["priorMeanPerTicketDay"], 1.0, places=12)

    def test_the_object_is_named_so_it_cannot_be_read_as_a_sale_probability(self) -> None:
        estimated = intensity.estimate(features=build(ISSUES), tier_id="t")
        self.assertIn("offered, then bought", estimated["objectName"])
        self.assertEqual(estimated["labelId"], "A1")
        self.assertIn("T4", estimated["extraLabelIds"])


class TestCompetingRisks(unittest.TestCase):
    def test_each_exit_is_counted_separately(self) -> None:
        ledger = ISSUES + [
            row("l4", "a", "sale", "2026-01-04T00:00:00.000Z", price=1_100_000_000),
            row("l5", "b", "transfer", "2026-01-04T00:00:00.000Z"),
            row("l6", "c", "redeem", "2026-01-04T00:00:00.000Z"),
        ]
        estimated = intensity.estimate(features=build(ledger), tier_id="t")
        self.assertEqual(
            estimated["causeSpecific"], {"sale": 1, "transfer": 1, "redeem": 1, "revoke": 0}
        )


class TestDispersionFloor(unittest.TestCase):
    def test_below_three_events_with_a_resale_the_word_is_insufficient(self) -> None:
        pool = [{"eventId": "a", "n": 2}, {"eventId": "b", "n": 0}]
        estimated = intensity.estimate(features=build(ISSUES), tier_id="t", pool=pool)
        self.assertEqual(estimated["dispersion"], "insufficient")
        self.assertEqual(estimated["eventsWithResale"], 1)


if __name__ == "__main__":
    unittest.main()

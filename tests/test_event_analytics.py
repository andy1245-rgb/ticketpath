"""EventAnalytics over the fixture store, against arithmetic recomputed from the rows.

The point of this file is the multi-tier case: a sale on a tier that is not the
event's cheapest, priced above the cheapest face, reads as a small markup against
its own tier face and as a large one against the event's lowest face. The test
computes both numbers itself and asserts the server returns the first, so the
contract's warning is enforced rather than commented on.

Every expected value is computed from `fixtures/synthetic_store.json` by
`tests/store_arithmetic.py`; no fixture number is retyped here.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from tests import store_arithmetic as arith
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import event_analytics, ledger_entries
from ticketpath.errors import ApiError
from ticketpath.orchestrator import Orchestrator


def _orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
    )


class TestEventAnalytics(unittest.TestCase):
    def setUp(self) -> None:
        self.store = arith.load()
        self.event = arith.first_event_with_sales(self.store, minimum=3)
        self.analytics = _orchestrator().event_analytics(self.event["id"])
        self.expected = arith.event_analytics(self.store, self.event["id"])

    def test_totals(self) -> None:
        self.assertEqual(self.analytics["eventId"], self.event["id"])
        self.assertEqual(
            self.analytics["faceValueLamports"], arith.lowest_face(self.event)
        )
        for field in (
            "totalVolumeLamports",
            "saleCount",
            "avgMarkupBps",
            "medianResalePriceLamports",
            "resoldShare",
            "uniqueHolders",
        ):
            self.assertEqual(self.analytics[field], self.expected[field], field)

    def test_avg_markup_is_per_sale_and_not_derived_from_the_lowest_face(self) -> None:
        ticket, sale = arith.ticket_with_own_tier_face_above_lowest(self.store)
        face = arith.face_of(self.store, ticket)
        lowest = arith.lowest_face(arith.event(self.store, ticket["eventId"]))
        own = arith.markup_bps(sale["priceLamports"], face)
        wrong = arith.markup_bps(sale["priceLamports"], lowest)
        self.assertGreater(wrong, own, "the wrong calculation overstates this sale")

        # And on the event as a whole, the served average is the mean of per-sale
        # markups, not the mean price divided by the event's lowest face.
        prices = [row["priceLamports"] for row in arith.sales_for_event(self.store, self.event["id"])]
        if prices:
            derived = arith.half_away(
                (sum(prices) // len(prices) - arith.lowest_face(self.event)) * 10_000,
                arith.lowest_face(self.event),
            )
            self.assertEqual(self.analytics["avgMarkupBps"], self.expected["avgMarkupBps"])
            if len({tier["faceValueLamports"] for tier in self.event["tiers"]}) > 1:
                self.assertNotEqual(self.analytics["avgMarkupBps"], derived)

    def test_price_series_is_day_bucketed_ascending(self) -> None:
        series = self.analytics["priceSeries"]
        self.assertEqual(series, self.expected["priceSeries"])
        dates = [point["date"] for point in series]
        self.assertEqual(dates, sorted(dates))
        if len(series) > 1:
            self.assertLess(dates[0], dates[-1])

    def test_markup_distribution_has_all_six_buckets_in_order(self) -> None:
        buckets = self.analytics["markupDistribution"]
        self.assertEqual(
            [bucket["label"] for bucket in buckets],
            [label for label, _, _ in arith.BUCKETS],
        )
        self.assertEqual(buckets, self.expected["markupDistribution"])
        self.assertIsNone(buckets[-1]["toBps"])

    def test_top_destinations(self) -> None:
        rows = self.analytics["topDestinations"]
        self.assertEqual(rows, self.expected["topDestinations"])
        self.assertLessEqual(len(rows), 12)
        # No wallet has volunteered a region, so the field is null, not a guess.
        self.assertEqual([row["region"] for row in rows], [None] * len(rows))

    def test_event_with_no_resale_history_is_still_a_real_answer(self) -> None:
        event = arith.event_by_regime(self.store, "cold_start")
        analytics = _orchestrator().event_analytics(event["id"])
        self.assertEqual(analytics["saleCount"], 0)
        self.assertEqual(analytics["totalVolumeLamports"], 0)
        self.assertIsNone(analytics["avgMarkupBps"])
        self.assertIsNone(analytics["medianResalePriceLamports"])
        self.assertEqual(analytics["resoldShare"], 0.0)
        self.assertEqual(analytics["priceSeries"], [])
        self.assertEqual(
            [bucket["count"] for bucket in analytics["markupDistribution"]], [0, 0, 0, 0, 0, 0]
        )
        self.assertEqual(len(analytics["topDestinations"]), analytics["uniqueHolders"])

    def test_event_with_nothing_issued_answers_with_empty_lists(self) -> None:
        event = arith.event_by_regime(self.store, "nothing_issued")
        analytics = _orchestrator().event_analytics(event["id"])
        self.assertEqual(analytics["saleCount"], 0)
        self.assertEqual(analytics["resoldShare"], 0.0)
        self.assertEqual(analytics["uniqueHolders"], 0)
        self.assertEqual(analytics["topDestinations"], [])

    def test_unknown_event_is_a_404(self) -> None:
        with self.assertRaises(ApiError) as caught:
            _orchestrator().event_analytics("evt_nope")
        self.assertEqual(caught.exception.status, 404)


class TestDayBucketing(unittest.TestCase):
    def test_sales_either_side_of_midnight_utc_are_separate_buckets(self) -> None:
        entries = [
            {
                "ticketId": "tkt_x",
                "kind": "sale",
                "priceLamports": 100,
                "markupBps": 1_000,
                "occurredAt": "2026-11-02T23:59:59.999Z",
            },
            {
                "ticketId": "tkt_x",
                "kind": "sale",
                "priceLamports": 200,
                "markupBps": 2_000,
                "occurredAt": "2026-11-03T00:00:00.000Z",
            },
        ]
        series = event_analytics.price_series(entries)
        self.assertEqual([point["date"] for point in series], ["2026-11-02", "2026-11-03"])
        self.assertEqual([point["avgPriceLamports"] for point in series], [100, 200])

    def test_an_offset_timestamp_is_converted_to_utc(self) -> None:
        entries = [
            {
                "ticketId": "tkt_x",
                "kind": "sale",
                "priceLamports": 100,
                "markupBps": 0,
                "occurredAt": "2026-11-03T01:30:00.000+02:00",  # 2026-11-02T23:30Z
            }
        ]
        self.assertEqual(event_analytics.price_series(entries)[0]["date"], "2026-11-02")


class TestMarkupIsPerTicket(unittest.TestCase):
    def test_two_tiers_one_price_two_markups(self) -> None:
        raw = [
            {"id": "l1", "ticketId": "a", "kind": "sale", "priceLamports": 1_000, "occurredAt": "2026-11-01T00:00:00.000Z"},
            {"id": "l2", "ticketId": "b", "kind": "sale", "priceLamports": 1_000, "occurredAt": "2026-11-01T01:00:00.000Z"},
        ]
        entries = ledger_entries.to_entries(raw, {"a": 500, "b": 2_000})
        self.assertEqual([entry["markupBps"] for entry in entries], [10_000, -5_000])


if __name__ == "__main__":
    unittest.main()

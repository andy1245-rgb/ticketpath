"""EventAnalytics over the fixture store, against arithmetic done by hand.

The point of this file is the multi-tier case: the same four sales produce
avgMarkupBps = 563 when each sale is measured against its own tier face, and
3125 if someone divides the average price by the event's lowest face. The test
asserts both numbers and that they are different, so the contract's warning is
enforced rather than commented on.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import event_analytics, ledger_entries
from ticketpath.errors import ApiError
from ticketpath.orchestrator import Orchestrator

W4 = "FXTUREacct411111111111111111111111111111111"
W5 = "FXTUREacct511111111111111111111111111111111"
W6 = "FXTUREacct611111111111111111111111111111111"
W7 = "FXTUREacct711111111111111111111111111111111"
W8 = "FXTUREacct811111111111111111111111111111111"


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
        self.analytics = _orchestrator().event_analytics("evt_fixture_1")

    def test_totals(self) -> None:
        self.assertEqual(self.analytics["eventId"], "evt_fixture_1")
        # the cheapest tier, not a single event-wide face
        self.assertEqual(self.analytics["faceValueLamports"], 1_000_000_000)
        # 1_250_000_000 + 1_050_000_000 + 2_050_000_000 + 900_000_000
        self.assertEqual(self.analytics["totalVolumeLamports"], 5_250_000_000)
        self.assertEqual(self.analytics["saleCount"], 4)
        # (0.9, 1.05, 1.25, 2.05) SOL -> (1.05 + 1.25) / 2
        self.assertEqual(self.analytics["medianResalePriceLamports"], 1_150_000_000)
        # 3 of 4 issued ticket rows sold at least once
        self.assertEqual(self.analytics["resoldShare"], 0.75)
        self.assertEqual(self.analytics["uniqueHolders"], 4)

    def test_avg_markup_is_per_sale_and_not_derived_from_the_lowest_face(self) -> None:
        # (2500 + 500 + 250 + -1000) / 4 = 562.5 -> 563
        self.assertEqual(self.analytics["avgMarkupBps"], 563)
        # The wrong calculation: mean price 1_312_500_000 over the 1_000_000_000
        # floor face reads as +3125 bps.
        wrong = round((5_250_000_000 / 4 - 1_000_000_000) * 10_000 / 1_000_000_000)
        self.assertEqual(wrong, 3_125)
        self.assertNotEqual(self.analytics["avgMarkupBps"], wrong)

    def test_price_series_is_day_bucketed_ascending(self) -> None:
        series = self.analytics["priceSeries"]
        self.assertEqual([point["date"] for point in series], ["2026-11-02", "2026-11-03", "2026-11-04"])
        first = series[0]
        # (1_250_000_000 + 1_050_000_000) / 2
        self.assertEqual(first["avgPriceLamports"], 1_150_000_000)
        self.assertEqual(first["saleCount"], 2)
        # (2500 + 500) / 2
        self.assertEqual(first["avgMarkupBps"], 1_500)
        self.assertEqual(series[1]["avgMarkupBps"], 250)
        self.assertEqual(series[2]["avgMarkupBps"], -1_000)

    def test_markup_distribution_has_all_six_buckets_in_order(self) -> None:
        buckets = self.analytics["markupDistribution"]
        self.assertEqual(
            [bucket["label"] for bucket in buckets],
            ["At or below face", "0-25%", "25-50%", "50-100%", "100-200%", "Over 200%"],
        )
        # -1000 | 250, 500 | 2500 | none | none | none
        self.assertEqual([bucket["count"] for bucket in buckets], [1, 2, 1, 0, 0, 0])
        self.assertEqual(buckets[0]["toBps"], 1)
        self.assertIsNone(buckets[-1]["toBps"])

    def test_top_destinations(self) -> None:
        rows = self.analytics["topDestinations"]
        self.assertEqual([row["wallet"] for row in rows], [W4, W5, W6, W8])
        self.assertEqual([row["ticketCount"] for row in rows], [1, 1, 1, 1])
        self.assertEqual([row["acquiredOnSecondary"] for row in rows], [True, True, True, False])
        # No wallet has volunteered a region, so the field is null, not a guess.
        self.assertEqual([row["region"] for row in rows], [None, None, None, None])

    def test_event_with_no_resale_history_is_still_a_real_answer(self) -> None:
        analytics = _orchestrator().event_analytics("evt_fixture_2")
        self.assertEqual(analytics["saleCount"], 0)
        self.assertEqual(analytics["totalVolumeLamports"], 0)
        self.assertIsNone(analytics["avgMarkupBps"])
        self.assertIsNone(analytics["medianResalePriceLamports"])
        self.assertEqual(analytics["resoldShare"], 0.0)
        self.assertEqual(analytics["priceSeries"], [])
        self.assertEqual([bucket["count"] for bucket in analytics["markupDistribution"]], [0, 0, 0, 0, 0, 0])
        self.assertEqual(analytics["topDestinations"][0]["wallet"], W7)

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

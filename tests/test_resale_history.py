"""ResaleHistory over the fixture store, against arithmetic recomputed from the rows.

Nothing in this file retypes a fixture number. Each test picks the ticket or event it
needs by property (the first ticket with two sales, the first never resold, the first
sale on a tier that is not the cheapest) and compares the server's answer with
`tests/store_arithmetic.py`, which recomputes it a second way from the raw JSON.

If the core changes in a way that moves a number, this file fails rather than a judge.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from tests import store_arithmetic as arith
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
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


class TestResaleHistory(unittest.TestCase):
    def setUp(self) -> None:
        self.orchestrator = _orchestrator()
        self.store = arith.load()

    def test_full_trail_and_stats(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store, minimum=2)
        payload = self.orchestrator.resale_history(ticket["id"])
        self.assertEqual(payload["ticketId"], ticket["id"])
        self.assertEqual(payload["faceValueLamports"], arith.face_of(self.store, ticket))
        self.assertEqual(payload["stats"], arith.ticket_stats(self.store, ticket["id"]))

    def test_entries_are_oldest_first_and_keep_every_kind(self) -> None:
        # A trail shaped issue, priced sale, unpriced gift, priced sale: the shape
        # the demo's custody card is written for.
        shaped = [
            ticket
            for ticket in arith.tickets(self.store)
            if [row["kind"] for row in arith.entries_for(self.store, ticket["id"])]
            == ["issue", "sale", "transfer", "sale"]
        ]
        self.assertTrue(shaped)
        for ticket in shaped:
            with self.subTest(ticket=ticket["id"]):
                entries = self.orchestrator.resale_history(ticket["id"])["entries"]
                self.assertEqual([entry["kind"] for entry in entries], ["issue", "sale", "transfer", "sale"])
                raw = arith.entries_for(self.store, ticket["id"])
                self.assertEqual([entry["id"] for entry in entries], [row["id"] for row in raw])
                self.assertIsNone(entries[0]["fromWallet"])
                self.assertIsNone(entries[0]["priceLamports"])
                self.assertIsNone(entries[0]["markupBps"])
                self.assertIsNone(entries[2]["priceLamports"])
                self.assertIsNone(entries[2]["markupBps"])

    def test_markup_is_measured_against_the_tickets_own_tier_face(self) -> None:
        ticket, sale = arith.ticket_with_own_tier_face_above_lowest(self.store)
        payload = self.orchestrator.resale_history(ticket["id"])
        entry = next(item for item in payload["entries"] if item["id"] == sale["id"])
        face = arith.face_of(self.store, ticket)
        lowest = arith.lowest_face(arith.event(self.store, ticket["eventId"]))
        own = arith.markup_bps(sale["priceLamports"], face)
        wrong = arith.markup_bps(sale["priceLamports"], lowest)
        self.assertEqual(entry["markupBps"], own)
        self.assertNotEqual(entry["markupBps"], wrong)
        self.assertGreater(wrong, own, "the wrong calculation overstates this sale")

    def test_ticket_never_resold_has_no_prices(self) -> None:
        ticket = arith.first_ticket_without_sales(self.store)
        payload = self.orchestrator.resale_history(ticket["id"])
        stats = payload["stats"]
        expected = arith.ticket_stats(self.store, ticket["id"])
        self.assertEqual(stats, expected)
        self.assertEqual(stats["saleCount"], 0)
        self.assertIsNone(stats["avgMarkupBps"])
        self.assertIsNone(stats["peakPriceLamports"])
        self.assertIsNone(stats["lastPriceLamports"])
        self.assertEqual(stats["totalVolumeLamports"], 0)

    def test_ticket_by_mint_resolves_to_the_same_ticket(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store)
        by_mint = self.orchestrator.get_ticket(ticket["mintAddress"])
        by_id = self.orchestrator.get_ticket(ticket["id"])
        self.assertEqual(by_mint["id"], by_id["id"])
        self.assertEqual(by_mint["mintAddress"], ticket["mintAddress"])

    def test_ticket_totals_come_from_the_ledger(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store, minimum=2)
        payload = self.orchestrator.get_ticket(ticket["id"])
        expected = arith.ticket_totals(self.store, ticket["id"])
        for field, value in expected.items():
            self.assertEqual(payload[field], value, field)
        self.assertEqual(payload["ownerWallet"], ticket["ownerWallet"])
        self.assertEqual(payload["issuedToWallet"], ticket["issuedToWallet"])
        # Nothing is deployed, so the "actually enforced right now" flag is false.
        self.assertFalse(payload["transferRestricted"])
        self.assertTrue(payload["dataSource"]["synthetic"])

    def test_unknown_ticket_is_a_404(self) -> None:
        with self.assertRaises(ApiError) as caught:
            self.orchestrator.resale_history("tkt_does_not_exist")
        self.assertEqual(caught.exception.status, 404)
        self.assertIn("not found", caught.exception.message)

    def test_every_payload_declares_its_source(self) -> None:
        ticket = arith.first_ticket_with_sales(self.store)
        payload = self.orchestrator.resale_history(ticket["id"])
        self.assertTrue(payload["dataSource"]["synthetic"])
        self.assertIn("Not real ticket data", payload["dataSource"]["note"])


class TestEmptyLedger(unittest.TestCase):
    def test_absent_ticket_on_an_empty_store_is_404_not_a_zeroed_record(self) -> None:
        orchestrator = Orchestrator(
            LedgerAdapter.empty(), RpcAdapter.from_env("devnet"), PricingModelAdapter(), "devnet"
        )
        with self.assertRaises(ApiError) as caught:
            orchestrator.resale_history("tkt_does_not_exist")
        self.assertEqual(caught.exception.status, 404)
        self.assertFalse(orchestrator.data_source()["synthetic"])
        self.assertEqual(orchestrator.data_source()["mode"], "empty-store")


if __name__ == "__main__":
    unittest.main()

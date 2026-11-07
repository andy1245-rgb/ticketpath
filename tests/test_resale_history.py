"""ResaleHistory over the fixture store, against arithmetic done by hand.

Every expected number below is written out with its derivation. If the core
changes in a way that moves one of them, this file fails rather than a judge.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.errors import ApiError
from ticketpath.orchestrator import Orchestrator

TICKET_WITH_TWO_SALES = "tkt_fixture_0001"
TICKET_BALCONY_SALE = "tkt_fixture_0003"
TICKET_NEVER_RESOLD = "tkt_fixture_0004"
MINT_OF_BALCONY = "FXTUREmint311111111111111111111111111111111"


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

    def test_full_trail_and_stats(self) -> None:
        payload = self.orchestrator.resale_history(TICKET_WITH_TWO_SALES)
        self.assertEqual(payload["ticketId"], TICKET_WITH_TWO_SALES)
        self.assertEqual(payload["faceValueLamports"], 1_000_000_000)

        stats = payload["stats"]
        self.assertEqual(stats["saleCount"], 2)
        # issue + sale + transfer + sale: transferCount counts sale and transfer only.
        self.assertEqual(stats["transferCount"], 3)
        # (2500 + -1000) / 2 = 750
        self.assertEqual(stats["avgMarkupBps"], 750)
        self.assertEqual(stats["peakPriceLamports"], 1_250_000_000)
        self.assertEqual(stats["lastPriceLamports"], 900_000_000)
        # 1_250_000_000 + 900_000_000
        self.assertEqual(stats["totalVolumeLamports"], 2_150_000_000)
        # w1, w2, w3, w4
        self.assertEqual(stats["uniqueWallets"], 4)

    def test_entries_are_oldest_first_and_keep_every_kind(self) -> None:
        entries = self.orchestrator.resale_history(TICKET_WITH_TWO_SALES)["entries"]
        self.assertEqual([entry["kind"] for entry in entries], ["issue", "sale", "transfer", "sale"])
        self.assertEqual(
            [entry["id"] for entry in entries], ["led_0001", "led_0002", "led_0003", "led_0004"]
        )
        self.assertEqual(entries[0]["fromWallet"], None)
        self.assertIsNone(entries[0]["priceLamports"])
        self.assertIsNone(entries[0]["markupBps"])
        self.assertIsNone(entries[2]["priceLamports"])

    def test_markup_is_measured_against_the_tickets_own_tier_face(self) -> None:
        payload = self.orchestrator.resale_history(TICKET_BALCONY_SALE)
        sale = next(entry for entry in payload["entries"] if entry["kind"] == "sale")
        # 2_050_000_000 against a 2_000_000_000 balcony face is +250 bps.
        # Measured against the event's 1_000_000_000 floor face it would be +10500,
        # which is the contract's stated mistake.
        self.assertEqual(sale["markupBps"], 250)
        self.assertNotEqual(sale["markupBps"], 10_500)

    def test_ticket_never_resold_has_no_prices(self) -> None:
        payload = self.orchestrator.resale_history(TICKET_NEVER_RESOLD)
        stats = payload["stats"]
        self.assertEqual(stats["saleCount"], 0)
        self.assertEqual(stats["transferCount"], 0)  # the redeem does not count
        self.assertIsNone(stats["avgMarkupBps"])
        self.assertIsNone(stats["peakPriceLamports"])
        self.assertIsNone(stats["lastPriceLamports"])
        self.assertEqual(stats["totalVolumeLamports"], 0)
        self.assertEqual(stats["uniqueWallets"], 1)

    def test_ticket_by_mint_resolves_to_the_same_ticket(self) -> None:
        by_mint = self.orchestrator.get_ticket(MINT_OF_BALCONY)
        by_id = self.orchestrator.get_ticket(TICKET_BALCONY_SALE)
        self.assertEqual(by_mint["id"], by_id["id"])
        self.assertEqual(by_mint["mintAddress"], MINT_OF_BALCONY)

    def test_ticket_totals_come_from_the_ledger(self) -> None:
        ticket = self.orchestrator.get_ticket(TICKET_WITH_TWO_SALES)
        self.assertEqual(ticket["lastSalePriceLamports"], 900_000_000)
        self.assertEqual(ticket["transferCount"], 3)
        self.assertEqual(ticket["issuedAt"], "2026-11-01T10:00:00.000Z")
        self.assertEqual(ticket["ownerWallet"], "FXTUREacct411111111111111111111111111111111")
        self.assertFalse(ticket["transferRestricted"])
        self.assertTrue(ticket["dataSource"]["synthetic"])

    def test_unknown_ticket_is_a_404(self) -> None:
        with self.assertRaises(ApiError) as caught:
            self.orchestrator.resale_history("tkt_does_not_exist")
        self.assertEqual(caught.exception.status, 404)
        self.assertIn("not found", caught.exception.message)

    def test_every_payload_declares_its_source(self) -> None:
        payload = self.orchestrator.resale_history(TICKET_WITH_TWO_SALES)
        self.assertTrue(payload["dataSource"]["synthetic"])
        self.assertIn("Not real ticket data", payload["dataSource"]["note"])


class TestEmptyLedger(unittest.TestCase):
    def test_absent_ticket_on_an_empty_store_is_404_not_a_zeroed_record(self) -> None:
        orchestrator = Orchestrator(
            LedgerAdapter.empty(), RpcAdapter.from_env("devnet"), PricingModelAdapter(), "devnet"
        )
        with self.assertRaises(ApiError) as caught:
            orchestrator.resale_history("tkt_fixture_0001")
        self.assertEqual(caught.exception.status, 404)
        self.assertFalse(orchestrator.data_source()["synthetic"])
        self.assertEqual(orchestrator.data_source()["mode"], "empty-store")


if __name__ == "__main__":
    unittest.main()

"""The ledger adapter refuses a store that lies about itself or contradicts itself.

These are the tests that make every number above trustworthy: if the store can be
loaded with an owner that disagrees with the last custody move, the ticket stats
are describing a ticket that does not exist.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter, StoreError
from ticketpath.core import base58

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "synthetic_store.json"


def _write_temp(store: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(store, handle)
    return handle.name


class TestFixtureLoads(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LedgerAdapter.from_fixture()

    def test_mode_and_label(self) -> None:
        self.assertEqual(self.store.mode, "fixture")
        self.assertTrue(self.store.meta["synthetic"])
        self.assertIn("SYNTHETIC", self.store.label)

    def test_counts(self) -> None:
        self.assertEqual(len(list(self.store.events())), 2)
        self.assertEqual(len(list(self.store.tickets())), 5)
        self.assertEqual(len(self.store.raw_entries_for_event("evt_fixture_1")), 9)

    def test_every_key_is_marked_synthetic_and_shape_valid(self) -> None:
        keys = [ticket["mintAddress"] for ticket in self.store.tickets()]
        keys += [ticket["ownerWallet"] for ticket in self.store.tickets()]
        keys += [ticket["issuedToWallet"] for ticket in self.store.tickets()]
        for event in self.store.events():
            keys.append(self.store.organizer(event["organizerId"])["walletAddress"])
        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(key.startswith("FXTURE"), "a fixture key must announce itself")
                self.assertTrue(base58.looks_like_base58(key))
                self.assertTrue(32 <= len(key) <= 44)
                self.assertEqual(len(base58.decode(key)), 32)

    def test_no_region_is_invented(self) -> None:
        self.assertEqual(self.store.wallet_regions(), {})


class TestRefusals(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_refuses_a_store_that_does_not_declare_itself_synthetic(self) -> None:
        broken = json.loads(json.dumps(self.raw))
        broken["meta"]["synthetic"] = False
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("synthetic", str(caught.exception))

    def test_refuses_an_owner_that_disagrees_with_the_trail(self) -> None:
        broken = json.loads(json.dumps(self.raw))
        broken["tickets"][0]["ownerWallet"] = broken["tickets"][0]["issuedToWallet"]
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("ownerWallet", str(caught.exception))

    def test_refuses_a_price_on_an_unpriced_move(self) -> None:
        broken = json.loads(json.dumps(self.raw))
        broken["ledger"][2]["priceLamports"] = 500_000_000  # led_0003 is a transfer
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("price", str(caught.exception))

    def test_refuses_missing_tickets_against_issued_count(self) -> None:
        broken = json.loads(json.dumps(self.raw))
        broken["tickets"] = broken["tickets"][:-1]
        broken["ledger"] = [row for row in broken["ledger"] if row["ticketId"] != "tkt_fixture_0005"]
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("issuedCount", str(caught.exception))

    def test_refuses_a_ticket_with_no_issue_entry(self) -> None:
        broken = json.loads(json.dumps(self.raw))
        broken["ledger"] = [row for row in broken["ledger"] if row["id"] != "led_0011"]
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("issue", str(caught.exception))


class TestEmptyStore(unittest.TestCase):
    def test_empty_store_is_empty_and_not_synthetic(self) -> None:
        empty = LedgerAdapter.empty()
        self.assertEqual(empty.mode, "empty")
        self.assertFalse(empty.meta["synthetic"])
        self.assertEqual(list(empty.events()), [])
        self.assertEqual(list(empty.tickets()), [])
        self.assertIsNone(empty.ticket("tkt_fixture_0001"))
        self.assertEqual(empty.face_by_ticket(), {})


if __name__ == "__main__":
    unittest.main()

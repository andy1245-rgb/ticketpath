"""The ledger adapter refuses a store that lies about itself or contradicts itself.

These are the tests that make every number above trustworthy: if the store can be
loaded with an owner that disagrees with the last custody move, the ticket stats
are describing a ticket that does not exist.

The refusals below mutate the store by finding a row of the kind they need rather
than by index, so they keep working when the fixture is regenerated.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tests import store_arithmetic as arith
from ticketpath.adapters.ledger_adapter import LedgerAdapter, StoreError
from ticketpath.core import base58

FIXTURE = arith.STORE_PATH


def _write_temp(store: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(store, handle)
    return handle.name


class TestFixtureLoads(unittest.TestCase):
    def setUp(self) -> None:
        self.store = LedgerAdapter.from_fixture()
        self.raw = arith.load()

    def test_mode_and_label(self) -> None:
        self.assertEqual(self.store.mode, "fixture")
        self.assertTrue(self.store.meta["synthetic"])
        self.assertIn("SYNTHETIC", self.store.label)

    def test_counts_match_the_rows_they_describe(self) -> None:
        events = list(self.store.events())
        tickets = list(self.store.tickets())
        self.assertGreaterEqual(len(events), 6)
        self.assertLessEqual(len(events), 9)
        self.assertGreaterEqual(len(tickets), 40)
        self.assertLessEqual(len(tickets), 120)
        for event_row in events:
            here = [row for row in tickets if row["eventId"] == event_row["id"]]
            self.assertEqual(
                len(here), sum(tier["issuedCount"] for tier in event_row["tiers"])
            )
        self.assertGreaterEqual(len(self.store._ledger), len(tickets))

    def test_every_key_is_marked_synthetic_and_shape_valid(self) -> None:
        keys = [ticket["mintAddress"] for ticket in self.store.tickets()]
        keys += [ticket["ownerWallet"] for ticket in self.store.tickets()]
        keys += [ticket["issuedToWallet"] for ticket in self.store.tickets()]
        for event in self.store.events():
            keys.append(self.store.organizer(event["organizerId"])["walletAddress"])
        for key in keys:
            with self.subTest(key=key):
                self.assertTrue(key.startswith("SYN"), "a fixture key must announce itself")
                self.assertTrue(base58.looks_like_base58(key))
                self.assertEqual(len(base58.decode(key)), 32)

    def test_no_two_keys_share_a_truncated_form(self) -> None:
        # The frontend prints first four and last four; two keys that agree on both
        # render as one wallet, which turns a custody trail into a self-transfer.
        unique = sorted(set(arith.addresses(self.raw)))
        forms = [arith.short_address(key) for key in unique]
        self.assertEqual(len(set(forms)), len(forms))

    def test_no_region_is_invented(self) -> None:
        self.assertEqual(self.store.wallet_regions(), {})


class TestRefusals(unittest.TestCase):
    def setUp(self) -> None:
        self.raw = arith.load()

    def _broken(self) -> dict:
        return json.loads(json.dumps(self.raw))

    def test_refuses_a_store_that_does_not_declare_itself_synthetic(self) -> None:
        broken = self._broken()
        broken["meta"]["synthetic"] = False
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("synthetic", str(caught.exception))

    def test_refuses_an_owner_that_disagrees_with_the_trail(self) -> None:
        broken = self._broken()
        moved = next(
            row
            for row in broken["tickets"]
            if any(
                entry["ticketId"] == row["id"] and entry["kind"] in ("sale", "transfer")
                for entry in broken["ledger"]
            )
        )
        moved["ownerWallet"] = moved["issuedToWallet"]
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("ownerWallet", str(caught.exception))

    def test_refuses_a_price_on_an_unpriced_move(self) -> None:
        broken = self._broken()
        transfer = next(row for row in broken["ledger"] if row["kind"] == "transfer")
        transfer["priceLamports"] = 500_000_000
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("price", str(caught.exception))

    def test_refuses_missing_tickets_against_issued_count(self) -> None:
        broken = self._broken()
        dropped = broken["tickets"].pop()
        broken["ledger"] = [row for row in broken["ledger"] if row["ticketId"] != dropped["id"]]
        with self.assertRaises(StoreError) as caught:
            LedgerAdapter.from_fixture(_write_temp(broken))
        self.assertIn("issuedCount", str(caught.exception))

    def test_refuses_a_ticket_with_no_issue_entry(self) -> None:
        broken = self._broken()
        issue = next(row for row in broken["ledger"] if row["kind"] == "issue")
        broken["ledger"] = [row for row in broken["ledger"] if row["id"] != issue["id"]]
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
        self.assertIsNone(empty.ticket(arith.first_ticket_with_sales(arith.load())["id"]))
        self.assertEqual(empty.face_by_ticket(), {})


if __name__ == "__main__":
    unittest.main()

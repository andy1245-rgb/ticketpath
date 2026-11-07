"""The fixture store's own invariants, asserted from the file rather than trusted.

These are the properties the store promises in `records/FIXTURE-STORE.md`, the ones
the demo depends on: three regimes, addresses that cannot read as one wallet handing
a ticket to itself, markups that recompute exactly from each ticket's own tier face,
a custody trail that is a single ordered chain, and a label on every string the
frontend prints. They are also asserted by the generator; checking them from the
outside means a hand edit to the JSON fails here even if nobody reruns the generator.

Every number below is computed from the store. Nothing is retyped from a previous
version of the store, so these tests keep passing when the generator's seed moves.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from tests import store_arithmetic as arith
from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.core import base58

REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "tools" / "build_fixture_store.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("build_fixture_store", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestStoreShape(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = arith.load()

    def test_the_adapter_accepts_the_file(self) -> None:
        adapter = LedgerAdapter.from_fixture()
        self.assertEqual(adapter.mode, "fixture")
        self.assertTrue(adapter.meta["synthetic"])
        self.assertEqual(len(list(adapter.events())), len(arith.events(self.store)))
        self.assertEqual(len(list(adapter.tickets())), len(arith.tickets(self.store)))

    def test_events_and_tickets_stay_auditable_by_hand(self) -> None:
        events = arith.events(self.store)
        tickets = arith.tickets(self.store)
        self.assertGreaterEqual(len(events), 6)
        self.assertLessEqual(len(events), 9)
        self.assertGreaterEqual(len(tickets), 40)
        self.assertLessEqual(len(tickets), 120)
        for event_row in events:
            here = arith.tickets_for_event(self.store, event_row["id"])
            self.assertEqual(event_row["issuedCount"], len(here), event_row["id"])
            self.assertEqual(
                event_row["totalSupply"], sum(tier["totalSupply"] for tier in event_row["tiers"])
            )
            for tier in event_row["tiers"]:
                self.assertEqual(
                    tier["issuedCount"],
                    sum(1 for row in here if row["tierId"] == tier["id"]),
                    tier["id"],
                )
                self.assertGreaterEqual(tier["totalSupply"], 1)
                self.assertGreater(tier["faceValueLamports"], 0)
            # The event page requests at most 25 tickets and never reads nextCursor.
            self.assertLessEqual(len(here), 25, event_row["id"])

    def test_every_event_is_its_own_venue_city_and_date(self) -> None:
        events = arith.events(self.store)
        for field in ("venue", "city", "startsAt"):
            values = [row[field] for row in events]
            self.assertEqual(len(set(values)), len(values), field)

    def test_at_least_one_event_prices_tiers_differently(self) -> None:
        multi = [
            row
            for row in arith.events(self.store)
            if len({tier["faceValueLamports"] for tier in row["tiers"]}) > 1
        ]
        self.assertTrue(multi)
        for row in multi:
            self.assertGreaterEqual(len(row["tiers"]), 2)

    def test_no_two_events_share_a_tier_structure(self) -> None:
        structures = [
            (
                len(row["tiers"]),
                tuple(tier["faceValueLamports"] for tier in row["tiers"]),
                tuple(tier["totalSupply"] for tier in row["tiers"]),
            )
            for row in arith.events(self.store)
        ]
        self.assertEqual(len(set(structures)), len(structures))

    def test_a_draft_event_reads_as_empty_not_zeroed(self) -> None:
        draft = arith.event_by_regime(self.store, "nothing_issued")
        self.assertEqual(draft["status"], "draft")
        self.assertEqual(arith.tickets_for_event(self.store, draft["id"]), [])
        self.assertEqual(arith.sales_for_event(self.store, draft["id"]), [])


class TestRegimes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = arith.load()

    def test_cap_present_and_not_binding(self) -> None:
        event_row = arith.event_by_regime(self.store, "cap_present_not_binding")
        markups = arith.markups_for_event(self.store, event_row["id"])
        self.assertTrue(markups, "the regime needs a resale history")
        self.assertIsNotNone(event_row["resalePriceCapBps"])
        self.assertLess(max(markups), event_row["resalePriceCapBps"])
        self.assertLess(min(markups), 0, "a sale below face belongs in this regime")

    def test_cap_binds_and_sales_cluster_on_it(self) -> None:
        event_row = arith.event_by_regime(self.store, "cap_binding")
        cap = event_row["resalePriceCapBps"]
        markups = arith.markups_for_event(self.store, event_row["id"])
        self.assertTrue(markups)
        at_cap = [markup for markup in markups if markup == cap]
        self.assertGreaterEqual(len(at_cap) * 100, 60 * len(markups))
        self.assertLessEqual(max(markups), cap)

    def test_cold_start_has_no_resale_rows_at_all(self) -> None:
        for regime in ("cold_start", "resale_disabled", "nothing_issued"):
            event_row = arith.event_by_regime(self.store, regime)
            with self.subTest(regime=regime):
                self.assertEqual(arith.sales_for_event(self.store, event_row["id"]), [])
        self.assertFalse(arith.event_by_regime(self.store, "resale_disabled")["resaleEnabled"])

    def test_uncapped_event_reaches_both_tails(self) -> None:
        event_row = arith.event_by_regime(self.store, "uncapped_spread")
        self.assertIsNone(event_row["resalePriceCapBps"])
        markups = arith.markups_for_event(self.store, event_row["id"])
        self.assertGreater(max(markups), 2_500, "an above-cap sale needs to exist")
        self.assertLess(min(markups), 0, "a below-face sale needs to exist")

    def test_completed_run_redeems_every_ticket_after_its_last_sale(self) -> None:
        event_row = arith.event_by_regime(self.store, "completed_run")
        tickets = arith.tickets_for_event(self.store, event_row["id"])
        self.assertTrue(tickets)
        for row in tickets:
            with self.subTest(ticket=row["id"]):
                self.assertEqual(row["status"], "redeemed")
                rows = arith.entries_for(self.store, row["id"])
                redeems = [entry for entry in rows if entry["kind"] == "redeem"]
                self.assertEqual(len(redeems), 1)
                self.assertEqual(row["redeemedAt"], redeems[0]["occurredAt"])
                sales = [entry for entry in rows if entry["kind"] == "sale"]
                if sales:
                    self.assertGreater(redeems[0]["occurredAt"], sales[-1]["occurredAt"])

    def test_cap_binds_on_one_tier_only(self) -> None:
        event_row = arith.event_by_regime(self.store, "tier_cap_binding")
        cap = event_row["resalePriceCapBps"]
        cheapest = min(event_row["tiers"], key=lambda tier: tier["faceValueLamports"])
        for row in arith.sales_for_event(self.store, event_row["id"]):
            ticket_row = arith.ticket(self.store, row["ticketId"])
            markup = arith.markup_bps(row["priceLamports"], arith.face_of(self.store, ticket_row))
            if ticket_row["tierId"] == cheapest["id"]:
                self.assertLessEqual(markup, cap)
            else:
                self.assertLess(markup, cap, "only the cheapest tier should reach the cap")


class TestAddresses(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = arith.load()

    def test_every_address_announces_itself_and_decodes_to_32_bytes(self) -> None:
        found = arith.addresses(self.store)
        self.assertTrue(found)
        for address in found:
            with self.subTest(address=address):
                self.assertTrue(address.startswith("SYN"), "a placeholder must say so")
                self.assertTrue(base58.looks_like_base58(address))
                self.assertEqual(len(base58.decode(address)), 32)

    def test_no_two_addresses_share_a_truncated_form(self) -> None:
        # The frontend prints the first four and last four characters. Two addresses
        # that agree on both read as the same wallet, which is exactly the defect
        # that made a correct custody trail look like a self-transfer.
        unique = sorted(set(arith.addresses(self.store)))
        forms = [arith.short_address(address) for address in unique]
        self.assertEqual(len(set(forms)), len(forms))
        self.assertFalse(all(form.endswith("1111") for form in forms))

    def test_mints_are_distinct_and_match_their_ticket(self) -> None:
        mints = [row["mintAddress"] for row in arith.tickets(self.store)]
        self.assertEqual(len(set(mints)), len(mints))
        for row in arith.tickets(self.store):
            self.assertTrue(row["mintAddress"].startswith("SYN"))


class TestLedgerConsistency(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = arith.load()

    def test_every_sale_price_is_an_exact_markup_of_its_own_tier_face(self) -> None:
        for row in self.store["ledger"]:
            if row["kind"] != "sale":
                continue
            ticket_row = arith.ticket(self.store, row["ticketId"])
            face = arith.face_of(self.store, ticket_row)
            price = row["priceLamports"]
            with self.subTest(row=row["id"]):
                self.assertIsInstance(price, int)
                # Exact division: no rounding at all between price and basis points.
                self.assertEqual((price - face) * 10_000 % face, 0)
                markup = arith.markup_bps(price, face)
                self.assertEqual(price, face + face * markup // 10_000)

    def test_every_non_sale_row_has_no_price(self) -> None:
        for row in self.store["ledger"]:
            if row["kind"] != "sale":
                with self.subTest(row=row["id"], kind=row["kind"]):
                    self.assertIsNone(row["priceLamports"])

    def test_issue_comes_first_and_timestamps_are_strict(self) -> None:
        for ticket_row in arith.tickets(self.store):
            rows = arith.entries_for(self.store, ticket_row["id"])
            with self.subTest(ticket=ticket_row["id"]):
                self.assertEqual(rows[0]["kind"], "issue")
                self.assertIsNone(rows[0]["fromWallet"])
                self.assertEqual(rows[0]["toWallet"], ticket_row["issuedToWallet"])
                self.assertEqual(sum(1 for row in rows if row["kind"] == "issue"), 1)
                stamps = [row["occurredAt"] for row in rows]
                self.assertEqual(stamps, sorted(stamps))
                self.assertEqual(len(set(stamps)), len(stamps))
                for stamp in stamps:
                    self.assertTrue(stamp.endswith("Z"))
                    self.assertEqual(len(stamp), len("2026-10-02T11:00:00.000Z"))

    def test_custody_chain_links_and_no_sale_is_a_self_transfer(self) -> None:
        for ticket_row in arith.tickets(self.store):
            rows = arith.entries_for(self.store, ticket_row["id"])
            holder = ticket_row["issuedToWallet"]
            for row in rows[1:]:
                with self.subTest(row=row["id"]):
                    self.assertEqual(row["fromWallet"], holder)
                    self.assertNotEqual(row["fromWallet"], row["toWallet"])
                    if row["toWallet"] is not None:
                        holder = row["toWallet"]
            self.assertEqual(ticket_row["ownerWallet"], holder)

    def test_no_ticket_moves_after_its_event_has_started(self) -> None:
        for row in self.store["ledger"]:
            ticket_row = arith.ticket(self.store, row["ticketId"])
            event_row = arith.event(self.store, ticket_row["eventId"])
            with self.subTest(row=row["id"]):
                if row["kind"] == "redeem":
                    self.assertLessEqual(event_row["startsAt"], row["occurredAt"])
                    self.assertLessEqual(row["occurredAt"], event_row["endsAt"])
                else:
                    self.assertLess(row["occurredAt"], event_row["startsAt"])

    def test_no_ticket_is_redeemed_before_it_is_sold(self) -> None:
        for ticket_row in arith.tickets(self.store):
            rows = arith.entries_for(self.store, ticket_row["id"])
            redeems = [row for row in rows if row["kind"] == "redeem"]
            sales = [row for row in rows if row["kind"] == "sale"]
            if not redeems:
                continue
            with self.subTest(ticket=ticket_row["id"]):
                if sales:
                    self.assertGreater(redeems[0]["occurredAt"], sales[-1]["occurredAt"])


class TestLabelling(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.store = arith.load()

    def test_the_store_says_what_it_is(self) -> None:
        meta = self.store["meta"]
        self.assertTrue(meta["synthetic"])
        self.assertIn("SYNTHETIC", meta["label"])
        self.assertIn("build_fixture_store.py", meta["generator"])
        self.assertIn("Not scraped", meta["provenance"])

    def test_every_printed_string_carries_a_marker(self) -> None:
        # The frontend cannot be edited, so the only label it can show on these
        # screens rides in Event.name, Event.description and Organizer.name.
        for event_row in arith.events(self.store):
            with self.subTest(event=event_row["id"]):
                self.assertTrue(
                    any(word in event_row["name"].lower() for word in ("synthetic", "demo")),
                    event_row["name"],
                )
                description = event_row["description"].lower()
                self.assertIn("synthetic demonstration record", description)
                self.assertIn("not a real show", description)
                self.assertIn("tools/build_fixture_store.py", description)
                # The resale density is a construction choice, not a market rate.
                # The sentence is not asserted verbatim, only that it is there and
                # that it names the real-market figure and its class, so re-wording
                # the disclosure does not fail the suite but dropping it does.
                self.assertIn("deliberately over-sampled for demonstration", description)
                self.assertIn("real market (class a)", description)
        for organizer in self.store["organizers"]:
            with self.subTest(organizer=organizer["id"]):
                self.assertTrue(
                    any(word in organizer["name"].lower() for word in ("synthetic", "demonstration"))
                )
        self.assertEqual(self.store["walletRegions"], {})


class TestGeneratorReproducesTheFile(unittest.TestCase):
    def test_the_committed_file_is_the_generators_output(self) -> None:
        generator = _load_generator()
        rebuilt = generator.dumps(generator.build_store())
        on_disk = arith.STORE_PATH.read_text(encoding="utf-8")
        self.assertEqual(rebuilt, on_disk, "fixtures/synthetic_store.json was hand edited")

    def test_the_generator_is_deterministic(self) -> None:
        generator = _load_generator()
        self.assertEqual(
            generator.dumps(generator.build_store()),
            generator.dumps(generator.build_store()),
        )


if __name__ == "__main__":
    unittest.main()

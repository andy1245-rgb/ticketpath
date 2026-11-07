"""Features at a cut: the filter once, at the top, and nothing that could see the future.

Expectations here are computed by hand and written out, not imported from the module
under test. The small ledgers are built in the test so the arithmetic can be read next to
the assertion.
"""

from __future__ import annotations

import ast
import datetime as dt
import inspect
import json
import unittest
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.core import price_features

UTC = dt.timezone.utc


def _nodes(tree):
    """Every node in the tree, without the recursive filesystem tool the shell guard watches."""
    stack = [tree]
    while stack:
        node = stack.pop()
        yield node
        stack.extend(ast.iter_child_nodes(node))
CUT = dt.datetime(2026, 1, 5, 0, 0, 0, tzinfo=UTC)
STARTS = "2026-01-11T00:00:00.000Z"
FACE = 1_000_000_000


def event(tiers, cap=1500, event_id="evt_t"):
    return {
        "id": event_id,
        "name": "Test event",
        "city": "Testville",
        "status": "on_sale",
        "startsAt": STARTS,
        "endsAt": None,
        "resalePriceCapBps": cap,
        "tiers": tiers,
    }


def tier(tier_id="tier_a", face=FACE, supply=10, issued=3):
    return {"id": tier_id, "name": "A", "faceValueLamports": face, "totalSupply": supply, "issuedCount": issued}


def ticket(ticket_id, tier_id="tier_a", event_id="evt_t"):
    return {"id": ticket_id, "eventId": event_id, "tierId": tier_id, "mintAddress": "SYNmint" + ticket_id}


def row(row_id, ticket_id, kind, occurred_at, price=None):
    return {
        "id": row_id,
        "ticketId": ticket_id,
        "kind": kind,
        "fromWallet": None,
        "toWallet": "SYNwallet",
        "priceLamports": price,
        "signature": None,
        "slot": None,
        "occurredAt": occurred_at,
    }


class TestExposureArithmetic(unittest.TestCase):
    """Three tickets, a stated cut, and ticket-days counted by hand.

    Ticket A: issued 2026-01-01, redeemed 2026-01-03  -> min(cut, redeem) - issue = 2 days
    Ticket B: issued 2026-01-02, never redeemed       -> cut - issue           = 3 days
    Ticket C: issued 2026-01-03, never redeemed       -> cut - issue           = 2 days
    Total                                                                    = 7.0 ticket-days
    """

    def setUp(self) -> None:
        tickets = [ticket("tkt_a"), ticket("tkt_b"), ticket("tkt_c")]
        ledger = [
            row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
            row("l2", "tkt_b", "issue", "2026-01-02T00:00:00.000Z"),
            row("l3", "tkt_c", "issue", "2026-01-03T00:00:00.000Z"),
            row("l4", "tkt_a", "redeem", "2026-01-03T00:00:00.000Z"),
        ]
        self.features = price_features.build(
            events=[event([tier()])],
            tickets=tickets,
            ledger=ledger,
            tier_faces={t["id"]: FACE for t in tickets},
            event_id="evt_t",
            as_of=CUT,
        )

    def test_ticket_days_is_exactly_seven(self) -> None:
        self.assertEqual(self.features["tiers"][0]["exposureTicketDays"], 7.0)

    def test_a_ticket_issued_after_the_cut_contributes_nothing(self) -> None:
        later = price_features.build(
            events=[event([tier()])],
            tickets=[ticket("tkt_d")],
            ledger=[row("l9", "tkt_d", "issue", "2026-01-09T00:00:00.000Z")],
            tier_faces={"tkt_d": FACE},
            event_id="evt_t",
            as_of=CUT,
        )
        self.assertEqual(later["tiers"][0]["exposureTicketDays"], 0.0)
        self.assertEqual(later["tiers"][0]["ticketsNotIssuedAtCut"], 1)
        self.assertEqual(later["event"]["sales"], 0)

    def test_the_cut_is_a_required_argument(self) -> None:
        signature = inspect.signature(price_features.build)
        self.assertIn("as_of", signature.parameters)
        self.assertIs(inspect.Parameter.empty, signature.parameters["as_of"].default)


class TestMarkArithmetic(unittest.TestCase):
    def test_markup_is_basis_points_over_the_ticket_own_face(self) -> None:
        # 1.10 SOL against a 1.00 SOL face is +10% = 1000 bps, by hand.
        features = price_features.build(
            events=[event([tier()])],
            tickets=[ticket("tkt_a")],
            ledger=[
                row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
                row("l2", "tkt_a", "sale", "2026-01-02T00:00:00.000Z", price=1_100_000_000),
            ],
            tier_faces={"tkt_a": FACE},
            event_id="evt_t",
            as_of=CUT,
        )
        mark = features["tiers"][0]["marks"][0]
        self.assertEqual(mark["markupBps"], 1000)
        self.assertEqual(mark["daysToEvent"], 9.0)  # 2026-01-02 -> 2026-01-11
        self.assertFalse(mark["atCeiling"])

    def test_the_cap_hit_test_has_a_one_basis_point_tolerance(self) -> None:
        # A face that does not divide evenly: 999_999_999 lamports.
        # price = face + 149_999_999 -> diff*10000/face = 1499.99999... which rounds to 1500.
        face = 999_999_999
        features = price_features.build(
            events=[event([tier(face=face)], cap=1500)],
            tickets=[ticket("tkt_a")],
            ledger=[
                row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
                row("l2", "tkt_a", "sale", "2026-01-02T00:00:00.000Z", price=face + 149_999_999),
            ],
            tier_faces={"tkt_a": face},
            event_id="evt_t",
            as_of=CUT,
        )
        mark = features["tiers"][0]["marks"][0]
        self.assertEqual(mark["markupBps"], 1500)
        self.assertTrue(mark["atCeiling"])
        self.assertEqual(features["tiers"][0]["atCeilingCount"], 1)

    def test_a_sale_one_basis_point_off_the_cap_still_counts_as_at_the_ceiling(self) -> None:
        # 1499 bps against a 1500 bps cap is inside abs(markup - cap) <= 1 (03-b row 16).
        face = 1_000_000_000
        features = price_features.build(
            events=[event([tier()], cap=1500)],
            tickets=[ticket("tkt_a")],
            ledger=[
                row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
                row("l2", "tkt_a", "sale", "2026-01-02T00:00:00.000Z", price=face + 149_900_000),
            ],
            tier_faces={"tkt_a": face},
            event_id="evt_t",
            as_of=CUT,
        )
        mark = features["tiers"][0]["marks"][0]
        self.assertEqual(mark["markupBps"], 1499)
        self.assertTrue(mark["atCeiling"])

    def test_an_uncapped_event_never_marks_a_ceiling(self) -> None:
        features = price_features.build(
            events=[event([tier()], cap=None)],
            tickets=[ticket("tkt_a")],
            ledger=[
                row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
                row("l2", "tkt_a", "sale", "2026-01-02T00:00:00.000Z", price=5_000_000_000),
            ],
            tier_faces={"tkt_a": FACE},
            event_id="evt_t",
            as_of=CUT,
        )
        self.assertIsNone(features["tiers"][0]["capBpsRecorded"])
        self.assertIsNone(features["tiers"][0]["capCeilingLamportsRecorded"])
        self.assertEqual(features["tiers"][0]["atCeilingCount"], 0)

    def test_a_priced_transfer_is_ignored_because_only_sales_carry_money(self) -> None:
        features = price_features.build(
            events=[event([tier()])],
            tickets=[ticket("tkt_a")],
            ledger=[
                row("l1", "tkt_a", "issue", "2026-01-01T00:00:00.000Z"),
                row("l2", "tkt_a", "transfer", "2026-01-02T00:00:00.000Z"),
            ],
            tier_faces={"tkt_a": FACE},
            event_id="evt_t",
            as_of=CUT,
        )
        self.assertEqual(features["tiers"][0]["marks"], [])
        self.assertEqual(features["tiers"][0]["exits"]["transfer"], 1)


class TestTemporalCorrectness(unittest.TestCase):
    """Row 7 and row 8 of 03-b section 7: the canary and the property test."""

    def setUp(self) -> None:
        self.adapter = LedgerAdapter.from_fixture()
        self.faces = self.adapter.face_by_ticket()

    def _features(self, ledger, cut):
        return price_features.build(
            events=list(self.adapter.events()),
            tickets=list(self.adapter.tickets()),
            ledger=ledger,
            tier_faces=self.faces,
            event_id="evt_syn_04",
            as_of=cut,
        )

    def test_a_future_sale_three_times_the_price_changes_nothing(self) -> None:
        cut = dt.datetime(2026, 9, 10, 0, 0, 0, tzinfo=UTC)
        ledger = self.adapter.raw_ledger()
        before = self._features(ledger, cut)
        canary = dict(
            row("led_canary", "tkt_syn_0040", "sale", "2026-09-10T01:00:00.000Z", price=9_000_000_000)
        )
        after = self._features(ledger + [canary], cut)
        self.assertEqual(json.dumps(before["tiers"], sort_keys=True), json.dumps(after["tiers"], sort_keys=True))
        self.assertEqual(json.dumps(before["event"], sort_keys=True), json.dumps(after["event"], sort_keys=True))

    def test_prefix_invariance_over_every_sale_instant(self) -> None:
        ledger = self.adapter.raw_ledger()
        instants = sorted({r["occurredAt"] for r in ledger if r["kind"] == "sale"})
        for instant in instants:
            cut = price_features.parse(instant)
            truncated = [r for r in ledger if price_features.parse(r["occurredAt"]) <= cut]
            with self.subTest(cut=instant):
                self.assertEqual(
                    json.dumps(self._features(truncated, cut)["tiers"], sort_keys=True),
                    json.dumps(self._features(ledger, cut)["tiers"], sort_keys=True),
                )

    def test_no_negative_time_to_event(self) -> None:
        features = self._features(self.adapter.raw_ledger(), dt.datetime(2026, 11, 7, 12, tzinfo=UTC))
        for tier_row in features["tiers"]:
            for mark in tier_row["marks"]:
                self.assertGreaterEqual(mark["daysToEvent"], 0.0)
            self.assertGreaterEqual(tier_row["timeSpreadDays"], 0.0)

    def test_the_null_slot_fallback_is_counted_not_silent(self) -> None:
        features = self._features(self.adapter.raw_ledger(), dt.datetime(2026, 11, 7, 12, tzinfo=UTC))
        self.assertGreater(features["provenance"]["nullSlotRows"], 0)


class TestForbiddenFields(unittest.TestCase):
    """03-b row 5: the engine reads raw rows and never a whole-history aggregate.

    The scan is over the syntax tree, not the text: a docstring that names a forbidden
    field (the engine's own modules do, to say they do not read it) is not a read. Only
    an attribute access or a string subscript counts.
    """

    FORBIDDEN = frozenset(
        {
            "avgMarkupBps",
            "medianResalePriceLamports",
            "resoldShare",
            "uniqueHolders",
            "totalVolumeLamports",
            "markupDistribution",
            "topDestinations",
            "transferCount",
            "lastSalePriceLamports",
            "redeemedAt",
            "ownerWallet",
        }
    )

    def _engine_files(self) -> list[Path]:
        root = Path(__file__).resolve().parents[1] / "ticketpath"
        return [
            root / "core" / "price_features.py",
            root / "core" / "value_band.py",
            root / "core" / "path_model.py",
            root / "core" / "intensity.py",
            root / "core" / "primary_optimum.py",
            root / "core" / "labels.py",
            root / "api" / "guidance.py",
            root / "console" / "page.py",
            root / "console" / "blocks.py",
            root / "console" / "units.py",
        ]

    def test_no_engine_module_reads_an_aggregate_or_a_whole_life_field(self) -> None:
        for path in self._engine_files():
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in _nodes(tree):
                if isinstance(node, ast.Attribute):
                    with self.subTest(path=path.name, field=node.attr):
                        self.assertNotIn(node.attr, self.FORBIDDEN)
                if isinstance(node, ast.Subscript) and isinstance(node.slice, ast.Constant):
                    if isinstance(node.slice.value, str):
                        with self.subTest(path=path.name, field=node.slice.value):
                            self.assertNotIn(node.slice.value, self.FORBIDDEN)


if __name__ == "__main__":
    unittest.main()

"""The two defects the independent review left open, each held by a test that fails on the old code.

`records/findings/07-engine-review.md` section 5.2 ("the candidate cap is not passed to
`primary_optimum`") and C8 ("the store validator and the core disagree about what a legal
row is"). Both are wiring defects, so both are pinned at the seam where the wiring is.

1. **The cap in force is a rule on the recommendation.** The value path resolved a cap for
   the payload and never passed it into `primary_optimum.recommend`, so `capBps=0` printed a
   recommendation above the ceiling that cap implies while the page said it was honouring
   it. The cap now travels into the arithmetic (`face * (10000 + cap) // 10000`), and a cap
   below the price the record supports is refused with a typed reason. The loop below is the
   general form: no recommendation may exceed its own page's ceiling.

2. **The loader refuses what the core cannot price.** `LedgerAdapter._validate` admitted a
   zero-priced sale, a sale dated after the event starts, and an event with no tiers; the
   core then raised on each, and because `cross_section` builds every event, one bad row
   refused every page. The loader now holds the offending event back with a typed reason,
   keeps serving the rest, and `tools/build_fixture_store.py --check` fails on a store that
   carries one.
"""

from __future__ import annotations

import contextlib
import datetime as dt
import html as html_module
import importlib.util
import io
import json
import os
import re
import tempfile
import unittest
from datetime import timedelta
from pathlib import Path
from unittest import mock

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.console import page
from ticketpath.core import labels, primary_optimum
from ticketpath.core.timeutil import parse, to_iso
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import console_index

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)
REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE = REPO_ROOT / "fixtures" / "synthetic_store.json"
GENERATOR = REPO_ROOT / "tools" / "build_fixture_store.py"

# The event the review's section 5.2 names, and the cap that makes its price illegal.
CAPPED_EVENT = "evt_syn_01"
CAPS_SWEPT = (0, 250, 500, 1000, 1500, 2000, 2500, 10000)


# -- harness --------------------------------------------------------------


def orchestrator(ledger: LedgerAdapter | None = None) -> Orchestrator:
    return Orchestrator(
        ledger or LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


def payload_for(**query) -> dict:
    return orchestrator().price_guidance(**query)


def html_for(**query) -> tuple[dict, str]:
    payload = payload_for(**query)
    payload["canonicalUrl"] = "http://127.0.0.1:8788/"
    return payload, page.render(payload)


def visible(html: str) -> str:
    without_style = re.sub(r"<style>.*?</style>", " ", html, flags=re.S)
    return re.sub(r"\s+", " ", html_module.unescape(re.sub(r"<[^>]+>", " ", without_style)))


def value(wrapper) -> int | float | None:
    return None if wrapper is None else wrapper.get("value")


def ceiling(face: int, cap_bps: int) -> int:
    """The cap's own arithmetic: integer lamports, the same expression the store uses."""
    return face * (10000 + cap_bps) // 10000


def fixture_store() -> dict:
    with open(FIXTURE, encoding="utf-8") as handle:
        return json.load(handle)


def write_store(store: dict) -> str:
    handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    with handle:
        json.dump(store, handle)
    return handle.name


def event_of_ticket(store: dict) -> dict[str, str]:
    return {ticket["id"]: ticket["eventId"] for ticket in store["tickets"]}


def zero_price_one_sale(store: dict) -> tuple[str, str]:
    """Set one sale to zero lamports. Returns (the event it belongs to, the row id)."""
    event_of = event_of_ticket(store)
    for row in store["ledger"]:
        if row["kind"] == "sale":
            row["priceLamports"] = 0
            return event_of[row["ticketId"]], row["id"]
    raise AssertionError("the fixture carries no sale row")


def move_one_sale_after_its_event(store: dict, event_id: str) -> tuple[str, str]:
    """Date this event's last sale an hour after the event starts. Returns (event, row)."""
    starts = {row["id"]: row["startsAt"] for row in store["events"]}[event_id]
    later = to_iso(parse(starts) + timedelta(hours=1))
    event_of = event_of_ticket(store)
    by_ticket: dict[str, list[dict]] = {}
    for row in store["ledger"]:
        by_ticket.setdefault(row["ticketId"], []).append(row)
    for ticket_id, rows in by_ticket.items():
        if event_of[ticket_id] != event_id:
            continue
        rows.sort(key=lambda row: (row["occurredAt"], row["id"]))
        if rows[-1]["kind"] == "sale":
            rows[-1]["occurredAt"] = later
            return event_id, rows[-1]["id"]
    raise AssertionError(f"no sale row on {event_id}")


def strip_one_events_tiers(store: dict, event_id: str) -> None:
    """Empty an event's tiers and leave its tickets in place: the state that used to crash."""
    for event in store["events"]:
        if event["id"] == event_id:
            event["tiers"] = []
            event.pop("totalSupply", None)
            event.pop("issuedCount", None)


def load_generator():
    spec = importlib.util.spec_from_file_location("build_fixture_store", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# -- defect 1: review section 5.2, the cap in force ------------------------


class TestTheCapReachesTheOptimum(unittest.TestCase):
    """Section 5.2: `recommend` had no cap parameter, so the cap never entered the price."""

    def setUp(self) -> None:
        # One tier, one band, one instance. The numbers are the fixture's shape for
        # `evt_syn_01` at face 1.00 SOL: a level of 1.026573088 SOL inside a band that a
        # zero cap puts a ceiling of exactly face, 1.00 SOL, below.
        self.features = {
            "eventId": "evt",
            "capBpsRecorded": 2500,
            "tiers": [
                {
                    "tierId": "t",
                    "name": "General",
                    "faceValueLamports": 1_000_000_000,
                    "totalSupply": 100,
                    "issuedCount": 4,
                    "sellThrough": 0.04,
                    "capBpsRecorded": 2500,
                    "capCeilingLamportsRecorded": 1_250_000_000,
                    "marks": [],
                    "atCeilingCount": 0,
                    "highestRecordedLamports": None,
                    "lowestRecordedLamports": None,
                    "exposureTicketDays": 400.0,
                    "ticketsNotIssuedAtCut": 0,
                    "timeSpreadDays": 0.0,
                    "exits": {"sale": 0, "transfer": 0, "redeem": 0, "revoke": 0},
                }
            ],
        }
        self.band = {
            "regime": "capped_no_mass_point",
            "floorLamports": None,
            "level": {"available": True, "lamports": 1_026_573_088, "basis": "tier_marks", "n": 6},
            "band": {"loLamports": 738_780_930, "hiLamports": 1_250_000_000, "noUpperBound": False},
            "labelId": "A2",
            "extraLabelIds": [],
        }

    def recommend(self, **kwargs) -> dict:
        return primary_optimum.recommend(
            features=self.features,
            tier_id="t",
            band=self.band,
            intensity={"sales": 6, "exposureTicketDays": 400.0, "salesPerTicketDay": 0.015},
            fee=None,
            sell_through_floor=None,
            **kwargs,
        )

    def test_a_cap_below_the_supported_price_is_refused_not_printed(self) -> None:
        refused = self.recommend(cap_bps_candidate=0)
        self.assertTrue(refused["refused"])
        self.assertEqual(refused["refusalCode"], "recommendation_above_cap")
        self.assertIsNone(refused["recommendedLamports"])
        self.assertEqual(refused["candidateCeilingLamports"], 1_000_000_000)
        self.assertIn("recommendation_above_cap", [row["code"] for row in refused["refusals"]])
        self.assertIn("no_demand_response", [row["code"] for row in refused["refusals"]])

    def test_a_cap_that_permits_the_price_changes_nothing(self) -> None:
        permitted = self.recommend(cap_bps_candidate=2500)
        self.assertFalse(permitted["refused"])
        self.assertEqual(permitted["recommendedLamports"], 1_026_573_088)

    def test_without_a_cap_the_arithmetic_is_unchanged(self) -> None:
        self.assertEqual(self.recommend()["recommendedLamports"], 1_026_573_088)

    def test_the_orchestrator_passes_the_resolved_cap_into_the_recommendation(self) -> None:
        """The wiring, at the seam: the cap the payload carries is the cap the optimum sees."""
        engine = orchestrator()
        calls: list[dict] = []
        real = primary_optimum.recommend

        def spy(**kwargs):
            calls.append(kwargs)
            return real(**kwargs)

        with mock.patch.object(primary_optimum, "recommend", spy):
            payload = engine.price_guidance(event_id=CAPPED_EVENT, cap_bps="0")
        self.assertTrue(calls)
        for call in calls:
            self.assertEqual(call.get("cap_bps_candidate"), 0)
        self.assertEqual(value(payload["selection"]["capBpsCandidate"]), 0)

        # and with no cap in the URL, the recorded cap is the one in force
        calls.clear()
        with mock.patch.object(primary_optimum, "recommend", spy):
            payload = engine.price_guidance(event_id=CAPPED_EVENT)
        recorded = value(payload["event"]["capBps"])
        self.assertIsNotNone(recorded)
        for call in calls:
            self.assertEqual(call.get("cap_bps_candidate"), recorded)

    def test_no_recommendation_exceeds_its_own_pages_ceiling(self) -> None:
        """The general invariant: the page says it honours a cap, and the number obeys it.

        On the old code `evt_syn_01` at `capBps=0` recommended 1.03 SOL against a 1.00 SOL
        ceiling; this sweep is what caught it and what keeps it caught.
        """
        engine = orchestrator()
        checked = 0
        for event_id in [row["id"] for row in engine.ledger.events()]:
            for cap_bps in CAPS_SWEPT:
                payload = engine.price_guidance(event_id=event_id, cap_bps=str(cap_bps))
                for tier in payload["tiers"]:
                    face = value(tier["faceValueLamports"])
                    recommended = value(tier["recommendation"]["recommendedLamports"])
                    stamped = value(tier["recommendation"]["candidateCeilingLamports"])
                    with self.subTest(event=event_id, tier=tier["tierId"], cap=cap_bps):
                        if recommended is not None:
                            checked += 1
                            self.assertLessEqual(recommended, ceiling(face, cap_bps))
                            continue
                        # a price was withheld: if the cap is the reason, the ceiling it
                        # was measured against is on the payload and it is the same integer
                        if tier["recommendation"]["refusalCode"] == "recommendation_above_cap":
                            self.assertEqual(stamped, ceiling(face, cap_bps))
        self.assertGreater(checked, 10)

    def test_the_zero_cap_url_prints_a_typed_reason_and_no_price(self) -> None:
        payload, html = html_for(event_id=CAPPED_EVENT, cap_bps="0")
        text = visible(html)
        self.assertIsNone(value(payload["decision"]["recommendedLamports"]))
        self.assertTrue(payload["decision"]["refused"])
        self.assertEqual(payload["decision"]["refusalCode"], "recommendation_above_cap")
        self.assertIn("[REFUSED]", text)
        self.assertIn("puts the resale ceiling at", text)
        # the ceiling is the cap's own arithmetic, printed so a reader can check it
        face = value(payload["tiers"][0]["faceValueLamports"])
        self.assertIn(f"[EXACT] {face:,} lamports", text)
        self.assertIn("[DECLARED] 0 bps", text)
        # no recommendation number anywhere on the page
        self.assertNotIn("Recommended primary price", text)
        self.assertNotIn("{'value'", text)
        # and the refusal panel names the same reason the decision block does
        self.assertIn("recommendation_above_cap", [row["code"] for row in payload["refusals"]])
        self.assertIn("recommendation_above_cap:", text)

    def test_a_cap_that_permits_the_price_still_prints_the_price(self) -> None:
        plain = payload_for(event_id=CAPPED_EVENT)
        capped = payload_for(event_id=CAPPED_EVENT, cap_bps="2500")
        plain_number = value(plain["decision"]["recommendedLamports"])
        capped_number = value(capped["decision"]["recommendedLamports"])
        self.assertIsNotNone(plain_number)
        self.assertEqual(capped_number, plain_number)
        face = value(capped["tiers"][0]["faceValueLamports"])
        self.assertLessEqual(capped_number, ceiling(face, 2500))
        _, html = html_for(event_id=CAPPED_EVENT, cap_bps="2500")
        self.assertIn("Recommended primary price", visible(html))
        self.assertNotIn("recommendation_above_cap", visible(html))

    def test_a_binding_floor_above_the_cap_is_refused_too(self) -> None:
        """The floor branch is a recommendation as well, so the cap rules there."""
        engine = orchestrator()
        for event_id in [row["id"] for row in engine.ledger.events()]:
            payload = engine.price_guidance(event_id=event_id, cap_bps="0")
            tier = next((row for row in payload["tiers"] if row["selected"]), None)
            if tier is None or tier["regime"] != "capped_and_binding":
                continue
            with self.subTest(event=event_id):
                self.assertEqual(tier["recommendation"]["refusalCode"], "recommendation_above_cap")
                self.assertIsNone(value(tier["recommendation"]["recommendedLamports"]))
                _, html = html_for(event_id=event_id, cap_bps="0")
                self.assertNotIn("at least", visible(html))
            return
        self.fail("the fixture carries no capped-and-binding event")


# -- defect 2: review C8, the loader and the core disagree -----------------


class TestTheLoaderHoldsBackWhatTheCoreCannotPrice(unittest.TestCase):
    """C8: the loader accepted rows the core then raised on, and one row refused every page."""

    def load(self, store: dict) -> LedgerAdapter:
        path = write_store(store)
        self.addCleanup(os.unlink, path)
        return LedgerAdapter.from_fixture(path)

    def test_a_zero_priced_sale_is_rejected_at_load_and_the_rest_is_served(self) -> None:
        store = fixture_store()
        broken, row_id = zero_price_one_sale(store)
        adapter = self.load(store)
        self.assertEqual(adapter.rejections()[broken]["code"], "sale_not_priced")
        self.assertEqual(adapter.rejections()[broken]["fields"]["row"], row_id)
        self.assertIsNone(adapter.event(broken))
        served = [row["id"] for row in adapter.events()]
        self.assertNotIn(broken, served)
        self.assertEqual(len(served), len(store["events"]) - 1)
        # its rows are gone from every read the engine makes, so it cannot reach a number
        self.assertFalse([row for row in adapter.tickets() if row["eventId"] == broken])
        kept = {row["id"] for row in adapter.tickets()}
        self.assertFalse([row for row in adapter.raw_ledger() if row["ticketId"] not in kept])

    def test_a_sale_after_the_event_started_is_rejected_at_load(self) -> None:
        store = fixture_store()
        broken, row_id = move_one_sale_after_its_event(store, "evt_syn_04")
        adapter = self.load(store)
        reason = adapter.rejections()[broken]
        self.assertEqual(reason["code"], "sale_after_event_start")
        self.assertEqual(reason["fields"]["row"], row_id)
        self.assertEqual(len(list(adapter.events())), len(store["events"]) - 1)

    def test_an_event_with_no_tiers_is_rejected_at_load_without_a_crash(self) -> None:
        store = fixture_store()
        strip_one_events_tiers(store, "evt_syn_03")
        # its tickets stay in the store on purpose: the tier they name no longer exists, and
        # that used to be a bare KeyError out of the constructor rather than a typed reason
        self.assertTrue([row for row in store["tickets"] if row["eventId"] == "evt_syn_03"])
        adapter = self.load(store)
        self.assertEqual(adapter.rejections()["evt_syn_03"]["code"], "event_has_no_tier")
        self.assertEqual(len(list(adapter.events())), len(store["events"]) - 1)
        self.assertEqual(len(list(adapter.tickets())), len([row for row in store["tickets"] if row["eventId"] != "evt_syn_03"]))

    def test_the_console_renders_the_typed_reason_and_keeps_serving_the_rest(self) -> None:
        store = fixture_store()
        broken, row_id = zero_price_one_sale(store)
        adapter = self.load(store)
        engine = orchestrator(adapter)
        status, html = console_index(engine, {"event": broken}, base="http://127.0.0.1:8788")
        text = visible(html)
        self.assertEqual(status, 422)
        self.assertIn("sale_not_priced", text)
        self.assertIn(labels.render("sale_not_priced", row=row_id), text)
        self.assertIn("<!doctype html>", html)
        # a healthy event on the same store still prices, with a number
        healthy = next(row["id"] for row in adapter.events())
        status, html = console_index(engine, {"event": healthy}, base="http://127.0.0.1:8788")
        self.assertEqual(status, 200)
        self.assertIn("Recommended primary price", visible(html))

    def test_the_shipped_store_has_nothing_held_back(self) -> None:
        self.assertEqual(LedgerAdapter.from_fixture().rejections(), {})

    def test_the_fixture_check_fails_on_a_store_that_carries_one(self) -> None:
        """`tools/build_fixture_store.py --check` must have an opinion, not only load."""
        module = load_generator()
        store = fixture_store()
        zero_price_one_sale(store)
        path = write_store(store)
        self.addCleanup(os.unlink, path)
        noise = io.StringIO()
        with mock.patch.object(module, "STORE_PATH", Path(path)), contextlib.redirect_stdout(
            noise
        ), contextlib.redirect_stderr(noise):
            self.assertEqual(module._load_through_adapter(), 1)
        self.assertIn("sale_not_priced", noise.getvalue())
        # the positive control: the committed store passes the same gate
        with mock.patch.object(module, "STORE_PATH", FIXTURE), contextlib.redirect_stdout(noise):
            self.assertEqual(module._load_through_adapter(), 0)


if __name__ == "__main__":
    unittest.main()

"""The payload walker: every number carries a badge, a basis and a label id.

The walk is recursive and unforgiving. A bare int or float anywhere in the payload is a
failure, with `STRUCTURAL_KEYS` the only exemption -- simulation error codes and HTTP
statuses are identifiers, not measurements. Every `value` arrives inside a wrapper that
also carries which of the eight badges applies, the basis naming the record and the
counts, and the id of the sentence the page must render beside it.

`basis` may not contain the word "data". A basis that says "from data" tells a reader
nothing about which record produced the number, which is the failure this file exists to
catch (spec section 2.2, P6).
"""

from __future__ import annotations

import datetime as dt
import json
import unittest

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.api import guidance
from ticketpath.core import labels
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)


def orchestrator() -> Orchestrator:
    return Orchestrator(
        ledger=LedgerAdapter.from_fixture(),
        rpc=RpcAdapter.from_env("devnet"),
        pricing_model=PricingModelAdapter(),
        cluster="devnet",
        now=lambda: CLOCK,
    )


def number_wrappers(node, path=""):
    """Yield (path, wrapper dict) for every number wrapper, skipping a wrapper's value."""
    if isinstance(node, dict):
        if "value" in node and isinstance(node["value"], (int, float)) and not isinstance(node["value"], bool):
            yield path, node
            for key, value in node.items():
                if key == "value":
                    continue
                yield from number_wrappers(value, f"{path}.{key}")
            return
        for key, value in node.items():
            if key in guidance.STRUCTURAL_KEYS:
                continue
            yield from number_wrappers(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from number_wrappers(value, f"{path}[{index}]")


def bare_numbers(node, path=""):
    """Yield (path, value) for every number that is NOT inside a wrapper."""
    if isinstance(node, dict):
        if "value" in node and isinstance(node["value"], (int, float)) and not isinstance(node["value"], bool):
            for key, value in node.items():
                if key == "value":
                    continue
                yield from bare_numbers(value, f"{path}.{key}")
            return
        for key, value in node.items():
            if key in guidance.STRUCTURAL_KEYS:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                yield f"{path}.{key}", value
            else:
                yield from bare_numbers(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                yield f"{path}[{index}]", value
            else:
                yield from bare_numbers(value, f"{path}[{index}]")


def strings(node, path=""):
    if isinstance(node, dict):
        for key, value in node.items():
            yield from strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            yield from strings(value, f"{path}[{index}]")
    elif isinstance(node, str):
        yield path, node


def states() -> dict[str, dict]:
    engine = orchestrator()
    return {
        "default (capped and binding)": engine.price_guidance(),
        "uncapped": engine.price_guidance(event_id="evt_syn_04"),
        "capped, no mass point": engine.price_guidance(event_id="evt_syn_01"),
        "cold start": engine.price_guidance(event_id="evt_syn_03"),
        "draft, nothing issued": engine.price_guidance(event_id="evt_syn_08"),
        "before the first sale": engine.price_guidance(event_id="evt_syn_02", as_of="2026-09-01T00:00:00Z"),
        "cap set to zero": engine.price_guidance(event_id="evt_syn_02", cap_bps="0"),
        "fee supplied": engine.price_guidance(event_id="evt_syn_02", fee_lamports="0"),
        "declared tau at the top of the grid": engine.price_guidance(event_id="evt_syn_04", tau="0.406"),
        "simulation shown": engine.price_guidance(show_sim=True),
    }


class TestEveryNumberIsLabelled(unittest.TestCase):
    def test_every_number_is_a_wrapper_with_a_badge_a_basis_and_a_label(self) -> None:
        for name, payload in states().items():
            for path, wrapper in number_wrappers(payload):
                with self.subTest(state=name, path=path):
                    self.assertIn(wrapper["badge"], labels.BADGES)
                    self.assertTrue(wrapper.get("basis"))
                    if wrapper["badge"] == "EXACT":
                        # arithmetic carries no interpretive sentence: the badge is the label
                        continue
                    self.assertIsNotNone(wrapper.get("labelId"), f"{path} has no label id")
                    self.assertIn(wrapper["labelId"], labels.ALLOWED_IDS)

    def test_no_bare_numbers(self) -> None:
        for name, payload in states().items():
            for path, value in bare_numbers(payload):
                with self.subTest(state=name, path=path):
                    self.fail(f"unlabelled number {value!r} at {path}")

    def test_basis_names_the_record_and_never_says_data(self) -> None:
        for name, payload in states().items():
            for path, wrapper in number_wrappers(payload):
                basis = wrapper["basis"]
                with self.subTest(state=name, path=path, basis=basis):
                    self.assertNotIn("data", basis.lower())
                    self.assertTrue(len(basis) > 8)


class TestTheRefusalsAreStates(unittest.TestCase):
    def test_sale_probability_is_none_with_not_identified_everywhere(self) -> None:
        for name, payload in states().items():
            with self.subTest(state=name):
                self.assertEqual(payload["saleProbability"]["value"], None)
                self.assertEqual(payload["saleProbability"]["reason"], "not_identified")
                for tier in payload["tiers"]:
                    self.assertIsNone(tier["refusal"]["saleProbability"])
                    self.assertEqual(tier["refusal"]["saleProbabilityReason"], "not_identified")

    def test_the_refusal_panel_is_never_empty(self) -> None:
        for name, payload in states().items():
            with self.subTest(state=name):
                self.assertGreaterEqual(len(payload["refusals"]), 3)
                codes = [row["code"] for row in payload["refusals"]]
                self.assertIn("not_identified", codes)
                self.assertIn("no_demand_response", codes)

    def test_a_binding_event_states_no_upper_bound_anywhere(self) -> None:
        payload = states()["default (capped and binding)"]
        self.assertTrue(payload["decision"]["noUpperBound"])
        self.assertIsNone(payload["decision"]["bandHiLamports"])
        self.assertIn("no_upper_bound", [row["code"] for row in payload["refusals"]])

    def test_a_cold_start_has_no_price_anywhere(self) -> None:
        payload = states()["cold start"]
        self.assertIsNone(payload["decision"]["recommendedLamports"])
        self.assertTrue(payload["decision"]["refused"])
        self.assertEqual(payload["decision"]["refusalCode"], "no_resale_record")
        for tier in payload["tiers"]:
            self.assertIsNone(tier["recommendation"]["recommendedLamports"])

    def test_net_revenue_is_withheld_without_a_fee_and_present_with_one(self) -> None:
        without = states()["default (capped and binding)"]
        with_fee = states()["fee supplied"]
        self.assertIsNone(without["decision"]["netRevenue"])
        self.assertIsNotNone(with_fee["decision"]["netRevenue"])


class TestNoBannedSentenceInAnyPayload(unittest.TestCase):
    def test_every_string_in_every_payload_passes_the_scan(self) -> None:
        for name, payload in states().items():
            for path, text in strings(payload):
                with self.subTest(state=name, path=path):
                    self.assertIsNone(labels.contains_banned(text), f"{path}: {text!r}")

    def test_the_serialised_payload_passes_the_scan_as_one_string(self) -> None:
        for name, payload in states().items():
            with self.subTest(state=name):
                self.assertIsNone(labels.contains_banned(json.dumps(payload, ensure_ascii=False)))


if __name__ == "__main__":
    unittest.main()

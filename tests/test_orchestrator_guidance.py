"""The orchestrator routes and does not calculate, and its three error codes are stable.

The routing test is a monkeypatch: `value_band.pooled` is replaced by a stub that records
the arguments it received and returns a sentinel, and the sentinel has to arrive in the
payload unmodified. If the orchestrator were computing anything of its own, the sentinel
would not survive.

The error tests pin the codes the console's URL can produce: `cap_invalid`,
`as_of_invalid`, `tau_invalid` and a 404 for an unknown event.
"""

from __future__ import annotations

import datetime as dt
import unittest

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.core import value_band
from ticketpath.errors import ApiError
from ticketpath.orchestrator import Orchestrator

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)


def orchestrator() -> Orchestrator:
    return Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        PricingModelAdapter(),
        "devnet",
        now=lambda: CLOCK,
    )


class TestRouting(unittest.TestCase):
    def test_the_pooling_sentinel_arrives_unmodified(self) -> None:
        engine = orchestrator()
        seen: list[dict] = []
        sentinel = {
            "mu": 0.123,
            "tau2": 0.04,
            "tau": 0.2,
            "method": "sentinel",
            "eventsWithResale": 2,
            "eventsInWindow": 3,
            "eventsTotal": 4,
            "varOfMu": 0.01,
            "shrinkageWeight": 0.5,
        }

        def fake_pooled(*, rows, declared_tau):
            seen.append({"rows": len(rows), "declared_tau": declared_tau})
            return dict(sentinel)

        original = value_band.pooled
        value_band.pooled = fake_pooled
        try:
            payload = engine.price_guidance(tau="0.25")
        finally:
            value_band.pooled = original
        self.assertEqual(seen, [{"rows": 8, "declared_tau": 0.25}])
        self.assertEqual(payload["pooled"]["method"], "sentinel")

    def test_the_parameters_reach_the_estimator_unchanged(self) -> None:
        engine = orchestrator()
        seen: list[dict] = []
        original = value_band.estimate

        def spy(**kwargs):
            seen.append({"tau": kwargs["tau"], "cap": kwargs["cap_bps_candidate"]})
            return original(**kwargs)

        value_band.estimate = spy
        try:
            engine.price_guidance(cap_bps="3000", tau="0.3")
        finally:
            value_band.estimate = original
        self.assertTrue(seen)
        self.assertTrue(all(row["tau"] == 0.3 for row in seen))
        self.assertTrue(all(row["cap"] == 3000 for row in seen))

    def test_the_same_parameters_twice_give_the_same_payload(self) -> None:
        first = orchestrator().price_guidance(event_id="evt_syn_02", as_of="2026-11-07T12:00:00Z")
        second = orchestrator().price_guidance(event_id="evt_syn_02", as_of="2026-11-07T12:00:00Z")
        self.assertEqual(first["decision"]["recommendedLamports"], second["decision"]["recommendedLamports"])
        self.assertEqual(first["evidence"]["resales"], second["evidence"]["resales"])


class TestErrorCodes(unittest.TestCase):
    def test_a_non_numeric_cap_is_cap_invalid(self) -> None:
        with self.assertRaises(ApiError) as caught:
            orchestrator().price_guidance(cap_bps="abc")
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(caught.exception.code, "cap_invalid")

    def test_a_cap_outside_the_range_is_cap_invalid(self) -> None:
        with self.assertRaises(ApiError) as caught:
            orchestrator().price_guidance(cap_bps="10001")
        self.assertEqual(caught.exception.code, "cap_invalid")

    def test_a_bad_instant_is_as_of_invalid(self) -> None:
        with self.assertRaises(ApiError) as caught:
            orchestrator().price_guidance(as_of="2026-13-45")
        self.assertEqual(caught.exception.status, 400)
        self.assertEqual(caught.exception.code, "as_of_invalid")

    def test_a_tau_outside_the_grid_is_tau_invalid(self) -> None:
        for value in ("0.05", "0.9"):
            with self.subTest(tau=value):
                with self.assertRaises(ApiError) as caught:
                    orchestrator().price_guidance(tau=value)
                self.assertEqual(caught.exception.code, "tau_invalid")

    def test_an_unknown_event_is_a_404(self) -> None:
        with self.assertRaises(ApiError) as caught:
            orchestrator().price_guidance(event_id="evt_nope")
        self.assertEqual(caught.exception.status, 404)

    def test_an_unknown_tier_is_a_404(self) -> None:
        with self.assertRaises(ApiError) as caught:
            orchestrator().price_guidance(event_id="evt_syn_02", tier_id="tier_nope")
        self.assertEqual(caught.exception.status, 404)

    def test_the_default_selection_is_the_cap_binding_event(self) -> None:
        payload = orchestrator().price_guidance()
        self.assertEqual(payload["event"]["id"], "evt_syn_02")
        self.assertEqual(payload["selection"]["tierId"], "tier_stg_general")


class TestNothingAfterTheCut(unittest.TestCase):
    def test_moving_the_cut_before_the_first_sale_drops_to_zero(self) -> None:
        payload = orchestrator().price_guidance(event_id="evt_syn_02", as_of="2026-09-01T00:00:00Z")
        self.assertEqual(payload["evidence"]["resales"]["value"], 0)
        self.assertEqual(payload["tiers"][0]["regime"], "no_resale")
        self.assertTrue(payload["decision"]["refused"])


if __name__ == "__main__":
    unittest.main()

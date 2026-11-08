"""The LLM run block, and the runner wiring that makes its caps real.

These tests never spawn a child. They prove the config surface, the parallel decision path,
the run-level token and dollar trip that feeds the same kill switch as the flag file, and the
sidecar/metadata that records what the run spent. The policy adapter itself is tested against
a fake child in `test_forge_policy.py` and `test_llm.py`.
"""

from __future__ import annotations

import dataclasses
import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from market_swarm.config import (
    ConfigError,
    EventSpec,
    LlmConfig,
    PriceTable,
    RunConfig,
    load_run_config,
)
from market_swarm.agents import Intent, MarketView
from market_swarm.runner import SwarmRunner
from market_swarm.tests.test_runner import (
    FakeGateway,
    FixedClock,
    _agents,
    _config,
    _event,
)


def _base_config(**llm) -> dict:
    """A valid run config as a dict, with the llm block the caller passes."""
    return {
        "run_id": "sw-llm",
        "cluster": "local",
        "seed": 3,
        "dry_run": False,
        "kill_after_seconds": 60,
        "out_dir": "market_swarm/runs",
        "total_budget_lamports": 1_000_000_000,
        "total_budget_actions": 50,
        "events": [
            {
                "event_id": "ev",
                "face_lamports": 1_000_000,
                "mode": "capped",
                "cap_bps": 2500,
                "tickets": 4,
                "rounds": 2,
                "round_seconds": 1,
            }
        ],
        "agents": [
            {
                "agent_id": "s1",
                "policy": "scalper",
                "wallet_label": "s1",
                "seed": 1,
                "budget_lamports": 5_000_000,
                "budget_actions": 10,
            }
        ],
        "llm": llm,
    }


class LlmConfigCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "run.json"

    def load(self, raw: dict):
        self.path.write_text(json.dumps(raw), encoding="utf-8")
        return load_run_config(self.path)

    def test_absent_block_means_scripted(self) -> None:
        raw = _base_config()
        del raw["llm"]
        self.assertIsNone(self.load(raw).llm)

    def test_disabled_block_is_kept_but_off(self) -> None:
        config = self.load(_base_config(enabled=False))
        self.assertIsNotNone(config.llm)
        self.assertFalse(config.llm.enabled)

    def test_defaults_are_the_cheap_safe_shape(self) -> None:
        config = self.load(_base_config(enabled=True))
        llm = config.llm
        self.assertEqual(llm.tier, "low")
        self.assertEqual(llm.max_concurrent, 2)
        self.assertEqual(llm.per_agent_token_budget, 60_000)
        self.assertEqual(llm.total_token_budget, 250_000)
        self.assertEqual(llm.timeout_seconds, 90.0)
        self.assertIsNone(llm.cost_cap_usd)

    def test_cost_cap_without_a_price_table_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(_base_config(enabled=True, cost_cap_usd=1.0))
        self.assertIn("usd_per_mtok", str(caught.exception))

    def test_cost_cap_with_prices_is_kept(self) -> None:
        config = self.load(
            _base_config(
                enabled=True,
                cost_cap_usd=0.5,
                usd_per_mtok={
                    "input": 0.15,
                    "output": 0.6,
                    "cache_read": 0.003,
                    "cache_write": 0.0,
                },
            )
        )
        self.assertEqual(config.llm.cost_cap_usd, 0.5)
        self.assertEqual(config.llm.usd_per_mtok.input, 0.15)

    def test_concurrency_above_the_measured_safe_bound_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(_base_config(enabled=True, max_concurrent=4))
        self.assertIn("max_concurrent", str(caught.exception))

    def test_total_below_per_agent_is_refused(self) -> None:
        with self.assertRaises(ConfigError):
            self.load(
                _base_config(
                    enabled=True, per_agent_token_budget=500, total_token_budget=100
                )
            )

    def test_a_policy_with_no_persona_is_refused_when_the_llm_is_on(self) -> None:
        raw = _base_config(enabled=True)
        raw["agents"][0]["policy"] = "not_a_policy"
        with self.assertRaises(ConfigError) as caught:
            self.load(raw)
        self.assertIn("not_a_policy", str(caught.exception))

    def test_an_unknown_policy_is_allowed_when_the_llm_is_off(self) -> None:
        # The scripted path already refuses an unknown policy at policy-build time; the
        # loader's extra check exists only because the LLM path needs a persona by name.
        raw = _base_config(enabled=False)
        raw["agents"][0]["policy"] = "not_a_policy"
        self.assertEqual(self.load(raw).agents[0].policy, "not_a_policy")

    def test_unknown_llm_field_is_refused(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(_base_config(enabled=True, budget=1))
        self.assertIn("unknown field", str(caught.exception))

    def test_an_unknown_tier_is_refused_at_load(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(_base_config(enabled=True, tier="high"))
        self.assertIn("llm.tier", str(caught.exception))

    def test_a_zero_cost_cap_is_refused_at_load(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(_base_config(enabled=True, cost_cap_usd=0))
        self.assertIn("greater than zero", str(caught.exception))

    def test_price_table_converts_tokens_to_dollars(self) -> None:
        table = PriceTable(input=1.0, output=2.0, cache_read=0.5, cache_write=3.0)
        usage = type(
            "U", (), {"input": 1_000_000, "output": 1_000_000,
                      "cache_read": 1_000_000, "cache_write": 1_000_000}
        )()
        self.assertAlmostEqual(table.cost_usd(usage), 6.5)


class DecideOnce:
    """A policy that records its view and returns one intent, optionally charging a budget."""

    name = "probe"

    def __init__(self, *, charge=None, usage=None, sleep=0.0) -> None:
        self.views: list[MarketView] = []
        self.threads: list[int] = []
        self._charge = charge
        self._usage = usage
        self._sleep = sleep
        self._lock = threading.Lock()

    def decide(self, view: MarketView) -> list[Intent]:
        with self._lock:
            self.views.append(view)
            self.threads.append(threading.get_ident())
        if self._charge is not None:
            self._charge(self._usage)
        if self._sleep:
            time.sleep(self._sleep)
        return [
            Intent(
                agent_id=view.agent_id,
                action="buy",
                price_lamports=view.face_lamports,
                ticket_id=None,
                rationale=f"{view.agent_id}-r{view.round}",
            )
        ]


class RunnerLlmCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "out"

    def _llm_config(self, *, agents=("a1", "b1", "c1"), max_concurrent=3,
                    total_tokens=100_000):
        llm = LlmConfig(
            enabled=True,
            tier="low",
            per_agent_token_budget=min(10_000, total_tokens),
            per_decision_token_budget=min(4_000, total_tokens),
            total_token_budget=total_tokens,
            max_concurrent=max_concurrent,
            timeout_seconds=30.0,
            cost_cap_usd=None,
            usd_per_mtok=None,
        )
        return RunConfig(
            run_id="sw-llm-run",
            cluster="local",
            events=(_event(rounds=1),),
            agents=_agents(*agents, policy="buyer"),
            total_budget_lamports=100_000_000,
            total_budget_actions=100,
            kill_after_seconds=60,
            out_dir=self.out,
            dry_run=False,
            seed=7,
            llm=llm,
        )

    def test_agents_decide_concurrently_up_to_the_cap(self) -> None:
        policies = {name: DecideOnce(sleep=0.05) for name in ("a1", "b1", "c1")}
        runner = SwarmRunner(self._llm_config(), FakeGateway(), clock=FixedClock(),
                             policies=policies)
        summary = runner.run()
        self.assertIsNone(summary.kill_reason)
        self.assertEqual(summary.rows, 3)
        threads = {thread for policy in policies.values() for thread in policy.threads}
        self.assertGreater(len(threads), 1, "decisions did not run on more than one thread")
        self.assertLessEqual(len(threads), 3)

    def test_a_serial_config_decides_on_one_thread(self) -> None:
        policies = {name: DecideOnce(sleep=0.01) for name in ("a1", "b1", "c1")}
        runner = SwarmRunner(
            self._llm_config(max_concurrent=1), FakeGateway(), clock=FixedClock(),
            policies=policies,
        )
        runner.run()
        threads = {thread for policy in policies.values() for thread in policy.threads}
        self.assertEqual(len(threads), 1)

    def test_the_round_hands_apply_its_intents_in_the_seeded_order(self) -> None:
        """Collection order is observable at the seam `_apply`, so a reordering fails here.

        `_apply` sorts by its own key, which is why comparing datasets cannot test this: a
        reversed collection would produce identical rows. The order the round hands over is
        what determines ties in that sort and is the thing the parallel path must preserve.
        """
        policies = {name: DecideOnce(sleep=0.01) for name in ("a1", "b1", "c1")}
        config = self._llm_config()
        runner = SwarmRunner(config, FakeGateway(), clock=FixedClock(), policies=policies)
        handed: list[list[str]] = []
        runner._apply = lambda ctx, round_no, intents: handed.append(
            [intent.agent_id for intent in intents]
        )
        runner.run()
        expected = runner._decision_order(config.events[0].event_id, 1)
        self.assertEqual(handed[0], expected)

    def test_a_tripped_token_budget_stops_the_run_and_names_the_cap(self) -> None:
        # The budget is rebuilt by `_reset` when `run()` starts, so the closure resolves it
        # at call time rather than holding the instance built by the constructor.
        holder: dict = {"budget": lambda: runner._llm_budget}
        usage = type("U", (), {"input": 9_000, "output": 9_000,
                               "cache_read": 0, "cache_write": 0, "usd": 0.0,
                               "total": 18_000})()
        policies = {
            name: DecideOnce(charge=lambda u: holder["budget"]().charge(u), usage=usage)
            for name in ("a1", "b1", "c1")
        }
        config = self._llm_config(total_tokens=20_000)
        runner = SwarmRunner(config, FakeGateway(), clock=FixedClock(), policies=policies)
        summary = runner.run()
        self.assertIsNotNone(summary.kill_reason)
        self.assertIn("token budget", summary.kill_reason)
        meta_path = Path(str(summary.dataset_paths[0]).replace(".jsonl", ".meta.json"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        # The sidecar has to say why the run stopped, not carry a null.
        self.assertEqual(meta["kill_reason"], summary.kill_reason)
        self.assertFalse(meta["complete"])
        # The round that tripped writes nothing: the check runs before `_apply`.
        self.assertEqual(summary.rows, 0)
        self.assertEqual(summary.llm["trip_reason"], summary.kill_reason)

    def test_sidecar_and_summary_carry_the_spend(self) -> None:
        usage = type("U", (), {"input": 100, "output": 50, "cache_read": 10,
                               "cache_write": 0, "usd": 0.0005, "total": 160})()
        holder: dict = {"budget": lambda: runner._llm_budget}
        policies = {
            name: DecideOnce(charge=lambda u: holder["budget"]().charge(u), usage=usage)
            for name in ("a1", "b1", "c1")
        }
        runner = SwarmRunner(self._llm_config(), FakeGateway(), clock=FixedClock(),
                             policies=policies)
        summary = runner.run()
        self.assertIsNotNone(summary.llm)
        self.assertEqual(summary.llm["total_tokens"], 480)
        self.assertAlmostEqual(summary.llm["usd"], 0.0015, places=9)
        self.assertEqual(summary.llm["cost_basis"], "stream")
        meta_path = Path(str(summary.dataset_paths[0]).replace(".jsonl", ".meta.json"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertEqual(meta["llm"]["total_tokens"], 480)
        self.assertIn("LLM agents", meta["note"])
        self.assertTrue(meta["synthetic"])
        # Provenance: the sidecar records what each agent asked for, in the agent's words,
        # and counts real against fallback decisions.
        self.assertEqual(len(meta["llm"]["decision_log"]), 3)
        self.assertEqual(meta["llm"]["decision_log"][0]["action"], "buy")
        self.assertEqual(meta["llm"]["decisions_real"], 0)
        self.assertEqual(meta["llm"]["decisions_fallback"], 0)
        self.assertEqual(meta["llm"]["decisions_total"], 0)
        self.assertIn("estimate, not a bill", meta["llm"]["cost_note"])
        self.assertEqual(meta["llm"]["pricing_errors"], 0)
        self.assertIn(meta["llm"]["cost_basis"], {"stream", "table", "mixed", "unpriced", "table_error"})
        # The children's cwd is a temp directory, never the run directory (which holds the
        # gateway's keypairs) and never the repository.
        scratch = Path(meta["llm"]["scratch_root"])
        self.assertTrue(scratch.is_dir())
        self.assertNotIn(Path.cwd().resolve(), [scratch.resolve(), *scratch.resolve().parents])

    def test_a_scratch_root_inside_the_repository_is_refused(self) -> None:
        from market_swarm.llm import LlmBudget, build_llm_policy

        spec = _agents("a1", policy="buyer")[0]
        budget = LlmBudget(total_token_budget=1_000)
        llm = self._llm_config().llm
        with self.assertRaises(ValueError) as caught:
            build_llm_policy(spec, llm=llm, budget=budget, scratch_root=Path.cwd())
        self.assertIn("inside the repository", str(caught.exception))

    def test_provenance_counts_sum_across_the_policies(self) -> None:
        runner = SwarmRunner(
            self._llm_config(), FakeGateway(), clock=FixedClock(), policies={}
        )
        first = DecideOnce()
        first.decisions_real = 4
        first.decisions_fallback = 1
        first.decisions_refused = 2
        first.fallback_reasons = ["zero tokens reported"]
        second = DecideOnce()
        second.decisions_real = 2
        second.decisions_fallback = 0
        second.decisions_refused = 0
        second.fallback_reasons = []
        runner._llm_policies = [first, second]
        block = runner._llm_meta()
        self.assertEqual(block["decisions_real"], 6)
        self.assertEqual(block["decisions_fallback"], 1)
        self.assertEqual(block["decisions_refused"], 2)
        self.assertEqual(block["decisions_total"], 9)
        self.assertEqual(block["fallback_reasons"], ["zero tokens reported"])

    def test_a_price_table_prices_a_stream_that_reports_no_cost(self) -> None:
        from market_swarm.config import PriceTable
        from market_swarm.llm import LlmBudget

        budget = LlmBudget(
            total_token_budget=10_000_000,
            cost_cap_usd=1.0,
            prices=PriceTable(input=1.0, output=2.0, cache_read=0.5, cache_write=0.0),
        )
        usage = type("U", (), {"input": 1_000_000, "output": 0, "cache_read": 0,
                               "cache_write": 0, "usd": 0.0, "total": 1_000_000})()
        budget.charge(usage)
        self.assertAlmostEqual(budget.usd, 1.0)
        self.assertEqual(budget.snapshot()["cost_basis"], "table")
        # 1.0 is not over 1.0, so the cap has not tripped; one more dollar does.
        budget.charge(usage)
        self.assertIn("cost cap", budget.trip_reason)

    def test_a_second_run_does_not_overwrite_the_first_dataset(self) -> None:
        config = _config(self.out, _agents("a1"), _event(rounds=1), kill_after_seconds=60)
        SwarmRunner(
            config, FakeGateway(), clock=FixedClock(), policies={"a1": DecideOnce()}
        ).run()
        with self.assertRaises(ValueError) as caught:
            SwarmRunner(
                config, FakeGateway(), clock=FixedClock(), policies={"a1": DecideOnce()}
            ).run()
        self.assertIn("refusing to overwrite", str(caught.exception))

    def test_no_llm_block_means_no_llm_metadata(self) -> None:
        config = _config(self.out, _agents("a1"), _event(rounds=1), kill_after_seconds=60)
        summary = SwarmRunner(
            config, FakeGateway(), clock=FixedClock(),
            policies={"a1": DecideOnce()},
        ).run()
        self.assertIsNone(summary.llm)


if __name__ == "__main__":
    unittest.main()

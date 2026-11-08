"""The runner-level findings of the feature-9 review, pinned against a fake child.

`tmp/review/feature-9.md` raised four things that live above the adapter: a sidecar that
told a reader a live run was scripted, a refusal counted as a purchase by the repo's own
summariser, a kill switch polled (or not) around the refusal rows, and a fallback row that
never said it was one. Every policy here is a real `ForgePolicy` whose `spawn` returns an
in-memory fake child, so nothing in this file spawns `pi`, reads a network or sets
`MARKET_SWARM_LIVE_LLM`.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from market_swarm import agents
from market_swarm import gateway as gw
from market_swarm.config import AgentSpec, EventSpec, RunConfig
from market_swarm.datasets import summarise
from market_swarm.forge_policy import ForgePolicy
from market_swarm.runner import SwarmRunner
from market_swarm.tests.test_forge_policy import (
    FakeChild,
    agent_end,
    message_end,
    message_end_without_usage,
)

FACE = 1_000_000_000
CAP_BPS = 2500
MODEL = "commandcode/deepseek/deepseek-v4.1-flash:low"


def reply_text(action: str = "buy", price: int = FACE, rationale: str = "face is fair") -> str:
    return json.dumps(
        {"action": action, "price_lamports": price, "rationale": rationale}
    )


def make_spec(agent_id: str, policy: str = "holder") -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        policy=policy,
        wallet_label=f"wallet-{agent_id}",
        seed=7,
        budget_lamports=10 * FACE,
        budget_actions=20,
    )


def make_config(
    out: Path,
    agent_ids: tuple[str, ...] = ("a1",),
    *,
    kill_after: float = 30.0,
    events: int = 1,
) -> RunConfig:
    return RunConfig(
        run_id="sw-f9",
        cluster="local",
        events=tuple(
            EventSpec(
                event_id=f"evt_f9_{index}",
                face_lamports=FACE,
                mode="capped",
                cap_bps=CAP_BPS,
                tickets=4,
                rounds=1,
                round_seconds=0,
            )
            for index in range(1, events + 1)
        ),
        agents=tuple(make_spec(agent_id) for agent_id in agent_ids),
        total_budget_lamports=50 * FACE,
        total_budget_actions=50,
        kill_after_seconds=kill_after,
        out_dir=out,
        dry_run=True,
        seed=7,
    )


def live_policy(child: FakeChild, scratch_root: Path, agent_id: str = "a1") -> ForgePolicy:
    """A real `ForgePolicy` wired to a fake child: the live adapter, with no live child."""
    return ForgePolicy(
        make_spec(agent_id),
        tier="low",
        token_budget=40_000,
        max_decision_tokens=40_000,
        timeout_seconds=5,
        acknowledge_cost=True,
        spawn=lambda argv, cwd=None: child,
        scratch_root=scratch_root,
    )


def _rows(path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def _data_rows(path) -> list[dict]:
    return [row for row in _rows(path) if row.get("record") != "header"]


def _meta(path) -> dict:
    sidecar = Path(str(path).replace(".jsonl", ".meta.json"))
    return json.loads(sidecar.read_text(encoding="utf-8"))


class SeamProvenanceTests(unittest.TestCase):
    """A run given live policies through `policies=` must not call itself scripted."""

    def _run(self, policies: dict, tmp: str, **kwargs) -> tuple:
        out = Path(tmp) / "out"
        agent_ids = kwargs.pop("agent_ids", tuple(policies))
        config = make_config(out, agent_ids, **kwargs)
        runner = SwarmRunner(
            config,
            gw.make_gateway("local", run_dir=Path(tmp) / "run", dry_run=True),
            policies=policies,
        )
        return runner.run(), out

    def test_a_live_policy_through_the_seam_does_not_publish_scripted_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild([message_end(reply_text()), agent_end()])
            policy = live_policy(child, Path(tmp) / "scratch")
            summary, _ = self._run({"a1": policy}, tmp)

            path = summary.dataset_paths[0]
            meta = _meta(path)
            # The sentence that was false about this exact run shape.
            self.assertNotIn("scripted agents", meta["note"])
            self.assertNotIn("provenance unknown", meta["note"])
            self.assertIn("LLM agents", meta["note"])
            self.assertEqual(meta["provenance"], "policy")

    def test_the_llm_block_is_filled_from_the_policy_own_accounting(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild([message_end(reply_text()), agent_end()])
            policy = live_policy(child, Path(tmp) / "scratch")
            summary, _ = self._run({"a1": policy}, tmp)

            block = _meta(summary.dataset_paths[0])["llm"]
            self.assertIsInstance(block, dict)
            self.assertEqual(block["provenance"], "policy")
            self.assertEqual(block["model"], MODEL)
            self.assertEqual(block["tier"], "low")
            self.assertEqual(block["decisions_real"], 1)
            self.assertEqual(block["decisions_fallback"], 0)
            self.assertEqual(block["decisions_total"], 1)
            self.assertEqual(block["total_tokens"], 12)  # the fake child's four counters
            self.assertGreater(block["input"], 0)
            self.assertEqual(block["cost_note"], "provider-reported estimate, not a bill")
            self.assertEqual(block["policies"][0]["agent_id"], "a1")
            # No run-level LlmBudget on this path, and the block says so rather than
            # implying a cap that does not exist.
            self.assertIsNone(block["total_token_budget"])
            self.assertIsNone(block["cost_cap_usd"])

    def test_the_childs_rationale_survives_into_the_sidecar_and_the_row(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild(
                [message_end(reply_text(rationale="buy now, demand is firm")), agent_end()]
            )
            policy = live_policy(child, Path(tmp) / "scratch")
            summary, _ = self._run({"a1": policy}, tmp)

            path = summary.dataset_paths[0]
            log = _meta(path)["llm"]["decision_log"]
            self.assertEqual(len(log), 1)
            self.assertIn("demand is firm", log[0]["rationale"])
            row = _data_rows(path)[0]
            self.assertIn("policy said:", row["rationale"])
            self.assertIn("demand is firm", row["rationale"])

    def test_the_summariser_reads_the_sidecar_and_says_llm_agents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild([message_end(reply_text()), agent_end()])
            policy = live_policy(child, Path(tmp) / "scratch")
            summary, _ = self._run({"a1": policy}, tmp)

            result = summarise(Path(summary.dataset_paths[0]))
            self.assertIn("LLM agents decided", result["note"])

    def test_an_opaque_caller_policy_publishes_provenance_unknown(self) -> None:
        class Opaque:
            name = "opaque"

            def decide(self, view):
                return [
                    agents.Intent(
                        agent_id=view.agent_id,
                        action="buy",
                        price_lamports=FACE,
                        ticket_id=None,
                        rationale="an opaque policy decided this",
                    )
                ]

        with tempfile.TemporaryDirectory() as tmp:
            summary, _ = self._run({"a1": Opaque()}, tmp)
            path = summary.dataset_paths[0]
            meta = _meta(path)
            # Neither claim is available, so neither is made.
            self.assertEqual(meta["provenance"], "unknown")
            self.assertIsNone(meta["llm"])
            self.assertIn("provenance unknown: caller-supplied policy", meta["note"].lower())
            self.assertNotIn("scripted agents", meta["note"])
            self.assertIn("could not say", summarise(Path(path))["note"])

    def test_a_two_event_seam_run_counts_both_events(self) -> None:
        # A caller-supplied policy is the same object across events, so a total folded when
        # the second event is pinned would miss everything it did afterwards.
        with tempfile.TemporaryDirectory() as tmp:
            children = [
                FakeChild([message_end(reply_text()), agent_end()]) for _ in range(2)
            ]
            policy = ForgePolicy(
                make_spec("a1"),
                tier="low",
                token_budget=40_000,
                max_decision_tokens=40_000,
                timeout_seconds=5,
                acknowledge_cost=True,
                spawn=lambda argv, cwd=None: children.pop(0),
                scratch_root=Path(tmp) / "scratch",
            )
            summary, _ = self._run({"a1": policy}, tmp, events=2)

            self.assertEqual(len(children), 0, "a second decision did not run")
            self.assertEqual(summary.llm["decisions_real"], 2)
            self.assertEqual(summary.llm["decisions_total"], 2)
            self.assertEqual(_meta(summary.dataset_paths[-1])["llm"]["decisions_real"], 2)

    def test_a_fallback_row_says_the_policy_fell_back(self) -> None:
        # The child reported no usage, so the adapter fell back to the scripted policy. The
        # row has to say that: a scripted trade standing in for a paid decision is only
        # honest if the dataset records which it was.
        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild(
                [message_end_without_usage(reply_text()), agent_end()]
            )
            policy = live_policy(child, Path(tmp) / "scratch")
            summary, _ = self._run({"a1": policy}, tmp)

            rows = _data_rows(summary.dataset_paths[0])
            self.assertTrue(rows, "the scripted fallback should have produced a row")
            self.assertIn("policy said: forge-fallback", rows[0]["rationale"])
            self.assertIn("no usage block", rows[0]["rationale"])
            self.assertEqual(policy.decisions_fallback, 1)
            self.assertEqual(policy.decisions_real, 0)

    def test_a_mixed_run_is_not_labelled_a_model_run(self) -> None:
        # One live adapter and one opaque stub: the block carries what the adapter reported,
        # and the provenance says the run cannot attribute the whole dataset.
        class Opaque:
            name = "opaque"

            def decide(self, view):
                return [
                    agents.Intent(
                        agent_id=view.agent_id,
                        action="buy",
                        price_lamports=FACE,
                        ticket_id=None,
                        rationale="an opaque policy decided this",
                    )
                ]

        with tempfile.TemporaryDirectory() as tmp:
            child = FakeChild([message_end(reply_text()), agent_end()])
            policy = live_policy(child, Path(tmp) / "scratch", agent_id="a1")
            summary, _ = self._run(
                {"a1": policy, "b1": Opaque()}, tmp, agent_ids=("a1", "b1")
            )
            meta = _meta(summary.dataset_paths[0])
            self.assertEqual(meta["provenance"], "unknown")
            self.assertEqual(meta["llm"]["provenance"], "unknown")
            self.assertEqual(meta["llm"]["decisions_real"], 1)
            self.assertIn("provenance unknown", meta["note"].lower())

    def test_a_scripted_run_still_says_scripted_agents(self) -> None:
        # The control: the scripted path builds its own policies, and there "scripted" is a
        # fact, not a guess.
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            config = make_config(out)
            summary = SwarmRunner(
                config,
                gw.make_gateway("local", run_dir=Path(tmp) / "run", dry_run=True),
            ).run()
            meta = _meta(summary.dataset_paths[0])
            self.assertEqual(meta["provenance"], "scripted")
            self.assertIsNone(meta["llm"])
            self.assertIn("scripted agents", meta["note"])


class _Clock:
    """A clock a test moves by hand, so a wall-clock kill can fire inside a policy."""

    def __init__(self, now: float = 1_000_000.0) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


class KillSwitchAroundRefusalsTests(unittest.TestCase):
    def test_a_clock_that_expires_inside_the_policy_writes_no_refusal_row(self) -> None:
        clock = _Clock()

        class ExpiringRefuser:
            name = "forge"

            def decide(self, view):
                clock.now += 5.0  # past kill_after_seconds, after deciding
                return [
                    agents.Refusal(
                        agent_id=view.agent_id,
                        action="refuse",
                        price_lamports=None,
                        rationale="forge-refused: total_tokens: the cap is spent.",
                    )
                ]

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            config = make_config(out, ("a1",), kill_after=1.0)
            runner = SwarmRunner(
                config,
                gw.make_gateway("local", run_dir=Path(tmp) / "run", dry_run=True),
                clock=clock,
                policies={"a1": ExpiringRefuser()},
            )
            summary = runner.run()

            self.assertIsNotNone(summary.kill_reason)
            self.assertIn("wall-clock cap reached", summary.kill_reason)
            # Not a partial round: the poll is above the call that writes the refusal row.
            self.assertEqual(summary.rows, 0)
            self.assertEqual(_data_rows(summary.dataset_paths[0]), [])
            self.assertFalse(_meta(summary.dataset_paths[0])["complete"])


class RefusalActionTests(unittest.TestCase):
    def test_a_forge_refusal_carries_the_refuse_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            policy = ForgePolicy(
                make_spec("a1"),
                tier="low",
                token_budget=12,
                max_decision_tokens=12,
                timeout_seconds=5,
                acknowledge_cost=True,
                spawn=lambda argv, cwd=None: FakeChild(
                    [message_end(reply_text()), agent_end()]
                ),
                scratch_root=Path(tmp) / "scratch",
            )
            policy.decide(self._view())
            # The adapter's budget is now spent, so the next decision is a refusal.
            decisions = policy.decide(self._view())
            self.assertEqual(len(decisions), 1)
            self.assertIsInstance(decisions[0], agents.Refusal)
            self.assertEqual(decisions[0].action, "refuse")

    @staticmethod
    def _view() -> agents.MarketView:
        return agents.MarketView(
            round=1,
            rounds_left=4,
            event_id="evt_f9",
            mode="capped",
            face_lamports=FACE,
            cap_bps=CAP_BPS,
            ceiling_lamports=FACE * (10_000 + CAP_BPS) // 10_000,
            tickets_available=4,
            holdings=(),
            last_prices=(),
            refused_attempts=0,
            agent_id="a1",
            seed=7,
        )


if __name__ == "__main__":
    unittest.main()

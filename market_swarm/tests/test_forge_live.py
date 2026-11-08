"""One live `pi` child, opt-in, bounded, and skipped by default.

    MARKET_SWARM_LIVE_LLM=1 python3 -m unittest market_swarm.tests.test_forge_live -v

Why a separate environment variable from `MARKET_SWARM_LIVE`: that one starts a local
validator and costs nothing, this one calls a hosted model and costs money. Running the
gateway's live suite must never spend a cent, so the two gates are not the same gate.

What the test asserts is the adapter's contract on a **real** child, not the model's
judgement: exactly one `Intent` (never zero, never two), labelled `forge:` and not
`forge-fallback:`, inside the per-decision token cap, inside subforge's `maxRunSeconds`,
with the child reaped and its own registry-shaped row written. It does not assert that the
price is *good*; there is no ground truth for that and a test that pretended otherwise
would be asserting its own arithmetic.

Cost, measured 2026-11-08 on the `low` tier (`records/findings/41-deepseek-live-adapter.md`):
one decision of this size is a few hundred to a few thousand tokens and well under a cent.
The caps below are the hard stop if that ever stops being true.
"""

from __future__ import annotations

import os
import tempfile
import time
import unittest
from pathlib import Path

from market_swarm import agents
from market_swarm.config import AgentSpec
from market_swarm.forge_policy import ForgePolicy

#: The gate. Absent, the whole file is one skip and nothing is spawned.
LIVE_ENV = "MARKET_SWARM_LIVE_LLM"

FACE = 1_000_000_000
CAP_BPS = 2500
CEILING = FACE * (10_000 + CAP_BPS) // 10_000

#: The operator's per-child ceiling for this build: no child without a literal cap, and no
#: cap above two minutes. Both are asserted below, not just passed.
MAX_RUN_SECONDS = 120.0
MAX_DECISION_TOKENS = 40_000
#: One decision and one budget, so there is no second child in this test. Note what these
#: numbers are: a reservation bounds *admission*, not the provider's bill. The measured
#: child took 27 091 of them; a child that overshot 40 000 would be charged for what it
#: burned, the overrun would be recorded, and every later decision would refuse.
TOTAL_TOKENS = 40_000


def make_spec() -> AgentSpec:
    return AgentSpec(
        agent_id="live1",
        policy="holder",
        wallet_label="wallet-live1",
        seed=7,
        budget_lamports=10 * FACE,
        budget_actions=20,
    )


def make_view() -> agents.MarketView:
    return agents.MarketView(
        round=1,
        rounds_left=5,
        event_id="SYN-live",
        mode="capped",
        face_lamports=FACE,
        cap_bps=CAP_BPS,
        ceiling_lamports=CEILING,
        tickets_available=4,
        holdings=(),
        last_prices=(),
        refused_attempts=0,
        agent_id="live1",
        seed=7,
    )


@unittest.skipUnless(
    os.environ.get(LIVE_ENV) == "1",
    f"live: set {LIVE_ENV}=1 to spend one capped `pi` child against the provider",
)
class LiveDeepseekDecisionTest(unittest.TestCase):
    def test_one_child_returns_exactly_one_intent_inside_the_caps(self) -> None:
        self.assertLessEqual(MAX_RUN_SECONDS, 120.0)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows_path = root / "rows.jsonl"
            policy = ForgePolicy(
                make_spec(),
                tier="low",
                token_budget=TOTAL_TOKENS,
                max_decision_tokens=MAX_DECISION_TOKENS,
                timeout_seconds=MAX_RUN_SECONDS,
                acknowledge_cost=True,
                scratch_root=root / "scratch",
                observation_path=rows_path,
            )

            started = time.monotonic()
            decisions = policy.decide(make_view())
            elapsed = time.monotonic() - started

            # Quoted rather than asserted quietly: this is the evidence the finding cites.
            print(f"\nlive decision: {len(decisions)} result(s) in {elapsed:.1f}s")
            for decision in decisions:
                print(f"  {type(decision).__name__}: {decision}")
            print(f"  usage: {policy.usage}")
            print(f"  budget: {policy.budget}")
            print(f"  row: {rows_path.read_text().strip()}")

            # The reply contract is one JSON object, and the adapter refused anything else, so
            # a child that answered twice would already have fallen back and failed the
            # rationale assertion below. `replyObjects` is the count the adapter actually
            # read, which is what makes this test able to fail for the failure it names.
            self.assertEqual(len(decisions), 1, decisions)
            intent = decisions[0]
            self.assertIsInstance(intent, agents.Intent)
            self.assertTrue(
                intent.rationale.startswith("forge: "),
                f"the child fell back instead of answering: {intent.rationale}",
            )
            self.assertIn(intent.action, agents.ACTIONS)
            self.assertIsInstance(intent.price_lamports, int)
            self.assertGreater(intent.price_lamports, 0)
            self.assertLessEqual(
                intent.price_lamports, FACE * agents.HARD_PRICE_MULTIPLE
            )

            # The caps held, and the numbers are the child's, not this test's.
            self.assertGreater(policy.usage.total, 0, "a zero-token run is a failure")
            self.assertLessEqual(policy.usage.total, TOTAL_TOKENS)
            self.assertEqual(policy.decisions_real, 1)
            self.assertEqual(policy.decisions_fallback, 0)

            row = policy.observations[0]
            self.assertEqual(row["status"], "finished")
            self.assertEqual(row["replyObjects"], 1, "the child did not answer with one object")
            self.assertIs(row["costUnknown"], False)
            self.assertEqual(row["maxRunSeconds"], MAX_RUN_SECONDS)
            self.assertLessEqual(row["seconds"], MAX_RUN_SECONDS)
            self.assertEqual((row["tokensIn"], row["tokensOut"]) >= (0, 0), True)
            self.assertGreaterEqual(row["tokensIn"], 0)
            self.assertGreaterEqual(row["tokensOut"], 0)
            self.assertIsNotNone(row["sessionId"], "the child's session id was not captured")
            self.assertTrue(rows_path.is_file())
            self.assertLess(elapsed, MAX_RUN_SECONDS + 30)


if __name__ == "__main__":
    unittest.main()

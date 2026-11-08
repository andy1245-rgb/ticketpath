"""The budget tracker: hard limits, no mutation on refusal, a recorded freeze.

The important tests here are the refusal ones: an over-charge must leave the tracker
byte-identical, because the runner writes the refusal row from the before/after balance
and a budget that moved on a refused action would make that row a lie.
"""

from __future__ import annotations

import json
import unittest
from dataclasses import FrozenInstanceError

from market_swarm.budget import BudgetExceeded, BudgetState, BudgetTracker
from market_swarm.config import AgentSpec


def _spec(agent_id: str = "a1", lamports: int = 1_000, actions: int = 3) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        policy="buyer",
        wallet_label=f"wallet-{agent_id}",
        seed=1,
        budget_lamports=lamports,
        budget_actions=actions,
    )


def _frozen_tracker_snapshot(tracker: BudgetTracker) -> str:
    """The tracker's state as one comparable string, key order pinned."""
    return json.dumps(tracker.snapshot(), sort_keys=True, separators=(",", ":"))


class TestWithinBudget(unittest.TestCase):
    def test_a_charge_returns_the_snapshot_it_just_produced(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        state = tracker.charge("a1", 400)
        self.assertIsInstance(state, BudgetState)
        self.assertEqual(state.agents[0].spent_lamports, 400)
        self.assertEqual(state.agents[0].actions, 1)
        written = tracker.snapshot()["agents"][0]
        self.assertEqual(written["spent_lamports"], state.agents[0].spent_lamports)
        self.assertEqual(written["actions"], state.agents[0].actions)
        self.assertEqual(written["remaining_lamports"], state.agents[0].remaining_lamports)

    def test_a_charge_at_exactly_the_limit_is_admitted(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        tracker.charge("a1", 1_000)
        snapshot = tracker.snapshot()
        self.assertEqual(snapshot["agents"][0]["remaining_lamports"], 0)
        self.assertEqual(snapshot["total"]["remaining_lamports"], 0)

    def test_a_zero_lamport_charge_still_counts_as_one_action(self) -> None:
        tracker = BudgetTracker([_spec(actions=1)], total_lamports=1_000, total_actions=5)
        tracker.charge("a1", 0)
        self.assertEqual(tracker.snapshot()["agents"][0]["actions"], 1)

    def test_the_totals_move_with_every_charge(self) -> None:
        tracker = BudgetTracker([_spec(), _spec("a2")], total_lamports=2_000, total_actions=6)
        tracker.charge("a1", 300)
        tracker.charge("a2", 200)
        total = tracker.snapshot()["total"]
        self.assertEqual(total["spent_lamports"], 500)
        self.assertEqual(total["actions"], 2)
        self.assertEqual(total["limit_lamports"], 2_000)


class TestCheckNeverMutates(unittest.TestCase):
    def test_a_passing_check_leaves_the_state_byte_identical(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        before = _frozen_tracker_snapshot(tracker)
        tracker.check("a1", 999)
        self.assertEqual(_frozen_tracker_snapshot(tracker), before)

    def test_every_failing_check_leaves_the_state_byte_identical(self) -> None:
        cases = [
            ("agent_lamports", BudgetTracker([_spec()], 1_000, 3), "a1", 1_001),
            ("agent_actions", BudgetTracker([_spec(lamports=1_000, actions=0)], 1_000, 3), "a1", 0),
            ("total_lamports", BudgetTracker([_spec(lamports=1_000)], 100, 3), "a1", 101),
            ("total_actions", BudgetTracker([_spec()], 1_000, 0), "a1", 0),
        ]
        for kind, tracker, agent_id, lamports in cases:
            with self.subTest(kind=kind):
                before = _frozen_tracker_snapshot(tracker)
                with self.assertRaises(BudgetExceeded) as caught:
                    tracker.check(agent_id, lamports)
                self.assertEqual(caught.exception.kind, kind)
                self.assertEqual(_frozen_tracker_snapshot(tracker), before)


class TestRefusals(unittest.TestCase):
    def test_an_over_charge_names_the_agent_lamport_budget_and_the_numbers(self) -> None:
        tracker = BudgetTracker([_spec(lamports=1_000)], total_lamports=1_000, total_actions=3)
        tracker.charge("a1", 700)
        with self.assertRaises(BudgetExceeded) as caught:
            tracker.charge("a1", 301)
        error = caught.exception
        self.assertEqual(error.kind, "agent_lamports")
        self.assertEqual(error.requested, 301)
        self.assertEqual(error.spent, 700)
        self.assertEqual(error.limit, 1_000)
        self.assertIn("a1", str(error))
        self.assertIn("301", str(error))
        self.assertIn("700", str(error))
        self.assertIn("1000", str(error))

    def test_an_over_charge_leaves_the_state_byte_identical(self) -> None:
        tracker = BudgetTracker([_spec(lamports=1_000)], total_lamports=1_000, total_actions=3)
        tracker.charge("a1", 900)
        before = _frozen_tracker_snapshot(tracker)
        with self.assertRaises(BudgetExceeded):
            tracker.charge("a1", 101)
        self.assertEqual(_frozen_tracker_snapshot(tracker), before)

    def test_the_agent_action_budget_is_named(self) -> None:
        tracker = BudgetTracker([_spec(actions=1)], total_lamports=1_000, total_actions=9)
        tracker.charge("a1", 1)
        with self.assertRaises(BudgetExceeded) as caught:
            tracker.check("a1", 1)
        self.assertEqual(caught.exception.kind, "agent_actions")
        self.assertEqual(caught.exception.spent, 1)
        self.assertEqual(caught.exception.limit, 1)

    def test_the_total_lamport_budget_is_named(self) -> None:
        tracker = BudgetTracker([_spec(lamports=1_000)], total_lamports=500, total_actions=9)
        with self.assertRaises(BudgetExceeded) as caught:
            tracker.check("a1", 501)
        self.assertEqual(caught.exception.kind, "total_lamports")
        self.assertEqual(caught.exception.limit, 500)

    def test_the_total_action_budget_is_named(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=0)
        with self.assertRaises(BudgetExceeded) as caught:
            tracker.check("a1", 0)
        self.assertEqual(caught.exception.kind, "total_actions")
        self.assertEqual(caught.exception.limit, 0)

    def test_a_frozen_agent_cannot_be_charged(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        tracker.freeze("a1", "total budget tripped")
        before = _frozen_tracker_snapshot(tracker)
        with self.assertRaises(BudgetExceeded) as caught:
            tracker.charge("a1", 1)
        self.assertEqual(caught.exception.kind, "agent_frozen")
        self.assertEqual(_frozen_tracker_snapshot(tracker), before)


class TestFreeze(unittest.TestCase):
    def test_a_freeze_is_recorded_in_the_snapshot(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        tracker.freeze("a1", "kill switch")
        entry = tracker.snapshot()["agents"][0]
        self.assertIs(entry["frozen"], True)
        self.assertEqual(entry["freeze_reason"], "kill switch")
        self.assertIs(tracker.is_frozen("a1"), True)

    def test_a_freeze_is_idempotent_and_keeps_the_first_reason(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        tracker.freeze("a1", "first reason")
        tracker.freeze("a1", "second reason")
        self.assertEqual(
            tracker.snapshot()["agents"][0]["freeze_reason"], "first reason"
        )

    def test_a_freeze_does_not_touch_the_spend(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        tracker.charge("a1", 100)
        tracker.freeze("a1", "stop")
        entry = tracker.snapshot()["agents"][0]
        self.assertEqual(entry["spent_lamports"], 100)
        self.assertEqual(entry["actions"], 1)

    def test_an_unknown_agent_raises_keyerror_everywhere(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        for call in (
            lambda: tracker.check("nope", 0),
            lambda: tracker.charge("nope", 0),
            lambda: tracker.freeze("nope", "why"),
            lambda: tracker.is_frozen("nope"),
        ):
            with self.subTest(call=call), self.assertRaises(KeyError):
                call()

    def test_a_blank_freeze_reason_is_refused(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        with self.assertRaises(ValueError):
            tracker.freeze("a1", "  ")
        self.assertIs(tracker.is_frozen("a1"), False)


class TestSnapshotShape(unittest.TestCase):
    def test_the_snapshot_is_json_serialisable_plain_values(self) -> None:
        tracker = BudgetTracker([_spec(), _spec("a2")], total_lamports=1_000, total_actions=3)
        tracker.charge("a1", 100)
        tracker.freeze("a2", "stop")
        snapshot = tracker.snapshot()
        text = json.dumps(snapshot)
        self.assertEqual(json.loads(text), snapshot)
        for entry in snapshot["agents"]:
            self.assertIsInstance(entry["spent_lamports"], int)
            self.assertIsInstance(entry["frozen"], bool)
            self.assertIsInstance(entry["freeze_reason"], (str, type(None)))

    def test_the_snapshot_keeps_the_constructor_order(self) -> None:
        tracker = BudgetTracker([_spec("b"), _spec("a")], total_lamports=1_000, total_actions=3)
        self.assertEqual([e["agent_id"] for e in tracker.snapshot()["agents"]], ["b", "a"])

    def test_the_state_is_immutable(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        state = tracker.charge("a1", 1)
        with self.assertRaises(FrozenInstanceError):
            state.total_spent_lamports = 0  # type: ignore[misc]
        with self.assertRaises(FrozenInstanceError):
            state.agents[0].spent_lamports = 0  # type: ignore[misc]
        self.assertIsInstance(state.agents, tuple)

    def test_remaining_values_on_the_state_agree_with_the_snapshot(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        state = tracker.charge("a1", 250)
        self.assertEqual(state.agents[0].remaining_lamports, 750)
        self.assertEqual(state.agents[0].remaining_actions, 2)
        self.assertEqual(state.total_remaining_lamports, 750)


class TestConstructionAndInputs(unittest.TestCase):
    def test_a_negative_charge_is_refused_and_does_not_mutate(self) -> None:
        tracker = BudgetTracker([_spec()], total_lamports=1_000, total_actions=3)
        before = _frozen_tracker_snapshot(tracker)
        for bad in (-1, 1.5, True):
            with self.subTest(bad=bad), self.assertRaises((ValueError, TypeError)):
                tracker.charge("a1", bad)
        self.assertEqual(_frozen_tracker_snapshot(tracker), before)

    def test_duplicate_agent_ids_are_refused(self) -> None:
        with self.assertRaises(ValueError):
            BudgetTracker([_spec(), _spec()], total_lamports=1_000, total_actions=3)

    def test_negative_totals_are_refused(self) -> None:
        for total_lamports, total_actions in ((-1, 1), (1, -1)):
            with self.subTest(total_lamports=total_lamports, total_actions=total_actions):
                with self.assertRaises(ValueError):
                    BudgetTracker([_spec()], total_lamports, total_actions)

    def test_a_non_integer_total_is_refused(self) -> None:
        for value in (1.0, True, "10"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                BudgetTracker([_spec()], value, 3)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()

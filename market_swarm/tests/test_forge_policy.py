"""The opt-in forge policy, tested against a fake child and never against a provider.

Nothing in this file spawns `pi`, calls a network, or imports a third-party package. The
properties pinned here are the ones a trading swarm depends on: a well-formed reply becomes
exactly one checked intent, and every other outcome - prose, a float price, an oversized
stream, a silent child, a non-zero exit, zero tokens - becomes a deterministic scripted
intent labelled `forge-fallback:`, with the child reaped on every path.
"""

from __future__ import annotations

import json
import tempfile
import threading
import time
import unittest
from pathlib import Path

from market_swarm import agents
from market_swarm.config import AgentSpec
from market_swarm.forge_policy import (
    CostNotAcknowledged,
    ForgeBudget,
    ForgeBudgetExceeded,
    ForgePolicy,
    TIER_MODELS,
    Usage,
    _usage_tokens,
    inflight_usage,
    spawn_argv,
    usage_from_record,
)

FACE = 100_000_000
CAP_BPS = 1200
CEILING = FACE * (10_000 + CAP_BPS) // 10_000
EVENT = "SYN-event"
USAGE = {"input": 5, "output": 5, "cacheRead": 1, "cacheWrite": 1}


def make_spec(agent_id: str = "a1", policy: str = "holder", seed: int = 7) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        policy=policy,
        wallet_label=f"wallet-{agent_id}",
        seed=seed,
        budget_lamports=10 * FACE,
        budget_actions=20,
    )


def make_view(
    *,
    holdings: tuple[agents.Holding, ...] = (),
    rounds_left: int = 5,
    refused_attempts: int = 0,
) -> agents.MarketView:
    return agents.MarketView(
        round=3,
        rounds_left=rounds_left,
        event_id=EVENT,
        mode="capped",
        face_lamports=FACE,
        cap_bps=CAP_BPS,
        ceiling_lamports=CEILING,
        tickets_available=4,
        holdings=holdings,
        last_prices=(FACE,),
        refused_attempts=refused_attempts,
        agent_id="a1",
        seed=7,
    )


def message_end(text: str | None, usage: dict | None = None, role: str = "assistant") -> str:
    message = {
        "role": role,
        "content": [{"type": "text", "text": text}] if text is not None else [],
        "usage": usage if usage is not None else dict(USAGE),
        "stopReason": "end",
    }
    return json.dumps({"type": "message_end", "message": message}) + "\n"


def agent_end(will_retry: bool = False) -> str:
    return json.dumps({"type": "agent_end", "willRetry": will_retry}) + "\n"


def reply(action: str, price: object, rationale: str = "because") -> str:
    return json.dumps(
        {"action": action, "price_lamports": price, "rationale": rationale}
    )


class FakeStdin:
    """Records every line the harness writes; honours `abort` unless told not to."""

    def __init__(self, owner: "FakeChild") -> None:
        self.owner = owner
        self.writes: list[str] = []
        self.closed = False

    def write(self, data: object) -> None:
        if isinstance(data, (bytes, bytearray)):
            data = data.decode("utf-8")
        text = str(data)
        self.writes.append(text)
        try:
            payload = json.loads(text)
        except ValueError:
            return
        if payload.get("type") == "abort" and self.owner.exit_on_abort:
            if self.owner.returncode is None:
                self.owner.returncode = 0

    def flush(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class FakeChild:
    """Just enough of `subprocess.Popen` for the harness: no pid is ever signalled."""

    def __init__(
        self,
        lines=(),
        *,
        returncode: int | None = None,
        exit_on_abort: bool = True,
    ) -> None:
        self.stdin = FakeStdin(self)
        self.stdout = iter(lines)
        self.pid = 1  # never used: the reap only group-kills a real subprocess
        self.returncode = returncode
        self.exit_on_abort = exit_on_abort
        self.terminated = 0
        self.killed = 0

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is None:
            raise TimeoutError("fake child still running")
        return self.returncode

    def terminate(self) -> None:
        self.terminated += 1
        if self.returncode is None:
            self.returncode = -15

    def kill(self) -> None:
        self.killed += 1
        if self.returncode is None:
            self.returncode = -9


def make_policy(
    *,
    child: FakeChild | None = None,
    spec: AgentSpec | None = None,
    token_budget: int = 1_000_000,
    timeout_seconds: float = 5,
    max_concurrent: int = 2,
    tier: str = "low",
    spawn=None,
    calls: list | None = None,
    system_prompt: str | None = None,
    extra_argv=(),
    on_usage=None,
    kill_check=None,
    scratch_root: Path | None = None,
    max_decision_tokens: int | None = None,
    observation_path: Path | None = None,
) -> ForgePolicy:
    spec = spec or make_spec()

    def default_spawn(argv, *, cwd=None):
        if calls is not None:
            calls.append({"argv": list(argv), "cwd": cwd})
        return child

    return ForgePolicy(
        spec,
        tier=tier,
        token_budget=token_budget,
        max_concurrent=max_concurrent,
        timeout_seconds=timeout_seconds,
        spawn=spawn or default_spawn,
        acknowledge_cost=True,
        system_prompt=system_prompt,
        extra_argv=extra_argv,
        on_usage=on_usage,
        kill_check=kill_check,
        scratch_root=scratch_root,
        max_decision_tokens=max_decision_tokens,
        observation_path=observation_path,
    )


class CostGateTests(unittest.TestCase):
    def test_construction_without_acknowledgement_raises(self) -> None:
        with self.assertRaises(CostNotAcknowledged):
            ForgePolicy(make_spec(), token_budget=1000)

    def test_unknown_tier_raises_instead_of_spawning_without_a_model(self) -> None:
        with self.assertRaises(ValueError) as caught:
            ForgePolicy(
                make_spec(), tier="deep", token_budget=1000, acknowledge_cost=True
            )
        self.assertIn("deep", str(caught.exception))

    def test_low_tier_resolves_to_the_documented_model_string(self) -> None:
        policy = make_policy(child=FakeChild(), tier="low")
        self.assertEqual(policy.model, "commandcode/deepseek/deepseek-v4.1-flash:low")
        self.assertEqual(policy.model, "%s/%s:%s" % TIER_MODELS["low"])


class SpawnContractTests(unittest.TestCase):
    def test_argv_is_the_documented_form_and_the_prompt_carries_no_path(self) -> None:
        calls: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(child=child, calls=calls)
        policy.decide(make_view())

        self.assertEqual(len(calls), 1)
        argv = calls[0]["argv"]
        self.assertEqual(argv[0], "pi")
        self.assertEqual(argv[1:5], ["--mode", "rpc", "--session-dir", argv[4]])
        self.assertEqual(argv[5], "--name")
        self.assertEqual(argv[6], "forge:a1")
        self.assertEqual(argv[7], "--model")
        self.assertEqual(argv[8], "commandcode/deepseek/deepseek-v4.1-flash:low")
        self.assertTrue(argv[4].endswith("decision-00001/session"))
        self.assertTrue(str(calls[0]["cwd"]).endswith("decision-00001/work"))

        prompt_lines = [json.loads(line) for line in child.stdin.writes]
        self.assertEqual(prompt_lines[0]["type"], "prompt")
        prompt = prompt_lines[0]["message"]
        self.assertNotIn("/", prompt)
        self.assertNotIn("market_swarm", prompt)
        self.assertIn("rounds_left", prompt)
        self.assertIn("no prose", prompt.lower())


class ReplyTests(unittest.TestCase):
    def test_well_formed_reply_becomes_one_intent_with_the_exact_price(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE + 1)), agent_end()])
        intents = make_policy(child=child).decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].action, "buy")
        self.assertEqual(intents[0].price_lamports, FACE + 1)
        self.assertTrue(intents[0].rationale.startswith("forge: "))
        self.assertTrue(child.stdin.closed)

    def test_prose_wrapped_json_is_extracted(self) -> None:
        wrapped = "Sure, here it is:\n" + reply("buy", FACE) + "\nThat is my answer."
        child = FakeChild([message_end("```json\n" + wrapped + "\n```"), agent_end()])
        intents = make_policy(child=child).decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].action, "buy")
        self.assertEqual(intents[0].price_lamports, FACE)

    def test_resell_on_a_holding_names_the_held_ticket(self) -> None:
        holding = agents.Holding(ticket_id="t-1", lot_price_lamports=FACE, acquired_round=1)
        view = make_view(holdings=(holding,))
        child = FakeChild([message_end(reply("resell", CEILING)), agent_end()])
        intents = make_policy(child=child).decide(view)

        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].action, "resell")
        self.assertEqual(intents[0].ticket_id, "t-1")
        self.assertEqual(intents[0].price_lamports, CEILING)

    def test_float_price_is_rejected_and_falls_back(self) -> None:
        child = FakeChild(
            [message_end(json.dumps({"action": "buy", "price_lamports": 100.5})), agent_end()]
        )
        intents = make_policy(child=child).decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertEqual(intents[0].action, "buy")
        self.assertEqual(intents[0].price_lamports, FACE)  # the holder fallback's buy
        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("not an integer", intents[0].rationale)

    def test_unknown_action_falls_back(self) -> None:
        child = FakeChild([message_end(reply("short", FACE)), agent_end()])
        intents = make_policy(child=child).decide(make_view())
        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))

    def test_unparseable_reply_falls_back(self) -> None:
        child = FakeChild([message_end("I would probably buy."), agent_end()])
        intents = make_policy(child=child).decide(make_view())
        self.assertEqual(len(intents), 1)
        self.assertIn("no JSON object", intents[0].rationale)


class LimitTests(unittest.TestCase):
    def test_oversized_token_stream_trips_the_budget_mid_stream(self) -> None:
        child = FakeChild(
            [
                message_end(None, usage={"input": 60, "output": 60, "cacheRead": 5}),
                message_end(reply("buy", FACE)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child, token_budget=100)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("per-decision token cap", intents[0].rationale)
        self.assertGreater(policy.tokens_spent, 0)
        # The tokens that arrived before the kill were billed, so they are charged.
        self.assertEqual(policy.budget.tokens, 125)
        self.assertEqual(policy.observations[0]["status"], "failed")

    def test_a_spent_budget_refuses_instead_of_falling_back(self) -> None:
        calls: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(
            child=child, calls=calls, token_budget=12, max_decision_tokens=12
        )
        first = policy.decide(make_view())
        self.assertTrue(first[0].rationale.startswith("forge: "))
        spent_before = policy.budget.tokens

        second = policy.decide(make_view())

        self.assertEqual(len(second), 1)
        self.assertIsInstance(second[0], agents.Refusal)
        self.assertTrue(second[0].rationale.startswith("forge-refused: total_tokens"))
        # Refused before spending: no second child, no second charge, and no scripted
        # trade standing in for a decision nobody paid for.
        self.assertEqual(len(calls), 1)
        self.assertEqual(policy.budget.tokens, spent_before)
        self.assertEqual(policy.budget.decisions, 1)
        self.assertEqual(policy.decisions_fallback, 0)
        # A decision nobody took is not a purchase: its own action value, so no reader can
        # count it under `buy`.
        self.assertEqual(second[0].action, "refuse")
        self.assertIsNone(second[0].price_lamports)

    def test_silent_child_trips_the_wall_clock_and_falls_back(self) -> None:
        def slow_stream():
            yield message_end(reply("buy", FACE))
            time.sleep(0.35)  # longer than the injected timeout, well under a second
            yield agent_end()

        child = FakeChild(slow_stream())
        policy = make_policy(child=child, timeout_seconds=0.2)
        intents = policy.decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertIn("timed out after 0.2s", intents[0].rationale)

    def test_stream_without_agent_end_falls_back(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE))])
        intents = make_policy(child=child).decide(make_view())
        self.assertIn("without a non-retrying agent_end", intents[0].rationale)

    def test_retrying_agent_end_is_not_completion(self) -> None:
        child = FakeChild(
            [
                agent_end(will_retry=True),
                message_end(reply("buy", FACE)),
                agent_end(will_retry=False),
            ]
        )
        intents = make_policy(child=child).decide(make_view())
        self.assertTrue(intents[0].rationale.startswith("forge: "))

    def test_non_zero_exit_falls_back(self) -> None:
        child = FakeChild([], returncode=3)
        intents = make_policy(child=child).decide(make_view())
        self.assertIn("child exited 3", intents[0].rationale)

    def test_zero_token_completion_falls_back(self) -> None:
        child = FakeChild(
            [
                message_end(None, usage={"input": 0, "output": 0}),
                agent_end(),
            ]
        )
        intents = make_policy(child=child).decide(make_view())
        self.assertIn("zero tokens", intents[0].rationale)


class FallbackTests(unittest.TestCase):
    def test_fallback_is_deterministic_for_the_same_view_and_seed(self) -> None:
        def run_once() -> list:
            child = FakeChild([], returncode=1)
            return make_policy(child=child).decide(make_view())

        first, second = run_once(), run_once()
        self.assertEqual(first, second)
        self.assertTrue(first[0].rationale.startswith("forge-fallback: "))

    def test_spawn_error_falls_back(self) -> None:
        def exploding_spawn(argv, *, cwd=None):
            raise FileNotFoundError("pi")

        policy = make_policy(spawn=exploding_spawn)
        intents = policy.decide(make_view())
        self.assertIn("spawn error", intents[0].rationale)
        self.assertIn("FileNotFoundError", intents[0].rationale)


class ReapTests(unittest.TestCase):
    def test_reap_runs_on_the_exception_path(self) -> None:
        child = FakeChild(
            [message_end("not json at all"), agent_end()], exit_on_abort=False
        )
        intents = make_policy(child=child).decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        abort_lines = [line for line in child.stdin.writes if '"abort"' in line]
        self.assertTrue(abort_lines, "the reap must abort over stdin")
        self.assertGreaterEqual(child.terminated, 1, "the reap must signal the child")
        self.assertTrue(child.stdin.closed)

    def test_reap_runs_after_a_successful_decision(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        make_policy(child=child).decide(make_view())
        self.assertTrue(any('"abort"' in line for line in child.stdin.writes))


class ConcurrencyTests(unittest.TestCase):
    def test_semaphore_keeps_two_children_at_most(self) -> None:
        lock = threading.Lock()
        state = {"active": 0, "peak": 0}

        def spawning(argv, *, cwd=None):
            with lock:
                state["active"] += 1
                state["peak"] = max(state["peak"], state["active"])
            time.sleep(0.05)
            with lock:
                state["active"] -= 1
            return FakeChild([message_end(reply("buy", FACE)), agent_end()])

        policy = make_policy(spawn=spawning, max_concurrent=2, token_budget=10**9)
        results: list = []

        def decide() -> None:
            results.append(policy.decide(make_view()))

        threads = [threading.Thread(target=decide) for _ in range(4)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertEqual(len(results), 4)
        self.assertEqual(state["peak"], 2)


class UsageTests(unittest.TestCase):
    def test_usage_from_record_sums_four_counters_and_reads_cost_total(self) -> None:
        record = {
            "type": "message_end",
            "message": {
                "role": "assistant",
                "usage": {
                    "input": 5,
                    "output": 7,
                    "cacheRead": 11,
                    "cacheWrite": 13,
                    "reasoning": 3,
                    "totalTokens": 39,
                    "cost": {
                        "input": 0.1,
                        "output": 0.2,
                        "cacheRead": 0.0,
                        "cacheWrite": 0.0,
                        "total": 0.3,
                    },
                },
            },
        }
        usage = usage_from_record(record)

        self.assertEqual(
            usage,
            Usage(input=5, output=7, cache_read=11, cache_write=13, usd=0.3),
        )
        self.assertEqual(usage.total, 36)

    def test_non_assistant_or_missing_usage_is_zero(self) -> None:
        self.assertEqual(
            usage_from_record({"message": {"role": "user", "usage": dict(USAGE)}}),
            Usage(),
        )
        self.assertEqual(usage_from_record({"type": "agent_end"}), Usage())
        self.assertEqual(usage_from_record({"message": {"role": "assistant"}}), Usage())
        self.assertEqual(
            usage_from_record({"message": {"role": "assistant", "usage": "nope"}}),
            Usage(),
        )

    def test_bools_and_non_integers_in_the_counters_are_ignored(self) -> None:
        record = {
            "message": {
                "role": "assistant",
                "usage": {
                    "input": True,
                    "output": 5.5,
                    "cacheRead": 2,
                    "cacheWrite": False,
                    "cost": {"total": True},
                },
            }
        }
        usage = usage_from_record(record)

        self.assertEqual(usage.total, 2)
        self.assertEqual(usage.usd, 0.0)

    def test_addition_is_element_wise_and_usd_is_rounded(self) -> None:
        first = Usage(input=1, output=2, cache_read=3, cache_write=4, usd=0.1)
        second = Usage(input=10, output=20, cache_read=30, cache_write=40, usd=0.2)
        total = first + second

        self.assertEqual(
            (total.input, total.output, total.cache_read, total.cache_write),
            (11, 22, 33, 44),
        )
        self.assertEqual(total.total, 110)
        self.assertEqual(total.usd, 0.3)

    def test_usage_tokens_equals_the_four_counters_and_ignores_cost(self) -> None:
        record = {
            "message": {
                "role": "assistant",
                "usage": {**dict(USAGE), "cost": {"total": 99.5}},
            }
        }
        self.assertEqual(_usage_tokens(record), 12)
        self.assertEqual(_usage_tokens({"type": "agent_end"}), 0)


class SpawnExtraTests(unittest.TestCase):
    def test_extra_is_appended_once_after_the_model_value(self) -> None:
        argv = spawn_argv(
            session_dir=Path("session"),
            name="a1",
            model="provider/model:low",
            extra=["--no-tools"],
        )

        self.assertEqual(argv[7], "--model")
        self.assertEqual(argv[8], "provider/model:low")
        self.assertEqual(len(argv), 10)
        self.assertEqual(argv[9], "--no-tools")

    def test_policy_passes_extra_argv_through_unchanged(self) -> None:
        calls: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(
            child=child, calls=calls, extra_argv=("--no-tools", "--sandbox")
        )
        policy.decide(make_view())

        argv = calls[0]["argv"]
        self.assertEqual(argv[8], policy.model)
        self.assertEqual(argv[9:], ["--no-tools", "--sandbox"])


class SystemPromptTests(unittest.TestCase):
    def test_system_prompt_is_written_into_the_child_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls: list = []
            child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
            policy = make_policy(
                child=child,
                calls=calls,
                system_prompt="You price tickets, nothing else.",
                scratch_root=Path(tmp),
            )
            intents = policy.decide(make_view())

            self.assertTrue(intents[0].rationale.startswith("forge: "))
            work = Path(calls[0]["cwd"])
            self.assertEqual(work, Path(tmp) / "a1" / "decision-00001" / "work")
            self.assertEqual(
                (work / ".pi" / "SYSTEM.md").read_text(encoding="utf-8"),
                "You price tickets, nothing else.",
            )
            self.assertEqual(
                (work / ".pi" / "APPEND_SYSTEM.md").read_text(encoding="utf-8"),
                "",
            )

    def test_no_system_prompt_creates_no_pi_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls: list = []
            child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
            policy = make_policy(child=child, calls=calls, scratch_root=Path(tmp))
            policy.decide(make_view())

            work = Path(calls[0]["cwd"])
            self.assertFalse((work / ".pi").exists())
            self.assertEqual(list(Path(tmp).iterdir()), [])


class UsageCallbackTests(unittest.TestCase):
    def test_on_usage_receives_the_tokens_of_a_successful_decision(self) -> None:
        seen: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(child=child, on_usage=seen.append)
        policy.decide(make_view())

        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].total, 12)
        self.assertEqual(policy.usage.total, 12)
        self.assertEqual(policy.tokens_spent, 12)

    def test_on_usage_receives_the_tokens_of_a_failed_decision(self) -> None:
        seen: list = []
        child = FakeChild([message_end("not json at all"), agent_end()])
        intents = make_policy(child=child, on_usage=seen.append).decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertEqual(len(seen), 1)
        self.assertEqual(seen[0].total, 12)


class KillCheckTests(unittest.TestCase):
    def test_kill_check_that_raises_returns_the_fallback_and_spawns_nothing(self) -> None:
        calls: list = []

        def never_spawn(argv, *, cwd=None):
            calls.append(argv)
            raise AssertionError("the spawn must never be reached")

        def killed() -> None:
            raise RuntimeError("operator pulled the plug")

        policy = make_policy(spawn=never_spawn, kill_check=killed)
        intents = policy.decide(make_view())

        self.assertEqual(calls, [])
        self.assertEqual(len(intents), 1)
        self.assertTrue(intents[0].rationale.startswith("forge-fallback: run killed:"))
        self.assertIn("operator pulled the plug", intents[0].rationale)
        self.assertEqual(policy.tokens_spent, 0)

    def test_a_base_exception_from_kill_check_propagates(self) -> None:
        def killed() -> None:
            raise KeyboardInterrupt

        policy = make_policy(kill_check=killed)
        with self.assertRaises(KeyboardInterrupt):
            policy.decide(make_view())


class ScratchRootTests(unittest.TestCase):
    def test_session_dir_lives_under_the_given_scratch_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            calls: list = []
            child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
            policy = make_policy(child=child, calls=calls, scratch_root=Path(tmp))
            policy.decide(make_view())

            argv = calls[0]["argv"]
            self.assertEqual(argv[4], str(Path(tmp) / "a1" / "decision-00001" / "session"))
            self.assertTrue(Path(argv[4]).is_relative_to(Path(tmp)))


if __name__ == "__main__":
    unittest.main()


class HostileUsageTests(unittest.TestCase):
    """A child is a process obeying a prompt; its arithmetic is not trusted."""

    def test_negative_counters_are_clamped_not_subtracted(self) -> None:
        record = {"type": "message_end", "message": {"role": "assistant",
                  "usage": {"input": -50_000, "output": -1, "cacheRead": -1,
                            "cacheWrite": -1, "cost": {"total": -9.0}}}}
        usage = usage_from_record(record)
        self.assertEqual(usage.total, 0)
        self.assertEqual(usage.usd, 0.0)

    def test_a_non_finite_cost_is_zero(self) -> None:
        record = {"type": "message_end", "message": {"role": "assistant",
                  "usage": {"input": 1, "output": 1, "cost": {"total": float("inf")}}}}
        self.assertEqual(usage_from_record(record).usd, 0.0)


class ProvenanceTests(unittest.TestCase):
    """A dataset has to be able to say whether the model or the fallback decided."""

    def test_a_real_reply_counts_as_a_real_decision(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(child=child)
        policy.decide(make_view())
        self.assertEqual(policy.decisions_real, 1)
        self.assertEqual(policy.decisions_fallback, 0)
        self.assertEqual(policy.fallback_reasons, [])

    def test_a_malformed_reply_counts_as_a_fallback_with_its_reason(self) -> None:
        child = FakeChild([message_end("I would rather not."), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())
        self.assertEqual(policy.decisions_real, 0)
        self.assertEqual(policy.decisions_fallback, 1)
        self.assertEqual(len(policy.fallback_reasons), 1)
        self.assertIn("JSON", policy.fallback_reasons[0])
        self.assertTrue(all(i.rationale.startswith("forge-fallback:") for i in intents))

    def test_a_kill_order_counts_as_a_fallback_and_spawns_nothing(self) -> None:
        calls: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(
            child=child,
            calls=calls,
            kill_check=lambda: (_ for _ in ()).throw(RuntimeError("cap tripped")),
        )
        policy.decide(make_view())
        self.assertEqual(policy.decisions_fallback, 1)
        self.assertEqual(policy.fallback_reasons[0], "run killed: cap tripped")
        self.assertEqual(calls, [])

    def test_the_reason_list_is_bounded(self) -> None:
        child = FakeChild([message_end("nope"), agent_end()])
        policy = make_policy(child=child)
        for _ in range(30):
            child.stdout = iter([message_end("nope"), agent_end()])
            policy.decide(make_view())
        self.assertEqual(policy.decisions_fallback, 30)
        self.assertEqual(len(policy.fallback_reasons), 20)


# ---------------------------------------------------------------------------------------
# What a *real* child does to this adapter, pinned against the fake one.
#
# The classes below exist because the adapter had only ever run against a fake: the wire
# attaches the same message object to `message_end`, `turn_end` and `agent_end`, streams an
# in-flight usage on every `message_update`, resolves `--session-dir` against the child's
# cwd, and reports a provider failure as an `agent_end` with zero usage. Each of those broke
# or would have broken the adapter on a live child; each one has a test here.
# ---------------------------------------------------------------------------------------


def turn_end(text: str, usage: dict | None = None) -> str:
    """The same assistant message `message_end` carried, repeated on `turn_end`."""
    return json.dumps(
        {
            "type": "turn_end",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "usage": usage if usage is not None else dict(USAGE),
                "stopReason": "end",
            },
        }
    ) + "\n"


def message_update(usage: dict) -> str:
    """An in-flight usage record: top-level `usage`, no `message` key."""
    return json.dumps({"type": "message_update", "usage": usage}) + "\n"


def get_state(session_id: str) -> str:
    return json.dumps(
        {
            "id": "st-1",
            "type": "response",
            "command": "get_state",
            "success": True,
            "data": {"sessionId": session_id, "model": {"id": "deepseek/deepseek-v4.1-flash"}},
        }
    ) + "\n"


def error_message(text: str = "Request timed out") -> str:
    """Exactly what pi emits when the provider request fails: empty usage, stopReason."""
    return json.dumps(
        {
            "type": "message_end",
            "message": {
                "role": "assistant",
                "content": [],
                "usage": {"input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0},
                "stopReason": "error",
                "errorMessage": text,
            },
        }
    ) + "\n"


class CountingTests(unittest.TestCase):
    def test_turn_end_does_not_bill_the_same_message_twice(self) -> None:
        child = FakeChild(
            [
                message_end(reply("buy", FACE)),
                turn_end(reply("buy", FACE)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "))
        self.assertEqual(policy.tokens_spent, 12)  # one message, not two
        self.assertEqual(policy.budget.tokens, 12)

    def test_the_in_flight_usage_trips_the_cap_before_the_message_ends(self) -> None:
        child = FakeChild(
            [
                message_update({"input": 200, "output": 0, "cacheRead": 0, "cacheWrite": 0}),
                message_end(reply("buy", FACE)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child, token_budget=1000, max_decision_tokens=100)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("per-decision token cap 100", intents[0].rationale)
        self.assertEqual(policy.tokens_spent, 200)  # the in-flight tokens were billed too

    def test_inflight_usage_is_read_only_from_a_message_update(self) -> None:
        self.assertEqual(
            inflight_usage({"type": "message_update", "usage": {"input": 7, "output": 3}}),
            Usage(input=7, output=3),
        )
        self.assertEqual(inflight_usage({"usage": {"input": 7}}), Usage())
        self.assertEqual(inflight_usage({"type": "message_update", "usage": "nope"}), Usage())


class ZeroTokenTests(unittest.TestCase):
    def test_a_zero_token_finished_run_is_an_error_not_an_answer(self) -> None:
        child = FakeChild(
            [message_end(None, usage={"input": 0, "output": 0}), agent_end()]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertTrue(intents[0].rationale.startswith("forge-fallback: zero tokens"))
        self.assertEqual(policy.decisions_real, 0)
        self.assertEqual(policy.observations[0]["status"], "failed")
        self.assertEqual(policy.observations[0]["tokensOut"], 0)

    def test_a_provider_error_is_reported_with_the_childs_own_sentence(self) -> None:
        child = FakeChild([error_message("Request timed out"), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn(
            "child reported a failed request: Request timed out", intents[0].rationale
        )
        self.assertEqual(policy.observations[0]["status"], "failed")


class MalformedIntentTests(unittest.TestCase):
    def test_a_malformed_intent_is_refused_and_never_becomes_a_trade(self) -> None:
        payloads = (
            '{"action": "buy", "price_lamports": "100"}',      # a string price
            '{"action": "buy"}',                                # no price at all
            '{"action": "buy", "price_lamports": -5}',          # negative
            '{"action": "resell", "price_lamports": 100}',      # resell with nothing held
            '{"action": "short", "price_lamports": 100}',       # not an action
        )
        for payload in payloads:
            with self.subTest(payload=payload):
                child = FakeChild([message_end(payload), agent_end()])
                policy = make_policy(child=child)
                intents = policy.decide(make_view())
                self.assertEqual(len(intents), 1)
                self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
                self.assertEqual(policy.decisions_real, 0)


class RecordedLimitTests(unittest.TestCase):
    def test_a_timeout_kills_the_child_and_is_recorded(self) -> None:
        def slow_stream():
            yield message_end(reply("buy", FACE))
            time.sleep(0.35)
            yield agent_end()

        child = FakeChild(slow_stream(), exit_on_abort=False)
        policy = make_policy(child=child, timeout_seconds=0.2)
        intents = policy.decide(make_view())

        self.assertIn("timed out after 0.2s", intents[0].rationale)
        self.assertGreaterEqual(child.terminated, 1, "a timed-out child must be signalled")
        row = policy.observations[0]
        self.assertEqual(row["status"], "timeout")
        self.assertEqual(row["maxRunSeconds"], 0.2)
        self.assertGreaterEqual(row["seconds"], 0.2)
        self.assertTrue(row["reason"].startswith("timed out after 0.2s"))


class WireShapeTests(unittest.TestCase):
    def test_a_relative_scratch_root_gives_the_child_absolute_paths(self) -> None:
        calls: list = []
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        make_policy(child=child, calls=calls).decide(make_view())

        argv, cwd = calls[0]["argv"], calls[0]["cwd"]
        session_dir = Path(argv[4])
        self.assertTrue(session_dir.is_absolute(), session_dir)
        self.assertTrue(Path(cwd).is_absolute(), cwd)
        # pi resolves --session-dir against its own cwd, so it must never be a child of it.
        self.assertEqual(session_dir.parent, Path(cwd).parent)
        self.assertNotIn(str(Path(cwd)), str(session_dir))

    def test_the_session_id_and_the_costs_are_written_as_one_registry_row(self) -> None:
        session = "01a1b9b7-349e-72aa-bf8b-d331448f3f0e"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rows.jsonl"
            child = FakeChild([get_state(session), message_end(reply("buy", FACE)), agent_end()])
            policy = make_policy(child=child, observation_path=path, timeout_seconds=30)
            policy.decide(make_view())

            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["runId"], "forge-a1-00001")
            self.assertEqual(row["sessionId"], session)
            self.assertEqual(row["status"], "finished")
            self.assertEqual((row["tokensIn"], row["tokensOut"]), (5, 5))
            self.assertEqual((row["cacheRead"], row["cacheWrite"]), (1, 1))
            self.assertEqual(row["maxRunSeconds"], 30)
            self.assertEqual(row["tier"], "low")
            self.assertIsNone(row["reason"])
            self.assertEqual(policy.observations[0], row)

    def test_a_get_state_record_that_is_not_one_is_ignored(self) -> None:
        child = FakeChild(
            [
                json.dumps({"id": "st-1", "type": "response", "data": {}}) + "\n",
                message_end(reply("buy", FACE)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        self.assertTrue(policy.decide(make_view())[0].rationale.startswith("forge: "))
        self.assertIsNone(policy.observations[0]["sessionId"])


class ForgeBudgetTests(unittest.TestCase):
    def test_a_reservation_is_bounded_by_the_remaining_total(self) -> None:
        budget = ForgeBudget(total_tokens=100, max_decision_tokens=60)
        self.assertEqual(budget.reserve(), 60)
        self.assertEqual(budget.reserve(), 40)  # the total, not another 60
        with self.assertRaises(ForgeBudgetExceeded) as caught:
            budget.reserve()
        self.assertEqual(caught.exception.kind, "total_tokens")
        position = budget.position()
        self.assertEqual((position.tokens, position.reserved_tokens), (0, 100))
        self.assertEqual(position.decisions, 0)
        budget.cancel(100)
        self.assertEqual(budget.reserve(), 60)

    def test_a_charge_that_would_exceed_leaves_the_position_untouched(self) -> None:
        budget = ForgeBudget(total_tokens=10, max_decision_tokens=10)
        reserved = budget.reserve()
        budget.settle(reserved, Usage(input=10), 1.0)
        before = budget.position()
        with self.assertRaises(ForgeBudgetExceeded):
            budget.reserve()
        self.assertEqual(budget.position(), before)

    def test_an_overrun_is_charged_truthfully_and_refuses_everything_after(self) -> None:
        budget = ForgeBudget(total_tokens=100, max_decision_tokens=100)
        reserved = budget.reserve()
        position = budget.settle(reserved, Usage(input=140, output=1, usd=0.25), 1.5)
        self.assertEqual(position.tokens, 141)
        self.assertEqual(position.seconds, 1.5)
        self.assertEqual(position.usd, 0.25)
        self.assertIn("no further decision may spend", position.overrun or "")
        with self.assertRaises(ForgeBudgetExceeded) as caught:
            budget.reserve()
        self.assertEqual(caught.exception.kind, "overrun")

    def test_a_non_positive_cap_is_refused_at_construction(self) -> None:
        for kwargs in (
            {"total_tokens": 0, "max_decision_tokens": 10},
            {"total_tokens": 10, "max_decision_tokens": 0},
            {"total_tokens": True, "max_decision_tokens": 10},
        ):
            with self.subTest(**{k: repr(v) for k, v in kwargs.items()}):
                with self.assertRaises((ValueError, TypeError)):
                    ForgeBudget(**kwargs)


class RunnerRefusalTests(unittest.TestCase):
    def test_a_refusal_is_a_skipped_row_and_the_other_agents_keep_trading(self) -> None:
        from market_swarm import gateway as gw
        from market_swarm.config import EventSpec, RunConfig
        from market_swarm.runner import SwarmRunner

        class Refuser:
            name = "forge"

            def decide(self, view):
                return [
                    agents.Refusal(
                        agent_id=view.agent_id,
                        action="refuse",
                        price_lamports=None,
                        rationale="forge-refused: total_tokens: the cap is spent.",
                    )
                ]

        class Buyer:
            name = "scripted"

            def decide(self, view):
                return [
                    agents.Intent(
                        agent_id=view.agent_id,
                        action="buy",
                        price_lamports=FACE,
                        ticket_id=None,
                        rationale="a scripted buy",
                    )
                ]

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            config = RunConfig(
                run_id="sw-refusal",
                cluster="local",
                events=(
                    EventSpec(
                        event_id="evt_refusal",
                        face_lamports=FACE,
                        mode="capped",
                        cap_bps=CAP_BPS,
                        tickets=2,
                        rounds=1,
                        round_seconds=0,
                    ),
                ),
                agents=(make_spec("a1"), make_spec("b1")),
                total_budget_lamports=10 * FACE,
                total_budget_actions=20,
                kill_after_seconds=30,
                out_dir=out,
                dry_run=True,
                seed=7,
            )
            runner = SwarmRunner(
                config,
                gw.make_gateway("local", run_dir=Path(tmp) / "run", dry_run=True),
                policies={"a1": Refuser(), "b1": Buyer()},
            )
            summary = runner.run()

            self.assertIsNone(summary.kill_reason)
            self.assertEqual(summary.by_status.get("skipped"), 1)
            self.assertEqual(summary.by_status.get("ok"), 1)
            rows = [
                json.loads(line)
                for line in Path(summary.dataset_paths[0]).read_text().splitlines()
                if line.strip()
            ]
            rows = [row for row in rows if row.get("record") != "header"]
            refused = [row for row in rows if row["agent_id"] == "a1"]
            self.assertEqual(len(refused), 1)
            self.assertEqual(refused[0]["status"], "skipped")
            self.assertIn("forge-refused", refused[0]["rationale"])
            self.assertIsNone(refused[0]["price_lamports"])
            self.assertTrue(refused[0]["synthetic"])
            # A decision nobody took is not a purchase. The row used to say action="buy",
            # and the repo's own summariser then counted the refusal as a buy.
            self.assertEqual(refused[0]["action"], "refuse")

            from market_swarm.datasets import summarise

            summary_of_the_file = summarise(Path(summary.dataset_paths[0]))
            self.assertEqual(summary_of_the_file["by_action"], {"buy": 1, "refuse": 1})
            self.assertEqual(
                summary_of_the_file["by_action_status"],
                {"buy": {"ok": 1}, "refuse": {"skipped": 1}},
            )
            self.assertTrue(all(row["chain"] == "simulated" for row in rows))


class ReapPipeTests(unittest.TestCase):
    def test_the_reap_closes_the_stdout_pipe_and_the_stderr_log(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        closed: list[str] = []

        class ClosingStdout:
            def __iter__(self):
                return iter(())

            def close(self) -> None:
                closed.append("stdout")

        class ClosingLog:
            def close(self) -> None:
                closed.append("stderr")

        child.stdout = ClosingStdout()
        child.forge_stderr_log = ClosingLog()
        make_policy(child=child).decide(make_view())

        self.assertEqual(sorted(closed), ["stderr", "stdout"])

    def test_the_exit_code_is_read_after_the_reap_not_before_it(self) -> None:
        child = FakeChild(
            [message_end(reply("buy", FACE)), agent_end()], exit_on_abort=False
        )
        policy = make_policy(child=child)
        policy.decide(make_view())

        # The fake child only gains a return code from `terminate`, i.e. from the reap. A row
        # that read `poll()` first would carry `None` for every real child, because a
        # `pi --mode rpc` child is still alive at the moment its decision completes.
        self.assertEqual(child.returncode, -15)
        self.assertEqual(policy.observations[0]["exitCode"], -15)


class RealPipeTests(unittest.TestCase):
    """The read path every live child uses, exercised on a real pipe.

    Every other test in this file feeds `iter(lines)`, where `_fileno` is None, so the
    `selectors` branch that a live read actually takes was never executed. These use
    `os.pipe()`: a real fd, real reads, real EOF.
    """

    def _reader(self, payload: bytes, *, close_write: bool = True):
        import os

        read_fd, write_fd = os.pipe()
        reader = os.fdopen(read_fd, "rb")
        self.addCleanup(reader.close)
        os.write(write_fd, payload)
        if close_write:
            os.close(write_fd)
        else:
            self.addCleanup(os.close, write_fd)
        child = type("PipeChild", (), {"stdout": reader, "pid": 1})()
        return child

    def _records(self, child, seconds: float = 5.0) -> list[str]:
        return list(
            ForgePolicy._iter_records(None, child, time.monotonic() + seconds)  # type: ignore[arg-type]
        )

    def test_complete_lines_come_back_and_eof_ends_the_stream(self) -> None:
        child = self._reader(b'{"type":"agent_start"}\n{"type":"agent_end"}\n')
        lines = self._records(child)
        self.assertEqual(
            [json.loads(line) for line in lines],
            [{"type": "agent_start"}, {"type": "agent_end"}],
        )

    def test_a_final_line_without_a_newline_is_not_lost(self) -> None:
        child = self._reader(b'{"type":"agent_end","willRetry":false}')
        lines = self._records(child)
        self.assertEqual(len(lines), 1)
        self.assertFalse(json.loads(lines[0])["willRetry"])

    def test_a_silent_pipe_trips_the_deadline_instead_of_hanging(self) -> None:
        import market_swarm.forge_policy as fp

        child = self._reader(b"", close_write=False)
        started = time.monotonic()
        with self.assertRaises(fp._Timeout):
            self._records(child, seconds=0.2)
        self.assertLess(time.monotonic() - started, 2.0)


# ---------------------------------------------------------------------------------------
# The review of feature 9 (tmp/review/feature-9.md) measured five billing and reply defects
# against this adapter. Each one is pinned below, against the fake child and never a
# provider: a message billed twice, a message that reported no usage, a provider error that
# retried to a good answer, a reply with two intents in it, and a price above the ceiling.
# ---------------------------------------------------------------------------------------


def message_end_with_id(
    message_id: str, text: str, usage: dict | None = None, stop: str = "end"
) -> str:
    """An assistant `message_end` that carries an id, as the wire sometimes does."""
    return json.dumps(
        {
            "type": "message_end",
            "message": {
                "id": message_id,
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "usage": usage if usage is not None else dict(USAGE),
                "stopReason": stop,
            },
        }
    ) + "\n"


def message_end_without_usage(text: str) -> str:
    """An assistant `message_end` whose message has no `usage` key at all."""
    return json.dumps(
        {
            "type": "message_end",
            "message": {
                "role": "assistant",
                "content": [{"type": "text", "text": text}],
                "stopReason": "end",
            },
        }
    ) + "\n"


def update_with_id(message_id: str, usage: dict) -> str:
    return json.dumps(
        {"type": "message_update", "messageId": message_id, "usage": usage}
    ) + "\n"


#: A message worth a measurable amount, so a double charge is unmistakable.
BIG = {
    "input": 1000,
    "output": 100,
    "cacheRead": 0,
    "cacheWrite": 0,
    "cost": {"total": 0.001},
}
BIG_USAGE = Usage(input=1000, output=100, usd=0.001)


class BillingOrderTests(unittest.TestCase):
    """One assistant message is billed once, whatever order the wire repeats it in."""

    def test_a_trailing_update_after_the_message_end_is_not_billed_twice(self) -> None:
        child = FakeChild(
            [
                message_end(reply("buy", FACE), usage=dict(BIG)),
                message_update(dict(BIG)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "))
        self.assertEqual(policy.usage, BIG_USAGE)
        self.assertEqual(policy.tokens_spent, 1100)
        row = policy.observations[0]
        self.assertEqual(row["tokensIn"], 1000)
        self.assertEqual(row["tokensOut"], 100)

    def test_a_trailing_update_is_ignored_by_message_id_when_one_is_carried(self) -> None:
        # The wire may not carry an id, but when it does the update is matched to the
        # message that already ended even if its numbers changed.
        doubled = {
            "input": 2000,
            "output": 200,
            "cacheRead": 0,
            "cacheWrite": 0,
            "cost": {"total": 0.002},
        }
        child = FakeChild(
            [
                message_end_with_id("m1", reply("buy", FACE), usage=dict(BIG)),
                update_with_id("m1", doubled),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        policy.decide(make_view())

        self.assertEqual(policy.usage, BIG_USAGE)

    def test_an_in_flight_update_before_its_message_ends_is_billed_once(self) -> None:
        child = FakeChild(
            [
                message_update(dict(BIG)),
                message_end(reply("buy", FACE), usage=dict(BIG)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        policy.decide(make_view())

        self.assertEqual(policy.usage, BIG_USAGE)


class NoUsageTests(unittest.TestCase):
    """A reporting gap is not a free decision, and it is not a provider error either."""

    def test_a_message_end_with_no_usage_block_is_an_unknown_cost_not_zero(self) -> None:
        child = FakeChild(
            [message_end_without_usage(reply("buy", FACE)), agent_end()]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("no usage block", intents[0].rationale)
        self.assertIn("unknown, not zero", intents[0].rationale)
        # Nothing was invented: the adapter charges only what it observed.
        self.assertEqual(policy.usage.total, 0)
        row = policy.observations[0]
        self.assertEqual(row["status"], "failed")
        self.assertIs(row["costUnknown"], True)
        self.assertIsNone(row["tokensIn"])
        self.assertIsNone(row["tokensOut"])
        self.assertIsNone(row["costUsd"])

    def test_a_missing_usage_block_does_not_leave_the_row_looking_free(self) -> None:
        # A zero would claim the decision cost nothing; null says it cost an unknown amount.
        child = FakeChild([message_end_without_usage(reply("buy", FACE)), agent_end()])
        policy = make_policy(child=child)
        policy.decide(make_view())
        row = policy.observations[0]
        self.assertNotEqual(row["tokensIn"], 0)
        self.assertNotEqual(row["costUsd"], 0)

    def test_an_update_with_usage_and_an_end_without_it_bills_the_update(self) -> None:
        # The stream did report the number, on the update; the end simply lacks the block.
        child = FakeChild(
            [
                message_update(dict(BIG)),
                message_end_without_usage(reply("buy", FACE)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)
        self.assertEqual(policy.usage, BIG_USAGE)
        self.assertIs(policy.observations[0]["costUnknown"], False)


class ProviderRetryTests(unittest.TestCase):
    """An error that retries to a good answer is the good answer."""

    def test_an_error_retried_to_a_good_answer_is_not_thrown_away(self) -> None:
        child = FakeChild(
            [
                error_message("Request timed out"),
                agent_end(will_retry=True),
                message_end(reply("buy", FACE), usage=dict(BIG)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertEqual(len(intents), 1)
        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)
        self.assertEqual(policy.decisions_real, 1)
        self.assertEqual(policy.decisions_fallback, 0)
        self.assertEqual(policy.usage, BIG_USAGE)
        self.assertEqual(policy.observations[0]["status"], "finished")

    def test_an_error_only_run_still_reports_the_error(self) -> None:
        child = FakeChild([error_message("429 Too Many Requests"), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("child reported a failed request: 429", intents[0].rationale)

    def test_a_no_usage_error_record_does_not_unprice_a_later_answer(self) -> None:
        # A provider that omits the usage block on the failure record has not made the
        # retried answer unpriced: the answer's own usage is the charge.
        bare_error = json.dumps(
            {
                "type": "message_end",
                "message": {
                    "role": "assistant",
                    "content": [],
                    "stopReason": "error",
                    "errorMessage": "Request timed out",
                },
            }
        ) + "\n"
        child = FakeChild(
            [
                bare_error,
                agent_end(will_retry=True),
                message_end(reply("buy", FACE), usage=dict(BIG)),
                agent_end(),
            ]
        )
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)
        self.assertEqual(policy.usage, BIG_USAGE)
        # The row still says part of the charge was never reported, so its counters are
        # withheld rather than presented as a total.
        self.assertIs(policy.observations[0]["costUnknown"], True)
        self.assertIsNone(policy.observations[0]["tokensIn"])


class ReplyContractTests(unittest.TestCase):
    """One JSON object, and a price the chain would admit."""

    def test_two_json_objects_in_one_reply_are_refused_not_resolved(self) -> None:
        text = reply("buy", FACE) + "\n" + reply("list", FACE)
        child = FakeChild([message_end(text), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("2 JSON objects", intents[0].rationale)
        self.assertEqual(policy.decisions_real, 0)

    def test_a_json_array_of_two_intents_is_refused(self) -> None:
        text = "[" + reply("buy", FACE) + "," + reply("list", FACE) + "]"
        child = FakeChild([message_end(text), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("2 JSON objects", intents[0].rationale)

    def test_a_nested_object_is_not_counted_as_a_second_reply(self) -> None:
        # A rationale that happens to contain braces inside a string must not trip the
        # one-object rule.
        payload = json.dumps(
            {"action": "buy", "price_lamports": FACE, "rationale": 'a {braced} note'}
        )
        child = FakeChild([message_end(payload), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)

    def test_a_price_above_the_event_ceiling_is_refused_in_capped_mode(self) -> None:
        child = FakeChild([message_end(reply("buy", CEILING + 1)), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge-fallback: "))
        self.assertIn("event ceiling", intents[0].rationale)
        self.assertEqual(policy.decisions_real, 0)

    def test_a_price_at_the_event_ceiling_is_admitted_in_capped_mode(self) -> None:
        child = FakeChild([message_end(reply("buy", CEILING)), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(make_view())

        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)
        self.assertEqual(intents[0].price_lamports, CEILING)

    def test_the_same_price_is_admitted_in_monitored_mode(self) -> None:
        # Monitored mode has no event cap to enforce: the field maximum is the ceiling, and
        # an over-cap ask is exactly what the mode exists to observe on chain.
        cap_bps = 65535
        view = agents.MarketView(
            round=3,
            rounds_left=5,
            event_id=EVENT,
            mode="monitored",
            face_lamports=FACE,
            cap_bps=cap_bps,
            ceiling_lamports=agents.cap_ceiling(FACE, cap_bps),
            tickets_available=4,
            holdings=(),
            last_prices=(FACE,),
            refused_attempts=0,
            agent_id="a1",
            seed=7,
        )
        child = FakeChild([message_end(reply("buy", CEILING + 1)), agent_end()])
        policy = make_policy(child=child)
        intents = policy.decide(view)

        self.assertTrue(intents[0].rationale.startswith("forge: "), intents[0].rationale)
        self.assertEqual(intents[0].price_lamports, CEILING + 1)

    def test_the_accepted_reply_records_how_many_objects_it_had(self) -> None:
        child = FakeChild([message_end(reply("buy", FACE)), agent_end()])
        policy = make_policy(child=child)
        policy.decide(make_view())

        self.assertEqual(policy.observations[0]["replyObjects"], 1)

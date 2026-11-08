"""The live-LLM layer: personas, the sandbox argv, and the run-wide cap.

Three properties are pinned here and nothing else is. A persona quotes the reply contract
verbatim, so the string a child is graded on and the string it was given cannot drift apart.
The hardened flags contain exactly one extension and one provider path, so a child cannot
acquire behaviour nobody wrote for it. And the cap trips once, thread-safely, with the
reason it actually tripped on, because a run that stops for the wrong reason is a run whose
report is wrong.

Nothing in this file spawns a process, calls a network, or touches a provider. The
`build_llm_policy` test patches the policy class with a recorder, so it checks the wiring
without depending on the real class's shape.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from types import MappingProxyType

from market_swarm import forge_policy, llm
from market_swarm.config import AgentSpec
from market_swarm.forge_policy import REPLY_CONTRACT, Usage

REQUIRED_PERSONAS = (
    "buyer",
    "holder",
    "flipper",
    "scalper",
    "sniper",
    "panic",
    "greater_fool",
)

#: The word each persona's objective has to carry, so a copy-paste between two entries is
#: caught rather than merely suspected.
OBJECTIVE_MARKER = {
    "buyer": "face",
    "holder": "last round",
    "flipper": "relist",
    "scalper": "cap",
    "sniper": "last round",
    "panic": "sell low",
    "greater_fool": "buy high",
}

EM_DASH = "\u2014"

#: An absolute path, in the shapes this project could accidentally leak: a POSIX path from
#: its first separator, or a home-relative one.
ABSOLUTE_PATH = re.compile(r"(?<![\w.])/(?:home|root|usr|etc|opt|tmp|var|mnt)\b|~/")


def make_spec(
    agent_id: str = "a1", policy: str = "scalper", seed: int = 7
) -> AgentSpec:
    return AgentSpec(
        agent_id=agent_id,
        policy=policy,
        wallet_label=f"wallet-{agent_id}",
        seed=seed,
        budget_lamports=100_000_000,
        budget_actions=20,
    )


class StubLlm:
    """The four fields `build_llm_policy` reads off the run's llm block."""

    def __init__(
        self,
        *,
        tier: str = "low",
        per_agent_token_budget: int = 50_000,
        max_concurrent: int = 2,
        timeout_seconds: float = 90,
    ) -> None:
        self.tier = tier
        self.per_agent_token_budget = per_agent_token_budget
        self.max_concurrent = max_concurrent
        self.timeout_seconds = timeout_seconds


class TestPersonas(unittest.TestCase):
    def test_every_required_persona_exists(self):
        self.assertEqual(set(llm.PERSONAS), set(REQUIRED_PERSONAS))

    def test_personas_are_read_only(self):
        self.assertIsInstance(llm.PERSONAS, MappingProxyType)
        with self.assertRaises(TypeError):
            llm.PERSONAS["buyer"] = "something else"  # type: ignore[index]

    def test_every_persona_is_non_empty_text(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                prompt = llm.PERSONAS[name]
                self.assertIsInstance(prompt, str)
                self.assertTrue(prompt.strip())
                self.assertEqual(prompt, prompt.strip())

    def test_every_persona_quotes_the_reply_contract_verbatim(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                self.assertIn(REPLY_CONTRACT, llm.PERSONAS[name])

    def test_every_persona_says_the_market_is_synthetic(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                prompt = llm.PERSONAS[name]
                self.assertIn("synthetic", prompt)
                self.assertIn("not evidence", prompt)

    def test_every_persona_says_no_tools_are_available(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                prompt = llm.PERSONAS[name]
                self.assertIn("no tools", prompt)

    def test_every_persona_names_its_own_objective(self):
        for name, marker in OBJECTIVE_MARKER.items():
            with self.subTest(persona=name):
                self.assertIn(marker, llm.PERSONAS[name])

    def test_no_persona_contains_an_em_dash_or_an_absolute_path(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                prompt = llm.PERSONAS[name]
                self.assertNotIn(EM_DASH, prompt)
                self.assertIsNone(
                    ABSOLUTE_PATH.search(prompt),
                    f"{name} quotes a path: {ABSOLUTE_PATH.search(prompt)!r}",
                )
                self.assertNotIn("~/", prompt)
                self.assertNotIn("\\", prompt)

    def test_no_persona_names_the_repository_or_the_operator(self):
        forbidden = ("market_swarm", "ticketPricing", "ticketpath", "andrew", "friend")
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                prompt = llm.PERSONAS[name].lower()
                for word in forbidden:
                    self.assertNotIn(word.lower(), prompt)

    def test_persona_for_returns_the_mapping_value(self):
        for name in REQUIRED_PERSONAS:
            with self.subTest(persona=name):
                self.assertEqual(llm.persona_for(name), llm.PERSONAS[name])

    def test_persona_for_refuses_an_unknown_name_and_lists_the_valid_ones(self):
        with self.assertRaises(ValueError) as caught:
            llm.persona_for("scalper-ish")
        message = str(caught.exception)
        self.assertIn("scalper-ish", message)
        for name in REQUIRED_PERSONAS:
            self.assertIn(name, message)

    def test_persona_for_refuses_a_non_string(self):
        with self.assertRaises(ValueError):
            llm.persona_for(None)  # type: ignore[arg-type]


class TestHardenedFlags(unittest.TestCase):
    def test_contains_every_safety_switch(self):
        flags = llm.hardened_flags()
        for switch in (
            "--no-extensions",
            "--no-tools",
            "--no-skills",
            "--no-context-files",
            "--no-mcp",
            "--no-prompt-templates",
            "--approve",
        ):
            with self.subTest(flag=switch):
                self.assertIn(switch, flags)

    def test_exactly_one_extension_and_it_is_the_model_provider(self):
        flags = llm.hardened_flags()
        self.assertEqual(flags.count("-e"), 1)
        index = flags.index("-e")
        self.assertTrue(
            flags[index + 1].endswith("pi-commandcode-provider/index.ts"),
            flags[index + 1],
        )

    def test_no_other_extension_path_is_passed(self):
        flags = llm.hardened_flags()
        paths = [flag for flag in flags if flag.endswith(".ts") or flag.startswith("/")]
        self.assertEqual(len(paths), 1, paths)

    def test_the_order_is_fixed(self):
        self.assertEqual(
            llm.hardened_flags(),
            (
                "--no-extensions",
                "-e",
                llm.PROVIDER_EXTENSION,
                "--no-tools",
                "--no-skills",
                "--no-context-files",
                "--no-mcp",
                "--no-prompt-templates",
                "--approve",
            ),
        )

    def test_an_override_replaces_the_default_path(self):
        flags = llm.hardened_flags("/somewhere/else/index.ts")
        self.assertEqual(flags[flags.index("-e") + 1], "/somewhere/else/index.ts")

    def test_the_default_path_is_resolved_from_home_at_import(self):
        expected = os.path.expanduser(
            "~/.pi/agent/npm/node_modules/pi-commandcode-provider/index.ts"
        )
        self.assertEqual(llm.PROVIDER_EXTENSION, expected)
        self.assertTrue(os.path.isabs(llm.PROVIDER_EXTENSION))

    def test_default_provider_extension_honours_its_override(self):
        override = os.path.join(tempfile.gettempdir(), "override.ts")
        self.assertEqual(llm._default_provider_extension(override), override)
        self.assertEqual(llm._default_provider_extension(), llm.PROVIDER_EXTENSION)

    def test_the_module_source_hardcodes_no_home_path(self):
        source = Path(llm.__file__).read_text(encoding="utf-8")
        self.assertNotIn(os.path.expanduser("~"), source)
        self.assertNotIn(EM_DASH, source)


class TestLlmBudget(unittest.TestCase):
    def test_charges_accumulate_across_the_four_counters(self):
        budget = llm.LlmBudget(total_token_budget=10_000)
        budget.charge(Usage(input=10, output=20, cache_read=30, cache_write=40, usd=0.5))
        budget.charge(Usage(input=1, output=2, cache_read=3, cache_write=4, usd=0.25))
        snapshot = budget.snapshot()
        self.assertEqual(snapshot["input"], 11)
        self.assertEqual(snapshot["output"], 22)
        self.assertEqual(snapshot["cache_read"], 33)
        self.assertEqual(snapshot["cache_write"], 44)
        self.assertEqual(snapshot["total_tokens"], 110)
        self.assertAlmostEqual(budget.usd, 0.75, places=12)
        self.assertIsNone(budget.trip_reason)

    def test_the_usage_property_is_a_forge_policy_usage(self):
        budget = llm.LlmBudget(total_token_budget=10_000)
        budget.charge(Usage(input=5, output=5, cache_read=1, cache_write=1, usd=0.001))
        aggregate = budget.usage
        self.assertIsInstance(aggregate, Usage)
        self.assertEqual(aggregate.total, 12)
        self.assertAlmostEqual(aggregate.usd, 0.001, places=12)

    def test_a_missing_counter_counts_as_zero_instead_of_raising(self):
        class Partial:
            input = 7
            usd = 0.001

        budget = llm.LlmBudget(total_token_budget=10_000)
        budget.charge(Partial())  # must not raise: a gap in reporting is not a crash
        self.assertEqual(budget.snapshot()["total_tokens"], 7)

    def test_the_token_trip_fires_once_the_running_total_passes_the_cap(self):
        budget = llm.LlmBudget(total_token_budget=100)
        budget.charge(Usage(input=60, output=40))
        self.assertIsNone(budget.trip_reason)
        budget.charge(Usage(input=1))
        self.assertEqual(
            budget.trip_reason, "llm token budget exceeded: 101 of 100 tokens"
        )

    def test_the_cost_trip_fires_once_the_dollar_total_passes_the_cap(self):
        budget = llm.LlmBudget(total_token_budget=10_000, cost_cap_usd=0.002)
        budget.charge(Usage(input=1, usd=0.002))
        self.assertIsNone(budget.trip_reason)
        budget.charge(Usage(input=1, usd=0.001))
        self.assertIsNotNone(budget.trip_reason)
        self.assertIn("llm cost cap exceeded", budget.trip_reason or "")
        self.assertIn("$0.003", budget.trip_reason or "")
        self.assertIn("$0.002", budget.trip_reason or "")

    def test_the_first_trip_reason_wins(self):
        budget = llm.LlmBudget(total_token_budget=10, cost_cap_usd=0.01)
        budget.charge(Usage(input=1))  # under both caps
        budget.charge(Usage(input=100, usd=100.0))  # over both at once
        first = budget.trip_reason
        self.assertIn("token budget exceeded", first or "")
        budget.charge(Usage(input=100, usd=100.0))
        self.assertEqual(budget.trip_reason, first)

    def test_check_returns_none_while_the_run_is_allowed(self):
        budget = llm.LlmBudget(total_token_budget=100)
        budget.charge(Usage(input=1))
        self.assertIsNone(budget.check())

    def test_check_raises_with_the_reason(self):
        budget = llm.LlmBudget(total_token_budget=10)
        budget.charge(Usage(input=11))
        with self.assertRaises(llm.LlmKilled) as caught:
            budget.check()
        self.assertEqual(str(caught.exception), budget.trip_reason)
        self.assertEqual(caught.exception.reason, budget.trip_reason)

    def test_llm_killed_is_a_runtime_error_carrying_its_reason(self):
        error = llm.LlmKilled("why")
        self.assertIsInstance(error, RuntimeError)
        self.assertEqual(error.reason, "why")
        self.assertEqual(str(error), "why")

    def test_snapshot_is_json_serialisable_with_the_documented_keys(self):
        budget = llm.LlmBudget(total_token_budget=10_000, cost_cap_usd=1.0)
        budget.charge(Usage(input=1, output=2, cache_read=3, cache_write=4, usd=0.1))
        snapshot = budget.snapshot()
        # The documented keys must all be there; the class may carry extra fields beside
        # them, and a meta sidecar that says more than a reader needs is not a defect.
        self.assertLessEqual(
            {
                "trip_reason",
                "total_tokens",
                "input",
                "output",
                "cache_read",
                "cache_write",
                "usd",
                "total_token_budget",
                "cost_cap_usd",
            },
            set(snapshot),
        )
        self.assertEqual(json.loads(json.dumps(snapshot)), snapshot)

    def test_concurrent_charges_are_not_lost(self):
        threads, per_thread = 8, 50
        budget = llm.LlmBudget(total_token_budget=1_000_000)

        def work() -> None:
            for _ in range(per_thread):
                budget.charge(Usage(input=10, output=5, usd=0.000001))

        workers = [threading.Thread(target=work) for _ in range(threads)]
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join()

        snapshot = budget.snapshot()
        self.assertEqual(snapshot["input"], threads * per_thread * 10)
        self.assertEqual(snapshot["output"], threads * per_thread * 5)
        self.assertEqual(snapshot["total_tokens"], threads * per_thread * 15)

    def test_a_zero_or_negative_token_budget_is_refused(self):
        for value in (0, -1, -10_000):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    llm.LlmBudget(total_token_budget=value)

    def test_a_non_positive_cost_cap_is_refused(self):
        for value in (0, 0.0, -0.01):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    llm.LlmBudget(total_token_budget=100, cost_cap_usd=value)

    def test_a_non_numeric_budget_or_cost_cap_is_refused(self):
        with self.assertRaises(TypeError):
            llm.LlmBudget(total_token_budget="100")  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            llm.LlmBudget(total_token_budget=100, cost_cap_usd="1.00")  # type: ignore[arg-type]

    def test_a_configured_price_table_prices_a_child_that_reports_no_cost(self):
        class Prices:
            """Stands in for a config price table: tokens in, dollars out."""

            def cost_usd(self, usage) -> float:
                return 0.002

        budget = llm.LlmBudget(total_token_budget=1_000, prices=Prices())
        budget.charge(Usage(input=10))
        self.assertAlmostEqual(budget.usd, 0.002, places=12)
        self.assertEqual(budget.snapshot()["cost_basis"], "table")

    def test_a_priced_table_still_trips_the_cost_cap(self):
        class Prices:
            def cost_usd(self, usage) -> float:
                return 0.002

        budget = llm.LlmBudget(
            total_token_budget=1_000, cost_cap_usd=0.001, prices=Prices()
        )
        budget.charge(Usage(input=10))
        self.assertIsNotNone(budget.trip_reason)
        self.assertIn("llm cost cap exceeded", budget.trip_reason or "")

    def test_the_cost_basis_says_where_the_dollars_came_from(self):
        unpriced = llm.LlmBudget(total_token_budget=1_000)
        unpriced.charge(Usage(input=1))
        self.assertEqual(unpriced.snapshot()["cost_basis"], "unpriced")

        streamed = llm.LlmBudget(total_token_budget=1_000)
        streamed.charge(Usage(input=1, usd=0.0001))
        self.assertEqual(streamed.snapshot()["cost_basis"], "stream")

    def test_no_cost_cap_means_no_dollar_limit(self):
        budget = llm.LlmBudget(total_token_budget=10)
        budget.charge(Usage(input=1, usd=1_000.0))
        self.assertIsNone(budget.trip_reason)
        self.assertIsNone(budget.snapshot()["cost_cap_usd"])


class Recorder:
    """Stands in for `ForgePolicy`: records the constructor call and nothing else."""

    calls: list[tuple[tuple, dict]] = []

    def __init__(self, *args, **kwargs) -> None:
        Recorder.calls.append((args, kwargs))


class TestBuildLlmPolicy(unittest.TestCase):
    def setUp(self) -> None:
        Recorder.calls = []
        scratch = tempfile.TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self._scratch = scratch.name
        self._real_policy = forge_policy.ForgePolicy
        forge_policy.ForgePolicy = Recorder  # type: ignore[misc]

    def tearDown(self) -> None:
        forge_policy.ForgePolicy = self._real_policy  # type: ignore[misc]

    def build(self, spec=None, *, spawn=None, llm_block=None, budget=None):
        """Build once through the recorder and return (its (args, kwargs), the budget)."""
        spec = make_spec() if spec is None else spec
        llm_block = llm_block or StubLlm()
        budget = budget or llm.LlmBudget(total_token_budget=100_000)
        before = len(Recorder.calls)
        # Outside the repository: a live child's cwd may not sit in the tree, and
        # `build_llm_policy` refuses one that does.
        llm.build_llm_policy(
            spec,
            llm=llm_block,
            budget=budget,
            scratch_root=self._scratch,
            spawn=spawn,
        )
        self.assertEqual(len(Recorder.calls), before + 1)
        return Recorder.calls[-1], budget

    def test_the_spec_is_passed_positionally_and_the_rest_by_keyword(self):
        (args, kwargs), _ = self.build()
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0].agent_id, "a1")
        self.assertEqual(
            set(kwargs),
            {
                "tier",
                "token_budget",
                "max_decision_tokens",
                "max_concurrent",
                "timeout_seconds",
                "acknowledge_cost",
                "spawn",
                "system_prompt",
                "extra_argv",
                "on_usage",
                "kill_check",
                "scratch_root",
                "intended_cap_bps",
            },
        )

    def test_the_per_agent_budget_and_limits_come_off_the_llm_block(self):
        block = StubLlm(
            tier="best",
            per_agent_token_budget=12_345,
            max_concurrent=4,
            timeout_seconds=45,
        )
        (_, kwargs), _ = self.build(llm_block=block)
        self.assertEqual(kwargs["tier"], "best")
        self.assertEqual(kwargs["token_budget"], 12_345)
        self.assertEqual(kwargs["max_concurrent"], 4)
        self.assertEqual(kwargs["timeout_seconds"], 45)
        self.assertIs(kwargs["acknowledge_cost"], True)

    def test_the_persona_matches_the_spec_policy(self):
        (_, kwargs), _ = self.build(make_spec(policy="scalper"))
        self.assertEqual(kwargs["system_prompt"], llm.PERSONAS["scalper"])
        (_, other), _ = self.build(make_spec(agent_id="a2", policy="panic"))
        self.assertEqual(other["system_prompt"], llm.PERSONAS["panic"])

    def test_the_hardened_flags_are_the_ones_passed(self):
        (_, kwargs), _ = self.build()
        self.assertEqual(kwargs["extra_argv"], llm.hardened_flags())

    def test_the_budget_object_is_wired_as_both_sinks(self):
        (_, kwargs), budget = self.build()
        self.assertEqual(kwargs["on_usage"], budget.charge)
        self.assertIs(kwargs["on_usage"].__self__, budget)
        self.assertEqual(kwargs["kill_check"], budget.check)
        self.assertIs(kwargs["kill_check"].__self__, budget)

    def test_the_kill_check_actually_kills(self):
        (_, kwargs), budget = self.build()
        budget.charge(Usage(input=200_000))
        with self.assertRaises(llm.LlmKilled):
            kwargs["kill_check"]()
        kwargs["on_usage"](Usage(input=1))  # the charge sink still swallows it
        self.assertIsNotNone(budget.trip_reason)

    def test_the_spawn_and_scratch_root_are_passed_through(self):
        def spawn(argv, *, cwd):  # stands in for `ForgePolicy`'s injected spawn
            return (argv, cwd)

        (args, kwargs), _ = self.build(spawn=spawn)
        self.assertIs(kwargs["spawn"], spawn)
        self.assertEqual(str(kwargs["scratch_root"]), str(Path(self._scratch).resolve()))

    def test_no_spawn_means_none(self):
        (_, kwargs), _ = self.build()
        self.assertIsNone(kwargs["spawn"])

    def test_an_unknown_spec_policy_stops_the_build(self):
        with self.assertRaises(ValueError) as caught:
            self.build(make_spec(policy="scaler"))
        self.assertIn("scaler", str(caught.exception))
        self.assertEqual(Recorder.calls, [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

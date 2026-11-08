"""The CLI verbs: what they print, what they refuse, and what they never touch.

The gateway is stubbed by putting a module in `sys.modules` for the duration of a test, so
`run` can be exercised end to end without the real gateway existing and without a socket.
The absent-gateway cases set the entry to `None`, which makes the import fail the way a
missing module does.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path

import market_swarm
from market_swarm.cli import main
from market_swarm.config import ceiling_lamports, effective_cap_bps
from market_swarm.datasets import verify_dataset

MISSING = object()


class StubChain:
    def __init__(self, spec) -> None:
        self.event_id = spec.event_id
        self.mode = spec.mode
        self.cap_bps = effective_cap_bps(spec.mode, spec.cap_bps)
        self.face_lamports = spec.face_lamports
        self.ceiling_lamports = ceiling_lamports(spec.face_lamports, self.cap_bps)
        self.house = 0
        self.sends = 0

    def open_account(self, wallet_label: str) -> str:
        return f"addr-{wallet_label}"

    def stock(self, count: int) -> None:
        self.house += count

    def transfer(
        self,
        *,
        from_label: str,
        to_label: str,
        price_lamports: int,
        charge_artist_fee: bool = True,
        charge_flip_tax: bool = True,
    ):
        self.sends += 1
        status = "ok" if price_lamports <= self.ceiling_lamports else "refused"
        return types.SimpleNamespace(
            status=status,
            signature=f"sig-{self.sends}",
            slot=self.sends,
            block_time=1_700_000_000 + self.sends,
            error_code=None if status == "ok" else 6010,
            latency_ms=1,
            logs=(),
        )

    def read_record(self) -> dict:
        return {"face": self.face_lamports, "cap_bps": self.cap_bps, "status": 1}


class StubGateway:
    def __init__(
        self, cluster: str, run_dir: Path, dry_run: bool, program: str = "v1"
    ) -> None:
        self.cluster = cluster
        self.run_dir = run_dir
        self.dry_run = dry_run
        # Carried through because the runner reads it back: a gateway that did not say which
        # program it drives would let a config name one and a run record the other.
        self.program = program
        self.started = False
        self.stopped = False

    def start(self) -> dict:
        self.started = True
        return {"cluster": self.cluster, "program": self.program, "healthy": True}

    def stop(self) -> None:
        self.stopped = True

    def create_event(self, spec) -> StubChain:
        return StubChain(spec)

    def status(self) -> dict:
        return {"cluster": self.cluster, "program": self.program, "healthy": True}


def _gateway_module(shape: str = "cluster") -> types.ModuleType:
    module = types.ModuleType("market_swarm.gateway")
    if shape == "config":
        module.make_gateway = lambda config: StubGateway(
            config.cluster, Path(config.out_dir), config.dry_run, config.program
        )
    else:
        module.make_gateway = lambda cluster, *, run_dir, dry_run=False, program="v1": StubGateway(
            cluster, Path(run_dir), dry_run, program
        )
    return module


class CliCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "out"
        self._saved_module = sys.modules.get("market_swarm.gateway", MISSING)
        self._saved_attr = market_swarm.__dict__.get("gateway", MISSING)
        self.addCleanup(self._restore_gateway)

    def _restore_gateway(self) -> None:
        if self._saved_module is MISSING:
            sys.modules.pop("market_swarm.gateway", None)
        else:
            sys.modules["market_swarm.gateway"] = self._saved_module
        if self._saved_attr is MISSING:
            market_swarm.__dict__.pop("gateway", None)
        else:
            market_swarm.gateway = self._saved_attr

    def use_gateway(self, module) -> None:
        sys.modules["market_swarm.gateway"] = module
        if module is None:
            market_swarm.__dict__.pop("gateway", None)
        else:
            market_swarm.gateway = module

    def write_config(self, *, mode: str = "capped", cap_bps: int | None = 2500,
                     rounds: int = 3, agents: int = 2,
                     kill_after_seconds: float | None = None,
                     llm: dict | None = None) -> Path:
        payload = {
            "run_id": "sw-cli-test",
            "cluster": "local",
            "events": [
                {
                    "event_id": "ev",
                    "face_lamports": 1_000_000,
                    "mode": mode,
                    "tickets": 5,
                    "rounds": rounds,
                    "round_seconds": 60,
                }
            ],
            "agents": [
                {
                    "agent_id": f"a{index}",
                    "policy": "buyer",
                    "wallet_label": f"w-a{index}",
                    "seed": index,
                    "budget_lamports": 10_000_000,
                    "budget_actions": 20,
                }
                for index in range(1, agents + 1)
            ],
            "total_budget_lamports": 100_000_000,
            "total_budget_actions": 100,
            "out_dir": str(self.out),
        }
        if cap_bps is not None:
            payload["events"][0]["cap_bps"] = cap_bps
        if kill_after_seconds is not None:
            payload["kill_after_seconds"] = kill_after_seconds
        if llm is not None:
            payload["llm"] = llm
        path = self.root / "run.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def call(self, *argv: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = main(list(argv))
            except SystemExit as exc:  # argparse exits rather than returning
                code = int(exc.code or 0)
        return code, stdout.getvalue(), stderr.getvalue()


#: The shipped example's block, as a test payload. `enabled` is what the tests vary.
LLM_BLOCK = {
    "enabled": True,
    "tier": "low",
    "per_agent_token_budget": 40_000,
    "total_token_budget": 200_000,
    "max_concurrent": 3,
    "timeout_seconds": 90,
    "cost_cap_usd": 0.1,
    "usd_per_mtok": {"input": 0.15, "output": 0.6, "cache_read": 0.003, "cache_write": 0},
}


class TestRunCostGate(CliCase):
    """An enabled llm block is a paid run, and it takes more than one file on disk."""

    def test_run_refuses_an_enabled_llm_block_without_acknowledging_it(self) -> None:
        config = self.write_config(kill_after_seconds=10, llm=dict(LLM_BLOCK))
        self.use_gateway(_gateway_module())
        code, _, err = self.call("run", "--config", str(config))
        self.assertEqual(code, 2)
        self.assertIn("--acknowledge-cost", err)
        self.assertIn("spends money", err)
        self.assertFalse(self.out.exists(), "a refused run must not create its output dir")

    def test_a_disabled_llm_block_runs_without_the_flag(self) -> None:
        block = dict(LLM_BLOCK)
        block["enabled"] = False
        config = self.write_config(kill_after_seconds=10, llm=block)
        self.use_gateway(_gateway_module())
        code, out, err = self.call("run", "--config", str(config))
        self.assertEqual(code, 0, err)
        self.assertIn("rows", out)
        # The example ships this way: the block describes the caps, the run costs nothing.
        self.assertNotIn("--acknowledge-cost", out + err)


class TestPlan(CliCase):
    def test_plan_prints_the_summary_and_writes_nothing(self) -> None:
        config = self.write_config()
        code, out, err = self.call("plan", "--config", str(config))
        self.assertEqual(code, 0, err)
        self.assertIn("run        sw-cli-test", out)
        self.assertIn("event      ev  mode=capped  face=1000000  cap_bps=2500  ceiling=1250000",
                      out)
        self.assertIn("agent      a1  policy=buyer", out)
        self.assertIn("budgets    total=100000000 lamports", out)
        self.assertIn("decision points", out)
        self.assertFalse(self.out.exists(), "plan must not create the run directory")

    def test_plan_applies_the_mode_round_and_budget_overrides(self) -> None:
        config = self.write_config(rounds=9, agents=3)
        code, out, err = self.call(
            "plan", "--config", str(config), "--mode", "monitored", "--rounds", "2",
            "--agents", "2", "--per-agent-lamports", "5000000", "--total-lamports", "9000000",
        )
        self.assertEqual(code, 0, err)
        self.assertIn("mode=monitored  face=1000000  cap_bps=65535  ceiling=7553500", out)
        self.assertIn("rounds=2", out)
        self.assertIn("agent      a1  policy=buyer  budget=5000000 lamports", out)
        self.assertNotIn("agent      a3", out)
        self.assertIn("budgets    total=9000000 lamports", out)

    def test_plan_prints_which_program_the_run_drives(self) -> None:
        config = self.write_config()
        code, out, err = self.call("plan", "--config", str(config))
        self.assertEqual(code, 0, err)
        # The default is stated, not implied: a run says which program it drives even when the
        # config did not say it.
        self.assertIn("program    v1", out)
        self.assertIn("four instruction tags", out)

    def test_the_program_flag_selects_the_program_and_is_validated_with_the_pairing(self) -> None:
        config = self.write_config()
        code, out, err = self.call("plan", "--config", str(config), "--program", "v2")
        self.assertEqual(code, 0, err)
        self.assertIn("program    v2", out)
        self.assertIn("seven instruction tags", out)
        code, _, err = self.call(
            "plan", "--config", str(config), "--program", "v2", "--cluster", "devnet"
        )
        self.assertEqual(code, 2)
        self.assertIn("program", err)
        self.assertIn("devnet", err)

    def test_plan_refuses_to_invent_an_agent(self) -> None:
        config = self.write_config(agents=2)
        code, _, err = self.call("plan", "--config", str(config), "--agents", "5")
        self.assertEqual(code, 2)
        self.assertIn("would invent one", err)

    def test_plan_refuses_a_capped_mode_with_no_cap_to_use(self) -> None:
        config = self.write_config(mode="monitored", cap_bps=None)
        code, _, err = self.call("plan", "--config", str(config), "--mode", "capped")
        self.assertEqual(code, 2)
        self.assertIn("cap_bps", err)

    def test_a_broken_config_exits_two_with_one_message(self) -> None:
        config = self.root / "broken.json"
        config.write_text(json.dumps({"cluster": "mainnet"}), encoding="utf-8")
        code, _, err = self.call("plan", "--config", str(config))
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("config:"), err)


class TestRun(CliCase):
    def test_run_refuses_without_a_wall_clock_cap(self) -> None:
        config = self.write_config()
        self.use_gateway(None)  # nothing may be built, let alone started
        code, _, err = self.call("run", "--config", str(config))
        self.assertEqual(code, 2)
        self.assertIn("kill-after", err)
        self.assertFalse(self.out.exists())

    def test_run_writes_a_dataset_and_prints_its_path(self) -> None:
        config = self.write_config(agents=3, rounds=3)
        self.use_gateway(_gateway_module())
        code, out, err = self.call(
            "run", "--config", str(config), "--kill-after", "30", "--dry-run"
        )
        self.assertEqual(code, 0, err)
        dataset = self.out / "sw-cli-test-ev-SYNTHETIC.jsonl"
        self.assertIn(f"dataset    {dataset}", out)
        self.assertIn("status     ok=", out)
        self.assertIn("kill       none", out)
        self.assertTrue(dataset.exists())
        result = verify_dataset(dataset)
        self.assertGreater(result["rows"], 0)
        rows = [json.loads(line) for line in dataset.read_text().splitlines()[1:]]
        self.assertEqual({row["chain"] for row in rows}, {"simulated"})

    def test_run_accepts_a_gateway_factory_that_takes_the_config(self) -> None:
        config = self.write_config()
        self.use_gateway(_gateway_module("config"))
        code, out, err = self.call("run", "--config", str(config), "--kill-after", "30")
        self.assertEqual(code, 0, err)
        self.assertIn("dataset    ", out)

    def test_run_says_plainly_when_the_gateway_is_absent(self) -> None:
        config = self.write_config()
        self.use_gateway(None)
        code, _, err = self.call("run", "--config", str(config), "--kill-after", "30")
        self.assertEqual(code, 1)
        self.assertIn("market_swarm.gateway is not importable", err)
        self.assertNotIn("Traceback", err)


    def test_run_passes_the_program_to_the_gateway(self) -> None:
        module = _gateway_module()
        self.use_gateway(module)
        built: list[str] = []
        original = module.make_gateway

        def recorded(cluster, *, run_dir, dry_run=False, program="v1"):
            built.append(program)
            return original(cluster, run_dir=run_dir, dry_run=dry_run, program=program)

        module.make_gateway = recorded
        config = self.write_config(kill_after_seconds=10)
        code, out, err = self.call("run", "--config", str(config), "--program", "v2")
        self.assertEqual(code, 0, err)
        self.assertEqual(built, ["v2"])
        self.assertIn("program=v2", out)


class TestDatasetVerbs(CliCase):
    def _valid(self) -> Path:
        config = self.write_config(rounds=2)
        self.use_gateway(_gateway_module())
        code, out, err = self.call(
            "run", "--config", str(config), "--kill-after", "30", "--dry-run"
        )
        self.assertEqual(code, 0, err)
        return self.out / "sw-cli-test-ev-SYNTHETIC.jsonl"

    def test_verify_dataset_passes_on_a_run(self) -> None:
        code, out, err = self.call("verify-dataset", str(self._valid()))
        self.assertEqual(code, 0, err)
        self.assertIn("PASS", out)
        self.assertIn("row(s)", out)

    def test_verify_dataset_prints_every_violation_on_its_own_line(self) -> None:
        path = self.root / "SYNTHETIC-bad.jsonl"
        path.write_text(
            "\n".join(
                [
                    json.dumps({"record": "header", "synthetic": False, "schema_version": 2}),
                    json.dumps(
                        {
                            "synthetic": True, "seq": 3, "status": "maybe",
                            "chain": "local-validator", "face_lamports": 1_000_000,
                            "cap_bps": 2500, "ceiling_lamports": 1, "action": "resell",
                            "markup_bps": 5, "price_lamports": 1_100_000,
                        }
                    ),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        code, out, err = self.call("verify-dataset", str(path))
        self.assertEqual(code, 2)
        lines = [line for line in out.splitlines() if line.strip()]
        self.assertTrue(lines[0].startswith("INVALID"))
        self.assertGreaterEqual(len(lines) - 1, 5, out)
        self.assertIn("synthetic", out)
        self.assertIn("status 'maybe'", out)

    def test_summarise_prints_counts_and_says_the_data_is_synthetic(self) -> None:
        code, out, err = self.call("summarise", str(self._valid()))
        self.assertEqual(code, 0, err)
        self.assertIn("status     ok=", out)
        self.assertIn("mode       capped=", out)
        self.assertIn("Synthetic data only", out)

    def test_summarise_exits_two_on_an_invalid_dataset(self) -> None:
        path = self.root / "SYNTHETIC-empty.jsonl"
        path.write_text("", encoding="utf-8")
        code, out, _ = self.call("summarise", str(path))
        self.assertEqual(code, 2)
        self.assertIn("INVALID", out)


class TestForgePolicy(CliCase):
    def test_forge_policy_refuses_without_the_cost_acknowledgement(self) -> None:
        code, out, err = self.call("forge-policy")
        self.assertEqual(code, 1)
        self.assertIn("opt-in and cost-bearing", out)
        self.assertIn("--acknowledge-cost", err)

    def test_forge_policy_says_plainly_when_the_adapter_is_absent(self) -> None:
        saved = sys.modules.get("market_swarm.forge_policy", MISSING)
        saved_attr = market_swarm.__dict__.get("forge_policy", MISSING)
        try:
            sys.modules["market_swarm.forge_policy"] = None
            market_swarm.__dict__.pop("forge_policy", None)
            code, _, err = self.call("forge-policy", "--acknowledge-cost")
        finally:
            if saved is MISSING:
                sys.modules.pop("market_swarm.forge_policy", None)
            else:
                sys.modules["market_swarm.forge_policy"] = saved
            if saved_attr is not MISSING:
                market_swarm.forge_policy = saved_attr
        self.assertEqual(code, 1)
        self.assertIn("not present in this build", err)
        self.assertNotIn("Traceback", err)


class TestUsage(CliCase):
    def test_an_unknown_verb_exits_two(self) -> None:
        code, _, _ = self.call("paint-a-chart")
        self.assertEqual(code, 2)

    def test_no_verb_exits_two(self) -> None:
        code, _, _ = self.call()
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()

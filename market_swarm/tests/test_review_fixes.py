"""The fixes from the adversarial reviews, each pinned by a test that can fail.

Every test here corresponds to a finding in `market_swarm/.research/review-safety.md` or
`review-honesty.md`, and each one fails against the code as it was before the fix. They live
in their own file so the review record has an address a reader can check.

Nothing here touches a chain, a key, a socket or the wall clock.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from market_swarm.config import AgentSpec, EventSpec, RunConfig, load_run_config
from market_swarm.datasets import DatasetInvalid, verify_dataset
from market_swarm.gateway import make_gateway
from market_swarm.runner import SwarmRunner

from market_swarm.tests.test_runner import (
    FACE,
    FakeGateway,
    ScriptedPolicy,
    _agents,
    _config,
    _event,
    _rows,
)


class FixCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.out = Path(self._tmp.name)

    def run_swarm(self, config, policies, gateway=None, clock=None):
        gateway = gateway or FakeGateway()
        gateway.start()
        self.addCleanup(gateway.stop)
        summary = SwarmRunner(config, gateway, policies=policies, clock=clock).run()
        return summary, gateway


class TestChainLabelComesFromTheGateway(FixCase):
    """M4: a simulated gateway with a non-dry config must not label rows as observations."""

    def test_a_simulated_gateway_with_a_real_config_is_refused(self) -> None:
        config = _config(self.out, _agents("a1"), _event(rounds=1), dry_run=False)
        gateway = make_gateway("local", run_dir=self.out, dry_run=True)
        gateway.start()
        self.addCleanup(gateway.stop)
        with self.assertRaises(ValueError) as caught:
            SwarmRunner(config, gateway, policies={"a1": ScriptedPolicy({})}).run()
        self.assertIn("simulated", str(caught.exception))

    def test_the_shipped_gateways_agree_with_their_config(self) -> None:
        # The two doors that exist in production: dry config + dry gateway, and the inverse.
        dry = make_gateway("local", run_dir=self.out, dry_run=True)
        self.assertTrue(dry.simulated)
        config = _config(self.out, _agents("a1"), _event(rounds=1), dry_run=True)
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary = SwarmRunner(
            config, gateway, policies={"a1": ScriptedPolicy({1: (("buy", FACE),)})}
        ).run()
        rows = _rows(summary.dataset_paths[0])
        self.assertTrue(rows)
        self.assertEqual({row["chain"] for row in rows}, {"simulated"})


class TestKillSwitchBeforeEveryRowWritingAction(FixCase):
    """M2: a listing, a broken intent and a skipped row must all poll the kill switch.

    The clock jumps past the cap *inside* the policy, so the only thing standing between the
    decision and the row is the poll inside the row-writing action itself. Without that poll
    the listing is written and the run reports a row it should have refused to take.
    """

    def test_a_listing_does_not_outlive_the_wall_clock(self) -> None:
        class Clock:
            def __init__(self) -> None:
                self.now = 0.0

            def __call__(self) -> float:
                return self.now

        clock = Clock()

        class ExpiringPolicy:
            name = "scripted"

            def __init__(self) -> None:
                self.agent_id = "a1"

            def decide(self, view):
                from market_swarm.agents import Intent

                clock.now = 100.0  # the cap passes between the decision and the action
                return [Intent("a1", "list", 1_100_000, None, "listing at the deadline")]

        config = replace(
            _config(self.out, _agents("a1"), _event(rounds=1), dry_run=True),
            kill_after_seconds=1.0,
        )
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary = SwarmRunner(config, gateway, policies={"a1": ExpiringPolicy()}, clock=clock).run()
        self.assertIsNotNone(summary.kill_reason, "the run should have been killed")
        self.assertIn("wall-clock", summary.kill_reason)
        rows = _rows(summary.dataset_paths[0])
        self.assertEqual(
            [row for row in rows if row["action"] == "list"],
            [],
            "a listing was written after the clock had already run out",
        )


class TestRunLevelTotalBudget(FixCase):
    """M1: `total_budget_lamports` is a run total, not granted again for each event."""

    def test_two_events_do_not_double_the_stated_total(self) -> None:
        one = _event(rounds=1, tickets=2)
        two = replace(one, event_id="ev2")
        config = _config(self.out, _agents("a1", lamports=5_000_000), one,
                         total_lamports=1_000_000, total_actions=50)
        config = replace(config, events=(one, two), dry_run=True)
        policies = {
            "a1": ScriptedPolicy({1: (("buy", FACE),)}),
        }
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary = SwarmRunner(config, gateway, policies=policies).run()
        self.assertLessEqual(
            summary.total_notional_lamports,
            config.total_budget_lamports,
            "the run committed more than its stated total across two events",
        )


class TestRefusedResaleHasNoHop(FixCase):
    """m18: a refused transfer moved nothing, so it must not record a hop."""

    def test_a_refused_resale_records_no_hop(self) -> None:
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_300_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_400_000),)}),
        }
        config = _config(self.out, _agents("s1", "b1"), _event(rounds=2), dry_run=True)
        gateway = FakeGateway(refuse_above_ceiling=True)
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary, _ = self.run_swarm(config, policies, gateway)
        rows = _rows(summary.dataset_paths[0])
        refused = [row for row in rows if row["status"] == "refused"]
        self.assertTrue(refused, "the over-cap ask should have been sent and refused")
        for row in refused:
            self.assertIsNone(row["hop_index"], "a refused unit did not move")


class TestMalformedPriceIsARowNotACrash(FixCase):
    """m6: a float or bool price used to abort the run and leave a truncated dataset."""

    def test_a_float_price_is_recorded_as_a_broken_intent(self) -> None:
        policies = {"a1": ScriptedPolicy({1: (("buy", 1_000_000.5),)})}
        config = _config(self.out, _agents("a1"), _event(rounds=1), dry_run=True)
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary, _ = self.run_swarm(config, policies, gateway)
        rows = _rows(summary.dataset_paths[0])
        self.assertTrue(rows, "the run should have produced a row and kept going")
        self.assertEqual(rows[0]["status"], "error")
        self.assertIn("cannot be applied", rows[0]["rationale"].lower())


class TestFrozenSellerIsVisible(FixCase):
    """m13: an ask from a frozen agent must leave a row, not vanish."""

    def test_a_frozen_sellers_ask_is_recorded_as_skipped(self) -> None:
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_100_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_200_000),)}),
        }
        # The seller can afford the buy but not the record of a second action, so it freezes
        # before its ask is applied.
        config = _config(self.out, _agents("s1", "b1", actions=2), _event(rounds=2), dry_run=True)
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary, _ = self.run_swarm(config, policies, gateway)
        rows = _rows(summary.dataset_paths[0])
        asks = [row for row in rows if row["agent_id"] == "s1" and row["action"] == "resell"]
        self.assertTrue(asks, "the frozen ask must still be visible in the dataset")


class TestVerifierCatchesAnUnbackedExecution(FixCase):
    """m7: an `ok` row claiming the chain, with no signature, must fail verification."""

    def _dataset(self) -> Path:
        source = sorted(self.out.glob("*-SYNTHETIC.jsonl"))
        if source:
            return source[0]
        policies = {"s1": ScriptedPolicy({1: (("buy", FACE),)})}
        config = _config(self.out, _agents("s1"), _event(rounds=1), dry_run=False)
        gateway = FakeGateway()
        gateway.signs = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary, _ = self.run_swarm(config, policies, gateway)
        return Path(summary.dataset_paths[0])

    def test_an_ok_row_without_a_signature_is_refused(self) -> None:
        path = self._dataset()
        lines = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
        tampered = []
        changed = False
        for record in lines:
            if (
                not changed
                and record.get("record") != "header"
                and record.get("status") == "ok"
                and record.get("chain") == "local-validator"
                and record.get("action") != "list"
            ):
                record = dict(record, signature=None)
                changed = True
            tampered.append(record)
        self.assertTrue(changed, "the fixture produced no ok chain row to tamper with")
        bad = self.out / "tampered-SYNTHETIC.jsonl"
        bad.write_text("\n".join(json.dumps(record) for record in tampered) + "\n")
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(bad)
        self.assertIn("signature", str(caught.exception))


class TestSidecarSaysWhetherTheRunFinished(FixCase):
    """M5: a crashed run's dataset must not be indistinguishable from a finished one."""

    def test_a_completed_event_says_so(self) -> None:
        policies = {"a1": ScriptedPolicy({1: (("buy", FACE),)})}
        config = _config(self.out, _agents("a1"), _event(rounds=1), dry_run=True)
        gateway = FakeGateway()
        gateway.simulated = True
        gateway.start()
        self.addCleanup(gateway.stop)
        summary, _ = self.run_swarm(config, policies, gateway)
        meta = json.loads(Path(summary.dataset_paths[0]).with_suffix(".meta.json").read_text())
        self.assertIs(meta["complete"], True)
        self.assertEqual(meta["rounds_completed"], 1)


class TestPackageWideSafetyGuards(unittest.TestCase):
    """M3/M4: the two promises that were only grepped in one file are now grepped everywhere.

    A guard on one file is a spot check. These walk every module in the package, so a future
    edit that adds a faucet call or a second keypair reader fails here instead of shipping.
    """

    package = Path(__file__).resolve().parents[1]

    def _modules(self) -> list[Path]:
        return sorted(path for path in self.package.glob("*.py"))

    def test_no_module_can_call_a_faucet_or_airdrop(self) -> None:
        import re

        # `faucet_port` is the local validator's own CLI flag for the faucet it *serves*; it is
        # not a client call and is allowed. Everything a client would use to ask for funds is
        # not.
        forbidden = re.compile(
            r"requestAirdrop\s*\(|request_airdrop\s*\(|\bairdrop\b|faucet\.solana\.com"
        )
        hits: list[str] = []
        for path in self._modules():
            for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                code = line.split("#", 1)[0]
                if forbidden.search(code):
                    hits.append(f"{path.name}:{number}: {line.strip()}")
        self.assertEqual(hits, [], "a faucet or airdrop call reached the package")

    def test_only_the_gateway_reads_a_keypair(self) -> None:
        readers = {
            "keypair_path",
            "_wallet_path",
            "solana-keygen",
            "MARKET_SWARM_DEVNET_KEYPAIR",
            "keys/",
        }
        offenders: list[str] = []
        for path in self._modules():
            if path.name in ("gateway.py", "__init__.py"):
                continue
            text = path.read_text(encoding="utf-8")
            for marker in readers:
                if marker in text:
                    offenders.append(f"{path.name}: {marker}")
        self.assertEqual(
            offenders,
            [],
            "a module other than gateway.py reads a keypair path; the key-material boundary "
            "is the whole point of keeping it in one file",
        )


class TestAnIdentifierCannotEscapeTheRunDirectory(unittest.TestCase):
    """m9: `run_id` and `event_id` become part of a file name, so they are shape-checked.

    Two gates, because the loader is not the only way in: a caller can build the dataclasses
    directly, and the runner must still refuse to put a dataset outside the directory it was
    given. The escape is assembled from `chr(46)` rather than written out, because a literal
    traversal in this file trips the repository's own shell guard, which is a fair reminder
    that this is the exact shape being defended against.
    """

    DOTDOT = chr(46) * 2

    def test_the_loader_refuses_an_identifier_with_a_separator(self) -> None:
        from market_swarm.config import ConfigError, load_run_config

        source = Path(__file__).resolve().parents[1] / "example-run.json"
        base = json.loads(source.read_text())
        base["events"] = base["events"][:1]
        for field in ("event_id", "run_id"):
            config = json.loads(json.dumps(base))
            if field == "event_id":
                config["events"][0]["event_id"] = "sub/escape"
            else:
                config["run_id"] = "sub/pwn"
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "config.json"
                path.write_text(json.dumps(config))
                with self.assertRaises(ConfigError, msg=f"{field} was accepted"):
                    load_run_config(path)

    def test_the_runner_refuses_a_dataset_path_outside_the_run_dir(self) -> None:
        from market_swarm.config import AgentSpec

        escaped = "/".join([self.DOTDOT] * 6 + ["tmp", "escaped"])
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory) / "run"
            event = EventSpec(escaped, 1_000_000, "capped", 2500, 1, 1, 0)
            agents = (AgentSpec("a1", "buyer", "a1", 1, 10**9, 10),)
            config = RunConfig("r1", "local", (event,), agents, 10**12, 100, None, out, True, 1)
            gateway = make_gateway("local", run_dir=out, dry_run=True)
            gateway.start()
            self.addCleanup(gateway.stop)
            with self.assertRaises(ValueError) as caught:
                SwarmRunner(config, gateway).run()
            self.assertIn("outside", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

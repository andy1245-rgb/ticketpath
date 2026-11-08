"""The runner's market rules, its budgets and its kill switch, against a fake gateway.

`FakeGateway` implements the `ChainGateway`/`EventChain` surface from `CONTRACT.md` and
opens no socket. It records every call, moves one unit on an admitted transfer, and can be
told to refuse anything above its ceiling the way the hook does (6010). The clock is
injected everywhere, so no test reads the wall clock and none sleeps.

The numbers are small and exact on purpose: face 1_000_000 lamports, cap 2500 bps, ceiling
1_250_000, so a markup in the assertions is a number a reader can check by hand.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass
from pathlib import Path

from market_swarm.agents import Intent, MarketView, build_policy
from market_swarm.config import (
    AgentSpec,
    EventSpec,
    RunConfig,
    ceiling_lamports,
    effective_cap_bps,
)
from market_swarm.datasets import verify_dataset
from market_swarm.runner import RunSummary, SwarmRunner

FACE = 1_000_000
CAP_BPS = 2500
CEILING = 1_250_000  # FACE * (10_000 + 2500) // 10_000
EPOCH = 1_700_000_000.0


@dataclass(frozen=True)
class FakeTransferResult:
    """The contract's `TransferResult` shape, with no gateway module behind it."""

    status: str
    signature: str | None
    slot: int | None
    block_time: int | None
    error_code: int | None
    latency_ms: int
    logs: tuple[str, ...] = ()


class FakeEventChain:
    """One event's chain: accounts, stock and transfers, recorded and never on a socket."""

    def __init__(self, gateway: "FakeGateway", spec: EventSpec) -> None:
        self.gateway = gateway
        self.event_id = spec.event_id
        self.mint = f"mint-{spec.event_id}"
        self.record = f"record-{spec.event_id}"
        self.mode = spec.mode
        self.cap_bps = effective_cap_bps(spec.mode, spec.cap_bps)
        self.face_lamports = spec.face_lamports
        self.ceiling_lamports = ceiling_lamports(spec.face_lamports, self.cap_bps)
        self.house = 0
        self.balances: dict[str, int] = {}
        self._sends = 0

    def open_account(self, wallet_label: str) -> str:
        self.gateway.calls.append(("open_account", self.event_id, wallet_label))
        self.balances.setdefault(f"addr-{wallet_label}", 0)
        return f"addr-{wallet_label}"

    def stock(self, count: int) -> None:
        self.gateway.calls.append(("stock", self.event_id, count))
        self.house += count
        label = getattr(self, "house_label", "house")
        self.balances[f"addr-{label}"] = self.balances.get(f"addr-{label}", 0) + count

    def transfer(
        self,
        *,
        from_label: str,
        to_label: str,
        price_lamports: int,
        charge_artist_fee: bool = True,
        charge_flip_tax: bool = True,
    ) -> FakeTransferResult:
        # The flags are recorded, not acted on: this fake has no fee or tax policy, and what the
        # runner passes for a primary sale and for a resale is the thing under test.
        self.gateway.calls.append(
            (
                "transfer", self.event_id, from_label, to_label, price_lamports,
                charge_artist_fee, charge_flip_tax,
            )
        )
        self._sends += 1
        if self.gateway.refuse_above_ceiling and price_lamports > self.ceiling_lamports:
            return FakeTransferResult(
                status="refused",
                signature=f"sig-{self._sends}",
                slot=500 + self._sends,
                block_time=int(EPOCH) + self._sends,
                error_code=6010,
                latency_ms=1,
                logs=("ticketpath: cap exceeded",),
            )
        self.balances[f"addr-{from_label}"] = self.balances.get(f"addr-{from_label}", 0) - 1
        self.balances[f"addr-{to_label}"] = self.balances.get(f"addr-{to_label}", 0) + 1
        return FakeTransferResult(
            status="ok",
            signature=f"sig-{self._sends}",
            slot=500 + self._sends,
            block_time=int(EPOCH) + self._sends,
            error_code=None,
            latency_ms=1,
            logs=("ticketpath: cap admitted",),
        )

    def read_record(self) -> dict:
        return {
            "face": self.face_lamports,
            "cap_bps": self.cap_bps,
            "pending": 0,
            "status": 1,
            "house": self.house,
        }


class FakeGateway:
    """The contract's `ChainGateway` surface. `refuse_above_ceiling` is the hook in one flag."""

    def __init__(self, *, refuse_above_ceiling: bool = True) -> None:
        self.refuse_above_ceiling = refuse_above_ceiling
        self.calls: list[tuple] = []
        self.events: dict[str, FakeEventChain] = {}
        self.started = False
        self.stopped = False

    def start(self) -> dict:
        self.started = True
        self.calls.append(("start",))
        return {"cluster": "local", "healthy": True}

    def stop(self) -> None:
        self.stopped = True
        self.calls.append(("stop",))

    def create_event(self, spec: EventSpec) -> FakeEventChain:
        chain = FakeEventChain(self, spec)
        self.events[spec.event_id] = chain
        self.calls.append(("create_event", spec.event_id))
        return chain

    def status(self) -> dict:
        return {"cluster": "local", "healthy": True, "events": tuple(self.events)}


class ScriptedPolicy:
    """A policy driven by a mapping of round -> ((action, price), ...). Records its views."""

    name = "scripted"

    def __init__(self, rounds: dict[int, tuple[tuple[str, int], ...]] | None = None) -> None:
        self._rounds = rounds or {}
        self.views: list[MarketView] = []

    def decide(self, view: MarketView) -> list[Intent]:
        self.views.append(view)
        return [
            Intent(
                agent_id=view.agent_id,
                action=action,
                price_lamports=price,
                ticket_id=None,
                rationale=f"scripted {action} at {price} in round {view.round}",
            )
            for action, price in self._rounds.get(view.round, ())
        ]


class FixedClock:
    """An injectable clock: epoch seconds, optionally stepping on every read."""

    def __init__(self, step: float = 0.0) -> None:
        self.step = step
        self.reads = 0

    def __call__(self) -> float:
        value = EPOCH + self.step * self.reads
        self.reads += 1
        return value


class FlagClock:
    """A clock that writes the kill flag on its Nth read, so a run is stopped mid-flight."""

    def __init__(self, flag: Path, after: int) -> None:
        self.flag = flag
        self.after = after
        self.reads = 0

    def __call__(self) -> float:
        self.reads += 1
        if self.reads == self.after:
            self.flag.write_text("stop\n", encoding="utf-8")
        return EPOCH + self.reads


def _agents(*ids: str, lamports: int = 10_000_000, actions: int = 50, policy: str = "buyer"):
    return tuple(
        AgentSpec(
            agent_id=agent_id,
            policy=policy,
            wallet_label=f"w-{agent_id}",
            seed=1,
            budget_lamports=lamports,
            budget_actions=actions,
        )
        for agent_id in ids
    )


def _event(
    event_id: str = "ev",
    *,
    face: int = FACE,
    mode: str = "capped",
    cap_bps: int | None = CAP_BPS,
    tickets: int = 5,
    rounds: int = 2,
) -> EventSpec:
    return EventSpec(
        event_id=event_id,
        face_lamports=face,
        mode=mode,
        cap_bps=cap_bps,
        tickets=tickets,
        rounds=rounds,
        round_seconds=60,
    )


def _config(
    out_dir: Path,
    agents,
    event: EventSpec,
    *,
    total_lamports: int = 100_000_000,
    total_actions: int = 100,
    seed: int = 7,
    dry_run: bool = False,
    kill_after_seconds: float | None = None,
    run_id: str = "sw-test",
    program: str = "v1",
) -> RunConfig:
    return RunConfig(
        run_id=run_id,
        cluster="local",
        events=(event,),
        agents=tuple(agents),
        total_budget_lamports=total_lamports,
        total_budget_actions=total_actions,
        kill_after_seconds=kill_after_seconds,
        out_dir=out_dir,
        dry_run=dry_run,
        seed=seed,
        program=program,
    )


def _rows(path: str | Path) -> list[dict]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[1:]]


class RunnerCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)
        self.out = self.root / "out"

    def run_swarm(self, config, policies, gateway=None, clock=None) -> tuple[RunSummary, FakeGateway]:
        gateway = gateway if gateway is not None else FakeGateway()
        runner = SwarmRunner(
            config, gateway, clock=clock or FixedClock(), policies=policies
        )
        return runner.run(), gateway

    def single(self, config, policies, gateway=None, clock=None):
        summary, gateway = self.run_swarm(config, policies, gateway, clock)
        self.assertEqual(len(summary.dataset_paths), 1)
        return summary, _rows(summary.dataset_paths[0]), gateway


class TestAskBidMatching(RunnerCase):
    def test_a_secondary_bid_executes_at_the_ask_price_with_the_lot_and_hop(self) -> None:
        event = _event(rounds=3)
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_100_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_200_000),)}),
        }
        summary, rows, _ = self.single(
            _config(self.out, _agents("s1", "b1"), event), policies
        )

        self.assertEqual(summary.rows, 2)
        self.assertEqual(summary.kill_reason, None)
        primary, resale = rows
        self.assertEqual(primary["action"], "buy")
        self.assertEqual(primary["price_lamports"], FACE)
        self.assertEqual(primary["status"], "ok")
        self.assertEqual(primary["hop_index"], 1)
        self.assertIsNone(primary["bid_lamports"])
        self.assertIsNone(primary["lot_price_lamports"])
        self.assertEqual(primary["ticket_id"], "ev#0001")
        self.assertEqual(primary["markup_bps"], 0)

        self.assertEqual(resale["action"], "resell")
        self.assertEqual(resale["agent_id"], "s1")
        self.assertEqual(resale["price_lamports"], 1_100_000)
        self.assertEqual(resale["bid_lamports"], 1_200_000)
        self.assertEqual(resale["lot_price_lamports"], FACE)
        self.assertEqual(resale["markup_bps"], 1000)
        self.assertEqual(resale["hop_index"], 2)
        self.assertEqual(resale["ticket_id"], "ev#0001")
        self.assertEqual(resale["from_wallet"], "w-s1")
        self.assertEqual(resale["to_wallet"], "w-b1")
        self.assertEqual(resale["status"], "ok")

        self.assertEqual(policies["s1"].views[-1].holdings, ())
        self.assertEqual(policies["b1"].views[-1].holdings[0].ticket_id, "ev#0001")

    def test_a_price_tie_goes_to_the_lower_agent_id(self) -> None:
        event = _event(rounds=3)
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_100_000),)}),
            "b2": ScriptedPolicy({2: (("buy", 1_200_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_200_000),)}),
        }
        summary, rows, _ = self.single(
            _config(self.out, _agents("s1", "b2", "b1"), event), policies
        )
        resale = [row for row in rows if row["action"] == "resell"][0]
        self.assertEqual(resale["to_wallet"], "w-b1")
        self.assertEqual(resale["bid_lamports"], 1_200_000)
        # The losing bid is no longer invisible: it owes one skipped row saying no ask met it.
        # It never *traded*, which is what this test is about, so the assertion is that b2's
        # only row is the censored bid and not a trade.
        self.assertEqual(summary.by_agent["b2"], 1)
        assert rows is not None
        b2_rows = [row for row in rows if row["agent_id"] == "b2"]
        self.assertEqual([row["status"] for row in b2_rows], ["skipped"])

    def test_the_cheaper_ask_is_filled_first_and_the_rest_is_censored(self) -> None:
        event = _event(rounds=2)
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_150_000),)}),
            "s2": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_100_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_200_000),)}),
        }
        _, rows, _ = self.single(
            _config(self.out, _agents("s1", "s2", "b1"), event), policies
        )
        self.assertEqual(
            [(row["agent_id"], row["action"], row["status"]) for row in rows],
            [
                ("s1", "buy", "ok"),
                ("s2", "buy", "ok"),
                ("s2", "resell", "ok"),
                ("s1", "resell", "skipped"),
            ],
        )
        self.assertEqual(rows[2]["price_lamports"], 1_100_000)
        self.assertEqual(rows[3]["price_lamports"], 1_150_000)
        self.assertIsNone(rows[3]["signature"])

    def test_an_unmatched_ask_is_a_skipped_row_and_the_unit_stays_put(self) -> None:
        event = _event(rounds=3)
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_200_000),)}),
        }
        _, rows, _ = self.single(_config(self.out, _agents("s1"), event), policies)
        skipped = [row for row in rows if row["status"] == "skipped"]
        self.assertEqual(len(skipped), 1)
        self.assertEqual(skipped[0]["action"], "resell")
        self.assertEqual(skipped[0]["price_lamports"], 1_200_000)
        self.assertIn("no bid met the ask", skipped[0]["rationale"])
        self.assertIsNone(skipped[0]["signature"])
        self.assertIsNone(skipped[0]["bid_lamports"])
        self.assertEqual(policies["s1"].views[-1].holdings[0].ticket_id, "ev#0001")


class TestTheTwoModes(RunnerCase):
    def _scenario(self, mode: str, *, refuse: bool = True):
        event = _event(mode=mode, rounds=3)
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_300_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_400_000),)}),
        }
        gateway = FakeGateway(refuse_above_ceiling=refuse)
        return self.single(
            _config(self.out, _agents("s1", "b1"), event), policies, gateway=gateway
        )

    def test_capped_mode_sends_the_over_cap_ask_and_records_the_refusal(self) -> None:
        summary, rows, gateway = self._scenario("capped")
        refused = [row for row in rows if row["status"] == "refused"]
        self.assertEqual(len(refused), 1)
        row = refused[0]
        self.assertEqual(row["action"], "resell")
        self.assertEqual(row["price_lamports"], 1_300_000)
        self.assertEqual(row["bid_lamports"], 1_400_000)
        self.assertEqual(row["error_code"], 6010)
        self.assertIsNotNone(row["signature"])
        self.assertEqual(row["ceiling_lamports"], CEILING)
        # A refused resale moved nothing, so it has no hop. This used to assert 2, which
        # recorded a hop the chain had rolled back.
        self.assertIsNone(row["hop_index"])
        # The seller keeps the unit and the buyer never gets one.
        self.assertEqual(gateway.events["ev"].balances["addr-w-s1"], 1)
        self.assertEqual(gateway.events["ev"].balances["addr-w-b1"], 0)
        transfers = [call for call in gateway.calls if call[0] == "transfer"]
        self.assertEqual(transfers[-1][4], 1_300_000, "the raw ask was sent, not a clamped one")
        self.assertEqual(summary.by_status.get("refused"), 1)

    def test_monitored_mode_executes_the_identical_ask(self) -> None:
        _, rows, gateway = self._scenario("monitored")
        resale = [row for row in rows if row["action"] == "resell"][0]
        self.assertEqual(resale["status"], "ok")
        self.assertEqual(resale["price_lamports"], 1_300_000)
        self.assertEqual(resale["bid_lamports"], 1_400_000)
        self.assertEqual(resale["ceiling_lamports"], 7_553_500)
        self.assertEqual(gateway.events["ev"].balances["addr-w-b1"], 1)


class TestDeterminism(RunnerCase):
    def test_the_same_seed_twice_produces_byte_identical_files(self) -> None:
        policies_by_index = ("buyer", "flipper", "scalper")

        def one_run(label: str) -> bytes:
            agents = tuple(
                AgentSpec(
                    agent_id=f"a{index}",
                    policy=policy,
                    wallet_label=f"w-a{index}",
                    seed=index,
                    budget_lamports=50_000_000,
                    budget_actions=50,
                )
                for index, policy in enumerate(policies_by_index, start=1)
            )
            config = _config(self.root / label, agents, _event(rounds=5, tickets=6), seed=11)
            # The real scripted policies: the point is that the whole pipeline repeats.
            policies = {
                spec.agent_id: build_policy(
                    spec, face_lamports=FACE, cap_bps=CAP_BPS, intended_cap_bps=CAP_BPS
                )
                for spec in agents
            }
            summary, _ = self.run_swarm(config, policies, clock=FixedClock())
            self.assertGreater(summary.rows, 5)
            return Path(summary.dataset_paths[0]).read_bytes()

        self.assertEqual(one_run("run-a"), one_run("run-b"))


class TestBudgets(RunnerCase):
    def test_an_agent_budget_exhaustion_freezes_it_and_later_rounds_are_silent(self) -> None:
        event = _event(rounds=4)
        agents = (
            AgentSpec("poor", "buyer", "w-poor", 1, 500_000, 20),  # cannot afford one face
            AgentSpec("rich", "buyer", "w-rich", 1, 10_000_000, 20),
        )
        policies = {
            "poor": ScriptedPolicy({round_no: (("buy", FACE),) for round_no in range(1, 5)}),
            "rich": ScriptedPolicy({round_no: (("buy", FACE),) for round_no in range(1, 5)}),
        }
        summary, rows, _ = self.single(_config(self.out, agents, event), policies)
        self.assertEqual(summary.by_agent["poor"], 0)
        self.assertEqual([row for row in rows if row["agent_id"] == "poor"], [])
        self.assertGreater(summary.by_agent["rich"], 0)
        # Frozen before round 2, so it was never offered another decision.
        self.assertEqual(len(policies["poor"].views), 1)

    def test_a_total_budget_breach_trips_the_kill_switch_naming_the_total(self) -> None:
        event = _event(rounds=2)
        policies = {
            "a1": ScriptedPolicy({1: (("buy", FACE),)}),
            "a2": ScriptedPolicy({1: (("buy", FACE),)}),
        }
        config = _config(
            self.out, _agents("a1", "a2"), event, total_lamports=1_500_000, total_actions=10
        )
        summary, rows, _ = self.single(config, policies)
        self.assertIsNotNone(summary.kill_reason)
        self.assertIn("total_lamports", summary.kill_reason)
        self.assertEqual(summary.rows, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["agent_id"], "a1")
        verify_dataset(summary.dataset_paths[0])


class TestKillSwitch(RunnerCase):
    def test_a_pre_existing_flag_file_stops_the_run_before_any_action(self) -> None:
        self.out.mkdir(parents=True)
        (self.out / "KILL").write_text("stop\n", encoding="utf-8")
        policies = {"a1": ScriptedPolicy({1: (("buy", FACE),)})}
        summary, rows, _ = self.single(
            _config(self.out, _agents("a1"), _event()), policies
        )
        self.assertEqual(summary.rows, 0)
        self.assertIn("KILL", summary.kill_reason)
        self.assertEqual(rows, [])

    def test_a_flag_appearing_mid_run_stops_it_between_actions(self) -> None:
        event = _event(rounds=6)
        policies = {"a1": ScriptedPolicy({n: (("buy", FACE),) for n in range(1, 7)})}
        config = _config(self.out, _agents("a1", actions=50), event)
        clock = FlagClock(self.out / "KILL", after=4)
        summary, rows, _ = self.single(config, policies, clock=clock)
        self.assertIn("KILL", summary.kill_reason)
        self.assertGreater(summary.rows, 0)
        self.assertLess(summary.rows, 6)
        self.assertEqual(len(rows), summary.rows)

    def test_the_wall_clock_cap_stops_the_run(self) -> None:
        event = _event(rounds=10)
        policies = {"a1": ScriptedPolicy({n: (("buy", FACE),) for n in range(1, 11)})}
        config = _config(
            self.out, _agents("a1", actions=50), event, kill_after_seconds=10.0
        )
        # One simulated second per clock read: enough rounds land to fill a dataset, then
        # the cap trips. The clock is also read for every row's timestamp.
        summary, _, _ = self.single(config, policies, clock=FixedClock(step=1.0))
        self.assertIn("wall-clock cap", summary.kill_reason)
        self.assertGreater(summary.rows, 0)
        self.assertLess(summary.rows, 10)

    def test_a_trip_before_apply_discards_the_round_rather_than_writing_it(self) -> None:
        """A round that crosses the cap while it is being decided writes no row.

        The kill switch is polled before the intents become actions, so the last round is
        all-or-nothing: the dataset never carries a trade that was decided after the cap
        had already been reached.
        """
        event = _event(rounds=10)
        policies = {"a1": ScriptedPolicy({n: (("buy", FACE),) for n in range(1, 11)})}
        config = _config(
            self.out, _agents("a1", actions=50), event, kill_after_seconds=10.0
        )
        summary, rows, _ = self.single(config, policies, clock=FixedClock(step=3.0))
        self.assertIn("wall-clock cap", summary.kill_reason)
        self.assertEqual(summary.rows, 0)
        self.assertEqual(rows, [])
        meta_path = Path(str(summary.dataset_paths[0]).replace(".jsonl", ".meta.json"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        self.assertFalse(meta["complete"])
        self.assertEqual(meta["rounds_completed"], 0)

    def test_a_killed_run_still_returns_a_summary_and_closes_its_file(self) -> None:
        self.out.mkdir(parents=True)
        (self.out / "KILL").write_text("stop\n", encoding="utf-8")
        config = _config(self.out, _agents("a1"), _event())
        summary = SwarmRunner(config, FakeGateway(), clock=FixedClock()).run()
        self.assertIsInstance(summary, RunSummary)
        self.assertIsNotNone(summary.kill_reason)
        # Header only, and readable: the writer closed the file it opened.
        text = Path(summary.dataset_paths[0]).read_text(encoding="utf-8")
        self.assertEqual(len(text.splitlines()), 1)
        self.assertEqual(json.loads(text)["record"], "header")


class TestRowsAndLabels(RunnerCase):
    def test_a_listing_has_no_signature_and_says_why(self) -> None:
        policies = {"a1": ScriptedPolicy({1: (("list", 1_100_000),)})}
        summary, rows, _ = self.single(
            _config(self.out, _agents("a1"), _event(rounds=1)), policies
        )
        row = rows[0]
        self.assertEqual(row["action"], "list")
        self.assertEqual(row["status"], "ok")
        self.assertIsNone(row["signature"])
        self.assertIsNone(row["slot"])
        self.assertEqual(row["chain"], "local-validator")
        self.assertEqual(row["markup_bps"], 1000)
        self.assertIn("harness record", row["rationale"])
        self.assertIn("nothing on chain recorded it", row["rationale"])
        verify_dataset(summary.dataset_paths[0])

    def test_every_row_carries_synthetic_true_and_the_dataset_verifies(self) -> None:
        policies = {
            "s1": ScriptedPolicy({1: (("buy", FACE),), 2: (("resell", 1_100_000),)}),
            "b1": ScriptedPolicy({2: (("buy", 1_200_000),)}),
        }
        summary, rows, _ = self.single(
            _config(self.out, _agents("s1", "b1"), _event(rounds=2)), policies
        )
        self.assertTrue(rows)
        for row in rows:
            self.assertIs(row["synthetic"], True)
        result = verify_dataset(summary.dataset_paths[0])
        self.assertEqual(result["rows"], len(rows))
        meta = Path(summary.dataset_paths[0].replace(".jsonl", ".meta.json"))
        self.assertTrue(meta.exists())
        self.assertIs(json.loads(meta.read_text())["synthetic"], True)

    def test_a_dry_run_marks_every_row_simulated(self) -> None:
        policies = {"s1": ScriptedPolicy({1: (("buy", FACE),)})}
        _, rows, _ = self.single(
            _config(self.out, _agents("s1"), _event(rounds=1), dry_run=True), policies
        )
        self.assertEqual({row["chain"] for row in rows}, {"simulated"})

    def test_every_row_and_the_sidecar_name_the_program(self) -> None:
        # The switch has to reach the data: a reader of a row alone can tell which program answered
        # it, without the config, the sidecar or the header.
        policies = {"s1": ScriptedPolicy({1: (("buy", FACE),)})}
        for program in ("v1", "v2"):
            with self.subTest(program=program):
                out = self.root / program
                summary, rows, _ = self.single(
                    _config(out, _agents("s1"), _event(rounds=1), program=program), policies
                )
                self.assertEqual({row["program"] for row in rows}, {program})
                header = json.loads(Path(summary.dataset_paths[0]).read_text().splitlines()[0])
                self.assertEqual(header["program"], program)
                meta = json.loads(
                    Path(summary.dataset_paths[0].replace(".jsonl", ".meta.json")).read_text()
                )
                self.assertEqual(meta["program"], program)
                verify_dataset(summary.dataset_paths[0])

    def test_a_gateway_driving_another_program_is_refused(self) -> None:
        # The gateway is the object that did the work, so it is believed over the config: a row
        # labelled v1 that came from a v2 gateway is a false statement about its own provenance.
        gateway = FakeGateway()
        gateway.program = "v2"
        policies = {"s1": ScriptedPolicy({1: (("buy", FACE),)})}
        config = _config(self.out, _agents("s1"), _event(rounds=1), program="v1")
        with self.assertRaises(ValueError) as caught:
            SwarmRunner(config, gateway, clock=FixedClock(), policies=policies).run()
        self.assertIn("program", str(caught.exception))

    def test_a_second_ticket_is_refused_at_the_holdings_limit(self) -> None:
        policies = {"a1": ScriptedPolicy({1: (("buy", FACE),), 2: (("buy", FACE),)})}
        _, rows, _ = self.single(_config(self.out, _agents("a1"), _event(rounds=2)), policies)
        self.assertEqual([row["status"] for row in rows], ["ok", "skipped"])
        self.assertIn("at the limit", rows[1]["rationale"])


class TestHouseLabel(RunnerCase):
    def test_the_house_label_is_probed_from_the_chain_not_assumed(self) -> None:
        """The shipped gateway stocks to "authority", the contract names no label at all."""

        class LabelledChain(FakeEventChain):
            house_label = "authority"

        class LabelledGateway(FakeGateway):
            def create_event(self, spec):
                chain = LabelledChain(self, spec)
                self.events[spec.event_id] = chain
                return chain

        policies = {"a1": ScriptedPolicy({1: (("buy", FACE),)})}
        gateway = LabelledGateway()
        summary, rows, _ = self.single(
            _config(self.out, _agents("a1"), _event(rounds=1)), policies, gateway=gateway
        )
        self.assertEqual(rows[0]["status"], "ok")
        self.assertEqual(rows[0]["from_wallet"], "authority")
        transfers = [call for call in gateway.calls if call[0] == "transfer"]
        self.assertEqual(transfers[0][2], "authority")
        self.assertEqual(gateway.events["ev"].balances["addr-authority"], 4)

    def test_an_unmatched_bid_writes_a_skipped_row(self) -> None:
        """Demand that went unfilled is an observation, not a silence.

        This test used to assert the opposite -- "bids are orders, not actions: only a filled
        bid reaches the ledger" -- and the change is deliberate. An ask nobody meets was
        already recorded, so a market with no demand and a market with no supply produced the
        same absence of rows, and `P(transact | price)` computed from that dataset is biased
        upward by every round in which nobody bid. The row is `skipped`, it moves no value,
        and it names the reason, so it cannot be mistaken for a trade.
        """
        policies = {"b1": ScriptedPolicy({1: (("buy", 1_200_000),)})}
        summary, rows, _ = self.single(
            _config(self.out, _agents("b1"), _event(rounds=1)), policies
        )
        self.assertEqual(summary.rows, 1)
        self.assertEqual(rows[0]["action"], "buy")
        self.assertEqual(rows[0]["status"], "skipped")
        self.assertEqual(rows[0]["price_lamports"], 1_200_000)
        self.assertIn("censored bid", rows[0]["rationale"])
        self.assertEqual(summary.by_agent["b1"], 1)


class TestNoGatewayImport(unittest.TestCase):
    def test_importing_the_runner_does_not_import_the_gateway(self) -> None:
        root = Path(__file__).resolve().parents[2]
        completed = subprocess.run(
            [
                sys.executable,
                "-c",
                "import sys, market_swarm.runner, market_swarm.datasets, market_swarm.cli; "
                "assert 'market_swarm.gateway' not in sys.modules, 'gateway imported eagerly'",
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()

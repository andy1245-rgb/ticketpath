"""`tools/swarm_summary.py`: the aggregate a panel reads, and the refusals it makes on the way.

The failures worth testing here are the ones a small summary makes easy and a reader cannot
see: a truncated run presented as a whole one, a dry run's *predicted* status labelled as a
chain's answer, a policy declining its own budget folded into the count of transactions the
program refused, and a median taken over the wrong rows. Each test asserts on the dict the
tool returns, which is the same object it serialises.

The rows are written through the real `LedgerWriter` so the schema is the runner's and not a
copy kept here, and the sidecar is written the way `SwarmRunner._write_meta` writes it. No
chain, no key, no socket: this file's subject reads a file and does arithmetic.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from market_swarm.ledger import LEDGER_HEADER, LedgerWriter, TradeRow

from tools import swarm_summary

FACE = 1_000_000_000
CAP_BPS = 2500
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000
RUN_ID = "summary-test"


def _row(**overrides) -> TradeRow:
    """One row with every required field set, then whatever the test is about."""
    fields = dict(
        run_id=RUN_ID,
        seq=0,  # the writer stamps it
        ts="2026-11-08T00:00:00Z",
        event_id="evt_capped",
        mode="capped",
        agent_id="buyer-1",
        action="buy",
        ticket_id="tkt-1",
        from_wallet="house",
        to_wallet="buyer-1",
        price_lamports=FACE,
        face_lamports=FACE,
        cap_bps=CAP_BPS,
        ceiling_lamports=CEILING,
        markup_bps=0,
        status="ok",
        error_code=None,
        signature="5" * 88,
        slot=1,
        block_time=1_760_000_000,
        latency_ms=12,
        hop_index=1,
        budget_before=4_000_000_000,
        budget_after=3_000_000_000,
        chain="local-validator",
        program="v2",
        rationale="a primary buy at face",
    )
    fields.update(overrides)
    return TradeRow(**fields)


def _write(tmp: Path, rows: list[TradeRow], *, name: str = "evt_capped", **meta) -> Path:
    """A dataset and the sidecar beside it, in the shape the runner writes them."""
    path = tmp / f"{name}.jsonl"
    with LedgerWriter(path, header={**LEDGER_HEADER, "run_id": RUN_ID}) as writer:
        for row in rows:
            writer.write(row)
    side = {
        "record": "meta",
        "synthetic": True,
        "schema_version": 1,
        "label": "SYNTHETIC DATA",
        "disclaimer": "Synthetic data only.",
        "run_id": RUN_ID,
        "complete": True,
        "rounds_completed": 3,
        "event_id": "evt_capped",
        "mode": "capped",
        "cluster": "local",
        "program": "v2",
        "dry_run": False,
        "face_lamports": FACE,
        "cap_bps": CAP_BPS,
        "ceiling_lamports": CEILING,
        "tickets": 24,
        "rounds": 3,
        "seed": 7,
        "agents": [
            {"agent_id": "buyer-1", "policy": "buyer", "wallet_label": "buyer-1",
             "budget_lamports": 4_000_000_000, "budget_actions": 60},
            {"agent_id": "scalper-1", "policy": "scalper", "wallet_label": "scalper-1",
             "budget_lamports": 8_000_000_000, "budget_actions": 60},
        ],
        "budget": {"total_lamports": 80_000_000_000, "total_actions": 600},
        "provenance": "scripted",
        "llm": None,
        "rows": len(rows),
        "by_status": {},
        "kill_reason": None,
        "wall_seconds": 1.0,
        "note": "Synthetic data only.",
    }
    side.update(meta)
    Path(str(path).replace(".jsonl", ".meta.json")).write_text(
        json.dumps(side, indent=2, sort_keys=True), encoding="utf-8"
    )
    return path


def _mixed_rows() -> list[TradeRow]:
    """Four rows that exercise every bucket the summary separates."""
    return [
        # executed primary buy in round 1
        _row(round=1, price_lamports=FACE, markup_bps=0),
        # executed resale in round 2, at the ceiling
        _row(
            agent_id="scalper-1", action="resell", round=2,
            price_lamports=CEILING, markup_bps=2500, hop_index=2,
        ),
        # the chain refused this one: 6010, the program's own code
        _row(
            agent_id="scalper-1", action="resell", round=2, status="refused",
            price_lamports=1_400_000_000, markup_bps=4000, signature=None,
            error_code=6010, hop_index=0, rationale="over the ceiling",
        ),
        # a policy declining its own cap: no transaction, no code, action "refuse"
        _row(
            agent_id="scalper-1", action="refuse", round=3, status="skipped",
            price_lamports=None, markup_bps=None, signature=None, error_code=None,
            rationale="my own action budget is spent",
        ),
    ]


class TestTheCounts(unittest.TestCase):
    def test_executed_and_refused_are_counted_apart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["executed"], 2)
        # One chain refusal plus one policy's own decline: two different events, one total.
        self.assertEqual(summary["refused"], 2)
        event = summary["events"][0]
        self.assertEqual(event["refused_on_chain"], 1)
        self.assertEqual(event["declined_by_policy"], 1)
        # This fixture has no censored ask, so the third bucket is empty here; the next test is
        # the one that fills it.
        self.assertEqual(event["unfilled_asks"], 0)

    def test_an_ask_no_bid_met_is_its_own_outcome(self) -> None:
        """Not a trade and not a refusal: the third thing a capped market produces."""
        with tempfile.TemporaryDirectory() as tmp:
            rows = _mixed_rows() + [
                _row(
                    agent_id="scalper-1", action="resell", round=3, status="skipped",
                    price_lamports=1_300_000_000, markup_bps=3000, signature=None,
                    rationale="ask 1300000000 met no bid; a censored ask",
                )
            ]
            path = _write(Path(tmp), rows)
            summary = swarm_summary.build([path], None)

        event = summary["events"][0]
        self.assertEqual(event["unfilled_asks"], 1)
        self.assertEqual(event["refused"], 2, "the censored ask is not a refusal")
        self.assertEqual(event["executed"], 2, "and it is not a trade either")
        self.assertEqual(summary["unfilled_asks"], 1)

    def test_the_refusal_carries_the_programs_own_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["refused_by_code"]["6010"]["count"], 1)
        self.assertEqual(summary["refused_by_code"]["6010"]["name"], "E_CAP_EXCEEDED")

    def test_a_policy_decline_does_not_invent_a_code(self) -> None:
        """The chain never answered for that row, so the summary must not answer for it."""
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        total_coded = sum(entry["count"] for entry in summary["refused_by_code"].values())
        self.assertEqual(total_coded, 1)
        self.assertLess(total_coded, summary["refused"])

    def test_agents_and_rounds_come_from_the_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["agents"], 2)
        self.assertEqual(summary["agent_policies"], ["buyer", "scalper"])
        self.assertEqual(summary["rounds"], {"configured": 3, "completed": 3})

    def test_a_scripted_run_reports_a_measured_zero_and_says_why(self) -> None:
        # Not `null`: nothing was billed, so the number is known and it is zero. `null` would read
        # as "unknown", and a panel showing an unknown cost for a run that spent nothing is wrong
        # in the direction that makes a reader suspicious of the rest of the file.
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["cost"]["usd"], 0.0)
        self.assertIn("scripted", summary["cost"]["basis"])
        self.assertIsNone(summary["events"][0]["cost"]["llm"])

    def test_the_validator_block_names_a_cluster_and_never_a_port(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["validator"]["cluster"], "local")
        self.assertEqual(summary["validator"]["chain"], "local-validator")
        self.assertEqual(summary["validator"]["program"], "v2")
        # A committed file: no pid, no port, no path may reach it.
        text = json.dumps(summary)
        for forbidden in ("127.0.0.1", "localhost", "/home/", "pid"):
            self.assertNotIn(forbidden, text)


class TestTheTwoPricePaths(unittest.TestCase):
    def test_asked_includes_the_refused_ask_and_cleared_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        paths = summary["events"][0]["price_paths"]
        asked = {point["round"]: point for point in paths["asked"]["points"]}
        cleared = {point["round"]: point for point in paths["cleared"]["points"]}

        # Round 2 asked twice: the ceiling, which cleared, and 1.4 SOL, which the chain refused.
        # The nearest-rank median of two integers is the lower one, so the refusal is only
        # visible in `max_lamports` -- which is exactly why that field exists.
        self.assertEqual(asked[2]["n"], 2)
        self.assertEqual(cleared[2]["n"], 1)
        self.assertEqual(cleared[2]["median_lamports"], CEILING)
        self.assertEqual(asked[2]["max_lamports"], 1_400_000_000)
        self.assertGreater(asked[2]["max_lamports"], CEILING)

        # A round where nothing cleared still has an ask, and its cleared point is null rather
        # than absent or zero: zero is a price and this was not one.
        self.assertEqual(asked[3]["n"], 0)
        self.assertIsNone(cleared[3]["median_lamports"])

    def test_the_ceiling_travels_with_the_event(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertEqual(summary["events"][0]["ceiling_lamports"], CEILING)

    def test_the_synthetic_label_is_on_the_aggregate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            summary = swarm_summary.build([path], None)

        self.assertTrue(summary["synthetic"])
        self.assertEqual(summary["label"], "SYNTHETIC")
        self.assertIn("Synthetic data only", summary["note"])


class TestTheRefusals(unittest.TestCase):
    def test_no_sidecar_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            Path(str(path).replace(".jsonl", ".meta.json")).unlink()
            with self.assertRaises(swarm_summary.SummaryError) as caught:
                swarm_summary.build([path], None)
        self.assertIn("no ", str(caught.exception))

    def test_an_incomplete_run_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows(), complete=False)
            with self.assertRaises(swarm_summary.SummaryError) as caught:
                swarm_summary.build([path], None)
        self.assertIn("complete", str(caught.exception))

    def test_a_dry_run_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows(), dry_run=True)
            with self.assertRaises(swarm_summary.SummaryError) as caught:
                swarm_summary.build([path], None)
        self.assertIn("dry_run", str(caught.exception))

    def test_a_simulated_chain_under_a_live_sidecar_is_refused(self) -> None:
        """The file disagreeing with itself about whether anything was sent."""
        with tempfile.TemporaryDirectory() as tmp:
            rows = _mixed_rows()
            rows[0] = _row(round=1, chain="simulated", signature=None)
            path = _write(Path(tmp), rows)
            with self.assertRaises(swarm_summary.SummaryError) as caught:
                swarm_summary.build([path], None)
        self.assertIn("simulated", str(caught.exception))

    def test_two_runs_are_not_summarised_as_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            first = _write(Path(tmp), _mixed_rows(), name="a")
            second = _write(Path(tmp), _mixed_rows(), name="b", run_id="another-run")
            with self.assertRaises(swarm_summary.SummaryError) as caught:
                swarm_summary.build([first, second], None)
        self.assertIn("run_id", str(caught.exception))

    def test_the_cli_exits_one_and_says_nothing_on_stdout(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows(), complete=False)
            self.assertEqual(swarm_summary.main(["build", "--dataset", str(path)]), 1)


class TestTheCommandLine(unittest.TestCase):
    def test_build_writes_the_file_it_was_asked_for(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = _write(Path(tmp), _mixed_rows())
            out = Path(tmp) / "summary.json"
            self.assertEqual(
                swarm_summary.main(["build", "--dataset", str(path), "--out", str(out)]), 0
            )
            written = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(written["executed"], 2)
        self.assertEqual(written["record"], "swarm-summary")

    def test_two_events_are_summed_and_kept_apart(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            capped = _write(Path(tmp), _mixed_rows(), name="capped")
            monitored = _write(
                Path(tmp), _mixed_rows(), name="monitored",
                event_id="evt_monitored", mode="monitored", cap_bps=65535,
                ceiling_lamports=7_553_500_000,
            )
            summary = swarm_summary.build([capped, monitored], None)

        self.assertEqual(len(summary["events"]), 2)
        self.assertEqual(summary["executed"], 4)
        self.assertEqual(
            [event["mode"] for event in summary["events"]], ["capped", "monitored"]
        )


if __name__ == "__main__":
    unittest.main()

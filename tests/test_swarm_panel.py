"""`tools/swarm_panel.py`: the committed run panel, and the checks that keep it true.

The subject is a transcription, so the failures worth testing are the ones a transcription
makes easy: a count typed instead of counted, a status word mapped to the wrong column, a
label that says "validator" over a dry run, a chart and a run id that do not belong
together, and a committed file that quietly stopped matching its source. Every assertion is
on a file the tool wrote, or on the real committed files, not on a helper's return value.

The synthetic meta files here are built to the schema the runner writes, one agent and
three outcomes, so the test does not need a swarm run and never writes to `.swarm-runs/`.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools import swarm_panel

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMITTED = REPO_ROOT / "frontend" / "data" / "sim-run.json"


def _meta(mode: str, **over) -> dict:
    row = {
        "run_id": swarm_panel.RUN_ID,
        "mode": mode,
        "dry_run": True,
        "cluster": "local",
        "llm": None,
        "synthetic": True,
        "complete": True,
        "rounds": 12,
        "rounds_completed": 12,
        "by_status": {"ok": 7, "refused": 2, "skipped": 3},
        "agents": [
            {"agent_id": "a1", "policy": "buyer"},
            {"agent_id": "a2", "policy": "holder"},
        ],
        "tickets": 4,
        "cap_bps": 2500,
        "ceiling_lamports": 1_250_000_000,
    }
    row.update(over)
    return row


def _chart(mode: str) -> bytes:
    return (
        b'<?xml version="1.0" encoding="UTF-8"?>\n<svg><title>run '
        + swarm_panel.RUN_ID.encode("utf-8")
        + b" evt_"
        + mode.encode("utf-8")
        + b"</title></svg>\n"
    )


class Workspace:
    """A throwaway tree with the four directories the tool reads and writes."""

    def __init__(self, root: Path) -> None:
        self.root = root
        self.meta = root / ".swarm-runs"
        self.out = root / "frontend" / "data" / "sim-run.json"
        self.charts = root / "frontend" / "public" / "charts"
        self.source = root / "docs" / "charts"
        for directory in (self.meta, self.out.parent, self.source):
            directory.mkdir(parents=True, exist_ok=True)
        for mode in swarm_panel.MODES:
            (self.meta / f"{swarm_panel.RUN_ID}-evt_{mode}-SYNTHETIC.meta.json").write_text(
                json.dumps(_meta(mode)), encoding="utf-8"
            )
            (self.source / f"price-path-evt_{mode}.svg").write_bytes(_chart(mode))

    def argv(self, *extra: str) -> list[str]:
        return [
            "--meta", str(self.meta),
            "--out", str(self.out),
            "--charts-dir", str(self.charts),
            "--source-charts", str(self.source),
            *extra,
        ]


class TranscriptionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Workspace(Path(self.temp.name))

    def test_the_panel_counts_its_agents_and_maps_its_status_words(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        panel = json.loads(self.workspace.out.read_text(encoding="utf-8"))
        self.assertEqual(panel["schema"], 1)
        self.assertEqual(panel["runId"], swarm_panel.RUN_ID)
        self.assertEqual(panel["recordedOn"], "2026-11-08")
        self.assertEqual(panel["agentCount"], 2)
        self.assertEqual(panel["agents"], [{"id": "a1", "policy": "buyer"}, {"id": "a2", "policy": "holder"}])
        self.assertEqual(panel["label"], "SCRIPTED AGENTS · DRY RUN · SYNTHETIC")
        self.assertIn("simulated", panel["chain"])
        self.assertNotIn("validator was used", panel["chain"])
        self.assertIsNone(panel["cost"]["usd"])
        self.assertTrue(panel["cost"]["reason"])
        mode = next(row for row in panel["modes"] if row["mode"] == "capped")
        self.assertEqual(mode["decisions"], {"executed": 7, "refused": 2, "skipped": 3, "total": 12})
        self.assertEqual(mode["rounds"], 12)
        self.assertEqual(mode["tickets"], 4)
        self.assertEqual(mode["capBps"], 2500)
        self.assertEqual(mode["ceilingLamports"], 1_250_000_000)
        self.assertEqual(mode["chart"], "/charts/price-path-evt_capped.svg")

    def test_the_charts_are_byte_copies(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        for mode in swarm_panel.MODES:
            source = self.workspace.source / f"price-path-evt_{mode}.svg"
            copy = self.workspace.charts / f"price-path-evt_{mode}.svg"
            self.assertEqual(copy.read_bytes(), source.read_bytes())

    def test_two_runs_of_the_tool_write_the_same_bytes(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        first = self.workspace.out.read_bytes()
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        self.assertEqual(self.workspace.out.read_bytes(), first)

    def test_an_unknown_status_key_is_refused_and_nothing_is_written(self) -> None:
        path = self.workspace.meta / f"{swarm_panel.RUN_ID}-evt_capped-SYNTHETIC.meta.json"
        path.write_text(json.dumps(_meta("capped", by_status={"ok": 1, "exploded": 2})), encoding="utf-8")
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 1)
        self.assertFalse(self.workspace.out.exists(), "a refused transcription writes no panel")

    def test_a_run_that_used_a_validator_is_refused_not_relabelled(self) -> None:
        for over in ({"dry_run": False}, {"cluster": "devnet"}, {"llm": {"model": "x"}}):
            with self.subTest(over=over):
                path = self.workspace.meta / f"{swarm_panel.RUN_ID}-evt_capped-SYNTHETIC.meta.json"
                path.write_text(json.dumps(_meta("capped", **over)), encoding="utf-8")
                self.assertEqual(swarm_panel.main(self.workspace.argv()), 1)
                self.assertFalse(self.workspace.out.exists())
                path.write_text(json.dumps(_meta("capped")), encoding="utf-8")

    def test_a_chart_from_another_run_is_refused(self) -> None:
        path = self.workspace.source / "price-path-evt_capped.svg"
        path.write_bytes(b"<svg><title>some other run</title></svg>")
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 1)
        self.assertFalse(self.workspace.out.exists())


class CheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Workspace(Path(self.temp.name))

    def test_a_fresh_transcription_passes_its_own_check(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        self.assertEqual(swarm_panel.main(self.workspace.argv("--check")), 0)

    def test_a_committed_file_that_stopped_matching_the_run_fails(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        panel = json.loads(self.workspace.out.read_text(encoding="utf-8"))
        panel["agentCount"] = 99
        self.workspace.out.write_text(json.dumps(panel), encoding="utf-8")
        self.assertEqual(swarm_panel.main(self.workspace.argv("--check")), 1)

    def test_a_chart_copy_edited_after_it_was_made_fails(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        copy = self.workspace.charts / "price-path-evt_monitored.svg"
        copy.write_bytes(copy.read_bytes() + b"<!-- edited -->")
        self.assertEqual(swarm_panel.main(self.workspace.argv("--check")), 1)

    def test_a_clone_without_the_run_still_checks_the_shape_and_the_charts(self) -> None:
        self.assertEqual(swarm_panel.main(self.workspace.argv()), 0)
        # No meta directory: the run cannot be re-derived, but the file's own claims and the
        # chart bytes can still be checked, and the tool says which check it could not make.
        shutil.rmtree(self.workspace.meta)
        self.assertEqual(swarm_panel.main(self.workspace.argv("--check")), 0)
        panel = json.loads(self.workspace.out.read_text(encoding="utf-8"))
        panel["cost"]["usd"] = "0.008261"
        self.workspace.out.write_text(json.dumps(panel), encoding="utf-8")
        self.assertEqual(swarm_panel.main(self.workspace.argv("--check")), 1)


class CommittedPanelTest(unittest.TestCase):
    """The real files in the tree, which is what a page will read."""

    def test_the_committed_panel_is_the_measured_run(self) -> None:
        panel = json.loads(COMMITTED.read_text(encoding="utf-8"))
        self.assertEqual(panel["runId"], "sw20261108T054830Z6297")
        self.assertEqual(panel["agentCount"], 9, "counted from the meta, never typed")
        self.assertEqual(panel["label"], "SCRIPTED AGENTS · DRY RUN · SYNTHETIC")
        self.assertEqual(panel["chain"], "dry run: the chain is simulated in the run, not a validator")
        self.assertIsNone(panel["cost"]["usd"])
        modes = {row["mode"]: row for row in panel["modes"]}
        self.assertEqual(modes["capped"]["decisions"], {"executed": 32, "refused": 4, "skipped": 15, "total": 51})
        self.assertEqual(modes["monitored"]["decisions"], {"executed": 64, "refused": 4, "skipped": 38, "total": 106})
        self.assertEqual(modes["capped"]["ceilingLamports"], 1_250_000_000)
        self.assertEqual(modes["capped"]["capBps"], 2500)

    def test_the_committed_panel_passes_the_tool_check(self) -> None:
        # Default paths. The run's meta files are git-ignored and may not be on this machine;
        # the chart copies and the file's own claims are checked either way.
        self.assertEqual(swarm_panel.main(["--check"]), 0)


if __name__ == "__main__":
    unittest.main()

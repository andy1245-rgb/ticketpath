"""The CLI surface: the same payload without a browser, which is what makes it testable.

`python3 tools/guidance.py --event ... --as-of ...` must print exactly what the console
receives in-process for the same parameters, or one of the two surfaces is lying.
"""

from __future__ import annotations

import datetime as dt
import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import guidance as cli  # noqa: E402

UTC = dt.timezone.utc
CLOCK = dt.datetime(2026, 11, 7, 12, 0, 0, tzinfo=UTC)


class TestCli(unittest.TestCase):
    def run_cli(self, argv: list[str]) -> str:
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            cli.main(argv)
        return buffer.getvalue()

    def test_events_lists_ids_and_tiers(self) -> None:
        out = self.run_cli(["--events"])
        self.assertIn("evt_syn_02", out)
        self.assertIn("tier_stg_general", out)

    def test_the_payload_equals_the_in_process_payload(self) -> None:
        out = self.run_cli(["--event", "evt_syn_04", "--as-of", "2026-11-07T12:00:00Z", "--tau", "0.2"])
        payload = json.loads(out)
        in_process = cli.build_orchestrator("2026-11-07T12:00:00Z").price_guidance(
            event_id="evt_syn_04", as_of="2026-11-07T12:00:00Z", tau="0.2"
        )
        self.assertEqual(payload["decision"], in_process["decision"])
        self.assertEqual(payload["event"], in_process["event"])
        self.assertEqual(payload["tiers"], in_process["tiers"])

    def test_the_script_runs_as_a_subprocess(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/guidance.py", "--events"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("evt_syn_02", result.stdout)

    def test_the_simulation_flag_adds_simulated_lines(self) -> None:
        payload = json.loads(self.run_cli(["--as-of", "2026-11-07T12:00:00Z", "--sim"]))
        self.assertTrue(payload["sim"])
        self.assertTrue(all(line["simulated"] for line in payload["sim"]))


if __name__ == "__main__":
    unittest.main()

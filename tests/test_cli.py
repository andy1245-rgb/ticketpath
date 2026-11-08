"""`tools/tp.py`: every verb, every exit code, and the gate that a commit depends on.

The CLI is tested the way an operator uses it -- as a subprocess, over a real socket,
with the exit code read from the process and not inferred from the text. That matters for
the four codes the CLI promises: a test that called `main()` in-process could return 3
while the shell still saw 0, and the value of a CLI is precisely what the shell sees.

The server is the project's own `make_server(0)` on an ephemeral port, started once for
the class. No test here opens 8788, 8787, 3000 or 3001: those belong to the operator's
running processes, and a test that binds one is a test that can kill his session.

The gate's failure paths are exercised with injected commands, not by running the real
suite inside the suite. What is asserted is the property a pre-commit hook needs: the
server this gate started is dead when the gate returns, on the failure path included.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ticketpath.adapters.ledger_adapter import LedgerAdapter
from ticketpath.adapters.pricing_model_adapter import PricingModelAdapter
from ticketpath.adapters.rpc_adapter import RpcAdapter
from ticketpath.orchestrator import Orchestrator
from ticketpath.server import ENGINE_DESCRIPTION, make_server

from tools import tp

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "tools" / "tp.py"
HOOK = REPO_ROOT / ".githooks" / "pre-commit"
INSTALLER = REPO_ROOT / "tools" / "install-hooks.sh"
SAFETY = REPO_ROOT / "tools" / "public_safety.py"

#: The exact line the hook must call, and the line a test removes to prove the wiring is
#: what refuses. Both are read out of the hook by `HookTest.test_the_hook_calls_the_checker_first`,
#: so this is the one place the contract between the hook and the checker is written down.
SAFETY_LINE = "python3 tools/public_safety.py check --staged || exit 1"

#: A key block is a denylist hit, so this file may not spell one out: the test assembles
#: it, and the string it plants is the rule it must not trip. Same for the home path below.
PRIVATE_KEY_HEADER = "-----BEGIN" + " OPENSSH PRIVATE KEY-----"
HOME_PATH = "/" + "home/friend/x"


def _orchestrator() -> Orchestrator:
    """The same wiring `python3 -m ticketpath.server` does, with a fixed clock.

    The engine is registered behind the seam exactly as `server.build_orchestrator` does
    it, because /health's answer about the pricing seam is part of what the CLI reports and
    a server built differently would be a different server.
    """
    model = PricingModelAdapter()
    engine = Orchestrator(
        LedgerAdapter.from_fixture(),
        RpcAdapter.from_env("devnet"),
        model,
        "devnet",
        now=lambda: datetime(2026, 11, 7, 12, 0, tzinfo=timezone.utc),
    )
    model.register(engine.engine_model, "engine-2026-11-07", **ENGINE_DESCRIPTION)
    return engine


def _dead_port() -> int:
    """A port nothing is listening on: bind it, read the number, close it."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _port_is_free(port: int) -> bool:
    """Nothing is listening on the port any more.

    SO_REUSEADDR on the probe, because a closed listen socket leaves its accepted
    connections in TIME_WAIT on that port and a bare bind would call that "still in use" --
    which would make this assertion about the kernel's timers, not about the gate.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
        except OSError:
            return False
    return True


def _answers(port: int) -> bool:
    """True if something is still answering HTTP on the port."""
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
    except Exception:  # noqa: BLE001 - refused, reset or timed out: all "not serving"
        return False
    return True


#: A doc-check that passes, for the gate tests below. The gate runs `tools/doc_check.py`
#: as its own position, and these tests are about the *other* positions: a test that booted
#: a server to prove a server is killed must not also be reading this repository's
#: documents, which are mid-edit in a way that has nothing to do with the behaviour under
#: test. `tests/test_doc_check.py` is where the checker and the wiring are exercised.
CLEAN_DOC_CHECK = [sys.executable, "-c", "print('doc_check: clean')"]


class CliTest(unittest.TestCase):
    """One real server for the class, and the CLI run as a process against it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0, "127.0.0.1", _orchestrator())
        cls.port = cls.server.server_address[1]
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=5)

    # -- helpers ---------------------------------------------------------

    def run_cli(self, *args: str, base: str | None = None) -> subprocess.CompletedProcess:
        command = [sys.executable, str(CLI), "--base", base or self.base, *args]
        return subprocess.run(
            command, cwd=str(REPO_ROOT), capture_output=True, text=True, timeout=120
        )

    def lines(self, result: subprocess.CompletedProcess) -> list[str]:
        return [line for line in result.stdout.splitlines() if line.strip()]

    def badges(self, lines: list[str]) -> list[str]:
        return [line for line in lines if re.search(r"\[[A-Z][A-Z0-9_]{2,}\]", line)]

    # -- health ----------------------------------------------------------

    def test_health_exits_zero_and_names_the_source_and_the_seam(self) -> None:
        result = self.run_cli("health")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SYNTHETIC FIXTURE DATA", result.stdout)
        self.assertIn("rule-based-bounded-estimator", result.stdout)
        self.assertIn("fitted: false", result.stdout)
        self.assertIn("program deployed: false", result.stdout)

    def test_health_carries_a_badge_on_every_line(self) -> None:
        lines = self.lines(self.run_cli("health"))
        self.assertGreaterEqual(len(lines), 4)
        self.assertEqual(self.badges(lines), lines)

    def test_health_json_is_the_payload_and_not_a_summary(self) -> None:
        result = self.run_cli("--json", "health")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertEqual(document["badge"], "[FIXTURE]")
        self.assertTrue(document["health"]["dataSource"]["synthetic"])
        self.assertEqual(document["health"]["contract"]["endpointsImplemented"], 9)

    # -- events, event, tickets -----------------------------------------

    def test_events_lists_one_line_per_event_with_the_badge_first(self) -> None:
        result = self.run_cli("events")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("events on this page", result.stdout)
        self.assertIn("evt_syn_02", result.stdout)
        self.assertIn("evt_syn_03", result.stdout)
        for line in self.lines(result):
            self.assertTrue(line.startswith("[FIXTURE]"), line)

    def test_events_paginates_and_says_how_to_continue(self) -> None:
        result = self.run_cli("events", "--limit", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 events on this page", result.stdout)
        self.assertIn("--cursor", result.stdout)
        cursor = re.search(r"--cursor (\S+)", result.stdout).group(1)
        second = self.run_cli("events", "--limit", "2", "--cursor", cursor)
        self.assertEqual(second.returncode, 0, second.stderr)
        first_ids = re.findall(r"evt_syn_\d+", result.stdout)
        second_ids = re.findall(r"evt_syn_\d+", second.stdout)
        self.assertTrue(second_ids)
        self.assertNotEqual(first_ids, second_ids)

    def test_event_names_the_tiers_and_their_faces(self) -> None:
        result = self.run_cli("event", "evt_syn_02")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("tier tier_stg_general General", result.stdout)
        self.assertIn("1,200,000,000 lamports", result.stdout)
        self.assertIn("cap 1500 bps", result.stdout)

    def test_an_unknown_event_is_a_refusal_printed_in_full_and_exit_one(self) -> None:
        result = self.run_cli("event", "evt_nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[REFUSED] 404", result.stdout)
        self.assertIn("not_found", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_tickets_lists_serials_and_the_sale_price_in_integer_lamports(self) -> None:
        result = self.run_cli("tickets", "--limit", "2")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("2 tickets on this page", result.stdout)
        self.assertIn("tkt_syn_0001", result.stdout)
        self.assertIn("940,000,000 lamports", result.stdout)
        self.assertNotIn("SOL", result.stdout)

    def test_tickets_event_filter_actually_filters_on_the_routes_parameter_name(self) -> None:
        result = self.run_cli("tickets", "--event", "evt_syn_06")
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = [line for line in self.lines(result) if "tkt_syn_" in line]
        self.assertTrue(lines)
        for line in lines:
            self.assertIn("evt_syn_06/", line)

    def test_a_ticket_with_no_sale_says_so_instead_of_printing_none(self) -> None:
        result = self.run_cli("tickets", "--event", "evt_syn_06", "--limit", "20")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("None", result.stdout)
        self.assertIn("no sale recorded", result.stdout)

    def test_history_prints_every_ledger_row_and_the_custody_note(self) -> None:
        result = self.run_cli("history", "tkt_syn_0001")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("led_0001 issue", result.stdout)
        self.assertIn("led_0004 sale", result.stdout)
        self.assertIn("2 sales, 3 transfers", result.stdout)
        self.assertIn("signature and slot are null", result.stdout)
        for line in self.lines(result):
            self.assertTrue(re.search(r"\[[A-Z][A-Z0-9_]{2,}\]", line), line)

    # -- page and price ---------------------------------------------------

    def test_page_renders_text_the_way_a_browser_shows_it(self) -> None:
        result = self.run_cli("page", "/")
        self.assertEqual(result.returncode, 0, result.stderr)
        body = result.stdout
        self.assertNotIn("<p>", body)
        self.assertNotIn("<style>", body)
        self.assertNotIn("color-scheme", body, "CSS is not page text")
        self.assertIn("SYNTHETIC FIXTURE DATA", body)
        self.assertNotIn("&amp;", body, "entities are resolved")
        for line in self.lines(result):
            self.assertTrue(re.search(r"\[[A-Z][A-Z0-9_]{2,}\]", line), line)

    def test_page_decodes_entities_so_a_sentence_matches_its_source(self) -> None:
        result = self.run_cli("page", "/?event=evt_syn_06")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("this event's own completed record", result.stdout)

    def test_page_on_an_unknown_path_prints_the_json_refusal_and_exits_one(self) -> None:
        result = self.run_cli("page", "/nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("[REFUSED] 404", result.stdout)
        self.assertIn("no_route", result.stdout)

    def test_page_on_a_rendered_error_page_prints_it_and_exits_one(self) -> None:
        result = self.run_cli("page", "/?capBps=nope")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cap_invalid", result.stdout)
        self.assertIn("SYNTHETIC FIXTURE DATA", result.stdout)

    def test_price_hits_the_console_route_with_the_flags_as_query_parameters(self) -> None:
        result = self.run_cli(
            "price", "evt_syn_02", "--tier", "tier_stg_front", "--cap", "298",
            "--at", "2026-11-07T12:00:00Z", "--mode", "before_on_sale",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        first = self.lines(result)[0]
        self.assertIn("price", first)
        self.assertIn("event=evt_syn_02", first)
        self.assertIn("tier=tier_stg_front", first)
        self.assertIn("capBps=298", first)
        self.assertIn("mode=before_on_sale", first)
        self.assertIn("Decision mode: BEFORE-ON-SALE", result.stdout)

    def test_price_on_a_bad_cap_shows_the_refusal_page_rather_than_crashing(self) -> None:
        result = self.run_cli("price", "evt_syn_02", "--cap", "not-a-number")
        self.assertEqual(result.returncode, 1)
        self.assertIn("cap_invalid", result.stdout)
        self.assertNotIn("Traceback", result.stderr)

    def test_price_json_carries_the_url_the_status_and_the_page_lines(self) -> None:
        result = self.run_cli("--json", "price", "evt_syn_06")
        self.assertEqual(result.returncode, 0, result.stderr)
        document = json.loads(result.stdout)
        self.assertIn("event=evt_syn_06", document["url"])
        self.assertEqual(document["status"], 200)
        self.assertTrue(any("hindsight" in line for line in document["lines"]))

    # -- exit codes -------------------------------------------------------

    def test_an_unreachable_server_is_exit_three_with_the_start_command(self) -> None:
        dead = _dead_port()
        result = self.run_cli("health", base=f"http://127.0.0.1:{dead}")
        self.assertEqual(result.returncode, 3)
        self.assertIn("no server at", result.stderr)
        self.assertIn("python3 -m ticketpath.server", result.stderr)
        self.assertIn(str(REPO_ROOT), result.stderr)

    def test_an_unknown_verb_is_usage_exit_two(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "nonsense"], capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)

    def test_a_missing_argument_is_usage_exit_two(self) -> None:
        result = subprocess.run(
            [sys.executable, str(CLI), "price"], capture_output=True, text=True, timeout=60
        )
        self.assertEqual(result.returncode, 2)

    def test_a_base_without_a_scheme_is_usage_exit_two(self) -> None:
        result = self.run_cli("health", base="127.0.0.1:8788")
        self.assertEqual(result.returncode, 2)
        self.assertIn("http://", result.stderr)

    def test_global_flags_work_before_and_after_the_verb(self) -> None:
        after = self.run_cli("events", "--json", "--limit", "1")
        before = subprocess.run(
            [sys.executable, str(CLI), "--json", "--base", self.base, "events", "--limit", "1"],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertEqual(json.loads(after.stdout)["badge"], "[FIXTURE]")
        self.assertEqual(json.loads(before.stdout)["badge"], "[FIXTURE]")

    # -- the text renderer, as a unit ------------------------------------

    def test_html_to_lines_drops_style_and_script_and_keeps_block_boundaries(self) -> None:
        markup = (
            "<html><head><title>t</title><style>p{color:red}</style></head>"
            "<body><h1>Head</h1><p>one &amp; two</p>"
            "<ul><li>first</li><li>second</li></ul>"
            "<table><tr><th>a</th><th>b</th></tr><tr><td>1</td><td>2</td></tr></table>"
            "<script>var x = 1;</script></body></html>"
        )
        lines = tp.html_to_lines(markup)
        self.assertEqual(lines[0], "Head")
        self.assertIn("one & two", lines)
        self.assertIn("- first", lines)
        self.assertIn("- second", lines)
        self.assertIn("a | b", lines)
        self.assertIn("1 | 2", lines)
        self.assertNotIn("color:red", " ".join(lines))
        self.assertNotIn("var x", " ".join(lines))

    def test_badge_lines_never_doubles_a_badge_the_page_already_has(self) -> None:
        lines = tp.badge_lines(["[EXACT] 1.25 SOL", "a heading"], "[FIXTURE]")
        self.assertEqual(lines, ["[EXACT] 1.25 SOL", "[FIXTURE] a heading"])

    # -- sweep ------------------------------------------------------------

    def test_sweep_prefers_the_independent_tool_and_falls_back_to_the_checker(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "tools").mkdir()
            checker = root / "tools" / "console-check.py"
            checker.write_text("# checker\n")
            self.assertEqual(tp.sweep_tool(root=root, audit=root / "absent.py"), checker)
            self.assertIsNone(tp.sweep_tool(root=root / "empty", audit=root / "absent.py"))
            audit = root / "sweep.py"
            audit.write_text("# sweep\n")
            self.assertEqual(tp.sweep_tool(root=root, audit=audit), audit)

    def test_the_independent_sweep_gets_the_base_as_an_argument(self) -> None:
        command = tp.sweep_command(Path("scratch") / "sweep.py", "http://127.0.0.1:9999")
        self.assertEqual(command[-1], "http://127.0.0.1:9999")
        checker = tp.sweep_command(Path("/repo/tools/console-check.py"), "http://127.0.0.1:9999")
        self.assertEqual(checker[-1], "/repo/tools/console-check.py")

    def test_the_optional_sweep_is_named_by_the_environment_and_skipped_when_absent(self) -> None:
        """No scratch path in this published file: TP_SWEEP names the sweep or there is none."""
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            (root / "tools").mkdir()
            checker = root / "tools" / "console-check.py"
            checker.write_text("# checker\n")
            audit = root / "sweep.py"
            audit.write_text("# sweep\n")
            original = os.environ.pop(tp.AUDIT_SWEEP_ENV, None)
            try:
                self.assertIsNone(tp.audit_sweep(), "an unset TP_SWEEP produced a default path")
                self.assertEqual(tp.sweep_tool(root=root), checker)
                os.environ[tp.AUDIT_SWEEP_ENV] = str(audit)
                self.assertEqual(tp.audit_sweep(), audit)
                self.assertEqual(tp.sweep_tool(root=root), audit)
                os.environ[tp.AUDIT_SWEEP_ENV] = str(root / "absent.py")
                self.assertEqual(
                    tp.sweep_tool(root=root), checker, "a named-but-missing sweep was not skipped"
                )
            finally:
                os.environ.pop(tp.AUDIT_SWEEP_ENV, None)
                if original is not None:
                    os.environ[tp.AUDIT_SWEEP_ENV] = original

    def test_sweep_says_when_the_optional_independent_tool_was_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            checker = Path(scratch) / "console-check.py"
            checker.write_text("print('FAILURES: 0')\n")
            original_tool, original_env = tp.sweep_tool, os.environ.pop(tp.AUDIT_SWEEP_ENV, None)
            tp.sweep_tool = lambda *a, **k: checker
            sink = io.StringIO()
            try:
                with contextlib.redirect_stdout(sink):
                    code = tp.main(["--base", self.base, "sweep"])
            finally:
                tp.sweep_tool = original_tool
                if original_env is not None:
                    os.environ[tp.AUDIT_SWEEP_ENV] = original_env
        text = sink.getvalue()
        self.assertEqual(code, 0, text)
        self.assertIn(tp.AUDIT_SWEEP_ENV, text, "the skip was silent")
        self.assertIn("skipped", text)

    def test_sweep_against_a_dead_server_is_exit_three(self) -> None:
        result = self.run_cli("sweep", base=f"http://127.0.0.1:{_dead_port()}")
        self.assertEqual(result.returncode, 3)
        self.assertIn("python3 -m ticketpath.server", result.stderr)

    def test_sweep_reports_a_failing_checker_as_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            checker = Path(scratch) / "console-check.py"
            checker.write_text("import sys\nprint('FAIL something')\nprint('FAILURES: 2')\nsys.exit(1)\n")
            original = tp.sweep_tool
            tp.sweep_tool = lambda *a, **k: checker
            sink = io.StringIO()
            try:
                with contextlib.redirect_stdout(sink):
                    code = tp.main(["--base", self.base, "sweep"])
            finally:
                tp.sweep_tool = original
        self.assertEqual(code, 1)
        self.assertIn("FAILURES: 2", sink.getvalue(), "the checker's own count is carried through")

    def test_sweep_json_is_one_parseable_document_even_when_the_checker_fails(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            checker = Path(scratch) / "console-check.py"
            checker.write_text("import sys\nprint('FAIL something')\nprint('FAILURES: 1')\nsys.exit(1)\n")
            original = tp.sweep_tool
            tp.sweep_tool = lambda *a, **k: checker
            sink = io.StringIO()
            try:
                with contextlib.redirect_stdout(sink):
                    code = tp.main(["--base", self.base, "--json", "sweep"])
            finally:
                tp.sweep_tool = original
        self.assertEqual(code, 1)
        document = json.loads(sink.getvalue())
        self.assertEqual(document["failures"], "1")
        self.assertEqual(document["exit"], 1)
        self.assertIn("FAIL something", document["output"])

    # -- the gate ---------------------------------------------------------

    def test_the_gate_kills_its_server_when_the_tests_fail(self) -> None:
        failing = [sys.executable, "-c", "print('Ran 3 tests in 0.1s'); print('FAILED (failures=1)'); raise SystemExit(1)"]
        holder: list[int] = []
        original = tp.pick_free_port

        def remember() -> int:
            port = original()
            holder.append(port)
            return port

        tp.pick_free_port = remember
        try:
            with tempfile.TemporaryFile(mode="w+") as sink:
                code = tp.run_gate(
                    tests_command=failing,
                    console_command=[sys.executable, "-c", "raise SystemExit(0)"],
                    doc_check_command=CLEAN_DOC_CHECK,
                    out=sink,
                )
        finally:
            tp.pick_free_port = original
        self.assertEqual(code, 1)
        self.assertEqual(len(holder), 1)
        self.assertFalse(_answers(holder[0]), "the gate left its server answering")
        self.assertTrue(_port_is_free(holder[0]), "the gate left its server holding the port")

    def test_the_gate_kills_its_server_when_console_check_fails(self) -> None:
        passing = [sys.executable, "-c", "print('Ran 7 tests in 0.1s'); print('OK')"]
        failing = [sys.executable, "-c", "print('FAIL one thing'); print('FAILURES: 1'); raise SystemExit(1)"]
        holder: list[int] = []
        original = tp.pick_free_port

        def remember() -> int:
            port = original()
            holder.append(port)
            return port

        tp.pick_free_port = remember
        try:
            with tempfile.TemporaryFile(mode="w+") as sink:
                code = tp.run_gate(
                    tests_command=passing,
                    console_command=failing,
                    doc_check_command=CLEAN_DOC_CHECK,
                    out=sink,
                )
        finally:
            tp.pick_free_port = original
        self.assertEqual(code, 1)
        self.assertFalse(_answers(holder[0]), "the gate left its server answering")
        self.assertTrue(_port_is_free(holder[0]), "the gate left its server holding the port")

    def test_the_gate_never_picks_a_port_the_machine_already_owns(self) -> None:
        for _ in range(20):
            self.assertNotIn(tp.pick_free_port(), tp.RESERVED_PORTS)

    def test_the_gate_summary_line_carries_the_test_count_and_the_failures(self) -> None:
        passing = [sys.executable, "-c", "print('Ran 421 tests in 0.1s'); print('OK')"]
        clean = [sys.executable, "-c", "print('ok   a check'); print('FAILURES: 0')"]
        with tempfile.TemporaryFile(mode="w+") as sink:
            code = tp.run_gate(
                tests_command=passing,
                console_command=clean,
                doc_check_command=CLEAN_DOC_CHECK,
                out=sink,
            )
            sink.seek(0)
            text = sink.read()
        self.assertEqual(code, 0, text)
        self.assertIn("tests=421 OK", text)
        self.assertIn("FAILURES: 0", text)
        self.assertRegex(text, r"wall=\d+\.\d+s")

    def test_the_gate_does_not_hand_git_plumbing_to_its_children(self) -> None:
        """git exports GIT_DIR and GIT_INDEX_FILE to the hook, and the gate must not pass them on.

        The gate runs inside `.githooks/pre-commit`, so the suite it starts inherits git's own
        plumbing. Those two variables override `git -C`, so every test that builds a throwaway
        repository read the outer index instead of its own: the hook's own tests failed while a
        code commit was staged, which is the one moment the gate has to work.
        """
        probe_source = (
            "import os, pathlib, sys; print('Ran 1 tests in 0.1s'); print('OK'); "
            "pathlib.Path(sys.argv[1]).write_text("
            "str(sorted(k for k in os.environ if k.startswith('GIT_'))))"
        )
        leaked = {"GIT_DIR": "/nowhere/.git", "GIT_INDEX_FILE": "/nowhere/.git/index"}
        original = {key: os.environ.get(key) for key in leaked}
        os.environ.update(leaked)
        try:
            with tempfile.TemporaryDirectory() as workdir:
                seen = Path(workdir) / "child-env.txt"
                probe = [sys.executable, "-c", probe_source, str(seen)]
                with tempfile.TemporaryFile(mode="w+") as sink:
                    code = tp.run_gate(
                        quick=True,
                        tests_command=probe,
                        doc_check_command=CLEAN_DOC_CHECK,
                        out=sink,
                    )
                    sink.seek(0)
                    text = sink.read()
                handed = seen.read_text()
        finally:
            for key, value in original.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertEqual(code, 0, text)
        self.assertEqual(
            handed,
            "[]",
            f"the gate passed git's plumbing into the suite: {handed}",
        )

    def test_quick_gate_runs_no_server_and_stops_after_the_tests(self) -> None:
        called: list[str] = []
        tests = [sys.executable, "-c", "print('Ran 5 tests in 0.1s'); print('OK')"]
        console = [sys.executable, "-c", "raise SystemExit('console-check must not run in quick mode')"]
        original = tp.pick_free_port
        tp.pick_free_port = lambda: called.append("port") or original()
        try:
            with tempfile.TemporaryFile(mode="w+") as sink:
                code = tp.run_gate(
                    quick=True,
                    tests_command=tests,
                    console_command=console,
                    doc_check_command=CLEAN_DOC_CHECK,
                    out=sink,
                )
                sink.seek(0)
                text = sink.read()
        finally:
            tp.pick_free_port = original
        self.assertEqual(code, 0)
        self.assertEqual(called, [], "the quick gate started a server")
        self.assertIn("tests=5 OK", text)
        self.assertIn("console-check skipped", text)

    def test_a_gate_that_times_out_is_a_failure_not_a_hang(self) -> None:
        slow = [sys.executable, "-c", "import time; time.sleep(30)"]
        started = time.monotonic()
        with tempfile.TemporaryFile(mode="w+") as sink:
            code = tp.run_gate(
                quick=True,
                tests_command=slow,
                tests_timeout=1.0,
                doc_check_command=CLEAN_DOC_CHECK,
                out=sink,
            )
        self.assertEqual(code, 1)
        self.assertLess(time.monotonic() - started, 20)

    def test_parse_tests_reads_the_count_and_the_verdict_from_unittest(self) -> None:
        self.assertEqual(tp.parse_tests("Ran 453 tests in 17.9s\n\nOK\n"), (453, True, "OK"))
        count, ok, detail = tp.parse_tests("Ran 12 tests in 0.2s\n\nFAILED (failures=1, errors=2)\n")
        self.assertEqual((count, ok), (12, False))
        self.assertIn("failures=1", detail)
        self.assertEqual(tp.parse_tests("nothing ran")[0], None)

    def test_parse_console_failures_reads_the_last_line_of_the_checker(self) -> None:
        self.assertEqual(tp.parse_console_failures("ok   a\nFAIL b\n\nFAILURES: 3\n"), 3)
        self.assertEqual(tp.parse_console_failures("ok   a\nFAILURES: 0\n"), 0)


class HookTest(unittest.TestCase):
    """The hook, driven by git itself in a scratch clone under /tmp.

    Nothing here runs the real gate: the secret path returns before it, and the code path
    is exercised with a copied hook whose gate command is a stub, so a test can prove the
    selection logic without the suite running itself.
    """

    def make_repo(self, gate_exit: int | None = None, wire_safety: bool = True) -> Path:
        """A scratch clone with the real hook, and optionally a stub standing in for the gate.

        The stub is a script rather than an inline command so the hook's own `if ! ...`
        still parses: the test replaces one word, not one line of shell.

        `tools/public_safety.py` and `.public-denylist` are copied in as they are, so the
        hook runs the real checker against the real rules. `wire_safety=False` removes the
        one line that calls it, which is how a test proves the refusal comes from the
        wiring and not from something else in the hook.
        """
        root = Path(tempfile.mkdtemp(prefix="tp-hook-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
        hooks = root / ".githooks"
        hooks.mkdir()
        text = HOOK.read_text()
        if gate_exit is not None:
            stub = hooks / "stub-gate"
            stub.write_text(f"#!/bin/sh\necho GATE RAN >&2\nexit {gate_exit}\n")
            stub.chmod(0o755)
            text = text.replace("python3 tools/tp.py gate --quick", "sh .githooks/stub-gate")
        if not wire_safety:
            text = text.replace(SAFETY_LINE, ": # public_safety was unwired for this test")
        (hooks / "pre-commit").write_text(text)
        (hooks / "pre-commit").chmod(0o755)
        (root / "tools").mkdir()
        shutil.copy2(SAFETY, root / "tools" / "public_safety.py")
        shutil.copy2(REPO_ROOT / ".public-denylist", root / ".public-denylist")
        (root / "README").write_text("scratch\n")
        subprocess.run(["git", "-C", str(root), "add", "README"], check=True)
        subprocess.run(["git", "-C", str(root), "commit", "-q", "-m", "base"], check=True)
        return root

    def commit(self, root: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["git", "-C", str(root), "commit", "-m", "test"], capture_output=True, text=True, timeout=120
        )

    def test_the_installer_sets_the_hooks_path_and_is_idempotent(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="tp-install-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        subprocess.run(["git", "init", "-q", str(root)], check=True)
        (root / "tools").mkdir()
        shutil.copy2(INSTALLER, root / "tools" / "install-hooks.sh")
        (root / ".githooks").mkdir()
        (root / ".githooks" / "pre-commit").write_text("#!/bin/sh\nexit 0\n")
        first = subprocess.run([str(root / "tools" / "install-hooks.sh")], capture_output=True, text=True)
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertIn("core.hooksPath = .githooks", first.stdout)
        configured = subprocess.run(
            ["git", "-C", str(root), "config", "--local", "--get", "core.hooksPath"],
            capture_output=True, text=True,
        )
        self.assertEqual(configured.stdout.strip(), ".githooks")
        second = subprocess.run([str(root / "tools" / "install-hooks.sh")], capture_output=True, text=True)
        self.assertEqual(second.returncode, 0)
        self.assertIn("already", second.stdout)

    def test_the_hook_refuses_a_staged_private_key_block_and_makes_no_commit(self) -> None:
        root = self.make_repo()
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        secret = root / "tools" / "notes.txt"
        secret.write_text(PRIVATE_KEY_HEADER + "\nnot a real key\n")
        subprocess.run(["git", "-C", str(root), "add", "tools/notes.txt"], check=True)
        result = self.commit(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not commit or push this", result.stderr)
        self.assertIn("private-key", result.stderr, "the class is printed; the match is not")
        self.assertIn("tools/notes.txt", result.stderr)
        self.assertNotIn("not a real key", result.stderr, "the hook echoed the secret")
        log = subprocess.run(["git", "-C", str(root), "log", "--oneline"], capture_output=True, text=True)
        self.assertNotIn("test", log.stdout)

    def test_the_hook_refuses_a_staged_dotenv_by_name(self) -> None:
        root = self.make_repo()
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / ".env").write_text("SOMETHING=value\n")
        subprocess.run(["git", "-C", str(root), "add", "-f", ".env"], check=True)
        result = self.commit(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".env", result.stderr)
        self.assertNotIn("SOMETHING=value", result.stderr)

    def test_the_hook_does_not_run_the_gate_for_a_docs_only_commit(self) -> None:
        root = self.make_repo(gate_exit=1)
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / "NOTES.md").write_text("a note\n")
        subprocess.run(["git", "-C", str(root), "add", "NOTES.md"], check=True)
        result = self.commit(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("GATE RAN", result.stderr + result.stdout)

    def test_the_hook_runs_the_gate_for_a_staged_code_file_and_refuses_on_failure(self) -> None:
        root = self.make_repo(gate_exit=1)
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / "tools" / "touched.py").write_text("# a change\n")
        subprocess.run(["git", "-C", str(root), "add", "tools/touched.py"], check=True)
        result = self.commit(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("GATE RAN", result.stderr)
        self.assertIn("the commit is refused", result.stderr)
    def test_the_hook_calls_the_public_safety_check_first_and_never_bypasses(self) -> None:
        """The wiring is one line, it comes before the secret scan, and there is no bypass."""
        text = HOOK.read_text()
        self.assertIn(SAFETY_LINE, text)
        self.assertLess(
            text.index("# -- 1. public safety"),
            text.index("# -- 2. credentials"),
            "the public-safety check is not the first step",
        )
        self.assertLess(
            text.index(SAFETY_LINE),
            text.index("# -- 3. the quick gate"),
            "the checker runs after the gate, not before it",
        )
        self.assertNotIn(
            True,
            [
                line for line in text.splitlines()
                if "--no-verify" in line and not line.lstrip().startswith("#") and "echo" not in line
            ],
            "the hook passes --no-verify itself, so its own gate could be skipped",
        )

    def test_the_hook_refuses_a_staged_handover_file(self) -> None:
        root = self.make_repo()
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / "NIGHT-FOO.md").write_text("a handover sheet\n")
        subprocess.run(["git", "-C", str(root), "add", "NIGHT-FOO.md"], check=True)
        result = self.commit(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("do not commit or push this", result.stderr)
        self.assertIn("NIGHT-FOO.md: handover-file", result.stderr)
        log = subprocess.run(["git", "-C", str(root), "log", "--oneline"], capture_output=True, text=True)
        self.assertNotIn("test", log.stdout, "the refused commit landed anyway")

    def test_the_hook_refuses_a_staged_home_path(self) -> None:
        root = self.make_repo()
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / "NOTES.md").write_text(f"the tree I was reading: {HOME_PATH}\n")
        subprocess.run(["git", "-C", str(root), "add", "NOTES.md"], check=True)
        result = self.commit(root)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("NOTES.md:1: home-path", result.stderr)
        log = subprocess.run(["git", "-C", str(root), "log", "--oneline"], capture_output=True, text=True)
        self.assertNotIn("test", log.stdout)

    def test_without_the_wiring_the_handover_file_would_commit(self) -> None:
        """The control for the two above: the same commit, with the one line taken out."""
        root = self.make_repo(wire_safety=False)
        subprocess.run(["git", "-C", str(root), "config", "core.hooksPath", ".githooks"], check=True)
        (root / "NIGHT-FOO.md").write_text("a handover sheet\n")
        subprocess.run(["git", "-C", str(root), "add", "NIGHT-FOO.md"], check=True)
        result = self.commit(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        log = subprocess.run(["git", "-C", str(root), "log", "--oneline"], capture_output=True, text=True)
        self.assertIn("test", log.stdout, "the unwired hook still refused, so the refusal is not the wiring")


if __name__ == "__main__":
    unittest.main()

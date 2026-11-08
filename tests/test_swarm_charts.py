"""`tools/swarm_charts.py`: the label it enforces on itself, and the verifier that re-checks it.

The subject is a chart tool, so the failures worth testing are the ones a picture makes easy:
a template that loses the word SYNTHETIC, an asset edited after it was written, a dataset
that stopped in the middle of its horizon, and a price that is not an integer at all. Every
test asserts on the file the tool wrote, not on the object it returned.

The datasets come from the real runner in dry-run mode (`DryRunGateway`, no socket, no key,
~10 ms), and from hand-built rows written through the real `LedgerWriter`, so the schema is
the one the runner produces rather than a copy of it kept here.

Nothing here writes to `docs/charts`: every generation goes to a temporary directory.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as element_tree
from dataclasses import replace
from pathlib import Path

from market_swarm.config import AgentSpec, EventSpec, RunConfig
from market_swarm.gateway import make_gateway
from market_swarm.ledger import LEDGER_HEADER, LedgerWriter, TradeRow
from market_swarm.runner import SwarmRunner

from tools import swarm_charts

REPO_ROOT = Path(__file__).resolve().parents[1]
CLI = REPO_ROOT / "tools" / "swarm_charts.py"
SVG_NS = "{http://www.w3.org/2000/svg}"

FACE = 1_000_000_000
CAP_BPS = 2500
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000


def _run_config(out_dir: Path, *, rounds: int = 10, seed: int = 7) -> RunConfig:
    """A small two-event run: one capped record and one monitored record, same agents.

    `g1` is a greater-fool bidder with room for eight units. Without a bid it can absorb, the
    scalper's over-cap ask is never matched and the run produces no refusal at all -- which
    is the difference between a capped run that exercises the hook and one that does not.
    """
    agents = (
        AgentSpec("b1", "buyer", "b1", 11, 4_000_000_000, 120),
        AgentSpec("h1", "holder", "h1", 21, 4_000_000_000, 120),
        AgentSpec("f1", "flipper", "f1", 31, 4_000_000_000, 120),
        AgentSpec("s1", "scalper", "s1", 41, 4_000_000_000, 120),
        AgentSpec("g1", "greater_fool", "g1", 71, 8_000_000_000, 120, 8),
    )
    events = (
        EventSpec("evt_capped", FACE, "capped", CAP_BPS, 16, rounds, 3600),
        EventSpec("evt_monitored", FACE, "monitored", None, 16, rounds, 3600),
    )
    return RunConfig(
        run_id="swtest01",
        cluster="local",
        events=events,
        agents=agents,
        total_budget_lamports=40_000_000_000,
        total_budget_actions=600,
        kill_after_seconds=60.0,
        out_dir=out_dir,
        dry_run=True,
        seed=seed,
    )


def run_dry_swarm(out_dir: Path, **kwargs) -> list[Path]:
    """Run the harness against the dry gateway and return the dataset paths it wrote."""
    config = _run_config(out_dir, **kwargs)
    gateway = make_gateway("local", run_dir=out_dir, dry_run=True)
    gateway.start()
    try:
        summary = SwarmRunner(config, gateway).run()
    finally:
        gateway.stop()
    return [Path(path) for path in summary.dataset_paths]


def _row(**overrides) -> TradeRow:
    """A row shaped like the runner's, with a capped/monitored event's arithmetic."""
    base = dict(
        run_id="swtest02",
        seq=1,
        ts="2026-11-08T00:00:00Z",
        event_id="evt_capped",
        mode="capped",
        agent_id="b1",
        action="buy",
        ticket_id="evt_capped#0001",
        from_wallet="authority",
        to_wallet="b1",
        price_lamports=FACE,
        face_lamports=FACE,
        cap_bps=CAP_BPS,
        ceiling_lamports=CEILING,
        markup_bps=0,
        status="ok",
        error_code=None,
        signature=None,
        slot=None,
        block_time=None,
        latency_ms=None,
        hop_index=1,
        budget_before=0,
        budget_after=FACE,
        chain="simulated",
        program="v1",
        rationale="hand-built for a test",
        bid_lamports=None,
        lot_price_lamports=None,
        round=1,
        rounds_left=3,
    )
    base.update(overrides)
    return TradeRow(**base)


def _markup(price: int) -> int:
    return (price - FACE) * 10_000 // FACE


def write_dataset(
    out_dir: Path,
    rows: list[TradeRow],
    *,
    event_id: str = "evt_capped",
    name: str = "swtest02-evt_capped-SYNTHETIC.jsonl",
    complete: bool = True,
    dry_run: bool = True,
    sidecar_overrides: dict | None = None,
) -> Path:
    """Write a dataset through the real writer, plus the sidecar the runner writes."""
    path = out_dir / name
    header = dict(LEDGER_HEADER)
    header.update(
        {
            "run_id": "swtest02",
            "event_id": event_id,
            "mode": "capped",
            "cluster": "simulated" if dry_run else "local-validator",
            "dry_run": dry_run,
        }
    )
    with LedgerWriter(path, header=header) as writer:
        for row in rows:
            writer.write(replace(row, event_id=event_id))

    meta = {
        "record": "meta",
        "synthetic": True,
        "schema_version": 1,
        "label": LEDGER_HEADER["label"],
        "disclaimer": LEDGER_HEADER["disclaimer"],
        "run_id": "swtest02",
        "complete": complete,
        "rounds_completed": 4 if complete else 1,
        "event_id": event_id,
        "mode": "capped",
        "cluster": "local",
        "dry_run": dry_run,
        "face_lamports": FACE,
        "cap_bps": CAP_BPS,
        "ceiling_lamports": CEILING,
        "tickets": 4,
        "rounds": 4,
        "seed": 7,
        "agents": [],
        "budget": {},
        "rows": len(rows),
        "by_status": {},
        "kill_reason": None,
        "wall_seconds": 0.01,
        "note": "Synthetic. Not evidence about any real market price.",
    }
    meta.update(sidecar_overrides or {})
    path.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n")
    return path


def sample_rows() -> list[TradeRow]:
    """A capped event with an executed move, a refusal, an unmet ask and a listing."""
    return [
        _row(),
        _row(
            action="resell",
            agent_id="b1",
            from_wallet="b1",
            to_wallet="f1",
            ticket_id="evt_capped#0001",
            price_lamports=1_100_000_000,
            markup_bps=_markup(1_100_000_000),
            hop_index=2,
            round=2,
            rounds_left=2,
            lot_price_lamports=FACE,
            bid_lamports=1_150_000_000,
        ),
        _row(
            action="resell",
            agent_id="s1",
            from_wallet="s1",
            to_wallet="f1",
            ticket_id="evt_capped#0002",
            price_lamports=1_300_000_000,
            markup_bps=_markup(1_300_000_000),
            status="refused",
            error_code=6010,
            hop_index=None,
            round=3,
            rounds_left=1,
            lot_price_lamports=FACE,
            bid_lamports=1_350_000_000,
        ),
        _row(
            action="list",
            agent_id="h1",
            from_wallet=None,
            to_wallet=None,
            ticket_id="evt_capped#0003",
            price_lamports=1_200_000_000,
            markup_bps=_markup(1_200_000_000),
            hop_index=1,
            round=3,
            rounds_left=1,
        ),
        _row(
            action="buy",
            agent_id="f1",
            from_wallet=None,
            to_wallet=None,
            ticket_id=None,
            price_lamports=900_000_000,
            markup_bps=_markup(900_000_000),
            status="skipped",
            hop_index=None,
            round=4,
            rounds_left=0,
        ),
    ]


class ChartTestCase(unittest.TestCase):
    """A temporary directory per test, and two helpers that run the two verbs."""

    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="swarm-charts-")
        self.tmp = Path(self._tmp)
        self.out = self.tmp / "charts"

    def tearDown(self) -> None:
        shutil.rmtree(self._tmp, ignore_errors=True)

    def generate(self, *datasets: Path) -> tuple[int, str, str]:
        argv = ["generate", "--out", str(self.out)]
        for dataset in datasets:
            argv += ["--dataset", str(dataset)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = swarm_charts.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def verify(self, *datasets: Path) -> tuple[int, str, str]:
        argv = ["verify", "--out", str(self.out)]
        for dataset in datasets:
            argv += ["--dataset", str(dataset)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = swarm_charts.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    def generate_into(self, out: Path, *datasets: Path) -> tuple[int, str, str]:
        argv = ["generate", "--out", str(out)]
        for dataset in datasets:
            argv += ["--dataset", str(dataset)]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = swarm_charts.main(argv)
        return code, stdout.getvalue(), stderr.getvalue()

    # -- helpers on the generated files ------------------------------------

    def assets(self) -> list[Path]:
        return sorted(self.out.glob("*.svg"))

    def provenance(self, path: Path) -> dict:
        root = element_tree.fromstring(path.read_text(encoding="utf-8"))
        metadata = root.find(f"{SVG_NS}metadata")
        self.assertIsNotNone(metadata, f"{path.name} has no provenance block")
        return json.loads(metadata.text or "")

    def document_text(self, path: Path) -> str:
        """Everything a reader sees: every text node outside title, desc and metadata."""
        root = element_tree.fromstring(path.read_text(encoding="utf-8"))
        visible = []
        for node in root.iter():
            tag = node.tag.rsplit("}", 1)[-1]
            if tag in ("title", "desc", "metadata", "style"):
                continue
            if node.text and node.text.strip():
                visible.append(node.text.strip())
            if node.tail and node.tail.strip():
                visible.append(node.tail.strip())
        return " ".join(visible)

    def title_text(self, path: Path) -> str:
        root = element_tree.fromstring(path.read_text(encoding="utf-8"))
        title = root.find(f"{SVG_NS}title")
        self.assertIsNotNone(title)
        return title.text or ""

    # -- geometry read off the picture's own axes, not off the renderer's maths ----

    def panel_box(self, root) -> tuple[float, float, float, float]:
        """The plot box, from the `<rect class="panel">` the renderer drew."""
        for node in root.iter(f"{SVG_NS}rect"):
            if node.get("class") == "panel":
                x, y = float(node.get("x")), float(node.get("y"))
                return x, y, x + float(node.get("width")), y + float(node.get("height"))
        self.fail("the asset has no panel rect")

    @staticmethod
    def _interpolate(ticks: list[tuple[float, float]]):
        """A linear map value -> pixel through the tick marks the asset actually carries."""
        ordered = sorted(ticks)

        def at(value: float) -> float:
            if value <= ordered[0][0]:
                return ordered[0][1]
            for (v0, p0), (v1, p1) in zip(ordered, ordered[1:]):
                if value <= v1:
                    return p0 + (value - v0) * (p1 - p0) / (v1 - v0)
            return ordered[-1][1]

        return at

    @staticmethod
    def _lamports(label: str) -> int:
        whole, rest = label.split(" SOL")[0].split(".")
        return int(whole) * 1_000_000_000 + int(rest) * 10_000_000

    def axes(self, root) -> tuple:
        """`(x_of, y_of)` for one asset, from its tick labels: value -> pixel."""
        x_ticks: list[tuple[float, float]] = []
        y_ticks: list[tuple[float, float]] = []
        for node in root.iter(f"{SVG_NS}text"):
            if node.get("class") != "tick":
                continue
            if node.get("text-anchor") == "middle":
                x_ticks.append((float(node.text or 0), float(node.get("x"))))
            elif node.get("text-anchor") == "end":
                # the label sits 4 px below the grid line it names
                y_ticks.append((self._lamports(node.text or "0.00 SOL"), float(node.get("y")) - 4))
        self.assertGreaterEqual(len(x_ticks), 2, "no x ticks to read a scale from")
        self.assertGreaterEqual(len(y_ticks), 2, "no y ticks to read a scale from")
        return self._interpolate(x_ticks), self._interpolate(y_ticks)

    def cross_centres(self, root, box) -> list[tuple[float, float]]:
        """The centre of every refusal cross inside the plot box (the legend swatch is outside)."""
        centres: list[tuple[float, float]] = []
        for group in root.iter(f"{SVG_NS}g"):
            if group.get("class") != "cross":
                continue
            line = group.find(f"{SVG_NS}line")
            self.assertIsNotNone(line, "a refusal cross with no line in it")
            x1, y1 = float(line.get("x1")), float(line.get("y1"))
            x2, y2 = float(line.get("x2")), float(line.get("y2"))
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            if box[0] <= cx <= box[2] and box[1] <= cy <= box[3]:
                centres.append((cx, cy))
        return sorted(centres)


class TestLabel(ChartTestCase):
    """The label is the deliverable: an asset that loses it is a broken asset."""

    def test_every_asset_carries_the_label_dataset_and_run_id(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        code, stdout, stderr = self.generate(*datasets)
        self.assertEqual(code, 0, stderr)

        assets = self.assets()
        self.assertEqual(len(assets), 5, [path.name for path in assets])
        for path in assets:
            prov = self.provenance(path)
            title = self.title_text(path)
            visible = self.document_text(path)
            with self.subTest(asset=path.name):
                self.assertIn("SYNTHETIC", title)
                self.assertIn("SYNTHETIC", visible)
                self.assertIn(swarm_charts.NOT_EVIDENCE, prov["not_evidence"])
                self.assertIn(swarm_charts.NOT_EVIDENCE, visible)
                self.assertEqual(prov["record"], "swarm-chart")
                self.assertIs(prov["synthetic"], True)
                for entry in prov["datasets"]:
                    self.assertIn(entry["name"], title)
                    self.assertIn(entry["name"], visible)
                for run_id in prov["run_ids"]:
                    self.assertIn(run_id, title)
                    self.assertIn(run_id, visible)

    def test_every_asset_carries_the_not_evidence_sentence_in_its_title(self):
        """Rule 3 asks for the sentence in the title, not a clause of it."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        for path in self.assets():
            with self.subTest(asset=path.name):
                self.assertIn(swarm_charts.NOT_EVIDENCE, self.title_text(path))

    def test_the_banner_and_the_footnote_read_the_label_itself(self):
        """The label has to be in the template, not only inside the dataset's file name."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        for path in self.assets():
            root = element_tree.fromstring(path.read_text(encoding="utf-8"))
            with self.subTest(asset=path.name):
                banner = [node for node in root.iter(f"{SVG_NS}text") if node.get("class") == "banner"]
                self.assertEqual(len(banner), 1, "one banner, at the top of the picture")
                self.assertEqual((banner[0].text or "").strip(), "SYNTHETIC")
                foot = [node for node in root.iter(f"{SVG_NS}text") if node.get("class") == "foot"]
                self.assertEqual(len(foot), 1)
                self.assertTrue((foot[0].text or "").startswith("SYNTHETIC"))

    def test_the_index_lists_every_asset_and_carries_the_sentence(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        index = (self.out / "index.html").read_text(encoding="utf-8")
        self.assertIn("SYNTHETIC", index)
        self.assertIn(swarm_charts.NOT_EVIDENCE, index)
        for path in self.assets():
            self.assertIn(path.name, index)
        manifest = swarm_charts._read_manifest(index)
        self.assertEqual(len(manifest), len(self.assets()))

    def test_generated_svg_parses_as_xml_and_the_animation_is_css_only(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        for path in self.assets():
            with self.subTest(asset=path.name):
                root = element_tree.fromstring(path.read_text(encoding="utf-8"))
                self.assertEqual(root.tag, f"{SVG_NS}svg")
                self.assertEqual(root.get("data-synthetic"), "true")

        animated = (self.out / "ticket-hop.svg").read_text(encoding="utf-8")
        self.assertIn("@keyframes hop", animated)
        self.assertIn("prefers-reduced-motion", animated)
        self.assertNotIn("<script", animated)
        root = element_tree.fromstring(animated)
        self.assertEqual(root.get("data-animation"), "true")

    def test_the_refusal_crosses_land_on_the_refused_rows_own_coordinates(self):
        """Assert the geometry, not the word "refused" that the legend always supplies.

        With `_cross` replaced by a no-op this test fails on a count of zero, and a cross
        drawn at the wrong price fails on a distance: both are the point.
        """
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        target = self.out / "price-path-evt_capped.svg"
        prov = self.provenance(target)
        refused = [
            point for point in prov["series"]["points"] if point["status"] == "refused"
        ]
        self.assertGreater(len(refused), 0, "this fixture is supposed to contain a refusal")
        self.assertGreater(prov["series"]["counts"]["refused"], 0)

        root = element_tree.fromstring(target.read_text(encoding="utf-8"))
        x_of, y_of = self.axes(root)
        centres = self.cross_centres(root, self.panel_box(root))
        self.assertEqual(len(centres), len(refused))

        expected = sorted(
            (x_of(point["round"]), y_of(point["price_lamports"])) for point in refused
        )
        for (want_x, want_y), (got_x, got_y) in zip(expected, centres):
            self.assertAlmostEqual(got_x, want_x, delta=2, msg=f"cross at {got_x} not {want_x}")
            self.assertAlmostEqual(got_y, want_y, delta=2, msg=f"cross at {got_y} not {want_y}")

    def test_a_dry_runs_refusal_is_written_as_something_that_did_not_happen(self):
        """A simulated refusal is what the hook *would* do: nothing was built, signed or sent."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        visible = self.document_text(self.out / "price-path-evt_capped.svg")
        self.assertNotIn("refused by the cap hook", visible)
        self.assertIn("the cap hook would refuse this", visible)
        self.assertIn("nothing was built, signed or sent", visible)
        hop = self.document_text(self.out / "ticket-hop.svg")
        self.assertIn("The hook would refuse it with", hop)
        self.assertNotIn("The hook refuses it", hop)
        self.assertIn("would refuse 6010", hop)

    def test_the_animated_ticket_stops_short_of_the_wall_it_is_refused_at(self):
        """The ticket box is 96 px wide; at closest approach it used to sit 14 px past the wall."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        text = (self.out / "ticket-hop.svg").read_text(encoding="utf-8")
        wall = float(re.search(r'<line class="wall" x1="([-\d.]+)"', text).group(1))
        box = re.search(r'<rect class="ticket" x="([-\d.]+)"[^>]*width="([\d.]+)"', text)
        self.assertIsNotNone(box, "no ticket box to measure")
        left, width = float(box.group(1)), float(box.group(2))
        closest = max(int(value) for value in re.findall(r"translateX\((-?\d+)px\)", text))
        right_edge = left + width + closest
        self.assertLessEqual(right_edge, wall, "the ticket straddles the wall")
        self.assertGreaterEqual(right_edge, wall - 20, "it should still reach the wall")

    def test_the_markup_median_is_labelled_with_its_sample_size(self):
        """Two jagged lines of single trades read as a trend; a mark with n does not."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        prov = self.provenance(self.out / "markup-vs-time-to-event.svg")
        text = (self.out / "markup-vs-time-to-event.svg").read_text(encoding="utf-8")
        samples = [entry[2] for series in prov["series"]["series"] for entry in series["median"]]
        self.assertIn(1, samples, "this fixture should contain a median taken over one trade")
        self.assertEqual(
            sorted(f"n={value}" for value in samples),
            sorted(re.findall(r'class="median-n"[^>]*>(n=\d+)<', text)),
        )
        neighbours = sum(
            1
            for series in prov["series"]["series"]
            for previous, current in zip(series["median"], series["median"][1:])
            if previous[2] >= 2 and current[2] >= 2
        )
        self.assertEqual(text.count('class="median-line"'), neighbours)
        if neighbours == 0:
            self.assertIn("no median line is drawn", self.document_text(
                self.out / "markup-vs-time-to-event.svg"))

    def test_every_class_an_asset_uses_has_a_style_rule(self):
        """`.banner-box` had no rule, so the SYNTHETIC pill rendered SVG's default black."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        for path in self.assets():
            text = path.read_text(encoding="utf-8")
            style = re.search(r"<style>(.*?)</style>", text, re.S)
            self.assertIsNotNone(style, path.name)
            defined = set(re.findall(r"\.([A-Za-z][\w-]*)", style.group(1)))
            used: set[str] = set()
            for value in re.findall(r'class="([^"]+)"', text):
                used.update(value.split())
            with self.subTest(asset=path.name):
                self.assertEqual(sorted(used - defined), [])
                rule = re.search(r"\.banner-box\s*\{([^}]*)\}", style.group(1))
                self.assertIsNotNone(rule, "the banner pill needs a fill of its own")
                self.assertIn("fill: #b8261c", rule.group(1))

    def test_coincident_executed_rows_draw_one_mark_plus_the_count(self):
        """Seven buys at one round and price are seven rows and one dot."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        target = self.out / "price-path-evt_capped.svg"
        prov = self.provenance(target)
        executed = [
            point
            for point in prov["series"]["points"]
            if point["status"] == "ok" and point["action"] in ("buy", "resell")
        ]
        counts: dict[tuple, int] = {}
        for point in executed:
            key = (point["round"], point["price_lamports"])
            counts[key] = counts.get(key, 0) + 1

        text = target.read_text(encoding="utf-8")
        self.assertEqual(
            sorted(int(value) for value in re.findall(r'class="dot-n"[^>]*>x(\d+)<', text)),
            sorted(count for count in counts.values() if count > 1),
        )
        root = element_tree.fromstring(text)
        box = self.panel_box(root)
        dots = [
            node
            for node in root.iter(f"{SVG_NS}circle")
            if node.get("class") == "dot"
            and box[0] <= float(node.get("cx")) <= box[2]
            and box[1] <= float(node.get("cy")) <= box[3]
        ]
        self.assertEqual(len(dots), len(counts), "one mark per distinct point, not per row")


class TestVerifier(ChartTestCase):
    """`verify` has to catch an edit by hand, or it is decoration."""

    def setUp(self) -> None:
        super().setUp()
        datasets = run_dry_swarm(self.tmp / "runs")
        self.dataset = datasets[0]
        self.datasets = datasets
        code, _, stderr = self.generate(*datasets)
        self.assertEqual(code, 0, stderr)

    def test_verify_passes_after_generate_with_the_datasets(self):
        code, stdout, stderr = self.verify(*self.datasets)
        self.assertEqual(code, 0, stderr + stdout)
        self.assertTrue(stdout.startswith("PASS "), stdout)
        self.assertIn("5 asset(s)", stdout)
        self.assertIn("series rebuilt from the dataset and matched on all 5", stdout)

    def test_verify_catches_a_hand_edited_number(self):
        target = self.out / "price-path-evt_capped.svg"
        text = target.read_text(encoding="utf-8")
        self.assertIn("1.25 SOL", text)
        target.write_text(text.replace("1.25 SOL", "9.99 SOL", 1), encoding="utf-8")

        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("price-path-evt_capped.svg", stdout)
        self.assertIn("edited by hand", stdout)

    def test_verify_catches_a_lost_visible_label(self):
        """Strip the word everywhere a reader can see it, leaving the provenance intact.

        The dataset's own file name carries SYNTHETIC (the runner puts it there), so the last
        occurrence a reader sees is inside that name. Removing all of them is the only honest
        way to test the check: an edit that leaves the word in the dataset name has left the
        label on the picture, which is the point of naming the dataset in every asset.
        """
        target = self.out / "ticket-hop.svg"
        text = target.read_text(encoding="utf-8")
        stripped = text.replace(">SYNTHETIC<", "><", 1)
        stripped = stripped.replace("SYNTHETIC - tools/swarm_charts.py", "tools/swarm_charts.py", 1)
        stripped = stripped.replace("-SYNTHETIC.jsonl", "-.jsonl")
        self.assertNotIn(">SYNTHETIC<", stripped)
        target.write_text(stripped, encoding="utf-8")

        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("SYNTHETIC is missing from the visible text", stdout)

    def test_verify_catches_a_lost_title(self):
        target = self.out / "hops-and-holding.svg"
        text = target.read_text(encoding="utf-8")
        start = text.index("<title")
        end = text.index("</title>", start) + len("</title>")
        target.write_text(text[:start] + text[end:], encoding="utf-8")

        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("no <title> element", stdout)

    def test_verify_catches_a_doctored_series_re_rendered_with_a_fresh_digest(self):
        """The review's mutation 5: doctor a value, recompute the digest, re-render, verify.

        Every check that compares the file with its own provenance passes here, because the
        file *is* what the tool renders from the doctored block. Only rebuilding the series
        from the dataset catches it, which is the whole point of that check.
        """
        target = self.out / "price-path-evt_capped.svg"
        root = element_tree.fromstring(target.read_text(encoding="utf-8"))
        prov = json.loads(root.find(f"{SVG_NS}metadata").text or "")
        kept = prov["series"]["points"][0]["price_lamports"]
        prov["series"]["points"][0]["price_lamports"] = FACE * 3
        prov["data_sha256"] = swarm_charts._data_digest(prov["series"])
        target.write_text(swarm_charts.render_asset(prov), encoding="utf-8")

        code, stdout, _ = self.verify(*self.datasets)
        self.assertEqual(code, 2, stdout)
        self.assertIn("not of that file's data", stdout)
        self.assertIn(f"points[0].price_lamports is {FACE * 3}, not {kept}", stdout)
        self.assertNotIn("edited by hand", stdout)

    def test_verify_catches_a_doctored_series_even_with_a_fresh_digest(self):
        target = self.out / "price-path-evt_capped.svg"
        root = element_tree.fromstring(target.read_text(encoding="utf-8"))
        metadata = root.find(f"{SVG_NS}metadata")
        prov = json.loads(metadata.text or "")
        prov["series"]["points"][0]["price_lamports"] = FACE * 3
        prov["data_sha256"] = swarm_charts._data_digest(prov["series"])
        text = target.read_text(encoding="utf-8")
        metadata_text = json.dumps(prov, indent=1, sort_keys=True, ensure_ascii=False)
        target.write_text(
            text.replace(metadata.text or "", swarm_charts._esc(metadata_text), 1), encoding="utf-8"
        )

        code, stdout, _ = self.verify(*self.datasets)
        self.assertEqual(code, 2)
        self.assertIn("not what this tool renders", stdout)

    def test_verify_catches_a_series_whose_digest_no_longer_matches(self):
        target = self.out / "price-path-evt_capped.svg"
        text = target.read_text(encoding="utf-8")
        root = element_tree.fromstring(text)
        metadata = root.find(f"{SVG_NS}metadata")
        prov = json.loads(metadata.text or "")
        prov["series"]["points"][0]["price_lamports"] = FACE * 3
        doctored = swarm_charts._esc(json.dumps(prov, indent=1, sort_keys=True, ensure_ascii=False))
        target.write_text(text.replace(swarm_charts._esc(metadata.text or ""), doctored, 1),
                          encoding="utf-8")

        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("sha256 of the series", stdout)

    def test_verify_reports_a_dataset_whose_digest_changed(self):
        original = self.dataset.read_text(encoding="utf-8")
        self.dataset.write_text(original + "\n", encoding="utf-8")
        code, stdout, _ = self.verify(self.dataset)
        self.assertEqual(code, 2)
        self.assertIn("digest", stdout.lower())
        self.assertIn("not of that file", stdout)

    def test_verify_without_the_dataset_says_it_did_not_recheck_it(self):
        """Nothing was checked against data, so it must not claim a pass or exit 0."""
        code, stdout, _ = self.verify()
        self.assertEqual(code, 3)
        self.assertTrue(stdout.startswith("PASS LABELS ONLY"), stdout)
        self.assertIn("0 re-checked against the file", stdout)
        self.assertIn("2 not present", stdout)
        self.assertIn("series rebuilt from the dataset on 0 of 5", stdout)
        self.assertIn("nothing about the data was checked", stdout)

    def test_verify_catches_an_index_digest_no_asset_has(self):
        """Re-rendering the index from its own manifest proves nothing about the assets."""
        index_path = self.out / "index.html"
        manifest = swarm_charts._read_manifest(index_path.read_text(encoding="utf-8"))
        manifest[0]["datasets"][0]["sha256"] = "0" * 64
        index_path.write_text(swarm_charts.render_index(manifest), encoding="utf-8")

        code, stdout, _ = self.verify(*self.datasets)
        self.assertEqual(code, 2, stdout)
        self.assertIn("is not the provenance that asset carries", stdout)
        self.assertIn("datasets[0].sha256", stdout)
        self.assertIn("0000000000000000", stdout)

    def test_verify_catches_a_title_without_the_not_evidence_sentence(self):
        target = self.out / "hops-and-holding.svg"
        text = target.read_text(encoding="utf-8")
        title = re.search(r"<title id=\"chart-title\">.*?</title>", text, re.S).group(0)
        chopped = title.replace(
            swarm_charts.NOT_EVIDENCE, "not evidence about any real ticket market"
        )
        target.write_text(text.replace(title, chopped, 1), encoding="utf-8")

        code, stdout, _ = self.verify(*self.datasets)
        self.assertEqual(code, 2)
        self.assertIn("missing from the <title> element", stdout)

    def test_verify_catches_a_missing_index(self):
        (self.out / "index.html").unlink()
        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("index is missing", stdout)

    def test_verify_catches_an_svg_the_index_does_not_list(self):
        shutil.copy(self.out / "ticket-hop.svg", self.out / "extra.svg")
        code, stdout, _ = self.verify()
        self.assertEqual(code, 2)
        self.assertIn("extra.svg", stdout)


class TestRefusals(ChartTestCase):
    """What the tool will not draw from, and the one thing it allows."""

    def test_an_incomplete_dataset_is_refused(self):
        dataset = write_dataset(self.tmp, sample_rows(), complete=False)
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", stderr)
        self.assertIn("complete is False", stderr)
        self.assertFalse(self.out.exists() and list(self.out.glob("*.svg")))

    def test_a_dataset_with_no_sidecar_is_refused(self):
        dataset = write_dataset(self.tmp, sample_rows())
        dataset.with_suffix(".meta.json").unlink()
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("no sidecar", stderr)
        self.assertFalse(self.out.exists() and list(self.out.glob("*.svg")))

    def test_a_sidecar_that_disagrees_with_the_dataset_is_refused(self):
        dataset = write_dataset(self.tmp, sample_rows(), sidecar_overrides={"run_id": "somebody-else"})
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("not one artefact", stderr)

    def test_a_sidecar_that_is_not_labelled_synthetic_is_refused(self):
        dataset = write_dataset(self.tmp, sample_rows(), sidecar_overrides={"synthetic": False})
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("synthetic", stderr)

    def test_a_dry_run_is_allowed_and_labelled(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        code, _, stderr = self.generate(*datasets)
        self.assertEqual(code, 0, stderr)
        for path in self.assets():
            with self.subTest(asset=path.name):
                prov = self.provenance(path)
                self.assertTrue(all(entry["dry_run"] is True for entry in prov["datasets"]))
                self.assertIn("DRY RUN", self.document_text(path))

                # The docstring says the banner *and* the footer; check the second one.
                nodes = list(element_tree.fromstring(path.read_text(encoding="utf-8")).iter())
                evidence_at = max(
                    index
                    for index, node in enumerate(nodes)
                    if node.get("class") == "caption"
                    and (node.text or "").startswith("This picture is not evidence")
                )
                self.assertTrue(
                    [
                        node
                        for index, node in enumerate(nodes)
                        if index > evidence_at
                        and node.get("class") == "dry"
                        and "DRY RUN" in (node.text or "")
                    ],
                    "the footer below the not-evidence sentence carries no DRY RUN marker",
                )

    def test_a_live_runs_refusal_keeps_the_plain_past_tense(self):
        """The dry-run branch must not have replaced the live wording with itself."""
        dataset = write_dataset(self.tmp, sample_rows(), dry_run=False)
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 0, stderr)
        visible = self.document_text(self.out / "price-path-evt_capped.svg")
        self.assertIn("refused by the cap hook (6010 CapExceeded)", visible)
        self.assertNotIn("would refuse", visible)
        hop = self.document_text(self.out / "ticket-hop.svg")
        self.assertIn("The hook refuses it with", hop)
        self.assertNotIn("would refuse", hop)
        for path in self.assets():
            self.assertNotIn("DRY RUN", self.document_text(path))

    def test_a_dataset_whose_rows_lack_the_label_is_refused(self):
        dataset = write_dataset(self.tmp, sample_rows())
        lines = dataset.read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[1])
        row["synthetic"] = False
        lines[1] = json.dumps(row)
        dataset.write_text("\n".join(lines) + "\n", encoding="utf-8")
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("fails its own verifier", stderr)
        self.assertIn("synthetic must be true", stderr)


class TestBrokenPrices(ChartTestCase):
    """A price that is not an integer must not take the chart down with it."""

    def test_a_float_price_that_passes_verification_is_counted_not_drawn(self):
        rows = sample_rows() + [
            _row(
                action="list",
                agent_id="h1",
                from_wallet=None,
                to_wallet=None,
                ticket_id="evt_capped#0004",
                price_lamports=1.5,
                markup_bps=None,
                hop_index=1,
                round=4,
                rounds_left=0,
            )
        ]
        dataset = write_dataset(self.tmp, rows)
        # The verifier accepts it: a listing's price is not checked for integer-ness, which
        # is exactly why the chart has to defend itself.
        swarm_charts._DATASETS.verify_dataset(dataset)

        code, stdout, stderr = self.generate(dataset)
        self.assertEqual(code, 0, stderr)
        prov = self.provenance(self.out / "price-path-evt_capped.svg")
        self.assertEqual(prov["series"]["unplottable_rows"], 1)
        self.assertIn("no usable integer price", self.document_text(self.out / "price-path-evt_capped.svg"))
        for path in self.assets():
            element_tree.fromstring(path.read_text(encoding="utf-8"))

    def test_a_broken_price_the_verifier_rejects_is_a_clean_refusal(self):
        rows = sample_rows()
        rows.append(
            _row(
                action="resell",
                agent_id="s1",
                from_wallet="s1",
                to_wallet="f1",
                ticket_id="evt_capped#0005",
                price_lamports="not-a-number",
                markup_bps=0,
                status="refused",
                error_code=6010,
                hop_index=None,
                round=4,
                rounds_left=0,
            )
        )
        dataset = write_dataset(self.tmp, rows)
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 2)
        self.assertIn("REFUSED", stderr)
        self.assertIn("fails its own verifier", stderr)
        self.assertNotIn("Traceback", stderr)
        self.assertFalse(self.out.exists() and list(self.out.glob("*.svg")))

    def test_a_listing_with_no_price_is_skipped_without_raising(self):
        series = swarm_charts.price_path_series(
            type(
                "Dataset",
                (),
                {
                    "facts": {
                        "event_id": "e",
                        "mode": "capped",
                        "face_lamports": FACE,
                        "cap_bps": CAP_BPS,
                        "ceiling_lamports": CEILING,
                        "rounds": 4,
                    },
                    "rows": (
                        {"seq": 1, "action": "list", "status": "ok", "price_lamports": None,
                         "round": 1},
                        {"seq": 2, "action": "buy", "status": "ok", "price_lamports": True,
                         "round": 1},
                    ),
                },
            )()
        )
        self.assertEqual(series["points"], [])
        self.assertGreaterEqual(series["unplottable_rows"], 1)


class TestMedianLine(ChartTestCase):
    """The median line joins only where two executed resales share a point on the horizon."""

    def _resales(self, pairs: list[tuple[int, int]]) -> list[TradeRow]:
        return [
            _row(
                action="resell",
                agent_id="s1",
                from_wallet="s1",
                to_wallet="g1",
                ticket_id=f"evt_capped#{index:04d}",
                price_lamports=price,
                markup_bps=_markup(price),
                hop_index=2,
                round=index,
                rounds_left=rounds_left,
            )
            for index, (rounds_left, price) in enumerate(pairs, start=1)
        ]

    def test_two_neighbouring_points_with_two_trades_each_get_one_segment(self):
        rows = self._resales(
            [(2, 1_100_000_000), (2, 1_200_000_000), (3, 1_150_000_000), (3, 1_300_000_000)]
        )
        dataset = write_dataset(self.tmp, rows)
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 0, stderr)
        prov = self.provenance(self.out / "markup-vs-time-to-event.svg")
        medians = prov["series"]["series"][0]["median"]
        self.assertEqual([entry[2] for entry in medians], [2, 2])
        text = (self.out / "markup-vs-time-to-event.svg").read_text(encoding="utf-8")
        self.assertEqual(text.count('class="median-line"'), 1)
        self.assertIn(
            "1 neighbouring pair(s) have n >= 2",
            self.document_text(self.out / "markup-vs-time-to-event.svg"),
        )

    def test_a_point_with_one_trade_is_never_joined_to_its_neighbour(self):
        rows = self._resales(
            [(2, 1_100_000_000), (2, 1_200_000_000), (3, 1_150_000_000)]
        )
        dataset = write_dataset(self.tmp, rows)
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 0, stderr)
        prov = self.provenance(self.out / "markup-vs-time-to-event.svg")
        self.assertEqual([entry[2] for entry in prov["series"]["series"][0]["median"]], [2, 1])
        text = (self.out / "markup-vs-time-to-event.svg").read_text(encoding="utf-8")
        self.assertEqual(text.count('class="median-line"'), 0)
        self.assertIn("no median line is drawn", self.document_text(
            self.out / "markup-vs-time-to-event.svg"))


class TestSingleDataset(ChartTestCase):
    """One dataset is a legitimate input, and the comparison chart says what it cannot do."""

    def test_markup_chart_says_there_is_no_second_series(self):
        dataset = write_dataset(self.tmp, sample_rows())
        code, _, stderr = self.generate(dataset)
        self.assertEqual(code, 0, stderr)
        prov = self.provenance(self.out / "markup-vs-time-to-event.svg")
        self.assertEqual(len(prov["series"]["series"]), 1)
        self.assertIn("no second mode to compare", self.document_text(
            self.out / "markup-vs-time-to-event.svg"))

    def test_a_stale_asset_from_an_earlier_generation_is_removed(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        self.assertEqual(len(self.assets()), 5)
        self.assertEqual(self.generate(datasets[0])[0], 0)
        names = [path.name for path in self.assets()]
        self.assertEqual(len(names), 4, names)
        self.assertNotIn("price-path-evt_monitored.svg", names)
        code, stdout, _ = self.verify(datasets[0])
        self.assertEqual(code, 0, stdout)


class TestCommandLine(ChartTestCase):
    """The tool as an operator runs it: a subprocess, a real exit code, a real file."""

    def test_generate_and_verify_from_the_command_line(self):
        datasets = run_dry_swarm(self.tmp / "runs")
        command = [sys.executable, str(CLI), "generate", "--out", str(self.out)]
        for dataset in datasets:
            command += ["--dataset", str(dataset)]
        done = subprocess.run(
            command, cwd=REPO_ROOT, capture_output=True, text=True, timeout=120, check=False
        )
        self.assertEqual(done.returncode, 0, done.stderr)
        self.assertIn("label     SYNTHETIC", done.stdout)
        self.assertIn("index.html", done.stdout)

        checked = subprocess.run(
            [sys.executable, str(CLI), "verify", "--out", str(self.out)]
            + [part for dataset in datasets for part in ("--dataset", str(dataset))],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(checked.returncode, 0, checked.stderr + checked.stdout)
        self.assertIn("PASS ", checked.stdout)
        self.assertIn("series rebuilt from the dataset", checked.stdout)

        labels_only = subprocess.run(
            [sys.executable, str(CLI), "verify", "--out", str(self.out)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(labels_only.returncode, 3, labels_only.stderr + labels_only.stdout)
        self.assertIn("PASS LABELS ONLY", labels_only.stdout)

    def test_two_generations_of_the_same_data_differ_only_in_the_timestamp(self):
        """Determinism, stated as a test: the only wall-clock value is `generated_at`."""
        datasets = run_dry_swarm(self.tmp / "runs")
        self.assertEqual(self.generate(*datasets)[0], 0)
        second = self.tmp / "charts-again"
        code, _, stderr = self.generate_into(second, *datasets)
        self.assertEqual(code, 0, stderr)

        first_files = {path.name: path.read_text(encoding="utf-8") for path in self.out.iterdir()}
        second_files = {path.name: path.read_text(encoding="utf-8") for path in second.iterdir()}
        self.assertEqual(sorted(first_files), sorted(second_files))

        stamp = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")
        for name in first_files:
            with self.subTest(file=name):
                self.assertEqual(
                    stamp.sub("<generated_at>", first_files[name]),
                    stamp.sub("<generated_at>", second_files[name]),
                )
        self.assertRegex(first_files["ticket-hop.svg"], stamp)

    def test_the_command_line_refuses_an_incomplete_dataset(self):
        dataset = write_dataset(self.tmp, sample_rows(), complete=False)
        done = subprocess.run(
            [sys.executable, str(CLI), "generate", "--dataset", str(dataset), "--out", str(self.out)],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        self.assertEqual(done.returncode, 2)
        self.assertIn("REFUSED", done.stderr)
        self.assertNotIn("Traceback", done.stderr)


if __name__ == "__main__":
    unittest.main()

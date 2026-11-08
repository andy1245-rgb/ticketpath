"""Chart and animation assets drawn from a `market_swarm` dataset, and a verifier for them.

    python3 tools/swarm_charts.py generate --dataset <path.jsonl> [--dataset ...] --out docs/charts
    python3 tools/swarm_charts.py verify   --out docs/charts [--dataset <path.jsonl> ...]

Standard library only. No network, no chain, no third-party plotting, no binaries: every
asset is hand-written SVG text or one HTML page, so it diffs in a review.

## What it reads, and what it does not re-implement

A `.jsonl` dataset the runner wrote, plus the `.meta.json` sidecar the runner writes beside
it. The dataset is checked with `market_swarm.datasets.verify_dataset` -- the same verifier
the CLI's `verify-dataset` verb calls -- before a single row is read for plotting, so this
module owns no copy of the row schema. The sidecar is read for the three facts a dataset
file cannot state about itself: `complete`, `dry_run`, and the config's `cluster`.

## The rule this tool inherits, and enforces without trusting the writer

Every number a `market_swarm` run produces is class E: synthetic, and not evidence about any
real market (`records/findings/31`, "Why it exists" and "What it is not"). So each asset
carries, in its visible text *and* inside its own `<title>` element, the word SYNTHETIC, the
dataset file name, the run id, and one sentence saying what the picture is not. A reader who
saves one image cannot mistake it, and `verify` re-checks those four facts instead of
trusting the code that wrote them.

## Two refusals, and the one thing it allows

The brief asked for this choice to be stated here rather than left implicit.

- **A dataset whose sidecar says `complete: false` is refused.** A run that stopped early has
  a price path that ends in the middle of its horizon, and a chart of it would present a
  truncated path as the whole one. There is no way for a picture to carry "this is half a
  run" honestly enough, so it is not drawn.
- **A dataset with no sidecar is refused** for the same reason: without one there is nothing
  saying the run finished, and every run in `.swarm-runs/` was started by something.
- **A dry run is allowed, and labelled.** `dry_run: true` means a `DryRunGateway` "would
  have" done each thing: no transaction was built, signed or sent, and every row's `chain`
  is `simulated`. That is not a defect to hide -- the scripted policies are the default path
  for a dataset, so most runs are dry runs, and refusing them would mean charting nothing.
  So the asset says **DRY RUN** in its banner and in its footer, the provenance records
  `dry_run: true`, and the caption says what the word means. A live run is charted the same
  way with the word absent; nothing else about the two paths differs.

  The prose branches on the flag as well, because a dry run's refusal is not a refusal that
  happened. Nothing is built, signed or sent: a dry row says the hook *would* refuse it and
  that no unit moved (`records/findings/31`, H1 -- the same defect `market_swarm` fixed in
  its own rationale strings). A live run keeps the plain past tense.

Two more refusals come out of the same principle: a dataset whose header and sidecar disagree
about `run_id`, `event_id`, `dry_run` or `chain` is refused (the pair is one artefact or it
is not provenance), and a dataset carrying rows for more than one event is refused.

## What `verify` proves, and what it does not

Rendering is a pure function of the provenance block embedded in each asset: no clock, no
random, no font metrics. So `verify` re-renders the asset from its own provenance and
compares bytes, which catches any hand edit to the file -- a changed number, a dropped
label, an added sentence. On its own that proves the file agrees with the block it carries,
and nothing about whether the block agrees with the data. A doctored series with a
recomputed `data_sha256`, re-rendered, would pass it.

So, when the dataset can be located (beside the assets, or passed with `--dataset`), `verify`
re-loads it and **rebuilds the series from it with the same functions `generate` used**, then
compares that series with the one in the provenance. "The digest matches" and "the series
rebuilds to the same bytes" together mean the picture is of that file's data. When the
dataset cannot be located, `verify` does not rebuild anything, says so once per dataset, and
exits **3** with `PASS LABELS ONLY` rather than claiming a pass: on a fresh clone with no
`.swarm-runs/`, the labels and the internal consistency are checked and the numbers are not.

The dataset's own sha256 is re-hashed on the same locating step, so a file that changed
under a picture is named. Narrower checks run first, so a failure names the problem instead
of saying "the bytes differ": the label and the not-evidence sentence are in the title and
in the visible text, the dataset file name and run id are present in both, the sha256 of the
embedded series matches, the series rebuilt from the dataset matches the recorded one, and
each manifest entry in the index is compared with the provenance of the asset it names.
Assets record the dataset's file name and digest and never its absolute path.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape as _sax_escape

REPO_ROOT = Path(__file__).resolve().parents[1]

GENERATOR = "tools/swarm_charts.py"
GENERATOR_VERSION = 2

#: The word every asset has to carry, in its text and in its title.
LABEL = "SYNTHETIC"

#: One sentence, the same in every asset, that says what the picture is not.
NOT_EVIDENCE = (
    "This picture is not evidence about any real ticket market: it is synthetic "
    "simulation output from scripted agents, not observed prices."
)

#: The provenance record name, so `verify` can tell this tool's SVG from anyone else's.
RECORD = "swarm-chart"

#: `<pre id="manifest">` in the index carries the manifest JSON; `verify` reads it back.
MANIFEST_OPEN = '<pre id="manifest">'
MANIFEST_CLOSE = '</pre>'

INDEX_NAME = "index.html"

LAMPORTS_PER_SOL = 1_000_000_000
BPS_DENOMINATOR = 10_000

SVG_NS = "http://www.w3.org/2000/svg"
WIDTH = 980

INK = "#16202b"
MUTED = "#5c6b7a"
FAINT = "#8a97a3"
GRID = "#dfe5ea"
RULE = "#c9d2da"
BANNER = "#b8261c"
PAPER = "#ffffff"
EXECUTED = "#1b6ca8"
REFUSED = "#c0392b"
UNMET = "#8a97a3"
FACE = "#2e7d5b"
CEILING = "#b5651d"
MODE_COLOURS = {"capped": "#7b3fa0", "monitored": "#0f7b6c"}
FALLBACK_COLOURS = ("#7b3fa0", "#0f7b6c", "#1b6ca8", "#b5651d")


class ChartError(RuntimeError):
    """Something this tool will not draw from, or will not pass. One message, no traceback."""


# --------------------------------------------------------------------------- helpers


def _esc(text: object) -> str:
    """Escape element text. Quotes are not escaped: they are legal in a text node."""
    return _sax_escape(str(text), {})


def _attr(text: object) -> str:
    return _sax_escape(str(text), {'"': "&quot;"})


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(payload: object) -> str:
    """The one JSON spelling used for a digest, so two runs agree byte for byte."""
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _data_digest(series: object) -> str:
    return _sha256(_canonical(series).encode("utf-8"))


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _int(value: object) -> int | None:
    """A real integer, or None. `bool` is an `int` in Python and must not pass."""
    return value if _is_int(value) else None


def _sol(lamports: int) -> str:
    """Lamports as SOL with two decimals, from integer arithmetic only."""
    sign = "-" if lamports < 0 else ""
    value = abs(int(lamports))
    whole, rest = divmod(value, LAMPORTS_PER_SOL)
    hundredths = rest * 100 // LAMPORTS_PER_SOL
    return f"{sign}{whole}.{hundredths:02d} SOL"


def _pct(bps: int) -> str:
    """Basis points as a signed percentage with two decimals, integer arithmetic only."""
    sign = "-" if bps < 0 else "+"
    value = abs(int(bps))
    whole, rest = divmod(value, 100)
    return f"{sign}{whole}.{rest:02d}%"


def _short(label: object, width: int = 16) -> str:
    """A wallet label or address, short enough for a chart and never a key."""
    text = str(label) if label else "?"
    return text if len(text) <= width else text[: width - 2] + ".."


def _wrap(text: str, width: int) -> list[str]:
    """Greedy word wrap to a character width. No font metrics, so the count is a choice."""
    words = str(text).split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > width:
            lines.append(current)
            current = word
        else:
            current = candidate
    if current:
        lines.append(current)
    return lines or [""]


def _safe_name(text: str) -> str:
    """A file name from an identifier: no separator, no traversal, no surprise."""
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(text)).strip("._")
    return cleaned or "unnamed"


# --------------------------------------------------------------------------- loading


@dataclass(frozen=True)
class Dataset:
    """One verified dataset: its file identity, the facts about it, and its rows."""

    path: Path
    name: str
    digest: str
    size: int
    facts: dict
    header: dict
    rows: tuple[dict, ...]


def _dataset_api():
    """`market_swarm.datasets`, imported from the repo root whatever the cwd is."""
    root = str(REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    from market_swarm import datasets as module

    return module


_DATASETS = _dataset_api()


def _read_json(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ChartError(f"{path.name}: cannot read: {exc.strerror}") from exc
    except json.JSONDecodeError as exc:
        raise ChartError(f"{path.name}: not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, dict):
        raise ChartError(f"{path.name}: expected a JSON object, got {type(payload).__name__}")
    return payload


def _dir_hint(path: Path) -> str | None:
    """The dataset's directory when it is inside this repository, else None.

    Assets carry no absolute path: a home directory in a published file is the operator's
    machine layout, and the file name plus the digest is what pins a dataset anyway.
    """
    try:
        relative = path.resolve().relative_to(REPO_ROOT)
    except (OSError, ValueError):
        return None
    parent = relative.parent.as_posix()
    return None if parent in ("", ".") else parent


def load_dataset(path: Path) -> Dataset:
    """Verify a dataset and its sidecar, then expose its rows. Raises `ChartError`."""
    source = Path(path).expanduser()
    if not source.is_file():
        raise ChartError(
            f"{source}: no such file. `generate` reads a .jsonl dataset the runner wrote."
        )
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise ChartError(f"{source.name}: cannot read: {exc.strerror}") from exc
    digest = _sha256(raw)
    size = len(raw)

    sidecar_path = source.with_suffix(".meta.json")
    if not sidecar_path.is_file():
        raise ChartError(
            f"{source.name}: no sidecar {sidecar_path.name} beside it. Without one there is "
            "nothing saying the run finished, and nothing is drawn from an unfinished run."
        )
    sidecar = _read_json(sidecar_path)

    if sidecar.get("record") != "meta":
        raise ChartError(
            f"{sidecar_path.name}: record is {sidecar.get('record')!r}, not 'meta'"
        )
    if sidecar.get("synthetic") is not True:
        raise ChartError(
            f"{sidecar_path.name}: synthetic is {sidecar.get('synthetic')!r}, not true. "
            "Nothing this tool writes may carry a dataset that is not labelled synthetic."
        )
    label = sidecar.get("label")
    if not isinstance(label, str) or not label.startswith("SYNTHETIC DATA"):
        raise ChartError(
            f"{sidecar_path.name}: label is {label!r}; it must start 'SYNTHETIC DATA'"
        )
    if sidecar.get("complete") is not True:
        raise ChartError(
            f"{sidecar_path.name}: complete is {sidecar.get('complete')!r}. A run that did "
            "not finish cannot be charted: the picture would present a truncated price path "
            "as if it were the whole one."
        )

    try:
        summary = _DATASETS.verify_dataset(source)
    except _DATASETS.DatasetInvalid as exc:
        violations = "\n    ".join(exc.violations)
        raise ChartError(
            f"{source.name}: the dataset fails its own verifier, so nothing is drawn from "
            f"it:\n    {violations}"
        ) from exc

    records: list[dict] = []
    for number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:  # verify_dataset rejected this already
            raise ChartError(f"{source.name} line {number}: not valid JSON: {exc.msg}") from exc
        records.append(record)
    if not records:
        raise ChartError(f"{source.name}: no header record")
    header, rows = records[0], records[1:]

    for field in ("run_id", "event_id"):
        if header.get(field) != sidecar.get(field):
            raise ChartError(
                f"{source.name}: header {field} is {header.get(field)!r} but "
                f"{sidecar_path.name} says {sidecar.get(field)!r}. A dataset and a sidecar "
                "that disagree are not one artefact, so this pair is refused."
            )
    if bool(header.get("dry_run")) != bool(sidecar.get("dry_run")):
        raise ChartError(
            f"{source.name}: header dry_run is {header.get('dry_run')!r} but the sidecar says "
            f"{sidecar.get('dry_run')!r}; one of them was relabelled."
        )
    dry_run = sidecar.get("dry_run") is True
    if dry_run and header.get("cluster") != "simulated":
        raise ChartError(
            f"{source.name}: a dry run's header must carry cluster='simulated', got "
            f"{header.get('cluster')!r}. Rows from a simulated gateway may not read as "
            "observations."
        )
    if not dry_run and header.get("cluster") == "simulated":
        raise ChartError(
            f"{source.name}: the header says cluster='simulated' but the sidecar says this "
            "was not a dry run."
        )

    event_ids = sorted({str(row.get("event_id")) for row in rows})
    run_ids = sorted({str(row.get("run_id")) for row in rows})
    if len(event_ids) > 1:
        raise ChartError(
            f"{source.name}: rows from more than one event ({', '.join(event_ids)}). One "
            "asset draws one event; pass the datasets separately."
        )
    if run_ids and run_ids != [str(header.get("run_id"))]:
        raise ChartError(
            f"{source.name}: rows carry run id(s) {', '.join(run_ids)} but the header says "
            f"{header.get('run_id')!r}"
        )
    if _int(summary.get("rows")) != len(rows):
        raise ChartError(
            f"{source.name}: the verifier counted {summary.get('rows')} row(s) and this "
            f"reader found {len(rows)}"
        )

    face = _int(sidecar.get("face_lamports"))
    cap = _int(sidecar.get("cap_bps"))
    ceiling = _int(sidecar.get("ceiling_lamports"))
    rounds = _int(sidecar.get("rounds"))
    facts = {
        "name": source.name,
        "dir": _dir_hint(source),
        "sha256": digest,
        "bytes": size,
        "run_id": str(header.get("run_id")),
        "event_id": str(header.get("event_id")),
        "mode": str(sidecar.get("mode") or header.get("mode")),
        "dry_run": dry_run,
        "cluster": str(sidecar.get("cluster")),
        "rows": len(rows),
        "face_lamports": face,
        "cap_bps": cap,
        "ceiling_lamports": ceiling,
        "rounds": rounds,
    }
    return Dataset(
        path=source,
        name=source.name,
        digest=digest,
        size=size,
        facts=facts,
        header=header,
        rows=tuple(rows),
    )


def _find_dataset(name: str, hint: str | None, extra: dict[str, Path]) -> Path | None:
    """Locate a dataset named by an asset, without ever reading an absolute path from it.

    The name and the hint come out of the asset's own provenance block, which is the part of
    an SVG a hand edit rewrites first, so both branches resolve the path and then refuse it
    unless it is inside this repository. A name with `..` in it is a name, not a way out.
    """
    if name in extra:
        return extra[name]
    if hint:
        candidate = (REPO_ROOT / hint / name).resolve()
    else:
        candidate = (REPO_ROOT / name).resolve()
    try:
        candidate.relative_to(REPO_ROOT)  # a recorded hint never leaves the repo
    except ValueError:
        return None
    return candidate if candidate.is_file() else None


def _base(rel: Path) -> str:
    return rel.as_posix()


# --------------------------------------------------------------------------- series


def _resale_points(dataset: Dataset) -> tuple[list[dict], int]:
    """Every resale attempt with a usable price and markup, plus the unplottable count.

    A price that is not a non-negative integer (a float, a bool, a string, a negative) is
    not drawn and is counted instead of raising: a dataset that slipped past the verifier
    must not take the chart down with it.
    """
    points: list[dict] = []
    unusable = 0
    for row in dataset.rows:
        if row.get("action") != "resell":
            continue
        price = _int(row.get("price_lamports"))
        markup = _int(row.get("markup_bps"))
        rounds_left = _int(row.get("rounds_left"))
        status = row.get("status")
        if price is None or price < 0 or markup is None or rounds_left is None:
            unusable += 1
            continue
        if status not in ("ok", "refused", "skipped"):
            unusable += 1
            continue
        points.append(
            {
                "seq": _int(row.get("seq")) or 0,
                "rounds_left": rounds_left,
                "price_lamports": price,
                "markup_bps": markup,
                "status": status,
                "agent_id": _short(row.get("agent_id")),
            }
        )
    points.sort(key=lambda point: (point["rounds_left"], point["seq"]))
    return points, unusable


def _median(values: list[int]) -> int:
    """Nearest-rank median on integers: one of the values that occurred, never an average."""
    ordered = sorted(values)
    count = len(ordered)
    rank = (50 * count + 99) // 100
    return ordered[min(max(rank - 1, 0), count - 1)]


def price_path_series(dataset: Dataset) -> dict:
    """The price path: every priced trade or ask in seq order, split by what happened to it.

    A skipped *buy* is a limit bid nobody met, so it is not a price on the path and is
    counted instead of drawn: a chart that mixed bids with asks would read as a price
    history that never happened.
    """
    points: list[dict] = []
    unusable = 0
    unmet_bids = 0
    counts = {"executed": 0, "listings": 0, "refused": 0, "unmet_asks": 0}
    for row in dataset.rows:
        price = _int(row.get("price_lamports"))
        if price is None or price < 0:
            unusable += 1
            continue
        status = row.get("status")
        action = row.get("action")
        if status not in ("ok", "refused", "skipped") or action not in ("buy", "resell", "list"):
            unusable += 1
            continue
        if action == "buy" and status == "skipped":
            unmet_bids += 1
            continue
        if status == "ok" and action in ("buy", "resell"):
            counts["executed"] += 1
        elif status == "ok":
            counts["listings"] += 1
        elif status == "refused":
            counts["refused"] += 1
        else:
            counts["unmet_asks"] += 1
        points.append(
            {
                "seq": _int(row.get("seq")) or 0,
                "round": _int(row.get("round")),
                "price_lamports": price,
                "status": status,
                "action": action,
                "agent_id": _short(row.get("agent_id")),
                "hop_index": _int(row.get("hop_index")),
            }
        )
    points.sort(key=lambda point: point["seq"])
    by_round = all(point["round"] is not None for point in points)
    return {
        "event_id": dataset.facts["event_id"],
        "mode": dataset.facts["mode"],
        "face_lamports": dataset.facts["face_lamports"],
        "cap_bps": dataset.facts["cap_bps"],
        "ceiling_lamports": dataset.facts["ceiling_lamports"],
        "rounds": dataset.facts["rounds"],
        "x_axis": "round" if by_round else "seq",
        "points": points,
        "counts": counts,
        "unmet_bid_rows": unmet_bids,
        "unplottable_rows": unusable,
    }


def markup_series(datasets: list[Dataset]) -> dict:
    """Markup against time-to-event, one series per dataset (so, per mode)."""
    series: list[dict] = []
    unusable = 0
    for dataset in datasets:
        points, skipped_rows = _resale_points(dataset)
        unusable += skipped_rows
        # The median line follows what actually cleared: a refused ask never became a
        # price, so mixing it into the median would plot a price nobody paid.
        medians: dict[int, list[int]] = {}
        for point in points:
            if point["status"] == "ok":
                medians.setdefault(point["rounds_left"], []).append(point["markup_bps"])
        series.append(
            {
                "mode": dataset.facts["mode"],
                "dataset_name": dataset.name,
                "run_id": dataset.facts["run_id"],
                "points": points,
                "median": [
                    [rounds_left, _median(values), len(values)]
                    for rounds_left, values in sorted(medians.items())
                ],
                "counts": {
                    "ok": sum(1 for point in points if point["status"] == "ok"),
                    "refused": sum(1 for point in points if point["status"] == "refused"),
                    "skipped": sum(1 for point in points if point["status"] == "skipped"),
                },
            }
        )
    series.sort(key=lambda entry: entry["mode"])
    horizon = max((dataset.facts["rounds"] or 1 for dataset in datasets), default=1)
    return {"series": series, "rounds": horizon, "unplottable_rows": unusable}


def hops_and_holding_series(datasets: list[Dataset]) -> dict:
    """Hops per ticket and holding duration in rounds, one bar group per dataset."""
    groups: list[dict] = []
    for dataset in datasets:
        hops: dict[str, int] = {}
        bought: dict[str, int] = {}
        resold: dict[str, int] = {}
        unusable = 0
        for row in dataset.rows:
            ticket = row.get("ticket_id")
            if not isinstance(ticket, str) or not ticket:
                continue
            status = row.get("status")
            action = row.get("action")
            if status == "ok" and action in ("buy", "resell"):
                hop = _int(row.get("hop_index"))
                if hop is not None and hop > 0:
                    hops[ticket] = max(hops.get(ticket, 0), hop)
                else:
                    unusable += 1
                rounds = _int(row.get("round"))
                if action == "buy" and rounds is not None:
                    bought.setdefault(ticket, rounds)
                if action == "resell" and rounds is not None:
                    resold.setdefault(ticket, rounds)

        hop_counts: dict[int, int] = {}
        for value in hops.values():
            hop_counts[value] = hop_counts.get(value, 0) + 1
        holding_counts: dict[int, int] = {}
        for ticket, exit_round in resold.items():
            entry_round = bought.get(ticket)
            if entry_round is None:
                unusable += 1
                continue
            held = exit_round - entry_round
            if held < 0:
                unusable += 1
                continue
            holding_counts[held] = holding_counts.get(held, 0) + 1

        groups.append(
            {
                "mode": dataset.facts["mode"],
                "dataset_name": dataset.name,
                "run_id": dataset.facts["run_id"],
                "hops": [[value, count] for value, count in sorted(hop_counts.items())],
                "holding": [[value, count] for value, count in sorted(holding_counts.items())],
                "tickets": len(hops),
                "resold": len(resold),
                "unplottable_rows": unusable,
            }
        )
    groups.sort(key=lambda entry: entry["mode"])
    return {"groups": groups}


def _custody_steps(dataset: Dataset) -> list[dict]:
    """The primary buy, the admitted resales and the refusals, as custody moves.

    A listing is not a custody move and a refused transfer moved nothing, which is why the
    row's `hop_index` is null on a refusal; the step keeps the refusal so the picture can
    show the bounce rather than a gap.
    """
    steps: list[dict] = []
    for row in dataset.rows:
        action = row.get("action")
        if action not in ("buy", "resell"):
            continue
        price = _int(row.get("price_lamports"))
        status = row.get("status")
        if price is None or price < 0 or status not in ("ok", "refused", "skipped"):
            continue
        steps.append(
            {
                "seq": _int(row.get("seq")) or 0,
                "action": action,
                "from": _short(row.get("from_wallet")),
                "to": _short(row.get("to_wallet")),
                "price_lamports": price,
                "status": status,
                "error_code": _int(row.get("error_code")),
            }
        )
    steps.sort(key=lambda step: step["seq"])
    return steps


def hop_steps_series(dataset: Dataset, steps: list[dict]) -> dict:
    """The custody chain of one ticket and the refusal that tried to extend it.

    The chain is the last admitted move *into* the refusing seller, then that seller's
    refused attempt, so the three agents on the rail are one ticket's actual story rather
    than three unrelated rows. When no earlier move into that wallet exists, the chain
    says so (`linked: false`) and only the two agents of the refused attempt are drawn.
    """
    refusals = [step for step in steps if step["status"] == "refused"]
    chosen: list[dict] = []
    linked = False
    refused_step: dict | None = None
    admitted_step: dict | None = None
    if refusals:
        refused_step = refusals[0]
        earlier = [
            step
            for step in steps
            if step["status"] == "ok" and step["to"] == refused_step["from"]
            and step["seq"] < refused_step["seq"]
        ]
        if earlier:
            admitted_step = earlier[-1]
            chosen.append(admitted_step)
            linked = True
        chosen.append(refused_step)
    else:
        admitted = [step for step in steps if step["status"] == "ok"]
        if admitted:
            admitted_step = admitted[0]
            chosen.append(admitted_step)
    if not chosen:
        return {
            "event_id": dataset.facts["event_id"],
            "mode": dataset.facts["mode"],
            "ceiling_lamports": dataset.facts["ceiling_lamports"],
            "face_lamports": dataset.facts["face_lamports"],
            "steps": [],
            "nodes": [],
            "roles": {},
            "admitted": None,
            "refused": None,
            "linked": False,
            "has_refusal": False,
            "refusals_in_dataset": len(refusals),
        }

    nodes: list[str] = []
    for step in chosen:
        for label in (step["from"], step["to"]):
            if label != "?" and label not in nodes:
                nodes.append(label)
    roles: dict[str, str] = {}
    for label in nodes:
        if label in ("authority", "house"):
            roles[label] = "the house (primary seller)"
        elif refused_step and label == refused_step["from"]:
            roles[label] = "seller, keeps the ticket"
        elif refused_step and label == refused_step["to"]:
            roles[label] = "buyer, never receives it"
        elif admitted_step and label == admitted_step["to"]:
            roles[label] = "holder after the admitted move"
        else:
            roles[label] = "agent"
    return {
        "event_id": dataset.facts["event_id"],
        "mode": dataset.facts["mode"],
        "ceiling_lamports": dataset.facts["ceiling_lamports"],
        "face_lamports": dataset.facts["face_lamports"],
        "steps": chosen,
        "nodes": nodes[:3],
        "roles": roles,
        "admitted": admitted_step,
        "refused": refused_step,
        "linked": linked,
        "has_refusal": bool(refusals),
        "refusals_in_dataset": len(refusals),
    }


# --------------------------------------------------------------------------- svg parts


def _text(
    x: int,
    y: int,
    body: object,
    *,
    cls: str = "body",
    anchor: str | None = None,
    weight: str | None = None,
    fill: str | None = None,
    size: int | None = None,
    extra: str = "",
) -> str:
    attrs = [f'x="{x}"', f'y="{y}"', f'class="{cls}"']
    if anchor:
        attrs.append(f'text-anchor="{anchor}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if fill:
        attrs.append(f'fill="{fill}"')
    if size:
        attrs.append(f'font-size="{size}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)}>{_esc(body)}</text>'


def _line(x1: int, y1: int, x2: int, y2: int, *, cls: str = "rule") -> str:
    return f'<line class="{cls}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'


def _rect(x: int, y: int, w: int, h: int, *, cls: str = "panel", extra: str = "") -> str:
    tail = f" {extra}" if extra else ""
    return f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}"{tail}/>'


def _dot(x: int, y: int, *, cls: str = "dot") -> str:
    return f'<circle class="{cls}" cx="{x}" cy="{y}" r="4.5"/>'


def _ring(x: int, y: int, *, cls: str = "ring") -> str:
    return f'<circle class="{cls}" cx="{x}" cy="{y}" r="4.5"/>'


def _cross(x: int, y: int) -> str:
    return (
        f'<g class="cross">'
        f'<line x1="{x - 5}" y1="{y - 5}" x2="{x + 5}" y2="{y + 5}"/>'
        f'<line x1="{x - 5}" y1="{y + 5}" x2="{x + 5}" y2="{y - 5}"/>'
        f"</g>"
    )


def _nice_max(value: int, divisions: int = 4) -> int:
    """The smallest 1/2/5-step ceiling at or above `value`, so tick labels are round."""
    if value <= 0:
        return 1
    for exponent in range(0, 13):
        for multiplier in (1, 2, 5, 10):
            step = multiplier * 10**exponent
            if step * divisions >= value:
                return step * divisions
    return value


def _nice_ticks(top: int, divisions: int = 4) -> list[int]:
    step = max(1, top // divisions)
    return [step * index for index in range(divisions + 1)]


class Frame:
    """A plot box and the linear maps from data coordinates to whole pixels.

    Integer floor division throughout: no floating point reaches a coordinate, so two runs
    of the same input produce the same bytes.
    """

    def __init__(
        self,
        box: tuple[int, int, int, int],
        x_domain: tuple[int, int],
        y_domain: tuple[int, int],
    ) -> None:
        self.x0, self.y0, self.x1, self.y1 = box
        self.x_min, self.x_max = x_domain
        self.y_min, self.y_max = y_domain
        if self.x_max <= self.x_min:
            self.x_max = self.x_min + 1
        if self.y_max <= self.y_min:
            self.y_max = self.y_min + 1

    def px(self, value: int) -> int:
        span = self.x_max - self.x_min
        return self.x0 + (value - self.x_min) * (self.x1 - self.x0) // span

    def py(self, value: int) -> int:
        span = self.y_max - self.y_min
        return self.y1 - (value - self.y_min) * (self.y1 - self.y0) // span

    def grid(
        self,
        x_ticks: list[int],
        y_ticks: list[int],
        x_format,
        y_format,
        x_label: str,
        y_label: str,
    ) -> list[str]:
        parts: list[str] = []
        for value in y_ticks:
            y = self.py(value)
            parts.append(_line(self.x0, y, self.x1, y, cls="grid"))
            parts.append(_text(self.x0 - 10, y + 4, y_format(value), cls="tick", anchor="end"))
        for value in x_ticks:
            x = self.px(value)
            parts.append(_line(x, self.y0, x, self.y1, cls="grid"))
            parts.append(_text(x, self.y1 + 18, x_format(value), cls="tick", anchor="middle"))
        parts.append(_line(self.x0, self.y0, self.x0, self.y1, cls="axis"))
        parts.append(_line(self.x0, self.y1, self.x1, self.y1, cls="axis"))
        parts.append(
            _text((self.x0 + self.x1) // 2, self.y1 + 46, x_label, cls="axis-label", anchor="middle")
        )
        middle = (self.y0 + self.y1) // 2
        parts.append(
            f'<text class="axis-label" text-anchor="middle" '
            f'transform="rotate(-90 {self.x0 - 84} {middle})" '
            f'x="{self.x0 - 84}" y="{middle}">{_esc(y_label)}</text>'
        )
        return parts


BASE_CSS = """
.sheet { fill: #ffffff; }
.banner-box { fill: #b8261c; }
text { font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; fill: #16202b; }
.body { font-size: 13px; }
.banner { font-size: 15px; font-weight: 700; letter-spacing: 1.5px; fill: #ffffff; }
.banner-note { font-size: 13px; fill: #5c6b7a; }
.title { font-size: 21px; font-weight: 700; }
.caption { font-size: 13px; fill: #5c6b7a; }
.meta { font-size: 12px; fill: #5c6b7a; }
.dry { font-size: 12px; font-weight: 700; fill: #b8261c; }
.tick { font-size: 11px; fill: #5c6b7a; }
.axis-label { font-size: 12px; fill: #16202b; }
.legend { font-size: 12px; fill: #16202b; }
.note { font-size: 12px; fill: #5c6b7a; }
.foot { font-size: 11px; fill: #8a97a3; }
.grid { stroke: #dfe5ea; stroke-width: 1; }
.axis { stroke: #8a97a3; stroke-width: 1.2; }
.rule { stroke: #c9d2da; stroke-width: 1; }
.panel { fill: #fbfcfd; stroke: #dfe5ea; stroke-width: 1; }
.dot { fill: #1b6ca8; }
.dot-n { font-size: 11px; font-weight: 700; fill: #1b6ca8; }
.median-mark { stroke-width: 2.6; }
.median-n { font-size: 11px; font-weight: 700; }
.ring { fill: #ffffff; stroke: #8a97a3; stroke-width: 1.6; }
.cross line { stroke: #c0392b; stroke-width: 2; }
.path-ok { fill: none; stroke: #1b6ca8; stroke-width: 2; }
.path-ask { fill: none; stroke: #c9d2da; stroke-width: 1; stroke-dasharray: 3 4; }
.dash-ceiling { stroke: #b5651d; stroke-width: 1.6; stroke-dasharray: 8 5; }
.dash-face { stroke: #2e7d5b; stroke-width: 1.4; stroke-dasharray: 2 4; }
.bar { stroke: #ffffff; stroke-width: 1; }
.bar-label { font-size: 11px; fill: #16202b; }
.rule-line { stroke: #c0392b; stroke-width: 1.4; }
"""


def _document(prov: dict, body: list[str], height: int, *, css: str = BASE_CSS, attrs: str = "") -> str:
    """Assemble the SVG. Every character below is a function of `prov` and the body."""
    title = _title_line(prov)
    names = ", ".join(entry["name"] for entry in prov["datasets"])
    runs = ", ".join(prov["run_ids"])
    desc = (
        f"{LABEL}. {prov['caption']} {prov['not_evidence']} Dataset: {names}. "
        f"Run: {runs}. Generated by {prov['generator']}."
    )
    provenance_text = json.dumps(prov, indent=1, sort_keys=True, ensure_ascii=False)
    head = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="{SVG_NS}" viewBox="0 0 {WIDTH} {height}" width="{WIDTH}" '
        f'height="{height}" role="img" aria-labelledby="chart-title chart-desc" '
        f'data-synthetic="true" data-generator="{_attr(prov["generator"])}"'
        + (f" {attrs}" if attrs else "")
        + ">",
        f'  <title id="chart-title">{_esc(title)}</title>',
        f'  <desc id="chart-desc">{_esc(desc)}</desc>',
        f'  <metadata id="provenance">{_esc(provenance_text)}</metadata>',
        "  <style>",
        css.strip("\n"),
        "  </style>",
        f'  <rect class="sheet" x="0" y="0" width="{WIDTH}" height="{height}"/>',
    ]
    return "\n".join(head + [f"  {line}" for line in body] + ["</svg>", ""])


def _title_line(prov: dict) -> str:
    """The `<title>`: the label, the dataset, the run, and the whole not-evidence sentence."""
    names = ", ".join(entry["name"] for entry in prov["datasets"])
    runs = ", ".join(prov["run_ids"])
    return (
        f"{LABEL}: {prov['title']} | dataset {names} | run {runs} | {NOT_EVIDENCE}"
    )


def _is_dry(prov: dict) -> bool:
    """True when any dataset this asset draws was a dry run, so the prose must not pretend."""
    return any(entry.get("dry_run") for entry in prov.get("datasets") or [])


def _header(prov: dict) -> tuple[list[str], int]:
    """The banner, the title, the caption and the dataset lines every asset carries."""
    parts: list[str] = []
    parts.append(_rect(32, 23, 186, 36, cls="banner-box", extra='rx="18"'))
    parts.append(_text(125, 47, LABEL, cls="banner", anchor="middle"))
    parts.append(
        _text(238, 46, "synthetic simulation data - not evidence about any real ticket market",
              cls="banner-note")
    )
    y = 96
    parts.append(_text(32, y, prov["title"], cls="title"))
    y += 26
    for line in _wrap(prov["caption"], 108):
        parts.append(_text(32, y, line, cls="caption"))
        y += 18
    y += 8
    for entry in prov["datasets"][:3]:
        where = f"{entry['dir']}/{entry['name']}" if entry.get("dir") else entry["name"]
        parts.append(_text(32, y, f"dataset {where}", cls="meta"))
        y += 17
        parts.append(
            _text(
                32,
                y,
                f"run {entry['run_id']}  |  event {entry['event_id']}  |  mode "
                f"{entry['mode']}  |  {entry['rows']} rows  |  sha256 "
                f"{entry['sha256'][:16]}..",
                cls="meta",
            )
        )
        y += 17
    if len(prov["datasets"]) > 3:
        parts.append(_text(32, y, f"(+{len(prov['datasets']) - 3} more in the manifest)", cls="meta"))
        y += 17
    dry = [entry for entry in prov["datasets"] if entry.get("dry_run")]
    if dry:
        for line in _wrap(
            "DRY RUN: a simulated gateway returned what the hook would have done. No "
            "transaction was built, signed or sent; every row reads chain=simulated.",
            104,
        ):
            parts.append(_text(32, y, line, cls="dry"))
            y += 17
    y += 10
    parts.append(_line(32, y, WIDTH - 32, y, cls="rule"))
    return parts, y + 8


def _footer(prov: dict, note_lines: list[str], content_end: int) -> tuple[list[str], int]:
    """The label block every asset ends with, placed just under the last line of content."""
    top = content_end + 26
    parts = [_line(32, top, WIDTH - 32, top, cls="rule")]
    y = top + 22
    for line in _wrap(prov["not_evidence"], 118):
        parts.append(_text(32, y, line, cls="caption"))
        y += 18
    if _is_dry(prov):
        for line in _wrap(
            "DRY RUN: a simulated gateway answered for the hook. No transaction was built, "
            "signed or sent; every row reads chain=simulated.",
            118,
        ):
            parts.append(_text(32, y, line, cls="dry"))
            y += 18
    parts.append(
        _text(
            32,
            y,
            f"{LABEL} - {prov['generator']} v{prov['generator_version']} - generated "
            f"{prov['generated_at']} - re-checked by "
            "`python3 tools/swarm_charts.py verify --out docs/charts`",
            cls="foot",
        )
    )
    y += 18
    parts.append(_text(32, y, "  |  ".join(note_lines), cls="note"))
    return parts, y + 34



# --------------------------------------------------------------------------- chart: price path


def _refusal_legend(prov: dict) -> str:
    """The refusal legend row, in the tense the dataset earned.

    A dry run builds, signs and sends nothing, so a cross on the chart is a price the hook
    *would* have refused. Saying "refused ... nothing moved" would narrate a chain event that
    never happened (`records/findings/31`, H1).
    """
    if _is_dry(prov):
        return (
            "the cap hook would refuse this (6010 CapExceeded): the seller keeps the ticket "
            "and no unit moves. Dry run: nothing was built, signed or sent"
        )
    return (
        "refused by the cap hook (6010 CapExceeded): nothing moved, the seller kept the "
        "ticket"
    )


def _body_price_path(prov: dict) -> tuple[list[str], int]:
    series = prov["series"]
    parts, y = _header(prov)
    top = y + 8
    bottom = top + 264
    box = (100, top, WIDTH - 80, bottom)

    points = series["points"]
    prices = [point["price_lamports"] for point in points]
    data_max = max(prices) if prices else 1
    ceiling = int(series.get("ceiling_lamports") or 0)
    face = int(series.get("face_lamports") or 0)
    # A monitored record's ceiling is the u16 field maximum, seven and a half times face,
    # and drawing it would squash every real price into the bottom eighth of the plot. It
    # is left off the scale and named in the legend as off-chart instead -- the number is
    # never hidden, only not drawn to a scale it would wreck.
    ceiling_on_scale = bool(ceiling) and ceiling <= max(data_max * 2, 1)
    scale_high = max([data_max] + ([ceiling] if ceiling_on_scale else []) + ([face] if face else []))
    y_max = _nice_max(scale_high)
    y_ticks = _nice_ticks(y_max, 4)

    x_axis = series.get("x_axis", "round")
    xs = [point[x_axis] for point in points if point.get(x_axis) is not None]
    x_min = max(1, min(xs)) if xs else 1
    x_max = max(xs) if xs else 1
    if series.get("rounds"):
        x_max = max(x_max, int(series["rounds"]))
    if x_max == x_min:
        x_max = x_min + 1
    span = x_max - x_min
    step = 1 if span <= 12 else max(1, (span + 7) // 8)
    x_ticks = list(range(x_min, x_max + 1, step))
    if x_ticks[-1] != x_max:
        x_ticks.append(x_max)

    frame = Frame(box, (x_min, x_max), (0, y_max))
    parts.append(_rect(box[0], box[1], box[2] - box[0], box[3] - box[1]))
    parts.extend(
        frame.grid(
            x_ticks,
            y_ticks,
            lambda value: str(value),
            _sol,
            "simulated round (one round is one time-to-event step)"
            if x_axis == "round"
            else "row order (seq)",
            "price, in SOL",
        )
    )

    # The two reference lines. Drawn first so the points sit on top of them.
    if ceiling_on_scale:
        ceiling_y = frame.py(ceiling)
        parts.append(_line(box[0], ceiling_y, box[2], ceiling_y, cls="dash-ceiling"))
    if face:
        face_y = frame.py(face)
        parts.append(_line(box[0], face_y, box[2], face_y, cls="dash-face"))

    executed = [
        point for point in points if point["status"] == "ok" and point["action"] in ("buy", "resell")
    ]
    if len(executed) > 1:
        path = " ".join(
            f"{frame.px(point[x_axis])},{frame.py(point['price_lamports'])}" for point in executed
        )
        parts.append(f'<polyline class="path-ok" points="{path}"/>')

    last_executed: tuple[int, int] | None = None
    # Coincident rows draw one mark plus a count, because seven buys at the same round and
    # price are seven rows and one dot: without the count a reader counts the dots and
    # under-reads the run. The count is a function of the series, so it is deterministic.
    stacked: dict[tuple[int, int], int] = {}
    for point in executed:
        key = (frame.px(point[x_axis]), frame.py(point["price_lamports"]))
        stacked[key] = stacked.get(key, 0) + 1
    drawn: set[tuple[int, int]] = set()
    for point in points:
        if point.get(x_axis) is None:
            continue
        x = frame.px(point[x_axis])
        y_value = frame.py(point["price_lamports"])
        if point["status"] == "ok" and point["action"] in ("buy", "resell"):
            key = (x, y_value)
            last_executed = key
            if key in drawn:
                continue
            drawn.add(key)
            parts.append(_dot(x, y_value))
            if stacked[key] > 1:
                parts.append(_text(x + 8, y_value - 7, f"x{stacked[key]}", cls="dot-n"))
        elif point["status"] == "ok":
            # A listing: an ask with no chain instruction behind it.
            parts.append(_ring(x, y_value))
        elif point["status"] == "refused":
            # A refusal is drawn as a refusal: a cross at the price the hook refused, and a
            # dashed bounce back to the price the ticket actually last changed hands at.
            if last_executed is not None:
                parts.append(
                    f'<line class="path-ask" x1="{last_executed[0]}" y1="{last_executed[1]}" '
                    f'x2="{x}" y2="{y_value}"/>'
                )
            parts.append(_cross(x, y_value))
        else:
            parts.append(_ring(x, y_value))

    counts = series["counts"]
    y = box[3] + 74
    parts.append(
        _text(
            32,
            y,
            f"{counts['executed']} executed custody move(s)  |  {counts['refused']} ask(s) "
            f"refused by the cap  |  {counts['listings']} listing(s)  |  "
            f"{counts['unmet_asks']} ask(s) nobody met",
            cls="legend",
        )
    )
    y += 24
    parts.append(_line(92, y - 4, 112, y - 4, cls="dash-ceiling"))
    parts.append(
        _text(
            118,
            y,
            f"cap ceiling {_sol(ceiling)} (cap_bps {series.get('cap_bps')})"
            + (
                ""
                if ceiling_on_scale
                else ": above the top of this chart, because nothing in this dataset came "
                "near it"
            ),
            cls="legend",
        )
    )
    y += 20
    parts.append(_line(92, y - 4, 112, y - 4, cls="dash-face"))
    parts.append(_text(118, y, f"face value {_sol(face)}", cls="legend"))
    y += 20
    parts.append(_dot(102, y - 4))
    parts.append(_text(118, y, "executed: the ticket changed hands at this price, in seq order",
                       cls="legend"))
    y += 20
    parts.append(_cross(102, y - 4))
    parts.append(
        _text(118, y, _refusal_legend(prov), cls="legend")
    )
    y += 20
    parts.append(_ring(102, y - 4))
    parts.append(
        _text(118, y, "a listing, or an ask nobody met: a price with no chain instruction "
                      "behind it", cls="legend")
    )
    y += 20
    parts.append(_line(92, y - 4, 112, y - 4, cls="path-ask"))
    parts.append(
        _text(118, y, "the ask the cap refused: the dashed connector runs from the last "
                      "price that did change hands to the price that did not", cls="legend")
    )
    y += 22

    for note in prov["notes"]:
        for line in _wrap(note, 118):
            parts.append(_text(32, y, line, cls="note"))
            y += 17
        y += 2
    if series.get("unmet_bid_rows"):
        parts.append(
            _text(
                32,
                y,
                f"{series['unmet_bid_rows']} bid(s) nobody met are not on this path: a skipped "
                "buy is a limit price, not a ticket price.",
                cls="note",
            )
        )
        y += 17
    if series.get("unplottable_rows"):
        parts.append(
            _text(
                32,
                y,
                f"{series['unplottable_rows']} row(s) carried no usable integer price and are "
                "not drawn; they are counted here rather than guessed at.",
                cls="note",
            )
        )
        y += 17

    footer, height = _footer(prov, [f"{len(points)} priced row(s) drawn"], y)
    return parts + footer, height


# --------------------------------------------------------------------------- chart: markup


def _body_markup(prov: dict) -> tuple[list[str], int]:
    series = prov["series"]
    parts, y = _header(prov)
    top = y + 8
    bottom = top + 264
    box = (100, top, WIDTH - 80, bottom)

    entries = series["series"]
    rounds = max(
        int(series.get("rounds") or 1),
        max((point["rounds_left"] for entry in entries for point in entry["points"]), default=1),
    )
    marks = [point["markup_bps"] for entry in entries for point in entry["points"]]
    for entry in entries:
        marks.extend(value for _, value, _ in entry["median"])
    low = min([0] + marks)
    high = max([0] + marks)
    y_max = _nice_max(max(abs(high), abs(low), 1), 4)
    y_min = -y_max if low < 0 else 0
    y_ticks = [y_min + (y_max - y_min) * index // 4 for index in range(5)]

    # The horizon runs left to right: far from the event on the left, event day on the
    # right. `rounds_left` counts down, so the axis is drawn on `rounds - rounds_left`.
    total_rounds = max(1, rounds)
    frame = Frame(box, (0, total_rounds), (y_min, y_max))
    parts.append(_rect(box[0], box[1], box[2] - box[0], box[3] - box[1]))
    parts.extend(
        frame.grid(
            [total_rounds * index // 4 for index in range(5)],
            y_ticks,
            lambda value: str(total_rounds - value),
            _pct,
            f"simulated rounds left to the event: {total_rounds} on the left, "
            "0 (event day) on the right",
            "markup over face value (basis points)",
        )
    )
    zero_y = frame.py(0)
    parts.append(_line(box[0], zero_y, box[2], zero_y, cls="dash-face"))
    parts.append(_text(box[2] - 4, zero_y + 16, "face value (0%)", cls="note", anchor="end"))

    joined = 0
    for index, entry in enumerate(entries):
        colour = MODE_COLOURS.get(entry["mode"], FALLBACK_COLOURS[index % len(FALLBACK_COLOURS)])
        for point in entry["points"]:
            x = frame.px(total_rounds - point["rounds_left"])
            y_value = frame.py(point["markup_bps"])
            if point["status"] == "refused":
                parts.append(_cross(x, y_value))
            elif point["status"] == "skipped":
                parts.append(_ring(x, y_value))
            else:
                parts.append(f'<circle fill="{colour}" cx="{x}" cy="{y_value}" r="4.5"/>')
        # The median, with its sample size. A median of one trade is a price, not a trend:
        # it is drawn as a mark with its n, and a dashed segment joins only two *neighbouring*
        # horizon points that both have n >= 2. On a run of scripted agents most points are a
        # single resale, so this mostly draws marks and no line, which is the honest picture.
        for previous, current in zip(entry["median"], entry["median"][1:]):
            if previous[2] >= 2 and current[2] >= 2:
                joined += 1
                parts.append(
                    f'<polyline class="median-line" fill="none" stroke="{colour}" '
                    f'stroke-width="2.4" stroke-dasharray="7 4" points="'
                    f'{frame.px(total_rounds - previous[0])},{frame.py(previous[1])} '
                    f'{frame.px(total_rounds - current[0])},{frame.py(current[1])}"/>'
                )
        for rounds_left, value, sample in entry["median"]:
            x = frame.px(total_rounds - rounds_left)
            y_value = frame.py(value)
            parts.append(
                f'<line class="median-mark" stroke="{colour}" x1="{x - 7}" y1="{y_value}" '
                f'x2="{x + 7}" y2="{y_value}"/>'
            )
            parts.append(
                _text(x, y_value - 11, f"n={sample}", cls="median-n", anchor="middle",
                      fill=colour)
            )

    y = box[3] + 74
    cursor = 32
    for index, entry in enumerate(entries):
        colour = MODE_COLOURS.get(entry["mode"], FALLBACK_COLOURS[index % len(FALLBACK_COLOURS)])
        counts = entry["counts"]
        label = entry["mode"]
        detail = f"ok {counts['ok']}, refused {counts['refused']}, skipped {counts['skipped']}"
        parts.append(f'<circle fill="{colour}" cx="{cursor + 6}" cy="{y - 4}" r="5"/>')
        parts.append(_text(cursor + 20, y, f"{label}  ({detail})", cls="legend"))
        cursor += 40 + 7 * len(f"{label}  ({detail})")
    y += 24
    for line in _wrap(
        "markers are single resale attempts: filled = executed, x = refused by the cap, "
        "hollow = an ask nobody met. The short rule is the median executed markup at that "
        "point on the horizon, labelled with the number of executed resales it was taken "
        "over; a dashed segment joins two neighbouring points only when both have n >= 2, "
        "because a median of one trade is a price and not a trend. On this chart "
        f"{joined} neighbouring pair(s) have n >= 2 on both ends.",
        118,
    ):
        parts.append(_text(32, y, line, cls="note"))
        y += 17
    if joined == 0 and any(entry["median"] for entry in entries):
        y += 2
        for line in _wrap(
            "No two neighbouring points have two observations each, so no median line is "
            "drawn: joining single trades would read as a markup trend over the run.",
            118,
        ):
            parts.append(_text(32, y, line, cls="note"))
            y += 17
    if len(entries) < 2:
        y += 4
        for line in _wrap(
            "Only one dataset was supplied, so there is no second mode to compare against "
            "and none is drawn. Pass both with --dataset to see the pair.",
            118,
        ):
            parts.append(_text(32, y, line, cls="dry"))
            y += 17

    y += 10
    for note in prov["notes"]:
        for line in _wrap(note, 118):
            parts.append(_text(32, y, line, cls="note"))
            y += 17
        y += 2
    if series.get("unplottable_rows"):
        parts.append(
            _text(
                32,
                y,
                f"{series['unplottable_rows']} resale row(s) carried no usable integer price "
                "or markup and are not drawn.",
                cls="note",
            )
        )
        y += 17

    footer, height = _footer(
        prov, [f"{sum(len(entry['points']) for entry in entries)} resale attempt(s) drawn"], y
    )
    return parts + footer, height


# --------------------------------------------------------------------------- chart: hops


def _bar_panel(
    parts: list[str],
    box: tuple[int, int, int, int],
    groups: list[dict],
    key: str,
    x_label: str,
    y_label: str,
    empty_note: str,
) -> None:
    parts.append(_rect(box[0], box[1], box[2] - box[0], box[3] - box[1]))
    values = sorted({value for group in groups for value, _ in group[key]})
    counts = [count for group in groups for _, count in group[key]]
    if not values:
        parts.append(_text(box[0] + 16, box[1] + 30, empty_note, cls="note"))
        parts.append(_line(box[0], box[3], box[2], box[3], cls="axis"))
        parts.append(_text((box[0] + box[2]) // 2, box[3] + 24, x_label, cls="axis-label", anchor="middle"))
        return
    y_max = _nice_max(max(counts), 4)
    frame = Frame(box, (0, len(values)), (0, y_max))
    parts.extend(
        frame.grid(
            [index for index in range(len(values) + 1)],
            _nice_ticks(y_max, 4),
            lambda value: "",
            lambda value: str(value),
            x_label,
            y_label,
        )
    )
    group_count = max(1, len(groups))
    slot = (box[2] - box[0]) // max(1, len(values))
    bar_width = min(64, max(10, (slot - 24) // group_count))
    for index, value in enumerate(values):
        for group_index, group in enumerate(groups):
            lookup = dict(group[key])
            if value not in lookup:
                continue
            colour = MODE_COLOURS.get(group["mode"], FALLBACK_COLOURS[group_index % len(FALLBACK_COLOURS)])
            count = lookup[value]
            height = box[3] - frame.py(count)
            x = box[0] + index * slot + (slot - bar_width * group_count) // 2 + group_index * bar_width
            parts.append(
                f'<rect class="bar" fill="{colour}" x="{x}" y="{frame.py(count)}" '
                f'width="{bar_width - 2}" height="{max(1, height)}"/>'
            )
            parts.append(_text(x + (bar_width - 2) // 2, frame.py(count) - 5, str(count),
                               cls="bar-label", anchor="middle"))
        label = str(value)
        parts.append(
            _text(box[0] + index * slot + slot // 2, box[3] + 18, label, cls="tick", anchor="middle")
        )


def _body_hops(prov: dict) -> tuple[list[str], int]:
    series = prov["series"]
    parts, y = _header(prov)
    top = y + 24
    bottom = top + 190
    left = (96, top, 470, bottom)
    right = (570, top, WIDTH - 64, bottom)

    groups = series["groups"]
    parts.append(_text(96, top - 12, "a. custody hops per ticket", cls="legend", weight="bold"))
    parts.append(_text(570, top - 12, "b. holding duration, in simulated rounds",
                       cls="legend", weight="bold"))
    _bar_panel(
        parts,
        left,
        groups,
        "hops",
        "hops: 1 = the primary buy, each further hop is one admitted resale",
        "tickets",
        "No ticket changed hands in this dataset, so there is no hop to count.",
    )
    _bar_panel(
        parts,
        right,
        groups,
        "holding",
        "rounds held, from the buy round to the resale round",
        "tickets",
        "No resale was executed in this dataset, so no holding duration exists.",
    )

    y = bottom + 84
    cursor = 96
    for index, group in enumerate(groups):
        colour = MODE_COLOURS.get(group["mode"], FALLBACK_COLOURS[index % len(FALLBACK_COLOURS)])
        label = f"{group['mode']}: {group['tickets']} ticket(s) moved, {group['resold']} resold"
        parts.append(f'<rect fill="{colour}" x="{cursor}" y="{y - 11}" width="12" height="12"/>')
        parts.append(_text(cursor + 18, y, label, cls="legend"))
        cursor += 60 + 7 * len(label)
    y += 26
    for note in prov["notes"]:
        for line in _wrap(note, 118):
            parts.append(_text(32, y, line, cls="note"))
            y += 17
        y += 2
    unplottable = sum(group.get("unplottable_rows", 0) for group in groups)
    if unplottable:
        parts.append(
            _text(32, y, f"{unplottable} row(s) could not be attributed to a ticket and hop and "
                         "are not drawn.", cls="note")
        )
        y += 17

    footer, height = _footer(prov, ["hop and holding counts are per ticket"], y)
    return parts + footer, height


# --------------------------------------------------------------------------- chart: animation


ANIMATION_CSS = """
.rail { stroke: #c9d2da; stroke-width: 3; }
.node-box { fill: #f4f7fa; stroke: #8a97a3; stroke-width: 1.4; }
.node-name { font-size: 14px; font-weight: 700; }
.node-role { font-size: 11px; fill: #5c6b7a; }
.wall { stroke: #b5651d; stroke-width: 2.4; stroke-dasharray: 9 5; }
.wall-label { font-size: 12px; fill: #b5651d; }
.ticket { fill: #1b6ca8; }
.ticket-text { font-size: 12px; font-weight: 700; fill: #ffffff; }
.admitted-text { font-size: 12px; font-weight: 700; fill: #2e7d5b; }
.refused-arrow { stroke: #c0392b; stroke-width: 2.2; stroke-dasharray: 6 4; }
.refused-text { font-size: 12px; font-weight: 700; fill: #c0392b; }
.flash { fill: #c0392b; opacity: 0; }
.flash-text { font-size: 13px; font-weight: 700; fill: #ffffff; }
#ticket-group { animation: hop 12s ease-in-out infinite; }
#flash-group { animation: flash 12s ease-in-out infinite; }
@media (prefers-reduced-motion: reduce) {
  #ticket-group { animation: none; }
  #flash-group { animation: none; }
}
"""


def _body_animation(prov: dict) -> tuple[list[str], int, str]:
    series = prov["series"]
    parts, y = _header(prov)
    top = y + 16

    nodes = list(series.get("nodes") or [])[:3]
    if len(nodes) < 2:
        nodes = ["seller", "buyer"]
    roles = series.get("roles") or {}
    admitted = series.get("admitted")
    refused = series.get("refused")
    ceiling = int(series.get("ceiling_lamports") or 0)

    box_w, box_h = 178, 62
    box_centre = top + 34
    rail_y = top + 152
    count = len(nodes)
    first = 96 + box_w // 2
    last = WIDTH - 96 - box_w // 2
    centres = [first + (last - first) * index // max(1, count - 1) for index in range(count)]

    parts.append(_line(centres[0], rail_y, centres[-1], rail_y, cls="rail"))
    for index, label in enumerate(nodes):
        cx = centres[index]
        parts.append(_line(cx, box_centre + box_h // 2, cx, rail_y, cls="rule"))
        parts.append(
            _rect(cx - box_w // 2, box_centre - box_h // 2, box_w, box_h, cls="node-box", extra='rx="8"')
        )
        parts.append(_text(cx, box_centre - 4, label, cls="node-name", anchor="middle"))
        for offset, line in enumerate(_wrap(roles.get(label, "agent"), 26)[:2]):
            parts.append(_text(cx, box_centre + 15 + offset * 14, line, cls="node-role", anchor="middle"))

    if count >= 3:
        wall_x = (centres[1] + centres[2]) // 2
    else:
        wall_x = (centres[0] + centres[1]) // 2
    parts.append(_line(wall_x, rail_y - 42, wall_x, rail_y + 26, cls="wall"))
    parts.append(_text(wall_x, rail_y - 48, "the cap hook's ceiling", cls="wall-label", anchor="middle"))
    parts.append(
        _text(wall_x, rail_y - 34, _sol(ceiling) if ceiling else "ceiling", cls="wall-label", anchor="middle")
    )

    stop1 = centres[1] if admitted else centres[0]
    # The ticket is 96 px wide, so it stops with its right edge 8 px short of the wall rather
    # than straddling the ceiling it is refused at.
    attempt = wall_x - 48 - 8
    dry = _is_dry(prov)

    if admitted:
        label = (
            f"1  admitted: {_sol(admitted['price_lamports'])} from {admitted['from']} to "
            f"{admitted['to']}"
        )
        parts.append(_text((centres[0] + stop1) // 2, rail_y - 18, label, cls="admitted-text", anchor="middle"))

    parts.append('<g id="ticket-group">')
    parts.append(_rect(centres[0] - 48, rail_y - 15, 96, 30, cls="ticket", extra='rx="6"'))
    parts.append(_text(centres[0], rail_y + 5, "1 ticket", cls="ticket-text", anchor="middle"))
    parts.append("</g>")

    if refused:
        parts.append('<g id="flash-group">')
        parts.append(_rect(wall_x - 62, rail_y - 30, 124, 26, cls="flash", extra='rx="6"'))
        verdict = f"would refuse {refused['error_code'] or 6010}" if dry else (
            f"refused {refused['error_code'] or 6010}"
        )
        parts.append(_text(wall_x, rail_y - 12, verdict, cls="flash-text", anchor="middle"))
        parts.append("</g>")

    y = rail_y + 46
    if refused:
        if dry:
            sentence = (
                f"2  {refused['from']} tries {_sol(refused['price_lamports'])} for the same "
                f"ticket, above the ceiling of {_sol(ceiling)}. The hook would refuse it with "
                f"{refused['error_code'] or 6010} CapExceeded and the attempt bounces back. "
                "Dry run: nothing was built, signed or sent."
            )
        else:
            sentence = (
                f"2  {refused['from']} tries {_sol(refused['price_lamports'])} for the same "
                f"ticket, above the ceiling of {_sol(ceiling)}. The hook refuses it with "
                f"{refused['error_code'] or 6010} CapExceeded and the attempt bounces back."
            )
        for line in _wrap(sentence, 118):
            parts.append(_text(32, y, line, cls="refused-text"))
            y += 17
    else:
        parts.append(
            _text(32, y, "this dataset contains no refusal, so there is no bounce: the wall is "
                         "drawn where the cap would bind", cls="note")
        )
        y += 17

    y += 10
    parts.append(_text(32, y, "The static frame, and the frame under reduced motion, in words:",
                       cls="legend", weight="bold"))
    y += 22
    steps_text: list[str] = []
    if admitted:
        kind = "the primary buy" if admitted["action"] == "buy" else "a resale"
        steps_text.append(
            f"1. {kind} moves the ticket from {admitted['from']} to {admitted['to']} at "
            f"{_sol(admitted['price_lamports'])}; at or under the ceiling, so the cap admits it"
        )
    if refused:
        if dry:
            steps_text.append(
                f"2. {refused['from']} offers it to {refused['to']} at "
                f"{_sol(refused['price_lamports'])}; the hook would refuse the transfer, so no "
                "custody hop is recorded"
            )
            steps_text.append(
                f"3. no hop is recorded, so the unit stays with {refused['from']} in the "
                "simulation: the dataset records hop_index null on that row"
            )
        else:
            steps_text.append(
                f"2. {refused['from']} offers it to {refused['to']} at "
                f"{_sol(refused['price_lamports'])}; the hook refuses the transfer, so no custody "
                "hop is recorded"
            )
            steps_text.append(
                f"3. the unit stays with {refused['from']}: a refusal moves nothing, which is why "
                "the dataset records hop_index null on that row"
            )
    for line in steps_text:
        for wrapped in _wrap(line, 120):
            parts.append(_text(44, y, wrapped, cls="body"))
            y += 19

    y += 8
    for note in prov["notes"]:
        for wrapped in _wrap(note, 118):
            parts.append(_text(32, y, wrapped, cls="note"))
            y += 17
        y += 2

    dx_admitted = stop1 - centres[0]
    dx_attempt = attempt - centres[0]
    keyframes = f"""
@keyframes hop {{
  0% {{ transform: translateX(0px); }}
  8% {{ transform: translateX(0px); }}
  22% {{ transform: translateX({dx_admitted}px); }}
  40% {{ transform: translateX({dx_admitted}px); }}
  54% {{ transform: translateX({dx_attempt}px); }}
  68% {{ transform: translateX({dx_admitted}px); }}
  100% {{ transform: translateX({dx_admitted}px); }}
}}
@keyframes flash {{
  0% {{ opacity: 0; }}
  46% {{ opacity: 0; }}
  52% {{ opacity: 1; }}
  74% {{ opacity: 1; }}
  82% {{ opacity: 0; }}
  100% {{ opacity: 0; }}
}}
"""

    footer, height = _footer(
        prov, ["decorative motion only; no JavaScript, and the words above carry the story"], y
    )
    return parts + footer, height, keyframes


def _render_animation(prov: dict) -> str:
    parts, height, keyframes = _body_animation(prov)
    css = BASE_CSS.rstrip("\n") + "\n" + ANIMATION_CSS.strip("\n") + "\n" + keyframes.strip("\n")
    return _document(prov, parts, height, css=css, attrs='data-animation="true"')


# --------------------------------------------------------------------------- rendering


RENDERERS = {
    "price-path": lambda prov: _document(prov, *_body_price_path(prov)),
    "markup-vs-time-to-event": lambda prov: _document(prov, *_body_markup(prov)),
    "hops-and-holding": lambda prov: _document(prov, *_body_hops(prov)),
    "ticket-hop": _render_animation,
}


def render_asset(prov: dict) -> str:
    """The asset's full text, from its provenance alone. Pure: same input, same bytes."""
    try:
        renderer = RENDERERS[prov["chart"]]
    except KeyError as exc:
        raise ChartError(f"unknown chart kind {prov.get('chart')!r}") from exc
    return renderer(prov)


# --------------------------------------------------------------------------- the index page

INDEX_CSS = """
:root { color-scheme: light; }
body { margin: 0; padding: 32px 32px 64px; background: #ffffff; color: #16202b;
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
  font-size: 15px; line-height: 1.5; }
h1 { font-size: 24px; margin: 0 0 6px; }
h2 { font-size: 18px; margin: 34px 0 8px; }
p { margin: 8px 0; max-width: 92ch; }
.label { display: inline-block; background: #b8261c; color: #fff; font-weight: 700;
  letter-spacing: 2px; padding: 6px 16px; border-radius: 16px; font-size: 14px; }
.rule { border: 0; border-top: 1px solid #c9d2da; margin: 20px 0; }
table { border-collapse: collapse; width: 100%; margin-top: 12px; font-size: 14px; }
th, td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #dfe5ea;
  vertical-align: top; }
th { background: #f4f7fa; font-size: 13px; }
code, pre { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 13px; }
pre { background: #f4f7fa; border: 1px solid #dfe5ea; padding: 12px; overflow-x: auto; }
.warn { color: #b8261c; font-weight: 700; }
.muted { color: #5c6b7a; }
figure { margin: 18px 0 6px; }
img { max-width: 100%; border: 1px solid #dfe5ea; }
figcaption { font-size: 13px; color: #5c6b7a; margin-top: 6px; }
"""


def _html_escape(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def render_index(manifest: list[dict]) -> str:
    """The index page: what each asset is, the dataset it came from, and the label.

    Self-contained: no external font, no stylesheet, no CDN, no script. It opens from disk.
    The manifest JSON is in `<pre id="manifest">` so `verify` can read the page back and
    re-render it byte for byte.
    """
    rows: list[str] = []
    for prov in manifest:
        names = ", ".join(entry["name"] for entry in prov["datasets"])
        runs = ", ".join(prov["run_ids"])
        digests = ", ".join(entry["sha256"][:16] + ".." for entry in prov["datasets"])
        modes = ", ".join(sorted({entry["mode"] for entry in prov["datasets"]}))
        dry = "yes" if any(entry.get("dry_run") for entry in prov["datasets"]) else "no"
        rows.append(
            "      <tr>"
            f'<td><a href="{_html_escape(prov["asset"])}">{_html_escape(prov["asset"])}</a></td>'
            f"<td>{_html_escape(prov['title'])}</td>"
            f"<td>{_html_escape(names)}<br><span class=\"muted\">run {_html_escape(runs)}, "
            f"mode {_html_escape(modes)}, dry run {dry}</span></td>"
            f'<td><code>{_html_escape(digests)}</code></td>'
            "</tr>"
        )

    figures: list[str] = []
    for prov in manifest:
        figures.append("  <figure>")
        figures.append(
            f'    <img src="{_html_escape(prov["asset"])}" '
            f'alt="{_html_escape(_title_line(prov))}">'
        )
        figures.append(
            f"    <figcaption><strong>{_html_escape(prov['title'])}</strong> - "
            f"{_html_escape(prov['caption'])}</figcaption>"
        )
        figures.append("  </figure>")

    manifest_json = json.dumps(manifest, indent=1, sort_keys=True, ensure_ascii=False)
    runs = sorted({run for prov in manifest for run in prov["run_ids"]})
    datasets = sorted({entry["name"] for prov in manifest for entry in prov["datasets"]})
    generated = manifest[0]["generated_at"] if manifest else "never"

    total = len(manifest)
    lines = [
        "<!DOCTYPE html>",
        '<html lang="en">',
        "<head>",
        '  <meta charset="utf-8">',
        '  <meta name="viewport" content="width=device-width, initial-scale=1">',
        f"  <title>{LABEL}: market_swarm charts ({total} asset(s))</title>",
        "  <style>",
        INDEX_CSS.strip("\n"),
        "  </style>",
        "</head>",
        "<body>",
        f'  <p><span class="label">{LABEL}</span></p>',
        "  <h1>Synthetic market_swarm charts</h1>",
        f"  <p><strong>{NOT_EVIDENCE}</strong></p>",
        "  <p>Every file on this page is drawn from a dataset written by "
        "<code>python3 -m market_swarm run</code>. Those datasets are generated by scripted "
        "agents against a local validator or, as here, a simulated gateway. The datasets are "
        "not committed: the repository is code only. Each asset records the dataset's file "
        "name and its sha256 digest, which pins the picture to that file; "
        "<code>verify --dataset</code> is what rebuilds the series from the file and "
        "re-checks the numbers against it.</p>",
        f"  <p>Run id(s): <code>{_html_escape(', '.join(runs))}</code>. "
        f"Datasets: <code>{_html_escape(', '.join(datasets))}</code>. "
        f"Generated {_html_escape(generated)} by "
        f"<code>{_html_escape(GENERATOR)}</code> v{GENERATOR_VERSION}.</p>",
        '  <hr class="rule">',
        "  <h2>The assets</h2>",
        "  <table>",
        "    <thead><tr><th>asset</th><th>what it shows</th><th>dataset</th>"
        "<th>dataset sha256</th></tr></thead>",
        "    <tbody>",
        *rows,
        "    </tbody>",
        "  </table>",
        *figures,
        '  <hr class="rule">',
        "  <h2>Regenerating all of it</h2>",
        "  <p>A stranger with this repository can reproduce every file on this page from a "
        "fresh dataset. Three things will differ, because they are wall-clock and file "
        "identity rather than data: the run id, the dataset's file name and digest, and the "
        "<code>generated_at</code> timestamp in each footer. Everything else is a function of "
        "the data.</p>",
        "  <pre>python3 -m market_swarm run --config market_swarm/example-run.json --dry-run "
        "--kill-after 120 --out .swarm-runs\n"
        "python3 tools/swarm_charts.py generate --out docs/charts \\\n"
        "    --dataset .swarm-runs/&lt;run&gt;-evt_capped-SYNTHETIC.jsonl \\\n"
        "    --dataset .swarm-runs/&lt;run&gt;-evt_monitored-SYNTHETIC.jsonl\n"
        "python3 tools/swarm_charts.py verify --out docs/charts \\\n"
        "    --dataset .swarm-runs/&lt;run&gt;-evt_capped-SYNTHETIC.jsonl \\\n"
        "    --dataset .swarm-runs/&lt;run&gt;-evt_monitored-SYNTHETIC.jsonl</pre>",
        "  <p>The last command is the one that checks the numbers: it rebuilds each series "
        "from the dataset and compares it with the series the asset recorded. Run as "
        "<code>verify --out docs/charts</code> with no <code>--dataset</code>, it checks the "
        "labels and the internal consistency of the files, says so, and exits 3 rather than "
        "claiming a pass.</p>",
        "  <p>docs/CHARTS.md is the written account: what each asset shows, the command that "
        "regenerates it, and the label rule the tool enforces on itself.</p>",
        f'  <p class="warn">Nothing on this page is a finding about a real market. Every '
        f"number on it is class E: synthetic, generated, and not evidence "
        f"(records/findings/31).</p>",
        '  <hr class="rule">',
        "  <h2>Manifest</h2>",
        "  <p>Every fact each asset was drawn from, so the page can be checked without "
        "trusting the tool that wrote it:</p>",
        f"  {MANIFEST_OPEN}{_html_escape(manifest_json)}{MANIFEST_CLOSE}",
        "</body>",
        "</html>",
        "",
    ]
    return "\n".join(lines)


# --------------------------------------------------------------------------- generate


def _provenance(
    *,
    chart: str,
    asset: str,
    title: str,
    caption: str,
    datasets: list[Dataset],
    series: dict,
    notes: list[str],
    generated_at: str,
) -> dict:
    return {
        "record": RECORD,
        "synthetic": True,
        "label": LABEL,
        "generator": GENERATOR,
        "generator_version": GENERATOR_VERSION,
        "generated_at": generated_at,
        "chart": chart,
        "asset": asset,
        "title": title,
        "caption": caption,
        "not_evidence": NOT_EVIDENCE,
        "run_ids": sorted({dataset.facts["run_id"] for dataset in datasets}),
        "datasets": [dict(dataset.facts) for dataset in datasets],
        "series": series,
        "data_sha256": _data_digest(series),
        "notes": notes,
    }


def _series_for(chart: str, datasets: list[Dataset]) -> dict:
    """The series one chart kind draws, from the datasets alone.

    `generate` and `verify` both come through here, which is what makes `verify` able to
    rebuild a picture's numbers from the data file rather than only re-render the block the
    picture carries. Adding a chart kind means adding its case here.
    """
    if chart == "price-path":
        if len(datasets) != 1:
            raise ChartError(f"price-path draws one dataset, not {len(datasets)}")
        return price_path_series(datasets[0])
    if chart == "markup-vs-time-to-event":
        return markup_series(datasets)
    if chart == "hops-and-holding":
        return hops_and_holding_series(datasets)
    if chart == "ticket-hop":
        if len(datasets) != 1:
            raise ChartError(f"ticket-hop draws one dataset, not {len(datasets)}")
        return hop_steps_series(datasets[0], _custody_steps(datasets[0]))
    raise ChartError(f"unknown chart kind {chart!r}")


def build_assets(datasets: list[Dataset], generated_at: str) -> list[dict]:
    """Every asset's provenance, in the order they are written. No file is touched here.

    Every series comes from `_series_for`, so `verify` can rebuild the same series from the
    same dataset and compare it to the one recorded here.
    """
    if not datasets:
        raise ChartError("generate needs at least one --dataset")
    provenances: list[dict] = []

    for dataset in datasets:
        series = _series_for("price-path", [dataset])
        asset = f"price-path-{_safe_name(dataset.facts['event_id'])}.svg"
        mode = dataset.facts["mode"]
        if mode == "monitored":
            cap_note = (
                f"The monitored record's cap sits at the u16 field maximum "
                f"({dataset.facts['cap_bps']} bps), so the ceiling is "
                f"{_sol(dataset.facts['ceiling_lamports'] or 0)}. That is not 'no cap': the "
                "same predicate still refuses anything above it."
            )
        else:
            cap_note = (
                f"The capped record's ceiling is {dataset.facts['ceiling_lamports']} lamports "
                f"({_sol(dataset.facts['ceiling_lamports'] or 0)}, cap_bps "
                f"{dataset.facts['cap_bps']}); the cap is immutable, so the mode is a property "
                "of the mint rather than of the run."
            )
        provenances.append(
            _provenance(
                chart="price-path",
                asset=asset,
                title=(
                    f"Price path per event: {dataset.facts['event_id']} "
                    f"({mode} mode)"
                ),
                caption=(
                    "Every priced row of one synthetic run, in the order the agents produced "
                    f"it, against a {mode} record. A refusal is drawn as a refusal, not as a "
                    "gap in the path."
                ),
                datasets=[dataset],
                series=series,
                notes=[
                    (
                        "A refused row is a transfer the hook would reject: no unit moves, "
                        "and the row carries the cap error and hop_index null. This is a dry "
                        "run: a simulated gateway answered for the hook, so nothing was "
                        "built, signed or sent."
                        if dataset.facts["dry_run"]
                        else "A refused row is a transfer the hook rejected: nothing moved, "
                        "the row carries the cap error and hop_index null."
                    ),
                    cap_note,
                ],
                generated_at=generated_at,
            )
        )

    markup = _series_for("markup-vs-time-to-event", datasets)
    provenances.append(
        _provenance(
            chart="markup-vs-time-to-event",
            asset="markup-vs-time-to-event.svg",
            title="Markup over time-to-event, capped against monitored",
            caption=(
                "Resale asks as markup over face value, placed on the simulated horizon: the "
                "further right a point sits, the closer the event. One series per mode."
            ),
            datasets=datasets,
            series=markup,
            notes=[
                "The two modes differ in one thing only: the cap_bps written into the record. "
                "Monitored is the same predicate at the field maximum, so nothing scripted can "
                "price above it.",
                "Markup is integer arithmetic from price and face, the same value the dataset "
                "carries and its verifier re-checks.",
            ],
            generated_at=generated_at,
        )
    )

    hops = _series_for("hops-and-holding", datasets)
    provenances.append(
        _provenance(
            chart="hops-and-holding",
            asset="hops-and-holding.svg",
            title="Custody hops per ticket, and holding duration",
            caption=(
                "How many times a synthetic ticket changed hands, and how long a holder kept "
                "it before selling, in simulated rounds. One bar group per mode."
            ),
            datasets=datasets,
            series=hops,
            notes=[
                "A hop is an admitted custody move: the primary buy is hop 1 and each admitted "
                "resale adds one. A refusal moved nothing and is not a hop.",
                "Holding duration is the resale round minus the buy round for the same ticket, "
                "so it is only defined for a ticket that was resold.",
            ],
            generated_at=generated_at,
        )
    )

    hop_dataset = None
    for dataset in datasets:
        if any(step["status"] == "refused" for step in _custody_steps(dataset)):
            hop_dataset = dataset
            break
    if hop_dataset is None:
        hop_dataset = datasets[0]
    hop_series = _series_for("ticket-hop", [hop_dataset])
    if hop_series["refused"] and hop_series["linked"]:
        hop_note = (
            "The chain drawn is the last admitted move into "
            f"{hop_series['refused']['from']} followed by that seller's first refused attempt, "
            "so the three agents on the rail are one ticket's story and not three unrelated "
            "rows."
        )
    else:
        hop_note = (
            "No admitted move into the refusing seller exists in this dataset, so only the "
            "refused attempt is drawn and no earlier hop is invented for it."
        )
    provenances.append(
        _provenance(
            chart="ticket-hop",
            asset="ticket-hop.svg",
            title="One ticket moving between agents, and a refusal bouncing back",
            caption=(
                "A ticket carried to its holder, then an attempt that the cap refuses, "
                "bouncing off the ceiling. Motion is decoration: the frame is readable with "
                "no animation at all."
            ),
            datasets=[hop_dataset],
            series=hop_series,
            notes=[
                hop_note,
                "No JavaScript: CSS keyframes, and the words under the picture say the same "
                "thing for a reader who saves the image or turns motion off.",
            ],
            generated_at=generated_at,
        )
    )
    return provenances


def _is_own_asset(path: Path) -> bool:
    """True for an SVG this tool wrote, recognised by the provenance record in its text."""
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            head = handle.read(4096)
    except OSError:
        return False
    return RECORD in head and GENERATOR in head


def cmd_generate(args: argparse.Namespace) -> int:
    datasets = [load_dataset(Path(path)) for path in args.dataset]
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    provenances = build_assets(datasets, generated_at)

    for dataset in datasets:
        where = f"{dataset.facts['dir']}/{dataset.name}" if dataset.facts["dir"] else dataset.name
        dry = "dry run" if dataset.facts["dry_run"] else "live"
        print(
            f"dataset   {where}  sha256 {dataset.digest[:16]}..  rows {dataset.facts['rows']}  "
            f"run {dataset.facts['run_id']}  event {dataset.facts['event_id']}  "
            f"mode {dataset.facts['mode']}  {dry}"
        )

    written: list[Path] = []
    for prov in provenances:
        text = render_asset(prov)
        target = out_dir / prov["asset"]
        target.write_text(text, encoding="utf-8", newline="\n")
        written.append(target)
        print(f"asset     {_base(target)}  {len(text.encode('utf-8'))} bytes  "
              f"series sha256 {prov['data_sha256'][:16]}..")

    index_path = out_dir / INDEX_NAME
    index_path.write_text(render_index(provenances), encoding="utf-8", newline="\n")
    written.append(index_path)
    print(f"index     {_base(index_path)}  {len(provenances)} asset(s) listed")

    removed = 0
    keep = {path.name for path in written}
    for existing in sorted(out_dir.glob("*.svg")):
        if existing.name in keep:
            continue
        if _is_own_asset(existing):
            existing.unlink()
            removed += 1
            print(f"removed   {_base(existing)}  (this tool's own output, not in this generation)")
        else:
            print(
                f"kept      {_base(existing)}  (not this tool's output; left alone)",
                file=sys.stderr,
            )
    if removed:
        print(f"removed   {removed} stale asset(s) this tool had written")
    print(
        f"label     {LABEL} in every asset's text and title, with the dataset file name, the "
        "run id and the sentence about what the picture is not"
    )
    return 0


# --------------------------------------------------------------------------- verify


def _first_difference(actual: object, expected: object, path: str = "") -> str:
    """A one-line pointer at the first place two JSON-shaped values differ.

    `verify` reports why, not just that: "the bytes differ" sends a reader to a diff of two
    thousand lines, and "series.points[3].price_lamports is 3000000000, not 1000000000"
    sends them to the doctored row.
    """
    label = path or "the value"
    if isinstance(actual, dict) and isinstance(expected, dict):
        for key in sorted(set(actual) | set(expected)):
            branch = f"{path}.{key}" if path else str(key)
            if key not in actual:
                return f"{branch} is missing"
            if key not in expected:
                return f"{branch} is an extra field"
            if actual[key] != expected[key]:
                return _first_difference(actual[key], expected[key], branch)
        return label
    if isinstance(actual, list) and isinstance(expected, list):
        if len(actual) != len(expected):
            return f"{label} has {len(actual)} entries, not {len(expected)}"
        for index, (left, right) in enumerate(zip(actual, expected)):
            if left != right:
                return _first_difference(left, right, f"{path}[{index}]")
        return label
    return f"{label} is {actual!r}, not {expected!r}"


def _provenance_of(path: Path) -> dict | None:
    """The provenance block an asset carries, or None. Read by the index cross-check."""
    try:
        root = element_tree.fromstring(path.read_text(encoding="utf-8"))
    except (OSError, element_tree.ParseError):
        return None
    metadata = root.find(f"{{{SVG_NS}}}metadata")
    if metadata is None or not metadata.text:
        return None
    try:
        payload = json.loads(metadata.text)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def verify_asset(
    path: Path, extra_datasets: dict[str, Path]
) -> tuple[list[str], list[tuple[str, str]], str]:
    """Check one asset against its own provenance and, when it is present, its dataset.

    Returns `(failures, dataset_notes, series_state)`. `dataset_notes` are
    `(dataset name, "matched" | "missing")` pairs, so the caller can report one line per
    dataset instead of one per asset that mentions it. `series_state` is `"rebuilt"` when
    the series was rebuilt from the located dataset and matched the recorded one, and
    `"missing"` when at least one dataset could not be located, so nothing about the numbers
    was checked against data.
    """
    failures: list[str] = []
    notes: list[tuple[str, str]] = []
    name = _base(path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{name}: cannot read: {exc.strerror}"], notes, "missing"
    try:
        root = element_tree.fromstring(text)
    except Exception as exc:  # ParseError, or anything ElementTree raises on a broken file
        return [f"{name}: does not parse as XML ({exc.__class__.__name__}: {exc})"], notes, "missing"

    namespace = {"svg": SVG_NS}
    title_nodes = root.findall("svg:title", namespace)
    title_text = " ".join((node.text or "") for node in title_nodes)
    if not title_nodes:
        failures.append(f"{name}: no <title> element, so the asset has no title to carry the label")
    if LABEL not in title_text:
        failures.append(f"{name}: the word {LABEL} is missing from the <title> element")
    if NOT_EVIDENCE not in title_text:
        failures.append(
            f"{name}: the sentence about what the picture is not is missing from the <title> "
            "element, which is where a saved image's caption comes from"
        )

    metadata_nodes = root.findall("svg:metadata", namespace)
    prov: dict | None = None
    if not metadata_nodes:
        failures.append(f"{name}: no <metadata> provenance block")
    else:
        raw = metadata_nodes[0].text or ""
        try:
            prov = json.loads(raw)
        except json.JSONDecodeError as exc:
            failures.append(f"{name}: the provenance block is not valid JSON: {exc.msg}")
            prov = None

    visible: list[str] = []
    for node in root.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag in ("title", "desc", "metadata", "style"):
            continue
        if node.text and node.text.strip():
            visible.append(node.text.strip())
        if node.tail and node.tail.strip():
            visible.append(node.tail.strip())
    visible_text = " ".join(visible)
    if LABEL not in visible_text:
        failures.append(
            f"{name}: the word {LABEL} is missing from the visible text; a saved image would "
            "carry no label"
        )

    if prov is None:
        return failures, notes, "missing"

    if prov.get("record") != RECORD:
        failures.append(f"{name}: provenance record is {prov.get('record')!r}, not {RECORD!r}")
    if prov.get("synthetic") is not True:
        failures.append(f"{name}: provenance synthetic is {prov.get('synthetic')!r}, not true")
    for field in ("run_ids", "datasets", "series", "not_evidence", "caption", "asset"):
        if field not in prov:
            failures.append(f"{name}: provenance is missing {field!r}")
    if prov.get("asset") != path.name:
        failures.append(
            f"{name}: provenance names the asset {prov.get('asset')!r}, which is not this file"
        )
    if NOT_EVIDENCE not in (prov.get("not_evidence") or ""):
        failures.append(f"{name}: the sentence about what the picture is not has been changed")
    if NOT_EVIDENCE not in text and prov.get("not_evidence"):
        failures.append(
            f"{name}: the sentence about what the picture is not is in the provenance but not "
            "in the visible text"
        )

    dataset_names = [entry.get("name", "") for entry in prov.get("datasets") or []]
    run_ids = prov.get("run_ids") or []
    for dataset_name in dataset_names:
        if dataset_name and dataset_name not in title_text:
            failures.append(
                f"{name}: the dataset file name {dataset_name!r} is missing from the <title>"
            )
        if dataset_name and dataset_name not in visible_text:
            failures.append(f"{name}: the dataset file name {dataset_name!r} is not in the text")
    for run_id in run_ids:
        if run_id and run_id not in title_text:
            failures.append(f"{name}: the run id {run_id!r} is missing from the <title>")
        if run_id and run_id not in visible_text:
            failures.append(f"{name}: the run id {run_id!r} is not in the text")

    expected = _data_digest(prov.get("series"))
    if prov.get("data_sha256") != expected:
        failures.append(
            f"{name}: the sha256 of the series it drew, {expected[:16]}.., does not match the "
            f"recorded data_sha256 {str(prov.get('data_sha256'))[:16]}..; the numbers were "
            "changed after the digest was taken"
        )

    located: list[Path | None] = []
    for entry in prov.get("datasets") or []:
        digest = entry.get("sha256")
        dataset_name = entry.get("name")
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest or ""):
            failures.append(f"{name}: dataset {dataset_name!r} has no sha256 digest recorded")
            located.append(None)
            continue
        found = _find_dataset(dataset_name, entry.get("dir"), extra_datasets)
        if found is None:
            notes.append((dataset_name, "missing"))
            located.append(None)
            continue
        actual = _sha256(found.read_bytes())
        if actual != digest:
            failures.append(
                f"{name}: dataset {dataset_name} now hashes to {actual[:16]}.. but the asset "
                f"recorded the digest {digest[:16]}..; this picture is not of that file"
            )
        else:
            notes.append((dataset_name, "matched"))
        located.append(found)

    # Rebuild the series from the dataset itself, with the function `generate` draws with.
    # Without this, a series edited to a number the dataset never held, with `data_sha256`
    # recomputed and the asset re-rendered, passes every check above: they are all about the
    # picture agreeing with the block it carries, never about the block agreeing with data.
    series_state = "missing"
    if located and all(found is not None for found in located):
        try:
            rebuilt_datasets = [load_dataset(found) for found in located if found is not None]
            rebuilt = _series_for(prov.get("chart"), rebuilt_datasets)
        except ChartError as exc:
            failures.append(
                f"{name}: cannot rebuild its series from the dataset it names, so the numbers "
                f"are unverified: {exc}"
            )
        else:
            if rebuilt != prov.get("series"):
                failures.append(
                    f"{name}: the series does not match the dataset it names, so the picture "
                    f"is not of that file's data: {_first_difference(prov.get('series'), rebuilt)}"
                )
            else:
                series_state = "rebuilt"

    try:
        regenerated = render_asset(prov)
    except ChartError as exc:
        failures.append(f"{name}: cannot be re-rendered from its own provenance: {exc}")
        return failures, notes, series_state
    if regenerated != text:
        failures.append(
            f"{name}: the file is not what this tool renders from the provenance it carries, "
            "so it has been edited by hand"
        )
    return failures, notes, series_state


def _read_manifest(index_text: str) -> list[dict]:
    start = index_text.find(MANIFEST_OPEN)
    end = index_text.find(MANIFEST_CLOSE, start + 1)
    if start < 0 or end < 0:
        raise ChartError("index.html has no manifest block, so nothing can be re-checked")
    raw = index_text[start + len(MANIFEST_OPEN) : end]
    unescaped = (
        raw.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&amp;", "&")
    )
    try:
        payload = json.loads(unescaped)
    except json.JSONDecodeError as exc:
        raise ChartError(f"index.html manifest is not valid JSON: {exc.msg}") from exc
    if not isinstance(payload, list):
        raise ChartError("index.html manifest is not a list of assets")
    return payload


def cmd_verify(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    if not out_dir.is_dir():
        print(f"FAIL {out_dir}: not a directory", file=sys.stderr)
        return 2

    extra_datasets: dict[str, Path] = {}
    for path in args.dataset or []:
        candidate = Path(path).expanduser()
        if not candidate.is_file():
            print(f"FAIL {path}: no such dataset", file=sys.stderr)
            return 2
        extra_datasets[candidate.name] = candidate

    failures: list[str] = []
    notes: list[str] = []
    index_path = out_dir / INDEX_NAME
    manifest: list[dict] = []
    if not index_path.is_file():
        failures.append(f"{_base(index_path)}: the index is missing")
    else:
        index_text = index_path.read_text(encoding="utf-8")
        if LABEL not in index_text:
            failures.append(f"{_base(index_path)}: the word {LABEL} is missing from the page")
        if NOT_EVIDENCE not in index_text:
            failures.append(
                f"{_base(index_path)}: the sentence saying these are not real tickets is missing"
            )
        try:
            manifest = _read_manifest(index_text)
        except ChartError as exc:
            failures.append(f"{_base(index_path)}: {exc}")
        else:
            if render_index(manifest) != index_text:
                failures.append(
                    f"{_base(index_path)}: the page is not what this tool renders from its own "
                    "manifest, so it has been edited by hand"
                )

    listed = [entry.get("asset") for entry in manifest if entry.get("asset")]
    rebuilt_assets: list[str] = []
    for asset_name in listed:
        asset_path = out_dir / asset_name
        if not asset_path.is_file():
            failures.append(f"{asset_name}: listed in the index but not on disk")
            continue
        asset_failures, asset_notes, series_state = verify_asset(asset_path, extra_datasets)
        failures.extend(asset_failures)
        notes.extend(asset_notes)
        if series_state == "rebuilt":
            rebuilt_assets.append(asset_name)

    # The index is re-rendered from its own manifest, so on its own it proves nothing about
    # the assets. Compare each entry with the provenance the asset it names carries: the page
    # a reader is told to use for the digest may not carry a digest no asset has.
    for entry in manifest:
        asset_name = entry.get("asset")
        if not asset_name or not (out_dir / asset_name).is_file():
            continue  # already reported above, or by verify_asset
        asset_prov = _provenance_of(out_dir / asset_name)
        if asset_prov is None or asset_prov == entry:
            continue
        failures.append(
            f"{_base(index_path)}: the entry for {asset_name} is not the provenance that "
            f"asset carries ({_first_difference(entry, asset_prov)})"
        )

    on_disk = sorted(path.name for path in out_dir.glob("*.svg"))
    for name in on_disk:
        if name not in listed:
            failures.append(
                f"{name}: an SVG in this directory that the index does not list, so nothing "
                "re-checks it"
            )

    if manifest:
        modes = sorted({entry.get("mode") for prov in manifest for entry in prov["datasets"]})
        chart_kinds = sorted({prov["chart"] for prov in manifest})
    else:
        modes, chart_kinds = [], []

    if failures:
        print(f"FAIL {out_dir}: {len(failures)} problem(s)")
        for failure in failures:
            print(f"  {failure}")
        return 2

    checked = {entry[0] for entry in notes if entry[1] == "matched"}
    missing = {entry[0] for entry in notes if entry[1] == "missing"}
    header = (
        f"{_base(out_dir)}: {len(listed)} asset(s) and the index, "
        f"{len(set(chart_kinds))} chart kind(s), mode(s) {', '.join(modes) or 'none'}"
    )
    label_line = (
        f"     label {LABEL} and the not-evidence sentence in every title and in every "
        "visible text; the bytes are what this tool renders from the provenance each asset "
        "carries"
    )
    all_rebuilt = bool(listed) and len(rebuilt_assets) == len(listed)
    status = "PASS" if all_rebuilt else "PASS LABELS ONLY"
    print(f"{status} {header}")
    print(label_line)
    if all_rebuilt:
        print(
            f"     series rebuilt from the dataset and matched on all {len(listed)} asset(s), "
            "so the numbers are the dataset's, not just the file's"
        )
    else:
        print(
            f"     series rebuilt from the dataset on {len(rebuilt_assets)} of "
            f"{len(listed)} asset(s): no dataset was present for the rest, so their numbers "
            "were not checked against any data file. Pass --dataset <path.jsonl> to check them"
        )
    print(
        f"     dataset digests: {len(checked)} re-checked against the file, {len(missing)} "
        "not present (named below, and not claimed)"
    )
    for dataset_name in sorted(checked):
        print(f"     dataset {dataset_name}: digest re-checked, matches")
    for dataset_name in sorted(missing):
        print(
            f"     dataset {dataset_name}: not present, so its digest and its series were not "
            "re-checked against the file"
        )
    if not all_rebuilt:
        print(
            "     note: exit 3, labels and internal consistency only; nothing about the data "
            "was checked"
        )
        return 3
    return 0


# --------------------------------------------------------------------------- cli


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="swarm_charts",
        description=(
            "Draw chart and animation assets from a market_swarm dataset. Everything it "
            "writes is labelled SYNTHETIC: the data is generated, not observed."
        ),
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    generate = verbs.add_parser("generate", help="write the assets and the index from a dataset")
    generate.add_argument(
        "--dataset",
        action="append",
        required=True,
        metavar="PATH",
        help="a .jsonl dataset plus its .meta.json sidecar; repeat to compare two modes",
    )
    generate.add_argument("--out", required=True, metavar="DIR", help="asset directory")

    verify = verbs.add_parser("verify", help="re-check every asset this tool wrote")
    verify.add_argument("--out", required=True, metavar="DIR")
    verify.add_argument(
        "--dataset",
        action="append",
        default=None,
        metavar="PATH",
        help=(
            "a dataset to rebuild the series from and re-hash; without one, verify checks the "
            "labels and internal consistency only and exits 3"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        if args.verb == "generate":
            return cmd_generate(args)
        return cmd_verify(args)
    except ChartError as exc:
        print(f"REFUSED {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

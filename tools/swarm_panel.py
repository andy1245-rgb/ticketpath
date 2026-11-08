#!/usr/bin/env python3
"""Transcribe one recorded swarm run into `frontend/data/sim-run.json` and its two charts.

The run's own meta files are the evidence, and they are not committed: they live in
`.swarm-runs/`, a git-ignored scratch directory, and they name this machine's layout. A
page cannot read a git-ignored directory, so this tool copies the aggregates a panel
needs into one small committed JSON and the two price-path SVGs into
`frontend/public/charts/`. Nothing else from the run crosses over.

    python3 tools/swarm_panel.py --meta .swarm-runs
    python3 tools/swarm_panel.py --check            # the committed files still match

The run is `sw20261108T054830Z6297`: nine scripted agents, twelve rounds, two events. Its
meta says `dry_run: true` and `cluster: local`, and its `llm` field is null. That is why
the committed label says SCRIPTED and DRY RUN: the chain in the run is simulated, no
validator was used, and no model call was made, so `cost.usd` stays null with its reason
rather than carrying a number nobody spent. A meta file that says otherwise is refused
rather than relabelled; the label is a claim about the run, and the run is what decides it.

`--check` compares the committed JSON with a fresh transcription when the run is on this
machine, and always compares the two chart copies byte for byte with `docs/charts/`. A
clone has no `.swarm-runs/`: there the run comparison cannot be made, the tool says so on
its own line, and it still checks the chart bytes and the shape of the committed file.

Determinism: the output is a pure function of the meta files and the chart bytes. No
clock, no network, no third-party import.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
RUN_ID = "sw20261108T054830Z6297"
MODES = ("capped", "monitored")

DEFAULT_META = REPO_ROOT / ".swarm-runs"
DEFAULT_OUT = REPO_ROOT / "frontend" / "data" / "sim-run.json"
DEFAULT_CHARTS = REPO_ROOT / "frontend" / "public" / "charts"
DEFAULT_SOURCE_CHARTS = REPO_ROOT / "docs" / "charts"

LABEL = "SCRIPTED AGENTS · DRY RUN · SYNTHETIC"
CHAIN = "dry run: the chain is simulated in the run, not a validator"
COST = {"usd": None, "reason": "scripted agents, no model calls, so no dollars were spent"}
SOURCE_NOTE = (
    "Transcribed by tools/swarm_panel.py from the run's own meta files, which are not "
    "committed because they name this machine's scratch directory. The two charts are "
    "byte copies of docs/charts/price-path-*.svg from the same run."
)

# The meta's own status vocabulary, mapped to the words a panel prints. A key outside this
# table is a run outcome this tool has never seen, and writing it as anything would be a
# guess about whether work happened.
STATUS_MAP = {"ok": "executed", "refused": "refused", "skipped": "skipped"}
DECISION_KEYS = ("executed", "refused", "skipped", "total")


class PanelError(Exception):
    """A source or a committed file that cannot be transcribed honestly."""


def recorded_on(run_id: str = RUN_ID) -> str:
    """`sw20261108T...` -> `2026-11-08`, from the id the run named itself."""
    if not run_id.startswith("sw") or len(run_id) < 10 or not run_id[2:10].isdigit():
        raise PanelError(f"run id {run_id!r} does not carry a YYYYMMDD date")
    stamp = run_id[2:10]
    return f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}"


def meta_path(meta_dir: Path, mode: str) -> Path:
    return meta_dir / f"{RUN_ID}-evt_{mode}-SYNTHETIC.meta.json"


def chart_name(mode: str) -> str:
    return f"price-path-evt_{mode}.svg"


def chart_path(directory: Path, mode: str) -> Path:
    return directory / chart_name(mode)


def read_meta(meta_dir: Path, mode: str) -> dict:
    """One mode's meta file, checked for the facts the committed label asserts."""
    path = meta_path(meta_dir, mode)
    try:
        meta = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise PanelError(f"cannot read the {mode} meta file at {path}: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise PanelError(f"the {mode} meta file at {path} is not JSON: {exc}") from exc
    if meta.get("run_id") != RUN_ID:
        raise PanelError(f"{path} is run {meta.get('run_id')!r}, not {RUN_ID}")
    if meta.get("mode") != mode:
        raise PanelError(f"{path} is mode {meta.get('mode')!r}, not {mode!r}")
    # The three facts the label rests on. A run that touched a validator or a model is a
    # different claim, and this tool will not dress it in these words.
    if meta.get("dry_run") is not True:
        raise PanelError(f"{path} is not a dry run, so it cannot be labelled one")
    if meta.get("cluster") != "local":
        raise PanelError(f"{path} names cluster {meta.get('cluster')!r}, not the simulated 'local'")
    if meta.get("llm") is not None:
        raise PanelError(f"{path} records an llm, so 'no model calls' would be false")
    if meta.get("synthetic") is not True:
        raise PanelError(f"{path} does not declare itself synthetic")
    if meta.get("complete") is not True:
        raise PanelError(f"{path} records an incomplete run")
    if meta.get("rounds_completed") != meta.get("rounds"):
        raise PanelError(
            f"{path} completed {meta.get('rounds_completed')} of {meta.get('rounds')} rounds"
        )
    for field in ("rounds", "rounds_completed", "tickets", "cap_bps", "ceiling_lamports"):
        if not isinstance(meta.get(field), int) or isinstance(meta.get(field), bool):
            raise PanelError(f"{path} has no integer {field}")
    statuses = meta.get("by_status")
    if not isinstance(statuses, dict):
        raise PanelError(f"{path} has no by_status object")
    unknown = sorted(set(statuses) - set(STATUS_MAP))
    if unknown:
        raise PanelError(f"{path} has status key(s) this tool does not know: {', '.join(unknown)}")
    return meta


def _decisions(statuses: dict) -> dict:
    counts = {word: int(statuses.get(source, 0)) for source, word in STATUS_MAP.items()}
    counts["total"] = sum(counts.values())
    return {key: counts[key] for key in DECISION_KEYS}


def _agents(meta: dict) -> list[dict]:
    agents = meta.get("agents")
    if not isinstance(agents, list) or not agents:
        raise PanelError("the meta file lists no agents")
    out = []
    for agent in agents:
        identifier, policy = agent.get("agent_id"), agent.get("policy")
        if not identifier or not policy:
            raise PanelError(f"an agent row is missing its id or policy: {agent!r}")
        out.append({"id": identifier, "policy": policy})
    return out


def build_panel(meta_dir: Path) -> dict:
    """The committed document, from the run's two meta files and nothing else."""
    modes = []
    agents: list[dict] | None = None
    for mode in MODES:
        meta = read_meta(meta_dir, mode)
        mode_agents = _agents(meta)
        if agents is None:
            agents = mode_agents
        elif mode_agents != agents:
            raise PanelError("the two modes disagree about which agents ran")
        modes.append(
            {
                "mode": mode,
                "rounds": int(meta["rounds_completed"]),
                "tickets": int(meta["tickets"]),
                "decisions": _decisions(meta["by_status"]),
                "capBps": int(meta["cap_bps"]),
                "ceilingLamports": int(meta["ceiling_lamports"]),
                "chart": f"/charts/{chart_name(mode)}",
            }
        )
    assert agents is not None
    return {
        "schema": 1,
        "label": LABEL,
        "runId": RUN_ID,
        "recordedOn": recorded_on(),
        "chain": CHAIN,
        "agentCount": len(agents),
        "agents": agents,
        "cost": dict(COST),
        "modes": modes,
        "sourceNote": SOURCE_NOTE,
    }


def read_chart(source_charts: Path, mode: str) -> bytes:
    """The chart the mode's panel links, checked to be the chart of this run."""
    path = chart_path(source_charts, mode)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise PanelError(f"cannot read the {mode} chart at {path}: {exc}") from exc
    if RUN_ID.encode("utf-8") not in data:
        raise PanelError(f"{path} does not name run {RUN_ID}, so it is not this run's chart")
    return data


def serialise(panel: dict) -> str:
    return json.dumps(panel, ensure_ascii=False, indent=2, sort_keys=False) + "\n"


def write(meta_dir: Path, out: Path, charts_dir: Path, source_charts: Path) -> dict:
    panel = build_panel(meta_dir)
    charts = {mode: read_chart(source_charts, mode) for mode in MODES}
    out.parent.mkdir(parents=True, exist_ok=True)
    charts_dir.mkdir(parents=True, exist_ok=True)
    for mode, data in charts.items():
        (charts_dir / chart_name(mode)).write_bytes(data)
    out.write_text(serialise(panel), encoding="utf-8")
    return panel


def _diff(committed: object, expected: object, path: str = "") -> str | None:
    """The first place two documents disagree, in a sentence a reader can act on."""
    if type(committed) is not type(expected):
        return f"{path or 'document'} is {type(committed).__name__}, expected {type(expected).__name__}"
    if isinstance(expected, dict):
        for key in sorted(set(committed) | set(expected)):
            if key not in committed:
                return f"{path}.{key}".lstrip(".") + " is missing"
            if key not in expected:
                return f"{path}.{key}".lstrip(".") + " is not in the run"
            found = _diff(committed[key], expected[key], f"{path}.{key}".lstrip("."))
            if found:
                return found
        return None
    if isinstance(expected, list):
        if len(committed) != len(expected):
            return f"{path} has {len(committed)} entries, the run has {len(expected)}"
        for index, (left, right) in enumerate(zip(committed, expected)):
            found = _diff(left, right, f"{path}[{index}]")
            if found:
                return found
        return None
    if committed != expected:
        return f"{path} is {committed!r}, the run says {expected!r}"
    return None


def check(meta_dir: Path, out: Path, charts_dir: Path, source_charts: Path) -> list[str]:
    """Every way the committed panel can have stopped being true, in plain lines."""
    problems: list[str] = []
    try:
        committed = json.loads(out.read_text(encoding="utf-8"))
    except OSError as exc:
        return [f"cannot read the committed panel at {out}: {exc}"]
    except json.JSONDecodeError as exc:
        return [f"the committed panel at {out} is not JSON: {exc}"]

    # The chart copies are checked against docs/charts whatever else is here: a chart
    # edited after it was copied is a picture the committed JSON's runId does not back.
    for mode in MODES:
        source, copy = chart_path(source_charts, mode), chart_path(charts_dir, mode)
        try:
            if source.read_bytes() != copy.read_bytes():
                problems.append(f"{copy} is not a byte copy of {source}")
        except OSError as exc:
            problems.append(f"cannot compare {copy} with {source}: {exc}")

    if meta_dir.is_dir():
        try:
            expected = build_panel(meta_dir)
        except PanelError as exc:
            problems.append(str(exc))
        else:
            difference = _diff(committed, expected)
            if difference:
                problems.append(f"the committed panel no longer matches the run: {difference}")
    else:
        print(
            f"swarm_panel: the run's meta files are not at {meta_dir}; "
            "the committed JSON was checked for shape, and the charts against docs/charts",
            flush=True,
        )
        problems.extend(_shape_problems(committed))
    return problems


def _shape_problems(panel: object) -> list[str]:
    """The claims the committed file makes about itself, without the source run."""
    problems: list[str] = []
    if not isinstance(panel, dict):
        return ["the committed panel is not a JSON object"]
    if panel.get("schema") != 1:
        problems.append(f"schema is {panel.get('schema')!r}, expected 1")
    if panel.get("runId") != RUN_ID:
        problems.append(f"runId is {panel.get('runId')!r}, expected {RUN_ID}")
    if panel.get("label") != LABEL:
        problems.append(f"label is {panel.get('label')!r}")
    if panel.get("chain") != CHAIN:
        problems.append(f"chain is {panel.get('chain')!r}")
    cost = panel.get("cost") or {}
    if cost.get("usd") is not None or not cost.get("reason"):
        problems.append("cost.usd must stay null with a reason: no dollars were spent")
    agents = panel.get("agents") or []
    if panel.get("agentCount") != len(agents):
        problems.append("agentCount does not equal the number of agents listed")
    modes = panel.get("modes") or []
    if [row.get("mode") for row in modes] != list(MODES):
        problems.append(f"modes are {[row.get('mode') for row in modes]}, expected {list(MODES)}")
    for row in modes:
        decisions = row.get("decisions") or {}
        if set(decisions) != set(DECISION_KEYS):
            problems.append(f"{row.get('mode')}: decisions keys are {sorted(decisions)}")
        elif decisions["total"] != decisions["executed"] + decisions["refused"] + decisions["skipped"]:
            problems.append(f"{row.get('mode')}: decisions.total is not the sum of its parts")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools/swarm_panel.py",
        description="transcribe one recorded swarm run into the committed frontend panel",
    )
    parser.add_argument("--meta", type=Path, default=DEFAULT_META, help=f"the run's meta directory (default {DEFAULT_META})")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"the committed JSON (default {DEFAULT_OUT})")
    parser.add_argument("--charts-dir", type=Path, default=DEFAULT_CHARTS, help=f"where the chart copies go (default {DEFAULT_CHARTS})")
    parser.add_argument("--source-charts", type=Path, default=DEFAULT_SOURCE_CHARTS, help=f"the charts to copy (default {DEFAULT_SOURCE_CHARTS})")
    parser.add_argument("--check", action="store_true", help="verify the committed files; write nothing")
    args = parser.parse_args(argv)

    try:
        if args.check:
            problems = check(args.meta, args.out, args.charts_dir, args.source_charts)
            for problem in problems:
                print(f"swarm_panel: {problem}", file=sys.stderr)
            if problems:
                return 1
            print(f"swarm_panel: {args.out} matches run {RUN_ID}, charts are byte copies", flush=True)
            return 0
        panel = write(args.meta, args.out, args.charts_dir, args.source_charts)
    except PanelError as exc:
        print(f"swarm_panel: {exc}", file=sys.stderr)
        return 1
    counts = ", ".join(
        f"{row['mode']} {row['decisions']['executed']}/{row['decisions']['refused']}/{row['decisions']['skipped']}"
        for row in panel["modes"]
    )
    print(
        f"swarm_panel: {RUN_ID} -> {args.out} "
        f"({panel['agentCount']} scripted agents, {counts} executed/refused/skipped), "
        f"2 charts -> {args.charts_dir}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

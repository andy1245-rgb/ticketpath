#!/usr/bin/env python3
"""swarm_summary.py: turn one `market_swarm` dataset into the small JSON a panel reads.

    python3 tools/swarm_summary.py build --dataset <path.jsonl> [--out <path.json>]
    python3 tools/swarm_summary.py build --dataset a.jsonl --dataset b.jsonl --out <path.json>

Standard library only. No network, no chain, no key.

## Why this exists

The dataset a live run writes is large, git-ignored and machine-shaped: every row carries
twenty-odd fields because a row you have to join to price is a row whose provenance you have
already lost. A consumer that wants to show *what the swarm did* should not have to read that
file, and must not be handed a subset of it that looks like a result on its own. So this tool
reads the datasets, verifies them with the same verifier the CLI uses, and writes one small
aggregate whose every number is derived and none is retyped.

## The four refusals, stated rather than implied

- **A dataset with no `.meta.json` sidecar is refused.** Without a sidecar nothing says the run
  finished, and a half-run's price path would be presented as a whole one.
- **A sidecar that says `complete: false` is refused**, for the same reason.
- **A sidecar that says `dry_run: true` is refused.** A dry run's rows are the hook's *predicted*
  status with no transaction built, signed or sent; a summary that says "local-validator" about
  them would be the one lie this file cannot afford.
- **A row whose `chain` is `simulated` is refused**, because the aggregate says which chain the
  rows happened on and a mixed dataset cannot answer that.

## What it derives, and what it will not claim

`executed` counts rows that landed on chain (`status: ok`) with a price-bearing trade action.
`refused` counts every decision that was not taken, split by the reason a reader can act on:
a chain refusal carries the program's own error code (`6010` is `E_CAP_EXCEEDED`), and a policy
declining its own cap has no code and is counted separately rather than folded into the chain
refusals. The two are different events and a panel that adds them together is reporting one
number for two things. `unfilled_asks` is the third outcome and the one a capped market produces
most of: an ask no bid met, or a seller with nothing to transfer. It is neither a trade nor a
refusal, and folding it into either would make the cap look busier than it is.

`price_paths` is two series per event, one value per round: `asked` is the median price the
agents staged, refusals included, and `cleared` is the median price that actually transacted.
The gap between them is the cap's work, and both are medians of integers so the same dataset
always produces the same picture. The event's `ceiling_lamports` is carried so a chart can draw
the line the asks were refused above.

Every output carries `synthetic: true`, the word SYNTHETIC and the dataset's own disclaimer:
these are scripted (or model-driven) agents trading a synthetic ticket on a validator, and they
are not evidence about any real market.

Exit 0 written, 1 refused, 2 the tree could not be read.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

# `tools/` has no `__init__.py`; the package is importable only once the repository root is on
# the path. The same four lines gateway.py runs, for the same reason.
REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from market_swarm.datasets import summarise, verify_dataset  # noqa: E402

SCHEMA_VERSION = 1

#: The two actions whose price is a price. `refuse` has no price by construction and is not one.
PRICE_ACTIONS = frozenset({"buy", "list", "resell"})

#: The program's own names for the codes a summary can carry, so a panel prints a sentence
#: rather than `custom program error: 0x177a`. Only codes this program can raise on a sale.
CODE_NAMES = {
    6008: "E_AMOUNT_NOT_ONE",
    6009: "E_TRANSFER_NOT_STAGED",
    6010: "E_CAP_EXCEEDED",
    6013: "E_TICKET_NOT_VALID",
    6020: "E_WRONG_EXTRA_ACCOUNT",
    6021: "E_BELOW_FLOOR",
    6023: "E_POLICY_INVALID",
    6026: "E_NOT_AUTHORITY",
}

LABEL = "SYNTHETIC"


class SummaryError(RuntimeError):
    """A dataset this tool will not summarise, with the reason in words."""


def _read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise SummaryError(f"{path.name}:{number}: not JSON: {exc}") from exc
    return rows


def _sidecar(path: Path) -> Path:
    return Path(str(path).replace(".jsonl", ".meta.json"))


def _median(values: list[int]) -> int:
    """Nearest rank on integers, the same rule `datasets` uses, so two tools cannot disagree."""
    ordered = sorted(values)
    if not ordered:
        raise ValueError("median of nothing")
    return ordered[(len(ordered) - 1) // 2]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_sidecar(path: Path) -> dict:
    side = _sidecar(path)
    if not side.exists():
        raise SummaryError(
            f"{path.name}: no {side.name} beside it. A dataset without a sidecar cannot say "
            f"that its run finished, and this tool will not present half a run as a whole one."
        )
    try:
        meta = json.loads(side.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SummaryError(f"{side.name}: not JSON: {exc}") from exc
    if meta.get("complete") is not True:
        raise SummaryError(
            f"{path.name}: the sidecar says complete={meta.get('complete')!r}. A run that "
            f"stopped early has a price path that ends in the middle of its horizon."
        )
    if meta.get("dry_run") is not False:
        raise SummaryError(
            f"{path.name}: the sidecar says dry_run={meta.get('dry_run')!r}. A dry run's rows "
            f"are predictions; a summary that named a chain for them would be false."
        )
    if meta.get("synthetic") is not True:
        raise SummaryError(f"{path.name}: the sidecar is not labelled synthetic.")
    return meta


def _event_block(path: Path, meta: dict) -> dict:
    """One dataset's contribution: counts, codes, cost and the two price paths."""
    verified = verify_dataset(path)
    rows = _read_jsonl(path)[1:]  # the first line is the header record

    executed = 0
    refused = 0
    declined = 0
    unfilled = 0
    codes: dict[int, int] = {}
    asked: dict[int, list[int]] = {}
    cleared: dict[int, list[int]] = {}
    executed_by_agent: dict[str, int] = {}
    refused_by_agent: dict[str, int] = {}

    for row in rows:
        status = row.get("status")
        action = row.get("action")
        price = row.get("price_lamports")
        rnd = row.get("round")
        agent = row.get("agent_id")
        if status == "ok" and action in PRICE_ACTIONS and isinstance(price, int):
            executed += 1
            executed_by_agent[agent] = executed_by_agent.get(agent, 0) + 1
            if isinstance(rnd, int):
                cleared.setdefault(rnd, []).append(price)
        if status == "refused":
            refused += 1
            refused_by_agent[agent] = refused_by_agent.get(agent, 0) + 1
            code = row.get("error_code")
            if isinstance(code, int):
                codes[code] = codes.get(code, 0) + 1
        elif status == "skipped" and action == "refuse":
            # A policy declining its own cap. No transaction was built, so there is no code:
            # counting it as a chain refusal would report an answer the chain never gave.
            declined += 1
            refused_by_agent[agent] = refused_by_agent.get(agent, 0) + 1
        elif status == "skipped" and action in PRICE_ACTIONS:
            # An ask no bid met, or a seller with nothing to transfer. A third outcome, and the
            # one a capped market produces most of: it is neither a trade nor a refusal, and
            # folding it into either would make the cap look busier than it is.
            unfilled += 1
        if action in PRICE_ACTIONS and isinstance(price, int) and isinstance(rnd, int):
            asked.setdefault(rnd, []).append(price)

    # The x-axis is the run's own horizon, not the rounds that happened to produce a price. A
    # round in which nothing was staged is a gap in the chart and must appear as one: a series
    # that silently skips it draws a straight line through a round that never traded.
    completed = meta.get("rounds_completed")
    horizon = range(1, completed + 1) if isinstance(completed, int) and completed > 0 else ()
    rounds = sorted(set(horizon) | set(asked) | set(cleared))

    def series(buckets: dict[int, list[int]]) -> list[dict]:
        """One point per round: the median, the top of the range, and how many asked.

        The median alone hides the ask a cap demo is about. With two asks in a round -- one
        cleared, one refused -- the nearest-rank median is the lower of them, so a series of
        medians would show a cap doing nothing. `max_lamports` is the ask that reached highest,
        which on a capped event is the one the chain refused.
        """
        out = []
        for rnd in rounds:
            values = buckets.get(rnd) or []
            out.append(
                {
                    "round": rnd,
                    "median_lamports": _median(values) if values else None,
                    "max_lamports": max(values) if values else None,
                    "n": len(values),
                }
            )
        return out

    counts = summarise(path)
    llm = meta.get("llm")
    return {
        "dataset": path.name,
        "dataset_sha256": _sha256(path),
        "event_id": meta.get("event_id"),
        "mode": meta.get("mode"),
        "rows": verified["rows"],
        "face_lamports": meta.get("face_lamports"),
        "cap_bps": meta.get("cap_bps"),
        "ceiling_lamports": meta.get("ceiling_lamports"),
        "rounds_completed": meta.get("rounds_completed"),
        "executed": executed,
        "refused": refused + declined,
        "refused_on_chain": refused,
        "declined_by_policy": declined,
        "unfilled_asks": unfilled,
        "refused_by_code": {
            str(code): {"count": count, "name": CODE_NAMES.get(code, "unrecognised")}
            for code, count in sorted(codes.items())
        },
        "by_status": counts["by_status"],
        "by_action": counts["by_action"],
        "executed_by_agent": dict(sorted(executed_by_agent.items())),
        "refused_by_agent": dict(sorted(refused_by_agent.items())),
        "notional_lamports": counts["total_notional_lamports"],
        # The two price paths, and the rule for each stated where a reader will look for it.
        "price_paths": {
            "asked": {
                "rule": (
                    "median and highest price staged by an agent in the round, refusals "
                    "included"
                ),
                "points": series(asked),
            },
            "cleared": {
                "rule": "median price that transacted in the round",
                "points": series(cleared),
            },
        },
        # Cost: the run's own accounting where it has one. A scripted run costs nothing and the
        # number says so rather than leaving a reader to guess: no model was called, and the
        # cluster is a validator this machine funded at genesis, so no money was spent anywhere.
        # `llm` carries the spend block when a model decided, and null when none did.
        "cost": {
            "usd": 0.0 if not llm else llm.get("usd"),
            "basis": (
                "scripted policies: no model calls, and no cluster spend -- the validator is "
                "funded at genesis and nothing is rented"
            )
            if not llm
            else "llm",
            "llm": llm,
        },
        "budget": meta.get("budget"),
        "wall_seconds": meta.get("wall_seconds"),
    }


def build(datasets: list[Path], out: Path | None) -> dict:
    """The aggregate: one block per event, then the totals a panel prints above them."""
    if not datasets:
        raise SummaryError("no dataset given: nothing to summarise")
    events: list[dict] = []
    first_meta: dict | None = None
    for path in datasets:
        if not path.exists():
            raise SummaryError(f"{path}: no such file")
        meta = _require_sidecar(path)
        if first_meta is None:
            first_meta = meta
        if meta.get("run_id") != first_meta.get("run_id"):
            raise SummaryError(
                f"{path.name}: run_id {meta.get('run_id')!r} is not {first_meta.get('run_id')!r}; "
                f"two runs summarised as one would report a census that never happened"
            )
        events.append(_event_block(path, meta))

    rows = _read_jsonl(datasets[0])
    header = rows[0]
    chains = {row.get("chain") for row in rows[1:]}
    chains |= {row.get("chain") for path in datasets[1:] for row in _read_jsonl(path)[1:]}
    if "simulated" in chains:
        raise SummaryError(
            "a row says chain=simulated while the sidecar says dry_run=false: the dataset "
            "disagrees with itself about whether a transaction was ever sent"
        )

    meta = first_meta or {}
    executed = sum(event["executed"] for event in events)
    refused = sum(event["refused"] for event in events)
    unfilled = sum(event["unfilled_asks"] for event in events)
    codes: dict[str, dict] = {}
    for event in events:
        for code, entry in event["refused_by_code"].items():
            bucket = codes.setdefault(code, {"count": 0, "name": entry["name"]})
            bucket["count"] += entry["count"]

    summary = {
        "record": "swarm-summary",
        "schema_version": SCHEMA_VERSION,
        "synthetic": True,
        "label": LABEL,
        "disclaimer": meta.get("disclaimer"),
        "run_id": meta.get("run_id"),
        "seed": meta.get("seed"),
        # Where the rows happened, in the terms the run states them. A cluster name, never a
        # port, a pid or a path: this file is committed and the record stays public-safe.
        "validator": {
            "cluster": meta.get("cluster"),
            "chain": sorted(chains)[0] if chains else None,
            "program": meta.get("program"),
            "dry_run": meta.get("dry_run"),
        },
        "agents": len(meta.get("agents") or []),
        "agent_policies": sorted({a.get("policy") for a in (meta.get("agents") or [])}),
        "rounds": {
            "configured": meta.get("rounds"),
            "completed": meta.get("rounds_completed"),
        },
        "executed": executed,
        "refused": refused,
        "unfilled_asks": unfilled,
        "refused_by_code": dict(sorted(codes.items())),
        "cost": {
            "usd": 0.0 if not meta.get("llm") else meta["llm"].get("usd"),
            "basis": (
                "scripted policies: no model calls, and no cluster spend -- the validator is "
                "funded at genesis and nothing is rented"
            )
            if not meta.get("llm")
            else "llm",
        },
        "provenance": meta.get("provenance"),
        "events": events,
        "note": (
            "Synthetic data only: scripted agents trading a synthetic ticket on a local "
            "validator. No real market price, markup or refusal rate is measured here, and the "
            "chain the rows name is a validator this machine started, not a public cluster."
        ),
    }
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="swarm_summary.py",
        description="Aggregate market_swarm datasets into the small JSON a panel reads.",
    )
    sub = parser.add_subparsers(dest="verb", required=True)
    build_parser = sub.add_parser("build", help="write the aggregate")
    build_parser.add_argument("--dataset", action="append", required=True, type=Path)
    build_parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        summary = build(args.dataset, args.out)
    except SummaryError as exc:
        print(f"swarm_summary: refused: {exc}", file=sys.stderr)
        return 1
    except (OSError, ValueError, KeyError) as exc:
        print(f"swarm_summary: could not read: {exc}", file=sys.stderr)
        return 2

    if args.out is None:
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print(
            f"swarm_summary: {args.out} — {summary['agents']} agents, "
            f"{summary['record']} {summary['executed']} executed, {summary['refused']} refused, "
            f"{len(summary['events'])} event(s)"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

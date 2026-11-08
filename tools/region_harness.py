#!/usr/bin/env python3
"""Resolve a trading-harness run config's jurisdictions into the modes the loader accepts.

The swarm's run config names, per event, a `mode` (`capped` or `monitored`) and a `cap_bps`.
That is a hand-typed legal decision. This tool replaces the typing with the rules table:

    draft config (may carry `jurisdiction`)  ->  resolved config (loader's exact shape)
                                             ->  <name>.law.json (why, with the table hash)

Three properties, and they are the reason this is a separate tool rather than an edit to
`market_swarm/config.py`:

1. **The resolved file is exactly what the loader accepts.** `_no_unknown_keys` refuses any
   extra field, so the law metadata cannot ride along inside the config; it goes in a sidecar
   next to it, and the sidecar carries the table version and hash so a run can be reproduced.
2. **A hand-typed cap may be stricter than the law, never looser.** If the draft names both a
   jurisdiction and its own `mode`/`cap_bps`, the two are compared in lamports and a looser
   hand-typed ceiling is refused, naming both numbers.
3. **An unresolved jurisdiction is refused unless the operator says so.** `--accept-unresolved`
   writes `monitored` and records that the law was not established; without it the tool stops.

    python3 tools/region_harness.py draft.json --out tmp/resolved.json --check
    python3 tools/region_harness.py draft.json --out tmp/resolved.json --run --dry-run

Exit codes follow the rest of the tree: 0 ok, 1 a refusal, 2 usage, 3 the run could not start.
Standard library only.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ticketpath.core import region_caps  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The loader's exact event fields (`market_swarm/config.py` `_EVENT_FIELDS`). Anything else
#: must stay out of the resolved config or the loader refuses the whole file.
EVENT_FIELDS = ("event_id", "face_lamports", "mode", "cap_bps", "tickets", "rounds", "round_seconds")
#: Fields this tool reads and does not pass through.
DRAFT_ONLY = ("jurisdiction", "declared_event", "fee_lamports", "note")


class Refused(RuntimeError):
    """The draft cannot be turned into a run that respects the law."""


@dataclass
class Resolution:
    event_id: str
    jurisdiction: str | None
    policy: region_caps.CapPolicy | None
    ceiling: region_caps.EffectiveCeiling | None
    mode: str
    cap_bps: int | None
    reason: str


def _int(value, field: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise Refused(f"{field}: expected an integer >= {minimum}, got {value!r}")
    return value


def resolve_event(event: dict, *, on_date: str, accept_unresolved: bool) -> Resolution:
    """One draft event -> the mode/cap the loader will take, plus the record of why."""
    if not isinstance(event, dict):
        raise Refused(f"event: expected an object, got {type(event).__name__}")
    event_id = event.get("event_id")
    if not isinstance(event_id, str) or not event_id:
        raise Refused("event: event_id must be a non-empty string")
    face = _int(event.get("face_lamports"), f"{event_id}.face_lamports", minimum=1)
    fee = event.get("fee_lamports")
    if fee is not None:
        fee = _int(fee, f"{event_id}.fee_lamports")
    draft_mode = event.get("mode")
    draft_cap = event.get("cap_bps")
    code = event.get("jurisdiction")

    if not code:
        # No jurisdiction: the draft must say its own mode, and nothing about the law is
        # claimed. This is the pre-existing behaviour and it stays available.
        if draft_mode not in (None, "capped", "monitored"):
            raise Refused(f"{event_id}.mode: expected 'capped' or 'monitored', got {draft_mode!r}")
        if draft_mode is None:
            raise Refused(
                f"{event_id}: no jurisdiction and no mode. Say which jurisdiction the event is "
                f"sold into, or say the mode explicitly."
            )
        return Resolution(
            event_id=event_id, jurisdiction=None, policy=None, ceiling=None,
            mode=draft_mode,
            cap_bps=draft_cap if draft_mode == "capped" else None,
            reason="no_jurisdiction_declared",
        )

    table = region_caps.load_table()
    policy = region_caps.resolve(
        [code], on_date=on_date, table=table, declared_event=event.get("declared_event")
    )

    if policy.kind == "unresolved" and not accept_unresolved:
        raise Refused(
            f"{event_id}: {code} is unresolved ({policy.reason}): the law could not be "
            f"established, so this tool will not choose a mode. Resolve the jurisdiction, or "
            f"pass --accept-unresolved to run it as monitored and say so in the record."
        )

    ceiling = region_caps.effective_ceiling(
        face_lamports=face,
        fee_lamports=fee,
        law=policy,
        platform_cap_bps=draft_cap if draft_mode == "capped" else None,
    )

    if draft_mode == "capped" and draft_cap is None:
        raise Refused(f"{event_id}.cap_bps: mode is capped and no cap_bps was given")

    if draft_mode is not None and policy.kind == "capped" and ceiling is not None:
        # Both rules exist. `effective_ceiling` already took the stricter one; if the hand-typed
        # rule lost, it was looser than the law and must not be presented as the run's rule.
        legal = region_caps.max_price_lamports(
            region_caps.cap_base_lamports(face, fee, policy), policy.cap_bps
        )
        typed = region_caps.max_price_lamports(face, draft_cap)
        if typed > legal:
            raise Refused(
                f"{event_id}: the draft's own cap admits {typed} lamports and {code}'s law "
                f"admits {legal}; the draft is looser than the law by {typed - legal} lamports. "
                f"Lower cap_bps to at most what the law allows, or drop mode/cap_bps and let the "
                f"table decide."
            )

    if ceiling is None:
        return Resolution(
            event_id=event_id, jurisdiction=code, policy=policy, ceiling=None,
            mode="monitored", cap_bps=None, reason=policy.reason,
        )

    mode = "capped"
    if ceiling.binding_rule == "platform" and policy.kind != "capped":
        reason = f"{policy.reason}+platform_cap"
    else:
        reason = policy.reason
    return Resolution(
        event_id=event_id, jurisdiction=code, policy=policy, ceiling=ceiling,
        mode=mode, cap_bps=ceiling.cap_bps, reason=reason,
    )


def build(draft: dict, *, on_date: str, accept_unresolved: bool) -> tuple[dict, dict]:
    """(the config the loader accepts, the sidecar that says why)."""
    if not isinstance(draft, dict):
        raise Refused(f"config: expected an object, got {type(draft).__name__}")
    events = draft.get("events")
    if not isinstance(events, list) or not events:
        raise Refused("config.events: expected a non-empty list")
    table = region_caps.load_table()

    resolved_events = []
    records = []
    for event in events:
        resolution = resolve_event(event, on_date=on_date, accept_unresolved=accept_unresolved)
        out = {key: event[key] for key in EVENT_FIELDS if key in event}
        out["event_id"] = resolution.event_id
        out["mode"] = resolution.mode
        out["cap_bps"] = resolution.cap_bps
        resolved_events.append(out)
        records.append(
            {
                "event_id": resolution.event_id,
                "jurisdiction": resolution.jurisdiction,
                "declaredEvent": bool(event.get("declared_event")),
                "policy": resolution.policy.kind if resolution.policy else None,
                "reason": resolution.reason,
                "bindingJurisdiction": (
                    resolution.policy.binding_jurisdiction if resolution.policy else None
                ),
                "capBasis": resolution.policy.base if resolution.policy else None,
                "feeCapBps": resolution.policy.fee_cap_bps if resolution.policy else None,
                "mode": resolution.mode,
                "capBps": resolution.cap_bps,
                "enforcedCap": resolution.ceiling.as_dict() if resolution.ceiling else None,
            }
        )

    resolved = {
        key: value
        for key, value in draft.items()
        if key not in ("events",) and key not in ("jurisdiction",)
    }
    resolved["events"] = resolved_events
    sidecar = {
        "lawTableVersion": table.version,
        "lawTableSha256": table.sha256,
        "asOf": on_date,
        "acceptedUnresolved": accept_unresolved,
        "events": records,
    }
    return resolved, sidecar


def _parse_on_date(text: str | None) -> str:
    if text:
        return text
    # The run's own simulated start: the config's events carry faces and rounds, not dates, so
    # the caller names the date the law is checked against. No clock is read here on purpose.
    raise Refused("--on-date is required: a resolution is always against a date")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="region_harness.py",
        description="Resolve a harness run config's jurisdictions through the rules table.",
    )
    parser.add_argument("draft", help="the draft run config, which may carry `jurisdiction` per event")
    parser.add_argument("--out", help="where to write the resolved config (default: stdout)")
    parser.add_argument("--on-date", help="the date the law is checked against, YYYY-MM-DD")
    parser.add_argument("--accept-unresolved", action="store_true",
                        help="run an unresolved jurisdiction as monitored and record that it was not established")
    parser.add_argument("--check", action="store_true", help="resolve and print, write nothing, run nothing")
    parser.add_argument("--run", action="store_true", help="invoke `python3 -m market_swarm run` on the result")
    parser.add_argument("--dry-run", action="store_true", help="passed through to the swarm")
    parser.add_argument("--run-id", help="passed through to the swarm")
    args = parser.parse_args(argv)

    try:
        draft = json.loads(Path(args.draft).read_text(encoding="utf-8"))
        resolved, sidecar = build(
            draft, on_date=_parse_on_date(args.on_date), accept_unresolved=args.accept_unresolved
        )
    except (OSError, json.JSONDecodeError) as exc:
        print(f"region_harness: cannot read the draft: {exc}", file=sys.stderr)
        return 2
    except Refused as exc:
        print(f"region_harness: refused: {exc}", file=sys.stderr)
        return 1

    lines = [
        f"table {sidecar['lawTableVersion']} sha256 {sidecar['lawTableSha256'][:12]} as of {sidecar['asOf']}",
    ]
    for record in sidecar["events"]:
        cap = record["enforcedCap"]
        ceiling = cap["enforcedCeilingLamports"] if cap else "none"
        lines.append(
            f"  {record['event_id']:<20} {str(record['jurisdiction']):<8} "
            f"{str(record['policy']):<10} mode={record['mode']:<9} "
            f"cap_bps={str(record['capBps']):<5} ceiling={ceiling:<12} "
            f"binding={cap['bindingRule'] if cap else '-':<8} reason={record['reason']}"
        )
    for line in lines:
        print(line)

    if args.check:
        return 0

    target = Path(args.out) if args.out else None
    if target is None:
        print(json.dumps(resolved, indent=2))
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(resolved, indent=2) + "\n", encoding="utf-8")
    sidecar_path = target.with_suffix(".law.json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target} and {sidecar_path.name}")

    if not args.run:
        return 0
    if args.dry_run:
        resolved["dry_run"] = True
    command = [sys.executable, "-m", "market_swarm", "run", "--config", str(target)]
    if args.dry_run:
        command.append("--dry-run")
    if args.run_id:
        command += ["--run-id", args.run_id]
    completed = subprocess.run(command, cwd=str(REPO_ROOT), timeout=300)
    return completed.returncode


if __name__ == "__main__":
    sys.exit(main())

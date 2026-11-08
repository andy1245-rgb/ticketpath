"""Read a `market_swarm` dataset back and check it, or summarise it.

Two functions, both taking a path to a `.jsonl` file the runner wrote:

- `verify_dataset(path)` walks every row and checks the invariants the writer promises, and
  raises `DatasetInvalid` carrying **every** violation it found rather than the first, so a
  broken file can be fixed in one pass instead of ten.
- `summarise(path)` verifies first, then reports counts, the executed-versus-skipped ask
  split, the refusal rate per mode and integer price quantiles per mode.

Every number either function reports describes **synthetic data**. It is a description of
what the harness's agents did against a local validator or in simulation, and it is not an
estimate of any real market price, real markup or real refusal rate. `summarise` says which
kind of agent the sidecar records — LLM, scripted, or "provenance unknown" for a
caller-supplied policy that could not describe itself.

The checks, exactly as the contract states them: the header is the first line and carries
`schema_version` 1; every row carries `synthetic: True` (identity, not truthiness); `seq` is
strictly increasing from 1; `status`, `action`, `chain` and `program` are inside the closed
vocabularies, and a row's `program` is the one its header names;
`markup_bps` agrees with `price_lamports` and `face_lamports` when both are present;
`ceiling_lamports == face * (10_000 + cap_bps) // 10_000`; a `refused` row carries an
`error_code`; and an `ok` row on the local validator carries a `signature` unless the action
is a listing, which has no chain instruction behind it at all.

Quantiles use the nearest-rank method with integer arithmetic: for `n` values and percentile
`p`, the index is `ceil(p * n / 100) - 1`, clamped. No float, no interpolation, so the
answer is one of the prices that actually occurred and two runs of the same file agree.
"""

from __future__ import annotations

import json
from pathlib import Path

from .config import BPS_DENOMINATOR, ceiling_lamports
from .ledger import ACTIONS, CHAINS, SCHEMA_VERSION, STATUSES, PROGRAMS

#: Actions whose price is a real transaction price. A listing has a price and no chain.
TRADE_ACTIONS = ("buy", "resell")

#: An `ok` row with this action is allowed to have no signature: the program has no
#: listing instruction, so there is nothing on chain for a signature to point at.
UNSIGNED_ACTIONS = ("list",)


class DatasetInvalid(RuntimeError):
    """A dataset that breaks the contract. Carries every violation, not the first.

    `violations` is a tuple of one-line messages, each naming the file line it came from, so
    a caller can print them one per line and a reader can jump straight to the row.
    """

    def __init__(self, path: Path, violations: list[str]) -> None:
        self.path = str(path)
        self.violations = tuple(violations)
        super().__init__("\n".join(self.violations))


def _is_int(value: object) -> bool:
    """A real integer lamport amount. `bool` is an `int` in Python and must not pass."""
    return isinstance(value, int) and not isinstance(value, bool)


def _read(path: Path) -> list[tuple[int, dict]]:
    """`(line number, record)` for every non-blank line. Line 1 is the header."""
    source = Path(path)
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        raise DatasetInvalid(source, [f"{source.name}: cannot read: {exc.strerror}"]) from exc
    records: list[tuple[int, dict]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as exc:
            raise DatasetInvalid(
                source,
                [f"{source.name} line {number}: not valid JSON: {exc.msg}"],
            ) from exc
        if not isinstance(record, dict):
            raise DatasetInvalid(
                source,
                [f"{source.name} line {number}: expected a JSON object, got {type(record).__name__}"],
            )
        records.append((number, record))
    return records


def _check_header(name: str, line: int, header: dict, violations: list[str]) -> None:
    if header.get("record") != "header":
        violations.append(
            f"{name} line {line}: the first record must be the header (record='header'), "
            f"got record={header.get('record')!r}"
        )
    if header.get("schema_version") != SCHEMA_VERSION:
        violations.append(
            f"{name} line {line}: header schema_version must be {SCHEMA_VERSION}, "
            f"got {header.get('schema_version')!r}"
        )
    if header.get("synthetic") is not True:
        violations.append(
            f"{name} line {line}: header synthetic must be true, "
            f"got {header.get('synthetic')!r}"
        )
    label = header.get("label")
    if not isinstance(label, str) or not label.startswith("SYNTHETIC DATA"):
        violations.append(
            f"{name} line {line}: header label must start 'SYNTHETIC DATA', got {label!r}"
        )


def _check_row(name: str, line: int, row: dict, violations: list[str]) -> None:
    where = f"{name} line {line}"
    if row.get("synthetic") is not True:
        violations.append(
            f"{where}: synthetic must be true, got {row.get('synthetic')!r}"
        )

    status = row.get("status")
    if status not in STATUSES:
        violations.append(
            f"{where}: status {status!r} is outside the closed set {sorted(STATUSES)}"
        )
    action = row.get("action")
    if action not in ACTIONS:
        violations.append(
            f"{where}: action {action!r} is outside the closed set {sorted(ACTIONS)}"
        )
    chain = row.get("chain")
    if chain not in CHAINS:
        violations.append(
            f"{where}: chain {chain!r} is outside the closed set {sorted(CHAINS)}"
        )

    program = row.get("program")
    if program not in PROGRAMS:
        violations.append(
            f"{where}: program {program!r} is outside the closed set {sorted(PROGRAMS)}"
        )

    face = row.get("face_lamports")
    cap = row.get("cap_bps")
    ceiling = row.get("ceiling_lamports")
    if not _is_int(face) or face <= 0:
        violations.append(f"{where}: face_lamports must be a positive integer, got {face!r}")
    if not _is_int(cap) or not 0 <= cap <= 65535:
        violations.append(f"{where}: cap_bps must be an integer in 0..65535, got {cap!r}")
    if _is_int(face) and face > 0 and _is_int(cap) and 0 <= cap <= 65535:
        expected = ceiling_lamports(face, cap)
        if ceiling != expected:
            violations.append(
                f"{where}: ceiling_lamports {ceiling!r} does not equal face*(10000+cap)"
                f"//10000 = {expected} for face {face} and cap {cap}"
            )

    # An `ok` row that claims a chain, on an action that is a real transfer, must carry the
    # signature of the transaction that did it. Without this a hand-edited file could assert
    # an execution that never happened and still pass its own verifier.
    signature = row.get("signature")
    if (
        status == "ok"
        and chain in ("local-validator", "devnet")
        and row.get("action") not in ("list", None)
        and not signature
    ):
        violations.append(
            f"{where}: an ok row on {chain} must carry a signature; action "
            f"{row.get('action')!r} has none, so it may not claim the chain executed it"
        )

    price = row.get("price_lamports")
    markup = row.get("markup_bps")
    # A buy or a resale carries a price, so it must carry the markup that price implies.
    # Stripping the markup column used to make a resale look like a listing and pass.
    if (
        row.get("action") in ("buy", "resell")
        and price is not None
        and status in ("ok", "refused", "skipped")
        and markup is None
    ):
        violations.append(
            f"{where}: a {row.get('action')} row carries a price but no markup_bps, so the "
            "markup it implies was removed rather than computed"
        )
    if price is not None and markup is not None:
        if not _is_int(price) or not _is_int(markup):
            violations.append(
                f"{where}: price_lamports and markup_bps must be integers when present, "
                f"got {price!r} and {markup!r}"
            )
        elif _is_int(face) and face > 0:
            expected = (price - face) * BPS_DENOMINATOR // face
            if markup != expected:
                violations.append(
                    f"{where}: markup_bps {markup} does not agree with price {price} over "
                    f"face {face} (expected {expected})"
                )

    if status == "refused" and row.get("error_code") is None:
        violations.append(f"{where}: a refused row must carry an error_code, got None")
    if (
        status == "ok"
        and chain == "local-validator"
        and row.get("action") not in UNSIGNED_ACTIONS
        and not row.get("signature")
    ):
        violations.append(
            f"{where}: an ok row on the local validator must carry a signature unless it "
            f"is a listing, and action is {row.get('action')!r}"
        )


def verify_dataset(path: Path) -> dict:
    """Check every invariant; raise `DatasetInvalid` listing all violations; else summarise.

    The returned dict is small on purpose: what the file says it is and how much of it there
    is. `summarise` is the function that produces the interesting numbers.
    """
    source = Path(path)
    return _verify_records(source, _read(source))


def _verify_records(source: Path, records: list[tuple[int, dict]]) -> dict:
    """The checks, over records already parsed, so `summarise` reads the file once."""
    name = source.name
    violations: list[str] = []

    if not records:
        raise DatasetInvalid(source, [f"{name}: empty file, no header record"])

    header_line, header = records[0]
    _check_header(name, header_line, header, violations)

    previous_seq: int | None = None
    for index, (line, row) in enumerate(records[1:], start=1):
        _check_row(name, line, row, violations)
        # A header names the program and every row repeats it, so a file that mixed two programs
        # is caught here rather than by a reader who grouped by `run_id` and got two answers to
        # two questions in one bucket. Only checked when the header states one: a hand-built file
        # without it is still checked row by row, against the closed set.
        if "program" in header and row.get("program") != header["program"]:
            violations.append(
                f"{name} line {line}: row program {row.get('program')!r} disagrees with the "
                f"header's {header['program']!r}, so this file mixes two programs"
            )
        seq = row.get("seq")
        if not _is_int(seq):
            violations.append(f"{name} line {line}: seq must be an integer, got {seq!r}")
            continue
        if index == 1 and seq != 1:
            violations.append(f"{name} line {line}: seq must start at 1, got {seq}")
        if previous_seq is not None and seq <= previous_seq:
            violations.append(
                f"{name} line {line}: seq must strictly increase, got {seq} after "
                f"{previous_seq}"
            )
        previous_seq = seq

    if violations:
        raise DatasetInvalid(source, violations)

    rows = len(records) - 1
    by_status: dict[str, int] = {}
    for _, row in records[1:]:
        status = row["status"]
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "path": name,
        "rows": rows,
        "schema_version": header["schema_version"],
        "run_id": header.get("run_id"),
        "event_id": header.get("event_id"),
        "mode": header.get("mode"),
        "by_status": dict(sorted(by_status.items())),
        "ok": True,
    }


def _quantile(sorted_values: list[int], percentile: int) -> int:
    """Nearest rank, integer arithmetic: the smallest value with rank >= p*n/100."""
    count = len(sorted_values)
    rank = (percentile * count + 99) // 100
    index = min(max(rank - 1, 0), count - 1)
    return sorted_values[index]


def summarise(path: Path) -> dict:
    """Verify, then count. Every number here describes synthetic data only.

    Counts by status, action, agent and mode; the action-by-status cross-tab, so a count of
    buys can be read against how many filled; executed versus skipped versus refused asks;
    the refusal rate per mode over resale attempts; and the min/p50/p90/max price over
    executed trades per mode, by nearest rank on integers.
    """
    source = Path(path)
    records = _read(source)
    verified = _verify_records(source, records)
    header = records[0][1]
    rows = [row for _, row in records[1:]]

    by_status: dict[str, int] = {}
    by_action: dict[str, int] = {}
    by_action_status: dict[str, dict[str, int]] = {}
    by_agent: dict[str, int] = {}
    by_mode: dict[str, int] = {}
    asks_by_mode: dict[str, dict[str, int]] = {}
    prices_by_mode: dict[str, list[int]] = {}
    notional = 0

    for row in rows:
        status = row["status"]
        action = row["action"]
        mode = row["mode"]
        agent = row["agent_id"]
        by_status[status] = by_status.get(status, 0) + 1
        by_action[action] = by_action.get(action, 0) + 1
        # The cross-tab, so `buy=7` can be read against how many of those actually happened.
        # A refusal is no longer inside `buy` at all (it has the action `refuse`), but an
        # unmet bid or censored ask still is: it is a real order that did not fill.
        bucket = by_action_status.setdefault(action, {})
        bucket[status] = bucket.get(status, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1
        by_mode[mode] = by_mode.get(mode, 0) + 1

        if action == "resell":
            bucket = asks_by_mode.setdefault(
                mode, {"attempts": 0, "executed": 0, "skipped": 0, "refused": 0}
            )
            bucket["attempts"] += 1
            outcome = {"ok": "executed", "skipped": "skipped", "refused": "refused"}
            if status in outcome:
                bucket[outcome[status]] += 1

        price = row.get("price_lamports")
        if status == "ok" and action in TRADE_ACTIONS and _is_int(price):
            prices_by_mode.setdefault(mode, []).append(price)
            notional += price

    refusal_rate: dict[str, dict] = {}
    for mode, bucket in sorted(asks_by_mode.items()):
        attempts = bucket["attempts"]
        refusal_rate[mode] = {
            "attempts": attempts,
            "refused": bucket["refused"],
            "skipped": bucket["skipped"],
            "executed": bucket["executed"],
            "rate_bps": (bucket["refused"] * BPS_DENOMINATOR // attempts) if attempts else 0,
        }

    quantiles: dict[str, dict] = {}
    for mode, prices in sorted(prices_by_mode.items()):
        ordered = sorted(prices)
        quantiles[mode] = {
            "n": len(ordered),
            "min": ordered[0],
            "p50": _quantile(ordered, 50),
            "p90": _quantile(ordered, 90),
            "max": ordered[-1],
        }

    return {
        "path": verified["path"],
        "rows": verified["rows"],
        "run_id": header.get("run_id"),
        "event_id": header.get("event_id"),
        "by_status": dict(sorted(by_status.items())),
        "by_action": dict(sorted(by_action.items())),
        "by_action_status": {
            action: dict(sorted(counts.items()))
            for action, counts in sorted(by_action_status.items())
        },
        "by_agent": dict(sorted(by_agent.items())),
        "by_mode": dict(sorted(by_mode.items())),
        "asks_by_mode": dict(sorted(asks_by_mode.items())),
        "refusal_rate_by_mode": refusal_rate,
        "price_quantiles_by_mode": quantiles,
        "total_notional_lamports": notional,
        "note": _provenance_note(path),
    }


def _provenance_note(path: Path) -> str:
    """What the dataset says decided it, in one sentence that cannot claim more than it knows.

    The sidecar is the only thing a dataset has for provenance, and three answers are
    possible: a live block (the model decided), no block (scripted), and a block that says
    its own provenance is unknown (a caller-supplied policy that could not describe itself).
    The third one used to be read as "scripted", which was a claim the file does not support.
    """
    provenance = _sidecar_provenance(path)
    if provenance == "unknown":
        return (
            "Synthetic data only: this run's policies could not say which decisions a model "
            "made, so these counts claim neither scripted nor LLM agents. They describe a "
            "simulation, not any real market price, markup or refusal rate."
        )
    if provenance == "live":
        return (
            "Synthetic data only: these numbers describe what LLM agents decided in a "
            "simulation, not any real market price, markup or refusal rate."
        )
    return (
        "Synthetic data only: these numbers describe what scripted agents did in a "
        "simulation, not any real market price, markup or refusal rate."
    )


def _sidecar_provenance(path: Path) -> str:
    """`live`, `unknown` or `scripted`, read from the sidecar beside the dataset.

    The dataset alone cannot say: the row schema is the same either way. The sidecar's own
    `provenance` field is the answer when it has one; an older sidecar without it is read
    from its `llm` block, and a missing or unreadable sidecar reads as scripted, which is
    the conservative answer for a file that did not record its own provenance.
    """
    sidecar = Path(str(path).replace(".jsonl", ".meta.json"))
    try:
        meta = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "scripted"
    label = meta.get("provenance")
    if label in ("llm", "policy"):
        return "live"
    if label == "unknown":
        return "unknown"
    if label == "scripted":
        return "scripted"
    block = meta.get("llm")
    if not isinstance(block, dict):
        return "scripted"
    return "unknown" if block.get("provenance") == "unknown" else "live"


__all__ = ["DatasetInvalid", "summarise", "verify_dataset", "TRADE_ACTIONS"]

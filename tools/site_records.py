#!/usr/bin/env python3
"""Copy the record a static page must print into the bundle the site is built from.

The published site is a static export: there is no backend to ask, so a record it prints
has to travel inside the build. This tool copies `records/devnet-artefacts.json`, byte for
byte, to `frontend/data/devnet-artefacts.json`, and `--check` proves the copy still equals
the record it came from.

Why a copy rather than an import from the parent directory: the deploy builds from a copy
of `frontend/` alone, so a path outside that directory does not exist at build time. Why a
copy rather than a transcription: a page that prints a deployment is printing evidence, and
evidence that has been re-typed is a second thing to keep true. The bytes are the bytes.

What it refuses:

  - `records/*.local.json`, the rehearsals `tools/devnet_publish.py --local` and
    `tools/publish_v2.py` write. Those are what a local validator proved on this machine,
    not a public cluster, and `.gitignore` keeps them out of the tree on purpose.
  - a source file that does not parse as JSON, or whose `programId`/`cluster` is missing,
    because a record without them cannot be printed as a deployment.

    python3 tools/site_records.py            # write the copies
    python3 tools/site_records.py --check     # the committed copies still match

Exit 0 clean, 1 a copy is missing or differs, 2 the tree could not be read. No clock, no
network, no third-party import: the output is a pure function of the source bytes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "frontend" / "data"

#: source (relative to the repository root) -> copy (relative to the repository root).
#: One row per record a page prints. A record that is not on this list is not in the
#: bundle, and a page that needs one has to add it here rather than reach outside the
#: build.
RECORDS: tuple[tuple[str, str], ...] = (
    ("records/devnet-artefacts.json", "frontend/data/devnet-artefacts.json"),
)

#: A file whose name ends with this is a rehearsal. It is refused by name, before its
#: content is read, so a copy that escaped the ignore rules cannot reach a published page.
REHEARSAL_SUFFIX = ".local.json"


class RecordRefused(RuntimeError):
    """A source file this tool will not put in the bundle, and why."""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_source(root: Path, rel: str) -> bytes:
    if rel.endswith(REHEARSAL_SUFFIX):
        raise RecordRefused(f"{rel} is a local rehearsal, not a record of a public cluster")
    path = root / rel
    if not path.is_file():
        raise RecordRefused(f"{rel} does not exist")
    data = path.read_bytes()
    try:
        parsed = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RecordRefused(f"{rel} is not JSON: {error}") from error
    if not isinstance(parsed, dict):
        raise RecordRefused(f"{rel} is not a JSON object")
    for key in ("cluster", "programId"):
        if not parsed.get(key):
            raise RecordRefused(f"{rel} has no {key}, so it records no deployment")
    return data


def expected(root: Path, records: tuple[tuple[str, str], ...] = RECORDS) -> dict[str, bytes]:
    """The bundle this tree says it should have: copy path -> bytes."""
    return {dst: _read_source(root, src) for src, dst in records}


def write(root: Path, records: tuple[tuple[str, str], ...] = RECORDS) -> list[str]:
    """Write every copy. Returns one line per copy, for the caller to print."""
    lines = []
    for src, dst in records:
        data = _read_source(root, src)
        target = root / dst
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        lines.append(f"wrote {dst} from {src} ({len(data)} bytes, sha256 {sha256(data)})")
    return lines


def check(root: Path, records: tuple[tuple[str, str], ...] = RECORDS) -> list[str]:
    """Every problem with the committed copies, one line each; empty means clean."""
    problems = []
    for dst, want in expected(root, records).items():
        path = root / dst
        if not path.is_file():
            problems.append(f"{dst}: missing; run tools/site_records.py")
            continue
        got = path.read_bytes()
        if got != want:
            problems.append(
                f"{dst}: {len(got)} bytes sha256 {sha256(got)} does not match the record "
                f"({len(want)} bytes sha256 {sha256(want)}); run tools/site_records.py"
            )
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="report differences, write nothing")
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root (a fixture tree, for tests)")
    args = parser.parse_args(argv)
    root = Path(args.root)

    try:
        if args.check:
            problems = check(root)
        else:
            for line in write(root):
                print(line)
            problems = check(root)
    except RecordRefused as error:
        print(f"site_records: {error}", file=sys.stderr)
        return 2

    if problems:
        for problem in problems:
            print(f"site_records: {problem}", file=sys.stderr)
        return 1
    print("site_records: the bundled copies match the records they came from")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

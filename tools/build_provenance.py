#!/usr/bin/env python3
"""build_provenance.py: which source, which toolchain, which bytes.

A `.so` on disk is a claim that some source produced it. Nothing in a Solana program
carries that claim: the binary has no build stamp, the crate has no committed lockfile, and
`git log` says what was edited, not what was compiled. So a validator deploying
`cap_hook.so` -- or a reader checking a figure in `programs/cap_hook/README.md` -- had no
way to say *which* revision and *which* toolchain those bytes came from. Two versions of
this program have run, one on devnet and one on a local validator, and the tree held only
the newer source: a v1 run deploying v2 bytes is not a hypothetical, it is what the missing
record allows.

This tool writes that record down and then checks it. It is the gate, not a report: a
mismatch exits 1.

    python3 tools/build_provenance.py write     # record what is on disk and what git says
    python3 tools/build_provenance.py verify    # fail if the record no longer holds

`write` builds nothing. It reads the binary that is already there, hashes it, and records
the facts a rebuild would have to reproduce:

  - the program's name, taken from the `[lib] name` of the crate's `Cargo.toml`;
  - the program id it is deployed under, but only when the tree states one. `lib.rs` says
    in its header that the id is a property of the deploy keypair, not of the crate, so
    there is no id to read from the Rust source and this tool invents none. Where the tree
    does state one -- `records/devnet-artefacts.json` for the devnet program -- it is read
    from there and the path it came from is recorded beside it;
  - the source commit, resolved by git and never typed here: HEAD for the version that is
    in the tree, and for a superseded version the commit that *added* its `src/lib.rs`
    (`git log --diff-filter=A`), which is the commit that still holds those bytes;
  - per-file sha256 of every `.rs` file and of `Cargo.toml` that the build used;
  - the toolchain, quoted from `cargo-build-sbf --version` and `solana --version`;
  - the exact build command and the directory it ran in;
  - the `.so`'s sha256 and byte size, and the same for any independent rebuild supplied
    with `--rebuild version=path`;
  - an ISO-8601 UTC timestamp.

`verify` re-derives what it can and fails, one line per violation, when:

  1. source-file   a recorded source file no longer hashes to the recorded value. A file
                   built from a commit is re-read from that commit (immutable, and the only
                   place a superseded version's bytes still exist); a file built from the
                   tree is re-read from disk, which is what catches an edit made after the
                   binary was built.
  2. source-commit the recorded commit no longer resolves in this repository. History has
                   been rewritten here once already; a provenance file whose commit is
                   gone is a file that has stopped meaning anything.
  3. binary        the recorded `.so` is absent, or its sha256 or size differs from the
                   recorded value.
  4. program-id    an id recorded from the tree is no longer the id the tree states.
  5. shape         an entry is missing a field the other checks need.

Exit codes: 0 clean, 1 any violation, 2 the artefact or the repository could not be read
(bad JSON, git refused, the toolchain is not on PATH for `write`).

Paths in the artefact are repo-relative and the output carries no pid and no port: this
repository is public, and `tools/public_safety.py` refuses an absolute home path. The
scratch directory a build is copied out of is therefore never recorded -- only the bytes
that came out of it.

What it does not claim. Reproducibility here is *measured*, not proven: the same command
was run twice in two independent directories and the two `.so` files were identical, which
is recorded in `build.reproducibility`. `VERIFY` does not re-run the build; re-running it is
the reader's own check, and `build.command` is written so that check is one line. The
dependency pins are the one thing that is not in the tree at all: `cargo-build-sbf`
generates `Cargo.lock` and `.gitignore` keeps it out, so a rebuild resolves its dependencies
from whatever the registry holds at that moment. The tool records the lockfile hash it saw
and says so in the artefact rather than pretending the pins are committed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The crate this records. One program, two versions, because two of them have run under a
#: name a reader will find in the README.
PROGRAM_DIR = "programs/cap_hook"

#: The committed artefact, repo-relative. It is the thing this tool exists to write.
ARTEFACT_PATH = "programs/cap_hook/BUILD-PROVENANCE.json"

SCHEMA = "build-provenance/1"

EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_UNREADABLE = 2


@dataclass(frozen=True)
class Version:
    """One build of the program: what it is called, and where its bytes came from.

    `commit_from` is a *rule*, resolved by git at write time, never a sha typed in here: a
    hardcoded commit would be a claim that stops being true the moment history is rewritten,
    and this repository's history has already been rewritten once.
    """

    label: str
    binary: str
    commit_from: str
    scope: str


#: The two builds the tree ships. `cap_hook.so` is the v2 binary and sits at the path the
#: harness deploys (`target/deploy/cap_hook.so`, see `tools/publish_v2.py`); the v1 binary
#: is kept beside it under its own name so both are on disk to be verified.
#:
#: scope "tree"    -- the bytes were built from the files in the working tree
#: scope "commit"  -- the bytes were built from the files at that commit, which for a
#:                    superseded version is the only place they still exist
VERSIONS = (
    Version(label="v1", binary="cap_hook-v1.so", commit_from="first-add", scope="commit"),
    Version(label="v2", binary="cap_hook.so", commit_from="head", scope="tree"),
)

#: Which version the one program id the tree states belongs to. v1 was deployed to devnet
#: and `records/devnet-artefacts.json` records the id it went to. v2 has only ever run on a
#: local validator under a keypair of its own, recorded in a git-ignored file, so the tree
#: states no v2 id and none is invented here.
PROGRAM_ID_VERSIONS = frozenset({"v1"})

#: Where the tree keeps the deployed program id, and the key inside it. Both are recorded
#: beside the value so a reader checks the same place this tool did.
PROGRAM_ID_SOURCE = "records/devnet-artefacts.json"
PROGRAM_ID_KEY = "programId"

#: The command a rebuild has to run. `--offline` because a build that reaches the network is
#: not a build of the source alone; two jobs under `nice` because the SBF link is the
#: peak-memory step of the build and this is a small machine.
BUILD_COMMAND = (
    "CARGO_BUILD_JOBS=2 nice -n 10 cargo-build-sbf --offline --sbf-out-dir <out-dir>"
)

#: The binaries whose `--version` line is part of the provenance. `cargo-build-sbf` prints
#: its own version followed by the platform-tools and rustc it will use, which is the whole
#: toolchain that decides the bytes.
TOOLCHAIN_BINARIES = ("cargo-build-sbf", "solana")

#: The files a build of this crate compiles, as the paths the commit holds them at. One
#: `.rs` file per module, and the manifest: nothing else is source.
SOURCE_FILE = re.compile(rf"^{re.escape(PROGRAM_DIR)}/(Cargo\.toml|src/[^/]+\.rs)$")


class ProvenanceError(RuntimeError):
    """The record cannot be written or read: git refused, a path is missing, no toolchain."""


# -- hashing, git, and the small parsers -----------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(root: Path, *args: str) -> str:
    """Run git in `root` and return its stdout as text. Never through a shell."""
    done = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if done.returncode != 0:
        raise ProvenanceError(
            f"git {' '.join(args)} failed in the repository: {done.stderr.strip()}"
        )
    return done.stdout


def git_blob(root: Path, spec: str) -> bytes:
    """The bytes of one blob, `commit:path` or a sha. Read from git, not from the tree."""
    done = subprocess.run(
        ["git", "-C", str(root), "cat-file", "blob", spec],
        capture_output=True,
        check=False,
    )
    if done.returncode != 0:
        raise ProvenanceError(f"git cannot read {spec}")
    return done.stdout


def utc_now() -> str:
    """ISO-8601 UTC, second resolution, `Z` suffix: the one form a log reader parses."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def toolchain_versions() -> dict[str, str]:
    """The version line of each tool the build depends on, quoted verbatim."""
    versions: dict[str, str] = {}
    for binary in TOOLCHAIN_BINARIES:
        if shutil.which(binary) is None:
            raise ProvenanceError(
                f"{binary} is not on PATH; the Solana block of the shell profile sets it"
            )
        done = subprocess.run(
            [binary, "--version"], capture_output=True, text=True, check=False
        )
        if done.returncode != 0:
            raise ProvenanceError(f"{binary} --version exited {done.returncode}")
        for line in done.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            name = line.split(None, 1)[0].replace("-", "_")
            versions[name] = line
    return versions


def cargo_lib_name(text: str) -> str | None:
    """The `name` of the `[lib]` table in a Cargo.toml, which is the program's name.

    The crate name is not the program name: the `[package]` table says `cap-hook` and the
    `[lib]` table says `cap_hook`, and it is the second one that names the `.so`.
    """
    section = None
    lib_name = None
    package_name = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            section = stripped[1:-1].strip()
            continue
        match = re.match(r'name\s*=\s*"([^"]+)"', stripped)
        if not match:
            continue
        if section == "lib" and lib_name is None:
            lib_name = match.group(1)
        elif section == "package" and package_name is None:
            package_name = match.group(1)
    return lib_name or package_name


def source_commit(root: Path, version: Version) -> str:
    """The commit the bytes were built from, resolved by git rather than typed here."""
    if version.commit_from == "head":
        return git(root, "rev-parse", "HEAD").strip()
    out = git(
        root,
        "log",
        "--diff-filter=A",
        "--format=%H",
        "--",
        f"{PROGRAM_DIR}/src/lib.rs",
    )
    commits = [line.strip() for line in out.splitlines() if line.strip()]
    if not commits:
        raise ProvenanceError(
            f"no commit adds {PROGRAM_DIR}/src/lib.rs, so there is no v1 source to name"
        )
    return commits[-1]


def source_files_from_commit(root: Path, commit: str) -> dict[str, str]:
    """Every `.rs` and the `Cargo.toml` this commit builds, path -> sha256 of its bytes."""
    listing = git(root, "ls-tree", "-r", "--name-only", commit, "--", PROGRAM_DIR)
    files: dict[str, str] = {}
    for name in sorted(line.strip() for line in listing.splitlines() if line.strip()):
        if not SOURCE_FILE.match(name):
            continue
        files[name] = sha256_bytes(git_blob(root, f"{commit}:{name}"))
    return files


def source_files_from_tree(root: Path) -> dict[str, str]:
    """The same set, read from disk: what a build in this worktree would compile now."""
    files: dict[str, str] = {}
    cargo = root / PROGRAM_DIR / "Cargo.toml"
    if not cargo.is_file():
        raise ProvenanceError(f"no {PROGRAM_DIR}/Cargo.toml in the tree")
    files[f"{PROGRAM_DIR}/Cargo.toml"] = sha256_file(cargo)
    for path in sorted((root / PROGRAM_DIR / "src").glob("*.rs")):
        files[f"{PROGRAM_DIR}/src/{path.name}"] = sha256_file(path)
    return files


def uncommitted_sources(root: Path, commit: str, files: dict[str, str]) -> list[str]:
    """Recorded source files whose bytes on disk are not the bytes at `commit`.

    A provenance entry that names a commit while holding a working-tree hash of a file that
    commit never had is a lie about both. `write` refuses to make it.
    """
    differs: list[str] = []
    for name in files:
        try:
            committed = git(root, "rev-parse", f"{commit}:{name}").strip()
        except ProvenanceError:
            differs.append(name)
            continue
        try:
            on_disk = git(root, "hash-object", name).strip()
        except ProvenanceError:
            differs.append(name)
            continue
        if committed != on_disk:
            differs.append(name)
    return differs


def program_id(root: Path) -> tuple[str | None, str | None]:
    """The deployed program id if the tree states one, and where it was read from."""
    path = root / PROGRAM_ID_SOURCE
    if not path.is_file():
        return None, None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProvenanceError(f"cannot read {PROGRAM_ID_SOURCE}: {exc}") from exc
    value = data.get(PROGRAM_ID_KEY) if isinstance(data, dict) else None
    if not isinstance(value, str) or not value:
        return None, None
    return value, f"{PROGRAM_ID_SOURCE}#{PROGRAM_ID_KEY}"


# -- write -----------------------------------------------------------------------


def _entry(root: Path, version: Version, rebuilds: list[tuple[str, Path]]) -> dict:
    commit = source_commit(root, version)
    if version.scope == "tree":
        files = source_files_from_tree(root)
        differs = uncommitted_sources(root, commit, files)
        if differs:
            raise ProvenanceError(
                "the working tree differs from the commit it is recorded against for "
                + ", ".join(sorted(differs))
                + "; commit the source, then rebuild and record it"
            )
        extraction = f"built in place from the working tree, cwd {PROGRAM_DIR}"
    else:
        files = source_files_from_commit(root, commit)
        extraction = (
            "the files above were read out of the commit with `git show <commit>:<path>` "
            "into a scratch crate directory, Cargo.toml and src/ at its root, and the "
            "command above was run with cwd set to that directory. Their repo paths, which "
            "are the keys of source_files, are the paths the same files have in the commit"
        )

    binary_path = f"{PROGRAM_DIR}/target/deploy/{version.binary}"
    binary = root / binary_path
    if not binary.is_file():
        raise ProvenanceError(
            f"no binary at {binary_path}; build it first (the README has the command)"
        )

    subject = git(root, "log", "-1", "--format=%s", commit).strip()

    if version.label in PROGRAM_ID_VERSIONS:
        deployed, origin = program_id(root)
        if deployed is None:
            note = (
                f"the tree states no program id ({PROGRAM_ID_SOURCE} carries no "
                f"{PROGRAM_ID_KEY}); none is invented here"
            )
        else:
            note = (
                "the program id is a property of the deploy keypair, not of the crate: "
                "lib.rs says so, and the Rust source declares none. This is the id the "
                f"tree records for this version, read from {origin}"
            )
    else:
        deployed, origin = None, None
        note = (
            "this version has only ever run on a local validator under a keypair of its "
            "own, and that run's record is git-ignored rather than part of the tree, so the "
            "tree states no id for it and none is invented here. The id is a property of "
            "the deploy keypair, not of the crate"
        )

    independent: list[dict] = []
    for label, path in rebuilds:
        if label != version.label:
            continue
        independent.append(
            {
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    for item in independent:
        item["identical"] = item["sha256"] == sha256_file(binary)

    return {
        "program": _lib_name(root, version, commit),
        "version": version.label,
        "source_commit": commit,
        "source_commit_short": commit[:7],
        "source_commit_subject": subject,
        "source_scope": version.scope,
        "source_files": files,
        "program_id": deployed,
        "program_id_source": origin,
        "program_id_note": note,
        "source_extraction": extraction,
        "binary": {
            "path": binary_path,
            "sha256": sha256_file(binary),
            "bytes": binary.stat().st_size,
        },
        "rebuilds": independent,
        "reproducible": all(item["identical"] for item in independent)
        if independent
        else None,
    }


def _lib_name(root: Path, version: Version, commit: str) -> str:
    """The program's name, from the `[lib] name` of the Cargo.toml the build used."""
    if version.scope == "tree":
        text = (root / PROGRAM_DIR / "Cargo.toml").read_text(encoding="utf-8")
    else:
        text = git_blob(root, f"{commit}:{PROGRAM_DIR}/Cargo.toml").decode("utf-8")
    name = cargo_lib_name(text)
    if not name:
        raise ProvenanceError(
            f"the Cargo.toml for {version.label} has no [lib] name, so the program has no "
            "name to record"
        )
    return name


def _lockfile(root: Path) -> dict:
    """The dependency pins: generated, git-ignored, and the one part of the build not in git."""
    path = root / PROGRAM_DIR / "Cargo.lock"
    return {
        "lockfile": f"{PROGRAM_DIR}/Cargo.lock",
        "lockfile_sha256": sha256_file(path) if path.is_file() else None,
        "lockfile_tracked": False,
        "note": (
            "cargo-build-sbf generates this pin file and .gitignore keeps it out of the "
            "tree, so the dependency set is not committed. The two measured builds resolved "
            "to the same lockfile on one machine, which is part of why the bytes agree; a "
            "rebuild after the registry moves could resolve different versions and is the "
            "one way the same source can produce different bytes."
        ),
    }


def _rebuilds(values: list[str]) -> list[tuple[str, Path]]:
    parsed: list[tuple[str, Path]] = []
    known = {version.label for version in VERSIONS}
    for value in values:
        label, _, raw = value.partition("=")
        label = label.strip()
        if not raw or label not in known:
            raise ProvenanceError(
                f"--rebuild takes version=path with version one of "
                f"{', '.join(sorted(known))}; got {value!r}"
            )
        path = Path(raw)
        if not path.is_file():
            raise ProvenanceError(f"--rebuild names a file that is not there: {raw}")
        parsed.append((label, path))
    return parsed


def cmd_write(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    out = Path(args.path).resolve() if args.path else root / ARTEFACT_PATH
    rebuilds = args.rebuild or []
    try:
        rebuilds = _rebuilds(rebuilds)
        entries = [_entry(root, version, rebuilds) for version in VERSIONS]
        document = {
            "schema": SCHEMA,
            "generated_at": utc_now(),
            "generated_by": "tools/build_provenance.py write",
            "verify_with": "python3 tools/build_provenance.py verify",
            "program_dir": PROGRAM_DIR,
            "toolchain": toolchain_versions(),
            "build": {
                "command": BUILD_COMMAND,
                "out_dir_note": (
                    "--sbf-out-dir only chooses where the .so and a program keypair are "
                    "copied; the bytes do not depend on it, and the two measured builds "
                    "wrote to scratch directories and were then copied to binary.path. It "
                    "is kept off its default here because cargo-build-sbf writes a program "
                    f"keypair beside the .so and {PROGRAM_DIR}/target/deploy/"
                    "cap_hook-keypair.json is the frozen devnet keypair path"
                ),
                "reproducibility": (
                    "measured, not proven: the command was run twice, in two independent "
                    "directories, and the two .so files were compared byte for byte. The "
                    "hashes are under each version's rebuilds, and `reproducible` is true "
                    "when every supplied rebuild matched the recorded binary"
                ),
            },
            "dependency_resolution": _lockfile(root),
            "programs": entries,
        }
    except ProvenanceError as exc:
        sys.stderr.write(f"build_provenance.py: {exc}\n")
        return EXIT_UNREADABLE

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    label = _relative(out, root)
    sys.stdout.write(f"{label}: wrote {len(entries)} program(s)\n")
    for entry in entries:
        binary = entry["binary"]
        sys.stdout.write(
            f"  {entry['version']} {entry['program']} from {entry['source_commit_short']}: "
            f"{binary['bytes']} bytes sha256 {binary['sha256']}\n"
        )
    return EXIT_OK


# -- verify ----------------------------------------------------------------------


def _relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.name


def _check_shape(entry: dict) -> list[str]:
    problems: list[str] = []
    for key in ("program", "version", "source_commit", "source_scope", "source_files"):
        if not entry.get(key):
            problems.append(f"shape: a program entry has no {key}")
    binary = entry.get("binary")
    if not isinstance(binary, dict) or not all(
        binary.get(key) for key in ("path", "sha256", "bytes")
    ):
        problems.append(
            f"shape: {entry.get('version', '<unnamed>')} has no binary path/sha256/bytes"
        )
    return problems


def _check_entry(root: Path, entry: dict) -> list[str]:
    problems: list[str] = []
    shape = _check_shape(entry)
    if shape:
        return shape

    version = entry["version"]
    commit = entry["source_commit"]
    scope = entry["source_scope"]

    try:
        git(root, "cat-file", "-e", f"{commit}^{{commit}}")
    except ProvenanceError:
        problems.append(
            f"source-commit: {version} names {commit[:12]}, which does not resolve in this "
            "repository: the commit it was built from is gone"
        )

    for name, recorded in sorted(entry["source_files"].items()):
        where = f"source-file: {version} {name}"
        try:
            if scope == "commit":
                actual = sha256_bytes(git_blob(root, f"{commit}:{name}"))
            elif scope == "tree":
                path = root / name
                if not path.is_file():
                    problems.append(f"{where} is recorded but is not in the tree")
                    continue
                actual = sha256_file(path)
            else:
                problems.append(f"{where} has an unknown source scope {scope!r}")
                continue
        except ProvenanceError:
            problems.append(f"{where} cannot be read from {scope} {commit[:12]}")
            continue
        if actual != recorded:
            problems.append(
                f"{where} is recorded as {recorded} and is now {actual}: the source changed "
                "after the binary was built"
            )

    binary = entry["binary"]
    path = root / binary["path"]
    if not path.is_file():
        problems.append(f"binary: {version} records {binary['path']}, which is absent")
    else:
        actual = sha256_file(path)
        if actual != binary["sha256"]:
            problems.append(
                f"binary: {version} {binary['path']} is recorded as sha256 "
                f"{binary['sha256']} and is now {actual}"
            )
        size = path.stat().st_size
        if size != binary["bytes"]:
            problems.append(
                f"binary: {version} {binary['path']} is recorded as {binary['bytes']} "
                f"bytes and is now {size}"
            )

    deployed = entry.get("program_id")
    origin = entry.get("program_id_source")
    if deployed and origin:
        stated, now_origin = program_id(root)
        if stated != deployed:
            problems.append(
                f"program-id: {version} records {deployed} from {origin}, and the tree now "
                f"states {stated if stated else 'none'}"
            )
        elif now_origin != origin:
            problems.append(
                f"program-id: {version} records {deployed} from {origin}, which no longer "
                "carries it"
            )

    return problems


def cmd_verify(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    path = Path(args.path).resolve() if args.path else root / ARTEFACT_PATH
    label = _relative(path, root)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        sys.stderr.write(f"build_provenance.py: cannot read {label}: {exc}\n")
        return EXIT_UNREADABLE
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"build_provenance.py: {label} is not JSON: {exc}\n")
        return EXIT_UNREADABLE

    if not isinstance(document, dict) or document.get("schema") != SCHEMA:
        sys.stderr.write(
            f"build_provenance.py: {label} does not declare schema {SCHEMA}\n"
        )
        return EXIT_UNREADABLE
    entries = document.get("programs")
    if not isinstance(entries, list) or not entries:
        sys.stderr.write(f"build_provenance.py: {label} records no programs\n")
        return EXIT_UNREADABLE

    try:
        violations: list[str] = []
        for entry in entries:
            if not isinstance(entry, dict):
                violations.append(
                    f"shape: a program entry is {type(entry).__name__}, not an object"
                )
                continue
            violations.extend(_check_entry(root, entry))
    except ProvenanceError as exc:
        sys.stderr.write(f"build_provenance.py: {exc}\n")
        return EXIT_UNREADABLE

    if violations:
        for line in violations:
            sys.stdout.write(f"{label}: {line}\n")
        sys.stdout.write(
            f"build_provenance: {len(violations)} violation(s), "
            f"{len(entries)} program(s) checked\n"
        )
        return EXIT_VIOLATION

    if not args.quiet:
        summary = ", ".join(
            f"{entry['version']} {entry['binary']['sha256'][:8]}"
            for entry in entries
        )
        sys.stdout.write(f"build_provenance: ok, {len(entries)} program(s): {summary}\n")
    return EXIT_OK


# -- command line ----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="build_provenance.py",
        description=(
            "Record which source and which toolchain produced a program binary, and fail "
            "when that record stops being true."
        ),
    )
    verbs = parser.add_subparsers(dest="verb", required=True)

    write = verbs.add_parser(
        "write",
        help="record what is on disk and what git says; builds nothing",
        description=(
            "Write the provenance artefact from the binaries already on disk. It records, "
            "it does not build, and it refuses to record a working-tree hash against a "
            "commit that never held those bytes."
        ),
    )
    write.add_argument("--root", default=str(REPO_ROOT), help="repository root")
    write.add_argument(
        "--path", default=None, help=f"where to write (default {ARTEFACT_PATH})"
    )
    write.add_argument(
        "--rebuild",
        action="append",
        default=[],
        metavar="VERSION=PATH",
        help=(
            "an independently built .so to compare with the recorded one, e.g. "
            "v2=build/cap_hook.so; repeatable, and only its hash is recorded"
        ),
    )
    write.set_defaults(handler=cmd_write)

    verify = verbs.add_parser(
        "verify",
        help="fail when the record no longer holds",
        description=(
            "Re-derive the source hashes and the binary hash and fail, one line per "
            "violation, on any disagreement."
        ),
    )
    verify.add_argument("--root", default=str(REPO_ROOT), help="repository root")
    verify.add_argument(
        "--path", default=None, help=f"which artefact to check (default {ARTEFACT_PATH})"
    )
    verify.add_argument("--quiet", action="store_true", help="say nothing when clean")
    verify.set_defaults(handler=cmd_verify)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse's own usage error, already printed
        code = exc.code
        return code if isinstance(code, int) else EXIT_UNREADABLE
    return args.handler(args)


if __name__ == "__main__":
    sys.exit(main())

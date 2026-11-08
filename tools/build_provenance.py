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
  - the program id each version runs under, read from the place in the tree that states it
    and never invented: v1's from `records/devnet-artefacts.json`, the frozen devnet record,
    and v2's from `PROGRAM_IDS["v2"]` in `market_swarm/gateway.py`, which is where the code
    says which address a run is talking to. The symbol the value came from is recorded
    beside it, and `verify` re-reads the same symbol -- so an edit to that table fails the
    check instead of passing it. `lib.rs` says in its header that the id is a property of the
    deploy keypair rather than of the crate, which is why reading it out of the tree is the
    only honest way to get one;
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
  2. source-set    a compiled source file is not in the record at all: a `.rs` under `src/`
                   at any depth, or a crate-root `build.rs`, that the recorded set lacks. The
                   reverse direction is checked too for a file built from a commit, whose
                   file set is fixed and must match exactly. Without this, a file added or
                   edited after the build is hashed by nobody.
  3. source-commit the recorded commit no longer resolves in this repository. History has
                   been rewritten here once already; a provenance file whose commit is
                   gone is a file that has stopped meaning anything.
  4. binary        the recorded `.so` is absent, or its sha256 or size differs from the
                   recorded value.
  5. program-id    every version the tree states an id for carries that id and says where it
                   was read from. An entry that states no id where the tree states one, an
                   id with no source, an id the tree no longer states, and an id the tree
                   now states differently are four separate violations. The id is what a run
                   is talking to, so silence about it is the failure this check ends.
  6. reproducible  `reproducible` is not the value the recorded rebuilds imply. It is true
                   only when there is at least one rebuild and every one of them hashes to
                   the recorded binary; a rebuild that does not hash to the binary is a
                   violation on its own line.
  7. toolchain     a toolchain line is missing, is not a version line for the binary it
                   names, or -- when that binary is on PATH, so the version can be read --
                   differs from what the installed toolchain prints. On a machine without
                   the Solana toolchain these lines are reported as not re-derived instead
                   of being claimed.
  8. lockfile      the git-ignored `Cargo.lock` is on disk and does not hash to the recorded
                   value. Absent, it is reported as not checked: the pins are not in git.
  9. shape         an entry is missing a field the other checks need.

Exit codes: 0 clean, 1 any violation, 2 the artefact or the repository could not be read
(bad JSON, git refused, the toolchain is not on PATH for `write`).

Paths in the artefact are repo-relative and the output carries no pid and no port: this
repository is public, and `tools/public_safety.py` refuses an absolute home path. The
scratch directory a build is copied out of is therefore never recorded -- only the bytes
that came out of it.

What it does not claim. Reproducibility here is *measured*, not proven: the command was run
again in independent directories, every `.so` it produced is recorded under `rebuilds`, and
`verify` compares those hashes with the recorded binary on every run. `verify` does not
re-run the build; re-running it is the reader's own check, and `build.command` is written so
that check is one line. Which fields `verify` re-derives and which it can only quote is
written into the artefact itself under `verify_checks`, so a reader checks the claim against
the code instead of taking it from this docstring. The dependency pins are the one thing
that is not in the tree at all: `cargo-build-sbf` generates `Cargo.lock` and `.gitignore`
keeps it out, so a rebuild resolves its dependencies from whatever the registry holds at
that moment. The tool records the lockfile hash it saw, re-checks it whenever the file is on
disk, and says so in the artefact rather than pretending the pins are committed.
"""

from __future__ import annotations

import argparse
import ast
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

#: Where each version's program id is stated in the tree, and the symbol that states it.
#:
#: This is a table of *places*, not of values: a value typed here would be a second copy of
#: the id, and the whole point of the check is that there is one. `records` reads a JSON key;
#: `code` reads a module-level dict literal out of a Python file with `ast`, so the package is
#: parsed and never imported -- reading the code that states the id must not mean running it.
#:
#: label -> (kind, path, key). `key` is the JSON key for `records` and the dict name for
#: `code`; the version label is the dict key inside a `code` table.
PROGRAM_ID_SOURCES: dict[str, tuple[str, str, str]] = {
    "v1": ("records", "records/devnet-artefacts.json", "programId"),
    "v2": ("code", "market_swarm/gateway.py", "PROGRAM_IDS"),
}

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

#: binary -> the key its version line lands under in the record. A table rather than a string
#: transform because `solana --version` prints a `solana-cli` line: the binary is `solana`,
#: the tool it reports is `solana-cli`, and verify has to look up the second to check the
#: first.
TOOLCHAIN_KEYS = (("cargo-build-sbf", "cargo_build_sbf"), ("solana", "solana_cli"))

#: The files a build of this crate compiles, as the paths the commit holds them at: the
#: manifest, a crate-root `build.rs` when the crate has one, and every `.rs` file under `src/`
#: at any depth. Depth matters: a nested `src/sub/mod.rs` is compiled exactly like
#: `src/lib.rs`, and a set that stops at the top directory leaves it hashed by nobody, so an
#: edit to it after the build is invisible.
SOURCE_FILE = re.compile(
    rf"^{re.escape(PROGRAM_DIR)}/(?:Cargo\.toml|build\.rs|src/.+\.rs)$"
)

#: Every child process this tool starts is bounded. A `git` that blocks -- on a lock, on a
#: wedged filesystem, on a prompt nobody can see -- would otherwise hold a gate open forever,
#: and a gate that can hang is a gate that gets skipped. The ceiling is generous because the
#: slowest thing here is `cargo-build-sbf --version`, which reads the whole platform-tools
#: tree once; nothing this tool runs should take a minute, so a minute is a fault, not a wait.
COMMAND_TIMEOUT_SECONDS = 60.0


class ProvenanceError(RuntimeError):
    """The record cannot be written or read: git refused, a path is missing, no toolchain."""


class CommandTimeout(ProvenanceError):
    """A child this tool started did not finish inside COMMAND_TIMEOUT_SECONDS.

    Its own class because it is not a statement about the record: a `git` that hangs is a
    broken machine, not a stale hash, and reporting it as a violation would put a fault of
    the verifier into a list of faults of the artefact. It exits 2, with the command named.
    """


def _run(
    argv: list[str], *, text: bool = False, check_message: str | None = None
) -> subprocess.CompletedProcess:
    """`subprocess.run` with a ceiling on every call, so no child can hold the tool open."""
    try:
        return subprocess.run(
            argv,
            capture_output=True,
            text=text,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as exc:
        raise CommandTimeout(
            f"{check_message or argv[0]} did not finish within "
            f"{COMMAND_TIMEOUT_SECONDS:g}s and was killed; a child that hangs is a fault, "
            "not a slow machine"
        ) from exc


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
    done = _run(
        ["git", "-C", str(root), *args],
        text=True,
        check_message=f"git {' '.join(args)}",
    )
    if done.returncode != 0:
        raise ProvenanceError(
            f"git {' '.join(args)} failed in the repository: {done.stderr.strip()}"
        )
    return done.stdout


def git_blob(root: Path, spec: str) -> bytes:
    """The bytes of one blob, `commit:path` or a sha. Read from git, not from the tree."""
    done = _run(
        ["git", "-C", str(root), "cat-file", "blob", spec],
        check_message=f"git cat-file blob {spec}",
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
        done = _run([binary, "--version"], text=True, check_message=f"{binary} --version")
        if done.returncode != 0:
            raise ProvenanceError(f"{binary} --version exited {done.returncode}")
        for line in done.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            name = line.split(None, 1)[0].replace("-", "_")
            versions[name] = line
    return versions


def toolchain_on_path() -> bool:
    """Whether every toolbox binary can be run here, so its version can be re-derived."""
    return all(shutil.which(binary) is not None for binary in TOOLCHAIN_BINARIES)


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
    """Every file this commit compiles -- `.rs` at any depth, `build.rs`, `Cargo.toml`."""
    listing = git(root, "ls-tree", "-r", "--name-only", commit, "--", PROGRAM_DIR)
    files: dict[str, str] = {}
    for name in sorted(line.strip() for line in listing.splitlines() if line.strip()):
        if not SOURCE_FILE.match(name):
            continue
        files[name] = sha256_bytes(git_blob(root, f"{commit}:{name}"))
    return files


def source_files_from_tree(root: Path) -> dict[str, str]:
    """The same set, read from disk: what a build in this worktree would compile now.

    `rglob`, not `glob`: a module at `src/sub/mod.rs` is compiled exactly like one at
    `src/sub.rs`, and a walk that stops at the first directory records a set that is missing
    files the binary contains. `build.rs` is hashed when the crate has one, because a build
    script decides the bytes as surely as a module does.
    """
    crate = root / PROGRAM_DIR
    cargo = crate / "Cargo.toml"
    if not cargo.is_file():
        raise ProvenanceError(f"no {PROGRAM_DIR}/Cargo.toml in the tree")
    files: dict[str, str] = {f"{PROGRAM_DIR}/Cargo.toml": sha256_file(cargo)}
    build_script = crate / "build.rs"
    if build_script.is_file():
        files[f"{PROGRAM_DIR}/build.rs"] = sha256_file(build_script)
    for path in sorted((crate / "src").rglob("*.rs")):
        if not path.is_file():
            continue
        files[f"{PROGRAM_DIR}/{path.relative_to(crate).as_posix()}"] = sha256_file(path)
    return files


def compiled_file_set(root: Path, scope: str, commit: str) -> dict[str, str]:
    """What the record *should* list for this scope, so a file it omits can be named.

    The hash check can only speak about files the record mentions, which is half a check: a
    module added to the tree after the build is compiled by nobody's rebuild and hashed by
    nobody's record. This is the other half.
    """
    if scope == "tree":
        return source_files_from_tree(root)
    return source_files_from_commit(root, commit)


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


def _dict_literals(source: str) -> dict[str, dict[str, str]]:
    """Every string-valued module-level dict literal in a Python file, by name.

    Parsed, never imported: `market_swarm/gateway.py` opens sockets and reads keyfiles when
    it is executed, and a provenance check that runs the package to learn a constant is a
    check that can start a validator. `ast.parse` reads the literal and stops there.
    """
    tables: dict[str, dict[str, str]] = {}
    for node in ast.parse(source).body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign) and node.value is not None:
            targets, value = [node.target], node.value
        if not isinstance(value, ast.Dict):
            continue
        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            entries: dict[str, str] = {}
            for key, item in zip(value.keys, value.values):
                if isinstance(key, ast.Constant) and isinstance(item, ast.Constant):
                    if isinstance(key.value, str) and isinstance(item.value, str):
                        entries[key.value] = item.value
            if entries:
                tables[target.id] = entries
    return tables


def stated_program_id(root: Path, label: str) -> tuple[str | None, str | None]:
    """The id the tree states for this version, and the symbol it was read from.

    Both halves are re-derived by `verify` from the same symbol, so an edit to the code that
    states the id fails the check. The value is never held in this file: a copy here would
    be a second place the id is stated and the first place it would drift.
    """
    kind, path_name, key = PROGRAM_ID_SOURCES[label]
    path = root / path_name
    if not path.is_file():
        return None, None
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ProvenanceError(f"cannot read {path_name}: {exc}") from exc
    if kind == "records":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ProvenanceError(f"cannot read {path_name}: {exc}") from exc
        value = data.get(key) if isinstance(data, dict) else None
        origin = f"{path_name}#{key}"
    else:
        try:
            table = _dict_literals(text).get(key, {})
        except SyntaxError as exc:
            raise ProvenanceError(f"cannot parse {path_name}: {exc}") from exc
        value = table.get(label)
        origin = f'{path_name}#{key}["{label}"]'
    if not isinstance(value, str) or not value:
        return None, None
    return value, origin


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

    deployed, origin = stated_program_id(root, version.label)
    kind, id_path, id_key = PROGRAM_ID_SOURCES[version.label]
    if deployed is None:
        note = (
            f"the tree states no program id for {version.label}: no {id_key} in {id_path}, "
            "so none is recorded and none is invented here. An absent id is a field the "
            "verify check reports as a violation the moment the tree states one"
        )
    else:
        note = (
            "the program id is a property of the deploy keypair, not of the crate: lib.rs "
            "says so and the Rust source declares none. This is the id the tree states for "
            f"this version, read from {origin}, and verify re-reads that same symbol, so an "
            "edit to it fails the check"
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
        if not item["identical"]:
            # A record is written to be verified, and `verify` fails a rebuild that does not
            # reproduce the binary. Writing one anyway would hand the reader a file that its
            # own gate rejects, so the refusal happens here, with both hashes named: the fix
            # is to find out why the two builds differ, not to record that they do.
            raise ProvenanceError(
                f"the rebuild supplied for {version.label} hashes to {item['sha256']}, not "
                f"to the recorded binary's {sha256_file(binary)}: the bytes did not "
                "reproduce, and a record cannot claim reproducibility it did not get. "
                "Investigate the two builds; nothing was written"
            )

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
                    "measured, not proven: the command was re-run in independent "
                    "directories and every .so it produced is recorded under that "
                    "version's rebuilds. `reproducible` is true only when there is at least "
                    "one rebuild and every one of them hashes to the recorded binary, and "
                    "write refuses to record a rebuild that did not: verify recomputes the "
                    "claim from the hashes on every run"
                ),
            },
            "dependency_resolution": _lockfile(root),
            "verify_checks": {
                "rederived": [
                    "each recorded source file's sha256, from the commit for a commit-scoped "
                    "version and from disk for a tree-scoped one",
                    "the compiled file set, so a `.rs` the record omits is a violation",
                    "that the recorded source commit still resolves",
                    "each binary's sha256 and byte size",
                    "each version's program id, from the same symbol write read it from",
                    "every rebuild's sha256 against the binary, and `reproducible` from those",
                    "the toolchain version lines, when both binaries are on PATH so they can "
                    "be run, and a printed note that they were not when they are not",
                    "the git-ignored lockfile's sha256, whenever the file is on disk",
                ],
                "not_rederived": [
                    "the build itself: verify never compiles anything, so `build.command` "
                    "is a quoted instruction and re-running it is the reader's own check",
                    "the toolchain version lines on a machine that does not have the "
                    "Solana toolchain installed; they are quoted at write time and verify "
                    "says so rather than implying it checked them",
                    "`dependency_resolution` when the lockfile is absent: the pins are "
                    "generated and git-ignored, so a fresh clone has none to compare",
                ],
            },
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
    for key in (
        "program",
        "version",
        "source_commit",
        "source_scope",
        "source_files",
        "rebuilds",
    ):
        if not entry.get(key) and not (key == "rebuilds" and entry.get(key) == []):
            problems.append(f"shape: a program entry has no {key}")
    if "source_files" in entry and not isinstance(entry["source_files"], dict):
        problems.append(
            f"shape: {entry.get('version', '<unnamed>')} source_files is "
            f"{type(entry['source_files']).__name__}, not a path-to-hash mapping"
        )
    # A version this tool does not know cannot be checked -- there is no place to read its
    # id from -- so it is a shape violation rather than a traceback in the middle of a gate.
    version = entry.get("version")
    if version and version not in PROGRAM_ID_SOURCES:
        problems.append(
            f"shape: {version} is not a version this record knows "
            f"({', '.join(sorted(PROGRAM_ID_SOURCES))})"
        )
    binary = entry.get("binary")
    if not isinstance(binary, dict) or not all(
        binary.get(key) for key in ("path", "sha256", "bytes")
    ):
        problems.append(
            f"shape: {entry.get('version', '<unnamed>')} has no binary path/sha256/bytes"
        )
    return problems


def _check_program_id(root: Path, version: str, entry: dict) -> list[str]:
    """The id the tree states, against the id the entry carries, in every direction.

    This is the check the record exists for: the id is what a run is talking to, and v2's
    identity is the whole subject of this branch. A missing field is a violation, never a
    skip -- the earlier form required both `program_id` and `program_id_source` to be present
    before checking anything, so deleting one line of JSON turned the check off.
    """
    problems: list[str] = []
    deployed = entry.get("program_id")
    origin = entry.get("program_id_source")
    stated, now_origin = stated_program_id(root, version)

    if deployed is not None:
        if not origin:
            problems.append(
                f"program-id: {version} records {deployed} and no program_id_source, so "
                "the reader cannot tell which statement of the id it is meant to equal"
            )
        if stated is None:
            problems.append(
                f"program-id: {version} records {deployed} from {origin or 'nowhere'}, and "
                f"the tree states no id for {version} at "
                f"{PROGRAM_ID_SOURCES[version][1]}"
            )
        elif deployed != stated:
            problems.append(
                f"program-id: {version} records {deployed} from {origin or 'nowhere'}, and "
                f"the tree now states {stated} at {now_origin}"
            )
        elif origin and origin != now_origin:
            problems.append(
                f"program-id: {version} records {deployed} from {origin}, which is not "
                f"where the tree states it ({now_origin})"
            )
    elif stated is not None:
        problems.append(
            f"program-id: {version} records no id, and the tree states {stated} at "
            f"{now_origin}: an id that is recorded as null cannot be checked"
        )
    return problems


def _check_rebuilds(version: str, entry: dict) -> list[str]:
    """`reproducible` against the hashes it claims to summarise, and each rebuild's hash."""
    problems: list[str] = []
    rebuilds = entry.get("rebuilds")
    binary = entry["binary"]
    if not isinstance(rebuilds, list):
        return [f"shape: {version} rebuilds is {type(rebuilds).__name__}, not a list"]

    for index, item in enumerate(rebuilds):
        where = f"rebuild: {version} rebuild {index + 1}"
        if not isinstance(item, dict):
            problems.append(f"{where} is {type(item).__name__}, not an object")
            continue
        digest = item.get("sha256")
        if not isinstance(digest, str) or not digest:
            problems.append(f"{where} carries no sha256")
            continue
        if digest != binary["sha256"]:
            problems.append(
                f"{where} hashes to {digest} and the recorded binary to "
                f"{binary['sha256']}: the rebuild did not reproduce the bytes"
            )
        elif item.get("identical") is not True:
            problems.append(
                f"{where} hashes to the binary and is recorded as identical "
                f"{item.get('identical')!r}"
            )
        if "bytes" in item and item["bytes"] != binary["bytes"]:
            problems.append(
                f"{where} is recorded as {item['bytes']} bytes and the binary is "
                f"{binary['bytes']}"
            )

    derived = (
        all(
            isinstance(item, dict) and item.get("sha256") == binary["sha256"]
            for item in rebuilds
        )
        if rebuilds
        else None
    )
    recorded = entry.get("reproducible")
    if recorded != derived:
        if derived is None:
            problems.append(
                f"reproducible: {version} claims {recorded!r} and records no rebuild to "
                "support it; a claim of reproducibility needs at least one"
            )
        else:
            problems.append(
                f"reproducible: {version} records {recorded!r} and its rebuilds imply "
                f"{derived!r}"
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
    except CommandTimeout:
        raise
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
                # A tree-scoped entry reads its bytes from disk, so resolving the commit says
                # nothing about whether that commit is the one the bytes came from. Measured: a
                # record naming v1's commit for v2 verified clean, because nothing compared the
                # two. This is that comparison, and it cannot fire on a healthy record: at write
                # time the tree and the commit are the same bytes, and an edit after the build is
                # already caught by the hash above.
                try:
                    committed = sha256_bytes(git_blob(root, f"{commit}:{name}"))
                except CommandTimeout:
                    raise
                except ProvenanceError:
                    problems.append(
                        f"source-commit: {version} names {commit[:12]}, and that commit has no "
                        f"{name}: the source it claims to have been built from is not there"
                    )
                else:
                    if committed != actual:
                        problems.append(
                            f"source-commit: {version} names {commit[:12]}, whose {name} is "
                            f"{committed}, while the tree holds {actual}: the recorded commit is "
                            "not the one these bytes came from"
                        )
            else:
                problems.append(f"{where} has an unknown source scope {scope!r}")
                continue
        except CommandTimeout:
            raise
        except ProvenanceError:
            problems.append(f"{where} cannot be read from {scope} {commit[:12]}")
            continue
        if actual != recorded:
            problems.append(
                f"{where} is recorded as {recorded} and is now {actual}: the source changed "
                "after the binary was built"
            )

    # The other half of the source check: a file that is compiled and not in the record is
    # hashed by nobody, so an edit to it is invisible. This is what a nested module or a
    # crate-root build.rs looked like before the set was widened.
    recorded_set = set(entry["source_files"])
    try:
        compiled = compiled_file_set(root, scope, commit)
    except CommandTimeout:
        raise
    except ProvenanceError:
        compiled = {}
    for name in sorted(set(compiled) - recorded_set):
        problems.append(
            f"source-set: {version} {name} is compiled by {scope} {commit[:12]} and is not "
            "in the record, so an edit to it after the build would be invisible"
        )
    if scope == "commit":
        for name in sorted(recorded_set - set(compiled)):
            problems.append(
                f"source-set: {version} records {name}, which {commit[:12]} does not contain"
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

    problems.extend(_check_program_id(root, version, entry))
    problems.extend(_check_rebuilds(version, entry))
    return problems


def _check_toolchain(document: dict) -> tuple[list[str], bool]:
    """The recorded version lines, and whether they were compared with the real toolchain.

    Re-derived only when both binaries can be run. A checkout without the Solana toolchain
    must still be able to verify the record, and the difference between "checked and equal"
    and "could not check" is printed either way rather than hidden behind a green run.
    """
    recorded = document.get("toolchain")
    if not isinstance(recorded, dict) or not recorded:
        return ["shape: the record carries no toolchain block"], False
    problems: list[str] = []
    for binary, key in TOOLCHAIN_KEYS:
        value = recorded.get(key)
        if not isinstance(value, str) or not value:
            problems.append(f"shape: the toolchain block has no {key} version line")
        elif not value.startswith(binary):
            problems.append(
                f"toolchain: {key} is recorded as {value!r}, which is not a version line "
                f"for {binary}"
            )
    if problems or not toolchain_on_path():
        return problems, False

    actual = toolchain_versions()
    for key, value in sorted(recorded.items()):
        if key in actual and value != actual[key]:
            problems.append(
                f"toolchain: the record quotes {key} as {value!r} and the installed "
                f"toolchain says {actual[key]!r}"
            )
    return problems, True


def _check_lockfile(root: Path, document: dict) -> tuple[list[str], bool]:
    """The pins, when the generated lockfile is on disk to be hashed."""
    resolution = document.get("dependency_resolution")
    if not isinstance(resolution, dict):
        return ["shape: the record carries no dependency_resolution block"], False
    recorded = resolution.get("lockfile_sha256")
    name = resolution.get("lockfile") or f"{PROGRAM_DIR}/Cargo.lock"
    path = root / name
    if not path.is_file():
        return [], False
    if not isinstance(recorded, str) or not recorded:
        return [f"shape: {name} is on disk and the record carries no lockfile_sha256"], True
    actual = sha256_file(path)
    if actual != recorded:
        return [
            f"lockfile: {name} is recorded as {recorded} and is now {actual}: the "
            "dependency pins moved, so the same source may no longer build these bytes"
        ], True
    return [], True


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

    checked: dict[str, bool] = {}
    try:
        violations: list[str] = []
        # Deleting a whole entry used to leave this green: the loop checks the entries that are
        # there, so the one that is not there is checked by nobody. Measured -- drop v1's entry
        # and `ok, 1 program(s)` came back at exit 0.
        recorded_versions = {
            entry.get("version") for entry in entries if isinstance(entry, dict)
        }
        for version in VERSIONS:
            if version.label not in recorded_versions:
                violations.append(
                    f"program-set: no entry for {version.label}, so its binary is pinned by "
                    "nothing here"
                )
        for entry in entries:
            if not isinstance(entry, dict):
                violations.append(
                    f"shape: a program entry is {type(entry).__name__}, not an object"
                )
                continue
            violations.extend(_check_entry(root, entry))
        toolchain_problems, toolchain_checked = _check_toolchain(document)
        violations.extend(toolchain_problems)
        checked["toolchain"] = toolchain_checked
        lockfile_problems, lockfile_checked = _check_lockfile(root, document)
        violations.extend(lockfile_problems)
        checked["lockfile"] = lockfile_checked
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
        # Said out loud, because a green run that silently skipped a check is the defect
        # this tool was written to fix.
        not_derived = [
            f"{name} ({reason})"
            for name, reason in (
                (
                    "toolchain",
                    "cargo-build-sbf and solana are not on PATH here",
                ),
                ("lockfile", "the git-ignored Cargo.lock is not on disk"),
            )
            if not checked.get(name)
        ]
        if not_derived:
            sys.stdout.write(
                "build_provenance: not re-derived on this machine: "
                + "; ".join(not_derived)
                + "\n"
            )
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
            "it does not build, and it refuses two things: a working-tree hash recorded "
            "against a commit that never held those bytes, and a rebuild that did not "
            "reproduce the binary. A record it writes always verifies."
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
            "Re-derive every field the tree or the disk can settle -- source hashes and the "
            "compiled file set, the commit, the binary, each version's program id, the "
            "rebuild hashes and the reproducible claim, the toolchain when it can be run, "
            "the lockfile when it is on disk -- and fail, one line per violation, on any "
            "disagreement or any missing field. A field it cannot re-derive is reported as "
            "not re-derived, never quietly skipped."
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

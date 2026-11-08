#!/usr/bin/env python3
"""doc_check.py: fail when the documentation disagrees with the code, or with itself.

The research record is the deliverable, and it is written by agents that also change the
code. That is how a document comes to describe nine instructions for a program that
implements four, name a file that was renamed two passes ago, or quote a program id the
devnet artefact no longer carries. None of those is a typo; each is a claim a reader will
check and find false. This checker is the gate. It is not a report: a violation exits 1.

    python3 tools/doc_check.py                     # every tracked markdown file
    python3 tools/doc_check.py --check paths       # one check, while writing a document
    python3 tools/doc_check.py --root <dir>        # a fixture tree, for the tests

Exit 0 clean, 1 any violation, 2 the tree could not be read (git refused, a required
file is missing where a check must read it). Violations print one per line as
`path:line: check: claim`, the shape `tools/public_safety.py` uses, so a log reader and
a test parse the same thing.

The seven checks, each one a claim that can be false:

  1. paths           every repo path a tracked .md names, in backticks or as a link
                     target, exists on disk -- unless git says `.gitignore` keeps it out
                     of the tree on purpose, which is not a claim about the tree.
  2. cross-refs      `records/findings/NN…` resolves to a file; every `§N.M` in
                     docs/ON-CHAIN-DESIGN.md resolves to a heading in that same file;
                     every `D<n>`/`Q<n>` has a `## D<n>`/`## Q<n>` heading in
                     records/F-decision-log.md.
  3. ids             the memo program ids quoted in README.md and
                     docs/ON-CHAIN-DESIGN.md are values of the table in
                     ticketpath/adapters/chain_client.py; the devnet program id and mint
                     quoted in README.md and records/STATE-OF-PROJECT.md are the ones in
                     records/devnet-artefacts.json.
  4. program-vs-doc  the error numbers in `TicketpathError`, the instruction tags in
                     `HookInstruction` and the seed literals of `pub fn *_seeds` in
                     programs/cap_hook/src/ equal the rows of the "implemented today"
                     table in docs/ON-CHAIN-DESIGN.md, both ways.
  5. registry-counts a registry that states a count of its own rows is stating the number
                     of rows present (records/C-, D-, E-…).
  6. feature-table   every row of the feature table in records/STATE-OF-PROJECT.md names
                     an existing file, and carries a status from the closed set. A row
                     claiming `tested` names an existing test file. A git-ignored path is
                     not a violation here either, and cannot be the test file either.
  7. findings-unique a reference to `records/findings/NN` (or `NN-a`) that lands on more
                     than one file is a violation, because the reader follows it into the
                     wrong one. A number with several claimants is reported as a warning on
                     every run and does not fail the gate: `00` and `02` pre-date the
                     collision that made this check, and a check that can only go green by
                     renaming the operator's record does more damage than the defect.

## An absent path: written down, or red

Some of the record names files that are deliberately not in the tree: a planning document
calls a script by the name it had before it shipped, a finding number was assigned and the
file never written, a handover sheet is kept out of git on purpose. Two mechanisms cover
them, and the difference between them is who owns the decision.

`ALLOWED_ABSENCES`, below `check_paths`, is for a path the tree will never have: one entry
per path, each with a reason. An entry with no reason (or one under four words) is itself a
violation and suppresses nothing; an entry suppresses only the absence of that exact path --
never an id, a cross-reference, a registry count or a feature row; and every run reports how
many absences it allowed, naming them under `--verbose`. The discipline is
`.public-denylist`'s, for the same reason: an exception that is not written beside its
argument is a rule nobody can review.

`.gitignore` is for a path the tree has on purpose and does not carry. The record cites a
local-validator artefact, a morning report page, a program's build output: they exist in the
checkout that produced them and in no clone, and `.gitignore` is the file that owns that
decision, so this checker asks it rather than keeping a second copy of the answer. One
`git check-ignore` covers every absent path a run finds; a hit means the document is naming
something the repository deliberately does not carry, which is not a claim about the tree.
Where git cannot answer -- no git on PATH, no work tree, a refused command -- every absent
path is judged by `exists()` as before, so a machine without git reports more violations
than one with it and never fewer.

## The two tables this checker reads, and their exact format

A checker that guesses at a table's shape checks its own guesses. Both tables are
therefore specified here, and a document that omits one gets a violation naming the
missing table rather than a crash or a silent pass.

### "implemented today" -- docs/ON-CHAIN-DESIGN.md, check 4

Any heading (`##`..`######`) whose text contains "implemented today", case-insensitive,
followed by the first markdown table under it:

    | kind | name | value | where |
    |---|---|---|---|
    | error | AmountNotOne | 6008 | `execute`, amount != 1 |
    | instruction | InitializeRecord | 1 | creates the mint's record |
    | seed | record_seeds | record | per-mint record PDA |

  * The header cells are exactly `kind`, `name`, `value`, `where`, in that order.
    Backticks and bold are tolerated; the words are not.
  * `kind` is one of `error`, `instruction`, `seed`.
  * `error`:    name = the Rust variant, value = its number (6008).
  * `instruction`: name = the Rust variant, value = its wire tag (0..3).
  * `seed`:     name = the Rust function (`record_seeds`), value = the byte literal it
                seeds with (`record`).
  * `where` is prose, unchecked.

The comparison is both ways: an item in the code and not in the table is a violation,
and so is an item in the table that the code no longer has.

### feature table -- records/STATE-OF-PROJECT.md, check 6

Any heading whose text contains "feature", followed by the first markdown table under it.
The header must carry a name column (`feature` or `item`), a status column (`status` or
`state`) and an evidence column (`file`, `path`, `test`, `evidence` or `where`):

    | feature | status | file |
    |---|---|---|
    | memo program id per cluster | tested | `tests/test_chain_client.py` |

The status of a row is one of, exactly:

    built        the code is in the tree and the row names it
    tested       a named command was run; the row names the test file
    unverified   stated where it is, and what would verify it
    not built    not started

## What this checker deliberately does not check

  * Prose that is true or false, and numbers nothing else carries: no checker can read
    "the cap is fixed at event creation" and know whether the program does that. Only
    the two tables above are machine-read claims of implementation.
  * A fourth kind of anything. The instruction *set* is read from the `unpack` match
    arms, not from a comment, so a comment that says "nine instructions" is not a claim
    this checker judges; the table is.
  * Counts of hits, test totals, line counts, hash values: numbers that move every time
    anyone runs anything. A gate that fails because a test count moved would be switched
    off within a day, and a switched-off gate is worse than none.
  * A path with a glob, a `<placeholder>`, a URL, a `~` or a leading `..`: it is not a
    claim about *this* tree. `../ticketing-frontend/lib/types.ts` is the sibling
    checkout, and this checker must not pretend to know whether it is there.
  * A bare filename (`README.md`) and a path with no extension (`records/findings/22`):
    the first is ambiguous across 40 directories, and the second belongs to check 2,
    which resolves it against the findings directory properly.
  * A reference the sentence itself says is absent ("`records/findings/22` does not
    exist"), and a `§`/`D`/`Q` reference whose paragraph names another document
    (`03-b` Q6 is 03-b's question, not this log's). Both are honest statements this
    checker would otherwise call lies.
  * The network, git history, and anything written. It reads files, one `git ls-files`
    and one `git check-ignore`, and it writes nothing, so it is safe inside a commit hook.

Standard library only, no dependency, and no network module is imported anywhere below.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The checks, in the order their violations print. `--check` takes one of these names.
CHECKS = (
    "paths",
    "cross-references",
    "findings-unique",
    "ids",
    "program-vs-doc",
    "registry-counts",
    "feature-table",
)

#: Where the documents this checker reads against live. Named once so a move breaks in
#: one place, loudly, instead of five checks quietly checking nothing.
DESIGN_DOC = "docs/ON-CHAIN-DESIGN.md"
DECISION_LOG = "records/F-decision-log.md"
FINDINGS_DIR = "records/findings"
ARTEFACT = "records/devnet-artefacts.json"
CHAIN_CLIENT = "ticketpath/adapters/chain_client.py"
#: The whole program, not only its `lib.rs`. The hook was one file when this check was
#: written and is now a small module tree (`error.rs`, `state.rs`, `lib.rs`), so a parser
#: that read one file would report an empty set of errors and seeds -- and an empty set is
#: not a pass here, it is every table row reported as "not in the code". A directory read
#: is the only shape that survives the program being split.
PROGRAM_SRC_DIR = "programs/cap_hook/src"
STATE_DOC = "records/STATE-OF-PROJECT.md"
REGISTRIES = (
    "records/C-variable-registry.md",
    "records/D-model-registry.md",
    "records/E-data-source-registry.md",
)

#: The top-level directories and files a backticked path is allowed to belong to. Anything
#: else is either not a path at all (`docs/CLI.md#gate` after the anchor is stripped is a
#: path) or is handled by another check. A closed set is what keeps check 1 from judging
#: `lib/api.ts` as a claim about this tree: the frontend's own documents name their files
#: the way their readers do, from the frontend root, and its internal paths are its own
#: business. `frontend` is in the set because a root document naming `frontend/README.md`
#: is making a claim about this tree, and that one is checked.
TOP_LEVEL = frozenset(
    {
        "tools",
        "ticketpath",
        "tests",
        "records",
        "docs",
        "programs",
        "market_swarm",
        "fixtures",
        ".githooks",
        "frontend",
        "AGENTS.md",
        "README.md",
        "RESEARCH-PROGRAM.md",
    }
)

#: A candidate path: segments of path characters and nothing else. This single regex is
#: what makes globs, `<placeholders>`, URLs, `~` and prose-with-spaces not-a-path.
PATH_SHAPE = re.compile(r"^[A-Za-z0-9._-]+(?:/[A-Za-z0-9._-]+)+$")
EXTENSION = re.compile(r"\.[A-Za-z0-9]{1,6}$")
INLINE_CODE = re.compile(r"`([^`\n]+)`")
LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")

BASE58 = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")

#: Program ids that are not this project's, quoted legitimately by a document that is
#: explaining the chain: the loaders, the two token programs, the ATA program, the
#: ed25519 and compute-budget programs, the system program and the wrapped-SOL mint.
#: A document may name any of these forever; it may not name a *ticket* id that the
#: artefact does not record.
KNOWN_PROGRAM_IDS = frozenset(
    {
        "BPFLoaderUpgradeab1e11111111111111111111111",
        "BPFLoader2111111111111111111111111111111111",
        "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA",
        "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
        "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL",
        "Ed25519SigVerify111111111111111111111111111",
        "ComputeBudget111111111111111111111111111111",
        "So11111111111111111111111111111111111111112",
        "MetaqbxxUerdq28cj1RbAWkYQm3ybzjb6a8bt518x1s",
        "11111111111111111111111111111111",
    }
)

#: The closed status vocabulary of the feature table. Nothing else may appear, so the
#: difference between "we tested it" and "we believe it" cannot be lost in a synonym.
FEATURE_STATUSES = ("built", "tested", "unverified", "not built")

#: Where a test suite lives in this tree. There are two: the root `tests/`, and
#: `market_swarm/tests/`, because `market_swarm` is a self-contained package with its own
#: suite, run with `python3 -m unittest discover -s market_swarm/tests -t .`. A rule that
#: knew only the root directory made a `tested` row impossible for anything tested there,
#: which forces the document to call a tested feature `built`: the tool understating the
#: work, which is the one thing a documentation check must never cause.
TEST_DIRS = ("tests", "market_swarm/tests")


def is_test_file(path: str) -> bool:
    """Is this path a test module in one of this tree's suites?"""
    return any(
        path.startswith(f"{directory}/test_") and path.endswith(".py")
        for directory in TEST_DIRS
    )

#: The three row kinds the implemented-today table may carry.
PROGRAM_KINDS = ("error", "instruction", "seed")

#: Noun stems that make `<n> <noun> in §X.Y` a count of rows rather than a reference to
#: something in a section. A number followed by any other phrase is not a count claim.
COUNT_NOUNS = ("row", "variable", "feature", "source", "model", "interaction")


@dataclass(frozen=True)
class Violation:
    """One claim that is not true, with the line that makes it."""

    check: str
    path: str
    line: int
    detail: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.check}: {self.detail}"


class Unreadable(Exception):
    """The tree could not be read where a check must read it. Exit 2, never a pass."""


# ---------------------------------------------------------------------------
# reading the tree
# ---------------------------------------------------------------------------


def tracked_markdown(root: Path) -> list[str]:
    """Every tracked `.md`, from git. Falls back to the tree on disk outside a repo.

    Git is the authority because the repository is what gets published: an untracked
    handover sheet in `tmp/` is full of paths that exist only on this machine, and
    judging a published document by it would be judging the wrong corpus. The fallback
    exists so the tests can hand this module a fixture directory with no `.git` in it.
    """
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--", "*.md"],
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        done = None
    if done is not None and done.returncode == 0:
        names = [part for part in done.stdout.decode("utf-8", "replace").split("\0") if part]
        if names:
            return sorted(names)
    ignored = {"tmp", "scratch", ".git", "runs", "node_modules", "target", "__pycache__"}
    found = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part in ignored for part in relative.parts):
            continue
        found.append(relative.as_posix())
    return sorted(found)


def read_lines(root: Path, relative: str) -> list[str]:
    """A file's lines. Absent is [] and never an exception: the caller decides meaning."""
    try:
        return (root / relative).read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return []


def require_lines(root: Path, relative: str) -> list[str]:
    """A file a check cannot work without. Absent is a violation, said out loud."""
    lines = read_lines(root, relative)
    if not lines:
        raise Unreadable(f"{relative} is missing or empty, and a check reads it")
    return lines


def split_row(line: str) -> list[str]:
    """A markdown table row's cells, with `\\|` treated as a cell's own pipe.

    `records/STATE-OF-PROJECT.md` carries `git ls-files records/findings \\| wc -l` inside
    a cell. Splitting naively on `|` would put that command's tail in the next column and
    shift every cell after it, which is exactly the kind of silent mis-parse a checker
    must not have.
    """
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells, current, escaped = [], [], False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return cells


def is_table_row(line: str) -> bool:
    return line.strip().startswith("|")


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{2,}:?", cell.strip()) for cell in cells if cell.strip())


@dataclass
class Table:
    """A markdown table: its header, and its rows with the line each sits on."""

    header: list[str]
    line: int
    rows: list[tuple[int, list[str]]]

    def column(self, *names: str) -> int | None:
        """The index of the first cell whose words include one of `names`.

        Matched by word, not by equality: a header written `Code path` and one written
        `File` are both an evidence column, and a checker that demands one spelling turns
        a naming choice into a gate failure.
        """
        for index, cell in enumerate(self.header):
            plain = re.sub(r"[`*]", "", cell).strip().lower()
            for name in names:
                if re.search(rf"\b{re.escape(name)}\b", plain):
                    return index
        return None


def tables_in(lines: list[str], start: int = 0, end: int | None = None) -> list[Table]:
    """Every table between `start` and `end`, fences skipped.

    A fenced code block holds examples of tables in at least three documents here, and
    reading an example as the table would compare the code against a quotation of some
    earlier version of itself.
    """
    stop = len(lines) if end is None else min(end, len(lines))
    found: list[Table] = []
    fenced = False
    index = start
    while index < stop:
        line = lines[index]
        if line.strip().startswith("```"):
            fenced = not fenced
            index += 1
            continue
        if fenced or not is_table_row(line):
            index += 1
            continue
        header = split_row(line)
        header_line = index + 1
        index += 1
        rows: list[tuple[int, list[str]]] = []
        while index < stop and is_table_row(lines[index]):
            cells = split_row(lines[index])
            if not is_separator(cells):
                rows.append((index + 1, cells))
            index += 1
        found.append(Table(header=header, line=header_line, rows=rows))
    return found


def headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(index, level, title) for every heading, fences skipped."""
    out = []
    fenced = False
    for index, line in enumerate(lines):
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if match:
            out.append((index, len(match.group(1)), match.group(2).strip()))
    return out


def paragraph_before(lines: list[str], index: int) -> list[str]:
    """The contiguous non-blank block a line sits in, for context a single line lacks."""
    start = index
    while start > 0 and lines[start - 1].strip():
        start -= 1
    end = index
    while end + 1 < len(lines) and lines[end + 1].strip():
        end += 1
    return lines[start : end + 1]


# ---------------------------------------------------------------------------
# check 1: paths
# ---------------------------------------------------------------------------


def looks_like_repo_path(text: str) -> bool:
    """Is this backticked text a claim about a file in *this* tree?

    The whole rule is `PATH_SHAPE`: it admits letters, digits, dot, dash, underscore and
    `/`, and nothing else, which is what excludes a URL, a glob, a `<placeholder>`, a
    shell command with a space in it and a `~`. The three extra conditions are the ones
    that keep the check narrow enough to trust: it must have more than one segment (so a
    bare filename is not judged across forty directories), the last segment must carry an
    extension (so `records/findings/22` is left to check 2), and the first segment must be
    one of this repository's, which is how a path into some directory outside the tree is
    not this repo's problem.
    """
    if not PATH_SHAPE.match(text):
        return False
    segments = text.split("/")
    if not EXTENSION.search(segments[-1]):
        return False
    return segments[0] in TOP_LEVEL


#: Paths a document may name without the file being in the tree, one entry per path, each
#: with a reason a reader can check against the tree in a minute. This is the discipline of
#: `.public-denylist`: the rule lives in data beside its reason, a reason is mandatory and
#: has to be arguable, and an exception is per path and per class rather than a blanket.
#:
#: What an entry suppresses, and what it cannot: it suppresses *one* thing, the absence of
#: that exact path. It does not suppress an id, a cross-reference, a registry count or a
#: feature row, because those are different claims with their own checks and their own
#: evidence. A path allowance that also quietened a stale id would be a lie by proxy.
#:
#: Every reason below is checkable: `tools/devnet_publish.py`, `tests/test_value_band.py`,
#: `tests/test_boundaries.py`, `tests/test_onchain_sim.py`, `ticketpath/core/value_band.py`
#: and `records/findings/17-hackathon-rules-recheck.md` are in the tree, and `.gitignore`
#: carries `NIGHT-*` and `records/devnet-artefacts.local.json`.
ALLOWED_ABSENCES: tuple[tuple[str, str], ...] = (
    (
        "tools/devnet_check.py",
        "the planning documents' name for the publish script, which shipped as tools/devnet_publish.py",
    ),
    (
        "tests/test_rpc_adapter.py",
        "planned and never written: the adapter is covered in tests/test_boundaries.py",
    ),
    (
        "tests/test_pricing_model_adapter.py",
        "planned and never written: the adapter is covered in tests/test_boundaries.py",
    ),
    (
        "tests/test_chain_client.py",
        "planned and never written: load_artefact is covered in tests/test_onchain_sim.py",
    ),
    (
        "ticketpath/core/markup_band.py",
        "a module the engine never needed; the band arithmetic is ticketpath/core/value_band.py",
    ),
    (
        "tests/test_markup_band.py",
        "the same planned module; the band tests are tests/test_value_band.py",
    ),
    (
        "records/NIGHT-CONTINUE.md",
        "a handover sheet, kept out of the tree by .gitignore's `NIGHT-*`: it names this machine",
    ),
    (
        "records/devnet-artefacts.local.json",
        "the local-validator rehearsal artefact, git-ignored by name so a rehearsal cannot be read as devnet",
    ),
)

#: A reason has to be something a reader can act on or argue with. Four words is the same
#: threshold `.public-denylist` uses for an exception, for the same reason.
MIN_REASON_WORDS = 4


@dataclass(frozen=True)
class Allowance:
    """One entry of `ALLOWED_ABSENCES`, with the line it sits on in this file."""

    path: str
    reason: str
    line: int

    @property
    def checkable(self) -> bool:
        return len(self.reason.split()) >= MIN_REASON_WORDS


def allowances(root: Path) -> list[Allowance]:
    """The allow table, with each entry's own line number in this file.

    The line is found by reading this file rather than being typed beside the entry: a
    hand-typed line number is a second copy of a fact, and the copy that goes stale is the
    one nobody re-reads.
    """
    source = read_lines(root, "tools/doc_check.py")
    out = []
    for path, reason in ALLOWED_ABSENCES:
        line = 0
        for index, text in enumerate(source, start=1):
            if f'"{path}"' in text:
                line = index
                break
        out.append(Allowance(path=path, reason=reason, line=line))
    return out


def git_ignored(root: Path, candidates: list[str]) -> set[str] | None:
    """Which of these paths `.gitignore` keeps out of the tree, or None if git cannot say.

    A document is checked against the repository, and the repository is the tracked tree. A
    path the checkout produced and no clone carries -- a local-validator artefact, a build
    output, a report page -- is not a claim about that tree, and re-deciding which paths
    those are here would be a second copy of `.gitignore` to keep in step with the first.
    So the question goes to the file that owns it, in one call for the whole run: forty
    absent paths cost one subprocess, not forty.

    `--no-index` because the ignore rules are the question, not the index: a path this
    checkout happens to have indexed and then deleted is still ignored by the rules, and
    the caller only asks about paths absent from disk anyway.

    None means git could not answer: no git on PATH, not a work tree, a return code that
    is neither "some are ignored" nor "none is". The caller then judges every path by
    `exists()` exactly as it did before this existed, so the degraded run reports more
    violations than a working one, never fewer, and a quiet gate never means a gate that
    silently stopped asking.
    """
    if not candidates:
        return set()
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "--no-index", "--stdin", "-z"],
            input=b"\0".join(name.encode("utf-8") for name in candidates),
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    # 0 is "at least one of these is ignored" and 1 is "none is": both are answers. Any
    # other code is a refusal, and a refusal must not read as "nothing is ignored".
    if done.returncode not in (0, 1):
        return None
    return {part for part in done.stdout.decode("utf-8", "replace").split("\0") if part}


def check_paths(root: Path, files: list[str], notes: dict | None = None) -> list[Violation]:
    """Every repo path a tracked document names exists, unless its absence is allowed.

    An absence is allowed two ways: written down in `ALLOWED_ABSENCES` with a reason, or
    kept out of the tree by `.gitignore`, which is the repository's own statement that the
    file is real and deliberately not carried. The second is asked in one batch after the
    walk, because it is a question for git and not for this file.

    `notes["allowed"]` collects the absences the table suppressed and `notes["ignored"]`
    the paths git excused, each with the document and line that named it, so the run can
    report how many there were and, under `--verbose`, which. A suppressed absence is not
    silent: it is counted, and either the entry that silenced it carries a reason a reader
    can check or `.gitignore` does.
    """
    out: list[Violation] = []
    allowed = {entry.path: entry for entry in allowances(root)}

    for entry in allowed.values():
        if not entry.reason.strip():
            out.append(
                Violation("paths", "tools/doc_check.py", entry.line,
                          f"the ALLOWED_ABSENCES entry for {entry.path} has no reason")
            )
        elif not entry.checkable:
            out.append(
                Violation("paths", "tools/doc_check.py", entry.line,
                          f"the ALLOWED_ABSENCES reason for {entry.path} is too thin to check: "
                          f"{entry.reason!r}")
            )

    suppressed: list[Allowance] = []
    absent: list[tuple[str, int, str]] = []
    for relative in files:
        for number, line in enumerate(read_lines(root, relative), start=1):
            candidates = [match.group(1) for match in INLINE_CODE.finditer(line)]
            candidates += [match.group(1) for match in LINK_TARGET.finditer(line)]
            if ABSENCE.search(line) and candidates:
                # The line itself says the thing is not there. A document that records a
                # plan it then checked and found absent is being honest, and a checker
                # that calls that a stale path teaches a reader to ignore it.
                continue
            seen = set()
            for candidate in candidates:
                text = candidate.strip()
                if "#" in text:  # a link to a section is a claim about the file
                    text = text.split("#", 1)[0].strip()
                if not looks_like_repo_path(text) or text in seen:
                    continue
                seen.add(text)
                if (root / text).exists():
                    continue
                if (root / relative).parent.joinpath(text).exists():
                    # A document inside a subproject names that subproject's files the way
                    # its own readers do: `tools/build-copy.sh` in `frontend/README.md` is
                    # the frontend's script and not the root's. Try the document's own
                    # directory before calling a file that is there missing. For a
                    # document at the root this resolves to the root and changes nothing.
                    continue
                entry = allowed.get(text)
                if entry is not None and entry.checkable:
                    suppressed.append(entry)
                    continue
                absent.append((relative, number, text))

    ignored: list[tuple[str, str, int]] = []
    ignored_paths = git_ignored(root, sorted({text for _relative, _number, text in absent})) or set()
    for relative, number, text in absent:
        if text in ignored_paths:
            # `.gitignore` keeps this out of every clone on purpose, so a document naming it
            # describes the run that produced it and not a file the tree is missing.
            ignored.append((text, relative, number))
            continue
        out.append(Violation("paths", relative, number, f"{text} does not exist"))

    if notes is not None:
        notes["allowed"] = suppressed
        notes["ignored"] = ignored
    return out


# ---------------------------------------------------------------------------
# check 2: cross-references
# ---------------------------------------------------------------------------


FINDINGS_REF = re.compile(r"(?<![\w/-])(?:records/)?findings/(\d{2})((?:-[A-Za-z0-9][A-Za-z0-9._-]*)?)")
ABSENCE = re.compile(r"does not exist|no such|is absent|\bmissing\b", re.IGNORECASE)
SECTION_REF = re.compile(r"§(\d+(?:\.\d+)*)")
HEADING_NUMBER = re.compile(r"^(\d+(?:\.\d+)*)[.)]?\s")
OTHER_DOC = re.compile(r"[A-Za-z0-9_.-]+\.md\b")
FINDINGS_SHORT = re.compile(r"\b\d\d-[a-z]\b")
DECISION_REF = re.compile(r"\b([DQ])(\d{1,2})\b")


def check_cross_references(root: Path, files: list[str]) -> list[Violation]:
    """A reference resolves, or it is reported: findings, sections, decisions."""
    out: list[Violation] = []

    findings_dir = root / FINDINGS_DIR
    existing = sorted(path.name for path in findings_dir.glob("*.md")) if findings_dir.is_dir() else []

    decisions = set()
    for line in read_lines(root, DECISION_LOG):
        match = re.match(r"^##\s+([DQ])(\d{1,2})\b", line)
        if match:
            decisions.add(match.group(0).split()[1])

    design_lines = read_lines(root, DESIGN_DOC)
    sections = set()
    items: dict[str, set[str]] = {}
    marks = headings(design_lines)
    for position, (index, level, title) in enumerate(marks):
        match = HEADING_NUMBER.match(title)
        if not match:
            continue
        number = match.group(1)
        sections.add(number)
        end = len(design_lines)
        for other_index, other_level, _title in marks[position + 1 :]:
            if other_level <= level:
                end = other_index
                break
        # A numbered list under the heading is a set of addressable items: `§4.2.5` is
        # the fifth thing §4.2 says this design does not stop. Reading only the headings
        # would call six true references dangling, which is the one failure a checker
        # must not have -- a reader who trusts it would go and "fix" the document.
        items[number] = {
            item.group(1)
            for item in (re.match(r"^(\d+)\.\s", line) for line in design_lines[index + 1 : end])
            if item
        }

    names_decisions = {}
    for relative in files:
        names_decisions[relative] = any("F-decision-log" in line for line in read_lines(root, relative))

    for relative in files:
        lines = read_lines(root, relative)
        for index, line in enumerate(lines):
            number = index + 1
            # -- findings --------------------------------------------------
            for match in FINDINGS_REF.finditer(line):
                if ABSENCE.search(line):
                    continue  # the sentence says it is absent; that is not a stale claim
                prefix, slug = match.group(1), match.group(2) or ""
                if slug.endswith("-") and index + 1 < len(lines):
                    # A path wrapped at a hyphen: `records/findings/01-a-market-` newline
                    # `structure.md`. Joining is what a reader does; anything else would
                    # report a file that is there as a file that is not.
                    continuation = re.match(r"[A-Za-z0-9._-]+", lines[index + 1].strip())
                    if continuation:
                        slug += continuation.group(0)
                if slug:
                    name = prefix + slug
                    if not name.endswith(".md"):
                        name += ".md"
                    # A number can also be a directory: a finding's sources sit beside it as
                    # `33-b-region-cap-law-sources/`, and a reference to the directory is a
                    # reference to what is in it. Reporting it as `...-sources.md does not
                    # exist` would send a reader to edit a true sentence, which is the one
                    # failure this check must not have.
                    directory = name[: -len(".md")]
                    if not (findings_dir / name).exists() and not (findings_dir / directory).is_dir():
                        out.append(
                            Violation("cross-references", relative, number,
                                      f"{FINDINGS_DIR}/{name} does not exist")
                        )
                elif not any(existing_name.startswith(prefix + "-") for existing_name in existing):
                    out.append(
                        Violation("cross-references", relative, number,
                                  f"no {FINDINGS_DIR}/{prefix}-* file exists")
                    )

            if relative == DESIGN_DOC:
                # -- sections of this file ---------------------------------
                context = " ".join(paragraph_before(lines, index))
                if "programme" in context.lower():
                    continue  # the research programme's own numbering, not this file's
                foreign = [name for name in OTHER_DOC.findall(context) if not name.endswith("ON-CHAIN-DESIGN.md")]
                if foreign:
                    continue  # a section number quoted from another document
                for match in SECTION_REF.finditer(line):
                    number = match.group(1)
                    if number in sections:
                        continue
                    parent, _, item = number.rpartition(".")
                    if parent in sections and item in items.get(parent, set()):
                        continue
                    out.append(
                        Violation("cross-references", relative, index + 1,
                                  f"§{number} is not a section of this file")
                    )

            # -- decisions and open questions ------------------------------
            if relative.startswith(FINDINGS_DIR + "/") or not names_decisions.get(relative):
                continue
            context = " ".join(paragraph_before(lines, index))
            if FINDINGS_SHORT.search(context) or "findings/" in context:
                continue  # this paragraph is quoting another registry's numbering
            for match in DECISION_REF.finditer(line):
                if match.group(2).startswith("0"):
                    continue  # D01/D02 are 03-b's row ids, not decisions
                token = match.group(0)
                if token not in decisions:
                    out.append(
                        Violation("cross-references", relative, number,
                                  f"{token} has no '## {token}' heading in {DECISION_LOG}")
                    )
    return out


# ---------------------------------------------------------------------------
# check 7: findings-unique
# ---------------------------------------------------------------------------

#: A finding's file name: two digits, a hyphen, then whatever the session called it.
FINDING_NAME = re.compile(r"^(\d{2})-(.+)$")

#: The group suffix the convention uses when one number carries several files: a single
#: letter and a hyphen, `01-a-market-structure.md`. `02-ai-ml-decision.md` is not a group
#: suffix, it is a word that happens to start with a letter.
FINDING_LETTER = re.compile(r"^([a-z])-")


@dataclass(frozen=True)
class Finding:
    """One entry under records/findings/: its name, its number, and its group letter."""

    name: str
    number: str
    letter: str  # "" when the name carries no single-letter suffix

    @property
    def key(self) -> str:
        return f"{self.number}-{self.letter}" if self.letter else self.number


def findings_in(root: Path) -> list[Finding]:
    """Every finding under records/findings/, a directory counting as one.

    The directory version matters here: two sessions can leave a finding's sources beside it
    as a directory under the same number, and a reader following `33` then cannot tell which
    entry was meant. Letters are the fix, not a rename: `33-a-region-cap-law.md` and
    `33-b-region-cap-law-sources/` say which is which, and the directory is still read as one
    claimant so the report names both. This function only reads names; it never judges them.
    """
    directory = root / FINDINGS_DIR
    if not directory.is_dir():
        raise Unreadable(f"{FINDINGS_DIR} is missing, and check 7 groups the findings there")
    found: list[Finding] = []
    for entry in sorted(directory.iterdir(), key=lambda path: path.name):
        match = FINDING_NAME.match(entry.name)
        if not match:
            continue
        number, rest = match.group(1), match.group(2)
        if entry.is_dir():
            letter = FINDING_LETTER.match(rest)
            found.append(Finding(entry.name, number, letter.group(1) if letter else ""))
            continue
        if entry.suffix not in (".md", ".rst", ".txt"):
            continue
        stem = rest[: -len(entry.suffix)] if entry.suffix else rest
        letter = FINDING_LETTER.match(stem)
        found.append(Finding(entry.name, number, letter.group(1) if letter else ""))
    return found


def finding_claimants(root: Path) -> dict[str, list[str]]:
    """Every number under records/findings/, mapped to the names that claim it."""
    groups: dict[str, list[str]] = {}
    for finding in findings_in(root):
        groups.setdefault(finding.number, []).append(finding.name)
    return groups


def findings_by_key(root: Path) -> dict[str, list[str]]:
    """The names a *reference* can land on, keyed by `34` and by `34-a`.

    A reference to `34` is answered by every claimant at that number; a reference to `34-a`
    by the files whose suffix is `a`. Both keys are needed because both are written in this
    tree, and a key with more than one name is a reference nobody can follow.
    """
    keys: dict[str, list[str]] = {}
    for finding in findings_in(root):
        keys.setdefault(finding.number, []).append(finding.name)
        if finding.letter:
            keys.setdefault(finding.key, []).append(finding.name)
    return keys


def check_findings_unique(root: Path, files: list[str], notes: dict | None = None) -> list[Violation]:
    """A reference to a shared finding number is ambiguous; a shared number is a warning.

    Two sessions allocating numbers concurrently wrote four different findings under `34`,
    and `README.md`, the decision log and the ledger then pointed at `34` and read as
    correct whichever one was meant. That is the defect: a reader following the reference
    lands in the wrong file, and no other check can see it, because `cross-references` can
    only ask whether *some* file at that number exists.

    What this does not do is fail the numbers themselves. `00` and `02` pre-date both
    sessions, were written by one hand under the convention in use at the time, and a check
    that can only go green by renaming the operator's existing record does more damage than
    the defect it catches. So a number with several claimants is *reported on every run* as
    a warning, one line each, and the run stays green; a *reference* that lands on such a
    number is a violation, because that is a claim with a wrong answer.
    """
    out: list[Violation] = []
    claimants = finding_claimants(root)
    by_key = findings_by_key(root)

    shared: list[str] = []
    for number, names in sorted(claimants.items()):
        if len(names) <= 1:
            continue
        letters = [f.letter for f in findings_in(root) if f.number == number]
        lettered_cleanly = all(letters) and len(set(letters)) == len(names)
        shape = (
            "each lettered, the convention working"
            if lettered_cleanly
            else "not all lettered, so a bare reference is ambiguous"
        )
        shared.append(f"number {number} has {len(names)} claimants ({shape}): {', '.join(names)}")
    if notes is not None:
        notes["findings_shared"] = shared

    for relative in files:
        for index, line in enumerate(read_lines(root, relative)):
            if ABSENCE.search(line):
                continue  # the sentence says it is not there; that is not a reference
            for match in FINDINGS_REF.finditer(line):
                number, slug = match.group(1), match.group(2) or ""
                bare = slug == "" or re.fullmatch(r"-[a-z]", slug) is not None
                if not bare:
                    continue  # `33-a-region-cap-law.md` names one file and cannot be ambiguous
                key = number + slug
                names = by_key.get(key, [])
                if len(names) <= 1:
                    continue
                out.append(
                    Violation(
                        "findings-unique", relative, index + 1,
                        f"references {key}, which is {len(names)} findings "
                        f"({', '.join(names)}); name the file, not the number",
                    )
                )
    return out


# ---------------------------------------------------------------------------
# check 3: ids
# ---------------------------------------------------------------------------


#: A module-level constant assignment, with or without a type annotation. Matched
#: broadly and filtered on the name, because a pattern that tried to anchor `MEMO` at the
#: start of the name needs a clever expression to also match a name that *is* the prefix,
#: and the clever version is how `MEMO_PROGRAM_DEVNET` went unread once already.
CONSTANT_ASSIGNMENT = re.compile(r"^([A-Z][A-Z0-9_]*)\s*(?::[^=]+)?=\s*(.*)$")
#: An id written as a string literal, and an id written as a bare name.
BASE58_LITERAL = re.compile(r'"([1-9A-HJ-NP-Za-km-z]{32,44})"')
BASE58_TOKEN = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")


def _constant_blocks(source: str) -> dict[str, str]:
    """Every module-level constant assignment whose name mentions `MEMO`, with its text.

    A block is the right-hand side plus any continuation lines, so a dict literal written
    across several lines arrives whole.
    """
    blocks: dict[str, str] = {}
    lines = source.splitlines()
    for index, line in enumerate(lines):
        match = CONSTANT_ASSIGNMENT.match(line.strip())
        if not match or "MEMO" not in match.group(1):
            continue
        name, rest = match.group(1), match.group(2)
        block = [rest]
        depth = rest.count("{") - rest.count("}")
        cursor = index + 1
        while depth > 0 and cursor < len(lines):
            block.append(lines[cursor])
            depth += lines[cursor].count("{") - lines[cursor].count("}")
            cursor += 1
        blocks[name] = "\n".join(block)
    return blocks


def memo_table(source: str) -> dict[str, str]:
    """Every base58 id literal a `MEMO_…` name in `chain_client.py` carries.

    The claim this feeds is "every memo id a document quotes is one of the id literals in
    that file", so the unit is a *set of literals* and not a mapping. The mapping half of
    the same file is `memo_programs`, which answers the other question a document can get
    wrong: not "is this id in the file" but "does this id belong to the cluster the
    sentence put it on".

    Why the mapping is resolved and not just read: the file grew a per-cluster table whose
    values are names, not literals --

        MEMO_PROGRAM_DEVNET = "Memo4c2pN…"
        MEMO_PROGRAMS = {"devnet": MEMO_PROGRAM_DEVNET, ...}

    -- and a reader that took only the mapping's string values would find none, fall through
    to the single-literal branch, and return one id. That is a checker bug that reads as
    three false document violations, which is the worst failure this file can have.

    Keys are labels for the message (`MEMO_PROGRAM_DEVNET`, `MEMO_PROGRAMS[devnet]`), not
    clusters: the constants and the mapping share no key space, and collapsing both onto
    one key is exactly what lost the devnet id. The verdict on whether the mapping covers
    the right clusters is `tests/test_onchain_sim.py`'s, not this file's.
    """
    blocks = _constant_blocks(source)

    literals: dict[str, str] = {}
    for name, text in blocks.items():
        found = BASE58_LITERAL.search(text)
        if found:
            literals[name] = found.group(1)

    for name, text in blocks.items():
        for cluster, value in re.findall(r'"([A-Za-z_-]+)"\s*:\s*([^,\n}]+)', text):
            value = value.strip()
            quoted = BASE58_LITERAL.fullmatch(value)
            resolved = quoted.group(1) if quoted else literals.get(value)
            if resolved:
                literals[f"{name}[{cluster}]"] = resolved
    return literals


def memo_programs(source: str) -> dict[str, str]:
    """The cluster -> id pairs `MEMO_PROGRAMS` really maps, resolved to literals.

    `memo_table` answers "which literals does this file carry"; this answers "which cluster
    does each of them belong to". The difference is a reversal: a document that says devnet
    is `MemoSq4gq…` and mainnet-beta is `Memo4c2p…` quotes two literals the file carries, so
    the set comparison passes, and the sentence is the exact error this check exists to stop.
    Empty when the file has no `MEMO_PROGRAMS` block, which is a file shape `check_ids` does
    not police -- `tests/test_doc_check.py` pins the reading.
    """
    blocks = _constant_blocks(source)
    table = blocks.get("MEMO_PROGRAMS")
    if table is None:
        return {}
    literals: dict[str, str] = {}
    for name, text in blocks.items():
        found = BASE58_LITERAL.search(text)
        if found:
            literals[name] = found.group(1)
    programs: dict[str, str] = {}
    for cluster, value in re.findall(r'"([A-Za-z_-]+)"\s*:\s*([^,\n}]+)', table):
        value = value.strip()
        quoted = BASE58_LITERAL.fullmatch(value)
        resolved = quoted.group(1) if quoted else literals.get(value)
        if resolved:
            programs[cluster] = resolved
    return programs


CLUSTER_WORD = r"\b({})\b"


def _distance(word: tuple[int, int, str], token: tuple[int, int, str]) -> tuple[int, int]:
    """How far apart a cluster word and an id are, with a preceding word winning a tie.

    "devnet's id is X" and "devnet is X" are both written far more often than "X is
    devnet's", so on a tie the word before the id is the one being read.
    """
    word_start, word_end, _ = word
    token_start, token_end, _ = token
    if word_end <= token_start:
        return (token_start - word_end, 0)
    if word_start >= token_end:
        return (word_start - token_end, 1)
    return (0, 2)


def _misattributed_clusters(line: str, number: int, relative: str, programs: dict[str, str]) -> list[Violation]:
    """Ids a memo line attributes to the wrong cluster.

    Each cluster word on the line is read against the id nearest to it, which is what a
    reader does. Only that one id is checked: a line saying "devnet uses `A` and the CLI
    ships `B`" names one cluster, and `B` is not a claim about devnet because `A` is the id
    next to the word. A reversal puts the wrong id next to the word and is caught.
    """
    if not programs:
        return []
    pattern = CLUSTER_WORD.format("|".join(sorted(programs, key=len, reverse=True)))
    words = [(match.start(), match.end(), match.group(1)) for match in re.finditer(pattern, line)]
    if not words:
        return []
    tokens = [(match.start(), match.end(), match.group(0)) for match in BASE58.finditer(line)]
    if not tokens:
        return []
    # One cluster and one id per clause reads positionally -- "devnet uses A and mainnet-beta
    # uses B" is two claims in order -- and a line whose counts do not match is read by
    # distance instead. Both readings are of the text on the line and neither guesses.
    pairs = list(zip(words, tokens)) if len(words) == len(tokens) else [
        (word, min(tokens, key=lambda candidate: _distance(word, candidate))) for word in words
    ]
    mapped = set(programs.values())
    out: list[Violation] = []
    for word, token in pairs:
        cluster = word[2]
        if token[2] not in mapped or token[2] == programs.get(cluster):
            continue
        out.append(
            Violation(
                "ids", relative, number,
                f"attributes {token[2]} to {cluster}; {CHAIN_CLIENT}'s MEMO_PROGRAMS puts "
                f"{programs[cluster]} there",
            )
        )
    return out


#: The words that place an id on devnet. A sentence naming either is saying where the id
#: lives; `records/devnet-artefacts.json` counts because naming the artefact is naming its
#: cluster.
DEVNET_WORDS = ("devnet", "devnet-artefacts.json")

#: The words that place an id somewhere other than devnet. There are two programs now: the
#: devnet one, frozen, which is the evidence, and a v2 that exists only on a local validator.
#: A rule that knows only the artefact's id makes an accurate sentence look wrong, and the
#: only way to satisfy it would be to stop naming the second program.
OTHER_CLUSTER_WORDS = ("local", "localnet", "validator", "not on devnet")


def _says(lowered: str, words: tuple[str, ...]) -> bool:
    return any(word in lowered for word in words)


def _program_id_violations(
    line: str,
    context: str,
    number: int,
    relative: str,
    artefact: dict,
    memo_ids: set[str],
) -> list[Violation]:
    """Program ids on one line, each against the cluster the sentence places it on.

    The rule: the artefact's program id and mint belong to devnet, so a sentence quoting
    them has to say so; any other program id belongs to some other cluster, so a sentence
    quoting it has to name one (`local`, `localnet`, `validator`) or say it is not on
    devnet; and an id with no cluster named at all is a violation whichever id it is.

    `context` is the sentence the id sits in, which is the contiguous block of text around
    the line and not the physical line: markdown here is hard-wrapped at 100 columns, so a
    thousand-line record breaks a sentence every dozen words. Measured: `README.md:384-385`
    says "it is on devnet at `5EJ1…`, with a / Token-2022 mint at `6RPS…`", one true
    sentence across two lines. Judging the mint on line 385 alone would call a correct
    sentence wrong, which is the failure this rule exists to remove rather than relocate.
    """
    out: list[Violation] = []
    lowered = line.lower()
    names_devnet = _says(context.lower(), DEVNET_WORDS)
    names_other = _says(context.lower(), OTHER_CLUSTER_WORDS)
    for match in BASE58.finditer(line):
        token = match.group(0)
        if token in KNOWN_PROGRAM_IDS or token in memo_ids:
            continue
        if "memo" in lowered:
            continue  # the memo pass owns this token; one claim, one report
        if token == artefact.get("mint"):
            if not names_devnet:
                out.append(
                    Violation("ids", relative, number,
                              f"quotes the devnet mint {token} and the sentence does not say devnet")
                )
            continue
        if token == artefact.get("programId"):
            if not names_devnet:
                out.append(
                    Violation("ids", relative, number,
                              f"quotes the devnet program id {token} and the sentence does not say devnet")
                )
            continue
        if names_other:
            continue  # the sentence places it on a cluster that is not devnet: true or false, not this check
        if names_devnet:
            out.append(
                Violation("ids", relative, number,
                          f"quotes program id {token}; {ARTEFACT} records "
                          f"{artefact.get('programId')} as the devnet program id")
            )
        else:
            out.append(
                Violation("ids", relative, number,
                          f"quotes program id {token} with no cluster named: say devnet, or say "
                          f"local, localnet or validator if it is not on devnet")
            )
    return out


def check_ids(root: Path, files: list[str]) -> list[Violation]:
    """Ids a document quotes are the ids the code and the artefact carry."""
    out: list[Violation] = []

    memos = memo_table((root / CHAIN_CLIENT).read_text(encoding="utf-8") if (root / CHAIN_CLIENT).is_file() else "")
    if not memos:
        raise Unreadable(f"{CHAIN_CLIENT} carries no memo program id, and check 3 compares against it")

    artefact_path = root / ARTEFACT
    artefact: dict = {}
    if artefact_path.is_file():
        try:
            artefact = json.loads(artefact_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            artefact = {}
    recorded = {value for value in artefact.values() if isinstance(value, str)}
    for key in ("programId", "mint", "memoProgram"):
        if isinstance(artefact.get(key), str):
            recorded.add(artefact[key])
    if artefact and not ({"programId", "mint"} & set(artefact)):
        # A file that exists but records no id would make every quoted id uncomparable,
        # and a silent pass is the one outcome this check must never produce.
        return [
            Violation("ids", ARTEFACT, 1,
                      "the artefact carries no programId and no mint, so no id can be confirmed")
        ]

    known = recorded | set(memos.values()) | KNOWN_PROGRAM_IDS

    chain_client_source = (root / CHAIN_CLIENT).read_text(encoding="utf-8") if (root / CHAIN_CLIENT).is_file() else ""
    programs = memo_programs(chain_client_source)

    memo_docs = ("README.md", DESIGN_DOC)
    for relative in memo_docs:
        for number, line in enumerate(read_lines(root, relative), start=1):
            if "memo" not in line.lower():
                continue
            for match in BASE58.finditer(line):
                token = match.group(0)
                if token in memos.values() or token in KNOWN_PROGRAM_IDS:
                    continue
                out.append(
                    Violation("ids", relative, number,
                              f"quotes memo program id {token}; no `MEMO_` name in {CHAIN_CLIENT} "
                              f"carries it (it carries "
                              f"{', '.join(sorted(set(memos.values())))})")
                )
            # The literal rule above cannot see a reversal: both ids are literals the file
            # carries, and the sentence has swapped them. This is the direction check.
            out.extend(_misattributed_clusters(line, number, relative, programs))

    quoted_docs = ("README.md", STATE_DOC)
    for relative in quoted_docs:
        lines = read_lines(root, relative)
        for index, line in enumerate(lines):
            number = index + 1
            lowered = line.lower()
            if not any(word in lowered for word in ("program", "mint", "devnet")):
                continue
            if not artefact:
                for match in BASE58.finditer(line):
                    token = match.group(0)
                    if token in known or "memo" in lowered:
                        continue
                    out.append(
                        Violation("ids", relative, number,
                                  f"quotes {token}; {ARTEFACT} is missing, so no id can be confirmed")
                    )
                continue
            context = " ".join(paragraph_before(lines, index))
            out.extend(
                _program_id_violations(
                    line, context, number, relative, artefact, set(memos.values())
                )
            )
    return out


# ---------------------------------------------------------------------------
# check 4: program vs doc
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ProgramFacts:
    """What the Rust program actually implements: the three sets a document can be wrong about."""

    errors: dict[str, str]        # variant -> number
    instructions: dict[str, str]  # variant -> wire tag
    seeds: dict[str, str]         # fn -> byte literal


def _enum_body(source: str, name: str) -> str:
    match = re.search(r"pub enum " + re.escape(name) + r"\s*\{(.*?)\n\}", source, re.DOTALL)
    return match.group(1) if match else ""


def _code_only(line: str) -> str:
    """One line of Rust with comments and string *contents* removed.

    A match arm's body is code, and only code may name a variant. A comment inside the
    block (`// Ok(Self::Foo) is not an arm`) and a message string are prose, and reading
    them as an arm invents an instruction the program does not have, which then reads as
    a table row that is wrong about the code. Char literals are left alone: nothing in a
    tag's body depends on one, and a second kind of quoting is a second way to be wrong.
    """
    out: list[str] = []
    index = 0
    length = len(line)
    in_string = False
    while index < length:
        char = line[index]
        if in_string:
            if char == "\\" and index + 1 < length:
                index += 2
                continue
            if char == '"':
                in_string = False
                out.append(char)
            index += 1
            continue
        if char == '"':
            in_string = True
            out.append(char)
            index += 1
            continue
        if char == "/" and index + 1 < length and line[index + 1] == "/":
            break
        out.append(char)
        index += 1
    return "".join(out)


def parse_program(sources: dict[str, str] | str) -> ProgramFacts:
    """Read the program's error numbers, instruction tags and PDA seed literals.

    `sources` is every `.rs` file of the program, keyed by name, or one file's text (which
    the tests use). The tags come from the `unpack` arms rather than from the doc comments
    above the variants: the arms are what a transaction on the wire is matched against, so
    a comment and a tag disagreeing is a code bug, and this check is about the document.
    """
    if isinstance(sources, str):
        sources = {"": sources}

    errors: dict[str, str] = {}
    instructions: dict[str, str] = {}
    seeds: dict[str, str] = {}
    for text in sources.values():
        for line in _enum_body(text, "TicketpathError").splitlines():
            match = re.match(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\d+)\s*,", line)
            if match:
                errors.setdefault(match.group(1), match.group(2))

        unpack = re.search(r"fn unpack\s*\(data:[^)]*\)(.*?)\n    \}", text, re.DOTALL)
        block = unpack.group(1) if unpack else ""
        current = None
        for raw in block.splitlines():
            line = _code_only(raw)
            arm = re.match(r"^\s*(\d+)\s*=>\s*(.*)$", line)
            if arm:
                current = arm.group(1)
                # An arm may close on its own line (`0 => Ok(Self::Foo),`) or open a block
                # that closes several lines later. Reading only the *following* lines, as
                # an earlier version did, misses every one-line arm: the tag is found and
                # then the variant on the same line is never read, which reported a
                # correct table row as a row the code does not have.
                same_line = re.search(r"Ok\(Self::([A-Za-z_][A-Za-z0-9_]*)", arm.group(2))
                if same_line:
                    instructions.setdefault(same_line.group(1), current)
                    current = None
                continue
            variant = re.search(r"Ok\(Self::([A-Za-z_][A-Za-z0-9_]*)", line)
            if variant and current is not None:
                instructions.setdefault(variant.group(1), current)
                current = None

        for match in re.finditer(r"pub fn ([A-Za-z0-9_]*_seeds)\s*\([^)]*\)[^{]*\{(.*?)\n\}", text, re.DOTALL):
            literal = re.search(r'b"([^"]+)"', match.group(2))
            if literal:
                seeds.setdefault(match.group(1), literal.group(1))
    return ProgramFacts(errors=errors, instructions=instructions, seeds=seeds)


def program_sources(root: Path) -> dict[str, str]:
    """Every `.rs` file of the program, keyed by its path relative to the tree."""
    directory = root / PROGRAM_SRC_DIR
    if not directory.is_dir():
        raise Unreadable(f"{PROGRAM_SRC_DIR} is missing, and check 4 parses the program there")
    sources = {}
    for path in sorted(directory.glob("*.rs")):
        sources[path.relative_to(root).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    if not sources:
        raise Unreadable(f"{PROGRAM_SRC_DIR} holds no .rs files, and check 4 parses the program there")
    return sources


def implemented_today_table(lines: list[str]) -> Table | None:
    """The first table under a heading that says the program is implemented.

    The heading is matched on "implement" and the table's header is checked by the
    caller, so a document may call the section "What the program implements today" or
    "14. Implemented today" and the check reads the same table either way. The header is
    the contract; the heading is only where to look. A table with the wrong header is
    reported as a header problem, which is a message the doc steward can act on.
    """
    marks = headings(lines)
    for position, (index, level, title) in enumerate(marks):
        if "implement" not in title.lower():
            continue
        end = len(lines)
        for other_index, other_level, _title in marks[position + 1 :]:
            if other_level <= level:
                end = other_index
                break
        found = tables_in(lines, index + 1, end)
        if found:
            return found[0]
    return None


def _plain_cells(cells: list[str]) -> list[str]:
    return [re.sub(r"[`*]", "", cell).strip().lower() for cell in cells]


def check_program_vs_doc(root: Path) -> list[Violation]:
    """The three sets match the implemented-today table, both ways."""
    out: list[Violation] = []
    facts = parse_program(program_sources(root))
    table = implemented_today_table(require_lines(root, DESIGN_DOC))
    if table is None:
        return [
            Violation(
                "program-vs-doc",
                DESIGN_DOC,
                1,
                'no implemented-today table in docs/ON-CHAIN-DESIGN.md (a heading naming it, '
                'then a table headed "| kind | name | value | where |")',
            )
        ]

    header = _plain_cells(table.header)
    if header[:4] != ["kind", "name", "value", "where"]:
        return [
            Violation(
                "program-vs-doc",
                DESIGN_DOC,
                table.line,
                f"the implemented-today table's header is {header}, not "
                '["kind", "name", "value", "where"]',
            )
        ]

    claimed = {"error": {}, "instruction": {}, "seed": {}}
    for number, cells in table.rows:
        cells = cells + [""] * 4
        kind = re.sub(r"[`*]", "", cells[0]).strip().lower()
        name = re.sub(r"[`*]", "", cells[1]).strip()
        value = re.sub(r"[`*]", "", cells[2]).strip()
        if kind not in PROGRAM_KINDS:
            out.append(
                Violation("program-vs-doc", DESIGN_DOC, number,
                          f"kind {kind!r} is not one of {', '.join(PROGRAM_KINDS)}")
            )
            continue
        if not name:
            out.append(Violation("program-vs-doc", DESIGN_DOC, number, "row names nothing"))
            continue
        claimed[kind][name] = value

    for kind, actual in (
        ("error", facts.errors),
        ("instruction", facts.instructions),
        ("seed", facts.seeds),
    ):
        for name, value in actual.items():
            if name not in claimed[kind]:
                out.append(
                    Violation("program-vs-doc", DESIGN_DOC, table.line,
                              f"{kind} {name} = {value} is in {PROGRAM_SRC_DIR} and not in the table")
                )
            elif claimed[kind][name] != value:
                out.append(
                    Violation("program-vs-doc", DESIGN_DOC, table.line,
                              f"{kind} {name} is {value} in {PROGRAM_SRC_DIR} and "
                              f"{claimed[kind][name]} in the table")
                )
        for name, value in claimed[kind].items():
            if name not in actual:
                out.append(
                    Violation("program-vs-doc", DESIGN_DOC, table.line,
                              f"the table claims {kind} {name} = {value}; {PROGRAM_SRC_DIR} has none")
                )
    return out


# ---------------------------------------------------------------------------
# check 5: registry counts
# ---------------------------------------------------------------------------


ID_TOKEN = re.compile(r"^[A-Z]{1,3}-?\d{1,3}$")
COUNT_LINE = re.compile(r"^\s*[-*]?\s*Count:\s*\**\s*(\d+)\b")

#: What marks a `Count:` statement as a record of a superseded number rather than the file's
#: current one. A record is append-only, so a correction keeps the old sentence and states
#: the new count beside it; the gate has to read the second and leave the first, or the only
#: way to pass is to delete the history. That is what happened to
#: `records/E-data-source-registry.md`, whose `27` was replaced in place with `32` and no
#: dated note, while `records/D-model-registry.md` kept its `Total 56` beside a dated
#: correction and passed. The same rule has to accept both.
#:
#: A statement is historic only when its paragraph carries a date AND one of these words. Two
#: conditions, because a marker made of one word can be sprinkled on a wrong count, and the
#: point of the rule is that an old number is dated and named as old.
HISTORIC_MARKERS = (
    "supersede",
    "superseded",
    "corrected",
    "correction",
    "previously",
    "historic",
    "original",
    "no longer",
    "old count",
    "earlier",
)
RECORD_DATE = re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b")
BOLD_TOTAL = re.compile(r"\*\*(\d+)\s+[A-Za-z][A-Za-z -]*\*\*")
PAIR = re.compile(r"(?<![\w.])(\d+)\s+in\s+§(\d+(?:\.\d+)*)")
COUNT_CLAIM = re.compile(r"(?<![\w.])(\d+)\s+((?:[A-Za-z][A-Za-z-]*\s+){1,4})in\s+§(\d+(?:\.\d+)*)")


def section_span(lines: list[str], number: str) -> tuple[int, int] | None:
    """The lines a numbered section covers, or None when the number is not a heading."""
    marks = headings(lines)
    for position, (index, level, title) in enumerate(marks):
        if re.match(rf"^{re.escape(number)}(?:[ .]|$)", title):
            end = len(lines)
            for other_index, other_level, _title in marks[position + 1 :]:
                if other_level <= level:
                    end = other_index
                    break
            return index, end
    return None


def registry_rows(lines: list[str], start: int = 0, end: int | None = None) -> set[str]:
    """The identifiers of the rows in a span, in whichever shape the file writes them.

    Three shapes occur here and all three are a row: a table whose first cell is an id
    (`| S14 |`), a table whose first cell is a position under a `#` header (`| 7 |`), and
    an entry heading that names its row (`### V1 \\`time_to_event\\``). A section that
    names each row in a bold-led paragraph instead (`**\\`on_sale_age\\` (A16).**`) is the
    third shape. The order matters: a section with row headings is counted by its
    headings and not also by the paragraphs inside them, which is how §8.1 stays 13 and
    does not become 14.
    """
    stop = len(lines) if end is None else min(end, len(lines))
    span = lines[start:stop]
    rows: set[str] = set()

    for table in tables_in(lines, start, stop):
        numeric = table.header and re.sub(r"[`*]", "", table.header[0]).strip() == "#"
        for _number, cells in table.rows:
            first = re.sub(r"[`*]", "", cells[0]).strip() if cells else ""
            if ID_TOKEN.match(first):
                rows.add(first)
            elif numeric and first.isdigit():
                rows.add(f"#{first}")

    heading_rows: set[str] = set()
    for index, _level, title in headings(span):
        numbered = re.match(r"^(\d+(?:\.\d+){2,})\s", title)
        if numbered and "`" in title:
            heading_rows.add(numbered.group(1))
            continue
        for token in re.findall(r"\b[A-Z]{1,3}-?\d{1,3}\b", title):
            heading_rows.add(token)
    if heading_rows:
        return rows | heading_rows

    fenced = False
    for line in span:
        if line.strip().startswith("```"):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("**"):
            for token in re.findall(r"\(([A-Z]{1,3}-?\d{1,3})\)", line[:200]):
                rows.add(token)
    return rows


def _count_statements(lines: list[str]) -> list[tuple[int, int, bool]]:
    """Every `Count:` statement in a registry: (line, stated number, is it marked historic).

    Historic means the paragraph around it carries a date and a correction word, which is
    the shape an append-only record uses to keep an old number without claiming it.
    """
    statements: list[tuple[int, int, bool]] = []
    for index, line in enumerate(lines):
        match = COUNT_LINE.match(line)
        if not match:
            continue
        paragraph = " ".join(paragraph_before(lines, index)).lower()
        historic = bool(RECORD_DATE.search(paragraph)) and any(
            marker in paragraph for marker in HISTORIC_MARKERS
        )
        statements.append((index + 1, int(match.group(1)), historic))
    return statements


def _check_count_statements(
    relative: str, statements: list[tuple[int, int, bool]], present: int
) -> list[Violation]:
    """The current count against the rows, and no second statement pretending to be current.

    The current statement is the last one not marked historic, so a file may keep any number
    of dated old counts above it (or below it, in a correction note). Two unmarked statements
    are two current counts and the file cannot say which is true, which is a violation even
    when one of them happens to match the rows: an ambiguous record is not a correct one.
    """
    out: list[Violation] = []
    current = [item for item in statements if not item[2]]
    if not current:
        line, _stated, _ = statements[-1]
        return [
            Violation("registry-counts", relative, line,
                      "every Count: statement is marked as superseded, so nothing states the "
                      "current count")
        ]
    for line, stated, _historic in current[:-1]:
        out.append(
            Violation("registry-counts", relative, line,
                      f"states {stated} rows and is not marked as superseded, while line "
                      f"{current[-1][0]} states {current[-1][1]}: two current counts")
        )
    line, stated, _ = current[-1]
    if stated != present:
        out.append(
            Violation("registry-counts", relative, line,
                      f"states {stated} rows; {present} are present")
        )
    return out


def check_registry_counts(root: Path, files: list[str]) -> list[Violation]:
    """A stated count equals the rows present, where the claim names its own scope."""
    out: list[Violation] = []
    for relative in REGISTRIES:
        if relative not in files and not (root / relative).is_file():
            continue
        lines = read_lines(root, relative)
        if not lines:
            continue
        whole = registry_rows(lines)
        statements = _count_statements(lines)
        if statements:
            out.extend(_check_count_statements(relative, statements, len(whole)))

        for index, line in enumerate(lines):
            number = index + 1

            pairs = PAIR.findall(line)
            total = BOLD_TOTAL.search(line)
            if total and len(pairs) >= 2:
                stated = int(total.group(1))
                summed = sum(int(part) for part, _section in pairs)
                if stated != summed:
                    out.append(
                        Violation("registry-counts", relative, number,
                                  f"states {stated} rows; its own breakdown sums to {summed}")
                    )

            for stated_text, noun, section in COUNT_CLAIM.findall(line):
                if not any(stem in noun.lower() for stem in COUNT_NOUNS):
                    continue
                span = section_span(lines, section)
                if span is None:
                    out.append(
                        Violation("registry-counts", relative, number,
                                  f"counts rows in §{section}, which is not a section of this file")
                    )
                    continue
                present = registry_rows(lines, *span)
                if present and int(stated_text) != len(present):
                    out.append(
                        Violation("registry-counts", relative, number,
                                  f"states {stated_text} {noun.strip()} in §{section}; "
                                  f"{len(present)} are present")
                    )
    return out


# ---------------------------------------------------------------------------
# check 6: feature table
# ---------------------------------------------------------------------------


def feature_table(lines: list[str]) -> Table | None:
    """The first table under a heading whose text says "feature"."""
    marks = headings(lines)
    for position, (index, level, title) in enumerate(marks):
        if "feature" not in title.lower():
            continue
        end = len(lines)
        for other_index, other_level, _title in marks[position + 1 :]:
            if other_level <= level:
                end = other_index
                break
        for table in tables_in(lines, index + 1, end):
            if table.column("status", "state") is not None:
                return table
    return None


def cited_paths(evidence: str) -> list[str]:
    """The repo paths one feature row names, deduplicated, in the order it names them.

    Two patterns because a row writes a path two ways, in backticks and bare inside a
    sentence, and one report per path because a row often quotes the same file twice.
    """
    found = [text for text in re.findall(r"`([^`\n]+)`", evidence) if looks_like_repo_path(text.strip())]
    found += [
        match
        for match in re.findall(
            r"\b(?:tests|tools|records|docs|ticketpath|programs|market_swarm)/[A-Za-z0-9._/-]+",
            evidence,
        )
        if looks_like_repo_path(match)
    ]
    return list(dict.fromkeys(found))


def check_feature_table(root: Path) -> list[Violation]:
    """Every feature row names a file that exists and a status from the closed set."""
    out: list[Violation] = []
    lines = require_lines(root, STATE_DOC)
    table = feature_table(lines)
    if table is None:
        return [
            Violation(
                "feature-table",
                STATE_DOC,
                1,
                "no feature table in records/STATE-OF-PROJECT.md (a heading naming 'features', "
                "a table with a status column, and every row a file plus one of "
                + " | ".join(FEATURE_STATUSES) + ")",
            )
        ]

    status_column = table.column("status", "state")
    name_column = table.column("feature", "item")
    evidence_column = table.column("file", "path", "test", "evidence", "where")
    for label, column in (("status", status_column), ("feature", name_column), ("file or test", evidence_column)):
        if column is None:
            out.append(
                Violation("feature-table", STATE_DOC, table.line,
                          f"the feature table has no {label} column")
            )
    if None in (status_column, name_column, evidence_column):
        return out

    # The same rule as check 1, for the same reason: a row may cite the local artefact its
    # numbers came from, and a path `.gitignore` keeps out of the tree is not a claim about
    # the tree. Asked once for the whole table rather than once per row.
    cited = {
        text
        for _number, cells in table.rows
        for text in cited_paths(" ".join(cells + [""] * (len(table.header) - len(cells))))
    }
    ignored = git_ignored(root, sorted(text for text in cited if not (root / text).exists())) or set()

    for number, cells in table.rows:
        cells = cells + [""] * (len(table.header) - len(cells))
        name = re.sub(r"[`*]", "", cells[name_column]).strip() or "(unnamed)"
        status = re.sub(r"[`*]", "", cells[status_column]).strip().lower()
        status = re.sub(r"[-_]+", " ", status)
        status = " ".join(status.split())
        found = cited_paths(" ".join(cells))
        existing = [text for text in found if (root / text).exists()]

        # A path a row names must exist whatever the status is; the difference between
        # the statuses is what a row owes: a `built` or `tested` row owes a file, and
        # `unverified` / `not built` may honestly say it has none to name. An ignored path
        # counts for neither: it is not a violation to cite it, and it cannot stand as the
        # existing test file a `tested` row owes, because a clone does not have it.
        for text in found:
            if (root / text).exists() or text in ignored:
                continue
            out.append(
                Violation("feature-table", STATE_DOC, number,
                          f"row {name!r} names {text}, which does not exist")
            )
        if status not in FEATURE_STATUSES:
            out.append(
                Violation("feature-table", STATE_DOC, number,
                          f"row {name!r} has status {status!r}; allowed: "
                          + " / ".join(FEATURE_STATUSES))
            )
            continue
        if status in ("built", "tested") and not found:
            out.append(
                Violation("feature-table", STATE_DOC, number,
                          f"row {name!r} claims {status} and names no file or test")
            )
        elif status == "tested" and not any(is_test_file(text) for text in existing):
            out.append(
                Violation("feature-table", STATE_DOC, number,
                          f"row {name!r} claims tested and names no existing "
                          f"tests/test_*.py or market_swarm/tests/test_*.py")
            )
    return out


# ---------------------------------------------------------------------------
# driver
# ---------------------------------------------------------------------------


def check_tree(
    root: Path = REPO_ROOT,
    checks: tuple[str, ...] = CHECKS,
    notes: dict | None = None,
) -> list[Violation]:
    """Run the checks over one tree, in check order, and return every violation.

    `notes` is how a check reports something that is not a violation but is not nothing
    either: `paths` lists the absences an allowance suppressed and the paths `.gitignore`
    keeps out of the tree, and `findings-unique` lists the numbers with several claimants.
    """
    root = Path(root)
    files = tracked_markdown(root)
    found: list[Violation] = []
    if "paths" in checks:
        found += check_paths(root, files, notes)
    if "cross-references" in checks:
        found += check_cross_references(root, files)
    if "findings-unique" in checks:
        found += check_findings_unique(root, files, notes)
    if "ids" in checks:
        found += check_ids(root, files)
    if "program-vs-doc" in checks:
        found += check_program_vs_doc(root)
    if "registry-counts" in checks:
        found += check_registry_counts(root, files)
    if "feature-table" in checks:
        found += check_feature_table(root)
    order = {name: index for index, name in enumerate(CHECKS)}
    return sorted(found, key=lambda item: (order.get(item.check, 99), item.path, item.line))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="doc_check.py",
        description="Fail when the documentation disagrees with the code, or with itself.",
    )
    parser.add_argument("--root", default=str(REPO_ROOT), help="repository root")
    parser.add_argument(
        "--check",
        action="append",
        choices=CHECKS,
        metavar="NAME",
        help="run one check (repeatable); the default is all of them",
    )
    parser.add_argument("--quiet", action="store_true", help="say nothing when clean")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="name the absences an ALLOWED_ABSENCES entry suppressed",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    root = Path(args.root).resolve()
    checks = tuple(args.check) if args.check else CHECKS
    notes: dict = {}
    try:
        violations = check_tree(root, checks, notes)
    except Unreadable as exc:
        print(f"doc_check: {exc}", file=sys.stderr)
        return 2

    allowed = notes.get("allowed") or []
    if args.verbose:
        named = set()
        for entry in allowed:
            if entry.path in named:
                continue
            named.add(entry.path)
            print(f"allowed: {entry.path}: {entry.reason}", file=sys.stderr)

    # A path `.gitignore` excused is counted the same way an allowance is, and named the same
    # way under `--verbose`, because the two are the same promise to a reader: nothing was
    # quietly dropped, and the record says which file decided it.
    ignored = notes.get("ignored") or []
    ignored_names = list(dict.fromkeys(text for text, _relative, _number in ignored))
    if args.verbose:
        for text, relative, number in ignored:
            print(f"ignored: {text}: named by {relative}:{number}, kept out by .gitignore",
                  file=sys.stderr)

    # Warnings are not violations: they are what a reader needs to know that the run is
    # still telling them about. A shared finding number is the one that matters here, and
    # it prints on every run, quiet or not, because the number stays shared until somebody
    # decides which side is renumbered, and that decision is the operator's.
    shared = notes.get("findings_shared") or []
    for line in shared:
        print(f"doc_check: warning: {FINDINGS_DIR} {line}", file=sys.stderr)

    for violation in violations:
        print(violation.render())
    allowance_text = (
        f"; {len(allowed)} allowed absence(s) suppressed by ALLOWED_ABSENCES" if allowed else ""
    )
    ignored_text = (
        f"; {len(ignored_names)} git-ignored path(s) not claimed of the tree" if ignored_names else ""
    )
    if violations:
        files = len({violation.path for violation in violations})
        counted: dict[str, int] = {}
        for violation in violations:
            counted[violation.check] = counted.get(violation.check, 0) + 1
        breakdown = ", ".join(f"{name} {counted[name]}" for name in CHECKS if name in counted)
        print(
            f"doc_check: {len(violations)} violation(s) in {files} file(s) of the tracked tree"
            f" ({breakdown}); the documents disagree with the code{allowance_text}{ignored_text}",
            file=sys.stderr,
        )
        return 1
    if not args.quiet:
        print(
            f"doc_check: clean, {len(checks)} check(s), {root}{allowance_text}{ignored_text}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())

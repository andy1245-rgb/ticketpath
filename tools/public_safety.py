#!/usr/bin/env python3
"""public_safety.py: refuse to publish operational handover material or a credential.

This repository is public and one of the things it holds is a research record written
by agents, which means it holds whatever those agents happened to write down: pids,
absolute paths, the operator's other repositories, a schedule, a key handle. None of
that belongs on a public remote. This checker is the gate.

    python3 tools/public_safety.py check                 # everything git tracks
    python3 tools/public_safety.py check --staged        # what a commit would add
    python3 tools/public_safety.py check --range A..B    # what a push would publish

Exit 0 clean, 1 if anything hit, 2 if the denylist itself could not be read. Hits are
printed one per line as `path:line: class: what`, so a caller can read the log and
see exactly where to look.

What it scans: file NAMES and file CONTENT. The rules live in `.public-denylist`,
next to this file's parent, in plain patterns with a comment each; this module is only
the machinery. Reading a rule list out of a data file means a rule can be added, or
argued with, without touching code, and it keeps the reasons beside the rules.

Deliberate limits, because a checker that lies about its coverage is worse than none:

  * It does not look at history. Nothing here reads old commits; a secret already
    pushed is a different job (rotate it), and rewriting history is the operator's
    call, never a tool's.
  * It does not prove absence of a secret. It proves absence of the shapes listed in
    the denylist. An unusual key shape will pass, and that is why the rule list is
    meant to grow.
  * It does not read the network, write files, or import anything outside the
    standard library. It is safe to run inside a hook.

Standard library only; runs on the Python this repository declares (3.12).
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
DENYLIST_NAME = ".public-denylist"

#: Content rules in these classes are masked when printed. A log line is not a
#: publication, but the log gets copied into chat and into reports, and a matched
#: credential is exactly the string that must not make that trip.
MASKED_CLASSES = frozenset({"private-key", "token-shape", "env-content", "secret-file"})

#: Records are the run's evidence. A content rule scoped "code" skips them; the only
#: rule that needs that scope is the /tmp one, and the reason is in the denylist.
RECORDS_PREFIX = "records/"

MAX_SNIPPET = 160


class DenylistError(Exception):
    """The denylist file could not be read or parsed. Never silently ignored."""


@dataclass(frozen=True)
class Rule:
    cls: str
    kind: str  # "path" | "content"
    scope: str  # "all" | "code"
    regex: re.Pattern[str]
    source: str  # the denylist line, for error messages


@dataclass(frozen=True)
class Exemption:
    glob: str
    classes: frozenset[str]  # class names, or {"*"} for every class
    reason: str


@dataclass(frozen=True)
class Hit:
    path: str
    line: int  # 1-based; 0 means the file NAME matched, not a line
    cls: str
    detail: str

    def render(self) -> str:
        where = self.path if self.line == 0 else f"{self.path}:{self.line}"
        return f"{where}: {self.cls}: {self.detail}"


# ---------------------------------------------------------------------------
# the denylist
# ---------------------------------------------------------------------------


def parse_denylist(text: str) -> tuple[list[Rule], list[Exemption]]:
    """Parse the denylist grammar. Raises DenylistError on a line it cannot read."""
    rules: list[Rule] = []
    exemptions: list[Exemption] = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=2)
        if len(parts) < 3:
            raise DenylistError(f"line {lineno}: need at least three fields: {raw!r}")
        kind, cls, rest = parts

        if kind == "allow":
            # The second field of an allow line is the glob, not the class, so the
            # grammar stays "keyword, subject, ..." for every line kind.
            fields = f"{cls} {rest}".split(maxsplit=2)
            if len(fields) != 3:
                raise DenylistError(
                    f"line {lineno}: allow needs a glob, a class and a reason: {raw!r}"
                )
            glob, exempt_classes, reason = fields
            classes = frozenset(part.strip() for part in exempt_classes.split("|") if part.strip())
            if not classes:
                raise DenylistError(f"line {lineno}: allow needs a class: {raw!r}")
            if len(reason.split()) < 4:
                raise DenylistError(
                    f"line {lineno}: an exception needs a reason someone can argue "
                    f"with: {raw!r}"
                )
            exemptions.append(Exemption(glob=glob, classes=classes, reason=reason))
            continue

        if kind == "path":
            rules.append(_rule(cls, "path", "all", rest, lineno, raw))
            continue

        if kind == "content":
            fields = rest.split(maxsplit=1)
            if len(fields) != 2:
                raise DenylistError(
                    f"line {lineno}: content needs a scope and a pattern: {raw!r}"
                )
            scope, pattern = fields
            if scope not in ("all", "code"):
                raise DenylistError(
                    f"line {lineno}: scope must be 'all' or 'code', not {scope!r}"
                )
            rules.append(_rule(cls, "content", scope, pattern, lineno, raw))
            continue

        raise DenylistError(f"line {lineno}: unknown rule kind {kind!r}: {raw!r}")

    if not rules:
        raise DenylistError("no rules: an empty denylist would pass everything")
    return rules, exemptions


def _rule(
    cls: str,
    kind: str,
    scope: str,
    pattern: str,
    lineno: int,
    raw: str,
) -> Rule:
    try:
        compiled = re.compile(pattern)
    except re.error as exc:
        raise DenylistError(f"line {lineno}: bad regex ({exc}): {raw!r}") from exc
    return Rule(cls=cls, kind=kind, scope=scope, regex=compiled, source=raw.strip())


def load_denylist(path: Path) -> tuple[list[Rule], list[Exemption]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise DenylistError(f"{path}: {exc}") from exc
    return parse_denylist(text)


def _exempt(path: str, cls: str, exemptions: Iterable[Exemption]) -> Exemption | None:
    for entry in exemptions:
        if cls not in entry.classes and "*" not in entry.classes:
            continue
        if fnmatch.fnmatchcase(path, entry.glob):
            return entry
    return None


# ---------------------------------------------------------------------------
# git: what would be public
# ---------------------------------------------------------------------------


def _git(repo: Path, *args: str) -> bytes:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed: {proc.stderr.decode('utf-8', 'replace').strip()}"
        )
    return proc.stdout


def _split_z(data: bytes) -> list[str]:
    return [chunk.decode("utf-8", "surrogateescape") for chunk in data.split(b"\0") if chunk]


@dataclass
class Selection:
    """What to scan, and how to read it. `read` returns None if the blob is absent."""

    label: str
    paths: list[str]
    read: Callable[[str], bytes | None]


def select_tracked(repo: Path) -> Selection:
    """Everything git tracks, read from disk: what the next commit would publish."""
    paths = _split_z(_git(repo, "ls-files", "-z"))

    def read(path: str) -> bytes | None:
        try:
            return (repo / path).read_bytes()
        except OSError:
            return None

    return Selection(label="tracked tree", paths=paths, read=read)


def select_staged(repo: Path) -> Selection:
    """Files a commit would add or change, read from the index (not the worktree)."""
    paths = _split_z(
        _git(repo, "diff", "--cached", "--name-only", "--diff-filter=ACMR", "-z")
    )

    def read(path: str) -> bytes | None:
        return _blob(repo, f":{path}")

    return Selection(label="staged", paths=paths, read=read)


def select_range(repo: Path, spec: str) -> Selection:
    """Files a push would publish, read from the end revision of the range."""
    if ".." not in spec:
        raise ValueError(f"range must look like A..B, got {spec!r}")
    left, _, right = spec.partition("..")
    right = right or "HEAD"
    left = left or "HEAD"
    if right.startswith("..."):  # tolerate A...B
        right = right[3:] or "HEAD"
    paths = _split_z(
        _git(
            repo,
            "diff",
            "--name-only",
            "--diff-filter=ACMR",
            f"{left}..{right}",
            "-z",
        )
    )

    def read(path: str) -> bytes | None:
        return _blob(repo, f"{right}:{path}")

    return Selection(label=f"range {left}..{right}", paths=paths, read=read)


def _blob(repo: Path, object_name: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", object_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        return None
    return proc.stdout


# ---------------------------------------------------------------------------
# scanning
# ---------------------------------------------------------------------------


def _is_records(path: str) -> bool:
    return path.startswith(RECORDS_PREFIX)


def _looks_binary(data: bytes) -> bool:
    return b"\0" in data[:8192]


def scan(
    selection: Selection,
    rules: list[Rule],
    exemptions: list[Exemption],
    repo: Path = REPO_ROOT,
) -> list[Hit]:
    """Return every hit, in path then line order. Pure: reads only."""
    hits: list[Hit] = []
    path_rules = [r for r in rules if r.kind == "path"]
    content_rules = [r for r in rules if r.kind == "content"]

    for path in sorted(set(selection.paths)):
        for rule in path_rules:
            if rule.regex.search(path) and _exempt(path, rule.cls, exemptions) is None:
                hits.append(Hit(path=path, line=0, cls=rule.cls, detail="file name"))
        data = selection.read(path)
        if data is None or _looks_binary(data):
            continue
        applicable = [
            r for r in content_rules if r.scope == "all" or not _is_records(path)
        ]
        if not applicable:
            continue
        text = data.decode("utf-8", "replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for rule in applicable:
                match = rule.regex.search(line)
                if match is None:
                    continue
                if _exempt(path, rule.cls, exemptions) is not None:
                    continue
                hits.append(
                    Hit(
                        path=path,
                        line=lineno,
                        cls=rule.cls,
                        detail=_detail(rule.cls, line, match),
                    )
                )
    return hits


def _detail(cls: str, line: str, match: re.Match[str]) -> str:
    if cls in MASKED_CLASSES:
        return f"[{len(match.group(0))} chars redacted]"
    snippet = " ".join(line.strip().split())
    if len(snippet) > MAX_SNIPPET:
        snippet = snippet[: MAX_SNIPPET - 1] + "…"
    return snippet


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="public_safety.py",
        description="Refuse to publish operational handover material or a credential.",
    )
    sub = parser.add_subparsers(dest="verb", required=True)
    check = sub.add_parser("check", help="scan what would be public")
    which = check.add_mutually_exclusive_group()
    which.add_argument(
        "--tracked", action="store_true", help="every tracked file (the default)"
    )
    which.add_argument(
        "--staged", action="store_true", help="what the next commit would add"
    )
    which.add_argument("--range", metavar="A..B", help="what a push would publish")
    check.add_argument("--repo", default=str(REPO_ROOT), help="repository root")
    check.add_argument(
        "--denylist", default=None, help=f"denylist path (default: <repo>/{DENYLIST_NAME})"
    )
    check.add_argument("--quiet", action="store_true", help="say nothing when clean")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    repo = Path(args.repo).resolve()
    denylist_path = Path(args.denylist) if args.denylist else repo / DENYLIST_NAME

    try:
        rules, exemptions = load_denylist(denylist_path)
    except DenylistError as exc:
        print(f"public_safety: denylist unreadable: {exc}", file=sys.stderr)
        return 2

    try:
        if args.range:
            selection = select_range(repo, args.range)
        elif args.staged:
            selection = select_staged(repo)
        else:
            selection = select_tracked(repo)
    except (RuntimeError, ValueError) as exc:
        print(f"public_safety: {exc}", file=sys.stderr)
        return 2

    hits = scan(selection, rules, exemptions, repo=repo)

    for hit in hits:
        print(hit.render())
    if hits:
        files = len({hit.path for hit in hits})
        print(
            f"public_safety: {len(hits)} hit(s) in {files} file(s) of {selection.label}"
            f"; do not commit or push this",
            file=sys.stderr,
        )
        return 1
    if not args.quiet:
        print(f"public_safety: clean, {selection.label}, {len(selection.paths)} file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())

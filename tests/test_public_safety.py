"""The public-safety gate, tested against a git repository it has never seen.

The thing under test decides whether research material may be published, so a test that
only proves it returns zero on a good tree would prove nothing: zero is also what a
broken checker returns. Every test here therefore builds a scratch repository in a
temporary directory, plants exactly one class of forbidden material, and asserts the
checker names that class at that path. A second test runs the same assertions against a
stub checker that always answers clean, and asserts that every one of them fails -- the
suite demonstrates its own ability to fail rather than asserting it.

Fixtures are assembled by concatenation (`"ghp" + "_" + ...`) so that this file, which is
tracked and public, does not itself contain a credential shape. That is not decoration:
the checker scans this file too, and `check --tracked` has to stay clean on it.

The one thing this file cannot prove is that the denylist is complete. It proves the
rules that exist fire, and fire only where they should.
"""

from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOL = REPO_ROOT / "tools" / "public_safety.py"
DENYLIST = REPO_ROOT / ".public-denylist"

HIT_RE = re.compile(r"^(?P<path>.+?)(?::(?P<line>\d+))?: (?P<cls>[a-z][a-z-]*): (?P<detail>.*)$")

# Credential shapes, assembled so the literal never appears in this file.
GITHUB_TOKEN = "ghp" + "_" + "a1b2c3d4e5f6g7h8i9j0k1l2"
GITHUB_PAT = "github" + "_pat_" + "11AA22bb33CC44dd55EE66ff77"
OPENAI_KEY = "sk" + "-" + "Q7w8E9r0T1y2U3i4O5p6A7s8"
ANTHROPIC_KEY = "sk" + "-ant-" + "api03-" + "Zx9Cv8Bn7Mm6"
AWS_KEY_ID = "AKIA" + "Q7W8E9R0T1Y2U3I4"
SLACK_TOKEN = "xox" + "b-" + "123456789012-" + "abcdefghijkl"
OAUTH_ASSIGNMENT = "CLAUDE_CODE_OAUTH_TOKEN" + "=" + "oauth" + "9" * 16
PEM_BLOCK = (
    "-----BEGIN "
    + "RSA PRIVATE KEY-----"
    + "\nMIIEowIBAAKCAQEA1234567890abcdefghij\n"
    + "-----END "
    + "RSA PRIVATE KEY-----"
    + "\n"
)


@dataclass(frozen=True)
class Case:
    """One forbidden thing, planted in one file, and the class that must name it."""

    name: str
    files: dict[str, str]
    expect: frozenset[str] = frozenset()  # classes that must appear, and only these
    denylist: Path = DENYLIST
    note: str = ""


def as_bytes(text: str) -> int:
    return len(text.encode("utf-8"))


# The pattern classes, one case each. `expect` empty means the file must come back clean:
# those cases are the half that stops the checker from firing on ordinary prose.
CASES: tuple[Case, ...] = (
    Case(
        "handover-filename",
        {"NIGHT-BRIEF.md": "Session opened. Everything below is this machine.\n"},
        frozenset({"handover-file"}),
        note="an operational handover document's own name",
    ),
    Case(
        "snapshot-directory",
        {"night-snapshot-20261107T164828Z/WIP.diff": "diff --git a/x b/x\n"},
        frozenset({"handover-file"}),
        note="a snapshot directory holding the night's in-flight edits",
    ),
    Case(
        "wip-handover-filename",
        {"docs/HANDOVER-legacy.md": "How to take over this run.\n"},
        frozenset({"handover-file"}),
        note="a handover document under another name",
    ),
    Case(
        "secret-filename",
        {".env": "TICKETPATH_PORT=8788\n"},
        frozenset({"secret-file"}),
        note="a file that is a credential by existing",
    ),
    Case(
        "fleet-repo-content",
        {"docs/notes.md": "The fleet runs out of fleet-manager and agentFleet.\n"},
        frozenset({"fleet-repo"}),
        note="the operator's other repositories, named in prose",
    ),
    Case(
        "home-path-content",
        {"docs/run.md": "cd /home/friend/ticketPricing && python3 -m ticketpath.server\n"},
        frozenset({"home-path"}),
        note="an absolute home path: machine layout and a user name",
    ),
    Case(
        "tmp-path-in-code",
        {"tools/thing.py": 'LOG = "/tmp/thing.log"\n'},
        frozenset({"tmp-path"}),
        note="a scratch path in code",
    ),
    Case(
        "tmp-path-quoted-in-records",
        {"records/RUN.md": "The sweep ran from /tmp/audit12/sweep.py.\n"},
        frozenset(),
        note="the stated exception: records quote /tmp, and a quote is evidence",
    ),
    Case(
        "tmp-path-quoted-in-the-frontend-record",
        {
            "frontend/VERIFY.md": (
                '$ node "$SHOT" http://127.0.0.1:3010/ /tmp/seatpass-1440.png --full\n'
            )
        },
        frozenset(),
        note="the frontend's records paste the output of their own /tmp run, as records/ may",
    ),
    Case(
        "tmp-path-in-frontend-code",
        {"frontend/tools/build-copy.sh": 'DST="/tmp/seatpass-build"\n'},
        frozenset({"tmp-path"}),
        note="the frontend exemption is its markdown; its scripts are still code",
    ),
    Case(
        "env-example-is-not-a-secret",
        {"frontend/.env.example": "NEXT_PUBLIC_API_BASE_URL=\nNEXT_PUBLIC_PROGRAM_ID=\n"},
        frozenset(),
        note="the tracked template a reader copies: the class is for files that are a credential by existing",
    ),
    Case(
        "real-env-beside-the-example",
        {"frontend/.env": "NEXT_PUBLIC_API_BASE_URL=https://api.example.org\n"},
        frozenset({"secret-file"}),
        note="one directory over from the example, and still a credential by existing",
    ),
    Case(
        "cron-line",
        {"docs/schedule.md": "*/15 * * * * /usr/local/bin/publish.sh\n"},
        frozenset({"cron-line"}),
        note="a scheduled job on his machine",
    ),
    Case(
        "deploy-key-path",
        {"docs/deploy.md": "The push runs with ~/.ssh/ticketpath_deploy_ed25519.\n"},
        frozenset({"deploy-key"}),
        note="the name of the deploy key",
    ),
    Case(
        "live-service-pid",
        {"records/STATE.md": "- The runner (pid 218725) is still going.\n"},
        frozenset({"live-service"}),
        note="a pid is a handle on a live process",
    ),
    Case(
        "live-service-port",
        {"docs/state.md": ":3000 is the operator's live frontend.\n"},
        frozenset({"live-service"}),
        note="a port tied on the same line to a running process",
    ),
    Case(
        "bare-port-in-design-note",
        {"README.md": "It binds 8788; 8787 is refused because another process owns it.\n"},
        frozenset(),
        note="a port in a design statement is not handover; the rule needs the context",
    ),
    Case(
        "private-key-block",
        {"fixtures/deploy.pem.txt": PEM_BLOCK},
        frozenset({"private-key"}),
        note="a PEM private key block",
    ),
    Case(
        "token-github-pat",
        {"docs/ci.md": f"token: {GITHUB_TOKEN}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-github-fine-grained",
        {"docs/ci.md": f"token: {GITHUB_PAT}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-openai",
        {"docs/ci.md": f"key {OPENAI_KEY}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-anthropic",
        {"docs/ci.md": f"key {ANTHROPIC_KEY}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-aws",
        {"docs/ci.md": f"aws {AWS_KEY_ID}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-slack",
        {"docs/ci.md": f"slack {SLACK_TOKEN}\n"},
        frozenset({"token-shape"}),
    ),
    Case(
        "token-oauth-assignment",
        {"docs/ci.md": OAUTH_ASSIGNMENT + "\n"},
        frozenset({"token-shape", "env-content"}),
        note="a named OAuth token with a value is both a token shape and an assignment",
    ),
    Case(
        "risk-adjusted-is-not-a-key",
        {"docs/model.md": "an objective that is risk-adjusted and risk-aware\n"},
        frozenset(),
        note="`sk-` needs its word boundary, or every risk-adjusted sentence is a hit",
    ),
    Case(
        "env-assignment",
        {"docs/setup.md": "API_KEY=abcdef123456\n"},
        frozenset({"env-content"}),
    ),
    Case(
        "env-reference-and-public-var-are-not-secrets",
        {
            "docs/setup.md": "TOKEN=$GITHUB_TOKEN\nNEXT_PUBLIC_API_BASE_URL=http://localhost:8788\nSEED = bytes(range(32))\nSEED = 20261107\n"
        },
        frozenset(),
        note="references, public config and deterministic seeds were false positives",
    ),
    Case(
        "contact-email",
        {"docs/terms.md": "Report a violation to enforcement@presalegroup.com.\n"},
        frozenset({"contact-email"}),
        note="a real address on a real domain is still a hit",
    ),
    Case(
        "contact-email-reserved-documentation-addresses",
        {
            "docs/setup.md": (
                "Set MAIL=nobody@example.com; also host@example.org, ops@example.net,\n"
                "user@example.invalid, user@mail.example.test, admin@something.example and\n"
                "12345+andy@users.noreply.github.com.\n"
            )
        },
        frozenset(),
        note=(
            "RFC 2606 and RFC 6761 reserve example.*, *.invalid, *.test and *.example for"
            " documentation: those cannot be a third party's address"
        ),
    ),
    Case(
        "contact-email-reserved-looking-real-domain",
        {"docs/setup.md": "Write to legal@notexample.com or support@test.com.\n"},
        frozenset({"contact-email"}),
        note="the exclusion is on the reserved label, not on a domain that resembles one",
    ),
    Case(
        "contact-email-github-is-not-a-contact",
        {"docs/remote.md": "remote git@github.com:andy1245-rgb/ticketpath.git\n"},
        frozenset(),
        note="the repository's own wiring is already public",
    ),
    Case(
        "contact-email-allowlisted-in-records",
        {"records/00-prior-direction-index.md": "disqualification and a report to `cheating@mlh.io`\n"},
        frozenset(),
        note="the recorded quote of the hackathon's own published address",
    ),
    Case(
        "personal-name-in-docs",
        {"docs/about.md": "Copyright (c) 2026 Andrew Radu\n"},
        frozenset({"personal-name"}),
    ),
    Case(
        "personal-name-allowlisted-in-licence",
        {"LICENSE": "MIT License\n\nCopyright (c) 2026 Andrew Radu\n"},
        frozenset(),
        note="the licence has to carry the name to be a licence",
    ),
    Case(
        "allowlist-is-per-class-not-per-file",
        {
            "records/00-prior-direction-index.md": (
                "Report to `cheating@mlh.io`; the runner (pid 218725) is still going.\n"
            )
        },
        frozenset({"live-service"}),
        note="the record is exempt for the quoted address and not for the pid",
    ),
    Case(
        "allowlisted-classes-are-the-only-ones-exempt",
        {
            "tests/test_public_safety.py": (
                f"The fleet runs in fleet-manager.\nkey {GITHUB_TOKEN}\n"
            )
        },
        frozenset({"token-shape"}),
        note="this file is exempt for the material classes it plants and not for a credential",
    ),
    Case(
        "denylist-spells-its-own-patterns",
        {".public-denylist": DENYLIST.read_text(encoding="utf-8")},
        frozenset(),
        note="the rule file must be allowed to name the rules",
    ),
)


class ScratchRepo:
    """A throwaway git repository, removed when the test that made it ends."""

    def __init__(self, root: Path) -> None:
        self.root = root

    @classmethod
    def create(cls, files: dict[str, str], history: int = 0) -> "ScratchRepo":
        root = Path(tempfile.mkdtemp(prefix="public-safety-"))
        repo = cls(root)
        repo.git("init", "-q")
        for i in range(history):
            (root / "README.md").write_text(f"baseline {i}\n", encoding="utf-8")
            repo.git("add", "-f", "-A", ".")
            repo.git("commit", "-q", "-m", f"baseline {i}")
        for name, text in files.items():
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        repo.git("add", "-f", "-A", ".")
        return repo

    def git(self, *args: str) -> str:
        proc = subprocess.run(
            [
                "git",
                "-C",
                str(self.root),
                "-c",
                "user.name=test",
                "-c",
                "user.email=test@example.invalid",
                "-c",
                "commit.gpgsign=false",
                "-c",
                "core.hooksPath=/dev/null",
                *args,
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            raise AssertionError(f"git {' '.join(args)} failed: {proc.stderr}")
        return proc.stdout

    def remove(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


@dataclass
class Result:
    code: int
    hits: list[tuple[str, int, str, str]]
    stdout: str = ""
    stderr: str = ""

    @property
    def classes(self) -> set[str]:
        return {hit[2] for hit in self.hits}


class RealChecker:
    """The tool, run the way a hook or the push script runs it."""

    name = "real"

    def check(self, root: Path, mode: tuple[str, ...], denylist: Path) -> Result:
        argv = [
            sys.executable,
            str(TOOL),
            "check",
            "--repo",
            str(root),
            "--denylist",
            str(denylist),
            *mode,
        ]
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=120, check=False)
        return Result(
            code=proc.returncode,
            hits=parse_hits(proc.stdout),
            stdout=proc.stdout,
            stderr=proc.stderr,
        )


class AlwaysCleanChecker:
    """The stub: a checker that answers clean to everything, including a live secret.

    It exists to be caught. Any test that cannot tell this apart from the real tool is
    not testing anything, and `test_every_positive_case_fails_against_a_stub` asserts
    that each one can.
    """

    name = "always-clean"

    def check(self, root: Path, mode: tuple[str, ...], denylist: Path) -> Result:
        return Result(code=0, hits=[], stdout="", stderr="")


def parse_hits(stdout: str) -> list[tuple[str, int, str, str]]:
    hits: list[tuple[str, int, str, str]] = []
    for line in stdout.splitlines():
        match = HIT_RE.match(line)
        if match is None:
            continue
        hits.append(
            (
                match.group("path"),
                int(match.group("line") or 0),
                match.group("cls"),
                match.group("detail"),
            )
        )
    return hits


def scratch(files: dict[str, str]) -> ScratchRepo:
    repo = ScratchRepo.create(files)
    return repo


def public_tree() -> list[str]:
    """Every path a commit could publish: tracked files plus untracked, unignored ones."""
    proc = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "ls-files", "--cached", "--others",
         "--exclude-standard", "-z"],
        capture_output=True,
        check=False,
    )
    return [p.decode("utf-8", "surrogateescape") for p in proc.stdout.split(b"\0") if p]


BY_NAME = {case.name: case for case in CASES}


class TestPatternClasses(unittest.TestCase):
    """One test per class of forbidden material, plus the near misses that must not fire."""

    def case(self, name: str) -> Case:
        return BY_NAME[name]

    def assert_case(self, case: Case, checker: object | None = None) -> None:
        """The assertion every case goes through, real or stub. Raises AssertionError."""
        engine = checker or RealChecker()
        repo = scratch(case.files)
        try:
            result = engine.check(repo.root, ("--tracked",), case.denylist)  # type: ignore[attr-defined]
        finally:
            repo.remove()

        if not case.expect:
            self.assertEqual(
                result.hits, [], f"{case.name}: expected no hits, got {result.hits}"
            )
            self.assertEqual(result.code, 0, f"{case.name}: expected exit 0, got {result.code}")
            return

        self.assertNotEqual(
            result.code,
            0,
            f"{case.name}: expected exit 1 for {sorted(case.expect)}, got {result.code}",
        )
        self.assertEqual(
            result.classes,
            set(case.expect),
            f"{case.name}: expected exactly {sorted(case.expect)}, got {sorted(result.classes)}",
        )
        for path, _line, _cls, _detail in result.hits:
            self.assertIn(
                path, case.files, f"{case.name}: a hit came from a file the case did not plant"
            )

    def test_handover_filenames(self) -> None:
        self.assert_case(self.case("handover-filename"))

    def test_snapshot_directories(self) -> None:
        self.assert_case(self.case("snapshot-directory"))

    def test_wip_handover_filenames(self) -> None:
        self.assert_case(self.case("wip-handover-filename"))

    def test_secret_filenames(self) -> None:
        self.assert_case(self.case("secret-filename"))

    def test_fleet_repo_names(self) -> None:
        self.assert_case(self.case("fleet-repo-content"))

    def test_home_paths(self) -> None:
        self.assert_case(self.case("home-path-content"))

    def test_tmp_path_in_code(self) -> None:
        self.assert_case(self.case("tmp-path-in-code"))

    def test_tmp_path_is_exempt_in_records(self) -> None:
        self.assert_case(self.case("tmp-path-quoted-in-records"))

    def test_tmp_path_is_exempt_in_the_frontend_records(self) -> None:
        self.assert_case(self.case("tmp-path-quoted-in-the-frontend-record"))

    def test_tmp_path_in_frontend_code_still_fires(self) -> None:
        self.assert_case(self.case("tmp-path-in-frontend-code"))

    def test_an_env_example_is_not_a_secret_file(self) -> None:
        """The one `.env*` a public tree may hold, and the reason it needs an entry.

        The `secret-file` PATH rule matches any `.env` or `.env.<anything>`, deliberately:
        that is what a build writes and what a value ends up in. The tracked template a
        reader copies is the exception, and it is one exact path rather than a pattern, so
        this case and the one below are the two directions of that claim.
        """
        self.assert_case(self.case("env-example-is-not-a-secret"))

    def test_a_real_env_beside_the_example_is_still_refused(self) -> None:
        self.assert_case(self.case("real-env-beside-the-example"))

    def test_cron_lines(self) -> None:
        self.assert_case(self.case("cron-line"))

    def test_deploy_key_path(self) -> None:
        self.assert_case(self.case("deploy-key-path"))

    def test_pids(self) -> None:
        self.assert_case(self.case("live-service-pid"))

    def test_live_port_in_prose(self) -> None:
        self.assert_case(self.case("live-service-port"))

    def test_a_bare_port_in_a_design_note_is_not_a_hit(self) -> None:
        self.assert_case(self.case("bare-port-in-design-note"))

    def test_private_key_blocks(self) -> None:
        self.assert_case(self.case("private-key-block"))

    def test_token_shapes(self) -> None:
        for name in (
            "token-github-pat",
            "token-github-fine-grained",
            "token-openai",
            "token-anthropic",
            "token-aws",
            "token-slack",
            "token-oauth-assignment",
        ):
            with self.subTest(case=name):
                self.assert_case(self.case(name))

    def test_risk_adjusted_is_not_a_key(self) -> None:
        self.assert_case(self.case("risk-adjusted-is-not-a-key"))

    def test_env_assignments(self) -> None:
        self.assert_case(self.case("env-assignment"))

    def test_env_near_misses(self) -> None:
        self.assert_case(self.case("env-reference-and-public-var-are-not-secrets"))

    def test_contact_emails(self) -> None:
        self.assert_case(self.case("contact-email"))

    def test_reserved_documentation_addresses_are_not_contacts(self) -> None:
        self.assert_case(self.case("contact-email-reserved-documentation-addresses"))

    def test_a_domain_that_resembles_a_reserved_name_is_still_a_contact(self) -> None:
        self.assert_case(self.case("contact-email-reserved-looking-real-domain"))

    def test_github_addresses_are_not_contacts(self) -> None:
        self.assert_case(self.case("contact-email-github-is-not-a-contact"))

    def test_allowlisted_quote_in_records(self) -> None:
        self.assert_case(self.case("contact-email-allowlisted-in-records"))

    def test_personal_name_in_docs(self) -> None:
        self.assert_case(self.case("personal-name-in-docs"))

    def test_personal_name_is_allowed_in_the_licence(self) -> None:
        self.assert_case(self.case("personal-name-allowlisted-in-licence"))

    def test_allowlist_applies_to_one_class_not_the_file(self) -> None:
        self.assert_case(self.case("allowlist-is-per-class-not-per-file"))

    def test_the_denylist_may_name_its_own_patterns(self) -> None:
        self.assert_case(self.case("denylist-spells-its-own-patterns"))

    def test_an_exception_lists_classes_and_does_not_cover_the_rest(self) -> None:
        self.assert_case(self.case("allowlisted-classes-are-the-only-ones-exempt"))

    def test_every_positive_case_fails_against_a_stub_that_always_says_clean(self) -> None:
        """The suite's own failure mode, demonstrated rather than claimed.

        Positive cases must fail against the stub: their assertions are the difference
        between a working check and a rubber stamp. Negative cases are expected to pass
        against it, and that is stated here rather than hidden -- a case that asserts
        absence cannot distinguish a correct checker from a silent one, so each negative
        case is paired with a positive one in this table.
        """
        stub = AlwaysCleanChecker()
        caught: list[str] = []
        squibbed: list[str] = []
        for case in CASES:
            try:
                self.assert_case(case, stub)
            except AssertionError:
                caught.append(case.name)
            else:
                squibbed.append(case.name)

        positive = sorted(case.name for case in CASES if case.expect)
        self.assertEqual(sorted(caught), positive, "a positive case did not catch the stub")
        self.assertEqual(
            sorted(squibbed), sorted(case.name for case in CASES if not case.expect)
        )
        if os.environ.get("PUBLIC_SAFETY_STUB_EVIDENCE"):
            for case in CASES:
                verdict = "FAILS against the stub" if case.name in caught else "passes the stub"
                print(f"stub-evidence: {case.name:<45} {case.note or '':<60} {verdict}")


class TestTheGateHolds(unittest.TestCase):
    """The behaviours the commit hook and the push script depend on."""

    def test_no_two_cases_share_a_name(self) -> None:
        """A duplicate name would silently point a test at the wrong case."""
        self.assertEqual(len(BY_NAME), len(CASES))

    def test_a_clean_tree_passes(self) -> None:
        repo = scratch(
            {
                "README.md": "# ticketpath\n\nRun `python3 -m ticketpath.server` on 8788.\n",
                "records/00.md": "The sweep ran from /tmp/audit12/sweep.py at 14:16Z.\n",
                "tools/run.py": "PORT = 8788\n",
                "LICENSE": "MIT License\n\nCopyright (c) 2026 Andrew Radu\n",
            }
        )
        self.addCleanup(repo.remove)
        result = RealChecker().check(repo.root, ("--tracked",), DENYLIST)
        self.assertEqual(result.hits, [], f"a clean tree produced hits: {result.hits}")
        self.assertEqual(result.code, 0)
        self.assertIn("clean", result.stdout)

    def test_a_hit_is_reported_with_a_path_a_line_and_a_class(self) -> None:
        repo = scratch({"records/STATE.md": "line one\nline two\n- runner (pid 424242)\n"})
        self.addCleanup(repo.remove)
        result = RealChecker().check(repo.root, ("--tracked",), DENYLIST)
        self.assertEqual(result.code, 1)
        self.assertEqual(result.hits[0][0], "records/STATE.md")
        self.assertEqual(result.hits[0][1], 3, "the line number is what makes the report usable")
        self.assertEqual(result.hits[0][2], "live-service")

    def test_staged_mode_sees_what_the_index_would_commit(self) -> None:
        repo = scratch({"README.md": "clean\n"})
        self.addCleanup(repo.remove)
        (repo.root / "docs").mkdir()
        (repo.root / "docs" / "leak.md").write_text(f"key {GITHUB_TOKEN}\n", encoding="utf-8")
        repo.git("add", "-f", "-A", ".")
        result = RealChecker().check(repo.root, ("--staged",), DENYLIST)
        self.assertEqual(result.code, 1)
        self.assertEqual(result.classes, {"token-shape"})
        self.assertEqual({hit[0] for hit in result.hits}, {"docs/leak.md"})

    def test_staged_mode_reads_the_index_not_the_worktree(self) -> None:
        """A secret staged and then deleted from the worktree is still in the commit."""
        repo = scratch({"README.md": "clean\n"})
        self.addCleanup(repo.remove)
        leak = repo.root / "leak.md"
        leak.write_text(f"key {GITHUB_TOKEN}\n", encoding="utf-8")
        repo.git("add", "-f", "-A", ".")
        leak.unlink()
        result = RealChecker().check(repo.root, ("--staged",), DENYLIST)
        self.assertEqual({hit[0] for hit in result.hits}, {"leak.md"})

    def test_range_mode_catches_a_committed_secret_that_a_push_would_publish(self) -> None:
        """This is the push gate: origin/main..HEAD, read from the commit, not the disk."""
        repo = ScratchRepo.create({"README.md": "clean\n"}, history=1)
        self.addCleanup(repo.remove)
        leak = repo.root / "scripts" / "deploy.md"
        leak.parent.mkdir()
        leak.write_text("ssh -i ~/.ssh/ticketpath_deploy_ed25519 git@host\n", encoding="utf-8")
        repo.git("add", "-f", "-A", ".")
        repo.git("commit", "-q", "-m", "add deploy notes")
        result = RealChecker().check(repo.root, ("--range", "HEAD~1..HEAD"), DENYLIST)
        self.assertEqual(result.code, 1)
        self.assertEqual(result.classes, {"deploy-key"})

    def test_range_mode_passes_a_clean_commit(self) -> None:
        repo = ScratchRepo.create({"README.md": "clean\n"}, history=1)
        self.addCleanup(repo.remove)
        (repo.root / "docs.md").write_text("It binds 8788.\n", encoding="utf-8")
        repo.git("add", "-f", "-A", ".")
        repo.git("commit", "-q", "-m", "docs")
        result = RealChecker().check(repo.root, ("--range", "HEAD~1..HEAD"), DENYLIST)
        self.assertEqual(result.hits, [])
        self.assertEqual(result.code, 0)

    def test_a_denylist_that_does_not_parse_is_an_error_not_a_pass(self) -> None:
        """A silently skipped rule is how a gate becomes a formality."""
        repo = scratch({"README.md": "clean\n"})
        self.addCleanup(repo.remove)
        broken = repo.root / "broken-denylist"
        broken.write_text("content token-shape all (unclosed\n", encoding="utf-8")
        result = RealChecker().check(repo.root, ("--tracked",), broken)
        self.assertEqual(result.code, 2, "an unreadable denylist must not exit 0")
        self.assertIn("bad regex", result.stderr)

    def test_an_empty_denylist_is_refused(self) -> None:
        repo = scratch({"README.md": "clean\n"})
        self.addCleanup(repo.remove)
        empty = repo.root / "empty-denylist"
        empty.write_text("# nothing but comments\n", encoding="utf-8")
        result = RealChecker().check(repo.root, ("--tracked",), empty)
        self.assertEqual(result.code, 2)

    def test_an_exception_without_a_reason_is_refused(self) -> None:
        repo = scratch({"README.md": "clean\n"})
        self.addCleanup(repo.remove)
        thin = repo.root / "thin-denylist"
        thin.write_text(
            "path handover-file ^NIGHT-\nallow LICENSE personal-name because\n", encoding="utf-8"
        )
        result = RealChecker().check(repo.root, ("--tracked",), thin)
        self.assertEqual(result.code, 2)
        self.assertIn("reason", result.stderr)

    def test_the_shipped_denylist_parses_and_covers_every_class(self) -> None:
        """Guard against a denied class losing its last rule during an edit."""
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import public_safety  # noqa: PLC0415

        rules, exemptions = public_safety.load_denylist(DENYLIST)
        covered = {rule.cls for rule in rules}
        for cls in ("handover-file", "secret-file", "fleet-repo", "home-path", "tmp-path",
                    "cron-line", "deploy-key", "live-service", "private-key", "token-shape",
                    "env-content", "contact-email", "personal-name"):
            self.assertIn(cls, covered, f"no rule left for {cls}")
        for entry in exemptions:
            self.assertGreaterEqual(
                len(entry.reason.split()), 4, f"exception {entry.glob} has no usable reason"
            )
        classes_in_cases = {cls for case in CASES for cls in (case.expect or ())}
        self.assertEqual(
            classes_in_cases,
            covered,
            "a class in the denylist has no test, or a test names a class that is not denied",
        )


class TestTheRecordsAllowlists(unittest.TestCase):
    """Four records quote what a run measured, and the imported frontend's do too.

    These records hold a pid in a state table, an absolute path inside a command's output
    and the licence line a check read. Those quotes are the run's evidence and cannot be
    edited without falsifying the evidence, so the classes they trip are exempt -- but for
    one named file and one named set of classes. The two tests below are the difference
    between that statement and a rubber stamp: one proves the entries as written, the other
    proves nothing outside the four files inherits them.
    """

    EXPECTED = {
        "records/BUILD-REPORT-CONSOLE.md": {"live-service", "personal-name"},
        "records/findings/13-submission-readiness.md": {"home-path", "personal-name"},
        "records/findings/14-frontend-attach-explore.md": {"home-path", "live-service"},
        "records/findings/15-visionhelper.md": {"home-path", "live-service"},
    }

    #: The same material, planted where the exemption should and should not reach.
    EXEMPT_FILE = {
        "records/BUILD-REPORT-CONSOLE.md": "- the runner (pid 242675) is still going.\n",
        "records/findings/13-submission-readiness.md": "cd /home/friend/ticketPricing\n",
        "records/findings/14-frontend-attach-explore.md": "- the copy (pid 81447) answered 200.\n",
        "records/findings/15-visionhelper.md": "ls -la /home/friend/visionHelper\n",
    }
    MUST_STILL_FIRE = {
        "records/findings/12-final-audit.md": "- the runner (pid 242675) is still going.\n",
        "tools/shot.py": 'OUT = "/home/friend/visionHelper/out.png"\n',
        "docs/SHOTS.md": "- the runner (pid 242675) is still going.\n",
        "README.md": "- the runner (pid 242675) is still going.\n",
    }

    def entries(self) -> dict[str, object]:
        sys.path.insert(0, str(REPO_ROOT / "tools"))
        import public_safety  # noqa: PLC0415

        _, exemptions = public_safety.load_denylist(DENYLIST)
        return {entry.glob: entry for entry in exemptions}

    def test_each_record_exemption_names_one_file_and_its_own_classes(self) -> None:
        entries = self.entries()
        tree = public_tree()
        for glob, classes in self.EXPECTED.items():
            with self.subTest(glob=glob):
                entry = entries.get(glob)
                self.assertIsNotNone(entry, f"no exception for {glob}")
                self.assertTrue((REPO_ROOT / glob).is_file(), f"{glob} is not a file")
                self.assertEqual(set(entry.classes), classes)  # type: ignore[attr-defined]
                self.assertNotIn("*", entry.classes)  # type: ignore[attr-defined]
                matched = [p for p in tree if fnmatch.fnmatchcase(p, glob)]
                self.assertEqual(
                    matched, [glob], f"{glob} is not one exact file, it matches {len(matched)}"
                )

    def test_no_exemption_for_records_reaches_a_file_outside_records(self) -> None:
        """Every records/ exception, old and new, matches only paths under records/.

        A glob that is one level too wide is the failure this catches: `records/*` is the
        contact-email quote and stops at the directory, and each of the four new entries is
        an exact path, so code under tools/ and a doc under docs/ are still checked.
        """
        entries = self.entries()
        tree = public_tree()
        self.assertGreater(len(tree), 100, "the tree came back empty, so this proves nothing")
        for glob, entry in entries.items():
            if not glob.startswith("records/"):
                continue
            with self.subTest(glob=glob):
                self.assertNotIn("*", entry.classes)  # type: ignore[attr-defined]
                matched = [p for p in tree if fnmatch.fnmatchcase(p, glob)]
                self.assertTrue(matched, f"{glob} matches nothing, so it exempts nothing")
                outside = [p for p in matched if not p.startswith("records/")]
                self.assertEqual(outside, [], f"{glob} reaches outside records/: {outside}")

    def test_a_record_exemption_does_not_reach_a_neighbour_or_a_tool(self) -> None:
        """Same material, four places: clean in the file named, a hit everywhere else."""
        repo = scratch({**self.EXEMPT_FILE, **self.MUST_STILL_FIRE})
        self.addCleanup(repo.remove)
        result = RealChecker().check(repo.root, ("--tracked",), DENYLIST)
        self.assertEqual(
            {hit[0] for hit in result.hits},
            set(self.MUST_STILL_FIRE),
            "a records exemption covered a file it does not name",
        )
        self.assertEqual(result.code, 1)

    def test_the_frontend_exemption_is_its_markdown_one_level_deep(self) -> None:
        """One glob, one class, and it stops before the frontend's code.

        The imported frontend's records quote the /tmp paths their own run wrote, the
        same reason records/ may. The entry is checked for width because that is how an
        exemption becomes a rubber stamp: `frontend/*` would cover `frontend/tools/`,
        and a glob one level too wide exempts the script that writes the path.
        """
        entry = self.entries().get("frontend/*.md")
        self.assertIsNotNone(entry, "no exception for the frontend's records")
        self.assertEqual(set(entry.classes), {"tmp-path"})  # type: ignore[attr-defined]
        matched = [p for p in public_tree() if fnmatch.fnmatchcase(p, "frontend/*.md")]
        self.assertTrue(matched, "the glob matches nothing, so it exempts nothing")
        for path in matched:
            self.assertNotIn(
                "/", path[len("frontend/") :], f"{path} is deeper than one level"
            )

    def test_a_credential_class_is_not_exempt_in_any_record(self) -> None:
        """The deploy key is the class the operator asked to redact rather than allow."""
        planted = {
            path: "push with ~/.ssh/ticketpath_deploy_ed25519\n"
            for path in self.EXPECTED
        }
        repo = scratch(planted)
        self.addCleanup(repo.remove)
        result = RealChecker().check(repo.root, ("--tracked",), DENYLIST)
        self.assertEqual(result.classes, {"deploy-key"})
        self.assertEqual({hit[0] for hit in result.hits}, set(self.EXPECTED))


if __name__ == "__main__":
    unittest.main()

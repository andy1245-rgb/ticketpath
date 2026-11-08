"""The documentation consistency checker, proven to be able to fail.

A check that cannot fail is not a check, so every method here builds a small tree, makes
the *smallest* change that is a lie, and asserts the checker names it. The positive case
is the same fixture with nothing wrong: a checker that fails everything is as useless as
one that fails nothing, and the positive assertion is what keeps that honest.

The fixtures are written to a temporary directory, never to this repository, so these
tests still pass while a document in the real tree is mid-edit. The checker's own scope
here is one fixture root, and it reads no network and writes nothing.

Run: python3 -m unittest tests.test_doc_check -v
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools import doc_check

REPO_ROOT = Path(__file__).resolve().parents[1]

#: A memo id pair, and a devnet program id and mint, that are the *fixture's* truth. The
#: checker compares documents against the code and the artefact, never against a table in
#: this file, so any base58-shaped string would do here.
MEMO_DEVNET = "Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"
MEMO_MAINNET = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
PROGRAM_ID = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
STALE_PROGRAM_ID = "7ZZ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
#: The other program: the one that exists only on a local validator. It is in no constant
#: the checker reads and in no artefact, which is exactly why a rule that knows only the
#: artefact's id cannot see it.
V2_PROGRAM_ID = "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w"
MINT = "6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV"

#: The program source in miniature: the four tags, five errors and two seed literals the
#: real program has, written the way the real file writes them, because the parsers are
#: line-shaped and a fixture that is shaped differently would test nothing.
PROGRAM_SRC = '''
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum TicketpathError {
    /// The transfer was for more than one ticket.
    AmountNotOne = 6008,
    /// The price staged on the record is above the cap.
    CapExceeded = 6010,
    /// The record has not been staged for a transfer.
    TransferNotStaged = 6009,
    /// The record is not in a transferable state.
    TicketNotValid = 6013,
    /// The wrong account was passed in the extra-account-metas list.
    WrongExtraAccount = 6020,
}

impl From<TicketpathError> for ProgramError {
    fn from(e: TicketpathError) -> Self {
        ProgramError::Custom(e as u32)
    }
}

pub enum HookInstruction {
    InitializeExtraAccountMetaList { record: Pubkey },
    InitializeRecord { face: u64, cap_bps: u16 },
    SetPendingPrice { price: u64 },
    SetStatus { status: u8 },
}

impl HookInstruction {
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        let (tag, rest) = data.split_first().ok_or(ProgramError::InvalidInstructionData)?;
        match tag {
            0 => {
                let record = Pubkey::try_from(rest)?;
                Ok(Self::InitializeExtraAccountMetaList { record })
            }
            1 => {
                let face = u64::from_le_bytes(rest.try_into().unwrap());
                Ok(Self::InitializeRecord { face, cap_bps: 0 })
            }
            2 => {
                let price = u64::from_le_bytes(rest.try_into().unwrap());
                Ok(Self::SetPendingPrice { price })
            }
            3 => {
                let status = *rest.first().ok_or(ProgramError::InvalidInstructionData)?;
                Ok(Self::SetStatus { status })
            }
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
}

pub fn record_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"record", mint.as_ref()]
}

pub fn extra_metas_seeds(mint: &Pubkey) -> [&[u8]; 2] {
    [b"extra-account-metas", mint.as_ref()]
}
'''

CHAIN_CLIENT_SRC = f'''
"""docstring first, as the real file has"""
MEMO_PROGRAMS = {{
    "devnet": "{MEMO_DEVNET}",
    "mainnet-beta": "{MEMO_MAINNET}",
    "localnet": "{MEMO_MAINNET}",
}}
'''

#: The "implemented today" table, in the format `tools/doc_check.py`'s docstring defines.
#: Every row here is what PROGRAM_SRC implements: the positive case.
IMPLEMENTED_TODAY = """
## 14. Implemented today

| kind | name | value | where |
|---|---|---|---|
| error | AmountNotOne | 6008 | `execute` |
| error | CapExceeded | 6010 | `execute` |
| error | TransferNotStaged | 6009 | `execute` |
| error | TicketNotValid | 6013 | `execute` |
| error | WrongExtraAccount | 6020 | `execute` |
| instruction | InitializeExtraAccountMetaList | 0 | creates the metas PDA |
| instruction | InitializeRecord | 1 | creates the record |
| instruction | SetPendingPrice | 2 | stages a price |
| instruction | SetStatus | 3 | flips the flag |
| seed | record_seeds | record | per-mint record PDA |
| seed | extra_metas_seeds | extra-account-metas | the SPL interface's PDA |
"""

FEATURE_TABLE = """
## 0A. THE TEN-FEATURE BUILD -- per-feature status

| # | Feature | Status | Code path | Test file / note |
|---|---|---|---|---|
| 1 | Memo program id, per cluster | **tested** | `ticketpath/adapters/chain_client.py` | `tests/test_doc_check.py` (one test, OK) |
| 2 | Console renders the artefact as recorded | **not built** | none claimed | nothing claimed |
"""


def build_tree(root: Path, **overrides: str | None) -> Path:
    """A small tree that must pass every check, with named files overridable.

    `overrides` replaces the content of one named file, which is how each negative case
    changes exactly one thing. A value of None removes the file.
    """
    files = {
        "README.md": (
            "# Fixture\n\n"
            "The memo program id is a property of the cluster: devnet uses "
            f"`{MEMO_DEVNET}` and mainnet-beta uses `{MEMO_MAINNET}`.\n\n"
            f"The program is deployed on devnet at `{PROGRAM_ID}`, with a Token-2022 mint at "
            f"`{MINT}`.\n\n"
            "Run `python3 tools/tp.py doc-check` from the repository root.\n"
        ),
        "docs/ON-CHAIN-DESIGN.md": "# Design\n\nSee `tools/doc_check.py`.\n" + IMPLEMENTED_TODAY,
        "docs/DOC-CHECK.md": "# Doc check\n\nSee `tools/doc_check.py`.\n",
        "records/STATE-OF-PROJECT.md": "# State\n" + FEATURE_TABLE,
        "records/F-decision-log.md": (
            "# Decisions\n\n## D1 -- one decision\n\nNo. D2 is not named here.\n\n"
            "## D2 -- another\n\nBody.\n\n## Q1 -- a question (open)\n\nBody.\n"
        ),
        "records/findings/28-devnet-resume-and-retry.md": "# 28\n\nResume.\n",
        "records/C-variable-registry.md": (
            "# C\n\n## 1. Group 1\n\n### V1 `time_to_event` -- priority 1\n\nBody.\n\n"
            "### V2 `sell_through` -- priority 1\n\nBody.\n"
        ),
        "records/D-model-registry.md": (
            "# D\n\n## 2. Index\n\n| # | Model | Verdict |\n|---|---|---|\n"
            "| M01 | Face value | REJECTED |\n| M02 | Fixed markup | REJECTED |\n"
        ),
        "records/E-data-source-registry.md": (
            "# E\n\n## Index -- one row per source\n\n| # | Source |\n|---|---|\n"
            "| S1 | Ticketmaster |\n| S2 | SeatGeek |\n\nCount: **2 sources registered.**\n"
        ),
        "records/devnet-artefacts.json": json.dumps(
            {"programId": PROGRAM_ID, "mint": MINT, "cluster": "devnet"}, indent=2
        ),
        "ticketpath/adapters/chain_client.py": CHAIN_CLIENT_SRC,
        "programs/cap_hook/src/lib.rs": PROGRAM_SRC,
        "tests/test_doc_check.py": "# the fixture's own test file\n",
        "tools/doc_check.py": "# the checker, named by a document\n",
    }
    for name, content in overrides.items():
        key = name.replace("__", "/")
        if content is None:
            files.pop(key, None)
        else:
            files[key] = content
    for name, content in files.items():
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return root


class CheckerTestCase(unittest.TestCase):
    """A fixture tree per test, and the helpers for asking the checker about it."""

    def setUp(self) -> None:
        holder = tempfile.TemporaryDirectory(prefix="doc-check-")
        self.addCleanup(holder.cleanup)
        self.root = Path(holder.name)

    def run_check(self, *checks: str, **overrides: str | None) -> list[doc_check.Violation]:
        build_tree(self.root, **overrides)
        return doc_check.check_tree(self.root, checks or doc_check.CHECKS)

    def assertOnly(self, violations, check: str, needle: str) -> None:
        """Exactly one violation, of this check, whose text names the claim."""
        self.assertEqual(len(violations), 1, [item.render() for item in violations])
        found = violations[0]
        self.assertEqual(found.check, check, found.render())
        self.assertIn(needle, found.detail)


class CleanTreeTest(CheckerTestCase):
    """The positive case: a tree with nothing wrong passes every check.

    Without this, every negative case below could be passing for the wrong reason -- a
    checker that reports a violation on any input would satisfy all of them.
    """

    def test_a_clean_fixture_passes_every_check(self) -> None:
        violations = self.run_check()
        self.assertEqual(violations, [], [item.render() for item in violations])

    def test_every_check_runs_and_reports_itself_clean(self) -> None:
        build_tree(self.root)
        for check in doc_check.CHECKS:
            with self.subTest(check=check):
                self.assertEqual(doc_check.check_tree(self.root, (check,)), [])

    def test_the_missing_tables_are_the_violation_on_a_tree_without_them(self) -> None:
        # The absence of a table is stated, not crashed on: one clear message each.
        design = "# Design\n\nNo table here.\n"
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "no implemented-today table")

        state = "# State\n\nNo table here either.\n"
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "feature-table", "no feature table")


class PathsTest(CheckerTestCase):
    """Check 1: a named repo path exists."""

    def test_a_stale_path_is_caught_with_its_line(self) -> None:
        readme = "# Fixture\n\nGeneralise with `tools/doc_check.py` and `tools/missing_tool.py`.\n"
        violations = self.run_check("paths", **{"README.md": readme})
        self.assertOnly(violations, "paths", "tools/missing_tool.py")
        self.assertEqual(violations[0].path, "README.md")
        self.assertEqual(violations[0].line, 3)

    def test_a_link_target_is_checked_like_inline_code(self) -> None:
        readme = "# Fixture\n\nSee [the map](docs/GONE.md) for details.\n"
        violations = self.run_check("paths", **{"README.md": readme})
        self.assertOnly(violations, "paths", "docs/GONE.md")

    def test_a_link_anchor_is_not_part_of_the_path(self) -> None:
        readme = "# Fixture\n\nSee [the gate](docs/DOC-CHECK.md#how-to-add-a-check).\n"
        self.assertEqual(self.run_check("paths", **{"README.md": readme}), [])

    def test_a_glob_a_placeholder_and_a_url_are_not_claims_about_this_tree(self) -> None:
        readme = (
            "# Fixture\n\n"
            "`tools/*.py`, `docs/<name>.md`, `https://example.invalid/docs/CLI.md`, "
            "`../ticketing-frontend/lib/types.ts`, `records/findings/28`.\n"
        )
        self.assertEqual(self.run_check("paths", **{"README.md": readme}), [])

    def test_a_line_that_says_the_thing_is_absent_is_not_a_stale_claim(self) -> None:
        readme = "# Fixture\n\nThe plan named `tools/never_written.py`; checked today: does not exist.\n"
        self.assertEqual(self.run_check("paths", **{"README.md": readme}), [])


class AllowanceTest(CheckerTestCase):
    """Check 1's stated allowances: a path whose absence is written down and argued.

    The point of the table is that the twenty-one absent paths the record names are a red
    gate no longer, without becoming an invisible one: each is listed by path with a reason
    a reader can check, the run counts how many it suppressed, and nothing else is quieted.
    """

    def setUp(self) -> None:
        super().setUp()
        self.original = doc_check.ALLOWED_ABSENCES
        self.addCleanup(setattr, doc_check, "ALLOWED_ABSENCES", self.original)

    def allow(self, *entries: tuple[str, str]) -> None:
        doc_check.ALLOWED_ABSENCES = entries

    def test_an_allowed_absence_passes_and_is_counted(self) -> None:
        self.allow(("tools/devnet_check.py", "the planning name; it shipped as tools/devnet_publish.py"))
        readme = "# Fixture\n\nThe publisher was `tools/devnet_check.py` when this was planned.\n"
        notes: dict = {}
        build_tree(self.root, **{"README.md": readme})
        violations = doc_check.check_tree(self.root, ("paths",), notes)
        self.assertEqual([item.render() for item in violations], [])
        self.assertEqual(len(notes["allowed"]), 1, "the suppression is counted, not silent")
        self.assertEqual(notes["allowed"][0].path, "tools/devnet_check.py")

    def test_an_allow_entry_with_no_reason_is_itself_a_violation(self) -> None:
        self.allow(("tools/devnet_check.py", ""))
        readme = "# Fixture\n\nThe publisher was `tools/devnet_check.py` when this was planned.\n"
        violations = self.run_check("paths", **{"README.md": readme})
        # Two violations, and both are the point: the entry is refused, and it does not
        # suppress anything either, so the path is still reported as absent.
        rendered = " ".join(item.render() for item in violations)
        self.assertIn("tools/doc_check.py", rendered)
        self.assertIn("has no reason", rendered)
        self.assertIn("paths: tools/devnet_check.py does not exist", rendered)
        self.assertEqual(len(violations), 2, rendered)

    def test_an_allow_reason_too_thin_to_check_is_a_violation(self) -> None:
        self.allow(("tools/devnet_check.py", "renamed"))
        readme = "# Fixture\n\nThe publisher was `tools/devnet_check.py` when this was planned.\n"
        violations = self.run_check("paths", **{"README.md": readme})
        rendered = " ".join(item.render() for item in violations)
        self.assertIn("too thin to check", rendered)
        self.assertIn("paths: tools/devnet_check.py does not exist", rendered, "a thin reason does not suppress")

    def test_an_absent_path_that_is_not_in_the_table_still_fails(self) -> None:
        self.allow(("tools/devnet_check.py", "the planning name; it shipped as tools/devnet_publish.py"))
        readme = (
            "# Fixture\n\nBoth `tools/devnet_check.py` and `tools/never_planned.py` were named.\n"
        )
        violations = self.run_check("paths", **{"README.md": readme})
        self.assertOnly(violations, "paths", "tools/never_planned.py")

    def test_an_allowance_does_not_quiet_a_stale_id_or_a_count(self) -> None:
        # The entry is per path and per class: an entry for a path must not turn the ids
        # check off for the document that names it.
        self.allow(("README.md", "a file this fixture does have, entered here to prove the point"))
        readme = f"# Fixture\n\nThe program id on devnet is `{PROGRAM_ID}` and `README.md` is here.\n"
        stale = json.dumps({"programId": STALE_PROGRAM_ID, "mint": MINT, "cluster": "devnet"})
        violations = self.run_check(
            "ids", **{"README.md": readme, "records/devnet-artefacts.json": stale}
        )
        self.assertOnly(violations, "ids", PROGRAM_ID)

    def test_the_table_in_the_real_tree_has_a_checkable_reason_for_every_path(self) -> None:
        entries = doc_check.allowances(REPO_ROOT)
        self.assertTrue(entries, "the table is empty, so ten planning names are red again")
        paths = [entry.path for entry in entries]
        self.assertEqual(len(paths), len(set(paths)), "one entry per path, not two")
        for entry in entries:
            with self.subTest(path=entry.path):
                self.assertTrue(entry.checkable, entry.reason)
                self.assertGreater(entry.line, 0, "the entry's line was not found in the module")
                self.assertTrue(
                    "does not exist" in entry.reason or "never" in entry.reason
                    or "kept out" in entry.reason or "git-ignored" in entry.reason
                    or "gitignore" in entry.reason or "shipped as" in entry.reason
                    or "band" in entry.reason or "covered in" in entry.reason,
                    f"the reason reads as a claim: {entry.reason}",
                )

    def test_the_command_line_reports_the_count_and_names_them_under_verbose(self) -> None:
        # Driven against a fixture rather than this tree: the count and the naming are what
        # is under test, and this repository's own documents are being edited by other
        # passes, so an assertion about them would fail for a reason that is not this code.
        self.allow(("tools/devnet_check.py", "the planning name; it shipped as tools/devnet_publish.py"))
        readme = "# Fixture\n\nThe publisher was `tools/devnet_check.py` when this was planned.\n"
        build_tree(self.root, **{"README.md": readme})
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = doc_check.main(["--root", str(self.root), "--check", "paths"])
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertIn("1 allowed absence(s) suppressed by ALLOWED_ABSENCES", stderr.getvalue())

        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            doc_check.main(["--root", str(self.root), "--check", "paths", "--verbose"])
        self.assertIn("allowed: tools/devnet_check.py:", stderr.getvalue())
        self.assertIn("tools/devnet_publish.py", stderr.getvalue(), "the reason travels with it")

    def test_the_real_trees_run_says_how_many_absences_it_allowed(self) -> None:
        # About this tree, but not about whether it is clean: the number and the phrase are
        # the contract, and the violations are the doc steward's to remove.
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            doc_check.main(["--root", str(REPO_ROOT), "--check", "paths"])
        self.assertIn("allowed absence(s) suppressed by ALLOWED_ABSENCES", stderr.getvalue())
        notes: dict = {}
        doc_check.check_tree(REPO_ROOT, ("paths",), notes)
        self.assertTrue(notes["allowed"], "the table suppressed nothing, so it is doing no work")


class FindingsUniqueTest(CheckerTestCase):
    """Check 7: an ambiguous reference fails, a shared number warns.

    The defect is a reference with a wrong answer, not a number used twice. `00` and `02`
    pre-date the 33/34 collision, were written by one hand under the convention in use at
    the time, and a check that can only go green by renaming the operator's record would do
    more damage than the defect it catches. So the number shape is reported on every run and
    the run stays green; the reference is what fails.
    """

    def findings(self, *names: str, directories: tuple[str, ...] = ()) -> None:
        """Put this many findings under records/findings/, files by name, dirs by entry."""
        for name in names:
            build_tree(self.root, **{f"records/findings/{name}": f"# {name}\n"})
        for name in directories:
            # a directory is a claimant too: one file inside it is enough to create it
            build_tree(self.root, **{f"records/findings/{name}/NOTES.md": f"# {name}\n"})

    def shared(self, *checks: str) -> tuple[list, list]:
        notes: dict = {}
        violations = doc_check.check_tree(self.root, checks or doc_check.CHECKS, notes)
        return violations, notes.get("findings_shared", [])

    def test_a_number_with_several_claimants_warns_and_stays_green(self) -> None:
        self.findings("33-memo-id.md", "33-alpha.md")
        violations, warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])
        self.assertEqual(len(warnings), 1, warnings)
        self.assertIn("number 33 has 2 claimants", warnings[0])
        self.assertIn("33-memo-id.md", warnings[0])
        self.assertIn("33-alpha.md", warnings[0])

    def test_the_warning_reaches_the_command_line_on_every_run(self) -> None:
        self.findings("33-memo-id.md", "33-alpha.md")
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            code = doc_check.main(["--root", str(self.root), "--check", "findings-unique"])
        self.assertEqual(code, 0, stderr.getvalue())
        self.assertIn("doc_check: warning: records/findings number 33 has 2 claimants", stderr.getvalue())

    def test_four_files_under_one_number_with_distinct_letters_pass_and_warn(self) -> None:
        self.findings(
            "01-a-market-structure.md",
            "01-b-identifiability.md",
            "01-c-methods.md",
            "01-d-external.md",
        )
        violations, warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])
        self.assertEqual(len(warnings), 1)
        self.assertIn("the convention working", warnings[0])

    def test_a_single_file_at_a_number_passes_silently(self) -> None:
        self.findings("28-devnet-resume-and-retry.md")
        violations, warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])
        self.assertEqual(warnings, [])

    def test_a_bare_reference_to_a_shared_number_fails_and_names_both_sides(self) -> None:
        self.findings(
            "33-memo-id.md",
            "33-alpha.md",
            directories=("33-beta",),
        )
        state = "# State\n\nThe measured id is quoted in `records/findings/33` section 2.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, warnings = self.shared("findings-unique")
        self.assertEqual(len(violations), 1, [item.render() for item in violations])
        self.assertEqual(violations[0].path, "records/STATE-OF-PROJECT.md")
        self.assertEqual(violations[0].line, 3)
        self.assertIn("references 33", violations[0].detail)
        self.assertIn("33-memo-id.md", violations[0].detail)
        self.assertIn("33-alpha.md", violations[0].detail)
        self.assertIn("33-beta", violations[0].detail)

    def test_a_bare_reference_to_a_single_claimant_passes(self) -> None:
        self.findings("28-devnet-resume-and-retry.md")
        state = "# State\n\nThe resume pass is `records/findings/28`.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, _warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])

    def test_a_reference_to_a_file_by_name_is_never_ambiguous(self) -> None:
        self.findings("33-memo-id.md", "33-alpha.md")
        state = "# State\n\nThe id is in `records/findings/33-memo-id.md`.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, _warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])

    def test_the_same_letter_twice_fails_through_a_reference(self) -> None:
        # Kept because `34-a` is genuinely ambiguous: two files answer to it, so a reference
        # written `records/findings/34-a` lands in whichever sorts first. The pair alone is
        # a warning; the reference is the violation.
        self.findings("34-a-build.md", "34-a-review.md")
        state = "# State\n\nThe review is `records/findings/34-a`.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, warnings = self.shared("findings-unique")
        self.assertEqual(len(violations), 1, [item.render() for item in violations])
        self.assertIn("references 34-a", violations[0].detail)
        self.assertIn("34-a-build.md", violations[0].detail)
        self.assertIn("34-a-review.md", violations[0].detail)
        self.assertTrue(warnings, "the shared number is still reported")

    def test_the_same_letter_twice_without_a_reference_only_warns(self) -> None:
        self.findings("34-a-build.md", "34-a-review.md")
        violations, warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])
        self.assertIn("number 34 has 2 claimants", warnings[0])

    def test_a_directory_and_a_file_at_one_number_warn_and_do_not_fail(self) -> None:
        # The 33 collision itself: a session's working directory and a file under one number.
        self.findings("33-alpha.md", directories=("33-beta",))
        violations, warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])
        self.assertIn("33-beta", warnings[0])

    def test_a_word_starting_with_a_letter_is_not_a_group_suffix(self) -> None:
        # `02-ai-ml-decision.md` is a word, not the letter `a`, so a reference to `02` has
        # no single file to land in and the number is shared.
        self.findings("02-ai-ml-decision.md", "02-rubric-and-scoring.md")
        state = "# State\n\nSee `records/findings/02`.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, _warnings = self.shared("findings-unique")
        self.assertEqual(len(violations), 1, [item.render() for item in violations])

    def test_a_line_saying_the_number_does_not_exist_is_not_a_reference(self) -> None:
        self.findings("33-memo-id.md", "33-alpha.md")
        state = "# State\n\n`records/findings/33-unwritten.md` does not exist.\n"
        build_tree(self.root, **{"records/STATE-OF-PROJECT.md": state})
        violations, _warnings = self.shared("findings-unique")
        self.assertEqual([item.render() for item in violations], [])

    def test_the_real_findings_directory_is_grouped_not_crashed_on(self) -> None:
        # About this tree, and not an assertion that it is clean: it carries the warnings
        # this check exists to print, and every one of them names real files.
        groups = doc_check.finding_claimants(REPO_ROOT)
        self.assertTrue(groups, "no findings were read at all")
        shared = {number: names for number, names in groups.items() if len(names) > 1}
        self.assertTrue(shared, "the fixture is not the tree: no shared number was found")
        for number, names in shared.items():
            with self.subTest(number=number):
                self.assertTrue(all(name.startswith(number) for name in names), names)


class CrossReferencesTest(CheckerTestCase):
    """Check 2: findings, sections and decisions all resolve."""

    def test_a_dangling_finding_reference_is_caught(self) -> None:
        state = "# State\n\nSee `records/findings/99-nothing.md` for the answer.\n"
        violations = self.run_check("cross-references", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "cross-references", "99-nothing.md")

    def test_a_bare_finding_number_needs_any_file_with_that_number(self) -> None:
        state = "# State\n\n`records/findings/28` is the resume pass.\n"
        self.assertEqual(
            self.run_check("cross-references", **{"records/STATE-OF-PROJECT.md": state}), []
        )
        state = "# State\n\n`records/findings/99` is not a pass.\n"
        violations = self.run_check("cross-references", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "cross-references", "records/findings/99-*")

    def test_a_finding_reference_wrapped_at_a_hyphen_still_resolves(self) -> None:
        state = "# State\n\nSee `records/findings/28-devnet-resume-and-\nretry.md`.\n"
        self.assertEqual(
            self.run_check("cross-references", **{"records/STATE-OF-PROJECT.md": state}), []
        )

    def test_a_finding_directory_resolves_as_a_reference(self) -> None:
        """A number can also be a directory, and naming it is a reference to what is inside.

        `33-b-region-cap-law-sources/` is the sources of the finding beside it. Before this
        could resolve, the checker appended `.md` to every findings reference and reported
        the directory as `...-sources.md does not exist`, which is a true sentence being
        called false: the one failure mode this check must not have.
        """
        build_tree(
            self.root,
            **{
                "records/findings/33-b-sources/NOTES.md": "# notes\n",
                "records/STATE-OF-PROJECT.md": (
                    "# State\n\nThe five records are in `records/findings/33-b-sources/`.\n"
                ),
            },
        )
        violations = doc_check.check_tree(self.root, ("cross-references",))
        self.assertEqual([item.render() for item in violations], [])

    def test_a_section_reference_must_be_a_heading_in_the_same_file(self) -> None:
        design = (
            "# Design\n\n## 3. Instructions\n\n### 3.9 `execute`\n\nBody.\n\n"
            "## 4. Threat model\n\n### 4.1 What it stops\n\nBody.\n\n"
            "6. **The sixth thing.** §4.1 says so, and §4.7 does not exist.\n"
        )
        violations = self.run_check(
            "cross-references",
            **{"docs/ON-CHAIN-DESIGN.md": design, "README.md": "# Fixture\n"},
        )
        self.assertOnly(violations, "cross-references", "§4.7")

    def test_a_section_reference_to_a_numbered_list_item_resolves(self) -> None:
        design = (
            "# Design\n\n## 4. Threat model\n\n### 4.2 What it does not stop\n\n"
            "1. One.\n2. Two.\n\nBody: §4.2.2 is the second of those, and §4.2.9 is not.\n"
        )
        violations = self.run_check(
            "cross-references",
            **{"docs/ON-CHAIN-DESIGN.md": design, "README.md": "# Fixture\n"},
        )
        self.assertOnly(violations, "cross-references", "§4.2.9")

    def test_a_decision_reference_must_have_a_heading(self) -> None:
        state = "# State\n\nOf D1 and D7, `records/F-decision-log.md` records only the first.\n"
        violations = self.run_check("cross-references", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "cross-references", "D7")

    def test_an_open_question_number_from_another_registry_is_not_this_logs(self) -> None:
        # `03-b` Q6 is 03-b's question. A checker that insists every Q is a decision-log
        # heading would demand a heading for somebody else's numbering.
        registry = "# C\n\nSee `03-b` Q6 for the missing timestamp.\n"
        violations = self.run_check(
            "cross-references", **{"records/C-variable-registry.md": registry}
        )
        self.assertEqual(violations, [])


class IdsTest(CheckerTestCase):
    """Check 3: a quoted id is the id the code and the artefact carry."""

    def test_the_v2_program_id_paired_with_a_local_validator_passes(self) -> None:
        # There are two programs now: the devnet one, frozen, which is the evidence, and a
        # v2 that exists only on a local validator. A rule that knows only the artefact's
        # id would make this true sentence wrong, and the only way to satisfy it would be
        # to stop naming the v2 program.
        state = (
            "# State\n\n| Program | Note |\n|---|---|\n"
            f"| v2 | a different program id, `{V2_PROGRAM_ID}`, local validator only |\n"
        )
        violations = self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state})
        self.assertEqual([item.render() for item in violations], [])

    def test_the_v2_program_id_with_no_cluster_word_fails(self) -> None:
        state = f"# State\n\nThe program id is `{V2_PROGRAM_ID}` and it runs our hook.\n"
        violations = self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "ids", "no cluster named")

    def test_the_devnet_program_id_paired_with_a_local_validator_fails(self) -> None:
        # The devnet id belongs to devnet. A sentence that places it on a local validator
        # has the two programs swapped, which is the claim this check exists to stop.
        state = (
            "# State\n\nThis program runs on a local validator here, and nothing else: "
            f"`{PROGRAM_ID}` is local validator only.\n"
        )
        violations = self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "ids", PROGRAM_ID)
        self.assertIn("does not say devnet", violations[0].detail)

    def test_the_devnet_program_id_paired_with_devnet_passes(self) -> None:
        state = f"# State\n\nThe program is on devnet at `{PROGRAM_ID}`, executable.\n"
        self.assertEqual(self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state}), [])

    def test_the_artefact_id_in_a_wrapped_sentence_still_finds_its_cluster(self) -> None:
        # The reason the cluster is read from the sentence and not the physical line:
        # markdown here is hard-wrapped, so the cluster word and the id can sit a dozen
        # words apart across a line break, and calling that wrong relocates the very
        # false positive this rule removes.
        state = (
            "# State\n\n"
            f"The program is on devnet at `{PROGRAM_ID}`, with a\n"
            f"Token-2022 mint at `{MINT}` carrying the transfer hook.\n"
        )
        self.assertEqual(self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state}), [])

    def test_a_memo_id_the_table_does_not_carry_is_caught(self) -> None:
        readme = "# Fixture\n\nThe devnet memo program is `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`.\n"
        chain = f'MEMO_PROGRAM_ID = "{MEMO_MAINNET}"\n'
        violations = self.run_check(
            "ids", **{"README.md": readme, "ticketpath/adapters/chain_client.py": chain}
        )
        self.assertOnly(violations, "ids", MEMO_DEVNET)

    def test_the_per_cluster_table_passes_where_the_single_constant_fails(self) -> None:
        readme = f"# Fixture\n\ndevnet memo: `{MEMO_DEVNET}`\n"
        self.assertEqual(self.run_check("ids", **{"README.md": readme}), [])

    def test_a_stale_program_id_is_caught_against_the_artefact(self) -> None:
        readme = f"# Fixture\n\nThe program id on devnet is `{STALE_PROGRAM_ID}`.\n"
        violations = self.run_check("ids", **{"README.md": readme})
        self.assertOnly(violations, "ids", STALE_PROGRAM_ID)
        self.assertIn(PROGRAM_ID, violations[0].detail, "the message names the recorded id")

    def test_a_stale_mint_in_the_state_document_is_caught(self) -> None:
        state = (
            "# State\n\nA hooked Token-2022 mint exists at "
            "`8AAA73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`.\n"
        )
        violations = self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "ids", "8AAA73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV")

    def test_a_document_may_record_the_id_the_artefact_records(self) -> None:
        state = f"# State\n\nThe program id on devnet is `{PROGRAM_ID}` and the mint `{MINT}`.\n"
        self.assertEqual(self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state}), [])

    def test_a_document_may_say_it_did_not_re_read_the_id(self) -> None:
        state = f"# State\n\nThe devnet program id is `{PROGRAM_ID}`, recorded, not re-read.\n"
        self.assertEqual(self.run_check("ids", **{"records/STATE-OF-PROJECT.md": state}), [])

    def test_an_absent_artefact_is_a_violation_not_a_pass(self) -> None:
        readme = f"# Fixture\n\nThe program id on devnet is `{PROGRAM_ID}`.\n"
        violations = self.run_check("ids", **{"README.md": readme, "records/devnet-artefacts.json": None})
        self.assertOnly(violations, "ids", "records/devnet-artefacts.json")

    def test_an_artefact_that_records_no_id_is_a_violation_not_a_pass(self) -> None:
        readme = f"# Fixture\n\nThe program id on devnet is `{PROGRAM_ID}`.\n"
        empty = json.dumps({"cluster": "devnet"})
        violations = self.run_check(
            "ids", **{"README.md": readme, "records/devnet-artefacts.json": empty}
        )
        self.assertOnly(violations, "ids", "carries no programId")


class ProgramVsDocTest(CheckerTestCase):
    """Check 4: the three sets match the implemented-today table, both ways."""

    def test_an_error_in_the_code_and_not_in_the_table_is_caught(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY.replace(
            "| error | TransferNotStaged | 6009 | `execute` |\n", ""
        )
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "TransferNotStaged")

    def test_an_error_in_the_table_and_not_in_the_code_is_caught(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY + "| error | NotInTheCode | 6099 | nowhere |\n"
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "NotInTheCode")

    def test_a_renumbered_error_is_caught_both_ways(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY.replace("| 6010 |", "| 6011 |")
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        rendered = " ".join(item.detail for item in violations)
        self.assertIn("CapExceeded", rendered)
        self.assertEqual(len(violations), 1, rendered)

    def test_an_instruction_tag_the_table_does_not_carry_is_caught(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY.replace(
            "| instruction | SetStatus | 3 | flips the flag |\n", ""
        )
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "SetStatus")

    def test_a_seed_literal_that_drifted_is_caught(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY.replace(
            "| seed | record_seeds | record |", "| seed | record_seeds | records |"
        )
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "record_seeds")

    def test_a_kind_outside_the_three_is_caught(self) -> None:
        design = "# Design\n" + IMPLEMENTED_TODAY + "| account | TicketRecord | 0 | the record |\n"
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "account")

    def test_the_absence_of_the_table_is_one_message_and_not_a_crash(self) -> None:
        design = "# Design\n\n## 3. Instructions\n\nNothing tabulated.\n"
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "no implemented-today table")

    def test_a_table_with_the_wrong_header_is_named_as_such(self) -> None:
        design = (
            "# Design\n\n## 14. Implemented today\n\n"
            "| kind | name | number | where |\n|---|---|---|---|\n| error | CapExceeded | 6010 | x |\n"
        )
        violations = self.run_check("program-vs-doc", **{"docs/ON-CHAIN-DESIGN.md": design})
        self.assertOnly(violations, "program-vs-doc", "header")


class RegistryCountTest(CheckerTestCase):
    """Check 5: a stated count is the number of rows present.

    A record is append-only, so a correction keeps the old sentence and states the new count
    beside it. The check reads the current statement and leaves a dated old one alone: the
    alternative, which this check caused once, is a gate that can only pass if the history is
    deleted.
    """

    TWO_ROWS = (
        "# E\n\n## Index -- one row per source\n\n| # | Source |\n|---|---|\n"
        "| S1 | Ticketmaster |\n| S2 | SeatGeek |\n\n"
    )

    def test_an_old_count_in_a_dated_note_passes_when_the_current_one_matches(self) -> None:
        registry = self.TWO_ROWS + (
            "Count: **1 source registered** (superseded 2026-11-08: S2 was added; "
            "the count below is the current one).\n\n"
            "Count: **2 sources registered.**\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        self.assertEqual([item.render() for item in violations], [])

    def test_an_old_count_below_a_current_one_in_a_correction_note_passes(self) -> None:
        # The order the other registry uses: the current line first, the dated correction
        # under it quoting what the file used to say.
        registry = self.TWO_ROWS + (
            "Count: **2 sources registered.**\n\n"
            "**Corrected 2026-11-08.** The file previously said `Count: **1 source "
            "registered**`, and that line is left where it was written.\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        self.assertEqual([item.render() for item in violations], [])

    def test_the_current_count_disagreeing_with_the_rows_is_caught(self) -> None:
        registry = self.TWO_ROWS + (
            "Count: **1 source registered** (superseded 2026-11-08: S2 was added).\n\n"
            "Count: **3 sources registered.**\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        self.assertOnly(violations, "registry-counts", "states 3 rows; 2 are present")

    def test_two_competing_current_counts_are_caught(self) -> None:
        # Neither statement is marked as superseded, so the file does not say which number
        # it is claiming. That is a violation even when one of them matches the rows: an
        # ambiguous record is not a correct one.
        registry = self.TWO_ROWS + (
            "Count: **2 sources registered.**\n\n"
            "Count: **4 sources registered.**\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        details = " ".join(item.detail for item in violations)
        self.assertIn("two current counts", details)
        self.assertIn("states 2 rows", details, "the earlier statement is named")
        self.assertIn("states 4 rows", details, "the later statement is named")
        self.assertIn("states 4 rows; 2 are present", details, "and it is still counted")

    def test_a_file_whose_only_count_is_marked_historic_has_no_current_count(self) -> None:
        # The marker cannot be used to escape the check: a file that marks every count as
        # superseded is stating no current count at all.
        registry = self.TWO_ROWS + (
            "Count: **1 source registered** (superseded 2026-11-08: S2 was added).\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        self.assertOnly(violations, "registry-counts", "nothing states the current count")

    def test_a_count_that_disagrees_with_the_rows_is_caught(self) -> None:
        registry = (
            "# E\n\n## Index -- one row per source\n\n| # | Source |\n|---|---|\n"
            "| S1 | Ticketmaster |\n| S2 | SeatGeek |\n\nCount: **3 sources registered.**\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/E-data-source-registry.md": registry}
        )
        self.assertOnly(violations, "registry-counts", "states 3 rows; 2 are present")

    def test_a_count_that_agrees_passes(self) -> None:
        self.assertEqual(self.run_check("registry-counts"), [])

    def test_a_file_with_no_stated_count_is_not_a_violation(self) -> None:
        registry = "# D\n\n## 2. Index\n\n| # | Model |\n|---|---|\n| M01 | one |\n"
        self.assertEqual(
            self.run_check("registry-counts", **{"records/D-model-registry.md": registry}), []
        )

    def test_a_breakdown_that_does_not_sum_to_its_total_is_caught(self) -> None:
        registry = (
            "# C\n\n## 8. Seven revisions\n\n"
            "### 8.1 One block\n\n#### 8.1.1 `a`\n\n### 8.2 Another\n\n#### 8.2.1 `b`\n\n"
            "## 9. Counts\n\n**Added in revision 2:** **7 variable rows** (1 in §8.1, 2 in §8.2).\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/C-variable-registry.md": registry}
        )
        details = " ".join(item.detail for item in violations)
        self.assertIn("sums to 3", details)

    def test_a_stated_count_inside_a_section_counts_that_section(self) -> None:
        registry = (
            "# C\n\n## 8. Seven revisions\n\n"
            "### 8.1 One block\n\n#### 8.1.1 `a`\n\n#### 8.1.2 `b`\n\n"
            "Body: 5 ledger rows in §8.1, measured.\n"
        )
        violations = self.run_check(
            "registry-counts", **{"records/C-variable-registry.md": registry}
        )
        self.assertOnly(violations, "registry-counts", "5 ledger rows in §8.1")


class FeatureTableTest(CheckerTestCase):
    """Check 6: every feature row names a file that exists and a status from the set."""

    def test_a_tested_row_naming_a_test_that_does_not_exist_is_caught(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 1 | Memo id | **tested** | `ticketpath/adapters/chain_client.py` | "
            "`tests/test_nowhere.py` |\n"
        )
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        details = " ".join(item.detail for item in violations)
        self.assertIn("tests/test_nowhere.py", details)
        self.assertIn("does not exist", details)

    def test_a_tested_row_that_names_only_code_is_caught(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 1 | Memo id | **tested** | `ticketpath/adapters/chain_client.py` | measured by hand |\n"
        )
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "feature-table", "claims tested and names no existing tests/test_*.py")

    def test_a_tested_row_naming_a_root_test_file_passes(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 1 | Memo id | **tested** | `ticketpath/adapters/chain_client.py` | "
            "`tests/test_doc_check.py` (1 test, OK) |\n"
        )
        self.assertEqual(self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state}), [])

    def test_a_tested_row_naming_a_market_swarm_test_file_passes(self) -> None:
        # `market_swarm` is a self-contained package with its own suite, run with
        # `python3 -m unittest discover -s market_swarm/tests -t .`. A rule that knew only
        # the root `tests/` directory made a feature tested there impossible to mark
        # `tested`, so the document understated it as `built`.
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 9 | Live deepseek adapter | **tested** | `market_swarm/forge_policy.py` | "
            "`market_swarm/tests/test_forge_live.py` (89 tests, OK) |\n"
        )
        violations = self.run_check(
            "feature-table",
            **{
                "records/STATE-OF-PROJECT.md": state,
                "market_swarm/forge_policy.py": "# the adapter the row names\n",
                "market_swarm/tests/test_forge_live.py": "# the package's own suite\n",
            },
        )
        self.assertEqual([item.render() for item in violations], [])

    def test_a_market_swarm_test_file_that_does_not_exist_is_caught(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 9 | Live deepseek adapter | **tested** | `market_swarm/forge_policy.py` | "
            "`market_swarm/tests/test_nowhere.py` |\n"
        )
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        details = " ".join(item.detail for item in violations)
        self.assertIn("market_swarm/tests/test_nowhere.py", details)
        self.assertIn("does not exist", details)

    def test_a_status_outside_the_closed_set_is_caught(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path |\n|---|---|---|---|\n"
            "| 1 | Memo id | mostly done | `ticketpath/adapters/chain_client.py` |\n"
        )
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "feature-table", "mostly done")

    def test_a_not_built_row_may_honestly_name_nothing(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path | Test file / note |\n|---|---|---|---|---|\n"
            "| 7 | Flip tax | **not built** | none claimed | nothing claimed |\n"
        )
        self.assertEqual(
            self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state}), []
        )

    def test_a_built_row_naming_a_file_that_is_not_there_is_caught(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path |\n|---|---|---|---|\n"
            "| 2 | Console | **built** | `tools/not_written.py` |\n"
        )
        violations = self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state})
        self.assertOnly(violations, "feature-table", "tools/not_written.py")

    def test_the_three_word_status_is_one_status(self) -> None:
        state = (
            "# State\n\n## 0A. THE TEN-FEATURE BUILD\n\n"
            "| # | Feature | Status | Code path |\n|---|---|---|---|\n"
            "| 3 | Charts | not built | none claimed |\n"
        )
        self.assertEqual(
            self.run_check("feature-table", **{"records/STATE-OF-PROJECT.md": state}), []
        )


class ParserTest(CheckerTestCase):
    """The two parsers, on the shapes the real files use."""

    def test_the_memo_table_reads_both_shapes(self) -> None:
        single = f'MEMO_PROGRAM_ID = "{MEMO_MAINNET}"  # the CLI\'s memo program\n'
        self.assertEqual(doc_check.memo_table(single), {"MEMO_PROGRAM_ID": MEMO_MAINNET})
        table = doc_check.memo_table(CHAIN_CLIENT_SRC)
        self.assertEqual(table["MEMO_PROGRAMS[devnet]"], MEMO_DEVNET)
        self.assertEqual(table["MEMO_PROGRAMS[mainnet-beta]"], MEMO_MAINNET)
        self.assertEqual(set(table.values()), {MEMO_DEVNET, MEMO_MAINNET})

    def test_the_memo_table_resolves_a_mapping_whose_values_are_names(self) -> None:
        # The shape the real file has, and the one that made this checker report three
        # false violations: the mapping's values are constant names, not literals, so a
        # reader that took only string values found none and fell back to one constant.
        source = (
            f'MEMO_PROGRAM_DEVNET = "{MEMO_DEVNET}"\n'
            f'MEMO_PROGRAM_CLI = "{MEMO_MAINNET}"\n'
            'MEMO_PROGRAMS = {\n'
            '    "devnet": MEMO_PROGRAM_DEVNET,\n'
            '    "mainnet-beta": MEMO_PROGRAM_CLI,\n'
            '    "localnet": MEMO_PROGRAM_CLI,\n'
            '}\n'
        )
        table = doc_check.memo_table(source)
        self.assertEqual(set(table.values()), {MEMO_DEVNET, MEMO_MAINNET})
        self.assertEqual(table["MEMO_PROGRAM_DEVNET"], MEMO_DEVNET)
        self.assertEqual(table["MEMO_PROGRAMS[localnet]"], MEMO_MAINNET)

    def test_a_document_may_quote_either_id_the_file_carries(self) -> None:
        # Both ids are in MEMO_ constants, so both are true claims; before the fix only
        # the last constant was seen and the devnet quotes were reported as stale.
        readme = (
            f"# Fixture\n\nThe devnet memo program is `{MEMO_DEVNET}` and the CLI's is "
            f"`{MEMO_MAINNET}`.\n"
        )
        self.assertEqual(self.run_check("ids", **{"README.md": readme}), [])

    def test_a_memo_id_in_no_constant_is_still_caught(self) -> None:
        stranger = "Memo9" + "z" * 39  # 44 base58 characters: id-shaped, in no constant
        readme = f"# Fixture\n\nThe devnet memo program is `{stranger}`.\n"
        violations = self.run_check("ids", **{"README.md": readme})
        self.assertOnly(violations, "ids", stranger)
        self.assertIn(MEMO_DEVNET, violations[0].detail, "the message names what the file carries")

    def test_the_program_mapping_is_read_as_cluster_to_id(self) -> None:
        # The mapping is the half the set comparison could not see, and the reversal below is
        # what it exists for.
        self.assertEqual(
            doc_check.memo_programs(CHAIN_CLIENT_SRC),
            {"devnet": MEMO_DEVNET, "mainnet-beta": MEMO_MAINNET, "localnet": MEMO_MAINNET},
        )
        self.assertEqual(doc_check.memo_programs(f'MEMO_PROGRAM_ID = "{MEMO_MAINNET}"\n'), {})

    def test_two_ids_swapped_between_two_clusters_is_caught(self) -> None:
        """The bypass the reviewer constructed: every literal is real, the direction is wrong.

        Before this rule the `ids` check compared against the set of literals, so this README
        produced zero violations -- the exact error the feature exists to prevent, waved
        through by the gate. Deleting the direction check makes this test fail.
        """
        readme = (
            "# Fixture\n\nThe memo program id is a property of the cluster: devnet uses "
            f"`{MEMO_MAINNET}` and mainnet-beta uses `{MEMO_DEVNET}`.\n"
        )
        violations = self.run_check("ids", **{"README.md": readme})
        self.assertEqual(len(violations), 2, [item.render() for item in violations])
        details = " ".join(item.detail for item in violations)
        self.assertIn(f"attributes {MEMO_MAINNET} to devnet", details)
        self.assertIn(f"attributes {MEMO_DEVNET} to mainnet-beta", details)

    def test_one_swapped_id_inside_a_correct_sentence_is_caught(self) -> None:
        readme = f"# Fixture\n\nOnly the mainnet-beta memo program is `{MEMO_DEVNET}`.\n"
        violations = self.run_check("ids", **{"README.md": readme})
        self.assertOnly(violations, "ids", "mainnet-beta")
        self.assertIn(MEMO_MAINNET, violations[0].detail)

    def test_the_program_parser_reads_errors_tags_and_seeds(self) -> None:
        facts = doc_check.parse_program(PROGRAM_SRC)
        self.assertEqual(facts.errors["CapExceeded"], "6010")
        self.assertEqual(len(facts.errors), 5)
        self.assertEqual(facts.instructions["SetStatus"], "3")
        self.assertEqual(len(facts.instructions), 4)
        self.assertEqual(facts.seeds, {"record_seeds": "record", "extra_metas_seeds": "extra-account-metas"})

    def test_a_pipe_inside_a_cell_is_not_a_column_break(self) -> None:
        cells = doc_check.split_row("| a | `git ls-files \\| wc -l` | c |")
        self.assertEqual(cells, ["a", "`git ls-files | wc -l`", "c"])

    def test_a_one_line_match_arm_resolves_to_its_tag(self) -> None:
        # The bug the gate found: `0 => Ok(Self::Alpha),` sets the tag and closes on the
        # same line, so a reader that only looks at the lines *below* an arm loses it and
        # then reports a correct table row as a row the code does not have.
        source = """
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        match tag {
            0 => Ok(Self::Alpha),
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
"""
        self.assertEqual(doc_check.parse_program(source).instructions, {"Alpha": "0"})

    def test_a_multi_line_match_arm_still_resolves_to_its_tag(self) -> None:
        source = """
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        match tag {
            3 => {
                let status = *rest.first().ok_or(ProgramError::InvalidInstructionData)?;
                Ok(Self::Gamma {
                    status,
                })
            }
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
"""
        self.assertEqual(doc_check.parse_program(source).instructions, {"Gamma": "3"})

    def test_a_variant_in_a_comment_or_a_string_is_not_an_arm(self) -> None:
        # A comment or a message string inside the block is prose. Reading it as an arm
        # invents an instruction, which reads as a table row that is wrong about the code.
        source = """
    fn unpack(data: &[u8]) -> Result<Self, ProgramError> {
        match tag {
            1 => {
                // Ok(Self::Commented) is a sentence, not an arm.
                let message = "Ok(Self::Quoted) is a string";
                Ok(Self::Delta { message })
            }
            _ => Err(ProgramError::InvalidInstructionData),
        }
    }
"""
        instructions = doc_check.parse_program(source).instructions
        self.assertEqual(instructions, {"Delta": "1"})
        self.assertNotIn("Commented", instructions)
        self.assertNotIn("Quoted", instructions)

    def test_a_one_line_arm_does_not_make_the_table_row_a_violation(self) -> None:
        # End to end, at the level the gate saw it: the table is right and the code is
        # right, so there is nothing to report.
        design = "# Design\n" + IMPLEMENTED_TODAY
        one_line = PROGRAM_SRC.replace(
            """            0 => {
                let record = Pubkey::try_from(rest)?;
                Ok(Self::InitializeExtraAccountMetaList { record })
            }""",
            "            0 => Ok(Self::InitializeExtraAccountMetaList),",
        )
        self.assertIn("0 => Ok(Self::InitializeExtraAccountMetaList),", one_line)
        violations = self.run_check(
            "program-vs-doc",
            **{"docs/ON-CHAIN-DESIGN.md": design, "programs/cap_hook/src/lib.rs": one_line},
        )
        self.assertEqual([item.render() for item in violations], [])


class CommandLineTest(unittest.TestCase):
    """The exit codes the gate depends on: 0 clean, 1 violations, 2 unreadable."""

    def quietly(self, root: Path) -> int:
        """Run the command line with its output captured: a test is not a terminal."""
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return doc_check.main(["--root", str(root), "--quiet"])

    def test_exit_one_on_a_violation_and_zero_on_a_clean_tree(self) -> None:
        with tempfile.TemporaryDirectory(prefix="doc-check-cli-") as scratch:
            root = build_tree(Path(scratch))
            self.assertEqual(self.quietly(root), 0)
            (root / "README.md").write_text("# Fixture\n\n`tools/gone.py`\n", encoding="utf-8")
            self.assertEqual(self.quietly(root), 1)

    def test_exit_two_when_a_file_a_check_must_read_is_missing(self) -> None:
        with tempfile.TemporaryDirectory(prefix="doc-check-cli-") as scratch:
            root = build_tree(Path(scratch))
            (root / "programs/cap_hook/src/lib.rs").unlink()
            self.assertEqual(self.quietly(root), 2)

    def test_the_real_tree_runs_without_crashing(self) -> None:
        # Not an assertion that the tree is clean: it is not, until the documents catch
        # up, and this checker's job is to say so. The assertion is that a real tree of
        # 69 tracked documents and 2,000-line files is read without a traceback, in the
        # time a commit hook can afford.
        done = subprocess.run(
            [sys.executable, str(REPO_ROOT / "tools" / "doc_check.py")],
            capture_output=True, text=True, timeout=120, check=False,
        )
        self.assertIn(done.returncode, (0, 1), done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_the_verb_is_wired_and_the_gate_carries_its_position(self) -> None:
        from tools import tp

        self.assertIn("doc-check", tp.COMMANDS)
        parser = tp.build_parser()
        self.assertEqual(parser.parse_args(["doc-check"]).command, "doc-check")


class GateWiringTest(unittest.TestCase):
    """`gate --quick` runs the documentation check and fails on it, in both modes.

    Driven with stub commands for the other two positions, because what is under test is
    the wiring: that doc-check runs, that its count reaches the summary line, and that a
    violation refuses the gate rather than being printed and passed over.
    """

    PASSING_TESTS = [sys.executable, "-c", "print('Ran 9 tests in 0.1s'); print('OK')"]
    CLEAN_DOC = [sys.executable, "-c", "print('doc_check: clean')"]
    DIRTY_DOC = [
        sys.executable, "-c",
        "print('docs/X.md:3: paths: tools/gone.py does not exist'); raise SystemExit(1)",
    ]

    def gate(self, **kwargs) -> tuple[int, str]:
        from tools import tp

        with tempfile.TemporaryFile(mode="w+") as sink:
            code = tp.run_gate(**{"out": sink, **kwargs})
            sink.seek(0)
            return code, sink.read()

    def test_the_quick_gate_runs_doc_check_and_says_so(self) -> None:
        code, text = self.gate(
            quick=True, tests_command=self.PASSING_TESTS, doc_check_command=self.CLEAN_DOC
        )
        self.assertEqual(code, 0, text)
        self.assertIn("doc-check: 0 violation(s)", text)
        self.assertIn("doc-check=0 violation(s)", text)

    def test_a_violation_refuses_the_gate_and_prints_the_line(self) -> None:
        code, text = self.gate(
            quick=True, tests_command=self.PASSING_TESTS, doc_check_command=self.DIRTY_DOC
        )
        self.assertEqual(code, 1, text)
        self.assertIn("docs/X.md:3: paths: tools/gone.py does not exist", text)
        self.assertIn("gate FAILED", text)

    def test_a_checker_that_cannot_run_is_a_failure_not_a_pass(self) -> None:
        broken = [sys.executable, "-c", "import sys; sys.stderr.write('doc_check: boom'); raise SystemExit(2)"]
        code, text = self.gate(quick=True, tests_command=self.PASSING_TESTS, doc_check_command=broken)
        self.assertEqual(code, 1, text)
        self.assertIn("boom", text, "the checker's own words are printed, not trimmed")


class HookDocsOnlyTest(unittest.TestCase):
    """`.githooks/pre-commit`, driven by git itself, on a markdown-only commit.

    The hook used to run the gate only when a staged path was code, so the one commit that
    can break the documentation was the one that skipped the documentation check. This
    runs the real hook script, unmodified, in a throwaway repository whose tree is the
    fixture every other test in this module shares, and stages markdown: once with a path
    the tree does not have, and once clean. Both outcomes are asserted, because a branch
    that refuses everything is as useless as one that refuses nothing.
    """

    def make_repo(self) -> Path:
        root = Path(tempfile.mkdtemp(prefix="tp-hook-docs-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        build_tree(root)
        # The fixture names the checker; for this test the checker has to *be* there, and
        # so does the CLI the hook calls, and the public-safety rules the hook runs first.
        for name in ("tools/doc_check.py", "tools/tp.py", "tools/public_safety.py"):
            shutil.copy2(REPO_ROOT / name, root / name)
        shutil.copy2(REPO_ROOT / ".public-denylist", root / ".public-denylist")
        (root / ".githooks").mkdir(exist_ok=True)
        shutil.copy2(REPO_ROOT / ".githooks" / "pre-commit", root / ".githooks" / "pre-commit")
        (root / ".githooks" / "pre-commit").chmod(0o755)
        subprocess.run(["git", "init", "-q", "-b", "main", str(root)], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email", "t@example.invalid"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name", "t"], check=True)
        return root

    def run_hook(self, root: Path) -> subprocess.CompletedProcess:
        return subprocess.run(
            ["sh", ".githooks/pre-commit"], cwd=str(root), capture_output=True, text=True, timeout=120
        )

    def test_a_markdown_commit_that_breaks_a_check_is_refused(self) -> None:
        root = self.make_repo()
        broken = root / "docs" / "BROKEN.md"
        broken.write_text("# Broken\n\nThe tool is `tools/never_written.py`.\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "docs/BROKEN.md"], check=True)
        done = self.run_hook(root)
        output = done.stdout + done.stderr
        self.assertEqual(done.returncode, 1, output)
        self.assertIn("markdown staged (docs/BROKEN.md)", output)
        self.assertIn("running the documentation check", output)
        self.assertIn("tools/never_written.py does not exist", output, "the violation travels")
        self.assertIn("the documentation check failed", output)

    def test_a_clean_markdown_commit_passes_the_same_branch(self) -> None:
        root = self.make_repo()
        (root / "docs" / "FINE.md").write_text("# Fine\n\nThe tool is `tools/doc_check.py`.\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "docs/FINE.md"], check=True)
        done = self.run_hook(root)
        output = done.stdout + done.stderr
        self.assertEqual(done.returncode, 0, output)
        self.assertIn("markdown staged (docs/FINE.md)", output)
        self.assertIn("doc_check: clean", output)

    def test_a_code_commit_does_not_run_the_branch_twice(self) -> None:
        root = self.make_repo()
        staged = root / "tools" / "note.py"
        staged.write_text("# a code change\n", encoding="utf-8")
        subprocess.run(["git", "-C", str(root), "add", "tools/note.py"], check=True)
        done = self.run_hook(root)
        output = done.stdout + done.stderr
        # The gate owns the code path, and it runs doc-check inside itself; the hook must
        # not add a second run of the same check behind it.
        self.assertNotIn("markdown staged", output)


if __name__ == "__main__":
    unittest.main()

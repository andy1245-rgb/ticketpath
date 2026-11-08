"""The build provenance record, proven to be able to fail.

The record is only worth having if a stale one is caught, so every method here builds a
small repository, writes the record against it, then makes the *smallest* change that is a
lie -- a mutated source hash, an absent binary, a commit that no longer exists, a program id
the tree stopped stating -- and asserts the checker names it. The positive case is the same
fixture with nothing wrong: a checker that fails everything is as useless as one that fails
nothing, and the positive assertion is what keeps that honest.

The mutations are the ones a reviewer actually used against the committed artefact, so the
list is a record of attacks that worked: a program id changed in the code that states it, a
`program_id_source` deleted to switch the check off, rebuild hashes zeroed under a
`reproducible: true`, a toolchain line replaced with a fake, and a nested module and a
crate-root `build.rs` that the record never hashed. Each is repeated here so it cannot come
back without a failing test.

The fixtures are written to a temporary directory and committed to a git repository of
their own, never to this one, so these tests still pass while a source file in the real tree
is mid-edit. Two methods read the real artefact instead: one pins the measured figures the
README quotes, one runs `verify` against this tree when the git-ignored binaries have been
built. Nothing here touches a cluster, a network or a key.

Run: python3 -m unittest tests.test_build_provenance -v
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import time
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from tools import build_provenance

REPO_ROOT = Path(__file__).resolve().parents[1]

#: The measured v1 and v2 figures: v1 from `records/findings/18-onchain-install-and-test.md`,
#: v2 from the build that produced `records/onchain-v2.local.json`. Both are quoted in
#: `programs/cap_hook/README.md`, and a change to either means the source or the toolchain
#: moved and the record has to be regenerated rather than quietly left alone.
MEASURED = {
    "v1": (
        85784,
        "a0dcc48d95b8fc22e0c5b60f296e6ec487a747f4d3c74b0e277658978b43e94d",
    ),
    "v2": (
        111504,
        "de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac",
    ),
}

FIXTURE_CARGO = """[package]
name = "cap-hook"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib", "lib"]
name = "cap_hook"
"""

FIXTURE_V1 = "//! the first version, one file\npub fn execute() {}\n"
FIXTURE_V2 = "//! the second version\nmod state;\npub fn execute() {}\n"
FIXTURE_STATE = "//! the second version's state\npub const LEN: usize = 8;\n"

#: The code that states v2's id, in the shape the real one has: a module-level dict whose
#: values are string literals. The `raise` at the bottom is deliberate -- a reader that
#: imports this file to learn a constant dies, so the tests only pass if the tool parses it.
FIXTURE_GATEWAY = '''"""the fixture's gateway: which address each program is at."""

PROGRAM_IDS = {
    "v1": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva",
    "v2": "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w",
}

raise SystemExit("importing this to read PROGRAM_IDS is what these tests forbid")
'''

#: The toolchain block the fixture records. The real version lines, so a test that mutates one
#: is mutating something that could plausibly have been written by the tool.
FIXTURE_TOOLCHAIN = {
    "cargo_build_sbf": "cargo-build-sbf 4.4.0",
    "platform_tools": "platform-tools v1.57",
    "rustc": "rustc 1.95.0",
    "solana_cli": "solana-cli 4.3.2 (src:0f131d36; feat:c9ad34d2, client:Agave)",
}


def run(argv: list[str]) -> tuple[int, str]:
    """Run the tool in-process and return its exit code and everything it printed.

    stdout and stderr are one stream here on purpose: a refusal is part of the answer, and
    the tests assert on what the operator would see in a terminal.
    """
    out = io.StringIO()
    err = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = build_provenance.main(argv)
    return code, out.getvalue() + err.getvalue()


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()


class Fixture:
    """A tiny repository with two versions of one crate, and a binary for each.

    Not a copy of this tree: the point is that the tool reads git and the disk and does not
    know what this project is. Whatever the fixture says is what the record must say.
    """

    def __init__(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="build-provenance-"))
        crate = self.root / "programs" / "cap_hook"
        (crate / "src").mkdir(parents=True)
        (crate / "Cargo.toml").write_text(FIXTURE_CARGO, encoding="utf-8")
        (crate / "src" / "lib.rs").write_text(FIXTURE_V1, encoding="utf-8")
        (self.root / "records").mkdir()
        (self.root / "records" / "devnet-artefacts.json").write_text(
            json.dumps({"programId": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"}),
            encoding="utf-8",
        )
        (self.root / "market_swarm").mkdir()
        (self.root / "market_swarm" / "gateway.py").write_text(
            FIXTURE_GATEWAY, encoding="utf-8"
        )
        (crate / "target" / "deploy").mkdir(parents=True)
        (crate / "target" / "deploy" / "cap_hook-v1.so").write_bytes(b"v1 bytes\n")
        (crate / "target" / "deploy" / "cap_hook.so").write_bytes(b"v2 bytes\n")

        git(self.root, "init", "-q", "-b", "main")
        git(self.root, "config", "user.email", "t@example.invalid")
        git(self.root, "config", "user.name", "t")
        self.commit_all("v1")
        self.v1_commit = git(self.root, "rev-parse", "HEAD")

        # v2 replaces lib.rs and adds a second source file, which is what makes the two
        # versions distinguishable by more than their label.
        (crate / "src" / "lib.rs").write_text(FIXTURE_V2, encoding="utf-8")
        (crate / "src" / "state.rs").write_text(FIXTURE_STATE, encoding="utf-8")
        self.commit_all("v2")
        self.v2_commit = git(self.root, "rev-parse", "HEAD")

        self.artefact = self.root / "programs" / "cap_hook" / "BUILD-PROVENANCE.json"

    def commit_all(self, message: str) -> None:
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", message)

    def write(self, *extra: str) -> tuple[int, str]:
        # The toolchain is not this fixture's business: the record's toolchain block is
        # pinned separately, and a machine without the Solana toolchain still has to be
        # able to run these tests.
        with mock.patch.object(
            build_provenance, "toolchain_versions", return_value=dict(FIXTURE_TOOLCHAIN)
        ):
            return run(["write", "--root", str(self.root), *extra])

    def verify(self) -> tuple[int, str]:
        """Verify with the fixture's toolchain standing in for the installed one."""
        with mock.patch.object(
            build_provenance, "toolchain_versions", return_value=dict(FIXTURE_TOOLCHAIN)
        ), mock.patch.object(build_provenance, "toolchain_on_path", return_value=True):
            return run(["verify", "--root", str(self.root)])

    def verify_without_toolchain(self) -> tuple[int, str]:
        """Verify on a machine where the Solana toolchain is not installed."""
        with mock.patch.object(
            build_provenance, "toolchain_on_path", return_value=False
        ), mock.patch.object(
            build_provenance,
            "toolchain_versions",
            side_effect=AssertionError("verify must not run a toolchain it said was absent"),
        ):
            return run(["verify", "--root", str(self.root)])

    def document(self) -> dict:
        return json.loads(self.artefact.read_text(encoding="utf-8"))

    def save(self, document: dict) -> None:
        self.artefact.write_text(json.dumps(document, indent=2), encoding="utf-8")

    def entry(self, version: str) -> dict:
        for entry in self.document()["programs"]:
            if entry["version"] == version:
                return entry
        raise AssertionError(f"no {version} entry in the record")

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)


class ProvenanceCase(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = Fixture()
        self.addCleanup(self.fixture.cleanup)


class TestWrite(ProvenanceCase):
    def test_records_each_version_from_git_and_from_disk(self) -> None:
        code, out = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_OK, out)

        document = self.fixture.document()
        self.assertEqual(document["schema"], build_provenance.SCHEMA)
        self.assertEqual(
            document["verify_with"],
            "python3 tools/build_provenance.py verify",
        )
        self.assertEqual([p["version"] for p in document["programs"]], ["v1", "v2"])

        v1 = self.fixture.entry("v1")
        v2 = self.fixture.entry("v2")

        # The commit is resolved by git, never typed: v1 is the commit that added lib.rs,
        # v2 is HEAD.
        self.assertEqual(v1["source_commit"], self.fixture.v1_commit)
        self.assertEqual(v2["source_commit"], self.fixture.v2_commit)
        self.assertEqual(v1["source_commit_short"], self.fixture.v1_commit[:7])
        self.assertEqual(v1["source_scope"], "commit")
        self.assertEqual(v2["source_scope"], "tree")

        # A superseded version's file set is the one that commit had: no state.rs.
        self.assertEqual(
            sorted(v1["source_files"]),
            ["programs/cap_hook/Cargo.toml", "programs/cap_hook/src/lib.rs"],
        )
        self.assertEqual(
            sorted(v2["source_files"]),
            [
                "programs/cap_hook/Cargo.toml",
                "programs/cap_hook/src/lib.rs",
                "programs/cap_hook/src/state.rs",
            ],
        )

        # The program's name comes from the [lib] table, not the [package] one.
        self.assertEqual(v1["program"], "cap_hook")

        # The binary's size and hash are measured, not copied from anywhere.
        self.assertEqual(v1["binary"]["bytes"], len(b"v1 bytes\n"))
        self.assertEqual(v2["binary"]["bytes"], len(b"v2 bytes\n"))
        self.assertEqual(v2["binary"]["path"], "programs/cap_hook/target/deploy/cap_hook.so")

        # The id is the one the tree states, and the record says where it read it. v1's is in
        # the devnet record; v2's is in the code that decides which address a run uses, and
        # recording it as null -- as the record did before it was fixed -- left v2's identity
        # unchecked by the one tool that exists to check it.
        self.assertEqual(
            v1["program_id"], "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
        )
        self.assertEqual(
            v1["program_id_source"], "records/devnet-artefacts.json#programId"
        )
        self.assertEqual(
            v2["program_id"], "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w"
        )
        self.assertEqual(
            v2["program_id_source"], 'market_swarm/gateway.py#PROGRAM_IDS["v2"]'
        )

        # ISO-8601 UTC, second resolution, Z suffix.
        self.assertRegex(document["generated_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        datetime.strptime(document["generated_at"], "%Y-%m-%dT%H:%M:%SZ")

    def test_records_a_supplied_rebuild_and_whether_it_matched(self) -> None:
        same = self.fixture.root / "same.so"
        same.write_bytes(b"v2 bytes\n")

        code, out = self.fixture.write("--rebuild", f"v2={same}")
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        rebuild = self.fixture.entry("v2")["rebuilds"]
        self.assertEqual(len(rebuild), 1)
        self.assertTrue(rebuild[0]["identical"])
        self.assertTrue(self.fixture.entry("v2")["reproducible"])

    def test_refuses_to_record_a_rebuild_that_did_not_reproduce(self) -> None:
        # A record is written to be verified, and verify fails a rebuild whose hash is not
        # the binary's. Writing one anyway would hand the reader a file its own gate rejects,
        # so the refusal is here, with both hashes in the sentence.
        different = self.fixture.root / "different.so"
        different.write_bytes(b"other bytes\n")

        code, out = self.fixture.write("--rebuild", f"v2={different}")
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE, out)
        self.assertIn("did not reproduce", out)
        self.assertFalse(self.fixture.artefact.exists())

    def test_a_rebuild_for_an_unknown_version_is_refused(self) -> None:
        code, _ = self.fixture.write("--rebuild", "v9=/nonexistent.so")
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)

    def test_refuses_to_record_a_tree_that_differs_from_the_commit(self) -> None:
        # The lie this prevents: a hash of a working-tree file recorded against a commit
        # that never held those bytes. The record names the commit *and* the content.
        crate = self.fixture.root / "programs" / "cap_hook"
        (crate / "src" / "lib.rs").write_text("//! edited, not committed\n", encoding="utf-8")
        code, out = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)
        self.assertIn("programs/cap_hook/src/lib.rs", out)

    def test_refuses_to_record_a_binary_that_is_not_there(self) -> None:
        (self.fixture.root / "programs" / "cap_hook" / "target" / "deploy" / "cap_hook.so").unlink()
        code, _ = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)
        self.assertFalse(self.fixture.artefact.exists())


class TestVerify(ProvenanceCase):
    def test_a_freshly_written_record_verifies(self) -> None:
        code, out = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        self.assertIn("ok, 2 program(s)", out)
        # The fixture has no generated lockfile, so a green run has to say that check did
        # not happen. A skip the output does not mention is the failure this tool fixes.
        self.assertIn("not re-derived on this machine: lockfile", out)

    def test_a_mutated_source_hash_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][1]["source_files"]["programs/cap_hook/src/lib.rs"] = "0" * 64
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-file: v2 programs/cap_hook/src/lib.rs", out)
        self.assertIn("0" * 64, out)

    def test_a_source_file_edited_after_the_build_is_reported(self) -> None:
        self.fixture.write()
        crate = self.fixture.root / "programs" / "cap_hook"
        (crate / "src" / "state.rs").write_text("//! changed\n", encoding="utf-8")

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-file: v2 programs/cap_hook/src/state.rs", out)

    def test_a_mutated_binary_hash_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][0]["binary"]["sha256"] = "f" * 64
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("binary: v1", out)

    def test_an_absent_binary_is_reported(self) -> None:
        self.fixture.write()
        (self.fixture.root / "programs" / "cap_hook" / "target" / "deploy" / "cap_hook-v1.so").unlink()

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("binary: v1", out)
        self.assertIn("absent", out)

    def test_a_size_that_does_not_match_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][1]["binary"]["bytes"] = 1
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("bytes", out)

    def test_a_source_commit_that_no_longer_exists_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][0]["source_commit"] = "f" * 40
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-commit: v1", out)

    def test_a_program_id_the_tree_stopped_stating_is_reported(self) -> None:
        self.fixture.write()
        (self.fixture.root / "records" / "devnet-artefacts.json").write_text(
            json.dumps({"programId": "7ZZ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"}),
            encoding="utf-8",
        )

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("program-id: v1", out)

    def test_a_v2_id_changed_in_the_code_that_states_it_is_reported(self) -> None:
        # The reviewer's attack on the committed record: change the id where the code keeps
        # it and see whether verify notices. With v2's id recorded as null, it did not.
        self.fixture.write()
        gateway = self.fixture.root / "market_swarm" / "gateway.py"
        gateway.write_text(
            FIXTURE_GATEWAY.replace(
                '"v2": "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w"',
                '"v2": "9ZZZnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w"',
            ),
            encoding="utf-8",
        )

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("program-id: v2", out)
        self.assertIn("CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w", out)
        self.assertIn("9ZZZnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w", out)

    def test_an_id_with_no_source_is_a_violation_not_a_skip(self) -> None:
        # The second half of the reviewer's attack: the old check required both fields, so
        # deleting one line of JSON turned the check off entirely.
        self.fixture.write()
        document = self.fixture.document()
        del document["programs"][0]["program_id_source"]
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("program-id: v1 records 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva", out)
        self.assertIn("no program_id_source", out)

    def test_a_changed_id_with_the_source_deleted_is_still_a_violation(self) -> None:
        # Both halves of the reviewer's mutation at once: 7ZZZ... for an id, no source. This
        # is what returned 0 before, and a reviewer can run it in one line.
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][0]["program_id"] = (
            "7ZZZ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
        )
        del document["programs"][0]["program_id_source"]
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("7ZZZ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva", out)
        self.assertIn("no program_id_source", out)
        self.assertIn("the tree now states 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva", out)

    def test_a_version_the_tree_states_an_id_for_cannot_record_none(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][1]["program_id"] = None
        document["programs"][1]["program_id_source"] = None
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("program-id: v2 records no id", out)
        self.assertIn("CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w", out)

    def test_zeroed_rebuild_hashes_under_a_true_reproducible_claim_are_reported(self) -> None:
        same = self.fixture.root / "same.so"
        same.write_bytes(b"v2 bytes\n")
        code, out = self.fixture.write("--rebuild", f"v2={same}")
        self.assertEqual(code, build_provenance.EXIT_OK, out)

        document = self.fixture.document()
        for entry in document["programs"]:
            for rebuild in entry["rebuilds"]:
                rebuild["sha256"] = "0" * 64
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("rebuild: v2 rebuild 1", out)
        self.assertIn("did not reproduce the bytes", out)
        self.assertIn("reproducible: v2 records True and its rebuilds imply False", out)

    def test_reproducible_true_with_no_rebuild_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][0]["reproducible"] = True
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("reproducible: v1 claims True and records no rebuild", out)

    def test_a_fabricated_toolchain_line_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["toolchain"]["cargo_build_sbf"] = "cargo-build-sbf 0.0.0-fake"
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("toolchain: the record quotes cargo_build_sbf", out)
        self.assertIn("cargo-build-sbf 0.0.0-fake", out)
        self.assertIn("cargo-build-sbf 4.4.0", out)

    def test_a_toolchain_line_that_is_not_a_version_line_is_reported(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["toolchain"]["solana_cli"] = "whatever was on the machine"
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("is not a version line for solana", out)

    def test_a_machine_without_the_toolchain_says_so_instead_of_claiming_it(self) -> None:
        self.fixture.write()
        code, out = self.fixture.verify_without_toolchain()

        self.assertEqual(code, build_provenance.EXIT_OK, out)
        self.assertIn("not re-derived on this machine: toolchain", out)

    def test_a_nested_module_added_after_the_build_is_reported(self) -> None:
        self.fixture.write()
        crate = self.fixture.root / "programs" / "cap_hook"
        (crate / "src" / "sub").mkdir()
        (crate / "src" / "sub" / "mod.rs").write_text("//! nested\n", encoding="utf-8")

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-set: v2 programs/cap_hook/src/sub/mod.rs", out)
        self.assertIn("not in the record", out)

    def test_a_build_script_added_after_the_build_is_reported(self) -> None:
        self.fixture.write()
        crate = self.fixture.root / "programs" / "cap_hook"
        (crate / "build.rs").write_text("fn main() {}\n", encoding="utf-8")

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-set: v2 programs/cap_hook/build.rs", out)

    def test_a_nested_module_and_a_build_script_are_hashed_by_write(self) -> None:
        crate = self.fixture.root / "programs" / "cap_hook"
        (crate / "src" / "sub").mkdir()
        (crate / "src" / "sub" / "mod.rs").write_text("//! nested\n", encoding="utf-8")
        (crate / "build.rs").write_text("fn main() {}\n", encoding="utf-8")
        self.fixture.commit_all("nested module and build script")

        code, out = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        recorded = self.fixture.entry("v2")["source_files"]
        self.assertIn("programs/cap_hook/src/sub/mod.rs", recorded)
        self.assertIn("programs/cap_hook/build.rs", recorded)

        # And now an edit to either is visible, which is the whole point of hashing them.
        (crate / "src" / "sub" / "mod.rs").write_text("//! edited\n", encoding="utf-8")
        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("source-file: v2 programs/cap_hook/src/sub/mod.rs", out)

    def test_a_lockfile_that_moved_after_the_record_is_reported(self) -> None:
        lock = self.fixture.root / "programs" / "cap_hook" / "Cargo.lock"
        lock.write_text("# pins\n", encoding="utf-8")
        self.fixture.commit_all("the generated pin file")
        code, out = self.fixture.write()
        self.assertEqual(code, build_provenance.EXIT_OK, out)

        lock.write_text("# different pins\n", encoding="utf-8")
        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("lockfile: programs/cap_hook/Cargo.lock", out)

    def test_an_entry_for_an_unknown_version_is_a_violation_not_a_traceback(self) -> None:
        # A record whose version label no longer names a version this tool knows has no place
        # to read an id from, so it is a shape violation: a gate reports, it does not crash.
        self.fixture.write()
        document = self.fixture.document()
        document["programs"][1]["version"] = "v9"
        self.fixture.save(document)

        code, out = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_VIOLATION)
        self.assertIn("shape: v9 is not a version this record knows", out)

    def test_a_record_with_no_programs_is_unreadable_not_a_pass(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["programs"] = []
        self.fixture.save(document)

        code, _ = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)

    def test_an_unknown_schema_is_unreadable(self) -> None:
        self.fixture.write()
        document = self.fixture.document()
        document["schema"] = "build-provenance/99"
        self.fixture.save(document)

        code, _ = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)

    def test_broken_json_is_unreadable(self) -> None:
        self.fixture.artefact.write_text("{ not json", encoding="utf-8")
        code, _ = self.fixture.verify()
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE)


class TestCargoName(unittest.TestCase):
    def test_the_lib_table_names_the_program_and_the_package_table_does_not(self) -> None:
        self.assertEqual(build_provenance.cargo_lib_name(FIXTURE_CARGO), "cap_hook")

    def test_with_no_lib_table_the_package_name_is_the_fallback(self) -> None:
        text = '[package]\nname = "cap-hook"\nversion = "0.1.0"\n'
        self.assertEqual(build_provenance.cargo_lib_name(text), "cap-hook")

    def test_no_name_at_all_is_none_rather_than_an_invention(self) -> None:
        self.assertIsNone(build_provenance.cargo_lib_name('[lib]\ncrate-type = ["cdylib"]\n'))


class TestReadingTheCodeThatStatesTheId(unittest.TestCase):
    """`stated_program_id` reads a dict literal; it must never import the module."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="build-provenance-id-"))
        self.addCleanup(shutil.rmtree, self.root, True)
        (self.root / "market_swarm").mkdir()

    def test_a_dict_literal_is_read_without_running_the_file(self) -> None:
        # FIXTURE_GATEWAY raises on import, so a reader that executes it cannot return here.
        (self.root / "market_swarm" / "gateway.py").write_text(
            FIXTURE_GATEWAY, encoding="utf-8"
        )
        value, origin = build_provenance.stated_program_id(self.root, "v2")
        self.assertEqual(value, "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w")
        self.assertEqual(origin, 'market_swarm/gateway.py#PROGRAM_IDS["v2"]')

    def test_an_annotated_table_is_read_too(self) -> None:
        (self.root / "market_swarm" / "gateway.py").write_text(
            'PROGRAM_IDS: dict[str, str] = {"v2": "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w"}\n',
            encoding="utf-8",
        )
        value, _ = build_provenance.stated_program_id(self.root, "v2")
        self.assertEqual(value, "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w")

    def test_a_file_that_is_not_there_states_nothing_rather_than_inventing_one(self) -> None:
        self.assertEqual(build_provenance.stated_program_id(self.root, "v2"), (None, None))

    def test_a_table_with_no_entry_for_the_version_states_nothing(self) -> None:
        (self.root / "market_swarm" / "gateway.py").write_text(
            'PROGRAM_IDS = {"v1": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"}\n',
            encoding="utf-8",
        )
        self.assertEqual(build_provenance.stated_program_id(self.root, "v2"), (None, None))

    def test_a_computed_value_is_not_read_as_if_it_were_a_literal(self) -> None:
        (self.root / "market_swarm" / "gateway.py").write_text(
            'PROGRAM_IDS = {"v2": compute_the_id()}\n',
            encoding="utf-8",
        )
        self.assertEqual(build_provenance.stated_program_id(self.root, "v2"), (None, None))


class TestBoundedChildren(ProvenanceCase):
    """No child can hold the tool open: every `subprocess.run` carries a ceiling."""

    def hung_git_on_path(self) -> dict:
        hang = self.fixture.root / "hang"
        hang.mkdir()
        fake = hang / "git"
        # `exec` so the process `subprocess.run` waits on is the sleep itself and the timeout
        # kills it, rather than leaving a grandchild behind.
        fake.write_text("#!/bin/sh\nexec sleep 120\n", encoding="utf-8")
        fake.chmod(0o755)
        # The fake comes first, so `git` is the sleeper; the real paths stay on PATH so the
        # shell that runs it can find `sleep`. A PATH with nothing else would test a missing
        # binary, not a hung one.
        return {"PATH": f"{hang}:/usr/bin:/bin"}

    def test_a_hung_git_cannot_hang_verify(self) -> None:
        self.fixture.write()
        started = time.monotonic()
        with mock.patch.dict(os.environ, self.hung_git_on_path()), mock.patch.object(
            build_provenance, "COMMAND_TIMEOUT_SECONDS", 0.5
        ):
            code, out = run(["verify", "--root", str(self.fixture.root)])
        elapsed = time.monotonic() - started

        # A timeout is a fault of the machine, not a violation in the record: exit 2, named.
        self.assertEqual(code, build_provenance.EXIT_UNREADABLE, out)
        self.assertIn("did not finish within 0.5s", out)
        self.assertLess(elapsed, 30.0, "the tool waited on a hung child")

    def test_a_hung_git_cannot_hang_write(self) -> None:
        started = time.monotonic()
        with mock.patch.dict(os.environ, self.hung_git_on_path()), mock.patch.object(
            build_provenance, "COMMAND_TIMEOUT_SECONDS", 0.5
        ):
            code, out = run(["write", "--root", str(self.fixture.root)])
        elapsed = time.monotonic() - started

        self.assertEqual(code, build_provenance.EXIT_UNREADABLE, out)
        self.assertIn("did not finish within 0.5s", out)
        self.assertLess(elapsed, 30.0, "the tool waited on a hung child")

    def test_every_subprocess_call_in_the_tool_carries_a_timeout(self) -> None:
        # The structural form of the same claim: a `subprocess.run` with no `timeout=` in
        # this file is a child that can hang the gate, and one is enough to lose a run.
        source = (REPO_ROOT / "tools" / "build_provenance.py").read_text(encoding="utf-8")
        calls = re.findall(r"subprocess\.run\(", source)
        self.assertEqual(len(calls), 1, calls)
        start = source.index("subprocess.run(")
        self.assertIn("timeout=COMMAND_TIMEOUT_SECONDS", source[start : start + 400])


class TestTheCommittedArtefact(unittest.TestCase):
    """The record this repository ships, not a fixture."""

    def setUp(self) -> None:
        self.path = REPO_ROOT / build_provenance.ARTEFACT_PATH
        self.assertTrue(self.path.is_file(), f"missing {self.path.name}")
        self.document = json.loads(self.path.read_text(encoding="utf-8"))

    def test_quotes_the_measured_figures_the_readme_quotes(self) -> None:
        for entry in self.document["programs"]:
            size, digest = MEASURED[entry["version"]]
            self.assertEqual(entry["binary"]["bytes"], size, entry["version"])
            self.assertEqual(entry["binary"]["sha256"], digest, entry["version"])

    def test_names_the_toolchain_that_decides_the_bytes(self) -> None:
        toolchain = self.document["toolchain"]
        self.assertTrue(toolchain["cargo_build_sbf"].startswith("cargo-build-sbf "))
        self.assertTrue(toolchain["solana_cli"].startswith("solana-cli "))

    def test_pins_v2s_program_id_from_the_code_that_states_it(self) -> None:
        v2 = self.entry("v2")
        self.assertEqual(v2["program_id"], "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w")
        self.assertEqual(
            v2["program_id_source"], 'market_swarm/gateway.py#PROGRAM_IDS["v2"]'
        )
        # And it is the id the code actually states, re-read rather than trusted.
        stated, origin = build_provenance.stated_program_id(REPO_ROOT, "v2")
        self.assertEqual(v2["program_id"], stated)
        self.assertEqual(v2["program_id_source"], origin)

    def test_says_what_verify_rederives_and_what_it_cannot(self) -> None:
        checks = self.document["verify_checks"]
        self.assertTrue(checks["rederived"])
        self.assertTrue(checks["not_rederived"])
        quoted = " ".join(checks["not_rederived"])
        self.assertIn("toolchain", quoted)
        self.assertIn("never compiles anything", quoted)

    def entry(self, version: str) -> dict:
        for entry in self.document["programs"]:
            if entry["version"] == version:
                return entry
        raise AssertionError(f"no {version} entry in the record")

    def test_carries_no_home_path_no_scratch_path_and_no_pid(self) -> None:
        # The repository is public and tools/public_safety.py refuses both by pattern. A
        # record that leaks the machine layout is a record nobody can publish.
        text = self.path.read_text(encoding="utf-8")
        # Built from parts, because a checker that greps this file for these very patterns
        # is the point: written literally they would be hits in this file instead.
        self.assertNotIn("/" + "home" + "/", text)
        self.assertNotIn("/" + "tmp" + "/", text)
        self.assertIsNone(re.search(r"\b(?:p|pg)id\s*[:=]?\s*\d{3,7}\b", text))

    def test_every_recorded_path_is_repo_relative(self) -> None:
        for entry in self.document["programs"]:
            paths = list(entry["source_files"]) + [entry["binary"]["path"]]
            for path in paths:
                self.assertFalse(path.startswith("/"), path)
                self.assertTrue(path.startswith("programs/cap_hook/"), path)

    def test_the_recorded_source_still_hashes_to_the_record(self) -> None:
        code, out = run(["verify", "--root", str(REPO_ROOT), "--quiet"])
        if not all(
            (REPO_ROOT / entry["binary"]["path"]).is_file()
            for entry in self.document["programs"]
        ):
            # The binaries are git-ignored, so a fresh clone has none; that is a missing
            # binary, not a broken record, and this test says which one it saw.
            self.assertEqual(code, build_provenance.EXIT_VIOLATION, out)
            self.assertIn("absent", out)
            return
        self.assertEqual(code, build_provenance.EXIT_OK, out)


if __name__ == "__main__":
    unittest.main()

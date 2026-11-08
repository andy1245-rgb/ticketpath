"""The build provenance record, proven to be able to fail.

The record is only worth having if a stale one is caught, so every method here builds a
small repository, writes the record against it, then makes the *smallest* change that is a
lie -- a mutated source hash, an absent binary, a commit that no longer exists, a program id
the tree stopped stating -- and asserts the checker names it. The positive case is the same
fixture with nothing wrong: a checker that fails everything is as useless as one that fails
nothing, and the positive assertion is what keeps that honest.

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
import re
import shutil
import subprocess
import tempfile
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
            build_provenance, "toolchain_versions", return_value={"rustc": "rustc 1.95.0"}
        ):
            return run(["write", "--root", str(self.root), *extra])

    def verify(self) -> tuple[int, str]:
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

        # The id is the one the tree states, and the record says where it read it.
        self.assertEqual(
            v1["program_id"], "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
        )
        self.assertEqual(
            v1["program_id_source"], "records/devnet-artefacts.json#programId"
        )
        self.assertIsNone(v2["program_id"])
        self.assertIsNone(v2["program_id_source"])

        # ISO-8601 UTC, second resolution, Z suffix.
        self.assertRegex(document["generated_at"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        datetime.strptime(document["generated_at"], "%Y-%m-%dT%H:%M:%SZ")

    def test_records_a_supplied_rebuild_and_whether_it_matched(self) -> None:
        same = self.fixture.root / "same.so"
        same.write_bytes(b"v2 bytes\n")
        different = self.fixture.root / "different.so"
        different.write_bytes(b"other bytes\n")

        code, out = self.fixture.write("--rebuild", f"v2={same}")
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        rebuild = self.fixture.entry("v2")["rebuilds"]
        self.assertEqual(len(rebuild), 1)
        self.assertTrue(rebuild[0]["identical"])
        self.assertTrue(self.fixture.entry("v2")["reproducible"])

        code, out = self.fixture.write("--rebuild", f"v2={different}")
        self.assertEqual(code, build_provenance.EXIT_OK, out)
        rebuild = self.fixture.entry("v2")["rebuilds"]
        self.assertFalse(rebuild[0]["identical"])
        self.assertFalse(self.fixture.entry("v2")["reproducible"])

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

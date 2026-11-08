"""`tools/site_records.py`: the copies a static page prints, and the checks that keep them true.

The subject is a copy, so the failures worth testing are the ones a copy makes easy: a copy
that drifted from the record it came from, one that is missing, one that was quietly
replaced by a rehearsal the local validator wrote, and a source that is not a record of any
deployment at all. Every assertion is on bytes on disk or on the tool's own report, not on a
helper's return value.

Each fixture tree is built in a temporary directory, so nothing here writes to the real
repository, and the mapping is passed in rather than patched onto the module, so no test can
change what another one reads.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from tools import site_records

REPO_ROOT = Path(__file__).resolve().parents[1]

RECORD = {
    "asOf": "2026-11-07T18:34:29.183Z",
    "checkedAt": "2026-11-08T00:50:25.281Z",
    "cluster": "devnet",
    "programId": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva",
    "signature": "2Lx6cboK8kvuJ7H6w2CELVZg3xF7cSHtBTSBXqi1w6KN2eXkQ6skqNPwnT5iVVAdrfBs5LiAau3pXiBMTtZMGCPZ",
    "slot": 519845921,
}

RECORDS = (("records/devnet-artefacts.json", "frontend/data/devnet-artefacts.json"),)


def _tree(record: dict | None = None, name: str = "devnet-artefacts.json") -> Path:
    """A repository root with one record in it and an empty frontend/data."""
    root = Path(tempfile.mkdtemp(prefix="site-records-"))
    (root / "records").mkdir()
    (root / "frontend" / "data").mkdir(parents=True)
    (root / "records" / name).write_text(json.dumps(record if record is not None else RECORD, indent=2) + "\n")
    return root


class CommittedCopyTest(unittest.TestCase):
    """The real tree: the committed copies are the records, byte for byte."""

    def test_every_record_has_a_copy_that_matches_it(self) -> None:
        self.assertEqual(site_records.check(REPO_ROOT), [])

    def test_the_devnet_copy_is_the_devnet_record(self) -> None:
        for src, dst in site_records.RECORDS:
            self.assertEqual(
                (REPO_ROOT / dst).read_bytes(),
                (REPO_ROOT / src).read_bytes(),
                f"{dst} is not a copy of {src}",
            )

    def test_the_copy_records_a_deployment(self) -> None:
        """A copy without a cluster or a program id cannot be printed as one."""
        copy = json.loads((REPO_ROOT / "frontend/data/devnet-artefacts.json").read_text())
        self.assertEqual(copy["cluster"], "devnet")
        self.assertEqual(copy["programId"], "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva")
        self.assertTrue(copy["signature"])


class ReportTest(unittest.TestCase):
    """What the tool says when the bundle and the record disagree."""

    def test_a_missing_copy_is_reported_and_names_the_fix(self) -> None:
        root = _tree()
        problems = site_records.check(root, RECORDS)
        self.assertEqual(len(problems), 1)
        self.assertIn("missing", problems[0])
        self.assertIn("tools/site_records.py", problems[0])

    def test_a_changed_copy_is_reported_with_both_hashes(self) -> None:
        root = _tree()
        site_records.write(root, RECORDS)
        self.assertEqual(site_records.check(root, RECORDS), [])
        copy = root / "frontend/data/devnet-artefacts.json"
        copy.write_bytes(copy.read_bytes().replace(b'"slot": 519845921', b'"slot": 519845922'))
        problems = site_records.check(root, RECORDS)
        self.assertEqual(len(problems), 1)
        self.assertIn(site_records.sha256(copy.read_bytes()), problems[0])

    def test_write_restores_a_copy_that_drifted(self) -> None:
        root = _tree()
        site_records.write(root, RECORDS)
        (root / "frontend/data/devnet-artefacts.json").write_text("{}\n")
        site_records.write(root, RECORDS)
        self.assertEqual(site_records.check(root, RECORDS), [])

    def test_a_rehearsal_is_refused_by_name_before_it_is_read(self) -> None:
        root = _tree(name="devnet-artefacts.local.json")
        rehearsal = (("records/devnet-artefacts.local.json", "frontend/data/devnet-artefacts.json"),)
        with self.assertRaises(site_records.RecordRefused) as caught:
            site_records.write(root, rehearsal)
        self.assertIn("rehearsal", str(caught.exception))
        self.assertFalse((root / "frontend/data/devnet-artefacts.json").exists())

    def test_the_committed_mapping_has_no_rehearsal_in_it(self) -> None:
        for src, _dst in site_records.RECORDS:
            self.assertFalse(src.endswith(site_records.REHEARSAL_SUFFIX), src)

    def test_a_source_that_is_not_json_is_refused(self) -> None:
        root = _tree()
        (root / "records/devnet-artefacts.json").write_text("not json\n")
        with self.assertRaises(site_records.RecordRefused):
            site_records.write(root, RECORDS)

    def test_a_source_without_a_program_id_is_refused(self) -> None:
        root = _tree(record={"cluster": "devnet"})
        with self.assertRaises(site_records.RecordRefused) as caught:
            site_records.write(root, RECORDS)
        self.assertIn("programId", str(caught.exception))

    def test_a_source_without_a_cluster_is_refused(self) -> None:
        root = _tree(record={"programId": "abc"})
        with self.assertRaises(site_records.RecordRefused) as caught:
            site_records.write(root, RECORDS)
        self.assertIn("cluster", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

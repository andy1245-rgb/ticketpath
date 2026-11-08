"""The signer: one signature out, nothing else, and it never sees a real key here.

The keypair this test uses is generated at run time in a temporary directory from a fixed
seed, so it is reproducible and can never be mistaken for a real one. Nothing about the
devnet authority is touched.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from ticketpath.core import base58, ed25519  # noqa: E402

SIGNER = REPO_ROOT / "tools" / "solana_sign.py"
SEED = bytes(range(32))  # a test seed, published here, holding nothing


class TestSigner(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = Path(tempfile.mkdtemp(prefix="tp-signer-test-"))
        self.addCleanup(shutil.rmtree, self.directory, True)
        public_key, _ = ed25519.sign(SEED, b"")
        self.public = public_key
        self.keypair = self.directory / "authority.json"
        self.keypair.write_text(json.dumps(list(SEED) + list(public_key)), encoding="utf-8")
        os.chmod(self.keypair, 0o600)

    def run_signer(self, message: bytes, *, keypair: Path | None = None) -> subprocess.CompletedProcess:
        environment = dict(os.environ)
        environment["TP_DEVNET_KEYPAIR"] = str(keypair or self.keypair)
        return subprocess.run(
            [sys.executable, str(SIGNER)], input=message, capture_output=True, timeout=120, env=environment
        )

    def test_it_prints_one_base58_signature_and_nothing_else(self) -> None:
        message = b"the message a transaction would carry"
        completed = self.run_signer(message)
        self.assertEqual(completed.returncode, 0, completed.stderr)
        text = completed.stdout.decode().strip()
        self.assertNotIn("\n", text)
        signature = base58.decode(text)
        self.assertEqual(len(signature), 64)
        self.assertTrue(ed25519.verify(self.public, signature, message))

    def test_the_public_key_mode_agrees_with_the_seed(self) -> None:
        environment = dict(os.environ)
        environment["TP_DEVNET_KEYPAIR"] = str(self.keypair)
        completed = subprocess.run(
            [sys.executable, str(SIGNER), "--public-key"], capture_output=True, timeout=120, env=environment
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.decode().strip(), base58.encode(self.public))

    def test_nothing_on_stdout_can_hold_key_material(self) -> None:
        message = b"anything"
        completed = self.run_signer(message)
        stdout = completed.stdout.decode()
        self.assertEqual(stdout.strip().count(" "), 0)
        self.assertNotIn(str(SEED[0]), stdout.replace(base58.encode(self.public), ""))
        # the seed itself must never appear as a number list or as base58
        self.assertNotIn(base58.encode(SEED), stdout)

    def test_a_corrupt_keypair_is_refused_without_echoing_it(self) -> None:
        corrupt = self.directory / "corrupt.json"
        corrupt.write_text(json.dumps(list(SEED) + list(bytes(32))), encoding="utf-8")
        completed = self.run_signer(b"x", keypair=corrupt)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, b"")
        self.assertIn("corrupt", completed.stderr.decode())

    def test_a_missing_keypair_is_refused_and_says_where_it_looked(self) -> None:
        completed = self.run_signer(b"x", keypair=self.directory / "absent.json")
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, b"")
        self.assertIn("no keypair at", completed.stderr.decode())

    def test_a_file_that_is_not_a_keypair_at_all_is_refused(self) -> None:
        wrong = self.directory / "not-a-keypair.json"
        wrong.write_text('{"hello": "world"}', encoding="utf-8")
        completed = self.run_signer(b"x", keypair=wrong)
        self.assertNotEqual(completed.returncode, 0)
        self.assertEqual(completed.stdout, b"")
        self.assertIn("64-integer shape", completed.stderr.decode())

    def test_the_publish_script_never_opens_the_keypair(self) -> None:
        # The rule this enforces: `tools/devnet_publish.py` hands the path to `solana`,
        # `spl-token` and this signer, and never reads the file itself. Checked line by line,
        # so a line that opens the keypair fails even if the rest of the file looks fine.
        source = (REPO_ROOT / "tools" / "devnet_publish.py").read_text(encoding="utf-8").splitlines()
        readers = ("open(", "read_text", "read_bytes", "json.load", "loads(", "readlines")
        offenders = [
            line.strip()
            for line in source
            if "ctx.keypair" in line and any(reader in line for reader in readers)
        ]
        self.assertEqual(offenders, [])
        self.assertIn('"--keypair", str(ctx.keypair)', "\n".join(source))
        self.assertIn("solana_sign.py", "\n".join(source))

    def test_a_keypair_path_that_is_not_a_file_does_not_stop_a_dry_run(self) -> None:
        # Behavioural version of the same rule, with no grep: the parent is handed a directory
        # where a keypair should be and still plans the whole run, so nothing in it opened it.
        # `--program-id` is not the frozen devnet id on purpose: that id with the v2 build on
        # disk is the refusal `tests/test_devnet_publish.py` covers, and this test is about
        # the keypair path, not about the frozen-upgrade guard.
        trap = self.directory / "a-directory-not-a-keypair.json"
        trap.mkdir()
        environment = dict(os.environ)
        environment["TP_DEVNET_KEYPAIR"] = str(trap)
        out = self.directory / "never-written.json"
        completed = subprocess.run(
            [
                sys.executable,
                str(REPO_ROOT / "tools" / "devnet_publish.py"),
                "--dry-run",
                "--program-id",
                "BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ",
                "--out",
                str(out),
            ],
            capture_output=True, text=True, timeout=300, env=environment, cwd=str(REPO_ROOT),
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()

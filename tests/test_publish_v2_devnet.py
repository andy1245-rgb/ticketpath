"""The refusals and the record discipline of `tools/publish_v2_devnet.py`, without a cluster.

Everything here runs offline in well under a second and asserts the properties that make a
devnet run trustworthy: the frozen paths are refused, the frozen program id is refused before
a deploy, the artefact cannot carry a secret or a home path, and the resume file refuses to mix
clusters.

The half that needs a cluster is not here. It is
`.swarm-runs/v2-devnet/local_rehearsal.py`, which starts a `solana-test-validator` and drives
this tool through six crash-and-resume scenarios; it is kept out of the tree because it writes
a validator ledger and keypairs, and no research claim rests on it. Run it with
`TP_V2_DEVNET_REHEARSAL=1 python3 -m unittest tests.test_publish_v2_devnet` to have this suite
shell it, or directly.

    python3 -m unittest tests.test_publish_v2_devnet -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools"))
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import devnet_publish as dp  # noqa: E402
import publish_v2 as pv  # noqa: E402
import publish_v2_devnet as pd  # noqa: E402

FROZEN = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"


def a_record(**overrides) -> dict:
    """A minimal artefact that `_assert_publishable` accepts, so a test can break one field."""
    record = {
        "version": 1,
        "checkerVersion": pd.CHECKER_VERSION,
        "cluster": "devnet",
        "rpcUrl": "https://api.devnet.solana.com",
        "writtenAt": "2026-11-08T00:00:00.000Z",
        "startedAt": "2026-11-08T00:00:00.000Z",
        "elapsedSeconds": 1.0,
        "elapsedBasis": "test",
        "firstTransactionAt": "2026-11-08T00:00:00Z",
        "programId": "Fiao9NXAKqVCPJLVbzxrkgx9o2Ndmc3yZBVwXG37Hq97",
        "program": {
            "path": "programs/cap_hook/target/deploy/cap_hook.so",
            "bytes": 111504,
            "sha256": "de89af3c",
            "sha256Source": "test",
            "sha256MatchesBuildOnDisk": True,
        },
        "deployAddress": "Fiao9NXAKqVCPJLVbzxrkgx9o2Ndmc3yZBVwXG37Hq97",
        "authority": "75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy",
        "deploy": {"signature": "4YfbbpX2BTiHgV9Koni1hkiTefiM4UK9ZY8ajd8Tvrrp2D9zM76M6P7o3ekVYP7icZhMm4E25NtQUqBTS74isF8x", "slot": 1},
        "mints": {"phase1": "11111111111111111111111111111111", "phase2": "11111111111111111111111111111111"},
        "record": "11111111111111111111111111111111",
        "extraMetas": "11111111111111111111111111111111",
        "seller": "11111111111111111111111111111111",
        "buyer": "11111111111111111111111111111111",
        "buyerAta": "11111111111111111111111111111111",
        "arguments": {"faceLamports": 1, "capBps": 2500, "bandLowLamports": 1},
        "recordAtEnd": {"face_value_lamports": 1},
        "recordAtEndSlot": 2,
        "proofs": {"a": {}, "b": {}, "c": {}, "d": {}, "e": {}, "f": {}, "g": {}},
        "proofs_v2": {"band": {}},
        "steps": {"deploy": {"signature": "x", "slot": 1}},
        "steps_v2": {},
        "phase2": {},
        "refusals": [],
        "errorCodes": {"required": {}, "observed": {}, "missing": {}},
        "pdas": {},
        "balances": {"authorityStart": 10, "authorityEnd": 5, "spentLamports": 5},
        "resumedSteps": [],
        "explorer": {"program": "https://explorer.solana.com/address/x?cluster=devnet"},
        "clusterFacts": {
            "token2022": dp.TOKEN_2022_PROGRAM,
            "frozenProgramId": FROZEN,
            "frozenProgramUntouched": True,
            "frozenArtefact": "records/devnet-artefacts.json",
            "funding": "the operator's funded authority; no faucet, no airdrop",
        },
        "resume": {"path": ".swarm-runs/v2-devnet/resume.json", "note": "bookkeeping"},
        "localOnly": False,
    }
    record.update(overrides)
    return record


class TheRecordDiscipline(unittest.TestCase):
    def test_a_clean_record_is_accepted(self):
        pd._assert_publishable(a_record())

    def test_an_extra_field_is_refused(self):
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(a_record(surprise="x"))

    def test_a_home_path_anywhere_is_refused(self):
        for name in ("authority", "program", "clusterFacts"):
            record = a_record()
            record[name] = {"path": str(Path.home() / "secret.json")} if isinstance(record[name], dict) else str(Path.home() / "x")
            with self.assertRaises(dp.PublishError, msg=f"{name} was not checked"):
                pd._assert_publishable(record)

    def test_a_home_path_inside_a_list_is_refused(self):
        record = a_record(refusals=[{"error": "/home/someone/x"}])
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(record)

    def test_a_key_handle_anywhere_is_refused(self):
        record = a_record(deploy={"note": "signed with the keypair at /x"})
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(record)

    def test_a_record_for_another_cluster_is_refused(self):
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(a_record(cluster="mainnet-beta"))

    def test_a_local_only_record_is_refused(self):
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(a_record(localOnly=True))

    def test_the_frozen_program_id_is_refused_twice(self):
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(a_record(programId=FROZEN))
        record = a_record()
        record["clusterFacts"] = {**record["clusterFacts"], "frozenProgramId": "11111111111111111111111111111111"}
        with self.assertRaises(dp.PublishError):
            pd._assert_publishable(record)


class TheFrozenGuards(unittest.TestCase):
    def test_the_frozen_program_id_is_refused_before_a_deploy(self):
        with self.assertRaises(pd.DevnetRefused):
            pd.refuse_frozen_target(program_id=FROZEN, binary=b"", source="test")

    def test_a_v2_binary_under_another_id_is_allowed(self):
        binary = b"below floor policy=monitored held_since_unix"
        pd.refuse_frozen_target(program_id="11111111111111111111111111111111", binary=binary, source="test")

    def test_the_sibling_guard_still_refuses_the_v2_binary_on_the_frozen_id(self):
        """The check the operator said must not be bypassed, called exactly as the tool calls it."""
        binary = b"below floor policy=monitored held_since_unix"
        with self.assertRaises(dp.Refused):
            dp.refuse_frozen_devnet_upgrade(program_id=FROZEN, binary=binary, source="test")

    def test_every_frozen_write_path_is_refused(self):
        for path in (
            "records/devnet-artefacts.json",
            "records/devnet-progress.json",
            "records/onchain-v2.local.json",
            "programs/cap_hook/target/deploy/cap_hook-keypair.json",
        ):
            with self.assertRaises(pd.DevnetRefused, msg=path):
                pd.resolve_guarded(path, "the artefact path")

    def test_a_relative_path_that_escapes_is_still_resolved(self):
        with self.assertRaises(pd.DevnetRefused):
            pd.resolve_guarded("records/../records/devnet-artefacts.json", "the artefact path")

    def test_the_local_v2_keypair_is_refused_as_a_deploy_target(self):
        with self.assertRaises(pd.DevnetRefused):
            pd.resolve_guarded(str(pv.DEPLOY_KEYPAIR), "the deploy keypair")

    def test_a_new_keypair_path_is_allowed(self):
        resolved = pd.resolve_guarded("programs/cap_hook/target/deploy/v2-devnet-keypair.json", "the deploy keypair")
        self.assertTrue(str(resolved).endswith("v2-devnet-keypair.json"))


class TheResumeFile(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "resume.json"

    def tearDown(self):
        self.directory.cleanup()

    def test_a_written_file_is_0600_and_versioned(self):
        resume = pd.Resume(self.path, cluster="devnet").load()
        resume.put("programId", "11111111111111111111111111111111")
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)
        state = json.loads(self.path.read_text())
        self.assertEqual(state["version"], pd.RESUME_VERSION)
        self.assertEqual(state["cluster"], "devnet")

    def test_a_resume_file_from_another_cluster_is_refused(self):
        self.path.write_text(json.dumps({"version": pd.RESUME_VERSION, "cluster": "testnet"}))
        with self.assertRaises(pd.DevnetRefused):
            pd.Resume(self.path, cluster="devnet").load()

    def test_a_resume_file_from_another_version_is_refused(self):
        self.path.write_text(json.dumps({"version": pd.RESUME_VERSION + 1, "cluster": "devnet"}))
        with self.assertRaises(pd.DevnetRefused):
            pd.Resume(self.path, cluster="devnet").load()

    def test_an_absolute_path_is_refused(self):
        resume = pd.Resume(self.path, cluster="devnet").load()
        with self.assertRaises(pd.DevnetRefused):
            resume.put("mint:1:main", {"address": "/home/someone/keys.json"})

    def test_a_key_handle_is_refused(self):
        resume = pd.Resume(self.path, cluster="devnet").load()
        with self.assertRaises(pd.DevnetRefused):
            resume.put("note", "the deploy keypair is fine")

    def test_a_dry_run_resume_is_never_written(self):
        resume = pd.Resume(self.path, cluster="devnet", writable=False).load()
        resume.put("programId", "11111111111111111111111111111111")
        self.assertFalse(self.path.exists())


class TheCommandLine(unittest.TestCase):
    def test_the_defaults(self):
        args = pd.parse_args([])
        self.assertEqual(args.cluster, "devnet")
        self.assertEqual(Path(args.out), pd.DEFAULT_OUT)
        self.assertEqual(Path(args.resume), pd.DEFAULT_RESUME)
        self.assertFalse(args.dry_run)

    def test_only_devnet_is_accepted(self):
        with self.assertRaises(SystemExit):
            pd.parse_args(["--cluster", "mainnet-beta"])
        with self.assertRaises(SystemExit):
            pd.parse_args(["--cluster", "testnet"])

    def test_the_keypair_falls_back_to_the_environment(self):
        os.environ["TP_DEVNET_KEYPAIR"] = "/somewhere/authority.json"
        try:
            self.assertEqual(pd.parse_args([]).keypair, "/somewhere/authority.json")
            self.assertEqual(pd.parse_args(["--keypair", "/other.json"]).keypair, "/other.json")
        finally:
            os.environ.pop("TP_DEVNET_KEYPAIR", None)

    def test_no_keypair_is_a_refusal_not_a_crash(self):
        os.environ.pop("TP_DEVNET_KEYPAIR", None)
        # A fresh temporary directory rather than a fixed scratch path: nothing here is read or
        # written, because the refusal is the first thing `main` does, and a path this test does
        # not own is a path it cannot promise is absent.
        with tempfile.TemporaryDirectory() as directory:
            code = pd.main(
                [
                    "--dry-run",
                    "--out",
                    str(Path(directory) / "x.json"),
                    "--resume",
                    str(Path(directory) / "y.json"),
                ]
            )
        self.assertEqual(code, pd.EXIT_REFUSED)

    def test_the_module_is_importable_without_running_anything(self):
        self.assertTrue(callable(pd.main))
        self.assertTrue(issubclass(pd.DevnetProof, pv.LocalProof))


class TheEndpointGuard(unittest.TestCase):
    """`--cluster devnet` is a label; the endpoint is where the lamports go."""

    def test_devnet_and_loopback_are_allowed(self):
        for url in (
            "https://api.devnet.solana.com",
            "https://api.devnet.solana.com/",
            "http://127.0.0.1:8899",
            "http://localhost:8899",
        ):
            self.assertEqual(pd.refuse_foreign_rpc(url), url)

    def test_mainnet_is_refused_by_name(self):
        with self.assertRaises(pd.DevnetRefused) as caught:
            pd.refuse_foreign_rpc("https://api.mainnet-beta.solana.com")
        self.assertIn("mainnet-beta", str(caught.exception))

    def test_testnet_is_refused(self):
        with self.assertRaises(pd.DevnetRefused):
            pd.refuse_foreign_rpc("https://api.testnet.solana.com")

    def test_a_credential_in_the_url_is_refused_and_not_repeated(self):
        # The host is a reserved documentation name, not devnet's own: `user:password@host` is
        # spelled like an address, and this repository's public-safety check refuses a third
        # party's address in public text. The userinfo branch runs before the host is compared,
        # so the host is not what this test is measuring.
        with self.assertRaises(pd.DevnetRefused) as caught:
            pd.refuse_foreign_rpc("https://user:secret@devnet.invalid")
        self.assertNotIn("secret", str(caught.exception))

    def test_a_query_or_fragment_is_refused(self):
        for url in ("https://api.devnet.solana.com?key=1", "https://api.devnet.solana.com#x"):
            with self.assertRaises(pd.DevnetRefused):
                pd.refuse_foreign_rpc(url)

    def test_a_non_http_scheme_is_refused(self):
        for url in ("ftp://api.devnet.solana.com", "api.devnet.solana.com", ""):
            with self.assertRaises(pd.DevnetRefused):
                pd.refuse_foreign_rpc(url)


class ThePathGuards(unittest.TestCase):
    def test_a_non_json_deploy_keypair_is_refused_by_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "README.md"
            target.write_text("not a key")
            before = target.stat().st_mode & 0o777
            with self.assertRaises(pd.DevnetRefused):
                pd.preflight(
                    cluster="devnet",
                    rpc_url="https://api.devnet.solana.com",
                    authority=Path(directory) / "authority.json",
                    deploy_keypair=target,
                    out=Path(directory) / "out.json",
                    resume=pd.Resume(Path(directory) / "resume.json", cluster="devnet"),
                    min_lamports=1,
                    say=lambda line="": None,
                )
            self.assertEqual(target.stat().st_mode & 0o777, before, "a file this run did not create was chmodded")

    def test_a_directory_as_an_output_is_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(pd.DevnetRefused):
                pd.preflight(
                    cluster="devnet",
                    rpc_url="https://api.devnet.solana.com",
                    authority=Path(directory) / "authority.json",
                    deploy_keypair=Path(directory) / "d.json",
                    out=Path(directory),
                    resume=pd.Resume(Path(directory) / "resume.json", cluster="devnet"),
                    min_lamports=1,
                    say=lambda line="": None,
                )


@unittest.skipUnless(os.environ.get("TP_V2_DEVNET_REHEARSAL") == "1", "needs a local validator; set TP_V2_DEVNET_REHEARSAL=1")
class TheLocalRehearsal(unittest.TestCase):
    def test_the_rehearsal_passes(self):
        script = REPO / ".swarm-runs" / "v2-devnet" / "local_rehearsal.py"
        if not script.exists():
            self.skipTest("the rehearsal script is not on this machine")
        result = subprocess.run([sys.executable, str(script)], capture_output=True, text=True, timeout=2400, cwd=str(REPO))
        self.assertEqual(result.returncode, 0, result.stdout[-3000:] + result.stderr[-2000:])


if __name__ == "__main__":
    unittest.main()

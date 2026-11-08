"""The simulated state machine and the quote commitment.

Two properties matter more than the lines themselves: every line says `simulated`, and
nothing that leaves `chain_client` contains a signature. A mirror that quietly claims a
cluster returned something would be the same lie as a `[DEVNET]` badge with nothing
behind it.
"""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ticketpath.adapters import chain_client
from ticketpath.onchain import sim


class TestCapArm(unittest.TestCase):
    def test_the_ceiling_is_admitted_and_one_lamport_above_is_refused(self) -> None:
        # face 1.20 SOL at 1500 bps = 1_200_000_000 + 180_000_000 = 1_380_000_000
        self.assertEqual(sim.ceiling_lamports(1_200_000_000, 1500), 1_380_000_000)
        lines = sim.run(("cap",))
        self.assertEqual([line["status"] for line in lines], ["ok", "refused"])
        self.assertEqual(lines[1]["code"], 6010)
        self.assertEqual(lines[1]["name"], "E_CAP_EXCEEDED")
        self.assertIn("1380000001", lines[1]["detail"])

    def test_every_line_says_simulated(self) -> None:
        for arm in ("cap", "unstaged", "unverified", "theorem"):
            for line in sim.run((arm,)):
                with self.subTest(arm=arm):
                    self.assertIs(line["simulated"], True)


class TestOtherArms(unittest.TestCase):
    def test_an_unstaged_custody_move_is_refused(self) -> None:
        lines = sim.run(("unstaged",))
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0]["code"], 6009)
        self.assertEqual(lines[0]["status"], "refused")

    def test_an_unverified_destination_is_refused_then_admitted(self) -> None:
        lines = sim.run(("unverified",))
        self.assertEqual([line["status"] for line in lines], ["refused", "ok"])
        self.assertEqual(lines[0]["code"], 6012)

    def test_the_theorem_sweep_is_three_faces_by_three_caps_by_three_prices(self) -> None:
        lines = sim.run(("theorem",))
        self.assertEqual(len(lines), 3 * 3 * 3)
        self.assertTrue(all("markup" in line["detail"] for line in lines))

    def test_an_unknown_arm_raises(self) -> None:
        with self.assertRaises(KeyError):
            sim.run(("nope",))


class TestMarkupArithmetic(unittest.TestCase):
    def test_markup_is_basis_points_over_face_rounding_half_away_from_zero(self) -> None:
        self.assertEqual(sim.markup_bps(1_380_000_000, 1_200_000_000), 1500)
        self.assertEqual(sim.markup_bps(1_200_000_000, 1_200_000_000), 0)
        self.assertEqual(sim.markup_bps(960_000_000, 1_200_000_000), -2000)


class TestQuoteCommitment(unittest.TestCase):
    FIELDS = {
        "quoteId": "q-test",
        "eventId": "evt_syn_02",
        "tierId": "tier_stg_general",
        "recommendedLamports": 1_380_000_000,
        "asOf": "2026-11-07T12:00:00.000Z",
        "modelVersion": "engine-2026-11-07",
    }

    def test_the_hash_is_the_sha256_of_the_canonical_json(self) -> None:
        # by hand: sorted keys, no whitespace, then sha256 of the UTF-8 bytes
        expected = hashlib.sha256(
            b'{"asOf":"2026-11-07T12:00:00.000Z","eventId":"evt_syn_02","modelVersion":"engine-2026-11-07",'
            b'"quoteId":"q-test","recommendedLamports":1380000000,"tierId":"tier_stg_general"}'
        ).hexdigest()
        self.assertEqual(chain_client.quote_hash(self.FIELDS), expected)

    def test_the_commitment_is_unavailable_and_says_why(self) -> None:
        commit = chain_client.quote_commit(quote_id="q-test", recommendation=self.FIELDS)
        self.assertFalse(commit["available"])
        self.assertEqual(commit["reason"], "no_toolchain_no_keypair_no_program")
        self.assertIsNone(commit["serialized"])
        self.assertIn(commit["quoteHash"], commit["memoText"])
        self.assertEqual(commit["instructions"][0]["program"], chain_client.MEMO_PROGRAM_DEVNET)

    def test_no_return_value_carries_a_signature(self) -> None:
        commit = chain_client.quote_commit(quote_id="q-test", recommendation=self.FIELDS)
        self.assertNotIn("signature", json.dumps(commit))
        self.assertFalse(chain_client.available())
        with self.assertRaises(chain_client.ChainUnavailable):
            chain_client.submit(commit)

    def test_the_quote_id_is_stable_for_the_same_three_fields(self) -> None:
        first = chain_client.quote_id_for(event_id="e", tier_id="t", as_of="2026-11-07T12:00:00.000Z")
        second = chain_client.quote_id_for(event_id="e", tier_id="t", as_of="2026-11-07T12:00:00.000Z")
        self.assertEqual(first, second)
        self.assertTrue(first.startswith("q-"))


class TestMemoProgramTable(unittest.TestCase):
    """The memo program id is per cluster, and every row is a measurement rather than a memory.

    Measured 2026-11-08T05:39:47Z: `getTransaction` on the proven memo transaction answers
    `accountKeys[3] == "Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"`, and its second
    instruction has `programIdIndex` 3. Measured again the same day on a local validator
    started from a fresh ledger: the shipped CLI's `--with-memo` instruction names the same
    id, in its simulation log and in the message it builds. See
    records/findings/40-memo-program-id.md and its correction.
    """

    MEASURED_DEVNET = "Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"
    CLI_MEMO = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

    def test_the_table_s_devnet_id_is_the_id_the_cluster_answered(self) -> None:
        self.assertEqual(chain_client.MEMO_PROGRAMS["devnet"], self.MEASURED_DEVNET)
        self.assertEqual(chain_client.memo_program_id("devnet"), self.MEASURED_DEVNET)
        self.assertEqual(chain_client.memo_program_id(), self.MEASURED_DEVNET)

    def test_the_local_validator_row_is_the_id_the_cli_writes_and_not_the_v3_one(self) -> None:
        # The row that used to be wrong. `solana-test-validator` hosts memo v3 at
        # MemoSq4gq and the shipped CLI still writes Memo4c2p, so the row follows the CLI.
        self.assertEqual(chain_client.memo_program_id("localnet"), self.MEASURED_DEVNET)
        self.assertNotEqual(chain_client.memo_program_id("localnet"), self.CLI_MEMO)

    def test_every_cluster_the_server_accepts_either_has_a_measurement_or_refuses(self) -> None:
        """No row is a guess: the table holds measured clusters and nothing else.

        `ticketpath/server.py` accepts four clusters. Two of them have a measured id, and the
        other two refuse. The old table carried `mainnet-beta` on the strength of "the CLI's
        shipped program", which the CLI measurement then contradicted, so a row is now
        either measured or absent.
        """
        from ticketpath import server

        measured = {"devnet", "localnet"}
        self.assertEqual(set(chain_client.MEMO_PROGRAMS), measured)
        for cluster in server.CLUSTERS:
            if cluster in measured:
                self.assertEqual(chain_client.memo_program_id(cluster), self.MEASURED_DEVNET)
            else:
                with self.assertRaises(chain_client.UnknownCluster):
                    chain_client.memo_program_id(cluster)

    def test_an_unknown_cluster_refuses_rather_than_guessing(self) -> None:
        for cluster in ("testnet", "mainnet-beta"):
            with self.assertRaises(chain_client.UnknownCluster) as caught:
                chain_client.memo_program_id(cluster)
            message = str(caught.exception)
            self.assertIn(cluster, message)
            self.assertNotIn(self.MEASURED_DEVNET, message)
            self.assertNotIn(self.CLI_MEMO, message)

    def test_the_commitment_for_devnet_names_devnet_s_id(self) -> None:
        commit = chain_client.quote_commit(quote_id="q-test", recommendation=TestQuoteCommitment.FIELDS, cluster="devnet")
        self.assertEqual(commit["instructions"][0]["program"], self.MEASURED_DEVNET)

    def test_the_commitment_for_localnet_names_the_id_the_cli_writes(self) -> None:
        commit = chain_client.quote_commit(quote_id="q-test", recommendation=TestQuoteCommitment.FIELDS, cluster="localnet")
        self.assertEqual(commit["instructions"][0]["program"], self.MEASURED_DEVNET)

    def test_a_commitment_for_an_unknown_cluster_refuses(self) -> None:
        with self.assertRaises(chain_client.UnknownCluster):
            chain_client.quote_commit(quote_id="q-test", recommendation=TestQuoteCommitment.FIELDS, cluster="testnet")

    def test_a_resolved_id_is_what_the_commitment_names_and_none_is_carried_through(self) -> None:
        """The console's path: an id it already resolved, including None for an unmeasured cluster."""
        resolved = chain_client.quote_commit(
            quote_id="q-test", recommendation=TestQuoteCommitment.FIELDS, cluster="testnet",
            memo_program="Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH",
        )
        self.assertEqual(resolved["instructions"][0]["program"], self.MEASURED_DEVNET)
        unmeasured = chain_client.quote_commit(
            quote_id="q-test", recommendation=TestQuoteCommitment.FIELDS, cluster="testnet", memo_program=None
        )
        self.assertIsNone(unmeasured["instructions"][0]["program"])
        self.assertEqual(unmeasured["memoText"], resolved["memoText"])


class TestArtefactVerification(unittest.TestCase):
    FIELDS = TestQuoteCommitment.FIELDS

    def _write(self, record: dict) -> Path:
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(record, handle)
        handle.close()
        return Path(handle.name)

    def test_absent_stays_absent(self) -> None:
        self.assertEqual(chain_client.load_artefact(None)["state"], "absent")
        self.assertEqual(chain_client.load_artefact("/nonexistent/file.json")["state"], "absent")

    def test_a_file_with_a_wrong_hash_is_unverified(self) -> None:
        record = dict(self.FIELDS)
        record.update({"signature": "sig", "slot": 1, "blockTime": 2, "quoteHash": "deadbeef", "cluster": "devnet"})
        self.assertEqual(chain_client.load_artefact(self._write(record))["state"], "unverified")

    def test_a_file_that_verifies_returns_the_slot_and_the_block_time(self) -> None:
        record = dict(self.FIELDS)
        record.update(
            {
                "signature": "5" * 88,
                "slot": 519_646_084,
                "blockTime": 1_760_000_000,
                "quoteHash": chain_client.quote_hash(self.FIELDS),
                # The memo is part of the grammar now: a file with no memo verifies nothing,
                # because the memo is what ties the signature to the quote (feature 2 review).
                "memoText": chain_client.expected_memo(
                    self.FIELDS["quoteId"], chain_client.quote_hash(self.FIELDS)
                ),
                "cluster": "devnet",
            }
        )
        verified = chain_client.load_artefact(self._write(record))
        self.assertEqual(verified["state"], "verified")
        self.assertEqual(verified["slot"], 519_646_084)
        self.assertEqual(verified["blockTime"], 1_760_000_000)

    def test_an_artefact_without_a_memo_program_still_verifies(self) -> None:
        # The proven record was written before the field existed. It is the record, not a
        # candidate: the checker adds a field, it does not demand one retroactively.
        record = dict(self.FIELDS)
        record.update(
            {
                "signature": "5" * 88,
                "slot": 519_646_084,
                "blockTime": 1_760_000_000,
                "quoteHash": chain_client.quote_hash(self.FIELDS),
                # The memo is part of the grammar now: a file with no memo verifies nothing,
                # because the memo is what ties the signature to the quote (feature 2 review).
                "memoText": chain_client.expected_memo(
                    self.FIELDS["quoteId"], chain_client.quote_hash(self.FIELDS)
                ),
                "cluster": "devnet",
            }
        )
        self.assertNotIn("memoProgram", record)
        verified = chain_client.load_artefact(self._write(record))
        self.assertEqual(verified["state"], "verified")
        self.assertIsNone(verified["memoProgram"])

    def test_a_recorded_memo_program_is_read_back_unchanged(self) -> None:
        # Read back, not re-derived: the field records what a run saw, and the loader's table
        # is not allowed to overwrite the observation with today's constant.
        record = dict(self.FIELDS)
        record.update(
            {
                "signature": "5" * 88,
                "slot": 519_646_084,
                "blockTime": 1_760_000_000,
                "quoteHash": chain_client.quote_hash(self.FIELDS),
                "memoText": chain_client.expected_memo(
                    self.FIELDS["quoteId"], chain_client.quote_hash(self.FIELDS)
                ),
                "cluster": "devnet",
                "memoProgram": chain_client.MEMO_PROGRAM_DEVNET,
            }
        )
        verified = chain_client.load_artefact(self._write(record))
        self.assertEqual(verified["state"], "verified")
        self.assertEqual(verified["memoProgram"], chain_client.MEMO_PROGRAM_DEVNET)


if __name__ == "__main__":
    unittest.main()

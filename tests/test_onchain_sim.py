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
        self.assertEqual(commit["instructions"][0]["program"], chain_client.MEMO_PROGRAM_ID)

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
                "cluster": "devnet",
            }
        )
        verified = chain_client.load_artefact(self._write(record))
        self.assertEqual(verified["state"], "verified")
        self.assertEqual(verified["slot"], 519_646_084)
        self.assertEqual(verified["blockTime"], 1_760_000_000)


if __name__ == "__main__":
    unittest.main()

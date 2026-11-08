"""The live half of the v2 wire-format proof, on a local validator, gated on an env var.

    TP_ONCHAIN_V2_LIVE=1 python3 -m unittest tests.test_onchain_v2_live -v

Without the variable every test here is skipped, so `python3 -m unittest discover -s tests -t .`
stays green on a machine that has no Solana toolchain and no time for a validator.

Gated because it starts `solana-test-validator`, deploys a program and sends real
transactions. What it asserts is what `tools/publish_v2.py` claims, each in its own test so a
partial failure says which claim broke:

    (a) InitializeRecord, decoded back: the record's authority is the mint's authority, and
        held_since_unix is 0
    (b) a transfer at band_low is admitted, and the log names the jurisdiction
    (c) a transfer at band_low - 1 is refused with 6021, on its own failed-transaction signature
    (d) a transfer at the cap is admitted; at cap + 1 refused with 6010
    (e) InitializeRecord with policy 2 is refused 6023; a floor above the ceiling refused 6022
    (f) after an admitted transfer, held_since_unix is not 0 and the staged price is 0: the
        hook consumed the staging, so one stage is one sale
    (g) tags 2 and 3 signed by a key that is not the record's authority are refused 6026, and
        the record's bytes do not move. This is the review's measured exploit, re-run

and the tag 4..6 facts, from the second phase on a fresh ledger:

    (4)    a band is published and read back
    (4')   a band signed by a non-authority is refused 6026
    (4'')  a band with low > high is refused 6022
    (4''') a band with sample_n = 0 and refused = 0 is refused 6032
    (4'''') a band whose as_of_slot is above the published slot is refused 6033
    (4v)   refused = 7 is stored and logged as 1
    (5)    a forecast is logged, forward-dated, naming its mint, its band and the rule hash
    (5')   a second forecast for the same as-of is refused 6024 and leaves the first unchanged
    (5'')  a forecast dated a year ago is refused 6029 and creates nothing
    (6)    a score is written; the forecast account's bytes are unchanged
    (6')   a second score for the same forecast is refused 6025
    (6'')  a score below the band's width is refused 6030 and creates nothing
    (6''') a realised price outside the band is scored with covered = 0

The artefact the run writes is asserted to be the dictionary the run returned, and to carry no
key handle and no absolute path: it is git-ignored, and a rule that only holds for the file
you meant to protect is not a rule.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import unittest
from pathlib import Path

from ticketpath.core import base58, forecast_score

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = "TP_ONCHAIN_V2_LIVE"
ARTEFACT = REPO_ROOT / "records" / "onchain-v2.local.json"
FROZEN_DEVNET_PROGRAM = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"

FACE = 1_000_000_000
CAP_BPS = 2500
BAND_LOW = 900_000_000
CEILING = 1_250_000_000


@unittest.skipUnless(
    os.environ.get(GATE) == "1",
    f"set {GATE}=1 to run the local-validator proof (it starts solana-test-validator)",
)
class TestOnchainV2Live(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        if str(REPO_ROOT / "tools") not in sys.path:
            sys.path.insert(0, str(REPO_ROOT / "tools"))
        import publish_v2

        cls.publish_v2 = publish_v2
        # One validator for the class: the whole sequence is one run, and a second run would
        # deploy a second program for no extra evidence.
        cls.artefact = publish_v2.publish(say=lambda line: None)

    # -- (a) -----------------------------------------------------------------

    def test_a_initialize_record_decodes_with_the_payers_authority_and_no_hold(self) -> None:
        proof = self.artefact["proofs"]["a"]
        self.assertTrue(proof["signature"])
        self.assertIsInstance(proof["slot"], int)
        self.assertEqual(proof["record"], self.artefact["record"])
        self.assertEqual(proof["decoded"]["face_value_lamports"], FACE)
        self.assertEqual(proof["decoded"]["cap_bps"], CAP_BPS)
        self.assertEqual(proof["decoded"]["band_low_lamports"], BAND_LOW)
        self.assertEqual(proof["decoded"]["jurisdiction"], "ZZ")
        self.assertEqual(proof["decoded"]["policy"], 0)
        self.assertEqual(proof["decoded"]["status"], 1)
        self.assertEqual(proof["decoded"]["pending_price_lamports"], 0)
        self.assertEqual(
            proof["decoded"]["authority"], self.artefact["payer"], "the authority must be the payer"
        )
        self.assertEqual(proof["decoded"]["held_since_unix"], 0, "a ticket that never moved has no hold")
        self.assertTrue(proof["authorityIsPayer"])
        self.assertTrue(proof["heldSinceIsZero"])
        # The new rule: the mint's own authority signed the create, and the record stores it.
        self.assertEqual(proof["mintAuthority"], self.artefact["payer"])
        self.assertTrue(proof["authorityIsMintAuthority"])

    # -- (b) -----------------------------------------------------------------

    def test_b_a_transfer_at_the_floor_is_admitted_and_the_log_names_the_jurisdiction(self) -> None:
        proof = self.artefact["proofs"]["b"]
        self.assertTrue(proof["admitted"], proof.get("error"))
        self.assertEqual(proof["priceLamports"], BAND_LOW)
        self.assertTrue(proof["jurisdictionInLog"])
        joined = "\n".join(proof["logLines"])
        self.assertIn("ticketpath: cap admitted", joined)
        self.assertIn("jurisdiction=ZZ", joined)
        self.assertIn(f"band_low={BAND_LOW}", joined)
        self.assertIn(f"price={BAND_LOW}", joined)

    # -- (c) -----------------------------------------------------------------

    def test_c_one_lamport_below_the_floor_is_refused_with_6021(self) -> None:
        proof = self.artefact["proofs"]["c"]
        self.assertFalse(proof["admitted"])
        self.assertEqual(proof["priceLamports"], BAND_LOW - 1)
        self.assertEqual(proof["errorCode"], 6021)
        self.assertIn("E_BELOW_FLOOR", proof["error"])
        self.assertIn("0x1785", proof["error"])
        # The failed transaction has its own signature: that is the only form of a refusal a
        # sceptic can look up, and it must not be the admitted transfer's signature.
        self.assertNotEqual(proof["signature"], self.artefact["proofs"]["b"]["signature"])
        self.assertIn("ticketpath: below floor", "\n".join(proof["logLines"]))

    # -- (d) -----------------------------------------------------------------

    def test_d_the_cap_is_inclusive_and_one_lamport_over_is_6010(self) -> None:
        proof = self.artefact["proofs"]["d"]
        self.assertEqual(proof["ceilingLamports"], CEILING)
        self.assertTrue(proof["atCap"]["admitted"], proof["atCap"].get("error"))
        self.assertEqual(proof["atCap"]["priceLamports"], CEILING)
        self.assertFalse(proof["overCap"]["admitted"])
        self.assertEqual(proof["overCap"]["priceLamports"], CEILING + 1)
        self.assertEqual(proof["overCap"]["errorCode"], 6010)
        self.assertIn("E_CAP_EXCEEDED", proof["overCap"]["error"])
        self.assertIn("0x177a", proof["overCap"]["error"])
        self.assertNotEqual(proof["overCap"]["signature"], proof["atCap"]["signature"])
        self.assertIn("ticketpath: cap exceeded", "\n".join(proof["overCap"]["logLines"]))
        self.assertIn("ticketpath: cap admitted", "\n".join(proof["atCap"]["logLines"]))

    # -- (e) -----------------------------------------------------------------

    def test_e_the_two_initialize_record_refusals_are_6023_and_6022(self) -> None:
        proof = self.artefact["proofs"]["e"]
        self.assertFalse(proof["recordCreated"])
        self.assertEqual(proof["policy2"]["policy"], 2)
        self.assertFalse(proof["policy2"]["admitted"])
        self.assertEqual(proof["policy2"]["errorCode"], 6023)
        self.assertIn("E_POLICY_INVALID", proof["policy2"]["error"])

        self.assertFalse(proof["bandUnsatisfiable"]["admitted"])
        self.assertEqual(proof["bandUnsatisfiable"]["errorCode"], 6022)
        self.assertIn("E_BAND_UNSATISFIABLE", proof["bandUnsatisfiable"]["error"])
        self.assertGreater(proof["bandUnsatisfiable"]["bandLowLamports"], CEILING)
        self.assertEqual(proof["bandUnsatisfiable"]["bandLowLamports"], CEILING + 1)

        # Both refusals are on the same mint, which is the point: a refused create leaves no
        # record behind, so the second attempt is the first attempt again and not an update.
        self.assertNotEqual(proof["policy2"]["signature"], proof["bandUnsatisfiable"]["signature"])
        # A different mint, so a different record address: the refusals are not being observed
        # against the record the transfers used.
        self.assertNotEqual(proof["mint"], self.artefact["mint"])
        self.assertNotEqual(proof["record"], self.artefact["record"])

    # -- (f) -----------------------------------------------------------------

    def test_f_an_admitted_transfer_writes_held_since_unix_and_consumes_the_staging(self) -> None:
        proof = self.artefact["proofs"]["f"]
        self.assertNotEqual(proof["heldSinceUnix"], 0, "the hook's clock write did not happen")
        self.assertFalse(proof["heldSinceIsZero"])
        # Fix 2: one stage, one sale. The price that was admitted is cleared, so the next
        # transfer without a new staging is refused 6009.
        self.assertEqual(proof["pendingPriceAfterAdmission"], 0)
        self.assertTrue(proof["stagingConsumed"])
        # The value is the validator's own clock at the slot that executed the transfer, so it
        # agrees with that transaction's block time to within a second or two.
        block_time = self.artefact["proofs"]["b"]["blockTime"]
        self.assertLessEqual(abs(proof["heldSinceUnix"] - block_time), 2)
        at_cap = self.artefact["proofs"]["d"]["atCap"]
        self.assertNotEqual(at_cap["heldSinceUnix"], 0)
        self.assertGreaterEqual(at_cap["heldSinceUnix"], proof["heldSinceUnix"])

    # -- (g) the review's exploit, re-run ------------------------------------

    def test_g_a_non_authority_cannot_stage_a_price_or_freeze_the_ticket(self) -> None:
        proof = self.artefact["proofs"]["g"]
        self.assertNotEqual(proof["nonAuthority"], proof["authority"])
        for name in ("stage", "setStatus"):
            with self.subTest(attempt=name):
                block = proof[name]
                self.assertFalse(block["ok"], name)
                self.assertEqual(block["errorCode"], 6026, name)
                self.assertIn("E_NOT_AUTHORITY", block["error"], name)
                self.assertTrue(block["signature"], name)
                self.assertIsInstance(block["slot"], int, name)
        # Two different failed transactions, neither of them the other's signature.
        self.assertNotEqual(proof["stage"]["signature"], proof["setStatus"]["signature"])
        # And the account itself did not move: the refusal is a fact about the bytes.
        self.assertTrue(proof["recordUnchanged"])
        self.assertEqual(proof["recordSha256Before"], proof["recordSha256AfterStage"])
        self.assertEqual(proof["recordSha256Before"], proof["recordSha256AfterStatus"])
        self.assertEqual(proof["statusAfter"], 1, "the ticket is still transferable")

    def test_the_record_read_at_the_end_matches_the_proofs(self) -> None:
        record = self.artefact["recordAtEnd"]
        self.assertEqual(record["held_since_unix"], self.artefact["proofs"]["d"]["atCap"]["heldSinceUnix"])
        self.assertEqual(record["pending_price_lamports"], CEILING + 1, "the last staged price")
        self.assertEqual(record["authority"], self.artefact["payer"])

    # -- phase two: tags 4..6 -------------------------------------------------

    def test_v2_band_is_published_and_read_back(self) -> None:
        proof = self.artefact["proofs_v2"]["band"]
        self.assertTrue(proof["ok"])
        self.assertTrue(proof["signature"])
        self.assertIsInstance(proof["slot"], int)
        band = proof["band"]
        self.assertEqual(band["version"], 1)
        self.assertEqual((band["low"], band["high"]), (900_000_000, 1_100_000_000))
        self.assertEqual(band["as_of_slot"], proof["asOfSlot"])
        self.assertGreaterEqual(band["published_slot"], band["as_of_slot"])
        self.assertEqual(band["sample_n"], 42)
        self.assertEqual(band["refused"], 0)
        self.assertEqual(band["authority"], self.artefact["payer"])
        self.assertTrue(proof["publishedSlotAtLeastAsOf"])
        self.assertEqual(
            band["model_hash"],
            base58.encode(hashlib.sha256(b"ticketpath-model-v2-local").digest()),
        )

    def test_v2_forecast_is_logged_with_its_mint_band_and_rule(self) -> None:
        proof = self.artefact["proofs_v2"]["forecast"]
        self.assertTrue(proof["ok"])
        forecast = proof["forecast"]
        self.assertEqual(forecast["version"], 1)
        self.assertEqual(forecast["mint"], self.artefact["phase2"]["mint"])
        self.assertEqual((forecast["low"], forecast["high"]), (900_000_000, 1_100_000_000))
        self.assertEqual(forecast["as_of_unix"], self.artefact["phase2"]["asOfUnix"])
        self.assertEqual(forecast["sample_n"], 42)
        self.assertEqual(forecast["authority"], self.artefact["payer"])
        self.assertEqual(
            forecast["scoring_rule_hash"],
            base58.encode(forecast_score.SCORING_RULE_HASH),
        )
        self.assertEqual(proof["scoringRuleHash"], forecast_score.SCORING_RULE_HASH.hex())
        self.assertGreater(proof["createdSlot"], 0)

    def test_v2_the_forecast_is_forward_dated(self) -> None:
        # The defect this fixes: the previous artefact's forecast had as_of 1760000000 and was
        # created at blockTime 1794120524, 394.9 days later, so the account read as a post-hoc
        # claim. The as-of is now ahead of the clock that wrote it, and `LogForecast` refuses a
        # backdated one 6029 (proven below).
        proof = self.artefact["proofs_v2"]["forecast"]
        as_of = proof["forecast"]["as_of_unix"]
        self.assertGreater(as_of, proof["blockTime"], "the forecast must be logged before its as-of")
        self.assertLess(as_of - proof["blockTime"], 3_600)

    def test_v2_a_forecast_dated_a_year_ago_is_refused_6029(self) -> None:
        proof = self.artefact["proofs_v2"]["backdatedForecast"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6029)
        self.assertIn("E_FORECAST_BACKDATED", proof["error"])
        self.assertFalse(proof["forecastCreated"], "a refused log must not consume the PDA")
        self.assertGreater(proof["backdatedBySeconds"], 86_400)
        self.assertNotEqual(proof["signature"], self.artefact["proofs_v2"]["forecast"]["signature"])

    def test_v2_a_score_below_the_band_width_is_refused_6030(self) -> None:
        proof = self.artefact["proofs_v2"]["scoreBelowWidth"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6030)
        self.assertIn("E_SCORE_BELOW_WIDTH", proof["error"])
        self.assertFalse(proof["scoreCreated"])
        self.assertEqual(proof["underscoredBy"], proof["widthMicro"] - 1)
        self.assertEqual(proof["widthMicro"], 200_000_000_000_000)

    def test_v2_a_miss_is_scored_with_covered_zero(self) -> None:
        # The branch no earlier artefact could produce: a realised price outside the band.
        proof = self.artefact["proofs_v2"]["scoreMiss"]
        self.assertTrue(proof["ok"], proof.get("error"))
        self.assertTrue(proof["realisedOutsideBand"])
        score = proof["score"]
        self.assertEqual(score["covered"], 0)
        self.assertEqual(score["realised_lamports"], 1_100_000_001)
        # [900e6, 1.1e9] at one lamport over the top: the width plus ten lamports of penalty.
        self.assertEqual(score["interval_score_micro"], 200_000_010_000_000)
        self.assertEqual(score["interval_score_micro"], proof["expectedIntervalScoreMicro"])
        self.assertFalse(proof["covered"])

    def test_v2_an_empty_band_and_an_as_of_from_the_future_are_refused(self) -> None:
        empty = self.artefact["proofs_v2"]["emptyBand"]
        self.assertFalse(empty["ok"])
        self.assertEqual(empty["errorCode"], 6032)
        self.assertIn("E_BAND_EMPTY", empty["error"])
        self.assertEqual((empty["sampleN"], empty["refused"]), (0, 0))
        self.assertTrue(empty["bandUnchanged"])
        self.assertEqual(empty["bandSha256Before"], empty["bandSha256After"])

        ahead = self.artefact["proofs_v2"]["asOfAhead"]
        self.assertFalse(ahead["ok"])
        self.assertEqual(ahead["errorCode"], 6033)
        self.assertIn("E_AS_OF_AHEAD", ahead["error"])
        self.assertGreater(ahead["asOfSlot"], ahead["publishedSlotBefore"])
        self.assertTrue(ahead["bandUnchanged"])
        self.assertNotEqual(ahead["signature"], empty["signature"])

    def test_v2_refused_is_stored_as_a_flag_not_a_count(self) -> None:
        proof = self.artefact["proofs_v2"]["bandRefusedNormalised"]
        self.assertTrue(proof["ok"], proof.get("error"))
        self.assertEqual(proof["sentRefused"], 7)
        self.assertEqual(proof["storedRefused"], 1)
        self.assertEqual(proof["band"]["refused"], 1)
        self.assertTrue(proof["refusedNormalised"])

    def test_v2_a_second_forecast_for_the_same_as_of_is_refused_6024(self) -> None:
        proof = self.artefact["proofs_v2"]["forecastExists"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6024)
        self.assertIn("E_FORECAST_EXISTS", proof["error"])
        self.assertTrue(proof["forecastUnchanged"])
        self.assertEqual(proof["forecastSha256Before"], proof["forecastSha256After"])
        # It is its own failed transaction, not the successful log's signature.
        self.assertNotEqual(
            proof["signature"], self.artefact["proofs_v2"]["forecast"]["signature"]
        )

    def test_v2_score_is_written_and_the_forecast_bytes_are_unchanged(self) -> None:
        proof = self.artefact["proofs_v2"]["score"]
        self.assertTrue(proof["ok"])
        score = proof["score"]
        self.assertEqual(score["version"], 1)
        self.assertEqual(score["realised_lamports"], 1_000_000_000)
        # [900_000_000, 1_100_000_000] at 1_000_000_000: covered, so the width in micro.
        self.assertEqual(score["interval_score_micro"], 200_000_000_000_000)
        self.assertEqual(score["interval_score_micro"], proof["expectedIntervalScoreMicro"])
        self.assertEqual(score["covered"], 1)
        self.assertTrue(proof["expectedCovered"])
        self.assertEqual(score["scorer"], self.artefact["payer"])
        self.assertTrue(proof["forecastUnchanged"])
        self.assertEqual(proof["forecastSha256Before"], proof["forecastSha256After"])

    def test_v2_the_same_forecast_cannot_be_scored_twice_6025(self) -> None:
        proof = self.artefact["proofs_v2"]["alreadyScored"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6025)
        self.assertIn("E_ALREADY_SCORED", proof["error"])
        self.assertTrue(proof["scoreUnchanged"])
        self.assertEqual(proof["scoreSha256Before"], proof["scoreSha256After"])
        self.assertNotEqual(proof["signature"], self.artefact["proofs_v2"]["score"]["signature"])

    def test_v2_a_band_signed_by_a_non_authority_is_refused_6026(self) -> None:
        proof = self.artefact["proofs_v2"]["nonAuthority"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6026)
        self.assertIn("E_NOT_AUTHORITY", proof["error"])
        self.assertNotEqual(proof["nonAuthority"], proof["authority"])
        self.assertTrue(proof["bandUnchanged"])
        self.assertEqual(proof["bandSha256Before"], proof["bandSha256After"])

    def test_v2_a_band_with_low_above_high_is_refused_6022(self) -> None:
        proof = self.artefact["proofs_v2"]["unsatisfiableBand"]
        self.assertFalse(proof["ok"])
        self.assertEqual(proof["errorCode"], 6022)
        self.assertIn("E_BAND_UNSATISFIABLE", proof["error"])
        self.assertGreater(proof["low"], proof["high"])
        self.assertTrue(proof["bandUnchanged"])
        self.assertEqual(proof["bandSha256Before"], proof["bandSha256After"])

    def test_v2_phase_two_uses_the_same_program_and_a_fresh_ledger(self) -> None:
        phase2 = self.artefact["phase2"]
        self.assertEqual(phase2["programId"], self.artefact["programId"])
        self.assertEqual(
            phase2["program"]["sha256"], self.artefact["program"]["sha256"]
        )
        self.assertNotEqual(phase2["ledger"], self.artefact["validator"]["ledger"])
        self.assertNotEqual(phase2["mint"], self.artefact["mint"])
        self.assertEqual(phase2["scoringRule"], forecast_score.SCORING_RULE)
        self.assertEqual(phase2["scoringRuleHash"], forecast_score.SCORING_RULE_HASH.hex())
        for name, step in self.artefact["steps_v2"].items():
            with self.subTest(step=name):
                self.assertTrue(step["signature"], name)
                self.assertIsInstance(step["slot"], int, name)
                self.assertTrue(step["wallClock"].endswith("Z"), name)

    # -- the artefact itself --------------------------------------------------

    def test_the_artefact_is_local_only_and_never_names_the_frozen_program(self) -> None:
        self.assertEqual(self.artefact["cluster"], "localnet")
        self.assertIs(self.artefact["localOnly"], True)
        self.assertNotEqual(self.artefact["programId"], FROZEN_DEVNET_PROGRAM)
        self.assertEqual(self.artefact["program"]["path"], "programs/cap_hook/target/deploy/cap_hook.so")
        self.assertEqual(len(self.artefact["program"]["sha256"]), 64)

    def test_the_written_artefact_is_what_the_run_returned(self) -> None:
        self.assertTrue(ARTEFACT.exists(), "tools/publish_v2.py must write the artefact")
        on_disk = json.loads(ARTEFACT.read_text(encoding="utf-8"))
        self.assertEqual(on_disk, self.artefact)

    def test_the_artefact_carries_no_key_handle_and_no_absolute_path(self) -> None:
        offenders = []

        def walk(value, where: str) -> None:
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{where}.{key}")
            elif isinstance(value, list):
                for position, item in enumerate(value):
                    walk(item, f"{where}[{position}]")
            elif isinstance(value, str):
                if value.startswith("/") or value.startswith("~"):
                    offenders.append(f"{where} is an absolute path")
                if "keypair" in value.lower():
                    offenders.append(f"{where} names a keypair")

        walk(self.artefact, "artefact")
        self.assertEqual(offenders, [], "the artefact would carry something it must not")

    def test_every_step_has_a_signature_a_slot_and_a_clock(self) -> None:
        for name, step in self.artefact["steps"].items():
            with self.subTest(step=name):
                self.assertTrue(step["signature"], name)
                self.assertIsInstance(step["slot"], int, name)
                self.assertTrue(step["wallClock"].endswith("Z"), name)


if __name__ == "__main__":
    unittest.main()

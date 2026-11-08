"""The flip tax proof tool's pure parts: the supplied age, the leg table, the builder's shapes.

Nothing here starts a validator, opens a keypair or touches a socket. The validator legs live
in `tools/flip_tax_proof.py` and run only when the operator runs that tool; what is checked
here is every claim the tool makes *before* it talks to a chain, so a leg that fails on the
validator is a fact about the chain and not a typo in a table.

Run from the repository root with `python3 -m unittest tests.test_flip_tax_proof -v`.
"""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import artist_fee_proof as afp  # noqa: E402
import devnet_publish as dp  # noqa: E402
import flip_tax_proof as ftp  # noqa: E402
from market_swarm import artist_fee as af  # noqa: E402
from market_swarm import flip_tax as ft  # noqa: E402


#: Distinct 32-byte base58 addresses: a seller, an artist, an issuer and the accounts a sale
#: names. Deterministic byte runs, so a failure names an obvious value and no two collide.
def address(offset: int) -> str:
    return dp.base58.encode(bytes((offset + index) % 256 for index in range(32)))


SELLER = address(0)
ARTIST = address(32)
ISSUER = address(64)
MINT = address(96)
RECORD = address(128)
EXTRA = address(160)
SOURCE = address(192)
DESTINATION = address(224)
PROGRAM = dp.base58.encode(bytes(range(255, 223, -1)))


def a_stage(price: int = 1_000_000_000) -> dp.Instruction:
    return ftp.ix_stage(authority=ISSUER, record=RECORD, mint=MINT, program_id=PROGRAM, price=price)


def a_move() -> dp.Instruction:
    return ftp.ix_move(source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER,
                       record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA)


def build(key: str, *, seller: str = SELLER) -> tuple:
    return ftp.build_leg(key=key, stage=a_stage(ftp.LEG_PRICES[key]), move=a_move(),
                         seller=seller, artist_wallet=ARTIST, now_unix=ftp.REFERENCE_NOW)


class TestSuppliedAge(unittest.TestCase):
    """The one number the tool invents, and the fact that it reads back as the hold it names."""

    def test_a_supplied_hold_reads_back_as_itself(self) -> None:
        for held in (0, 1, 3_540, 3_600, 2_591_999, 2_592_000, 5_000_000):
            with self.subTest(held=held):
                since = ftp.supplied_held_since(ftp.REFERENCE_NOW, held)
                self.assertEqual(since, ftp.REFERENCE_NOW - held)
                self.assertEqual(ft.hold_seconds(since, ftp.REFERENCE_NOW), held)

    def test_the_boundaries_are_the_operators_clocks(self) -> None:
        self.assertEqual(ftp.LEG_HELD_SECONDS["2a"], 59 * 60)
        self.assertEqual(ftp.LEG_HELD_SECONDS["2a"], 3_540)
        self.assertEqual(ftp.LEG_HELD_SECONDS["2b"], 60 * 60)
        self.assertEqual(ftp.LEG_HELD_SECONDS["2b"], ft.DEFAULT_FULL_HOLD_SECONDS)
        self.assertEqual(ftp.LEG_HELD_SECONDS["3"], 30 * 24 * 60 * 60)
        self.assertEqual(ftp.LEG_HELD_SECONDS["3"], ft.DEFAULT_ZERO_HOLD_SECONDS)

    def test_the_two_boundary_sides_are_one_second_apart_and_price_the_same(self) -> None:
        short = ft.DEFAULT_SCHEDULE.bps_for(ftp.LEG_HELD_SECONDS["2a"])
        exact = ft.DEFAULT_SCHEDULE.bps_for(ftp.LEG_HELD_SECONDS["2b"])
        self.assertEqual(short, exact)
        self.assertEqual(short, ft.DEFAULT_FULL_BPS)

    def test_a_hold_that_cannot_be_supplied_is_refused(self) -> None:
        for now, held in ((100, 3_540), (ftp.REFERENCE_NOW, -1), (ftp.REFERENCE_NOW, True),
                          (ftp.REFERENCE_NOW, "3540")):
            with self.subTest(now=now, held=held):
                with self.assertRaises(ftp.ProofError):
                    ftp.supplied_held_since(now, held)

    def test_an_unknown_hold_is_not_a_time_and_pays_the_full_rate(self) -> None:
        # `0` is what the program writes at InitializeRecord. Read as 1970 it would be about
        # 1.8 billion seconds old and worth 0%; read as unknown it pays the full rate.
        self.assertIsNone(ft.hold_seconds(ft.UNKNOWN_HOLD, ftp.REFERENCE_NOW))
        assessed = ft.assess(price_lamports=1_000_000_000, held_since_unix=ft.UNKNOWN_HOLD,
                             now_unix=ftp.REFERENCE_NOW)
        self.assertEqual((assessed.held_seconds, assessed.bps, assessed.lamports),
                         (None, ft.DEFAULT_FULL_BPS, 150_000_000))
        self.assertFalse(assessed.known)

    def test_the_table_row_for_the_unknown_hold_supplies_nothing(self) -> None:
        self.assertIsNone(ftp.LEG_HELD_SECONDS["8"])


class TestTheLegTable(unittest.TestCase):
    """The prices, the ages and the money each row is expected to move, from the module."""

    def test_the_prices_are_the_briefs(self) -> None:
        self.assertEqual(ftp.FACE, 1_000_000_000)
        self.assertEqual(ftp.CAP_BPS, 2_500)
        self.assertEqual(ftp.CEILING, 1_250_000_000)
        self.assertEqual(ftp.LEG_PRICES["1"], ftp.FACE)
        self.assertEqual(ftp.LEG_PRICES["7"], ftp.CEILING + 1)
        self.assertEqual(ftp.LEG_PRICES["5a"], 6)
        self.assertEqual(ftp.LEG_PRICES["5b"], 7)
        self.assertEqual(ftp.LEG_PRICES["5c"], 19)

    def test_the_artist_fees_are_the_modules_numbers(self) -> None:
        self.assertEqual(ftp.planned_fees(), {
            "1": 50_000_000,
            "2a": 50_000_000,
            "2b": 50_000_000,
            "3": 50_000_000,
            "4": 50_000_000,
            "5a": 0,
            "5b": 0,
            "5c": 0,
            "6": 50_000_000,
            "7": 62_500_000,
            "8": 50_000_000,
        })

    def test_the_flip_taxes_are_the_modules_numbers(self) -> None:
        self.assertEqual(ftp.planned_taxes(), {
            "1": 150_000_000,
            "2a": 150_000_000,
            "2b": 150_000_000,
            "3": 0,
            "4": 150_000_000,
            "5a": 0,
            "5b": 1,
            "5c": 2,
            "6": 150_000_000,
            "7": 187_500_000,
            "8": 150_000_000,
        })

    def test_the_two_boundary_sides_both_pay_the_full_hundred_and_fifty_million(self) -> None:
        self.assertEqual(ftp.planned_taxes()["2a"], 150_000_000)
        self.assertEqual(ftp.planned_taxes()["2b"], 150_000_000)
        self.assertEqual(ftp.planned_taxes()["2a"] * 2 + ftp.planned_fees()["2a"],
                         350_000_000)

    def test_thirty_days_pays_no_tax_and_still_pays_the_fee(self) -> None:
        self.assertEqual(ftp.planned_taxes()["3"], 0)
        self.assertEqual(ftp.planned_fees()["3"], 50_000_000)

    def test_price_nineteen_pays_two_lamports_and_not_zero(self) -> None:
        # The brief's example assumed 19 lamports builds no tax leg. It does: 19 * 1500 // 10_000
        # is 2. The row is kept so the correction is a number in the report, not a footnote.
        self.assertEqual(ftp.planned_taxes()["5c"], 2)
        self.assertNotEqual(ftp.planned_taxes()["5c"], 0)
        self.assertEqual(ftp.planned_fees()["5c"], 0)
        self.assertEqual(len(build("5c")), 3)

    def test_the_pair_that_straddles_the_floor_is_six_and_seven(self) -> None:
        self.assertEqual(ftp.planned_taxes()["5a"], 0)
        self.assertEqual(ftp.planned_taxes()["5b"], 1)
        self.assertEqual((ftp.LEG_PRICES["5a"], ftp.LEG_PRICES["5b"]), (6, 7))

    def test_the_underfunded_seller_can_pay_the_fee_and_cannot_pay_the_tax_with_it(self) -> None:
        fee = ftp.planned_fees()["6"]
        tax = ftp.planned_taxes()["6"]
        self.assertGreater(ftp.SELLER_UNDERFUNDED_LAMPORTS, fee)
        self.assertLess(ftp.SELLER_UNDERFUNDED_LAMPORTS, fee + tax)
        self.assertGreater(ftp.SELLER_UNDERFUNDED_LAMPORTS, 2 * 5_000)
        self.assertEqual((fee + tax) - ftp.SELLER_UNDERFUNDED_LAMPORTS, 100_000_000)

    def test_every_row_has_a_price_an_age_a_count_and_a_title(self) -> None:
        self.assertEqual(set(ftp.LEG_PRICES), set(ftp.LEG_HELD_SECONDS))
        self.assertEqual(set(ftp.LEG_PRICES), set(ftp.LEG_INSTRUCTION_COUNTS))
        self.assertEqual(set(ftp.LEG_KEYS) | ftp.COMPUTED_ONLY, set(ftp.LEG_PRICES))
        self.assertEqual(len(set(ftp.LEG_KEYS)), len(ftp.LEG_KEYS))
        for key in ftp.LEG_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, ftp.LEG_TITLES)
        self.assertTrue(ftp.COMPUTED_ONLY <= set(ftp.LEG_PRICES))

    def test_the_computed_only_row_is_the_briefs_example_and_nothing_else(self) -> None:
        self.assertEqual(ftp.COMPUTED_ONLY, frozenset({"5c"}))

    def test_the_sale_mint_has_a_ticket_for_every_leg_that_moves_one(self) -> None:
        moving = ["1", "2a", "2b", "3", "4", "5a", "5b"]
        self.assertEqual(len(moving), 7)
        self.assertGreaterEqual(ftp.TICKETS_SALE, len(moving))
        self.assertEqual(ftp.TICKETS_FRESH, 1)
        self.assertEqual(ftp.TICKETS_UNDERFUNDED, 1)

    def test_the_two_signature_transaction_fee_is_what_every_delta_is_stated_against(self) -> None:
        self.assertEqual(ftp.TRANSACTION_FEE, 10_000)
        self.assertEqual(ftp.TRANSACTION_FEE, 2 * 5_000)

    def test_leg_ones_seller_delta_is_the_two_payments_plus_the_transaction_fee(self) -> None:
        paid = ftp.planned_fees()["1"] + ftp.planned_taxes()["1"]
        self.assertEqual(paid, 200_000_000)
        self.assertEqual(paid + ftp.TRANSACTION_FEE, 200_010_000)
        # The brief states this delta as -(200,000,010,000): three digits too long, and larger
        # than the 3,000,000,000 lamports the seller is funded with. The tool asserts the
        # measured number and says the correction out loud; pinned here so nobody "fixes" the
        # tool back to a number no balance could produce.
        self.assertGreater(200_000_010_000, 3_000_000_000)
        source = (REPO_ROOT / "tools" / "flip_tax_proof.py").read_text(encoding="utf-8")
        self.assertIn("200,000,010,000", source)
        self.assertIn("-200_010_000", source)


class TestTheBuildersShapes(unittest.TestCase):
    """What `flip_tax.sale_instructions` actually returns for each row, instruction by instruction."""

    def test_every_instruction_count_is_what_the_builder_produces(self) -> None:
        for key in ftp.LEG_PRICES:
            with self.subTest(key=key):
                self.assertEqual(len(build(key)), ftp.LEG_INSTRUCTION_COUNTS[key])

    def test_a_taxed_sale_is_stage_fee_tax_move(self) -> None:
        self.assertEqual([instruction.program_id for instruction in build("1")],
                         [PROGRAM, dp.SYSTEM_PROGRAM, dp.SYSTEM_PROGRAM, dp.TOKEN_2022_PROGRAM])

    def test_the_two_payments_are_the_fee_then_the_tax(self) -> None:
        self.assertEqual(ftp.system_transfers(build("1")), [50_000_000, 150_000_000])
        self.assertEqual(ftp.system_transfers(build("2a")), [50_000_000, 150_000_000])
        self.assertEqual(ftp.system_transfers(build("2b")), [50_000_000, 150_000_000])

    def test_both_payments_go_to_the_artist(self) -> None:
        destinations = [meta.pubkey
                        for instruction in build("1")
                        if instruction.program_id == dp.SYSTEM_PROGRAM
                        for meta in instruction.accounts[1:2]]
        self.assertEqual(destinations, [ARTIST, ARTIST])

    def test_thirty_days_drops_the_tax_leg_and_keeps_the_fee(self) -> None:
        sale = build("3")
        self.assertEqual(len(sale), 3)
        self.assertEqual([instruction.program_id for instruction in sale],
                         [PROGRAM, dp.SYSTEM_PROGRAM, dp.TOKEN_2022_PROGRAM])
        self.assertEqual(ftp.system_transfers(sale), [50_000_000])

    def test_the_rounding_pair_differs_by_exactly_the_tax_leg(self) -> None:
        dust = build("5a")
        penny = build("5b")
        self.assertEqual(len(dust), 2)
        self.assertEqual(len(penny), 3)
        self.assertEqual(ftp.system_transfers(dust), [])
        self.assertEqual(ftp.system_transfers(penny), [1])

    def test_the_toggled_off_row_is_the_artist_fee_builders_own_output(self) -> None:
        # Row 4 is the path an event with no `flip_tax` block takes, so it must be byte-identical
        # to what the artist fee builder returns: nothing about the tax is anywhere in it.
        mine = build("4")
        theirs = af.sale_instructions(
            stage=a_stage(), move=a_move(), seller=SELLER, artist_wallet=ARTIST,
            price_lamports=ftp.LEG_PRICES["4"], fee_bps=ftp.ARTIST_FEE_BPS,
        )
        self.assertEqual(len(mine), len(theirs))
        for left, right in zip(mine, theirs):
            with self.subTest(instruction=left.program_id):
                self.assertEqual(left.program_id, right.program_id)
                self.assertEqual(bytes(left.data), bytes(right.data))
                self.assertEqual(
                    [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in left.accounts],
                    [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in right.accounts],
                )

    def test_the_unknown_hold_is_charged_the_full_rate_by_the_builder(self) -> None:
        sale = build("8")
        self.assertEqual(len(sale), 4)
        self.assertEqual(ftp.system_transfers(sale), [50_000_000, 150_000_000])

    def test_a_disabled_policy_is_refused_before_anything_is_built(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.sale_instructions(
                stage=a_stage(), move=a_move(), seller=SELLER,
                policy=ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled=False),
                price_lamports=ftp.FACE, held_since_unix=ftp.REFERENCE_NOW - 3_540,
                now_unix=ftp.REFERENCE_NOW,
                artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST,
                                              fee_bps=ftp.ARTIST_FEE_BPS),
            )
        self.assertIn("enabled", str(caught.exception))

    def test_a_zero_price_and_a_self_paying_sale_are_refused(self) -> None:
        policy = ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled=True)
        with self.subTest(case="zero price"):
            with self.assertRaises(ft.FlipTaxError):
                ft.sale_instructions(stage=a_stage(0), move=a_move(), seller=SELLER,
                                     policy=policy, price_lamports=0,
                                     held_since_unix=ftp.REFERENCE_NOW - 3_540,
                                     now_unix=ftp.REFERENCE_NOW)
        with self.subTest(case="the artist is the seller"):
            with self.assertRaises(ft.FlipTaxError):
                ft.sale_instructions(stage=a_stage(), move=a_move(), seller=ARTIST,
                                     policy=policy, price_lamports=ftp.FACE,
                                     held_since_unix=ftp.REFERENCE_NOW - 3_540,
                                     now_unix=ftp.REFERENCE_NOW)

    def test_the_supplied_age_is_what_changes_the_leg_count(self) -> None:
        # Same price, same everything: only the age moves, and the tax leg appears or not.
        now = ftp.REFERENCE_NOW
        enabled = ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled=True)

        def at(held: int) -> tuple:
            return ft.sale_instructions(
                stage=a_stage(), move=a_move(), seller=SELLER, policy=enabled,
                price_lamports=6, held_since_unix=now - held, now_unix=now,
                artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=500),
            )

        self.assertEqual(len(at(3_540)), 2)
        self.assertEqual(len(at(2_592_000)), 2)  # price 6 pays 0 either way: the floor, not the age
        self.assertEqual(len(build("5b")), 3)     # price 7 with the full rate buys a leg
        self.assertEqual([ft.assess(price_lamports=6, held_since_unix=now - held, now_unix=now).lamports
                          for held in (0, 3_540, 2_592_000)], [0, 0, 0])


class TestTheSystemTransferReader(unittest.TestCase):
    """The helper that says how many lamports of tax are in the transaction, and where."""

    def test_it_reads_the_lamports_out_of_each_transfer(self) -> None:
        legs = [
            a_stage(),
            af.system_transfer_instruction(source=SELLER, destination=ARTIST, lamports=50_000_000),
            af.system_transfer_instruction(source=SELLER, destination=ARTIST, lamports=150_000_000),
            a_move(),
        ]
        self.assertEqual(ftp.system_transfers(legs), [50_000_000, 150_000_000])

    def test_a_sale_with_no_payment_has_no_system_legs(self) -> None:
        self.assertEqual(ftp.system_transfers(build("5a")), [])

    def test_a_system_instruction_that_is_not_a_transfer_is_refused(self) -> None:
        bogus = dp.Instruction(program_id=dp.SYSTEM_PROGRAM, accounts=(), data=b"\x01\x00\x00\x00")
        with self.assertRaises(ftp.ProofError):
            ftp.system_transfers([bogus])
        short = dp.Instruction(program_id=dp.SYSTEM_PROGRAM, accounts=(), data=b"\x02\x00")
        with self.assertRaises(ftp.ProofError):
            ftp.system_transfers([short])


def a_stub_proof(*, failures: list[str] | None = None) -> SimpleNamespace:
    """A run's worth of entries with no cluster behind them, for the writers to render."""
    results = [
        ftp.leg_entry(
            key=key,
            title=ftp.LEG_TITLES[key],
            checks=afp.Checks(),
            measured={"price": ftp.LEG_PRICES[key], "flip_tax": ftp.planned_taxes()[key]},
            sent=None if key in ftp.COMPUTED_ONLY else {
                "signature": f"signature-{key}", "signers": [SELLER, ISSUER],
                "instructions": ftp.LEG_INSTRUCTION_COUNTS[key], "ok": True,
                "error": {"text": "no error", "index": None, "code": None},
                "failed_log": "none", "logs": [],
            },
            note=f"note for {key}",
        )
        for key in ftp.LEG_KEYS
    ]
    return SimpleNamespace(
        validator_version="solana-test-validator 4.3.2 (src:devbuild; feat:4063377879)",
        url="http://127.0.0.1:20000",
        port_closed=True,
        program_id=PROGRAM,
        so_sha=ftp.SO_SHA256,
        issuer=ISSUER,
        artist=ARTIST,
        codes={"CapExceeded": 6010},
        mints={"sale": {"mint": MINT, "record": RECORD, "seller": SELLER, "buyer": DESTINATION,
                        "record_at_birth": {"face_value_lamports": ftp.FACE, "held_since_unix": 0}}},
        results=results,
        snapshots=[],
        leg8_records={"moved": {"held_since_unix": 1_760_000_000},
                      "fresh_before_sale": {"held_since_unix": 0}},
        failed=failures or [],
    )


class TestTheReportNamesEveryLeg(unittest.TestCase):
    """The report is a durable output: a leg missing from it is a leg nobody can read later."""

    def test_the_report_carries_a_section_for_every_leg(self) -> None:
        text = ftp.report_text(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                              total=len(ftp.LEG_KEYS), failures=[])
        for key in ftp.LEG_KEYS:
            with self.subTest(key=key):
                self.assertIn(f"### Leg {key} — {ftp.LEG_TITLES[key]}", text)
                self.assertIn(ftp.LEG_TITLES[key], text)

    def test_the_report_states_what_is_measured_and_what_is_supplied(self) -> None:
        text = ftp.report_text(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                              total=len(ftp.LEG_KEYS), failures=[])
        self.assertIn("## What is measured and what is supplied", text)
        for phrase in ("supplied by this tool", "wall clock", "--warp-slot 6480000",
                       "the leg and the money", "rate-for-age", "unit tests"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_the_report_carries_the_leg_table_with_every_row(self) -> None:
        text = ftp.report_text(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                              total=len(ftp.LEG_KEYS), failures=[])
        for key in ftp.LEG_PRICES:
            with self.subTest(key=key):
                self.assertIn(f"\n| {key} | {ftp.LEG_PRICES[key]:,} |", text)
        self.assertIn("## The leg table", text)
        self.assertIn("## The record is the clock", text)

    def test_the_report_says_which_cluster_it_ran_on_and_that_the_port_closed(self) -> None:
        text = ftp.report_text(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                              total=len(ftp.LEG_KEYS), failures=[])
        self.assertIn("LOCAL `solana-test-validator`", text)
        self.assertIn("closed after the run: **True**", text)
        self.assertIn(ftp.SO_SHA256, text)

    def test_the_report_states_the_correction_to_the_briefs_seller_delta(self) -> None:
        # Written by the report and the leg's note, so a reader of the durable output sees the
        # brief's number and the measured one side by side.
        text = ftp.report_text(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                              total=len(ftp.LEG_KEYS), failures=[])
        self.assertIn("200,000,010,000", text)
        self.assertIn("200,010,000", text)

    def test_a_failure_is_named_rather_than_hidden(self) -> None:
        text = ftp.report_text(a_stub_proof(), passed=0, total=len(ftp.LEG_KEYS),
                              failures=["leg 3: the tax was not 0"])
        self.assertIn("**FAIL 0/11**", text)
        self.assertIn("leg 3: the tax was not 0", text)

    def test_the_report_writes_to_a_path_it_is_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "REPORT.md"
            ftp.write_report(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                             total=len(ftp.LEG_KEYS), failures=[], path=path)
            self.assertTrue(path.exists())
            self.assertIn("# The flip tax at checkout", path.read_text(encoding="utf-8"))

    def test_the_measurements_carry_every_leg_and_the_tables(self) -> None:
        proof = a_stub_proof()
        measured = ftp.measurements(proof, passed=len(ftp.LEG_KEYS),
                                    total=len(ftp.LEG_KEYS), failures=[])
        self.assertEqual([leg["leg"] for leg in measured["legs"]], list(ftp.LEG_KEYS))
        self.assertEqual(measured["planned_taxes"], ftp.planned_taxes())
        self.assertEqual(measured["planned_fees"], ftp.planned_fees())
        self.assertEqual(measured["constants"]["ceiling_lamports"], ftp.CEILING)
        self.assertEqual(measured["constants"]["record_len"], ft.RECORD_LEN)
        self.assertEqual(measured["constants"]["schedule"], ft.DEFAULT_SCHEDULE.to_dict())
        self.assertIn("supplied", measured["measured_and_supplied"])
        self.assertEqual(measured["result"]["total"], len(ftp.LEG_KEYS))

    def test_the_measurements_write_to_a_path_they_are_given(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "measurements.json"
            ftp.write_measurements(a_stub_proof(), passed=len(ftp.LEG_KEYS),
                                   total=len(ftp.LEG_KEYS), failures=[], path=path)
            self.assertTrue(path.exists())
            self.assertIn('"legs"', path.read_text(encoding="utf-8"))


class TestTheToolRefusesAWrongSoHash(unittest.TestCase):
    """The program is an input: a binary this proof cannot name stops the run before a boot."""

    def test_the_right_digest_passes_through(self) -> None:
        self.assertEqual(ftp.verify_so_hash(ftp.SO_SHA256), ftp.SO_SHA256)

    def test_a_wrong_digest_is_refused_and_both_hashes_are_named(self) -> None:
        with self.assertRaises(ftp.ProofError) as caught:
            ftp.verify_so_hash("0" * 64)
        self.assertIn(ftp.SO_SHA256, str(caught.exception))
        self.assertIn("0" * 64, str(caught.exception))

    def test_it_is_the_same_binary_the_artist_fee_proof_describes(self) -> None:
        self.assertEqual(ftp.SO_SHA256, afp.SO_SHA256)

    def test_the_digest_comes_from_the_files_own_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            present = Path(tmp) / "cap_hook.so"
            present.write_bytes(b"not the program")
            self.assertEqual(ftp.so_digest(present),
                             hashlib.sha256(b"not the program").hexdigest())
            self.assertEqual(ftp.so_digest(Path(tmp) / "absent.so"), "missing")
            with self.assertRaises(ftp.ProofError):
                ftp.verify_so_hash(ftp.so_digest(present))


class TestWorkDirAndLock(unittest.TestCase):
    """Its own work directory and its own lock, so two tools and two runs cannot collide."""

    def test_the_work_directory_is_the_tools_own(self) -> None:
        self.assertEqual(ftp.WORK, REPO_ROOT / "tmp" / "flip-tax")
        self.assertEqual(ftp.KEYS, ftp.WORK / "keys")
        self.assertEqual(ftp.LEDGER, ftp.WORK / "ledger")
        self.assertEqual(ftp.MEASUREMENTS, ftp.WORK / "measurements.json")
        self.assertEqual(ftp.REPORT, ftp.WORK / "REPORT.md")

    def test_the_lock_is_outside_the_directory_that_is_wiped_at_boot(self) -> None:
        self.assertEqual(ftp.LOCK_PATH, REPO_ROOT / "tmp" / "flip-tax.lock")
        # Containment, not a string prefix: `tmp/flip-tax.lock` shares a prefix with `tmp/flip-tax`
        # and is still outside it, which is the whole point of naming it that way.
        self.assertNotIn(ftp.WORK, ftp.LOCK_PATH.parents)
        self.assertNotEqual(ftp.WORK, afp.WORK)
        self.assertNotEqual(ftp.LOCK_PATH, afp.LOCK_PATH)

    def test_the_program_paths_are_the_ones_the_crate_publishes(self) -> None:
        self.assertEqual(ftp.SO_PATH, REPO_ROOT / "programs" / "cap_hook" / "target"
                         / "deploy" / "cap_hook.so")
        self.assertEqual(ftp.PROGRAM_KEYPAIR.parent, ftp.SO_PATH.parent)


class TestTheHarnessIsImportedNotCopied(unittest.TestCase):
    """One set of encoders, one `Checks`, one validator teardown: the harness, by identity."""

    def test_every_chain_piece_is_the_artist_fee_proofs_object(self) -> None:
        for name in ("LocalCluster", "Checks", "ProofError", "ix_init_extra_metas",
                     "ix_init_record", "ix_move", "ix_stage", "resolve_signers", "read_record",
                     "transaction_meta", "get_balance", "token_amount", "load_program_codes",
                     "free_block", "port_is_closed", "assert_loopback", "describe_error"):
            with self.subTest(name=name):
                self.assertIs(getattr(ftp, name), getattr(afp, name))

    def test_it_does_not_restate_the_shared_classes(self) -> None:
        source = (REPO_ROOT / "tools" / "flip_tax_proof.py").read_text(encoding="utf-8")
        self.assertIn("import artist_fee_proof as afp", source)
        for forbidden in ("class LocalCluster", "class Checks", "def ix_stage",
                          "def ix_move", "def ix_init_record", "def ix_init_extra_metas"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_it_does_not_subclass_the_proof_whose_lifecycle_uses_the_other_work_dir(self) -> None:
        # `afp.Proof` binds KEYS and WORK in its own __init__/boot/make_mint/send, so a subclass
        # would write this run's keys under tmp/artist-fee/. The lifecycle is restated instead.
        source = (REPO_ROOT / "tools" / "flip_tax_proof.py").read_text(encoding="utf-8")
        self.assertNotIn("(afp.Proof)", source)
        self.assertIn("class Proof:", source)


class TestTheToolsOwnLimits(unittest.TestCase):
    """What the source itself must never grow: a build, a public cluster, a clone, a git write."""

    SOURCE = (REPO_ROOT / "tools" / "flip_tax_proof.py").read_text(encoding="utf-8")

    def test_the_program_is_an_asserted_input_and_never_rebuilt(self) -> None:
        self.assertIn(ftp.SO_SHA256, self.SOURCE)
        self.assertIn("verify_so_hash(so_digest(SO_PATH))", self.SOURCE)
        for forbidden in ("cargo-build-sbf", "cargo build", "cargo_build"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_no_public_cluster_anywhere_in_the_file(self) -> None:
        for forbidden in ("api.devnet.solana.com", "api.mainnet-beta.solana.com",
                          "request_airdrop", "solana airdrop", "faucet.solana.com"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_it_never_clones_a_program_and_never_names_a_devnet_url(self) -> None:
        for forbidden in ("--clone", "--url devnet", "devnet.solana"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_it_writes_no_git_state(self) -> None:
        for forbidden in ("git add", "git commit", "git push", 'subprocess.run(["git"'):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_every_run_has_a_deadline_and_the_validator_teardown_is_the_harness_one(self) -> None:
        self.assertIn("--deadline", self.SOURCE)
        self.assertIn("default=600.0", self.SOURCE)
        self.assertIs(ftp.LocalCluster, afp.LocalCluster)
        self.assertIn("port_is_closed(proof.port)", self.SOURCE)
        self.assertIn("validator.stop()", self.SOURCE)

    def test_it_never_opens_a_keypair_itself(self) -> None:
        # Keys are opened only by `tools/solana_sign.py` and `solana-keygen`, in child processes.
        for forbidden in ("read_text()", "json.load"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)


class TestLoopbackRefusal(unittest.TestCase):
    """The tool refuses any RPC that is not this machine's own validator."""

    def test_the_check_is_the_harness_one(self) -> None:
        self.assertIs(ftp.assert_loopback, afp.assert_loopback)

    def test_loopback_is_accepted(self) -> None:
        for url in ("http://127.0.0.1:8899", "http://localhost:20000", "http://[::1]:9999"):
            with self.subTest(url=url):
                self.assertEqual(ftp.assert_loopback(url), url)

    def test_a_public_cluster_is_refused(self) -> None:
        for url in ("https://api.devnet.solana.com", "https://api.mainnet-beta.solana.com",
                    "http://10.0.0.5:8899", "http://127.0.0.1", "", None, "devnet"):
            with self.subTest(url=url):
                with self.assertRaises(ftp.ProofError):
                    ftp.assert_loopback(url)

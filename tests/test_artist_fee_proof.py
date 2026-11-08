"""The proof tool's pure parts: the v2 wire, the record decode, the signer order, the numbers.

Nothing here starts a validator, opens a keypair or touches a socket. The validator legs live
in `tools/artist_fee_proof.py` and run only when the operator runs that tool; what is checked
here is every claim the tool makes *before* it talks to a chain, so a leg that fails on the
validator is a fact about the chain and not a typo in an encoder.

Run from the repository root with `python3 -m unittest tests.test_artist_fee_proof -v`.
"""

from __future__ import annotations

import unittest
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
for entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import artist_fee_proof as afp  # noqa: E402
import devnet_publish as dp  # noqa: E402
from market_swarm import artist_fee as af  # noqa: E402

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
BLOCKHASH = address(11)

PRICE = 1_000_000_000
BPS = 500


class TestStageWire(unittest.TestCase):
    """Tag 2: nine bytes, three accounts, and the authority signs rather than paying."""

    def instruction(self, price: int = PRICE) -> dp.Instruction:
        return afp.ix_stage(authority=ISSUER, record=RECORD, mint=MINT,
                            program_id=PROGRAM, price=price)

    def test_the_data_is_two_then_the_price_little_endian(self) -> None:
        self.assertEqual(self.instruction().data, bytes([2]) + PRICE.to_bytes(8, "little"))

    def test_the_data_is_nine_bytes_for_every_price_including_zero(self) -> None:
        for price in (0, 1, 19, 2**64 - 1):
            with self.subTest(price=price):
                self.assertEqual(len(self.instruction(price).data), 9)

    def test_the_accounts_are_authority_then_record_then_mint(self) -> None:
        self.assertEqual(
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in self.instruction().accounts],
            [(ISSUER, True, False), (RECORD, False, True), (MINT, False, False)],
        )

    def test_the_payload_is_the_v1_payload_and_the_accounts_are_not(self) -> None:
        # The tag and the price never moved; the accounts did. One account and no signer is the
        # v1 shape, and a v2 record refuses it with 6026 (`checked_record_for_write`).
        v1 = dp.instruction_set_pending_price(record=RECORD, program_id=PROGRAM, price=PRICE)
        self.assertEqual(v1.data, self.instruction().data)
        self.assertEqual(len(v1.accounts), 1)
        self.assertEqual(len(self.instruction().accounts), 3)
        self.assertEqual([meta.pubkey for meta in self.instruction().accounts if meta.is_signer],
                         [ISSUER])

    def test_the_gateways_v2_builder_agrees_where_it_applies(self) -> None:
        from market_swarm import gateway as gw

        theirs = gw.instruction_set_pending_price_v2(
            authority=ISSUER, record=RECORD, mint=MINT, program_id=PROGRAM, price=PRICE
        )
        mine = self.instruction()
        self.assertEqual(theirs.data, mine.data)
        self.assertEqual(
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in theirs.accounts],
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in mine.accounts],
        )

    def test_a_zero_price_is_encodable_here_and_refused_by_the_gateway(self) -> None:
        # Leg 6 stages 0 to measure the chain's 6009; the gateway refuses to build that sale.
        self.assertEqual(self.instruction(0).data, bytes([2]) + bytes(8))
        from market_swarm import gateway as gw

        with self.assertRaises(ValueError):
            gw.instruction_set_pending_price_v2(
                authority=ISSUER, record=RECORD, mint=MINT, program_id=PROGRAM, price=0
            )

    def test_a_price_beyond_u64_is_refused_by_the_encoder(self) -> None:
        for bad in (-1, 2**64):
            with self.subTest(price=bad):
                with self.assertRaises(afp.ProofError):
                    self.instruction(price=bad)


class TestInitRecordWire(unittest.TestCase):
    """Tag 1: 22 bytes, five accounts, and the mint's authority as a signer."""

    def instruction(self, jurisdiction: str = "GB") -> dp.Instruction:
        return afp.ix_init_record(
            payer=ISSUER, mint=MINT, record=RECORD, mint_authority=ISSUER, program_id=PROGRAM,
            face=afp.FACE, cap_bps=afp.CAP_BPS, band_low=afp.BAND_LOW,
            jurisdiction=jurisdiction, policy=afp.POLICY_CAPPED,
        )

    def test_the_data_is_twenty_two_bytes_in_the_programs_field_order(self) -> None:
        expected = (
            bytes([1])
            + (1_000_000_000).to_bytes(8, "little")
            + (2_500).to_bytes(2, "little")
            + (0).to_bytes(8, "little")
            + b"GB"
            + bytes([0])
        )
        self.assertEqual(len(expected), 22)
        self.assertEqual(self.instruction().data, expected)

    def test_the_lib_rs_unpack_offsets_hold(self) -> None:
        # `HookInstruction::unpack` reads rest[..8], rest[8..10], rest[10..18], rest[18..20],
        # rest[20]. This asserts the encoder against those offsets rather than against itself.
        data = self.instruction("GB").data
        rest = data[1:]
        self.assertEqual(int.from_bytes(rest[0:8], "little"), afp.FACE)
        self.assertEqual(int.from_bytes(rest[8:10], "little"), afp.CAP_BPS)
        self.assertEqual(int.from_bytes(rest[10:18], "little"), afp.BAND_LOW)
        self.assertEqual(rest[18:20], b"GB")
        self.assertEqual(rest[20], afp.POLICY_CAPPED)
        self.assertEqual(len(rest), 21)

    def test_the_accounts_are_payer_mint_record_authority_system(self) -> None:
        self.assertEqual(
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in self.instruction().accounts],
            [
                (ISSUER, True, True),
                (MINT, False, False),
                (RECORD, False, True),
                (ISSUER, True, False),
                (dp.SYSTEM_PROGRAM, False, False),
            ],
        )

    def test_a_jurisdiction_that_is_not_two_bytes_is_refused(self) -> None:
        for bad in ("", "G", "GBR"):
            with self.subTest(jurisdiction=bad):
                with self.assertRaises(afp.ProofError):
                    self.instruction(bad)


class TestInitExtraMetasWire(unittest.TestCase):
    """Tag 0: the record pubkey, so the list the program writes resolves to it."""

    def test_the_data_is_the_tag_then_thirty_two_bytes_of_record(self) -> None:
        instruction = afp.ix_init_extra_metas(
            payer=ISSUER, mint=MINT, extra_metas=EXTRA, record=RECORD, program_id=PROGRAM
        )
        self.assertEqual(instruction.data, bytes([0]) + dp.base58.decode(RECORD))
        self.assertEqual(len(instruction.data), 33)

    def test_the_accounts_are_payer_mint_extra_metas_system(self) -> None:
        instruction = afp.ix_init_extra_metas(
            payer=ISSUER, mint=MINT, extra_metas=EXTRA, record=RECORD, program_id=PROGRAM
        )
        self.assertEqual(
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in instruction.accounts],
            [(ISSUER, True, True), (MINT, False, False), (EXTRA, False, True),
             (dp.SYSTEM_PROGRAM, False, False)],
        )

    def test_a_record_that_is_not_a_key_is_refused(self) -> None:
        with self.assertRaises(afp.ProofError):
            afp.ix_init_extra_metas(payer=ISSUER, mint=MINT, extra_metas=EXTRA,
                                    record="not-a-key", program_id=PROGRAM)


class TestMoveWire(unittest.TestCase):
    """The hooked transfer: `dp`'s order and bytes, with the record writable."""

    def instruction(self, amount: int = 1) -> dp.Instruction:
        return afp.ix_move(source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER,
                           record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA, amount=amount)

    def test_the_accounts_are_the_seven_the_program_expects(self) -> None:
        self.assertEqual(
            [(meta.pubkey, meta.is_signer, meta.is_writable) for meta in self.instruction().accounts],
            [
                (SOURCE, False, True),
                (MINT, False, False),
                (DESTINATION, False, True),
                (SELLER, True, False),
                (RECORD, False, True),
                (PROGRAM, False, False),
                (EXTRA, False, False),
            ],
        )

    def test_the_data_is_transfer_checked_for_one_ticket_of_zero_decimals(self) -> None:
        self.assertEqual(self.instruction().data, bytes([12]) + (1).to_bytes(8, "little") + bytes([0]))
        self.assertEqual(len(self.instruction().data), 10)

    def test_the_bytes_match_the_published_encoder_and_the_record_flag_does_not(self) -> None:
        # Same accounts in the same order and the same data, one flag apart. The reason is the
        # runtime's: an account is writable for a transaction if any instruction says so, and an
        # inner CPI cannot ask for more than the outer granted. v2's metas list declares the record
        # writable, so a message that only ever names it read-only is refused `PrivilegeEscalation`
        # at the Token-2022 instruction and the hook never runs. Measured by the review of 38.
        published = dp.instruction_transfer_checked(
            source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER, record=RECORD,
            hook_program=PROGRAM, extra_metas=EXTRA, amount=1, decimals=0,
        )
        mine = self.instruction()
        self.assertEqual(mine.data, published.data)
        self.assertEqual([meta.pubkey for meta in mine.accounts],
                         [meta.pubkey for meta in published.accounts])
        published_record = published.accounts[4]
        self.assertTrue(published_record.is_writable is False, "the published encoder marks it read-only")
        self.assertTrue(mine.accounts[4].is_writable, "the v2 write path needs it writable")

    def test_only_the_seller_signs(self) -> None:
        self.assertEqual([meta.pubkey for meta in self.instruction().accounts if meta.is_signer],
                         [SELLER])

    def test_an_amount_other_than_one_is_refused_before_it_is_sent(self) -> None:
        for amount in (0, 2, 10):
            with self.subTest(amount=amount):
                with self.assertRaises(afp.ProofError):
                    self.instruction(amount)


class TestRecordDecode(unittest.TestCase):
    """The 70-byte `TicketRecord`, decoded here so the layout is checked and not assumed."""

    def buffer(self) -> bytes:
        return (
            (1_000_000_000).to_bytes(8, "little")
            + (2_500).to_bytes(2, "little")
            + (0).to_bytes(8, "little")
            + bytes([1])
            + (0).to_bytes(8, "little")
            + b"GB"
            + bytes([0])
            + (1_760_000_000).to_bytes(8, "little", signed=True)
            + dp.base58.decode(ISSUER)
        )

    def test_the_buffer_is_the_width_the_program_declares(self) -> None:
        self.assertEqual(len(self.buffer()), 70)
        self.assertEqual(len(self.buffer()), afp.RECORD_LEN)

    def test_every_field_lands_where_state_rs_says_it_does(self) -> None:
        self.assertEqual(
            afp.decode_record(self.buffer()),
            {
                "face_value_lamports": 1_000_000_000,
                "cap_bps": 2_500,
                "pending_price_lamports": 0,
                "status": 1,
                "band_low_lamports": 0,
                "jurisdiction": "GB",
                "policy": 0,
                "held_since_unix": 1_760_000_000,
                "authority": ISSUER,
                "raw_len": 70,
            },
        )

    def test_held_since_is_signed_so_a_negative_stamp_does_not_read_as_a_huge_one(self) -> None:
        raw = bytearray(self.buffer())
        raw[30:38] = (-1).to_bytes(8, "little", signed=True)
        self.assertEqual(afp.decode_record(bytes(raw))["held_since_unix"], -1)

    def test_a_buffer_of_the_wrong_width_is_refused_rather_than_part_read(self) -> None:
        for width in (0, 19, 58, 69, 71, 102):
            with self.subTest(width=width):
                with self.assertRaises(afp.ProofError):
                    afp.decode_record(bytes(width))

    def test_the_decode_carries_no_fee_field(self) -> None:
        # Leg 7's whole point: the record stores the staged price and nothing about a payment.
        fields = set(afp.decode_record(self.buffer()))
        self.assertEqual(fields - {"raw_len"}, {
            "face_value_lamports", "cap_bps", "pending_price_lamports", "status",
            "band_low_lamports", "jurisdiction", "policy", "held_since_unix", "authority",
        })


class TestDescribeError(unittest.TestCase):
    """The error split into what a report needs: index, code, and the cluster's own text."""

    def test_a_program_refusal_names_its_index_and_code(self) -> None:
        described = afp.describe_error({"InstructionError": [2, {"Custom": 6010}]})
        self.assertEqual((described["index"], described["code"], described["variant"]), (2, 6010, "Custom"))
        self.assertEqual(described["text"], '{"InstructionError": [2, {"Custom": 6010}]}')

    def test_the_system_programs_insufficient_funds_is_a_custom_one(self) -> None:
        described = afp.describe_error({"InstructionError": [1, {"Custom": 1}]})
        self.assertEqual((described["index"], described["code"]), (1, 1))

    def test_a_builtin_variant_is_reported_as_itself(self) -> None:
        described = afp.describe_error({"InstructionError": [0, "InvalidAccountData"]})
        self.assertEqual((described["index"], described["code"]), (0, None))
        self.assertEqual(described["variant"], "InvalidAccountData")

    def test_a_transaction_level_error_has_no_instruction_to_blame(self) -> None:
        described = afp.describe_error({"InsufficientFundsForFee": {"account_index": 0}})
        self.assertIsNone(described["index"])
        self.assertEqual(described["variant"], "InsufficientFundsForFee")

    def test_no_error_says_so_rather_than_printing_a_null(self) -> None:
        self.assertEqual(afp.describe_error(None)["text"], "no error")

    def test_an_error_that_is_not_a_dict_is_still_printable(self) -> None:
        self.assertEqual(afp.describe_error("boom")["text"], '"boom"')


class TestSignerOrder(unittest.TestCase):
    """Two signatures per sale, in the order the compiled message asks for them."""

    def sale(self, *, price: int = PRICE, bps: int = BPS) -> bytes:
        stage = afp.ix_stage(authority=ISSUER, record=RECORD, mint=MINT,
                             program_id=PROGRAM, price=price)
        move = afp.ix_move(source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER,
                           record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA)
        legs = af.sale_instructions(stage=stage, move=move, seller=SELLER, artist_wallet=ARTIST,
                                    price_lamports=price, fee_bps=bps)
        return dp.compile_message(SELLER, list(legs), BLOCKHASH)

    def test_a_sale_needs_the_seller_then_the_issuer(self) -> None:
        from market_swarm import gateway as gw

        self.assertEqual(gw.signer_keys_from_message(self.sale()), (SELLER, ISSUER))

    def test_the_issuer_is_there_for_the_stage_and_not_for_the_fee(self) -> None:
        from market_swarm import gateway as gw

        # A zero fee drops the System transfer and keeps both signers: the signer set comes from
        # the v2 stage, not from the payment.
        zero_fee = gw.signer_keys_from_message(self.sale(price=19))
        paid = gw.signer_keys_from_message(self.sale(price=20))
        self.assertEqual(zero_fee, (SELLER, ISSUER))
        self.assertEqual(paid, zero_fee)

    def test_the_two_free_ride_transactions_have_one_signer_each(self) -> None:
        from market_swarm import gateway as gw

        stage = afp.ix_stage(authority=ISSUER, record=RECORD, mint=MINT,
                             program_id=PROGRAM, price=PRICE)
        move = afp.ix_move(source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER,
                           record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA)
        self.assertEqual(gw.signer_keys_from_message(dp.compile_message(ISSUER, [stage], BLOCKHASH)),
                         (ISSUER,))
        self.assertEqual(gw.signer_keys_from_message(dp.compile_message(SELLER, [move], BLOCKHASH)),
                         (SELLER,))

    def test_the_artist_signs_nothing_and_the_payer_comes_first(self) -> None:
        from market_swarm import gateway as gw

        signers = gw.signer_keys_from_message(self.sale())
        self.assertNotIn(ARTIST, signers)
        self.assertEqual(signers[0], SELLER, "the payer is the first key in a canonical message")


class TestResolveSigners(unittest.TestCase):
    """A missing or an extra keypair is a hard error that names both sides."""

    def test_an_exact_set_resolves_in_the_messages_order(self) -> None:
        keypairs = {ISSUER: Path("issuer.json"), SELLER: Path("seller.json")}
        self.assertEqual(
            afp.resolve_signers((SELLER, ISSUER), keypairs),
            [(SELLER, Path("seller.json")), (ISSUER, Path("issuer.json"))],
        )

    def test_a_missing_keypair_is_refused_and_named(self) -> None:
        with self.assertRaises(afp.ProofError) as caught:
            afp.resolve_signers((SELLER, ISSUER), {SELLER: Path("seller.json")})
        self.assertIn("no keypair for", str(caught.exception))
        self.assertIn(ISSUER, str(caught.exception))

    def test_an_extra_keypair_is_refused_and_named(self) -> None:
        keypairs = {SELLER: Path("seller.json"), ISSUER: Path("issuer.json"), ARTIST: Path("a")}
        with self.assertRaises(afp.ProofError) as caught:
            afp.resolve_signers((SELLER, ISSUER), keypairs)
        self.assertIn("a path", str(caught.exception))
        self.assertIn(ARTIST, str(caught.exception))

    def test_a_sale_through_the_real_message_maps_both_keys(self) -> None:
        from market_swarm import gateway as gw

        stage = afp.ix_stage(authority=ISSUER, record=RECORD, mint=MINT,
                             program_id=PROGRAM, price=PRICE)
        move = afp.ix_move(source=SOURCE, mint=MINT, destination=DESTINATION, authority=SELLER,
                           record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA)
        legs = af.sale_instructions(stage=stage, move=move, seller=SELLER, artist_wallet=ARTIST,
                                    price_lamports=PRICE, fee_bps=BPS)
        message = dp.compile_message(SELLER, list(legs), BLOCKHASH)
        keypairs = {SELLER: Path("seller.json"), ISSUER: Path("issuer.json")}
        pairs = afp.resolve_signers(gw.signer_keys_from_message(message), keypairs)
        self.assertEqual([key for key, _ in pairs], [SELLER, ISSUER])


class TestTheLegsNumbers(unittest.TestCase):
    """The arithmetic each leg asserts, against the numbers the brief pins."""

    def test_the_ceiling_is_the_cap_predicate_solved_for_price(self) -> None:
        self.assertEqual(afp.ceiling_lamports(face_lamports=1_000_000_000, cap_bps=2_500), 1_250_000_000)
        self.assertEqual(afp.CEILING, 1_250_000_000)
        self.assertEqual(afp.ceiling_lamports(face_lamports=1, cap_bps=0), 1)
        self.assertEqual(afp.ceiling_lamports(face_lamports=1, cap_bps=65_535), 7)

    def test_a_bad_ceiling_input_is_refused(self) -> None:
        for face, cap in ((-1, 100), (1, -1), (1, 65_536)):
            with self.subTest(face=face, cap=cap):
                with self.assertRaises(ValueError):
                    afp.ceiling_lamports(face_lamports=face, cap_bps=cap)

    def test_the_planned_fees_are_the_briefs_numbers(self) -> None:
        self.assertEqual(afp.planned_fees(), {
            "leg1": 50_000_000,
            "leg3": 62_500_000,
            "leg4_price_19": 0,
            "leg4_price_20": 1,
            "leg5": 1_000_000_000,
            "leg6": 0,
            "leg8_would_be": 50_000_000,
        })

    def test_the_100_percent_fee_is_the_whole_price_and_no_more(self) -> None:
        self.assertEqual(afp.planned_fees()["leg5"], afp.FACE)

    def test_the_underfunded_seller_can_pay_the_fee_it_never_can(self) -> None:
        # The leg's claim is "covers the two-signature transaction fee, cannot pay the fee".
        self.assertGreater(afp.SELLER_UNDERFUNDED_LAMPORTS, 2 * 5_000)
        self.assertLess(afp.SELLER_UNDERFUNDED_LAMPORTS, afp.planned_fees()["leg1"])

    def test_the_sale_mint_has_enough_tickets_for_the_legs_that_move_one(self) -> None:
        moving_legs = 5  # legs 1, 4a, 4b, 5 and 8 each move exactly one ticket
        self.assertGreaterEqual(afp.TICKETS_SALE, moving_legs)

    def test_every_leg_key_is_accounted_for(self) -> None:
        self.assertEqual(afp.LEG_KEYS, ("1", "2", "3", "4a", "4b", "5", "6", "7", "8"))
        self.assertEqual(len(set(afp.LEG_KEYS)), len(afp.LEG_KEYS))


class TestLoopbackRefusal(unittest.TestCase):
    """The tool refuses any RPC that is not this machine's own validator."""

    def test_loopback_is_accepted(self) -> None:
        for url in ("http://127.0.0.1:8899", "http://localhost:20000", "http://[::1]:9999"):
            with self.subTest(url=url):
                self.assertEqual(afp.assert_loopback(url), url)

    def test_a_public_cluster_is_refused(self) -> None:
        for url in ("https://api.devnet.solana.com", "https://api.mainnet-beta.solana.com",
                    "http://10.0.0.5:8899", "http://127.0.0.1", "", None, "devnet"):
            with self.subTest(url=url):
                with self.assertRaises(afp.ProofError):
                    afp.assert_loopback(url)


class TestFmt(unittest.TestCase):
    def test_numbers_are_grouped_and_never_floats(self) -> None:
        self.assertEqual(afp.fmt(50_000_000), "50,000,000")
        self.assertEqual(afp.fmt(0), "0")
        self.assertEqual(afp.fmt(-1), "-1")
        self.assertEqual(afp.fmt(True), "yes")
        self.assertEqual(afp.fmt(None), "None")


class TestTheToolsOwnLimits(unittest.TestCase):
    """What the source itself must never grow: a rebuild, a public cluster, a git write."""

    SOURCE = (REPO_ROOT / "tools" / "artist_fee_proof.py").read_text(encoding="utf-8")

    def test_the_program_is_an_asserted_input_and_never_rebuilt(self) -> None:
        self.assertIn(afp.SO_SHA256, self.SOURCE)
        for forbidden in ("cargo-build-sbf", "cargo build", "cargo_build"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_no_public_cluster_anywhere_in_the_file(self) -> None:
        for forbidden in ("api.devnet.solana.com", "api.mainnet-beta.solana.com",
                          "CLUSTER_URLS", "request_airdrop"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_the_validator_command_carries_no_url_and_no_clone(self) -> None:
        # The docstring says the words; the command must not. Read the function that builds it.
        import inspect

        command = inspect.getsource(afp.LocalCluster.start)
        self.assertIn('"--bind-address"', command)
        self.assertIn('"--gossip-port"', command)
        for forbidden in ("--clone", "--url", "devnet"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, command)

    def test_it_does_not_use_the_v1_encoders_the_program_refuses(self) -> None:
        for forbidden in ("dp.instruction_init_record(", "dp.instruction_set_pending_price("):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_it_writes_no_git_state(self) -> None:
        for forbidden in ("git add", "git commit", "git push", "subprocess.run([\"git\""):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_it_never_opens_a_keypair_itself(self) -> None:
        # Keys are opened only by `tools/solana_sign.py` and `solana-keygen`, in child processes.
        for forbidden in ("read_text()", "json.load"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, self.SOURCE)

    def test_the_ledger_and_the_keys_live_under_the_ignored_tmp(self) -> None:
        self.assertTrue(str(afp.WORK).endswith("tmp/artist-fee"))
        self.assertTrue(str(afp.KEYS).endswith("tmp/artist-fee/keys"))
        self.assertTrue(str(afp.LEDGER).endswith("tmp/artist-fee/ledger"))
        self.assertIn("tmp/", self.SOURCE)

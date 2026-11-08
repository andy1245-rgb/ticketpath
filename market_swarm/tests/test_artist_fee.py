"""The artist fee at checkout: the policy, the arithmetic, and the three-instruction sale.

What is checked here is every claim `market_swarm/artist_fee.py` makes about itself: the two
fields are bounded the way a config error needs them to be, the division is integer and floored
(the exact table the spec pins, including the boundary at 19/20 lamports), the System transfer is
bincode with the source the only signer, and the sale is three instructions with the fee leg in
the middle or two with no fee leg at all.

`system_transfer_instruction` is checked twice: against its own bytes, and against
`market_swarm.gateway.system_transfer_instruction` for the same amounts. The gateway is imported
inside that one test — it reaches no cluster, no key and no file at import — because the two
builders must not drift: the gateway funds wallets with one, the checkout pays the artist with
the other, and both write to the same chain.
"""

from __future__ import annotations

import ast
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from market_swarm import artist_fee as af

REPO_ROOT = Path(__file__).resolve().parents[2]

#: Two real 32-byte base58 addresses. The first is the Token program's own id, the second and
#: third are deterministic byte runs, so a failure in the wallet check names an obvious value.
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
SELLER = af.dp.base58.encode(bytes(range(1, 33)))
ARTIST = af.dp.base58.encode(bytes(range(33, 65)))
#: 31 bytes: base58-valid, one short of a public key, which is exactly the typo the length
#: check exists for.
SHORT_WALLET = af.dp.base58.encode(bytes(range(1, 32)))

PRICE = 1_000_000_000  # 1 SOL, the design's own worked pair
BPS = 500
FEE = 50_000_000


def _instruction(tag: int) -> af.dp.Instruction:
    """A stand-in for a leg this module does not own. Only identity is asserted of it."""
    return af.dp.Instruction(program_id=af.dp.SYSTEM_PROGRAM, accounts=(), data=bytes([tag]))


class TestPolicy(unittest.TestCase):
    def test_rates_at_both_ends_are_accepted(self) -> None:
        for bps in (0, 1, 500, 9_999, af.MAX_FEE_BPS):
            with self.subTest(bps=bps):
                self.assertEqual(af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=bps).fee_bps, bps)

    def test_a_rate_above_the_maximum_is_refused_naming_the_field(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_001)
        self.assertIn("fee_bps", str(caught.exception))
        self.assertIn("10000", str(caught.exception))

    def test_a_negative_rate_is_refused(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=-1)
        self.assertIn("fee_bps", str(caught.exception))

    def test_bools_and_floats_are_refused_as_rates(self) -> None:
        for bad in (True, False, 500.0, "500", None, [500]):
            with self.subTest(bad=bad):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=bad)
                self.assertIn("fee_bps", str(caught.exception))

    def test_the_wallet_must_decode_to_32_bytes(self) -> None:
        for bad in ("", "1111", SHORT_WALLET, SHORT_WALLET + "1", "0OIl"):
            with self.subTest(bad=bad):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.ArtistFeePolicy(artist_wallet=bad, fee_bps=500)
                self.assertIn("artist_wallet", str(caught.exception))

    def test_a_non_string_wallet_is_refused(self) -> None:
        for bad in (None, 32, b"\x00" * 32):
            with self.subTest(bad=bad):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.ArtistFeePolicy(artist_wallet=bad, fee_bps=500)
                self.assertIn("artist_wallet", str(caught.exception))

    def test_the_policy_is_frozen(self) -> None:
        policy = af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS)
        with self.assertRaises(FrozenInstanceError):
            policy.fee_bps = 900  # type: ignore[misc]

    def test_to_dict_round_trips_through_from_mapping(self) -> None:
        policy = af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS)
        self.assertEqual(policy.to_dict(), {"artist_wallet": ARTIST, "fee_bps": BPS})
        self.assertEqual(af.ArtistFeePolicy.from_mapping(policy.to_dict()), policy)

    def test_from_mapping_refuses_an_unknown_key_and_names_the_path(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy.from_mapping(
                {"artist_wallet": ARTIST, "fee_bps": BPS, "fee_rate": 5}, field="events[0].artist_fee"
            )
        message = str(caught.exception)
        self.assertIn("events[0].artist_fee", message)
        self.assertIn("fee_rate", message)

    def test_from_mapping_reports_a_bad_value_under_the_path_it_was_given(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy.from_mapping(
                {"artist_wallet": ARTIST, "fee_bps": 20_000}, field="events[1].artist_fee"
            )
        message = str(caught.exception)
        self.assertIn("events[1].artist_fee.fee_bps", message)
        self.assertIn("20000", message)

    def test_from_mapping_refuses_a_missing_key_and_a_non_object(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy.from_mapping({"fee_bps": BPS}, field="artist_fee")
        self.assertIn("artist_fee.artist_wallet", str(caught.exception))
        with self.assertRaises(af.ArtistFeeError):
            af.ArtistFeePolicy.from_mapping([ARTIST, BPS])

    def test_the_default_field_path_is_artist_fee(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.ArtistFeePolicy.from_mapping({"artist_wallet": ARTIST})
        self.assertIn("artist_fee.fee_bps", str(caught.exception))


class TestFeeArithmetic(unittest.TestCase):
    def test_the_pinned_table(self) -> None:
        # The spec's own table, quoted so a change to the rounding shows up as a named case.
        cases = {
            (19, 500): 0,
            (20, 500): 1,
            (1, 9_999): 0,
            (1, 10_000): 1,
            (0, 500): 0,
            (0, 10_000): 0,
            (PRICE, BPS): FEE,
            (PRICE, 0): 0,
            (PRICE, 10_000): PRICE,
            (2**64 - 1, 10_000): 2**64 - 1,
        }
        for (price, bps), expected in sorted(cases.items()):
            with self.subTest(price=price, bps=bps):
                got = af.fee_lamports(price_lamports=price, fee_bps=bps)
                self.assertEqual(got, expected)
                self.assertIsInstance(got, int)
                self.assertNotIsInstance(got, bool)

    def test_floor_never_takes_more_than_the_rate_says(self) -> None:
        # A ceiling would make these 1 and 2; floor leaves the sale's fee at nothing and one.
        self.assertEqual(af.fee_lamports(price_lamports=19, fee_bps=500), 0)
        self.assertEqual(af.fee_lamports(price_lamports=1, fee_bps=9_999), 0)

    def test_the_fee_never_exceeds_the_price(self) -> None:
        prices = (0, 1, 19, 20, 999, 1_000_000, PRICE, 2**64 - 1)
        rates = (0, 1, 250, 500, 2_500, 9_999, 10_000)
        for price in prices:
            for bps in rates:
                with self.subTest(price=price, bps=bps):
                    fee = af.fee_lamports(price_lamports=price, fee_bps=bps)
                    self.assertLessEqual(fee, price)
                    self.assertGreaterEqual(fee, 0)

    def test_the_fee_equals_the_price_at_one_hundred_percent(self) -> None:
        for price in (0, 1, 19, 20, 999, PRICE):
            with self.subTest(price=price):
                self.assertEqual(af.fee_lamports(price_lamports=price, fee_bps=10_000), price)

    def test_monotone_in_the_price(self) -> None:
        previous = 0
        for price in range(0, 5_000, 7):
            fee = af.fee_lamports(price_lamports=price, fee_bps=BPS)
            self.assertGreaterEqual(fee, previous)
            previous = fee

    def test_monotone_in_the_rate(self) -> None:
        previous = 0
        for bps in range(0, af.MAX_FEE_BPS + 1, 13):
            fee = af.fee_lamports(price_lamports=PRICE, fee_bps=bps)
            self.assertGreaterEqual(fee, previous)
            previous = fee

    def test_bad_inputs_are_refused_naming_the_field(self) -> None:
        for kwargs, field in (
            ({"price_lamports": -1, "fee_bps": BPS}, "price_lamports"),
            ({"price_lamports": 1.5, "fee_bps": BPS}, "price_lamports"),
            ({"price_lamports": True, "fee_bps": BPS}, "price_lamports"),
            ({"price_lamports": PRICE, "fee_bps": -1}, "fee_bps"),
            ({"price_lamports": PRICE, "fee_bps": 10_001}, "fee_bps"),
            ({"price_lamports": PRICE, "fee_bps": 500.0}, "fee_bps"),
            ({"price_lamports": PRICE, "fee_bps": False}, "fee_bps"),
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.fee_lamports(**kwargs)
                self.assertIn(field, str(caught.exception))


class TestSystemTransfer(unittest.TestCase):
    def test_the_data_is_twelve_bytes_of_bincode(self) -> None:
        for amount in (1, 255, 256, 50_000_000, 2**64 - 1):
            with self.subTest(amount=amount):
                instruction = af.system_transfer_instruction(
                    source=SELLER, destination=ARTIST, lamports=amount
                )
                self.assertEqual(len(instruction.data), 12)
                self.assertEqual(instruction.data[:4], bytes([2, 0, 0, 0]))
                self.assertEqual(instruction.data[4:], amount.to_bytes(8, "little"))

    def test_the_accounts_are_source_then_destination(self) -> None:
        instruction = af.system_transfer_instruction(
            source=SELLER, destination=ARTIST, lamports=FEE
        )
        self.assertEqual(instruction.program_id, af.dp.SYSTEM_PROGRAM)
        self.assertEqual(len(instruction.accounts), 2)
        source, destination = instruction.accounts
        self.assertEqual((source.pubkey, source.is_signer, source.is_writable), (SELLER, True, True))
        self.assertEqual(
            (destination.pubkey, destination.is_signer, destination.is_writable),
            (ARTIST, False, True),
        )

    def test_amounts_outside_one_to_u64_are_refused(self) -> None:
        for bad in (0, -1, 2**64, 1.0, True, "1"):
            with self.subTest(bad=bad):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.system_transfer_instruction(source=SELLER, destination=ARTIST, lamports=bad)
                self.assertIn("lamports", str(caught.exception))

    def test_the_bytes_match_the_gateways_transfer_exactly(self) -> None:
        # Imported here and not at module scope: the gateway imports this module, so a
        # module-level import would be the cycle the design forbids.
        from market_swarm import gateway as gw

        for amount in (1, 2, 255, 256, 50_000_000, PRICE, 2**64 - 1):
            with self.subTest(amount=amount):
                ours = af.system_transfer_instruction(
                    source=SELLER, destination=ARTIST, lamports=amount
                )
                theirs = gw.system_transfer_instruction(
                    source=SELLER, destination=ARTIST, lamports=amount
                )
                self.assertEqual(ours.data, theirs.data)
                self.assertEqual(ours.program_id, theirs.program_id)
                self.assertEqual(
                    [(a.pubkey, a.is_signer, a.is_writable) for a in ours.accounts],
                    [(a.pubkey, a.is_signer, a.is_writable) for a in theirs.accounts],
                )


class TestSaleInstructions(unittest.TestCase):
    def test_a_positive_fee_gives_three_instructions_in_order(self) -> None:
        stage, move = _instruction(11), _instruction(12)
        built = af.sale_instructions(
            stage=stage,
            move=move,
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=PRICE,
            fee_bps=BPS,
        )
        self.assertEqual(len(built), 3)
        self.assertIs(built[0], stage)
        self.assertIs(built[2], move)
        self.assertEqual(built[1].data[:4], bytes([2, 0, 0, 0]))
        self.assertEqual(built[1].data[4:], FEE.to_bytes(8, "little"))

    def test_a_zero_fee_gives_two_instructions_and_no_fee_leg(self) -> None:
        stage, move = _instruction(11), _instruction(12)
        for price, bps in ((PRICE, 0), (19, BPS)):
            with self.subTest(price=price, bps=bps):
                built = af.sale_instructions(
                    stage=stage,
                    move=move,
                    seller=SELLER,
                    artist_wallet=ARTIST,
                    price_lamports=price,
                    fee_bps=bps,
                )
                self.assertEqual(len(built), 2)
                self.assertIs(built[0], stage)
                self.assertIs(built[1], move)

    def test_the_fee_leg_pays_the_artist_from_the_seller(self) -> None:
        built = af.sale_instructions(
            stage=_instruction(11),
            move=_instruction(12),
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=PRICE,
            fee_bps=BPS,
        )
        fee_leg = built[1]
        self.assertEqual(fee_leg.program_id, af.dp.SYSTEM_PROGRAM)
        self.assertEqual([account.pubkey for account in fee_leg.accounts], [SELLER, ARTIST])
        self.assertEqual([account.is_signer for account in fee_leg.accounts], [True, False])

    def test_a_zero_price_is_refused_because_the_chain_reads_it_as_nothing_staged(self) -> None:
        for price in (0, -1):
            with self.subTest(price=price):
                with self.assertRaises(af.ArtistFeeError) as caught:
                    af.sale_instructions(
                        stage=_instruction(11),
                        move=_instruction(12),
                        seller=SELLER,
                        artist_wallet=ARTIST,
                        price_lamports=price,
                        fee_bps=BPS,
                    )
                self.assertIn("price_lamports", str(caught.exception))
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.sale_instructions(
                stage=_instruction(11),
                move=_instruction(12),
                seller=SELLER,
                artist_wallet=ARTIST,
                price_lamports=0,
                fee_bps=BPS,
            )
        self.assertIn("6009", str(caught.exception))

    def test_the_artist_may_not_be_the_seller(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.sale_instructions(
                stage=_instruction(11),
                move=_instruction(12),
                seller=SELLER,
                artist_wallet=SELLER,
                price_lamports=PRICE,
                fee_bps=BPS,
            )
        self.assertIn("artist_wallet", str(caught.exception))

    def test_a_fee_beyond_u64_is_refused(self) -> None:
        with self.assertRaises(af.ArtistFeeError) as caught:
            af.sale_instructions(
                stage=_instruction(11),
                move=_instruction(12),
                seller=SELLER,
                artist_wallet=ARTIST,
                price_lamports=2**64,
                fee_bps=10_000,
            )
        self.assertIn("fee_lamports", str(caught.exception))

    def test_a_fee_of_exactly_u64_is_still_buildable(self) -> None:
        built = af.sale_instructions(
            stage=_instruction(11),
            move=_instruction(12),
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=2**64 - 1,
            fee_bps=10_000,
        )
        self.assertEqual(len(built), 3)
        self.assertEqual(built[1].data[4:], bytes([0xFF] * 8))

    def test_a_bad_policy_is_refused_before_anything_is_built(self) -> None:
        for wallet, bps in ((ARTIST, 10_001), (SHORT_WALLET, BPS), ("0OIl", BPS)):
            with self.subTest(wallet=wallet, bps=bps):
                with self.assertRaises(af.ArtistFeeError):
                    af.sale_instructions(
                        stage=_instruction(11),
                        move=_instruction(12),
                        seller=SELLER,
                        artist_wallet=wallet,
                        price_lamports=PRICE,
                        fee_bps=bps,
                    )


class TestModuleSurface(unittest.TestCase):
    def test_the_constants_are_pinned(self) -> None:
        self.assertEqual(af.FEE_BPS_DENOMINATOR, 10_000)
        self.assertEqual(af.MAX_FEE_BPS, 10_000)
        self.assertEqual(af.U64_MAX, 2**64 - 1)

    def test_the_error_is_a_value_error(self) -> None:
        self.assertTrue(issubclass(af.ArtistFeeError, ValueError))

    def test_the_module_imports_no_gateway_and_no_network(self) -> None:
        # The gateway imports this module, so this module importing it back would be a cycle;
        # and a fee calculation is arithmetic, so it has no reason to open a socket.
        tree = ast.parse((REPO_ROOT / "market_swarm" / "artist_fee.py").read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        for forbidden in ("market_swarm.gateway", "socket", "urllib", "http.client", "subprocess"):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    [name for name in imported if name == forbidden or name.startswith(forbidden + ".")],
                    f"artist_fee must not import {forbidden}",
                )

    def test_there_is_no_float_division_in_the_source(self) -> None:
        # `REPO_ROOT / "tools"` is a path join, not a division, so a `/` with a string operand
        # is skipped. Everything else is money arithmetic and must be `//`.
        tree = ast.parse((REPO_ROOT / "market_swarm" / "artist_fee.py").read_text(encoding="utf-8"))
        divides = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp)
            and isinstance(node.op, ast.Div)
            and not any(
                isinstance(side, ast.Constant) and isinstance(side.value, str)
                for side in (node.left, node.right)
            )
        ]
        self.assertEqual(divides, [], "money arithmetic is integer only; `//` or nothing")
        floats = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, float)
        ]
        self.assertEqual(floats, [], "no float literal belongs in a lamport calculation")

    def test_the_public_surface_is_the_one_both_builders_code_to(self) -> None:
        for name in (
            "FEE_BPS_DENOMINATOR",
            "MAX_FEE_BPS",
            "ArtistFeeError",
            "ArtistFeePolicy",
            "fee_lamports",
            "system_transfer_instruction",
            "sale_instructions",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(af, name), f"artist_fee is missing {name}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

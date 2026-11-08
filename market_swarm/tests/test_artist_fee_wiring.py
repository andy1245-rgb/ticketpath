"""The artist fee wired into the harness: config, dry run, ledger, dataset, signers.

`test_artist_fee.py` checks what `market_swarm/artist_fee.py` does on its own. This file checks
that the rest of the harness uses it and uses it the same way: a config block that parses into an
`EventSpec` (or is refused as a `ConfigError`, the type a config loader raises), a dry run that
prices the fee with the real arithmetic and still says it simulated, a ledger column and a
`verify_dataset` rule that can disagree with each other, `TransferResult.fee_lamports` defaulting
to zero so nothing that predates the fee has to change, and the signature order read back out of
a compiled message instead of assumed.

Three claims are deliberately about *absence*:

- the no-fee path is untouched, so a result from an event with no policy reports 0 and carries
  exactly the one simulated log line it carried before;
- a refused sale reports 0, because a refused transaction moved nothing -- that is the atomicity
  claim as the dataset sees it, and a refusal that reported a fee would be the harness paying an
  artist in a row for money nobody transferred;
- an existing dataset is still valid, so the fee column is additive and not a schema break.

No validator, no network, no keypair file, no `solana` or `spl-token` child: the one cluster
here is a dictionary of RPC answers, and the keypair paths are names that are never opened.
"""

from __future__ import annotations

import base64
import contextlib
import io
import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from market_swarm import gateway as gw
from market_swarm.cli import main
from market_swarm.config import (
    BPS_DENOMINATOR,
    ConfigError,
    EventSpec,
    ceiling_lamports,
    effective_cap_bps,
    load_run_config,
)
from market_swarm.datasets import DatasetInvalid, verify_dataset
from market_swarm.ledger import LEDGER_HEADER, LedgerWriter, TradeRow

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE = REPO_ROOT / "market_swarm" / "example-run.json"

#: The design's own worked pair: 5% of a 1 SOL ticket.
PRICE = 1_000_000_000
BPS = 500
FEE = 50_000_000
FACE = PRICE
CAP_BPS = 2500
CEILING = ceiling_lamports(FACE, CAP_BPS)


def address(seed: int) -> str:
    """A real 32-byte base58 address, so `compile_message` accepts it and nothing is generated."""
    return gw.dp.base58.encode(bytes([seed % 251]) * 32)


SELLER = address(2)
ISSUER = address(1)
ARTIST = address(3)
#: 31 bytes: base58-valid and one short of a public key, which is the typo the length check exists
#: for. It must be refused by the loader with the field path, not accepted and refused on chain.
SHORT_WALLET = gw.dp.base58.encode(bytes(range(1, 32)))
BLOCKHASH = gw.dp.base58.encode(bytes(range(32)))
SIGNATURE = gw.dp.base58.encode(bytes([9]) * 64)


def spec(**overrides) -> EventSpec:
    base = dict(
        event_id="evt_fee",
        face_lamports=FACE,
        mode="capped",
        cap_bps=CAP_BPS,
        tickets=4,
        rounds=2,
        round_seconds=0,
    )
    base.update(overrides)
    return EventSpec(**base)


def policy_wire(**overrides) -> dict:
    """The mapping a config file carries under one event's `artist_fee`."""
    block = {"artist_wallet": ARTIST, "fee_bps": BPS}
    block.update(overrides)
    return block


def config_document(**event_overrides) -> dict:
    """A whole run config, as JSON, with one event that may carry a fee block."""
    event = {
        "event_id": "evt_fee",
        "face_lamports": FACE,
        "mode": "capped",
        "cap_bps": CAP_BPS,
        "tickets": 4,
        "rounds": 2,
        "round_seconds": 0,
    }
    event.update(event_overrides)
    return {
        "cluster": "local",
        "dry_run": True,
        "seed": 1,
        "kill_after_seconds": 60,
        "out_dir": "market_swarm/runs",
        "total_budget_lamports": 10_000_000_000,
        "total_budget_actions": 100,
        "events": [event],
        "agents": [
            {
                "agent_id": "a1",
                "policy": "buyer",
                "wallet_label": "a1",
                "seed": 3,
                "budget_lamports": 1_000_000_000,
                "budget_actions": 10,
            }
        ],
    }


class ConfigCase(unittest.TestCase):
    """Write a config document, load it, and keep the temporary directory alive for the test."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self._written = 0

    def write(self, document: dict) -> Path:
        self._written += 1
        path = self.dir / f"run-{self._written}.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def load(self, document: dict):
        return load_run_config(self.write(document))


class TestConfigParsesTheFee(ConfigCase):
    def test_a_named_fee_becomes_a_policy_on_that_event_only(self) -> None:
        document = config_document(artist_fee=policy_wire())
        plain = dict(document["events"][0], event_id="evt_plain")
        plain.pop("artist_fee")  # the second event names no fee; the first one's must not reach it
        document["events"].append(plain)
        config = self.load(document)
        self.assertEqual(config.events[0].artist_fee.artist_wallet, ARTIST)
        self.assertEqual(config.events[0].artist_fee.fee_bps, BPS)
        self.assertIsNone(
            config.events[1].artist_fee,
            "a fee on one event must not leak to another: the rate is per event, not per run",
        )

    def test_the_shipped_example_config_names_no_fee(self) -> None:
        config = load_run_config(EXAMPLE)
        self.assertTrue(config.events)
        for event in config.events:
            with self.subTest(event=event.event_id):
                self.assertIsNone(event.artist_fee)

    def test_an_explicit_null_is_no_fee(self) -> None:
        self.assertIsNone(self.load(config_document(artist_fee=None)).events[0].artist_fee)

    def test_the_rates_at_both_ends_are_accepted(self) -> None:
        for bps in (0, 10_000):
            with self.subTest(bps=bps):
                config = self.load(config_document(artist_fee=policy_wire(fee_bps=bps)))
                self.assertEqual(config.events[0].artist_fee.fee_bps, bps)

    def test_a_malformed_block_is_a_config_error_naming_the_field(self) -> None:
        for block, expected in (
            (5, "events[0].artist_fee"),
            ([], "events[0].artist_fee"),
            ("5%", "events[0].artist_fee"),
        ):
            with self.subTest(block=block):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(artist_fee=block))
                self.assertIn(expected, str(caught.exception))

    def test_an_unknown_key_is_refused_by_name(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(artist_fee=policy_wire(fee_rate=5)))
        message = str(caught.exception)
        self.assertIn("events[0].artist_fee", message)
        self.assertIn("fee_rate", message)

    def test_a_rate_out_of_range_is_refused_with_the_path_to_the_key(self) -> None:
        for bps in (10_001, -1, 500.0, True, "500"):
            with self.subTest(bps=bps):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(artist_fee=policy_wire(fee_bps=bps)))
                self.assertIn("events[0].artist_fee.fee_bps", str(caught.exception))

    def test_a_missing_rate_or_wallet_is_refused_by_name(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(artist_fee={"fee_bps": BPS}))
        self.assertIn("events[0].artist_fee.artist_wallet", str(caught.exception))
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(artist_fee={"artist_wallet": ARTIST}))
        self.assertIn("events[0].artist_fee.fee_bps", str(caught.exception))

    def test_a_bad_wallet_is_refused_by_name(self) -> None:
        for wallet in (SHORT_WALLET, "0OIl", "", 7):
            with self.subTest(wallet=wallet):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(artist_fee=policy_wire(artist_wallet=wallet)))
                self.assertIn("events[0].artist_fee.artist_wallet", str(caught.exception))

    def test_the_refusal_is_the_loader_error_and_a_value_error(self) -> None:
        # The fee module raises `ArtistFeeError`, which is a `ValueError`; the loader re-raises it
        # as `ConfigError`, which is also a `ValueError`. A caller that catches `ConfigError` from
        # a config load catches this too, and that is the whole reason for the re-raise.
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(artist_fee=policy_wire(fee_bps=10_001)))
        self.assertIsInstance(caught.exception, ValueError)
        self.assertNotIn("Traceback", str(caught.exception))


class TestEventSpecField(unittest.TestCase):
    def test_the_fee_trails_the_required_fields_and_defaults_to_none(self) -> None:
        # `flip_tax` is appended after the fee by the wiring that added it (that order and its own
        # defaults are pinned in `test_flip_tax_wiring.py`), so the fee is no longer the last name
        # in the dataclass. What this pins is unchanged: both optional policies trail the seven
        # required fields, both default, and a seven-argument call still means what it meant.
        names = [field.name for field in fields(EventSpec)]
        self.assertEqual(names[7:], ["artist_fee", "flip_tax"])
        self.assertIsNone(spec().artist_fee)

    def test_a_spec_without_the_field_is_still_constructible_positionally(self) -> None:
        # Every existing call site passes the seven fields in order: a defaulted eighth cannot
        # break one of them.
        event = EventSpec("evt", FACE, "capped", CAP_BPS, 2, 1, 0)
        self.assertIsNone(event.artist_fee)


class TestDryRunFee(unittest.TestCase):
    """The dry-run chain prices the fee with the shared arithmetic and reports it.

    The fee is charged on a resale, so the seller in these tests is an agent reselling a unit it
    already holds. A primary sale, the house selling its own stock, is the exception and is tested
    as one: it pays nothing and still belongs to an event that has a rate.
    """

    def gateway(self) -> gw.DryRunGateway:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return gw.make_gateway("local", run_dir=Path(tmp.name), dry_run=True)

    def chain(self, artist_fee=None, **overrides):
        gateway = self.gateway()
        chain = gateway.create_event(spec(artist_fee=artist_fee, **overrides))
        chain.open_account("house")
        chain.open_account("a1")
        chain.open_account("a2")
        chain.stock(2)
        return gateway, chain

    def chain_with_a_holder(self, artist_fee=None, **overrides):
        """A chain where a1 already owns one unit, bought from the house with no fee charged."""
        gateway, chain = self.chain(artist_fee, **overrides)
        bought = chain.transfer(
            from_label=gw.HOUSE_LABEL,
            to_label="a1",
            price_lamports=PRICE,
            charge_artist_fee=False,
        )
        self.assertEqual(bought.status, "ok")
        return gateway, chain

    def test_an_admitted_resale_reports_the_fee_the_arithmetic_says(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway, chain = self.chain_with_a_holder(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, PRICE * BPS // BPS_DENOMINATOR)
        self.assertEqual(result.fee_lamports, FEE)
        self.assertTrue(gw.is_simulated(result), "the simulated marker must survive the fee path")
        self.assertTrue(
            any(ARTIST in line and "simulated" in line for line in result.logs),
            f"the fee line must name the artist and say it was simulated: {result.logs}",
        )

    def test_a_primary_sale_pays_nothing_and_says_nothing_about_a_payment(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway, chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        result = chain.transfer(
            from_label=gw.HOUSE_LABEL,
            to_label="a1",
            price_lamports=PRICE,
            charge_artist_fee=False,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)
        self.assertEqual(
            result.logs, (gw.SIMULATED_LOG,),
            "no fee was charged, so no line may claim one would have been",
        )

    def test_the_same_event_still_charges_the_resale_that_follows(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway, chain = self.chain_with_a_holder(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        resale = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(resale.fee_lamports, FEE)

    def test_a_refused_sale_reports_no_fee_because_nothing_moved(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway, chain = self.chain_with_a_holder(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        result = chain.transfer(
            from_label="a1", to_label="a2", price_lamports=CEILING + 1
        )
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.error_code, gw.E_CAP_EXCEEDED)
        self.assertEqual(result.fee_lamports, 0)
        self.assertTrue(gw.is_simulated(result))

    def test_a_zero_rate_executes_and_pays_nothing(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway, chain = self.chain_with_a_holder(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=0))
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)

    def test_an_event_with_no_policy_is_byte_for_byte_what_it_was(self) -> None:
        gateway, chain = self.chain()
        self.assertIsNone(chain.artist_fee)
        result = chain.transfer(from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)
        self.assertEqual(result.logs, (gw.SIMULATED_LOG,))

    def test_the_dry_run_chain_is_built_from_the_spec(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        policy = ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS)
        gateway, chain = self.chain(policy)
        self.assertEqual(chain.artist_fee, policy)
        self.assertIn(ARTIST, repr(chain), "a review reads the repr and must see the policy")


class TestTheMoveInstruction(unittest.TestCase):
    """The fee path's move is `dp.instruction_transfer_checked` plus one write flag.

    The message has to make the record writable somewhere, or Token-2022's CPI to the hook is
    refused `PrivilegeEscalation` and the hook never runs: v2's extra-account-metas list declares the
    record writable and an inner CPI cannot escalate. The published builder declares it read-only, so
    the fee path uses a copy of it, and this pins the copy: same program, same seven accounts in the
    same order, same ten data bytes, and the record's `is_writable` as the one difference. A
    second difference is a change to a transfer instruction nobody reviewed.
    """

    KWARGS = dict(
        source=address(6),
        mint=address(5),
        destination=address(7),
        authority=SELLER,
        record=address(4),
        hook_program=address(9),
        extra_metas=address(8),
    )

    def both(self):
        return (
            gw.dp.instruction_transfer_checked(**self.KWARGS),
            gw.instruction_transfer_checked_writable(**self.KWARGS),
        )

    def test_it_is_the_published_builder_with_the_record_writable(self) -> None:
        published, writable = self.both()
        self.assertEqual(writable.program_id, published.program_id)
        self.assertEqual(writable.data, published.data)
        self.assertEqual(len(writable.data), 10, "[12, amount u64 le, decimals]")
        self.assertEqual(
            [meta.pubkey for meta in writable.accounts],
            [meta.pubkey for meta in published.accounts],
            "the seven accounts and their order are the token program's contract",
        )
        differences = [
            (index, before, after)
            for index, (before, after) in enumerate(
                zip(published.accounts, writable.accounts)
            )
            if before != after
        ]
        self.assertEqual(len(differences), 1, f"expected exactly one difference, got {differences}")
        index, before, after = differences[0]
        self.assertEqual(index, 4, "the record is the fifth account")
        self.assertEqual(before.pubkey, self.KWARGS["record"])
        self.assertEqual((before.is_signer, before.is_writable), (False, False))
        self.assertEqual((after.is_signer, after.is_writable), (False, True))

    def test_the_signers_and_the_amounts_are_unchanged(self) -> None:
        published, writable = self.both()
        self.assertEqual(
            [meta.pubkey for meta in writable.accounts if meta.is_signer],
            [meta.pubkey for meta in published.accounts if meta.is_signer],
        )
        for amount, decimals in ((1, 0), (7, 2)):
            with self.subTest(amount=amount, decimals=decimals):
                self.assertEqual(
                    gw.instruction_transfer_checked_writable(
                        **self.KWARGS, amount=amount, decimals=decimals
                    ).data,
                    gw.dp.instruction_transfer_checked(
                        **self.KWARGS, amount=amount, decimals=decimals
                    ).data,
                )


class TestTransferResultFee(unittest.TestCase):
    def test_the_fee_defaults_to_zero_and_trails_the_chain_fields(self) -> None:
        result = gw.TransferResult(status="ok", signature="s")
        self.assertEqual(result.fee_lamports, 0)
        # The flip tax's three fields were appended after the fee (pinned in
        # `test_flip_tax_wiring.py`), so the fee no longer closes the dataclass. Every payment
        # field still defaults, which is what lets a caller that predates them construct a result
        # with the seven positional arguments it always passed.
        names = [field.name for field in fields(gw.TransferResult)]
        self.assertEqual(
            names[-4:], ["fee_lamports", "flip_tax_lamports", "flip_tax_bps", "held_seconds"],
            "the payment fields sit after the chain fields and before nothing else",
        )

    def test_a_result_built_the_old_way_still_has_every_other_field(self) -> None:
        result = gw.TransferResult(
            "refused", "sig", 7, 1_700_000_000, gw.E_CAP_EXCEEDED, 12, ("log",)
        )
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.logs, ("log",))
        self.assertEqual(result.fee_lamports, 0)


class TestSignerOrder(unittest.TestCase):
    """The signer set comes out of the compiled message, not out of an assumption."""

    def sale_message(self, *, stage_v2: bool = True, with_fee: bool = True) -> bytes:
        from market_swarm.artist_fee import sale_instructions

        stage = (
            gw.instruction_set_pending_price_v2(
                authority=ISSUER, record=address(4), mint=address(5),
                program_id=address(9), price=PRICE,
            )
            if stage_v2
            # The v1 encoder the gateway uses when there is no fee: one account, no signer. It is
            # here to show that the two signers come from the v2 stage and not from the fee leg.
            else gw.dp.instruction_set_pending_price(
                record=address(4), program_id=address(9), price=PRICE
            )
        )
        move = gw.dp.instruction_transfer_checked(
            source=address(6),
            mint=address(5),
            destination=address(7),
            authority=SELLER,
            record=address(4),
            hook_program=address(9),
            extra_metas=address(8),
        )
        legs = (
            sale_instructions(
                stage=stage, move=move, seller=SELLER, artist_wallet=ARTIST,
                price_lamports=PRICE, fee_bps=BPS,
            )
            if with_fee
            else (stage, move)
        )
        return gw.dp.compile_message(SELLER, list(legs), BLOCKHASH)

    def test_the_payer_alone_when_the_seller_signs_both_legs(self) -> None:
        message = self.sale_message(stage_v2=False, with_fee=False)
        self.assertEqual(gw.signer_keys_from_message(message), (SELLER,))

    def test_the_v2_stage_is_what_puts_the_issuer_on_the_signer_list(self) -> None:
        # Not the fee: the record's authority is the issuer, and a v2 stage without its
        # signature fails on chain. The fee leg adds an instruction and no signer.
        without_fee = gw.signer_keys_from_message(self.sale_message(with_fee=False))
        with_fee = gw.signer_keys_from_message(self.sale_message())
        self.assertEqual(without_fee, (SELLER, ISSUER))
        self.assertEqual(with_fee, without_fee)

    def test_two_signers_in_the_message_order_the_payer_first(self) -> None:
        message = self.sale_message()
        self.assertEqual(gw.signer_keys_from_message(message), (SELLER, ISSUER))

    def test_a_non_signer_is_never_reported(self) -> None:
        signers = gw.signer_keys_from_message(self.sale_message())
        for stranger in (ARTIST, address(4), address(5), gw.dp.SYSTEM_PROGRAM):
            with self.subTest(stranger=stranger):
                self.assertNotIn(stranger, signers)

    def test_the_artist_pays_nothing_and_signs_nothing(self) -> None:
        # The fee leg's source is the seller and its destination is the artist: only one of the
        # two is a signer, and it is not the one being paid.
        message = self.sale_message()
        self.assertNotIn(ARTIST, gw.signer_keys_from_message(message))

    def test_the_header_count_is_what_decides(self) -> None:
        message = bytearray(self.sale_message())
        self.assertEqual(message[0], 2)
        message[0] = 1
        self.assertEqual(gw.signer_keys_from_message(bytes(message)), (SELLER,))

    def test_a_message_that_could_not_have_been_compiled_is_a_value_error(self) -> None:
        good = bytearray(self.sale_message())
        truncated_keys = bytes(good[:3]) + bytes([30]) + bytes(len(good) - 4)
        too_many_signers = bytes([255]) + bytes(good[1:])
        for label, message in (
            ("empty", b""),
            ("header only", b"\x02\x00\x00"),
            ("keys truncated", truncated_keys),
            ("more signers than keys", too_many_signers),
        ):
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    gw.signer_keys_from_message(message)

    def test_it_refuses_something_that_is_not_bytes(self) -> None:
        with self.assertRaises(ValueError):
            gw.signer_keys_from_message("not a message")  # type: ignore[arg-type]


class FakeGateway(gw.ChainGateway):
    """A `ChainGateway` whose cluster is a dict and whose signer is a marker byte.

    Only the seams a signature path touches are replaced: `_rpc` answers the blockhash and accepts
    the send, `_confirmation` says it landed, and `_sign` records which path signed what and
    returns a signature the test can tell apart. Nothing here opens a socket, a keypair file or a
    child process, and `_send_multi` -- the code under test -- is the real one.
    """

    def __init__(self, run_dir: Path) -> None:
        super().__init__("local", run_dir=run_dir)
        self.rpc_url = "http://127.0.0.1:1"
        self.program_id = address(9)
        self.signers: list[Path] = []
        self.messages: list[bytes] = []
        self.sent: list[dict] = []
        self.balances: dict[str, int] = {}
        self.funded: list[tuple[str, int]] = []
        for label, addr in (("authority", ISSUER), ("seller", SELLER), ("buyer", address(6))):
            self._keys[label] = run_dir / "keys" / f"{label}.json"
            self._addresses[label] = addr

    # -- the seams ---------------------------------------------------------

    def _rpc(self, method, params, *, timeout=None, attempts=None):
        if method == "getLatestBlockhash":
            return {"value": {"blockhash": BLOCKHASH}}
        if method == "sendTransaction":
            self.sent.append({"wire": params[0], "skipPreflight": params[1]["skipPreflight"]})
            return SIGNATURE
        raise AssertionError(f"the fake cluster was asked for {method}")

    def _confirmation(self, signature: str) -> dict:
        return {"ok": True, "err": None, "slot": 7}

    def _sign(self, keypair_path: Path, message: bytes) -> bytes:
        self.signers.append(keypair_path)
        self.messages.append(message)
        return bytes([len(self.signers)]) * 64

    def _balance(self, addr: str) -> int:
        return self.balances.get(addr, 0)

    def _fund_wallet(self, addr: str, lamports: int) -> None:
        self.funded.append((addr, lamports))
        self.balances[addr] = self.balances.get(addr, 0) + lamports


class FakeCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.gateway = FakeGateway(self.dir)

    def stage_instruction(self):
        return gw.instruction_set_pending_price_v2(
            authority=ISSUER, record=address(4), mint=address(5),
            program_id=address(9), price=PRICE,
        )

    def fee_leg(self):
        return gw.dp.Instruction(
            program_id=gw.dp.SYSTEM_PROGRAM,
            accounts=(
                gw.dp.AccountMeta(SELLER, True, True),
                gw.dp.AccountMeta(ARTIST, False, True),
            ),
            data=(2).to_bytes(4, "little") + FEE.to_bytes(8, "little"),
        )


class TestMultiSignerSend(FakeCase):
    def send(self, instructions, signer_paths):
        return self.gateway._send_multi(
            instructions,
            payer=SELLER,
            signer_paths=signer_paths,
        )

    def both_paths(self) -> dict:
        return {
            SELLER: self.gateway._wallet_path("seller"),
            ISSUER: self.gateway._wallet_path("authority"),
        }

    def test_two_signatures_in_the_order_the_message_asks_for(self) -> None:
        signature, status, latency = self.send(
            [self.stage_instruction(), self.fee_leg()], self.both_paths()
        )
        self.assertEqual(signature, SIGNATURE)
        self.assertTrue(status["ok"])
        self.assertIsInstance(latency, int)
        self.assertEqual(
            [path.name for path in self.gateway.signers],
            ["seller.json", "authority.json"],
            "signatures are positional: the payer signs first, then the second signer",
        )
        self.assertEqual(len(self.gateway.sent), 1)
        transaction = base64.b64decode(self.gateway.sent[0]["wire"])
        # A transaction is a compact-u16 count, then that many 64-byte signatures, then the
        # message. The two markers identify which signer produced which signature.
        self.assertEqual(transaction[0], 2)
        self.assertEqual(transaction[1:65], bytes([1]) * 64)
        self.assertEqual(transaction[65:129], bytes([2]) * 64)
        self.assertEqual(transaction[129:], self.gateway.messages[0])
        self.assertFalse(self.gateway.sent[0]["skipPreflight"])

    def test_a_missing_signer_is_a_hard_error_naming_both_sides(self) -> None:
        paths = self.both_paths()
        paths.pop(ISSUER)
        with self.assertRaises(gw.ChainUnavailable) as caught:
            self.send([self.stage_instruction(), self.fee_leg()], paths)
        message = str(caught.exception)
        self.assertIn(ISSUER, message)
        self.assertIn(SELLER, message)
        self.assertIn("no keypair path", message)
        self.assertEqual(self.gateway.sent, [], "a badly signed transaction must never be sent")
        self.assertEqual(self.gateway.signers, [], "nothing may be signed before the set is checked")

    def test_an_extra_signer_is_a_hard_error_naming_both_sides(self) -> None:
        paths = self.both_paths()
        paths[ARTIST] = self.gateway._wallet_path("authority")
        with self.assertRaises(gw.ChainUnavailable) as caught:
            self.send([self.stage_instruction(), self.fee_leg()], paths)
        message = str(caught.exception)
        self.assertIn(ARTIST, message)
        self.assertIn("does not ask to sign", message)
        self.assertEqual(self.gateway.sent, [])

    def test_one_signer_still_works_through_the_multi_signer_path(self) -> None:
        signature, status, _ = self.send(
            [self.fee_leg()], {SELLER: self.gateway._wallet_path("seller")}
        )
        self.assertEqual(signature, SIGNATURE)
        self.assertTrue(status["ok"])
        self.assertEqual(len(self.gateway.signers), 1)


class SaleGateway(FakeGateway):
    """Enough of a cluster for `EventChain.transfer`, and no more.

    The account lookups all answer "it is there", so nothing tries to create one; the token
    balance is a dictionary; and the transaction read-back is fixed. The transaction itself is the
    real code: `_send_multi`, `dp.compile_message`, `dp.build_transaction` and the instruction
    builders all run, which is the point -- what is asserted below is the bytes.
    """

    def __init__(self, run_dir: Path) -> None:
        super().__init__(run_dir)
        self.held: dict[str, int] = {}
        self.err: dict | None = None

    def _token_balance(self, token_account: str) -> int:
        return self.held.get(token_account, 0)

    def _derive_address(self, program_id: str, *seeds: str) -> str:
        return address(sum(ord(c) for c in program_id + "|".join(seeds)))

    def _account_exists(self, addr: str) -> bool:
        return True

    def _wait_for_account(self, addr: str, **_kwargs) -> bool:
        return True

    def _run(self, command, *, timeout, what, check=True, cwd=None):
        raise AssertionError(f"no child process may run here: {what}")

    def _spl(self, *args):
        raise AssertionError("no solana or spl-token command may run here")

    def _confirmation(self, signature: str) -> dict:
        return {"ok": self.err is None, "err": self.err, "slot": 7}

    def _transaction(self, signature: str) -> dict:
        return {"slot": 7, "block_time": 1_700_000_000, "logs": ("Program log: admitted",)}


def decode_message(message: bytes) -> dict:
    """The legacy message format, just far enough to say what was compiled. No library."""
    at = 3

    def shortvec(index: int) -> tuple[int, int]:
        value = 0
        shift = 0
        while True:
            byte = message[index]
            index += 1
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return value, index
            shift += 7

    count, at = shortvec(at)
    keys = [
        gw.dp.base58.encode(message[at + 32 * i: at + 32 * (i + 1)]) for i in range(count)
    ]
    at += 32 * count
    at += 32  # blockhash
    instructions = []
    total, at = shortvec(at)
    for _ in range(total):
        program = keys[message[at]]
        at += 1
        accounts, at = shortvec(at)
        metas = list(message[at: at + accounts])
        at += accounts
        length, at = shortvec(at)
        data = message[at: at + length]
        at += length
        instructions.append(
            {"program": program, "accounts": [keys[index] for index in metas], "data": data}
        )
    return {"header": list(message[0:3]), "keys": keys, "instructions": instructions}


class TestTheWholeSaleIsOneTransaction(FakeCase):
    """The sale `EventChain.transfer` builds: bytes, order, signers, and what it reports."""

    def setUp(self) -> None:
        super().setUp()
        self.gateway = SaleGateway(self.dir)
        self.record = address(4)
        self.mint = address(5)

    def chain(self, artist_fee):
        cap_bps = effective_cap_bps("capped", CAP_BPS)
        chain = gw.EventChain(
            gateway=self.gateway,
            event_id="evt_fee",
            mint=self.mint,
            record=self.record,
            extra_metas=address(8),
            mode="capped",
            cap_bps=cap_bps,
            face_lamports=FACE,
            ceiling_lamports=ceiling_lamports(FACE, cap_bps),
            artist_fee=artist_fee,
        )
        self.gateway.held[chain.ticket_account("seller")] = 1
        return chain

    def sent(self) -> dict:
        self.assertEqual(len(self.gateway.sent), 1, "one sale is one transaction")
        transaction = base64.b64decode(self.gateway.sent[0]["wire"])
        count = transaction[0]
        signatures = [
            transaction[1 + 64 * i: 1 + 64 * (i + 1)] for i in range(count)
        ]
        return {
            "count": count,
            "signatures": signatures,
            "message": decode_message(transaction[1 + 64 * count:]),
            "skipPreflight": self.gateway.sent[0]["skipPreflight"],
        }

    def test_the_fee_sale_is_three_instructions_in_order(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, FEE)

        sent = self.sent()
        instructions = sent["message"]["instructions"]
        self.assertEqual(
            [step["program"] for step in instructions],
            [self.gateway.program_id, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "stage, then the fee, then the move",
        )
        # [0] the v2 stage: `[authority (signer), record (writable), mint]`, data [2] + price u64.
        stage = instructions[0]
        self.assertEqual(stage["data"], bytes([2]) + PRICE.to_bytes(8, "little"))
        self.assertEqual(stage["accounts"], [ISSUER, self.record, self.mint])
        # [1] the fee: bincode System transfer, seller to artist, exactly `fee_lamports`.
        fee = instructions[1]
        self.assertEqual(fee["data"], (2).to_bytes(4, "little") + FEE.to_bytes(8, "little"))
        self.assertEqual(fee["accounts"], [SELLER, ARTIST])
        # [2] the move, and the seller is its authority as well as its payer.
        move = instructions[2]
        self.assertEqual(move["data"], bytes([12]) + (1).to_bytes(8, "little") + bytes([0]))

    def test_two_signatures_payer_first_then_the_issuer(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        sent = self.sent()
        self.assertEqual(sent["count"], 2)
        self.assertEqual([path.name for path in self.gateway.signers],
                         ["seller.json", "authority.json"])
        self.assertEqual(len(self.gateway.messages), 2)
        self.assertEqual(self.gateway.messages[0], self.gateway.messages[1])
        self.assertFalse(sent["skipPreflight"], "an admitted price is sent through preflight")

    def test_a_primary_sale_on_a_fee_event_is_two_instructions_and_one_signature(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        # The house sells its own stock, so the seller is the issuer: the stage's authority and the
        # move's authority are the same key, the message needs one signature, and no fee is paid.
        chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        self.gateway.held[chain.ticket_account(gw.HOUSE_LABEL)] = 1
        result = chain.transfer(
            from_label=gw.HOUSE_LABEL,
            to_label="buyer",
            price_lamports=PRICE,
            charge_artist_fee=False,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)
        sent = self.sent()
        self.assertEqual(
            len(sent["message"]["instructions"]), 2,
            "the stage and the move, and no fee leg between them",
        )
        self.assertEqual(
            [step["program"] for step in sent["message"]["instructions"]],
            [self.gateway.program_id, gw.dp.TOKEN_2022_PROGRAM],
        )
        self.assertEqual(sent["count"], 1, "one key is the payer, the stage authority and the seller")
        self.assertEqual([path.name for path in self.gateway.signers], ["authority.json"])

    def test_a_zero_fee_omits_the_fee_instruction(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=0))
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)
        sent = self.sent()
        self.assertEqual(len(sent["message"]["instructions"]), 2)
        self.assertEqual(sent["count"], 2, "the v2 stage still needs the issuer's signature")

    def test_a_refused_sale_reports_6010_and_no_fee(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        chain = self.chain(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        self.gateway.err = {"InstructionError": [1, {"Custom": gw.E_CAP_EXCEEDED}]}
        result = chain.transfer(
            from_label="seller", to_label="buyer", price_lamports=CEILING + 1
        )
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.error_code, gw.E_CAP_EXCEEDED)
        self.assertEqual(
            result.fee_lamports, 0,
            "a refused transaction moved nothing, so it paid no fee",
        )
        sent = self.sent()
        self.assertTrue(sent["skipPreflight"], "a refusal has to be observable: no preflight")

    def test_the_no_fee_path_sends_the_v1_stage_and_one_signature(self) -> None:
        chain = self.chain(None)
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)
        sent = self.sent()
        self.assertEqual(sent["count"], 1)
        self.assertEqual([path.name for path in self.gateway.signers], ["seller.json"])
        instructions = sent["message"]["instructions"]
        self.assertEqual(len(instructions), 2)
        # The stage is `dp.instruction_set_pending_price`, unchanged: one account, no signer.
        self.assertEqual(instructions[0]["data"], bytes([2]) + PRICE.to_bytes(8, "little"))
        self.assertEqual(instructions[0]["accounts"], [self.record])
        self.assertEqual(
            [step["program"] for step in instructions],
            [self.gateway.program_id, gw.dp.TOKEN_2022_PROGRAM],
        )

    def test_a_primary_sale_never_reaches_the_fee_builder(self) -> None:
        from market_swarm.artist_fee import ArtistFeeError, ArtistFeePolicy

        # The artist is the house in this policy, so a sale that charged the fee would be the house
        # paying itself and `sale_instructions` refuses to build it. A primary sale charges nothing
        # and so never asks: the same event sells its own stock with no complaint.
        chain = self.chain(ArtistFeePolicy(artist_wallet=ISSUER, fee_bps=BPS))
        self.gateway.held[chain.ticket_account(gw.HOUSE_LABEL)] = 1
        with self.assertRaises(ArtistFeeError):
            chain.transfer(
                from_label=gw.HOUSE_LABEL, to_label="buyer", price_lamports=PRICE,
                charge_artist_fee=True,
            )
        result = chain.transfer(
            from_label=gw.HOUSE_LABEL, to_label="buyer", price_lamports=PRICE,
            charge_artist_fee=False,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.fee_lamports, 0)

    def test_a_sale_it_refuses_to_build_touches_no_cluster(self) -> None:
        from market_swarm.artist_fee import ArtistFeeError, ArtistFeePolicy

        # The artist is the seller: the fee would pay the seller and be logged as a fee. The
        # refusal has to happen before a blockhash is fetched, or the run pays for a signature
        # that cannot exist.
        chain = self.chain(ArtistFeePolicy(artist_wallet=SELLER, fee_bps=BPS))
        with self.assertRaises(ArtistFeeError):
            chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(self.gateway.sent, [])
        self.assertEqual(self.gateway.signers, [])


class TestWalletFloorForTheFee(FakeCase):
    """A seller funded with the fee on top of its float, through the one funding path."""

    def test_the_seller_is_funded_with_the_fee_on_top_of_its_transaction_money(self) -> None:
        self.gateway._ensure_wallet("seller", fee_lamports=FEE)
        self.assertEqual(len(self.gateway.funded), 1)
        destination, lamports = self.gateway.funded[0]
        self.assertEqual(destination, SELLER)
        self.assertGreaterEqual(
            self.gateway.balances[SELLER],
            FEE + gw.WALLET_FLOOR_LAMPORTS,
            "the seller must be able to pay the fee and still pay its own signature",
        )

    def test_no_fee_funds_exactly_what_it_always_did(self) -> None:
        self.gateway._ensure_wallet("seller")
        self.assertEqual(self.gateway.funded, [(SELLER, gw.FUND_LAMPORTS_PER_WALLET)])

    def test_a_seller_already_holding_the_fee_is_left_alone(self) -> None:
        self.gateway.balances[SELLER] = FEE + gw.WALLET_FLOOR_LAMPORTS
        self.gateway._ensure_wallet("seller", fee_lamports=FEE)
        self.assertEqual(self.gateway.funded, [])

    def test_the_house_is_never_funded(self) -> None:
        self.gateway._ensure_wallet(gw.HOUSE_LABEL, fee_lamports=FEE)
        self.assertEqual(self.gateway.funded, [])

    def test_a_negative_fee_is_refused(self) -> None:
        for bad in (-1, True, 1.5, "1000"):
            with self.subTest(fee=bad):
                with self.assertRaises(ValueError):
                    self.gateway._ensure_wallet("seller", fee_lamports=bad)


def row(**overrides) -> TradeRow:
    """A dataset row that passes every invariant the writer and the verifier promise."""
    base = dict(
        run_id="sw20261108T000000Z0000",
        seq=1,
        ts="2026-11-08T00:00:00Z",
        event_id="evt_fee",
        mode="capped",
        agent_id="a1",
        action="resell",
        ticket_id="evt_fee#0001",
        from_wallet="a1",
        to_wallet="b1",
        price_lamports=PRICE,
        face_lamports=FACE,
        cap_bps=CAP_BPS,
        ceiling_lamports=CEILING,
        markup_bps=(PRICE - FACE) * BPS_DENOMINATOR // FACE,
        status="ok",
        error_code=None,
        signature="sig",
        slot=7,
        block_time=1_700_000_000,
        latency_ms=12,
        hop_index=2,
        budget_before=0,
        budget_after=0,
        chain="simulated",
        # The program column is required on every row (it is provenance, not a default), so a
        # fixture that builds a row has to name one. v1 is the program this fake chain drives.
        program="v1",
        rationale="one resale",
    )
    base.update(overrides)
    return TradeRow(**base)


class DatasetCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, rows: list[TradeRow], name: str = "dataset.jsonl") -> Path:
        header = dict(LEDGER_HEADER)
        header["run_id"] = rows[0].run_id if rows else "sw20261108T000000Z0000"
        path = self.dir / name
        with LedgerWriter(path, header=header) as writer:
            for one in rows:
                writer.write(one)
        return path


class TestDatasetInvariant(DatasetCase):
    def test_a_dataset_with_the_fee_the_arithmetic_says_verifies(self) -> None:
        path = self.write([row(fee_lamports=FEE, artist_fee_bps=BPS)])
        self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_the_fee_can_be_recomputed_from_the_row_alone(self) -> None:
        good = row(fee_lamports=FEE, artist_fee_bps=BPS)
        self.assertEqual(good.price_lamports * good.artist_fee_bps // 10_000, good.fee_lamports)

    def test_a_row_that_overpaid_is_caught_naming_the_line_and_the_arithmetic(self) -> None:
        path = self.write([row(), row(fee_lamports=FEE + 1, artist_fee_bps=BPS)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn("line 3", message)
        self.assertIn("fee_lamports", message)
        self.assertIn(str(FEE), message)
        self.assertIn("500 bps", message)

    def test_a_row_that_underpaid_is_caught(self) -> None:
        path = self.write([row(fee_lamports=FEE - 1, artist_fee_bps=BPS)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        self.assertIn("fee_lamports", "\n".join(caught.exception.violations))

    def test_a_primary_sale_that_claims_a_fee_is_caught(self) -> None:
        # The fee is charged on resales, so a buy row carrying one is a fee the product does not
        # charge, on a sale where it would be the artist paying themselves.
        path = self.write([row(action="buy", fee_lamports=FEE, artist_fee_bps=BPS)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn("line 2", message)
        self.assertIn("primary sale", message)
        self.assertIn("resales only", message)

    def test_a_primary_sale_of_a_fee_event_verifies_when_it_paid_nothing(self) -> None:
        # The rate stays on the row, so a reader can see the event has one and that this sale paid
        # none of it; that pair is exactly what the invariant above is about.
        path = self.write([
            row(action="buy", fee_lamports=0, artist_fee_bps=BPS),
            row(action="buy", fee_lamports=None, artist_fee_bps=BPS),
            row(fee_lamports=FEE, artist_fee_bps=BPS),
        ])
        self.assertEqual(verify_dataset(path)["rows"], 3)

    def test_a_negative_fee_is_caught_even_on_a_negative_price(self) -> None:
        # The review's crafted row: a negative price floors to a negative expected fee, so the
        # arithmetic agrees with the fee unless the bound refuses it first.
        path = self.write([row(
            price_lamports=-PRICE,
            markup_bps=-20_000,
            fee_lamports=-FEE,
            artist_fee_bps=BPS,
        )])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn("negative", message)
        self.assertIn("a fee outside 0..price is not a fee", message)

    def test_a_fee_above_the_price_is_caught(self) -> None:
        path = self.write([row(fee_lamports=PRICE + 1, artist_fee_bps=BPS)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn(f"exceeds price_lamports {PRICE}", message)
        self.assertIn("a fee outside 0..price is not a fee", message)

    def test_an_executed_trade_with_a_rate_and_no_price_is_caught(self) -> None:
        # An executed trade always has a price, so a row that names a rate and no price has had its
        # price removed, and a fee cannot be checked against nothing.
        path = self.write([row(price_lamports=None, markup_bps=None, fee_lamports=0,
                               artist_fee_bps=BPS)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn("line 2", message)
        self.assertIn("cannot be checked against anything", message)

    def test_a_fee_on_a_row_that_never_sold_is_caught(self) -> None:
        for overrides in (
            dict(action="list", price_lamports=None, markup_bps=None, fee_lamports=1),
            dict(status="refused", error_code=gw.E_CAP_EXCEEDED, fee_lamports=FEE),
            dict(status="skipped", signature=None, fee_lamports=FEE),
        ):
            with self.subTest(**overrides):
                path = self.write([row(artist_fee_bps=BPS, **overrides)])
                with self.assertRaises(DatasetInvalid) as caught:
                    verify_dataset(path)
                self.assertIn(
                    "must be 0 or null", "\n".join(caught.exception.violations)
                )

    def test_zero_is_accepted_on_a_row_that_did_not_sell(self) -> None:
        path = self.write([row(action="list", price_lamports=None, markup_bps=None,
                               artist_fee_bps=BPS, fee_lamports=0)])
        self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_a_rate_outside_the_bounds_is_caught(self) -> None:
        for bps in (10_001, -1, "500", 500.0, True):
            with self.subTest(bps=bps):
                path = self.write([row(fee_lamports=0, artist_fee_bps=bps)])
                with self.assertRaises(DatasetInvalid) as caught:
                    verify_dataset(path)
                self.assertIn("artist_fee_bps", "\n".join(caught.exception.violations))

    def test_a_dataset_from_a_run_with_no_fee_is_unchanged_and_valid(self) -> None:
        path = self.write([row(), row(action="list", price_lamports=None, markup_bps=None)])
        verified = verify_dataset(path)
        self.assertEqual(verified["rows"], 2)
        written = [
            json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()[1:]
        ]
        for payload in written:
            self.assertIsNone(payload["fee_lamports"])
            self.assertIsNone(payload["artist_fee_bps"])

    def test_a_fee_with_no_rate_is_caught(self) -> None:
        # A payment to nobody: the amount is there and the rule behind it is not, so a reader
        # cannot check the fee or say what it was for. Reported, not silently accepted.
        path = self.write([row(), row(fee_lamports=FEE)])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        message = "\n".join(caught.exception.violations)
        self.assertIn("line 3", message)
        self.assertIn("artist_fee_bps", message)
        self.assertIn(str(FEE), message)

    def test_zero_or_null_with_no_rate_is_fine(self) -> None:
        for index, fee in enumerate((None, 0)):
            with self.subTest(fee=fee):
                path = self.write(
                    [row(fee_lamports=fee, artist_fee_bps=None)], name=f"no-fee-{index}.jsonl"
                )
                self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_the_columns_trail_the_row_and_default_to_none(self) -> None:
        columns = [field.name for field in fields(TradeRow)]
        # The flip tax's three columns were appended after the fee's two (their order and meaning
        # are pinned in `test_flip_tax_wiring.py`), and `synthetic` still closes the dataclass: it
        # is the label the writer checks, not a fact about a trade.
        self.assertEqual(
            columns[-6:],
            ["fee_lamports", "artist_fee_bps", "flip_tax_lamports", "flip_tax_bps",
             "held_seconds", "synthetic"],
        )
        plain = row()
        self.assertIsNone(plain.fee_lamports)
        self.assertIsNone(plain.artist_fee_bps)
        self.assertIsNone(plain.flip_tax_lamports)
        self.assertIsNone(plain.flip_tax_bps)
        self.assertIsNone(plain.held_seconds)
        self.assertIs(plain.synthetic, True)


#: What `plan` prints for the shipped example config, line for line, minus its generated run id.
#: The config names no fee, so this is also the statement that a run without one plans exactly as
#: it planned before the fee existed: not a promise in a docstring, a fixed string in a test.
class TestTheRunnerChargesResalesOnly(unittest.TestCase):
    """A real run, end to end: one fee event, a primary buy and the resale that follows.

    Every layer is the shipped one -- `SwarmRunner`, `DryRunGateway`, `LedgerWriter`,
    `verify_dataset` -- and only the cluster is simulated, so this is the test that says the fee
    reaches the row on a resale and stays off it on a primary sale. The policies are scripted, so
    the two rows exist by construction rather than by luck of a seed.
    """

    class Scripted:
        """One action per round, from a table. The runner's documented test seam."""

        name = "scripted"

        def __init__(self, rounds: dict[int, tuple[tuple[str, int], ...]]) -> None:
            self._rounds = rounds

        def decide(self, view):
            from market_swarm.agents import Intent

            return [
                Intent(
                    agent_id=view.agent_id,
                    action=action,
                    price_lamports=price,
                    ticket_id=None,
                    rationale=f"scripted {action} at {price} in round {view.round}",
                )
                for action, price in self._rounds.get(view.round, ())
            ]

    def run_it(self, artist_fee):
        from market_swarm.agents import Intent  # noqa: F401 - imported for the policies above
        from market_swarm.config import AgentSpec, RunConfig
        from market_swarm.runner import SwarmRunner

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        config = RunConfig(
            run_id="sw-fee-wiring",
            cluster="local",
            events=(spec(artist_fee=artist_fee),),
            agents=(
                AgentSpec("a1", "buyer", "w-a1", 1, 100_000_000_000, 10),
                AgentSpec("a2", "buyer", "w-a2", 2, 100_000_000_000, 10),
            ),
            total_budget_lamports=100_000_000_000,
            total_budget_actions=20,
            kill_after_seconds=None,
            out_dir=root / "out",
            dry_run=True,
            seed=3,
        )
        gateway = gw.make_gateway("local", run_dir=root / "run", dry_run=True)
        policies = {
            "a1": self.Scripted({1: (("buy", PRICE),), 2: (("resell", PRICE),)}),
            # A bid one lamport above face, so it is a secondary bid rather than a second primary
            # purchase: anything at or below face buys stock from the house and consumes the bid.
            "a2": self.Scripted({2: (("buy", PRICE + 1),)}),
        }
        summary = SwarmRunner(config, gateway, clock=lambda: 1_700_000_000.0, policies=policies).run()
        self.assertEqual(len(summary.dataset_paths), 1)
        rows = [
            json.loads(line)
            for line in Path(summary.dataset_paths[0]).read_text(encoding="utf-8").splitlines()[1:]
        ]
        return summary, rows

    def test_the_primary_buy_pays_nothing_and_the_resale_pays_the_fee(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        summary, rows = self.run_it(ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=BPS))
        buy = [row for row in rows if row["action"] == "buy" and row["status"] == "ok"]
        resale = [row for row in rows if row["action"] == "resell" and row["status"] == "ok"]
        self.assertEqual(len(buy), 1, f"expected one primary purchase, got {summary.by_status}")
        self.assertEqual(len(resale), 1, f"expected one executed resale, got {summary.by_status}")
        self.assertEqual(buy[0]["price_lamports"], PRICE)
        self.assertEqual(buy[0]["fee_lamports"], 0, "a primary sale pays no artist fee")
        self.assertEqual(buy[0]["artist_fee_bps"], BPS, "and the rate is still on the row")
        self.assertEqual(resale[0]["fee_lamports"], PRICE * BPS // 10_000)
        self.assertEqual(resale[0]["artist_fee_bps"], BPS)
        # The file the run wrote passes its own verifier, with both kinds of row in it.
        self.assertEqual(verify_dataset(summary.dataset_paths[0])["rows"], len(rows))

    def test_an_event_with_no_fee_writes_neither_column(self) -> None:
        summary, rows = self.run_it(None)
        self.assertTrue(rows)
        for one in rows:
            self.assertIsNone(one["fee_lamports"])
            self.assertIsNone(one["artist_fee_bps"])
        self.assertEqual(verify_dataset(summary.dataset_paths[0])["rows"], len(rows))


PLAN_OF_THE_EXAMPLE = [
    "cluster    local  dry_run=False  seed=7",
    # The program switch adds this line to `plan` for every run, fee or no fee; it is the run's
    # provenance and it sits under the cluster it pairs with.
    "program    v1  (deployed on devnet, four instruction tags)",
    "kill-after 180",
    "out        .swarm-runs",
    "event      evt_capped  mode=capped  face=1000000000  cap_bps=2500  ceiling=1250000000  "
    "tickets=32  rounds=12  round_seconds=3600",
    "event      evt_monitored  mode=monitored  face=1000000000  cap_bps=65535  ceiling=7553500000  "
    "tickets=32  rounds=12  round_seconds=3600",
    "agent      b1  policy=buyer  budget=3000000000 lamports  actions=120",
    "agent      b2  policy=buyer  budget=3000000000 lamports  actions=120",
    "agent      h1  policy=holder  budget=3000000000 lamports  actions=120",
    "agent      f1  policy=flipper  budget=3000000000 lamports  actions=120",
    "agent      s1  policy=scalper  budget=3000000000 lamports  actions=120",
    "agent      n1  policy=sniper  budget=3000000000 lamports  actions=120",
    "agent      p1  policy=panic  budget=3000000000 lamports  actions=120",
    "agent      f2  policy=flipper  budget=3000000000 lamports  actions=120",
    "agent      g1  policy=greater_fool  budget=8000000000 lamports  actions=120",
    "budgets    total=80000000000 lamports  actions=1200",
    "actions    at most 216 decision points (9 agents x 24 rounds)",
    "actions    hard cap 1200 actions, 80000000000 lamports notional",
    "llm        off, scripted policies",
]


class PlanCase(ConfigCase):
    def plan(self, path: Path) -> list[str]:
        """The lines `plan` prints, in process, with no subprocess and no run directory."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["plan", "--config", str(path)])
        self.assertEqual(code, 0, "plan must exit 0 for a valid config")
        return buffer.getvalue().splitlines()


class TestPlanPrintsTheFee(PlanCase):
    def test_the_shipped_example_plans_byte_for_byte_as_it_did_before_the_fee(self) -> None:
        lines = self.plan(EXAMPLE)
        self.assertRegex(lines[0], r"^run        sw\d{8}T\d{6}Z[0-9a-f]{4}$")
        self.assertEqual(lines[1:], PLAN_OF_THE_EXAMPLE)

    def test_the_only_line_a_fee_adds_is_its_own(self) -> None:
        without = self.plan(self.write(config_document()))
        with_fee = self.plan(self.write(config_document(artist_fee=policy_wire())))
        self.assertEqual(len(with_fee), len(without) + 1)
        # The generated run id is the only line that may differ between two invocations.
        self.assertEqual(with_fee[1:5], without[1:5])
        # The fee line is inserted under the event, so everything from the first agent on is the
        # same list shifted by one: `program` and the event line precede the insertion.
        self.assertEqual(with_fee[7:], without[6:])
        self.assertEqual(
            with_fee[6].strip(),
            f"fee  {BPS} bps of the sale price, paid by the seller to {ARTIST}",
            "the fee line sits under its event and names the rate and the artist",
        )

    def test_an_event_with_no_fee_prints_no_fee_line(self) -> None:
        # A prefix, not a substring: the event id in these documents is `evt_fee`, and a check that
        # looked for "fee" anywhere would either fail on that or pass on nothing.
        label = " " * 11 + "fee  "
        self.assertEqual(
            [line for line in self.plan(self.write(config_document())) if line.startswith(label)],
            [],
        )
        self.assertTrue(
            [
                line
                for line in self.plan(self.write(config_document(artist_fee=policy_wire())))
                if line.startswith(label)
            ],
            "the same document with a fee does print one, so the check above is not vacuous",
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

"""The flip tax wired into the harness: config, sale, dry run, ledger, dataset, plan.

`test_flip_tax.py` checks what `market_swarm/flip_tax.py` does on its own, and
`test_flip_tax_mutation.py` checks that its tests can fail. This file checks that the rest of the
harness uses it, and uses it the same way: a config block that parses into an `EventSpec` (or is
refused as a `ConfigError`, the type a config loader raises), a sale that reads the hold from the
record through a seam instead of waiting an hour, a toggle that off means exactly the instructions
the event built before the tax existed, a dry run that prices the tax with the same arithmetic and
still says it simulated, three ledger columns, a `verify_dataset` rule that is its own function so
the tax and the artist fee can disagree, and a `plan` line in the fee line's shape.

Four claims are deliberately about *absence*, because each is a thing a plausible implementation
would get wrong:

- a sale with `charge_flip_tax=False`, and an event with no block, build exactly the instructions
  they built before the tax existed, and never read the record or the clock;
- a record that cannot be read is a `ChainUnavailable`, and nothing is funded and nothing is
  signed: pricing a tax off a record nobody read is worse than not selling;
- a refused sale reports `flip_tax_lamports=0` and still reports the rate and the hold that were
  applied, because a refusal rolls the tax leg back with the staging;
- a dataset from an event with no tax policy carries `None` in all three columns and verifies.

No validator, no network, no keypair file, no `solana` or `spl-token` child: the one cluster here
is a dictionary of RPC answers, and the keypair paths are names that are never opened.
"""

from __future__ import annotations

import base64
import contextlib
import hashlib
import io
import json
import tempfile
import unittest
from dataclasses import fields
from pathlib import Path

from market_swarm import artist_fee as af
from market_swarm import flip_tax as ft
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

#: The operator's default schedule, as numbers this file can reason about: 15% under an hour,
#: falling linearly to 0 at 30 days.
FULL_BPS = ft.DEFAULT_FULL_BPS
FULL_HOLD = ft.DEFAULT_FULL_HOLD_SECONDS
ZERO_HOLD = ft.DEFAULT_ZERO_HOLD_SECONDS

PRICE = 1_000_000_000
FACE = PRICE
CAP_BPS = 2500
CEILING = ceiling_lamports(FACE, CAP_BPS)

#: A hold of two hours: past the flat segment, so the rate is the falling line and a test that
#: accidentally prices the full rate is caught by a different number rather than by an equal one.
TWO_HOURS = 7_200
TWO_HOUR_BPS = ft.DEFAULT_SCHEDULE.bps_for(TWO_HOURS)
TWO_HOUR_TAX = PRICE * TWO_HOUR_BPS // BPS_DENOMINATOR

#: A fixed clock, far from zero and far from any real run, so the seam is obvious in a failure.
NOW = 1_800_000_000


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
RECORD = address(4)
MINT = address(5)
EXTRA_METAS = address(8)
PROGRAM_ID = address(9)


def spec(**overrides) -> EventSpec:
    base = dict(
        event_id="evt_tax",
        face_lamports=FACE,
        mode="capped",
        cap_bps=CAP_BPS,
        tickets=4,
        rounds=2,
        round_seconds=0,
    )
    base.update(overrides)
    return EventSpec(**base)


def policy(**overrides) -> ft.FlipTaxPolicy:
    block = {"artist_wallet": ARTIST, "enabled": True}
    block.update(overrides)
    return ft.FlipTaxPolicy(**block)


def policy_wire(**overrides) -> dict:
    """The mapping a config file carries under one event's `flip_tax`."""
    block = {"artist_wallet": ARTIST, "enabled": True}
    block.update(overrides)
    return block


def schedule_wire(**overrides) -> dict:
    block = {"full_bps": FULL_BPS, "full_hold_seconds": FULL_HOLD, "zero_hold_seconds": ZERO_HOLD}
    block.update(overrides)
    return block


def config_document(**event_overrides) -> dict:
    """A whole run config, as JSON, with one event that may carry a fee and a tax block."""
    event = {
        "event_id": "evt_tax",
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


def record_bytes(held_since_unix: int, *, length: int = ft.RECORD_LEN) -> bytes:
    """A v2 `["record", mint]` account with the hook's clock at its real offset.

    Only the field the tax reads is meaningful; the rest is zeros, because a reader that also
    depended on face or cap would be a reader this module does not have.
    """
    data = bytearray(length)
    start = ft.HELD_SINCE_UNIX_OFFSET
    data[start:start + ft.HELD_SINCE_UNIX_WIDTH] = held_since_unix.to_bytes(
        ft.HELD_SINCE_UNIX_WIDTH, "little", signed=True
    )
    return bytes(data)


def account_info(data: bytes | None, *, encoding: str = "base64") -> dict:
    """The `getAccountInfo` answer a fake cluster gives for a record, or for no record."""
    if data is None:
        return {"value": None}
    return {"value": {"data": [base64.b64encode(data).decode("ascii"), encoding]}}


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


class TestConfigParsesTheTax(ConfigCase):
    def test_a_full_block_becomes_a_policy_on_that_event_only(self) -> None:
        block = policy_wire(
            schedule=schedule_wire(full_bps=1200, full_hold_seconds=600, zero_hold_seconds=86_400)
        )
        document = config_document(flip_tax=block)
        plain = dict(document["events"][0], event_id="evt_plain")
        plain.pop("flip_tax")  # the second event names no tax; the first one's must not reach it
        document["events"].append(plain)
        config = self.load(document)
        tax = config.events[0].flip_tax
        self.assertEqual(tax.artist_wallet, ARTIST)
        self.assertTrue(tax.enabled)
        self.assertEqual(tax.schedule.full_bps, 1200)
        self.assertEqual(tax.schedule.full_hold_seconds, 600)
        self.assertEqual(tax.schedule.zero_hold_seconds, 86_400)
        self.assertIsNone(config.events[1].flip_tax, "the tax is per event, not per run")

    def test_the_shipped_example_config_names_no_tax(self) -> None:
        config = load_run_config(EXAMPLE)
        self.assertTrue(config.events)
        for event in config.events:
            with self.subTest(event=event.event_id):
                self.assertIsNone(event.flip_tax)

    def test_an_explicit_null_is_no_tax(self) -> None:
        self.assertIsNone(self.load(config_document(flip_tax=None)).events[0].flip_tax)

    def test_an_omitted_wallet_inherits_the_artist_fee_wallet(self) -> None:
        document = config_document(
            artist_fee={"artist_wallet": ARTIST, "fee_bps": 500},
            flip_tax={"enabled": True},
        )
        tax = self.load(document).events[0].flip_tax
        self.assertEqual(tax.artist_wallet, ARTIST)
        self.assertTrue(tax.enabled)

    def test_a_block_that_names_a_different_wallet_is_refused_with_the_field_path(self) -> None:
        document = config_document(
            artist_fee={"artist_wallet": ARTIST, "fee_bps": 500},
            flip_tax=policy_wire(artist_wallet=address(6)),
        )
        with self.assertRaises(ConfigError) as caught:
            self.load(document)
        message = str(caught.exception)
        self.assertIn("events[0].flip_tax.artist_wallet", message)
        self.assertIn(ARTIST, message)
        self.assertIn(address(6), message)

    def test_a_tax_wallet_that_is_not_a_public_key_is_refused_by_name(self) -> None:
        for wallet in (SHORT_WALLET, "0OIl", "", 7):
            with self.subTest(wallet=wallet):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(flip_tax=policy_wire(artist_wallet=wallet)))
                self.assertIn("events[0].flip_tax.artist_wallet", str(caught.exception))

    def test_a_block_with_no_wallet_and_no_fee_is_refused_by_name(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(flip_tax={"enabled": True}))
        self.assertIn("events[0].flip_tax.artist_wallet", str(caught.exception))

    def test_enabled_defaults_to_false_and_the_default_schedule_is_the_operators(self) -> None:
        tax = self.load(config_document(flip_tax={"artist_wallet": ARTIST})).events[0].flip_tax
        self.assertFalse(tax.enabled, "a block that omits the toggle has not turned the tax on")
        self.assertEqual(tax.schedule.full_bps, FULL_BPS)
        self.assertEqual(tax.schedule.full_hold_seconds, FULL_HOLD)
        self.assertEqual(tax.schedule.zero_hold_seconds, ZERO_HOLD)

    def test_a_bad_schedule_is_refused_with_the_path_to_the_key(self) -> None:
        for schedule, expected in (
            ({"full_bps": 10_001}, "events[0].flip_tax.schedule.full_bps"),
            ({"full_hold_seconds": -1}, "events[0].flip_tax.schedule.full_hold_seconds"),
            ({"zero_hold_seconds": 0}, "events[0].flip_tax.schedule.zero_hold_seconds"),
            # A curve that ends before it starts has no falling segment. The frozen module
            # raises this one from the schedule's own constructor, which has no event path to
            # name, so `FlipTaxSchedule.from_mapping` prefixes the block's path to it; the test
            # pins the field and the rule, and the path is pinned by the two rows above.
            (
                {"full_hold_seconds": 100, "zero_hold_seconds": 100},
                "zero_hold_seconds: must be greater than full_hold_seconds",
            ),
        ):
            with self.subTest(schedule=schedule):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(flip_tax=policy_wire(schedule=schedule)))
                self.assertIn(expected, str(caught.exception))

    def test_an_unknown_key_is_refused_by_name(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(flip_tax=policy_wire(fee_rate=5)))
        message = str(caught.exception)
        self.assertIn("events[0].flip_tax", message)
        self.assertIn("fee_rate", message)

    def test_a_malformed_block_is_a_config_error_naming_the_field(self) -> None:
        for block in (5, [], "15%", True):
            with self.subTest(block=block):
                with self.assertRaises(ConfigError) as caught:
                    self.load(config_document(flip_tax=block))
                self.assertIn("events[0].flip_tax", str(caught.exception))

    def test_the_refusal_is_the_loader_error_and_a_value_error(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(config_document(flip_tax=policy_wire(schedule={"full_bps": 10_001})))
        self.assertIsInstance(caught.exception, ValueError)
        self.assertNotIn("Traceback", str(caught.exception))


class TestTheCombinedTake(ConfigCase):
    """The two seller-side payments together are the take, and a take above 100% is refused."""

    def document(self, fee_bps: int, tax_bps: int) -> dict:
        return config_document(
            artist_fee={"artist_wallet": ARTIST, "fee_bps": fee_bps},
            flip_tax=policy_wire(schedule=schedule_wire(full_bps=tax_bps)),
        )

    def test_a_take_above_the_whole_price_is_refused_naming_both_numbers_and_fields(self) -> None:
        with self.assertRaises(ConfigError) as caught:
            self.load(self.document(9000, 1500))
        message = str(caught.exception)
        self.assertIn("events[0].artist_fee.fee_bps", message)
        self.assertIn("events[0].flip_tax.schedule.full_bps", message)
        self.assertIn("9000", message)
        self.assertIn("1500", message)
        self.assertIn("10500", message)
        self.assertIn("pays to sell", message)

    def test_exactly_the_whole_price_is_allowed(self) -> None:
        # 100% is a take a seller can still receive zero from; it is the boundary, not over it.
        config = self.load(self.document(8500, 1500))
        self.assertEqual(config.events[0].flip_tax.schedule.full_bps, 1500)
        self.assertEqual(config.events[0].artist_fee.fee_bps, 8500)

    def test_a_disabled_block_does_not_count_towards_the_take(self) -> None:
        document = self.document(10_000, 1500)
        document["events"][0]["flip_tax"]["enabled"] = False
        config = self.load(document)
        self.assertFalse(config.events[0].flip_tax.enabled)

    def test_the_same_tax_with_no_fee_is_allowed(self) -> None:
        # 10000 bps of tax and no fee is still a take of the whole price, and the schedule's own
        # bound allows it; what the refusal is about is the *sum* of two rules.
        config = self.load(
            config_document(flip_tax=policy_wire(schedule=schedule_wire(full_bps=10_000)))
        )
        self.assertEqual(config.events[0].flip_tax.schedule.full_bps, 10_000)


class TestEventSpecField(unittest.TestCase):
    def test_the_tax_is_the_last_field_and_defaults_to_none(self) -> None:
        names = [field.name for field in fields(EventSpec)]
        self.assertEqual(names[-1], "flip_tax")
        self.assertIsNone(spec().flip_tax)

    def test_a_spec_without_the_field_is_still_constructible_positionally(self) -> None:
        # Every existing call site passes the seven fields in order, and the fee the eighth: a
        # defaulted ninth cannot break one of them.
        event = EventSpec("evt", FACE, "capped", CAP_BPS, 2, 1, 0)
        self.assertIsNone(event.artist_fee)
        self.assertIsNone(event.flip_tax)


class FakeGateway(gw.ChainGateway):
    """A `ChainGateway` whose cluster is a dictionary of answers and whose key is a marker byte.

    Only the seams the transfer path touches are replaced: `_rpc` answers the record read, the
    blockhash and the send, `_confirmation` and `_transaction` answer the read-back, `_sign`
    records which path signed what, and `_now` is a number the test sets. `_read_record_v2`,
    `_send_multi`, `dp.compile_message`, `dp.build_transaction` and every instruction builder are
    the real ones, so what is asserted is the wire, not a mock of it.
    """

    def __init__(
        self, run_dir: Path, *, record_data: bytes | None = None, clock: int = NOW
    ) -> None:
        super().__init__("local", run_dir=run_dir)
        self.rpc_url = "http://127.0.0.1:1"
        self.program_id = PROGRAM_ID
        self.signers: list[Path] = []
        self.messages: list[bytes] = []
        self.sent: list[dict] = []
        self.requests: list[tuple[str, list]] = []
        self.balances: dict[str, int] = {}
        self.funded: list[tuple[str, int]] = []
        self.held: dict[str, int] = {}
        self.err: dict | None = None
        self.record_data = record_data
        self.clock = clock
        for label, addr in (("authority", ISSUER), ("seller", SELLER), ("buyer", address(6))):
            self._keys[label] = run_dir / "keys" / f"{label}.json"
            self._addresses[label] = addr

    # -- the seams ---------------------------------------------------------

    def _rpc(self, method, params, *, timeout=None, attempts=None):
        self.requests.append((method, params))
        if method == "getAccountInfo":
            return account_info(self.record_data)
        if method == "getLatestBlockhash":
            return {"value": {"blockhash": BLOCKHASH}}
        if method == "sendTransaction":
            self.sent.append({"wire": params[0], "skipPreflight": params[1]["skipPreflight"]})
            return SIGNATURE
        raise AssertionError(f"the fake cluster was asked for {method}")

    def _confirmation(self, signature: str) -> dict:
        return {"ok": self.err is None, "err": self.err, "slot": 7}

    def _transaction(self, signature: str) -> dict:
        return {"slot": 7, "block_time": 1_700_000_000, "logs": ("Program log: admitted",)}

    def _sign(self, keypair_path: Path, message: bytes) -> bytes:
        self.signers.append(keypair_path)
        self.messages.append(message)
        return bytes([len(self.signers)]) * 64

    def _now(self) -> int:
        return self.clock

    # -- the rest of the surface the sale touches ---------------------------

    def _balance(self, addr: str) -> int:
        return self.balances.get(addr, 0)

    def _fund_wallet(self, addr: str, lamports: int) -> None:
        self.funded.append((addr, lamports))
        self.balances[addr] = self.balances.get(addr, 0) + lamports

    def _token_balance(self, token_account: str) -> int:
        return self.held.get(token_account, 0)

    def _derive_address(self, program_id: str, *seeds: str) -> str:
        # A sha256 of the seeds, not a fold of them: a fold collides with the constant-byte
        # addresses above (and with itself), and two accounts sharing a key would make the
        # writability assertions below meaningless.
        return gw.dp.base58.encode(
            hashlib.sha256((program_id + "|" + "|".join(seeds)).encode()).digest()
        )

    def _account_exists(self, addr: str) -> bool:
        return True

    def _wait_for_account(self, addr: str, **_kwargs) -> bool:
        return True

    def _run(self, command, *, timeout, what, check=True, cwd=None):
        raise AssertionError(f"no child process may run here: {what}")

    def _spl(self, *args):
        raise AssertionError("no solana or spl-token command may run here")

    # -- what the test reads ------------------------------------------------

    def methods(self) -> list[str]:
        return [method for method, _params in self.requests]


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


def writable_keys(message: bytes) -> set[str]:
    """The account keys a compiled message declares writable.

    A legacy message orders its keys `[writable signers][read-only signers][writable
    non-signers][read-only non-signers]`, and the header's three bytes are the signer count and
    how many of each group are read-only. A key is writable for the transaction if any
    instruction says so, which is exactly why a sale cannot be told apart by its message alone:
    the stage always asks for the record writable, so the move's own flag is the only place the
    difference lives. `test_the_taxed_move_is_the_writable_builder` is the check that reads that
    flag rather than the message.
    """
    decoded = decode_message(message)
    signers, readonly_signers, readonly_unsigned = decoded["header"]
    keys = decoded["keys"]
    writable = set(keys[: signers - readonly_signers])
    writable.update(keys[signers: len(keys) - readonly_unsigned])
    return writable


class CreateEventGateway(FakeGateway):
    """`FakeGateway` with the cluster-shaped half of `create_event` replaced.

    A mint, a record and two addresses are attributes on a real chain and transactions on a real
    cluster; here they are constants, so the method body that wires a spec to a chain -- including
    the line that carries the flip tax -- runs as shipped.
    """

    def _require_started(self) -> None:
        return None

    def _create_mint(self, spec: EventSpec) -> str:
        return MINT

    def _init_extra_metas(self, **kwargs) -> None:
        return None

    def _init_record(self, **kwargs) -> None:
        return None

    def _record_until(self, record: str, *, face: int, cap_bps: int) -> dict:
        return {"face_lamports": face, "cap_bps": cap_bps}


class SaleCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def gateway(self, *, record_data: bytes | None = None, clock: int = NOW) -> FakeGateway:
        gateway = FakeGateway(self.dir, record_data=record_data, clock=clock)
        self.gateway_obj = gateway
        return gateway

    def chain(self, gateway: FakeGateway, *, artist_fee=None, flip_tax=None):
        chain = gw.EventChain(
            gateway=gateway,
            event_id="evt_tax",
            mint=MINT,
            record=RECORD,
            extra_metas=EXTRA_METAS,
            mode="capped",
            cap_bps=effective_cap_bps("capped", CAP_BPS),
            face_lamports=FACE,
            ceiling_lamports=ceiling_lamports(FACE, effective_cap_bps("capped", CAP_BPS)),
            artist_fee=artist_fee,
            flip_tax=flip_tax,
        )
        gateway.held[chain.ticket_account("seller")] = 1
        return chain

    def sent(self, gateway: FakeGateway) -> dict:
        self.assertEqual(len(gateway.sent), 1, "one sale is one transaction")
        transaction = base64.b64decode(gateway.sent[0]["wire"])
        count = transaction[0]
        signatures = [transaction[1 + 64 * i: 1 + 64 * (i + 1)] for i in range(count)]
        message = transaction[1 + 64 * count:]
        return {
            "count": count,
            "signatures": signatures,
            "message": decode_message(message),
            "writable": writable_keys(message),
            "raw": message,
            "skipPreflight": gateway.sent[0]["skipPreflight"],
        }


class TestTheRecordRead(SaleCase):
    def test_it_returns_the_raw_bytes_of_a_present_record(self) -> None:
        data = record_bytes(NOW - TWO_HOURS)
        gateway = self.gateway(record_data=data)
        self.assertEqual(gateway._read_record_v2(RECORD), data)
        method, params = gateway.requests[-1]
        self.assertEqual(method, "getAccountInfo")
        self.assertEqual(params[0], RECORD)
        self.assertEqual(
            params[1], {"encoding": "base64", "commitment": "confirmed"},
            "the read is at confirmed commitment, or a just-written clock reads back as its old "
            "value",
        )

    def test_an_absent_record_is_chain_unavailable_and_names_it(self) -> None:
        gateway = self.gateway(record_data=None)
        with self.assertRaises(gw.ChainUnavailable) as caught:
            gateway._read_record_v2(RECORD)
        self.assertIn(RECORD, str(caught.exception))
        self.assertIn("not on chain", str(caught.exception))

    def test_a_record_that_is_not_base64_is_chain_unavailable(self) -> None:
        for payload in (
            account_info(record_bytes(0), encoding="jsonParsed"),
            {"value": {"data": "not a list"}},
            {"value": {}},
        ):
            with self.subTest(payload=payload):
                gateway = FakeGateway(self.dir)
                gateway._rpc = lambda method, params, **_kwargs: payload
                with self.assertRaises(gw.ChainUnavailable):
                    gateway._read_record_v2(RECORD)


class TestTheTaxSale(SaleCase):
    def test_a_taxed_resale_with_a_fee_is_four_instructions_and_two_signers(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        fee_policy = ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=500)
        chain = self.chain(gateway, artist_fee=fee_policy, flip_tax=policy())
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)

        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, TWO_HOUR_TAX)
        self.assertEqual(result.flip_tax_bps, TWO_HOUR_BPS)
        self.assertEqual(result.held_seconds, TWO_HOURS)
        # Two hours is inside the falling segment, so the rate is neither the full rate nor zero.
        self.assertNotEqual(TWO_HOUR_BPS, FULL_BPS)
        self.assertNotEqual(TWO_HOUR_BPS, 0)

        sent = self.sent(gateway)
        instructions = sent["message"]["instructions"]
        self.assertEqual(
            [step["program"] for step in instructions],
            [PROGRAM_ID, gw.dp.SYSTEM_PROGRAM, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "stage, artist fee, flip tax, move -- the tax leg last before the move",
        )
        # [0] the v2 stage: `[authority (signer), record (writable), mint]`.
        self.assertEqual(instructions[0]["data"], bytes([2]) + PRICE.to_bytes(8, "little"))
        self.assertEqual(instructions[0]["accounts"], [ISSUER, RECORD, MINT])
        # [1] the artist fee, unchanged by the tax beside it.
        fee = PRICE * 500 // BPS_DENOMINATOR
        self.assertEqual(
            instructions[1]["data"], (2).to_bytes(4, "little") + fee.to_bytes(8, "little")
        )
        self.assertEqual(instructions[1]["accounts"], [SELLER, ARTIST])
        # [2] the tax: seller to the artist wallet, exactly the arithmetic's number.
        self.assertEqual(
            instructions[2]["data"], (2).to_bytes(4, "little") + TWO_HOUR_TAX.to_bytes(8, "little")
        )
        self.assertEqual(instructions[2]["accounts"], [SELLER, ARTIST])
        # [3] the move.
        self.assertEqual(
            instructions[3]["data"], bytes([12]) + (1).to_bytes(8, "little") + bytes([0])
        )
        self.assertEqual(sent["count"], 2)
        self.assertEqual(
            [path.name for path in gateway.signers], ["seller.json", "authority.json"]
        )

    def test_the_record_is_read_before_the_blockhash_and_before_anything_is_signed(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(gateway, flip_tax=policy())
        chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(
            gateway.methods()[:3], ["getAccountInfo", "getLatestBlockhash", "sendTransaction"],
            "the hold is read before the sale is priced and sent",
        )
        self.assertEqual(len(gateway.messages), 2)

    def test_the_log_line_names_the_tax_the_rate_and_the_hold(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        result = self.chain(gateway, flip_tax=policy()).transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE
        )
        self.assertEqual(result.status, "ok")
        lines = [line for line in result.logs if "flip tax" in line]
        self.assertEqual(len(lines), 1, f"exactly one tax line in {result.logs}")
        line = lines[0]
        self.assertIn(str(TWO_HOUR_TAX), line)
        self.assertIn(f"{TWO_HOUR_BPS} bps", line)
        self.assertIn(f"{TWO_HOURS}s", line)
        self.assertTrue(line.startswith("ticketpath: "), "the same voice as the other log lines")

    def test_the_unknown_hold_pays_the_full_rate_and_the_log_says_unknown(self) -> None:
        gateway = self.gateway(record_data=record_bytes(ft.UNKNOWN_HOLD))
        result = self.chain(gateway, flip_tax=policy()).transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_bps, FULL_BPS)
        self.assertEqual(result.flip_tax_lamports, PRICE * FULL_BPS // BPS_DENOMINATOR)
        self.assertIsNone(result.held_seconds)
        self.assertIn("held unknown", " ".join(result.logs))

    def test_the_clock_is_the_seam_and_not_the_wall_clock(self) -> None:
        # `held_since_unix` is what the hook wrote; `now` is `_now()`. A test that used
        # `time.time()` here could not price a 30-day hold, and a gateway that did would price
        # every hold as zero seconds.
        gateway = self.gateway(record_data=record_bytes(NOW - ZERO_HOLD), clock=NOW)
        result = self.chain(gateway, flip_tax=policy()).transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE
        )
        self.assertEqual(result.held_seconds, ZERO_HOLD)
        self.assertEqual(result.flip_tax_bps, 0)
        self.assertEqual(result.flip_tax_lamports, 0)

    def test_a_hold_in_the_future_is_zero_seconds_and_the_full_rate(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW + 500), clock=NOW)
        result = self.chain(gateway, flip_tax=policy()).transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE
        )
        self.assertEqual(result.held_seconds, 0)
        self.assertEqual(result.flip_tax_bps, FULL_BPS)

    def test_a_taxed_event_with_no_fee_stages_v2_and_moves_a_writable_record(self) -> None:
        # The v1 stage encoder cannot stage a v2 record and `dp`'s move names the record
        # read-only, which Token-2022 refuses with `PrivilegeEscalation`; a taxed event with no
        # fee must still be able to stage and move, so it takes the v2 builders.
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(gateway, flip_tax=policy())
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        sent = self.sent(gateway)
        instructions = sent["message"]["instructions"]
        self.assertEqual(
            [step["program"] for step in instructions],
            [PROGRAM_ID, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "stage, tax, move",
        )
        self.assertEqual(instructions[0]["accounts"], [ISSUER, RECORD, MINT], "the v2 stage")
        self.assertIn(RECORD, sent["writable"])
        self.assertEqual(sent["count"], 2, "the issuer signs the stage, the seller the move")

    def test_the_taxed_move_is_the_writable_builder(self) -> None:
        # The message cannot show it: the stage asks for the record writable either way, and a
        # key is writable for the transaction if any instruction says so. So the builder is
        # recorded as it is called. `test_artist_fee_wiring.py` pins what the two builders differ
        # by; this pins which one the taxed path takes.
        original = gw.instruction_transfer_checked_writable
        calls: list[dict] = []

        def recorder(**kwargs):
            calls.append(kwargs)
            return original(**kwargs)

        gw.instruction_transfer_checked_writable = recorder
        self.addCleanup(setattr, gw, "instruction_transfer_checked_writable", original)
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(gateway, flip_tax=policy())
        chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(len(calls), 1, "the taxed sale builds its move once")
        self.assertEqual(calls[0]["record"], RECORD)
        self.assertEqual(calls[0]["amount"], 1)

    def test_an_event_with_no_tax_keeps_the_v1_stage(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        result = self.chain(gateway).transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE
        )
        self.assertEqual(result.status, "ok")
        sent = self.sent(gateway)
        instructions = sent["message"]["instructions"]
        self.assertEqual(instructions[0]["accounts"], [RECORD], "the v1 stage, unchanged")
        self.assertEqual(sent["count"], 1)
        self.assertNotIn("getAccountInfo", gateway.methods(), "no tax, no record read")
        self.assertEqual(result.logs, ("Program log: admitted",), "and no line about a tax")

    def test_the_toggle_off_builds_exactly_the_artist_fee_legs(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(
            gateway,
            artist_fee=ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=500),
            flip_tax=policy(),
        )
        result = chain.transfer(
            from_label="seller", to_label="buyer", price_lamports=PRICE, charge_flip_tax=False
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)
        sent = self.sent(gateway)
        self.assertEqual(
            [step["program"] for step in sent["message"]["instructions"]],
            [PROGRAM_ID, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "the fee sale's three instructions, and no tax leg",
        )
        self.assertEqual(sent["count"], 2)
        self.assertNotIn("getAccountInfo", gateway.methods(), "a toggle-off sale reads no record")
        self.assertEqual([line for line in result.logs if "flip tax" in line], [])

    def test_a_disabled_block_builds_the_sale_it_builds_without_one(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(gateway, flip_tax=policy(enabled=False))
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertEqual(self.sent(gateway)["count"], 1)
        self.assertNotIn("getAccountInfo", gateway.methods())

    def test_a_primary_sale_on_a_taxed_event_stages_v2_and_reads_no_record(self) -> None:
        # The event's policy decides the record shape; the flag decides the payment. A primary
        # sale pays no tax and reads no clock, and it still stages v2 so the record can be written
        # -- otherwise a taxed event's own stock could not be sold in a live run.
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(gateway, flip_tax=policy())
        gateway.held[chain.ticket_account(gw.HOUSE_LABEL)] = 1
        result = chain.transfer(
            from_label=gw.HOUSE_LABEL, to_label="buyer", price_lamports=PRICE,
            charge_flip_tax=False,
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)
        sent = self.sent(gateway)
        instructions = sent["message"]["instructions"]
        self.assertEqual(len(instructions), 2, "the stage and the move, and no tax leg")
        self.assertEqual(instructions[0]["accounts"], [ISSUER, RECORD, MINT], "the v2 stage")
        self.assertEqual(sent["count"], 1, "the house is the seller and the issuer: one key")
        self.assertNotIn("getAccountInfo", gateway.methods(), "a primary sale reads no clock")
        self.assertEqual([line for line in result.logs if "flip tax" in line], [])

    def test_a_record_that_cannot_be_read_is_a_chain_unavailable_and_nothing_is_signed(
        self,
    ) -> None:
        for label, data in (("absent", None), ("too short", b"\x00" * 19)):
            with self.subTest(record=label):
                gateway = self.gateway(record_data=data)
                chain = self.chain(gateway, flip_tax=policy())
                with self.assertRaises(gw.ChainUnavailable) as caught:
                    chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
                self.assertIn(RECORD, str(caught.exception))
                self.assertEqual(gateway.sent, [], "nothing reached the cluster")
                self.assertEqual(gateway.signers, [], "nothing was signed")
                self.assertEqual(gateway.funded, [], "the seller was not even funded")
                self.assertNotIn(
                    "getLatestBlockhash", gateway.methods(),
                    "the sale stopped before a blockhash was fetched",
                )

    def test_a_refused_sale_reports_no_tax_and_keeps_the_rate_and_the_hold(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        gateway.err = {"InstructionError": [3, {"Custom": gw.E_CAP_EXCEEDED}]}
        chain = self.chain(gateway, flip_tax=policy())
        result = chain.transfer(
            from_label="seller", to_label="buyer", price_lamports=CEILING + 1
        )
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.error_code, gw.E_CAP_EXCEEDED)
        self.assertEqual(
            result.flip_tax_lamports, 0,
            "a refused transaction rolled the tax leg back, so it paid nothing",
        )
        self.assertEqual(result.flip_tax_bps, TWO_HOUR_BPS, "the rate that was applied is kept")
        self.assertEqual(result.held_seconds, TWO_HOURS)
        self.assertTrue([line for line in result.logs if "flip tax" in line])

    def test_a_preflight_rejection_reports_no_tax_and_keeps_the_rate(self) -> None:
        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))

        def refuse(method, params, **kwargs):
            if method == "sendTransaction":
                raise gw.dp.PublishError("preflight failed")
            if method == "getLatestBlockhash":
                return {"value": {"blockhash": BLOCKHASH}}
            return account_info(gateway.record_data)

        gateway._rpc = refuse
        chain = self.chain(gateway, flip_tax=policy())
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        self.assertEqual(result.status, "error")
        self.assertIsNone(result.signature, "a preflight rejection produced no signature")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertEqual(result.flip_tax_bps, TWO_HOUR_BPS)
        self.assertEqual(result.held_seconds, TWO_HOURS)

    def test_the_seller_is_funded_for_the_fee_and_the_tax(self) -> None:
        from market_swarm.artist_fee import ArtistFeePolicy

        gateway = self.gateway(record_data=record_bytes(NOW - TWO_HOURS))
        chain = self.chain(
            gateway,
            artist_fee=ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=500),
            flip_tax=policy(),
        )
        chain.transfer(from_label="seller", to_label="buyer", price_lamports=PRICE)
        fee = PRICE * 500 // BPS_DENOMINATOR
        self.assertEqual(len(gateway.funded), 1)
        destination, lamports = gateway.funded[0]
        self.assertEqual(destination, SELLER)
        self.assertGreaterEqual(lamports, fee + TWO_HOUR_TAX + gw.WALLET_FLOOR_LAMPORTS)
        self.assertGreaterEqual(
            gateway.balances[SELLER], fee + TWO_HOUR_TAX + gw.WALLET_FLOOR_LAMPORTS
        )

    def test_the_tax_is_assessed_on_the_price_the_sale_stages(self) -> None:
        # The tax is a fraction of the staged price, like the fee: at a price below one lamport
        # per 10 000 bps it rounds to zero and no leg is built at all.
        gateway = self.gateway(record_data=record_bytes(ft.UNKNOWN_HOLD))
        chain = self.chain(gateway, flip_tax=policy())
        result = chain.transfer(from_label="seller", to_label="buyer", price_lamports=6)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_bps, FULL_BPS)
        self.assertEqual(result.flip_tax_lamports, 0, "6 lamports at 1500 bps rounds to 0")
        self.assertEqual(
            len(self.sent(gateway)["message"]["instructions"]), 2,
            "a zero tax builds no leg, exactly as a zero fee builds none",
        )

    def test_a_policy_that_is_not_a_policy_is_refused_before_the_validator_boots(self) -> None:
        with self.assertRaises(ValueError) as caught:
            gw._check_spec(spec(flip_tax={"enabled": True}))
        self.assertIn("spec.flip_tax", str(caught.exception))

    def test_a_hand_built_spec_cannot_build_a_take_above_the_price(self) -> None:
        # The loader refuses this event, and so must the checkout: a spec built in code never
        # passes through a config file, and review measured a 10 000 bps fee plus a 1 500 bps tax
        # building a four-instruction sale in which the seller paid 115% of the price, which the
        # chain accepted. `_check_spec` is the door every construction path goes through.
        take_over = spec(
            artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_000),
            flip_tax=policy(),
        )
        with self.assertRaises(ValueError) as caught:
            gw._check_spec(take_over)
        message = str(caught.exception)
        self.assertIn("10000", message)
        self.assertIn("1500", message)
        self.assertIn("11500", message)
        self.assertIn("pays to sell", message)

    def test_exactly_the_whole_price_is_allowed_through_the_same_door(self) -> None:
        # The boundary is 10 000 and it is allowed: 100% is a take a seller can still receive
        # nothing from. A refusal one bps early would be the off-by-one this test exists for.
        at_the_boundary = spec(
            artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=8_500),
            flip_tax=policy(),
        )
        self.assertEqual(gw._check_spec(at_the_boundary), (CAP_BPS, FACE))

    def test_a_disabled_policy_does_not_count_towards_the_take(self) -> None:
        # A policy that charges nothing cannot overcharge, so the sum is of the rules that apply.
        disabled = ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled=False, schedule=ft.DEFAULT_SCHEDULE)
        self.assertEqual(
            gw._check_spec(
                spec(
                    artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_000),
                    flip_tax=disabled,
                )
            ),
            (CAP_BPS, FACE),
        )

    def test_the_chain_carries_the_policy_from_the_spec(self) -> None:
        policy_obj = policy()
        gateway = self.gateway(record_data=record_bytes(0))
        chain = self.chain(gateway, flip_tax=policy_obj)
        self.assertEqual(chain.flip_tax, policy_obj)
        self.assertIn(ARTIST, repr(chain), "a review reads the repr and must see the policy")

    def test_a_chain_constructed_directly_cannot_build_a_take_above_the_price(self) -> None:
        # `EventChain` is public: `create_event` and the loader are not the only doors, and review
        # built a 11 500-bps sale by calling the class itself. The refusal is repeated in `__init__`
        # so the rule does not depend on which door a caller used.
        with self.assertRaises(ValueError) as caught:
            gw.EventChain(
                gateway=None,
                event_id="evt_direct",
                mint=address(1),
                record=RECORD,
                extra_metas=address(5),
                mode="capped",
                cap_bps=CAP_BPS,
                face_lamports=FACE,
                ceiling_lamports=CEILING,
                artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=10_000),
                flip_tax=policy(),
            )
        message = str(caught.exception)
        self.assertIn("EventChain", message)
        self.assertIn("11500", message)

    def test_the_loader_and_the_checkout_share_one_definition_of_the_bound(self) -> None:
        # One function (`flip_tax.combined_take_bps`) and three callers: the loader, `_check_spec`
        # and `EventChain.__init__`. A review made the loader's own arithmetic disagree with the
        # gateway's by changing `MAX_BPS`, which is what two definitions of one rule buy you.
        import inspect

        from market_swarm import config as config_module

        self.assertIn("combined_take_bps", inspect.getsource(config_module._parse_event))
        self.assertIn("combined_take_bps", inspect.getsource(gw._refuse_combined_take))
        self.assertEqual(
            ft.combined_take_bps(artist_fee_bps=8_500, schedule=ft.DEFAULT_SCHEDULE), 10_000
        )
        self.assertEqual(
            ft.combined_take_bps(artist_fee_bps=8_500, schedule=ft.FlipTaxSchedule(full_bps=0)),
            8_500,
        )

    def test_create_event_passes_the_specs_policy_onto_the_chain(self) -> None:
        # The one line in `create_event` this change adds, exercised through the real method with
        # the cluster-shaped steps replaced: the spec's policy is what the chain carries, and an
        # event without one builds a chain with none.
        policy_obj = policy()
        gateway = CreateEventGateway(self.dir)
        self.assertEqual(gateway.create_event(spec(flip_tax=policy_obj)).flip_tax, policy_obj)
        self.assertIsNone(gateway.create_event(spec(event_id="evt_plain")).flip_tax)


class ClockedDryRunChain(gw.DryRunEventChain):
    """A dry-run chain whose clock a test sets, so a 30-day hold is not a 30-day test."""

    def __init__(self, *args, clock: int = NOW, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.clock = clock

    def _now(self) -> int:
        return self.clock


def dry_chain(flip_tax=None, *, clock: int = NOW, artist_fee=None) -> ClockedDryRunChain:
    cap_bps = effective_cap_bps("capped", CAP_BPS)
    chain = ClockedDryRunChain(
        spec(artist_fee=artist_fee, flip_tax=flip_tax),
        mode="capped",
        cap_bps=cap_bps,
        face_lamports=FACE,
        ceiling=ceiling_lamports(FACE, cap_bps),
        clock=clock,
    )
    chain.open_account("house")
    chain.open_account("a1")
    chain.open_account("a2")
    chain.stock(2)
    return chain


class TestDryRunTax(unittest.TestCase):
    def test_an_event_with_no_block_keeps_the_one_line_it_had(self) -> None:
        chain = dry_chain()
        self.assertIsNone(chain.flip_tax)
        result = chain.transfer(from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)
        self.assertEqual(result.logs, (gw.SIMULATED_LOG,))

    def test_the_tax_is_the_real_arithmetic_and_the_line_names_it(self) -> None:
        chain = dry_chain(policy(), clock=NOW)
        chain.transfer(from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE)
        chain.clock = NOW + TWO_HOURS
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_bps, TWO_HOUR_BPS)
        self.assertEqual(result.flip_tax_lamports, TWO_HOUR_TAX)
        self.assertEqual(result.held_seconds, TWO_HOURS)
        self.assertIsNone(result.signature, "a simulated sale never carries a signature")
        self.assertTrue(gw.is_simulated(result))
        lines = [line for line in result.logs if "flip tax" in line]
        self.assertEqual(len(lines), 1)
        self.assertIn(ARTIST, lines[0])
        self.assertIn(f"{TWO_HOUR_TAX} lamports", lines[0])
        self.assertIn(f"{TWO_HOUR_BPS} bps", lines[0])
        self.assertIn(f"{TWO_HOURS}s", lines[0])
        self.assertTrue(lines[0].startswith("simulated: "))

    def test_the_hold_clock_starts_unknown_and_is_stamped_by_a_simulated_transfer(self) -> None:
        chain = dry_chain(policy(), clock=NOW)
        self.assertEqual(chain._held_since, {}, "unknown is the empty dict, not zero")
        chain.transfer(from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE)
        self.assertEqual(chain._held_since["a1"], NOW)
        chain.clock = NOW + ZERO_HOLD
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(result.held_seconds, ZERO_HOLD)
        self.assertEqual(result.flip_tax_bps, 0, "30 days is the zero point")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertEqual(chain._held_since["a2"], NOW + ZERO_HOLD)

    def test_a_label_that_never_bought_is_charged_the_full_rate(self) -> None:
        chain = dry_chain(policy(), clock=NOW)
        chain._held["a1"] = 1  # a ticket in hand and no clock: the unknown hold, literally
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=PRICE)
        self.assertEqual(result.flip_tax_bps, FULL_BPS)
        self.assertIsNone(result.held_seconds)
        self.assertIn("held unknown", " ".join(result.logs))

    def test_a_primary_sale_pays_no_tax_and_says_nothing_about_one(self) -> None:
        chain = dry_chain(policy())
        result = chain.transfer(
            from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE, charge_flip_tax=False
        )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)
        self.assertEqual(result.logs, (gw.SIMULATED_LOG,))
        self.assertEqual(
            chain._held_since["a1"], NOW,
            "the hold clock still starts: the ticket moved, whichever flags this sale carried",
        )

    def test_a_refused_sale_reports_no_tax_and_keeps_the_rate_and_the_hold(self) -> None:
        chain = dry_chain(policy(), clock=NOW)
        chain._held_since["a1"] = NOW - TWO_HOURS
        chain._held["a1"] = 1
        result = chain.transfer(from_label="a1", to_label="a2", price_lamports=CEILING + 1)
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertEqual(result.flip_tax_bps, TWO_HOUR_BPS)
        self.assertEqual(result.held_seconds, TWO_HOURS)
        self.assertIsNone(result.signature)
        self.assertTrue([line for line in result.logs if "flip tax" in line])

    def test_a_disabled_block_prices_nothing(self) -> None:
        chain = dry_chain(policy(enabled=False))
        result = chain.transfer(from_label=gw.HOUSE_LABEL, to_label="a1", price_lamports=PRICE)
        self.assertEqual(result.status, "ok")
        self.assertIsNone(result.flip_tax_bps)
        self.assertEqual(result.logs, (gw.SIMULATED_LOG,))

    def test_the_event_chain_is_built_from_the_spec(self) -> None:
        policy_obj = policy()
        chain = dry_chain(policy_obj)
        self.assertEqual(chain.flip_tax, policy_obj)
        self.assertIn(ARTIST, repr(chain))


class TestTransferResultTax(unittest.TestCase):
    def test_the_money_defaults_to_zero_and_the_rate_fields_to_none(self) -> None:
        result = gw.TransferResult(status="ok", signature="s")
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)

    def test_the_three_fields_follow_the_fee_and_close_the_dataclass(self) -> None:
        names = [field.name for field in fields(gw.TransferResult)]
        self.assertEqual(
            names[-4:], ["fee_lamports", "flip_tax_lamports", "flip_tax_bps", "held_seconds"]
        )

    def test_a_result_built_the_old_way_is_unchanged(self) -> None:
        result = gw.TransferResult(
            "refused", "sig", 7, 1_700_000_000, gw.E_CAP_EXCEEDED, 12, ("log",)
        )
        self.assertEqual(result.fee_lamports, 0)
        self.assertEqual(result.flip_tax_lamports, 0)
        self.assertIsNone(result.flip_tax_bps)
        self.assertIsNone(result.held_seconds)


def row(**overrides) -> TradeRow:
    """A dataset row that passes every invariant the writer and the verifier promise."""
    base = dict(
        run_id="sw20261108T000000Z0000",
        seq=1,
        ts="2026-11-08T00:00:00Z",
        event_id="evt_tax",
        mode="capped",
        agent_id="a1",
        action="resell",
        ticket_id="evt_tax#0001",
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


def write_rows(directory: Path, rows: list[TradeRow], name: str = "dataset.jsonl") -> Path:
    header = dict(LEDGER_HEADER)
    header["run_id"] = rows[0].run_id if rows else "sw20261108T000000Z0000"
    path = directory / name
    with LedgerWriter(path, header=header) as writer:
        for one in rows:
            writer.write(one)
    return path


class DatasetCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def write(self, rows: list[TradeRow], name: str = "dataset.jsonl") -> Path:
        return write_rows(self.dir, rows, name)

    def violations(self, one: TradeRow) -> str:
        path = self.write([one])
        with self.assertRaises(DatasetInvalid) as caught:
            verify_dataset(path)
        return "\n".join(caught.exception.violations)


class TestLedgerColumns(DatasetCase):
    def test_the_three_columns_default_to_none_and_sit_after_the_fee(self) -> None:
        names = [field.name for field in fields(TradeRow)]
        index = names.index("artist_fee_bps")
        self.assertEqual(
            names[index + 1: index + 4],
            ["flip_tax_lamports", "flip_tax_bps", "held_seconds"],
        )
        self.assertEqual(names[-1], "synthetic")
        plain = row()
        self.assertIsNone(plain.flip_tax_lamports)
        self.assertIsNone(plain.flip_tax_bps)
        self.assertIsNone(plain.held_seconds)

    def test_a_written_row_carries_them(self) -> None:
        path = self.write([row(flip_tax_lamports=TWO_HOUR_TAX, flip_tax_bps=TWO_HOUR_BPS,
                               held_seconds=TWO_HOURS)])
        payload = json.loads(path.read_text(encoding="utf-8").splitlines()[1])
        self.assertEqual(payload["flip_tax_lamports"], TWO_HOUR_TAX)
        self.assertEqual(payload["flip_tax_bps"], TWO_HOUR_BPS)
        self.assertEqual(payload["held_seconds"], TWO_HOURS)

    def test_a_dataset_with_no_tax_columns_still_verifies(self) -> None:
        path = self.write([row(), row(action="list", price_lamports=None, markup_bps=None)])
        self.assertEqual(verify_dataset(path)["rows"], 2)


class TestDatasetInvariant(DatasetCase):
    def test_a_tax_the_arithmetic_says_verifies(self) -> None:
        path = self.write([
            row(flip_tax_lamports=TWO_HOUR_TAX, flip_tax_bps=TWO_HOUR_BPS, held_seconds=TWO_HOURS),
            row(held_seconds=None),
        ])
        self.assertEqual(verify_dataset(path)["rows"], 2)

    def test_the_tax_can_be_recomputed_from_the_row_alone(self) -> None:
        good = row(flip_tax_lamports=TWO_HOUR_TAX, flip_tax_bps=TWO_HOUR_BPS)
        self.assertEqual(good.price_lamports * good.flip_tax_bps // BPS_DENOMINATOR,
                         good.flip_tax_lamports)

    def test_a_tax_with_no_rate_is_caught(self) -> None:
        message = self.violations(row(flip_tax_lamports=TWO_HOUR_TAX))
        self.assertIn("flip_tax_bps", message)
        self.assertIn(str(TWO_HOUR_TAX), message)
        self.assertIn("report both or neither", message)

    def test_zero_or_null_with_no_rate_is_fine(self) -> None:
        for index, tax in enumerate((None, 0)):
            with self.subTest(tax=tax):
                path = self.write(
                    [row(flip_tax_lamports=tax, flip_tax_bps=None)], name=f"no-rate-{index}.jsonl"
                )
                self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_a_rate_outside_the_bounds_is_caught(self) -> None:
        for bps in (10_001, -1, "1500", 1500.0, True):
            with self.subTest(bps=bps):
                self.assertIn("flip_tax_bps", self.violations(row(flip_tax_bps=bps,
                                                                 flip_tax_lamports=0)))

    def test_a_negative_tax_is_caught(self) -> None:
        message = self.violations(row(flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=-1))
        self.assertIn("negative", message)
        self.assertIn("not a tax", message)

    def test_a_tax_above_the_price_is_caught(self) -> None:
        message = self.violations(
            row(flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=PRICE + 1)
        )
        self.assertIn(f"exceeds price_lamports {PRICE}", message)

    def test_a_negative_tax_on_a_negative_price_is_still_caught(self) -> None:
        # The crafted row a mirror of the fee's review turned up: a negative price floors to a
        # negative expected tax, so the arithmetic agrees unless the bound refuses it first.
        message = self.violations(row(
            price_lamports=-PRICE,
            markup_bps=-20_000,
            flip_tax_bps=TWO_HOUR_BPS,
            flip_tax_lamports=-TWO_HOUR_TAX,
        ))
        self.assertIn("negative", message)

    def test_a_tax_that_does_not_agree_with_the_rate_is_caught(self) -> None:
        for tax in (TWO_HOUR_TAX + 1, TWO_HOUR_TAX - 1, 0):
            with self.subTest(tax=tax):
                message = self.violations(row(flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=tax))
                self.assertIn("does not agree", message)
                self.assertIn(f"{TWO_HOUR_BPS} bps", message)

    def test_a_primary_sale_that_claims_a_tax_is_caught(self) -> None:
        message = self.violations(row(
            action="buy", flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=TWO_HOUR_TAX
        ))
        self.assertIn("primary sale", message)
        self.assertIn("resales only", message)

    def test_a_primary_sale_with_zero_or_no_tax_verifies(self) -> None:
        path = self.write([
            row(action="buy", flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=0),
            row(action="buy", flip_tax_bps=None, flip_tax_lamports=None),
        ])
        self.assertEqual(verify_dataset(path)["rows"], 2)

    def test_a_tax_on_a_row_that_never_sold_is_caught(self) -> None:
        for overrides in (
            dict(action="list", price_lamports=None, markup_bps=None,
                 flip_tax_lamports=TWO_HOUR_TAX),
            dict(status="refused", error_code=gw.E_CAP_EXCEEDED,
                 flip_tax_lamports=TWO_HOUR_TAX),
            dict(status="skipped", signature=None, flip_tax_lamports=TWO_HOUR_TAX),
        ):
            with self.subTest(**overrides):
                message = self.violations(row(flip_tax_bps=TWO_HOUR_BPS, **overrides))
                self.assertIn("must be 0 or null", message)

    def test_zero_is_accepted_on_a_row_that_did_not_sell(self) -> None:
        path = self.write([row(action="list", price_lamports=None, markup_bps=None,
                               flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=0)])
        self.assertEqual(verify_dataset(path)["rows"], 1)

    def test_an_executed_trade_with_a_rate_and_no_price_is_caught(self) -> None:
        message = self.violations(row(
            price_lamports=None, markup_bps=None, flip_tax_bps=TWO_HOUR_BPS,
            flip_tax_lamports=0,
        ))
        self.assertIn("cannot be checked against anything", message)

    def test_a_hold_that_is_not_a_whole_number_of_seconds_is_caught(self) -> None:
        for held in (-1, "7200", 7200.0, True):
            with self.subTest(held=held):
                message = self.violations(row(
                    flip_tax_bps=TWO_HOUR_BPS, flip_tax_lamports=TWO_HOUR_TAX, held_seconds=held
                ))
                self.assertIn("held_seconds", message)

    def test_the_tax_and_the_fee_are_checked_independently(self) -> None:
        # A row with a correct tax and a wrong fee fails on the fee alone, and the message does
        # not mention the tax: the two rules are separate functions so one cannot excuse the other.
        message = self.violations(row(
            flip_tax_bps=TWO_HOUR_BPS,
            flip_tax_lamports=TWO_HOUR_TAX,
            fee_lamports=1,
            artist_fee_bps=500,
        ))
        self.assertIn("fee_lamports", message)
        self.assertNotIn("flip_tax", message)


class PlanCase(ConfigCase):
    def plan(self, path: Path) -> list[str]:
        """The lines `plan` prints, in process, with no subprocess and no run directory."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = main(["plan", "--config", str(path)])
        self.assertEqual(code, 0, "plan must exit 0 for a valid config")
        return buffer.getvalue().splitlines()


class TestPlanPrintsTheTax(PlanCase):
    #: What `plan` prints for an event with no block, above its agent lines.
    TAX_LABEL = " " * 11 + "tax  "

    def tax_lines(self, lines: list[str]) -> list[str]:
        return [line for line in lines if line.startswith(self.TAX_LABEL)]

    def test_an_event_with_no_block_prints_no_tax_line(self) -> None:
        without = self.plan(self.write(config_document()))
        explicit_null = self.plan(self.write(config_document(flip_tax=None)))
        self.assertEqual(self.tax_lines(without), [])
        self.assertEqual(without[1:], explicit_null[1:], "a null block is the same as no block")

    def test_a_disabled_block_is_reported_as_off(self) -> None:
        lines = self.plan(self.write(config_document(flip_tax={"artist_wallet": ARTIST})))
        self.assertEqual(len(lines), len(self.plan(self.write(config_document()))) + 1)
        self.assertEqual(self.tax_lines(lines), ["           tax  off"])

    def test_an_enabled_block_reports_the_rate_both_instants_and_the_wallet(self) -> None:
        block = policy_wire(
            schedule=schedule_wire(full_bps=1200, full_hold_seconds=600, zero_hold_seconds=86_400)
        )
        lines = self.plan(self.write(config_document(flip_tax=block)))
        self.assertEqual(
            self.tax_lines(lines),
            [
                "           tax  1200 bps of the sale price while held under 600s, falling to 0 "
                f"at 86400s, paid by the seller to {ARTIST}"
            ],
        )

    def test_the_tax_line_sits_under_its_event_after_the_fee_line(self) -> None:
        document = config_document(
            artist_fee={"artist_wallet": ARTIST, "fee_bps": 500},
            flip_tax=policy_wire(),
        )
        lines = self.plan(self.write(document))
        event_index = next(i for i, line in enumerate(lines) if line.startswith("event      "))
        self.assertTrue(lines[event_index + 1].startswith(" " * 11 + "fee  "))
        self.assertTrue(lines[event_index + 2].startswith(self.TAX_LABEL))
        self.assertEqual(len(lines), 2 + len(self.plan(self.write(config_document()))))

    def test_nothing_else_on_the_event_line_changed(self) -> None:
        without = self.plan(self.write(config_document()))
        with_tax = self.plan(self.write(config_document(flip_tax=policy_wire())))
        event_line = "event      "
        self.assertEqual(
            [line for line in without if line.startswith(event_line)],
            [line for line in with_tax if line.startswith(event_line)],
        )


class FixedClockDryRunGateway(gw.DryRunGateway):
    """A `DryRunGateway` whose chains all read a clock the test sets.

    The chain is the shipped `DryRunEventChain` and not a subclass, because `SwarmRunner` reads
    the house label off the chain's own module and a subclass defined in a test module would
    change it. The clock is bound onto the instance instead, which is the seam `_now` exists to
    be, and the run is otherwise the shipped one.
    """

    def __init__(self, *args, clock: int = NOW, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.clock = clock

    def create_event(self, spec: EventSpec) -> gw.DryRunEventChain:
        cap_bps = effective_cap_bps(spec.mode, spec.cap_bps)
        chain = gw.DryRunEventChain(
            spec,
            mode=spec.mode,
            cap_bps=cap_bps,
            face_lamports=spec.face_lamports,
            ceiling=ceiling_lamports(spec.face_lamports, cap_bps),
        )
        chain._now = lambda: self.clock
        self._events[spec.event_id] = chain
        return chain


class TestTheRunnerChargesTheTaxOnResales(unittest.TestCase):
    """A real run, end to end: one taxed event, a primary buy and the resale that follows.

    Every layer is the shipped one -- `SwarmRunner`, `DryRunGateway`, `LedgerWriter`,
    `verify_dataset` -- and only the cluster and its clock are simulated, so this is the test that
    says the tax reaches the row on a resale, stays at 0 on a primary sale, and that the row's
    three columns come out of the transfer's own result rather than being invented.
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

    def run_it(self, flip_tax):
        from market_swarm.config import AgentSpec, RunConfig
        from market_swarm.runner import SwarmRunner

        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        config = RunConfig(
            run_id="sw-tax-wiring",
            cluster="local",
            events=(spec(flip_tax=flip_tax),),
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
        gateway = FixedClockDryRunGateway("local", run_dir=root / "run", clock=NOW)
        policies = {
            "a1": self.Scripted({1: (("buy", PRICE),), 2: (("resell", PRICE),)}),
            # A bid one lamport above face, so it is a secondary bid rather than a second primary
            # purchase: anything at or below face buys stock from the house and consumes the bid.
            "a2": self.Scripted({2: (("buy", PRICE + 1),)}),
        }
        summary = SwarmRunner(
            config, gateway, clock=lambda: 1_700_000_000.0, policies=policies
        ).run()
        self.assertEqual(len(summary.dataset_paths), 1)
        rows = [
            json.loads(line)
            for line in Path(summary.dataset_paths[0]).read_text(encoding="utf-8").splitlines()[1:]
        ]
        return summary, rows

    def test_the_primary_buy_pays_no_tax_and_the_resale_pays_it(self) -> None:
        summary, rows = self.run_it(policy())
        buy = [one for one in rows if one["action"] == "buy" and one["status"] == "ok"]
        resale = [one for one in rows if one["action"] == "resell" and one["status"] == "ok"]
        self.assertEqual(len(buy), 1, f"expected one primary purchase, got {summary.by_status}")
        self.assertEqual(len(resale), 1, f"expected one executed resale, got {summary.by_status}")
        self.assertEqual(buy[0]["flip_tax_lamports"], 0, "a primary sale pays no flip tax")
        self.assertIsNone(buy[0]["flip_tax_bps"])
        self.assertIsNone(buy[0]["held_seconds"])
        # The buy stamped the hold clock at the same instant the resale reads it, so the hold is
        # exactly zero seconds and the rate is the schedule's flat 15%.
        self.assertEqual(resale[0]["held_seconds"], 0)
        self.assertEqual(resale[0]["flip_tax_bps"], FULL_BPS)
        self.assertEqual(resale[0]["flip_tax_lamports"], PRICE * FULL_BPS // BPS_DENOMINATOR)
        self.assertEqual(verify_dataset(summary.dataset_paths[0])["rows"], len(rows))

    def test_an_event_with_no_tax_writes_none_of_the_three_columns(self) -> None:
        summary, rows = self.run_it(None)
        self.assertTrue(rows)
        for one in rows:
            self.assertIsNone(one["flip_tax_lamports"])
            self.assertIsNone(one["flip_tax_bps"])
            self.assertIsNone(one["held_seconds"])
        self.assertEqual(verify_dataset(summary.dataset_paths[0])["rows"], len(rows))

    def test_a_taxed_run_is_still_simulated_on_every_row(self) -> None:
        _, rows = self.run_it(policy())
        self.assertTrue(rows)
        for one in rows:
            self.assertEqual(one["chain"], "simulated")
            self.assertIsNone(one["signature"], "a simulated row may not claim a signature")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

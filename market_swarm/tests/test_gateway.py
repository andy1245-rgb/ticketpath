"""The gateway's unit tests: no validator, no socket, no signature, no keypair file read.

Every test here runs a real `ChainGateway` against a fake cluster. The fake replaces five seams --
`_rpc`, `_sign`, `_run`, `_derive_address` and `_wait_for_account` -- so the message encoding, the
instruction bytes, the cap decision and the lock are the real code and only the cluster is a
stand-in. That is deliberate: the parts worth testing are the parts that decide what bytes go on a
wire, and a test that stubbed those out would assert nothing.

What is *not* here is anything that needs a chain. `tests/test_gateway_live.py` has that, behind
`MARKET_SWARM_LIVE=1`.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import json
import os
import re
import socket
import tempfile
import threading
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from market_swarm import gateway as gw
from market_swarm.config import EventSpec, ceiling_lamports, effective_cap_bps

REPO_ROOT = Path(__file__).resolve().parents[2]

CAP_BPS = 2500
FACE = 1_000_000_000
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000
BLOCKHASH = gw.dp.base58.encode(bytes(range(32)))


def b58(value: bytes) -> str:
    return gw.dp.base58.encode(value)


def address(seed: int) -> str:
    """A deterministic 32-byte address. Real base58, so `compile_message` accepts it."""
    return b58(bytes([seed % 251]) * 32)


def unique(text: str) -> str:
    """A deterministic 32-byte address from a name, so two events never share a mint."""
    return b58(hashlib.sha256(text.encode()).digest())


def spec(**overrides) -> EventSpec:
    base = dict(
        event_id="evt_unit",
        face_lamports=FACE,
        mode="capped",
        cap_bps=CAP_BPS,
        tickets=4,
        rounds=2,
        round_seconds=0,
    )
    base.update(overrides)
    return EventSpec(**base)


class NoSocket:
    """Turn any attempt to open a socket into a failure. The contract's "no socket" as a test."""

    def setUp(self):
        super().setUp()
        original = socket.socket.connect

        def refuse(sock, *args, **kwargs):
            raise AssertionError(f"a unit test tried to open a socket to {args!r}")

        socket.socket.connect = refuse
        self.addCleanup(setattr, socket.socket, "connect", original)


class FakeChain(gw.ChainGateway):
    """A ChainGateway whose cluster is a dictionary.

    `_sign` returns a 64-byte marker instead of running a signer, and `_rpc` answers the handful of
    methods the gateway uses. `sent` records every `sendTransaction` body with the window it
    occupied, which is how the lock test proves there is no overlap.

    `program` is a constructor argument so the v2 encode path can be driven through the same fake:
    the record account it reads back has to be the length v2 stores, and `start()` never runs here.
    """

    def __init__(self, run_dir: Path, *, program: str = "v1") -> None:
        super().__init__("local", run_dir=run_dir, program=program)
        self.rpc_url = "http://127.0.0.1:1"
        self.program_id = address(9)
        self.record_account = unique("record:evt_unit")
        self.record_bytes = (
            FACE.to_bytes(8, "little")
            + CAP_BPS.to_bytes(2, "little")
            + (0).to_bytes(8, "little")
            + bytes([1])
        )
        if program == "v2":
            # Face, cap, pending and status first, as v1 has them, then the three fields v2 adds
            # and the 32-byte authority: 70 bytes, the length `decode_v2_record` refuses otherwise.
            self.record_bytes += (
                (0).to_bytes(8, "little")      # band_low_lamports
                + b"ZZ"                         # jurisdiction
                + bytes([0])                    # policy: capped
                + (0).to_bytes(8, "little")      # held_since_unix
                + bytes(32)                     # authority
            )
        self.balances: dict[str, int] = {}
        self.lamports: dict[str, int] = {}
        self.errors: dict[str, object] = {}
        self.calls: list[tuple[str, list]] = []
        self.sent: list[dict] = []
        self.instructions: list[list] = []
        self.signed: list[bytes] = []
        self.signers: list[Path] = []
        self.sign_error: Exception | None = None
        self.overlap = 0
        self._in_flight = 0
        self._flight_lock = threading.Lock()
        self.send_delay = 0.02
        # Pre-registered wallets: paths the tests never open, and addresses the real encoder
        # accepts. Nothing is generated and nothing is signed.
        seeds = {"authority": 1, "seller": 2, "buyer": 3}
        for label, seed in seeds.items():
            self._keys[label] = run_dir / "keys" / f"{label}.json"
            self._addresses[label] = address(seed)
            # Funded, as a wallet in a running swarm already is: a transfer must not spend a
            # transaction on topping the seller up, and the count of sends is asserted below.
            self.lamports[address(seed)] = gw.FUND_LAMPORTS_PER_WALLET
        self._started = True

    # -- the five seams ----------------------------------------------------

    def _run(self, command, *, timeout, what, check=True, cwd=None):  # noqa: D401 - a seam
        self.calls.append(("run", list(command)))
        return ""

    def _wait_for_account(self, addr: str) -> bool:
        self.calls.append(("wait", [addr]))
        return True

    def _account_exists(self, addr: str) -> bool:
        # Nothing exists in a dictionary until something puts it there, and the gateway only uses
        # this to decide whether to create an account: False is the honest answer for a fresh one.
        self.calls.append(("exists", [addr]))
        return False

    def _derive_address(self, program_id: str, *seeds: str) -> str:
        return unique(program_id + "|" + "|".join(seeds))

    def _confirmation(self, signature: str) -> dict:
        err = self.errors.get(signature)
        return {"ok": err is None, "err": err, "slot": 42}

    def _send(self, instructions, *, payer, signer_path, skip_preflight=False):
        """Keep the instructions as built, then send them for real through the fake cluster.

        The compiled message is the thing a reader can see, but it merges account flags across the
        two instructions: the record is a writable key either way because staging writes it. The
        per-program difference -- v2's hook writes `held_since_unix`, so its transfer marks the
        record writable -- is only visible here, before compilation.
        """
        self.instructions.append(list(instructions))
        return super()._send(
            instructions, payer=payer, signer_path=signer_path, skip_preflight=skip_preflight
        )

    def _send_multi(self, instructions, *, payer, signer_paths, skip_preflight=False):
        """The same record-then-send for the two-signature paths, which is all of v2's sales.

        `_send_multi` is the real one: the fake replaces the cluster, not the signer check, so a
        test here still fails when the message and the keypair paths disagree.
        """
        self.instructions.append(list(instructions))
        return super()._send_multi(
            instructions, payer=payer, signer_paths=signer_paths, skip_preflight=skip_preflight
        )

    def _sign(self, keypair_path: Path, message: bytes) -> bytes:
        self.signed.append(message)
        self.signers.append(keypair_path)
        if self.sign_error is not None:
            raise self.sign_error
        return bytes([7]) * 64

    def _rpc(self, method, params, *, timeout=None, attempts=None):
        self.calls.append((method, params))
        if method == "getLatestBlockhash":
            return {"value": {"blockhash": BLOCKHASH}}
        if method == "getHealth":
            return "ok"
        if method == "getBalance":
            return {"value": self.lamports.get(params[0], 0)}
        if method == "getTokenAccountBalance":
            return {"value": {"amount": str(self.balances.get(params[0], 0))}}
        if method == "getAccountInfo":
            if params[0] == self.record_account:
                return {"value": {"data": [base64.b64encode(self.record_bytes).decode(), "base64"],
                                  "executable": False}}
            if params[0] == self.program_id:
                return {"value": {"executable": True}}
            return {"value": None}
        if method == "sendTransaction":
            with self._flight_lock:
                self._in_flight += 1
                self.overlap = max(self.overlap, self._in_flight)
            try:
                signature = b58(bytes([len(self.sent) + 1]) * 64)
                self.sent.append({
                    "signature": signature,
                    "wire": params[0],
                    "skipPreflight": params[1]["skipPreflight"],
                    "thread": threading.get_ident(),
                })
                self._apply_system_transfers(params[0])
                threading.Event().wait(self.send_delay)
            finally:
                with self._flight_lock:
                    self._in_flight -= 1
            return signature
        if method == "getSignatureStatuses":
            err = self.errors.get(params[0][0])
            return {"value": [{"slot": 42, "err": err, "confirmationStatus": "confirmed"}]}
        if method == "getTransaction":
            err = self.errors.get(params[0])
            return {
                "slot": 42,
                "blockTime": 1_700_000_000,
                "meta": {"err": err, "logMessages": ["Program log: ticketpath: cap admitted"]},
            }
        raise AssertionError(f"the fake cluster was asked for {method}")

    def _apply_system_transfers(self, wire: str) -> None:
        """Credit a funded wallet, so "is it funded" is a real question on the second look."""
        transaction = base64.b64decode(wire)
        message = decode_message(transaction[1 + 64 * transaction[0]:])
        for instruction in message["instructions"]:
            if message["keys"][instruction["program"]] != gw.dp.SYSTEM_PROGRAM:
                continue
            if instruction["data"][:4] != (2).to_bytes(4, "little"):
                continue
            destination = message["keys"][instruction["accounts"][1]]
            lamports = int.from_bytes(instruction["data"][4:12], "little")
            self.lamports[destination] = self.lamports.get(destination, 0) + lamports

    def refuse_every_send_with(self, err) -> None:
        """Make the next accepted transaction land with `err`, whatever its signature turns out to be."""
        original = self._rpc

        def rpc(method, params, **kw):
            if method == "sendTransaction":
                expected = b58(bytes([len(self.sent) + 1]) * 64)
                self.errors[expected] = err
            return original(method, params, **kw)

        self._rpc = rpc


def event(chain_gateway: FakeChain, **overrides) -> gw.EventChain:
    spec_obj = spec(**overrides)
    cap_bps = effective_cap_bps(spec_obj.mode, spec_obj.cap_bps)
    return gw.EventChain(
        gateway=chain_gateway,
        event_id=spec_obj.event_id,
        mint=unique(f"mint:{spec_obj.event_id}"),
        record=chain_gateway.record_account,
        extra_metas=unique(f"extra:{spec_obj.event_id}"),
        mode=spec_obj.mode,
        cap_bps=cap_bps,
        face_lamports=spec_obj.face_lamports,
        ceiling_lamports=ceiling_lamports(spec_obj.face_lamports, cap_bps),
    )


class FakeCase(NoSocket, unittest.TestCase):
    """A fake cluster in a temporary run directory, with a seller holding tickets."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chain_gateway = FakeChain(Path(self.tmp.name))
        self.event = event(self.chain_gateway)
        self.seller_ata = self.event.ticket_account("seller")

    def hold(self, count: int) -> None:
        self.chain_gateway.balances[self.seller_ata] = count


class DecodeRecordTest(unittest.TestCase):
    def test_hand_built_buffer(self):
        data = (
            FACE.to_bytes(8, "little")
            + CAP_BPS.to_bytes(2, "little")
            + CEILING.to_bytes(8, "little")
            + bytes([1])
        )
        self.assertEqual(len(data), 19)
        self.assertEqual(
            gw.decode_record(data),
            {
                "face_lamports": FACE,
                "cap_bps": CAP_BPS,
                "pending_price_lamports": CEILING,
                "status": 1,
            },
        )

    def test_maximum_fields(self):
        data = ((2**64 - 1).to_bytes(8, "little") + (65535).to_bytes(2, "little")
                + (0).to_bytes(8, "little") + bytes([0]))
        decoded = gw.decode_record(data)
        self.assertEqual(decoded["face_lamports"], 2**64 - 1)
        self.assertEqual(decoded["cap_bps"], 65535)
        self.assertEqual(decoded["status"], 0)

    def test_the_rust_constant_is_wrong_and_20_is_refused(self):
        # `TicketRecord::LEN` says 8+2+8+1+1 = 20 and is never used; `initialize_record` allocates
        # the borsh length, which is 19. Decoding 20 would read a byte nobody wrote.
        with self.assertRaises(ValueError) as caught:
            gw.decode_record(bytes(20))
        self.assertIn("19", str(caught.exception))
        self.assertIn("20", str(caught.exception))

    def test_not_bytes(self):
        with self.assertRaises(ValueError):
            gw.decode_record("nine hundred and fifty two")  # type: ignore[arg-type]


class SystemTransferTest(unittest.TestCase):
    def test_twelve_bytes_tag_two_then_lamports(self):
        instruction = gw.system_transfer_instruction(
            source=address(1), destination=address(2), lamports=50_000_000
        )
        self.assertEqual(instruction.program_id, "11111111111111111111111111111111")
        self.assertEqual(len(instruction.data), 12)
        self.assertEqual(instruction.data[:4], b"\x02\x00\x00\x00")
        self.assertEqual(instruction.data[4:], (50_000_000).to_bytes(8, "little"))
        self.assertEqual(instruction.data.hex(), "0200000080f0fa0200000000")

    def test_accounts_source_signs_and_both_are_writable(self):
        instruction = gw.system_transfer_instruction(
            source=address(1), destination=address(2), lamports=1
        )
        (from_meta, to_meta) = instruction.accounts
        self.assertEqual((from_meta.is_signer, from_meta.is_writable), (True, True))
        self.assertEqual((to_meta.is_signer, to_meta.is_writable), (False, True))

    def test_it_feeds_the_message_encoder(self):
        instruction = gw.system_transfer_instruction(
            source=address(1), destination=address(2), lamports=1_000
        )
        message = gw.dp.compile_message(
            address(1), [instruction], BLOCKHASH
        )
        self.assertGreater(len(message), 32)

    def test_refuses_a_bad_amount(self):
        for bad in (0, -1, 2**64, True, 1.5, "1"):
            with self.subTest(lamports=bad), self.assertRaises(ValueError):
                gw.system_transfer_instruction(source=address(1), destination=address(2), lamports=bad)


class RefusalCodeTest(unittest.TestCase):
    """The program's own code, out of whatever spelling the cluster used for it.

    A refusal written as an unbranded `error` row is a refusal a reader cannot count, so the two
    spellings a preflight or a confirmed transaction can produce are both read. The hex form is
    what a simulation failure quotes; the decimal one is what some RPC shapes print.
    """

    def test_hex_form(self) -> None:
        text = (
            "Transaction simulation failed: Error processing Instruction 0: "
            "custom program error: 0x177a"
        )
        self.assertEqual(gw._code_from_text(text), 6010)

    def test_decimal_form(self) -> None:
        self.assertEqual(
            gw._code_from_text("Transaction simulation failed: custom program error: 6010"),
            6010,
        )

    def test_hex_wins_when_a_message_carries_both(self) -> None:
        self.assertEqual(
            gw._code_from_text("custom program error: 0x177a ... custom program error: 6021"),
            6010,
        )

    def test_a_message_with_no_code_returns_none_rather_than_a_guess(self) -> None:
        self.assertIsNone(gw._code_from_text("blockhash not found"))


class CapDecisionTest(unittest.TestCase):
    def test_agrees_with_the_configured_ceiling(self):
        for face in (0, 1, 999, FACE, 2**64 - 1):
            for cap in (0, 1, 2500, 65535):
                with self.subTest(face=face, cap=cap):
                    ceiling = ceiling_lamports(face, cap)
                    self.assertEqual(ceiling, face * (10_000 + cap) // 10_000)
                    self.assertTrue(gw.cap_admits(price_lamports=ceiling, face_lamports=face, cap_bps=cap))
                    self.assertFalse(
                        gw.cap_admits(price_lamports=ceiling + 1, face_lamports=face, cap_bps=cap)
                    )

    def test_the_worked_pair_both_sides(self):
        # The design's own numbers: face 1.0 SOL, cap 2500 bps, 1_250_000_000 admitted and one
        # lamport over it refused. Both sides, because one side alone proves nothing.
        self.assertTrue(gw.cap_admits(price_lamports=1_250_000_000, face_lamports=FACE, cap_bps=2500))
        self.assertFalse(gw.cap_admits(price_lamports=1_250_000_001, face_lamports=FACE, cap_bps=2500))

    def test_monitored_mode_is_not_no_cap(self):
        cap = effective_cap_bps("monitored", None)
        self.assertEqual(cap, 65535)
        ceiling = ceiling_lamports(FACE, cap)
        self.assertEqual(ceiling, 7_553_500_000)  # face * 7.5535, not "no cap"
        self.assertTrue(gw.cap_admits(price_lamports=ceiling, face_lamports=FACE, cap_bps=cap))
        self.assertFalse(gw.cap_admits(price_lamports=ceiling + 1, face_lamports=FACE, cap_bps=cap))


def decode_message(message: bytes) -> dict:
    """Just enough of the legacy message format to check what was compiled. No library."""
    index = 3

    def shortvec(at: int) -> tuple[int, int]:
        value, shift = 0, 0
        while True:
            byte = message[at]
            at += 1
            value |= (byte & 0x7F) << shift
            if not byte & 0x80:
                return value, at
            shift += 7

    count, index = shortvec(index)
    keys = [message[index + 32 * i:index + 32 * (i + 1)] for i in range(count)]
    index += 32 * count
    blockhash = message[index:index + 32]
    index += 32
    instructions, index = shortvec(index)
    decoded = []
    for _ in range(instructions):
        program_index = message[index]
        index += 1
        accounts, index = shortvec(index)
        account_indices = list(message[index:index + accounts])
        index += accounts
        length, index = shortvec(index)
        data = message[index:index + length]
        index += length
        decoded.append({"program": program_index, "accounts": account_indices, "data": data})
    return {
        "header": list(message[0:3]),
        "keys": [b58(key) for key in keys],
        "blockhash": b58(blockhash),
        "instructions": decoded,
        "consumed": index,
        "length": len(message),
    }


class OneTransactionTest(FakeCase):
    """Fact (a): `compile_message` takes a list, so the pair is one transaction, one signature."""

    def setUp(self):
        super().setUp()
        self.hold(2)
        self.event.ticket_account("buyer", create=True)

    def message(self) -> dict:
        transaction = base64.b64decode(self.chain_gateway.sent[-1]["wire"])
        self.assertEqual(transaction[0], 1, "one signature slot")
        return decode_message(transaction[65:])

    def test_stage_and_transfer_are_one_message_signed_once(self):
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "ok")
        self.assertEqual(len(self.chain_gateway.sent), 1)
        self.assertEqual(len(self.chain_gateway.signed), 1, "one transaction, one signature")
        message = self.message()
        self.assertEqual(message["header"][0], 1, "one required signature")
        self.assertEqual(len(message["instructions"]), 2)
        first, second = message["instructions"]
        self.assertEqual(message["keys"][first["program"]], self.chain_gateway.program_id)
        self.assertEqual(message["keys"][second["program"]], gw.dp.TOKEN_2022_PROGRAM)
        self.assertEqual(first["data"], bytes([2]) + CEILING.to_bytes(8, "little"), "tag 2 stages the price")
        self.assertEqual(second["data"], bytes([12]) + (1).to_bytes(8, "little") + bytes([0]),
                         "transfer_checked, amount 1, 0 decimals")
        self.assertEqual(message["blockhash"], BLOCKHASH)
        self.assertEqual(message["length"], message["consumed"], "the message was parsed exactly")

    def test_the_record_appears_once_in_the_key_table(self):
        # Two instructions touching one account is exactly what a dedupe bug breaks: one record,
        # one index, or the runtime sees two accounts where the hook expects one.
        self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        message = self.message()
        self.assertEqual(message["keys"].count(self.chain_gateway.record_account), 1)
        stage, move = message["instructions"]
        record_index = message["keys"].index(self.chain_gateway.record_account)
        self.assertEqual(stage["accounts"], [record_index])
        self.assertIn(record_index, move["accounts"])

    def test_the_seller_is_the_only_signer(self):
        self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        message = self.message()
        self.assertEqual(message["keys"][0], self.chain_gateway._addresses["seller"])

    def test_preflight_is_on_at_the_cap_and_off_above_it(self):
        self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING + 1)
        self.assertEqual([sent["skipPreflight"] for sent in self.chain_gateway.sent], [False, True])


class RefusalTest(FakeCase):
    def setUp(self):
        super().setUp()
        self.hold(2)

    def test_cap_exceeded_maps_to_refused_with_6010(self):
        self.chain_gateway.refuse_every_send_with({"InstructionError": [1, {"Custom": 6010}]})
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING + 1)
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.error_code, 6010)
        self.assertIsNotNone(result.signature, "a refusal sent with preflight off has its own signature")
        self.assertEqual(result.slot, 42)
        self.assertEqual(result.block_time, 1_700_000_000)
        self.assertGreaterEqual(result.latency_ms, 0)
        self.assertIn("cap admitted", " ".join(result.logs))
        self.assertEqual(len(self.chain_gateway.sent), 1)

    def test_a_different_program_error_maps_to_error_not_refused(self):
        # 6009 is "transfer not staged": it looks like a cap problem and is not, so it must not be
        # reported as a refusal. That distinction is why the codes are named.
        self.chain_gateway.refuse_every_send_with({"InstructionError": [1, {"Custom": 6009}]})
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, 6009)

    def test_a_builtin_error_has_no_code(self):
        self.chain_gateway.refuse_every_send_with({"InstructionError": [1, "IncorrectProgramId"]})
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "error")
        self.assertIsNone(result.error_code)
        self.assertIsNotNone(result.signature)

    def test_a_price_the_client_refuses_that_the_hook_admits_is_a_warning(self):
        # The status says what the chain did; the log says the two disagreed. Anything else would
        # either hide the transfer or invent a refusal.
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING + 1)
        self.assertEqual(result.status, "ok")
        self.assertIsNone(result.error_code)
        self.assertTrue(any("WARNING" in line for line in result.logs))

    def test_preflight_rejection_returns_an_error_result_not_an_exception(self):
        original = self.chain_gateway._rpc

        def rpc(method, params, **kw):
            if method == "sendTransaction":
                raise gw.dp.PublishError(
                    "sendTransaction: Transaction simulation failed: Error processing Instruction 1: "
                    "custom program error: 0x1779"
                )
            return original(method, params, **kw)

        self.chain_gateway._rpc = rpc
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "error")
        self.assertEqual(result.error_code, 6009)
        self.assertIsNone(result.signature, "a transaction refused in preflight has no signature on chain")
        self.assertEqual(len(self.chain_gateway.sent), 0)

    def test_an_unconfirmed_send_keeps_its_signature(self):
        # The dangerous state: sent, not confirmed. Dropping the signature is how a landed transfer
        # becomes a second transfer, so the result carries it and says not to resend.
        def confirmation(signature):
            raise gw.dp.PublishError(f"timed out after 60s waiting for {signature}")

        self.chain_gateway._confirmation = confirmation
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "error")
        self.assertIsNotNone(result.signature)
        self.assertTrue(any("do not resend" in line for line in result.logs))


class BalancePreflightTest(FakeCase):
    def test_no_ticket_names_the_balance_and_sends_nothing(self):
        self.hold(0)
        with self.assertRaises(gw.TicketNotHeld) as caught:
            self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertIn("holds 0 tickets", str(caught.exception))
        self.assertIn("seller", str(caught.exception))
        self.assertEqual(self.chain_gateway.sent, [], "nothing may be staged when there is no ticket")

    def test_a_held_ticket_is_enough(self):
        self.hold(1)
        self.assertEqual(
            self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING).status,
            "ok",
        )


class LockTest(NoSocket, unittest.TestCase):
    """The per-mint lock is what stops two transfers reading each other's staged price."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chain_gateway = FakeChain(Path(self.tmp.name))
        self.chain_gateway.send_delay = 0.05
        self.first = event(self.chain_gateway, event_id="evt_a")
        self.second = event(self.chain_gateway, event_id="evt_b")

    def hammer(self, chains) -> None:
        for chain in chains:
            self.chain_gateway.balances[chain.ticket_account("seller")] = 5
        threads = [
            threading.Thread(
                target=chain.transfer,
                kwargs=dict(from_label="seller", to_label="buyer", price_lamports=CEILING),
            )
            for chain in chains
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)
        self.assertTrue(all(not thread.is_alive() for thread in threads), "a transfer deadlocked")

    def test_two_sends_on_one_mint_never_overlap(self):
        self.hammer([self.first, self.first])
        self.assertEqual(len(self.chain_gateway.sent), 2)
        self.assertEqual(self.chain_gateway.overlap, 1, "the stage+send pair is serialised per mint")

    def test_two_mints_do_overlap(self):
        # The other half of the claim: a global lock would also pass the test above, and would
        # serialise independent events for no reason.
        self.hammer([self.first, self.second])
        self.assertEqual(self.chain_gateway.overlap, 2, "different mints are independent")

    def test_each_transfer_is_signed_by_its_own_seller(self):
        # Two mints, two sellers, run at once. The message's fee payer is the seller, so a
        # signature made with the other seller's key would show up as a mismatched pair here.
        other = event(self.chain_gateway, event_id="evt_c")
        for chain in (self.first, other):
            self.chain_gateway.balances[chain.ticket_account("seller")] = 5
        self.hammer([self.first, other])
        self.assertEqual(len(self.chain_gateway.signed), 2)
        for path, message in zip(self.chain_gateway.signers, self.chain_gateway.signed):
            decoded = decode_message(message)
            payer = decoded["keys"][0]
            label = next(
                name for name, candidate in self.chain_gateway._keys.items() if candidate == path
            )
            self.assertEqual(payer, self.chain_gateway._addresses[label])

    def test_the_registry_is_keyed_by_mint(self):
        self.assertIs(gw.mint_lock("mint-a"), gw.mint_lock("mint-a"))
        self.assertIsNot(gw.mint_lock("mint-a"), gw.mint_lock("mint-b"))


class WalletLockTest(NoSocket, unittest.TestCase):
    def test_two_threads_create_and_fund_one_wallet_once(self):
        # A wallet generated twice is a wallet whose key nobody has: the second `solana-keygen
        # new` overwrites the first, and the address held in memory is the one that was replaced.
        with tempfile.TemporaryDirectory() as tmp:
            chain_gateway = FakeChain(Path(tmp))
            keygens: list[list[str]] = []
            fresh = address(77)

            def fake_run(command, *, timeout, what, check=True, cwd=None):
                if "new" in command:
                    keygens.append(command)
                    Path(command[command.index("-o") + 1]).write_text("[]", encoding="utf-8")
                    threading.Event().wait(0.05)  # a window wide enough for the other thread
                    return f"pubkey: {fresh}\n"
                if "pubkey" in command:
                    return f"{fresh}\n"
                return ""

            chain_gateway._run = fake_run
            latched = []
            threads = [
                threading.Thread(target=lambda: latched.append(chain_gateway._ensure_wallet("fresh")))
                for _ in range(2)
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=10)
            self.assertEqual(len(keygens), 1, "the keypair was generated twice")
            self.assertEqual(latched, [fresh, fresh])
            self.assertEqual(len(chain_gateway.sent), 1, "the wallet was funded twice")
            self.assertEqual(chain_gateway._addresses["fresh"], fresh)


class StopTest(NoSocket, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_dir = Path(self.tmp.name)

    def test_stop_twice_does_not_raise(self):
        chain_gateway = FakeChain(self.run_dir)
        chain_gateway.stop()
        chain_gateway.stop()
        self.assertTrue(chain_gateway._stopped)

    def test_stop_kills_the_validator_once_and_deletes_the_ledger(self):
        chain_gateway = FakeChain(self.run_dir)
        killed = []

        class FakeValidator:
            def stop(self):
                killed.append(True)

        ledger = self.run_dir / "validator-ledger"
        ledger.mkdir(parents=True)
        (ledger / "genesis.bin").write_bytes(b"1.5 GB, supposedly")
        chain_gateway._validator = FakeValidator()
        chain_gateway._ledger = ledger
        chain_gateway.stop()
        chain_gateway.stop()
        self.assertEqual(len(killed), 1)
        self.assertFalse(ledger.exists(), "a kept ledger is 1.5 GB; stop deletes it")

    def test_stop_survives_a_validator_that_raises(self):
        chain_gateway = FakeChain(self.run_dir)

        class Exploding:
            def stop(self):
                raise RuntimeError("the process group is already gone")

        chain_gateway._validator = Exploding()
        chain_gateway.stop()  # must not raise: it runs on every exit path
        self.assertTrue(chain_gateway._stopped)

    def test_stop_before_start_is_harmless(self):
        chain_gateway = gw.make_gateway("devnet", run_dir=self.run_dir)
        chain_gateway.stop()


class DryRunTest(NoSocket, unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_dir = Path(self.tmp.name)

    def test_make_gateway_returns_the_dry_one(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        self.assertIsInstance(chain_gateway, gw.DryRunGateway)
        self.assertTrue(chain_gateway.simulated)
        self.assertTrue(chain_gateway.status()["healthy"])
        self.assertTrue(chain_gateway.status()["simulated"])
        self.assertIsNone(chain_gateway.status()["program_id"])

    def test_the_constructor_dry_run_flag_also_returns_it(self):
        # CONTRACT.md: "dry_run=True returns a DryRunGateway". Both doors give the same answer.
        self.assertIsInstance(
            gw.ChainGateway("local", run_dir=self.run_dir, dry_run=True), gw.DryRunGateway
        )

    def test_a_dry_transfer_is_marked_and_has_no_signature(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        chain_gateway.start()
        event_chain = chain_gateway.create_event(spec())
        event_chain.open_account("buyer")
        event_chain.stock(2)  # the house mints; the first hop is house -> agent, as in a real run
        result = event_chain.transfer(
            from_label=gw.HOUSE_LABEL, to_label="buyer", price_lamports=CEILING
        )
        self.assertEqual(result.status, "ok")
        self.assertIsNone(result.signature)
        self.assertIsNone(result.slot)
        self.assertIsNone(result.error_code)
        self.assertTrue(gw.is_simulated(result))
        self.assertIn(gw.SIMULATED_LOG, result.logs)

    def test_a_dry_over_cap_price_is_predicted_as_a_refusal(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        chain_gateway.start()
        event_chain = chain_gateway.create_event(spec())
        event_chain.stock(1)
        result = event_chain.transfer(
            from_label=gw.HOUSE_LABEL, to_label="buyer", price_lamports=CEILING + 1
        )
        # The status vocabulary means the same thing in a dry run and a live run; only
        # `chain` distinguishes them. Answering `ok` here would put a price the cap forbids
        # into a dataset as an execution, and make a dry refusal rate incomparable.
        self.assertEqual(result.status, "refused")
        self.assertEqual(result.error_code, 6010)
        self.assertIsNone(result.signature)
        self.assertTrue(gw.is_simulated(result))
        self.assertEqual(
            event_chain._held[gw.HOUSE_LABEL], 1, "a refused simulated transfer moves nothing"
        )

    def test_dry_fields_match_the_spec(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        chain_gateway.start()
        event_chain = chain_gateway.create_event(spec(mode="monitored", cap_bps=None))
        self.assertEqual(event_chain.cap_bps, 65535)
        self.assertEqual(event_chain.ceiling_lamports, 7_553_500_000)
        self.assertEqual(event_chain.read_record()["cap_bps"], 65535)

    def test_dry_stop_twice(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        chain_gateway.start()
        chain_gateway.stop()
        chain_gateway.stop()

    def test_a_dry_seller_without_tickets_still_refuses_to_pretend(self):
        chain_gateway = gw.make_gateway("local", run_dir=self.run_dir, dry_run=True)
        chain_gateway.start()
        event_chain = chain_gateway.create_event(spec())
        with self.assertRaises(gw.TicketNotHeld):
            event_chain.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)


class ClusterTest(NoSocket, unittest.TestCase):
    def test_an_unknown_cluster_raises_before_anything_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("mainnet", "MAINNET", "", None, "localnet"):
                with self.subTest(cluster=bad), self.assertRaises(ValueError):
                    gw.ChainGateway(bad, run_dir=Path(tmp))
                with self.subTest(cluster=bad), self.assertRaises(ValueError):
                    gw.make_gateway(bad, run_dir=Path(tmp), dry_run=True)

    def test_the_dry_gateway_also_refuses_it(self):
        with tempfile.TemporaryDirectory() as tmp, self.assertRaises(ValueError):
            gw.DryRunGateway("mainnet", run_dir=Path(tmp))


class ProgramTest(NoSocket, unittest.TestCase):
    """The switch: which program a gateway drives, and the pairs that cannot exist."""

    def test_an_unknown_program_raises_before_anything_starts(self):
        with tempfile.TemporaryDirectory() as tmp:
            for bad in ("v3", "V1", "", None):
                with self.subTest(program=bad), self.assertRaises(ValueError):
                    gw.ChainGateway("local", run_dir=Path(tmp), program=bad)
                with self.subTest(program=bad), self.assertRaises(ValueError):
                    gw.make_gateway("local", run_dir=Path(tmp), dry_run=True, program=bad)

    def test_v2_on_devnet_is_refused_even_without_a_config(self):
        # Refused twice on purpose: the loader names it, and so does the gateway, because a caller
        # can build a gateway with no config at all.
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError) as caught:
                gw.make_gateway("devnet", run_dir=Path(tmp), program="v2")
            self.assertIn("v2", str(caught.exception))
            self.assertIn("devnet", str(caught.exception))
            with self.assertRaises(ValueError):
                gw.DryRunGateway("devnet", run_dir=Path(tmp), program="v2")

    def test_the_default_is_v1(self):
        with tempfile.TemporaryDirectory() as tmp:
            chain_gateway = gw.make_gateway("local", run_dir=Path(tmp))
            self.assertEqual(chain_gateway.program, "v1")
            self.assertEqual(chain_gateway.status()["program"], "v1")

    def test_the_dry_gateway_runs_v2_without_a_chain(self):
        # v2's cap and policy rules are the same predicate as v1's for the part this harness
        # models, nothing a dry run reports is an observation, and every row says `simulated`.
        # A labelled simulation is what `--dry-run --program v2` still gives, and it is the one
        # v2 path that needs no validator.
        with tempfile.TemporaryDirectory() as tmp:
            chain_gateway = gw.make_gateway("local", run_dir=Path(tmp), dry_run=True, program="v2")
            self.assertTrue(chain_gateway.simulated)
            self.assertEqual(chain_gateway.status()["program"], "v2")
            self.assertIn("v2", repr(chain_gateway))

    def test_a_v2_run_starts_like_a_v1_run(self):
        # v2's stage is authorised by the record's authority and the house holds that key, so the
        # refusal that stood here is gone: `start()` may not raise for v2 any more. Today's code
        # raised before it ever looked at `_started`; `FakeChain` is already up, so reaching its
        # status is the whole difference. `test_v2_authority_signing` drives the body below that.
        with tempfile.TemporaryDirectory() as tmp:
            chain_gateway = FakeChain(Path(tmp), program="v2")
            status = chain_gateway.start()
            self.assertEqual(status["program"], "v2")
            self.assertIsNotNone(status["program_id"])
            self.assertEqual(
                [call for call in chain_gateway.calls if call[0] == "run"], [],
                "nothing may be generated or spawned to start a run that is already up",
            )
            chain_gateway.stop()


class V2TransferTest(FakeCase):
    """The v2 shapes through the same fake cluster: what the seller's transaction carries.

    A regression to v1's encoders fails: v1 stages with the record alone and one signature, and
    its transfer makes the record read-only. A regression to a seller-signed v2 stage fails too:
    the record's authority is the house, and a stage naming the seller is refused `6026` on chain.
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chain_gateway = FakeChain(Path(self.tmp.name), program="v2")
        self.event = event(self.chain_gateway)
        self.seller_ata = self.event.ticket_account("seller")
        self.hold(2)
        self.event.ticket_account("buyer", create=True)

    def message(self) -> dict:
        transaction = base64.b64decode(self.chain_gateway.sent[-1]["wire"])
        # A compact-u16 signature count, that many 64-byte signatures, then the message. A v2
        # plain sale has two, so the offset is read rather than assumed.
        return decode_message(transaction[1 + 64 * transaction[0]:])

    def test_the_stage_names_the_house_as_a_signer(self):
        result = self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assertEqual(result.status, "ok")
        message = self.message()
        stage = message["instructions"][0]
        self.assertEqual(message["keys"][stage["program"]], self.chain_gateway.program_id)
        self.assertEqual(stage["data"], bytes([2]) + CEILING.to_bytes(8, "little"))
        self.assertEqual(
            [message["keys"][index] for index in stage["accounts"]],
            [
                self.chain_gateway._addresses[gw.HOUSE_LABEL],
                self.chain_gateway.record_account,
                self.event.mint,
            ],
            "v2 stages with [authority, record, mint] and the authority is the record's",
        )
        # The first key in a compiled message is the fee payer, which is the seller; the header
        # says how many keys must sign, and a v2 plain sale needs the seller and the house.
        self.assertEqual(message["header"][0], 2)
        self.assertEqual(message["keys"][0], self.chain_gateway._addresses["seller"])

    def test_the_transfer_record_is_writable_so_the_hook_can_write_the_hold(self):
        self.event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        stage, move = self.chain_gateway.instructions[-1]
        record_meta = [meta for meta in move.accounts if meta.pubkey == self.chain_gateway.record_account]
        self.assertEqual(len(record_meta), 1, "one record account, once")
        self.assertTrue(record_meta[0].is_writable, "v2's hook writes held_since_unix into it")
        self.assertEqual([meta.is_signer for meta in stage.accounts], [True, False, False])

    def test_a_v1_run_keeps_the_record_read_only_and_the_stage_one_account(self):
        v1 = FakeChain(Path(self.tmp.name), program="v1")
        v1_event = event(v1)
        v1.balances[v1_event.ticket_account("seller")] = 2
        v1_event.ticket_account("buyer", create=True)
        v1_event.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        stage, move = v1.instructions[-1]
        self.assertEqual([meta.pubkey for meta in stage.accounts], [v1.record_account])
        self.assertFalse(any(meta.is_signer for meta in stage.accounts), "v1 reads no signer")
        record_meta = [meta for meta in move.accounts if meta.pubkey == v1.record_account]
        self.assertEqual(len(record_meta), 1)
        self.assertFalse(record_meta[0].is_writable, "v1's hook writes nothing into the record")

    def test_the_v2_record_decodes_through_the_chain(self):
        # The fake answers `getAccountInfo` with 70 bytes when it is a v2 gateway, so the
        # per-program reader is what gets exercised, and a v1 reader would refuse this buffer.
        self.assertEqual(len(self.chain_gateway.record_bytes), 70)
        with self.assertRaises(ValueError):
            gw.decode_record(self.chain_gateway.record_bytes)
        observed = self.event.read_record()
        self.assertEqual(observed["face_value_lamports"], FACE)
        self.assertEqual(observed["cap_bps"], CAP_BPS)
        self.assertEqual(observed["policy"], 0)
        self.assertEqual(observed["jurisdiction"], b"ZZ")


class LabelAndPriceTest(FakeCase):
    def test_a_label_cannot_walk_out_of_the_keys_directory(self):
        for bad in ("../escape", "a/b", ".hidden", "", "x" * 65, 7, None):
            with self.subTest(label=bad), self.assertRaises(ValueError):
                self.chain_gateway._wallet_path(bad)

    def test_a_bad_price_is_refused_before_a_transaction_is_built(self):
        self.hold(1)
        for bad in (0, -1, 2**64, True, 1.0, "1250"):
            with self.subTest(price=bad), self.assertRaises(ValueError):
                self.event.transfer(from_label="seller", to_label="buyer", price_lamports=bad)
        self.assertEqual(self.chain_gateway.sent, [])

    def test_a_bad_spec_is_refused(self):
        chain_gateway = gw.make_gateway("local", run_dir=Path(self.tmp.name), dry_run=True)
        for bad in (
            spec(mode="capped", cap_bps=None),
            spec(mode="wild"),
            spec(face_lamports=0),
            spec(cap_bps=65536),
        ):
            with self.subTest(spec=bad), self.assertRaises(ValueError):
                chain_gateway.create_event(bad)

    def test_a_transfer_before_start_says_so(self):
        chain_gateway = gw.make_gateway("devnet", run_dir=Path(self.tmp.name))
        with self.assertRaises(gw.ChainUnavailable):
            chain_gateway.create_event(spec())


class ReadRecordTest(FakeCase):
    def test_reads_through_the_rpc(self):
        self.chain_gateway.record_bytes = (
            FACE.to_bytes(8, "little")
            + CAP_BPS.to_bytes(2, "little")
            + (1_100_000_000).to_bytes(8, "little")
            + bytes([1])
        )
        self.assertEqual(
            self.event.read_record(),
            {
                "face_lamports": FACE,
                "cap_bps": CAP_BPS,
                "pending_price_lamports": 1_100_000_000,
                "status": 1,
            },
        )

    def test_an_absent_record_says_so(self):
        self.chain_gateway.record_account = unique("absent")
        with self.assertRaises(gw.ChainUnavailable) as caught:
            self.event.read_record()
        self.assertIn("not on chain", str(caught.exception))

    def test_a_record_of_the_wrong_length_is_refused(self):
        self.chain_gateway.record_bytes = bytes(20)
        with self.assertRaises(ValueError):
            self.event.read_record()


class KeyDisciplineTest(NoSocket, unittest.TestCase):
    """No object the gateway hands out may carry bytes from a keypair file.

    The seed is injected the only way it can be: as the content of a file the gateway is pointed
    at. If any code path opened it and put a byte of it into an object, a repr, a log line or an
    exception, one of the encodings below would appear.
    """

    SENTINEL = bytes([243, 17, 92, 201, 44, 7, 168, 3] * 4)
    SEED = SENTINEL + bytes(reversed(SENTINEL))

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.run_dir = Path(self.tmp.name)
        keys = self.run_dir / "keys"
        keys.mkdir(parents=True)
        self.keypair = keys / "seller.json"
        self.keypair.write_text(json.dumps(list(self.SEED)), encoding="utf-8")
        os.chmod(self.keypair, 0o600)

    def encodings(self) -> list[str]:
        raw = self.keypair.read_bytes()
        return [
            raw.decode("utf-8", "replace"),      # the file as text
            raw.hex(),                            # hex
            base64.b64encode(raw).decode(),       # base64
            b58(raw),                            # base58
            str(list(self.SEED)),                 # the seed as a Python list
            repr(self.SEED),
            self.SEED.decode("latin-1"),          # the raw bytes read as text
        ]

    def assert_clean(self, text: str, what: str) -> None:
        for encoding in self.encodings():
            self.assertNotIn(encoding, text, f"{what} leaks key material")

    def a_chain(self) -> tuple[FakeChain, gw.EventChain]:
        chain_gateway = FakeChain(self.run_dir)
        chain_gateway._keys["seller"] = self.keypair
        chain_gateway._addresses["seller"] = address(2)
        event_chain = event(chain_gateway)
        chain_gateway.balances[event_chain.ticket_account("seller")] = 1
        return chain_gateway, event_chain

    def test_every_handed_out_object_is_clean(self):
        chain_gateway, event_chain = self.a_chain()
        result = event_chain.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        for value, what in (
            (repr(result), "repr(TransferResult)"),
            (str(result), "str(TransferResult)"),
            (repr(result.logs), "the transfer logs"),
            (repr(event_chain), "repr(EventChain)"),
            (str(event_chain), "str(EventChain)"),
            (repr(vars(event_chain)), "EventChain attributes"),
            (repr(chain_gateway.status()), "the status dict"),
            (json.dumps(chain_gateway.status(), default=str), "the status dict as JSON"),
            (repr(sorted(vars(chain_gateway))), "the gateway's attributes"),
        ):
            self.assert_clean(value, what)

    def test_an_exception_message_is_clean(self):
        chain_gateway, event_chain = self.a_chain()
        chain_gateway.balances[event_chain.ticket_account("seller")] = 0
        with self.assertRaises(gw.TicketNotHeld) as caught:
            event_chain.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assert_clean(str(caught.exception), "the TicketNotHeld message")

    def test_a_signer_failure_does_not_carry_the_file(self):
        chain_gateway, event_chain = self.a_chain()
        chain_gateway.sign_error = gw.dp.PublishError("the signer refused: bad keypair shape")
        with self.assertRaises(gw.dp.PublishError) as caught:
            event_chain.transfer(from_label="seller", to_label="buyer", price_lamports=CEILING)
        self.assert_clean(str(caught.exception), "the signer failure")

    def test_open_account_returns_an_address_and_never_a_path(self):
        chain_gateway, event_chain = self.a_chain()
        opened = event_chain.open_account("seller")
        self.assertEqual(opened, chain_gateway._addresses["seller"])
        self.assertRegex(opened, r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
        self.assertNotIn(".json", opened)
        self.assert_clean(opened, "open_account")


class SourceTest(unittest.TestCase):
    """Contract invariants 2 and 3, checked against the source rather than promised."""

    def setUp(self):
        self.source = (REPO_ROOT / "market_swarm" / "gateway.py").read_text(encoding="utf-8")

    def test_no_public_funding_call_shape(self):
        for shape in ("requestAirdrop", '"airdrop"', "faucet.solana.com", "solana airdrop"):
            self.assertNotIn(shape, self.source, f"the gateway must never ask a cluster for funds: {shape}")

    def test_the_only_faucet_reference_is_the_local_validators_own_port(self):
        # `LocalValidator` takes `faucet_port` and the validator binds it on 127.0.0.1; that is a
        # local port, not a funding path, and the constructor cannot be called without it.
        for line in self.source.splitlines():
            if "faucet" in line:
                self.assertIn("faucet_port", line, f"a faucet reference that is not the port: {line.strip()}")

    def test_no_mainnet(self):
        self.assertNotIn("mainnet", self.source.lower())
        self.assertIn('"https://api.devnet.solana.com"', self.source, "devnet is the only remote URL")

    def test_no_absolute_home_path(self):
        self.assertNotIn("/home/", self.source)

    def test_the_signing_context_is_never_shared(self):
        # A shared `Context` whose `keypair` is assigned before the signer child reads it is the
        # one way this module could sign with the wrong agent's key while two mints run at once.
        self.assertNotIn("self._ctx.keypair", self.source)
        self.assertIn("context = dp.Context(", self.source)

    def test_no_cargo_and_no_git(self):
        # The build may be *named* in a sentence a human reads ("never builds one"); it may never
        # be an argument to a child process. So the check is on quoted argv elements, not on the
        # word, and the sentence that promises no build has to still be there.
        for shape in ('"cargo"', "'cargo'", '"build-sbf"', '"git"', "'git'", '"push"', '"clone"'):
            self.assertNotIn(shape, self.source)
        self.assertIn("never builds one", self.source)

    def test_every_network_call_goes_through_the_bounded_reader(self):
        # One `urlopen`, `requests` or raw http client outside `dp.rpc` would be an unbounded
        # socket with its own retry story; there is none.
        for shape in ("urlopen", "requests.", "http.client", "socket.create_connection"):
            self.assertNotIn(shape, self.source)

    def test_the_approved_units_are_the_only_dp_functions_called(self):
        # Parsed, not grepped: a docstring that names `dp.account_exists` to explain why it is not
        # used is not a call site.
        tree = ast.parse(self.source)
        called = {
            node.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "dp"
        }
        approved = {
            # pure encoders
            "compile_message", "build_transaction", "shortvec", "AccountMeta", "Instruction",
            # instruction builders
            "instruction_init_extra_metas", "instruction_init_record",
            "instruction_set_pending_price", "instruction_transfer_checked",
            # the two tags the builders encode, so the v2 stage instruction and the writable
            # move name their own discriminators instead of restating 2 and 12 in this module
            "TAG_SET_PENDING_PRICE", "TOKEN_INSTRUCTION_TRANSFER_CHECKED",
            # bounded readers
            "rpc", "account_exists", "wait_for_account", "confirm", "transaction_details",
            "describe_error", "blockhash_is_dead", "derive_address",
            # the key boundary, the validator, the context
            "sign_message", "LocalValidator", "Context",
            # not functions: the exception type those units raise, the program ids the builders
            # need, the prebuilt artefact paths, and the base58 codec the tests reuse.
            "PublishError", "SYSTEM_PROGRAM", "TOKEN_2022_PROGRAM", "ASSOCIATED_TOKEN_PROGRAM",
            "SO_PATH", "PROGRAM_KEYPAIR", "base58",
        }
        self.assertEqual(called - approved, set(), "an unapproved devnet_publish unit is in use")
        self.assertFalse([name for name in called if name.startswith("step_")])
        # Two approved units are deliberately not called, both because they read at `finalized`
        # commitment: measured at 13 s of invisibility for a fresh account on this validator.
        self.assertNotIn("account_exists", called)
        self.assertNotIn("wait_for_account", called)
        self.assertIn("commitment", self.source)


class TransferResultTest(unittest.TestCase):
    def test_it_is_frozen_and_has_no_key_field(self):
        result = gw.TransferResult(status="ok")
        with self.assertRaises(FrozenInstanceError):
            result.status = "refused"  # type: ignore[misc]
        self.assertEqual(
            set(result.__dataclass_fields__),
            {
                "status", "signature", "slot", "block_time", "error_code", "latency_ms", "logs",
                # What the seller paid the artist in the same transaction. It has to be a field
                # and it has to default, because a transfer that moved nothing reports 0 and a
                # caller that predates the fee still constructs a result with six arguments.
                "fee_lamports",
                # The flip tax, added the same way and for the same reason: the money that moved,
                # the rate it was assessed at, and the hold the rate came from. All three default,
                # so a caller that predates the tax is unaffected; the two rate fields default to
                # None because an event without a policy has no rate and no hold to report.
                "flip_tax_lamports", "flip_tax_bps", "held_seconds",
            },
        )

    def test_the_simulated_marker_is_how_a_runner_tells_them_apart(self):
        self.assertFalse(gw.is_simulated(gw.TransferResult(status="ok", signature="s")))
        self.assertTrue(gw.is_simulated(gw.TransferResult(status="ok", logs=(gw.SIMULATED_LOG,))))


if __name__ == "__main__":
    unittest.main()

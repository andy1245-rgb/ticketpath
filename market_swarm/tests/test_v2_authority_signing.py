"""A v2 plain sale is signed twice: the seller moves the ticket, the house stages the price.

This is the fact that made `ChainGateway.start()` refuse v2 outright. v2's `SetPendingPrice` (tag
2) is `[authority (signer), record (writable), mint]`, and the program's
`checked_record_for_write` refuses `6026` for any key that is not the record's authority. v2's
`InitializeRecord` pins that authority to the mint's authority -- `mint_authority_of(mint)` is
compared against the signer -- and this gateway creates every mint and initialises every record
with one key, the house (`gateway.HOUSE_LABEL`). So the seller's own signature stages nothing, and
the two signatures are in one transaction: one blockhash, one message, stage-and-move still atomic.

What is asserted here, and why each one is worth a test:

- a v2 plain sale's compiled message requires **exactly** the seller and the house, and the set is
  read back out of the message with `signer_keys_from_message` rather than asserted from the call
  that built it -- the message is what a validator checks;
- a v1 plain sale still compiles to one signer, with the stage one account and no signer: v1's
  `SetPendingPrice` reads no signature at all, so adding the house key there would be a signature
  the message has no room for (`_send_multi` refuses exactly that);
- the fee and the flip-tax paths, which were two-signature paths before this change, still sign
  with both keys and build the same instructions in the same order;
- `start()` no longer refuses v2, and the body below the refusal still runs.

Nothing here boots a chain, opens a socket or reads a keypair. The fake cluster, the message
decoder and the fixture builders are `test_gateway`'s, imported rather than copied: one fake for
one gateway is one place for the signed bytes to be right.

Two tests here fail on the code before this change -- the stage authority and the `start()`
refusal -- and so does the signer-count one, because a seller-signed v2 stage needs one signature
and not two. That is what pins the fix.
"""

from __future__ import annotations

import base64
import tempfile
import unittest
from pathlib import Path

from market_swarm import artist_fee as af
from market_swarm import flip_tax as ft
from market_swarm import gateway as gw
from market_swarm.tests.test_gateway import (
    CEILING,
    FakeChain,
    NoSocket,
    address,
    decode_message,
    event,
)

ARTIST = address(31)
PRICE = CEILING


def sale_transaction(chain_gateway: FakeChain) -> dict:
    """The one transaction that was sent: its signatures, its signers, and its message.

    A legacy transaction is a compact-u16 signature count, that many 64-byte signatures, then the
    message. The signer set comes out of the *message* -- `signer_keys_from_message` reads the
    header and the key table -- so a test cannot pass by agreeing with the call that built it.
    """
    assert len(chain_gateway.sent) == 1, "one sale is one transaction"
    raw = base64.b64decode(chain_gateway.sent[0]["wire"])
    count = raw[0]
    message = raw[1 + 64 * count:]
    return {
        "count": count,
        "signatures": [raw[1 + 64 * i: 1 + 64 * (i + 1)] for i in range(count)],
        "signers": gw.signer_keys_from_message(message),
        "message": decode_message(message),
        "skipPreflight": chain_gateway.sent[0]["skipPreflight"],
    }


def event_with(chain_gateway: FakeChain, **policy) -> gw.EventChain:
    """`test_gateway.event()`, plus the fee or tax policy, which that helper does not carry.

    A fee or tax event is a different sale -- three or four instructions and two signatures --
    and the policy lives on the `EventChain` rather than on the spec, so the chain is rebuilt
    from the borrowed one's public fields with the policy added.
    """
    base = event(chain_gateway)
    return gw.EventChain(
        gateway=chain_gateway,
        event_id=base.event_id,
        mint=base.mint,
        record=base.record,
        extra_metas=base.extra_metas,
        mode=base.mode,
        cap_bps=base.cap_bps,
        face_lamports=base.face_lamports,
        ceiling_lamports=base.ceiling_lamports,
        **policy,
    )


class SaleCase(NoSocket, unittest.TestCase):
    """A fake cluster with a seller holding two tickets, and a buyer account that exists."""

    program = "v1"

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.chain_gateway = FakeChain(Path(self.tmp.name), program=self.program)
        self.chain_gateway.send_delay = 0
        self.event = event(self.chain_gateway)
        self.seller = self.chain_gateway._addresses["seller"]
        self.house = self.chain_gateway._addresses[gw.HOUSE_LABEL]
        self.chain_gateway.balances[self.event.ticket_account("seller")] = 2
        # Funded well above the float and above any fee or tax this file prices, so a sale is one
        # transaction: a wallet below the floor is topped up first, and that is a second send.
        self.chain_gateway.lamports[self.seller] = 10**12
        self.event.ticket_account("buyer", create=True)

    def sell(self, **overrides) -> dict:
        result = self.event.transfer(
            from_label=overrides.pop("from_label", "seller"),
            to_label="buyer",
            price_lamports=overrides.pop("price_lamports", PRICE),
            **overrides,
        )
        self.assertEqual(result.status, "ok", result.logs)
        return sale_transaction(self.chain_gateway)

    def signer_paths(self) -> list[str]:
        return [path.name for path in self.chain_gateway.signers]


class V2PlainSaleTest(SaleCase):
    """The change: two keys on a plain v2 sale, and the stage names the record's authority."""

    program = "v2"

    def test_the_message_requires_exactly_the_seller_and_the_house(self):
        sent = self.sell()
        self.assertEqual(sent["count"], 2)
        self.assertEqual(
            sent["signers"], (self.seller, self.house),
            "the payer signs first, then the record's authority",
        )
        self.assertEqual(sent["message"]["header"][0], 2, "the header agrees with the reader")
        self.assertEqual(sent["message"]["keys"][0], self.seller, "the fee payer is still the seller")
        self.assertEqual(self.signer_paths(), ["seller.json", "authority.json"])
        self.assertEqual(len(sent["signatures"]), 2)
        self.assertEqual(len({path for path in self.signer_paths()}), 2,
                         "two keys signed it, not one key twice")

    def test_the_stage_names_the_house_and_the_mint_and_the_seller_is_not_on_it(self):
        # FAILS on the code before this change: the stage named the seller, which the program
        # refuses 6026 for, and the message then needed one signature instead of two.
        sent = self.sell()
        stage = sent["message"]["instructions"][0]
        self.assertEqual(sent["message"]["keys"][stage["program"]], self.chain_gateway.program_id)
        self.assertEqual(stage["data"], bytes([2]) + PRICE.to_bytes(8, "little"), "tag 2, the price")
        self.assertEqual(
            [sent["message"]["keys"][index] for index in stage["accounts"]],
            [self.house, self.chain_gateway.record_account, self.event.mint],
            "v2 stages with [authority, record, mint] and the authority is the record's",
        )
        self.assertNotIn(self.seller, [sent["message"]["keys"][i] for i in stage["accounts"]])

    def test_the_move_keeps_the_seller_as_its_authority_and_the_record_writable(self):
        sent = self.sell()
        move = sent["message"]["instructions"][1]
        self.assertEqual(sent["message"]["keys"][move["program"]], gw.dp.TOKEN_2022_PROGRAM)
        self.assertEqual(move["data"], bytes([12]) + (1).to_bytes(8, "little") + bytes([0]))
        self.assertEqual(
            [sent["message"]["keys"][index] for index in move["accounts"]][3], self.seller,
            "the token account's authority is the seller, as on every sale",
        )
        # Writability is a per-instruction flag, and it merges in the message; the built
        # instruction is where the per-program difference lives.
        _, module_move = self.chain_gateway.instructions[-1]
        record_meta = [
            meta for meta in module_move.accounts
            if meta.pubkey == self.chain_gateway.record_account
        ]
        self.assertEqual(len(record_meta), 1, "one record account, once")
        self.assertTrue(record_meta[0].is_writable, "v2's hook writes held_since_unix into it")

    def test_the_house_selling_its_own_stock_is_one_signature(self):
        # A primary sale: the seller is the record's authority, so the two keys are one key and
        # `_send_multi`'s set check has to see one required signer and one path.
        self.chain_gateway.balances[self.event.ticket_account(gw.HOUSE_LABEL)] = 2
        sent = self.sell(from_label=gw.HOUSE_LABEL)
        self.assertEqual(sent["count"], 1)
        self.assertEqual(sent["signers"], (self.house,))
        self.assertEqual(self.signer_paths(), ["authority.json"])


class V1PlainSaleTest(SaleCase):
    """The other half: v1's stage reads no signer, so a v1 sale keeps one signature."""

    program = "v1"

    def test_a_v1_plain_sale_still_compiles_to_one_signer(self):
        sent = self.sell()
        self.assertEqual(sent["count"], 1)
        self.assertEqual(sent["signers"], (self.seller,), "the seller, and nobody else")
        self.assertEqual(sent["message"]["header"][0], 1)
        self.assertEqual(self.signer_paths(), ["seller.json"])
        self.assertNotIn(
            self.chain_gateway._addresses[gw.HOUSE_LABEL], sent["message"]["keys"],
            "a v1 run does not even name the house in the message",
        )

    def test_the_v1_stage_is_still_one_account_and_no_signer(self):
        sent = self.sell()
        stage = sent["message"]["instructions"][0]
        self.assertEqual(stage["data"], bytes([2]) + PRICE.to_bytes(8, "little"))
        self.assertEqual(
            [sent["message"]["keys"][index] for index in stage["accounts"]],
            [self.chain_gateway.record_account],
            "v1 stages against the record alone",
        )
        # The record is on the move, read-only, because v1's hook writes nothing into it.
        module_stage, module_move = self.chain_gateway.instructions[-1]
        record_meta = [
            meta for meta in module_move.accounts
            if meta.pubkey == self.chain_gateway.record_account
        ]
        self.assertEqual(len(record_meta), 1, "the record appears once in the move")
        self.assertFalse(record_meta[0].is_writable, "v1's hook writes nothing")
        self.assertEqual([meta.is_signer for meta in module_stage.accounts], [False],
                         "one account, and it is not a signer")


class V2StartTest(SaleCase):
    """`start()` no longer refuses v2: the body below the old refusal runs."""

    program = "v2"

    def test_start_does_not_refuse_v2_and_walks_the_boot_body(self):
        # FAILS on the code before this change, with `ChainUnavailable` and the "the signer is the
        # missing piece" sentence. The seam is the smallest one that reaches the body: the
        # gateway is the fake (its RPC, signer, child-process and account seams are dictionaries),
        # the program id is answered instead of derived from a `.so` on disk, and the validator
        # boot itself is a recorder. Everything else in `start()` is the real code, and the test
        # asserts that nothing was generated and no child was spawned.
        chain_gateway = self.chain_gateway
        chain_gateway._started = False
        chain_gateway._program_id_from_disk = lambda: address(9)
        booted: list[Path] = []
        chain_gateway._start_local = booted.append
        self.addCleanup(chain_gateway.stop)

        status = chain_gateway.start()

        self.assertTrue(chain_gateway._started)
        self.assertEqual(status["program"], "v2")
        self.assertEqual(status["program_id"], address(9))
        self.assertEqual(len(booted), 1, "the local boot was reached, once")
        self.assertEqual(
            booted[0], chain_gateway._wallet_path(gw.HOUSE_LABEL),
            "the house keypair is the one the boot is handed",
        )
        self.assertEqual(
            [call for call in chain_gateway.calls if call[0] == "run"], [],
            "no keygen, no deploy: nothing was spawned to get here",
        )


class TheTwoSignaturePathsThisChangeDidNotTouch(SaleCase):
    """The fee and flip-tax sales were two-signature sales before v2 could run, and are unchanged."""

    program = "v2"

    def fee_event(self) -> None:
        self.event = event_with(
            self.chain_gateway,
            artist_fee=af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=250),
        )
        self.chain_gateway.balances[self.event.ticket_account("seller")] = 2
        self.event.ticket_account("buyer", create=True)

    def test_the_artist_fee_sale_still_signs_with_both_keys(self):
        self.fee_event()
        sent = self.sell()
        self.assertEqual(sent["count"], 2)
        self.assertEqual(sent["signers"], (self.seller, self.house))
        self.assertEqual(self.signer_paths(), ["seller.json", "authority.json"])
        instructions = sent["message"]["instructions"]
        self.assertEqual(
            [sent["message"]["keys"][step["program"]] for step in instructions],
            [self.chain_gateway.program_id, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "stage, then the fee, then the move",
        )
        fee = instructions[1]
        expected = PRICE * 250 // 10_000
        self.assertEqual(fee["data"], (2).to_bytes(4, "little") + expected.to_bytes(8, "little"))
        self.assertEqual(
            [sent["message"]["keys"][index] for index in fee["accounts"]],
            [self.seller, ARTIST],
        )

    def test_the_flip_tax_sale_still_signs_with_both_keys(self):
        self.event = event_with(
            self.chain_gateway,
            flip_tax=ft.FlipTaxPolicy(
                artist_wallet=ARTIST, enabled=True, schedule=ft.DEFAULT_SCHEDULE
            ),
        )
        self.chain_gateway.balances[self.event.ticket_account("seller")] = 2
        self.event.ticket_account("buyer", create=True)
        sent = self.sell()
        self.assertEqual(sent["count"], 2)
        self.assertEqual(sent["signers"], (self.seller, self.house))
        instructions = sent["message"]["instructions"]
        self.assertEqual(
            [sent["message"]["keys"][step["program"]] for step in instructions],
            [self.chain_gateway.program_id, gw.dp.SYSTEM_PROGRAM, gw.dp.TOKEN_2022_PROGRAM],
            "stage, then the tax, then the move",
        )
        tax = instructions[1]
        self.assertEqual(tax["data"][:4], (2).to_bytes(4, "little"), "a System transfer")
        self.assertGreater(
            int.from_bytes(tax["data"][4:12], "little"), 0,
            "the fake record's hold clock is 0, so the full rate applies",
        )
        self.assertEqual(
            [sent["message"]["keys"][index] for index in tax["accounts"]],
            [self.seller, ARTIST],
        )


class TestTheDeployFollowsTheProgram(unittest.TestCase):
    """The deploy names the `.so` and the keypair of the program the run selected.

    This is the second thing the `start()` refusal was hiding. `_deploy` used to take both from
    `devnet_publish`'s v1 constants whatever `self.program` was, so a v2 run deployed v2's
    bytecode under v1's keypair -- one program's bytes at the other program's address -- and then
    waited for an account at v2's id that nothing had been deployed to. Both halves follow the
    name now, and the two `.so` paths differ, which is what makes "which bytes ran" answerable.
    """

    def deploy_command(self, program: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            chain_gateway = FakeChain(Path(tmp), program=program)
            chain_gateway._deploy()
        deploy = [call for call in chain_gateway.calls if call[0] == "run"]
        self.assertEqual(len(deploy), 1, "a deploy is one child")
        return deploy[0][1]

    def test_a_v2_run_deploys_v2s_so_and_v2s_keypair(self) -> None:
        command = self.deploy_command("v2")
        self.assertEqual(command[command.index("deploy") + 1], str(gw.dp.SO_PATH))
        self.assertEqual(
            command[command.index("--program-id") + 1],
            str(gw.PROGRAM_KEYPAIRS["v2"]),
        )
        self.assertTrue(gw.PROGRAM_KEYPAIRS["v2"].name.startswith("v2-"))

    def test_a_v1_run_deploys_the_v1_build_and_not_the_v2_one(self) -> None:
        command = self.deploy_command("v1")
        self.assertEqual(
            command[command.index("deploy") + 1], str(gw.PROGRAM_BINARIES["v1"])
        )
        self.assertNotEqual(
            gw.PROGRAM_BINARIES["v1"], gw.PROGRAM_BINARIES["v2"],
            "one shared path would make which bytes ran depend on which build ran last",
        )
        self.assertEqual(
            command[command.index("--program-id") + 1],
            str(gw.dp.PROGRAM_KEYPAIR),
        )

    def test_the_two_keypairs_are_two_files(self) -> None:
        self.assertNotEqual(gw.PROGRAM_KEYPAIRS["v1"], gw.PROGRAM_KEYPAIRS["v2"])


class TestThePortsTheValidatorMayNotTake(unittest.TestCase):
    """A picked port must never be one another service owns.

    `_free_port` binds port 0 and asks the kernel what it gave; that cannot reserve anything, so
    the only guarantee available is to refuse the ports whose owner is known. 3010 is a live web
    server on this machine and 8795 is kept back for one; a validator that took either would take
    a service down instead of failing.
    """

    def test_the_two_named_ports_are_reserved(self) -> None:
        self.assertIn(3010, gw._RESERVED_PORTS)
        self.assertIn(8795, gw._RESERVED_PORTS)

    def test_free_port_refuses_rather_than_returning_one_of_them(self) -> None:
        class AlwaysReserved:
            def __init__(self, *args, **kwargs) -> None:
                pass

            def setsockopt(self, *args) -> None:
                pass

            def bind(self, *args) -> None:
                pass

            def getsockname(self):
                return ("127.0.0.1", 3010)

            def __enter__(self):
                return self

            def __exit__(self, *exc) -> bool:
                return False

        original = gw.socket.socket
        gw.socket.socket = AlwaysReserved
        try:
            with self.assertRaises(gw.ChainUnavailable):
                gw._free_port()
        finally:
            gw.socket.socket = original

    def test_a_free_port_is_still_found_when_one_is_offered(self) -> None:
        # The refusal above must not have turned into a function that never answers.
        port = gw._free_port()
        self.assertGreater(port, 1024)
        self.assertNotIn(port, gw._RESERVED_PORTS)


if __name__ == "__main__":  # pragma: no cover - the suite runs it through discovery
    unittest.main()

"""The wire format follows the program: v1's bytes, v2's bytes, and no way to confuse them.

Two things are checked here, and they are different questions:

* **What each encoder produces** is compared, byte for byte, with the module that already
  describes that wire -- `tools/devnet_publish.py` for v1 (the bytes that landed on devnet) and
  `ticketpath/onchain/v2.py` for v2 (the client half of the local program). A change on either
  side that is not made on both is a failing test here rather than two implementations that
  drifted apart quietly.
* **That a run cannot emit the other program's shape.** The program is an argument to every
  encoder, there is no default, and the two shapes differ in the places a mistake would show: a
  v1 `InitializeExtraAccountMetaList` carries the record and a v2 one does not, a v2
  `InitializeRecord` is 22 bytes against v1's 11, v2's `SetPendingPrice` needs a signer, and v2's
  transfer makes the record writable so the hook can write the hold clock into it.

Nothing here opens a socket, reads an RPC response or needs a validator.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from market_swarm import gateway as gw
from market_swarm import wire
from ticketpath.onchain import v2

FACE = 1_000_000_000
CAP_BPS = 2500

PAYER = gw.dp.base58.encode(bytes([1]) * 32)
MINT = gw.dp.base58.encode(bytes([2]) * 32)
RECORD = gw.dp.base58.encode(bytes([3]) * 32)
EXTRA = gw.dp.base58.encode(bytes([4]) * 32)
PROGRAM = gw.dp.base58.encode(bytes([5]) * 32)
AUTHORITY = gw.dp.base58.encode(bytes([6]) * 32)
SOURCE = gw.dp.base58.encode(bytes([7]) * 32)
DESTINATION = gw.dp.base58.encode(bytes([8]) * 32)


def accounts(instruction) -> tuple:
    """`(pubkey, is_signer, is_writable)` for each account, the shape both sources use."""
    return tuple(
        (meta.pubkey, meta.is_signer, meta.is_writable) for meta in instruction.accounts
    )


class TestTheTagSets(unittest.TestCase):
    def test_v1_has_four_tags_and_v2_has_seven(self) -> None:
        self.assertEqual(wire.tags_for("v1"), frozenset({0, 1, 2, 3}))
        self.assertEqual(wire.tags_for("v2"), frozenset(range(7)))

    def test_the_tags_v1_does_not_have_are_the_three_satellites(self) -> None:
        # Naming them is what makes "a v1 run carries no v2 tag" a check rather than a hope.
        self.assertEqual(
            wire.tags_for("v2") - wire.tags_for("v1"),
            frozenset({wire.TAG_PUBLISH_BAND, wire.TAG_LOG_FORECAST, wire.TAG_SCORE_FORECAST}),
        )
        self.assertEqual(wire.tags_for("v2") - wire.tags_for("v1"), frozenset({4, 5, 6}))

    def test_an_unknown_program_is_refused_by_every_entry_point(self) -> None:
        with self.assertRaises(ValueError) as caught:
            wire.tags_for("v3")
        self.assertIn("program", str(caught.exception))
        with self.assertRaises(ValueError):
            wire.instruction_init_extra_metas(
                "v3", payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA, program_id=PROGRAM
            )
        with self.assertRaises(ValueError):
            wire.decode_record("v3", bytes(19))

    def test_the_vocabulary_is_the_configs(self) -> None:
        from market_swarm.config import PROGRAMS

        self.assertEqual(set(wire.TAGS), set(PROGRAMS))


class TestTheV1FormatIsThePublishedOne(unittest.TestCase):
    """v1's encoders are `devnet_publish`'s, so the check is that they are still the same ones."""

    def test_init_extra_metas_is_byte_for_byte_the_published_builder(self) -> None:
        ours = wire.instruction_init_extra_metas(
            "v1", payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA, program_id=PROGRAM
        )
        theirs = gw.dp.instruction_init_extra_metas(
            payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA, program_id=PROGRAM
        )
        self.assertEqual(accounts(ours), accounts(theirs))
        self.assertEqual(ours.data, theirs.data)
        # v1 takes the record as an argument: the tag, then the 32-byte account.
        self.assertEqual(len(ours.data), 1 + 32)
        self.assertEqual(ours.data[0], wire.TAG_INIT_EXTRA_METAS)

    def test_init_record_is_byte_for_byte_the_published_builder(self) -> None:
        ours = wire.instruction_init_record(
            "v1",
            payer=PAYER,
            mint=MINT,
            record=RECORD,
            program_id=PROGRAM,
            face=FACE,
            cap_bps=CAP_BPS,
            mint_authority=AUTHORITY,
            mode="capped",
        )
        theirs = gw.dp.instruction_init_record(
            payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE, cap_bps=CAP_BPS
        )
        self.assertEqual(accounts(ours), accounts(theirs), "v1's record has no mint-authority signer")
        self.assertEqual(ours.data, theirs.data)
        self.assertEqual(len(ours.data), 1 + 8 + 2)

    def test_set_pending_price_is_byte_for_byte_the_published_builder(self) -> None:
        ours = wire.instruction_set_pending_price(
            "v1", record=RECORD, program_id=PROGRAM, price=FACE, authority=AUTHORITY, mint=MINT
        )
        theirs = gw.dp.instruction_set_pending_price(record=RECORD, program_id=PROGRAM, price=FACE)
        self.assertEqual(accounts(ours), accounts(theirs), "v1 stages with the record alone")
        self.assertEqual(ours.data, theirs.data)
        self.assertFalse(any(meta[1] for meta in accounts(ours)), "v1 reads no signer at all")

    def test_transfer_checked_is_byte_for_byte_the_published_builder(self) -> None:
        ours = wire.instruction_transfer_checked(
            "v1",
            source=SOURCE,
            mint=MINT,
            destination=DESTINATION,
            authority=AUTHORITY,
            record=RECORD,
            hook_program=PROGRAM,
            extra_metas=EXTRA,
        )
        theirs = gw.dp.instruction_transfer_checked(
            source=SOURCE,
            mint=MINT,
            destination=DESTINATION,
            authority=AUTHORITY,
            record=RECORD,
            hook_program=PROGRAM,
            extra_metas=EXTRA,
        )
        self.assertEqual(accounts(ours), accounts(theirs))
        self.assertEqual(ours.data, theirs.data)

    def test_every_tag_a_v1_run_emits_is_a_v1_tag(self) -> None:
        emitted = [
            wire.instruction_init_extra_metas(
                "v1", payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA,
                program_id=PROGRAM,
            ).data,
            wire.instruction_init_record(
                "v1", payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE,
                cap_bps=CAP_BPS,
            ).data,
            wire.instruction_set_pending_price(
                "v1", record=RECORD, program_id=PROGRAM, price=FACE
            ).data,
        ]
        for data in emitted:
            with self.subTest(tag=data[0]):
                self.assertIn(data[0], wire.tags_for("v1"))
                self.assertNotIn(data[0], wire.tags_for("v2") - wire.tags_for("v1"))


class TestTheV2FormatIsTheOnchainClients(unittest.TestCase):
    """v2's encoders are this package's, pinned against `ticketpath/onchain/v2.py`."""

    def test_init_extra_metas_matches_the_client_and_carries_no_record(self) -> None:
        ours = wire.instruction_init_extra_metas(
            "v2", payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA, program_id=PROGRAM
        )
        self.assertEqual(ours.data, v2.initialize_extra_account_meta_list())
        self.assertEqual(len(ours.data), 1, "v2 derives the record from the mint and takes no argument")
        self.assertEqual(
            accounts(ours), v2.initialize_extra_account_meta_list_accounts(
                payer=PAYER, mint=MINT, extra_metas=EXTRA
            )
        )
        self.assertNotIn(RECORD, [meta[0] for meta in accounts(ours)])

    def test_init_record_matches_the_client_byte_for_byte(self) -> None:
        ours = wire.instruction_init_record(
            "v2",
            payer=PAYER,
            mint=MINT,
            record=RECORD,
            program_id=PROGRAM,
            face=FACE,
            cap_bps=CAP_BPS,
            mint_authority=AUTHORITY,
            mode="monitored",
        )
        theirs = v2.initialize_record(
            face_value_lamports=FACE,
            cap_bps=CAP_BPS,
            band_low_lamports=wire.NO_FLOOR_LAMPORTS,
            jurisdiction=wire.NO_JURISDICTION,
            policy=wire.POLICY_MONITORED,
        )
        self.assertEqual(ours.data, theirs)
        self.assertEqual(len(ours.data), v2.INITIALIZE_RECORD_DATA_LEN)
        self.assertEqual(
            accounts(ours),
            v2.initialize_record_accounts(
                payer=PAYER, mint=MINT, record=RECORD, mint_authority=AUTHORITY
            ),
        )

    def test_the_policy_byte_follows_the_mode_and_the_floor_is_neutral(self) -> None:
        def data(mode: str) -> bytes:
            return wire.instruction_init_record(
                "v2", payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE,
                cap_bps=CAP_BPS, mint_authority=AUTHORITY, mode=mode,
            ).data

        capped, monitored = data("capped"), data("monitored")
        self.assertEqual(capped[21], wire.POLICY_CAPPED)
        self.assertEqual(monitored[21], wire.POLICY_MONITORED)
        self.assertEqual(capped[:21], monitored[:21], "only the policy byte changes with the mode")
        # The tag is byte 0, so the payload offsets are the layout's plus one.
        self.assertEqual(capped[11:19], (0).to_bytes(8, "little"), "no floor is declared by this harness")
        self.assertEqual(capped[19:21], b"ZZ", "and no jurisdiction")

    def test_set_pending_price_matches_the_client_and_names_a_signer(self) -> None:
        ours = wire.instruction_set_pending_price(
            "v2", record=RECORD, program_id=PROGRAM, price=FACE, authority=AUTHORITY, mint=MINT
        )
        self.assertEqual(ours.data, v2.set_pending_price(price_lamports=FACE))
        self.assertEqual(
            accounts(ours),
            v2.set_pending_price_accounts(authority=AUTHORITY, record=RECORD, mint=MINT),
        )
        self.assertEqual([meta[1] for meta in accounts(ours)], [True, False, False],
                         "v2 stages with the record's authority as the only signer")

    def test_the_transfer_makes_the_record_writable_for_the_hold_clock(self) -> None:
        v1_move = wire.instruction_transfer_checked(
            "v1", source=SOURCE, mint=MINT, destination=DESTINATION, authority=AUTHORITY,
            record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA,
        )
        v2_move = wire.instruction_transfer_checked(
            "v2", source=SOURCE, mint=MINT, destination=DESTINATION, authority=AUTHORITY,
            record=RECORD, hook_program=PROGRAM, extra_metas=EXTRA,
        )
        self.assertEqual(len(accounts(v1_move)), 7)
        self.assertEqual(len(accounts(v2_move)), 7)
        record_index = [meta[0] for meta in accounts(v1_move)].index(RECORD)
        self.assertFalse(accounts(v1_move)[record_index][2], "v1's hook writes nothing")
        self.assertTrue(accounts(v2_move)[record_index][2], "v2 writes held_since_unix")
        self.assertEqual(v1_move.data, v2_move.data, "the data is Token-2022's, not the program's")

    def test_the_v2_encoders_refuse_the_missing_v2_arguments(self) -> None:
        with self.assertRaises(ValueError) as caught:
            wire.instruction_init_record(
                "v2", payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE,
                cap_bps=CAP_BPS,
            )
        self.assertIn("mint_authority", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            wire.instruction_init_record(
                "v2", payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE,
                cap_bps=CAP_BPS, mint_authority=AUTHORITY,
            )
        self.assertIn("mode", str(caught.exception))
        with self.assertRaises(ValueError) as caught:
            wire.instruction_set_pending_price(
                "v2", record=RECORD, program_id=PROGRAM, price=FACE
            )
        self.assertIn("authority", str(caught.exception))

    def test_every_tag_a_v2_run_emits_is_a_v2_tag(self) -> None:
        emitted = [
            wire.instruction_init_extra_metas(
                "v2", payer=PAYER, mint=MINT, record=RECORD, extra_metas=EXTRA,
                program_id=PROGRAM,
            ).data,
            wire.instruction_init_record(
                "v2", payer=PAYER, mint=MINT, record=RECORD, program_id=PROGRAM, face=FACE,
                cap_bps=CAP_BPS, mint_authority=AUTHORITY, mode="capped",
            ).data,
            wire.instruction_set_pending_price(
                "v2", record=RECORD, program_id=PROGRAM, price=FACE, authority=AUTHORITY, mint=MINT
            ).data,
        ]
        for data in emitted:
            with self.subTest(tag=data[0]):
                self.assertIn(data[0], wire.tags_for("v2"))


class TestTheRecordAccountReadsBackUnderItsOwnProgram(unittest.TestCase):
    def v1_bytes(self, *, pending: int = 0, status: int = 1) -> bytes:
        return (
            FACE.to_bytes(8, "little")
            + CAP_BPS.to_bytes(2, "little")
            + pending.to_bytes(8, "little")
            + bytes([status])
        )

    def v2_bytes(self) -> bytes:
        return (
            FACE.to_bytes(8, "little")
            + CAP_BPS.to_bytes(2, "little")
            + (0).to_bytes(8, "little")
            + bytes([1])
            + (0).to_bytes(8, "little")
            + b"CA"
            + bytes([wire.POLICY_CAPPED])
            + (1_700_000_000).to_bytes(8, "little", signed=True)
            + bytes([9]) * 32
        )

    def test_v1_decodes_nineteen_bytes(self) -> None:
        decoded = wire.decode_record("v1", self.v1_bytes(pending=5, status=1))
        self.assertEqual(
            decoded,
            {"face_lamports": FACE, "cap_bps": CAP_BPS, "pending_price_lamports": 5, "status": 1},
        )

    def test_v1_refuses_the_v2_length(self) -> None:
        with self.assertRaises(ValueError) as caught:
            wire.decode_record("v1", self.v2_bytes())
        self.assertIn("19", str(caught.exception))

    def test_v2_refuses_the_v1_length(self) -> None:
        with self.assertRaises(ValueError) as caught:
            wire.decode_record("v2", self.v1_bytes())
        self.assertIn("70", str(caught.exception))

    def test_v2_decodes_seventy_bytes_the_way_the_onchain_client_does(self) -> None:
        raw = self.v2_bytes()
        self.assertEqual(len(raw), v2.TICKET_RECORD_LAYOUT[-1][1] + v2.TICKET_RECORD_LAYOUT[-1][2])
        ours = wire.decode_record("v2", raw)
        theirs = v2.decode_ticket_record(raw)
        self.assertEqual(ours["face_value_lamports"], theirs.face_value_lamports)
        self.assertEqual(ours["cap_bps"], theirs.cap_bps)
        self.assertEqual(ours["pending_price_lamports"], theirs.pending_price_lamports)
        self.assertEqual(ours["status"], theirs.status)
        self.assertEqual(ours["band_low_lamports"], theirs.band_low_lamports)
        self.assertEqual(ours["jurisdiction"], theirs.jurisdiction)
        self.assertEqual(ours["policy"], theirs.policy)
        self.assertEqual(ours["held_since_unix"], theirs.held_since_unix)
        self.assertEqual(ours["authority"], theirs.authority)
        self.assertEqual(ours["jurisdiction"], b"CA")
        self.assertEqual(ours["policy"], wire.POLICY_CAPPED)

    def test_the_gateways_own_decoder_is_the_v1_one(self) -> None:
        # `gateway.decode_record` predates the switch and is still the entry point a caller with a
        # v1 buffer uses; it must be the same reader, not a copy that can drift.
        self.assertEqual(gw.decode_record(self.v1_bytes()), wire.decode_v1_record(self.v1_bytes()))
        with self.assertRaises(ValueError):
            gw.decode_record(self.v2_bytes())


def _keypair_address(path: Path) -> str | None:
    """The base58 address a keypair file derives, or `None` when the file is not there.

    Here in the test and not in the package: a Solana keypair file holds the secret half, and the
    package's rule is that only `gateway.py` names one. A test that pins the gateway's stated ids
    to the keypairs they come from is the check the rule leaves room for.
    """
    if not path.exists():
        return None
    values = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(values, list) or len(values) != 64:
        return None
    return gw.dp.base58.encode(bytes(values[32:64]))


class TestTheStatedProgramIdsAreTheKeypairs(unittest.TestCase):
    """The address in `gateway.PROGRAM_IDS` is the pubkey of the keypair it deploys with.

    Skipped when there is no build: the keypairs live in `programs/cap_hook/target/deploy`, which
    a fresh clone does not have. Nothing here needs the network.
    """

    def test_each_id_is_its_keypairs_own_address(self) -> None:
        for program, keypair in gw.PROGRAM_KEYPAIRS.items():
            with self.subTest(program=program):
                address = _keypair_address(keypair)
                if address is None:
                    self.skipTest(f"no keypair at {keypair.name}: nothing built in this tree")
                self.assertEqual(address, gw.PROGRAM_IDS[program])

    def test_v1_is_the_frozen_address_the_publish_tool_deploys_to(self) -> None:
        # This half needs no build: the frozen constant is in the tool that deployed it, so the
        # gateway's stated address is pinned even in a checkout with no `target/deploy`.
        self.assertEqual(gw.PROGRAM_IDS["v1"], gw.dp.FROZEN_DEVNET_PROGRAM)

    def test_the_two_programs_are_two_different_addresses(self) -> None:
        self.assertEqual(len(set(gw.PROGRAM_IDS.values())), 2)
        self.assertEqual(set(gw.PROGRAM_IDS), set(gw.PROGRAM_KEYPAIRS))

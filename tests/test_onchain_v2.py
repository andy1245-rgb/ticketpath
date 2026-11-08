"""The v2 wire format, pinned: instruction bytes, account offsets, PDA derivation.

What this file is for, and what it refuses to assume:

1. **The bytes are the contract.** Every instruction builder is checked against a literal
   byte string, parsed back, and re-built from the parse. A builder and a parser that both
   change together still fail here, because the literal does not.
2. **The offsets are the contract too.** Each decoder is fed a buffer whose every field holds
   a distinct, recognisable value at the documented offset, so a field silently moved by two
   bytes cannot pass as "still 70 bytes long".
3. **The Rust is the source.** `programs/cap_hook/src/lib.rs` and `state.rs` are read from
   this test and compared with the constants here: the tag-1 unpack slices, the documented
   argument widths, the struct field order, and the `LEN` constants. If either side changes
   alone, this file fails rather than letting two implementations drift.
4. **A short buffer raises.** Every decoder, every truncation length. A decoder that pads is
   a client that decides a transfer is safe on bytes it never received.

Nothing here touches a cluster. The live half is `tests/test_onchain_v2_live.py`.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from ticketpath.core import base58
from ticketpath.onchain import v2

RUST_SRC = Path(__file__).resolve().parents[1] / "programs" / "cap_hook" / "src"

# A devnet program and mint that were measured, not invented: `records/devnet-artefacts.json`
# holds both, and the addresses below were read back from `solana find-program-derived-address`
# against them. They are public identifiers and carry no key material. They are also the only
# independent check this file has that `find_program_address` is the runtime's algorithm and
# not an approximation of it.
DEVNET_PROGRAM = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"
DEVNET_MINT = "6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV"
MEASURED = {
    "record": ("FBqu9x92hwbNXdmBneZmKEHwceDFy48ZPSMPaTJtNSca", 254),
    "extra-account-metas": ("Drbm332n7YMeVuetYjCw7bhBrhs3MZ4Wmqh1pAWPhYmo", 255),
    "band": ("GWVKyGeMfiT7grwfVgLkQHezGS15xqiJj1PeS77JnHW3", 255),
    "forecast": ("G29a8bnJcAaqPDYNzeZFh9mYsQfrGVWkc4spHJQhQjoY", 254),
    "score": ("CcLr2Nd2QJAiXRaUCW4XKGnsLJfGE7zRhRwni9BfDCGf", 255),
    "fee-authority": ("5hJWVS1vBxqkjUJz5T8VKKt3EYK8vb7acKHvsX9CyaMs", 254),
    "rebate-pool": ("HdDHLEgj38Wk4HpkYCWofjuXyAXxfVPjsj7n92YZN6cC", 255),
}


def _bytes_at(value: int, width: int, signed: bool = False) -> bytes:
    return value.to_bytes(width, "little", signed=signed)


def _key(fill: int) -> bytes:
    return bytes([fill]) * 32


class TestInstructionBytes(unittest.TestCase):
    def test_initialize_record_is_twenty_two_bytes_and_round_trips(self) -> None:
        # The operator's own arguments for the local proof: face 1 SOL, cap 2500 bps, floor
        # 0.9 SOL, jurisdiction ZZ, policy 0. Written out byte by byte, so a changed field
        # order fails here even if the total length stays 22.
        data = v2.initialize_record(
            face_value_lamports=1_000_000_000,
            cap_bps=2500,
            band_low_lamports=900_000_000,
            jurisdiction="ZZ",
            policy=0,
        )
        self.assertEqual(
            data.hex(),
            "01"
            "00ca9a3b00000000"  # 1_000_000_000
            "c409"              # 2500
            "00e9a43500000000"  # 900_000_000
            "5a5a"              # "ZZ"
            "00",               # policy 0
        )
        self.assertEqual(len(data), 22)
        self.assertEqual(len(data) - 1, v2.INITIALIZE_RECORD_PAYLOAD_LEN)
        self.assertEqual(len(data), v2.INITIALIZE_RECORD_DATA_LEN)

        parsed = v2.parse_instruction(data)
        self.assertIsInstance(parsed, v2.InitializeRecord)
        self.assertEqual(parsed.face_value_lamports, 1_000_000_000)
        self.assertEqual(parsed.cap_bps, 2500)
        self.assertEqual(parsed.band_low_lamports, 900_000_000)
        self.assertEqual(parsed.jurisdiction, b"ZZ")
        self.assertEqual(parsed.policy, 0)
        self.assertEqual(parsed.data, data, "build(parse(bytes)) must be bytes")

    def test_initialize_extra_account_meta_list_is_the_tag_alone(self) -> None:
        # The record is derived from the mint by the program, so there is no argument to name
        # the wrong account: the list is create-once and 6020 against a wrong record is forever.
        data = v2.initialize_extra_account_meta_list()
        self.assertEqual(data, b"\x00")
        self.assertEqual(len(data), v2.INITIALIZE_EXTRA_ACCOUNT_META_LIST_DATA_LEN)
        self.assertEqual(len(data) - 1, v2.INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD_LEN)
        self.assertIsInstance(v2.parse_instruction(data), v2.InitializeExtraAccountMetaList)
        self.assertEqual(v2.parse_instruction(data).data, data)

    def test_set_pending_price_is_the_tag_and_a_u64(self) -> None:
        data = v2.set_pending_price(price_lamports=1_250_000_000)
        self.assertEqual(data, bytes([2]) + _bytes_at(1_250_000_000, 8))
        self.assertEqual(len(data), 9)
        parsed = v2.parse_instruction(data)
        self.assertEqual(parsed.price_lamports, 1_250_000_000)
        self.assertEqual(parsed.data, data)

    def test_set_status_is_the_tag_and_a_u8(self) -> None:
        for status in (0, 1, 255):
            with self.subTest(status=status):
                data = v2.set_status(status=status)
                self.assertEqual(data, bytes([3, status]))
                self.assertEqual(len(data), 2)
                self.assertEqual(v2.parse_instruction(data).status, status)
                self.assertEqual(v2.parse_instruction(data).data, data)

    def test_the_seven_tags_are_zero_to_six_and_the_hook_discriminator_is_105(self) -> None:
        # lib.rs routes `tag <= 6` here and everything else to the SPL transfer-hook
        # discriminator, whose first byte is 105. A builder that emitted 105 would be read as
        # a hook call; a parser that accepted 105 would silently accept one.
        self.assertEqual(v2.TAGS, (0, 1, 2, 3, 4, 5, 6))
        for tag in v2.TAGS:
            with self.subTest(tag=tag):
                self.assertIn(v2._READERS[tag].TAG, v2.TAGS)
        self.assertNotIn(105, v2.TAGS)
        with self.assertRaises(ValueError):
            v2.parse_instruction(bytes([105]) + _bytes_at(1, 8))
        with self.assertRaises(ValueError):
            v2.parse_instruction(bytes([7]) + _bytes_at(1, 8))

    def test_publish_band_is_sixty_two_bytes_and_round_trips(self) -> None:
        data = v2.publish_band(
            low=10,
            high=20,
            as_of_slot=30,
            sample_n=40,
            refused=1,
            model_hash=_key(0xAA),
        )
        expected = (
            b"\x04"
            + _bytes_at(10, 8)
            + _bytes_at(20, 8)
            + _bytes_at(30, 8)
            + _bytes_at(40, 4)
            + b"\x01"
            + _key(0xAA)
        )
        self.assertEqual(data, expected)
        self.assertEqual(len(data), 62)
        self.assertEqual(len(data) - 1, v2.PUBLISH_BAND_PAYLOAD_LEN)
        self.assertEqual(len(data), v2.PUBLISH_BAND_DATA_LEN)
        parsed = v2.parse_instruction(data)
        self.assertIsInstance(parsed, v2.PublishBand)
        self.assertEqual(
            (parsed.low, parsed.high, parsed.as_of_slot, parsed.sample_n, parsed.refused),
            (10, 20, 30, 40, 1),
        )
        self.assertEqual(parsed.model_hash, _key(0xAA))
        self.assertEqual(parsed.data, data)

    def test_log_forecast_is_ninety_three_bytes_and_round_trips(self) -> None:
        data = v2.log_forecast(
            low=10,
            high=20,
            as_of_unix=-7,
            sample_n=40,
            model_hash=_key(0xBB),
            scoring_rule_hash=_key(0xCC),
        )
        expected = (
            b"\x05"
            + _bytes_at(10, 8)
            + _bytes_at(20, 8)
            + _bytes_at(-7, 8, signed=True)
            + _bytes_at(40, 4)
            + _key(0xBB)
            + _key(0xCC)
        )
        self.assertEqual(data, expected)
        self.assertEqual(len(data), 93)
        self.assertEqual(len(data) - 1, v2.LOG_FORECAST_PAYLOAD_LEN)
        self.assertEqual(len(data), v2.LOG_FORECAST_DATA_LEN)
        parsed = v2.parse_instruction(data)
        self.assertIsInstance(parsed, v2.LogForecast)
        self.assertEqual((parsed.low, parsed.high, parsed.as_of_unix), (10, 20, -7))
        self.assertEqual(parsed.sample_n, 40)
        self.assertEqual(parsed.model_hash, _key(0xBB))
        self.assertEqual(parsed.scoring_rule_hash, _key(0xCC))
        self.assertEqual(parsed.data, data)

    def test_score_forecast_is_seventeen_bytes_and_round_trips(self) -> None:
        data = v2.score_forecast(realised_lamports=1_000_000_000, interval_score_micro=2_000_000)
        expected = b"\x06" + _bytes_at(1_000_000_000, 8) + _bytes_at(2_000_000, 8)
        self.assertEqual(data, expected)
        self.assertEqual(len(data), 17)
        self.assertEqual(len(data) - 1, v2.SCORE_FORECAST_PAYLOAD_LEN)
        self.assertEqual(len(data), v2.SCORE_FORECAST_DATA_LEN)
        parsed = v2.parse_instruction(data)
        self.assertIsInstance(parsed, v2.ScoreForecast)
        self.assertEqual(parsed.realised_lamports, 1_000_000_000)
        self.assertEqual(parsed.interval_score_micro, 2_000_000)
        self.assertEqual(parsed.data, data)

    def test_the_new_builders_refuse_a_value_that_does_not_fit(self) -> None:
        with self.assertRaises(ValueError):
            v2.publish_band(low=1, high=2, as_of_slot=3, sample_n=2**32, refused=0, model_hash=_key(1))
        with self.assertRaises(ValueError):
            v2.publish_band(low=1, high=2, as_of_slot=3, sample_n=4, refused=256, model_hash=_key(1))
        with self.assertRaises(ValueError):
            v2.log_forecast(
                low=1, high=2, as_of_unix=2**63, sample_n=4, model_hash=_key(1), scoring_rule_hash=_key(2)
            )
        with self.assertRaises(ValueError):
            v2.log_forecast(
                low=1, high=2, as_of_unix=0, sample_n=4, model_hash=b"short", scoring_rule_hash=_key(2)
            )
        with self.assertRaises(ValueError):
            v2.score_forecast(realised_lamports=2**64, interval_score_micro=0)

    def test_the_account_argument_lists_are_the_programs_order(self) -> None:
        # Tags 0..3, which the review found had no account list at all in this module: the
        # caller had to read lib.rs. The order is the program's `next_account_info` order.
        self.assertEqual(
            v2.INITIALIZE_EXTRA_ACCOUNT_META_LIST_ACCOUNTS,
            (("payer", True, True), ("mint", False, False), ("extra_metas", False, True),
             ("system_program", False, False)),
        )
        self.assertEqual(
            v2.INITIALIZE_RECORD_ACCOUNTS,
            (("payer", True, True), ("mint", False, False), ("record", False, True),
             ("mint_authority", True, False), ("system_program", False, False)),
        )
        self.assertEqual(
            v2.SET_PENDING_PRICE_ACCOUNTS,
            (("authority", True, True), ("record", False, True), ("mint", False, False)),
        )
        self.assertEqual(v2.SET_STATUS_ACCOUNTS, v2.SET_PENDING_PRICE_ACCOUNTS)
        self.assertEqual(
            v2.set_status_accounts(authority="A", record="R", mint="M"),
            (("A", True, True), ("R", False, True), ("M", False, False)),
        )
        self.assertEqual(
            v2.initialize_record_accounts(payer="P", mint="M", record="R", mint_authority="I"),
            (("P", True, True), ("M", False, False), ("R", False, True),
             ("I", True, False), (v2.SYSTEM_PROGRAM, False, False)),
        )
        self.assertEqual(
            v2.PUBLISH_BAND_ACCOUNTS,
            (("authority", True, True), ("record", False, False), ("band", False, True),
             ("mint", False, False), ("system_program", False, False)),
        )
        self.assertEqual(
            v2.LOG_FORECAST_ACCOUNTS,
            (("authority", True, True), ("record", False, False), ("forecast", False, True),
             ("mint", False, False), ("system_program", False, False)),
        )
        self.assertEqual(
            v2.SCORE_FORECAST_ACCOUNTS,
            (("scorer", True, True), ("forecast", False, False), ("score", False, True),
             ("system_program", False, False)),
        )
        self.assertEqual(
            v2.publish_band_accounts(authority="A", record="R", band="B", mint="M"),
            (("A", True, True), ("R", False, False), ("B", False, True),
             ("M", False, False), (v2.SYSTEM_PROGRAM, False, False)),
        )
        self.assertEqual(
            v2.log_forecast_accounts(authority="A", record="R", forecast="F", mint="M"),
            (("A", True, True), ("R", False, False), ("F", False, True),
             ("M", False, False), (v2.SYSTEM_PROGRAM, False, False)),
        )
        self.assertEqual(
            v2.score_forecast_accounts(scorer="S", forecast="F", score="Z"),
            (("S", True, True), ("F", False, False), ("Z", False, True),
             (v2.SYSTEM_PROGRAM, False, False)),
        )

    def test_every_instruction_refuses_every_truncation(self) -> None:
        full = {
            "tag 0": v2.initialize_extra_account_meta_list(),
            "tag 1": v2.initialize_record(
                face_value_lamports=1_000_000_000,
                cap_bps=2500,
                band_low_lamports=0,
                jurisdiction="CA",
                policy=0,
            ),
            "tag 2": v2.set_pending_price(price_lamports=1),
            "tag 3": v2.set_status(status=1),
            "tag 4": v2.publish_band(
                low=1, high=2, as_of_slot=3, sample_n=4, refused=0, model_hash=_key(1)
            ),
            "tag 5": v2.log_forecast(
                low=1, high=2, as_of_unix=0, sample_n=4,
                model_hash=_key(1), scoring_rule_hash=_key(2),
            ),
            "tag 6": v2.score_forecast(realised_lamports=1, interval_score_micro=2),
        }
        for name, data in full.items():
            for length in range(len(data)):
                with self.subTest(instruction=name, length=length):
                    with self.assertRaises(v2.ShortBuffer):
                        v2.parse_instruction(data[:length])
        with self.assertRaises(v2.ShortBuffer):
            v2.parse_instruction(b"")

    def test_the_jurisdiction_is_two_uppercase_letters(self) -> None:
        # The builder is the strict side: the chain stores what it is given and would never
        # complain about `ca`, so the client refuses it instead.
        for good in ("CA", "ZZ", b"US"):
            with self.subTest(jurisdiction=good):
                data = v2.initialize_record(
                    face_value_lamports=1, cap_bps=0, band_low_lamports=0, jurisdiction=good, policy=0
                )
                self.assertIn(bytes(data[19:21]), (b"CA", b"ZZ", b"US"))
        for bad in ("ca", "Zz", "ZZZ", "C", "", b"\x00\x01"):
            with self.subTest(jurisdiction=bad):
                with self.assertRaises(ValueError):
                    v2.initialize_record(
                        face_value_lamports=1, cap_bps=0, band_low_lamports=0, jurisdiction=bad, policy=0
                    )

    def test_the_builder_does_not_validate_the_policy(self) -> None:
        # Proof (e) of the local run sends policy 2 and expects 6023 from the program. If this
        # builder refused it, the refusal could not be observed on chain at all.
        data = v2.initialize_record(
            face_value_lamports=1_000_000_000, cap_bps=2500, band_low_lamports=0, jurisdiction="ZZ", policy=2
        )
        self.assertEqual(data[21], 2)
        self.assertEqual(v2.parse_instruction(data).policy, 2)

    def test_an_integer_that_does_not_fit_its_width_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            v2.set_pending_price(price_lamports=2**64)
        with self.assertRaises(ValueError):
            v2.set_status(status=256)
        with self.assertRaises(ValueError):
            v2.initialize_record(
                face_value_lamports=2**64, cap_bps=0, band_low_lamports=0, jurisdiction="ZZ", policy=0
            )
        with self.assertRaises(ValueError):
            v2.initialize_record(
                face_value_lamports=1, cap_bps=65536, band_low_lamports=0, jurisdiction="ZZ", policy=0
            )


class TestTicketRecord(unittest.TestCase):
    def _buffer(self) -> bytes:
        """A record with a different, recognisable value in every field."""
        return b"".join(
            (
                _bytes_at(0x0102_0304_0506_0708, 8),  # face_value_lamports
                _bytes_at(0x090A, 2),                # cap_bps
                _bytes_at(0x1112_1314_1516_1718, 8),  # pending_price_lamports
                _bytes_at(0x19, 1),                  # status
                _bytes_at(0x2122_2324_2526_2728, 8),  # band_low_lamports
                b"CA",                               # jurisdiction
                _bytes_at(0x2B, 1),                  # policy
                _bytes_at(0x3132_3334_3536_3738, 8, signed=True),  # held_since_unix
                _key(0x41),                          # authority
            )
        )

    def test_the_layout_is_the_documented_one_and_is_seventy_bytes(self) -> None:
        data = self._buffer()
        self.assertEqual(len(data), 70)
        self.assertEqual(v2.TICKET_RECORD_LAYOUT, (
            ("face_value_lamports", 0, 8, "u64"),
            ("cap_bps", 8, 2, "u16"),
            ("pending_price_lamports", 10, 8, "u64"),
            ("status", 18, 1, "u8"),
            ("band_low_lamports", 19, 8, "u64"),
            ("jurisdiction", 27, 2, "raw"),
            ("policy", 29, 1, "u8"),
            ("held_since_unix", 30, 8, "i64"),
            ("authority", 38, 32, "pubkey"),
        ))
        record = v2.decode_ticket_record(data)
        self.assertEqual(record.face_value_lamports, 0x0102_0304_0506_0708)
        self.assertEqual(record.cap_bps, 0x090A)
        self.assertEqual(record.pending_price_lamports, 0x1112_1314_1516_1718)
        self.assertEqual(record.status, 0x19)
        self.assertEqual(record.band_low_lamports, 0x2122_2324_2526_2728)
        self.assertEqual(record.jurisdiction, b"CA")
        self.assertEqual(record.jurisdiction_text, "CA")
        self.assertEqual(record.policy, 0x2B)
        self.assertEqual(record.held_since_unix, 0x3132_3334_3536_3738)
        self.assertEqual(record.authority, _key(0x41))
        self.assertEqual(v2.TicketRecord.LEN, 70)

    def test_the_offset_table_is_expressed_by_the_decoder(self) -> None:
        # One byte at a time: flip byte n and exactly the field that owns n changes. This is
        # the test that a field moved by one byte cannot survive.
        base = bytearray(self._buffer())
        for position in range(len(base)):
            with self.subTest(position=position):
                mutated = bytearray(base)
                mutated[position] ^= 0xFF
                self.assertNotEqual(v2.decode_ticket_record(bytes(mutated)),
                                    v2.decode_ticket_record(bytes(base)))

    def test_a_negative_held_since_is_read_as_signed(self) -> None:
        data = bytearray(self._buffer())
        data[30:38] = _bytes_at(-1, 8, signed=True)
        self.assertEqual(v2.decode_ticket_record(bytes(data)).held_since_unix, -1)

    def test_the_decoded_view_is_json_ready_and_names_the_jurisdiction(self) -> None:
        view = v2.decode_ticket_record(self._buffer()).as_dict()
        self.assertEqual(view["jurisdiction"], "CA")
        self.assertEqual(view["authority"], base58.encode(_key(0x41)))
        self.assertEqual(view["held_since_unix"], 0x3132_3334_3536_3738)
        json.dumps(view)  # must not raise: the artefact carries this view

    def test_a_short_buffer_raises_at_every_length(self) -> None:
        data = self._buffer()
        for length in range(len(data)):
            with self.subTest(length=length):
                with self.assertRaises(v2.ShortBuffer):
                    v2.decode_ticket_record(data[:length])

    def test_trailing_bytes_are_ignored_not_read(self) -> None:
        # A Token-2022 account carries extension data after its base length; a record has no
        # extensions today, but a decoder that refused any surplus would be refusing the
        # account it is handed the day one is added.
        data = self._buffer()
        self.assertEqual(v2.decode_ticket_record(data + b"\xff" * 16), v2.decode_ticket_record(data))


class TestBandForecastScore(unittest.TestCase):
    def test_band_is_one_hundred_and_two_bytes_at_the_documented_offsets(self) -> None:
        data = b"".join((
            _bytes_at(1, 1),                     # version
            _bytes_at(11, 8),                    # low
            _bytes_at(22, 8),                    # high
            _bytes_at(33, 8),                    # as_of_slot
            _bytes_at(44, 8),                    # published_slot
            _bytes_at(55, 4),                    # sample_n
            _bytes_at(1, 1),                     # refused
            _key(0x22),                          # model_hash
            _key(0x33),                          # authority
        ))
        self.assertEqual(len(data), 102)
        band = v2.decode_band(data)
        self.assertEqual(band.version, 1)
        self.assertEqual(band.low, 11)
        self.assertEqual(band.high, 22)
        self.assertEqual(band.as_of_slot, 33)
        self.assertEqual(band.published_slot, 44)
        self.assertEqual(band.sample_n, 55)
        self.assertEqual(band.refused, 1)
        self.assertEqual(band.model_hash, _key(0x22))
        self.assertEqual(band.authority, _key(0x33))
        self.assertEqual(v2.Band.LEN, 102)

    def test_forecast_is_one_hundred_and_sixty_five_bytes_at_the_documented_offsets(self) -> None:
        data = b"".join((
            _bytes_at(1, 1),                     # version
            _key(0x44),                          # mint
            _bytes_at(111, 8),                   # low
            _bytes_at(222, 8),                   # high
            _bytes_at(1_760_000_000, 8, True),   # as_of_unix
            _bytes_at(7, 4),                     # sample_n
            _key(0x55),                          # model_hash
            _key(0x66),                          # scoring_rule_hash
            _bytes_at(888, 8),                   # created_slot
            _key(0x88),                          # authority
        ))
        self.assertEqual(len(data), 165)
        forecast = v2.decode_forecast(data)
        self.assertEqual(forecast.version, 1)
        self.assertEqual(forecast.mint, _key(0x44))
        self.assertEqual(forecast.low, 111)
        self.assertEqual(forecast.high, 222)
        self.assertEqual(forecast.as_of_unix, 1_760_000_000)
        self.assertEqual(forecast.sample_n, 7)
        self.assertEqual(forecast.model_hash, _key(0x55))
        self.assertEqual(forecast.scoring_rule_hash, _key(0x66))
        self.assertEqual(forecast.created_slot, 888)
        self.assertEqual(forecast.authority, _key(0x88))
        self.assertEqual(v2.Forecast.LEN, 165)

    def test_score_is_fifty_eight_bytes_at_the_documented_offsets(self) -> None:
        data = b"".join((
            _bytes_at(1, 1),                     # version
            _bytes_at(1_000_000_000, 8),         # realised_lamports
            _bytes_at(2_000_000, 8),             # interval_score_micro
            _bytes_at(1, 1),                     # covered
            _bytes_at(999, 8),                   # scored_slot
            _key(0x99),                          # scorer
        ))
        self.assertEqual(len(data), 58)
        score = v2.decode_score(data)
        self.assertEqual(score.version, 1)
        self.assertEqual(score.realised_lamports, 1_000_000_000)
        self.assertEqual(score.interval_score_micro, 2_000_000)
        self.assertEqual(score.covered, 1)
        self.assertEqual(score.scored_slot, 999)
        self.assertEqual(score.scorer, _key(0x99))
        self.assertEqual(v2.Score.LEN, 58)

    def test_every_decoder_refuses_every_short_buffer(self) -> None:
        decoders = (
            (v2.decode_band, v2.Band.LEN),
            (v2.decode_forecast, v2.Forecast.LEN),
            (v2.decode_score, v2.Score.LEN),
        )
        for decoder, length in decoders:
            for provided in range(length):
                with self.subTest(decoder=decoder.__name__, provided=provided):
                    with self.assertRaises(v2.ShortBuffer):
                        decoder(b"\x00" * provided)

    def test_a_short_buffer_is_a_value_error_and_not_a_silent_zero(self) -> None:
        # A caller that catches ValueError already catches this; a caller that catches
        # nothing sees the reason. What must never happen is a decoded zero.
        self.assertTrue(issubclass(v2.ShortBuffer, ValueError))
        with self.assertRaisesRegex(v2.ShortBuffer, "102 bytes are needed and 101 arrived"):
            v2.decode_band(b"\x00" * 101)


class TestProgramAddresses(unittest.TestCase):
    def test_the_seed_shapes_are_the_rust_ones(self) -> None:
        mint = _key(0x5A)
        forecast = _key(0x5B)
        self.assertEqual(v2.seeds_record(mint), (b"record", mint))
        self.assertEqual(
            v2.seeds_extra_account_meta_list(mint), (b"extra-account-metas", mint)
        )
        self.assertEqual(v2.seeds_band(mint), (b"band", mint))
        self.assertEqual(
            v2.seeds_forecast(mint, 1_760_000_000),
            (b"forecast", mint, _bytes_at(1_760_000_000, 8, True)),
        )
        self.assertEqual(v2.seeds_score(forecast), (b"score", forecast))
        self.assertEqual(v2.seeds_fee_authority(mint), (b"fee-authority", mint))
        self.assertEqual(v2.seeds_rebate_pool(mint), (b"rebate-pool", mint))

    def test_the_measured_addresses_reproduce(self) -> None:
        # Measured with `solana find-program-derived-address` (4.3.2) against the devnet
        # program id and mint above. A different algorithm cannot reproduce seven for seven.
        forecast = MEASURED["forecast"][0]
        derived = {
            "record": v2.record_address(DEVNET_PROGRAM, DEVNET_MINT),
            "extra-account-metas": v2.extra_account_meta_list_address(DEVNET_PROGRAM, DEVNET_MINT),
            "band": v2.band_address(DEVNET_PROGRAM, DEVNET_MINT),
            "forecast": v2.forecast_address(DEVNET_PROGRAM, DEVNET_MINT, 1_760_000_000),
            "score": v2.score_address(DEVNET_PROGRAM, forecast),
            "fee-authority": v2.fee_authority_address(DEVNET_PROGRAM, DEVNET_MINT),
            "rebate-pool": v2.rebate_pool_address(DEVNET_PROGRAM, DEVNET_MINT),
        }
        for name, measured in MEASURED.items():
            with self.subTest(name=name):
                self.assertEqual(derived[name], measured)

    def test_a_forecast_address_changes_with_the_instant_and_signs_the_seed(self) -> None:
        first = v2.forecast_address(DEVNET_PROGRAM, DEVNET_MINT, 1_760_000_000)
        second = v2.forecast_address(DEVNET_PROGRAM, DEVNET_MINT, 1_760_000_001)
        self.assertNotEqual(first[0], second[0])
        # A pre-1970 instant is a legal i64 seed; it must encode as eight bytes and not raise.
        negative = v2.seeds_forecast(DEVNET_MINT, -1)
        self.assertEqual(negative[2], b"\xff" * 8)
        self.assertEqual(len(v2.forecast_address(DEVNET_PROGRAM, DEVNET_MINT, -1)[0]), 44)

    def test_the_address_off_the_curve_is_the_one_that_is_returned(self) -> None:
        # The rule the runtime applies: the digest is not a valid ed25519 point. If the curve
        # test were inverted or absent, this property would not hold for the addresses above.
        for name, (address, _bump) in MEASURED.items():
            with self.subTest(name=name):
                raw = base58.decode(address)
                self.assertEqual(len(raw), 32)
                self.assertFalse(v2.is_on_curve(raw), f"{name} is on the curve and cannot be a PDA")

    def test_the_curve_test_accepts_a_point_it_must_accept(self) -> None:
        # The ed25519 base point, compressed: y = 4/5, sign bit 0. If `is_on_curve` returned
        # False for everything, the test above would pass while the derivation was wrong.
        base_point = bytes.fromhex(
            "5866666666666666666666666666666666666666666666666666666666666666"
        )
        self.assertTrue(v2.is_on_curve(base_point))
        # y = 0 is a point as well: x^2 = -1 has a square root in this field.
        self.assertTrue(v2.is_on_curve(bytes(32)))

    def test_seed_limits_are_the_runtimes(self) -> None:
        with self.assertRaises(v2.NotAProgramAddress):
            v2.find_program_address(DEVNET_PROGRAM, [b"x" * 33])
        with self.assertRaises(v2.NotAProgramAddress):
            v2.find_program_address(DEVNET_PROGRAM, [b"x"] * 17)
        with self.assertRaises(TypeError):
            v2.find_program_address(DEVNET_PROGRAM, ["not bytes"])
        with self.assertRaises(ValueError):
            v2.find_program_address("not-a-key", [b"x"])

    def test_a_mint_must_be_thirty_two_bytes(self) -> None:
        with self.assertRaises(ValueError):
            v2.seeds_record("too-short")
        with self.assertRaises(TypeError):
            v2.seeds_record(12345)


class TestMintAuthority(unittest.TestCase):
    """The one field tag 1 reads out of the mint, at the offset Token-2022 keeps it."""

    def _mint(self, authority: bytes | None) -> bytes:
        tag = (0 if authority is None else 1).to_bytes(4, "little")
        key = bytes(32) if authority is None else authority
        # supply, decimals, is_initialized, freeze authority (none).
        return tag + key + bytes(8) + bytes(1) + bytes(1) + bytes(4) + bytes(32)

    def test_a_present_authority_is_read_at_offset_four(self) -> None:
        key = bytes([0x09]) * 32
        self.assertEqual(v2.mint_authority(self._mint(key)), key)
        self.assertEqual(len(self._mint(key)), v2.MINT_BASE_LEN)

    def test_a_mint_with_no_authority_reads_as_none(self) -> None:
        # A fixed-supply mint: `initialize_record` refuses it 6026, because nobody can authorise
        # a policy for it. Fail-closed, and the client can see it before trying.
        self.assertIsNone(v2.mint_authority(self._mint(None)))

    def test_a_short_buffer_and_a_bad_tag_are_refused(self) -> None:
        with self.assertRaises(v2.ShortBuffer):
            v2.mint_authority(self._mint(bytes(32))[:81])
        bad = (2).to_bytes(4, "little") + bytes(78)
        with self.assertRaises(ValueError):
            v2.mint_authority(bad)


class TestTheRustSourcesAgree(unittest.TestCase):
    """Read the Rust and compare. The program is the source of truth for these numbers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.lib = (RUST_SRC / "lib.rs").read_text(encoding="utf-8")
        cls.state = (RUST_SRC / "state.rs").read_text(encoding="utf-8")

    def test_tag_one_unpacks_the_slices_this_module_packs(self) -> None:
        block = self.lib[self.lib.index("1 => {") : self.lib.index("2 => {")]
        slices = []
        # One `rest.get(18..20)` in lib.rs is split across a line break, so the pattern allows
        # whitespace around the dot.
        for slice_text in re.findall(r"rest\s*\.\s*get\(([^)]*)\)", block):
            start, _, end = slice_text.partition("..")
            start_at = int(start) if start else 0
            end_at = int(end) if end else start_at + 1
            slices.append((start_at, end_at, end_at - start_at))
        self.assertEqual(len(slices), 5, "tag 1 must read five fields")
        expected = [(offset, offset + width, width) for _n, offset, width, _k in v2.INITIALIZE_RECORD_LAYOUT]
        self.assertEqual(slices, expected)
        self.assertEqual(sum(width for _s, _e, width in slices), v2.INITIALIZE_RECORD_PAYLOAD_LEN)

    def test_the_documented_argument_widths_are_these_widths(self) -> None:
        # The doc comment on `InitializeRecord` states the wire order and each field's width,
        # so a reader and a decoder start from the same paragraph.
        start = self.lib.index("Wire bytes after the tag")
        paragraph = self.lib[start : self.lib.index("InitializeRecord {", start)]
        documented = re.findall(r"`(\w+)`[^,`]*?\((\d+)\)", paragraph)
        self.assertEqual(
            documented,
            [("face", "8"), ("cap_bps", "2"), ("band_low", "8"), ("jurisdiction", "2"), ("policy", "1")],
        )
        self.assertEqual(sum(int(width) for _name, width in documented), 21)
        # And the names line up with the field names this module uses, modulo the `_lamports`
        # suffix the record carries and the instruction does not.
        names = [name.replace("value_", "").removesuffix("_lamports") for name, *_ in v2.INITIALIZE_RECORD_LAYOUT]
        self.assertEqual([name for name, _w in documented], names)

    def _struct_fields(self, name: str) -> list[tuple[str, str]]:
        start = self.state.index(f"pub struct {name} {{")
        body = self.state[start : self.state.index("\n}", start)]
        return re.findall(r"^\s*pub (\w+): ([^,]+),$", body, re.MULTILINE)

    def _const_len(self, name: str) -> int:
        start = self.state.index(f"impl {name} {{")
        body = self.state[start : self.state.index("\n}", start)]
        match = re.search(r"pub const LEN: usize = (\d+);", body)
        assert match, f"no LEN in impl {name}"
        return int(match.group(1))

    def _comment_sum(self, name: str) -> int:
        start = self.state.index(f"impl {name} {{")
        body = self.state[start : self.state.index("\n}", start)]
        match = re.search(r"///\s*((?:\d+\s*\+\s*)+\d+)\.", body)
        assert match, f"no width comment in impl {name}"
        return sum(int(part) for part in re.findall(r"\d+", match.group(1)))

    def test_every_struct_matches_its_layout_here(self) -> None:
        widths = {"u64": 8, "u16": 2, "u32": 4, "u8": 1, "i64": 8, "Pubkey": 32, "[u8; 2]": 2, "[u8; 32]": 32}
        for name, cls in (
            ("TicketRecord", v2.TicketRecord),
            ("Band", v2.Band),
            ("Forecast", v2.Forecast),
            ("Score", v2.Score),
        ):
            with self.subTest(struct=name):
                fields = self._struct_fields(name)
                self.assertTrue(fields, f"no fields parsed for {name}")
                offsets = []
                cursor = 0
                for field, rust_type in fields:
                    width = widths[rust_type]
                    offsets.append((field, cursor, width))
                    cursor += width
                self.assertEqual(
                    offsets,
                    [(field, offset, width) for field, offset, width, _kind in cls.LAYOUT],
                    f"{name}: state.rs and ticketpath/onchain/v2.py disagree",
                )
                self.assertEqual(cursor, cls.LEN)
                self.assertEqual(self._const_len(name), cls.LEN, f"{name}::LEN")
                self.assertEqual(self._comment_sum(name), cls.LEN, f"{name}'s width comment")
                self.assertEqual(len(fields), len(cls.LAYOUT))

    def test_the_tag_routing_in_lib_rs_is_the_routing_here(self) -> None:
        # `if tag <= 6` is what makes 0..=6 this program's and 105 the hook's.
        self.assertIn("if tag <= 6 {", self.lib)
        self.assertEqual(max(v2.TAGS), 6)
        self.assertIn("TransferHookInstruction::unpack", self.lib)

    def _documented_payload(self, anchor: str) -> list[tuple[str, int, int]]:
        """The `(name, offset, width)` triples from the doc comment above an instruction."""
        at = self.lib.index(anchor)
        start = self.lib.rindex("Wire bytes after the tag", 0, at)
        end = self.lib.index("That is", at)
        paragraph = self.lib[start:end]
        return [
            (name, int(offset), int(width))
            for name, offset, width in re.findall(r"`(\w+)`\s+[^()]+?\((\d+),\s*(\d+)\)", paragraph)
        ]

    def _arm(self, tag: int) -> str:
        start = re.search(rf"\n\s*{tag} => \{{", self.lib)
        assert start, f"no match arm for tag {tag}"
        following = (
            re.search(rf"\n\s*{tag + 1} => \{{", self.lib[start.end():])
            if tag < 6
            else re.search(r"\n\s*_ => Err", self.lib[start.end():])
        )
        assert following, f"no end for tag {tag}'s arm"
        return self.lib[start.end() : start.end() + following.start()]

    def test_the_new_payload_offsets_are_the_documented_ones(self) -> None:
        for anchor, layout in (
            ("`as_of_slot` u64 (16, 8)", v2.PUBLISH_BAND_LAYOUT),
            ("`as_of_unix` i64 (16, 8)", v2.LOG_FORECAST_LAYOUT),
            ("`realised_lamports`", v2.SCORE_FORECAST_LAYOUT),
        ):
            with self.subTest(anchor=anchor):
                self.assertEqual(
                    self._documented_payload(anchor),
                    [(name, offset, width) for name, offset, width, _kind in layout],
                )
                self.assertEqual(sum(width for _name, _offset, width, _kind in layout),
                                 v2._span(layout))

        for layout, payload_len in (
            (v2.PUBLISH_BAND_LAYOUT, v2.PUBLISH_BAND_PAYLOAD_LEN),
            (v2.LOG_FORECAST_LAYOUT, v2.LOG_FORECAST_PAYLOAD_LEN),
            (v2.SCORE_FORECAST_LAYOUT, v2.SCORE_FORECAST_PAYLOAD_LEN),
        ):
            self.assertEqual(v2._span(layout), payload_len)

    def test_the_new_unpack_slices_are_the_layout_offsets(self) -> None:
        for tag, layout in (
            (4, v2.PUBLISH_BAND_LAYOUT),
            (5, v2.LOG_FORECAST_LAYOUT),
            (6, v2.SCORE_FORECAST_LAYOUT),
        ):
            with self.subTest(tag=tag):
                slices = []
                for slice_text in re.findall(r"rest\s*\.\s*get\(([^)]*)\)", self._arm(tag)):
                    start, _, end = slice_text.partition("..")
                    start_at = int(start) if start else 0
                    end_at = int(end) if end else start_at + 1
                    slices.append((start_at, end_at))
                expected = [(offset, offset + width) for _n, offset, width, _k in layout]
                self.assertEqual(slices, expected)

    def _fn_body(self, name: str) -> str:
        start = self.lib.index(f"fn {name}(")
        following = self.lib.find("\nfn ", start + 1)
        assert following != -1, f"no function after {name}"
        return self.lib[start:following]

    def test_tags_two_and_three_read_a_signer_a_record_and_a_mint(self) -> None:
        # The account list this module builds is the list the program reads, and the program
        # passes the record through `checked_record_for_write`, which is where the signer, the
        # address and the authority check live. A builder that grew an account without the Rust
        # growing one is the drift this test exists for.
        for name, accounts in (
            ("set_pending_price", v2.SET_PENDING_PRICE_ACCOUNTS),
            ("set_status", v2.SET_STATUS_ACCOUNTS),
        ):
            with self.subTest(instruction=name):
                body = self._fn_body(name)
                self.assertEqual(body.count("next_account_info"), len(accounts), name)
                self.assertIn("checked_record_for_write", body, name)
        guard = self._fn_body("checked_record_for_write")
        for needle in ("is_signer", "data_len() != TicketRecord::LEN", "authorises("):
            self.assertIn(needle, guard, "the authenticated write must check all three")

    def test_tag_zero_derives_the_record_instead_of_taking_it(self) -> None:
        body = self._fn_body("initialize_extra_account_meta_list")
        self.assertIn("record_seeds(mint.key)", body)
        self.assertNotIn("record: Pubkey", self.lib)
        # And it takes no instruction argument at all, which is what the builder sends.
        self.assertIn("InitializeExtraAccountMetaList,", self.lib)

    def test_record_creation_reads_the_mints_authority(self) -> None:
        body = self._fn_body("initialize_record")
        self.assertIn("mint_authority_of(mint)", body)
        self.assertIn("mint_authority.is_signer", body)
        parse = self._fn_body("mint_authority_of")
        # Offset 0 is the COption tag, 4..36 the key: the base Mint layout.
        self.assertIn("get(..4)", parse)
        self.assertIn("get(4..36)", parse)

    def test_the_record_slot_order_is_what_the_hook_writes(self) -> None:
        # `record.held_since_unix = Clock::get()?.unix_timestamp;` inside the writable branch
        # is the one write the unit tests cannot reach, and the field it writes has to exist
        # here at the offset this module decodes.
        self.assertIn("record.held_since_unix = Clock::get()?.unix_timestamp;", self.lib)
        self.assertIn("if record_ai.is_writable {", self.lib)
        self.assertEqual(
            dict((name, offset) for name, offset, _width, _kind in v2.TICKET_RECORD_LAYOUT)["held_since_unix"],
            30,
        )


if __name__ == "__main__":
    unittest.main()

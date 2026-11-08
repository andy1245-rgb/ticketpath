"""The flip tax at checkout: the schedule, its boundaries, the arithmetic, and the leg.

Every claim `market_swarm/flip_tax.py` makes about itself is checked here. The default schedule
is 15% of the sale price under an hour, falling linearly to 0% at thirty days, floored in
integers, and the three boundaries the brief names (59 minutes, one hour, thirty days) are
asserted as exact integers rather than as an inequality. An unknown hold -- a record whose clock
was never written -- pays the **full** rate and keeps `held_seconds is None` so the row says
why; a future hold clamps to 0 seconds for the same reason. The tax is
`lamports = price * bps // 10_000`, never more than the price for any rate the schedule may
carry, and the rounding is floor: 19 lamports at 1500 bps is 2, not 3. Every refusal
`sale_instructions` documents is asserted with its own reason, and the leg order is
`(stage, artist_fee?, flip_tax?, move)` with no leg at all when the tax is zero.

**The record layout is pinned against the client, not copied from it.** The module transcribes
the v2 `["record", mint]` layout instead of importing `ticketpath`, so this file reads
`ticketpath/onchain/v2.py` and compares `RECORD_LEN`, `HELD_SINCE_UNIX_OFFSET` and
`HELD_SINCE_UNIX_WIDTH` with `TicketRecord.LEN` and the `held_since_unix` entry of
`TICKET_RECORD_LAYOUT`, and asserts the literals on both sides. A field that moves on either side
is a failing test instead of two implementations that drift quietly. The test builds its record
buffers with literal byte 30 for the same reason: a buffer built from the module's own constant
would agree with a moved constant.

The wallet check is pinned against `market_swarm/artist_fee.py`: the same three bad addresses are
refused by both modules, each raising its own error type, so the two checks cannot drift.

What this file deliberately does not do:

- It runs no validator and reaches no cluster. The age of a hold is an **input** here, not a
  measurement; the boundary legs that prove four instructions, two signers and the lamport delta
  on chain are `tools/flip_tax_proof.py` and its own test, and nothing here replaces them.
- It does not test the wiring that decides when the tax is charged or what `now_unix` is. That is
  `market_swarm/tests/test_flip_tax_wiring.py` and the call-site tests; here `now_unix` is always
  passed in, which is the seam the checkout exists to make testable.
- It does not test the hook. Whether the program writes the field it says it writes is a
  validator measurement; the layout pin only proves this side reads the byte the Rust declares.
- It asserts no number it has not computed. Every expected lamport is a literal with the
  arithmetic that produced it beside it.
"""

from __future__ import annotations

import ast
import unittest
from dataclasses import FrozenInstanceError
from pathlib import Path

from market_swarm import artist_fee as af
from market_swarm import flip_tax as ft
from ticketpath.onchain import v2

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "market_swarm" / "flip_tax.py"

#: Three real 32-byte base58 addresses. The seller and the artist are deterministic byte runs;
#: the third is the tax recipient, kept distinct from the fee's so a test can say which wallet
#: a leg names rather than matching either one.
SELLER = af.dp.base58.encode(bytes(range(1, 33)))
ARTIST = af.dp.base58.encode(bytes(range(33, 65)))
TAX_ARTIST = af.dp.base58.encode(bytes(range(65, 97)))
#: 31 and 33 bytes: both base58-valid, one either side of a public key, which is the typo the
#: length check exists for.
SHORT_WALLET = af.dp.base58.encode(bytes(range(1, 32)))
LONG_WALLET = af.dp.base58.encode(bytes(range(1, 34)))
TOKEN_PROGRAM = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"

PRICE = 1_000_000_000  # 1 SOL, the design's own worked pair
FULL_BPS = 1_500
TAX = PRICE * FULL_BPS // 10_000  # 150_000_000
FEE_BPS = 500
FEE = PRICE * FEE_BPS // 10_000  # 50_000_000
NOW = 1_700_000_000

ONE_HOUR = 3_600
ONE_DAY = 86_400
THIRTY_DAYS = 2_592_000

#: `bps` for a hold under the default schedule, as literals rather than recomputed. The module's
#: own expression is `1500 * (2592000 - held) // 2588400`; a test that recomputed it would agree
#: with any arithmetic error inside it, so each number below is that expression evaluated by hand
#: and the working is beside it.
PINNED_RATES = {
    0: 1_500,  # flat: under the full-hold point
    3_540: 1_500,  # 59 minutes, the brief's first boundary
    3_600: 1_500,  # the full-hold point; the line starts here, so both readings agree
    3_601: 1_499,  # 1500 * 2_588_399 // 2_588_400 = 1499.9994, floored
    1_296_000: 751,  # 15 days: 1500 * 1_296_000 // 2_588_400 = 751.04, floored
    1_297_800: 750,  # the exact midpoint: 1500 * 1_294_200 // 2_588_400 = 750.0
    2_591_999: 0,  # one second before the zero point: 1500 * 1 // 2_588_400 = 0
    2_592_000: 0,  # the zero point itself
    2_592_001: 0,  # past it
}


def _instruction(tag: int) -> af.dp.Instruction:
    """A stand-in for a leg this module does not own. Only identity is asserted of it."""
    return af.dp.Instruction(program_id=af.dp.SYSTEM_PROGRAM, accounts=(), data=bytes([tag]))


def _record(held_since_unix: int) -> bytes:
    """A 70-byte v2 record with the hook's clock at byte 30, little-endian and signed.

    The 30 and the 70 are literals on purpose. A buffer built from `ft.HELD_SINCE_UNIX_OFFSET`
    would agree with a moved constant, and the decode test would then pass against a module that
    read the wrong byte.
    """
    raw = bytearray(70)
    raw[30:38] = held_since_unix.to_bytes(8, "little", signed=True)
    return bytes(raw)


def _policy(**overrides) -> ft.FlipTaxPolicy:
    """A policy that is on, at the default schedule, paying the tax recipient."""
    arguments = {"artist_wallet": TAX_ARTIST, "enabled": True, "schedule": ft.DEFAULT_SCHEDULE}
    arguments.update(overrides)
    return ft.FlipTaxPolicy(**arguments)


def _sale(**overrides) -> tuple:
    """A taxed sale at the design's worked pair, a minute into the hold, with any argument
    replaced. A minute is under the full-hold point, so the rate is the full one."""
    arguments = {
        "stage": _instruction(11),
        "move": _instruction(12),
        "seller": SELLER,
        "policy": _policy(),
        "price_lamports": PRICE,
        "held_since_unix": NOW - 60,
        "now_unix": NOW,
    }
    arguments.update(overrides)
    return ft.sale_instructions(**arguments)


class TestDefaultSchedule(unittest.TestCase):
    def test_the_defaults_are_the_operators_sentence(self) -> None:
        self.assertEqual(ft.DEFAULT_FULL_BPS, 1_500)
        self.assertEqual(ft.DEFAULT_FULL_HOLD_SECONDS, 3_600)
        self.assertEqual(ft.DEFAULT_ZERO_HOLD_SECONDS, 2_592_000)
        self.assertEqual(ft.DEFAULT_SCHEDULE, ft.FlipTaxSchedule(1_500, 3_600, 2_592_000))

    def test_the_pinned_rate_table(self) -> None:
        for held, expected in sorted(PINNED_RATES.items()):
            with self.subTest(held=held):
                got = ft.DEFAULT_SCHEDULE.bps_for(held)
                self.assertEqual(got, expected, f"bps_for({held}) = {got}")
                self.assertIs(type(got), int)

    def test_the_boundaries_the_brief_names_are_exact(self) -> None:
        # 59 minutes, one hour, thirty days. Written as its own test because these three are the
        # numbers a validator run cannot manufacture and a reader will look for first.
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(3_540), 1_500)
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(3_600), 1_500)
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_592_000), 0)

    def test_one_second_either_side_of_the_thirty_day_point(self) -> None:
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_591_999), 0)
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_592_000), 0)
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_592_001), 0)

    def test_the_rounding_band_at_the_end_of_the_schedule(self) -> None:
        # Flooring, not rounding up, means the rate reads 0 before the stated 30 days: the rate
        # is 0 once 1500 * (2_592_000 - held) < 2_588_400, i.e. once the gap is at most 1_725
        # seconds. So 2_592_000 - 1_725 = 2_590_275 is the first 0 and one second earlier is 1.
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_590_274), 1)
        self.assertEqual(ft.DEFAULT_SCHEDULE.bps_for(2_590_275), 0)

    def test_the_rate_never_rises_with_the_hold(self) -> None:
        previous = ft.DEFAULT_SCHEDULE.bps_for(0)
        for held in range(0, THIRTY_DAYS + 1, 997):
            rate = ft.DEFAULT_SCHEDULE.bps_for(held)
            self.assertLessEqual(
                rate, previous, f"bps_for({held}) = {rate} rose above {previous}"
            )
            self.assertGreaterEqual(rate, 0, f"bps_for({held}) = {rate} is negative")
            self.assertLessEqual(rate, FULL_BPS, f"bps_for({held}) = {rate} is above the rate")
            previous = rate

    def test_the_schedule_is_frozen(self) -> None:
        schedule = ft.FlipTaxSchedule(full_bps=1_000)
        with self.assertRaises(FrozenInstanceError):
            schedule.full_bps = 900  # type: ignore[misc]

    def test_a_hold_below_zero_is_refused(self) -> None:
        # The module has no meaning for a negative age; a caller that has one has read a clock
        # wrong, and flooring it to the full rate would hide that.
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.DEFAULT_SCHEDULE.bps_for(-1)
        self.assertIn("held_seconds", str(caught.exception))


class TestScheduleBounds(unittest.TestCase):
    def test_a_rate_above_the_maximum_is_refused_naming_the_field(self) -> None:
        for bad in (10_001, 20_000, 2**40):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxSchedule(full_bps=bad)
                self.assertIn("full_bps", str(caught.exception))
                self.assertIn("10000", str(caught.exception))

    def test_a_negative_rate_is_refused(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxSchedule(full_bps=-1)
        self.assertIn("full_bps", str(caught.exception))

    def test_bools_and_floats_are_refused_in_every_integer_field(self) -> None:
        for bad in (True, False, 500.0, "500", None, [500]):
            with self.subTest(bad=bad):
                for field in ("full_bps", "full_hold_seconds", "zero_hold_seconds"):
                    with self.subTest(field=field):
                        with self.assertRaises(ft.FlipTaxError) as caught:
                            ft.FlipTaxSchedule(**{field: bad})
                        self.assertIn(field, str(caught.exception))

    def test_a_curve_that_ends_before_it_starts_is_refused(self) -> None:
        for full, zero in ((100, 100), (100, 99), (3_600, 0)):
            with self.subTest(full=full, zero=zero):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxSchedule(full_hold_seconds=full, zero_hold_seconds=zero)
                self.assertIn("zero_hold_seconds", str(caught.exception))

    def test_the_endpoints_of_the_curve_are_accepted(self) -> None:
        self.assertEqual(ft.FlipTaxSchedule(full_bps=0).bps_for(1), 0)
        self.assertEqual(ft.FlipTaxSchedule(full_bps=10_000).bps_for(1), 10_000)
        # full_hold_seconds 0 is a rate that starts falling immediately; zero_hold_seconds 1 is
        # the shortest curve the span allows.
        self.assertEqual(
            ft.FlipTaxSchedule(full_bps=10_000, full_hold_seconds=0, zero_hold_seconds=1)
            .bps_for(0),
            10_000,
        )


class TestHoldSeconds(unittest.TestCase):
    def test_unknown_is_none_and_not_a_number(self) -> None:
        # 0 is `InitializeRecord`'s value and must not be read as 1970: `now - 0` would price an
        # unset field at 0%, the cheapest evasion in the system.
        for now in (0, 1, NOW, 2**40):
            with self.subTest(now=now):
                self.assertIsNone(ft.hold_seconds(0, now))
                self.assertNotIsInstance(ft.hold_seconds(0, now), int)

    def test_a_future_hold_clamps_to_zero_seconds(self) -> None:
        for ahead in (1, 3_600, 2_592_000, 2**40):
            with self.subTest(ahead=ahead):
                held = ft.hold_seconds(NOW + ahead, NOW)
                self.assertEqual(held, 0)
                self.assertIsNotNone(held)

    def test_a_normal_hold_is_the_difference(self) -> None:
        self.assertEqual(ft.hold_seconds(NOW - 3_540, NOW), 3_540)
        self.assertEqual(ft.hold_seconds(NOW - 2_592_000, NOW), 2_592_000)
        self.assertEqual(ft.hold_seconds(NOW, NOW), 0)

    def test_negative_inputs_are_refused_naming_the_field(self) -> None:
        for since, now, field in (
            (-1, NOW, "held_since_unix"),
            (NOW, -1, "now_unix"),
            (1.5, NOW, "held_since_unix"),
            (True, NOW, "held_since_unix"),
        ):
            with self.subTest(since=since, now=now):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.hold_seconds(since, now)
                self.assertIn(field, str(caught.exception))


class TestAssess(unittest.TestCase):
    def test_an_unknown_hold_pays_the_full_rate_and_says_why(self) -> None:
        assessment = ft.assess(price_lamports=PRICE, held_since_unix=0, now_unix=NOW)
        self.assertIsNone(assessment.held_seconds)
        self.assertFalse(assessment.known)
        self.assertEqual(assessment.bps, FULL_BPS)
        self.assertEqual(assessment.lamports, TAX)
        self.assertEqual(
            assessment.to_dict(),
            {"held_seconds": None, "bps": FULL_BPS, "lamports": TAX},
        )

    def test_a_thirty_day_hold_pays_nothing(self) -> None:
        assessment = ft.assess(
            price_lamports=PRICE, held_since_unix=NOW - THIRTY_DAYS, now_unix=NOW
        )
        self.assertEqual(assessment.held_seconds, THIRTY_DAYS)
        self.assertTrue(assessment.known)
        self.assertEqual(assessment.bps, 0)
        self.assertEqual(assessment.lamports, 0)

    def test_the_lamports_are_the_floored_fraction_of_the_price(self) -> None:
        cases = {
            (0, 1_500): 0,
            (1, 1_500): 0,
            (19, 1_500): 2,  # 19 * 1500 = 28_500; // 10_000 = 2
            (20, 1_500): 3,  # 20 * 1500 = 30_000; // 10_000 = 3 exactly
            (999, 1_500): 149,  # 1_498_500 // 10_000 = 149
            (PRICE, 1_500): TAX,
            (PRICE, 0): 0,
            (PRICE, 10_000): PRICE,
            (2**64 - 1, 10_000): 2**64 - 1,
        }
        for (price, bps), expected in sorted(cases.items()):
            with self.subTest(price=price, bps=bps):
                assessment = ft.assess(
                    price_lamports=price,
                    held_since_unix=NOW - 60,
                    now_unix=NOW,
                    schedule=ft.FlipTaxSchedule(full_bps=bps),
                )
                self.assertEqual(assessment.bps, bps)
                self.assertEqual(assessment.lamports, expected)
                self.assertEqual(assessment.lamports, price * bps // 10_000)

    def test_the_tax_never_exceeds_the_price_at_any_rate(self) -> None:
        # `MAX_BPS` is what makes this a bound on accepted input rather than an accident of the
        # division; the sweep walks every rate a schedule may carry.
        prices = (0, 1, 19, 20, 999, 1_000_000, PRICE, 2**64 - 1)
        for bps in (*range(0, 10_001, 137), 1, 9_999, 10_000):
            schedule = ft.FlipTaxSchedule(full_bps=bps)
            for price in prices:
                with self.subTest(bps=bps, price=price):
                    lamports = ft.assess(
                        price_lamports=price,
                        held_since_unix=NOW - 60,
                        now_unix=NOW,
                        schedule=schedule,
                    ).lamports
                    self.assertLessEqual(lamports, price)
                    self.assertGreaterEqual(lamports, 0)

    def test_floor_and_not_ceiling_at_the_two_lamport_cases(self) -> None:
        # A ceiling would take the whole ticket at 1 lamport and 3 of 19: the defect that killed
        # the token fee (finding 36 §2), one unit lower down.
        self.assertEqual(
            ft.assess(price_lamports=1, held_since_unix=NOW - 60, now_unix=NOW).lamports, 0
        )
        self.assertEqual(
            ft.assess(price_lamports=19, held_since_unix=NOW - 60, now_unix=NOW).lamports, 2
        )

    def test_a_zero_price_assesses_to_zero(self) -> None:
        # The builder refuses a zero price; the arithmetic still has to be exact at it, because
        # a dataset row can carry one.
        self.assertEqual(
            ft.assess(price_lamports=0, held_since_unix=NOW - 60, now_unix=NOW).lamports, 0
        )

    def test_bad_inputs_are_refused_naming_the_field(self) -> None:
        for kwargs, field in (
            ({"price_lamports": -1}, "price_lamports"),
            ({"price_lamports": 1.5}, "price_lamports"),
            ({"price_lamports": True}, "price_lamports"),
            ({"schedule": {"full_bps": 1_500}}, "schedule"),
            ({"schedule": None}, "schedule"),
        ):
            arguments = {
                "price_lamports": PRICE,
                "held_since_unix": NOW - 60,
                "now_unix": NOW,
            }
            arguments.update(kwargs)
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.assess(**arguments)
                self.assertIn(field, str(caught.exception))

    def test_the_assessment_is_frozen(self) -> None:
        assessment = ft.assess(price_lamports=PRICE, held_since_unix=0, now_unix=NOW)
        with self.assertRaises(FrozenInstanceError):
            assessment.bps = 0  # type: ignore[misc]


class TestScheduleMapping(unittest.TestCase):
    def test_to_dict_round_trips_through_from_mapping(self) -> None:
        schedule = ft.FlipTaxSchedule(full_bps=1_000, full_hold_seconds=1_800,
                                      zero_hold_seconds=1_296_000)
        self.assertEqual(
            schedule.to_dict(),
            {"full_bps": 1_000, "full_hold_seconds": 1_800, "zero_hold_seconds": 1_296_000},
        )
        self.assertEqual(ft.FlipTaxSchedule.from_mapping(schedule.to_dict()), schedule)
        self.assertEqual(ft.FlipTaxSchedule.from_mapping(ft.DEFAULT_SCHEDULE.to_dict()),
                         ft.DEFAULT_SCHEDULE)

    def test_a_partial_mapping_keeps_the_fields_it_does_not_name(self) -> None:
        for raw, expected in (
            ({"full_bps": 1_000}, ft.FlipTaxSchedule(1_000, 3_600, 2_592_000)),
            ({"full_hold_seconds": 1_800}, ft.FlipTaxSchedule(1_500, 1_800, 2_592_000)),
            ({"zero_hold_seconds": 1_296_000}, ft.FlipTaxSchedule(1_500, 3_600, 1_296_000)),
            ({}, ft.DEFAULT_SCHEDULE),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(ft.FlipTaxSchedule.from_mapping(raw), expected)

    def test_an_unknown_field_is_refused_naming_the_path_and_the_key(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxSchedule.from_mapping(
                {"full_bps": 1_000, "rate": 15}, field="events[0].flip_tax.schedule"
            )
        message = str(caught.exception)
        self.assertIn("events[0].flip_tax.schedule", message)
        self.assertIn("rate", message)

    def test_a_non_object_is_refused(self) -> None:
        for bad in ([1_500], "1500", 1_500, None):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxSchedule.from_mapping(bad)
                self.assertIn("flip_tax.schedule", str(caught.exception))

    def test_a_bad_value_is_reported_under_the_path_it_was_given(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxSchedule.from_mapping(
                {"full_bps": 20_000}, field="events[1].flip_tax.schedule"
            )
        message = str(caught.exception)
        self.assertIn("events[1].flip_tax.schedule.full_bps", message)
        self.assertIn("20000", message)


class TestPolicyMapping(unittest.TestCase):
    def test_an_omitted_toggle_is_off(self) -> None:
        # The event maker's toggle, and the default is off: a block that does not say
        # "enabled": true has not turned the tax on.
        policy = ft.FlipTaxPolicy.from_mapping({"artist_wallet": ARTIST})
        self.assertFalse(policy.enabled)
        self.assertEqual(policy.schedule, ft.DEFAULT_SCHEDULE)
        self.assertFalse(ft.FlipTaxPolicy(artist_wallet=ARTIST).enabled)

    def test_to_dict_round_trips_through_from_mapping(self) -> None:
        policy = ft.FlipTaxPolicy(
            artist_wallet=ARTIST, enabled=True, schedule=ft.FlipTaxSchedule(full_bps=1_000)
        )
        self.assertEqual(
            policy.to_dict(),
            {
                "artist_wallet": ARTIST,
                "enabled": True,
                "schedule": policy.schedule.to_dict(),
            },
        )
        self.assertEqual(ft.FlipTaxPolicy.from_mapping(policy.to_dict()), policy)
        off = ft.FlipTaxPolicy(artist_wallet=ARTIST)
        self.assertEqual(ft.FlipTaxPolicy.from_mapping(off.to_dict()), off)

    def test_an_omitted_wallet_inherits_the_events_artist_fee_wallet(self) -> None:
        policy = ft.FlipTaxPolicy.from_mapping({"enabled": True}, default_wallet=ARTIST)
        self.assertEqual(policy.artist_wallet, ARTIST)

    def test_a_missing_wallet_with_no_default_is_refused(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy.from_mapping({"enabled": True})
        self.assertIn("artist_wallet", str(caught.exception))

    def test_a_named_null_wallet_is_refused_and_does_not_inherit(self) -> None:
        # `raw.get` cannot tell an omitted key from an explicit null, and the difference is the
        # one that matters: an omitted wallet may inherit the event's artist fee wallet, while a
        # wallet written as null is a field somebody meant to fill. Defaulting it would pay a
        # tax to an address the config never named.
        for raw in ({"artist_wallet": None}, {"artist_wallet": None, "enabled": True}):
            with self.subTest(raw=raw):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxPolicy.from_mapping(raw, default_wallet=ARTIST)
                self.assertIn("artist_wallet", str(caught.exception))
                self.assertIn("null", str(caught.exception))
        with self.assertRaises(ft.FlipTaxError):
            ft.FlipTaxPolicy.from_mapping({"artist_wallet": None})

    def test_a_wallet_that_differs_from_the_default_is_refused(self) -> None:
        # Two destinations for one event is a decision, not a default.
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy.from_mapping({"artist_wallet": SELLER}, default_wallet=ARTIST)
        message = str(caught.exception)
        self.assertIn("artist_wallet", message)
        self.assertIn(SELLER, message)
        self.assertIn(ARTIST, message)

    def test_a_wallet_equal_to_the_default_is_accepted(self) -> None:
        policy = ft.FlipTaxPolicy.from_mapping({"artist_wallet": ARTIST}, default_wallet=ARTIST)
        self.assertEqual(policy.artist_wallet, ARTIST)

    def test_an_unknown_field_is_refused_naming_the_path(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy.from_mapping(
                {"artist_wallet": ARTIST, "enabled": True, "fee_bps": 500},
                field="events[0].flip_tax",
            )
        message = str(caught.exception)
        self.assertIn("events[0].flip_tax", message)
        self.assertIn("fee_bps", message)

    def test_a_non_boolean_toggle_is_refused(self) -> None:
        for bad in ("true", 1, 0, None, [True]):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxPolicy.from_mapping({"artist_wallet": ARTIST, "enabled": bad})
                self.assertIn("enabled", str(caught.exception))

    def test_a_bad_wallet_is_refused_naming_the_path(self) -> None:
        for bad in ("", "1111", SHORT_WALLET, LONG_WALLET, "0OIl", None, 32, b"\x00" * 32):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.FlipTaxPolicy.from_mapping(
                        {"artist_wallet": bad}, field="events[2].flip_tax"
                    )
                message = str(caught.exception)
                self.assertIn("events[2].flip_tax.artist_wallet", message)

    def test_a_non_object_and_a_bad_schedule_are_refused(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy.from_mapping(["wallet"])
        self.assertIn("flip_tax", str(caught.exception))
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy.from_mapping({"artist_wallet": ARTIST, "schedule": 1_500})
        self.assertIn("flip_tax.schedule", str(caught.exception))

    def test_the_policy_defaults_to_off_and_the_default_schedule(self) -> None:
        policy = ft.FlipTaxPolicy(artist_wallet=ARTIST)
        self.assertFalse(policy.enabled)
        self.assertEqual(policy.schedule, ft.DEFAULT_SCHEDULE)

    def test_the_policy_refuses_a_schedule_of_the_wrong_type_and_a_bad_toggle(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy(artist_wallet=ARTIST, schedule={"full_bps": 1_500})
        self.assertIn("schedule", str(caught.exception))
        with self.assertRaises(ft.FlipTaxError) as caught:
            ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled="yes")  # type: ignore[arg-type]
        self.assertIn("enabled", str(caught.exception))

    def test_the_policy_is_frozen(self) -> None:
        policy = ft.FlipTaxPolicy(artist_wallet=ARTIST, enabled=True)
        with self.assertRaises(FrozenInstanceError):
            policy.enabled = False  # type: ignore[misc]


class TestWalletParityWithTheArtistFee(unittest.TestCase):
    def test_the_same_three_bad_wallets_are_refused_by_both_modules(self) -> None:
        # The check is `artist_fee`'s, restated so this module raises its own error type for its
        # own fields. Three addresses that base58 accepts and a public key does not.
        for value in (SHORT_WALLET, LONG_WALLET, "0OIl"):
            with self.subTest(value=value):
                with self.assertRaises(af.ArtistFeeError) as fee_caught:
                    af.ArtistFeePolicy(artist_wallet=value, fee_bps=FEE_BPS)
                with self.assertRaises(ft.FlipTaxError) as tax_caught:
                    ft.FlipTaxPolicy(artist_wallet=value, enabled=True)
                self.assertNotIsInstance(tax_caught.exception, af.ArtistFeeError)
                self.assertIn("artist_wallet", str(fee_caught.exception))
                self.assertIn("artist_wallet", str(tax_caught.exception))

    def test_a_real_address_is_accepted_by_both(self) -> None:
        for value in (TOKEN_PROGRAM, ARTIST, TAX_ARTIST):
            with self.subTest(value=value):
                self.assertEqual(
                    af.ArtistFeePolicy(artist_wallet=value, fee_bps=FEE_BPS).artist_wallet, value
                )
                self.assertEqual(
                    ft.FlipTaxPolicy(artist_wallet=value, enabled=True).artist_wallet, value
                )

    def test_the_two_error_types_are_distinct_value_errors(self) -> None:
        self.assertTrue(issubclass(ft.FlipTaxError, ValueError))
        self.assertTrue(issubclass(af.ArtistFeeError, ValueError))
        self.assertIsNot(ft.FlipTaxError, af.ArtistFeeError)


class TestSaleInstructions(unittest.TestCase):
    def test_a_fee_and_a_tax_give_four_legs_in_order(self) -> None:
        stage, move = _instruction(11), _instruction(12)
        fee_policy = af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=FEE_BPS)
        built = _sale(stage=stage, move=move, artist_fee=fee_policy)
        self.assertEqual(len(built), 4)
        self.assertIs(built[0], stage)
        self.assertIs(built[3], move)
        fee_leg, tax_leg = built[1], built[2]
        self.assertIsNot(fee_leg, stage)
        self.assertIsNot(tax_leg, move)
        # The fee's leg pays the artist; the tax's leg pays the policy's wallet. Two addresses
        # here, because the config layer is what keeps one event to one recipient and this
        # function's only rule is which wallet the tax leg names.
        self.assertEqual([account.pubkey for account in fee_leg.accounts], [SELLER, ARTIST])
        self.assertEqual([account.pubkey for account in tax_leg.accounts], [SELLER, TAX_ARTIST])
        for leg, amount in ((fee_leg, FEE), (tax_leg, TAX)):
            with self.subTest(amount=amount):
                self.assertEqual(leg.program_id, af.dp.SYSTEM_PROGRAM)
                self.assertEqual(leg.data, bytes([2, 0, 0, 0]) + amount.to_bytes(8, "little"))
                self.assertEqual(
                    [account.is_signer for account in leg.accounts], [True, False]
                )
                self.assertEqual(
                    [account.is_writable for account in leg.accounts], [True, True]
                )

    def test_a_positive_tax_and_no_artist_fee_is_three_legs(self) -> None:
        stage, move = _instruction(11), _instruction(12)
        built = _sale(stage=stage, move=move)
        self.assertEqual(len(built), 3)
        self.assertIs(built[0], stage)
        self.assertIs(built[2], move)
        self.assertEqual([account.pubkey for account in built[1].accounts], [SELLER, TAX_ARTIST])
        self.assertEqual(built[1].data, bytes([2, 0, 0, 0]) + TAX.to_bytes(8, "little"))

    def test_a_thirty_day_hold_leaves_the_artist_fee_sale_alone(self) -> None:
        # The tax is 0 bps at thirty days, so the tuple must be exactly what the artist fee alone
        # builds: same length, same legs, same order, and no 0-lamport transfer.
        stage, move = _instruction(11), _instruction(12)
        fee_policy = af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=FEE_BPS)
        expected = af.sale_instructions(
            stage=stage,
            move=move,
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=PRICE,
            fee_bps=FEE_BPS,
        )
        built = _sale(
            stage=stage,
            move=move,
            held_since_unix=NOW - THIRTY_DAYS,
            artist_fee=fee_policy,
        )
        self.assertEqual(built, expected)
        self.assertEqual(len(built), 3)
        self.assertIs(built[0], stage)
        self.assertIs(built[2], move)
        self.assertEqual(built[1].data, bytes([2, 0, 0, 0]) + FEE.to_bytes(8, "little"))

    def test_a_tax_that_rounds_to_zero_builds_no_transfer(self) -> None:
        # A 1% schedule on a 20-lamport sale is 0 lamports: 20 * 100 // 10_000 = 0. The fee at
        # 500 bps is 1 lamport, so the sale still has a payment in it and the test can tell the
        # omitted tax leg from an omitted fee leg.
        stage, move = _instruction(11), _instruction(12)
        fee_policy = af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=FEE_BPS)
        expected = af.sale_instructions(
            stage=stage,
            move=move,
            seller=SELLER,
            artist_wallet=ARTIST,
            price_lamports=20,
            fee_bps=FEE_BPS,
        )
        built = _sale(
            stage=stage,
            move=move,
            price_lamports=20,
            policy=_policy(schedule=ft.FlipTaxSchedule(full_bps=100)),
            artist_fee=fee_policy,
        )
        self.assertEqual(built, expected)
        self.assertEqual(len(built), 3)
        self.assertEqual(built[1].data, bytes([2, 0, 0, 0]) + (1).to_bytes(8, "little"))
        for leg in built:
            with self.subTest(data=leg.data.hex()):
                self.assertNotEqual(leg.data, bytes([2, 0, 0, 0]) + bytes(8))

    def test_a_tax_free_sale_with_no_artist_fee_is_the_two_legs_handed_in(self) -> None:
        # 6 lamports at 1500 bps is 9_000 // 10_000 = 0, so the tax leg is omitted and the tuple
        # is exactly the two instructions the caller passed in, by identity.
        stage, move = _instruction(11), _instruction(12)
        built = _sale(stage=stage, move=move, price_lamports=6)
        self.assertEqual(len(built), 2)
        self.assertIs(built[0], stage)
        self.assertIs(built[1], move)

    def test_a_disabled_policy_is_refused(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            _sale(policy=ft.FlipTaxPolicy(artist_wallet=TAX_ARTIST))
        message = str(caught.exception)
        self.assertIn("enabled", message)
        self.assertIn("off", message)

    def test_the_artist_may_not_be_the_seller(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            _sale(policy=_policy(artist_wallet=SELLER))
        self.assertIn("artist_wallet", str(caught.exception))

    def test_a_price_of_zero_or_less_is_refused(self) -> None:
        for price in (0, -1):
            with self.subTest(price=price):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    _sale(price_lamports=price)
                self.assertIn("price_lamports", str(caught.exception))
        with self.assertRaises(ft.FlipTaxError) as caught:
            _sale(price_lamports=0)
        self.assertIn("6009", str(caught.exception))

    def test_a_non_integer_price_is_refused(self) -> None:
        for bad in (1.5, True, "1000", None):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    _sale(price_lamports=bad)
                self.assertIn("price_lamports", str(caught.exception))

    def test_a_tax_beyond_u64_is_refused_as_a_tax(self) -> None:
        # 2**64 lamports at 10 000 bps is 2**64 lamports of tax, one more than a System transfer
        # carries; the refusal must name the tax and not an amount the caller never passed.
        with self.assertRaises(ft.FlipTaxError) as caught:
            _sale(
                price_lamports=2**64,
                policy=_policy(schedule=ft.FlipTaxSchedule(full_bps=10_000)),
            )
        self.assertIn("flip_tax_lamports", str(caught.exception))

    def test_a_tax_of_exactly_u64_is_still_buildable(self) -> None:
        built = _sale(
            price_lamports=2**64 - 1,
            policy=_policy(schedule=ft.FlipTaxSchedule(full_bps=10_000)),
        )
        self.assertEqual(len(built), 3)
        self.assertEqual(built[1].data, bytes([2, 0, 0, 0]) + bytes([0xFF] * 8))

    def test_a_policy_of_the_wrong_type_is_refused(self) -> None:
        for bad in ({"artist_wallet": TAX_ARTIST, "enabled": True}, None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    _sale(policy=bad)
                self.assertIn("policy", str(caught.exception))

    def test_an_artist_fee_of_the_wrong_type_is_refused(self) -> None:
        for bad in ({"artist_wallet": ARTIST, "fee_bps": FEE_BPS}, 500):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    _sale(artist_fee=bad)
                self.assertIn("artist_fee", str(caught.exception))

    def test_a_bad_seller_address_is_refused(self) -> None:
        with self.assertRaises(ft.FlipTaxError) as caught:
            _sale(seller=SHORT_WALLET)
        self.assertIn("seller", str(caught.exception))


class TestRecordDecode(unittest.TestCase):
    def test_the_clock_is_read_at_byte_thirty_little_endian_and_signed(self) -> None:
        for value in (1, 255, 256, 3_600, 2**31 - 1, 2**32, 2**63 - 1):
            with self.subTest(value=value):
                self.assertEqual(ft.held_since_unix_from_record(_record(value)), value)

    def test_the_bytes_are_the_field_and_not_its_neighbours(self) -> None:
        # A decoder one byte early reads the policy byte; one byte late reads the authority's
        # first byte. Both are built here so a moved offset fails on the value, not only on the
        # transcription.
        raw = bytearray(70)
        raw[29] = 0x01
        raw[30:38] = (1_234).to_bytes(8, "little", signed=True)
        raw[38] = 0xFF
        self.assertEqual(ft.held_since_unix_from_record(bytes(raw)), 1_234)

    def test_a_negative_field_decodes_negative(self) -> None:
        # The field is i64, not u64: the hook would only write a negative if the validator's
        # clock were negative, and the clamp in `hold_seconds` is what makes that harmless, but a
        # decoder that read it unsigned would turn -5 into 2**64 - 5 and land in the future.
        self.assertEqual(ft.held_since_unix_from_record(_record(-5)), -5)
        self.assertEqual(ft.held_since_unix_from_record(_record(-(2**63))), -(2**63))

    def test_a_short_buffer_is_refused_rather_than_padded(self) -> None:
        for length in (0, 1, 37, 38, 69):
            with self.subTest(length=length):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.held_since_unix_from_record(bytes(length))
                message = str(caught.exception)
                self.assertIn("record", message)
                self.assertIn("70", message)
        # 38 bytes is exactly the end of the field: a 19-byte v1 record plus rubbish, not a v2
        # record, and it must not be read just because the field happens to fit.
        with self.assertRaises(ft.FlipTaxError):
            ft.held_since_unix_from_record(bytes(38))

    def test_a_non_bytes_value_is_refused(self) -> None:
        for bad in ("0" * 70, [0] * 70, None, 70, 70.0):
            with self.subTest(bad=bad):
                with self.assertRaises(ft.FlipTaxError) as caught:
                    ft.held_since_unix_from_record(bad)
                self.assertIn("record", str(caught.exception))

    def test_a_bytearray_and_a_memoryview_are_accepted(self) -> None:
        raw = _record(NOW)
        self.assertEqual(ft.held_since_unix_from_record(bytearray(raw)), NOW)
        self.assertEqual(ft.held_since_unix_from_record(memoryview(raw)), NOW)

    def test_trailing_bytes_are_ignored_not_read(self) -> None:
        self.assertEqual(ft.held_since_unix_from_record(_record(NOW) + b"\xff" * 8), NOW)


class TestRecordLayoutTranscription(unittest.TestCase):
    def test_the_transcription_matches_the_client_layout(self) -> None:
        # Both sides are read, so a field that moves in either file fails here. This is the check
        # that makes transcribing the layout instead of importing it safe.
        self.assertEqual(ft.RECORD_LEN, v2.TicketRecord.LEN)
        layout = {name: (offset, width, kind) for name, offset, width, kind
                  in v2.TICKET_RECORD_LAYOUT}
        offset, width, kind = layout["held_since_unix"]
        self.assertEqual(ft.HELD_SINCE_UNIX_OFFSET, offset)
        self.assertEqual(ft.HELD_SINCE_UNIX_WIDTH, width)
        self.assertEqual(kind, "i64", "the field is signed; the decoder reads it signed")

    def test_the_literals_on_both_sides_are_the_wire_ones(self) -> None:
        # The pins above compare two files that could move together. These are the numbers, so a
        # coordinated move is still a failing test.
        self.assertEqual(
            (ft.RECORD_LEN, ft.HELD_SINCE_UNIX_OFFSET, ft.HELD_SINCE_UNIX_WIDTH),
            (70, 30, 8),
        )
        self.assertEqual(v2.TicketRecord.LEN, 70)
        self.assertEqual(
            [entry for entry in v2.TICKET_RECORD_LAYOUT if entry[0] == "held_since_unix"],
            [("held_since_unix", 30, 8, "i64")],
        )

    def test_the_field_fits_inside_the_record(self) -> None:
        self.assertLessEqual(
            ft.HELD_SINCE_UNIX_OFFSET + ft.HELD_SINCE_UNIX_WIDTH, ft.RECORD_LEN
        )
        # And there is more after it: the authority's 32 bytes, which is why 38 bytes is not a
        # record.
        self.assertEqual(ft.RECORD_LEN - ft.HELD_SINCE_UNIX_OFFSET, 40)


class TestSourceDiscipline(unittest.TestCase):
    def test_there_is_no_float_literal_and_no_true_division(self) -> None:
        # Unlike `artist_fee`, this module has no path join, so no operand is exempt: every `/`
        # here would be money arithmetic and every `/` in money arithmetic is a bug.
        tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
        divides = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div)
        ]
        self.assertEqual(divides, [], "money arithmetic is integer only; `//` or nothing")
        floats = [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, float)
        ]
        self.assertEqual(floats, [], "no float literal belongs in a lamport calculation")

    def test_the_module_imports_no_gateway_and_no_network(self) -> None:
        # A tax calculation is arithmetic: it has no reason to open a socket, and the gateway
        # imports the modules underneath it, so an import back would be a cycle.
        tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
                imported.update(f"{node.module}.{alias.name}" for alias in node.names)
        for forbidden in ("market_swarm.gateway", "socket", "urllib", "http.client",
                          "subprocess", "time"):
            with self.subTest(forbidden=forbidden):
                self.assertFalse(
                    [name for name in imported
                     if name == forbidden or name.startswith(forbidden + ".")],
                    f"flip_tax must not import {forbidden}",
                )

    def test_the_constants_are_pinned(self) -> None:
        self.assertEqual(ft.BPS_DENOMINATOR, 10_000)
        self.assertEqual(ft.MAX_BPS, 10_000)
        self.assertEqual(ft.U64_MAX, 2**64 - 1)
        self.assertEqual(ft.UNKNOWN_HOLD, 0)
        self.assertEqual(ft.DEFAULT_FULL_BPS, 1_500)
        self.assertEqual(ft.DEFAULT_FULL_HOLD_SECONDS, 3_600)
        self.assertEqual(ft.DEFAULT_ZERO_HOLD_SECONDS, 2_592_000)

    def test_the_public_surface_is_the_one_the_checkout_codes_to(self) -> None:
        for name in (
            "FlipTaxError",
            "BPS_DENOMINATOR",
            "MAX_BPS",
            "U64_MAX",
            "FlipTaxSchedule",
            "DEFAULT_SCHEDULE",
            "FlipTaxPolicy",
            "Assessment",
            "hold_seconds",
            "held_since_unix_from_record",
            "assess",
            "sale_instructions",
        ):
            with self.subTest(name=name):
                self.assertTrue(hasattr(ft, name), f"flip_tax is missing {name}")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

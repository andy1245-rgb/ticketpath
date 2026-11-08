"""The mutation harness: proof that the flip-tax tests can fail.

`test_flip_tax.py` asserts what the module does. This file asks the other question -- if the
module did something else, would anybody notice? It is built from the same two tables
`test_artist_fee_mutation.py` uses:

- **properties**, each a function taking a loaded module and raising `AssertionError` (or any
  other exception) if the module breaks one rule. They take the module as an argument rather
  than importing `market_swarm.flip_tax` directly, so the same property runs against a modified
  copy;
- **mutations**, each a single source-text replacement applied to a temporary copy of
  `market_swarm/flip_tax.py`, loaded under its own name with `importlib`. Every mutation must
  break at least one property, and the mutation's comment says which one. One that breaks none
  is a hole in the suite and this file **fails** naming it -- it does not skip, because a
  skipped hole is a hole.

The unmutated source runs through the same properties as a control. Without it a property table
that raised on everything would look like a suite that caught every mutation.

**The one mutation behaviour alone cannot see, and how this suite sees it.** At exactly
`full_hold_seconds` the flat branch and the falling branch return the same number: the line
starts at `(full_hold_seconds, full_bps)`, so `full_bps * (zero - full) // (zero - full)` is
`full_bps` for every legal schedule. Flipping the boundary comparison from `<=` to `<` therefore
changes no output, and an assertion on the value at 3600 passes either way. The difference that
*is* observable is that the falling branch subtracts the hold from the zero point, so the
`boundary-is-the-flat-branch` property hands the module a hold whose subtraction raises. That
turns "which branch ran" into a behaviour rather than a reading of the source.

The mutations are the ones the build brief names -- the raised maximum, the changed denominator,
the ceiling that killed the token fee, the unknown hold priced as zero seconds, the unclamped
future, the line replaced by a constant, the exclusive zero point, the inclusive full-hold
boundary, each removed refusal, the tax leg after the move, the inverted zero-tax omission, the
record offset, the removed record-length check, the flipped `enabled` default and the accepted
wallet mismatch -- plus the ones a reader would try next: a ceiling inside the line, a removed
wallet-length check, a widened policy whitelist, a shortened record constant, and the
denominator swapped for the rate bound (which is invisible at runtime because both are 10 000
today, and which `constants-independent` catches by moving one of them).

No network, no validator, no key: a mutation is text, and a property is arithmetic.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from market_swarm import artist_fee
from ticketpath.onchain import v2

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = REPO_ROOT / "market_swarm" / "flip_tax.py"
SOURCE = SOURCE_PATH.read_text(encoding="utf-8")

SELLER = artist_fee.dp.base58.encode(bytes(range(1, 33)))
ARTIST = artist_fee.dp.base58.encode(bytes(range(33, 65)))
TAX_ARTIST = artist_fee.dp.base58.encode(bytes(range(65, 97)))
SHORT_WALLET = artist_fee.dp.base58.encode(bytes(range(1, 32)))
LONG_WALLET = artist_fee.dp.base58.encode(bytes(range(1, 34)))

PRICE = 1_000_000_000
FULL_BPS = 1_500
TAX = PRICE * FULL_BPS // 10_000  # 150_000_000
FEE_BPS = 500
FEE = PRICE * FEE_BPS // 10_000  # 50_000_000
NOW = 1_700_000_000
THIRTY_DAYS = 2_592_000

#: The default schedule's rate for a hold, as literals. The same table as `test_flip_tax.py`'s,
#: restated here because a property takes a loaded module and cannot borrow the other file's
#: constants without also borrowing its assumptions.
PINNED_RATES = {
    0: 1_500,
    3_540: 1_500,
    3_600: 1_500,
    3_601: 1_499,  # 1500 * 2_588_399 // 2_588_400 = 1499.9994, floored
    1_296_000: 751,  # 1500 * 1_296_000 // 2_588_400 = 751.04, floored
    1_297_800: 750,  # the exact midpoint
    2_591_999: 0,
    2_592_000: 0,
    2_592_001: 0,
}

#: The System `Transfer` of nothing: a u32 bincode tag of 2 then eight zero bytes. A payment of
#: nothing, and the thing the zero-tax omission exists to prevent.
ZERO_TRANSFER = bytes([2, 0, 0, 0]) + bytes(8)


# -- the property table ------------------------------------------------------


class _TrappingHold(int):
    """An `int` that refuses to be subtracted from the zero point.

    Proof that the flat branch ran, not the falling one. The two agree on the value at exactly
    `full_hold_seconds`, so the only observable difference between them is that the falling
    branch computes `zero_hold_seconds - held`; a hold whose `__rsub__` raises makes that
    difference a failure. `int` arithmetic in Python gives a subclass's reflected method
    priority, which is what lets a plain number carry this.
    """

    def __rsub__(self, other: object) -> int:
        raise AssertionError(
            "the falling branch was taken at the full-hold point; that boundary is inclusive"
        )


def refusal(module, call, what: str):
    """The `FlipTaxError` a call must raise; an `AssertionError` if it raised nothing."""
    try:
        result = call()
    except module.FlipTaxError as exc:
        return exc
    raise AssertionError(f"{what}: expected FlipTaxError, got {result!r}")


def legs(module) -> tuple:
    """Two stand-ins for the instructions this module does not build."""
    system = module.af.dp.SYSTEM_PROGRAM
    return (
        module.af.dp.Instruction(program_id=system, accounts=(), data=b"\x0b"),
        module.af.dp.Instruction(program_id=system, accounts=(), data=b"\x0c"),
    )


def sale(module, **overrides) -> tuple:
    """A taxed sale at the design's worked pair, a minute into the hold, with any argument
    replaced. A minute is under the full-hold point, so the rate is the full one."""
    stage, move = legs(module)
    arguments = {
        "stage": stage,
        "move": move,
        "seller": SELLER,
        "policy": module.FlipTaxPolicy(artist_wallet=TAX_ARTIST, enabled=True),
        "price_lamports": PRICE,
        "held_since_unix": NOW - 60,
        "now_unix": NOW,
    }
    arguments.update(overrides)
    return module.sale_instructions(**arguments)


def record(held_since_unix: int) -> bytes:
    """A 70-byte v2 record with the hook's clock at **literal** byte 30.

    Literal on purpose: a buffer built from `module.HELD_SINCE_UNIX_OFFSET` would move with a
    moved constant, and `record-decode` would then pass against a module reading the wrong byte.
    """
    raw = bytearray(70)
    raw[30:38] = held_since_unix.to_bytes(8, "little", signed=True)
    return bytes(raw)


def property_schedule_table(module) -> None:
    """The pinned rate table, the boundaries, and a rate that never rises with the hold."""
    schedule = module.DEFAULT_SCHEDULE
    assert schedule.full_bps == FULL_BPS, f"the default rate is {schedule.full_bps}"
    assert schedule.full_hold_seconds == 3_600, f"the full hold is {schedule.full_hold_seconds}"
    assert schedule.zero_hold_seconds == 2_592_000, (
        f"the zero point is {schedule.zero_hold_seconds}"
    )
    for held, expected in sorted(PINNED_RATES.items()):
        got = schedule.bps_for(held)
        assert got == expected, f"bps_for({held}) = {got}, expected {expected}"
    previous = schedule.bps_for(0)
    for held in range(0, THIRTY_DAYS + 1, 997):
        rate = schedule.bps_for(held)
        assert rate <= previous, f"bps_for({held}) = {rate} rose above {previous}: not falling"
        assert 0 <= rate <= FULL_BPS, f"bps_for({held}) = {rate} is outside 0..{FULL_BPS}"
        previous = rate


def property_hold_seconds(module) -> None:
    """Unknown is `None`, a future instant clamps to 0, a normal pair is the difference."""
    for now in (0, 1, NOW, 2**40):
        got = module.hold_seconds(0, now)
        assert got is None, f"hold_seconds(0, {now}) = {got!r}, expected None for an unknown hold"
    for ahead in (1, 3_600, THIRTY_DAYS, 2**40):
        got = module.hold_seconds(NOW + ahead, NOW)
        assert got == 0, f"hold_seconds({NOW + ahead}, {NOW}) = {got!r}, expected 0 (clamped)"
    assert module.hold_seconds(NOW - 3_540, NOW) == 3_540, "a 59-minute hold is not 3_540"
    assert module.hold_seconds(NOW - THIRTY_DAYS, NOW) == THIRTY_DAYS
    assert module.hold_seconds(NOW, NOW) == 0


def property_unknown_pays_the_full_rate(module) -> None:
    """An unset clock is the full rate, and the row says why. Not 0%, not a refusal."""
    assessment = module.assess(price_lamports=PRICE, held_since_unix=0, now_unix=NOW)
    assert assessment.held_seconds is None, f"an unknown hold reported {assessment.held_seconds!r}"
    assert assessment.known is False, "an unknown hold says it is known"
    assert assessment.bps == FULL_BPS, f"an unknown hold was charged {assessment.bps} bps"
    assert assessment.lamports == TAX, f"an unknown hold was charged {assessment.lamports}"
    assert assessment.to_dict() == {"held_seconds": None, "bps": FULL_BPS, "lamports": TAX}


def property_thirty_days_is_free(module) -> None:
    """The zero point is 0 bps and 0 lamports, with the age still on the row."""
    assessment = module.assess(
        price_lamports=PRICE, held_since_unix=NOW - THIRTY_DAYS, now_unix=NOW
    )
    assert assessment.held_seconds == THIRTY_DAYS, f"held_seconds {assessment.held_seconds}"
    assert assessment.known is True
    assert assessment.bps == 0, f"a thirty-day hold was charged {assessment.bps} bps"
    assert assessment.lamports == 0, f"a thirty-day hold was charged {assessment.lamports}"


def property_arithmetic_and_bound(module) -> None:
    """`price * bps // 10_000`, and never more than the price for any rate a schedule carries."""
    for price in (0, 1, 19, 20, 999, 1_000_000, PRICE, 2**64 - 1):
        for rate in (0, 1, 250, 1_500, 2_500, 9_999, 10_000):
            assessment = module.assess(
                price_lamports=price,
                held_since_unix=NOW - 60,
                now_unix=NOW,
                schedule=module.FlipTaxSchedule(full_bps=rate),
            )
            expected = price * rate // 10_000
            assert assessment.lamports == expected, (
                f"assess({price}, {rate} bps) = {assessment.lamports}, expected {expected}"
            )
            assert type(assessment.lamports) is int, "the tax came back as a non-int"
            assert 0 <= assessment.lamports <= price, (
                f"assess({price}, {rate} bps) = {assessment.lamports}, outside 0..{price}"
            )


def property_floor_not_ceiling(module) -> None:
    """Floor, stated independently of the module's own expression.

    A ceiling takes the whole ticket at 1 lamport and 3 of 19: the defect that killed the
    Token-2022 fee (finding 36 §2), one unit lower down. 19 * 1_500 = 28_500, so 2 is floor and
    3 is ceiling; 1 * 1_500 = 1_500, so 0 is floor and 1 is ceiling.
    """
    for price, expected in ((1, 0), (19, 2), (20, 3), (999, 149)):
        assessment = module.assess(
            price_lamports=price, held_since_unix=NOW - 60, now_unix=NOW
        )
        assert assessment.lamports == expected, (
            f"assess({price}, 1500 bps) = {assessment.lamports}, expected {expected} (floored); "
            f"a ceiling would give {-(-price * FULL_BPS // 10_000)}"
        )


def property_rate_bound(module) -> None:
    """10 000 is the largest rate, and the two numbers the arithmetic depends on are pinned."""
    assert module.MAX_BPS == 10_000, f"MAX_BPS {module.MAX_BPS}"
    assert module.BPS_DENOMINATOR == 10_000, f"BPS_DENOMINATOR {module.BPS_DENOMINATOR}"
    assert module.U64_MAX == 2**64 - 1, f"U64_MAX {module.U64_MAX}"
    assert module.FlipTaxSchedule(full_bps=10_000).full_bps == 10_000
    for bad in (10_001, 20_000, 2**40):
        error = refusal(
            module,
            lambda bad=bad: module.FlipTaxSchedule(full_bps=bad),
            f"a rate of {bad} bps",
        )
        assert "full_bps" in str(error), f"the refusal blamed {str(error)!r}"
    for bad in (-1, True, 500.0, "500", None):
        refusal(
            module,
            lambda bad=bad: module.FlipTaxSchedule(full_bps=bad),
            f"a rate of {bad!r}",
        )


def property_boundary_is_the_flat_branch(module) -> None:
    """3600 is the flat rate, and the flat branch is the one that produced it.

    The value alone cannot tell the branches apart at the boundary, so the trapping hold is what
    makes this property able to fail. The one second after the boundary is the same argument in
    numbers: 1499 is the line, and a schedule stuck on the full rate reads 1500.
    """
    schedule = module.DEFAULT_SCHEDULE
    assert schedule.bps_for(3_600) == FULL_BPS, f"bps_for(3600) = {schedule.bps_for(3_600)}"
    trapped = schedule.bps_for(_TrappingHold(3_600))
    assert trapped == FULL_BPS, f"bps_for(3600) = {trapped} through the trap"
    assert schedule.bps_for(3_601) == 1_499, (
        f"bps_for(3601) = {schedule.bps_for(3_601)}; 1500 would be the full rate, so the line "
        "is not being read"
    )
    assert schedule.bps_for(3_601) != schedule.bps_for(3_600), "the rate did not start falling"


def property_zero_point_inclusive(module) -> None:
    """At and past the zero point the rate is exactly 0, never negative."""
    schedule = module.DEFAULT_SCHEDULE
    for held in (2_591_999, 2_592_000, 2_592_001, 2_592_000 * 2, 2**40):
        rate = schedule.bps_for(held)
        assert rate == 0, f"bps_for({held}) = {rate}, expected 0"
    for held in range(THIRTY_DAYS, THIRTY_DAYS + 5_000, 37):
        rate = schedule.bps_for(held)
        assert rate == 0, f"bps_for({held}) = {rate}: past the zero point must be 0, not negative"


def property_disabled_policy_refused(module) -> None:
    """The toggle is the event maker's and the default is off, so a builder refuses a policy
    that is off rather than charging it."""
    for policy in (
        module.FlipTaxPolicy(artist_wallet=TAX_ARTIST),
        module.FlipTaxPolicy(artist_wallet=TAX_ARTIST, enabled=False),
        module.FlipTaxPolicy.from_mapping({"artist_wallet": TAX_ARTIST}),
    ):
        error = refusal(module, lambda policy=policy: sale(module, policy=policy),
                        "a sale on a disabled policy")
        assert "enabled" in str(error), f"the refusal blamed {str(error)!r}"


def property_artist_is_seller_refused(module) -> None:
    """A tax paid to the seller pays nothing and would be logged as one."""
    error = refusal(
        module,
        lambda: sale(module, policy=module.FlipTaxPolicy(artist_wallet=SELLER, enabled=True)),
        "an artist who is the seller",
    )
    assert "artist_wallet" in str(error), f"the refusal blamed {str(error)!r}"


def property_price_must_be_positive(module) -> None:
    """A staged 0 reads on chain as 'nothing staged' and is refused with 6009."""
    for price in (0, -1):
        error = refusal(module, lambda price=price: sale(module, price_lamports=price),
                        f"a price of {price}")
        assert "price_lamports" in str(error), f"the refusal blamed {str(error)!r}"
    for bad in (1.5, True, "1000", None):
        error = refusal(module, lambda bad=bad: sale(module, price_lamports=bad),
                        f"a price of {bad!r}")
        assert "price_lamports" in str(error), f"the refusal blamed {str(error)!r}"


def property_tax_beyond_u64_refused(module) -> None:
    """The sale is refused as a tax, not as an amount the caller never passed.

    2**64 lamports at 10 000 bps is 2**64 lamports of tax, one more than a System transfer
    carries.
    """
    def build():
        return sale(
            module,
            price_lamports=2**64,
            policy=module.FlipTaxPolicy(
                artist_wallet=TAX_ARTIST,
                enabled=True,
                schedule=module.FlipTaxSchedule(full_bps=10_000),
            ),
        )

    try:
        built = build()
    except module.FlipTaxError as exc:
        assert "flip_tax_lamports" in str(exc), f"the refusal blamed {str(exc)!r}"
        return
    raise AssertionError(f"a tax of 2**64 lamports was built as {built!r}")


def property_instruction_order(module) -> None:
    """`(stage, artist_fee, flip_tax, move)`, and `(stage, flip_tax, move)` with no fee.

    The tax leg is last before the move: both payments sit between the instruction that
    authorises the price and the one the hook checks.
    """
    stage, move = legs(module)
    fee_policy = module.af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=FEE_BPS)
    built = sale(module, stage=stage, move=move, artist_fee=fee_policy)
    assert len(built) == 4, f"a fee and a tax built {len(built)} instructions, expected 4"
    assert built[0] is stage, "the stage must be first: the hook reads a staged price"
    assert built[3] is move, "the token move must be last, after both payments"
    fee_leg, tax_leg = built[1], built[2]
    assert fee_leg.data == bytes([2, 0, 0, 0]) + FEE.to_bytes(8, "little"), (
        f"the fee leg carries {fee_leg.data.hex()}"
    )
    assert tax_leg.data == bytes([2, 0, 0, 0]) + TAX.to_bytes(8, "little"), (
        f"the tax leg carries {tax_leg.data.hex()}"
    )
    assert [account.pubkey for account in tax_leg.accounts] == [SELLER, TAX_ARTIST], (
        f"the tax leg pays {[a.pubkey for a in tax_leg.accounts]}"
    )
    assert [account.is_signer for account in tax_leg.accounts] == [True, False]

    without_fee = sale(module, stage=stage, move=move)
    assert len(without_fee) == 3, f"a tax and no fee built {len(without_fee)} instructions"
    assert without_fee[0] is stage and without_fee[2] is move
    assert without_fee[1].data == bytes([2, 0, 0, 0]) + TAX.to_bytes(8, "little")


def property_zero_tax_omits_the_leg(module) -> None:
    """A zero tax is no leg at all: the tuple is exactly what the artist fee alone builds.

    Two ways to reach zero: a rate that rounds the whole tax away (20 lamports at 100 bps is
    2_000 // 10_000 = 0, while the 500-bps fee on the same sale is 1 lamport), and a hold at the
    zero point on a one-SOL sale. Neither may produce a transfer of nothing.
    """
    stage, move = legs(module)
    fee_policy = module.af.ArtistFeePolicy(artist_wallet=ARTIST, fee_bps=FEE_BPS)
    expected = module.af.sale_instructions(
        stage=stage,
        move=move,
        seller=SELLER,
        artist_wallet=ARTIST,
        price_lamports=20,
        fee_bps=FEE_BPS,
    )
    rounded_away = sale(
        module,
        stage=stage,
        move=move,
        price_lamports=20,
        policy=module.FlipTaxPolicy(
            artist_wallet=TAX_ARTIST,
            enabled=True,
            schedule=module.FlipTaxSchedule(full_bps=100),
        ),
        artist_fee=fee_policy,
    )
    assert rounded_away == expected, (
        f"a tax that rounds to zero built {rounded_away!r}; the fee alone builds {expected!r}"
    )
    assert expected[1].data == bytes([2, 0, 0, 0]) + (1).to_bytes(8, "little"), (
        "the fee on a 20-lamport sale at 500 bps is one lamport; the sale must still pay it"
    )
    aged_out = sale(module, stage=stage, move=move, held_since_unix=NOW - THIRTY_DAYS)
    assert len(aged_out) == 2, f"a thirty-day hold built {len(aged_out)} instructions, expected 2"
    assert aged_out[0] is stage and aged_out[1] is move
    for leg in (*rounded_away, *aged_out):
        assert leg.data != ZERO_TRANSFER, "a 0-lamport System transfer was built"


def property_record_decode(module) -> None:
    """The clock is at literal byte 30, little-endian and signed, and a short buffer is refused."""
    for value in (1, 255, 256, 3_600, 2**31 - 1, 2**32, 2**63 - 1):
        got = module.held_since_unix_from_record(record(value))
        assert got == value, f"the decoded clock is {got}, expected {value}"
    assert module.held_since_unix_from_record(record(-5)) == -5, "a negative clock lost its sign"
    neighbour = bytearray(70)
    neighbour[29] = 0x01
    neighbour[30:38] = (1_234).to_bytes(8, "little", signed=True)
    neighbour[38] = 0xFF
    assert module.held_since_unix_from_record(bytes(neighbour)) == 1_234, (
        "the decoder read the policy byte or the authority byte instead of the clock"
    )
    for length in (0, 1, 37, 38, 69):
        error = refusal(
            module,
            lambda length=length: module.held_since_unix_from_record(bytes(length)),
            f"a {length}-byte record",
        )
        assert "record" in str(error), f"the refusal blamed {str(error)!r}"
    for bad in ("0" * 70, [0] * 70, None, 70):
        refusal(
            module,
            lambda bad=bad: module.held_since_unix_from_record(bad),
            f"a record of {type(bad).__name__}",
        )


def property_layout_transcription(module) -> None:
    """The transcribed record layout still matches the client's own.

    Both sides are read, so a field that moves in either file fails: this is the check that makes
    transcribing rather than importing safe.
    """
    assert module.RECORD_LEN == v2.TicketRecord.LEN, (
        f"RECORD_LEN {module.RECORD_LEN}, TicketRecord.LEN {v2.TicketRecord.LEN}"
    )
    layout = {name: (offset, width, kind) for name, offset, width, kind
              in v2.TICKET_RECORD_LAYOUT}
    offset, width, kind = layout["held_since_unix"]
    assert module.HELD_SINCE_UNIX_OFFSET == offset, (
        f"offset {module.HELD_SINCE_UNIX_OFFSET}, the layout says {offset}"
    )
    assert module.HELD_SINCE_UNIX_WIDTH == width, (
        f"width {module.HELD_SINCE_UNIX_WIDTH}, the layout says {width}"
    )
    assert kind == "i64", f"the field is {kind}; the decoder reads it signed"
    assert (module.RECORD_LEN, module.HELD_SINCE_UNIX_OFFSET, module.HELD_SINCE_UNIX_WIDTH) == (
        70,
        30,
        8,
    ), "the literals moved: the record is 70 bytes and the clock is eight bytes at byte 30"


def property_wallet_is_32_bytes(module) -> None:
    """Base58 is not a length check: a 31- or 33-byte string decodes happily and is wrong."""
    for bad in (SHORT_WALLET, LONG_WALLET, "", "0OIl", b"\x00" * 32, None):
        error = refusal(
            module,
            lambda bad=bad: module.FlipTaxPolicy(artist_wallet=bad, enabled=True),
            f"a wallet of {bad!r}",
        )
        assert "artist_wallet" in str(error), f"the refusal blamed {str(error)!r}"
    assert module.FlipTaxPolicy(artist_wallet=ARTIST, enabled=True).artist_wallet == ARTIST


def property_policy_mapping(module) -> None:
    """A policy round-trips, the toggle defaults off, and the wallet rules hold.

    The default is the rule the brief spells out: an omitted toggle is off, and a block that
    names a different wallet from the event's artist fee is refused rather than redirecting the
    money.
    """
    off = module.FlipTaxPolicy.from_mapping({"artist_wallet": ARTIST})
    assert off.enabled is False, f"an omitted toggle parsed as enabled={off.enabled!r}"
    assert off.schedule == module.DEFAULT_SCHEDULE, "an omitted schedule is not the default"
    full = module.FlipTaxPolicy(
        artist_wallet=ARTIST, enabled=True, schedule=module.FlipTaxSchedule(full_bps=1_000)
    )
    assert full.to_dict() == {
        "artist_wallet": ARTIST,
        "enabled": True,
        "schedule": full.schedule.to_dict(),
    }, f"to_dict {full.to_dict()}"
    assert module.FlipTaxPolicy.from_mapping(full.to_dict()) == full, "a policy did not round-trip"
    inherited = module.FlipTaxPolicy.from_mapping({"enabled": True}, default_wallet=ARTIST)
    assert inherited.artist_wallet == ARTIST, "the artist fee's wallet was not inherited"

    for unknown in ("rate", "fee_bps", "bps", "wallet", "artistWallet", "Enabled"):
        error = refusal(
            module,
            lambda name=unknown: module.FlipTaxPolicy.from_mapping(
                {"artist_wallet": ARTIST, name: 1}, field="events[0].flip_tax"
            ),
            f"an unknown key {unknown!r}",
        )
        assert "events[0].flip_tax" in str(error) and unknown in str(error), (
            f"the message for {unknown!r} is {str(error)!r}"
        )
    error = refusal(
        module,
        lambda: module.FlipTaxPolicy.from_mapping({"enabled": True}),
        "a wallet with no default to inherit",
    )
    assert "artist_wallet" in str(error), f"the refusal blamed {str(error)!r}"
    error = refusal(
        module,
        lambda: module.FlipTaxPolicy.from_mapping(
            {"artist_wallet": SELLER}, default_wallet=ARTIST
        ),
        "a wallet that differs from the event's artist fee",
    )
    assert SELLER in str(error) and ARTIST in str(error), f"the refusal says {str(error)!r}"
    for bad in ("true", 1, 0, None):
        refusal(
            module,
            lambda bad=bad: module.FlipTaxPolicy.from_mapping(
                {"artist_wallet": ARTIST, "enabled": bad}
            ),
            f"a toggle of {bad!r}",
        )


def property_schedule_mapping(module) -> None:
    """A schedule round-trips, a partial mapping keeps the fields it does not name, and an
    unknown key is refused rather than ignored."""
    schedule = module.FlipTaxSchedule(
        full_bps=1_000, full_hold_seconds=1_800, zero_hold_seconds=1_296_000
    )
    assert schedule.to_dict() == {
        "full_bps": 1_000,
        "full_hold_seconds": 1_800,
        "zero_hold_seconds": 1_296_000,
    }, f"to_dict {schedule.to_dict()}"
    assert module.FlipTaxSchedule.from_mapping(schedule.to_dict()) == schedule
    partial = module.FlipTaxSchedule.from_mapping({"full_bps": 1_000})
    assert partial.full_hold_seconds == 3_600, f"full_hold_seconds {partial.full_hold_seconds}"
    assert partial.zero_hold_seconds == 2_592_000, f"zero_hold_seconds {partial.zero_hold_seconds}"
    assert module.FlipTaxSchedule.from_mapping({}) == module.DEFAULT_SCHEDULE
    error = refusal(
        module,
        lambda: module.FlipTaxSchedule.from_mapping({"full_bps": 1_000, "rate": 15},
                                                    field="events[0].flip_tax.schedule"),
        "an unknown schedule key",
    )
    assert "events[0].flip_tax.schedule" in str(error) and "rate" in str(error), (
        f"the message is {str(error)!r}"
    )
    for full, zero in ((100, 100), (100, 99), (3_600, 0)):
        refusal(
            module,
            lambda full=full, zero=zero: module.FlipTaxSchedule(
                full_hold_seconds=full, zero_hold_seconds=zero
            ),
            f"a curve from {full} to {zero}",
        )


def property_constants_independent(module) -> None:
    """The rate bound and the denominator are two rules, not one number under two names.

    Both are 10 000 today, so dividing by the wrong one is invisible at runtime. This property
    moves `MAX_BPS` and asserts the arithmetic does not move with it: a module whose division
    used the rate bound fails here the moment the bound is retuned, which is the bug the module's
    own comment says the two names exist to prevent.
    """
    saved = module.MAX_BPS
    try:
        for raised in (20_000, 5_000):
            module.MAX_BPS = raised
            got = module.assess(price_lamports=PRICE, held_since_unix=NOW - 60,
                                now_unix=NOW).lamports
            assert got == TAX, (
                f"with MAX_BPS = {raised}, the tax on {PRICE} lamports is {got}, expected {TAX}: "
                "the rate bound is being used as the basis-point denominator"
            )
    finally:
        module.MAX_BPS = saved


def property_one_lamport_is_a_payment(module) -> None:
    """A tax of exactly 1 lamport is a payment, and it must be built as one.

    The omission rule is `== 0`, and a sale whose tax is 1 lamport is the nearest thing to it: a
    module that widened the rule to `<= 1` builds a sale that moves the ticket and charges a seller
    who owed a lamport nothing, and nothing else in the suite notices, because one lamport is below
    every other test's noise floor. Measured in review: that mutant survived the whole
    `market_swarm` suite.

    7 lamports at the full 1 500 bps is 10 500 // 10 000 = 1, and 6 is 9 000 // 10 000 = 0, so the
    two properties together pin the floor from both sides.
    """
    stage, move = legs(module)
    legs_one = sale(
        module,
        stage=stage,
        move=move,
        price_lamports=7,
        policy=module.FlipTaxPolicy(artist_wallet=TAX_ARTIST, enabled=True),
    )
    assert len(legs_one) == 3, f"a 1-lamport tax built {len(legs_one)} legs, expected 3"
    assert legs_one[0] == stage and legs_one[2] == move, "the tax leg is not between the two"
    built = legs_one[1]
    assert built.program_id == module.af.dp.SYSTEM_PROGRAM, f"the leg's program is {built.program_id}"
    assert built.data == bytes.fromhex("02000000") + (1).to_bytes(8, "little"), (
        f"the leg's data is {built.data!r}; a System Transfer of 1 lamport is 02 00 00 00 01 00 00 "
        "00 00 00 00 00"
    )
    assert built.accounts[1].pubkey == TAX_ARTIST, built.accounts[1].pubkey
    assert module.assess(price_lamports=7, held_since_unix=NOW - 60, now_unix=NOW).lamports == 1
    assert module.assess(price_lamports=6, held_since_unix=NOW - 60, now_unix=NOW).lamports == 0


PROPERTIES = (
    ("schedule-table", property_schedule_table),
    ("hold-seconds", property_hold_seconds),
    ("unknown-pays-the-full-rate", property_unknown_pays_the_full_rate),
    ("thirty-days-is-free", property_thirty_days_is_free),
    ("arithmetic-and-bound", property_arithmetic_and_bound),
    ("floor-not-ceiling", property_floor_not_ceiling),
    ("rate-bound", property_rate_bound),
    ("boundary-is-the-flat-branch", property_boundary_is_the_flat_branch),
    ("zero-point-inclusive", property_zero_point_inclusive),
    ("disabled-policy-refused", property_disabled_policy_refused),
    ("artist-is-seller-refused", property_artist_is_seller_refused),
    ("price-must-be-positive", property_price_must_be_positive),
    ("tax-beyond-u64-refused", property_tax_beyond_u64_refused),
    ("instruction-order", property_instruction_order),
    ("zero-tax-omits-the-leg", property_zero_tax_omits_the_leg),
    ("one-lamport-is-a-payment", property_one_lamport_is_a_payment),
    ("record-decode", property_record_decode),
    ("layout-transcription", property_layout_transcription),
    ("wallet-is-32-bytes", property_wallet_is_32_bytes),
    ("policy-mapping", property_policy_mapping),
    ("schedule-mapping", property_schedule_mapping),
    ("constants-independent", property_constants_independent),
)


# -- the mutation table ------------------------------------------------------

#: Each entry is `(name, old_text, new_text)`, and the comment above each says which property
#: catches it. `old_text` must appear exactly once in the source: a table entry that no longer
#: matches the file is a stale mutation, and this file fails on it rather than silently passing.
MUTATIONS = (
    # rate-bound and arithmetic-and-bound: 10 001 bps is accepted, and a full-rate sale of
    # 2**64 lamports charges more than the price it is taken from.
    ("max-rate-raised", "MAX_BPS = 10_000", "MAX_BPS = 20_000"),
    # arithmetic-and-bound: every lamport figure moves by a factor of ten.
    ("denominator-changed-to-1000", "BPS_DENOMINATOR = 10_000", "BPS_DENOMINATOR = 1_000"),
    # floor-not-ceiling: 19 lamports at 1500 bps becomes 3, and 1 lamport becomes 1.
    (
        "ceiling-in-the-tax",
        "lamports=price * bps // BPS_DENOMINATOR",
        "lamports=(price * bps + BPS_DENOMINATOR - 1) // BPS_DENOMINATOR",
    ),
    # schedule-table and boundary-is-the-flat-branch: 3601 comes back as 1500, not 1499.
    (
        "ceiling-in-the-line",
        "        return self.full_bps * (self.zero_hold_seconds - held) // span",
        "        return -(-self.full_bps * (self.zero_hold_seconds - held) // span)",
    ),
    # hold-seconds and unknown-pays-the-full-rate: an unset field is priced as `now - 0`, which
    # lands past the zero point, so an unknown hold becomes the cheapest evasion in the system.
    (
        "unknown-hold-priced-as-zero-seconds",
        "    if since == UNKNOWN_HOLD:\n        return None",
        "    if since == -1:\n        return None",
    ),
    # hold-seconds: a clock that went backwards yields a negative age instead of clamping.
    ("future-hold-not-clamped", "    return max(0, now - since)", "    return now - since"),
    # schedule-table: the falling segment is replaced by the flat rate, so nothing ever falls.
    (
        "line-replaced-by-the-full-rate",
        "        return self.full_bps * (self.zero_hold_seconds - held) // span",
        "        return self.full_bps",
    ),
    # zero-point-inclusive: the zero branch fires only at the instant itself, so a hold one
    # second past thirty days is put through the line and floors to -1 bps, a negative tax.
    (
        "zero-point-read-as-exclusive",
        "        if held >= self.zero_hold_seconds:",
        "        if held == self.zero_hold_seconds:",
    ),
    # boundary-is-the-flat-branch: at exactly 3600 the falling branch runs. Its value is also
    # 1500, which is why the property hands in a hold whose subtraction raises.
    (
        "full-hold-boundary-exclusive",
        "        if held <= self.full_hold_seconds:",
        "        if held < self.full_hold_seconds:",
    ),
    # disabled-policy-refused: a policy that is off is charged for.
    ("disabled-policy-refusal-removed", "    if not policy.enabled:", "    if False:"),
    # artist-is-seller-refused: the seller pays themselves, and the sale logs a tax it did not
    # move.
    (
        "artist-is-seller-refusal-removed",
        "    if policy.artist_wallet == seller_address:",
        "    if False:",
    ),
    # price-must-be-positive: a staged 0, which the chain refuses with 6009, is built anyway.
    ("price-check-removed", "    if price <= 0:", "    if False:"),
    # tax-beyond-u64-refused: the tax is handed to the fee module's transfer builder instead,
    # which refuses it as an amount nobody passed.
    ("tax-u64-bound-removed", "    if tax.lamports > U64_MAX:", "    if tax.lamports > 2**200:"),
    # instruction-order: the tax leg lands after the move, so the ticket leaves before the
    # payment is attempted.
    (
        "tax-leg-appended-after-the-move",
        "    return (*legs[:-1], transfer, legs[-1])",
        "    return (*legs, transfer)",
    ),
    # zero-tax-omits-the-leg: nothing is omitted, so the fee module's own transfer builder is
    # asked for a 0-lamport transfer and refuses it (its amount has `minimum=1`). That refusal is
    # what the property sees, which is why the comment here used to say "a 0-lamport transfer is
    # built" and was wrong: it is not built, it raises.
    (
        "zero-tax-omission-inverted",
        "    if tax.lamports == 0:\n        return legs",
        "    if tax.lamports < 0:\n        return legs",
    ),
    # one-lamport-is-a-payment: the omission rule is widened by one lamport, so a seller who owed
    # exactly one pays nothing and the sale looks identical to a zero-tax one.
    (
        "omission-widened-to-one-lamport",
        "    if tax.lamports == 0:\n        return legs",
        "    if tax.lamports <= 1:\n        return legs",
    ),
    # record-decode and layout-transcription: the clock is read one byte early, off the policy
    # byte.
    ("record-offset-changed-to-29", "HELD_SINCE_UNIX_OFFSET = 30", "HELD_SINCE_UNIX_OFFSET = 29"),
    # record-decode: the length check is gone, so a 38-byte v1 record plus rubbish is read as a
    # v2 record because the field happens to fit.
    ("record-length-check-removed", "    if len(raw) < RECORD_LEN:", "    if False:"),
    # policy-mapping and disabled-policy-refused: a block that does not name the toggle turns
    # the tax on.
    (
        "enabled-default-flipped-in-from-mapping",
        '        enabled = raw.get("enabled", False)',
        '        enabled = raw.get("enabled", True)',
    ),
    # policy-mapping: an omitted toggle is off at the dataclass too.
    (
        "enabled-default-flipped-on-the-policy",
        "    enabled: bool = False",
        "    enabled: bool = True",
    ),
    # policy-mapping: a block may name a second recipient for one event's money.
    (
        "default-wallet-mismatch-accepted",
        "            if default_wallet is not None and wallet != default_wallet:",
        "            if False:",
    ),
    # wallet-is-32-bytes: a 31-byte 'public key' reaches the wire and fails there as an opaque
    # error rather than here as a named field.
    ("wallet-length-check-removed", "    if len(raw) != _PUBKEY_LEN:", "    if False:"),
    # policy-mapping: one name is whitelisted instead of the field set, so any other typo is
    # accepted silently.
    (
        "policy-whitelist-widened",
        "        unknown = sorted(set(raw) - _POLICY_FIELDS)",
        '        unknown = sorted(set(raw) - {"rate"})',
    ),
    # layout-transcription: the transcription moves without the client, which is the drift this
    # check exists to catch.
    ("record-length-constant-shortened", "RECORD_LEN = 70", "RECORD_LEN = 38"),
    # constants-independent: the division uses the rate bound as the denominator. Invisible at
    # runtime while both are 10 000, which is why the property retunes the bound.
    (
        "denominator-swapped-for-the-rate-bound",
        "lamports=price * bps // BPS_DENOMINATOR",
        "lamports=price * bps // MAX_BPS",
    ),
)

#: The eighteen the build brief names. Named separately so deleting one from the table is a
#: failing test rather than a quietly shorter list.
REQUIRED_MUTATIONS = frozenset(
    {
        "max-rate-raised",
        "denominator-changed-to-1000",
        "ceiling-in-the-tax",
        "unknown-hold-priced-as-zero-seconds",
        "future-hold-not-clamped",
        "line-replaced-by-the-full-rate",
        "zero-point-read-as-exclusive",
        "full-hold-boundary-exclusive",
        "disabled-policy-refusal-removed",
        "artist-is-seller-refusal-removed",
        "price-check-removed",
        "tax-u64-bound-removed",
        "tax-leg-appended-after-the-move",
        "zero-tax-omission-inverted",
        "omission-widened-to-one-lamport",
        "record-offset-changed-to-29",
        "record-length-check-removed",
        "enabled-default-flipped-in-from-mapping",
        "default-wallet-mismatch-accepted",
    }
)


# -- the harness -------------------------------------------------------------


def failures(module) -> list[str]:
    """Every property the loaded module breaks, by property name and reason."""
    broken = []
    for name, property_function in PROPERTIES:
        try:
            property_function(module)
        except Exception as exc:  # noqa: BLE001 - any breakage counts against the mutant
            broken.append(f"{name} ({type(exc).__name__}: {exc})")
    return broken


def caught_by(module) -> list[str]:
    """The names of the properties a mutant breaks, for the report this file prints."""
    caught = []
    for name, property_function in PROPERTIES:
        try:
            property_function(module)
        except Exception:  # noqa: BLE001 - a broken property is a catch, whatever the reason
            caught.append(name)
    return caught


class MutationHarness(unittest.TestCase):
    """Loads temp copies of `flip_tax.py` and runs the property table against each."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._directory = tempfile.TemporaryDirectory(prefix="flip-tax-mutants-")
        cls.directory = Path(cls._directory.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._directory.cleanup()

    def load(self, text: str, label: str):
        """A module object from `text`, loaded from a file of its own.

        The copy imports `market_swarm.artist_fee` absolutely, so it resolves against the same
        package the real module does and no path has to be arranged for it. The module is
        registered in `sys.modules` for the duration of the load because `dataclasses` resolves a
        class's namespace through `sys.modules[cls.__module__]`, and a module object that is not
        registered there makes `@dataclass` raise before the mutation can be tested.
        """
        path = self.directory / f"{label}.py"
        path.write_text(text, encoding="utf-8")
        module_name = f"flip_tax_mutant_{label}"
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec is not None and spec.loader is not None, f"could not load {label}"
        module = importlib.util.module_from_spec(spec)
        saved_path = list(sys.path)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        finally:
            sys.modules.pop(module_name, None)
            sys.path[:] = saved_path
        return module

    def test_the_control_passes_the_same_properties(self) -> None:
        """The unmutated source passes. Without this, a table that raised on everything would
        look like a suite that caught every mutation."""
        broken = failures(self.load(SOURCE, "control"))
        self.assertEqual(broken, [], f"the property table rejects the real module: {broken}")

    def test_every_mutation_is_caught(self) -> None:
        """Each mutation must break at least one property, and one that does not is named."""
        inapplicable: list[str] = []
        survivors: list[str] = []
        for name, old, new in MUTATIONS:
            occurrences = SOURCE.count(old)
            if occurrences != 1:
                inapplicable.append(f"{name}: its source text appears {occurrences} times")
                continue
            module = self.load(SOURCE.replace(old, new, 1), name.replace("-", "_"))
            if not failures(module):
                survivors.append(name)
        self.assertEqual(inapplicable, [], f"stale mutations that no longer apply: {inapplicable}")
        self.assertEqual(
            survivors,
            [],
            f"these mutations survived, so the suite has a hole in it: {survivors}",
        )

    def test_the_table_covers_the_mutations_the_brief_names(self) -> None:
        missing = REQUIRED_MUTATIONS - {name for name, _, _ in MUTATIONS}
        self.assertEqual(
            missing, set(), f"the table dropped a required mutation: {sorted(missing)}"
        )

    def test_every_mutation_changes_something(self) -> None:
        for name, old, new in MUTATIONS:
            with self.subTest(mutation=name):
                self.assertNotEqual(old, new, f"{name} replaces text with itself")

    def test_the_tables_are_the_size_this_file_claims(self) -> None:
        """The count of what this suite proves, printed so a run says how much it covered, and
        floored so a shrunken table is a failing test rather than a quieter one."""
        print(
            f"\nflip_tax mutation suite: {len(MUTATIONS)} mutations against "
            f"{len(PROPERTIES)} properties"
        )
        self.assertGreaterEqual(len(MUTATIONS), len(REQUIRED_MUTATIONS))
        self.assertGreaterEqual(len(PROPERTIES), 18)

    def test_every_mutation_is_caught_by_a_named_property(self) -> None:
        """The claim in each comment, checked: the mutation is caught, and this is what caught
        it. A comment that named the wrong property would still pass
        `test_every_mutation_is_caught`, so the mapping is printed and asserted non-empty here."""
        report = []
        for name, old, new in MUTATIONS:
            with self.subTest(mutation=name):
                module = self.load(SOURCE.replace(old, new, 1), f"named_{name.replace('-', '_')}")
                caught = caught_by(module)
                self.assertNotEqual(caught, [], f"{name} was not caught by any property")
                report.append(f"{name}: {', '.join(caught)}")
        print("\n" + "\n".join(report))

    def test_a_change_that_breaks_nothing_is_reported_as_a_survivor(self) -> None:
        """The detection the harness turns on itself: a source edit no property sees is a
        survivor, which is exactly what `test_every_mutation_is_caught` fails on."""
        harmless = SOURCE.replace("#: The largest rate", "#: the largest rate", 1)
        self.assertNotEqual(harmless, SOURCE, "the behaviour-preserving control did not apply")
        self.assertEqual(failures(self.load(harmless, "harmless")), [])


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

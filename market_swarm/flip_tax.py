"""The flip tax: lamports the seller pays on a quick resale, on top of the artist fee.

**What it is.** A tax on flipping, not a rebate for hoarding: the rate falls the longer the
ticket was held, so selling an hour after buying costs more than selling a month later. The
default schedule is 15% of the sale price while the hold is under an hour, falling linearly to
0% at 30 days, and the schedule is per event. The money goes to the artist's wallet, which is
the same wallet `market_swarm/artist_fee.py` pays, and the two payments ride in one atomic
transaction with the price stage and the token move.

**Where the hold comes from.** `held_since_unix` in the 70-byte v2 `["record", mint]` account,
written by the hook itself on every admitted transfer (`programs/cap_hook/src/lib.rs` step 7,
`record.held_since_unix = Clock::get()?.unix_timestamp`). The checkout reads it before it builds
the sale, decodes the field at its byte offset, and prices the tax from the difference against
the clock. Nothing about the age is supplied by the seller, so the seller cannot claim a hold it
did not have; the one thing the seller can do is stage a price, and the tax is a fraction of
whatever they stage (finding 42 §5(3), the same limit the artist fee has).

**Three facts about that clock, each of which a screen or a README would otherwise get wrong.**

1. It is the record's, so it is the mint's: **one clock for every holder of an event**, not one
   per ticket account. It is the time of the last admitted transfer of *any* seat of that mint,
   so one holder's sale resets every other holder's clock, and the number is a seller's own hold
   only where one wallet holds the mint at a time. The design's mint carries `supply = 1`, which
   is that case; the harness runs one mint per event carrying the event's whole supply, so there
   it is the event's clock and not a seller's. A per-holder clock is a different account layout
   and is not built, and nothing in this module pretends the number is per holder.
2. `0` means **unknown**, not "held forever". The program writes 0 at `InitializeRecord` and
   only ever overwrites it with a real timestamp, and a v1 metas list (record read-only) leaves
   it at 0 for good. So 0 is charged the **full** rate: an unset field must not be the cheapest
   way to escape the tax, and this is the mirror image of the rebate, which refuses to *pay* on
   an unknown hold rather than guessing (`ClaimRebate`'s `6027`, documented and not built).
3. A clock that went backwards (a restarted ledger, a validator whose clock is not the one that
   wrote the field) clamps the hold to 0 seconds and therefore to the full rate. A disagreement
   about the time cannot buy a discount. The Rust clamps the same way, in `held_seconds`.

**What this does not do, and it is the same sentence as the artist fee's.** The tax binds only
sales this app builds. The hook has no instruction and no check that mentions lamports moving
between wallets: a transaction can stage a price, move the ticket and pay no tax, and the hook
admits it. What the chain does force, on a v2 record whose authority is the issuer, is that no
ticket moves without the issuer's signature on a stage, and that stage is what the checkout
prices. The stronger variant -- a hook that reads the instructions sysvar and requires a
matching transfer -- is documented and not built in `docs/ON-CHAIN-DESIGN.md` §15.4, for the
reasons stated there.

**Not built, and named so no reader assumes it.** A refund-to-holders pool: the tax could accrue
to holders who did not flip instead of only to the artist. It needs a pool account, a claim
instruction and a claim rule, and `programs/cap_hook` mentions `ClaimRebate` only in prose (the
instruction is absent from `lib.rs`, and the two error codes reserved for it are declared in
`error.rs` and raised by nothing), so building the seller-paid half here must not be mistaken for
building that half. The recipient is a config value, not a record field: the 70-byte record this
module decodes has no recipient in it, so a pool would be an account of its own -- a lamport
account owned by the `["rebate-pool", mint]` PDA, whose seeds exist in `state.rs` and that no
instruction creates -- which is a program change and another run's work.

Standard library only. No float, no network, no key: an address here is a public string. The one
import from this package is `market_swarm.artist_fee`, which is where the artist fee's arithmetic and
its System-transfer encoder live, and which puts `tools/` on `sys.path` for `devnet_publish`'s pure
encoders; the claim above is about the standard library, not about this module being importable
without the rest of the tree.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from market_swarm import artist_fee as af

#: The basis-point denominator. Separate from `artist_fee.FEE_BPS_DENOMINATOR` on purpose: the
#: artist fee and the flip tax are different rules, and retuning one must not move the other.
BPS_DENOMINATOR = 10_000

#: The largest rate any schedule may carry: 100% of the price. Above it a tax would exceed the
#: price it is taken from, which is not a tax, and the bound is what keeps `tax <= price` true
#: for every accepted schedule rather than the division happening to.
MAX_BPS = 10_000

#: The largest amount a System `Transfer` can carry: the amount is a `u64`.
U64_MAX = 2**64 - 1

#: The default schedule, and the operator's sentence: 15% under an hour, falling linearly to 0
#: at 30 days. Seconds, not days, because the clock the program writes is seconds.
DEFAULT_FULL_BPS = 1_500
DEFAULT_FULL_HOLD_SECONDS = 3_600          # one hour
DEFAULT_ZERO_HOLD_SECONDS = 2_592_000      # thirty days

#: The v2 `["record", mint]` account, and where the hook's clock sits inside it: face (8), cap
#: (2), pending price (8), status (1), band low (8), jurisdiction (2), policy (1) = byte 30, then
#: 8 signed bytes. Transcribed rather than imported so this package keeps no runtime dependency
#: on `ticketpath`; `market_swarm/tests/test_flip_tax.py` reads
#: `ticketpath/onchain/v2.py`'s `TICKET_RECORD_LAYOUT` and fails if the two disagree, which is
#: the check that makes the transcription safe.
RECORD_LEN = 70
HELD_SINCE_UNIX_OFFSET = 30
HELD_SINCE_UNIX_WIDTH = 8

#: `held_since_unix` at InitializeRecord, and the value a read-only v1 metas list leaves behind.
#: It means "this record's clock was never written", which is not a time and is not zero seconds.
UNKNOWN_HOLD = 0

#: A base58 public key decodes to 32 bytes and nothing else does.
_PUBKEY_LEN = 32

_POLICY_FIELDS = frozenset({"artist_wallet", "enabled", "schedule"})
_SCHEDULE_FIELDS = frozenset({"full_bps", "full_hold_seconds", "zero_hold_seconds"})

DEFAULT_SCHEDULE = None  # assigned below, after the class exists


class FlipTaxError(ValueError):
    """A schedule, a policy or a sale the checkout refuses to build. Names the field or rule."""


def _require_int(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    """An integer field, refusing bools (which are ints) and floats (which are money bugs)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise FlipTaxError(f"{field}: expected an integer, got {type(value).__name__}")
    if value < minimum:
        raise FlipTaxError(f"{field}: must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise FlipTaxError(f"{field}: must be at most {maximum}, got {value}")
    return value


def _require_bps(value: Any, field: str = "full_bps") -> int:
    """A rate in basis points: 0..`MAX_BPS` inclusive."""
    return _require_int(value, field, minimum=0, maximum=MAX_BPS)


def _require_wallet(value: Any, field: str = "artist_wallet") -> str:
    """A base58 string that decodes to exactly 32 bytes.

    The length is the check that matters: base58 will happily decode a typo, and a 31-byte
    "public key" reaches the wire and fails there as an opaque error rather than here as a
    named field. The check is `artist_fee`'s, restated so this module raises its own error type
    for its own fields; `test_flip_tax.py` pins the two against each other so they cannot drift.
    """
    if not isinstance(value, str):
        raise FlipTaxError(f"{field}: expected a base58 string, got {type(value).__name__}")
    try:
        raw = af.dp.base58.decode(value)
    except ValueError as exc:
        raise FlipTaxError(f"{field}: {value!r} is not base58: {exc}") from exc
    if len(raw) != _PUBKEY_LEN:
        raise FlipTaxError(f"{field}: {value!r} decodes to {len(raw)} bytes, expected 32")
    return value


@dataclass(frozen=True)
class FlipTaxSchedule:
    """How the rate falls with the hold: `full_bps` until `full_hold_seconds`, then linear to 0.

    Frozen because it is read on both sides of a transaction and a schedule that changed under a
    signing loop would make the tax leg and its row disagree.

    The curve is a straight line between `(full_hold_seconds, full_bps)` and
    `(zero_hold_seconds, 0)`, floored, in integers only. At exactly `full_hold_seconds` both
    readings of the operator's sentence -- "15% while under an hour" and "falling from an hour"
    -- give the same number, because the line starts there; the boundary is therefore not a
    choice this module makes. Below it the rate is flat, above it the rate only falls.
    """

    full_bps: int = DEFAULT_FULL_BPS
    full_hold_seconds: int = DEFAULT_FULL_HOLD_SECONDS
    zero_hold_seconds: int = DEFAULT_ZERO_HOLD_SECONDS

    def __post_init__(self) -> None:
        _require_bps(self.full_bps, "full_bps")
        _require_int(self.full_hold_seconds, "full_hold_seconds", minimum=0)
        _require_int(self.zero_hold_seconds, "zero_hold_seconds", minimum=1)
        if self.zero_hold_seconds <= self.full_hold_seconds:
            raise FlipTaxError(
                f"zero_hold_seconds: must be greater than full_hold_seconds "
                f"({self.full_hold_seconds}), got {self.zero_hold_seconds}. A curve that ends "
                "before it starts has no falling segment, so the division below would be by "
                "zero or by a negative span."
            )

    def bps_for(self, held_seconds: int) -> int:
        """`full_bps` under the full-hold point, 0 at and beyond the zero point, linear between.

        Floored, never rounded up: the rounding cost is a rate that reads 0 shortly before the
        stated zero point -- any hold in the last `(zero - full) / full_bps` seconds floors to 0,
        which with the defaults is the last 1 725 seconds, 28 minutes short of 30 days -- and the
        alternative, a ceiling, would charge a rate above the stated one, which is the defect that
        killed the token fee (finding 36 §2). The zero-point boundary itself is asserted at exactly
        0.
        """
        held = _require_int(held_seconds, "held_seconds", minimum=0)
        if held <= self.full_hold_seconds:
            return self.full_bps
        if held >= self.zero_hold_seconds:
            return 0
        span = self.zero_hold_seconds - self.full_hold_seconds
        return self.full_bps * (self.zero_hold_seconds - held) // span

    def to_dict(self) -> dict:
        """The mapping `from_mapping` accepts, so a schedule round-trips through a config."""
        return {
            "full_bps": self.full_bps,
            "full_hold_seconds": self.full_hold_seconds,
            "zero_hold_seconds": self.zero_hold_seconds,
        }

    @classmethod
    def from_mapping(cls, raw: Any, *, field: str = "flip_tax.schedule") -> "FlipTaxSchedule":
        """Parse `{"full_bps": int, "full_hold_seconds": int, "zero_hold_seconds": int}`.

        Every field is optional and defaults to the operator's schedule, so an event that only
        wants to change the rate writes `{"full_bps": 1000}` and keeps the two instants.
        """
        if not isinstance(raw, Mapping):
            raise FlipTaxError(f"{field}: expected an object, got {type(raw).__name__}")
        unknown = sorted(set(raw) - _SCHEDULE_FIELDS)
        if unknown:
            raise FlipTaxError(f"{field}: unknown field(s) {', '.join(unknown)}")
        defaults = cls()
        try:
            return cls(
                full_bps=_require_bps(raw.get("full_bps", defaults.full_bps), f"{field}.full_bps"),
                full_hold_seconds=_require_int(
                    raw.get("full_hold_seconds", defaults.full_hold_seconds),
                    f"{field}.full_hold_seconds",
                    minimum=0,
                ),
                zero_hold_seconds=_require_int(
                    raw.get("zero_hold_seconds", defaults.zero_hold_seconds),
                    f"{field}.zero_hold_seconds",
                    minimum=1,
                ),
            )
        except FlipTaxError as exc:
            # The three fields above are already validated with their full paths, so the only
            # refusal that can arrive from the constructor is the cross-field one, which has no
            # field of its own: it is given the block's path here rather than by the constructor,
            # because a schedule built by hand has no config path to name.
            raise FlipTaxError(f"{field}: {exc}") from exc


DEFAULT_SCHEDULE = FlipTaxSchedule()


@dataclass(frozen=True)
class FlipTaxPolicy:
    """One event's flip tax: whether it is on, who is paid, and how the rate falls with time.

    `enabled` defaults to **False** and the block is opt-in, so an event that does not name a
    flip tax is charged no tax and is otherwise identical to the event before this field
    existed. An event that names a block without `"enabled": true` carries a policy that is off
    rather than silently charging: the toggle is the event maker's, and a config that omits the
    toggle has not turned the tax on.

    `artist_wallet` is the recipient and is always resolved to a concrete address by the loader:
    the block may omit it and inherit the event's artist fee wallet, because the money goes to
    the artist, and an event with neither has nowhere to pay and is refused.
    """

    artist_wallet: str
    enabled: bool = False
    schedule: FlipTaxSchedule = DEFAULT_SCHEDULE

    def __post_init__(self) -> None:
        _require_wallet(self.artist_wallet)
        if not isinstance(self.enabled, bool):
            raise FlipTaxError(f"enabled: expected true or false, got {type(self.enabled).__name__}")
        if not isinstance(self.schedule, FlipTaxSchedule):
            raise FlipTaxError(
                f"schedule: expected a FlipTaxSchedule, got {type(self.schedule).__name__}"
            )

    @classmethod
    def from_mapping(
        cls,
        raw: Any,
        *,
        field: str = "flip_tax",
        default_wallet: str | None = None,
    ) -> "FlipTaxPolicy":
        """Parse one event's `flip_tax` block.

        `field` is the path the caller was given -- `"events[0].flip_tax"` -- and every refusal
        is reported under it, so a bad rate in a config with several events says which event.
        `default_wallet` is the event's artist fee wallet: an omitted `artist_wallet` inherits
        it, and a block that names a *different* wallet is refused rather than quietly redirecting
        the money, because the tax is the artist's and two destinations for one event is a
        decision the operator has not made.
        """
        if not isinstance(raw, Mapping):
            raise FlipTaxError(f"{field}: expected an object, got {type(raw).__name__}")
        unknown = sorted(set(raw) - _POLICY_FIELDS)
        if unknown:
            raise FlipTaxError(f"{field}: unknown field(s) {', '.join(unknown)}")

        enabled = raw.get("enabled", False)
        if not isinstance(enabled, bool):
            raise FlipTaxError(
                f"{field}.enabled: expected true or false, got {type(enabled).__name__}"
            )

        # An omitted wallet inherits the event's artist fee wallet; an explicit null is not an
        # omission. `raw.get` cannot tell the two apart, and a config that writes `"artist_wallet":
        # null` would otherwise be paid to a wallet it never named -- the same surprise as writing a
        # different one, so it is refused the same way rather than defaulted.
        if "artist_wallet" not in raw:
            if default_wallet is None:
                raise FlipTaxError(
                    f"{field}.artist_wallet: required when the event names no artist_fee. The "
                    "tax is paid to the artist and there is no other destination for it."
                )
            wallet = _require_wallet(default_wallet, field=f"{field}.artist_wallet")
        else:
            named = raw["artist_wallet"]
            if named is None:
                raise FlipTaxError(
                    f"{field}.artist_wallet: null is not a wallet. Omit the field to inherit the "
                    "event's artist fee wallet, or name the address the tax is paid to."
                )
            wallet = _require_wallet(named, field=f"{field}.artist_wallet")
            if default_wallet is not None and wallet != default_wallet:
                raise FlipTaxError(
                    f"{field}.artist_wallet: {wallet} is not the event's artist fee wallet "
                    f"{default_wallet}. The flip tax is paid to the artist, so one event has one "
                    "recipient; two would be a decision, not a default."
                )

        schedule_raw = raw.get("schedule")
        schedule = (
            DEFAULT_SCHEDULE
            if schedule_raw is None
            else FlipTaxSchedule.from_mapping(schedule_raw, field=f"{field}.schedule")
        )
        return cls(artist_wallet=wallet, enabled=enabled, schedule=schedule)

    def to_dict(self) -> dict:
        """The mapping `from_mapping` accepts, so a policy round-trips through a config."""
        return {
            "artist_wallet": self.artist_wallet,
            "enabled": self.enabled,
            "schedule": self.schedule.to_dict(),
        }


@dataclass(frozen=True)
class Assessment:
    """What the tax is on one sale, and the hold it was computed from.

    `held_seconds` is `None` when the record's clock was never written. It is kept beside the
    rate rather than discarded because it is the only number that explains the rate to a reader
    of the row, and because a dataset row that carries a rate and no age cannot be checked
    against any schedule.
    """

    held_seconds: int | None
    bps: int
    lamports: int

    @property
    def known(self) -> bool:
        """True when the hold came from the record's clock rather than from the unknown value."""
        return self.held_seconds is not None

    def to_dict(self) -> dict:
        return {"held_seconds": self.held_seconds, "bps": self.bps, "lamports": self.lamports}


def hold_seconds(held_since_unix: int, now_unix: int) -> int | None:
    """The age of the hold, or `None` when the record never had its clock written.

    `UNKNOWN_HOLD` is not a time and must not be read as 1970: `now - 0` is about 1.8 billion
    seconds, which would price every unknown hold at 0% and make an unset field the cheapest
    evasion in the system. A future `held_since_unix` (a clock that went backwards between the
    write and the read) clamps to 0 seconds, which is the full rate.
    """
    since = _require_int(held_since_unix, "held_since_unix", minimum=0)
    now = _require_int(now_unix, "now_unix", minimum=0)
    if since == UNKNOWN_HOLD:
        return None
    return max(0, now - since)


def combined_take_bps(*, artist_fee_bps: int, schedule: FlipTaxSchedule = DEFAULT_SCHEDULE) -> int:
    """What a quick resale costs the seller: the artist fee's rate plus the tax's full rate.

    The tax's *full* rate, not the rate at some hold, because this is the bound on what any sale
    can cost: the curve never rises above `full_bps`, so the sum is the worst case and the case a
    config has to be safe for. `> MAX_BPS` means the seller pays more than the whole price to sell,
    which is not a price a checkout may build.

    Two callers, and they are the two doors into a sale: `market_swarm/config.py` refuses such an
    event at load, and `market_swarm/gateway.py`'s `_check_spec` refuses a hand-built `EventSpec`
    that never went through a config file. It is one function so the two cannot disagree, which is
    exactly the hole a review found: with the rule only in the loader, a hand-built spec built a
    sale at 11 500 bps and the chain accepted it.
    """
    return _require_bps(artist_fee_bps, "artist_fee_bps") + schedule.full_bps


def held_since_unix_from_record(data: Any) -> int:
    """The hook's clock, read out of a v2 `["record", mint]` account.

    A short buffer is refused rather than padded: a record decoded past its end reads a field
    that is not the field, and this number decides a rate on money. The length is checked against
    `RECORD_LEN` and not against the field's own end, because a 38-byte buffer that happens to
    contain the field is a 19-byte v1 record plus rubbish, not a v2 record.
    """
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise FlipTaxError(f"record: expected bytes, got {type(data).__name__}")
    raw = bytes(data)
    if len(raw) < RECORD_LEN:
        raise FlipTaxError(
            f"record: {len(raw)} bytes arrived and a v2 record is {RECORD_LEN}; the hook's clock "
            f"is at byte {HELD_SINCE_UNIX_OFFSET} and cannot be read from a shorter account"
        )
    return int.from_bytes(
        raw[HELD_SINCE_UNIX_OFFSET : HELD_SINCE_UNIX_OFFSET + HELD_SINCE_UNIX_WIDTH],
        "little",
        signed=True,
    )


def assess(
    *,
    price_lamports: int,
    held_since_unix: int,
    now_unix: int,
    schedule: FlipTaxSchedule = DEFAULT_SCHEDULE,
) -> Assessment:
    """`(held_seconds, bps, lamports)` for one sale: the whole arithmetic, in one place.

    `lamports = price * bps // 10_000`, floored, integers only, exactly like the artist fee and
    for the same reason (finding 42 §3): floor never charges more than the stated rate, and its
    cost is rounding to zero. `unknown` (a record whose clock was never written) is the full
    rate, and its `held_seconds` stays `None` so the row says why.
    """
    if not isinstance(schedule, FlipTaxSchedule):
        raise FlipTaxError(f"schedule: expected a FlipTaxSchedule, got {type(schedule).__name__}")
    price = _require_int(price_lamports, "price_lamports", minimum=0)
    held = hold_seconds(held_since_unix, now_unix)
    bps = schedule.full_bps if held is None else schedule.bps_for(held)
    return Assessment(held_seconds=held, bps=bps, lamports=price * bps // BPS_DENOMINATOR)


def sale_instructions(
    *,
    stage: Any,
    move: Any,
    seller: str,
    policy: FlipTaxPolicy,
    price_lamports: int,
    held_since_unix: int,
    now_unix: int,
    artist_fee: Any = None,
) -> tuple[Any, ...]:
    """`(stage, artist_fee?, flip_tax?, move)`: the whole sale, in one transaction.

    The tax leg goes last before the move, so the two payments sit between the two instructions
    they belong to: the stage that authorises the price, and the move the hook checks. Every leg
    shares one blockhash and one signature set, so a leg that fails fails the sale and rolls the
    two legs before it back.

    The artist-fee half, when the event has one, is built by
    `market_swarm.artist_fee.sale_instructions` rather than here: the fee arithmetic, the
    omission of a zero fee and its refusals stay in the module that owns them, and this function
    only decides whether a tax leg is inserted. Zero tax means no leg at all, for the same reason
    a zero fee means no leg: a 0-lamport `System` transfer is a payment of nothing and is
    indistinguishable in a signature from one that was meant and paid zero.

    Refusals, each naming its rule:

    - a disabled policy. The toggle is the event maker's and the default is off, so a disabled
      policy reaching a builder is a caller that skipped the toggle, not a sale to be built;
    - an artist wallet equal to the seller: the seller would pay themselves, which pays no tax
      and would be logged as one;
    - a tax that does not fit the `u64` a System transfer carries, reachable only from a price
      above `2**64 - 1`;
    - a price of 0 or less. The chain reads a staged 0 as "nothing staged" and refuses the move
      with 6009, so the sale this would build can only fail.
    """
    if not isinstance(policy, FlipTaxPolicy):
        raise FlipTaxError(f"policy: expected a FlipTaxPolicy, got {type(policy).__name__}")
    if not policy.enabled:
        raise FlipTaxError(
            "enabled: this policy is off. The flip tax is off by default and an event turns it "
            "on; a builder asked to charge a disabled policy is a caller that skipped the toggle."
        )
    price = _require_int(price_lamports, "price_lamports")
    if price <= 0:
        raise FlipTaxError(
            f"price_lamports: expected a positive price, got {price}. The chain reads a staged 0 "
            "as 'nothing staged' and refuses the move with 6009 (E_TRANSFER_NOT_STAGED)."
        )
    seller_address = _require_wallet(seller, field="seller")
    if policy.artist_wallet == seller_address:
        raise FlipTaxError(
            "artist_wallet: the artist is the seller, so the flip tax would pay the seller and "
            "the sale would record a tax that moved nothing"
        )

    # The legs the artist fee owns, if this event has one. `artist_fee` is a policy object or
    # None; anything else is a caller that did not parse its config.
    if artist_fee is None:
        legs: tuple = (stage, move)
    else:
        if not isinstance(artist_fee, af.ArtistFeePolicy):
            raise FlipTaxError(
                f"artist_fee: expected an ArtistFeePolicy or None, got {type(artist_fee).__name__}"
            )
        legs = af.sale_instructions(
            stage=stage,
            move=move,
            seller=seller_address,
            artist_wallet=artist_fee.artist_wallet,
            price_lamports=price,
            fee_bps=artist_fee.fee_bps,
        )

    tax = assess(
        price_lamports=price,
        held_since_unix=held_since_unix,
        now_unix=now_unix,
        schedule=policy.schedule,
    )
    if tax.lamports == 0:
        return legs
    if tax.lamports > U64_MAX:
        raise FlipTaxError(
            f"flip_tax_lamports: {tax.lamports} does not fit the u64 a System transfer carries"
        )
    transfer = af.system_transfer_instruction(
        source=seller_address, destination=policy.artist_wallet, lamports=tax.lamports
    )
    # Before the move, after everything already built: `legs` ends with the move by construction.
    return (*legs[:-1], transfer, legs[-1])

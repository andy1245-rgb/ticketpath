"""The artist fee: lamports the seller pays, in the same transaction as the move.

**Why not a Token-2022 transfer fee.** Measured, not argued, in
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md` §0-2: at `decimals = 0` an
`amount = 1` transfer **ceils** the fee, so every rate in 1..9999 bps withholds the whole
ticket and pays the buyer nothing. A token fee is a fraction of a token, and this mint's
tokens are indivisible. A fee in lamports is a fraction of a *price*, which is what "5% of
the resale" means.

**Why floor, and not ceiling.** `fee_lamports` divides with `//` and never with `/`, because
lamports are integers and a float would put a rounding error into a money value. The
rounding is floor because a ceiling takes a whole lamport on a 1-lamport sale, 100% of it:
that is the same defect that killed the token fee, one unit lower down. Floor never charges
more than the stated percentage, and the price of that is rounding to zero — 19 lamports at
500 bps is a fee of 0. When the fee is 0 no System transfer is built at all, rather than a
0-lamport one: a transfer of nothing is not a payment, and it would put an instruction in the
transaction that a reader could not tell from a fee that was meant and failed to move.
Whether the runtime accepts a 0-lamport System `Transfer` was not measured here, so nothing
depends on either answer.

**The sale, and which part of it is here.** One atomic transaction holds: stage the price
(`cap_hook` `SetPendingPrice`), seller pays the artist, token moves (Token-2022
`TransferChecked`). `sale_instructions` returns those three in that order and builds only
the middle one: the stage comes from the cap hook and the move from Token-2022, so both are
handed in. The order is the reason the fee is here and not in a frontend: the fee instruction
sits between the two legs it belongs to, and the whole transaction fails if any leg does.

**What this binds, and what it does not.** The fee binds only sales this code builds. The
chain does not force it: a transaction can stage a price, move the ticket and pay the artist
nothing, and the hook admits it. What the chain does force, on a record whose authority is
the issuer, is that no ticket moves without the issuer's signature on the stage instruction.

Standard library only. No float, no network, no key: an address here is a public string.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

# `tools/` has no `__init__.py`, so it becomes importable only once it is on `sys.path` — the
# same block `market_swarm/gateway.py` uses, for the same reason. Importing `devnet_publish`
# reaches no cluster, no key and no file: it is two path computations, imports and constants.
REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import devnet_publish as dp  # noqa: E402

#: The basis-point denominator. `market_swarm/config.py` has the same 10_000 for the cap, and
#: it is deliberately a separate constant: the cap and the fee are different rules, and one
#: being retuned must not silently move the other.
FEE_BPS_DENOMINATOR = 10_000

#: The largest rate a policy may carry: 100% of the price. Above it the fee would exceed the
#: price, which is not a fee, so the bound is what keeps `fee <= price` true for every
#: accepted input rather than the division happening to.
MAX_FEE_BPS = 10_000

#: The largest amount a System `Transfer` can carry: the amount is a `u64`.
U64_MAX = 2**64 - 1

#: Bincode variant index 2 is `Transfer`, then a u64 of lamports. 12 bytes, unlike the
#: Borsh the program itself uses.
SYSTEM_TAG_TRANSFER = 2
SYSTEM_TRANSFER_LEN = 12

#: A base58 public key decodes to 32 bytes and nothing else does.
_PUBKEY_LEN = 32

_POLICY_FIELDS = frozenset({"artist_wallet", "fee_bps"})


class ArtistFeeError(ValueError):
    """A fee policy or a sale the checkout refuses to build. Names the field or the rule."""


def _require_int(value: Any, field: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    """An integer field, refusing bools (which are ints) and floats (which are money bugs)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise ArtistFeeError(f"{field}: expected an integer, got {type(value).__name__}")
    if value < minimum:
        raise ArtistFeeError(f"{field}: must be at least {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ArtistFeeError(f"{field}: must be at most {maximum}, got {value}")
    return value


def _require_bps(value: Any, field: str = "fee_bps") -> int:
    """A rate in basis points: 0..`MAX_FEE_BPS` inclusive."""
    return _require_int(value, field, minimum=0, maximum=MAX_FEE_BPS)


def _require_wallet(value: Any, field: str = "artist_wallet") -> str:
    """A base58 string that decodes to exactly 32 bytes.

    The length is the check that matters: base58 will happily decode a typo, and a 31-byte
    "public key" reaches the wire and fails there as an opaque error rather than here as a
    named field.
    """
    if not isinstance(value, str):
        raise ArtistFeeError(f"{field}: expected a base58 string, got {type(value).__name__}")
    try:
        raw = dp.base58.decode(value)
    except ValueError as exc:
        raise ArtistFeeError(f"{field}: {value!r} is not base58: {exc}") from exc
    if len(raw) != _PUBKEY_LEN:
        raise ArtistFeeError(f"{field}: {value!r} decodes to {len(raw)} bytes, expected 32")
    return value


@dataclass(frozen=True)
class ArtistFeePolicy:
    """The fee for one event: who is paid, and what fraction of the resale.

    Frozen because it is read on both sides of a transaction and a rate that changed under
    a signing loop would make the fee leg and its log disagree.
    """

    artist_wallet: str
    fee_bps: int

    def __post_init__(self) -> None:
        _require_wallet(self.artist_wallet)
        _require_bps(self.fee_bps)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, field: str = "artist_fee") -> "ArtistFeePolicy":
        """Parse `{"artist_wallet": str, "fee_bps": int}` from a config block.

        `field` is the path the caller was given — `"events[0].artist_fee"` — and every
        refusal is reported under it, so a bad rate in a config with several events says
        which event rather than only which key.
        """
        if not isinstance(raw, Mapping):
            raise ArtistFeeError(f"{field}: expected an object, got {type(raw).__name__}")
        unknown = sorted(set(raw) - _POLICY_FIELDS)
        if unknown:
            raise ArtistFeeError(f"{field}: unknown field(s) {', '.join(unknown)}")
        missing = sorted(_POLICY_FIELDS - set(raw))
        if missing:
            raise ArtistFeeError(f"{field}.{missing[0]}: required field is missing")
        wallet = _require_wallet(raw["artist_wallet"], field=f"{field}.artist_wallet")
        bps = _require_bps(raw["fee_bps"], field=f"{field}.fee_bps")
        return cls(artist_wallet=wallet, fee_bps=bps)

    def to_dict(self) -> dict:
        """The mapping `from_mapping` accepts, so a policy round-trips through a config."""
        return {"artist_wallet": self.artist_wallet, "fee_bps": self.fee_bps}


def fee_lamports(*, price_lamports: int, fee_bps: int) -> int:
    """`price * bps // 10_000`: the fee on one resale, floored, exact.

    0 at price 0 and at 0 bps, and never more than the price for any rate this function
    accepts — `MAX_FEE_BPS` is what makes that a bound on the accepted input rather than an
    accident of the arithmetic. The result is an `int` and not a `float` even at 100% of a
    1-lamport sale.
    """
    price = _require_int(price_lamports, "price_lamports", minimum=0)
    bps = _require_bps(fee_bps)
    return price * bps // FEE_BPS_DENOMINATOR


def system_transfer_instruction(*, source: str, destination: str, lamports: int) -> dp.Instruction:
    """A System Program `Transfer`: the fee leg, and the only instruction here that is built.

    Bincode rather than Borsh: a u32 little-endian variant index (2 is `Transfer`) and a u64
    little-endian amount, 12 bytes in total. Accounts are `[source, destination]`, the source
    the only signer and both writable. Byte-identical to
    `market_swarm.gateway.system_transfer_instruction`; a test pins the two against each
    other so the fee leg and the funding leg cannot drift, and this module does not import
    the gateway because the gateway imports this.
    """
    amount = _require_int(lamports, "lamports", minimum=1, maximum=U64_MAX)
    data = SYSTEM_TAG_TRANSFER.to_bytes(4, "little") + amount.to_bytes(8, "little")
    assert len(data) == SYSTEM_TRANSFER_LEN, "bincode: a u32 variant index then a u64 amount"
    return dp.Instruction(
        program_id=dp.SYSTEM_PROGRAM,
        accounts=(dp.AccountMeta(source, True, True), dp.AccountMeta(destination, False, True)),
        data=data,
    )


def sale_instructions(
    *,
    stage: dp.Instruction,
    move: dp.Instruction,
    seller: str,
    artist_wallet: str,
    price_lamports: int,
    fee_bps: int,
) -> tuple[dp.Instruction, ...]:
    """`(stage, fee_transfer?, move)`: the sale in one transaction, fee omitted when it is 0.

    The two instructions this module does not own are passed in, so the caller decides what
    stages the price and what moves the token and this function decides only whether a payment
    sits between them. Three instructions when the fee is positive, two when it is zero: a
    0-lamport transfer is not built, because a payment of nothing is indistinguishable in a
    signature from a fee that was meant and paid zero.

    Refusals, each naming its rule:

    - a price of 0 or less. The chain reads a staged 0 as "nothing staged" and refuses the
      move with 6009, so the sale this would build can only fail, and the checkout says why
      before a blockhash is fetched;
    - an artist wallet equal to the seller: the seller would pay themselves, which pays no
      fee and would be logged as one;
    - a fee that does not fit the `u64` a System transfer carries, reachable only from a price
      above `2**64 - 1`. It is refused here rather than left to `system_transfer_instruction` so
      the error names the fee the caller asked for and not an amount it never passed;
    - a rate above 10 000 bps, or a wallet that is not 32 bytes of base58, both reported by
      `ArtistFeePolicy`.
    """
    price = _require_int(price_lamports, "price_lamports")
    if price <= 0:
        raise ArtistFeeError(
            f"price_lamports: expected a positive price, got {price}. The chain reads a staged "
            "0 as 'nothing staged' and refuses the move with 6009 (E_TRANSFER_NOT_STAGED)."
        )
    policy = ArtistFeePolicy(artist_wallet=artist_wallet, fee_bps=fee_bps)
    if policy.artist_wallet == seller:
        raise ArtistFeeError(
            "artist_wallet: the artist is the seller, so the fee transfer would pay the seller "
            "and the sale would record a fee that moved nothing"
        )
    fee = fee_lamports(price_lamports=price, fee_bps=policy.fee_bps)
    if fee > U64_MAX:
        raise ArtistFeeError(f"fee_lamports: {fee} does not fit the u64 a System transfer carries")
    if fee == 0:
        return (stage, move)
    transfer = system_transfer_instruction(
        source=seller, destination=policy.artist_wallet, lamports=fee
    )
    return (stage, transfer, move)

"""`cap_hook` v2 on the wire: instruction data, account layouts, and PDA seeds.

This module is the client half of `programs/cap_hook/src/state.rs`. The Rust side owns the
predicates and the storage; this side owns the bytes a client has to produce and read, and
nothing else: no network, no RPC, no key material, standard library only.

Three things live here, and they are all of it:

* **Instruction data for tags 0..6.** Each builder returns the exact `Vec<u8>` the program's
  `HookInstruction::unpack` accepts, and `parse_instruction` reads it back. The round trip is
  what the tests lean on, because a builder that emits 21 argument bytes and a parser that
  reads 22 agree with nobody.
* **Account decoders.** `TicketRecord` (70 bytes), `Band` (102), `Forecast` (165), `Score`
  (58). Borsh, little-endian, no discriminator, no length prefix. A decoder refuses a short
  buffer; it never zero-pads a field it did not receive, because a decoded record is used to
  decide whether a transfer is worth attempting.
* **PDA seeds and derivation.** `["record", mint]`, `["extra-account-metas", mint]`,
  `["band", mint]`, `["forecast", mint, as_of_unix_le]`, `["score", forecast]`,
  `["fee-authority", mint]`, `["rebate-pool", mint]`, derived the way the runtime derives
  them. `find_program_address` hashes and then tests the digest against the ed25519 curve,
  which is the step a client cannot skip: a client that stops at the first digest hands out an
  address the program will never own.

Where the numbers come from, and why they are not invented here: `state.rs` is the layout and
`lib.rs` is the wire format. `tests/test_onchain_v2.py` reads both Rust sources and compares
them with the constants below, so a field added on one side without the other is a failing
test rather than two implementations that drift quietly. The same test pins the offsets as
literal byte positions, which is the form a client codes against.

The one measurement this module cannot make is whether the program writes what it says it
writes. That is `tools/publish_v2.py` and `tests/test_onchain_v2_live.py`, on a local
validator, with a real Token-2022 transfer.
"""

from __future__ import annotations

import hashlib

from ticketpath.core import base58

# -- instruction tags --------------------------------------------------------
#
# `lib.rs` reserves 0..=6 for this program's own instructions and routes anything else to the
# SPL transfer-hook discriminator, whose first byte is 105 (`TransferHookInstruction::Execute`
# starts with `spl_discriminator!` = [105]). Tag 7 (ClaimRebate, MD4) is not implemented in
# lib.rs and is deliberately absent here too: a builder for an instruction the program refuses
# is a client that cannot work.
#
# The two limits the program enforces and a client has to know about, stated here so a caller
# can read them without opening the Rust:
#
# * `FORECAST_BACKDATE_TOLERANCE_SECONDS` (lib.rs): `LogForecast` refuses an `as_of_unix`
#   earlier than the validator's clock minus this many seconds, with `6029`. The builder does
#   **not** check it: the refusal has to be observable on chain, the same reason `policy` is
#   not checked (6023). A caller that wants to log an old instant has to hear it from the chain.
# * `MAX_BAND_WIDTH_LAMPORTS` (state.rs): `LogForecast` refuses a band wider than this with
#   `6031`, because the width term of the score (`width * 1_000_000`) would not fit the `u64`
#   the score field is, so the forecast could never be scored. 18_446_744_073_709 lamports is
#   about 18,446.7 SOL.

FORECAST_BACKDATE_TOLERANCE_SECONDS = 300
MAX_BAND_WIDTH_LAMPORTS = (2**64 - 1) // 1_000_000
SCORE_MICRO_SCALE = 1_000_000

TAG_INITIALIZE_EXTRA_ACCOUNT_META_LIST = 0
TAG_INITIALIZE_RECORD = 1
TAG_SET_PENDING_PRICE = 2
TAG_SET_STATUS = 3
TAG_PUBLISH_BAND = 4
TAG_LOG_FORECAST = 5
TAG_SCORE_FORECAST = 6

TAGS = (
    TAG_INITIALIZE_EXTRA_ACCOUNT_META_LIST,
    TAG_INITIALIZE_RECORD,
    TAG_SET_PENDING_PRICE,
    TAG_SET_STATUS,
    TAG_PUBLISH_BAND,
    TAG_LOG_FORECAST,
    TAG_SCORE_FORECAST,
)

# -- the one exception -------------------------------------------------------


class ShortBuffer(ValueError):
    """Fewer bytes arrived than the layout needs. Never padded, never guessed."""


# -- layouts -----------------------------------------------------------------
#
# One tuple per structure: (field name, byte offset, width, kind). `kind` is what the field
# means when a decoder turns it into a Python value; the offsets are the contract. Written out
# by hand rather than accumulated from the widths, because a decoder reads offsets and an
# accumulated list would agree with itself even if both were wrong.

INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD = ()
"""Tag 0's payload after the tag: nothing. The record it names is derived from the mint."""

INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD_LEN = 0
INITIALIZE_EXTRA_ACCOUNT_META_LIST_DATA_LEN = 1

INITIALIZE_RECORD_LAYOUT = (
    ("face_value_lamports", 0, 8, "u64"),
    ("cap_bps", 8, 2, "u16"),
    ("band_low_lamports", 10, 8, "u64"),
    ("jurisdiction", 18, 2, "raw"),
    ("policy", 20, 1, "u8"),
)
"""Tag 1's payload after the tag: 21 bytes, so the instruction data is 22."""

INITIALIZE_RECORD_PAYLOAD_LEN = 21
INITIALIZE_RECORD_DATA_LEN = 1 + INITIALIZE_RECORD_PAYLOAD_LEN

PUBLISH_BAND_LAYOUT = (
    ("low", 0, 8, "u64"),
    ("high", 8, 8, "u64"),
    ("as_of_slot", 16, 8, "u64"),
    ("sample_n", 24, 4, "u32"),
    ("refused", 28, 1, "u8"),
    ("model_hash", 29, 32, "hash"),
)
"""Tag 4's payload after the tag: 61 bytes, so the instruction data is 62."""

PUBLISH_BAND_PAYLOAD_LEN = 61
PUBLISH_BAND_DATA_LEN = 1 + PUBLISH_BAND_PAYLOAD_LEN

LOG_FORECAST_LAYOUT = (
    ("low", 0, 8, "u64"),
    ("high", 8, 8, "u64"),
    ("as_of_unix", 16, 8, "i64"),
    ("sample_n", 24, 4, "u32"),
    ("model_hash", 28, 32, "hash"),
    ("scoring_rule_hash", 60, 32, "hash"),
)
"""Tag 5's payload after the tag: 92 bytes, so the instruction data is 93."""

LOG_FORECAST_PAYLOAD_LEN = 92
LOG_FORECAST_DATA_LEN = 1 + LOG_FORECAST_PAYLOAD_LEN

SCORE_FORECAST_LAYOUT = (
    ("realised_lamports", 0, 8, "u64"),
    ("interval_score_micro", 8, 8, "u64"),
)
"""Tag 6's payload after the tag: 16 bytes, so the instruction data is 17."""

SCORE_FORECAST_PAYLOAD_LEN = 16
SCORE_FORECAST_DATA_LEN = 1 + SCORE_FORECAST_PAYLOAD_LEN

TICKET_RECORD_LAYOUT = (
    ("face_value_lamports", 0, 8, "u64"),
    ("cap_bps", 8, 2, "u16"),
    ("pending_price_lamports", 10, 8, "u64"),
    ("status", 18, 1, "u8"),
    ("band_low_lamports", 19, 8, "u64"),
    ("jurisdiction", 27, 2, "raw"),
    ("policy", 29, 1, "u8"),
    ("held_since_unix", 30, 8, "i64"),
    ("authority", 38, 32, "pubkey"),
)

BAND_LAYOUT = (
    ("version", 0, 1, "u8"),
    ("low", 1, 8, "u64"),
    ("high", 9, 8, "u64"),
    ("as_of_slot", 17, 8, "u64"),
    ("published_slot", 25, 8, "u64"),
    ("sample_n", 33, 4, "u32"),
    ("refused", 37, 1, "u8"),
    ("model_hash", 38, 32, "hash"),
    ("authority", 70, 32, "pubkey"),
)

FORECAST_LAYOUT = (
    ("version", 0, 1, "u8"),
    ("mint", 1, 32, "pubkey"),
    ("low", 33, 8, "u64"),
    ("high", 41, 8, "u64"),
    ("as_of_unix", 49, 8, "i64"),
    ("sample_n", 57, 4, "u32"),
    ("model_hash", 61, 32, "hash"),
    ("scoring_rule_hash", 93, 32, "hash"),
    ("created_slot", 125, 8, "u64"),
    ("authority", 133, 32, "pubkey"),
)

SCORE_LAYOUT = (
    ("version", 0, 1, "u8"),
    ("realised_lamports", 1, 8, "u64"),
    ("interval_score_micro", 9, 8, "u64"),
    ("covered", 17, 1, "u8"),
    ("scored_slot", 18, 8, "u64"),
    ("scorer", 26, 32, "pubkey"),
)

_INT_WIDTHS = {"u8": 1, "u16": 2, "u32": 4, "u64": 8, "i64": 8}


def _span(layout: tuple) -> int:
    """The number of bytes a layout occupies, and the check that it has no gap or overlap."""
    end = 0
    for _name, offset, width, _kind in layout:
        if offset != end:
            raise AssertionError(f"layout is not contiguous at byte {offset}: expected {end}")
        if _kind in _INT_WIDTHS and _INT_WIDTHS[_kind] != width:
            raise AssertionError(f"{_kind} is {_INT_WIDTHS[_kind]} bytes, not {width}")
        end = offset + width
    return end


# -- value readers -----------------------------------------------------------


def _require(data, length: int, what: str) -> None:
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise TypeError(f"{what}: expected bytes, got {type(data).__name__}")
    if len(data) < length:
        raise ShortBuffer(f"{what}: {length} bytes are needed and {len(data)} arrived")


def _read(data, offset: int, width: int, kind: str):
    raw = bytes(data[offset : offset + width])
    if kind in _INT_WIDTHS:
        return int.from_bytes(raw, "little", signed=(kind == "i64"))
    if kind == "pubkey":
        return raw
    if kind == "hash":
        return raw
    if kind == "raw":
        return raw
    raise AssertionError(f"unknown field kind {kind!r}")


def _written(value, width: int, kind: str) -> bytes:
    """One field, little-endian, refusing a value that would not survive the round trip."""
    if kind in _INT_WIDTHS:
        if not isinstance(value, int) or isinstance(value, bool):
            raise TypeError(f"{kind} field needs an int, got {type(value).__name__}")
        low, high = (0, 2 ** (8 * width) - 1) if kind != "i64" else (-(2 ** 63), 2 ** 63 - 1)
        if not low <= value <= high:
            raise ValueError(f"{value} does not fit in {kind}")
        return value.to_bytes(width, "little", signed=(kind == "i64"))
    raw = _as_bytes(value, width, kind)
    return raw


def _as_bytes(value, width: int, what: str) -> bytes:
    if isinstance(value, str):
        raw = base58.decode(value)
    elif isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
    else:
        raise TypeError(f"{what}: expected base58 text or bytes, got {type(value).__name__}")
    if len(raw) != width:
        raise ValueError(f"{what}: expected {width} bytes, got {len(raw)}")
    return raw


def _text(raw) -> str:
    """Two bytes as text, or `??` when they are not ASCII: what the program logs."""
    try:
        return bytes(raw).decode("ascii")
    except UnicodeDecodeError:
        return "??"


def _pack(layout: tuple, values: dict) -> bytes:
    out = bytearray(_span(layout))
    for name, offset, width, kind in layout:
        if name not in values:
            raise TypeError(f"missing field {name}")
        out[offset : offset + width] = _written(values[name], width, kind)
    extra = set(values) - {name for name, *_ in layout}
    if extra:
        raise TypeError(f"unknown fields: {sorted(extra)}")
    return bytes(out)


def _unpack(layout: tuple, data, what: str) -> dict:
    _require(data, _span(layout), what)
    return {name: _read(data, offset, width, kind) for name, offset, width, kind in layout}


# -- decoded accounts --------------------------------------------------------


class _Account:
    """Equality and printing over the declared layout; nothing else is shared."""

    __slots__ = ()
    LAYOUT: tuple = ()
    LEN: int = 0
    TEXT: frozenset = frozenset()

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name) for name, *_ in self.LAYOUT)

    def __repr__(self) -> str:
        fields = ", ".join(f"{name}={getattr(self, name)!r}" for name, *_ in self.LAYOUT)
        return f"{type(self).__name__}({fields})"

    def as_dict(self) -> dict:
        """A JSON-ready view: every byte field as base58, the jurisdiction as text."""
        out = {}
        for name, _offset, _width, _kind in self.LAYOUT:
            value = getattr(self, name)
            if name in self.TEXT:
                out[name] = _text(value)
            elif isinstance(value, (bytes, bytearray)):
                out[name] = base58.encode(value)
            else:
                out[name] = value
        return out

    @classmethod
    def decode(cls, data):
        """Decode the first `cls.LEN` bytes. Trailing bytes are ignored, never read."""
        fields = _unpack(cls.LAYOUT, data, cls.__name__)
        return cls(**fields)


class TicketRecord(_Account):
    """`["record", mint]`, 70 bytes. Field order is `state.rs::TicketRecord`."""

    __slots__ = tuple(name for name, *_ in TICKET_RECORD_LAYOUT)
    LAYOUT = TICKET_RECORD_LAYOUT
    LEN = 70
    TEXT = frozenset({"jurisdiction"})

    def __init__(self, *, face_value_lamports, cap_bps, pending_price_lamports, status,
                 band_low_lamports, jurisdiction, policy, held_since_unix, authority):
        self.face_value_lamports = face_value_lamports
        self.cap_bps = cap_bps
        self.pending_price_lamports = pending_price_lamports
        self.status = status
        self.band_low_lamports = band_low_lamports
        self.jurisdiction = _jurisdiction_bytes(jurisdiction)
        self.policy = policy
        self.held_since_unix = held_since_unix
        self.authority = _as_bytes(authority, 32, "authority")

    @property
    def jurisdiction_text(self) -> str:
        """The two bytes as text, or `??` when they are not ASCII, matching the program's log."""
        return _text(self.jurisdiction)


class Band(_Account):
    """`["band", mint]`, 102 bytes: the public price feed's head, rewritten by `PublishBand`."""

    __slots__ = tuple(name for name, *_ in BAND_LAYOUT)
    LAYOUT = BAND_LAYOUT
    LEN = 102

    def __init__(self, *, version, low, high, as_of_slot, published_slot, sample_n,
                 refused, model_hash, authority):
        self.version = version
        self.low = low
        self.high = high
        self.as_of_slot = as_of_slot
        self.published_slot = published_slot
        self.sample_n = sample_n
        self.refused = refused
        self.model_hash = bytes(model_hash)
        self.authority = _as_bytes(authority, 32, "authority")


class Forecast(_Account):
    """`["forecast", mint, as_of_unix_le]`, 165 bytes. Create-once, written by `LogForecast`."""

    __slots__ = tuple(name for name, *_ in FORECAST_LAYOUT)
    LAYOUT = FORECAST_LAYOUT
    LEN = 165

    def __init__(self, *, version, mint, low, high, as_of_unix, sample_n, model_hash,
                 scoring_rule_hash, created_slot, authority):
        self.version = version
        self.mint = _as_bytes(mint, 32, "mint")
        self.low = low
        self.high = high
        self.as_of_unix = as_of_unix
        self.sample_n = sample_n
        self.model_hash = bytes(model_hash)
        self.scoring_rule_hash = bytes(scoring_rule_hash)
        self.created_slot = created_slot
        self.authority = _as_bytes(authority, 32, "authority")


class Score(_Account):
    """`["score", forecast]`, 58 bytes. Create-once, written by `ScoreForecast`."""

    __slots__ = tuple(name for name, *_ in SCORE_LAYOUT)
    LAYOUT = SCORE_LAYOUT
    LEN = 58

    def __init__(self, *, version, realised_lamports, interval_score_micro, covered,
                 scored_slot, scorer):
        self.version = version
        self.realised_lamports = realised_lamports
        self.interval_score_micro = interval_score_micro
        self.covered = covered
        self.scored_slot = scored_slot
        self.scorer = _as_bytes(scorer, 32, "scorer")


def decode_ticket_record(data) -> TicketRecord:
    """Decode a `["record", mint]` account. Raises `ShortBuffer` below 70 bytes."""
    return TicketRecord.decode(data)


def decode_band(data) -> Band:
    """Decode a `["band", mint]` account. Raises `ShortBuffer` below 102 bytes."""
    return Band.decode(data)


def decode_forecast(data) -> Forecast:
    """Decode a `["forecast", mint, as_of_unix_le]` account. Raises `ShortBuffer` below 165."""
    return Forecast.decode(data)


def decode_score(data) -> Score:
    """Decode a `["score", forecast]` account. Raises `ShortBuffer` below 58 bytes."""
    return Score.decode(data)


# -- the mint, read for the one thing tag 1 checks ---------------------------

MINT_BASE_LEN = 82
"""The base `Mint` account: `COption<Pubkey>` authority (36), supply (8), decimals (1),
`is_initialized` (1), `COption<Pubkey>` freeze authority (36). Token-2022 appends its extensions
*after* these 82 bytes, so this layout is the whole contract `initialize_record` reads."""


def mint_authority(data):
    """The mint's authority as 32 bytes, or `None` when the mint has none.

    `COption<Pubkey>` is a 4-byte little-endian tag (0 = none, 1 = present) and then the key. The
    program requires this key to sign `InitializeRecord` and refuses 6026 otherwise, so a client
    that wants to know who can create a record for a mint reads it here rather than guessing.
    A buffer shorter than a mint raises `ShortBuffer`; a tag that is neither 0 nor 1 raises
    `ValueError`, matching the program's `InvalidAccountData`.
    """
    _require(data, MINT_BASE_LEN, "mint")
    tag = int.from_bytes(bytes(data[0:4]), "little")
    if tag == 0:
        return None
    if tag == 1:
        return bytes(data[4:36])
    raise ValueError(f"mint authority COption tag is {tag}, not 0 or 1")


# -- instructions, tag 0..3 --------------------------------------------------
#
# `data` is the whole instruction data this program reads: the tag, then the payload. The
# account lists are the caller's, because they differ between a fresh create and a retry and
# this module never talks to a cluster.


class _Instruction:
    __slots__ = ()
    TAG: int = -1
    PAYLOAD: tuple = ()

    def __eq__(self, other):
        if type(other) is not type(self):
            return NotImplemented
        return all(getattr(self, name) == getattr(other, name) for name in self.fields())

    def __repr__(self) -> str:
        body = ", ".join(f"{name}={getattr(self, name)!r}" for name in self.fields())
        return f"{type(self).__name__}({body})"

    @classmethod
    def fields(cls) -> tuple:
        return tuple(name for name, *_ in cls.PAYLOAD)

    @property
    def data(self) -> bytes:
        values = {name: getattr(self, name) for name in self.fields()}
        return bytes([self.TAG]) + _pack(self.PAYLOAD, values)


class InitializeExtraAccountMetaList(_Instruction):
    """Tag 0. Creates `["extra-account-metas", mint]`, naming `["record", mint]` as the extra account.

    No argument. The program derives the record from the mint: the list is create-once and the
    hook refuses 6020 against any record but the derived one, so a caller-supplied pubkey would
    be a way to brick the mint's transfers with no way back.
    """

    __slots__ = ()
    TAG = TAG_INITIALIZE_EXTRA_ACCOUNT_META_LIST
    PAYLOAD = INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD


class InitializeRecord(_Instruction):
    """Tag 1. Creates `["record", mint]` with the face, the cap, the floor and the policy.

    The jurisdiction rule lives in `initialize_record`, the builder: the class stores the two
    bytes it is given, so `parse_instruction` can read bytes another client wrote without
    imposing a rule the program itself does not enforce.
    """

    __slots__ = tuple(name for name, *_ in INITIALIZE_RECORD_LAYOUT)
    TAG = TAG_INITIALIZE_RECORD
    PAYLOAD = INITIALIZE_RECORD_LAYOUT

    def __init__(self, *, face_value_lamports, cap_bps, band_low_lamports, jurisdiction, policy):
        # `policy` is not validated here on purpose: the program's 6023 is the refusal that
        # has to be observable, and a client-side check would hide it.
        self.face_value_lamports = face_value_lamports
        self.cap_bps = cap_bps
        self.band_low_lamports = band_low_lamports
        self.jurisdiction = _jurisdiction_bytes(jurisdiction)
        self.policy = policy


class SetPendingPrice(_Instruction):
    """Tag 2. Stages the price the next transfer of this mint is checked against.

    The instruction carries no signer, but the program reads one: the account list is
    `[authority (signer), record, mint]` and a signature that is not the record's `authority` is
    refused 6026. Staging is what the hook admits against, so it is a write and it is authorised
    like the satellites are.
    """

    __slots__ = ("price_lamports",)
    TAG = TAG_SET_PENDING_PRICE
    PAYLOAD = (("price_lamports", 0, 8, "u64"),)

    def __init__(self, *, price_lamports):
        self.price_lamports = price_lamports


class SetStatus(_Instruction):
    """Tag 3. Flips the record's transferable flag: 1 transferable, 0 not.

    Same accounts and the same 6026 as tag 2: `status = 0` refuses every later transfer of the
    ticket with 6013, which is a permanent freeze if a stranger can do it.
    """

    __slots__ = ("status",)
    TAG = TAG_SET_STATUS
    PAYLOAD = (("status", 0, 1, "u8"),)

    def __init__(self, *, status):
        self.status = status


class PublishBand(_Instruction):
    """Tag 4. Writes the rewritable head of `["band", mint]`."""

    __slots__ = tuple(name for name, *_ in PUBLISH_BAND_LAYOUT)
    TAG = TAG_PUBLISH_BAND
    PAYLOAD = PUBLISH_BAND_LAYOUT

    def __init__(self, *, low, high, as_of_slot, sample_n, refused, model_hash):
        self.low = low
        self.high = high
        self.as_of_slot = as_of_slot
        self.sample_n = sample_n
        self.refused = refused
        self.model_hash = _as_bytes(model_hash, 32, "model_hash")


class LogForecast(_Instruction):
    """Tag 5. Creates the one forecast for `["forecast", mint, as_of_unix_le]`."""

    __slots__ = tuple(name for name, *_ in LOG_FORECAST_LAYOUT)
    TAG = TAG_LOG_FORECAST
    PAYLOAD = LOG_FORECAST_LAYOUT

    def __init__(self, *, low, high, as_of_unix, sample_n, model_hash, scoring_rule_hash):
        self.low = low
        self.high = high
        self.as_of_unix = as_of_unix
        self.sample_n = sample_n
        self.model_hash = _as_bytes(model_hash, 32, "model_hash")
        self.scoring_rule_hash = _as_bytes(scoring_rule_hash, 32, "scoring_rule_hash")


class ScoreForecast(_Instruction):
    """Tag 6. Creates the one score for `["score", forecast]`; the forecast is read-only."""

    __slots__ = tuple(name for name, *_ in SCORE_FORECAST_LAYOUT)
    TAG = TAG_SCORE_FORECAST
    PAYLOAD = SCORE_FORECAST_LAYOUT

    def __init__(self, *, realised_lamports, interval_score_micro):
        self.realised_lamports = realised_lamports
        self.interval_score_micro = interval_score_micro


def _jurisdiction_bytes(value) -> bytes:
    """The two bytes of a jurisdiction code.

    A `str` is the code itself (`"CA"`, `"ZZ"`), not base58: two letters are also two
    perfectly good base58 digits, so treating the text as an encoding would turn `ZZ` into
    bytes nobody wrote. `bytes` is taken as the pair. Every other 32-byte field on this wire
    is a key and does travel as base58; this one is not a key.
    """
    if isinstance(value, str):
        try:
            raw = value.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ValueError(f"jurisdiction must be ASCII, got {value!r}") from exc
    elif isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value)
    else:
        raise TypeError(f"jurisdiction: expected text or bytes, got {type(value).__name__}")
    if len(raw) != 2:
        raise ValueError(f"jurisdiction is two bytes, got {value!r}")
    return raw


def _jurisdiction(value) -> bytes:
    """Two uppercase ASCII bytes. `ZZ` is the specified "no jurisdiction" value.

    The program stores the pair as written and does not validate it, so this is the client
    being strict where the chain is permissive: a lowercase or three-byte code would be stored
    and logged, and nothing on chain would ever notice.
    """
    raw = _jurisdiction_bytes(value)
    if not all(0x41 <= byte <= 0x5A for byte in raw):
        raise ValueError("jurisdiction must be two uppercase ASCII letters, e.g. 'CA' or 'ZZ'")
    return raw


def initialize_extra_account_meta_list() -> bytes:
    """Tag 0's instruction data: the tag alone, 1 byte. The record is derived from the mint."""
    return InitializeExtraAccountMetaList().data


def initialize_record(*, face_value_lamports, cap_bps, band_low_lamports, jurisdiction, policy) -> bytes:
    """Tag 1's instruction data: 22 bytes (1 tag + 21 argument bytes).

    The jurisdiction is checked here and not in the class: a builder that emitted `ca` would
    write a code no reader expects, and the chain would never say so.
    """
    _jurisdiction(jurisdiction)
    return InitializeRecord(
        face_value_lamports=face_value_lamports,
        cap_bps=cap_bps,
        band_low_lamports=band_low_lamports,
        jurisdiction=jurisdiction,
        policy=policy,
    ).data


def set_pending_price(*, price_lamports) -> bytes:
    """Tag 2's instruction data: 1 tag byte + a u64 price = 9 bytes.

    Accounts: `[authority (signer), record, mint]`. See `set_pending_price_accounts`.
    """
    return SetPendingPrice(price_lamports=price_lamports).data


def set_status(*, status) -> bytes:
    """Tag 3's instruction data: 1 tag byte + a u8 status = 2 bytes.

    Accounts: `[authority (signer), record, mint]`. See `set_status_accounts`.
    """
    return SetStatus(status=status).data


def publish_band(*, low, high, as_of_slot, sample_n, refused, model_hash) -> bytes:
    """Tag 4's instruction data: 62 bytes (1 tag + 61 argument bytes)."""
    return PublishBand(
        low=low,
        high=high,
        as_of_slot=as_of_slot,
        sample_n=sample_n,
        refused=refused,
        model_hash=model_hash,
    ).data


def log_forecast(*, low, high, as_of_unix, sample_n, model_hash, scoring_rule_hash) -> bytes:
    """Tag 5's instruction data: 93 bytes (1 tag + 92 argument bytes)."""
    return LogForecast(
        low=low,
        high=high,
        as_of_unix=as_of_unix,
        sample_n=sample_n,
        model_hash=model_hash,
        scoring_rule_hash=scoring_rule_hash,
    ).data


def score_forecast(*, realised_lamports, interval_score_micro) -> bytes:
    """Tag 6's instruction data: 17 bytes (1 tag + 16 argument bytes)."""
    return ScoreForecast(
        realised_lamports=realised_lamports,
        interval_score_micro=interval_score_micro,
    ).data


_READERS = {
    TAG_INITIALIZE_EXTRA_ACCOUNT_META_LIST: InitializeExtraAccountMetaList,
    TAG_INITIALIZE_RECORD: InitializeRecord,
    TAG_SET_PENDING_PRICE: SetPendingPrice,
    TAG_SET_STATUS: SetStatus,
    TAG_PUBLISH_BAND: PublishBand,
    TAG_LOG_FORECAST: LogForecast,
    TAG_SCORE_FORECAST: ScoreForecast,
}


def parse_instruction(data):
    """Read instruction data back into one of the seven classes. Strict, like the program.

    A tag outside 0..=6 is not this program's own instruction: the Rust side hands it to the
    SPL transfer-hook discriminator. Here it is a `ValueError`, because a client that built
    one would be sending bytes this program reads as a hook call.
    """
    _require(data, 1, "instruction data")
    tag = data[0]
    cls = _READERS.get(tag)
    if cls is None:
        raise ValueError(f"tag {tag} is not one of this program's own instructions (0..=6)")
    payload = _unpack(cls.PAYLOAD, data[1:], f"tag {tag} payload")
    return cls(**payload)


# -- PDA seeds and derivation ------------------------------------------------


class NotAProgramAddress(ValueError):
    """No bump produces an address off the ed25519 curve, or the seeds are not seedable."""


MAX_SEEDS = 16
MAX_SEED_LEN = 32
PDA_MARKER = b"ProgramDerivedAddress"


def _mint_seed(mint) -> bytes:
    return _as_bytes(mint, 32, "mint")


def seeds_record(mint) -> tuple:
    """`["record", mint]`, the hook's record, one per mint."""
    return (b"record", _mint_seed(mint))


def seeds_extra_account_meta_list(mint) -> tuple:
    """`["extra-account-metas", mint]`, the literal the SPL interface fixes."""
    return (b"extra-account-metas", _mint_seed(mint))


def seeds_band(mint) -> tuple:
    """`["band", mint]`, the public feed's head."""
    return (b"band", _mint_seed(mint))


def seeds_forecast(mint, as_of_unix: int) -> tuple:
    """`["forecast", mint, as_of_unix_le]`, one forecast per (mint, instant)."""
    if not isinstance(as_of_unix, int) or isinstance(as_of_unix, bool):
        raise TypeError("as_of_unix must be an int (unix seconds)")
    return (b"forecast", _mint_seed(mint), as_of_unix.to_bytes(8, "little", signed=True))


def seeds_score(forecast) -> tuple:
    """`["score", forecast]`, one score per forecast."""
    return (b"score", _as_bytes(forecast, 32, "forecast"))


def seeds_fee_authority(mint) -> tuple:
    """`["fee-authority", mint]`, the mint's withdraw-withheld authority as a PDA."""
    return (b"fee-authority", _mint_seed(mint))


def seeds_rebate_pool(mint) -> tuple:
    """`["rebate-pool", mint]`, the owner of the token account withheld fees are harvested into."""
    return (b"rebate-pool", _mint_seed(mint))


def _check_seeds(seeds) -> tuple:
    seeds = tuple(seeds)
    if len(seeds) > MAX_SEEDS:
        raise NotAProgramAddress(f"at most {MAX_SEEDS} seeds, got {len(seeds)}")
    for seed in seeds:
        if not isinstance(seed, (bytes, bytearray)):
            raise TypeError(f"a seed is bytes, got {type(seed).__name__}")
        if len(seed) > MAX_SEED_LEN:
            raise NotAProgramAddress(f"a seed is at most {MAX_SEED_LEN} bytes, got {len(seed)}")
    return tuple(bytes(seed) for seed in seeds)


# -- the curve test ----------------------------------------------------------
#
# `create_program_address` refuses an address that decompresses to an ed25519 point, because a
# point has a discrete log and the program has no private key for it. The test below is RFC
# 8032 section 5.1.3 (recover x from y), the same test `ticketpath/core/ed25519.py` performs
# on the verification path. It is repeated rather than imported because that module keeps it
# private, and forty lines of public arithmetic is cheaper than a private dependency.

_P = 2**255 - 19
_D = -121665 * pow(121666, _P - 2, _P) % _P
_I = pow(2, (_P - 1) // 4, _P)


def is_on_curve(point) -> bool:
    """True when these 32 little-endian bytes are a valid ed25519 point (a PDA cannot be)."""
    if len(point) != 32:
        raise ValueError(f"a curve point is 32 bytes, got {len(point)}")
    y = int.from_bytes(point, "little") & ((1 << 255) - 1)
    y %= _P
    u = (y * y - 1) % _P
    v = (_D * y * y + 1) % _P
    x_squared = u * pow(v, _P - 2, _P) % _P
    if x_squared == 0:
        return True
    x = pow(x_squared, (_P + 3) // 8, _P)
    if x * x % _P != x_squared:
        x = x * _I % _P
    return x * x % _P == x_squared


def find_program_address(program_id, seeds) -> tuple:
    """`(base58 address, bump)`, the way the runtime derives it.

    The digest is `sha256(seeds || [bump] || program_id || "ProgramDerivedAddress")`, and the
    first bump from 255 downwards whose digest is **not** on the curve wins. Stopping at the
    first digest is the mistake this function exists to prevent: that address has a private
    key and the program can never sign for it.
    """
    program = _as_bytes(program_id, 32, "program id")
    checked = _check_seeds(seeds)
    for bump in range(255, -1, -1):
        digest = hashlib.sha256(
            b"".join(checked) + bytes([bump]) + program + PDA_MARKER
        ).digest()
        if not is_on_curve(digest):
            return base58.encode(digest), bump
    raise NotAProgramAddress("no bump between 255 and 0 produced an address off the curve")


def record_address(program_id, mint) -> tuple:
    """`["record", mint]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_record(mint))


def extra_account_meta_list_address(program_id, mint) -> tuple:
    """`["extra-account-metas", mint]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_extra_account_meta_list(mint))


def band_address(program_id, mint) -> tuple:
    """`["band", mint]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_band(mint))


def forecast_address(program_id, mint, as_of_unix: int) -> tuple:
    """`["forecast", mint, as_of_unix_le]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_forecast(mint, as_of_unix))


def score_address(program_id, forecast) -> tuple:
    """`["score", forecast]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_score(forecast))


def fee_authority_address(program_id, mint) -> tuple:
    """`["fee-authority", mint]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_fee_authority(mint))


def rebate_pool_address(program_id, mint) -> tuple:
    """`["rebate-pool", mint]` as `(address, bump)`."""
    return find_program_address(program_id, seeds_rebate_pool(mint))


# -- account argument lists, tags 0..3 ---------------------------------------
SYSTEM_PROGRAM = "11111111111111111111111111111111"

#
# Same convention as tags 4..6 below: the order is the program's `next_account_info` order and
# the flags are what it needs. Tag 0's list has no record in it because the program derives it;
# tags 2 and 3 lead with the signer because the program refuses 6026 without one.

INITIALIZE_EXTRA_ACCOUNT_META_LIST_ACCOUNTS = (
    ("payer", True, True),
    ("mint", False, False),
    ("extra_metas", False, True),
    ("system_program", False, False),
)
INITIALIZE_RECORD_ACCOUNTS = (
    ("payer", True, True),
    ("mint", False, False),
    ("record", False, True),
    ("mint_authority", True, False),
    ("system_program", False, False),
)
SET_PENDING_PRICE_ACCOUNTS = (
    ("authority", True, True),
    ("record", False, True),
    ("mint", False, False),
)
SET_STATUS_ACCOUNTS = SET_PENDING_PRICE_ACCOUNTS


def initialize_extra_account_meta_list_accounts(*, payer, mint, extra_metas,
                                                system_program=SYSTEM_PROGRAM):
    """`(pubkey, is_signer, is_writable)` in the order tag 0 reads them."""
    return (
        (payer, True, True),
        (mint, False, False),
        (extra_metas, False, True),
        (system_program, False, False),
    )


def initialize_record_accounts(*, payer, mint, record, mint_authority,
                               system_program=SYSTEM_PROGRAM):
    """`(pubkey, is_signer, is_writable)` in the order tag 1 reads them.

    `mint_authority` must be the mint's authority and must sign, or the program refuses 6026:
    the key that fixes the cap, the floor and the policy is the key that issued the ticket.
    """
    return (
        (payer, True, True),
        (mint, False, False),
        (record, False, True),
        (mint_authority, True, False),
        (system_program, False, False),
    )


def set_pending_price_accounts(*, authority, record, mint):
    """`(pubkey, is_signer, is_writable)` in the order tag 2 reads them."""
    return (
        (authority, True, True),
        (record, False, True),
        (mint, False, False),
    )


def set_status_accounts(*, authority, record, mint):
    """`(pubkey, is_signer, is_writable)` in the order tag 3 reads them."""
    return set_pending_price_accounts(authority=authority, record=record, mint=mint)


# -- account argument lists, tags 4..6 ---------------------------------------
#
# The order is the program's `next_account_info` order, and the flags are what the program
# needs: the signer writes, the record is read, the satellite PDA is written, the mint is
# read, and the system program is only used when the account has to be created. Names are
# kept beside the tuples so a caller and the Rust reader can be compared by this test.

PUBLISH_BAND_ACCOUNTS = (
    ("authority", True, True),
    ("record", False, False),
    ("band", False, True),
    ("mint", False, False),
    ("system_program", False, False),
)
LOG_FORECAST_ACCOUNTS = (
    ("authority", True, True),
    ("record", False, False),
    ("forecast", False, True),
    ("mint", False, False),
    ("system_program", False, False),
)
SCORE_FORECAST_ACCOUNTS = (
    ("scorer", True, True),
    ("forecast", False, False),
    ("score", False, True),
    ("system_program", False, False),
)


def publish_band_accounts(*, authority, record, band, mint, system_program=SYSTEM_PROGRAM):
    """`(pubkey, is_signer, is_writable)` in the order `PublishBand` reads them."""
    return (
        (authority, True, True),
        (record, False, False),
        (band, False, True),
        (mint, False, False),
        (system_program, False, False),
    )


def log_forecast_accounts(*, authority, record, forecast, mint, system_program=SYSTEM_PROGRAM):
    """`(pubkey, is_signer, is_writable)` in the order `LogForecast` reads them."""
    return (
        (authority, True, True),
        (record, False, False),
        (forecast, False, True),
        (mint, False, False),
        (system_program, False, False),
    )


def score_forecast_accounts(*, scorer, forecast, score, system_program=SYSTEM_PROGRAM):
    """`(pubkey, is_signer, is_writable)` in the order `ScoreForecast` reads them."""
    return (
        (scorer, True, True),
        (forecast, False, False),
        (score, False, True),
        (system_program, False, False),
    )


# -- the lengths, checked against the layouts at import ----------------------
#
# A constant that disagrees with the layout it describes is a decoder that reads past the end
# of an account at run time, so the disagreement is made an import-time error instead.

for _cls in (TicketRecord, Band, Forecast, Score):
    if _span(_cls.LAYOUT) != _cls.LEN:
        raise AssertionError(f"{_cls.__name__}.LEN is {_cls.LEN}, its layout is {_span(_cls.LAYOUT)}")

if _span(INITIALIZE_RECORD_LAYOUT) != INITIALIZE_RECORD_PAYLOAD_LEN:
    raise AssertionError("INITIALIZE_RECORD_PAYLOAD_LEN disagrees with the layout")

if _span(INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD) != INITIALIZE_EXTRA_ACCOUNT_META_LIST_PAYLOAD_LEN:
    raise AssertionError("tag 0's payload length disagrees with its (empty) layout")

for _layout, _length in (
    (PUBLISH_BAND_LAYOUT, PUBLISH_BAND_PAYLOAD_LEN),
    (LOG_FORECAST_LAYOUT, LOG_FORECAST_PAYLOAD_LEN),
    (SCORE_FORECAST_LAYOUT, SCORE_FORECAST_PAYLOAD_LEN),
):
    if _span(_layout) != _length:
        raise AssertionError(f"a payload length disagrees with its layout: {_length}")

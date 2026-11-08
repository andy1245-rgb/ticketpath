"""The one place a program name becomes bytes: v1's wire format and v2's, side by side.

`config.PROGRAMS` names the two programs; this module is what a name means on the wire. Every
instruction the gateway sends to a program is built here from the program the run selected, so a
v1 run cannot emit a v2 shape and a v2 run cannot emit a v1 one -- the selector is an argument
with no default, and a caller that forgot which program it was driving gets an error rather than
the other format.

The four instructions the swarm uses differ between the programs, and the differences are not
cosmetic. Measured against the two sources, not remembered:

    instruction              v1 (devnet, four tags)      v2 (local only, seven tags)
    InitExtraAccountMetas    record is an argument:       the record is derived from the
                             33 bytes, 4 accounts        mint: 1 byte, 4 accounts
    InitializeRecord         11 bytes, 4 accounts;       22 bytes, 5 accounts; the mint's
                             the payer signs and any    authority also signs and becomes the
                             payer may create it       record's authority; carries the floor,
                                                        the jurisdiction and the policy byte
    SetPendingPrice          9 bytes, `[record]` only   9 bytes, `[authority(signer), record,
                             -- no signer at all         mint]`, refused 6026 for any other
                                                         signer (v2's authorisation fix)
    TransferChecked          7 accounts, record         7 accounts, record **writable**: v2's
                             read-only                   hook writes `held_since_unix` into it

v1's encoders are `tools/devnet_publish.py`'s, called rather than copied: those are the bytes
that landed on devnet, and a second implementation of them would be two answers to one question.
v2's are written out here from `ticketpath/onchain/v2.py`, which describes that wire, and
`market_swarm/tests/test_wire.py` compares every v2 byte string with that module and every v1 one
with `devnet_publish`, so either side drifting is a failing test rather than a quiet fork.

What does *not* switch: the PDA seeds. `["record", mint]` and `["extra-account-metas", mint]` are
the same in both programs, so an address derived for one program differs from the other's only by
the program id it is derived under -- which is why the id has to be the program's own. The ids
themselves are the gateway's: naming a keypair is the gateway's job and nobody else's, so this
module takes a `program_id` from its caller and never looks one up.

Standard library only, and no socket: this module produces and reads bytes.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from market_swarm.config import PROGRAMS

# `tools/` has no `__init__.py`, so it is importable only once it is on `sys.path`; the same
# four lines gateway.py runs, for the same reason, because a test may import this module first.
REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import devnet_publish as dp  # noqa: E402

# -- the tag sets ------------------------------------------------------------

#: The tags each program reserves for its own instructions. v1 stops at 3; v2 adds the band, the
#: forecast and the score. A run's instruction data must carry a tag from its own set, and 4 to 6
#: are the tags v1 does not have -- sending one to a v1 program is how a harness reports "v2" while
#: the program answers `InvalidInstructionData`.
TAG_INIT_EXTRA_METAS = 0
TAG_INIT_RECORD = 1
TAG_SET_PENDING_PRICE = 2
TAG_SET_STATUS = 3
TAG_PUBLISH_BAND = 4
TAG_LOG_FORECAST = 5
TAG_SCORE_FORECAST = 6

TAGS = {
    "v1": frozenset({TAG_INIT_EXTRA_METAS, TAG_INIT_RECORD, TAG_SET_PENDING_PRICE, TAG_SET_STATUS}),
    "v2": frozenset(range(TAG_SCORE_FORECAST + 1)),
}

#: v2's `policy` byte, which is what its hook reads instead of v1's "monitored is cap 65535 and
#: nothing else". 0 caps the price at the ceiling, 1 admits anything expressible; any other value
#: is `6023` at `InitializeRecord`.
POLICY_CAPPED = 0
POLICY_MONITORED = 1
POLICY_BYTES = {"capped": POLICY_CAPPED, "monitored": POLICY_MONITORED}

#: v2's `InitializeRecord` needs a floor and a jurisdiction, and this harness has neither: the run
#: config carries no field for them. 0 lamports is "no floor" (`band_low_lamports > 0` is what
#: enables the check, so 0 disables it) and `ZZ` is the specified "no jurisdiction". A record made
#: this way enforces exactly the cap and the policy, which is the part of v2 this harness can
#: exercise; a run that wanted a floor needs a config field that does not exist yet.
NO_FLOOR_LAMPORTS = 0
NO_JURISDICTION = b"ZZ"

#: The `TicketRecord` account lengths. v1's is 19 bytes (`LEN` in its Rust says 20 and is dead
#: code: the account is allocated at its serialised length); v2's is 70, which is the layout in
#: `ticketpath/onchain/v2.py` and in `state.rs`.
V1_RECORD_LEN = 19
V2_RECORD_LEN = 70


# -- the boundary ------------------------------------------------------------


def _require_program(program: str) -> str:
    """The program name, or a refusal that names what was asked for."""
    if program not in PROGRAMS:
        raise ValueError(f"program: expected one of {sorted(PROGRAMS)}, got {program!r}")
    return program


def tags_for(program: str) -> frozenset[int]:
    """The tags this program has. A run's instruction data must stay inside it."""
    return TAGS[_require_program(program)]


# -- the instructions --------------------------------------------------------


def instruction_init_extra_metas(
    program: str, *, payer: str, mint: str, record: str, extra_metas: str, program_id: str
) -> Any:
    """`InitializeExtraAccountMetaList`, tag 0, in this program's shape.

    v1 takes the record as an argument: 33 bytes, the tag then the record's pubkey. v2 derives it
    from the mint and takes no argument at all, so its data is the tag alone -- the change is the
    fix for a caller being able to name a record the hook would not accept (v2 refuses `6020`).
    `record` is therefore accepted here and used by v1 only; a v2 run passes it because the
    gateway derives it either way and the address is worth having in one place.
    """
    program = _require_program(program)
    if program == "v1":
        return dp.instruction_init_extra_metas(
            payer=payer, mint=mint, extra_metas=extra_metas, record=record, program_id=program_id
        )
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(payer, True, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(extra_metas, False, True),
            dp.AccountMeta(dp.SYSTEM_PROGRAM, False, False),
        ),
        data=bytes([TAG_INIT_EXTRA_METAS]),
    )


def instruction_init_record(
    program: str,
    *,
    payer: str,
    mint: str,
    record: str,
    program_id: str,
    face: int,
    cap_bps: int,
    mint_authority: str | None = None,
    mode: str | None = None,
) -> Any:
    """`InitializeRecord`, tag 1: the face and the cap, plus whatever else this program stores.

    v1 stores the face and the cap, 11 bytes, and any payer may create the record.
    v2 stores the floor, the jurisdiction and the policy byte as well, 22 bytes, and the mint's
    authority has to sign -- so it becomes the record's authority, and every later write against
    that record (`SetPendingPrice`, `SetStatus`, the satellites) is refused `6026` for any other
    key. `mint_authority` and `mode` are required for v2 and refused when they are missing rather
    than defaulted: a v2 record with an invented policy byte would be a cap rule nobody chose.
    """
    program = _require_program(program)
    if program == "v1":
        return dp.instruction_init_record(
            payer=payer, mint=mint, record=record, program_id=program_id, face=face, cap_bps=cap_bps
        )
    if mint_authority is None:
        raise ValueError("mint_authority: required for v2, whose InitializeRecord is signed by it")
    if mode not in POLICY_BYTES:
        raise ValueError(f"mode: required for v2 as one of {sorted(POLICY_BYTES)}, got {mode!r}")
    data = (
        bytes([TAG_INIT_RECORD])
        + face.to_bytes(8, "little")
        + cap_bps.to_bytes(2, "little")
        + NO_FLOOR_LAMPORTS.to_bytes(8, "little")
        + NO_JURISDICTION
        + bytes([POLICY_BYTES[mode]])
    )
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(payer, True, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(mint_authority, True, False),
            dp.AccountMeta(dp.SYSTEM_PROGRAM, False, False),
        ),
        data=data,
    )


def instruction_set_pending_price(
    program: str,
    *,
    record: str,
    program_id: str,
    price: int,
    authority: str | None = None,
    mint: str | None = None,
) -> Any:
    """`SetPendingPrice`, tag 2: the price the next transfer of this mint is checked against.

    The same 9 bytes in both -- the tag and a `u64` -- and a different account list, which is the
    difference that matters. v1 takes the record alone and reads no signer, so anyone may stage a
    price on any record. v2 takes `[authority, record, mint]` and refuses `6026` for a signature
    that is not the record's authority.
    """
    program = _require_program(program)
    if program == "v1":
        return dp.instruction_set_pending_price(
            record=record, program_id=program_id, price=price
        )
    if authority is None or mint is None:
        raise ValueError(
            "authority and mint: required for v2, whose SetPendingPrice is [authority (signer), "
            "record, mint] and is refused 6026 for any other signer"
        )
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(authority, True, True),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(mint, False, False),
        ),
        data=bytes([TAG_SET_PENDING_PRICE]) + price.to_bytes(8, "little"),
    )


def instruction_transfer_checked(
    program: str,
    *,
    source: str,
    mint: str,
    destination: str,
    authority: str,
    record: str,
    hook_program: str,
    extra_metas: str,
    amount: int = 1,
    decimals: int = 0,
) -> Any:
    """Token-2022 `TransferChecked`, which is Token-2022's instruction and not the program's.

    The seven accounts and the 10 bytes of data are the same in both, and it is the program's
    hook that reads them. One flag differs: v2's hook writes `held_since_unix` into the record,
    so the record has to be writable, and it logs that it could not write when it is not -- a
    hook that runs, refuses correctly and never records a hold. v1's hook writes nothing, so its
    record stays read-only.
    """
    program = _require_program(program)
    if program == "v1":
        return dp.instruction_transfer_checked(
            source=source,
            mint=mint,
            destination=destination,
            authority=authority,
            record=record,
            hook_program=hook_program,
            extra_metas=extra_metas,
            amount=amount,
            decimals=decimals,
        )
    return dp.Instruction(
        program_id=dp.TOKEN_2022_PROGRAM,
        accounts=(
            dp.AccountMeta(source, False, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(destination, False, True),
            dp.AccountMeta(authority, True, False),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(hook_program, False, False),
            dp.AccountMeta(extra_metas, False, False),
        ),
        data=bytes([dp.TOKEN_INSTRUCTION_TRANSFER_CHECKED])
        + amount.to_bytes(8, "little")
        + bytes([decimals]),
    )


# -- the record account, read back -------------------------------------------


def decode_v1_record(data: bytes) -> dict:
    """The v1 `["record", mint]` account, 19 bytes of Borsh and no discriminator.

    `face_value_lamports u64 | cap_bps u16 | pending_price_lamports u64 | status u8`. The Rust
    `TicketRecord::LEN` says 20 and is dead code: `initialize_record` allocates the length of the
    actual serialisation, which is 19.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError(f"data: expected bytes, got {type(data).__name__}")
    if len(data) != V1_RECORD_LEN:
        raise ValueError(f"record: expected {V1_RECORD_LEN} bytes of Borsh, got {len(data)}")
    return {
        "face_lamports": int.from_bytes(data[0:8], "little"),
        "cap_bps": int.from_bytes(data[8:10], "little"),
        "pending_price_lamports": int.from_bytes(data[10:18], "little"),
        "status": data[18],
    }


def decode_v2_record(data: bytes) -> dict:
    """The v2 `["record", mint]` account, 70 bytes, in `ticketpath/onchain/v2.py`'s field names.

    `face u64 | cap u16 | pending u64 | status u8 | band_low u64 | jurisdiction [u8;2] |
    policy u8 | held_since i64 | authority [u8;32]`. The bytes are kept for the jurisdiction and
    the authority rather than turned into text here: a decoder that guessed an encoding would
    disagree with the program's own log, which prints `??` for anything that is not ASCII.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError(f"data: expected bytes, got {type(data).__name__}")
    if len(data) != V2_RECORD_LEN:
        raise ValueError(f"record: expected {V2_RECORD_LEN} bytes of Borsh, got {len(data)}")
    return {
        "face_value_lamports": int.from_bytes(data[0:8], "little"),
        "cap_bps": int.from_bytes(data[8:10], "little"),
        "pending_price_lamports": int.from_bytes(data[10:18], "little"),
        "status": data[18],
        "band_low_lamports": int.from_bytes(data[19:27], "little"),
        "jurisdiction": bytes(data[27:29]),
        "policy": data[29],
        "held_since_unix": int.from_bytes(data[30:38], "little", signed=True),
        "authority": bytes(data[38:70]),
    }


def decode_record(program: str, data: bytes) -> dict:
    """The record account as the selected program lays it out.

    Two shapes, so a v2 run cannot read v1's 19 bytes as if they were its own 70: each length is
    exact and the other program's length is refused, which is the reader half of the same switch
    the encoders are.
    """
    program = _require_program(program)
    return decode_v1_record(data) if program == "v1" else decode_v2_record(data)


__all__ = [
    "NO_FLOOR_LAMPORTS",
    "NO_JURISDICTION",
    "POLICY_BYTES",
    "POLICY_CAPPED",
    "POLICY_MONITORED",
    "TAGS",
    "TAG_INIT_EXTRA_METAS",
    "TAG_INIT_RECORD",
    "TAG_PUBLISH_BAND",
    "TAG_LOG_FORECAST",
    "TAG_SCORE_FORECAST",
    "TAG_SET_PENDING_PRICE",
    "TAG_SET_STATUS",
    "V1_RECORD_LEN",
    "V2_RECORD_LEN",
    "decode_record",
    "decode_v1_record",
    "decode_v2_record",
    "instruction_init_extra_metas",
    "instruction_init_record",
    "instruction_set_pending_price",
    "instruction_transfer_checked",
    "tags_for",
]

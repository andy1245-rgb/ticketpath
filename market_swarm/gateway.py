"""The only module in `market_swarm` that touches a keypair path, an RPC endpoint or a validator.

Above this line nothing holds a key, a socket or a process handle: `Policy.decide` receives a
`MarketView`, the runner receives a `TransferResult`, and a `TransferResult` has no field a key
could hide in. Everything that reads a keypair file is a child process (`tools/solana_sign.py`
for signatures, `solana-keygen pubkey` for an address), so this module holds paths and public
addresses and never bytes.

What it drives is the real program. One local validator, started here, with the prebuilt
`programs/cap_hook/target/deploy/cap_hook.so` deployed to it (never rebuilt: the build peaks near
4.6 GB on a box that has less than that free). Each event is a Token-2022 mint carrying the
transfer-hook and metadata-pointer extensions, plus the program's two PDAs: `["record", mint]`
holds face, cap, the staged price and a status byte, and `["extra-account-metas", mint]` is what
Token-2022 resolves before it calls the hook.

**One transaction per transfer, two instructions.** `SetPendingPrice` and the Token-2022
`TransferChecked` are compiled into a single legacy message by `compile_message`, which takes a
list, and signed once by the seller -- twice on a v2 run, where the stage instruction is
authorised by the record's authority and the seller is not that key. That is what makes
stage-and-check atomic: the record's staged price cannot be moved by another transfer between
the two instructions, and a refusal rolls the staging back with it. It also halves the v1 fee,
from two signatures to one.

**One event exception: an artist fee.** An event whose spec names a fee policy pays the artist in
the same transaction, so that sale is three instructions and two signatures -- the v2 stage signed
by the issuer (the record's authority), a System `Transfer` of `fee_bps` of the price from the
seller, and the move. The fee arithmetic, the omission of a zero fee and the refusal to build a
sale that cannot succeed live in `market_swarm/artist_fee.py`; this module decides only which
signatures go on the wire, and it reads that set back out of the compiled message instead of
assuming it. An event with no policy takes every branch this file took before the fee existed.

**A second exception, layered on the first: the flip tax.** An event whose spec names an enabled
flip tax pays a second seller-side `System` transfer, whose rate falls with the hold. The hold is
the `held_since_unix` the hook writes into the v2 record, so a taxed sale reads the record before
it builds anything, prices the tax with `market_swarm/flip_tax.py`'s arithmetic, and then builds
`(stage, artist_fee?, flip_tax?, move)` in one transaction. A record that cannot be read is a
`ChainUnavailable` and nothing is signed: pricing a tax off a record nobody read is worse than not
selling. The one clock read on that path is `_now()`, an instance method so a test can replace it
rather than wait an hour. An event with no tax block, or a sale that says `charge_flip_tax=False`,
takes exactly the branch it took before the tax existed.

The reused units are `tools/devnet_publish.py`'s pure encoders and bounded readers (see
`.research/wave2-gateway.md` for the function-by-function list). No `step_*` function is called:
each of those writes the publish run's resume file under `records/`, assumes one mint and one
buyer, and raises on a refusal instead of returning one.

**Which program this drives is a parameter, not an assumption.** `program` is `"v1"` or `"v2"`,
and every instruction that reaches a program on a plain sale is built for that program by
`market_swarm/wire.py`, so the program id this connects to, the keypair it deploys with and the
bytes a plain sale sends all follow the same name. v1 is what devnet serves; v2 has only ever run
locally, from its own keypair, and its `SetPendingPrice` is authorised by the record's authority
-- `InitializeRecord` pins that to the mint's authority, which is the house key this gateway
creates the mint and signs the record with. So the seller cannot stage a v2 price on its own
signature, and a v2 plain sale is the one sale this file signs with two keys: the seller pays and
authorises the move, the house stages the price, and `_send_multi` checks the pair against the
compiled message before either key is used. v1's stage takes the record alone and reads no
signer, so a v1 plain sale is still one signature.

The fee and flip-tax paths above are the exception, and it is stated rather than glossed: their
stage and move are always the v2 shapes, on a v1 run too, because the record those paths write is
the one that carries the hold clock and the v2 authority. So a fee or tax event is a v2-record
event whatever `program` says, and a plain sale on a v1 run keeps the v1 encoders.

Standard library only.
"""

from __future__ import annotations

import atexit
import base64
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from market_swarm import wire
from market_swarm.config import (
    EventSpec,
    MODES,
    PROGRAM_CLUSTERS,
    PROGRAM_DEFAULT,
    PROGRAMS,
    ceiling_lamports,
    effective_cap_bps,
)
from market_swarm.artist_fee import ArtistFeePolicy, fee_lamports, sale_instructions
from market_swarm.flip_tax import (
    FlipTaxError,
    FlipTaxPolicy,
    MAX_BPS,
    UNKNOWN_HOLD,
    assess as assess_flip_tax,
    combined_take_bps,
    held_since_unix_from_record,
    sale_instructions as tax_sale_instructions,
)

# `tools/` has no `__init__.py`; it becomes importable only once it is on `sys.path`, and it is
# already inside the repository as `devnet_publish.py` needs it to be (its own REPO_ROOT comes
# from __file__, so a copy outside the tree breaks its imports). Importing it reaches no cluster,
# no key, no network and no file: it is two pathlib computations, two imports and constants.
REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(REPO_ROOT), str(REPO_ROOT / "tools")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import devnet_publish as dp  # noqa: E402

# -- the closed sets ---------------------------------------------------------

#: Clusters this gateway can reach. There is no branch, default or override that names another
#: one, so a config that says anything else fails before a socket opens.
CLUSTERS = frozenset({"local", "devnet"})
DEVNET_RPC = {"devnet": "https://api.devnet.solana.com"}

#: Which address each program is at. This is the identity a run is talking to, so it is stated
#: rather than read off whichever keypair happens to be in `target/deploy`: v1's frozen devnet
#: address (no upgrade, no re-sign, no edit), and v2's, which nothing public has ever run. Both are
#: the pubkeys of the two keypairs beside the `.so`, which `_program_id_from_disk` checks before a
#: deploy, and `tests/test_wire.py` checks against the files themselves.
PROGRAM_IDS = {
    "v1": "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva",
    "v2": "CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w",
}

#: The keypair each program deploys with, beside the prebuilt `.so`. Two programs share one
#: `target/deploy` and the keypair is what decides the address, so the mapping follows the program:
#: deploying v1's key under a v2 run would put one program's bytecode at the other's address.
#: v2's file is the one `tools/publish_v2.py` deploys with.
PROGRAM_KEYPAIRS = {
    "v1": dp.PROGRAM_KEYPAIR,
    "v2": dp.PROGRAM_KEYPAIR.with_name("v2-keypair.json"),
}

#: The `.so` each program deploys, for the same reason as the keypair table above: two programs
#: share one `target/deploy`, and a build overwrites the file it writes, so one shared path would
#: make "which bytes are deployed" depend on which build ran last. That is exactly the question a
#: build-provenance record exists to answer, and `programs/cap_hook/BUILD-PROVENANCE.json` names
#: these two paths. v2 keeps `dp.SO_PATH` because every tool here already deploys that one.
PROGRAM_BINARIES = {
    "v1": dp.SO_PATH.with_name("cap_hook-v1.so"),
    "v2": dp.SO_PATH,
}

#: The program's own error for a price over the cap, `0x177a`.
E_CAP_EXCEEDED = 6010
#: `E_TRANSFER_NOT_STAGED` (6009): the refusal a swarm gets when it forgets to stage a price. It
#: looks like a cap problem and is not, so it is named here and mapped to `error`, not `refused`.
E_TRANSFER_NOT_STAGED = 6009

#: System Program `Transfer`: bincode variant index 2, then a u64 of lamports. 12 bytes.
SYSTEM_TAG_TRANSFER = 2
SYSTEM_TRANSFER_LEN = 12

#: The label whose wallet is the mint authority, the fee payer for setup and the house that
#: `stock` mints to. It is funded at genesis by the validator's own `--mint`, not by a transfer.
HOUSE_LABEL = "authority"

#: Lamports handed to each agent wallet so it can pay its own fees. A signature is 5000
#: lamports, so this is 10,000 signed transactions per wallet; rent-exempt for an empty system
#: account is well under it on every rent rate this repository has measured.
FUND_LAMPORTS_PER_WALLET = 50_000_000

#: Below this a wallet is topped up rather than left alone, so a second `start()` on the same run
#: directory (a fresh ledger, key files already on disk) does not hand an agent an empty wallet.
WALLET_FLOOR_LAMPORTS = 10_000_000

#: The marker every `DryRunGateway` result carries. The runner turns its presence into
#: `chain="simulated"`, and it is the only thing standing between a "would have happened" row
#: and a claim that something did.
SIMULATED_LOG = "simulated: no transaction was built, signed or sent"

_BOUND_DEPLOY = 900.0
_BOUND_CLI = 180.0
_BOUND_KEYGEN = 60.0
_BOUND_PUBKEY = 30.0
#: A read that decorates a result (slot, block time, logs, a balance). Short on purpose: the
#: verdict is already known when one of these runs, and a decoration must not outlast it.
_READ_TIMEOUT = 15.0
_READ_ATTEMPTS = 2
_CONFIRM_TIMEOUT = 60.0
_LOOKS = 5
_LOOK_INTERVAL = 0.6

#: The validator writes to a pipe nobody drains in `LocalValidator`; a long run can fill it and
#: block the node mid-transaction. This thread drains it into a file beside the ledger, and stops
#: writing after this many bytes so a runaway log cannot fill the disk either.
_LOG_CAP_BYTES = 4_000_000

#: Ports the validator never takes, even when the kernel offers them. The first four are the
#: console's and the API's; 3010 and 8795 are kept back for services on this machine that this
#: repository does not own, and a picked port that landed on one would take that service down
#: rather than fail. `bind(0)` cannot reserve a port, so the only safe pick is to refuse the ports
#: whose owner is already known.
_RESERVED_PORTS = frozenset({3000, 3001, 3010, 8787, 8788, 8795})
_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
_SIGNALS = ("SIGINT", "SIGTERM", "SIGHUP")


# -- what a caller can catch -------------------------------------------------


class ChainUnavailable(RuntimeError):
    """The chain cannot be reached, or an account the gateway needs is not there.

    Never raised for a refusal: a refused transfer is a `TransferResult` with
    `status="refused"`. This is for "there is no cluster" and "the record is not on it".
    """


class _Rejected(Exception):
    """The cluster refused a transaction in preflight, so it never accepted one.

    Internal on purpose: a caller never sees it. It exists so the two ways `sendTransaction` can
    fail are not confused -- a preflight rejection is a verdict about the transaction (no
    signature exists on chain), while a failure to get a blockhash or to sign is a fault.
    """


class TicketNotHeld(ChainUnavailable):
    """The seller holds no ticket, so the transfer could not be attempted.

    Its own class because the cost of confusing it with a cap refusal is a wrong finding: the
    swarm would report the hook refusing a trade that never reached it.
    """


# -- the result --------------------------------------------------------------


@dataclass(frozen=True)
class TransferResult:
    """One transfer's public outcome. No key field, by construction.

    `status` is one of `{"ok", "refused", "error"}` and it is the chain's answer, not a
    prediction: `ok` means the transfer landed, `refused` means it landed as a failed
    transaction whose error was the cap, `error` means it landed (or was rejected in preflight)
    with some other error. `signature` is `None` only when no transaction was ever signed.
    """

    status: str
    signature: str | None = None
    slot: int | None = None
    block_time: int | None = None
    error_code: int | None = None
    latency_ms: int | None = None
    logs: tuple[str, ...] = ()

    #: What the seller paid the artist, in lamports, in the same transaction as the move.
    #: It is 0 on an event with no fee policy, 0 on anything that did not land, and the fee
    #: itself only on a transfer the chain executed: a refused or unconfirmed send reports 0
    #: because nothing was observed to move, and a row that claimed a fee it did not see
    #: would be the one number in the dataset pointing at a payment nobody can look up.
    fee_lamports: int = 0

    #: What the seller paid in flip tax, in lamports, in the same transaction as the move. 0 on
    #: an event with no tax policy, 0 on a sale that did not carry the tax (a primary sale), and
    #: 0 on anything that did not land -- the same sentence as the fee above, because a refused
    #: transaction rolls its tax leg back with the staging and a row that reported the tax anyway
    #: would name money nobody moved.
    flip_tax_lamports: int = 0

    #: The rate the tax was assessed at on this sale, in basis points, or `None` when the event
    #: has no tax policy or this sale did not carry it. It is kept even when no money moved: a
    #: refused sale reports 0 lamports and the rate that would have applied, so a dataset reader
    #: can see both the rule and the outcome instead of only the outcome.
    flip_tax_bps: int | None = None

    #: How long the record's clock says the ticket was held, in seconds, or `None` when the
    #: record never had its clock written (`held_since_unix == 0`, charged the full rate) or when
    #: no tax was assessed at all. `None` is not "held zero seconds": it is "nobody knows", and
    #: it is the number that explains the rate beside it.
    held_seconds: int | None = None


def is_simulated(result: TransferResult) -> bool:
    """True when this result came from a `DryRunGateway` and nothing reached a chain."""
    return SIMULATED_LOG in result.logs


# -- pure helpers ------------------------------------------------------------


def cap_admits(*, price_lamports: int, face_lamports: int, cap_bps: int) -> bool:
    """The on-chain predicate, in Python: `price * 10_000 <= face * (10_000 + cap_bps)`.

    The Rust computes both sides in `u128` because a `u64` product wraps and a wrapped result
    reads as a small number. Python integers do not wrap, so the same expression is exact; it is
    kept in that shape rather than as `price <= ceiling` so the two forms can be checked against
    each other, which `tests/test_gateway.py` does.
    """
    return price_lamports * 10_000 <= face_lamports * (10_000 + cap_bps)


def system_transfer_instruction(*, source: str, destination: str, lamports: int) -> Any:
    """A System Program `Transfer`: the one instruction no existing builder covers.

    Bincode, not Borsh: a u32 little-endian variant index (2 is `Transfer`) and a u64
    little-endian amount, 12 bytes in total. Accounts are `[from, to]`, with the source the only
    signer and both writable. This is how each agent wallet is funded from the authority, so the
    harness never asks a cluster's public source for anything.
    """
    if isinstance(lamports, bool) or not isinstance(lamports, int):
        raise ValueError(f"lamports: expected an integer, got {lamports!r}")
    if not 0 < lamports < 2**64:
        raise ValueError(f"lamports: expected 1..2**64-1, got {lamports}")
    data = SYSTEM_TAG_TRANSFER.to_bytes(4, "little") + lamports.to_bytes(8, "little")
    assert len(data) == SYSTEM_TRANSFER_LEN, "bincode: a u32 variant index then a u64 amount"
    return dp.Instruction(
        program_id=dp.SYSTEM_PROGRAM,
        accounts=(dp.AccountMeta(source, True, True), dp.AccountMeta(destination, False, True)),
        data=data,
    )


def instruction_set_pending_price_v2(
    *, authority: str, record: str, mint: str, program_id: str, price: int
) -> Any:
    """`SetPendingPrice` (tag 2) as the deployed v2 program takes it: nine bytes, three accounts.

    The accounts are `[authority (signer), record (writable), mint]`, and they are not the ones
    `dp.instruction_set_pending_price` builds. That encoder is v1: one account, no authority, and
    against a v2 record it cannot succeed, because `checked_record_for_write` requires
    `record.authority` to have signed. It is left alone here rather than corrected -- it belongs
    to the publish tool's run -- and this builder sits beside it so the sale path can name the v2
    shape without changing what anything else compiles.

    `mint` is read-only on purpose: the program derives the record's own address from the mint
    and writes it nowhere.
    """
    amount = _require_price(price)
    data = bytes([dp.TAG_SET_PENDING_PRICE]) + amount.to_bytes(8, "little")
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(authority, True, False),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(mint, False, False),
        ),
        data=data,
    )


def instruction_transfer_checked_writable(
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
    """The Token-2022 `TransferChecked`, byte for byte, with the record passed **writable**.

    One difference from `dp.instruction_transfer_checked`, which declares the record read-only.
    The rule the runtime enforces is that an account is writable for a transaction if **any**
    instruction in it says so, and that an inner CPI may not ask for more than the outer
    instruction granted. v2's extra-account-metas list declares the record writable
    (`RECORD_META_WRITABLE = true`, `programs/cap_hook/src/lib.rs`), so Token-2022 builds its CPI
    to the hook asking for a writable record; a message whose only mention of the record is
    read-only is therefore refused `PrivilegeEscalation` at the Token-2022 instruction and the hook
    never runs. It does not land with the write skipped — measured by the non-builder review of
    finding 42, section "the writability experiment".

    On the fee path the stage instruction already marks the record writable, so this flag changes
    nothing there and is belt-and-braces; on any path where the move is the only instruction that
    names the record it is the difference between a sale and a failed transaction.

    Same seven accounts in the same order, same ten data bytes. The test pins the two builders
    against each other and asserts that the record's write flag is the only difference.
    """
    return dp.Instruction(
        program_id=dp.TOKEN_2022_PROGRAM,
        accounts=(
            dp.AccountMeta(source, False, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(destination, False, True),
            dp.AccountMeta(authority, True, False),
            dp.AccountMeta(record, False, True),  # the one difference: the hook writes here
            dp.AccountMeta(hook_program, False, False),
            dp.AccountMeta(extra_metas, False, False),
        ),
        data=bytes([dp.TOKEN_INSTRUCTION_TRANSFER_CHECKED])
        + amount.to_bytes(8, "little")
        + bytes([decimals]),
    )


def _read_shortvec(data: bytes, at: int) -> tuple[int, int]:
    """A compact-u16 as `dp.shortvec` writes it. Returns `(value, next offset)`."""
    value = 0
    shift = 0
    while True:
        if at >= len(data):
            raise ValueError("message: a compact-u16 ran past the end of the bytes")
        byte = data[at]
        at += 1
        value |= (byte & 0x7F) << shift
        if not byte & 0x80:
            return value, at
        shift += 7
        if shift > 21:
            raise ValueError("message: a compact-u16 longer than three bytes")


def signer_keys_from_message(message: bytes) -> tuple[str, ...]:
    """The account keys that must sign a compiled message, in signature order.

    The legacy message layout is three header bytes, a compact-u16 key count, then that many
    32-byte keys; the header's first byte says how many of them are signers, and the canonical
    order `dp.compile_message` writes puts exactly those signers first. Signatures are positional,
    so the report has to be in that order and not merely the right set.

    Pure, and bounded: a message that could not have been compiled raises `ValueError` rather
    than walking off the end of the bytes. `dp.shortvec` writes the compact-u16 and has no reader,
    so the reader is here; the test pins the two against each other through `compile_message`.
    """
    if not isinstance(message, (bytes, bytearray)):
        raise ValueError(f"message: expected bytes, got {type(message).__name__}")
    if len(message) < 4:
        raise ValueError(f"message: expected at least 4 bytes, got {len(message)}")
    needed = message[0]
    count, at = _read_shortvec(bytes(message), 3)
    if needed > count:
        raise ValueError(
            f"message: the header claims {needed} signers and there are {count} account keys"
        )
    end = at + 32 * count
    if end > len(message):
        raise ValueError(
            f"message: {count} keys need {end} bytes and the message is {len(message)}"
        )
    return tuple(
        dp.base58.encode(message[at + 32 * index: at + 32 * (index + 1)])
        for index in range(needed)
    )


def decode_record(data: bytes) -> dict:
    """The `["record", mint]` account, 19 bytes of Borsh and no discriminator.

    `face_value_lamports u64 | cap_bps u16 | pending_price_lamports u64 | status u8`. This is the
    **v1** layout, 19 bytes, which is what `initialize_record` wrote when this function was
    written. It is stale against the deployed v2 program, whose `TicketRecord::LEN` is 70 and whose
    `checked_record_for_write` refuses any other length, so every caller of this decoder dies
    against a v2 record. Correcting it is a change to the harness's whole record read path and is
    disclosed rather than silently half-done: `records/findings/42-artist-fee-at-checkout.md` §6.
    """
    if not isinstance(data, (bytes, bytearray)):
        raise ValueError(f"data: expected bytes, got {type(data).__name__}")
    if len(data) != 19:
        raise ValueError(f"record: expected 19 bytes of Borsh, got {len(data)}")
    return {
        "face_lamports": int.from_bytes(data[0:8], "little"),
        "cap_bps": int.from_bytes(data[8:10], "little"),
        "pending_price_lamports": int.from_bytes(data[10:18], "little"),
        "status": data[18],
    }


def custom_error_code(err: Any) -> int | None:
    """The program's own error number out of a transaction error, or `None`.

    Only a `Custom` code is a program error; a builtin one (`IncorrectProgramId`, the runtime's
    `InsufficientFunds` as `Custom: 1`) is not, and `describe_error` says so in words.
    """
    if not isinstance(err, dict):
        return None
    detail = err.get("InstructionError")
    if isinstance(detail, list) and len(detail) == 2 and isinstance(detail[1], dict):
        code = detail[1].get("Custom")
        if isinstance(code, int) and not isinstance(code, bool):
            return code
    return None


def _code_from_text(text: str) -> int | None:
    """The `custom program error: 0x177a` a simulation failure quotes, as a number."""
    match = re.search(r"custom program error: 0x([0-9a-fA-F]+)", text)
    return int(match.group(1), 16) if match else None


_MINT_LOCKS: dict[str, threading.Lock] = {}
_MINT_LOCKS_GUARD = threading.Lock()


_LABEL_LOCKS: dict[str, threading.RLock] = {}
_LABEL_LOCKS_GUARD = threading.Lock()


def wallet_lock(label: str) -> threading.RLock:
    """The one lock for a label's keypair file.

    Two transfers on different mints can first use the same agent at the same moment. Without
    this, both run `solana-keygen new -o <the same path>`, one overwrites the other's address,
    and the agent trades from a wallet whose key nobody has. Re-entrant because funding one
    wallet reads the authority's path, which takes the authority's lock in turn.
    """
    with _LABEL_LOCKS_GUARD:
        lock = _LABEL_LOCKS.get(label)
        if lock is None:
            lock = threading.RLock()
            _LABEL_LOCKS[label] = lock
        return lock


def mint_lock(mint: str) -> threading.Lock:
    """The one lock for a mint's `stage -> transfer` pair.

    The staged price lives on the per-mint record, so two transfers of the same mint in flight
    together see whichever price was staged last. Different mints are independent and their locks
    are different objects, which is what lets two events run in parallel.
    """
    with _MINT_LOCKS_GUARD:
        lock = _MINT_LOCKS.get(mint)
        if lock is None:
            lock = threading.Lock()
            _MINT_LOCKS[mint] = lock
        return lock


# -- process plumbing --------------------------------------------------------


def _toolchain_path() -> str:
    """PATH with the two install locations this machine uses appended when they are missing."""
    path = os.environ.get("PATH", "")
    hints = [
        Path.home() / ".cargo" / "bin",
        Path.home() / ".local" / "share" / "solana" / "install" / "active_release" / "bin",
    ]
    for hint in hints:
        if hint.is_dir() and str(hint) not in path.split(os.pathsep):
            path = f"{path}{os.pathsep}{hint}" if path else str(hint)
    return path


def _which(binary: str) -> str | None:
    return shutil.which(binary, path=_toolchain_path())


def record_face_cap(observed: dict) -> tuple[int | None, int | None]:
    """The face and the cap out of either program's record decode, under one name each.

    The two decoders name the same first eight bytes differently on purpose: v1's
    `face_lamports` is this package's own name, and v2's `face_value_lamports` is the name
    `ticketpath/onchain/v2.py` and every v2 tool already reads, so neither is renamed. What a
    caller must not have to know is which program answered -- the ceiling is built from these
    two numbers and a record read as `None` would price a run against nothing -- so they are
    asked for here, once. An absent record is `(None, None)`, which matches no spec.
    """
    face = observed.get("face_lamports")
    if face is None:
        face = observed.get("face_value_lamports")
    return face, observed.get("cap_bps")


def _free_port() -> int:
    """A port nobody is on. A probe, not a reservation: the validator binds it microseconds later."""
    for _ in range(64):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        if port not in _RESERVED_PORTS and port > 1024:
            return port
    raise ChainUnavailable("no free port outside the reserved ones")


def _last_address(output: str) -> str | None:
    for token in reversed(re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b", output)):
        try:
            if len(dp.base58.decode(token)) == 32:
                return token
        except Exception:  # noqa: BLE001 - not base58, keep looking
            continue
    return None


def _require_label(label: str) -> str:
    if not isinstance(label, str) or not _LABEL.match(label):
        raise ValueError(
            f"wallet label: expected letters, digits, dot, dash or underscore (1..64) and a "
            f"leading letter or digit, got {label!r}"
        )
    return label


def _require_price(price: int) -> int:
    if isinstance(price, bool) or not isinstance(price, int):
        raise ValueError(f"price_lamports: expected an integer, got {price!r}")
    if not 0 < price < 2**64:
        raise ValueError(f"price_lamports: expected 1..2**64-1, got {price}")
    return price


def _refuse_combined_take(
    fee: "ArtistFeePolicy | None", tax: "FlipTaxPolicy | None", *, where: str
) -> None:
    """Refuse an event whose fee plus full tax rate is more than the whole price.

    The seller pays both out of one price, so their sum is what a quick resale costs, and a sum above
    `10_000` bps means the seller pays to sell. The rule has one definition
    (`flip_tax.combined_take_bps`) and three callers: the config loader, `_check_spec` (every
    `create_event`, real or dry), and `EventChain.__init__` -- because `EventChain` is public and a
    caller can construct one without going through either of the first two, which is exactly how
    review built a sale at 11 500 bps that the chain accepted.

    A disabled policy is not counted: a rule that charges nothing cannot overcharge.
    """
    if fee is None or tax is None or not tax.enabled:
        return
    combined = combined_take_bps(artist_fee_bps=fee.fee_bps, schedule=tax.schedule)
    if combined > MAX_BPS:
        raise ValueError(
            f"{where}.artist_fee.fee_bps {fee.fee_bps} plus {where}.flip_tax.schedule.full_bps "
            f"{tax.schedule.full_bps} is {combined} bps of the sale price, and the seller pays "
            f"both. A take above {MAX_BPS} bps means the seller pays to sell."
        )


def _check_spec(spec: EventSpec) -> tuple[int, int]:
    """`(cap_bps, face_lamports)` for a spec, refusing anything the record cannot hold."""
    if not isinstance(spec, EventSpec):
        raise ValueError(f"spec: expected an EventSpec, got {type(spec).__name__}")
    if spec.mode not in MODES:
        raise ValueError(f"spec.mode: expected one of {sorted(MODES)}, got {spec.mode!r}")
    if isinstance(spec.face_lamports, bool) or not isinstance(spec.face_lamports, int):
        raise ValueError(f"spec.face_lamports: expected an integer, got {spec.face_lamports!r}")
    if not 0 < spec.face_lamports < 2**64:
        raise ValueError(f"spec.face_lamports: expected 1..2**64-1, got {spec.face_lamports}")
    cap_bps = effective_cap_bps(spec.mode, spec.cap_bps)
    # The fee is opt-in and is a policy object, not a mapping by the time it gets here: the
    # loader parsed it into `ArtistFeePolicy` and this refuses anything else, so a hand-built
    # spec that forgot to parse its block fails here rather than at the first sale, after the
    # validator has booted and the ticket has been stocked.
    fee = getattr(spec, "artist_fee", None)
    if fee is not None and not isinstance(fee, ArtistFeePolicy):
        raise ValueError(
            f"spec.artist_fee: expected an ArtistFeePolicy or None, got {type(fee).__name__}"
        )
    # The tax is opt-in in the same way and is refused in the same place, for the same reason: a
    # hand-built spec that kept its block as a mapping fails here, before the validator boots and
    # the ticket is stocked, rather than at the first sale.
    tax = getattr(spec, "flip_tax", None)
    if tax is not None and not isinstance(tax, FlipTaxPolicy):
        raise ValueError(
            f"spec.flip_tax: expected a FlipTaxPolicy or None, got {type(tax).__name__}"
        )
    _refuse_combined_take(fee, tax, where="spec")
    # "monitored" is not "no cap". It fills the record's u16 field with its maximum, 65535, so the
    # hook still refuses any price above `face * 7.5535` -- and nothing above that ratio can be
    # expressed through this field at all. Prices below it are admitted, which is the point of the
    # mode: the ceiling sits so far above face that a scalper's ask passes, and the run records
    # that the hook saw it.
    return cap_bps, spec.face_lamports


# -- the gateway -------------------------------------------------------------


class ChainGateway:
    """One local validator (or one devnet connection), the program deployed, wallets funded.

    `start()` boots, deploys and funds; every later call assumes it succeeded. A transfer is the
    unit of work: one transaction, one signature, one row.
    """

    simulated = False

    def __new__(cls, *args, **kwargs):
        # `CONTRACT.md`: dry_run=True returns a DryRunGateway with the same surface. Dispatch here
        # so both doors -- this constructor and `make_gateway` -- give the same answer. `*args`
        # rather than the declared signature so a subclass can be constructed with its own.
        if cls is ChainGateway and kwargs.get("dry_run"):
            options = dict(kwargs)
            options.pop("dry_run")
            return DryRunGateway(*args, **options)
        return super().__new__(cls)

    def __init__(
        self,
        cluster: str,
        *,
        run_dir: Path,
        program: str = PROGRAM_DEFAULT,
        dry_run: bool = False,
    ) -> None:
        if cluster not in CLUSTERS:
            raise ValueError(f"cluster: expected one of {sorted(CLUSTERS)}, got {cluster!r}")
        if program not in PROGRAMS:
            raise ValueError(f"program: expected one of {sorted(PROGRAMS)}, got {program!r}")
        if cluster not in PROGRAM_CLUSTERS[program]:
            # The config loader refuses this pairing first; refused again here because the gateway
            # is constructed directly by callers and a seam is not a place for one copy of a rule.
            raise ValueError(
                f"program: {program!r} cannot be paired with cluster {cluster!r}: v2 has no "
                "devnet deployment, so a v2 run there would read v1's answers and call them v2's"
            )
        if dry_run:  # unreachable through __new__, kept for a subclass that calls __init__ directly
            raise ValueError("dry_run: construct DryRunGateway or use make_gateway")
        self.cluster = cluster
        self.program = program
        self.run_dir = Path(run_dir)
        self.rpc_url = DEVNET_RPC.get(cluster, "")
        self.program_id: str | None = None

        self._keys_dir = self.run_dir / "keys"
        self._ledger = self.run_dir / "validator-ledger"
        self._validator: Any = None
        self._drain: threading.Thread | None = None
        self._cli_config: Path | None = None
        self._ctx: Any = None
        self._keys: dict[str, Path] = {}
        self._addresses: dict[str, str] = {}
        self._ata: dict[tuple[str, str], str] = {}
        self._derive_cache: dict[tuple, str] = {}
        self._events: dict[str, "EventChain"] = {}
        self._started = False
        self._stopped = False
        self._state_lock = threading.Lock()

    # -- lifecycle -----------------------------------------------------------

    def start(self) -> dict:
        """Boot the cluster, deploy the prebuilt program, fund the wallet that pays for setup.

        Local: a fresh ledger under the run directory, deleted on `stop()` (a kept one is 1.5 GB),
        the authority funded at genesis by the validator's `--mint` so no public funding source is
        ever touched, then `solana program deploy` of the `.so` that is already built. Nothing here
        builds anything: the build peaks near 4.6 GB and the box does not have it.

        Devnet: connect only. No deploy, no key generation, no funding of the authority -- the
        path comes from `MARKET_SWARM_DEVNET_KEYPAIR` or `TP_DEVNET_KEYPAIR`, and a missing one
        is a refusal with a sentence rather than an automatic attempt to obtain test SOL.

        A local validator installs process-global signal handlers when it starts, so this method
        is main-thread only; the handlers are put back the moment the boot finishes, because a
        library must not own the harness's Ctrl-C. `atexit` is registered here, inside the thing
        that owns the process, and `stop()` is idempotent so a signal path and an `atexit` path
        cannot fight.

        v2 boots on v1's terms and differs in what it sends afterwards: its program id and deploy
        keypair are the v2 pair in the table at the top of this file, and its `SetPendingPrice`
        needs the record's authority to sign -- the mint authority this method funds at genesis and
        `_init_record` signs as -- so a v2 sale carries the house's signature beside the seller's.
        """
        with self._state_lock:
            # Read under the lock and answer outside it: `status()` takes the same non-reentrant
            # lock, so returning it from inside would deadlock the second `start()`.
            started = self._started
            if not started:
                self._stopped = False
                self.run_dir.mkdir(parents=True, exist_ok=True)
                self._keys_dir.mkdir(parents=True, exist_ok=True)
                os.chmod(self._keys_dir, 0o700)
        if started:
            return self.status()
        # Armed before anything can start a process: a start that fails after the validator is up
        # still has to be killed by somebody, and the caller's finally may never run.
        atexit.register(self.stop)
        if self.cluster == "devnet":
            self._adopt_devnet_authority()
        authority = self._wallet_path(HOUSE_LABEL)  # generates one only when there is no path yet
        self._wallet_address(HOUSE_LABEL)
        self.program_id = self._program_id_from_disk()
        if self.cluster == "local":
            self._start_local(authority)
        else:
            self._start_devnet()
        self._cli_config = self._write_cli_config(authority)
        self._started = True
        return self.status()

    def _start_local(self, authority: Path) -> None:
        if not _which("solana-test-validator"):
            raise ChainUnavailable(
                "solana-test-validator is not on PATH; the toolchain block the shell profile "
                "installs is what puts it there, so start the CLI from a login shell"
            )
        binary = PROGRAM_BINARIES[self.program]
        if not binary.exists():
            raise ChainUnavailable(
                f"{binary.name} is not built: this gateway deploys a prebuilt program for "
                f"{self.program} and never builds one. Build it once with `cargo-build-sbf` in "
                f"programs/cap_hook, and see BUILD-PROVENANCE.json for which build is which."
            )
        keypair = PROGRAM_KEYPAIRS[self.program]
        if not keypair.exists():
            raise ChainUnavailable(f"no {self.program} program keypair beside the .so at {keypair.name}")
        if threading.current_thread() is not threading.main_thread():
            raise ChainUnavailable(
                "a local validator installs process-global signal handlers, so it can only be "
                "started from the main thread; start the gateway there or run dry"
            )
        shutil.rmtree(self._ledger, ignore_errors=True)  # a leftover is 1.5 GB of another run
        port = _free_port()
        faucet_port = _free_port()
        while faucet_port == port:
            faucet_port = _free_port()
        validator = dp.LocalValidator(
            ledger=self._ledger,
            port=port,
            faucet_port=faucet_port,
            reset=True,  # deletes the ledger on stop
            fund=self._addresses[HOUSE_LABEL],  # genesis funding: the authority pays for setup
        )
        saved = {name: signal.getsignal(getattr(signal, name)) for name in _SIGNALS}
        try:
            validator.start()
        except Exception as exc:  # noqa: BLE001 - every failure here means "no cluster"
            validator.stop()
            raise ChainUnavailable(f"the local validator did not start: {exc}") from exc
        finally:
            for name, handler in saved.items():
                try:
                    signal.signal(getattr(signal, name), handler)
                except (ValueError, OSError):  # not the main thread: nothing to put back
                    pass
        self._validator = validator
        self.rpc_url = validator.rpc_url
        self._drain_validator(validator)
        self._deploy()
        if not self._wait_for_account(self.program_id):
            raise ChainUnavailable(f"the program {self.program_id} is not visible after the deploy")
        if not self._is_executable(self.program_id):
            raise ChainUnavailable(f"the program {self.program_id} deployed but is not executable")

    def _adopt_devnet_authority(self) -> None:
        """Use a wallet the operator already funded. Never creates one, never funds it."""
        named = os.environ.get("MARKET_SWARM_DEVNET_KEYPAIR") or os.environ.get("TP_DEVNET_KEYPAIR")
        if not named:
            raise ChainUnavailable(
                "devnet needs an already funded authority: set MARKET_SWARM_DEVNET_KEYPAIR (or "
                "TP_DEVNET_KEYPAIR) to its path. This gateway does not create or fund one."
            )
        path = Path(named).expanduser()
        if not path.exists():
            raise ChainUnavailable(
                f"no keypair at the path named in MARKET_SWARM_DEVNET_KEYPAIR (expected {path.name})"
            )
        os.chmod(path, 0o600)
        self._keys[HOUSE_LABEL] = path

    def _start_devnet(self) -> None:
        if not self._account_exists(self.program_id):
            raise ChainUnavailable(
                f"the program {self.program_id} is not deployed on devnet; deploy it once with "
                f"tools/devnet_publish.py before running a swarm against this cluster"
            )

    def stop(self) -> None:
        """Kill the validator, its children and the ledger. Idempotent, safe from any exit path."""
        with self._state_lock:
            if self._stopped:
                return
            self._stopped = True
            self._started = False
        try:
            atexit.unregister(self.stop)
        except Exception:  # noqa: BLE001 - unregistering twice is not a failure
            pass
        validator, self._validator = self._validator, None
        if validator is not None:
            try:
                validator.stop()  # killpg on its own process group, then the ledger under reset=True
            except Exception:  # noqa: BLE001 - stopping must never raise
                pass
        drain, self._drain = self._drain, None
        if drain is not None and drain.is_alive():
            drain.join(timeout=2.0)
        shutil.rmtree(self._ledger, ignore_errors=True)
        config, self._cli_config = self._cli_config, None
        if config is not None:
            try:
                config.unlink(missing_ok=True)
            except OSError:
                pass

    # -- events --------------------------------------------------------------

    def create_event(self, spec: EventSpec) -> "EventChain":
        """A mint wired to the hook, a record holding the cap, and the ceiling that follows."""
        self._require_started()
        cap_bps, face = _check_spec(spec)
        mint = self._create_mint(spec)
        program_id = self._program_id()
        record = self._derive_address(program_id, "string:record", f"pubkey:{mint}")
        extra_metas = self._derive_address(
            program_id, "string:extra-account-metas", f"pubkey:{mint}"
        )
        self._init_extra_metas(mint=mint, record=record, extra_metas=extra_metas)
        self._init_record(mint=mint, record=record, face=face, cap_bps=cap_bps, mode=spec.mode)
        observed = self._record_until(record, face=face, cap_bps=cap_bps)
        ceiling = ceiling_lamports(face, cap_bps)
        observed_face, observed_cap = record_face_cap(observed)
        chain = EventChain(
            gateway=self,
            event_id=spec.event_id,
            mint=mint,
            record=record,
            extra_metas=extra_metas,
            mode=spec.mode,
            cap_bps=observed_cap,
            face_lamports=observed_face,
            ceiling_lamports=ceiling,
            artist_fee=getattr(spec, "artist_fee", None),
            flip_tax=getattr(spec, "flip_tax", None),
        )
        with self._state_lock:
            self._events[mint] = chain
        return chain

    def status(self) -> dict:
        with self._state_lock:
            mints = tuple(sorted(self._events))
            started = self._started
        healthy = False
        if started and self.rpc_url:
            try:
                healthy = self._rpc("getHealth", [], timeout=2.0, attempts=1) == "ok"
            except Exception:  # noqa: BLE001 - an unreachable cluster is an answer, not an error
                healthy = False
        return {
            "cluster": self.cluster,
            "program": self.program,
            "program_id": self.program_id,
            "mints": mints,
            "healthy": healthy,
            "simulated": False,
        }

    # -- the seams a fake cluster replaces ----------------------------------

    def _now(self) -> int:
        """The one clock read on the flip-tax path, and the seam a test replaces.

        `held_since_unix` is the validator's wall clock, written by the hook, so the hold is
        `now - held_since` and `now` has to come from somewhere. It is an instance method rather
        than `time.time()` inline so a test can price a one-hour hold without waiting an hour and
        can price a clock that went backwards without changing this machine's clock. Nothing else
        in this module reads it, and no other path calls it: a sale with no tax never asks what
        time it is.
        """
        return int(time.time())

    def _rpc(
        self,
        method: str,
        params: list,
        *,
        timeout: float = _READ_TIMEOUT,
        attempts: int | None = _READ_ATTEMPTS,
    ) -> Any:
        """One JSON-RPC call through the approved bounded reader."""
        return dp.rpc(self.rpc_url, method, params, timeout=timeout, attempts=attempts)

    def _sign(self, keypair_path: Path, message: bytes) -> bytes:
        """Sign in a child process. This process never opens the file.

        `dp.sign_message` runs `tools/solana_sign.py`, hands it the message on stdin and takes
        one base58 signature back; the child is the only reader of key bytes in the system, which
        is the invariant that makes everything above this line stateless with respect to keys.

        A fresh `Context` per call, never a shared one: two mints are allowed to sign at the same
        time, and a shared context whose `keypair` field is assigned before the child reads it is
        the one way this module could sign one agent's transaction with another agent's key.
        """
        context = dp.Context(
            cluster=self.cluster,
            rpc_url=self.rpc_url,
            keypair=keypair_path,
            buyer_keypair=keypair_path,
            out=self.run_dir / "gateway.json",
            progress=None,
        )
        return dp.sign_message(context, message)

    def _run(
        self,
        command: list[str],
        *,
        timeout: float,
        what: str,
        check: bool = True,
        cwd: Path | None = None,
    ) -> str:
        """One bounded child. On failure the message carries the child's tail, nothing else."""
        env = dict(os.environ)
        env["PATH"] = _toolchain_path()
        try:
            completed = subprocess.run(
                command,
                cwd=str(cwd or REPO_ROOT),
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        except FileNotFoundError as exc:
            raise ChainUnavailable(f"{what}: {command[0]} is not on PATH") from exc
        except subprocess.TimeoutExpired as exc:
            raise ChainUnavailable(f"{what}: exceeded its {timeout:g}s bound and was killed") from exc
        output = (completed.stdout or "") + (completed.stderr or "")
        if check and completed.returncode != 0:
            tail = "\n".join(line for line in output.splitlines()[-8:] if line.strip())
            raise ChainUnavailable(f"{what} failed (rc {completed.returncode}):\n{tail}")
        return output

    def _derive_address(self, program_id: str, *seeds: str) -> str:
        """A PDA from the toolchain's own deriver, cached by its inputs."""
        cache_key = (program_id,) + seeds
        cached = self._derive_cache.get(cache_key)
        if cached:
            return cached
        # `dp.derive_address` takes a Context and never reads it: the toolchain derives from the
        # seeds alone. One is kept so the approved signature is satisfied, and nothing is signed.
        if self._ctx is None:
            self._ctx = dp.Context(
                cluster=self.cluster,
                rpc_url=self.rpc_url,
                keypair=self._wallet_path(HOUSE_LABEL),
                buyer_keypair=self._wallet_path(HOUSE_LABEL),
                out=self.run_dir / "gateway.json",
                progress=None,
            )
        address = dp.derive_address(self._ctx, program_id, *seeds)
        if not address:
            raise ChainUnavailable(f"the toolchain derived nothing for {program_id} {seeds}")
        self._derive_cache[cache_key] = address
        return address

    def _account_exists(self, address: str) -> bool:
        """Is this account there, at the commitment every other read here uses.

        Not `dp.account_exists`: that reads `getAccountInfo` at its default, which is
        `finalized`. Measured on this machine against a local validator: a freshly created
        account reads present at `confirmed` in **0.0 s** and absent at `finalized` for about
        **13 s**. Every "already done, or create it" decision in this module therefore reads
        confirmed, or it spends thirteen seconds deciding wrongly and then creates a second
        account.
        """
        result = self._rpc(
            "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}]
        )
        return bool(((result or {}).get("value")))

    def _wait_for_account(self, address: str, *, looks: int = 20, interval: float = 0.75) -> bool:
        """True once the account is visible, at the same commitment as `_account_exists`.

        Same bound as `dp.wait_for_account` (20 looks, 0.75 s apart, 15 s in total) for the same
        reason: a validator answers `getHealth` before it has replayed, and a stale "absent" is a
        second account. The difference is the commitment, which is what made the published helper
        spend its whole budget on this cluster.
        """
        for look in range(looks):
            if self._account_exists(address):
                return True
            if look + 1 < looks:
                time.sleep(interval)
        return False

    def _confirmation(self, signature: str) -> dict:
        return dp.confirm(self.rpc_url, signature, timeout=_CONFIRM_TIMEOUT)

    def _token_balance(self, token_account: str) -> int:
        try:
            result = self._rpc("getTokenAccountBalance", [token_account, {"commitment": "confirmed"}])
        except dp.PublishError as exc:
            if "could not find account" in str(exc).lower() or "invalid param" in str(exc).lower():
                return 0
            raise ChainUnavailable(f"reading the balance of a token account failed: {exc}") from exc
        value = (result or {}).get("value") or {}
        try:
            return int(value.get("amount", 0))
        except (TypeError, ValueError):
            return 0

    def _transaction(self, signature: str) -> dict:
        """Slot, block time and log lines for a signature that landed. Best effort, bounded."""
        for look in range(_LOOKS):
            try:
                result = self._rpc(
                    "getTransaction",
                    [
                        signature,
                        {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 0},
                    ],
                    timeout=10.0,
                    attempts=1,
                )
            except dp.PublishError:
                result = None
            if result:
                meta = result.get("meta") or {}
                return {
                    "slot": result.get("slot"),
                    "block_time": result.get("blockTime"),
                    "logs": tuple(meta.get("logMessages") or ()),
                }
            if look + 1 < _LOOKS:
                time.sleep(_LOOK_INTERVAL)
        return {"slot": None, "block_time": None, "logs": ()}

    # -- transaction assembly ----------------------------------------------

    def _send(
        self,
        instructions: list,
        *,
        payer: str,
        signer_path: Path,
        skip_preflight: bool = False,
    ) -> tuple[str, dict, int]:
        """Compile, sign and send one transaction. Returns `(signature, status, latency_ms)`.

        `skip_preflight=True` is what makes a refusal observable: with the preflight check on, a
        transaction the hook will reject never gets a signature, so there is nothing to point at.
        With it off, the refusal lands as a failed transaction with its own signature and its own
        error, which is the only form of it a sceptic can look up.

        A fresh blockhash every call, never reused: a transaction carrying a dead one is a
        guaranteed failure and a signature printed for it would prove nothing.
        """
        started = time.monotonic()
        blockhash = self._rpc("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
        message = dp.compile_message(payer, list(instructions), blockhash)
        signature = self._sign(signer_path, message)
        wire = base64.b64encode(dp.build_transaction(message, [signature])).decode("ascii")
        try:
            sent = self._rpc(
                "sendTransaction",
                [
                    wire,
                    {"encoding": "base64", "skipPreflight": skip_preflight, "preflightCommitment": "confirmed"},
                ],
            )
        except dp.PublishError as exc:
            # The transaction is signed locally, but the cluster never accepted it: the signature
            # this process holds is one nothing has seen, so it is not reported as if it had landed.
            raise _Rejected(str(exc)) from exc
        try:
            status = self._confirmation(sent)
        except dp.PublishError as exc:
            # Sent, and not confirmed inside the bound. It may still land, so the signature is
            # returned with the doubt attached rather than dropped: a lost signature is how a
            # landed transfer turns into a second transfer.
            status = {"ok": False, "err": None, "slot": None, "unconfirmed": True, "detail": str(exc)}
        latency = int(round((time.monotonic() - started) * 1000))
        return sent, status, latency

    def _send_multi(
        self,
        instructions: list,
        *,
        payer: str,
        signer_paths: dict[str, Path],
        skip_preflight: bool = False,
    ) -> tuple[str, dict, int]:
        """Compile, sign with every required signer, send. `(signature, status, latency_ms)`.

        A second method rather than a widening of `_send`, because `_send` is on the path of every
        transaction this harness built before the artist fee existed and its shape is part of that
        path's correctness. This one exists for the one sale that has two signatures: the seller
        pays and authorises the move, and the issuer signs the stage instruction, because the
        record's authority is the issuer and `checked_record_for_write` requires its signature.

        The signer set is **read back out of the compiled message**, never assumed. `signer_paths`
        maps an address to the keypair path this process holds for it, `dp.compile_message` decides
        which of the accounts in these instructions must sign and in what order, and the two sets
        have to agree exactly: a missing entry would leave a required signature empty and an extra
        one would write a signature the message has no room for, and either is a bug worth a hard
        error that names both sides. Signatures are positional, so they are produced in the
        message's own order and not in the dict's.

        The submit half is deliberately the same sequence as `_send`'s: a fresh blockhash every
        call, `skipPreflight` only when a refusal has to be observable, a preflight rejection
        raised as `_Rejected` (nothing was sent, so no signature is reported), and a send that did
        not confirm returned with the doubt attached rather than dropped.
        """
        started = time.monotonic()
        blockhash = self._rpc("getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
        message = dp.compile_message(payer, list(instructions), blockhash)
        required = signer_keys_from_message(message)
        missing = [key for key in required if key not in signer_paths]
        extra = [key for key in signer_paths if key not in required]
        if missing or extra:
            raise ChainUnavailable(
                "signers: this transaction needs exactly "
                f"[{', '.join(required)}] and the call holds [{', '.join(sorted(signer_paths))}]; "
                f"no keypair path for {missing or 'nothing'} and a path for {extra or 'nothing'} "
                "the message does not ask to sign"
            )
        signatures = [self._sign(signer_paths[key], message) for key in required]
        wire = base64.b64encode(dp.build_transaction(message, signatures)).decode("ascii")
        try:
            sent = self._rpc(
                "sendTransaction",
                [
                    wire,
                    {"encoding": "base64", "skipPreflight": skip_preflight, "preflightCommitment": "confirmed"},
                ],
            )
        except dp.PublishError as exc:
            raise _Rejected(str(exc)) from exc
        try:
            status = self._confirmation(sent)
        except dp.PublishError as exc:
            status = {"ok": False, "err": None, "slot": None, "unconfirmed": True, "detail": str(exc)}
        latency = int(round((time.monotonic() - started) * 1000))
        return sent, status, latency

    def _send_or_raise(self, instructions: list, *, payer: str, signer_path: Path) -> str:
        """A setup transaction, where anything short of a confirmed success is a failure."""
        try:
            signature, status, _ = self._send(instructions, payer=payer, signer_path=signer_path)
        except _Rejected as exc:
            raise ChainUnavailable(f"the cluster refused a setup transaction: {exc}") from exc
        if not status.get("ok"):
            detail = status.get("detail") or dp.describe_error(status.get("err"))
            raise ChainUnavailable(f"a setup transaction did not succeed: {detail} ({signature})")
        return signature

    # -- wallets -----------------------------------------------------------

    def _wallet_path(self, label: str) -> Path:
        """Where a label's keypair lives, generated on first use at 0600 if it is not there."""
        _require_label(label)
        with wallet_lock(label):
            return self._wallet_path_locked(label)

    def _wallet_path_locked(self, label: str) -> Path:
        existing = self._keys.get(label)
        if existing is not None:
            return existing
        path = self._keys_dir / f"{label}.json"
        if not path.exists():
            self._keys_dir.mkdir(parents=True, exist_ok=True)
            if not _which("solana-keygen"):
                raise ChainUnavailable("solana-keygen is not on PATH, so no wallet can be made")
            # check=False and a message that names the file, not the output: `new` without
            # --silent prints a recovery phrase, and no failure of this call may echo it.
            output = self._run(
                [_which("solana-keygen"), "new", "--silent", "--no-bip39-passphrase", "-o", str(path)],
                timeout=_BOUND_KEYGEN,
                what="solana-keygen new",
                check=False,
            )
            if not path.exists():
                raise ChainUnavailable(f"solana-keygen new produced no keypair named {path.name}")
            try:
                address = _last_address(output)
            except Exception:  # noqa: BLE001 - the address is asked for again below
                address = None
            if address:
                self._addresses.setdefault(label, address)
        os.chmod(path, 0o600)
        self._keys[label] = path
        return path

    def _wallet_address(self, label: str) -> str:
        """A label's public address, from `solana-keygen pubkey`: a string, never the file."""
        cached = self._addresses.get(label)
        if cached is not None:
            return cached
        path = self._wallet_path(label)
        output = self._run(
            [_which("solana-keygen"), "pubkey", str(path)],
            timeout=_BOUND_PUBKEY,
            what="solana-keygen pubkey",
        )
        address = _last_address(output)
        if not address:
            raise ChainUnavailable(f"solana-keygen pubkey printed no address for {path.name}")
        self._addresses[label] = address
        return address

    def _ensure_wallet(self, label: str, *, fee_lamports: int = 0) -> str:
        """The label's address, funded and usable as a fee payer. Idempotent per run.

        `fee_lamports` is a payment this wallet also has to make out of its own balance in the
        action that follows -- the artist fee on a resale. When one is named the floor becomes
        `max(WALLET_FLOOR_LAMPORTS, fee + WALLET_FLOOR_LAMPORTS)`, and the top-up reaches at least
        that floor rather than the plain per-wallet amount.

        The reason is that the floor is not a spending target, it is the float a wallet needs to
        pay its own signatures. Topping a wallet up to the floor alone and then taking a fee out of
        it leaves the seller holding the fee's worth of nothing, so the sale after next fails with
        an `InsufficientFunds` from the System Program -- an error that reads like a chain fault
        and is really a funding decision made one step earlier. Funding `fee + floor` means the fee
        is paid out of money that was added for it, and the float survives the sale.

        It stays a floor and not a target: a wallet already holding the fee is left alone, and a
        wallet with no fee to pay is treated exactly as it was before the fee existed.
        """
        _require_label(label)
        if isinstance(fee_lamports, bool) or not isinstance(fee_lamports, int) or fee_lamports < 0:
            raise ValueError(f"fee_lamports: expected a non-negative integer, got {fee_lamports!r}")
        floor = max(WALLET_FLOOR_LAMPORTS, fee_lamports + WALLET_FLOOR_LAMPORTS)
        with wallet_lock(label):
            address = self._wallet_address(label)
            if label == HOUSE_LABEL:
                return address  # funded at genesis; a transfer to itself would waste a fee
            funded = self._balance(address)
            if funded >= floor:
                return address
            self._fund_wallet(address, max(FUND_LAMPORTS_PER_WALLET, floor) - funded)
            return address

    def _balance(self, address: str) -> int:
        result = self._rpc("getBalance", [address, {"commitment": "confirmed"}])
        return int((result or {}).get("value") or 0)

    def _fund_wallet(self, address: str, lamports: int) -> None:
        """One System Program transfer from the authority. The only funding path here."""
        if lamports <= 0:
            return
        authority = self._wallet_address(HOUSE_LABEL)
        instruction = system_transfer_instruction(
            source=authority, destination=address, lamports=lamports
        )
        self._send_or_raise(
            [instruction], payer=authority, signer_path=self._wallet_path(HOUSE_LABEL)
        )

    # -- mint and record ---------------------------------------------------

    def _create_mint(self, spec: EventSpec) -> str:
        """The Token-2022 mint: 0 decimals, the transfer hook, and a metadata pointer.

        Zero decimals is not stylistic: finding 18 F2 records `6010` masked by `6008` because the
        mint defaulted to 9 and "1 token" became 10**9 base units. `--enable-metadata` is what
        installs the MetadataPointer extension; `initialize-metadata` is deliberately not called,
        because nothing the gateway reads needs the metadata body and it is another transaction.
        """
        keypair = self._keys_dir / f"{spec.event_id}_mint.json"
        if not keypair.exists():
            self._keys_dir.mkdir(parents=True, exist_ok=True)
            if not _which("solana-keygen"):
                raise ChainUnavailable("solana-keygen is not on PATH, so no mint can be made")
            self._run(
                [_which("solana-keygen"), "new", "--silent", "--no-bip39-passphrase", "-o", str(keypair)],
                timeout=_BOUND_KEYGEN,
                what="solana-keygen new (mint)",
            )
        os.chmod(keypair, 0o600)
        mint = self._pubkey_of(keypair)
        if self._account_exists(mint):
            return mint  # a rerun against a kept ledger, or a second create_event for one spec
        try:
            self._run(
                self._spl(
                    "create-token",
                    "--decimals", "0",
                    "--transfer-hook", self._program_id(),
                    "--enable-metadata", str(keypair),
                ),
                timeout=_BOUND_CLI,
                what="spl-token create-token",
            )
        except ChainUnavailable:
            if self._wait_for_account(mint):
                return mint  # the account is there: the failure was the CLI's stale negative
            raise
        if not self._wait_for_account(mint):
            raise ChainUnavailable(f"the mint {mint} is not visible after create-token")
        return mint

    def _init_extra_metas(self, *, mint: str, record: str, extra_metas: str) -> None:
        if self._account_exists(extra_metas):
            return
        authority = self._wallet_address(HOUSE_LABEL)
        instruction = wire.instruction_init_extra_metas(
            self.program,
            payer=authority,
            mint=mint,
            extra_metas=extra_metas,
            record=record,
            program_id=self._program_id(),
        )
        try:
            self._send_or_raise(
                [instruction], payer=authority, signer_path=self._wallet_path(HOUSE_LABEL)
            )
        except ChainUnavailable:
            if not self._wait_for_account(extra_metas):
                raise  # the account is not there either, so the failure stands
        if not self._wait_for_account(extra_metas):
            raise ChainUnavailable(f"{extra_metas} is not visible after initialising it")

    def _init_record(self, *, mint: str, record: str, face: int, cap_bps: int, mode: str) -> None:
        if self._account_exists(record):
            return
        authority = self._wallet_address(HOUSE_LABEL)
        instruction = wire.instruction_init_record(
            self.program,
            payer=authority,
            mint=mint,
            record=record,
            program_id=self._program_id(),
            face=face,
            cap_bps=cap_bps,
            # v2 stores the policy byte and requires the mint's authority to sign, which is the
            # key that already pays for setup here. v1 ignores both; `wire` refuses them missing.
            mint_authority=authority,
            mode=mode,
        )
        try:
            self._send_or_raise(
                [instruction], payer=authority, signer_path=self._wallet_path(HOUSE_LABEL)
            )
        except ChainUnavailable:
            if not self._wait_for_account(record):
                raise  # the account is not there either, so the failure stands
        if not self._wait_for_account(record):
            raise ChainUnavailable(f"{record} is not visible after initialising it")

    def _record_until(self, record: str, *, face: int, cap_bps: int) -> dict:
        """The record, once it reads what was asked for.

        `initialize_record` returns `Ok(())` on a non-empty account, so a second call with a
        different face or cap is silently ignored rather than refused. Reading back what landed is
        therefore the only way to know the record is the one the spec asked for, and a mismatch is
        named here instead of becoming a wrong ceiling later.
        """
        observed: dict = {}
        for look in range(_LOOKS * 2):
            try:
                observed = self._read_record(record)
            except ChainUnavailable:
                observed = {}  # not visible yet: the same "absent" a replay shows
            observed_face, observed_cap = record_face_cap(observed)
            if observed_face == face and observed_cap == cap_bps:
                return observed
            if look + 1 < _LOOKS * 2:
                time.sleep(_LOOK_INTERVAL)
        observed_face, observed_cap = record_face_cap(observed)
        raise ChainUnavailable(
            f"the record {record} reads face={observed_face} "
            f"cap_bps={observed_cap}, the spec asked for face={face} cap_bps={cap_bps}"
        )

    def _read_record(self, record: str) -> dict:
        # `commitment: confirmed` is not optional. `getAccountInfo` defaults to `finalized`, so a
        # write that is confirmed but not yet finalized reads back as its *old* value -- measured
        # here: the staged price read as 0 immediately after a transfer that had just used it.
        # Finding 21 G3 records the same default costing a landed transaction.
        result = self._rpc(
            "getAccountInfo", [record, {"encoding": "base64", "commitment": "confirmed"}]
        )
        value = (result or {}).get("value")
        if not value:
            raise ChainUnavailable(f"the record {record} is not on chain")
        encoded = value.get("data") or ["", "base64"]
        try:
            data = base64.b64decode(encoded[0])
        except (ValueError, TypeError) as exc:
            raise ChainUnavailable(f"the record {record} did not arrive as base64") from exc
        return wire.decode_record(self.program, data)

    def _read_record_v2(self, record: str) -> bytes:
        """The raw bytes of a v2 `["record", mint]` account, read at `confirmed`.

        The same `getAccountInfo` call and the same commitment as `_read_record`, differing only
        in what comes back: the bytes, not a decoded dict. `decode_record` reads the 19-byte v1
        layout, so it cannot serve this path -- a v2 record is 70 bytes and the hook's clock sits
        at byte 30 -- and neither function is changed here: the v1 read and decoder are another
        run's repair (finding 42 §6). This is the reader the flip-tax path needs, and it is
        deliberately the only place that unpacks the account, so the byte offset has one owner
        (`flip_tax.held_since_unix_from_record`) and one reader.

        Raises `ChainUnavailable` when the account is absent or does not arrive as base64, which
        is the fail-closed rule for the tax: a sale whose hold cannot be read is not built, and no
        transaction is signed.
        """
        result = self._rpc(
            "getAccountInfo", [record, {"encoding": "base64", "commitment": "confirmed"}]
        )
        value = (result or {}).get("value")
        if not value:
            raise ChainUnavailable(f"the record {record} is not on chain")
        encoded = value.get("data")
        if not isinstance(encoded, list) or len(encoded) < 2 or encoded[1] != "base64":
            raise ChainUnavailable(f"the record {record} did not arrive as base64")
        try:
            return base64.b64decode(encoded[0])
        except (ValueError, TypeError) as exc:
            raise ChainUnavailable(f"the record {record} did not arrive as base64") from exc

    # -- small readers -----------------------------------------------------

    def _program_id(self) -> str:
        if self.program_id is None:
            raise ChainUnavailable("no program id: start() did not complete")
        return self.program_id

    def _program_id_from_disk(self) -> str:
        """The id the selected program deploys at, derived from its own keypair and checked.

        Two programs share one `target/deploy` directory, and the id is what decides which program
        a run is talking to, so the keypair follows the program rather than whichever file is
        first. `dp.PROGRAM_KEYPAIR` is v1's, whose pubkey is the frozen devnet address; v2's is the
        keypair `tools/publish_v2.py` deploys with. A keypair that derives some third address is a
        refusal: the run would otherwise deploy to an id nobody named and report the other
        program's answers under this one's name.
        """
        keypair = PROGRAM_KEYPAIRS[self.program]
        expected = PROGRAM_IDS[self.program]
        if not keypair.exists():
            raise ChainUnavailable(
                f"no {self.program} program keypair at {keypair.name} beside the .so, so the "
                f"program id cannot be derived; the build that produces both was never run here"
            )
        derived = self._pubkey_of(keypair)
        if derived != expected:
            raise ChainUnavailable(
                f"the keypair at {keypair.name} derives {derived}, and {self.program} is "
                f"{expected}: refusing to deploy a program at an id the run did not name"
            )
        return derived

    def _pubkey_of(self, path: Path) -> str:
        output = self._run(
            [_which("solana-keygen"), "pubkey", str(path)],
            timeout=_BOUND_PUBKEY,
            what="solana-keygen pubkey",
        )
        address = _last_address(output)
        if not address:
            raise ChainUnavailable(f"solana-keygen pubkey printed no address for {path.name}")
        return address

    def _is_executable(self, address: str) -> bool:
        result = self._rpc(
            "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}]
        )
        return bool(((result or {}).get("value") or {}).get("executable"))

    def _deploy(self) -> None:
        """`solana program deploy` of the .so and keypair this program's name names. No build.

        Both halves follow `self.program` and not whichever pair happens to be at hand: deploying
        v2's bytecode under v1's keypair puts one program at the other's address, and the run then
        waits for an account at an id nothing was deployed to. Before this followed the name, a v2
        run that got past `start()` would have deployed v1's id and failed on that wait.
        """
        program_id = self._program_id()
        self._run(
            [
                _which("solana") or "solana",
                "--url", self.rpc_url,
                "program", "deploy", str(PROGRAM_BINARIES[self.program]),
                "--program-id", str(PROGRAM_KEYPAIRS[self.program]),
                "--keypair", str(self._wallet_path(HOUSE_LABEL)),
            ],
            timeout=_BOUND_DEPLOY,
            what="solana program deploy",
        )

    def _write_cli_config(self, authority: Path) -> Path:
        """A throwaway `spl-token` config naming the keypair by path. It never holds the key."""
        path = self.run_dir / "spl-token.yml"
        path.write_text(
            f"json_rpc_url: {self.rpc_url}\n"
            'websocket_url: ""\n'
            f"keypair_path: {authority}\n"
            "commitment: confirmed\n",
            encoding="utf-8",
        )
        os.chmod(path, 0o600)
        return path

    def _spl(self, *args: str) -> list[str]:
        """The `spl-token` command line, every signer named so no verb has to guess one."""
        if self._cli_config is None:
            raise ChainUnavailable("spl-token is only usable after start()")
        return [
            _which("spl-token") or "spl-token",
            "--url", self.rpc_url,
            "--config", str(self._cli_config),
            "--fee-payer", str(self._wallet_path(HOUSE_LABEL)),
            "--program-2022",
            *args,
        ]

    def _drain_validator(self, validator: Any) -> None:
        """Keep the validator's pipe empty, into a file with a ceiling.

        `LocalValidator` starts the node with `stdout=PIPE` and reads that pipe only after the
        process has exited. A long run that trips one log line per transaction can fill the kernel
        buffer and block the node mid-transaction, so the pipe is drained here instead -- bounded
        in bytes, so a runaway log cannot fill the disk either.
        """
        stream = getattr(validator.process, "stdout", None)
        if stream is None:
            return
        target = self.run_dir / "validator.log"

        def pump() -> None:
            written = 0
            try:
                with target.open("w", encoding="utf-8", errors="replace") as log:
                    for line in stream:
                        if written >= _LOG_CAP_BYTES:
                            continue  # keep draining, stop writing
                        log.write(line)
                        written += len(line)
            except (OSError, ValueError):
                return

        thread = threading.Thread(target=pump, name="validator-log", daemon=True)
        thread.start()
        self._drain = thread

    def _require_started(self) -> None:
        if not self._started:
            raise ChainUnavailable("the gateway is not started: call start() first")


# -- one event ---------------------------------------------------------------


class EventChain:
    """One mint, one record, one mode. Every attribute here is public and holds no key."""

    def __init__(
        self,
        *,
        gateway: ChainGateway,
        event_id: str,
        mint: str,
        record: str,
        extra_metas: str,
        mode: str,
        cap_bps: int,
        face_lamports: int,
        ceiling_lamports: int,
        artist_fee: ArtistFeePolicy | None = None,
        flip_tax: FlipTaxPolicy | None = None,
    ) -> None:
        self._gateway = gateway
        self.event_id = event_id
        self.mint = mint
        self.record = record
        self.extra_metas = extra_metas
        self.mode = mode
        self.cap_bps = cap_bps
        self.face_lamports = face_lamports
        self.ceiling_lamports = ceiling_lamports
        #: The event's fee policy, carried from the spec. `None` is the whole of "no fee":
        #: every branch below that mentions the fee asks this first, and a chain built
        #: without one executes the sale it always did, instruction for instruction.
        self.artist_fee = artist_fee
        #: The event's flip tax policy, carried from the spec the same way. `None` and a policy
        #: whose `enabled` is false are the same thing to every branch below: no tax is read, no
        #: record is fetched for it, and the sale is the one this file built before the tax
        #: existed. A policy that is present and on is the only case that reads the clock.
        self.flip_tax = flip_tax
        # The third door onto the combined-take rule. `create_event` goes through `_check_spec`, and
        # the loader goes through its own parse, but this class is public and review constructed one
        # directly, so the refusal is repeated here rather than assumed upstream.
        _refuse_combined_take(artist_fee, flip_tax, where="EventChain")

    simulated = False

    def __repr__(self) -> str:  # a review reads this, so it names only public identifiers
        return (
            f"EventChain(event_id={self.event_id!r}, mint={self.mint!r}, record={self.record!r}, "
            f"mode={self.mode!r}, cap_bps={self.cap_bps}, face_lamports={self.face_lamports}, "
            f"ceiling_lamports={self.ceiling_lamports}, artist_fee={self.artist_fee!r}, "
            f"flip_tax={self.flip_tax!r})"
        )

    # -- wallets -----------------------------------------------------------

    def open_account(self, wallet_label: str) -> str:
        """Make `label` a usable trader: a funded wallet and its token account. Returns the address.

        The public address, never the key: the path stays inside the gateway, and the only process
        that reads the file is the signer child.
        """
        address = self._gateway._ensure_wallet(wallet_label)
        self.ticket_account(wallet_label, create=True)
        return address

    def ticket_account(self, wallet_label: str, *, create: bool = False) -> str:
        """The associated token account for (wallet, mint), derived by the toolchain."""
        address = self._gateway._wallet_address(wallet_label)
        cached = self._gateway._ata.get((self.mint, address))
        if cached is not None:
            return cached
        ata = self._gateway._derive_address(
            dp.ASSOCIATED_TOKEN_PROGRAM,
            f"pubkey:{address}",
            f"pubkey:{dp.TOKEN_2022_PROGRAM}",
            f"pubkey:{self.mint}",
        )
        if create and not self._gateway._account_exists(ata):
            try:
                self._gateway._run(
                    self._gateway._spl("create-account", self.mint, "--owner", address),
                    timeout=_BOUND_CLI,
                    what="spl-token create-account",
                )
            except ChainUnavailable:
                if not self._gateway._wait_for_account(ata):
                    raise  # the account really is not there; the failure stands
            if not self._gateway._wait_for_account(ata):
                raise ChainUnavailable(f"the token account {ata} is not visible after creating it")
        self._gateway._ata[(self.mint, address)] = ata
        return ata

    # -- supply ------------------------------------------------------------

    def stock(self, count: int) -> None:
        """Mint `count` tickets to the house, and prove the balance moved by exactly that.

        The delta check is the finding-18 F2 lesson turned into a test at runtime: a mint with the
        wrong decimals turns "2 tickets" into 2 * 10**9 base units, and a stale balance read makes
        a second call mint a third ticket. Both are caught here rather than after a refused
        transfer that looks like a cap problem.
        """
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"count: expected a non-negative integer, got {count!r}")
        if count == 0:
            return
        self._gateway._ensure_wallet(HOUSE_LABEL)
        account = self.ticket_account(HOUSE_LABEL, create=True)
        before = self._gateway._token_balance(account)
        self._gateway._run(
            self._gateway._spl("mint", self.mint, str(count), account),
            timeout=_BOUND_CLI,
            what="spl-token mint",
        )
        after = self._gateway._token_balance(account)
        if after - before != count:
            raise ChainUnavailable(
                f"stocking {self.event_id} asked for {count} tickets and the house balance went "
                f"from {before} to {after}, so a ticket is not one base unit on this mint"
            )

    # -- trade -------------------------------------------------------------

    def transfer(
        self,
        *,
        from_label: str,
        to_label: str,
        price_lamports: int,
        charge_artist_fee: bool = True,
        charge_flip_tax: bool = True,
    ) -> TransferResult:
        """Stage a price and move one ticket, in one transaction.

        One signature and two instructions on an event with no fee -- two signatures on a v2 run,
        where the stage is authorised by the record's authority and the seller is not that key; two
        signatures and three on an event that pays an artist. Either way it is one transaction, and
        the seller pays for it.

        The two instructions are `SetPendingPrice` and the Token-2022 `TransferChecked`; they share
        the record, the seller signs the move and -- on v1, where the stage reads no signer -- the
        stage as well. On a v2 run the stage carries the house's signature instead, because the
        record's authority is the mint's authority and `_init_record` signed that as the house.
        Nothing between them can move the staged price, because there is nothing between them: the
        transaction is atomic, and if the hook refuses, the staging is rolled back with it.

        **With an artist fee** -- an event whose spec named one -- a third instruction sits between
        them, and the stage is the v2 shape so the issuer signs it, because the record's authority
        is the issuer. The middle leg is a System `Transfer` of `price * fee_bps // 10_000` lamports
        from the seller to the artist, and the move takes the seller's signature on the token
        account. The order is stage, fee, move, on one blockhash: a leg that fails fails the sale
        and rolls the staging back with it. The fee leg is built by
        `artist_fee.sale_instructions`, which omits it when the fee rounds to zero, and it refuses
        a sale it cannot build (a price of 0, the artist being the seller) before a blockhash is
        asked for. The move on this path also passes the record writable: v2's hook writes it and
        Token-2022 asks for it writable, so a message that only ever names it read-only is refused
        `PrivilegeEscalation` before the hook runs. The stage in this transaction already says so,
        which makes the move's flag redundant here and correct if the shape changes.

        `charge_artist_fee=False` builds that sale without the middle leg and pays the artist
        nothing: the primary price is the artist's own money, and the fee is specified on a resale.
        The event's rate still reaches the row, so a reader can see the rate and that this sale paid
        none of it.

        **With a flip tax** -- an event whose spec named an *enabled* one -- a fourth instruction
        joins them and the order is stage, artist fee, flip tax, move. The tax leg is a System
        `Transfer` from the seller to the artist wallet, built by
        `flip_tax.sale_instructions`, which omits it when the tax rounds to zero exactly as the
        fee leg is omitted. The rate falls with the hold, and the hold is read from the v2 record
        before anything is funded or signed: the gateway fetches the record's bytes,
        `flip_tax.held_since_unix_from_record` decodes the hook's clock at its offset, and the tax
        is `price * bps // 10_000` for the hold that the record and `_now()` agree on.
        `held_since_unix == 0` means the record's clock was never written and is charged the full
        rate, with `held_seconds` reported as `None` so the row says why.

        **A record that cannot be read is `ChainUnavailable` and nothing is signed.** That is the
        fail-closed rule: a hold nobody read cannot price a tax, and refusing the sale is the
        honest answer. The read happens before the funding top-up, before a blockhash is fetched
        and before a signature exists, so a tax path that fails leaves no transaction behind.

        `charge_flip_tax=False` builds the sale without the tax leg: the tax, like the fee, is on
        resales, and a primary sale is the house selling the artist's own stock at face. The event's
        policy still decides the record shape, so such a sale is the v2 stage and the writable move
        with nothing between them -- the same instructions an artist-fee event's primary sale
        builds with `charge_artist_fee=False`, and the reason a taxed event can stage its own
        record from its first sale. An event with no block, or a block that is off, executes every
        instruction it executed before the tax existed.

        Without a fee **and** without a tax this method builds the per-program encoders: v1's stage
        and `dp`'s read-only move on a v1 run, v2's stage and its writable move on a v2 run, so the
        switch reaches the plain sale and not only the fee path. The v2 stage there is signed by
        the house and the move by the seller, and those are the two keys the transaction is signed
        with; the v1 pair is one signature, unchanged. A fee or tax event takes the v2
        shapes whatever the program is, because the record those paths write is a v2 record; that
        is why the v1 branch above is exactly the branch with neither. The v2 record that the tax
        is priced from is read raw by `_read_record_v2` because `decode_record` reads the 19-byte
        v1 layout -- disclosed in `records/findings/42-artist-fee-at-checkout.md` §6 and another
        run's repair.

        `fee_lamports` on the result is what was paid, so it is `0` for anything that did not land:
        a refused or unconfirmed send reports nothing paid, and a row that reported a fee it did not
        observe would name a payment nobody can look up. `flip_tax_lamports` follows the same rule
        and `flip_tax_bps`/`held_seconds` are reported anyway on a taxed sale, so a row shows the
        rate that was applied beside the 0 that says the sale did not move it. The artist is still
        owed the fee on a sale that lands later; the log line says the transaction may still land,
        which is the part of it this result cannot know.

        Never raises for a refusal -- a refusal is a `TransferResult` with `status="refused"` and
        the program's own error code. It raises `TicketNotHeld` when the seller has no ticket,
        because that must not read as the hook refusing a trade that never reached it.
        """
        price = _require_price(price_lamports)
        gateway = self._gateway
        source = self.ticket_account(from_label)
        held = gateway._token_balance(source)
        if held < 1:
            raise TicketNotHeld(
                f"{from_label} holds {held} tickets on {self.event_id} ({source}); a transfer needs "
                f"1, and a ticket has to be stocked before it can be sold"
            )
        destination = self.ticket_account(to_label, create=True)
        # The flip tax, when this event has one that is on and this sale carries it. Everything
        # about it happens before the seller is funded, before a blockhash is fetched and before
        # anything can be signed: the hold is a fact the chain already holds, and a hold nobody
        # could read is a `ChainUnavailable` rather than a sale priced off a guess. `taxing` is
        # false on every event without a block, on a block that is off and on a primary sale, and
        # every branch below that asks about the tax asks this first.
        #
        # Two conditions, separated on purpose. `taxed_event` decides the *record shape*: an event
        # that turns the tax on is a v2-record event, so its stage and its move are v2 even on a
        # sale that pays no tax (a primary sale, `charge_flip_tax=False`), exactly as an
        # artist-fee event's primary sale still stages v2 with `charge_artist_fee=False`. `taxing`
        # decides the *payment*: the record read, the tax leg, the log line and the result fields
        # exist only on a sale that carries the tax. Deciding the shape by the flag as well would
        # leave a taxed event whose primary sale cannot stage its own record, which is the one
        # thing the v2 branch exists to prevent.
        taxed_event = self.flip_tax is not None and self.flip_tax.enabled
        taxing = taxed_event and charge_flip_tax
        tax = None
        held_since = UNKNOWN_HOLD
        now_unix = 0
        if taxing:
            tax_record = gateway._read_record_v2(self.record)  # ChainUnavailable: fail closed
            try:
                held_since = held_since_unix_from_record(tax_record)
            except FlipTaxError as exc:
                # A record that is on chain and too short to hold the hook's clock is a record
                # this checkout cannot price a tax from. It is the same refusal as an absent
                # record, and it is raised before the funding top-up below, so no transaction
                # and no signature exists when it fires.
                raise ChainUnavailable(
                    f"the record {self.record} cannot be read for the flip tax: {exc}"
                ) from exc
            now_unix = gateway._now()
            tax = assess_flip_tax(
                price_lamports=price,
                held_since_unix=held_since,
                now_unix=now_unix,
                schedule=self.flip_tax.schedule,
            )
        tax_lamports = 0 if tax is None else tax.lamports
        # 0 when the event has no fee policy or this sale does not carry one, and then the funding
        # decision below is the one it always was: `max(floor, 0 + floor)` is the floor. A primary
        # sale is the second case, because the fee is charged on resales: the house is selling the
        # artist's own ticket at the artist's own price, so a fee there would be the artist paying
        # themselves.
        charging = self.artist_fee is not None and charge_artist_fee
        fee = (
            0
            if not charging
            else fee_lamports(price_lamports=price, fee_bps=self.artist_fee.fee_bps)
        )
        # Funded for both payments it has to make out of this sale, or it cannot pay its own fee:
        # `fee + 0` is the number this call was given before the tax existed.
        gateway._ensure_wallet(from_label, fee_lamports=fee + tax_lamports)
        seller_path = gateway._wallet_path(from_label)  # a path for the signer child only
        seller_address = gateway._wallet_address(from_label)
        program_id = gateway._program_id()
        # The house key, resolved only on a v2 run. v2's stage is authorised by the record's
        # authority, and `InitializeRecord` pinned that to the mint authority `_init_record` signs
        # as -- the house -- so a v2 sale has to carry that signature beside the seller's. v1's
        # stage reads no signer at all, and a v1 run must not so much as resolve this key.
        house_address = gateway._wallet_address(HOUSE_LABEL) if gateway.program == "v2" else None
        admitted = cap_admits(
            price_lamports=price, face_lamports=self.face_lamports, cap_bps=self.cap_bps
        )
        if self.artist_fee is None and not taxed_event:
            stage = wire.instruction_set_pending_price(
                gateway.program,
                record=self.record,
                program_id=program_id,
                price=price,
                # v2 reads a signer here and refuses 6026 for a key that is not the record's
                # authority, which is the house and not the seller: this argument is why a v2 sale
                # is signed twice. v1's encoder takes neither and reads no signer.
                authority=house_address,
                mint=self.mint,
            )
        else:
            # The v2 stage on the taxed path for the same reason as on the fee path: the deployed
            # program's `checked_record_for_write` requires `record.authority` to have signed, and
            # the v1 encoder sends one account with no authority and cannot stage a v2 record at
            # all. A taxed event must be able to stage and move one even when it charges no fee,
            # so the branch that fell back to the v1 builders is the branch with neither.
            stage = instruction_set_pending_price_v2(
                authority=gateway._wallet_address(HOUSE_LABEL),
                record=self.record,
                mint=self.mint,
                program_id=program_id,
                price=price,
            )
        # The move. The taxed and fee paths build it with `instruction_transfer_checked_writable`,
        # which is `dp.instruction_transfer_checked` with the record passed writable so the hook
        # can write it; the path with neither keeps the per-program builder, which is v1's
        # published one on a v1 run and v2's writable one on a v2 run.
        if self.artist_fee is None and not taxed_event:
            move = wire.instruction_transfer_checked(
                gateway.program,
                source=source,
                mint=self.mint,
                destination=destination,
                authority=seller_address,
                record=self.record,
                hook_program=program_id,
                extra_metas=self.extra_metas,
                amount=1,
                decimals=0,
            )
        else:
            move = instruction_transfer_checked_writable(
                source=source,
                mint=self.mint,
                destination=destination,
                authority=seller_address,
                record=self.record,
                hook_program=program_id,
                extra_metas=self.extra_metas,
                amount=1,
                decimals=0,
            )
        # Built before the lock and before any blockhash: a sale the checkout refuses is refused
        # here, not after a signature exists.
        legs: tuple = ()
        if taxing:
            legs = tax_sale_instructions(
                stage=stage,
                move=move,
                seller=seller_address,
                policy=self.flip_tax,
                price_lamports=price,
                held_since_unix=held_since,
                now_unix=now_unix,
                # The fee half is the fee module's to build, and a sale that says
                # `charge_artist_fee=False` must not carry one: passing `None` is how this path
                # asks for the tax leg and nothing else.
                artist_fee=self.artist_fee if charging else None,
            )
        elif self.artist_fee is not None and charge_artist_fee:
            legs = sale_instructions(
                stage=stage,
                move=move,
                seller=seller_address,
                artist_wallet=self.artist_fee.artist_wallet,
                price_lamports=price,
                fee_bps=self.artist_fee.fee_bps,
            )
        # Anything else is the stage and the move with nothing between them -- a taxed event's
        # primary sale, a fee event's, or both -- and `sale_instructions` is not asked about it.
        # One line a log reader can act on: the amount, the rate it was taken at and the hold that
        # chose the rate, in the same voice as the lines below. It says the leg was built into the
        # transaction and not that it was paid -- the money is `flip_tax_lamports` on the result,
        # and the tax leg rolls back with everything else when the sale does not land.
        tax_log: tuple[str, ...] = ()
        if taxing:
            held_text = "unknown" if tax.held_seconds is None else f"{tax.held_seconds}s"
            tax_log = (
                f"ticketpath: flip tax {tax.lamports} lamports at {tax.bps} bps of {price}, held "
                f"{held_text}, built into the same transaction as the move",
            )
        with mint_lock(self.mint):
            started = time.monotonic()
            try:
                if self.artist_fee is None and not taxed_event and gateway.program == "v2":
                    # Two keys on a plain v2 sale, and `_send_multi` reads the required set back
                    # out of the compiled message before either is used: a message that asks for
                    # one signer and not the other is refused there rather than sent half-signed.
                    signature, status, _ = gateway._send_multi(
                        [stage, move],
                        payer=seller_address,
                        signer_paths={
                            seller_address: seller_path,
                            house_address: gateway._wallet_path(HOUSE_LABEL),
                        },
                        skip_preflight=not admitted,
                    )
                elif self.artist_fee is None and not taxed_event:
                    # v1: one account on the stage, no signer, so one signature -- the path every
                    # sale in this harness took before v2 could run.
                    signature, status, _ = gateway._send(
                        [stage, move], payer=seller_address, signer_path=seller_path,
                        skip_preflight=not admitted,
                    )
                else:
                    signature, status, _ = gateway._send_multi(
                        list(legs) if legs else [stage, move],
                        payer=seller_address,
                        signer_paths={
                            seller_address: seller_path,
                            # The issuer's keypair is the record's authority, which is what the
                            # v2 stage instruction requires to be a signer.
                            gateway._wallet_address(HOUSE_LABEL): gateway._wallet_path(HOUSE_LABEL),
                        },
                        skip_preflight=not admitted,
                    )
            except _Rejected as exc:
                return TransferResult(
                    status="error",
                    latency_ms=int(round((time.monotonic() - started) * 1000)),
                    error_code=_code_from_text(str(exc)),
                    logs=(f"preflight refused the transaction: {exc}", *tax_log),
                    fee_lamports=0,
                    flip_tax_lamports=0,
                    flip_tax_bps=None if tax is None else tax.bps,
                    held_seconds=None if tax is None else tax.held_seconds,
                )
        detail = gateway._transaction(signature)
        code = custom_error_code(status.get("err"))
        logs = list(detail["logs"])
        logs.extend(tax_log)
        if status.get("unconfirmed"):
            logs.append(
                f"ticketpath: {signature} was sent and did not confirm inside "
                f"{_CONFIRM_TIMEOUT:g}s, so it may still land: do not resend it, check it"
            )
        if status.get("ok"):
            outcome = "ok"
            code = None
            if not admitted:  # a client that thinks a price is over the cap, and a hook that disagrees
                logs.append(
                    f"ticketpath: WARNING the chain admitted {price} lamports, and the client "
                    f"predicate refuses anything above {self.ceiling_lamports} on {self.event_id}"
                )
        elif code == E_CAP_EXCEEDED:
            outcome = "refused"
        else:
            outcome = "error"
        return TransferResult(
            status=outcome,
            signature=signature,
            slot=detail["slot"] if detail["slot"] is not None else status.get("slot"),
            block_time=detail["block_time"],
            error_code=code,
            latency_ms=int(round((time.monotonic() - started) * 1000)),
            logs=tuple(logs),
            # Only a landed transfer paid a fee. A refusal rolls the whole transaction back, so
            # the artist was paid nothing and this says so. `flip_tax_lamports` follows the same
            # rule; the rate and the hold are reported either way, because they are what was
            # applied to this row and the 0 is what happened to the money.
            fee_lamports=fee if outcome == "ok" else 0,
            flip_tax_lamports=tax_lamports if outcome == "ok" else 0,
            flip_tax_bps=None if tax is None else tax.bps,
            held_seconds=None if tax is None else tax.held_seconds,
        )

    def read_record(self) -> dict:
        """The record account as it is on chain: face, cap, the staged price and the status byte."""
        return self._gateway._read_record(self.record)


# -- dry run -----------------------------------------------------------------


class DryRunEventChain:
    """The same surface with no cluster behind it. Every answer is marked simulated."""

    simulated = True

    def __init__(self, spec: EventSpec, *, mode: str, cap_bps: int, face_lamports: int, ceiling: int) -> None:
        self.event_id = spec.event_id
        self.mint = f"simulated-mint:{spec.event_id}"
        self.record = f"simulated-record:{spec.event_id}"
        self.extra_metas = f"simulated-extra-metas:{spec.event_id}"
        self.mode = mode
        self.cap_bps = cap_bps
        self.face_lamports = face_lamports
        self.ceiling_lamports = ceiling
        #: The event's fee policy, carried from the spec exactly as the real chain carries it.
        #: The arithmetic below is the same arithmetic, so a dry run prices the fee it would
        #: have paid and a live run prices the fee it did; the one word that differs is in the
        #: logs, where every dry-run result says it was simulated.
        self.artist_fee = getattr(spec, "artist_fee", None)
        #: The event's flip tax policy, carried the same way. It prices the tax with the real
        #: arithmetic (`flip_tax.assess`) against this chain's own simulated hold clock, so a dry
        #: run reports the tax a live run would charge and the one word that differs is in the
        #: logs.
        self.flip_tax = getattr(spec, "flip_tax", None)
        self._stocked = 0
        self._held: dict[str, int] = {}
        #: When each wallet label last received a unit, on this chain's simulated clock. It starts
        #: empty, which means "unknown" for every label and is charged the full rate -- the same
        #: rule the record's zero clock follows -- and a transfer stamps the recipient, so a wallet
        #: that buys and later resells is priced on the hold between the two. There is no record
        #: account here to write a mint-wide clock into and no balance to spend, so a per-label
        #: number is the whole of the simulation.
        self._held_since: dict[str, int] = {}

    def __repr__(self) -> str:
        return (
            f"DryRunEventChain(event_id={self.event_id!r}, mode={self.mode!r}, "
            f"cap_bps={self.cap_bps}, face_lamports={self.face_lamports}, "
            f"ceiling_lamports={self.ceiling_lamports}, artist_fee={self.artist_fee!r}, "
            f"flip_tax={self.flip_tax!r})"
        )

    def _now(self) -> int:
        """The simulated chain's clock: the one read on the tax path, and the seam a test replaces.

        It exists for exactly the reason `ChainGateway._now` does -- a test that wants to price an
        hour's hold must not wait an hour -- and it is per chain rather than per module so two
        simulated runs cannot share a clock by accident.
        """
        return int(time.time())

    def open_account(self, wallet_label: str) -> str:
        _require_label(wallet_label)
        self._held.setdefault(wallet_label, 0)
        return f"simulated-wallet:{wallet_label}"

    def ticket_account(self, wallet_label: str, *, create: bool = False) -> str:
        _require_label(wallet_label)
        return f"simulated-ata:{self.event_id}:{wallet_label}"

    def stock(self, count: int) -> None:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError(f"count: expected a non-negative integer, got {count!r}")
        self._held[HOUSE_LABEL] = self._held.get(HOUSE_LABEL, 0) + count
        self._stocked += count

    def transfer(
        self,
        *,
        from_label: str,
        to_label: str,
        price_lamports: int,
        charge_artist_fee: bool = True,
        charge_flip_tax: bool = True,
    ) -> TransferResult:
        """The status the hook *would* have produced, with no signature, and no hop either way.

        A simulated above-ceiling transfer comes back `refused` with 6010 and moves nothing,
        exactly as the real one would. That is deliberate. An earlier version answered `ok`
        and put the prediction in a log line; the effect was that a dry-run dataset recorded a
        price the cap forbids as `executed`, and a reader comparing a dry run against a live
        run saw two different refusal rates. Nothing here is an observation -- `chain` says
        `simulated` on every row -- but the *status vocabulary* now means the same thing in
        both, so a dry run can price a thousand configurations and the refusal rate is
        comparable.

        The fee follows the same rule and the same arithmetic as the real chain: an admitted sale
        reports `fee_lamports = price * fee_bps // 10_000`, and a refused one reports 0, because a
        refused sale on the chain rolls the fee back with the staging. The fee is reported, never
        deducted from anything: the dry run has no balances to spend, and inventing a running
        ledger here would make two things in the harness that claim to know a wallet's balance.
        `charge_artist_fee=False` reports 0 and says nothing about a payment, because a primary sale
        pays no fee: the primary price is the artist's own money and the fee is charged on resales.

        The tax is the same arithmetic again, priced by `flip_tax.assess` against this chain's own
        `_held_since` clock: the seller's label starts unknown (a full-rate hold) and every
        simulated transfer stamps the recipient, so a later resale is priced on the hold it
        simulated. A refused sale reports `flip_tax_lamports=0` with the rate and the hold it would
        have been charged at, mirroring the live path, and the simulated tax line names both. No
        branch here ever carries a signature: a simulated sale did not happen.
        """
        price = _require_price(price_lamports)
        _require_label(from_label)
        _require_label(to_label)
        held = self._held.get(from_label, 0)
        if held < 1:
            raise TicketNotHeld(
                f"{from_label} holds {held} tickets on {self.event_id} (simulated); a transfer needs 1"
            )
        taxing = self.flip_tax is not None and self.flip_tax.enabled and charge_flip_tax
        tax = None
        # Read once, whether or not this sale carries the tax: the simulated hold clock starts on
        # every admitted transfer, tax or no tax, because the chain's clock is written by the hook
        # on every admitted move. A sale that is refused stamps nothing, because nothing moved.
        now_unix = self._now()
        if taxing:
            tax = assess_flip_tax(
                price_lamports=price,
                held_since_unix=self._held_since.get(from_label, UNKNOWN_HOLD),
                now_unix=now_unix,
                schedule=self.flip_tax.schedule,
            )
        tax_log: list[str] = []
        if taxing:
            held_text = "unknown" if tax.held_seconds is None else f"{tax.held_seconds}s"
            tax_log.append(
                f"simulated: the seller would have paid {tax.lamports} lamports to "
                f"{self.flip_tax.artist_wallet} as flip tax at {tax.bps} bps of {price}, held "
                f"{held_text}, in the same transaction as the move"
            )
        charging = self.artist_fee is not None and charge_artist_fee
        fee = (
            0
            if not charging
            else fee_lamports(price_lamports=price, fee_bps=self.artist_fee.fee_bps)
        )
        if not cap_admits(price_lamports=price, face_lamports=self.face_lamports, cap_bps=self.cap_bps):
            return TransferResult(
                status="refused",
                signature=None,
                # None, not 0: a simulated leg has no latency, and 0 is indistinguishable
                # from a very fast real send.
                latency_ms=None,
                error_code=E_CAP_EXCEEDED,
                logs=(
                    SIMULATED_LOG,
                    f"simulated: {price} lamports is above the ceiling {self.ceiling_lamports} "
                    f"the hook enforces on {self.event_id}; a real transfer is refused with "
                    f"{E_CAP_EXCEEDED} and the unit does not move",
                    *tax_log,
                ),
                fee_lamports=0,
                # Nothing moved, so nothing was paid; the rate and the hold are still what this
                # sale would have been charged at, which is what makes the row explain itself.
                flip_tax_lamports=0,
                flip_tax_bps=None if tax is None else tax.bps,
                held_seconds=None if tax is None else tax.held_seconds,
            )
        self._held[from_label] = held - 1
        self._held[to_label] = self._held.get(to_label, 0) + 1
        self._held_since[to_label] = now_unix
        logs = [SIMULATED_LOG]
        if charging:
            logs.append(
                f"simulated: the seller would have paid {fee} lamports to "
                f"{self.artist_fee.artist_wallet} at {self.artist_fee.fee_bps} bps of {price}, "
                "in the same transaction as the move"
            )
        logs.extend(tax_log)
        return TransferResult(
            status="ok",
            signature=None,
            latency_ms=None,
            logs=tuple(logs),
            fee_lamports=fee,
            flip_tax_lamports=0 if tax is None else tax.lamports,
            flip_tax_bps=None if tax is None else tax.bps,
            held_seconds=None if tax is None else tax.held_seconds,
        )

    def read_record(self) -> dict:
        return {
            "face_lamports": self.face_lamports,
            "cap_bps": self.cap_bps,
            "pending_price_lamports": 0,
            "status": 1,
        }


class DryRunGateway:
    """`ChainGateway`'s surface with no socket, no key and no validator.

    Tests and `--dry-run` use it. It is never a way to claim a trade happened: every result it
    hands out carries `SIMULATED_LOG`, and `simulated` is `True` on the gateway and on every event.
    """

    simulated = True

    def __init__(
        self, cluster: str, *, run_dir: Path, program: str = PROGRAM_DEFAULT
    ) -> None:
        if cluster not in CLUSTERS:
            raise ValueError(f"cluster: expected one of {sorted(CLUSTERS)}, got {cluster!r}")
        if program not in PROGRAMS:
            raise ValueError(f"program: expected one of {sorted(PROGRAMS)}, got {program!r}")
        if cluster not in PROGRAM_CLUSTERS[program]:
            raise ValueError(
                f"program: {program!r} cannot be paired with cluster {cluster!r}: v2 has no "
                "devnet deployment, so a v2 run there would read v1's answers and call them v2's"
            )
        self.cluster = cluster
        # A dry run still names its program, and the rows it causes carry that name. It is the one
        # way to exercise v2's cap and policy rules here, because nothing it reports is an
        # observation: every row says `simulated` and no signature is ever produced.
        self.program = program
        self.run_dir = Path(run_dir)
        self.rpc_url = ""
        self.program_id: str | None = None
        self._events: dict[str, DryRunEventChain] = {}
        self._started = False
        self._stopped = False

    def start(self) -> dict:
        self._started = True
        self._stopped = False
        return self.status()

    def stop(self) -> None:
        self._started = False
        self._stopped = True

    def create_event(self, spec: EventSpec) -> DryRunEventChain:
        cap_bps, face = _check_spec(spec)
        chain = DryRunEventChain(
            spec,
            mode=spec.mode,
            cap_bps=cap_bps,
            face_lamports=face,
            ceiling=ceiling_lamports(face, cap_bps),
        )
        self._events[spec.event_id] = chain
        return chain

    def status(self) -> dict:
        return {
            "cluster": self.cluster,
            "program": self.program,
            "program_id": None,
            "mints": tuple(sorted(self._events)),
            "healthy": True,
            "simulated": True,
        }

    def __repr__(self) -> str:
        return (
            f"DryRunGateway(cluster={self.cluster!r}, program={self.program!r}, "
            f"events={tuple(sorted(self._events))!r})"
        )


def make_gateway(
    cluster: str,
    *,
    run_dir: Path,
    dry_run: bool = False,
    program: str = PROGRAM_DEFAULT,
) -> ChainGateway | DryRunGateway:
    """The one door: a real gateway, or the dry one, for a program and a cluster that can pair.

    Validating here rather than in `start()` means a typo cannot open a socket first: an unknown
    cluster or an impossible program/cluster pairing raises before anything else happens.
    """
    if cluster not in CLUSTERS:
        raise ValueError(f"cluster: expected one of {sorted(CLUSTERS)}, got {cluster!r}")
    if program not in PROGRAMS:
        raise ValueError(f"program: expected one of {sorted(PROGRAMS)}, got {program!r}")
    if cluster not in PROGRAM_CLUSTERS[program]:
        raise ValueError(
            f"program: {program!r} cannot be paired with cluster {cluster!r}: v2 has no devnet "
            "deployment, so a v2 run there would read v1's answers and call them v2's"
        )
    if dry_run:
        return DryRunGateway(cluster, run_dir=run_dir, program=program)
    return ChainGateway(cluster, run_dir=run_dir, program=program, dry_run=False)

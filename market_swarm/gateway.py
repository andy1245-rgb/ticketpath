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
list, and signed once by the seller. That is what makes stage-and-check atomic: the record's
staged price cannot be moved by another transfer between the two instructions, and a refusal
rolls the staging back with it. It also halves the fee, from two signatures to one.

The reused units are `tools/devnet_publish.py`'s pure encoders and bounded readers (see
`.research/wave2-gateway.md` for the function-by-function list). No `step_*` function is called:
each of those writes the publish run's resume file under `records/`, assumes one mint and one
buyer, and raises on a refusal instead of returning one.

**Which program this drives is a parameter, not an assumption.** `program` is `"v1"` or `"v2"`,
and every instruction that reaches a program is built by `market_swarm/wire.py` from it, so the
program id this connects to, the keypair it deploys with and the bytes it sends all follow the
same name. v1 is what devnet serves; v2 has only ever run locally and its `SetPendingPrice` is
authorised by the record's authority, which this harness cannot sign, so `start()` refuses v2
with that sentence instead of writing a dataset of `6026` rows.

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

_RESERVED_PORTS = frozenset({3000, 3001, 8787, 8788})
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


def decode_record(data: bytes) -> dict:
    """The v1 `["record", mint]` account, 19 bytes of Borsh and no discriminator.

    `face_value_lamports u64 | cap_bps u16 | pending_price_lamports u64 | status u8`. The Rust
    `TicketRecord::LEN` says 20 and is dead code: `initialize_record` allocates the length of the
    actual serialisation, which is 19. No decoder for this existed anywhere in the repository
    before this function, so it is written here and unit-tested against a hand-built buffer.

    The layout lives in `wire` now, beside v2's 70-byte one, so this entry point and the
    per-program reader the gateway uses cannot disagree about which shape the bytes are.
    """
    return wire.decode_v1_record(data)


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

        v2 never reaches the boot: see the refusal at the top of the body.
        """
        if self.program == "v2":
            # Before anything boots and before a directory is made, because the failure is in the
            # instruction sequence and not in the cluster. v2's `SetPendingPrice` is signed by the
            # record's authority, which v2's `InitializeRecord` pins to the mint's authority -- the
            # house key -- while the swarm stages a price inside the seller's own signed
            # transaction, and one transaction with two unrelated signers is a design change, not a
            # wire choice. Left to run, every action would come back `6026 NotAuthority`: a dataset
            # that looks like a result and proves nothing, which is the one outcome this switch
            # exists to prevent.
            raise ChainUnavailable(
                "v2 cannot be driven end to end by this harness yet: its SetPendingPrice (tag 2) "
                "is authorised by the record's authority, which InitializeRecord pins to the "
                "mint's authority, and this swarm stages a price inside the seller's signed "
                "transaction. Every action would land as 6026 NotAuthority. The wire format is "
                "built and tested (market_swarm/wire.py); the signer is the missing piece. Run v1, "
                "or run v2 with --dry-run for a labelled simulation."
            )
        with self._state_lock:
            if self._started:
                return self.status()
            self._stopped = False
            self.run_dir.mkdir(parents=True, exist_ok=True)
            self._keys_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(self._keys_dir, 0o700)
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
        if not dp.SO_PATH.exists():
            raise ChainUnavailable(
                f"{dp.SO_PATH.name} is not built: this gateway deploys a prebuilt program and "
                f"never builds one. Build it once with `cargo-build-sbf` in programs/cap_hook."
            )
        if not dp.PROGRAM_KEYPAIR.exists():
            raise ChainUnavailable(f"no program keypair beside the .so at {dp.PROGRAM_KEYPAIR.name}")
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
        chain = EventChain(
            gateway=self,
            event_id=spec.event_id,
            mint=mint,
            record=record,
            extra_metas=extra_metas,
            mode=spec.mode,
            cap_bps=observed["cap_bps"],
            face_lamports=observed["face_lamports"],
            ceiling_lamports=ceiling,
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

    def _ensure_wallet(self, label: str) -> str:
        """The label's address, funded and usable as a fee payer. Idempotent per run."""
        _require_label(label)
        with wallet_lock(label):
            address = self._wallet_address(label)
            if label == HOUSE_LABEL:
                return address  # funded at genesis; a transfer to itself would waste a fee
            funded = self._balance(address)
            if funded >= WALLET_FLOOR_LAMPORTS:
                return address
            self._fund_wallet(address, FUND_LAMPORTS_PER_WALLET - funded)
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
            if observed.get("face_lamports") == face and observed.get("cap_bps") == cap_bps:
                return observed
            if look + 1 < _LOOKS * 2:
                time.sleep(_LOOK_INTERVAL)
        raise ChainUnavailable(
            f"the record {record} reads face={observed.get('face_lamports')} "
            f"cap_bps={observed.get('cap_bps')}, the spec asked for face={face} cap_bps={cap_bps}"
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
        """`solana program deploy` of the .so that is already there. No build, ever."""
        program_id = self._program_id()
        self._run(
            [
                _which("solana") or "solana",
                "--url", self.rpc_url,
                "program", "deploy", str(dp.SO_PATH),
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

    simulated = False

    def __repr__(self) -> str:  # a review reads this, so it names only public identifiers
        return (
            f"EventChain(event_id={self.event_id!r}, mint={self.mint!r}, record={self.record!r}, "
            f"mode={self.mode!r}, cap_bps={self.cap_bps}, face_lamports={self.face_lamports}, "
            f"ceiling_lamports={self.ceiling_lamports})"
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

    def transfer(self, *, from_label: str, to_label: str, price_lamports: int) -> TransferResult:
        """Stage a price and move one ticket, in one transaction, signed once by the seller.

        The two instructions are `SetPendingPrice` and the Token-2022 `TransferChecked`; they share
        the record and the seller signs both. Nothing between them can move the staged price,
        because there is nothing between them: the transaction is atomic, and if the hook refuses,
        the staging is rolled back with it.

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
        gateway._ensure_wallet(from_label)  # funded, or it cannot pay its own fee
        seller_path = gateway._wallet_path(from_label)  # a path for the signer child only
        seller_address = gateway._wallet_address(from_label)
        program_id = gateway._program_id()
        admitted = cap_admits(
            price_lamports=price, face_lamports=self.face_lamports, cap_bps=self.cap_bps
        )
        stage = wire.instruction_set_pending_price(
            gateway.program,
            record=self.record,
            program_id=program_id,
            price=price,
            # v2 reads a signer here and refuses 6026 for a key that is not the record's
            # authority. The seller is the only key this transaction has, so this is what a v2
            # run would send -- and why `ChainGateway.start()` refuses v2 rather than send it.
            authority=seller_address,
            mint=self.mint,
        )
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
        with mint_lock(self.mint):
            started = time.monotonic()
            try:
                signature, status, _ = gateway._send(
                    [stage, move], payer=seller_address, signer_path=seller_path,
                    skip_preflight=not admitted,
                )
            except _Rejected as exc:
                return TransferResult(
                    status="error",
                    latency_ms=int(round((time.monotonic() - started) * 1000)),
                    error_code=_code_from_text(str(exc)),
                    logs=(f"preflight refused the transaction: {exc}",),
                )
        detail = gateway._transaction(signature)
        code = custom_error_code(status.get("err"))
        logs = list(detail["logs"])
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
        self._stocked = 0
        self._held: dict[str, int] = {}

    def __repr__(self) -> str:
        return (
            f"DryRunEventChain(event_id={self.event_id!r}, mode={self.mode!r}, "
            f"cap_bps={self.cap_bps}, face_lamports={self.face_lamports}, "
            f"ceiling_lamports={self.ceiling_lamports})"
        )

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

    def transfer(self, *, from_label: str, to_label: str, price_lamports: int) -> TransferResult:
        """The status the hook *would* have produced, with no signature, and no hop either way.

        A simulated above-ceiling transfer comes back `refused` with 6010 and moves nothing,
        exactly as the real one would. That is deliberate. An earlier version answered `ok`
        and put the prediction in a log line; the effect was that a dry-run dataset recorded a
        price the cap forbids as `executed`, and a reader comparing a dry run against a live
        run saw two different refusal rates. Nothing here is an observation -- `chain` says
        `simulated` on every row -- but the *status vocabulary* now means the same thing in
        both, so a dry run can price a thousand configurations and the refusal rate is
        comparable.
        """
        price = _require_price(price_lamports)
        _require_label(from_label)
        _require_label(to_label)
        held = self._held.get(from_label, 0)
        if held < 1:
            raise TicketNotHeld(
                f"{from_label} holds {held} tickets on {self.event_id} (simulated); a transfer needs 1"
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
                ),
            )
        self._held[from_label] = held - 1
        self._held[to_label] = self._held.get(to_label, 0) + 1
        return TransferResult(status="ok", signature=None, latency_ms=None, logs=(SIMULATED_LOG,))

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

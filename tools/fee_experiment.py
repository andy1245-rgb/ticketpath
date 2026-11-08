#!/usr/bin/env python3
"""Measure what Token-2022's transfer fee withholds on an indivisible ticket.

The question this answers, with numbers read off a cluster instead of argued from a
document: a ticket mint has `decimals = 0`, every transfer is `amount == 1`, and the
transfer hook refuses anything else. Token-2022's transfer fee is computed on the
transferred *amount* in base units, so what is a 500 bps artist fee, or a 1500 bps flip
tax, on a transfer of one base unit? Zero, or the whole ticket?

Both answers have consequences, and they are not the same consequence:

  * if the fee floors, every sub-10000 bps fee withholds zero and the feature is dead;
  * if it ceils (which is what `spl-token-2022`'s `calculate_fee` does), a one-unit
    transfer at any nonzero bps withholds **one base unit -- the entire ticket** -- so
    the mechanism exists but cannot express a percentage of a price.

So this tool creates real mints on a throw-away local validator, moves real tokens,
and reads `withheldAmount` out of `getAccountInfo` in `jsonParsed` form, before and
after. It asserts what it finds against the source's arithmetic and prints both, so a
disagreement is a failed run and not a paragraph.

What it runs (`python3 tools/fee_experiment.py`):

  1. decimals 0, fee 500 bps, maximum set, withdraw authority set -- transfer 1
  2. decimals 0, fee 1500 bps                                  -- transfer 1
  3. decimals 0, fee 1500 bps                                  -- transfer 10
  4. decimals 9, fee 1500 bps                                  -- transfer 1_000_000_000
  5. the same mint with a `TransferHook` as well: a fee-bearing transfer (10), a
     one-unit transfer (which withholds), and a `WithdrawWithheldTokensFromAccounts`
     with the staged price cleared first, so a hook invocation on the withdraw path
     would be visible as a refusal instead of hiding behind an admitted transfer.

Bounds and blast radius: it starts its own `solana-test-validator` with a genesis
allocation (`--mint`), never the faucet, never devnet or mainnet, and no `--url` that is
not loopback is accepted. The validator is killed on every exit path and the run proves
the process is gone. Keys and the ledger live under `.swarm-runs/fee-experiment/`
(git-ignored), key files are mode 0600, and no code path here prints, logs or
tracebacks a byte of key material: signing is handed to `tools/solana_sign.py`, exactly
as `tools/devnet_publish.py` does.

Standard library only in the pure parts (`fee_for`, `floor_fee_for`, the two JSON
readers, the refusals). The chain plumbing reuses `tools/devnet_publish.py`, which is
already the repository's proven transaction builder.
"""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import stat
import subprocess
import sys
import time
from decimal import Decimal
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
# `tools/` has no `__init__.py`; it is importable only once it is on sys.path.
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import devnet_publish as dp  # noqa: E402
from ticketpath.core import base58  # noqa: E402

# -- constants that are facts about Token-2022, not about this repository ---------

TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
SYSTEM_PROGRAM = "11111111111111111111111111111111"
#: `spl-token-2022`'s `MAX_FEE_BASIS_POINTS`: 100% is the top of the scale.
MAX_FEE_BASIS_POINTS = 10_000
#: The fee is computed on the amount in base units. This is the divisor.
BASIS_POINTS_ONE = 10_000

CAP_HOOK_CRATE = REPO_ROOT / "programs" / "cap_hook"
CAP_HOOK_SO = CAP_HOOK_CRATE / "target" / "deploy" / "cap_hook.so"
CAP_HOOK_KEYPAIR = CAP_HOOK_CRATE / "target" / "deploy" / "cap_hook-keypair.json"

DEFAULT_WORKDIR = REPO_ROOT / ".swarm-runs" / "fee-experiment"
DEFAULT_DEADLINE = 600.0

#: `cap_hook`'s tag for `SetPendingPrice`; only used to *clear* the staged price before
#: the withdraw leg. Read from the program's dispatcher, not guessed.
CAP_HOOK_TAG_SET_PENDING_PRICE = 2


class ExperimentError(RuntimeError):
    """Something the run must not paper over. Ends the run non-zero."""


def say(line: str = "") -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


# -- the pure part: Token-2022's fee arithmetic ----------------------------------


def ceil_div(numerator: int, denominator: int) -> int:
    """Ceiling division, the way `spl-token-2022::TransferFee::ceil_div` spells it."""
    if denominator <= 0:
        raise ValueError("denominator must be positive")
    return (numerator + denominator - 1) // denominator


def fee_for(amount: int, bps: int, maximum_fee: int | None = None) -> int:
    """The fee Token-2022 withholds, in base units, for `amount` at `bps`.

    Transcribed from `spl-token-2022`'s `TransferFee::calculate_fee`: zero for a zero
    amount or a zero rate, otherwise **ceiling** division of `amount * bps / 10_000`,
    finally clamped by the mint's `maximum_fee`.

    The ceiling is the whole point of the measurement. At `amount = 1` and any
    `bps` in 1..=9_999 the numerator is below 10_000, the ceiling is 1, and the fee is
    the entire amount transferred.
    """
    if amount < 0:
        raise ValueError("amount must not be negative")
    if not 0 <= bps <= MAX_FEE_BASIS_POINTS:
        raise ValueError(f"bps must be in 0..={MAX_FEE_BASIS_POINTS}, got {bps}")
    if amount == 0 or bps == 0:
        return 0
    fee = ceil_div(amount * bps, BASIS_POINTS_ONE)
    if maximum_fee is not None:
        if maximum_fee < 0:
            raise ValueError("maximum_fee must not be negative")
        fee = min(fee, int(maximum_fee))
    return fee


def floor_fee_for(amount: int, bps: int) -> int:
    """The reading the brief tested: `floor(amount * bps / 10_000)`.

    Kept only so the disagreement with `fee_for` is computed and printed rather than
    asserted in prose. Nothing in the run uses this value to decide anything.
    """
    if amount < 0 or bps < 0:
        raise ValueError("amount and bps must not be negative")
    return (amount * bps) // BASIS_POINTS_ONE


def active_fee(config: dict, epoch: int) -> tuple[int, int]:
    """`(bps, maximum_fee)` in force at `epoch`, from the parsed `transferFeeConfig`.

    Token-2022 keeps an older and a newer schedule; the newer one takes effect at its
    own epoch. Reading the active one is what stops this tool measuring a fee that has
    not started yet.
    """
    older = config["olderTransferFee"]
    newer = config["newerTransferFee"]
    schedule = older if epoch < int(newer["epoch"]) else newer
    return int(schedule["transferFeeBasisPoints"]), int(schedule["maximumFee"])


def ui_amount(base_units: int, decimals: int) -> str:
    """Base units as the decimal UI amount the `spl-token` CLI takes on its command line."""
    if decimals < 0:
        raise ValueError("decimals must not be negative")
    value = Decimal(int(base_units)).scaleb(-decimals)
    return f"{value:.{decimals}f}"


# -- the pure part: reading the two jsonParsed accounts ---------------------------


def _parsed_info(account_value: dict) -> dict:
    """`result.value` of getAccountInfo(jsonParsed) -> the parsed `info` object."""
    if not account_value:
        raise ExperimentError("the account does not exist")
    data = account_value.get("data")
    if not isinstance(data, dict) or data.get("program") != "spl-token-2022":
        raise ExperimentError("not a Token-2022 account")
    return data["parsed"]["info"]


def withheld_amount(account_value: dict) -> int:
    """`withheldAmount` from a token account's `transferFeeAmount` extension.

    A token account for a fee-bearing mint must carry the extension; if it does not,
    that is a finding and not a zero, so this raises instead of defaulting.
    """
    info = _parsed_info(account_value)
    for extension in info.get("extensions", []):
        if extension.get("extension") == "transferFeeAmount":
            return int(extension["state"]["withheldAmount"])
    raise ExperimentError("the token account has no transferFeeAmount extension")


def token_amount(account_value: dict) -> int:
    return int(_parsed_info(account_value)["tokenAmount"]["amount"])


def mint_details(account_value: dict) -> dict:
    """Decimals, supply, and the transfer-fee configuration of a parsed mint."""
    info = _parsed_info(account_value)
    details = {
        "decimals": int(info["decimals"]),
        "supply": int(info["supply"]),
        "withdrawWithheldAuthority": None,
        "withheldAmount": None,
        "olderTransferFee": None,
        "newerTransferFee": None,
    }
    for extension in info.get("extensions", []):
        if extension.get("extension") == "transferFeeConfig":
            state = extension["state"]
            details["withdrawWithheldAuthority"] = state.get("withdrawWithheldAuthority")
            details["withheldAmount"] = int(state.get("withheldAmount", 0))
            details["olderTransferFee"] = state["olderTransferFee"]
            details["newerTransferFee"] = state["newerTransferFee"]
    if details["olderTransferFee"] is None:
        raise ExperimentError("the mint has no transferFeeConfig extension")
    return details


# -- the pure part: refusals that must be true before any process starts ----------


def assert_local_url(url: str) -> None:
    """No devnet, no mainnet, no faucet: this measurement is a local one.

    The genesis allocation is the only funding this tool knows how to use, and spending
    real lamports on a question the source already answers is not a trade worth making.
    """
    match = re.match(r"^http://(127\.0\.0\.1|localhost|\[::1\]):(\d+)$", url or "")
    if not match:
        raise ExperimentError(
            f"refusing {url!r}: this experiment runs only against a loopback validator it started"
        )


def assert_funded(balance_lamports: int, *, minimum: int = 1_000_000_000) -> None:
    """The genesis `--mint` allocation, checked instead of assumed."""
    if balance_lamports < minimum:
        raise ExperimentError(
            f"the payer holds {balance_lamports} lamports, under the {minimum} this run needs; "
            "the validator was not started with a genesis allocation for it"
        )


def require_binary(name: str) -> str:
    found = dp.which(name)
    if not found:
        raise ExperimentError(
            f"{name} is not on PATH; export PATH=\"$HOME/.local/share/solana/install/"
            "active_release/bin:$HOME/.cargo/bin:$PATH\""
        )
    return found


# -- key material: created, never read --------------------------------------------


def ensure_keypair(path: Path) -> str:
    """A keypair file under the work directory, mode 0600, and only its public key back."""
    if path.exists():
        return keypair_pubkey(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    result = subprocess.run(
        [require_binary("solana-keygen"), "new", "--no-bip39-passphrase", "--silent", "--force", "-o", str(path)],
        capture_output=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise ExperimentError("solana-keygen could not write a keypair")
    os.chmod(path, 0o600)
    return keypair_pubkey(path)


def keypair_pubkey(path: Path) -> str:
    """The address of a keypair, without this process ever opening the file."""
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ExperimentError(f"{path.name} is mode {mode:04o}; a key file must be 0600")
    result = subprocess.run(
        [require_binary("solana-keygen"), "pubkey", str(path)], capture_output=True, timeout=60
    )
    if result.returncode != 0:
        raise ExperimentError(f"solana-keygen could not read {path.name}")
    return result.stdout.decode("utf-8", "replace").strip().splitlines()[-1].strip()


def sign_message(keypair: Path, message: bytes) -> bytes:
    """One signature from a separate process; this process never opens the keypair."""
    result = subprocess.run(
        [sys.executable, str(TOOLS_DIR / "solana_sign.py"), "--keypair", str(keypair)],
        input=message,
        capture_output=True,
        timeout=120,
    )
    if result.returncode != 0:
        tail = result.stderr.decode("utf-8", "replace").strip().splitlines()
        raise ExperimentError(f"the signer refused: {tail[-1] if tail else 'no reason given'}")
    signature = base58.decode(result.stdout.decode().strip())
    if len(signature) != 64:
        raise ExperimentError("the signer returned something that is not a 64-byte signature")
    return signature


# -- the local validator ----------------------------------------------------------


class Validator:
    """One throw-away single-node cluster, killed on every exit path and proved gone."""

    def __init__(self, *, ledger: Path, payer: str, workdir: Path):
        self.ledger = ledger
        self.payer = payer
        self.workdir = workdir
        self.port = 0
        self.faucet_port = 0
        self.process: subprocess.Popen | None = None
        self.log_path = workdir / "validator.log"
        self._log_handle = None
        self._stopped = False

    @property
    def rpc_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def _free_range(self, width: int = 60) -> tuple[int, int]:
        """A contiguous, free port range for the validator's gossip/TVU sockets."""
        for _ in range(50):
            base = self._free_ports(1)[0]
            sockets = []
            try:
                for offset in range(width):
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.bind(("127.0.0.1", base + offset))
                    sockets.append(sock)
            except OSError:
                continue
            finally:
                for sock in sockets:
                    sock.close()
            return base, base + width - 1
        raise ExperimentError("could not find a free contiguous port range for the validator")

    def _free_ports(self, count: int) -> list[int]:
        """Distinct ports, held open together so the kernel cannot hand out the same one twice."""
        sockets = []
        try:
            for _ in range(count):
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.bind(("127.0.0.1", 0))
                sockets.append(sock)
            return [sock.getsockname()[1] for sock in sockets]
        finally:
            for sock in sockets:
                sock.close()

    def start(self, *, health_timeout: float = 90.0) -> None:
        binary = require_binary("solana-test-validator")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        self.port, self.faucet_port = self._free_ports(2)
        gossip_port = self._free_ports(1)[0]
        dynamic_low, dynamic_high = self._free_range()
        self._log_handle = open(self.log_path, "wb")
        command = [
            binary,
            "--reset",
            "--quiet",
            "--ledger", str(self.ledger),
            "--rpc-port", str(self.port),
            "--faucet-port", str(self.faucet_port),
            # Do not take the default gossip port: on a machine running other validators it
            # can already be bound, and the failure is a panic before the RPC is up.
            "--gossip-port", str(gossip_port),
            "--dynamic-port-range", f"{dynamic_low}-{dynamic_high}",
            # Genesis funding, not the faucet: this address receives the initial
            # allocation when the ledger is created.
            "--mint", self.payer,
            # Short epochs so a fee whose start epoch is two ahead becomes active in
            # seconds instead of never on a laptop.
            "--slots-per-epoch", "32",
        ]
        self.process = subprocess.Popen(
            command, stdout=self._log_handle, stderr=subprocess.STDOUT, start_new_session=True
        )
        atexit.register(self.stop)
        for received in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
            signal.signal(received, self._on_signal)
        # No pid and no port in this line: it is the line the finding quotes, and a pid
        # or a listening port is a handle on a live process. The workdir log has both.
        say("validator: started from a fresh ledger, genesis-funded payer, no faucet, no clone")
        try:
            self.wait_health(self.rpc_url, timeout=health_timeout)
        except ExperimentError as exc:
            tail = ""
            if self.log_path.exists():
                lines = self.log_path.read_text(errors="replace").strip().splitlines()
                tail = f"; validator log tail: {lines[-3:]}" if lines else "; validator log is empty"
            raise ExperimentError(f"{exc}{tail}") from None

    @staticmethod
    def wait_health(url: str, *, timeout: float) -> None:
        assert_local_url(url)
        deadline = time.monotonic() + timeout
        last: Exception | None = None
        while time.monotonic() < deadline:
            try:
                if dp.rpc(url, "getHealth", [], timeout=2.0, attempts=1) == "ok":
                    return
            except Exception as exc:  # noqa: BLE001 - the reason is kept for the failure message
                last = exc
            time.sleep(0.25)
        raise ExperimentError(f"the validator did not answer getHealth within {timeout:g}s ({last})")

    def _on_signal(self, signum, _frame) -> None:
        self.stop()
        raise SystemExit(128 + signum)

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        process = self.process
        if process is not None and process.poll() is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=5)
        if process is not None:
            # Reaped by wait(), so a live pid here would be a leaked process.
            try:
                os.kill(process.pid, 0)
            except ProcessLookupError:
                alive = False
            else:
                alive = True
            if alive:
                raise ExperimentError("the validator survived SIGKILL: not leaving it running")
        if self._log_handle is not None:
            self._log_handle.close()
            self._log_handle = None
        if self.port:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.settimeout(0.5)
                still_listening = probe.connect_ex(("127.0.0.1", self.port)) == 0
            if still_listening:
                raise ExperimentError("the validator's RPC port is still open after the kill")
        say("validator: stopped; the process is gone and its RPC port is closed")


# -- the experiment ---------------------------------------------------------------


class Experiment:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.workdir = Path(args.workdir).resolve()
        self.keys = self.workdir / "keys"
        self.ledger = self.workdir / "ledger"
        self.config_path = self.workdir / "cli.yml"
        self.deadline = time.monotonic() + float(args.deadline)
        self.url = args.url
        self.validator: Validator | None = None
        self.payer_key = self.keys / "payer.json"
        self.recipient_key = self.keys / "recipient.json"
        self.pool_key = self.keys / "pool.json"
        self.payer = ""
        self.recipient = ""
        self.pool = ""
        self.cap_hook = ""
        self.measurements: list[dict] = []
        self.failures: list[str] = []

    # -- output

    def check_deadline(self) -> None:
        if time.monotonic() > self.deadline:
            raise ExperimentError(f"the run passed its {self.args.deadline:g}s deadline")

    def display(self, command: list[str]) -> str:
        """The command with machine layout stripped: relative paths, tool names, `$RPC`.

        This is the form the finding quotes, so no absolute home path and no listening
        port ever reaches a public file.
        """
        prefix = str(REPO_ROOT) + os.sep
        shown = []
        for part in command:
            if part.startswith(prefix):
                part = part[len(prefix):]
            elif part == self.url:
                part = "$RPC"
            elif part.startswith(str(Path(part).parent) + os.sep) and os.sep in part and not part.startswith("."):
                candidate = Path(part)
                if candidate.is_absolute() and candidate.name in {
                    "solana", "solana-keygen", "solana-test-validator", "spl-token", "python3"
                }:
                    part = candidate.name
            shown.append(part)
        return " ".join(shown)

    def run(self, command: list[str], *, timeout: float, what: str, check: bool = True) -> subprocess.CompletedProcess:
        self.check_deadline()
        say("  $ " + self.display(command))
        result = subprocess.run(command, capture_output=True, timeout=timeout)
        if check and result.returncode != 0:
            stderr = result.stderr.decode("utf-8", "replace").strip().splitlines()
            raise ExperimentError(f"{what} failed: {stderr[-1] if stderr else 'no stderr'}")
        return result

    # -- setup

    def prepare(self) -> None:
        work = self.workdir
        if DEFAULT_WORKDIR != work and DEFAULT_WORKDIR not in work.parents:
            raise ExperimentError(
                f"refusing workdir {work}: keys and the ledger live under {DEFAULT_WORKDIR}"
            )
        work.mkdir(parents=True, exist_ok=True)
        os.chmod(work, 0o700)
        if not self.args.keep:
            for stale in (self.keys, self.ledger):
                if stale.exists():
                    shutil.rmtree(stale)
        self.keys.mkdir(parents=True, exist_ok=True)
        os.chmod(self.keys, 0o700)
        self.payer = ensure_keypair(self.payer_key)
        self.recipient = ensure_keypair(self.recipient_key)
        self.pool = ensure_keypair(self.pool_key)
        say(f"payer (genesis-funded): {self.payer}")

        if self.url:
            assert_local_url(self.url)
            self.validator = None
            say("validator: attaching to the loopback validator given on the command line")
        else:
            self.validator = Validator(ledger=self.ledger, payer=self.payer, workdir=work)
            self.validator.start()
            self.url = self.validator.rpc_url
        assert_local_url(self.url)

        self.config_path.write_text(
            f"json_rpc_url: {self.url}\nwebsocket_url: \"\"\nkeypair_path: {self.payer_key}\ncommitment: confirmed\n"
        )
        os.chmod(self.config_path, 0o600)

        self.wait_for_token_2022()

        balance = dp.rpc(self.url, "getBalance", [self.payer, {"commitment": "confirmed"}])["value"]
        assert_funded(int(balance))
        say(f"payer balance at genesis: {balance} lamports")

        epoch = dp.rpc(self.url, "getEpochInfo", [{"commitment": "confirmed"}])["epoch"]
        say(f"validator epoch: {epoch}")

    def wait_for_token_2022(self, *, timeout: float = 45.0) -> None:
        """Token-2022 is in the validator's genesis, but only once the first bank exists.

        getHealth answers before the first slot is produced, and a transaction sent into
        that gap is rejected with "Program is not deployed". Waiting for the account to
        be executable is the readiness condition this run actually needs.
        """
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            slot = int(dp.rpc(self.url, "getSlot", [{"commitment": "confirmed"}], attempts=1))
            value = dp.rpc(
                self.url, "getAccountInfo",
                [TOKEN_2022_PROGRAM, {"encoding": "base64", "commitment": "confirmed"}], attempts=1,
            )
            value = (value or {}).get("value")
            if slot > 0 and value and value.get("executable"):
                say(f"token-2022: executable at its canonical id, slot {slot}")
                return
            time.sleep(0.25)
        raise ExperimentError("Token-2022 never became executable on the validator")

    def cli(self, *args: str, timeout: float = 120.0) -> str:
        command = [
            require_binary("spl-token"),
            "--config", str(self.config_path),
            "--fee-payer", str(self.payer_key),
            "--program-2022",
            *args,
        ]
        return self.run(command, timeout=timeout, what=f"spl-token {args[0]}").stdout.decode()

    def solana(self, *args: str, timeout: float = 180.0) -> str:
        command = [require_binary("solana"), "--url", self.url, *args]
        return self.run(command, timeout=timeout, what=f"solana {args[0]}").stdout.decode()

    # -- transactions

    def send(self, instructions: list[dp.Instruction], *, what: str, allow_failure: bool = False) -> tuple[str, dict]:
        self.check_deadline()
        blockhash = dp.rpc(self.url, "getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
        message = dp.compile_message(self.payer, instructions, blockhash)
        signature = sign_message(self.payer_key, message)
        wire = base64.b64encode(dp.build_transaction(message, [signature])).decode("ascii")
        sent = dp.rpc(
            self.url,
            "sendTransaction",
            [wire, {"encoding": "base64", "skipPreflight": allow_failure, "preflightCommitment": "confirmed"}],
        )
        status = dp.confirm(self.url, sent, timeout=90.0)
        state = "ok" if status["ok"] else f"FAILED ({status['err']})"
        say(f"  tx {what}: {sent} slot={status.get('slot')} {state}")
        if not status["ok"] and not allow_failure:
            raise ExperimentError(f"{what} was refused: {status['err']} ({sent})")
        return sent, status

    def transaction_logs(self, signature: str) -> dict:
        for _ in range(20):
            result = dp.rpc(
                self.url,
                "getTransaction",
                [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}],
                attempts=1,
            )
            if result:
                return result
            time.sleep(0.25)
        raise ExperimentError(f"the cluster has no transaction for {signature}")

    def account(self, address: str) -> dict:
        """`result.value` of getAccountInfo(jsonParsed), retried past the RPC's bank lag."""
        for _ in range(40):
            result = dp.rpc(
                self.url,
                "getAccountInfo",
                [address, {"encoding": "jsonParsed", "commitment": "confirmed"}],
                attempts=1,
            )
            if result and result.get("value"):
                return result["value"]
            time.sleep(0.25)
        raise ExperimentError(f"{address} does not exist after 10s")

    # -- mints and token accounts

    def create_mint(self, label: str, *, decimals: int, bps: int, maximum_fee: int, hook: str | None = None) -> tuple[str, str]:
        """`maximum_fee` is in base units; the CLI takes a UI amount."""
        path = self.keys / f"mint-{label}.json"
        mint = ensure_keypair(path)
        args = [
            "create-token",
            "--decimals", str(decimals),
            "--transfer-fee-basis-points", str(bps),
            "--transfer-fee-maximum-fee", ui_amount(maximum_fee, decimals),
        ]
        if hook:
            args += ["--transfer-hook", hook]
        args.append(str(path))
        output = self.cli(*args)
        signature = self.last_signature(output)
        say(f"mint {label}: {mint} decimals={decimals} fee={bps}bps maximum_fee={maximum_fee} base units"
            + (f" hook={hook}" if hook else ""))
        return mint, signature

    @staticmethod
    def last_signature(output: str) -> str:
        matches = re.findall(r"Signature: ([1-9A-HJ-NP-Za-km-z]{64,88})", output)
        if not matches:
            raise ExperimentError("the command printed no signature")
        return matches[-1]

    def create_token_account(self, mint: str, owner: str) -> str:
        output = self.cli("create-account", "--owner", owner, mint)
        self.last_signature(output)
        output = self.cli("address", "--verbose", "--token", mint, "--owner", owner)
        match = re.search(r"Associated token address: ([1-9A-HJ-NP-Za-km-z]{32,44})", output)
        if not match:
            raise ExperimentError("spl-token did not print an associated token address")
        return match.group(1)

    def mint_to(self, mint: str, amount: int, decimals: int) -> str:
        output = self.cli("mint", mint, ui_amount(amount, decimals))
        return self.last_signature(output)

    def wait_for_fee(self, mint: str, bps: int, *, timeout: float = 120.0) -> dict:
        """Wait until the schedule at `bps` is the one in force, and return the mint details."""
        deadline = time.monotonic() + timeout
        while True:
            details = mint_details(self.account(mint))
            epoch = int(dp.rpc(self.url, "getEpochInfo", [{"commitment": "confirmed"}])["epoch"])
            active_bps, active_maximum = active_fee(details, epoch)
            if active_bps == bps:
                details["activeBasisPoints"] = active_bps
                details["activeMaximumFee"] = active_maximum
                details["epoch"] = epoch
                return details
            if time.monotonic() > deadline:
                raise ExperimentError(
                    f"{mint}: the fee in force is {active_bps} bps at epoch {epoch}, not {bps}; "
                    "the schedule never became active within the timeout"
                )
            time.sleep(1.0)

    def checked_mint_config(self, mint: str, *, decimals: int, bps: int) -> dict:
        details = self.wait_for_fee(mint, bps)
        if details["decimals"] != decimals:
            raise ExperimentError(f"{mint}: decimals {details['decimals']} != {decimals}")
        if not details["withdrawWithheldAuthority"]:
            raise ExperimentError(f"{mint}: no withdraw-withheld authority is set")
        return details

    # -- token-2022 instructions

    def transfer_checked(self, *, source: str, mint: str, destination: str, amount: int, decimals: int,
                         extra_accounts: tuple[dp.AccountMeta, ...]) -> dp.Instruction:
        accounts = [
            dp.AccountMeta(source, False, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(destination, False, True),
            dp.AccountMeta(self.payer, True, False),
        ]
        accounts += list(extra_accounts)
        return dp.Instruction(
            program_id=TOKEN_2022_PROGRAM,
            accounts=tuple(accounts),
            data=bytes([12]) + int(amount).to_bytes(8, "little") + bytes([decimals]),
        )

    def withdraw_withheld(self, *, mint: str, destination: str, sources: list[str]) -> dp.Instruction:
        # TransferFeeExtension (26), WithdrawWithheldTokensFromAccounts (3), count.
        accounts = [
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(destination, False, True),
            dp.AccountMeta(self.payer, True, False),
        ]
        accounts += [dp.AccountMeta(source, False, True) for source in sources]
        return dp.Instruction(
            program_id=TOKEN_2022_PROGRAM,
            accounts=tuple(accounts),
            data=bytes([26, 3, len(sources)]),
        )

    # -- the measured legs

    def measure(self, label: str, *, mint: str, decimals: int, bps: int, maximum_fee: int,
                amount: int, mint_authority_ata: str, recipient_ata: str) -> dict:
        """One before/after reading of `withheldAmount`, with the transfer quoted."""
        self.check_deadline()
        before_account = self.account(recipient_ata)
        before_withheld = withheld_amount(before_account)
        before_amount = token_amount(before_account)
        say(f"[{label}] transfer {amount} of mint {mint} (decimals {decimals}, {bps} bps, max {maximum_fee})")
        say(f"  before: recipient amount={before_amount} withheldAmount={before_withheld}")
        signature, _ = self.send(
            [self.transfer_checked(
                source=mint_authority_ata, mint=mint, destination=recipient_ata,
                amount=amount, decimals=decimals, extra_accounts=(),
            )],
            what=f"transfer {amount}",
        )
        after_account = self.account(recipient_ata)
        after_withheld = withheld_amount(after_account)
        after_amount = token_amount(after_account)
        expected = fee_for(amount, bps, maximum_fee)
        floor = floor_fee_for(amount, bps)
        say(f"  after:  recipient amount={after_amount} withheldAmount={after_withheld}")
        say(f"  arithmetic: ceil({amount}*{bps}/10000)={expected}  floor({amount}*{bps}/10000)={floor}")
        if after_withheld != expected:
            raise ExperimentError(
                f"[{label}] the cluster withheld {after_withheld}, the source's arithmetic says {expected}"
            )
        if after_amount != amount - expected:
            raise ExperimentError(
                f"[{label}] the recipient holds {after_amount}, {amount} - {expected} was expected"
            )
        record = {
            "leg": label,
            "mint": mint,
            "decimals": decimals,
            "bps": bps,
            "maximumFee": maximum_fee,
            "amount": amount,
            "beforeWithheld": before_withheld,
            "afterWithheld": after_withheld,
            "recipientAmount": after_amount,
            "ceilingFee": expected,
            "floorFee": floor,
            "signature": signature,
            # The exact object the RPC returned under data.parsed.info: what the finding quotes.
            "beforeAccount": _parsed_info(before_account),
            "afterAccount": _parsed_info(after_account),
        }
        self.measurements.append(record)
        return record

    # -- the hook leg

    def derive_pda(self, program_id: str, name: str, mint: str) -> str:
        """The toolchain derives the PDA; the seed shape is `string:` and `pubkey:`."""
        command = [
            require_binary("solana"), "find-program-derived-address", program_id,
            f"string:{name}", f"pubkey:{mint}",
        ]
        output = self.run(command, timeout=60, what="solana find-program-derived-address").stdout.decode()
        return output.strip().splitlines()[-1].strip()

    def deploy_cap_hook(self) -> str:
        """Deploy the already-built hook; this run never builds it."""
        so_copy = self.workdir / "cap_hook.so"
        key_copy = self.keys / "cap_hook-deploy.json"
        if not CAP_HOOK_SO.exists() or not CAP_HOOK_KEYPAIR.exists():
            raise ExperimentError("programs/cap_hook has no built .so or deploy keypair; this run does not build it")
        so_copy.write_bytes(CAP_HOOK_SO.read_bytes())
        key_copy.write_bytes(CAP_HOOK_KEYPAIR.read_bytes())
        os.chmod(key_copy, 0o600)
        self.cap_hook = keypair_pubkey(key_copy)
        say(f"  hook program {self.cap_hook} (cap_hook.so sha256={hashlib.sha256(so_copy.read_bytes()).hexdigest()}, copied not rebuilt)")
        output = self.solana(
            "program", "deploy", "--use-rpc", "--program-id", str(key_copy), str(so_copy),
            "--fee-payer", str(self.payer_key),
        )
        self.last_signature(output)
        say("  deployed")
        return self.cap_hook

    def _init_record(self, mint: str, record: str, data: bytes) -> dp.Instruction:
        return dp.Instruction(
            program_id=self.cap_hook,
            accounts=(
                dp.AccountMeta(self.payer, True, True),
                dp.AccountMeta(mint, False, False),
                dp.AccountMeta(record, False, True),
                dp.AccountMeta(SYSTEM_PROGRAM, False, False),
            ),
            data=data,
        )

    def wire_cap_hook(self, mint: str) -> dict:
        """Create the extra-account-metas account, the record, and stage a price."""
        extra_metas = self.derive_pda(self.cap_hook, "extra-account-metas", mint)
        record = self.derive_pda(self.cap_hook, "record", mint)
        face, cap_bps, price = 1_000_000_000, 2_500, 1_000_000_000
        self.send(
            [dp.Instruction(
                program_id=self.cap_hook,
                accounts=(
                    dp.AccountMeta(self.payer, True, True),
                    dp.AccountMeta(mint, False, False),
                    dp.AccountMeta(extra_metas, False, True),
                    dp.AccountMeta(SYSTEM_PROGRAM, False, False),
                ),
                data=bytes([0]) + base58.decode(record),
            )],
            what="cap_hook initialize extra-account-metas",
        )
        say(f"  extra-account-metas {extra_metas}")

        # The built artifact may predate the v2 record fields (the source tree is being
        # edited by another run), so try the v1 field list first and the v2 one only if
        # the program rejects the data. Which one it accepts is printed, not assumed.
        v1 = bytes([1]) + face.to_bytes(8, "little") + cap_bps.to_bytes(2, "little")
        v2 = v1 + (0).to_bytes(8, "little") + b"ON" + bytes([0])
        signature, status = self.send(
            [self._init_record(mint, record, v1)], what="cap_hook record (v1 layout)", allow_failure=True
        )
        layout = "v1"
        if not status["ok"]:
            signature, status = self.send(
                [self._init_record(mint, record, v2)], what="cap_hook record (v2 layout)", allow_failure=True
            )
            layout = "v2"
            if not status["ok"]:
                logs = self.transaction_logs(signature)["meta"].get("logMessages") or []
                raise ExperimentError(f"cap_hook refused both record layouts: {status['err']} :: {logs[-3:]}")
        record_value = self.account(record)
        data_length = len(base64.b64decode(record_value["data"][0]))
        say(f"  record {record} ({layout} layout accepted, data length {data_length})")
        self.send(
            [dp.Instruction(
                program_id=self.cap_hook,
                accounts=(dp.AccountMeta(record, False, True),),
                data=bytes([CAP_HOOK_TAG_SET_PENDING_PRICE]) + price.to_bytes(8, "little"),
            )],
            what=f"cap_hook stage price {price}",
        )
        return {"program": self.cap_hook, "extraMetas": extra_metas, "record": record,
                "layout": layout, "face": face, "capBps": cap_bps, "price": price}

    def clear_staged_price(self, record: str) -> None:
        self.send(
            [dp.Instruction(
                program_id=self.cap_hook,
                accounts=(dp.AccountMeta(record, False, True),),
                data=bytes([CAP_HOOK_TAG_SET_PENDING_PRICE]) + (0).to_bytes(8, "little"),
            )],
            what="cap_hook clear staged price",
        )

    def hook_section(self) -> None:
        """A fee-bearing transfer, a one-unit transfer, and a withdrawal with nothing staged."""
        say("")
        say("[6] one mint carrying both TransferFeeConfig and TransferHook(cap_hook)")
        try:
            self.deploy_cap_hook()
            mint, _ = self.create_mint("hooked", decimals=0, bps=1_500, maximum_fee=1_000_000, hook=self.cap_hook)
            details = self.checked_mint_config(mint, decimals=0, bps=1_500)
            say(f"  withdraw authority: {details['withdrawWithheldAuthority']}")
            wiring = self.wire_cap_hook(mint)
            source_ata = self.create_token_account(mint, self.payer)
            self.mint_to(mint, 10, 0)
            recipient_ata = self.create_token_account(mint, self.recipient)
            pool_ata = self.create_token_account(mint, self.pool)
            # The v2 metas list marks the record writable (the hook writes held_since_unix),
            # so the transfer must pass it writable or Token-2022 refuses with PrivilegeEscalation.
            # The transaction must carry the hook program's own account, or Token-2022's
            # CPI into it fails with "Unknown program" before the hook sees the amount.
            extra = (
                dp.AccountMeta(wiring["program"], False, False),
                dp.AccountMeta(wiring["extraMetas"], False, False),
                dp.AccountMeta(wiring["record"], False, True),
            )

            say("  fee-bearing transfer, amount 10, with the hook's extra account:")
            refused_sig, refused = self.send(
                [self.transfer_checked(
                    source=source_ata, mint=mint, destination=recipient_ata,
                    amount=10, decimals=0, extra_accounts=extra,
                )],
                what="transfer 10 (hook must refuse amount != 1)",
                allow_failure=True,
            )
            if refused["ok"]:
                raise ExperimentError("the hook admitted amount 10; that contradicts its refusal and is a finding")
            logs = self.transaction_logs(refused_sig)["meta"].get("logMessages") or []
            hook_lines = [line for line in logs if self.cap_hook in line or "ticketpath" in line]
            say(f"  refused: err={refused['err']}")
            for line in hook_lines[-4:]:
                say(f"    log: {line}")
            after_refusal = self.account(recipient_ata)
            say(f"  after refusal: recipient amount={token_amount(after_refusal)} "
                f"withheldAmount={withheld_amount(after_refusal)} (nothing moved)")
            if withheld_amount(after_refusal) != 0 or token_amount(after_refusal) != 0:
                raise ExperimentError("the refused transfer moved tokens")

            say("  one-unit transfer, same hook, staged price present:")
            accepted_sig, _ = self.send(
                [self.transfer_checked(
                    source=source_ata, mint=mint, destination=recipient_ata,
                    amount=1, decimals=0, extra_accounts=extra,
                )],
                what="transfer 1 (hook admits, fee withheld)",
            )
            accepted_logs = self.transaction_logs(accepted_sig)["meta"].get("logMessages") or []
            for line in [line for line in accepted_logs if "ticketpath" in line][-2:]:
                say(f"    log: {line}")
            after_transfer = self.account(recipient_ata)
            hooked_withheld = withheld_amount(after_transfer)
            hooked_amount = token_amount(after_transfer)
            say(f"  after:  recipient amount={hooked_amount} withheldAmount={hooked_withheld}")
            if hooked_withheld != fee_for(1, 1_500, 1_000_000):
                raise ExperimentError(f"the hooked mint withheld {hooked_withheld}, not the whole unit")

            say("  clear the staged price, then withdraw the withheld unit (nothing in the")
            say("  record admits a transfer any more, so a hook invocation here would refuse):")
            self.clear_staged_price(wiring["record"])
            withdraw_sig, _ = self.send(
                [self.withdraw_withheld(mint=mint, destination=pool_ata, sources=[recipient_ata])],
                what="WithdrawWithheldTokensFromAccounts",
            )
            after_withdraw = self.account(recipient_ata)
            pool = self.account(pool_ata)
            say(f"  after:  recipient amount={token_amount(after_withdraw)} "
                f"withheldAmount={withheld_amount(after_withdraw)}")
            say(f"  pool balance={token_amount(pool)}")
            if token_amount(pool) != hooked_withheld:
                raise ExperimentError("the destination did not receive the withheld unit")
            if withheld_amount(after_withdraw) != 0:
                raise ExperimentError("the source still reports a withheld amount after the withdrawal")

            self.measurements.append({
                "leg": "6",
                "mint": mint,
                "hook": self.cap_hook,
                "refusedAmount": 10,
                "refusedError": refused["err"],
                "refusedLog": hook_lines,
                "acceptedLog": [line for line in accepted_logs if "ticketpath" in line],
                "afterTransfer": _parsed_info(after_transfer),
                "afterWithdraw": _parsed_info(after_withdraw),
                "pool": _parsed_info(pool),
                "acceptedAmount": 1,
                "withheldOnHookedMint": hooked_withheld,
                "withdrawSignature": withdraw_sig,
                "withdrawSource": recipient_ata,
                "withdrawDestination": pool_ata,
                "poolBalance": token_amount(pool),
                "recordLayout": wiring["layout"],
            })
        except (ExperimentError, dp.PublishError) as exc:
            self.failures.append(f"[6] {exc}")
            say(f"  FAILED: {exc}")

    # -- the run

    def execute(self) -> int:
        self.prepare()
        self.say_plan()

        # Legs 1-4 do not involve the hook at all.
        plain = [
            ("1", 0, 500, 1_000_000, 1, 3),
            ("2", 0, 1_500, 1_000_000, 1, 3),
            ("3", 0, 1_500, 1_000_000, 10, 10),
            ("4", 9, 1_500, 1_000_000_000, 1_000_000_000, 1_000_000_000),
        ]
        for label, decimals, bps, maximum, amount, supply in plain:
            mint, _ = self.create_mint(label, decimals=decimals, bps=bps, maximum_fee=maximum)
            details = self.checked_mint_config(mint, decimals=decimals, bps=bps)
            say(f"  withdraw authority: {details['withdrawWithheldAuthority']}")
            source_ata = self.create_token_account(mint, self.payer)
            self.mint_to(mint, supply, decimals)
            recipient_ata = self.create_token_account(mint, self.recipient)
            record = self.measure(
                label, mint=mint, decimals=decimals, bps=bps, maximum_fee=maximum, amount=amount,
                mint_authority_ata=source_ata, recipient_ata=recipient_ata,
            )
            record["mintConfig"] = details

        self.hook_section()

        self.write_results()
        self.summary()
        return 0 if not self.failures else 1

    def say_plan(self) -> None:
        say("")
        say("What is measured: withheldAmount read from getAccountInfo(jsonParsed) on the")
        say("recipient token account, before and after a TransferChecked whose amount the")
        say("runtime itself turns into a fee. No client-side fee arithmetic is passed in.")
        say("")

    def write_results(self) -> None:
        path = self.workdir / "measurements.json"
        path.write_text(json.dumps({"measurements": self.measurements, "failures": self.failures}, indent=2) + "\n")
        say(f"\nresults: {path.relative_to(REPO_ROOT)}")

    def summary(self) -> None:
        say("")
        say("measured withheldAmount by leg (base units):")
        for record in self.measurements:
            if "afterWithheld" in record:
                say(
                    f"  [{record['leg']}] decimals={record['decimals']} bps={record['bps']} "
                    f"amount={record['amount']} -> withheldAmount={record['afterWithheld']} "
                    f"(recipient {record['recipientAmount']}; ceiling {record['ceilingFee']}, floor {record['floorFee']})"
                )
        if self.failures:
            say("")
            say("failures:")
            for failure in self.failures:
                say(f"  {failure}")
        else:
            say("")
            say("no failures")

    def shutdown(self) -> None:
        if self.validator is not None:
            self.validator.stop()


def parse_arguments(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Measure Token-2022's withholding on a one-unit ticket.")
    parser.add_argument("--workdir", default=str(DEFAULT_WORKDIR), help="ledger, keys and results (git-ignored)")
    parser.add_argument("--url", default=None, help="attach to a loopback validator instead of starting one")
    parser.add_argument("--deadline", type=float, default=DEFAULT_DEADLINE, help="whole-run bound in seconds")
    parser.add_argument("--keep", action="store_true", help="keep the previous run's ledger and keys")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_arguments(argv)
    experiment = Experiment(args)
    try:
        return experiment.execute()
    except (ExperimentError, dp.PublishError) as exc:
        say(f"\nfailed: {exc}")
        return 1
    finally:
        experiment.shutdown()


if __name__ == "__main__":
    sys.exit(main())

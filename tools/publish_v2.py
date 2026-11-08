#!/usr/bin/env python3
"""Publish `cap_hook` v2 to a LOCAL validator, and prove what it does there.

    python3 tools/publish_v2.py

What it publishes: this program, under the keypair at
`programs/cap_hook/target/deploy/v2-keypair.json` — a key that is **not** the frozen devnet one,
created if absent and reused if present so the program id is stable across reruns on this
machine — to a `solana-test-validator` this file starts and kills. Nothing here can reach devnet
with a transaction and nothing here opens the frozen devnet artefacts. The one devnet
conversation is the validator's own `--clone` of Token-2022 and the memo program, which reads
program code and is how the existing local path already works.

The frozen devnet deploy (`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, recorded in
`records/devnet-artefacts.json`) is untouchable: this file does not name it as a deploy target,
refuses to proceed if the generated program id happens to equal it, and never writes those two
paths. `tools/devnet_publish.py` is imported for its RPC, its transaction builder and its
signer isolation, and is not modified or wrapped: it has a `__main__` guard (checked below
before the import), so importing it runs nothing.

What it proves, with real transactions, each with its own signature:

    (a) InitializeRecord(face 1e9, cap 2500, band_low 9e8, "ZZ", policy 0) signed by the mint's
        authority, then the record decoded back: authority is that authority, held_since_unix 0.
    (b) a transfer priced at band_low is admitted, and the program's log names the jurisdiction.
    (c) a transfer priced at band_low - 1 is refused with 6021.
    (d) a transfer priced at the cap is admitted; at cap + 1 refused with 6010.
    (e) InitializeRecord with policy 2 is refused with 6023, and with a floor above the
        ceiling refused with 6022.
    (f) after an admitted transfer, the record's held_since_unix is not 0: the clock write
        through Token-2022's CPI, which the Rust unit tests cannot reach, and
        pending_price_lamports is 0: the staging was consumed, so one stage is one sale.
    (g) the review's exploit, re-run against the patched program: the phase-1 buyer, who is not
        the record's authority, stages a price of 1 and is refused 6026; the same key sends
        SetStatus(0) and is refused 6026 again, with the record's bytes unchanged both times.

and phase two, on a fresh ledger and a second validator:

    a band is published and read back; a second forecast for the same as-of is refused 6024 and
    leaves the first unchanged; a score is written with the forecast's bytes unchanged; a second
    score for the same forecast is refused 6025; a band signed by a non-authority is refused
    6026; a band with low > high is refused 6022; a band with no observations and no refusal is
    refused 6032; a band whose as_of_slot is in the future is refused 6033; a forecast backdated
    a year is refused 6029; a score below the band's width is refused 6030; and a *miss*
    (realised outside the band) is scored with covered = 0, which no earlier artefact had.

Refusals go with `skipPreflight` on purpose. With the preflight check on, a transaction the
hook will reject never gets a signature and there is nothing to look up; off, the refusal
lands as a failed transaction with its own signature and its own error.

The artefact is `records/onchain-v2.local.json`, git-ignored alongside the other run
artefacts: a local rehearsal on this machine, not evidence of anything on a public cluster.
`tests/test_onchain_v2_live.py` runs this same sequence and asserts (a)-(f) item by item.
"""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
for _path in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Import the existing publish path for its primitives: RPC with bounded retries, the message
# compiler, the out-of-process signer, and the validator class that kills itself on every exit
# path. Before the import, prove there is nothing to run at import time.
_DEVNET_PUBLISH = TOOLS_DIR / "devnet_publish.py"
_DEVNET_SOURCE = _DEVNET_PUBLISH.read_text(encoding="utf-8")
if 'if __name__ == "__main__":' not in _DEVNET_SOURCE:
    raise SystemExit(
        "tools/devnet_publish.py has no __main__ guard, so importing it would run it. "
        "Nothing was published."
    )

import devnet_publish as dp  # noqa: E402
from ticketpath.core import base58, forecast_score  # noqa: E402
from ticketpath.onchain import v2  # noqa: E402

if Path(dp.__file__).resolve() != _DEVNET_PUBLISH:
    raise SystemExit(f"imported devnet_publish from {dp.__file__}, not the checked file")

# -- what is deployed, and where -------------------------------------------------

PROGRAM_DIR = REPO_ROOT / "programs" / "cap_hook"
SO_PATH = PROGRAM_DIR / "target" / "deploy" / "cap_hook.so"
# The frozen deploy keypair is `cap_hook-keypair.json` and it is never named here. This is a
# different file, regenerated on every run, so the program id is new every run.
DEPLOY_KEYPAIR = PROGRAM_DIR / "target" / "deploy" / "v2-keypair.json"
ARTEFACT = REPO_ROOT / "records" / "onchain-v2.local.json"
RUN_ROOT = REPO_ROOT / ".swarm-runs"

# The devnet program, quoted so the guard below can refuse to touch it. It is public data (it
# is in records/devnet-artefacts.json and the README) and it is not a deploy target.
FROZEN_DEVNET_PROGRAM = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"

CHECKER_VERSION = "onchain-v2-local-2026-11-08-review2"

# The operator's own arguments, and the design's worked pair (§3.10).
FACE = 1_000_000_000
CAP_BPS = 2500
BAND_LOW = 900_000_000
JURISDICTION = "ZZ"
POLICY_CAPPED = 0
CEILING = FACE + FACE * CAP_BPS // 10_000  # 1_250_000_000
OVER_CEILING = CEILING + 1
TICKETS = 4

# The forecast phase's fixed arguments. The band is wider than the record's floor/cap on
# purpose, because the feed is the model's estimate and the record is the transfer rule. The
# score example is the covered case, so the arithmetic is exactly the width of the band in
# micro-lamports.
#
# The as-of is **not** a constant any more. `LogForecast` refuses an `as_of_unix` earlier than
# the clock minus `FORECAST_BACKDATE_TOLERANCE_SECONDS`, and a constant in this file would be a
# date in the past by the next run: the artefact's own forecast was as-of 1760000000 and was
# created 394.9 days later, which is the defect the review measured. The instants are computed
# from the clock at the start of each phase, forward of it, so the forecast is logged *before*
# the instant it is about.
PHASE2_BAND_LOW = 900_000_000
PHASE2_BAND_HIGH = 1_100_000_000
PHASE2_SAMPLE_N = 42
PHASE2_MODEL_HASH = hashlib.sha256(b"ticketpath-model-v2-local").digest()
PHASE2_REALISED = 1_000_000_000
NON_AUTHORITY_FUNDING = 1_000_000_000
#: How far ahead of the clock a forecast's as-of sits. Long enough that the transaction cannot
#: land before it, short enough to be a forecast about the near future and not a fiction.
FORECAST_LEAD_SECONDS = 120
#: How far in the past the backdating refusal reaches: a year, so nobody can argue about it.
BACKDATED_BY_SECONDS = 365 * 24 * 60 * 60

# `programs/cap_hook/src/error.rs`, in one place. A code beside its number is what makes a
# refusal readable; the numbers are the interface and are never renamed.
ERROR_NAMES = {
    6008: "E_AMOUNT_NOT_ONE",
    6009: "E_TRANSFER_NOT_STAGED",
    6010: "E_CAP_EXCEEDED",
    6013: "E_TICKET_NOT_VALID",
    6020: "E_WRONG_EXTRA_ACCOUNT",
    6021: "E_BELOW_FLOOR",
    6022: "E_BAND_UNSATISFIABLE",
    6023: "E_POLICY_INVALID",
    6024: "E_FORECAST_EXISTS",
    6025: "E_ALREADY_SCORED",
    6026: "E_NOT_AUTHORITY",
    6027: "E_REBATE_NOT_DUE",
    6028: "E_REBATE_UNAVAILABLE",
    6029: "E_FORECAST_BACKDATED",
    6030: "E_SCORE_BELOW_WIDTH",
    6031: "E_BAND_TOO_WIDE",
    6032: "E_BAND_EMPTY",
    6033: "E_AS_OF_AHEAD",
}

TOKEN_INSTRUCTION_TRANSFER_CHECKED = 12


class ProofFailed(RuntimeError):
    """A step did not do what this file says it does. Nothing is recorded as a result."""


# -- small helpers ---------------------------------------------------------------


def free_port_range(width: int = 40, tries: int = 64) -> int:
    """The first base port whose next `width` ports are all bindable, checked and released."""
    for _ in range(tries):
        base = dp.free_port()
        if base + width >= 65535:
            continue
        held = []
        ok = True
        for port in range(base, base + width):
            try:
                probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                probe.bind(("127.0.0.1", port))
                held.append(probe)
            except OSError:
                ok = False
                break
        for probe in held:
            probe.close()
        if ok:
            return base
    raise ProofFailed(f"no free block of {width} ports after {tries} tries")


class PhaseValidator(dp.LocalValidator):
    """`dp.LocalValidator` with its own gossip port and dynamic port range.

    The default gossip port 8000 is machine-wide and another session's local validator can
    already hold it; `dp.LocalValidator` does not expose `--gossip-port`, and
    `tools/devnet_publish.py` is not modified. This subclass repeats `start` with those two
    flags added, so the two validators this file starts (one per phase) get private ports.
    """

    def start(self) -> None:
        if not dp.which("solana-test-validator"):
            raise dp.PublishError("solana-test-validator is not on PATH")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        width = 40
        for _ in range(8):
            base = free_port_range(width)
            if self.port not in range(base, base + width) and self.faucet_port not in range(base, base + width):
                break
        else:
            raise dp.PublishError("could not find a port range clear of the RPC and faucet ports")
        command = [
            dp.which("solana-test-validator") or "solana-test-validator",
            *(["--reset"] if self.reset else []),
            "--quiet",
            "--ledger", str(self.ledger),
            "--rpc-port", str(self.port),
            "--faucet-port", str(self.faucet_port),
            # Private gossip and dynamic ports: two test validators on one machine otherwise
            # both try to bind 8000 and the second exits before it answers.
            "--gossip-port", str(base),
            "--dynamic-port-range", f"{base + 1}-{base + width}",
            *(["--mint", self.fund] if self.fund else []),
            "--clone-upgradeable-program", dp.TOKEN_2022_PROGRAM,
            "--clone", dp.chain_client.memo_program_id("devnet"),
            "--url", dp.CLUSTER_URLS["devnet"],
        ]
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
        )
        atexit.register(self.stop)
        for signal_name in ("SIGINT", "SIGTERM", "SIGHUP"):
            signal.signal(getattr(signal, signal_name), self._on_signal)
        deadline = time.monotonic() + dp.BOUND_VALIDATOR_START
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                tail = (self.process.stdout.read() or "")[-1500:] if self.process.stdout else ""
                raise dp.PublishError(f"solana-test-validator exited before it answered:\n{tail}")
            try:
                if dp.rpc(self.rpc_url, "getHealth", [], timeout=2, attempts=1) == "ok":
                    return
            except dp.PublishError:
                time.sleep(0.5)
        raise dp.PublishError(
            f"solana-test-validator did not answer on {self.rpc_url} within "
            f"{dp.BOUND_VALIDATOR_START:g}s"
        )


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime | None = None) -> str:
    moment = moment or now()
    return moment.strftime("%Y-%m-%dT%H:%M:%S.") + f"{moment.microsecond // 1000:03d}Z"


def relative(path: Path) -> str:
    """A repository-relative path, so the artefact names no home directory."""
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return path.name


def custom_code(err) -> int | None:
    """The program's own error number out of an `InstructionError`, or None."""
    if isinstance(err, dict) and isinstance(err.get("InstructionError"), list):
        detail = err["InstructionError"][1]
        if isinstance(detail, dict) and isinstance(detail.get("Custom"), int):
            return detail["Custom"]
    return None


def error_text(err) -> str | None:
    if err is None:
        return None
    code = custom_code(err)
    if code is None:
        return json.dumps(err, sort_keys=True)
    name = ERROR_NAMES.get(code, "unknown")
    return f"custom program error: 0x{code:x} ({code} {name})"


def ticketpath_logs(logs) -> list[str]:
    """Only this program's own lines, so a log excerpt reads as the decision it recorded."""
    return [line for line in (logs or []) if "ticketpath:" in line]


def account_data(value: dict) -> bytes:
    """The account's bytes. `getAccountInfo` answers `[payload, encoding]`, in that order."""
    data = value.get("data")
    if not isinstance(data, list) or len(data) != 2:
        raise ProofFailed("an account arrived in an encoding this reader does not handle")
    raw, encoding = data
    if encoding != "base64":
        raise ProofFailed(f"account data encoding {encoding!r} is not base64")
    return base64.b64decode(raw)


# -- the run -----------------------------------------------------------------------


class LocalProof:
    """One publish, one proof, one artefact. Every child process dies with it."""

    def __init__(self, *, say=print):
        self._say = say
        self.pid = os.getpid()
        self.ledger = RUN_ROOT / f"v2-ledger-{self.pid}"
        self.keys = RUN_ROOT / f"v2-keys-{self.pid}"
        self.validator = None
        self.ctx = None
        self.started = now()
        self.steps: dict[str, dict] = {}
        self.program_id: str | None = None
        self.deploy_keypair: Path | None = None
        self.payer: str | None = None
        self.payer_keypair: Path | None = None
        self.mint: str | None = None
        self.record: str | None = None
        self.extra_metas: str | None = None
        self.seller_ata: str | None = None
        self.buyer: str | None = None
        self.buyer_ata: str | None = None
        # The forward-dated as-of instants, set by `_set_forecast_instants` at the start of each
        # phase's `_wire`. None until the clock has been read.
        self.forecast_at: int | None = None
        self.forecast_miss_at: int | None = None

    # -- output -----------------------------------------------------------------

    def say(self, line: str) -> None:
        self._say(line)

    @property
    def rpc(self) -> str:
        if self.validator is None:
            raise ProofFailed("no validator is running")
        return self.validator.rpc_url

    # -- the run ----------------------------------------------------------------

    def run(self) -> dict:
        try:
            self._toolchain()
            self._keys()
            self._start_validator()
            self._deploy()
            self._wire()
            proof_a = self._proof_a()
            self._fund_tickets()
            proof_b = self._proof_b()
            proof_f = self._proof_f()
            proof_c = self._proof_c()
            proof_d = self._proof_d()
            proof_e = self._proof_e()
            proof_g = self._proof_g()
            proofs = {
                "a": proof_a,
                "b": proof_b,
                "c": proof_c,
                "d": proof_d,
                "e": proof_e,
                "f": proof_f,
                "g": proof_g,
            }

            # Snapshot the first phase's identity and end state: the second phase starts a
            # fresh ledger and overwrites `self.mint`, so the artefact's phase-1 fields must
            # be taken now rather than after it.
            record, _address, slot = self._read_record(self.mint)
            phase1 = {
                "mint": self.mint,
                "record": self.record,
                "extraMetas": self.extra_metas,
                "seller": self.seller_ata,
                "buyer": self.buyer,
                "buyerAta": self.buyer_ata,
                "recordAtEnd": record.as_dict(),
                "recordAtEndSlot": slot,
                "pdas": self._pda_crosscheck,
                "ledger": relative(self.ledger),
                "steps": self.steps,
            }
            phase2 = self._phase2()
            self._stop()
            return self._artefact(proofs, phase1=phase1, phase2=phase2)
        finally:
            self._stop()

    def _toolchain(self) -> None:
        for binary in ("solana", "spl-token", "solana-keygen"):
            if not dp.which(binary):
                raise ProofFailed(f"{binary} is not on PATH; the Solana block in ~/.profile sets it")
        if not SO_PATH.exists():
            raise ProofFailed(f"no program at {relative(SO_PATH)}; build it with cargo-build-sbf first")
        # The two frozen paths, named so the guard is readable. Neither is opened or written
        # by anything in this file; the check is here so an edit to the constants above cannot
        # silently point this run at them.
        frozen = (
            REPO_ROOT / "records" / "devnet-artefacts.json",
            REPO_ROOT / "records" / "devnet-progress.json",
            PROGRAM_DIR / "target" / "deploy" / "cap_hook-keypair.json",
        )
        for path in (ARTEFACT, DEPLOY_KEYPAIR):
            if path.resolve() in {item.resolve() for item in frozen}:
                raise ProofFailed(f"{relative(path)} is a frozen devnet artefact; this run will not touch it")

    def _keys(self) -> None:
        """Fresh keypairs, fresh ledger. A pid that repeats must not inherit a stale run."""
        for directory in (self.ledger, self.keys):
            shutil.rmtree(directory, ignore_errors=True)
        self.keys.mkdir(parents=True, exist_ok=True)
        os.chmod(self.keys, 0o700)
        self.payer_keypair = self._new_keypair(self.keys / "payer.json")
        self.payer = self._pubkey(self.payer_keypair)
        self.say(f"keys: payer {self.payer} (funded at genesis, keypair on disk only)")

    def _new_keypair(self, path: Path) -> Path:
        """Generate a keypair and never read it. 0600, in a 0700 directory, never printed."""
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        path.unlink(missing_ok=True)
        dp.run(
            [dp.which("solana-keygen") or "solana-keygen", "new", "--silent", "--no-bip39-passphrase", "-o", str(path)],
            timeout=60,
            what=f"solana-keygen new ({path.name})",
        )
        os.chmod(path, 0o600)
        return path

    def _pubkey(self, path: Path) -> str:
        output = dp.run(
            [dp.which("solana-keygen") or "solana-keygen", "pubkey", str(path)],
            timeout=30,
            what=f"solana-keygen pubkey ({path.name})",
        )
        address = output.strip().splitlines()[-1].strip() if output.strip() else ""
        if not address:
            raise ProofFailed(f"solana-keygen printed no address for {path.name}")
        return address

    def _start_validator(self) -> None:
        # The v2 deploy keypair is reused when it is already on disk, so the program id is
        # stable across the two phases and across proof reruns. It is a new program relative
        # to the frozen devnet id, which is the property that matters; a new keypair on every
        # run would only make the artefact's program id change for no evidence.
        if DEPLOY_KEYPAIR.exists():
            deploy_keypair = DEPLOY_KEYPAIR
        else:
            deploy_keypair = self._new_keypair(DEPLOY_KEYPAIR)
        self.program_id = self._pubkey(deploy_keypair)
        if self.program_id == FROZEN_DEVNET_PROGRAM:
            raise ProofFailed(
                "the generated keypair unlocks the frozen devnet program id; refusing to deploy. "
                "Delete the keypair and run again."
            )
        self.deploy_keypair = deploy_keypair
        self.say(f"program: {self.program_id} (a keypair of its own, never the devnet one)")

        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        port = dp.free_port()
        faucet_port = dp.free_port()
        while faucet_port == port:
            faucet_port = dp.free_port()
        self.validator = PhaseValidator(
            ledger=self.ledger,
            port=port,
            faucet_port=faucet_port,
            # Not `--reset`: the directory is removed above, so this ledger is fresh, and
            # keeping it afterwards is what lets the signatures be re-checked.
            reset=False,
            fund=self.payer,
        )
        self.validator.start()
        if not self.rpc.startswith("http://127.0.0.1:"):
            raise ProofFailed(f"the validator answered at {self.rpc}, which is not a local address")
        self.ctx = dp.Context(
            cluster="localnet",
            rpc_url=self.rpc,
            keypair=self.payer_keypair,
            buyer_keypair=self.keys / "buyer.json",
            out=ARTEFACT,
        )
        # Route the imported helpers' own narration through this run's sink, so `--quiet`
        # is quiet and a test run's output reads as one log. This rebinds an instance
        # attribute; tools/devnet_publish.py itself is untouched.
        self.ctx.say = self.say
        self.say(
            f"validator: ledger {relative(self.ledger)}, {self.rpc}, "
            "Token-2022 and the devnet memo program cloned"
        )

    def _stop(self) -> None:
        if self.validator is not None:
            self.validator.stop()
            self.validator = None

    # -- one step, recorded -------------------------------------------------------

    def _transact(self, name: str, instructions: list, *, what: str, skip_preflight: bool = False) -> dict:
        """Send one transaction that must succeed, and record its signature, slot and clock."""
        return self._transact_with(self.ctx, name, instructions, what=what, skip_preflight=skip_preflight)

    def _transact_with(self, ctx, name: str, instructions: list, *, what: str, skip_preflight: bool = False) -> dict:
        signature, status = dp.send_instructions(
            ctx, instructions, what=what, skip_preflight=skip_preflight
        )
        detail = self._detail(signature, status)
        self.steps[name] = detail
        return detail

    def _attempt(self, name: str, instructions: list, *, what: str) -> dict:
        """Send one transaction that is expected to fail, and keep the signature it failed with."""
        return self._attempt_with(self.ctx, name, instructions, what=what)

    def _attempt_with(self, ctx, name: str, instructions: list, *, what: str) -> dict:
        signature, status = dp.send_instructions(
            ctx, instructions, what=what, skip_preflight=True, allow_failure=True
        )
        detail = self._detail(signature, status)
        self.steps[name] = detail
        return detail

    def _detail(self, signature: str, status: dict) -> dict:
        if not status.get("ok") and status.get("err") is None:
            raise ProofFailed(f"{signature}: the cluster reported a failure with no error")
        transaction = self._transaction(signature)
        detail = {
            "signature": signature,
            "slot": status.get("slot") if status.get("slot") is not None else transaction.get("slot"),
            "blockTime": transaction.get("blockTime"),
            "error": error_text(status.get("err")),
            "errorCode": custom_code(status.get("err")),
            "ok": bool(status.get("ok")),
            "logs": ticketpath_logs(transaction.get("logs")),
            "wallClock": iso(),
        }
        self.say(
            f"  {detail['signature']} (slot {detail['slot']})"
            + (f" REFUSED {detail['error']}" if detail["error"] else " ok")
        )
        return detail

    def _transaction(self, signature: str) -> dict:
        """The landed transaction's metadata, including the logs a refusal leaves behind."""
        result = None
        for attempt in range(12):
            result = dp.rpc(
                self.rpc,
                "getTransaction",
                [signature, {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 0}],
            )
            if result:
                break
            time.sleep(0.5)
        if not result:
            raise ProofFailed(f"getTransaction returned nothing for {signature}")
        meta = result.get("meta") or {}
        return {
            "slot": result.get("slot"),
            "blockTime": result.get("blockTime"),
            "err": meta.get("err"),
            "logs": meta.get("logMessages") or [],
        }

    def _account_info(self, address: str, *, looks: int = 20, interval: float = 0.25) -> tuple:
        """`(value, slot)` at `confirmed`, waiting out the confirmed-to-finalized lag.

        A transaction that has just landed is confirmed before the account it created is
        readable at the default commitment. A single read is the stale negative this
        repository has already paid for; this one waits, bounded, and then says "absent".
        """
        for look in range(looks):
            result = dp.rpc(
                self.rpc,
                "getAccountInfo",
                [address, {"encoding": "base64", "commitment": "confirmed"}],
            )
            value = (result or {}).get("value")
            if value:
                return value, ((result or {}).get("context") or {}).get("slot")
            if look + 1 < looks:
                time.sleep(interval)
        return None, None

    def _read_account(self, address: str, decoder) -> tuple[dict, int | None]:
        value, slot = self._account_info(address)
        if not value:
            raise ProofFailed(f"no account at {address}")
        return decoder(account_data(value)), slot

    def _read_record(self, mint: str) -> tuple[dict, str, int | None]:
        address = v2.record_address(self.program_id, mint)[0]
        record, slot = self._read_account(address, v2.decode_ticket_record)
        return record, address, slot

    # -- deploying ----------------------------------------------------------------

    def _deploy(self) -> None:
        output = dp.run(
            [
                dp.which("solana") or "solana",
                "--url", self.rpc,
                "program", "deploy", str(SO_PATH),
                "--program-id", str(self.deploy_keypair),
                "--keypair", str(self.payer_keypair),
            ],
            timeout=dp.BOUND_DEPLOY,
            what="solana program deploy",
        )
        signature = dp.last_base58(output)
        if signature is None:
            raise ProofFailed("solana program deploy printed no signature; nothing to confirm")
        status = dp.confirm(self.rpc, signature)
        if not status["ok"]:
            raise ProofFailed(f"the deploy failed: {error_text(status['err'])} ({signature})")
        # A just-confirmed deploy is visible at `confirmed` before it is visible at the RPC's
        # default commitment, and a single read right after the confirmation is the stale
        # negative this repository has already paid for once. Bounded, then honest.
        executable = False
        for _look in range(30):
            if self._is_executable(self.program_id):
                executable = True
                break
            time.sleep(0.5)
        if not executable:
            tail = "\n".join(line for line in output.splitlines()[-6:] if line.strip())
            raise ProofFailed(f"{self.program_id} is not executable after the deploy:\n{tail}")
        self.steps["deploy"] = {
            "signature": signature,
            "slot": status.get("slot"),
            "blockTime": self._transaction(signature).get("blockTime"),
            "error": None,
            "errorCode": None,
            "ok": True,
            "logs": [],
            "wallClock": iso(),
        }
        self.say(f"  deploy {signature} (slot {status.get('slot')}), executable")

    def _is_executable(self, address: str) -> bool:
        result = dp.rpc(
            self.rpc, "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}]
        )
        value = (result or {}).get("value") or {}
        return bool(value.get("executable"))

    def _pdas_agree_with_the_toolchain(self) -> None:
        """Every seed shape, derived here and by the CLI, compared. A mismatch stops the run."""
        mint = self.mint
        forecast = v2.forecast_address(self.program_id, mint, self.forecast_at)[0]
        ours = {
            "record": v2.record_address(self.program_id, mint)[0],
            "extra-account-metas": v2.extra_account_meta_list_address(self.program_id, mint)[0],
            "band": v2.band_address(self.program_id, mint)[0],
            "forecast": forecast,
            "score": v2.score_address(self.program_id, forecast)[0],
            "fee-authority": v2.fee_authority_address(self.program_id, mint)[0],
            "rebate-pool": v2.rebate_pool_address(self.program_id, mint)[0],
        }
        self._pda_crosscheck = {}
        seeds = {
            "record": [f"string:record", f"pubkey:{mint}"],
            "extra-account-metas": [f"string:extra-account-metas", f"pubkey:{mint}"],
            "band": [f"string:band", f"pubkey:{mint}"],
            "forecast": ["string:forecast", f"pubkey:{mint}", f"i64le:{self.forecast_at}"],
            "score": ["string:score", f"pubkey:{forecast}"],
            "fee-authority": ["string:fee-authority", f"pubkey:{mint}"],
            "rebate-pool": ["string:rebate-pool", f"pubkey:{mint}"],
        }
        for name, seed_list in seeds.items():
            theirs = dp.run(
                [
                    dp.which("solana") or "solana",
                    "--url", self.rpc,
                    "find-program-derived-address", self.program_id, *seed_list,
                ],
                timeout=60,
                what="solana find-program-derived-address",
            ).strip().splitlines()[-1].strip()
            if theirs != ours[name]:
                raise ProofFailed(
                    f"{name}: ticketpath/onchain/v2.py derives {ours[name]} and the toolchain derives {theirs}"
                )
            self._pda_crosscheck[name] = theirs
        self.say(f"pdas: all {len(ours)} seed shapes agree with solana find-program-derived-address")

    # -- mint, accounts, program instructions -------------------------------------

    def _create_mint(self, label: str) -> str:
        keypair = self.keys / f"{label}-mint.json"
        mint = self._pubkey(self._new_keypair(keypair))
        output = dp.run(
            dp.spl(self.ctx, "create-token", "--decimals", "0", "--transfer-hook", self.program_id, str(keypair)),
            timeout=dp.BOUND_TOKEN,
            what="spl-token create-token",
        )
        found = dp.first_pubkey(output)
        if found and found != mint:
            raise ProofFailed(f"spl-token created {found}, not the {mint} this run chose")
        self.say(f"  mint {mint}: Token-2022, 0 decimals, transfer hook -> {self.program_id}")
        return mint

    def _instruction_init_extra_metas(self, mint: str) -> tuple[str, "dp.Instruction"]:
        address = v2.extra_account_meta_list_address(self.program_id, mint)[0]
        accounts = v2.initialize_extra_account_meta_list_accounts(
            payer=self.payer, mint=mint, extra_metas=address
        )
        instruction = dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            # No argument: the program derives the record it names from the mint, so a wrong
            # record cannot be written into a create-once list.
            data=v2.initialize_extra_account_meta_list(),
        )
        return address, instruction

    def _instruction_init_record(self, mint: str, *, face: int, cap_bps: int, band_low: int, policy: int):
        address = v2.record_address(self.program_id, mint)[0]
        accounts = v2.initialize_record_accounts(
            payer=self.payer, mint=mint, record=address, mint_authority=self.payer
        )
        instruction = dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.initialize_record(
                face_value_lamports=face,
                cap_bps=cap_bps,
                band_low_lamports=band_low,
                jurisdiction=JURISDICTION,
                policy=policy,
            ),
        )
        return address, instruction

    def _instruction_stage(self, record: str, price: int, *, mint: str | None = None,
                           authority: str | None = None) -> "dp.Instruction":
        """Tag 2, `[authority (signer), record, mint]`. Refused 6026 for any other signer."""
        accounts = v2.set_pending_price_accounts(
            authority=authority or self.payer, record=record, mint=mint or self.mint
        )
        return dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.set_pending_price(price_lamports=price),
        )

    def _instruction_set_status(self, record: str, status: int, *, mint: str | None = None,
                                authority: str | None = None) -> "dp.Instruction":
        """Tag 3, the same accounts as tag 2 and the same 6026."""
        accounts = v2.set_status_accounts(
            authority=authority or self.payer, record=record, mint=mint or self.mint
        )
        return dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.set_status(status=status),
        )

    def _instruction_transfer(self, *, mint: str, source: str, destination: str) -> "dp.Instruction":
        """`transfer_checked` with the accounts Token-2022 resolves for a hooked mint.

        The order is the SPL offchain helper's: `[source, mint, destination, authority]`, then
        the resolved extra accounts, then the hook program, then the extra-account-metas PDA.
        The record is **writable** because v2's hook writes `held_since_unix` into it; a
        read-only record here is a hook that runs, refuses correctly, and never records a hold
        (its `is_writable` branch then logs exactly that).
        """
        return dp.Instruction(
            program_id=dp.TOKEN_2022_PROGRAM,
            accounts=(
                dp.AccountMeta(source, False, True),
                dp.AccountMeta(mint, False, False),
                dp.AccountMeta(destination, False, True),
                dp.AccountMeta(self.payer, True, False),
                dp.AccountMeta(self.record, False, True),
                dp.AccountMeta(self.program_id, False, False),
                dp.AccountMeta(self.extra_metas, False, False),
            ),
            data=bytes([TOKEN_INSTRUCTION_TRANSFER_CHECKED])
            + (1).to_bytes(8, "little")
            + bytes([0]),
        )

    def _instruction_publish_band(self, *, authority: str, low: int, high: int,
                                  as_of_slot: int, sample_n: int, refused: int,
                                  model_hash: bytes) -> tuple[str, "dp.Instruction"]:
        band = v2.band_address(self.program_id, self.mint)[0]
        accounts = v2.publish_band_accounts(
            authority=authority, record=self.record, band=band, mint=self.mint
        )
        instruction = dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.publish_band(
                low=low,
                high=high,
                as_of_slot=as_of_slot,
                sample_n=sample_n,
                refused=refused,
                model_hash=model_hash,
            ),
        )
        return band, instruction

    def _instruction_log_forecast(self, *, authority: str, low: int, high: int,
                                  as_of_unix: int, sample_n: int, model_hash: bytes,
                                  scoring_rule_hash: bytes) -> tuple[str, "dp.Instruction"]:
        forecast = v2.forecast_address(self.program_id, self.mint, as_of_unix)[0]
        accounts = v2.log_forecast_accounts(
            authority=authority, record=self.record, forecast=forecast, mint=self.mint
        )
        instruction = dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.log_forecast(
                low=low,
                high=high,
                as_of_unix=as_of_unix,
                sample_n=sample_n,
                model_hash=model_hash,
                scoring_rule_hash=scoring_rule_hash,
            ),
        )
        return forecast, instruction

    def _instruction_score_forecast(self, *, scorer: str, realised_lamports: int,
                                    interval_score_micro: int,
                                    as_of: int | None = None) -> tuple[str, str, "dp.Instruction"]:
        as_of = self.forecast_at if as_of is None else as_of
        forecast = v2.forecast_address(self.program_id, self.mint, as_of)[0]
        score = v2.score_address(self.program_id, forecast)[0]
        accounts = v2.score_forecast_accounts(scorer=scorer, forecast=forecast, score=score)
        instruction = dp.Instruction(
            program_id=self.program_id,
            accounts=tuple(dp.AccountMeta(*account) for account in accounts),
            data=v2.score_forecast(
                realised_lamports=realised_lamports,
                interval_score_micro=interval_score_micro,
            ),
        )
        return forecast, score, instruction

    def _raw_account(self, address: str) -> tuple[bytes, int | None]:
        """The account's exact bytes and the slot they were read at."""
        value, slot = self._account_info(address)
        if not value:
            raise ProofFailed(f"no account at {address}")
        return account_data(value), slot

    def _fund_wallet(self, address: str, lamports: int) -> dict:
        """Move lamports from the payer to a second signer so it can pay its own fee."""
        data = (2).to_bytes(4, "little") + lamports.to_bytes(8, "little")
        instruction = dp.Instruction(
            program_id=dp.SYSTEM_PROGRAM,
            accounts=(dp.AccountMeta(self.payer, True, True), dp.AccountMeta(address, False, True)),
            data=data,
        )
        return self._transact(
            "v2FundNonAuthority", [instruction], what="fund the non-authority signer"
        )

    def _second_phase_context(self) -> "dp.Context":
        """A second context signed by the buyer, for the refusals that must not be the authority's.

        `dp.send_instructions` uses `ctx.keypair` as both fee payer and signer, so a second
        Context is the way to send a transaction that is *not* signed by the record's authority
        without adding an argument to `tools/devnet_publish.py`. Used in both phases: the band
        refusal in phase two, and the tag 2 / tag 3 refusals in phase one (the review's exploit).
        """
        ctx = dp.Context(
            cluster="localnet",
            rpc_url=self.rpc,
            keypair=self.ctx.buyer_keypair,
            buyer_keypair=self.ctx.buyer_keypair,
            out=ARTEFACT,
        )
        ctx.say = self.say
        return ctx

    # -- the proofs ----------------------------------------------------------------

    def _set_forecast_instants(self) -> None:
        """The two as-of instants this phase logs, both **ahead of the clock**.

        `LogForecast` refuses an as-of earlier than the clock minus a stated tolerance, so a
        constant here would make every rerun a backdated forecast, which is exactly the defect
        the review measured in the previous artefact (as-of 1760000000, created at 1794120524,
        394.9 days later). The validator's clock is the host's wall clock; `_proof_f` shows the
        two agree to within a second, and `_proof_v2_forecast` asserts the as-of is after the
        block time that carried the transaction.
        """
        now = int(time.time())
        self.forecast_at = now + FORECAST_LEAD_SECONDS
        self.forecast_miss_at = self.forecast_at + FORECAST_LEAD_SECONDS

    def _wire(self) -> None:
        """Mint, token accounts, extra-account-metas, record. The state every proof needs."""
        self._set_forecast_instants()
        self.mint = self._create_mint("main")
        self.seller_ata = dp.token_account_for(self.ctx, self.mint, self.payer, create=True)
        self.buyer = dp.buyer_pubkey(self.ctx)
        self.buyer_ata = dp.token_account_for(self.ctx, self.mint, self.buyer, create=True)

        # The toolchain's derivation is the reference; this module's is what the client will
        # use. Prove they are the same before anything is created at an address this file chose.
        self._pdas_agree_with_the_toolchain()

        self.extra_metas, init_metas = self._instruction_init_extra_metas(self.mint)
        self._transact("extraMetas", [init_metas], what="initialise extra-account-metas")

    def _proof_a(self) -> dict:
        # The mint's authority, read out of the mint account: tag 1 requires it to sign, and the
        # record stores it as the authority. Read it before the create so the assertion is about
        # what the chain says the issuer is, not about what this file assumed.
        mint_value, _mint_slot = self._account_info(self.mint)
        if not mint_value:
            raise ProofFailed(f"no mint account at {self.mint}")
        issuer = v2.mint_authority(account_data(mint_value))
        if issuer is None:
            raise ProofFailed("the mint has no authority, so no record can be created for it")
        if base58.encode(issuer) != self.payer:
            raise ProofFailed(
                f"the mint's authority is {base58.encode(issuer)}, not the payer {self.payer}: "
                "initialize_record would be refused 6026"
            )

        self.record, init_record = self._instruction_init_record(
            self.mint, face=FACE, cap_bps=CAP_BPS, band_low=BAND_LOW, policy=POLICY_CAPPED
        )
        step = self._transact("initRecord", [init_record], what="initialise record (v2)")
        record, address, slot = self._read_record(self.mint)
        if address != self.record:
            raise ProofFailed(f"the record is at {address}, not at the derived {self.record}")
        if record.authority != base58.decode(self.payer):
            raise ProofFailed(
                f"the record's authority is {base58.encode(record.authority)}, not the payer {self.payer}"
            )
        if record.held_since_unix != 0:
            raise ProofFailed(f"a fresh record carries held_since_unix {record.held_since_unix}, not 0")
        if (record.face_value_lamports, record.cap_bps, record.band_low_lamports) != (FACE, CAP_BPS, BAND_LOW):
            raise ProofFailed(f"the record decoded as {record!r}")
        if record.jurisdiction != b"ZZ" or record.policy != POLICY_CAPPED or record.status != 1:
            raise ProofFailed(f"the record decoded as {record!r}")
        self.say(
            f"  record {self.record}: face={record.face_value_lamports} cap={record.cap_bps} "
            f"band_low={record.band_low_lamports} jurisdiction={record.jurisdiction_text} "
            f"policy={record.policy} held_since={record.held_since_unix} authority={base58.encode(record.authority)}"
        )
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "record": self.record,
            "decoded": record.as_dict(),
            "readSlot": slot,
            "mintAuthority": base58.encode(issuer),
            "authorityIsPayer": True,
            "authorityIsMintAuthority": True,
            "heldSinceIsZero": True,
        }

    def _fund_tickets(self) -> None:
        dp.run(
            dp.spl(self.ctx, "mint", self.mint, str(TICKETS), self.seller_ata),
            timeout=dp.BOUND_TOKEN,
            what="spl-token mint",
        )
        self.say(f"  {TICKETS} tickets minted to {self.seller_ata}")

    def _transfer_leg(self, name: str, price: int) -> tuple[dict, dict]:
        staged = self._transact(f"stage-{name}", [self._instruction_stage(self.record, price)], what=f"stage {price}")
        attempt = self._attempt(
            name,
            [self._instruction_transfer(mint=self.mint, source=self.seller_ata, destination=self.buyer_ata)],
            what=f"transfer at {price}",
        )
        return staged, attempt

    def _proof_b(self) -> dict:
        staged, at_floor = self._transfer_leg("transferAtFloor", BAND_LOW)
        if not at_floor["ok"]:
            raise ProofFailed(f"the at-floor transfer was REFUSED: {at_floor['error']}")
        joined = "\n".join(at_floor["logs"])
        if "jurisdiction=ZZ" not in joined:
            raise ProofFailed(f"the admitted transfer's log never names the jurisdiction: {at_floor['logs']}")
        if "cap admitted" not in joined:
            raise ProofFailed(f"the admitted transfer's log is not the capped admission: {at_floor['logs']}")
        return {
            "priceLamports": BAND_LOW,
            "stagedSignature": staged["signature"],
            "signature": at_floor["signature"],
            "slot": at_floor["slot"],
            "blockTime": at_floor["blockTime"],
            "admitted": True,
            "logLines": at_floor["logs"],
            "jurisdictionInLog": True,
        }

    def _proof_f(self) -> dict:
        stepped = self.steps["transferAtFloor"]
        record, _address, slot = self._read_record(self.mint)
        if record.held_since_unix == 0:
            raise ProofFailed(
                "held_since_unix is still 0 after an admitted transfer: the clock write through "
                "Token-2022's CPI did not happen"
            )
        if record.pending_price_lamports != 0:
            raise ProofFailed(
                f"the staged price is still {record.pending_price_lamports} after an admitted "
                "transfer: one staging would admit every later transfer"
            )
        self.say(
            f"  held_since_unix={record.held_since_unix} and pending_price=0 after "
            f"{stepped['signature']} (read at slot {slot})"
        )
        return {
            "signature": stepped["signature"],
            "slot": stepped["slot"],
            "readSlot": slot,
            "heldSinceUnix": record.held_since_unix,
            "heldSinceIsZero": False,
            "pendingPriceAfterAdmission": record.pending_price_lamports,
            "stagingConsumed": True,
        }

    def _proof_c(self) -> dict:
        _staged, below = self._transfer_leg("transferBelowFloor", BAND_LOW - 1)
        if below["ok"]:
            raise ProofFailed("the below-floor transfer was ADMITTED, which is the bug this run exists to catch")
        if below["errorCode"] != 6021:
            raise ProofFailed(f"the below-floor transfer failed with {below['error']}, not 6021")
        if not any("below floor" in line for line in below["logs"]):
            raise ProofFailed(f"the refusal did not log the floor predicate: {below['logs']}")
        return {
            "priceLamports": BAND_LOW - 1,
            "bandLowLamports": BAND_LOW,
            "signature": below["signature"],
            "slot": below["slot"],
            "blockTime": below["blockTime"],
            "admitted": False,
            "error": below["error"],
            "errorCode": below["errorCode"],
            "logLines": below["logs"],
        }

    def _proof_d(self) -> dict:
        _staged, at_cap = self._transfer_leg("transferAtCap", CEILING)
        if not at_cap["ok"]:
            raise ProofFailed(f"the at-cap transfer was REFUSED: {at_cap['error']}")
        record_after, _address, slot_after = self._read_record(self.mint)
        if record_after.held_since_unix == 0:
            raise ProofFailed("the at-cap transfer did not write held_since_unix either")

        _staged_over, over_cap = self._transfer_leg("transferOverCap", OVER_CEILING)
        if over_cap["ok"]:
            raise ProofFailed("the over-cap transfer was ADMITTED, which is the bug this run exists to catch")
        if over_cap["errorCode"] != 6010:
            raise ProofFailed(f"the over-cap transfer failed with {over_cap['error']}, not 6010")
        if not any("cap exceeded" in line for line in over_cap["logs"]):
            raise ProofFailed(f"the refusal did not log the cap predicate: {over_cap['logs']}")
        return {
            "ceilingLamports": CEILING,
            "atCap": {
                "priceLamports": CEILING,
                "signature": at_cap["signature"],
                "slot": at_cap["slot"],
                "blockTime": at_cap["blockTime"],
                "admitted": True,
                "logLines": at_cap["logs"],
                "heldSinceUnix": record_after.held_since_unix,
                "readSlot": slot_after,
            },
            "overCap": {
                "priceLamports": OVER_CEILING,
                "signature": over_cap["signature"],
                "slot": over_cap["slot"],
                "blockTime": over_cap["blockTime"],
                "admitted": False,
                "error": over_cap["error"],
                "errorCode": over_cap["errorCode"],
                "logLines": over_cap["logs"],
            },
        }

    def _proof_e(self) -> dict:
        """Two refusals of `InitializeRecord`, on a second mint so no record exists yet."""
        refusal_mint = self._create_mint("refusal")
        metas_address, init_metas = self._instruction_init_extra_metas(refusal_mint)
        self._transact("refusalMintMetas", [init_metas], what="initialise extra-account-metas (refusal mint)")

        _address, by_policy = self._instruction_init_record(
            refusal_mint, face=FACE, cap_bps=CAP_BPS, band_low=0, policy=2
        )
        policy_step = self._attempt("initRecordPolicy2", [by_policy], what="initialise record with policy 2")
        if policy_step["ok"]:
            raise ProofFailed("InitializeRecord accepted policy 2")
        if policy_step["errorCode"] != 6023:
            raise ProofFailed(f"policy 2 failed with {policy_step['error']}, not 6023")

        record_address, by_band = self._instruction_init_record(
            refusal_mint, face=FACE, cap_bps=CAP_BPS, band_low=OVER_CEILING, policy=POLICY_CAPPED
        )
        band_step = self._attempt("initRecordUnsatisfiable", [by_band], what="initialise record with floor above ceiling")
        if band_step["ok"]:
            raise ProofFailed("InitializeRecord accepted a floor above the ceiling")
        if band_step["errorCode"] != 6022:
            raise ProofFailed(f"the unsatisfiable band failed with {band_step['error']}, not 6022")

        created, _slot = self._account_info(record_address, looks=4)
        if created:
            raise ProofFailed(f"a refused InitializeRecord created {record_address} anyway")
        self.say(f"  the refusal mint still has no record at {record_address}, as a refusal must leave it")
        return {
            "mint": refusal_mint,
            "extraMetas": metas_address,
            "record": record_address,
            "policy2": {
                "policy": 2,
                "signature": policy_step["signature"],
                "slot": policy_step["slot"],
                "blockTime": policy_step["blockTime"],
                "admitted": False,
                "error": policy_step["error"],
                "errorCode": policy_step["errorCode"],
                "logLines": policy_step["logs"],
            },
            "bandUnsatisfiable": {
                "bandLowLamports": OVER_CEILING,
                "ceilingLamports": CEILING,
                "signature": band_step["signature"],
                "slot": band_step["slot"],
                "blockTime": band_step["blockTime"],
                "admitted": False,
                "error": band_step["error"],
                "errorCode": band_step["errorCode"],
                "logLines": band_step["logs"],
            },
            "recordCreated": False,
        }

    def _proof_g(self) -> dict:
        """The review's exploit, re-run against the patched program: tags 2 and 3 by a stranger.

        Measured on the pre-fix program, on a copy of this artefact's ledger: the phase-1 buyer
        (not the record's authority; it holds one of the four tickets) sent `SetPendingPrice(1)`
        and the record's staged price became 1, which made every later transfer of that ticket
        admissible at 1 lamport; the same key then sent `SetStatus(0)`, which would refuse every
        later transfer of that ticket with 6013 permanently. Both landed. Both are refused 6026
        now, and the record's bytes are compared before and after each attempt so "refused" is a
        fact about the account and not only about the error code.

        The positive control is every `stage-*` step earlier in this phase: the same instruction,
        signed by the authority, is admitted. A refusal that came from a broken instruction would
        fail those and this run would not have got here.
        """
        self._fund_wallet(self.buyer, NON_AUTHORITY_FUNDING)
        before, before_slot = self._raw_account(self.record)
        ctx = self._second_phase_context()

        stage = self._attempt_with(
            ctx,
            "v2SetPendingPriceNonAuthority",
            [self._instruction_stage(self.record, 1, authority=self.buyer)],
            what="stage a price signed by a non-authority",
        )
        if stage["ok"]:
            raise ProofFailed("a non-authority staged a price: anyone can make any price admissible")
        if stage["errorCode"] != 6026:
            raise ProofFailed(f"the non-authority stage failed with {stage['error']}, not 6026")
        after_stage, after_stage_slot = self._raw_account(self.record)
        if before != after_stage:
            raise ProofFailed("the refused non-authority stage changed the record's bytes")

        status = self._attempt_with(
            ctx,
            "v2SetStatusNonAuthority",
            [self._instruction_set_status(self.record, 0, authority=self.buyer)],
            what="freeze the ticket, signed by a non-authority",
        )
        if status["ok"]:
            raise ProofFailed("a non-authority froze the ticket: SetStatus(0) would be permanent")
        if status["errorCode"] != 6026:
            raise ProofFailed(f"the non-authority status failed with {status['error']}, not 6026")
        after_status, after_status_slot = self._raw_account(self.record)
        if before != after_status:
            raise ProofFailed("the refused non-authority status changed the record's bytes")

        record = v2.decode_ticket_record(after_status)
        if record.status != 1:
            raise ProofFailed(f"the ticket is not transferable after two refusals: status {record.status}")
        self.say(
            f"  non-authority {self.buyer}: stage and SetStatus refused 6026, record bytes unchanged "
            f"({hashlib.sha256(before).hexdigest()[:16]}…)"
        )
        return {
            "nonAuthority": self.buyer,
            "authority": self.payer,
            "address": self.record,
            "readSlotBefore": before_slot,
            "stage": {
                "signature": stage["signature"],
                "slot": stage["slot"],
                "blockTime": stage["blockTime"],
                "ok": False,
                "error": stage["error"],
                "errorCode": stage["errorCode"],
            },
            "setStatus": {
                "signature": status["signature"],
                "slot": status["slot"],
                "blockTime": status["blockTime"],
                "ok": False,
                "error": status["error"],
                "errorCode": status["errorCode"],
            },
            "recordSha256Before": hashlib.sha256(before).hexdigest(),
            "recordSha256AfterStage": hashlib.sha256(after_stage).hexdigest(),
            "recordSha256AfterStatus": hashlib.sha256(after_status).hexdigest(),
            "recordUnchanged": True,
            "statusAfter": record.status,
            "readSlotAfter": after_status_slot,
            "stageReadSlot": after_stage_slot,
        }

    # -- phase two: the forecast log against a fresh ledger ------------------------
    def _phase2(self) -> dict:
        """The seven tag 4..6 proofs, on a second validator with a fresh ledger.

        The first phase's validator is stopped and a new ledger is used, so the forecast
        accounts here are created from empty and no state from the transfer proofs can be
        mistaken for this phase's. The deploy keypair is reused, so the program id and the
        `.so` are the same program the first phase proved.
        """
        self._stop()
        phase1_steps = self.steps
        self.steps = {}
        self.ledger = RUN_ROOT / f"v2-ledger-{self.pid}-phase2"
        self.keys = RUN_ROOT / f"v2-keys-{self.pid}-phase2"
        shutil.rmtree(self.ledger, ignore_errors=True)
        shutil.rmtree(self.keys, ignore_errors=True)
        self.keys.mkdir(parents=True, exist_ok=True)
        os.chmod(self.keys, 0o700)

        self._start_validator()
        self._deploy()
        self._wire()
        self._proof_a()

        proofs = {
            "band": self._proof_v2_band(),
            "forecast": self._proof_v2_forecast(),
            "forecastExists": self._proof_v2_forecast_exists(),
            "score": self._proof_v2_score(),
            "alreadyScored": self._proof_v2_already_scored(),
            "nonAuthority": self._proof_v2_non_authority(),
            "unsatisfiableBand": self._proof_v2_unsatisfiable(),
            # Added after the review: the three predicates that had no code, the one that had
            # no test of its false branch, and the two band rules that were promises only.
            "backdatedForecast": self._proof_v2_backdated_forecast(),
            "scoreBelowWidth": self._proof_v2_score_below_width(),
            "emptyBand": self._proof_v2_empty_band(),
            "asOfAhead": self._proof_v2_as_of_ahead(),
            "bandRefusedNormalised": self._proof_v2_band_refused_normalised(),
            "scoreMiss": self._proof_v2_score_miss(),
        }
        band = v2.band_address(self.program_id, self.mint)[0]
        forecast = v2.forecast_address(self.program_id, self.mint, self.forecast_at)[0]
        score = v2.score_address(self.program_id, forecast)[0]
        miss_forecast = v2.forecast_address(self.program_id, self.mint, self.forecast_miss_at)[0]
        miss_score = v2.score_address(self.program_id, miss_forecast)[0]
        phase2 = {
            "programId": self.program_id,
            "program": {
                "path": relative(SO_PATH),
                "bytes": SO_PATH.stat().st_size,
                "sha256": hashlib.sha256(SO_PATH.read_bytes()).hexdigest(),
            },
            "mint": self.mint,
            "record": self.record,
            "extraMetas": self.extra_metas,
            "band": band,
            "forecast": forecast,
            "score": score,
            "asOfUnix": self.forecast_at,
            "missAsOfUnix": self.forecast_miss_at,
            "missForecast": miss_forecast,
            "missScore": miss_score,
            "bandLowLamports": PHASE2_BAND_LOW,
            "bandHighLamports": PHASE2_BAND_HIGH,
            "realisedLamports": PHASE2_REALISED,
            "modelHash": base58.encode(PHASE2_MODEL_HASH),
            "scoringRule": forecast_score.SCORING_RULE,
            "scoringRuleHash": forecast_score.SCORING_RULE_HASH.hex(),
            "proofs": proofs,
            "steps": self.steps,
            "ledger": relative(self.ledger),
            "pdas": self._pda_crosscheck,
        }
        self.steps_v2 = self.steps
        self.steps = phase1_steps
        self.say("phase 2: seven tag 4..6 proofs on a fresh ledger")
        return phase2

    def _proof_v2_band(self) -> dict:
        as_of_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        if as_of_slot > 0:
            as_of_slot -= 1
        address, instruction = self._instruction_publish_band(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_slot=as_of_slot,
            sample_n=PHASE2_SAMPLE_N,
            refused=0,
            model_hash=PHASE2_MODEL_HASH,
        )
        step = self._transact("v2PublishBand", [instruction], what="publish band")
        band, read_slot = self._read_account(address, v2.decode_band)
        expected_authority = base58.decode(self.payer)
        if band.version != 1:
            raise ProofFailed(f"the band decoded with version {band.version}")
        if (band.low, band.high) != (PHASE2_BAND_LOW, PHASE2_BAND_HIGH):
            raise ProofFailed(f"the band decoded as {band!r}")
        if band.as_of_slot != as_of_slot or band.sample_n != PHASE2_SAMPLE_N or band.refused != 0:
            raise ProofFailed(f"the band decoded as {band!r}")
        if band.model_hash != PHASE2_MODEL_HASH or band.authority != expected_authority:
            raise ProofFailed(f"the band decoded as {band!r}")
        if band.published_slot < band.as_of_slot:
            raise ProofFailed(
                f"published_slot {band.published_slot} is below as_of_slot {band.as_of_slot}"
            )
        self.say(
            f"  band {address}: low={band.low} high={band.high} as_of_slot={band.as_of_slot} "
            f"published_slot={band.published_slot} sample_n={band.sample_n} refused={band.refused}"
        )
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": True,
            "error": None,
            "errorCode": None,
            "address": address,
            "readSlot": read_slot,
            "band": band.as_dict(),
            "asOfSlot": as_of_slot,
            "publishedSlotAtLeastAsOf": True,
        }

    def _proof_v2_forecast(self) -> dict:
        address, instruction = self._instruction_log_forecast(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_unix=self.forecast_at,
            sample_n=PHASE2_SAMPLE_N,
            model_hash=PHASE2_MODEL_HASH,
            scoring_rule_hash=forecast_score.SCORING_RULE_HASH,
        )
        step = self._transact("v2LogForecast", [instruction], what="log forecast")
        forecast, read_slot = self._read_account(address, v2.decode_forecast)
        expected_authority = base58.decode(self.payer)
        if forecast.version != 1:
            raise ProofFailed(f"the forecast decoded with version {forecast.version}")
        if forecast.mint != base58.decode(self.mint):
            raise ProofFailed(f"the forecast's mint is {base58.encode(forecast.mint)}")
        if (forecast.low, forecast.high) != (PHASE2_BAND_LOW, PHASE2_BAND_HIGH):
            raise ProofFailed(f"the forecast decoded as {forecast!r}")
        if forecast.as_of_unix != self.forecast_at or forecast.sample_n != PHASE2_SAMPLE_N:
            raise ProofFailed(f"the forecast decoded as {forecast!r}")
        if forecast.model_hash != PHASE2_MODEL_HASH:
            raise ProofFailed(f"the forecast's model hash is {base58.encode(forecast.model_hash)}")
        if forecast.scoring_rule_hash != forecast_score.SCORING_RULE_HASH:
            raise ProofFailed("the forecast did not commit the module's scoring rule hash")
        if forecast.authority != expected_authority:
            raise ProofFailed(f"the forecast's authority is {base58.encode(forecast.authority)}")
        self.say(
            f"  forecast {address}: low={forecast.low} high={forecast.high} "
            f"as_of_unix={forecast.as_of_unix} sample_n={forecast.sample_n} "
            f"rule={forecast_score.SCORING_RULE_HASH.hex()[:16]}…"
        )
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": True,
            "error": None,
            "errorCode": None,
            "address": address,
            "readSlot": read_slot,
            "forecast": forecast.as_dict(),
            "scoringRuleHash": forecast_score.SCORING_RULE_HASH.hex(),
            "createdSlot": forecast.created_slot,
        }

    def _proof_v2_forecast_exists(self) -> dict:
        forecast_address = v2.forecast_address(self.program_id, self.mint, self.forecast_at)[0]
        before, _before_slot = self._raw_account(forecast_address)
        _address, instruction = self._instruction_log_forecast(
            authority=self.payer,
            low=PHASE2_BAND_LOW + 1,
            high=PHASE2_BAND_HIGH + 1,
            as_of_unix=self.forecast_at,
            sample_n=PHASE2_SAMPLE_N + 1,
            model_hash=PHASE2_MODEL_HASH,
            scoring_rule_hash=forecast_score.SCORING_RULE_HASH,
        )
        step = self._attempt(
            "v2LogForecastAgain", [instruction], what="log a second forecast for the same as-of"
        )
        if step["ok"]:
            raise ProofFailed("a second LogForecast for the same as-of was ADMITTED")
        if step["errorCode"] != 6024:
            raise ProofFailed(f"the duplicate forecast failed with {step['error']}, not 6024")
        after, after_slot = self._raw_account(forecast_address)
        if before != after:
            raise ProofFailed("the refused duplicate changed the forecast account's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "address": forecast_address,
            "readSlot": after_slot,
            "forecastSha256Before": hashlib.sha256(before).hexdigest(),
            "forecastSha256After": hashlib.sha256(after).hexdigest(),
            "forecastUnchanged": True,
        }

    def _proof_v2_score(self) -> dict:
        forecast_address = v2.forecast_address(self.program_id, self.mint, self.forecast_at)[0]
        forecast, _slot = self._read_account(forecast_address, v2.decode_forecast)
        before, _before_slot = self._raw_account(forecast_address)
        scored = forecast_score.scored_forecast(PHASE2_REALISED, forecast)
        _forecast, score_address, instruction = self._instruction_score_forecast(
            scorer=self.payer,
            realised_lamports=scored["realised_lamports"],
            interval_score_micro=scored["interval_score_micro"],
        )
        step = self._transact("v2ScoreForecast", [instruction], what="score the forecast")
        score, read_slot = self._read_account(score_address, v2.decode_score)
        expected_authority = base58.decode(self.payer)
        if score.version != 1:
            raise ProofFailed(f"the score decoded with version {score.version}")
        if score.realised_lamports != PHASE2_REALISED:
            raise ProofFailed(f"the score decoded as {score!r}")
        if score.interval_score_micro != scored["interval_score_micro"]:
            raise ProofFailed(
                f"the score stored {score.interval_score_micro}, expected "
                f"{scored['interval_score_micro']}"
            )
        if score.covered != (1 if scored["covered"] else 0):
            raise ProofFailed(f"the score's covered flag is {score.covered}")
        if score.scorer != expected_authority:
            raise ProofFailed(f"the score's scorer is {base58.encode(score.scorer)}")
        after, after_slot = self._raw_account(forecast_address)
        if before != after:
            raise ProofFailed(
                "ScoreForecast changed the forecast account: it must be read-only in the instruction"
            )
        self.say(
            f"  score {score_address}: realised={score.realised_lamports} "
            f"interval_score_micro={score.interval_score_micro} covered={score.covered}"
        )
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": True,
            "error": None,
            "errorCode": None,
            "address": score_address,
            "forecastAddress": forecast_address,
            "readSlot": read_slot,
            "score": score.as_dict(),
            "expectedIntervalScoreMicro": scored["interval_score_micro"],
            "expectedCovered": bool(scored["covered"]),
            "forecastSha256Before": hashlib.sha256(before).hexdigest(),
            "forecastSha256After": hashlib.sha256(after).hexdigest(),
            "forecastUnchanged": True,
        }

    def _proof_v2_already_scored(self) -> dict:
        forecast_address = v2.forecast_address(self.program_id, self.mint, self.forecast_at)[0]
        score_address = v2.score_address(self.program_id, forecast_address)[0]
        before, _before_slot = self._raw_account(score_address)
        _forecast, _score, instruction = self._instruction_score_forecast(
            scorer=self.payer,
            realised_lamports=PHASE2_REALISED + 1,
            interval_score_micro=1,
        )
        step = self._attempt(
            "v2ScoreForecastAgain", [instruction], what="score the same forecast twice"
        )
        if step["ok"]:
            raise ProofFailed("a second ScoreForecast was ADMITTED")
        if step["errorCode"] != 6025:
            raise ProofFailed(f"the second score failed with {step['error']}, not 6025")
        after, after_slot = self._raw_account(score_address)
        if before != after:
            raise ProofFailed("the refused second score changed the score account's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "address": score_address,
            "readSlot": after_slot,
            "scoreSha256Before": hashlib.sha256(before).hexdigest(),
            "scoreSha256After": hashlib.sha256(after).hexdigest(),
            "scoreUnchanged": True,
        }

    def _proof_v2_non_authority(self) -> dict:
        self._fund_wallet(self.buyer, NON_AUTHORITY_FUNDING)
        band_address = v2.band_address(self.program_id, self.mint)[0]
        before, _before_slot = self._raw_account(band_address)
        as_of_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        _address, instruction = self._instruction_publish_band(
            authority=self.buyer,
            low=PHASE2_BAND_LOW + 1,
            high=PHASE2_BAND_HIGH + 1,
            as_of_slot=as_of_slot,
            sample_n=PHASE2_SAMPLE_N + 1,
            refused=0,
            model_hash=PHASE2_MODEL_HASH,
        )
        ctx = self._second_phase_context()
        step = self._attempt_with(
            ctx,
            "v2PublishBandNonAuthority",
            [instruction],
            what="publish a band signed by a non-authority",
        )
        if step["ok"]:
            raise ProofFailed("a band published by a non-authority was ADMITTED")
        if step["errorCode"] != 6026:
            raise ProofFailed(f"the non-authority publish failed with {step['error']}, not 6026")
        after, after_slot = self._raw_account(band_address)
        if before != after:
            raise ProofFailed("the refused non-authority publish changed the band's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "nonAuthority": self.buyer,
            "authority": self.payer,
            "address": band_address,
            "readSlot": after_slot,
            "bandSha256Before": hashlib.sha256(before).hexdigest(),
            "bandSha256After": hashlib.sha256(after).hexdigest(),
            "bandUnchanged": True,
        }

    def _proof_v2_unsatisfiable(self) -> dict:
        band_address = v2.band_address(self.program_id, self.mint)[0]
        before, _before_slot = self._raw_account(band_address)
        as_of_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        _address, instruction = self._instruction_publish_band(
            authority=self.payer,
            low=PHASE2_BAND_HIGH + 1,
            high=PHASE2_BAND_LOW,
            as_of_slot=as_of_slot,
            sample_n=PHASE2_SAMPLE_N,
            refused=0,
            model_hash=PHASE2_MODEL_HASH,
        )
        step = self._attempt(
            "v2PublishBandUnsatisfiable", [instruction], what="publish a band with low above high"
        )
        if step["ok"]:
            raise ProofFailed("a band with low > high was ADMITTED")
        if step["errorCode"] != 6022:
            raise ProofFailed(f"the inverted band failed with {step['error']}, not 6022")
        after, after_slot = self._raw_account(band_address)
        if before != after:
            raise ProofFailed("the refused inverted band changed the band's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "low": PHASE2_BAND_HIGH + 1,
            "high": PHASE2_BAND_LOW,
            "address": band_address,
            "readSlot": after_slot,
            "bandSha256Before": hashlib.sha256(before).hexdigest(),
            "bandSha256After": hashlib.sha256(after).hexdigest(),
            "bandUnchanged": True,
        }

    # -- the review's refusals, phase two -------------------------------------------
    #
    # Each of these was a predicate the review found missing, a band rule that was a promise in a
    # comment rather than a check, or a branch no artefact had ever produced. They are here so
    # the refusal has a signature a sceptic can look up, not only a unit test they have to trust.

    def _proof_v2_empty_band(self) -> dict:
        """6032: `sample_n = 0` with `refused = 0` is a band with nothing behind it."""
        address = v2.band_address(self.program_id, self.mint)[0]
        before, _before_slot = self._raw_account(address)
        as_of_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        _address, instruction = self._instruction_publish_band(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_slot=as_of_slot,
            sample_n=0,
            refused=0,
            model_hash=PHASE2_MODEL_HASH,
        )
        step = self._attempt("v2PublishBandEmpty", [instruction], what="publish a band with no observations")
        if step["ok"]:
            raise ProofFailed("a band with sample_n = 0 and refused = 0 was ADMITTED")
        if step["errorCode"] != 6032:
            raise ProofFailed(f"the empty band failed with {step['error']}, not 6032")
        after, after_slot = self._raw_account(address)
        if before != after:
            raise ProofFailed("the refused empty band changed the band's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "sampleN": 0,
            "refused": 0,
            "address": address,
            "readSlot": after_slot,
            "bandSha256Before": hashlib.sha256(before).hexdigest(),
            "bandSha256After": hashlib.sha256(after).hexdigest(),
            "bandUnchanged": True,
        }

    def _proof_v2_as_of_ahead(self) -> dict:
        """6033: an `as_of_slot` above the slot the write lands in is a claim from the future."""
        address = v2.band_address(self.program_id, self.mint)[0]
        before, _before_slot = self._raw_account(address)
        published_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        as_of_slot = published_slot + 1000
        _address, instruction = self._instruction_publish_band(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_slot=as_of_slot,
            sample_n=PHASE2_SAMPLE_N,
            refused=0,
            model_hash=PHASE2_MODEL_HASH,
        )
        step = self._attempt("v2PublishBandAsOfAhead", [instruction], what="publish a band as of the future")
        if step["ok"]:
            raise ProofFailed("a band with as_of_slot above the published slot was ADMITTED")
        if step["errorCode"] != 6033:
            raise ProofFailed(f"the future as-of failed with {step['error']}, not 6033")
        after, after_slot = self._raw_account(address)
        if before != after:
            raise ProofFailed("the refused future as-of changed the band's bytes")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "asOfSlot": as_of_slot,
            "publishedSlotBefore": published_slot,
            "address": address,
            "readSlot": after_slot,
            "bandSha256Before": hashlib.sha256(before).hexdigest(),
            "bandSha256After": hashlib.sha256(after).hexdigest(),
            "bandUnchanged": True,
        }

    def _proof_v2_band_refused_normalised(self) -> dict:
        """`refused` is a flag: a write of 7 stores and logs 1, not 7."""
        address = v2.band_address(self.program_id, self.mint)[0]
        as_of_slot = int(dp.rpc(self.rpc, "getSlot", [{"commitment": "confirmed"}]))
        _address, instruction = self._instruction_publish_band(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_slot=as_of_slot,
            sample_n=PHASE2_SAMPLE_N,
            refused=7,
            model_hash=PHASE2_MODEL_HASH,
        )
        step = self._transact("v2PublishBandRefusedNormalised", [instruction], what="publish a band with refused = 7")
        band, read_slot = self._read_account(address, v2.decode_band)
        if band.refused != 1:
            raise ProofFailed(f"refused = 7 was stored as {band.refused}, not 1")
        if not any("refused=1" in line for line in step["logs"]):
            raise ProofFailed(f"the log line does not report the normalised flag: {step['logs']}")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": True,
            "error": None,
            "errorCode": None,
            "sentRefused": 7,
            "storedRefused": band.refused,
            "address": address,
            "readSlot": read_slot,
            "band": band.as_dict(),
            "refusedNormalised": True,
            "headRewritten": True,
        }

    def _proof_v2_backdated_forecast(self) -> dict:
        """6029: a forecast dated a year ago can be told from a post-hoc claim only by the clock.

        This is the defect the review measured in the previous artefact: its forecast had
        as_of_unix 1760000000 and was created at blockTime 1794120524, 394.9 days later. The
        refusal leaves the PDA empty, so nothing can be scored against a backdated band.
        """
        as_of_unix = int(time.time()) - BACKDATED_BY_SECONDS
        address, instruction = self._instruction_log_forecast(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_unix=as_of_unix,
            sample_n=PHASE2_SAMPLE_N,
            model_hash=PHASE2_MODEL_HASH,
            scoring_rule_hash=forecast_score.SCORING_RULE_HASH,
        )
        step = self._attempt("v2LogForecastBackdated", [instruction], what="log a forecast dated a year ago")
        if step["ok"]:
            raise ProofFailed("a backdated forecast was ADMITTED")
        if step["errorCode"] != 6029:
            raise ProofFailed(f"the backdated forecast failed with {step['error']}, not 6029")
        created, _slot = self._account_info(address, looks=4)
        if created:
            raise ProofFailed(f"a refused backdated log created {address} anyway")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "asOfUnix": as_of_unix,
            "backdatedBySeconds": BACKDATED_BY_SECONDS,
            "address": address,
            "forecastCreated": False,
        }

    def _proof_v2_score_below_width(self) -> dict:
        """6030: a score below the band's width is not a score under any reading of the rule.

        The band for this instant is logged first, because the check reads the forecast. The
        forecast is left unscored by this refusal: the next proof scores it honestly as a miss.
        """
        forecast_address, instruction = self._instruction_log_forecast(
            authority=self.payer,
            low=PHASE2_BAND_LOW,
            high=PHASE2_BAND_HIGH,
            as_of_unix=self.forecast_miss_at,
            sample_n=PHASE2_SAMPLE_N,
            model_hash=PHASE2_MODEL_HASH,
            scoring_rule_hash=forecast_score.SCORING_RULE_HASH,
        )
        logged = self._transact("v2LogForecastMiss", [instruction], what="log the forecast the miss will score")
        width_micro = (PHASE2_BAND_HIGH - PHASE2_BAND_LOW) * 1_000_000
        _forecast, score_address, score_instruction = self._instruction_score_forecast(
            scorer=self.payer,
            realised_lamports=PHASE2_REALISED,
            interval_score_micro=width_micro - 1,
            as_of=self.forecast_miss_at,
        )
        step = self._attempt("v2ScoreBelowWidth", [score_instruction], what="score below the band's width")
        if step["ok"]:
            raise ProofFailed("a score below the band's width was ADMITTED")
        if step["errorCode"] != 6030:
            raise ProofFailed(f"the understated score failed with {step['error']}, not 6030")
        created, _slot = self._account_info(score_address, looks=4)
        if created:
            raise ProofFailed(f"a refused score created {score_address} anyway")
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": False,
            "error": step["error"],
            "errorCode": step["errorCode"],
            "forecastSignature": logged["signature"],
            "forecast": forecast_address,
            "address": score_address,
            "widthMicro": width_micro,
            "underscoredBy": width_micro - 1,
            "scoreCreated": False,
        }

    def _proof_v2_score_miss(self) -> dict:
        """The branch no artefact had: a realised price outside the band, stored as covered = 0."""
        forecast_address = v2.forecast_address(self.program_id, self.mint, self.forecast_miss_at)[0]
        realised = PHASE2_BAND_HIGH + 1
        scored = forecast_score.scored_forecast(
            realised, {"low": PHASE2_BAND_LOW, "high": PHASE2_BAND_HIGH}
        )
        if scored["covered"]:
            raise ProofFailed("the test's premise: one lamport above the band must not be covered")
        _forecast, score_address, instruction = self._instruction_score_forecast(
            scorer=self.payer,
            realised_lamports=scored["realised_lamports"],
            interval_score_micro=scored["interval_score_micro"],
            as_of=self.forecast_miss_at,
        )
        step = self._transact("v2ScoreMiss", [instruction], what="score a realised price outside the band")
        score, read_slot = self._read_account(score_address, v2.decode_score)
        if score.covered != 0:
            raise ProofFailed(f"a miss was stored with covered = {score.covered}")
        if score.realised_lamports != realised:
            raise ProofFailed(f"the score decoded as {score!r}")
        if score.interval_score_micro != scored["interval_score_micro"]:
            raise ProofFailed(
                f"the score stored {score.interval_score_micro}, expected "
                f"{scored['interval_score_micro']}"
            )
        self.say(
            f"  miss score {score_address}: realised={score.realised_lamports} "
            f"interval_score_micro={score.interval_score_micro} covered={score.covered}"
        )
        return {
            "signature": step["signature"],
            "slot": step["slot"],
            "blockTime": step["blockTime"],
            "ok": True,
            "error": None,
            "errorCode": None,
            "forecastAddress": forecast_address,
            "address": score_address,
            "readSlot": read_slot,
            "score": score.as_dict(),
            "realisedOutsideBand": True,
            "expectedIntervalScoreMicro": scored["interval_score_micro"],
            "covered": False,
        }

    # -- the artefact ---------------------------------------------------------------

    def _artefact(self, proofs: dict, *, phase1: dict, phase2: dict) -> dict:
        so_bytes = SO_PATH.read_bytes()
        artefact = {
            "version": 2,
            "checkerVersion": CHECKER_VERSION,
            "cluster": "localnet",
            "localOnly": True,
            "writtenAt": iso(),
            "startedAt": iso(self.started),
            "elapsedSeconds": round((now() - self.started).total_seconds(), 1),
            "programId": self.program_id,
            "program": {
                "path": relative(SO_PATH),
                "bytes": len(so_bytes),
                "sha256": hashlib.sha256(so_bytes).hexdigest(),
            },
            "payer": self.payer,
            "mint": phase1["mint"],
            "record": phase1["record"],
            "extraMetas": phase1["extraMetas"],
            "seller": phase1["seller"],
            "buyer": phase1["buyer"],
            "buyerAta": phase1["buyerAta"],
            "arguments": {
                "faceLamports": FACE,
                "capBps": CAP_BPS,
                "bandLowLamports": BAND_LOW,
                "jurisdiction": JURISDICTION,
                "policy": POLICY_CAPPED,
                "ceilingLamports": CEILING,
            },
            "recordAtEnd": phase1["recordAtEnd"],
            "recordAtEndSlot": phase1["recordAtEndSlot"],
            "proofs": proofs,
            "proofs_v2": phase2["proofs"],
            "steps": phase1["steps"],
            "steps_v2": phase2["steps"],
            "pdas": phase1["pdas"],
            "phase2": {
                key: value
                for key, value in phase2.items()
                if key not in ("proofs", "steps")
            },
            "validator": {
                "ledger": phase1["ledger"],
                "genesisFunding": "the payer, via --mint at genesis; no faucet, no airdrop",
                # Both ids are resolved, not typed: the third copy of the devnet memo id in
                # this tree was a literal here that nothing read, and it would have kept
                # agreeing with a table that had gone stale.
                "clones": [
                    f"{dp.TOKEN_2022_PROGRAM} (Token-2022)",
                    f"{dp.chain_client.memo_program_id('devnet')} (devnet memo program)",
                ],
                "note": "the validator is killed on every exit path; the ledger is kept so the signatures can be re-read",
            },
            "phase2Validator": {
                "ledger": phase2["ledger"],
                "note": "a second validator and a fresh ledger for the tag 4..6 proofs; same program id and .so",
            },
        }
        ARTEFACT.parent.mkdir(parents=True, exist_ok=True)
        ARTEFACT.write_text(json.dumps(artefact, indent=2, sort_keys=False) + "\n", encoding="utf-8")
        ARTEFACT.chmod(0o644)
        return artefact


def publish(*, say=print) -> dict:
    """Run the whole sequence against a local validator and return (and write) the artefact."""
    return LocalProof(say=say).run()


def summary(artefact: dict) -> list[str]:
    identity = f"program {artefact['programId']} on {artefact['cluster']}"
    lines = [
        identity,
        f"artefact: {relative(ARTEFACT)}",
        f"so: {artefact['program']['sha256']} ({artefact['program']['bytes']} bytes)",
        f"mint {artefact['mint']}, record {artefact['record']}",
    ]
    proofs = artefact["proofs"]
    signatures = {
        "a": (proofs["a"], "InitializeRecord by the mint authority, authority and held_since"),
        "b": (proofs["b"], "at band_low admitted, jurisdiction logged"),
        "c": (proofs["c"], "band_low - 1 refused 6021"),
        "d": (proofs["d"]["atCap"], "at cap admitted"),
        "d'": (proofs["d"]["overCap"], "cap + 1 refused 6010"),
        "e": (proofs["e"]["policy2"], "policy 2 refused 6023"),
        "e'": (proofs["e"]["bandUnsatisfiable"], "floor above ceiling refused 6022"),
        "f": (proofs["f"], "held_since_unix written, staged price consumed"),
        "g": (proofs["g"]["stage"], "non-authority stage refused 6026"),
        "g'": (proofs["g"]["setStatus"], "non-authority SetStatus refused 6026"),
    }
    for key, (block, label) in signatures.items():
        lines.append(f"  ({key}) {label}: {block['signature']} (slot {block['slot']})")

    phase2 = artefact.get("proofs_v2") or {}
    if phase2:
        v2_lines = {
            "4": (phase2["band"], "PublishBand, read back"),
            "4'": (phase2["nonAuthority"], "band from a non-authority refused 6026"),
            "4''": (phase2["unsatisfiableBand"], "band with low > high refused 6022"),
            "4'''": (phase2["emptyBand"], "band with no observations refused 6032"),
            "4''''": (phase2["asOfAhead"], "band as of the future refused 6033"),
            "4v": (phase2["bandRefusedNormalised"], "refused = 7 stored and logged as 1"),
            "5": (phase2["forecast"], "LogForecast, forward-dated"),
            "5'": (phase2["forecastExists"], "same as-of refused 6024"),
            "5''": (phase2["backdatedForecast"], "as-of a year ago refused 6029"),
            "6": (phase2["score"], "ScoreForecast, forecast bytes unchanged"),
            "6'": (phase2["alreadyScored"], "same forecast scored twice refused 6025"),
            "6''": (phase2["scoreBelowWidth"], "score below the band width refused 6030"),
            "6'''": (phase2["scoreMiss"], "a miss scored, covered = 0"),
        }
        for key, (block, label) in v2_lines.items():
            lines.append(f"  ({key}) {label}: {block['signature']} (slot {block['slot']})")
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="tools/publish_v2.py",
        description="Deploy cap_hook v2 under a new keypair to a local validator and prove the boundary.",
        epilog="Local only: starts its own solana-test-validator and kills it. Writes records/onchain-v2.local.json.",
    )
    parser.add_argument("--quiet", action="store_true", help="print the summary only")
    args = parser.parse_args(argv)
    say = (lambda line: None) if args.quiet else print
    try:
        artefact = publish(say=say)
    except (ProofFailed, dp.PublishError) as exc:
        sys.stderr.write(f"\nFAILED: {exc}\n")
        return 1
    except KeyboardInterrupt:
        sys.stderr.write("\ninterrupted\n")
        return 130
    for line in summary(artefact):
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

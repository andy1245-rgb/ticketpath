#!/usr/bin/env python3
"""Put the cap check on a cluster and record what is publicly there.

    python3 tools/devnet_publish.py --dry-run     # what it would do, no writes, no signing
    python3 tools/devnet_publish.py --local       # rehearse the whole thing on a local validator
    python3 tools/devnet_publish.py               # devnet, once the authority is funded

It is idempotent, and that is now enforced rather than hoped for. Every step reads the
cluster first and skips what is already true, every step writes what it finished to a local
resume file (`records/devnet-progress.json`, git-ignored) *immediately*, and every RPC call
that fails in transit is retried with a bounded backoff. A run that dies halfway is resumed
by running it again: same mint, same token accounts, same signatures, none of them repeated.

The resume file exists because of one concrete failure. A devnet run deployed the program and
minted a mint, then died on `getSignatureStatuses: ... did not answer (HTTPError)`, and the
mint address lived only in that process's memory, so the rerun minted a second mint. Two
things prevent a repeat, and they are not the same thing:

  * the mint keypair is generated here and its address is written down **before** the
transaction that creates it, so a rerun creates that address or finds it, never another one;
  * a transaction's signature is written down the moment `sendTransaction` returns it, so a
rerun can ask the cluster whether it landed instead of resending it. A resend of a transfer
moves a second ticket, so "not visible" is not treated as "did not happen": the run waits
until the transaction's blockhash is dead before it will send again, and otherwise stops and
says so.

Every command is bounded and every validator it starts is killed on every exit path
(`atexit`, SIGINT, SIGTERM and the normal return).

What it does, in order, and what it refuses:

1. **Balance.** Below `MIN_BALANCE_LAMPORTS` it stops and prints the faucet instruction. The
   devnet RPC faucet is closed (`410`), so `solana airdrop` cannot work and retrying it is
   wasted time; funding needs the operator's GitHub session at https://faucet.solana.com.
2. **Build.** `cargo build-sbf` in `programs/cap_hook`, which produces the `.so`.
3. **Deploy.** `solana program deploy`, skipped when the program account is already executable,
   and refused outright, in the plan as well, when the `.so` is the v2 build and the target is the
   frozen devnet program: that deploy is an upgrade of the one program this repository has proved,
   under the keypair that still owns it, and nothing turns the refusal off.
4. **Mint.** A Token-2022 mint, 0 decimals, with `TransferHook` pointing at the program and
   `MetadataPointer` pointing at itself, then `initialize-metadata`. One base unit is one
   ticket, which is what the hook's `amount == 1` check means.
5. **Wire.** The `["extra-account-metas", mint]` PDA and the `["record", mint]` PDA, both
   created by the program itself.
6. **One ticket**, minted to the authority's token account.
7. **The memo.** The console's own quote for `evt_syn_02` in `counterfactual` mode, pinned at
   `AS_OF`, hashed by `ticketpath.adapters.chain_client.quote_hash` and sent as
   `ticketpath:quote:<quoteId>:<hash>` -- the grammar `ticketpath/console` and
   `ticketpath/adapters/chain_client.py` already verify against, so the `[DEVNET]` slot
   recomputes. The previous run used a `ticketpath:v1:` memo, which cannot pass that check;
   the operator settled on this one.
8. **The boundary, as a pair.** A transfer priced exactly at the cap and one priced one lamport
   over it. The second is sent with the preflight check skipped so it lands as a failed
   transaction with its own signature and its own error, which is the only form of refusal a
   sceptic can check. One side alone proves nothing.
9. **The artefact.** `records/devnet-artefacts.json`, public data only: cluster, program id,
   mint, signatures, slots, block times, explorer URLs. Never a key, never a path, never the
   inside of the keypair.

Where the keypair goes, and where it does not: this file never opens it. `solana` and
`spl-token` read it themselves when they are told `--keypair <path>`, and the three
instructions that only this project's program understands are signed by
`tools/solana_sign.py`, a separate process that prints one signature and nothing else. There
is no code path here that can print, log or traceback a byte of key material. The resume file
follows the same rule: it holds public identifiers, integers and signatures, and
`Progress.save` refuses to write a path, a key handle or a port into it.

Two flags exist for the rehearsal and for nothing else. `--restart` forgets the resume file
(the cluster is never touched). `--inject after:<step>` / `--inject rpc:<method>:<count>`
makes a run die on purpose, which is how the resume path is tested rather than assumed; a
fault that can fire by accident would be a bug in the thing this file exists to prove, so it
is armed by an explicit flag and by nothing in the environment.

Standard library only, plus this repository's own `ticketpath` package (which is itself
standard library only).
"""

from __future__ import annotations

import argparse
import atexit
import base64
import hashlib
import http.client
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from urllib import error as urlerror
from urllib import request as urlrequest

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from ticketpath.adapters import chain_client  # noqa: E402
from ticketpath.core import base58  # noqa: E402

# -- what the run is ---------------------------------------------------------

PROGRAM_DIR = REPO_ROOT / "programs" / "cap_hook"
SO_PATH = PROGRAM_DIR / "target" / "deploy" / "cap_hook.so"
PROGRAM_KEYPAIR = PROGRAM_DIR / "target" / "deploy" / "cap_hook-keypair.json"

# The one program this repository has proved anything on: the v1 build, deployed to devnet on
# 2026-11-07 and recorded in `records/devnet-artefacts.json`. `PROGRAM_KEYPAIR` above still
# unlocks it, and `cargo-build-sbf` writes the v2 build over the same `SO_PATH` this file
# deploys, so the two together are an upgrade waiting for one command. That is what
# `refuse_frozen_devnet_upgrade` is for.
FROZEN_DEVNET_PROGRAM = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva"

# Log strings only the v2 build carries: the floor refusal, the policy branch, and the
# held-time write. No v1 build logs any of them, so a program binary that does is v2, and the
# bytes decide it rather than a filename, a flag or a build timestamp.
V2_ONLY_LOG_STRINGS = ("below floor", "policy=monitored", "held_since_unix")

DEVNET_ARTEFACT = REPO_ROOT / "records" / "devnet-artefacts.json"
LOCAL_ARTEFACT = REPO_ROOT / "records" / "devnet-artefacts.local.json"
# The resume file. Local, git-ignored and never evidence: it is what a run in flight has
# already done, so the next run continues instead of starting a second mint.
DEVNET_PROGRESS = REPO_ROOT / "records" / "devnet-progress.json"
LOCAL_PROGRESS = REPO_ROOT / "records" / "devnet-progress.local.json"

CLUSTER_URLS = {"devnet": "https://api.devnet.solana.com"}
FAUCET_URL = "https://faucet.solana.com"
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ASSOCIATED_TOKEN_PROGRAM = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
SYSTEM_PROGRAM = "11111111111111111111111111111111"
# There is no memo program constant here on purpose. The id is per cluster and the clusters
# disagree, so this file asks `chain_client.memo_program_id` for the run's own cluster; the
# one place it names a cluster explicitly is the local validator's `--clone`, which pulls from
# `--url <devnet>` and so names devnet's.

# Two SOL: the deploy rent for an 85,784-byte program is about 0.6 SOL and the buffer account
# holds a second copy until the deploy succeeds, so 1.4 SOL is the floor and 2 is the round
# number the previous run measured against. Signatures are 5000 lamports each.
MIN_BALANCE_LAMPORTS = 2_000_000_000

# The design's own worked pair (§3.10): face 1.0 SOL, cap 2500 bps, so the maximum admissible
# price is exactly 1.25 SOL and one lamport over it is refused.
FACE_LAMPORTS = 1_000_000_000
CAP_BPS = 2500
ACCEPTED_PRICE_LAMPORTS = FACE_LAMPORTS + (FACE_LAMPORTS * CAP_BPS) // 10_000
REFUSED_PRICE_LAMPORTS = ACCEPTED_PRICE_LAMPORTS + 1
TICKETS_NEEDED = 2

# The quote the console renders and verifies. Pinned so the hash reproduces byte for byte.
EVENT_ID = "evt_syn_02"
TIER_ID = "tier_stg_general"
AS_OF = "2026-11-07T18:34:29.183Z"

CHECKER_VERSION = "devnet-publish-2026-11-07"
TICKET_NAME = "Ticketpath Synthetic Ticket"
TICKET_SYMBOL = "TKT"
# .invalid is reserved (RFC 2606) and can never resolve: a placeholder that reads as one.
TICKET_URI = "https://example.invalid/ticketpath/evt_syn_02"

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_REFUSED = 2

BOUND_BUILD = 1800.0
BOUND_DEPLOY = 900.0
BOUND_TOKEN = 180.0
BOUND_RPC = 30.0
BOUND_CONFIRM = 180.0
BOUND_VALIDATOR_START = 120.0

# A transient RPC failure is worth retrying: every call this file makes is either a read or
# the resend of bytes that never landed. Four attempts over about 3.5s of backoff, then one
# sentence. Nothing here retries a rejected transaction or a wrong request.
RPC_ATTEMPTS = 4
RPC_BACKOFF_BASE = 0.5
RPC_BACKOFF_CAP = 8.0
TRANSIENT_HTTP_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})
TRANSIENT_RPC_MESSAGE = re.compile(
    r"(?i)(node is behind|blockhash not found|block not available|service unavailable|"
    r"too many requests|rate.?limit|timed? ?out|try again|connection)"
)

# Ports this machine already uses for something else. A validator this script starts must
# never land on one of them, and never on a port a browser would guess.
RESERVED_PORTS = {3000, 3001, 8787, 8788}


class PublishError(RuntimeError):
    """A step failed. The message is short, printable and carries no key material."""


class Refused(PublishError):
    """The run cannot proceed until the operator does something (funding, mostly)."""


class InjectedFault(PublishError):
    """A rehearsal fault (`--inject`), so a log reads as deliberate rather than as a bug."""


class _Transient(Exception):
    """One failed attempt, of a kind worth repeating. Never escapes `rpc`."""

    def __init__(self, detail: str):
        super().__init__(detail)
        self.detail = detail


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.") + f"{datetime.now(timezone.utc).microsecond // 1000:03d}Z"


# -- running commands, bounded ----------------------------------------------


def toolchain_path() -> str:
    """PATH, with the two install locations this machine uses appended if they are missing."""
    path = os.environ.get("PATH", "")
    hints = [Path.home() / ".cargo" / "bin", Path.home() / ".local" / "share" / "solana" / "install" / "active_release" / "bin"]
    for hint in hints:
        if hint.is_dir() and str(hint) not in path.split(os.pathsep):
            path = f"{path}{os.pathsep}{hint}" if path else str(hint)
    return path


def which(binary: str) -> str | None:
    return shutil.which(binary, path=toolchain_path())


def run(command: list[str], *, timeout: float, what: str, check: bool = True, cwd: Path | None = None) -> str:
    """One bounded child. On failure the message carries the child's own tail, nothing else."""
    env = dict(os.environ)
    env["PATH"] = toolchain_path()
    try:
        completed = subprocess.run(
            command, cwd=str(cwd or REPO_ROOT), env=env, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError as exc:
        raise PublishError(f"{what}: {command[0]} is not on PATH") from exc
    except subprocess.TimeoutExpired as exc:
        raise PublishError(f"{what}: exceeded its {timeout:g}s bound and was killed") from exc
    output = (completed.stdout or "") + (completed.stderr or "")
    if check and completed.returncode != 0:
        tail = "\n".join(line for line in output.splitlines()[-12:] if line.strip())
        raise PublishError(f"{what} failed (rc {completed.returncode}):\n{tail}")
    return output


def last_base58(output: str) -> str | None:
    """The last signature-shaped token a CLI printed. Signatures are 64 bytes of base58."""
    for token in reversed(re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{64,90}\b", output)):
        try:
            if len(base58.decode(token)) == 64:
                return token
        except Exception:  # noqa: BLE001 - not base58, keep looking
            continue
    return None


#: What a CLI says when it looked for an account the cluster had not shown it yet.
CLI_NOT_FOUND = re.compile(r"(?i)(not found|could not find|accountnotfound)")


def settled(call, *, what: str, attempts: int = 3, log=None) -> str:
    """Call a CLI helper, and retry while the failure is a "not visible yet".

    Measured on this machine: the RPC this process uses can see an account a full second before
    `spl-token` does, and the CLI that loses that race says "not found" rather than answering
    wrong. That window is a "not yet", so it is retried; anything else is a real failure and is
    raised as one. The distinction matters because a zero balance decides how many tickets to
    mint, and a minted ticket cannot be taken back.
    """
    for attempt in range(attempts):
        try:
            return call()
        except PublishError as exc:
            if attempt + 1 >= attempts or not CLI_NOT_FOUND.search(str(exc)):
                raise
            if log is not None:
                log(f"  {what}: the account is not visible to the CLI yet; looking again")
            time.sleep(1.5)
    raise AssertionError("unreachable")


# -- a rehearsal fault hook, armed only by an explicit flag --------------------


@dataclass
class Faults:
    """Make one run die at a chosen point, so the resume can be tested rather than assumed.

    Two shapes, and nothing else:

        --inject after:mint                  stop once the mint exists, metadata not yet done
        --inject rpc:getSignatureStatuses:2  the next two status reads fail as HTTP 502

    Armed by the `--inject` flag only. Nothing here reads the environment, because a fault
    that can fire in a real run is worse than no fault injection at all. The point names are
    raised by the call sites themselves, so a step that forgets one shows up as a test that
    did not fail.
    """

    after: set = field(default_factory=set)
    rpc: dict = field(default_factory=dict)

    def arm(self, specs: list[str]) -> None:
        for spec in specs or []:
            kind, _, rest = spec.partition(":")
            if kind == "after" and rest:
                self.after.add(rest)
            elif kind == "rpc" and rest.count(":") == 1:
                method, _, count = rest.partition(":")
                if not count.isdigit() or int(count) < 1:
                    raise ValueError(f"--inject {spec!r}: the count must be a positive number")
                self.rpc[method] = int(count)
            else:
                raise ValueError(f"--inject {spec!r}: expected after:<step> or rpc:<method>:<count>")

    def after_step(self, point: str) -> None:
        if point in self.after:
            self.after.discard(point)
            raise InjectedFault(
                f"injected fault after {point}: the run stops here on purpose, so the resume path can be tested"
            )

    def before_rpc(self, method: str) -> None:
        remaining = self.rpc.get(method, 0)
        if remaining <= 0:
            return
        self.rpc[method] = remaining - 1
        # An HTTP 502 is the shape the terminal run actually died on, so the retry sees the
        # same class of failure it is meant to survive.
        raise urlerror.HTTPError(
            "https://injected.invalid", 502, f"injected transport failure for {method} ({remaining - 1} left)", None, None
        )


FAULTS = Faults()


# -- the resume file: what this run has already done --------------------------

PROGRESS_VERSION = 1

# Everything the resume file may hold. Public identifiers, integers and signatures only: the
# mint, the token accounts, the two PDAs, the balances the boundary pair started from, and one
# signature per finished step. No path, no key, no port -- `_assert_local_state` refuses them,
# so this file is safe to read even though it is git-ignored and never published.
PROGRESS_FIELDS = (
    "version",
    "cluster",
    "checkerVersion",
    "programId",
    "mint",
    "mintMetadata",
    "buyer",
    "authorityAta",
    "buyerAta",
    "record",
    "extraMetas",
    "ticketsMinted",
    "memo",
    "transfers",
    "pending",
    "balancesBefore",
    "balancesAfter",
    "completedAt",
)


def _assert_local_state(state: dict) -> None:
    """No path, no key handle, no list, no field the loader does not know.

    The same discipline as `_assert_public` for the artefact, applied to a file that is not
    published: a rule that only holds for the file you meant to protect is not a rule.
    """

    extra = set(state) - set(PROGRESS_FIELDS)
    if extra:
        raise PublishError(f"the resume file would carry fields it should not: {sorted(extra)}")

    def walk(value: object, where: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{where}.{key}")
        elif isinstance(value, (list, tuple, set)):
            raise PublishError(f"the resume file would carry a list in {where}")
        elif isinstance(value, str):
            if value.startswith("/") or value.startswith("~"):
                raise PublishError(f"the resume file would carry an absolute path in {where}")
            if "keypair" in value.lower():
                raise PublishError(f"the resume file would carry a key handle in {where}")

    for name, item in state.items():
        walk(item, name)


class Progress:
    """What a run has already done, on disk, written immediately after each step.

    Loaded at the start, written with `os.replace` so a crash leaves either the old file or the
    new one and never half of one, and read back by the next run to skip the steps it describes.
    A dry run reads it and never writes it.
    """

    def __init__(self, path: Path, *, cluster: str, writable: bool = True):
        self.path = path
        self.cluster = cluster
        self.writable = writable
        self.state: dict = {}

    def load(self) -> "Progress":
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self
        except (OSError, json.JSONDecodeError) as exc:
            raise PublishError(
                f"the resume file {self.path.name} could not be read ({type(exc).__name__}); "
                f"move it aside or run with --restart to start clean"
            ) from exc
        if not isinstance(loaded, dict) or loaded.get("version") != PROGRESS_VERSION:
            raise PublishError(
                f"the resume file {self.path.name} is not version {PROGRESS_VERSION}; "
                f"move it aside or run with --restart to start clean"
            )
        if loaded.get("cluster") not in (None, self.cluster):
            raise PublishError(
                f"the resume file {self.path.name} records a {loaded['cluster']} run and this is "
                f"{self.cluster}; a mint from one cluster cannot be reused on another"
            )
        self.state = loaded
        return self

    def get(self, key: str, default=None):
        return self.state.get(key, default)

    def put(self, key: str, value) -> None:
        if self.state.get(key) == value:
            return
        self.state[key] = value
        self.save()

    def leg(self, leg: str) -> dict | None:
        return (self.state.get("transfers") or {}).get(leg)

    def put_leg(self, leg: str, detail: dict) -> None:
        transfers = dict(self.state.get("transfers") or {})
        transfers[leg] = detail
        self.put("transfers", transfers)

    def pending(self, leg: str) -> dict | None:
        return (self.state.get("pending") or {}).get(leg)

    def put_pending(self, leg: str, *, signature: str, blockhash: str | None) -> None:
        pending = dict(self.state.get("pending") or {})
        pending[leg] = {"signature": signature, "blockhash": blockhash}
        self.put("pending", pending)

    def clear_pending(self, leg: str) -> None:
        pending = dict(self.state.get("pending") or {})
        if pending.pop(leg, None) is not None:
            self.put("pending", pending)

    def clear(self) -> None:
        """Forget the local record. The cluster is not touched, so nothing on it is undone."""
        self.state = {}
        self.path.unlink(missing_ok=True)

    def save(self) -> None:
        if not self.writable:
            return
        state = dict(self.state)
        state["version"] = PROGRESS_VERSION
        state["cluster"] = self.cluster
        state["checkerVersion"] = CHECKER_VERSION
        _assert_local_state(state)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(state, indent=2, sort_keys=True) + "\n"
        handle, temporary = tempfile.mkstemp(prefix=self.path.name + ".", dir=str(self.path.parent))
        try:
            with os.fdopen(handle, "w", encoding="utf-8") as stream:
                stream.write(text)
            os.chmod(temporary, 0o600)
            os.replace(temporary, self.path)
        except BaseException:
            Path(temporary).unlink(missing_ok=True)
            raise


# -- JSON-RPC, read-where-it-is-safe, retried-while-it-is-transient -----------


def _describe_transport(exc: Exception | None) -> str:
    if exc is None:
        return "no attempt was made"
    if isinstance(exc, urlerror.HTTPError):
        return f"HTTPError {exc.code}"
    if isinstance(exc, _Transient):
        return exc.detail
    return type(exc).__name__


def _rpc_once(url: str, method: str, params: list, *, timeout: float):
    """One attempt. Raises `_Transient` for a failure worth repeating, `PublishError` otherwise."""
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    call = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        FAULTS.before_rpc(method)
        with urlrequest.urlopen(call, timeout=timeout) as response:
            raw = response.read()
        payload = json.loads(raw.decode("utf-8"))
    except urlerror.HTTPError as exc:  # a status code: 5xx/429 is the cluster's problem, 4xx is ours
        if exc.code in TRANSIENT_HTTP_STATUS or exc.code >= 500:
            raise _Transient(f"HTTPError {exc.code}") from exc
        raise PublishError(f"{method}: {url} refused the request with HTTP {exc.code} {exc.reason}") from exc
    except (OSError, http.client.HTTPException) as exc:  # timeout, reset, DNS, truncated read
        raise _Transient(type(exc).__name__) from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise _Transient(f"unreadable body ({type(exc).__name__})") from exc
    if payload.get("error"):
        message = payload["error"].get("message") if isinstance(payload["error"], dict) else payload["error"]
        if TRANSIENT_RPC_MESSAGE.search(str(message)):
            raise _Transient(f"jsonrpc error: {message}")
        raise PublishError(f"{method}: {message}")
    return payload.get("result")


def rpc(url: str, method: str, params: list, *, timeout: float = BOUND_RPC, attempts: int | None = None):
    """One JSON-RPC call, retried while the failure is a transport one, then one clear sentence.

    Bounded: at most `RPC_ATTEMPTS` attempts, and the waits between them are 0.5s, 1s, 2s. A
    rejected request or a 4xx is not retried, because repeating it cannot change the answer.
    """
    budget = RPC_ATTEMPTS if attempts is None else max(1, attempts)
    started = time.monotonic()
    last: Exception | None = None
    for attempt in range(budget):
        try:
            return _rpc_once(url, method, params, timeout=timeout)
        except _Transient as exc:
            last = exc
            if attempt + 1 >= budget:
                break
            delay = min(RPC_BACKOFF_CAP, RPC_BACKOFF_BASE * (2**attempt))
            # Printed, not swallowed: a run that quietly retried twice is a run whose log cannot
            # explain why it took longer than the one before it.
            sys.stderr.write(
                f"  {method}: {exc.detail}; retrying in {delay:g}s (attempt {attempt + 2} of {budget})\n"
            )
            sys.stderr.flush()
            time.sleep(delay)
    spent = time.monotonic() - started
    raise PublishError(
        f"{method}: {url} did not answer after {budget} attempts in {spent:.1f}s ({_describe_transport(last)})"
    )


def account_exists(url: str, address: str) -> bool:
    result = rpc(url, "getAccountInfo", [address, {"encoding": "base64"}])
    return bool(result and result.get("value"))


def account_is_executable(url: str, address: str) -> bool:
    result = rpc(url, "getAccountInfo", [address, {"encoding": "base64"}])
    value = (result or {}).get("value") or {}
    return bool(value.get("executable"))


# A validator restarted on a kept ledger answers `getHealth` before it has replayed, and until
# it has, every account reads as absent. Measured on this machine: health ok at +0.5s, the
# program account visible at +4.5s, the mint at +5.0s, and one run that saw neither for nine
# seconds. So every read that decides "already done, or create it" waits, bounded, before it
# believes a negative -- a stale "absent" is a second mint, and that is the bug this file fixes.
REPLAY_LOOKS = 20
REPLAY_INTERVAL = 0.75


def wait_for_account(url: str, address: str, *, looks: int = REPLAY_LOOKS, interval: float = REPLAY_INTERVAL) -> bool:
    """True once the account is visible. Bounded by `looks` x `interval` (15s by default)."""
    for look in range(looks):
        if account_exists(url, address):
            return True
        if look + 1 < looks:
            time.sleep(interval)
    return False


def confirm(url: str, signature: str, *, timeout: float = BOUND_CONFIRM, attempts: int | None = None) -> dict:
    """Wait for a signature, and say whether it succeeded. A failure is a result, not an error.

    A read that fails in transit does not end the wait: `rpc` has already retried it, and the
    answer to "did this land" is still available until this deadline. It records the last
    transport error so the timeout message says what went wrong instead of only that time passed.
    """
    deadline = time.monotonic() + timeout
    last_error: str | None = None
    while time.monotonic() < deadline:
        try:
            result = rpc(
                url, "getSignatureStatuses", [[signature], {"searchTransactionHistory": True}], attempts=attempts
            )
        except PublishError as exc:
            last_error = str(exc)
            time.sleep(1.0)
            continue
        value = ((result or {}).get("value") or [None])[0]
        if value:
            status = value.get("confirmationStatus")
            if value.get("err") is not None:
                return {"ok": False, "err": value["err"], "slot": value.get("slot")}
            if status in ("confirmed", "finalized"):
                return {"ok": True, "err": None, "slot": value.get("slot")}
        time.sleep(0.4)
    suffix = f"; the last read failed with: {last_error}" if last_error else ""
    raise PublishError(f"timed out after {timeout:g}s waiting for {signature}{suffix}")


def blockhash_is_dead(url: str, blockhash: str) -> bool:
    """Provably past its validity window, so a transaction carrying it can never land.

    Anything else -- live, or unreadable -- is reported as not dead, because the caller uses
    this answer to decide whether resending is safe.
    """
    try:
        result = rpc(url, "isBlockhashValid", [blockhash, {"commitment": "confirmed"}], attempts=1)
    except PublishError:
        return False
    return bool(result) and result.get("value") is False


def recover_signature(url: str, signature: str, *, blockhash: str | None, timeout: float = BOUND_CONFIRM) -> dict:
    """Did a transaction we already sent land? Bounded, and it says when it cannot tell.

    Sent-but-unconfirmed is the state that cost the duplicate mint. For a read this is only a
    delay; for a transfer it is a decision, because a resend moves a second ticket. So absence
    is not enough: the blockhash has to be dead too, and when neither can be established the
    run stops and says to run it again rather than guessing.
    """
    deadline = time.monotonic() + timeout
    seen_at: int | None = None
    while time.monotonic() < deadline:
        try:
            result = rpc(
                url, "getSignatureStatuses", [[signature], {"searchTransactionHistory": True}], attempts=1
            )
        except PublishError:
            result = None  # cannot tell yet; keep looking until the deadline
        value = ((result or {}).get("value") or [None])[0]
        if value:
            if value.get("err") is not None:
                return {"state": "landed", "ok": False, "err": value["err"], "slot": value.get("slot")}
            if value.get("confirmationStatus") in ("confirmed", "finalized"):
                return {"state": "landed", "ok": True, "err": None, "slot": value.get("slot")}
            seen_at = value.get("slot")
        elif blockhash and blockhash_is_dead(url, blockhash):
            return {"state": "dropped", "ok": False, "err": None, "slot": None}
        time.sleep(1.0)
    if seen_at is not None:
        raise PublishError(
            f"{signature} is on the cluster at slot {seen_at} but was not confirmed within {timeout:g}s; "
            f"run this again to pick it up, do not resend it"
        )
    detail = " and its blockhash is still live" if blockhash else ""
    raise PublishError(
        f"{signature} was sent and is not visible after {timeout:g}s{detail}; it may still land, so this "
        f"run will not resend it. Run this again to check."
    )


def transaction_details(url: str, signature: str, *, attempts: int = 12, memo: str | None = None) -> dict:
    """Slot, block time, error and the memo strings of a landed transaction.

    `memo` is the text the caller expects to find. Give it and `memoPrograms` answers which
    program carried *that* text; omit it and the field answers which programs carried any
    decodable text, which is only useful for looking at a transaction nobody claims.
    """
    for _ in range(attempts):
        result = rpc(url, "getTransaction", [signature, {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 0}])
        if result:
            return _summarise_transaction(result, signature, memo=memo)
        time.sleep(1.0)
    raise PublishError(f"getTransaction returned nothing for {signature}")



def _instruction_text(data: str) -> str | None:
    """Instruction data arrives base58 in json encoding. Base64 is accepted because it can."""
    for decode in (lambda raw: base58.decode(raw), base64.b64decode):
        try:
            return decode(data).decode("utf-8")
        except Exception:  # noqa: BLE001 - try the next encoding
            continue
    return None


def _memo_instructions(result: dict) -> list[tuple[str, str | None]]:
    """Every memo this transaction carries, as a (text, program id) pair.

    The pair is the point. A list of texts cannot say which instruction produced one, and a
    list of ids cannot say which program carried *our* memo: the transfer instruction in the
    measured devnet transaction decodes as UTF-8 too, so "some instruction's data is a string"
    is satisfied by the System program. The caller that cares about a particular memo compares
    text, and the id it gets back is the id of the instruction that carried that text.

    Instruction data is read first because logs are not guaranteed to be kept. Two log shapes
    exist and both were measured on this machine: the devnet memo program at `Memo4c2p` logs
    `Program log: Memo (len 100)` and then `Program log: ticketpath:quote:...` on the next line,
    and the local validator's memo program at `MemoSq4gq` is the one that logs
    `Program log: Memo (len N): "text"` on a single line -- the attribution in the first draft
    of this docstring was the other way round. A memo echoed only in a log is credited to the
    program whose `invoke` line is open at that point, which is read off the logs and not
    assumed.
    """
    message = (result.get("transaction") or {}).get("message") or {}
    meta = result.get("meta") or {}
    keys = message.get("accountKeys") or []
    pairs: list[tuple[str, str | None]] = []
    for instruction in message.get("instructions") or []:
        data = instruction.get("data")
        if not isinstance(data, str):
            continue
        text = _instruction_text(data)
        if not text:
            continue
        program = None
        index = instruction.get("programIdIndex")
        if isinstance(index, int) and 0 <= index < len(keys):
            key = keys[index]
            identifier = key.get("pubkey") if isinstance(key, dict) else key
            if isinstance(identifier, str):
                program = identifier
        pairs.append((text, program))

    logs = meta.get("logMessages") or []
    open_programs: list[str] = []
    for position, line in enumerate(logs):
        invoked = re.match(r"Program ([1-9A-HJ-NP-Za-km-z]{32,44}) invoke \[\d+\]$", line)
        if invoked:
            open_programs.append(invoked.group(1))
            continue
        exited = re.match(r"Program ([1-9A-HJ-NP-Za-km-z]{32,44}) (success|failed.*)$", line)
        if exited and open_programs:
            open_programs.pop()
            continue
        current = open_programs[-1] if open_programs else None
        quoted = re.match(r'Program log: Memo \(len \d+\): "(.*)"$', line)
        if quoted:
            pairs.append((quoted.group(1), current))
            continue
        header = re.match(r"Program log: Memo \(len (\d+)\)$", line)
        if header and position + 1 < len(logs):
            following = logs[position + 1]
            if following.startswith("Program log: "):
                candidate = following[len("Program log: "):]
                if len(candidate.encode("utf-8")) == int(header.group(1)):
                    pairs.append((candidate, current))
    return pairs


def _programs_for(pairs: list[tuple[str, str | None]], memo: str) -> list[str]:
    """The programs that carried `memo` itself: the pairs whose text equals it, byte for byte."""
    return _unique([program for text, program in pairs if text == memo and program])


def _unique(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _summarise_transaction(result: dict, signature: str, memo: str | None = None) -> dict:
    pairs = _memo_instructions(result)
    return {
        "signature": signature,
        "slot": result.get("slot"),
        "blockTime": result.get("blockTime"),
        "err": (result.get("meta") or {}).get("err"),
        "fee": (result.get("meta") or {}).get("fee"),
        # Every string the transaction carries, which is what "the text landed" is checked
        # against. Not the same question as "which program carried the quote" -- that one is
        # `memoPrograms`, and it filters on the text this run sent.
        "memos": _unique([text for text, _ in pairs]),
        # The pairs themselves, so an assertion can be made about a pair and not about two
        # lists that happen to line up.
        "memoInstructions": [[text, program] for text, program in pairs],
        "memoPrograms": (
            _programs_for(pairs, memo)
            if memo is not None
            else _unique([program for _, program in pairs if program])
        ),
    }


def assert_memo_program(details: dict, cluster: str, *, memo: str) -> str:
    """Check the program that carried *our* memo, and name both ids when it is the wrong one.

    The table is a claim about a cluster, and a claim nothing reads is the bug this function
    exists to stop: the run reads the program id out of the transaction the cluster just
    handed back and compares it with what this repository says that cluster's memo program
    is. A mismatch is one sentence naming both, because the fix is a table edit by a human
    and not a retry -- and a memo that landed under some other program is a quote nothing
    will find.

    `memo` is required, and the comparison is on the pair whose text equals it. Without that,
    a transaction carrying our memo under the right program *and* any other decodable string
    under any other program satisfies the check, which is what the previous version did: it
    compared program ids against a list of every text in the transaction.
    """
    expected = chain_client.memo_program_id(cluster)
    landed = _programs_for([tuple(pair) for pair in details.get("memoInstructions") or []], memo)
    if expected in landed:
        return expected
    shown = ", ".join(landed) if landed else "no instruction carrying that text"
    raise PublishError(
        f"the memo of {details.get('signature')} landed under {shown}, and this repository names "
        f"{expected} as {cluster}'s memo program"
    )


# -- a transaction builder, so the three own instructions can be sent ---------
#
# `solana` and `spl-token` have no verb for "send this instruction", and the three setup
# instructions belong to this project's program, not to the token program. The message format
# is four fields and a list, so it is built here and cross-checked against `solana
# decode-transaction` in tests/test_devnet_publish.py rather than trusted.


def shortvec(value: int) -> bytes:
    out = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value:
            out.append(byte | 0x80)
        else:
            out.append(byte)
            return bytes(out)


@dataclass(frozen=True)
class AccountMeta:
    pubkey: str
    is_signer: bool = False
    is_writable: bool = False


@dataclass(frozen=True)
class Instruction:
    program_id: str
    accounts: tuple[AccountMeta, ...]
    data: bytes


def compile_message(payer: str, instructions: list[Instruction], blockhash: str) -> bytes:
    """The Solana message: header, account keys in canonical order, blockhash, instructions."""
    flags: dict[str, list[bool]] = {}
    order: list[str] = []

    def note(key: str, signer: bool, writable: bool) -> None:
        if key not in flags:
            flags[key] = [False, False]
            order.append(key)
        flags[key][0] = flags[key][0] or signer
        flags[key][1] = flags[key][1] or writable

    note(payer, True, True)
    for instruction in instructions:
        note(instruction.program_id, False, False)
        for meta in instruction.accounts:
            note(meta.pubkey, meta.is_signer, meta.is_writable)

    # Canonical order: the fee payer, then writable signers, readonly signers, writable
    # non-signers, readonly non-signers; first appearance breaks ties inside a group.
    def rank(key: str) -> tuple[int, int]:
        signer, writable = flags[key]
        if key == payer:
            return (0, 0)
        if signer and writable:
            return (1, order.index(key))
        if signer:
            return (2, order.index(key))
        if writable:
            return (3, order.index(key))
        return (4, order.index(key))

    keys = sorted(flags, key=rank)
    index_of = {key: position for position, key in enumerate(keys)}
    signer_count = sum(1 for key in keys if flags[key][0])
    readonly_signed = sum(1 for key in keys if flags[key][0] and not flags[key][1])
    readonly_unsigned = sum(1 for key in keys if not flags[key][0] and not flags[key][1])

    out = bytearray()
    out += bytes([signer_count, readonly_signed, readonly_unsigned])
    out += shortvec(len(keys))
    for key in keys:
        out += base58.decode(key)
    out += base58.decode(blockhash)
    out += shortvec(len(instructions))
    for instruction in instructions:
        out.append(index_of[instruction.program_id])
        out += shortvec(len(instruction.accounts))
        for meta in instruction.accounts:
            out.append(index_of[meta.pubkey])
        out += shortvec(len(instruction.data))
        out += instruction.data
    return bytes(out)


def build_transaction(message: bytes, signatures: list[bytes]) -> bytes:
    return shortvec(len(signatures)) + b"".join(signatures) + message


# -- the program's own instructions -----------------------------------------

TAG_INIT_EXTRA_METAS = 0
TAG_INIT_RECORD = 1
TAG_SET_PENDING_PRICE = 2


def instruction_init_extra_metas(*, payer: str, mint: str, extra_metas: str, record: str, program_id: str) -> Instruction:
    return Instruction(
        program_id=program_id,
        accounts=(
            AccountMeta(payer, True, True),
            AccountMeta(mint, False, False),
            AccountMeta(extra_metas, False, True),
            AccountMeta(SYSTEM_PROGRAM, False, False),
        ),
        data=bytes([TAG_INIT_EXTRA_METAS]) + base58.decode(record),
    )


def instruction_init_record(*, payer: str, mint: str, record: str, program_id: str, face: int, cap_bps: int) -> Instruction:
    return Instruction(
        program_id=program_id,
        accounts=(
            AccountMeta(payer, True, True),
            AccountMeta(mint, False, False),
            AccountMeta(record, False, True),
            AccountMeta(SYSTEM_PROGRAM, False, False),
        ),
        data=bytes([TAG_INIT_RECORD]) + face.to_bytes(8, "little") + cap_bps.to_bytes(2, "little"),
    )


def instruction_set_pending_price(*, record: str, program_id: str, price: int) -> Instruction:
    return Instruction(
        program_id=program_id,
        accounts=(AccountMeta(record, False, True),),
        data=bytes([TAG_SET_PENDING_PRICE]) + price.to_bytes(8, "little"),
    )


# -- the artefact: public data only -----------------------------------------


ARTEFACT_FIELDS = (
    "cluster",
    "rpcUrl",
    "signature",
    "slot",
    "blockTime",
    "memoText",
    "quoteHash",
    "quoteId",
    "eventId",
    "tierId",
    "recommendedLamports",
    "asOf",
    "modelVersion",
    "mint",
    "programId",
    "memoProgram",
    "checkedAt",
    "checkerVersion",
    "faceLamports",
    "capBps",
    "explorer",
    "transfers",
)

TRANSFER_FIELDS = ("signature", "slot", "blockTime", "priceLamports", "error", "explorer")


def explorer_url(kind: str, value: str, cluster: str) -> str | None:
    """An explorer link, for devnet only. A local rehearsal has no public explorer to link to."""
    if cluster != "devnet":
        return None
    return f"https://explorer.solana.com/{kind}/{value}?cluster=devnet"


def build_artefact(
    *,
    cluster: str,
    rpc_url: str,
    quote: dict,
    memo: dict,
    mint: str,
    program_id: str,
    transfers: dict,
    checked_at: str | None = None,
) -> dict:
    """Assemble the record the console reads. Pure: no clock, no cluster, no file.

    Everything it can hold is in ARTEFACT_FIELDS, and the hash it carries is recomputed from
    the fields beside it, so a file that does not verify cannot be built by this function.
    """
    record = {
        "cluster": cluster,
        "rpcUrl": rpc_url,
        "signature": memo["signature"],
        "slot": memo["slot"],
        "blockTime": memo["blockTime"],
        "memoText": quote["memoText"],
        "quoteHash": quote["quoteHash"],
        "quoteId": quote["quoteId"],
        "eventId": quote["eventId"],
        "tierId": quote["tierId"],
        "recommendedLamports": quote["recommendedLamports"],
        "asOf": quote["asOf"],
        "modelVersion": quote["modelVersion"],
        "mint": mint,
        "programId": program_id,
        # Which program the memo instruction landed under, read off the transaction this run
        # sent, and not off the per-cluster table: a field filled from the table would agree
        # with itself and could never show what the cluster actually did. `assert_memo_program`
        # has already compared the two by the time this record is built, so a run that reaches
        # here recorded the observation that matched the claim -- and a file that records a
        # different id is a file written by a run that failed before this point.
        "memoProgram": (memo.get("memoPrograms") or [None])[0],
        "checkedAt": checked_at or now_iso(),
        "checkerVersion": CHECKER_VERSION,
        "faceLamports": FACE_LAMPORTS,
        "capBps": CAP_BPS,
        "explorer": {
            "transaction": explorer_url("tx", memo["signature"], cluster),
            "mint": explorer_url("address", mint, cluster),
            "program": explorer_url("address", program_id, cluster),
        },
        "transfers": transfers,
    }
    if chain_client.quote_hash(record) != record["quoteHash"]:
        raise PublishError("the artefact's own quote hash does not recompute; refusing to write it")
    if record["memoText"] != chain_client.expected_memo(record["quoteId"], record["quoteHash"]):
        raise PublishError("the artefact's memo is not the console's grammar; refusing to write it")
    _assert_public(record)
    return record


def _assert_public(record: dict) -> None:
    """No key material, no home path, no field the loader does not know."""
    extra = set(record) - set(ARTEFACT_FIELDS)
    if extra:
        raise PublishError(f"the artefact carries fields it should not: {sorted(extra)}")
    for name, value in record.items():
        if name == "transfers":
            for leg, detail in value.items():
                bad = set(detail) - set(TRANSFER_FIELDS)
                if bad:
                    raise PublishError(f"transfer {leg} carries fields it should not: {sorted(bad)}")
            continue
        if isinstance(value, str) and value.startswith(str(Path.home())):
            raise PublishError(f"the artefact carries an absolute home path in {name}")


def write_artefact(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    path.write_text(text, encoding="utf-8")


def read_artefact(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# -- the console's quote, and the memo that commits to it --------------------


def console_quote() -> dict:
    """The quote the console renders for the pinned instant, and the memo that commits to it.

    Built through the console's own `price_guidance` and hashed with the console's own
    `quote_hash`, so the two implementations cannot drift: if this returns, the `[DEVNET]`
    slot will recompute the same digest.
    """
    from guidance import build_orchestrator  # tools/guidance.py, standard library only

    orchestrator = build_orchestrator(AS_OF)
    payload = orchestrator.price_guidance(event_id=EVENT_ID, tier_id=TIER_ID, as_of=AS_OF)
    chain = payload.get("chain") or {}
    decision = payload.get("decision") or {}
    recommended = decision.get("recommendedLamports")
    if isinstance(recommended, dict):
        recommended = recommended.get("value")
    if recommended is None:
        raise PublishError(f"the console refused to recommend a price for {EVENT_ID}: {decision.get('refusalCode')}")
    fields = {
        "quoteId": chain.get("quoteId"),
        "eventId": EVENT_ID,
        "tierId": TIER_ID,
        "recommendedLamports": recommended,
        "asOf": payload.get("asOf"),
        "modelVersion": payload.get("modelVersion"),
    }
    digest = chain_client.quote_hash(fields)
    if digest != chain.get("quoteHash"):
        raise PublishError("the quote hash recomputed here is not the one the console renders")
    if chain.get("memoText") != chain_client.expected_memo(fields["quoteId"], digest):
        raise PublishError("the console's memo text is not the quote grammar")
    return {**fields, "quoteHash": digest, "memoText": chain["memoText"]}


# -- the run -----------------------------------------------------------------


@dataclass
class Context:
    cluster: str
    rpc_url: str
    keypair: Path
    buyer_keypair: Path
    out: Path
    dry_run: bool = False
    min_lamports: int = MIN_BALANCE_LAMPORTS
    validator: "LocalValidator | None" = None
    ledger: Path | None = None
    program_id: str | None = None
    payer: str | None = None
    mint_keypair_path: Path | None = None
    progress: Progress | None = None
    cache: dict = field(default_factory=dict)

    def say(self, line: str) -> None:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def plan(self, line: str) -> None:
        sys.stdout.write(("[plan] " if self.dry_run else "") + line + "\n")
        sys.stdout.flush()

    def fault(self, point: str) -> None:
        """A rehearsal hook, inert unless `--inject` armed this exact point."""
        FAULTS.after_step(point)

    def note(self, key: str, value) -> None:
        """Write one finished fact to the resume file, now, before the next step can be lost."""
        if self.progress is not None:
            self.progress.put(key, value)

    def recorded(self, key: str):
        return self.progress.get(key) if self.progress is not None else None

    def save_leg(self, leg: str, detail: dict) -> None:
        if self.progress is not None:
            self.progress.put_leg(leg, detail)

    def clear_pending(self, leg: str) -> None:
        if self.progress is not None:
            self.progress.clear_pending(leg)

    def record_accounts(self, *, authority_ata: str, buyer: str, buyer_ata: str) -> None:
        """Persist the three addresses this run is about, refusing to mix runs."""
        for key, value in (("authorityAta", authority_ata), ("buyer", buyer), ("buyerAta", buyer_ata)):
            recorded = self.recorded(key)
            if recorded and recorded != value:
                raise PublishError(
                    f"this run derives {key} {value}, and the resume file records {recorded}: a different "
                    f"buyer or mint, so the earlier transfer pair cannot be reused. Restore the keypair the "
                    f"run started with, or delete the resume file to start clean (--restart)."
                )
            self.note(key, value)


def solana(ctx: Context, *args: str, timeout: float = BOUND_TOKEN, check: bool = True) -> str:
    command = [which("solana") or "solana", "--url", ctx.rpc_url, *args]
    return run(command, timeout=timeout, what=f"solana {args[0] if args else ''}".strip(), check=check)


def spl_token(ctx: Context, *args: str, timeout: float = BOUND_TOKEN, check: bool = True) -> str:
    command = [which("spl-token") or "spl-token", "--url", ctx.rpc_url, "--program-2022", *args]
    return run(command, timeout=timeout, what=f"spl-token {args[0] if args else ''}".strip(), check=check)


def spl(ctx: Context, *args: str) -> list[str]:
    """The spl-token command line, fully specified so no verb has to guess a signer.

    The config file names the keypair by path, and `--fee-payer` is repeated explicitly
    because `create-account --owner <someone-else>` otherwise refuses with "fee payer is
    required": the owner is not the client keypair and the CLI will not assume the payer is.
    """
    return [
        which("spl-token") or "spl-token",
        "--url", ctx.rpc_url,
        "--config", str(keypair_config(ctx)),
        "--fee-payer", str(ctx.keypair),
        "--program-2022",
        *args,
    ]


def keypair_config(ctx: Context) -> Path:
    """A throwaway CLI config pointing at the keypair by path. It never holds the key."""
    cached = ctx.cache.get("config")
    if cached:
        return cached
    handle = tempfile.NamedTemporaryFile("w", suffix=".yml", prefix="tp-devnet-", delete=False)
    handle.write(
        f"json_rpc_url: {ctx.rpc_url}\n"
        'websocket_url: ""\n'
        f"keypair_path: {ctx.keypair}\n"
        'address_labels:\n'
        '  "11111111111111111111111111111111": System Program\n'
        "commitment: confirmed\n"
    )
    handle.close()
    os.chmod(handle.name, 0o600)
    atexit.register(lambda: Path(handle.name).unlink(missing_ok=True))
    ctx.cache["config"] = Path(handle.name)
    ctx.say(f"  cli config: {handle.name} -> {ctx.rpc_url}")
    return Path(handle.name)


def payer_pubkey(ctx: Context) -> str:
    if ctx.payer:
        return ctx.payer
    output = run(
        [which("solana-keygen") or "solana-keygen", "pubkey", str(ctx.keypair)],
        timeout=30,
        what="solana-keygen pubkey",
    )
    ctx.payer = output.strip().splitlines()[-1].strip()
    return ctx.payer


def program_id_for(ctx: Context) -> str:
    if ctx.program_id:
        return ctx.program_id
    if not PROGRAM_KEYPAIR.exists():
        raise PublishError(f"no program keypair at {PROGRAM_KEYPAIR}; run the build step first")
    output = run(
        [which("solana-keygen") or "solana-keygen", "pubkey", str(PROGRAM_KEYPAIR)],
        timeout=30,
        what="solana-keygen pubkey (program)",
    )
    ctx.program_id = output.strip().splitlines()[-1].strip()
    return ctx.program_id


def derive_address(ctx: Context, program_id: str, *seeds: str) -> str:
    """`find-program-derived-address`, so the PDA is derived by the toolchain and not here."""
    command = [which("solana") or "solana", "find-program-derived-address", program_id, *seeds]
    output = run(command, timeout=60, what="solana find-program-derived-address")
    return output.strip().splitlines()[-1].strip()


def sign_message(ctx: Context, message: bytes) -> bytes:
    """One signature from a separate process; this process never opens the keypair."""
    command = [sys.executable, str(TOOLS_DIR / "solana_sign.py"), "--keypair", str(ctx.keypair)]
    try:
        completed = subprocess.run(command, input=message, capture_output=True, timeout=300)
    except subprocess.TimeoutExpired as exc:
        raise PublishError("the signer did not answer within 300s") from exc
    if completed.returncode != 0:
        reason = completed.stderr.decode("utf-8", "replace").strip().splitlines()
        raise PublishError(f"the signer refused: {reason[-1] if reason else 'no reason'}")
    signature = base58.decode(completed.stdout.decode("utf-8", "replace").strip())
    if len(signature) != 64:
        raise PublishError("the signer returned something that is not a 64-byte signature")
    return signature


def send_instructions(
    ctx: Context,
    instructions: list[Instruction],
    *,
    what: str,
    skip_preflight: bool = False,
    allow_failure: bool = False,
    pending_key: str | None = None,
) -> tuple[str, dict]:
    """Build, sign and send one transaction. Returns (signature, status).

    `skip_preflight` is what makes a *refusal* observable: with the preflight check on, a
    transaction the hook will reject never gets a signature, so there is nothing to show. With
    it off, the refusal lands as a failed transaction with its own signature and its own error,
    which is the only form of it a sceptic can look up.

    `pending_key` names a step whose signature is written to the resume file the instant
    `sendTransaction` returns it, together with the blockhash it was signed against, and is
    only cleared by the caller once the outcome is recorded. A rerun that finds one asks the
    cluster whether it landed instead of sending it again -- which is what stops a second
    ticket crossing while the operator is not looking.
    """
    blockhash = rpc(ctx.rpc_url, "getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
    message = compile_message(payer_pubkey(ctx), instructions, blockhash)
    signature = sign_message(ctx, message)
    wire = base64.b64encode(build_transaction(message, [signature])).decode("ascii")
    sent = rpc(
        ctx.rpc_url,
        "sendTransaction",
        [wire, {"encoding": "base64", "skipPreflight": skip_preflight, "preflightCommitment": "confirmed"}],
    )
    if pending_key is not None and ctx.progress is not None:
        ctx.progress.put_pending(pending_key, signature=sent, blockhash=blockhash)
    status = confirm(ctx.rpc_url, sent)
    if not status["ok"] and not allow_failure:
        raise PublishError(f"{what}: the transaction failed: {status['err']} ({sent})")
    ctx.say(f"  {what}: {sent} (slot {status.get('slot')})")
    return sent, status


# -- the local validator ------------------------------------------------------


class LocalValidator:
    """A single-node cluster started for one run, and killed on every exit path."""

    def __init__(self, *, ledger: Path, port: int, faucet_port: int, reset: bool = True, fund: str | None = None):
        self.ledger = ledger
        self.port = port
        self.faucet_port = faucet_port
        self.reset = reset
        self.fund = fund
        self.process: subprocess.Popen | None = None
        self._stopped = False

    @property
    def rpc_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        if not which("solana-test-validator"):
            raise PublishError("solana-test-validator is not on PATH")
        # `--ledger` is a directory the caller names, and the validator will not create the
        # parents of it: a path under a directory that does not exist yet is a legitimate
        # argument, so make the parents here rather than failing after a 4s retry budget.
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        command = [
            which("solana-test-validator") or "solana-test-validator",
            *(["--reset"] if self.reset else []),
            "--quiet",
            "--ledger", str(self.ledger),
            "--rpc-port", str(self.port),
            # The faucet's default port is fixed, so a validator someone left running makes
            # this one fail with "failed to start faucet". Pick a free one instead.
            "--faucet-port", str(self.faucet_port),
            # Fund the authority at genesis, so the rehearsal does not need the faucet at all:
            # `--mint` is the account the native tokens are created into, and a local ledger
            # starts with hundreds of millions of SOL that nothing on this machine can spend.
            # The faucet stays enabled for the case where the ledger predates this flag.
            *(["--mint", self.fund] if self.fund else []),
            "--clone-upgradeable-program", TOKEN_2022_PROGRAM,
            # The clone source is `--url <devnet>` below, so this names the account devnet hosts
            # at the id the CLI writes its memo to. Measured on 2026-11-08, a local validator's
            # genesis already holds that id, but as a stub whose ProgramData records slot 0, and
            # the memo cannot execute there: `solana transfer --with-memo` fails with "Program is
            # not deployed". Cloning the program, upgrading it, and cloning its programdata were
            # each tried and none of them moves that slot, because the genesis account wins. The
            # clone is kept because it leaves the rehearsal's ledger holding devnet's account at
            # the id the run will name, and the failure it does not fix is recorded in finding 40
            # rather than papered over here.
            "--clone", chain_client.memo_program_id("localnet"),
            "--url", CLUSTER_URLS["devnet"],
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
        deadline = time.monotonic() + BOUND_VALIDATOR_START
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                tail = (self.process.stdout.read() or "")[-1500:] if self.process.stdout else ""
                raise PublishError(f"solana-test-validator exited before it answered:\n{tail}")
            try:
                # One attempt per look: this is already a poll loop with its own deadline, and the
                # rpc retry budget would spend 3.5s of it on a validator that has not opened its
                # port yet.
                if rpc(self.rpc_url, "getHealth", [], timeout=2, attempts=1) == "ok":
                    return
            except PublishError:
                time.sleep(0.5)
        raise PublishError(f"solana-test-validator did not answer on {self.rpc_url} within {BOUND_VALIDATOR_START:g}s")

    def _on_signal(self, signum, _frame) -> None:
        self.stop()
        raise SystemExit(128 + signum)

    def stop(self) -> None:
        if self._stopped:
            return
        self._stopped = True
        if self.process and self.process.poll() is None:
            try:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
                self.process.wait(timeout=20)
            except (ProcessLookupError, subprocess.TimeoutExpired):
                try:
                    os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
        if self.reset and self.ledger.exists():
            shutil.rmtree(self.ledger, ignore_errors=True)
        elif self.ledger.exists():
            sys.stderr.write(f"devnet_publish: ledger kept at {self.ledger}\n")


def free_port() -> int:
    for _ in range(64):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            probe.bind(("127.0.0.1", 0))
            port = probe.getsockname()[1]
        if port not in RESERVED_PORTS and port > 1024:
            return port
    raise PublishError("no free port outside the reserved ones")


# -- the steps ----------------------------------------------------------------


def step_preflight(ctx: Context) -> None:
    for binary in ("solana", "spl-token", "solana-keygen", "cargo-build-sbf"):
        if not which(binary):
            raise PublishError(f"{binary} is not on PATH; the Solana toolchain block in ~/.profile sets it, so run this from a login shell (bash -lc)")
    if not ctx.keypair.exists():
        message = (
            f"no keypair at {ctx.keypair}. Set TP_DEVNET_KEYPAIR to its path; "
            f"solana-keygen new --silent -o <path> makes one and never prints its phrase."
        )
        if ctx.dry_run:
            ctx.say(f"warning: {message}")
        else:
            raise PublishError(message)


def step_balance(ctx: Context) -> None:
    if ctx.cluster == "localnet":
        # A local validator has its own faucet and no scarcity: fund and move on.
        deadline = time.monotonic() + 120
        while time.monotonic() < deadline:
            lamports = balance_lamports(ctx)
            if lamports >= ctx.min_lamports:
                return
            solana(ctx, "airdrop", "2", payer_pubkey(ctx), timeout=60, check=False)
            time.sleep(1.0)
        raise PublishError(f"the local validator did not fund {payer_pubkey(ctx)} within 120s")
    lamports = balance_lamports(ctx)
    if lamports < ctx.min_lamports:
        raise Refused(
            f"balance is {lamports / 1e9:.9f} SOL and this needs {ctx.min_lamports / 1e9:.2f} SOL.\n"
            f"The devnet RPC faucet is closed (error 410), so `solana airdrop` cannot work and retrying it is wasted time.\n"
            f"Fund it yourself, once:\n"
            f"  1. open {FAUCET_URL} and sign in with GitHub\n"
            f"  2. network: devnet, address: {payer_pubkey(ctx)}\n"
            f"  3. request SOL, then run this again"
        )


def balance_lamports(ctx: Context) -> int:
    output = run(
        [which("solana") or "solana", "balance", payer_pubkey(ctx), "--url", ctx.rpc_url, "--output", "json"],
        timeout=60,
        what="solana balance",
    )
    try:
        return int(json.loads(output).get("lamports", 0))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PublishError(f"solana balance printed something unexpected: {output.strip()[:120]}") from exc


def step_build(ctx: Context) -> Path:
    if SO_PATH.exists() and SO_PATH.stat().st_size > 0:
        ctx.say(f"build: reusing {SO_PATH.name} ({SO_PATH.stat().st_size:,} bytes)")
        return SO_PATH
    if ctx.dry_run:
        ctx.plan(f"build: cargo-build-sbf in {PROGRAM_DIR} -> {SO_PATH}")
        return SO_PATH
    env_note = f"build: cargo-build-sbf in {PROGRAM_DIR.name}/ (bounded at {BOUND_BUILD:g}s, this is the slow step)"
    ctx.say(env_note)
    started = time.monotonic()
    run(
        [which("cargo-build-sbf") or "cargo-build-sbf", "--sbf-out-dir", "target/deploy"],
        timeout=BOUND_BUILD,
        what="cargo-build-sbf",
        cwd=PROGRAM_DIR,
    )
    if not SO_PATH.exists():
        raise PublishError(f"the build produced no {SO_PATH}")
    ctx.say(f"  {SO_PATH.name}: {SO_PATH.stat().st_size:,} bytes in {time.monotonic() - started:.1f}s")
    return SO_PATH


def v2_log_strings_in(binary: bytes) -> tuple[str, ...]:
    """Which v2-only log strings a program binary carries; empty means no evidence of v2.

    It exists so that the deploy is judged on its bytes and on nothing else: `cargo-build-sbf`
    writes the v2 build over the same `cap_hook.so` the v1 run deployed, so the path, the
    file name and the build timestamp all say "v1" while the code inside is v2. The three
    phrases below are in the v2 program's own log strings -- the floor refusal, the policy
    branch, the held-time write -- and in no v1 build. A hit is therefore the v2 build, and
    one hit is enough wherever in the file it sits.
    """
    return tuple(marker for marker in V2_ONLY_LOG_STRINGS if marker.encode("ascii") in binary)


def refuse_frozen_devnet_upgrade(*, program_id: str, binary: bytes, source: str) -> None:
    """Refuse to send a deploy that would upgrade the frozen devnet program to the v2 build.

    `FROZEN_DEVNET_PROGRAM` was deployed from the v1 build on 2026-11-07 and exercised on
    devnet; `records/devnet-artefacts.json` is its public record and the console renders
    that record. The keypair that owns it is still on disk, and this file deploys whatever
    `SO_PATH` holds, which is now the v2 build, so nothing but the target id and the bytes
    separates a rehearsal from an upgrade: a `solana program deploy` under that keypair
    would keep the program id, change the code underneath it, and leave every existing
    devnet mint running v2 while its record was only ever checked against v1.

    There is deliberately no switch. No flag, no environment variable, no config file: an
    escape hatch that can be tripped by accident is the bug this function exists to close.
    The recorded way to deploy v2 is `tools/publish_v2.py`, which uses a keypair of its own
    on a local validator and never names this program id as a target.

    `binary` is empty when there is no build to inspect, and an empty binary is not v2.
    """
    if program_id != FROZEN_DEVNET_PROGRAM:
        return
    markers = v2_log_strings_in(binary)
    if not markers:
        return
    digest = hashlib.sha256(binary).hexdigest()
    raise Refused(
        f"REFUSING TO DEPLOY: {program_id} is the frozen devnet program and {source} is the v2 build.\n"
        f"  the binary carries v2-only log strings: {', '.join(markers)} (sha256 {digest}).\n"
        "  the frozen program was deployed from the v1 build with\n"
        "  programs/cap_hook/target/deploy/cap_hook-keypair.json, and that keypair still owns it, so this\n"
        "  deploy would upgrade the proven program in place: same program id, v2 code underneath, and every\n"
        "  mint that points at it running something its record was never checked against.\n"
        "  a deliberate v2 deploy is `python3 tools/publish_v2.py`: its own keypair, its own program id, on\n"
        "  a local validator. Upgrading the frozen program is not a thing this repository does.\n"
        "  there is no flag and no environment variable that turns this check off, on purpose."
    )


def step_deploy(ctx: Context, program_id: str) -> None:
    # First, before the dry-run branch and before any cluster read: with the v2 build in
    # `SO_PATH` and this keypair, the deploy this step would send is an upgrade of the frozen
    # program. `account_is_executable` is not what stands between those two facts -- it is a
    # read that answers "absent" while a node replays -- so the guard is the bytes and the id.
    source = SO_PATH.relative_to(REPO_ROOT).as_posix() if SO_PATH.is_relative_to(REPO_ROOT) else str(SO_PATH)
    binary = b""
    if SO_PATH.exists():  # absent is a dry run before the first build: nothing to inspect
        try:
            binary = SO_PATH.read_bytes()
        except OSError as exc:
            raise PublishError(
                f"{source} cannot be read ({exc}), so there is no way to know whether it is the v2 build: "
                "refusing to deploy a binary that cannot be checked"
            ) from exc
    refuse_frozen_devnet_upgrade(program_id=program_id, binary=binary, source=source)
    if ctx.dry_run:
        ctx.plan(f"deploy: solana program deploy {SO_PATH.name} as {program_id} (skipped when it is already executable)")
        return
    # A validator restarted on a kept ledger answers getHealth before it has replayed, and for
    # a moment every account reads as absent. Measured: a second run against a kept ledger
    # tried to deploy a program that was already there and the runtime refused with
    # "account already in use". Six bounded looks is enough for replay and costs nothing
    # on a genuinely fresh cluster.
    for attempt in range(6):
        if account_is_executable(ctx.rpc_url, program_id):
            ctx.say(f"deploy: {program_id} is already deployed and executable")
            return
        if attempt < 5:
            time.sleep(1.5)
    ctx.say(f"deploy: {program_id}")
    signature = solana(
        ctx,
        "program", "deploy", str(SO_PATH),
        "--program-id", str(PROGRAM_KEYPAIR),
        "--keypair", str(ctx.keypair),
        timeout=BOUND_DEPLOY,
    )
    found = last_base58(signature)
    ctx.say(f"  deployed{f' ({found})' if found else ''}")


def first_pubkey(output: str) -> str | None:
    """The first address-shaped token a CLI printed. An address is 32 bytes of base58."""
    for token in re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b", output):
        try:
            if len(base58.decode(token)) == 32:
                return token
        except Exception:  # noqa: BLE001 - not base58, keep looking
            continue
    return None


def keypair_pubkey(ctx: Context, path: Path) -> str:
    """The address a keypair file unlocks, asked of `solana-keygen`, never read here."""
    output = run(
        [which("solana-keygen") or "solana-keygen", "pubkey", str(path)],
        timeout=30,
        what=f"solana-keygen pubkey ({path.name})",
    )
    address = output.strip().splitlines()[-1].strip() if output.strip() else ""
    if not address:
        raise PublishError(f"solana-keygen pubkey printed no address for {path.name}")
    return address


def mint_keypair(ctx: Context) -> Path:
    """The mint's keypair, made here once and kept, so the mint address survives the process.

    A keypair file is generated rather than left to `spl-token`, because `spl-token
    create-token` otherwise invents the address inside the call that creates it: a run that
    died before the CLI printed the address left a mint on the cluster that nothing on disk
    could name, and the rerun made a second one. It sits beside the authority keypair and is
    never opened by this process.
    """
    path = ctx.mint_keypair_path or (ctx.keypair.parent / "mint-keypair.json")
    ctx.mint_keypair_path = path
    if path.exists():
        return path
    if ctx.dry_run:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    run(
        [which("solana-keygen") or "solana-keygen", "new", "--silent", "--no-bip39-passphrase", "-o", str(path)],
        timeout=60,
        what="solana-keygen new (mint)",
    )
    os.chmod(path, 0o600)
    return path


def mint_metadata_on_chain(url: str, mint: str) -> bool | None:
    """True when *our* metadata is already on the mint, False when it is not, None when unreadable.

    The parsed account shape is what Token-2022's metadata extension reports; an RPC that does
    not answer in that shape is not a "no", it is an "unknown", and the caller treats the two
    differently.
    """
    try:
        result = rpc(url, "getAccountInfo", [mint, {"encoding": "jsonParsed"}])
    except PublishError:
        return None
    data = ((result or {}).get("value") or {}).get("data")
    if not isinstance(data, dict):
        return None
    extensions = ((data.get("parsed") or {}).get("info") or {}).get("extensions") or []
    for extension in extensions:
        if extension.get("extension") == "tokenMetadata":
            state = extension.get("state") or {}
            return (
                state.get("name") == TICKET_NAME
                and state.get("symbol") == TICKET_SYMBOL
                and state.get("uri") == TICKET_URI
            )
    return False


def ensure_mint_metadata(ctx: Context, mint: str, *, already: bool) -> None:
    """`initialize-metadata` exactly once per mint, whether this run made the mint or not.

    Safe to attempt on a mint that may already carry it: the CLI's refusal is checked against
    the chain, and only a refusal that the chain does not explain is an error. That is what
    makes a resume after the metadata landed but before it was recorded harmless. The second
    attempt covers the measured case where the CLI's own read of the mint preceded replay and
    it answered `AccountNotFound` for a mint that was there.
    """
    if already or ctx.recorded("mintMetadata") is True:
        return
    if ctx.dry_run:
        ctx.plan(f"mint: spl-token initialize-metadata {mint} {TICKET_NAME!r} {TICKET_SYMBOL} {TICKET_URI}")
        return
    if mint_metadata_on_chain(ctx.rpc_url, mint) is True:
        ctx.say("  metadata is already on the mint")
        ctx.note("mintMetadata", True)
        return
    for attempt in (1, 2):
        try:
            run(
                spl(ctx, "initialize-metadata", mint, TICKET_NAME, TICKET_SYMBOL, TICKET_URI),
                timeout=BOUND_TOKEN,
                what="spl-token initialize-metadata",
            )
        except PublishError:
            if mint_metadata_on_chain(ctx.rpc_url, mint) is True:
                ctx.say("  metadata was already initialised by an earlier attempt")
                break
            if attempt == 1 and wait_for_account(ctx.rpc_url, mint):
                ctx.say("  the mint was not visible to the CLI for a moment; retrying once")
                continue
            raise
        else:
            ctx.say(f"  metadata initialised: {TICKET_NAME!r} {TICKET_SYMBOL} <{TICKET_URI}>")
            break
    ctx.note("mintMetadata", True)


def step_mint(ctx: Context, program_id: str) -> str:
    """Create the mint, or take the one this run already made. Never a second one.

    Three places can name the mint, in the order they are trusted: the resume file, the
    artefact of a run that got all the way through, and the mint keypair on disk. The keypair
    is the one that matters, because it is what makes the address exist before the cluster
    does: a rerun either finds that address or creates that same address again.

    Every candidate that predates this process is looked up patiently, and a create that fails
    because the account is already there is treated as done rather than as an error: both are
    the same stale-negative race against a validator that has not finished replaying.
    """
    recorded = ctx.recorded("mint")
    from_artefact = (read_artefact(ctx.out) or {}).get("mint")
    if ctx.dry_run:
        existing = recorded or from_artefact
        if existing:
            ctx.plan(f"mint: would reuse {existing} from {'the resume file' if recorded else ctx.out.name}")
            return existing
        ctx.plan(f"mint: spl-token create-token --program-2022 --decimals 0 --transfer-hook {program_id} --enable-metadata")
        ctx.plan(f"mint: spl-token initialize-metadata <mint> {TICKET_NAME!r} {TICKET_SYMBOL} {TICKET_URI}")
        return "<mint>"

    for candidate, source, metadata_done in (
        (recorded, "the resume file", ctx.recorded("mintMetadata") is True),
        # An artefact is only written by a run that got all the way through, so the mint it
        # names has had its metadata initialised already.
        (from_artefact, ctx.out.name, True),
    ):
        if candidate and wait_for_account(ctx.rpc_url, candidate):
            ctx.say(f"mint: reusing {candidate} from {source}")
            ctx.note("mint", candidate)
            ensure_mint_metadata(ctx, candidate, already=metadata_done)
            return candidate

    # Only now is the keypair needed: creating one for a run that is reusing a recorded mint
    # would put a file on disk for nothing.
    keypair_existed = (ctx.mint_keypair_path or (ctx.keypair.parent / "mint-keypair.json")).exists()
    keypair = mint_keypair(ctx)
    chosen = keypair_pubkey(ctx, keypair)
    # A mint keypair that was already on disk means an earlier attempt chose this address.
    # One this run just generated cannot have an account yet, so there is nothing to wait for.
    if keypair_existed and wait_for_account(ctx.rpc_url, chosen):
        ctx.say(f"mint: reusing {chosen} (the mint keypair already has an account)")
        ctx.note("mint", chosen)
        ensure_mint_metadata(ctx, chosen, already=ctx.recorded("mintMetadata") is True)
        return chosen

    # Written down before it exists. If the next call dies, this address is already the one
    # on disk, so the rerun creates this mint rather than another one.
    ctx.note("mint", chosen)
    ctx.say(f"mint: {chosen} (chosen here and recorded before it is created)")
    try:
        output = run(
            spl(ctx, "create-token", "--decimals", "0", "--transfer-hook", program_id, "--enable-metadata", str(keypair)),
            timeout=BOUND_TOKEN,
            what="spl-token create-token",
        )
    except PublishError:
        if not wait_for_account(ctx.rpc_url, chosen):
            raise
        ctx.say(f"  {chosen} was already on the cluster; the read before the create was stale")
    else:
        found = first_pubkey(output)
        if found and found != chosen:
            raise PublishError(
                f"spl-token created {found}, not the {chosen} this run chose; the mint keypair on disk is "
                f"not the one that was used, so nothing here can be trusted. Nothing was recorded."
            )
        ctx.say(f"mint: {chosen} (Token-2022, 0 decimals, TransferHook -> {program_id}, MetadataPointer -> itself)")
    ctx.fault("mint.created")
    ensure_mint_metadata(ctx, chosen, already=False)
    return chosen


def step_accounts(ctx: Context, mint: str) -> tuple[str, str, str]:
    """The authority's token account, the buyer's wallet, and the buyer's token account.

    All three are derived rather than remembered, so they are the same on every run for the
    same mint and the same two keypairs, and `record_accounts` refuses a run whose record
    disagrees with what the toolchain derives now.
    """
    if ctx.dry_run:
        ctx.plan(f"accounts: spl-token create-account {mint} for the authority and for a throwaway buyer")
        return "<authority-ata>", buyer_pubkey(ctx), "<buyer-ata>"
    authority_ata = token_account_for(ctx, mint, payer_pubkey(ctx), create=True)
    buyer = buyer_pubkey(ctx)
    buyer_ata = token_account_for(ctx, mint, buyer, create=True)
    ctx.record_accounts(authority_ata=authority_ata, buyer=buyer, buyer_ata=buyer_ata)
    return authority_ata, buyer, buyer_ata


def buyer_pubkey(ctx: Context) -> str:
    cached = ctx.cache.get("buyer")
    if cached:
        return cached
    if not ctx.buyer_keypair.exists():
        if ctx.dry_run:
            return "<buyer>"
        ctx.buyer_keypair.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(ctx.buyer_keypair.parent, 0o700)
        run(
            [which("solana-keygen") or "solana-keygen", "new", "--silent", "--no-bip39-passphrase", "-o", str(ctx.buyer_keypair)],
            timeout=60,
            what="solana-keygen new (buyer)",
        )
        os.chmod(ctx.buyer_keypair, 0o600)
    output = run(
        [which("solana-keygen") or "solana-keygen", "pubkey", str(ctx.buyer_keypair)],
        timeout=30,
        what="solana-keygen pubkey (buyer)",
    )
    ctx.cache["buyer"] = output.strip().splitlines()[-1].strip()
    return ctx.cache["buyer"]


def token_account_for(ctx: Context, mint: str, owner: str, *, create: bool) -> str:
    """The associated token account for (owner, mint), derived by the toolchain, not here."""
    address = derive_address(
        ctx,
        ASSOCIATED_TOKEN_PROGRAM,
        f"pubkey:{owner}",
        f"pubkey:{TOKEN_2022_PROGRAM}",
        f"pubkey:{mint}",
    )
    if create and not account_exists(ctx.rpc_url, address):
        try:
            run(
                spl(ctx, "create-account", mint, "--owner", owner),
                timeout=BOUND_TOKEN,
                what="spl-token create-account",
            )
        except PublishError:
            # The same stale negative as everywhere else: if the account is there now, this
            # "failure" is the account already existing, and the step is done.
            if not wait_for_account(ctx.rpc_url, address):
                raise
            ctx.say(f"  token account {address} for {owner} was already there; the read before it was stale")
        else:
            ctx.say(f"  token account {address} for {owner}")
    return address


def step_wire(ctx: Context, mint: str, program_id: str) -> tuple[str, str]:
    if ctx.dry_run and (mint.startswith("<") or program_id.startswith("<")):
        ctx.plan(f"wire: ['extra-account-metas', mint] and ['record', mint] PDAs of {program_id} (skipped if they exist)")
        return "<record>", "<extra-account-metas>"
    record = derive_address(ctx, program_id, "string:record", f"pubkey:{mint}")
    extra_metas = derive_address(ctx, program_id, "string:extra-account-metas", f"pubkey:{mint}")
    for key, derived in (("record", record), ("extraMetas", extra_metas)):
        recorded = ctx.recorded(key)
        if recorded and recorded != derived:
            raise PublishError(
                f"the toolchain derives {key} {derived} and the resume file records {recorded}; the program "
                f"id or the mint changed under this run, so it will not reuse an address it cannot re-derive"
            )
        ctx.note(key, derived)
    if ctx.dry_run:
        ctx.plan(f"wire: extra-account-metas {extra_metas} and record {record} (skipped if they exist)")
        return record, extra_metas
    if account_exists(ctx.rpc_url, extra_metas) and account_exists(ctx.rpc_url, record):
        ctx.say(f"wire: {extra_metas} and {record} already exist")
        return record, extra_metas
    if not account_exists(ctx.rpc_url, extra_metas):
        try:
            send_instructions(
                ctx,
                [instruction_init_extra_metas(payer=payer_pubkey(ctx), mint=mint, extra_metas=extra_metas, record=record, program_id=program_id)],
                what="initialise extra-account-metas",
            )
        except PublishError:
            if not wait_for_account(ctx.rpc_url, extra_metas):
                raise
            ctx.say(f"  {extra_metas} was already initialised; the read before it was stale")
    if not account_exists(ctx.rpc_url, record):
        try:
            send_instructions(
                ctx,
                [instruction_init_record(payer=payer_pubkey(ctx), mint=mint, record=record, program_id=program_id, face=FACE_LAMPORTS, cap_bps=CAP_BPS)],
                what=f"initialise record (face {FACE_LAMPORTS}, cap {CAP_BPS} bps)",
            )
        except PublishError:
            if not wait_for_account(ctx.rpc_url, record):
                raise
            ctx.say(f"  {record} was already initialised; the read before it was stale")
    return record, extra_metas


def step_ticket(ctx: Context, mint: str, authority_ata: str, buyer_ata: str) -> None:
    """Two tickets: one for the admitted sale and one for the refused one.

    The refused transfer must be refused by *the cap*, not by an empty account -- the first run
    of this script minted one, moved it, and then produced `Custom: 1` (Token-2022
    InsufficientFunds) instead of the hook's 6010.

    The count that matters is the two accounts together, not the seller's alone: after the
    at-cap transfer has moved one ticket, the seller holds one, and asking the seller alone
    would mint a third ticket on every rerun and break the pair's own arithmetic.
    """
    if ctx.dry_run:
        ctx.plan(f"ticket: spl-token mint {mint} {TICKETS_NEEDED} {authority_ata}")
        return
    held = token_balance(ctx, authority_ata) + token_balance(ctx, buyer_ata)
    if held >= TICKETS_NEEDED:
        ctx.say(f"ticket: {held} already minted across the seller and the buyer")
        ctx.note("ticketsMinted", held)
        return
    need = TICKETS_NEEDED - held
    settled(
        lambda: run(
            spl(ctx, "mint", mint, str(need), authority_ata),
            timeout=BOUND_TOKEN,
            what="spl-token mint",
        ),
        what="spl-token mint",
        log=ctx.say,
    )
    ctx.say(f"ticket: {need} minted to {authority_ata} ({held} already existed)")
    ctx.note("ticketsMinted", held + need)


def token_balance(ctx: Context, address: str) -> int:
    """How many tickets an account holds. "Not visible yet" is waited for, never read as 0.

    Reading 0 for an account that exists is the expensive mistake in this file: the ticket step
    compares that number against what the pair needs, so a stale 0 mints more tickets, and a
    minted ticket cannot be taken back. Two waits, because the two readers lag differently: the
    RPC sees the account, then the CLI sees it a second later.
    """
    if not wait_for_account(ctx.rpc_url, address):
        raise PublishError(
            f"{address} is not on the cluster, so its balance cannot be read; the token account should "
            f"have been created before anything was asked about it"
        )
    output = settled(
        lambda: run(
            spl(ctx, "balance", "--address", address, "--output", "json"),
            timeout=60,
            what="spl-token balance",
        ),
        what="spl-token balance",
        log=ctx.say,
    )
    try:
        return int(json.loads(output).get("amount", 0))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise PublishError(f"spl-token balance printed something unexpected: {output.strip()[:120]}") from exc


def step_memo(ctx: Context, quote: dict, buyer: str) -> dict:
    """One transaction carrying `ticketpath:quote:<id>:<hash>`, read back from the cluster.

    Reused when a previous run already landed it: the resume file first, then the artefact, and
    either one is re-read from the cluster with the memo text checked before it is trusted. The
    memo is only reusable for the quote it commits to, so a changed quote sends a new one.

    Both paths then check the program the memo landed under against the per-cluster table, so a
    resumed run is held to the same claim as a fresh one.
    """
    recorded = ctx.recorded("memo") or {}
    candidates = []
    if recorded.get("signature") and recorded.get("quoteHash") == quote["quoteHash"]:
        candidates.append(recorded["signature"])
    artefact = read_artefact(ctx.out) or {}
    if artefact.get("signature") and artefact.get("memoText") == quote["memoText"]:
        candidates.append(artefact["signature"])
    for signature in candidates:
        try:
            details = transaction_details(ctx.rpc_url, signature, attempts=2, memo=quote["memoText"])
        except PublishError:
            continue
        if quote["memoText"] not in details["memos"]:
            continue
        assert_memo_program(details, ctx.cluster, memo=quote["memoText"])
        ctx.say(f"memo: reusing {signature} (slot {details['slot']})")
        ctx.note("memo", {"signature": signature, "slot": details["slot"], "quoteHash": quote["quoteHash"]})
        return details
    if ctx.dry_run:
        ctx.plan(
            f"memo: solana transfer {buyer} 1 --with-memo {quote['memoText']}, on the program "
            f"{chain_client.memo_program_id(ctx.cluster)} that this repository names for {ctx.cluster}"
        )
        return {"signature": "<memo signature>", "slot": 0, "blockTime": 0, "err": None, "memos": [quote["memoText"]]}
    output = settled(
        lambda: solana(
            ctx,
            "transfer", buyer, "1",
            "--from", str(ctx.keypair),
            "--with-memo", quote["memoText"],
            "--allow-unfunded-recipient",
            timeout=BOUND_TOKEN,
        ),
        what="solana transfer (memo)",
        log=ctx.say,
    )
    signature = last_base58(output)
    if not signature:
        raise PublishError(f"solana transfer printed no signature:\n{output[-400:]}")
    status = confirm(ctx.rpc_url, signature)
    if not status["ok"]:
        raise PublishError(f"the memo transaction failed: {status['err']}")
    details = transaction_details(ctx.rpc_url, signature, memo=quote["memoText"])
    if quote["memoText"] not in details["memos"]:
        raise PublishError("the transaction landed but the chain does not carry the memo text we sent")
    assert_memo_program(details, ctx.cluster, memo=quote["memoText"])
    ctx.note("memo", {"signature": signature, "slot": details["slot"], "quoteHash": quote["quoteHash"]})
    ctx.say(f"memo: {signature} (slot {details['slot']}, block time {details['blockTime']})")
    ctx.say(f"  {quote['memoText']}")
    return details


def step_transfer(
    ctx: Context,
    *,
    leg: str,
    mint: str,
    authority_ata: str,
    buyer_ata: str,
    price: int,
    expect_failure: bool,
) -> tuple[dict, bool]:
    """Stage a price, attempt the transfer, and report what the chain did with it.

    Both legs take the same path and differ only in the staged price, because a boundary shown
    by two different mechanisms is not a boundary.

    Returns the record and whether this run is the one that sent it. A leg a previous run
    already sent is re-read from the cluster instead of repeated: a transfer moves a ticket,
    so repeating one is not a retry, it is a second sale.

    Three states are distinguished, and they are the whole point of the file:

      * **recorded** -- the signature is in the resume file, so the cluster decides whether it
        still says what it said, and nothing is sent;
      * **pending** -- sent at some point and never recorded (the run died in between), so the
        cluster is asked whether it landed before anything is resent;
      * **nothing** -- send it.
    """
    label = "refused over cap" if expect_failure else "accepted at cap"
    program_id = ctx.program_id or program_id_for(ctx)
    if ctx.dry_run:
        ctx.plan(f"transfer ({label}): stage {price} lamports, then transfer 1 ticket with the preflight check skipped")
        return {"signature": f"<{label}>", "slot": 0, "blockTime": 0, "priceLamports": price, "error": None, "explorer": None}, False

    recorded = ctx.recorded("transfers") or {}
    if leg in recorded:
        reused = reuse_transfer(ctx, recorded[leg], price=price, expect_failure=expect_failure, label=label)
        if reused is not None:
            return reused, False

    pending = ctx.progress.pending(leg) if ctx.progress is not None else None
    if pending and pending.get("signature"):
        recovered = recover_signature(
            ctx.rpc_url, pending["signature"], blockhash=pending.get("blockhash")
        )
        if recovered["state"] == "landed":
            ctx.say(f"  {label}: {pending['signature']} had already landed; recording it instead of resending")
            detail = transfer_record(ctx, pending["signature"], recovered, price=price, expect_failure=expect_failure, label=label)
            ctx.save_leg(leg, detail)
            ctx.clear_pending(leg)
            return detail, False
        ctx.say(f"  {label}: {pending['signature']} never landed (its blockhash is dead); sending it once")
        ctx.clear_pending(leg)

    send_instructions(
        ctx,
        [instruction_set_pending_price(record=ctx.cache["record"], program_id=program_id, price=price)],
        what=f"stage {price} lamports",
    )
    signature, status = send_instructions(
        ctx,
        [
            instruction_transfer_checked(
                source=authority_ata,
                mint=mint,
                destination=buyer_ata,
                authority=payer_pubkey(ctx),
                record=ctx.cache["record"],
                hook_program=program_id,
                extra_metas=ctx.cache["extra_metas"],
            )
        ],
        what=f"transfer {label}",
        skip_preflight=True,
        allow_failure=True,
        pending_key=leg,
    )
    ctx.fault(f"transfer.{leg}.sent")
    detail = transfer_record(ctx, signature, status, price=price, expect_failure=expect_failure, label=label)
    ctx.save_leg(leg, detail)
    ctx.clear_pending(leg)
    return detail, True


def transfer_record(ctx: Context, signature: str, status: dict, *, price: int, expect_failure: bool, label: str) -> dict:
    """One leg of the boundary, in the shape the artefact carries, with its own assertions."""
    details = transaction_details(ctx.rpc_url, signature)
    if expect_failure:
        if status["ok"]:
            raise PublishError(f"the over-cap transfer was ADMITTED, which is the bug this run exists to catch: {signature}")
        ctx.say(f"  REFUSED {describe_error(status['err'])}")
    elif not status["ok"]:
        raise PublishError(f"the at-cap transfer was refused: {status['err']} ({signature})")
    return {
        "signature": signature,
        "slot": details["slot"],
        "blockTime": details["blockTime"],
        "priceLamports": price,
        "error": describe_error(status["err"]) if status["err"] else None,
        "explorer": explorer_url("tx", signature, ctx.cluster),
    }


def reuse_transfer(ctx: Context, recorded: dict, *, price: int, expect_failure: bool, label: str) -> dict | None:
    """A leg a previous run recorded: believed only after the cluster agrees with it.

    The short window is deliberate. The record is written *after* a confirmation, so on the
    cluster that made it the signature is in the transaction history; a signature the cluster
    does not know within a few seconds is a different cluster (a fresh rehearsal ledger), and
    that is the one case where sending again is the right answer.
    """
    if recorded.get("priceLamports") != price:
        raise PublishError(
            f"the recorded {label} transfer was staged at {recorded.get('priceLamports')} lamports and this run "
            f"stages {price}; the cap or the face changed, so the recorded boundary is not this boundary"
        )
    try:
        status = confirm(ctx.rpc_url, recorded["signature"], timeout=15.0)
    except PublishError:
        return None
    detail = transfer_record(ctx, recorded["signature"], status, price=price, expect_failure=expect_failure, label=label)
    ctx.say(f"  {label}: reusing {recorded['signature']} from an earlier run (slot {detail['slot']})")
    return detail


TOKEN_INSTRUCTION_TRANSFER_CHECKED = 12


def instruction_transfer_checked(
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
) -> Instruction:
    """The transfer spl-token builds for a hooked mint, byte for byte.

    Accounts `[source, mint, destination, authority, record, hook program, extra-account-metas]`
    and data `[12, amount u64 little-endian, decimals]` were read back from a landed
   
`spl-token transfer` on a local validator, not guessed: findings 18 F4 records the four
    wrong orders that came before it. `tests/test_devnet_publish.py` pins the data bytes against
    that sample. It is built here rather than by the CLI because `spl-token` has no
    `--skip-preflight`, and a refused transfer sent through the CLI dies in simulation with no
    signature to show.
    """
    return Instruction(
        program_id=TOKEN_2022_PROGRAM,
        accounts=(
            AccountMeta(source, False, True),
            AccountMeta(mint, False, False),
            AccountMeta(destination, False, True),
            AccountMeta(authority, True, False),
            AccountMeta(record, False, False),
            AccountMeta(hook_program, False, False),
            AccountMeta(extra_metas, False, False),
        ),
        data=bytes([TOKEN_INSTRUCTION_TRANSFER_CHECKED]) + amount.to_bytes(8, "little") + bytes([decimals]),
    )


def verify_balances(
    ctx: Context, *, authority_ata: str, buyer_ata: str, before: tuple[int, int] | None, at_cap_sent: bool
) -> None:
    """One ticket moved, one did not. The refusal's own signature says why; this says it held.

    Relative to the balances the pair started from, which the resume file keeps, so a rerun that
    reuses a leg still checks the same property instead of an absolute count. `before` is None
    when this run never saw the pair start -- the at-cap transfer was already recorded -- and
    then the live balances are checked against the record that run left, nothing more.
    """
    seller = token_balance(ctx, authority_ata)
    buyer = token_balance(ctx, buyer_ata)
    was = "not seen" if before is None else f"was {before[0]}, {before[1]}"
    ctx.say(f"  after: seller {seller}, buyer {buyer} ({was})")
    recorded_after = ctx.recorded("balancesAfter") or {}
    recorded_pair = (recorded_after.get("authority"), recorded_after.get("buyer"))
    if before is None:
        if recorded_after and recorded_pair != (seller, buyer):
            raise PublishError(
                f"the at-cap transfer was recorded by an earlier run and these balances ({seller}, {buyer}) are "
                f"not the {recorded_pair} it left, so something else has moved these tickets since. This run will "
                f"not record a pair it cannot vouch for."
            )
        if recorded_after:
            ctx.say("  the at-cap leg predates this run; these are the balances it left")
        else:
            ctx.say(
                "  the at-cap leg predates this run and no starting pair was recorded (the resume file was "
                "restarted), so the movement cannot be re-derived here; the pair's own confirmations are what "
                "the artefact rests on"
            )
        return
    if (seller, buyer) != (before[0] - 1, before[1] + 1):
        raise PublishError(
            f"the balances moved the wrong way: seller {seller} and buyer {buyer}, after {before[0]} "
            f"and {before[1]}; exactly one ticket should have crossed, so the refused transfer moved one"
        )
    if not at_cap_sent:
        ctx.say("  the at-cap leg was recorded by an earlier run; the movement still matches the pair's own starting point")


def starting_balances(
    ctx: Context, *, authority_ata: str, buyer_ata: str, at_cap_recorded: bool
) -> tuple[int, int] | None:
    """The balances the boundary pair starts from, recorded once and reused by every rerun.

    Recorded before the first transfer and never overwritten, so a rerun that reuses the at-cap
    leg reads the same starting pair. When the at-cap leg is already recorded and no starting
    pair was ever written, the pair predates this run and no "before" exists to read: it says
    so instead of inventing one from the balances the pair already moved.
    """
    recorded = ctx.recorded("balancesBefore") or {}
    if isinstance(recorded.get("authority"), int) and isinstance(recorded.get("buyer"), int):
        return recorded["authority"], recorded["buyer"]
    if at_cap_recorded:
        return None
    current = (token_balance(ctx, authority_ata), token_balance(ctx, buyer_ata))
    ctx.note("balancesBefore", {"authority": current[0], "buyer": current[1]})
    return current


def seed_from_artefact(ctx: Context) -> None:
    """Take the public facts a finished artefact records into the resume file.

    `--restart` (or a resume file someone deleted) must not turn a completed run into one that
    resends its transfers: the artefact names the mint, the memo and both legs, which are
    exactly what the resume file would have held. Only an artefact for *this* cluster is used,
    because a signature from another one cannot be reused.
    """
    if ctx.progress is None or ctx.dry_run:
        return
    record = read_artefact(ctx.out)
    if not record or record.get("cluster") != ctx.cluster:
        return
    if record.get("mint") and not ctx.recorded("mint"):
        ctx.progress.put("mint", record["mint"])
        ctx.progress.put("mintMetadata", True)
    if record.get("signature") and not ctx.recorded("memo"):
        ctx.progress.put(
            "memo", {"signature": record["signature"], "slot": record.get("slot"), "quoteHash": record.get("quoteHash")}
        )
    known = ctx.recorded("transfers") or {}
    for leg, detail in (record.get("transfers") or {}).items():
        if leg in known or not isinstance(detail, dict):
            continue
        ctx.progress.put_leg(leg, {name: detail.get(name) for name in TRANSFER_FIELDS})
    ctx.say(f"resume: took {', '.join(sorted(set(record.get('transfers') or {}) & {'acceptedAtCap', 'refusedOverCap'})) or 'nothing'} from {ctx.out.name}")


def describe_error(err) -> str:
    """The design's own name for a program error, printed beside the number."""
    if err is None:
        return "no error"
    code = None
    if isinstance(err, dict):
        detail = err.get("InstructionError")
        if isinstance(detail, list) and len(detail) == 2 and isinstance(detail[1], dict):
            code = detail[1].get("Custom")
    if isinstance(code, int):
        name = {6008: "E_AMOUNT_NOT_ONE", 6009: "E_TRANSFER_NOT_STAGED", 6010: "E_CAP_EXCEEDED", 6013: "E_TICKET_INVALID"}.get(code, "")
        return f"custom program error: 0x{code:x} ({code}{' ' + name if name else ''})"
    return json.dumps(err, sort_keys=True)


# -- main --------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="tools/devnet_publish.py",
        description="Deploy the cap-check hook to a cluster, commit the console's quote, prove the cap boundary and record the result.",
        epilog="Reads the keypair path from TP_DEVNET_KEYPAIR; never opens the file. Nothing is pushed and nothing is published.",
    )
    parser.add_argument("--local", action="store_true", help="rehearse on a local validator this script starts and kills (writes records/devnet-artefacts.local.json)")
    parser.add_argument("--dry-run", action="store_true", help="print the plan and touch nothing: no build, no deploy, no signature, no file")
    parser.add_argument("--ledger", default=None, help="with --local, keep the ledger here and do not reset it, so a second run exercises the idempotent path")
    parser.add_argument("--cluster", choices=sorted(CLUSTER_URLS), default=None, help="cluster to publish to (default devnet; ignored with --local)")
    parser.add_argument("--rpc-url", default=None, help="override the RPC endpoint, for a validator you started yourself")
    parser.add_argument("--keypair", default=None, help="authority keypair path (default $TP_DEVNET_KEYPAIR or ~/.config/ticketpath-devnet/authority.json)")
    parser.add_argument("--buyer-keypair", default=None, help="where the demo buyer's throwaway keypair lives (default beside the authority)")
    parser.add_argument("--program-id", default=None, help="deploy to this program id instead of the one target/deploy holds")
    parser.add_argument("--out", default=None, help="artefact path (default records/devnet-artefacts.json, or .local.json with --local)")
    parser.add_argument("--min-balance", type=float, default=None, help="SOL the authority must hold before anything is sent (default 2)")
    parser.add_argument("--progress", default=None, help="resume file (default records/devnet-progress.json, or .local.json with --local); local and git-ignored")
    parser.add_argument("--restart", action="store_true", help="forget the resume file and start at the first step; the cluster is not touched")
    parser.add_argument("--mint-keypair", default=None, help="keypair whose address the mint gets (default beside the authority keypair)")
    parser.add_argument("--inject", action="append", default=[], metavar="SPEC", help="rehearsal only, makes a run die on purpose: after:<step> or rpc:<method>:<count>")
    return parser.parse_args(argv)


def build_context(args: argparse.Namespace) -> Context:
    keypair = Path(args.keypair or os.environ.get("TP_DEVNET_KEYPAIR") or "~/.config/ticketpath-devnet/authority.json").expanduser()
    buyer = Path(args.buyer_keypair).expanduser() if args.buyer_keypair else keypair.parent / "buyer.json"
    cluster = "localnet" if args.local else (args.cluster or "devnet")
    if args.local:
        out = Path(args.out).expanduser() if args.out else LOCAL_ARTEFACT
    else:
        out = Path(args.out).expanduser() if args.out else DEVNET_ARTEFACT
    rpc_url = args.rpc_url or CLUSTER_URLS.get(cluster, "http://127.0.0.1:8899")
    progress_path = Path(args.progress).expanduser() if args.progress else (LOCAL_PROGRESS if args.local else DEVNET_PROGRESS)
    progress = Progress(progress_path, cluster=cluster, writable=not args.dry_run)
    if not args.dry_run:
        if args.restart:
            progress.clear()
        progress.load()
    try:
        FAULTS.arm(args.inject)
    except ValueError as exc:
        raise ValueError(str(exc)) from exc
    return Context(
        ledger=Path(args.ledger).expanduser() if args.ledger else None,
        cluster=cluster,
        rpc_url=rpc_url,
        keypair=keypair,
        buyer_keypair=buyer,
        out=out,
        dry_run=args.dry_run,
        min_lamports=int(round((args.min_balance if args.min_balance is not None else MIN_BALANCE_LAMPORTS / 1e9) * 1e9)),
        program_id=args.program_id,
        mint_keypair_path=Path(args.mint_keypair).expanduser() if args.mint_keypair else None,
        progress=progress,
    )


def publish(ctx: Context) -> int:
    started = time.monotonic()
    ctx.say(f"cluster: {ctx.cluster} ({ctx.rpc_url})")
    ctx.say(f"artefact: {ctx.out.relative_to(REPO_ROOT) if ctx.out.is_relative_to(REPO_ROOT) else ctx.out}")

    step_preflight(ctx)
    seed_from_artefact(ctx)
    if ctx.dry_run and ctx.cluster != "localnet":
        ctx.plan(f"balance: needs at least {ctx.min_lamports / 1e9:.2f} SOL and a funded authority")
    elif ctx.dry_run:
        ctx.plan(f"validator: would start solana-test-validator on a free port with Token-2022 and Memo cloned from devnet, and kill it on exit")
        ctx.plan(f"balance: would fund the local authority from the validator's own faucet (needs {ctx.min_lamports / 1e9:.2f} SOL)")
    else:
        if ctx.cluster == "localnet" and ctx.validator is None:
            ledger = ctx.ledger or (Path(tempfile.gettempdir()) / f"ticketpath-devnet-ledger-{os.getpid()}")
            port = free_port()
            ctx.validator = LocalValidator(
                ledger=ledger,
                port=port,
                faucet_port=free_port(),
                reset=ctx.ledger is None,
                # Funded at genesis, so a rehearsal needs no faucet call at all. The faucet is
                # still enabled in `step_balance` as the fallback for a ledger that predates it.
                fund=payer_pubkey(ctx),
            )
            ctx.say(f"validator: starting solana-test-validator on 127.0.0.1:{port}, ledger {ledger}")
            ctx.validator.start()
            ctx.rpc_url = ctx.validator.rpc_url
            ctx.cache.pop("config", None)
        step_balance(ctx)

    step_build(ctx)
    program_id = program_id_for(ctx) if PROGRAM_KEYPAIR.exists() or ctx.program_id else "<program id>"
    ctx.say(f"program: {program_id}")
    ctx.note("programId", None if program_id.startswith("<") else program_id)
    step_deploy(ctx, program_id)
    ctx.fault("deploy")
    mint = step_mint(ctx, program_id)
    ctx.fault("mint")
    quote = console_quote()
    ctx.say(f"quote: {quote['quoteId']} {quote['quoteHash'][:16]}… recommended {quote['recommendedLamports']:,} lamports at {quote['asOf']}")
    authority_ata, buyer, buyer_ata = step_accounts(ctx, mint)
    ctx.fault("accounts")
    record, extra_metas = step_wire(ctx, mint, program_id)
    ctx.cache["record"] = record
    ctx.cache["extra_metas"] = extra_metas
    ctx.fault("wire")
    step_ticket(ctx, mint, authority_ata, buyer_ata)
    ctx.fault("ticket")
    memo = step_memo(ctx, quote, buyer)
    ctx.fault("memo")
    if ctx.dry_run:
        ctx.plan(f"transfer (accepted at cap): stage {ACCEPTED_PRICE_LAMPORTS} lamports, then spl-token transfer 1")
        ctx.plan(f"transfer (refused over cap): stage {REFUSED_PRICE_LAMPORTS} lamports, then spl-token transfer 1 --skip-preflight")
        ctx.say(f"dry run: {time.monotonic() - started:.1f}s, nothing built, signed, written or deployed")
        return EXIT_OK

    balances_before = starting_balances(
        ctx,
        authority_ata=authority_ata,
        buyer_ata=buyer_ata,
        at_cap_recorded="acceptedAtCap" in (ctx.recorded("transfers") or {}),
    )
    accepted, accepted_sent = step_transfer(
        ctx, leg="acceptedAtCap", mint=mint, authority_ata=authority_ata, buyer_ata=buyer_ata,
        price=ACCEPTED_PRICE_LAMPORTS, expect_failure=False,
    )
    ctx.fault("transfer.acceptedAtCap")
    refused, _ = step_transfer(
        ctx, leg="refusedOverCap", mint=mint, authority_ata=authority_ata, buyer_ata=buyer_ata,
        price=REFUSED_PRICE_LAMPORTS, expect_failure=True,
    )
    ctx.fault("transfer.refusedOverCap")
    verify_balances(
        ctx, authority_ata=authority_ata, buyer_ata=buyer_ata, before=balances_before, at_cap_sent=accepted_sent
    )
    ctx.note(
        "balancesAfter",
        {"authority": token_balance(ctx, authority_ata), "buyer": token_balance(ctx, buyer_ata)},
    )

    record_doc = build_artefact(
        cluster=ctx.cluster,
        rpc_url=ctx.rpc_url,
        quote=quote,
        memo=memo,
        mint=mint,
        program_id=program_id,
        transfers={"acceptedAtCap": accepted, "refusedOverCap": refused},
    )
    write_artefact(ctx.out, record_doc)
    ctx.note("completedAt", now_iso())
    ctx.say("")
    ctx.say(f"wrote {ctx.out.relative_to(REPO_ROOT) if ctx.out.is_relative_to(REPO_ROOT) else ctx.out}")
    for line in summary_lines(record_doc):
        ctx.say(line)
    ctx.say(f"done in {time.monotonic() - started:.1f}s")
    if ctx.cluster != "devnet":
        ctx.say("this is a local rehearsal: cluster 'localnet', no explorer links, and it must never be committed as devnet")
    return EXIT_OK


def summary_lines(record: dict) -> list[str]:
    """Public values only: the same fields the artefact is allowed to carry."""
    lines = [
        f"cluster     {record['cluster']}",
        f"program     {record['programId']}",
        f"mint        {record['mint']}",
        f"memo        {record['signature']} (slot {record['slot']}, block time {record['blockTime']})",
        f"quote       {record['quoteId']} hash {record['quoteHash']}",
        f"memo prog   {record.get('memoProgram') or 'not recorded'}",
    ]
    for leg, label in (("acceptedAtCap", "at cap  "), ("refusedOverCap", "over cap")):
        detail = record["transfers"].get(leg) or {}
        suffix = detail.get("error") or "admitted"
        lines.append(f"transfer    {label} {detail.get('signature')} (slot {detail.get('slot')}) {suffix}")
    if record["explorer"].get("transaction"):
        lines.append(f"explorer    {record['explorer']['transaction']}")
    return lines


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        ctx = build_context(args)
    except (ValueError, OSError) as exc:
        sys.stderr.write(f"devnet_publish: {exc}\n")
        return EXIT_FAIL
    try:
        return publish(ctx)
    except Refused as exc:
        sys.stderr.write(f"\nREFUSED: {exc}\n")
        return EXIT_REFUSED
    except PublishError as exc:
        sys.stderr.write(f"\nFAILED: {exc}\n")
        return EXIT_FAIL
    except KeyboardInterrupt:
        sys.stderr.write("\ninterrupted\n")
        return 130
    finally:
        if ctx.validator:
            ctx.validator.stop()


if __name__ == "__main__":
    raise SystemExit(main())

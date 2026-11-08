#!/usr/bin/env python3
"""Prove the artist fee is paid atomically at checkout, on a real local Solana validator.

This is a verification tool, not a product feature. It boots a throw-away
`solana-test-validator` on loopback, deploys the **existing** prebuilt
`programs/cap_hook/target/deploy/cap_hook.so` to it (never rebuilt here: its sha256 is
asserted first), creates the mints and records the sale needs, and then drives eight legs
through real transactions, reading every number back off the cluster.

The sale it is proving is the one `market_swarm/artist_fee.py` builds: three instructions in
one atomic transaction — `cap_hook` `SetPendingPrice`, a System `Transfer` of the seller's
lamports to the artist, and a Token-2022 `TransferChecked` whose hook checks the staged
price. Two signers, because the record's authority is the mint's authority and
`checked_record_for_write` requires its signature on the stage.

What this tool adds over the module's own unit tests is the chain: exact lamport deltas from
`getBalance`, each transaction's own `meta.fee`, the two token balances, the 70-byte record
read back and decoded here, and the refusals with their real signatures. A leg whose
assertion does not hold fails the run — nothing is weakened to make it green.

Two things are deliberately not touched. There is no `--url devnet` in this file, no faucet,
no airdrop and no `--clone`: Token-2022 is in the validator's own genesis on agave 4.3.2, so
nothing has to be fetched. And the program is an input: this file never edits it and never
builds it.

Keys are generated fresh every run, under `tmp/artist-fee/keys/` at 0600, so the mint ids
differ between runs. The four properties the legs assert do not.

Everything is bounded: `--deadline` (default 600s) covers the whole run, every child carries
a subprocess timeout, the deadline is re-checked between legs, the validator is killed on
every exit path (atexit plus SIGINT/SIGTERM/SIGHUP) and its ledger is removed.
"""

from __future__ import annotations

import argparse
import atexit
import base64
import fcntl
import hashlib
import json
import os
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _entry in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import devnet_publish as dp  # noqa: E402
from market_swarm import artist_fee as af  # noqa: E402
from market_swarm import gateway as gw  # noqa: E402

# -- what exists, and is read rather than written -----------------------------

CRATE = REPO_ROOT / "programs" / "cap_hook"
SO_PATH = CRATE / "target" / "deploy" / "cap_hook.so"
#: `tools/publish_v2.py`'s keypair, not the frozen devnet one: v2 must never be deployed under
#: the id the proven v1 build was published at, and `devnet_publish.refuse_frozen_devnet_upgrade`
#: exists to make that a hard error rather than a convention. The id is therefore new per build.
PROGRAM_KEYPAIR = CRATE / "target" / "deploy" / "v2-keypair.json"
ERROR_SOURCE = CRATE / "src" / "error.rs"

#: The v2 build this proof is about. Asserted, never rebuilt.
SO_SHA256 = "de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac"

WORK = REPO_ROOT / "tmp" / "artist-fee"
#: Outside WORK on purpose: WORK is wiped at boot, and two runs must not both decide they are
#: the only one.
LOCK_PATH = REPO_ROOT / "tmp" / "artist-fee.lock"
KEYS = WORK / "keys"
LEDGER = WORK / "ledger"
MEASUREMENTS = WORK / "measurements.json"
REPORT = WORK / "REPORT.md"

# -- the program's constants, transcribed from lib.rs/state.rs and asserted at runtime --

TAG_INIT_EXTRA_METAS = 0
TAG_INIT_RECORD = 1
TAG_SET_PENDING_PRICE = 2

POLICY_CAPPED = 0
#: `TicketRecord::LEN`: 8 + 2 + 8 + 1 + 8 + 2 + 1 + 8 + 32. Decoded by hand below.
RECORD_LEN = 70

# -- the sale's numbers: the brief's worked pair -------------------------------------

FACE = 1_000_000_000
CAP_BPS = 2_500
BAND_LOW = 0
JURISDICTION = "GB"
FEE_BPS = 500

#: The cap predicate is inclusive and in `u128` on chain, so `face * (10_000 + cap) / 10_000`
#: is the largest admissible staged price and one lamport over it must be refused.
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000

#: One mint per seller shape. `sale` carries the legs that must land (legs 1, 3, 4, 5, 6, 8);
#: `underfunded` has its own seller so the fee it cannot pay is genuinely unpayable.
TICKETS_SALE = 8
TICKETS_UNDERFUNDED = 1

#: Funded so it covers a two-signature fee and is nowhere near the 50_000_000 it is asked to
#: pay. The brief says "say, 10_000"; 10_000 is exactly the two-signature fee, which would let
#: the transaction die at the fee charge instead of inside it, and a leg that fails at the door
#: proves nothing about atomicity. 1_000_000 is above the rent-exempt floor for a 0-data
#: account and still four orders of magnitude short of the fee.
SELLER_UNDERFUNDED_LAMPORTS = 1_000_000


class ProofError(RuntimeError):
    """Something in the harness, not in the program. Ends the run non-zero."""


def say(line: str = "") -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fmt(value) -> str:
    """A number as a reader reads it: thousands separated, and no float anywhere."""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)


def ceiling_lamports(*, face_lamports: int, cap_bps: int) -> int:
    """`face * (10_000 + cap_bps) // 10_000`: the largest price the record admits, floored."""
    if face_lamports < 0 or not 0 <= cap_bps <= 65_535:
        raise ValueError(f"face {face_lamports!r} / cap {cap_bps!r} is not a record's inputs")
    return face_lamports * (10_000 + cap_bps) // 10_000


def planned_fees() -> dict[str, int]:
    """The fee each leg expects, computed by the product's own arithmetic.

    Pinned in `tests/test_artist_fee_proof.py` against the numbers the brief states, so a change
    to `fee_lamports` moves this table and fails the test rather than silently moving a leg.
    """
    return {
        "leg1": af.fee_lamports(price_lamports=FACE, fee_bps=FEE_BPS),
        "leg3": af.fee_lamports(price_lamports=CEILING + 1, fee_bps=FEE_BPS),
        "leg4_price_19": af.fee_lamports(price_lamports=19, fee_bps=FEE_BPS),
        "leg4_price_20": af.fee_lamports(price_lamports=20, fee_bps=FEE_BPS),
        "leg5": af.fee_lamports(price_lamports=FACE, fee_bps=10_000),
        "leg6": af.fee_lamports(price_lamports=0, fee_bps=FEE_BPS),
        "leg8_would_be": af.fee_lamports(price_lamports=FACE, fee_bps=FEE_BPS),
    }


# -- the program's own instructions ------------------------------------------
#
# The v2 wire, verbatim from `programs/cap_hook/src/lib.rs`. `dp.instruction_init_record` and
# `dp.instruction_set_pending_price` are the v1 shapes (no `band_low`/`policy`, no authority
# signer) and would be refused by this program; the stage comes from `market_swarm.gateway`,
# which is where the sale path's own unit tests pin it.


def ix_init_extra_metas(*, payer: str, mint: str, extra_metas: str, record: str,
                        program_id: str) -> dp.Instruction:
    """Tag 0: accounts `[payer(s,w), mint, extra_metas(w), system_program]`, data `[0] + record`.

    The 32 bytes are the record the list will resolve. The program re-derives it from the mint
    and ignores the argument (`initialize_extra_account_meta_list`), which is why a wrong value
    here cannot brick a mint; it is still what the wire carries.
    """
    try:
        body = dp.base58.decode(record)
    except ValueError as exc:
        raise ProofError(f"record {record!r} is not base58: {exc}") from exc
    if len(body) != 32:
        raise ProofError(f"record {record!r} decodes to {len(body)} bytes, expected 32")
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(payer, True, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(extra_metas, False, True),
            dp.AccountMeta(dp.SYSTEM_PROGRAM, False, False),
        ),
        data=bytes([TAG_INIT_EXTRA_METAS]) + body,
    )


def ix_init_record(*, payer: str, mint: str, record: str, mint_authority: str,
                   program_id: str, face: int, cap_bps: int, band_low: int,
                   jurisdiction: str, policy: int) -> dp.Instruction:
    """Tag 1: 22 bytes, `[1, face u64, cap_bps u16, band_low u64, jurisdiction [2], policy u8]`.

    `mint_authority` must be the mint's current authority and must sign: the record takes its
    `authority` from that key, and nothing rewrites it afterwards.
    """
    if len(jurisdiction.encode("ascii")) != 2:
        raise ProofError(f"jurisdiction {jurisdiction!r} is not two ASCII bytes")
    data = (
        bytes([TAG_INIT_RECORD])
        + face.to_bytes(8, "little")
        + cap_bps.to_bytes(2, "little")
        + band_low.to_bytes(8, "little")
        + jurisdiction.encode("ascii")
        + bytes([policy])
    )
    if len(data) != 22:
        raise ProofError(f"InitializeRecord data is {len(data)} bytes, the wire is 22")
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


def ix_move(*, source: str, mint: str, destination: str, authority: str, record: str,
            hook_program: str, extra_metas: str, amount: int = 1) -> dp.Instruction:
    """The hooked transfer: 7 accounts, data `[12] + amount u64 le + decimals u8`.

    Same order and same bytes as `dp.instruction_transfer_checked`, with one flag changed: the
    record is **writable**. The rule the runtime enforces is that an account is writable for a
    transaction if any instruction in it says so, and that an inner CPI may not ask for more than
    the outer instruction granted. v2's extra-account-metas list declares the record writable
    (`RECORD_META_WRITABLE = true`, `programs/cap_hook/src/lib.rs`), so Token-2022 asks for a
    writable record when it calls the hook; a message that only ever names the record read-only is
    refused `PrivilegeEscalation` at the Token-2022 instruction and the hook never runs. It does not
    land with the write skipped. Measured by the non-builder review of finding 42, which sent the
    same move with and without a stage in the transaction, and by leg 8b below, which is a move with
    no other instruction in its message.
    """
    if amount != 1:
        raise ProofError(f"amount {amount}: the hook admits one ticket at a time (6008)")
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
        data=bytes([12]) + amount.to_bytes(8, "little") + bytes([0]),
    )

def ix_stage(*, authority: str, record: str, mint: str, program_id: str, price: int) -> dp.Instruction:
    """Tag 2: accounts `[authority (signer), record (writable), mint]`, data `[2] + price u64 le`.

    The v2 shape. `dp.instruction_set_pending_price` is the v1 encoder — one account, no
    authority signer — and `checked_record_for_write` refuses it on a v2 record. This is written
    out rather than delegating to `gw.instruction_set_pending_price_v2` for one measured reason:
    that builder refuses `price == 0` in `_require_price` (1..u64-1, a product rule: a sale at 0
    cannot succeed), and leg 6 has to stage 0 to show the chain's own 6009. The wire is identical
    for every price the gateway accepts, which `tests/test_artist_fee_proof.py` pins against it.
    """
    if isinstance(price, bool) or not isinstance(price, int) or not 0 <= price < 2**64:
        raise ProofError(f"price {price!r} is not a u64 a staged price can hold")
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(authority, True, False),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(mint, False, False),
        ),
        data=bytes([dp.TAG_SET_PENDING_PRICE]) + price.to_bytes(8, "little"),
    )


def resolve_signers(required, keypairs: dict[str, Path]) -> list[tuple[str, Path]]:
    """Pair each required signer with the one keypair path this process holds for it.

    The set has to match exactly. A missing path leaves a required signature empty; an extra
    one writes a signature the message has no slot for. Either is a bug worth a hard error that
    names both sides rather than a guess that produces a transaction nobody can decode.
    """
    missing = [key for key in required if key not in keypairs]
    extra = [key for key in keypairs if key not in required]
    if missing or extra:
        raise ProofError(
            f"signers: this transaction needs exactly [{', '.join(required)}] and the call holds "
            f"[{', '.join(sorted(keypairs))}]; no keypair for {missing or 'nothing'} and a path "
            f"for {extra or 'nothing'} the message does not ask to sign"
        )
    return [(key, keypairs[key]) for key in required]



def decode_record(raw: bytes) -> dict:
    """The 70-byte Borsh `TicketRecord`, decoded by hand so the layout is checked here.

    `face u64 | cap_bps u16 | pending u64 | status u8 | band_low u64 | jurisdiction [u8;2] |
    policy u8 | held_since i64 | authority [32]`. The length is asserted, because
    `try_from_slice` on chain only refuses a wrong size and a decoder that accepted one would
    read a band or a score account as a record.
    """
    if len(raw) != RECORD_LEN:
        raise ProofError(f"record is {len(raw)} bytes, the Borsh width is {RECORD_LEN}")
    return {
        "face_value_lamports": int.from_bytes(raw[0:8], "little"),
        "cap_bps": int.from_bytes(raw[8:10], "little"),
        "pending_price_lamports": int.from_bytes(raw[10:18], "little"),
        "status": raw[18],
        "band_low_lamports": int.from_bytes(raw[19:27], "little"),
        "jurisdiction": raw[27:29].decode("ascii", "replace"),
        "policy": raw[29],
        "held_since_unix": int.from_bytes(raw[30:38], "little", signed=True),
        "authority": dp.base58.encode(raw[38:70]),
        "raw_len": len(raw),
    }


def describe_error(err) -> dict:
    """A transaction error split into what a reader needs: index, code, and the verbatim text.

    The failing instruction index is what turns "the transaction failed" into a claim about
    atomicity: a failure at index 1 happened after index 0 executed, and the runtime rolls a
    failed transaction back whole, so the stage is proven to have been rolled back rather than
    never to have run.
    """
    text = "no error" if err is None else json.dumps(err, sort_keys=True)
    described = {"text": text, "index": None, "code": None, "variant": None}
    if not isinstance(err, dict):
        return described
    detail = err.get("InstructionError")
    if not (isinstance(detail, list) and len(detail) == 2):
        # A transaction-level error (`InsufficientFundsForFee`, `AccountNotFound`) has no index:
        # nothing was executed, so no instruction can be blamed.
        described["variant"] = ";".join(sorted(err))
        return described
    index, why = detail
    described["index"] = index if isinstance(index, int) else None
    if isinstance(why, dict) and "Custom" in why:
        described["code"] = why["Custom"]
        described["variant"] = "Custom"
    else:
        described["variant"] = str(why)
    return described


def assert_loopback(url: str) -> str:
    """Refuse anything that is not this machine's own validator."""
    if not re.match(r"^http://(127\.0\.0\.1|localhost|\[::1\]):\d+$", url or ""):
        raise ProofError(f"refusing to run against {url!r}: this proof only touches loopback")
    return url


# -- reading the chain --------------------------------------------------------


def get_balance(url: str, address: str) -> int:
    """Lamports, at `confirmed`. An account that does not exist reads 0, which is what it holds."""
    result = dp.rpc(url, "getBalance", [address, {"commitment": "confirmed"}])
    return int((result or {}).get("value") or 0)


def token_amount(url: str, account: str) -> int | None:
    """How many whole tokens an account holds, or None when the account is not on the chain.

    The two reads are separate on purpose: `getTokenAccountBalance` on a missing account is an
    RPC error, and an error read as 0 would be a leg passing on an account that was never made.
    """
    info = dp.rpc(url, "getAccountInfo", [account, {"encoding": "base64", "commitment": "confirmed"}])
    if not (info or {}).get("value"):
        return None
    result = dp.rpc(url, "getTokenAccountBalance", [account, {"commitment": "confirmed"}])
    return int(((result or {}).get("value") or {})["amount"])


def read_record(url: str, address: str) -> dict | None:
    """The record account, decoded. None when it is not there, which is a fact worth reporting."""
    result = dp.rpc(url, "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}])
    value = (result or {}).get("value")
    if not value:
        return None
    return decode_record(base64.b64decode(value["data"][0]))


def transaction_meta(url: str, signature: str) -> dict:
    """The landed transaction's metadata: `err`, `fee` and `logMessages`, read from the cluster.

    `getTransaction` can be a slot or two behind a confirmed signature, so absence is waited
    for rather than read as "no such transaction".
    """
    for _ in range(15):
        result = dp.rpc(
            url,
            "getTransaction",
            [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0,
                         "commitment": "confirmed"}],
        )
        if result:
            return result
        time.sleep(0.4)
    raise ProofError(f"getTransaction returned nothing for {signature} after 15 looks")


def load_program_codes(path: Path) -> dict[str, int]:
    """The error numbers out of the program's own `error.rs`, not out of a memory of them."""
    text = path.read_text(encoding="utf-8")
    block = re.search(r"pub enum TicketpathError \{(.*?)\n\}", text, re.S)
    if not block:
        raise ProofError(f"no `pub enum TicketpathError` block in {path}")
    codes = {name: int(value) for name, value in re.findall(r"(\w+)\s*=\s*(\d+)\s*,", block.group(1))}
    for name in ("AmountNotOne", "TransferNotStaged", "CapExceeded", "BelowFloor"):
        if name not in codes:
            raise ProofError(f"the program's error enum no longer defines {name}; this tool is stale")
    return codes


# -- ports and the validator --------------------------------------------------


def free_block(count: int) -> int:
    """`count` consecutive free TCP ports on loopback.

    The validator binds gossip and a dynamic range as well as RPC, and a busy gossip port is a
    hard panic at startup, not a retry. So the whole range is probed here rather than left to
    the default 8000..8009 — which on this host is where a second validator dies.
    """
    def one(port: int) -> bool:
        probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            probe.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False
        finally:
            probe.close()

    for base in range(20000, 60000, count + 1):
        if all(one(port) for port in range(base, base + count)):
            return base
    raise ProofError("no free block of consecutive ports for the validator")


def port_is_closed(port: int) -> bool:
    """True when nothing on loopback is listening on `port` any more."""
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        probe.bind(("127.0.0.1", port))
        return True
    except OSError:
        return False
    finally:
        probe.close()


class LocalCluster(dp.LocalValidator):
    """`dp.LocalValidator` with its startup command replaced, and nothing else.

    The inherited half is the part worth reusing: `stop()` kills the process group (not just the
    parent), waits, escalates to SIGKILL, and removes the ledger; `__init__` registers it with
    `atexit` and with the three signals. A validator that survives the run is the failure mode
    this class exists to prevent, so its teardown is not reimplemented.

    The override is for the same two measured reasons `tools/region_local_proof.py` documents:
    the inherited `start()` clones Token-2022 and the memo program from `--url devnet`, which
    this run must not do and does not need (on agave 4.3.2 the test validator's genesis already
    carries Token-2022 at `TokenzQd…`), and it leaves gossip on 8000, where a second listener on
    this host panics it. Loopback with explicit gossip and dynamic ranges starts in ~2s.
    """

    def __init__(self, *, ledger: Path, port: int, faucet_port: int, gossip_port: int,
                 dynamic_base: int, dynamic_count: int, reset: bool = True,
                 fund: str | None = None):
        super().__init__(ledger=ledger, port=port, faucet_port=faucet_port, reset=reset, fund=fund)
        self.gossip_port = gossip_port
        self.dynamic_base = dynamic_base
        self.dynamic_count = dynamic_count

    def wipe_ledger(self) -> None:
        """Remove the ledger and wait for it to be gone.

        `--reset` does this itself, but a launch that fails part way leaves a half-built RocksDB
        behind and the next attempt then dies on a rename inside it with an error that says
        nothing about the real cause.
        """
        if self.ledger.exists():
            shutil.rmtree(self.ledger, ignore_errors=True)
        for _ in range(20):
            if not self.ledger.exists():
                return
            time.sleep(0.05)

    def start(self) -> None:
        binary = dp.which("solana-test-validator")
        if not binary:
            raise ProofError("solana-test-validator is not on PATH (run from a login shell)")
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        if self.reset:
            self.wipe_ledger()
        command = [
            binary,
            *(["--reset"] if self.reset else []),
            "--quiet",
            "--bind-address", "127.0.0.1",
            "--ledger", str(self.ledger),
            "--rpc-port", str(self.port),
            "--faucet-port", str(self.faucet_port),
            "--gossip-port", str(self.gossip_port),
            "--dynamic-port-range", f"{self.dynamic_base}-{self.dynamic_base + self.dynamic_count - 1}",
            *(["--mint", self.fund] if self.fund else []),
        ]
        env = dict(os.environ)
        env["PATH"] = dp.toolchain_path()
        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            text=True,
            env=env,
        )
        atexit.register(self.stop)
        for signal_name in ("SIGINT", "SIGTERM", "SIGHUP"):
            signal.signal(getattr(signal, signal_name), self._on_signal)
        deadline = time.monotonic() + 120.0
        while time.monotonic() < deadline:
            if self.process.poll() is not None:
                tail = (self.process.stdout.read() or "")[-2000:] if self.process.stdout else ""
                raise ProofError(f"solana-test-validator exited before it answered:\n{tail}")
            try:
                if dp.rpc(self.rpc_url, "getHealth", [], timeout=2, attempts=1) == "ok":
                    return
            except dp.PublishError:
                time.sleep(0.5)
        raise ProofError(f"solana-test-validator did not answer on {self.rpc_url} within 120s")

    def tail(self) -> str:
        if self.process and self.process.stdout and self.process.poll() is not None:
            try:
                return (self.process.stdout.read() or "")[-2000:]
            except Exception:  # noqa: BLE001 - a dead pipe tells us nothing
                return ""
        return ""


# -- one leg's assertions ------------------------------------------------------


class Checks:
    """The assertions of one leg, and the numbers that support them.

    Every check records what it wanted and what it saw, so a failure prints the disagreement
    rather than only the word "failed". `eq` never coerces: the two sides must be the same
    integer, and a `None` on either side is a failure with `None` printed.
    """

    def __init__(self) -> None:
        self.items: list[dict] = []

    def eq(self, name: str, got, want) -> bool:
        ok = got == want and type(got) is type(want)
        self.items.append({"check": name, "got": repr(got), "want": repr(want), "ok": ok})
        return ok

    def true(self, name: str, ok: bool, detail: str = "") -> bool:
        """A yes/no check, with an optional human detail.

        `got` records the detail only when the check FAILED. A detail on a passing check
        ("no matching log line", recorded because there was nothing to quote) reads in
        `measurements.json` as a failure that the `ok: true` beside it does not excuse, and a
        reader diffing one run against the next should not have to resolve that.
        """
        self.items.append({
            "check": name,
            "got": (detail or "false") if not ok else "true",
            "want": "true",
            "ok": bool(ok),
        })
        return bool(ok)

    def failed(self) -> list[dict]:
        return [item for item in self.items if not item["ok"]]


# -- the run -------------------------------------------------------------------


class Proof:
    def __init__(self, *, deadline: float):
        self.started = time.monotonic()
        self.deadline = deadline
        self.validator: LocalCluster | None = None
        self.url = ""
        self.port = 0
        self.program_id = ""
        self.so_sha = ""
        self.codes: dict[str, int] = {}
        self.ctx: dp.Context | None = None
        self.issuer = ""
        self.issuer_key = KEYS / "issuer.json"
        self.artist = ""
        self.artist_key = KEYS / "artist.json"
        self.mints: dict[str, dict] = {}
        self.results: list[dict] = []
        self.snapshots: list[tuple[str, str, dict | None]] = []
        self.leg1_record: dict | None = None
        self.port_closed: bool | None = None
        self.validator_version = "unknown"

    # -- housekeeping ---------------------------------------------------

    def remaining(self) -> float:
        return self.deadline - (time.monotonic() - self.started)

    def check_deadline(self, where: str) -> None:
        if self.remaining() <= 0:
            raise ProofError(f"the {self.deadline:g}s deadline passed before {where}")

    def keygen(self, path: Path) -> str:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            path.unlink()
        dp.run(
            [dp.which("solana-keygen") or "solana-keygen", "new", "--no-bip39-passphrase",
             "--silent", "-o", str(path)],
            timeout=60,
            what=f"solana-keygen new ({path.name})",
        )
        os.chmod(path, 0o600)
        return self.pubkey_of(path)

    def pubkey_of(self, path: Path) -> str:
        out = dp.run(
            [dp.which("solana-keygen") or "solana-keygen", "pubkey", str(path)],
            timeout=30,
            what=f"solana-keygen pubkey ({path.name})",
        )
        return out.strip().splitlines()[-1].strip()

    def spl(self, *args: str) -> str:
        return dp.run(dp.spl(self.ctx, *args), timeout=120, what=f"spl-token {args[0]}")

    def boot(self) -> None:
        self.codes = load_program_codes(ERROR_SOURCE)
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        KEYS.mkdir(parents=True, exist_ok=True)

        self.issuer = self.keygen(self.issuer_key)
        self.artist = self.keygen(self.artist_key)
        # The issuer is funded at genesis (`--mint`) so no faucet call is needed and the run
        # does not depend on the ledger's faucet behaviour.
        # One contiguous block for every port the validator binds: rpc, faucet, gossip and the
        # dynamic range. Probing them separately lets `free_port()` hand back a port inside the
        # block, and a busy gossip port is a hard panic at startup, not a retry.
        base = free_block(34)
        self.port = base
        self.validator = LocalCluster(
            ledger=LEDGER,
            port=base,
            faucet_port=base + 1,
            gossip_port=base + 2,
            dynamic_base=base + 3,
            dynamic_count=31,
            reset=True,
            fund=self.issuer,
        )
        for attempt in (1, 2):
            try:
                self.validator.start()
                break
            except ProofError as exc:
                if attempt == 2:
                    raise ProofError(f"validator would not start after two attempts: {exc}") from exc
                say(f"  validator start attempt {attempt} failed, retrying once: {exc}")
                self.validator.wipe_ledger()
                time.sleep(1.0)
        self.url = assert_loopback(self.validator.rpc_url)

        self.ctx = dp.Context(
            cluster="local",
            rpc_url=self.url,
            keypair=self.issuer_key,
            buyer_keypair=self.issuer_key,
            out=WORK / "out",
        )
        self.ctx.payer = self.issuer
        assert_loopback(self.ctx.rpc_url)

    def deploy(self) -> None:
        self.so_sha = dp.run(["sha256sum", str(SO_PATH)], timeout=30, what="sha256sum (program)").split()[0]
        if self.so_sha != SO_SHA256:
            raise ProofError(
                f"{SO_PATH.relative_to(REPO_ROOT)} is {self.so_sha}, and this proof is about "
                f"{SO_SHA256}. Another run rebuilt it. Not deploying a binary this proof cannot "
                "describe; the tool never rebuilds it either."
            )
        if not PROGRAM_KEYPAIR.exists():
            raise ProofError(f"no program keypair at {PROGRAM_KEYPAIR}")
        self.program_id = self.pubkey_of(PROGRAM_KEYPAIR)
        dp.run(
            [
                dp.which("solana") or "solana",
                "--url", self.url,
                "program", "deploy", str(SO_PATH),
                "--program-id", str(PROGRAM_KEYPAIR),
                "--keypair", str(self.issuer_key),
            ],
            timeout=min(300.0, max(60.0, self.remaining() - 30)),
            what="solana program deploy",
        )
        if not dp.wait_for_account(self.url, self.program_id):
            raise ProofError(f"program {self.program_id} is not visible after deploy")
        account = dp.rpc(self.url, "getAccountInfo", [self.program_id, {"encoding": "base64"}])
        if not ((account or {}).get("value") or {}).get("executable"):
            raise ProofError(f"program {self.program_id} is not executable after deploy")

    def fund(self, address: str, lamports: int, what: str) -> None:
        """Fund from the issuer, through the product's own System-transfer builder."""
        instruction = af.system_transfer_instruction(
            source=self.issuer, destination=address, lamports=lamports
        )
        dp.send_instructions(self.ctx, [instruction], what=what)

    def ata_for(self, *, mint: str, owner: str) -> str:
        """Create the associated token account for `owner` and read its address back.

        The address is read from the chain rather than parsed out of the CLI: `spl-token
        address --verbose` prints three lines and a parser that took the last token would take
        the mint. One account per (mint, owner) is an invariant of the create.
        """
        self.spl("create-account", mint, "--owner", owner)
        result = dp.rpc(
            self.url,
            "getTokenAccountsByOwner",
            [owner, {"mint": mint}, {"encoding": "jsonParsed", "commitment": "confirmed"}],
        )
        accounts = (result or {}).get("value") or []
        if len(accounts) != 1:
            raise ProofError(f"{owner} holds {len(accounts)} accounts for mint {mint}, expected 1")
        return accounts[0]["pubkey"]

    # -- mints and the sale ---------------------------------------------

    def make_mint(self, *, name: str, seller: str, seller_key: Path, tickets: int) -> None:
        """One mint, its record, its extra-metas list, two token accounts and `tickets` tickets."""
        self.check_deadline(f"creating the {name} mint")
        mint_key = KEYS / f"{name}-mint.json"
        mint = self.keygen(mint_key)
        self.spl("create-token", "--decimals", "0", "--transfer-hook", self.program_id, str(mint_key))
        record = dp.derive_address(self.ctx, self.program_id, "string:record", f"pubkey:{mint}")
        extra_metas = dp.derive_address(
            self.ctx, self.program_id, "string:extra-account-metas", f"pubkey:{mint}"
        )

        dp.send_instructions(
            self.ctx,
            [ix_init_extra_metas(payer=self.issuer, mint=mint, extra_metas=extra_metas,
                                 record=record, program_id=self.program_id)],
            what=f"{name}: init extra-account-metas",
        )
        dp.send_instructions(
            self.ctx,
            [ix_init_record(payer=self.issuer, mint=mint, record=record,
                            mint_authority=self.issuer, program_id=self.program_id,
                            face=FACE, cap_bps=CAP_BPS, band_low=BAND_LOW,
                            jurisdiction=JURISDICTION, policy=POLICY_CAPPED)],
            what=f"{name}: init record",
        )
        record_state = read_record(self.url, record)
        if record_state is None:
            raise ProofError(f"{name}: no record at {record} after InitializeRecord")

        buyer = self.keygen(KEYS / f"{name}-buyer.json")
        seller_ata = self.ata_for(mint=mint, owner=seller)
        buyer_ata = self.ata_for(mint=mint, owner=buyer)
        self.spl("mint", mint, str(tickets), seller_ata)

        self.mints[name] = {
            "mint": mint,
            "record": record,
            "extra_metas": extra_metas,
            "seller": seller,
            "seller_key": seller_key,
            "buyer": buyer,
            "seller_ata": seller_ata,
            "buyer_ata": buyer_ata,
            "record_at_birth": record_state,
        }
        say(
            f"  {name}: mint {mint} record {record} tickets {tickets} "
            f"seller {seller} buyer {buyer}"
        )

    def move(self, name: str) -> dp.Instruction:
        spec = self.mints[name]
        return ix_move(
            source=spec["seller_ata"], mint=spec["mint"], destination=spec["buyer_ata"],
            authority=spec["seller"], record=spec["record"], hook_program=self.program_id,
            extra_metas=spec["extra_metas"],
        )

    def stage(self, name: str, price: int) -> dp.Instruction:
        spec = self.mints[name]
        return ix_stage(authority=self.issuer, record=spec["record"], mint=spec["mint"],
                        program_id=self.program_id, price=price)

    def sale(self, name: str, *, price: int, fee_bps: int) -> tuple[dp.Instruction, ...]:
        """`(stage, fee?, move)` from the product's own builder, so the leg tests the checkout."""
        spec = self.mints[name]
        return af.sale_instructions(
            stage=self.stage(name, price), move=self.move(name), seller=spec["seller"],
            artist_wallet=self.artist, price_lamports=price, fee_bps=fee_bps,
        )

    def snapshot(self, name: str) -> dict:
        spec = self.mints[name]
        return {
            "seller_lamports": get_balance(self.url, spec["seller"]),
            "artist_lamports": get_balance(self.url, self.artist),
            "seller_tokens": token_amount(self.url, spec["seller_ata"]),
            "buyer_tokens": token_amount(self.url, spec["buyer_ata"]),
            "record": read_record(self.url, spec["record"]),
        }

    def sign(self, keypair: Path, message: bytes) -> bytes:
        """One signature from a child process. This process never opens the keypair."""
        context = dp.Context(
            cluster="local", rpc_url=self.url, keypair=keypair,
            buyer_keypair=keypair, out=WORK / "out",
        )
        return dp.sign_message(context, message)

    def send(self, *, payer: str, instructions, signers: dict[str, Path], what: str,
             skip_preflight: bool = True, allow_failure: bool = False) -> dict:
        """Compile, sign with exactly the signers the message asks for, send, read back.

        The signer set is parsed out of the compiled message (`gw.signer_keys_from_message`)
        and the two sets must agree exactly: a missing path leaves a required signature empty,
        an extra one writes a signature the message has no slot for, and both are hard errors.
        Signatures are positional, so they are produced in the message's order rather than the
        dict's. Every leg is sent with `skipPreflight`, so a refusal lands as a failed
        transaction with its own signature instead of dying in simulation with none.
        """
        self.check_deadline(what)
        blockhash = dp.rpc(self.url, "getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
        message = dp.compile_message(payer, list(instructions), blockhash)
        required = gw.signer_keys_from_message(message)
        try:
            pairs = resolve_signers(required, signers)
        except ProofError as exc:
            raise ProofError(f"{what}: {exc}") from exc
        signatures = [self.sign(path, message) for _, path in pairs]
        wire = base64.b64encode(dp.build_transaction(message, signatures)).decode("ascii")
        signature = dp.rpc(
            self.url,
            "sendTransaction",
            [wire, {"encoding": "base64", "skipPreflight": skip_preflight,
                    "preflightCommitment": "confirmed"}],
        )
        status = dp.confirm(self.url, signature)
        meta = transaction_meta(self.url, signature)["meta"] or {}
        result = {
            "signature": signature,
            "ok": bool(status.get("ok")),
            "err": meta.get("err"),
            "fee": int(meta.get("fee") or 0),
            "logs": list(meta.get("logMessages") or []),
            "signers": list(required),
            "instructions": len(instructions),
        }
        result["error"] = describe_error(result["err"])
        result["failed_log"] = next(
            (line for line in reversed(result["logs"]) if "failed" in line.lower()), "none"
        )
        if not result["ok"] and not allow_failure:
            raise ProofError(f"{what}: the transaction failed: {result['error']['text']} ({signature})")
        say(
            f"    {what}: {signature} ok={result['ok']} fee={result['fee']} "
            f"signers={','.join(result['signers'])}"
        )
        return result

    def singed(self, name: str) -> dict[str, Path]:
        """The two keypaths a sale of `name`'s ticket needs: its seller, and the record's authority."""
        return {self.mints[name]["seller"]: self.mints[name]["seller_key"], self.issuer: self.issuer_key}

    # -- one leg on stdout, in the report, and in the measurements ------

    def record_leg(self, *, key: str, title: str, checks: Checks, measured: dict,
                   sent: dict | None = None, note: str = "") -> bool:
        failed = checks.failed()
        ok = not failed
        entry = {
            "leg": key,
            "title": title,
            "ok": ok,
            "measured": measured,
            "checks": checks.items,
            "failed": failed,
            "signature": (sent or {}).get("signature"),
            "signers": (sent or {}).get("signers"),
            "instructions": (sent or {}).get("instructions"),
            "err": (sent or {}).get("error", {}).get("text"),
            "err_index": (sent or {}).get("error", {}).get("index"),
            "err_code": (sent or {}).get("error", {}).get("code"),
            "failed_log": (sent or {}).get("failed_log"),
            "logs": (sent or {}).get("logs") or [],
            "note": note,
            #: A leg may carry more than one transaction (leg 8 is two).
            "transactions": (sent or {}).get("transactions") or [],
        }
        self.results.append(entry)
        body = ", ".join(f"{name}={fmt(value)}" for name, value in measured.items())
        say(f"LEG {key} {'PASS' if ok else 'FAIL'}  {title}: {body}")
        for item in failed:
            say(f"    ! {item['check']}: got {item['got']}, wanted {item['want']}")
        return ok

    # -- legs ------------------------------------------------------------

    def leg1(self) -> None:
        """The fee is paid: price 1e9, 500 bps, 50_000_000 lamports, in one atomic transaction."""
        name = "sale"
        spec = self.mints[name]
        price = FACE
        fee = planned_fees()["leg1"]
        before = self.snapshot(name)
        instructions = self.sale(name, price=price, fee_bps=FEE_BPS)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.singed(name), what="leg 1 sale")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.leg1_record = dict(rec) if rec else None
        self.snapshots.append(("after leg 1 (a complete sale)", spec["record"], rec))

        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("instruction count (stage, fee, move)", len(instructions), 3)
        checks.eq("signer count", len(sent["signers"]), 2)
        checks.true("the two signers are the seller and the issuer",
                    set(sent["signers"]) == {spec["seller"], self.issuer},
                    ",".join(sent["signers"]))
        checks.true("the transaction succeeded", sent["ok"], str(sent["ok"]))
        checks.eq("staging before the sale", (before["record"] or {}).get("pending_price_lamports"), 0)
        checks.eq("seller lamports delta (-(fee + tx fee))", seller_delta, -(fee + sent["fee"]))
        checks.eq("artist lamports delta", artist_delta, fee)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        checks.true("record held_since_unix is non-zero",
                    int(rec.get("held_since_unix") or 0) > 0, str(rec.get("held_since_unix")))
        checks.true("the hook's own log line carries the price",
                    any(f"cap admitted price={price}" in line for line in sent["logs"]),
                    "no matching log line")
        self.record_leg(
            key="1", title="fee paid, price 1e9 at 500 bps", checks=checks, sent=sent,
            measured={"price": price, "fee_bps": FEE_BPS, "fee": fee, "tx_fee": sent["fee"],
                      "seller_delta": seller_delta, "artist_delta": artist_delta,
                      "seller_tokens": after["seller_tokens"], "buyer_tokens": after["buyer_tokens"],
                      "record_pending": rec.get("pending_price_lamports"),
                      "held_since_unix": rec.get("held_since_unix")},
        )

    def leg2(self) -> None:
        """Atomicity: a seller who cannot pay the fee fails the whole sale, staging included."""
        name = "underfunded"
        spec = self.mints[name]
        fee = planned_fees()["leg1"]
        before = self.snapshot(name)
        instructions = self.sale(name, price=FACE, fee_bps=FEE_BPS)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.singed(name), what="leg 2 sale (underfunded)",
                         allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        err = sent["error"]
        self.snapshots.append(("after leg 2 (the fee could not be paid)", spec["record"], rec))

        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("instruction count (stage, fee, move)", len(instructions), 3)
        checks.true("the seller holds less than the fee and more than the transaction fee",
                    before["seller_lamports"] < fee and before["seller_lamports"] > sent["fee"],
                    f"seller {before['seller_lamports']}, fee {fee}, tx fee {sent['fee']}")
        checks.true("the transaction failed", not sent["ok"], err["text"])
        # The index is the atomicity claim: 0 staged the price and executed, so the stage was
        # rolled back rather than never run. The code is reported, not asserted -- the brief
        # says to record what the cluster gave, and the cluster gave what it gave.
        checks.eq("the failing instruction index", err["index"], 1)
        checks.eq("seller lamports delta (the transaction fee only)", seller_delta, -sent["fee"])
        checks.eq("artist lamports delta", artist_delta, 0)
        checks.eq("seller tokens delta (the ticket did not move)",
                  after["seller_tokens"] - before["seller_tokens"], 0)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 0)
        checks.eq("the ticket is still in the seller's account", after["seller_tokens"], 1)
        checks.eq("record pending after the rollback", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="2", title="underfunded fee, atomic rollback", checks=checks, sent=sent,
            measured={"price": FACE, "fee": fee, "seller_before": before["seller_lamports"],
                      "tx_fee": sent["fee"], "seller_delta": seller_delta,
                      "artist_delta": artist_delta, "err_index": err["index"],
                      "err_code": err["code"], "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note="the error code is reported, not asserted: the brief says record what the cluster gave",
        )

    def leg3(self) -> None:
        """A refused sale pays no fee: one lamport over the ceiling, refused 6010, all rolled back."""
        name = "sale"
        spec = self.mints[name]
        price = CEILING + 1
        fee = planned_fees()["leg3"]
        before = self.snapshot(name)
        instructions = self.sale(name, price=price, fee_bps=FEE_BPS)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.singed(name), what="leg 3 sale (over cap)",
                         allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        err = sent["error"]
        self.snapshots.append(("after leg 3 (over cap, refused)", spec["record"], rec))

        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        checks = Checks()
        checks.eq("instruction count (stage, fee, move)", len(instructions), 3)
        checks.eq("the ceiling", CEILING, ceiling_lamports(face_lamports=FACE, cap_bps=CAP_BPS))
        checks.true("the transaction failed", not sent["ok"], err["text"])
        checks.eq("the refusal carries CapExceeded", err["code"], self.codes["CapExceeded"])
        checks.eq("the failing instruction index (the move)", err["index"], 2)
        checks.eq("artist lamports delta", after["artist_lamports"] - before["artist_lamports"], 0)
        # The fee leg is instruction 1 and it ran before the refusal at 2. Only the transaction
        # fee is missing from the seller afterwards, so the 62_500_000 payment was rolled back.
        checks.eq("seller lamports delta (the fee leg was rolled back)", seller_delta, -sent["fee"])
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], 0)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 0)
        checks.eq("record pending after the refusal", rec.get("pending_price_lamports"), 0)
        checks.true("the hook logged the cap refusal",
                    any(f"cap exceeded price={price}" in line for line in sent["logs"]),
                    "no matching log line")
        self.record_leg(
            key="3", title=f"over cap, p={price}", checks=checks, sent=sent,
            measured={"price": price, "ceiling": CEILING, "fee_that_was_rolled_back": fee,
                      "artist_delta": 0, "seller_delta": seller_delta, "tx_fee": sent["fee"],
                      "err_code": err["code"], "err_index": err["index"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note="a refused sale pays the artist nothing, and the fee instruction that ran was undone",
        )

    def leg4(self) -> None:
        """Rounding: 19 lamports pays 0 and 20 pays 1, and neither is expressed as a 0 transfer."""
        name = "sale"
        spec = self.mints[name]
        for tag, price, expected in (("4a", 19, planned_fees()["leg4_price_19"]),
                                     ("4b", 20, planned_fees()["leg4_price_20"])):
            before = self.snapshot(name)
            instructions = self.sale(name, price=price, fee_bps=FEE_BPS)
            sent = self.send(payer=spec["seller"], instructions=instructions,
                             signers=self.singed(name), what=f"leg {tag} sale (price {price})",
                             allow_failure=True)
            after = self.snapshot(name)
            rec = after["record"] or {}
            checks = Checks()
            checks.eq("fee the checkout computed", expected, 0 if price < 20 else 1)
            checks.eq("instruction count (no fee leg when the fee is 0)",
                      len(instructions), 2 if expected == 0 else 3)
            checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
            checks.eq("artist lamports delta", after["artist_lamports"] - before["artist_lamports"], expected)
            checks.eq("seller lamports delta",
                      after["seller_lamports"] - before["seller_lamports"], -(expected + sent["fee"]))
            checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
            checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
            checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
            self.record_leg(
                key=tag, title=f"rounding, price {price} pays {expected}", checks=checks, sent=sent,
                measured={"price": price, "fee_bps": FEE_BPS, "fee": expected,
                          "instructions": len(instructions), "tx_fee": sent["fee"],
                          "artist_delta": after["artist_lamports"] - before["artist_lamports"],
                          "seller_tokens": after["seller_tokens"]},
            )

    def leg5(self) -> None:
        """The upper bound, measured: 10_000 bps at 1e9 moves exactly the whole price."""
        name = "sale"
        spec = self.mints[name]
        price = FACE
        fee = planned_fees()["leg5"]
        before = self.snapshot(name)
        instructions = self.sale(name, price=price, fee_bps=10_000)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.singed(name), what="leg 5 sale (100%)", allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("the fee equals the price at 10_000 bps", fee, price)
        checks.eq("instruction count (stage, fee, move)", len(instructions), 3)
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("seller lamports delta (-(price + tx fee))", seller_delta, -(price + sent["fee"]))
        checks.eq("artist lamports delta", artist_delta, price)
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="5", title="100% fee, price 1e9", checks=checks, sent=sent,
            measured={"price": price, "fee_bps": 10_000, "fee": fee, "tx_fee": sent["fee"],
                      "seller_delta": seller_delta, "artist_delta": artist_delta,
                      "seller_tokens": after["seller_tokens"]},
        )

    def leg6(self) -> None:
        """Zero price: the checkout refuses to build it, and the chain refuses the move with 6009."""
        name = "sale"
        spec = self.mints[name]
        refused = None
        try:
            self.sale(name, price=0, fee_bps=FEE_BPS)
        except af.ArtistFeeError as exc:
            refused = str(exc)
        before = self.snapshot(name)
        # Two instructions and no fee leg: exactly the sale the checkout refuses to build.
        instructions = [self.stage(name, 0), self.move(name)]
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.singed(name), what="leg 6 move with 0 staged", allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        err = sent["error"]
        self.snapshots.append(("after leg 6 (staged 0, refused)", spec["record"], rec))
        checks = Checks()
        checks.true("sale_instructions refuses this sale at build time", refused is not None,
                    refused or "it built the sale")
        checks.eq("instruction count (stage, move; no fee leg)", len(instructions), 2)
        checks.true("the transaction failed", not sent["ok"], err["text"])
        checks.eq("the refusal carries TransferNotStaged", err["code"], self.codes["TransferNotStaged"])
        checks.eq("the failing instruction index (the move)", err["index"], 1)
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], 0)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 0)
        checks.eq("artist lamports delta", after["artist_lamports"] - before["artist_lamports"], 0)
        checks.eq("record pending after the refusal", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="6", title="zero price, refused 6009", checks=checks, sent=sent,
            measured={"staged": 0, "err_code": err["code"], "err_index": err["index"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("the leg exists to show the chain's own rule: the checkout's build-time refusal "
                  "is quoted in the refusal table below, and a unit test pins it"),
        )
        self.results[-1]["build_time_refusal"] = refused

    def leg7(self) -> None:
        """Fee paid is not price paid: read the record after leg 1 and say what it does not hold."""
        spec = self.mints["sale"]
        rec = dict(self.leg1_record or {})
        fee = planned_fees()["leg1"]
        fields = ["face_value_lamports", "cap_bps", "pending_price_lamports", "status",
                  "band_low_lamports", "jurisdiction", "policy", "held_since_unix", "authority"]
        values = [rec.get(name) for name in fields]
        checks = Checks()
        checks.eq("record width in bytes", rec.get("raw_len"), RECORD_LEN)
        checks.eq("the record's fields", sorted(set(rec) - {"raw_len"}), sorted(fields))
        checks.eq("the record's authority is the issuer", rec.get("authority"), self.issuer)
        checks.eq("pending after the sale", rec.get("pending_price_lamports"), 0)
        checks.true("held_since_unix > 0", int(rec.get("held_since_unix") or 0) > 0,
                    str(rec.get("held_since_unix")))
        checks.true("no field of the record equals the fee", fee not in values,
                    f"{fee} is one of {values}")
        self.snapshots.append(("the record read for leg 7 (after leg 1)", spec["record"], rec))
        self.record_leg(
            key="7", title="what the record stores after a sale", checks=checks,
            measured={"record_len": rec.get("raw_len"), "pending": rec.get("pending_price_lamports"),
                      "held_since_unix": rec.get("held_since_unix"),
                      "authority_is_issuer": rec.get("authority") == self.issuer,
                      "fields": len(fields), "fee": fee,
                      "fields_equal_to_fee": sum(1 for value in values if value == fee)},
            note=("the chain stores the staged number, not lamports that moved: the fee is charged "
                  "on the staged price and nothing on chain proves the buyer paid it"),
        )

    def leg8(self) -> None:
        """The free ride: stage in one transaction, move in another, pay the artist nothing."""
        name = "sale"
        spec = self.mints[name]
        price = FACE
        would_be = planned_fees()["leg8_would_be"]
        before = self.snapshot(name)
        stage_sent = self.send(
            payer=self.issuer, instructions=[self.stage(name, price)],
            signers={self.issuer: self.issuer_key}, what="leg 8a stage alone",
        )
        staged = read_record(self.url, spec["record"]) or {}
        move_sent = self.send(
            payer=spec["seller"], instructions=[self.move(name)],
            signers={spec["seller"]: spec["seller_key"]}, what="leg 8b move alone",
        )
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.snapshots.append(("after leg 8 (a move with no fee at all)", spec["record"], rec))
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("8a instruction count", stage_sent["instructions"], 1)
        checks.eq("8a signer count (the issuer alone)", len(stage_sent["signers"]), 1)
        checks.eq("8a signer is the issuer", stage_sent["signers"][0], self.issuer)
        checks.true("8a landed", stage_sent["ok"], stage_sent["error"]["text"])
        checks.eq("the staged price is on the record", staged.get("pending_price_lamports"), price)
        checks.eq("8b instruction count (the move alone, no fee leg)", move_sent["instructions"], 1)
        checks.eq("8b signer count (the seller alone)", len(move_sent["signers"]), 1)
        checks.eq("8b signer is the seller", move_sent["signers"][0], spec["seller"])
        checks.true("8b landed", move_sent["ok"], move_sent["error"]["text"])
        checks.eq("artist lamports delta (not one lamport)", artist_delta, 0)
        checks.eq("a checkout sale at this price would have paid the artist", would_be, planned_fees()["leg1"])
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("record pending after the unstaged sale", rec.get("pending_price_lamports"), 0)
        combined = dict(move_sent)
        combined["transactions"] = [
            {"role": "8a the stage, alone", "signature": stage_sent["signature"],
             "signers": stage_sent["signers"], "ok": stage_sent["ok"],
             "instructions": stage_sent["instructions"], "fee": stage_sent["fee"]},
            {"role": "8b the move, alone", "signature": move_sent["signature"],
             "signers": move_sent["signers"], "ok": move_sent["ok"],
             "instructions": move_sent["instructions"], "fee": move_sent["fee"]},
        ]
        self.record_leg(
            key="8", title="the free ride, two transactions", checks=checks, sent=combined,
            measured={"price": price, "fee_not_paid": would_be, "artist_delta": artist_delta,
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("admitted with no fee leg at all: this is why the checkout's monopoly on "
                  "staging is the only thing collecting the fee"),
        )

    def run_legs(self) -> None:
        """Every leg, in order, each recorded whether it passes, fails, or raises."""
        plan = [("1", self.leg1), ("2", self.leg2), ("3", self.leg3), ("4", self.leg4),
                ("5", self.leg5), ("6", self.leg6), ("7", self.leg7), ("8", self.leg8)]
        for key, leg in plan:
            self.check_deadline(f"leg {key}")
            try:
                leg()
            except (ProofError, dp.PublishError, KeyError, TypeError, ValueError) as exc:
                self.results.append({
                    "leg": key, "title": f"leg {key} raised", "ok": False, "measured": {},
                    "checks": [{"check": "the leg ran to a measurement", "got": str(exc),
                                "want": "a measured outcome", "ok": False}],
                    "failed": [{"check": "the leg ran to a measurement", "got": str(exc),
                                "want": "a measured outcome"}],
                    "signature": None, "signers": None, "instructions": None, "err": None,
                    "err_index": None, "err_code": None, "failed_log": None, "logs": [],
                    "note": "", "transactions": [],
                })
                say(f"LEG {key} FAIL  the leg raised: {exc}")


# -- the outputs ---------------------------------------------------------------


HONESTY = (
    "The fee binds only sales that our app builds. The chain does not force it: a transaction "
    "can stage a price, move the ticket and pay the artist nothing, and the hook admits it — "
    "leg 8 is that, measured. What the chain does force, on a record whose authority is the "
    "issuer, is that no ticket moves at all without the issuer's signature on the stage "
    "instruction, so a sale cannot bypass the checkout without first bypassing the hook."
)


def measurements(proof: Proof, *, passed: int, total: int, failures: list[str]) -> dict:
    """Everything the run measured, in a shape a later reader can diff against a rerun."""
    return {
        "tool": "tools/artist_fee_proof.py",
        "written_at": now_iso(),
        "surface": "solana local validator (loopback), the prebuilt cap_hook.so",
        "validator": proof.validator_version,
        "rpc_url": proof.url,
        "rpc_port_closed_after": proof.port_closed,
        "program_id": proof.program_id,
        "program_so": {"path": str(SO_PATH.relative_to(REPO_ROOT)), "sha256": proof.so_sha},
        "error_codes": proof.codes,
        "constants": {"face_value_lamports": FACE, "cap_bps": CAP_BPS, "ceiling_lamports": CEILING,
                      "band_low_lamports": BAND_LOW, "jurisdiction": JURISDICTION,
                      "fee_bps": FEE_BPS},
        "planned_fees": planned_fees(),
        "wallets": {"issuer": proof.issuer, "artist": proof.artist},
        "mints": {
            name: {key: (None if isinstance(value, Path) else value)
                   for key, value in spec.items() if key != "seller_key"}
            for name, spec in proof.mints.items()
        },
        "legs": proof.results,
        "record_snapshots": [
            {"when": when, "record": address, "state": state} for when, address, state in proof.snapshots
        ],
        "result": {"passed": passed, "total": total, "failures": failures},
        "honesty": HONESTY,
        "keys": ("generated fresh on every run under tmp/artist-fee/keys/ at 0600: the mint ids "
                 "differ between runs, the asserted properties do not"),
    }


def write_measurements(proof: Proof, *, passed: int, total: int, failures: list[str]) -> None:
    MEASUREMENTS.parent.mkdir(parents=True, exist_ok=True)
    MEASUREMENTS.write_text(
        json.dumps(measurements(proof, passed=passed, total=total, failures=failures), indent=2) + "\n",
        encoding="utf-8",
    )


def write_report(proof: Proof, *, passed: int, total: int, failures: list[str]) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# The artist fee at checkout — local validator proof",
        "",
        f"Written {now_iso()} by `tools/artist_fee_proof.py`.",
        "",
        "**This ran on a LOCAL `solana-test-validator`.** Nothing here touched devnet: no `--url`",
        "other than the validator's own loopback RPC, no faucet, no airdrop, no `--clone`. The",
        "validator's ledger was deleted when the run ended.",
        "",
        f"- Validator: `{proof.validator_version}`",
        f"- RPC: `{proof.url}`, closed after the run: **{proof.port_closed}**",
        f"- Program id: `{proof.program_id}` (deployed from `v2-keypair.json`, never rebuilt)",
        f"- Program `.so` sha256: `{proof.so_sha}`",
        f"- Issuer (the record's authority): `{proof.issuer}`",
        f"- Artist wallet: `{proof.artist}`",
        f"- Result: **{'PASS' if not failures else 'FAIL'} {passed}/{total}**",
        "",
        "Keys are generated fresh on every run under `tmp/artist-fee/keys/` (0600), so the mint",
        "ids differ between runs. The properties the legs assert do not.",
        "",
        "## The record and the sale",
        "",
        f"Face `{FACE:,}`, cap `{CAP_BPS}` bps → ceiling `{CEILING:,}`, band_low `{BAND_LOW}`,",
        f"jurisdiction `{JURISDICTION}`, fee `{FEE_BPS}` bps. One transaction holds three",
        "instructions — `SetPendingPrice`, the System `Transfer` of the fee, the Token-2022",
        "`Move` — and two signatures, because the record's authority is the mint's authority and",
        "the stage requires its signature. Every leg was sent with `skipPreflight`, so a refusal",
        "lands as a failed transaction with its own signature instead of dying in simulation.",
        "",
        "| mint | mint id | record | seller | buyer | face booked at birth |",
        "|---|---|---|---|---|---|",
    ]
    for name, spec in proof.mints.items():
        born = spec.get("record_at_birth") or {}
        lines.append(
            f"| {name} | `{spec['mint']}` | `{spec['record']}` | `{spec['seller']}` | "
            f"`{spec['buyer']}` | face {born.get('face_value_lamports')} |"
        )

    lines += [
        "",
        "## Legs",
        "",
        "| leg | what it asserts | result | signature |",
        "|---|---|---|---|",
    ]
    for result in proof.results:
        verdict = "pass" if result["ok"] else "**FAIL**"
        lines.append(
            f"| {result['leg']} | {result['title']} | {verdict} | "
            f"{'`' + result['signature'] + '`' if result['signature'] else '—'} |"
        )

    lines += ["", "## What each leg measured", ""]
    for result in proof.results:
        lines += [f"### Leg {result['leg']} — {result['title']}", ""]
        if result["measured"]:
            lines += ["| number | value |", "|---|---|"]
            for key, value in result["measured"].items():
                shown = f"{value:,}" if isinstance(value, int) and not isinstance(value, bool) else value
                lines.append(f"| {key} | {shown} |")
            lines.append("")
        if result["transactions"]:
            lines += ["| transaction | signature | signers | instructions | ok |", "|---|---|---|---|---|"]
            for tx in result["transactions"]:
                lines.append(
                    f"| {tx['role']} | `{tx['signature']}` | "
                    f"{', '.join('`' + key + '`' for key in tx['signers'])} | "
                    f"{tx['instructions']} | {tx['ok']} |"
                )
            lines.append("")
        if result["note"]:
            lines += [result["note"], ""]
        failed = result["failed"]
        if failed:
            lines += ["**Assertions that did not hold:**", ""]
            for item in failed:
                lines.append(f"- `{item['check']}`: got `{item['got']}`, wanted `{item['want']}`")
            lines.append("")
        elif result["checks"]:
            lines += [f"All {len(result['checks'])} assertions held.", ""]

    detail = [result for result in proof.results if result["leg"] in ("2", "3", "6")]
    lines += ["## The refusals, in the cluster's own words", ""]
    for result in detail:
        lines += [
            f"**Leg {result['leg']} — {result['title']}**",
            "",
            f"- signature: `{result['signature']}`",
            f"- `meta.err` verbatim: `{result['err']}`",
            f"- failing instruction index: `{result['err_index']}`, code: `{result['err_code']}`",
            f"- the failing program's log line: `{result['failed_log']}`",
        ]
        if result.get("build_time_refusal"):
            # Leg 6's other half: the checkout refuses to build the same sale at all, and a unit
            # test in `market_swarm/tests/test_artist_fee.py` already pins that refusal. The leg
            # exists to show the chain's own rule, which is a different rule and a different code.
            lines += [
                f"- the checkout's refusal, observed here before a blockhash was fetched: "
                f"`{result['build_time_refusal']}`",
                "- that build-time refusal is covered by a unit test "
                "(`market_swarm/tests/test_artist_fee.py`); this leg exists to show the chain's "
                "own rule, which does not depend on the checkout",
            ]
        lines.append("")

    lines += [
        "## Leg 7 — fee paid is not price paid",
        "",
        "The record after leg 1, read back and decoded here:",
        "",
        "```json",
        json.dumps(proof.leg1_record, indent=2, sort_keys=True),
        "```",
        "",
        "The 70-byte record holds the face, the cap, the staged price, the status, the floor, the",
        "jurisdiction, the policy, the hold clock and the authority. It holds **no fee and no",
        "payment**: after the sale the staged price is 0 and the number that moved 50,000,000",
        "lamports is nowhere on chain. The seller pays the fee on the staged price, and nothing",
        "on chain forces the buyer to have paid that price. That is documented, not fixed.",
        "",
        "## Leg 8 — the free ride, MEASURED",
        "",
        "Two separate transactions on a mint with tickets left: the issuer stages a price alone,",
        "then the seller moves the ticket alone with no fee leg. Both are admitted, and the artist",
        "balance is unchanged to the lamport.",
        "",
    ]
    for result in proof.results:
        if result["leg"] != "8":
            continue
        for tx in result["transactions"]:
            lines.append(f"- `{tx['role']}`: `{tx['signature']}` ({tx['instructions']} instruction, "
                         f"signers {', '.join('`' + key + '`' for key in tx['signers'])})")
        lines += [
            "",
            f"A checkout sale at the same price would have paid the artist "
            f"{result['measured'].get('fee_not_paid', 0):,} lamports and this paid "
            f"{result['measured'].get('artist_delta')}, so **the checkout's monopoly on staging "
            "is the only thing collecting the fee**: a staging is consumed by whoever moves next, "
            "and the chain asks for no payment on the way.",
            "",
        ]

    lines += [
        "## What this proves, and what it does not",
        "",
        HONESTY,
        "",
        "What was measured on this surface: every lamport delta above, each transaction's own",
        "`meta.fee`, both token balances, the decoded record, and each refusal's code and",
        "instruction index. What was **not** measured here: a real buyer's payment of the sale",
        "price (no such thing exists in this design), and any cluster other than this one.",
        "",
        "## Notes a reader should not have to rediscover",
        "",
        f"- The underfunded seller is funded with {SELLER_UNDERFUNDED_LAMPORTS:,} lamports, not the",
        "  10,000 the brief illustrates. 10,000 is exactly the two-signature transaction fee, and",
        "  a transaction that dies at the fee charge executes no instruction, so it would have",
        "  proved nothing about atomicity. The leg's claim is the failing instruction index: 1.",
        f"- The over-cap leg (price {CEILING + 1:,}) pays a {planned_fees()['leg3']:,}-lamport fee at",
        "  instruction 1 and is refused at instruction 2, and the seller's balance afterwards is",
        "  short only the transaction fee. That is the rollback, measured on a balance.",
        "- The program is deployed from `programs/cap_hook/target/deploy/v2-keypair.json`, not from",
        "  the frozen devnet keypair: `tools/devnet_publish.py` refuses to put v2 under that id, and",
        "  this tool follows the same rule rather than restating it.",
        "- No file in the repository was edited by this run. The ledger and the keys are under the",
        "  git-ignored `tmp/artist-fee/`.",
        "",
    ]
    if failures:
        lines += ["## Failures", ""] + [f"- {name}" for name in failures] + [""]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


#: Every leg key the run must produce a result for. Leg 4 emits two (`4a`, `4b`) because the
#: boundary it measures has two sides, and a missing key is a failure rather than a shorter list.
LEG_KEYS = ("1", "2", "3", "4a", "4b", "5", "6", "7", "8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deadline", type=float, default=600.0,
                        help="seconds for the whole run (default 600)")
    args = parser.parse_args(argv)

    # One run at a time. Two instances share `tmp/artist-fee/`, and the second one's `rmtree`
    # lands inside the first one's validator startup.
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        say(f"another artist_fee_proof run holds {LOCK_PATH.name}; not starting a second one")
        lock.close()
        return 2

    # The program is an input. Checked before a validator is started, so a rebuilt binary stops
    # the run in one line instead of after a boot.
    digest = hashlib.sha256(SO_PATH.read_bytes()).hexdigest() if SO_PATH.exists() else "missing"
    if digest != SO_SHA256:
        say(f"REFUSING TO RUN: {SO_PATH.relative_to(REPO_ROOT)} is {digest},")
        say(f"and this proof is about {SO_SHA256}.")
        say("Another run rebuilt it. This tool never rebuilds the program and will not describe a")
        say("binary it cannot name; rerun when the .so matches.")
        lock.close()
        return 3

    proof = Proof(deadline=args.deadline)
    passed = 0
    total = 0
    failures: list[str] = []
    exit_code = 1

    try:
        proof.validator_version = dp.run(
            [dp.which("solana-test-validator") or "solana-test-validator", "--version"],
            timeout=30, what="solana-test-validator --version",
        ).strip().splitlines()[-1]
        say(f"artist fee proof: face {FACE:,} cap {CAP_BPS} bps ceiling {CEILING:,} "
            f"band_low {BAND_LOW} fee {FEE_BPS} bps")
        say(f"  .so sha256 {SO_SHA256[:16]}… matches; deploying the existing binary")
        say(f"booting a local validator under {WORK.relative_to(REPO_ROOT)}/")
        proof.boot()
        say(f"  rpc {proof.url}")
        proof.deploy()
        say(f"  deployed {proof.program_id} ({proof.so_sha[:16]}…)")

        seller_key = KEYS / "seller.json"
        seller = proof.keygen(seller_key)
        proof.fund(proof.artist, 1_000_000, "fund the artist")
        proof.fund(seller, 3_000_000_000, "fund the seller")
        say(f"  seller {seller} artist {proof.artist}")

        proof.make_mint(name="sale", seller=seller, seller_key=seller_key, tickets=TICKETS_SALE)
        under_key = KEYS / "underfunded-seller.json"
        underfunded = proof.keygen(under_key)
        proof.make_mint(name="underfunded", seller=underfunded, seller_key=under_key,
                        tickets=TICKETS_UNDERFUNDED)
        proof.fund(underfunded, SELLER_UNDERFUNDED_LAMPORTS, "fund the underfunded seller")
        say(f"  underfunded seller {underfunded} holds {get_balance(proof.url, underfunded):,} lamports")
        say("")

        proof.run_legs()

        produced = [result["leg"] for result in proof.results]
        missing = [key for key in LEG_KEYS if key not in produced]
        total = len(proof.results)
        passed = sum(1 for result in proof.results if result["ok"])
        failures = [f"leg {r['leg']}: {'; '.join(item['check'] for item in r['failed'])}"
                    for r in proof.results if not r["ok"]]
        if missing:
            failures.append(f"no result for leg(s) {', '.join(missing)}")
        if proof.so_sha != SO_SHA256:
            failures.append(f"the .so changed during the run ({proof.so_sha}); something else is writing")

        say("")
        if failures:
            say(f"FAIL {passed}/{total}")
            for name in failures:
                say(f"  {name}")
            exit_code = 1
        else:
            say(f"PASS {passed}/{total}")
            exit_code = 0
    except ProofError as exc:
        say("")
        say(f"FAIL: {exc}")
        if proof.validator is not None and proof.validator.tail().strip():
            say("validator output tail:")
            say(proof.validator.tail())
        exit_code = 1
    except dp.PublishError as exc:
        say("")
        say(f"FAIL: {exc}")
        if proof.validator is not None and proof.validator.tail().strip():
            say("validator output tail:")
            say(proof.validator.tail())
        exit_code = 1
    finally:
        try:
            if proof.validator is not None:
                proof.validator.stop()
                proof.port_closed = port_is_closed(proof.port)
                say(f"  validator stopped; rpc port {proof.port} closed: {proof.port_closed}")
        finally:
            try:
                write_measurements(proof, passed=passed, total=total, failures=failures)
                write_report(proof, passed=passed, total=total, failures=failures)
                say(f"measurements: {MEASUREMENTS.relative_to(REPO_ROOT)}")
                say(f"report: {REPORT.relative_to(REPO_ROOT)}")
            except Exception as exc:  # noqa: BLE001 - the exit code already reflects the run
                say(f"could not write the outputs: {type(exc).__name__}: {exc}")
            lock.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

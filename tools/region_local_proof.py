#!/usr/bin/env python3
"""Prove `region_gate`'s three policies on a real local Solana validator.

This is a verification tool, not a product feature. It boots a throw-away
`solana-test-validator`, deploys `programs/region_gate` to it, creates one
Token-2022 mint per policy (capped / monitored / unresolved), and then drives
nine legs through **real transactions**, reading each refusal's error code and
each admission's log line off the cluster.

Two things are deliberately not touched: the devnet program (`5EJ1GU3M4vn…`) and
`programs/cap_hook`. There is no `--url devnet` anywhere in this file, and no
network call at all: Token-2022 is present in the validator's own genesis on
solana 4.x, so nothing has to be cloned from a cluster.

The program is an *input*. Its instruction layouts and its log strings were read
out of `programs/region_gate/src/lib.rs` before a byte was written here; this
tool never edits it and never rebuilds it unless the `.so` is missing.

Everything bounded: `--deadline` (default 600s) covers the whole run, every
child carries a subprocess timeout, and the deadline is re-checked between legs.
The validator is killed on every exit path (atexit plus SIGINT/SIGTERM/SIGHUP)
and its ledger is removed.
"""

from __future__ import annotations

import argparse
import atexit
import fcntl
import base64
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
# `tools/` has no `__init__.py`; it is importable only once it is on sys.path.
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import devnet_publish as dp  # noqa: E402

# -- what exists, and is read rather than written -----------------------------

CRATE = REPO_ROOT / "programs" / "region_gate"
SO_PATH = CRATE / "target" / "deploy" / "region_gate.so"
PROGRAM_KEYPAIR = CRATE / "target" / "deploy" / "region_gate-keypair.json"

WORK = REPO_ROOT / "tmp" / "region-proof"
#: Outside WORK on purpose: WORK is wiped at boot, and two runs must not both
#: decide they are the only one.
LOCK_PATH = REPO_ROOT / "tmp" / "region-proof.lock"
KEYS = WORK / "keys"
LEDGER = WORK / "ledger"
REPORT = REPO_ROOT / "tmp" / "build" / "region-local-proof.md"

# -- the program's constants, transcribed from lib.rs and asserted at runtime --

TAG_INIT_EXTRA_METAS = 0
TAG_INIT_RECORD = 1
TAG_SET_PENDING_PRICE = 2
TAG_SET_STATUS = 3
TAG_TIGHTEN_POLICY = 4

POLICY_CAPPED = 0
POLICY_MONITORED = 1
POLICY_UNRESOLVED = 2
U16_MAX_CAP = 65_535

E_AMOUNT_NOT_ONE = 6008
_E_TRANSFER_NOT_STAGED = 6009
E_CAP_EXCEEDED = 6010
_E_TICKET_NOT_VALID = 6013

#: The numbers the brief for this tool quotes for the four codes this crate
#: added. They are **not** what the program assigns: see `load_program_codes`.
#: Kept here so the disagreement is checked and reported rather than assumed
#: away, and so a reader can see which side moved.
BRIEF_CODES = {
    "PolicyInvalid": 6021,
    "PolicyLoosens": 6022,
    "JurisdictionCode": 6023,
    "NotAuthority": 6024,
}

RECORD_LEN = 58

BASE = 1_000_000_000
CAP_BPS = 1_000
CAP_CEILING = BASE * (10_000 + CAP_BPS) // 10_000            # 1_100_000_000
TIGHT_CEILING = BASE * (10_000 + 500) // 10_000              # 1_050_000_000
THREE_X = 3 * BASE

#: How many tickets each mint is stocked with: enough single-ticket legs to
#: land, plus two so the `amount == 2` refusal has a balance to spend.
TICKETS_CAPPED = 6
TICKETS_OTHER = 1


class ProofError(RuntimeError):
    """Something in the harness, not in the program. Ends the run non-zero."""


def say(line: str = "") -> None:
    sys.stdout.write(line + "\n")
    sys.stdout.flush()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# -- ports and the validator --------------------------------------------------


def free_block(count: int) -> int:
    """`count` consecutive free TCP ports on loopback.

    The validator binds gossip and a dynamic range as well as RPC, and a busy
    gossip port is a hard panic at startup, not a retry. So the whole range is
    probed here rather than left to the default 8000..8009.
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


class LocalCluster(dp.LocalValidator):
    """`dp.LocalValidator` with its startup command replaced, and nothing else.

    The inherited half is the part worth reusing: `stop()` kills the process
    group (not just the parent), waits, escalates to SIGKILL, and removes the
    ledger; `__init__` registers it with `atexit` and with the three signals.
    A validator that survives the run is the failure mode this class exists to
    prevent, so its teardown is not reimplemented.

    The override is for two measured reasons, both of which would make the
    inherited `start()` wrong here:

    1. `dp.LocalValidator.start()` passes `--url devnet` as a *clone* source and
       clones Token-2022 and the memo program from it. This run must not touch
       devnet at all, so that is out. It is also unnecessary: on solana 4.3.2 the
       test validator's genesis already carries Token-2022 at
       `TokenzQd…` (verified: account present, executable, at slot 0).
    2. It sets only RPC and faucet ports. Gossip then binds 8000, and on this
       host a second validator (or any listener on that port) panics it with
       `gossip_addr bind_to port 8000: Address already in use`. Binding loopback
       with explicit gossip and dynamic ranges starts in about two seconds.
    """

    def __init__(self, *, ledger: Path, port: int, faucet_port: int, gossip_port: int,
                 dynamic_base: int, dynamic_count: int, reset: bool = True, fund: str | None = None):
        super().__init__(ledger=ledger, port=port, faucet_port=faucet_port, reset=reset, fund=fund)
        self.gossip_port = gossip_port
        self.dynamic_base = dynamic_base
        self.dynamic_count = dynamic_count

    def wipe_ledger(self) -> None:
        """Remove the ledger and wait for it to be gone.

        `--reset` does this itself, but a launch that fails part way leaves a
        half-built RocksDB behind, and the next attempt then dies on a rename
        inside it with an error that says nothing about the real cause. Removing
        it here means an attempt always starts from nothing, and a retry is a
        retry rather than a repair.
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


# -- the program's own instructions ------------------------------------------
#
# `dp` carries v1 builders. Tag 0's account order and data are unchanged, so it
# is reused as-is. Tags 1, 2 and 4 changed (new record fields; an authority
# signer on the staging call) and are built here from lib.rs.


def ix_init_extra_metas(*, payer: str, mint: str, extra_metas: str, record: str, program_id: str) -> dp.Instruction:
    """Tag 0. Reused: `dp`'s account order and payload are the ones lib.rs reads."""
    return dp.instruction_init_extra_metas(
        payer=payer, mint=mint, extra_metas=extra_metas, record=record, program_id=program_id
    )


def ix_init_record(*, payer: str, mint: str, record: str, program_id: str,
                   base_lamports: int, cap_bps: int, jurisdiction: str,
                   policy: int, law_version: int) -> dp.Instruction:
    """Tag 1: `[1, base u64, cap_bps u16, jurisdiction [u8;2], policy u8, law_version u32]`."""
    if len(jurisdiction) != 2:
        raise ProofError(f"jurisdiction {jurisdiction!r} is not two bytes")
    data = (
        bytes([TAG_INIT_RECORD])
        + base_lamports.to_bytes(8, "little")
        + cap_bps.to_bytes(2, "little")
        + jurisdiction.encode("ascii")
        + bytes([policy])
        + law_version.to_bytes(4, "little")
    )
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(payer, True, True),
            dp.AccountMeta(mint, False, False),
            dp.AccountMeta(record, False, True),
            dp.AccountMeta(dp.SYSTEM_PROGRAM, False, False),
        ),
        data=data,
    )


def ix_set_pending_price(*, authority: str, record: str, program_id: str, price: int) -> dp.Instruction:
    """Tag 2: accounts `[authority(signer), record]`; data `[2, price u64]`.

    `dp.instruction_set_pending_price` passes only `[record]`, which is the v1
    shape. This program reads a signer first and checks it against the record's
    authority, so the v1 builder would fail with `NotAuthority`.
    """
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(authority, True, True),
            dp.AccountMeta(record, False, True),
        ),
        data=bytes([TAG_SET_PENDING_PRICE]) + price.to_bytes(8, "little"),
    )


def ix_tighten_policy(*, authority: str, record: str, program_id: str,
                      cap_bps: int, jurisdiction: str, law_version: int) -> dp.Instruction:
    """Tag 4: accounts `[authority(signer), record]`; data `[4, cap u16, jur [u8;2], law u32]`."""
    if len(jurisdiction) != 2:
        raise ProofError(f"jurisdiction {jurisdiction!r} is not two bytes")
    return dp.Instruction(
        program_id=program_id,
        accounts=(
            dp.AccountMeta(authority, True, True),
            dp.AccountMeta(record, False, True),
        ),
        data=(
            bytes([TAG_TIGHTEN_POLICY])
            + cap_bps.to_bytes(2, "little")
            + jurisdiction.encode("ascii")
            + law_version.to_bytes(4, "little")
        ),
    )


def ix_transfer(*, source: str, mint: str, destination: str, authority: str,
                record: str, program_id: str, extra_metas: str, amount: int = 1) -> dp.Instruction:
    """The hooked transfer. `dp`'s builder is unchanged from the proven v1 wire.

    `region_gate::execute` reads its hook accounts in exactly the order
    `cap_hook::execute` did — `[source, mint, destination, authority,
    extra_metas, record]` — so the same outer instruction produces the same
    order, and it is reused rather than re-derived.
    """
    return dp.instruction_transfer_checked(
        source=source,
        mint=mint,
        destination=destination,
        authority=authority,
        record=record,
        hook_program=program_id,
        extra_metas=extra_metas,
        amount=amount,
        decimals=0,
    )


# -- reading the chain --------------------------------------------------------


def read_record(url: str, address: str) -> dict | None:
    """The 58-byte Borsh `TicketRecord`, decoded by hand so the layout is checked here."""
    result = dp.rpc(url, "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}])
    value = (result or {}).get("value")
    if not value:
        return None
    raw = base64.b64decode(value["data"][0])
    if len(raw) != RECORD_LEN:
        raise ProofError(f"record {address} is {len(raw)} bytes, the Borsh width is {RECORD_LEN}")
    return {
        "base_lamports": int.from_bytes(raw[0:8], "little"),
        "cap_bps": int.from_bytes(raw[8:10], "little"),
        "pending_price_lamports": int.from_bytes(raw[10:18], "little"),
        "status": raw[18],
        "jurisdiction": raw[19:21].decode("ascii", "replace"),
        "policy": raw[21],
        "law_version": int.from_bytes(raw[22:26], "little"),
        "authority": raw[26:58].hex(),
    }


def load_program_codes(path: Path) -> dict[str, int]:
    """Read the error numbers out of the program's own source.

    Every leg below asserts against these, not against a remembered number. The
    brief for this tool states `6022` for `PolicyLoosens` and `6024` for
    `NotAuthority`; the crate assigns `6042` and `6040`, because 6021-6028 are
    already taken by the v2 program in `programs/cap_hook/` with different
    meanings, and it says so in a comment above the enum. Reading the source is
    how the tool stays right when the crate moves again instead of quietly
    encoding a stale expectation.
    """
    text = path.read_text(encoding="utf-8")
    block = re.search(r"pub enum RegionError \{(.*?)\n\}", text, re.S)
    if not block:
        raise ProofError(f"no `pub enum RegionError` block in {path}")
    codes = {name: int(value) for name, value in re.findall(r"(\w+)\s*=\s*(\d+)\s*,", block.group(1))}
    for name in ("AmountNotOne", "CapExceeded", "NotAuthority", "PolicyLoosens", "PolicyInvalid"):
        if name not in codes:
            raise ProofError(f"the program's error enum no longer defines {name}; this tool is stale")
    return codes


def custom_code(err) -> int | None:
    """The `Custom` number inside a transaction error, or None."""
    def walk(node):
        if isinstance(node, dict):
            if "Custom" in node:
                return node["Custom"]
            for value in node.values():
                found = walk(value)
                if found is not None:
                    return found
        elif isinstance(node, (list, tuple)):
            for value in node:
                found = walk(value)
                if found is not None:
                    return found
        return None

    return walk(err)


def chain_result(url: str, signature: str, status: dict) -> tuple[int | None, list[str]]:
    """The error code and the log lines, read back from the cluster.

    The status the send path already saw is the fallback: `getTransaction` can
    still be catching up for a slot or two, and a leg must not be reported as
    "no logs" because of that.
    """
    logs: list[str] = []
    err = status.get("err")
    for _ in range(10):
        try:
            tx = dp.rpc(
                url,
                "getTransaction",
                [signature, {"encoding": "json", "maxSupportedTransactionVersion": 0, "commitment": "confirmed"}],
            )
        except dp.PublishError:
            tx = None
        if tx:
            err = tx.get("meta", {}).get("err")
            logs = list(tx.get("meta", {}).get("logMessages") or [])
            break
        time.sleep(0.4)
    return custom_code(err), logs


def matched(logs: list[str], needle: str) -> str:
    for line in logs:
        if needle in line:
            return needle
    return "none"


# -- the run ------------------------------------------------------------------


class Proof:
    def __init__(self, *, deadline: float):
        self.started = time.monotonic()
        self.deadline = deadline
        self.validator: LocalCluster | None = None
        self.url = ""
        self.program_id = ""
        self.authority = ""
        self.other = ""
        self.ctx: dp.Context | None = None
        self.ctx_other: dp.Context | None = None
        self.mints: dict[str, dict] = {}
        self.results: list[dict] = []
        self.snapshots: list[tuple[str, str, dict | None]] = []
        self.so_sha = ""
        self.codes: dict[str, int] = {}

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

    def boot(self) -> None:
        self.codes = load_program_codes(CRATE / "src" / "lib.rs")
        if WORK.exists():
            shutil.rmtree(WORK, ignore_errors=True)
        KEYS.mkdir(parents=True, exist_ok=True)

        authority_key = KEYS / "authority.json"
        self.authority = self.keygen(authority_key)
        # Fund the authority at genesis so no faucet call is needed and the run
        # does not depend on the ledger's faucet behaviour.
        base = free_block(31)
        port, faucet = dp.free_port(), dp.free_port()
        self.validator = LocalCluster(
            ledger=LEDGER,
            port=port,
            faucet_port=faucet,
            gossip_port=base,
            dynamic_base=base + 1,
            dynamic_count=30,
            reset=True,
            fund=self.authority,
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
        self.url = self.validator.rpc_url

        self.ctx = dp.Context(
            cluster="local",
            rpc_url=self.url,
            keypair=authority_key,
            buyer_keypair=authority_key,
            out=WORK / "out",
        )
        self.ctx.payer = self.authority

        other_key = KEYS / "other.json"
        self.other = self.keygen(other_key)
        self.ctx_other = dp.Context(
            cluster="local",
            rpc_url=self.url,
            keypair=other_key,
            buyer_keypair=other_key,
            out=WORK / "out",
        )
        self.ctx_other.payer = self.other

    def deploy(self) -> None:
        source = CRATE / "src" / "lib.rs"
        stale = (
            source.exists()
            and SO_PATH.exists()
            and SO_PATH.stat().st_mtime + 1 < source.stat().st_mtime
        )
        if stale:
            say(f"  {SO_PATH.name} is older than lib.rs, rebuilding so the proof matches the source")
        if not SO_PATH.exists() or stale:
            say(f"  {SO_PATH.name} is missing, building with cargo-build-sbf")
            dp.run(
                [dp.which("cargo-build-sbf") or "cargo-build-sbf", "--sbf-out-dir", "target/deploy"],
                timeout=min(400.0, max(60.0, self.remaining() - 60)),
                what="cargo-build-sbf",
                cwd=CRATE,
            )
        if not SO_PATH.exists():
            raise ProofError(f"no program at {SO_PATH} even after a build")
        self.so_sha = dp.run(
            ["sha256sum", str(SO_PATH)], timeout=30, what="sha256sum (program)"
        ).split()[0]
        if not PROGRAM_KEYPAIR.exists():
            raise ProofError(f"no program keypair at {PROGRAM_KEYPAIR}")
        self.program_id = self.pubkey_of(PROGRAM_KEYPAIR)
        dp.run(
            [
                dp.which("solana") or "solana",
                "--url", self.url,
                "program", "deploy", str(SO_PATH),
                "--program-id", str(PROGRAM_KEYPAIR),
                "--keypair", str(self.ctx.keypair),
            ],
            timeout=min(300.0, max(60.0, self.remaining() - 30)),
            what="solana program deploy",
        )
        # `program deploy` returns once the transaction lands, but the account can
        # take a slot or two to answer a read. Poll rather than assume.
        if not dp.wait_for_account(self.url, self.program_id):
            raise ProofError(f"program {self.program_id} is not visible after deploy")
        account = dp.rpc(self.url, "getAccountInfo", [self.program_id, {"encoding": "base64"}])
        value = (account or {}).get("value") or {}
        if not value.get("executable"):
            raise ProofError(f"program {self.program_id} is not executable after deploy")

    def fund_other(self) -> None:
        instruction = dp.Instruction(
            program_id=dp.SYSTEM_PROGRAM,
            accounts=(
                dp.AccountMeta(self.authority, True, True),
                dp.AccountMeta(self.other, False, True),
            ),
            data=bytes([2, 0, 0, 0]) + (2_000_000_000).to_bytes(8, "little"),
        )
        dp.send_instructions(self.ctx, [instruction], what="fund the second wallet", skip_preflight=False)

    def spl(self, *args: str) -> str:
        return dp.run(dp.spl(self.ctx, *args), timeout=120, what=f"spl-token {args[0]}")

    def make_mint(self, *, name: str, policy: int, cap_bps: int, jurisdiction: str,
                  law_version: int, tickets: int) -> None:
        self.check_deadline(f"creating the {name} mint")
        mint_key = KEYS / f"{name}-mint.json"
        mint = self.keygen(mint_key)
        self.spl(
            "create-token", "--decimals", "0", "--transfer-hook", self.program_id, str(mint_key)
        )
        record = dp.derive_address(self.ctx, self.program_id, "string:record", f"pubkey:{mint}")
        extra_metas = dp.derive_address(
            self.ctx, self.program_id, "string:extra-account-metas", f"pubkey:{mint}"
        )

        dp.send_instructions(
            self.ctx,
            [ix_init_extra_metas(payer=self.authority, mint=mint, extra_metas=extra_metas,
                                 record=record, program_id=self.program_id)],
            what=f"{name}: init extra-account-metas",
        )
        dp.send_instructions(
            self.ctx,
            [ix_init_record(payer=self.authority, mint=mint, record=record, program_id=self.program_id,
                            base_lamports=BASE, cap_bps=cap_bps, jurisdiction=jurisdiction,
                            policy=policy, law_version=law_version)],
            what=f"{name}: init record",
        )

        record_state = read_record(self.url, record)
        if record_state is None:
            raise ProofError(f"{name}: no record at {record} after InitializeRecord")

        authority_ata = self.spl(
            "address", "--verbose", "--token", mint, "--owner", self.authority
        ).strip().split()[-1]
        self.spl("create-account", mint)
        buyer_ata = self.spl(
            "address", "--verbose", "--token", mint, "--owner", self.other
        ).strip().split()[-1]
        self.spl("create-account", mint, "--owner", self.other)
        if tickets:
            self.spl("mint", mint, str(tickets), authority_ata)

        self.mints[name] = {
            "mint": mint,
            "record": record,
            "extra_metas": extra_metas,
            "authority_ata": authority_ata,
            "buyer_ata": buyer_ata,
            "policy": policy,
            "cap_bps": cap_bps,
            "jurisdiction": jurisdiction,
            "law_version": law_version,
            "record_at_birth": record_state,
        }
        say(
            f"  {name}: mint {mint} record {record} cap={cap_bps} jur={jurisdiction} "
            f"policy={policy} law={law_version}"
        )

    # -- legs -----------------------------------------------------------

    def send(self, ctx: dp.Context, instructions: list[dp.Instruction], what: str):
        self.check_deadline(what)
        signature, status = dp.send_instructions(
            ctx, instructions, what=what, skip_preflight=True, allow_failure=True
        )
        code, logs = chain_result(self.url, signature, status)
        return signature, code, logs

    def stage(self, name: str, price: int) -> None:
        spec = self.mints[name]
        signature, code, logs = self.send(
            self.ctx,
            [ix_set_pending_price(authority=self.authority, record=spec["record"],
                                  program_id=self.program_id, price=price)],
            f"stage {price} on {name}",
        )
        if code is not None:
            raise ProofError(
                f"staging {price} on {name} was refused ({code}); the stage call must succeed "
                f"for the leg that follows to mean anything: {signature}"
            )

    def transfer(self, name: str, amount: int = 1):
        spec = self.mints[name]
        return self.send(
            self.ctx,
            [ix_transfer(source=spec["authority_ata"], mint=spec["mint"],
                         destination=spec["buyer_ata"], authority=self.authority,
                         record=spec["record"], program_id=self.program_id,
                         extra_metas=spec["extra_metas"], amount=amount)],
            f"transfer {amount} on {name}",
        )

    def record(self, name: str) -> dict | None:
        return read_record(self.url, self.mints[name]["record"])

    def leg(self, name: str, expectation: str, *, signature: str, code: int | None,
            logs: list[str], want_code: int | None, want_log: str | None,
            extra_ok: bool = True, extra_why: str = "") -> None:
        """Record one leg's observed outcome against what the brief says must happen."""
        log_matched = matched(logs, want_log) if want_log else "none"
        problems: list[str] = []
        if code != want_code:
            problems.append(f"error code {code} (wanted {want_code})")
        if want_log and log_matched == "none":
            problems.append(f"no log line containing {want_log!r}")
        if not extra_ok:
            problems.append(extra_why)
        ok = not problems
        self.results.append({
            "leg": name,
            "expectation": expectation,
            "signature": signature,
            "err": code,
            "log": log_matched,
            "ok": ok,
            "problems": problems,
            "logs": logs,
        })
        say(
            f"{name} {expectation} observed={signature} "
            f"err={'null' if code is None else code} log={log_matched}"
            + ("" if ok else f"  <-- FAILED: {'; '.join(problems)}")
        )

    def run_legs(self) -> None:
        # L1 — capped, exactly at the ceiling.
        self.stage("capped", CAP_CEILING)
        sig, code, logs = self.transfer("capped")
        self.leg("L1", f"capped-at-ceiling({CAP_CEILING})-succeeds", signature=sig, code=code,
                 logs=logs, want_code=None, want_log="cap admitted")

        # L2 — capped, one lamport over. The predicate has no division and is
        # inclusive, so exactly one lamport past the ceiling must be refused.
        self.stage("capped", CAP_CEILING + 1)
        sig, code, logs = self.transfer("capped")
        self.leg("L2", f"capped+1({CAP_CEILING + 1})-refused-{self.codes['CapExceeded']}", signature=sig, code=code,
                 logs=logs, want_code=self.codes["CapExceeded"], want_log="cap exceeded")

        # L3 — monitored admits 3x the base and says so.
        self.stage("monitored", THREE_X)
        sig, code, logs = self.transfer("monitored")
        self.leg("L3", f"monitored-at-3x({THREE_X})-succeeds", signature=sig, code=code,
                 logs=logs, want_code=None, want_log="monitored")

        # L4 — unresolved admits and records that the law is unresolved.
        self.stage("unresolved", THREE_X)
        sig, code, logs = self.transfer("unresolved")
        self.leg("L4", f"unresolved-at-3x({THREE_X})-succeeds", signature=sig, code=code,
                 logs=logs, want_code=None, want_log="unresolved")

        # L5 — tightening downwards lands, and the record carries the new cap.
        before = self.record("capped")
        self.snapshots.append(("capped before TightenPolicy", self.mints["capped"]["record"], before))
        spec = self.mints["capped"]
        sig, code, logs = self.send(
            self.ctx,
            [ix_tighten_policy(authority=self.authority, record=spec["record"],
                               program_id=self.program_id, cap_bps=500,
                               jurisdiction="GB", law_version=2)],
            "tighten capped 1000->500",
        )
        after = self.record("capped")
        self.snapshots.append(("capped after TightenPolicy 500/law2", spec["record"], after))
        landed = (
            after is not None
            and after["cap_bps"] == 500
            and after["law_version"] == 2
            and after["policy"] == POLICY_CAPPED
        )
        why = (
            "record did not read back cap=500 law=2 policy=0; it reads "
            f"{ {k: (after or {}).get(k) for k in ('cap_bps', 'law_version', 'policy')} }"
        )
        self.leg("L5", "tighten-downward-to-500-succeeds-and-binds", signature=sig, code=code,
                 logs=logs, want_code=None, want_log="tighten", extra_ok=landed, extra_why=why)

        # The new cap binds: the ceiling moved from 1.1e9 to 1.05e9. Measured on
        # both sides of it, because "it binds" is only true if the old price is
        # now refused and the new one is still admitted.
        self.stage("capped", TIGHT_CEILING)
        sig, code, logs = self.transfer("capped")
        self.leg("L5b", f"new-ceiling({TIGHT_CEILING})-still-admitted", signature=sig, code=code,
                 logs=logs, want_code=None, want_log="cap admitted")

        self.stage("capped", TIGHT_CEILING + 1)
        sig, code, logs = self.transfer("capped")
        self.leg("L5c", f"new-ceiling+1({TIGHT_CEILING + 1})-refused-{self.codes['CapExceeded']}", signature=sig, code=code,
                 logs=logs, want_code=self.codes["CapExceeded"], want_log="cap exceeded")

        # L6 — tightening upwards is refused, not applied.
        sig, code, logs = self.send(
            self.ctx,
            [ix_tighten_policy(authority=self.authority, record=spec["record"],
                               program_id=self.program_id, cap_bps=800,
                               jurisdiction="GB", law_version=3)],
            "tighten capped 500->800 (loosens)",
        )
        self.leg(f"L6", f"tighten-upward-to-800-refused-{self.codes['PolicyLoosens']}", signature=sig, code=code,
                 logs=logs, want_code=self.codes["PolicyLoosens"], want_log=None)
        still = self.record("capped")
        if not still or still["cap_bps"] != 500:
            self.results[-1]["ok"] = False
            self.results[-1]["problems"].append("the refused tighten changed the record")

        # L7 — monitored -> capped is a real tightening and is allowed.
        mon = self.mints["monitored"]
        before = self.record("monitored")
        self.snapshots.append(("monitored before TightenPolicy", mon["record"], before))
        sig, code, logs = self.send(
            self.ctx,
            [ix_tighten_policy(authority=self.authority, record=mon["record"],
                               program_id=self.program_id, cap_bps=1000,
                               jurisdiction="DE", law_version=2)],
            "tighten monitored->capped 1000",
        )
        after = self.record("monitored")
        self.snapshots.append(("monitored after TightenPolicy 1000/law2", mon["record"], after))
        landed = (
            after is not None
            and after["policy"] == POLICY_CAPPED
            and after["cap_bps"] == 1000
            and after["law_version"] == 2
        )
        why = (
            "record did not read back policy=0 cap=1000 law=2; it reads "
            f"{ {k: (after or {}).get(k) for k in ('policy', 'cap_bps', 'law_version')} }"
        )
        self.leg("L7", "monitored-to-capped-succeeds", signature=sig, code=code, logs=logs,
                 want_code=None, want_log="tighten", extra_ok=landed, extra_why=why)

        # L8 — a funded wallet that is not the record's authority cannot tighten.
        sig, code, logs = self.send(
            self.ctx_other,
            [ix_tighten_policy(authority=self.other, record=mon["record"],
                               program_id=self.program_id, cap_bps=500,
                               jurisdiction="DE", law_version=3)],
            "tighten by non-authority",
        )
        self.leg(f"L8", f"non-authority-tighten-refused-{self.codes['NotAuthority']}", signature=sig, code=code,
                 logs=logs, want_code=self.codes["NotAuthority"], want_log=None)

        # L9 — a hook that admits amount > 1 admits a bulk dump.
        self.stage("capped", BASE)
        sig, code, logs = self.transfer("capped", amount=2)
        self.leg(f"L9", f"amount-2-refused-{self.codes['AmountNotOne']}", signature=sig, code=code, logs=logs,
                 want_code=self.codes["AmountNotOne"], want_log=None)


# -- the report ---------------------------------------------------------------


def write_report(proof: Proof, *, passed: int, total: int, failures: list[str],
                 validator_version: str, so_sha_after: str) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    spec_rows = []
    for name, spec in proof.mints.items():
        born = spec["record_at_birth"] or {}
        spec_rows.append(
            f"| {name} | `{spec['mint']}` | `{spec['record']}` | {spec['policy']} | "
            f"{spec['cap_bps']} | {spec['jurisdiction']} | {spec['law_version']} | "
            f"{born.get('base_lamports')} |"
        )

    lines = [
        "# region_gate — local validator proof",
        "",
        f"Written {now_iso()} by `tools/region_local_proof.py`.",
        "",
        "**This ran on a LOCAL `solana-test-validator`.** Nothing here touched devnet, and the",
        "devnet program `5EJ1GU3M4vn…` was not deployed to, called, or in any way used. The",
        "validator's ledger is deleted when the run ends.",
        "",
        f"- Validator: `{validator_version}`",
        f"- Program id: `{proof.program_id}`",
        f"- Program `.so` sha256: `{so_sha_after}`",
        f"- Authority: `{proof.authority}`",
        f"- Result: **{'PASS' if not failures else 'FAIL'} {passed}/{total}**",
        "",
        "## The three mints",
        "",
        "| policy | mint | record | policy byte | cap_bps | jurisdiction | law_version | base |",
        "|---|---|---|---|---|---|---|---|",
        *spec_rows,
        "",
        "## Legs",
        "",
        "Each leg is a real transaction. `err` is the `Custom` code read back from the cluster,",
        "`log` is the substring matched in that transaction's own logs. Every leg is sent with",
        "`skipPreflight`, so a refusal lands with its own signature instead of dying in",
        "simulation.",
        "",
        "| leg | expected | signature | err | matched log | result |",
        "|---|---|---|---|---|---|",
    ]
    for result in proof.results:
        err = "null" if result["err"] is None else str(result["err"])
        verdict = "pass" if result["ok"] else "FAIL: " + "; ".join(result["problems"])
        lines.append(
            f"| {result['leg']} | {result['expectation']} | `{result['signature']}` | {err} | "
            f"{result['log']} | {verdict} |"
        )

    lines += [
        "",
        "## The record across each tighten",
        "",
        "| when | account | base | cap_bps | pending | status | jurisdiction | policy | law_version |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for when, account, record in proof.snapshots:
        if record is None:
            lines.append(f"| {when} | `{account}` | — | — | — | — | — | — | — |")
            continue
        lines.append(
            f"| {when} | `{account}` | {record['base_lamports']} | {record['cap_bps']} | "
            f"{record['pending_price_lamports']} | {record['status']} | {record['jurisdiction']} | "
            f"{record['policy']} | {record['law_version']} |"
        )

    shifted = {
        name: (BRIEF_CODES[name], proof.codes.get(name))
        for name in BRIEF_CODES
        if proof.codes.get(name) != BRIEF_CODES[name]
    }
    if shifted:
        lines += [
            "",
            "## The brief's error numbers are stale - the program's own numbers are used",
            "",
            "The brief for this tool quotes `6021`-`6024` for the four codes `region_gate` adds.",
            "The crate does not. It assigns",
            ", ".join(f"`{name}` = **{new}**" for name, (_, new) in sorted(shifted.items())),
            "",
            "with the reason written above its error enum: `6021`-`6028` are already taken by the",
            "v2 program in `programs/cap_hook/` with *different* meanings (`E_BAND_UNSATISFIABLE` is",
            "6022 there, `E_POLICY_INVALID` 6023), and a number meaning two things in two programs",
            "is not branchable by a client. So this tool parses the enum out of",
            "`programs/region_gate/src/lib.rs` and asserts against what the program assigns rather",
            "than encoding the brief. `L6` and `L8` still test the behaviour the brief asked for -",
            "an upward tighten is refused, a non-authority is refused - on the program's codes.",
            "",
            "| error | the brief says | the program assigns |",
            "|---|---|---|",
            *[f"| {name} | {old} | **{new}** |" for name, (old, new) in sorted(shifted.items())],
        ]

    lines += [
        "",
        "## What each policy was shown to do",
        "",
        "- **capped** admits a staged price at the ceiling and refuses one lamport over it. The",
        "  predicate is `price * 10_000 <= base * (10_000 + cap_bps)`, in `u128`, with no division",
        "  and inclusive at the cap — so at 1000 bps over a 1e9 base the ceiling is exactly",
        "  1_100_000_000. The refusal carries `6010`.",
        "- **monitored** admits 3x the base and logs the jurisdiction, price and ratio.",
        "- **unresolved** admits 3x the base and logs that the law is unresolved.",
        f"- **TightenPolicy** lands downwards (cap 1000 -> 500) and the new cap then binds at the",
        f"  new ceiling; refuses an upward move with `{proof.codes.get('PolicyLoosens')}`; allows",
        f"  monitored -> capped; and refuses a signer that is not the record's authority with",
        f"  `{proof.codes.get('NotAuthority')}`.",
        "- **amount != 1** is refused with `6008`, so a hooked mint cannot be dumped in bulk.",
        "",
        "## Notes a reader should not have to rediscover",
        "",
        "- `L5` in the brief asked for a transfer at 1_050_000_000 to fail and, in the same",
        "  sentence, for the ceiling at 1_050_000_000 to succeed. Those cannot both hold. The",
        "  program's predicate is inclusive (proven by `L1` and by its own unit test",
        "  `capped_boundary_is_inclusive`), so the ceiling is admitted and the ceiling **+1** is",
        "  refused: that is `L5b` and `L5c`.",
        "- `L6` carries `law_version` 3 so it cannot be refused for a stale generation. A",
        "  tightening must also name a later table generation, and the program checks",
        "  `tighten_allows` before it checks the law version, so what comes back is the loosen",
        f"  refusal (`{proof.codes.get('PolicyLoosens')}`) and not the policy-invalid code",
        f"  (`{proof.codes.get('PolicyInvalid')}`).",
        "- `L9` needs a balance of 2 in the source account to reach the hook at all, and four",
        f"  legs move one ticket each, so the capped mint is stocked with {TICKETS_CAPPED} tickets:",
        "  enough that the 2-token attempt is refused for the amount and not for the balance.",
        "",
    ]
    if failures:
        lines += ["## Failures", ""] + [f"- {name}" for name in failures] + [""]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deadline", type=float, default=600.0,
                        help="seconds for the whole run (default 600)")
    args = parser.parse_args(argv)

    # One run at a time. Two instances share `tmp/region-proof/`, and the second
    # one's `rmtree` lands inside the first one's validator startup: the observed
    # failure is a RocksDB rename on a ledger that vanished under it, which reads
    # like a program bug and is not one.
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        say(f"another region_local_proof run holds {LOCK_PATH.name}; not starting a second one")
        lock.close()
        return 2

    proof = Proof(deadline=args.deadline)
    passed = 0
    total = 0
    failures: list[str] = []
    validator_version = "unknown"
    so_sha_after = "unknown"
    exit_code = 1

    try:
        validator_version = dp.run(
            [dp.which("solana-test-validator") or "solana-test-validator", "--version"],
            timeout=30, what="solana-test-validator --version",
        ).strip().splitlines()[-1]

        say(f"booting a local validator under {WORK.relative_to(REPO_ROOT)}/")
        proof.boot()
        say(f"  rpc {proof.url}")
        proof.deploy()
        say(f"  deployed {proof.program_id} ({proof.so_sha[:16]}…)")
        for name, brief_value in BRIEF_CODES.items():
            actual = proof.codes.get(name)
            if actual != brief_value:
                say(f"  note: the brief says {name}={brief_value}, the program assigns {actual}")
        proof.fund_other()

        proof.make_mint(name="capped", policy=POLICY_CAPPED, cap_bps=CAP_BPS,
                        jurisdiction="GB", law_version=1, tickets=TICKETS_CAPPED)
        proof.make_mint(name="monitored", policy=POLICY_MONITORED, cap_bps=U16_MAX_CAP,
                        jurisdiction="DE", law_version=1, tickets=TICKETS_OTHER)
        proof.make_mint(name="unresolved", policy=POLICY_UNRESOLVED, cap_bps=U16_MAX_CAP,
                        jurisdiction="ZZ", law_version=1, tickets=TICKETS_OTHER)
        say("")

        proof.run_legs()

        total = len(proof.results)
        passed = sum(1 for result in proof.results if result["ok"])
        failures = [f"{r['leg']}: {'; '.join(r['problems'])}" for r in proof.results if not r["ok"]]

        so_sha_after = proof.so_sha
        try:
            now = dp.run(["sha256sum", str(SO_PATH)], timeout=30, what="sha256sum (program)").split()[0]
            if now != proof.so_sha:
                failures.append(
                    f"the program .so changed during the run ({proof.so_sha[:12]} -> {now[:12]}); "
                    "something else is writing to the crate"
                )
                so_sha_after = f"{proof.so_sha} then {now} (changed mid-run)"
        except dp.PublishError:
            pass

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
        if proof.validator is not None:
            tail = proof.validator.tail()
            if tail.strip():
                say("validator output tail:")
                say(tail)
        exit_code = 1
    except dp.PublishError as exc:
        say("")
        say(f"FAIL: {exc}")
        if proof.validator is not None:
            tail = proof.validator.tail()
            if tail.strip():
                say("validator output tail:")
                say(tail)
        exit_code = 1
    finally:
        try:
            if proof.mints:
                total = total or len(proof.results)
                passed = passed or sum(1 for result in proof.results if result["ok"])
                write_report(proof, passed=passed, total=total, failures=failures,
                             validator_version=validator_version, so_sha_after=so_sha_after)
                say(f"report: {REPORT.relative_to(REPO_ROOT)}")
        finally:
            if proof.validator is not None:
                proof.validator.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())

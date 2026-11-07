#!/usr/bin/env python3
"""Put the cap check on a cluster and record what is publicly there.

    python3 tools/devnet_publish.py --dry-run     # what it would do, no writes, no signing
    python3 tools/devnet_publish.py --local       # rehearse the whole thing on a local validator
    python3 tools/devnet_publish.py               # devnet, once the authority is funded

It is idempotent: every step reads the cluster first and skips what is already true, so a run
that dies halfway is resumed by running it again. Every command is bounded and every
validator it starts is killed on every exit path (`atexit`, SIGINT, SIGTERM and the normal
return).

What it does, in order, and what it refuses:

1. **Balance.** Below `MIN_BALANCE_LAMPORTS` it stops and prints the faucet instruction. The
   devnet RPC faucet is closed (`410`), so `solana airdrop` cannot work and retrying it is
   wasted time; funding needs the operator's GitHub session at https://faucet.solana.com.
2. **Build.** `cargo build-sbf` in `programs/cap_hook`, which produces the `.so`.
3. **Deploy.** `solana program deploy`, skipped when the program account is already executable.
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
is no code path here that can print, log or traceback a byte of key material.

Standard library only, plus this repository's own `ticketpath` package (which is itself
standard library only).
"""

from __future__ import annotations

import argparse
import atexit
import base64
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

DEVNET_ARTEFACT = REPO_ROOT / "records" / "devnet-artefacts.json"
LOCAL_ARTEFACT = REPO_ROOT / "records" / "devnet-artefacts.local.json"

CLUSTER_URLS = {"devnet": "https://api.devnet.solana.com"}
FAUCET_URL = "https://faucet.solana.com"
TOKEN_2022_PROGRAM = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"
ASSOCIATED_TOKEN_PROGRAM = "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL"
MEMO_PROGRAM = chain_client.MEMO_PROGRAM_ID
SYSTEM_PROGRAM = "11111111111111111111111111111111"

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

# Ports this machine already uses for something else. A validator this script starts must
# never land on one of them, and never on a port a browser would guess.
RESERVED_PORTS = {3000, 3001, 8787, 8788}


class PublishError(RuntimeError):
    """A step failed. The message is short, printable and carries no key material."""


class Refused(PublishError):
    """The run cannot proceed until the operator does something (funding, mostly)."""


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


# -- JSON-RPC, read-only ------------------------------------------------------


def rpc(url: str, method: str, params: list, *, timeout: float = BOUND_RPC):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode("utf-8")
    call = urlrequest.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urlrequest.urlopen(call, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - every transport failure is the same sentence
        raise PublishError(f"{method}: {url} did not answer ({type(exc).__name__})") from exc
    if payload.get("error"):
        message = payload["error"].get("message") if isinstance(payload["error"], dict) else payload["error"]
        raise PublishError(f"{method}: {message}")
    return payload.get("result")


def account_exists(url: str, address: str) -> bool:
    result = rpc(url, "getAccountInfo", [address, {"encoding": "base64"}])
    return bool(result and result.get("value"))


def account_is_executable(url: str, address: str) -> bool:
    result = rpc(url, "getAccountInfo", [address, {"encoding": "base64"}])
    value = (result or {}).get("value") or {}
    return bool(value.get("executable"))


def confirm(url: str, signature: str, *, timeout: float = BOUND_CONFIRM) -> dict:
    """Wait for a signature, and say whether it succeeded. A failure is a result, not an error."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = rpc(url, "getSignatureStatuses", [[signature], {"searchTransactionHistory": True}])
        value = ((result or {}).get("value") or [None])[0]
        if value:
            status = value.get("confirmationStatus")
            if value.get("err") is not None:
                return {"ok": False, "err": value["err"], "slot": value.get("slot")}
            if status in ("confirmed", "finalized"):
                return {"ok": True, "err": None, "slot": value.get("slot")}
        time.sleep(0.4)
    raise PublishError(f"timed out after {timeout:g}s waiting for {signature}")


def transaction_details(url: str, signature: str, *, attempts: int = 12) -> dict:
    """Slot, block time, error and the memo string of a landed transaction."""
    for _ in range(attempts):
        result = rpc(url, "getTransaction", [signature, {"encoding": "json", "commitment": "confirmed", "maxSupportedTransactionVersion": 0}])
        if result:
            return _summarise_transaction(result, signature)
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


def _memo_texts(result: dict) -> list[str]:
    """Every UTF-8 string this transaction carries as instruction data or echoes as a memo.

    Two shapes exist in the wild and this machine has both: devnet's memo program logs
    `Program log: Memo (len N): "text"` on one line, and the validator's built-in memo
    program logs `Program log: Memo (len N)` and then `Program log: text` on the next line.
    Neither is trusted on its own: the caller checks that *our* memo text is in the list, and
    instruction data is read first because logs are not guaranteed to be kept.
    """
    message = (result.get("transaction") or {}).get("message") or {}
    meta = result.get("meta") or {}
    texts: list[str] = []
    for instruction in message.get("instructions") or []:
        data = instruction.get("data")
        if isinstance(data, str):
            text = _instruction_text(data)
            if text is not None:
                texts.append(text)
    logs = meta.get("logMessages") or []
    for position, line in enumerate(logs):
        quoted = re.match(r'Program log: Memo \(len \d+\): "(.*)"$', line)
        if quoted:
            texts.append(quoted.group(1))
            continue
        header = re.match(r"Program log: Memo \(len (\d+)\)$", line)
        if header and position + 1 < len(logs):
            following = logs[position + 1]
            if following.startswith("Program log: "):
                candidate = following[len("Program log: "):]
                if len(candidate.encode("utf-8")) == int(header.group(1)):
                    texts.append(candidate)
    return _unique(texts)


def _unique(values: list[str]) -> list[str]:
    unique: list[str] = []
    for value in values:
        if value not in unique:
            unique.append(value)
    return unique


def _summarise_transaction(result: dict, signature: str) -> dict:
    meta = result.get("meta") or {}
    return {
        "signature": signature,
        "slot": result.get("slot"),
        "blockTime": result.get("blockTime"),
        "err": meta.get("err"),
        "fee": meta.get("fee"),
        "memos": _memo_texts(result),
    }


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
    cache: dict = field(default_factory=dict)

    def say(self, line: str) -> None:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()

    def plan(self, line: str) -> None:
        sys.stdout.write(("[plan] " if self.dry_run else "") + line + "\n")
        sys.stdout.flush()


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
) -> tuple[str, dict]:
    """Build, sign and send one transaction. Returns (signature, status).

    `skip_preflight` is what makes a *refusal* observable: with the preflight check on, a
    transaction the hook will reject never gets a signature, so there is nothing to show. With
    it off, the refusal lands as a failed transaction with its own signature and its own error,
    which is the only form of it a sceptic can look up.
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
    status = confirm(ctx.rpc_url, sent)
    if not status["ok"] and not allow_failure:
        raise PublishError(f"{what}: the transaction failed: {status['err']} ({sent})")
    ctx.say(f"  {what}: {sent} (slot {status.get('slot')})")
    return sent, status


# -- the local validator ------------------------------------------------------


class LocalValidator:
    """A single-node cluster started for one run, and killed on every exit path."""

    def __init__(self, *, ledger: Path, port: int, faucet_port: int, reset: bool = True):
        self.ledger = ledger
        self.port = port
        self.faucet_port = faucet_port
        self.reset = reset
        self.process: subprocess.Popen | None = None
        self._stopped = False

    @property
    def rpc_url(self) -> str:
        return f"http://127.0.0.1:{self.port}"

    def start(self) -> None:
        if not which("solana-test-validator"):
            raise PublishError("solana-test-validator is not on PATH")
        command = [
            which("solana-test-validator") or "solana-test-validator",
            *(["--reset"] if self.reset else []),
            "--quiet",
            "--ledger", str(self.ledger),
            "--rpc-port", str(self.port),
            # The faucet's default port is fixed, so a validator someone left running makes
            # this one fail with "failed to start faucet". Pick a free one instead.
            "--faucet-port", str(self.faucet_port),
            "--clone-upgradeable-program", TOKEN_2022_PROGRAM,
            "--clone", MEMO_PROGRAM,
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
                if rpc(self.rpc_url, "getHealth", [], timeout=2) == "ok":
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


def step_deploy(ctx: Context, program_id: str) -> None:
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


def step_mint(ctx: Context, program_id: str) -> str:
    existing = read_artefact(ctx.out) or {}
    mint = existing.get("mint")
    if mint and account_exists(ctx.rpc_url, mint):
        ctx.say(f"mint: reusing {mint} from {ctx.out.name}")
        return mint
    if ctx.dry_run:
        ctx.plan(f"mint: spl-token create-token --program-2022 --decimals 0 --transfer-hook {program_id} --enable-metadata")
        ctx.plan(f"mint: spl-token initialize-metadata <mint> {TICKET_NAME!r} {TICKET_SYMBOL} {TICKET_URI}")
        return "<mint>"
    output = run(
        spl(ctx, "create-token", "--decimals", "0", "--transfer-hook", program_id, "--enable-metadata"),
        timeout=BOUND_TOKEN,
        what="spl-token create-token",
    )
    mint = None
    for token in re.findall(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b", output):
        try:
            if len(base58.decode(token)) == 32:
                mint = token
                break
        except Exception:  # noqa: BLE001 - not a pubkey
            continue
    if not mint:
        raise PublishError(f"spl-token create-token printed no address:\n{output[-400:]}")
    ctx.say(f"mint: {mint} (Token-2022, 0 decimals, TransferHook -> {program_id}, MetadataPointer -> itself)")
    run(
        spl(ctx, "initialize-metadata", mint, TICKET_NAME, TICKET_SYMBOL, TICKET_URI),
        timeout=BOUND_TOKEN,
        what="spl-token initialize-metadata",
    )
    ctx.say(f"  metadata initialised: {TICKET_NAME!r} {TICKET_SYMBOL} <{TICKET_URI}>")
    return mint


def step_accounts(ctx: Context, mint: str) -> tuple[str, str, str]:
    """The authority's token account, the buyer's wallet, and the buyer's token account."""
    if ctx.dry_run:
        ctx.plan(f"accounts: spl-token create-account {mint} for the authority and for a throwaway buyer")
        return "<authority-ata>", buyer_pubkey(ctx), "<buyer-ata>"
    authority_ata = token_account_for(ctx, mint, payer_pubkey(ctx), create=True)
    buyer = buyer_pubkey(ctx)
    buyer_ata = token_account_for(ctx, mint, buyer, create=True)
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
        run(
            spl(ctx, "create-account", mint, "--owner", owner),
            timeout=BOUND_TOKEN,
            what="spl-token create-account",
        )
        ctx.say(f"  token account {address} for {owner}")
    return address


def step_wire(ctx: Context, mint: str, program_id: str) -> tuple[str, str]:
    if ctx.dry_run and (mint.startswith("<") or program_id.startswith("<")):
        ctx.plan(f"wire: ['extra-account-metas', mint] and ['record', mint] PDAs of {program_id} (skipped if they exist)")
        return "<record>", "<extra-account-metas>"
    record = derive_address(ctx, program_id, "string:record", f"pubkey:{mint}")
    extra_metas = derive_address(ctx, program_id, "string:extra-account-metas", f"pubkey:{mint}")
    if ctx.dry_run:
        ctx.plan(f"wire: extra-account-metas {extra_metas} and record {record} (skipped if they exist)")
        return record, extra_metas
    if account_exists(ctx.rpc_url, extra_metas) and account_exists(ctx.rpc_url, record):
        ctx.say(f"wire: {extra_metas} and {record} already exist")
        return record, extra_metas
    if not account_exists(ctx.rpc_url, extra_metas):
        send_instructions(
            ctx,
            [instruction_init_extra_metas(payer=payer_pubkey(ctx), mint=mint, extra_metas=extra_metas, record=record, program_id=program_id)],
            what="initialise extra-account-metas",
        )
    if not account_exists(ctx.rpc_url, record):
        send_instructions(
            ctx,
            [instruction_init_record(payer=payer_pubkey(ctx), mint=mint, record=record, program_id=program_id, face=FACE_LAMPORTS, cap_bps=CAP_BPS)],
            what=f"initialise record (face {FACE_LAMPORTS}, cap {CAP_BPS} bps)",
        )
    return record, extra_metas


def step_ticket(ctx: Context, mint: str, authority_ata: str) -> None:
    """Two tickets: one for the admitted sale and one for the refused one.

    The refused transfer must be refused by *the cap*, not by an empty account -- the first run
    of this script minted one, moved it, and then produced `Custom: 1` (Token-2022
    InsufficientFunds) instead of the hook's 6010.
    """
    balance = token_balance(ctx, authority_ata)
    if balance >= TICKETS_NEEDED:
        ctx.say(f"ticket: {authority_ata} already holds {balance}")
        return
    if ctx.dry_run:
        ctx.plan(f"ticket: spl-token mint {mint} {TICKETS_NEEDED} {authority_ata}")
        return
    run(
        spl(ctx, "mint", mint, str(TICKETS_NEEDED - balance), authority_ata),
        timeout=BOUND_TOKEN,
        what="spl-token mint",
    )
    ctx.say(f"ticket: {TICKETS_NEEDED - balance} minted to {authority_ata}")


def token_balance(ctx: Context, address: str) -> int:
    output = run(
        spl(ctx, "balance", "--address", address, "--output", "json"),
        timeout=60,
        what="spl-token balance",
        check=False,
    )
    try:
        return int(json.loads(output).get("amount", 0))
    except (json.JSONDecodeError, TypeError, ValueError):
        return 0


def step_memo(ctx: Context, quote: dict, buyer: str) -> dict:
    """One transaction carrying `ticketpath:quote:<id>:<hash>`, read back from the cluster."""
    existing = read_artefact(ctx.out) or {}
    if existing.get("signature") and existing.get("memoText") == quote["memoText"]:
        try:
            details = transaction_details(ctx.rpc_url, existing["signature"], attempts=2)
            if quote["memoText"] in details["memos"]:
                ctx.say(f"memo: reusing {existing['signature']} (slot {details['slot']})")
                return details
        except PublishError:
            pass
    if ctx.dry_run:
        ctx.plan(f"memo: solana transfer {buyer} 1 --with-memo {quote['memoText']}")
        return {"signature": "<memo signature>", "slot": 0, "blockTime": 0, "err": None, "memos": [quote["memoText"]]}
    output = solana(
        ctx,
        "transfer", buyer, "1",
        "--from", str(ctx.keypair),
        "--with-memo", quote["memoText"],
        "--allow-unfunded-recipient",
        timeout=BOUND_TOKEN,
    )
    signature = last_base58(output)
    if not signature:
        raise PublishError(f"solana transfer printed no signature:\n{output[-400:]}")
    status = confirm(ctx.rpc_url, signature)
    if not status["ok"]:
        raise PublishError(f"the memo transaction failed: {status['err']}")
    details = transaction_details(ctx.rpc_url, signature)
    if quote["memoText"] not in details["memos"]:
        raise PublishError("the transaction landed but the chain does not carry the memo text we sent")
    ctx.say(f"memo: {signature} (slot {details['slot']}, block time {details['blockTime']})")
    ctx.say(f"  {quote['memoText']}")
    return details


def step_transfer(
    ctx: Context,
    *,
    mint: str,
    authority_ata: str,
    buyer_ata: str,
    price: int,
    expect_failure: bool,
) -> dict:
    """Stage a price, attempt the transfer, and report what the chain did with it.

    Both legs take the same path and differ only in the staged price, because a boundary shown
    by two different mechanisms is not a boundary.
    """
    label = "refused over cap" if expect_failure else "accepted at cap"
    program_id = ctx.program_id or program_id_for(ctx)
    if ctx.dry_run:
        ctx.plan(f"transfer ({label}): stage {price} lamports, then transfer 1 ticket with the preflight check skipped")
        return {"signature": f"<{label}>", "slot": 0, "blockTime": 0, "priceLamports": price, "error": None, "explorer": None}
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
    )
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


def verify_balances(ctx: Context, *, authority_ata: str, buyer_ata: str, before: tuple[int, int]) -> None:
    """One ticket moved, one did not. The refusal's own signature says why; this says it held.

    Relative to the balances before the pair, so a second run against a cluster that already
    holds tickets checks the same property instead of an absolute count.
    """
    seller = token_balance(ctx, authority_ata)
    buyer = token_balance(ctx, buyer_ata)
    ctx.say(f"  after: seller {seller}, buyer {buyer} (was {before[0]}, {before[1]})")
    if (seller, buyer) != (before[0] - 1, before[1] + 1):
        raise PublishError(
            f"the balances moved the wrong way: seller {seller} and buyer {buyer}, after {before[0]} "
            f"and {before[1]}; exactly one ticket should have crossed, so the refused transfer moved one"
        )


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
    )


def publish(ctx: Context) -> int:
    started = time.monotonic()
    ctx.say(f"cluster: {ctx.cluster} ({ctx.rpc_url})")
    ctx.say(f"artefact: {ctx.out.relative_to(REPO_ROOT) if ctx.out.is_relative_to(REPO_ROOT) else ctx.out}")

    step_preflight(ctx)
    if ctx.dry_run and ctx.cluster != "localnet":
        ctx.plan(f"balance: needs at least {ctx.min_lamports / 1e9:.2f} SOL and a funded authority")
    elif ctx.dry_run:
        ctx.plan(f"validator: would start solana-test-validator on a free port with Token-2022 and Memo cloned from devnet, and kill it on exit")
        ctx.plan(f"balance: would fund the local authority from the validator's own faucet (needs {ctx.min_lamports / 1e9:.2f} SOL)")
    else:
        if ctx.cluster == "localnet" and ctx.validator is None:
            ledger = ctx.ledger or (Path(tempfile.gettempdir()) / f"ticketpath-devnet-ledger-{os.getpid()}")
            port = free_port()
            ctx.validator = LocalValidator(ledger=ledger, port=port, faucet_port=free_port(), reset=ctx.ledger is None)
            ctx.say(f"validator: starting solana-test-validator on 127.0.0.1:{port}, ledger {ledger}")
            ctx.validator.start()
            ctx.rpc_url = ctx.validator.rpc_url
            ctx.cache.pop("config", None)
        step_balance(ctx)

    step_build(ctx)
    program_id = program_id_for(ctx) if PROGRAM_KEYPAIR.exists() or ctx.program_id else "<program id>"
    ctx.say(f"program: {program_id}")
    step_deploy(ctx, program_id)
    mint = step_mint(ctx, program_id)
    quote = console_quote()
    ctx.say(f"quote: {quote['quoteId']} {quote['quoteHash'][:16]}… recommended {quote['recommendedLamports']:,} lamports at {quote['asOf']}")
    authority_ata, buyer, buyer_ata = step_accounts(ctx, mint)
    record, extra_metas = step_wire(ctx, mint, program_id)
    ctx.cache["record"] = record
    ctx.cache["extra_metas"] = extra_metas
    step_ticket(ctx, mint, authority_ata)
    memo = step_memo(ctx, quote, buyer)
    if ctx.dry_run:
        ctx.plan(f"transfer (accepted at cap): stage {ACCEPTED_PRICE_LAMPORTS} lamports, then spl-token transfer 1")
        ctx.plan(f"transfer (refused over cap): stage {REFUSED_PRICE_LAMPORTS} lamports, then spl-token transfer 1 --skip-preflight")
        ctx.say(f"dry run: {time.monotonic() - started:.1f}s, nothing built, signed, written or deployed")
        return EXIT_OK

    balances_before = (token_balance(ctx, authority_ata), token_balance(ctx, buyer_ata))
    accepted = step_transfer(
        ctx, mint=mint, authority_ata=authority_ata, buyer_ata=buyer_ata,
        price=ACCEPTED_PRICE_LAMPORTS, expect_failure=False,
    )
    refused = step_transfer(
        ctx, mint=mint, authority_ata=authority_ata, buyer_ata=buyer_ata,
        price=REFUSED_PRICE_LAMPORTS, expect_failure=True,
    )
    verify_balances(ctx, authority_ata=authority_ata, buyer_ata=buyer_ata, before=balances_before)

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

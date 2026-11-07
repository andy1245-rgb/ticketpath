"""The quote commitment: a hash, a memo, and never a signature.

`quote_commit` builds the memo a real client would submit -- the SHA-256 of a canonical
JSON of the pricing decision -- and returns it with `available: False`, because there is
no toolchain, no keypair and no program on this machine. This module imports no network
module, holds no key material, and has no code path that produces a signature.

`load_artefact` is the other half of the honesty boundary. The console may render a
`[DEVNET]` slot only when `records/devnet-artefacts.json` exists *and* the quote hash in
it recomputes from the fields the console is displaying. A file that fails the
recomputation renders as unverified, not as a slot. Nothing here writes: the file is
written by the operator's checker, once.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
CANONICAL_FIELDS = ("quoteId", "eventId", "tierId", "recommendedLamports", "asOf", "modelVersion")
CHECKER_VERSION = "devnet-check-2026-11-07"

# The one memo grammar this project speaks: `ticketpath:quote:<quoteId>:<hash>`. Everything
# that writes a memo -- `tools/devnet_publish.py` on the command line, `quote_commit` here --
# spells it with `expected_memo`, and `load_artefact` refuses an artefact whose memo is not
# this string, so a `v1`-shaped memo cannot render as verified.
MEMO_PREFIX = "ticketpath:quote"
CLUSTER = "devnet"


class ChainUnavailable(RuntimeError):
    """There is nothing to submit to, so submitting is not a thing this build does."""


def expected_memo(quote_id: str, digest: str) -> str:
    """The memo a quote commits with. One function, so two writers cannot spell it two ways."""
    return f"{MEMO_PREFIX}:{quote_id}:{digest}"


def canonical_json(fields: Mapping) -> str:
    """Sort keys, no whitespace: the one spelling two implementations must agree on."""
    return json.dumps(fields, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def quote_hash(fields: Mapping) -> str:
    """SHA-256 over the canonical JSON of the decision fields."""
    payload = {name: fields.get(name) for name in CANONICAL_FIELDS}
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def quote_id_for(*, event_id: str, tier_id: str, as_of: str) -> str:
    """A stable id for a quote: same event, tier and instant give the same id."""
    digest = hashlib.sha256(f"{event_id}|{tier_id}|{as_of}".encode("utf-8")).hexdigest()
    return f"q-{digest[:16]}"


def quote_commit(*, quote_id: str, recommendation: Mapping, mint: str | None = None, model_version: str = "engine-2026-11-07") -> dict:
    """Build the commitment. It is not sent, and there is no signature anywhere in it."""
    fields = {
        "quoteId": quote_id,
        "eventId": recommendation.get("eventId"),
        "tierId": recommendation.get("tierId"),
        "recommendedLamports": recommendation.get("recommendedLamports"),
        "asOf": recommendation.get("asOf"),
        "modelVersion": model_version,
    }
    digest = quote_hash(fields)
    memo = expected_memo(quote_id, digest)
    return {
        "available": False,
        "reason": "no_toolchain_no_keypair_no_program",
        "quoteId": quote_id,
        "quoteHash": digest,
        "memoText": memo,
        "mint": mint,
        "fields": fields,
        "instructions": [{"program": MEMO_PROGRAM_ID, "data": memo}],
        "serialized": None,
    }


def available() -> bool:
    """Nothing on this machine can sign. Always False, and it says so rather than raising."""
    return False


def submit(payload: Mapping) -> dict:
    raise ChainUnavailable("no keypair, no toolchain and no program: nothing is signed or sent")


def load_artefact(path: str | Path | None) -> dict:
    """Read and verify the operator's devnet artefact. Absent stays absent.

    Four things have to hold for `verified`: every field the console displays is present, the
    quote hash recomputes from those fields, the memo is this repository's grammar, and the
    cluster is **devnet**. A file written by a local rehearsal carries `cluster: "localnet"`
    and is refused here rather than rendered as chain evidence -- the rehearsal proves the
    path runs, not that anything is on devnet.
    """
    if path is None:
        return {"state": "absent", "reason": "devnet_absent"}
    target = Path(path)
    if not target.exists():
        return {"state": "absent", "reason": "devnet_absent"}
    try:
        record = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"state": "unverified", "reason": "devnet_unverified"}
    if not isinstance(record, dict):
        return {"state": "unverified", "reason": "devnet_unverified"}
    required = ("signature", "slot", "blockTime", "quoteHash", "quoteId", "eventId", "tierId", "recommendedLamports", "asOf", "modelVersion")
    if any(record.get(name) is None for name in required):
        return {"state": "unverified", "reason": "devnet_unverified"}
    if record.get("cluster") != CLUSTER:
        return {"state": "unverified", "reason": "cluster_not_devnet", "cluster": record.get("cluster")}
    if record.get("memoText") is not None and record["memoText"] != expected_memo(record["quoteId"], record["quoteHash"]):
        return {"state": "unverified", "reason": "memo_grammar_mismatch"}
    if quote_hash(record) != record["quoteHash"]:
        return {"state": "unverified", "reason": "quote_hash_mismatch"}
    return {
        "state": "verified",
        "signature": record["signature"],
        "slot": record["slot"],
        "blockTime": record["blockTime"],
        "cluster": record["cluster"],
        "rpcUrl": record.get("rpcUrl"),
        "quoteId": record["quoteId"],
        "quoteHash": record["quoteHash"],
        "checkedAt": record.get("checkedAt"),
        "checkerVersion": record.get("checkerVersion", CHECKER_VERSION),
        "mint": record.get("mint"),
        "programId": record.get("programId"),
        "explorer": record.get("explorer"),
        "transfers": record.get("transfers"),
    }

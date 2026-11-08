"""The quote commitment: a hash, a memo, and never a signature.

`quote_commit` builds the memo a real client would submit -- the SHA-256 of a canonical
JSON of the pricing decision -- and returns it with `available: False`, because there is
no toolchain, no keypair and no program on this machine. This module imports no network
module, holds no key material, and has no code path that produces a signature.

`load_artefact` is the other half of the honesty boundary. A `[DEVNET]` slot is rendered
only from a file whose quote hash recomputes, whose cluster is devnet, whose memo is
present and spells this repository's grammar, and whose signature, slot, block time, mint,
program id and memo program pass the type checks in `_malformed_fields`; anything else
renders as unverified, with the reason named, and no signature. Nothing here writes: the
file is written by the operator's checker, once.

The hash covers six fields (`CANONICAL_FIELDS`) and nothing else, so the checks below are
not a second hash: they are the cheap ones that can be made without a network, and the page
prints every field they do not cover as the writer's assertion rather than as chain evidence
(feature 2 review, the forged-signature finding).

The block it returns is the *recorded* quote, not the console's current one. `asOf`,
`quoteId` and `quoteHash` in it are the file's, and a caller that also holds a live quote
must keep the two apart (decision MD2). A field the file does not carry reads back as
None; nothing here is defaulted in from a constant, because a defaulted field would be a
chain fact the file never stated.

`MEMO_PROGRAMS` is a table and not a constant because the memo program id is a property of
a cluster, and this module carried one id for every cluster: the mainnet one, on devnet
too. A caller that knows its cluster passes it to `memo_program_id`; a cluster the table
has no measurement for raises rather than borrowing a neighbour's id. Only clusters this
repository has actually measured a program id for are in it, and each entry says which
measurement put it there.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Mapping

CLUSTER = "devnet"

# Every id below was read off a cluster or off a tool this machine ran, and the comment
# beside each one is the measurement that justifies it. Nothing here is a memory of how the
# CLI behaves: that is what this table had wrong once already.
#
# devnet -- MEASURED 2026-11-08T05:39:47Z. The second instruction of the proven memo
# transaction
# 2Lx6cboK8kvuJ7H6w2CELvZg3xF7cSHtBTSBXqi1w6KN2eXkQ6skqNPwnT5iVVAdrfBs5LiAau3pXiBMTtZMGCPZ
# has programIdIndex 3, and accountKeys[3] reads `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`.
# Method, time and the quoted JSON are in records/findings/40-memo-program-id.md.
MEMO_PROGRAM_DEVNET = "Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"
# memo v3, and NOT the program the `solana` CLI writes a `--with-memo` instruction to: the
# shipped 4.3.2 CLI wrote `Memo4c2p` on devnet (the landed transaction above) and on a local
# validator (its simulation log names `Memo4c2p` as the invoked program). No cluster has been
# measured at this id by this repository, so no cluster in the table below names it. It stays
# named here because README.md and docs/ON-CHAIN-DESIGN.md quote it as mainnet's unmeasured
# id, and the documentation gate compares the ids those files quote against the literals this
# module carries.
MEMO_PROGRAM_CLI = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"

# cluster -> the memo program id a run on that cluster uses, one row per measurement.
#
# devnet: the landed transaction above. localnet: the same id, measured twice on
# 2026-11-08 on a `solana-test-validator` 4.3.2 started from a fresh ledger -- the CLI's
# own simulation log names `Memo4c2p` as the invoked program, and the validator holds the
# program account and its programdata at that id from genesis. That last part is a warning
# and not a reassurance: the genesis copy is a stub whose ProgramData records slot 0, so the
# memo cannot execute locally at all until something deploys it. See finding 40's correction.
#
# mainnet-beta and testnet are absent on purpose. The one id this repository used to name for
# mainnet was the CLI's shipped one, and the CLI has since been measured writing the devnet
# id instead, so that row was a guess the evidence contradicts. Nothing has been read off
# mainnet, so nothing is named for it.
MEMO_PROGRAMS = {
    "devnet": MEMO_PROGRAM_DEVNET,
    "localnet": MEMO_PROGRAM_DEVNET,
}

CANONICAL_FIELDS = ("quoteId", "eventId", "tierId", "recommendedLamports", "asOf", "modelVersion")

# The one memo grammar this project speaks: `ticketpath:quote:<quoteId>:<hash>`. Everything
# that writes a memo -- `tools/devnet_publish.py` on the command line, `quote_commit` here --
# spells it with `expected_memo`, and `load_artefact` refuses an artefact whose memo is not
# this string, so a `v1`-shaped memo cannot render as verified.
MEMO_PREFIX = "ticketpath:quote"

# The two transfer legs the publisher records, in the order a reader meets them. A leg the
# file does not carry is dropped rather than filled in; a field it does not carry is dropped
# for the same reason.
TRANSFER_LEGS = ("acceptedAtCap", "refusedOverCap")
TRANSFER_FIELDS = ("signature", "slot", "blockTime", "priceLamports", "error", "explorer")

# The grammar the six hashed fields do not cover, checked without a network. `slot`,
# `blockTime`, `signature`, `mint` and `programId` are rendered as chain identity, and the
# quote hash does not touch any of them: a file whose `signature` is 88 "F" characters
# recomputes its hash and used to verify, so the page printed a forged signature beside a real
# slot and the file's explorer link (feature 2 review, the forged-signature finding).
SIGNATURE_LENGTH = 88
SIGNATURE_BYTES = 64
ADDRESS_BYTES = 32

# Base58, the alphabet Solana writes addresses and signatures in. 0, O, I and l are absent on
# purpose, which is what makes a missed character a refused file rather than a wrong address.
BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class ChainUnavailable(RuntimeError):
    """There is nothing to submit to, so submitting is not a thing this build does."""


class UnknownCluster(LookupError):
    """No memo program id has been measured for this cluster, so there is none to name.

    A wrong program id is not a failed transaction: a memo sent to an id no cluster hosts is
    refused, but a memo sent to an id that another cluster hosts lands and is read by nobody.
    So an unknown cluster stops the caller here rather than borrowing a neighbouring id.
    """


def memo_program_id(cluster: str | None = None) -> str:
    """The memo program id for one cluster. An unmeasured cluster raises; nothing is guessed.

    Omitted, the cluster is this module's own (`CLUSTER`, devnet), which is the cluster the
    console's commitment is for. A caller that knows its cluster passes it and never relies
    on that default.
    """
    name = CLUSTER if cluster is None else cluster
    try:
        return MEMO_PROGRAMS[name]
    except KeyError:
        raise UnknownCluster(
            f"no memo program id is measured for cluster {name!r}; "
            f"the table covers {', '.join(sorted(MEMO_PROGRAMS))}"
        ) from None


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


_RESOLVE = object()  # "no id was supplied; ask the table"


def quote_commit(
    *,
    quote_id: str,
    recommendation: Mapping,
    mint: str | None = None,
    model_version: str = "engine-2026-11-07",
    cluster: str | None = None,
    memo_program=_RESOLVE,
) -> dict:
    """Build the commitment. It is not sent, and there is no signature anywhere in it.

    The instruction names the memo program of `cluster`, because the caller that knows which
    cluster a commitment is for is the caller that must say so; omitted, it is this module's
    cluster. A cluster with no measurement raises, which is what a caller that has not
    thought about the cluster should get.

    `memo_program` is for the caller that has already asked -- `ticketpath/orchestrator.py`
    resolves the id once and reuses it for the payload field and for this instruction. It is
    the resolved id, or None for a cluster the table cannot name, and then the instruction
    names no program rather than a nearby cluster's. Nothing else should pass it: one lookup
    per caller is the point of `memo_program_id`.
    """
    program = memo_program_id(cluster) if memo_program is _RESOLVE else memo_program
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
        "instructions": [{"program": program, "data": memo}],
        "serialized": None,
    }


def available() -> bool:
    """Nothing on this machine can sign. Always False, and it says so rather than raising."""
    return False


def submit(payload: Mapping) -> dict:
    raise ChainUnavailable("no keypair, no toolchain and no program: nothing is signed or sent")


def _transfers(value) -> dict | None:
    """The legs the file records, each with only the fields it sets. Nothing is invented."""
    if not isinstance(value, Mapping):
        return None
    legs = {}
    for leg in TRANSFER_LEGS:
        row = value.get(leg)
        if not isinstance(row, Mapping):
            continue
        legs[leg] = {name: row[name] for name in TRANSFER_FIELDS if name in row}
    return legs or None


def is_whole(value) -> bool:
    """A lamport count or a slot: an int, and not a bool dressed as one."""
    return isinstance(value, int) and not isinstance(value, bool)


def _base58_decoded(value) -> bytes | None:
    """The bytes a base58 string decodes to, or None when a character is not base58."""
    if not isinstance(value, str) or not value:
        return None
    number = 0
    for char in value:
        index = BASE58_ALPHABET.find(char)
        if index < 0:
            return None
        number = number * 58 + index
    body = number.to_bytes((number.bit_length() + 7) // 8, "big") if number else b""
    # A leading base58 zero is a leading zero byte, and dropping it shortens an address.
    leading = len(value) - len(value.lstrip("1"))
    return b"\x00" * leading + body


def _is_address(value) -> bool:
    """A Solana address: base58 that decodes to exactly 32 bytes."""
    decoded = _base58_decoded(value)
    return decoded is not None and len(decoded) == ADDRESS_BYTES


def _is_signature(value) -> bool:
    """The signature grammar: base58 that decodes to exactly 64 bytes.

    Checked on the decoded bytes and not on a character count, because 64 bytes render to 86,
    87 or 88 base58 characters and the operator's own artefact carries all three lengths: its
    memo signature and its refused leg are 88 characters and its accepted leg is 87. An
    "88 characters" rule would have refused a signature that is on devnet, so the rule is the
    one that makes the rendering true: 64 bytes, base58.
    """
    decoded = _base58_decoded(value)
    return decoded is not None and len(decoded) == SIGNATURE_BYTES


def _malformed_fields(record: Mapping) -> dict | None:
    """The first cheap check the file fails, as (reason, field). None when it passes them all.

    Ordered so the reason names the first thing a reader would look at: the signature is the
    identity the page's link is built from, then the two numbers that place it on the chain,
    then the two addresses, then the memo program, and the hash last because it is the most
    expensive and the least specific.
    """
    if not _is_signature(record.get("signature")):
        return {"reason": "signature_malformed"}
    if not is_whole(record.get("slot")):
        return {"reason": "slot_malformed"}
    if not is_whole(record.get("blockTime")):
        return {"reason": "block_time_malformed"}
    # Both are optional fields: an artefact written before they existed still verifies. A file
    # that carries one has to carry an address.
    if record.get("mint") is not None and not _is_address(record.get("mint")):
        return {"reason": "mint_malformed"}
    if record.get("programId") is not None and not _is_address(record.get("programId")):
        return {"reason": "program_id_malformed"}
    if record.get("mint") is not None and record.get("mint") == record.get("programId"):
        return {"reason": "mint_is_program"}
    memo_program = record.get("memoProgram")
    if memo_program is not None:
        try:
            measured = memo_program_id(record.get("cluster"))
        except UnknownCluster:
            # No measurement for this cluster: the loader has already refused a non-devnet
            # file above, so this is a cluster nobody has read rather than a wrong id.
            measured = None
        if measured is not None and memo_program != measured:
            return {"reason": "memo_program_mismatch"}
    return None


def _signature_count(record: Mapping, transfers: Mapping | None) -> int:
    """How many transaction signatures the file carries: the memo, plus each transfer leg.

    Counted here rather than in the payload builder because the count is a fact about the
    file's grammar, and the evidence strip printed 1 for a file that carries three
    (feature 2 review). Only a leg whose signature is a string counts: a leg with a malformed
    one has no transaction the page can point at.
    """
    count = 1 if isinstance(record.get("signature"), str) and record["signature"] else 0
    for row in (transfers or {}).values():
        if isinstance(row, Mapping) and isinstance(row.get("signature"), str) and row["signature"]:
            count += 1
    return count


def load_artefact(path: str | Path | None) -> dict:
    """Read and verify the operator's devnet artefact. Absent stays absent.

    Five things have to hold for `verified`: every field the console displays is present, the
    quote hash recomputes from those fields, the memo is this repository's grammar **and is
    present at all**, the cluster is **devnet**, and the fields the hash does not cover pass
    `_malformed_fields`. A file written by a local rehearsal carries `cluster: "localnet"` and
    is refused here rather than rendered as chain evidence -- the rehearsal proves the path
    runs, not that anything is on devnet.

    The memo check is not optional. It used to be skipped when the file carried no `memoText`,
    so a file with no memo verified and the page still said "one quote memo"; nothing tied the
    signature to the quote except a field the loader treated as absent-able. `memo_missing` is
    the reason now.
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
    if record.get("memoText") is None:
        return {"state": "unverified", "reason": "memo_missing"}
    if record["memoText"] != expected_memo(record["quoteId"], record["quoteHash"]):
        return {"state": "unverified", "reason": "memo_grammar_mismatch"}
    malformed = _malformed_fields(record)
    if malformed is not None:
        return {"state": "unverified", **malformed}
    if quote_hash(record) != record["quoteHash"]:
        return {"state": "unverified", "reason": "quote_hash_mismatch"}
    transfers = _transfers(record.get("transfers"))
    return {
        "state": "verified",
        "asOf": record["asOf"],
        "eventId": record["eventId"],
        "tierId": record["tierId"],
        "modelVersion": record["modelVersion"],
        "recommendedLamports": record["recommendedLamports"],
        "signature": record["signature"],
        "slot": record["slot"],
        "blockTime": record["blockTime"],
        "cluster": record["cluster"],
        "rpcUrl": record.get("rpcUrl"),
        "quoteId": record["quoteId"],
        "quoteHash": record["quoteHash"],
        "checkedAt": record.get("checkedAt"),
        # Additive fields read back as None rather than as a value somebody guessed after the
        # fact: an artefact written before a field existed still verifies, and the page
        # prints nothing for it.
        "checkerVersion": record.get("checkerVersion"),
        "memoText": record.get("memoText"),
        "mint": record.get("mint"),
        "programId": record.get("programId"),
        "memoProgram": record.get("memoProgram"),
        "capBps": record.get("capBps"),
        "faceLamports": record.get("faceLamports"),
        "explorer": record.get("explorer"),
        "transfers": transfers,
        # How many signatures the file carries, counted from its grammar. The evidence count
        # was `1 if verified else 0` while the page printed three (feature 2 review).
        "signatureCount": _signature_count(record, transfers),
    }

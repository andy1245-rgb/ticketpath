#!/usr/bin/env python3
"""Publish `cap_hook` v2 to devnet under a NEW program id, and prove what it does there.

    TP_DEVNET_KEYPAIR=<funded authority> python3 tools/publish_v2_devnet.py \\
        --keypair "$TP_DEVNET_KEYPAIR" --deploy-keypair programs/cap_hook/target/deploy/v2-devnet-keypair.json

Why this file exists. `tools/publish_v2.py` proves the v2 program on a local
`solana-test-validator` that it starts, funds at genesis and kills; its artefact says `localOnly`,
and a local rehearsal is not evidence that the program works on a public cluster with real
account rent, real block times and its own clock. `tools/devnet_publish.py` publishes *v1* to
devnet and is frozen behind a guard so that the v1 program cannot be silently upgraded. So this
is the third thing: the v2 program, on devnet, under a program id that is neither v1's nor the
local one.

What it does not do, by construction:

* It does not edit or wrap `tools/publish_v2.py`. It imports it and subclasses `LocalProof`.
  Every proof assertion in this run is the parent's code — the same `_proof_a` to `_proof_g`,
  the same thirteen tag 4..6 proofs — reached by overriding the setup and teardown around them:
  `_toolchain`, `_keys`, `_start_validator`, `_stop`, `_deploy`, `_create_mint`,
  `_second_phase_context`, `_phase2`, `_transact_with`, `_attempt_with`, `_artefact`, and a
  recording wrapper on each of the twenty proofs. Measured on the parent at authoring time: 27
  references to `self.validator` / `self.ledger` / `self.keys`, across eight methods, and no
  `_proof_*` method holds one. Seven of the eight are overridden here; the eighth is `run`, whose
  single reference only formats `self.ledger` into a string `_artefact` does not read. So a proof
  cannot be quietly re-implemented here and drift from the one that was reviewed.
* It does not bypass `refuse_frozen_devnet_upgrade`. It calls it with the real program id and
  the real bytes before any deploy, and it refuses to proceed if its own target is the frozen
  devnet program, the frozen artefact, or the v1 deploy keypair.
* It does not use the faucet. The authority is a keypair the operator already funded, named by
  `--keypair` or by `TP_DEVNET_KEYPAIR`; every lamport this run spends is that account's.
* It never reads or prints key material. Keypairs are handled as paths and passed to
  `solana-keygen pubkey` and to `tools/solana_sign.py`, which signs out of process. The
  artefact carries public addresses only.
* It does not write `records/devnet-artefacts.json`, `records/onchain-v2.local.json`,
  `records/devnet-progress.json`, or the v1 deploy keypair. Those four are refused by resolved
  path at preflight, not by comment.

Two differences from the local parent, both deliberate and both visible in the artefact:

1. **The cluster persists.** A local run starts from a fresh ledger, so every run creates a
   new mint, a new record and a new set of forecasts. On devnet those accounts stay. This file
   therefore keeps a resume file (default `.swarm-runs/v2-devnet/resume.json`, under the
   directory that is already git-ignored, so no ignore rule has to change and nothing
   unignorable lands in a public tree). Every step transaction is keyed `<phase>:<step>` and its
   signature written the instant it exists, so a run killed between the send and the outcome asks
   the cluster whether it landed instead of sending a second ticket. Re-running finishes the run
   instead of paying rent for a second copy of it. A mint's address is written to the resume file
   *before* the mint is created, so a run killed between the two reuses the keypair it already
   made. Three kinds of transaction are not keyed that way and do not need to be: the deploy,
   which is judged by whether the program is executable; `create-token` and `create-account`,
   which are judged by whether the account exists; and `spl-token mint`, which is guarded by a
   recorded ticket count.
2. **Phase two is re-runnable, not resumable.** The parent runs the thirteen tag 4..6 proofs
   against a second validator with a fresh ledger. There is no second devnet to reset, so this
   file gives phase two its own fresh *mint* on the same cluster and re-runs the proofs from
   the top if it is interrupted. That costs about 0.02 SOL of rent on an interruption and
   cannot produce a mixed artefact, which is the trade this run wants.

`--inject` exists for the local rehearsal only and is armed by an explicit flag, never by the
environment: `after:keys`, `after:deploy`, `after:wire`, `after:artefact`, `after:<phase>:<step>`
for any transaction, and `rpc:<method>:<count>` for a transport fault. Fault injection against
devnet is not something this file prevents, so the flag also prints a line saying it fired.

Exit codes: 0 the run finished, 1 it failed, 2 it refused before writing anything, 130 killed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = Path(__file__).resolve().parent
for _path in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

# Both siblings are imported, and neither may run anything at import time. Check that before
# the import rather than after: an unguarded `__main__` would publish something at import.
for _sibling in ("devnet_publish.py", "publish_v2.py"):
    _source = (TOOLS_DIR / _sibling).read_text(encoding="utf-8")
    if 'if __name__ == "__main__":' not in _source:
        raise SystemExit(
            f"tools/{_sibling} has no __main__ guard, so importing it would run it. "
            "Nothing was published."
        )
    del _source

import devnet_publish as dp  # noqa: E402
import publish_v2 as pv  # noqa: E402

if Path(dp.__file__).resolve() != (TOOLS_DIR / "devnet_publish.py"):
    raise SystemExit(f"imported devnet_publish from {dp.__file__}, not the checked file")

# The guard this run must never bypass lives in the sibling, and the sibling in this tree is a
# newer revision than the last commit: the version under git carries no
# `refuse_frozen_devnet_upgrade` at all. Check for it here, at import, so a tree that has lost the
# guard says so in one sentence instead of failing at an AttributeError an hour into a run.
_MISSING = [
    name
    for name in ("FROZEN_DEVNET_PROGRAM", "refuse_frozen_devnet_upgrade", "v2_log_strings_in", "Refused")
    if not hasattr(dp, name)
]
if _MISSING:
    raise SystemExit(
        "tools/devnet_publish.py in this tree is missing "
        + ", ".join(_MISSING)
        + ": it is the older revision without the frozen-program guard. This tool refuses to run "
        "without that guard, and nothing was published."
    )
if not hasattr(pv, "LocalProof") or not hasattr(pv.LocalProof, "_proof_v2_score_miss"):
    raise SystemExit(
        "tools/publish_v2.py in this tree is older than the tag 4..6 proof suite this tool drives; "
        "nothing was published."
    )
if Path(pv.__file__).resolve() != (TOOLS_DIR / "publish_v2.py"):
    raise SystemExit(f"imported publish_v2 from {pv.__file__}, not the checked file")

# -- what is deployed, and where -------------------------------------------------

SO_PATH = REPO_ROOT / "programs" / "cap_hook" / "target" / "deploy" / "cap_hook.so"

#: v1's deploy keypair. Named so this file can refuse it; never opened, never a target.
V1_DEPLOY_KEYPAIR = REPO_ROOT / "programs" / "cap_hook" / "target" / "deploy" / "cap_hook-keypair.json"

#: This run's own keypair. A different file from v1's, and different from the one the local
#: publish reuses, so the devnet program id is its own. Ignored by git on three rules
#: (`*keypair*.json`, `**/target/deploy/`, and the denylist's shape check).
DEFAULT_DEPLOY_KEYPAIR = REPO_ROOT / "programs" / "cap_hook" / "target" / "deploy" / "v2-devnet-keypair.json"

#: The frozen devnet program. Public data; it is in `records/devnet-artefacts.json` and the
#: README. It is not a deploy target and this file refuses it twice: once by id, once by bytes
#: through `dp.refuse_frozen_devnet_upgrade`.
FROZEN_DEVNET_PROGRAM = dp.FROZEN_DEVNET_PROGRAM

#: Paths this run will not write, resolved. The first two are the frozen devnet record and the
#: resume file of the v1 publisher; the third is the local v2 proof, which a live test asserts
#: equals that run's return value, so overwriting it would break a test by succeeding.
FROZEN_WRITES = (
    REPO_ROOT / "records" / "devnet-artefacts.json",
    REPO_ROOT / "records" / "devnet-progress.json",
    REPO_ROOT / "records" / "onchain-v2.local.json",
    V1_DEPLOY_KEYPAIR,
)

DEFAULT_OUT = REPO_ROOT / "records" / "onchain-v2-devnet.json"
DEFAULT_RESUME = REPO_ROOT / ".swarm-runs" / "v2-devnet" / "resume.json"
KEYS_ROOT = REPO_ROOT / ".swarm-runs" / "v2-devnet" / "keys"

CHECKER_VERSION = "onchain-v2-devnet-2026-11-08"
RESUME_VERSION = 1

CLUSTER_URLS = {"devnet": "https://api.devnet.solana.com"}

#: Hosts a rehearsal may point at with `--rpc-url`. A local validator is the one case where the
#: cluster label and the endpoint legitimately disagree, and it is loopback: nothing leaves the
#: machine. Anything else is refused by `refuse_foreign_rpc`, because `--cluster devnet` is a
#: label and `--rpc-url` is where the lamports actually go.
LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1", "[::1]"})

#: The refusals this run must observe, each at least once. Phase one carries the four the
#: operator named plus the two policies; phase two carries the band, forecast and score rules.
#: A run that finishes without one of these is reported as failed here rather than as a shorter
#: artefact: "the code was not raised" and "the assertion was not written" are different facts
#: and only one of them is acceptable.
REQUIRED_CODES = {
    6010: "E_CAP_EXCEEDED",
    6021: "E_BELOW_FLOOR",
    6022: "E_BAND_UNSATISFIABLE",
    6023: "E_POLICY_INVALID",
    6024: "E_FORECAST_EXISTS",
    6025: "E_ALREADY_SCORED",
    6026: "E_NOT_AUTHORITY",
    6029: "E_FORECAST_BACKDATED",
    6030: "E_SCORE_BELOW_WIDTH",
    6032: "E_BAND_EMPTY",
    6033: "E_AS_OF_AHEAD",
}

EXIT_OK = 0
EXIT_FAIL = 1
EXIT_REFUSED = 2
EXIT_INTERRUPTED = 130

SOL = 1_000_000_000
DEFAULT_MIN_BALANCE_SOL = 3.0


class DevnetRefused(dp.PublishError):
    """A refusal from this file: the run stopped before it wrote anything to the cluster."""


# -- helpers --------------------------------------------------------------------


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(moment: datetime | None = None) -> str:
    return (moment or now()).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def relative(path: Path) -> str:
    """A repository-relative path, or the bare name for anything outside it.

    The artefact is published to a public repository, so it carries no home directory. This is
    the same rule `tools/publish_v2.py` applies to its own artefact, applied here because the
    file it writes is the one a stranger reads.
    """
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except (ValueError, OSError):
        return path.name


def explorer(kind: str, value: str) -> str | None:
    if not value:
        return None
    return f"https://explorer.solana.com/{kind}/{value}?cluster=devnet"


def resolve_guarded(path_text: str, what: str) -> Path:
    """A path the operator named, refused if it is one this run may not write.

    Four of them are frozen, and a fifth is refused for the deploy keypair alone: the keypair
    the local publish reuses. This run exists to put the program on a public cluster under an
    id of its own, and reusing the local id would make two records describe one address on two
    clusters -- the confusion `records/` exists to prevent.
    """
    path = Path(path_text).expanduser()
    if not path.is_absolute():
        path = (REPO_ROOT / path)
    resolved = path.resolve()
    for frozen in FROZEN_WRITES:
        if resolved == frozen.resolve():
            raise DevnetRefused(
                f"{what} resolves to {relative(frozen)}, which is frozen: it is either the v1 "
                "devnet record, the v1 publisher's resume file, the local v2 proof, or the v1 "
                "deploy keypair. Nothing was published and nothing was written."
            )
    if what == "the deploy keypair" and resolved == pv.DEPLOY_KEYPAIR.resolve():
        raise DevnetRefused(
            f"{what} is the keypair tools/publish_v2.py deploys under on a local validator, so "
            "this would be the same program id on a second cluster. Name a new keypair."
        )
    return path


def refuse_frozen_target(*, program_id: str, binary: bytes, source: str) -> None:
    """The frozen-program guard, called before any deploy and not switchable off.

    `dp.refuse_frozen_devnet_upgrade` is the checked function and it is called, not copied: a
    second implementation is a second rule, and the one that would rot is the copy. What is
    added here is the case its name does not cover -- this run's *own* target being the frozen
    program before a keypair is even derived.
    """
    if program_id == FROZEN_DEVNET_PROGRAM:
        raise DevnetRefused(
            f"REFUSING: the deploy keypair derives {program_id}, the frozen devnet program. "
            "A v2 deploy must be a new program id; nothing was sent."
        )
    dp.refuse_frozen_devnet_upgrade(program_id=program_id, binary=binary, source=source)


def cluster_for_rpc(rpc_url: str) -> str:
    """The cluster a recorded run belongs to, decided by the endpoint rather than the label."""
    return "localnet" if (urlsplit(rpc_url).hostname or "").lower() in LOOPBACK_HOSTS else "devnet"


def refuse_foreign_rpc(rpc_url: str) -> str:
    """Refuse to send anything anywhere but devnet, whatever `--cluster` says.

    Measured as a hole by review: `--cluster devnet --rpc-url https://api.mainnet-beta.solana.com`
    would deploy to mainnet and then write `"cluster": "devnet"` beside the mainnet URL, in a file
    this repository publishes. The label is not the guard; the endpoint is. Devnet's own URL and a
    loopback address (the rehearsal) are the only two endpoints this tool will talk to, and a URL
    carrying a username, a password, a query or a fragment is refused rather than trimmed.
    """
    from urllib.parse import urlsplit

    text = (rpc_url or "").strip()
    parts = urlsplit(text)
    if parts.scheme not in ("http", "https"):
        raise DevnetRefused(f"the RPC endpoint {text!r} is not an http(s) URL; nothing was sent")
    if parts.username or parts.password:
        raise DevnetRefused(
            "the RPC endpoint carries a username or password and this tool will not print or store "
            "one; pass a plain URL. Nothing was sent."
        )
    if parts.query or parts.fragment:
        raise DevnetRefused(f"the RPC endpoint {text!r} carries a query or fragment; pass a plain URL")
    host = (parts.hostname or "").lower()
    if host in LOOPBACK_HOSTS:
        return text
    if f"{parts.scheme}://{parts.netloc}".rstrip("/") == CLUSTER_URLS["devnet"]:
        return text
    named = {
        "api.mainnet-beta.solana.com": "mainnet-beta",
        "api.testnet.solana.com": "testnet",
    }.get(host)
    raise DevnetRefused(
        f"the RPC endpoint {host or text!r} is "
        + (f"{named}, and this tool writes only to devnet" if named else "not devnet")
        + ". A devnet deploy cannot be pointed at another cluster: pass "
        f"{CLUSTER_URLS['devnet']}, or a loopback address for a local rehearsal. Nothing was sent."
    )


def lamports_text(lamports: int) -> str:
    return f"{lamports / SOL:.9f} SOL"


# -- the resume file: what a run has already done --------------------------------


class Resume:
    """What this run has already done, on disk, written immediately after each step.

    Modelled on `dp.Progress`: `os.replace` so a crash leaves the old file or the new one and
    never half of one, mode 0600, a version and a cluster it refuses to mix. It differs in two
    ways and both are stated here rather than discovered later:

    * It lives under `.swarm-runs/`, which is already git-ignored, instead of `records/`. A
      resume file is a run's bookkeeping, not evidence, and the tree already has a place for
      that; adding a fifth ignore rule for a fifth file is how a tree starts to look unloved.
    * It allows lists, because a refusal's log lines are a list and they are the evidence that
      the refusal said what it was supposed to say. It still refuses an absolute path and the
      string "keypair" in any value, so a copy that escapes leaks addresses and no secret.
    """

    def __init__(self, path: Path, *, cluster: str, writable: bool = True):
        self.path = path
        self.cluster = cluster
        self.writable = writable
        self.state: dict = {}

    def load(self) -> "Resume":
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return self
        except (OSError, json.JSONDecodeError) as exc:
            raise DevnetRefused(
                f"the resume file {self.path.name} could not be read ({type(exc).__name__}); "
                "move it aside or run with --restart to start clean"
            ) from exc
        if not isinstance(loaded, dict) or loaded.get("version") != RESUME_VERSION:
            raise DevnetRefused(
                f"the resume file {self.path.name} is not version {RESUME_VERSION}; "
                "move it aside or run with --restart to start clean"
            )
        recorded = loaded.get("cluster")
        if recorded not in (None, self.cluster):
            raise DevnetRefused(
                f"the resume file {self.path.name} records a {recorded} run and this is "
                f"{self.cluster}; a mint from one cluster cannot be reused on another"
            )
        version = loaded.get("checkerVersion")
        if version not in (None, CHECKER_VERSION):
            # A resume file written by a different schema is not a file to guess at: the field
            # names and the meaning of `phase2Completed` can both move between revisions.
            raise DevnetRefused(
                f"the resume file {self.path.name} was written by {version} and this is "
                f"{CHECKER_VERSION}; finish it with that revision or run with --restart"
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

    def pending(self, key: str) -> dict | None:
        return (self.state.get("pending") or {}).get(key)

    def put_pending(self, key: str, *, signature: str, blockhash: str | None) -> None:
        """The signature, written the instant it exists and before the outcome is known.

        Same shape and same purpose as `devnet_publish.Progress.put_pending`, so the sibling's
        `pending_key` argument can be passed straight through to `dp.send_instructions`.
        """
        pending = dict(self.state.get("pending") or {})
        pending[key] = {"signature": signature, "blockhash": blockhash}
        self.put("pending", pending)

    def clear_pending(self, key: str) -> None:
        pending = dict(self.state.get("pending") or {})
        if pending.pop(key, None) is not None:
            self.put("pending", pending)

    def clear(self) -> None:
        self.state = {}
        self.path.unlink(missing_ok=True)

    def save(self) -> None:
        if not self.writable:
            return
        state = dict(self.state)
        state["version"] = RESUME_VERSION
        state["cluster"] = self.cluster
        state["checkerVersion"] = CHECKER_VERSION
        _assert_resumable(state)
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


def _assert_resumable(state: dict) -> None:
    """No absolute path, no key handle, no secret shape. Every value is walked."""

    def walk(value: object, where: str) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                walk(item, f"{where}.{key}")
        elif isinstance(value, list):
            for index, item in enumerate(value):
                walk(item, f"{where}[{index}]")
        elif isinstance(value, str):
            if value.startswith("/") or value.startswith("~"):
                raise DevnetRefused(f"the resume file would carry an absolute path in {where}")
            if "keypair" in value.lower():
                raise DevnetRefused(f"the resume file would carry a key handle in {where}")
        elif isinstance(value, (int, float, bool)) or value is None:
            return
        else:
            raise DevnetRefused(f"the resume file would carry a {type(value).__name__} in {where}")

    for name, item in state.items():
        walk(item, name)


# -- the run --------------------------------------------------------------------


class DevnetProof(pv.LocalProof):
    """`LocalProof`, with the cluster swapped underneath it and its proofs untouched.

    The parent's `run()` drives the sequence: toolchain, keys, "start the validator", deploy,
    wire, proofs a-g, phase two, artefact. Here "start the validator" means "check the cluster
    and adopt the funded authority", and "stop" means nothing at all. Everything between those
    two is the parent's code.
    """

    def __init__(
        self,
        *,
        cluster: str,
        rpc_url: str,
        authority: Path,
        deploy_keypair: Path,
        out: Path,
        resume: Resume,
        min_lamports: int,
        say=print,
    ):
        super().__init__(say=say)
        self.cluster = cluster
        self.remote_rpc = rpc_url
        self.authority = authority
        self.deploy_keypair_path = deploy_keypair
        self.artefact_path = out
        self.resume = resume
        self.min_lamports = min_lamports
        self.phase = 1
        # Stable across runs, unlike the parent's pid-suffixed directory: a mint keypair that a
        # killed run created must be the keypair the next run finds, or the mint is orphaned and
        # a second one is paid for.
        self.keys = KEYS_ROOT
        self.ledger = KEYS_ROOT / "no-ledger"  # nothing reads this; the parent's name is kept
        self.deploy_step: dict = {}
        self.balance_before: int | None = None
        self.balance_after: int | None = None
        self.sent = 0
        self.resumed: list[str] = []

    # -- the cluster, instead of a validator ------------------------------------

    @property
    def rpc(self) -> str:
        return self.remote_rpc

    def _toolchain(self) -> None:
        pv.LocalProof._toolchain(self)
        so_bytes = SO_PATH.read_bytes()
        # The guard, before a keypair exists and before anything is sent. `refuse_frozen_target`
        # is what stands between a mistyped --deploy-keypair and an upgrade of the frozen
        # program, and it reads the bytes rather than a name.
        markers = dp.v2_log_strings_in(so_bytes)
        if not markers:
            raise DevnetRefused(
                f"{relative(SO_PATH)} carries no v2-only log strings, so this run cannot prove "
                "it is deploying v2. Build it with cargo-build-sbf and run again."
            )
        self.say(f"toolchain: {relative(SO_PATH)} is the v2 build ({', '.join(markers)})")

    def _keys(self) -> None:
        """The operator's funded authority, adopted. No keypair is generated here."""
        if not self.authority.exists():
            raise DevnetRefused(
                "no keypair at the path named by --keypair/TP_DEVNET_KEYPAIR "
                f"({self.authority.name}, under {relative(self.authority.parent)}); this run does "
                "not create an authority and does not use the faucet"
            )
        self.keys.mkdir(parents=True, exist_ok=True)
        os.chmod(self.keys, 0o700)
        self.payer_keypair = self.authority
        self.payer = self._pubkey(self.authority)
        # Pinned, like the program id: review measured that a completed run resumed with a
        # different --keypair would replay every proof, send nothing signed by the new key, and
        # still write the new key as the artefact's authority beside the old one's signatures.
        recorded = self.resume.get("authority")
        if recorded and recorded != self.payer:
            raise DevnetRefused(
                f"this run's authority is {self.payer} and the resume file records {recorded}: the "
                "transactions already on the cluster were paid by the first. Point --keypair back "
                "at it, or run with --restart under a new program id."
            )
        if not recorded:
            self.resume.put("authority", self.payer)

        self.say(f"keys: authority {self.payer} (funded, from the operator; contents never read here)")
        dp.FAULTS.after_step("keys")

    def _start_validator(self) -> None:
        """Check the cluster, derive the program id, check the balance. Nothing is started."""
        refuse_foreign_rpc(self.rpc)
        health = dp.rpc(self.rpc, "getHealth", [], attempts=2)
        if health != "ok":
            raise DevnetRefused(f"{self.rpc} did not answer getHealth with ok: {health!r}")
        if self.phase == 2:
            # The parent gives phase two a directory named after this process id, which is fine for
            # a validator it is about to reset and wrong here: a repeat run would make a new buyer
            # keypair and two new token accounts, measured as two transactions the artefact does
            # not list because they are not proof steps. A stable directory makes a repeat run
            # send nothing at all.
            self.keys = KEYS_ROOT / "phase2"
        self.keys.mkdir(parents=True, exist_ok=True)
        os.chmod(self.keys, 0o700)
        self.ctx = dp.Context(
            cluster=self.cluster,
            rpc_url=self.rpc,
            keypair=self.authority,
            buyer_keypair=self.keys / "buyer.json",
            out=self.artefact_path,
            min_lamports=self.min_lamports,
            progress=self.resume,
        )
        self.ctx.say = self.say
        self.ctx.program_id = None

        if not self.deploy_keypair_path.exists():
            self._new_keypair(self.deploy_keypair_path)
            self.say(f"  deploy keypair created at {relative(self.deploy_keypair_path)} (0600, new program id)")
        else:
            # No `chmod` here. Review measured that `chmod` on a path the operator named would
            # change the mode of whatever that path is -- `--deploy-keypair README.md` made the
            # README 0600 and then failed. The mode of a file this run did not create is not this
            # run's to change; `preflight` refuses a path that is not a `.json` keypair instead.
            self.say(f"  deploy keypair reused at {relative(self.deploy_keypair_path)} (same program id as the last run)")
        self.deploy_keypair = self.deploy_keypair_path
        self.program_id = self._pubkey(self.deploy_keypair)
        if self.program_id == FROZEN_DEVNET_PROGRAM:
            raise DevnetRefused(
                f"the deploy keypair derives {self.program_id}, the frozen devnet program; "
                "nothing was sent"
            )
        self.ctx.program_id = self.program_id
        recorded = self.resume.get("programId")
        if recorded and recorded != self.program_id:
            raise DevnetRefused(
                f"the resume file records program {recorded} and this keypair derives "
                f"{self.program_id}; a resumed run cannot change the program id under the "
                "accounts it already created. Restore the keypair or run with --restart."
            )
        self.resume.put("programId", self.program_id)
        self.resume.put("deployAddress", self.program_id)

        # The starting balance is written to the resume file the first time it is read, and read
        # back on every later call. Measured on the devnet run: phase two calls this method again,
        # and re-reading there reported the balance after phase one, so the artefact claimed the
        # run spent 1.01 SOL when the authority had gone from 11.54 to 8.95. A spend that is only
        # counted from the middle is a spend the record hides.
        if not self.resume.get("balanceStart"):
            self.resume.put("balanceStart", self._balance(self.payer))
        self.balance_before = int(self.resume.get("balanceStart"))
        self.say(f"  authority balance {lamports_text(self.balance_before)} at the start of this lineage")
        if self.balance_before < self.min_lamports:
            raise DevnetRefused(
                f"{self.payer} holds {lamports_text(self.balance_before)} and this run needs "
                f"{lamports_text(self.min_lamports)} (--min-balance). There is no faucet step in "
                "this file on purpose; fund the account or lower the floor with a stated reason."
            )
        if dp.account_is_executable(self.rpc, self.program_id):
            self.say(f"  {self.program_id} is already deployed and executable")

    def _stop(self) -> None:
        """The cluster is not this process's to stop, and the parent's teardown would delete the
        phase-one keys directory a resumed run needs. Phase two's keys are throwaway by design:
        an interrupted phase two is re-run, not resumed."""
        return

    def _balance(self, address: str) -> int:
        result = dp.rpc(self.rpc, "getBalance", [address, {"commitment": "confirmed"}])
        return int((result or {}).get("value") or 0)

    # -- deploy: the parent's, with the guard in front and a read before it ----------

    def _deploy(self) -> None:
        source = relative(SO_PATH)
        binary = SO_PATH.read_bytes()
        refuse_frozen_target(program_id=self.program_id, binary=binary, source=source)

        # The bytes the cluster is running are pinned the first time this tool deploys, and every
        # later run compares them with the build on disk. Review measured the hole: `program.sha256`
        # was re-hashed from the file at artefact time, so a rebuild between two runs would write a
        # hash of bytes the cluster had never executed.
        sha = hashlib.sha256(binary).hexdigest()
        recorded_sha = self.resume.get("deployedSha256")

        if self._is_executable(self.program_id):
            if recorded_sha and recorded_sha != sha:
                raise DevnetRefused(
                    f"{self.program_id} is already deployed from sha256 {recorded_sha} and the build "
                    f"here is {sha}. The artefact would name bytes the cluster never ran. Restore the "
                    "build that was deployed, or deploy a new program id."
                )
            if not recorded_sha:
                # An existing program this tool did not deploy in this lineage: the build on disk
                # is the only candidate, so record it and say that it was not checked against the
                # cluster rather than implying that it was.
                self.resume.put("deployedSha256", sha)
                self.resume.put("deployedSha256Source", "the build on disk when this run adopted an existing program")
            recorded = self.resume.get("deploy") or {}
            self.deploy_step = {
                "signature": recorded.get("signature"),
                "slot": recorded.get("slot"),
                "blockTime": recorded.get("blockTime"),
                "error": None,
                "errorCode": None,
                "ok": True,
                "logs": [],
                "wallClock": recorded.get("wallClock") or iso(),
                "note": "already executable when this run started; no deploy was sent",
            }
            self.steps["deploy"] = self.deploy_step
            self.say(f"deploy: {self.program_id} was already executable; nothing sent")
            return

        self.say(f"deploy: {self.program_id} from {source} ({len(binary)} bytes, sha256 {sha[:16]}…)")
        last: Exception | None = None
        for attempt in range(1, 3):
            signature: str | None = None
            try:
                output = dp.run(
                    [
                        dp.which("solana") or "solana",
                        "--url", self.rpc,
                        "program", "deploy", str(SO_PATH),
                        "--program-id", str(self.deploy_keypair),
                        "--keypair", str(self.authority),
                    ],
                    timeout=dp.BOUND_DEPLOY,
                    what="solana program deploy",
                )
                signature = dp.last_base58(output)
            except dp.PublishError as exc:
                last = exc

            # The account is the authority on whether a deploy happened, not the CLI's exit code.
            # Review measured that the recovery branch used to fall through and raise "did not
            # land" after a deploy that had in fact landed; this branch records what it can see.
            if dp.wait_for_account(self.rpc, self.program_id, looks=8, interval=1.0) and self._is_executable(self.program_id):
                status = dp.confirm(self.rpc, signature) if signature else {"ok": True, "err": None, "slot": None}
                self.deploy_step = {
                    "signature": signature,
                    "slot": status.get("slot"),
                    "blockTime": self._transaction(signature).get("blockTime") if signature else None,
                    "error": None,
                    "errorCode": None,
                    "ok": True,
                    "logs": [],
                    "wallClock": iso(),
                    "note": None if signature else "the deploy became executable but printed no signature",
                }
                self.steps["deploy"] = self.deploy_step
                self.resume.put("deploy", self.deploy_step)
                self.resume.put("deployedSha256", sha)
                self.resume.put("deployedSha256Source", "the bytes this run sent")
                self.say(f"  deploy {signature or '(no signature)'} (slot {status.get('slot')}), executable")
                dp.FAULTS.after_step("deploy")
                return
            self.say(f"  deploy attempt {attempt} failed; {'retrying' if attempt == 1 else 'giving up'}")
            continue
        raise dp.PublishError(f"the deploy did not land in two attempts: {last}")

    # -- accounts: reused when the resume file knows them ---------------------------

    def _create_mint(self, label: str) -> str:
        """A fresh mint, or the one a previous run already made under this label.

        The address is written to the resume file *before* the create, so a run killed between
        the two leaves a keypair whose mint is known and one `spl-token create-token` away,
        rather than an orphaned mint and a second one paid for.
        """
        key = f"mint:{self.phase}:{label}"
        keypair = self.keys / f"{label}-mint.json"
        recorded = self.resume.get(key) or {}
        mint = recorded.get("address")

        if mint and dp.account_exists(self.rpc, mint):
            self.say(f"  mint {mint}: resumed from the resume file ({label})")
            self.resumed.append(f"mint:{self.phase}:{label}")
            return mint

        if mint:
            if not keypair.exists():
                raise DevnetRefused(
                    f"the resume file names mint {mint} for {label} but the keypair that created "
                    "it is gone from the run directory, so it cannot be finished or re-created"
                )
            self.say(f"  mint {mint}: recorded but absent on the cluster; creating it now")
        else:
            mint = self._pubkey(self._new_keypair(keypair))
            self.resume.put(key, {"address": mint, "created": False})

        output = dp.run(
            dp.spl(self.ctx, "create-token", "--decimals", "0", "--transfer-hook", self.program_id, str(keypair)),
            timeout=dp.BOUND_TOKEN,
            what="spl-token create-token",
        )
        found = dp.first_pubkey(output)
        if found and found != mint:
            raise pv.ProofFailed(f"spl-token created {found}, not the {mint} this run chose")
        if not dp.wait_for_account(self.rpc, mint, looks=20, interval=0.75):
            raise pv.ProofFailed(f"{mint} is not visible on the cluster after create-token")
        self.resume.put(key, {"address": mint, "created": True})
        self.say(f"  mint {mint}: Token-2022, 0 decimals, transfer hook -> {self.program_id}")
        return mint

    def _fund_tickets(self) -> None:
        key = f"tickets:{self.phase}"
        if self.resume.get(key):
            self.say(f"  {self.resume.get(key)} tickets already minted to {self.seller_ata} (resumed)")
            self.resumed.append(key)
            return
        pv.LocalProof._fund_tickets(self)
        self.resume.put(key, pv.TICKETS)

    def _wire(self) -> None:
        pv.LocalProof._wire(self)
        # The buyer is a signer of record: its tickets, its ATAs. A run resumed with a different
        # buyer would replay transfers paid by one account and sign the artefact with another.
        key = f"buyer:{self.phase}"
        recorded = self.resume.get(key)
        if recorded and recorded != self.buyer:
            raise DevnetRefused(
                f"this run derives buyer {self.buyer} and the resume file records {recorded}: the "
                "transfers already on the cluster were paid by the first. Restore keys/buyer.json "
                "or run with --restart."
            )
        if not recorded:
            self.resume.put(key, self.buyer)
        dp.FAULTS.after_step("wire")

    # -- every transaction, keyed and recorded -----------------------------------

    def _recover_pending(self, key: str) -> dict | None:
        """Ask the cluster about a transaction a killed run sent before it could record it.

        The window this closes, measured by review: the process dies between `sendTransaction`
        returning and the outcome being written, the next run finds no record, and re-sending a
        *transfer* moves a second ticket -- and the resend then fails 6009, which the artefact
        would file as a program refusal the program never made. The signature is written to the
        resume file the instant it exists, by the sibling's own `pending_key` path, so the next
        run asks whether it landed instead of acting again.
        """
        pending = self.resume.pending(key)
        if not pending:
            return None
        signature = pending["signature"]
        outcome = dp.recover_signature(self.rpc, signature, blockhash=pending.get("blockhash"))
        if outcome["state"] == "dropped":
            self.say(f"  {signature} was sent by a run that died and did not land; sending again")
            self.resume.clear_pending(key)
            return None
        status = {"ok": bool(outcome.get("ok")), "err": outcome.get("err"), "slot": outcome.get("slot")}
        detail = self._detail(signature, status)
        self.say(f"  {signature}: recovered from the run that died; the transaction is on the cluster")
        return detail

    def _transact_with(self, ctx, name: str, instructions: list, *, what: str, skip_preflight: bool = False) -> dict:
        key = f"{self.phase}:{name}"
        recorded = self.resume.get(key)
        if recorded:
            if recorded.get("error"):
                raise pv.ProofFailed(
                    f"step {key} is recorded as a FAILED transaction ({recorded.get('error')}); a "
                    "step that must succeed cannot be resumed from a refusal. Run with --restart."
                )
            self.steps[name] = recorded
            self.resumed.append(key)
            self.say(f"  {recorded['signature']} (slot {recorded.get('slot')}) resumed, not resent")
            return recorded
        recovered = self._recover_pending(key)
        if recovered is not None:
            if recovered.get("error"):
                raise pv.ProofFailed(
                    f"step {key} was sent by a run that died and the cluster refused it "
                    f"({recovered['error']}); a step that must succeed cannot be resumed from a refusal"
                )
            self.steps[name] = recovered
            self.resume.put(key, recovered)
            self.resume.clear_pending(key)
            self.resumed.append(key)
            return recovered
        signature, status = dp.send_instructions(
            ctx, instructions, what=what, skip_preflight=skip_preflight, pending_key=key
        )
        self.sent += 1
        detail = self._detail(signature, status)
        self.steps[name] = detail
        self.resume.put(key, detail)
        self.resume.clear_pending(key)
        dp.FAULTS.after_step(f"{self.phase}:{name}")
        return detail

    def _attempt_with(self, ctx, name: str, instructions: list, *, what: str) -> dict:
        key = f"{self.phase}:{name}"
        recorded = self.resume.get(key)
        if recorded:
            self.steps[name] = recorded
            self.resumed.append(key)
            self.say(f"  {recorded['signature']} (slot {recorded.get('slot')}) resumed refusal, not resent")
            return recorded
        recovered = self._recover_pending(key)
        if recovered is not None:
            self.steps[name] = recovered
            self.resume.put(key, recovered)
            self.resume.clear_pending(key)
            self.resumed.append(key)
            return recovered
        signature, status = dp.send_instructions(
            ctx, instructions, what=what, skip_preflight=True, allow_failure=True, pending_key=key
        )
        self.sent += 1
        detail = self._detail(signature, status)
        self.steps[name] = detail
        self.resume.put(key, detail)
        self.resume.clear_pending(key)
        dp.FAULTS.after_step(f"{self.phase}:{name}")
        return detail

    # -- proofs: recorded once, replayed verbatim on a resume ---------------------

    def _memo(self, name: str, run):
        """A proof that finished is not proved twice.

        The parent's proofs assert things that are only true on a first attempt: `_proof_a`
        requires `held_since_unix == 0` on a fresh record, and the rehearsal measured that a
        resumed run has already written that clock through an admitted transfer. Re-proving
        would therefore fail a run that is in fact correct, so a finished proof is stored and
        replayed -- the artefact then carries the assertion as it was made, on the run that made
        it, and never a weaker one re-asserted later.
        """
        key = f"proof:{self.phase}:{name}"
        recorded = self.resume.get(key)
        if recorded:
            # A replayed proof sends nothing, so `_transact_with` never runs and the step table
            # would come out empty -- and the artefact's refusal index with it. The steps this
            # proof recorded are stored beside it and put back, so the artefact from a resume is
            # the same artefact, not a shorter one.
            for step_name in self.resume.get(f"proofsteps:{self.phase}:{name}") or []:
                detail = self.resume.get(f"{self.phase}:{step_name}")
                if detail is not None:
                    self.steps[step_name] = detail
            self.resumed.append(key)
            self.say(f"  proof {name}: replayed from the resume file, not re-proved")
            return recorded
        before = set(self.steps)
        value = run()
        self.resume.put(f"proofsteps:{self.phase}:{name}", [n for n in self.steps if n not in before])
        self.resume.put(key, value)
        dp.FAULTS.after_step(f"{self.phase}:proof:{name}")
        return value

    def _proof_a(self):
        def run():
            return pv.LocalProof._proof_a(self)

        key = f"proof:{self.phase}:a"
        recorded = self.resume.get(key)
        if recorded:
            # The following proofs stage and transfer against this address, so it is restored
            # from the record rather than re-derived from an instruction that will not be sent.
            self.record = recorded["record"]
        return self._memo("a", run)

    def _proof_b(self):
        return self._memo("b", lambda: pv.LocalProof._proof_b(self))

    def _proof_c(self):
        return self._memo("c", lambda: pv.LocalProof._proof_c(self))

    def _proof_d(self):
        return self._memo("d", lambda: pv.LocalProof._proof_d(self))

    def _proof_e(self):
        return self._memo("e", lambda: pv.LocalProof._proof_e(self))

    def _proof_f(self):
        return self._memo("f", lambda: pv.LocalProof._proof_f(self))

    def _proof_g(self):
        return self._memo("g", lambda: pv.LocalProof._proof_g(self))

    def _proof_v2_band(self):
        return self._memo("v2.band", lambda: pv.LocalProof._proof_v2_band(self))

    def _proof_v2_forecast(self):
        return self._memo("v2.forecast", lambda: pv.LocalProof._proof_v2_forecast(self))

    def _proof_v2_forecast_exists(self):
        return self._memo("v2.forecastExists", lambda: pv.LocalProof._proof_v2_forecast_exists(self))

    def _proof_v2_score(self):
        return self._memo("v2.score", lambda: pv.LocalProof._proof_v2_score(self))

    def _proof_v2_already_scored(self):
        return self._memo("v2.alreadyScored", lambda: pv.LocalProof._proof_v2_already_scored(self))

    def _proof_v2_non_authority(self):
        return self._memo("v2.nonAuthority", lambda: pv.LocalProof._proof_v2_non_authority(self))

    def _proof_v2_unsatisfiable(self):
        return self._memo("v2.unsatisfiable", lambda: pv.LocalProof._proof_v2_unsatisfiable(self))

    def _proof_v2_empty_band(self):
        return self._memo("v2.emptyBand", lambda: pv.LocalProof._proof_v2_empty_band(self))

    def _proof_v2_as_of_ahead(self):
        return self._memo("v2.asOfAhead", lambda: pv.LocalProof._proof_v2_as_of_ahead(self))

    def _proof_v2_band_refused_normalised(self):
        return self._memo("v2.bandRefusedNormalised", lambda: pv.LocalProof._proof_v2_band_refused_normalised(self))

    def _proof_v2_backdated_forecast(self):
        return self._memo("v2.backdatedForecast", lambda: pv.LocalProof._proof_v2_backdated_forecast(self))

    def _proof_v2_score_below_width(self):
        return self._memo("v2.scoreBelowWidth", lambda: pv.LocalProof._proof_v2_score_below_width(self))

    def _proof_v2_score_miss(self):
        return self._memo("v2.scoreMiss", lambda: pv.LocalProof._proof_v2_score_miss(self))

    # -- phase two, on the same cluster ------------------------------------------

    def _second_phase_context(self):
        """The parent's second signer, with this run's cluster name rather than `localnet`."""
        ctx = dp.Context(
            cluster=self.cluster,
            rpc_url=self.rpc,
            keypair=self.ctx.buyer_keypair,
            buyer_keypair=self.ctx.buyer_keypair,
            out=self.artefact_path,
            progress=self.resume,
        )
        ctx.say = self.say
        return ctx

    def _set_forecast_instants(self) -> None:
        """The two as-of instants, restored rather than recomputed when this phase has run before.

        `LogForecast` writes a PDA keyed by its as-of, so an instant recomputed on a resumed run
        would name a different account than the transactions already sent: the artefact would
        carry signatures for one forecast and the address of another. Phase one records them and
        never uses them for state; phase two's restart clears them on the way in (see `_phase2`).
        """
        key = f"forecastAt:{self.phase}"
        recorded = self.resume.get(key) or {}
        if recorded.get("forecastAt") and recorded.get("forecastMissAt"):
            self.forecast_at = recorded["forecastAt"]
            self.forecast_miss_at = recorded["forecastMissAt"]
            self.say(f"  as-of instants restored from the resume file: {self.forecast_at}, {self.forecast_miss_at}")
            return
        pv.LocalProof._set_forecast_instants(self)
        self.resume.put(key, {"forecastAt": self.forecast_at, "forecastMissAt": self.forecast_miss_at})

    def _phase2(self) -> dict:
        self.phase = 2
        if not self.resume.get("phase2Completed"):
            # Phase two is re-runnable and not resumable, stated in the module docstring and
            # implemented here: an interrupted phase two is thrown away and started again on a
            # fresh mint, because half its proofs against a mint from a killed run is a mixed
            # record. Nothing on the cluster is touched; the old mint is simply not used again.
            # Every key phase two can write: the step keys (`2:name`), the proof keys and their
            # side tables (`proof:2:name`, `proofsteps:2:name`), and the four that are not steps.
            # Measured by review: leaving `proof:2:*` behind replayed the thirteen proofs against
            # a mint they were never made for, and then failed REQUIRED_CODES after paying rent.
            stale = [
                key
                for key in list(self.resume.state)
                if key.split(":")[0] == "2"
                or key.startswith(("proof:2:", "proofsteps:2:", "mint:2:", "tickets:2", "forecastAt:2", "buyer:2"))
            ]
            # The pending signatures live in one top-level dict keyed by `<phase>:<step>`, so the
            # phase-two half is dropped there rather than as a top-level key.
            pending = dict(self.resume.state.get("pending") or {})
            stale_pending = [key for key in pending if key.split(":")[0] == "2"]
            if stale_pending:
                for key in stale_pending:
                    pending.pop(key, None)
                self.resume.state["pending"] = pending
                stale.extend(f"pending:{key}" for key in stale_pending)
            if stale:
                for key in stale:
                    self.resume.state.pop(key, None)
                self.resume.save()
                self.say(f"phase 2: {len(stale)} unfinished step(s) from a killed run dropped; a fresh mint follows")
        self.say("phase 2: thirteen tag 4..6 proofs on a fresh mint of the same cluster")
        phase2 = pv.LocalProof._phase2(self)
        self.resume.put("phase2Completed", True)
        dp.FAULTS.after_step("phase2")
        return phase2

    # -- the artefact ------------------------------------------------------------

    def _refusals(self) -> list[dict]:
        """Every transaction that failed, with the code and the name it belongs to.

        Derived from the recorded steps rather than from a list written by hand, so a refusal the
        program emitted and this file forgot to name still appears here.
        """
        rows: list[dict] = []
        for phase, steps in ((1, self.steps), (2, getattr(self, "steps_v2", {}) or {})):
            for name, detail in steps.items():
                if not detail.get("error"):
                    continue
                code = detail.get("errorCode")
                rows.append(
                    {
                        "phase": phase,
                        "step": name,
                        "signature": detail.get("signature"),
                        "slot": detail.get("slot"),
                        "errorCode": code,
                        "errorName": pv.ERROR_NAMES.get(code),
                        "error": detail.get("error"),
                        "explorer": explorer("tx", detail.get("signature") or ""),
                    }
                )
        return sorted(rows, key=lambda row: (row["errorCode"] or 0, row["phase"], row["step"]))

    def _artefact(self, proofs: dict, *, phase1: dict, phase2: dict) -> dict:
        so_bytes = SO_PATH.read_bytes()
        self.balance_after = self._balance(self.payer)
        refusals = self._refusals()
        seen: dict[int, int] = {}
        for row in refusals:
            code = row["errorCode"]
            if code is not None:
                seen[code] = seen.get(code, 0) + 1
        missing = {code: name for code, name in REQUIRED_CODES.items() if code not in seen}
        if missing:
            raise pv.ProofFailed(
                "these refusals were required and did not appear in the run: "
                + ", ".join(f"{code} {name}" for code, name in sorted(missing.items()))
            )

        def legs(steps: dict) -> dict:
            return {
                name: {
                    "signature": detail.get("signature"),
                    "slot": detail.get("slot"),
                    "blockTime": detail.get("blockTime"),
                    "errorCode": detail.get("errorCode"),
                    "error": detail.get("error"),
                    "explorer": explorer("tx", detail.get("signature") or ""),
                }
                for name, detail in steps.items()
            }

        artefact = {
            "version": 1,
            "checkerVersion": CHECKER_VERSION,
            "cluster": self.cluster,
            "rpcUrl": self.rpc,
            "writtenAt": iso(),
            "startedAt": iso(self.started),
            "elapsedSeconds": round((now() - self.started).total_seconds(), 1),
            # A resumed run's clock is its own, not the lineage's: the first rebuild reported
            # "elapsed 2.3s" for a record made by 195 seconds of transactions. Rather than invent
            # a lineage start, the artefact says what the number measures and carries the earliest
            # block time in the record, which is a fact read from the steps.
            "firstTransactionAt": first_block_time(self.steps, getattr(self, "steps_v2", {}) or {}, {"deploy": self.deploy_step}),
            "elapsedBasis": "this process; every step carries the block time it landed at",
            "programId": self.program_id,
            "program": {
                "path": relative(SO_PATH),
                "bytes": len(so_bytes),
                # The hash of the bytes this run deployed, not of whatever is on disk when the
                # artefact is written: review measured that a rebuild between two runs would
                # otherwise publish a hash the cluster never executed.
                "sha256": self.resume.get("deployedSha256") or hashlib.sha256(so_bytes).hexdigest(),
                "sha256Source": self.resume.get("deployedSha256Source") or "the build on disk at artefact time; this run did not deploy it",
                "sha256MatchesBuildOnDisk": (self.resume.get("deployedSha256") or hashlib.sha256(so_bytes).hexdigest())
                == hashlib.sha256(so_bytes).hexdigest(),
            },
            "deployAddress": self.program_id,
            "authority": self.payer,
            "deploy": self.deploy_step,
            "mints": {
                "phase1": phase1["mint"],
                "phase2": phase2["mint"],
            },
            "record": phase1["record"],
            "extraMetas": phase1["extraMetas"],
            "seller": phase1["seller"],
            "buyer": phase1["buyer"],
            "buyerAta": phase1["buyerAta"],
            "arguments": {
                "faceLamports": pv.FACE,
                "capBps": pv.CAP_BPS,
                "bandLowLamports": pv.BAND_LOW,
                "jurisdiction": pv.JURISDICTION,
                "policy": pv.POLICY_CAPPED,
                "ceilingLamports": pv.CEILING,
            },
            "recordAtEnd": phase1["recordAtEnd"],
            "recordAtEndSlot": phase1["recordAtEndSlot"],
            "proofs": proofs,
            "proofs_v2": phase2["proofs"],
            "steps": legs(self.steps),
            "steps_v2": legs(getattr(self, "steps_v2", {}) or {}),
            "phase2": {
                key: value
                for key, value in phase2.items()
                if key not in ("proofs", "steps", "ledger", "pdas")
            },
            "refusals": refusals,
            "errorCodes": {
                "required": {str(code): name for code, name in sorted(REQUIRED_CODES.items())},
                "observed": {str(code): seen[code] for code in sorted(seen)},
                "missing": {},
            },
            "pdas": phase1["pdas"],
            "balances": {
                "authorityStart": self.balance_before,
                "authorityEnd": self.balance_after,
                "spentLamports": (self.balance_before - self.balance_after)
                if self.balance_before is not None and self.balance_after is not None
                else None,
                "basis": "the authority's balance when this run lineage first looked, against its "
                "balance now; a resumed run reports the whole lineage, not one process's share",
            },
            "resumedSteps": sorted(set(self.resumed)),
            "explorer": {
                "program": explorer("address", self.program_id),
                "mint": explorer("address", phase1["mint"]),
                "deploy": explorer("tx", (self.deploy_step or {}).get("signature") or ""),
            },
            "clusterFacts": {
                "token2022": dp.TOKEN_2022_PROGRAM,
                "frozenProgramId": FROZEN_DEVNET_PROGRAM,
                "frozenProgramIsDeployTarget": False,
                "frozenArtefact": "records/devnet-artefacts.json",
                "funding": "the operator's funded authority; no faucet, no airdrop",
            },
            "resume": {
                "path": relative(self.resume.path),
                "note": "a local run's bookkeeping, git-ignored, not part of this record",
            },
            "localOnly": self.cluster != "devnet",
        }
        _assert_publishable(artefact)
        return artefact


ARTEFACT_FIELDS = (
    "version",
    "checkerVersion",
    "cluster",
    "rpcUrl",
    "writtenAt",
    "startedAt",
    "elapsedSeconds",
    "elapsedBasis",
    "firstTransactionAt",
    "programId",
    "program",
    "deployAddress",
    "authority",
    "deploy",
    "mints",
    "record",
    "extraMetas",
    "seller",
    "buyer",
    "buyerAta",
    "arguments",
    "recordAtEnd",
    "recordAtEndSlot",
    "proofs",
    "proofs_v2",
    "steps",
    "steps_v2",
    "phase2",
    "refusals",
    "errorCodes",
    "pdas",
    "balances",
    "resumedSteps",
    "explorer",
    "clusterFacts",
    "resume",
    "localOnly",
)


def _assert_publishable(record: dict) -> None:
    """The same discipline as `dp._assert_public`, for a different record.

    A closed set of fields, no home path anywhere in any string, and the checks that would make
    the file dishonest if they failed: the program id is the one the deploy keypair derives, the
    artefact is not `localOnly`, and the frozen program id is the frozen one.
    """
    extra = set(record) - set(ARTEFACT_FIELDS)
    if extra:
        raise dp.PublishError(f"the artefact carries fields it should not: {sorted(extra)}")
    home = str(Path.home())
    for name, value in record.items():
        for text in _strings(value):
            if text.startswith(home) or text.startswith("/home/") or text.startswith("~"):
                raise dp.PublishError(f"the artefact carries an absolute path in {name}: {text!r}")
            if "keypair" in text.lower():
                raise dp.PublishError(f"the artefact carries a key handle in {name}: {text!r}")
    if record["cluster"] not in ("devnet", "localnet"):
        raise dp.PublishError(f"this artefact claims cluster {record['cluster']!r}, not devnet or localnet")
    # The cluster label and the endpoint that produced the record are checked as a pair: a loopback
    # run labelled devnet is the artefact review measured landing in records/ as if it were real.
    loopback = (urlsplit(record["rpcUrl"]).hostname or "").lower() in LOOPBACK_HOSTS
    if record["cluster"] == "devnet":
        if record["localOnly"]:
            raise dp.PublishError("a devnet artefact must not be marked localOnly")
        if loopback:
            raise dp.PublishError(f"a devnet artefact names a loopback endpoint {record['rpcUrl']!r}")
    else:
        if not record["localOnly"]:
            raise dp.PublishError("a localnet artefact must be marked localOnly")
        if not loopback:
            raise dp.PublishError(f"a localnet artefact names a non-loopback endpoint {record['rpcUrl']!r}")
    if record["clusterFacts"]["frozenProgramId"] != FROZEN_DEVNET_PROGRAM:
        raise dp.PublishError("the artefact's frozen program id is not the frozen program id")
    if record["programId"] == FROZEN_DEVNET_PROGRAM:
        raise dp.PublishError("the artefact's program id is the frozen devnet program")
    if record["program"].get("sha256MatchesBuildOnDisk") is False:
        raise dp.PublishError(
            "the artefact would name a program hash the cluster never ran: the build on disk has "
            "changed since the deploy"
        )


def first_block_time(*groups: dict) -> str | None:
    """The earliest block time among the recorded steps, as an instant, or None.

    Derived from the transactions themselves, so it cannot claim a start the record does not show.
    """
    times = [
        detail.get("blockTime")
        for group in groups
        for detail in (group or {}).values()
        if isinstance(detail, dict) and isinstance(detail.get("blockTime"), int)
    ]
    if not times:
        return None
    return datetime.fromtimestamp(min(times), tz=timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _strings(value: object):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def write_artefact(path: Path, record: dict) -> None:
    """Atomic, 0644, sorted: a reader never sees half a record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(record, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)


# -- preflight -------------------------------------------------------------------


def preflight(*, cluster: str, rpc_url: str, authority: Path, deploy_keypair: Path, out: Path, resume: Resume, min_lamports: int, say=print) -> dict:
    """Everything that can be checked without spending a lamport, checked first.

    A dry run stops here: it answers "would this run be allowed to send anything, and to what
    program id" and sends nothing. The three orderings matter: the guard is evaluated before the
    program id is printed, the balance before the deploy, and the resume file's cluster before
    anything is reused from it.
    """
    say(f"preflight: cluster {cluster} at {rpc_url}")
    for path, what in ((out, "the artefact"), (deploy_keypair, "the deploy keypair")):
        resolved = path.resolve()
        for frozen in FROZEN_WRITES:
            if resolved == frozen.resolve():
                raise DevnetRefused(f"{what} resolves to {relative(frozen)}, which is frozen")
    if not SO_PATH.exists():
        raise DevnetRefused(f"no program at {relative(SO_PATH)}; build it with cargo-build-sbf first")
    if deploy_keypair.exists() and deploy_keypair.suffix != ".json":
        raise DevnetRefused(
            f"the deploy keypair path {relative(deploy_keypair)} is not a .json keypair file; refusing "
            "to treat an arbitrary file as a key"
        )
    if deploy_keypair.is_dir() or out.is_dir() or resume.path.is_dir():
        raise DevnetRefused(
            "one of --out, --resume or --deploy-keypair names a directory; each must name a file"
        )
    # Two paths that collide are two writes to one file, and the second one silently wins: the
    # resume file is written after the artefact, so `--out` equal to `--resume` exits 0 with a
    # summary saying the artefact was written and a resume file where it should be.
    for other, what in ((resume.path, "--resume"), (deploy_keypair, "--deploy-keypair")):
        if out.resolve() == other.resolve():
            raise DevnetRefused(
                f"--out and {what} name the same file ({relative(out)}); each write would destroy the "
                "other. Name two paths."
            )
    binary = SO_PATH.read_bytes()
    markers = dp.v2_log_strings_in(binary)
    if not markers:
        raise DevnetRefused(
            f"{relative(SO_PATH)} carries no v2-only log strings, so this run cannot prove it is "
            "deploying v2"
        )
    say(f"preflight: program {relative(SO_PATH)}, {len(binary)} bytes, sha256 {hashlib.sha256(binary).hexdigest()}, v2 markers {', '.join(markers)}")
    if not authority.exists():
        raise DevnetRefused(
            "no authority keypair on the path named by --keypair/TP_DEVNET_KEYPAIR; this run does "
            "not create one and does not use the faucet"
        )
    for binary_name in ("solana", "spl-token", "solana-keygen"):
        if not dp.which(binary_name):
            raise DevnetRefused(f"{binary_name} is not on PATH")

    health = dp.rpc(rpc_url, "getHealth", [], attempts=2)
    if health != "ok":
        raise DevnetRefused(f"{rpc_url} did not answer getHealth with ok: {health!r}")
    authority_pubkey = dp.run(
        [dp.which("solana-keygen") or "solana-keygen", "pubkey", str(authority)],
        timeout=30,
        what="solana-keygen pubkey (authority)",
    ).strip().splitlines()[-1].strip()
    balance = int((dp.rpc(rpc_url, "getBalance", [authority_pubkey, {"commitment": "confirmed"}]) or {}).get("value") or 0)
    say(f"preflight: authority {authority_pubkey} holds {lamports_text(balance)}, floor {lamports_text(min_lamports)}")
    if balance < min_lamports:
        raise DevnetRefused(
            f"{authority_pubkey} holds {lamports_text(balance)} and this run needs "
            f"{lamports_text(min_lamports)} (--min-balance). No faucet step exists in this file."
        )

    if deploy_keypair.exists():
        program_id = dp.run(
            [dp.which("solana-keygen") or "solana-keygen", "pubkey", str(deploy_keypair)],
            timeout=30,
            what="solana-keygen pubkey (deploy)",
        ).strip().splitlines()[-1].strip()
    else:
        program_id = None
        say(f"preflight: no deploy keypair yet at {relative(deploy_keypair)}; the run will create one")
    if program_id == FROZEN_DEVNET_PROGRAM:
        raise DevnetRefused(
            f"the deploy keypair derives {program_id}, the frozen devnet program; nothing was sent"
        )
    if program_id:
        refuse_frozen_target(program_id=program_id, binary=binary, source=relative(SO_PATH))
        executable = dp.account_is_executable(rpc_url, program_id)
        say(
            f"preflight: deploy target {program_id}"
            + (" (already executable: no deploy will be sent)" if executable else " (not deployed yet)")
        )
    recorded = resume.get("programId")
    if recorded and program_id and recorded != program_id:
        raise DevnetRefused(
            f"the resume file records program {recorded} and this keypair derives {program_id}"
        )
    steps = [key for key in resume.state if key.split(":")[0] in ("1", "2")]
    say(f"preflight: resume file {relative(resume.path)} records {len(steps)} transaction step(s)")
    return {"programId": program_id, "authority": authority_pubkey, "balance": balance}


# -- CLI -------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="publish_v2_devnet.py",
        description="Publish the cap_hook v2 program to devnet under a new program id and prove it there.",
    )
    parser.add_argument("--cluster", default="devnet", choices=sorted(CLUSTER_URLS), help="the cluster this run may write to (devnet only)")
    parser.add_argument("--rpc-url", default=None, help="override the cluster's RPC endpoint")
    parser.add_argument("--keypair", default=os.environ.get("TP_DEVNET_KEYPAIR"), help="funded authority keypair; defaults to $TP_DEVNET_KEYPAIR. The path is used, the contents are never read or printed")
    parser.add_argument("--deploy-keypair", default=str(DEFAULT_DEPLOY_KEYPAIR), help="keypair the new program id comes from; must not be v1's")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="the artefact to write")
    parser.add_argument("--resume", default=str(DEFAULT_RESUME), help="the resume file (git-ignored directory)")
    parser.add_argument("--dry-run", action="store_true", help="check everything, send nothing")
    parser.add_argument(
        "--min-balance",
        type=float,
        default=DEFAULT_MIN_BALANCE_SOL,
        help="refuse below this many SOL (default %(default)s: the measured spend is about 2.9, "
        "being 0.78 of program rent, two 1 SOL transfers to non-authority signers, and account rent)",
    )
    parser.add_argument("--restart", action="store_true", help="delete the resume file first; the cluster is not touched")
    parser.add_argument("--inject", action="append", default=[], metavar="SPEC", help="after:<point> or rpc:<method>:<count>; for the local rehearsal only")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    say = lambda line="": (sys.stdout.write(str(line) + "\n"), sys.stdout.flush())
    started = time.monotonic()
    # What the refusal message may claim depends on how far the run got: before preflight ends,
    # nothing has been sent; after that, "nothing was sent" can be false.
    stage = "preflight"
    out = Path(args.out)

    try:
        if not args.keypair:
            raise DevnetRefused(
                "no authority keypair. Set TP_DEVNET_KEYPAIR or pass --keypair; this file does not "
                "create one and does not use the faucet."
            )
        # The endpoint decides the cluster, not the flag. A loopback endpoint is a local rehearsal
        # whatever `--cluster` says, and it is recorded as one: review measured a rehearsal artefact
        # labelled devnet with `localOnly: false` and a 127.0.0.1 URL, which the default `--out`
        # would have put in records/.
        rpc_url = refuse_foreign_rpc(args.rpc_url or CLUSTER_URLS[args.cluster])
        cluster = cluster_for_rpc(rpc_url)
        if cluster != args.cluster:
            say(f"cluster: the endpoint is {rpc_url}, so this run is recorded as {cluster}, not {args.cluster}")
        authority = resolve_guarded(args.keypair, "the authority keypair")  # refused only if frozen
        deploy_keypair = resolve_guarded(args.deploy_keypair, "the deploy keypair")
        out = resolve_guarded(args.out, "the artefact path")
        resume_path = resolve_guarded(args.resume, "the resume path")
        min_lamports = int(args.min_balance * SOL)

        if args.inject:
            dp.FAULTS.arm(args.inject)
            say(f"fault injection armed: {', '.join(args.inject)} (this run is a rehearsal; results are not evidence)")

        if args.restart and resume_path.exists() and not args.dry_run:
            if resume_path.is_dir():
                raise DevnetRefused(f"{relative(resume_path)} is a directory, not a resume file")
            resume_path.unlink()
            say(f"resume: deleted {relative(resume_path)}; the cluster is untouched")
        elif args.restart and args.dry_run:
            say("resume: --restart ignored under --dry-run; a dry run writes nothing and deletes nothing")

        resume = Resume(resume_path, cluster=cluster, writable=not args.dry_run).load()
        plan = preflight(
            cluster=cluster,
            rpc_url=rpc_url,
            authority=authority,
            deploy_keypair=deploy_keypair,
            out=out,
            resume=resume,
            min_lamports=min_lamports,
            say=say,
        )
        if args.dry_run:
            say("")
            say("dry run: nothing was sent and nothing was written.")
            say(f"  would deploy under {plan['programId'] or '<a new keypair>'}, prove a-g and the thirteen tag 4..6 proofs, and write {relative(out)}")
            return EXIT_OK

        proof = DevnetProof(
            cluster=cluster,
            rpc_url=rpc_url,
            authority=authority,
            deploy_keypair=deploy_keypair,
            out=out,
            resume=resume,
            min_lamports=min_lamports,
            say=say,
        )
        say("")
        stage = "run"
        artefact = proof.run()
        write_artefact(out, artefact)
        resume.put("completedAt", iso())
        dp.FAULTS.after_step("artefact")
        say("")
        for line in summary_lines(artefact, elapsed=time.monotonic() - started):
            say(line)
        return EXIT_OK
    except (dp.Refused, DevnetRefused) as exc:
        say("")
        say(str(exc))
        say("")
        if stage == "preflight":
            say("refused: nothing was sent and nothing was written (exit 2).")
        else:
            say("refused after the run started (exit 2). No artefact was written; what was sent is on  the cluster and in the resume file.".replace("  ", " "))
        return EXIT_REFUSED
    except dp.InjectedFault as exc:
        say("")
        say(str(exc))
        say("injected fault: this run stopped on purpose; the resume file holds what finished.")
        return EXIT_FAIL
    except pv.ProofFailed as exc:
        say("")
        say(f"PROOF FAILED: {exc}")
        say(_what_survived(out))
        return EXIT_FAIL
    except dp.PublishError as exc:
        say("")
        say(f"FAILED: {exc}")
        say(_what_survived(out))
        return EXIT_FAIL
    except KeyboardInterrupt:
        say("")
        say("interrupted; the resume file holds the steps that did finish.")
        return EXIT_INTERRUPTED


def _what_survived(out: Path) -> str:
    """Say what is actually on disk, rather than claiming nothing was written."""
    if out.exists():
        return (
            f"no new artefact was written. {out.name} already existed and is from an earlier run; "
            "the resume file holds the steps that did finish."
        )
    return "the artefact was not written; the resume file holds the steps that did finish."


def summary_lines(artefact: dict, *, elapsed: float) -> list[str]:
    """What was proved, where it landed, and every refusal with its code."""
    lines = [
        f"program {artefact['programId']} on {artefact['cluster']} ({artefact['program']['bytes']} bytes, sha256 {artefact['program']['sha256'][:16]}…)",
        f"  explorer {artefact['explorer']['program']}",
    ]
    deploy = artefact.get("deploy") or {}
    lines.append(f"  deploy {deploy.get('signature') or 'not sent (already executable)'} slot {deploy.get('slot')}")
    lines.append(f"  mint {artefact['mints']['phase1']} record {artefact['record']}")
    codes = artefact["errorCodes"]["observed"]
    refusals = artefact["refusals"]
    lines.append(f"  {len(refusals)} refusal(s), codes: " + ", ".join(f"{code}×{count}" for code, count in codes.items()))
    for row in refusals:
        lines.append(
            f"    {row['errorCode']} {row['errorName']} phase {row['phase']} {row['step']} "
            f"{row['signature']} slot {row['slot']}"
        )
    balances = artefact["balances"]
    lines.append(
        f"  authority {artefact['authority']} spent "
        f"{lamports_text(balances['spentLamports'] or 0)}; balance now {lamports_text(balances['authorityEnd'] or 0)}"
    )
    if artefact["resumedSteps"]:
        lines.append(f"  resumed {len(artefact['resumedSteps'])} step(s) from the resume file")
    lines.append(f"  elapsed {elapsed:.1f}s; artefact written")
    return lines


if __name__ == "__main__":
    sys.exit(main())

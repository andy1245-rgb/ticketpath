#!/usr/bin/env python3
"""Prove the flip tax is charged atomically at checkout, on a real local Solana validator.

This is a verification tool, not a product feature. It boots a throw-away
`solana-test-validator` on loopback, deploys the **existing** prebuilt
`programs/cap_hook/target/deploy/cap_hook.so` to it (never rebuilt here: its sha256 is
asserted first, in `main()` and again in `deploy`), creates the mints and records the sale
needs, and then drives eight legs through real transactions, reading every number back off
the cluster.

The sale it is proving is the one `market_swarm/flip_tax.py` builds:
`[cap_hook SetPendingPrice v2, System Transfer to the artist (artist fee), System Transfer to
the artist (flip tax), Token-2022 TransferChecked]` in ONE transaction with two signers, the
seller and the issuer. It is built by `flip_tax.sale_instructions`, which builds the fee half
through `artist_fee.sale_instructions`, so the legs test the product's own builder and not a
transcription of it.

What this tool adds over the module's own unit tests is the chain: exact lamport deltas from
`getBalance`, each transaction's own `meta.fee`, the two token balances, the 70-byte record
read back and decoded twice (here, and by `ticketpath.onchain.v2`), and the refusals with
their real signatures and instruction indices.

**What the chain can and cannot measure here.** The age that decides the rate is *supplied*.
A bounded local run cannot manufacture a 59-minute, one-hour or 30-day hold: measured on
agave 4.3.2, `solana-test-validator` with a warped slot leaves `Clock::unix_timestamp` at wall
clock, so the hook writes the wall clock and nothing here can make it write anything else.
Each leg therefore hands the builder the exact `held_since_unix` the record would carry for
that hold, and what the chain measures is the leg and the money: the instruction count, which
legs pay the artist, the exact lamport delta, or no tax leg at all. The rate-for-age curve is
a pure function of the supplied age and is measured as such in `market_swarm`'s unit tests.

Two things are deliberately not touched. There is no devnet URL in this file, no faucet, no
airdrop and no clone: Token-2022 is in the validator's own genesis on agave 4.3.2, so nothing
has to be fetched, and the issuer is funded at genesis with `--mint`. And the program is an
input: this file never edits it and never builds it.

Keys are generated fresh every run, under `tmp/flip-tax/keys/` at 0600, so the mint ids
differ between runs. The properties the legs assert do not.

Everything is bounded: `--deadline` (default 600s) covers the whole run, every child carries
a subprocess timeout, the deadline is re-checked between legs, the validator is killed on
every exit path (atexit plus SIGINT/SIGTERM/SIGHUP) and its ledger is removed.

**The harness is imported, not copied.** `LocalCluster`, `Checks`, `ProofError`, the four
instruction encoders, `resolve_signers`, `read_record`, `transaction_meta`, `get_balance`,
`token_amount`, `load_program_codes`, `free_block`, `port_is_closed`, `assert_loopback` and
`describe_error` all come from `tools/artist_fee_proof.py`, which is not edited by this run.
Its `Proof` class is *not* subclassed: `afp.Proof.__init__`, `boot()`, `make_mint()` and
`send()` read that module's `KEYS` and `WORK` globals directly (`KEYS / "issuer.json"`,
`out=WORK / "out"`, `shutil.rmtree(WORK)`), so a subclass would write its keys and its ledger
under `tmp/artist-fee/` and wipe that run's work directory at boot. The lifecycle steps are
therefore restated in `Proof` below against this tool's own paths under `tmp/flip-tax/`; the
pieces with no path in them are the imported ones.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
for _entry in (str(REPO_ROOT), str(TOOLS_DIR)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

import artist_fee_proof as afp  # noqa: E402
import devnet_publish as dp  # noqa: E402
from market_swarm import artist_fee as af  # noqa: E402
from market_swarm import flip_tax as ft  # noqa: E402
from ticketpath.onchain import v2 as onchain_v2  # noqa: E402

# -- the reusable harness, taken from `tools/artist_fee_proof.py` -------------------
#
# One set of wire encoders, one `Checks`, one validator teardown. `afp.gw` is the product's
# gateway as that module already imports it, so a concurrent edit to `market_swarm/gateway.py`
# reaches this run through the one path that module owns and not through a second import here.
Checks = afp.Checks
LocalCluster = afp.LocalCluster
ProofError = afp.ProofError
assert_loopback = afp.assert_loopback
describe_error = afp.describe_error
fmt = afp.fmt
free_block = afp.free_block
get_balance = afp.get_balance
ix_init_extra_metas = afp.ix_init_extra_metas
ix_init_record = afp.ix_init_record
ix_move = afp.ix_move
ix_stage = afp.ix_stage
load_program_codes = afp.load_program_codes
port_is_closed = afp.port_is_closed
read_record = afp.read_record
resolve_signers = afp.resolve_signers
say = afp.say
token_amount = afp.token_amount
transaction_meta = afp.transaction_meta
decode_record = afp.decode_record
ceiling_lamports = afp.ceiling_lamports
POLICY_CAPPED = afp.POLICY_CAPPED

# -- what exists, and is read rather than written ---------------------------------

CRATE = REPO_ROOT / "programs" / "cap_hook"
SO_PATH = CRATE / "target" / "deploy" / "cap_hook.so"
#: The same keypair `tools/artist_fee_proof.py` deploys from, and for the same reason recorded
#: there: v2 must never be deployed under the id the proven v1 build was published at, and
#: `devnet_publish.refuse_frozen_devnet_upgrade` exists to make that a hard error rather than a
#: convention. The id is therefore new per build.
PROGRAM_KEYPAIR = CRATE / "target" / "deploy" / "v2-keypair.json"
ERROR_SOURCE = CRATE / "src" / "error.rs"

#: The v2 build this proof is about. Asserted against the file's sha256 before a validator is
#: started, and again after the deploy. Never rebuilt. Pinned equal to the artist fee proof's
#: copy by `tests/test_flip_tax_proof.py`, so the two tools cannot describe different binaries.
SO_SHA256 = "de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac"

WORK = REPO_ROOT / "tmp" / "flip-tax"
#: Outside WORK on purpose: WORK is wiped at boot, and two runs must not both decide they are
#: the only one.
LOCK_PATH = REPO_ROOT / "tmp" / "flip-tax.lock"
KEYS = WORK / "keys"
LEDGER = WORK / "ledger"
MEASUREMENTS = WORK / "measurements.json"
REPORT = WORK / "REPORT.md"

# -- the sale's numbers: the brief's worked pair -----------------------------------

FACE = 1_000_000_000
CAP_BPS = 2_500
BAND_LOW = 0
JURISDICTION = "GB"

#: The artist fee the taxed sale carries, the same 500 bps finding 42 measured, so the two
#: contributions to the artist's balance are separable: 50,000,000 from the fee and
#: 150,000,000 from the tax at the full rate.
ARTIST_FEE_BPS = 500

#: The cap predicate is inclusive and in `u128` on chain, so `face * (10_000 + cap) / 10_000`
#: is the largest admissible staged price and one lamport over it must be refused.
CEILING = FACE * (10_000 + CAP_BPS) // 10_000  # 1_250_000_000

#: A mint per seller shape. `sale` carries every leg that must land and has its own tickets;
#: `underfunded` has its own seller so the tax it cannot pay is genuinely unpayable; `fresh`
#: is never moved, so its record's clock is still `UNKNOWN_HOLD` when leg 8 sells it.
TICKETS_SALE = 8
TICKETS_UNDERFUNDED = 1
TICKETS_FRESH = 1

#: Funded for the artist fee (50,000,000) and nowhere near the fee plus the tax
#: (200,000,000). Above the rent-exempt floor for a 0-data account and far above the
#: two-signature transaction fee, so the sale dies at the tax leg and not at the door: a leg
#: that fails at the fee charge executes nothing and would prove nothing about atomicity.
SELLER_UNDERFUNDED_LAMPORTS = 100_000_000

#: The four digits a two-signature legacy transaction costs on this cluster: 5,000 per
#: signature. Asserted rather than assumed, because every seller delta below is stated net of it.
TRANSACTION_FEE = 10_000

#: A fixed instant the pure tables are computed against, so a table is a number and not a
#: clock reading. The run's own `now` is `int(time.time())` at the moment each sale is built;
#: the rate is constant across any `now` for a hold that was handed in exactly, so the two
#: agree by construction and the tests can pin one.
REFERENCE_NOW = 1_800_000_000

# -- the leg table: prices, supplied ages, and the counts the builder must produce --------
#
# One row per assertion set. `1`..`8` are the brief's legs; the boundary and rounding legs
# have one row per side because each side is its own transaction, its own balance delta and
# its own instruction count. `5c` is the brief's own example price (19 lamports): it is
# computed and asserted here and deliberately *not* sent, because at 1500 bps it pays 2
# lamports -- not the 0 the example assumed -- and the pair that actually straddles the floor
# is 6 and 7. Keeping it in the table is what makes the correction a number in the report.

LEG_PRICES: dict[str, int] = {
    "1": FACE,
    "2a": FACE,
    "2b": FACE,
    "3": FACE,
    "4": FACE,
    "5a": 6,
    "5b": 7,
    "5c": 19,
    "6": FACE,
    "7": CEILING + 1,
    "8": FACE,
}

#: The age the checkout is handed for each row, in seconds. `None` is `flip_tax.UNKNOWN_HOLD`:
#: the record's clock was never written, which is not a time and is charged the full rate.
LEG_HELD_SECONDS: dict[str, int | None] = {
    "1": 3_540,        # 59 minutes: under the full-hold point, so the full rate
    "2a": 3_540,       # the boundary, supplied as exactly 3,540 s
    "2b": 3_600,       # the boundary, supplied as exactly 3,600 s
    "3": 2_592_000,    # the far boundary: 30 days, exactly
    "4": 3_540,        # the same event, toggled off
    "5a": 3_540,
    "5b": 3_540,
    "5c": 3_540,
    "6": 3_540,
    "7": 3_540,
    "8": None,         # the record was never written: unknown, and unknown pays full
}

#: What `flip_tax.sale_instructions` must return for each row, instruction by instruction.
#: Leg 4 is the no-tax path an event with no `flip_tax` block builds, so it is three.
LEG_INSTRUCTION_COUNTS: dict[str, int] = {
    "1": 4,
    "2a": 4,
    "2b": 4,
    "3": 3,
    "4": 3,
    "5a": 2,
    "5b": 3,
    "5c": 3,
    "6": 4,
    "7": 4,
    "8": 4,
}

#: Rows the run computes and asserts but never sends.
COMPUTED_ONLY = frozenset({"5c"})

LEG_TITLES: dict[str, str] = {
    "1": "fee and flip tax paid, price 1e9 at 500 bps plus the full 1500 bps rate",
    "2a": "boundary 59 min supplied (3,540 s): the full rate, and it lands",
    "2b": "boundary 1 h supplied (3,600 s): the full rate, and it lands",
    "3": "boundary 30 d supplied (2,592,000 s): no tax leg at all",
    "4": "toggle off: refused by the builder, and the no-tax sale pays the fee only",
    "5a": "rounding: price 6 pays a 0-lamport tax, so there is no tax leg",
    "5b": "rounding: price 7 pays 1 lamport of tax",
    "5c": "the brief's example corrected: price 19 pays 2 lamports, not 0 (computed, not sent)",
    "6": "underfunded seller: the tax leg fails the whole sale",
    "7": "over cap: refused 6010 at the move, both payments rolled back",
    "8": "the record is the clock: a real timestamp, and the unknown hold pays the full rate",
}

#: Every leg key the run must produce a result for. A missing key is a failure, not a shorter
#: list, and `tests/test_flip_tax_proof.py` pins it against the tables above.
LEG_KEYS = ("1", "2a", "2b", "3", "4", "5a", "5b", "5c", "6", "7", "8")


# -- pure arithmetic: the supplied age, the tables, and the builder -------------


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def supplied_held_since(now_unix: int, held_seconds: int) -> int:
    """The record clock that reads as a hold of `held_seconds` at `now_unix`.

    This is the only place the proof invents a number, and it invents the *instant*, not the
    rate: the hook writes `Clock::get()?.unix_timestamp` and a bounded run cannot move that
    clock backwards, so a leg that wants a 59-minute hold hands the builder the timestamp the
    record would carry for one. `flip_tax.hold_seconds` then reads back exactly
    `held_seconds`, which is what makes the supplied age an input and not a fudge.
    """
    if isinstance(held_seconds, bool) or not isinstance(held_seconds, int) or held_seconds < 0:
        raise ProofError(f"held_seconds {held_seconds!r}: a hold is a non-negative integer")
    if isinstance(now_unix, bool) or not isinstance(now_unix, int) or now_unix < held_seconds:
        raise ProofError(
            f"now_unix {now_unix!r} cannot carry a {held_seconds}s hold: the instant would be "
            "before 1970, which is `UNKNOWN_HOLD`'s neighbourhood and not a timestamp"
        )
    return now_unix - held_seconds


def planned_fees() -> dict[str, int]:
    """The artist fee each row carries, computed by the product's own arithmetic."""
    return {key: af.fee_lamports(price_lamports=price, fee_bps=ARTIST_FEE_BPS)
            for key, price in LEG_PRICES.items()}


def planned_taxes() -> dict[str, int]:
    """The flip tax each row carries, computed by `flip_tax.assess` against a fixed instant.

    Pinned in `tests/test_flip_tax_proof.py`, so a change to the schedule or to the floor moves
    the table and fails the test rather than quietly moving a leg.
    """
    taxes: dict[str, int] = {}
    for key, price in LEG_PRICES.items():
        held = LEG_HELD_SECONDS[key]
        held_since = ft.UNKNOWN_HOLD if held is None else supplied_held_since(REFERENCE_NOW, held)
        taxes[key] = ft.assess(
            price_lamports=price,
            held_since_unix=held_since,
            now_unix=REFERENCE_NOW,
        ).lamports
    return taxes


def build_leg(
    *,
    key: str,
    stage,
    move,
    seller: str,
    artist_wallet: str,
    now_unix: int,
    schedule: ft.FlipTaxSchedule = ft.DEFAULT_SCHEDULE,
) -> tuple:
    """One row's sale, from the product's own builder, so a leg tests the checkout.

    `flip_tax.sale_instructions` is what an event with a `flip_tax` block builds, and it builds
    the fee half through `artist_fee.sale_instructions`. Row `4` is the other path: an event
    with no `flip_tax` block never reaches the flip tax builder, so the checkout calls the
    artist fee builder and this row does too. The difference between the two rows is exactly
    what leg 4 measures.
    """
    if key not in LEG_PRICES:
        raise ProofError(f"{key}: no such row in the leg table")
    price = LEG_PRICES[key]
    held = LEG_HELD_SECONDS[key]
    held_since = ft.UNKNOWN_HOLD if held is None else supplied_held_since(now_unix, held)
    if key == "4":
        return af.sale_instructions(
            stage=stage,
            move=move,
            seller=seller,
            artist_wallet=artist_wallet,
            price_lamports=price,
            fee_bps=ARTIST_FEE_BPS,
        )
    return ft.sale_instructions(
        stage=stage,
        move=move,
        seller=seller,
        policy=ft.FlipTaxPolicy(artist_wallet=artist_wallet, enabled=True, schedule=schedule),
        price_lamports=price,
        held_since_unix=held_since,
        now_unix=now_unix,
        artist_fee=af.ArtistFeePolicy(artist_wallet=artist_wallet, fee_bps=ARTIST_FEE_BPS),
    )


def system_transfers(instructions) -> list[int]:
    """The lamports each System `Transfer` in a built sale carries, in order.

    Read out of the instructions the checkout built rather than off the cluster, because it is
    the *leg* this proves: a `System` transfer of 150,000,000 lamports to the artist either is
    in the transaction or is not, and a balance delta alone cannot say how many legs paid it.
    The tags are `artist_fee`'s: a u32 little-endian variant index (2 is `Transfer`) then a
    u64 amount.
    """
    amounts: list[int] = []
    for instruction in instructions:
        if instruction.program_id != dp.SYSTEM_PROGRAM:
            continue
        data = bytes(instruction.data)
        if len(data) != af.SYSTEM_TRANSFER_LEN:
            raise ProofError(f"a System instruction carries {len(data)} bytes, not a transfer")
        tag = int.from_bytes(data[:4], "little")
        if tag != af.SYSTEM_TAG_TRANSFER:
            raise ProofError(f"a System instruction carries tag {tag}, and 2 is Transfer")
        amounts.append(int.from_bytes(data[4:], "little"))
    return amounts


def so_digest(path: Path) -> str:
    """The sha256 of the program binary, or the word `missing` when there is none."""
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else "missing"


def verify_so_hash(digest: str) -> str:
    """Refuse to run against a binary this proof cannot describe.

    Called before a validator exists and again after the deploy, because the file is an input
    another run may rebuild underneath us and a proof of a binary nobody can name is not a
    proof.
    """
    if digest != SO_SHA256:
        raise ProofError(
            f"{SO_PATH.relative_to(REPO_ROOT)} is {digest}, and this proof is about {SO_SHA256}. "
            "Another run rebuilt it. This tool never rebuilds the program and will not describe "
            "a binary it cannot name."
        )
    return digest


def read_record_raw(url: str, address: str) -> bytes | None:
    """The record account's raw bytes, or None when it is not on the chain.

    `read_record` (imported) decodes the same account through this tool's hand-written decoder.
    Leg 8 needs the bytes themselves, to put them through `flip_tax.held_since_unix_from_record`
    and through `ticketpath.onchain.v2.decode_ticket_record` and show the two agree.
    """
    result = dp.rpc(url, "getAccountInfo", [address, {"encoding": "base64", "commitment": "confirmed"}])
    value = (result or {}).get("value")
    if not value:
        return None
    return base64.b64decode(value["data"][0])


# -- ports and the run ---------------------------------------------------------


class Proof:
    """The run: one throw-away validator, two signers, three mints, eleven assertion sets.

    The lifecycle is `tools/artist_fee_proof.py`'s, restated against this tool's own paths.
    That module's `Proof` reads its `KEYS`/`WORK` globals inside `__init__`, `boot()`,
    `make_mint()` and `send()`, so subclassing it would put this run's keys, ledger and output
    under `tmp/artist-fee/` and wipe the other tool's work directory at boot. Nothing about
    the chain work differs; only the paths do.
    """

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
        self.leg8_records: dict | None = None
        self.port_closed: bool | None = None
        self.validator_version = "unknown"

    # -- housekeeping ---------------------------------------------------

    def remaining(self) -> float:
        return self.deadline - (time.monotonic() - self.started)

    def check_deadline(self, where: str) -> None:
        if self.remaining() <= 0:
            raise ProofError(f"the {self.deadline:g}s deadline passed before {where}")

    def now(self) -> int:
        """The instant the checkout prices against: the wall clock, which the hook also writes."""
        return int(time.time())

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
        # One contiguous block for every port the validator binds: rpc, faucet, gossip and the
        # dynamic range. Probing them separately lets a later probe hand back a port inside the
        # block, and a busy gossip port is a hard panic at startup, not a retry.
        base = free_block(34)
        self.port = base
        # FAIL_CLOSED: the validator is the only long-running child, and `LocalCluster` kills
        # its process group from atexit and from SIGINT/SIGTERM/SIGHUP.
        self.validator = LocalCluster(
            ledger=LEDGER,
            port=base,
            faucet_port=base + 1,
            gossip_port=base + 2,
            dynamic_base=base + 3,
            dynamic_count=31,
            reset=True,
            # The issuer is funded at genesis: no faucet call, no airdrop, no devnet.
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
        self.so_sha = verify_so_hash(so_digest(SO_PATH))
        if not PROGRAM_KEYPAIR.exists():
            raise ProofError(f"no program keypair at {PROGRAM_KEYPAIR}")
        self.program_id = self.pubkey_of(PROGRAM_KEYPAIR)
        dp.run(
            [
                dp.which("solana") or "solana",
                # This `--url` is the validator this run just started on loopback, asserted by
                # `assert_loopback` above. It is not a cluster and cannot be made one.
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
        the mint.
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

    def sale(self, name: str, *, key: str) -> tuple:
        """One row's sale, from the product's builder, for the mint named `name`."""
        spec = self.mints[name]
        return build_leg(
            key=key,
            stage=self.stage(name, LEG_PRICES[key]),
            move=self.move(name),
            seller=spec["seller"],
            artist_wallet=self.artist,
            now_unix=self.now(),
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

    def signers_for(self, name: str) -> dict[str, Path]:
        """The two keypaths a sale of `name`'s ticket needs: its seller, and the record's authority."""
        return {self.mints[name]["seller"]: self.mints[name]["seller_key"],
                self.issuer: self.issuer_key}

    def send(self, *, payer: str, instructions, signers: dict[str, Path], what: str,
             skip_preflight: bool = True, allow_failure: bool = False) -> dict:
        """Compile, sign with exactly the signers the message asks for, send, read back.

        The signer set is parsed out of the compiled message (`afp.gw.signer_keys_from_message`)
        and the two sets must agree exactly: a missing path leaves a required signature empty,
        an extra one writes a signature the message has no slot for, and both are hard errors.
        Signatures are positional, so they are produced in the message's order rather than the
        dict's. Every leg is sent with `skipPreflight`, so a refusal lands as a failed
        transaction with its own signature instead of dying in simulation with none.
        """
        self.check_deadline(what)
        blockhash = dp.rpc(self.url, "getLatestBlockhash", [{"commitment": "confirmed"}])["value"]["blockhash"]
        message = dp.compile_message(payer, list(instructions), blockhash)
        required = afp.gw.signer_keys_from_message(message)
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

    # -- one leg on stdout, in the report, and in the measurements ------

    def record_leg(self, *, key: str, title: str, checks: Checks, measured: dict,
                   sent: dict | None = None, note: str = "") -> bool:
        entry = leg_entry(key=key, title=title, checks=checks, measured=measured,
                          sent=sent, note=note)
        self.results.append(entry)
        body = ", ".join(f"{name}={fmt(value)}" for name, value in measured.items())
        say(f"LEG {key} {'PASS' if entry['ok'] else 'FAIL'}  {title}: {body}")
        for item in entry["failed"]:
            say(f"    ! {item['check']}: got {item['got']}, wanted {item['want']}")
        return entry["ok"]

    # -- legs ------------------------------------------------------------

    def leg1(self) -> None:
        """Fee AND tax paid: 50,000,000 + 150,000,000 to the artist in one atomic transaction."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES["1"]
        fee = planned_fees()["1"]
        tax = planned_taxes()["1"]
        before = self.snapshot(name)
        instructions = self.sale(name, key="1")
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what="leg 1 sale with fee and tax")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.leg1_record = dict(rec) if rec else None
        self.snapshots.append(("after leg 1 (a complete taxed sale)", spec["record"], rec))

        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        transfers = system_transfers(instructions)
        checks = Checks()
        checks.eq("instruction count (stage, fee, tax, move)", len(instructions), 4)
        checks.eq("signer count", len(sent["signers"]), 2)
        checks.true("the two signers are the seller and the issuer",
                    set(sent["signers"]) == {spec["seller"], self.issuer},
                    ",".join(sent["signers"]))
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("the System legs, in order (fee then tax)", transfers, [fee, tax])
        checks.eq("the artist fee is 500 bps of the price", fee, 50_000_000)
        checks.eq("the flip tax is the full 1500 bps of the price", tax, 150_000_000)
        checks.eq("the transaction fee (two signatures)", sent["fee"], TRANSACTION_FEE)
        checks.eq("staging before the sale", (before["record"] or {}).get("pending_price_lamports"), 0)
        checks.eq("seller lamports delta (-(fee + tax + tx fee))",
                  seller_delta, -(fee + tax + sent["fee"]))
        # The exact number, not only the decomposition: 50,000,000 + 150,000,000 + 10,000. The
        # brief states it as -(200,000,010,000), which is three digits too long and larger than
        # the whole balance the seller was funded with; the chain measured this, and the note
        # below says so rather than the assertion being softened to fit either number.
        checks.eq("seller lamports delta, the exact number", seller_delta, -200_010_000)
        checks.eq("artist lamports delta (fee + tax)", artist_delta, 200_000_000)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="1", title=LEG_TITLES["1"], checks=checks, sent=sent,
            measured={"price": price, "fee_bps": ARTIST_FEE_BPS, "tax_bps": ft.DEFAULT_FULL_BPS,
                      "held_seconds_supplied": LEG_HELD_SECONDS["1"], "artist_fee": fee,
                      "flip_tax": tax, "tx_fee": sent["fee"], "seller_delta": seller_delta,
                      "artist_delta": artist_delta, "seller_tokens": after["seller_tokens"],
                      "buyer_tokens": after["buyer_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("the tax leg is instruction 2, between the fee that pays the artist and the move "
                  "the hook checks: one signature set, one blockhash, four instructions. The "
                  "brief states this delta as -(200,000,010,000); that is three digits too long "
                  "(the seller holds 3,000,000,000 in total) and the chain measured "
                  "-(200,010,000) = -(50,000,000 + 150,000,000 + 10,000), to the lamport. The "
                  "correction is stated here rather than absorbed by a weaker assertion"),
        )

    def leg2(self) -> None:
        """The boundary, both sides: 59 minutes and one hour both pay the full rate and land."""
        for key in ("2a", "2b"):
            self.boundary(key)

    def boundary(self, key: str) -> None:
        """One side of the hold boundary, its own transaction, its own balance delta."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES[key]
        held = LEG_HELD_SECONDS[key]
        fee = planned_fees()[key]
        tax = planned_taxes()[key]
        # One reading of the clock for both the supply and the read-back, so a second ticking
        # over between two calls cannot turn an exact hold into a hold plus one.
        now = self.now()
        before = self.snapshot(name)
        instructions = self.sale(name, key=key)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name),
                         what=f"leg {key} sale (held {held} s supplied)")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.snapshots.append((f"after leg {key} (held {held} s supplied)", spec["record"], rec))
        transfers = system_transfers(instructions)
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        read_back = ft.hold_seconds(supplied_held_since(now, held), now)
        checks = Checks()
        checks.eq("the supplied hold reads back as itself", read_back, held)
        checks.eq("the rate the schedule gives for that hold", ft.DEFAULT_SCHEDULE.bps_for(read_back),
                  ft.DEFAULT_FULL_BPS)
        checks.eq("the tax the builder charged", tax, 150_000_000)
        checks.eq("instruction count (stage, fee, tax, move)", len(instructions), 4)
        checks.eq("the System legs, in order (fee then tax)", transfers, [fee, tax])
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("artist lamports delta (fee + tax)", artist_delta, fee + tax)
        checks.eq("artist lamports delta, as the brief states it", artist_delta, 200_000_000)
        checks.eq("seller lamports delta", seller_delta, -(fee + tax + sent["fee"]))
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key=key, title=LEG_TITLES[key], checks=checks, sent=sent,
            measured={"price": price, "held_seconds_supplied": held,
                      "full_hold_seconds": ft.DEFAULT_FULL_HOLD_SECONDS,
                      "rate_bps": ft.DEFAULT_SCHEDULE.bps_for(held),
                      "artist_fee": fee, "flip_tax": tax, "instructions": len(instructions),
                      "artist_delta": artist_delta, "seller_delta": seller_delta,
                      "tx_fee": sent["fee"], "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("the boundary is inside the flat part of the schedule, which is the operator's "
                  "sentence read strictly: the falling line starts at one hour, so one hour is "
                  "the full rate and not the first point below it"),
        )

    def leg3(self) -> None:
        """Thirty days, exactly: the tax is 0, so no tax leg is built, and the sale still lands."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES["3"]
        fee = planned_fees()["3"]
        tax = planned_taxes()["3"]
        before = self.snapshot(name)
        instructions = self.sale(name, key="3")
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what="leg 3 sale (held 30 d supplied)")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.snapshots.append(
            ("after leg 3 (held 2,592,000 s supplied: no tax leg)", spec["record"], rec)
        )
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        transfers = system_transfers(instructions)
        checks = Checks()
        checks.eq("the tax at exactly 2,592,000 s", tax, 0)
        checks.eq("instruction count (stage, fee, move; no tax leg)", len(instructions), 3)
        checks.eq("the only System leg is the artist fee", transfers, [fee])
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("artist lamports delta (the fee only)", artist_delta, fee)
        checks.eq("seller lamports delta", seller_delta, -(fee + sent["fee"]))
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="3", title=LEG_TITLES["3"], checks=checks, sent=sent,
            measured={"price": price, "held_seconds_supplied": LEG_HELD_SECONDS["3"],
                      "zero_hold_seconds": ft.DEFAULT_ZERO_HOLD_SECONDS, "tax": tax,
                      "instructions": len(instructions), "artist_fee": fee,
                      "artist_delta": artist_delta, "tx_fee": sent["fee"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("a zero tax is no leg at all, for the same reason a zero fee is no leg: a "
                  "0-lamport transfer is indistinguishable in a signature from one that was "
                  "meant and paid nothing"),
        )

    def leg4(self) -> None:
        """The toggle: an off policy is refused at build time; the no-tax sale pays the fee only."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES["4"]
        fee = planned_fees()["4"]
        self.check_deadline("leg 4")
        refused = None
        try:
            # The same event, toggled off. This call is the checkout's, and it happens before a
            # blockhash is asked for, so a disabled policy cannot reach a signature.
            ft.sale_instructions(
                stage=self.stage(name, price),
                move=self.move(name),
                seller=spec["seller"],
                policy=ft.FlipTaxPolicy(artist_wallet=self.artist, enabled=False),
                price_lamports=price,
                held_since_unix=supplied_held_since(self.now(), LEG_HELD_SECONDS["4"]),
                now_unix=self.now(),
                artist_fee=af.ArtistFeePolicy(artist_wallet=self.artist, fee_bps=ARTIST_FEE_BPS),
            )
        except ft.FlipTaxError as exc:
            refused = str(exc)
        before = self.snapshot(name)
        instructions = self.sale(name, key="4")
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what="leg 4 sale (tax toggled off)")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.snapshots.append(("after leg 4 (the tax toggled off)", spec["record"], rec))
        transfers = system_transfers(instructions)
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        checks = Checks()
        checks.true("a disabled policy is refused by the builder", refused is not None,
                    refused or "it built the sale")
        checks.true("the refusal names the toggle", "enabled" in (refused or ""),
                    refused or "no refusal")
        checks.eq("instruction count (stage, fee, move; no tax leg)", len(instructions), 3)
        checks.eq("the only System leg is the artist fee (the tax is not mentioned)",
                  transfers, [fee])
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("artist lamports delta (the fee exactly)", artist_delta, fee)
        checks.eq("seller lamports delta", seller_delta, -(fee + sent["fee"]))
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="4", title=LEG_TITLES["4"], checks=checks, sent=sent,
            measured={"price": price, "artist_fee": fee, "flip_tax_if_it_had_been_on":
                      planned_taxes()["4"], "artist_delta": artist_delta,
                      "instructions": len(instructions), "tx_fee": sent["fee"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("the no-tax sale is built by the artist fee builder, which is the path an event "
                  "with no flip_tax block takes: nothing in the transaction names the tax"),
        )
        self.results[-1]["build_time_refusal"] = refused

    def leg5(self) -> None:
        """Rounding: 6 lamports pays a 0-lamport tax and 7 pays 1, so the leg count differs."""
        self.dust("5a")
        self.dust("5b")

    def dust(self, key: str) -> None:
        """One side of the rounding floor: the tax either buys a leg or it does not."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES[key]
        fee = planned_fees()[key]
        tax = planned_taxes()[key]
        before = self.snapshot(name)
        instructions = self.sale(name, key=key)
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what=f"leg {key} sale (price {price})")
        after = self.snapshot(name)
        rec = after["record"] or {}
        self.snapshots.append((f"after leg {key} (price {price})", spec["record"], rec))
        transfers = system_transfers(instructions)
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        checks = Checks()
        checks.eq("the tax the builder charged", tax, 0 if key == "5a" else 1)
        checks.eq("the artist fee at this price floors to 0", fee, 0)
        checks.eq("instruction count", len(instructions), LEG_INSTRUCTION_COUNTS[key])
        # The tax is the only payment either price makes, so the System legs are it and nothing
        # else: an empty list on the side whose tax floored to 0.
        checks.eq("the System legs (the tax, or nothing)", transfers, [tax] if tax else [])
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("artist lamports delta", artist_delta, tax)
        checks.eq("seller lamports delta", seller_delta, -(tax + sent["fee"]))
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], -1)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 1)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        measured = {"price": price, "artist_fee": fee, "flip_tax": tax,
                    "instructions": len(instructions), "artist_delta": artist_delta,
                    "seller_delta": seller_delta, "tx_fee": sent["fee"],
                    "seller_tokens": after["seller_tokens"],
                    "record_pending": rec.get("pending_price_lamports")}
        if key == "5b":
            # The pair's whole claim is that the instruction count is where the floor shows.
            a, b = LEG_INSTRUCTION_COUNTS["5a"], LEG_INSTRUCTION_COUNTS["5b"]
            checks.true("the instruction count differs between the two prices", a != b, f"{a} and {b}")
            checks.eq("and the difference is exactly the tax leg", b - a, 1)
            measured["instructions_at_price_6"] = a
            measured["tax_at_price_6"] = planned_taxes()["5a"]
        self.record_leg(
            key=key, title=LEG_TITLES[key], checks=checks, sent=sent, measured=measured,
            note=("floor never charges more than the stated rate; its cost is the long tail of "
                  "dust sales that pay the artist nothing at all, and the transaction shape "
                  "says so rather than implying a payment of zero"),
        )

    def leg5c(self) -> None:
        """The brief's own example, corrected: 19 lamports at 1500 bps pays 2, not 0."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES["5c"]
        tax = planned_taxes()["5c"]
        fee = planned_fees()["5c"]
        self.check_deadline("leg 5c")
        instructions = self.sale(name, key="5c")
        transfers = system_transfers(instructions)
        assessment = ft.assess(
            price_lamports=price,
            held_since_unix=supplied_held_since(REFERENCE_NOW, LEG_HELD_SECONDS["5c"]),
            now_unix=REFERENCE_NOW,
        )
        checks = Checks()
        checks.eq("the tax at 19 lamports and 1500 bps", tax, 2)
        checks.eq("... read off the assessment as well", assessment.lamports, 2)
        checks.eq("... at the full rate", assessment.bps, ft.DEFAULT_FULL_BPS)
        checks.eq("the artist fee at 19 lamports and 500 bps", fee, 0)
        checks.eq("instruction count (stage, tax, move)", len(instructions), 3)
        checks.eq("the only System leg is the tax", transfers, [tax])
        self.record_leg(
            key="5c", title=LEG_TITLES["5c"], checks=checks, sent=None,
            measured={"price": price, "tax": tax, "fee": fee,
                      "instructions": len(instructions), "sent": False,
                      "why": "the pair that straddles the floor is 6 and 7"},
            note=("the brief's example assumed price 19 builds no tax leg. It does: 19 * 1500 "
                  "// 10_000 is 2 lamports, so the leg exists and is asserted here. Nothing is "
                  "sent for this row, because 6 and 7 are where the floor is actually crossed"),
        )

    def leg6(self) -> None:
        """Atomicity: a seller who can pay the fee but not the fee plus the tax fails whole."""
        name = "underfunded"
        spec = self.mints[name]
        price = LEG_PRICES["6"]
        fee = planned_fees()["6"]
        tax = planned_taxes()["6"]
        before = self.snapshot(name)
        instructions = self.sale(name, key="6")
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what="leg 6 sale (underfunded)",
                         allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        err = sent["error"]
        self.snapshots.append(("after leg 6 (the tax could not be paid)", spec["record"], rec))
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("instruction count (stage, fee, tax, move)", len(instructions), 4)
        checks.eq("the seller's starting balance", before["seller_lamports"],
                  SELLER_UNDERFUNDED_LAMPORTS)
        checks.true("the seller can pay the fee and cannot pay the fee plus the tax",
                    before["seller_lamports"] >= fee
                    and before["seller_lamports"] < fee + tax,
                    f"seller {before['seller_lamports']}, fee {fee}, fee + tax {fee + tax}")
        checks.true("the transaction failed", not sent["ok"], err["text"])
        checks.eq("the failing instruction index (the tax leg)", err["index"], 2)
        # The index is the atomicity claim: 0 staged the price and 1 paid the fee, both before
        # the failure, so the runtime rolled a completed payment back rather than never running
        # it. The code is the System program's own and is reported, not asserted against a
        # memory: the cluster gave 1, `ResultWithNegativeLamports`.
        checks.eq("seller lamports delta (the transaction fee only)", seller_delta, -sent["fee"])
        checks.eq("artist lamports delta (the fee that ran was rolled back)", artist_delta, 0)
        checks.eq("seller tokens delta (the ticket did not move)",
                  after["seller_tokens"] - before["seller_tokens"], 0)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 0)
        checks.eq("the ticket is still in the seller's account", after["seller_tokens"], 1)
        checks.eq("record pending after the rollback", rec.get("pending_price_lamports"), 0)
        self.record_leg(
            key="6", title=LEG_TITLES["6"], checks=checks, sent=sent,
            measured={"price": price, "artist_fee": fee, "flip_tax": tax,
                      "fee_plus_tax": fee + tax,
                      "seller_before": before["seller_lamports"],
                      "shortfall": (fee + tax) - before["seller_lamports"],
                      "tx_fee": sent["fee"], "seller_delta": seller_delta,
                      "artist_delta": artist_delta, "err_index": err["index"],
                      "err_code": err["code"], "err_variant": err["variant"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=(f"the seller starts with {SELLER_UNDERFUNDED_LAMPORTS:,} lamports: enough for "
                  f"the {fee:,}-lamport fee at instruction 1, {fee + tax - SELLER_UNDERFUNDED_LAMPORTS:,} "
                  f"short of the {fee + tax:,} the two payments need, so the sale dies inside the "
                  "tax leg and takes the fee with it"),
        )

    def leg7(self) -> None:
        """Over the cap: refused 6010 at the move, after BOTH payments ran, and all rolled back."""
        name = "sale"
        spec = self.mints[name]
        price = LEG_PRICES["7"]
        fee = planned_fees()["7"]
        tax = planned_taxes()["7"]
        before = self.snapshot(name)
        instructions = self.sale(name, key="7")
        sent = self.send(payer=spec["seller"], instructions=instructions,
                         signers=self.signers_for(name), what="leg 7 sale (over cap)",
                         allow_failure=True)
        after = self.snapshot(name)
        rec = after["record"] or {}
        err = sent["error"]
        self.snapshots.append(("after leg 7 (over cap, refused)", spec["record"], rec))
        transfers = system_transfers(instructions)
        seller_delta = after["seller_lamports"] - before["seller_lamports"]
        checks = Checks()
        checks.eq("the ceiling", CEILING, ceiling_lamports(face_lamports=FACE, cap_bps=CAP_BPS))
        checks.eq("the price is one lamport over it", price, CEILING + 1)
        checks.eq("instruction count (stage, fee, tax, move)", len(instructions), 4)
        checks.eq("both payments are in the transaction", transfers, [fee, tax])
        checks.true("the transaction failed", not sent["ok"], err["text"])
        checks.eq("the refusal carries CapExceeded", err["code"], self.codes["CapExceeded"])
        checks.eq("the failing instruction index (the move)", err["index"], 3)
        checks.eq("artist lamports delta (both payments rolled back)",
                  after["artist_lamports"] - before["artist_lamports"], 0)
        checks.eq("seller lamports delta (the transaction fee only)", seller_delta, -sent["fee"])
        checks.eq("seller tokens delta", after["seller_tokens"] - before["seller_tokens"], 0)
        checks.eq("buyer tokens delta", after["buyer_tokens"] - before["buyer_tokens"], 0)
        checks.eq("record pending after the refusal", rec.get("pending_price_lamports"), 0)
        checks.true("the hook logged the cap refusal",
                    any(f"cap exceeded price={price}" in line for line in sent["logs"]),
                    "no matching log line")
        self.record_leg(
            key="7", title=LEG_TITLES["7"], checks=checks, sent=sent,
            measured={"price": price, "ceiling": CEILING,
                      "fee_that_was_rolled_back": fee, "tax_that_was_rolled_back": tax,
                      "artist_delta": 0, "seller_delta": seller_delta, "tx_fee": sent["fee"],
                      "err_code": err["code"], "err_index": err["index"],
                      "seller_tokens": after["seller_tokens"],
                      "record_pending": rec.get("pending_price_lamports")},
            note=("the tax leg is instruction 2 and it ran before the refusal at 3. The seller "
                  "is short only the transaction fee afterwards, so 187,500,000 lamports of tax "
                  "and 62,500,000 of fee were undone by the hook's own cap check"),
        )

    def leg8(self) -> None:
        """The record is the clock: a real stamp after a move, and the unknown hold pays full."""
        moved_name = "sale"
        fresh_name = "fresh"
        moved = self.mints[moved_name]
        fresh = self.mints[fresh_name]
        self.check_deadline("leg 8")
        now = self.now()

        # (a) After an admitted transfer, the hook has written its own wall clock.
        moved_raw = read_record_raw(self.url, moved["record"])
        if moved_raw is None:
            raise ProofError(f"no record at {moved['record']}")
        moved_decoded = decode_record(moved_raw)
        mine = ft.held_since_unix_from_record(moved_raw)
        theirs = onchain_v2.decode_ticket_record(moved_raw).held_since_unix

        # (b) A record whose mint has never moved: the clock was never written.
        fresh_raw = read_record_raw(self.url, fresh["record"])
        if fresh_raw is None:
            raise ProofError(f"no record at {fresh['record']}")
        fresh_decoded = decode_record(fresh_raw)
        fresh_held = ft.held_since_unix_from_record(fresh_raw)
        fresh_hold_seconds = ft.hold_seconds(fresh_held, now)
        fresh_assessment = ft.assess(
            price_lamports=LEG_PRICES["8"], held_since_unix=fresh_held, now_unix=now
        )
        before = self.snapshot(fresh_name)
        # Built from the record's own value, not from the table: this is the checkout's read.
        instructions = ft.sale_instructions(
            stage=self.stage(fresh_name, LEG_PRICES["8"]),
            move=self.move(fresh_name),
            seller=fresh["seller"],
            policy=ft.FlipTaxPolicy(artist_wallet=self.artist, enabled=True),
            price_lamports=LEG_PRICES["8"],
            held_since_unix=fresh_held,
            now_unix=now,
            artist_fee=af.ArtistFeePolicy(artist_wallet=self.artist, fee_bps=ARTIST_FEE_BPS),
        )
        sent = self.send(payer=fresh["seller"], instructions=instructions,
                         signers=self.signers_for(fresh_name),
                         what="leg 8 sale (a record whose clock was never written)")
        after = self.snapshot(fresh_name)
        rec = after["record"] or {}
        self.leg8_records = {"moved": moved_decoded, "fresh_before_sale": fresh_decoded}
        self.snapshots.append(("the record of a mint never moved (leg 8)", fresh["record"], fresh_decoded))
        self.snapshots.append(("after leg 8 (the unknown hold, charged full)", fresh["record"], rec))

        fee = planned_fees()["8"]
        tax = planned_taxes()["8"]
        transfers = system_transfers(instructions)
        artist_delta = after["artist_lamports"] - before["artist_lamports"]
        checks = Checks()
        checks.eq("the record is 70 bytes", len(moved_raw), ft.RECORD_LEN)
        checks.true("held_since_unix is not 0", mine != 0, str(mine))
        checks.true("held_since_unix is a real timestamp near now",
                    abs(now - mine) < 3_600, f"held {mine}, now {now}")
        checks.eq("flip_tax and this tool's decoder agree", mine, moved_decoded["held_since_unix"])
        checks.eq("flip_tax and ticketpath.onchain.v2 agree", mine, theirs)
        checks.eq("a fresh record's held_since_unix", fresh_held, ft.UNKNOWN_HOLD)
        checks.true("flip_tax.hold_seconds says the hold is unknown",
                    fresh_hold_seconds is None, str(fresh_hold_seconds))
        checks.eq("the unknown hold is charged the full rate", fresh_assessment.bps,
                  ft.DEFAULT_FULL_BPS)
        checks.eq("the unknown hold does not report an age", fresh_assessment.held_seconds, None)
        checks.eq("the tax the checkout charged it", fresh_assessment.lamports, tax)
        checks.eq("instruction count (stage, fee, tax, move)", len(instructions), 4)
        checks.eq("the System legs are the fee and the full-rate tax", transfers, [fee, tax])
        checks.true("the transaction succeeded", sent["ok"], sent["error"]["text"])
        checks.eq("artist lamports delta (fee + full-rate tax)", artist_delta, fee + tax)
        checks.eq("record pending after the sale", rec.get("pending_price_lamports"), 0)
        checks.true("the move wrote the record's clock", int(rec.get("held_since_unix") or 0) != 0,
                    str(rec.get("held_since_unix")))
        self.record_leg(
            key="8", title=LEG_TITLES["8"], checks=checks, sent=sent,
            measured={"record_len": len(moved_raw), "held_since_unix_moved": mine,
                      "held_since_v2_module": theirs,
                      "held_since_ticketpath_v2": theirs,
                      "fresh_record_held_since": fresh_held,
                      "fresh_hold_seconds": fresh_hold_seconds,
                      "fresh_bps": fresh_assessment.bps,
                      "fresh_tax": fresh_assessment.lamports,
                      "price": LEG_PRICES["8"], "artist_fee": fee,
                      "artist_delta": artist_delta,
                      "instructions": len(instructions),
                      "held_since_after_sale": rec.get("held_since_unix"),
                      "record_pending": rec.get("pending_price_lamports")},
            note=("0 is 'the clock was never written', not 1970: it is charged the full rate, so "
                  "an unset field is the most expensive way to sell and not the cheapest. The "
                  "decoders are two independent readers of the same 8 bytes"),
        )

    def run_legs(self) -> None:
        """Every leg, in order, each recorded whether it passes, fails, or raises."""
        plan = [
            ("1", self.leg1), ("2", self.leg2), ("3", self.leg3), ("4", self.leg4),
            ("5", self.leg5), ("5c", self.leg5c), ("6", self.leg6), ("7", self.leg7),
            ("8", self.leg8),
        ]
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


def leg_entry(*, key: str, title: str, checks: Checks, measured: dict,
              sent: dict | None = None, note: str = "") -> dict:
    """One leg's record: what it asserted, what it measured, and the transaction behind it.

    A function of its own so `tests/test_flip_tax_proof.py` can build a run's worth of entries
    without a validator and read the report the writer produces from them.
    """
    failed = checks.failed()
    sent = sent or {}
    return {
        "leg": key,
        "title": title,
        "ok": not failed,
        "measured": measured,
        "checks": checks.items,
        "failed": failed,
        "signature": sent.get("signature"),
        "signers": sent.get("signers"),
        "instructions": sent.get("instructions"),
        "err": (sent.get("error") or {}).get("text"),
        "err_index": (sent.get("error") or {}).get("index"),
        "err_code": (sent.get("error") or {}).get("code"),
        "failed_log": sent.get("failed_log"),
        "logs": sent.get("logs") or [],
        "note": note,
        #: A leg may carry more than one transaction (legs 2 and 5 are two apiece).
        "transactions": sent.get("transactions") or [],
    }


# -- the outputs ---------------------------------------------------------------

#: What is measured on this surface and what is supplied to it. The report quotes this in full,
#: because a reader who takes the boundary legs for a measurement of time passing would be
#: taking them for something this run cannot show.
MEASURED_AND_SUPPLIED = (
    "**What is measured, and what is supplied.** The hold -- the age that decides the rate -- "
    "is **supplied by this tool**. The local validator's clock cannot be moved backwards: "
    "measured on agave 4.3.2, `solana-test-validator --warp-slot 6480000` moves the slot and "
    "leaves `Clock::unix_timestamp` at wall clock, so a bounded run cannot manufacture a "
    "59-minute, one-hour or 30-day hold. Each leg therefore hands `flip_tax.sale_instructions` "
    "the exact `held_since_unix` a record would carry for that hold, and what the chain "
    "measures is the leg and the money: the instruction count, which legs pay the artist, the "
    "exact lamport delta, or no tax leg at all. The rate-for-age mapping is a pure function of "
    "the supplied age and is measured as such, over a dense sweep with both boundaries pinned, "
    "in `market_swarm`'s own unit tests. What is not measured here -- here or anywhere in this "
    "repository -- is an hour passing on a real chain."
)

HONESTY = (
    "The tax binds only sales that our app builds. The chain does not force it: a transaction "
    "can stage a price, move the ticket and pay no tax, and the hook admits it -- finding 42 "
    "leg 8 measured exactly that shape for the artist fee, and the tax rides in the same "
    "transaction as the fee, so it inherits the same limit. What the chain does force, on a "
    "record whose authority is the issuer, is that no ticket moves at all without the issuer's "
    "signature on the stage instruction, and that stage is what the checkout prices."
)


def measurements(proof: Proof, *, passed: int, total: int, failures: list[str]) -> dict:
    """Everything the run measured, in a shape a later reader can diff against a rerun."""
    return {
        "tool": "tools/flip_tax_proof.py",
        "written_at": now_iso(),
        "surface": "solana local validator (loopback), the prebuilt cap_hook.so",
        "validator": proof.validator_version,
        "rpc_url": proof.url,
        "rpc_port_closed_after": proof.port_closed,
        "program_id": proof.program_id,
        "program_so": {"path": str(SO_PATH.relative_to(REPO_ROOT)), "sha256": proof.so_sha},
        "error_codes": proof.codes,
        "constants": {
            "face_value_lamports": FACE, "cap_bps": CAP_BPS, "ceiling_lamports": CEILING,
            "band_low_lamports": BAND_LOW, "jurisdiction": JURISDICTION,
            "artist_fee_bps": ARTIST_FEE_BPS, "record_len": ft.RECORD_LEN,
            "held_since_unix_offset": ft.HELD_SINCE_UNIX_OFFSET,
            "schedule": ft.DEFAULT_SCHEDULE.to_dict(),
            "reference_now": REFERENCE_NOW,
            "transaction_fee_two_signatures": TRANSACTION_FEE,
            "seller_underfunded_lamports": SELLER_UNDERFUNDED_LAMPORTS,
        },
        "planned_fees": planned_fees(),
        "planned_taxes": planned_taxes(),
        "leg_prices": LEG_PRICES,
        "leg_held_seconds": dict(LEG_HELD_SECONDS),
        "leg_instruction_counts": LEG_INSTRUCTION_COUNTS,
        "wallets": {"issuer": proof.issuer, "artist": proof.artist},
        "mints": {
            name: {key: (None if isinstance(value, Path) else value)
                   for key, value in spec.items() if key != "seller_key"}
            for name, spec in proof.mints.items()
        },
        "legs": proof.results,
        "record_snapshots": [
            {"when": when, "record": address, "state": state}
            for when, address, state in proof.snapshots
        ],
        "leg8_records": proof.leg8_records,
        "result": {"passed": passed, "total": total, "failures": failures},
        "measured_and_supplied": MEASURED_AND_SUPPLIED,
        "honesty": HONESTY,
        "keys": ("generated fresh on every run under tmp/flip-tax/keys/ at 0600: the mint ids "
                 "differ between runs, the asserted properties do not"),
    }


def write_measurements(proof: Proof, *, passed: int, total: int, failures: list[str],
                       path: Path = MEASUREMENTS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(measurements(proof, passed=passed, total=total, failures=failures), indent=2) + "\n",
        encoding="utf-8",
    )


def report_text(proof: Proof, *, passed: int, total: int, failures: list[str]) -> str:
    """The run's report. A function of the run so a test can read it without a validator."""
    version = getattr(proof, "validator_version", "unknown")
    lines = [
        "# The flip tax at checkout — local validator proof",
        "",
        f"Written {now_iso()} by `tools/flip_tax_proof.py`.",
        "",
        "**This ran on a LOCAL `solana-test-validator`.** Nothing here touched devnet: no `--url`",
        "other than the validator's own loopback RPC, no faucet, no airdrop, no clone. The",
        "validator's ledger was deleted when the run ended.",
        "",
        f"- Validator: `{version}`",
        f"- RPC: `{proof.url}`, closed after the run: **{proof.port_closed}**",
        f"- Program id: `{proof.program_id}` (deployed from `v2-keypair.json`, never rebuilt)",
        f"- Program `.so` sha256: `{proof.so_sha}`",
        f"- Issuer (the record's authority): `{proof.issuer}`",
        f"- Artist wallet (fee and tax both pay it): `{proof.artist}`",
        f"- Result: **{'PASS' if not failures else 'FAIL'} {passed}/{total}**",
        "",
        "Keys are generated fresh on every run under `tmp/flip-tax/keys/` (0600), so the mint",
        "ids differ between runs. The properties the legs assert do not.",
        "",
        "## What is measured and what is supplied",
        "",
        MEASURED_AND_SUPPLIED,
        "",
        "## The record and the sale",
        "",
        f"Face `{FACE:,}`, cap `{CAP_BPS}` bps → ceiling `{CEILING:,}`, band_low `{BAND_LOW}`,",
        f"jurisdiction `{JURISDICTION}`, artist fee `{ARTIST_FEE_BPS}` bps, flip tax",
        f"`{ft.DEFAULT_SCHEDULE.full_bps}` bps while the hold is under",
        f"`{ft.DEFAULT_SCHEDULE.full_hold_seconds:,}` s and falling to 0 at",
        f"`{ft.DEFAULT_SCHEDULE.zero_hold_seconds:,}` s.",
        "",
        "One transaction holds four instructions — `SetPendingPrice`, the System `Transfer` of",
        "the artist fee, the System `Transfer` of the flip tax, the Token-2022 `Move` — and two",
        "signatures, because the record's authority is the mint's authority and the stage",
        "requires its signature. Every leg was sent with `skipPreflight`, so a refusal lands as",
        "a failed transaction with its own signature instead of dying in simulation.",
        "",
        "| mint | mint id | record | seller | buyer | face at birth | held at birth |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, spec in proof.mints.items():
        born = spec.get("record_at_birth") or {}
        lines.append(
            f"| {name} | `{spec['mint']}` | `{spec['record']}` | `{spec['seller']}` | "
            f"`{spec['buyer']}` | {born.get('face_value_lamports')} | "
            f"{born.get('held_since_unix')} |"
        )

    lines += [
        "",
        "## The leg table",
        "",
        "| row | price (lamports) | age supplied (s) | artist fee | flip tax | instructions | sent |",
        "|---|---|---|---|---|---|---|",
    ]
    fees = planned_fees()
    taxes = planned_taxes()
    for key in LEG_PRICES:
        held = LEG_HELD_SECONDS[key]
        age = "unknown (record never written)" if held is None else f"{held:,}"
        lines.append(
            f"| {key} | {LEG_PRICES[key]:,} | {age} | {fees[key]:,} | {taxes[key]:,} | "
            f"{LEG_INSTRUCTION_COUNTS[key]} | {'no' if key in COMPUTED_ONLY else 'yes'} |"
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

    lines += ["## The refusals, in the cluster's own words", ""]
    for result in proof.results:
        if result["leg"] not in ("6", "7"):
            continue
        lines += [
            f"**Leg {result['leg']} — {result['title']}**",
            "",
            f"- signature: `{result['signature']}`",
            f"- `meta.err` verbatim: `{result['err']}`",
            f"- failing instruction index: `{result['err_index']}`, code: `{result['err_code']}`",
            f"- the failing program's log line: `{result['failed_log']}`",
            "",
        ]
    for result in proof.results:
        if result.get("build_time_refusal"):
            lines += [
                f"- Leg {result['leg']}'s other half, refused by the checkout before a blockhash "
                f"was fetched: `{result['build_time_refusal']}`",
                "",
            ]

    lines += ["## The record is the clock", ""]
    records = getattr(proof, "leg8_records", None) or {}
    if records:
        lines += [
            "After an admitted transfer, the 70-byte record read back and decoded twice:",
            "",
            "```json",
            json.dumps(records.get("moved"), indent=2, sort_keys=True),
            "```",
            "",
            "and the record of a mint that has never been moved:",
            "",
            "```json",
            json.dumps(records.get("fresh_before_sale"), indent=2, sort_keys=True),
            "```",
            "",
        ]
    lines += [
        "`held_since_unix` is the hook's own wall clock, written on every admitted transfer",
        "(`programs/cap_hook/src/lib.rs`, step 7). On a mint that has never moved it is `0`,",
        "which `flip_tax` reads as *unknown* and charges the full rate — never as 1970, which",
        "would make an unset field the cheapest way to sell. The two decoders (`flip_tax`'s",
        "byte slice and `ticketpath.onchain.v2`'s layout-driven reader) are independent readers",
        "of the same 8 bytes and leg 8 asserts they agree.",
        "",
        "## What this proves, and what it does not",
        "",
        HONESTY,
        "",
        "What was measured on this surface: every lamport delta above, each transaction's own",
        "`meta.fee`, both token balances, the decoded record, and each refusal's code and",
        "instruction index. What was **not** measured here: the passage of time (see above), a",
        "real buyer's payment of the sale price (no such thing exists in this design), and any",
        "cluster other than this one.",
        "",
        "## Notes a reader should not have to rediscover",
        "",
        f"- The underfunded seller is funded with {SELLER_UNDERFUNDED_LAMPORTS:,} lamports. It",
        f"  can pay the {planned_fees()['6']:,}-lamport artist fee and cannot pay the",
        f"  {planned_fees()['6'] + planned_taxes()['6']:,} the fee and the tax need together, so",
        "  the sale dies at the tax leg and not at the door; a transaction that fails at the fee",
        "  charge executes nothing and would prove nothing about atomicity.",
        f"- The over-cap leg (price {CEILING + 1:,}) pays a {planned_fees()['7']:,}-lamport fee at",
        f"  instruction 1 and a {planned_taxes()['7']:,}-lamport tax at instruction 2, and is",
        "  refused at instruction 3. The seller's balance afterwards is short only the",
        "  transaction fee, which is the rollback measured on a balance rather than argued.",
        f"- Leg 1's seller delta is stated in the brief as -(200,000,010,000). That number is",
        f"  three digits too long -- the seller is funded with 3,000,000,000 lamports in total --",
        f"  and the cluster measured -({planned_fees()['1']:,} + {planned_taxes()['1']:,} +",
        f"  {TRANSACTION_FEE:,}) = -{planned_fees()['1'] + planned_taxes()['1'] + TRANSACTION_FEE:,}.",
        "  The assertion is on the measured number and the decomposition, and the brief's literal",
        "  is corrected here rather than quietly satisfied by a weaker check.",
        "- The program is deployed from `programs/cap_hook/target/deploy/v2-keypair.json`, not",
        "  from the frozen devnet keypair: `tools/devnet_publish.py` refuses to put v2 under that",
        "  id, and this tool follows the same rule rather than restating it.",
        "- No file in the repository was edited by this run. The ledger and the keys are under",
        "  the git-ignored `tmp/flip-tax/`.",
        "",
    ]
    if failures:
        lines += ["## Failures", ""] + [f"- {name}" for name in failures] + [""]
    return "\n".join(lines) + "\n"


def write_report(proof: Proof, *, passed: int, total: int, failures: list[str],
                 path: Path = REPORT) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_text(proof, passed=passed, total=total, failures=failures),
                    encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deadline", type=float, default=600.0,
                        help="seconds for the whole run (default 600)")
    args = parser.parse_args(argv)

    # One run at a time. Two instances share `tmp/flip-tax/`, and the second one's `rmtree`
    # lands inside the first one's validator startup.
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    lock = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        say(f"another flip_tax_proof run holds {LOCK_PATH.name}; not starting a second one")
        lock.close()
        return 2

    # The program is an input. Checked before a validator is started, so a rebuilt binary stops
    # the run in one line instead of after a boot.
    try:
        verify_so_hash(so_digest(SO_PATH))
    except ProofError as exc:
        say(f"REFUSING TO RUN: {exc}")
        say("Rerun when the .so matches.")
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
        say(f"flip tax proof: face {FACE:,} cap {CAP_BPS} bps ceiling {CEILING:,} "
            f"band_low {BAND_LOW}, artist fee {ARTIST_FEE_BPS} bps, flip tax "
            f"{ft.DEFAULT_SCHEDULE.full_bps} bps under {ft.DEFAULT_SCHEDULE.full_hold_seconds:,} s, "
            f"0 at {ft.DEFAULT_SCHEDULE.zero_hold_seconds:,} s")
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
        say(f"  underfunded seller {underfunded} holds "
            f"{get_balance(proof.url, underfunded):,} lamports")
        proof.make_mint(name="fresh", seller=seller, seller_key=seller_key, tickets=TICKETS_FRESH)
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

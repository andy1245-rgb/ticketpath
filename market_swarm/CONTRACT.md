# `market_swarm` build contract

Written before any module exists. It fixes the interfaces so independent work can proceed
in parallel. It is binding: a module that changes a signature here changes it for everyone.

Python 3.12, **standard library only** (the repository has zero runtime dependencies and
the new package keeps that). Tests are `unittest`. Nothing here is imported by
`ticketpath/`; the package is separate on purpose.

## The one sentence this package keeps

A swarm of agents trades synthetic tickets through the **real** `cap_hook` transfer hook on
a **local validator** (or devnet), every action is written to a ledger-shaped dataset, the
dataset is labelled synthetic in every file, and an agent never holds key material, never
spends beyond its budget, and never reaches a faucet.

## Hard invariants (a review that finds one of these broken has found a bug)

1. **No key material above the gateway.** Only `market_swarm/gateway.py` reads a keypair
   path. Nothing it returns contains key bytes. `Policy.decide` receives a `MarketView`,
   never a gateway, never a path, never a process handle.
2. **No faucet, no airdrop.** The harness never calls `requestAirdrop`, `solana airdrop`,
   or any faucet URL. Funding is genesis funding from the local validator. A test greps the
   package for those call shapes and fails on a hit.
3. **No mainnet.** Cluster is one of `{"local", "devnet"}`. Anything else raises before a
   socket opens. There is no branch that can reach mainnet.
4. **Every file labelled synthetic.** Header record first in every `.jsonl`, `synthetic:
   true` on every row, a `.meta.json` beside every dataset, and the literal string
   `SYNTHETIC` in every file name the harness writes for datasets.
5. **Budgets are hard.** A budget check that fails stops that agent's next intent; a total
   budget that fails trips the kill switch. No partial write, no silent overflow.
6. **Every command bounded.** The CLI takes a wall-clock cap; the kill switch polls it
   before every action.

## The program switch: which `cap_hook` a run drives

There are two programs and they are not two versions of one thing.

**v1** is the four-tag program deployed on devnet at `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`:
`InitializeExtraAccountMetaList`, `InitializeRecord`, `SetPendingPrice`, `SetStatus`. It is frozen
evidence -- no upgrade, no re-sign, no edit -- and it is what any devnet reader is reading. It can
also be deployed on a local validator, from its own keypair, at that same id.

**v2** is a different program id, `CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`, with seven tags:
it adds the floor, the jurisdiction and policy bytes and the hold clock. It has only ever run on a
local `solana-test-validator` built from this tree.

`program` is a field of the run config, one of `{"v1", "v2"}`, and it defaults to `v1` -- the
program devnet serves and the one every config in this tree was written against, so a config that
omits the field still loads as the run it always was. What each pairing proves, and nothing else:

| program | cluster | what the run proves |
|---|---|---|
| v1 | devnet | Every row is an observation of the frozen deployed program, at the id a devnet reader reads. |
| v1 | local | Every row is an observation of a v1 build this machine deployed, at the same id. |
| v2 | local | Admitted by the config and encoded by `wire.py`. This harness cannot drive it end to end yet: v2's `SetPendingPrice` is authorised by the record's authority, which v2's `InitializeRecord` pins to the mint's authority, while the swarm stages a price inside the seller's own signed transaction. `ChainGateway.start()` refuses with that sentence instead of writing a dataset of `6026` rows, and `--dry-run` is a labelled simulation. |
| v2 | devnet | Refused at load. v2 has never been deployed on devnet, so a v2 run there would read the v1 program's answers and record them as v2's. |

The switch is not a label on the dataset. It selects the program id the gateway connects to and
the keypair it deploys with (`gateway.PROGRAM_IDS`, checked against the keypairs beside the `.so`),
and the bytes a plain sale is built from (`market_swarm/wire.py`, where the program is an
argument with no default and the two shapes differ in four places: the record argument on
`InitializeExtraAccountMetaList`, the size and signer on `InitializeRecord`, the signer on
`SetPendingPrice`, and the record's writability on the transfer, which v2 needs to write the hold
clock). Every row carries the program it came from, as does the header and the sidecar, and
`verify_dataset` refuses a file whose rows disagree with its header.

The artist fee and the flip tax below are the one exception, stated rather than glossed. Their
stage and move are always the v2 shapes, on a v1 run too, because the record those paths write is
the one that carries the hold clock and the v2 authority; a fee or tax event is therefore a
v2-record event whatever `program` says, and a plain sale on a v1 run keeps the v1 encoders.

## Modules and fixed signatures

### `market_swarm/config.py`

```python
@dataclass(frozen=True)
class AgentSpec:
    agent_id: str
    policy: str            # registry name, see agents.POLICIES
    wallet_label: str
    seed: int
    budget_lamports: int
    budget_actions: int

@dataclass(frozen=True)
class EventSpec:
    event_id: str
    face_lamports: int
    mode: str              # "capped" | "monitored"
    cap_bps: int | None    # required for capped; ignored (field max) for monitored
    tickets: int
    rounds: int
    round_seconds: int     # simulated time-to-event step, never a real sleep by default

@dataclass(frozen=True)
class RunConfig:
    run_id: str
    cluster: str            # "local" | "devnet"
    events: tuple[EventSpec, ...]
    agents: tuple[AgentSpec, ...]
    total_budget_lamports: int
    total_budget_actions: int
    kill_after_seconds: float | None
    out_dir: Path
    dry_run: bool
    seed: int
    program: str = "v1"               # "v1" | "v2"; see the program switch above
    llm: LlmConfig | None = None      # off unless the config says otherwise

@dataclass(frozen=True)
class PriceTable:                   # USD per million tokens
    input: float; output: float; cache_read: float; cache_write: float
    def cost_usd(self, usage) -> float

@dataclass(frozen=True)
class LlmConfig:
    enabled: bool
    tier: str                       # "low" | "default" | "best"
    per_agent_token_budget: int
    total_token_budget: int
    max_concurrent: int             # 1..3, the measured safe bound on one credential
    timeout_seconds: float
    cost_cap_usd: float | None      # requires usd_per_mtok when set
    usd_per_mtok: PriceTable | None

def load_run_config(path: Path, *, overrides: Mapping | None = None) -> RunConfig
def effective_cap_bps(mode: str, cap_bps: int | None) -> int   # monitored -> 65535
def ceiling_lamports(face: int, cap_bps: int) -> int           # exact, integer, no float
```

The optional `llm` block is the only way to turn real agents on; absent or `enabled: false`
means the scripted policies, at no cost. It is validated like every other field: an unknown
key, a concurrency above 3, a total below the per-agent cap, a policy with no persona, and a
cost cap with no price table are all refused at load time, before any socket or child exists.
```

`ceiling_lamports` must agree with the on-chain predicate: `price * 10_000 <= face *
(10_000 + cap_bps)`, integer floor of `face * (10_000 + cap_bps) // 10_000`.

### `market_swarm/ledger.py`

```python
LEDGER_HEADER = {"record": "header", "synthetic": True, ...}

@dataclass(frozen=True)
class TradeRow:            # every field the dataset needs, no chain types
    run_id: str; seq: int; ts: str; event_id: str; mode: str
    agent_id: str; action: str; ticket_id: str | None
    from_wallet: str | None; to_wallet: str | None
    bid_lamports: int | None; lot_price_lamports: int | None
    round: int | None; rounds_left: int | None
    price_lamports: int | None; face_lamports: int; cap_bps: int
    ceiling_lamports: int; markup_bps: int | None
    status: str; error_code: int | None; signature: str | None
    slot: int | None; block_time: int | None; latency_ms: int | None
    hop_index: int | None; budget_before: int; budget_after: int
    chain: str; program: str; rationale: str; synthetic: bool = True
    def as_dict(self) -> dict

class LedgerWriter:
    def __init__(self, path: Path, *, header: Mapping) -> None
    def write(self, row: TradeRow) -> None      # stamps seq monotonically, refuses a row
                                                # whose synthetic is not True
    def close(self) -> None
    def __enter__/__exit__
```

Status vocabulary, closed set: `ok`, `refused`, `error`, `skipped`. `chain` vocabulary:
`local-validator`, `devnet`, `simulated`. `program` vocabulary: `v1`, `v2`, the same closed set the
config names, required on every row because it is provenance and not a default. A row with
`chain == "simulated"` and `status == "ok"` means "would have happened", never "happened".

Action vocabulary, closed set: `buy`, `list`, `resell`, `refuse`, `unknown`. The first three
are the intents a policy can return. `refuse` is a decision that was **not** taken — a live
policy declining because its own cap is spent — and it always carries `status: "skipped"`,
`price_lamports: null` and no move. It is a separate value on purpose: a refusal written as
`buy` made every reader that groups by action count a decision nobody took as a purchase.
`unknown` is written only for an intent whose action could not be read; the row's rationale
quotes what it said. `LedgerWriter.write` refuses a row outside the vocabulary before
writing anything, and `verify_dataset` reports one.

`bid_lamports` is the opposing order the row was matched against, `lot_price_lamports` is
what the seller paid, and `round`/`rounds_left` place the row on the horizon. They are on the
row rather than derivable by joining, because a dataset you have to join to price is a
dataset whose provenance you have already lost.

`budget_before`/`budget_after` describe the **row's `agent_id`**, always, the actor, which
for a resale is the seller. Money leaves the buyer, so the buyer's commitment is stated in
the row's `rationale` instead of being written under the seller's name.

### `market_swarm/budget.py`

```python
class BudgetExceeded(RuntimeError): ...

@dataclass
class BudgetState:   # per agent and total, lamports + actions
    ...

class BudgetTracker:
    def __init__(self, agents: Sequence[AgentSpec], total_lamports: int, total_actions: int)
    def check(self, agent_id: str, lamports: int) -> None    # raises BudgetExceeded
    def charge(self, agent_id: str, lamports: int) -> BudgetState
    def freeze(self, agent_id: str, reason: str) -> None
    def is_frozen(self, agent_id: str) -> bool
    def snapshot(self) -> dict
```

### `market_swarm/agents.py`

```python
@dataclass(frozen=True)
class Intent:
    agent_id: str; action: str; price_lamports: int | None
    ticket_id: str | None; rationale: str

@dataclass(frozen=True)
class Refusal:          # a policy declining to decide; row action "refuse", status "skipped"
    agent_id: str; action: str; price_lamports: int | None; rationale: str

@dataclass(frozen=True)
class Holding:
    ticket_id: str; lot_price_lamports: int; acquired_round: int

@dataclass(frozen=True)
class MarketView:      # read-only; carries no chain handle and no key
    round: int; rounds_left: int; event_id: str; mode: str
    face_lamports: int; cap_bps: int; ceiling_lamports: int
    tickets_available: int; holdings: tuple[Holding, ...]
    last_prices: tuple[int, ...]; refused_attempts: int
    def rng(self) -> random.Random        # seeded per (agent, round); deterministic

class Policy(Protocol):
    name: str
    def decide(self, view: MarketView) -> list[Intent | Refusal]

POLICIES: dict[str, type[Policy]]   # "buyer","holder","flipper","scalper","sniper","panic"
def build_policy(spec: AgentSpec, *, face_lamports: int, cap_bps: int) -> Policy
```

The **scalper** must, by design: aim above `ceiling_lamports` for its first N attempts
(deterministic N from its seed), and if refused, retry at or just under the ceiling so it
still trades. In `monitored` mode its over-cap price succeeds, that is the point of the
mode. Tests assert both behaviours.

### `market_swarm/gateway.py`

The only module that touches keys, RPC, or a validator. May import helpers from `tools/`
if they import cleanly, otherwise shell out; either way this interface is fixed.

```python
class ChainUnavailable(RuntimeError): ...

@dataclass(frozen=True)
class TransferResult:
    status: str                 # "ok" | "refused" | "error"
    signature: str | None; slot: int | None; block_time: int | None
    error_code: int | None      # 6010 == 0x177a == CapExceeded
    latency_ms: int; logs: tuple[str, ...]

class EventChain:               # one mint, one record, one mode
    event_id: str; mint: str; record: str; mode: str
    cap_bps: int; face_lamports: int; ceiling_lamports: int
    def open_account(self, wallet_label: str) -> str          # public address only
    def stock(self, count: int) -> None                       # mint `count` tickets to house
    def transfer(self, *, from_label: str, to_label: str, price_lamports: int) -> TransferResult
    def read_record(self) -> dict                             # face,cap,pending,status

class ChainGateway:
    def __init__(self, cluster: str, *, run_dir: Path, program: str = "v1", dry_run: bool = False) -> None
    def start(self) -> dict            # boots + funds a local validator, or connects to devnet
    def stop(self) -> None             # idempotent; kills every child it started
    def create_event(self, spec: EventSpec) -> EventChain
    def status(self) -> dict           # cluster, program, program id, mint(s), healthy bool
```

`dry_run=True` returns a `DryRunGateway` with the same surface, no socket, and **the status
the hook would return**: below the ceiling `ok`, above it `refused` with 6010 predicted from
the same predicate, with `signature=None`, `slot=None`, `latency_ms=None` and a rationale
that says in words that no transaction was built, signed or sent. Every row it causes
carries `chain: "simulated"`, and a gateway whose `simulated` disagrees with the config is
refused rather than relabelled. Tests use it. It is never a way to claim a trade happened on
chain.

### `market_swarm/runner.py`

```python
@dataclass(frozen=True)
class RunSummary:
    run_id: str; rows: int; by_status: dict; by_agent: dict
    total_notional_lamports: int; kill_reason: str | None
    dataset_paths: tuple[str, ...]; wall_seconds: float
    llm: dict | None = None      # LlmBudget.snapshot() when the live mode ran, else None

class SwarmRunner:
    def __init__(self, config: RunConfig, gateway, *, clock=None,
                 policies: Mapping[str, Policy] | None = None) -> None
    def run(self) -> RunSummary
```

Rounds: each round, every agent gets a `MarketView` and returns intents; intents are
applied in a deterministic order (seeded shuffle of agent ids, stable per round); a resale
runs `gateway.transfer` then writes one row; a `list` writes a row with `status="ok"` and
`chain=<cluster>` but no signature, because the program has no listing surface and the row
says so in `rationale`. Every action is budget-checked before it is attempted, and the
kill switch is polled before every action.

With the `llm` block enabled, decisions for one round may run concurrently, up to
`llm.max_concurrent`: every view is built from the same pre-round state and nothing is
applied until the round ends, so concurrency cannot change a decision, and the intents are
collected in the seeded order so the dataset is as reproducible as a scripted run's. A
tripped `LlmBudget` is part of the same kill switch as the flag file and the wall clock; it
stops the run before the round is applied and its reason lands in `kill_reason`. Either way
each dataset's `.meta.json` carries `llm: null` or the spend block, so a reader can tell a
scripted run from a paid one without asking.

The sidecar also carries a top-level `provenance`, one of `llm`, `policy`, `unknown`,
`scripted`. `llm` is the wired path with a run-level `LlmBudget`; `policy` means the run was
built with `policies=` and those policies reported their own accounting (a `ForgePolicy`
does, and its model, tier, decision counts and spend go into the `llm` block); `unknown`
means caller-supplied policies that report nothing about model decisions, in which case
neither the block nor the note claims either way; `scripted` is claimed only when this runner
built the policies itself from the config. `summarise` reads that field, so a summary of a
live run no longer calls it scripted.

### `market_swarm/datasets.py`

```python
def verify_dataset(path: Path) -> dict     # schema, synthetic flags, monotone seq, invariants
def summarise(path: Path) -> dict          # counts, price distribution, refusal rate per mode
```

`summarise` returns `by_action` (every row, keyed by the action vocabulary above),
`by_action_status` (the same rows crossed with status, so `buy=7` can be read against how
many filled), `by_status`, `by_agent`, `by_mode`, `asks_by_mode`, `refusal_rate_by_mode`,
`price_quantiles_by_mode` and the synthetic-only `note`.

`verify_dataset` is what the CLI's `verify-dataset` verb calls and what the tests call. It
must FAIL on: a missing header, a row without `synthetic: true`, a non-monotone `seq`, a
`markup_bps` that disagrees with price/face, a `status`, `action` or `chain` outside its
closed set.

### `market_swarm/forge_policy.py`, opt-in only

```python
@dataclass(frozen=True)
class Usage:
    input: int = 0; output: int = 0; cache_read: int = 0; cache_write: int = 0
    usd: float = 0.0
    total: int                     # the four counters, never the dollars
    def __add__(self, other: "Usage") -> "Usage"

def usage_from_record(record: dict) -> Usage   # all four counters plus cost.total
def spawn_argv(*, session_dir, name, model, extra: Sequence[str] = ()) -> list[str]

class ForgePolicy:                 # implements Policy
    def __init__(self, spec, *, tier: str = "low", token_budget: int,
                 max_concurrent: int = 2, timeout_seconds: float = 180,
                 spawn: Callable | None = None,
                 acknowledge_cost: bool = False,
                 system_prompt: str | None = None,
                 extra_argv: Sequence[str] = (),
                 on_usage: Callable[[Usage], None] | None = None,
                 kill_check: Callable[[], None] | None = None,
                 scratch_root: Path | None = None) -> None
```

Reuses subforge's documented shape: `pi --mode rpc --session-dir … --name forge:<name>
--model <provider>/<model>[:<effort>]`, prompt over stdin, line-delimited JSON out, kill by
process group, `runs.jsonl`-shaped row field names, folded status. The per-agent **token**
budget is enforced from the child's own stream, mid-stream; the reported `cost.total` is kept
per attempt and handed to `on_usage` once per attempt, including failures. `spawn` is
injectable so tests run against a fake child and never touch a provider. Constructing it
without `acknowledge_cost=True` raises: spending money is the operator's decision.

`system_prompt` is written to `<cwd>/.pi/SYSTEM.md` before the spawn, with an empty
`.pi/APPEND_SYSTEM.md`; a trusted project prompt replaces the operator's global
`<agent-dir>/SYSTEM.md` and its append, which a child would otherwise inherit on every turn.
`extra_argv` is appended after `--model` and is where the caller puts the sandbox flags; this
module never invents them. Neither is a sandbox: they shape the child, and the guarantee is
that a dead, slow, broke or incoherent child produces a labelled scripted intent instead of
stalling the run.

### `market_swarm/llm.py`, the live mode

```python
PROVIDER_EXTENSION: str                        # resolved from ~, never a home path literal
PERSONAS: Mapping[str, str]                    # buyer, holder, flipper, scalper, sniper,
                                               # panic, greater_fool
def persona_for(policy_name: str) -> str
def hardened_flags(provider_extension: str | None = None) -> tuple[str, ...]
class LlmKilled(RuntimeError): reason: str
class LlmBudget:                               # one per run, shared by every agent
    def __init__(self, *, total_token_budget: int, cost_cap_usd: float | None = None,
                 prices: PriceTable | None = None) -> None
    def charge(self, usage: Usage) -> None     # never raises; first trip wins
    def check(self) -> None                    # raises LlmKilled when tripped
    trip_reason: str | None; usd: float; usage: Usage
    def snapshot(self) -> dict                 # the sidecar block
def build_llm_policy(spec, *, llm, budget: LlmBudget, scratch_root, spawn=None) -> ForgePolicy
```

`hardened_flags()` returns `--no-extensions -e <provider> --no-tools --no-skills
--no-context-files --no-mcp --no-prompt-templates --approve`. The `-e` is not optional: the
`commandcode` provider is an extension, so dropping extensions without re-adding it makes
`--model commandcode/...` unresolvable. `--no-tools` is what "agents never see key material"
actually rests on: the child has no file or shell tool to look with.

`LlmBudget` is the run-level cap. It counts all four billed counters and the dollar figure,
uses the configured price table only when a child reports no cost of its own, and records
which basis it used in `snapshot()["cost_basis"]` (`stream`, `table`, `mixed`, `unpriced`).
It never raises in `charge`, because that runs inside the child's stream loop; the kill is
`check`, which `ForgePolicy` calls before its next decision and the runner calls before
every action.

### `market_swarm/cli.py`

`python3 -m market_swarm <verb>`:

- `plan`, print the resolved config and the cost, start nothing. With the LLM on it also
  prints the tier, both token caps, the dollar cap and the decision count.
- `run`, run the swarm. Flags: `--cluster local|devnet`, `--program v1|v2`, `--dry-run`,
  `--mode capped|monitored`, `--agents N`, `--rounds N`, `--seed N`,
  `--per-agent-lamports`, `--total-lamports`, `--kill-after SECONDS`, `--out DIR`, and
  `--acknowledge-cost`, which is required when the config's `llm.enabled` is true: a paid
  run takes an explicit flag, not just a file on disk. With the LLM on it also prints the
  tokens, the four counters, the dollar estimate and the kill reason.
- `verify-dataset PATH`, `summarise PATH`.
- `forge-policy`, opt-in, refuses without `--acknowledge-cost`, and names the personas and
  the example config when acknowledged.

Every verb exits non-zero on a failed invariant and prints nothing that needs a chart to
read.

## The artist fee, added 2026-11-08

An event may carry `artist_fee: {"artist_wallet": <base58 pubkey>, "fee_bps": 0..10_000}`. Absent, the
package behaves exactly as it did before this existed: a sale is two instructions and one signature,
every fee column is null, and every dataset written before it still verifies.

With it, a **resale** through `EventChain.transfer` is one transaction of three instructions and two
signatures — `cap_hook` `SetPendingPrice` (the issuer signs it, because the record's authority is the
issuer), a System `Transfer` of `price * fee_bps // 10_000` lamports from the seller to the artist, and
the Token-2022 move (the seller signs) — and `TransferResult.fee_lamports` is what was paid: the fee
only when the outcome is `ok`, `0` for anything that did not land. Atomicity is the transaction's, not
this package's: a leg that fails fails the sale and rolls the rest back.

Fixed signatures this adds:

- `config.EventSpec.artist_fee: ArtistFeePolicy | None = None` (last field; parsed by
  `artist_fee.ArtistFeePolicy.from_mapping`, whose `ArtistFeeError` the loader re-raises as
  `ConfigError` with the field path intact).
- `gateway.TransferResult.fee_lamports: int = 0` (last field).
- `gateway.EventChain.transfer(..., charge_artist_fee: bool = True)` and the same keyword on
  `DryRunEventChain.transfer`. The runner passes `False` for the primary buy and `True` for the resale,
  both explicitly: the house is selling the artist's own stock at face, so a fee there is the artist
  paying themselves, and the operator's sentence is "on each resale". Every call site names the flag,
  and `market_swarm/tests/test_artist_fee_call_sites.py` fails if one does not.
- `gateway.instruction_set_pending_price_v2(...)` and `gateway.instruction_transfer_checked_writable(...)`:
  the two v2 shapes the fee path needs, beside the v1 encoders they must not replace.
- `ledger.TradeRow.fee_lamports` and `.artist_fee_bps` (both `int | None = None`). A fee event's rows
  carry the event's rate on every row and the amount only where money moved; a no-fee event's rows
  carry neither.

The dataset invariant `datasets.verify_dataset` enforces: an executed **resale** with a price carries
exactly `price * bps // 10_000`; an executed **buy** with a rate carries 0 or null; a fee below 0 or
above the price is a violation; a fee with no rate is a violation; an executed trade that names a rate
with no price is a violation.

Two things this contract does not claim, and a reader of a dataset must not read into it: the chain
does not enforce the fee (a staged price can be consumed by a transfer that pays nothing), and the
dataset header carries no event-level policy, so a row with both fee columns deleted cannot be told
from a row from a no-fee event. Both are stated in `records/findings/42-artist-fee-at-checkout.md` §5
and §8, and the proof is `tools/artist_fee_proof.py`.

## The flip tax, added 2026-11-08

An event may carry `flip_tax: {"enabled": bool, "artist_wallet": <base58 pubkey>, "schedule":
{"full_bps", "full_hold_seconds", "zero_hold_seconds"}}`. **The default is off**: absent, the package
behaves exactly as it did before this existed, a policy that is off builds no leg, and every dataset
written before it still verifies. It is a second seller-paid lamport `System` `Transfer` in the same
atomic transaction as the artist fee and the move, charged on **resales**, paid to the **artist's
wallet**, and it sits last before the move.

The rate is a function of the hold, and the hold is the chain's: `held_since_unix` is read at checkout
from byte 30 of the 70-byte v2 `["record", mint]` account, which the hook writes on every admitted
transfer. `full_bps` while the hold is at or under `full_hold_seconds`, then a straight line floored in
integers to 0 at `zero_hold_seconds`; defaults 1 500 bps, 3 600 s and 2 592 000 s. `0` in the record
means the clock was never written and is charged the full rate; a clock that went backwards clamps to
zero seconds and is charged the full rate too.

Fixed signatures this adds:

- `config.EventSpec.flip_tax: FlipTaxPolicy | None = None` (last field; parsed by
  `flip_tax.FlipTaxPolicy.from_mapping`, whose `FlipTaxError` the loader re-raises as `ConfigError`
  with the field path intact). An omitted `artist_wallet` inherits the event's `artist_fee` wallet; a
  different one, or an explicit null, is refused. A config whose `artist_fee.fee_bps +
  flip_tax.schedule.full_bps` exceeds `10 000` on an enabled block is refused at load.
- `flip_tax.combined_take_bps(...)`: the one definition of that bound, called by the loader **and** by
  `gateway._check_spec`, so a hand-built `EventSpec` that never saw a config file is refused at
  `create_event`, before the validator boots.
- `gateway.TransferResult.flip_tax_lamports: int = 0`, `.flip_tax_bps: int | None = None` and
  `.held_seconds: int | None = None`, after `fee_lamports`. Money is what moved: the tax only when
  the outcome is `ok`, `0` otherwise, with the rate and the hold reported anyway so a row shows what
  was applied.
- `gateway.EventChain.transfer(..., charge_flip_tax: bool = True)` and the same keyword on
  `DryRunEventChain.transfer`. The runner passes `False` for the primary buy and `True` for the
  resale, both explicitly, and every call site names the flag.
- `gateway.ChainGateway._read_record_v2(record) -> bytes` and `ChainGateway._now() -> int`: the raw
  record read and the clock seam. A record that is absent, not base64 or shorter than 70 bytes raises
  `ChainUnavailable` **before** any signature exists, so a sale is never priced on a record nobody
  read.
- `ledger.TradeRow.flip_tax_lamports`, `.flip_tax_bps` and `.held_seconds` (all `int | None = None`),
  after `artist_fee_bps`. A taxed event's rows carry the rate and the hold on a sale that was assessed
  and the amount only where money moved; an event with no tax policy carries none of the three.

The dataset invariants `datasets.verify_dataset` enforces are the ten listed in
`records/findings/43-flip-tax-at-checkout.md` §5.1: the amount agrees with `price * bps // 10 000` on
an executed resale, is 0 or null on an executed buy, is 0 or null on a row that never executed, and is
never negative, never above the price and never present without a rate; `held_seconds` is a
non-negative integer or null.

Three things this contract does not claim, and a reader of a dataset must not read into it. The chain
does not enforce the tax, exactly as it does not enforce the fee. The dataset header carries no
event-level policy, so no `held_seconds`/`flip_tax_bps` pair is checked against any curve, and a rate
that is arithmetically consistent with its own amount can still be the wrong rate for the event. And
the record is not a history: the sale that paid the tax is an admitted transfer, so it overwrites the
clock it was priced from, and the age has to be reconstructed from the transfer history rather than
read back from the account. All three are stated in `records/findings/43-flip-tax-at-checkout.md` §5,
and the proof is `tools/flip_tax_proof.py`.

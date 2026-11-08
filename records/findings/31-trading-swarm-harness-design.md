# 31, A trading-swarm harness for generating synthetic resale-market data

Status: design and implementation record. The verification section at the end states
exactly what was run and on what surface; nothing is claimed here that was not executed.

Classification, per the programme's §4.3: the **harness mechanics** are A (established by
running them). Every **price, markup, refusal rate and distribution** the harness produces
is **E, synthetic, and not evidence about any real market**. Nothing in `records/` may
quote a number from a `market_swarm` dataset as a finding about tickets. That sentence is
the reason this file exists separately from the research record.

## Why it exists

The programme needs resale price paths. The literature is mostly about latent
market-clearing prices under censoring; the platform this project prices for is
ledger-ticketed, where a resale is a recorded transaction. There is no lawful
listing-level price feed on this machine (`records/findings/08`) and the frontend's
`lib/mock/` is fixture data built to render a UI.

So the question the harness answers is narrow and honest: **given agents with known
budget rules and known strategies, what does the price path through our own cap hook look
like**, how many hops, what markups, where the cap binds, how a resale market behaves
when one participant is actively trying to break the cap. That is a *mechanism* test and a
*load* test for the pricing model. It is not, and cannot be, an estimate of real prices.

## What it is not

- Not a market simulator of real ticket demand. The agents are scripted policies with
  seeds; they have no model of preferences, no elasticity, no outside option.
- Not evidence that the cap works in the real world. It shows the *program* refuses a
  transfer over the cap, which `records/findings/18` already proved with a signature pair.
- Not a settlement system. The cap hook holds no lamports, has no escrow and no listing
  instruction (its README says so in those words). A "sale" here is a **custody transfer
  with a declared price**, and the price is a number staged in the record account. No SOL
  changes hands for a ticket in this harness. Anyone reading the dataset as revenue data
  would be reading it wrong, so the dataset says so in its header, in every row, and in a
  sidecar file.
- Not a sybil or bot-resistance demonstration. There is no nullifier in the program.

## The three levels of the thing

**One event, one mint, one record.** `InitializeRecord { face, cap_bps }` fixes the face
and the cap; the cap is immutable afterwards, so *the mode is a property of the mint, not
of the run*. Two mints are how two modes are compared: identical in every respect except
`cap_bps`.

**The two modes.**

| mode | record `cap_bps` | what the chain does | what the dataset gets |
|---|---|---|---|
| `capped` | the event's real cap, e.g. 2500 (+25%) | the hook refuses any staged price above `face·(1+cap)`, with `CapExceeded` 6010 | refusal rows with a signature and an error code, and no hop |
| `monitored` | 65535, the u16 field maximum | the same predicate, but nothing a scripted agent can price is above it, so every resale is admitted and recorded | the unconstrained price path, including the scalper's tail |

The residual limit is real and is stated in the code and the dataset: `monitored` is not
"no cap", it is "cap at the field maximum", so a price above `face·7.5535` is still
refused. The harness records each event's `ceiling_lamports` on every row so the boundary
is never implicit.

**The trade lifecycle.** Primary acquisition, listing and resale:

- **Buy** is a transfer of one ticket (one base unit, the hook's `amount == 1`) from the
  house account to the agent's own wallet, priced at face or below.
- **List** is a harness record only. The program has no listing instruction, so a listing
  is an intent with a price and a horizon; it becomes a chain fact only when a resale is
  attempted. The dataset labels it that way (`signature` absent, `rationale` says so).
- **Resell** is `SetPendingPrice(p)` immediately followed by the Token-2022 transfer, **in
  one transaction**. That pairing is not a style choice: the staged price lives in a
  per-mint record, so two transfers of the same mint in separate transactions can have
  their prices clobbered between the stage and the check. One atomic transaction removes
  the race, and an over-cap attempt then fails as a whole, leaving the record's staged
  price untouched by the rollback.
- **Refusal** is sent with preflight skipped, deliberately, so it lands as a *failed
  transaction with its own signature*. That is the only form of refusal anyone else can
  check afterwards, and it is the same technique `tools/devnet_publish.py` uses for its
  boundary pair.

## Safety model

Non-negotiable, and each one is a test rather than an intention.

1. **Cluster is a closed set.** `{"local", "devnet"}`. There is no branch, flag or
   environment variable that reaches mainnet; an unknown value raises before a socket
   opens.
2. **No faucet, no airdrop, ever, by anyone in this package.** Funding is genesis funding
   from the local validator; the harness never calls `requestAirdrop` or `solana airdrop`.
   A test greps the package for those call shapes.
3. **Agents never hold key material.** A policy receives a read-only `MarketView` and
   returns `Intent` objects. It gets no gateway, no path, no process handle, no signer.
   The harness custodies every wallet; this is a data generator, not a trustless
   marketplace. Only `gateway.py` reads a keypair path, and it signs out of process through
   the existing `tools/solana_sign.py`, so the process that runs agent code has no line
   that touches a seed.
4. **Hard budgets, two currencies.** Per agent and in total: notional lamports and a count
   of actions. A failed check stops that agent. A total check trips the kill switch. A
   charge that would exceed leaves state untouched.
5. **A kill switch, in three forms.** A wall-clock cap, a flag file, and signal handlers;
   polled before every action. The local validator is killed on every exit path. No
   orphaned validator, no orphaned agent process.
6. **Every command bounded.** The CLI refuses to start without a wall-clock cap.
7. **The label is enforced by the writer.** `LedgerWriter` refuses to write a row that
   does not carry `synthetic: true`; the header record is written first and carries the
   disclaimer; a `.meta.json` sits beside each dataset; `SYNTHETIC` is in every dataset
   file name.

## Why the LLM agents are an adapter, not the default

The request was a swarm of deepseek-flash agents. What was established about that channel
is in `records/findings/30`: every tier on this profile is the same model differing only
in effort, subforge has no default timeout, a finished run's output is p90 ~207k tokens,
and a run can report `finished` with zero tokens. A market dataset needs thousands of
decisions; a decision that costs a two-minute child and 200k output tokens produces a
research toy, not a data source.

So the harness has a **pluggable policy interface** with two implementations: scripted
policies (deterministic, zero cost, the default and what the tests and dataset runs use)
and a `forge` adapter that reuses subforge's documented spawn form, registry row shape,
fold precedence, token accounting and `maxRunSeconds` kill. The adapter is opt-in and
refuses to construct without an explicit cost acknowledgement. It is **not** run against
live agents in this build; that is a spend decision, and spend is the operator's.

That is the honest version of "based on subforge": the *enterprise* parts of subforge, the delegation contract, the tier resolution, the append-only registry with folded status,
the per-run kill, the write-as-you-go discipline, are adopted. The part that costs money
per trade is isolated behind an interface and left switched off.

## Layout

New code only, separate from the existing package, standard library only:

```
market_swarm/
  CONTRACT.md      the binding interface contract, written before the code
  config.py        run/event/agent config, the cap arithmetic
  budget.py        hard budgets and freeze
  ledger.py        the append-only synthetic-labelled dataset writer
  agents.py        the scripted policies, including the scalper
  gateway.py       the only module that touches keys, RPC or a validator
  runner.py        rounds, intent application, kill switch
  datasets.py      verify and summarise a dataset
  forge_policy.py  the opt-in subforge-shaped LLM policy adapter
  cli.py           `python3 -m market_swarm <verb>`
  tests/           unittest, no network, no chain
```

Run artefacts, datasets, throwaway keypairs, the validator's ledger, go to a git-ignored
directory and are never committed. The repository is code only.

## Verification

Everything below was executed on this machine on 2026-11-08. The surface is named for each
claim, because "tests pass" is not a surface anyone reads.

### Unit tests, no chain, no network

```
python3 -m unittest discover -s market_swarm/tests -t .
Ran 293 tests in 1.17s
OK (skipped=1)
```

The one skip is the live test, which is gated on `MARKET_SWARM_LIVE=1`. The suite covers
the cap arithmetic against the on-chain predicate in both directions, budget refusals that
leave state untouched, the ledger's refusal to write an unlabelled row, policy determinism
re-run in a fresh process, the scalper's behaviour in both modes, the runner's ask/bid
matching and its tie-breaks, the kill switch (wall clock, flag file, total budget), the
CLI's refusals, and the forge adapter against a fake child.

The existing repository suite is unchanged and still green: `python3 -m unittest discover
-s tests -t .` → `Ran 610 tests in 24.3s` / `OK`.

### The real program, on a local validator

The gateway's own live test, run by me, not by whoever wrote it:

```
MARKET_SWARM_LIVE=1 python3 -m unittest market_swarm.tests.test_gateway_live -v
Ran 1 test in 10.691s
OK
```

It asserts more than "no exception": the record PDA decodes to the face and cap that were
asked for; a transfer priced at exactly `1_250_000_000` (face `1_000_000_000`, cap `2500`)
succeeds with a signature, a slot and the hook's own `ticketpath: cap admitted` log line; a
transfer priced at `1_250_000_001` comes back `refused` with `6010`, its **own distinct**
signature and slot, and the hook's `ticketpath: cap exceeded` log line. The refusal is sent
with preflight skipped precisely so it lands as a failed transaction anyone can look up.

### The full harness end to end, on the chain

A four-agent, four-round, single-event run against a fresh local validator:

```
python3 -m market_swarm run --config .swarm-runs/live-small.json --kill-after 420
rows 10   status ok=6 refused=3 skipped=1
wall 8.759s
```

Reading the produced dataset with the verifier (`verify-dataset` → `PASS`):

| seq | agent | action | status | price | error | signature |
|---|---|---|---|---|---|---|
| 1–3 | b1, h1, s1 | buy | ok | 1,000,000,000 |, | present, distinct |
| 4 | g1 | buy | skipped | 1,500,000,000 |, |, |
| 5 | s1 | resell | **refused** | 1,270,000,000 | **6010** | present |
| 7 | s1 | resell | **refused** | 1,280,000,000 | **6010** | present |
| 9 | s1 | resell | **refused** | 1,290,000,000 | **6010** | present |

Six signatures, six unique, every `ok` and every `refused` row carrying one; the refused
rows carry the slot of the transaction that was rejected and `hop_index: null`, because a
refused transfer moved nothing. That is the cap being enforced by
the program on a chain, with the scalper's escalating asks as the thing it refuses.

### The two modes, on the chain

The same scalper, the same ask, two mints, both on a real local validator:

| event | record `cap_bps` | ceiling | ask | outcome |
|---|---|---|---|---|
| `evt_live` | 2500 | 1,250,000,000 | 1,270,000,000 | `refused`, error 6010, failed transaction with its own signature |
| `evt_live_monitored` | 65535 | 7,553,500,000 | 1,270,000,000 | `ok`, executed and recorded, distinct signature |

That pair is the whole point of the harness. The program refuses the price one way and
admits it the other, and the dataset says which, with a signature either way.

### The two modes, measured in simulation

The dry run of `example-run.json` (nine agents, two events, twelve rounds each, the
scripted default, no chain):

```
rows 106   status ok=64 refused=4 skipped=38
capped     ok=32 skipped=15 refused=4    above +2500 bps: 4 skipped, 4 refused
monitored  ok=32 skipped=23              above +2500 bps: 21 skipped, 3 ok
```

The same agents and seeds, identical until the first over-cap ask: from there the paths
diverge, because a refusal keeps the unit with the seller and an execution moves it. In
`capped` the over-cap asks are refused with 6010; in `monitored` three of them execute and
are recorded. The `skipped` counts include over-cap *bids* that no ask met, not only asks. The rest are censored
because no bid met them, which is a market fact, not a filter.

### Safety gates

- `python3 tools/public_safety.py check --tracked`: 64 hits in 9 files, **all** under
  `records/` and all pre-existing (the 2026-11-07 measurement in `AGENTS.md` is the same
  64); **zero in `market_swarm/`**.
- Key files created by a live run are mode `0600`, under a git-ignored directory, and
  `git status` shows nothing from `.swarm-runs/`.
- After the live runs: no `solana-test-validator` process left running, and the run
directory is 156 KB rather than the 1.5 GB a kept ledger costs.
- No mainnet literal exists in the package; the cluster is validated against
  `{"local", "devnet"}` at load time and again at gateway construction.

### What is not tested, and is not claimed

- **The LLM swarm has never run against a provider.** `forge_policy` is implemented and
  tested against a fake child only. No deepseek child made a trading decision in this
  build. The default path for a dataset is the scripted policies.
- **No devnet run.** Everything on-chain was on a local validator. Devnet needs a funded
  authority, and the RPC faucet is closed, so funding is the operator's action.
- **`devnet` cluster is code-complete and untested.** The same code path as `local` except
  for the endpoint and the funding check; nobody has executed it.
- **No adversarial or sybil resistance is modelled**, and the program has none.
- **Nothing here prices a real ticket.** The dataset says so in its header, in every row,
  in the sidecar, and in the file name.

## Adversarial review, and what it changed

Two reviewers who did not write the code read it adversarially, one for safety and
correctness, one for honesty and dataset semantics, and both wrote findings to
`market_swarm/.research/`. **No critical finding.** Nothing could reach mainnet or testnet,
nothing could make the package call a faucet, no key byte or key path reached anything an
agent or the runner can see, and `LedgerWriter` could not be made to emit an unlabelled row.

The findings that were real, and what was done:

| finding | what was wrong | fix |
|---|---|---|
| M1 | `total_budget_*` was granted once **per event**, so two events doubled the run's stated total | the totals are now checked cumulatively across the run, before every charge; a breach trips the kill switch naming the total |
| M2 | the wall clock was polled before transfers but not before listings, broken intents or skipped rows | polled at the top of every row-writing action; a regression test expires the clock *inside* the policy so the poll is the only thing that can stop the row |
| M4 | the `chain` column came from the config, so a simulated gateway with `cluster="devnet"` could label rows as observations | the label comes from the gateway; a disagreement with the config is refused |
| M5 | a crashed run left a dataset indistinguishable from a finished one | the sidecar carries `complete` and `rounds_completed` |
| H1 | a **simulated** refusal was narrated "was sent; the chain refused it" | the prose branches on the chain: a dry row says the hook *would* refuse and that nothing was built, signed or sent |
| H2 | a dry run's header named a cluster and never said nothing ran | the header carries `chain` and `dry_run` |
| H3 | a resale row's budget columns described the buyer while the row named the seller | the columns are the actor's; the buyer's commitment is in the rationale |
| M1(h) | no round field, so "markup by time-to-event" was not computable from the dataset | `round` and `rounds_left` on every row |
| m7 | an `ok` row claiming the chain with no signature passed verification; so did a resale with its markup stripped | both are now violations; nine tamper cases were run and each is caught (the markup case needs a dataset containing an executed resale, which the live sample does not have -- it is tested on the dry one) |
| m18 | a refused resale recorded a hop the chain had rolled back | `hop_index: null` on a refusal |
| m6 | a float, bool or negative price aborted the run and left a truncated dataset | a malformed price is a `broken` row and the run continues |
| m13 | a frozen seller's ask vanished with no row | recorded as `skipped` with the reason |
| m3, m4(h) | the faucet and key-path guards each grepped one file | both now walk every module in the package |
| m9 | `run_id` and `event_id` were concatenated into a file name unvalidated, so a stray separator could put a dataset outside the run directory | identifiers are shape-checked at load, and the runner refuses any resolved path outside the run directory it was given |

Two findings were **accepted with a reason, not fixed**:

- **A bid is a limit price, not a quantity.** One bid intent can fill several units in a
  round, while the buyer has inventory room and budget. That is a market order with a limit
  price, which is what the agent meant, and the alternative needs an order-size field on the
  Intent contract. It is stated here and in the runner rather than left for a reader to
  discover; the buyer's total fills are still bounded by its holdings limit.
- **A `local` run is not an offline run.** The validator is started with `--clone` of the
  Token-2022 and Memo programs from the public devnet endpoint, so a first boot needs
  network. It needs devnet's code, not its state, and no transaction is ever sent there.
- **A listing is written `status: "ok"`.** It *is* a successful record: the harness wrote it
  and nothing failed. It is not a chain action, and `summarise` separates by action, so
  `ok = 64` can be read as "60 chain, 4 listing". Renaming the status would break the closed
  vocabulary for one row type to save a reader one line of the summary.

Everything a reviewer found has a test in `market_swarm/tests/test_review_fixes.py`, and the
regression tests were checked by disabling the fix and watching them fail.

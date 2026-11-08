# Ticketpath

Ticketpath is a tool for the organizer of a live event who sets a primary ticket price and
then has no view of what the same seat changes hands for afterwards. It reads the platform's
own resale record and computes what that record supports: the markup on every recorded sale
measured against that ticket's own tier's face value, the custody path of a single ticket
with a price on each hop, the roll up an organizer needs (volume, median price, markup
distribution, where the tickets ended up), and a recommended primary price where the record
can carry one. It is not a marketplace: there is no listing, bid, buy or checkout path here,
none is served by the backend, and none is planned. Resale value, how it moves, and the
chance a ticket sells are specified rather than fitted, and today the honest output is a
refusal naming the missing observation, because nothing records what an unsold ticket asked.

## What works today

Measured 2026-11-07T11:54Z on this machine, Python 3.12.3, standard library only. Run
every command from the repository root.

**[CORRECTED 2026-11-08T03:45Z. Five statements below were true when written and are not true of the
tree now; each is corrected in place with its command, and this note is the index: the test count
(546 → 610, §"Run the tests"); the finding count (29 → 32 tracked, 42 on disk, §"How the research is
organised"); "no program is deployed on any cluster" and "no mint, no transaction, no signature in
this repository" (§"Deployed on devnet, in part", which the deployment rewrote); "this machine has no
Solana toolchain" (it has one, in a login shell); and the closing "Nothing is deployed". The
measurements in this section that were not re-taken are marked as of their date. Nothing in this
edit changes code or a number that was not re-measured.]**

**[Added 2026-11-08T08:15Z: a sixth statement joins the five above. The console banner no longer says
"no program is deployed"; the page prints "The chain slot at the bottom prints what a verified devnet
artefact records, and the [DESIGN] block is a design; neither is a deployed guarantee." The sentence is
corrected in §"Open the console page" and measured at 17,380 bytes on the same reading.]**

**Start the backend.** It binds `127.0.0.1:8788`; `TICKETPATH_PORT` overrides, and 8787 is
refused because another process owns it.

```bash
python3 -m ticketpath.server
```

Observed on an instance bound to 8793, because 8788 was already serving on this machine:

```
ticketpath 0.1.0 listening on http://127.0.0.1:8793 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
  SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
```

**Open the console page.** The backend serves one server rendered HTML page at `/`.

```bash
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://127.0.0.1:8788/
```

Observed `200`, and a page of **17,380 bytes** at `/` (`17,307` at the pinned `[DEVNET]` state),
measured on a fresh instance at 2026-11-08T08:07Z. The status code is the invariant; the byte count
moves whenever the console is edited, so it is dated here and not quoted as if it were fixed. The
page opens with a banner whose first sentence is `SYNTHETIC FIXTURE DATA: every number on this page
is computed from a synthetic fixture generated in this repository. Not real ticket data. No accuracy
claim is made or implied.`, followed by `The chain slot at the bottom prints what a verified devnet
artefact records, and the [DESIGN] block is a design; neither is a deployed guarantee.` It then
lists all eight events with the pricing regime each is in. It shows the
evidence counts behind the decision, then the decision or a refusal. On the default selection
it prints a recommended primary price of at least 1.38 SOL
per ticket tagged `[UNVALIDATED]`, and says that is a floor, not an estimate, with no upper
bound stated. `?sim=1` runs the simulated state machine: five lines, including a transfer a
lamport above the cap refused with 6010 and an unstaged move refused with 6009.

**Query the API.**

```bash
curl -s 'http://127.0.0.1:8788/api/events?limit=100'   # 8 events
curl -s 'http://127.0.0.1:8788/api/tickets?limit=200'  # 76 tickets
curl -s 'http://127.0.0.1:8788/health'
```

Observed 8 events, 76 tickets, 9 of 9 contract endpoints over 10 routes,
`dataSource.synthetic: true`, `chain.programDeployed: false`, `chain.programId: null`, and
`pricingModel.available: true` with `modelVersion: engine-2026-11-07`, `kind:
rule-based-bounded-estimator` and `fitted: false`. The analytics route for
`evt_syn_02` returns volume, sale count, average markup, median price, resold share, holders
and a daily series. Wallet verification is the one real cryptographic operation: the
challenge endpoint returned a nonce, and an Ed25519 signature is checked against the public
key it is given. The console and `/health` now tell one story: the number the console prints
is bounded arithmetic over fixture prices, and `/health` says the same thing in the model
block, naming no fitted model because there is none.

**Run the tests.**

```bash
python3 -m unittest discover -s tests
```

Observed at 2026-11-08T03:35Z: `python3 -m unittest discover -s tests` reports `Ran 610 tests in
23.958s`, `OK`. The count moves as the backend grows, so the command's own output is the number that
matters, not this line. It was 546 at 18:11Z, 453 at 17:36Z, 306 at 12:12Z and 293 twenty minutes before
that. The swarm harness carries its own suite, which this command does not collect:
`python3 -m unittest discover -s market_swarm/tests` → `Ran 274 tests in 1.028s`, `OK`.

**Regenerate the fixtures.**

```bash
python3 tools/build_fixture_store.py --check   # verify, writes nothing
python3 tools/build_fixture_store.py           # rewrite fixtures/synthetic_store.json
```

Observed with `--check`: `seed 20261107, 8 events, 76 tickets, 147 ledger rows`, ending with
`fixtures/synthetic_store.json matches a fresh build exactly`. 61 of those rows are priced
sales. The generator opens no socket and reads no clock; two runs write identical files.

**Not in this repository.** The Next.js frontend is the platform's own app, outside this
tree; a copy points here with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788`
(`docs/BACKEND.md`), and `docs/frontend-honesty.patch` is the text only patch that makes its
screens state what the data is. No hosted demo, no deploy URL.

## Why the chain

The cap is a promise the platform cannot quietly break and anyone can verify. It is not a claim
that scalping is impossible.

1. **It binds us too.** The cap is written into the ticket's own record, and the program has no
   instruction that changes it afterwards. The platform cannot raise a cap quietly, and neither can
   we.
2. **The sale record is public and tamper-proof.** Every transfer of a hooked ticket, and the price
   it declares, is a ledger entry nobody can edit afterwards. The pricing engine reads that record,
   and so would a monitor-only mode where resale is legal, watching the market instead of capping it
   (the direction is decided by `records/F-decision-log.md` D11 for the region-cap work; the mapping
   from a jurisdiction to a policy is not built in this program, which records the code and does not
   interpret it, D16).
3. **Anyone can check the rule without trusting us.** The program, its arithmetic and every
   transaction are public, so a reader verifies the boundary instead of taking this file's word.

The limit is the price: the program checks the price a transfer declares, so the claim is that the
chain refuses over-cap resales through the platform, not that scalping is impossible. What else the
design does not stop is listed in `programs/cap_hook/README.md`.

## The ten features: eight tested, two blocked

**Added 2026-11-08.** One entry per feature of the ten-feature build. Each names one command that
runs it, the surface it is verified on, and the limit it carries. Two features are **not built and
blocked by a measured mechanism fact**, and they say so in their own entry rather than sitting in a
table that could read as shipped. The full record is
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md`.

**These commands run against the working tree, not against a clone.** Nothing here is committed, by
the operator's instruction. `HEAD` is `33d95b3` and carries none of the ten features: a fresh clone of
`HEAD` runs **574 tests**, `memo_program_id` does not exist in it, `tools/swarm_charts.py`,
`tools/doc_check.py`, `ticketpath/onchain/v2.py`, `ticketpath/core/forecast_score.py` and the whole
`market_swarm/` package are absent, and every command below fails there. Measured on a
`git clone --no-hardlinks` of this tree: `Ran 574 tests in 23.262s`, `OK`. The eight results, one per
command:

- Feature 1: `ImportError: cannot import name 'memo_program_id' from 'ticketpath.adapters.chain_client'`.
- Feature 2: `KeyError: 'matchesCurrentQuote'`.
- Feature 3: `can't open file 'tools/swarm_charts.py': [Errno 2] No such file or directory`.
- Feature 4: `tests/test_forecast_score.py` and `tests/test_onchain_v2.py` are untracked, `FAILED (errors=2)`.
- Feature 6: `tests/test_onchain_v2.py` is untracked, `FAILED (errors=1)`.
- Feature 8: the same file, `FAILED (errors=1)`.
- Feature 9: `ImportError: Start directory is not importable: 'market_swarm/tests'`.
- Feature 10: `tests/test_onchain_v2.py` is untracked, `FAILED (errors=1)`.

So every count below is a count of the working tree; the clone's whole suite is **574 tests**.

**When these commands were run.** Every command below was run on 2026-11-08 between 07:00Z and
07:30Z and re-run at 08:07-08:12Z with the same output, and that output is quoted as it printed. The tree was being edited by another agent while this
section was written, and one intermediate run caught that edit in flight: the suite at 07:22Z reported
`Ran 993 tests`, `FAILED (failures=77, errors=223, skipped=19)` in the console and
artefact-verification modules. The last reading in this pass, after that edit and a second one landed,
is `python3 -m unittest discover -s tests -t .` → `Ran 1058 tests in 30.275s`, `OK (skipped=26)`, at
07:47Z **on the working tree; the clone of `HEAD` is 574 tests and `OK`**. If a command below fails
for you, run `git status` before concluding a feature is missing.

### 1. Memo program id, per cluster

The memo instruction that commits a quote runs under a program whose id differs by cluster, so
`ticketpath/adapters/chain_client.py` carries a table and not a constant: `devnet` and `localnet`
resolve to `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, and `mainnet-beta` and `testnet` have no
entry at all. The publisher asserts the id in the transaction the cluster landed against the table's
id for the run's cluster, on both the fresh-send and the reuse path.

```bash
python3 -c "from ticketpath.adapters.chain_client import memo_program_id; print(memo_program_id('devnet'))"
```

Observed: `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`.

**The limit.** Mainnet-beta's id has not been measured, so it is not in the table: `memo_program_id`
raises `UnknownCluster` rather than borrowing devnet's, and the console answers `chain.memoProgram:
null` for such a cluster instead of failing the page. The `MemoSq4gq…` literal stays in the file
because documents quote it and the `ids` gate compares against it, but it is not a mapping for any
cluster. A local validator cannot land a memo under the measured id at all: its genesis holds that
address as a program-data stub that cannot execute, and no clone replaces it. That is measured and
quoted in `records/findings/40-memo-program-id.md`.

### 2. The console renders the recorded devnet artefact as recorded

The `[DEVNET]` block on the console prints the artefact's own fields (its instant, slot, block time,
signature, mint, program, memo program, the recommended lamports, both transfer legs and the
refusal's `6010`) and then, separately, whether the quote on screen is the one the chain recorded.
The two questions are two fields: `chain.state` says the file verified, `chain.matchesCurrentQuote`
says the number on the page is that number.

```bash
python3 tools/guidance.py --event evt_syn_02 --as-of 2026-11-07T18:34:29.183Z | python3 -c "import json,sys; c=json.load(sys.stdin)['chain']; print(c['state'], c['matchesCurrentQuote'], c['recorded']['asOf'])"
```

Observed: `verified True 2026-11-07T18:34:29.183Z`. At any other instant the same command prints
`verified False 2026-11-07T18:34:29.183Z`, and the page then says the quote it commits is not the
quote the file records, naming both ids and both instants. It prints both recommended numbers only
where they differ.

**The limit.** Recorded, not independently re-read: the page recomputes the quote hash from the
fields it prints and asks no cluster. `rpc_adapter.program_status` still answers
`programDeployed: false` with `askedCluster: false`, because it asked none, and carries the recorded
program id in a separate block with its source.

**[Corrected 2026-11-08T07:45Z. Two sentences above were stale and one claim was wrong. (1) The page
no longer says "the number on this page is computed now and is not the number the chain recorded":
that sentence printed on a page showing the same 1.38 SOL twice. The agreement sentence is now about
the quote, with both quote ids and both instants, and the recommendation is printed twice only where
it differs. (2) `TICKETPATH_RPC_ENABLED=1` does not enable a live re-read, and no flag on this server
does: the adapter opens no socket, and the page says so in its own sentence. The line that named the
flag is kept above because it is what the edit replaced.]**

### 3. Chart and animation assets, every one labelled SYNTHETIC

`tools/swarm_charts.py` generates five SVG assets and one index into `docs/charts/` from a
`market_swarm` dataset, and `verify` rebuilds each series from that dataset and compares. Every asset
carries the word `SYNTHETIC`, the dataset file name, the run id and the not-evidence sentence in its
`<title>` and in its visible text.

```bash
python3 tools/swarm_charts.py verify --out docs/charts
```

Observed on this machine: `PASS docs/charts: 5 asset(s) and the index, 4 chart kind(s), mode(s) capped, monitored`,
followed by four more lines (the label and not-evidence sentence in every title and visible text, the
series rebuilt from the dataset and matched on all five, and the two dataset digests re-checked), exit 0.

**The limit.** Every number on them is class E: scripted agents against a simulated gateway, not
observed prices. The datasets live in `.swarm-runs/`, which is git-ignored, so on a clone with none
present `verify` exits 3 with `PASS LABELS ONLY`: the labels and the internal consistency were
checked, the numbers were not. `docs/CHARTS.md` is the full account.

### 4. Forecast log on chain, scored off chain

`LogForecast` (tag 5) creates `["forecast", mint, as_of_unix]` once and refuses a second write with
`6024`. `ScoreForecast` (tag 6) creates `["score", forecast]` once (`6025`) and does not touch the
forecast account, whose sha256 is quoted before and after in the run's record. Only the record's
`authority` may write either (`6026`). `ticketpath/core/forecast_score.py` is the rule the forecast
commits by hash: the Winkler interval score at alpha = 1/5, integer arithmetic only.

```bash
python3 -m unittest tests.test_forecast_score tests.test_onchain_v2
```

Observed: `Ran 63 tests`, `OK` (63 at 07:29Z; it was 56 at 07:05Z, because the test file grew with a
concurrent program edit). On the clone of `HEAD` these two modules are untracked and the whole suite
is 574 tests.

**The limit.** The program stores `interval_score_micro` as supplied and recomputes only `covered`.
Nothing on chain recomputes the penalty, so a score above the band's width is a well-formed account
on the authority's word; this is a log with an arithmetic rule beside it, not an on-chain scorer. `ScoreForecast`
recomputes `covered` from the forecast's own ends and refuses a score below the band's width, but it
does not recompute the penalty term: `interval_score_micro` above that floor is the authority's
assertion, not a number the chain verified. The end-to-end proof ran on a local validator, not on a
public cluster.

**The v1 hole, which changes what the devnet deployment proves.** v1's `SetPendingPrice` and
`SetStatus` take no signer, so on the deployed devnet program any keypair can stage a price and flip a
ticket's status; an immutable deploy has no upgrade path, so that hole is in v1's bytes permanently,
and the devnet refusals prove the price predicate on prices the deploy key chose, not that a stranger
was kept from choosing them. v2 authenticates both instructions and refuses the exploit with `6026`;
the deployed v1 never will. `records/findings/37-program-v2-review-fixes.md` is the measurement.

### 6. Price floor

`TicketRecord.band_low_lamports` is the floor, and `0` means no floor. The hook refuses a staged
price below it with `6021 E_BELOW_FLOOR`, admits one exactly at it, and `InitializeRecord` refuses a
floor above the ceiling with `6022 E_BAND_UNSATISFIABLE` rather than creating a record no price could
satisfy.

```bash
python3 -m unittest tests.test_onchain_v2 -k TicketRecord
```

Observed: `Ran 6 tests`, `OK`. On the clone of `HEAD` the module is untracked and the whole suite is
574 tests.

**The limit.** The predicate is in the Rust program, so the proof that it refuses is a chain run:
on a local validator, 899,999,999 lamports was refused `6021` and 900,000,000 was admitted with the
jurisdiction in the log line, recorded at `records/onchain-v2.local.json` (git-ignored). That run is
the build's and the documentation pass did not re-run it, because the live test rewrites that file.
A record with `policy = 1` skips both price predicates, so no floor is enforced there.

### 8. Public price feed

`PublishBand` (tag 4) writes `["band", mint]`: low, high, as-of slot, published slot, sample size, a
refusal flag, a model hash and the authority that signed it. It is rewritable on purpose, because it
is a head and not a history: the history is the forecast log, and a score is a separate account so it
can never rewrite what it scores.

```bash
python3 -m unittest tests.test_onchain_v2 -k band
```

Observed: `Ran 2 tests`, `OK`. On the clone of `HEAD` the module is untracked and the whole suite is
574 tests.

**The limit.** No third-party program consumes the feed today, so the composability claim is
unproven: what exists is a readable account with its own uncertainty fields, and this repository is
the only reader. `refused` is stored, not enforced, and `low > high` is refused `6022` rather than
written. The account is authority-signed (`6026`), which is a permission and not a guarantee about
the number.

### 9. A live agent adapter, on tiny budgets

`market_swarm/forge_policy.py` is an opt-in path that lets one capped child model make a decision.
The scripted policies remain the default, and a budget is reserved before a child exists and settled
at the observed usage afterwards.

```bash
python3 -m unittest discover -s market_swarm/tests -t .
```

Observed: `Ran 436 tests`, `OK (skipped=2)`. On the clone of `HEAD` there is no `market_swarm/` and the
`tests/` suite is 574 tests.

**The limit.** The cap is parent-side: the child is spawned with no limit of its own, so a SIGKILLed
parent can leak a child with no wall clock and no token cap on it. The provider usage log is also
structurally blind to `--no-extensions` children, so 38 children spawned by another session rest on
their own session files alone. The live path is off unless `MARKET_SWARM_LIVE_LLM=1`; the measured
spend was one decision at 22,838 in, 157 out, 4,096 cache-read, $0.003532, and four children at
$0.011581380 in total, recorded in `records/findings/41-deepseek-live-adapter.md`. This pass spent
nothing.

### 10. Per-event jurisdiction and policy on the record

`TicketRecord.jurisdiction` is two bytes, an ISO-3166-1 alpha-2 code in uppercase, with `ZZ` for
unspecified, and `TicketRecord.policy` is `0` (capped) or `1` (monitored). The hook logs the
jurisdiction on every admitted transfer and skips both price predicates when the policy is monitored.

```bash
python3 -m unittest tests.test_onchain_v2 -k jurisdiction
```

Observed: `Ran 2 tests`, `OK`. On the clone of `HEAD` the module is untracked and the whole suite is
574 tests.

**The limit.** The program does not interpret the country code and does not map a jurisdiction to a
policy. It does not validate the code either: there is no list on chain to check it against, so a
wrong code is a wrong statement by the issuer, not a malformed account. Neither of the record's own
two bytes is on the wire contract: the event-level `jurisdiction` and `resalePolicy` fields in
`lib/types.ts` (under the comment "additive fields the live backend serves") are a different pair at a
different level, and D16 is the decision that says so.

**Where the mapping lives, and the conflict a reader should know about.** The program's part is the
two bytes and a policy flag; that is all this feature ships. The mapping from a jurisdiction to a
policy is a separate piece of work in this same repository by another session: a dated table of
instruments (`ticketpath/data/region-caps.json`), a resolver (`ticketpath/core/region_caps.py`), its
own decision entry (D11 in `records/F-decision-log.md`), its own design
(`records/REGION-CAPS-DESIGN.md`) and its own local-only program (`programs/region_gate/`). Both are
in the tree, and they are not yet reconciled: no instruction compares the record's two bytes with the
table's resolved policy, and nothing forces an issuer to write the code the table resolved. **The
reconciliation can only be nation-level**, because the record's field is `[u8; 2]` and 72 of the
table's 82 codes are subdivisions (`CA-ON`, `AU-NSW`, `US-CA`) that do not fit two bytes; the finer
mapping has nowhere to be written on the v2 record. Which of the two is the platform's answer is the
operator's to decide; this entry does not settle it, and nothing here deletes D11.

### 5 and 7: the artist fee and the flip tax, not built and blocked

**Feature 5 was an artist fee of 500 to 1000 bps paid to the artist's wallet from a
`TransferFeeConfig`; feature 7 was a flip tax at 1500 bps into a pool, rebated on how long the
holder held. Neither is built. Both are blocked by one measured fact about the token program.**

Token-2022 computes a transfer fee on the base-unit amount and rounds it **up**. At `decimals 0`,
`amount 1`, any rate from 1 to 9999 bps withholds the whole ticket: `withheldAmount = 1`, the
recipient receives 0. The ceiling is proven by `ceil(10 x 1500 / 10 000) = 2` on a ten-unit transfer,
and the same 1500 bps on `decimals 9` and 10^9 base units withholds exactly 150,000,000, so the
arithmetic scales with the amount and not with a price. On this mint the only two fees it can express
are 0 and the entire ticket, and a 5% artist fee is not one of them.

What survives is the operator's choice and this file recommends none of the three: a lamport fee
charged at the venue on the staged price, a recorded obligation settled off chain, or a divisible
mint. One measurement narrows the third: on a mint carrying both the fee and the transfer hook,
`WithdrawWithheldTokensFromAccounts` succeeds without the hook's accounts and does not invoke the
hook, so a pool and a rebate have working plumbing; only the rate is missing. `held_since_unix` is
written by the hook on every admitted transfer and nothing consumes it yet, `ClaimRebate` (tag 7) is
not implemented, and the two error names reserved for it (`6027`, `6028`) are declared in the source
and raised by nothing. The measurement, the four legs and the quoted RPC objects are
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md`.

## Region-aware resale caps

Resale law is not one rule. Ireland caps a secondary sale at the original price including fees,
Ontario added a cap in April 2026, New South Wales caps at face plus the fees actually paid (counted
at no more than 10% of face), and the United Kingdom has announced a cap that is **not law**. A
platform that applies one number everywhere is either breaking a law somewhere or refusing a lawful
sale somewhere. This is the feature that resolves that per event.

Three policies, decided by a table rather than by a model:

| policy | the law says | on chain |
|---|---|---|
| `capped` | resale above a limit is restricted | the hook refuses a staged price above the limit |
| `monitored` | a law in force establishes no price limit | the hook admits and logs the jurisdiction and the price |
| `unresolved` | the law could not be established from a primary source | the hook admits, logs `unresolved`, and the event may not claim lawfulness |

Run it:

```bash
python3 tools/region_harness.py --help
python3 tools/region_harness.py market_swarm/example-run.json --on-date 2026-12-01 --check     # resolve, write nothing
python3 tools/region_harness.py market_swarm/example-run.json --on-date 2026-12-01 --out tmp/run.json --run --dry-run
python3 -c "from ticketpath.core import region_caps as r; print(r.describe(r.resolve(['AU-NSW'], on_date='2026-12-01')))"
python3 -m unittest tests.test_region_caps tests.test_region_caps_table tests.test_event_jurisdiction tests.test_region_harness -q
```

`tools/region_harness.py` takes a draft run config that may name a `jurisdiction` per event and
writes the config the swarm's loader already accepts, plus a `.law.json` sidecar carrying the table
version, its SHA-256 and the reason for each event. **[Corrected 2026-11-08T08:15Z: the two commands
above used to name `draft-run.json`, which exists nowhere in the tree and which nothing creates. They
now name `market_swarm/example-run.json`, the file the swarm ships, which resolves cleanly and says
`no_jurisdiction_declared` for both its events; a draft that wants a jurisdiction adds
`"jurisdiction": "CA-ON"` (or any table code) inside an event object. Both commands were re-run at
08:09Z, exit 0.]** A hand-typed cap that is looser than the law is
**refused**, naming both ceilings; an unresolved jurisdiction is refused unless the operator passes
`--accept-unresolved`, which records that the law was not established.

The table is `ticketpath/data/region-caps.json` (version `2026-11-08.1`, 82 jurisdiction codes, 84
instruments), the resolver is `ticketpath/core/region_caps.py`, the design is
`records/REGION-CAPS-DESIGN.md`, and the law behind every row is
`records/findings/33-a-region-cap-law.md` with its five cluster records beside it. Each row carries its
instrument, a quoted provision, its dates, its coverage and a confidence grade; `announced_policy` is
a first-class kind and never binds.

**Verified on a local validator, not on devnet.** `programs/region_gate/` is a separate, local-only
crate (the proven devnet program `5EJ1GU3M4vn…` is untouched and is not this feature's program).
`python3 tools/region_local_proof.py` boots a `solana-test-validator`, deploys it, and runs eleven
legs as real transactions: the capped ceiling admitted, ceiling + 1 refused `6010`, monitored at 3×
face admitted and logged, unresolved admitted and labelled, a tightening 1000 → 500 landing and then
binding, an upward tighten refused `6042`, monitored → capped allowed, a non-authority refused `6040`,
and a two-ticket transfer refused `6008`. Result: **PASS 11/11**, evidence in
`records/findings/34-region-caps-build.md`.

**The limits, stated where they can be read.** The table is not a survey: most jurisdictions are
`unresolved` because no primary source was read, and an unresolved event is the platform declining to
claim a rule it cannot show. A fixed money cap (Florida's $1 margin) is never converted into basis
points without an FX snapshot with a source and a time; without one it stays unresolved. The chain
sees the ticket it is asked to move and not a side payment outside the product (D9). And a law that
repeals a cap does not loosen an issued ticket: the chain can only tighten, because it cannot tell a
repeal from an organiser's convenience.

## Deployed on devnet, in part

The chain work is one invariant:

> A ticket cannot move without the program recording the hop, and the program will not
> record a price above the organizer's cap.

A transfer the program never sees is missing data, not just a policy breach, so the value
here is the integrity of the engine's own input, not a marketplace. The design is a Token-2022
mint with a transfer hook, plus a per-ticket record the program owns and appends to on every
custody move. Layout, instruction set, cap check, error codes and threat model are in
`docs/ON-CHAIN-DESIGN.md`, sections 2 and 3.

**What is deployed, and what that proves.** `programs/cap_hook/` is a native Rust program with
no Anchor in it, and it is on devnet at `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, with a
Token-2022 mint at `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV` carrying the transfer hook,
a metadata pointer and token metadata. At face 1.0 SOL and cap 2,500 bps, a transfer at
1,250,000,000 lamports landed and one at 1,250,000,001 was refused by the cluster with
`6010`, as a failed transaction carrying its own signature and block time. The three
signatures, the memo, the slots and the refusal's error are recorded in
`records/devnet-artefacts.json`, and the console renders them when the page is on the exact
state that artefact commits to (see below). What the program does **not** do is written out in
`programs/cap_hook/README.md`: no hop record, no destination check, no verified-wallet gate, no
escrow, no nullifier. So the sentence the deployment earns is the second half of the invariant
above, and not the first.

**What the devnet pair does not prove, stated 2026-11-08T07:45Z.** v1's `SetPendingPrice` and
`SetStatus` take no signer, and an immutable deploy has no upgrade path, so on the deployed program any
keypair can stage a price and flip a ticket's status. The devnet refusals prove the price predicate on
prices the deploy key chose; they do not prove that a stranger was kept from choosing them. v2 closes
the hole with `6026` and the sealed artefact re-runs the reviewer's exploit as two refused
transactions, and v2 has run only on a local validator. `docs/ON-CHAIN-DESIGN.md` §0 states this in
the same section as the instruction table.

**The memo program id is a property of the cluster, not a constant.** The memo that commits a
quote runs on devnet at `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, measured from the proven
transaction on 2026-11-08, while the `solana` CLI's own memo program, which this repository names
for mainnet-beta, is `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`. `chain_client.MEMO_PROGRAMS`
maps each cluster to its id, an unmeasured cluster raises rather than borrowing a neighbour's id,
and the publisher reads the id back out of the transaction it landed and refuses a mismatch.
`records/findings/40-memo-program-id.md` is the measurement, with the quoted account keys.

**[CORRECTED 2026-11-08T08:30Z. The sentence above names `MemoSq4gq…` for mainnet-beta and says the
table maps each cluster. Both halves are now false against the code, and this note is the correction
rather than an edit, so the earlier claim stays legible. `mainnet-beta` is not in `MEMO_PROGRAMS`:
nothing was ever read off mainnet, and the installed CLI was later measured building a
`Memo4c2p…` memo, which contradicts the row that used to sit there. `testnet` is not in the table
either. Both clusters are refused, and the two surfaces refuse differently: `memo_program_id` raises
`UnknownCluster` naming the clusters the table covers, and the console answers
`chain.memoProgram: null` for the server's cluster instead of failing the page. The two literals stay
in `chain_client.py` because this file and `docs/ON-CHAIN-DESIGN.md` quote them and the `ids` gate
compares quoted ids against them.]**

The cap is checked inside the hook, against a price staged into the program's own record
account by `SetPendingPrice` immediately before the transfer, and the transfer and the stage are
sent in one transaction so the staging cannot be clobbered between the two. That is a departure
from `docs/ON-CHAIN-DESIGN.md` §3.9, which puts the check in a `transfer_ticket` instruction;
the program's README states the departure and why it is the smallest arrangement that can still
refuse. A direct `spl-token transfer` of a hooked ticket therefore fails inside the hook rather
than bypassing the cap.

**`/health` still reports `programDeployed: false`, `programId: null`, `rpcEnabled: false`, and
that is not in tension with the deployment.** The chain adapter opens no socket: it reports what
it has asked the cluster, which is nothing. The `[DEVNET]` block on the console is rendered from
`records/devnet-artefacts.json` after recomputing the quote hash from the fields on the page, and
it says in its own sentence that it is recorded rather than independently re-read. A live read
would need `TICKETPATH_RPC_ENABLED=1`. **[This paragraph replaces "No program is deployed on any
cluster. There is no mint, no transaction and no signature in this repository", 2026-11-08T03:45Z.
Verified by reading the cluster: `getAccountInfo` on the program id returns
`executable: true`, and `getTransaction` on the refused leg returns
`InstructionError [0, Custom 6010]` with the program's own log line.]**

**[Corrected 2026-11-08T07:45Z. The last sentence above is wrong: `TICKETPATH_RPC_ENABLED=1` does not
cause a live read, because `rpc_adapter` opens no socket on any flag, and the page now prints "A live
re-read is not implemented in this build, so no flag on this server makes the page read the chain."
The flag is still configuration the adapter reports; it is not a switch. And the `[DEVNET]` block no
longer renders only "when the page is on the exact state that artefact commits to": it renders the
recorded block at every state the file verifies, and says separately whether the quote on screen is
the recorded quote.]**

**The toolchain is installed here.** Agave CLI 4.3.2, `spl-token` 5.6.1 and `cargo-build-sbf`
4.4.0 under one install root and rustc 1.99.1 under the usual cargo home, all reachable from a
login shell (`bash -lc 'which solana spl-token cargo-build-sbf rustc cargo'` resolves all five).
A non-login shell still prints nothing for them, which is why an earlier reading of this file said
there was no toolchain. **[Corrected 2026-11-08T03:45Z; versions measured this pass.]**
`ticketpath/onchain/sim.py`, the Python mirror of the same state machine with the same error
codes, is still what the console renders under a `[SIMULATED]` label: it proves the arithmetic and
the ordering, and nothing about any cluster.

`tools/devnet_publish.py` is how the deployment is made and remade. Nine steps, each of which
reads the cluster before it writes, so a run that dies halfway is finished by running it again: the
mint's address is written down before the transaction that creates it, a transfer's signature is
recorded the instant it is sent, a rerun asks the cluster rather than resending, and transport
failures are retried four times before the run stops and says so. `records/findings/28` is the
account of that fix and `tests/test_devnet_publish.py` is its test, 81 tests over the publisher,
the resume file and the instruction bytes. `records/devnet-progress.json` is the resume file: git
ignored, mode 0600, public identifiers and integers only. `docs/ON-CHAIN-DESIGN.md` section 6 is the
remaining runbook for the parts that are design rather than code.

**[Corrected 2026-11-08T08:15Z: the count above read 56. Measured at 08:07Z,
`python3 -m unittest tests.test_devnet_publish` is `Ran 81 tests`, `OK`; 56 was the 03:45Z figure and
is kept as the sentence's history.]**

One stale pointer, fixed: `/health`'s `chain.designDoc` named `docs/ON-CHAIN-FOR-LAPTOP.md`,
the superseded one-page pointer. It now names `docs/ON-CHAIN-DESIGN.md`, the design.
`records/ON-CHAIN-RECONCILIATION.md` records why, and `records/REPO-CONSISTENCY.md` records the
change and the command that shows it. **A server started before that change keeps the old value
in memory**, so restart it before reading `/health` and expecting the new one.

## What this data is

`fixtures/synthetic_store.json` is a generated fixture, not ticket data. It is produced by
`tools/build_fixture_store.py` from event specifications in that same file, with seed
`20261107`. Every payload the backend serves from it carries a `dataSource` label saying it
is synthetic, and the console prints that label in a banner at the top of the page.

It is deliberately over-sampled for demonstration. On the five events that have resales, 62%
to 77% of tickets resold at least once, against roughly 5.1% in the real market: twelve to
fifteen times the real rate, because a resale record has to contain resales for a resale
computation to be shown on it. Each event's description states that ratio in its own text,
computed from its own rows at build time.

Do not conclude any of the following:

- That any markup, price or distribution here is evidence about tickets. Markups were drawn
  from rules per regime so three cases could be shown; nothing was fitted or calibrated.
- That the series is a price path. The draws are independent of time to event, so there is no
  decline and no end game uptick, and a trend read off it is noise.
- That any event, venue, organizer or city describes something that happened.
- That any ticket, price or custody row here is on chain. The cap hook is deployed (see
  "Deployed on devnet, in part"), and every one of the fixture's 147 ledger rows still carries
  `signature: null` and `slot: null`: no cluster knows any ticket in this repository.
- That any accuracy figure exists. No model has been fitted; the console's recommendation is a bound
  with a declared width whose parameters are declared, not estimated from real data.

## How the research is organised

Every conclusion carries an evidence class, A to E: A is direct ticket market evidence, B is
evidence from a related market, C is mathematical or statistical theory, D is a plausible
hypothesis with a mechanism and no evidence, E is a speculative opportunity recorded so it
is not lost. `SIM` marks something established by simulation here under stated assumptions,
and `UNVALIDATED` marks a claim whose validation needs data the programme does not have.
Findings are append only, conflicts are recorded rather than resolved quietly, and
`records/README.md` holds the conventions in full.

One line per record file:

- `README.md` the index: the six records, the evidence classes, the writing rules.
- `00-data-situation.md` the Phase 0 audit of what data actually exists on this machine.
- `00-prior-direction-index.md` the earlier direction documents and the decisions they fix.
- `A-research-ledger.md` every research question, its status, finding, class and sources.
- `B-mathematical-kb.md` formulations, assumptions, derivations, parameters, failure modes.
- `C-variable-registry.md` every candidate feature, its mechanism, availability and leakage risk.
- `D-model-registry.md` every model considered, its data cost, evidence and recommended role.
- `E-data-source-registry.md` providers, depth, frequency, licence, cost and reliability.
- `F-decision-log.md` decisions, rejected approaches, conflicts, open and closed questions.
- `FIXTURE-STORE.md` what the synthetic store contains, what it must not be read as, its invariants.
- `CONTRACT-MAP.md` the endpoint contract field by field, and what this backend can answer.
- `CONTRACT-CONFORMANCE.md` the contract as a test that addresses every route over a socket.
- `CORRECTIONS-APPLIED.md` what an independent verification round found and what changed.
- `DEMO-PROOF.md` which screens served backend numbers, measured, written at a time when no screenshot existed; there is a headless browser on the build machine now, `docs/SHOTS.md` is the account of it and `tools/shot.py` is the helper that captures a page (`README.md` corrected 2026-11-07T18:45Z, see the pack's §2.5 item five).
- `FRONTEND-INTEGRATION.md` what the frontend renders and which numbers are ours; partly superseded.
- `FRONTEND-HONESTY-PATCH.md` the text only patch that makes the frontend say what the data is.
- `ON-CHAIN-RECONCILIATION.md` why the design document replaced its earlier sibling.
- `BUILD-SPEC-NIGHT.md` what the overnight build was told to build, module by module.
- `SUBMISSION-PACK.md` the video script, submission text, field checklist and last hour checks.
- `findings/` per investigation reports, append only, the primary record the six index (`git ls-files records/findings | wc -l` → 32 tracked, and 42 on disk at 2026-11-08T03:35Z: numbers 20 and 23 to 31 are written and uncommitted. This line said twenty-nine, and twenty-seven before that). **[Corrected 2026-11-08T08:15Z: measured now, `ls records/findings/*.md | wc -l` is 52 on disk and 20 of them are untracked, not 42 and 10. The ten extra entries are the ten-feature and region-cap evidence: `33-a-region-cap-law.md` with its `33-b-region-cap-law-sources/` directory, `34-region-caps-build.md`, `35-live-llm-agents.md`, `36-transfer-fee-on-a-one-unit-ticket.md`, `37-program-v2-review-fixes.md`, `38-region-caps-local-validator.md`, `39-visitor-identity.md`, `40-memo-program-id.md` and `41-deepseek-live-adapter.md`. Eight of the ten features rest on evidence that is not committed.]**
- `STATE-OF-PROJECT.md` the read-only measurement of the tree, the chain and the console, rewritten at 2026-11-08T03:45Z.
- `BUILD-REPORT-CONSOLE.md` what the console pass built and where it departed from its spec.
- `FINAL-PROOF.md` the end-to-end proof run: what was executed, what it showed, what it did not.
- `FINAL-PROOF-2.md` the second proof run: the README's own commands, the live frontend's write check, and the
  64-state sweep.
- `DELIVERABLE.md` the Phase 8 integrated specification, 22 sections, assembled at 12:40Z. It was a
  stub marked NOT WRITTEN YET before that time and is not one after it; `records/README.md` was
  corrected on 2026-11-07T14:00Z and this line was not (**corrected 2026-11-08T03:45Z**; the
  correction record is `DELIVERABLE.md` §R2-31).
- `REPO-CONSISTENCY.md` the consistency pass over this tree: every change, its evidence, and the
  claims that could not be fixed.

## Layout

```
ticketpath/    the backend. server.py is the route table and nothing else
  api/         one module per contract area: events, tickets, analytics, wallets, health
  core/        pure functions: no network, no clock except an injected now()
  adapters/    the only paths to the ledger file, Solana RPC and the pricing model seam
  console/     the server rendered page served at /
  onchain/     the Python mirror of the state machine, simulated only
programs/      cap_hook/, the native Rust transfer-hook program that is deployed on devnet; its
               target/ directory is generated, git-ignored, and never committed
market_swarm/  a separate package: a bounded agent swarm that trades synthetic tickets through that
               program on a local validator and writes synthetic-labelled datasets. Imports nothing
               from ticketpath/ and is imported by nothing in it. See records/findings/31
tests/         unittest tests over 36 test modules, plus store_arithmetic.py; the run prints the count
fixtures/      synthetic_store.json and the note saying what it is not
tools/         build_fixture_store.py the deterministic fixture generator, guidance.py the console
               payload as JSON, devnet_publish.py the idempotent publisher, solana_sign.py the
               out-of-process signer, public_safety.py the tree check, shot.py the capture helper
docs/          backend notes, the on-chain design and runbook, the frontend labelling patch
records/       the six research records, the build and submission packs, findings/, and the devnet
               artefact the console's chain slot reads
```

**[Layout corrected 2026-11-08T03:45Z: `programs/` and `market_swarm/` were missing and the test
module count was 34. Every other line in this block was re-checked against the tree.]**

The root also holds `AGENTS.md` and `RESEARCH-PROGRAM.md`, the brief and the research
standard this work was held to, and `NIGHT-BRIEF.md`, `NIGHT-LOG.md`, `NIGHT-QUEUE.md`, the
overnight build's working log.

## How this was built

Most of the code and the documents in this repository were written by AI coding agents, orchestrated by
the operator: agents wrote the backend, the engine, the console, the test suite and the research records,
and he set the briefs, checked the claims against the commands that produced them, and made every decision
that ships. The commit trailers name one of the tools on six of the repository's nineteen commits
(`git log --format='%(trailers)'`). This is not a claim of solo human authorship and no part of this
repository should be read as one. No generative model is implemented inside the product: the pricing
engine is bounded arithmetic with declared parameters, and `/health` reports `fitted: false`.

## Licence and status

MIT. The text is in `LICENSE`, and the copyright line names the holder:
`Copyright (c) 2026 Andrew Radu`.

Status: a local build with one deployed program. The cap hook is on devnet and its boundary is
proven there by a landed transfer and a refused one, recorded in `records/devnet-artefacts.json`;
the design's hop record, destination check and verification gate are not built. There is no hosted
demo and no deploy URL, so the console and the frontend are loopback surfaces. Every price and
every custodian in this repository comes from a synthetic fixture. The pricing seam is populated by
a rule-based bounded estimator with no fitted model behind it, and `/health` says so in those words
(`kind`, `fitted`, `note`). The research records say what is established, what is designed and what
is still a hypothesis, and `records/DELIVERABLE.md` is the Phase 8 specification with a status per
section. **[Corrected 2026-11-08T03:45Z: this paragraph read "Nothing is deployed, no program exists
on any cluster", which the deployment made false. The hosted-demo and no-fitted-model sentences are
unchanged and still true.]**
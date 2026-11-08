# BUILD-STATE MATRIX: every claim a 2:00 video might make, and what the record proves

**Written:** 2026-11-08 by the video-inputs pass, from a read-only survey of this tree, the
git state, the running record and four live reads of the public devnet cluster. **Nothing was
built, fixed, committed, pushed, edited or started.** The only file written is this one. No
test suite was run; another agent holds that surface and the tree is in flux.

**Why this file exists.** A video script is a list of claims about a build, and the build in
this repository is a mixture of things that ran, things that ran only on this machine, things
that ran only in a simulation, things that are blocked by a measured fact, and things that are
still ideas. The record already knows this about itself and says so in several places. This
file collects the per-claim version in one place so the script writer can be held to it
sentence by sentence.

**Labels used, and only these.**

| Label | Meaning here |
|---|---|
| **BUILT** | Code exists at a named path, it runs, and the claim about it was executed on a named surface. |
| **PARTLY BUILT** | Some of the claim was executed and some of it was not. The row says which half. |
| **IDEA** | No code implements it anywhere in the tree. A finding, a cost estimate or a design may exist. |
| **BLOCKED** | Not built, and the record names a measured mechanism fact that stops it from being buildable as specified. Not a synonym for unfinished. |

**Evidence tags used on every line.**

- **[M] MEASURED**: a command output, a file field, a byte count, a chain read, or arithmetic on
  those, quoted with its `path:line`. Where I re-measured something this pass, the row says so.
- **[I] INFERENCE**: reasoning from measured facts. Never presented as a fact about the world.

Two further words from `records/README.md` are used with their fixed meanings and are not
evidence classes: **SIM** (established by simulation under stated assumptions, says nothing
about ticket markets) and **UNVALIDATED** (validation needs data this programme does not have).

**Path rule obeyed.** Every path in this file is repository-relative. The sibling app is
`../ticketing-frontend` (the operator's tree) and `../ticketpath-demo` (the copy the honesty
patch was applied to). No home path, no user name, no process id, no port, no service name, and
no record screen content is reproduced here, because this file lands in a public repository.

---

## 1. The tree at the moment of writing

| Fact | Value | How |
|---|---|---|
| `HEAD` | `33d95b3`, on `main`, equal to `origin/main`, nothing unpushed | [M] `git log --oneline -12`, `git status` |
| Working tree | **42 modified files, +7,873 / −660, and 55 untracked entries** | [M] `git diff --stat`, `git status --porcelain` |
| The devnet proof | `records/devnet-artefacts.json` is **untracked** | [M] `git status --porcelain` |
| The charts | `docs/charts/` and `docs/CHARTS.md` are **untracked** | [M] same |
| The swarm | `market_swarm/` is **untracked** | [M] same |
| Findings on disk | **53**, of which **32 tracked** | [M] file count, `git ls-files records/findings \| wc -l` |
| State of the project | `records/STATE-OF-PROJECT.md` is **untracked** and was last extended 2026-11-08T08:20Z | [M] `git status`, file header |
| Test count | **a moving number, and the record's own readings moved five times in one hour**: `971` at 07:05Z, `1007`, then `1053` (`Ran 1053 tests in 29.044s`, `OK (skipped=26)`) at 07:31Z, with `Ran 981 tests … FAILED (errors=10)` and a three-failure reading interleaved from concurrent edits | [M] `records/STATE-OF-PROJECT.md:201` and `:219-226`, `records/findings/37-program-v2-review-fixes.md:246-260` |
| Consequence for a video | **A judge who clones the public repo today cannot see the artefact, the charts or the swarm.** `records/STATE-OF-PROJECT.md` §A7 says so and the file's own opening calls the gap "the first thing to fix" | [M] `records/STATE-OF-PROJECT.md:25` and `:347-357` |

---

## 2. The beats

### B1. The on-chain cap refusing a scalper (the 6010 refusal)

**Label: PARTLY BUILT.** The refusal is BUILT on a public cluster. The *scalper* is local-only.
No single artefact in this tree shows an agent being refused on devnet, and the record says so
in the words a script must not smooth over.

**Evidence**

- The predicate and its code are in the deployed program: `CapExceeded = 6010` at
  `programs/cap_hook/src/error.rs:60`, table row at `:15`. [M]
- The refusal is a **function of a staged price**, and the stage and the transfer are sent in
  one transaction: `SetPendingPrice` immediately before the transfer,
  `records/findings/31-trading-swarm-harness-design.md` "The trade lifecycle"; the runbook
  statement is `README.md:424-428`. [M]
- Devnet refusal, re-read by **this pass** from `api.devnet.solana.com`: signature
  `22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79`,
  slot `519846008`, blockTime `1794099023`, `err: {"InstructionError":[0,{"Custom":6010}]}`,
  program log `ticketpath: cap exceeded price=1250000001 face=1000000000 cap_bps=2500`. [M]
- The scalper being refused exists only on a local validator, in a dataset that is
  git-ignored: `.swarm-runs/sw20261108T041005Zc9f3-evt_live-SYNTHETIC.jsonl`, rows 5, 7 and 9,
  asks of `1,270,000,000`, `1,280,000,000`, `1,290,000,000` against a ceiling of
  `1,250,000,000`, each `status: refused`, `error_code: 6010`, its own signature, its own slot,
  `hop_index: null`, `"chain": "local-validator"`, `synthetic: true`. [M] (I read all of this
  from the file this pass.)
- `records/findings/32-video-beats-and-storyboards.md:29-40` states the split in one paragraph:
  the devnet pair came from the publish script's boundary test, not from an agent, and the agent
  rows are UNVERIFIED by anyone outside this machine. [M]

**A judge can check:** the devnet signature and nothing else in this beat. They can look up the
failed transaction, see `Custom: 6010`, and read the program's own log line. They cannot check
the scalper row without a copy of a git-ignored file.

**The video must not say:** "we refused a scalper on devnet"; that the three refused asks on
screen are on a chain anyone can reach; or that the cap blocks a determined seller (B17).

**The honest sentence:**

> "This is one transaction being refused by the program on a public cluster: a transfer staged
> at one lamport over the ceiling comes back with the program's own error code and its own
> signature. The scalper agent being refused three times is a run on a local validator, and the
> dataset is labelled synthetic."

---

### B2. The devnet boundary pair: admitted at 1,250,000,000, refused at 1,250,000,001

**Label: BUILT.** This is the strongest thing in the submission and it survived re-reading.

**Evidence**

- `records/devnet-artefacts.json:31-33` admitted leg: `priceLamports 1250000000`, signature
  `E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf`,
  slot `519845933`, `error: null` (`:29`). [M]
- `records/devnet-artefacts.json:37-41` refused leg: `priceLamports 1250000001`, signature
  `22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79`,
  slot `519846008`, `error: "custom program error: 0x177a (6010 E_CAP_EXCEEDED)"`. [M]
- Face and cap in the same file: `faceLamports 1000000000` (`:14`), `capBps 2500` (`:4`). The
  ceiling is `1,000,000,000 x 12,500 / 10,000 = 1,250,000,000`. [M] arithmetic on the file.
- Re-read **live by this pass**: admitted leg `err: null`, slot 519845933, blockTime 1794099006,
  log `ticketpath: cap admitted price=1250000000 face=1000000000 cap_bps=2500`; refused leg as
  in B1. Program account `executable: true`, owner `BPFLoaderUpgradeab1e…`, space 36 bytes. [M]
- The record's own version: `records/STATE-OF-PROJECT.md:127-133` (cluster table) and `:135-138`
  ("the boundary is proven on a public cluster, not only on a validator"). [M]

**A judge can check:** everything. Two signatures, two slots, two block times, one error code,
and the program account. This is the only beat where the artefact and the chain are the same
artefact.

**The video must not say:** that this pair proves the program stops a *seller* from choosing the
price, or that it proves hop recording, destination checks or a verified-wallet gate. The
program does not do those (`README.md:400-404`, `programs/cap_hook/README.md`). And see B17 for
what finding 37 added about who can stage a price on the deployed v1.

**The honest sentence:**

> "Same ticket, same face value, one lamport apart. At the ceiling the transfer lands; one
> lamport over, the cluster refuses it with the program's error code, in a failed transaction
> with its own signature. Both are on devnet and both can be looked up."

---

### B3. The publish leg: the quote committed in a memo, with its model version and recommended lamports

**Label: BUILT**, with one measured internal inconsistency the video must not paper over.

**Evidence**

- Memo transaction: `records/devnet-artefacts.json:15, 21-24`, signature
  `2Lx6cboK8kvuJ7H6w2CELvZg3xF7cSHtBTSBXqi1w6KN2eXkQ6skqNPwnT5iVVAdrfBs5LiAau3pXiBMTtZMGCPZ`,
  slot `519845921`, blockTime `1794099003`, `modelVersion engine-2026-11-07`,
  `recommendedLamports 1380000000`. [M]
- Re-read **live by this pass**: the transaction resolves, `err: null`, and its logs carry
  `Program Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH invoke`, `Memo (len 100)`, and
  `ticketpath:quote:q-18f4ec73dd8d8fd1:d90cb033491701947b711c6e07139282d1faae6041b77f5a99161bdd1f177b12`. [M]
- The hash is recomputable by the repository's own code: `load_artefact(
  "records/devnet-artefacts.json")` returned `state: verified` and quote id
  `q-18f4ec73dd8d8fd1` when I ran it this pass. [M]
- **The inconsistency.** The same file records `faceLamports 1,000,000,000` and `capBps 2,500`,
  which puts the resale ceiling at `1,250,000,000`, while `recommendedLamports` is
  `1,380,000,000`, i.e. **130,000,000 lamports above the ceiling the file's own face and cap
  imply**. [M] arithmetic on `records/devnet-artefacts.json:4,14,21`. The console prints this
  out loud: I rendered the page this pass and it reads "The face and cap the file states put the
  resale ceiling at 1,250,000,000 lamports. The recorded recommendation of 1,380,000,000
  lamports is above that ceiling." The source is `ticketpath/core/labels.py:334-340`. [M]
- The publish path is resumable and reads the cluster before each write:
  `README.md:452-460`, `records/findings/28-devnet-resume-and-retry.md`. [M]
- The memo program id is per cluster and measured, not assumed: `MEMO_PROGRAMS` maps `devnet`
  and `localnet` to `Memo4c2p…` (`ticketpath/adapters/chain_client.py:52-78`), and an unmeasured
  cluster raises (`:130-135`). [M] I read the table this pass. Note this contradicts
  `records/F-decision-log.md` D10; see the collision report.

**A judge can check:** the memo transaction, the memo text, and the hash recomputation with the
repo's own code once the artefact is committed.

**The video must not say:** that the published number is the price the cap supports, that the
quote was scored, or that the recommendation came from a fitted model. Do not read `1.38 SOL`
over the devnet shot without saying which record it came from: the store's tier face is 1.20 SOL
and the artefact's is 1.00 SOL, and that is exactly the sort of swapped denominator a judge who
reads both files will catch.

**The honest sentence:**

> "The engine's number was committed before anything moved: a memo on devnet carrying the quote
> id, a hash of the quote and the engine version, so the number cannot be quietly revised. The
> cap is our own program, not the memo program, and the file's own face and cap put the ceiling
> below the number it recorded. The console says that on the page."

---

### B4. The pricing engine itself: what it computes, what is fitted, what validation exists

**Label: PARTLY BUILT.** The arithmetic is BUILT and runs. Nothing is fitted. No out-of-sample
score exists. The declared width is known to under-cover at the shipped default, and the record
measured that.

**Evidence: what it computes**

- Four required outputs, and what became of each: `records/DELIVERABLE.md` §2.1. [M]
- Value level is `face x exp(mean log(price/face))` over the tier's own marks; the band is
  `level x exp(∓ z·max(τ, 0.10))` with `z = 1.6449`; the width is exactly `2zτ` in logs. [M]
  `ticketpath/core/value_band.py:39-43`, and `records/STATE-OF-PROJECT.md` §A5 re-derived it
  from the payload and found agreement to the lamport.
- Re-measured **by this pass** through `tools/guidance.py`: for the demo event and tier at the
  pinned instant, `recommendedLamports 1,380,000,000`, `bandLoLamports 1,380,000,000`,
  `bandHiLamports null`, `recommendedIsFloor true`, `noUpperBound true`,
  `basis lower_bound_at_cap`, evidence "12 sales, 9 at the ceiling, 5 events with resale". For an
  uncapped event at the same instant: `930,549,431` with band `669,676,793` to `1,293,045,022`. [M]
- The refusals are computed, not decorative: the pinned payload carries
  `not_identified`, `no_demand_response`, `no_fee_model`, `cap_mass_dominates`,
  `no_upper_bound`, `insufficient_events`. [M] Same tool.
- The sale-probability object is refused by name and the interior optimum does not exist:
  `records/STATE-OF-PROJECT.md` §A5, `records/BUILD-SPEC-NIGHT.md:288-296` (the banned sentence).

**Evidence: what is fitted**

- **Nothing.** `pooled.method` on the live payload reads `"declared"`, because the between-event
  variance is declared below nine events: `ticketpath/core/value_band.py:43` and `:129-146`. [M]
  I read `method: declared` out of the payload this pass.
- The engine's own disclosure sentence: `ticketpath/core/labels.py:209-215`, "The model is not
  fitted. {n_events} events have completed in the observation window and {m} have any resale
  activity, so the between-event dispersion cannot be estimated and no out-of-sample score
  exists. What follows is the pooled prior with its width declared, not estimated." [M]
- `/health` reports `fitted: false` and `kind: rule-based-bounded-estimator`
  (`records/SUBMISSION-PACK.md:586-592`, and `:408-411`). [M]
- **No model in the registry is validated, and the registry forbids the number outright:**
  "no model in this file is validated, none may be marked validated, and no accuracy, lift,
  coverage or error number appears anywhere in it" (`records/D-model-registry.md:35-37`). [M]

**Evidence: what validation exists, and what it found**

- A simulation study exists, and it **failed two of its three arms**: `A PASS, B FAIL, C FAIL`,
  37 of 43 pre-declared conditions held (`records/DELIVERABLE.md:2165-2170`). [M]
- At the API default `tau = 0.20`, the declared band covered **0.620 / 0.694 / 0.718** of draws
  at 2 / 5 / 20 events against a nominal 0.90 (`records/DELIVERABLE.md` §20.6 item 2). [M]
- At two events and a true tau of 0.30, coverage is **0.805** against the pre-declared
  `[0.87, 0.93]` (§20.6 item 1). [M]
- A SIM study cannot validate the estimator anyway: "A SIM study can only test an estimator
  against its own assumption" (`records/CORRECTIONS-APPLIED.md` R2-14). [M]
- The engine review's verdicts, dated 2026-11-07T14:25Z: Mathematics STANDS-WITH-NARROWING,
  Honesty **FAILS**, Code STANDS-WITH-NARROWING, Refusals STANDS-WITH-NARROWING
  (`records/findings/10-final-review.md:38-43`). Two specific narrowings that survived into the
  tree: the band is not trimmed to the cap in force and can exceed it
  (`records/findings/10-final-review.md` N2), and the ticket-day denominator runs past the event
  end so the printed rate falls as the cut advances (N3). [M]

**A judge can check:** the arithmetic, by hand, from the payload or the page: the `[EXACT]`
ceiling line is integer arithmetic that re-computes. The refusal list is printed with the missing
observation beside each. Nothing about the engine's accuracy is checkable, because there is no
accuracy.

**The video must not say:** any accuracy, coverage, error, lift or significance number; that
anything is fitted, trained, calibrated or validated; that the simulation validated the band;
that the number is a forecast, an estimate or a prediction; that the band is a 90% interval; or
that the recommendation is the revenue-maximising price.

**The honest sentence:**

> "The engine does arithmetic on the record and refuses the three questions the record cannot
> answer, naming the missing observation each time. Nothing here is fitted: the width is a
> number somebody declared, and the page says so. On a capped event the only honest statement is
> a floor."

---

### B5. The trading swarm: what ran, where, how many agents, rounds, rows, refusals

**Label: PARTLY BUILT.** The harness is BUILT and tested. It ran on a **local validator** and in
simulation. The live-model runs happened and their datasets were overwritten. **Every number it
produces is synthetic and is E-class evidence about nothing real.**

**Evidence**

- The package exists and is separate: 12 Python files at the top level of `market_swarm/`, **10 of
them working modules** plus `__init__.py` and `__main__.py`, and 15 test modules, **436 test
methods** counted by grep this pass; the record's suite readings agree
(`records/STATE-OF-PROJECT.md` §A4). [M]
- **Local validator, scripted, 4 agents, 4 rounds, one event**:
  `.swarm-runs/sw20261108T041005Zc9f3-evt_live-SYNTHETIC.jsonl`, 10 rows, `ok 6 / refused 3 /
  skipped 1`, wall 8.759 s, `dry_run: false`, `cluster: local-validator`; and the paired
  monitored mint `.swarm-runs/sw20261108T041235Z55ad-evt_live_monitored-SYNTHETIC.jsonl`, 11
  rows, `ok 9 / skipped 2`, `refused 0`. [M] (Both read by me this pass, and both match
  `records/findings/31-trading-swarm-harness-design.md` "The full harness end to end".)
- **Simulation, 9 agents, 12 rounds, two events**: `.swarm-runs/sw20261108T054830Z6297-…`:
  capped dataset 51 rows (`ok 32 / refused 4 / skipped 15`), monitored dataset 55 rows (`ok 32 /
  skipped 23 / refused 0`), 106 rows in the pair, `dry_run: true`. [M] (I counted the statuses;
  note the earlier record's "106 rows" is the pair's total, not the monitored dataset alone.)
- **Live LLM children did run**, six personas, two rounds, against the real hook on a local
  validator: `records/findings/35-live-llm-agents.md:88-95` gives `capped 12 rows (ok 11, skipped
  1) … 82.2 s` and `monitored 12 rows (ok 10, skipped 2) … 107.3 s`. [M] as recorded.
- **And those two datasets are gone.** `records/findings/35-live-llm-agents.md:139-143`: the
  dry-run re-runs reused the same run id, so the files on disk under those names are the
  **dry-run** namesakes. [M] I confirmed this: `.swarm-runs/sw-llm-capped-…meta.json` carries
  `dry_run: true`, 12 rows, `ok 10 / skipped 2`, and the capped dataset contains **no refused
  row and no signature at all**. [M]
- **And the validator path does not currently reproduce**:
  `records/findings/35-live-llm-agents.md:133-138`, invalid instruction data on record init after
  the program was rebuilt mid-session. [M] (Note the tree moved again while this file was being
  written: `records/STATE-OF-PROJECT.md` §A4 was re-measured from 1007 to 1053 tests between two of
  my own reads, and finding 37 §5's quoted suite line changed with it. Treat every count here as a
  timestamp.)
- **No devnet run, ever**: `records/findings/31-trading-swarm-harness-design.md:258-263`, "No
  devnet run … `devnet` cluster is code-complete and untested". [M]
- Label enforcement is code, not intention: the writer refuses an unlabelled row, the file name
  carries `SYNTHETIC`, every row carries `synthetic: true`, the sidecar carries the disclaimer.
  `records/findings/31-trading-swarm-harness-design.md` "Safety model" item 7; I read
  `synthetic: true` and the label in every header and sidecar. [M]
- Two run configs now exist (`market_swarm/example-run.json`, `market_swarm/example-llm-run.json`),
  so `plan`/`run` are exercisable. This contradicts `records/STATE-OF-PROJECT.md:399-401`; see the
  collision report. [M]

**A judge can check:** nothing in this beat. The datasets are git-ignored, local-validator
signatures are meaningless off this machine, and the two live-model runs left no file behind.
The one thing a reader can verify is the package's own tests once it is committed.

**The video must not say:** "validated on devnet"; that the swarm is evidence about ticket
markets, markups or demand; "the cap reduced scalping by X%"; any forecast-error number; that the
LLM agents' on-chain results are on disk; or that a `skipped` row is a refusal.

**The honest sentence, and put it on screen while any swarm number is:**

> "Generating by scripted agents against a local validator or in simulation. This is not
> evidence of real market pricing."

with the corner badge `SYNTHETIC · 4 agents · 4 rounds · local validator`, wording from
`records/findings/32-video-beats-and-storyboards.md:110-113`. [M]

---

### B6. The transfer-fee finding: what was measured, and on what

**Label: the FEATURE is BLOCKED; the MEASUREMENT is BUILT and reproducible.** The artist fee and
the flip tax do not exist anywhere in the product, and the record says the mechanism cannot
express them on this mint.

**Evidence**

- The measurement, four legs, with the RPC's own objects quoted:
  `records/findings/36-transfer-fee-on-a-one-unit-ticket.md:96-215`. At `decimals 0` and
  `amount 1`, **500 bps and 1500 bps both withhold the whole ticket** (`withheldAmount 1`,
  recipient 0). At `amount 10` and 1500 bps the fee is **2**, not `floor(1)`, because Token-2022
  ceils. [M]
- The consequence, in the finding's own words: "the fee can only be 0 or 1 base unit, never a
  fraction" (`:27`), and "a demo that turns the fee on does not quietly under-deliver a 5% cut,
  it transfers the ticket to the fee authority and gives the buyer nothing" (`:29-31`). [M]
- On a mint carrying both a fee and the hook, the hook refuses the amount at which a partial fee
  would be possible (`6008`), and `WithdrawWithheldTokensFromAccounts` succeeds without invoking
  the hook (`:222-295`). [M]
- The tool and its test exist: `tools/fee_experiment.py`, `tests/test_fee_experiment.py`. [M]
- The numbers reproduce from the current artefact: I read
  `.swarm-runs/fee-experiment/measurements.json` this pass and the four legs give withheld
  `1 / 1 / 2 / 150000000` and recipient `0 / 0 / 8 / 850000000`, exactly the finding's
  arithmetic. [M]
- Nothing ships: `records/F-decision-log.md` D15, "No fee instruction ships … recorded in every
  table as **not built, blocked**"; `ClaimRebate` (tag 7) is unimplemented and `6027`/`6028` are
  raised by nothing (`records/STATE-OF-PROJECT.md` §0A row 7). [M]
- Three surviving alternatives, none built, none recommended:
  `records/F-decision-log.md` Q5. [M]

**A judge can check:** the finding's arithmetic against Token-2022's documented ceiling division,
and, with a validator, the four legs by re-running the tool. They cannot see a fee in the
product, because there is none.

**The video must not say:** that the artist fee or the flip tax exists, is switched on, is
available, or is "coming" as if designed; that a 5% or 15% fee works; or that the fee can be
turned on later by a setting.

**The honest sentence:**

> "We tried to give the artist a cut of every resale and could not. On an indivisible ticket the
> token program rounds a fee up, so any rate at all takes the whole ticket and leaves the buyer
> with nothing. That is measured, four legs on four fresh mints, and it is why no fee ships."

---

### B7. Region caps: what is built, what is law-source only

**Label: BUILT end to end on a local validator; PARTLY BUILT as a product claim; the devnet
program does not enforce a region at all.**

**Evidence**

- The rules table: `ticketpath/data/region-caps.json`, version `2026-11-08.1`, compiled
  2026-11-08T06:05Z. I counted this pass: **82 jurisdiction codes, 84 instruments**; by
  instrument kind 21 primary legislation, 2 secondary, 1 announced policy, 60
  `none_identified`; by status **22 in force, 1 announced, 61 unknown**. [M]
- One row per instrument, not per jurisdiction, because a jurisdiction can carry an in-force
  disclosure duty and an announced price cap at once; `announced_policy` never binds. [M]
  `records/F-decision-log.md` D11, `records/STATE-OF-PROJECT.md` §G.
- The resolver is a pure function of (jurisdictions, date, table): `ticketpath/core/region_caps.py`.
  [M]
- The on-chain policy layer is a **separate crate, local only**: `programs/region_gate/`, proven
  by `tools/region_local_proof.py` at **PASS 11/11**, 11 real transactions
  (`records/findings/34-region-caps-build.md` §2, `records/STATE-OF-PROJECT.md:621`). [M]
- The devnet program is untouched by this feature and enforces no region:
  `records/STATE-OF-PROJECT.md:633-635`, "It does not claim the devnet deployment enforces a
  region". [M]
- The law source is written with per-row citation, quoted provision, dates and grade:
  `records/findings/33-a-region-cap-law.md` plus five cluster records. [M]
- **Most of the world is unverified and the table says so in the row.** 61 of 84 instrument rows
  are `unknown`. [M] And `records/STATE-OF-PROJECT.md` §G names the EU member states among the
  unresolved. [M]
- Test counts for the four Python modules, counted by me this pass with `grep -c "def test_"`:
  `tests/test_region_caps.py` 54, `tests/test_region_caps_table.py` 29,
  `tests/test_event_jurisdiction.py` 11, `tests/test_region_harness.py` 14. The record's own
  numbers disagree with each other and with these (see collisions). [M]

**A judge can check:** the law, by opening the citation in the table's own row. That is the most
independently checkable research artefact in the submission.

**The video must not say:** that the deployed program enforces a region; that the table is
complete or current; that an unknown row means resale is unrestricted there; or that the fixture
demonstrates the feature as evidence about any market.

**The honest sentence:**

> "Resale law is not one rule, so the platform resolves each event to one of three policies from
> a table built from primary sources, 84 instruments with the provision quoted. Where we could
> not read the law, the row says so and the event resolves to unresolved. The chain half of this
> is proven on a local validator; the deployed program enforces no region yet."

---

### B8. The frontend: what it shows, and that it runs on fixtures

**Label: PARTLY BUILT, and the part that is built runs on bundled fixtures, not on the backend.**

**Evidence**

- The operator's tree `../ticketing-frontend` is **fixture-only** at read time: the API base URL
  is empty in `.env.example:4`, which makes mock mode true (`lib/api.ts:44-46`), and every screen
  renders `lib/mock/*.json`. [M] as inventoried in `records/video/inputs/frontend-inventory.md`
  §0 (an input written for this same video run, reading that tree; not touched by me).
- It is **mid-rebuild and does not typecheck**: `PriceHistoryChart` takes four props and all
  three call sites pass a different set (`records/video/inputs/frontend-inventory.md` §0, §8
  item 1). 23 modified and 17 untracked paths on a single baseline commit. [M] as inventoried.
- The honesty scaffolding is **written and not mounted**: `lib/capabilities.ts`, `getHealth()` and
  the `dataSource` labels are dead code; the label that says the data is fake "exists and is
  rendered nowhere" (`records/video/inputs/frontend-inventory.md` §7 item 1). [M] as inventoried.
- The most misleading string in the app is `Enforced on-chain`, driven by a fixture boolean
  (`app/tickets/[ticketId]/page.tsx:158`, inventory §7 item 2). [M] as inventoried.
- Every fixture mint links to an explorer page that 404s, and every fixture ledger row carries a
  signature (`records/video/inputs/frontend-inventory.md` §7 item 3). [M] as inventoried.
- The earlier honesty patch was applied to a **copy**, not to the live tree, and it hardcodes
  "no program is deployed" in five places which are now false of the world:
  `records/FRONTEND-HONESTY-PATCH.md:256-276` warns that "whoever deploys the program must also
  delete the five hardcoded 'once the program is deployed; simulated in this build' clauses". [M]
- The two brand names diverge: the mounted chrome says `SEATPASS`, the repository documents say
  `Ticketpath` (`records/video/inputs/frontend-inventory.md` §7 item 10). [M]
- The frontend is **outside this repository**, so nothing about it is in the public repo a judge
  clones. [M] `records/SUBMISSION-PACK.md` §2.3, §2.5 item five.

**A judge can check:** nothing in the repository. The app is not in it, is not hosted, and is
being rebuilt.

**The video must not say:** that the app is reading our backend; that it is a live product; that
the ledger rows on it are chain records; that the mint address is real; that "Enforced on-chain"
means anything; or that the UI was built this weekend (it is the company's own frontend, which
`records/SUBMISSION-PACK.md` §2.8 requires be said out loud once).

**The honest sentence:**

> "The surrounding app is the company's own ticketing frontend, which I did not build. What I
> built is the pricing layer behind it. Every number you can see on this screen comes from a
> generated fixture, and where the app still says a rule is enforced on chain, that sentence is
> the app's, not the record's."

---

### B9. The visitor identity and the claim link (the decision the brief attributes to the board at 07:08Z)

**Label: IDEA.** Nothing is built. A recorded design and cost estimate exist, and the record says
the honest total is larger than the time left. **Note on provenance:** the board's decision text is
not in this repository and I did not read it; the only evidence for this direction inside the tree
is the finding cited below, and `records/video/COLLISIONS-AND-STATE.md:44-52` records that one of
the board's two decision entries is truncated, so no script may quote the board for it. [M]

**Evidence**

- The design and the options: `records/findings/39-visitor-identity.md`, eight candidates with
  cost, privacy and legal markers (`:67-88`). The claim link is described as "the base layer"
  both other recovery mechanisms need (`:84`), estimated **6 to 10 h** (`:75`). [M]
- The honest total: "The honest total is 14 to 24 h against about 8 h left"
  (`records/findings/39-visitor-identity.md:543`). [M]
- The recommended order, claim link then passkey then stop, is a recommendation, not a build
  (`:729`). [M]
- **Nothing implements it.** The route table has 10 routes and none of them is a claim, an
  identity, a session or a cookie: `ticketpath/server.py:117-137`. [M] I read the route table
  this pass.
- What *is* built and is often confused with it: **wallet signature verification**, real Ed25519
  over a nonce and a frozen message, with three endpoints of its own (`ticketpath/server.py:127-129`,
  `ticketpath/core/wallet_verification.py`, `ticketpath/core/ed25519.py`) and a test module,
  `tests/test_wallet_verification_flow.py` (10 test methods by grep). [M]

**A judge can check:** the verification endpoints' tests once committed; nothing about a claim
link, because there is none.

**The video must not say:** that a visitor can recover their tickets on a new device; that there
is an identity layer; or that wallet verification is the same thing as knowing who a visitor is.

**The honest sentence:**

> "Wallet signature verification is real cryptography and it runs in this build. Letting a
> visitor come back on a new device without losing their tickets is designed and costed and not
> built, so nothing on screen shows it."

---

### B10. What the repository's own reviews flag as an overclaim a video is at risk of repeating

**Label: n/a, this is a warning list.** Each row is a sentence a script is tempted to say, the
review that forbids it, and what the record says instead.

| Tempting sentence | Who forbids it | What the record says instead |
|---|---|---|
| "The gate passes, 43 attach checks green" | `records/findings/24-scoring-second-pass-review.md` §5 (last line, "The line that must not be said anywhere") | At that reading the gate exited 1 and the published attach harness was 31 passed / 1 failed. Both numbers have moved again since; quote no number you did not run. |
| "The engine's headline is the primary price it recommends" | `records/findings/10-final-review.md:38-43` (Mathematics, the narrowing) and §3 | The headline is a resale-value/cap floor presented as a primary price; the page calls it a floor and refuses an upper bound. |
| "The band brackets the value" | `records/findings/10-final-review.md` N2 | The band is never trimmed to the cap in force and can carry an upper end above the ceiling the page itself asserts. |
| "The model is validated" | `records/D-model-registry.md:35-37`, `records/DELIVERABLE.md` §20.4 item 7 | No model is validated; no accuracy, coverage or error number may appear. |
| "No program is deployed" | `records/SUBMISSION-PACK.md:272-273` (beat 5 of the shipped script) and `:416-421` (its own "obsolete" note) | False since the devnet deployment. The pack's own note says do not record that variant. |
| "The repo says nothing is on chain" | `records/SUBMISSION-PACK.md` §2.4 against §2.5 and §3 item 16 | §2.4 was left as a 12:19Z snapshot and is false of the tree; the field checklist still says paste §2.4 verbatim. |
| "The research was done before the event" | `records/SUBMISSION-PACK.md` §2.8 (provenance block) | The reading is inside the window by 39 minutes to 1 h 49 min; nothing pre-event. |
| "The frontend was built this weekend" | `records/SUBMISSION-PACK.md` §2.8 | It is the company's own frontend; one plain sentence removes the only prior-work exposure. |

---

### B11. The console as a surface (added beat)

**Label: BUILT.** Server-rendered HTML, no JavaScript, one page, every state a URL.

**Evidence**

- 10 routes, 9 of them contract endpoints (`ticketpath/server.py:117-137`); one page at `/`
  served outside the route table (`:43-46`). [M]
- Eight badge families on the page, `[FIXTURE] [EXACT] [UNVALIDATED] [REFUSED] [DECLARED] [DESIGN]
  [SIMULATED] [DEVNET]`, with the fixture strip first (`records/SUBMISSION-PACK.md:309-319`,
  `records/findings/13-submission-readiness.md` §3). [M]
- The recorded-quote rule, decided as D12 and measured again by me this pass by rendering the
  page in process: for the pinned state the page prints "The recorded recommendation is [DEVNET]
  1,380,000,000 lamports, and this page recommends the same number", then "The quote this page
  commits is the quote the file records: quote id q-18f4ec73dd8d8fd1, taken at
  2026-11-07T18:34:29.183Z", then "The file verified. The checker wrote 2026-11-08T00:50:25.281Z
  with checker devnet-publish-2026-11-07", then the two transfer legs as the file states them,
  then the 130,000,000 gap sentence quoted in B3. [M]
- The `[DEVNET]` slot is state specific: any other state renders `unverified /
  quote_hash_mismatch` with a named reason (`records/STATE-OF-PROJECT.md` §A3). [M]
- Known carried defects, not re-measured by me: no viewport meta, the price below the fold, and
  two cold-start sentences the audit called out (`records/STATE-OF-PROJECT.md` §A6 item 5). [M]
  as carried.

**A judge can check:** nothing unless the backend is runnable from the clone, and the artefact
half only if the artefact is committed.

**The video must not say:** that the page reads the chain live. The adapter opens no socket and
says so (`README.md:434-441`). Or read the `Decision mode: COUNTERFACTUAL` block aloud; the
record's own instruction is keep it in frame and do not read it
(`records/findings/13-submission-readiness.md` §12).

**The honest sentence:**

> "Every number on this page carries a tag saying what kind of number it is, and the chain block
> is the recorded artefact re-checked by its own hash, not a live read."

---

### B12. The charts and the animation (added beat)

**Label: BUILT, from a dry run.** Five SVG assets and an index page, all labelled SYNTHETIC and
DRY RUN, none of them committed.

**Evidence**

- `docs/charts/` holds `price-path-evt_capped.svg`, `price-path-evt_monitored.svg`,
  `markup-vs-time-to-event.svg`, `hops-and-holding.svg`, `ticket-hop.svg` (CSS keyframes, no
  JavaScript) and `index.html`; the tool is `tools/swarm_charts.py`, standard library only. [M]
  I listed the directory and read `docs/CHARTS.md:1-60`.
- Drawn from run `sw20261108T054830Z6297`, whose sidecar says `dry_run: true`: 51 rows in the
  capped dataset and 55 in the monitored one (`docs/CHARTS.md:45-46`; my count agrees). [M]
- Every asset carries the word SYNTHETIC, the dataset file name, the run id and the sentence
  "This picture is not evidence about any real ticket market: it is synthetic simulation output
  from scripted agents, not observed prices", in the visible text **and** in `<title>`; I
  confirmed both by grepping the SVG this pass. [M]
- A dry run is allowed and **labelled**: the asset says `DRY RUN` in the header and the footer,
  because "a simulated gateway returned what the hook would have done" (`docs/CHARTS.md:53-58`,
  and the SVG text I read). [M]
- `python3 tools/swarm_charts.py verify --out docs/charts` → PASS, 5 assets
  (`records/STATE-OF-PROJECT.md` §A4). [M] as recorded.
- **`docs/charts/` is untracked.** A judge cloning today sees no chart. [M]

**A judge can check:** the verifier once committed, which re-checks the four label facts rather
than trusting the writer (`tools/swarm_charts.py:24-34`). [M]

**The video must not say:** that a refusal in a chart is a chain event (it is a dry run, the hook
*would* have refused), or that the animated path is real pricing.

**The honest sentence:**

> "Every chart is drawn from a synthetic dataset and says so inside the file, and this one is a
> dry run: the chain was simulated, so a refusal here is what the program would have done."

---

### B13. The forecast log and the on-chain score (added beat, and the most dangerous one)

**Label: BUILT on a local validator, and it is not a scored forecast.** The mechanism exists. The
number it stores is the band's width, which is the floor any honest score could take. The model is
unfitted, so there is no forecast to score, and the record says the chain cannot verify the score
it stores anyway.

**Evidence**

- Instructions `LogForecast` (tag 5) and `ScoreForecast` (tag 6), with a band feed on tag 4:
  `records/F-decision-log.md` D14, `programs/cap_hook/src/lib.rs`, decoder in
  `ticketpath/onchain/v2.py`. [M]
- The append-only behaviour is proven by failed transactions with their own signatures and
  unchanged account bytes: a second forecast refused `6024` with the account hash identical
  before and after; a second score refused `6025`; both in
  `records/onchain-v2.local.json` (git-ignored, rewritten 2026-11-08T07:31Z by the review run).
  [M] I read this artefact this pass.
- The stored score is `interval_score_micro 200000000000000` for `realised_lamports 1000000000`
  inside `[900000000, 1100000000]`. That is exactly `(high − low) x 10^6`, i.e. the width term,
  the lowest value the program admits. [M] arithmetic on the artefact.
- The residual, in the record's words: "The score is an assertion … it does not recompute the
  penalty term" (`records/findings/37-program-v2-review-fixes.md:195-198`), and the same sentence
  is proposed for the design document at `:329-332`. [M]
- The forecast is forward-dated by 117 s, and the backdating guard is one-sided with its residual
  stated (`records/findings/37-program-v2-review-fixes.md` §2.3). [M]
- **All of it is local.** `cluster: localnet`, `localOnly: true`, program id `CTEnej2b…` which is
  not on any public cluster (`records/F-decision-log.md` D13, `:199-203` of finding 37). [M]
- The feature's own row in the record is `tested` (`records/STATE-OF-PROJECT.md` §0A row 4), and
  the live half is gated and was skipped by the documentation pass (§A4). [M]

**A judge can check:** nothing on a cluster. The artefact is git-ignored and local.

**The video must not say:** "we scored our forecast afterwards", "the model was right", or "the
forecast was logged before the outcome, so the score is honest". The first is the frame the
record calls the single most dangerous one
(`records/findings/32-video-beats-and-storyboards.md:199-201`), and the third would claim a
foresight the account cannot prove.

**The honest sentence:**

> "The chain can hold a forecast, refuse to let it be rewritten, and store a score against it.
> That mechanism runs on a local validator. The model behind it is not fitted, so there is no
> forecast worth scoring yet, and the score the program accepts is the band's own width."

---

### B14. The four refusals, which are the product (added beat)

**Label: BUILT.** This is the claim least likely to be overstated and most likely to be
memorable, and it is the one the engine review let stand.

**Evidence**

- The refusals are computed per state and printed with the missing observation named. Re-measured
  by me this pass on two events: the pinned capped state returns `not_identified`,
  `no_demand_response`, `no_fee_model`, `cap_mass_dominates`, `no_upper_bound`,
  `insufficient_events`; the uncapped state returns five of those. [M]
- The banned sentence and its replacement are written into the build spec:
  `records/BUILD-SPEC-NIGHT.md:288-296`, "The engine must stop printing the sentence 'This ticket
  has an X% chance of selling at price p.'" [M]
- The output is "a bound, not an optimum", and the reader prohibitions list nine things a reader
  must not conclude, including "Not that the engine finds the revenue-maximising primary price"
  (`records/DELIVERABLE.md` §20.4 items 1 to 9). [M]
- The dependence is measured, not stylistic: `P(sale at price p)` is not identified because no
  ask is recorded anywhere (`records/F-decision-log.md` D3, `records/DELIVERABLE.md` §20.2 item 1).
  [M]

**A judge can check:** the refusal list and its reasons on any state of the page, and the
identifiability argument in the record.

**The video must not say:** that the refusals are a limitation the team ran out of time on, or
that a model would fix them. The record's point is that a model cannot recover a column that does
not exist (`records/F-decision-log.md` D5 point 1).

**The honest sentence:**

> "The engine refuses three questions and names the missing observation for each. Nobody records
> what an unsold ticket was asking, so the chance a ticket sells at a given price cannot be
> computed from this record, and no model fixes a missing column."

---

### B15. The v2 on-chain features: floor, band feed, jurisdiction and policy (added beat)

**Label: BUILT and tested on a local validator only.** Not deployed anywhere public.

**Evidence**

- Price floor: `band_low_lamports` in `programs/cap_hook/src/state.rs`, refusals `6021`/`6022`.
  The predicate's proof is the recorded local run: `899,999,999` refused `6021`, `900,000,000`
  admitted (`records/STATE-OF-PROJECT.md` §0A row 6). [M] as recorded, not re-run by me.
- Band feed: `["band", mint]`, rewritable by design, read back on the local validator with
  `low 900000000`, `high 1100000000`, `sample_n 42` (`records/F-decision-log.md` D14). [M]
  I confirmed those fields in `records/onchain-v2.local.json`.
- Jurisdiction and policy: `[u8; 2]` ISO code with `ZZ` for unspecified, `policy 0` capped or `1`
  monitored, the program logs the code and does not interpret it
  (`records/F-decision-log.md` D16). [M]
- **No third-party consumer of the band feed exists**, so composability is unproven and `refused`
  is stored rather than enforced (`records/F-decision-log.md` D14 "Consequence";
  `records/STATE-OF-PROJECT.md` §F item 15). [M]
- v2 is a different program id on a fresh local ledger, and the devnet deployment is frozen
  evidence (`records/F-decision-log.md` D13). [M]

**A judge can check:** nothing on a cluster. They can read the code and the docs, and the
`doc_check` gate compares the docs to the source both ways (`records/F-decision-log.md` D18). [M]

**The video must not say:** that the floor, the band feed or the policy byte are on devnet, or
that anything consumes the feed.

**The honest sentence:**

> "A second version of the program adds a price floor, a public band account and a jurisdiction
> byte, and all three are exercised with real transactions on a local validator. The program on
> devnet is the earlier one and does the cap check only."

---

### B16. The wallet verification, which is the only real cryptography in the app (added beat)

**Label: BUILT.**

**Evidence**

- Ed25519 implemented in the repository: `ticketpath/core/ed25519.py`, no dependency. [M]
- A nonce challenge and a frozen message: `ticketpath/core/verification_message.py`,
  `ticketpath/core/wallet_verification.py`, three routes (`ticketpath/server.py:127-129`). [M]
- Tests: `tests/test_wallet_verification_flow.py`, 10 test methods by grep. [M]
- The frontend's verify page renders a fixture `verified: true` and does no checking
  (`records/video/inputs/frontend-inventory.md` §7 item 5), so the *app* screenshot is not this
  claim. [M]

**A judge can check:** the endpoints and the tests once committed.

**The video must not say:** that the app's "Wallet verified" is this code running. It is a
fixture.

**The honest sentence:** "Wallet verification in the backend is real Ed25519 over a nonce and a
frozen message. The screen in the app is a fixture."

---

### B17. The frozen devnet program's authentication hole (added beat, a boundary on B1 and B2)

**Label: MEASURED, and it narrows what B1 and B2 prove.**

**Evidence**

- v1's `SetPendingPrice` and `SetStatus` take no signer, so on the deployed program any keypair
  can stage a price and flip a ticket's status; an immutable deploy has no upgrade path, so the
  hole is in v1's bytes permanently (`records/findings/37-program-v2-review-fixes.md:200-210`,
  and the publishable paragraph at `:325-328`). [M]
- The reviewer's exploit was run against a copy of the previous artefact's ledger and accepted;
  the same two instructions against the patched v2 program are refused `6026` with the record
  bytes unchanged (`records/findings/37-program-v2-review-fixes.md` §1). [M]
- The consequence the record states: the devnet refusals "prove the price predicate on prices the
  deploy key chose, not that a stranger was kept from choosing them"
  (`records/findings/37-program-v2-review-fixes.md:327`). [M]

**A judge can check:** that the refusal is a real failed transaction, and, as the record states,
that the deploy is frozen (`records/STATE-OF-PROJECT.md` §A1). They cannot see the v2 fix on
devnet.

**The video must not say:** "no one can bypass the cap", "the cap binds the seller", or "the
deployed program is the reviewed one".

**The honest sentence:** "The program refuses a price over the ceiling. It does not yet police
who may stage that price; that hole is in the deployed bytes, it is closed in the version we are
testing locally, and it is written down in the repository."

---

### B18. The test suite and the documentation gate (added beat, and a trap)

**Label: BUILT, with a moving count and a red period in the last hour.** Treat the number as
unquotable unless it was run at the instant it is spoken.

**Evidence**

- The record contains four different readings of the same command for the same hour: `971` at
  07:05Z, `1007`, `1053`, and a `Ran 981 tests … FAILED (errors=10)` reading in between, because two
  sessions were editing the same tree (`records/STATE-OF-PROJECT.md:201`, `:219-226`,
  `records/findings/37-program-v2-review-fixes.md:246-260`). [M]
- The gate is real and it is a gate: `tools/doc_check.py` exits 1 on a violation and six checks
  are named (`records/F-decision-log.md` D18). [M]
- A documentation gate run went red at 07:27Z on a dangling reference and cleared at 07:30Z
  (`records/F-decision-log.md` D18, closing paragraph). [M]
- A different gate, `tools/console-check.py:111`, was pinned to a number that decays with the
  clock and failed for that reason (`records/findings/24-scoring-second-pass-review.md` §2.2).
  [M] as recorded; whether it was fixed after that reading is not settled in the files I read.

**A judge can check:** by running the command, which is exactly why no number may be spoken.

**The video must not say:** a test count, "all tests pass", or "the gate is green". If a count is
wanted, show the command's own last line on screen and say nothing about it.

**The honest sentence:** "The suite and a documentation gate run in one command, and every number
in this repository is checked against the file it came from."

---

## 3. MUST-NOT-SAY

The sentences a 2:00 video is tempted to say that the record forbids, each with the file that
forbids it. This list is the operative part of this document.

| # | Do not say | Forbidden by | Say instead |
|---|---|---|---|
| 1 | Any accuracy, coverage, error, lift, or significance number for the engine | `records/D-model-registry.md:35-37`; `RESEARCH-PROGRAM.md:937-941` (§4.6); `records/DELIVERABLE.md` §20.4 item 7 | "Nothing here is fitted, so there is no accuracy number to give." |
| 2 | "Validated on devnet" about the trading swarm | `records/findings/32-video-beats-and-storyboards.md:120`; `records/findings/31-trading-swarm-harness-design.md:258-263` | "The harness ran on a local validator. Its devnet path is written and has never been executed." |
| 3 | "The forecast was scored afterwards", or that a logged forecast was later marked right | `records/findings/32-video-beats-and-storyboards.md:199-201`; `records/findings/37-program-v2-review-fixes.md:195-198` | "The chain can hold a forecast and refuse to let it be rewritten. There is no out-of-sample score, because the model is not fitted." |
| 4 | Reading a `skipped` dataset row as a refusal | `records/findings/32-video-beats-and-storyboards.md:121` | "A skipped row is an ask no bid met. Only the refused rows are the cap." |
| 5 | "Monitored mode is where resale is legal" | `records/findings/32-video-beats-and-storyboards.md:122`; `records/F-decision-log.md` D11 (unknown jurisdictions resolve to unresolved) | "Monitored means no price limit was established from a primary source. Where we could not read the law, the event is unresolved." |
| 6 | That the cap is set per event, or per region, as settled or as built | `records/findings/32-video-beats-and-storyboards.md:242-243`; `records/F-decision-log.md` D6 (cap fixed at creation, immutable) | "The cap is one number per ticket record, fixed before the tickets exist. Whether it should be set per event or per region is undecided." |
| 7 | "The gate passes, 43 attach checks green" | `records/findings/24-scoring-second-pass-review.md` §5, final line | Nothing. Do not quote a check count you did not run. |
| 8 | "This ticket has an X% chance of selling at price P" | `records/BUILD-SPEC-NIGHT.md:293` | "The chance a ticket sells at a given price cannot be computed from this record, because nothing records the ask." |
| 9 | "Forecast", "prediction" or "expected price" as a noun for the band or the recommendation | `records/BUILD-SPEC-NIGHT.md:272` | "A recommendation and a declared band, not a forecast." |
| 10 | "The band is a 90% interval" | `records/DELIVERABLE.md` §20.6 item 2 (coverage 0.620 to 0.718 at the shipped default) | "The width is declared, not estimated, and it is not a coverage statement." |
| 11 | "The simulation validated the model" | `records/DELIVERABLE.md` §20.6 and R2-14 in `records/CORRECTIONS-APPLIED.md` | "A simulation can only test an estimator against its own assumption, and two of its three arms failed." |
| 12 | "The artist fee takes 5%", "the flip tax takes 15%", or that either exists | `records/findings/36-transfer-fee-on-a-one-unit-ticket.md:27-31`; `records/F-decision-log.md` D15 | "On an indivisible ticket a fee rounds up to the whole ticket, so no fee ships. That is measured." |
| 13 | That the deployed program enforces region caps, a price floor, a band, or a jurisdiction | `records/STATE-OF-PROJECT.md:633-635`; `records/F-decision-log.md` D13 | "The deployed program does the cap check. The floor, the feed and the policy byte are on a local validator." |
| 14 | That the legal table is complete, current, or that unknown means unregulated | `records/STATE-OF-PROJECT.md` §G, "three claims this section explicitly does not make"; 61 of 84 rows `unknown` [M] | "Where we could not read the law, the row says so and the event is unresolved." |
| 15 | "No program is deployed", or a frame whose own text says it | `records/SUBMISSION-PACK.md:272-273` and `:416-421`; `records/FRONTEND-HONESTY-PATCH.md:272-276` | "The cap-check program is deployed on devnet. The app's label saying otherwise is stale and has to be corrected before it is filmed." |
| 16 | "The frontend is reading our backend" or "this is a live product" | `records/video/inputs/frontend-inventory.md` §0 and §7 item 1 | "The app is in fixture mode. Every number on it is generated." |
| 17 | An explorer link, mint or signature from the fixture store as if it were real | `records/video/inputs/frontend-inventory.md` §7 item 3; `records/FRONTEND-HONESTY-PATCH.md` §6 | Show the devnet signature from `records/devnet-artefacts.json`, and never the app's mint link. |
| 18 | That the recommendation is the revenue-maximising primary price, or an optimum | `records/DELIVERABLE.md` §20.4 item 9; `records/F-decision-log.md` D7 | "It is a floor on value. It is not an optimum, and the cap is not the primary price." |
| 19 | That the 1.38 SOL quote is the price the cap supports | the 130,000,000 lamport gap [M]; `ticketpath/core/labels.py:337` | "The file's own face and cap put the ceiling below the number it recorded, and the console says so on the page." |
| 20 | That the swarm shows the cap reduced scalping, or any market inference | `records/findings/32-video-beats-and-storyboards.md:115-122`; `records/findings/31-trading-swarm-harness-design.md:1-12` | "Scripted agents against a local validator. Not evidence of real market pricing." |
| 21 | That anyone can verify the swarm, the charts or the on-chain v2 work today | `git status` [M]: all three are untracked or local | "Those are on this machine. The devnet transactions are the part you can look up." |
| 22 | That the UI was built this weekend | `records/SUBMISSION-PACK.md` §2.8 | "The surrounding UI is the company's own frontend. What was built is the pricing layer." |
| 23 | That the research was done before the hackathon | `records/SUBMISSION-PACK.md` §2.8 provenance block | "Reading done inside the window, cited with attribution." |
| 24 | Any reference to a machine, a process, a port or a record screen on camera | `records/SUBMISSION-PACK.md:393-412` (what must not appear on any frame); `python3 tools/public_safety.py check --tracked` reads 64 hits in 9 tracked files, all under `records/` | Keep record screens off camera. Show the console, the chart and the Explorer transaction only. |

---

## 4. VERIFIABLE-BY-A-JUDGE

Ranked by evidential strength, meaning how little trust in this repository a stranger needs.

| # | What they can check | How | Strength |
|---|---|---|---|
| 1 | The over-cap transfer was refused on devnet with `Custom: 6010` | Public RPC `getTransaction` on signature `22dqSri…e79`. Re-read by this pass: slot 519846008, blockTime 1794099023, `InstructionError [0, {Custom: 6010}]`, program log naming the price. Zero trust in the repo needed. | Strongest. A failed transaction is unforgeable and self-describing. |
| 2 | The at-cap transfer landed | Same call on `E5RCrLwW…pJf`: `err: null`, slot 519845933, log `cap admitted price=1250000000 …`. | Strongest, and it is the pair that makes 1 meaningful. |
| 3 | The program exists and is executable | `getAccountInfo 5EJ1GU3M…4eva`: `executable: true`, owner the BPF loader, 36 bytes. | Strong. Proves a program account, not what it does. |
| 4 | The mint is a hooked Token-2022 mint | `getAccountInfo 6RPS73X5…nimV` parsed: Token-2022, 0 decimals, supply 2, extensions `transferHook`, `metadataPointer`, `tokenMetadata`. | Strong for the token shape. |
| 5 | The quote was committed in a memo | `getTransaction 2Lx6cbo…ZMGCPZ`: memo program `Memo4c2p…`, `Memo (len 100)`, text `ticketpath:quote:q-18f4ec73dd8d8fd1:d90cb0…`. | Strong, and it dates the number before the sales. |
| 6 | The recorded artefact's own hash holds | `chain_client.load_artefact("records/devnet-artefacts.json")` returns `state: verified`, once the file is committed. | Strong but repo-dependent: it is the repo checking its own file. |
| 7 | The law table's rows | Each row carries a citation, a URL, a quoted provision and a retrieval date. A stranger can open the statute. | Strong for the 22 in-force rows. Useless for the 61 unknown ones, which is the point. |
| 8 | The transfer-fee ceiling | Token-2022's `calculate_fee` ceils, so one base unit at any rate above zero yields one. Reproducible with a validator and `tools/fee_experiment.py`. | Strong, mechanical, needs a validator. |
| 9 | The refusal taxonomy and the arithmetic on the console | Run the backend from the clone and read the page. The `[EXACT]` ceiling re-computes by hand. | Medium: needs the clone to run. |
| 10 | The chart verifier | `tools/swarm_charts.py verify` re-checks the four label facts. | Medium, and it only proves the label, not the data. |
| 11 | The on-chain v2 work (floor, band, forecast, score, policy) | Nothing. `records/onchain-v2.local.json` is local and git-ignored. | None. Say so. |
| 12 | The swarm datasets | Nothing. Git-ignored, local-validator signatures, synthetic by construction. | None. Say so. |
| 13 | The frontend | Nothing. Outside the repo, fixture mode, uncommitted rebuild. | None. Say so. |

**The video should lean on 1, 2, 3 and 5.** Those four are the only claims in the whole project
that a judge can confirm without trusting us, and they are the only ones worth spending seconds
on. Numbers 11 to 13 should appear only if labelled as local.

---

## 5. COLLISION REPORT

Everything below is in flux or contradictory **between files right now**. None of it is resolved
here; where two files disagree, both are named. Several of these are the sort that a script
silently inherits.

### 5.1 The tree itself

| # | Collision | Where | What the video should do |
|---|---|---|---|
| C1 | **42 modified files and 55 untracked entries** on a clean `HEAD`. Two concurrent builds hold different paths, and the board recorded the project at phase `verify` with **four criticals under repair at 07:30Z** | `git status --porcelain` [M]; `records/video/COLLISIONS-AND-STATE.md:1-31` | Treat every screen as provisional. No shot is "final" until a capture of it exists in the state the script describes. |
| C2 | **The devnet proof is not in the repository.** `records/devnet-artefacts.json` is untracked, so a clone renders the console's chain slot absent | [M] `git status`; `records/STATE-OF-PROJECT.md` §A7 | Say the transactions out loud and show signatures on screen; do not tell a judge to open the repo for them unless the file is committed first. |
| C3 | **The charts, the swarm and the state file are untracked too**, so three of the beats in this matrix are invisible to a clone | [M] `git status` | Show them on screen or drop them; do not imply the repo carries them. |
| C4 | **The test count moves inside one hour and the record keeps every reading**: `971` → `1007` → `1053` for the same command, with `FAILED (errors=10)` and a three-failure reading interleaved from two sessions editing | `records/STATE-OF-PROJECT.md:201`, `:219-226`; `records/findings/37-program-v2-review-fixes.md:246-260` [M] | Never speak a count. If one is shown, it is the command's own last line, captured at that instant. |

### 5.2 The submission pack

| # | Collision | Where | What the video should do |
|---|---|---|---|
| C5 | **§2.4 still reads "What is on-chain: Nothing."** and §3's field checklist still says "field 8 = §2.4, verbatim, set", while §2.5 and §3 item 16 were rewritten to say a program is deployed | `records/SUBMISSION-PACK.md:558-573` against `:575-592` and `:775`, with the note at `:1056-1059` admitting §2.4 is false of the tree | If the submission text is pasted from the pack, §2.4 must not be. Name it to the operator; do not fix it in a script. |
| C6 | **§1.2's script (the one to record) still contains "Nothing is deployed"** and puts `Not enforced — no program is deployed` on screen, while its own header block says the deployment landed | `records/SUBMISSION-PACK.md:266-273`, `:355-368`; the pack's own warning at `:416-421` | Do not record that beat as written. Either the deployment is the story (B2) or it is omitted; it cannot be both. |
| C7 | **The AI disclosure says no generative model is implemented**, while the swarm now has a live LLM adapter with a tested live path | `records/SUBMISSION-PACK.md:649-656` against `records/F-decision-log.md` D17 and `records/findings/35-live-llm-agents.md` | If the video mentions LLM agents at all, the disclosure text needs re-reading. Do not put LLM agents in the product's story; they are a data-generation experiment. |
| C8 | **The pack's script says 610 tests and two suites**, and both counts have moved twice since | `records/SUBMISSION-PACK.md:33-36` | Do not speak a count (C4). |

### 5.3 The decision log against the code

| # | Collision | Where | What the video should do |
|---|---|---|---|
| C9 | **D10 says `mainnet-beta` and `localnet` resolve to `MemoSq4gq…`.** The code maps `devnet` and `localnet` to `Memo4c2p…` and has no `mainnet-beta` row at all; `README.md` carries a dated correction saying so | `records/F-decision-log.md` D10 against `ticketpath/adapters/chain_client.py:75-78` and `README.md:414-424` [M] | If the memo program is named at all, name the devnet id measured from the transaction, which I re-confirmed this pass. |
| C10 | **D10 says the artefact records `memoProgram`.** It does not: the file has no such field | `records/F-decision-log.md` D10 against `records/devnet-artefacts.json` (21 keys, no `memoProgram`) [M] | Do not say the artefact records the memo program. The transaction's own account keys do. |
| C11 | **D11 says the table holds 25 jurisdiction codes and 33 instruments.** The file holds **82 codes and 84 instruments**; the state file says 82 and 84 | `records/F-decision-log.md` D11 against `ticketpath/data/region-caps.json` [M] and `records/STATE-OF-PROJECT.md:617` | Quote neither number, or quote the file's, with the version string. |
| C12 | **§0A's feature table calls feature 4 "tested"** while the live half is gated and was skipped, and finding 37 says the stored score is an assertion | `records/STATE-OF-PROJECT.md` §0A row 4 against §A4 and `records/findings/37-program-v2-review-fixes.md:195` | Say "tested in the decoder and wire half, exercised on a local validator", not "tested". |
| C13 | **`records/STATE-OF-PROJECT.md` §A9 says there is no run config in the tree, so the swarm CLI cannot be exercised.** Two configs exist now, and the charts document prints commands that use one | `records/STATE-OF-PROJECT.md:399-401` against `market_swarm/example-run.json`, `market_swarm/example-llm-run.json` [M] and `docs/CHARTS.md:60-70` | Ignore §A9's "no config" sentence. Prefer the measured dataset counts. |
| C14 | **§A9 says the LLM adapter is "deliberately switched off" and was not run against live agents.** Finding 35 records two live validator runs with real children | `records/STATE-OF-PROJECT.md:402-404` against `records/findings/35-live-llm-agents.md:88-95` | If LLM agents are mentioned at all, the state file is the stale one. |
| C15 | **The region test counts disagree three ways** in one section: `25` in the table, `101 = 54+23+10+14` in the prose, and the files now carry 54 / 29 / 11 / 14 methods | `records/STATE-OF-PROJECT.md:617-620` §G; `records/findings/34-region-caps-build.md` §1 row 8 [M] | Do not quote a test count for this feature. |

### 5.4 Artefacts that have moved under the record

| # | Collision | Where | What the video should do |
|---|---|---|---|
| C16 | **`records/onchain-v2.local.json` was rewritten at 2026-11-08T07:31Z** by the v2 review run, with `checkerVersion onchain-v2-local-2026-11-08-review2`, while D13 cites the artefact written at 06:48:48.836Z | the artefact header [M] against `records/F-decision-log.md` D13 | If a v2 number is shown, take it from the file as it stands, and say "local validator, this hour". |
| C17 | **The fee experiment's artefact has been regenerated: its mint ids differ from the ones quoted in finding 36**, though the four numbers reproduce exactly | `.swarm-runs/fee-experiment/measurements.json` [M] against `records/findings/36-transfer-fee-on-a-one-unit-ticket.md:96-215` | Quote the arithmetic, which reproduces. Do not quote the mint ids or the signatures. |
| C18 | **The two live LLM datasets were overwritten by their dry-run namesakes**, so the files that exist carry `dry_run: true` and no signatures at all | `records/findings/35-live-llm-agents.md:139-143`; confirmed by me in the sidecars [M] | Do not put an LLM dataset on screen as an on-chain run. It is a simulated chain. |
| C19 | **The frontend moved from "the copy points at our backend" to "the operator's tree is a fixture-mode rebuild that does not typecheck"**, and the earlier patch's five hardcoded "no program is deployed" clauses are now false in the other direction | `records/FRONTEND-HONESTY-PATCH.md:256-276`; `records/video/inputs/frontend-inventory.md` §0, §7, §8 [M] as inventoried | Name the surface on screen precisely. Do not call the app "our frontend" and do not show its mint or explorer links. |
| C20 | **Two product names are live**: the mounted chrome says one name, the repository documents another, and the rename decision is on the board at 07:08Z rather than in any file in this tree | `records/video/inputs/frontend-inventory.md` §7 item 10 [M]; `records/video/COLLISIONS-AND-STATE.md:58-64` | Pick one name for the video and say it in the first sentence, and have the operator confirm which. Do not show a frame carrying the other. |

### 5.5 One thing the record contradicts itself about and nobody should try to settle on camera

**The engine's headline.** `records/findings/10-final-review.md:38-43` calls the headline "a
resale-value/cap floor presented as a primary price" and marks it as labelled rather than resolved;
`records/F-decision-log.md` D7 narrows the *cap* claim and explicitly says the engine's output and
"no number moved"; `records/SUBMISSION-PACK.md:301-321` tells the video to speak the floor as
"the highest recorded price in this tier, hence a floor on value". All three can be true at once
and they read as if they disagree. **The video should say the narrow version** (a floor on value
from the record, not a target for the primary price) and should not adjudicate between the files.

---

## 6. What this pass could not verify

1. **The current test suite's state.** Not run, by instruction and because another agent holds it.
   The record contains a green reading and a red reading from the same hour (§1).
2. **The console's own byte count and the served page.** I rendered the page in process from the
   payload and read its text; I did not start a server, so no HTTP-level check was made.
3. **The frontend** was not opened, built or served by me. Every frontend claim in B8 is carried
   from `records/video/inputs/frontend-inventory.md`, which read that tree and labels its own
   inferences.
4. **The v2 local artefact's transactions.** They are local-validator signatures on a ledger that
   is no longer running, so I could not re-read any of them; I read the recorded fields only.
5. **The two live LLM runs.** Their datasets no longer exist (C18), so the token and dollar figures
   in finding 35 are quoted from that finding, not re-measured.
6. **Whether the frontend honesty patch's five hardcoded clauses have been removed in the rebuilt
   tree.** The inventory lists `lib/capabilities.ts` and a `DataSourceNote` component as written
   and unmounted, which suggests they have not been re-added as mounted text; that is an
   inference, not a measurement.
7. **Anything about mainnet.** No mainnet call was made in this pass, so no mainnet statement
   appears in this file except where the record itself marks it class D.

---

*Nothing was built, fixed, run against the suite, committed or pushed by this pass. One file was
written: this one. The four devnet reads and the one artefact verification it quotes were made
this pass and are marked [M].*

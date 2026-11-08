# STATE OF THE PROJECT — measured 2026-11-08T03:30–03:45Z

A read-only measurement of the tree, the chain and the console, written for the operator.
Nothing here is recalled; every line names the command, the endpoint or the `path:line` it
came from. Committed by this pass: **nothing.** The files this pass edited are this one,
`README.md`, `records/DELIVERABLE.md`, `records/SUBMISSION-PACK.md` and
`docs/ON-CHAIN-DESIGN.md`, each of which says in its own text what changed and when.

**[Corrected 2026-11-08T09:22Z: the sentence above, "Committed by this pass: **nothing**", was
true of the 03:30Z pass that wrote it and is false of the repository today. This file is committed
in `4c1b23b`, and `docs/charts/`, `docs/CHARTS.md`, `market_swarm/` and `records/devnet-artefacts.json`
are committed in this branch. Read it as a record of what the 03:30Z pass did, not as a claim about
the tree. `git ls-files records/STATE-OF-PROJECT.md` returns the path.]**

**This edition replaces the 2026-11-07T18:25Z edition of this file.** That edition is not in
git (this file is untracked), so nothing published is contradicted by the replacement; the table in
§0 lists what changed and why, and every claim the older edition made that this pass could not
re-measure is marked *unverified* rather than carried silently.

**[Corrected 2026-11-08T09:22Z: "this file is untracked" was true at 03:30Z and is false now.
The file is tracked as of `4c1b23b`. The reasoning it supports still holds, because the 18:25Z
edition was never committed; only the word "untracked" describes a state the repository has left.]**

**[Extended 2026-11-08T05:54Z by the feature-1 documentation pass: this file, `README.md`,
`records/F-decision-log.md`, `docs/ON-CHAIN-DESIGN.md`, `records/E-data-source-registry.md`, and an
appended correction in `records/findings/40-memo-program-id.md`. No code was touched by that
pass.]**

**The tree at this reading.** `HEAD` is `33d95b3`, on `main`, equal to `origin/main` — nothing
unpushed, nothing to push. The working tree is dirty and the dirty part is the news:
`records/devnet-artefacts.json`, `records/findings/20`, `23`–`31` and the whole `market_swarm/`
package are **untracked**, and `.gitignore`, `tests/test_devnet_publish.py`,
`tools/devnet_publish.py` and `tools/check_frontend_attach.py` are modified
(`git status --porcelain`). The devnet proof is real on the chain and is **not in the
repository yet**. That gap is the first thing to fix, and it is one commit of explicit paths.

**[Corrected 2026-11-08T09:22Z: that paragraph describes the tree at 03:30Z and is now the
opposite of it. `HEAD` is `948b5d5` on `release/prep`, the working tree is clean, and everything
it calls untracked is committed in this branch: `records/devnet-artefacts.json`, findings `20` and
`23`-`31`, `market_swarm/`, `docs/charts/` and `docs/CHARTS.md`. Measured: `git status --porcelain`
prints nothing, `git ls-files market_swarm | wc -l` is 35, `git ls-files docs/charts | wc -l` is 6.
The gap it calls "the first thing to fix" is fixed. A reader arriving after the merge should
take the paragraph as the 03:30Z record and this note as the state.]**

**Extended 2026-11-08T08:20Z, after the 05:54Z edition above.** This is the documentation pass for the
ten-feature build, and it is the first edition of this file written after all ten features landed. It
**replaces the ten-feature table in §0A** with the measured statuses and the test file behind each,
rewrites §A1's program and console rows, adds the re-measured §A3 behaviour and §A4 counts, closes
§A6's first defect, and extends §F with the five things this pass could not verify. The 03:45Z
measurements it does not re-run are carried with their dates and marked as carried. Files this pass
edited: this one, `README.md`, `records/F-decision-log.md`, `docs/ON-CHAIN-DESIGN.md`,
`records/C-variable-registry.md`, `records/D-model-registry.md`, `records/E-data-source-registry.md`,
with appended corrections in `records/A-research-ledger.md`, `records/CONTRACT-MAP.md` and
`records/CONTRACT-CONFORMANCE.md`. No code, test or tool was touched. No commit, no push.

**Extended 2026-11-08T09:22Z, the release-record correction pass.** This pass answers an independent
review of `release/prep` and edits documents only. It corrects the chart-verifier quotation in
feature 3 (§0A) and in §A4, which named an output and an exit code the shipped tool cannot produce;
re-measures every count in §A4 and in §0's findings row; records that the public-safety gate is
clean on the tracked tree since `aea1cbe`; says that the local-validator artefact behind features 6
and 8 stays local; and marks the time-stamped sentences at the top of this file that the branch's
own commits made false. Files this pass edited: this one, `AGENTS.md`, `docs/PUBLIC-SAFETY.md`,
`records/SUBMISSION-PACK.md`, `records/FINAL-PROOF.md`, `records/video/inputs/build-state-matrix.md`.
No code, test or tool was touched. No commit, no push. The commands and outputs behind every new
number are in `tmp/release-prep/fix-record.md`, which is git-ignored.

---

# 0. What changed since the 18:25Z edition

| # | Then (18:25Z) | Now (03:30Z) | Evidence |
|---|---|---|---|
| 1 | no program, no mint, no signature anywhere | **a program is deployed on devnet**, a hooked Token-2022 mint exists, a quote memo and a two-leg transfer pair landed, and the over-cap leg is a *failed transaction with its own signature* | `records/devnet-artefacts.json`; independently re-read from the cluster in this pass, §A2 |
| 2 | `[DEVNET]` slot always empty | the slot renders **verified** for exactly one state, and `unverified / quote_hash_mismatch` for every other | §A3 |
| 3 | test suite 546 tests | **610** in `tests/` (36 modules) plus **274** in `market_swarm/tests/` | §A4 |
| 4 | 29 findings tracked, 30 on disk | **32 tracked, 42 on disk**; numbers 20 and 23–31 are untracked | `git ls-files records/findings \| wc -l` |
| 5 | no Solana toolchain on this machine | toolchain **installed and working** in a login shell: Agave 4.3.2, `spl-token` 5.6.1, `cargo-build-sbf` 4.4.0, rustc 1.99.1. It is still absent from a non-login `PATH`, which is why the older reading said "no toolchain" | §A1 |
| 6 | publish script had one shot per run, and a died run minted a second mint | **resume file plus transport retries**: a rerun reuses the mint, the memo and any landed transfer, and it will not resend until the blockhash is provably dead | `records/findings/28`; 56 tests in `tests/test_devnet_publish.py` |
| 7 | a trading-swarm harness was an idea | `market_swarm/` exists: **11 modules, 9,228 lines with its tests, 274 tests green in 1.03 s**, every dataset labelled synthetic, and the LLM policy adapter switched off | §A9 |
| 8 | the memo program id was one constant for every cluster, and it was mainnet's | **a per-cluster table**, devnet's id measured from the proven transaction, an unknown cluster refused, the publish path asserting the landed id, and `memoProgram` recorded in the artefact | `records/findings/40`; §A4 |
| 9 | the ten-feature build was in progress: one feature measured, nine unmeasured | **eight shipped and tested, two blocked by a measured mechanism fact**; the suite green at 07:05Z (971 tests) and again at 07:31Z (1053 tests, `OK`), having been red at 07:22Z under another agent's in-flight code edit; `doc-check` green at 07:24Z, red at 07:27Z only on a code-owned file's dangling reference, and green again at 07:30Z | §0A, §A4, §A6 defect 1, §F items 13 to 20 |

**What the older edition said that is still true** and is repeated below rather than dropped:
the fixture's contents and its determinism, the engine's arithmetic and its refusals, the
public-safety gate failing on the published tree, the console's mobile and above-the-fold
defects, and the absence of a hosted demo.

**[Corrected 2026-11-08T09:22Z: the fourth item in that list is no longer true. The public-safety
gate is clean on the tracked tree, measured `python3 tools/public_safety.py check --tracked` →
`public_safety: clean, tracked tree, 285 file(s)`, exit 0. Commit `aea1cbe` ("Redact the machine
handles from the published proof files") is what changed it. The other four items in the list stand.]**

**Corrected 2026-11-08T08:25Z: four counts in the table above moved, and three of them are mine to
re-measure.** Measured on this tree at 08:13Z: (a) row 3, the suite is **1076** in `tests/` and
**436** in `market_swarm/tests/`, not 610 and 274; (b) row 4, findings are **32 tracked and 52 on
disk**, with **20** untracked, not 42 on disk and 10; (c) row 7, `market_swarm/` is **twelve Python
files (eleven modules and the package `__init__.py`), fifteen test modules, 15,037 lines with its
tests, and 436 tests green in 1.9 s**, not 11 modules, 7 test modules, 9,228 lines and 274 tests;
(d) row 9 is this pass's own row and is current. The untracked findings include the evidence for eight
of the ten features: `33-a-region-cap-law.md` and `33-b-region-cap-law-sources/`,
`34-region-caps-build.md`, `35-live-llm-agents.md`, `36-transfer-fee-on-a-one-unit-ticket.md`,
`37-program-v2-review-fixes.md`, `38-region-caps-local-validator.md`, `39-visitor-identity.md`,
`40-memo-program-id.md` and `41-deepseek-live-adapter.md`.

**Corrected 2026-11-08T09:22Z, at `HEAD 948b5d5`: the 08:25Z counts above moved again, and rows 3,
4 and 7 of the table are stale for a second time.** Every number below is this pass's own reading
at 09:20-09:22Z on a clean tree, quoted with the command that produced it:

| Row | 08:25Z said | Measured at `948b5d5` 09:22Z | Command |
|---|---|---|---|
| 3, `tests/` | 1076 | **1079 tests** (`Ran 1079 tests in 30.321s`, `OK (skipped=26)`) | `python3 -m unittest discover -s tests` |
| 3, `market_swarm/tests/` | 436 | **489 tests** (`Ran 489 tests in 1.990s`, `OK (skipped=2)`) | `python3 -m unittest discover -s market_swarm/tests` |
| 4, findings tracked | 32 | **57** | `git ls-files records/findings \| wc -l` |
| 4, findings on disk | 52 | **57**, with **0** untracked | `find records/findings -name '*.md' \| wc -l`; `git ls-files -o --exclude-standard records/findings \| wc -l` |
| 7, Python files in `market_swarm/` | twelve | **thirteen** | `ls market_swarm/*.py \| wc -l` |
| 7, test modules in `market_swarm/tests/` | fifteen | **sixteen** | `ls market_swarm/tests/test_*.py \| wc -l` |
| 7, lines with its tests | 15,037 | **16,425** | `find market_swarm -name '*.py' \| xargs wc -l` |
| 7, tests green | 436 | **489**, `OK (skipped=2)` | `python3 -m unittest discover -s market_swarm/tests` |

**Why the 08:25Z pair was never true of the commit that carried it, and this pair is.**
`git diff --name-only 4c1b23b..HEAD -- tests market_swarm/tests` prints nothing, so the test tree
committed in `4c1b23b` is the tree measured here; the 1076/436 reading was taken on a working tree
that was never committed, which is the one thing this file exists not to do. `tests/test_event_jurisdiction.py`
has had 12 test methods since `0266570`, two commits before the records commit. The 57/57 findings
count is the first reading in this file where tracked and on disk agree, because every finding is
committed in this branch. §A4 carries the same numbers with the same commands.

**Final reading at the release head, 2026-11-08T09:48Z.** The two commits after `948b5d5` add tests
(`tests/test_doc_check.py`, `tests/test_region_caps.py`, `tests/test_onchain_v2.py`,
`tests/test_swarm_charts.py`), so the count moved once more and the pair above is short of it.
Measured on the committed tree: `Ran 1092 tests` / `OK (skipped=26)` for `tests/`, `Ran 489 tests` /
`OK (skipped=2)` for `market_swarm/tests/`, `doc_check: clean, 7 check(s)` with 24 allowed absences,
and `tp.py gate --quick` reporting `tests=1092 OK - doc-check=0 violation(s)`. Every earlier reading in
this file stays where it is, tagged with the tree it was taken on.

**Read again at 2026-11-08T11:27-11:30Z, after the release merge: `Ran 1251 tests` (`OK
(skipped=27)`) in `tests/` and `Ran 771 tests` (`OK (skipped=2)`) in `market_swarm/tests/`, with
`doc_check` clean and `public_safety: clean, tracked tree, 367 file(s)`. §A4 carries that table with
the command behind every number. The 1092/489 pair above was a reading of `dd42348` and is not
superseded by assertion: it is superseded by measurement, at the later instant, on a tree the merge
and three parallel agents had moved.**

**Extended 2026-11-08T05:54Z, after the 03:45Z edition above.** This edition adds the ten-feature
status table (below), corrects §A4 with the test counts measured in this edit, and adds the three
memo-program rows to §F. It does not re-run the 03:45Z measurements and carries them unchanged.

---

# 0A. THE TEN-FEATURE BUILD — per-feature status (2026-11-08)

The closed status set is `built` / `tested` / `unverified` / `not built`. Nothing here is a
prediction. A `built` row names the code path, a `tested` row names the test file and the measured
count, an `unverified` row says what would verify it, and `not built` means no code that
implements the feature is claimed in this pass.

| # | Feature | Status | Code path | Test file / note |
|---|---|---|---|---|
| 1 | Memo program id, per cluster | **tested** | `ticketpath/adapters/chain_client.py` (`MEMO_PROGRAMS`, `MEMO_PROGRAM_DEVNET`, `MEMO_PROGRAM_CLI`, `memo_program_id`, `quote_commit`); `ticketpath/orchestrator.py` (`_memo_program_or_none`); `tools/devnet_publish.py` (`assert_memo_program`) | `tests/test_onchain_sim.py` (24 tests, `OK`) and `tests/test_devnet_publish.py` (81 tests, `OK`), both run by this pass. `mainnet-beta` and `testnet` are absent from the table and refused; devnet and localnet both resolve to `Memo4c2p…` |
| 2 | Console renders the real devnet artefact as recorded | **tested** | `ticketpath/orchestrator.py` (`_chain_payload`, `recorded`, `matchesCurrentQuote`); `ticketpath/console/page.py` (`chain_slot`, `_recorded_quote`, `_match_sentence`); `ticketpath/adapters/rpc_adapter.py` (`program_status.recorded`) | `tests/test_console_recorded_artefact.py` (20 tests, `OK`). Measured through `tools/guidance.py`: pinned state → `verified True`; any other instant → `verified False`, with both quote ids and both instants named on the page and the two recommendations printed only where they differ (re-measured 2026-11-08T07:45Z) |
| 3 | Chart and animation assets from `market_swarm` data, every asset labelled SYNTHETIC | **tested** | `tools/swarm_charts.py`; `docs/charts/` (five SVGs and an index); `docs/CHARTS.md` | `tests/test_swarm_charts.py` (41 tests, `OK`), which is what the status rests on. `python3 tools/swarm_charts.py verify --out docs/charts` prints `PASS LABELS ONLY`, `series rebuilt from the dataset on 0 of 5 asset(s)`, and `note: exit 3, labels and internal consistency only; nothing about the data was checked`, and exits **3**. The label and the internal consistency are verified; the data series are not, because `.swarm-runs/` is not in the repository and `docs/CHARTS.md:48` says the datasets are not in it. Re-measured 2026-11-08T09:22Z |
| 4 | Forecast log on chain plus off-chain scoring | **tested** | `programs/cap_hook/src/lib.rs` (tags 5 and 6), `ticketpath/onchain/v2.py`, `ticketpath/core/forecast_score.py` | `tests/test_forecast_score.py` (18 tests) and `tests/test_onchain_v2.py` (45 tests), both `OK`. The live local-validator half is `tests/test_onchain_v2_live.py`, 26 tests, **skipped** by the documentation pass (the gate is `TP_ONCHAIN_V2_LIVE=1` and the run rewrites the run's artefact). The rebuilt artefact (111,504 bytes, sha256 `de89af3c…`) carries proofs `a` to `g` and thirteen tag 4..6 proofs, and proof `g` is the two non-authority refusals `6026` |
| 5 | Artist fee via `TransferFeeConfig` | **built** | `market_swarm/artist_fee.py` (the seller-paid lamport leg: the assessment, the instruction and the order it sits in); `market_swarm/config.py`, `market_swarm/gateway.py`, `market_swarm/runner.py` and `market_swarm/ledger.py` (the per-event option, the leg in the sale transaction and the row's columns); `tools/artist_fee_proof.py` | **Built as a seller-paid lamport leg; the token-fee form is dead.** `records/findings/42-artist-fee-at-checkout.md` is the measurement, PASS 9/9 on a throw-away local validator, and `tools/artist_fee_proof.py` is the tool. The ceiling that killed the token-fee form is unchanged: at `decimals 0`, `amount 1`, any rate from 1 to 9999 bps withholds the whole ticket, `records/findings/36-transfer-fee-on-a-one-unit-ticket.md`. Off unless an event turns it on, the chain does not enforce it, and no live harness run can charge it (§0A feature 7 states the same limit for both legs) |
| 6 | Price floor | **tested** | `programs/cap_hook/src/state.rs` (`band_low_lamports`), `programs/cap_hook/src/lib.rs` (`6021`, `6022`), `ticketpath/onchain/v2.py` | `tests/test_onchain_v2.py` (45 tests, `OK`) for the field and the wire format. The predicate's proof is the local-validator run recorded at `records/onchain-v2.local.json`: `899,999,999` refused `6021`, `900,000,000` admitted. Not re-run by this pass. **That artefact is git-ignored (`.gitignore:65`, 32,679 bytes on disk here) and stays local: it is not in the repository and a reader will not find it** |
| 7 | Flip tax | **tested** | `market_swarm/flip_tax.py` (the schedule, the assessment, the 70-byte record decoder, the leg and the instruction order); `market_swarm/config.py`, `market_swarm/gateway.py`, `market_swarm/runner.py`, `market_swarm/ledger.py` and `market_swarm/datasets.py` (the per-event option, the leg in the sale transaction, the row's three columns and the dataset check); `programs/cap_hook/src/lib.rs` step 7, which writes `held_since_unix`, is the input this build reads | Off chain: `market_swarm/tests/test_flip_tax.py`, `market_swarm/tests/test_flip_tax_mutation.py` and `market_swarm/tests/test_flip_tax_wiring.py`. On chain: `tools/flip_tax_proof.py`, with `tests/test_flip_tax_proof.py` for the tool itself and the run quoted in `records/findings/43-flip-tax-at-checkout.md`. **The charging half only:** the tax is a seller-paid lamport leg in the sale transaction, 15% under an hour falling to 0 at 30 days by default and off unless an event turns it on, and the chain does not enforce it (a sale can move the ticket and pay nothing). **The pool half is not built**: the money goes to the artist wallet, a refund-to-holders pool is documented as a future option in `docs/ON-CHAIN-DESIGN.md` §16.6, `ClaimRebate` (tag 7) is absent from `lib.rs`, `6027` and `6028` are raised by nothing, and `state.rs`'s `HOLD_FULL_SECONDS = 60` is that unbuilt curve's demo number, not this schedule. **No live harness run can charge it either:** `market_swarm/gateway.py:45-56` states that `start()` refuses `program=v2`, and that the fee and tax paths build v2 instruction shapes on a v1 run too, because the record those paths write is the one that carries the hold clock and the v2 authority, so a fee or tax event is a v2-record event whatever `program` says and cannot complete a live run under either program. The legs are measured by `tools/flip_tax_proof.py` and `tools/artist_fee_proof.py` on a throw-away local validator, not by a harness run. **[Corrected 2026-11-08T12:00Z: this cell described the charging half and not the limit on driving it. The build and the measurement are unchanged, and `market_swarm/CONTRACT.md:52-71` already carried the limit.]** |
| 8 | Public price feed | **tested** | `programs/cap_hook/src/lib.rs` (tag 4), `programs/cap_hook/src/state.rs` (`band_seeds`), `ticketpath/onchain/v2.py` | `tests/test_onchain_v2.py` (45 tests, `OK`). The account was published and read back on the local validator (`low 900000000`, `high 1100000000`, `sample_n 42`); **no third-party consumer**, so composability is unproven. The run is the same local-only one behind feature 6: the artefact `records/onchain-v2.local.json` is git-ignored and stays local, so the numbers are the record and the artefact is not |
| 9 | Live deepseek agent adapter, tiny budgets | **tested** | `market_swarm/forge_policy.py`, `market_swarm/budget.py`; opt-in on `MARKET_SWARM_LIVE_LLM=1` | `market_swarm/tests/test_feature9_fixes.py` and `test_forge_policy.py` (89 tests, `OK`); the whole package is 489 tests, `OK (skipped=2)` (re-measured 2026-11-08T09:22Z, was 436). The documentation gate's feature check reads both test roots as of 2026-11-08, so this row is `tested` on the suite that exercises it |
| 10 | Per-event jurisdiction field | **tested** | `programs/cap_hook/src/state.rs` (`jurisdiction`, `policy`), `programs/cap_hook/src/lib.rs` (log line, the `policy == 1` skip), `ticketpath/onchain/v2.py` | `tests/test_onchain_v2.py` (45 tests, `OK`). The local run initialised `jurisdiction ZZ`, admitted a transfer with `jurisdiction=ZZ` in the log and refused `policy 2` with `6023`. The wire carries neither field. **This program records the code and does not interpret it**; the jurisdiction-to-policy table is a separate piece of work in this same tree by another session (D11 there, `ticketpath/core/region_caps.py`), the two must be reconciled by the operator, and any such reconciliation is nation-level only because the record is two bytes while 72 of the table's 82 codes are subdivisions (§A6 item 7) |
| 11 | v2 publish to devnet under a new program id, with a resume file and fault injection | **tested** | `tools/publish_v2_devnet.py` (subclasses `LocalProof` from `tools/publish_v2.py`, overrides eleven lifecycle methods and wraps the twenty proofs without re-implementing an assertion); `records/onchain-v2-devnet.json` is the devnet record | `tests/test_publish_v2_devnet.py` (35 tests, `OK (skipped=1)`, the skip being the local-validator rehearsal behind `TP_V2_DEVNET_REHEARSAL=1`). The rehearsal itself passed 64 assertions including three crash-and-resume scenarios, and the devnet run it then made recorded 35 transaction rows and observed all eleven required refusals. Not reviewed by the operator, and not re-run since the last edit to the tool |

**Corrected 2026-11-08T08:20Z.** The table above replaces the 05:54Z edition, which read "one
measured row, nine unmeasured" and marked features 2 to 10 `not built`. That was true when it was
written and is false now: eight of the ten have code and a passing test file named here, and the two
that do not are **blocked by a measured mechanism fact**, not unfinished. The older sentence is kept
below rather than deleted, and this note is what a reader should believe.

One measured row, nine unmeasured. The build order this table follows is a local working note, not
a record, and nothing here is copied from it.

**Corrected 2026-11-08T09:22Z, on the release-record correction pass.** Two substantive changes to
the table above, and both are corrections of a claim rather than of a number:

1. **Feature 3 quoted a verification the shipped tool cannot produce.** The row read
   `python3 tools/swarm_charts.py verify --out docs/charts` → `PASS`, 5 assets, series rebuilt and
   matched, exit 0. The tool prints `PASS LABELS ONLY`, reports `series rebuilt from the dataset on
   0 of 5 asset(s)` and `note: exit 3, labels and internal consistency only; nothing about the data
   was checked`, and exits **3**. `tools/swarm_charts.py` sets `status = "PASS" if all_rebuilt else
   "PASS LABELS ONLY"` and returns 3 otherwise, and its own docstring says it prints exactly that
   when the datasets are absent. They are absent: `.swarm-runs/` is not in the repository and
   `docs/CHARTS.md:48` says the datasets are not in it. The status stays `tested` on
   `tests/test_swarm_charts.py` (41 tests, `OK`, measured on a clean tree at `948b5d5`; a parallel
   pass has since made it 44 in the uncommitted working tree), which is what justifies it; what that
   verifies is the label and the internal consistency, not the data series.
2. **Features 6 and 8 rest on an artefact that stays local.** `records/onchain-v2.local.json` is
   git-ignored at `.gitignore:65` and is not in the repository. The numbers in both rows are the
   record of that run and are kept; the rows now say the artefact is local, so a reader is not sent
   looking for a file that does not ship.

This note is what a reader should believe about feature 3 where it disagrees with the row's older
text, which is kept above so the false claim is visible rather than erased.

**Corrected 2026-11-08T12:00Z: feature 5's row read `not built` and the correction is a status word,
not a claim.** The row as it stood was:

> `| 5 | Artist fee via TransferFeeConfig | **not built** | none | **Blocked** by the measured
> Token-2022 ceiling: at decimals 0, amount 1, any rate from 1 to 9999 bps withholds the whole ticket.
> records/findings/36-transfer-fee-on-a-one-unit-ticket.md |`

That wording described the token-fee mechanism and was true of it. It was false of the tree: the
artist fee ships as a seller-paid lamport leg, `market_swarm/artist_fee.py` and
`tools/artist_fee_proof.py` are its code and its proof, and `records/findings/42-artist-fee-at-checkout.md`
measures it at PASS 9/9. The row now says `built` and names those files; the ceiling in finding 36 is
still the reason the token-fee form is not the one that shipped, and the row keeps it. This is the
item `README.md` §"The ten features" was already describing in its heading, and the two now agree:
rows 1, 2, 3, 4, 6, 8, 9 and 10 are the eight that are neither of the lamport pair and all eight read
`tested`, which is the heading's "eight tested"; rows 5 and 7 are the pair built on the lamport route.
Row 5's status cell reads `built` and row 7's still reads `tested`, so the heading's "two built on the
lamport route" is a statement about where both are built and not about either row's status word, and
this note does not move row 7.

---

# A. TECHNICAL

## A1. Architecture — what is there, and what state each piece is in

| Piece | State | Evidence |
|---|---|---|
| HTTP server, stdlib only | **WORKS** | started by this pass on a scratch loopback port, `GET /health` → 200, `contract.routesImplemented: 10`, `endpointsImplemented: 9` |
| Route table | **WORKS** | 10 routes, 9 of them contract endpoints; `/health` was read live in this pass |
| Ledger adapter | **WORKS** | `ticketpath/adapters/ledger_adapter.py` — the only path to data; refuses a store that does not declare `meta.synthetic: true` |
| Store (fixture) | **WORKS, synthetic only** | `build_fixture_store.py --check` in this pass → `fixtures/synthetic_store.json matches a fresh build exactly`, and the loader accepts it |
| Core (pure functions) | **WORKS** | unchanged since `375126f` (17:25Z): no clock except an injected `now()`, no network |
| RPC adapter | **ABSENT BY DESIGN, AND NOW A NUANCE** | `ticketpath/adapters/rpc_adapter.py`: `programDeployed: False` is returned *because this adapter never asks the cluster*, not because nothing is deployed. Read live in this pass: `/health` → `programDeployed: false`, `programId: null`, `rpcEnabled: false`, `reason: rpc_disabled`. **That field is a statement about the adapter, not about the world.** Since feature 2 it also returns `askedCluster: false` and a `recorded` block naming the artefact's program id, mint, cluster, source and checkedAt, so a reader can tell a configured id from a read one |
| Chain client (quote commitment) | **WORKS, read-only** | `chain_client.load_artefact` recomputes the quote hash from the fields the page is displaying; run in this pass against the real file → `state: verified` |
| Solana program | **TWO VERSIONS DEPLOYED ON DEVNET, UNDER DIFFERENT PROGRAM IDS** | `programs/cap_hook/`, native Rust with no Anchor, four source files (`lib.rs`, `state.rs`, `error.rs`, `tests.rs`). **v1** is on devnet at `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, executable, owner `BPFLoaderUpgradeab1e…`, 36 bytes of account data, and is frozen: no upgrade, no re-sign, no edit, and its program data is still the 85,784-byte v1 build last deployed in slot 519806063. **v2** is deployed on devnet under a program id of its own, `Bebo55oe…` (read it in full in `records/onchain-v2-devnet.json`; a second, local-validator id `CTEnej2b…` is in `records/F-decision-log.md` D13 and `docs/ON-CHAIN-DESIGN.md` §0), and adds the floor, jurisdiction, policy, the hold clock, the band, the forecast and the score. The devnet deploy is `tools/publish_v2_devnet.py`, which imports `tools/publish_v2.py` and overrides only its validator lifecycle; it recorded 35 transaction rows (34 distinct) and observed 14 refusals across both phases, and its record is `records/onchain-v2-devnet.json`. `docs/ON-CHAIN-DESIGN.md` §0 is the instruction, error and seed table and `tools/doc_check.py` compares it with the source both ways. What v1 does **not** do is listed in `programs/cap_hook/README.md`: no hop record, no destination check, no verified-wallet gate, no escrow, no nullifier |
| Devnet mint | **EXISTS** | `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`, owner `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` (Token-2022), 0 decimals, supply 2, extensions `transferHook`, `metadataPointer`, `tokenMetadata` |
| On-chain state machine | **DESIGN-ONLY + SIMULATED** | `ticketpath/onchain/sim.py`, Python mirror, same error codes; console renders 5 arms under `[SIMULATED]` |
| Solana toolchain | **INSTALLED, NOT ON A NON-LOGIN PATH** | `bash -lc 'which solana spl-token cargo-build-sbf rustc cargo'` → all five resolve; versions in §0 row 5. In a plain non-login shell `which solana` still returns nothing |
| API layer | **WORKS** | one module per contract area; `tests/test_contract_conformance.py` addresses every route over a socket |
| Console | **WORKS** | one server-rendered page at `/`, no JavaScript, every state a URL. **The `[DEVNET]` slot now renders the recorded artefact as recorded** (§A3): the file's own instant, slot, block time, signature, mint, program, memo program, both transfer legs and the refusal's `6010`, plus a separate sentence saying whether the page's number is the chain's. The `Verified at None` defect is closed (§A6 defect 1). Page byte count not re-measured this pass |
| CLI (`tools/tp.py`) | **WORKS** | 8 verbs, exit codes 0/1/2/3 **[corrected 2026-11-08T12:00Z: 10 verbs, `timeout 60 python3 tools/tp.py --help` → `health events event tickets history price page sweep gate doc-check`, and the exit codes are unchanged. `docs/CLI.md:19-30` already tabulated all ten]** |
| Publish script | **WORKS, AND RESUMABLE** | `tools/devnet_publish.py`: nine steps, each reads the cluster before it writes; transport retries 4× with 0.5/1/2 s backoff; resume file `records/devnet-progress.json` (git-ignored, 0600); `--inject` faults armed only by an explicit flag; `--local` runs a validator it kills on every exit path |
| `market_swarm/` | **IN PROGRESS, SEPARATE PACKAGE** | 11 modules + 7 test modules, standard library only, imports nothing from `ticketpath/` and is imported by nothing in it. 274 tests green. No run config file in the tree, so `python3 -m market_swarm plan --config <path>` is the only entry point and there is nothing to point it at yet (§A9) |
| Public-safety check | **WORKS AS A TOOL, AND CLEAN ON THE TRACKED TREE SINCE `aea1cbe`** (`64 hits in 9 tracked files` was the reading on 2026-11-08T03:30Z; see the correction below the table) | `python3 tools/public_safety.py check --tracked` re-measured 2026-11-08T09:22Z → `public_safety: clean, tracked tree, 285 file(s)`, exit 0. Detail in §A6 |
| Frontend (`frontend/`) | **IN THE TREE AND COMMITTED, AT `009f103`; ITS OWN CHECKS RE-RUN FROM THE NEW PATH** | the SeatPass app, 82 files and 1,097,690 bytes **[corrected 2026-11-08T11:41Z: the cell read STAGED, NOT COMMITTED and 81 files / 1,097,001 bytes, which was the index before the commit and before `frontend/.env.example`; see §A10]** (1,093,317 as copied). Listed from `git ls-files` in its own checkout. From the new path, in a throwaway copy under the system temp dir with `node_modules` symlinked: `npm run typecheck` exit 0, `npm run lint` exit 0, `npm test` → `tests 15, pass 15, fail 0`, `bash tools/greps.sh` → `8.5 GREPS: ALL ZERO`, `node tools/contrast.mjs` → `28 pairs, 0 below 4.5:1`. `npm run build` was not run and `frontend/tools/verify-landing.cjs` was not re-run. Detail in §A10, provenance and the operator's statement in `records/F-decision-log.md` D19 |
| Frontend attach | **PARTIAL** | 43 checks against a copy, last green at 18:40Z; **not re-run in this pass** — `tools/check_frontend_attach.py` needs a backend on the documented port and none was running (*unverified this pass*) |

**Corrected 2026-11-08T08:25Z: the `market_swarm/` row in the table above is stale in four
places.** Measured at 08:07Z: twelve Python files (eleven modules and the package `__init__.py`),
**fifteen** test modules, **436** tests (`Ran 436 tests in 1.947s`, `OK (skipped=2)`), and **15,037**
lines with its tests, not 11 modules, 7 test modules, 274 tests and 9,228 lines. There **is** a run
config in the tree: `market_swarm/example-run.json`, which `tools/region_harness.py` accepts (both
of its events resolve with `no_jurisdiction_declared`) and which `docs/CHARTS.md` names as the input
for the committed assets. The row's status, "in progress", is also out of date in one respect: the
package's own suite is green and the live LLM path is opt-in, but a live validator run of the whole
harness is still not in the record.

**Corrected 2026-11-08T09:22Z, at `HEAD 948b5d5`, on the release-record correction pass. Two rows
above are stale, and one of them was stale in the other direction.**

1. **The public-safety row.** It read **WORKS AS A TOOL, STILL FAILING AS A GATE**, with
   `64 hits in 9 tracked files`, carried forward from 03:30Z. That is no longer true of the tree:
   `python3 tools/public_safety.py check --tracked` → `public_safety: clean, tracked tree, 285 file(s)`,
   exit 0. Commit `aea1cbe` ("Redact the machine handles from the published proof files",
   2026-11-08T09:03Z) is what changed it: it redacted the eight records that carried the hits and
   left `.public-denylist` unchanged, so no exception was bought to make the number go away. The
   64-in-9 reading is kept here because a reader comparing this file to an older one needs to know
   which commit made the difference. The row's status is now the measured one.
2. **The `market_swarm/` row's counts.** The 08:25Z correction above put it at twelve Python files,
   fifteen test modules, 436 tests and 15,037 lines. Measured at 09:22Z: **thirteen** (`ls
   market_swarm/*.py | wc -l`), **sixteen** (`ls market_swarm/tests/test_*.py | wc -l`), **489 tests**
   (`Ran 489 tests in 1.990s`, `OK (skipped=2)`) and **16,425 lines** (`find market_swarm -name
   '*.py' | xargs wc -l`). The row's own text still says "11 modules + 7 test modules ... 274 tests",
   which was the 03:45Z reading; the 08:25Z note and this one are what to believe.

## A2. Devnet, re-read from the cluster by this pass

Every row below was fetched by this pass from `https://api.devnet.solana.com` over plain HTTPS
`curl`, not read from a file. Public identifiers only; no key, no path, no balance of anybody's
account beyond the program account's own rent.

| What | Method | Result |
|---|---|---|
| the program exists and is executable | `getAccountInfo 5EJ1GU3M…4eva` | `executable: true`, owner `BPFLoaderUpgradeab1e11111111111111111111111`, `space: 36` |
| the mint exists and is hooked | `getAccountInfo 6RPS73X5…nimV` (`jsonParsed`) | Token-2022, `decimals 0`, `supply 2`, extensions `transferHook`, `metadataPointer`, `tokenMetadata` |
| the at-cap transfer landed | `getTransaction E5RCrLwW…pJf` | `err: null`, slot 519845933, blockTime 1794099006, log: `ticketpath: cap admitted price=1250000000 face=1000000000 cap_bps=2500` |
| the over-cap transfer was refused | `getTransaction 22dqSri…e79` | `err: {InstructionError: [0, {Custom: 6010}]}`, slot 519846008, blockTime 1794099023, log: `ticketpath: cap exceeded price=1250000001 face=1000000000 cap_bps=2500`, then `custom program error: 0x177a` |
| the artefact's own checksum holds | `chain_client.load_artefact(records/devnet-artefacts.json)` | `state: verified`; the quote id recomputes to `q-18f4ec73dd8d8fd1`, the same value the file records |

So the boundary is proven **on a public cluster**, not only on a validator: face 1.0 SOL at
cap 2,500 bps admits exactly 1,250,000,000 lamports and refuses 1,250,000,001, and the refusal
is a transaction with a signature and a block time, which is the only form of it a sceptic can
look up. Both ledgers took the same path and differ only in the staged price.

**What is not proven by that pair**, and must not be implied: the record/hop accounting, the
destination check and the verified-wallet gate are absent from the program
(`programs/cap_hook/README.md`, "What the program does NOT do"), so the sentence the deployment
earns is the second half of D6's — *the program will not record a price over the cap* — and not
the first.

**The pair also does not prove that a stranger could not have set the price (added
2026-11-08T08:25Z).** v1's `SetPendingPrice` and `SetStatus` take no signer, and an immutable deploy
has no upgrade path, so on the deployed program any keypair can stage a price and flip a ticket's
status. What the devnet pair proves is the price predicate operating on prices the **deploy key**
chose; it does not prove a holder was kept from choosing a different number. v2 authenticates tags 2
and 3 and re-runs the exploit as two refused transactions (`6026`, proof `g`), and v2 has run only on
a local validator. `records/findings/37-program-v2-review-fixes.md` §1 and §3, `README.md` §"Deployed
on devnet, in part" and `docs/ON-CHAIN-DESIGN.md` §0 carry the same narrowing; this paragraph is the
one `records/DELIVERABLE.md` calls the measurement of record, so it belongs here and not only at §A6
item 6.

## A3. The console's `[DEVNET]` slot, and exactly when it shows what

The slot is state-specific, and this is the precise behaviour, measured in this pass:

- State `?event=evt_syn_02&tier=tier_stg_general&asOf=2026-11-07T18:34:29.183Z` → the page
  contains the signature, slot 519845921, blockTime 1794099003, and the sentence
  `[DEVNET] Verified at None against api.devnet.solana.com`. It renders **verified**, because
  the artefact's quote hash recomputes against exactly that state (recommended 1,380,000,000
  lamports at that instant).
- Any other state → `chain.state: "unverified"`, `reason: "quote_hash_mismatch"`, no signature
  (measured on `evt_syn_04` at `asOf 2026-11-07T18:00:00Z` through `tools/guidance.py`).

That is the design working: one recorded quote verifies for the state it was recorded on, and
nothing else inherits it. The slot's own sentence says it is *recorded, not independently
re-read*, and that a live re-read needs `TICKETPATH_RPC_ENABLED=1`, which is off.

**Added 2026-11-08T05:54Z. The slot exists and does not yet render the real devnet artefact as
an artefact.** It renders the recorded signature, slot, block time and quote hash for exactly the
state the artefact commits to, and its absent/unverified branches for every other state
(`ticketpath/console/page.py:370-402`). It does not carry a field saying whether the quote on
screen is the one the artefact records; no such field exists in the payload or the page, and
feature 2 (the recorded-versus-current quote rule) is `not built` in §0A. The instant line
still prints `None` because `checkedAt` never enters the payload (§A6 defect 1).

**Re-measured 2026-11-08T07:10Z, and the paragraph above is superseded.** Feature 2 landed. The slot
now has two separate facts and two states, measured by rendering the page from `tools/guidance.py`'s
payload in process:

- `evt_syn_02` at `2026-11-07T18:34:29.183Z`: `chain.state verified`, `matchesCurrentQuote True`,
  and the page prints the recorded verification instant and checker version, then the recorded
  `asOf`, signature, slot, block time and cluster, then the quote id, quote hash and recommended
  lamports, then the two transfer rows (`accepted` and `refused by the chain … 6010`), and then the
  sentence saying the number on the page is the quote the chain recorded.
- `evt_syn_04` at `2026-11-07T18:00:00Z`: `chain.state verified`, `matchesCurrentQuote False`, and the
  page prints the recorded block above plus the sentence saying the number on this page is computed
  now, is not the number the chain recorded, and naming `2026-11-07T18:34:29.183Z` as the recorded
  quote's instant.

So a verified artefact is now visible on every page rather than on one, and the page never presents a
freshly computed number as the recorded one. The `None` sentence in the paragraph above is fixed by
the same change: `checkedAt` and `checkerVersion` are in the payload and the page prints them.

The exact wording of both sentences was in flux when this was written: another agent was editing
`ticketpath/console/page.py` at 07:23Z, and `tests/test_console_recorded_artefact.py` was failing
against the new wording at that moment. What is stable, and what this row should be read as, is the
pair of payload facts (`state`, `matchesCurrentQuote`) and the rule that the two sentences never merge.

**Reconciled 2026-11-08T07:50Z against the console as it now stands, and the two paragraphs above are
superseded where they disagree.** Measured by rendering `page.chain_slot` from `tools/guidance.py`'s
payload:

- The sentence in the 03:45Z block, "one recorded quote verifies for the state it was recorded on, and
  nothing else inherits it", describes the loader before feature 2. It is the opposite of the current
  behaviour: the recorded block renders at **every** state the file verifies, and a separate sentence
  says whether this page's quote is that quote.
- The sentence "a live re-read needs `TICKETPATH_RPC_ENABLED=1`" is false. The adapter opens no socket
  on any flag, and the page now prints "A live re-read is not implemented in this build, so no flag on
  this server makes the page read the chain."
- `[DEVNET]` marks only the six fields the quote hash covers: quote id, event, tier, recommended
  price, instant and model version. Every other number (signature, slot, block time, cluster, mint,
  program, memo program, face, cap, transfer prices) is printed under one label, "The file states, and
  the quote hash does not cover", with no badge.
- `checkedAt` is the checker's clock and is printed unbadged: "The file verified. The checker wrote
  2026-11-08T00:50:25.281Z with checker devnet-publish-2026-11-07." It used to carry a `[DEVNET]`
  badge.
- The agreement sentence is about the **quote**, with both ids and both instants: "The quote this page
  commits is the quote the file records: quote id …, taken at …" or "This page commits … for …; the
  file records … for …". The recommendation sentence is separate and prints both numbers only where
  they differ.
- The evidence count is **3 on-chain transactions**, not 1: it counts the signatures the file carries.
- The absent state is about the console's file, not the project: "No devnet transaction is recorded in
  the console's artefact file." A file from another cluster has that cluster named, and the local
  rehearsal sentence is printed for `localnet` only.
- The explorer link is rendered only for an `https` URL whose authority is `explorer.solana.com`;
  anything else prints the signature as text.

## A4. Test and check inventory, counted in this pass

**Re-measured 2026-11-08T11:27-11:30Z, on the merged release tree, by the record-integration pass.**
Every number below is a reading taken then, with the command that produced it. Other agents were
writing this tree while the readings were taken, so each one is an instant and not a promise; the
09:48Z pair in §0 (1092 and 489) and every earlier table below stay where they are, tagged with the
tree they were taken on.

| Command | Count | Measured at 11:27-11:30Z |
|---|---|---|
| `python3 -m unittest discover -s tests` | **1251 tests** | `Ran 1251 tests in 29.602s`, `OK (skipped=27)`, exit 0 |
| `python3 -m unittest discover -s market_swarm/tests` | **771 tests** | `Ran 771 tests in 2.192s`, `OK (skipped=2)`, exit 0 |
| the two suites together, on disk | **2,022 tests** | 1251 + 771, both measured then |
| `python3 tools/doc_check.py --root .` | **7 checks, 24 allowed absences, 0 violations** | `doc_check: clean, 7 check(s), <repo root>; 24 allowed absence(s) suppressed by ALLOWED_ABSENCES`, exit 0 |
| `python3 tools/public_safety.py check --tracked` | **clean** | `public_safety: clean, tracked tree, 367 file(s)`, exit 0 |
| `git ls-files \| wc -l` | **367 files in the index** | 367 |
| `git ls-tree -r --name-only HEAD \| wc -l` | **285 tracked at `HEAD`** | 285, which is the commit and not the index |
| `find records/findings -name '*.md' \| wc -l` | **59 on disk** | 59 |
| `git ls-files records/findings \| wc -l` | **57 tracked** | 57 |
| `git ls-files -o --exclude-standard records/findings \| wc -l` | **2 untracked** | 2: `42-artist-fee-at-checkout.md` and `43-flip-tax-at-checkout.md` |
| `ls tests/test_*.py \| wc -l` | **51 test modules under `tests/`** | 51 |
| `ls market_swarm/*.py \| wc -l` | **15 Python files in `market_swarm/`** | 15 |
| `ls market_swarm/tests/test_*.py \| wc -l` | **23 test modules there** | 23 |
| `find market_swarm -name '*.py' \| xargs wc -l` | **24,147 lines with its tests** | 24,147 **[corrected 2026-11-08T12:00Z: 24,153, by the same command at `HEAD 3ad15bb`]** |
| `git ls-files frontend \| wc -l` | **82 files in the index** | 82, and 1,097,690 bytes by `du -cb`; the 81 / 1,097,001 in §A1 and §A10 was the reading before `frontend/.env.example` was staged at 11:18Z, and it is 689 bytes |

**[Corrected 2026-11-08T12:00Z, at `HEAD 3ad15bb`. Four rows above are readings of an instant at
which the tree they describe did not exist. The commits that built the merged tree are timestamped
2026-11-08 11:38:37 to 11:41:29 (`git log --format='%h %ci' dd42348..HEAD`), and the first of them,
`df02ea2` at 11:38:37, is eight minutes after the last reading in this table. So 367 was the index at
that moment, with 285 committed files at `HEAD 948b5d5` beside 82 staged frontend files -- which the
table itself half-admits where it says "which is the commit and not the index" -- and findings 42 and
43 were untracked because their commit `7df7597` landed at 11:39:08. The readings were true of the
index they were taken on and nothing that was measured at 11:27-11:30Z became the released tree.
Re-measured at `HEAD`, with the commands in the rows: `git ls-files | wc -l` → **394 tracked**;
`git ls-tree -r --name-only HEAD | wc -l` → **394 at `HEAD`**;
`git ls-files records/findings | wc -l` → **59 tracked findings**;
`git ls-files -o --exclude-standard records/findings | wc -l` → **0 untracked**; and
`python3 tools/public_safety.py check --tracked` → `public_safety: clean, tracked tree, 394 file(s)`.
The four old readings stay in the rows above so the instant each belongs to is visible.]**

**Beyond the counts, the merge changed the finding series.** `records/findings/` now runs to 43 with
gaps at 04, 05 and 22, and it gained two entries from the other checkout: the artist fee at 42 and the
flip tax at 43. They were written there as 38 and 39, and both numbers were already taken here by
`38-region-caps-local-validator.md` and `39-visitor-identity.md`. The directory holds 59 markdown files
in all, because the five cluster records under `33-b-region-cap-law-sources/` are `.md` too.

**Re-measured 2026-11-08T09:20-09:22Z at `HEAD 948b5d5`, on a clean tree, by the release-record
correction pass.** These supersede every count below where they overlap. Every number is a reading
taken in this pass, with the command that produced it; nothing here is copied from a review or from
the table below.

| Command | Count | Measured at 09:20-09:22Z |
|---|---|---|
| `python3 -m unittest discover -s tests` | **1079 tests** | `Ran 1079 tests in 30.321s`, `OK (skipped=26)`, exit 0 |
| `python3 -m unittest discover -s tests -t .` | **1079 tests** | `Ran 1079 tests in 30.107s`, `OK (skipped=26)`, exit 0 |
| `python3 -m unittest discover -s market_swarm/tests` | **489 tests** | `Ran 489 tests in 1.990s`, `OK (skipped=2)`, exit 0 |
| `python3 -m unittest discover -s market_swarm/tests -t .` | **489 tests** | `Ran 489 tests in 1.996s`, `OK (skipped=2)`, exit 0 |
| the two suites together, on disk | **1,568 tests** | 1079 + 489, both measured in this pass; `python3 -m unittest discover -s . -p 'test_*.py' -t .` reads `Ran 1568 tests in 32.200s`, `OK (skipped=28)` |
| `python3 -m unittest tests.test_event_jurisdiction` | **12 tests** | `Ran 12 tests in 0.204s`, `OK` |
| `python3 -m unittest tests.test_swarm_charts` | **41 tests** | `Ran 41 tests in 0.626s`, `OK` |
| `python3 tools/swarm_charts.py verify --out docs/charts` | **5 assets + index, labels only** | `PASS LABELS ONLY`, `series rebuilt from the dataset on 0 of 5 asset(s)`, `note: exit 3, labels and internal consistency only; nothing about the data was checked`, exit **3** |
| `python3 tools/doc_check.py --root .` | **7 checks, 24 allowed absences, 0 violations** | `doc_check: clean, 7 check(s), <repo root>; 24 allowed absence(s) suppressed by ALLOWED_ABSENCES`, exit 0, with 5 warnings (2 of them unlettered number collisions the tool reports as warnings by design) |
| `python3 tools/public_safety.py check --tracked` | **clean** | `public_safety: clean, tracked tree, 285 file(s)`, exit 0 |
| `git ls-tree -r --name-only HEAD \| wc -l` | **285 tracked files** | 285 |
| `git ls-files records/findings \| wc -l` | **57 tracked findings** | 57, equal to the 57 on disk (`find records/findings -name '*.md' \| wc -l`) |
| `ls tests/test_*.py \| wc -l` | **48 test modules under `tests/`** | 48 |
| `ls market_swarm/*.py \| wc -l` | **13 Python files in `market_swarm/`** | 13 |
| `ls market_swarm/tests/test_*.py \| wc -l` | **16 test modules there** | 16 |
| `find market_swarm -name '*.py' \| xargs wc -l` | **16,425 lines with its tests** | 16,425 |

**Two counts were never true of the commit that carried them, and this is the distinction the file
exists to keep.** `git diff --name-only 4c1b23b..HEAD -- tests market_swarm/tests` prints nothing, so
the test tree committed in `4c1b23b` is the tree measured above; the 1076 and 436 readings in the
table below were taken at 08:13Z on a working tree that was never committed. `tests/test_event_jurisdiction.py`
has had 12 test methods since `0266570`, two commits before that records commit, so the `11 tests`
row below was already wrong when it was written. The counts here are of committed code.

**The tree moved under these readings, again, and this is the second half of the same point.**
`git status --porcelain` printed nothing when the table above was taken at 09:20-09:22Z, so every
number in it is a reading of the committed tree at `948b5d5`. A parallel pass editing `tools/doc_check.py`,
`tools/swarm_charts.py`, `ticketpath/core/region_caps.py` and five test modules then added tests to
the working tree without committing. The same commands at 09:27Z read `Ran 1091 tests` for `-s tests`
and `Ran 44 tests` for `tests.test_swarm_charts`. Neither of those is a HEAD number and neither should
be pasted; the `market_swarm` counts, the 285 tracked files, the 57 findings and the two check counts
did not move. Take a reading when you need one, and say which tree it was taken on.

**Measured 2026-11-08T07:29-07:31Z by the ten-feature documentation pass, while a concurrent build was
landing.** These are that pass's own readings, and they are kept below as the earlier reading rather
than overwritten. The suite is green; every count is quoted with the command that produced it.

| Suite | Count | Measured (2026-11-08, this pass) |
|---|---|---|
| `python3 -m unittest discover -s tests -t .` | **1058 tests** | `Ran 1058 tests in 30.275s`, `OK (skipped=26)` (07:47Z, after the v2 review's tests landed) |
| `python3 -m unittest tests.test_onchain_sim` | **24 tests** | `OK` |
| `python3 -m unittest tests.test_devnet_publish` | **81 tests** | `OK` |
| `python3 -m unittest tests.test_console_recorded_artefact` | **20 tests** | `OK` |
| `python3 -m unittest tests.test_swarm_charts` | **41 tests** | `OK` |
| `python3 -m unittest tests.test_forecast_score` | **18 tests** | `OK` |
| `python3 -m unittest tests.test_forecast_score tests.test_onchain_v2` | **63 tests** | `OK` |
| `python3 -m unittest tests.test_onchain_v2` | **45 tests** | `OK` |
| `python3 -m unittest tests.test_onchain_v2 -k TicketRecord` and `-k band` and `-k jurisdiction` | **6, 2, 2** | `OK` each |
| `python3 -m unittest tests.test_onchain_v2_live` | **26 tests** | `OK (skipped=26)`: gated on `TP_ONCHAIN_V2_LIVE=1`, and the run writes the run's own artefact |
| `python3 -m unittest tests.test_event_jurisdiction` | **11 tests** | `OK`. **[CORRECTED 2026-11-08T09:22Z: 12 tests today (`Ran 12 tests in 0.204s`, `OK`); the file has had 12 methods since `0266570`, so 11 was wrong when written]** |
| `python3 -m unittest discover -s market_swarm/tests -t .` | **436 tests** | `Ran 436 tests in 1.864s`, `OK (skipped=2)`. **[CORRECTED 2026-11-08T09:22Z: 489 tests, `Ran 489 tests in 1.996s`, `OK (skipped=2)`]** |
| `python3 -m unittest market_swarm.tests.test_forge_policy market_swarm.tests.test_feature9_fixes` | **89 tests** | `OK` |
| `python3 tools/swarm_charts.py verify --out docs/charts` | **5 assets + index** | **[CORRECTED 2026-11-08T09:22Z: this row read `PASS`, series rebuilt from the dataset and matched on all 5, exit 0, which the tool cannot print. Re-measured: `PASS LABELS ONLY`, `series rebuilt from the dataset on 0 of 5 asset(s)`, `note: exit 3, labels and internal consistency only; nothing about the data was checked`, exit 3. The datasets are absent (`.swarm-runs/` is not in the repository; `docs/CHARTS.md:48`)]** |
| `python3 tools/tp.py doc-check` | **0 violations on this pass's documents, 6 checks** | green at 07:24Z, red at 07:27Z only on `programs/cap_hook/README.md:18` (a finding not yet written), and green again at 07:30Z: `doc_check: clean, 6 check(s), <repo root>; 21 allowed absence(s) suppressed by ALLOWED_ABSENCES`, exit 0 (§F item 20). **[CORRECTED 2026-11-08T09:22Z: the check count is now 7 and the allowed absences 24, `doc_check: clean, 7 check(s), <repo root>; 24 allowed absence(s) suppressed by ALLOWED_ABSENCES`, exit 0]** |

The two suites together are **1,494 tests** on disk, the `tests/` half and the `market_swarm` half both
measured by this pass. **[CORRECTED 2026-11-08T09:22Z: 1,568 tests on disk at `HEAD 948b5d5`, 1079 +
489, both halves re-measured then. The 1,494 was 1058 + 436.]** The 26 skips are the live v2 half; the 2 in `market_swarm` are its two live
gates. **Never quote the count without the command**: it has moved 293 → 306 → 309 → 352 → 453 → 546 →
610 → 626 → 671 → 834 → 971 → 1007 → 1053 → 1058 in one day, and this table's own first reading was 971 at
07:05Z.

**The tree moved under these readings, and this is the correction.** The 07:05Z reading of the same
command was `Ran 971 tests in 28.081s`, `OK (skipped=19)`, with smaller per-file counts
(`test_onchain_sim` 24, `test_devnet_publish` 70, `test_console_recorded_artefact` 19,
`test_onchain_v2` 39, `test_forecast_score` 17, the feature-4 pair 56). At 07:22Z the same command read
`Ran 993 tests`, `FAILED (failures=77, errors=223, skipped=19)`, because another agent was midway
through `ticketpath/console/page.py` and `ticketpath/adapters/chain_client.py`; at 07:30Z a further
wave made it 1053 tests with 4 failures and 1 error, by 07:31Z it was `OK` at that count, and the v2 review's tests put it at 1058 by 07:47Z. This
documentation pass edited documents and nothing else, so the only count it can honestly give is a
timestamped one.

**Re-counted 2026-11-08T05:51-05:54Z for the feature-1 documentation pass.** These are the numbers
this edition adds; the 03:45Z rows below are kept as the earlier reading rather than overwritten.

| Suite | Count | Measured (2026-11-08, this pass) |
|---|---|---|
| `python3 -m unittest discover -s tests -t .` | **626 tests** | `Ran 626 tests in 24.402s`, `OK` |
| `python3 -m unittest tests.test_devnet_publish` | **63 tests** | `Ran 63 tests in 0.900s`, `OK` |
| `python3 -m unittest tests.test_onchain_sim` | **23 tests** | `Ran 23 tests in 0.002s`, `OK` |
| `tools/tp.py doc-check` | **red: 25 violations in 7 files** | `exit=1`; the tool appeared during this pass (it is untracked and its own test module is red), 21 of the violations are missing paths in older records, 3 are the `ids` rule misreading the memo table (see the note below), 1 is the implemented-today table this step was told not to add |

| Suite | Count | Measured at 03:45Z (carried, not re-run) |
|---|---|---|
| `python3 -m unittest discover -s tests` | **610 tests, 36 modules** | `Ran 610 tests in 23.958s`, `OK` |
| `python3 -m unittest tests.test_devnet_publish` | **56 tests** | `Ran 56 tests in 0.974s`, `OK`, before feature 1's tests were added |
| `python3 -m unittest discover -s market_swarm/tests` | **274 tests** | `Ran 274 tests in 1.028s`, `OK`, not re-run in this pass |
| `tools/public_safety.py check --tracked` | 64 hits in 9 files | see §A6, not re-run in this pass. **[CORRECTED 2026-11-08T09:22Z: clean at `HEAD 948b5d5`, `public_safety: clean, tracked tree, 285 file(s)`, exit 0, since `aea1cbe`]** |
| `tools/build_fixture_store.py --check` | store invariants and determinism | `matches a fresh build exactly`, not re-run |
| `tools/console-check.py` | **not run** | needs a running backend; last reading 113 assertions, 0 failed, at 18:40Z |
| `tools/check_frontend_attach.py` | **not run** | same reason; last reading 43 passed, 0 failed, at 18:40Z |
| `tp.py gate` | **not run** | it shells out to the two above |

Total suite size on disk: 626 + 274 = **900 tests**, with the `tests/` half measured now and the
`market_swarm` half carried from 03:45Z. **Never quote the count without the command**: it has
moved 293 → 306 → 309 → 352 → 453 → 546 → 610 → 626 in one day, and the 56 → 63 move in
`test_devnet_publish` is feature 1's tests.

**The tree moved under this measurement.** A rerun at 2026-11-08T05:58Z read `Ran 671 tests` with
4 failures and 8 errors: in `tests/test_boundaries.py` (an untracked `ticketpath/core/region_caps.py`
imports `dataclasses`), `tests/test_cli.py` (the gate's count and summary lines), and
`tests/test_doc_check.py` and `tests/test_swarm_charts.py` (two tools that landed during this pass).
None of those is feature 1's code; the 626 `OK` above is this step's reading and the feature-1 tests
passed in every run.

**On the three `ids` violations, which are mine and are a tool mismatch, not a wrong claim.**
`tools/doc_check.py` reports `README.md:151` and `docs/ON-CHAIN-DESIGN.md:162,981` as quoting a memo
program id the code does not carry. It reads the table with `doc_check.memo_table(...)`, which
resolves only literal ids inside `MEMO_PROGRAMS`; step 1's mapping refers to the constants
`MEMO_PROGRAM_DEVNET` and `MEMO_PROGRAM_CLI`, so the reader returns
`{'*': 'MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr'}` and cannot see the measured devnet id. The
code carries both ids; the checker's parser does not resolve the names. This pass did not edit the
tool or the code, so the violation stands until whoever owns `tools/doc_check.py` reads the mapping's
values.

## A5. The engine's mathematics — re-checked where it was cheap

Re-derived in this pass from `python3 tools/guidance.py --event evt_syn_04 --as-of
2026-11-07T18:00:00Z` (34,766 bytes of labelled JSON), not taken from the older edition:

- **Value level** `= face × exp(mean log(price/face))` over the tier's own marks; for the
  default tier of `evt_syn_04` this is 930,549,431 lamports on face 800,000,000, i.e.
  ln(level/face) = 0.15115.
- **Value band** `= level × exp(∓ z·max(τ, 0.10))`, `z = 1.6449`, `τ` declared 0.2. The payload
  prints `loLamports 669,676,793` and `hiLamports 1,293,045,022`, which is level × e^∓0.32898
  and 0.32898 = 1.6449 × 0.2. It agrees to the lamport, and the width being `2zτ` in logs is the
  invariant a reader can check without the code.
- **Cap handling**: on a binding cap the level is refused (`no_upper_bound`), the floor is the
  highest recorded price and the band is `[floor, None]`; on a non-binding or uncapped event the
  band's top is clipped to the lower of the two ceilings and the clip names which cap produced
  it.
- **Sale probability** is refused by name (`not_identified`); **no interior optimum** exists
  (`no_demand_response`, with the three inputs it would need named).
- Under `?sim=1` the simulated state machine still renders: **7** occurrences of the
  `[SIMULATED]` badge on that page against **3** on the default page (`grep -c`, plain string
  count, in this pass). The older edition described the same block as five arms; the arm count
  was not recounted here, only the badge count.

The rest of the older edition's §A2/§A3 — the pooling method, the prior, the badge counts, the
refusal list — was **not** re-derived this pass. `ticketpath/core` has not changed since
`375126f` (17:25Z), so those readings still describe this code; treat them as
*measured 18:25Z, code unchanged since* rather than as fresh numbers.

## A6. Known defects, and claims the evidence does not support

**1. The verified chain slot prints its verification instant as the string `None`.**
`ticketpath/console/page.py:376` renders `chain.get("checkedAt")`, and the
`chain.update(...)` at `ticketpath/orchestrator.py:592-600` never puts `checkedAt` into that dict — it carries
`signature`, `slot`, `blockTime`, `cluster`. Measured: the page reads
`[DEVNET] Verified at None against api.devnet.solana.com`. The artefact has
`checkedAt: 2026-11-08T00:50:25.281Z`; the payload drops it. **Not fixed by this pass** (this
pass does not touch code). It is the single most visible defect now that the slot renders at
all, because it is the one line on the page that is supposed to say when the claim was checked.

**Closed 2026-11-08T08:10Z, measured by this pass.** Feature 2 fixed it. `_chain_payload` now builds a
`recorded` block carrying `checkedAt` and `checkerVersion` from the artefact, and
`ticketpath/console/page.py`'s `_recorded_quote` prints them. Rendered from `tools/guidance.py`'s
payload for the pinned state, the line now reads `[DEVNET] The file verified at 2026-11-08T00:50:25.281Z
with checker devnet-publish-2026-11-07`. The paragraph above is left as the record of the defect.

**Corrected 2026-11-08T07:50Z: the wording changed again, and the badge came off.** The line now
reads "The file verified. The checker wrote `2026-11-08T00:50:25.281Z` with checker
`devnet-publish-2026-11-07`", with no `[DEVNET]` badge on the timestamp: `checkedAt` is the checker's
own clock, not a chain fact, and the page stopped claiming devnet provenance for it. The defect this
item recorded stays closed; only the sentence's shape moved.

**2. The public-safety gate still fails on the published tree.**
`python3 tools/public_safety.py check --tracked` → **64 hits in 9 tracked files**, all at HEAD
and pushed: `records/FINAL-PROOF-2.md`, `FINAL-PROOF.md`, `DEMO-PROOF.md`,
`findings/07-engine-review.md`, `findings/10-final-review.md`, `REPO-CONSISTENCY.md`,
`FRONTEND-HONESTY-PATCH.md`, `CONTRACT-CONFORMANCE.md`, `FIXTURE-STORE.md`. Classes:
live-service, home-path, fleet-repo. The hook only checks `--staged`, so a commit that does not
touch those files never sees them. `AGENTS.md` now states this accurately (it was corrected to);
`docs/PUBLIC-SAFETY.md` is the full account. Removing them forward does not unpublish history —
that is the operator's call, not a tool's.

**[CORRECTED 2026-11-08T09:22Z: this defect is closed, and the paragraph above is kept as the
record of it. The removal it calls the operator's call was made in commit `aea1cbe`, forward and
not by rewriting history: the eight records were redacted and `.public-denylist` was not touched,
so no exception was bought. Re-measured at `HEAD 948b5d5`: `python3 tools/public_safety.py check
--tracked` → `public_safety: clean, tracked tree, 285 file(s)`, exit 0. The nine files named above
are still published; what they no longer carry is the process handles. The sentence that the hook
only checks `--staged` remains true of the hook.]**

**3. The chain client's own docstring is stale.** `ticketpath/adapters/chain_client.py:1-11`
says "there is no toolchain, no keypair and no program on this machine". There is a toolchain, a
program and a devnet deployment. The code's behaviour is correct; the sentence is not. Left in
place because this pass does not touch code.

**4. `market_swarm`'s own design record has no verification section.**
`records/findings/31` ends with "Filled in from the runs, with the surface named. See the
section at the end." and there is no such section. The package's 436 tests pass (corrected
2026-11-08T08:25Z from 274; **[corrected again 2026-11-08T09:22Z: 489 tests, `Ran 489 tests in
1.990s`, `OK (skipped=2)`]**); what has *not*
been run is a live validator run and any dataset, which is what that heading is reserved for.

**5. Carried, not re-measured this pass** (from the 18:25Z edition, code unchanged since except
where noted): the console has no viewport meta and overflows at 390 px; the price is below the
fold on both surfaces; two sentences the audit called out are still on the cold-start page;
`labels.py` A4's "based on … sell-through" overstates; `uvicorn`-class robustness (traceback to
stderr, no request log). Each was a live measurement when taken; none was re-taken here.

**6. v1 on devnet has an unauthenticated staging path, and it narrows what the devnet pair proves.**
Added 2026-11-08T07:50Z from `records/findings/37-program-v2-review-fixes.md`. v1's `SetPendingPrice`
and `SetStatus` take no signer, so on the deployed devnet program any keypair can stage a price and
flip a ticket's status; an immutable deploy has no upgrade path, so that hole is in v1's bytes
permanently, and the devnet refusals prove the price predicate on prices the deploy key chose, not
that a stranger was kept from choosing them. v2 authenticates tags 2 and 3 with the record's
`authority` and the reviewer's exploit is two refused transactions in the sealed artefact (proof `g`,
`6026` twice, record bytes unchanged); v2 has run only on a local validator. Measured by finding 37
§1 and §3, and stated in `docs/ON-CHAIN-DESIGN.md` §0 and in `README.md`.

**7. Two things in this tree both decide what a jurisdiction means, and they are not reconciled.**
Added 2026-11-08T07:50Z. The v2 program stores `jurisdiction` (`[u8; 2]`) and `policy` and does not
interpret either: no mapping from a country code to a policy exists in `programs/cap_hook/`. A
separate piece of work in this same tree, by another session, resolves a jurisdiction to one of
`capped` / `monitored` / `unresolved` from a dated table (`ticketpath/data/region-caps.json`), with
its own decision entry (D11 in `records/F-decision-log.md`), its own design
(`records/REGION-CAPS-DESIGN.md`) and its own local-only program (`programs/region_gate/`). Both are
in the tree and neither is wrong about its own scope, but they are not yet reconciled: the record's
two bytes and the table's resolved policy are not tied together by any code, and no instruction
compares them. **The reconciliation can only be nation-level**, because the record is `[u8; 2]` and
72 of the table's 82 codes are subdivisions (`CA-ON`, `CA-QC`, `AU-NSW`, `US-CA`) that do not fit
two bytes; the finer mapping has nowhere to be written on the v2 record. That reconciliation, and
which of the two is the platform's answer, is the operator's to decide. This file records the
conflict rather than resolving it, and nothing here deletes D11.

## A7. What is committed, and what is only on disk

This is the sharpest operational fact of the pass.

| On disk, **not in git** | Size / content |
|---|---|
| `records/devnet-artefacts.json` | the whole devnet proof: program id, mint, memo, three signatures, two block times, the refusal's error |
| `records/findings/20`, `23`, `24`, `25`, `26`, `27`, `28`, `29`, `30`, `31` | ten investigations, 5,888 lines |
| `market_swarm/` (11 modules, 7 test modules) | 9,228 lines with tests |
| `records/STATE-OF-PROJECT.md` | this file, rewritten in this pass |

| Modified, uncommitted | Lines changed |
|---|---|
| `.gitignore` | +19 |
| `tests/test_devnet_publish.py` | +486 |
| `tools/devnet_publish.py` | +1,102 / −? |
| `tools/check_frontend_attach.py` | +360 |

**Corrected 2026-11-08T08:25Z: the four line counts above are from 03:30Z and one of them is not a
number.** Re-measured with `git diff --numstat`: `.gitignore` **+25 / -0**,
`tests/test_devnet_publish.py` **+964 / -21**, `tools/devnet_publish.py` **+1,213 / -133**,
`tools/check_frontend_attach.py` **+331 / -29**. The table's "`-?`" was never a measurement, and the
deletions are now stated for every file. The line above that reads "`market_swarm/` (11 modules, 7
test modules) | 9,228 lines with tests" is superseded by the A1 correction: twelve Python files,
fifteen test modules, 15,037 lines. **[CORRECTED 2026-11-08T09:22Z: thirteen Python files, sixteen
test modules, 16,425 lines, measured at `HEAD 948b5d5`.]**

`git rev-list --count origin/main..HEAD` → `0`. Nothing has been pushed, and `HEAD` `33d95b3`
is the commit that put the hook, the publisher and the read-back into the tree — before the
deployment succeeded. A judge or an operator cloning the public repository today gets the
program source and the publisher but **not the artefact**, so the console's slot renders absent
for them. One commit of explicit paths closes it; this pass did not make it.

**Added 2026-11-08, on the frontend import.** `frontend/` is in the index and not in any commit: 81 files, 1,097,001 bytes as staged, `frontend/.gitignore` included. `git ls-files frontend | wc -l` reads 81 once the index is written. Nothing was pushed, and the push gate reads commits, so no reader of the public repository sees these files until the operator makes the commit.

**[Corrected 2026-11-08T11:41Z: the commit is made, `009f103`, and the paragraph above describes the state before it. `git ls-tree -r --name-only 009f103 frontend | wc -l` reads 82, the eighty-second being `frontend/.env.example`, 689 bytes, which the import had excluded. 1,097,690 bytes by `git ls-files frontend | xargs -d '\n' du -cb | tail -1`. The last sentence is now the one that still applies: nothing was pushed, so no reader of the public repository sees these files until the operator pushes.]**

## A8. Performance, measured this pass

One instance of the server, started by this pass on a scratch loopback port and killed at the
end of the measurements. The scratch port is not named here: it was mine, it is closed, and a port in
prose is the kind of machine detail `AGENTS.md` asks a record not to carry. The project's own port 8788
is the only port this file names, and nothing was listening on it when this pass began (a `GET /health`
against it was refused).

| What | Measurement | How |
|---|---|---|
| console page `/` | 2.2–4.5 ms, 5 samples | `curl -w %{time_total}` |
| `/api/events?limit=100` | 0.4 ms, 10,161 bytes | same |
| console page bytes | **17,380** at `/` and **17,307** at the pinned `[DEVNET]` state, measured 2026-11-08T08:07Z. The 13,726 in this row was the 18:25Z reading and is not identical to today's: feature 2 added the recorded block (corrected 08:25Z) | `curl -w %{size_download}` |
| `?sim=1` page | 14,634 bytes | same |
| the pinned `[DEVNET]` state page | 14,275 bytes | same |
| whole test suite | 23.96 s for 610 tests | `unittest discover` own wall |

## A9. The trading-swarm harness, and what it is not

`market_swarm/` is a second, separate package: a bounded agent swarm that trades synthetic
tickets through the **real** `cap_hook` on a local validator (or devnet), writing every action
to an append-only dataset. Its contract was written before its code (`CONTRACT.md`), and the
invariants are tests rather than intentions: cluster is a closed set `{local, devnet}` with no
branch to mainnet, no faucet call shape anywhere in the package, agents hold no key material
(only `gateway.py` reads a keypair path and it signs out of process), hard budgets in lamports
and in action count, a kill switch in three forms, and a writer that refuses any row without
`synthetic: true`.

**Status: in progress.** 436 tests pass in 1.9 s (corrected 2026-11-08T08:25Z from "274 tests pass in
1.03 s"); the package is twelve Python files, fifteen test modules and 15,037 lines with its tests.
**[CORRECTED 2026-11-08T09:22Z: 489 tests pass in 1.99 s (`Ran 489 tests in 1.990s`, `OK
(skipped=2)`); the package is thirteen Python files, sixteen test modules and 16,425 lines. The
sentence three lines below this one, that there is no run config in the tree, is also superseded:
`market_swarm/example-run.json` and `market_swarm/example-llm-run.json` are both committed, as the
A1 correction says.]**
What is missing, measured: there is no run
config file in the tree, so the CLI's `plan` or `run` verb cannot be exercised without one; no
dataset has been produced; no validator run has been made in this package. And the part that
would cost money is deliberately switched off — `forge_policy.py` implements a subforge-shaped
LLM policy, refuses to construct without an explicit cost acknowledgement, and is not run
against live agents here.

**The label, which is the whole point of the package's existence: every number it produces is
synthetic and is E-class evidence about nothing real.** `records/findings/31` states it, the
dataset writer enforces it row by row, and nothing in `records/` may quote a `market_swarm`
number as a finding about tickets. It is a mechanism and load test for the pricing model: how
many hops, what markups, where the cap binds, what an agent trying to break the cap gets.

---

# B. WHAT A USER SEES

Two surfaces, both loopback, neither hosted. A judge with no URL sees neither, so the video is
the only way any of it travels.

- **The console** at the project's own documented `127.0.0.1:8788/`. 17,380 bytes at `/` and 17,307
  at the pinned state on 2026-11-08T08:07Z (13,726 was the 18:25Z reading, before feature 2 added the
  recorded block), no
  JavaScript, every state a URL. A synthetic-data banner first, then evidence counts, then the
  decision or a named refusal, then the `[DESIGN]` table, then the chain slot. On the default
  selection it prints a floor of at least 1.38 SOL tagged `[UNVALIDATED]` and says it is a
  bound. With the artefact in place, one pinned state renders a verified devnet signature — with
  "Verified at None" where the instant should be (§A6 defect 1).
- **The frontend**, the platform's own Next.js app served as a copy outside this tree, whose
  `/pricing` frames the console through a closed proxy. Eight event cards, an event page with a
  custody trail per ticket, an organizer roll-up, and a footer on every page saying the ledger
  is simulated. Last measured green at 18:40Z; not re-measured this pass.

The reading order problem the older edition named is unchanged and worth repeating once: the
number is below the fold and the honesty is above it, so a first-time reader meets a compliance
notice before they meet the product.

---

# C. A JUDGE'S VIEW

**This pass did not re-score the entry.** `records/findings/23` scored it at 20:40Z,
`records/findings/24` re-measured 23's facts and corrected three, and `records/findings/29`
superseded both in the one place that matters after the deployment. What changed, and what is
measured:

The materials test — "a working product that uses Solana for something it's good at … not a
chain bolted onto a web2 app" — was **0 of 4** at 18:25Z. It is now, on the evidence in §A2:

| Test | State now | Evidence |
|---|---|---|
| an account that belongs to the project | **met** | program `5EJ1GU3M…4eva`, executable on devnet |
| a transaction signature with a block time | **met** | three signatures, block times 1794099003 / 1794099006 / 1794099023 |
| a program the team did not write, doing work the product depends on | **partial** | Token-2022 processes each transfer and calls our hook (both are in the logs); the shipped app still calls no chain |
| the product reading that state back | **partial** | the console renders the recorded artefact with a recomputed hash; `rpc_adapter` opens no socket, so it is a recorded read, not a live one |

`records/findings/29` §1 reaches the same 2 clear / 2 partial and is the authority; the table is
here because it is the one line a judge will check.

**Score band: 55/100 at 18:25Z, not re-scored.** The two axes that moved are Technology and
Completion, both of which the older edition said "move with one devnet write". The write has
happened and is independently verifiable. No number is claimed for it here, because a point
estimate would be a prediction (class D) and the operator has three prior passes that disagree
by a few points each.

---

# D. THE FINDING LIST, 20 TO 31, ONE LINE EACH

`records/findings/22` does not exist: the pass that took that number deleted its own file when
23 answered the same brief (`24` §header records this). 20 and 23–31 are untracked; 21 is
tracked.

| # | One line | Status |
|---|---|---|
| 20 | Hosting and data: 82 static HTML pages from the console already served can be published on GitHub Pages in ~2.5 h; keep the fixtures, do not scrape, because an ask is not a realised transaction | option, not taken |
| 21 | The cap-check hook is in the tree and the publish pipeline was rehearsed end to end against a local validator; devnet still unfunded at that reading | **superseded by 28 and by the deployment** |
| 23 | What the judged score is made of: the live rubric is four equal criteria, the Top 3 sentence is not a rubric at all, and the entry was 0 of 4 on it at 20:40Z | analysis; superseded in one section by 29 |
| 24 | Second pass on the score: independent re-measurement of 23's facts, three corrections, and the criteria fact 23 lacked | review |
| 25 | Solana from first principles, for choosing a project: what the chain is good at, what changed in October 2026, and the shapes a Solana-native product takes. Chooses nothing | reference |
| 26 | Identity-bound wallets and airlines: proof-of-personhood options, name-matched tickets, and which parts of this design could be chain-native. Chooses no concept | option |
| 27 | The submission itself: what a judge physically sees, what past videos were built like, three storyboard options. Decides nothing | option |
| 28 | The duplicate-mint failure and its fix: a resume file written before the mint exists, four transport retries, three states per leg (recorded / pending / nothing), and four races a local validator shows that devnet does not | **fixed and tested** |
| 29 | Nineteen things this project could put on Solana, costed against the hours left, ranked, with three combinations. The operator's eleven plus eight more | option list; the authority on the materials test |
| 30 | What `subforge` is: the forge subagent runtime, its API, and the eight limits that decide a harness design (all tiers one model, silent tier fallback, no default timeout, p90 ~207k output tokens per run) | reference |
| 31 | The trading-swarm harness: a bounded agent swarm through the real hook, producing synthetic-labelled datasets that are E-class evidence about nothing real | in progress (§A9) |

---

# E. WHAT IS AN OPTION, AND WHAT IS A DECISION

Stated separately because the difference is the thing that keeps this record honest.

**Decisions recorded in the tree.** D6 in `records/F-decision-log.md`: the cap is fixed at event
creation, no escrow, no nullifier, no sybil claim. The submission's provenance and team entries
in `records/F-decision-log.md` D8 and `SUBMISSION-PACK.md` §2.8. The on-chain scope, in
`programs/cap_hook/README.md`'s "What the program does NOT do".

**Options, not decisions.**

- **The idea portfolio** (`records/findings/29`): nineteen ideas with hours and risks, three
  combinations, a ranked shortlist, and an explicit "decisions this file does not make" section.
  Nothing in it was built. Choosing from it is the operator's.
- **A region-varying cap** (the direction the operator named in this session). **No file in this
  tree describes it, and nothing is built for it.** What exists is the cap as one number per
  tier, immutable once the record is created (`programs/cap_hook/README.md`), and one observation
  that cuts against the cheap version of the idea: an SPL transfer carries an amount and no
  price, so a cap that varies by region needs the region to be written somewhere the hook can
  read, and there is no such field today. Recorded here as an **option, unverified as a design**
  — there is no costed proposal to point at.
- **The swarm harness** (§A9) is a build in progress, not a decision about the product; its
  output is synthetic by construction and cannot be evidence for the engine.

**Dropped, per the operator in this session, and not recorded anywhere in the tree:** the
passport / identity-bound-wallet and airline directions from `records/findings/26`. That file
examines both and chooses nothing; no file here records the drop. Written down here so the next
pass does not re-open it, and attributed to him rather than to a document.

---

# F. WHAT THIS PASS COULD NOT VERIFY

Listed so nobody mistakes silence for a measurement.

1. **`tools/console-check.py` and `tools/check_frontend_attach.py`** — not run; both need a
   backend, and none was running. Their last readings (113 assertions, 43 checks) stand as of
   18:40Z.
2. **The frontend copy's pages** — not opened this pass. Every §B statement about the frontend
   is carried from 18:25Z and marked as such.
3. **The engine's pooling method, prior values, badge counts and refusal list** — not
   re-derived. `ticketpath/core` unchanged since `375126f`.
4. **The two live defects the older edition measured on a browser** (no viewport meta, price
   below the fold) — not re-measured; no browser was used this pass.
5. **Whether the deployed program's `.so` on devnet matches `programs/cap_hook/target/`** — the
   build artefact is git-ignored and its hash was not compared to the deployed account's data.
   The deployed program is 36 bytes of account data at the loader, which is the loader's record
   of the program, not the bytecode; the bytecode hash comparison would settle it and was not run.
6. **The `market_swarm` harness on a validator** — never run: no run config in the tree.
7. **The capture directory beside `tools/shot.py`** holds **12** PNGs, newest 18:04Z. The pack's
   claim of a thirteenth capture at 18:40Z is not supported by that directory now. *Unverified*;
   the claim may be true of a different path.
8. **The capture (screenshot) claim in the pack and DELIVERABLE** — 12 files exist, so "there are
   no screenshots" is false; how many a submission may attach is not something this pass checked.
9. **Mainnet-beta's memo program id**: named as the `solana` CLI's shipped memo program
   `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`, class D. No mainnet call was made in this pass; a
   `getTransaction` on a mainnet memo transaction would measure it the way finding 40 measured
   devnet's.
10. **`testnet`'s memo program id**: deliberately absent from the table, so the client raises
    `UnknownCluster` on it. No id has been measured there, and a refusal is the honest state.
11. **The localnet memo mapping**: `MemoSq4gq...` for a CLI-written memo on a local validator is
    class D: the CLI's documented behaviour and this repository's assumption, not a measurement.
    Finding 40 §6 said no toolchain could try it; its appended correction records that the
    toolchain is installed here, so the two rows finding 40 §7 marks untestable may now be
    testable. This pass did not run a validator.
12. **The full suite's greenness depends on files outside feature 1.** An earlier run of
    `python3 -m unittest discover -s tests -t .` at 05:51Z reported 626 tests with one failure
    (`tests.test_boundaries`: an untracked `ticketpath/core/region_caps.py` imported `dataclasses`,
    which the boundary allowlist does not carry). That file was gone by the next run, which is the
    `OK` quoted in §A4. The feature-1 tests passed in both runs.

**Added 2026-11-08T08:20Z by the ten-feature documentation pass.** These are the five things this
pass could not verify, plus the two structural limits that belong beside them.

13. **Mainnet-beta's memo program id is unmeasured.** Nothing was ever read off mainnet, so no id is
    named for it: `chain_client.MEMO_PROGRAMS` maps `devnet` and `localnet` only, and
    `memo_program_id("mainnet-beta")` raises `UnknownCluster`. `MemoSq4gq…` remains a named literal
    in that file because documents quote it and the `ids` gate compares against it, and it is class D.
    A mainnet `getTransaction` on a memo transaction would measure it the way finding 40 measured
    devnet's, and this pass made no mainnet call.
14. **Features 5 and 7 are blocked, not unfinished.** Token-2022 ceils the fee, so at `decimals 0`
    and `amount 1` any rate from 1 to 9999 bps withholds the whole ticket; the only fees this mint
    can express are 0 and everything. Nothing is built for the artist fee or the flip tax, `ClaimRebate`
    (tag 7) does not exist, and `6027` and `6028` are declared in the source and raised by nothing.
    `records/findings/36-transfer-fee-on-a-one-unit-ticket.md` is the measurement and `Q5` in
    `records/F-decision-log.md` puts the three surviving alternatives to the operator.
15. **No third-party program consumes the band feed.** `["band", mint]` exists and was published and
    read back on a local validator, but this repository is its only reader, so the composability
    claim is unproven. `refused` is stored in the account and not enforced by anything.
16. **A local rehearsal cannot land a memo at all, so `tools/devnet_publish.py --local` cannot
    complete its memo step.** A local validator's genesis holds the measured id as a program-data
    stub (`ProgramData.slot = 0`), `--clone` does not replace it, and `--account` replaces it and then
    hits the runtime's program cache limit. Four bounded local runs, quoted in `records/findings/40`'s
    second CORRECTION. This is a property of this CLI and this validator version, not of the memo id.
17. **The live agent adapter's cap is parent-side.** The child is spawned with no limit of its own
    and `start_new_session=True`, so a SIGKILLed parent leaks a child with no wall clock and no token
    cap. The provider usage log is also written by an extension that a `--no-extensions` child does
    not load, so 38 hardened children spawned by another session have only their own session files
    as a record. Both are stated where the feature is documented (D17, `S32`) and neither is fixed.
18. **The v2 live half was not re-run by this pass.** `tests/test_onchain_v2_live.py` starts a local
    validator, deploys the program and sends real transactions, and it rewrites
    `records/onchain-v2.local.json`, which is not one of this pass's files. The floor, band, forecast,
    score, `policy 2` and floor-above-ceiling numbers quoted in §0A and §A4 are read from that
    artefact (written 2026-11-08T06:48:48.836Z) and were not re-executed here. The decoder and wire
    half was re-run: `tests/test_onchain_v2.py`, 39 tests, `OK` at 07:05Z and 45 tests, `OK` at 07:22Z
    on the moved tree.
19. **The tree was being edited while this pass ran, so the readings above are timestamped.** Between
    07:14Z and 07:23Z another agent changed the program sources (five new error codes `6029`-`6033`,
    `InitializeExtraAccountMetaList` made argument-free, `InitializeRecord` moved to the mint's
    authority and tags 2 and 3 to the record's), `ticketpath/adapters/chain_client.py` and
    `ticketpath/console/page.py`. The `IMPLEMENTED TODAY` table in `docs/ON-CHAIN-DESIGN.md` was
    re-read against the source at 07:20Z and matches it; `python3 tools/tp.py doc-check` is green at
    07:24Z, `doc_check: clean, 6 check(s), 21 allowed absence(s) suppressed`, exit 0. The Python suite
    was red at 07:22Z mid-edit and green again at 07:31Z and at 07:47Z, `Ran 1058 tests`, `OK (skipped=26)`; at 08:13Z the same command was `Ran 1076 tests`, `OK (skipped=26)` (§A4).
    This pass changed no code, test or tool.
20. **The documentation gate went red at 07:27Z on a file this pass does not own, and cleared at 07:30Z.**
    `programs/cap_hook/README.md:18` now cites `records/findings/37-program-v2-review-fixes.md`, and
    that finding does not exist yet: another agent is writing it. The gate reports two violations
    (one `paths`, one `cross-references`) on that line. The table and every other document this pass
    wrote were clean at 07:24Z, and the red was a dangling reference in a code-owned file, so fixing it
    was the code owner's edit or the finding's arrival. It arrived at 07:30Z: finding 37 is written and
    the gate reads `doc_check: clean, 6 check(s), 21 allowed absence(s) suppressed`, exit 0.

---

# G. REGION-AWARE RESALE CAPS — built and locally verified, 2026-11-08

Declared status, in the closed set this file uses elsewhere:

| part | status | where it is | what proves it |
|---|---|---|---|
| the rules table | **built** | `ticketpath/data/region-caps.json` (version `2026-11-08.1`, 82 codes, 84 instruments) | `tests/test_region_caps_table.py` (29 tests, corrected 08:25Z from 25) **[corrected 2026-11-08T12:00Z: 30 tests, `Ran 30 tests in 0.031s`, `OK`]** |
| the resolver | **built, tested** | `ticketpath/core/region_caps.py` | `tests/test_region_caps.py` (54 tests) **[corrected 2026-11-08T12:00Z: 57 tests, `Ran 57 tests in 0.008s`, `OK`]** |
| the event field and the additive wire keys | **built, tested** | `ticketpath/core/event_records.py`; declared in `tests/test_contract_conformance.py` | `tests/test_event_jurisdiction.py` (11 tests, corrected 08:25Z from 10; **corrected again 2026-11-08T09:22Z: 12 tests, `Ran 12 tests in 0.204s`, `OK`**) |
| the harness adapter | **built, tested** | `tools/region_harness.py` | `tests/test_region_harness.py` (14 tests), including the swarm's own loader accepting the resolved file |
| the on-chain policy layer | **built, tested on a local validator** | `programs/region_gate/` (separate crate; the devnet program is untouched) | `tools/region_local_proof.py`, **PASS 11/11**, 11 real transactions, `records/findings/34-region-caps-build.md` |
| the legal basis | **written, primary sources** | `records/findings/33-a-region-cap-law.md` + five cluster records | per-row instrument, quote, dates and grade |
| most of the world | **unverified** | `unresolved` in the table | nothing read; the row says which wall stopped it |
| the EU member states (FR, IT, ES, BE, PT, and nine more) | **unverified** | `unknown` rows | the national gazettes are JS shells or bot walls; a retry was dispatched, its result belongs in a later version |

**The one-line reading.** The feature is built end to end and verified on a local validator with real
transactions; the legal table is honest about what was read (Ireland, Ontario, Quebec, BC, NSW, SA,
WA, VIC, the UK, the US federal rules, CA, FL, MA, NY's text) and about what was not (everything
else, marked unresolved).

**Three claims this section explicitly does not make.**

1. It does not claim the devnet deployment enforces a region. The devnet program `5EJ1GU3M4vn…` is
   the v1 cap check; `programs/region_gate/` is local-only. The README says which program is which
   and `records/findings/34` says so again.
2. It does not claim the table is complete or current. Every row is stamped with the date it was
   retrieved, and a row whose instrument changed after that date is stale until it is re-read.
3. It does not claim the fixture demonstrates the feature. The synthetic store's events now carry
   `jurisdiction: CA-ON` (every venue in it is an invented Ontario city), so the additive keys are
   populated on every fixture event and Ontario's 2026 cap is stricter than the fixture's own +25%
   organiser cap. That is a demonstration of the code path on synthetic data, not evidence about any
   market, and the store's own label still says so on every payload.

**Collision record.** While this feature was being built, another agent in this tree was
implementing the ten-feature plan's program v2 inside `programs/cap_hook/`, and it moved this
feature's files into `tmp/abandoned-region-caps/` at 05:52Z. They were restored, nothing was lost,
and the resolution is recorded in `records/REGION-CAPS-DESIGN.md` §12. The overlap is feature 10
(`jurisdiction` + `policy`, which v2 already carries) and error numbers (v2 owns 6021-6028, so this
crate's four codes are 6040-6043). No file that agent was writing was edited by this pass.

**Test inventory measured at 06:20Z.** The four new modules are 101 tests
(54 + 23 + 10 + 14). The full suite is **not green**, and the failures are not this feature's: at
06:17Z `python3 -m unittest discover -s tests -q` reported 834 tests with 148 failures and 3 errors,
all in `test_guidance_api`, `test_labels` and the console tests, against files
`ticketpath/api/guidance.py` and `ticketpath/console/page.py` that had been written two minutes
earlier by the concurrent ten-feature build. This pass did not touch those files, and the four new
modules pass on their own.

**[Corrected 2026-11-08T12:00Z, at `HEAD 3ad15bb`. The 06:20Z inventory above is wrong in its
terms, and the same section's table states a different set for the same four modules. This
is the disagreement the claim matrix already carried as C15, "the region test counts disagree three
ways". Measured now, one command per module: `python3 -m unittest tests.test_region_caps_table` →
`Ran 30 tests`; `python3 -m unittest tests.test_region_caps` → `Ran 57 tests`;
`python3 -m unittest tests.test_event_jurisdiction` → `Ran 12 tests`;
`python3 -m unittest tests.test_region_harness` → `Ran 14 tests`. All four `OK`, and the four together
are **113 tests (30 + 57 + 12 + 14)**. The 101 above is 54 + 23 + 10 + 14: the sum is right and the
terms are not, because the table in the same section gives 29 and 54 for the first two modules, so the
section had stated three sets of numbers for four files. The 23 is the one term no row of that table
carries in either its 08:25Z or its 09:22Z reading, and this pass cannot recover what it was measured
on. The 113 is the reading to quote, and the command is the thing to run rather than the number.]**

**Five things the operator may want to decide**, all of them named in `D11`'s open list: whether a
mid-event tightening binds tickets already sold; whether the platform may be stricter than the law
(it can, and the record says which rule bound); which jurisdiction governs a cross-border resale;
whether `programs/region_gate/` is retired once v2 carries `policy = 2` and `TightenPolicy`; and
whether to buy the fee data that Ontario, Queensland and NSW caps need to be applied at their real
base rather than the stricter fallback.

## A10. The frontend, now in this tree

| | Count | Where |
|---|---|---|
| routes | 15 `page.tsx` | `frontend/app/` |
| client components | 5, all for the wallet or a form | `frontend/app/**/*Client.tsx` |
| components | 12 `.tsx` (eleven named components and `ui.tsx`) plus `useMeasure.ts` | `frontend/components/` |
| library modules | 13, of them 4 test modules | `frontend/lib/` |
| bundled fixtures | 4 JSON files | `frontend/lib/mock/` |
| its own tools | 4: build-copy, greps, contrast, headless render check | `frontend/tools/` |
| documents | 6: README, NOTES, VERIFY, DECISIONS, COVERAGE, API_CONTRACT | `frontend/` |

**Re-counted 2026-11-08T11:30Z, on the merged tree: every row above still holds, and the file total
has moved by one.** `git ls-files frontend | wc -l` → **82** and `git ls-files frontend | xargs -d
'\n' du -cb | tail -1` → **1,097,690 total**, where this section and the §A1 row said 81 files and
1,097,001 bytes. The difference is `frontend/.env.example`, 689 bytes, which the import deliberately
left out and which another pass staged at 11:18Z; it carries four `NEXT_PUBLIC_*` variable names with
empty values and no secret. The per-directory counts above were re-read at the same time and are
unchanged: 15 `page.tsx`, 5 `*Client.tsx`, 12 `.tsx` plus `useMeasure.ts`, 13 `lib/*.ts` of which 4
are tests, 4 mock JSON files, 4 tools, 6 documents. This changes no check result in this section.

**What it is.** The product surface: an attendee's landing, browse, event, ticket, holdings, door and
resale screens, an organizer's dashboard and create form, wallet verification, the backend's own
health as `/pricing`, and the cap rules as `/rules`. One data seam (`frontend/lib/api.ts`), no
component that fetches, seven capabilities false in `frontend/lib/capabilities.ts` and each rendering
a panel that names the missing endpoint rather than a mock success. `README.md`'s *The frontend*
section says how to run it and which four `NEXT_PUBLIC_*` variables it reads.

**What its checks printed from the new path, measured 2026-11-08.** In a copy under the system temp
dir with `node_modules` symlinked to the builder's install, so nothing was installed into this tree:

| Command | Result |
|---|---|
| `npm run typecheck` | exit 0 |
| `npm run lint` | exit 0, no warnings |
| `npm test` | `tests 15, pass 15, fail 0, cancelled 0, skipped 0`, `duration_ms 180.747` |
| `bash tools/greps.sh` | every forbidden-string count 0 → `8.5 GREPS: ALL ZERO` |
| `node tools/contrast.mjs` | `28 pairs, 0 below 4.5:1` |

**Not run here, and named rather than implied.** `npm run build`, because a build replaces a bundle
and takes minutes and `frontend/tools/build-copy.sh` exists to put it somewhere that is not this
checkout; and `frontend/tools/verify-landing.cjs`, which needs a browser and a served copy. Both were
run by the builder in its own checkout and `frontend/VERIFY.md` holds those numbers. Nothing in this
section is a re-measurement of them.

**What the import changed besides adding a directory.** Four machine handles in the app's tooling and
documents were replaced: absolute paths under a home directory and the port another session's dev
server holds. `.public-denylist` gained one line, `allow frontend/*.md tmp-path`, because two of the
app's documents quote the `/tmp` paths their own run wrote and a quote of a scratch path is evidence;
`tests/test_public_safety.py` proves the line is markdown wide and does not reach the app's code.
`tools/doc_check.py` gained `frontend` in its top-level set and a fallback that resolves a path
against the naming document's own directory, because eleven true references like
`tools/build-copy.sh` in a frontend document were being reported missing. The whole list is in
`records/F-decision-log.md` D19 and, for a reader of the app, in `frontend/NOTES.md`.

---

*Nothing committed or pushed by the 03:30Z pass this file measures, and nothing committed or pushed by the 2026-11-08 frontend import until 11:41Z, when the import was committed as `009f103`; nothing at all has been pushed. Nothing here was written by a build.* No code touched by the documentation edit. The
six document files this pass edited each carry a dated note saying what changed.*

## Appended 2026-11-08T09:15Z: feature 5's status moved, and the table above is not rewritten

Row 5 of the feature table says the artist fee is **not built, blocked** by the measured Token-2022
ceiling. The ceiling holds and the mint's transfer fee still ships switched off — but the *fee* now
exists by the other mechanism, so the row is stale in the direction that matters to a reader: it reads
as "there is no artist fee", and there is one at the checkout as of this pass.

- **Built and measured**: a seller-paid lamport fee inside the sale transaction
  (`records/findings/42-artist-fee-at-checkout.md`, decision `D26`,
  `docs/ON-CHAIN-DESIGN.md` §15). Nine legs on a throw-away local validator, PASS 9/9:
  the fee is paid exactly, an underfunded seller fails the sale whole, an over-cap sale is refused
  `6010` and pays nothing, the rounding boundary pays 0 and 1 where the arithmetic says, a 100% fee
  equals the price, and a staged 0 is refused `6009`.
- **Not enforced by the chain**, stated in every one of those documents and measured as leg 8: a
  staging is consumed by whoever moves the ticket next, so a transfer that skips the fee is admitted
  and the artist is paid nothing. No screen, README or row may say the chain charges this fee.
- **Feature 7 (the flip tax)** ships its **charging half** and not its pool half, and this bullet
  said it was not built at all until this pass. The tax is a second seller-paid lamport leg in the
  same sale transaction as the artist fee, priced off the hold clock the hook writes into the record
  (`held_since_unix`), 15% under an hour falling to 0 at 30 days by default, per-event and off
  unless an event turns it on: `records/findings/43-flip-tax-at-checkout.md`, decision `D27`,
  `docs/ON-CHAIN-DESIGN.md` §16. **Not built:** the refund-to-holders pool (`ClaimRebate`, tag 7,
  is not implemented), and the chain does not enforce the tax, exactly as it does not enforce the
  fee.
- **The harness options** (`market_swarm`) are off unless an event names them: `artist_fee` turns on
  the fee, and `flip_tax` with `"enabled": true` turns on the tax and, with it, the v2 record shape
  every sale of that event uses. `plan` prints the state of both. Their live paths are unit-tested and
  their transaction bytes are pinned, and neither is **verified through the harness on a cluster** —
  the validator measured the same instruction set built by the two proof tools. Finding 42 §8 also
  names the stale v1-shaped no-fee path in `market_swarm/gateway.py` that is another run's to repair.

The counts in this file's later sections were measured before this change and are not updated here;
the suites that include this work run green at 535 tests in `market_swarm/tests` and 1,166 in `tests/`,
run by the orchestrator of this pass, and a reader should re-measure rather than quote that sentence.

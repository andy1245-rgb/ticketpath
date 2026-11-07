# 13 — Submission readiness: every claim a judge could test, checked at HEAD

**Written:** 2026-11-07T17:31Z by an independent checker that did not write the pack.
**Scope:** `records/SUBMISSION-PACK.md`, `README.md`, `docs/ON-CHAIN-DESIGN.md`, and the tree at
HEAD `375126f`. **Read-only throughout.** Nothing was committed, pushed, or edited. The only write
is this file.
**Deadline it is written against:** initial submission Sun 2026-11-08 **15:00Z**.

**What I could not measure, and did not fake.** `:3000`, `:3001`, `:8787` and `:8788` are
off limits to this check, so every claim that only the served frontend can settle is marked
**ASSERTED** below and I say so where it appears. I read the frontend copy on disk
(`../ticketpath-demo`) instead, which settles the source-level half of those claims and not the
served half. The repository was read with `git ls-remote` only; no fetch, no push.

---

## 0. The surface, measured

| Thing | State at HEAD | How |
|---|---|---|
| HEAD | `375126fba2cb0462151a96e1951770d917b0cd19`, 2026-11-07 17:25:26 +0000, "Make the decision-mode sentences true at the printed instant (audit property d: 60 -> 0)" | `git log -1` |
| Working tree | one modified file, `NIGHT-LOG.md`; nothing untracked before this file was written | `git status --short` |
| Files at HEAD | 148 tracked | `git ls-tree -r --name-only HEAD \| wc -l` |
| Remote `main` | `ecfae2ee987f142360d3422af98079f8c29141e2`, **one commit behind HEAD**, 147 tracked files | `git ls-remote origin` |
| Remote, other refs | `refs/heads/wip/mode-sentences-20261107T1650Z` = `8ea1863` | `git ls-remote origin` |
| Commit gap | 10 files: `tests/test_decision_mode_states.py` added, 9 modified | `git diff --name-status ecfae2e HEAD` |
| Backend on a spare port | binds, logs `ticketpath 0.1.0 listening on http://127.0.0.1:8798 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10` | `TICKETPATH_PORT=8798 python3 -m ticketpath.server` |
| Test suite | **`Ran 453 tests in 17.937s` / `OK`** | `python3 -m unittest discover -s tests` |
| Test modules | 32 `tests/test_*.py`, plus `store_arithmetic.py` and `__init__.py` (34 `.py`) | `ls tests/test_*.py \| wc -l` |
| Store | 8 events, 76 tickets, 147 ledger rows, 61 priced sales, `matches a fresh build exactly` | `curl /api/events?limit=100`, `tools/build_fixture_store.py --check` |
| `evt_syn_02` analytics | `saleCount 12`, `avgMarkupBps 1233`, `totalVolumeLamports 22026000000`, `medianResalePriceLamports 1380000000`, `uniqueHolders 11` | `curl /api/events/evt_syn_02/analytics` |
| Resale share, the five events with resales | 62.5%, 66.7%, 72.7%, 76.9%, 62.5% (range 62% to 77%) | per-event analytics |
| Console `/` | 200, 13,726 bytes | `curl -o /dev/null` |
| Route table | 10 routes, 9 of them contract routes | `ticketpath/server.py:117` |
| `LICENSE` | MIT, `Copyright (c) 2026 Andrew Radu` | `head -3 LICENSE` |
| Toolchain | `which solana anchor cargo rustc spl-token` exits 1 | measured |
| Browser | none of chromium, chromium-browser, google-chrome, firefox, playwright; no `~/.cache/ms-playwright` | `which`, `ls` |
| Devnet, read by hand | `getVersion` → `solana-core 4.4.0`; Token-2022 `TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` → `executable: true`, owner `BPFLoaderUpgradeab1e11111111111111111111111`, slot 519735045 | two `curl` POSTs to `api.devnet.solana.com` |
| Outbound network in the shipped package | **none.** No `socket`, `urllib.request`, `http.client` or `requests` imported anywhere under `ticketpath/`. The only `urllib.request` in the repo is in `tools/console-check*.py`, and it calls `127.0.0.1` | `grep -rn` over `ticketpath/`, `tools/` |

---

## 1. MEASURED against ASSERTED

**MEASURED in this pass** (re-runnable by the operator or a judge):
the test counts, the listening line, `/health`'s full body, 8 events and 76 tickets, the
`evt_syn_02` analytics figures, the fixture re-build, the console page's strings and tags, the word
count of all six spoken beats, the route count, `LICENSE`, the absent toolchain, the absent browser,
the devnet `getVersion` and Token-2022 account, the remote `main` sha and its file list, and the
fact that nothing under `ticketpath/` opens a socket.

**ASSERTED, and untestable from here** (do not present these as verified):
that `:3001` is the patched copy serving backend numbers and not mock data (I confirmed the patch is
present in the source of `../ticketpath-demo` and wired into all four screens, but the served HTML is
off limits to this check, and `../ticketpath-demo/.env` has `NEXT_PUBLIC_API_BASE_URL=` **empty**, so
whatever is on `:3001` was started with the variable set inline and would lose it on a plain
restart); that the console's numbers are stable across two `asOf` values an hour apart; that the
hackathon's official name is "MLH Solana Hackathon" (sourced in
`records/findings/02-rubric-and-scoring.md`, not re-sourced here); that `Node 24` is what runs the
frontend; that the recorded video will land under 2:00.

---

## 2. The findings, ranked by how likely a judge hits it

Rank is not severity. It is the order in which a tired judge moving from the form, to the video, to
the repo, to the README will meet the sentence. Every quote is verbatim and every line number is the
line at HEAD.

### 1. The paste-ready "what is not done" text contradicts the video. HIGH.

`records/SUBMISSION-PACK.md:390-392` (§2.5, item three of five):

> Third, the decision surface does not exist yet: there is no page that shows a recommended price, the
> backend registers no pricing model, and the honest output of the pricing work today is a written
> specification and a refusal, not a number.

The console at `/` prints `Recommended primary price: at least 1.38 SOL per ticket, General tier.`
under an `[UNVALIDATED]` badge, and `/health` reports `pricingModel.available: true`,
`modelVersion: engine-2026-11-07`, `kind: rule-based-bounded-estimator`. Measured, both.

A judge who watches the video and then reads this paragraph has caught the submission in a
self-contradiction about its own central surface. This sentence is the single most damaging one left,
because §3 item 9 says to paste §2.5 **verbatim**.

**Replace with:**

> Third, the pricing engine is unvalidated. A console page served at `/` prints a recommended primary
> price for the selected event, and that number is a bound with a declared width computed from the
> fixture's own resale rows: no parameter was estimated from real data, `/health` reports
> `fitted: false`, and the page tags the recommendation `[UNVALIDATED]`.

### 2. The answer to "what does the engine output" is still the pre-console answer. HIGH.

`records/SUBMISSION-PACK.md:605-606` (§5, answer 9):

> **What does the pricing engine output today?** Nothing: `/health` reports `pricingModel.available:
> false` with the reason `no_model_registered`, and no endpoint serves a price.

Same reason as above: §5 is the list a judge's questions get answered from, and this answer is the
opposite of the running build.

**Replace with:**

> **What does the pricing engine output today?** A floor, not an estimate. The console served at `/`
> prints a recommended primary price for the selected event (at least 1.38 SOL per ticket on the
> default event, tagged `[UNVALIDATED]`), `/health` reports `pricingModel.available: true`,
> `modelVersion: engine-2026-11-07`, `kind: rule-based-bounded-estimator`, `fitted: false`, and the
> engine still refuses an upper bound, a sale probability and an interior optimum, naming the missing
> observation for each.

### 3. Every test count in the pack is wrong, and they are wrong in five places. HIGH.

Measured: **453 tests, `OK`**. The pack carries 149 at five sites and 306 in its own correction note:

- `:29` (§0 table) `→ **149 tests, OK**`
- `:332` (§2.2, the description a judge reads) `on a 149-test suite that passes`
- `:412` (§2.6 Built with) `a 149-test unittest suite`
- `:448` (§3 item 10) `accomplished: 149 tests, real signature verification, …`
- `:602` (§5 answer 7) `on 149 passing tests`
- `:647` (snapshot note) `293 tests when this pass began and 306 when it ended`

The suite also printed 306 at 12:12Z per `README.md:74`, so it has moved again since. A judge who
runs the one command the README gives gets 453 and sees the submission say 149. That reads as
careless, and it is the cheapest thing on this list to fix.

**Replace with** a number measured against the exact tree that is pushed, and name the command
beside it, so the two cannot drift:

> on a 453-test suite that passes (`python3 -m unittest discover -s tests`, `Ran 453 tests`, `OK`)

Correction note for `:647`: `306 at 12:12Z; 453 at HEAD 375126f`.

### 4. "Solana JSON-RPC over HTTPS, devnet, read only" is a technology the build does not use. HIGH.

`records/SUBMISSION-PACK.md:409` (§2.6 Built with). Nothing under `ticketpath/` imports a network
module. `ticketpath/adapters/rpc_adapter.py` opens with `It never opens a socket`, `/health` reports
`rpcEnabled: false` with `reason: rpc_disabled`, and `ticketpath/adapters/chain_client.py` says it
`imports no network module`. The devnet reads quoted in §2.4 were the operator's own `curl`, from a
shell, by hand. So the entry lists as a building block something the running product never touches.

This is the line that a judge asking the event's own materials question ("does the app read state
back?") will hold against the entry. What is true is that there is a **disabled read adapter**, not a
read.

**Replace with:**

> - No Solana RPC in the running build: the chain adapter is off by default and opens no socket
>   (`/health` reports `rpcEnabled: false`, `reason: rpc_disabled`). The devnet reads in §2.4 were
>   made by hand with `curl` from the build machine, are recorded there, and are not performed by the
>   app.

### 5. The technical description omits the only surface the video shows. HIGH.

`records/SUBMISSION-PACK.md:363` (§2.3) marks an append **VERSION-IF-CONSOLE-LANDS**, and the console
landed. As the pack stands, the field-8 "how it works" text in §2.3 never mentions the console, while
§1.2 beat 3 puts it on camera for 21 seconds. A judge reading the description cannot find the screen
he was shown.

**Fix:** the replacement paragraph is already written, at `:365-367`. Apply it to §2.3 as-is, and add
the two details the video shows and that paragraph leaves out, so the description and the frame agree:

> The second surface is a server-rendered console at `/`, served by the same Python backend: it states
> the recommended primary price for a selected event and tier, shows the evidence counts the answer
> rests on, prints a `[UNVALIDATED]` badge on the recommendation and a `[REFUSED]` block naming each
> question the record cannot answer.

### 6. The README's test count, on the repo front page, is wrong. HIGH for a judge who opens the repo.

`README.md:74-76`:

> Observed at 12:12Z: `Ran 306 tests` in 9.5 seconds, `OK`. It was 293 twenty minutes earlier
> and 306 by the end of this pass, …

Measured 453 in 17.9 s. The README's own hedge ("the command's own output is the number that matters")
is good practice and does not save the number.

**Replace with:** `Observed at 17:5xZ: `Ran 453 tests` in 17.9 seconds, `OK`. The count moves as the
backend grows, so the command's own output is the number that matters, not this line.`

### 7. The pack's headline blocker is stale, and it is stale in the alarming direction. MEDIUM-HIGH.

`records/SUBMISSION-PACK.md:33` (§0 table):

> Remote vs local | remote `main` = `e55a18b` (pushed 10:27Z); local HEAD = `3bece48` **plus
> uncommitted changes**. The public repo does **not** contain the backend, the fixture store or any
> Phase 2 record

Same claim at `:441` (`content not pushed: see T1`), `:462` (T1), `:630-631` (§6), and it is repeated
as the pack's `T1 blocks submission outright`. Measured: remote `main` is `ecfae2e`, **one commit**
behind HEAD, and it carries 41 files under `ticketpath/`, plus `README.md`, `LICENSE`,
`fixtures/synthetic_store.json`, `docs/ON-CHAIN-DESIGN.md` and the research records. `T1` is now a
one-commit push of 10 changed files, not an upload of the tree.

This one is dangerous in both directions: an operator reading it believes the submitted link shows no
code (so he may over-correct, or lose an hour), and it hides the one real repo risk left, which is
that the pushed tree is one commit behind what he verified.

**Replace the `:33` row with:**

> | Remote vs local | remote `main` = `ecfae2e` (2026-11-07, before the decision-mode commit); local HEAD
> = `375126f`, one commit ahead, plus an uncommitted `NIGHT-LOG.md`. The public repo already carries
> the backend (41 files under `ticketpath/`), `README.md`, `LICENSE`, the fixture store and
> `docs/ON-CHAIN-DESIGN.md`. `T1` is a one-commit push, and `NIGHT-LOG.md` stays out of it. |

and `:630` (§6) with: `The repo is public and its main is one commit behind the verified tree: 10
files, one of them a new test module. That commit is the whole of T1.`

**Also:** `refs/heads/wip/mode-sentences-20261107T1650Z` is visible to anyone who clicks "branches".
Either delete it or accept that a judge reads a branch named after an unfinished sentence fix.

### 8. T1 and the licence are described as open decisions that are closed. MEDIUM.

- `:455` (§3 item 17) `repo is public with `license: None` on GitHub. Pick one, add `LICENSE``
- `:32` (§0) `GitHub reports `license: None``
- `:648` (snapshot note) `Both exist: `README.md` and `LICENSE` (MIT, copyright line still a bracketed
  placeholder for the operator)`

Measured: `LICENSE` exists **on remote `main`** and reads `Copyright (c) 2026 Andrew Radu`. The
bracket is filled. `T6` is closed, and §3 item 17 now asks for work that is done.

**Replace `:455` with:** `MIT, in `LICENSE`, copyright line filled. Nothing to decide; confirm the
name is the one he wants on a public repo.`

**Replace `:648`'s licence clause with:** `(MIT, copyright line reads "Andrew Radu")`.

### 9. `README.md:214-218` tells a judge the licence names no holder when it does. MEDIUM.

> MIT. The text is in `LICENSE`, and **the copyright line is a placeholder that the operator
> must fill in.** It reads, in full:
>
> ```
> Copyright (c) 2026 [OPERATOR: replace this bracket with your name]
> ```

`LICENSE` line 3 reads `Copyright (c) 2026 Andrew Radu`. This is the README contradicting a file in
the same repo, on the page a judge reads first, and it also prints a bracket string that no longer
exists anywhere. It is a two-line fix and it is the sort of thing that reads as sloppy rather than
dishonest, which is the cheaper of the two failures but still a failure.

**Replace `:214-219` with:**

> MIT. The text is in `LICENSE`, and the copyright line names the holder:
> `Copyright (c) 2026 Andrew Radu`.

### 10. The snapshot note claims a cleanup its own command disproves. MEDIUM.

`records/SUBMISSION-PACK.md:651` (snapshot note, last row):

> Done in this pass: `records/`, `docs/`, `tests/` and `tools/` now carry repo-relative paths only,
> `../ticketing-frontend` for the sibling checkout. `NIGHT-*.md` are untouched by instruction |
> `grep -rn "hom[e]/" README.md records docs tests tools ticketpath` → no hits outside `NIGHT-*.md`

Measured: that command returns **24 hits** outside `NIGHT-*.md`, including four in
`docs/morning.html` (`cd /home/friend/ticketPricing`), four in `records/DELIVERABLE.md` and three in
`records/FINAL-PROOF-2.md`. Personal home paths are in the public tree, which is the operator's own
rule against personal paths in a repo, and the pack says they were removed.

**Replace with:** `Not done: 24 hits remain outside `NIGHT-*.md` (`docs/morning.html`, `records/
DELIVERABLE.md`, `records/FINAL-PROOF-2.md`, and the rest of `records/`). Recorded here as an open
item rather than fixed, because the operator asked for the pack, not the tree.`

### 11. Two strings the video script tells him to have on screen are not on the page. MEDIUM (video).

`records/SUBMISSION-PACK.md:163` (§1.2 beat 3):

> The two lines doing the work are `[EXACT] ceiling 1.38 SOL = face 1.20 SOL plus a cap of 15%` and
> `[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General tier.`

Measured on `/`: the `[EXACT]` line reads

> `[EXACT] ceiling 1,380,000,000 lamports = face 1,200,000,000 lamports × (10,000 + 1500) / 10,000 —
> integer arithmetic on the tier face, not an estimate. That is exactly 1.38 SOL.`

There is no `ceiling 1.38 SOL = face 1.20 SOL plus a cap of 15%` anywhere on the page, and the second
line quoted is correct.

`records/SUBMISSION-PACK.md:162` also quotes a badge as `8 events on this platform, 5 with any
resale`. Measured: `[FIXTURE] 8 events in the store, [FIXTURE] 5 with any resale at this instant`.
Different words, and the tags sit between the numbers.

**Replace `:163` with:** `` `[EXACT] ceiling 1,380,000,000 lamports = face 1,200,000,000 lamports ×
(10,000 + 1500) / 10,000` and `[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket,
General tier.` ``

**Replace `:162` with:** `` `8 events in the store`, `5 with any resale at this instant` ``

### 12. Beat 3 does not mention the block that now sits in the middle of its frame. MEDIUM (video).

Between the `[UNVALIDATED] The decision` badge and the event line the console now prints, measured
verbatim on `/`:

> `[UNVALIDATED] Decision mode: COUNTERFACTUAL. This page recomputes the value from this event's own
> record as it stands at this decision instant. The event has not ended at this instant, so the record
> read here is the record up to this instant and not a finished one: this page is not hindsight, it is
> what the record in hand implies now, and it is not a price you could have set.`

This is the newest sentence on the page (it is what HEAD's commit made true), it appears in the first
three seconds of the beat, and the script says nothing about it. Unscripted, it is either dead air or
a caveat that lands before the number it qualifies.

**Add to `:158-160`:** `Between the decision badge and the event line the page prints a
[UNVALIDATED] Decision mode: COUNTERFACTUAL block ending "it is not a price you could have set". It
is three lines above the number: keep it in frame, do not read it aloud, and do not scroll it half
off.`

### 13. `README.md`'s own inventory of the repo is stale in three places, one of them trivial. LOW-MEDIUM.

- `README.md:201` `tests/ unittest tests over 24 test modules, plus store_arithmetic.py` — measured 32
  `test_*.py`.
- `README.md:186` `findings/ seventeen per investigation reports` — measured 24 files in
  `records/findings/`.
- `README.md:39` `Observed 200, and a page of about 12 KB` — measured 13,726 bytes. The README already
  says the byte count moves, so this one is only worth fixing if the line is being touched anyway.

**Replace:** `32 test modules` and `twenty-four per investigation reports`. Same sentence also does
not list `records/FINAL-PROOF.md`, `records/FINAL-PROOF-2.md`, `records/BUILD-REPORT-CONSOLE.md` or
`records/NIGHT-CONTINUE.md`, which exist; the index claims to be "one line per record file".

### 14. The pack's own verification checks would fail as written, and one failure is a false alarm. LOW-MEDIUM.

`records/SUBMISSION-PACK.md:519` (§4 item 5) passes only if `no signature appears anywhere`. Measured:
`records/00-prior-direction-index.md:169` quotes
`J8hNmBD7PCuVvNNxL4HSjj3LV9QHwkaUgfseZhRGdjbe`, which is a devnet transaction signature from an
earlier spike in this corpus (I resolved it against devnet: `getTransaction` returns `Invalid param:
WrongSize`, consistent with the design doc's own note that those mints and signatures now return
null). It is a citation of prior work, not a claim of this project's deployment, so the honest fix is
to widen the pass condition, not to delete the record.

**Amend the pass condition to:** `every occurrence is a negation or a design label ("no program is
deployed", "designed, not deployed"), no address is presented as ours, and the one signature in the
tree (`records/00-prior-direction-index.md`, an earlier spike, resolved as null) is cited as prior
work and not as this project's.`

### 15. `§0`'s state table is false in four rows, and the snapshot note covers only three of them. LOW.

Rows at `:26` (console `does not exist`), `:27` (price served `none`), `:30` (`Root README | missing`),
`:31` (`LICENSE | missing`). The 12:14Z snapshot note corrects all four, and the pack is honest that it
is a snapshot. Left as-is it is defensible for a record. But §4's checklist is what he will actually
run in the last hour, and §4 item 3 still begins `There is no root README. Write it,` and item 4 still
begins `Add LICENSE` — both are done, and an operator following them will look for work that is not
there while the real work (the video) is not started. Strike items 3 and 4 to one line each:
`Verified: README exists, satisfies this pass condition (measured at 8798).` / `Verified: LICENSE is
MIT with the holder filled in.`

### 16. `§4 item 9`'s paste-time correction is itself out of date. LOW-MEDIUM.

`records/SUBMISSION-PACK.md:563-566` says §2.2 still ends `no price is served: the backend reports
pricingModel.available: false`, and that it needs the VERSION-IF-CONSOLE-LANDS replacement. §2.2 was
rewritten at 15:10Z and no longer contains that sentence. The instruction now sends him to fix a
sentence that is gone, and it does not tell him the three that are still wrong (§2.5 item three, §5
answers 5 and 9, and §2.3's missing append). Point item 9 at findings 1, 2 and 5 of this file instead.

---

## 3. What is true, measured, and must not be "fixed"

Listing this because the fastest way to break the entry now is to over-correct. Every line below was
measured in this pass and is honest as written.

- **The on-chain story.** `docs/ON-CHAIN-DESIGN.md` is the strongest thing in the repo. It opens with
  `Status: design only. No program is deployed. No address in this document is invented, and no test
  result is claimed`, and §10 lists fourteen claims it cannot verify from this machine with the step
  that would settle each. `docs/ON-CHAIN-FOR-LAPTOP.md` is correctly marked `SUPERSEDED` and names the
  old blob so nothing was lost. Do not touch either.
- **`§2.4 What is on-chain`** (`:371-382`) is accurate, including `Nothing. No program, no mint, no
  transaction, no address, and no signature to show or explorer link to follow.` The devnet read it
  quotes re-measures today: `solana-core 4.4.0`, Token-2022 `executable: true`. The slot has moved
  (519735045 now against 519647005 quoted); the claim is a point-in-time measurement and stays true.
- **`/health`** matches the pack's `§4` item 7 pass condition field for field: `available: true`,
  `modelVersion: engine-2026-11-07`, `kind: rule-based-bounded-estimator`, `fitted: false`,
  `programDeployed: false`, `programId: null`, `designDoc: docs/ON-CHAIN-DESIGN.md`,
  `dataSource.synthetic: true`.
- **The console's labels.** `§4` item 6's console check passes: `SYNTHETIC FIXTURE DATA` is the first
  element, `[UNVALIDATED]` present, `Recommended primary price: at least 1.38 SOL per ticket` present.
  All eight tags the pack names (`[FIXTURE] [EXACT] [UNVALIDATED] [REFUSED] [DECLARED] [DESIGN]
  [SIMULATED] [DEVNET]`) are on the page.
- **Every number the script speaks** is on a page: 12 sales, 22.026 SOL, 1233 bps, 1.38 SOL, 1.20 SOL
  face, 8 of 9 at the ceiling, 88.9%. The beat-5 custody trail is real: `tkt_syn_0001` is issue, sale
  1.18 SOL +18%, an **unpriced** transfer at `2026-10-12T02:00:00.000Z`, sale 0.94 SOL −6.0%, and every
  ledger row carries `signature: null` and `slot: null`.
- **The word count.** All six beats sum to exactly **264** words (51/46/49/36/47/35), which is 113.1 s
  at 140 wpm and 118.1 s with the five beats: 1:58 against a 2:00 cap. `§6`'s count is right.
- **The labels on the demo copy are in the source**: `components/SyntheticNotice.tsx` renders the
  backend's own `dataSource.label`, it is wired into all four screens the pack names, and the strings
  `Resale analytics`, `On-chain (simulated)` and `Not enforced — no program is deployed` all exist in
  `../ticketpath-demo`.
- **`README.md`'s own run steps all work as printed**: the listening line, `TICKETPATH_PORT`
  override, the 8787 refusal (`refusing to bind port 8787: the fleet page owns 127.0.0.1:8787`), 200 on
  `/`, 8 events, 76 tickets, 147 ledger rows, 61 priced sales, `matches a fresh build exactly`, and
  `?sim=1` returning exactly five `[SIMULATED]` arms including `6010 E_CAP_EXCEEDED` and
  `6009 E_TRANSFER_NOT_STAGED`.
- **`§2.7`'s AI disclosure obligation and the `TBD-TOOL-NAMES` placeholder** are correctly left to
  him. Nothing about that can be filled in from here.

---

## 4. The event's four-part materials test, applied

The criterion is one sentence on the event page, quoted at
`records/findings/02-rubric-and-scoring.md:34`, and the finding reads it as four things a judge looks
for (`:37-38, :358-360`). Scored against this tree:

| test | what exists | verdict |
|---|---|---|
| an account that belongs to the project | `chain.programId: null`; every mint is a `SYN*` placeholder that no cluster resolves (`getAccountInfo` on the frontend's own placeholder returns `Invalid param: WrongSize`) | **absent** |
| a transaction signature, with a block time | none. Every ledger row is `signature: null`, `slot: null`. `records/findings/02-rubric-and-scoring.md:90` names this as the one thing worth buying | **absent** |
| a program the team did not write, doing work the product depends on | none invoked. Token-2022 is proven to exist on devnet (`executable: true`) and nothing in the product calls it. `ticketpath/onchain/sim.py` is a Python mirror, labelled `[SIMULATED]` | **absent** |
| the app reading that state back | nothing. `ticketpath/adapters/rpc_adapter.py` never opens a socket; `chain_client.py` imports no network module; no module under `ticketpath/` imports a network client at all | **absent** |

So the entry fails all four, and **the pack is right to say so**: `§2.4` opens with `Nothing.`, `§5`
answer 3 explains why, and the console prints `No program is deployed on any cluster. Nothing on this
page is a deployed guarantee.` What is wrong is narrower and specific:

1. `§2.6`'s `Solana JSON-RPC over HTTPS, devnet, read only` (finding 4) is the one sentence that
   implies the fourth test is met in some form. It is not, not even disabled-then-enabled, because
   enabling it would still find nothing.
2. `§3` item 13 (`:451`) says `The criterion is one sentence about Solana being load-bearing, and the
   honest answer is "designed, not deployed"`. That under-states it. The honest answer is that the
   repo has none of the four things the criterion is applied by looking for, so **Top 3 Overall is
   unlikely on the chain criterion** and the entry's realistic path is MLH's own four-part rubric
   (Technology, Design, Completion, Learning), where `records/findings/02-rubric-and-scoring.md:41-42`
   notes Design is the cheapest quarter and the build had no interface at all. The console is now that
   interface, which is the one thing that has changed in the entry's favour since that finding.
3. Nothing in the pack claims a deploy, a devnet address, a mint, a transaction or a signature for
   this project. I looked for it: `§4` item 5's `no signature appears anywhere` rule holds for this
   project, with the one prior-spike citation described in finding 14. **The pack does not imply a
   deployment anywhere I could find.** That is the thing most likely to have gone wrong in a document
   this size and it did not.

---

## 5. What the operator must still do by hand before 15:00Z

1. Record the video from `§1.2` as amended by findings 11 and 12, under 2:00, "MLH Solana Hackathon" in
   the first spoken sentence, the hackathon name and the repo URL in the end card.
2. Push the one commit (`375126f`) so the public `main` matches the tree he verified; leave the
   uncommitted `NIGHT-LOG.md` out of it, and stop pretending (findings 7) that the repo has no code.
3. Run `python3 -m unittest discover -s tests` on the pushed tree and paste the number it prints into
   the five sites in finding 3 and into `README.md:74`. Do not paste 149, and do not paste 306.
4. Replace `§2.5` item three (finding 1), `§5` answers 5 and 9 (findings 2), `§2.6`'s Solana line
   (finding 4), and append the console paragraph to `§2.3` (finding 5). Those four edits are the whole
   of the paste-ready text.
5. Fill `TBD-TOOL-NAMES` in `§2.7` (`:417`), and put the same list in the form. Naming the wrong tools is worse
   than naming none.
6. Strike `§4` items 3, 4 and 17 as done (README exists, LICENSE is MIT with the holder filled in) so
   the last hour is spent on the two hard gates, the video and the push.
7. Fill the form's team, school, country and code-of-conduct fields (`T4`), leave the devnet
   program/mint/address field **empty**, and leave the demo URL blank or pointing at the repo with one
   plain sentence that it runs locally.
8. Decide `T11` before he starts, not after: with no tunnel and no deploy, the console is seen only in
   the video, and no frame may imply a judge can open it.
9. Fix the two README lines a judge hits on the front page (findings 6 and 9: the test count and the
   licence placeholder), and the inventory counts (finding 13). Nothing else in the README needs
   touching; its run steps all pass.
10. After the submission: capture the confirmation id, freeze the tree, and change nothing until a
    judge asks. If the `wip/mode-sentences-…` branch is still on the remote, delete it before the
    judging window.

**One thing I did not do and would not recommend doing now:** removing the personal home paths of
finding 10. It is a real defect against his own rule, the pack says it was already fixed, and the fix
is a 24-line sweep that touches `records/` and `docs/morning.html` at the exact hour he should be
recording. It is the first thing to do after the submission, and the correction line in the pack
should say it is open rather than done.

# 00: Verification of the research ledger against the files it cites

**Status:** complete. **UTC:** 2026-11-07T10:55Z. **Agent:** ledger verification pass (read-only).
**Scope:** the nine rows of `records/A-research-ledger.md` (P0.1 through P0.5, P1.A, P1.B, P1.C,
P1.D) checked against the file each rests on: `records/00-data-situation.md`,
`records/findings/01-a-market-structure.md`, `records/findings/01-b-identifiability.md`,
`records/findings/01-d-external.md`, `records/README.md`, `records/F-decision-log.md`, and for the
P0 rows the frontend tree at `../ticketing-frontend/`. Citations checked by DOI lookup at
Crossref and by fetching the regulator and register documents the findings quote.
I did not edit the ledger or any finding. Nothing was committed or pushed.

---

## 1. Verdicts

| ID | Ledger says | Verdict | The quote that decides it | Recommended correction |
|---|---|---|---|---|
| **P0.1** | `answered`; "No backend, no DB, no program id anywhere; `API_CONTRACT.md` specifies a backend that does not exist."; class `verified` | **PARTIAL** | Audit: "**None referenced.** No `programId`, `PROGRAM_ID` or `program_id` anywhere **in the frontend tree** (grep over `*.ts|*.tsx|*.md|*.json`, `node_modules` excluded)." And `F` Q2 still reads: "Is any part of the platform live, on devnet or otherwise? (open)". | `answered-partial`: "No backend, database or program id in the frontend tree; `API_CONTRACT.md` specifies a backend that does not exist. Whether a program is deployed elsewhere is unanswered and is F Q2." The word "anywhere" in the current cell claims more than the audit's grep covered. |
| **P0.2** | `answered`; "Synthetic fixtures: no generator, no provenance, mint addresses are not valid pubkeys (devnet RPC `WrongSize`), cap never binds in the generated prices."; class `verified` | **SUPPORTED** | "No script in the tree produces them, no seed, no capture date, no source noted anywhere"; "`getAccountInfo` … returns `{"code":-32602,"message":"Invalid param: WrongSize"}`"; "the maximum markup sits strictly below the event's `resalePriceCapBps` in every event that has a cap, and no sale lands exactly on it". | Keep. Reword the last clause to the audit's own words ("strictly below the cap, no sale lands on it") rather than "cap never binds", which is a paraphrase of a measurement. |
| **P0.3** | `answered`; "The `lib/types.ts` wire contract: ledger rows, ticket metadata, event metadata, derived aggregates. Full audit in `00-data-situation.md`."; class `verified` | **SUPPORTED** | "`lib/types.ts` is the wire contract and is the authority. For one ticket the platform yields: `LedgerEntry[]` … `Ticket` … `Event` … `ResaleStats` / `EventAnalytics`: derived aggregates". | Keep. Independently confirmed on disk: `lib/types.ts` opens "This file is the contract." |
| **P0.4** | `answered`; "Four gaps: no listing exposure (kills sale-hazard identification), policy price ceiling truncating the value distribution, no seat coordinates, no fee/settlement field."; class `verified` | **SUPPORTED** | Section 4 is headed "What the contract does **not** carry — the four gaps": "**Gap 1 — no listing exposure, therefore no sale hazard.**", through "**Gap 4 — no fee, royalty or settlement field.**" | Keep the finding, but the row must carry the open conflict: `01-b` §5.1 disputes the Gap 1 diagnosis on file (see §4 below). `README.md`: "Record conflicts, do not resolve them silently." |
| **P0.5** | `answered`; "No. Every quantitative conclusion is class B, C, SIM or UNVALIDATED. Simulation is admissible only for estimator properties."; class `verified` | **SUPPORTED** | "**No result in this programme can be class A from our own data.** Every quantitative conclusion is class B, C, SIM, or UNVALIDATED." and "Simulation is legitimate, but only for estimator properties." | Keep. |
| **P1.A** | `dispatched`; finding `—`; class `—` | **UNSUPPORTED** | The ledger row says `dispatched`, and the file on disk (24,600 bytes, mtime 08:42:11Z) opens: "**Status:** complete. **Last updated:** 2026-11-07T09:10Z. **Author:** Phase 1 subagent A." | `answered`. One-line finding: "Primary tickets are systematically priced below secondary clearing value, but the prize is small (≈41% markup on the ~5% of tickets that resell, worth 1.4% of primary revenue); secondary prices near the event overwhelmingly fall, and on a capped on-chain ledger the recorded markup is a biased-down lower bound exactly where value is highest." Classes: A for the empirical core, C for the truncation argument, D for the three new mechanisms. |
| **P1.B** | `dispatched`; finding `—`; class `—` | **UNSUPPORTED** | File on disk (34,046 bytes, mtime 08:52:13Z): "**Status:** complete (first pass). **Written:** 2026-11-07T08:55Z. **Author:** Phase 1-B research agent." | `answered-partial` (the file labels itself a first pass). One-line finding: "Of six targets, one is buildable today, two are set-identified with computable bounds and three are not identified; the missing object is the asking price of the risk set, not the at-risk denominator, and four fields per listing convert the sale hazard from unidentifiable to estimable." Classes: C for the identification arguments, B for the demand bracket, A only where cited. |
| **P1.C** | `dispatched`; finding `—`; class `—` | **FILE-ABSENT** | `records/findings/` contains exactly `01-a-market-structure.md`, `01-b-identifiability.md`, `01-d-external.md`. ~~No `01-c*` file exists.~~ **[CORRECTION 2026-11-07T14:00Z, R2-6 — dead: `01-c-methods.md` exists and is complete, 1,558 lines, written 10:57Z–11:09Z. This row was a 10:55Z observation and was true then; the file landed four minutes later. The FILE-ABSENT verdict is history and is now false as a statement about the tree. `A-research-ledger.md` has since recorded P1.C as `answered` from that file.]** | ~~`dispatched` is correct here, and it is the only Phase 1 row for which it is. Record "no deliverable on disk" rather than leaving the row looking like the other three.~~ **[CORRECTION 2026-11-07T14:00Z, R2-6 — dead: `01-c` answered the question, and the ledger row was updated at 12:55Z.]** |
| **P1.D** | `dispatched`; finding `—`; class `—` | **UNSUPPORTED** | File on disk (31,773 bytes, mtime 08:40:17Z): "**Status:** complete for Phase 1 purposes. **Written:** 2026-11-07T09:00Z. **Agent:** `p1-external`." | `answered`. One-line finding: "17 variables admitted with a class and a priority, 11 rejected on licence, mechanism or legal grounds; only Ticketmaster Discovery, a venue capacity table and NOAA weather are worth collecting, and the two highest-value variables (listing depth and seat coordinates) are not in the contract at all." Note the file's own head-line counts do not reconcile with its tables (§2.3 below). |

**Tally:** 4 SUPPORTED, 1 PARTIAL, 3 UNSUPPORTED, 1 FILE-ABSENT (9 rows).

### 1.1 The evidence class on the Phase 0 rows is invented

All five Phase 0 rows carry `verified` in the Class column. `records/README.md` does not contain
that class. It lists A, B, C, D, E, then says:

> "Two further labels appear and are **not** evidence classes: **SIM** … **UNVALIDATED**"

`verified` is absent from the table and from that sentence. Its only occurrences in the records are
prose: the audit's own title, "Phase 0 — Data situation audit (verified)", its table column
"Verified state", and `README.md` line 23, "what data actually exists on this machine, verified
rather than assumed". So the word exists as a description of the audit's method, and the ledger has
promoted it into the evidence-class vocabulary.

This also contradicts the ledger's own header, which says: "Evidence class (A–E, SIM, UNVALIDATED)
is per `records/README.md`". The cells then use a value its header does not admit.

Two honest repairs, pick one and apply it consistently: either label the Phase 0 rows with a class
that exists (P0.2, P0.3 and P0.5 are C, statements true of our own artifact by inspection; P0.1 and
P0.4 likewise C but conditional on the audit being right), or extend `README.md` with an explicit
sixth label, "AUDIT" or similar, defined as "true of our own code and data by direct inspection, says
nothing about ticket markets", and then use it. Leaving it as is means every Phase 0 row carries an
out-of-vocabulary class, which is the exact failure `README.md` marks as mandatory to avoid.

### 1.2 The whole Phase 1 block is stale, and provably so

The ledger's "Last updated" line is `2026-11-07T08:45Z`. The ledger file's mtime is
`2026-11-07 08:27:45`. All three findings files were created after the ledger was written
(`01-d` 08:40:17, `01-a` 08:42:11, `01-b` 08:52:13), and carry in-file stamps later still
(09:00, 09:10, 08:55). So the Phase 1 block was not merely left un-updated after the work landed; it
was written before any of the work existed, and nothing has folded it back in. Three of four Phase 1
questions are answered on disk and the ledger reports none of them.

A second, smaller thing to fix while the rows are being rewritten: the `Agent` column claims a tier
for each dispatch, `forge p1-market` (tier `default`) and `forge p1-ident` (tier `best`). None of the
three findings states a tier or a run id, so the tier claim cannot be checked against the deliverable.
It may be right; it is not evidence in the records.

---

## 2. Measured against asserted, inside the Phase 1 findings

The answer to "does each finding separate measured from asserted" is: **partly in `01-a`, mostly in
`01-b`, and in `01-d` only inside its tables.**

### 2.1 `01-a-market-structure.md`: classes on the tables, none on the connectors

The two empirical tables (§2 studies, §4 sizing) carry a Class column and use it. The prose around
them does not. Conclusions carrying no class, in order of how much they matter:

- **§1, the whole mechanism map table.** Every row's "Where the fees sit" and "Observable to us" cells
  are unclassed, and the table is what the report calls the mechanism map.
- **§1: "Fees on resale are *two-sided*, so 'the price' is ambiguous by 20-40%** depending on the
  observed side". A quantified range with no citation anywhere in the file, and no class.
- **§1, the regulatory paragraph.** NSW penalties "A$110,000/A$22,000", Ireland's 2021-07-31 ban, the
  UK announcement, "on 2026-04-15 an SDNY jury found Live Nation and Ticketmaster liable on all
  antitrust counts". The last is self-labelled "(secondary source, docket not read)" but carries no
  class; the rest carry neither.
- **§2, the closing "Magnitudes to carry forward" line**: "level ≈1.3-1.5× face on average for
  concerts … 25% of resold tickets above +67%, 26% below face; total resale surplus small relative to
  primary revenue (1.4%)." That is the report's summary of the numbers a modeller would use, presented
  with no class and no per-figure citation.
- **§3: "The UK's 37.1m primary tickets a year support ≈1.9m secondary sales worth £350m before fees —
  ≈£184 gross average, ≈£269 per resale ticket inclusive of all fees."** No class. Checked: the first
  two figures are the DBT note's baseline; £269 is from a different flow in the same note (£404m over
  1.5m tickets), not from the 1.9m/£350m pair, so the sentence splices two baselines.
- **§4: "repricing the top 10% of seats at the median resale price for those seats raises primary
  revenue 3.4%, ≈$27,000 per event"**. Marked "(their counterfactual — a model-based simulation, not
  an observed adoption)" but given no class, and it is the number that determines whether the prize is
  worth building for.
- **§5: "Get Protocol … claims 'millions of on-chain smart tickets since 2016' (vendor claim; I did
  not verify a count against chain state)."** No class. This is E by the `README.md` definition and
  should say so, especially because §6 then relies on that dataset being real.
- **§6 and §7 in full.** "Vanishes / Survives, relocated / Appears", and the three-column
  "Literature problems we no longer have / Still have / Newly have" summary carry no classes at all,
  including the sentence the whole project turns on: "the sale count is a numerator with no denominator
  and `P(sale | price, exposure, t)` is unidentified (Gap 1)". That is class C by construction and is
  the project's central constraint. It is unlabelled.
- **§6: "all class D with a clear test"** is the one place the summary assigns classes, and it covers
  only the three new mechanisms.

### 2.2 `01-b-identifiability.md`: the best disciplined file, with two holes

Classes are applied inline throughout §4 and most of §4 is genuinely careful ("Class C — an argument,
not a measurement"). The holes:

- **§3, the identifiability ledger, has no Class column.** Six target quantities T1 through T6, each
  with a status ("Set-identified at trade instants", "Not identified", "Estimable"), and not one status
  carries a class. These statuses are the file's entire output.
- **§1 and §6 carry no classes.** "one is honestly buildable today, two are set-identified with bounds
  we can actually compute, and three are not identified at all", and all three "design consequences".
- **§4.3, the three survivors** (unconditional intensity, competing-risks split, cure component) are
  each unclassed. All three are C.
- **Two fixture numbers, unclassed and wrong.** §4.1: "only 90 of 128 fixture tickets ever sell, so
  pairs come from the liquid subset". §4.3: "14 of 128 tickets redeem". The audit gives 90 `sale`
  **rows** and 14 `redeem` **rows** in a 253-row ledger, and says "79 of 128 tickets have no sale at
  all". So 49 tickets sell, not 90, and 1-B has read row counts as ticket counts. It also breaks the
  programme's own rule: `00-data-situation.md` §2 says "No number in this programme comes from
  `lib/mock/`". The same file uses the correct 79-of-128 figure at §4.6, so the two numbers sit in one
  document and disagree.
- **§4.5: "I found no peer-reviewed econometric study of resale price caps in ticket markets."** An
  absence claim, unclassed (harmless, but it is a conclusion).
- **§7: "Metadata for every item below was checked against Crossref or OpenAlex during this pass; no
  citation is from memory alone."** This is a claim about the file's own diligence and it is the one
  claim in the file that is checkable, so I checked it. It is false as printed: one DOI does not
  resolve (§3 below).

### 2.3 `01-d-external.md`: classes in the tables, and a count that does not exist

Table C-1 gives every variable a Class and a Priority, and that part is the strongest of its kind in
the records. Outside the tables:

- **"Nineteen candidate variables were examined against §4.2 and eleven survive at usable priority."**
  Neither number can be reached from the file. C-1 has 17 rows (V1 to V17). C-2 rejects 11. Priority
  1 through 4 covers 15 rows; priority 1 and 2 cover 9. There is no reading that gives eleven, and no
  reading that gives nineteen candidates from 17 plus 11 rows. Treat both counts as asserted, and
  replace them with a derived count.
- **§4, the four mechanism paragraphs.** They cite V-numbers but carry no classes, and they add claims
  about our market that the tables do not make: "On events that sold out at on-sale, the observed path
  rises into the event date; on soft events it decays." The "(class A)" in that section attaches to
  Sweeting's baseball result, not to the platform claim.
- **§5, the causal/predictive split.** "Three of the eleven are genuinely causal" and the assignment
  of the other fourteen are unclassed judgements.
- **§9 is an honest limits section** and should be read as part of the finding: it says the four
  ticket-market bibliographies were "not re-checked in this run" and that the Ticketmaster price-field
  removal is "reported, not established". Good practice; the ledger should not present this file as
  fully verified without it.

---

## 3. Citations

I checked 43 DOI lookups at Crossref covering 42 distinct works, plus four regulator and register
documents fetched live. **Every DOI cited in the three findings resolves to the cited title, author
set and journal, ~~with one exception~~** **[CORRECTION 2026-11-07T14:00Z, R2-7 — dead as a tally: no DOI
fails to resolve. Two *author sets* do not match Crossref (`01-b` §7's "Luo" and Mason entries), which is a
printing error inside a resolving record and not an unresolvable citation; see `01-b` CORRECTION 3.]** **.**

### Confirmed wrong as cited

- ~~**`10.1016/S0304-4076(73)90005-5`** (`01-b` §7, Aigner 1973, *Journal of Econometrics* 1(1), 49-59).
  Crossref returns **HTTP 404**. A stray `S` has been inserted: the correct DOI is
  **`10.1016/0304-4076(73)90005-5`**, which resolves to exactly the cited title. This is the single
  unresolvable citation in the records, and it lands on the sentence in `01-b` claiming every citation
  was checked.~~ **[CORRECTION 2026-11-07T14:00Z, R2-5 — dead, and it is the only dead bullet in this
  section: `01-b` does not contain that string. Its two Aigner occurrences are the resolving form; the only
  `S0304-4076` DOI in the file is Bollinger's. The 404 was real but was run on an input that is not in the
  file. Withdrawn in full at the end of this file; nothing about Aigner needed correcting.]**
- **"16 CFR Part 464, 90 FR 2166"** (`01-a` §1 and §7). The rule is **90 FR 2066**, not 2166, federal
  register document 2024-30293, *Trade Regulation Rule on Unfair or Deceptive Fees*, published
  2025-01-10, `cfr_references` part 464 title 16, `effective_on` 2025-05-12. A digit transposition. The
  effective date and the part number are right, so the substantive claim stands on a mis-cited
  register page.

### Could not confirm

- **Gov.ie, *Sale of Tickets Act 2021*.** The page returns **HTTP 403** to this host. The Irish ban
  and its 2021-07-31 commencement are unconfirmed here; they are also not load-bearing for any
  conclusion in `01-a`.
- **The Live Nation / Ticketmaster SDNY verdict of 2026-04-15.** The cited Paul, Weiss memo URL
  returns HTTP 200, but a law-firm client memo is not a court record and I read no docket. `01-a`
  itself flags it "(secondary source, docket not read)". Unconfirmed as a factual claim about a
  verdict.
- **Get Protocol, "millions of on-chain smart tickets since 2016".** Vendor claim; `01-a` says it did
  not verify it against chain state and `01-d` says `docs.get-protocol.io` returns 401 without an
  account. Unconfirmed, and it should be class E wherever it appears.
- **Krueger, *Rockonomics* (2019), cited by `01-d`.** No DOI, no publisher detail, and `01-d` §9
  admits it was cited from memory. Not confirmable from the record as written.
- **Ticketmaster "priceRanges present on 3 of 2,397 US events".** A vendor's October 2026 test, which
  `01-d` §9 correctly labels "reported, not established". I could not confirm it independently.
- **He & Lin, cited by `01-a` as "2025"** (`10.1287/mksc.2023.0623`). The DOI resolves; Crossref gives
  *Marketing Science*, issued **2026-05**, with an SSRN preprint at 2023. So the work is real, but the
  year as printed does not match the published record. Same pattern is not present elsewhere: all
  other year and volume labels match Crossref.

### A citation disagreement between two findings files

`01-a` cites "Budish & Bhave, *AEJ:Micro* 15(1):142-170, 2023, doi:10.1257/mic.20180230", which is
correct. `01-d` §9 cites "Bhave & Budish (2017, NBER WP)", with the author order reversed. Both refer
to the same paper (NBER WP 23770 in 2017, published version 2023). The ledger should not inherit the
reversed form.

### One internal reference that points at nothing

`01-a` §7 cites "Primary sell-through velocity: inventory is a snapshot only (Gap 5)". The audit
numbers four gaps and then lists two more as "Two smaller ones, recorded for completeness", never as
Gap 5. `grep -n "Gap 5"` finds the label only in `01-a`. Minor, but a reader following it finds no
Gap 5 to read.

---

## 4. Does `01-b` §5 genuinely contradict `00-data-situation.md`? Yes, twice, and the records do not say so

`01-b` opens with "Disagreements with `00-data-situation.md` are recorded in §5, not resolved
silently" and then makes four claims. Two are real contradictions, one is a genuine narrowing, and one
converges with the audit rather than opposing it.

**Contradiction 1: what the missing denominator is.**

Audit, Gap 1: "So for each ticket we know whether it eventually sold but **not the interval during
which it was at risk of selling**, nor at what ask. **`P(sale | price, exposure, t)` is not identified
from a completed-transaction ledger alone.** Without exposure, the observed sale count is a numerator
with no denominator."

`01-b` §5.1: "**Gap 1 is misdiagnosed; the fix is right.** The audit calls the sale count 'a numerator
with no denominator'. **The denominator is present** — every ticket has an `issue` row and a known
life. The unobserved object is the ask of the risk set."

These do not reconcile. The audit asserts two things are missing, the exposure interval and the ask.
`01-b` asserts one is missing, the ask. That is a straight disagreement about the observation set, and
it matters: if the interval is observed, the baseline sale intensity is buildable now, which is
`01-b`'s central recommendation.

**Contradiction 2, and this is the sharper one: whether the asking-versus-realised gap shrinks.**

Audit, Gap 1: "The *asking-versus-realised* gap **does shrink**. The *censoring* problem does not
shrink — it **relocates**, from censored asking prices to an unobserved exposure denominator plus a
policy-truncated price ceiling."

`01-b` §5.2: "**The asking-versus-realised gap does not shrink; it vanishes.** There is *no ask
anywhere in the record*, so there is no wedge to estimate, and a whole block of Phase 2 A — listing
revision, duplicate listings, seller competition, price discovery through asking — is **not partially
available but entirely unavailable**."

"Does shrink" against "entirely unavailable" is a contradiction on the face of the two documents.

**Not a contradiction: the identification result itself.** On the sentence that matters most, the two
files agree. The audit says `P(sale | price, exposure, t)` is not identified; `01-b` T3 says "**Not
identified.** Only λ(t|p)·Pr(ask=p|listed,t)·Pr(listed|t) is", and §4.3 says "The price response is
not recoverable". Both also land on the same fix, the four listing fields. So `01-b`'s disagreement is
with the audit's *diagnosis* and its *severity*, not with its conclusion.

**Narrowing, not contradiction: Gap 4.** `01-b` §4.5(i) shows an ad-valorem fee is neutral for the
resale ask (`arg max p(1−φ)h(p) = arg max p·h(p)`), so Gap 4 "does not bite on the resale
recommendation — only on the primary optimum". `01-b` calls this "Gap 4 is narrower than stated"; the
audit's Gap 4 text is about the primary optimum, so this is a refinement rather than a conflict.

**Why this matters for the ledger.** The conflict exists only inside `01-b` §5. `F-decision-log.md`
D3 records the audit's version as settled: "there is no listing start, ask, revision or withdrawal, so
the sale count is a numerator with no exposure denominator". The audit has not been amended. So the
six records currently carry the contested claim as the decided one, which is the thing `README.md`
forbids: "Conflicting findings are recorded, not silently dropped" and "Record conflicts, do not
resolve them silently." The ledger's P0.4 row says the gap "kills sale-hazard identification", which is
the version `01-b` disputes. Either P0.4 gets an explicit contested marker, or `F` gets a new entry
naming both versions and leaving it open. It is an operator or orchestrator decision, not mine.

---

## 5. What this means for the ledger

1. **The ledger is two documents stapled together.** Phase 0 is fully written up with findings and an
   invented class label. Phase 1 is a dispatch log that never got a second pass, and three of its four
   deliverables are sitting in `findings/` unindexed. The fix is mechanical: three rows change from
   `dispatched` with no finding to `answered` with a one-line finding, one row stays `dispatched` and says openly
   that no file exists, and the "Last updated" line moves to the newest finding.
2. **Every Phase 0 row carries a class that does not exist.** Five of five. This is the one defect
   that propagates: any reader who trusts the Class column is reading a vocabulary the same directory
   defines differently. It should be fixed in the ledger, or the vocabulary extended in `README.md` and
   the extension applied everywhere.
3. **P0.1 overstates its own audit.** "No program id anywhere" is "no program id in the frontend tree",
   and `F` Q2 leaves the deployment question open. A row that answers a narrower question than it asks
   is worse than a row that says it is partial, because the next session will treat the deployment
   question as closed.
4. **The conflict on Gap 1 is not in the records.** It is in one findings file's §5 and nowhere else,
   while `F` D3 and ledger P0.4 both state the disputed version as settled. `README.md` requires the
   opposite.
5. **The class discipline is uneven in a specific, predictable way.** `01-b` classes its arguments but
   not its table or its summary. `01-a` classes its tables but not its prose or its three-column
   synthesis. `01-d` classes its variable table but not its mechanism prose or its counts. In all
   three, the unclassed material is the material a reader would act on: the identification statuses,
   the "magnitudes to carry forward", the "what we newly have", the surviving-variable count.
6. ~~**One unresolvable citation and one mis-cited register page** are the only bibliographic failures
   across 42 works, which is a good rate. Both are transcription errors, not invented sources. Fix
   both, and strike the sentence in `01-b` §7 claiming every item was Crossref-checked, or correct it
   to what was actually done.~~ **[CORRECTION 2026-11-07T14:00Z, R2-7b — dead as a count and as an
   instruction: there is one bibliographic failure, the 90 FR 2166 register page, which is a transcription
   error and not an invented source. The "unresolvable citation" does not exist (see §3 above). The other
   real defect in `01-b` §7 is two printed author sets, not a DOI, and it is corrected in that file's
   CORRECTION 3.]**
7. **Two fixture numbers in `01-b` break the programme's own evidence rule** and are arithmetically
   wrong on the audit's own figures (90 sale rows read as 90 sold tickets when 49 tickets sold). They
   are not load-bearing for `01-b`'s conclusion, but they are exactly the kind of number that gets
   copied forward into a model registry, so they should be corrected at source rather than noted in
   the ledger.

**Method note.** Every verdict above rests on a file on disk, read in full. Where a claim could not be
settled from the documents (the tier used at dispatch, the Irish commencement, the antitrust verdict,
the Get Protocol count) I have said so rather than inferring. Quotes are verbatim, with ellipses where
text is elided; nothing is paraphrased inside quotation marks.

---

## CORRECTION (2026-11-07T11:28Z) — the Aigner 404 finding is false, and is withdrawn

Appended by the corrections pass after `records/findings/00-verification-round1.md` §2. Nothing above is
deleted. This is the first finding in this file that the record has had to withdraw, so the withdrawal is
stated at length.

**Withdrawn text, §3 "Confirmed wrong as cited", first bullet:**

> "**`10.1016/S0304-4076(73)90005-5`** (`01-b` §7, Aigner 1973, *Journal of Econometrics* 1(1), 49-59).
> Crossref returns **HTTP 404**. A stray `S` has been inserted: the correct DOI is
> **`10.1016/0304-4076(73)90005-5`**, which resolves to exactly the cited title. This is the single
> unresolvable citation in the records, and it lands on the sentence in `01-b` claiming every citation
> was checked."

**What is true.** `01-b-identifiability.md` does not contain the S-prefixed DOI. Checked in the working copy
on 2026-11-07: the Aigner DOI appears twice and both are the resolving form, at line 246 as a link and at
line 325 in the reference list. The two occurrences of `S0304-4076` in the file are both Bollinger (1996),
`10.1016/S0304-4076(95)01730-5`, where the `S` belongs. A Crossref query for
`10.1016/0304-4076(73)90005-5` on 2026-11-07 returns Aigner, "Regression with a binary independent variable
subject to errors of observation", *Journal of Econometrics* 1, 49-59.

So the 404 was real and was produced by querying a string that is not in the file. The check was run against
the wrong input and its result attributed to `01-b`. Every sentence of the bullet is withdrawn, including
"This is the single unresolvable citation in the records".

**What this does not rescue.** The closing clause of the bullet, that the sentence in `01-b` claiming every
citation was checked is false as printed, is **true for a different reason**: two author attributions in that
reference list are wrong (see `01-b` CORRECTION 3 and `00-verification-round1.md` §4). Consequently the
opening sentence of this section, "Every DOI cited in the three findings resolves to the cited title, author
set and journal, with one exception", is also wrong, because the author sets of two entries do not match
Crossref. The correct tally for this section is: no unresolved DOI, two wrong author sets, one wrong page
range (`02-e`, Ekeland et al.).

**Propagation.** The false finding was inherited by `records/A-research-ledger.md` ("Defects the verification
found that no record carries") and by `00-adversarial-review-phase1.md` (its notes on the prior pass). Both
carry a dated correction withdrawing it. No other file repeats it.

**What stands in this file.** Everything else in §3: the 90 FR 2066 finding and its Federal Register document
2024-30293 detail, the Gov.ie 403, the unconfirmable Krueger and Get Protocol entries, the He & Lin year, and
the whole of §1 and §2. Nothing in the verdict table rests on the withdrawn bullet.

---

## CORRECTION R2-5 to R2-7 (2026-11-07T14:00Z) — the withdrawal is now marked at the site, not only at the end

Appended by the round-2 corrections pass after `records/findings/00-verification-round2.md` §1 items 8–10 and
§2.2. Round 1's withdrawal above was correct and was carried on the last page of the file; §3 "Confirmed wrong
as cited" still printed the accusation as a live finding, in the section a reader opens for the citation audit.
The verifier's verdict on that is exact and is adopted here: a true withdrawal that leaves the withdrawn text
standing where a reader meets it first has not corrected the record.

Four passages in the body now carry dated markers: the Aigner bullet in §3 (R2-5); the P1.C row's
"no `01-c*` file exists" and its correction cell (R2-6); §3's opening "with one exception" (R2-7); and the
closing list's "one unresolvable citation and one mis-cited register page" (R2-7b). Nothing is deleted here or
there; the argument remains in the round-1 block above.

**What was true, and when.** The 404 was real: a Crossref query for `10.1016/S0304-4076(73)90005-5` returns it.
The string simply is not in `01-b-identifiability.md`, whose two Aigner occurrences are the resolving form.
The P1.C row was a 10:55Z observation and `01-c-methods.md` landed complete at 11:09Z, so the row was true when
written and false by the time anyone read it — which is why the marker says "dead as a statement about the
tree" rather than "always false".

**One thing this file still gets right and no pass should touch.** The 90 FR 2066 finding is independent of the
Aigner error and is unaffected. §3's "with one exception" is now shown to be wrong in a second way: the
exception it named does not exist, and the two real bibliographic defects in `01-b` §7 are printed author sets,
not failing DOIs. Both are recorded in `01-b` CORRECTION 3.

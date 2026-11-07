# A — Research ledger

Curated index of every research question. The raw reports live in `findings/` and are the
primary record; this file indexes them and does not replace them. A row is only as good as
the file in its File column.

**Last updated:** 2026-11-07T10:59Z
**Rows:** 10 (nine carried forward, one added — the verification pass).

---

## How to read this

- **Status** is one of `answered`, `answered-partial`, `open`, `dispatched`,
  `closed-not-worth-it`. No other word is used.
- **Class** is `records/README.md`'s vocabulary and nothing else: **A, B, C, D, E**, plus
  the two labels README explicitly says are not evidence classes, **SIM** and
  **UNVALIDATED**. An earlier version of this file used `verified` on the Phase 0 rows;
  that label does not exist in `records/README.md` and is gone.
- **`OBSERVED`** on the Phase 0 rows is **not** an evidence class and is not offered as
  one. It marks a statement that is true of this repository by direct inspection, with the
  observing command quoted in `00-data-situation.md` §6. It says nothing about ticket
  markets. Where a Phase 0 row draws a market consequence, the consequence carries a
  README class in the finding text.
- **File** is where the finding lives. A row with no file on disk is `dispatched` and its
  File cell says so.
- `—` means there is nothing to record yet, not that the value is zero.

---

## Phase 0 — data situation

| ID | Question | Who | Status | Finding | Class | File |
|---|---|---|---|---|---|---|
| P0.1 | Does a backend, database or deployed Solana program exist on this machine? | orchestrator | answered-partial | No backend, database or program id in the frontend tree, and `API_CONTRACT.md` specifies a backend that does not exist; whether a program is deployed anywhere else is unanswered and is F Q2. | OBSERVED | `records/00-data-situation.md` §1 (open part: `records/F-decision-log.md` Q2) |
| P0.2 | Are `lib/mock/` the real ledger? | orchestrator | answered | Synthetic fixtures: no generator, no seed, no provenance; the mint strings do not decode to 32 bytes (devnet returns `WrongSize`); the maximum markup sits strictly below each event's cap and no sale lands exactly on it. | OBSERVED | `records/00-data-situation.md` §2 |
| P0.3 | What observation set does an estimator receive? | orchestrator | answered | The `lib/types.ts` wire contract: `LedgerEntry[]`, `Ticket`, `Event`, and derived `ResaleStats` / `EventAnalytics` aggregates; a full audit is in `00-data-situation.md`. | OBSERVED | `records/00-data-situation.md` §3 |
| P0.4 | What is missing from the contract that a pricing engine needs? | orchestrator | answered | Four absences: no listing exposure, a policy price ceiling that truncates the value distribution, no seat coordinates, no fee/settlement field. The Gap 1 diagnosis — that missing exposure leaves a numerator with no denominator — is contested, class C, and carried as Contradiction C1 below. | OBSERVED (market consequence: C, contested) | `records/00-data-situation.md` §4 |
| P0.5 | Can any estimator be validated here? | orchestrator | answered | No: no result can be class A from our own data, every quantitative conclusion is B, C, SIM or UNVALIDATED, and simulation is admissible only for estimator properties. | OBSERVED | `records/00-data-situation.md` §5 |

---

## Phase 1 — foundational discovery

| ID | Question | Who | Status | Finding | Class | File |
|---|---|---|---|---|---|---|
| P1.A | What is the actual market structure and economic mechanism of primary and secondary live-event ticketing, and what does the evidence say about time-to-event price paths, resale caps, and platform economics? | forge `p1-market` (tier claimed `default`; no run id in the file) | answered | Primary tickets are systematically priced below secondary clearing value but the prize is modest (≈41% markup on the ~5% of tickets that resell, worth 1.4% of primary revenue), secondary prices near the event overwhelmingly fall, and on a capped on-chain ledger the recorded markup is a biased-down lower bound exactly where value is highest. | A (empirical core), C (truncation argument), D (three new mechanisms) — its own §6 | `records/findings/01-a-market-structure.md` |
| P1.B | Given a completed-transaction ledger with no asks and no exposure, what is identifiable? Which quantities (value, path, sale probability, elasticity) survive, which do not, and what is the minimal extra observation that fixes each? | forge `p1-ident` (tier claimed `best`; no run id in the file) | answered-partial | Of six targets, one is buildable today, two are set-identified with computable bounds and three are not identified; the missing object is the ask of the risk set rather than the at-risk denominator, and four fields per listing convert the sale hazard from unidentifiable to estimable. The file labels itself a first pass. | C (identification arguments), B (demand bracket), A where cited; §3 statuses themselves unclassed | `records/findings/01-b-identifiability.md` |
| P1.C | Which methods from other fields (revenue management, survival, hedonic pricing, auction theory, online learning, Bayesian partial pooling, conformal prediction, stochastic control) genuinely buy something here, and for which subproblem? | forge `p1-methods` (tier `default`; re-dispatched 2026-11-07T10:53Z as run `dmw6a4s92aum0`; the duplicate `dmw6a5ghzhhl8` was killed) | dispatched | No finding yet: the file on disk at 10:59Z is a 28-byte placeholder reading `# Phase 1-C — placeholder`, and the previous run died after "Now writing the report." | — | `records/findings/01-c-methods.md` — placeholder, no content |
| P1.D | Which external signals have a plausible mechanism and are actually obtainable and licensable, and what is each one's collection cost and leakage risk? | forge `p1-external` (tier claimed `default`; no run id in the file) | answered | 17 variables admitted with a class and a priority and 11 rejected on licence, mechanism or legal grounds; only Ticketmaster Discovery, a venue capacity table and NOAA weather are worth collecting, and the two highest-value variables (listing depth and seat coordinates) are not in the contract at all. Its head-line counts (19 examined, 11 survive) do not reconcile with its own tables (17 admitted rows, 11 rejected). | per-variable A/B/C/D in Table C-1; §4–§5 prose and the head-line counts unclassed | `records/findings/01-d-external.md` |

Dispatch metadata: no finding file states a run id or a tier, so the tier in the Who column
is what was claimed at dispatch, not a fact the deliverable evidences
(`00-ledger-verification.md` §1.2).

---

## Records verification

| ID | Question | Who | Status | Finding | Class | File |
|---|---|---|---|---|---|---|
| V1 | Is every row of this ledger supported by the file it cites? | verification pass (tier `low`, run `dmw6a5h9shisa`) | answered | 4 rows supported, 1 partial (P0.1 overstates its own grep), 3 unsupported because P1.A, P1.B and P1.D said `dispatched` while their files were on disk, and 1 file-absent (P1.C); it also found the invented `verified` class, two real contradictions between 01-b §5 and the audit, one unresolvable DOI and two wrong fixture counts. | OBSERVED | `records/findings/00-ledger-verification.md` |

---

## Contradictions on record

Two conflicts between `01-b-identifiability.md` §5 and `00-data-situation.md` §4 are real
and are **not resolved here**. Neither is carried by an F entry; F D3 carries the audit's
version as the settled one, which is the failure `records/README.md` forbids ("Record
conflicts, do not resolve them silently").

**C1 — what the missing denominator is.**

- Audit, Gap 1: "So for each ticket we know whether it eventually sold but not the interval
  during which it was at risk of selling, nor at what ask. `P(sale | price, exposure, t)` is
  not identified from a completed-transaction ledger alone. Without exposure, the observed
  sale count is a numerator with no denominator."
- `01-b` §5.1: "Gap 1 is misdiagnosed; the fix is right. The audit calls the sale count 'a
  numerator with no denominator'. The denominator is present — every ticket has an `issue`
  row and a known life. The unobserved object is the ask of the risk set."

Recorded in: `records/findings/01-b-identifiability.md` §5.1 only. Not in F. F D3's evidence
line is the audit's version: "there is no listing start, ask, revision or withdrawal, so the
sale count is a numerator with no exposure denominator." **Open.**

**C2 — whether the asking-versus-realised gap shrinks or vanishes.**

- Audit, Gap 1: "The asking-versus-realised gap does shrink. The censoring problem does not
  shrink — it relocates, from censored asking prices to an unobserved exposure denominator
  plus a policy-truncated price ceiling."
- `01-b` §5.2: "The asking-versus-realised gap does not shrink; it vanishes. There is no ask
  anywhere in the record, so there is no wedge to estimate, and a whole block of Phase 2 A —
  listing revision, duplicate listings, seller competition, price discovery through asking —
  is not partially available but entirely unavailable."

Recorded in: `records/findings/01-b-identifiability.md` §5.2 only. Not in F. **Open.**

Not a contradiction, recorded so it is not mistaken for one: the Gap 4 fee question. `01-b`
§4.5(i) shows an ad-valorem fee is neutral for the resale ask, so the missing fee field
bites only on the primary optimum; that is a narrowing of the audit's Gap 4, not a conflict
(`01-b` §5.4; F D4 is unaffected).

### Defects the verification found that no record carries

From `records/findings/00-ledger-verification.md` §2 and §3, restated here only as pointers:

- `01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404; the
  resolving DOI is `10.1016/0304-4076(73)90005-5`. The claim in that section that every
  citation was checked is false as printed.
- `01-a` §1 and §7 cite "16 CFR Part 464, 90 FR 2166"; the rule is 90 FR 2066.
- `01-b` §4.1 and §4.3 read 90 `sale` rows as 90 sold tickets and 14 `redeem` rows as 14
  redeemed tickets; on the audit's figures 49 of 128 tickets sell and 79 never do. The same
  file uses the correct 79-of-128 at §4.6.
- `01-a` §7 cites a "Gap 5" that `00-data-situation.md` never numbers.

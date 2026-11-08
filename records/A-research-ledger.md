# A — Research ledger

Curated index of every research question. The raw reports live in `findings/` and are the
primary record; this file indexes them and does not replace them. A row is only as good as
the file in its File column.

**Last updated:** 2026-11-07T12:55Z
**Rows:** 10 (nine carried forward, one added — the verification pass).

**Refresh, 2026-11-07T12:55Z.** Every row was re-checked against the file in its File column. One row was
wrong: P1.C still read `dispatched` with a placeholder finding after `01-c-methods.md` had landed complete
(1,558 lines, written 10:57Z–11:09Z, mtime 12:03Z). It now carries its own conclusion, its class and its
path. The other nine rows match their files; P1.A, P1.B and P1.D were already `answered`/
`answered-partial` with a finding and a path, and the Phase 0 and V1 rows cite files that exist and say what
the rows say they say. No conclusion in any row was rewritten.

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
| P1.C | Which methods from other fields (revenue management, survival, hedonic pricing, auction theory, online learning, Bayesian partial pooling, conformal prediction, stochastic control) genuinely buy something here, and for which subproblem? | forge `p1-methods` (tier `default`; re-dispatched 2026-11-07T10:53Z as run `dmw6a4s92aum0`; the duplicate `dmw6a5ghzhhl8` was killed) | answered | Three of the eight families ship code for a quantity this observation set actually identifies, two ship the decision structure and no number, and three ship reasons not to build; no family converts an unidentifiable target into an identifiable one — "a method is not a substitute for an observation". Build order: censored hedonic on log markup, repeat-sales check, competing-risks hazard with a cure component, hierarchical layer, reserve-price surface; nothing past the second needs an external field, everything from the third needs the operator's four fields, money, or both. | per-family A/B/C/D throughout (A only where inherited from `01-a`/`01-b`); the file states no single class, and §1.1 and §1.2 are unclassed | `records/findings/01-c-methods.md` |
| P1.D | Which external signals have a plausible mechanism and are actually obtainable and licensable, and what is each one's collection cost and leakage risk? | forge `p1-external` (tier claimed `default`; no run id in the file) | answered | 17 variables admitted with a class and a priority and 11 rejected on licence, mechanism or legal grounds; only Ticketmaster Discovery, a venue capacity table and NOAA weather are worth collecting, and the two highest-value variables (listing depth and seat coordinates) are not in the contract at all. Its head-line counts (19 examined, 11 survive) do not reconcile with its own tables (17 admitted rows, 11 rejected). | per-variable A/B/C/D in Table C-1; §4–§5 prose and the head-line counts unclassed | `records/findings/01-d-external.md` |

Dispatch metadata: no finding file states a run id or a tier, so the tier in the Who column
is what was claimed at dispatch, not a fact the deliverable evidences
(`00-ledger-verification.md` §1.2).

**Superseded, kept as history:** the V1 row below records that at 11:22Z three Phase 1 rows said
`dispatched` with files on disk and P1.C had no file at all. That was true of the tree at that moment. The
Phase 1 rows above are the tree as it stands at 12:55Z, and P1.C is `answered` on a complete file, not on the
run that was re-dispatched at 10:53Z — the placeholder it replaced is gone.

---

## Records verification

| ID | Question | Who | Status | Finding | Class | File |
|---|---|---|---|---|---|---|
| V1 | Is every row of this ledger supported by the file it cites? | verification pass (tier `low`, run `dmw6a5h9shisa`) | answered | 4 rows supported, 1 partial (P0.1 overstates its own grep), 3 unsupported because P1.A, P1.B and P1.D said `dispatched` while their files were on disk, and 1 file-absent (P1.C); it also found the invented `verified` class, two real contradictions between 01-b §5 and the audit, ~~one unresolvable DOI and two wrong fixture counts~~ **[CORRECTION 2026-11-07T14:00Z, R2-9c — dead: no unresolvable DOI (see the Aigner bullet below, now struck in place). Of the two fixture counts, one was wrong (90 `sale` rows read as tickets; 49 tickets sell) and one was a row count whose ticket count the record does not establish.]**. | OBSERVED | `records/findings/00-ledger-verification.md` |

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

- ~~`01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404; the
  resolving DOI is `10.1016/0304-4076(73)90005-5`. The claim in that section that every
  citation was checked is false as printed.~~ **[CORRECTION 2026-11-07T14:00Z, R2-9 — dead: `01-b` does not
  contain the S-prefixed string. Both of its Aigner occurrences are the resolving form, so there is no
  unresolvable DOI and no citation defect here. Withdrawn at the end of this file.]**
- `01-a` §1 and §7 cite "16 CFR Part 464, 90 FR 2166"; the rule is 90 FR 2066.
- `01-b` §4.1 and §4.3 read 90 `sale` rows as 90 sold tickets and 14 `redeem` rows as 14
  redeemed tickets; on the audit's figures 49 of 128 tickets sell and 79 never do. The same
  file uses the correct 79-of-128 at §4.6. **[CORRECTION 2026-11-07T14:00Z, R2-9b — the count is right and the
  bullet stands as a defect record; what has changed is that the four fixture-derived sentences in `01-b`,
  including the two named here, are now marked dead inline in that file rather than only in its correction
  block.]**
- `01-a` §7 cites a "Gap 5" that `00-data-situation.md` never numbers. **Resolved 2026-11-07T12:55Z:**
  Gap 5 is now defined in `00-data-situation.md` §4 — the missing primary inventory time series, hence no
  sell-through velocity — and all eight forward references agree on that referent. See the correction block
  at the end of this file.

---

## CORRECTION (2026-11-07T11:28Z) — the Aigner bullet above is false and is withdrawn

**Withdrawn text:**

> "- `01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404; the
>   resolving DOI is `10.1016/0304-4076(73)90005-5`. The claim in that section that every
>   citation was checked is false as printed."

The first sentence is false. `01-b` contains the resolving DOI and only the resolving DOI; the S-prefixed
string is not in the file. Checked in the working copy on 2026-11-07 and recorded in full in the new
correction appended to `records/findings/00-ledger-verification.md` §3. The `00-adversarial-review-phase1.md`
note that repeated it also carries a withdrawal.

The second sentence is true for a different reason: two **author** attributions in that reference list are
wrong (Fosse & Winship, not "Luo"; Winsborough, not "Winship"). Corrected in `01-b` CORRECTION 3.

**Also withdrawn, from the V1 row of the table above:** "one unresolvable DOI and two wrong fixture counts".
There is no unresolvable DOI, so the count is zero. Of the two fixture counts, the 90-of-128 is wrong
(90 `sale` rows, 49 tickets) and the 14-of-128 is a row count whose ticket count the record does not
establish; neither is a count of tickets. The row's substance (class discipline, the 01-b versus audit
contradictions) is unaffected.

---

## Corrections applied (2026-11-07T11:28Z)

This file and the findings beneath it were audited by an independent verification pass
(`records/findings/00-verification-round1.md`, 2026-11-07T11:26Z) and then corrected by a corrections pass
at 2026-11-07T11:28Z. Every correction is appended to the file it corrects, quoted there, and dated; nothing
was deleted and no finding's conclusion was rewritten. The full table, including defects the verification
reported that this pass did not touch, is `records/CORRECTIONS-APPLIED.md`.

| File | Defect corrected | Status of the finding |
|---|---|---|
| `findings/01-b-identifiability.md` | "only 90 of 128 fixture tickets ever sell": a `sale` row count read as a ticket count, and the one place in that file where a fixture number carries an argument. True figures from `00-data-situation.md` §2: 253 rows (128 + 90 + 21 + 14), 79 of 128 tickets never sell, so **49** sell. "14 of 128 tickets redeem" is the same row-as-ticket reading and cannot be restated as a ticket count from the record. | Withdrawn as printed; the selection argument stands as class C without the number |
| `findings/01-b-identifiability.md` | §5.3: the cap "varies ... across tiers within an event", so "the cap is an instrument". `resalePriceCapBps` is one field on `Event`; only the money ceiling varies, as face × (1+c), collinear with face. `01-c` §1.4(1) is right. | Withdrawn; cross-event instrument and the one-sided bounds survive, within-event instrument strength does not |
| `findings/01-b-identifiability.md` | Two wrong author attributions in a list claiming Crossref verification: `10.1146/annurev-soc-073018-022616` is Fosse & Winship, and Mason et al.'s third author is Winsborough. | Corrected; DOIs, titles, journals and pages verified unchanged |
| `findings/01-a-market-structure.md` | "even after scaling for the ~50% of resale the authors do not observe": the paper says the 1.4% covers only the half it observes. | Withdrawn; 1.4% stands as an unscaled figure with the paper's caveat attached |
| `findings/01-a-market-structure.md` | The £269 per-ticket figure is spliced onto the £350m / 1.9m flow; 269 × 1.9 = £511m, and £269 is £404m / 1.5m. | Withdrawn as a before-and-after pair; each pair must be quoted on its own |
| `findings/01-a-market-structure.md` | He & Lin cited as 2025; Crossref gives *Marketing Science* 45(3):515–533, 2026-05. | Corrected |
| `findings/00-ledger-verification.md` | The Aigner 404 finding accuses `01-b` of a DOI it does not contain. | Withdrawn in full, including "the single unresolvable citation in the records" |
| `findings/00-adversarial-review-phase1.md` | Repeated the Aigner finding. | Withdrawn |
| `findings/02-e-cold-start.md` | "−49% to +95%" labelled "as markup around face" is a multiplier on the point estimate, not an absolute markup band. | Relabelled; the arithmetic stands as exp(±1.645τ) |
| `findings/01-d-external.md` | "Nineteen candidate variables ... eleven survive at usable priority" is not derivable from its own tables: 17 admitted, 11 rejected, 9 at priority 1–2. | Withdrawn; the tables are the count of record |
| `C-variable-registry.md` | C-3 repeats the within-event cap claim. | Withdrawn; the cross-event statement stands |
| `findings/02-a-price-paths.md`, `findings/03-b-temporal-correctness.md` | Inherited the two wrong author attributions; `03-b`'s Luo entry also carries a title and page range that do not match its DOI. | Corrected at origin and in both inheritors |

**Not corrected, and why:** the header timestamps on `02-a` and `02-ai-ml-decision` that postdate their own
mtime, and the undefined "Gap 5" label, are recorded in `CORRECTIONS-APPLIED.md` with the reason each was
left alone. Neither is a statement this pass can correct without inventing a fact (a true write time, or a
definition of a gap nobody defined).

---

## CORRECTION (2026-11-07T12:55Z) — "Gap 5" is defined, and P1.C is answered

Two of the defects this file listed as open are closed, in the files that carried them. Nothing above is
withdrawn; the text that said these were open was true when it was written.

1. **"Gap 5" is now numbered.** `00-data-situation.md` §4 carries a fifth gap in the same style as Gaps 1–4:
   *no primary inventory time series, therefore no sell-through velocity* — `totalSupply` and `issuedCount`
   are a snapshot with no capture time and `Event.status` has no transition timestamps. This is the first of
   the two absences that section previously listed unnumbered, and it is what all eight forward references
   mean: `01-a` §7, `01-c` §1.4(3)/§2/§3.6/§9.3, and `B-mathematical-kb.md` §6.4/§6.5/§9. The full site
   table is in `00-data-situation.md` §4. No citation was rewritten, because none of the eight meant
   anything other than the inventory series; defining the label once was the smaller change.
2. **P1.C's row above now carries its finding.** The row was `dispatched` with a placeholder finding because
   that is what the tree held at 10:59Z. `01-c-methods.md` landed complete at 11:09Z. The row is now
   `answered`, with the conclusion from that file's own §1 and §1.3, its per-family classes and its path.

Both are recorded in the 2026-11-07T12:55Z entry of `records/CORRECTIONS-APPLIED.md`.

---

## CORRECTION R2-9 (2026-11-07T14:00Z) — the Aigner bullet above is struck where it stands

Appended by the round-2 corrections pass after `records/findings/00-verification-round2.md` §1 item 10 and
§2.2. The 11:28Z block above withdrew the bullet and the V1 tally, correctly; this pass found both still
printed unmarked in the body, under the heading a reader uses to find what the verification established. They
are now struck in place with dated pointers, and nothing is deleted. The verification file's own §3 carried the
same defect and is marked the same way.

One correction to the wording of the 11:28Z block, which says "Every sentence of the finding is withdrawn".
The 404 itself was real — a Crossref query for `10.1016/S0304-4076(73)90005-5` returns it — and the statement
that the resolving DOI is `10.1016/0304-4076(73)90005-5` is true. What is false is the attribution of that
string to `01-b`, and with it the word "unresolvable". The distinction matters because it is the difference
between a citation that needs fixing and a check that was run on the wrong input.


---

## R3-1 (2026-11-08T06:25Z) — findings 33 and 34: the region-aware cap, and two premises corrected

Two records were added by the region-aware resale caps pass, and both change what this ledger should
carry rather than only adding to it.

**`findings/33-a-region-cap-law.md`** (with five cluster records in the
`33-b-region-cap-law-sources` directory, one file per region: `uk-ie.md`, `eu.md`, `us.md`, `canada.md`,
`australia.md`) establishes, from primary instruments, which jurisdictions
restrict resale above a price and on what basis. Two premises that were supplied to the research were
checked and were wrong, and both are recorded as corrections rather than quietly replaced:

*[Reference corrected 2026-11-08: this row cited the sources directory as a path, which
`tools/doc_check.py` resolves as a claim that a file ending in `.md` exists at that name and reports
as a violation. The five files are named directly instead. The claim is unchanged.]*

1. **The United Kingdom's resale cap is announced policy, not law.** The government announced on
   19 November 2025 that resale above the original price plus unavoidable fees would be made illegal;
   no bill, instrument or commencement was identified. A table that treated the announcement as law
   would have refused lawful sales in the largest market in this dataset.
2. **New South Wales is not a flat 10%.** Part 4A of the Fair Trading Act 1987 (NSW) caps at "original
   acquisition cost", which s. 58E builds as the original supply cost plus the transaction cost
   actually paid, counted at no more than 10% of the supply cost. The ceiling is
   `face + min(fees paid, 10% of face)`, and the advertisement ceiling (110% of supply cost) is a
   different and looser number.

**Classification.** A for every instrument whose text was read; D for the one jurisdiction whose number
came from a committee report (Queensland) and is therefore **not enforced**; E for every jurisdiction
that was not read, which is most of the world. The table's own tests refuse a cap produced by a D- or
E-grade row, so the class is not decoration.

**`findings/34-region-caps-build.md`** carries the build and verification record, including the local
validator's eleven legs.

**What this does not establish.** Nothing about a market. It is a legal-constraint record: not a price,
not an elasticity, not a transaction probability. The only empirical claim in it is structural — a cap
truncates a price distribution, and a table of caps partitions the sample.

## R3-2 (2026-11-08T08:00Z) — the fee finding's ceiling stands, two of its alternatives do not

`findings/36-transfer-fee-on-a-one-unit-ticket.md` was reviewed by a non-builder (`tmp/review/fee-mechanism.md`,
read-only, reproduced the measurement independently). The review's verdict on the finding's central
claim is **reproduced and confirmed**, and the review found two errors in the alternatives section
that a reader would have acted on. This ledger entry records both, because finding 36 is not the doc
steward's file and is not rewritten.

**Confirmed, independently.** Token-2022 ceils the fee. At `decimals 0` and `amount 1` every rate
from 1 to 10,000 bps withholds the whole base unit, the withheld set is exactly `{0, 1}`, and the
reviewer proved it by enumerating the surface rather than sampling. `maximum_fee = 0` is the only
other way to withhold 0. Two premises the finding listed as unverified were exercised by the review:
the `maximum_fee` clamp on a real transfer, and `bps = 10,000` (legal on chain, refused above it). The
finding's conclusion is unaffected: features 5 and 7 are not buildable on an indivisible ticket.

**Corrected by the review, and this is the part this ledger now carries.**

1. **A venue lamport fee cannot come from the buyer.** The signer of a Token-2022 `TransferChecked`
the **seller** (the source account's owner or delegate); the buyer never signs, and the hook sees the
destination only as a token account. Finding 36 §5.1 says the opposite. The fee would have to be
taken from the seller through a `system_program::transfer` CPI out of the `authority` account the hook
already receives, with the recipient wallet added via extra-account-metas. The seller must hold the
lamports at transfer time, and the fee is charged on the staged price in the record, not on lamports
that moved.
2. **A divisible mint does not deliver a whole ticket.** Token-2022 invokes the hook with the
**pre-fee** amount and credits the destination `amount - fee`. A transfer of `TICKET_UNITS` leaves
the buyer holding 950,000 of 1,000,000 units at 500 bps and 850,000 at 1,500 bps. The seller must
send `calculate_pre_fee_amount(TICKET_UNITS)` (1,052,632 and 1,176,471), which is not equal to
`TICKET_UNITS`, so the proposed `amount == TICKET_UNITS` check refuses the only transfer that would
work. The check would have to move to the net amount, which the hook cannot compute without the
mint's live fee schedule, or to a per-holder balance check.
3. Two smaller corrections: the record carries `pending_price_lamports` and no hop count, and §3.3's
stated detector for the withdraw path is wrong (the instruction has no account slot for hook accounts
at all) though its conclusion holds.

**Classification.** A for the ceiling and everything the review and the finding measured; C for the
two corrected mechanisms (properties of the token program's call shape, read from the interface
source); no market claim either way. Q5 in `records/F-decision-log.md` now carries the same two
corrections, and features 5 and 7 remain **not built, blocked**.

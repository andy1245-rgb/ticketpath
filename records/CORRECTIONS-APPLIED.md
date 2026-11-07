# Corrections applied — verification round 1

**Status:** complete. **UTC:** 2026-11-07T11:28Z. **Agent:** corrections pass.
**Trigger:** `records/findings/00-verification-round1.md` (2026-11-07T11:26Z), an independent verification of
every file in `records/findings/`.
**Scope:** the defects that verification named, plus the inherited statements that carry them. Nothing outside
`records/` was read for evidence or edited. Nothing was committed or pushed.

**Rules this pass worked under.** The record is append-only. No text was deleted, no number was silently
replaced, and no finding's conclusion was rewritten. Each correction is appended to the file it corrects,
quotes the sentence it withdraws, states what is true and why, and carries a UTC ISO-8601 date and the word
CORRECTION. Where the verifier's own claim was wrong, that is said in the file and not propagated. Every new
number in this pass is either quoted from a named source or shown as arithmetic on numbers already in the
record.

**How each claim was checked.** Repository facts were checked by grep and by reading the working copy
(`01-b` has no S-prefixed Aigner DOI; `resalePriceCapBps` is declared once, on `Event`; Table C-1 has 17 rows
and Table C-2 has 11). Bibliographic facts were re-queried at Crossref during this pass, and the returned
title, author set, journal, volume, issue and pages are quoted in the corrections: `10.1016/0304-4076(73)90005-5`,
`10.1146/annurev-soc-073018-022616`, `10.2307/2094398`, `10.1287/mksc.2023.0623`, `10.1086/379947`. Arithmetic
was recomputed in Python and the intermediate values are printed in the corrections.

---

## 1. Defects corrected

One row per defect. "Found by" names the verification file and the section that raised it; where this pass
extended or narrowed the verifier's finding, the row says so.

| # | File | The wrong sentence (quoted, trimmed) | What is true | Found by |
|---|---|---|---|---|
| 1 | `findings/01-b-identifiability.md` §4.1 | "only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of an already-selected subset" | 90 is a `sale` **row** count. `00-data-situation.md` §2 gives 253 rows (128 `issue` + 90 `sale` + 21 `transfer` + 14 `redeem`) and 79 of 128 tickets with no sale, so **49** tickets sell and 41 tickets sold more than once. It is also the one place in that file where a `lib/mock/` figure does argumentative work, against the audit's rule "No number in this programme comes from `lib/mock/`". | verifier §4 and "defects that matter" 1 |
| 2 | `findings/01-b-identifiability.md` §4.3 | "14 of 128 tickets redeem" | Same row-as-ticket reading. The audit reports 14 `redeem` rows and no ticket-level redemption count, so the ticket count **cannot be reconciled from the record**. Read it as 14 rows. A fixture count was deliberately not produced to settle it, because the rule being cited forbids that. | verifier §4 (flagged as suspect, not proved) |
| 3 | `findings/01-b-identifiability.md` §5.3 | "`resalePriceCapBps` is observed and varies, across events and across tiers within an event … so the cap is an instrument" | The field is a single one on `Event`; `TicketTier` has no cap. The **money ceiling** varies across tiers as face × (1 + c) and is collinear with face, so there is no within-event identifying variation. The instrument is cross-event only. `01-c` §1.4(1) is right. | verifier §C1 (conflict C1) |
| 4 | `findings/01-b-identifiability.md` §7 | "Luo, L. (2019)" and "Winship, C." in Mason et al. (1973) | Crossref returns `10.1146/annurev-soc-073018-022616` as **Fosse, E. & Winship, C. (2019)**, and `10.2307/2094398` with third author **Winsborough, H. H.** Titles, journals, volumes and pages are right. | verifier §4, §8 |
| 5 | `findings/01-a-market-structure.md` §4 | "**1.4% of primary revenue**, even after scaling for the ~50% of resale the authors do not observe" | The paper: "This is equivalent to 1.4% of the total primary market revenue for these events … even if we are accounting for only half of resale activity." 1.4% is the **observed half, unscaled**. "Even after scaling" inverts the caveat on the number the commercial case rests on. | verifier §3 and "defects that matter" 2 |
| 6 | `findings/01-a-market-structure.md` §3 | "≈1.9m secondary sales worth £350m before fees — ≈£184 gross average, ≈£269 per resale ticket" | 350 / 1.9 = 184.2, so £184 follows. 269 × 1.9 = £511m, not £350m; £269 is £404m / 1.5m, a different flow in the same DBT note. Two baselines were spliced into a before-and-after pair. | verifier §3 and "defects that matter" 6 |
| 7 | `findings/01-a-market-structure.md` §3, §7 | "He & Lin (*Marketing Science*, 2025)" | Crossref: *Marketing Science* **45(3):515–533**, issued **2026-05**, "Price Caps by Matching Platforms: The Case of Ticket Resales". Cite as He & Lin (2026). | verifier §3, §3 "secondary findings" 14 |
| 8 | `findings/00-ledger-verification.md` §3 | "**`10.1016/S0304-4076(73)90005-5`** (`01-b` §7, Aigner 1973 …). Crossref returns **HTTP 404**. … This is the single unresolvable citation in the records" | `01-b` does not contain that string. Both Aigner occurrences are the resolving form (`10.1016/0304-4076(73)90005-5`); the only S-prefixed DOIs in the file are Bollinger's, where the S belongs. The 404 was real but was run against an input that is not in the file. Every sentence of the finding is withdrawn. The section's opening tally ("with one exception") is also wrong, for a different reason: two author sets do not match Crossref. | verifier §2 and "defects that matter" 3 |
| 9 | `findings/00-adversarial-review-phase1.md` (notes on the prior pass) | "the Aigner DOI (I re-checked Crossref: the `S`-prefixed DOI returns 404, the corrected one 200)" | The DOI check is real; the attribution to `01-b` is false, so the item is withdrawn as a finding. The paragraph also contradicts the same file's own coverage note, which says the Aigner DOI was not verified. | verifier §2 |
| 10 | `A-research-ledger.md` (defects list, and the V1 row) | "`01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404" and "one unresolvable DOI and two wrong fixture counts" | No unresolvable DOI, so that count is zero. Of the two fixture counts, one is wrong (90 rows read as tickets) and one is a row count whose ticket count the record does not establish. The rest of both entries stands. | verifier §2 (the propagation it names) |
| 11 | `findings/02-e-cold-start.md` §4.7 table, E8 | "90% band on the event mean, log units … as markup around face" with "−49% to +95%" | The column is exp(±1.645τ) applied to the point estimate: ×0.513 to ×1.950, i.e. −49%/+95% **of the estimate**. Centred where the model puts it (μ = 0.261), the absolute band is 0.666 to 2.532, i.e. **−33% to +153%**. As labelled it says the markup can be 49% below face, contradicting the file's own +41% mean and 26%-below-face input. The verification pass prints +155% for the upper end; 0.929 gives 2.532 and +153%, so that digit is corrected here. | verifier §11 and "defects that matter" 4 |
| 12 | `findings/02-e-cold-start.md` reference list | "Ekeland, I., Heckman, J. J. & Nesheim, L. (2004). *JPE* 112(6), 1278-1320" | Crossref for `10.1086/379947`: *JPE* **112(S1), S60–S109**. `01-b` has it right. | verifier §11 and "defects that matter" 13 |
| 13 | `findings/01-d-external.md` (What I concluded) | "Nineteen candidate variables were examined against §4.2 and eleven survive at usable priority." | Table C-1 has 17 rows; Table C-2 rejects 11; 28 candidates. Priority 1: 5 (V1–V5); 2: 4 (V6–V9); 3: 4 (V10–V13); 4: 2 (V16, V17); 0: 2 (V14, V15). So 9 at priority 1–2 (4 of them obtainable from the contract today) and 15 above 0. Neither 19 nor "11 survivors" is derivable; 11 is the reject count, and also the count of variables obtainable only outside the contract. | verifier §6 and "defects that matter" 5 |
| 14 | `C-variable-registry.md` C-3 | "varies across tiers within one event because it is bps over each tier's own face" | Same defect as row 3. Withdrawn; the cross-event statement, the mass point and the `01-c`/`D`/`B` versions stand. | verifier §C1 |
| 15 | `findings/02-a-price-paths.md` reference list | "Mason … Winship, C. & Poole" and "Luo, L. (2019)" | Same two attributions as row 4, inherited. Corrected at origin and here. | verifier §8, §13 |
| 16 | `findings/03-b-temporal-correctness.md` reference list | "[Luo 2019] Luo, L. (2019). Bayesian age-period-cohort analysis. *Annual Review of Sociology* 45, 109–132" | Crossref for the DOI printed there: **Fosse & Winship (2019), "Analyzing Age-Period-Cohort Data: A Review and Critique", 45, 467–492**. Author, title and pages are wrong; volume and DOI are right. **The verifier's statement that both of `01-b`'s author errors recur in this file is half wrong:** its Mason entry already has Winsborough. | verifier §13, extended by this pass |

That is **16 defects corrected across 10 files** (some files carry more than one).

---

## 2. What was checked and needed no correction

- **The 25/25/25/25 rubric weighting, requested as defect 7 of this brief.** Checked in
  `records/F-decision-log.md` and `records/BUILD-SPEC-NIGHT.md`, and by grep across `records/` for the four
  criterion words. **No file in `records/` states the brief's weighting as sourced.** `F-decision-log` relies
  on `02-rubric`'s B2 (idea quality is excluded), which is sourced. `BUILD-SPEC-NIGHT` R1 says "Design is 25%
  and Completion is 25%", which is a different weighting: `02-rubric` B1 quotes MLH's rules, "Judges will
  weigh the criteria equally", over Technology, Design, Completion and Learning, and 25% each is the
  arithmetic consequence. That is sourced. No correction was appended, because appending one would have
  asserted a defect that is not there.
  The unsourced weighting does appear at `NIGHT-BRIEF.md:130`, which is outside `records/` and outside this
  pass's remit. It is still uncorrected and still the document a build could be pointed at.
- **`02-rubric`'s own finding.** Re-read for this check and left alone: it is correct, it marks the weighting
  MEASURED-ABSENT, and its quotations of the two criterion sentences are the verbatim ones.
- **`records/D-model-registry.md` C6 and `records/B-mathematical-kb.md` C6.** Both already carry `01-c`'s
  correction of the cap claim and agree with correction 3 above, so nothing was appended to either.
- **`findings/02-b-cap-truncation.md`** (landed at 11:27Z, during this pass). Its B2 says the ceiling's
  "absolute level differs across tiers inside a single event", which is true and consistent with correction 3.
  It was not edited: another agent was writing it while this pass ran, and it is not defective on the point
  at issue.

---

## 3. Defects the verification reported that this pass did not touch, and why

| Defect | File | Why not touched |
|---|---|---|
| "Written: 2026-11-07T11:20Z" postdates the file's own mtime (11:06Z and 11:10Z) | `findings/02-a-price-paths.md`, `findings/02-ai-ml-decision.md` | The true write time is not in the record, and mtime is not usable as evidence after this pass's own appends. Correcting the header would mean inventing a timestamp and rewriting a header field, both of which this pass forbids. Flagged for whoever owns the clock. |
| "Gap 5" cited five times and defined nowhere | `findings/01-a-market-structure.md` §7, `findings/01-c-methods.md` (§1.2, §2, §3.6, §9.3) | `00-data-situation.md` numbers Gaps 1–4 and then adds "two smaller ones" unnumbered, so no file says what Gap 5 was meant to be. A correction could only either invent a definition or delete five forward references, and this pass does neither. It needs the author's intent or a one-line decision from the operator. |
| Class discipline: `01-b` §3's identifiability ledger has no Class column; `01-a` §6–§7 unclassed; `01-d`'s E-1 table and §4–§8 unclassed; `01-c` §1.1 and §1.2 unclassed; `02-c` E1/E2 and `02-e` E1 use "verified", which `records/README.md` does not define | five findings files | Appending cannot put a class on a table row or a paragraph: that is a per-claim judgement about what each conclusion rests on, and doing it from here would be assigning evidence classes I did not weigh. It is the largest remaining defect in the corpus and the one most likely to matter at review. |
| Zero DOIs, zero URLs, four ticket-market papers cited from memory, an NBER working paper with no number | `findings/01-d-external.md` | Adding locators is new sourcing, not the correction of a false statement, and every locator would have to be verified before it went in. The file states its own limitation honestly, which is why the verification ranked it a registry problem rather than a fabrication. |
| The prize sizing at 1.4–3.4% of primary revenue rests on a late-window mean | `findings/01-a-market-structure.md`, inherited by `01-c` | `02-a` item 11 makes the argument and no file has overturned `01-a`'s number. Changing it is a conclusion change on a live conflict (C4 in the verification), not the correction of a defect. Recorded in the ledger's contradiction section. |
| The Gap 1 diagnosis and the asking-versus-realised conflict (C2, C3) | `01-b` §5 against `00-data-situation.md` §4 | Already recorded as open contradictions in `A-research-ledger.md` and resolved in `02-c` for C2 only. Settling them is a research call, and `02-c` shows it needs a new object named, not a correction appended. |
| "2166 is the **end page**" | `findings/00-adversarial-review-phase1.md` | The Federal Register record (2024-30293, pages 2066–2167) was not re-fetched in this pass, so the verifier's own imprecision is recorded in `00-verification-round1.md` §1 and left there rather than restated as a correction on my authority. The neighbouring `90 FR 2066` finding stands. |
| `01-a` §2 "level ≈1.3-1.5× face" as a range around a 1.41× point estimate | `findings/01-a-market-structure.md` | It is a synthesis, not a misquote, and the same file's §2 table carries the paper's point estimate. Correcting it would mean choosing a range on no source. |
| `01-a`'s "16 CFR Part 464, 90 FR 2166" | `findings/01-a-market-structure.md` §1, §7 | Correct in substance and correct as the eCFR "Source" line, which is what the file is citing. The register page is 2066. The ledger-verification already records the distinction; a further correction would add noise without changing a claim. |

---

## 4. Questions this pass opened and did not resolve

1. **Is there a peer-reviewed study of resale price caps in ticket markets?** `01-b` §4.5 says it found no
   peer-reviewed *econometric* study, and `C-variable-registry.md` C-3 says no peer-reviewed *study*, which is
   the broader claim. `01-a` §3 already cites He & Lin, *Marketing Science* 45(3):515–533 (2026), "Price Caps
   by Matching Platforms: The Case of Ticket Resales". Whether that is an econometric study or a model of
   matching decides whether the broader sentence is false. This pass read its Crossref record and not the
   paper, so it asserts nothing and changes no conclusion. Whoever reads the paper should settle it, because
   it bears on "no class-A claim about caps may appear in the deliverable".
2. **The 14-of-128 redemption count.** The record cannot say whether 14 `redeem` rows are 14 tickets. Settling
   it needs a ticket-level status count, which is a fixture read the programme's own rule discourages.
3. **Two verifier overstatements**, both recorded in the files they affect rather than propagated: the
   "+155%" upper end of the cold-start band (correct value +153% from this file's own inputs), and the claim
   that `03-b` inherits both author errors (its Mason entry is correct; its Fosse & Winship entry is wrong in
   three fields, more than the verifier said).

---

## 5. Files touched by this pass

Appended, never rewritten: `findings/01-b-identifiability.md` (3 corrections), `findings/01-a-market-structure.md`
(3), `findings/00-ledger-verification.md` (1), `findings/00-adversarial-review-phase1.md` (1),
`findings/02-e-cold-start.md` (2), `findings/01-d-external.md` (1), `findings/02-a-price-paths.md` (1),
`findings/03-b-temporal-correctness.md` (1), `C-variable-registry.md` (1), `A-research-ledger.md` (1 correction
plus the "Corrections applied" block). Written new: this file.

Nothing was committed. Nothing was pushed. No file outside `records/` was edited.

---

## 5. Records tidy-up — 2026-11-07T12:55Z

**Trigger.** A records tidy-up pass over four defects a reader meets in the first ten minutes. **Scope.** Four
items, `records/` only. Nothing was committed or pushed, and no file outside `records/` was read for evidence or
edited.

**Rules this pass worked under.** Append-only in every finding; in place only in the index files
(`A-research-ledger.md`, `00-data-situation.md`, `F-decision-log.md`, `DELIVERABLE.md`), where a stale
pointer is the defect. No finding's conclusion was rewritten. Every quoted sentence below is copied from the
file as it stands; nothing is paraphrased into quotation marks. No source was invented: the one bibliographic
check made in this pass was a Crossref query whose returned record is printed in full.

### 5.1 The four defects

| # | Defect | File | What was wrong | What changed |
|---|---|---|---|---|
| 1 | P1.C stale in the ledger | `A-research-ledger.md` | The row read `dispatched`, finding "No finding yet … 28-byte placeholder reading `# Phase 1-C — placeholder`", class `—`, while `findings/01-c-methods.md` had been complete on disk since 11:09Z (1,558 lines, mtime 12:03Z). The row was true at 10:59Z and stale by 11:09Z. | Row now `answered`, with the conclusion taken from `01-c`'s own §1 and §1.3: **"Three of the eight families ship code for a quantity this observation set actually identifies, two ship the decision structure and no number, and three ship reasons not to build; no family converts an unidentifiable target into an identifiable one — 'a method is not a substitute for an observation'."** Class cell now records that the file states no single class and is per-family A/B/C/D (A only where inherited from `01-a`/`01-b`), with §1.1 and §1.2 unclassed — the same convention the P1.D row already uses. File cell is the path. Header re-dated. A dated line below the table says the V1 row's "three rows said `dispatched` while their files were on disk" is history, not the current state. |
| 1b | The rest of the ledger, checked row by row | `A-research-ledger.md` | Nine other rows. Seven were right as printed. | **No correction needed and none made.** P0.1–P0.5 cite `00-data-situation.md` §1–§5, all of which exist and say what the rows say. P1.A, P1.B and P1.D were already `answered`/`answered-partial` with a conclusion and a path, and their one-liners match §"What I concluded" in `01-a`, `01-b` and `01-d`. V1 cites `00-ledger-verification.md`, which exists. **One observation recorded rather than fixed:** the ledger indexes none of the thirteen files under `findings/` that are not one of its own rows — `00-adversarial-review-phase1`, `00-verification-round1`, `02-a-price-paths`, `02-ai-ml-decision`, `02-b-cap-truncation`, `02-c-sale-hazard`, `02-d-elasticity-fees-optimum`, `02-e-cold-start`, `02-rubric-and-scoring`, `03-a-interactions`, `03-b-temporal-correctness`, `06-validation-protocol`, `07-engine-review`. Ten of those are Phase 2 and Phase 3 findings that landed after 10:59Z. That is a missing-row defect, not a wrong row, and closing it means writing a conclusion for each of ten files, which is a different job from this one. See §5.4. |
| 2 | "Gap 5" cited and defined nowhere | `00-data-situation.md` §4 (definition), plus the two files that called it open, `A-research-ledger.md` and `DELIVERABLE.md` | Eight sentences in three files referred to a "Gap 5" that no file numbered, and four other files reported the dangling reference. `00-data-situation.md` numbered Gaps 1–4 and then listed "Two smaller ones, recorded for completeness" unnumbered. | **Defined, not replaced.** A fifth gap now sits in §4 in the same style as Gaps 1–4: **Gap 5 — no primary inventory time series, therefore no sell-through velocity** — `totalSupply`/`issuedCount` are a snapshot with no capture time, `Event.status` has no transition timestamps, so the sell-through *level* is observable and the *path* is not. It states what the gap does **not** do (it does not delete the demand bracket, which `01-b` §5 identifies at the level) and its minimal fix (a timestamped per-tier series plus the four status transition times, explicitly **not** among Gap 1's four listing fields). All eight citations were read for referent first: all eight mean this and nothing else, so no forward reference was rewritten — defining the label once is the smaller change than rewriting eight. They are tabulated in `00-data-situation.md` §4 with the sentence at each site: `01-a` §7; `01-c` §1.4(3), §2 ("Data"), §3.6, §9.3 ("Data"); `B-mathematical-kb.md` §6.4, §6.5, §9 diagram. No citation in `docs/`: a grep over `docs/*.md` finds "Gap 2" once (`ON-CHAIN-DESIGN.md:71`) and no "Gap 5". |
| 3 | He & Lin against "no peer-reviewed cap study" | `findings/01-a-market-structure.md` (NOTE appended), `C-variable-registry.md` C-3 (one-paragraph dated NOTE) | `01-a` §3 cites He & Lin for a cap proposition labelled class C; `01-b` §4.5 says "I found no peer-reviewed econometric study of resale price caps in ticket markets" and forbids any class-A cap claim; `C-variable-registry.md` C-3 restated that more broadly as "no peer-reviewed study". The contradiction had been noticed twice and resolved neither time. | **Both files are right about different objects, so neither got a correction; `01-a` got the note the brief asks for.** `01-a` NOTE 2026-11-07T12:55Z quotes both passages verbatim and shows the two claims are about different predicates: a peer-reviewed **model** of price caps with a class-C label does not contradict the absence of a peer-reviewed **econometric study**, and `01-a` nowhere claims an empirical measurement exists. The rule "no class-A claim about caps may appear in the deliverable" is therefore unaffected. One sentence in the records *is* falsified by this: `C-variable-registry.md` C-3's broader "no peer-reviewed study … was found", which now carries a dated note narrowing it to `01-b`'s wording. The Crossref record for `10.1287/mksc.2023.0623` was re-queried and printed in the note: type `journal-article`, "Price Caps by Matching Platforms: The Case of Ticket Resales", Da He & Song Lin, *Marketing Science* 45(3):515–533, issued 2026-05, abstract "analyzing their adoption incentives and effects on prices, sales, profitability, and welfare". **The abstract does not say whether the analysis is econometric or a model, so nothing about the paper's method is asserted.** |
| 4 | `F` D3 recorded Gap 1's diagnosis as settled | `F-decision-log.md` D3 | D3's Evidence line carried the Phase 0 audit's reading — "the sale count is a numerator with no exposure denominator" — as settled, while `01-b` §5.1 and `02-c` §2.1 refine it and `A-research-ledger.md` already said F carried the audit's version as "the failure `records/README.md` forbids". | **A dated note appended under D3, and nothing resolved.** The note quotes all three positions verbatim — audit: a numerator with no denominator; `01-b`: "The denominator is present — every ticket has an `issue` row and a known life. The unobserved object is the ask of the risk set"; `02-c`: "the intensity of a **composite process — offered, then bought** — marginalised over the unrecorded offering state", and "'a numerator with no denominator' is the wrong diagnosis of the same defect — the denominator exists, it is the denominator of the wrong process." It records that **the data request is unchanged by the dispute** (the four fields, quoted from D3, stand as printed), that only the diagnosis and therefore the severity of the baseline-intensity claim are contested, and that this file does not pick a reading. D3's **Decision** line is untouched. |

### 5.2 Counts

**Four defects, plus one extension (1b) and one stale-pointer cleanup in `DELIVERABLE.md`.** Files edited:
**6**, all under `records/` — `A-research-ledger.md`, `00-data-situation.md`, `findings/01-a-market-structure.md`,
`C-variable-registry.md`, `F-decision-log.md`, `DELIVERABLE.md` — plus this file.

### 5.3 Where each Gap 5 citation lives

`01-a-market-structure.md` §7 (1); `01-c-methods.md` §1.4(3), §2, §3.6, §9.3 (4); `B-mathematical-kb.md` §6.4,
§6.5, §9 diagram (3). Total 8 forward references, all meaning the primary inventory time series. In addition,
7 sites *report* the dangling label rather than use it and keep their histories unchanged:
`A-research-ledger.md` (2, both now carrying dated resolution lines), `00-ledger-verification.md` §3,
`00-verification-round1.md` §3 and item C5, `00-adversarial-review-phase1.md` (3), this file §3 and §4,
`DELIVERABLE.md` §20.5.

### 5.4 What this pass could not settle

1. **Whether He & Lin is an econometric study.** The one question that decides whether `01-b` §4.5's first
   sentence is true of that paper. Needs the full text; not read here, and nothing was asserted about it.
2. **Thirteen files under `findings/` are still unindexed in `A-research-ledger.md`**, ten of them Phase 2 and Phase 3 findings written after the ledger's last update. The ledger's own
   header says it indexes every research question and its rows number 10, all Phase 0/1 plus the verification
   pass. Adding rows is writing a conclusion per file, which is out of scope for a tidy-up and was left alone
   rather than half-done.
3. **`records/README.md` describes `DELIVERABLE.md` as "a stub … it is not written yet".** The file is 199KB and
   written through §21. That is a stale index pointer of the same kind as defect 1, found while working here and
   not part of the four, so it is recorded and not changed.

---

# Corrections applied — verification round 2

**Status:** complete. **UTC:** 2026-11-07T14:00Z. **Agent:** corrections pass, round 2.
**Trigger:** `records/findings/00-verification-round2.md` (2026-11-07T13:50Z), an independent check of round 1's
corrections, of the four protection tests those corrections were meant to establish, of `09-sim-recovery.md`,
and of `DELIVERABLE.md` §20–§22.
**Scope:** exactly what that file names, in the order it names it. Nothing outside `records/` was read for
evidence or edited. No code was touched. Nothing was committed or pushed.

**Why there was a round 2.** Round 1's corrections were right in substance (11 of 16 held, 5 right in substance
with a defective detail, 0 new falsehoods about a source) and the protections failed anyway: nine false
statements sat in records no correction reached, and twelve more were corrected only on the last page of the
file that still asserted them in the body. The verifier's sentence is the one this pass was written to answer:
*"the section and the file disagree until the tail is read."*

## 6. The two marking rules, and which was used where

**Rule A — inline marking.** The false sentence is struck where it stands and carries a dated one-line marker
(`**[CORRECTION 2026-11-07T14:00Z, R2-n — dead: <what is true in one line>. <pointer>]**`). Used wherever a
reader would otherwise believe a false sentence mid-argument and the correction fits in a line or a short
bracket. Nothing is deleted: the text stays visible, struck, so the history of the defect survives in the place
the defect was made.
**Rule B — appended or newly written prose.** The correction is a block (§) carrying the argument, the arithmetic
or the quoted source. Used where a one-liner would mangle a derivation or a table, where the correction needs
counts the reader should be able to check, or where the file is an index or the deliverable and a block is the
only place the correction can live without rewriting what it corrects.

Every mark carries a UTC ISO-8601 date and the word CORRECTION. Every number is quoted from a named source in
this repository or shown as arithmetic on one; no number in this pass comes from `lib/mock/`.

## 6.1 Round-2 defects, one row per site

| # | File | The wrong sentence (quoted, trimmed) | What is true | Verifier's finding | Rule |
|---|---|---|---|---|---|
| R2-1 | `findings/01-b-identifiability.md` §4.1 | "only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of an already-selected subset" | 90 is a `sale` **row** count. `00-data-situation.md` §2: 253 rows (128 `issue` + 90 `sale` + 21 `transfer` + 14 `redeem`) and 79 of 128 tickets with no sale, so **49** tickets sell (128 − 79) and 41 sold more than once. It is also a fixture figure doing argumentative work, which the audit bars | §1 item 1, (c); §2.1 row 1; §5 B10 | A |
| R2-2 | `findings/01-b-identifiability.md` §4.3 item 2 | "14 of 128 tickets redeem" | 14 is a `redeem` row count; the record carries no ticket-level redemption count, and the programme's rule forbids producing one from the fixture | §1 item 2; §2.1 row 2; §5 B11 | A |
| R2-3 | `findings/01-b-identifiability.md` §4.3 item 3 | "fits 79-of-128 better than a long tail" | The fraction is a recorded property of the fixture, so it cannot choose a specification. The cure component stands on censusing and Boag (1949) | §2.1 row 3 (named, not withdrawn) | A |
| R2-4 | `findings/01-b-identifiability.md` §4.6 | "so 79-of-128 is an upper bound on the never-*offered* fraction" | Same rule: a fixture fraction bounds nothing about tickets offered on the platform. The attenuation direction stands on Bollinger (1996) and Aigner (1973) | §2.1 row 4 (named by no correction) | A |
| R2-5 | `findings/00-ledger-verification.md` §3, "Confirmed wrong as cited" | the S-prefixed Aigner DOI "returns HTTP 404 … the single unresolvable citation in the records" | `01-b` does not contain that string. Both its Aigner occurrences are the resolving form; the only `S0304-4076` DOI in the file is Bollinger's. The 404 was real but was run on an input that is not in the file | §1 items 8–10, (c); §2.2 | A |
| R2-6 | `findings/00-ledger-verification.md` P1.C row (verdict and correction cell) | "No `01-c*` file exists"; "`dispatched` is correct here" | `01-c-methods.md` exists, complete, 1,558 lines, written 10:57Z–11:09Z. The row was a 10:55Z observation, true then, stale four minutes later | §5 A6 | A |
| R2-7 | `findings/00-ledger-verification.md` §3 opening | "Every DOI … resolves … with one exception" | No DOI fails to resolve. Two printed **author sets** do not match Crossref, which is a printing error inside a resolving record | §1 item 8 note | A |
| R2-7b | `findings/00-ledger-verification.md` closing list item 6 | "One unresolvable citation and one mis-cited register page are the only bibliographic failures" | One failure, the register page. The other real defect is `01-b` §7's two printed author sets | §1 items 8–10 | A |
| R2-8 | `findings/01-c-methods.md` §1.4(1) | "**01-b §4.4(ii) overstates the cap as an instrument.** It says `resalePriceCapBps` 'varies … across tiers within an event …'" | The quoted sentence is §5.3 item 3's. §4.4(ii) says the opposite — "its **absolute level** differs across tiers within one event" — and is already correct. **The argument survives the correction:** it turns on the wire contract (`resalePriceCapBps` is one field on `Event`), not on which section got it wrong, and §5.3 is the section that awards identifying variation. No conclusion in `01-c` changes | §2.3; §5 A2 | A |
| R2-8b | `D-model-registry.md` C6 | "`01-b` §4.4(ii) treats the cap as an instrument with cross-tier variation" | Same mis-attribution, same correction; §4.4(ii) uses cross-**event** cap variation. C6's conclusion was never resting on it | §2.3; §5 A3 | A |
| R2-9 | `A-research-ledger.md` defects list | "`01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404" | It does not. No unresolvable DOI, so no citation defect there | §1 item 10; §2.2; §5 B21 | A |
| R2-9b | `A-research-ledger.md` fixture bullet | the fixture-count bullet as written | The count is right and the bullet stands as a defect record; the four fixture sentences in `01-b` are now marked dead in that file, not only in its tail | §2.1 | A |
| R2-9c | `A-research-ledger.md` V1 row | "one unresolvable DOI and two wrong fixture counts" | No unresolvable DOI. Of the two fixture counts, one was wrong (90 rows read as tickets) and one is a row count whose ticket count the record does not establish | §1 item 10 | A |
| R2-10 | `findings/09-sim-recovery.md` summary heading | "**The three failures first**, because they are the result" | Five conditions failed (`B.pooled_width`, `B.declared_matched`, `B.width_shrinks`, `C.cap_direction`, `C.cap_magnitude`), six of the 43 condition-lines; 43 − 6 = 37 held, the printed count | §3.3 | U+A |
| R2-10b | `findings/09-sim-recovery.md` summary | the list omits a failed condition | The omitted failure is `B.width_shrinks` in the 0.20 arm: pooled width 0.8328 / 0.7329 / 0.9982 at J = 2 / 5 / 20, which falls then jumps because the variance switches from a declared 0.04 to an estimated 0.09 at nine events | §3.3 | A |
| R2-11 | `findings/09-sim-recovery.md` summary item 2 | "**B, the default declared tau**" listed as a failure | Not a failed condition: the log prints `B.declared_default` **PASS** at J = 2, 5 and 20, because the condition was pre-declared as a predicted failure ("coverage at declared=0.20 is < 0.87"). The numbers 0.620 / 0.694 / 0.718 are the log's and are right | §3.3 | A |
| R2-11b | `findings/09-sim-recovery.md` summary item 3 | one condition named | Two failed here: `C.cap_direction` and `C.cap_magnitude` ("relative attenuation" −0.131 at s=0.40, −0.085 at s=0.70) | §3.3 | A |
| R2-12 | `findings/01-b-identifiability.md` §5.3 item 3 | "across events and across tiers within an event … so the cap is an instrument" | `resalePriceCapBps` is one field on `Event`; only the implied ceiling varies, as face × (1 + c), collinear with face. Cross-event instrument only | §5 B12 | A |
| R2-13 | `DELIVERABLE.md` §11.1, last row | "a price-distribution coverage number … **not available and must not be simulated into existence**" | True of a price distribution and now too strong unqualified: `09-sim-recovery.md` reports coverage of the **declared band on an event's mean** (0.805 at J=2; 0.620 / 0.694 / 0.718 at the default tau). Class SIM, not calibration | §4.3 item 2; §5 A9 | A |
| R2-14 | `DELIVERABLE.md` §8.2 | "The evidence that would validate it is a SIM recovery study and, on a real ledger, …" | The study exists and did **not** validate the band: 0.805 at two events against `[0.87, 0.93]`. A SIM study can only test an estimator against its own assumption, so it was never the validating evidence; the real-ledger half stands | §4.3 item 2; §5 A9 | A |
| R2-15 | `findings/01-a-market-structure.md` §3 | "He & Lin (*Marketing Science*, **2025**)" | Crossref for `10.1287/mksc.2023.0623`: 45(3):515–533, issued 2026-05 | §1 item 7; §5 B15 | A |
| R2-15b | `findings/01-a-market-structure.md` §7 reference | "He, D. & Lin, S. (2025). *Marketing Science*." | 2026; 45(3):515–533. DOI is right | §1 item 7 | A |
| R2-16 | `findings/01-a-market-structure.md` §3 | "≈£184 gross average, ≈£269 per resale ticket inclusive of all fees" | 350 / 1.9 = 184.2, so £184 follows. £269 is £404m / 1.5m, a second flow; 269 × 1.9 = £511m, not £350m | §1 item 6; §5 B14 | A |
| R2-17 | `findings/01-a-market-structure.md` §4 | "1.4% of primary revenue, **even after scaling for** the ~50% of resale the authors do not observe" | The paper: "1.4% … even if we are accounting for only half of resale activity". 1.4% is the observed half, unscaled; "even after scaling" inverts the caveat | §1 item 5; §5 B13 | A |
| R2-18 | `findings/01-d-external.md` "What I concluded" | "Nineteen candidate variables were examined … and eleven survive at usable priority" | 28 examined (17 + 11 rejected), 9 at priority 1–2 (4 obtainable today), 15 above 0. Eleven is the reject count. The tables are the artefact | §1 item 13; §5 B16 | A |
| R2-19 | `findings/02-e-cold-start.md` §4.7 table header | "as markup around face" with "−49% to +95%" | The column is exp(±1.645τ) − 1, the percentage move in the point estimate. As markup over face centred at 0.261 the last row is −33% to +153% | §1 item 11; §5 B17 | A |
| R2-19b | `findings/02-e-cold-start.md` E8 | the same claim in the evidence table | Same; the arithmetic stands, the object named was wrong | §1 item 11; §5 B17 | A |
| R2-20 | `findings/02-a-price-paths.md` reference list | "Mason, K. O., Mason, W. M., **Winship, C.** & Poole, W. K. (1973)" | Crossref: third author **Winsborough, H. H.** Titles, journal, volume and pages right | §1 item 4; §5 B18 | A |
| R2-21 | `findings/02-a-price-paths.md` reference list | "**Luo, L. (2019).** Analyzing age-period-cohort data" | Fosse, E. & Winship, C. (2019), same title, journal, volume, pages and year | §1 item 15; §5 B19 | A |
| R2-22 | `findings/03-b-temporal-correctness.md` reference list | "[Luo 2019] Luo, L. (2019). **Bayesian age-period-cohort analysis**. *Annu. Rev. Sociol.* 45, **109–132**" | Fosse & Winship (2019), "Analyzing Age-Period-Cohort Data: A Review and Critique", 45:467–492. Author, title and pages wrong; volume and DOI right | §1 item 16; §5 B19 | A |
| R2-23 | `records/README.md` | "**It is a stub and says so at the top: it is not written yet.**" | `DELIVERABLE.md` is 210,575 bytes at this pass's count, §1 to §22 plus a closing note, and its header says it is the Phase 8 document rather than a table of contents for one | §4.3 item 3; §5 A1 | A |
| R2-24 | `DELIVERABLE.md` §20.5, He & Lin bullet | "Whether the sentence is false depends on whether that paper is an econometric study … which nobody has read" | The clause needing no reading is settled: a peer-reviewed paper on resale caps *was* found, so C-3's broader sentence is false and is dead there. Whether it is econometric is still unread | §4.2; §5 A8 | A |
| R2-25 | `C-variable-registry.md` C-3 | "varies across tiers within one event because it is bps over each tier's own face" | One field on `Event`; only the money ceiling varies, collinear with face. No within-event identifying variation | §1 item 14; §5 A4 | A |
| R2-26 | `C-variable-registry.md` C-3 | "because no peer-reviewed study of resale price caps in ticket markets was found" | One was found and `01-a` §3 cites it: He & Lin (2026), *Marketing Science* 45(3):515–533. The surviving claim is `01-b` §4.5's "no peer-reviewed **econometric** study"; whether He & Lin is econometric is unread | §1 item 14; §5 A5 | A |
| R2-26b | `C-variable-registry.md`, the 12:55Z NOTE | "read C-3's evidence clause as `01-b`'s" | The NOTE was an instruction under a sentence that still read the other way; a note below a sentence cannot amend it. The clause is now struck, which is what the NOTE asked for | §1 item 14 | B |
| R2-27 | `findings/00-adversarial-review-phase1.md` notes on the prior pass | "the Aigner DOI (I re-checked Crossref: the `S`-prefixed DOI returns 404, the corrected one 200)" | The check is real, the attribution is not: `01-b` contains no S-prefixed DOI | §2.2 | A |
| R2-28 | `DELIVERABLE.md` §22 | "Full bibliography … Deduplicated from the sources the findings cite" | Ahn & Lee (2007), *IJFS* 2(2):79–93, doi:10.1177/155862350700200203, cited at `02-d` lines 839-840, was missing (added as entry `1a`). Five `Used by` cells named a file that does not cite the source: Artzner→06, Ekeland→02a, Gallego→01a, Lakkaraju→01c, DBT→02e. Cells now name only citing files, checked by searching every file under `records/findings/`. Counts 123→124 and 161→162, with the arithmetic shown | §4.1; §5 A7 | B |
| R2-29 | `DELIVERABLE.md` §20 | §20 did not mention the simulation study at all | New §20.6: coverage 0.805 at J=2 against the declared `[0.87, 0.93]`; 0.620 / 0.694 / 0.718 at the default τ = 0.20 against a true 0.30; RMSE 1.0425 in a 40–60-day window with no conditioning guard; and the cap's upward bias on the curvature, which corrects the reading of `02-a` C1. Class SIM throughout, with what the study cannot support stated | §4.3 item 1 | B |
| R2-30 | `DELIVERABLE.md` §20.5 status note and §21.2 row | "The He & Lin question **is settled** … C-3's broader 'no peer-reviewed study' **is narrowed to `01-b`'s wording there**" | Nothing narrowed it, and the question is open: §21.2 said so in the same document. §20.5 now says the question is open and C-3's sentence is dead as printed; §21.2's row is worded to match | §4.2; §5 A8 | B |
| R2-31 | `DELIVERABLE.md` §20.5 list | the list omitted the README staleness | Added as an eighth bullet: an index that misdescribes its own deliverable is a limitation of the record | §4.3 item 3 | B |

**Note on R2-10.** That row used both rules: the two false sentences in the summary are struck in place and the
reconciliation — because it needs the declared conditions quoted and the 43-line arithmetic shown — is appended
in a block. It is the only defect in this pass that needed both.

## 6.2 Counts

- **Rule A, struck in place:** 32 marks across 15 files.
- **Rule B, appended or newly written prose:** 8 blocks — 4 appended correction blocks in findings (`01-b`,
  `00-ledger-verification`, `A-research-ledger`, `09-sim-recovery`), 1 note appended inside an existing note
  (`C-variable-registry` C-3), 1 new subsection (§20.6), 1 corrected status note (§20.5), and 1 corrected table
  with its correction paragraph (§22).
- **Total items:** R2-1 to R2-31 with nine sub-items (R2-7b, R2-8b, R2-9b, R2-9c, R2-10b, R2-11b, R2-15b,
  R2-19b, R2-26b), i.e. 40 dated marks. One site, R2-10, is corrected by both rules.
- **Of the verifier's list:** all nine §5-A false statements and all twelve §5-B ones are marked; four
  protection-test sites from §2.1 are added (two of which no earlier correction had named); §3.3's framing
  defect and §4's four §22/§20 defects are corrected. Nothing the verifier did not name was changed, except one
  count inside round 1's own CORRECTION 1 (the "one of two places" tally, which §1.1 of the verification says is
  wrong in two documents) and a grammar repair where a strike crossed a sentence boundary.

## 6.3 Files touched

`records/findings/01-b-identifiability.md`, `records/findings/00-ledger-verification.md`,
`records/findings/00-adversarial-review-phase1.md`, `records/findings/01-c-methods.md`,
`records/findings/01-a-market-structure.md`, `records/findings/01-d-external.md`,
`records/findings/02-e-cold-start.md`, `records/findings/02-a-price-paths.md`,
`records/findings/03-b-temporal-correctness.md`, `records/findings/09-sim-recovery.md`,
`records/A-research-ledger.md`, `records/C-variable-registry.md`, `records/D-model-registry.md`,
`records/README.md`, `records/DELIVERABLE.md`, and this file. **Fifteen files plus this one.**

Nothing outside `records/` was edited. No code was touched. Nothing was committed or pushed. No fleet path was
read or written.

## 6.4 The one defect this pass could not fix without changing a conclusion

**The He & Lin question.** `C-variable-registry.md` C-3's broader sentence is now dead, because a peer-reviewed
paper on resale price caps in ticket markets exists and is cited in this programme. What cannot be settled from
the record is whether that paper is an **econometric** study, and that single unread fact decides two live
sentences in opposite directions:

- if He & Lin is econometric, `01-b` §4.5's "I found **no peer-reviewed econometric study** of resale price caps
  in ticket markets" is false, and with it the rule it supports — "no class-A claim about caps may appear in the
  deliverable";
- if it is a matching model, `01-b` §4.5 is true and `01-a` §3's class-C use of it is right, and only C-3 was
  wrong.

Closing it means either withdrawing `01-b` §4.5's first sentence or reclassifying `01-a`'s use — both are
conclusion changes on evidence nobody in this programme has read. This pass marked both sites, left both
conclusions standing, and recorded the question as open in `DELIVERABLE.md` §20.5 and §21.2. It is the one item
in the verification's list whose repair depends on something other than editing.

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

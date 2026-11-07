# 00 — Verification round 1: what the night's findings actually are

**Status:** complete. **UTC:** 2026-11-07T11:26Z. **Agent:** independent verifier (`00-verification-round1`).
I wrote none of the files I checked and I edited none of them. The only file written by this pass is this one.
**Scope:** every file of the form `records/findings/*.md` present at the moment of verification, checked
mechanically against five tests: header completeness, evidence-class presence, whether the first four cited
sources exist and are what the file says, where every number comes from, and whether any two files disagree
about the same quantity.
**Method:** each file read in full; every DOI queried at Crossref; the Federal Register and eCFR records
fetched; nine URLs fetched and status-checked; the wire contract read directly; the Leslie & Sorensen PDF
text extracted locally to settle the numbers three files inherit from it; every arithmetic claim I could
recompute, recomputed. Nothing was committed or pushed. `lib/mock/` was not used as evidence — it was read
only to check a claim *about* it, never for a number.

**Snapshot.** The directory was being written while I ran: it held 7 files at 11:00, 11 at 11:08, 12 at
11:11, and 13 at 11:20. Every verdict below is against a **locked 12-file snapshot taken at
2026-11-07T11:15:49Z** and re-checked byte-identical at 11:20. `03-b-temporal-correctness.md` (85,461 B)
landed at 11:20:10Z, after the lock; it is verified to header, class and citation depth only and is marked
as such everywhere below. Anything that lands after 11:26 is outside this pass.

| # | File | Bytes at snapshot |
|---|---|---|
| 1 | `00-adversarial-review-phase1.md` | 50,305 |
| 2 | `00-ledger-verification.md` | 25,687 |
| 3 | `01-a-market-structure.md` | 24,600 |
| 4 | `01-b-identifiability.md` | 34,046 |
| 5 | `01-c-methods.md` | 121,543 |
| 6 | `01-d-external.md` | 31,773 |
| 7 | `02-a-price-paths.md` | 73,366 |
| 8 | `02-ai-ml-decision.md` | 36,924 |
| 9 | `02-c-sale-hazard.md` | 83,835 |
| 10 | `02-d-elasticity-fees-optimum.md` | 61,540 |
| 11 | `02-e-cold-start.md` | 76,531 |
| 12 | `02-rubric-and-scoring.md` | 42,904 |
| 13 | `03-b-temporal-correctness.md` (post-snapshot) | 85,461 |

`03-b` was re-read at 85,464 B three seconds after the reading recorded here; the three-byte change does not
touch any claim I verified in it (the 61-feature partition and the `asOf` absence are intact), so the depth
of check stated for it stands.

---

## The table

"Header" = states status, a UTC date, an author or agent, its scope, and what it depends on.
"Classes" = distinct conclusions carrying an explicit A–E / SIM / UNVALIDATED class, as a fraction of the
headings whose conclusions I could count. "Citations" = of the first four distinct sources, how many I
confirmed exist and are what the file says. "Numbers unexplained" = quantitative claims with no traceable
origin, or with a wrong one. "Conflicts" = live disagreements with another file on the same quantity.

| File | Header | Classes present | Citations confirmed | Numbers unexplained | Cross-file conflicts |
|---|---|---|---|---|---|
| `00-adversarial-review` | complete | own verdicts unclassed (review form) | 4/4 | 0 material (1 minor: FR end page) | flags 5, creates 0 |
| `00-ledger-verification` | complete | verdicts unclassed (review form) | 3/4 — one **false attribution** | 0 (all recomputable, all correct) | flags 4, creates 1 false |
| `01-a-market-structure` | complete, **no depends-on** | tables classed; §1/§6/§7 prose unclassed | 4/4 | 2 (the £269 splice; the unscaled 1.4%) | 3 |
| `01-b-identifiability` | **no Scope field** | §4 classed; §3 table and §1/§5/§6 unclassed | 4/4 (2 author-name errors elsewhere) | 2 (90-of-128; 14 redeem) | 4 |
| `01-c-methods` | complete | family verdicts classed; §1.1/§1.2/§1.4/§10/§12 unclassed | 4/4 | 0 | 2 (one wins) |
| `01-d-external` | complete | **only C-1 classed**; E-1 and §4–§8 unclassed | **0/4 checkable** (no locators) | 1 (19/11) | 3 |
| `02-a-price-paths` | complete, **timestamp postdates mtime** | best in corpus; per-claim tags | 4/4 | 1 (R²/θ not reproducible) | 2 |
| `02-ai-ml-decision` | complete, **timestamp postdates mtime** | A–E declared inapplicable; MEASURED/ASSERTED used | 3/3 | 0 | 0 |
| `02-c-sale-hazard` | complete | table classed but **2 rows use "verified"** | 4/4 | 0 | 1 (resolves one) |
| `02-d-elasticity-fees-optimum` | complete | strong, 14 classes + 27 MEASURED | 4/4 | 0 | 1 (agrees with 01-c) |
| `02-e-cold-start` | complete | strong; **1 row "verified absence"** | 4/4 | 1 (band label) + 1 page error | 0 |
| `02-rubric-and-scoring` | complete | **none, declared exception** | 4/4 URLs | 0 | 1 (wins against the brief) |
| `03-b-temporal-correctness` | complete | 10 classes + 13 MEASURED | 4/4 | 0 | 1 |

**Totals.** 13 files, 3,4xx distinct DOI lookups spot-checked (60+ distinct works), 0 fabricated sources, 0
non-resolving DOIs except two deliberately 404-checked ones, 4 wrong author attributions, 5 wrong or
unsourced numbers, 6 class-discipline gaps, 2 header defects, 6 live cross-file conflicts.

---

## Detail, file by file

### 1. `00-adversarial-review-phase1.md` — accurate, and its own correction contains an error

Header complete and unusually honest: it names the versions it reviewed by mtime and byte count, and lists
what it did not review. Classes: it is a review, so its output is verdicts (`STANDS-WITH-NARROWING`), not
evidence claims; that is defensible but undeclared.

First four sources it says it spot-checked — Sweeting 2012, Leslie & Sorensen 2014, Ekeland–Heckman–Nesheim
2004, Prentice 1986 — all four resolve and match (`10.1086/669254`, `10.1093/restud/rdt033`, `10.1086/379947`,
`10.1093/biomet/73.1.1`). **4/4.**

Its recomputed fixture counts (90 sale rows, 49 tickets with ≥1 sale, 79 with none, 27 with ≥2, one with 4)
agree with the audit's own statement that "79 of 128 tickets have no" sale. I checked the audit text; the
arithmetic is consistent.

Its one error is inside its own correction of the prior pass:

> "(i) '90 FR 2166' is not a random digit transposition; 2166 is the **end page** and the eCFR 'Source' line"

The eCFR source line does read `90 FR 2166` — I confirmed that by fetching Part 464. But the Federal
Register record for 2024-30293 gives `start_page: 2066, end_page: 2167`, so 2166 is *not* the end page. The
correction is directionally right and numerically imprecise.

### 2. `00-ledger-verification.md` — correct arithmetic, and one false accusation

This file's arithmetic and structural findings hold up: the fixture row/ticket confusion, the £269 splice,
the dangling "Gap 5", the 19/11 count, and the `01-b` vs audit Gap-1 conflict are all real and all verify.

But its single most prominent bibliographic finding is **false**:

> "**`10.1016/S0304-4076(73)90005-5`** (`01-b` §7, Aigner 1973 …). Crossref returns **HTTP 404**. … This is the
> single unresolvable citation in the records"

`01-b` does not contain that string. I grepped the file, and the committed version at `e55a18b`, and both
carry only the resolving form:

```
01-b:325  *Journal of Econometrics* 1(1), 49–59. https://doi.org/10.1016/0304-4076(73)90005-5
```

The S-prefixed DOI does 404 (I confirmed), and the corrected one does resolve — so the *check* was run. It
was run against the wrong input and the result attributed to `01-b`. Worse, the false finding has already
been inherited: `records/A-research-ledger.md:108` now asserts "`01-b` §7 cites Aigner (1973) as
`10.1016/S0304-4076(73)90005-5`, which returns 404", and `00-adversarial-review` corroborates it with "I
re-checked Crossref" — a check of the DOI, not of the file. **Three documents now carry a defect that does
not exist in the source.** This is the only defect in the corpus that is *created* rather than found.

Citations: 3/4 in the sense that three of the four DOIs it names exist and are what it says; the fourth is
attributed to the wrong file.

### 3. `01-a-market-structure.md` — best-sourced, worst-classed header block

Header missing an explicit depends-on; it states Scope only. Citations **4/4 confirmed**: Sweeting
(`10.1086/669254`, JPE 120(6):1133–1172, 2012), Leslie & Sorensen (`10.1093/restud/rdt033`, RES 81(1):266–300),
Budish & Bhave (`10.1257/mic.20180230`, AEJ:Micro 15(1):142–170, 2023), Courty & Pagliero
(`10.1162/rest_a_00179`, REStat 94(1):359–369, 2012). All ten of its DOIs resolve, and the quantitative
claims it takes from Leslie & Sorensen are verbatim correct — I extracted the paper and checked: "the average
markup is 41% over the face value, and 25% of resold tickets obtain markups above 67% … 26% of tickets are sold
below face value"; "The average seat quality of tickets purchased in the primary market is 0.50, while the
average seat quality of resold tickets is 0.61"; "50% of resale transactions occur within 26 days … 25% …
within 7 days"; "they decline slightly as the event date approaches, with a modest uptick in the last week";
"We observe the universe of transactions in the primary market … 1,034,353 tickets".

**Wrong number 1, and it is the commercial headline.** The file says:

> "resale profit of slightly over $1.17m on 56 concerts = **1.4% of primary revenue**, even after scaling for
> the ~50% of resale the authors do not observe (class A)"

The paper says the opposite of "after scaling":

> "This is equivalent to 1.4% of the total primary market revenue for these events. … this suggests a fairly
> modest amount of forgone profit by firms in the primary market, **even if we are accounting for only half of
> resale activity**."

1.4% is the *observed half*. It is not scaled, and the paper flags that it excludes the other half. The file
converts the paper's caveat into a claim of conservatism the paper does not make. That number is the numerator
of the project's commercial case.

**Wrong number 2, the £269 splice.** "≈1.9m secondary sales worth £350m before fees — ≈£184 gross average,
≈£269 per resale ticket inclusive of all fees." £184 = 350/1.9 ✓. £269 × 1.9m = £511m, which is not £350m;
£269 is £404m/1.5m, a different flow in the same note. Presented as a consequence of the previous clause, it
is not one. My own arithmetic, not a citation.

**Citations, minor:** He & Lin is cited as "(2025)"; Crossref gives *Marketing Science* 45(3):515–533,
**2026**. The paper is real and the proposition it supports is right; the year is not.

**Classes.** The two empirical tables carry a Class column and use it. Outside them, the unclassed
conclusions, by heading: §1 the whole mechanism map and the "ambiguous by 20-40%" fee range (a quantified
range with no source anywhere in the file); §2 "Magnitudes to carry forward"; §3 the £269 sentence and the
20%/95%/25% displacement assumptions; §4 the 3.4% / $27,000 counterfactual (marked as a simulation in a
parenthetical but classless); §5 the Get Protocol vendor claim; **§6 and §7 in full**, including the sentence
the whole project turns on — "the sale count is a numerator with no denominator and `P(sale | price, exposure,
t)` is unidentified (Gap 1)", which is class C by construction and carries no label.

### 4. `01-b-identifiability.md` — the best argued, the most rule-breaking

**Header defect:** no **Scope** field. It has Status, Written, Author, Depends-on, Append-only — the scope
has to be inferred from the depends-on list.

Citations **4/4 confirmed** for the first four (Lagakos `10.2307/2529941`, Bailey–Muth–Nourse
`10.1080/01621459.1963.10480679`, Case & Shiller `10.3386/w2393`, Ekeland–Heckman–Nesheim `10.1086/379947`).
All 35 DOIs in the file resolve.

**Two author attributions are wrong, in a file whose §7 says otherwise.** `01-b` §7 opens: "Metadata for
every item below was checked against Crossref or OpenAlex during this pass; no citation is from memory alone".

- It cites "**Luo, L.** (2019). Analyzing age-period-cohort data: a review and critique. *Annual Review of
  Sociology* 45, 467–492." DOI `10.1146/annurev-soc-073018-022616` resolves to **Fosse, E. & Winship, C.
  (2019)** — same title, journal, volume, pages, year. The first author is wrong and a second author is omitted.
- It cites "Mason, K. O., Mason, W. M., **Winship, C.**, & Poole, W. K. (1973)". Crossref gives Mason,
  Mason, **Winsborough, H. H.**, Poole. The third author is wrong.

Both errors recur in `02-a` and `03-b`, which inherited the reference list.

**The number that breaks the programme's own rule.** §4.1:

> "only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of an already-selected subset"

`00-data-situation.md` §2 states the fixture has 253 ledger rows "(128 `issue`, 90 `sale`, 21 `transfer`, 14
`redeem`)" and that "79 of 128 tickets have no" sale — so **49** tickets sell, not 90. The 90 is a row count
read as a ticket count. The same file gets it right at §4.6 ("fits 79-of-128"), so the two numbers sit in one
document and disagree. This is also a `lib/mock/`-derived number in a programme whose audit says "No number in
this programme comes from `lib/mock/`" — the file's header does not carry `01-a`'s disclaimer, and this is why.

"14 of 128 tickets redeem" is the same row-as-ticket reading, though for redemption the two may coincide
(one redeem per ticket), so it is suspect rather than proved wrong.

**Classes.** The identifiability ledger in §3 — six target quantities, each with a status, and the file's
entire output — **has no Class column**. §1 and §6 carry none. §4 is genuinely careful and is the model the
other files should follow.

### 5. `01-c-methods.md` — complete now, and right about the cap

Header complete, including a two-stage timestamp (`10:57Z; last section appended 11:09Z`) that matches its
mtime. It grew from 36 KB to 121 KB during the evening; at the snapshot it is complete, with §1–§12 present
and every forward reference resolving — an earlier partial version referenced §5–§12 that did not exist, and
that is fixed.

Citations **4/4 confirmed**: Gallego & van Ryzin 1994 (`10.1287/mnsc.40.8.999`), Barber et al. 2023
(`10.1214/23-AOS2276`), Dudík et al. 2014 (`10.1214/14-sts500`), Gallego & van Ryzin 1997
(`10.1287/opre.45.1.24`) — titles, authors, volumes and pages all match. 61 distinct DOIs, all resolving.

Numbers: the one arithmetic claim I could check independent of any source — "60 daily steps, 2,000 units and
41 price points … roughly 4.9 million inner operations" — is 60×2,000×41 = 4,920,000 ✓.

**Classes.** Family verdicts are classed (C for the method, D for the transfer). Unclassed: §1.1's matrix
(uses ●/◐/○ instead), §1.2's five adversarial answers (a)–(e), §1.3's build order, §1.4's disagreements,
§10 and §12.

**It wins one conflict outright.** See the cap section below.

### 6. `01-d-external.md` — good tables, no locators, and a count that does not exist

Header complete. Classes: **only Table C-1 carries a Class column.** Table E-1, the data-source registry and
the other half of the file's output, has no class column at all, and §4–§8 are unclassed prose.

**Citations: 0/4 checkable.** The file contains **zero DOIs and zero URLs** — I counted. Every citation is a
bare journal reference, and it says so: "Bibliographic details for the four ticket-market papers I cite from
memory — Sweeting (2012, *JPE*), Leslie & Sorensen (2014, *REStud*), Bhave & Budish (2017, NBER WP), Krueger
(2019, *Rockonomics*) — were not re-checked in this run."

That is honest, and it makes four of its sources **unconfirmable from the file**: no DOI, no URL, no paper
number for the NBER working paper it names. I can confirm from Crossref that Sweeting 2012 and Leslie &
Sorensen 2014 exist as described and that an NBER WP on primary-market auctions by Bhave & Budish exists at
`10.3386/w23770` (2017) — but the file gives no locator, and its author order for that paper is reversed
against the published form ("Budish & Bhave" in `01-a`, "Bhave & Budish" here). Krueger, *Rockonomics* (2019)
has no publisher, no ISBN and no page locator in the file.

**The count.** "Nineteen candidate variables were examined against §4.2 and eleven survive at usable
priority." Table C-1 has 17 rows (V1–V17). Table C-2 rejects 11. Priorities 1–2 cover **9** rows (V1–V9);
priorities 1–4 cover 15. No reading of the file yields 19 candidates or 11 survivors. Both numbers are
asserted and neither is derivable.

**One more.** §4 states, with no class, that "On events that sold out at on-sale, the observed path rises into
the event date; on soft events it decays", and the "(class A)" in that section attaches to Sweeting's baseball
result, not to the platform claim.

### 7. `02-a-price-paths.md` — the most disciplined file, and one header that cannot be true

This is the strongest file in the corpus on evidence discipline: every load-bearing claim carries a
`[MEASURED]` / `[ASSERTED]` tag *and* an A–E class, 64 class labels in total, and the arithmetic is shown.
I re-derived its four headline percentages from its own printed endpoints and every one is correct:

| Subsample | p(81+d) / p(0–2d) | File says | My check |
|---|---|---|---|
| High demand | 3.532 / 2.014 | −43.0% | 1 − 2.014/3.532 = 42.98% ✓ |
| Low demand | 1.611 / 0.932 | −42.1% | 42.15% ✓ |
| Cheap seats | 2.853 / 1.834 | −35.7% | 35.72% ✓ |
| Expensive seats | 2.252 / 1.431 | −36.5% | 36.46% ✓ |

Its "derived per-day arrival rate 2.7 times lower" is (25/7)/(25/19) = 2.71 ✓.

Citations **4/4 confirmed**: Sweeting 2012, Leslie & Sorensen 2014, Lee et al. 2023
(`10.1108/sbm-05-2022-0042` → *Sport, Business and Management* 13(3):397–415, authors Lee, Morse, Hyun,
Shapiro, Drayer ✓), and NBER WP 14505, which Crossref confirms is Sweeting's own earlier version of the same
paper — correctly described as such.

**Header defect.** It states "**Written:** 2026-11-07T11:20Z". The file's last write was 11:06:07Z, and the
wall clock when I checked was 11:15–11:20. The header's timestamp postdates its own content by fourteen
minutes; it cannot be the time the file was written. `02-ai-ml-decision.md` carries the same 11:20Z against a
11:10:26Z mtime. Both are the only self-reported times in the corpus that are provably not the write time.

Number I could not close: the R² column (0.55–0.69 vs 0.90–0.97) and the fitted exponent θ (0.133–0.164) come
from "a two-parameter OLS per column on nine published points", but the table prints only the two endpoints
per subsample, so the fit cannot be reproduced from the file. The claim is probably right — the endpoints
constrain it — and it is not checkable as printed.

### 8. `02-ai-ml-decision.md` — declares its own vocabulary, and the quotes hold

Header complete except for an explicit depends-on line (the Sources list serves). A–E is declared
"almost nowhere" applicable and MEASURED/ASSERTED/ESTIMATE used instead; that is defensible for a document
about a hackathon clock rather than a market, and it says so.

Its two load-bearing external quotes are **verbatim correct** — I fetched the page it cites and found both:

> "We're looking for a working product that uses Solana for something it's good at (speed, low fees,
> composability, on-chain ownership), not a chain bolted onto a web2 app."

> "Build something where AI and Solana each do real work."

Same header timestamp defect as `02-a`.

### 9. `02-c-sale-hazard.md` — clean, and it resolves the corpus's central conflict

Header complete. It states plainly that nothing in it is measured. Its 30-row evidence table is the best
structured table in the corpus.

Its two **MEASURED** rows are accurate to the line: `TicketStatus` does include `"listed"` (`lib/types.ts:22`)
and `EventAnalytics.resoldShare` does exist (`lib/types.ts:192`). I checked both.

**Class defect:** those rows use `verified` in the Class column. `records/README.md` defines A, B, C, D, E and
states SIM and UNVALIDATED are "not evidence classes". `verified` is in neither list. This is the same
out-of-vocabulary promotion the ledger made for its Phase 0 rows — the defect the verification file calls
"the one defect that propagates". It has now propagated into Phase 2.

Citations **4/4 confirmed** (Allison `10.2307/270718`, Andersen & Gill `10.1214/aos/1176345976`, Vaupel et al.
`10.2307/2061224`, Lancaster `10.2307/1914140`); all 33 DOIs resolve.

### 10. `02-d-elasticity-fees-optimum.md` — the cleanest numbers file

Header complete. 14 classes, 27 MEASURED tags, 14 ASSERTED tags — the tagging is consistent.

Citations **4/4 confirmed**, and its two MEASURED product facts check exactly: "`API_CONTRACT.md` has no
price-mutation endpoint (9 endpoints, 7 reads, 2 wallet-verification POSTs)" — I counted 7 `GET` and 2
`POST` in the contract, so 9/7/2 ✓. And `TicketTier.faceValueLamports` is per tier and static ✓.

Its "16 CFR Part 464, source 90 FR 2166" is the eCFR source-line citation, which I confirmed Part 464 carries;
the Federal Register citation is 90 FR 2066. Defensible, worth aligning.

### 11. `02-e-cold-start.md` — strong arithmetic, one mislabelled headline, one wrong page range

Header complete, and the markings are excellent: `[MEASURED]`, `[ASSERTED]`, `[COMPUTED]` plus A–E, with the
COMPUTED rows showing their method.

**The arithmetic verifies.** Its prior fit and its band table are correct; I re-derived both:

- Fitted log-ratio N(0.261, 0.406²) reproduces all three Leslie & Sorensen facts: mean markup
  exp(0.261 + 0.406²/2) = 1.41 (+41% ✓); P(markup < 0) = Φ(−0.643) = 0.260 (26% ✓); P(markup > 67%) = 0.267
  against the published 0.25 (close ✓). And I confirmed the three source facts verbatim in the paper.
- The band table is exp(±1.645τ) around the estimate: τ = 0.10 → ×0.848/×1.179 → −15%/+18% ✓ exactly;
  τ = 0.406 → ×0.513/×1.951 → −49%/+95% ✓ exactly.
- The χ² span pairs are internally consistent: 0.12/2.79 = 0.0430 against χ²₀.₀₂₅,₄/χ²₀.₉₇₅,₄ = 0.484/11.143 =
  0.0434 ✓; 0.001/5.02 = 0.000199 against 0.000982/5.024 = 0.000195 ✓. Both use df = J−1, as they should.

**But the headline is mislabelled, and it is the one number the cold-start deliverable shows.** The column
reads "90% band on the event mean, log units | **as markup around face**", and the evidence table restates it
as "A 90% band on a brand-new event's mean markup runs from about −49% to +95%". What is actually computed is
the multiplier around the point estimate, not an absolute markup band. Centred where the model puts it, the
band is exp(0.261 ± 0.668) = 0.665 to 2.548, i.e. **−33% to +155%**. As printed, "−49% to +95%" says the
markup on a new event can be 49% *below face*, which contradicts the file's own class-A inputs (26% of resold
tickets below face, mean +41%). A reader who takes the label literally gets the sign of the downside wrong.

**One citation detail is wrong.** It cites Ekeland, Heckman & Nesheim as "*JPE* 112(6), 1278–1320" with DOI
`10.1086/379947`; that DOI resolves to **JPE 112(S1):S60–S109**. `01-b` has it right. Same paper, one file
wrong.

**Class defect:** E1's class cell reads "— (verified absence)", out of vocabulary again.

### 12. `02-rubric-and-scoring.md` — no A–E at all, and right about the rubric

Header complete. **Classes: none**, by declared exception: "The programme's A–E classes describe evidence
about ticket markets. They do not apply to a document about a hackathon's rules, and forcing them on would be
false precision." It uses MEASURED / MEASURED-ABSENT / ASSERTED throughout, 36 and 7 tags respectively.

That is a real deviation from `AGENTS.md` ("every important conclusion carries the programme's classification")
and it is declared, reasoned, and applied consistently — which is the best available handling short of asking.

Citations **4/4 confirmed**: `events.mlh.com/events/15200-solana-hackathon` 200, `www.mlh.com/events/
solana-hackathon` 200, the MLH rules raw file 200, the judging-plan 200 — and its claim that
`/events/solana-hackathon/submissions` "returns 'Page Not Found'" is exactly right, that URL returns **404**.

**Its central claim is true, and I verified it independently.** It says the brief's "25/25/25/25 —
originality / technical complexity / theme adherence / practical implementation" weighting "is not published
anywhere I could reach" and records it as MEASURED-ABSENT. I fetched both event pages and searched: **zero
occurrences** of "originality", "technical complexity", "theme adherence", "practical implementation" or "25%".
Meanwhile `NIGHT-BRIEF.md:130` still states "25/25/25/25 — originality, technical complexity, theme adherence".
And the page's embedded payload carries `"submissionsCount":7`, which confirms the file's "seven submissions"
claim exactly. This file overturns the brief and is right to.

Its environment claims all verify: python3 3.12.3, no `numpy`, no `scipy`, no `solana`/`anchor`/`cargo`/`rustc`,
node v24.22.2, devnet reachable, no `LICENSE`, remote `git@github.com:andy1245-rgb/ticketpath.git`.

### 13. `03-b-temporal-correctness.md` — arrived after the snapshot; verified to header, class and citation depth

Header complete, including a list of which Phase 2 files existed when it ran. Classes present (10 class
labels, 13 MEASURED, 3 UNVALIDATED). No numbers unexplained: its "61 features … 25 usable at D1, 43 at D2,
18 dropped … 6 absent, 11 post-decision, 1 unidentified" reconciles internally (25 + 18 = 43; 43 + 18 = 61;
6 + 11 + 1 = 18) ✓.

**Its MEASURED claim verifies exactly.** It says the contract contains "no `asOf`, no `as_of`, no `since`, no
`until` and no `as of` (counted: zero occurrences in both files)", and that `EventQuery` is `status, city, q,
cursor, limit` and `TicketQuery` is `eventId, ownerWallet, status, cursor, limit`. I grepped: **0** occurrences
in `lib/types.ts` and **0** in `API_CONTRACT.md`; both query interfaces match field for field.

First four sources **4/4 confirmed** — Powell 1986, Mason et al. 1973, Luo 2019, Fine & Gray 1999 — with the
same two author-name errors inherited from `01-b` (the Luo entry is Fosse & Winship; Mason's third author is
Winsborough).

---

## The cross-file conflicts, quoted, with a verdict on each

### C1. Does `resalePriceCapBps` vary within an event? — `01-b` against `01-c`, and the contract decides it

`01-b` §5.3:

> "`resalePriceCapBps` is *observed and varies*, across events and **across tiers within an event** because it
> is bps over each tier's own face — so the cap is an instrument"

`01-c` §1.4(1):

> "The *absolute* ceiling does differ across tiers, but the bps does not: `resalePriceCapBps` is a single field
> on `Event`, not on `TicketTier` … There is **no within-event identifying variation in the cap**; the
> instrument is a *cross-event* one"

**The contract settles it, and `01-c` is right.** `lib/types.ts` declares `resalePriceCapBps: number | null`
on `Event` only; `TicketTier` has five fields and no cap. So the field does not vary across tiers;
the *level* it implies does, mechanically, as a multiple of each tier's face. `01-b`'s §4.4(ii) states this
correctly ("its absolute level differs across tiers within one event"); it is §5.3's summary that overstates
it, and `01-c` is quoting §5.3 while attributing it to §4.4. Net: the one-sided bounds survive (cross-event
variation is real), but any claim of within-event instrument strength is withdrawn. `02-d` conclusion 3 agrees
with `01-c`.

### C2. Is the at-risk denominator observed? — `01-b` against the audit, `02-c` resolves

Audit Gap 1: "`P(sale | price, exposure, t)` is not identified from a completed-transaction ledger alone.
Without exposure, the observed sale count is a numerator with no denominator."

`01-b` §5.1: "**The denominator is present** — every ticket has an `issue` row and a known life."

`02-c` §1.2 resolves it without choosing a side: the ticket-time denominator is observed, but the object it
identifies is `λ_obs = s(t) · E[λ | offered]`, "a *base rate of transaction per ticket-day*, not a hazard of
sale". **`02-c` is the best-supported statement in the corpus on this point** — it keeps `01-b`'s observation
and the audit's conclusion, and it is the only file that names why both were right about different objects.

### C3. Does the asking-versus-realised gap shrink or vanish? — unresolved, and `01-b` is better supported

Audit: "The *asking-versus-realised* gap **does shrink**."
`01-b` §5.2: "The asking-versus-realised gap does not shrink; **it vanishes**. There is *no ask anywhere in
the record*".

If there is no ask in the record there is no wedge to shrink, so `01-b` is right and the audit's phrasing is
wrong — for the record we will have. The audit's sentence is arguably about the *literature's* problem, not
ours. Neither file says which question it is answering. This is a live conflict and it is still recorded as
settled in `F-decision-log.md` D3 and in ledger P0.4, which take the audit's version.

### C4. How big is the prize? — `02-a` against `01-a`, and `02-a` has the better argument

`01-a`: "repricing the top 10% of seats at the median resale price for those seats raises primary revenue
**3.4%**, ≈$27,000 per event", and "The three are consistent and they bound the prize: single-digit percent of
primary revenue".

`02-a` item 11: "**The mean observed markup is a late-window object and cannot be used as the secondary anchor
for the primary decision.** … Using the observed mean therefore understates the value at the moment the
primary price is set, by an amount that is large relative to the 3.4% of primary revenue that repricing the
top seats is worth."

`02-a` is better supported: it shows that half of resales occur inside 26 days and a quarter inside 7 (verbatim
from the paper, as I confirmed), so a mean taken over transacted markups is conditioned late. `01-a` carries
3.4% with no class and no window. Nobody has corrected the number; `01-c` ("the whole prize at 1.4–3.4%")
inherits `01-a`'s version. **Treat 1.4–3.4% as an order of magnitude, not a sizing.**

### C5. "Gap 5" — a dangling label that has spread

`00-data-situation.md` numbers Gaps 1–4 and then lists "Two smaller ones" *without* numbers.
`01-a` §7 cites "(Gap 5)". `01-c` cites "Gap 5" **four times** (§1.2, §2 data, §3.6, §9.3). No file defines
it. A reader following any of those five references finds nothing. `01-a` originated it; `01-c` propagated it.

### C6. The rubric — the brief against `02-rubric`, and the brief is wrong

`NIGHT-BRIEF.md:129-130`: "Rubric: … 25/25/25/25 — originality, technical complexity, theme adherence, …"
`02-rubric` §What I concluded 3: "The weighting quoted in the brief … is **not published anywhere I could
reach**. MEASURED-ABSENT on the event page, the canonical mlh.com event page, the five challenge-category
pages, the standard hackathon rules, the judging plan and the organizer rule page."

**`02-rubric` wins.** I fetched both event pages and found zero occurrences of those four criterion words and
of "25%", while finding the verbatim top-prize and AI-track sentences it quotes, and `"submissionsCount":7`.
The brief is carrying an unsourced rubric that a build could be pointed at.

---

## The defects that matter, ranked

Wrong number first, missing class last.

1. **`01-b` §4.1: "only 90 of 128 fixture tickets ever sell".** 90 is a `sale` row count; 49 tickets sell, 79
   never do. It is wrong on the audit's own figures, it is a `lib/mock/`-derived number in a programme that
   forbids them, and it sits in the sentence the T1 selection argument turns on.
2. **`01-a`: "1.4% of primary revenue, even after scaling for the ~50% of resale the authors do not observe".**
   The paper states the opposite — "even if we are accounting for only half of resale activity". The commercial
   case's numerator is presented as conservative when it is the observed half, unscaled.
3. **`00-ledger-verification` accuses `01-b` of a 404 DOI that `01-b` does not contain,** and
   `A-research-ledger.md:108` plus `00-adversarial-review` have inherited the false finding. Three documents
   now carry a defect that exists only in the first of them.
4. **`02-e`'s headline band is mislabelled.** "−49% to +95%" is a multiplier around the point estimate; as
   labelled ("as markup around face", and in the evidence table "a 90% band on … mean markup") it implies the
   markup can be 49% below face, contradicting the file's own class-A inputs. The correctly-centred band is
   −33% to +155%.
5. **`01-d`: "Nineteen candidate variables … eleven survive at usable priority."** 17 rows, 11 rejected, 9 at
   priority 1–2. Neither number is derivable, and both are unclassed.
6. **`01-a`'s £269 is spliced onto the £350m/1.9m pair.** £184 = 350/1.9 ✓; £269 = 404/1.5, a different flow.
   Over one clause the sentence implies a before/after pair that is two unrelated baselines.
7. **`01-b` §5.3 says the cap varies "across tiers within an event".** It does not; the field is on `Event`.
   `01-c` catches it and is right. The within-event instrument claim should be withdrawn; the cross-event one
   stands.
8. **Two wrong author attributions in three files that claim Crossref verification.** `10.1146/annurev-soc-
   073018-022616` is **Fosse & Winship (2019)**, cited as "Luo, L. (2019)" in `01-b`, `02-a`, `03-b`; Mason et
   al. (1973)'s third author is **Winsborough**, cited as "Winship". Titles, journals, volumes and pages are
   right in both cases.
9. **`01-d` cites with no locator at all** — zero DOIs, zero URLs, four papers admitted to be from memory, an
   NBER WP with no number, and Krueger with no publisher. The file is honest about it; the registry it feeds is
   not protected by that honesty.
10. **`02-a`'s and `02-ai-ml`'s "Written: 2026-11-07T11:20Z"** postdate their own last write (11:06:07Z,
    11:10:26Z) and cannot be true. Only self-reported times in the corpus that are provably not the write time.
11. **`01-b` has no Scope field**; `01-a`, `00-ledger-verification` and `00-adversarial-review` carry no
    explicit depends-on.
12. **"Gap 5" is cited five times across `01-a` and `01-c` and defined nowhere.**
13. **`02-e` misstates Ekeland–Heckman–Nesheim as 112(6):1278–1320**; the DOI resolves to 112(S1):S60–S109.
14. **`01-a` cites He & Lin as 2025**; Crossref gives *Marketing Science* 45(3), 2026.
15. **Missing classes, in the order of how much they matter:** `01-b` §3's identifiability ledger (the file's
    entire output) has no Class column; `01-a` §6 and §7 are unclassed in full, including the project's central
    constraint; `01-d`'s E-1 registry table and §4–§8 are unclassed; `01-c`'s §1.1 matrix and §1.2 answers are
    unclassed; `02-c` E1/E2 and `02-e` E1 use **"verified"**, a class `records/README.md` does not define — the
    same defect that was corrected in the ledger has propagated into Phase 2.

Two things I expected to find and did not: **no fabricated source anywhere.** Every DOI resolves except the two
that were *meant* to 404, every URL that matters resolves with the status the file claims for it, and the two
files whose business is the outside world (`02-rubric`, `02-ai-ml`) quote their sources verbatim. The citation
hygiene is far better than the class discipline.

---

## What a reader may trust tonight

- **That the sources are real.** 60-plus distinct works, every DOI resolved, no invented paper, no invented
  dataset, no invented statistic. The wrong citations are transcription errors in author names and one page
  range, not fabrication.
- **`02-a`'s numbers.** The four decline percentages, the 2.7× arrival-rate ratio, the 50%/26-day and 25%/7-day
  timing figures: recomputed and correct, against a paper whose text I extracted and read.
- **`02-e`'s arithmetic**, once the band's label is read as a multiplier: the prior fit, the χ² spans and the
  sensitivity table are all internally correct and correctly derived from cited facts.
- **`02-rubric`'s rubric finding.** The brief's 25/25/25/25 weighting is not on any MLH page; the top-prize
  criterion and the AI-track criterion are quoted verbatim; the field is seven submissions.
- **`03-b`'s contract facts.** No as-of marker and no time parameter in either query interface — checked by
  grep, exactly as stated.
- **`02-d`'s fee algebra and product facts** — 9 endpoints, 7 reads, 2 POSTs — and `02-c`'s schema facts.
- **`00-adversarial-review`'s verdicts.** Its recomputed fixture counts agree with the audit, and its three
  narrowings are argued from the files' own text.
- **That `01-b`'s identification argument is sound** on the full price-response curve. Four independent files
  reach the same conclusion by different routes, and the adversarial review's attack narrows the summary
  without breaking the argument.

## What a reader must not trust yet

- **The 1.4% figure as a conservative lower bound.** It is the observed half, unscaled, and `01-a` says the
  opposite of what the paper says. Do not put it in a pitch without the "half of resale" caveat attached.
- **The prize sizing at 1.4–3.4% of primary revenue.** `02-a` shows the mean it rests on is conditioned late;
  no file has corrected it, and `01-c` inherits it.
- **Anything in `01-d`'s registry as "verified".** It is a good map with no locators behind it and four papers
  cited from memory.
- **The 19/11 variable counts, and "Gap 5".** Neither number nor the label exists in the record that is
  supposed to define them.
- **The cold-start band as "−49% to +95% of face".** As a multiplier around the estimate it is right; as an
  absolute markup band it is wrong and contradicts the +41% mean.
- **The claim that every citation was Crossref-checked** (`01-b` §7). Two author names in that file's own list
  are wrong.
- **Any inherited statement that `01-b` cites a broken Aigner DOI.** It does not. The correct DOI is in the
  file, in both the working copy and the commit.
- **The brief's rubric weighting**, until someone points at a page that carries it.

---

**One defect that would embarrass the submission if a judge found it.** `01-b` line 86, "only 90 of 128
fixture tickets ever sell" — because it is simultaneously a number derived from `lib/mock/` in a programme
whose own audit forbids that, a number that is wrong on the audit's own row counts (49 tickets sell), and a
number sitting in the file whose §7 claims every citation and metadata item was checked. A judge who opened
the research record would find the bright-line rule, the arithmetic and the diligence claim all broken in one
sentence. The second-most is `01-a`'s "even after scaling", which misstates the source paper's own caveat on
the number the commercial case rests on.

*Nothing was edited but this file. Nothing was committed or pushed.*

# 00 — Verification round 2: the corrections, and the new material

**Status:** complete. **UTC:** 2026-11-07T13:50Z. **Agent:** independent verifier (round 2).
**Scope:** (a) every defect listed in `records/CORRECTIONS-APPLIED.md` §1, checked against the file it
corrects and against the source each correction relies on; (b) the four protection tests those corrections
were supposed to establish; (c) `records/findings/09-sim-recovery.md` against
`records/sim/sim-recovery-2026-11-07.txt`; (d) `records/DELIVERABLE.md` §20–§22.
**Method:** every correction read in the file that carries it and in `CORRECTIONS-APPLIED.md`; the four
targeted Crossref records re-queried live today (`10.1146/annurev-soc-073018-022616`, `10.2307/2094398`,
`10.1086/379947`, `10.1287/mksc.2023.0623`) and the returned author sets, volumes, issues and pages compared
field by field; the Leslie & Sorensen full text re-read at `/tmp/leslie.txt` (the extraction the round-1
pass used) for the 1.4% sentence and the seat-quality and resale-share facts; the UK DBT analytical note
re-read at `/tmp/dbt.txt` for the £350m/1.9m and £404m/1.5m pairs; the MLH standard rules re-read at
`/tmp/mlh-rules.md` and the Solana event page re-scanned at `/tmp/mlh-solana-page.html` for the rubric
question; the wire contract re-read at `ticketing-frontend/lib/types.ts`; `01-d`'s two tables recounted row
by row; the Gap 5 site table checked sentence by sentence; and the simulation harness re-run once
(`python3 tools/sim_recovery.py`, output to `/tmp`, the record not touched) to test the determinism and
reproducibility claims.
**I wrote none of what I am checking, and I fixed nothing.** The only file written by this pass is this one.
Nothing was committed or pushed. `lib/mock/` was not read. No frontend file was edited. No fleet path was
read or written.

**Snapshot.** `records/` was read as it stood at 13:50Z: `09-sim-recovery.md` 26,026 B,
`sim-recovery-2026-11-07.txt` 16,895 B, `CORRECTIONS-APPLIED.md` 26,142 B, `DELIVERABLE.md` 200,549 B.

---

## 1. Per-defect verdicts

Verdict vocabulary, as the brief sets it: **(a) holds** — true, and the source it relies on says what the
correction says; **(b) new error** — the correction itself asserts something false; **(c) right in
substance, wrong in a detail** — the restored fact is true but a number, a count, a quotation or a location
is not, or the false sentence is left standing where a reader meets it first. I checked the underlying
source every time; where the correction and the source disagree, the source wins and I say so.

| # | Defect | Verdict | What I checked |
|---|---|---|---|
| 1 | `01-b` §4.1/§4.3 fixture counts | **(c)** | numbers right, tally of remaining sites wrong |
| 2 | `01-b` §4.3 "14 of 128 tickets redeem" | **(a)** | the record does not carry a ticket count |
| 3 | `01-b` §5.3 within-event cap | **(a)** | contract checked field by field |
| 4 | `01-b` §7 two author attributions | **(a)** | both Crossref records re-queried |
| 5 | `01-a` §4 "even after scaling" | **(a)** | source sentence re-read verbatim |
| 6 | `01-a` §3 £269 splice | **(a)** | both DBT pairs re-read, arithmetic redone |
| 7 | `01-a` §3/§7 He & Lin year | **(a)** | Crossref: 45(3):515–533, 2026-05 |
| 8 | `00-ledger-verification` §3 Aigner accusation | **(c)** | accusation false as stated, and still printed as a live finding |
| 9 | `00-adversarial-review` Aigner note | **(c)** | same, same reason |
| 10 | `A-research-ledger` Aigner bullet and V1 row | **(c)** | same, same reason |
| 11 | `02-e` band label and E8 | **(a)** | recomputed all four rows; +153% is right, +155% was not |
| 12 | `02-e` Ekeland issue and pages | **(a)** | Crossref: 112(S1), S60–S109 |
| 13 | `01-d` "Nineteen / eleven survive" | **(a)** | tables recounted: 17 + 11, 9 at priority 1–2 |
| 14 | `C-variable-registry` C-3 cap claim | **(c)** | withdrawal right; the same paragraph's other false sentence left uncorrected |
| 15 | `02-a` reference list, two entries | **(a)** | both Crossref records re-queried |
| 16 | `03-b` [Luo 2019] entry | **(a)** | Crossref: author, title and pages all wrong as stated; Mason entry already right |

**Tally: 11 hold, 5 are right in substance with a defective detail, 0 assert a new falsehood about a source.**
The rubric item, which is a decision not to correct rather than a correction, also holds. The five (c) verdicts
are two different faults: 1 miscounts how much of its own defect survives, and 8–10 and 14 are true
withdrawals that leave the withdrawn text standing where a reader meets it first.

**Detail on each.**

**1. `01-b` §4.1/§4.3 — (c).** The arithmetic holds and I re-derived it from `00-data-situation.md` §2:
"253 ledger rows (128 `issue`, 90 `sale`, 21 `transfer`, 14 `redeem`)"; "79 of 128 tickets have no sale at
all"; 128 − 79 = **49** tickets sell, 90 − 49 = **41** tickets sold more than once, 128+90+21+14 = 253. The
correction's reading of 14 as a `redeem` row count, and its refusal to convert it without a ticket-level
count, are both right.

The detail that is wrong is the tally of how much of the same defect remains. `CORRECTIONS-APPLIED.md` row 1
says "It is **also the one place** in that file where a `lib/mock/` figure does argumentative work", while
`01-b` CORRECTION 1 two pages later says "It is **one of two places** in this file". Two documents, two
counts, and neither is right: `01-b` uses a fixture fraction to argue a *model form* at §4.3 item 3
("a point mass at 'will never be offered' **fits 79-of-128 better** than a long tail") and to bound a
measurement-error quantity at §4.5 ("so **79-of-128 is an upper bound** on the never-*offered* fraction"),
and both sentences stand. The correction names the §4.3 one and declines to withdraw it ("should be argued
from those and not from the fixture's never-sell fraction"); it never mentions the §4.5 one. So three
fixture-derived argumentative uses survive in that file, one of them unidentified, against a stated count of
one or two. The number that matters — 49 tickets, not 90 — is restored correctly.

**2. `01-b` §4.3 — (a).** `00-data-situation.md` records 14 `redeem` rows and no ticket-level redemption
count, so "cannot be reconciled from the record" is exactly right, and the refusal to count the fixture to
settle it is consistent with the audit's rule. The sentence is nevertheless still printed as written
(see §5, item 2).

**3. `01-b` §5.3 — (a).** Verified against the contract: `resalePriceCapBps: number | null` is declared at
`lib/types.ts:68`, inside `interface Event`; `TicketTier` (lines 20–26) has five fields — `id`, `name`,
`faceValueLamports`, `totalSupply`, `issuedCount` — and no cap. The basis-point cap cannot vary within an
event; the money ceiling does, as face × (1 + c). The correction says exactly this and separately notes that
`01-c` §1.4(1) mis-attributes the sentence to §4.4(ii). That last point is correct and, as §3 below shows,
was never carried into `01-c`.

**4. `01-b` §7 — (a).** Live Crossref today:
`10.1146/annurev-soc-073018-022616` → title "Analyzing Age-Period-Cohort Data: A Review and Critique",
authors **Ethan Fosse, Christopher Winship**, *Annual Review of Sociology* 45(1):467–492, 2019.
`10.2307/2094398` → authors **Karen Oppenheim Mason, William M. Mason, H. H. Winsborough, W. Kenneth
Poole**, *ASR* 38(2):242, 1973. Both corrections are exact, including that titles, journals, volumes and
pages are unaffected.

**5. `01-a` §4 — (a).** The paper, re-read at `/tmp/leslie.txt` line 44: "This is equivalent to 1.4% of the
total primary market revenue for these events. As a measure of 'money left on the table' this suggests a
fairly modest amount of forgone profit by firms in the primary market, **even if we are accounting for only
half of resale activity**." 1.4% is the observed half, unscaled, and the paper's "even if" is a limitation,
not a correction upwards. "Even after scaling" inverts it. Correction holds.

**6. `01-a` §3 — (a).** `/tmp/dbt.txt`: "1.9 million … £350 million"; and "**£404 million is spent in the
resale market on 1.5 million tickets, giving an average ticket cost on the resale market of £269.**"
350/1.9 = 184.2; 404/1.5 = 269.3; 269.3 × 1.9 = 511.7 ≠ 350. The splice is real, the correction's
arithmetic is right, and the two pairs must not be quoted as a before-and-after.

**7. `01-a` §3/§7 — (a).** Crossref for `10.1287/mksc.2023.0623`: He, Da; Lin, Song, "Price Caps by Matching
Platforms: The Case of Ticket Resales", *Marketing Science* 45(3):515–533, issued 2026-05. "2025" is wrong;
2026 is right.

**8–10. The Aigner accusation — (c) three times.** The substance is right and I confirmed it: `01-b` contains
no S-prefixed Aigner DOI. Its two Aigner occurrences are the resolving form (lines 246 and 325), and the only
`S0304-4076` strings in the file are Bollinger (1996) at lines 245 and 334, where the `S` belongs. The
correction's explanation of how the 404 was produced is right, and so is its observation that the section's
opening tally ("with one exception") is wrong for a different reason.

The detail that fails is the one the brief asks about. The accusation is **still printed as a live finding**
in two of the three files, in sections that assert it is confirmed:

- `findings/00-ledger-verification.md:167`, under the heading **"### Confirmed wrong as cited"**:
  "**`10.1016/S0304-4076(73)90005-5`** (`01-b` §7, Aigner 1973, *Journal of Econometrics* 1(1), 49-59).
  Crossref returns **HTTP 404**. … This is the single unresolvable citation in the records".
- `A-research-ledger.md:120`, under the heading "### Defects the verification found that no record carries":
  "- `01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`, which returns 404".

Both files carry the withdrawal at their end (line 312 and line 134 respectively), and neither carries a
marker at the site. A reader who opens §3 of the verification file — the section a judge would go to for the
citation audit — reads the false finding as current. So the record still contains three documents' worth of
the defect the correction was written to delete; only the last page of two of them says otherwise.
(One further imprecision: correction 8 says "Every sentence of the finding is withdrawn", including "the
correct DOI is `10.1016/0304-4076(73)90005-5`, which resolves to exactly the cited title", which is true.)

**11. `02-e` — (a), and the pass corrected the verifier.** I recomputed every cell. exp(±1.6449 × 0.406) =
×0.513/×1.950, which is −49%/+95% on the estimate. The correctly centred band is exp(0.261 ± 0.668) =
0.666 to 2.532 = **−33% to +153%**, so the round-1 file's +155% was wrong by two points and this correction
is right to say so. The other rows check too: τ=0.10 → 1.102 to 1.530 (+10%/+53%); τ=0.20 → 0.934 to 1.804;
τ=0.30 → 0.793 to 2.125. The label was the defect and the label is now stated correctly in the correction,
which also keeps the prose "minus half to double" as the multiplier reading that was always right.

**12. `02-e` — (a).** Crossref `10.1086/379947`: Ekeland, Heckman, Nesheim, "Identification and Estimation of
Hedonic Models", *JPE* 112(S1):S60–S109, 2004. `01-b` had it right; `02-e` did not; now stated.

**13. `01-d` — (a).** Recounted: `Table C-1` has 17 `V` rows with priorities 1×5 (V1–V5), 2×4 (V6–V9), 3×4
(V10–V13), 0×2 (V14, V15), 4×2 (V16, V17); `Table C-2` has 11 rows. 17 + 11 = 28 examined; 9 at priority
1–2, of which 4 are obtainable from the contract today; 15 above 0. Neither 19 nor "11 survivors" is
derivable, and the correction's diagnosis (11 is the reject count) is right.

**14. `C-variable-registry` C-3 — (c).** The cap withdrawal is true for the reason given in 3 above. The
detail that is wrong is that C-3 contains a *second* false sentence in the same paragraph, and the
correction leaves it standing while the tidy-up pass records it as fact:

> "The registry treats V3 as both, and 01-b's original point stands: **no class-A claim about caps may
> appear in the deliverable**, because **no peer-reviewed study of resale price caps in ticket markets was
> found**."

`01-a` §3 cites He & Lin, a peer-reviewed *Marketing Science* paper on exactly that subject, so the clause
"no peer-reviewed study … was found" is false. `CORRECTIONS-APPLIED.md` §5.1 item 3 says so in terms: "One
sentence in the records *is* falsified by this: `C-variable-registry.md` C-3's broader 'no peer-reviewed
study … was found', which now carries a dated note narrowing it to `01-b`'s wording." I read the appended
text: it does **not** narrow the sentence. It says "One question this correction does not settle … Whether
it is an econometric study, which is the narrower bar `01-b` §4.5 sets, I did not read and do not assert."
The clause remains as printed at `C-variable-registry.md:820-822`, unamended, and the note sits 30 lines
below it. So the correction is right and the record still asserts the thing the correction's own report says
is falsified.

**15. `02-a` — (a).** Both Crossref records re-queried; both attributions in `02-a`'s list (lines 896, 899)
are wrong exactly as the correction says, and its corrected readings are right.

**16. `03-b` — (a).** `03-b:1024` reads "[Luo 2019] Luo, L. (2019). **Bayesian age-period-cohort analysis**.
*Annual Review of Sociology* 45, **109–132**". Crossref returns Fosse & Winship (2019), "**Analyzing
Age-Period-Cohort Data: A Review and Critique**", 45:467–492. Author, title and pages wrong; volume and DOI
right, as stated. And `03-b:1021` already has "Mason, K. O., Mason, W. M., **Winsborough, H. H.**, & Poole",
so the correction is right that round 1's "both errors recur here" was half wrong.

**The rubric item, reported as needing no correction.** I checked it independently and the pass is right.
`/tmp/mlh-rules.md:56`: "Teams will be judged on these four criteria … **Judges will weigh the criteria
equally.**" over Technology, Design, Completion, Learning (lines 58–64). Scoring `/tmp/mlh-solana-page.html`
for the brief's four words and for "25%" returns **0 occurrences each**. So 25% each is arithmetic on a
sourced "equally", not a sourced weighting, and no file in `records/` states the brief's 25/25/25/25 as
sourced: `02-rubric` A5 records it MEASURED-ABSENT, `02-ai-ml-decision` §3.2 defers to that finding,
`BUILD-SPEC-NIGHT` R1's "Design is 25% and Completion is 25%" is the four-way arithmetic, and
`SUBMISSION-PACK` says it is not used. **The unsourced weighting lives only in `NIGHT-BRIEF.md:129-130`,
outside `records/`, where it still reads "25/25/25/25 — originality, technical complexity, theme
adherence, practical implementation".**

---

## 2. The four protection tests

**2.1 Fixture-derived numbers in findings — FAILS, in part.** `01-b` is the only finding that derives an
argument from a fixture number. Four sites survive there, two of them identified by the correction and two
not:

| Site | The sentence | Status |
|---|---|---|
| `01-b:86` | "only 90 of 128 fixture tickets ever sell" | withdrawn at the end of the file; printed unmarked in §4.1 |
| `01-b:149` | "This matters: 14 of 128 tickets redeem" | same |
| `01-b:152-153` | "a point mass at 'will never be offered' **fits 79-of-128 better** than a long tail" | flagged by the correction, not withdrawn, still the stated ground for the cure component |
| `01-b:247` | "so **79-of-128 is an upper bound** on the never-*offered* fraction" | not mentioned by any correction |

Everything else I could find is legitimate: `02-c` §7.2's "128 of 2,400 tickets in this tier" is an
illustrative sentence for a UI and its own arithmetic (128/2,400 = 5.3%) is right; `00-adversarial-review`
recomputes fixture counts as a check *on* `01-b`; `00-ledger-verification` reports them as defects. No other
finding puts a fixture number into a market claim.

**2.2 The withdrawn accusation appears nowhere as a live finding — FAILS.** See 8–10. It appears live in
`00-ledger-verification.md:167` (under "Confirmed wrong as cited") and `A-research-ledger.md:120` (under
"Defects the verification found that no record carries"). It appears only as quoted-and-refuted in
`00-verification-round1.md:104`, and only as quoted-and-withdrawn in the correction blocks and in
`CORRECTIONS-APPLIED.md`. `00-adversarial-review`'s version survives live at line 477 ("I corroborate … the
Aigner DOI (I re-checked Crossref: the `S`-prefixed DOI returns 404, the corrected one 200)"), which is
quoted and withdrawn at line 601.

**2.3 No other file still relies on a within-event cap — PASSES on the conclusion, FAILS on the text.**
No file's *conclusion* rests on within-event cap variation. `03-a` I12 marks it "No — untestable here" and
cites the withdrawal; `02-b` B2 states only the true absolute-level fact; `B` C6 and `D` C6 both record
`01-c`'s version; `01-c` §1.4(1) states the correct contract fact. What does not pass is the text of two
records, which mis-attribute the corrected sentence to the one section of `01-b` that gets it right — and
neither was amended by any pass:

- `01-c-methods.md:136-137`: "**01-b §4.4(ii) overstates the cap as an instrument.** It says
  `resalePriceCapBps` 'varies … across tiers within an event because it is bps over each tier's own face'."
  `01-b` §4.4(ii) says the opposite — "Because the cap is bps over *each tier's own* face, its **absolute
  level** differs across tiers within one event" — and the sentence quoted is §5.3's.
- `D-model-registry.md:1480` (C6): "`01-b` §4.4(ii) treats the cap as an instrument with cross-tier
  variation." Same mis-attribution.

`01-b` CORRECTION 2 notices this ("One detail: its citation is to '§4.4(ii)', while the sentence it quotes
and corrects is §5.3's") and stops there. `B-mathematical-kb.md` C6 records the distinction correctly, which
is why the corpus now disagrees with itself about which section said what.

**2.4 No file states 25/25/25/25 as sourced from the event pages — PASSES.** See §1 above. Verified against
the fetched pages, not against the finding's claim about them.

---

## 3. New material: `09-sim-recovery.md` against its log

**3.1 Every number is in the log, or is shown arithmetic on it.** I extracted every numeric token from the
finding and matched it against `records/sim/sim-recovery-2026-11-07.txt`. Sixteen do not appear literally;
all sixteen are accounted for:

| Token | Where it comes from |
|---|---|
| `0.0067` | binomial SE at 90% with R=2,000: √(0.9×0.1/2000) = 0.00671 |
| `3.7` | 0.0097 / 0.2612 = 3.71% ("3.7% of the true mean") |
| `2.9`, `2.1`, `1.46` | 0.2586/0.09, 0.1849/0.09, 0.1316/0.09 against the truth 0.09 |
| `1.6449` | the z in the log's printed width 0.6580 = 2×1.6449×0.20 and 0.9869 = 2×1.6449×0.30 |
| `4.1`, `4.2`, `4.4`, `4.5`, `4.7`, `5.1`, `8.2` | section references inside the finding |
| `139`, `895`, `300` | the output's line count, its byte count, the 300 s budget |

The three tables match the log cell for cell: A1 (μ̂, bias, MC SE, threshold at J = 2/5/20 in both declared
arms), A2 (mean τ̂², relative bias, p10/p50/p90, share at the floor), B1 (six coverage/width pairs), C1
(seven cells, both estimators, RMSE, cap mass, clipped-end share), C2 (four diagnostic rows plus the
correlation and variance-factor pair). The derived sentences check: 0.0491/(0.09+0.0491) = 0.353
("more than a third of the gap's variance is missing"); 0.9649/0.6957 = 1.387 ("39% above the truth");
0.0124/0.30 and 0.0393/0.30 = "4% to 13%".

**3.2 The log reproduces.** The harness prints to stdout and writes no file, so re-running it cannot touch a
record. I ran `python3 tools/sim_recovery.py` once, to `/tmp/verify_sim_run2.txt`: 139 lines, exit 0, and
`diff` against the record is **three lines** — the `start=` timestamp and the two timing lines. Every
verdict, number and condition line is byte-identical. The finding's "Determinism: two runs identical apart
from the timing lines" is therefore true, and I verified it rather than taking it. `tools/sim_recovery.py`
is 39,650 bytes as stated; it imports `ticketpath.core.path_model` and `value_band` (line 58), carries
`PASS_CONDITIONS` at line 107, and runs each study under a 60 s `SIGALRM` (lines 142, 186, 824).
`value_band.EVENTS_FOR_ESTIMATED_TAU = 9` (line 43), and the two shipped modules' mtimes (11:55 and 12:33)
both precede the run. My `git status` at 13:43Z showed one modified path, `NIGHT-LOG.md`, and no engine
file — so "the engine was not edited" holds for the state the study ran against.
**One thing the next reader must know:** at 13:46Z, while this pass was reading, another writer modified
eleven tracked files and added one (`ticketpath/console/blocks.py`, `console/units.py`, `core/labels.py`,
`core/primary_optimum.py`, `orchestrator.py`, `api/guidance.py`, `adapters/ledger_adapter.py`,
`tests/test_console_fixes.py`, `tests/test_labels.py`, `tools/build_fixture_store.py`,
`tools/console-check-stores.py`, and new `tests/test_cap_and_loader_refusals.py`). I did not make those
changes and did not read them; they postdate the 13:30Z simulation run and are not in this pass's scope.
Anyone re-checking "the engine was not edited" should re-run `git status` rather than rely on the 13:43Z
observation.

**3.3 The three verdicts are consistent with the declared conditions — with one framing defect.** Counted
from the log's own condition lines: 19 A-conditions (all PASS), 14 B-conditions (4 fail: `declared_matched`
at J=2, `pooled_width` at declared 0.20 for J=2 and J=5, `width_shrinks` at 0.20), 10 C-conditions (2 fail:
`cap_direction`, `cap_magnitude`). 19+14+10 = 43, 43−6 = 37, so "A **PASS**, B **FAIL**, C **FAIL**; 37 of
43 pre-declared conditions held" is exactly the log, and the finding's §5 tables reproduce the log's
PASS/FAIL lines condition by condition.

The defect is at the top. Under "**The three failures first**, because they are the result", item 2 reads:

> "2. **B, the default declared tau**: at the API default `tau = 0.20`, coverage is **0.620 / 0.694 /
> 0.718** at J = 2 / 5 / 20 against a true between-event tau of 0.30."

Those are the log's `B.declared_default` figures, and the log prints that condition **PASS** at all three J
— it was declared as a predicted failure ("coverage at declared=0.20 is < 0.87 … under-covers a tau of
0.30"), so the under-coverage confirms it. The finding's own §5 says "PASS, 0.620 / 0.694 / 0.718, all below
0.87 **as predicted**", and §3.3 says "this is the predicted failure, not a surprise". The third genuinely
failed condition, `B.width_shrinks` in the 0.20 arm, is not in the trio (it is disclosed at §3 point 4 and
in §5). So the summary presents a held condition as a failure and omits a failed one. The substance of item
2 is true — the default does under-cover — but the word "failures" and the count of three are not the
source's. Nothing else in the finding overstates; the file's limits section (its §6) is unusually careful
about what a SIM result can and cannot say, and the C1 reconciliation in §4 ("02-a C1 is right about the
object it names … the curvature moves the other way") is correct: I checked it against `02-a:516` and the
two are about different quantities.

---

## 4. New material: `DELIVERABLE.md` §20–§22

**4.1 §22's one-directional claim holds; its completeness does not.** I checked all 161 entries. Every
entry's first author appears in the findings or in a registry, so "**No source appears here that no finding
cites**" survives — with the accent-spelling caveat that Brémaud and Dudík are printed unaccented here and
accented in `01-c`. Two things do not survive:

- The section is headed "**Full bibliography**" and opens "Deduplicated from **the sources the findings
  cite**". One source a finding cites is missing: `02-d:839-840` cites "**Ahn, S. C. & Lee, Y. H. (2007).**
  Lifecycle demand for Major League Baseball. *International Journal of Sport Finance* 2(2):79–93.
  doi:10.1177/155862350700200203" and it is not in §22. (I swept every DOI in `findings/*.md` against the
  bibliography; this is the only real omission. The others that failed the sweep were trailing-punctuation
  artefacts or `01-c`'s recorded wrong DOI.)
- Five `Used by` cells name a finding that does not cite the source: **Artzner (1999) → 06** (the validation
  protocol uses CVaR at line 329 and never cites Artzner); **Ekeland et al. (2004) → 02a** (`02-a` never
  cites it); **Gallego & van Ryzin (1994) → 01a** (`01-a` never cites it); **Lakkaraju et al. (2017) → 01c**
  (the phrase and the paper are in `01-b` and `02-c`, not `01-c`); **UK DBT note → 02e** (`02-e` cites no DBT
  material). The arithmetic of the counts is right: 123 + 7 + 3 + 22 + 2 = 157 cited, +4 checked-and-not-used
  = 161 entries, matching the printed count.

**4.2 §20.5's status note is itself false in one clause, and contradicts §21.2.** The note says:

> "(3) … `C-variable-registry.md` C-3's broader "no peer-reviewed study" **is narrowed to `01-b`'s wording
> there**."

Nothing narrows it. `C-variable-registry.md:820-822` still reads "no peer-reviewed study of resale price
caps in ticket markets was found", and the appended note declines to assert anything about He & Lin. The
same sentence also resolves the question one way ("`01-a`'s class-C use of a peer-reviewed **model**") while
`01-a`'s NOTE says "I did not read the paper in this pass and therefore assert nothing about its method", and
while `DELIVERABLE.md` §21.2's own row says "whether it is an *econometric* study is still open". §20.5 says
the question "is settled"; §21.2 says it is open. One of the two must go.

**4.3 What §20 omits that the findings call out.** §20 is otherwise strong: it carries the four absences,
the fee point, seat coordinates, the unidentified level, the twofold selection, the ~5% resale share
(51,318/1,034,353 = 4.96%, checked in the paper), the 0.61-vs-0.50 seat-quality fact (checked verbatim), the
1.4%-covers-half caveat, the +153% correction, and the live conflicts. Three things the findings call out
are missing:

1. **The whole of `09-sim-recovery.md`.** It landed at 13:30Z, after the document was assembled at 12:40Z,
   and §20 and §20.5 do not mention it. That matters because two of the SIM results are limitations of
   shipped code: the declared band's coverage of a new event's mean is **0.805 at J=2** against a declared
   [0.87, 0.93], and at the API default τ = 0.20 it is **0.620 / 0.694 / 0.718** against a true τ of 0.30;
   and the shipped path estimator has **RMSE 1.04** in a 40–60-day window with no guard testing the design's
   conditioning. §11 and §20.5 are the places these belong.
2. **The coverage sentence in §11.** It reads "What is **not available: any coverage claim**" and "it is not
   calibrated, because calibration of any price distribution is blocked by selective labels". The first is
   now too strong as written: the record contains measured coverage numbers for the band (conditional on a
   stated DGP, which the SIM file is careful to say). The second remains true and is about a different
   object. §8.2's "The evidence that would validate it is a **SIM recovery study**" is the sharper version
   of the same staleness: the study exists and did not validate the band.
3. **`records/README.md:30-31` still describes `DELIVERABLE.md` as "a stub and says so at the top: it is not
   written yet".** That is §20.5's business — a limitation *in the records* — and it is not in that list.

---

## 5. Remaining false statements

Every item below is a sentence that a hostile reviewer can show false, with the check that shows it. I have
separated the ones no correction touches (A) from the ones whose correction exists but sits at the end of the
file while the sentence sits in the body (B), because the first group is the one that needs a decision and
the second is a matter of how the append-only rule is applied.

### A. False, and no correction anywhere in the corpus

1. **`records/README.md:30-31`** — "**It is a stub and says so at the top: it is not written yet.**"
   *True:* `DELIVERABLE.md` is 200,549 bytes, written through §22 and a closing note, and its top says the
   opposite: "**Status of this document:** it is the Phase 8 document, not a table of contents for one."

2. **`findings/01-c-methods.md:136-137`** — "**01-b §4.4(ii) overstates the cap as an instrument.** It says
   `resalePriceCapBps` 'varies … across tiers within an event because it is bps over each tier's own face'."
   *True:* that sentence is `01-b` §5.3's; §4.4(ii) says "Because the cap is bps over *each tier's own* face,
   its **absolute level** differs across tiers within one event", which is the correct statement. `01-b`
   CORRECTION 2 records the mis-attribution and `01-c` was never amended.

3. **`D-model-registry.md:1480`** — "`01-b` §4.4(ii) treats the cap as an instrument with cross-tier
   variation." *True:* §4.4(ii) uses cross-**event** variation ("Across events with different caps, such
   statements at different points trace a lower bound") and states only that the ceiling's level scales with
   face.

4. **`C-variable-registry.md:816`** — "the cap is observed, varies across events, and **varies across tiers
   within one event** because it is bps over each tier's own face". *True:* the field is on `Event`;
   `TicketTier` has no cap; only the implied money ceiling varies, collinear with face.

5. **`C-variable-registry.md:820-822`** — "**no peer-reviewed study of resale price caps in ticket markets
   was found**". *True:* He & Lin (2026), *Marketing Science* 45(3):515–533, is a peer-reviewed study of
   resale price caps in ticket markets, and `01-a` §3 cites it. `CORRECTIONS-APPLIED.md` §5.1 calls this
   sentence falsified and leaves it.

6. **`findings/00-ledger-verification.md:25`** — "`records/findings/` contains exactly
   `01-a-market-structure.md`, `01-b-identifiability.md`, `01-d-external.md`. **No `01-c*` file exists.**"
   *True:* `01-c-methods.md` exists, 1,558 lines, written 10:57Z–11:09Z. The row was a 10:55Z observation;
   the file says "Status: complete" and nothing corrects it, while `A-research-ledger.md` has since been
   updated to say P1.C is answered — so the two records now contradict each other.

7. **`DELIVERABLE.md` §22, "Full bibliography"** — omission of **Ahn & Lee (2007)**, *IJFS* 2(2):79–93,
   doi:10.1177/155862350700200203, which `02-d:839-840` cites; and five `Used by` cells naming a finding
   that does not cite the source (Artzner→06, Ekeland→02a, Gallego→01a, Lakkaraju→01c, DBT→02e). *True:* as
   in §4.1 above.

8. **`DELIVERABLE.md` §20.5 status note (3)** — "`C-variable-registry.md` C-3's broader 'no peer-reviewed
   study' **is narrowed to `01-b`'s wording there**", and the same note's "**is settled as far as the record
   can settle it**". *True:* nothing narrows it (item 5 stands as printed), and §21.2's own row says the
   question is still open.

9. **`DELIVERABLE.md` §11** — "What is not available: **any coverage claim**"; and §8.2 — "The evidence that
   would validate it **is a SIM recovery study**". *True:* `09-sim-recovery.md` reports measured coverage of
   the declared band (0.805 at J=2; 0.620/0.694/0.718 at the default τ) and the study did **not** validate
   the band. The statements were true when written and are now stale in the way the record calls a defect
   elsewhere.

### B. False, corrected only at the end of the same file

These are the withdrawn sentences still printed where a reader meets them. Each is refuted by its own file's
correction block, which is why I list them together; a judge who reads the section and not the tail is
misled by every one.

10. **`01-b:86`** — "only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of an
    already-selected subset." *True:* 90 is a `sale` row count; **49** tickets sell (128 − 79) and 41 sold
    more than once. Also a fixture number doing argumentative work in a programme whose audit says "No number
    in this programme comes from `lib/mock/`".

11. **`01-b:149`** — "14 of 128 tickets redeem". *True:* 14 is a `redeem` row count; the record carries no
    ticket-level redemption count.

12. **`01-b:272`** — "`resalePriceCapBps` is *observed and varies*, across events and **across tiers within
    an event** … so the cap is an instrument". *True:* see A4.

13. **`01-a:133`** — "1.4% of primary revenue, **even after scaling for** the ~50% of resale the authors do
    not observe". *True:* the 1.4% is the observed half, unscaled; the paper's caveat is that half is
    missing.

14. **`01-a:125-126`** — "≈£184 gross average, **≈£269 per resale ticket** inclusive of all fees". *True:*
    £269 belongs to the £404m/1.5m pair; 269 × 1.9 = £511m, not £350m.

15. **`01-a:112`** — "He & Lin (*Marketing Science*, **2025**)". *True:* 2026, 45(3):515–533.

16. **`01-d:13`** — "**Nineteen** candidate variables were examined against §4.2 and **eleven survive** at
    usable priority." *True:* 28 examined (17 + 11 rejected), 9 at priority 1–2.

17. **`02-e:562` and `02-e:871` (E8)** — the band printed "as markup around face" with "−49% to +95%".
    *True:* that is a multiplier on the estimate; as markup over face centred at μ = 0.261 it is −33% to
    +153%.

18. **`02-a:896`** — "Mason, K. O., Mason, W. M., **Winship, C.**, & Poole, W. K. (1973)". *True:*
    Winsborough, H. H.

19. **`02-a:899`** and **`03-b:1024`** — "**Luo, L.** (2019)" against `10.1146/annurev-soc-073018-022616`
    (and in `03-b`, the title "Bayesian age-period-cohort analysis" and pages 109–132 as well). *True:*
    Fosse & Winship (2019), "Analyzing Age-Period-Cohort Data: A Review and Critique", 45:467–492.

20. **`00-ledger-verification.md:167`** — the S-prefixed Aigner DOI "returns HTTP 404 … This is the single
    unresolvable citation in the records". *True:* `01-b` does not contain that string; both its Aigner
    occurrences are the resolving form.

21. **`A-research-ledger.md:120`** — "`01-b` §7 cites Aigner (1973) as `10.1016/S0304-4076(73)90005-5`,
    which returns 404". *True:* it does not.

**What is not on this list, and why.** `09-sim-recovery.md`, `08-fix-verification.md`, `06-validation-protocol`
and `07-engine-review` produced no sentence I could show false; the sim study's summary framing (§3.3 above)
is imprecise about which conditions failed but every figure in it is the log's. `02-rubric` states the
rubric correctly. The Gap 5 table in `00-data-situation.md` §4 quotes all eight sites verbatim — I checked
each against the source sentence, including two that span a line break. `SUBMISSION-PACK.md`'s "does not
exist" table and `DELIVERABLE.md` §20.5's "P1.C as dispatched" are dated snapshots, each fixed in the same
document by a later note, and I do not count a dated measurement as a false sentence.

---

## 6. What a reader may trust now

The corrections that rest on an outside source — the Leslie & Sorensen 1.4% caveat, the DBT £269 pair,
He & Lin's year and volume, the two author attributions and the Ekeland issue and pages — are true against
those sources, and I re-queried every one rather than believing the correction, while the simulation study is
the best-evidenced file in the record: reproducible byte for byte from its own harness, with every number
traceable to its log. What a reader may not trust is any section read on its own, because nine false
statements sit in records no correction reaches and twelve more still stand unmarked in the bodies of files
whose correction is on the last page, so the section and the file disagree until the tail is read. The
deliverable's §20 is honest about almost everything the findings call out, but it was assembled before the
simulation study landed, so its §11 still says no coverage claim is available while a coverage number sits in
the record, and its §20.5 says the He & Lin question is settled while §21.2 says it is open.

---

*Nothing was edited but this file. Nothing was committed or pushed. The simulation harness was run once with
its output redirected to `/tmp`; no record was written.*

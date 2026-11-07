# 08: Independent verification of the console fix pass

**Status:** verification complete. I did not write any file except this one. No fix applied, no commit, no push, no dependency installed, no touch to `../ticketing-frontend` or `:3000`.
**UTC:** 2026-11-07T12:57Z. **Agent:** independent verifier. I did not make these fixes and did not work on the engine.
**What was verified:** the eight ranked fixes in `07-engine-review.md` §6, the five-minute catches in §7, the fix report appended to `records/BUILD-REPORT-CONSOLE.md` (12:45Z entry), and the regression tests it claims.
**The store did not move.** `fixtures/synthetic_store.json` on disk is `15e6f6611652ae43`, the hash the review pinned, so the data under every number below is the same store the review read.

**Two limits, stated up front.**

1. **The pre-fix tree was never committed.** `816637c` is the fix commit; its parent `cc779b3` predates the console entirely (`ticketpath/console/` does not exist there), so the reviewed 12:25 state cannot be re-run as shipped. For every fix I therefore reproduced the original defect by reverting that specific change in a scratch copy (`/tmp/rv`, `git archive` of the current tree) and serving the reverted code on its own port. Where the revert could not produce the visible symptom I say so and rely on the before-text quoted by both the review and the fix report.
2. **`records/` moved under me.** Three research records and one finding were rewritten at 12:54 to 12:56 by another writer (not me). `ticketpath/` and `tests/` did not move, and `git status` is clean for both. Verified hashes:

| File | sha256 (first 16) |
|---|---|
| `ticketpath/server.py` | `4f1da6fdc7289da2` |
| `ticketpath/orchestrator.py` | `b48fa121d46e4cff` |
| `ticketpath/console/blocks.py` | `75bf989464d2f748` |
| `ticketpath/console/page.py` | `fb80ec3329d2d720` |
| `ticketpath/core/labels.py` | `8e20449134faafe3` |
| `ticketpath/core/value_band.py` | `a094e3ff2477f478` |
| `ticketpath/core/price_features.py` | `6f465ce418e2c10d` |
| `ticketpath/api/guidance.py` | `f9a7df51b0664d27` |
| `tests/test_console_fixes.py` | `ffef106be3ee92ff` |
| `fixtures/synthetic_store.json` | `15e6f6611652ae43` |

Ports: reads on the running console at `8788`; scratch instances on `8891` to `8907`. `8787` was not touched. All of my instances are stopped and `8788` is still serving.

---

## 1. The eight fixes

| # | Fix | Original defect reproduced | Fix holds | Adjacent input tried | Result |
|---|---|---|---|---|---|
| 1 | Console total (C1, C5, C8) | **yes**, `HTTP 000`, curl exit 52, `ValueError: math domain error`, `/health` 200 (reverted copy on 8905) | **yes** | a sale exactly at `startsAt`; a store whose only event has no tiers; a zero-priced sale on a *different* event | 422 with a typed reason each time, no blank reply; the blast radius of one bad row is the whole console (fail-closed) |
| 2 | Two renderer defects (C2, C3) | **yes**, `4 of {'value': 6, 'badge': 'FIXTURE', …} recorded sales` and `insufficient_marks: {'value': 0, …} sales is too few` | **yes** | 8 events × 4 states (32 URLs); a tier with 1 and 2 marks; `capBps=0` on two other events | 0 occurrences of `{'value'`, `{'badge'`, `{n}`, `None`, `nan`; `9 of 9`, `4 of 4`, `4 of 6`, and `One sale is too few` all render |
| 3 | Every label true (A1, A13, A17, A2, A16, zero rate, fee) | **yes**, all seven, by revert (`On this event the ledger records 6 sales` beside `14 resales`; `the spread across 5 other events`; `3 events have completed` where 2 had) | **yes** | capped-not-binding event; `capBps=0`; two cuts for A17; a cut where the tier has 1 sale; a fee on a cold event | every renamed sentence is true where it prints; the cap sentences still appear on the event that has a cap |
| 4 | Decision mode COUNTERFACTUAL vs BEFORE-ON-SALE | **yes**, no mode statement anywhere (reverted page opens straight into `Recommended primary price: at least 1.38 SOL`) | **partial** | the same event in both modes on one server; a store with only one event | the mode machinery holds; the before-on-sale page states the event has no resale record while 12 sales are in the store |
| 5 | [EXACT] true at displayed precision | **yes**, `That is exactly 1.12 SOL` for 1,125,000,000 lamports (revert to two decimals) | **yes** | face `900,000,001` lamports, cap 2500, sales re-priced to the new ceiling | `ceiling 1,125,000,001 lamports … That is exactly 1.125000001 SOL`, headline `at least 1.125000001 SOL`; equality holds at nine decimals |
| 6 | Ticket count cut-aware | **yes**, `[FIXTURE] 12 tickets` at a cut before the first issue | **partial** | a cut exactly equal to the first issue instant | count is right (0, 1, 12 against the ledger) but the page then says `No ticket had been issued at this instant` beside `1 ticket` |
| 7 | Integer fee arithmetic, bound, negative-net state | **partial** (the float/bound path cannot be reached any more; reproduced only at the code level) | **yes** | fee exactly equal to the price; one lamport above; on a cold event; on an uncapped event | `0 SOL`, negative-net refusal, silence, and an exact 9-decimal net `0.880549431 SOL`; above `10**15` is a 400 |
| 8 | HEAD and POST methods | **yes**, `HTTP/1.1 501 Unsupported method ('HEAD')` with `do_HEAD` removed | **yes** | `HEAD` on an error URL, `POST /api/events`, `PUT /` | 404 mirrors, 405, and `PUT /` still 501 with Python's default page |

### The evidence for each line

**1. Console total.** Reverted copy, zero-priced store, port 8905:

```
curl -s -o /dev/null -w "status=%{http_code}" "http://127.0.0.1:8905/?event=evt_syn_04"
status=000   (curl exit 52)
log: ValueError: math domain error
/health: 200
```

Current code, the same store on 8892, 8893, 8894:

```
422 sale_not_priced: ledger row led_0065 is a sale recorded at 0 lamports; a sale must carry money, so this store cannot be priced back to the decision
422 sale_after_event_start: ledger row led_0084 is a sale 35.25 days after the event started; a negative time-to-event cannot be priced back to the decision
422 event_has_no_tier: This event has no tier to price, so there is nothing to show.
```

The default page still serves 200 with the tierless event present in the store. Over a socket, with `price_guidance` raising `ZeroDivisionError`: `500`, page with `console_error` and T1, no traceback in the body, `/health` 200 afterwards. With the renderer raising instead: `500` and the same page. Adjacency: a sale exactly at `startsAt` is accepted and the *next* sale at 0.46 days refuses, so the boundary is strict `>` and nothing crashes; a store whose only event has no tiers refuses `/` with `event_has_no_tier`; a zero face and a negative price are rejected by the loader at boot (`StoreError: tier … has a non-positive face value`, `ledger row … has an unusable price`), so there is no blank page to render. One observation, not a failure: a zero-priced sale on `evt_syn_01` makes `evt_syn_04` and `evt_syn_03` both 422, because the check is store-wide.

**2. Renderers.** Revert of `esc(value_of(…))` to `esc(…)` printed the wrapper verbatim, `[FIXTURE] 4 of {'value': 6, 'badge': 'FIXTURE', 'basis': '6 recorded sales in this tier', 'labelId': 'A1', 'unit': None} recorded sales`. Revert of the counted refusal printed `insufficient_marks: {'value': 0, 'badge': 'FIXTURE', …} sales is too few to fit a path`. On the current code the sweep of 32 URLs found no wrapper, no `{n}`, no `None`, no `nan`.

**3. Labels.** Live text, current code:

- `/?event=evt_syn_02`: strip `[FIXTURE] 12 resales on this event`; market `[FIXTURE] 9 sales of [FIXTURE] 12 on this event`; `In this tier the ledger records 9 sales. The sale rate above is this tier's own: its sales over its ticket-days at risk.`
- `/?event=evt_syn_03`: `the band is the declared literature prior on the log price-to-face ratio, widened by the declared τ on each side. It is not a spread measured across other events, and it has not been checked against a single sale here.` The printed band `0.65 – 1.26 SOL` is `0.70 × e^(0.2612 ∓ 1.6449 × 0.20)` = 0.654 to 1.263.
- `/?event=evt_syn_03&asOf=2026-11-21T23:30:00Z`: `2 events have completed in the observation window` twice, and the fixture has 2 ended by that instant.
- `/?event=evt_syn_03`: `[DECLARED] 7.5 per 1,000 ticket-days`, basis `0 sales over 131.6 ticket-days at risk; posterior mean of the declared Gamma(1, 1) prior on the transaction rate`, and `The rate above is not measured from the record … so it falls as that exposure grows and it is not zero.`
- `/?event=evt_syn_04`: `This event has no resale cap, so no ceiling enters the bound.` and `This event has no resale cap, so there is no ceiling to count against.` The words `the resale cap gives a ceiling` and `At the cap` are absent.
- `/?event=evt_syn_02&feeLamports=50000000`: `no_fee_model` absent, `[EXACT] Net to the seller per ticket: 1.33 SOL after the declared fee of 0.05 SOL.` present.
- `/?event=evt_syn_02&capBps=0`: `9 of 9 recorded sales in this tier are above this cap; had this cap been enforced, those transfers would have failed` and no `under the deployed program` anywhere on the page.

Adjacency on the same item: `/?event=evt_syn_01` (cap present, not binding) still prints both cap sentences and `at the ceiling [FIXTURE] 0`, which is true there; `/?event=evt_syn_01&asOf=2026-10-01T00:00:00Z` renders `In this tier the ledger records one sale.` and `One sale is too few to fit a path, so no path is quoted.`; `/?event=evt_syn_03&feeLamports=50000000` prints neither a net line nor `no_fee_model`, because there is no price to net. Silence, not a false sentence.

**4. Decision mode.** What holds: `Decision mode: COUNTERFACTUAL` with the sentence verbatim and `status on_sale · starts 2026-11-21T23:00:00.000Z · … · decision instant …` beneath it, on a page whose strip and market block use the same instant; `mode=nonsense` and `mode=whenever` are 400 `mode_invalid`; `mode=BEFORE-ON-SALE` normalises to the same state; in before-on-sale the platform count drops from 5 events with resale to 4, so the own record really is excluded; the band is named as `the pooled mean log price-to-face over 4 other events with resale`; a one-event store refuses the value block with `No other event on this platform has a resale record`. What does not hold is in §3 below.

**5. [EXACT].** `/?event=evt_syn_07` prints `[EXACT] ceiling 1,125,000,000 lamports = face 900,000,000 lamports × (10,000 + 2500) / 10,000 … That is exactly 1.125 SOL` and the headline `at least 1.125 SOL`. At face `900,000,001` lamports the same page prints `1,125,000,001 lamports … exactly 1.125000001 SOL` and `at least 1.125000001 SOL`, so the trim is exact beyond two decimals.

**6. Ticket count.** Against the fixture's issue rows: 0 issued at `2026-09-01T00:00:00Z`, 1 at `2026-09-11T11:00:00Z`, 12 at `2026-09-25T00:00:00Z`. The page prints `[FIXTURE] 0 tickets`, `[FIXTURE] 1 ticket`, `[FIXTURE] 12 tickets`. The count is right at all three.

**7. Fee arithmetic.** `50000000` gives `1.33 SOL`; `5000000000` gives `[REFUSED] The declared fee of 5 SOL per ticket is larger than the recommended price of 1.38 SOL, so a sale at that price would leave the seller short by 3.62 SOL per ticket. A negative net is not a price, so the line is refused rather than printed as one.`; `1380000000` (exactly the price) gives `0 SOL`; `1380000001` gives the shortfall state; `1000000000000001` and `999999999999999999999` are 400 `fee_invalid`; `1000000000000000` is accepted and refused as a negative net. `/?event=evt_syn_04&feeLamports=50000000` prints `0.880549431 SOL`, which is integer subtraction from `930549431`, not a rounded two-decimal value.

**8. Methods.** `HEAD /` → `200`, `content-type: text/html; charset=utf-8`, `content-length: 13147`, and `GET /` is also `13147`, no body. `HEAD /?event=evt_nope` → `404`. `POST /` → `405` with the rendered error page. `POST /api/events` → `405`. `PUT /` → `501` with Python's default error page.

---

## 2. The five-minute catches in §7

| Catch | Reproduced | Now |
|---|---|---|
| cold start: 0 sales, a non-zero rate, `[FIXTURE]`, basis `0 sales over 131.4 ticket-days` | **yes** (revert printed `[FIXTURE] 7.5`) | `[DECLARED] 7.5 per 1,000 ticket-days`, basis expanded to name the Gamma(1, 1) posterior mean, and a sentence saying the number is not measured and falls as exposure grows |
| default page: strip says 12, A1 says 9 | **yes** | strip 12, market `9 sales of 12 on this event`, A1 `In this tier the ledger records 9 sales.` |
| cold start: `5 events have completed` beside `One event has completed` | **yes** | `One event has completed` twice at the default cut (truth 1), `2 events have completed` twice at 2026-11-21T23:30Z (truth 2) |
| cold band: `the spread across 5 other events` over a literature prior | **yes** | names the literature prior; the printed band matches `0.70 × e^(0.2612 ∓ 0.329)` |
| uncapped page: `the resale cap gives a ceiling` with no cap | **yes** | replaced, and the cap-count sentence replaced too |
| `evt_syn_07`: `[EXACT] ceiling 1.12 SOL = face 0.90 SOL plus a cap of 25%` | **yes** | prints the lamport equality and `1.125 SOL` |

All six are closed.

---

## 3. The honesty answer

**With the eight named fixes in, a judge who reads the default page, the uncapped page, the cold start, the frozen-cap page, a fee state or the completed event is not misled: every number on those pages comes from the record, the sentences that describe them check out, and the ten false or mis-scoped claims the first review named are now true.** The exception is the before-on-sale page, which this pass added: it tells the reader that the event has no resale record, and shows `0 resales` and `0 tickets` under a `[FIXTURE]` badge, while the same server in the default mode reports `12 resales on this event · 12 tickets` for the same event from the same store. A second, narrower exception is the cut taken exactly at the first issue instant, where the page says no ticket had been issued beside a strip that says one had.

**Sentences still not true, with their URLs.**

1. `http://127.0.0.1:8788/?event=evt_syn_02&mode=before_on_sale`:
   `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.`
   The store holds 12 sale rows on `evt_syn_02`; the mode excludes them from the computation, it does not unrecord them. The same class of statement appears twice more on that page: `[FIXTURE] 0 resales on this event · [FIXTURE] 0 tickets`, and the payload basis `0 ticket rows exist in the store`, where 12 exist.
2. `http://127.0.0.1:8788/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z`:
   `[REFUSED] No ticket had been issued at this instant, so there is no denominator.`
   One issue row exists at exactly that instant, and the strip two lines above says `[FIXTURE] 1 ticket`. The sentence describes zero elapsed exposure, not a ticket that was never issued.

The one I would put in front of the operator first is the first: it is on a page a URL parameter produces, and its own regression test asserts the sentence is correct.

---

## 4. Regressions and residuals I found

| # | Where | What | Class |
|---|---|---|---|
| R1 | `/?event=evt_syn_02&mode=before_on_sale` | `0 resales`, `0 tickets` and `No resale has been recorded on this event`, all false at the record level; basis claims `0 ticket rows exist in the store` | **new**, from fix 4 |
| R2 | `/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z` | `1 ticket` beside `No ticket had been issued at this instant` | pre-existing sentence, exposed by fix 6's corrected count |
| R3 | `PUT http://127.0.0.1:8788/` | `501` with Python's default `Error response` page, no banner | pre-existing, same class as fix 8, outside its named scope |
| R4 | `/?event=evt_syn_03` | `That is a transaction rate for the ticket population …` renders twice (A1's tail and T4), one of the two badged | duplication, not a falsehood |
| R5 | the 422 pages | `[REFUSED] [REFUSED] 422 sale_not_priced: …`, two badges on one line | cosmetic |
| R6 | `/?event=evt_syn_03` | `0 events have completed in the observation window` at the default cut is true; at `asOf=2026-10-01` the same clause is also true (0 ended). No defect found here, recorded because it is the clause that was wrong before | checked, clean |

---

## 5. Test suite and regression tests

**Suite.** `python3 -m unittest discover -s tests -t .` → **Ran 352 tests in 12.152s, OK.** The review's last count was 309; the difference is `tests/test_console_fixes.py`, which holds **43** tests, all present and passing.

**Would the regression tests fail if the fix were reverted?** I reverted each fix in `/tmp/rv` and ran the named test. Fourteen of fifteen probes failed as required. Two probes needed the real site found first, which is itself worth knowing:

| Fix reverted | Test | Result |
|---|---|---|
| console catch (item 1) | `…test_a_pricing_exception_renders_a_labelled_page_not_an_empty_reply` | FAILS, pins |
| `capViolations["of"]` wrapper (2a) | `…test_the_cap_violation_sentence_prints_counts_not_wrappers` | FAILS, pins |
| counted refusal (2b) | `…test_the_insufficient_marks_refusal_fills_and_badges_its_count` | FAILS, pins |
| A1 sentence (3a) | `…test_a1_names_the_tier_its_count_comes_from` | FAILS, pins |
| A13 sentence (3b) | `…test_the_cold_band_is_said_to_be_the_declared_prior` | FAILS, pins |
| `completedAtCut` in `value_band.py` (3c) | `…test_the_page_counts_completed_and_not_started` | FAILS, pins (the test reads a payload leaf, so the revert has to be in `value_band.py`; the same word in `price_features.py` does not move it) |
| zero-rate basis (3d) | `…test_the_badge_the_basis_and_the_sentence_all_name_the_prior` | FAILS, pins |
| `fee_present` in `api/guidance.py` (3e) | `…test_the_no_fee_refusal_is_conditional_on_no_fee` | FAILS, pins (the page's refusal list comes from `guidance._refusals`, not from `primary_optimum`, so a revert there alone changes nothing) |
| mode block (4) | `…test_the_default_page_is_a_labelled_counterfactual` | FAILS, pins |
| `sol_exact` (5) | `…test_the_ceiling_is_printed_in_lamports_with_its_own_multiplication` | FAILS, pins |
| cut-aware count (6) | `…test_a_cut_before_the_first_issue_counts_no_ticket` | FAILS, pins |
| max fee (7) | `…test_a_fee_past_the_maximum_is_refused_before_it_is_computed` | FAILS, pins |
| negative-net branch (7) | `…test_a_negative_net_is_not_rendered_as_a_price` | FAILS, pins |
| **integer net (7)** | **`…test_the_net_line_is_integer_arithmetic`** | **STILL PASSES with float arithmetic restored**, so it does not pin the integer claim |
| HEAD (8) | `…test_head_mirrors_the_get_headers` | FAILS, pins |

**Tests that pin the behaviour, not something adjacent:** the cap-violation count, the counted refusal, the [EXACT] equality (it re-parses the printed numbers and re-does the multiplication), A13's band (it recomputes `0.70 × e^(0.2612 ∓ 1.6449 × 0.20)` and compares the payload), A17's single count, the cut-aware count (it recounts the issue rows by hand), the max fee, the negative-net state, HEAD's content length.

**Tests that do not pin what their name claims, or that pin the wrong thing:**

- `test_the_net_line_is_integer_arithmetic`: it compares `gross - fee` to the payload, and at `recommended = 1_380_000_000` a float and an integer give the same answer. The float revert passes all four tests in `TestTheFeeArithmetic`. The integer path is in the code (`(recommended * (10000 - ad_valorem) + 5000) // 10000`) and I verified it by hand, but no test would catch a regression to float.
- `test_a_later_cut_counts_the_tickets_issued_by_then`: `assertLessEqual(value, value)` is a tautology; the test's only real assertion is that the count is above zero at the default cut.
- `test_a_zero_priced_sale_refuses_with_a_typed_reason`: contains `row["eventId" if False else "id"]`, a dead expression, and the row it zeroes (`led_0002`) belongs to `evt_syn_01`, not `evt_syn_04`. It passes on the store-wide refusal rather than the per-event premise its docstring names.
- `test_the_maximum_fee_is_accepted_and_still_renders_a_state`: the name says "renders a state"; it asserts the payload's `negative` flag only.
- `test_before_on_sale_is_reachable_and_uses_only_other_events`: asserts `[FIXTURE] 0 resales on this event`, `[FIXTURE] 0 tickets` and `No resale has been recorded on this event` are present, so it locks R1 in. Fixing that sentence will fail this test.

**The fixer's own checker.** `python3 tools/console-check.py` prints `FAILURES: 0` against the live server. It checks for the absence of known bad strings and for the presence of the new sentences; it cannot catch a sentence that is false, and it does not visit `mode=before_on_sale` for truth, only for leaks.

---

## 6. What I did not do

- I did not re-review the engine, the mathematics, the frontend, or the chain slot.
- I did not verify the review's own claims that are outside this fix list (D1 as a product fork, the pooled estimator not being applied, the boundary price rule).
- I did not run the pre-fix tree as shipped, because it does not exist in git; every "reproduced" above is a faithful revert served on its own port, and I have said where a revert could not show the visible symptom (item 7).
- I did not touch `ticketpath/`, `tests/`, `fixtures/` or the running `8788` instance, and I did not read or write the fleet trees.

*End. One file written, this one. No commit, no push, no fix.*

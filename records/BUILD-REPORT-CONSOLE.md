# BUILD-REPORT-CONSOLE — what this pass built, and where it knowingly departs from the spec

**Written:** 2026-11-07T12:5xZ by the engine-engineer pass. **Scope:** the console page, the
engine behind it, the tests, and nothing else. No commit, no push, no change to
`../ticketing-frontend`, no touch to 8787 or the fleet's trees.
**Authority:** `records/BUILD-SPEC-NIGHT.md`. Where the brief and the spec disagreed the
spec won; each departure below is a spec line I deviated from and why.

## What exists now

`python3 -m ticketpath.server` then **http://127.0.0.1:8788/** — one server-rendered page,
stdlib only, no JavaScript required, every state a query parameter. The decision block on
the default (cap-binding) event reads, in order, `at least 1.38 SOL per ticket`, A19, the
floor line, `Range: 1.38 SOL and up. We do not state an upper bound from this record.`,
`This is a bound, not an optimum.`

Engine, as pure functions under `ticketpath/core/`, reached only through the orchestrator:
`price_features` (features at a mandatory cut), `value_band` (regimes, floor or band,
declared width, partial pooling), `path_model` (curvature, five guards, martingale),
`intensity` (composite rate, competing risks, gamma-Poisson zero), `primary_optimum`
(boundary recommendation, exact consequence table, four refusals), `labels` (58 ids and
the banned-phrase list).

## Deviations, each with its reason

1. **`GET /` is served outside `ROUTES`.** Counting the console in
   `implemented_route_count()` would change `/health.contract.routesImplemented` from 10 to
   12 and break `tests/test_http_contract.py`, which the spec says must keep passing
   untouched. The console is not a contract endpoint, so the route table stays the
   contract's and `CONSOLE_PATHS` handles `/` and `/favicon.ico`.
2. **`ticketpath/console/` is three files, not one.** `page.py` (shell, banner, controls,
   evidence, design panel, simulation, chain slot), `blocks.py` (decision, market,
   refusals), `units.py` (escape, badge, money, percent). The spec's single-file budget of
   320 lines could not hold all of §1.1's fourteen steps plus the four regimes.
3. **File budgets are exceeded in four places**: `labels.py` 362 (160), `value_band.py` 385
   (260), `price_features.py` 331 (220), `api/guidance.py` 412 (180). The causes are the
   sentence registry the spec puts in one file (58 ids including the page prose, because
   the spec forbids literals in the page), the badge plumbing that makes every number a
   three-field wrapper, and the module docstrings that record which finding each rule
   comes from. Recorded as a defect, not defended.
4. **τ pooling is declared below nine events, not five.** The brief says "declared rather
   than estimated below five events"; 03-b §6.4 puts the floor for any between-event
   quantity at about nine, and A17 says "the model is not fitted". Estimating at five would
   make the payload print a fitted tau beside a sentence saying nothing is fitted.
   Declaring below nine satisfies the brief's condition and removes the contradiction.
5. **The band width is exactly `2·z·τ`** (the spec's §4.7 invariant), not
   `2·z·√(τ² + V)`. The pooled predictive width is computed and returned as
   `pooledWidthLog`, and it does not move the band, because a width that changes with the
   event count would break the number a judge can check by hand. 02-e calls `2zτ` a floor
   on the width, so this is the narrowest admissible band, not a wider one.
6. **The path anchor is the median observation, not the pair of marginal medians.** 02-a
   §8.2 reads as two separately taken medians; those need not lie on the fitted curve, and
   on the noiseless test design the resulting path is off by 0.5% at every horizon. One
   observation, median in `d`, is coherent and exactly recoverable.
7. **Two guards the spec does not list, both adopted from findings:** `cap_mass_dominates`
   (03-b checklist row 15: more than half the marks on the ceiling, so no central path
   statistic) and `outside_support` (a local fit evaluated at a horizon the record does not
   cover produced factors of hundreds on this fixture; the curvature is still reported as a
   diagnostic and no path value is quoted).
8. **A tier with no marks inside an event with marks** reports the event's regime with
   `basis: pooled_across_tiers` rather than the `no resale` refusal. That is spec §3.4 rung
   3; `classify` alone would have returned `no_resale` and refused.
9. **`feeLamports` has no default.** Spec §1.1 step 2's example URL carries `feeLamports=0`;
   §4.7's table says net revenue is withheld with `no_fee_model`. Zero would make the net
   line appear by default. Absent means no fee model, and the tax consequence is honest
   because the recommendation is fee-neutral for an ad-valorem fee.
10. **`/health` now reports a registered model** (`engine-2026-11-07`) instead of
    `no_model_registered`, because the engine exists and the console serves it. One
    assertion in `tests/test_http_contract.py` was updated with that reason, and the same
    test still asserts `chain.programDeployed: false` and `programId: null`.
11. **`tools/devnet_check.py` was not built** (cut-list item 8) and `rpc_adapter.chain_status`
    is not called (item 10). `adapters/chain_client.py` does the quote hash and verifies an
    artefact file if one appears, and the chain slot renders its absent state. Nothing was
    invented to fill it.
12. **A stale `python3 -m ticketpath.server` (pid 242675, started 11:30Z by an earlier
    session in this directory) held 8788** and served a 404 at `/`. It was restarted, not
    killed and left: 8788 now serves the new code. 8787, 3000 and every other process were
    left alone.

## Measured, so it can be disputed with a number

- Suite: **293 tests, OK** (`python3 -m unittest discover -s tests`), 143 of them new.
- Fixture: `tools/build_fixture_store.py --check` — matches a fresh build exactly.
- The page across the seven reachable states: no banned phrase, no `title=`, no `<script`,
  no external asset, banner first, every `.n` span begins with a badge.
- Uncapped event: level 0.93 SOL, band 0.67–1.29 SOL at τ = 0.20 — matches §4.7(b) to the
  lamport. At τ = 0.406 the band widens to 0.48–1.81 and the point does not move.
- Binding event: 8 of 9 General-tier resales at the ceiling, 88.9%, floor = ceiling =
  1.38 SOL, no upper end.

---

## 2026-11-07T12:12Z — presentation pass: six defects seen on the rendered page

Scope: the six listed defects plus the two also-checks. No computed value, no refusal
reason, no label's meaning, no banned-sentence rule, no test assertion was changed, and
nothing was pushed or committed. Code touched: `ticketpath/console/page.py`,
`ticketpath/console/blocks.py`, `ticketpath/console/units.py`, `ticketpath/core/labels.py`;
one new test module, `tests/test_console_presentation.py`. No new dependency; 8787 and
`../ticketing-frontend` untouched; 8788 restarted on the new code
(pid 263482, was 255762).

Each defect was reproduced first by curling `http://127.0.0.1:8788/` and stripping tags.
Before and after are the stripped text.

1. **Badges doubling.** Before: `[FIXTURE] [FIXTURE] 12 resales on this event · [FIXTURE]
   12 tickets · [FIXTURE] 9 at the ceiling` and `[DEVNET] [DEVNET] 0 on-chain
   transactions`, and `[FIXTURE] exposure [FIXTURE] 435.1 ticket-days ticket-days at risk`.
   Cause: a literal badge in the paragraph *and* the badge `units.num` puts inside the same
   text run as the value, so `[X] <span class="n">[X] 12` printed twice. After: `[FIXTURE]
   12 resales on this event · [FIXTURE] 12 tickets · [FIXTURE] 9 at the ceiling`, `[DEVNET]
   0 on-chain transactions`, `exposure [FIXTURE] 435.1 ticket-days at risk`. The badge now
   lives only in the span with the number, which is the rule `units.num` documents and
   `tests/test_console_page.py` tests; the doubled unit word (`ticket-days ticket-days`) in
   that same sentence went with it, as a pure repeat. Fix: dropped the literal prefix at
   five call sites (`page.evidence` x3, `blocks.market` exposure, `blocks.decision`
   cap-violation line) and the restated unit.
2. **The banner repeated itself.** Before: line 2 `No program is deployed on any cluster.
   Nothing on this page is a deployed guarantee.` then line 3 `No program is deployed on any
   cluster. The [DESIGN] block at the bottom says what that means.` After: line 2 is the
   design pointer only. Cause: T5 was printed in the banner, and spec §2.3 puts T5 on the
   chain slot in its absent state. Fix: T5 removed from the banner and printed on the chain
   slot (`[DEVNET] No program is deployed on any cluster. Nothing on this page is a deployed
   guarantee.`), so the banner is now exactly spec §1.1 step 1's three lines and T5 is
   verbatim on the panel it belongs to. The two remaining copies of the sentence on the page
   (design panel `P_CHAIN_DESIGN`, chain slot T5) are separate panels, not consecutive
   sentences, and both are spec text.
3. **`None` in prose.** Before: `The 6 resales span None days and stop 52.3 days before the
   event, so the requested horizons fall outside the window the record covers.` After: `The 6
   resales stop 52.3 days before the event, so the requested horizons fall outside the window
   the record covers. No path value is quoted.` Cause: `blocks._refusal_fields` read
   `path.spreadDays.value`, and the api permits a wrapper with no value (`guidance.num(None)`
   returns `{"value": None}`; `path_model._refused` defaults `spread_days=None`), so the
   sentence was handed a `None` and `str.format` printed it. Fix: new registry id
   `outside_support_no_span` used when the span is absent — the clause that needs it is
   dropped, everything else in the refusal (count, stop, missing window, withheld value) is
   unchanged. `insufficient_time_spread` is deliberately not rewritten: its span is the
   reason it refuses, so a missing one must not be quietly dropped.
   **Honest note on reproduction:** no fixture event yields a missing span today, so there is
   no URL that prints it (I swept all 8 events x every tier x 10 instants x 9 caps: 1302
   distinct renders, no `None`). The before-text above is the sentence as the renderer
   printed it with the payload's `spreadDays` value absent, which is the shape the api
   permits; the after-text is the same state under the new code. The defect is closed at the
   renderer rather than in a URL, and `tests/test_console_presentation.py` locks it there.
4. **Pluralisation.** Before (`?event=evt_syn_01&asOf=2026-09-01T00:00:00Z`): `The model is
   not fitted. 1 events have completed in the observation window and 1 have any resale
   activity`, `the band is the spread across 1 other events`; and
   (`&asOf=2026-10-01T00:00:00Z`) `On this event the ledger records 1 sales.` After: `The
   model is not fitted. One event has completed in the observation window and it has resale
   activity`, `the band is the spread across one other event`, `On this event the ledger
   records one sale.` Fix: singular variants of the three registry sentences that carry a
   count of one (`A1_ONE`, `A13_ONE`, `A17_ONE_ONE`, plus `A17_ONE_M` for one event with
   resale beside several completed), chosen by two helpers in `blocks.py`; the page's own
   strip labels (`resales`, `tickets`, `events`, `on-chain transactions`) now go through a
   `units.plural()` so a future count of one reads as singular there too. Counts are
   unchanged: only the noun and verb agree.
5. **Two names for one quantity.** Before: `Band 0.74 – 1.25 SOL.` then, two lines later,
   `Range: 0.74 to 1.25 SOL. We would not argue with any price in that range.` After: `Band
   0.74 – 1.25 SOL.` then `We would not argue with any price in that range.` The interval is
   named once, as the band; the second sentence now carries only the claim the first does
   not. `P_BAND` and T3's "band" are spec text (§1.1 step 5, §2.3), so "band" is the term
   that survived.
6. **Repeats elsewhere.** The one other consecutive repeat the page had was the banner,
   covered by 2. A similarity scan over the same 1302 renders found no third family. One
   pair is left deliberately: see (a) below.

Also-check 1, precision inside one row: before `median markup [FIXTURE] 15% · mean markup
[FIXTURE] 13.7%` (and `1.2%` beside `3%` on the uncapped event); after `median markup
[FIXTURE] 15.0% · mean markup [FIXTURE] 13.7%` and `1.2% · 3.0%`. Cause: `units._bps`
stripped a trailing `.0` from whichever value happened to be round. Fix: a `trim` flag on
`num`/`bps_text`, both markups printed through `trim=False`; the cap and A19 keep `15%`.
Values unchanged, one decimal in the row.

Also-check 2, one unit for one quantity: **declined, nothing to fix on the page.** No prose
on the console prints `lamports`; every money value reaches the reader as SOL (the only
`lamport` strings are the form parameter names `feeLamports` and A19's prose about the
tier). The `"unit": "lamports"` strings are payload fields the JSON contract and
`tests/test_guidance_api.py` read, so relabelling them would be a wire change, not a
presentation one.

### Declined, with the reason

- **(a) `A1`'s closing sentence beside `T4`.** `A1` ends `That is a transaction rate for
  the ticket population, not the probability that a listed ticket sells.` and `T4`, printed
  immediately after, begins `That is a transaction rate for the ticket population,
  marginalised over whether the ticket was ever offered. It is not the probability that a
  listed ticket sells.` It is the same fact twice (975 of the 1302 renders). Cutting it means
  editing `A1`'s verbatim text (§2.6) or dropping a mandatory sentence (§2.3), and spec line
  940 says "the page prints A1 and T4 together, always". Two of your rules collide here
  (defect 6 vs spec §1–2 wording), so I left it and am naming both rather than picking one.
- **(b) The binding block's `Value: at least 1.38 SOL per ticket.` and `Range: 1.38 SOL and
  up.`** The same figure twice, but this is spec §1.1 step 4's block verbatim and §2.6's A19
  trio; a test asserts the range line's second sentence word for word. Left unchanged.
- **(c) `[EXACT] ceiling 1.38 SOL = face 1.20 SOL plus a cap of 15%`** directly after the
  headline's `at least 1.38 SOL`. It repeats the figure but adds the derivation from face and
  cap, which the headline does not carry — by defect 5's own rule ("if the second sentence
  adds a claim the first does not") it adds only that. Left unchanged.
- **(d) "range" survives in `A4`** (`The primary price recommendation is a range, not a
  point.`) and in `P_A19_RANGE`. Both are spec text (§2.6, §1.1 step 4), and `A4` is tested
  by id. The band's numbers now appear in exactly one place, so no quantity carries two
  names; the word "range" is left where the spec puts it.
- **(e) Two prose leaks found while scanning, outside the listed six, not touched:**
  (i) the cap-violation paragraph prints a payload dict — `?event=evt_syn_01&capBps=0` gives
  `1 of {'value': 6, 'badge': 'FIXTURE', 'basis': …, 'labelId': 'A1', 'unit': None} recorded
  sales`, because `esc()` is applied to `capViolations["of"]`, which is a number wrapper, not
  a number (`esc(count["value"])` beside it is right); one-line fix, and it is also the last
  source of the string `None` on the page.
  (ii) the `insufficient_marks` refusal prints its template unfilled — `The {n} sales is too
  few to fit a path; …` — on every no-resale event, because `labels.render` returns the
  template untouched when no fields are passed (`return template.format(**fields) if fields
  else template`). Both are pure presentation and meaning-neutral to fix; I left them because
  the brief for this pass was the listed six, and both change what a reader sees.

### Measured after this pass

- Suite: **306 tests, OK** (`python3 -m unittest discover -s tests`); 293 before, 13 new in
  `tests/test_console_presentation.py`, one per defect plus the two also-checks and a panel
  smoke check. I checked each new assertion fires on the before-text, so none of them is
  vacuous.
- Sweep: 1302 distinct renders (8 events x every tier x 10 instants x 9 caps x 3 taus x 3
  fees) — no doubled badge, no prose `None`, no `1 events`/`1 sales`/`1 other events`, no
  `ticket-days ticket-days`.
- The page across the seven reachable states: banner first and now three lines, T5 on the
  chain slot, decision/market/refusals/design/simulation/chain all present, no banned
  phrase.

## 2026-11-07T12:19Z — the two prose leaks above, fixed

Both are the leaks named at the end of the previous pass, and nothing else was touched:
two lines in `ticketpath/console/blocks.py`, no sentence, no number and no refusal logic
changed. `esc()` is no longer applied to a number wrapper, and the `insufficient_marks`
sentence is rendered from the registry with its count going through `units.num`, so the
number carries the badge it carries everywhere else.

1. Cap violation, `http://127.0.0.1:8788/?event=evt_syn_01&capBps=0`
   - before: `[FIXTURE] 4 of {'value': 6, 'badge': 'FIXTURE', 'basis': '6 recorded sales in
     this tier', 'labelId': 'A1', 'unit': None} recorded sales in this tier are above this
     cap; …`
   - after: `[FIXTURE] 4 of 6 recorded sales in this tier are above this cap; under the
     deployed program those transfers would have failed, so this record could not exist.`
   - cause: `capViolations["of"]` is a number wrapper and was escaped whole; `value_of()`
     now reads its value, as the count beside it already did.
2. `insufficient_marks` refusal, `http://127.0.0.1:8788/?event=evt_syn_03`
   - before: `[REFUSED] insufficient_marks: {n} sales is too few to fit a path; the flat
     line below is the benchmark, not a forecast.`
   - after: `[REFUSED] insufficient_marks: [FIXTURE] 0 sales is too few to fit a path; the
     flat line below is the benchmark, not a forecast.` — the count is
     `<span class="n">[FIXTURE] 0</span>`, the tier's own `market["sales"]` wrapper (`path_model`
     counts the same `tier["marks"]` list that wrapper counts), with its basis and label id.
   - cause: `_refusal_fields` had no branch for the label, and `labels.render` returns the
     template verbatim when no fields are passed.

Measured: suite **309 tests, OK** (`python3 -m unittest discover -s tests`), 306 before,
three new in `tests/test_console_presentation.py` (`TestNoPayloadShapesInProse` plus a
per-state check that no state prints `{n}` or `{'value'`); each fails on the before-text.
Server restarted on 8788 (job `jmw6deauo2ez7`); 8787 untouched. Left as found: the same
wrapper-not-value mistake in `_refusal_fields`' `cap_would_refuse` branch, which no payload
in this build reaches, and the registry's `{n} sales` wording, which reads `1 sales` at
`?event=evt_syn_01&asOf=2026-10-01T00:00:00Z`; both are outside this pass's brief.

## 2026-11-07T12:45Z — the independent review's fix list (sections 3, 4, 6), worked in order

**Scope:** `ticketpath/` and `tests/` only, plus two read-only check scripts under `tools/`.
No commit, no push, no change to `../ticketing-frontend`, no touch to 8787 or the fleet's
trees, no new dependency (stdlib only). The server on 8788 was restarted (`jmw6eaabld0g6`)
and every URL below was fetched from it. Suite: **352 tests, OK** — 309 before, 43 new in
`tests/test_console_fixes.py`. `python3 tools/console-check.py` re-checks all sixteen URLs
and the label claims against the live page and prints `FAILURES: 0`;
`python3 tools/console-check-stores.py` does the same for the three malformed stores.

### 1. The console is total (review C1, C5, C8)

- **`console_index` moved inside the handler's try** (`server.py:167` was outside the
  `try` at 170) **and catches `Exception`**, so a pricing failure ends in a status and a
  page. Only `ApiError` was caught before; anything else left the thread with no response.
  - before: `curl` → `HTTP 000`, "Empty reply from server"
  - after: `500`, `text/html`, `[REFUSED] 500 console_error: The console could not compute
    this page…`, traceback on stderr only
  - held by `TestTheConsoleIsTotal.test_a_pricing_exception_renders_a_labelled_page_not_an_empty_reply`
    and `…test_the_handler_catches_the_console_too`
- **Three loader-valid stores now refuse with a typed reason** instead of raising:
  a zero-priced sale (`price_features.FeatureError("sale_not_priced")`, was `math.log(0/face)`),
  a sale after the event started (`sale_after_event_start`, was `ValueError`), an event with
  no tiers (`event_has_no_tier`, was `IndexError` at `orchestrator.py:316`). All three render
  the error page with status 422 and the code on it.
  - before: HTTP 000 for each; after: 422 + a page + the code
  - held by `…test_a_zero_priced_sale_refuses_with_a_typed_reason`,
    `…test_a_sale_after_the_event_started_refuses_with_a_typed_reason`,
    `…test_an_event_with_no_tier_refuses_with_a_typed_reason`,
    `…test_a_malformed_store_still_answers_over_a_socket`
- **The tierless event no longer takes the default page out**: `default_selection` skips an
  event with no tiers when another event has one
  (`…test_the_tierless_event_does_not_break_the_default_page`).

### 2. The two renderer fixes on the judge path (review C2, C3) — kept, now pinned

Both were already in the working tree; each has its own regression test so a revert fails:

- `capViolations["of"]` goes through `value_of`, so it prints a count.
  before: `9 of {'value': 9, 'badge': 'FIXTURE', …} recorded sales` ·
  after: `9 of 9 recorded sales` — `…test_the_cap_violation_sentence_prints_counts_not_wrappers`
- `insufficient_marks` renders with its count, badged.
  before: `[REFUSED] insufficient_marks: {n} sales is too few…` ·
  after: `[REFUSED] insufficient_marks: [FIXTURE] 0 sales is too few to fit a path, so no
  path is quoted.` — `…test_the_insufficient_marks_refusal_fills_and_badges_its_count`
- The same sentence promised "the flat line below", and no path is drawn anywhere in the
  console (I did not add one). The sentence was changed, not the test:
  after: `…sales is too few to fit a path, so no path is quoted.`
  — `…test_the_insufficient_marks_sentence_promises_nothing_that_is_not_drawn`

### 3. Every label true (review 3.2–3.9)

Each is a sentence change, not a number change. No computed value moved.

| defect | before | after | test |
|---|---|---|---|
| A1 said "on this event", printed the tier's count (strip 14, A1 6 on `evt_syn_01`) | "On this event the ledger records **6** sales." | "In this tier the ledger records 6 sales. The sale rate above is this tier's own: its sales over its ticket-days at risk." | `TestA1CountsTheTierAndSaysSo` (3) |
| strip and market disagreed about resales (12 vs 9 on the default page) | strip `12 resales on this event` · market `sales 9` with no scope | strip `[FIXTURE] 12 resales on this event` · market `in this tier [FIXTURE] 9 sales of [FIXTURE] 12 on this event` | `…test_the_strip_and_the_market_block_agree_on_the_event_count` |
| A13 said the cold band was "the spread across 5 other events" | "…so the band is the spread across 5 other events and has not been checked against what those events sold for." | "…so the band is the declared literature prior on the log price-to-face ratio, widened by the declared τ on each side. It is not a spread measured across other events, and it has not been checked against a single sale here." | `TestA13NamesTheBandItUses` (2) |
| A17 said "completed" but counted started events, and two blocks printed two numbers (5 and One on one screen) | cold block `5 events have completed`, refusal panel `One event has completed` | both print the same completed count: `2 events have completed in the observation window and 5 have any resale activity` twice at `asOf=2026-11-21T23:30Z` | `TestA17CountsCompletedEventsOnce` (2) |
| A2/A16 talked about a ceiling on an uncapped event | "the resale cap gives a ceiling" + "at the ceiling 0 — At the cap" on `evt_syn_04` | "…This event has no resale cap, so no ceiling enters the bound." and the market line says "This event has no resale cap, so there is no ceiling to count against." `P_CAP_FORWARD` is no longer printed there either | `TestACapIsOnlyMentionedWhereOneExists` (2) |
| zero-sale rate presented as a fixture measurement with a basis that contradicted it | `[FIXTURE]` rate 7.6 · basis "0 sales over 131.4 ticket-days at risk" · "On this event the ledger records 0 sales. The sale rate is 7.6 …" | `[DECLARED] 7.6 per 1,000 ticket-days` · basis "0 sales over 131.4 ticket-days at risk; posterior mean of the declared Gamma(1, 1) prior on the transaction rate" · "In this tier the ledger records no sale. The rate above is not measured from the record: it is the posterior mean of the declared Gamma(1, 1) prior over the ticket-days at risk, so it falls as that exposure grows and it is not zero." | `TestTheZeroSaleRateIsNotAMeasuredRate` (2) |
| `no_fee_model` printed when a fee was set | `[REFUSED] no_fee_model: No fee model is configured.` with `feeLamports=50000000` | the refusal is emitted only when no fee is set; with a fee the net line renders: `[EXACT] Net to the seller per ticket: 1.33 SOL after the declared fee of 0.05 SOL.` | `TestTheFeeControlIsHonest` (3) |
| "under the deployed program" contradicted the banner (review 3.8) | "…above this cap; under the deployed program those transfers would have failed…" | "…above this cap; had this cap been enforced, those transfers would have failed…" (registry and page, one wording) | `?capBps=0` in `tools/console-check.py` |

### 4. The decision instant, decided and implemented (review 2.8, D1; fix-list item 4)

Two modes, both reachable from the control and the URL, and neither silent:

- **COUNTERFACTUAL is the default** for every event, completed or not:
  `[UNVALIDATED] Decision mode: COUNTERFACTUAL. This page recomputes the value from this
  event's own completed record: this is not a price you could have set; it is what the record
  implies in hindsight.` — with `Event … · status on_sale · starts 2026-11-21T23:00:00.000Z ·
  ends … · decision instant 2026-11-07T12:00:00.000Z` immediately beneath it, in a dark
  banner with an 8px red rule.
  before: `[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General
  tier.` and no statement anywhere of which record produced it or when.
- **BEFORE-ON-SALE** (`?mode=before_on_sale`) withholds this event's own ledger and ticket
  rows (`price_features.build(use_own_rows=False)`, `cross_section(own_record_excluded=…)`):
  only other events' completed resale records and this event's metadata enter. On this
  fixture the value block is then the pooled prior over the four other events with resale
  (`A13_POOLED` names the count and the centre), the primary price refuses
  (`no_resale_record`, because a pooled prior is not a record), and the market block says
  `No ticket had been issued at this instant`. With nothing to pool the whole value block
  refuses: `[REFUSED] No other event on this platform has a resale record, so there is
  nothing to pool for a before-on-sale value and we will not state one.`
  - held by `TestTheDecisionInstantIsExplicit` (7 tests: default label, completed event,
    unmissable placement, before-on-sale reachable and own record excluded, no-pool refusal,
    canonical URL and control, `mode_invalid` is a 400 and not a silent default)

### 5. The [EXACT] line is exact at its displayed precision (review 2.10, M10)

- before: `[EXACT] ceiling 1.12 SOL = face 0.90 SOL plus a cap of 25% — integer arithmetic on the
  tier face.` (0.90 × 1.25 = 1.125, so the equality was false as printed)
- after: `[EXACT] ceiling 1,125,000,000 lamports = face 900,000,000 lamports × (10,000 + 2500) /
  10,000 — integer arithmetic on the tier face, not an estimate. That is exactly 1.125 SOL.`
- Floors and ceilings print through `units.sol_exact`, which trims zeros from the exact decimal
  instead of rounding to two places, so the `at least` headline reads `at least 1.125 SOL`.
- held by `TestTheExactLineIsExact.test_the_ceiling_is_printed_in_lamports_with_its_own_multiplication`
  and `…test_every_binding_event_prints_an_equality_that_holds`, which parses the printed
  numbers back and re-does the multiplication.

### 6. The ticket count is cut-aware (review 3.9, C4)

- `price_features.build` counts issue rows at the cut for the strip, for `issuedCount` and for
  `sellThrough` (which feeds `netRevenue.perTier`); the store's own field stays available as
  `storeTickets` and is named in the basis.
- before: `?event=evt_syn_02&asOf=2026-09-01T00:00:00Z` → `[FIXTURE] 12 tickets` while the same
  page said `No ticket had been issued at this instant`
- after: `[FIXTURE] 0 tickets`, with the basis `tickets with an issue row at or before the cut;
  12 ticket rows exist in the store`
- held by `TestTheTicketCountIsCutAware` (3), one of which recounts the issue rows by hand.

### 7. Fee arithmetic (review C7)

- integer arithmetic: `gross = (recommended * (10000 - bps) + 5000) // 10000`, then subtract the
  per-ticket fee in lamports; no float anywhere on the net path
- `MAX_FEE_LAMPORTS = 10**15`; past it the page is a 400 `fee_invalid` instead of a 21-digit net
- a negative net is a state, not a price with a minus in front of it:
  `[REFUSED] The declared fee of 5 SOL per ticket is larger than the recommended price of 1.38
  SOL, so a sale at that price would leave the seller short by 3.62 SOL per ticket. A negative
  net is not a price, so the line is refused rather than printed as one.`
- held by `TestTheFeeArithmetic` (4).

### 8. Headers and methods (review C6)

- `HEAD /` mirrors `GET /`: 200, `text/html`, the same `content-length`, no body (was 501 with
  Python's default error page and the interpreter version in `Server`)
- `POST /` is 405 with the rendered error page (was 404); an unknown path is still 404
- held by `TestMethodsAndHeaders` (3).

### Verified surfaces

`python3 -m unittest discover -s tests -t .` → **352 tests, OK**. Live on
`http://127.0.0.1:8788`: cold start, default page, `evt_syn_04` (uncapped), `evt_syn_07`,
`capBps=0`, cut before the first issue, `evt_syn_06` (completed), `mode=before_on_sale`,
a fee, a fee above the price, `sim=1`, `mode=nonsense` (400), `capBps=nope` (400),
`evt_nope` (404), `HEAD /` (200), `POST /` (405) — all sixteen answer, all render a page,
and every label check passes. Three malformed stores over a socket: 422 with
`sale_not_priced`, `sale_after_event_start`, `event_has_no_tier`, each a rendered page.

### What I did not fix, and why

- **Review 3.11, badge placement inside prose.** A19's "8 of 9 (88.9%)" and the counts in the
  A1 sentence still sit in a paragraph whose badge is the block's, not the number's. It is
  outside the ranked fix list and it is not a false label (the same counts are printed with
  `[FIXTURE]` in the market block on the same screen). Fixing it means turning every
  count-bearing sentence into marker-substituted spans, which changes the page's badge model
  that `tests/test_console_page.py` enforces; that is a page rewrite, not this pass.
- **Review 5.2, the candidate cap is not passed to `primary_optimum`.** Also outside the
  ranked list, and it changes the recommendation on `capBps=0` — a product decision, not a
  label fix. Left as found and named here.
- **Review C8, the store validator vs the core.** The console now refuses the three rows
  cleanly, but `LedgerAdapter._validate` still accepts them; making the loader reject them
  would take the server down at load instead of on the page, so it needs its own pass.

## 2026-11-07T13:08Z — the four defects left by `08-fix-verification.md`

**Writer:** fix pass, not the verifier and not the engine reviewer. **Scope:** the four items
named in the brief and nothing else — one refusal sentence, three tests. No number, no
threshold, no refusal code and no arithmetic changed. Nothing committed, nothing pushed, no
dependency added, `../ticketing-frontend` and `:3000` untouched, 8787 untouched, and the
fleet trees were not read or written. The store on disk is unchanged:
`fixtures/synthetic_store.json` still hashes `15e6f6611652ae43`.

Files touched, and only these: `ticketpath/core/labels.py`, `ticketpath/console/blocks.py`,
`tests/test_console_fixes.py`.

### 1. The before-on-sale refusal said the event had no resale record

The event has 12 recorded sales. The mode excludes them; it does not unrecord them.

**before**, `http://127.0.0.1:8788/?event=evt_syn_02&mode=before_on_sale`:

> `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.`

**after**, same URL:

> `[REFUSED] This event's own resale rows are excluded by the BEFORE-ON-SALE decision mode, so
> its record supplies no price here; the band on this page is the pooled record of 4 other
> events on this platform, and a pooled band is not a price for this ticket, so no primary
> price is stated.`

How it is true by construction, not by wording:

- `blocks._cold_refusal` reads `decisionMode.usesOwnRecord` from the payload. The plain
  `no_resale_record` sentence is still what prints in the counterfactual mode, where the
  engine does use this event's rows and the count really is zero (`?event=evt_syn_03`, and
  `?event=evt_syn_02&asOf=2026-09-01T00:00:00Z`, both unchanged).
- The count is not typed into the sentence. It comes from `blocks._pool_events(payload)`, the
  same function that feeds the band label `A13_POOLED`, so the two sentences on the page
  cannot disagree about how many other events there are. `TestTheDecisionInstantIsExplicit`
  now asserts that the refusal's number equals the band label's number.
- The no-pool case has its own sentence (`no_resale_record_excluded_no_pool`): with zero other
  events there is no band on the page, so the pooled-band clause would be false there. It is
  selected on the same count.
- The typed reason code is unchanged: `no_resale_record` is still what the payload carries;
  only the sentence differs by mode.
- One adjacent sentence was saying the same untrue thing and had to move with it, or the page
  would still have told the reader the event's own record does not exist: `A13_POOLED` read
  `this event has no resale record of its own`, and now reads `this decision excludes this
  event's own resale rows`. `A13_POOLED` prints only in the before-on-sale pooled case. No
  number in it changed; `pooled mean log price-to-face over {n_events} other events with
  resale` is preserved word for word.

Held by `TestTheDecisionInstantIsExplicit.test_no_sentence_says_this_event_has_no_resale_record`
(item 4) and `…test_before_on_sale_is_reachable_and_uses_only_other_events`.

### 2. The integer-arithmetic test did not pin integer arithmetic

**before:** the test compared `netRevenue.perTicket` to `gross - fee` at a per-ticket fee of
50,000,000. With no ad-valorem part, a float and an integer give the same answer, so the test
passed with float arithmetic restored. The verifier said so and was right.

**after:** the page assertion stays (type plus `gross - fee`), and the two cases that separate
the arithmetic are asserted on `primary_optimum.recommend` directly, because the console's fee
control cannot reach the ad-valorem half of the money path:

| price | ad valorem | integer half-up | what a float gives |
|---|---|---|---|
| 930,549,431 | 5000 bps | 465,274,716 | 465,274,715 (truncation of x.5) |
| 2^53 + 1 | 5000 bps | 4,503,599,627,370,497 | 4,503,599,627,370,496 (product not exact in a float) |

The implementation was not touched. Reverting it and watching the test fail:

```
gross = int(recommended * (10000 - ad_valorem) / 10000)
  FAIL … AssertionError: 465274715 != 465274716
  FAIL … AssertionError: 4503599627370496 != 4503599627370497
gross = int(round(recommended * (10000 - ad_valorem) / 10000))
  FAIL … AssertionError: 4503599627370496 != 4503599627370497
restored: sha256 0d4550b02386aee6… , test OK
```

The second case is there so rounding cannot rescue a float: beyond 2^53 the product is not
representable, so every float form, `round()` included, lands one lamport low.

### 3. `assertLessEqual(value, value)` was a tautology

**before:** `test_a_later_cut_counts_the_tickets_issued_by_then` counted the tickets at the
default cut, asserted the count was above zero, then compared the count to itself.

**after:** it hand-counts the store's own `issue` rows at three cuts (2026-09-01, the first
issue instant, the last issue instant), compares the page's count to the hand count at each,
and asserts the count strictly rises across them. A count that ignores the cut fails on the
first and a count that ignores issue rows fails on all three.

Reverting the cut-awareness (`issued = len(tier_tickets)`) and watching it fail:

```
FAIL … AssertionError: 12 != 0 : count at 2026-09-01T00:00:00Z
restored: sha256 6f465ce418e2c10d… , tests OK
```

### 4. The before-on-sale test asserted the false sentences were present

**before:** it required `[FIXTURE] 0 resales on this event`, `[FIXTURE] 0 tickets` and
`No resale has been recorded on this event` to be on the page, so it locked the untrue sentence
in and any repair to item 1 would have failed it.

**after:** `test_no_sentence_says_this_event_has_no_resale_record` asserts the premise from the
store first (this event has sale rows), then asserts that no sentence matching the claim class
is on the page — `no resale has been recorded on this event`, `this event has no resale record`,
`this event has no resales`, `there are no resales on this event`, `no resale rows exist for
this event`, `this event sold nothing` — and that the page says what is true instead: the mode
excludes the rows, and the pool is named as the source. The claim class, not one string,
because a repair to one phrasing would have left the others.

Reverting the sentence and the band label and watching it fail:

```
FAIL … the page says 'this event has no resale record' while 12 sale rows exist on this event
FAIL … 'excluded by the BEFORE-ON-SALE decision mode' not found in "…"
restored: sha256 c7ff447ed9fdaab2… (labels) 974e429e98c01549… (blocks), tests OK
```

Why the two strip assertions were dropped rather than inverted: `page.evidence` prints
`[FIXTURE] 0 resales on this event · [FIXTURE] 0 tickets` in this mode from the mode-scoped
counts in the payload. Those are counts, not sentences, and changing them is a change to a
number, which this pass was told not to make. They are the remaining half of R1 in
`08-fix-verification.md` and are named below, not silently accepted.

### Verified after the change

- `python3 -m unittest discover -s tests -t .` → **Ran 353 tests, OK** (352 before; one test
  became two, so `tests/test_console_fixes.py` holds 44).
- `python3 tools/console-check.py` against the live server → `FAILURES: 0`.
- Server restarted on 8788 (`python3 -m ticketpath.server`, log
  `~/.pi/jobs/jmw6f4vpul87b.log`); 8787 was not touched.
- The four URLs `08-fix-verification.md` names:

| URL | status | what it renders now |
|---|---|---|
| `/?event=evt_syn_02&mode=before_on_sale` | 200 | the exclusion sentence above; `Decision mode: BEFORE-ON-SALE`; `pooled mean log price-to-face over 4 other events with resale`; no sentence of the denial class |
| `/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z` | 200 | unchanged: `[FIXTURE] 1 ticket` beside `No ticket had been issued at this instant` (R2) |
| `PUT /` | 501 | unchanged: Python's default error page, no banner (R3) |
| `/?event=evt_syn_03` | 200 | unchanged: the counterfactual cold page, `That is a transaction rate…` twice (R4) |

- Also re-rendered and unchanged on the same server: `/?event=evt_syn_03` (counterfactual
  refusal, still `No resale has been recorded on this event…`, true there),
  `/?event=evt_syn_02` (default), `/?event=evt_syn_04`, `/?event=evt_syn_07`, `capBps=0`,
  `feeLamports=50000000`, `feeLamports=5000000000`, `mode=nonsense` (400), and the one-event
  store in before-on-sale (the no-pool sentence).

### What this pass did not touch, and why

- **R1's counts.** `[FIXTURE] 0 resales on this event`, `[FIXTURE] 0 tickets` and the basis
  `0 ticket rows exist in the store` still print in before-on-sale mode. They are mode-scoped
  counts presented under an event-level noun; making them true means either changing a number
  or re-scoping the strip's nouns, and the brief for this pass is wording in the refusal only.
  Named here so it is a known residue, not a fix I claim.
- **R2** `No ticket had been issued at this instant` at a cut exactly on the first issue
  instant, **R3** `PUT /` returning Python's 501 page, **R4** the duplicated A1/T4 sentence,
  **R5** the doubled `[REFUSED]` badge on 422 pages. All four are in the verifier's list and
  none of them is one of the four items this pass was given.
- The engine, the arithmetic, the payload, the thresholds and the page's other blocks.

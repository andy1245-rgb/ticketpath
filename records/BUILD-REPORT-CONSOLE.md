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

## 2026-11-07T13:40Z — the five residues: R2, R3, R4, R5, and the counts inside A19 and A1

**Writer:** residue fixer, not the verifier and not the engineer reviewer. **Scope:** the
five items named in the brief and nothing else. No number, threshold, refusal code or
arithmetic changed; the engine, the payload's computed values, the store and the fixture
hash are untouched (`fixtures/synthetic_store.json` is still `15e6f6611652ae43`). Nothing
committed, nothing pushed, no dependency added, `../ticketing-frontend` and `:3000`
untouched, 8787 untouched, and the fleet trees were not read or written.

Files touched, and only these: `ticketpath/console/blocks.py`,
`ticketpath/console/page.py`, `ticketpath/console/units.py` (docstring),
`ticketpath/core/labels.py`, `ticketpath/server.py`, `tests/test_console_fixes.py`,
`tests/test_console_page.py`, `tools/console-check.py`, `docs/CONSOLE.md`, and this
section. Hashes after the pass: `blocks.py bad697e5ce4243c5`, `labels.py b98be810efc9b2c8`,
`page.py 7fbde2fff50becee`, `server.py f14961ca2591c1b0`,
`tests/test_console_fixes.py 20bc8fcd3116ce81`.

**The tree moved under this pass.** `records/findings/09-sim-recovery.md`, `records/sim/`
and `tools/sim_recovery.py` appeared while it ran, from another writer (not me), and
`NIGHT-LOG.md` was already modified when it started. I did not touch any of them, and
`ticketpath/` and `tests/` hold my changes and nothing else.

**Note on the item numbers.** The verifier's R4 is the duplicated A1/T4 rate sentence and
its R5 is the doubled `[REFUSED]` badge on error pages. The brief for this pass defines its
R4 as a cap sentence on an uncapped event and its R5 as a count that is not cut-aware, and
these five entries are what those definitions name. Both verifier items are named in
"What I chose not to change" below, untouched.

### R2. `1 ticket` beside "No ticket had been issued at this instant"

The event's first issue row is at exactly that instant, so the cut counts one ticket and
the exposure denominator is zero: the sentence described the denominator and blamed the
issue record.

**before**, `http://127.0.0.1:8788/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z`:

> `[FIXTURE] 0 resales on this event · [FIXTURE] 1 ticket · [FIXTURE] 0 at the ceiling`
> … `[REFUSED] No ticket had been issued at this instant, so there is no denominator.`

**after**, same URL:

> `[REFUSED] [FIXTURE] 1 ticket had been issued on this event by this instant, but no
> ticket-day of exposure has elapsed in this tier, so the rate has no denominator.`

How it is true by construction:

- `blocks._no_exposure_sentence` reads `payload["evidence"]["tickets"]`, the same wrapper
  the strip prints, so the sentence and the strip cannot disagree about the count. It
  branches on that count: zero keeps `no_exposure` verbatim, one takes
  `no_exposure_issued_one`, more than one takes `no_exposure_issued`.
- The zero case is unchanged and still prints at
  `?event=evt_syn_02&asOf=2026-09-01T00:00:00Z` and on `?event=evt_syn_08`, where the store
  really has no issue row (`[FIXTURE] 0 tickets`).
- The clause says "in this tier" because the denominator is the tier's: if the event's
  tickets sat in another tier, this tier's exposure would still be zero and the sentence
  would still be true. No tier in this fixture is in that state, so the wording is belt and
  braces rather than a case a URL reaches.
- The count is badged and sits in its own span, through the helper the `{n}` refusal already
  used.

Held by `TestTheZeroExposureRefusalFollowsTheCut` (4 tests: the fix, the zero case kept, the
sentence's number equal to the strip's number, and a hand-built store with two tickets
issued at one instant for the plural). Reverting the sentence to
`labels.render("no_exposure")` fails three of the four, one of them with
`'No ticket had been issued at this instant' unexpectedly found`; the fourth, the zero case,
is the guard against over-correcting and passes either way.

### R3. `PUT /` returned 501

Python's `http.server` answers an unimplemented verb with its own 501 page, which is a
different answer to the same question `POST /` gets.

**before:** `PUT http://127.0.0.1:8788/` → `501`, body Python's own page:
`Error response / Error code: 501 / Message: Unsupported method ('PUT').`

**after:** → `405`, the console's rendered error page:
`[REFUSED] [REFUSED] 405 method_not_allowed: PUT is not allowed here; allowed: GET, HEAD`.

- `do_PUT`, `do_DELETE` and `do_PATCH` route into the same `_handle` the other verbs use, so
  a route that exists answers 405 and a path that does not is still 404, exactly as for GET.
  `DELETE /` and `PATCH /` were 501 for the same reason and are 405 now.
- One new plumbing line: a verb that never reads a body sets `close_connection` when the
  request carries one, so an unread body cannot be parsed as the next request on a
  keep-alive socket. Checked over the socket with `PUT /` plus `{"capBps":0}`: 405, then
  `GET /` 200 on a new connection.
- `HEAD /` 200, `GET /` 200, `POST /` 405 are unchanged.

Held by `TestVerbsThisServerDoesNotImplement` (3 tests). Removing the three `do_*` methods
fails them with `501 != 405` on the console route and the API route and `501 != 404` on the
unknown path.

### R4. A sentence about a cap on an event whose regime is uncapped

The decision block printed "A cap does not hide the price; it hides the top of the price
distribution" on every page, including the three events whose cap field is null and whose
own regime line says `uncapped` two lines below it. On those pages it read as a claim about
a cap this event does not have.

**before**, `http://127.0.0.1:8788/?event=evt_syn_04`:

> `[UNVALIDATED] Decision mode: COUNTERFACTUAL. … A cap does not hide the price; it hides
> the top of the price distribution.` … `regime [FIXTURE] uncapped`

**after**, same URL:

> `… No cap applies to this event, so nothing hides the top of the price distribution.` …
> `regime [FIXTURE] uncapped`

- New registry id `P_CAPLINE_UNCAPPED`; `blocks.decision` chooses on
  `payload["event"]["capBps"]`, the same field the A2/A16 branch already reads. Where a cap
  exists the spec's line is printed word for word and no negative appears
  (`evt_syn_01`, `evt_syn_02`, `evt_syn_03`).
- The uncapped page's other cap sentences were already conditional (A2_UNCAPPED, `P_NO_CAP`,
  `P_CEILING_NONE`), or are inside `[DESIGN]`, which describes the program rather than this
  event. I read every sentence on `evt_syn_04`, `evt_syn_05` and `evt_syn_08` looking for a
  positive cap claim; this was the only one left.

Held by `test_the_uncapped_page_does_not_say_a_cap_hides_the_top_of_the_distribution` (three
uncapped events, each asserted to have a null cap first) and
`test_a_capped_page_keeps_the_cap_line` (three capped events). Reverting the line to the
unconditional `P_CAPLINE` fails the first on all three events.

### R5. A count that is not cut-aware, beyond the ticket count

I swept for one and there is no other stale number on the page. The sweep takes eight
events, every tier of each, six cut instants and both decision modes, and compares the
page's counts against a hand count of the store's own rows at the same instant: the ticket
count from `issue` rows, the resale and at-ceiling counts from `sale` rows, the tier's
sales, the events with a resale, the events completed. **Zero mismatches**, and
`TestNoCountOnThePageIsStaleAtTheCut` keeps six of those cases in the suite.

The one printed count that cannot follow a cut is the event total, and it was presented as
if it could. The schema carries no instant at which an event was created, so "8 events" is
the store's event list at every cut, while the strip sits under the sentence "Nothing after
{asOf} enters any number".

**before**, `http://127.0.0.1:8788/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z`:

> `[FIXTURE] 8 events on this platform, [FIXTURE] 1 with any resale`

**after**, same URL:

> `[FIXTURE] 8 events in the store, [FIXTURE] 1 with any resale at this instant`

- No number changed: the noun now names what the number counts, and the clause beside it is
  the one that moves with the cut (1 at that instant, 2 at 2026-09-11, 5 today).
- This is the "re-scope the noun" fix shape the 13:08Z pass named, chosen over inventing an
  event-creation timestamp the schema does not carry.
- `docs/CONSOLE.md` quoted the old strip text and was updated with it.
  `tools/console-check.py` gained a check that the store count is named as the store's and
  that the cut-aware clause moves.

Held by `test_the_event_total_is_named_as_the_store_and_the_cut_count_beside_it_moves`
(reverting the noun fails it) and `test_the_strip_and_the_market_counts_are_the_counts_at_the_cut`.

### Review 3.11. The counts inside A19 and A1

A19's "8 of 9 (88.9%)" and A1's "records 9 sales" sat in paragraphs whose nearest badge was
the panel's `[UNVALIDATED]`, while each of those numbers is a `[FIXTURE]` count. The badge
now travels with the number.

**before**, `http://127.0.0.1:8788/?event=evt_syn_02`:

> `The resale price in this tier is capped at 15% over face, and the cap is binding: 8 of 9
> recorded resales (88.9%) settled at exactly the ceiling.`
> `In this tier the ledger records 9 sales.`

**after**, same URL (spans shown as the reader's text; the markup is one `.n` span each):

> `The resale price in this tier is capped at [FIXTURE] 15% over face, and the cap is
> binding: [FIXTURE] 8 of [FIXTURE] 9 recorded resales ([FIXTURE] 88.9%) settled at exactly
> the ceiling.`
> `In this tier the ledger records [FIXTURE] 9 sales.`

- `blocks._sentence` hands each count to `labels.render` as a marker and replaces the marker
  with `units.num`'s output, so the wording stays the registry's and one sentence can carry
  four badged numbers. The cap percent is the record's own bps wrapper; the share is the
  ratio of the two badged counts and takes the sales count's badge.
- Two registry edits came with it: A19's template now reads `{c} over face` and `({s})`
  because the percent sign travels inside the badged number, and A1's `{n}` is substituted
  as a span instead of a bare int. The printed digits are identical, which the whole-page
  digit comparison below shows for every state.
- A1_ONE and A1_ZERO say `one sale` and `no sale`; they carry no digits and need no badge,
  so they print exactly as before.
- **The badge model did not move; two test expectations did, and in the strict direction.**
  The two A1 assertions in `tests/test_console_fixes.py` now require the badge
  (`"In this tier the ledger records [FIXTURE] 6 sales."`), and
  `tests/test_console_page.py` gained two tests that pin the new rule in both directions:
  each of A19's four counts and A1's count is a `.n` span that begins with a badge, and with
  every badged span stripped out of the page the sentence's digits are gone. The old
  rendering fails both (`'<span class="n">[FIXTURE] 15%</span>' not found`, and the regex
  `\d+ of \d+ recorded resales` matching) while the existing badge tests still pass, so
  nothing was weakened to make room for this.

### No number moved

The whole page's digit multiset was compared between the pre-pass tree (`git archive HEAD`)
and the current tree over 25 states: the default page, all eight events, four cuts on
`evt_syn_02`, two non-default tiers, `capBps=0` on a capped and on an uncapped event, three
fees, `sim=1`, both decision modes, `tau=0.406`, and `mode=nonsense`. Every state's status
and every digit token are identical except one: the R2 state gains a second `1`, which is
the count its new sentence carries and which the strip was already printing. The percent
signs in A19 moved into the badged numbers without changing a digit
(`capped at [FIXTURE] 15%` where it read `capped at 15%`).

### What I chose not to change

- **The doubled `[REFUSED]` badge on error pages** (the verifier's R5, and the reason the
  new 405 page reads `[REFUSED] [REFUSED] 405 method_not_allowed: …`). It is cosmetic, it is
  not one of the five items, and it is one line in `page.render_error`. Left as found and
  named here.
- **R1's mode-scoped counts on the before-on-sale page.** `[FIXTURE] 0 resales on this
  event · [FIXTURE] 0 tickets` and the basis `0 ticket rows exist in the store` still print
  where the store holds 12. Making them true means changing a number or giving the strip a
  mode-aware noun table; both are outside this brief, and the previous pass names it.
- **The `[DEVNET]` on-chain transaction count.** It is the one other printed count that does
  not move with the cut, because it is a live chain read at wall-clock time, badged
  `[DEVNET]` rather than `[FIXTURE]` and not a count of the record. Making it cut-aware
  would need chain state per instant, which the artefact file does not carry.
- **The duplicated A1/T4 rate sentence** (the verifier's R4, not the cap line this brief
  calls R4): spec section 2.3 and spec line 940 require A1 and T4 together, so it stays.
- **Review 5.2, the candidate cap not reaching `primary_optimum`, and C8, the store
  validator versus the core.** Both still stand where the earlier passes left them; neither
  is a label, and the first changes a recommendation.

### Verified after the change

- `python3 -m unittest discover -s tests -t .` → **Ran 366 tests, OK** (353 before; 13 new:
  11 in `tests/test_console_fixes.py`, 2 in `tests/test_console_page.py`).
- `python3 tools/console-check.py` against the live server → **FAILURES: 0** (19 response
  cases, three of them new: `PUT /`, `DELETE /` and `PATCH /` at 405, plus the new label
  checks).
- Server restarted on 8788 (`python3 -m ticketpath.server`, job `jmw6g5m1vume9`, pid
  287813); 8787 was not touched and is still the fleet page's.
- Each new test was shown to fail on the old behaviour, by reverting that one change in a
  scratch copy of the tree (`git archive HEAD` in `/tmp/old` and `/tmp/res`), never in
  place:

| Fix reverted | Failing assertion |
|---|---|
| R2 sentence | `'No ticket had been issued at this instant' unexpectedly found` (3 of 4 tests) |
| R3 verbs | `501 != 405` on `/` and on `/api/events`, `501 != 404` on `/nope` |
| R4 cap line | `'A cap does not hide the price' unexpectedly found` on evt_syn_04, 05, 08 |
| R5 noun | `'[FIXTURE] 8 events in the store,' not found` |
| A19/A1 badges | `'<span class="n">[FIXTURE] 15%</span>' not found`; regex `\d+ of \d+ recorded resales` matched |

- By hand on the restarted server, the five URLs and the pages around them:

| URL | status | what it renders now |
|---|---|---|
| `/?event=evt_syn_02&asOf=2026-09-11T11:00:00Z` | 200 | the issue-count sentence above; strip `[FIXTURE] 1 ticket`; no `No ticket had been issued` |
| `/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z` | 200 | `[FIXTURE] 0 tickets` and the original no-denominator sentence, unchanged |
| `PUT /` | 405 | the rendered page and `method_not_allowed`; no Python 501 page, no `Unsupported method` |
| `PUT`, `DELETE`, `PATCH` on `/api/events` | 405 | typed `method_not_allowed`; on `/nope` all three are 404 |
| `/?event=evt_syn_04` | 200 | `No cap applies to this event, so nothing hides the top of the price distribution.` beside `regime uncapped`; `A cap does not hide the price` absent |
| `/?event=evt_syn_05`, `/?event=evt_syn_08` | 200 | the same negative line, and no positive cap claim |
| `/?event=evt_syn_01`, `evt_syn_02`, `evt_syn_03` | 200 | the spec's cap line, word for word, and no negative |
| `/?event=evt_syn_02` | 200 | `records [FIXTURE] 9 sales`, `capped at [FIXTURE] 15%`, `[FIXTURE] 8 of [FIXTURE] 9 recorded resales ([FIXTURE] 88.9%)` |
| `/?event=evt_syn_01`, `/?event=evt_syn_07` | 200 | the same shape: `[FIXTURE] 6 sales`, `[FIXTURE] 4 sales`, `25%`, `100.0%` |
| `/?event=evt_syn_02&mode=before_on_sale`, `evt_syn_06`, `capBps=0`, `feeLamports=50000000`, `feeLamports=5000000000`, `sim=1` | 200 | unchanged, including A1_ONE and A1_ZERO (`one sale`, `no sale`) |
| `/?capBps=nope` (400), `/?event=evt_nope` (404), `/?mode=nonsense` (400) | 400 / 404 / 400 | unchanged |
| `HEAD /` | 200 | same headers as GET, no body |

*End of this pass. Five defects, five repairs, one item left alone and named.*

## 2026-11-07T13:58Z — the two defects the review left open: the cap that never reached the optimum (§5.2), and the loader that admitted what the core cannot price (C8)

**Writer:** fix engineer. **Scope:** `records/findings/07-engine-review.md` section 5.2 and
C8, and nothing else. No fixture, no store, no threshold and no other number, sentence or
refusal changed; `fixtures/synthetic_store.json` is still `15e6f6611652ae43`. Nothing
committed, nothing pushed, no dependency added. `../ticketing-frontend` and `:3000` were not
touched, 8787 was not touched, and the fleet trees were not read or written.

Files touched, and only these: `ticketpath/core/primary_optimum.py`,
`ticketpath/orchestrator.py`, `ticketpath/adapters/ledger_adapter.py`,
`ticketpath/core/labels.py`, `ticketpath/console/blocks.py`,
`ticketpath/console/units.py` (one new formatting kind), `ticketpath/api/guidance.py`,
`tools/build_fixture_store.py`, `tools/console-check-stores.py`, `docs/CONSOLE.md`,
`tests/test_cap_and_loader_refusals.py` (new, 14 tests), `tests/test_console_fixes.py`
(two tests rewritten, see below), `tests/test_labels.py` (three sample fields), and this
section. Hashes after the pass: `primary_optimum.py 53322138877df920`,
`orchestrator.py 32f3f440330ee72a`, `ledger_adapter.py 4b11dd712e5afa36`,
`labels.py 8d2ea5d16cf584cc`, `blocks.py eef3545d88a13a80`, `units.py 38e435a993d08016`,
`guidance.py 2c97d3977ccdafa5`, `tools/build_fixture_store.py 8aca72e9a6a4bcfc`,
`tests/test_cap_and_loader_refusals.py 2dc0de323e8ff577`.

### 1. The cap in force is now a rule on the recommendation (§5.2)

`price_guidance` resolved a cap for the payload (`selection.capBpsCandidate`, the URL's cap
or the recorded one) and passed it to `value_band.estimate` only. `primary_optimum.recommend`
had no such parameter, so the number and the page disagreed: the page reported a cap, the
recommendation ignored it, and on `?event=evt_syn_01&capBps=0` the page printed 1.03 SOL per
ticket against a ceiling of 1.00 SOL that its own cap implies.

**before** (old code, `http://127.0.0.1:8788/?event=evt_syn_01&capBps=0`, status 200):

> `[UNVALIDATED] Recommended primary price: 1.03 SOL per ticket.`
> `[UNVALIDATED] Band 0.74 – 1.25 SOL.`
> `[FIXTURE] 4 of 6 recorded sales in this tier are above this cap; ...`

The violation line flagged the recorded sales and said nothing about the recommendation,
which was the number the cap actually forbade.

**after** (same URL, status 200):

> `[REFUSED] The cap of [DECLARED] 0 bps in force on this page puts the resale ceiling at
> [EXACT] 1,000,000,000 lamports, below the price this record supports, so no primary price
> is stated: a recommendation above that ceiling is a price the cap forbids, and the ceiling
> is not a target for the primary price.`

and the refusal panel carries the same sentence under `recommendation_above_cap`.

How it is true by construction:

- `orchestrator.price_guidance` resolves the cap once, into `cap_in_force` (the URL's
  `capBps`, else the event's recorded `resalePriceCapBps`), and that one value is what the
  payload reports and what `primary_optimum.recommend(cap_bps_candidate=...)` receives. A
  test patches `primary_optimum.recommend` and asserts the argument, so a future caller
  cannot drop it silently.
- The ceiling is `face * (10000 + cap) // 10000`, integer lamports, the same expression
  `price_features` uses for the recorded ceiling. It is computed inside `core`, so the page
  prints `core`'s arithmetic and not the renderer's.
- The recommendation is refused, not clamped. Handing back the ceiling would print the cap
  dressed as a primary price, and A10 says the cap is a ceiling on the resale price and a
  floor on value, never a target for the primary price. The refusal names what would change
  it: "a cap at or above the price this record supports".
- The refusal is a state of the recommendation, so it travels to every surface that reads
  one: the decision block (`blocks._binding` and `blocks._banded` both branch before they
  print a number), the refusal panel, the payload, and `tools/guidance.py`, which prints the
  same payload over the same call. The console is the only route that carries a cap today:
  the pricing seam (`engine_model`) asks for no cap, so its answer is unchanged, and if it
  ever asks for one the refusal arrives with it because the code is a state of the
  recommendation and not a sentence the renderer writes.
- The ceiling is printed because a reader can check it by hand; the forbidden recommendation
  is not printed anywhere, in either block.

What stayed the same, proved by bytes rather than by argument: 19 fixture states were
rendered under the old code and the new one and diffed. **17 are byte-identical**
(`/`, `evt_syn_01`, `evt_syn_01 capBps=1000`, `evt_syn_01 capBps=2500`, `evt_syn_02`,
`evt_syn_02 capBps=1500`, `evt_syn_02` with a fee, `mode=before_on_sale`, the 2026-09-01
cut, `evt_syn_03` through `evt_syn_08`, `sim=1`, `tau=0.406`). The two that differ are the
two states where the cap forbids the price: `evt_syn_01&capBps=0` and `evt_syn_02&capBps=0`.
`?event=evt_syn_01&capBps=2500` still prints `1.03 SOL` and its ceiling is `1.25`, so the
number agrees with its own cap.

### 2. The loader holds back what the core cannot price, and the rest keeps serving (C8)

`LedgerAdapter._validate` admitted a zero-priced sale, a sale dated after the event starts,
and an event with no tiers. `price_features` then raised `FeatureError` on the first two,
and because `cross_section` builds every event for the pool, one bad row in one event turned
**every** console URL into a 422. The review's C1 fix made that a labelled page instead of a
closed connection, which is why the defect was visible and not fatal.

**The choice, stated.** These three are per-event rejections, not store-fatal errors. The
loader keeps the event out of `events()`, `tickets()` and `raw_ledger()`, records a typed
reason (`code`, registry sentence id, fields), and serves the rest of the store untouched.
The alternatives and why they lost:

- *Raise `StoreError`, refuse the whole store.* Simple, and wrong: one malformed row from
  real data would take a store of seven good events offline. The brief forbids it.
- *Leave it to the engine, as before.* That is C8: the loader becomes a gate that admits
  rows the core cannot price, and one bad row refuses every page.
- *Keep the event and render it with a null price.* A page that looks priced and is not.
- *Per-event rejection with the other events served.* Chosen. The offending event is
  refused by name at its own URL with a code, and every healthy event still prices.

The three typed reasons:

| code | when | the sentence on the page |
|---|---|---|
| `sale_not_priced` | a `sale` row with `priceLamports` 0 (a negative price was already store-fatal) | "Row {row} is a sale recorded without money, so this event cannot be priced: a zero resale price has no ratio to face value, and no number for this event is stated." |
| `sale_after_event_start` | a `sale` row strictly after the event's `startsAt`, the same boundary `price_features` refuses on | "Row {row} is a sale dated after this event starts, so this event cannot be priced: the time from that sale to the event is negative, and no number for this event is stated." |
| `event_has_no_tier` | an event with `tiers: []` | `P_NO_TIER`, the sentence and the code that URL already produced |

The codes are the ones `price_features.FeatureError` already used, so a reader who met the
refusal before meets the same word now; `price_features` keeps its own raise as the second
line of defence. `sale` rows with a *null* price are still skipped rather than rejected,
because that is what the core does with them (a gift is an unpriced sale in this schema's
own custody trail) and changing it would change a behaviour nobody named.

Details that make it hold:

- The check runs per event, before the structural checks for that event, so an event with no
  tiers is held back even when its `totalSupply` no longer agrees with the tiers it lost.
  Before this, that store raised `StoreError` and the server did not start at all.
- `_index_tiers` no longer raises a bare `KeyError` for a ticket whose tier does not exist,
  which is the state a tierless event with tickets leaves behind. The event is held back
  before anything reads that index.
- After the hold-back the tier and entry indexes are rebuilt from the survivors, so no
  number, pool or page can reach a rejected row.
- `tools/build_fixture_store.py --check` now fails (exit 1, one `[FAIL]` line naming the
  event and the code) if the shipped store carries one of the three. A store that fails to
  load for any other reason also reports `[FAIL]` and returns 1 instead of printing a
  traceback. On the committed store it is unchanged: exit 0.
- `tools/console-check-stores.py` now asks each malformed store for the held-back event's
  page **and** for a healthy event on the same server, and fails if either half is wrong.
  The old version asked only for `?event=evt_syn_04`, which was the wrong half of this.

### The six URLs, before and after

Served on 8788 by the shipped code after the restart, one store per run, killed and
restarted between runs (`/tmp/tp-bad-zero.json`, `/tmp/tp-bad-late.json`,
`/tmp/tp-bad-tierless.json` are the fixture with one mutation each).

| # | URL | before | after |
|---|---|---|---|
| 1 | `/?event=evt_syn_01&capBps=0` | 200, `Recommended primary price: 1.03 SOL per ticket` against a 1.00 SOL ceiling | 200, `[REFUSED] recommendation_above_cap` with `[DECLARED] 0 bps` and `[EXACT] 1,000,000,000 lamports`; no price |
| 2 | `/?event=evt_syn_01&capBps=2500` | 200, `1.03 SOL` | 200, `1.03 SOL`, unchanged, and `1.03 <= 1.25` |
| 3 | zero-priced sale, `/?event=evt_syn_01` | 422 `sale_not_priced`, from the core, after every event had been built | 422 at load, `Row led_0002 ...`, same code |
| 4 | sale after start, `/?event=evt_syn_04&asOf=2026-11-14T12:00:00Z` | 422 `sale_after_event_start`, same reason | 422 at load, `Row led_0066 ...`, same code |
| 5 | no tiers, `/?event=evt_syn_03` | 422 `event_has_no_tier`, `P_NO_TIER` | 422 `event_has_no_tier`, `P_NO_TIER` (the page is the same; the difference is that the loader now reports it and `--check` fails on the store) |
| 6 | same zero-priced store, healthy `/?event=evt_syn_04` | **422 `sale_not_priced`**: one bad event refused the whole store | **200**, `Recommended primary price: 0.93 SOL per ticket`, band 0.67 to 1.29 |

URL 6 is the half of C8 the review did not spell out and the half the brief asked for: with
the same three stores, `?event=evt_syn_02` on the tierless store still prints `at least 1.38
SOL per ticket`, and `?event=evt_syn_01` on the late-sale store still prices at that cut.

### Verified after the change

- `python3 -m unittest discover -s tests -t .` → **Ran 380 tests, OK** (366 before; 14 new
  in `tests/test_cap_and_loader_refusals.py`).
- `python3 tools/build_fixture_store.py --check` → exit 0, store unchanged
  (`15e6f6611652ae43`), adapter accepts it. Pointed at a store with one zero-priced sale it
  returns 1 and prints `[FAIL] evt_syn_01 cannot be priced: sale_not_priced`.
- `python3 tools/console-check.py` against 8788 → **FAILURES: 0** (83 checks).
- `python3 tools/console-check-stores.py` → **FAILURES: 0** (8 checks: 4 held-back events,
  4 healthy events on the same stores).
- Server restarted on 8788 (`python3 -m ticketpath.server`, job `jmw6gswtezg8l`, pid
  292206); `/health` is 200, `/` is 200 and still prints `at least 1.38 SOL` for the binding
  event. 8787 was not touched.

Each new test was shown to fail on the old behaviour, by reverting only the product files to
`HEAD` in a scratch copy of the tree (`/tmp/tp-old`, an `rsync` copy plus `git show
HEAD:<file>` for each of them) and running the new file there. Never in place:

| Test | On the old code |
|---|---|
| `test_a_cap_below_the_supported_price_is_refused_not_printed` | `TypeError: recommend() got an unexpected keyword argument 'cap_bps_candidate'` |
| `test_a_cap_that_permits_the_price_changes_nothing` | same `TypeError` |
| `test_without_a_cap_the_arithmetic_is_unchanged` | passes on both (control) |
| `test_the_orchestrator_passes_the_resolved_cap_into_the_recommendation` | `None != 0` |
| `test_no_recommendation_exceeds_its_own_pages_ceiling` | fails on `evt_syn_01 capBps=0` (and 43 more sub-cases) |
| `test_the_zero_cap_url_prints_a_typed_reason_and_no_price` | `1026573088 is not None` |
| `test_a_cap_that_permits_the_price_still_prints_the_price` | passes on both (control) |
| `test_a_binding_floor_above_the_cap_is_refused_too` | `None != 'recommendation_above_cap'` on `evt_syn_02` |
| the five loader tests | `AttributeError: 'LedgerAdapter' object has no attribute 'rejections'` |
| `test_the_fixture_check_fails_on_a_store_that_carries_one` | `0 != 1`: the old gate passed the bad store |
| `test_console_fixes.test_a_zero_priced_sale_refuses_with_a_typed_reason` | `422 != 200` on the healthy event |
| `test_console_fixes.test_a_malformed_store_still_answers_over_a_socket` | `422 != 200` on the healthy event |

### What I chose not to change, and why

- **Two existing tests in `tests/test_console_fixes.py` were rewritten, not deleted.** They
  pinned the old behaviour on purpose: they asked for `?event=evt_syn_04` on a store whose
  `evt_syn_01` carried a zero-priced sale and asserted 422, which is exactly the "one bad
  row refuses every page" rule the brief replaces. Each now asserts both halves (the
  offending event refuses with its code, a healthy event on the same server returns 200).
  This is the one place where an assertion changed rather than a number.
- **The band's upper end still uses the recorded ceiling, not the candidate one.** In
  `capped_no_mass_point` the band is trimmed to the ceiling recorded when the sales
  happened. Trimming it to a candidate cap would change a band number on pages the review
  did not name, and the band is a statement about the record, not about the policy.
- **`capViolations` still counts against the URL cap only.** A page whose cap comes from the
  store therefore reports no violations, because the store's own sales cannot violate the
  store's own cap. Changing that would restate the past under a policy.
- **The `capBps` form field still shows the event's recorded cap** while the canonical URL
  carries the URL's cap. That is a control-wording defect (the field reads as if the page is
  honouring the recorded cap when the URL says otherwise), it is not in section 5.2 or C8,
  and fixing it changes what a judge types into. Named here so it is not lost.
  **Closed 2026-11-07T14:10Z — see the cap-field section at the end of this file.**
- **`GET /api/events/<rejected id>` still answers 404 `not_found`.** The loader does not
  serve the event, so the contract's not-found answer is not a lie about the contract, but it
  is less informative than the console's typed 422. Changing an API status for a store state
  the contract does not describe is a decision for the operator, not a fix.
- **`list_events` now lists one event fewer on a store with a rejection** (8 became 7 in the
  zero-priced test). That follows from holding the event back; the alternative is a list
  entry with no price behind it.
- **`sale` rows with a null price are still accepted and skipped.** See above.
- **A store where every event is rejected answers with the first rejection's reason**, not
  `no_ledger`. `no_ledger` would be false there: a ledger exists and it is unpriceable.

## 2026-11-07T14:10Z — the cap field shows the cap in force, and the page says which cap that is

**Scope:** the `capBps` control, the one line of prose that states its rule, the cap line and
the cap-in-force line in the decision block, one regression test file, and this section. No
commit, no push, no change to `../ticketing-frontend`, no touch to 8787 or the fleet's trees,
no new dependency.

The defect the previous pass named at line 1043 above is closed. On
`/?event=evt_syn_02&capBps=0` the page used to show a control reading `1500`, a canonical URL
reading `capBps=0`, and a decision reading "The cap of 0 bps in force on this page puts the
resale ceiling at 1,200,000,000 lamports" — three different numbers for the cap on one page.
The control rendered `event.capBps` (the cap in force when each sale was recorded) while the
URL, the refusal headline and the recommendation all used `selection.capBpsCandidate` (the cap
this page prices against). The control now renders the same wrapper the URL and the decision
read from, so the page has one cap in force.

**The rule, stated on the page in one line (P_CAP_RULE):** "The cap field shows the resale cap
this page prices against and the canonical URL carries the same number: clear the field and
submit to fall back to this event's recorded cap of 1500 bps." The number in that line is the
event's own recorded cap, printed from the payload, not a literal.

**An uncapped event (P_CAP_RULE_UNCAPPED):** "This event records no cap, so a blank field means
no cap and this page prices against none: type a number to price against that cap, and the
canonical URL carries it." The field's own label also says `capBps (0–10000, this event records
no cap)`, so the empty box is explained where the box is.

**One addition to the decision block, because the agreement is only honest if both caps are
named:** when the URL names a cap that is not the event's recorded one, the block prints
`[DECLARED] This page prices against a cap of [DECLARED] N bps. The record was made under a cap
of [FIXTURE] M bps, so the recorded sales are described under that cap, not this one.`
(P_CAP_IN_FORCE, and P_CAP_IN_FORCE_UNCAPPED where the event records no cap.) Without it, the
`capBps=2500` page showed 2500 in the control and the URL while A19 and the ceiling line said
1500, which is correct arithmetic about the record but left the reader to reconcile two
unnamed caps. Both numbers already existed on the payload; no arithmetic changed. The cap line
above the block (`A cap does not hide the price…`) now follows the cap in force rather than the
recorded cap, so an uncapped event priced under a URL cap does not say "No cap applies" two
lines above a sentence naming the cap it is pricing against.

**Verified by hand over HTTP against the restarted server on 8788** (`python3 -m
ticketpath.server --port 8788`, fixture store, synthetic):

| URL | form shows | canonical URL carries | decision block says |
|---|---|---|---|
| `/?event=evt_syn_02` (no capBps) | `1500` | `capBps=1500` | cap is binding at `[FIXTURE] 15%` over face; ceiling `(10,000 + 1500) / 10,000`; form and URL carry the record's own cap |
| `/?event=evt_syn_02&capBps=0` | `0` | `capBps=0` | `[DECLARED] This page prices against a cap of [DECLARED] 0 bps`, record was made under `[FIXTURE] 1500 bps`, then `[REFUSED] The cap of [DECLARED] 0 bps in force on this page` |
| `/?event=evt_syn_02&capBps=2500` | `2500` | `capBps=2500` | `[DECLARED] This page prices against a cap of [DECLARED] 2500 bps`, record made under `[FIXTURE] 1500 bps`; A19 and the ceiling still describe 1500 |
| `/?event=evt_syn_04` (uncapped) | blank, label says the event records no cap | no `capBps` parameter | `No cap applies to this event, so nothing hides the top of the price distribution.` |

All three agree on every row: the control and the URL carry the same integer, and the block
names that integer wherever it is not the record's own.

**Regression test:** `tests/test_console_cap_field.py`, 11 tests, including one that fetches the
four URLs above from a real socket and reads the control out of the served HTML. Reverting the
fix in a scratch copy (`/tmp/tp-cap-scratch`: the control back to `event.capBps`, the decision
block's in-force line removed, the cap line back on the recorded cap) fails 15 assertions in
that file; on this tree all 11 pass. Full suite: **391 tests, OK** (was 380).

**What I chose not to change:** the recorded ceiling, the A19 sentence and the band arithmetic
still describe the sales under the cap they were made under (`capBps=2500` does not restate the
past at 2500). The canonical URL still writes `capBps` explicitly when it equals the recorded
cap, because it already did and because the field now shows that number too; dropping it would
make the URL and the field disagree in the other direction.


---

## 2026-11-07T14:49Z — the four defects `10-final-review.md` failed honesty on: N1, N2, N3, N4

**Scope:** three renderer branches and one label each (N1), the band's upper end in
`core/value_band.py` plus the sentence that says where it stops (N2), the exposure denominator in
`core/price_features.py` (N3), the before-on-sale counts on the payload and in the strip and
refusal (N4). One new test file, `tests/test_final_review_fixes.py`; one assertion inverted and
four cases added in `tools/console-check.py`; two harness edits in existing tests (a sample field
for the new sentence, and the band-top assertion the review's N2 overturns); and this section. No
commit, no push, no change to `../ticketing-frontend`, no touch to 8787, no read or write of the
fleet's trees, no new dependency.

The tree before this pass is exactly the tree the review pinned: `git archive HEAD` gives
`ticketpath/console/page.py` = `893cccb39144d19e…` and `ticketpath/console/blocks.py` =
`1e6a6e99d13d5b59…`, the two hashes in the review's table. Every "before" number and sentence
below was measured from that archive at `/tmp/old-tree` and run against the same fixture on the
same clock, not from memory and not from the review's text.

**Test count: 391 before, 408 after, all OK.** Conformance 22 OK. `tools/console-check.py`
FAILURES: 0 (22 URL cases, 71 label checks). `tools/console-check-stores.py` FAILURES: 0. A live
sweep of 72 served pages (8 events x 8 cap states, plus the before-on-sale page of every event) is
clean on all three internal-consistency properties in the brief.

### 1. N1 — the cap branches read the recorded cap instead of the cap in force

Three branches asked "does this page have a cap?" and read `event.capBps`, which is the cap each
recorded sale was made under, while the page priced against `selection.capBpsCandidate`, which is
the cap in force. All three now read the cap in force, and where the two differ they say which one
they are describing. `blocks.py:46` (the cap line) was already right and was not touched.

**URL: `/?event=evt_syn_04&capBps=1700`** — an uncapped event with a typed cap, the state the
console itself tells the reader to build. Cap in force 1700 bps, ceiling `800,000,000 x 1.17 =
936,000,000`, and 7 of the tier's 12 recorded sales above it.

| | before | after |
|---|---|---|
| strip (`page.py`) | `[FIXTURE] 12 resales on this event · [FIXTURE] 11 tickets ·` **`no resale cap, so no ceiling`** | `… · no resale cap is recorded on this event, so its sales have no ceiling to be counted against; this page prices against a cap of [DECLARED] 1700 bps` |
| `A2` (`blocks.py:287`) | `…` **`This event has no resale cap, so no ceiling enters the bound.`** | `… the cap this page prices against gives a ceiling … This event records no cap of its own, so that ceiling is the page's and not the record's.` |
| market (`blocks.py:388`) | `… mean markup [FIXTURE] 19.8% ·` **`This event has no resale cap, so there is no ceiling to count against.`** | `… This event records no resale cap, so its sales have no ceiling to be counted against. This page prices against a cap of [DECLARED] 1700 bps, and the sales above that cap are counted in the decision.` |

**And where both caps exist and differ, the count says which ceiling it counts.** On
`/?event=evt_syn_01&capBps=298` (recorded 2500, in force 298) the strip and the market block now
print `0 at the recorded ceiling` instead of `0 at the ceiling`, so the at-ceiling count cannot be
read as a count against the 298 bps the page prices against.

**Revert, demonstrated:** with the three branches put back on `event.capBps`, the new class
`TestTheCapInForceReachesEverySentenceAboutTheCap` fails 22 assertions, including
`'no resale cap, so no ceiling' at cap 1700` on `evt_syn_04`, `evt_syn_05` and `evt_syn_08` across
the six typed caps in the sweep. On this tree all three tests pass.

### 2. N2 — the recommendation's band ran above the cap it refuses to cross

Chosen fix: **the band is truncated at the cap in force.** The other option in the brief (print
the record's band and call the recommendation the crossed-out part) would have left the
recommendation object carrying an upper end its own cap rule forbids. The truncation is in
`value_band.estimate`, next to the recorded-ceiling truncation that was already there, so the band
and the recommendation cannot disagree by construction: two ceilings exist and the lower one
binds. The page states it in one sentence, `[EXACT] The top of that band is the ceiling the cap in
force puts on this tier, at N SOL, so the range stops where the cap does.`, printed wherever the
band's top is a ceiling rather than a width.

**URL: `/?event=evt_syn_01&capBps=298`** — page ceiling `1,000,000,000 x 1.0298 = 1,029,800,000`.

| | before | after |
|---|---|---|
| band | `Band 0.74 – 1.25 SOL.` (upper end 220,200,000 above the ceiling) | `Band 0.74 – 1.0298 SOL.` |
| says where it stops | nothing | `[EXACT] … at 1.0298 SOL, so the range stops where the cap does.` |
| `bandHiLamports` in the payload | `1,250,000,000` | `1,029,800,000`, with `boundCeilingLamports` and `topIsCeiling` true |

On **`/?event=evt_syn_04&capBps=1632`** the same: `Band 0.67 – 1.29 SOL` before, `Band 0.67 –
0.93056 SOL` after, against a page ceiling of `800,000,000 x 1.1632 = 930,560,000`.

The band's top is now printed at its exact value when it is a ceiling, because two decimals put
`0.94` above the `0.936` stated in the next sentence. That is the only precision change in this
pass, and it is why `Band 0.74 – 1.25 SOL` still reads `1.25` (exact) while `4.50` now reads `4.5`
and `0.62` now reads `0.625` on the two pages whose top is a ceiling that does not round to its own
two decimals.

**Revert, demonstrated:** with the candidate ceiling dropped from the trim, the new class
`TestTheBandStopsAtTheCeilingThePageEnforces` fails 32 assertions:
`1250000000 not less than or equal to 1029800000` on `evt_syn_01&capBps=298`,
`1293045022 != 930560000` on `evt_syn_04&capBps=1632`, and 30 cells of the
eight events by eight caps by every tier sweep. On this tree all three tests pass.

### 3. N3 — the ticket-day denominator ran past the event end

`_exposure_ticket_days` took `min(cut, redeem)`. It now takes `min(cut, event endsAt, redeem)`, so
a ticket stops accruing exposure when the event it admits to is over, and an event with no
recorded end is still stopped by the cut alone. Every number below is the selected tier of the
event named, on the fixture's own record; the record does not change with the cut.

**Before and after on `evt_syn_02` (General tier, 9 sales throughout):**

| cut | exposure before | rate /1,000 before | exposure after | rate /1,000 after |
|---|---|---|---|---|
| `2026-11-07T12:00Z` (default, before the end) | 435.1 | 20.7 | 435.1 | 20.7 |
| `2026-11-22T03:00Z` (1 h after the end 02:00) | 552.1 | 16.3 | 551.8 | 16.3 |
| `2026-12-31T00:00Z` | 863.1 | 10.4 | 551.8 | 16.3 |
| `2027-06-01T00:00Z` | 2079.1 | 4.3 | 551.8 | 16.3 |

**Before and after on the cold-start event `evt_syn_03`** (Standing tier, 0 sales, so the printed
rate is the `[DECLARED]` gamma-Poisson posterior mean, not a measured rate):

| cut | exposure before | rate /1,000 before | exposure after | rate /1,000 after |
|---|---|---|---|---|
| `2026-11-07T12:00Z` (default, before the end) | 131.4 | 7.6 | 131.4 | 7.6 |
| `2026-12-12T04:00Z` (the event end) | 339.4 | 2.9 | 339.4 | 2.9 |
| `2027-06-01T00:00Z` | 1364.4 | 0.7 | 339.4 | 2.9 |

Every post-end cut now prints one value, and the value is the one the record supports: 551.8
ticket-days and 16.3 per 1,000 for the nine sales on `evt_syn_02`, which is the figure the review
computed by hand (its 551.8 at a 14:12Z cut, 16.3). `evt_syn_06` at the default clock is unchanged
(460.5 / 15.2): it is past its end, but every one of its tickets carries a `redeem` row before the
end, so the redeem stop already bound and the end adds nothing.

**Revert, demonstrated:** with the end dropped from the stops, the new class
`TestTheDenominatorStopsAtTheEventEnd` fails 5 assertions, including
`[('551.8', '16.3'), ('552.1', '16.3'), ('863.1', '10.4'), ('2079.1', '4.3')]` for the four cuts,
`301.0 != 5.0` on the ten-day-after unit case, and the cold-start page's
`exposure [FIXTURE] 339.4 ticket-days at risk` going absent. Two tests in that class still pass on
the old code on purpose: an event with no recorded end, and a cut before the end, are the states
where the fix must change nothing, and they are the premise that it bites only past the end.

**Numbers changed, and only these:** exposure and the rates derived from it, on every cut after an
event's end (the two tables above); and the band tops in item 2. Nothing else moved: a
state-by-state diff of the rendered page from `/tmp/old-tree` to this tree over 26 states (`/`,
all eight events, the non-default tiers of `evt_syn_07`, five cap states, two cuts, the fee and
negative-net states, `sim=1`, `tau=0.10`, both before-on-sale pages, two post-end cuts) shows the
default page, `evt_syn_02`, `evt_syn_03`, `evt_syn_04`, `evt_syn_05`, `evt_syn_07`, `evt_syn_08`,
the fee states, `sim=1` and `tau=0.10` byte-identical.

### 4. N4 — the before-on-sale page printed the excluded record as an absent one

The mode withholds this event's rows from the features; it does not unrecord them. The store is
now counted at the same cut, outside the pricing path (`Orchestrator._excluded_own_counts`), and the
zeroes are printed as what enters the decision beside the count of what the mode excluded.

**URL: `/?event=evt_syn_02&mode=before_on_sale`** — the store holds 12 priced sale rows and 12
ticket rows on this event at the cut.

| | before | after |
|---|---|---|
| strip | `[FIXTURE] 0 resales on this event · [FIXTURE] 0 tickets · [FIXTURE] 0 at the ceiling` | `[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event are excluded by the mode · [FIXTURE] 0 tickets enter it; [FIXTURE] 12 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| ticket basis (payload) | `tickets with an issue row at or before the cut; 0 ticket rows exist in the store` | `… 12 ticket rows exist in the store and the decision mode excludes them` |
| no-denominator refusal | `[REFUSED] No ticket had been issued at this instant, so there is no denominator.` | `[REFUSED] [FIXTURE] 12 tickets are recorded on this event at this instant, and the BEFORE-ON-SALE decision mode excludes every one of them, so no ticket-day of exposure enters this denominator and the rate has none.` |

The zero-denominator sentence follows the count it prints: one recorded ticket reads `1 ticket is
recorded … excludes it`, and the counterfactual mode's own zero-ticket cut
(`/?event=evt_syn_02&asOf=2026-09-01T00:00:00Z`, 0 issue rows) keeps `No ticket had been issued at
this instant`, which is true there.

**One defect this fix introduced, caught by the live sweep and fixed before it was reported.** The
first cut of the refusal used the excluded count unconditionally in the mode, so
`/?event=evt_syn_08&mode=before_on_sale` — an event with no rows at all — read `0 tickets are
recorded on this event at this instant, and the BEFORE-ON-SALE decision mode excludes every one of
them`. That is a sentence about rows that do not exist, the same class of error as the one being
fixed. The refusal now falls through to the plain sentence when the excluded count is zero, and
`test_an_event_with_no_rows_keeps_the_sentence_that_is_true_there` holds it: 408 tests, not 407.

**`tools/console-check.py:140` was inverted.** It asserted
`"[FIXTURE] 0 resales on this event" in b and "[FIXTURE] 0 tickets" in b` — it pinned the false
counts as correct. It now requires those sentences to be absent, requires both excluded counts to
be printed, and requires the refusal to name the 12 excluded tickets.

**Revert, demonstrated:** with `excluded` passed as `None` again (the whole of the old behaviour),
`TestTheBeforeOnSaleStripSaysTheRowsAreExcluded` reports 6 failures and 1 error out of its five
tests, and the inverted check in `tools/console-check.py` fails with `the page says '[FIXTURE] 0
resales on this event' while the store holds 12`. On this tree all five tests and the tool pass.

### The five URLs, checked by hand over HTTP against the restarted server on 8788

`python3 -m ticketpath.server --port 8788` (fixture store, synthetic). The previous instance on
8788 was stopped and this one started; 8787 was not bound and not contacted.

| URL | status | what the page now says |
|---|---|---|
| `/?event=evt_syn_04&capBps=1700` | 200 | cap in force 1700 named in the strip, `A2` and the market; band `0.67 – 0.936`; "the range stops where the cap does"; 7 of 12 above it |
| `/?event=evt_syn_04` | 200 | unchanged: `no resale cap, so no ceiling`, band `0.67 – 1.29`, no ceiling sentence |
| `/?event=evt_syn_02&mode=before_on_sale` | 200 | `0 resales enter this decision; 12 recorded on this event are excluded by the mode`, and the refusal names the 12 tickets and the mode |
| `/?event=evt_syn_03` | 200 | cold start unchanged at this cut: `0 resales`, `10 tickets`, `[DECLARED] 7.5` (the server clock is 14:46Z, so the posterior mean is 7.5 there and 7.6 at the tests' 12:00Z), prior band `0.65 – 1.26`, no price |
| `/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z` | 200 | priced seven months after its end: `exposure [FIXTURE] 551.8 ticket-days at risk`, `16.3 per 1,000`, the same as at the end and the same as on `2026-12-31` |

`/?event=evt_syn_06` (a completed event, so also priced after its end at the default clock) is 200
and unchanged, for the reason in item 3.

### What I chose not to change, and why

1. **The market block's tier counts in the before-on-sale mode** still read `in this tier
   [FIXTURE] 0 sales of [FIXTURE] 0 on this event`. The review's N4 named the strip, the basis and
   the refusal, not this sentence; fixing it needs a tier-scoped excluded count that the brief did
   not sanction, and the strip two blocks above now states the excluded count for the event. It is
   the next thing that should be fixed if this mode is judged again.
2. **`A20`** ("This tier has a resale cap and no sale has reached it") is still gated on the
   recorded cap. It is a sentence about the recorded cap in a tier whose recorded cap nothing
   reached, it is not one of the three branches the brief names, and on `evt_syn_01&capBps=298` it
   sits beside the in-force line that names both caps.
3. **The cold page's prior band** (`prior band around face: 0.65 – 1.26 SOL`) is not truncated at a
   typed cap. It is the declared prior around face, it is labelled as the prior, and the page
   states no price on that state, so no recommendation crosses a ceiling there. The review's N2 is
   about the recommendation object, and a cold event has none.
4. **`status on_sale` beside a post-end decision instant** (N8) and **`TRACE` returning Python's
   501** (N9) are still there: both are review findings, neither is one of the four, and the brief
   says change nothing else.
5. **`7 events in the store` on a held-back store** (N6) is untouched for the same reason.

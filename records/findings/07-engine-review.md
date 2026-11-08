# 07 — Independent review of the Ticketpath engine and console

**Status:** review complete. Read-only over the tree; this file is the only one I wrote. No fix applied by me, no commit, no push.
**UTC:** 2026-11-07T12:20Z. **Agent:** independent reviewer. I did not build, design or operate any part of it before this pass.
**The tree moved twice during the pass.** At 12:00Z the suite ran 293 tests; at 12:15Z it ran 306; at 12:26Z it ran 309. `ticketpath/server.py`, `ticketpath/orchestrator.py`, `ticketpath/console/blocks.py`, `ticketpath/console/page.py` and `ticketpath/core/labels.py` changed between 12:08 and 12:11, and `blocks.py` changed again at 12:17 while this file was being written. The two renderer defects I found at 12:16 (the cap-violation dict, C2, and the `{n}` path refusal, C3) were fixed in the working tree at 12:17. The body records them as findings against the 12:16 state and marks them fixed where they are current. Every other finding below was re-checked against the 12:25Z state and is quoted from it. The reviewed state is pinned by these hashes, so a later reader can tell whether it still applies:

| File | sha256 (first 16) |
|---|---|
| `ticketpath/server.py` | `98cbdab058f0771d` |
| `ticketpath/orchestrator.py` | `b986d78525aa7d26` |
| `ticketpath/console/blocks.py` | `6e5b820f4cd77576` (12:16) / `c6cb0e61b20b5e2d` (12:25) |
| `ticketpath/console/page.py` | `27d1d60876d92b88` (12:25) |
| `ticketpath/core/labels.py` | `5e148132965c4783` |
| `ticketpath/core/value_band.py` | `45c099734de823f1` |
| `ticketpath/core/price_features.py` | `beecaca8dc8f3c0a` |
| `ticketpath/api/guidance.py` | `c8e5d2860409e72e` |
| `fixtures/synthetic_store.json` | `15e6f6611652ae43f3967e110e2feeffde0cc2ace13ea868ff3abb0012bb9bfa` |

**What I did not review.**
- The Next.js frontend at `../ticketing-frontend` (out of bounds for this pass). I did not apply or assess `docs/frontend-honesty.patch`.
- The Solana program. None exists; there is nothing compiled, deployed or run. I read the design and the simulated state machine, not a cluster.
- The literature claims in the findings. I read 02-a §8, 02-b §1–3, 02-c §2 and §6, 02-d §2, 02-e §4–5, 03-b §2 and §6, and the ban in 00-adversarial-review §6, and checked the code against them. I did not verify their citations or the borrowed numbers.
- The six records A–F row by row; the fixture generator's intent (I verified its output invariants with `--check`); the wallet-verification cryptography beyond what the conformance suite exercises; the operator's fleet tool repositories (out of bounds).
- Anything about the operator's accounts, a real ledger, or a devnet artefact. The store is synthetic and the chain slot is absent.

---

## 0. The four verdicts, up front

| Area | Verdict | The statement that stands |
|---|---|---|
| **Mathematics** | **STANDS-WITH-NARROWING** | The arithmetic that is implemented is right: the three regimes, the cap floor, the two-sided band, integer markup, the gamma–Poisson zero, the 2×2 path solve. The narrowing is that the headline is not the finding's boundary (02-d §2.4 case ii) and it is computed from the same event's resales, which 03-b §2.1's D1 forbids. It is a resale-value level or cap floor presented as a primary price. |
| **Honesty** | **FAILS** | The badge machinery and the ban on the sale-probability sentence stand. Four registry sentences state things the engine does not compute (A1, A2, A13, A17); a zero-sale rate is a prior badged as a fixture with a basis that contradicts its value; the fee refusal is false when a fee is supplied. On the default page the evidence strip and A1 give two different sales counts for the same event. |
| **Code** | **FAILS** | Three store-valid inputs produce an empty reply with no HTTP status, because the console is outside the handler's try. The two renderer defects found at 12:16 (a Python dict and a literal `{n}`) were fixed at 12:17, after this review's first pass; the blank-page class, the [EXACT] arithmetic, the loader/core gap and the fee float remain. |
| **Refusals** | **STANDS-WITH-NARROWING** | The engine refuses the sale probability, the interior optimum, the uncapped bound, the prior-only price and the zero-exposure denominator, visibly and in words. The path refusal promises a flat line that is not rendered (its `{n}` placeholder was fixed at 12:17); the no-fee refusal is false when a fee is supplied. |

The rest of this file is the evidence for those lines, then the fix list ranked by risk.

---

## 1. Run results

### 1.1 Start and health

`8788` was already bound by another process (`python3`) when the pass began. `8787` was left alone, as instructed. I ran my own instances on scratch ports: `--port 8891` (12:00Z, code before the 12:08 changes) and `--port 8896`/`8897` (12:13Z and later, current code). The cold-start and pathological stores were served on `8908`, `8911`–`8913`, `8974`, `8981`, `8986`, `8991`, `8994`, `8995`; all of those were mine and are stopped.

`GET /health` on the current code:

```
service ticketpath, version 0.1.0, status ok
dataSource.mode synthetic-fixture, synthetic true
chain.programDeployed false, programId null, rpcEnabled false, reason rpc_disabled
pricingModel.modelVersion engine-2026-11-07
contract.endpointsInContract 9, implemented 9, routesImplemented 10
```

The fixture check:

```
python3 tools/build_fixture_store.py --check   -> exit 0
  8 events, 76 tickets, 147 ledger rows
  "fixtures/synthetic_store.json matches a fresh build exactly"
sha256 15e6f6611652ae43f3967e110e2feeffde0cc2ace13ea868ff3abb0012bb9bfa
```

### 1.2 Tests and conformance

| When | Command | Result |
|---|---|---|
| 12:00Z | `python3 -m unittest discover -s tests` | **Ran 293 tests in 9.408s, OK** |
| 12:15Z | same | **Ran 306 tests in 9.540s, OK** |
| 12:26Z | same | **Ran 309 tests in 9.571s, OK** |
| 12:15Z | `python3 -m unittest tests.test_contract_conformance` | **Ran 22 tests in 0.693s, OK** |

The count moved because the tree moved, not because a suite was skipped. The 306-test run is the one that matches the 12:16 pinned hashes; the 309-test run is the current one at 12:26. I am recording all three numbers rather than the flattering one.

### 1.3 The fourteen-step acceptance test, run in order

The spec's §1.1 says the acceptance test is the fourteen steps, performed in order, by someone who did not build the page. That is what this pass did. The result is not a clean pass.

| Step | Result | What actually happened |
|---|---|---|
| 1. Open `/` | **pass** | Title `Ticketpath — organizer pricing console`; banner is the first element; T1 present; fixture sha present. |
| 2. Event selector | **pass** | All 8 events listed with regimes; default is `evt_syn_02` / `tier_stg_general`, the highest at-ceiling share. |
| 3. Evidence strip | **pass** | `[FIXTURE] 12 resales on this event · 12 tickets · 9 at the ceiling`; `[FIXTURE] 8 events on this platform, 5 with any resale`; `[DEVNET] 0 on-chain transactions`. The ticket count is not cut-aware (see H8), but at the default cut it is right. |
| 4. Binding decision block | **pass on the default; fail on the other binding event** | Default: `at least 1.38 SOL`, A19, floor line, `Range: 1.38 SOL and up`, T2. On `evt_syn_07` the [EXACT] line reads `ceiling 1.12 SOL = face 0.90 SOL plus a cap of 25%`; 0.90 × 1.25 = 1.125, not 1.12 (M9). |
| 5. Uncapped event | **pass on structure; two false clauses** | `0.93 SOL`, band `0.67 – 1.29`, `basis: tier_marks`, T3, A4. A2 says "the resale cap gives a ceiling" on an event with no cap, and A16 describes a cap hit when the at-ceiling count is 0 (H4). |
| 6. Market block | **pass** | Median/mean markup, sales, at-ceiling, repeat sale, A1, T4, exposure. The A1 number is the tier's, not the event's (H1). |
| 7. Refused block | **pass at 12:25; one defect remains** | Never empty; `not_identified`, `no_demand_response`, `no_fee_model`, the path reason, `no_upper_bound`, `insufficient_events`. At 12:16 the path reason printed `{n}` (C3, fixed at 12:17). `no_fee_model` is still false after the fee control is used (H5). |
| 8. Change `asOf` | **partial** | Counts and regime change; the decision becomes the refusal. But at `asOf=2026-09-01T00:00:00Z` the strip still says `[FIXTURE] 12 tickets` although the first issue is 2026-09-11T11:00Z, under the sentence "Nothing after 2026-09-01T00:00:00Z enters any number" (H8). |
| 9. Change `capBps` | **fail at 12:16; pass at 12:25** | At 12:16 `/?event=evt_syn_02&capBps=0` printed `9 of {'value': 9, 'badge': 'FIXTURE', ...} recorded sales` (C2). The current code prints `9 of 9 recorded sales`. |
| 10. Change `tau` | **pass** | Uncapped: 0.67–1.29 at 0.20, 0.48–1.81 at 0.406, point 0.93 unmoved. Binding: `τ 0.2 · [REFUSED] There is no upper tail in this record for τ to widen`. |
| 11. No resales | **fail** | At 12:16 the path refusal printed `{n}` (C3, fixed at 12:17). The cold block still says "5 events have completed" while the refusal panel says "One event has completed" (H3), and A13 still calls the literature prior "the spread across 5 other events" (H2). |
| 12. On-chain panel | **pass** | `[DESIGN]` invariant, instruction table, error codes, `No program is deployed on any cluster`. |
| 13. `Show the refusal` | **pass** | Five `[SIMULATED]` lines: cap ok at 1.38, cap+1 refused 6010, unstaged refused 6009, unverified refused 6012, verified admitted. |
| 14. Chain slot | **pass** | `[DEVNET] No devnet transaction has been recorded`, no signature, no Explorer link, no fake slot. |

So: at 12:16 there were ten clean passes, step 4 passed on the default but failed its exact-arithmetic claim on the other binding event, step 8 was partial, and steps 9 and 11 failed. At 12:25 step 9 passes (the dict was fixed), step 11 still fails on the A17 contradiction and A13's source sentence, and step 7 still has the fee-refusal defect. The remaining failures are on the scripted judge path.

### 1.4 Every control and state

All 8 events render 200. The tier selector on `evt_syn_01`, `evt_syn_02` and `evt_syn_07` renders every tier. The documented URLs in `docs/RUN.md` all render 200 except the three crash inputs in §1.5. The input matrix:

| Control | Input | Result |
|---|---|---|
| `event` | unknown id | 404 page, banner present, "back to the decision" |
| `tier` | unknown id | 404 page |
| `asOf` | `not-a-date` | 400, code `as_of_invalid` |
| `asOf` | `2026-11-07` | 200, read as UTC midnight |
| `asOf` | `2026-11-07T12:00:00+05:00` | 200, normalised to `07:00:00.000Z`; the canonical URL carries `07:00Z` |
| `asOf` | `2099-01-01T00:00:00Z`, `1999-01-01T00:00:00Z` | 200; no future/past guard, but the cut is applied |
| `capBps` | `abc`, `-100`, `20000` | 400 |
| `capBps` | blank | 200, candidate = recorded cap |
| `capBps` | `0` | 200, violation line (the dict bug at 12:16, fixed at 12:17) |
| `feeLamports` | `abc`, `-5` | 400 |
| `feeLamports` | `999999999999999999999` | 200; the JSON net revenue is hugely negative, not rendered on the page |
| `tau` | `abc`, `0`, `-1`, `0.5`, `9` | 400 |
| `tau` | `0.10`, `0.20`, `0.30`, `0.406` | 200; band widens monotonically, point fixed |
| `sim=1` | | 200, five simulated lines |
| `HEAD /` | | **501 Unsupported method ('HEAD')**, default Python error page, no banner |
| `POST /` | | 404, not 405 |
| `GET /favicon.ico` | | 204 |

### 1.5 The crash inputs

Three stores, each accepted by `LedgerAdapter.from_fixture` (the loader's own validation), each taking the console page for one event out with **no HTTP response at all**. `curl` reports `HTTP 000` and `Empty reply from server`; the process stays up, `/health` answers, and other events on the same server answer.

1. **A sale at price 0.** Take `fixtures/synthetic_store.json`, set one `sale` row on `evt_syn_04` to `priceLamports: 0`. The loader accepts (`price < 0` is rejected; `price >= 0` is allowed). `GET /?event=evt_syn_04` -> `ValueError: math domain error` at `value_band.py:80` (`math.log(0 / face)`).
2. **A sale after the event starts.** Set `evt_syn_04.startsAt` to `2026-08-01T00:00:00Z`, before its sales. The loader accepts (it does not check sale time against `startsAt`). `GET /?event=evt_syn_04` -> `ValueError: ledger row ... is a sale after the event started` at `price_features.py:87`.
3. **An event with no tiers.** Append a draft event with `tiers: []`, `totalSupply: 0`, `issuedCount: 0`. The loader accepts. `GET /?event=evt_notier` -> `IndexError: list index out of range` at `orchestrator.py:316` (`event["tiers"][0]["id"]`).

The root is C1: the console call is outside the handler's `try`, and `console_index` catches only `ApiError`.

### 1.6 The empty store

`TICKETPATH_LEDGER_MODE=empty`:
- `GET /` is 400 with the banner and `[REFUSED] 400 no_ledger: no ledger exists, so there is nothing to price`.
- `GET /api/events` is 200 with `{"items": [], "nextCursor": null, "dataSource": {"mode": "empty-store", "synthetic": false, ...}}`.

That is a defensible refusal: visible, in words, and it does not invent data.

---

## 2. Mathematics

The check is implementation against the finding that specifies the quantity, the finding against itself, and the console's description against both. I quote the code line and the finding line where they disagree.

### 2.1 The regimes and the cap floor: correct

`value_band.classify` uses the pair (cap, at-ceiling count), not `cap != null`:

```
if not marks: regime = "no_resale"
elif cap is not None and at_ceiling > 0: regime = "capped_and_binding"
elif cap is not None: regime = "capped_no_mass_point"
else: regime = "uncapped"
```

That is 02-b §3.1 verbatim. The binding floor is `row["highestRecordedLamports"]`, the band is `{lo: floor, hi: None, noUpperBound: True}`, the level is `available: False`, and the sensitivity is `applicable: False`. 02-b §3.2 says report the value as a floor, no mean, no upper quantile; the code does. 02-b B1 says the pointwise lower bound for a sale at the ceiling is `p(1+c)`, and the aggregate over observed sales is the highest observed price; the code does. On `evt_syn_02` General: 8 of 9 at 1.38, floor 1.38, no upper. **STANDS.**

### 2.2 The band: correct

For `uncapped` and `capped, no mass point`, `value_band.estimate` computes

```
mean = _log_summary(marks)                      # mean(log(price/face))
half = z * max(tau, TAU_MIN)
lo = round(face * exp(mean - half))
hi = round(face * exp(mean + half))
```

and clamps `hi = min(hi, recordedCeiling)` on the capped-no-mass regime. The width is exactly `2 z τ` in logs, monotone in τ. That is BUILD-SPEC §3.4 and §4.7(b). `statistics` is not imported; the sample SD is never the width. The cap candidate never truncates the band; `_violations` counts recorded prices above the candidate and leaves the band alone. **STANDS.**

### 2.3 Partial pooling is computed and not applied

The finding's update rule, 02-e §4.3:

> `B_j = τ² / (τ² + s_j²)`, `θ̂_j = B_j y_j + (1 − B_j) ȳ(τ)`, `ȳ(τ) = Σ y_j/(s_j²+τ²) / Σ 1/(s_j²+τ²)`.

The code has both pieces:

- `value_band.pooled` computes `mu` exactly as `ȳ(τ)`. I checked it by hand: `mu = 0.094961807` both ways on the fixture's five events.
- `value_band.shrink_weight(tau2, s2)` (`value_band.py:158`) returns `τ²/(τ²+s²)`, which is `B_j`.

But `value_band.estimate` never calls either. The level is:

```
mean, within, n = _log_summary(marks)          # value_band.py:308
...
"level": {"lamports": int(round(face * math.exp(mean))), ...}
```

The only use of `pool` in `estimate` is `pooledWidthLog` at line 367, which is returned beside the band and does not move it. `primary_optimum.recommend` then uses `band["level"]["lamports"]` (`primary_optimum.py:114`). So the pooled mean and the shrinkage weight are dead code with respect to every number a user sees.

This follows BUILD-SPEC §3.4, which says the level is the raw mean. The spec does not implement 02-e §4.3. On this fixture the omission is small because `τ² = 0.04` dominates the within variance: `B_j` is 0.968 (Floor), 0.989 (Balcony), 0.982 (Box), 0.879 (`evt_syn_04`). The Floor level would move from 1.027 to 1.029 SOL, about 0.2%. So this is a narrowing of the estimator, not a visible arithmetic error on this data. It becomes visible on the cold band, where the pooled mean is not used at all (H2).

One further point on `pooled` itself: `usable` (`value_band.py:106`) includes the capped-and-binding events. 02-b §3.3 says "do not silently pool" a truncated and an untruncated distribution. On this fixture the all-events `mu` is 0.095 and the non-binding `mu` is 0.0845, so the mixture is not downward-biased here, but the principle is violated. Because `mu` is not used, the visible effect is nil; the `pooled.muLogRatio` leaf in the JSON is the only place it surfaces.

**STANDS-WITH-NARROWING:** the pooled mean and the shrinkage weight are correct and unused; the level is the raw tier mean, as the build spec says, and the finding's update rule is not the estimator.

### 2.4 Declared versus estimated τ below five events: correct, and the deviation is documented

The brief says "declared rather than estimated below five events". The code uses nine:

```
TAU_MIN = 0.10
EVENTS_FOR_ESTIMATED_TAU = 9   # 03-b section 6.4
```

03-b §6.4's floor for the between-event variance is "about 9 events" (the 95% interval on τ is narrower than τ itself at G ≥ 9). The code's DerSimonian–Laird branch is the finding's formula: `Q`, the denominator, `max(0, ...)`, and a floor at `TAU_MIN²` with `method = "declared_floor"`. The deviation from the brief is recorded in `BUILD-REPORT-CONSOLE.md` §4, with the reason: estimating at five would print a fitted τ beside A17 saying nothing is fitted. That is a defensible narrowing and it is in the record. **STANDS.**

### 2.5 The path index: per-tier, not per-event, and the identification claim is not the estimator

The finding, 02-a §8.3:

> "Per event e with n_e ≥ 4 sales: ... demean within the event ... Solve the 2×2 system ... Pool with inverse-variance weights ... Guards: require n_e ≥ 4, Δ > 0, and at least 5 days of spread in d within the event; discard events that fail and report how many were discarded."

The code takes a `tier_id`, fits one tier:

```
row = _tier(features, tier_id)
marks = row["marks"]
n = len(marks)
spread = row["timeSpreadDays"]
```

and never pools across events. There is no discarded-event count. A tier with 3 marks refuses `insufficient_marks` even when its event has 12. That is a narrower estimator than the finding's, and the console's path block is tier-scoped, so the difference is visible in which guards fire.

The `IDENTIFICATION` string (`path_model.py:44`) says:

> "Identified from within-ticket first differences where a ticket resold and from within-tier demeaning elsewhere."

The estimator has no first difference. Every mark enters as a level; a ticket sold twice contributes two rows to the same within-tier demean. The within-ticket transform of 02-a §4.1 (Bailey–Muth–Nourse, ticket fixed effect differences out) is not what the code computes. Demeaning within a tier removes the tier constant, not the ticket's own quality. The string is a claim about the estimator that the estimator does not support; it would be printed on the page only in the `path_answered` branch, which never fires on this fixture.

And it never fires at all on this fixture. Every sale is 52 to 70 days before its event; the horizons are `(28, 14, 7, 2, 0)`; `outside_support` refuses every horizon. I ran every event and tier at 2026-11-07T12:00Z: all 15 tier fits refuse, 6 with `outside_support`, 2 with `cap_mass_dominates` and 7 with `insufficient_marks`; none is available. So the 2×2 solve, the bracket and the anchor are exercised by the hand-built tests only, never end to end. The spec §3.5 says the page prints the refusal and the flat martingale; the page prints the refusal only, and the `insufficient_marks` sentence promises "the flat line below" with nothing below it.

**STANDS-WITH-NARROWING:** the 2×2 algebra is correct; the unit is the tier, not the event; the first-difference claim is not implemented; and the path is unobservable on the shipped fixture.

### 2.6 The composite intensity: the denominator is right, the cold-start multiplier is missing

The denominator is correct per 02-c §1.2 and BUILD-SPEC §3.6: `min(as_of, redeem) − issue`, from raw `issue` and `redeem` rows, never `Ticket.redeemedAt`. The suite's hand-built 3-ticket / 6.0-ticket-day case passes, and the fixture's `435.1` ticket-days for the General tier is consistent with 12 tickets issued weeks before the cut.

The zero-sale branch is:

```
rate = float(prior["a"]) / (float(prior["b"]) + exposure)   # a=1, b=1
```

02-c §6.1 specifies:

> `λ̂_cold = a/(b+E) · λ0(τ)e^{x'β} / λ̄_prior`, not `a/b`.

The code implements the first factor only. With no population baseline model, the multiplier is assumed to be 1. On the Standing tier of `evt_syn_03`, `E = 131.427`, so the rate is `1/(1+131.427) = 0.007551` per ticket-day. The finding's "the zero is evidence" is honoured; the finding's "shrink with the observed exposure" is honoured; the population-baseline correction is not.

The bigger issue is the label: the value is a declared-prior posterior mean, and the payload badges it `[FIXTURE]` with basis `"0 sales over 131.4 ticket-days at risk"`. `0 / 131.4 = 0`, not 0.00755. The basis contradicts the value. This is H7 and M10.

### 2.7 The boundary price rule: not implemented

The finding, 02-d §2.4 case (ii):

> `P*` = the highest all-in price at which expected sell-through still meets the organizer's floor.

The code:

```
recommended = band["level"]["lamports"]   # primary_optimum.py:114
```

for the uncapped and no-mass regimes, and the floor for the binding regime. `recommend` receives `sell_through_floor=None` from `orchestrator.price_guidance`; it has no `eta`, no `q_min`, no grid. The only place sell-through enters is the consequence table, `face * sellThrough / candidate`, and that table is not rendered. So the recommendation is the observed resale level (or the cap floor), not the boundary. `A14`, the sentence that would describe the boundary, is in the registry and in `extraLabelIds`, but no console state prints it.

This is the product-level narrowing: "price primary tickets off the resale record" is implemented as "set the primary price to the observed resale level". Whether that is the product he wants is an operator decision. It is not the finding's boundary, and the console does not claim it is (`basis: tier_marks`, A4, T2). But the headline says "Recommended primary price", which is the claim.

### 2.8 The D1 look-ahead: the headline number is computed from the event's own resales

This is the most consequential mathematical finding.

The finding, 03-b §2.1 (D1, the primary price):

> "In this product that happens while `Event.status = "draft"`, before the first `issue` row exists for the event, and it happens once."
>
> "What the engine may know at D1: the event's fixed facts and its own policy choices ... and fitted parameters from completed earlier events. It may not know any ticket-level, ledger-level or aggregate fact about `e`, and it may not know its own sell-through, because there is none yet."

The code computes the recommendation from the selected event's own marks at the `asOf` cut:

```
features = price_features.build(..., event_id=event_id, as_of=cut)
band = value_band.estimate(features=features, tier_id=tier["tierId"], ...)
recommendation = primary_optimum.recommend(features=features, ..., band=band, ...)
```

On `evt_syn_02` the first issue is `2026-09-11T11:00:00Z`, the first sale is `2026-09-14T19:00:00Z`, and the default cut is `2026-11-07T12:00:00Z`. The recommendation uses 9 of the event's own resales. At the true D1 cut the event has no sale, the regime is `no_resale`, and the recommendation would be `no_resale_record`. The binding branch that the product exists for is reachable only after the primary price was already charged.

The page presents it as a decision:

> `[UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General tier.`

and, three lines above, a true sentence:

> "Nothing after 2026-11-07T12:00:00.000Z enters any number, and the URL carries the instant."

Both are true statements about different clocks. The second is the data cut; the first is a D1 decision that 03-b says happens before the first issue. The page does not distinguish them.

It is not an implementation slip: `evt_syn_06` is `status: completed` (ends `2026-10-04T02:00:00Z`) and the page still recommends `0.53 SOL` from its 7 completed resales at a November cut. The build spec's §4.7 prints the same number, so the departure is in the spec, not only in the code. I am reporting the divergence, not attributing it to the build agent.

What would fix it is an operator decision, not a patch: either the recommendation is a counterfactual ("if this event were priced again") and the page says so, or it is a D1 decision and it is computed only from events that completed before this event's first issue. On this fixture the second choice leaves the cold start and a refusal, which is the honest answer for a primary price.

### 2.9 The cap-truncation bound: correct

02-b B1, B2, §3.2, §3.4 are implemented as written: the floor is the highest recorded price, the band has no upper end, no mean or upper quantile is computed, the sensitivity table is inert with `reason: "no upper tail in this record"`, and A19's three sentences are printed. The ceiling is integer `face * (10000 + cap) // 10000`, exact to the lamport. The at-ceiling test is `abs(markupBps - capBpsRecorded) <= 1`, and `capBpsRecorded is None` is its own branch. **STANDS.**

### 2.10 The [EXACT] line is wrong at its displayed precision

`evt_syn_07` Gallery: face 0.90 SOL, cap 2500 bps, exact ceiling `900000000 * 12500 // 10000 = 1125000000` lamports = 1.125 SOL. The page:

> `[EXACT] ceiling 1.12 SOL = face 0.90 SOL plus a cap of 25% — integer arithmetic on the tier face.`

0.90 × 1.25 = 1.125, not 1.12. `units._sol` (`units.py:67-70`) formats `f"{value:.2f}"`, which rounds 1.125 to 1.12. The payload is exact; the display is not. The recommended floor is printed as "at least 1.12 SOL", which is a true statement (1.12 < 1.125) but understates the floor by 5,000,000 lamports, and the [EXACT] equality is false as printed. A floor should round up, not to even. The default event (1.20 × 1.15 = 1.38) does not show it; the other binding event does.

### Mathematics verdict

**STANDS-WITH-NARROWING.** The implemented arithmetic is correct: the regimes, the floor, the band, the integer markup, the 2×2 solve, the gamma–Poisson zero, the DL τ with a floor. The narrowed statement: *the engine computes a resale-value level, a declared band, and a cap floor correctly; it does not compute the primary-price boundary of 02-d §2.4, and its headline number uses the same event's resales, which 03-b §2.1's D1 forbids. On a new event with no resales it refuses, so the number is a retrospective valuation of an event whose primary price is already committed.*

---

## 3. Honesty

The rule in BUILD-SPEC §2: every number carries its badge, the label is true, the badge is not interchangeable, and the banned sentence is not printed. I checked all four.

### 3.1 What stands

- The banner is the first element in document order, is not dismissible, and carries T1 verbatim plus the fixture sha.
- No `title=` attribute on any page state (`grep` found none; the test passes).
- Every numeric `.n` span begins with a badge. I walked the payload recursively; every numeric wrapper has `badge`, `basis` and `labelId`; I found no unbadged numeric wrapper.
- The banned sentence does not appear in any page state or in the JSON payload. `labels.contains_banned` returned `None` for all 12 states I fetched, including the cold start, the candidate cap, the fee and the sim. The X1 sentence appears only in `records/findings/00-adversarial-review-phase1.md` and `records/BUILD-SPEC-NIGHT.md` as the prohibition, which is where it belongs, and as a pattern in `labels.BANNED_SOURCES`, so deleting the ban would break a test.
- T1, T2, T3, T4 and T5 are the exact strings from §2.3.
- The design, simulation and chain blocks use `[DESIGN]`, `[SIMULATED]` and `[DEVNET]` correctly; the chain slot is absent with no fake signature, slot, Explorer link or "verified" claim.
- The fixture sha on the page matches the file on disk.

Those are real. The failures below are in the second half of the rule: whether the sentence is true.

### 3.2 A1 says "on this event" and prints the tier's count

The label (`labels.ALLOWED["A1"]`):

> "On this event the ledger records {n} sales. The sale rate is {x} per 1,000 ticket-days at risk. ..."

The code:

```
# api/guidance.py:288-290
def _market(tier, features, intensity, sales, at_ceiling, events):
    marks = tier["marks"]
    basis = f"{len(marks)} sales in this tier, {events} events with resale"
...
# console/blocks.py:190
f'{esc(labels.render("A1_ONE" if sales == 1 else "A1", n=sales, x=_per1000(market)))}'
```

`sales` is `len(tier["marks"])`, the tier's count. The page, on `evt_syn_01` (Floor tier):

> `[FIXTURE] 14 resales on this event · [FIXTURE] 14 tickets · [FIXTURE] 0 at the ceiling`
>
> ...
>
> "On this event the ledger records **6** sales. The sale rate is 25.9 per 1,000 ticket-days at risk."

The event has 14 sales; the Floor tier has 6. On `evt_syn_02` General: strip 12, A1 9. On `evt_syn_07` Gallery: strip 16, A1 4. The JSON basis string says "in this tier", so the marshaller knows the scope; the sentence does not.

This is the easiest five-minute catch in the product, and it is on the default page. The same block prints the tier name above the decision (`tier: Floor`), so a careful reader can resolve it, but the sentence itself is false as written.

### 3.3 A13 says the cold band is the spread across other events; it is the literature prior

The label (`labels.ALLOWED["A13"]`):

> "Not a prediction: this event has no resales yet, so the band is the spread across {n_events} other events and has not been checked against what those events sold for."

The code:

```
# value_band.prior_only
mu = float(prior["muLogRatio"])          # PRIOR = {"muLogRatio": 0.2612, "sigma": 0.406, "source": "02-e 4.7"}
lo = round(face * exp(mu - Z90 * tau))
hi = round(face * exp(mu + Z90 * tau))
```

and `_cold` passes `eventsWithResale` (5) as `n_events`. The band uses the 02-e §4.7 literature prior and the declared τ; it does not use the 5 events' mean, their spread or their count.

The page on `evt_syn_03` Standing (face 0.70 SOL):

> `[UNVALIDATED] prior band around face: 0.65 SOL – 1.26 SOL. That is a band around the declared prior, not a price for this ticket.`
>
> "Not a prediction: this event has no resales yet, so the band is the spread across **5** other events and has not been checked against what those events sold for."
>
> "This is a class-C bound from the schema and a class-B prior from the literature; it is not a measured result on this platform."

Two consecutive paragraphs give two different sources for the same band. The arithmetic settles it: 0.70 × e^{0.2612 ∓ 0.329} = 0.654 to 1.263. The pooled mean over the 5 events is 0.094962; 0.70 × e^{0.094962 ∓ 0.329} = 0.554 to 1.070. The shown band is the prior, not the 5 events. The finding 02-e §5.4 says the sentence must change rather than lie about the source; this one lies about the source. It is also the visible face of M2: the pooled estimate is computed and not applied.

### 3.4 A17 counts the wrong events, and the cold block and the refusal panel disagree on the same page

The label (`labels.ALLOWED["A17"]`):

> "The model is not fitted. {n_events} events have completed in the observation window and {m} have any resale activity, ..."

The code:

```
# price_features.py:298
"startedAtCut": parse(event["startsAt"]) <= as_of
# value_band.py:120
events_in_window = sum(1 for row in rows if row.get("startedAtCut"))
```

That is **started**, not completed. The cold decision block passes `eventsWithResale` for both counts (`blocks.py:_fitted_label` -> `_a17_label(events, events)`), while the refusal panel passes `eventsInWindow` for `n_events` (`blocks.py:237`). So the same page has two different counts.

Default `evt_syn_03` (cut 2026-11-07T12:00Z):
- cold block: "**5** events have completed in the observation window and 5 have any resale activity"
- refusal panel: "**One** event has completed in the observation window and 5 have any resale activity"
- truth: 1 completed (`evt_syn_06` ends 2026-10-04), 1 started.

At `asOf=2026-11-21T23:30:00Z` on the same event:
- cold block: "**5** events have completed"
- refusal panel: "**3** events have completed"
- truth: 2 completed (`evt_syn_04` ends 2026-11-14, `evt_syn_06` ends 2026-10-04); 3 started (plus `evt_syn_02`, which starts at 23:00 and ends at 02:00 the next day).

Three different numbers for the same clause on one screen. This is the clearest self-contradiction in the console, and it is on the spec's step 11.

### 3.5 A2 and A16 are printed on uncapped events, where there is no cap

A2 (`labels.ALLOWED["A2"]`):

> "The resale value of this ticket is bounded. The last recorded sale gives a floor, the resale cap gives a ceiling, and the interval is wide because the ledger records sales, not listings."

Page `evt_syn_04` (regime `uncapped`, face 0.80, no `resalePriceCapBps`):

> `[FIXTURE] tier: General Admission · face [FIXTURE] 0.80 SOL · regime [FIXTURE] uncapped`
>
> "The resale value of this ticket is bounded. The last recorded sale gives a floor, the resale cap gives a ceiling, ..."

There is no resale cap. A16 is the same problem:

> "at the ceiling [FIXTURE] 0 — At the cap — a rationing point, not a market-clearing price."

There is no cap and there are no cap hits. A2 is printed in the `_banded` branch (`blocks.py:105`), which is the uncapped and capped-no-mass regimes, and A16 is printed in every market block (`blocks.py:179`). On a capped-no-mass event both are defensible; on the uncapped event they describe an object that does not exist.

### 3.6 The zero-sale rate is a prior badged as a fixture, with a basis that contradicts its value

`evt_syn_03` has 0 sales and 131.427 ticket-days of exposure. The page:

> "On this event the ledger records 0 sales. The sale rate is **7.6** per 1,000 ticket-days at risk. That is a transaction rate for the ticket population, not the probability that a listed ticket sells."

The payload (12:16 state; at 12:25 the value is `0.007503`, because the exposure grew with the clock):

```
salesPerTicketDay: {value: 0.007551332, badge: "FIXTURE",
                    basis: "0 sales over 131.4 ticket-days at risk", labelId: "A1"}
```

`0 / 131.4 = 0`; the value is `1/(1+131.427) = 0.007551`. The rate is the gamma–Poisson posterior mean with the declared `Gamma(1,1)` prior (`intensity.py`). It is not computed from the fixture's counts; it is an engine output driven by a declared prior. The badge `[FIXTURE]` is the wrong badge under BUILD-SPEC §2.1 (B1 is counts, prices, dates, tiers, cap, sell-through, exposure; B4 is the band, the point estimate, the recommendation). The basis names the record but not the prior. And 03-b §6.5 and BUILD-SPEC §3.6 require the counts and the word `insufficient` rather than "a rate with a prior dressed as a measurement". The word `insufficient` appears only in the events refusal (`insufficient_events`), not next to the rate.

A judge who divides 0 by 131.4 gets 0; the page says 7.6. That is the honesty failure in its purest form: a number that does not come from the record, labelled as if it does.

### 3.7 The fee control lies and does nothing

The page has `feeLamports` with the label `(blank = no fee model)`. Enter `50000000` and press Recompute. The payload computes:

```
netRevenue.perTicket = 1,330,000,000 lamports   # 1.38 SOL - 0.05 SOL
netRevenue.perTier   = 10,640,000,000
```

and `_refusals` still appends:

```
{"code": "no_fee_model", "labelId": "no_fee_model", "reason": None}
```

unconditionally (`api/guidance.py:392`). The page prints:

> `[REFUSED] no_fee_model: No fee model is configured. The recommendation does not depend on an ad-valorem fee; the net value line does, so it is withheld.`

Both halves are false: a fee is configured, and the net line is computed. It is not rendered anywhere in `ticketpath/console/` (`grep netRevenue` in the console: no matches). The control changes the canonical URL and the JSON, not the page, and the page's refusal sentence is false on its face. This is a visible lie triggered by using a control on the page.

### 3.8 "under the deployed program" contradicts the banner

Banner:

> "[T5] No program is deployed on any cluster. Nothing on this page is a deployed guarantee."

`capBps=0` sentence:

> "9 of 9 recorded sales in this tier are above this cap; **under the deployed program** those transfers would have failed, so this record could not exist."

There is no deployed program. The sentence is a counterfactual written as an assertion. The banned-pattern list does not catch it because it looks for `\bis deployed\b`, `\bhas been deployed\b`, `\bwas deployed\b`, not "the deployed program". The spec's §4.8 wording contains the same phrase, so the build followed the spec; the spec violates its own X18.

### 3.9 The ticket count is not cut-aware

The page claim:

> "Nothing after 2026-09-01T00:00:00.000Z enters any number, and the URL carries the instant."

At that cut on `evt_syn_02`:

> `[FIXTURE] 0 resales on this event · [FIXTURE] 12 tickets · [FIXTURE] 0 at the ceiling`

The first issue on `evt_syn_02` is `2026-09-11T11:00:00Z`, after the cut. The market block on the same page refuses with "No ticket had been issued at this instant". The count is `len(event_tickets)` (`price_features.py:214`), all tickets in the store, not the issue rows at the cut. A future count is on the page under a sentence that says nothing future enters it. The same store-level count feeds `issuedCount` in the consequence table and `netRevenue.perTier`, neither of which is rendered, so the strip is the visible instance.

### 3.10 The [EXACT] line is false at its displayed precision

Covered in M10. `[EXACT]` is the badge that means "arithmetic true by definition"; on `evt_syn_07` it prints `1.12 = 0.90 × 1.25`, which is false as printed. This is a small number and a large category error: the one badge that claims exactness is the one that does not check out.

### 3.11 Badge placement inside prose

The A19 sentence's "8 of 9 (88.9%)" and the A1 sentence's counts sit in paragraphs with no badge immediately before them; the nearest badge is the panel heading. The decision panel's heading is `[UNVALIDATED]`; those counts are `[FIXTURE]`. The same counts are printed with `[FIXTURE]` in the market block, so a reader can check, but BUILD-SPEC P1 says the badge is the first text in the block. I rank this low because the counts are not hidden and the block badge is present; it is a gap in the letter of P1, not a false label.

### Honesty verdict

**FAILS.** The badge machinery, the banner, the ban and the exact mandatory sentences stand. The label-truth requirement does not. Four registry sentences state things the engine does not compute (A1, A2, A13, A17); the zero-sale rate is a prior badged as a fixture with a basis that contradicts its value; the fee refusal is false when the fee control is used; and the ticket count contradicts the page's own as-of claim. On `evt_syn_01` the evidence strip says 14 resales on this event and A1 says 6 sales on this event; on the default `evt_syn_02` the same pair is 12 and 9. On the cold-start page the same screen says 5 events have completed and One event has completed. These are exactly the failures §2 exists to prevent.

---

## 4. Code

The boring failures that ship, each with the file, the line and the input.

### C1. The console is outside the handler's try, so a pricing exception is an empty reply

```
# ticketpath/server.py:167
status, html = console_index(self.orchestrator, query, base=f"http://{host}:{port}")
# ... line 170:
try:
    handler, extra = match(method, split.path)
```

and inside `console_index`:

```
# ticketpath/server.py:61
except ApiError as exc:
    return exc.status, console_page.render_error(...)
```

Only `ApiError` is caught. A `ValueError` or `IndexError` leaves the handler thread; the connection closes with no status. `curl` reports `HTTP 000` and "Empty reply from server". The process stays up, `/health` and other events answer. This is the "exception path that renders a blank page", except there is not even a blank page.

Three triggers, all accepted by the loader:

| Input | Where it raises | HTTP |
|---|---|---|
| a `sale` row with `priceLamports: 0` on `evt_syn_04` | `value_band.py:80` `math.log(0/face)` | 000 |
| a sale after `evt_syn_04.startsAt` | `price_features.py:87` `raise ValueError(...)` | 000 |
| an event with `tiers: []`, selected | `orchestrator.py:316` `event["tiers"][0]["id"]` | 000 |

The API endpoints do not crash on the same stores: `/api/events/evt_syn_04/analytics` returns 200 on both the zero-price and the late-sale store, because those routes are inside the try and do not compute time-to-event. The console is the only surface with this hole.

### C2. The cap-violation sentence escapes the wrapper (fixed at 12:17, after the review)

**Status at 12:25: fixed in the working tree.** `blocks.py` now reads `esc(value_of(tier["band"]["capViolations"]["of"]))` and the page prints `9 of 9 recorded sales`. The entry is kept because it is what the 12:16 state did, and because it is the reason the acceptance test's step 9 failed at that time.

```
# ticketpath/console/blocks.py:44 at 12:16
f'{esc(tier["band"]["capViolations"]["of"])} recorded sales</span> in this tier are above this cap; '
```

`"of"` is a number wrapper (`{"value": 9, "badge": ..., ...}`), not an `int`. The page prints:

> `9 of {'value': 9, 'badge': 'FIXTURE', 'basis': '9 recorded sales in this tier', 'labelId': 'A1', 'unit': None} recorded sales in this tier are above this cap; under the deployed program those transfers would have failed, so this record could not exist.`

Trigger: `/?event=evt_syn_02&capBps=0`, the spec's step 9. The `count` is escaped correctly (`count["value"]`); only `of` is wrong.

### C3. `labels.render` returns the raw template when no fields are passed (fixed at 12:17, after the review)

**Status at 12:25: fixed on the page.** The refusal now prints `[FIXTURE] 0 sales is too few to fit a path` through a new `_count_sentence` helper, so the `{n}` is gone and the count keeps its badge. The registry function is unchanged (`labels.py:387`), so any future caller that passes no fields can still leak a placeholder; the page no longer does.

```
# ticketpath/core/labels.py:387 (unchanged)
return template.format(**fields) if fields else template
```

`insufficient_marks` has `{n}` in its template:

```
"insufficient_marks": "{n} sales is too few to fit a path; the flat line below is the benchmark, not a forecast."
```

`_refusal_fields` returns `{}` for it (`blocks.py:237`), so the page prints:

> `[REFUSED] insufficient_marks: {n} sales is too few to fit a path; the flat line below is the benchmark, not a forecast.`

Trigger: any tier with 1 to 3 marks or 0 marks (`evt_syn_03`, `evt_syn_05`, `evt_syn_08`, `evt_syn_01` Box, `evt_syn_02` Front). This is the spec's step 11. The `insufficient_time_spread` and `outside_support` branches pass n/d/k and format correctly; only `insufficient_marks` and `degenerate_design` have no fields.

The same sentence promises "the flat line below"; no path table is rendered anywhere in the console (`grep martingale ticketpath/console/` is empty). The refusal tells the reader to look at something that is not there. The spec §3.5 requires the flat martingale; the build omits it.

### C4. The ticket count is not cut-aware

```
# ticketpath/core/price_features.py:214
"tickets": len(event_tickets),
```

`event_tickets` is every ticket of the event, regardless of issue date. The evidence strip renders it (`console/page.py:167`). At `asOf=2026-09-01T00:00:00Z` on `evt_syn_02`, the strip says `12 tickets` while the first issue is 2026-09-11. The exposure denominator correctly uses issue rows, so the same page can say "12 tickets" and "No ticket had been issued at this instant". This is a temporal-correctness bug in a feature, not just a label.

### C5. The tierless event crashes

```
# ticketpath/orchestrator.py:316
tier_id = event["tiers"][0]["id"]
```

A store with an event whose `tiers` is empty is accepted by the validator (there is no minimum). The console's default tier dereferences `[0]`. HTTP 000. The API returns 200 for the same event (`faceValueLamports: 0`, `saleCount: 0`), so only the console has the gap.

### C6. HEAD `/` is 501

`BaseHTTPRequestHandler` has no `do_HEAD`. `curl -I http://127.0.0.1:8891/` returns:

```
HTTP/1.1 501 Unsupported method ('HEAD')
Content-Type: text/html;charset=utf-8
```

with the default Python error page, no banner, and the Python version in the `Server` header. `POST /` is 404 and `PUT /` is 501. A link checker or a `curl -I` sees a different page. Low risk, but the console is server-rendered and a HEAD should mirror the GET headers, or the method should 405.

### C7. The fee has no upper bound and the net revenue goes through float

`_parse_fee` rejects `< 0` and accepts arbitrarily large integers. `primary_optimum` computes:

```
per_ticket = int(round(recommended * (1.0 - float(fee.get("adValoremBps", 0)) / 10000.0))) - int(fee.get("perTicketLamports", 0))
```

`recommended` is a lamport int; the multiplication is float. At 1e18 lamports the float loses precision before the `int()` round. On this fixture, `feeLamports=999999999999999999999` produces a net revenue of `-999999999998619999999` with an `[EXACT]` badge. The page does not render it, so the visible risk is the JSON tool and any future renderer. This is a "money should be integer" defect on the input path, and it has no maximum.

### C8. The store validator and the core disagree about what a legal row is

The loader accepts `priceLamports: 0` and a sale after `startsAt`; the core asserts a sale must be priced (`math.log`) and must be before the event (`raise ValueError`). The loader is the gate for the fixture; a real adapter would need the same checks, or C1 is reachable from any store the loader accepts. This is the root of C1, and it is why the crash is not a "bad fixture" story.

### C9. The suite is green because it tests the modules, not the states that fail

306 tests, OK. The gap is coverage, not honesty in the tests:

- `tests/test_console_page.py` covers the cold start's refusal and the prior band, but not the rendered refusal text (`{n}`) and not the cap-violation sentence.
- `tests/test_console_route.py` covers the 400/404 pages and the canonical URL, not a pricing exception.
- `tests/test_labels.py` checks that an allowed sentence matches no banned phrase; it does not check that a label's subject matches the number it is given (A1's "on this event" versus the tier's count), or that A13's source sentence matches the band it describes.
- `tests/test_guidance_api.py` walks the payload for badges and basis, which is why the unbadged numbers are absent; it does not check semantic truth.

None of the three crash inputs is in the suite. The suite is real and it passes; it is not the acceptance test the spec describes.

### Code verdict

**FAILS.** Three store-valid inputs produce no HTTP response at all; the [EXACT] line is wrong at its displayed precision; the loader accepts rows the core cannot price; and the fee arithmetic goes through float with no upper bound. The two renderer defects that were on the spec's own judge path at 12:16 (C2, C3) were fixed at 12:17, so the current state does not have them; the blank-page class remains, and it is one malformed row away from real data.

---

## 5. Refusals

The engine must refuse to answer what it cannot answer, visibly and in words.

### 5.1 What works

| Object | Refusal | Evidence |
|---|---|---|
| Sale probability at a price | `saleProbability: None`, `reason: "not_identified"`, A15 in the refusal panel | Every tier and the top-level payload; the `pricing_model_adapter` sets it `None` explicitly; I could not get a number through any route or control. |
| Primary price with no resales | `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.` plus the prior band | `evt_syn_03`, `evt_syn_05`, `evt_syn_08`, and `evt_syn_02` before its first sale. |
| Upper bound on a binding cap | `noUpperBound: true`, `hiLamports: None`, A19, no mean, no upper quantile, `applicable: false` on the sensitivity | `evt_syn_02`, `evt_syn_07`; a test fails if a mean or upper end is returned. |
| Interior optimum | `no_demand_response`, unconditional, with `requiredInputs: ["eta", "q_min", "a completed sell-through series"]` | Every state; no code path returns an interior optimum. |
| Net revenue without a fee | `no_fee_model`, `netRevenue: None` | Every state with a blank fee. |
| Zero exposure | `no_exposure`, with the sentence "No ticket had been issued at this instant, so there is no denominator." | `evt_syn_02` at 2026-09-01; `evt_syn_08`. |
| Path | A named reason per guard: `insufficient_marks`, `insufficient_time_spread`, `degenerate_design`, `cap_mass_dominates`, `outside_support` | Every tier on the fixture; none is available. |
| The refusal panel itself | Never empty, every line `[REFUSED]` with a code and a sentence | All 12 states. |

I could not get a sale probability, a forecast on an event with no resales (only a band labelled as a prior), or a value on a capped-and-binding event without `noUpperBound`. Those three attempts all failed in the right direction. That is the product's strongest area.

### 5.2 What fails

- **The path refusal promises "the flat line below" that is not rendered.** At 12:16 it also printed `{n}`; that placeholder was fixed at 12:17. The missing flat path is still the only path content on the cold-start URL.
- **The no-fee refusal is false when a fee is supplied.** The engine computes the net line; the page says it has no fee model and withholds it.
- **The no-resale refusal is followed by a non-zero sale rate on the same page.** `evt_syn_03`: the decision says it will not state a primary price, then the market block says "the sale rate is 7.6 per 1,000 ticket-days" with 0 sales. The rate is a prior; the page does not say so.
- **The candidate cap is not passed to `primary_optimum`.** The spec says the candidate travels to `value_band` and `primary_optimum`; `recommend` has no such parameter. On `capBps=0` the recommendation is still 1.38, above the candidate ceiling, and the page does not say the recommendation is impossible under that policy. The violation line flags the recorded sales, not the recommendation.
- **`no_upper_bound` is in the refusal panel on a binding event, but the cap-violation sentence says "under the deployed program"**, which contradicts the banner.

### Refusals verdict

**STANDS-WITH-NARROWING.** The engine refuses the unanswerable consistently and visibly; the three attempts the brief names all fail in the right direction. The narrowed statement: *the refusal codes and the sentences are there, but the path refusal promises a flat path that is not rendered (the `{n}` placeholder was fixed at 12:17), the fee refusal is false in the one state where the fee control is used, and the no-resale page still prints a prior-derived rate beside the refusal.*

---

## 6. Fix list, ranked by risk

1. **Make the console total.** Move `console_index` inside the handler's `try` (or catch `Exception` in `console_index` and render `render_error`), and make the value path refuse on a zero-price sale, a post-start sale and an event with no tiers. Today three loader-valid stores take the page out with no HTTP response. This is the only class that produces nothing at all, and it is one malformed row from real data.
2. **Fix the two renderer defects on the spec's judge path.** `capViolations["of"]["value"]` in `blocks.py:44`, and a fields dict for `insufficient_marks` (with `n` = the tier's sale count). **Both were fixed in the working tree at 12:17, after this review's first pass.** Keep a regression test for each; the `insufficient_marks` sentence still promises a flat path that is not rendered.
3. **Make the labels true.** A1 must say "in this tier" or carry the event count; A13 must use the pooled band or be replaced by A12 plus A11; A17 must count completed events and pass the same count to both blocks; A2 and A16 must be conditioned on a cap; the zero-sale rate must be badged `[DECLARED]` or `[UNVALIDATED]` with a sentence naming the gamma prior and a basis that matches its value; the fee refusal must be conditional and the net line must be rendered when a fee is set. This is the area that decides whether the honesty rule is real.
4. **Decide D1.** Either the recommendation is a D1 decision, in which case it may not use this event's resales (and on this fixture it becomes a refusal), or it is a counterfactual, in which case the page must say "if this event were priced again" and show the event's status and date in the decision block. This is a product fork, not a bug fix; it should go to the operator as a decision.
5. **Fix the [EXACT] display.** Render the ceiling in lamports or round a floor up; do not print an equality that is false at the displayed precision.
6. **Make the ticket count cut-aware.** Use the issue rows at the cut, as the exposure denominator already does.
7. **Fee arithmetic and bounds.** Integer arithmetic for the net line, a maximum on `feeLamports`, and a clear negative-net state.
8. **Headers and methods.** HEAD `/` should mirror the GET headers or return 405; `POST /` should be 405, not 404.

The three I would do first: **1, 3, 4**. Item 2 is already fixed in the working tree at 12:17; it still needs tests. If the D1 decision is available, it is first by consequence; but it is a decision for him, not a fix, and it changes the product's central number.

---

## 7. What a judge could catch in five minutes

**Open the cold-start event `/?event=evt_syn_03` and read the market block.** It says:

> "On this event the ledger records 0 sales. The sale rate is 7.5 per 1,000 ticket-days at risk."

Zero sales, a non-zero rate, badged `[FIXTURE]` and based on `"0 sales over 131.4 ticket-days at risk"`. Divide 0 by 131.4 and you get 0; the 7.5 is the `Gamma(1,1)` prior posterior mean `1/(1+131.4)`. It was 7.6 twenty minutes earlier, because the clock advanced and the exposure grew; a rate that moves with the clock on a static fixture is itself the proof that it is a prior, not a measurement. A judge who asks "where does that rate come from with no sales" has caught the honesty failure in one screen, and no arithmetic on the page explains it.

This replaces the Python dict that was the five-minute catch at 12:16: setting `capBps=0` used to print `{'value': 9, 'badge': 'FIXTURE', ...}` on the judge path, and that was fixed in the working tree at 12:17, while this review was being written. If a later reader finds the dict gone, this is why; if they find it back, C2 applies again.

The runner-ups, all in the same five minutes:
- **The default page:** the evidence strip says 12 resales on this event; the market block says "On this event the ledger records 9 sales." On `evt_syn_01` the pair is 14 and 6.
- **The cold-start page:** one paragraph says "5 events have completed in the observation window", another says "One event has completed". The true count at the default cut is 1.
- **The cold-start band:** A13 says the band is "the spread across 5 other events"; the numbers are the literature prior `0.70 × e^{0.2612 ∓ 0.329}`, and the pooled 5-event mean would give a different band.
- **The uncapped page:** "the resale cap gives a ceiling" on an event whose regime line says `uncapped` and whose cap field is absent.
- **`evt_syn_07`:** `[EXACT] ceiling 1.12 SOL = face 0.90 SOL plus a cap of 25%`, which does not multiply.

---

*End of review. No file other than this one was written. No commit, no push, no fix.*

---

## CORRECTION (2026-11-08T08:30Z): four machine handles redacted, no verdict changed

**Scope:** this file only, and only three lines: two in "What I did not review" and one in §1.1.
**Why:** this repository is public and `tools/public_safety.py` refuses a tracked file that carries
an absolute path under a home directory, a process id, or the name of another of the operator's
repositories. The rule and its reason are in `.public-denylist`.

**What the redaction costs: nothing that was reviewed.** The bullet's job is to say what was out of
bounds. It still says that: the frontend is given by the repository-relative path this repository
uses for it everywhere else, and the out-of-bounds trees of the operator's are named by what they
are instead of by three directory names. In §1.1 the point is that the port was already held by a
plain `python3` process that this pass did not own, which the sentence still says; the pid it then
printed identified a process that stopped on 2026-11-07.

| Where | Was | Now |
|---|---|---|
| What I did not review, frontend bullet | an absolute path under a home directory | `../ticketing-frontend` |
| What I did not review, records bullet | three of the operator's repositories, named | "the operator's fleet tool repositories (out of bounds)" |
| §1.1 | ``(`python3`, pid <n>)`` | ``(`python3`)`` |

**Residue, stated rather than hidden.** Port numbers on lines this rule does not classify are
unchanged. `.public-denylist` states why it does not deny those, and `/tmp` paths are exempt for
`records/` on purpose. `python3 tools/public_safety.py check --tracked` reports zero hits for this
file as of this note.

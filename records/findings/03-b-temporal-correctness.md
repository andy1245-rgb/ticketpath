# Phase 3-B — Temporal correctness of every feature, and the leakage audit

**Status:** complete (first pass). **Written:** 2026-11-07T11:13Z UTC.
**Agent:** Phase 3-B research agent (`p3-temporal`).
**Scope:** programme §4.8 in full; §4.7 for the predictive/causal split where it decides a feature;
§3 Phase 3 for the feedback loops and causal question insofar as they are a clock problem; §3 Phase 6
for leakage, survivorship, selection and regime change. The deliverable is the decision-time table for
every feature the engine computes, the look-ahead traps with the test that catches each, the
policy-contamination audit, the evaluation protocol that follows, and a mechanical build checklist.

**Depends on:** `RESEARCH-PROGRAM.md` §3 Phase 3, §3 Phase 6, §4 in full; `AGENTS.md`;
`records/README.md`; `records/00-data-situation.md`; `records/F-decision-log.md`;
`records/C-variable-registry.md`; `records/CONTRACT-MAP.md`; `../ticketing-frontend/lib/types.ts`
and `API_CONTRACT.md`; the `ticketpath/` source and `tests/` on disk.

**Phase 2 files present when this ran:** `02-a-price-paths.md` (73.4 KB), `02-c-sale-hazard.md`
(83.8 KB), `02-d-elasticity-fees-optimum.md` (61.5 KB), `02-e-cold-start.md` (76.5 KB).
**`02-b-cap-truncation.md` was NOT present**: `NIGHT-QUEUE.md` lists it as dispatched and no file exists,
so the cap treatment here rests on `00-data-situation.md` Gap 2, `01-b` §4.4 and §5.3, and `02-a` §6,
not on the report that was meant to own it. Also present and read where relevant:
`02-ai-ml-decision.md` (36.9 KB), `02-rubric-and-scoring.md` (42.9 KB). **No `03-a` existed**, so the
interaction registry this file would defer to is absent and the interaction-dependence of a cut is
handled here directly (§4 T6, §5 P3).

**Append-only.** Disagreements with prior findings are in §9, recorded and not resolved.

---

## 1. What I concluded

1. **There are three instants, not two, and the third is the one the data imposes.** The product decides a
   primary price before on-sale (D1) and produces estimates inside the trading window (D2). But every
   field in the wire contract is a value as of the instant the payload was computed (D3, extraction), and
   the contract carries no marker for it. Leakage in this dataset is exactly D3 information entering a D1
   or D2 decision. Stated that way, the audit has one question per field, not one per model.

2. **Of the 61 features the engine would compute, 25 are usable at D1, 43 at D2, and 18 are dropped.**
   Every D1 fact is still true at D2, so nothing is usable at D1 alone; 18 are usable only at D2 (A14 is one
   of them, and it is the case worth naming: a state that is a future fact at D1 and a live reading at D2).
   The 18 dropped split into three reasons that need different remedies: 6 are absent from the observation
   set, 11 carry post-decision information, 1 is unidentified rather than absent. §3 has the table and
   §3.5 the counts.

3. **The contract states no as-of for any derived aggregate, and its query types carry no time window.**
   `API_CONTRACT.md` and `lib/types.ts` contain no `asOf`, no `as_of`, no `since`, no `until` and no `as of`
   (counted: zero occurrences in both files), and neither query interface takes a time parameter
   (`EventQuery`: `status`, `city`, `q`, `cursor`, `limit`; `TicketQuery`: `eventId`, `ownerWallet`,
   `status`, `cursor`, `limit`; MEASURED, `lib/types.ts` lines 205 and 214). Nor does either file state the
   window over which `avgMarkupBps`, `medianResalePriceLamports`, `resoldShare`, `markupDistribution`,
   `topDestinations`, `ResaleStats` or `EventAnalytics.uniqueHolders` are computed. By construction they
   are whole history or as of the request, and a consumer cannot tell which. **This is a finding and a
   question for the operator (Q1), not an assumption.** The consequence is testable and unforgiving: no
   derived aggregate may be a live feature. They are label and audit objects only. `priceSeries` is the
   single exception and only when the caller drops the current, incomplete UTC day. [MEASURED: absence,
   by grep over the contract; class C: the consequence]

4. **The temporal defects fall into three families, and one mechanism closes all three.** Clock (a value
   from after the cut enters a feature), population (the event set is selected on an outcome that is
   partly unknowable at the cut), edit (a row entered or changed after the cut). Every member of every
   family is caught by the same three tests: a mandatory cut argument, a prefix-invariance property test,
   and a future canary. That is why §7 is a checklist and not a set of principles.

5. **The feature most likely to ship with a leak is one the programme recommends: the cap-crossing date
   and the cap mass.** `02-a` §6.1 C3 and C4 call the cap mass "the single best use of the cap" and give
   the crossing date as a known-price anchor. As written, C4 defines it as *the last* day on which a sale
   landed at the cap, which is a whole-history quantity: to know a day was the last you must have seen
   every later day. It reads like an as-of feature, it is recommended by a report, and no name or type in
   the contract hints at the problem. The as-of restatement ("the most recent cap sale at or before `t`")
   is admissible; the retrospective one is a direct read on the level of value and will be learned.
   §4 T1 has the mechanism and §7 row 16 the check. [MEASURED definition, class C for the consequence]

6. **The three policy contaminations are real, and the third is structural rather than statistical.**
   The resale cap truncates the price record. The verified-wallet gate changes who can arrive, which makes
   the pooled hazard a mixture rather than a biased estimate. And the organiser's own primary price is the
   denominator of the target, the base of the cap, and the cause of the sell-through that is used as a
   regressor. That last one is not a bias to be corrected by conditioning: **the engine's recommendation
   changes the data generating process for the engine's own inputs**, so the deployment distribution is
   not the training distribution by construction, and no resampling fixes it. Only one randomised tier-face
   experiment corrects it (`02-d` §3.6). §5 gives the direction of each bias and says, for each, whether
   it is correctable inside the observation set or only flaggable.

7. **The age-period-cohort collinearity is worse than `01-b` §4.2 states, in a way that matters for this
   build.** `01-b` shows the linear price trend is not identified because age + cohort = period inside an
   event. The same dependency means a **regime dummy for a platform policy change is a cohort effect**:
   the date the cap changed, the date the verified-wallet requirement was switched on, and the date the US
   fee-disclosure rule changed what "face" means are all collinear with calendar drift in a single-platform
   series. So the one natural experiment the dataset offers (policy variation) cannot be separated from
   time without staggered adoption. §4 T4. [ASSERTED, class C]

8. **The evaluation protocol that follows is prequential, with three clocks frozen rather than one.** The
   cut instant, the hyperparameters, and the event population must all be frozen at the fold, or the fold
   leaks through a door `02-a` §8.5 leaves open. `02-a` names two boundaries (across events, within an
   event) and I add the two that sit outside both. §6.2 is the crossing table. [class C]

9. **The floors are arithmetic, not power analysis.** Between-event dispersion needs about 9 events before
   its interval is narrower than its own value; an empirical 5%/95% residual band needs about 20
   out-of-sample residuals or it is just the minimum and maximum. Below those, the honest output is a
   stated band and the word "insufficient", never a number that looks like accuracy. §6.4 and §6.5.
   [class C, derived]

10. **The build already enforces one temporal rule and it is the wrong half.** `tests/test_boundaries.py`
    asserts that `ticketpath/core/` contains no `datetime.now(` or `utcnow(`, which prevents the wrong
    clock. It does not prevent the wrong window, and every leak in this document is a wrong window.
    [MEASURED: the test exists and its scope is one directory]

11. **One correction to a prior record.** `CONTRACT-MAP.md` §6 lists "event-level cap *binding* evidence
    (sales at the cap, rationed demand)" as absent from the contract. It is not absent; it is derivable.
    A sale is at the ceiling when `markupBps` equals `resalePriceCapBps`, both fields being bps over the
    ticket's own face, which is what `01-b` §5.3 and `02-a` §6.1 both say. One caveat belongs in the code
    rather than the prose: the wire rounds markup half away from zero, so an on-the-ceiling sale can read
    `cap-1` or `cap+1` bps on a face value that does not divide evenly, and the test needs a one-basis-point
    tolerance. [MEASURED: `core/markup.py` `_round_half_away_from_zero`; class C for the tolerance]

12. **Nothing here is validated against data, and two things in it are not even testable yet.** No real
    ledger exists (`00-data-situation.md` §1, §2), so the leakage audit is a specification of the tests,
    run against synthetic fixtures that exercise code paths only. The overlap that would let T4's
    collinearity be *measured* (overlapping asks at different prices, staggered issuance) requires either
    the listing panel or a real ledger. Wording throughout: the test exists, the failure has not been
    observed.

---

## 2. The decision times, stated precisely

### 2.1 D1 — the primary price

**The instant.** The organiser commits `TicketTier.faceValueLamports` per tier. In this product that
happens while `Event.status = "draft"`, before the first `issue` row exists for the event, and it happens
**once**: `API_CONTRACT.md` has nine endpoints, seven reads and two wallet-verification POSTs, and no
price-mutation endpoint (`02-d` §1.1, MEASURED). So D1 is irreversible, and every later estimate the
product shows is either a valuation of something already priced or a recommendation for a different event.

**The cut instant for a replay, and why deriving it is legitimate.** The contract carries no `onSaleAt`
(`02-e` §2.1, MEASURED), so a backtest must construct one. Define

```
T1(e) = min { occurredAt : entry.kind = "issue" and entry.ticketId belongs to e }
```

Every entry that could inform a D1 decision for event `e` is strictly before `T1(e)`, because no ticket of
`e` existed before it and no resale of one could. Cutting at `T1(e)` therefore admits nothing that existed
after the decision, and any earlier cut yields the same empty set for `e`. The derivation is not
look-ahead. What *would* be look-ahead is using anything else about `e`'s issuance history, and in
particular the last issue row, or `issuedCount` as an achieved total rather than a rate over time.

**What the engine may know at D1:** the event's fixed facts and its own policy choices (venue, city,
`startsAt`, tier structure, cap, the two resale flags, fee configuration), whatever external variables
were published before `T1`, and fitted parameters from *completed earlier* events. It may not know any
ticket-level, ledger-level or aggregate fact about `e`, and it may not know its own sell-through, because
there is none yet.

### 2.2 D2 — the in-market estimate

**The instant.** Any `t` with `T1(e) < t < startsAt(e)`, the instant at which the engine is called to
produce a value, a horizon path, a sale probability, or an alternative primary price. There is no single
such instant: D2 is a grid, and every row of §3 marked **R** is a function of where on the grid you stand.

**What the product can do at D2, stated so the protocol does not assume more.** It can show a valuation
and a hazard. It cannot change a posted price, because no endpoint mutates `faceValueLamports` and the
tier price is fixed at event creation. So D2's honest outputs are: the current secondary value band, the
probability of transacting, and a recommendation for a primary price on a *future* event. A genuine
dynamic policy is a schema and product change, and it is the operator's decision (`02-d` §8, and
`F-decision-log` should carry it as a row). This matters for temporal correctness in a specific way: if D2
cannot act, then D2's numbers are descriptive and cannot create the feedback loop that §5 P3 describes.
If the operator adds a price-mutation endpoint, every D2 number becomes an action and P3 becomes live.
Recorded as Q8.

**The three clocks inside D2.** Time-to-event `τ = startsAt - t`; ticket age `a = t - issuedAt`; calendar
time `t`. They satisfy `τ = (startsAt - issuedAt) - a` exactly, so with a common issue time per event two
of the three are affine functions of each other (`02-c` §3.1). This is the same dependency as §4 T4.

### 2.3 D3 — extraction, the instant the payload was computed

Every field in `lib/types.ts` is a value as of the moment the server built it. The contract carries no
field saying when that was: `API_CONTRACT.md` specifies no payload timestamp, and `CONTRACT-MAP.md` §6
records the omission as a known gap, with `now` exposed only on `/health`. Our own build adds a
`dataSource` block to every payload, and it carries `{mode, synthetic, label, note}` with no instant
(MEASURED, `records/CONTRACT-MAP.md` §7.2). So a cached payload and a live one are indistinguishable to
any consumer of the contract.

**This is the audit's organising fact.** For each field the question is not "when could a human know
this", it is **"is the value I am holding the value at `t`"**. §3's `Vintage` column answers that question
separately from the `D1`/`D2` verdict, because they fail differently: a field can be perfectly knowable in
principle and still be a leak in practice, which is the case for every snapshot field in the contract.

### 2.4 The sentence the whole audit reduces to

> Leakage is D3 information entering a D1 or D2 decision. Nothing else in this document is a separate
> failure mode; the families in §4 differ only in how the D3 information arrives.

---

## 3. The decision-time table

### 3.0 Legend

**Decision verdict**

| Verdict | Meaning |
|---|---|
| **P** | Knowable at or before D1, and therefore at D2 as well |
| **R** | Knowable at a D2 instant `t`, not at D1 |
| **N** | Knowable at neither without look-ahead. **Dropped**, with the reason given |

**Vintage** (whether the value you hold is the value at `t`)

| Code | Meaning |
|---|---|
| **S** | Static. Fixed at event creation; no vintage problem |
| **H** | Historical row. Carries its own `slot` and `occurredAt`; safe if and only if truncated at the cut |
| **K** | Snapshot. The quantity is knowable at `t`, but the stored value is as of D3. Must be polled and logged at `t` or it is look-ahead |
| **A** | Aggregate over a window the contract does not state, and not truncatable by the consumer |

Feature identifiers follow `records/C-variable-registry.md` where one exists (`V1`, `V2`, …). Where the
registry has no entry, the identifier here is new and prefixed with the group letter. Nothing in this
table is added to the registry by this file; §11 lists the rows it implies.

### 3.1 Group A — event, tier, policy and external facts (29 features)

| # | Feature | Definition | Becomes knowable at | D1 | D2 | Vintage | Note |
|---|---|---|---|---|---|---|---|
| A01 | `time_to_event` (V1) | `startsAt - t` in hours, and its day bucket | `startsAt` is published, before on-sale | P | P | S | The clock. Future-blind by construction. Must enter interacted, never as a standalone slope (`01-d` §4) |
| A02 | `event_ends_at` | `Event.endsAt` | event creation | P | P | S | Only used for fold construction and event duration |
| A03 | `venue`, `city` | free-text strings | event creation | P | P | S | Join keys for A17 to A19 and A28. A name mismatch drops a row silently; normalise before use |
| A04 | `organizer_id`, `organizer.verified` | organiser identity and vetting flag | creation; `verified` may change later | P | P | S for id, **K** for `verified` | `verified` is a state, not a date |
| A05 | `tier_count` | number of tiers | creation | P | P | S | Evidence that demand is heterogeneous, not a demand measure |
| A06 | `tier_total_supply` | `TicketTier.totalSupply` per tier | creation | P | P | S | The denominator of sell-through |
| A07 | `tier_face` (**V-endogenous**) | `TicketTier.faceValueLamports` | creation | P | P | S | **At D1 this is the decision, not a predictor.** Retained as the numeraire only. §5 P3 |
| A08 | `price_ladder_ratio` | max/min tier face within the event | creation | P | P | S | Same exclusion as A07: it is chosen |
| A09 | `resale_enabled` | `Event.resaleEnabled` | creation | P | P | S | No endpoint changes it, so static. A false value means resale is unobserved, not absent |
| A10 | `resale_cap_bps` | `Event.resalePriceCapBps`, null = uncapped | creation | P | P | S | A **parameter of the data generating process**, not a covariate (`01-d` §4). As a *money* ceiling it is `p0(1+c)` and therefore a function of the D1 decision |
| A11 | `requires_verified_wallet` | `Event.requiresVerifiedWallet` | creation | P | P | S | Stratum only, never a free regressor. §5 P2 |
| A12 | `fee_model`, `settlement` | platform fee, royalty, per-unit vs ad valorem, settlement lag | must be a contract term known before D1 | P | P | S | Configuration, not data. Absent from the contract (`00-data-situation.md` Gap 4). Missing fee must raise, not default to zero |
| A13 | `event_status_flag` | `status` reduced to "has on-sale happened" | from the transition, which is untimestamped | P | P | **K** | Usable only as the live `draft`/`on_sale` pair read at `t`. A value read later is the eventual state |
| A14 | `event_status_terminal_at_D1` | `sold_out` or `completed` as a D1 predictor | after the event begins selling | **N** | R | K | Dropped at D1: the state is a fact about the future and carries no clock (`02-e` §2.2) |
| A15 | `primary_sell_through` (V2) | `issuedCount / totalSupply`, per tier and event | continuously, as tickets issue | **R** | R | **K** | The most valuable D2 feature and the most dangerous vintage: a snapshot used at `t` must have been logged at `t`. `01-b` §5 addition 4 and `02-e` §2.4 for the mechanism |
| A16 | `on_sale_age` | `t - onSaleAt` | never: no field exists | **N** | **N** | — | **Dropped, absent.** Also kills sell-through velocity. Operator Q6 |
| A17 | `venue_capacity` (V4) | seats, external | a published source, before on-sale | P | P | S | Not in contract. External join on free-text `venue` |
| A18 | `venue_type` (V6) | indoor/outdoor/arena/stadium | external | P | P | S | Same join |
| A19 | `city_market_size` (V7) | population/DMA, Census | the source's release date, which must precede D1 | P | P | S | **Condition:** if the release postdates `T1(e)`, it is a leak, and it is a small one nobody checks |
| A20 | `competing_supply_same_night` (V8) | other events at nearby venues that night | announced, on a rolling basis | P | P | **K** | Condition: a show announced after `T1` was invisible at D1. The set as of D3 is the eventual set, so the collection must be dated |
| A21 | `tour_routing` (V9) | announced stops and gaps | announced, incrementally | P | P | **K** | Same condition, sharper: the *completed* routing is the future. Added dates are the classic version of this leak |
| A22 | `event_calendar_structure` (V11) | weekday, holiday, festival adjacency | calendar | P | P | S | Truly static |
| A23 | `weather_forecast` (V12) | forecast for the event date | within the forecast horizon, about 10 days | **R** only | R | K | Not knowable at D1. Admissible at D2 only when `τ` is inside the horizon, which must be a condition in code, not in prose |
| A24 | `weather_actual` | observed weather | after the event | **N** | **N** | — | **Dropped, post-decision.** It is a label for an attendance model, not a feature |
| A25 | `artist_team_state` (V10) | injury, lineup, suspension | during the window | **R** only | R | K | `01-d` rejects it from the primary problem for exactly this reason. Admissible at D2 |
| A26 | `album_release_timing` (V13) | announced releases | if pre-announced | P | P | K | Condition: a release announced after `T1` is not knowable at D1 |
| A27 | `macro_conditions` (V16) | CPI, unemployment, consumer confidence | release date, and **revised afterwards** | P | P | **K** | The revised series is D3 information. Use the vintage as published at the time, or the coefficient absorbs revisions |
| A28 | `transit_and_access` (V17) | transit proximity, parking | external, static | P | P | S | Weak, and static |
| A29 | `event_category` | genre, tour identity | never: no field | **N** | **N** | — | **Dropped, absent.** `02-e` Q2. Best single cold-start covariate and it does not exist |

### 3.2 Group B — ticket state as the contract carries it (11 features)

| # | Feature | Definition | Becomes knowable at | D1 | D2 | Vintage | Note |
|---|---|---|---|---|---|---|---|
| B01 | `tier_id`, `tier_name` | the ticket's tier | mint | P | P | S | Tier is the only quality axis the contract supports (`00-data-situation.md` Gap 3) |
| B02 | `ticket_face` | `Ticket.faceValueLamports` | mint | P | P | S | Equal to the tier face. Normaliser, never a regressor at D1 |
| B03 | `serial_prefix` | tier prefix of `Ticket.serial` | mint | P | P | S | Class **E** and unverified: only worth using if the numeric part is issuance-ordered, which is a hypothesis, not a fact (`C-variable-registry` §5.2) |
| B04 | `issued_at` | `Ticket.issuedAt` | when the ticket issues | **R** | R | H | Nonexistent at D1 by definition |
| B05 | `seat_coordinates` (V15) | section, row, seat | never: no field | **N** | **N** | — | **Dropped, absent.** `F-decision-log` Q1. Strongest within-event axis in the published literature and unexpressible here |
| B06 | `owner_wallet` as stored | `Ticket.ownerWallet` | the current owner is a fact now; the field is as of D3 | **N** | **N** | **A/K** | **Dropped as a field, recoverable from the ledger.** Use the last `toWallet` at or before `t` instead, which is group C |
| B07 | `ticket_status` as stored | `valid`/`listed`/`redeemed`/`revoked` | the state at `t`; the field is as of D3 | **N** | **N** | **K** | **Dropped.** "Listed at D3" says nothing about "listed at `t`". This is the exposure denominator that does not exist (`F-decision-log` D3) |
| B08 | `redeemed_at` | `Ticket.redeemedAt` | at the door | **N** | **N** | A | **Dropped as a covariate.** Admissible only as a competing-risk exit time once it has occurred, never as a feature (`02-c` §3.4) |
| B09 | `transfer_count_field` | `Ticket.transferCount` | never as stored: a whole-life count | **N** | **N** | **A** | **Dropped as stored.** Recompute from truncated entries, which is C03 |
| B10 | `last_sale_price_field` | `Ticket.lastSalePriceLamports` | never as stored: a whole-life summary | **N** | **N** | **A** | **Dropped as stored.** Recompute, which is C06 |
| B11 | `transfer_restricted` | whether the restriction is enforced on chain now | now, as of D3 | **N** | **N** | **K** | **Dropped as a feature.** It is a consequence of policy plus the ticket's own history, and its stored value is chain state at D3 |

**The pattern in this table is the finding.** Seven of the eleven ticket fields are dropped, and six of
those seven are dropped not because they are unknowable but because the contract delivers a summary over
a life rather than a value at a time. The ledger can reconstruct six of them. That is a statement about
where the engine's work goes: it is a truncation engine over raw rows, not a reader of fields.

### 3.3 Group C — ledger-derived, truncatable (17 features)

Every row here is **H** by construction: the row carries its own `slot` and `occurredAt`, so a value at `t`
exists and is obtainable, provided the truncation happens before any aggregation. The D2 verdict assumes
the truncation is done; the note says what breaks if it is not.

| # | Feature | Definition | Becomes knowable at | D1 | D2 | Vintage | Note |
|---|---|---|---|---|---|---|---|
| C01 | `prior_sale_count_event` | count of `sale` rows for the event, `slot < cut` | each sale | **R** | R | H | The count is the label's numerator; using it for a ticket's own sale is circular |
| C02 | `prior_sale_count_tier` | same, restricted to the tier | each sale | **R** | R | H | The tier is the weakest defensible level of pooling (`02-a` §8.6) |
| C03 | `hop_count_as_of_t` | priced and unpriced custody hops for this ticket, `slot < cut` | each hop | **R** | R | H | Replaces B09. Selection on liquidity (`02-c` §3.6) |
| C04 | `holding_duration` | time since the last hop, and the mean over hops | each hop | **R** | R | H | Needs `slot` ordering, not timestamp ordering (§4 T1) |
| C05 | `repeat_reseller_features` | prior sales by this `fromWallet`, **history truncated at cut** | each of that wallet's sales | **R** | R | H | **The named trap of the programme** (`01-d` §4). A wallet index computed once over all rows is the whole leak, and it looks like a dictionary |
| C06 | `own_markup_path` | this ticket's realised markups up to `slot < cut` | each sale | **R** | R | H | Replaces B10. The only true per-ticket price observation the platform has |
| C07 | `tier_cumulative_volume` | sum of prior sale prices in the tier | each sale | **R** | R | H | A mean of ratios problem (§4 T7 note): sum of prices is not a value |
| C08 | `sales_last_24h` | momentum | each sale | **R** | R | H | The window must be `(t-24h, t]`, not `(t-24h, D3]` |
| C09 | `cap_hit_share_as_of_t` | share of prior sales with `markupBps` at the cap | each sale | **R** | R | H | The best excess-demand signal in the dataset (`02-a` §6.2). Needs the ±1 bps tolerance (§9) |
| C10 | `cap_crossing_date_as_of_t` | the **most recent** cap sale at or before `t`, as `τ` | each cap sale | **R** | R | H | The retrospective form ("the last cap sale") is **N** and is what `02-a` §6.1 C4 literally specifies. §4 T1 |
| C11 | `quantile_log_price_per_tier_day` | lower quantiles of `log(p/face)` by tier and day | each sale | **R** | R | H | Lower quantiles survive truncation, means and upper quantiles do not (`02-a` §6.2) |
| C12 | `sale_hazard_output` | `F(τ)`, `λ`, or the model's own fitted value at `t` | after the model is fitted on data before `t` | **R** | R | H | A model output, so it inherits the model's cut. Two cuts nest (`02-c` §3) |
| C13 | `price_series_truncated` | `EventAnalytics.priceSeries` filtered to **complete** UTC days before `t` | each completed day | **R** | R | **A** | The one aggregate that becomes usable, and only with the current day dropped. Never `<=` |
| C14 | `analytics_scalars` | `avgMarkupBps`, `medianResalePriceLamports`, `resoldShare`, `uniqueHolders`, `totalVolumeLamports`, `saleCount`, `markupDistribution`, `topDestinations` | never as delivered: whole history, no as-of | **N** | **N** | **A** | **Dropped as features.** Legitimate as training labels on **completed** events. Operator Q1 |
| C15 | `resale_stats_block` | `ResaleStats.saleCount`, `avgMarkupBps`, `peakPrice`, `lastPrice`, `totalVolume`, `uniqueWallets` | never as delivered: whole ticket life | **N** | **N** | **A** | **Dropped as features.** Same as C14 at ticket scale |
| C16 | `acquired_on_secondary` | `DestinationRow.acquiredOnSecondary` | as of D3 | **N** | **N** | **A** | **Dropped.** Derived from the current owner. Class E anyway |
| C17 | `destination_region` | `DestinationRow.region` | never: voluntary subsample | **N** | **N** | **A** | **Dropped.** Selected with no denominator (`C-variable-registry` §5.2) |

### 3.4 Group D — absent and decisive (4 features)

| # | Feature | Definition | Becomes knowable at | D1 | D2 | Vintage | Reason dropped |
|---|---|---|---|---|---|---|---|
| D01 | `listing_panel` | `{listPriceLamports, listedAt, delistedAt, delistReason}` | not recorded | **N** | **N** | — | **Absent.** `F-decision-log` D3, the one data request. Without it the probability of sale at a price is unidentifiable |
| D02 | `listing_depth` (V14) | live supply at an ask | not recorded | **N** | **N** | — | **Absent.** `01-d`: worth more than every external variable combined, and unobtainable |
| D03 | `demand_side_record` | bids, offers, views, searches | not recorded | **N** | **N** | — | **Absent.** Every demand statement in the programme rests on assumption (`01-b` §6) |
| D04 | `own_price_elasticity` | `ε_own` on the primary side | only with exogenous price variation | **N** | **N** | — | **Unidentified, not absent.** No price change exists in the record to respond to. `02-d` §3.6's randomised tier-face experiment is the only correction. This is why the primary optimum reports a boundary and not an interior point |

### 3.5 What is knowable at each instant, by feature group

| Group | n | P (D1, and at D2) | R (D2 only) | N (dropped) |
|---|---|---|---|---|
| A event/tier/external | 29 | 22 | 4 | 3 |
| B ticket as stored | 11 | 3 | 1 | 7 |
| C ledger-derived | 17 | 0 | 13 | 4 |
| D absent/decisive | 4 | 0 | 0 | 4 |
| **Total** | **61** | **25** | **18** | **18** |

The three columns are mutually exclusive and exhaustive, so they sum to 61. Checked against the table
row by row, not asserted. The one row whose two verdicts differ is A14, which is **N** at D1 and **R** at
D2; it is counted in the R column because that is the only instant at which it can be used.

- **Knowable at D1: 25.** Every one is also knowable at D2, so there is no D1-only feature.
- **Knowable at D2: 43** (the 25 plus the 18 D2-only).
- **Dropped: 18**, of which **6 are absent from the observation set** (A16, A29, B05, D01, D02, D03),
  **11 carry post-decision information** (A24, B06, B07, B08, B09, B10, B11, C14, C15, C16, C17), and
  **1 is unidentified rather than absent** (D04).

The shape of that count is the honest summary of the data situation: the D1 feature set is almost entirely
the organiser's own policy choices and the calendar, which is why the primary price is better identified
than it looks and the *market* response to it is not identified at all.

### 3.6 The three groups of dropped feature need three different remedies

| Reason | Count | Features | Remedy |
|---|---|---|---|
| Absent from the observation set | 6 | A16, A29, B05, D01, D02, D03 | Data request. In descending value: the listing panel, then depth and the buy side, then on-sale timestamps, then category, then seat coordinates (`01-b` §6, `02-c` §10) |
| Post-decision information | 11 | A24, B06–B11, C14–C17 | Recompute from rows, or drop. Six of the eleven are partially recoverable from the ledger (B06→C06-derived owner, B07 partly via C01, B08→a competing-risk exit, B09→C03, B10→C06) and five are not |
| Unidentified | 1 | D04 | Experiment, not data collection |

---

## 4. The look-ahead traps, each with the test that catches it

All six are the same failure (D3 information entering a `t` decision) arriving by a different route. The
tests are ordered by how cheaply they run: T1's three tests catch most of T2, T5 and T6 as a side effect,
which is why the checklist in §7 is short.

### T1 — Event-end information inside a mid-event feature

**What it is.** A feature computed at `t` over rows that include anything after `t`. The named cases in
this dataset: redemption counts, final sale counts, and any average the API computes over the whole event.
The subtle case, and the reason this is trap one, is a definition that sounds as-of and is not.

**Where it bites.** `C09` if written over the full record. `C10` in the form `02-a` §6.1 C4 gives it: *the
last day on which a sale lands at the cap*. `C05` if the wallet index is built once. `C07`, `C08` with the
window ending at extraction. Any "first sale" feature, because "first" is a fact about the whole series.
Any "did this event sell out" feature. Any "how many times was this ticket resold" that is not truncated.

**The three tests, all mechanical.**

1. **Mandatory cut argument.** Every feature function takes the cut instant as a required parameter with
   no default. A default value (`as_of=None`, `cut=None` meaning "now") is a fail, because in production
   "now" is the only value it will ever get.
2. **Prefix invariance.** For every feature `f` and every cut `t` before the event ends,
   `f(prefix(t)) == f(full record, evaluated at t)`. If a feature's value changes when later rows are
   appended, the feature is reading the future. This is a property test, not an example, and it runs on a
   synthetic ledger where it can be exhaustive.
3. **The future canary.** A fixture whose future is deliberately different: take a completed event, append
   a sale at three times the price one hour after the cut, and assert every feature value at the cut is
   bit-identical. This is the test that catches the definition-level leak that prefix invariance misses,
   because prefix invariance compares two computations of the same function and the canary compares a
   feature against a *changed world*. A feature like "the last cap sale" passes 2 and fails 3.

**What a failure looks like.** The model reports a path that is suspiciously well-calibrated in-sample and
collapses out of sample, or a coefficient on a "market state" variable that is implausibly large. `02-c`
§3.7 predicts the second one exactly: using `transferCount` or `lastSalePriceLamports` as if historical
"will inflate every market-state coefficient".

### T2 — The derived aggregates, whose as-of the contract does not state

**What it is.** `EventAnalytics` and `ResaleStats` are computed by the platform over a window the contract
never names (`API_CONTRACT.md` has no time parameter on any endpoint, MEASURED). The consumer cannot
truncate them, cannot tell whether they are as of the request or as of the last write, and cannot tell when
the payload was built (D3, §2.3). So the honest classification is **A**: not truncatable, therefore not a
feature, therefore a label or an audit object.

**Where it bites.** The natural mistake is not exotic. A builder reads `avgMarkupBps`, which is the most
market-like number in the contract, and uses it as "the market's view now". Every event-level and
ticket-level scalar is exposed to it. `priceSeries` is the near miss: it *looks* truncatable, and is,
except that the current UTC day's bucket is already partly populated and is not marked as partial.

**The tests.**

1. **Forbidden-path check, static.** A list of field paths the engine may not read
   (`EventAnalytics.avgMarkupBps`, `.medianResalePriceLamports`, `.resoldShare`, `.uniqueHolders`,
   `.totalVolumeLamports`, `.saleCount`, `.markupDistribution`, `.topDestinations`, all of `ResaleStats`,
   `Ticket.transferCount`, `Ticket.lastSalePriceLamports`, `Ticket.redeemedAt`, `Ticket.status`,
   `Ticket.ownerWallet`). Any hit outside a test or a label builder fails review. A grep, not a judgement.
2. **Stale-payload test, dynamic.** Feed the engine two payloads identical except that the whole-history
   aggregates have been replaced with different values, and assert the output is byte-identical. If it
   moves, something is reading an aggregate.
3. **Day-boundary test.** For `priceSeries`, assert the filter is strictly `<` the cut's UTC date, and add
   a case where a sale exists earlier on the cut day and must be excluded.

**What a failure looks like.** A feature that is uncannily predictive of the event's final resale volume,
or a sale-probability estimate that tracks the observed sale count. Because these numbers are monotone in
event success, the model learns "hot events are hot".

### T3 — Survivorship: only events that had resales enter a resale-trained model

**What it is.** The target `y = log(p / face)` exists only where a sale happened. Restricting the training
set to events with at least one resale conditions on the event-level outcome being modelled, and the
excluded events are not a random subset: an event with no resales is plausibly the overpriced, the
displaced, the cancelled, or the one whose market moved off-ledger.

**Where it bites, and where it does not.** This is worth stating carefully because `01-b` §5 already
overturned the Phase 0 framing for the *sale-intensity* model:

- The **sale-intensity** model is not subject to event survivorship. Every ticket has an `issue` row and a
  known life, so the risk set is censused (`01-b` §2(a), §5.1). That asymmetry is real and should be
  stated wherever the survivorship problem is named, because conflating the two makes a sound component
  look unsound.
- The **price-path** model is subject to it twice: at event level (events with no resale contribute
  nothing) and at ticket level (repeat-sales pairs come from an already-selected liquid subset, `01-b`
  §4.1 with Gatzlaff & Haurin and Steele & Goy). The bias direction at ticket level is the standard one:
  the index is computed on the properties that traded twice, which are not a random sample.
- The **cold-start prior** is the worst affected, because its whole purpose is to price an event with no
  history, and the events it was fitted on are precisely the ones with history. `02-e` §3.2 handles this
  by pooling at the event level and reporting the between-event variance rather than a point; that is the
  right response and it depends on the excluded events being counted and described, which is the test.

**The tests.**

1. **Count and describe the excluded.** Report the number of events with zero resales and compare their
   observables (city, tier face, cap, sell-through, status, event duration) against the included ones. A
   two-sample comparison on observables is not a proof of no selection, but its absence is proof of
   unexamined selection.
2. **Freeze the population at the cut.** At fold time `t`, an event may enter the study only if the
   information that decides its inclusion was available at `t`. An event whose `startsAt` is after the cut
   cannot be in the study on the grounds that it later had resales. This is survivorship applied to the
   fold construction rather than to the model, and `02-a` §8.5 does not name it.
3. **Report the inclusion rule as code, not prose.** The set of events must be an argument to the fit, not
   the result of a query that filters on resale activity at scoring time.

**What a failure looks like.** The skill score improves when the event count falls. That is the signature:
the model is getting better as the sample gets more selected.

### T4 — The age-period-cohort collinearity, extended to policy

**What it is.** `01-b` §4.2 establishes that within an event, age and calendar time are the same variable
up to a constant, and across events the three-way decomposition has an exact linear dependency, so the
linear price trend is not identified and every point estimate is a normalisation. `02-c` §3.1 finds the
same trap in a second place: `age = (startsAt - issuedAt) - τ`, so with a common issue time per event, age
and time-to-event are affine in each other.

**What this file adds.** A **policy regime dummy is a cohort effect**. The platform's own changes (a cap
introduced or changed, the verified-wallet requirement switched on, the US total-price disclosure rule of
2025-05-12 changing what "face" means, `02-d` §1.1 and `02-e` §2.3 condition 2) are dated events on the
platform's timeline. In a single-platform series with one adoption date, a post-change dummy is perfectly
collinear with calendar drift, so:
- the effect of a policy change cannot be separated from a market trend;
- and, in the other direction, a genuine trend can be absorbed by a regime dummy and read as policy.
This makes the one natural experiment the dataset offers unusable without staggered adoption. It is also
why §5 P2 and P3 are worse than they look: they are not only unstratifiable, they are unidentifiable in
the same way the trend is.

**The tests.**

1. **Rank and condition number of the linear clock block.** Build the design with the linear terms
   (`t`, `τ`, `a`, and every regime dummy) and report the rank and condition number before any coefficient.
   A singular block is a specification error, not a numerical nuisance (`02-c` §4.4 makes the same point
   about the price term).
2. **The two-clock rule, enforced in code.** At most two of `{t, τ, a}` may enter linearly; the third may
   enter only as curvature (buckets, splines, `log(1+τ)`), and the choice must be recorded with the
   estimate. This is a mechanical assertion on the design matrix, not a review comment.
3. **The calendar-shock diagnostic `02-a` §8.5 specifies**: correlation of fold residuals across events
   sharing a calendar week. A large positive correlation means the folds are not independent and the
   prequential estimate is optimistic.
4. **Adoption-date table.** Every policy change carries the date it took effect and whether adoption was
   staggered. If the table has one row, no policy effect is identifiable and the report says so.

**What a failure looks like.** A model with a "post-regulation" dummy whose coefficient is large and whose
removal changes nothing, because the data cannot tell the two apart. The estimate is not wrong; it is
empty.

### T5 — Revision: a sale that is later revoked, and a field that is later redefined

**What it is.** Programme §4.8 names "revised historical data" explicitly. In this contract there are two
distinct revisions and they are both unaddressed:

1. **Row-level revision.** `LedgerEntryKind` includes `revoke` and `TicketStatus` includes `revoked`
   (MEASURED, `lib/types.ts`), and the contract says nothing about what a revoke does to earlier rows:
   whether the sale stays in the ledger, whether the price is voided, whether the ticket is reissued.
   `API_CONTRACT.md` contains no occurrence of "revoke", "amend", "void", "correction" or "backfill"
   (MEASURED). `CONTRACT-MAP.md` §4.3 notes that the build accepts the kind and no row uses it.
2. **Definitional revision.** `02-e` §2.3 condition 2: if `faceValueLamports` means all-in after
   2025-05-12 and pre-fee before it, a pooled series spanning that date manufactures a level shift that
   reads as a market move. That is a revision of the *meaning* of a field, invisible in any row.

**Where it bites.** `C01`, `C11`, `C12` and every count built from `sale` rows. Also the sort order: a
revoked sale that is rewritten reappears at a different `slot`, and a model fitted before the revision
disagrees with one fitted after.

**The tests.**

1. **Append-only assertion.** A two-snapshot canary: capture the ledger for a ticket, re-read it later,
   assert the earlier rows are unchanged in `(slot, kind, priceLamports, fromWallet, toWallet)`. Any
   mutation is a revision and must be modelled, not ignored.
2. **Sane-state assertion.** Assert no ticket has a `sale` after its own `revoke`, and no `redeem` after a
   `revoke`. If the record violates this, the record is not a state machine and the sale count is not a
   count.
3. **Revoke as a competing risk, never a censor.** `02-c` §3.4 already requires this for `redeem`; it
   applies identically to `revoke`. A test that pipes a revoked ticket through the estimator and asserts it
   exits the risk set at the revoke `slot`, rather than being dropped, closes it.
4. **Break test at the definitional date.** If a policy or definition change falls inside the observation
   window, fit with and without a step at that date and report both. If the step absorbs everything, say
   so.

**What a failure looks like.** A feature that is stable in one extraction and unstable across two. Silent,
because nothing in the pipeline is designed to compare extractions.

### T6 — Right-censored exposure on events still open at extraction

**What it is.** Every ticket for a future event is in the ledger and is right-censored at D3. `02-c` §3.4
names the consequence and it is a correctness point, not a bias: those tickets sit in the *exposure* at `τ`
values far from the event where the hazard is near zero, so they dilute the estimate and make the `τ`
support look wider than the evidence. The second consequence is worse: an event whose on-sale has not
happened contributes tickets that have not been offered at all, which is `π` (never-offered) being counted
as survival.

**The tests.**

1. **Report the support.** Every hazard estimate carries the `τ` range it was estimated over and the share
   of total exposure sitting in buckets with zero sales (`02-c` §3.4).
2. **No extrapolation past the support.** An assertion that the prediction grid's `τ` is inside the
   fitted support, or that the call returns a flag when it is not.
3. **Open events excluded from folds whose cut precedes their end**, or included explicitly as censored
   with the cut inside the window. The choice is recorded per fold; silently pooling them is the failure.

**What a failure looks like.** A hazard curve that decays implausibly slowly, and a sell-out probability
that is too low for every event, because a third of the exposure is tickets that were never on sale.

### T7 — note on the target, which is not a look-ahead trap but belongs beside them

The target `y = log(p / face)` is a **censored draw**: `min(m*, c)` under a binding cap, where `c` is known
but `m*` is not. That is not a clock problem; it is §5 P1. It appears here because it changes the meaning of
every residual in §6: a residual of zero on a capped event means "the model predicted the ceiling", which
is a successful prediction of policy and no evidence about value. Any residual diagnostic that pools capped
and uncapped events is uninterpretable, and the stratification in `02-a` §8.8 is the minimum fix.

One further arithmetic point that will otherwise be misread as a level shift: `avgMarkupBps` is a **mean of
per-sale markups**, each over that sale's own ticket face (the contract says so twice). It is therefore an
equal-weighted mean across tiers of different face values, and it is not the markup of the average ticket.
Day-bucketed, that error is small; across a multi-tier event it is large, which is the contract's own
warning. `core/markup.py`'s `mean_int` rounds half away from zero, so a series of daily means does not
reconcile to an event mean, and nothing should attempt to reconcile it.

---

## 5. Policy contamination: which features predict the platform's policy rather than the market

Three channels, each with the feature it contaminates, the direction of the bias in the naive estimator,
and whether it is correctable inside the observation set or only flaggable.

### P1 — The resale cap truncates the price record

**Contaminated features.** Every mean and upper quantile of markup: `C11` at the mean and upper quantiles,
`C14`'s `avgMarkupBps` and `medianResalePriceLamports` and the top `markupDistribution` buckets, the
fitted path slope on capped events, any statement about the *level* of resale value, and the target `y`
itself wherever a sale landed at the ceiling.

**Direction of the bias in the naive estimator.** Unambiguous and downward: `E[min(m*, c)] ≤ E[m*]`, with
the shortfall increasing in the cap-hit share. Three second-order effects all point the same way and one
does not:

- The **slope** is attenuated (flatter than true) because the truncation removes exactly the high side at
  large `τ`, so measured decline is shallower than actual (`02-a` §6.1 C1).
- The **ranking inverts**. Events where the cap binds are the high-demand events, so the hottest events
  look the coolest, which is the inversion `02-a` §6.1 records for the level.
- **Selection on the supply side**: at a binding ceiling the sellers who transact are those with the
  lowest reservation, so the observed sale rate at the cap measures supply response, not demand.
- The counter-effect: a sale at the cap is a *known* ask under Q3 option A, so the cap stratum carries one
  exact price point per event that the uncapped stratum does not.

**Correctable within the observation set, or only flaggable?** Split, and the split is what makes the cap
usable:

| Object | Status | Why |
|---|---|---|
| Lower quantiles below the cap mass | **Correctable** | One-sided truncation from above leaves a low quantile equal to its latent counterpart when the cap mass is below it (Powell 1986, as `02-a` §6.2 applies it) |
| The cap mass and its trajectory in `τ` | **Correctable**, and it is the best feature in the dataset | The mass measures rationed quantity, not value, and does not need the level (`02-a` §6.1 C3) |
| One known price point per capped event (`d*`) | **Correctable** in the as-of form of `C10` | `m*(d*) = c` and `c` is known |
| The median, when the cap mass exceeds 50% | **Not correctable, refuse to report it** | Degenerate; the median is the cap (`02-a` §6.1 C2) |
| The level of value above the cap, and any upper quantile | **Flaggable only** | The censored tail's location is invisible to any estimator that sees only transactions |
| A pooled mean across capped and uncapped events | **Flaggable only, and it should not be computed** | Mixing a truncated and an untruncated distribution |

**And a fourth thing that must be said.** Because the ceiling in money is `p0(1+c)`, the cap-hit share is
itself a function of the organiser's chosen `p0`. So the "best feature in the dataset" is contaminated by
the same policy that contaminates everything else, and it can be used as a cross-event level only
conditioned on `p0`, which is the variable that is not independent. This is recorded as a caveat on
`02-a` §6.3 and it is the bridge to P3.

### P2 — The verified-wallet requirement changes who can buy

**Contaminated features.** Every buyer-side construct. The sale hazard `λ` and everything derived from it
(`C12`, `C01`); the wallet counts (`C14`'s `uniqueHolders`, `C17`'s destinations); the repeat-reseller
features `C05`, because the wallet population observed is conditional on having been admitted; and the
price level, because a restricted pool has a different willingness-to-pay distribution even if the demand
curve is unchanged.

**Direction of the bias in the naive estimator.** **Not a bias. A mixture.** This is the honest statement
and the more useful one. Write `λ_pool = ω λ_verified + (1-ω) λ_unverified` where `ω` is the admitted
share. The recorded hazard is that weighted average, and neither component is identified from the pooled
record. There is no sign to report because there is no single parameter being estimated. The two mechanisms
people expect (a gate shrinks the pool, which lowers price and arrival rate; verification proxies for
seriousness, which raises willingness to pay among those admitted) push in opposite directions and `02-e`
§2.2 records the sign as unknown. The mixture framing is stronger than "unknown sign": it says the pooled
number is not an estimate of either regime, so reporting it as one is a specification error rather than a
weak result.

**Correctable or flaggable?** **Flagged and stratifiable, not correctable.**

- The flag is a known event field at D1 (`A11`), so a stratified estimation is possible in principle.
- Within an event the flag does not vary, so its effect cannot be identified from one event's history at
  all. It needs a cross-event comparison, which is the APC problem again (T4).
- If the requirement is a **platform-wide constant** across the observation window, it is perfectly
  collinear with calendar time and its effect is not identified even in principle. That is Q5, and the
  answer changes whether `A11` is a stratum or a constant.

**Consequence for the build.** `requires_verified_wallet` never enters as a free regressor; it partitions
the sample or it is reported as an unidentifiable constant. And the wallet-history features must be
described as conditional on admission, in the one sentence the interface shows.

### P3 — The organiser's own primary price changes the resale supply

**Contaminated features.** The most structural and the largest set:

- The **target** `y = log(p / face)` has the decision in its denominator. At D1 the engine is choosing a
  quantity that appears in the outcome it is predicting.
- `A15` `primary_sell_through` (V2), `A13`/`A14` status, `C01` prior sale count, `C09` cap mass, `C11`
  quantiles, `C12` hazard. All are downstream of the price the organiser set.
- `A10` as a money ceiling: `p0(1+c)`.
- `resoldShare` and any "resale propensity" statement (`C14`).

**Direction of the bias in the naive estimator.** Two channels with opposite signs on the same coefficient:

1. **Policy channel, positive.** Set a low primary price and sell-through rises *and* the resale markup
   rises, because the primary market is rationing. So a naive regression of markup on sell-through has a
   coefficient that is too positive: the omitted variable is the organiser's own price, and it moves both.
   This is exactly `01-d` §5's "reads its own past decisions back as a law of nature".
2. **Demand channel, also positive within a fixed price.** A genuinely hot event sells through faster and
   clears higher on resale. So the two are confounded and the naive coefficient is a compound of a policy
   function and a demand function, with no way to separate them in-sample.
3. **The level, separately.** At a fixed latent resale value, raising `p0` mechanically lowers `y`, so a
   pooled mean of `y` across events with different `p0` is an average over price points, not over values.
   Relative markups are not invariant to a rescaling of both `p0` and the resale price, because the cap
   and the reference point both move with `p0`.

**Correctable or flaggable?** **Only flaggable, and the reason is structural rather than statistical.**
The engine's recommendation changes `p0`, which changes the cap in money, which changes the truncation,
the sell-through, the cap mass and the target. So **the deployment distribution is not the training
distribution by construction**, and this is not covariate shift from a drifting world: it is a shift the
model causes. No reweighting, no resampling and no extra data fixing the same policy will correct it.
Three consequences for the build:

1. `faceValueLamports` and `price_ladder_ratio` (`A07`, `A08`) may never be free regressors. The first is
   the decision; the second is a choice.
2. Every cross-event comparison is conditioned on a `p0` band, or it is a comparison of policies dressed
   as a comparison of markets.
3. The only correction is exogenous variation: the randomised tier-face experiment in `02-d` §3.6. Until
   it runs, the primary optimum is a boundary statement (§6 of `02-d`), and the report says so in one
   sentence, once, without hedging.

**Also recorded:** if the platform ever logs what the engine recommended and what was accepted, this
becomes a propensity-score problem with a clean fix. It does not today (`02-ai-ml-decision` §4(e): no
logged actions or propensities). That is Q8, and it is the cheapest future-proofing available.

### 5.4 What this means for the numbers the deliverable may print

| May print | May not print |
|---|---|
| A lower quantile of resale markup per tier and horizon, with the cap-hit share beside it | A mean or an upper quantile of markup on a capped event |
| The cap mass and its trajectory as evidence of rationing | The cap mass as evidence about value |
| A sale rate at the prevailing market ask, with both footnotes `02-c` §2.6 requires | A sale probability at an arbitrary ask |
| The primary optimum as a boundary, with the two assumed parameters named | An interior optimum from an elasticity that was not identified |
| A stratified result with the stratum counts | A pooled result across cap, verified-wallet or `p0` strata |
| A band labelled with the number of events behind it | A point estimate and a confidence interval from fewer events than §6.4's floor |

---

## 6. The evaluation protocol that follows

### 6.1 What is being predicted, at which cut

| Target | Decision time | Cut instant | Scored on |
|---|---|---|---|
| `y = log(p/face)` for a sale at `t_j` | D2 | `t_j` itself (prequential), and a grid of forecast instants as a check | MAE in logs, by horizon band, against the martingale `B0` (`02-a` §8.5) |
| Sale indicator within a horizon | D2 | the instant the horizon starts | Log score / Brier, reported as a score, never as calibration (`02-c` §5.2) |
| The primary price recommendation | D1 | `T1(e)` | Realised revenue and sell-through under the recommendation, replayable only where the true `p0` is observed |
| The cold-start band | D1 | `T1(e)` | Interval width and coverage, with the event count stated |

### 6.2 What may cross the cut and what may not

| Object | May cross? | Condition |
|---|---|---|
| Static event facts (dates, venue, city, tier structure, policy flags, fee config) | **Yes** | Dated at creation, before any decision. `A01`–`A12` |
| Fitted parameters | **Yes, from earlier folds only** | The fold's fit data must end strictly before the fold's cut |
| **Hyperparameters** (pooled mean, between-event variance, shrinkage weight) | **Only if frozen per fold** | This is the door `02-a` §8.5 does not name. A pooled mean computed over all events carries post-cut information at the parameter level even when every row is truncated |
| Residual quantiles used as intervals | **Only from out-of-sample folds before the cut** | Read off the fitted sample, they are a fitted quantity and an interval claim in disguise |
| The list of events in the study | **Only if the inclusion criterion was satisfiable at the cut** | T3 test 2 |
| Any `EventAnalytics` or `ResaleStats` scalar | **No** | `A` vintage, not truncatable. §4 T2 |
| Any `Ticket` whole-life field | **No** | B06–B11 |
| A day bucket that is not complete at the cut | **No** | Drop the partial day; filter with `<`, never `<=` |
| The cap in **bps** | **Yes** | It is policy, dated at creation |
| The cap in **money**, at D1 | **Only as a function of the candidate `p0`** | `p0(1+c)`. Treating it as a constant answers the wrong question (`02-a` §7.2) |
| Another ticket's outcome, including a "similar" one | **No** | Includes any neighbour or peer feature computed over the whole sample |
| Wallet history beyond the cut | **No** | T1 |
| A value read from a payload with no timestamp | **No** | Cannot be shown to be a `t` value. §2.3 |

### 6.3 The fold construction

1. **Primary rule: prequential.** At a grid of forecast instants `t`, fit on rows with `slot < cut(t)`
   from all events, score the sales immediately after `t`. This uses the data and enforces the clock,
   which is the boundary that actually matters (`02-a` §8.5(b)).
2. **The check: strict event-level.** For event `e`, fit only on events whose `endsAt` is before `e`'s
   first recorded sale. Wasteful and unimpeachable. Run it to show that the prequential number is not
   bought from shared calendar time. If the two disagree by more than the per-event dispersion, the
   prequential result is the suspect one.
3. **Hyperparameters frozen per fold**, estimated on the fit window only (§6.2).
4. **Population frozen per fold** (§6.2), and the exclusion documented with the observables comparison
   T3 test 1.
5. **Event-level disjointness asserted in code**, not in a comment: `fit_events ∩ test_events == ∅` and,
   for the strict variant, `max(endsAt for fit_events) < min(cut for test_events)`.
6. **Every fold records**: the cut, the number of events in fit and test, the number of sales in each,
   the number and identity of excluded events, the `τ` support of the fit, and the cap-hit share of the
   scored window.

### 6.4 How many events before a holdout is meaningful

These are floors from the estimator's own structure, not power calculations. No variance was measured, so
no power claim is made, and none should be inferred.

| Object | Floor | Where the number comes from |
|---|---|---|
| The between-event variance `τ²` | **about 9 events** | The sample variance of `G` event means has `G-1` df and a relative standard error of `sqrt(2/(G-1))`. A 95% interval on `τ` is narrower than `τ` itself when `1.96·sqrt(2/(G-1))/2 < 0.5`, i.e. `G ≥ 9`. Below that, the interval on the dispersion is wider than the dispersion, and the "shrinkage weight" is a number with no content. [class C, derived] |
| Any holdout at all | **3 events** | A variance needs two groups and a fold needs one held-out event. Below 3, the honest answer is the declared prior band with `basis: "insufficient_events"` |
| An empirical 5%/95% residual interval | **about 20 out-of-sample residuals per horizon band** | With `n` residuals the 5% order statistic is at rank `0.05n`; at `n = 20` it is the first order statistic and the interval is the sample range. Fewer than 20 and the "interval" is a minimum and a maximum, which is a range and must be labelled as one. This is a count of *sales*, not events [class C, derived] |
| A skill score against `B0` | **about 30 sales per horizon band** | The MAE of a fold has its own sampling error; `02-a` §8.5's pre-registered rule compares two MAEs, and a difference smaller than the per-event dispersion of `θ̂` is not a result. Report the difference with the dispersion, never the score alone |
| The stratified `θ̂` by cap-binding stratum (`02-a` §8.8) | **about 5 events per stratum** | Two parameters estimated on two strata; below 5 per stratum the strata are each other's noise |

**The consequence for this programme, stated plainly.** With zero real events, all five floors are unmet
by construction. Every number in the deliverable is either a prior, a band, or a SIM result, and the
evaluation protocol exists so that the first real extraction can be scored without rebuilding anything.

### 6.5 What to report when there are too few events

Not a number, and not a caveated number either: a caveat around a point estimate is read as the point
estimate. Report the following, in this order, and stop:

1. **The count.** `N` events in the population, `M` with any completed post-cut history, `K` sales at or
   before the last cut. This is the only fully honest output available and it is one line.
2. **The floors that are unmet**, by name, from §6.4.
3. **What is being reported instead**: the pooled prior with its declared width, and the word that it is
   declared rather than estimated (`02-e` §5.4's label discipline).
4. **The experiment that would lift each floor**: a completed event with a resale, the listing panel, the
   randomised tier-face arm.
5. **No skill score, no calibration claim, no interval.** An interval from `n = 3` is a fabrication with
   arithmetic on its side.

Worked wording, to be pasted rather than paraphrased:

> The model is not fitted. Three events have completed in the observation window and two have any resale
> activity, so the between-event dispersion cannot be estimated and no out-of-sample score exists. What
> follows is the pooled prior with its width declared, not estimated. It is the number the engine would
> start from on its first day, not a claim about how it performs.

### 6.6 Metrics, and what each one can and cannot show

| Metric | Shows | Does not show |
|---|---|---|
| MAE in logs by horizon band | Whether the path model beats the martingale out of sample | Anything about value, because the target is censored (§4 T7) |
| Skill score `1 - MAE_M/MAE_B0` | Incremental value over the null the literature itself supplies | Generalisation to another platform |
| Empirical residual quantiles per band | The realised dispersion of errors, if out of sample and `n ≥ 20` | A predictive interval under a regime change |
| Log score / Brier on the sale indicator | Whether the sale indicator is sharper than the base rate | Calibration, unless the residuals are out of sample and stratified (`02-c` §5.2) |
| Realised revenue and sell-through under the recommendation | The economic question | Causality: the recommendation was not assigned |
| The excluded-event comparison (T3) | Whether the sample is observably selected | Whether it is selected on the unobservable |
| The calendar-shock correlation (`02-a` §8.5) | Whether folds are independent | Whether a residual trend is real |
| The cap stratification (`02-a` §8.8) | Whether the measured decline is partly truncation | The level above the cap |

### 6.7 The pre-registered rule, with its clock attached

`02-a` §8.5 pre-registers: if the model at `ω = 0` does not beat `B0` out of sample by a margin that
survives the per-event dispersion of `θ̂`, ship `B0`. I add the clock conditions that make the rule
meaningful, because a pre-registration without them is a pre-registration of an unknown test:

- The folds are the ones in §6.3, with hyperparameters and population frozen.
- The comparison is within horizon band, never pooled across bands.
- The margin is compared to the per-event dispersion of `θ̂`, not to a standard error computed as if
  events were independent. Events overlap in time, so they are not.
- If fewer than the §6.4 floors are met, the rule is **not evaluable** and the answer is `B0` by default,
  with the reason stated. A martingale with a measured residual band is a defensible product; a
  pre-registered test that was never run is not.

---

## 7. The build checklist

One line per rule, and for each the thing to look for in the source. Written to be run against the code,
not discussed. Rows 1 to 6 are the ones that catch everything else.

| # | Rule | Look for in the source | Fails when |
|---|---|---|---|
| 1 | The cut is a required argument | `def ...` with `as_of` or `cut` in every feature builder's signature | The parameter has a default, or is read from a clock inside the function |
| 2 | Truncation happens once, at the top | One `if ... slot < cut` (or `<=`) per function, appearing before the first `sum(`, `len(`, `max(`, `mean`, `sorted(` | Any aggregation precedes the filter, or there are two filters |
| 3 | `slot` is the time index, `occurredAt` the fallback | Sort keys `(slot, id)`; a `slot is None` branch that counts and logs | Sorting on `occurredAt` alone; no tie-break; no count of fallbacks |
| 4 | No negative durations | After sorting, an assertion that each delta is `>= 0` | The assertion is missing, or is a `print` |
| 5 | Forbidden field paths are never read | `grep -n` over the engine package, once per name: `avgMarkupBps`, `medianResalePriceLamports`, `resoldShare`, `uniqueHolders`, `totalVolumeLamports`, `markupDistribution`, `topDestinations`, `transferCount`, `lastSalePriceLamports`, `redeemedAt`, `ownerWallet` | Any hit outside a test, a label builder, or a comment |
| 6 | `priceSeries` only from complete days | `p["date"] < cut_date` | `<=`, or no filter, or the filter is applied after a cumulative sum |
| 7 | A future canary exists per feature | A fixture where a post-cut row is appended with a wildly different value, and a per-feature equality assertion | The canary exists for the model but not for the feature functions |
| 8 | Prefix invariance is a property test | A test that loops over cuts and compares `f(prefix(t))` with the post-cut evaluation | It is an example test on one cut |
| 9 | Wallet features come from the truncated ledger | No module-level wallet index, no cached `dict` keyed by wallet built outside a fold | A wallet index built once at import or at boot |
| 10 | No ambient clock anywhere in the engine | A scan for `datetime.now(`, `utcnow(`, `time.time()` in engine code. `tests/test_boundaries.py::test_core_has_no_ambient_clock` already does exactly this, all three patterns, over `ticketpath/core/**/*.py` | The guard's scope does not reach the engine package |
| 11 | The engine never reads a payload aggregate | A test that mutates the aggregate block and asserts identical output | No such test |
| 12 | Fold disjointness is asserted | `assert not (fit_events & test_events)` and `max(fit_endsAt) < min(test_cut)` | Asserted in prose, or only for the prequential variant |
| 13 | Hyperparameters are frozen per fold | The pooling fit is called in the fit phase and its outputs passed in; no call inside the scoring loop | The between-event variance is computed from all events |
| 14 | The event population is an argument | `def fit(events, ...)`; the scoring path does not query for "events with sales" | The population is discovered by a filter at scoring time |
| 15 | The 50% cap-mass guard | `if cap_hit_share > 0.5:` and no central path statistic beyond it | A median is reported anyway |
| 16 | The cap-hit test has a rounding tolerance | `abs(markupBps - capBps) <= 1` and an explicit `capBps is None` branch | Exact equality, which misses on-the-ceiling sales on faces that do not divide evenly |
| 17 | The cap stratum is never pooled with the interior | Separate `θ̂` per stratum, or an interaction, and the stratum counts printed with the estimate | One `θ̂` across both |
| 18 | Redemption and revoke are competing risks | A cause-specific loop over `{sale, transfer, redeem, revoke}`; no `if redeemed: drop` | Any exit is treated as censoring |
| 19 | Face value is never a free regressor | No coefficient on `faceValueLamports` or the ladder ratio in the path model; used as a normaliser or an offset | It appears on the right-hand side |
| 20 | Policy flags partition, they do not regress | `requires_verified_wallet` and `resale_cap_bps` used as strata or as DGP parameters | Either is a covariate |
| 21 | Fees come from configuration | No fee literal in the code; a missing fee raises | A default of zero |
| 22 | Every output carries its provenance | `asOf`, fold id, event and sale counts, `τ` support, cap-hit share, `modelVersion` | Any output without them |
| 23 | Below the floor is a distinct code path | A named branch returning a band and `basis: "insufficient_events"` | The band is returned by the same path as a point estimate |
| 24 | The band widens as `N` falls | A test asserting monotone width across the `02-a` §8.6 ladder | Width is constant, or narrows |
| 25 | No fixture number reaches a claim | `tests/test_boundaries.py`'s `lib/mock` guard, plus a check that no fixture path is imported by the engine | Fixtures used to demonstrate accuracy rather than a code path |
| 26 | The revision canary | A test appending a `revoke` row after a sale, asserting earlier feature values are unchanged and the ticket exits as a competing risk | No revision test at all |

Two notes for the reviewer. Row 5 is a grep and should be run as one, in CI, over the engine package with
an allowlist file for test paths. Row 10's guard already exists but covers `ticketpath/core/`; extending
its scope is a one-line change to `tests/test_boundaries.py`'s directory walk, and it is the cheapest
temporal assertion in the repository.

---

## 8. Questions this raises for the operator

Each with what it blocks. Questions already open in `F-decision-log` or `02-e` §10 are marked and not
restated at length.

**Q1 (new). Is `EventAnalytics` computed as of a supplied instant, or as of the request?**
The contract has no time parameter on any endpoint and no payload timestamp (MEASURED). Until answered,
every aggregate is treated as whole-history.
*Blocks:* whether any aggregate can be a live feature (§3 C13–C15); T2's whole treatment; and 13 of the 17
D2-only features, which would move from "must be recomputed from raw rows" to "readable". If the answer is
"as of the request", the engine gets materially cheaper and one entire class of leak disappears. If it is
"as of the last write", the analytics surface is a label store and the interface must say so.

**Q2 (new). Is the ledger append-only? Does `revoke` void prior sale rows, and are rows ever rewritten or
backfilled?**
`API_CONTRACT.md` contains no occurrence of revoke, amend, void, correction or backfill (MEASURED); the
kind exists in the type and no row uses it.
*Blocks:* T5 in full, and the assumption behind prefix invariance (if rows can be rewritten, a value at `t`
is not stable and no backtest is reproducible). Also blocks the label for any revoked ticket.

**Q3 (new). Does `priceSeries` include the current, incomplete UTC day?**
The contract says day-bucketed in UTC and does not say whether a partial day appears.
*Blocks:* the safe filter in §7 row 6. If partial days appear, the filter must be `<`; if the series only
ever contains complete days, the same filter is still safe and costs one day of information.

**Q4 (re-raises `F-decision-log` Q3). Is the cap enforced on the ask or at settlement?**
*Blocks:* whether a sale at the ceiling is a known ask (§5 P1's one correctable anchor) or only a lower
bound, and therefore whether `delistReason: cap_blocked` in D3's four-field request is even observable.

**Q5 (new). Is `requiresVerifiedWallet` a per-event choice or a platform-wide constant, and did it change
during the observation window?**
*Blocks:* §5 P2's status as stratifiable (per-event variation) or wholly unidentifiable (a constant
collinear with calendar time). Also decides whether the wallet-history features can be described as
unconditional.
*Blocks in code:* whether §7 row 20 is a stratum or a constant.

**Q6 (re-raises `02-e` Q3, sharpened). Will status transitions and the on-sale instant be timestamped, and
does `issuedCount` update continuously?**
*Blocks:* D1's cut instant, which this document has to derive from the first `issue` row (§2.1); `A16`,
which is dropped for absence; and sell-through *velocity*, which turns the demand bracket into a curve.
Also: if `issuedCount` updates continuously and is logged, `A15` becomes usable at D2 without the vintage
problem, and that is the single highest-value D2 feature in the contract.

**Q7 (re-raises `02-e` Q4 and `F-decision-log` D4). What is the fee stack, and is `faceValueLamports` the
all-in price?**
*Blocks:* the objective's level; and, temporally, the definitional break at 2025-05-12, which is T5's
revision case. A pooled series spanning that date manufactures a level shift.

**Q8 (new, and cheap). Will the platform log what the engine recommended and what the organizer did with
it?**
*Blocks:* any future correction of §5 P3. Without logged recommendations and acceptances the engine can
never learn the effect of its own advice, so the contamination is permanent rather than merely present.
This is the same gap `02-ai-ml-decision` §4(e) uses to rule out an agent loop, and it is worth recording
here because the temporal argument for it is independent: a model that changes its own inputs needs a
record of the changes.

---

## 9. Where this disagrees with prior records

Recorded, not resolved, per `records/README.md`.

**D-1. `CONTRACT-MAP.md` §6 understates what is derivable.** The table lists "event-level cap *binding*
evidence (sales at the cap, rationed demand)" as absent. It is derivable exactly: a sale is at the ceiling
when `markupBps == resalePriceCapBps`, and both are bps over the same ticket's face, which is what
`01-b` §5.3 and `02-a` §6.1 C3/C4 both rely on. What is genuinely absent is any *attempt* that failed at
the cap, which is D3's `delistReason`. Add the tolerance: `core/markup.py` rounds half away from zero, so
an on-the-ceiling sale can read `cap ± 1` bps. This is a narrowing of an absence, not a new capability.

**D-2. `02-a` §8.5 names two leakage boundaries; there are four.** Its across-events and within-event
boundaries are right and insufficient. The hyperparameter clock and the population clock sit outside both
and leak even when every row is truncated (§6.2). The fix is one line each in the fold loop, and without
them the prequential number is optimistic in a way the strict event-level check will not reveal, because
the strict check shares the same hyperparameters.

**D-3. `02-a` §6.1 C4's definition of the crossing date is a look-ahead as written.** "The last day on
which a sale lands at the cap" requires the whole series. The as-of restatement is admissible and should
replace it in the record. The economics of C4 survive intact.

**D-4. `01-b` §4.2's APC argument needs one addition for a single-platform dataset.** It treats cohort as
event start date. A platform policy regime is also a cohort, and in a series with one adoption date it is
perfectly collinear with calendar drift. So the natural experiment that policy variation appears to offer
is available only with staggered adoption. This strengthens `01-b`'s conclusion and changes what Phase 3
can claim from a cap change.

**D-5. `02-c` §3.7's leakage list is right and one item is under-stated.** It says `transferCount` and
`lastSalePriceLamports` are current snapshots and using them as historical "will inflate every market-state
coefficient". Agreed, and the mechanism generalises: the same is true of `Ticket.status`,
`Ticket.ownerWallet` and `Ticket.transferRestricted`, so five ticket fields are the future, not two. §3
Group B drops all five.

**D-6. `02-d` §1.1's finding that a dynamic policy is not implementable has a temporal consequence nobody
has drawn.** It means D2 cannot act, so the feedback loop in §5 P3 is currently inert and D2's numbers are
descriptive. If a price-mutation endpoint is ever added, every D2 number becomes an action and P3 becomes
live on the same day. Worth a row in `F-decision-log` so the coupling is not discovered later.

---

## 10. What is unvalidated, and what would falsify this

**Unvalidated throughout.** No real ledger exists (`00-data-situation.md` §1, §2), so every test in §4 and
§7 is a specification of a check, not an observation of a failure. The leakage audit says what could go
wrong and how it would be caught; it does not say that any of it has. Label: **UNVALIDATED**, with the
tests as the validation design.

**Two specific things are not testable yet.**

1. **T4's collinearity is not measurable without overlapping asks.** Identifiability of anything that
   separates a time effect from a policy effect needs dispersion among simultaneously live listings at
   different prices (`02-c` §4.4 makes the same point for the price term). That requires the listing panel
   or a real ledger. Until then the rank and condition number can be computed on the design, but not the
   variance that would make the estimate informative.
2. **P1's cap correction cannot be exercised on the fixtures at all.** `00-data-situation.md` §2 records
   that no generated sale lands exactly on a cap. So the cap-hit test, the ±1 bps tolerance and the 50%
   guard can be unit-tested on constructed rows and never on a fixture event. That is fine and must be
   said, or a future reader will assume the cap path is exercised.

**What would falsify the conclusions here.**

- **A payload timestamp and an as-of parameter would not falsify T2, it would delete it.** If Q1 comes
  back "as of the request", §3 C14 and C15 change verdict, the count of dropped features falls from 18 to
  16 and the D2 count rises from 43 to 45, row 5 of the checklist loses most of its list, and row 11
  becomes a test that the as-of is passed through. I would update the table rather than defend it.
- **A contract with no `revoke` semantics and an append-only guarantee** would close T5's first half and
  leave the definitional half, which is the one that actually bites.
- **If the between-event dispersion turns out to be small** relative to within-event variation, the
  cold-start prior stops being the hard case and §6.4's floors relax. That is measurable at about ten
  completed events and should be measured before any further work on the pooling.
- **If the engine's recommendations are never acted on**, P3 is a theoretical problem and `faceValue` can
  be treated as a fixed stratum rather than a decision. That is a product question, not a data one.

---

## 11. Registry rows this file implies

Not edited here, per the pass's file boundary.

- **A (research ledger):** one row, P3.B "temporal correctness of every feature and the leakage audit",
  this file, class C, complete first pass.
- **B (mathematical knowledge base):** the prefix-invariance criterion; the future-canary construction;
  the four-clock crossing table §6.2; the dispersion floor derivation in §6.4; the mixture framing of a
  gated arrival process (§5 P2); the two-clock identifiability rule (§4 T4).
- **C (variable registry):** eleven admissions with a verdict and a vintage, which the registry currently
  carries only as prose notes: `prior_sale_count_tier`, `hop_count_as_of_t`, `holding_duration`,
  `own_markup_path`, `tier_cumulative_volume`, `sales_last_24h`, `cap_hit_share_as_of_t`,
  `cap_crossing_date_as_of_t`, `quantile_log_price_per_tier_day`, `sale_hazard_output`,
  `price_series_complete_days`. Also twelve downgrades to **N** with the reason: `Ticket.status`,
  `Ticket.ownerWallet`, `Ticket.transferRestricted` join the four already noted in §5.2 of the registry.
- **D (model registry):** no new model. One constraint row on the path model: two strata by cap binding,
  a frozen hyperparameter clock, and a `p0` band on every cross-event comparison.
- **F (decision log):** D-2, D-3, D-6 above as corrections; Q1, Q2, Q5, Q8 as questions; and, if accepted,
  a decision row that no derived aggregate may be a live feature until Q1 is answered.

---

## Sources

Primary sources cited here for claims that belong to other findings, so this file can be read alone.

- Absence of an as-of in the contract: `API_CONTRACT.md` and `lib/types.ts` in
  `../ticketing-frontend`, read in full this pass. No `asOf`, `at`, `from` or `to` parameter on
  any endpoint; no payload timestamp. `records/CONTRACT-MAP.md` §6 records the omission; §7.2 records that
  the added `dataSource` block carries no instant.
- Absence of price mutation: `API_CONTRACT.md` endpoint list, nine endpoints, seven reads and two
  wallet-verification POSTs. Confirms `02-d` §1.1.
- Absence of revoke semantics: `API_CONTRACT.md`, no occurrence of revoke, amend, void, correction or
  backfill. `lib/types.ts` defines `revoke` as a ledger kind and `revoked` as a ticket status.
- Markup rounding: `ticketpath/core/markup.py`, `_round_half_away_from_zero`, half away from zero on an
  integer fraction. Confirms `records/CONTRACT-MAP.md` §1.
- The one existing temporal guard: `tests/test_boundaries.py`, `test_core_has_no_ambient_clock`, which
  forbids `datetime.now(` and `utcnow(` in `ticketpath/core/`.
- [Powell 1986] Powell, J. L. (1986). Censored regression quantiles. *Journal of Econometrics* 32(1),
  143–155. https://doi.org/10.1016/0304-4076(86)90016-3: the lower-quantile result this file relies on
  in §5 P1, and the reason `02-a` §6.2's table survives truncation.
- [Mason et al. 1973] Mason, K. O., Mason, W. M., Winsborough, H. H., & Poole, W. K. (1973). Some
  methodological issues in cohort analysis of archival data. *American Sociological Review* 38(2),
  242–258. https://doi.org/10.2307/2094398: the age-period-cohort linear dependency, per `01-b` §4.2.
- ~~[Luo 2019] Luo, L. (2019). Bayesian age-period-cohort analysis. *Annual Review of Sociology* 45,
  109–132.~~ **[CORRECTION 2026-11-07T14:00Z, R2-22 — dead: Crossref for this DOI gives Fosse, E. & Winship, C.
  (2019), "Analyzing Age-Period-Cohort Data: A Review and Critique", *Annual Review of Sociology* 45:467–492.
  The author, the title and the pages are wrong; the volume and DOI are right. The proposition it is cited for
  (bounds rather than point estimates) is unaffected. See the CORRECTION at the end of this file.]**
  https://doi.org/10.1146/annurev-soc-073018-022616: bounds rather than point estimates.
- [Fine & Gray 1999] Fine, J. P., & Gray, R. J. (1999). A proportional hazards model for the
  subdistribution of a competing risk. *JASA* 94(446), 496–509.
  https://doi.org/10.1080/01621459.1999.10474144: redemption and revocation as competing events, not
  censoring, per `02-c` §3.4.
- [Gatzlaff & Haurin 1997] Gatzlaff, D. H., & Haurin, D. R. (1997). Sample selection bias and repeat-sales
  index estimates. *Journal of Real Estate Finance and Economics* 14(1), 33–50.
  https://doi.org/10.1023/A:1007763816289: the repeat-sales survivorship this file's T3 applies at event
  level.
- [Bulow & Klemperer 2012] Bulow, J., & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer
  surplus. *Journal of Political Economy* 120(1), 160–186. https://doi.org/10.1086/665416: a binding
  ceiling clears by speed and rationing, so the observed hazard at the cap is arrival intensity.
- [Sweeting 2012] Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence
  from secondary markets for Major League Baseball tickets. *Journal of Political Economy* 120(6),
  1133–1172. https://doi.org/10.1086/669254: the declining option value of holding, which is the
  mechanism behind `time_to_event` and the reason it must be interacted.
- [Lagakos 1979] Lagakos, S. W. (1979). General right censoring and its impact on the analysis of survival
  data. *Biometrics* 35(1), 139–156. https://doi.org/10.2307/2529941: informative observation times, per
  `01-b` §2(a).

Internal records cited: `records/00-data-situation.md` Gaps 1–4 and §2; `records/F-decision-log.md` D1–D5,
Q1–Q3; `records/C-variable-registry.md` §0 (the P/R/P+R/N verdict vocabulary this file reuses), V1, V2,
V5, §5.2, §7 C-1 to C-6; `records/CONTRACT-MAP.md` §1, §4.4, §4.6, §6, §7.2; findings 01-b §2, §4.1, §4.2,
§5, §6; 01-d §1, §4, §5; 02-a §6.1, §6.2, §7.1, §7.2, §8.5, §8.6, §8.8; 02-c §2.5, §2.6, §3.1, §3.4,
§3.7, §3.9, §4.4, §4.5, §5.2; 02-d §1.1, §3.6, §8; 02-e §2.1, §2.2, §2.3, §2.4, §5.4, §10;
02-ai-ml-decision §4(e).

---

## CORRECTION (2026-11-07T11:28Z) — the [Luo 2019] reference entry

Appended by the corrections pass after `records/findings/00-verification-round1.md` §4 and §13. Nothing above
is deleted.

**Withdrawn entry:**

> "- [Luo 2019] Luo, L. (2019). Bayesian age-period-cohort analysis. *Annual Review of Sociology* 45,
>   109–132. https://doi.org/10.1146/annurev-soc-073018-022616: bounds rather than point estimates."

**What is true.** A Crossref query for that DOI on 2026-11-07 returns **Fosse, E. & Winship, C. (2019),
"Analyzing Age-Period-Cohort Data: A Review and Critique"**, *Annual Review of Sociology* **45, 467–492**. So
the author, the title and the page range in the entry above are all wrong; the volume and the DOI are right.

**Corrected reading.** Wherever the text cites "Luo 2019" or "Luo", read **Fosse & Winship (2019)**, with the
title and pages above. The proposition it is cited for in §9 (bounds rather than point estimates, because the
linear component of an APC decomposition is a normalisation) is unaffected and is what the paper argues.

**Two related points.** (i) The `[Mason et al. 1973]` entry in this file already has the correct third author,
Winsborough, so the verification pass's statement that both of `01-b`'s author errors recur here is true of
the Fosse & Winship entry only. (ii) The `00-verification-round1.md` §13 verdict on this file, "4/4 confirmed"
with "the same two author-name errors inherited from `01-b`", is therefore half right: one entry is wrong in
three fields, the other is correct.

# Phase 6 — The validation protocol, the SIM study specification and the failure-mode registry

**Status:** complete (first pass). **Written:** 2026-11-07T11:52Z UTC.
**Agent:** Phase 6 research agent (`p6-validation`).
**Scope:** `RESEARCH-PROGRAM.md` §3 Phase 6 in full; §4.6, §4.7, §4.8; the whole of §4.3 as it decides what
may be called a result. It answers four questions: what can be validated at all, with what protocol, with
what experiment, and how the work is to be attacked before it is trusted. It extends
`03-b-temporal-correctness.md` §6 (which is the evaluation protocol for the *clock*) and does not restate it.

**Depends on:** `RESEARCH-PROGRAM.md` §3 Phase 6, §4; `AGENTS.md`; `records/README.md` (the A–E, SIM,
UNVALIDATED vocabulary); `records/00-data-situation.md` (§1 toolchain, §2 fixtures, §4 Gaps 1–4, §5);
`records/findings/01-b-identifiability.md`; `02-c-sale-hazard.md` §5 (calibration with no validation set);
`02-b-cap-truncation.md`; `03-b-temporal-correctness.md` §2, §6, §7; `00-adversarial-review-phase1.md` §3
and §6; `00-verification-round1.md`; `CORRECTIONS-APPLIED.md`; `records/D-model-registry.md` (role
vocabulary, M01–M56); `records/BUILD-SPEC-NIGHT.md` §3.7, §4; `records/CONTRACT-CONFORMANCE.md`;
the working tree at `ticketpath/` and `tests/`.

**The rule this file works under, stated once.** No number here is a result. Every experiment is marked
**PLANNED** with the pass condition written down *before* it runs, which is the only thing that makes a
pass condition mean anything. Sixteen of the last pass's defects were corrected this evening
(`CORRECTIONS-APPLIED.md`), and those sixteen are the evidence base for §4: this is not a hypothetical
failure-mode registry. It is a description of how this particular programme has already gone wrong.

**Nothing in this file was executed.** The one exception is the measurement of the existing test suite and
of pure-Python fit costs, both marked MEASURED with the command that produced them. `lib/mock/` was not
read or used. No file outside this one was written.

---

## 1. What can be validated at all

### 1.1 The blunt statement, first

There is no real ledger. There is no backend, no database, no deployed program, and the frontend's fixture
data is synthetic and barred from estimation (`00-data-situation.md` §1, §2). Therefore:

> **Nothing about ticket prices, ticket sales, ticket values, sale probabilities, or primary-price optima
> can be validated today.** Not approximately, not provisionally, not "indicatively". The words "validated",
> "verified", "accuracy", "coverage", "calibration" and "out of sample" have no referent on this machine for
> any quantity the engine exists to produce.

That is not a failure of this pass. It is the position stated in `00-data-situation.md` §5.1 and it is the
premise the whole programme has been written under. The useful question is not "can we validate the engine"
but "what are the *two* things that are testable now, and what exactly does each of them buy".

Two things, and they are different in kind.

| | What it is | What it can establish | What it can never establish |
|---|---|---|---|
| **A. Estimator properties under stated generative assumptions** | A simulation study: generate data from a process whose parameters are known, run the estimator, check whether it returns them | That the estimator is *internally coherent*: that it recovers a parameter it was designed to recover, that a declared interval attains its declared coverage, that it degrades in a predicted way as data thin out, that it behaves as the bound binds | Anything about ticket markets. A SIM result is a statement conditional on the assumptions, and the assumptions are the experiment's own definition, not a claim about the world |
| **B. Internal correctness** | Contract conformance, arithmetic invariants, refusal behaviour, label discipline | That the engine is what it says it is: that it honours `lib/types.ts`, that its identities hold exactly, that it refuses where it claims to refuse instead of inventing a number, and that the sentence it prints matches the object it computed | Whether the number, once printed, is any good |

**A is legitimate and is labelled SIM.** `00-data-situation.md` §5.2 already authorises it and bounds it:
simulation is admissible *for estimator properties*, never as validation of the engine against ticket
markets, and a simulated accuracy number may not be quoted as if it measured performance on tickets. §3
below is the specification.

**B is the thing the test suite should be judged on, and it is testable now, today, with no data at all.**
This is the important sentence in the file: *a test suite that is green on B is a claim about engineering,
and the programme's own standard for "done" (R20, R57) is that B is what "the tests pass" is allowed to
mean.* Anything the suite says about A is a claim about methodology. Nothing the suite says bears on whether
the engine prices tickets well, and the suite must never be described as though it did.

### 1.2 What follows for the programme's claims

Three consequences, and they are not negotiable at review.

1. **No result in this programme can be class A from our own data** (`00-data-situation.md` §5.1). Every
   quantitative conclusion is B (cited from a related market), C (true by construction), SIM, or
   UNVALIDATED. Class A exists in this programme only as a citation of published ticket research, and the
   transfer from that research to this platform is class B or D and must be labelled where it is used.
2. **Every estimator in the SHIP set carries UNVALIDATED** and the model registry already says so in every
   row (`D-model-registry.md` §2). The registry's own sentence is the standard: no model in it is
   validated, none may be marked validated, and no accuracy, lift, coverage or error number appears in it.
3. **The four data gaps decide which claims are even candidates for later validation**
   (`00-data-situation.md` §4). This is worth tabulating because it is what makes the protocol in §2
   partial rather than general:

| Gap | Claim it makes unvalidatable | Can a future extraction fix it? |
|---|---|---|
| **1. No listing exposure** | `P(sale \| price, exposure, t)`. There is no denominator, so any sale-probability claim is unfalsifiable | Only with the four-field listing panel. Until then the engine must refuse (`not_identified`) and the refusal is correct, not timid |
| **2. Cap is a policy truncation** | The level of value above the ceiling, and the ranking of events by value where the cap binds | No. The tail is not in the record and no extraction of *this* record recovers it. This is the one gap where the answer is permanently "a bound, not a point" |
| **3. No seat coordinates** | Anything within-event and below tier | Yes, if the platform's internal ledger carries section/row/seat and the wire contract is widened |
| **4. No fee field** | Net economic value; the primary optimum's level; the sign of any cap correction | Yes, and it is a parameter the operator can supply today. Until it is supplied the engine withholds net revenue (`no_fee_model`) |

So of the engine's four advertised outputs, one (the value band) is validatable in the future on two of
three regimes, one (the horizon path) is validatable as a forecast coefficient, one (the sale probability at
a price) is **not validatable at all** without new data collection, and one (the primary price) is
validatable only as a boundary statement plus a sell-through arithmetic check.

### 1.3 Path A, stated so it cannot be overclaimed

The programme permits simulation. What simulation buys, precisely:

- **A recovery check.** Does an estimator designed to recover μ return μ when the data are generated with μ
  and the estimator's own assumptions? If not, the estimator is wrong, and the error is in the code or in
  the algebra, not in the market. This is a real and useful finding and it is available today.
- **A coverage check.** Does an interval declared at 90% contain the truth 90% of the time *under the stated
  DGP*? If not, the width formula is wrong. Also available today, and it is the only path by which the
  declared band can be defended at all before data exists.
- **A degradation check.** Does the estimator get worse, in the predicted way, as the event count falls to
  the cold-start floor? This is the property that makes the cold-start story (02-e) a design rather than an
  assertion.
- **A binding-constraint check.** Does the estimator do the *declared* thing when the cap binds: refuse the
  mean, refuse the upper quantile, return a floor, and widen the band as `N` falls? This is the property
  that makes §P1 of `03-b` a mechanism instead of a paragraph.

What simulation cannot buy, stated in one line so a reviewer can quote it: **a SIM study cannot fail for the
reason the engine will actually fail.** It can only fail for reasons the engine's author thought of, because
the author wrote the DGP. That is why §5 exists and why the reviewer of a SIM study must not have written it.

### 1.4 Path B, specified: the four classes of internal correctness

This is what the suite is judged on. Each class has a different failure signature and a different source of
truth, and a suite that only does one of them is not a validation of the other three.

**(a) Contract conformance.** The source of truth is `../ticketing-frontend/lib/types.ts` and
`API_CONTRACT.md`, read as a specification of a server that does not exist. The test must not import the
backend's models, because a test that imports the thing it tests proves only that the code agrees with
itself. **Status MEASURED at the snapshot in §1.5:** `tests/test_contract_conformance.py`, 22 tests, all
passing in 0.688 s, encoding the contract in declarative per-type tables and checking both structure (field
presence, JSON type, nullability, integer lamports, base58 32-byte decode, ISO-8601 UTC) and semantics (markup
against the ticket's own tier face, `transferCount` excluding issue and redeem, event totals equal to the sum
of tiers, `markupDistribution` bucket bounds in order, cursor pagination walking once, detail routes 404 not
200-with-null, and the Ed25519 verification message rebuilt from the contract text and signed for real). This
is the one class that is genuinely caught today, and it is worth saying why: the encoder is independent, so
the test can fail.

**(b) Arithmetic invariants.** Identities that are true by definition and must hold to the lamport, with no
tolerance except where rounding is specified. The list the build already commits to, from
`BUILD-SPEC-NIGHT.md` §4.7's right-hand column: `ceiling = face × (1 + cap/10000)` exactly; `share =
atCeiling / sales`; `lamports = face × exp(mean(log(price/face)))` monotone in the marks; band width
`= 2zτ` in logs and monotone in τ; `required sell-through = face × s / candidate`; markup against *that
ticket's own tier face*; `atCeiling` as `|markupBps − capBps| ≤ 1` with `capBps is None` as its own branch;
`priceSeries` day mean as the mean of that day's per-sale markups, never the event-level derivation. **Status:
partially caught.** `tests/test_markup.py`, `tests/store_arithmetic.py` and `tests/test_event_analytics.py`
cover the contract-arithmetic of markup, buckets, totals and per-day series. Nothing covers the five modules
that compute the pricing claims, per §1.5.

**(c) Refusal behaviour.** The engine has thirteen named refusal codes (`BUILD-SPEC-NIGHT.md` §4.8) and the
whole honesty thesis of the product is that a refusal is a *distinct code path returning a band and a reason*,
not a caveated number. This is a property with a sharp test: for every code, the payload must carry the code,
the label id, and a `null` where a number would have been, and must not carry the number. It is testable with
zero data, it is testable on an empty store, and **it is the one class where a test proves something a reader
actually cares about**. Status: the codes exist in `guidance.py` and `primary_optimum.py`
(`not_identified`, `no_demand_response`, `no_fee_model`, `insufficient_events` all present, MEASURED by grep);
no test asserts any of them, because no test imports the modules that produce them.

**(d) Label discipline.** Every static sentence the console prints comes from `core/labels.py` by id, so that
`core` returns ids and never sentences. Two lists: `MANDATORY`/`ALLOWED` (what may be said) and `BANNED`
(what must never be said), the second being the X-list derived from `00-adversarial-review-phase1.md` §6.
The intended check is `contains_banned(text)` scanned over the page and the payload. **Status at the snapshot:
the guard is dead code.** `contains_banned` is defined in `labels.py` and called from nowhere in the
repository (MEASURED: `grep -rn contains_banned --include=*.py .` returns only its definition). A guard that
nothing invokes cannot fail, and tonight it does not.

**(e) The boundary rules.** No third-party imports; no socket outside `server.py`; nothing in the package
mentions `lib/mock`; no ambient clock in `core`. These are the cheapest assertions in the repository and
they are the ones that keep the build inside D2. **Status: red, and instructively so.** See §1.5.

### 1.5 The suite as it stands, measured, and what it says

**Superseded within minutes: read the CORRECTION block at the end of this file for the 11:50Z measurement, then
come back here for the judgement rule, which is unchanged.** The tree was being written while this pass ran,
and six test files landed at 11:47–11:50Z.

Taken at **2026-11-07T11:47Z** against a tree that was being written by another session while this pass ran
(`ticketpath/console/page.py` appeared at 11:44, three minutes before the snapshot). The digest of
`tests/*.py` plus the five claim-bearing core modules plus `labels.py` and `page.py` at the moment of
measurement is `a0513affac4e2577d6d86d4f331d8945200fb42ff7c3e102318e932914be4f15`. Any verdict below is
against that set and not against whatever landed afterwards.

```
python3 -m unittest discover -s tests -t .     → Ran 149 tests in 8.336s, FAILED (failures=5)
python3 -m unittest tests.test_contract_conformance → Ran 22 tests, OK
python3 -m unittest tests.test_boundaries          → Ran 13 tests, FAILED (failures=5)
```

Three facts, in order of how much they matter.

**1. The five failures are all one method, failing on false positives.**
`test_no_third_party_imports` compares each import root against a hand-written `ALLOWED_ROOTS` set and does
not contain `math`, `re` or `html`. The five failures are `units.py` importing `html`, `labels.py` importing
`re`, and `price_features.py`, `path_model.py` and `value_band.py` importing `math`. All three are standard
library. So the dependency gate is not catching a dependency; it is catching its own stale allowlist, and the
cheapest way to make CI green is to add three names to a set, which is exactly the habit that destroys a
gate. That is failure mode **F21** in §4 and it is live tonight, not hypothetical.

**2. The five modules that make the pricing claims have no tests at all.**
`grep -l` for each module name across `tests/*.py` returns nothing for `price_features`, `value_band`,
`path_model`, `intensity` and `primary_optimum`. Those five files are 1,183 of the 2,501 lines in
`ticketpath/core` (**47%**), and they are precisely the ones that compute the value band, the path, the
intensity, the boundary rule and the features. The tested part of `core` is markup arithmetic, base58,
Ed25519, the verification message, the event analytics series and the record accessors. So the suite is
currently a strong test of **B(a) and B(b)-as-it-applies-to-the-contract** and a complete blank on **B(c),
and on every arithmetic invariant that belongs to the claims rather than to the wire**.

**3. The judgement rule for the suite, stated so it can be applied rather than argued about.**
A suite is adequate when all four hold, and I would refuse to call this one adequate until they do:

| # | Test | How it is checked | Today |
|---|---|---|---|
| J1 | **It can fail.** Mutation check: corrupt an operator, an index or a comparison in each module under test and confirm a test goes red | Run one mutation per module, count survivors. A module with 0 tests survives every mutation by construction | No mutation run exists. The five untested modules would survive any mutation |
| J2 | **It encodes an independent source of truth.** For contract tests, the contract; for arithmetic, the definition; never an import of the implementation | Read the imports of each test file | Contract conformance: yes. The rest: mostly yes, and `test_boundaries` imports the package on purpose, which is correct for a boundary test |
| J3 | **Every module that makes a claim has a test that would fail if the claim were false.** Not coverage; a specific failing scenario per claim | One row per claim in §1.4(b), each naming the module and the wrong value it would produce | Fails for the five modules |
| J4 | **Red is actionable and green is meaningful.** A red suite must point at a defect in the engine, not at the harness's own bookkeeping | Triage each failure to "engine" or "harness" | 5/5 of tonight's failures are harness |

That table is the answer to "what should the test suite be judged on". It is deliberately not a coverage
percentage: coverage tells you a line was executed by a test, not that any test would fail if the line were
wrong, and `labels.py` is the standing proof (342 lines, one dead guard, no consumer).

---

## 2. The protocol for when data exists

Written now, while it is uncontaminated by any result, so that the first real extraction can be scored
without rebuilding the harness. `03-b` §6.1–§6.7 already fixes the clock side of this: three decision
instants (D1, D2, D3), the cut derivation `T1(e) = min{occurredAt : kind = "issue", ticket ∈ e}`, the
crossing table, the fold construction, the count floors and the pre-registered rule. This section extends
that and does not repeat it. What is added here is: the **event boundary as the fold unit**, the eight
objects `03-b`'s crossing table does not list, the **resolution floors** that decide when a metric means
anything, the four **metrics** the programme actually names, the four **baselines** an estimator must beat,
and the eight **ablations**.

### 2.1 The cut instant, at the event boundary

One fold is one **event boundary**, and the cut is a single instant `t_k` per fold. The reason to fold at
the event boundary rather than at a calendar date is that the product's decision is per event: the organiser
prices event `e`, and the moment that happened is `T1(e)`. A calendar cut mixes events whose decisions are
in the future with events whose decisions are in the past, and the mixture is what makes a backtest look
better than the product ("most of my training events had already finished").

```
For fold k:
    t_k          = the cut instant. Either a D1 fold (t_k = T1(e_k)) or a D2 grid point
                   (T1(e_k) < t_k < startsAt(e_k)).
    FIT(k)       = rows from every event whose last informative instant <= t_k
    SCORE(k)     = every settled sale of e_k with T1(e_k) <= t < t_k?  no: with t >= t_k
    POP(k)       = events whose inclusion was decidable at t_k, as an explicit argument
```

Five rules that make `t_k` a real cut rather than a decorated parameter:

1. **`t_k` is a value, not a query.** It is written into the fold record, printed with every score, and
   passed to every feature function, which has no default. A feature function whose cut parameter defaults
   to "now" is a fail (`03-b` §7 row 1).
2. **One filter, at the top.** Truncation happens once, before the first `sum`, `len`, `max` or `sort`,
   and the code path is the same one production uses. A second filter inside an aggregation is a defect even
   when it is correct, because the next edit will not be.
3. **The cut is on the row's own clock.** Sort on `(slot, id)` where slots exist and on
   `(occurredAt, slot, id)` where they do not, and count the null-slot rows so the fallback is visible. The
   build does this today (`price_features._truncate`, MEASURED) and it is the right shape: a store with no
   slots must say so rather than pretend.
4. **A cut inside an event is legitimate and must be stated.** D2 folds cut mid-event, so the same event
   appears in both `FIT` and `SCORE`. That is not leakage, because the fit is truncated; but it is why the
   event-level disjointness assertion in `03-b` §6.3 applies to the *strict* variant only, and the fold
   record must say which variant produced the number.
5. **The cut has a resolution limit.** `occurredAt` is ISO-8601 at unspecified granularity, so two rows can
   share an instant. The fold record carries the count of rows at exactly `t_k` so a later reader can see
   whether a tie was resolved by the sort key or by luck.

### 2.2 What may cross the cut

`03-b` §6.2 lists fifteen objects. These eight are not on that list and each has bitten someone in this
programme's own records or in the adjacent literature.

| Object | May cross? | Why it is on this list |
|---|---|---|
| **A re-extraction of the same rows** | **Only if bit-identical in `(slot, kind, price, from, to)`** | `revoke` exists in the type and no semantics exist in the contract (`03-b` T5). If rows can be rewritten, no backtest is reproducible and the fold record must carry the extraction digest. The snapshot discipline of `00-verification-round1.md` (a locked digest, re-checked byte-identical) is the model, and it was vindicated: the tree was being written throughout that pass |
| **A revised macro series** (CPI, unemployment, confidence) | **Only the vintage as published at `t_k`** | `03-b` A27. The revised series is D3 information and the coefficient silently absorbs the revision |
| **A venue-capacity or city-population figure** | **Only if its release date precedes `t_k`** | `03-b` A19. Nobody checks this one, and it is the classic "external variable that was measured once, later" |
| **A competing-event or tour-routing set** | **Only the set as announced at `t_k`** | `03-b` A20, A21. The eventual set is the future, and added tour dates are the canonical version of the leak |
| **A weather forecast** | **Only inside the forecast horizon at `t_k`**, as a code condition | `03-b` A23. A 10-day forecast used at τ = 60 days is a hindsight value wearing a forecast's name |
| **A "similar event" or neighbour feature** | **No** | `03-b` §6.2 already bans another ticket's outcome; the generalisation is that any k-NN, peer or comparables feature computed over the whole sample is a whole-sample statistic and must be recomputed inside the fold. The registry rejects M11 for exactly this |
| **The organiser's chosen price, as a right-hand-side variable** | **No, and this is the hardest one** | `03-b` §5 P3. `faceValueLamports` is the decision at D1 and the denominator of the target afterwards. It may be a normaliser, a stratum, or the base of the cap; it may never be a free regressor |
| **The engine's own prior recommendation for this event** | **Yes, and it must be logged** | This is the only object that can cross the cut *and* is created by the engine. Without a record of what was recommended and what was accepted, `03-b` Q8 stands: the engine changes its own inputs and can never learn that it did |

The last row is the one to keep: a leakage protocol that only asks "was this knowable" is incomplete for a
system whose output is an input. The fold record must therefore contain the recommendation history, not
just the data history.

### 2.3 The metric set, with pass conditions attached now

Four metrics, because the programme names four in Phase 6 ("forecasting accuracy, calibration,
sell-through, realized revenue, and downside risk", which is five names for four objects, since two of them are
the same thing at event level).
Each gets a definition, a pass condition, and one line on what it cannot show. The pass conditions are
**PLANNED**; none has been run.

**M1. Calibration of the value band** (the programme's "calibration").
Definition: the share of out-of-sample scored sales whose realised `log(price/face)` falls inside the band
the engine printed *at the instant before that sale*. That is coverage of a predictive interval, and it is
the only calibration statement available for a continuous target.
Pass condition (PLANNED): empirical coverage within `[0.87, 0.93]` for a declared 90% band, **per horizon
band and per regime, never pooled across regimes**. Pooling a truncated and an untruncated distribution is
not a smaller sample, it is an uninterpretable one (`03-b` T7).
Cannot show: whether the band is *right* on the capped-and-binding regime, where there is no upper end to
cover. On that regime M1 is replaced by M3.

**M2. Coverage of the band, as a function of N** (the programme's "calibration" at the cold-start end).
Definition: M1 computed at each event count in the ladder `J = 1, 3, 5, 9, 20`. The point is the *shape*,
not the level: the band is declared to widen as `N` falls (`03-b` §7 row 24), so coverage should be roughly
flat in `J` while width rises. A band whose coverage collapses as `J` falls is a declared width that is
too narrow at the bottom of the ladder, and the cold-start story is then false.
Pass condition (PLANNED): coverage in `[0.87, 0.93]` at every `J ≥ 1`, with width strictly decreasing in
`J`. Both halves must hold; a flat width or flat coverage fails.
Cannot show: whether the between-event variance is right. That is `03-b`'s `τ²` and it needs the 9-event
floor.

**M3. The boundary rule's realised sell-through, and its floor violations.**
Two distinct checks, and the second one is the honest one.
(a) *The floor statement.* On a `capped and binding` event the engine prints "at least `floor`" where
`floor = face × (1 + c)` exactly. The falsifier is a realised resale mark below that floor. It is
**nearly tautological within the extraction that produced it** (the record was truncated at the same
ceiling), so it can only fail through a moved cap, a changed fee basis, a different tier's ceiling, or a
compliance channel that settles below the cap. Stated properly: the floor claim is *testable across
extractions and across events*, not inside one. Pass condition (PLANNED): zero floor violations in a
forward extraction at the same cap, and the count printed either way.
(b) *The required-sell-through arithmetic.* The recommendation prints "required sell-through at candidate
price = `face × s / candidate`". The observable is `issuedCount / totalSupply` at the cut. This is
arithmetic and it is checkable to the lamport today. But: **realised sell-through cannot be attributed to
the recommendation unless the recommendation was assigned**, and it is not assigned (no price-mutation
endpoint, `03-b` §2.2; no recommendation log, Q8). So the pass condition is (PLANNED): the arithmetic
identity holds exactly, and the *economic* claim is reported as descriptive until an adoption log exists.
Cannot show: causality, under any amount of data, without an adoption record or the randomised tier-face
experiment of `02-d` §3.6.

**M4. Downside.** Define the loss as realised net revenue minus the revenue implied by the engine's
recommendation at the realised sell-through, and report the 5% CVaR of that loss over out-of-sample events.
Two honesty conditions: the empirical 5% tail average needs **at least five observations in the tail**
before it is a tail average rather than its own worst point, which is `n ≥ 100` out-of-sample outcomes; and
the loss is defined against a counterfactual that was not run, so it must be reported as a *shortfall
against the printed recommendation*, not as "value lost".
Pass condition (PLANNED): CVaR reported with its tail count and its `n`, and the mean-CVaR optimiser (M47)
must not be preferred to the plain optimum (M46) unless its CVaR is lower at the same mean with the
difference larger than the per-event dispersion. Otherwise the risk term is decoration and ships off.
Cannot show: a coherent risk preference. `α = 5%` and `λ` are the operator's parameters, not estimates.

**The resolution floors, derived here because the programme names no number and §6.4 of `03-b` stops at the
dispersion floors.** These are floors on *how many observations a metric needs before the metric is
distinguishable from noise*, not power calculations. No variance was measured, so no power claim is made.

| Metric | Floor | Derivation |
|---|---|---|
| M1 coverage | **about 139 out-of-sample sales per horizon band** | The standard error of a coverage estimate at nominal `p = 0.9` is `sqrt(p(1-p)/n)`. For a 95% interval on coverage to be narrower than ±0.05: `1.96 × sqrt(0.09/n) ≤ 0.05` → `n ≥ 1.96² × 0.09 / 0.0025 = 138.3`. At 20 sales the interval is ±0.13, which cannot separate a 90% band from an 80% one. [class C, derived] |
| M2 coverage by `J` | **139 sales at the smallest `J` in the ladder**, so the `J = 1` cell is the binding one | Same arithmetic. This is the number that makes the cold-start study expensive and it is worth knowing before writing it |
| M3 floor violations | **one event with a forward extraction** | A violation count of zero has no interval; the floor is a single well-observed event, and the metric is a count, not a rate |
| M4 CVaR at 5% | **about 100 out-of-sample outcomes**, so the tail contains ≥ 5 | `0.05n ≥ 5`. At `n = 20` the "tail average" is the single worst observation, which is a maximum wearing a risk label. [class C, derived] |
| Any holdout at all, and the between-event dispersion | **3 events, and about 9 for `τ²`** | `03-b` §6.4, not restated |
| A skill score against a baseline | **about 30 sales per band** | `03-b` §6.4, not restated |

### 2.4 The baselines every model must beat

Four, named by the programme and already in the model registry as rejected rows. That is not a
contradiction: they are rejected as *products* and mandatory as *floors*. The rule is the same for all four
and it is pre-registered: **if the model does not beat the baseline out of sample by a margin that survives
the per-event dispersion of the statistic, the baseline ships** (`03-b` §6.7).

| ID | Baseline | Definition, exactly | Registry row | What it is a floor against |
|---|---|---|---|---|
| **B0** | Face value | `predicted resale = face`, i.e. `log(p/face) = 0` | M01 | The claim that the market pays a premium at all. It is also the null the ticket literature supplies, which is the strongest reason it is first |
| **B1** | Population mean | `predicted log(p/face) = ȳ` over the pooled fit events | M03 | The claim that any covariate adds anything. A model that loses to a single pooled mean has no features |
| **B2** | Last observed markup | `predicted log(p/face) = ` the most recent mark for that tier at or before `t` | M18 (martingale) | The claim that the model knows the level better than the last trade. This is the binding baseline: `02-a` §8.5 pre-registers shipping B0, meaning the random walk, if the fitted path does not beat it. B2 is that object |
| **B3** | Fixed markup rule | `predicted resale = face × k` for `k` fixed in advance (declared, not fitted) | M02 | The claim that the model's *time variation* is worth anything. If a constant multiple of face is as good as a path, the path is noise with parameters |

Two conditions that make the comparison real rather than ceremonial.

1. **The baseline is evaluated on the same folds, with the same cut and the same population.** A baseline
   scored on all events against a model scored on events with a resale is not a comparison, it is a
   selection (`03-b` T3).
2. **The baseline's parameters are frozen per fold too, and if the baseline has no parameters it must be
   said.** `B0`, `B1` and `B3` have a fitted or declared constant; `B2` has none. A baseline with an
   unfair advantage is as misleading as a model with one, and the advantage in this dataset is the pooled
   mean: `B1` computed over all events carries post-cut information at the parameter level
   (`03-b` §6.2, the hyperparameter clock). So `B1`'s mean must be the fit-window mean, or `B1` is not a
   baseline but a cheat.

### 2.5 The ablation list

The programme names eight. The protocol for all eight is identical and it is stated once, then the table
gives what removal should look like so the reader can tell a null result from a bug.

**Protocol (PLANNED, for each item).** Remove the component from the full model, keep the folds, the cut,
the population, the hyperparameter clock and the metric identical, and score. Report the score difference
with the per-event dispersion of the difference. Pre-registered reading: **a component that does not improve
the out-of-sample score by more than that dispersion is removed from the build**, and removing it is a
result, not a defeat. The one exception is a component whose purpose is a *refusal* rather than a number
(the cap guard, the cold-start branch, the fee gate): those are not scored, they are tested for being
switched on, because a guard that pays for itself in points is not a guard.

| # | Ablation | What is removed | Predicted signature if the component is real | The reading that means it is not |
|---|---|---|---|---|
| A1 | Historical prices | All marks before the cut; the model sees only event and tier facts | MAE rises against `B2` most on `τ` far from the event | No rise: the marks are noise, and `B2` was never a baseline worth beating |
| A2 | Resale inventory | `hop_count_as_of_t`, `sales_last_24h`, tier cumulative volume (`03-b` C03, C07, C08) | The intensity and the path degrade, the level barely moves | Nothing moves: supply features are decorative on this record |
| A3 | Primary inventory | `primary_sell_through`, `issued_count`, tier supply (`03-b` A06, A15) | The D2 estimates degrade, D1 not at all | D1 moves: it cannot, sell-through does not exist at D1, so the run leaked |
| A4 | External variables | Venue capacity/type, city size, calendar structure (`03-b` A17–A22) | Cold-start band narrows less than the pooled band; small lift at `J` small | A large lift: check the release dates first (A19, A27), because a leaked external variable always looks valuable |
| A5 | Interaction features | `time_to_event × tier`, `τ × cap-stratum` | The path's slope estimate changes sign or size | Nothing: the interactions were never identified (the APC collinearity, `03-b` T4) |
| A6 | Demand estimation | The primary bracket (M24, Tobit) | The recommendation's band widens; the boundary statement is unchanged | The point estimate moves: it cannot, it is a boundary by construction |
| A7 | Uncertainty estimation | The band, the declared width, the `insufficient_events` branch | Coverage collapses while MAE is unchanged | Coverage unchanged: the band was decorative, which is a finding about the band |
| A8 | Dynamic optimization | The time-varying path; `B2` (random walk) ships instead | The score difference is the whole case for the path model | `B2` wins: ship the martingale, as `02-a` §8.5 pre-registers |

A5 deserves one sentence of warning because it is the ablation most likely to be misread. On this record the
three clocks are affine in each other within an event (`03-b` T4), so an interaction in time is partly
collinear with the level, and its removal will *always* look harmful in sample because the in-sample fit is
absorbing the collinearity. The only admissible reading of A5 is out of sample against `B2`.

### 2.6 What a fold prints, so the report is not a number with a story attached

One block per fold, and the deliverable prints all of them rather than a mean of means:

```
fold  event  variant(prequential|strict)  cut  fitEvents  testEvents  fitSales  testSales
      excludedEvents(list, with observables)  tauSupport[min,max]  capHitShare  regimeCounts
      MAE(log)  B0  B1  B2  B3  skill-vs-B2  perEventDispersion
      coverage  nScored  floorViolations  cvar5  tailCount
      floorsUnmet(list)  refusalsFired(count by code)
```

The block is the unit of reporting because the floors are per-fold and a pooled number hides which floor was
unmet. `03-b` §6.5's wording for the too-few-events case is the template for the whole report: state the
count, name the unmet floors, state what is being reported instead, name the experiment that would lift each
floor, and print no skill score, no calibration claim and no interval.

---

## 3. The SIM study specification

**PLANNED. Not one line of this has been run.** `D-model-registry.md` states the fact plainly: no
simulation study exists anywhere in this repository, and not one row in the registry is labelled SIM.

### 3.1 The rules the study works under

1. **One generative model per estimator, and the generative model is written as the estimator's own
   assumptions.** This is the discipline that makes SIM informative rather than circular: if the estimator
   assumes a censored normal with a known bound, the DGP is a normal truncated at a known bound. The study
   then answers "does this estimator do what it claims *when its assumptions hold*", which is the only
   question it can answer. The assumptions are the experiment's definition and must be printed with the
   result, not summarised as "realistic".
2. **The pass condition is decided before the run and written into the harness as an assertion**, so the
   run cannot be reinterpreted afterwards. That is the whole difference between a study and a screenshot.
3. **Every number is labelled SIM and every output line carries the DGP's parameters.** No simulated
   accuracy figure may be printed in the same table as a real one, and none may be quoted as a claim about
   tickets (`00-data-situation.md` §5.2).
4. **The harness is judged on its ability to fail.** A SIM study that has never produced a failure is
   evidence about the author's DGP, not about the estimator. Hence G7 below, which is the harness testing
   itself.
5. **No fixture is used.** `fixtures/synthetic_store.json` is generated to exercise the API and the page; a
   study that used it would be measuring the fixture generator. The SIM harness generates its own data from
   an explicit seed and prints the seed.
6. **Standard library only** (D2). No numpy, no scipy. Every fit below is a small closed-form or Newton
   update over a few hundred rows, which is why the runtime in §3.4 is seconds and not hours.

### 3.2 The studies

`n` = replications per grid cell. All grids are the shipped grid unless the row says otherwise. "Property"
is what the study checks; "Pass" is the condition asserted in the harness.

---

**G1 · Value-level recovery, for the censored hedonic estimator (M05).**
DGP: `y_i = μ + x_i β + ε_i`, `ε ~ N(0, σ²)`; observed `min(y_i, c_e)` with `c_e` known per event; `x` is
one tier indicator and one time-to-event term. The estimator is the censored regression with a known,
event-varying bound, fitted by EM.
Grid (6 cells): `σ ∈ {0.15, 0.40}` × cap-hit share `s ∈ {0.0, 0.25, 0.6}`, selected so the cells differ in
how much of the distribution is truncated. `n = 200` per cell, `β` fixed, 400 marks per replication.
Property: parameter recovery and interval coverage for `μ`, in the untruncated cells and in the truncated
ones, reported separately.
Pass (PLANNED): `|μ̂ − μ| < 0.05` in relative terms in the two `s = 0` cells and empirical coverage of the
90% interval in `[0.87, 0.93]` in every cell. In the `s = 0.6` cells there is an extra clause: the estimator
must show a **visible downward bias** and the study must report it, because reporting the bias is the
correct behaviour of a truncated estimator and suppressing it would be the defect. So the pass condition for
`s = 0.6` is not "unbiased", it is "biased in the predicted direction, and the bias is inside the width the
declared band reports".

**G2 · Cold-start band coverage and degradation (M07, M38).**
DGP: two-level normal, `μ_e ~ N(μ, τ²)`, marks within event `~ N(μ_e, σ²)`; a target event with no marks.
Estimator: normal-normal partial pooling with a *declared* `τ` below the five-event threshold, which is what
the build does (`value_band.py`, MEASURED).
Grid (5 cells): `J ∈ {1, 3, 5, 9, 20}` events observed; 300 replications each.
Property: coverage of the declared band for a new event's mean, and the width as a function of `J`.
Pass (PLANNED): coverage in `[0.87, 0.93]` at every `J`, and width strictly decreasing in `J`, and the
`insufficient_events` branch firing for `J < 3` with the code, not the band. A study where coverage holds at
`J = 20` and collapses at `J = 1` fails, and its failure is the useful output: it says the declared `τ` is
too small at the bottom, which is a change to one constant.

**G3 · Behaviour as the cap binds (M08, and the regime dispatch).**
DGP: latent `m*` with a known distribution, observed `min(m*, c)`, plus a leakage probability `q` that a
capped trade is settled off-platform (so the observed cap mass is the demand behind it, less `q`).
Grid (4 cells): `s ∈ {0.0, 0.1, 0.4, 0.7}` where `s` is the share of latent values above `c`; 250
replications each; `q ∈ {0, 0.2}` as a nuisance factor, declared not estimated.
Property: the regime classification and what the engine is allowed to print on each regime.
Pass (PLANNED), all four assertions, no tolerance: (i) `s = 0` produces `regime = capped_no_mass_point`
**and** the A20 sentence is attached; (ii) `s > 0` with at least one observed sale at the ceiling produces
`capped_and_binding` in **100%** of replications; (iii) on that regime `hi` is `None` and the median is never
computed, in 100% of replications; (iv) the reported floor is `≤` every latent value above the cap in 100%
of replications, which is the definition of a floor. Note what is deliberately absent: there is no recovery
target, because no correction is computable (`02-b` §1.2). The study checks *discipline*, not accuracy, and
that is the honest form.

**G4 · Intensity recovery with competing risks and separation (M30).**
DGP: piecewise-constant cause-specific hazards over `K` τ-buckets, with exposure per ticket-day, exit causes
`{sale, transfer, redeem, revoke}` and right-censoring at the event end. Estimator: Newton on the Poisson
representation with an exposure offset and a ridge/Firth guard.
Grid (3 cells): `K ∈ {4, 8, 12}`, with one cell deliberately containing a bucket whose true hazard is near
zero, so separation is exercised rather than assumed; 300 replications each.
Property: recovery of `log λ_k`, the cause-specific split, and the guard's behaviour.
Pass (PLANNED): `|log λ̂_k − log λ_k| ≤ 2 ×` delta-method SE in ≥ 95% of replications for buckets with
exposure; the condition number printed every fit and `< 1e10` in 100% of fits; the guarded bucket's estimate
finite in 100% of fits (a diverging `α_k` is a failure of the guard, and the guard exists precisely to
prevent it); and the reported exposure shares summing to 1 to within 1e-12.

**G5 · The path guard and the deadline-convex path (M17, M18).**
DGP: a path with a known curvature parameter `θ` and known noise; marks placed on a grid of `τ` with a
controlled spread in days.
Grid (4 cells): mark spread `∈ {2, 5, 12, 30}` days × 250 replications; `n_marks = 12` fixed, so the spread
is the only thing that changes.
Property: the guard is a function of the data, not of the mood, and the fitted path beats the flat line when
the spread supports it.
Pass (PLANNED): refusal rate **1.0** when spread `< 5` days and **0.0** when spread `≥ 12` days (the two
middle cells are reported, not asserted); when fitted, out-of-sample MAE against `B2` `< 1` with the
per-event dispersion of the ratio printed; and the flat line always printed alongside, labelled, on every
path where the fit refused.

**G6 · Optimiser identities and the fee wedge (M46, M47).**
DGP: none, or rather an exhaustive grid of inputs, because the optimiser is deterministic. 200 random
configurations of `{cap, fee (per-unit | ad valorem | absent), floor, sell-through}` drawn from a stated
grid.
Property: the boundary is returned where the demand response is absent; the fee wedge moves the optimum in
the correct direction; a missing fee withholds net revenue.
Pass (PLANNED), exact, zero tolerance: `no_demand_response` in 100% of configurations; `recommended ==
ceiling` whenever a sale sits at the ceiling; `hi is None` on that regime; `netRevenue is None` whenever the
fee is absent, in 100% of those configurations; the recommendation monotone non-increasing in an ad-valorem
fee and non-increasing in a per-unit fee; the required-sell-through identity exact to the lamport.

**G7 · The harness tests itself: a leakage canary (this is the important one).**
DGP: a clean panel, plus a deliberately leaked feature that peeks at the whole record (the retrospective
cap-crossing date of `03-b` T1, or a wallet index built once over all rows).
Property: **the prequential harness must detect a leak.** Score the same estimator twice, once with the clean
feature set and once with the leak injected, on identical folds.
Grid: 2 arms × 20 replications × 20 folds = 800 fits.
Pass (PLANNED): the leak arm shows a **strictly better** score in 100% of replications, with the difference
larger than the per-event dispersion; the clean arm shows no improvement. If the leak is *not* detected, the
harness is broken and **every score it has ever produced is void**. That is the pass condition, and it is
the reason this study runs before any other score is believed. A protocol that cannot detect a known leak is
not a protocol.

**G8 · The band is a band, not a confidence interval (the label-versus-object check).**
DGP: the G1 process, with the declared band treated first as an interval for the mean and second as a
predictive interval for the next sale.
Property: which object the printed band actually covers, measured rather than argued.
Grid: 1 cell, 1,000 replications.
Pass (PLANNED): the study prints two coverage numbers, `coverage_of_mean` and `coverage_of_next_sale`. The
pass condition is not a threshold on either; it is that **the sentence in `labels.py` matches the object the
higher coverage corresponds to**, and the measurement is reported either way. If the band covers the mean at
90% but the page's sentence reads as though it covers the next sale, the sentence changes. That is the
cheapest possible version of failure mode F03 and it is the only one that can be settled before data exists.

### 3.3 What the study must never produce

- A number described as "accuracy", "expected error on tickets", "expected lift", or "calibration on this
  platform". All four are category errors and all four have appeared in adjacent programmes.
- A pooled pass across studies. Each study's pass condition is asserted separately in the harness so a
  summary cannot launder a failure.
- A grid cell dropped because it failed. A failed cell is the result.
- A DGP tuned until the estimator passes. The grid is fixed before the first run and the seed is printed;
  if a cell fails, the failure is written into the record and the estimator or its constant changes with a
  dated note.

### 3.4 Runtime, with the arithmetic shown

Under D2 the study is pure Python. The per-fit costs below were **MEASURED** on this machine at
2026-11-07T11:50Z by a throwaway timing probe (`python3 -` heredoc, random numbers only, no fixture, no
ticket data, nothing written to disk), on stand-ins of the same shape as the real fits: 400 rows and 60 EM
iterations for the censored hedonic, a 40-cell repeat-sales normal-equation solve on 200 pairs, an 8-cell
Newton on 25 iterations, and a 400-row panel build.

| Operation | Measured |
|---|---|
| Censored hedonic EM, 400 marks, 60 iterations | 1.41 ms |
| Repeat-sales 40-cell solve, 200 pairs | 0.84 ms |
| Piecewise-exponential Newton, 8 cells, 25 iterations | 0.02 ms |
| Panel build, 400 rows plus one pass | 0.24 ms |

A realistic replication is a panel build of a few thousand rows (about 2 ms extrapolating from 0.24 ms at
400 rows), one fit, and a scoring pass: call it **5 ms**, with a 2× headroom factor for the panels and
iteration counts in the grid.

| Study | Fits | Per fit | Time |
|---|---|---|---|
| G1 value recovery | 6 cells × 200 = 1,200 | 6 ms | 7 s |
| G2 cold-start coverage | 5 × 300 = 1,500 | 5 ms | 8 s |
| G3 cap binding | 4 × 2 × 250 = 2,000 | 3 ms | 6 s |
| G4 intensity recovery | 3 × 300 = 900 | 4 ms | 4 s |
| G5 path guard | 4 × 250 = 1,000 | 6 ms | 6 s |
| G6 optimiser identities | 300 configs | 1 ms | 0.3 s |
| G7 leakage canary | 2 × 20 × 20 = 800 | 3 ms | 2.5 s |
| G8 band versus predictive interval | 1,000 | 3 ms | 3 s |
| **Total** | **≈ 8,700 fits** | | **≈ 37 s** |

**Expected wall clock: about 37 s of compute, under 90 s with interpreter start-up and reporting. The hard
cap for the run is 300 s, with a 60 s timeout per study**, and the harness writes each study's result to its
own file as it completes so a killed study does not lose the others. If a study exceeds its timeout that is
a defect in the harness's iteration bounds, not a reason to relax the grid.

That budget is the reason this study is worth writing tonight rather than after data: it is a coffee break,
and it converts eight paragraphs of design into eight assertions.

---

## 4. The failure-mode registry

### 4.1 How to read it

One row per way the engine, or the record of the engine, can be wrong. Three columns carry the weight:
**Symptom** is what a reviewer would actually see (not the mechanism, the observable), **Test** is the check
that would catch it, and **Caught** is whether that check exists in the tree at the snapshot in §1.5.
"Caught" is deliberately strict: **YES** means a test exists today that fails when the defect is present;
**PARTIAL** means the mechanism that prevents it exists but nothing asserts it, or the guard exists and its
scope misses this case, or the guard exists and nothing invokes it; **NO** means nothing.

The tree was being written throughout this pass, so the column is a statement about
`a0513affac4e…` at 11:47Z and not about the tree a reader is holding.

### 4.2 The registry

**Group I: the record lies about itself.** These are the modes that make the *documents* false while the
code is fine. Every one of them happened tonight; the sixteen corrections in `CORRECTIONS-APPLIED.md` are
the evidence.

| # | Failure mode | Symptom a reviewer sees | Test that catches it | Caught |
|---|---|---|---|---|
| F01 | **A `lib/mock` number enters a finding.** A fixture count is read as a market fact, or a fixture distribution supports a modelling choice | A number in a findings file that traces to `lib/mock/` or to `fixtures/`, and that a conclusion leans on. Tonight: "90 of 128 fixture tickets ever sell", which is a row count, used as the argument for a cure component | Two checks, both needed: (i) the existing `test_no_package_file_reaches_for_the_frontend_fixtures` grep over the package - present and passing; (ii) a **prose lint** over `records/**.md` for the strings `lib/mock`, `90 of 128`, `synthetic_store` outside a sentence that labels the number as a fixture, plus a requirement that any number in a findings file carries a source or a `[FIXTURE]` badge. (ii) does not exist | **PARTIAL** - (i) yes, (ii) no. The defect occurred and was caught by a human verifier, twice |
| F02 | **A retrospective feature that looks as-of.** "The last day a sale landed at the cap", "the first sale", "did this event sell out", a wallet index built once | A feature whose value changes when later rows are appended; an implausible "market state" coefficient; a path that is well calibrated in sample and collapses out of sample | Prefix invariance as a **property** test (`f(prefix(t)) == f(full, at t)` for every cut) plus a **future canary** (append a sale at 3× one hour after the cut; every feature value at the cut must be bit-identical). `03-b` §4 T1. Neither exists | **PARTIAL** - `price_features` requires `as_of` with no default and applies one filter at the top (MEASURED), which is the mechanism; no property test, no canary |
| F03 | **A band described as a confidence interval.** "90% confident the value is between…" over a declared width that is a prior, not a sampling interval | The page's sentence is narrower than the object. A reader concludes a coverage guarantee where there is a declared width | The X-list (`labels.py`) bans "confidence: high", "calibrated to", "accurate to ±" and the A-label states "declared width … not a confidence interval"; the check is `contains_banned` over the page and payload. **MEASURED: `contains_banned` is called from nowhere in the repository** | **PARTIAL** - the phrases and the sentence exist; the guard is dead code, so tonight it cannot fail |
| F04 | **A cap-truncated mean reported as value.** A mean or an upper quantile computed on an event whose record is truncated at the ceiling | A level printed on a `capped and binding` event; a band with an upper end on that regime; a band that inverts the ranking (the hottest events reading coolest) | The regime dispatch refuses the mean, the median and the upper quantile on that regime, and `hi is None` (`value_band.py`, `02-b` §3). Test: for every capped-and-binding fixture and every constructed case, assert `level is None`, `hi is None`, `median is None`, and the A19 sentence attached | **PARTIAL** - the dispatch exists and looks right; no test imports `value_band` |
| F05 | **A cold-start point estimate presented as a measurement.** An event with no resales gets a number and a reassuring band | A price with no `n`, or an `n` of 0 with a point estimate beside it, or a band that does not widen as `N` falls | The `no_resale` branch returns the prior band with `n_events = 0`, the `insufficient_events` code, and no price. Test: assert the branch fires, assert `price is None`, assert width monotone in `J`, assert the A17 sentence is attached | **PARTIAL** - the branch exists; no test |
| F06 | **A route drifts from the contract.** A field renamed, a null dropped instead of present, a lamport serialised as a float, a detail route answering 200-with-null | A frontend that breaks on one endpoint, or a payload that type-checks by accident | `tests/test_contract_conformance.py`: the contract encoded independently as per-type tables, both structure and semantics, every route addressed over a real socket | **YES** - 22 tests, passing in 0.688 s at the snapshot. The one mode genuinely caught today |
| F07 | **A synthetic label that never reaches the screen.** The badge exists in the payload and in `labels.py`, the page renders something else, and the human sees an unlabelled number | A screenshot with a price on it and no `[FIXTURE]` / `[UNVALIDATED]` / `[REFUSED]` badge; a page whose provenance block is below the fold; the live frontend unpatched while the record says "honest" | A render-level test: fetch the rendered HTML, assert the T1 sentence and the regime badge are present **in the same response as the number**, and assert the page contains no number without a badge beside it. Then a check on the *deployed* surface, because a passing unit test on a patch that was never applied is the failure | **NO** - `console/page.py` renders `labels.render('T1')` (MEASURED at 11:44Z) and no test asserts it; the honesty patch is a file in `docs/`, unapplied; the live tree on :3000 was never patched |

**Group II: the clock.** Grouped because `03-b` establishes they are one family with three tests, and the
registry is where a builder looks.

| # | Failure mode | Symptom | Test | Caught |
|---|---|---|---|---|
| F08 | **A window that is not the window.** A 24-hour window ending at extraction; a day bucket including the current partial UTC day; a count over "recent" sales with no defined end | A feature whose value moves when the extraction time moves, with no row changing | `priceSeries` filtered strictly `< cut_date`, with a case where a sale exists earlier on the cut day and must be excluded; every window boundary an explicit parameter | **NO** - no feature module has a test |
| F09 | **A hyperparameter clock leak.** The pooled mean, the between-event variance or the shrinkage weight computed over all events and used inside a fold | The prequential score is better than the strict event-level check, and both share the same hyperparameters so the check does not reveal it (`03-b` D-2) | The pooling fit is called in the fit phase and its outputs passed in as arguments; an assertion that no pooling call appears inside the scoring loop; a fold record carrying the fit window's event ids | **NO** - no fold code exists |
| F10 | **A population clock leak (survivorship).** The event set is "events with a resale", discovered at scoring time | The skill score improves as the event count falls. The excluded events are the overpriced, the cancelled and the ones whose market moved off-ledger | The population is an argument to `fit`, never a query; a report of the excluded events with an observables comparison; an assertion that an event whose `startsAt` is after the cut cannot enter on the grounds that it later had sales | **NO** - no fold code |
| F11 | **A derived aggregate read as a live feature.** `avgMarkupBps`, `medianResalePriceLamports`, `resoldShare`, `ResaleStats`, `Ticket.transferCount`, `Ticket.lastSalePriceLamports`, `Ticket.status`, `Ticket.ownerWallet`, `Ticket.redeemedAt` | A feature uncannily predictive of the event's final volume; a hazard that tracks the observed sale count; a coefficient that inflates every market-state term | A static grep of the engine package per field name with an allowlist for the label builders, plus a dynamic stale-payload test (mutate the aggregate block, assert byte-identical output). `03-b` §4 T2 | **NO** - the forbidden list is documented in `price_features.py`'s docstring and enforced by nothing. The field names legitimately appear in `event_analytics.py` and `resale_stats.py` as label builders, which is where an allowlist is needed |
| F12 | **A tie resolved by luck.** Rows sharing an instant, sorted by nothing, producing negative durations or a nondeterministic feature | The same extraction scored twice gives different numbers; a negative holding duration; a `τ` support with a hole | Sort on `(occurredAt, slot, id)`, assert every delta `>= 0`, print the count of rows at exactly the cut | **PARTIAL** - `price_features` sorts on `(occurredAt, slot, id)`, counts null slots, and asserts a non-negative time-to-event (MEASURED); no property test, and the assertion is in one function |
| F13 | **A revision treated as immutability.** A `revoke` rewrites a prior sale; a field's meaning changes at a definitional date; a backfill changes a value at a past instant | A feature stable in one extraction and unstable across two. A level shift at a date that reads as a market move | A two-snapshot append-only canary on `(slot, kind, price, from, to)`; a sane-state assertion (no sale after its own revoke); the extraction digest in the fold record; a break test at the definitional date | **NO** - `API_CONTRACT.md` has no revoke semantics (`03-b` Q2) |

**Group III: the estimator.** The ones that are wrong even when the clock is right.

| # | Failure mode | Symptom | Test | Caught |
|---|---|---|---|---|
| F14 | **The cap-hit test off by one basis point.** Exact equality on a rounded bps field, so every capped event reads uncapped | Every event shows `capped_no_mass_point`; the mass point is never seen; the cap stratum is empty | `abs(markupBps - capBps) <= 1`, with `capBps is None` as its own branch and a constructed case on a face that does not divide evenly (`03-b` §7 row 16, D-1) | **PARTIAL** - specified in the build and in `03-b`; no test, and `00-data-situation.md` §2 notes the fixture never lands on a cap, so the path cannot be exercised on a fixture at all |
| F15 | **The median on a truncated distribution.** A central statistic reported where the cap mass exceeds 50%, so the "median" is the policy ceiling | A median exactly equal to the cap; a band centred on the ceiling | `if cap_hit_share > 0.5: refuse`, and no central path statistic beyond it | **PARTIAL** - `value_band` refuses on the capped-and-binding regime generally; the 50% guard specifically is not tested |
| F16 | **Strata pooled.** Capped and uncapped, verified and unverified, or two `p0` bands estimated with one `θ̂` | A coefficient that is a compound of two populations and estimates neither (`03-b` §5 P1, P2) | Separate `θ̂` per stratum, or an interaction, with the stratum counts printed beside every estimate; an assertion that the strata are never combined in one number | **NO** |
| F17 | **Redemption or revocation treated as censoring.** Redeemed tickets dropped rather than exiting the risk set | A hazard inflated or deflated depending on who redeems, and no way to tell which; the exposure denominator wrong by the redemption count | A cause-specific exit loop over `{sale, transfer, redeem, revoke}`, no `if redeemed: drop`, and a test that pipes a redeemed ticket through and asserts it exits at its own instant | **PARTIAL** - `intensity` is documented as cause-specific and reads rows, not `Ticket.redeemedAt`; no test |
| F18 | **Face value as a free regressor.** The decision, or the cap in money, on the right-hand side | A plausible-looking coefficient on price that is the organiser's own policy read back as a law of nature (`03-b` §5 P3, `01-d` §5) | No coefficient on `faceValueLamports` or the ladder ratio; `resale_cap_bps` and `requires_verified_wallet` partition, never regress; a design-matrix assertion | **NO** - and there is no coefficient code yet, so this is the mode that will arrive with the first fitted model and nothing will be waiting for it |
| F19 | **The fee defaulting to zero.** A missing fee treated as no fee | Net revenue that looks better than gross; an optimum that ignores the wedge; a level shift at a definitional date | A missing fee raises, or returns `netRevenue: None` with `no_fee_model`. The refusal exists (`primary_optimum.py`, MEASURED by grep); a test asserting it does not | **PARTIAL** |
| F20 | **The engine's recommendation changes the data and nothing records it.** The deployment distribution is not the training distribution because the engine moved it (`03-b` §5 P3) | A model that scores well in backtest and drifts in production for no observable reason; no way to attribute the drift | Log every recommendation and whether it was accepted; if not logged, the report must say the contamination is permanent. The randomised tier-face experiment (`02-d` §3.6) is the only correction | **NO** - and no test can catch it; it is a data-collection requirement and belongs in the deliverable as one |

**Group IV: the guards.** The modes where the thing that was supposed to catch the others fails quietly.

| # | Failure mode | Symptom | Test | Caught |
|---|---|---|---|---|
| F21 | **A guard that never runs, or cries wolf.** A checker that is defined and not wired; an allowlist that goes stale and fails on the standard library; a lint that everyone widens by reflex | A red suite whose failures are all in the harness; a green suite that proves nothing because the check was disabled; `grep` finding one definition and no caller. Both halves are live tonight: `contains_banned` has no caller, and five of the five failing tests are the stale dependency allowlist rejecting `math`, `re` and `html` | A mutation test per guard (disable it, confirm something fails); an assertion that every `BANNED` pattern is reachable by `contains_banned` from a page or payload path; and, for the allowlist, a positive test that the *check itself* detects a genuine third-party import | **YES, as noise** - the stale allowlist is red right now, which is the failure mode caught in the worst possible way: as a false positive that trains the reader to edit the allowlist |
| F22 | **A golden number instead of an invariant.** A test that pins the fixture's current output, so a change in the arithmetic is caught but a wrong arithmetic is not | A test that must be updated in the same commit as every fixture regeneration; a "golden" file whose expected values nobody can derive | Every assertion is an invariant or a recomputation from the contract's own rule, with the fixture number only as a *reported* snapshot (`BUILD-SPEC-NIGHT.md` §4.7's right-hand column is the model) | **PARTIAL** - the contract tests recompute from the contract (good); no test asserts the §4.7 invariants at all |
| F23 | **A row count read as a count of things.** "90 of 128 tickets sell" where 90 is sale rows and 49 tickets sold | A denominator that cannot be reconciled with the schema; two files disagreeing on the same quantity | A reconciliation check per statistic: the count must be defined as rows or as distinct keys, and the two must be printed separately when they differ | **NO** - this is the defect that actually shipped, and it took a human verifier and a corrections pass |
| F24 | **A citation attached to the wrong proposition.** A real paper cited for a claim it does not make, or with the wrong authors, year or pages | A reference that resolves but does not support the sentence; an author set that fails Crossref | A per-citation check that the proposition is quotable from the source, not merely that the DOI resolves. `00-verification-round1.md` ran the DOI check and found 4 wrong attributions anyway, because resolving is not supporting | **NO** |
| F25 | **The verifier's own defect propagating.** A reviewing pass introduces a finding that is false, and it is inherited by three documents before anyone checks it | A defect that three files agree on and the source does not contain. This happened: the S-prefixed Aigner DOI that `01-b` never contained | The verifier must quote the line it is reviewing, with the file and the string; and a correction pass must check the claim against the source before appending. Both are now practice, neither is enforced | **NO** |
| F26 | **A SIM result quoted as evidence about tickets.** "The estimator recovers the parameter to within 5%" printed without its DGP | A number that travels out of its conditional. The registry already has a live instance of the adjacent case: a cure-versus-tail comparison computed on fixtures, ruled at best SIM, and therefore carrying no admissible support at all | Every SIM number carries `SIM` and its DGP in the same line; a lint over the deliverable for accuracy vocabulary outside a SIM block; and the rule that no SIM number appears in a table beside a real one | **PARTIAL** - the vocabulary exists (`records/README.md`); nothing enforces it |
| F27 | **A truncated record read as a demand curve.** The hottest events reading as the coolest because their prices were clipped | A negative relationship between demand and price in a market everyone knows is hot; a ranking that inverts | The cap stratum estimated separately, the cap mass reported as rationing not value, and no pooled mean across capped and uncapped events (`03-b` §5.1's table) | **PARTIAL** - the sentences exist (A19, A20); no test asserts they are attached |
| F28 | **The engine saying the sentence it exists to remove.** A price-specific sale probability on the page | "X% chance of selling at price p" anywhere in a payload or on a screen | The X-list's first three patterns plus `saleProbability: null` in every state. The payload does carry `null` with `not_identified` (MEASURED in `guidance.py`); the scan is dead code | **PARTIAL** - the refusal is in the code, the scan is not wired |

### 4.3 Where the modes came from, in one paragraph

Twenty-seven of the twenty-eight rows trace to a named source; the twenty-eighth, F06, is the mode already
covered by a working test. F01, F23, F24 and F25 are defects that shipped
tonight and were corrected in `CORRECTIONS-APPLIED.md`: a row count read as a ticket count in a
load-bearing argument; five numbers wrong or unsourced; four author attributions wrong; one false finding
created by a verifier and inherited by three documents. F02, F04, F05, F07, F09, F10, F12, F14, F15, F19 and
F28 are named in `03-b` or in the build spec as live traps with named instants, and the registry here adds
the "caught today" column that neither has. F21 is measured in this pass. F03, F08, F11, F13, F16, F17, F18,
F20, F22, F26 and F27 come from the identifiability and cap findings. The point of listing them together is
that **the ones that actually caused damage were documentation failures, not estimator failures**, and the
test suite is aimed almost entirely at the estimator.

### 4.4 The count

**The count below is the 11:47Z snapshot; the CORRECTION block at the end of this file re-measures it at
11:50Z as 12 caught, 6 PARTIAL, 10 uncaught, and names the eleven rows that moved.** The reasoning that
follows survives the change, so it is left standing.

**28 failure modes. 2 are caught today by a test that would fail: F06 (contract drift) and F21 (a guard that
never runs, caught only because its allowlist went stale).** 14 are PARTIAL: the mechanism that would prevent
them exists and no assertion exists to prove it. 12 are NO: nothing is watching. Of the seven modes this pass
was asked to include specifically, one is caught (F06), five are PARTIAL, and one (F07, the label that never
reaches the screen) is uncaught and is the most likely of the seven to embarrass the product, because it is
the only one a person looking at the screen would see.

The shape of that count is the finding. The two that are caught are both about the *interface* (the wire
contract and the dependency boundary). The twelve that nothing is watching are, with one exception, about the
*claims*: the clock, the aggregates, the strata, the face-as-regressor, the fee default, the row-as-ticket
count, the wrong citation. The suite is aimed at the place where a defect is cheap to find and the damage
has been done where it is expensive.

---

## 5. The adversarial review protocol

`RESEARCH-PROGRAM.md` Phase 6 requires independent agents to challenge mathematical assumptions, data
assumptions, model identifiability, causal conclusions, economic assumptions, generalization and operational
feasibility, and to propose failure scenarios and counterexamples. All three passes so far have done this
and the pattern in their output is consistent and worth encoding: **every verdict was
STANDS-WITH-NARROWING, and in every case the body was more careful than the summary.** The reviews'
finding was not that the analysis was wrong; it was that the headline sentence was the least defensible
sentence in the file and the one a reader would carry.

### 5.1 Who reviews what, and the one disqualification

| Reviewer | Reviews | Must not have | Why the disqualification is absolute |
|---|---|---|---|
| **R1 · Mathematical** | The algebra: the estimator's derivation, the identifiability claims, the truncation result, the band formula | Written or co-written the file; supplied the derivation | A reviewer who derived it reviews their own mistake. `00-adversarial-review-phase1.md` is the model: it was written by an agent that wrote none of the three files, and it re-derived each claim before testing it |
| **R2 · Data and temporal** | The cut, the folds, the crossings, the survivorship, the re-extraction stability | Built the feature pipeline | The person who wrote the truncation filter cannot see the window they forgot |
| **R3 · Economic and product** | Whether the recommendation is the thing an organiser would act on, the fee basis, the objective, the boundary statement, and whether the printed sentence means what the reader will take from it | Written the interface copy | The author of a label reads their intention, not the sentence |
| **R4 · Operational** | Whether it runs on this machine under D2, within the five-minute bound, with the refusals firing, and whether a refusal is distinguishable from a bug at the screen | Written the deploy path | Optimism about the environment is the author's |
| **R5 · SIM and harness** | The simulation design, the pass conditions, and the harness's ability to fail (G7) | Written the SIM study | This is the single most important disqualification in the list: a SIM study reviewed by its author is a tautology with a table of numbers |
| **R6 · Verifier** | The five reviews themselves, mechanically: does each quoted line exist, does each DOI resolve *and* support its sentence, does each number have a source | Written any of the five | `00-verification-round1.md` found 16 defects, of which one was created by a prior reviewing pass. A review is a document and needs the same treatment as one |

**Neither the builder nor the orchestrator is a reviewer.** The orchestrator reads the reviews and folds
them in; it does not adjudicate between a reviewer and its own author, because that is the same conflict in
a different chair.

### 5.2 The questions a reviewer must answer before the work is trusted

Each is answerable yes, no, or with a named file and line. "It seems reasonable" is not an answer and
"probably fine" is not an answer. Written as a checklist so a review can be graded rather than admired.

**On the claim itself**

1. **What is the strongest sentence in this file, and is it in the body as well as the summary?** If the
   body qualifies and the summary does not, the summary is the finding and it must be rewritten. This is the
   single highest-yield question in the list: it caught three of three in round one.
2. **What is the class of this conclusion, and is it the right class?** A hypothesis stated as a finding is
   a class violation, not a judgement call. Which specific source supports it, and does that source say it?
3. **Is the sentence about value or about price, about correlation or about causation, about this platform
   or about tickets generally?** The four confusions in one question, and every one of them has shipped here.
4. **What is the falsifier?** If nothing could show this wrong, it is not a claim.

**On the data**

5. **Which field carries this number, and when did that field become what it is now?** The answer must be a
   field path and an instant.
6. **If a filter changed tomorrow, what would move?** Name the statistic that would change, and whether it
   should.
7. **Was this computed from the observation set in `00-data-situation.md` §3, or from something adjacent to
   it?** Adjacent includes a fixture, a mock, a page, a screenshot, and a memory of a number.
8. **Does this quantity exist in the record at all?** `03-b` §3 finds 18 of 61 candidate features dropped,
   6 of them absent from the schema. Absence is a different defect from bias and needs a different remedy.

**On the method**

9. **Does this estimator recover the parameter when its own assumptions hold?** If nobody has run that
   study, say so; the answer is not "it should".
10. **Is the pass condition written down before the number exists?** A pass condition chosen after the run
    is a description of the run.
11. **What happens at the boundary: `N = 0`, `N = 1`, `N = 3`, and `N` just under every floor?** The
    refusal is the product's honest state, and it is the state nobody tests.
12. **If this component were removed, what would the score do?** If the answer is "nothing", the component
    is not justified by out-of-sample evidence and the file must say so.

**On the treatment of uncertainty**

13. **Is this an interval, a band, a bound, or a point, and does the sentence use the right word?** A band
    described as a confidence interval, or a bound printed as a level, is the failure the product exists to
    avoid.
14. **What is the width, what is it made of, and does it widen as the data thin?** A constant width across
    the `N` ladder is a defect.
15. **On a capped event, is the direction of the bias stated and the tail declared invisible?** The bias is
    `s · E[m* − c | m* ≥ c]` with both factors unobserved (`02-b` §1.2); a correction would be an invention.

**On the record**

16. **Where is this written down, and is it the place the next session will load?** Chat is not storage.
17. **Does any number in this file appear in two files with two values?** Six live cross-file conflicts were
    counted in one pass. A conflict recorded is fine; a conflict unnoticed is a defect.
18. **What did this review not check?** Every review so far has stated this, and it is the most useful
    section of each.

### 5.3 The verdict vocabulary, and what a verdict must contain

Three verdicts and no others: **STANDS**, **STANDS-WITH-NARROWING**, **FALLS**. Each verdict must carry:
the quoted sentence attacked, the attack, the strongest counter-argument to the attack, the verdict, and
the narrowed wording if the verdict is not STANDS. The counter-argument is not politeness; it is the only
thing that distinguishes a review from an opinion, and in round one every attack had a real counter-argument
that had to be answered on the way to the verdict.

Two rules about severity, because a review that reports only high-severity findings is not doing the job:

- **Every finding gets a severity (H/M/L) and its own line**, and the count is reported. Round one produced
  39 rows across three files: the useful output was the *distribution*, not the worst item.
- **A defect the reviewer cannot substantiate is recorded as unverified, not as a defect.** Round one
  carried several "unverified, not refuted" items on purpose, and the correction pass then had to withdraw
  one finding that had been stated as fact.

### 5.4 Why the reviewer needs a verifier

Because a review is the most trusted document in the pile and the least checked. The one defect in this
corpus that was *created* rather than found was created by a reviewing pass, asserted by a second reviewing
pass, and inherited into a third document before anyone grepped for the string. `00-verification-round1.md`
exists because of that, and its own output contained two overstatements, which
`CORRECTIONS-APPLIED.md` §4.3 then had to correct. The lesson is structural, not personal: **a review is a
claim, the claim needs a source, and the source is checked by a different pass with a different method.**
The method that works is mechanical: quote the line with the file, grep for the string, query the DOI,
recompute the arithmetic, and print the intermediate values.

---

## 6. What is unvalidated here, and what would falsify this document

**Unvalidated.** Everything in §2 and §3 is PLANNED. No fold has been constructed, no baseline has been
scored, no study has been run, and no metric has a value. The runtime table in §3.4 is measured per-fit cost
plus arithmetic on a planned grid, and it is an estimate of the study's cost, not of anything the study
would find.

**Label on this file's own conclusions:** the protocol is class C (established statistical methodology
applied to a specified observation set), the floors in §2.3 are class C and derived in-line, the count in
§4.4 is MEASURED against a named snapshot, and the SIM pass conditions are PLANNED with their algebra shown.
Nothing here is class A or B, and nothing here is a ticketing finding.

**What would falsify it.**

- **A listing panel arriving tomorrow** would not falsify §2, it would shorten it: M1 through M4 stand, the
  `not_identified` refusal disappears for the price-conditional question, and F11's forbidden list shrinks
  by two rows. I would update the protocol rather than defend it.
- **If the between-event dispersion turns out to be small** at about ten completed events, the `τ²` floor
  relaxes and G2's grid should be re-centred. That is measurable at ten events and should be measured
  before any further pooling work.
- **If the first real extraction shows a floor violation on a capped event** (a settled sale below
  `face × (1 + c)`), then either the cap is enforced at settlement rather than at the ask (`03-b` Q4) or the
  fee basis differs from the record's, and the whole floor statement in §2.3 M3 needs restating. That is the
  one result that would change the *product's* central sentence rather than the protocol.
- **If G7 fails** (the harness cannot detect a known leak), every score the harness produces is void and the
  protocol in §2 is unexecuted in the only sense that matters. G7 therefore runs first, before any other
  study, and its result is reported even if every other study is skipped.
- **If the five untested modules acquire tests that pass on the first run**, check the tests before
  believing them (J1 in §1.5): a test written against an implementation has a strong tendency to be green.

---

## 7. Registry rows this file implies

Not edited here, per the pass's file boundary.

- **A (research ledger):** one row, "P6 validation protocol and failure-mode registry", this file, class C,
  first pass complete, with §3 marked PLANNED.
- **B (mathematical knowledge base):** the coverage-resolution floor `n ≥ 1.96²p(1−p)/δ²` (§2.3); the CVaR
  tail-count floor `0.05n ≥ 5` (§2.3); the baseline definitions B0–B3 as a named set (§2.4); the
  pre-registered reading of an ablation (§2.5); the pass-condition form used in §3.2.
- **D (model registry):** no new model. One constraint row per SHIP estimator: "subject to G1/G2/G3/G4/G5/G6
  as specified in `06-validation-protocol.md` §3.2, none run". And a note on M01–M03: rejected as products,
  mandatory as baselines B0/B1/B3.
- **F (decision log):** a decision row that a component which fails its ablation is removed from the build
  rather than kept behind a flag; a decision row that G7 runs before any score is believed; and an open
  question, already implied by `03-b` Q8, on whether recommendations and acceptances will be logged, since
  without that M3(b) and M4 can never be more than descriptive.
- **C (variable registry):** nothing new. The eight crossing objects in §2.2 are admissions conditions on
  existing rows, not new variables.

---

## Sources

Cited here for propositions that belong to other records, so this file can be read alone.

- The observation set, the four gaps and the toolchain: `records/00-data-situation.md` §1 (no pip, no numpy,
  standard library only), §2 (fixtures synthetic, three independent checks), §3 (the wire contract's fields),
  §4 (Gaps 1–4), §5 (no class A from our own data; simulation admissible for estimator properties only).
- Evidence vocabulary, SIM and UNVALIDATED: `records/README.md`.
- The identification status of each target: `records/findings/01-b-identifiability.md` §3 and §4.
- The cap as a policy truncation and the refusal wording: `records/findings/02-b-cap-truncation.md` §1,
  §3; `records/findings/03-b-temporal-correctness.md` §5 P1, §7 rows 15–18.
- Calibration with no validation set, the prequential requirement, the proper-scoring requirement and the
  seven things a user must not conclude: `records/findings/02-c-sale-hazard.md` §3.9, §5.1–§5.3.
- The clock, the crossing table, the fold construction, the count floors and the pre-registered rule:
  `records/findings/03-b-temporal-correctness.md` §2, §4 (T1–T6), §6.1–§6.7, §7, §9 D-2, D-3.
- The review form this protocol encodes, and the sentences the engine may and may not print:
  `records/findings/00-adversarial-review-phase1.md` §1, §2, §3, §4, §6.
- The verification method and the false finding: `records/findings/00-verification-round1.md` §1, §2.
- The sixteen defects and the standard for a correction: `records/CORRECTIONS-APPLIED.md` §1, §3, §4.
- Role vocabulary, the SHIP set and the "no model is validated" basis: `records/D-model-registry.md` §1,
  §2.
- The refusal codes and the worked fixture invariants: `records/BUILD-SPEC-NIGHT.md` §3.7, §4.7, §4.8.
- The contract as an executable acceptance test: `records/CONTRACT-CONFORMANCE.md` §1.
- [Dawid 1984] Dawid, A. P. (1984). Statistical theory: the prequential approach. *JRSS A* 147(2), 278–292.
  https://doi.org/10.2307/2981683: the prequential protocol is the one that tests the forward decision.
- [Gneiting & Raftery 2007] Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction,
  and estimation. *JASA* 102(477), 359–378. https://doi.org/10.1198/016214506000001437: why a proper score
  is required for a baseline comparison to mean anything.
- [Graf et al. 1999] Graf, E., Schmoor, C., Sauerbrei, W. & Schumacher, M. (1999). Assessment and comparison
  of prognostic classification schemes for survival data. *Statistics in Medicine* 18(17–18), 2529–2545.
  https://doi.org/10.1002/(SICI)1097-0258(19990915/30)18:17/18<2529::AID-SIM274>3.0.CO;2-5: the IPCW Brier
  score, for scoring a right-censored outcome inside a fold.
- [Wilson 1927] Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference.
  *JASA* 22(158), 209–212. https://doi.org/10.1080/01621459.1927.10502953: the interval for a small rate, and
  the family of arithmetic the coverage floor in §2.3 comes from.
- [Powell 1986] Powell, J. L. (1986). Censored regression quantiles. *Journal of Econometrics* 32(1), 143–155.
  https://doi.org/10.1016/0304-4076(86)90016-3: why a lower quantile survives the truncation that G3 and
  F04 assume, and the reason the engine may print one and not the other.
- [Fine & Gray 1999] Fine, J. P. & Gray, R. J. (1999). A proportional hazards model for the subdistribution of
  a competing risk. *JASA* 94(446), 496–509. https://doi.org/10.1080/01621459.1999.10474144: redemption and
  revocation as competing risks, the assumption G4's DGP is written to.
- [Firth 1993] Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika* 80(1), 27–38.
  https://doi.org/10.1093/biomet/80.1.27: the penalty in G4's separation cell, and the reason a block with
  zero sales cannot be allowed to diverge.

Internal measurements this pass took, all reproducible:

```
python3 -m unittest discover -s tests -t .          # 149 tests, 8.336 s, 5 failures (11:47Z)
python3 -m unittest discover -s tests -t .          # 222 tests, 8.376 s, OK           (11:50Z, after the six test files landed)
python3 -m unittest tests.test_contract_conformance  # 22 tests, OK
python3 -m unittest tests.test_boundaries           # 13 tests, 5 failures on one method
grep -rn contains_banned --include=*.py .           # one hit: the definition
grep -l value_band tests/*.py                       # no hits
wc -l ticketpath/core/price_features.py ticketpath/core/value_band.py \
       ticketpath/core/path_model.py ticketpath/core/intensity.py \
       ticketpath/core/primary_optimum.py           # 1183 of 2501 lines in core
```

*No file outside this one was written. Nothing was committed or pushed. `lib/mock/` was not read. The SIM
study was not run, no fold was constructed, and no metric in §2 has a value.*

---

## CORRECTION (2026-11-07T11:56Z) — the "caught today" column, measured again on a tree that moved

Appended because the working tree was being written throughout this pass and the snapshot in §1.5 stopped
being true within minutes of being taken. Nothing above is deleted; the 11:47Z measurement was correct for
`a0513aff…` and this block supersedes it. **Wherever §1.5 says 149 tests with 5 failures, or §4.4 says 2
caught, read this block instead.**

### What changed

Six test files landed between 11:47Z and 11:50Z, 1,259 lines in total, covering exactly the five modules
§1.5 identified as untested plus the label registry: `test_price_features.py`, `test_value_band.py`,
`test_path_model.py`, `test_intensity.py`, `test_primary_optimum.py`, `test_labels.py`. The stale
standard-library allowlist in `test_boundaries.py` was fixed in the same window, so the five false-positive
failures are gone.

Measured at **2026-11-07T11:50Z**, digest `a653e5bfa49c6871d6f8107a1404dffe722c27f39d588da37dd6a14b23ea6f9d`
over `tests/*.py` plus the five claim modules plus `labels.py` and `page.py`:

```
python3 -m unittest discover -s tests -t .   → Ran 222 tests in 8.376s, OK
```

`ticketpath/core` is 2,512 lines at this snapshot, of which the five claim modules are 1,194 (48%), and they
are now covered. The three facts in §1.5 therefore become: (1) the suite is green, and the failure that was
there was a harness false positive, which is F21's evidence and stands as evidence; (2) the claim that the
five claim-bearing modules have no tests is **withdrawn**, and with it the 47% figure; (3) the J1–J4
judgement rule stands unchanged and now has something to be applied to. On J2, the new tests are
invariant-based rather than golden-number-based, which is the right form: `test_the_band_is_z_times_tau_wide_in_logs`,
`test_required_sell_through_is_face_times_sell_through_over_the_candidate`,
`test_the_floor_is_the_highest_recorded_price` all recompute from a definition. On J1, no mutation run
exists yet, so "these tests can fail" is still an assumption rather than a measurement.

Two of the new tests are stronger than the checklist asked for and worth naming because they close rows I had
marked uncaught: `test_a_future_sale_three_times_the_price_changes_nothing` is the future canary `03-b` §4 T1
specifies, and `test_prefix_invariance_over_every_sale_instant` is the property test rather than an example.
`test_no_engine_module_reads_an_aggregate_or_a_whole_life_field` walks the AST of every engine module instead
of grepping, which is the correct implementation of `03-b` §7 row 5.

One caveat that survives both snapshots and belongs next to the canary. Prefix invariance compares two
computations of the *same function*, so it cannot catch a definition-level leak: a feature defined as "the
last cap sale" passes prefix invariance at every cut by construction, because the function is evaluated on
the truncated prefix in both arms. That is precisely the case `03-b` §4 T1 says only the canary catches. The
canary now exists for the feature builder as a whole; `03-b` §7 row 7 still asks for one **per feature**, and
that is not what shipped.

### The failure-mode count, re-measured

**28 failure modes. 12 are now caught by a test that fails when the defect is present, 6 are PARTIAL, and 10
have nothing watching.** The rows that moved from PARTIAL or NO to caught, with the test that does it:

| Row | The mode | What now catches it |
|---|---|---|
| F02 | A retrospective feature that looks as-of | the future canary and the prefix-invariance property test |
| F04 | A cap-truncated mean reported as value | `test_there_is_no_upper_end_and_no_level`, `test_the_binding_event_is_a_floor_and_never_an_upper_end` |
| F05 | A cold-start point estimate presented as a measurement | `test_a_prior_is_not_a_record_so_the_band_is_prior_only`, `test_no_events_returns_the_borrowed_prior_and_says_so`, `test_below_nine_events_the_between_event_variance_is_declared` |
| F11 | A derived aggregate read as a live feature | the AST walk over every engine module. The **static** half: the dynamic stale-payload test still does not exist |
| F12 | A tie resolved by luck, or a negative duration | `test_no_negative_time_to_event`, `test_the_null_slot_fallback_is_counted_not_silent` |
| F14 | The cap-hit test off by one basis point | `test_the_cap_hit_test_has_a_one_basis_point_tolerance`, `test_a_sale_one_basis_point_off_the_cap_still_counts_as_at_the_ceiling` |
| F15 | A median on a distribution whose mass is at the ceiling | `test_more_than_half_the_marks_on_the_ceiling_refuses_a_central_statistic` |
| F17 | Redemption or revocation treated as censoring | `test_a_redeemed_ticket_stops_contributing_at_its_redeem_row`, `test_each_exit_is_counted_separately` |
| F19 | The fee defaulting to zero | `test_no_fee_withholds_net_revenue_and_leaves_the_recommendation_alone` |
| F21 | A guard that never runs | `contains_banned` now has callers in `test_labels.py`, tested in both directions (a banned shape is caught, the allowed negatives are not). The stale-allowlist half is green, which does not fix the mode, it only stops the false alarm |
| F28 | The engine saying the sentence it exists to remove | `test_the_sentence_this_build_exists_to_remove_is_banned`, `test_each_prohibited_shape_is_caught`, plus `saleProbability: null` with `not_identified` in the payload |

F03 and F22 stay PARTIAL, and the reason is the same in both: the *phrases* are pinned and the *objects* are
not measured. No test asks whether the declared band's coverage matches the sentence's claim, which is G8, and
no test asserts the sentence reaches a rendered page.

**The ten that nothing is watching, grouped, because the grouping is the finding:**

- **Everything that needs a fold** (F09 the hyperparameter clock, F10 the population clock, F16 strata
  pooling): there is no fold code, so no test can exist. These are the rows the first backtest has to build,
  and building them without these three tests means the first score produced is uninterpretable.
- **Everything that needs the screen** (F07 the label that never reaches the screen): `console/page.py`
  exists and renders T1, `console/blocks.py` exists, and no test fetches a rendered page. The live frontend
  on :3000 is still unpatched. This remains the single highest-risk uncaught mode in the registry.
- **Everything that is prose** (F23 the row read as a ticket count, F24 the citation attached to the wrong
  proposition, F25 the verifier's own defect propagating): all three shipped tonight and were corrected by
  hand. A documentation lint is the only thing that would catch them, and none exists.
- **The engine's own effect on its inputs** (F20, the `p0` contamination): no test can catch it. It is a
  data-collection requirement and it belongs in the deliverable as one, not in the suite.
- **Everything that arrives with the first fitted model** (F18, face value as a free regressor): there is no
  coefficient code yet, so the mode is latent. It is the one to write the test for *before* the model, since
  after the model the test will be written against it.

None of this changes the conclusion in §1.1. Nothing about tickets has been validated, the 222 green tests
are a claim about engineering and not about pricing, and both statements have to be made in the same breath
or the second one is read as the first.

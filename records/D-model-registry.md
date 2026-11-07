# D · Model registry

**What this is.** The programme's §2.D record: every model this programme has investigated, with its target
subproblem, mathematical form, parameter count, data requirement, computational cost under D2, what it would buy
if it worked, its failure mode, its evidence class, its validation status, and its recommended role. Rows for
losers are kept, because a registry with only the winners cannot answer "why not this one" in six months.

**Status:** first complete pass. **Last updated:** 2026-11-07T11:10Z. **Author:** records agent, folding
`findings/` into §2.D. **Append-only after this point.** A model is never deleted from here; a superseded verdict is
struck through or marked superseded with the date.

**Inputs read for this pass.** `RESEARCH-PROGRAM.md` §2.D, §4.3, Phase 4 and Phase 5. `records/00-data-situation.md`,
`records/F-decision-log.md` (D1, D2, D3, D4, Q1, Q2, Q3), `records/README.md`,
`records/findings/01-a-market-structure.md`, `01-b-identifiability.md`, `01-c-methods.md` (all eight families, plus
§10's rejected-and-deferred list and §12's unresolved items, 1,558 lines at read time), `01-d-external.md`,
`00-ledger-verification.md`,
`00-adversarial-review-phase1.md`, `02-a-price-paths.md`, `02-c-sale-hazard.md`, `02-d-elasticity-fees-optimum.md`,
`02-e-cold-start.md`. Also read: `ticketpath/adapters/pricing_model_adapter.py`, `ticketpath/core/markup.py`,
`ticketpath/core/resale_stats.py`.

**Inputs absent from disk when this file was written, and therefore not folded in.**

- `records/findings/02-b-cap-truncation.md`: **does not exist.** The cap is covered here only through
  `01-b` §4.4 and §4.5, `01-a` §3, `01-c` §4.3 and `02-a` §6. If 02-b lands, rows M08, M09, M13, M24 and M31 need
  re-reading against it.
- `01-c-methods.md` was still being appended while this file was written. It reached §10 (rejected and deferred),
  §11 (sources) and §12 (unresolved) before this pass closed, and all three are folded in. A later section could
  still arrive; the verdicts below are the ones on disk at 11:10Z.
- `records/B-mathematical-kb.md` is a 106-byte stub, so the derivations behind these rows live in the findings
  files only. This file points at them and does not restate them.

**Basis, stated once so no row has to repeat it.**

- **D1.** There is no real ledger. No backend, no database, no deployed program, fixtures synthetic and barred from
  estimation (`00-data-situation.md` §1 and §2). Therefore **no model in this file is validated, none may be marked
  validated, and no accuracy, lift, coverage or error number appears anywhere in it.**
- **D2.** Standard-library Python 3.12 only. No numpy, scipy, sklearn, statsmodels, no LP solver, no MCMC library.
  Cost estimates below are for that stack.
- **D3.** `P(sale at price p)` is a data requirement, not a model. It appears here as gated rows M31 and M32.
- **SIM.** **No simulation study exists anywhere in this repository.** Not one row in this file is labelled SIM,
  and none can be until someone writes the estimator-recovery study that `00-data-situation.md` §5 permits. In
  particular, `01-b`'s cure-versus-long-tail comparison was computed on fixtures; `00-adversarial-review-phase1.md`
  error 2 rules it at best SIM and not class C, so it is **not** carried as evidence for the cure component (M30).
  Under `00-data-situation.md` §2 the fixtures cannot support it either, which leaves the claim with no admissible
  support at all.

**Measured state of the engine, so the role column cannot be misread.** `ticketpath/adapters/pricing_model_adapter.py`
registers **no model** and returns `available: false, basis: "no_model_registered"`. `ticketpath/core/markup.py`
computes markup, mean, median and the six contract buckets over whatever rows it is given: descriptive arithmetic,
not a model. So **zero models are in the engine tonight.** Every SHIP row below is a build instruction with a named
owner-level reason, not a description of the current build.

## Subproblems

The seven of Phase 4, with the identifiability-ledger rows of `01-b` they answer to.

| # | Subproblem | Ledger | Identification status today |
|---|---|---|---|
| S1 | Latent transaction-price estimation | T1, T1′ | set-identified at trade instants; between trades not identified; level disputed (see C2) |
| S2 | Current market-state estimation | T2 (level), ξ | identified as a transaction mark-time intensity; the latent level is not |
| S3 | Future resale-price forecasting | T2 (path) | curvature and event deviations identified; linear trend not identified |
| S4 | Demand estimation | T4a / T4b | attributes: set-identified; demand: not identified, one-sided bracket only |
| S5 | Sale-probability estimation | T3 | price response **not identified**; composite transaction rate identified |
| S6 | Prediction uncertainty | T6 | sale indicator calibratable on a full population; no price distribution is |
| S7 | Primary-price optimisation | T5 | a set with bounds, not a point; primary demand response not identified |

## Role vocabulary

Exactly one per model. The definitions are this file's, and the reason sits in the row.

- **SHIP** : the code belongs in the engine tonight. It is either identified on the current contract (no missing
  field) or it is a numerical guard or evaluation harness the engine cannot be honest without. SHIP does not mean
  "produces a number": with an empty ledger every SHIP row must refuse rather than guess, which is what
  `pricing_model_adapter.py` already does at the top level.
- **SHIP-BEHIND-ADAPTER** : implemented, registered behind a data adapter, and **switched off** until a named field
  exists. The default gate is the four listing fields of D3 (`listPriceLamports`, `listedAt`, `delistedAt`,
  `delistReason`); where the gate is a different field, the row names it.
- **SPECIFIED-NOT-IMPLEMENTED** : mathematically written down here or in the cited finding, code **deliberately
  absent**, with the reason it is absent (no data, no solver under D2, a parameter that is a prior in disguise, or
  a decision the operator has not made). A spec without an implementation is a claim about what would be built.
- **REJECTED** : not to be built, with the reason. Every rejection names what would revive it, because
  `01-c` §10's own standard for a defensible rejection is that it names its revival condition.

**Evidence classes** are `records/README.md`'s A to E, quoted, never computed here. Verdicts that rest on an
argument are C; verdicts that rest on a published ticket study are A at the source and are marked "A-cited" so the
transfer is not implied; hypotheses are D; ideas recorded so they are not lost are E.

---

## 2. Index

| ID | Model | Target | Params | Role | Validation |
|---|---|---|---|---|---|
| M01 | Face-value rule | S1 | 0 | REJECTED | n/a, rejected at identification |
| M02 | Fixed-markup rule | S1, S7 | 1 | REJECTED | n/a |
| M03 | Population-mean rule | S1 | 1 | REJECTED | n/a |
| M04 | Uncensored hedonic (OLS) | S1, S4 | tier + event + k | REJECTED | superseded by M05 |
| M05 | Censored hedonic (known bound, EM) | S1, S3, S4 | ≈ tier + event + knots + 2 | **SHIP** | C by argument, UNVALIDATED |
| M06 | Repeat-sales index (BMN) | S1, S3 | time cells | **SHIP** | C by argument, UNVALIDATED |
| M07 | Empirical-Bayes cold-start band | S1 | 2 hyperparams + grid | **SHIP** | C by argument, UNVALIDATED |
| M08 | Cap-bound one-sided estimator | S1, S6 | 0 to 2 | **SHIP** | A-cited structure, UNVALIDATED |
| M09 | Latent markup with leakage probability | S1, S6 | 2 + q(cap,event) | SPECIFIED | D, UNVALIDATED |
| M10 | Hybrid hedonic + repeat-sales | S1 | stacked | SPECIFIED | C, UNVALIDATED |
| M11 | Nearest-neighbour comparables | S1 | 0 (K fixed) | REJECTED | n/a |
| M12 | Matrix completion / collaborative filtering | S1 | factors | REJECTED | n/a |
| M13 | Extreme-value tail above the cap | S1, S6 | 2 to 3 | REJECTED | n/a |
| M14 | Joint mark-time intensity ξ(p,τ) | S2 | 0 (binned) | **SHIP** | C by argument, UNVALIDATED |
| M15 | Local-level state-space (Kalman) | S2, S3 | q, r | SPECIFIED | C, UNVALIDATED |
| M16 | Change-point guard (CUSUM/PELT) | S2 | 1 to 2 | SPECIFIED | C, UNVALIDATED |
| M17 | Deadline-convex path (1 param) | S3 | 1 + nuisances | **SHIP** | A-cited shape, UNVALIDATED |
| M18 | Martingale anchor / random walk | S3 | 0 | **SHIP** | C, UNVALIDATED |
| M19 | ARIMA / SARIMA | S3 | p,d,q | REJECTED | n/a |
| M20 | GARCH / volatility | S3, S6 | p,q | REJECTED | n/a |
| M21 | GAM / spline in τ, standalone | S3 | knots | REJECTED | n/a |
| M22 | Quantile regression (censored, IRLS) | S3, S6 | per quantile | SPECIFIED | C, UNVALIDATED |
| M23 | Recursive least squares, forgetting | S2, S3 | 1 (λ) | SPECIFIED | C, UNVALIDATED |
| M24 | Tobit primary sell-through bracket | S4, S7 | 2 per tier | SHIP-BEHIND-ADAPTER | B-cited, UNVALIDATED |
| M25 | Structural demand (Rosen 2nd stage / BLP) | S4 | many | REJECTED | n/a |
| M26 | Auction private-value inversion (GPV) | S4 | kernel | REJECTED | n/a |
| M27 | Optimal auction design, fitted | S4, S7 | prior | REJECTED | n/a |
| M28 | GP / kriging seat-quality surface | S1, S4 | hyperparams | REJECTED | n/a |
| M29 | Synthetic control / DiD / event study | S4 | few | REJECTED | n/a |
| M30 | Piecewise-exponential intensity + exposure | S5, S2 | K buckets + p + π | **SHIP** | C by argument, UNVALIDATED |
| M31 | Listing-episode cloglog hazard (Spec B) | S5 | M bins + 4 + p | SHIP-BEHIND-ADAPTER | C, UNVALIDATED |
| M32 | Constant-elasticity markup hazard | S5 | 1 (γ) | SHIP-BEHIND-ADAPTER | C, UNVALIDATED |
| M33 | Choke-price hazard | S5 | 1 (p*) | SPECIFIED | D, UNVALIDATED |
| M34 | Cox proportional hazards | S5 | p | SPECIFIED | C, UNVALIDATED |
| M35 | Fine-Gray subdistribution hazard | S5 | p | SPECIFIED | C, UNVALIDATED |
| M36 | Shared frailty hazard | S5 | + variance | SPECIFIED | C, UNVALIDATED |
| M37 | Full hierarchy sale⊂tier⊂event⊂category | S1, S4, S5 | β + τ + u | SPECIFIED | C, UNVALIDATED |
| M38 | Gamma-Poisson cold-start intensity | S5 | 2 | **SHIP** | C by argument, UNVALIDATED |
| M39 | Ridge / Firth separation guard | S5 | 1 penalty | **SHIP** | C by construction |
| M40 | HMC / NUTS full posterior | S5 | many | REJECTED | n/a |
| M41 | Contextual bandit over prices | S5, S7 | model-dependent | REJECTED | n/a |
| M42 | Conformal prediction | S6 | 0 (order stat) | REJECTED | n/a |
| M43 | Isotonic calibration | S6 | step function | REJECTED | n/a |
| M44 | Prequential proper scoring | S6 | 0 | **SHIP** | C by argument |
| M45 | Bandit over models | S6 | 0 | SPECIFIED | C, UNVALIDATED |
| M46 | Static grid optimiser, fee wedge, boundary | S7 | c**, η, u, q_min | **SHIP** | C by argument, UNVALIDATED |
| M47 | Mean-CVaR static optimiser | S7, S6 | + λ, α | **SHIP** | C by argument |
| M48 | Mean-variance optimiser | S7 | + γ | REJECTED | n/a |
| M49 | Reserve-price surface (backward induction) | S7 | per state | SPECIFIED | C, UNVALIDATED |
| M50 | Multiproduct fluid relaxation | S7 | per tier | SPECIFIED | C, UNVALIDATED |
| M51 | Overbooking / cancellation RM | S7 | n/a | REJECTED | n/a |
| M52 | Network / OD yield, bid-price, EMSR | S7 | n/a | REJECTED | n/a |
| M53 | Tree ensemble (RF / GBM) | any | many | REJECTED | n/a |
| M54 | Neural network | any | many | REJECTED | n/a |
| M55 | Hybrid statistical + ML | any | many | REJECTED | n/a |
| M56 | Agent-based market simulation | any | many | REJECTED | n/a |

Counts by role: SHIP 13 · SHIP-BEHIND-ADAPTER 3 · SPECIFIED-NOT-IMPLEMENTED 14 · REJECTED 26. Total 56.

---

## 3. One record per model

Field order is fixed, per §2.D: target, form, parameters, data, cost, what it buys, failure mode, evidence,
validation, role with reason.

### S1 · latent transaction-price estimation (T1, T1′)

#### M01 · Face-value rule

- **Target:** S1.
- **Form:** `V̂ = faceValueLamports`. Zero parameters, zero data.
- **Params:** 0.
- **Data:** the ticket's own `faceValueLamports`.
- **Cost:** O(1).
- **Buys:** a numeraire, and the only price the contract carries before any resale. Nothing else.
- **Failure:** face is the organiser's own choice, it is the denominator of the ratio being measured, and it is
  endogenous to the decision (`02-e` §4.1, `01-b` §4.1). `01-a` §2 records the published pattern: primary tickets
  are priced below secondary clearing value, with resale averaging about 41% above face on the roughly 5% of
  tickets that resell (A-cited, Leslie & Sorensen). A rule that returns face inside a market that trades above face
  is a systematic downward bias presented as a value, and it is invisible because it is a unit.
- **Evidence:** A-cited against the claim that face is a market value; C for the endogeneity argument.
- **Validation:** n/a. Rejected at identification, not on performance: nobody measures how wrong it is because it
  is not an estimate.
- **Role:** **REJECTED** as a value model. Its two admissible uses are not this row: face is the unit `markupBps`
  is defined over, and the J≤1 cold-start rung is face plus exact cap and fee arithmetic (M07's degradation, `02-e`
  §3.5). Revival: never as an estimate; it becomes informative only if an event's resale transactions sit at face,
  which is a measurement, not a policy.

#### M02 · Fixed-markup rule

- **Target:** S1, S7.
- **Form:** `V̂ = face · (1 + k)`, one global `k`; equivalent to a constant bps over face for every ticket, tier and
  horizon.
- **Params:** 1.
- **Data:** face, and one pooled `k`.
- **Cost:** O(1) per ticket.
- **Buys:** a level, which is exactly what M05 and M06 cannot deliver without a normalisation; that is why it is
  tempting.
- **Failure:** three independent ones. (i) The pooled mean markup is a **censored** statistic wherever the cap
  binds, biased down by construction, and it is a **selected** statistic because resold tickets are better seats
  (mean seat-quality percentile 0.61 against 0.50, A-cited, `01-a` §6). (ii) The published dispersion is wide and
  two-sided: about 25% of resold tickets above +67% and 26% below face in the concert data `01-a` §2 reports. A
  constant cannot represent that. (iii) The path is not constant in `τ`: within-seller prices decline as the event
  approaches, on the published dummies, by a proportional 36% to 43% over an 81-day window (`02-a` §3.3, arithmetic
  on Sweeting's table; A-cited inputs, C for the fit). A fixed markup therefore misstates by a factor that grows
  monotonically toward the deadline, which is when most sales happen.
- **Evidence:** A-cited against constancy in `τ`; C for the censoring argument.
- **Validation:** n/a.
- **Role:** **REJECTED**. It is M03 with the tier and horizon variation removed, so it is dominated by M03, which
  is itself rejected. Revival: none. Recorded because a "just use the average markup" rule is the first thing a
  builder reaches for, and the three reasons above are the answer.

#### M03 · Population-mean rule

- **Target:** S1.
- **Form:** `V̂ = face · (1 + m̄)` where `m̄` is the mean or median markup of a stratum (event, or event × tier),
  applied to every ticket in it.
- **Params:** 1 per stratum.
- **Data:** any recorded sales in the stratum.
- **Cost:** O(n) one pass, integer arithmetic. This is exactly what `ticketpath/core/markup.py::mean_int` and
  `median_int` already do over `ResaleStats`.
- **Buys:** an exactly computable, assumption-free descriptive statistic of what transactions actually fetched. As a
  description it is true, and it is the only thing in this file that already runs.
- **Failure:** (i) it is a mean of **cleared** prices, so it describes the success branch only and says nothing about
  the 95% of tickets that never transact (`01-a` §5). (ii) It is censored at the cap and, where the cap binds, the
  recorded price is the ceiling and the value is above it. (iii) It ignores `τ`, and the mean observed markup is a
  late-window object: under the fitted shape, half of resales fall inside 26 days of the event, where prices are
  roughly 82% to 85% of the start-of-window level (`02-a` §7.1). (iv) It has no width, so it cannot be wrong out
  loud.
- **Evidence:** C for the selection and censoring argument; A-cited for the timing and the seat-quality selection.
- **Validation:** UNVALIDATED as a predictor. Its arithmetic is exact, its interpretation is not.
- **Role:** **REJECTED** as an engine output. It is retained in one place: `02-c` §5.1(6) requires a no-model
  baseline (the empirical rate by stratum) for any calibration or skill claim, and that baseline is this statistic.
  A model that cannot beat it has no reason to exist, so the number must be printed in evaluation reports and never
  in a price quote. Revival: as an output only if the event has no `τ` variation in its sales at all.

#### M04 · Uncensored hedonic regression (OLS)

- **Target:** S1, S4.
- **Form:** `y = log(price/face)`, `y = μ + α_tier + δ_event + s(τ) + γ'X + ε`, `ε ~ N(0, σ²)`, fitted by least
  squares on observed sales.
- **Params:** `|tier|` dummies (or one per tier) + `|event|` + knots + k covariates + 2. Order 10 to 30 for a small
  panel.
- **Data:** sale rows with `priceLamports`, `faceValueLamports`, `tierId`, `startsAt`, plus ticket attributes fixed
  at issue. No listing fields.
- **Cost:** normal equations or Householder QR on a 10³ × 20 design: milliseconds, stdlib.
- **Buys:** tier and event differentials and the shape of `τ`, which is most of what the value model needs.
- **Failure:** on a capped event the response is not `y` but `min(y, log(1+cap))`. Fitting the observed sample
  without a censoring term biases the `τ` slope **toward zero** (the cap removes the top of the distribution
  preferentially near the deadline, `01-c` §4.3) and attributes cap hits to whatever covariate correlates with a hot
  event. The bias is largest on the events where value is highest, which is the ranking inversion `01-a` §3 warns
  about.
- **Evidence:** C.
- **Validation:** superseded. Correct only in the regime where the cap never binds, which is a fact about an event
  that must be tested, not assumed (`02-a` §8.8's stratified check).
- **Role:** **REJECTED** as the general model, superseded by M05, which is this model plus the observation rule. Not
  deleted from the registry because the difference between the two is the whole argument for M05.

#### M05 · Censored hedonic (Tobit with a known, event-varying bound, fitted by EM)

- **Target:** S1 primarily; S3 for the path (the same model evaluated at a different `τ`); S4 for tier
  differentials. Not S5: a hedonic coefficient is not a sale probability.
- **Form:** latent `y* = μ + α_tier + δ_event + s(τ) + γ'X + ε`, observed `y = y*` when `y* ≤ c_e =
  log(1 + resalePriceCapBps/10⁴)`; a point mass at `c_e` when the cap binds (censored regime), or no observation
  beyond `c_e` (truncated regime), depending on Q3. EM: E-step `E[y* | y* > c] = μ̂ + σ̂·λ((c−μ̂)/σ̂)` with `λ` the
  inverse Mills ratio, M-step plain least squares.
- **Params:** tier effects, event effects, `τ` spline coefficients, k covariates (transferRestricted,
  requiresVerifiedWallet, tier size, city), plus `μ, σ`. A few dozen at most; the exact count is fixed by the first
  real dump.
- **Data:** sale rows of the censused ticket population. `resalePriceCapBps` per event. No listing fields. Needs one
  operator answer that is not a field: **Q3**, whether the cap is enforced on-chain (truncation) or on the ask
  (censoring), because the two give different likelihoods (`01-c` §4.3) and the first diagnostic on real data
  distinguishes them by whether a mass at exactly `cap_bps` exists.
- **Cost:** under D2, EM with `statistics.NormalDist` for `cdf`/`pdf`/`inv_cdf`: about 120 lines, each iteration is one
  least-squares solve at O(np² + p³) with p in the tens. Milliseconds per iteration, tens of iterations. Monotone,
  no line search.
- **Buys:** a predicted relative value for **every** ticket, including tickets that never traded, which is the one
  thing no other identified model does (`01-c` §4.6). Plus the residual distribution that feeds the interval and the
  value signal the optimiser consumes. It is the engine's headline output.
- **Failure:** (i) no level. `α` and `δ` are identified relative to a normalisation, so the output is a
  quality-adjusted relative price (see conflict C2, where `01-b` §4.1 and §4.4(i) disagree about whether primary
  sell-through supplies the anchor). (ii) tier-level only: no seat coordinates, so it prices a tier and not a seat,
  and the published evidence says seats are where the within-event variation is (`01-a` §6). (iii) normality of the
  latent on the log scale is untestable inside the censored region. (iv) it is a forecasting object, and its
  coefficients are **not** willingness to pay; using them as elasticities is the commonest error in applied pricing
  work (`01-c` §4.1).
- **Evidence:** C for the method; B for treating a policy ceiling as a known censoring bound (standard Tobit
  structure, new application); A-cited that seat quality is the dominant within-event axis; D for the claim that the
  surface is stable enough across an event's life to be usable out of sample.
- **Validation:** **class C by argument, UNVALIDATED against any market.** Test: an event-level walk-forward in log
  space, scored by MAE and by `02-c` §5.1's prequential protocol, against M03 and M18. No number is quoted.
- **Role:** **SHIP.** It needs none of the four missing fields, it is the only component that prices a cold ticket,
  and its identifying assumption (quality fixed at mint) is exactly true for a ticket rather than approximately true.
  Ship it with the normalisation printed beside the number.

#### M06 · Repeat-sales index (Bailey-Muth-Nourse)

- **Target:** S1 as an index of changes; S3 for the path; and it is the independent check on M05.
- **Form:** pairs on the same `mintAddress`; response `log p_{i2} − log p_{i1}`; regressors a sparse set of time-cell
  dummies. The ticket fixed effect differences out and is never estimated. `log p_{i2} − log p_{i1} = Σ_k β_k
  (D_{i2k} − D_{i1k}) + u_i`.
- **Params:** one per time cell (monthly at first, because pairs are few).
- **Data:** tickets with at least two priced sales. Nothing else. No listing fields.
- **Cost:** normal equations in the number of time cells, which is small: O(pairs · cells + cells³), tens of cells.
  Trivial.
- **Buys:** a price-change index with no distributional assumption and different identifying variation from M05, so
  disagreement between the two is the diagnostic for composition bias. Also the cleanest available answer to "how
  much has this tier's resale price moved", which the contract's `priceSeries` only approximates.
- **Failure:** (i) **no level.** It identifies ratios only (`01-b` §4.1). (ii) Selection: pairs come from the liquid
  subset of an already small subset (`01-a` §5 puts resale at about 5% of tickets), and repeat-sales indices inherit
  that bias, concentrated in short-hold pairs (Gatzlaff & Haurin 1997; Steele & Goy 1997). (iii) Composition drift
  across time cells. (iv) Ageing: remaining life shrinks monotonically, so the index mixes a calendar effect with an
  age effect (the T2 problem).
- **Evidence:** C for the method and for the "quality fixed at mint" argument, which is stronger here than in real
  estate: no renovation, no depreciation, no redevelopment. A-cited and B-cited for the selection literature.
- **Validation:** class C by argument, UNVALIDATED. Test: does its time-cell path agree with M05's `δ_event` and
  `s(τ)` on the same window. Disagreement is the result, not a nuisance.
- **Role:** **SHIP.** Cheap, needs no missing field, and it is the only internal check on the model that produces the
  headline number. Ship it with the pair sample described and never present it as a price.

#### M07 · Empirical-Bayes cold-start band (normal-normal partial pooling)

- **Target:** S1, the cold-start case T1′.
- **Form:** within `y_ij = log(p_ij/f_ij) ~ N(θ_j, σ_j²)`; between `θ_j ~ N(μ, τ²)`. Shrinkage
  `B_j = τ²/(τ²+s_j²)`, `θ̂_j = B_j y_j + (1−B_j) ȳ(τ)`. A genuinely new event has `s² = ∞`, so `B = 0` and the point
  estimate is the pooled mean; `τ²` enters only the interval.
- **Params:** `μ`, `τ²`, plus a 601-point grid over `τ`. Fixed a priori: the shrinkage weight when estimated
  shrinkage is unavailable (0.5), the covariate entry order.
- **Data:** `J ≥ 2` events with resale activity. At `J ≤ 1` it degenerates to a prior and must be declared as one.
  `log face`, tier count, sell-through state and city enter one at a time, only once `J ≥ k+3`.
- **Cost:** closed form plus a 1-D grid, two bisections and the regularised incomplete gamma function for the χ²
  quantiles (about 40 lines of series and continued fraction). Milliseconds.
- **Buys:** the only honest thing a cold-start event can be given: a band on the event's mean log price ratio, whose
  width **is** the deliverable (`02-e` §1). It reports the between-event variance as a sensitivity range from the
  method-of-moments estimate, the χ² upper limit and a declared floor, and it never prints a point without its width.
- **Failure:** (i) it is a prior wearing a posterior's clothes below about five events: at `J = 5` the 95% interval
  for `τ²` spans a factor of 23, at `J = 2` a factor of 5100 (`02-e` §4.4, computed). (ii) Exchangeability of events
  is declared, not testable, and the direction of its failure is known and bad: events with no resale activity are
  not a random sample, so estimating `τ²` only on active events biases it down and makes the cold-start band too
  narrow, which is why zero-sale events must sit inside the variance estimate (`02-c` §6.2). (iii) The target is a
  ratio to face, and face is the organiser's decision, so the band cannot choose a primary price (`02-e` §4.1,
  §6.2(4)).
- **Evidence:** C. The shrinkage algebra is exact; the exchangeability is D.
- **Validation:** class C by argument, UNVALIDATED. Test: once `J ≥ 5`, leave-one-event-out on squared log error
  against (a) the arithmetic mean of the others and (b) face value, with the comparison's own uncertainty reported.
- **Role:** **SHIP.** It is the cold-start answer and it degrades to face plus cap arithmetic at `J ≤ 1`. Ship the
  band, the label and the sensitivity table together; the label must change weight the moment the event has its own
  sales.

#### M08 · Cap-bound one-sided estimator

- **Target:** S1 and S6: a lower bound on value, a lower bound on the willingness-to-pay survival function, and the
  rationed quantity.
- **Form:** no likelihood. Three exact objects. (i) The cap-binding indicator and the cap-hit share by `τ` bucket:
  `ĥ(τ) = #(markupBps = cap_bps)/#(sales at τ)`. (ii) The one-sided statement: a sale at the cap implies `V ≥
  p_0(1+c)`. (iii) Across events with different `cap_bps`, such statements at different points trace a lower bound on
  the WTP survival function at each cap level. Under Q3's option A a sale at the cap also identifies the ask exactly
  on that stratum (`02-c` §2.5), which is a genuine single known point on the price axis.
- **Params:** 0, or 2 if the cap-hit share is smoothed in `τ`.
- **Data:** `markupBps`, `resalePriceCapBps`, `faceValueLamports`, `startsAt`. Nothing missing.
- **Cost:** O(sales). Integer arithmetic.
- **Buys:** the only part of the record that speaks about value **above** the observed prices, and the only level
  anchor anywhere in the data (`02-a` §1.9). It is what lets the engine say "this is worth at least the ceiling"
  rather than "this is worth the ceiling".
- **Failure:** (i) it is one-sided: the location of the latent tail above the cap is not identified and EVT cannot
  recover it (M13). (ii) At a binding cap the market clears by speed and allocation, so the hazard there measures
  buyer arrival under rationing, not acceptance (Bulow & Klemperer 2012; Glaeser & Luttmer 2003). (iii) The
  instrument is **cross-event only**: `resalePriceCapBps` is one number per event and the cross-tier ceiling moves
  exactly in proportion to face value, so there is no within-event identifying variation (`01-c` §1.4(1), correcting
  `01-b` §4.4(ii)), and cross-event variation is confounded with everything else that differs between events. (iv) It
  cannot be exercised on the fixtures at all: no fixture sale lands exactly on a cap (`00-data-situation.md` §2).
- **Evidence:** A-cited for the structural fact that at a binding cap the recorded price is the ceiling; B for
  rent-seeking under a price control; C for the bound algebra.
- **Validation:** class C by argument for the bound, UNVALIDATED for any magnitude. Test: the mass at exactly
  `cap_bps` and the cap-region velocity relative to below-cap velocity, on the first real dump. Together these also
  answer Q3.
- **Role:** **SHIP.** It is a bound and a diagnostic, not a price; it is the cheapest honest statement the engine can
  make about its best inventory, and it is the first diagnostic a real dataset should produce.

#### M09 · Latent markup with a leakage probability

- **Target:** S1, S6.
- **Form:** `M*` latent markup, observed as `min(M*, cap)` with a leakage probability `q(cap, event)` that a
  transaction moved off the recorded rail (side payment, wallet handoff, bundling). `Pr(observed m | M*) = (1−q)
  ·1[m = min(M*,c)] + q·(off-rail)`. `q` is estimated from dark tickets and bundled listings.
- **Params:** the M05 parameter set plus `q(cap, event)`, so 1 to 2 more per event stratum.
- **Data:** everything M05 needs, **plus** a way to observe `q`: dark-ticket detection (a ticket that redeems from a
  wallet that never received a transfer row) and evidence of bundling. Neither is in the contract.
- **Cost:** the same EM as M05 with a mixture weight; still stdlib, still milliseconds.
- **Buys:** if it worked, the sign and size of the cap correction. `01-a` §3 and §6 argue the recorded markup is
  biased down exactly where demand is strongest, and this is the model that would quantify that.
- **Failure:** `q` is unidentified from the ledger, and the existing leakage channels are class D with a named test
  (`00-adversarial-review-phase1.md` error 14 raises the class inflation of exactly this claim). A model whose only
  new parameter is unobservable is a prior with a mechanism attached. Worse, the sign of the average correction is
  not established, so the model could as easily widen the bound the wrong way.
- **Evidence:** D for the mechanism; C for the algebra.
- **Validation:** UNVALIDATED and currently unfalsifiable on this record. Test: `delistReason = cap_blocked` counts,
  the excess mass just below the cap, dark-ticket rate as a function of event heat, and a cap-free comparison set.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Mathematically written, deliberately not coded: the parameter it exists to
  estimate has no observable counterpart, and implementing it would put an unidentifiable number inside the headline
  model. Revival: a leakage observable of any kind.

#### M10 · Hybrid hedonic + repeat-sales (stacked)

- **Target:** S1.
- **Form:** the Meese-Wallace hybrid: a repeat-sales equation and a hedonic equation estimated jointly, with the
  repeat-sales pairs weighted against the single-sale observations, sharing the time-cell coefficients.
- **Params:** the union of M05 and M06's, minus the double-counted time terms.
- **Data:** the same as M05 and M06 together.
- **Cost:** a weighted least-squares solve in the stacked design: still small, still stdlib.
- **Buys:** in principle, efficiency: the hedonic carries the cross-section and the pairs carry the change, and each
  corrects the other's bias (Pakes 2003 on matched-model bias; Meese & Wallace 1997 on hybrid accuracy).
- **Failure:** it is only worth building if the two components can be **compared** first. Stacking two estimators
  whose disagreement is the diagnostic hides the diagnostic inside one number. It also inherits both components'
  failures, and it does not create a level.
- **Evidence:** C. B-cited from the real-estate hybrid literature, whose home market has repeated sales at a density
  this one does not.
- **Validation:** UNVALIDATED. Test: the hybrid against each component on an event-level walk-forward; ship it only
  if it beats both on the same folds.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** The two components ship separately (M05, M06) and their disagreement is
  more informative tonight than their average. Revival: M05 and M06 both fitted on real data, with a measured
  disagreement to resolve.

#### M11 · Nearest-neighbour event comparables

- **Target:** S1, cold start.
- **Form:** `V̂_new = weighted mean of exp(θ̂_j)` over the `K` nearest events by observed attributes, distance
  declared (e.g. Gower), weights fixed.
- **Params:** 0 estimated; `K` and the distance are choices.
- **Data:** `J` comparable events, and the attributes needed to define "near". Event category, on-sale timing and
  venue capacity are **all absent** from `lib/types.ts` (`02-e` §2.2, measured), so the metric would be built from
  city, organiser and face value.
- **Cost:** O(J) per query.
- **Buys:** nothing M07 does not buy more honestly, and it produces a spread without a model.
- **Failure:** (i) it cannot define its own distance metric from the contract, because the attribute that would carry
  most of the information is missing. (ii) Its reported spread is post-selection: the neighbours are drawn from the
  events that had resale, which are disproportionately the hot ones. (iii) A nearest-neighbour estimate has no
  mechanism, so when it is wrong there is nothing to inspect.
- **Evidence:** C for the pathology; B-cited for the general nearest-neighbour selection problem in `02-e` §3.3.
- **Validation:** UNVALIDATED and not worth validating before M07 has been tried.
- **Role:** **REJECTED** as a reported number. Kept as a support diagnostic: if the neighbourhood's own values are
  wildly dispersed, the pooling in M07 is being asked to do something it cannot. Revival: an event-category field
  plus enough events for neighbours to be distinguishable.

#### M12 · Matrix completion / collaborative filtering

- **Target:** S1, cold start.
- **Form:** complete a tickets × events price matrix by low-rank factorisation under a missing-at-random assumption.
- **Params:** rank × (tickets + events).
- **Data:** a matrix of prices with ignorable missingness.
- **Cost:** alternating least squares, feasible in stdlib, but pointless: see the failure.
- **Buys:** in principle, cold-start imputation from co-movement across events.
- **Failure:** the missingness **is** the phenomenon. An event with no resale history is not a randomly unobserved
  cell; it is an event nobody wanted to resell, and treating the two as the same is the error the identification
  report exists to prevent. The matrix is also almost entirely empty by construction, at roughly 5% resale (`01-a`
  §5), so the factorisation would be fitting noise in a sparse corner.
- **Evidence:** E.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.7). Revival: a dense price matrix, which a 5%-resale market will not produce.

#### M13 · Extreme-value tail above the cap

- **Target:** S1, S6.
- **Form:** a generalised Pareto tail fitted to exceedances over a high threshold, used to extrapolate the latent
  value distribution above the ceiling.
- **Params:** 2 to 3 (threshold, shape, scale).
- **Data:** tail observations above the threshold. The cap guarantees there are none above the ceiling.
- **Cost:** cheap; irrelevant.
- **Buys:** the one thing every other row cannot give, the location of the latent right tail, which is exactly what a
  binding cap hides.
- **Failure:** it is a **support** problem, not a small-sample problem: EVT estimates a tail from tail observations
  and the observation rule deletes them. The asymptotic regime the theory needs is one the data can never enter.
  There is also a modelling error waiting: for a perishable good with a hard deadline the economically relevant tail
  is the **left** one, the risk of not selling, not the right tail of value.
- **Evidence:** C for the rejection.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.5). Revival, and it is a genuinely cheap idea: an event with
  `resalePriceCapBps = null` (the schema allows it) and enough volume to put observations in the tail, used
  deliberately as a measurement device for what the cap hides. That belongs in the Phase 2 plan as a comparison
  group, not as an EVT model.

### S2 · current market-state estimation

#### M14 · Joint mark-time intensity ξ(p, τ)

- **Target:** S2.
- **Form:** a nonparametric estimate of the rate of transactions **per ticket-day at each markup, as a function of
  time-to-event**. Binned: `ξ̂(b_p, b_τ) = #(sales in cell) / exposure in cell`, with exposure the ticket-days at risk
  in that cell. This is the joint distribution of (time, price) over cleared transactions, normalised by exposure.
- **Params:** 0. The bins are a resolution choice, and the contract already fixes one axis in six markup buckets.
- **Data:** `sale` rows with `priceLamports`/`markupBps`, `occurredAt`/`slot`, `startsAt`, and the censused population
  for exposure. Nothing missing.
- **Cost:** O(rows) binning. Milliseconds.
- **Buys:** the identified and displayable answer to "how much trade happens, at what price levels, and when". It is
  the honest replacement for a price-response chart in the interface (`02-c` §2.4, §7). It is also the object behind
  the contract's `priceSeries` and `markupDistribution`.
- **Failure:** it is **not** a demand curve: a locus of realised prices where sellers chose the prices traces the
  intersections of supply and demand and neither curve (Working 1927). Two further traps. Reading it as `P(sale | p)`
  is the single error this whole registry exists to prevent. And the revenue-management temptation, that the average
  hazard at the average ask is the hazard at that ask, is false because hazards are not linear in price.
- **Evidence:** C for identification under the Aalen argument on the observed filtration; C for the Working critique.
- **Validation:** class C by argument, UNVALIDATED against a market. The estimator has no free parameter to be wrong
  about, which is why it is the safest row in the file; its *interpretation* is what needs the label. Test: nothing
  to validate beyond the exposure audit (`02-c` §3.8 step 9).
- **Role:** **SHIP.** It is identified, it needs no missing field, it costs one pass over the rows, and it is the only
  price-indexed object the record supports. Label it "transaction price distribution, not a demand curve" in the
  code, in the API and on the screen.

#### M15 · Local-level state-space model (scalar Kalman filter and smoother)

- **Target:** S2, and S3 for the interval between trades.
- **Form:** `log V_i(t+1) = log V_i(t) + η`, `η ~ N(0,q)`; observed `y_ik = log V_i(t_ik) + ε`, `ε ~ N(0,r)`. Scalar
  Kalman filter and smoother; `q/r` estimated or declared.
- **Params:** 2 (`q`, `r`), plus a tier prior for `log V_i(issued)`.
- **Data:** tickets with at least two priced observations, to say anything at all; one observation per ticket reduces
  it to the prior.
- **Cost:** about 30 lines, O(observations) per ticket.
- **Buys:** a price at any `τ`, not only at trade instants; an explicit, falsifiable statement of how much the price
  moves between trades; a natural way to pool across tickets within a tier.
- **Failure:** `q` is a prior in disguise. The smoothed path between two trades is an interpolation whose accuracy is
  a function of `q/r`, so the honest label is "declared interpolation", not "estimated price" (`01-c` §7.4). With one
  to four observations per ticket, `q/r` is barely identified, and `02-a` §8.9 is blunt about the consequence: it
  reduces to "martingale plus a drift that is not identified".
- **Evidence:** C.
- **Validation:** UNVALIDATED. Test: does the smoothed path beat the martingale anchor (M18) out of sample on second
  sales. Until it does, the martingale is the shipped path.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Written down, deliberately not coded: it is M18 plus an unidentifiable
  drift, and shipping the drift as if it were estimated is exactly the overclaim the programme forbids. Revival: a
  measured `q/r` from tickets with three or more observations, or a prequential loss for M18 that a smoothed path
  clearly beats.

#### M16 · Change-point guard (CUSUM / PELT)

- **Target:** S2.
- **Form:** a sequential test for a break in a monitored statistic (e.g. mean markup, cap-hit share, transaction
  rate): `CUSUM_t = max(0, CUSUM_{t−1} + (x_t − μ_0 − k))`, alarm at `h`.
- **Params:** 1 to 2 (`k`, `h`).
- **Data:** a time-ordered series of whatever is monitored. Available.
- **Cost:** O(n), a few dozen lines.
- **Buys:** a guard, not an estimate. `01-a` §6 names regime switches that would silently invalidate any pooled
  estimate: cap enforcement on or off, and the US all-in pricing rule effective 2025-05-12. Both are cheap to test
  for and expensive to miss. It is also the honest exception to "series too short": the cap-crossing date `d*` is a
  change point that is directly observable rather than detected.
- **Failure:** on short series it alarms on noise. It detects a break in a statistic, not a cause, so a break in the
  mean markup can be a demand shift, a cap change, or a change in who is reselling.
- **Evidence:** C.
- **Validation:** UNVALIDATED, and it does not need validating: a guard's false-positive cost is a warning.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED** as a *model*, per `01-c` §10 F1, which demotes it. It belongs in the
  pipeline as a diagnostic that prints "a regime break is possible here", not as an estimator. Revival of a
  modelling role: none.

### S3 · future resale-price forecasting

#### M17 · Deadline-convex path model, one parameter

- **Target:** S3.
- **Form:** `ŷ(τ) = ȳ_anchor + θ̂[log(1+τ) − log(1+d_a)] + ω·β̂_e·(τ − d_a)`, with `y = log(price/face)` and `τ` in days
  to the event. `θ̂` is the single estimated structural parameter; `ȳ_anchor` and `d_a` are the median log relative
  price and median days-to-event of the last `K = 5` sales in the tier (or event, per the ladder); `ω ∈ {0,1}` is a
  declared normalisation, both reported.
- **Params:** 1 estimated (`θ`), plus one nuisance slope per event discarded under `ω = 0`. Fixed a priori, not
  fitted: `K = 5`, `δ = 1` day, the shrinkage weight 0.5, the horizon bands.
- **Data:** `sale` rows with `priceLamports`, `faceValueLamports`, `tierId`, `startsAt`. `n_e ≥ 4` sales per event,
  at least 5 days of spread in `d`. No listing fields.
- **Cost:** a 2×2 solve per event plus an inverse-variance average; closed form, no iteration, no inversion beyond
  2×2, no randomness. Microseconds per event.
- **Buys:** curvature, which is the only structural feature of the path the data identifies, and a fallback ladder
  that degrades by the number of prior sales in the event (≥20, 5 to 20, 1 to 5, 0). It is the "how it moves" claim.
- **Failure:** (i) the **linear trend is not identified**: within one event, `τ` and calendar time are the same
  variable up to a constant, and across events age + cohort = period has an exact linear dependency. `ω` is a
  normalisation, and reporting one number for the slope without it is overclaiming. (ii) The measured decline in the
  literature is a **seller-side** object measured on listings that failed and were relisted; our record is
  transactions that cleared, which is the opposite conditioning, so the magnitudes are not comparable (`02-a` §4.4,
  the report's most consequential methodological point). (iii) The published record disagrees with itself in the last
  48 hours: two peer-reviewed studies, two markets, opposite signs. (iv) Under a binding cap the observed path is
  `min(latent, cap)`, which biases the measured decline toward zero.
- **Evidence:** A-cited for the direction and the shape: within-seller prices decline as the event approaches
  (Sweeting 2012), and the deadline-convex form fits his table with one exponent of 0.133 to 0.164 stable across
  demand and price strata (`02-a` §3.1 to §3.3, arithmetic on his printed coefficients). C for the fit. D for any
  transfer to this market. C for the trend non-identification.
- **Validation:** class C by argument, UNVALIDATED. Pre-registered decision rule: if `ω = 0` does not beat the
  martingale M18 out of sample by a margin that survives the per-event dispersion of `θ̂_e`, ship M18 instead. Test:
  event-level walk-forward, MAE in log space by horizon band, with the two leakage boundaries enforced (no later
  event, no later sale in the same event).
- **Role:** **SHIP.** One estimated parameter is not modesty, it is the identification result. Ship it with `ω`
  printed, the anchor audited, the discarded-event count reported, and the martingale as the alternative.

#### M18 · Martingale anchor / random-walk benchmark

- **Target:** S3.
- **Form:** `ŷ(τ') = ȳ_anchor`, the median log relative price of the last `K` sales in the tier, flat in `τ`. The
  forecast is a martingale with a measured residual band read off empirical quantiles, not fitted.
- **Params:** 0 estimated.
- **Data:** at least one prior sale in the tier or event; below that it becomes M07's cold-start path.
- **Cost:** O(K log K) for the median. Trivial.
- **Buys:** the null the theory itself supplies (competitive sellers plus strategic buyers predicts a martingale, as
  Sweeting notes) and the benchmark M17 must beat to be worth shipping. It is also a defensible product: a flat
  forecast with a measured band that says "we do not know the direction, and here is how wide our ignorance is".
- **Failure:** it cannot express the decline the literature documents, so it is systematically wrong in the last
  week if the decline is real here. It has no mechanism, so when it is wrong there is nothing to inspect.
- **Evidence:** C; A-cited for the theory that a martingale is the right null in this kind of market.
- **Validation:** class C by argument, UNVALIDATED. It is the benchmark, so it is validated only in the sense of
  being measurable on real data when it arrives.
- **Role:** **SHIP.** Not as the preferred model but as the pre-registered fallback and the scoring baseline. If M17
  does not beat it, it becomes the product. A declining trend that is not there is worse than a flat one.

#### M19 · ARIMA / SARIMA

- **Target:** S3.
- **Form:** `φ(L)(1−L)^d y_t = θ(L) ε_t` on a price or log-price series.
- **Params:** `p + d + q` (+ seasonal terms).
- **Data:** a series with many observations per unit.
- **Cost:** feasible in stdlib for small orders, but irrelevant.
- **Buys:** nothing here that M17 does not buy with less data: it models a series, and there is no series.
- **Failure:** a ticket has 1 to 4 observations in its life and an event-tier series has a handful. This is not a
  data-volume objection that more data fixes; it is the identification objection that the series has no level
  (`02-a` §8.9). Differencing removes the only thing there is.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`02-a` §8.9). Not the same as excluded in principle: `01-c` §10 F8 defers time-series
  models until the hedonic's `τ` basis fails an out-of-sample prequential test against a simple state-space
  alternative. Revival: that failure, plus a per-unit series long enough to estimate anything.

#### M20 · GARCH / volatility model

- **Target:** S3, S6.
- **Form:** conditional variance recursion on returns, `σ²_t = ω + α a²_{t−1} + β σ²_{t−1}`.
- **Params:** 3+.
- **Data:** a return series.
- **Cost:** feasible; irrelevant.
- **Buys:** a time-varying interval for the path.
- **Failure:** 1 to 4 points per ticket is not a return series. What is actually wanted, a width that varies with
  horizon, is available directly by reporting residual dispersion by horizon band, which is the object `02-a` §8.9
  recommends and which needs no model.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED.** The useful content is the residual band per horizon, which ships inside M18 and M17.

#### M21 · GAM / spline in time-to-event, as a separate model

- **Target:** S3.
- **Form:** `y = μ + Σ_j f_j(x_j) + s(τ)` with `s` a piecewise-linear spline with knots concentrated in the final
  fortnight.
- **Params:** one per knot plus penalties.
- **Data:** enough sales per event to place and identify the knots.
- **Cost:** a penalised least-squares solve, feasible.
- **Buys:** flexible curvature in `τ`.
- **Failure:** per event it is unidentifiable curvature by another name: `02-a` §8.9 recommends a single-parameter
  basis `log(1+d)` because the data will not support knots, and a spline with more free parameters than the shape
  evidence can distinguish is a way of not stating the shape. Note the conflict (C1): `01-c` §4.6 does recommend a
  spline in `τ` inside the pooled censored hedonic. Both are recorded.
- **Evidence:** C.
- **Validation:** UNVALIDATED; the shape itself is A-cited only in the one-parameter form.
- **Role:** **REJECTED** as a standalone model. It is a basis choice inside M05, where pooling across events supplies
  enough sales to place knots, and it must then be reported as unidentifiable curvature beyond the knot support. It is
  not a separate entry, which is why Phase 4's "GAM" line is answered here and nowhere else.

#### M22 · Quantile regression (censored, by IRLS approximation)

- **Target:** S3, S6.
- **Form:** `min_β Σ ρ_τ(y_i − x_i'β)` for the τ-th quantile, with Powell-type censoring correction at the cap.
- **Params:** one coefficient vector per quantile.
- **Data:** the same design as M05, plus enough observations below the censoring point at each quantile.
- **Cost:** exact quantile regression is a linear program, and D2 has no LP solver. Iteratively reweighted least
  squares is the standard approximation and is an approximation with no guarantee of exact quantile optimality, so
  the honest alternative under D2 is to bin the sample by M05's fitted value and take empirical quantiles within
  bins: exact within the bin, cruder in resolution, and explicit about which (`01-c` §8.3).
- **Buys:** conditional quantiles robust to the asymmetric cap mass at the top, and a path for capped events below
  the cap mass. It is the only interval route that does not lean on the normality assumption M05 makes.
- **Failure:** the IRLS approximation may not reach the quantile it claims; censored quantile regression on a sample
  with a mass point at the bound is fragile exactly where the cap binds; and with few sales per event the higher
  quantiles are noise.
- **Evidence:** C for the method; C for the approximation caveat.
- **Validation:** UNVALIDATED. Test: empirical coverage of the binned quantiles on a walk-forward, which is a
  describable comparison and not a claim about the market.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Written down, deliberately not coded: no LP solver under D2, no data to
  fit, and M05's residual quantiles plus `02-c` §8.3's binned empirical quantiles deliver the interval tonight.
  Revival: an LP solver, or a demonstrated need for a tail quantile the binned approach cannot resolve.

#### M23 · Recursive least squares with a forgetting factor

- **Target:** S2, S3.
- **Form:** `β̂_t = β̂_{t−1} + K_t(y_t − x_t'β̂_{t−1})` with `K_t` the rank-one gain and a forgetting factor `λ`.
- **Params:** 1 (`λ`) plus the coefficient vector.
- **Data:** a stream of observations arriving in order, with resolved outcomes.
- **Cost:** O(p²) per update, a few dozen lines. This is the cheapest legitimate adaptation in the file.
- **Buys:** coefficients that track a changing market without refitting from scratch, which is what a live deployment
  would need.
- **Failure:** adaptation without a prequential loss is unmonitored drift, and the forgetting factor is a choice that
  determines how fast the model forgets a real regime change versus treats noise as one. With no live stream it has
  nothing to update.
- **Evidence:** C (Plackett 1950 rank-one update).
- **Validation:** UNVALIDATED, and it cannot be otherwise before deployment.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: there is no stream, and an adaptive estimator with no
  monitoring is worse than a frozen one because its outputs move for reasons nobody can reconstruct. Revival: a live
  feed plus the prequential scorer M44 running beside it.

### S4 · demand estimation

#### M24 · Tobit primary sell-through demand bracket

- **Target:** S4, and S7 as an input.
- **Form:** per tier, demand at the primary price is censored at `totalSupply`: a sold-out tier is censored ("demand
  met or exceeded supply at this price"), an unsold tier is a point ("demand equals issued while supply remained").
  `D*_k = x_k'β + ε`, observed `D_k = min(D*_k, totalSupply_k)` with a censoring indicator. Inverted, because here
  availability is observed and demand is not (Conlon & Mortimer 2013).
- **Params:** 2 per tier in the simplest form (a location and a scale), plus cross-tier and cross-event coefficients.
- **Data:** `faceValueLamports`, `issuedCount`, `totalSupply` per tier; `Event.status`. **Gate:** two operator
  answers, not fields. Whether `issuedCount` means **sold** or **minted**, which the contract does not say and which
  destroys the inference if it means minted (`02-e` §10.1, measured absence); and a timestamped inventory series,
  because `issuedCount` and `Event.status` are snapshots with no capture time, so using them as a predictor at time
  `t` is look-ahead bias (`01-c` §3.6).
- **Cost:** EM for a Tobit, exactly as in M05: stdlib, milliseconds.
- **Buys:** the only demand object identified anywhere in this schema (`01-b` §4.4(i), restated as the review's error
  5: the level is set-identified from primary sell-through, not unidentified). A sold-out tier at face implies
  excess demand at face and hence resale at or above face; an unsold tier implies the marginal buyer's willingness to
  pay is at or below face. That is a **sign**, not a level, and it is evidence-backed.
- **Failure:** (i) it identifies a demand **bracket**, and one-sided statements at observed prices, not a demand
  curve. (ii) Uniform primary pricing within a tier is assumed; a discount or a fee between face and the transaction
  price breaks it. (iii) The snapshot problem: as a predictor it is a look-ahead violation until the series is
  timestamped. (iv) `Event.status` transitions are untimestamped, so on-sale start, sell-out and hold-back release
  times are unknown and primary sell-through velocity is not observable. (v) Cross-event comparison is confounded
  with everything else that differs between events.
- **Evidence:** B-cited (demand under incomplete availability; the auction and repricing results). UNVALIDATED for
  any functional form.
- **Validation:** class B by cited method, UNVALIDATED on this platform. Test: resale prices on sold-out against
  not-sold-out events, after the `issuedCount` question is answered.
- **Role:** **SHIP-BEHIND-ADAPTER.** Implemented and switched off, gated on `issuedCount` semantics plus a timestamped
  inventory series (not on the four listing fields). This is the only route to the primary question that does not
  require an experiment (`02-c` §10 item 6), so it should exist in code before the data arrives.

#### M25 · Structural demand model (Rosen's second stage, BLP-type random coefficients)

- **Target:** S4.
- **Form:** recover the demand and supply primitives from the equilibrium hedonic locus, by instrumenting the
  endogenous price with attributes or cost shifters and inverting market shares for mean utilities.
- **Params:** many: a random-coefficient distribution plus supply-side parameters.
- **Data:** observations on **demand and supply**, buyers' choices among simultaneous alternatives, and declining
  buyers. We observe offered bundles and accepted purchases, and nothing about anyone who declined.
- **Cost:** a fixed-point inversion plus a GMM objective: needs a numerical stack. Out under D2 regardless.
- **Buys:** elasticities and marginal willingness to pay, which is what the primary optimum actually needs.
- **Failure:** not identified. A single market's transactions do not separate demand from supply (Rosen 1974; Brown
  & Rosen 1982; Ekeland, Heckman & Nesheim 2004, whose positive result requires data on both sides and is only up to
  an affine transformation anyway). Separately, selection on issuance (N4 in `02-c`): the population in the ledger
  bought at the price actually charged, so varying the primary price changes who is in the sample and no amount of
  secondary data repairs it.
- **Evidence:** C, and the theory cuts against us.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.11, `01-b` §4.4). Revival: bid-side data, a randomised price arm, or a second
  market observed simultaneously.

#### M26 · Auction private-value inversion (Guerre-Perrigne-Vuong)

- **Target:** S4.
- **Form:** invert observed bids through the equilibrium first-order condition to recover the private-value
  distribution, nonparametrically, from bids and bidder counts.
- **Params:** nonparametric (kernel bandwidths), or a parametric restriction.
- **Data:** bids and the number of bidders. The contract has neither. The four listing fields do not help: they are
  about asks, and this needs bids.
- **Cost:** two-step nonparametric inversion with kernel density estimation on a 2-D support. Writable in stdlib in
  principle, numerically fragile in practice, and an event with tens of transactions is far below where a
  nonparametric density means anything.
- **Buys:** a value distribution, which is the only thing that would make a demand curve or an optimal mechanism
  computable.
- **Failure:** there is no bid data, so there is nothing to estimate. `01-c` §5.1 also makes the positive point that
  a settled resale is a posted-price transaction, so the correct structural frame is sequential search with posted
  prices, which needs the same two unidentified objects.
- **Evidence:** C for the theory; D for every implication drawn for this engine.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.3). Revival: any record of bids or offers, or an auction arm.

#### M27 · Optimal auction design as a fitted object

- **Target:** S4, S7.
- **Form:** `max` expected revenue over mechanisms given the prior on values (Myerson 1981); the reserve price is a
  functional of that prior.
- **Params:** the prior.
- **Data:** the value distribution. Absent, and M26 is how it would be obtained.
- **Cost:** the mechanism itself is closed form given a prior; the prior is the problem.
- **Buys:** nothing as a model. As a **decision**, it is the highest-value fork in the file: Budish & Bhave find that
  primary auctions substantially improved price discovery and nearly eliminated arbitrage profits in their setting
  (A-cited via `01-a` §4), which would dominate any pricing engine's payoff.
- **Failure:** without the prior there is no optimal mechanism to compute. And note conflict C5: "roughly doubled"
  revenue (mechanism change) and "about 3.4%" (reprice the top 10% at the median resale price) are two published
  class-A answers to the same commercial question, differing by more than an order of magnitude.
- **Evidence:** C for the theory; A-cited for the empirical phenomenon; D for the transfer.
- **Validation:** n/a.
- **Role:** **REJECTED** as a fitted object, retained as the prescriptive fork that goes to the operator
  (`01-c` §5.4, §10.4). Revival: a value prior (M26) plus an operator willing to change the selling mechanism.

#### M28 · Gaussian process / kriging seat-quality price surface

- **Target:** S1, S4.
- **Form:** a GP prior over `price(section, row, seat)` with a kernel; posterior mean as the price surface.
- **Params:** kernel hyperparameters.
- **Data:** seat coordinates. Absent (Gap 3), and the field is an open operator question (Q1).
- **Cost:** `O(n³)` linear algebra plus hyperparameter optimisation: forbidden by D2.
- **Buys:** if seats arrived with a numerical stack, the natural model for the within-event price surface, which is
  where the published evidence says the variation lives.
- **Failure:** three independent reasons: no numerical stack, no seat coordinates, and of order ten squared
  observations per event means the posterior would be prior-dominated and would look like a confident surface while
  being a statement about the kernel.
- **Evidence:** C for the rejection.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.6). Revival, stated as a future specification: seat coordinates plus a
  permitted numerical stack. At that point it becomes the first thing to build for within-tier pricing.

#### M29 · Synthetic control, difference-in-differences, event studies

- **Target:** S4, as a route to a causal price effect.
- **Form:** compare treated and untreated units under a parallel-trends or donor-pool assumption.
- **Params:** few.
- **Data:** untreated comparison units with a parallel trend, or an exogenous timestamped shock.
- **Cost:** cheap. Irrelevant.
- **Buys:** a causal price response without an experiment.
- **Failure:** there is neither. Any two events differ in demand, venue, city and organiser at once, and no policy
  change is recorded with a timestamp. The cap's cross-event variation is the closest thing to an instrument and it
  is confounded with whatever else differs between events (`01-c` §1.4(1)).
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.10). What is not rejected is the one design that identifies the causal price
  response: **randomised price variation**, on listings (an ask arm) or on primary tiers. That is money given up on
  purpose, so it is the operator's decision, and it should be put to him as a costed proposal because every
  price-response claim otherwise stays class D forever.

### S5 · sale-probability estimation

#### M30 · Piecewise-exponential composite intensity with exposure offset, competing risks and a cure component

- **Target:** S5, and S2 for the rate's shape in `τ`.
- **Form:** on a `τ` grid of `K` buckets, `λ_i(t) = exp(α_b + x_i'β)` within bucket `b`, likelihood
  `ℓ = Σ_{b,c} [D_{bc}(α_b + x_c'β) − E_{bc} e^{α_b + x_c'β}]`, which is exactly a Poisson log-likelihood with
  offset `log E_{bc}` and no constant. `E_{bc}` are **exposure** days at risk. Cause-specific fits for
  sale / transfer / redeem / revoke, combined into `p̂_sale = (λ̂_sale/λ̂_·)(1 − e^{−Λ̂})` and
  `F̂_sale(τ) = Σ Ŝ p̂_sale`. Cure mixture `S(t|x) = π(x) + (1−π(x))S_u(t|x)` with `π` estimated, interval reported,
  not tested against a point null.
- **Params:** `K` bucket intercepts (about 8) + `p` covariates (about 10 to 30 for the full set) + `π`. Under 40
  columns.
- **Data:** the censused ticket population: `issue` rows, `issuedAt`, `redeemedAt`, `revoke`, `startsAt`/`endsAt`,
  and per-ticket attributes. **Exposure is observed and largely valid.** Two caveats that must be printed with the
  fit: ticket-days during which resale was disabled or the mint was `transferRestricted` are in the denominator but
  are not at risk (the current flag has no history), and wallet-to-wallet self-dealing inflates the numerator with a
  known upward direction.
- **Cost:** aggregate to cells, then Newton-Raphson: `O(iter · (K+p)³)` with `K+p ≲ 40`, milliseconds per fit,
  memory is the cell table and not the expanded ledger (`02-c` §3.8).
- **Buys:** three identified objects. The composite transaction rate per ticket-day and its functionals (cumulative
  incidence, time to first transaction, share that ever transacts); the cause-specific exit intensities and therefore
  the competing-risks cumulative incidence; and an upper bound on the never-offered share. Plus two genuinely new
  empirical objects: the **gap-time distribution between custody hops** and repeat-reseller behaviour, which `01-a`
  §5 records that no published dataset measures.
- **Failure:** three that matter. (i) **It is not a sale hazard and not a probability at a price.** The estimand is
  `s(t|x)·E[λ(t|p) | offered, t, x]`, a composite of offering and buying, so `1−exp(−λh)` is the chance a ticket
  like this transacts, not the chance a listed ticket sells. Calling it a sale intensity is defensible algebra and a
  bad name (`02-c` §2.1). (ii) The coefficients are **associations**, attenuated relative to individual-level effects
  under unobserved heterogeneity, and never per-ticket effects. (iii) The `τ` clock and ticket age are collinear
  within an event unless issuance is staggered, so an age effect may not enter naively beside `τ`. (iv) If
  `transferRestricted` is not actually enforced and off-ledger key handoff is common, the ledger is a **sample** of
  transfers rather than a census, and every rate below is a rate for the observable subset only (`01-c` §12 item 5).
  That is a conditioning question nothing in the contract can answer.
- **Evidence:** C for identification (Aalen multiplicative-intensity argument on the observed filtration), C for the
  Poisson equivalence, C for cloglog being the exact grouped-data link and logit the small-hazard approximation,
  C that redemption must be a competing risk, C that `π` is identifiable with a terminal point and is an upper bound
  on never-offered. D/UNVALIDATED that it describes ticket resale timing. The cure fraction's support: the
  fixture-based comparison that once supported it is not admissible (`00-adversarial-review-phase1.md` error 2), so
  the mechanism is argued from class C identifiability and nothing else.
- **Validation:** class C by argument, UNVALIDATED. Test: rolling-origin holdout on completed events, prequential
  Brier with IPCW, against the raw stratum rate (M03). Also: two-origin stability across successive event cohorts,
  because one holdout window cannot distinguish a good model from a lucky one.
- **Role:** **SHIP.** This is the "will it transact" component, it is identified, it needs no missing field except the
  `slot` clock rule, and it is the most comfortably stdlib family in the programme. Ship it with the seven
  "must not conclude" sentences of `02-c` §3.9 attached to the output.

#### M31 · Listing-episode discrete-time hazard with a price response (Specification B)

- **Target:** S5, the actual price-conditional sale probability. This is the target D3 says is a data requirement.
- **Form:** unit is a listing episode `j` on ticket `i` with entry `L_j`, exit `D_j`, reason `r_j`, ask `p_j`, and
  `z_j = log(1 + markup_j)`; `λ_j(t) = λ_0(τ(t))·exp(x_i'β + γ z_j + δ w_j(t))` with `w_j` the number of other
  listings in the tier (depth). Piecewise-constant baseline on the `τ` grid, likelihood as in M30 with episode
  exposure. Price response entered **nonparametrically in the primary form**: `Σ_m θ_m 1{z_j ∈ B_m}` over markup
  bins, with `θ_m` by `τ` bucket as the surface to inspect. Target
  `P̂(sold within h | listed today at p, τ_0, x) = 1 − exp(−e^{x'β+γz+δw} Σ_k λ̂_{0k}Δ_k)`, reported as a
  competing-risks quantity (sold versus withdrawn).
- **Params:** `M` markup bins × `K` buckets for the primary form (tens), plus 4 structural terms (ask, depth, `τ`,
  intercept) and `p` covariates.
- **Data:** the four listing fields, with revisions recorded as separate episodes: `listPriceLamports`, `listedAt`,
  `delistedAt`, `delistReason ∈ {sold, withdrawn, expired, cap_blocked}`. The content requirement matters as much as
  the field: asks must be recorded **for listings that never sell** and **per revision**. A listing table that logs
  only completed sales reproduces today's defect in a new schema.
- **Cost:** same solver as M30, same cell table. Milliseconds. "The solver does not change" is the engineering answer
  to what the listing table costs.
- **Buys:** `γ`, the price response, and with it the product's headline sentence; the depth effect; the eventual
  sale-versus-withdrawal split; the rationing quantity at the cap; and the `cap_blocked` stratum, which is the
  observably recorded form of excess demand at the ceiling.
- **Failure:** four, all of which must be printed. (i) **Even with the four fields, the fitted object is the hazard
  given the ask the seller chose**, so it is a prediction under the observed ask policy, not `E[sale | we set p]`.
  The ask carries the seller's private information about value. Reporting the first as the second is the error this
  row exists to prevent. (ii) Identification of `γ` needs ask dispersion within `(event, tier, τ)`; zero dispersion
  is rank deficiency. (iii) Omitting the time effect inflates `|γ|`, within-tier quality attenuates it, and the net
  sign of the confound is unknown without seat coordinates. (iv) It does not identify the **primary** optimum: the
  secondary hazard and primary demand are different objects, and selection on issuance remains (N4).
- **Evidence:** C for identification as a conditional association (Cox 1972; Andersen & Gill 1982), with a causal
  reading additionally requiring the no-unobserved-confounding assumption A2; C for the collinearity arithmetic;
  B for the cap stratum measuring arrival speed under rationing.
- **Validation:** class C by argument, UNVALIDATED, and **not exercisable on the fixtures** even in principle because
  no fixture sale lands on a cap and no fixture has a listing panel. Test: the ask-dispersion diagnostics, then a
  prequential IPCW Brier on a temporal holdout, then a randomised ask arm or the cap instrument for the causal
  reading.
- **Role:** **SHIP-BEHIND-ADAPTER.** Implemented, registered, switched off until the four fields exist. This is the row
  that answers "probability at a price", and it answers it only through that adapter.

#### M32 · Constant-elasticity markup hazard (Specification B, reporting form)

- **Target:** S5.
- **Form:** M31 with `η_j = ... + γ z_j`, `z = log(1 + m)`. `γ` is the elasticity of the sale hazard with respect to
  the ask: a 1% higher markup multiplies the hazard by about `(1.01)^γ`.
- **Params:** 1 (`γ`), plus the rest of M31.
- **Data:** same gate as M31.
- **Cost:** same as M31.
- **Buys:** one interpretable number, which is what an operator can act on and what a UI can state: "a 10% higher ask
  cuts the per-day sale rate by roughly a third" when `γ = −4`.
- **Failure:** it is a functional commitment. It should be imposed only if M31's nonparametric surface has iso-hazard
  contours that are straight lines in `(z, τ)`. If the interaction is large, the honest output is a `γ(τ)` surface and
  not a scalar. And a monotone curve fitted by maximum likelihood will look monotone whatever the truth, so the sign
  is not evidence of anything.
- **Evidence:** C.
- **Validation:** class C by argument, UNVALIDATED. Test: likelihood-ratio against the nonparametric form, plus the
  `τ` interaction.
- **Role:** **SHIP-BEHIND-ADAPTER.** Same gate as M31, and it is the *reporting* form of the same fit, never the
  primary specification.

#### M33 · Choke-price hazard

- **Target:** S5.
- **Form:** `η = ... + log(1 − p/p*)`, `p* > p` a parameter: a finite ask at which the sale hazard is zero.
- **Params:** 1 (`p*`), plus the rest of M31.
- **Data:** same gate as M31, and enough asks spread over the range to locate a point where the hazard reaches zero.
- **Cost:** same solver; the likelihood is non-monotone in `p*` near the boundary, so it needs a grid or bounded
  search rather than pure Newton.
- **Buys:** the most commercially interpretable object in the family ("the market will not pay above `p*`") and a
  direct feed into the primary optimiser.
- **Failure:** it is a strong functional commitment on the least-identified part of the surface (the upper tail of
  asks), and it puts a singularity in the parameter space exactly where the data are thinnest. With a binding cap,
  the observed ask range stops at the ceiling, so `p*` may be beyond the support and driven entirely by the form.
- **Evidence:** D.
- **Validation:** UNVALIDATED. Test: it must be checked against the nonparametric surface (M31) and retained only if
  the surface supports a finite choke point.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Written down, deliberately not coded: it is a third check, and shipping it
  before the first two have data would ship a shape with no evidence behind it. Revival: M31 and M32 fitted on a real
  listing panel with ask dispersion near the ceiling.

#### M34 · Cox proportional hazards

- **Target:** S5, as a check.
- **Form:** `λ(t|x) = λ_0(t) exp(x'β)`, estimated by partial likelihood with Breslow or Efron ties; Schoenfeld
  residuals for the proportional-hazards check.
- **Params:** `p`.
- **Data:** the same risk set as M30, and with the four fields the same episode structure as M31.
- **Cost:** a `k × k` Newton iteration per step, `k = p`: tens of lines, milliseconds. Schoenfeld residuals are a
  by-product.
- **Buys:** a semi-parametric estimate of `β` with no baseline shape assumption, and the standard diagnostic for
  proportional hazards. It is the natural robustness check on M30 and M31.
- **Failure:** the clock. `occurredAt` is ISO-8601 at unspecified granularity while `slot` is strictly monotone, so
  any duration derived from `occurredAt` alone can come out zero or negative, and a hazard model with negative
  durations does not fail loudly (`02-c` §3.4). Coarse and unequal timestamps are exactly what the grouped-data
  estimator was built for, so the discrete-time form is forced and Cox is the check rather than the primary.
- **Evidence:** C.
- **Validation:** UNVALIDATED. Test: Schoenfeld residuals on the first real fit, and agreement of `β` with M30's
  cloglog estimate.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: it is a check, it needs the data the primary
  estimator needs, and there is nothing to check yet. Revival: a fitted M30, which is when a check becomes useful.

#### M35 · Fine-Gray subdistribution hazard

- **Target:** S5.
- **Form:** a proportional-hazards model for the cumulative incidence function of the event of interest, keeping
  competing events in the risk set with inverse-probability-of-censoring weights.
- **Params:** `p`.
- **Data:** M30's data plus a censoring model for the weights.
- **Cost:** about sixty lines with IPCW on the risk set: implementable in stdlib but not routine, and it must be
  checked against a simulated competing-risks dataset before it is trusted.
- **Buys:** a direct model of the cumulative incidence, which is the quantity the product reports, rather than a
  conversion from cause-specific hazards.
- **Failure:** the weights depend on a censoring model that is itself estimated, so its misspecification enters the
  answer. It adds nothing over the cause-specific construction when censoring is purely administrative, which is the
  benign case here.
- **Evidence:** C.
- **Validation:** UNVALIDATED, and it cannot be validated without the SIM study that does not exist.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: the cause-specific route (M30) produces the same
  reported quantity, and this adds an estimated nuisance weight for no identified gain tonight. Revival: a SIM study
  showing the cause-specific conversion is materially biased on realistic censoring patterns, or a product question
  that needs the subdistribution directly.

#### M36 · Shared frailty hazard (event-level random effect)

- **Target:** S5.
- **Form:** `λ_i(t) = λ_0(τ) exp(x_i'β + u_{e(i)})`, `u_e ~ N(0, σ²)` or gamma. `E[λ|x] = λ_0 e^{x'β + σ²/2}`.
- **Params:** `p + σ²`.
- **Data:** `J ≥ 2` completed events per stratum, with zero-transaction events included.
- **Cost:** gamma is conjugate (closed form); lognormal needs quadrature, which is hand-codable but non-conjugate
  (`01-c` §7). Feasible, not trivial.
- **Buys:** honest width in the presence of event-level heterogeneity, and the machinery the cold-start update M38
  needs to state its variance.
- **Failure:** `σ²` is identified from the number of groups, not the number of sales, so with few events it is prior
  dominated and the shrinkage weight is itself noisy (`02-c` §6.2). Estimating `σ²` only on events with transactions
  biases it down and makes intervals too narrow, which is the specific failure mode to guard against.
- **Evidence:** C.
- **Validation:** UNVALIDATED. Test: between-event variance computed including zero-transaction events; if it
  dominates, the pooled mean is a poor predictor and the deliverable becomes a wide declared band.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: the empirical-Bayes version (M07) and the
  gamma-Poisson update (M38) deliver the cold-start behaviour without a random-effects likelihood, and the full
  version needs groups that do not exist. Revival: `J ≥ 5` completed events per pooling stratum.

#### M37 · Full hierarchy over sale ⊂ tier ⊂ event ⊂ category

- **Target:** S1, S4, S5 together.
- **Form:** a multi-level model with partial pooling at each level; `θ_ijk = μ + v_category + u_event + w_tier + ε`.
  Dispersion pooled fully, location pooled partially, the cap never pooled because it is observed.
- **Params:** fixed effects plus one variance component per level.
- **Data:** groups at every level. The scarce parameter is not the event effect, it is the **tier** effect, which is
  estimated from a handful of sales with many tiers (`01-c` §7.3).
- **Cost:** non-conjugate versions need quadrature or MCMC. Feasible in hand-written form, not shippable tonight.
- **Buys:** the level where pooling actually pays is the tier, not the event: cold start is the dramatic use, the tier
  level is the valuable one.
- **Failure:** every stratification divides the number of groups, and `τ` is estimated from groups. A declared
  exchangeability partition does all the work and is untestable. If the within-group likelihood is not censored at
  the cap, the hierarchy pools biased means whose bias is an event-level covariate, so the bias enters at the same
  level as the parameter being pooled and is invisible in the output (`01-c` §7.2c).
- **Evidence:** C.
- **Validation:** UNVALIDATED. Test: the EB version against the full posterior, on the same folds, and only then ask
  whether the extra structure matters.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED** (`01-c` §10 F3 defers non-conjugate random effects until the EB version has
  been compared against it). Revival: that comparison, plus groups.

#### M38 · Gamma-Poisson cold-start intensity update

- **Target:** S5, cold start.
- **Form:** `λ ~ Gamma(a,b)`; observing zero transactions over exposure `E` has likelihood `e^{−λE}`, so the posterior
  is `Gamma(a, b+E)` and the predictive intensity is `λ̂_cold = (a/(b+E))·(λ_0(τ)e^{x'β}/λ̄_prior)` rather than the
  prior mean `a/b`. The predictive is the gamma-mixed (negative-binomial-like) one, which is **wider** than the
  Poisson interval at the same mean.
- **Params:** 2 (`a`, `b`).
- **Data:** exposure `E` per event, which the ledger supplies; and the population baseline from M30.
- **Cost:** `math.lgamma` and arithmetic. Trivial.
- **Buys:** the correct treatment of "an event with no resale history": the zero is **evidence**, so the estimate
  shrinks with the observed exposure. An event 200 days out with no activity and an event one week out with none are
  different statements, and this is the formula that distinguishes them.
- **Failure:** the update is on the **composite** intensity, so it says "tickets like this do not transact much", not
  "nobody is listing". The two are not separable without the listing panel. And the scope statement matters: for the
  price level the cold-start estimate is the population mean (M07), while for the sale intensity it is the population
  mean updated by the observed zero (`02-c` §6.2's reconciliation with `02-e`).
- **Evidence:** C (conjugate posterior).
- **Validation:** class C by argument, UNVALIDATED. Test: backtest on held-out events with zero early activity,
  comparing the predictive log score against the population mean.
- **Role:** **SHIP.** It is closed form, identified, and it is the specific mistake that most cold-start treatments
  make. Ship it with the wider-than-Poisson interval, because overstating precision where the product is most tempted
  to state a confident number is the failure this row prevents.

#### M39 · Ridge / Firth separation guard

- **Target:** S5, as a numerical guard on every Newton fit.
- **Form:** add `(κ/2)‖β‖²` to the log-likelihood (ridge), or use Firth's penalised likelihood `ℓ*(β) = ℓ(β) +
  (1/2)log|I(β)|`, when a `τ` bucket has zero events and drives its intercept to `−∞`.
- **Params:** 1 penalty (or none, for Firth).
- **Data:** none beyond the fit itself.
- **Cost:** one line in the objective and one term in the Hessian.
- **Buys:** a fit that does not silently diverge, and a reported sensitivity of the `τ → 0` estimate to the penalty.
  `02-c` §3.8(7) requires this explicitly, together with a printed condition number per fit.
- **Failure:** the penalty is a prior on the coefficients, so it must be **reported** rather than buried, and its
  value changes the answer exactly in the sparse cells where the answer is least stable. Firth is better behaved but
  not assumption-free.
- **Evidence:** C by construction.
- **Validation:** not applicable in the usual sense; the guard's correctness is arithmetic and is checked by the
  likelihood being finite with an all-zero bucket.
- **Role:** **SHIP.** It is not a model in its own right and it is not optional: without it, empty cells produce
  infinite intercepts and the hazard near the event is meaningless.

#### M40 · Full posterior sampling (HMC / NUTS, Stan, PyMC)

- **Target:** S5, S1.
- **Form:** Hamiltonian Monte Carlo on the joint posterior of a non-conjugate hierarchical or censored model.
- **Params:** the model's, plus sampler tuning.
- **Data:** as the underlying model.
- **Cost:** needs a numerical stack. Under D2 this is not a cost, it is an impossibility.
- **Buys:** exact posterior inference where conjugate and EB approximations are unavailable.
- **Failure:** no stack exists on this machine and none may be installed (D2), and no model here is genuinely
  non-conjugate *and* decision-relevant enough to justify it.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.9). Revival: a permitted numerical stack plus a model whose answer changes the
  decision under a full posterior but not under the EB approximation.

#### M41 · Contextual bandit over prices

- **Target:** S5, S7.
- **Form:** a policy mapping context to price, learned by Thompson sampling or UCB while accumulating reward.
- **Params:** model-dependent, plus the exploration schedule.
- **Data:** a **pricing-decision log**: for each tier and price change, the timestamp, the price chosen, and the rule
  or propensity that chose it. That is a fifth data request this programme has not made and should, because it is
  cheap to record now and impossible to reconstruct later.
- **Cost:** the sampler is forty lines; the data requirement is the blocker.
- **Buys:** a policy with a regret guarantee, in principle.
- **Failure:** five requirements, four of which fail. The decisive one is arithmetic: the platform sets one price per
  tier and records no rule and no propensity, so the logging policy has probability 1 on one action and 0 on every
  other, which makes off-policy evaluation not hard but **undefined** (Dudík et al. 2014). The reward is an
  untimestamped snapshot (`issuedCount`, `Event.status`), so it cannot be attributed to a decision time. The action
  moves the outcome: the cap is `face·(1+c)`, so raising the primary price loosens the ceiling and the observation
  rule moves with the action. And exploration costs real money, which is the operator's decision, not a model's.
- **Evidence:** C for the negative result (positivity is a theorem-level requirement); E for any suggestion that a
  learnable price-response loop exists here.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §6.4, §10 F6). Its one admissible descendant is the bandit over **models** (M45),
  where no money is at risk, and the prequential discipline (M44). Revival: operator-authorised randomised price
  variation. If that happens, the right design is a randomised ask or price arm analysed as an experiment, not a
  bandit, because a properly randomised arm identifies the price response without the exploration scaffolding.

### S6 · prediction uncertainty

#### M42 · Conformal prediction

- **Target:** S6, and only S6.
- **Form:** split conformal: fit on a training split, compute nonconformity scores on a calibration split, take the
  `⌈(n+1)(1−α)⌉`-th smallest score as the radius; coverage at least `1−α`, at most `1−α+1/(n+1)` when scores are
  almost surely distinct.
- **Params:** 0 (an order statistic).
- **Data:** a calibration set of scored, unresolved units, exchangeable with the test unit, with outcomes on **both**
  branches. Stronger than the four listing fields, which give exposure and ask but still record a price only on the
  success branch.
- **Cost:** fifteen lines. Trivially implementable and unusable, which is the clearest case in the programme where
  those are different words.
- **Buys:** a finite-sample coverage guarantee under exchangeability, which nothing else in the file offers.
- **Failure:** three assumptions, three failures. No calibration set exists. Calibration and test points are not
  exchangeable because the only scored observations are sales, so calibration is conditioned on "this ticket sold"
  while the test ticket may not sell (Barber, Candès, Ramdas & Tibshirani 2023). And the deepest one: a ticket that
  never resells has **no resale price**, so an unconditional prediction-set statement has no referent for most of the
  population, at roughly 95% of tickets.
- **Evidence:** C for the coverage theorem; D at best for the claim that a ticket price interval can ever be
  conformally valid, and arguably not well posed.
- **Validation:** n/a.
- **Role:** **REJECTED** as an implementation. Its value is a paragraph: it states exactly what a defensible interval
  would require (`1/(n_s+1) ≤ α` per stratum, a uniformly sampled scoring population, outcomes on both branches) and
  exactly which assumption this observation set violates. Building it now would demonstrate competence in a method
  the data cannot support. Revival: the stratified scoring design of `01-c` §8.2, which is a data-schema decision and
  must be made before launch because it cannot be reconstructed afterwards.

#### M43 · Isotonic calibration

- **Target:** S6.
- **Form:** fit a monotone nondecreasing map `g` from predicted probability to observed frequency, minimising squared
  error under the ordering constraint (pool-adjacent-violators).
- **Params:** one step per distinct predicted value, so `n` in the worst case.
- **Data:** a forward, held-out, resolved validation set with outcomes on both branches.
- **Cost:** PAV is O(n) and ten lines.
- **Buys:** in principle, a monotone recalibration of the sale indicator, which is the one thing M44 can score
  honestly on the full population.
- **Failure:** (i) there is no held-out validation set, and an **in-sample** reliability curve is worthless here for
  an exact algebraic reason: with one baseline parameter per time cell, the reliability curve is the score equation
  plotted, so it must look calibrated and says nothing (`02-c` §5.2). (ii) Monotonicity cannot remove selection: the
  biases that matter are the cap truncation and the sold-only conditioning, and neither is a monotone distortion of
  the predicted probability. (iii) Fitting the map on the same period it is applied to is interpolation within a
  period, which is not what deployment does.
- **Evidence:** C for the algebra.
- **Validation:** n/a.
- **Role:** **REJECTED.** It is the right *object* to want and the wrong thing to build without a forward holdout.
  What replaces it tonight is M44's proper scoring plus descriptive rates with exact denominators and the censoring
  audit. Revival: two forward holdout origins with resolved outcomes.

#### M44 · Prequential proper-scoring evaluation

- **Target:** S6.
- **Form:** score every prediction before seeing the next observation with a proper scoring rule (Brier, log score),
  accumulate, and compare models by their cumulative score; for a survival target, the IPCW Brier at pre-declared
  horizons; report the reliability-resolution decomposition for the binary sale indicator.
- **Params:** 0.
- **Data:** a forward stream of predictions and outcomes. On the current contract the **sale indicator** population is
  complete, so this is the one calibration task that is fully available the day data exists; any **price**
  distribution is not, because every scored observation is conditioned on "sold at this price".
- **Cost:** a running average. Tens of lines.
- **Buys:** the only admissible calibration evidence in the programme, the discipline that makes M17's pre-registered
  decision rule executable, and the comparator that stops a model being shipped because it converged.
- **Failure:** it needs resolved outcomes; it cannot score a horizon that has not elapsed; and it will tempt someone
  into reporting an in-sample number if the temporal boundaries are not enforced in code, so the leakage rules must
  sit in the same module.
- **Evidence:** C (proper scoring rules; prequential evaluation).
- **Validation:** class C by argument. It is not a claim about the market, so it needs no market validation; it needs
  a data stream. Until then it must print **NOT RUN** and no number.
- **Role:** **SHIP.** It is the honest replacement for every calibration claim the programme cannot make, and it is
  the module that makes every other row's decision rule enforceable.

#### M45 · Bandit over models / adaptive model selection

- **Target:** S6.
- **Form:** treat candidate forecasters as arms, score them by prequential loss, and allocate trust adaptively
  (Thompson sampling over model weights, or exponential weights).
- **Params:** 0 to a few.
- **Data:** a prediction stream plus the same resolved outcomes M44 needs.
- **Cost:** a few dozen lines.
- **Buys:** model selection that adapts without a held-out set, which is the only bandit in this programme whose
  action costs no revenue.
- **Failure:** with no stream it selects nothing, and an adaptive selector whose loss is not monitored can lock onto
  a model that was briefly lucky. It is model selection dressed as adaptive control and should be labelled as such.
- **Evidence:** C.
- **Validation:** UNVALIDATED.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: the scorer (M44) must exist and produce a loss history
  before a selector can select, and shipping the selector first would be an algorithm without a null. Revival: six
  months of prequential losses from at least three candidate models.

### S7 · primary-price optimisation

#### M46 · Static grid optimiser with the fee wedge and the boundary rule

- **Target:** S7.
- **Form:** `Π(p) = Σ_k N_k [q_k(p)(m_k(p_k) + u_k) − u_k] + ρ·E[T(p)] − F`, maximised on a price grid because `Π` is
  not guaranteed unimodal. The static first-order condition collapses the whole fee stack into one scalar,
  `c** = b + (1+β)(f − a − u)/(1−φ)`, giving `(P − c**)/P = 1/ε(P)`, equivalently `P = c**·ε/(ε−1)`. Three cases: an
  interior optimum; a sell-through boundary, which is the default; and a degenerate no-maximum case.
- **Params:** configuration, not estimates: `c**`'s components (`b, β, f, φ, a, u`), `q_min`, and `η` or a scenario
  set. The engine estimates nothing here; it reports which parameters it had to assume.
- **Data:** `faceValueLamports`, `totalSupply`, `issuedCount` per tier; plus operator configuration for the fee stack,
  the ancillary margin and the empty-seat cost. The sale probability `q_k(p)` is **not identified**, which is why the
  output is a range and a rule.
- **Cost:** a grid sweep, `O(G · M)` for `G` candidate prices and `M` demand scenarios: microseconds for a few hundred
  prices.
- **Buys:** the only honest form of the fourth claim. Three derived results survive an unidentified demand function:
  an ad-valorem fee is **neutral** for the optimum, a per-unit fee is not and acts as marginal cost, and the cap is
  proportional so the band is scale-free and does not constrain the organiser's price at all. Plus the sharp
  observation that with `ε ≤ 1` near the observed price and `c** ≥ 0`, the recommendation is "raise", with the size
  set by the boundary: a defensible, evidence-backed statement available today.
- **Failure:** (i) it cannot produce a point optimum, because its demand input is not identified and selection on
  issuance means no counterfactual in the primary price is identified from secondary data. (ii) `u` (empty-seat cost,
  with its sponsor and strategic components) is unobservable and is the only term that makes the objective
  non-degenerate; drop it and a sold-out event has no interior optimum. (iii) If the organiser revises the primary
  price mid-sale, the whole dynamic-pricing question collapses, and the contract cannot tell us whether that happens
  (a cheap test: within-tier variation in `faceValueLamports` on the first real dump). (iv) The mechanism fork (M27)
  may dominate any price-level answer by an order of magnitude (conflict C5).
- **Evidence:** C for the objective, the wedge algebra (exact for any demand function) and the three cases; B-cited
  from tax incidence for proportional versus specific wedges; A-cited for demand being inelastic at observed prices
  and for mean capacity utilisation near 0.99, which is why the boundary case is the common one.
- **Validation:** class C by argument, UNVALIDATED. Its own falsification test: on the first real dump, does a
  recommended increase hold with sell-through, or does sell-through collapse? Until then it is a range with a
  sensitivity map, and `∂p*/∂η` printed.
- **Role:** **SHIP.** It is the decision layer, it needs no unidentified input to state a **bound**, and reporting the
  boundary rule as the recommendation when `c** ≤ 0` or `η` is absent uses only data the platform has.

#### M47 · Mean-CVaR risk-adjusted optimiser

- **Target:** S7, S6.
- **Form:** `max_p (1−λ)E[Π(p)] + λ·CVaR_α(Π(p))`, with `CVaR_α(X) = max_v {v − α^{-1}E[(v−X)^+]}`. For a finite
  equal-weighted scenario set it reduces to sorting the profits and averaging the worst `k = ⌈αM⌉`:
  `CVaR_α = −(1/k)Σ_{worst k}`.
- **Params:** 2 configuration (`λ = 0.5`, `α = 0.1` as defaults), plus the scenario set.
- **Data:** a scenario set for demand uncertainty. Declared, not estimated.
- **Cost:** `O(M log M)` per candidate price, a sort and a partial mean. Pure stdlib, no matrix algebra, no solver.
- **Buys:** the "risk-adjusted" half of the fourth claim, computed exactly on the empirical profit distribution, and
  the risk functional that suits this business because it penalises unsold inventory at the deadline rather than
  penalising upside.
- **Failure:** coherence is a property of the functional, not evidence that the scenarios are right: the scenario set
  is an assumption, so the output inherits an assumption the static optimiser did not need. The joint multi-tier
  version with capacity coupling and Wasserstein ambiguity needs a convex solver and is out under D2. And `λ`
  and `α` are choices the operator should make, not defaults an engine should bury.
- **Evidence:** C for the CVaR algebra and coherence; C for implementability.
- **Validation:** class C by argument, UNVALIDATED. Test: report it beside the risk-neutral answer on the same
  scenario set; if the two prices are the same, the risk term is not doing anything and the report should say so.
- **Role:** **SHIP.** It is closed form, cheap, and it is the only formulation that can carry risk **inside** the
  objective rather than bolted on afterwards, which is what the fourth claim asks for.

#### M48 · Mean-variance optimiser

- **Target:** S7.
- **Form:** `max_p E[Π(p)] − (γ/2)Var[Π(p)]`.
- **Params:** 1 (`γ`).
- **Data:** the same scenario set as M47.
- **Cost:** a second moment from the same scenarios. Trivial.
- **Buys:** the standard risk-return trade-off, familiar to any organiser.
- **Failure:** two reasons, neither about implementability. It penalises upside as well as downside, which is the
  wrong attitude for a pricing decision whose purpose is to move the upper quantiles. And its scale grows with `N²`,
  so `γ` must be re-tuned per event size, which makes it unportable across a tool that runs on events selling from a
  few thousand to tens of thousands of tickets.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`02-d` §4.3). Implementable, not recommended. CVaR is coherent (Artzner et al. 1999) and
  variance is not. Revival: none anticipated; coherence is not a matter of taste.

#### M49 · Reserve-price surface by backward induction (revenue management and stochastic control, entered once)

- **Target:** S7.
- **Form:** a finite-state MDP on `(inventory-remaining bucket, days-to-event bucket, cap-binding regime)`, about
  6 × 12 × 3 = 216 states, with backward induction over a 41-point price grid; the output is a reserve-price
  surface `p*(τ, inventory, cap-binding)`, reported as a **set** of surfaces over the demand-parameter box. Certainty
  equivalence: the latent value enters as the M05 prediction, its uncertainty as the state-space variance. The
  continuous-time HJB is the same problem and its discrete DP is the numerical solution, so the distinction is
  cosmetic as long as the grid is presented as an approximation.
- **Params:** one value per state per price, plus the demand parameters that are swept.
- **Data:** a state transition law (T2, identified only in curvature), the demand response (absent), and `u`.
  `delistReason` would give the terminal value `u` its first evidence.
- **Cost:** 216 states × 41 prices: microseconds per sweep in pure Python. This is the cheapest decision layer in the
  file.
- **Buys:** the only formulation that can express the primary-secondary feedback, and the only one whose output is
  the right shape for a set-identified problem: "above this price the recommendation is insensitive to the elasticity
  we cannot estimate; below it, it is not".
- **Failure:** four assumptions fail. The transition law is not identified. The state is only partly observed, so the
  true problem is a POMDP and certainty equivalence must be declared. The terminal condition is not `V(T,n) = 0` but
  `n·u` with `u` unobserved, which converts the last period into an optimal stopping problem with a free boundary
  rather than a clearance sale. And the action moves the environment, because the primary price sets the resale
  ceiling. The optimal-stopping form also needs the withdrawal option, which the record cannot observe today.
- **Evidence:** C for the method; B-cited for the phenomenon it explains (declining prices into expiry, negative
  final-period opportunity costs); D for the coupled primary-secondary formulation, which nobody has estimated.
- **Validation:** UNVALIDATED. Test: the measurable prediction that the endgame flattens when the owner's use value is
  high, which connects to the strongest empirical result in the ticket literature and is testable once
  `delistReason = withdrawn` exists. One free proxy for `u > 0` is already available: a `redeem` row whose
  `toWallet` equals the ticket's `issuedToWallet` is a lower bound on the attended fraction, hence on `u > 0`,
  though not an estimate of `u`.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: it is a decision layer that consumes two unidentified
  inputs, and a surface computed from a swept demand parameter would be a picture of the box, not of the market. The
  static optimiser M46 answers the same question tonight with fewer claims. Revival: M24 unblocked (so the demand
  bracket exists) plus `delistReason`, after which this is the first thing to build for the decision layer.

#### M50 · Multiproduct fluid relaxation

- **Target:** S7, the multi-tier problem.
- **Form:** the deterministic fluid limit of the `K`-tier pricing problem with a demand system `D_k(P_1..P_K)`, an ODE
  solvable by Euler or RK4, used as the relaxation of the stochastic multiproduct DP, which is
  `O(T·N₁·N₂·|P|²)` and must not be attempted.
- **Params:** one demand function per tier plus cross-elasticities.
- **Data:** a demand system. Absent. Tier substitution is an equilibrium object.
- **Cost:** a dozen lines for the ODE. Cheap; the inputs are the problem.
- **Buys:** the right frame for tiers, which do not share capacity but do substitute in demand; and it carries the
  measured multi-tier prize, about 5% average revenue gain from price discrimination across 21,120 concerts
  (A-cited).
- **Failure:** every tier's cross-price response is unidentified, so the fluid solution is a function of assumed
  elasticities. It is also a deterministic relaxation, so it cannot express the uncertainty that M47 exists to price.
- **Evidence:** C; A-cited for the size of the multi-tier prize.
- **Validation:** UNVALIDATED.
- **Role:** **SPECIFIED-NOT-IMPLEMENTED.** Deliberately absent: cross-tier elasticities have no data behind them, and
  the single-tier boundary rule is what the evidence supports. Revival: M24 unblocked, or a tier-level price
  experiment.

#### M51 · Overbooking, cancellation and no-show revenue management

- **Target:** S7.
- **Form:** oversell against expected cancellations, with a reaccommodation cost.
- **Params:** cancellation rate, reaccommodation cost.
- **Data:** a reservation that can be oversold and a second inventory to protect.
- **Cost:** trivial; irrelevant.
- **Buys:** nothing. A ticket token **is** the seat: there is no reservation that could be oversold, no
  reaccommodation cost, and a redeemed ticket is a consumed unit rather than a no-show the seller can resell.
- **Failure:** the market does not have the object the model prices. Note that the classical model explicitly extends
  to overbooking, which is why this rejection has to be stated rather than assumed.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.1). Revival: a product where a ticket is a revocable reservation rather than an
  owned token. That is a different business.

#### M52 · Network / origin-and-destination yield management, bid-price control, EMSR

- **Target:** S7.
- **Form:** allocate a shared capacity across fare classes with nesting and an arrival order; bid prices ration the
  shared resource; EMSR heuristics set protection levels.
- **Params:** per class, per leg.
- **Data:** shared capacity being rationed across classes.
- **Cost:** trivial; irrelevant.
- **Buys:** nothing here.
- **Failure:** each `TicketTier` has its own `totalSupply`, so tiers do not share capacity at all. The only cross-tier
  coupling is demand substitution, which is M50's problem and not network RM. Bid-price control and EMSR both presume
  the absent object.
- **Evidence:** C.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.2). Revival: a venue with one physical capacity sold under several price fences
  with upgrade rights, where a seat released from one class can serve another.

### Cross-cutting families

#### M53 · Tree ensemble (random forest / gradient boosting)

- **Target:** any, in principle.
- **Form:** an additive or bagged ensemble of axis-aligned splits, fitted to minimise a loss.
- **Params:** hundreds to thousands of nodes.
- **Data:** enough rows per event to support the capacity. An event's resale history is tens of transactions.
- **Cost:** no implementation exists in the stdlib and none may be installed (D2).
- **Buys:** nonlinearity and interactions without specification.
- **Failure:** the sample size is wrong by orders of magnitude, nothing in `01-a` or `01-b` suggests a nonlinearity
  worth fitting, and a tree cannot extrapolate outside the observed `τ` support, which is exactly where the last-week
  forecast lives. A censored or truncated response also needs a custom loss, so the off-the-shelf objective is the
  wrong one. An ensemble of martingales is a martingale.
- **Evidence:** D as a claim about their usefulness here, either way.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.6a). Rejected for this data volume, not in principle. Revival: a ledger large
  enough that a nonlinearity could be estimated, plus a permitted stack, plus a censored loss.

#### M54 · Neural network

- **Target:** any.
- **Form:** a parametric composition of nonlinear layers fitted by gradient descent.
- **Params:** thousands to millions.
- **Data:** far more than exists, and more than the platform will have for years.
- **Cost:** no stack under D2.
- **Buys:** nothing the identified object needs. The object is a smooth equilibrium locus estimated from a few
  thousand transactions at most.
- **Failure:** every failure of M53, plus uninterpretable coefficients, which directly conflicts with the programme's
  requirement that the engine report which parameters it assumed. It would also interpolate a 5%-resale population
  and present the interpolation as a price.
- **Evidence:** D.
- **Validation:** n/a.
- **Role:** **REJECTED.** Revival: none on this observation set. The programme's own argument for small models
  (`RESEARCH-PROGRAM.md` §4.9) is the reason, and it is also the reason M17 ships one parameter rather than ten.

#### M55 · Hybrid statistical + ML system

- **Target:** any.
- **Form:** a statistical core with an ML residual or correction layer.
- **Params:** the union.
- **Data:** the union.
- **Cost:** the union.
- **Buys:** in principle, the statistical model's interpretability plus the ML layer's flexibility.
- **Failure:** there is nothing to hybridise. The ML half has no data and no library, so the hybrid is the statistical
  model with an unestimable correction and an extra failure mode. `RESEARCH-PROGRAM.md` Phase 4 asks for these to be
  compared; the comparison is answerable by inspection.
- **Evidence:** D.
- **Validation:** n/a.
- **Role:** **REJECTED.** Revival: the ML half becoming estimable, which is M53's revival condition.

#### M56 · Agent-based market simulation

- **Target:** any, as a model of the market.
- **Form:** a population of rule-following agents whose interaction generates prices.
- **Params:** behavioural rules and their parameters.
- **Data:** the parameters are not identified from this observation set.
- **Cost:** simulation is cheap; calibration is the problem.
- **Buys:** a laboratory for market design questions, in principle.
- **Failure:** a calibrated agent model is a calibrated assumption wearing a simulation's clothes.
  `00-data-situation.md` §5 restricts simulation in this programme to **estimator properties** (labelled SIM), never
  to a description of ticket markets, and no SIM study exists yet.
- **Evidence:** E.
- **Validation:** n/a.
- **Role:** **REJECTED** (`01-c` §10.8). Note what survives: the SIM study of estimator recovery, which is a build
  task for the implementation phase and not a research result. Nothing in this file is SIM today.
  Revival: never as a market model; as an estimator test bed, immediately.

---

## 4. What this registry does not contain

Recorded so a later reader does not assume absence means "nobody thought of it".

- **No model that produces a calibrated price distribution.** M44 scores the sale indicator; nothing scores a price.
  The reason is T6: every scored price observation is conditioned on the sale having happened.
- **No model of the bid side.** M26 is the only family that would consume bids and it has no data.
- **No model with a validated parameter anywhere.** Not one number in this file has been estimated on real data.
- **No model comparison table with losses.** Phase 4 requires "candidate architecture comparisons" and a comparison
  of "simple baselines, regularized regression, GAMs, tree boosting, Bayesian hierarchical, state-space, survival,
  point-process, structural demand, hybrid". Every one of those is in this registry with a verdict, and **none can be
  compared on data because there is no data.** The comparison that exists is an identification comparison, not a
  performance comparison, and it is the honest form of Phase 4 under D1. Accuracy, calibration, generalization and
  robustness columns are therefore absent by design: filling them would require numbers this programme must not
  invent.

## 5. Conflicts carried, not resolved

Numbered so `F` can cite them. Nothing here is settled by being listed.

- **C1 · Spline versus one-parameter basis in time-to-event.** `01-c` §4.6 specifies `s(τ)` as a piecewise-linear
  spline with knots in the final fortnight. `02-a` §8.9 rejects a spline per event ("unidentifiable curvature by
  another name") and recommends the single-parameter `log(1+d)` basis. **Registry decision, stated as a choice:** M17
  (per-event path) uses the one-parameter basis; M05 (pooled across events, many more sales) may use a spline, and
  must then report curvature beyond the knot support as unsupported. `01-c` §10 F8 defers time-series models until
  the spline fails a prequential test, which implies the spline is expected to be tried. Both are recorded; the
  operator can overrule.
- **C2 · Whether the value level has an anchor.** `01-b` §4.1 says only ratios are identified and the schema contains
  no exogenous anchor. `01-b` §4.4(i) and `00-adversarial-review-phase1.md` error 5 say the level **is**
  set-identified from primary sell-through, and that §4.1 contradicts §4.4 on this. **Consequence for the registry:**
  M05 and M06 are labelled "no level" with the anchor question open. This is the single most load-bearing unresolved
  item for the first claim.
- **C3 · Which input the primary optimum needs.** `01-b` T5 says the optimum inherits the widths of T3 and T4.
  `00-adversarial-review-phase1.md` error 4 says the primary optimum's demand input is the **primary** sale process
  (T4b), not the secondary hazard (T3), and that the sentence linking them is wrong. **Consequence:** M46's input row
  names primary sell-through (M24), not M31, and the review's correction is preferred here because it is the later
  and the more specific finding. If someone restores the `01-b` reading, M46 and M31 both change.
- **C4 · Two cold-start answers.** `02-e` says the cold-start point estimate is the population mean and the interval
  is the deliverable. `02-c` §6 says a zero over exposure is evidence and the estimate must shrink with exposure.
  `02-c` §6.2 reconciles them by object: **price level** uses the population mean (M07); **sale intensity** uses the
  mean updated by the observed zero (M38). The rule is adopted here and is the version to hand a builder.
- **C5 · The size of the prize.** A mechanism change (Budish & Bhave, primary auctions, "roughly doubled performer
  revenues") and a price change (Leslie & Sorensen's model-based counterfactual, repricing the top 10% of seats at the
  median resale price, about 3.4%) are two published class-A answers to the same commercial question, more than an
  order of magnitude apart (`01-c` §5.4). This decides what to build first and it is unresolved. It is the operator's
  fork (M27).
- **C6 · The cap's within-event variation.** `01-b` ~~§4.4(ii)~~ **§5.3** treats the cap as an instrument with cross-tier
  variation. **[CORRECTION 2026-11-07T14:00Z, R2-8b — attribution corrected: the offending sentence is §5.3
  item 3's. `01-b` §4.4(ii) states only that the ceiling's *absolute level* differs across tiers because the cap
  is a percentage of each tier's own face, and it draws its bound from cross-**event** cap variation, so it is
  already correct and this registry's C6 never rested on it. `01-c` §1.4(1) carried the same wrong section
  number and was corrected with this one.]** `01-c` §1.4(1) corrects it: `resalePriceCapBps` is one field on `Event`, so cross-tier ceilings move
  exactly in proportion to face and there is no independent within-event variation. **The registry follows the
  correction**, which weakens M08's bound and is why its instrument is labelled cross-event only.
- **C7 · Fee neutrality.** D4 says a per-unit fee and an ad-valorem fee give different optima. `02-d` §2.3 sharpens
  it: ad valorem fees are **neutral** for the all-in optimum and only per-unit fees move it, with the whole stack
  collapsing into `c**`. **Registry follows `02-d`**, which is exact algebra rather than an assumption.
- **C8 · The cure component's evidence.** `01-b` supported it with a fixture-based comparison
  (`00-adversarial-review-phase1.md` error 2: SIM at best, and inadmissible under the no-fixture rule).
  **The registry carries the cure fraction as class C identifiability only** and records that no simulation exists in
  the repository, so the row has no SIM support either. M30 must say "never-transacted fraction" and never
  "never-offered fraction".
- **C9 · The price path's conditioning.** `02-a` §4.4: the published decline is measured on **listings that failed
  and were relisted**; this ledger measures **transactions that cleared**. The magnitudes are not comparable, and this
  is the report's own "most consequential methodological point". **Registry consequence:** M17's `θ̂` is not a
  transfer of Sweeting's exponent, it is a locally estimated curvature, and the sweep of published dummies is
  A-cited support for the **shape**, not for the value.
- **C10 · `issuedCount` semantics.** Whether it means sold or minted is unknown and load-bearing for M24 and for the
  sign of the demand bracket (`02-e` §10.1). The registry treats M24 as gated on the answer.

## 6. The smallest model set that delivers the four claims

The four claims in the product's own words: **what it is worth**, **how it moves**, **the probability it transacts at
a price**, and **the primary price that maximises risk-adjusted value**. Below is the smallest set of models from
this registry that supports each, and the explicit gap where none does.

| Claim | Smallest set | What the output is | Validation status |
|---|---|---|---|
| What it is worth | M05 (censored hedonic) + M08 (cap bound) + M06 (repeat-sales check) | a relative value with a width, a cap-implied lower bound, and an internal disagreement report | C by argument, UNVALIDATED; the level anchor is disputed (C2) |
| How it moves | M17 (deadline-convex path) + M18 (martingale fallback) | a proportional move over the horizon, with `ω` printed and a residual band by horizon | C, A-cited for the shape only; UNVALIDATED |
| Probability at a price | **none today.** M31 + M32 behind the four-field adapter, and M30 for the rate without a price | today: a transaction rate per ticket-day, not a probability at a price | M30 C by argument, UNVALIDATED; M31/M32 gated and UNVALIDATED even when unblocked |
| Primary price maximising risk-adjusted value | M46 (grid + fee wedge + boundary rule) + M47 (mean-CVaR) + M24 (sell-through bracket, gated) | a **range** and a rule, with the two assumed parameters named, not a point | C by argument, UNVALIDATED; a point optimum is not identified (T5, N4) |

Plus two rows that are not claims and cannot be dropped: **M44** (prequential scoring) because without it no claim
above can be checked and every decision rule in M17 and M18 is unenforceable, and **M39** (the separation guard)
because without it the hazard fit diverges on empty cells and the failure is silent.

**The explicit gap.** The third claim has **no model behind it.** `P(sale at price p | state)` is not identified
from this record, because the ask is written down only on the success branch, and no functional form, no method
family and no pooling arrangement recovers it. What the engine can support is the strictly weaker and still useful
statement: the composite transaction rate per ticket-day at risk, the realised price-time distribution, and the
identity of the four fields that would convert the gap into a standard survival problem. Every other claim is
deliverable as a bound or a set, which is why the gap is one claim and not four. It is also why the engine's
top-level adapter must keep returning `available: false` until either the four listing fields exist or the operator
accepts a relabelled claim.

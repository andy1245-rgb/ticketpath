# B · Mathematical knowledge base

**What this is.** The programme's mathematical record: every formulation the engine rests on, written out,
with its assumptions carried inside the derivation, its parameters and their units, the data that estimates
each parameter, the identifiability target it serves, its evidence class, its standard-library cost, and the
condition under which it is wrong. It is the curated layer over the finding files: `D-model-registry.md`
records *verdicts and roles* (SHIP / SPECIFIED / REJECTED); this file records the *mathematics* those verdicts
are about. Cite `D` for what to build, this file for what the equations say.

**Last updated:** 2026-11-07T11:30Z. **Author:** records agent, Phase 2 consolidation.
**Programme section:** §2.B (formulations, assumptions, derivations, parameter requirements, limits,
relationships, candidate integration methods).

---

## 0. How to read this file, and what it is conditioned on

### 0.1 Inputs, and the state they were in

Read in dependency order, as briefed. Recorded here because the record is only as good as its inputs, and two
of them are not what a reader would assume.

| Input | State on disk at time of writing | Consequence for this file |
|---|---|---|
| `records/findings/01-b-identifiability.md` | complete, first pass (§7 sources verified against Crossref) | the spine. Every formulation below names its `T` target and that target's status, in `01-b` §3's vocabulary |
| `records/findings/01-c-methods.md` | complete, 121 KB, eight method families, §1.3 build order | decides admission. No formulation below is invented; if `01-c` rejected a family, it is not here |
| `records/findings/02-a-price-paths.md` | complete, 73 KB | the price-path and cap-truncation mathematics (§5, §6, §8) |
| **`records/findings/02-b-cap-truncation.md`** | **DOES NOT EXIST.** No file by that name, and no other Phase 2-B file is on disk. | **The cap mathematics below is reconstructed from where it actually lives**: `02-a` §6 and §6.1–§6.3 (the `min(latent, cap)` structure, features that survive, the crossing date), `01-a` §3 (the three observational consequences of a binding cap), and `01-b` §4.4(ii) and §4.5(iii) (the one-sided bound and the uninformative allocation). Where a cap result is thinner than the brief for a dedicated file would have made it, it is marked **THIN** and named as a gap. This section is the one that must be refreshed when 02-B lands. |
| `records/findings/02-c-sale-hazard.md` | complete, 83 KB | the sale-intensity mathematics: two specifications, the likelihoods, the CIF, the cure mixture, the calibration algebra |
| `records/findings/02-d-elasticity-fees-optimum.md` | complete, 61 KB | the objective, the fee wedge, the first-order condition, the risk functionals |
| `records/findings/02-e-cold-start.md` | complete, 76 KB | the partial-pooling mathematics, the between-event variance problem, the stdlib code |
| `records/F-decision-log.md` | D1–D5 | D1 (no real data), D2 (stdlib only), D3 (sale probability is a data requirement not a model), D4 (fees symbolic), D5 (one estimator, prior-only branch) constrain every formulation below and are cited where they bite |
| `records/00-data-situation.md` | complete, Phase 0 audit | the observation set, and the four gaps. Every parameter table's "estimated by" column is answered against this file |
| `records/findings/00-adversarial-review-phase1.md` | complete, 39 errors | nine of its errors change equations or identifying assumptions. They are applied, not repeated: see §12 |
| `records/findings/00-verification-round1.md` | complete, discovered mid-pass and read, **not in the brief** | the later verification pass, and it is the more authoritative of the two on arithmetic. It confirms every number quoted here and it catches one **verified error in `02-e` §4.7's band label** which this file would otherwise have propagated; the correction is applied in §8.3 and recorded in §12 as C13. Cite this file, not `02-e`, for the absolute markup band |
| `records/findings/01-a-market-structure.md` | complete | the class-A empirical anchors and the cap's observational consequences |

**One stale cross-reference to be aware of, not fixed here** (it is `A`'s file, not mine): `A-research-ledger.md`
still marks P1.C as `dispatched` with a 28-byte placeholder, while `01-c-methods.md` on disk is complete at
121 KB. The ledger row is behind the file.

### 0.2 The three rules this file obeys

1. **Traceability.** Every formulation names either a finding section or a named result in standard statistical
   theory, and says which. Where both apply, both are named: the method is theory, the applicability is a
   finding. Nothing here is a method no finding supports. `01-c` §10's rejected list is respected: ARIMA,
   GARCH, GAM-as-primary, Gaussian processes, deep learning, matrix completion, agent-based simulation, HMC,
   synthetic control, Rosen's second stage, extreme-value tails and full-posterior sampling do not appear as
   formulations. Where a rejected method is mentioned it is inside a limitation clause explaining what would
   revive it.
2. **Derivations are class C.** Any step that is algebra or an argument from the schema is class C and is
   tagged `[C]`. Measurements are class A/B and cite the finding that read the paper. Simulation is `SIM` and
   appears nowhere as validation. Anything needing data the programme does not have is `UNVALIDATED` and is
   stated as a hypothesis plus its test, never as a result.
3. **No number without a source.** Every quantity in a table carries the finding section it came from, or the
   word `config` (a parameter the operator supplies), or `derived` with the derivation shown. Numbers lifted
   from published papers are quoted as the finding quotes them, with the market and sample attached, because
   the programme's whole difficulty is that they do not transfer (`02-d` §3.3).

### 0.3 Evidence classes, quoted

**A** directly supported by ticket-market empirical evidence · **B** supported by empirical research in a
related market · **C** mathematical theory or established statistical methodology, true by construction ·
**D** plausible, mechanism argued, untested · **E** speculative opportunity. `SIM` and `UNVALIDATED` are
labels, not classes (`records/README.md`). Because of D1, **no result in this programme can be class A from
our own data**: class A appears only as a citation to published ticket research.

### 0.4 Identification vocabulary

`01-b` §3's ledger: **T1** latent value (set-identified at trade instants, ratios only, level disputed, see
C2 in §12) · **T1′** value for an event with no history (not identified; prior predictive only) · **T2** price
path (curvature identified, linear trend not, APC collinearity) · **T3** sale hazard vs price (not identified;
the composite transaction rate is) · **T4a** hedonic locus (set-identified up to normalisation, selected
sample) · **T4b** demand / willingness to pay (not identified from secondary trades; set-identified from
primary sell-through) · **T5** primary optimum (a set, not a point) · **T6** uncertainty (calibratable for the
sale indicator, not for any price distribution).

Three words are used exactly and are not interchangeable:

- **identified**: the parameter is a function of the observed data; a consistent estimator exists.
- **set-identified / bounded**: the data pin down a set; a bound, a bracket or a one-sided restriction is
  computable, and a point is not.
- **not identified**: no function of the observed data recovers it. The honest response is a declared
  assumption plus a data requirement, never a fitted number.

Per adversarial review error 13, a set-identified *optimum* is the **image of the input sets under the
optimisation map**, not the union of the input widths. That distinction is used in §6.

---

## 1. The map: seven subproblems, the formulation serving each, and what each can and cannot say

One line per subproblem in each of the three status columns. "Bounded" means a computable bound, bracket or
one-sided restriction exists today.

| # | Subproblem | Formulation that serves it | What is **identified** | What is **bounded** | What is **not identified** |
|---|---|---|---|---|---|
| **P1** | Value level: what a ticket is realistically worth on resale | **F3** censored hedonic (with **F2** repeat-sales as its check, **F4** cap bound as its floor) | a quality-adjusted **relative** price, `y = log(price/face)`, for every ticket including never-traded ones (§2.3) | the level, one-sided from the cap mass (§2.4) and from primary sell-through (§5.1); the change, as an index, from F2 | the **absolute** level; between trades; seller reservation; buyer WTP; anything inside the censored region |
| **P2** | Price path: how value moves over the remaining horizon, and forecasting it | **F5** deadline-convex path, **F6** local-level state space, **F1** martingale as the fallback | curvature (convexity) and per-event deviations from the event mean (§3.1) | the slope, as a bracket over a declared normalisation `ω ∈ {0,1}` (§3.1) | the linear trend (exact age–period–cohort collinearity); the level path of a ticket that never resold; a rate or half-life |
| **P3** | Sale intensity: the probability a ticket transacts, and at what price | **F7** composite intensity (no price), **F8** mark–time intensity (descriptive), **F9** listing-episode hazard (price response, gated) | the composite transaction rate per ticket-day at risk; the cumulative incidence; the never-transacted fraction (an **upper bound** on never-offered); the realised price-time distribution ξ (§4) | the hazard *given the seller's own ask*, once the four listing fields exist; a prediction under the observed ask policy (§4.3) | `∂λ/∂p`; any `E[sale if we set p]`; the split of the composite rate into offered-rate × sale-rate; the ask distribution |
| **P4** | Elasticity: how primary quantity responds to primary price | **F10** primary sell-through bracket | the **sign** of excess demand at face, per tier, from the sold-out indicator (§5.1) | a one-sided bracket on demand at each observed face value; `ε ≤ 1` in the neighbourhood of observed prices, from the literature (§5.1) | `ε_own` as a number; any functional form; cross-price effects; the response under a resale cap (no study exists) |
| **P5** | The primary optimum: the price maximising risk-adjusted net value | **F11** fee wedge and FOC, **F12** grid optimiser with the boundary rule, **F13** mean-CVaR, **F14** reserve-price surface | the objective's **structure**: the whole fee stack collapses to one scalar `c**`; ad-valorem fees are neutral; a proportional cap does not bind the organiser (§6.1–§6.3) | the recommendation, as a **set** over the `(ε, u, q_min)` box, plus the sell-through boundary (§6.2, §6.4) | a point optimum; the primary demand level; the sign of the risk correction (it depends on the elasticity in the adverse state); dynamic pricing (no reprice endpoint) |
| **P6** | Uncertainty: intervals, calibration, honest width | **F15** prequential proper scoring, **F16** empirical quantile band, with **F17**'s mixture quantiles for cold start | calibration and the reliability–resolution decomposition **for the sale indicator** on the full censused population (§7.1) | any **price** interval, read off as empirical residual quantiles scoped to transactions (§7.2) | coverage of any price-distribution interval; conformal guarantees (no exchangeable calibration set); portfolio-level risk |
| **P7** | Cold start: pricing an event with no resale history | **F17** normal–normal partial pooling, **F18** gamma–Poisson exposure update | the prior-predictive **band** and its width; exact cap/fee arithmetic; the handover count `n* = σ²/τ²` (§8.1) | the between-event variance, above `J = 2` and poorly even there: the 95% interval spans 23× at `J = 5` (§8.2) | a point value; the level; `τ²` at `J ≤ 1`; whether the chosen face is optimal (the band is in units of face, so it cannot choose face) |

**The one-sentence summary of the map.** P1 is a ratio with a one-sided floor, P2 is curvature, P3 is a rate
with no price in it, P4 is a sign, P5 is a set, P6 is a scoring rule for one indicator and empirical
quantiles for the rest, P7 is a declared width. **Nothing here is a point price and nothing here is a demand
curve**, and that is the identification result, not a shortfall of effort.

---

## 2. P1 · The value level

### 2.1 F1 · Martingale anchor (the null, and the fallback)

**Serves.** P2 primarily, P1 as a standing reference. It is the benchmark every price model must beat, and
the model shipped if none does (`02-a` §8.5, `02-a` §8.6; `D` M18).

**Mathematics.** For a ticket observed at price `p` at time `t`, the forecast at any horizon `h` is

```
ŷ(t+h) = y(t)                               (MART)
```

in log space, i.e. the best forecast of the price is the last observed price. Equivalently `log p` is a
random walk with no drift: `E[log p_{t+h} | F_t] = log p_t`.

**Assumptions, in the derivation.** (i) The price index has no predictable drift over the remaining horizon.
(ii) The last observed transaction is an unbiased anchor for the current price, which fails under staleness
(nonsynchronous trading, `01-b` §4.2) and is at its worst exactly where trades are rarest. (iii) For
deliberate reason, it is the *theoretical* benchmark as well as the naive one: Deneckere and Peck's
competitive-sellers-plus-strategic-buyers model predicts a martingale, as noted in `02-a` §8.5.

**Parameters.** None. Zero estimated parameters, zero configuration.

**Data.** One prior transaction for the ticket. Nothing else. This is the only formulation in this file that
requires no parameter and no missing field.

**Identification.** Serves P2 as a *reference*, and it is not an estimate of T2; it is the hypothesis T2 is
tested against.

**Evidence class.** **C** (the random-walk null), with the theoretical support above. That it holds in this
market is **UNVALIDATED**.

**D2 cost.** Trivial: one assignment.

**Wrong when.** The true path has a predictable component, which is precisely the possibility `02-a` §5
measures and endorses in shape, so this model is knowingly misspecified and is shipped anyway because a
misspecified model that is measurable beats a curved one that is not. It is *also* wrong in a way that cannot
be detected by backtesting on our own data: a martingale benchmark scored against a path model fitted on the
same ledger can be beaten by sampling luck when events are few (`02-a` §8.5's per-event dispersion guard).

---

### 2.2 F2 · Repeat-sales index (Bailey–Muth–Nourse)

**Serves.** P1 as **ratios only**, P2 as an independent check on the curvature. Not a level.

**Mathematics.** For a ticket `i` with two recorded sales at prices `p_{i1}, p_{i2}` in time cells `t(i,1)`,
`t(i,2)`:

```
log p_{i2} − log p_{i1}  =  Σ_t β_t ( D_{i2t} − D_{i1t} )  +  u_i                     (BMN)
```

with `D` the time-cell dummies. Estimated by least squares on the differenced equation; the ticket fixed
effect is differenced out and never estimated. The index is `exp(β_t)` **relative to one normalised cell**,
because `β` is identified only up to an additive constant (a level shift common to all cells cancels in the
difference). Residual variance `s² = Σu²/(N_pairs − T)`.

**Assumptions, in the derivation.**

- *A1 Quality is unchanged between the two sales.* **This is the family's free lunch and it is literally true
  here**: a ticket's attribute vector is fixed at mint. No renovation, no depreciation, no redevelopment,
  which is exactly the concern that makes BMN an approximation in real estate (`01-b` §4.1, `01-c` §4.2). [C]
- *A2 The pair sample is representative of the price index being constructed.* **Fails.** Tickets that trade
  twice are the liquid subset of an already-selected subset: resale is about 5% of tickets, measured twice
  independently, and the mean is carried by a few hot events (`01-a` §5, class A). Bias direction and
  magnitude are the literature's own result (Gatzlaff & Haurin 1997; Steele & Goy 1997 on short holds).
- *A3 No compositional drift across time cells.* Fails: which tickets trade is correlated with `τ`.
- *A4 the differenced price is a pure price movement.* True per pair by A1; the three residual problems are
  all *across* pairs (`01-c` §4.2). [C]

**Parameters.** `β_t`, one per time cell; `T` of them, with one normalisation (so `T − 1` free). No other
parameter. The number of pairs is data, not a parameter.

**Data.** `mintAddress` (to pair), `priceLamports`, `occurredAt`/`slot`, on `sale` rows only. **No missing
field is needed**: this is one of the two formulations in the file that runs on the contract as it stands.

**Identification.** Serves T1's *ratio* component and T2's curvature; contributes nothing to the level, which
is why `02-a` §4.3 and `01-b` §6(1) both require it be reported as an index and never as a price.

**Evidence class.** **C** for the estimator (a well-established index construction); the transfer to tickets
is **C** by the fixed-attribute argument; its accuracy here is **UNVALIDATED**.

**D2 cost.** Normal equations in `T`. **`T` must be small and fixed**: monthly cells over one year is `T=12`,
a 12×12 solve, honest as a hand-written Gaussian elimination. **Not honest** at per-day or per-week cells over
a multi-year window (`T ≥ 100`), where the flops are tolerable but the conditioning is not, and where the
information matrix is sparse (only pairs that exist contribute) and dense linear algebra wastes the
structure. If cells must be fine, the honest reformulation is to estimate a single parametric index slope
instead of `T` free cells, i.e. to admit the linear-trend collinearity rather than fight it. See §10.

**Wrong when.** The selected pairs differ from the population in their price *change* (not merely their
level), which the short-hold result says they do. It is also wrong when the index is read as a level: `β_t`
has an arbitrary additive constant and any absolute number derived from it is a normalisation in disguise.

---

### 2.3 F3 · Censored hedonic price locus · **the load-bearing formulation** (§13)

**Serves.** P1 directly (a relative value for **every** ticket, including never-traded ones, which no other
formulation gives), P2 (because `τ` is an attribute, §3), P5 (the value signal the optimiser consumes), and
P6 (its residual distribution is the interval). Target T4a; T1 as ratios; **not** T4b.

**Mathematics.**

Response, on every `sale` row and, at prediction time, on every ticket:

```
y = log( priceLamports / faceValueLamports )                          (H1)
```

Latent model:

```
y* = μ + α_tier + δ_event + s(τ) + γ'X + ε,        ε ~ N(0, σ²)       (H2)
```

with `τ` = days to `Event.startsAt`, `s(·)` a piecewise-linear spline in `τ` with knots concentrated inside
the final fortnight, and `X` the attributes fixed at issue (`transferRestricted`, `requiresVerifiedWallet`,
tier size, event category, city).

Observation rule, with the cap as a **known** bound in the same units as the response:

```
c_event = log( 1 + resalePriceCapBps / 10⁴ )        (∞ when the cap is null)      (H3)
y = y*                        if y* ≤ c_event
y = c_event                   if y* > c_event      [censored regime  → mass point]
y unobserved                  if y* > c_event      [truncated regime → nothing recorded]
```

Log-likelihood, censored regime (upper censoring at a known, event-specific point):

```
ℓ(θ) = Σ_{y < c} [ log φ((y − x'β)/σ) − log σ ]
     + Σ_{y = c} log Φ( (x'β − c)/σ )                                              (H4)
```

and truncated regime, which is the same expression with the censored term dropped and every uncensored term
divided by `Φ((c − x'β)/σ)` (a normalising constant that depends on `θ`, so it does not drop out of the
likelihood: this is the one algebra step that is easy to get wrong):

```
ℓ_trunc(θ) = Σ_{y < c} [ log φ((y − x'β)/σ) − log σ − log Φ((c − x'β)/σ) ]         (H5)
```

**Which of (H4) and (H5) is correct depends on open question Q3** and is decided empirically by whether a
mass point at exactly `cap_bps` exists in the record (`01-c` §4.3). On-chain enforcement reverts the transfer,
so no sale above the cap is possible → truncation → (H5). Platform-level refusal to list produces a pile-up at
the ceiling and censoring of latent WTP → (H4). **The first diagnostic on real data therefore answers Q3**, and
it should be run before either likelihood is fitted. `[C]`

Estimation by **EM**, not Newton: at iteration `k`, for each censored observation with `z = (c − x'β̂_k)/σ̂_k`
and inverse Mills ratio for the **upper** tail `λ(z) = φ(z)/(1 − Φ(z))`,

```
E-step:  ỹ* = x'β̂_k + σ̂_k λ(z)                                          (H6)
         ṽ*  = σ̂_k² [ 1 + z λ(z) − λ(z)² ]        (the second moment the σ update needs)
M-step:  β̂_{k+1} = (X'X)^{-1} X'ỹ*   ;   σ̂²_{k+1} = mean( ṽ* + (ỹ* − x'β̂_{k+1})² )
```

iterate to a tolerance on `ℓ`. EM is chosen over Newton deliberately (`01-c` §4.6): it converges monotonically
and it avoids the badly conditioned Newton step that the censored-normal likelihood produces when the
censoring fraction is high, which it will be on tightly capped events.

**Assumptions, in the derivation.**

- *A1 Price-taking at the recorded price.* **Fails under a binding cap** (handled by H3) and under bargaining,
  where the latent value is interval-identified with unobserved width (`01-b` §2b). What is estimated is
  therefore the *clearing* locus, not value.
- *A2 Implicit attribute prices are constant over the estimation window.* **Fails by construction for `τ`**,
  which is why `τ` enters as a state through `s(τ)`, not as a constant (§3). [C]
- *A3 Traded units are representative.* **Fails.** Resold tickets are better seats: mean seat-quality
  percentile 0.61 against 0.50 for all tickets (`01-a` §6, class A). The fitted locus describes the
  **tradable subpopulation**; a prediction for a random ticket is biased up by an unmeasured amount.
- *A4 Quality unchanged per unit.* **Holds exactly** (fixed at mint), the same free lunch as F2. [C]
- *A5 The latent `y*` is normal.* Does real work and is **untestable inside the censored region**;
  mitigated by working in `log(price/face)` rather than basis points, whose right tail is long by
  construction.
- *A6 The bound is known and carries no sampling error.* **Holds**: `resalePriceCapBps` is an observed field.
  This is what makes the problem Tobit-type rather than a threshold-estimation problem. [C]
- *A7 Error is independent of the regressors.* Untested; seat quality is an omitted variable and it is
  correlated with tier, so `α_tier` absorbs part of it and the rest is in `ε`.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `μ` | grand mean log ratio | log units (dimensionless) | the fit; not identified separately from the normalisation of `α`, `δ` |
| `α_tier` | tier effect | log units | sales within the tier, pooled across events (F17) |
| `δ_event` | event effect | log units | that event's sales; **identified relative to a normalisation only** |
| `s(·)` knots | curvature of the path in `τ` | log units per knot | within-event variation in `τ` (see C1, §12) |
| `γ` | attribute effects | log units | cross-sectional variation; **contaminated by selection (A3)** |
| `σ` | within-cell dispersion of log ratio | log units | residual variance, including censored observations via `ṽ*` |
| `c_event` | the cap, in response units | log units | **not a parameter**: `log(1 + cap_bps/10⁴)`, observed |

**Data that estimates each.** `sale` rows with `priceLamports`, `Ticket.faceValueLamports`, `Event.startsAt`,
`Ticket.tierId`, `Event.resalePriceCapBps`. **No missing field is required.** Seat coordinates are *not*
required for the model to run; they are required for the model to price a seat rather than a tier, which is
the structural limitation, not a technical one (`00-data-situation.md` Gap 3; Q1 open).

**Identification.** T4a: **set-identified up to an affine normalisation, subject to selection**. The
`δ_event` and `α_tier` coefficients are identified relative to a choice of reference, so the output is a
*quality-adjusted relative price*; the affine indeterminacy of the index is not removable from this data and
the anchor question is the operator's. See C2 in §12 for the contested part.

**Evidence class.** **C** for the method. **A** for the proposition that seat quality is the dominant
within-event price axis and that resale prices vary seat by seat (`01-a` §6). **B** for treating a policy
ceiling as a known censoring bound (Tobit-type structure is standard; the ticket application is new). **D**
for the claim that a ticket's hedonic surface is stable enough over an event's life for the coefficients to be
usable out of sample; nothing has tested that.

**D2 cost.** **Honest, and the most comfortable fit in the file** despite being the richest model, because
the survival of the structure depends on one trick: **absorb the event dummies by within-event demeaning**
before solving, then recover `δ_event` by subtraction in the M-step. Without absorption the design is
`p ≈ J + tier + knots + k` and at `J = 60` events the normal-equation solve is 80×80, which is not a
hand-written solve anyone should trust. **With absorption** you solve a `p_small × p_small` system where
`p_small = tier + knots + k`, which is of order 15–25; that is honest at `n ≤ 30`, and the demeaning is exact.
Cost per EM iteration is `O(n·p_small² + p_small³)`; at a few thousand sales and 20 iterations this is well
under a second in CPython. `statistics.NormalDist` supplies `cdf`/`pdf`/`inv_cdf` in 3.12 (verified in `01-c`
§4.6), and `λ(z)` is `pdf(u)/(1 − cdf(u))`. Roughly 120 lines. See §10 for the general rule.

**Wrong when.**

- *The level is read as money.* It is a ratio with an arbitrary additive normalisation. Any "the ticket is
  worth X lamports" derived without an external anchor is a normalisation.
- *The censoring regime is chosen wrongly.* Fitting (H4) when the truth is (H5) invents a mass point and
  biases `σ` down; fitting (H5) when the truth is (H4) throws away the mass that identifies the tail. Q3
  decides it, and the mass-at-cap diagnostic decides Q3.
- *The censored fraction is near 1.* When nearly every trade hits the cap, `σ` is identified off almost
  nothing and the fit is a statement about the cap, not about value. Guard: report the cap-hit share and
  refuse the surface above a stated threshold (`02-a` §6.2 fixes the central-tendency threshold at 50%).
- *Seat quality varies within tier and is correlated with `τ`.* Then `s(τ)` absorbs a compositional change
  and the estimated path is partly a mix effect. This is unresolvable without Gap 3 and must be carried as a
  limitation on every path number.
- *The hedonic is used as a demand function.* `α_tier` is a price differential along an equilibrium locus. It
  is **not** marginal willingness to pay; entering it in the optimiser as if it were is the commonest error in
  applied pricing (`01-c` §4.1, `01-b` §4.4; Rosen 1974, Brown & Rosen 1982). [C]

---

### 2.4 F4 · Cap truncation: the mass point, the one-sided bound, and the crossing anchor · **THIN**

**Serves.** P1 as a **floor** on value; P3 as the only observable proxy for excess demand; P2 as a sign test
that needs no level. This is the section that stands in for the missing `02-b-cap-truncation.md`.

**Mathematics.** Let `m*(d)` be the latent markup multiple (price over the ticket's own face) at `d` days out,
decreasing in `d`, and `c` the cap in the same units. The record contains

```
m̃(d) = min{ m*(d), c }   +  leakage noise                                  (CAP-1)
```

The three consequences a binding cap has are observationally distinct (`01-a` §3, class C):

1. **A one-sided bound at the cap.** A recorded sale at exactly the cap asserts
   `V ≥ p₀(1+c)`, the buyer paid the maximum permitted price, so willingness to pay is at least the ceiling,
   and its location above the ceiling is **not** in the data. Across events with different caps this traces a
   **lower bound on the survival function of willingness to pay at each observed cap level** (`01-b` §4.4(ii)).
   Sign and one-sided magnitude identified; location not.
2. **A mass point whose height measures rationing, not value.** Behind a binding ceiling, allocation is by
   speed, and the allocation carries no information about valuations (Glaeser & Luttmer 2003; Bulow &
   Klemperer 2012; the latter is **theory, so class C**, per adversarial review error 36, not B). So a ticket
   sold at the cap went to whoever was fastest: a statement about latency, not value. [C/B]
3. **Attenuation of any measured path.** Truncation removes exactly the high side at large `d`, so the
   observed slope between early and late is flatter than the true one, and it removes it most on the events
   with the strongest demand. The resulting error is a **ranking inversion**, not merely a level bias: the
   engine would conclude the hottest events decline least (`02-a` §6.1 C1, `01-a` §3(3) as corrected by review
   error 18). [C]

**The crossing date, which is the record's only known-price point.** Define

```
d*  =  the last day on which a sale lands at the cap, so  m*(d*) = c,  and c is KNOWN   (CAP-2)
```

That pins a latent quantity to a known number at one date per event, with no exogenous reference price, 
which is a partial answer to T1's missing anchor. It is **interval**-identified, with width equal to the gap
between the last sale at the cap and the first sale below it, so it is only as sharp as sales are dense; and
leakage pushes it **later** than the true crossing (sellers keep recording at the cap while settling off-ledger),
making the mass point an upper bound on genuine cap trades (`02-a` §6.1 C4). [C]

**Which features survive**, which is what makes the cap usable rather than merely fatal (`02-a` §6.2):

| Feature | Survives | Condition, stated precisely |
|---|---|---|
| lower quantiles of `y` per event and day-bucket (e.g. the 0.25) | **yes**, *provided the cap mass lies below that quantile unconditionally* | the identity is **unconditional**: the observed `q`-th quantile equals the latent `q`-th quantile when `P(cap) < q`. A **conditional** quantile needs the bound above the conditional quantile pointwise, which is a stronger and untested condition |
| median | yes iff cap mass < 50% | above that the median *is* the cap and every central measure is degenerate (`02-a` §6.2 C2) |
| mean, any upper quantile | **no** | that is the censored region, biased down by construction |
| cap mass and its trajectory over `d` | **yes**, and it is the best feature in the dataset | a sign test on the path immune to both the level indeterminacy and the attenuation bias; one-way, not decisive |
| crossing date `d*` | yes, interval-identified | (CAP-2) |
| slope of the path on cap-free events | **yes, fully** | no truncation |
| slope of the path on capped events | **no, attenuated** | C1 |
| anything pooled across tiers in markup space | **no** | the cap is bps over each tier's own face, so it binds at different absolute prices; pooling compares differently truncated objects |

**Assumptions, in the derivation.** (i) The cap is enforced on the ask or at transaction time, in one of the
two regimes of **Q3**; (CAP-1) as written assumes the ask-side regime and needs `V ≥ p` at the transaction-time
regime. (ii) No leakage, or leakage of known direction only, all four leakage channels are **class D** in
`01-a` §6, so this is an assumption with a stated sign, not a measured correction. (iii) The cap is observed
rather than latent, which holds. (iv) The cap varies usefully across events; it does **not** vary within an
event beyond proportionality (see C6, §12).

**Parameters.** None free. `c` is observed; `d*` is a derived data summary. The latent-markup-with-leakage
variant (`D` M09) adds `q(cap, event)`, the leakage probability, which is **specified-not-implemented** and
class D, its two parameters cannot be estimated from a record that does not show the leaked transactions.

**Data.** `Event.resalePriceCapBps`, `priceLamports`, `faceValueLamports`, `occurredAt`. Nothing missing.

**Identification.** One-sided bound on T1 and on the WTP survival function; a sign test on T2; a rationing
quantity for P3. Not a level, not a tail location.

**Evidence class.** **C** for the truncation algebra and the quantile identity (standard censored-quantile
results). **B** for the rationing interpretation, borrowed from rent control and mechanism theory. **A** for
the existence and enforcement of resale caps in the studied markets (`01-a` §3). **D** for every magnitude.
`01-b` §4.5 records the honest gap: **no peer-reviewed econometric study of resale price caps in ticket
markets was found**, so **no class-A claim about caps may appear in the deliverable**.

**D2 cost.** Trivial. Counting a mass, finding a crossing, and taking an empirical lower quantile are one pass
and a sort. No matrix.

**Wrong when.**

- *The cap does not bind*, then it is a no-op and must not be treated as evidence of anything.
- *Leakage is large and correlated with demand*, which is the case the four channels describe. The bias is
  then largest where value is highest and the bound is at its least informative exactly where it matters.
- *A central-tendency statistic is reported anyway.* Above 50% cap mass the median is the cap; reporting it
  is reporting the policy back at the operator.
- *The bound is read as an estimate.* `V ≥ p₀(1+c)` is a floor. Any number placed above it is invented.
- *The cap mass is pooled with the interior* in a hazard or a hedonic. It measures arrival speed under
  rationing and biases the price effect toward the rationing regime's mechanics (`02-c` §4.5).
- **THIN warning.** This is the reconstructed cap section. A dedicated 02-B would likely have carried the
  formal identification of the latent tail's location and the leak-corrected likelihood; neither is here.
  What is here is what `02-a` §6, `01-a` §3 and `01-b` §4.4–4.5 support.

---

## 3. P2 · The price path

### 3.1 F5 · Deadline-convex path, one estimated parameter

**Serves.** P2, and through `τ` it is the same object as F3 (§3.3). The one model whose single parameter is a
direct consequence of the identification result.

**Mathematics.** Two candidate shapes, and the evidence prefers the second (`02-a` §5.1–§5.2):

```
A  (constant concession):  log p(d) = a + λ d,        half-life  ln2 / λ
B1 (deadline convex):      log p(d) = a + θ log(1 + d),  per-day concession  θ/(1+d)
B2 (hyperbolic + floor):   p(d) = u + κ (1+d)^{−ψ}       → price tends to a use value u, not to zero
B3 (deadline step):        p(d) = a − γ·1{d ≤ 1}
```

Fitted form, per event `e` with `n_e ≥ 4` sales, on `y_i = log(p_i / face_{g(i)})` and `u_i = log(1 + d_i)`,
with both regressors demeaned within the event (`ỹ = y − ȳ_e`, `ũ = u − ū_e`, `d̃ = d − d̄_e`):

```
[ S_dd  S_du ] [ β_e ]   [ S_dy ]
[ S_du  S_uu ] [ θ_e ] = [ S_uy ],     S_ab = Σ ã_i b̃_i                        (PATH-1)

β̂_e = (S_uu S_dy − S_du S_uy)/Δ,  θ̂_e = (S_dd S_uy − S_du S_dy)/Δ,  Δ = S_dd S_uu − S_du²
RSS_e = Σ ỹ_i² − β̂_e S_dy − θ̂_e S_uy,  s_e² = RSS_e/(n_e − 2)
Var̂(θ̂_e) = s_e² S_dd / Δ
```

pooled by inverse variance:

```
θ̂ = Σ_e w_e θ̂_e / Σ_e w_e,        w_e = 1 / Var̂(θ̂_e)                          (PATH-2)
```

Forecast at horizon `τ`, anchored on the event-tier's own most recent transactions:

```
ŷ(τ) = ȳ_anchor + θ̂ [ log(1+τ) − log(1+d_a) ] + ω β̂_e (τ − d_a)                 (PATH-3)
```

with `ȳ_anchor, d_a` the median log relative price and median days-to-event of the last `K = 5` sales in the
tier (data, not parameters), `β̂_e` the event's linear slope (a nuisance), and

```
ω ∈ {0, 1}, a DECLARED NORMALISATION, not an estimate.  ω = 0: curvature only (identified).
                                                             ω = 1: attribute all within-event level movement
                                                                    to time-to-event.
```

Both are reported. Guards: `n_e ≥ 4`, `Δ > 0`, at least 5 days of spread in `d` within the event; discard
failures and **report how many were discarded**, because a model fitted on 12 of 60 events is a different
claim from one fitted on 50.

**Assumptions, in the derivation.**

- *A1 Curvature is identified; the linear trend is not.* This is not an assumption of convenience: it is the
  exact linear dependency `age + cohort = period` in an age–period–cohort decomposition: within one event,
  `τ` and calendar time are the same variable up to a constant, and across events the three-way decomposition
  is rank-deficient in its linear component (`01-b` §4.2, from the APC literature). **The constraint is
  therefore a declared restriction, no common calendar trend across events beyond what the event effects
  absorb, and it is stated rather than hidden.** [C]
- *A2 The shape is convex.* Supported by the anchor study: on Sweeting's own within-seller table a
  constant proportional decline reaches R² 0.55–0.69, while `log(1+d)` reaches R² 0.90–0.97 with a single
  exponent of 0.133–0.164 stable across high/low demand and cheap/expensive seats (`02-a` §3.1–§3.3, class A
  for the table, C for the fit, D for any transfer). The mechanism: the seller's reservation is the value of
  continuing to wait, and the probability of at least one buyer arriving by `d` is `1 − e^{−νd}`, so the
  outside option shrinks fastest at the deadline (`02-a` §5.2); this is the standard finite-horizon
  perishable-inventory result (Gallego & van Ryzin 1994). [C]
- *A3 The fitted object is a clearing price conditional on a sale occurring at `τ`.* **Not** the ticket's
  value, **not** the price for a ticket that will not sell, **not** a sale probability. Three different
  objects with three different identification statuses (`02-a` §8.1, §4.2).
- *A4 The observation is the **success** branch.* Our ledger records transactions that cleared; Sweeting
  measures listings that failed and were relisted. If sellers cut only when they fail to sell, the published
  decline measures the failure branch and **our measured magnitude is not comparable to it** (C9, §12). This
  is the report's own "most consequential methodological point" and it is an assumption in the derivation, not
  a caveat after it.
- *A5 Both forces at the deadline are present and the seller's dominates.* Buyer arrivals rise into the
  deadline, 25% of concert resales in the final 7 days against 25% in the preceding 19, a derived per-day
  arrival rate 2.7× lower (`02-a` §5.3, arithmetic on Leslie & Sorensen's reported shares, class A), and the
  measured net is a decline. Any model that **hard-codes** a decline is assuming the outcome of a race the
  literature shows can go either way; Leslie & Sorensen report a modest uptick in the final week and Lee et
  al. find a game-day drop, opposite signs in the last 48 hours, recorded unresolved (`02-a` §3.5).
- *A6 The `s_e²` are treated as known.* They are not; PATH-2 is a fixed-effects meta-analysis, not a mixed
  model, and it **understates the uncertainty of `θ̂` when events are few**. Stated in the code comment, not
  discovered later.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `θ` | degree of deadline convexity; the per-day proportional concession is `θ/(1+d)` | dimensionless | within-event curvature, PATH-1 → PATH-2. **The one estimated parameter** |
| `β_e` | event linear slope | log units per day | within-event; **discarded under `ω = 0`**, used only under `ω = 1` |
| `ȳ_anchor`, `d_a` | anchor level and anchor day | log units, days | the last `K` sales. Data |
| `ω` | normalisation | {0,1} | **declared**, both reported |
| `K = 5`, `δ = 1` day, shrinkage weight `0.5`, three horizon bands | fixed a priori |, | **not fitted**: tuning them would add parameters the data cannot support |
| `u` (in B2) | the floor / use value | lamports | only if B2 is fitted; `02-a` §5.2 records the floor as *measured* at 0–2 days (2.014 and 0.932 × face for high and low demand) but its level is not pinned |

**Data.** `priceLamports`, `faceValueLamports`, `Event.startsAt`, `occurredAt`/`slot`, `tierId`. Nothing
missing.

**Identification.** T2: curvature and event deviations identified; **linear trend and any per-day rate or
half-life not identified** without a declared normalisation, hence the bracket over `ω`. The path is
identified only for repeat-traded tickets in the strict sense; the anchored form (PATH-3) extends it to a
ticket with no sales **at that ticket's own price** by borrowing the tier/event level, which is an
assumption, not identification.

**Evidence class.** **A** for the shape on the anchor study's market (Sweeting, MLB 2007, within-seller), and
for the arrival-rate arithmetic. **C** for the fit against the printed coefficients and for the mechanism.
**D** for any transfer of the exponent, of the magnitude, or of the sign in the final week to this market.

**D2 cost.** **The cheapest non-trivial formulation in the file, and exactly as honest as it looks.** Per event
a 2×2 solve, closed form, two multiplications and a subtraction, then an inverse-variance average. No
iteration, no matrix inversion beyond 2×2, no randomness, no library. Cost is `O(Σ n_e)` plus `O(E)`.

**Wrong when.**

- *`ω = 1` is used and calendar drift is real.* Then the whole within-event level movement is attributed to
  time-to-event and the slope is a confounded number presented as a rate.
- *A spline is used instead on a handful of points per event.* That is unidentifiable curvature by another
  name (`02-a` §8.9), and it is why C1 (§12) resolves toward the one-parameter basis at the event level and
  permits a spline only in the pooled F3 where there are many more sales.
- *The event has fewer than about 4 sales or less than 5 days of spread.* Then `Δ` is numerically meaningless
  and the event must be discarded, and the discarded count reported.
- *More than half of trades sit at the cap.* Then the central path is degenerate (F4) and only the lower
  quantiles are usable.
- *The magnitude is transferred from the literature.* Per A4 the conditioning is opposite, so `θ̂` is a
  locally estimated curvature, never Sweeting's exponent re-used.

---

### 3.2 F6 · Local-level state space · declared interpolation between trades

**Serves.** P2 and P1-between-trades. It is the **implementable form of the martingale assumption** T1 says
interpolation requires (`01-b` T1, `01-c` §7.4).

**Mathematics.**

```
state:     log V_i(t+1) = log V_i(t) + η,     η ~ N(0, q)                     (SS-1)
measure:   y_ik        = log V_i(t_ik) + ε,   ε ~ N(0, r)                     (SS-2)
```

A scalar Kalman filter and smoother. One-step predict/update:

```
predict:  m⁻ = m,  P⁻ = P + q
update:   K = P⁻/(P⁻ + r),   m = m⁻ + K (y − m⁻),   P = (1 − K) P⁻
```

The smoothed path between two trades is the interpolation; the ratio `q/r` is the signal-to-noise and is what
sets how much the path moves between observations. Pooling across tickets within a tier enters through the
prior on `log V_i(issue)`.

**Assumptions, in the derivation.** (i) The latent log value follows a random walk, the same assumption F1
makes, here made explicit as a variance rather than a point. (ii) The measurement error is additive and
homoscedastic in logs. (iii) `q` and `r` are constant over the ticket's life. (iv) Conditional independence of
the `y_ik` given the path. **This buys no identification**: `q` is a prior in disguise, and the accuracy of the
smoothed path at any instant is a function of `q/r` (`01-c` §7.4).

**Parameters.** `q` (state variance, log² per day), `r` (measurement variance, log²). Two, estimated by
maximising the prediction-error decomposition, or **declared** when there are too few tickets with ≥ 3
observations to estimate them.

**Data.** Repeat sales per ticket (`mintAddress` grouping), `priceLamports`, `slot`. No missing field.

**Identification.** Serves T1's between-trade component under a *declared* martingale; it identifies nothing.
The honest label is **"declared interpolation", not "estimated price"** (`01-c` §7.4). [C]

**Evidence class.** **C** for the method; **D** for the claim that a ticket's log value random-walks with
constant `q` between trades. `UNVALIDATED`.

**D2 cost.** **Honest and small**: a scalar filter is about thirty lines, no matrix at all (the state is
1-dimensional, so every "matrix" is a scalar). `O(Σ n_i)`.

**Wrong when.** `q/r` is small and the price really moves between trades (the smoothing then reports a stale
level as a current price); `q/r` is large and the interpolation is worthless noise; or the ticket trades twice
in its life, which makes (SS-2) a two-point series and any estimated `q` fitted noise. Also wrong when the
requirement is a *level*: it produces a path, and per T1 the level is not in the data.

---

### 3.3 Why P1 and P2 are one model, and what that costs

`τ` is not a characteristic of a ticket but of the transaction, so the hedonic is a **state-dependent price
function** `p(x, τ)`. Its derivative in `τ` *is* the price path. Consequences, stated because they decide the
architecture (`01-c` §4.4):

1. T2 and T4a are **the same object seen twice**. The architecture should be **one component with `τ` in it**,
   not a hedonic plus a separate forecaster. The forecast at horizon `h` is the same model evaluated at
   `τ − h`, smaller and more honest than fitting a time-series model to a series with about one trade per
   ticket.
2. The normalisation problem is **unavoidable** in both, and the practical resolution is the same in both:
   include event effects and a function of `τ`; **do not include calendar time**; report curvature and
   deviations from each event's mean.
3. The two formulations nonetheless **compete**: F5 estimates `θ` from within-event curvature only and is
   robust but thin; F3 estimates `s(τ)` pooled across events with fixed effects absorbed and is richer but
   rests on the normality of `y*` and on A3's selection. They should be run together and their disagreement
   is the diagnostic (C1, §12).

---

## 4. P3 · Sale intensity

### 4.1 The object, and the exact reason the price response fails

`01-b` §4.3's decomposition, in `02-c` §1's corrected form:

```
λ_obs(t | x)  =  s(t | x) · E[ λ(t | p) | offered, t, x ]                       (INT-1)
```

`λ` the wanted sale hazard, `s(t|x)` the probability the ticket is offered at `t`, the expectation taken over
the unrecorded asks. We observe the left side. **Nothing separates the two factors**, because the mark is
recorded only where the sale happened: a non-seller has no ask in the record.

Two corrections to the way `01-b` states this, both of which change what is estimable and neither of which
changes the conclusion:

- The at-risk **ticket-time** denominator is **observed**: every ticket carries an `issue` row and a known
  life to `min(redeem, event end)`. What is unobserved is the **listing** denominator and the price of the
  risk set. So this is a **case-only sample with no controls**, not a numerator without a denominator
  (`01-b` §1, `02-c` §1.2, adversarial review error 7). The fix is the ask on a random subset of the risk set, 
  a case-cohort design (Prentice 1986), which is the correct citation, not an informative-censoring citation.
  [C]
- Consequently `λ_obs` is the intensity of a **composite process, offered, then bought**: marginalised over
  the unrecorded offering state. Calling it "the sale hazard" invites a reader to compute `1 − exp(−λh)` and
  be told the probability their ticket sells, which it will not answer (`02-c` §1.2). [C]

**The trap, named because it survives review.** `markupBps` exists only on `sale` rows. A hazard model built
with it conditions on the event being modelled and will report a strong, significant, entirely tautological
"price effect on sales", because a sale *is* recorded by its price. The model converges, the coefficient is
large, and the whole thing is an artefact of the recording rule (`02-c` §3.3). **Never put `markupBps` on the
right-hand side.** [C]

---

### 4.2 F7 · Composite transaction intensity · piecewise-exponential, competing risks, cure

**Serves.** P3's identified part and P6's calibratable part. Target T3's identified remainder. **No price in
it.**

**Mathematics.** For ticket `i` in bucket `b` (a time-to-event grid; weekly far out, daily inside the last
week) with covariates `x`:

```
λ_i(t) = exp( α_b + x_i'β )                                                    (CI-1)

ℓ(α, β) = Σ_{b,c} [ D_bc (α_b + x_c'β) − E_bc exp(α_b + x_c'β) ]                (CI-2)
```

which is **exactly a Poisson log-likelihood with offset `log E_bc` and no constant** (`D` = events, `E` =
exposure in ticket-days). Score and observed information:

```
∂ℓ/∂α_b = Σ_c (D_bc − E_bc μ_bc),   ∂ℓ/∂β = Σ_{b,c} x_c (D_bc − E_bc μ_bc),  μ_bc = exp(α_b + x_c'β)
−H = Σ_{b,c} E_bc μ_bc  x̃_c x̃_c',  x̃_c = (e_b, x_c)
```

Newton from `α = log(D̄/Ē)`, `β = 0` converges in a handful of iterations.

The **discrete-time form and its link**, stated correctly because the wrong link is a common error: the exact
grouped-data hazard is

```
h_ic = 1 − exp( −exp(α_b + x'β) δ_ic )        →  complementary log-log, NOT logit
```

The familiar discrete-time logit is an approximation to this that is accurate when within-cell event
probabilities are small, which they are, a per-ticket-day sale probability of order 1e-3. The exponential
form is preferred because it is **exact**, its offset handles ragged cell lengths (every ticket's first and
last cell are partial), and its predictive integral is closed form below.

**Competing risks, and why redemption is not censoring.** Redemption, unpriced transfer, sale and revocation
are four competing events. A ticket redeemed at the door was, by revealed behaviour, held for use, so treating
redemption as censoring removes tickets for reasons correlated with the outcome, attendance and resale are
substitutes. Estimate the cause-specific `λ_k` for `k ∈ {sale, transfer, redeem, revoke}` by applying (CI-2)
once per cause (each as a binary outcome, other exits censored at their time). On the day grid, with total
hazard per cell `Λ_bc = Σ_k λ_{k,bc} δ`:

```
p̂_sale(b,c) = ( λ̂_sale,bc / λ̂_·,bc ) ( 1 − e^{−Λ̂_bc} ),     Ŝ_{bc+1} = Ŝ_bc e^{−Λ̂_bc}

F̂_sale(τ) = Σ_{cells ≤ τ} Ŝ_bc  p̂_sale(b,c)                                    (CI-3)
```

(CI-3) is the product-limit / cumulative-incidence estimate under the fitted model: closed form, no
simulation. Two outputs:

```
cumulative incidence:            F̂_sale(τ)                         → "X% of issued tickets in this tier transacted"
remaining-horizon incidence:     ( Ŝ(τ₀) − Ŝ(τ₁) ) / Ŝ(τ₀)         → "given alive and unsold now, P(sale in next h)"
```

(`F̂(τ→0)` is the estimated counterpart of `EventAnalytics.resoldShare`.)

**Cure component.** With a terminal point, after the event, no ticket can sell again, the never-transacted
fraction is identifiable unusually cleanly:

```
S(t | x) = π(x) + (1 − π(x)) S_u(t | x)

ℓ = Σ_sold log[(1 − π) f_u(T_i)] + Σ_censored log[π + (1 − π) S_u(T_i)]          (CI-4)
```

Two warnings that belong in the code:
1. `π̂` is **not** "the share of owners who never intended to sell". It pools *never offered* with *offered and
   never bought*, so **`π̂` is an upper bound on the never-offered share**. It must be reported as
   "never-transacted", never as "never-offered" (C8, adversarial review error 2).
2. With a terminal point the honest default is to **estimate** `π` and report its interval, not to test
   `π > 0`, whose null is non-standard.

**Assumptions, in the derivation.**

- *A1 Piecewise-constant baseline on the grid.* The grid is chosen so that within a cell the hazard is
  plausibly flat; the choice is a modelling decision and the cell boundaries are reported.
- *A2 Censoring at event end is exogenous given the event* (benign); **dataset-extraction censoring is not**
  benign in the same way; it puts future events' tickets into the exposure at `τ` values where the hazard is
  near zero. Consequence: **quote the `τ` support of the estimate, never extrapolate past it, and report the
  share of total exposure in buckets where the sale count is zero** (`02-c` §3.4).
- *A3 The clock is `slot`.* `occurredAt` is ISO-8601 at unspecified granularity, so any duration derived from
  it can come out zero or negative for two genuinely ordered events, and a hazard model with negative
  durations fails silently. The discrete-time formulation is therefore **forced**, not chosen (`02-c` §3.4;
  `01-b` §4.6(c); adversarial review error 37 makes this a first-class data requirement).
- *A4 First passage is the target, not the recurrent process.* Stop the risk window at the first sale. The
  recurrent rate is **not** the per-ticket rate: a ticket re-enters the risk set only because it proved
  liquid, so pooling first and later sales mixes a population of tickets with a population of *tickets selected
  on having sold*. Never present the two on the same chart (`02-c` §3.6).
- *A5 No unobserved event-level heterogeneity.* **Fails at the event level**; the fix is a shared frailty,
  which is the same object as F17's partial pooling and should be built once, not twice.
- *A6 Redemption's effect on the sale hazard has a known sign.* It does **not** (adversarial review error 8:
  if redeemed tickets have a lower sale hazard, removing them raises the remaining hazard; if higher, it
  lowers it). Fine & Gray supports the competing-risks *correction*, not the sign. State the correction, do
  not state the direction.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `α_b` | baseline log-hazard in bucket `b` | log(1/day) | the fit, one per bucket |
| `β` | covariate effects on the transaction rate | log-hazard per unit | the fit; `x` = `faceValueLamports`, `resalePriceCapBps`, tier size, event category, city, organiser, `requiresVerifiedWallet`, `transferRestricted` |
| `π` | never-transacted fraction | probability | (CI-4) |
| `δ_ic` | cell exposure | days | computed from `slot` |

**Data.** `issue`/`sale`/`transfer`/`redeem`/`revoke` rows, `occurredAt`/`slot`, `issuedAt`, `redeemedAt`,
`Event.startsAt`/`endsAt`, ticket attributes. **Nothing missing.** This is the most data-complete formulation
in the file and needs none of the four listing fields.

**Identification.** T3's identified remainder: the **composite** rate, the cumulative incidence, the
never-transacted fraction, the competing-risks split. **Not** the price response, **not** the split of
`λ_obs` into `s(t)` and `λ(t|p)`, **not** the ask distribution, **not** any counterfactual over the primary
price.

**Evidence class.** **C** for the estimators and estimator properties (established survival methodology).
**D/UNVALIDATED** for the empirical claim that this describes ticket resale timing, **no one has published a
hazard model of a ticket ledger**, which is the opportunity.

**D2 cost.** **Honest.** `k = buckets + covariates`, of order 15–30. Newton–Raphson on a `k × k` observed
information matrix solved by hand-written Gaussian elimination or Cholesky: `O(k³)` ≈ 10⁴ flops per iteration,
trivial. **The ring fence is `k`, not the number of rows**: the design is aggregated cells, tens of columns,
so the fit does not grow with ticket count. Honest for `k ≲ 40`. Above that, either reduce the design (coarser
buckets, fewer interactions) or treat it as specified-not-implemented. Fine–Gray needs inverse-probability-of-
censoring weights and is **implementable with care**, validated against a simulated competing-risks dataset
first, not routine.

**Wrong when.**

- *It is called a sale hazard.* It is a transaction base rate per ticket-day, marginalised over the offering
  state. Plugging it into `1 − exp(−λh)` answers a question nobody asked.
- *It is extrapolated past the `τ` support* or used for a bucket with zero observed sales. A model cannot
  learn a hazard from an empty bucket; it can only be regularised, and the regularisation is a choice that
  must be stated.
- *The cure fraction is read as never-offered.* It is an upper bound on that and a direct estimate of
  never-transacted.
- *First passage and recurrence are mixed.* Two different estimands on one chart.
- *`issuedCount` is used as a sell-through covariate.* It is a snapshot with **no capture time**, so using
  "fraction sold" at time `t` is look-ahead bias unless the snapshot's timestamp is recorded. Until then,
  sell-through enters only as an ex post descriptive statistic, never as a predictor (`02-c` §3.6; `01-c`
  §1.4(3)). This is a `RESEARCH-PROGRAM` §4.8 violation if ignored.

---

### 4.3 F8 · Joint mark–time intensity `ξ(p, τ)` · the realised price-time distribution

**Serves.** P3 as a **descriptive** object and the only honest substitute for a price-response chart in the
interface. Fully observed.

**Mathematics.** Bin time-to-event into cells `b` and markup into bins `m`, and report

```
ξ̂(b, m) = count of transactions in (b, m) / exposure_b                              (XI-1)
```

with `exposure_b` the ticket-days at risk in bucket `b`. It answers "how much trade happens, at what price
levels, and when" with no assumption beyond the ticketing clock. It is behind two aggregates the wire
contract already exposes: `EventAnalytics.priceSeries` (day-bucketed mean sale price) and
`markupDistribution` (six bps buckets).

**Assumptions, in the derivation.** One: the clock. No distributional assumption, no functional form, no
price response. Because it imposes nothing, it identifies what it reports, which is why it is
`02-c` §2.4's correction to `01-b`'s treatment of the left side of (INT-1) as "useless debris".

**Parameters.** None. Bins are a display choice, declared.

**Data.** `sale` rows with `markupBps`/`priceLamports`, `occurredAt`/`slot`, `Event.startsAt`. Nothing
missing.

**Identification.** Identified, and identified as a **transaction-price distribution**. Not a demand curve:
a locus of realised prices where sellers chose the prices traces the intersections of supply and demand and
neither curve (Working 1927). [C]

**Evidence class.** **C**. The trap it replaces, a fitted `λ(p)` read as demand, is **D and dangerous
precisely because it will look estimable** (`01-b` §4.3).

**D2 cost.** One pass and a dictionary. Trivial.

**Wrong when.** It is called a demand curve, or an elasticity is read off it by regressing on it; or the
bins are pooled across tiers in markup space under a binding cap (the cap binds at different absolute prices
per tier, so the pooled bins compare differently truncated objects); or it is used to answer "what if we
listed at X", which requires an ask on the risk set that `ξ` does not contain.

---

### 4.4 F9 · Listing-episode hazard with an ask covariate · gated on the four fields

**Serves.** P3's price response, **once D3's four fields exist**. Status: specified, gated.
`D` M31/M32 role SHIP-BEHIND-ADAPTER.

**Mathematics.** Unit: a listing **episode** `j` on ticket `i`, occupying the half-open interval
`(listedAt, delistedAt]`, truncated at `min(redemption_i, event endsAt)`. Tickets can contribute several
episodes; that is a recurrent-event structure and it is the correct one, not a defect. Event types
`r_j ∈ {sold, cap_blocked, withdrawn, expired}` with `sold` the event of interest and the rest competing.
Ask `p_j` constant within the episode, markup `m_j = p_j/face_i − 1`, scaled ask `z_j = log(1 + m_j)`:

```
λ_j(t) = λ_0(τ(t)) · exp( x_i'β + γ z_j + δ w_j(t) )                            (LE-1)

w_j(t) = the number of OTHER tickets listed in the same tier at t   (depth, the competition axis)

ℓ(θ) = Σ_j Σ_{k ∈ K_j} −λ_{0k} e^{η_jk} Δ_jk  +  Σ_{j : r_j = sold} [ α_{b(D_j)} + η_{j,b(D_j)} ]   (LE-2)

η_jk = x_i'β + γ z_j + δ w_jk
```

`K_j` = the `τ`-cells episode `j` overlaps, `Δ_jk` = overlap length in days. Correctly censored: a
**withdrawn** episode contributes exposure and no failure; an **expired** episode likewise; a **cap_blocked**
episode is a censored observation *in the cap region* and carries extra meaning.

Note (LE-2) is the **same likelihood as (CI-2)** with an episode-level design instead of a ticket-level one.
**The solver does not change.** That is the engineering answer to "what the listing table costs": new rows,
same code.

Target functional:

```
Pr̂(sold within h | listed today at p, τ₀, x) = 1 − exp( −e^{x'β + γz + δw} Σ_{k ∈ (τ₀−h, τ₀]} λ̂_{0k} Δ_k )   (LE-3)
```

and letting `h → τ₀` gives the eventual sale probability of a listing, which must be reported as a
**competing-risks** quantity, sold versus withdrawn, not as a single probability.

Three candidate price-response forms, in the order to estimate them: (i) **nonparametric in price**, replacing
`γz_j` with `Σ_m θ_m 1{z_j ∈ B_m}`, no shape imposed, doubles as the specification test for (ii) and (iii) by
likelihood ratio; (ii) **constant elasticity in markup**, `γz`, `γ` is the elasticity of the sale hazard with
respect to the ask, so `γ = −4` means a 10% higher ask cuts the per-day rate by roughly a third, imposed only
if the nonparametric surface's iso-hazard contours are straight in `(z, τ)`; (iii) **choke-price form**,
`log(1 − p/p*)`, the most interpretable and the one the primary optimisation would consume directly, but a
strong functional commitment that makes the hazard non-monotone in its own parameters near `p*`. Markup, not
lamports, is the right scale: the cap is proportional to each tier's own face, so lamports would make one
coefficient do the work of a per-tier level and a within-tier position. [C]

**Assumptions, in the derivation, and this is the part that decides whether the number is causal.**

- *A1 Proportional form*: the price effect is multiplicative and constant across `τ`, tickets and events.
  Test by interacting `γ` with `τ`-buckets; if the interaction is large the honest output is a `γ(τ)` surface.
- *A2 No unobserved confounding of the ask*: conditional on `(e, g, τ, x)`, the ask is independent of the
  ticket's unobserved sale propensity. **Under A2, `γ̂` is the causal price response. Without A2 it is still
  identified, the ask is a legitimate regressor, but it is the equilibrium locus of chosen asks, i.e. a
  prediction model under the observed ask policy, and NOT `E[sale | we set p]`** (`02-c` §4.3, §1). The ask
  carries the seller's private information about value (Working 1927). Reporting the first as the second is
  the error this whole section exists to prevent.
- *A3 Overlapping spells at different asks exist.* Identification of `γ` comes **only** from
  `Var(ε | e, g, τ)`, the cross-sectional dispersion of asks among tickets co-listed at the same time, in the
  same tier, for the same event. If every seller prices at the same markup at each time-to-event, `z` lies in
  the span of the `τ` dummies, the design is rank-deficient, `γ` is not identified, and the software will only
  say the Hessian is singular. **A listing table in which all sellers set the same price is four fields of
  nothing.** The data requirement is therefore not just the fields but **price dispersion among simultaneously
  live listings** (`02-c` §4.4).
- *A4 The cap stratum must not be pooled with the interior.* A sale at the cap went to the fastest buyer, not
  the highest valuer, so the observed hazard there measures arrival speed under rationing. Include a
  `cap_blocked` indicator and an "ask at cap" indicator, interact them with the price term, or estimate the
  stratum separately (`02-c` §4.5).
- *A5 A normalisation is required and must be chosen, not inherited*: either a parametric baseline shape with
  few `τ` parameters, or a reference markup bin with `θ = 0`. The choice determines what `γ̂` means as a
  number, so it is recorded with the estimate.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `λ_{0k}` | baseline hazard per `τ` cell | 1/day | the fit |
| `β` | ticket/event covariates | log-hazard | the fit |
| `γ` | **elasticity of the sale hazard w.r.t. the ask** | dimensionless | within-`(e,g,τ)` ask dispersion, A3 |
| `δ` | depth (competition) effect | log-hazard per competing listing | the fit |
| `p*` | choke price (form iii only) | lamports | the fit, weakly |
| `z_j`, `w_j(t)` | scaled ask, contemporaneous depth | dimensionless, count | **the four listing fields** |

**Data.** All four of D3's fields: `listPriceLamports`, `listedAt`, `delistedAt`, `delistReason`, with
`cap_blocked` the most valuable enum value, because it is the only observation in the whole design that
separates "nobody wanted it" from "everybody wanted it and the cap rationed them". Without it, a failed
listing at the cap is indistinguishable from a failed listing at a delusional price. Plus live-listing depth,
which the four fields also supply. **This is why `listPriceLamports` is worth more than the other three
combined and `delistReason` is second** (`02-c` §1.5).

**Identification.** **The secondary price response, and only that.** `γ` is the hazard *given the ask the
seller chose*. It does not identify the primary demand response: the primary optimum's demand input is T4b
(§5), a different population, a different bundle, and a capped upside. **The four fields close one of two
identification gaps** (`02-c` §1.6; C3, §12). Even with A2 satisfied, `γ̂` identifies the response to an *ask
under the observed ask policy*, and a randomised ask arm is the only clean route to a counterfactual, 
a money and commercial decision, therefore the operator's.

**Evidence class.** **C** for the likelihood and the identification argument. **D/UNVALIDATED** for `γ̂`'s
usefulness even once fitted, and **D for the causal reading** unless A2 is licensed by an experiment.

**D2 cost.** Same solver as F7, same `k ≲ 40` ring fence, `k × k` Newton. **Honest.** The four fields add rows,
not columns of a new kind. Depends on data, not on computation.

**Wrong when.**

- *A2 fails and the result is called a demand curve.* The default failure mode, and the one that will look
  like it worked.
- *Ask dispersion is absent.* Then `γ` is not identified and the honest output is "not identified", not a
  singular-matrix traceback.
- *The cap stratum is pooled with the interior.* Biases `γ` toward the rationing regime's mechanics.
- *`occurredAt` is used for the clock.* Use `slot` (A3 of F7).
- *Time-to-event and the ask are collinear by construction*; they genuinely are, since prices fall as the
  event approaches and the hazard rises. Publish, **before any `γ̂`**: (a) the within-`(e,g,τ)` variance of
  `z` and its ratio to the total; (b) the `R²` of `z` on `(e × g × τ)` dummies; (c) the condition number of
  the information matrix; (d) the count of `τ`-cells containing more than one distinct observed ask.

---

## 5. P4 · Elasticity

### 5.1 F10 · Primary sell-through demand bracket (Tobit with an observed censoring indicator)

**Serves.** P4, and through it **P5's demand input**: this is the corrected link (C3, §12). Target T4b.

**Mathematics.** Each tier `k` carries `faceValueLamports` `p₀ₖ`, `totalSupply` `Nₖ` and `issuedCount`
`issuedₖ`. A tier is one of two things:

```
sold out  (issuedₖ = Nₖ)   →  demand met or exceeded supply:  D*ₖ ≥ Nₖ      [CENSORED]
not sold  (issuedₖ < Nₖ)   →  demand equals issued:           D*ₖ = issuedₖ  [A POINT]
```

That is a Tobit with an **observed** censoring indicator, the benign case, because the censoring threshold
`Nₖ` is known and the indicator is recorded. Latent demand

```
D*ₖ = a + b·p₀ₖ + c'zₖ + uₖ,     uₖ ~ N(0, s²)                                (ST-1)

ℓ = Σ_{unsold} [ log φ((issuedₖ − a − b p₀ₖ − c'zₖ)/s) − log s ]
  + Σ_{sold out} log ( 1 − Φ((Nₖ − a − b p₀ₖ − c'zₖ)/s) )                      (ST-2)
```

and the own-price elasticity at a tier's own price

```
ε̂ₖ = b̂ · p₀ₖ / D̂*ₖ                                                            (ST-3)
```

**Cross-event and cross-tier variation in face value is what bounds the schedule.** This needs **no secondary
data at all**, which is `01-b` §4.4(i)'s highest-value finding. It is the inverse of demand estimation under
incomplete availability (Conlon & Mortimer 2013): availability is *observed* and demand is not.

**Assumptions, in the derivation.**

- *A1 Uniform primary pricing within a tier*, one `p₀` per tier, no mid-sale revision. Testable for free:
  `faceValueLamports` is carried per **ticket**, so if the organiser revises mid-sale, tickets within one tier
  will carry different face values. **If within-tier face value is constant on the first real dump, the
  primary price is static per tier and the entire dynamic-primary-pricing question collapses to a single
  static optimisation** (`01-c` §1.4(4)). This is the cheapest test in the file.
- *A2 `faceValueLamports` = the primary transaction price.* **May not hold**: a discount or fee breaks it,
  and post-May-2025 US all-in disclosure rules make the distinction sharper (`02-d` §1.1). Operator question.
- *A3 `issuedCount` = sold.* **May mean minted.** Load-bearing: under A3 the sign of the bracket is right;
  under its negation the sold-out indicator is uninformative (`02-e` §10.1, C10).
- *A4 `zₖ` (event, city, category, tier rank) is exogenous to `D*`.* Weakly held; the organiser chooses tiers
  partly on expected demand, which is the same endogeneity Working (1927) names.
- *A5 `uₖ` normal.* Does real work; untestable with the coarseness of `issuedCount`.
- *A6 No supply-side response within the window*, the organiser does not add or withdraw inventory in
  response to sales. Unverified.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `a` | baseline demand | tickets | the fit, across tiers and events |
| `b` | demand slope in price | tickets per lamport | the fit; **identified from cross-tier/cross-event face variation only** |
| `c` | event/tier covariates | tickets per unit | the fit |
| `s` | demand dispersion | tickets | the fit |
| `Nₖ`, `issuedₖ`, `p₀ₖ` | supply, sold, price | tickets, tickets, lamports | **data**, per tier |

**Data.** Per-tier `faceValueLamports`, `totalSupply`, `issuedCount`. **All present in the contract.** The
weakness is not missing fields but **`n` = the number of tier-events**, which is small, and the absence of a
time series (so velocity is unobservable and only the level is identified, which is exactly enough, per
`01-b` §5).

**Identification.** T4b: **set-identified from primary sell-through, bounded below at each distinct cap
level**; the *sign* at each observed face value is identified, and `ε ≤ 1` in the neighbourhood of observed
prices is supported by the literature (`02-d` §3.4). **A level is not identified** and no functional form is
validated.

**Evidence class.** **B**: Tobit-type structure is standard and the sell-through-as-demand-bracket argument
is borrowed from the incomplete-availability literature. **UNVALIDATED** for any functional form.
`D` M24 is gated on A3.

**D2 cost.** **Honest and small.** A censored-normal likelihood in `p = 4` parameters: Newton or EM on a 4×4
information matrix, or EM with the same inverse-Mills machinery as F3 (`statistics.NormalDist`). No library.
Cost is negligible.

**Wrong when.**

- *A3 is false* (`issuedCount` = minted, not sold), the censoring indicator is then meaningless and the
  bracket is void.
- *A1 is false* (the organiser revises price mid-sale), then `p₀` is endogenous to within-tier demand and
  `b` is biased.
- *Face value is discounted below the stated price*, so `p₀` is not the transacted price (A2).
- *`n` is small and events are heterogeneous*, then `b` is identified off a handful of face-value
  contrasts and its standard error is the whole story. Report the contrast count, not just the coefficient.
- *It is treated as an elasticity of demand under a resale cap.* **No study in the literature estimates
  demand under a resale cap**; the regulatory analyses model caps with assumed displacement, not estimated
  elasticities (`02-d` §3.3, a negative search result). Any cap-adjusted elasticity is invented.

---

## 6. P5 · The primary optimum

### 6.1 F11 · The objective, the fee wedge, and the first-order condition

**Serves.** P5. It is the only part of P5 that is **exact algebra** rather than an assumption, which is why it
is the most defensible thing in this section.

**The objective.** One event, tiers `k = 1..K`, `Nₖ` units offered in tier `k`, `Q = ΣNₖ`, decision vector
`p = (p₁, …, p_K)` in lamports. Buyer's all-in cost `Pₖ = pₖ(1+βₖ) + bₖ`; organiser's net per unit sold
`mₖ(pₖ) = (1−φₖ)pₖ − fₖ + aₖ`. Demand `Dₖ(p, ξ)` realised after the price is set, under state `ξ`; units sold
`Sₖ = min(Dₖ, Nₖ)`; per-offered-unit sale probability `qₖ(p) = E[Sₖ]/Nₖ`, the **truncated** demand, not
demand.

```
Π(p) = Σ_k Nₖ [ qₖ(p)( mₖ(pₖ) + uₖ ) − uₖ ]  +  ρ·E[T(p)]  −  F          (OBJ)
```

`T` = resale turnover, `F` = fixed cost. **Assumptions used in writing (OBJ), stated as part of it:**

- *A1* Paid per unit sold at the time of sale, no settlement lag or default. A lag `Δ` contributes
  `e^{−rΔ}` multiplying the whole objective, **neutral for `argmax`**, level only. [C]
- *A2* No refunds or chargebacks. With refund probability `r`, `mₖ` becomes `(1−r)mₖ − r·(refund cost)`:
  an **additive per-unit term, so it behaves exactly like `−f`**. [C]
- *A3* The resale royalty term is second order and **bounded, not estimated**: on the most resale-active
  sample in the literature, total resale profit is "slightly over $1.17 million … equivalent to 1.4% of the
  total primary market revenue", against a 41% mean markup (`02-d` §1.5, class A, read from the paper). Even a
  royalty capturing 100% of the resale *spread* adds about 1.4% of primary revenue.
- *A4* Cross-event demand effects are absent by construction (one event at a time).
- *A5* All quantities are expectations, so (OBJ) is **risk-neutral**; §6.3 replaces it.
- *A6* `q = 1` is not assumed anywhere. **The objective is non-degenerate only because `u` and `a` are in it**; see the degeneracy below.

**The first-order condition, derived.** Single tier (`K = 1`), so drop the subscript. Differentiating (OBJ)
in the decision `p`, with `dP/dp = 1+β` and `dq/dp = q'(P)(1+β)`:

```
Π'(p)/N = q'(P)(1+β)(m+u) + q(P)(1−φ) = 0
```

With the elasticity of the **truncated** demand `ε(P) = −P q'(P)/q(P) > 0`, substituting `q' = −εq/P` and
dividing by `q`:

```
ε(P)(1+β)(m+u) = (1−φ)P                                              (FOC-1)
```

Now `m+u = (1−φ)p − f + a + u` and `p = (P−b)/(1+β)`, so

```
(1+β)(m+u) = (1−φ)(P − b) + (1+β)(a + u − f)
```

Substituting into (FOC-1) and dividing through by `(1−φ)` gives, with the **wedge**

```
c** ≡ b + (1+β)(f − a − u)/(1−φ)                                     (WEDGE)

ε(P)·( P − c** ) = P        ⟺        (P − c**)/P = 1/ε(P)   ⟺   P = c**·ε/(ε−1)   (FOC-2)
```

**Result, and it is exact algebra for any demand function `q(P)`: the entire fee stack `(φ, β, f, b)`, the
ancillary `a` and the empty-seat cost `u` enter the recommended all-in price through the single scalar
`c**`.** Everything else about the stack changes the reported profit level and not the recommendation.

**Four consequences, each an answer to a question the programme asks.**

| # | Result | Class |
|---|---|---|
| (i) | **Ad-valorem fees are neutral for the optimum.** With `f=a=u=b=0`, `c**=0` and (FOC-2) reduces to `ε(P)=1`, independent of `φ` and `β`. A proportional fee rescales the objective by a positive constant and cannot move its argmax; a buyer-side proportional fee is neutral in the all-in price and only rescales the posted price by `1/(1+β)`. | **C** (exact), B support from the standard incidence result for proportional vs specific taxes under imperfect competition |
| (ii) | **Per-unit fees are not neutral and act as marginal cost.** With `f>0` only, `c**=f`, and (FOC-2) reads `ε = P/(P−f) > 1`, placing the optimum at a *higher* elasticity than the no-fee case. The seller under-shifts: pass-through `∂p*/∂f ∈ (0,1)` under log-concave demand. | **C**, B support |
| (iii) | **The empty-seat cost has the opposite sign to the fee and is what makes the model non-degenerate.** With `u>0` only, `c** = −u/(1−φ) < 0`, so `ε = P/(P − c**) < 1` (since `c** < 0`): the organiser accepts an inelastic price point in exchange for filling seats. With `f=a=u=0` and no capacity constraint there is nothing to trade off and the objective is revenue, whose optimum is the unit-elastic point or a corner. **Drop `u` and `a` and the model has no interior optimum on a sell-out event.** | **C** |
| (iv) | **Refunds and chargebacks are a per-unit term.** Under A2 a sold unit yields the price with probability `1−r` and a refund obligation with probability `r`; the effective deduction enters **exactly like `f`** and shifts the optimum up. It also raises revenue variance, which is §6.3's problem, not this one. | **C** |

**This narrows D4 and corrects it in one respect.** D4 said a per-unit fee and an ad-valorem fee give
different optima, right, but the sharper statement is that **one of them gives no different optimum, and it
is the one everybody worries about** (C7, §12). Consequence for a settlement field: **a field that records
only the percentage fee buys nothing for the price recommendation.** The field that matters is the one
revealing the **fixed per-ticket component**: the opposite of what a "fee field" is usually specified to
contain, and the single most actionable sentence about Gap 4 (`02-d` §2.6).

**Parameters.**

| Symbol | Interpretation | Units | Estimated / supplied by |
|---|---|---|---|
| `φₖ` | organiser-side ad-valorem fee rate | `[0,1)` | **config**; not in contract |
| `fₖ` | organiser-side per-unit fee | ≥ 0 lamports | **config**; not in contract |
| `βₖ` | buyer-side ad-valorem rate | ≥ 0 | **config**; `0` in the US post-2025 |
| `bₖ` | buyer-side per-unit fee | ≥ 0 lamports | **config**; `0` in the US post-2025 |
| `aₖ` | ancillary margin per attendee | ≥ 0 lamports | organiser's own accounts |
| `uₖ` | cost of an offered-but-unsold unit | ≥ 0 lamports | organiser's own accounts; see the decomposition below |
| `ρ` | organiser's royalty on resale turnover | `[0,1]` | config; term bounded at ~1.4% of primary revenue |
| `c_k` | resale ceiling as a decimal `cap_bps/10⁴` | ≥ 0, `null → ∞` | contract |
| `qₖ(p)` | truncated sale probability | probability | **not identified as a function of price** (F9/F10) |
| `ε` | elasticity of the truncated demand | dimensionless | **not identified**; `ε ≤ 1` near observed prices from the literature |

**`uₖ` decomposed, because three of its four components are real and one is a trap** (`02-d` §1.4):

1. *Sunk production cost of the seat*: **zero**. It is not a cost of leaving a seat empty; it is paid either
   way. Including it is the commonest error in this calculation. [C]
2. *Foregone ancillary per empty seat*: real and equal to `aₖ`, but (OBJ) already carries it through
   `m+u−u`. Adding `aₖ` to `uₖ` as well **double counts**. The correct statement is that `uₖ` is everything
   *other than* the ancillary already inside `mₖ`. [C]
3. *Sponsor, attendance and venue obligations*: real, positive, event-specific, usually a **step** function
   (a bonus at sell-out) rather than a per-seat line. Approximating a step as linear is a modelling choice
   that must be reported. [D]
4. *Strategic value of a sell-out*: real, unmeasurable here. Belongs in `uₖ`; cannot be estimated. Flag it. [D]

**Evidence class.** **C** throughout the algebra. The *objective* is class C. Its inputs are mostly `config`
or not identified, which is the honest state of P5.

**D2 cost.** (FOC-2) is closed form: one division. (OBJ) evaluated on a grid is `O(G·M)` for `G` candidate
prices and `M` scenarios, microseconds. No matrix.

**Wrong when.**

- *`u` and `a` are dropped.* Then the model has no interior optimum on a sell-out event and the answer is a
  corner presented as a solution (§6.1(iii)).
- *The elasticity is inverted to produce a price.* `p* = c**η/(η−1)` is for **interpretation and directions
  only**. `Π` is not guaranteed unimodal, so the implementation rule is **maximise on a grid** (§6.2).
- *The measured relationship `∂p*/∂η = −c**/(η−1)²` is read as reassuring.* It is not: for `η` near 1 the
  ratio `c**/(η−1)²` is **large**, so `p*` is *very* sensitive to a parameter we do not have. An elasticity
  near 1 makes the answer depend almost entirely on the assumption.
- *`ρ` is read as a capture rate.* There is **no** "share of resale margin the organiser can capture through
  pricing" term: under a cap defined in basis points over face, the ceiling moves with the decision, so there
  is nothing left over to capture by a separate mechanism (§6.2 below, `02-d` §1.5).
- *The fee stack is assumed ad-valorem-only, or zero.* D4's specific prohibition; and (i) above shows the
  assumption that matters is the one about the **per-unit** component.

---

### 6.2 F12 · Static grid optimiser with the boundary rule

**Serves.** P5. This is the recommendation engine, and its honest output is a **range and a rule**.

**Mathematics.**

```
p* ∈ argmax_{p ∈ 𝒫} Π(p),      𝒫 = { p : q_k(p) ≥ q_min }                       (RN)
```

solved **on a grid**, because `Π` is not guaranteed unimodal. `q_min` is the organiser's sell-through floor,
supplied as config. With constant elasticity, used only to read the comparative statics:

| Case | Condition | Optimum |
|---|---|---|
| (i) Interior | `c** > 0`, `η > 1` | `P* = c** η/(η−1)` |
| (ii) **Sell-through boundary** | `c** ≤ 0`, or `η ≤ 1`, or the interior `P*` is below the price at which the house fills | `P*` = the highest all-in price at which expected sell-through still meets the floor |
| (iii) Degenerate | `q = 1` over the candidate range and `c** = 0` | `Π` strictly increasing; keep raising until (ii). **No maximum exists** |

**Diagnostic, exact from `p*/c** = η/(η−1)` and no data:**

| `η` | 1.2 | 1.5 | 2.0 | 3.0 | 5.0 |
|---|---|---|---|---|---|
| `p*/c**` | 6.00 | 3.00 | 2.00 | 1.50 | 1.25 |

Read it this way: if the effective per-ticket wedge is 5% of face and `η = 1.5`, the interior optimum is
`3 × 5% = 15%` of face, far below any observed face value, so the interior condition is infeasible and the
boundary rule applies. **The table is a diagnostic on the model, not on a market** (`02-d` §5.2).

Why the boundary dominates here, in two independent ways (`02-d` §3.4, §5.2):
1. **Demand is inelastic at observed primary prices**: the standard result in the sports-attendance
   literature, per the quoted characterisations (`02-d` §3.2, class A for the characterisations), so
   `ε ≤ 1` near the current price, which with `c** ≥ 0` implies the current price is left of the optimum.
   The defensible, evidence-backed recommendation is **"raise"**, with the size set by the boundary.
2. **The venue fills.** Mean capacity utilisation 0.99 across 56 concerts (`02-d` §3.2, class A), so the
   primary price is infra-marginal, `∂q/∂p ≈ 0` by construction, and the Lerner term is empty.

**Assumptions, in the derivation.** (i) The demand system `Dₖ(p,ξ)` is known up to parameters, **it is
not**; this is why the output is a set over the parameter box. (ii) `q_min` is the organiser's true floor.
(iii) The event is priced alone (A4 of (OBJ)). (iv) No reprice is possible, so this is a **static** problem;
`TicketTier.faceValueLamports` is per tier and static and `API_CONTRACT.md` has no price-mutation endpoint
(9 endpoints, 7 reads, 2 wallet-verification POSTs). **A dynamic policy is a schema and product change, which
is the operator's decision, not the model's** (`02-d` §1.1, §4.4).

**Parameters.** `c**` (from F11's components), `ε` (config, or the `ε ≤ 1` bound), `u`, `q_min`, `G` the grid
size. Typically 4 parameters, of which **two are assumptions the report must name**.

**Data.** `Nₖ`, `p₀ₖ` from the contract; `qₖ` from F10 once it exists; the fee stack from config.

**Identification.** T5: **a set with bounds, not a point**. Per adversarial review error 13 the identified
set is the **image of the input sets under the optimisation map**: so it is produced by mapping the
`(ε, u, q_min)` box through (RN) and reporting the resulting range of `p*`, not by taking a union of widths.

**Evidence class.** **C** for the method and the boundary rule. The *prize* is class A: **5%** of revenue
from multi-tier pricing across 21,120 concerts, and **3.4%** (≈$27k per event) from repricing the top decile
of a 56-concert sample; the latter a **model-based counterfactual, not an observed adoption**. Both
single-digit, and that disciplines any enthusiasm.

**D2 cost.** `O(G·M)`, a double loop. **Honest.** With `G = 41` prices and `M = 10⁴` scenarios this is about
4×10⁵ evaluations of a few arithmetic operations: seconds in CPython, for a decision made once per event.

**Wrong when.**

- *A point optimum is reported.* Not identified; report the set and the boundary.
- *The elasticity is invented.* Anything hard-coded from the published table is a fabricated parameter
  (`02-d` §3.3). Report `η` as config and publish `∂p*/∂η`.
- *The elasticity of demand `ε_D` is used instead of the elasticity of truncated demand `ε`.* `ε_own ≤ ε_D`
  whenever capacity truncation is active, so using `ε_D` **understates the recommended price**.
- *Multi-tier is claimed to be worth more than it is.* The measured prizes are 5% and 3.4%; and the
  single-static-price case is stronger than usual here because there is **no within-tier heterogeneity axis**
  (Gap 3), so an extra tier buys nothing inside an existing tier and the useful move is **one parameter, the
  level**, needing one unknown (`ε_own`) instead of `K + K(K−1)/2`.
- *Dynamic pricing is claimed as a modelling option.* It is not implementable: no reprice endpoint, and no
  state variable to condition on, so its value is not measurable here and must not be claimed.

---

### 6.3 F13 · Mean-CVaR risk adjustment

**Serves.** P5 and P6. The only formulation that puts a risk functional **inside** the objective rather than
bolted on afterwards.

**Mathematics.**

```
max_p  (1−λ) E[Π(p)]  +  λ CVaR_α(Π(p)),      CVaR_α(X) = max_v { v − α^{−1} E[(v − X)^+] }     (CVAR)
```

For a finite scenario set with equal probabilities this reduces to **a sort plus a partial mean**:

```
CVaR_α = −(1/k) Σ of the k = ⌈αM⌉ WORST outcomes,    O(M log M) per candidate price
```

CVaR is coherent, subadditive, monotone, positively homogeneous, translation-invariant, and it penalises
exactly the risk this business carries: unsold inventory at the deadline.

**Assumptions, in the derivation.** (i) The scenario set stands in for the demand distribution. It does not
represent it: it is a **declared** set, and `λ, α` are config with defaults. (ii) The decision is
one-dimensional, so a grid search over `p` is exact to grid resolution and the LP formulation is unnecessary.
(iii) Outcomes are measured in profit, so the functional is on the right scale.

**Parameters.** `λ ∈ [0,1]` (weight on the risk term, default 0.5), `α` (tail level, default 0.1), `M`
(scenario count). All config; all named in the report.

**Data.** None beyond `Π`'s inputs and the scenario set.

**Identification.** Serves T5/T6; identifies nothing itself. It **chooses** a point from the identified set,
and the choice is the operator's preference, which is why `λ` and `α` are printed.

**Evidence class.** **C** for the algebra and for coherence. The claim that CVaR is the right functional for
this business is **D**.

**D2 cost.** **Honest** by sorting. The Rockafellar–Uryasev LP representation is **specified-not-implemented**
under D2 (no LP solver), and unnecessary here, because the decision is one-dimensional and the grid is exact
to resolution. **Not implementable:** CVaR over a joint multi-tier price vector with capacity coupling and a
Wasserstein ambiguity set (convex program), and exact VaR optimisation (non-convex; enumeration or MILP).

**Wrong when.**

- *`λ` and `α` are hidden.* They are the organiser's risk preference, not ours to choose silently.
- *Mean-variance is used instead.* It penalises **upside** as well as downside, the wrong attitude for a
  pricing decision whose whole point is to move the upper quantiles, and its scale grows with `N²`, so `γ`
  must be re-tuned per event size, which is unportable across events selling 3,169 to 34,844 tickets
  (Leslie & Sorensen's sample range, class A). **Implementable, not recommended.**
- *The sign of the risk correction is asserted.* It is **ambiguous and derived**: truncation at `N` flattens
  the quantity response and pushes the risk-neutral optimum **up**; downside-risk aversion pushes it **down
  exactly when the adverse-state demand is elastic** (`ε_D > 1`) and has no effect when it is inelastic.
  Which dominates is an empirical question this programme cannot answer (`02-d` §5.1).

---

### 6.4 F14 · Reserve-price surface by backward induction

**Serves.** P5 as a policy and P2 as a state's transition law; it is the only formulation that can express
the primary–secondary feedback. **Specified-not-implemented** (`D` M49).

**Mathematics.** Discrete-time MDP over the state

```
s = ( inventory-remaining bucket, days-to-event bucket, cap-binding regime )
```

with about 6, 12 and 3 cells respectively, **216 states**. Backward induction:

```
V_t(s) = max_{ p ∈ grid } { r(s, p) + γ E[ V_{t+1}(s') | s, p ] }
p*(s)   = inf{ p : sell-value at p ≥ continue-value at p }                      (MDP-1)
```

The **implementable object is a reserve-price surface `p*(τ, inventory, cap-binding)`, a scalar per state,
not a value function**, which is dramatically smaller and is what the optimiser actually consumes. Latent
value enters by **certainty equivalence**: the F3 prediction as the state's location and F6's state-space
variance as its uncertainty, a reduction that must be **declared**, since the true problem is a partially
observed MDP.

**The coupled system, which is what Phase 3 asks for.** For this platform the coupling is specific and short,
a Stackelberg structure rather than a general equilibrium:

```
platform sets p₀  →  ceiling = p₀(1+c)  →  resale market clears under the ceiling
                 →  resale price and liquidity  →  buyer's resale option value
                 →  primary willingness to pay  →  primary sell-through at p₀
```

Because the platform moves first and the resale market clears within the event, the right computational
structure is: solve the **follower** (resale clearing given `p₀` and the ceiling), then optimise the
**leader's one-dimensional problem** over `p₀`. **That is a nested one-dimensional search, not a fixed point
in a high-dimensional space**: an outer grid over `p₀` (say 41 points), an inner fixed-point iteration of a few
sweeps.

**Assumptions, in the derivation, and which fail.**

| # | Assumption | Status |
|---|---|---|
| 1 | a controlled Markov state with a **known** transition law | **Fails.** The transition law is T2, identified in curvature only; the linear trend is a normalisation |
| 2 | the state is observed | **Fails.** Latent value is unobserved; the workable reduction is certainty equivalence and it must be declared |
| 3 | a terminal condition `V(T,n) = 0` | **Fails as usually written.** A ticket's terminal payoff is an unobserved **use value**: `V(T,n) = n·u` with `u > 0` for any owner who might attend. Expiry is a wall, not an anchor, value **jumps** at the boundary rather than approaching it |
| 4 | a reward and a risk functional | Holds, and is the family's real contribution |
| 5 | the action does not move the environment | **Fails, and it matters**: the primary price sets the resale ceiling. That is the whole reason F11's `c**` algebra is worth having |

**The one measurably testable prediction, and it links to the strongest empirical anchor in the literature.**
Because `u` is heterogeneous, the observed path is a **mixture**: with `u` small the reserve decays toward the
market as the deadline approaches, reproducing Sweeting's steep endgame declines; with `u` large the reserve is
approximately `u` and the price path is flat or rising. **So the curvature of the fitted `τ`-spline in F5 is
informative about the distribution of `u`**: this is the cleanest link in the whole record between an
unidentified quantity (T2's level) and a partly identified one (its shape). [C] And the endgame is a
**withdrawal decision**, so the `withdrawn` versus `expired` split in `delistReason` is what identifies it.

**Parameters.** Per state: `p*(s)`. Plus `u`, `γ` (discount, ≈1 within an event), the grid resolutions, and
`λ, α` from F13 if the risk functional is inside.

**Data.** `delistReason` for `u` (withdrawal versus expiry) and a primary inventory time series (Gap 5) for
the coupled system. Both are **missing**, which is why this is specified rather than implemented.

**Identification.** Serves T5 as a **set of surfaces over the demand-parameter box**, because the demand
function is not identified and reporting one surface would be overclaiming. What this buys over a single
number is a statement of the form *"above this price the recommendation is insensitive to the elasticity we
cannot estimate; below it, it is not"*: exactly what a set-identified problem can honestly support.

**Evidence class.** **C** for the method and the CVaR algebra. **B** for the empirical phenomenon the model
explains, declining prices as expiry approaches (Sweeting 2012, class A per `01-a` §2). **D** for the coupled
primary–secondary formulation, which nobody has estimated.

**D2 cost.** **Split down the middle, and the split is cosmetic.** Discrete-time backward induction on a small
grid: **yes, and it is the whole answer**: 216 states × a 41-point price grid is about 9×10³ evaluations per
stage, microseconds to milliseconds in pure Python, no matrix. **Continuous-time HJB as a PDE: no**: it needs
a solver, and the discrete DP *is* the numerical solution of the same problem, so the distinction is
presentational as long as the grid is presented as the approximation it is.

**Wrong when.** The terminal value is set to zero (it is `n·u`, `u > 0`); certainty equivalence is used
without declaration; one surface is reported instead of a set; or `γ` is set to something other than ≈1, 
within a single event's horizon there is no meaningful discounting.

---

### 6.5 What actually composes into the pricing decision

The composition, stated so it is auditable, and with the correction of C3 applied:

```
F10 sell-through bracket  ──►  ε, or the ε ≤ 1 bound, or "not identified"
        (the ONLY level-bearing demand input)                        │
                                                                     ▼
F11 (OBJ) + (WEDGE) + (FOC-2)  ◄── config: φ, f, β, b, a, u, q_min, ρ
        │                                    ▲
        │                                    └── D4: supplied, never assumed
        ▼
F12 (RN) grid over p ∈ 𝒫, boundary rule  ──►  the recommendation, as a SET
        │
        ├── F14 (MDP-1) if a policy rather than a static price is wanted: gated on Gap 5 + delistReason
        ├── F13 (CVAR) for the risk-adjusted member of the set
        ▼
what the organiser sees: a price, a range, the two parameters that had to be assumed,
and the conditions under which the recommendation is wrong
```

**And the part that is missing, in one line:** the resale record enters P5 only through the **residual** demand
curve, because under a proportional cap substitution between primary and resale is already inside `ε_own`
(`02-d` §2.5(c)). **It does not enter as a level.** That is why the primary recommendation cannot be read off
the secondary price, and why C3 matters.

---

## 7. P6 · Uncertainty

### 7.1 F15 · Prequential proper scoring and the reliability decomposition

**Serves.** P6 for the **sale indicator**, where the population is complete. This is the one calibration task
fully available today, and it needs **no calibration set** because it is scored on the whole population.

**Mathematics.** For forecast `f` and outcome `o`:

```
Brier  = (1/n) Σ (f_i − o_i)²                                             (SCORE-1)
       = REL − RES + UNC                                                  (reliability decomposition)
```

with `REL = (1/n) Σ_k n_k (f̄_k − ō_k)²` over forecast bins, `RES = (1/n) Σ_k n_k (ō_k − ō)²`,
`UNC = ō(1−ō)`. Plus reliability curves and log score. Prequential (sequential) scoring: at each forecast
timestamp `t`, fit on data strictly before `t` and score the next block, which enforces the leakage boundary
that actually matters (`RESEARCH-PROGRAM` §4.8) and is the same protocol F5's validation uses.

**Assumptions, in the derivation.** (i) The population is **censused**: every ticket appears, with a known
life, so every ticket contributes an outcome. This is what makes the score honest, and it is `01-b` §4.6's
substantive result. (ii) The scoring rule is **proper**: otherwise the comparison of models rewards the wrong
thing. (iii) Forecasts are made from information available at the forecast timestamp, not from the label.

**Parameters.** None for the score. Bin count is a display choice.

**Data.** The full ticket population with `issue` and exit, plus the model's forecasts. No missing field.

**Identification.** T6's **estimable** half: calibration for the sale indicator is computable honestly on
every ticket.

**Evidence class.** **C**.

**D2 cost.** Trivial: arithmetic and a sort. `O(n)`.

**Wrong when** it is applied to a **price** distribution. Every scored observation is then conditioned on
"sold at this price", and whether a ticket sold is the very dependence being measured, the selective-labels
problem. The mature analogue, reject inference in credit scoring, generally fails to improve performance.
**Report the interval, label the calibration UNVALIDATED, quote no coverage number.** This is `01-b`'s T6 and
it is the boundary of this formulation.

---

### 7.2 F16 · Empirical quantile band, scoped to transactions

**Serves.** P6 where nothing else is available. The honest answer to "give me an interval" with no calibration
set.

**Mathematics.** Among comparable tickets that resold, report the empirical quantiles of the realised
`price/face` ratio. Optionally bin by the hedonic's fitted value and take empirical quantiles within bins:

```
band = [ Q̂_q(y | bin), Q̂_{1−q}(y | bin) ]        exact within the bin
```

Three usable substitutes, in order of honesty (`01-c` §8.3):

1. **Empirical quantiles of the realised price ratio, scoped to transactions.** Honest because it is
   explicitly conditional, and it is what an operator actually needs. Cheap, exact, no assumption.
2. **Quantile regression on the hedonic** for conditional quantiles. **D2 caveat:** exact quantile regression
   is a **linear program** and D2 has no LP solver. IRLS is the standard approximation and it is an
   *approximation with no guarantee of exact quantile optimality*, so binned empirical quantiles are
   preferred: exact within the bin, cruder in resolution, and honest about which.
3. **Prequential scoring for the sale indicator** (F15).

**Assumptions, in the derivation.** (i) The scored sample is the *traded* one, so the band describes traded
tickets, and resold tickets are the better seats (mean seat-quality percentile 0.61 vs 0.50, class A), **the
band is biased up for a randomly chosen ticket and it says so**. (ii) Bin membership is exogenous to the
outcome, which is an assumption of the binning, not a result.

**Parameters.** None estimated. The quantile level and the bin count are display choices.

**Data.** `sale` rows. Nothing missing.

**Identification.** Serves T6 as a **declared conditional band**, not a coverage guarantee. Conformal
prediction is **rejected** for exactly this reason: it *is* a procedure that consumes a calibration set, and
the only calibration set this market can supply is drawn from **sold** tickets, whose observations are not
exchangeable with a test ticket that may not sell, so the guarantee is void by its own hypothesis, not
merely hard to compute (`01-c` §8.1).

**Evidence class.** **C** for the empirical quantile; the description of the traded subpopulation is **A**
(seat quality `01-a` §6). `UNVALIDATED` as a predictor.

**D2 cost.** A sort. Trivial.

**Wrong when.** It is presented as a forecast interval for an arbitrary ticket; it is computed on a sample
that includes censored observations beyond the cap (use only quantiles below the cap mass, F4); or an
out-of-sample coverage statement is attached to it, which is not available.

---

### 7.3 F17's cold-start quantiles

The one place a mixture quantile is computed rather than read off: F17's grid posterior gives a mixture of
normals, and its quantiles are found by bisection on the mixture CDF (`02-e` §4.8, `mixture_quantile`). That
belongs to P7 and is recorded there. Noted here so P6's methods list is complete: **the cold-start band is the
only interval in this file with a probabilistic derivation, and its width is declared, not calibrated.**

---

## 8. P7 · Cold start

### 8.1 F17 · Normal–normal partial pooling (empirical Bayes) · the estimator

**Serves.** P7 for the **price level**, T1′ directly, T4a through tier effects estimated from few sales, and
the event-level frailty of F7. **Declared, not estimated, below about five events.** This is `D` M07 and, per
D5, the programme's single fitted estimator.

**Mathematics.**

```
within:   y_ij = log(p_ij / f_ij) ~ N(θ_j, σ_j²)
between:  θ_j ~ N(x_j'β, τ²)                                            (EB-1)
```

with `β` flat-prior. Cold start takes `x_j' = 1`, so `β` collapses to a scalar `μ`: **two hyperparameters,
`μ` and `τ²`.** Covariates are added one at a time and only once `J ≥ k + 3`, in a fixed pre-declared order
(log face, tier count, sell-through state, city), with `J` this small, data-driven selection is fitting noise.

Given `τ²`, the shrinkage weight and the estimate:

```
B_j = τ²/(τ² + s_j²),    θ̂_j = B_j y_j + (1 − B_j) ȳ(τ),    ȳ(τ) = Σ_j y_j/(s_j²+τ²) / Σ_j 1/(s_j²+τ²)   (EB-2)

B_j is the weight on the event's OWN mean;  1 − B_j the weight on the population mean.
```

(EB-2) is the posterior mean `(y_j/s_j² + μ/τ²)/(1/s_j² + 1/τ²)` rearranged. `B_j` increases in `τ²` (events
really do differ) and in `n_j` (this event has its own evidence), and **does not depend on `μ`**.

**Two limits are the whole cold-start story:**

```
a genuinely new event  →  s_new² = ∞  →  B_new = 0  →  θ̂_new = ȳ(τ)      (the population mean)
therefore  τ² DOES NOT ENTER THE COLD-START POINT ESTIMATE AT ALL.
           It enters only the interval, through the predictive variance.
```

The most poorly identified parameter in the problem is also the only one that does not matter for the number,
and the only one that matters for the honesty of the number. **This is why the cold-start deliverable is a
width** (`02-e` §1, §4.3).

**Predictive variance, and the three objects that must not be conflated:**

| Object | Symbol | Variance | What it answers |
|---|---|---|---|
| the event's mean log ratio | `θ_j` | `τ² + V(τ)` | "what will this event trade at on average", **the cold-start headline** |
| one ticket's realised ratio | `y_ij` | `τ² + V(τ) + σ²` | "what will this ticket fetch" |
| the population mean | `μ` | `V(τ)` | "what is the average of the population", **a parameter interval, not a prediction** |

Confusing the first with the second understates an individual ticket's spread by the whole within-event
dispersion; confusing the third with the first understates it by `τ²`. That second confusion is the specific
failure mode of reporting a truncated `τ̂²` (§8.2).

**The handover count, a one-line derivation with real product consequences.** With `s_j² = σ²/n_j`,
`B_j = τ²/(τ² + σ²/n_j)` equals `1/2` exactly when

```
n* = σ²/τ²                                                              (EB-3)
```

the count at which the event's own mean and the population mean carry equal weight. Verified numerically at
`τ/σ ∈ {0.25, 0.5, 1}` giving `n* ∈ {16, 4, 1}` with `B = 0.5` exactly (`02-e` §4.6, arithmetic only). It is
what lets the interface say "your own data takes over after about `n*` resales" and come off the cold-start
label at a **stated count rather than a vibe**. And `n*` **diverges as `τ → 0`**, which is not a defect but
the same pathology as the truncation below: if the between-event variance really were zero, the event's own
sales could never add anything. **So the declared floor `τ₀` is load-bearing twice**: it keeps a truncated
moment estimate from producing false precision, and it is what makes the handover count finite.

**Assumptions, in the derivation.**

- *A1 Exchangeability of events given covariates.* **Declared, never testable, and it does all the work.** If
  the partition is wrong, every shrinkage is wrong. The recommendation is `event category × venue-size band ×
  organiser`, because those are the axes on which the primary price and demand level differ most. The
  arithmetic consequence is brutal: **every stratification divides the number of groups, and `τ` is estimated
  from the number of groups, not the number of sales.**
- *A2 Enough groups, with a defensible prior on `τ`.* With one group, `τ²` is not identified at all and the
  estimator **is** the prior. The elementary reason the prior is not decoration: a uniform prior on `τ²`
  implies a prior on `τ` proportional to `τ`, which increases in `τ`, which pushes `τ` up, which
  **under-shrinks every thin cell**: it tells you each cell is more informative than it is. And `τ̂²` is
  itself estimated with roughly `J − 1` degrees of freedom, so the cold-start interval is an estimate with its
  own wide interval and that second-order uncertainty must be propagated or the band will be too narrow.
- *A3 A censored within-group likelihood.* If the cap truncates, pooling uncensored sample means pools
  quantities whose bias depends on each event's cap, and the cap is an **event-level** covariate, so the bias
  enters at the same level as the parameter being pooled. That is the specific way this model goes wrong here,
  and it is invisible: the shrinkage looks well-behaved and the pooled mean is quietly a function of policy.
  **So the within-group likelihood is F3's, not a plain normal.**
- *A4 Conditional independence within a group given its parameter.* Holds for sales given a ticket's latent
  value; fails if there are unmodelled price dynamics, which is why F6 exists.

**Parameters.**

| Symbol | Interpretation | Units | Estimated by |
|---|---|---|---|
| `μ` | population mean log price ratio | log units | the pooled fit; **the cold-start point estimate** |
| `τ²` | between-event variance | log² | §8.2; **declared** below about five events, never a point |
| `τ` | between-event standard deviation | log units | the parameter the prior goes on (half-Cauchy / half-t, per A2) |
| `σ²` | within-event variance | log² | the event's own across-ticket dispersion |
| `β` | covariate effects | log units | only once `J ≥ k+3` |
| `τ₀` | declared floor on `τ` | log units | **declared from outside the data**; see the borrow in §8.3 |

**Data.** Per-event mean log ratio and its standard error, i.e. `sale` rows grouped by event. At `J = 0`:
nothing, and the prior. **No missing field**, but a **volume requirement the contract cannot create**: a
stratum with two events cannot estimate `τ`.

**Identification.** T1′: **not identified**; this is the prior predictive. It is the honest thing a
cold-start event can be given, a predictive distribution centred on a pooled mean whose width includes the
between-event variance, and it buys **nothing about identification**. With one group it degenerates to the
prior.

**Evidence class.** **C** throughout, the shrinkage algebra is exact. The **exchangeability of events is
`D`** and is the assumption, not a finding. `UNVALIDATED` for the transfer.

**D2 cost.** **Honest, and closed form except for one grid.** (i) Empirical-Bayes closed form (EB-2) is a
dozen lines, no iteration, no library, build this first. (ii) The grid posterior is a 601-point loop, no
matrix. (iii) Conjugate Gibbs for the normal hierarchy is about eighty lines and runs a few thousand
iterations in seconds at this scale, fine. (iv) **Anything non-conjugate**: a censored likelihood or a
hazard with random effects, needs hand-coded quadrature or a random-walk Metropolis with convergence
diagnostics: feasible, **implementable-not-recommended until the EB version has been compared against it**.
Full posterior sampling with HMC/NUTS (Stan, PyMC) is **specified-not-implemented** under D2.
`statistics.NormalDist` + `math.erf` supply everything the code in `02-e` §4.8 uses.

**Wrong when.**

- *The cold-start point estimate is reported as "what this ticket is worth".* It is a pooled mean **for resold
  tickets** in a *different market in 2004* (§8.3), and it is a mean log ratio, not a price.
- *The band is reported as the point.* The point is the pooled mean; the **interval is the deliverable**. And
  a band narrower than the borrowed-upper-bound row of §8.3's table asserts a precision the literature does
  not support.
- *A truncated-at-zero moment estimate is used in a predictive interval.* This is the one that survives review
  by accident: the point estimate is the pooled mean either way, so **nothing visible moves**, while the
  predictive variance loses its `τ²` term and collapses to `V(0)`, the band then claims a new event's mean is
  known to within the sampling spread of the old events' arithmetic mean, and **shrinks without limit as
  tickets accumulate**. **Rule: never use a truncated `τ̂²` in a predictive interval; substitute `τ₀` and
  print the sensitivity table.**
- *`J = 1` is treated like `J ≥ 2`.* The moment estimator's denominator is exactly `0.0` there, checked
  arithmetically, and this is undefined **by construction, not numerically**. Do not estimate `τ²`; the
  single event gives one draw of `θ`, which is not information about a *different* event. What it does buy is
  `σ²` and, if it has several tiers with sales, a within-event slope on log face. Worth having; worth nothing
  about the level.
- *The band is used to choose face.* Because the band is denominated in the units of face, moving face moves
  the band proportionally, and "set face to the middle of the band" is **circular**: the same scale freedom
  F11 exploits for the cap. **The cold-start output prices the resale ask, not the ticket.** Only the demand
  side can set the primary price, and before any resale the only demand observation is primary sell-through
  (F10), which gives a sign and not a level (`02-e` §6.3).

---

### 8.2 F17a · What constrains `τ²` when `J` is small

**Serves.** P7's width. Four options, in ascending order of honesty. **None of them estimates `τ²` when `J`
is small; they constrain it, and the difference must be said out loud.**

**(i) Method of moments (DerSimonian–Laird).** With `w_j = 1/s_j²`:

```
Q = Σ_j w_j (y_j − ȳ_w)²,     τ̂² = max( 0, (Q − (J−1)) / ( Σ_j w_j − Σ_j w_j²/Σ_j w_j ) )     (DL)
```

With known `s_j²` this is unbiased at the true `τ²`; with estimated `s_j²` it is biased and the weights are
noisy. **One degree of freedom, one number, no interval.**

**(ii) An upper confidence limit from `Q`**: the only **conservative** object available. Because `Q` is
approximately `χ²_{J−1}` under `τ² = 0`, solving `Q(τ²) = χ²_{J−1;0.975}` for `τ²` gives an upper limit. This
is the right thing in a cold-start band: **too narrow a band is a false claim while too wide a band is merely
uninformative, and the loss is asymmetric.**

**How badly `τ²` is pinned**: computed from `χ²` quantiles (incomplete gamma by series and continued fraction,
quantile by bisection, 2.5%/97.5%, 1e-12 convergence; `02-e` §4.4, class C):

| `J` events | 95% interval on `τ²`, as a multiple of the `Q` point estimate | span |
|---|---|---|
| 2 | 0.001× to 5.02× | 5100× |
| 3 | 0.025× to 3.69× | 146× |
| 4 | 0.072× to 3.12× | 43× |
| 5 | 0.121× to 2.79× | 23.0× |
| 8 | 0.24× to 2.29× | 9.5× |
| 10 | 0.30× to 2.11× | 7.0× |
| 15 | 0.40× to 1.87× | 4.6× |
| 20 | 0.47× to 1.73× | 3.7× |

**At five events the between-event *variance* is known to within a factor of 23, so the *standard deviation*
to within about 4.8.** Any single number quoted for it at `J = 5` is decoration. Below 20 events there is no
rung of this table at which a point estimate of `τ²` deserves to be reported without the table.

**(iii) A grid posterior with a declared prior**: the recommended route. With `μ` integrated out under a flat
prior:

```
p(y | τ) ∝ ( Π_j (s_j² + τ²)^{-1/2} ) ( Σ_j (s_j² + τ²)^{-1} )^{-1/2} exp( −Q(τ)/2 )      (MARG)
```

so a 601-point grid over `τ ∈ (0, τ_max]` times a half-normal or half-Cauchy prior gives the posterior of
`τ`, and the mixture over the grid gives the predictive for `θ_new` by the law of total variance. It never
produces a negative or zero variance; it degrades gracefully to the prior at `J = 1`, and it costs a 601-point
loop. **What it does at `J ≤ 2` must be stated, not hidden: the output is the prior**: the posterior over
`τ` equals the prior up to the likelihood of a single draw, and printing that as a "credible interval"
without saying whose prior produced it is the exact failure this section exists to prevent.

**(iv) A declared floor `τ₀`**: a minimum below which the estimate is not allowed to fall, chosen from
outside the data, reported alongside the sensitivity grid. **It is what protects against the pathology in
§8.1.**

**Cross-check rule.** Report (iii) as the band, (i) and (ii) as printed cross-checks with their `J`, and (iv)
as the declared floor. **If (ii)'s upper limit is much wider than (iii)'s interval, or (i) is at the floor
while (ii) is not, say so on the surface rather than picking one.**

**Parameters.** `J`, `Q`, `τ₀`, and the prior family and scale. All but `J` and `Q` are declared.

**D2 cost.** (i) is three lines. (ii) needs `χ²` quantiles: a regularised incomplete gamma by series and
continued fraction plus a bisection, about 40 lines (`02-e` §4.4, §4.8). (iii) is the loop. **All honest.**

**Wrong when.** Any of these is reported as an estimate of `τ²` at `J ≤ 2`, or when the cross-checks disagree
and one is silently preferred.

---

### 8.3 F17b · The population spread that is not invented

At `J = 0` even the prior needs a location and a scale, and inventing them is forbidden. The one legitimate
route: **fit the published markup distribution, cite it, and carry the transfer as a labelled liability.**

Leslie & Sorensen's concert sample reports (**class A for that market**): arithmetic-mean markup 41% above
face, 26% of resold tickets below face, 25% above +67%. Fit `log(p/f) ~ N(m, s²)` and check the third:

| Reading of "averages 41% above face" | fitted `m` | fitted `s` | implied `P(markup > +67%)` | published |
|---|---|---|---|---|
| arithmetic mean | 0.2612 | 0.4060 | 0.268 | 0.25 |
| median | 0.3436 | 0.5341 | 0.376 | 0.25 |

The arithmetic-mean reading reproduces the third published fact and the median reading does not, so **the
arithmetic reading is the one to carry**: mean log ratio 0.2612 (geometric-mean markup +29.8%), across-ticket
dispersion 0.406, implied `P(above face) = 0.740` against the published 0.74. **This is a consistency check,
not a calibration**: it says the three quoted numbers can come from one lognormal, nothing more (`02-e` §4.7,
computed, class C).

Carried to this platform, with the liabilities stated:
- **Location** `μ ≈ 0.26` is a *borrowed* prior for resold tickets on eBay/StubHub in 2004 for 56 rock
  concerts. **Class B** for the mechanism, **D** for the transfer.
- **Selection direction is known.** The prior is conditional on resale and resold tickets are the better seats,
  so it is biased **up** for a randomly chosen ticket. *The direction is known, which is worth more than the
  size.*
- **The scale gives an upper bound for `τ`, not a value.** Since across-ticket dispersion decomposes as
  `τ² + σ²_within` and `τ` cannot exceed the total, `τ ≤ 0.406` **on the assumption that our platform's
  across-ticket dispersion is no wider than theirs**. Untestable at `J = 0`; printed as a condition. The
  literature gives the **top** of `τ`'s range and **no bottom**, which is why the sensitivity grid runs from
  near zero upward.

**The sensitivity table, which is what the cold-start band actually is** (class C; a 90% band on
`θ_new` is `ȳ ± 1.6449√(τ² + V(τ))` with `V(τ) = 1/Σ(s_j²+τ²)^{-1}`). Since `V(τ) > 0` always, every row is a
**floor** on the width for a given `τ` and never an overstatement. The last column is centred on the borrowed
point estimate `μ = 0.2612`, so it reads as an absolute markup band. **The table in `02-e` §4.7 gives the
multiplier around the point estimate and labels it "as markup around face"; that label is wrong and the
`00-verification-round1.md` §11 correction is applied here.** Read literally, `02-e`'s "−49% to +95%" would
say a new event's markup can be 49% below face, which contradicts its own class-A inputs (26% of resold
tickets below face, mean +41%).

| declared `τ` | 90% band on the event mean, log units | multiplier on the point estimate | **absolute markup band** |
|---|---|---|---|
| 0.10 | ±0.164 | ×1.102 to ×1.531 | **+10% to +53%** |
| 0.20 | ±0.329 | ×0.934 to ×1.804 | **−7% to +80%** |
| 0.30 | ±0.493 | ×0.793 to ×2.127 | **−21% to +113%** |
| 0.406 (borrowed upper bound) | ±0.668 | ×0.666 to ×2.532 | **−33% to +153%** |

Recomputed in this pass from `μ = 0.2612` as `exp(μ ± 1.6449τ)`. The verification round's `−33%` lower end
agrees with this; its `+155%` upper end disagrees and is a rounding slip on the same formula. `+153%` is what
the formula returns.

Read the last row as the answer to "how much uncertainty must be attached": even with the most information
the literature can supply, a brand-new event's geometric-mean resale markup is pinned only to roughly **a
third below face to one and a half times face**, and that is the optimistic end. **An engine showing a
narrower band than the last row is asserting a precision the literature does not support.**

**Wrong when** the location is transferred without the selection caveat; when `τ ≤ 0.406` is read as a
measurement rather than a conditional upper bound; or when the band is quoted without the word "prior".

---

### 8.4 F18 · Gamma–Poisson exposure update (cold start for the *intensity*)

**Serves.** P7 for the **sale intensity**, as distinct from the price level. This is the reconciliation of C4:
**price level uses F17's population mean; sale intensity uses the mean updated by the observed zero.**

**Mathematics.** Prior `λ ~ Gamma(a, b)`; exposure `E` ticket-days; `D` events observed.

```
posterior  λ | D, E  ~  Gamma(a + D, b + E)
posterior mean       =  (a + D)/(b + E)          NOT the prior mean a/b          (GP-1)
predictive           =  Negative-Binomial (over-dispersion from the gamma)
```

**Assumptions, in the derivation.** (i) `λ` is constant over the exposure window, the piecewise-constant grid
of F7 supplies the cells. (ii) The gamma prior is the conjugate choice, and conjugacy is a convenience, not a
finding. (iii) `E` is measured on the same clock as everything else, `slot`-derived, per F7's A3.

**Parameters.** `a`, `b` (declared prior, two parameters), `E` (computed), `D` (observed).

**Data.** Ticket-days at risk per event, and the sale count. Both present. **At `E = 0` the answer is the
prior, which is the honest statement.**

**Identification.** Serves P3/P7: the posterior intensity and its predictive count distribution. **Not the
price level**: this is the `02-c` §6 answer and it is a different object from F17's.

**Evidence class.** **C** for the conjugate algebra. **D** for the prior's scale.

**D2 cost.** Closed form: two additions and a division. The negative-binomial predictive needs a product
series. Trivial.

**Wrong when.** An event with zero sales and substantial exposure is treated as missing data, **the zero is
evidence and must update the estimate** (`02-c` §1.8). Also wrong when events with zero sales are **excluded**
from the between-event variance estimate: that biases the variance **down** and makes the cold-start interval
come out **too narrow**: the same failure mode as the truncated moment estimate in §8.1, reached by a
different route.

---

## 9. Relationships between the formulations

### 9.1 The composition graph, in text

```
                          ┌──────────────────────────────────────────────┐
   THE OBSERVATION SET    │ lib/types.ts: LedgerEntry[], Ticket, Event   │
   (00-data-situation)    │ + ResaleStats / EventAnalytics aggregates    │
                          └───────────────┬──────────────────────────────┘
                                          │
        ┌─────────────────────────────────┼──────────────────────────────┐
        ▼                                 ▼                              ▼
  ┌───────────┐                    ┌─────────────┐                ┌─────────────┐
  │ F2 repeat │                    │ F3 CENSORED │                │ F7 composite│
  │  sales    │◄── cross-check ───►│   HEDONIC   │                │  intensity  │
  │ (ratios)  │   (disagreement    │ (+F5 path)  │                │ (+cure, CR) │
  └─────┬─────┘    is diagnostic)  └──┬───────┬──┘                └──┬───────┬──┘
        │                             │       │                      │       │
        │ ratios                      │ ŷ, s(τ)│ residual σ          │ rate  │ ξ
        │                             │       ▼                      │       ▼
        │                             │   ┌────────┐                 │  ┌─────────┐
        │                             │   │F16 band│                 │  │ F8 ξ    │
        │                             │   │(P6)    │                 │  │(display)│
        │                             ▼   └────────┘                 │  └─────────┘
        │                       ┌──────────────┐                     │
        └──────────────────────►│ F17 EB band  │◄──── frailty ───────┘
             (level for a       │ (P7, T1′)    │      (same object,
              cold event)       └──────┬───────┘       built once)
                                        │ θ̂_new, τ²
                                        ▼
                                  ┌──────────┐
                                  │ value    │
                                  │ signal   │
                                  └────┬─────┘
                                       │ (certainty equivalence, declared)
                                       ▼
  ┌─────────────┐   ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
  │ F10 primary │   │ F11 (OBJ)   │   │ F12 (RN)     │   │ F13 (CVAR)   │
  │ sell-through│──►│ (WEDGE)     │──►│ grid +       │──►│ risk-adjusted│
  │  bracket    │ε  │ (FOC-2)     │   │ boundary     │   │ member of set│
  │ (P4, T4b)   │   │ c**, fee    │   │ rule / SET   │   └──────────────┘
  └─────────────┘   └──────┬──────┘   └──────┬───────┘
        ▲                  │                 │
        │                  │ config: φ,f,β,b,a,u,q_min,ρ  (D4: supplied, never assumed)
        │                  ▼                 ▼
        │            ┌──────────┐      ┌───────────┐
        │            │F14 (MDP) │◄─────│ F14 needs │
        │            │reserve   │      │ Gap 5 +   │
        │            │price set │      │delistReason│
        │            └──────────┘      └───────────┘
        │
        └── the ONLY level-bearing demand input. Everything on the resale side is a RATIO.

  F4 cap truncation feeds: a floor on F3's value (+FOC-2's ceiling), the regime variable for F7,
  the sign test for F5, and the "refuse to report a central statistic" guard for all of P1/P2.
  F15 prequential scoring + F1 martingale benchmark sit OUTSIDE the graph and score every arrow.
```

### 9.2 Which formulations **share parameters**

Sharing is the reason the architecture should have one component per shared object, not one per subproblem.

| Shared object | Formulations that consume it | Consequence |
|---|---|---|
| `τ²`, the between-event variance | **F3** (event effects, as a prior), **F7** (event-level frailty), **F17** (the cold-start band), **F18** (prior scale) | **the same object; build the shrinkage layer once.** `01-c` §7.5 and §3.5 make this explicit: F7's frailty and F17's pooling are one thing |
| `σ²` (within-event dispersion of log ratio) | **F3** (residual), **F17** (`s_j² = σ²/n_j`), **F6** (`r`), and `n* = σ²/τ²` | `n*` is a **ratio of two shared parameters**, so the handover count moves with both |
| `ε` / `q(P)` | **F10** (produced), **F11** (`c**`'s partner in FOC-2), **F12** (the grid), **F13** (the scenario set), **F14** (the state's transition) | one unknown drives five formulations. Reporting `∂p*/∂η` once serves all |
| `p₀` (the primary price / face) | **F11**, **F12**, **F14** as decision; **F3**, **F5**, **F17** as **denominator** | **the coupling that makes the ratio models unable to set the price** (§9.4) |
| `u` (use value / empty-seat cost) | **F11** (`c**`), **F12** (degeneracy and boundary), **F14** (`V(T,n) = n·u`, and `u` controls the *shape* of the path) | one unmeasured scalar decides the endgame, the interior optimum and the path's curvature. That is a lot of weight on a `config` value, and the report says so |
| `cap_bps` → `c` | **F3** (`c_event`), **F4** (the bound), **F5** (attenuation), **F7** (regime), **F11** (`p₀(1+c)`), **F12** (cap-binding duration), **F17** (truncated prior) | observed, not estimated, and it moves **with the decision**: the single most consequential fact in P5 |
| the clock (`slot`) | **everything with a duration**: F2, F5, F6, F7, F9, F18 | one rule, `slot` not `occurredAt`, stated once and enforced everywhere |

### 9.3 Which formulations **compete for the same target**

Recorded, not resolved silently. Each pair is a live design choice.

| Target | Competing formulations | Where the conflict is recorded | What I would use, and why |
|---|---|---|---|
| **T2 curvature** | **F5** (within-event `θ̂`, one parameter, robust, thin) vs **F3**'s `s(τ)` spline (pooled, richer, rests on normality + selection) | **C1** | **F5 for the per-event path**, F3's spline only pooled and with curvature beyond knot support reported as unsupported. `02-a` §8.9's objection is decisive at the event level: a spline on a handful of points is unidentifiable curvature by another name. |
| **T1 level** | **F3** (affine normalisation, no anchor) vs **F10** (a censored anchor from sell-through) | **C2**, adversarial review error 5 | **Both, and this is genuinely unresolved.** My position: the level is **bounded**, not identified, and "contains no exogenous anchor" is too strong, but the anchor is censored, so it buys a bracket and not a point. Do not print a level either way. |
| **P7 price level** | **F17** (population mean, `τ²`) vs **F18** (gamma–Poisson, exposure) | **C4** | **Different objects, so no real competition**: price level uses F17, sale intensity uses F18. This is the one conflict with a clean resolution and it is adopted. |
| **P1 "the" estimate** | **F3** (rich, one number per ticket) vs **F2** (thin, one index) | `01-c` §4.5, `02-a` §4.3 | **Run both.** Different identifying variation, no distributional assumption for F2. **Where they disagree is the diagnostic for composition bias**: a disagreement report, not a winner. |
| **P6 intervals** | **F16** (empirical quantiles, exact but conditional) vs F15 (proper score, calibrated but only for the sale indicator) vs conformal (rejected) | `01-c` §8 | **Both, scoped**: F15 for the sale indicator, F16 for any price interval, and nothing claims coverage. |
| **P5 risk** | **F13 mean-CVaR** vs mean-variance (rejected) | `02-d` §4.3 | **CVaR**: coherent, penalises the downside the business carries, and does not need re-tuning per event size. |

### 9.4 The one relationship that decides the architecture

**F3, F5 and F17 are all expressed in units of `faceValueLamports`, and `faceValueLamports` is the primary
decision variable.** Three consequences, and together they are the load-bearing logic of the whole record:

1. **The resale record identifies a ratio distribution that is invariant to `p₀`.** Raise the primary price by
   `λ` and, under a proportional cap, the ceiling rises by `λ` in the same proportion (F11 §6.2(a)); the band
   translates and the seller's problem collapses to *where to sit in the willingness-to-pay distribution*
   (`01-b` §4.5(ii), `02-d` §2.5(a)). **So the band tells the engine nothing about the level of `p₀`.**
2. **Therefore a markup-space model cannot be evaluated at a different `p₀`.** A model whose output is
   `log(p/p₀)` cannot answer "what if `p₀` were different", because changing `p₀` changes its own denominator.
   The curvature can be *estimated* in either normalisation (they differ by an event-tier constant and `θ̂` is
   identical), but the **level must be converted to money**, `p = face · e^y`, and the cap re-applied at
   `p₀(1+c)` for each candidate primary price (`02-a` §7.2, §8.1). Leaving a forecast in markup space when the
   decision changes face value is the error, and it is silent. [C]
3. **So the primary price cannot come from the resale model at all.** The only level-bearing demand object is
   **F10** (primary sell-through), and it is censored and one-sided. This is **C3**: adversarial review
   error 4, and it is the correction that keeps the whole Phase 5 chain honest: **T5's demand input is
   T4b (primary), not T3 (secondary).**

The corollary is the sentence the deliverable must carry: **the resale engine prices the resale ask; the
primary decision needs a primary demand object, and before any resale the only one in the schema gives a sign
and not a level.** The cap-binding **duration** is then an output of the pricing decision rather than a
property of the event, raising `p₀` raises the ceiling in money and shortens the window over which the cap
binds, and it is cheap: one root-find per candidate price against the fitted path (`02-a` §7.2).

---

## 10. Computational requirements under D2 (pure Python standard library)

D2 is a hard constraint, verified on this machine: no pip, no ensurepip, no numpy/scipy/pandas/sklearn/
statsmodels, `venv` exists but cannot install (`00-data-situation.md` §1; D2's evidence). It must therefore be
established, formulation by formulation, **whether the linear algebra is honest at the dimension it actually
has**: not whether it is possible.

### 10.1 The rule, stated once

| Situation | Honest? | Why |
|---|---|---|
| `n × n` dense solve, **`n` small and fixed** (`n ≲ 30`) | **YES** | hand-written Gaussian elimination with partial pivoting is ~30 lines; `O(n³)` ≈ 2.7×10⁴ flops is nothing; the code is auditable and the pivot log is a diagnostic you can print |
| `n × n` solve after **exact absorption** of a large dummy block (within-group demeaning), leaving `n_small ≲ 30` | **YES** | the absorption is an algebraic identity, not an approximation; this is the standard fixed-effects trick and it is what makes F3 honest |
| `n × n` dense solve with **`n` growing with the data** (`n ≳ 100`) | **NO** | the flops are survivable (`n = 200` → 8×10⁶) but **the condition number is the real problem, not the flops**, and a hand-written solve gives you a plausible wrong answer rather than an error. Restructure (absorb, aggregate, or impose a parametric form) or mark specified-not-implemented |
| **normal equations** vs **QR** at the same `n` | QR preferred whenever `κ` is questionable | normal equations **square** the condition number. At `n ≤ 30` and well-scaled regressors either is fine; this is the one place where the 30-line QR (Householder or Givens) earns its keep |
| anything needing **general eigen-decomposition, SVD, LP/QP, more-than-1-D numerical integration, or automatic differentiation** | **NO** unless hand-coded for one specific small case | D2 has none of it. Gauss–Hermite nodes *can* be generated from a short symmetric-tridiagonal eigen-decomposition, which is the one exception, and it is why non-conjugate quadrature is "feasible, not recommended" |
| a **grid, a sort, or a 1-D bisection** where a solver would otherwise be needed | **YES**, and it replaces the solver | exact to resolution, and the honest thing to say is that the resolution is the only cost |

**And the honest label for all of it: implementable is not implemented.** As of this writing **no estimator
code exists** in `ticketpath/`. The seam is `ticketpath/adapters/pricing_model_adapter.py`, which registers
nothing and returns `available: false` with reason `no_model_registered`, and that refusal is correct rather
than provisional. Every "honest" in the table below means *the mathematics admits a stdlib implementation of
auditable size*; none of it is running.

### 10.2 Per formulation

| # | Formulation | Params | Matrix work | `n` and character | Under D2 |
|---|---|---|---|---|---|
| **F1** | Martingale anchor | 0 | none |, | **implementable**, 1 line |
| **F2** | Repeat-sales index | `T` time cells, minus 1 normalisation | normal equations in `T` | `T` = monthly cells over ~1 yr → `T ≈ 12`, **small and fixed → honest**. Per-day/per-week cells over years → `T ≳ 100`, **not honest** (sparse, ill-conditioned) → restructure to a one-parameter index | **implementable** for `T ≲ 30`; **specified-not-implemented** for fine cells |
| **F3** | Censored hedonic, EM | `tier + knots + k` after absorption; + `σ` | **`p_small × p_small` least squares per EM iteration, with event dummies absorbed by demeaning** | `p_small ≈ 15–25`, **small and fixed → honest**. **Without absorption** the design is `J + tier + knots + k`; at `J = 60` events that is 80×80 → **not a hand-written solve anyone should trust**. The absorption is the whole reason this is honest | **implementable**: the programme's best fit to D2. ~120 lines; `statistics.NormalDist` for `φ`, `Φ` |
| **F4** | Cap bound / crossing | 0 | none |, | **implementable**: count, sort, one comparison |
| **F5** | Deadline-convex path | **1** (`θ`), `+1` nuisance per event | **2×2 closed form**, then a weighted mean | `n = 2`, fixed → **trivially honest** | **implementable**, ~60 lines |
| **F6** | Local-level state space | 2 (`q`, `r`) | **none, scalar filter** | the state is 1-D, so every "matrix" is a scalar | **implementable**, ~30 lines |
| **F7** | Composite intensity, CR, cure | `k = buckets + covariates ≈ 15–30`, + `π` | `k × k` information, Newton | **fixed in `k`, not in rows** (aggregated cells) → `k ≲ 40` **honest**; `k > 40` → reduce the design or mark it | **implementable** (Newton on the Poisson form). Fine–Gray: **implementable with care** (IPCW weights, validate on a SIM competing-risks dataset first) |
| **F8** | `ξ(p,τ)` | 0 | none |, | **implementable**: a dictionary and a divisor |
| **F9** | Listing-episode hazard | `M` bins + 4 + `p` | `k × k` Newton, same solver as F7 |, | **implementable, data-gated**: the same code as F7 on new rows. Blocked on data, not on computation |
| **F10** | Tobit sell-through bracket | 4 | 4×4 information, Newton or EM | `n = 4`, fixed → **honest** | **implementable**, ~60 lines |
| **F11** | (OBJ), (WEDGE), (FOC-2) | 2 assumptions, rest config | none |, | **implementable**: algebra and a grid |
| **F12** | (RN) grid + boundary | `c**`, `ε`, `u`, `q_min` | **none** | `O(G·M)` | **implementable**: 41 × 10⁴ evaluations, seconds |
| **F13** | Mean-CVaR | `λ`, `α` | **none** | a sort | **implementable** by sort. **Rockafellar–Uryasev LP: specified-not-implemented** (no LP solver), and unnecessary at one dimension. VaR optimisation and Wasserstein-robust multi-tier CVaR: **specified-not-implemented** |
| **F14** | Reserve-price MDP | per state | **none** | 216 states × 41 prices ≈ 9×10³ per stage | discrete-time **implementable**; continuous HJB **specified-not-implemented** (and the DP is its numerical solution, so the distinction is cosmetic) |
| **F15** | Prequential scoring | 0 | none |, | **implementable** |
| **F16** | Empirical quantile band | 0 | none | a sort | **implementable**. Exact quantile regression: **specified-not-implemented** (LP); IRLS is an **approximation** and must be labelled one |
| **F17** | EB pooling / cold-start band | `μ`, `τ²` (+`τ₀`) | **none** | 601-point grid, no matrix | **implementable** (closed form + grid). Conjugate Gibbs: implementable. Non-conjugate: feasible-not-recommended. **HMC/NUTS: specified-not-implemented** |
| **F17a** | `τ²` constraints | 0 | none | `χ²` quantiles via incomplete gamma + bisection | **implementable**, ~40 lines |
| **F18** | Gamma–Poisson exposure | 2 (`a`, `b`) | none | closed form | **implementable**, 5 lines |

### 10.3 The explicit answer to "where does an `n × n` normal-equation solve stop being honest"

- **Honest:** `n ≤ 30`, fixed by the specification and not by the data (F3's `p_small`, F5's 2, F7's `k`,
  F10's 4), and, where a large dummy block exists, **only after exact absorption**. Also honest: any `n`
  when the matrix is diagonal or triangular, which is what the piecewise-exponential information matrix is
  before covariates are added.
- **Dishonest:** `n` that grows with events (`J` event dummies unabsorbed), with time cells (per-day F2), or
  with listings. The failure is not speed; it is that a hand-written solve at `n = 100` with a condition
  number of 10⁶ returns a number and no warning.
- **The repair, in order of preference:** (1) absorb the block exactly by demeaning (F3); (2) aggregate cells
  before fitting so the parameter count is fixed (F7); (3) impose a parametric form on the offending block
  (F2's single index slope); (4) mark specified-not-implemented. Option (4) is honest and is what D2 asks
  for; it is never "vendor a library", which D2 rejected on the repo-is-code-only rule.

---

## 11. Known limitations, per formulation, in the form "this is wrong when …"

Collected so they can be pasted into a report. Each is a condition, not a disclaimer.

| # | Wrong when |
|---|---|
| **F1** | …the true path has a predictable component (which is the very hypothesis it is the null for), **or** the last observation is stale and the staleness is correlated with value, **or** it is scored against a path model on the same few events, where sampling luck beats it. |
| **F2** | …the pairs differ from the population in their price **change**, not merely their level (short-hold selection), **or** the index is read as a level (its additive constant is arbitrary), **or** time cells are so fine that the design is sparse and ill-conditioned. |
| **F3** | …the level is read as money (the normalisation is arbitrary); …the censoring regime is wrong for Q3 (invents a mass point, or discards it); …the cap-hit share approaches 1 and `σ` is identified off almost nothing; …seat quality varies within tier and correlates with `τ`, so the path absorbs a mix effect; …a tier coefficient is used as a willingness-to-pay derivative; …`α_tier` is read as a seat price when it is a tier price. |
| **F4** | …the cap does not bind (then it is evidence of nothing); …leakage is large and correlated with demand, so the bound is weakest where value is highest; …a central-tendency statistic is reported above 50% cap mass; …a lower-quantile identity is used **conditionally** without the pointwise bound condition; …the bound is read as an estimate. |
| **F5** | …`ω = 1` is used and calendar drift is real; …a spline replaces the one-parameter basis on a handful of points per event; …`n_e < 4` or spread `< 5` days and the event is not discarded; …more than half of trades sit at the cap; …the magnitude is transferred from the failure-branch literature (opposite conditioning); …the `s_e²`-known approximation is forgotten and the interval is presented as exact. |
| **F6** | …`q/r` is small and the price really moves (a stale level is reported as current); …`q/r` is large and the interpolation is noise; …a ticket has two observations and `q` is "estimated"; …a level is expected from it. |
| **F7** | …it is called a sale hazard (it is a composite rate); …it is extrapolated past the `τ` support, or read from a zero-sale bucket without stating the regularisation; …`π̂` is read as never-**offered**; …first passage and the recurrent process are mixed on one chart; …`issuedCount` enters as a predictor (look-ahead, no capture time); …redemption's effect on the sale hazard is asserted with a sign. |
| **F8** | …it is called a demand curve; …an elasticity is regressed off it; …bins are pooled across tiers in markup space under a binding cap; …it is used to answer "what if we listed at X". |
| **F9** | …A2 fails and `γ̂` is called a demand curve; …ask dispersion is absent and the honest output is not printed; …the cap stratum is pooled with the interior; …`occurredAt` is the clock; …the collinearity diagnostics are not published before `γ̂`; …it is used to identify the **primary** demand response. |
| **F10** | …`issuedCount` means minted, not sold; …the organiser revises price mid-sale within a tier; …face value is discounted, so `p₀` is not the transacted price; …`n` tier-events is small and only the coefficient is reported; …it is treated as a demand elasticity **under a resale cap**, which no study estimates. |
| **F11** | …`u` and `a` are dropped (no interior optimum); …the elasticity is inverted to produce a price rather than to interpret one; …the `1/(η−1)²` sensitivity near `η = 1` is read as reassurance; …`ρ` is read as a capturable share of resale margin; …a percentage-only fee is assumed to be the fee structure (the per-unit term is what moves the answer). |
| **F12** | …a point optimum is reported; …`ε` is hard-coded from the literature; …`ε_D` is used for `ε_own` (understates the price); …multi-tier is claimed beyond the measured 5%/3.4%; …dynamic pricing is claimed as available (no reprice endpoint, no state variable). |
| **F13** | …`λ` and `α` are hidden; …mean-variance is used instead (penalises upside, unportable `γ`); …the sign of the risk correction is asserted rather than derived (it depends on the adverse-state elasticity). |
| **F14** | …the terminal value is set to `0` instead of `n·u`, `u > 0`; …certainty equivalence is used undeclared; …one surface is reported instead of a set over the demand-parameter box; …`γ` is set to anything other than ≈1 within one event's horizon. |
| **F15** | …it is applied to a **price** distribution. Then every scored observation is conditioned on having sold, which is the dependence being measured. Report the interval, label UNVALIDATED, quote no coverage number. |
| **F16** | …it is presented as a forecast interval for an arbitrary ticket (it is conditional on trading, and traded tickets are better seats); …censored observations beyond the cap are included in the quantile; …a coverage statement is attached. |
| **F17** | …the pooled mean is called "what this ticket is worth" (it is a borrowed prior for resold tickets in a 2004 market); …the band is reported as the point; …a truncated-at-zero `τ̂²` enters a predictive interval (invisible in the number, fatal in the width, and the band shrinks without limit as tickets accumulate); …`J = 1` is treated like `J ≥ 2`; …the band is used to choose face (circular: it is denominated in face). |
| **F17a** | …any of the four constraints is reported as an estimate of `τ²` at `J ≤ 2`; …the cross-checks disagree and one is silently preferred. |
| **F18** | …a zero-sale event with real exposure is treated as missing (the zero is evidence); …zero-sale events are excluded from the variance estimate (biases `τ²` down, so the band is too narrow). |

---

## 12. Conflicts carried, not resolved · and which I would use

Numbers match `D-model-registry.md` §5 where the conflict is already filed there, so `F` can cite one name.
Two are added here because they are mathematical rather than registry-level.

| # | Conflict | Sides | What I would use, and why |
|---|---|---|---|
| **C1** | spline vs one-parameter basis in time-to-event | `01-c` §4.6 specifies `s(τ)` as a piecewise-linear spline with knots in the final fortnight; `02-a` §8.9 rejects a spline per event as "unidentifiable curvature by another name" | **Both, at different levels.** Per event: the one-parameter `log(1+d)` basis, because a spline on a handful of points is not identified. Pooled in F3: a spline is admissible, because there are many more sales, and curvature beyond the knot support must then be reported as unsupported. This is the registry's own resolution and I agree with it. |
| **C2** | whether the value level has an anchor | `01-b` §4.1 "only ratios are identified, the schema contains no exogenous anchor" vs `01-b` §4.4(i) and adversarial review error 5: the level is set-identified from primary sell-through | **Both, corrected**: the level is **bounded, not identified**. The sell-through bracket is a real anchor but it is **censored**, so it buys a bracket. `01-b`'s "none" is too strong; "identified" is too weak. **Print no level.** This is the most load-bearing unresolved item for P1. |
| **C3** | which input the primary optimum needs | `01-b` T5 "the optimum inherits the widths of T3 and T4" vs adversarial review error 4: the demand input is the **primary** sale process (T4b), not the secondary hazard (T3) | **The review's correction**, because it is later, more specific, and it follows from the scale-freedom argument in §9.4: a resale model in units of face cannot set face. **F12's demand input is F10, not F9.** This changes what a builder wires up. |
| **C4** | two cold-start answers | `02-e`: the point estimate is the population mean and the interval is the deliverable; `02-c` §6: a zero over exposure is evidence and the estimate must shrink with exposure | **Both, by object:** price level → F17; sale intensity → F18. This is `02-c` §6.2's own reconciliation and it is adopted. |
| **C6** | the cap's within-event variation | `01-b` §5.3's summary treats the cap as an instrument with "across tiers within an event" variation; `01-c` §1.4(1) corrects it. `00-verification-round1.md` C1 checks the contract and settles it: `resalePriceCapBps` is one field on **Event**, `TicketTier` has no cap, so the **field** does not vary across tiers and only the **level** it implies does, mechanically, as a multiple of each tier's face. Note `01-b` §4.4(ii) states only the correct absolute-level fact; it is the §5.3 summary that overstates, and `01-c` quotes it as §4.4(ii) | **`01-c`'s correction.** The instrument is **cross-event only** and therefore confounded with everything else that varies across events. The one-sided bounds survive (cross-event variation is real); **any claim of within-event instrument strength is withdrawn**, and F4's bounds are reported with that confound named. |
| **C7** | fee neutrality | D4: a per-unit fee and an ad-valorem fee give different optima; `02-d` §2.3: ad-valorem fees are **neutral**, only per-unit fees move it, and the stack collapses to `c**` | **`02-d`**, because it is exact algebra rather than an assumption. This *sharpens* D4 rather than overturning it, and the consequence for a settlement-field request is inverted: the **per-unit** component is the one worth recording. |
| **C9** | the price path's conditioning | `02-a` §4.4: the published decline is measured on **listings that failed and were relisted**; this ledger measures **transactions that cleared** | **Neither transfers.** `θ̂` is a locally estimated curvature, **never** Sweeting's exponent re-used. The published sweep is A-cited support for the **shape** only. This is the record's own "most consequential methodological point" and it constrains F5's evidence class permanently. |
| **C10** | `issuedCount` semantics | sold vs minted, unknown | **Treat F10 as gated** on the operator's answer. No formulation above depends on it except F10, and F10 is the level-bearing one, so this one unresolved word gates the primary-price claim. |
| **C11** *(new)* | the fitting loss vs the scoring loss | F3 fits by a Gaussian likelihood (least squares in the M-step); F5 is **scored** by MAE in log space (`02-a` §8.4) | **Both, deliberately.** This is not an inconsistency: the likelihood is the estimator, MAE is the **decision loss** (a percentage of a price), and they answer different questions. But it must be **stated**, because a Gaussian fit scored by MAE is an unusual combination and a reviewer will ask. The alternative, fitting by least absolute deviations, is not implementable exactly under D2 (it is an LP) and would be an approximation, which is worse. |
| **C12** *(new)* | the lower-quantile survival claim | `02-a` §6.2 says lower quantiles survive truncation "whenever the cap mass is below that quantile (Powell 1986)" | **Weaker than written, and stated precisely.** The identity of the observed and latent `q`-th quantile holds **unconditionally** when `P(cap) < q`. A **conditional** quantile needs the bound above the conditional quantile **pointwise**, which is stronger and untested. Powell (1986) is the reference for a censored **quantile regression estimator**, a stronger object than the identity invoked; citing it for the identity overstates the support. F4's table carries the precise condition. |
| **C13** *(new)* | the cold-start band's units | `02-e` §4.7 labels its last column "as markup around face" and its evidence table restates it as a band "from about −49% to +95%"; `00-verification-round1.md` §11 shows that column is the **multiplier around the point estimate**, and that the absolute band centred at `μ = 0.2612` is about −33% to +153% | **The verification round, and §8.3 is recomputed from the formula rather than copied.** A −49% lower end would say a new event's markup can be 49% below face, contradicting the same file's class-A inputs (26% of resold tickets below face, mean +41%). The verification round's own `+155%` upper end is a rounding slip on `exp(0.2612 + 0.6678) = 2.532`, so `+153%` is used. **This is the one place in this file where a number differs from the finding it came from, deliberately.** |

**Applied, not carried:** the nine adversarial-review errors that touch equations, error 4 (C3), 5 (C2),
6 (the affine-indeterminacy citation is about preferences and technology, not the price level, so the
normalisation claim is supported by the **estimator's construction** rather than by Ekeland–Heckman–Nesheim),
7 (Prentice 1986, not Lagakos, for a mark observed only on cases), 8 (no sign on redemption's censoring
effect), error 2 together with C8 (`π̂` is never-transacted, never never-offered), 13 (the identified set of an optimum is an
image, not a union of widths), 18 (the cap bias is a **ranking inversion**, not a level bias), and 36
(Burdett & Judd and Bulow & Klemperer are theory = class C). Errors 1, 3 and 12 are fixture-arithmetic and
transfer-quality problems, not mathematics; they are noted where they bear on F2 and F4 and are not repeated.

---

## 13. The single load-bearing formulation

**F3, the censored hedonic price locus.** It is the load-bearing formulation because it is the only one that
satisfies all five of the following, and no other formulation satisfies more than three:

1. **Its identifying assumption is exactly true, not approximately.** Quality is fixed at mint, so the
   within-unit price ratio is a pure price movement (F2's free lunch, inherited).
2. **It produces output for a ticket nobody has ever resold**: the engine's headline claim, and the one thing
   neither the repeat-sales index nor the hazard can give (`01-c` §4.6).
3. **It carries `τ`, so it subsumes the price path** rather than sitting beside a separate forecaster (§3.3).
   One component instead of two, and smaller.
4. **It uses the cap as information instead of being ruined by it.** The thing that destroys naive markup
   averages is the thing that makes the specification interesting: a known, event-varying censoring bound that
   identifies the upper region across events (`01-c` §4.7, F4).
5. **It needs none of the four missing listing fields**, so it is not gated on a data request, a decision by
   the operator, or money.

**Its residual distribution is also the only honest source of an interval** for a ticket price (F16), and it
feeds the value signal the optimiser consumes (F14's certainty equivalence).

**The caveat, stated so it is not a hidden weakness.** F3 cannot set the primary price. By §9.4, a model in
units of face is invariant to face, so the Phase 5 claim rests on **F10** instead, and F10 is the *weaker* of
the two, being censored, one-sided, gated on the meaning of `issuedCount` (C10), and supported only at class B
with no validated functional form. **So the honest summary of the engine is: the value and path claims rest on
F3 and are defensible as ratios with a floor; the primary-price claim rests on F10 and is a boundary
recommendation with a sign, not a level.** If only one of the two can be built, build F3; if the primary-price
claim is the one being judged, F10 is the one that has to be made to work, and no amount of work on F3
substitutes for it.

---

## 14. Traceability index

Every formulation, its primary source, and the theory it stands on. Finding sections are the authority for
what the source says; the DOIs are in those files and are not repeated here.

| # | Formulation | Finding (what it says here) | Standard theory it stands on |
|---|---|---|---|
| F1 | Martingale anchor | `02-a` §8.5 (B0 benchmark), §8.6 | random-walk forecast; Deneckere–Peck martingale as cited there |
| F2 | Repeat-sales index | `01-b` §4.1, `01-c` §4.2, §4.5, `02-a` §4.3 | Bailey–Muth–Nourse 1963; Gatzlaff–Haurin 1997; Steele–Goy 1997; Meese–Wallace 1997; Pakes 2003 |
| **F3** | **Censored hedonic (EM)** | `01-c` §4.3, §4.6 (the specification), `01-b` T4a, `01-a` §6 | Rosen 1974; Amemiya 1984; Tobit-type censored regression; EM for censored normal (Dempster–Laird–Rubin); `statistics.NormalDist` |
| F4 | Cap truncation, mass point, crossing | `02-a` §6.1–§6.3, `01-a` §3, `01-b` §4.4(ii), §4.5(iii), **the 02-B file is absent; this is the reconstruction** | censored-quantile identity; Powell 1986 (conditional estimator, a stronger object, C12); Glaeser–Luttmer 2003; Bulow–Klemperer 2012 (theory = C) |
| F5 | Deadline-convex path | `02-a` §5.1–§5.4, §8.1–§8.9 | Gallego–van Ryzin 1994; Sweeting 2012 (class A, shape only, C9); APC collinearity, Mason et al. 1973 / Luo 2019; fixed-effects meta-analysis |
| F6 | Local-level state space | `01-c` §7.4 | scalar Kalman filter/smoother; local-level state-space model |
| F7 | Composite intensity, CR, cure | `02-c` §3.1–§3.9, §1 | Cox 1972; Andersen–Gill 1982; Prentice–Gloeckler 1978; Holford 1980; Allison 1982; Fine–Gray 1999; Boag 1949; Maller–Zhou 1995 |
| F8 | `ξ(p,τ)` | `02-c` §2.4 | Working 1927 (why a realised-price locus is not demand) |
| F9 | Listing-episode hazard | `02-c` §4.1–§4.6 | cloglog discrete-time hazard; case-cohort (Prentice 1986); Working 1927 for the endogeneity |
| F10 | Primary sell-through bracket | `01-b` §4.4(i), `02-d` §3, `02-e` §2.4 | Tobit 1958; Conlon–Mortimer 2013 (inverted); Heckman 1979 |
| F11 | (OBJ), (WEDGE), (FOC-2) | `02-d` §1.2–§2.6 | Lerner condition under capacity truncation; tax incidence, Delipalla–Keen 1992; Weyl–Fabinger 2013 |
| F12 | (RN) grid + boundary | `02-d` §2.4, §4.2, §5.2 | constrained grid maximisation; corner/boundary solutions |
| F13 | Mean-CVaR | `02-d` §4.3 | Artzner et al. 1999 (coherence); Rockafellar–Uryasev 2000 (LP form, specified-not-implemented) |
| F14 | Reserve-price MDP | `01-c` §9.2–§9.5 | optimal stopping / free boundary, Peskir–Shiryaev 2006; MDP backward induction; certainty equivalence |
| F15 | Prequential scoring | `01-b` §4.6 (T6), `02-c` §5 | Murphy 1973 (reliability–resolution); Dawid 1982 (prequential); Gneiting–Raftery 2007 (properness) |
| F16 | Empirical quantile band | `01-c` §8.3, `02-a` §8.5 | empirical quantiles; Koenker–Bassett 1978 (LP form, specified-not-implemented); selective labels, Lakkaraju et al. 2017; Crook–Banasik 2004 |
| F17 | EB pooling / cold-start band | `02-e` §4.1–§4.8, `01-b` §4.6 (T1′) | Efron–Morris 1975; Efron 2010; Gelman 2006 (prior on `τ`); Hartung–Knapp small-`J` correction |
| F17a | `τ²` constraints | `02-e` §4.4, §4.5 | DerSimonian–Laird; Viechtbauer (upper limit from `Q`); Sidik–Jonkman; `χ²` quantiles |
| F17b | Borrowed population spread | `02-e` §4.7, `01-a` §2 | lognormal fit as a consistency check: Leslie–Sorensen's three reported facts |
| F18 | Gamma–Poisson exposure | `02-c` §1.8, §6.1–§6.2 | gamma–Poisson conjugacy; negative-binomial predictive |
| n/a | Balanced-view anchor (not a formulation) | `01-a` §5 (about 5% resale, measured twice), §6 (seat quality 0.61 vs 0.50) | a measured calibration fact carried into F17b and F3's A3 |

**Counts.** 18 numbered formulations recorded (F1 to F18), plus two recorded sub-formulations of F17 (F17a,
the constraint set for the between-event variance; F17b, the borrowed population spread), so 20 entries.

**Under D2 today, all 18 admit a stdlib implementation of auditable size**, and the reason is structural
rather than lucky: none of them needs a dense solve at a dimension that grows with the data. Three
qualifications, and they are different kinds:

- **Data-gated, not computation-gated:** F9. Its code is the same solver as F7 and is implementable now; it is
  switched off behind D3's four listing fields. Nothing about D2 stands in its way.
- **Implementable only in discrete form:** F14. Backward induction on a 216-state grid needs no matrix and is
  the numerical solution of the continuous problem; the continuous-time HJB is **specified-not-implemented**
  and is not needed.
- **Library-needing variants inside otherwise-implementable formulations, named and not attempted:** the
  Rockafellar–Uryasev LP inside F13 (the grid replaces it exactly to resolution), exact quantile regression
  inside F16 (IRLS is an approximation and is labelled one), HMC/NUTS inside F17 (the EB closed form and the
  grid are the honest subset), and non-conjugate random-effects quadrature inside F7/F17.

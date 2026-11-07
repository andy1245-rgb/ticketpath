# Phase 1-B — Identifiability of the pricing targets

**Status:** complete (first pass). **Written:** 2026-11-07T08:55Z. **Author:** Phase 1-B research agent.
**Depends on:** `RESEARCH-PROGRAM.md` §4, §3 (Phase 1; Phase 2 A, C, F); `records/00-data-situation.md`;
`../ticketing-frontend/lib/types.ts`; `records/README.md`. **Append-only.** Disagreements with
`00-data-situation.md` are recorded in §5, not resolved silently.

---

## 1. What I concluded

Of the six target quantities, **one is honestly buildable today, two are set-identified with bounds we can
actually compute, and three are not identified at all.** The ledger buys a *price-change* index, a *sale
frequency*, and a set of *one-sided lower bounds* on value wherever the resale ceiling binds — not a price, not
a demand curve, and not a sale-probability curve. The binding constraint is narrower than the Phase 0 audit
states and lands somewhere else. The ticket population is fully enumerated (every ticket carries an `issue` row
and a known life from issue to redemption or event end), so the at-risk denominator is observed and the
unconditional sale rate per ticket-time is identified. What is missing is the **asking price of the risk set**:
the mark is recorded only on the success branch, making this a case-only sample with no controls rather than a
numerator without a denominator. That distinction changes the build. A time-and-ticket-conditional baseline
intensity is estimable now; a price-response multiplier is not, and no modelling choice recovers it. The
consequences are §6: build the identified parts on the data as it stands, flag the rest UNVALIDATED with its
test, and specify the missing observations as data requirements — four fields per listing convert the hardest of
these from unidentifiable to directly estimable.

---

## 2. The identification primitive

Treat the observation set as a marked point process on the ticket population. For ticket $i$ with attributes
$x_i$ we observe ordered events $(t_{ik}, m_{ik})$ where the mark is one of {sale at price $p$, transfer at
price $\varnothing$, redeem, revoke}, and a terminal observation $T_i = \min(\text{redeem}_i, \text{event end})$.
Two features do all the work below.

**(a) The population is censused; the price is not.** Every ticket appears, so the risk set
$\{(i,t): t \in [\text{issue}_i, T_i]\}$ is observed; only the price is event-time-only. This is **informative
observation times** / **informative censoring** — the observation mechanism depends on the outcome. When
censoring is informative the naive estimator is inconsistent and the correct object is a conditional model
([Lagakos 1979](https://doi.org/10.2307/2529941)).

**(b) The mark is a censored draw, not a measurement of the latent.** A trade at $p$ reveals $p$, not the
buyer's willingness to pay or the seller's reservation: $p=V$ at that instant only under price-taking, which is
class C; under bargaining $V$ is interval-identified with unobserved width; under a binding ceiling the trade
reveals $V \ge p_0(1+c)$ only. Every row below is an application of (a) or (b).

---

## 3. Identifiability ledger

| # | Quantity | Status | Assumption needed | Minimal additional observation | Key source |
|---|---|---|---|---|---|
| **T1** | Latent resale value $V_i(t)$ | **Set-identified at trade instants**; **not identified between trades** or for never-traded tickets; level identified only up to an affine normalisation | Martingale interpolation; price-taking at trade; cap non-binding, or $V\ge$ cap | A second trade or a quote in the interval; for the level, one exogenous price anchor | [Bailey, Muth & Nourse 1963](https://doi.org/10.1080/01621459.1963.10480679); [Case & Shiller 1987](https://doi.org/10.3386/w2393); [Ekeland, Heckman & Nesheim 2004](https://doi.org/10.1086/379947) |
| **T1′** | $V$ for an event with no resale history | **Not identified.** Only a prior predictive | Exchangeability of events given covariates; a *known* between-event variance | $\ge 2$ completed events per stratum with resale activity | [Efron & Morris 1975](https://doi.org/10.1080/01621459.1975.10479864) |
| **T2** | Price path over the remaining horizon | **Set-identified:** curvature and event deviations identified, **linear trend not identified** (exact age–period–cohort collinearity); path identified only for repeat-traded tickets | A normalising restriction on the linear component; no compositional drift between first and second sale | Staggered start dates (already present) plus one normalisation; seat coordinates to fix within-tier mix | [Mason et al. 1973](https://doi.org/10.2307/2094398); [Luo 2019](https://doi.org/10.1146/annurev-soc-073018-022616); [Sweeting 2012](https://doi.org/10.1086/669254) |
| **T3** | Sale hazard as a function of price | **Not identified.** Only $\lambda(t\mid p)\cdot\Pr(\text{ask}=p\mid\text{listed},t)\cdot\Pr(\text{listed}\mid t)$ is. The unconditional intensity $\lambda_0(t)$ **is** identified | That the ask is exogenous to value | Listing panel `{listPrice, listedAt, delistedAt, delistReason}`; asks on a random subset of the risk set | [Cox 1972](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x); [Prentice 1986](https://doi.org/10.1093/biomet/73.1.1); [Working 1927](https://doi.org/10.2307/1883501) |
| **T4a** | Hedonic price function (equilibrium locus) | **Set-identified up to affine transformation**, subject to selection | Attribute prices constant over the window; sold units representative | Seat coordinates (dominant within-event axis) | [Rosen 1974](https://doi.org/10.1086/260169); [Brown & Rosen 1982](https://doi.org/10.2307/1912614); Ekeland et al. 2004 |
| **T4b** | Demand / WTP, elasticity | **Not identified** from secondary trades. **Set-identified from primary sell-through**, bounded below at each distinct cap level | Uniform primary pricing; `faceValueLamports` = primary transaction price; `issuedCount` = sold | Primary inventory time series; exogenous price variation for elasticity | [Heckman 1979](https://doi.org/10.2307/1912352); [Tobin 1958](https://doi.org/10.2307/1907382); [Conlon & Mortimer 2013](https://doi.org/10.1257/mic.5.4.1) |
| **T5** | Primary price maximising risk-adjusted net value | **Set-identified, width = union of the T3 and T4 widths.** Structure and one-sided bounds identified; point optimum not | The T3/T4 models; a fee model; a risk functional | Nothing of its own | [Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999); [Leslie & Sorensen 2014](https://doi.org/10.1093/restud/rdt033) |
| **T6** | Predictive uncertainty, calibration | **Estimable for the sale indicator on the full population; not validatable for any price distribution** | That the evaluation sample is representative — false by construction for prices | Ask panel, or a random hold-out of listings scored but not sold | [Murphy 1973](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2); [Lakkaraju et al. 2017](https://doi.org/10.1145/3097983.3098066) |

---

## 4. The argument, row by row

### 4.1 T1 — the value level, and the absence of a free anchor

Repeat-sales is unusually well-suited here, for a reason worth stating because it is the one place this market
is *easier* than the literature's home turf. The Bailey–Muth–Nourse estimator regresses
$\log p_{i2}-\log p_{i1}$ on a pair of time dummies, so the ticket fixed effect differences out and nothing
about which ticket it is need be known. The BMN assumption that quality is unchanged between sales is, for a
ticket, **literally true**: the attribute vector is fixed at mint, with no decay and no renovation. Quality
change is zero. *(Class C — an argument, not a measurement.)*

Three residual nonstationarities remain. (i) **Ageing, not quality change:** remaining life shrinks
monotonically and price moves for that reason, so the index mixes a calendar effect with an age effect — the T2
problem. (ii) **Real news** (lineup, injuries, weather) is a genuine price change for an unchanged asset. (iii)
**Within-tier composition:** with no seat coordinates "quality" is tier-level only, so differencing removes the
tier mean but not the within-tier mix. *(Class C.)*

Selection is the harder problem and has its own literature: properties transacting twice are not a random
sample and repeat-sales indices are biased accordingly
([Gatzlaff & Haurin 1997](https://doi.org/10.1023/A:1007763816289)), the bias concentrating in short-hold pairs
([Steele & Goy 1997](https://doi.org/10.1023/A:1007780219924)), with
[Goetzmann 1992](https://doi.org/10.1007/BF00153997) and [Meese & Wallace
1997](https://doi.org/10.1023/A:1007715917198) on estimator accuracy and alternatives. Here selection is
direct: ~~only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of an already-selected
subset~~ **[CORRECTION 2026-11-07T14:00Z, R2-1 — dead: 90 is a `sale` row count, not a ticket count, and 49 of 128 tickets sell (128 − 79); the sentence is also a `lib/mock/` figure doing argumentative work, which the audit bars. See CORRECTION 1 at the end of this file.]**

Then the decisive point, unregistered in the programme so far: **a repeat-sales index identifies only ratios.**
The level is not in the data, and the natural-looking anchor — face value — is endogenous, being the primary
seller's choice and the denominator of the markup under measurement. This is not a small-sample complaint.
Ekeland, Heckman and Nesheim prove that in an additive hedonic model, preferences and technology are identified
from a single market **up to affine transformations**
([Ekeland, Heckman & Nesheim 2004](https://doi.org/10.1086/379947)); an affine indeterminacy is precisely a
missing location and scale, i.e. exactly the missing price anchor. T1's level needs one exogenous reference
price, and the observation set contains none. *(Class C.)*

### 4.2 T2 — the path, and the age–period–cohort trap

Within one event, time-to-event and calendar time are the same variable up to a constant:
$\text{age}=t-\text{start}_j$. A single event cannot distinguish "prices fall as the event approaches" from
"prices fell in March". Across events with different start dates there is variation, but the three-way
decomposition has an exact linear dependency, age + cohort = period, so the **linear component is not
identified**. The APC literature converged on bounds precisely because every point estimator is a normalisation
in disguise ([Luo 2019](https://doi.org/10.1146/annurev-soc-073018-022616); original statement in
[Mason et al. 1973](https://doi.org/10.2307/2094398)). Curvature *is* identified: "prices decline, accelerating
in the last week" is estimable; "prices decline by $k$% per day" is not, without a declared normalisation.

The shape has a class-A anchor. Sweeting, using two online MLB secondary markets with listing prices, sale
times and seller types, finds that **controlling for ticket quality, prices decline significantly as the game
approaches**, because the opportunity cost of holding falls as future selling opportunities disappear
([Sweeting 2012](https://doi.org/10.1086/669254)). That is declining option value of continued search — the
stopping structure of [Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999). It is also a warning:
Sweeting needed listings. On transactions alone the question is answered from a stale, irregularly-sampled
series — the nonsynchronous-trading problem ([Lo & MacKinlay 1990](https://doi.org/10.1016/0304-4076(90)90098-E))
— and a ticket trading twice in its life is thinner than almost any stock in that literature.

**The terminal condition does not help.** $V=0$ after the event starts is true and useless, because the limit
from inside is not zero — use value at the gate can be large, so value jumps at the boundary rather than
approaching it. Unlike an option, the ticket's terminal payoff is an unobserved use value. Expiry is a wall,
not an anchor. *(Class C.)*

### 4.3 T3 — the crux, and the exact reason it fails

The rate at which sales at price $p$ are observed is

$$\lambda_{\text{obs}}(p,t)=\lambda(t\mid p)\cdot\pi(p\mid\text{listed},t)\cdot s(t),$$

with $\lambda$ the wanted hazard, $\pi$ the density of asks across sellers, $s$ the probability a ticket is
listed at all. We observe the left side; nothing separates the three factors, because **the mark is recorded
only where the sale happened** — a non-seller has no ask in the record. The denominator exists and is large; it
is the *price of the risk set* that is absent.

The literature states the fix exactly. In a case-cohort design an expensive time-varying covariate is measured
on all cases plus a *random subset of the risk set*, and the relative-risk parameters are then identified
([Prentice 1986](https://doi.org/10.1093/biomet/73.1.1)). Our problem is that the random subset of the risk
set — a sample of asks that did *not* sell — is the specific thing the schema lacks. Hence the missing
observation is the ask, not the exposure. Formally the ask is an endogenous regressor: sellers choose it,
plausibly on private information about $V$, so regressing sale on price traces neither demand nor supply but
the locus of their intersections ([Working 1927](https://doi.org/10.2307/1883501)).

Three things survive, and are worth having.

1. **The unconditional intensity $\lambda_0(t)$** and its dependence on ticket covariates. Sales per
   ticket-day at risk are fully identified from the censused population, with right-censoring at redemption
   and event end handled by ordinary survival methods
   ([Cox 1972](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x)).
2. **The competing-risks split** among sale, unpriced transfer, redeem and revoke, with terminal states read
   as competing events rather than censoring. This matters: ~~14 of 128 tickets redeem~~ **[CORRECTION
   2026-11-07T14:00Z, R2-2 — dead: 14 is a `redeem` row count; the record carries no ticket-level redemption
   count]**, and treating redemption
   as censoring inflates the sale hazard because it removes tickets for reasons correlated with demand
   ([Fine & Gray 1999](https://doi.org/10.1080/01621459.1999.10474144)).
3. **The never-sells**, as a cure component rather than an infinite duration: a point mass at "will never be
   offered" ~~fits 79-of-128 better than a long tail~~ **[CORRECTION 2026-11-07T14:00Z, R2-3 — dead as the
   ground for the model form: 79-of-128 is a recorded property of the fixture, and §4.6 of the audit bars a
   `lib/mock/` figure from choosing a specification. The cure component is argued from censusing and from
   Boag (1949), not from that fraction]** and is identifiable when tickets are censused
   ([Boag 1949](https://doi.org/10.1111/j.2517-6161.1949.tb00020.x)). Cure means "not returned to market in
   the window", not "valued at nothing" — an owner who attends is a non-seller, not a zero.

The price response is not recoverable. The error to avoid is fitting $\lambda(p)$ on observed sales and
reporting it as the sale-probability curve: it will look monotone, it will look well-behaved, and it will be an
artefact of which sellers chose which prices. **[D — dangerous precisely because it will look estimable.]**

### 4.4 T4 — hedonic price function versus demand function

Conflating these two objects is the most common error in pricing work. **The hedonic price function** — the
equilibrium locus mapping attributes to price — is a *forecasting* object, identified up to the affine
indeterminacy of §4.1 and the selection of §3. Fitting $\log p$ on tier, event, city and time-to-event is
legitimate class C machinery with class B support, and is what a pricing engine needs for features. Its tier
coefficient is *not* marginal willingness to pay.

**The demand function** is not identified from trades. Rosen's second stage does not separate demand from
supply in a single market ([Rosen 1974](https://doi.org/10.1086/260169);
[Brown & Rosen 1982](https://doi.org/10.2307/1912614)); Ekeland, Heckman and Nesheim's sharpest statement is
that identification *is* available from a single market, but only from *data on demand and supply* — the joint
distribution of offered bundles and buyers' choices — only up to an affine transformation, and only by leaning
on generic equilibrium nonlinearity. We observe offered bundles and accepted purchases; we observe neither
buyers, nor their choices among simultaneous alternatives, nor anyone who declined. *(Class C, and it cuts
against us.)* With costly search, price dispersion is itself an equilibrium object shaped by search costs, so
the transaction-price distribution reflects frictions as much as valuations
([Burdett & Judd 1983](https://doi.org/10.2307/1912045)). *(Class B.)*

Two routes are already in the schema, and this is the report's highest-value finding. **(i) The primary market
is a demand experiment already run.** Each tier carries `faceValueLamports` and `issuedCount` versus
`totalSupply`. A sold-out tier is *censored* — demand met or exceeded supply at that price; an unsold tier is a
*point on the demand curve* — demand equals issued where supply remained. That is a Tobit with an observed
censoring indicator, the benign case ([Tobin 1958](https://doi.org/10.2307/1907382)), needing no secondary data
at all: demand estimation under incomplete availability
([Conlon & Mortimer 2013](https://doi.org/10.1257/mic.5.4.1)) inverted, since availability is observed and
demand is not. Cross-event and cross-tier variation in face value then bounds a demand schedule. *(Class B;
UNVALIDATED for any functional form.)* **(ii) The cap gives free lower bounds.** Because the cap is bps over
*each tier's own* face, its absolute level differs across tiers within one event; and because it is observed
rather than latent, "a sale occurs at exactly the cap" is the one-sided statement $V\ge p_0(1+c)$. Across
events with different caps, such statements at different points trace a **lower bound on the survival function
of willingness to pay at each cap level.** Sign and one-sided magnitude identified; location not.

### 4.5 T5 — the primary optimum

The objective is class C: choose $p_0$ to maximise expected risk-adjusted net value over the sale process, the
resale market supplying the value signal ([Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999)).
Its two inputs are T3 and T4, both non-identified, so the optimum inherits their width. A point optimum would
be overclaiming; the deliverable is a set with a sensitivity map.

Three identified results change the design. **(i) An ad-valorem fee is neutral for the ask:** with net
$p(1-\phi)$, $\arg\max_p p(1-\phi)h(p)=\arg\max_p p\,h(p)$, so the missing fee field does **not** bite on the
resale recommendation — only on the primary optimum, where it shifts the buyer's total cost, and on
participation. This narrows Gap 4. *(Class C, one line.)* **(ii) The cap is proportional, so the band is
scale-free:** raising $p_0$ raises the ceiling $p_0(1+c)$ in the same proportion, so the band translates and
the seller's problem collapses to *where to sit in the willingness-to-pay distribution*, trading volume against
margin — one dimension, monotone, needing no knowledge of the cap's absolute level. *(Class C.)*
**(iii) Surplus above the cap does not accrue to the buyer, so the objective must not credit it:** competition
dissipates it through non-price channels ([Bulow & Klemperer 2012](https://doi.org/10.1086/665416)), and the
allocation behind the ceiling is effectively random among those who want the good, so observed consumption
carries no information about valuations ([Glaeser & Luttmer 2003](https://doi.org/10.1257/000282803769206188)).
A ticket sold at the cap went to whoever was fastest — a statement about latency, not value. *(Class B.)*

A gap to record: I found **no peer-reviewed econometric study of resale price caps in ticket markets.** The
ticket literature covers resale's allocative and rent-seeking effects
([Leslie & Sorensen 2014](https://doi.org/10.1093/restud/rdt033): class A, resale raises allocative efficiency
by about 5% with a third eaten by rent-seeking, from merged primary and secondary data) and price dynamics
([Sweeting 2012](https://doi.org/10.1086/669254)), not caps. The cap component is therefore class B borrowed
from rent control plus class C theory, and **no class-A claim about caps may appear in the deliverable.**

### 4.6 T6, cold start, and measurement error

**T6.** Calibration is methods-complete and data-blocked. For the sale indicator the population is complete, so
Brier scores, reliability curves and the reliability–resolution decomposition are computable honestly on every
ticket ([Murphy 1973](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2); prequential
calibration in [Dawid 1982](https://doi.org/10.1080/01621459.1982.10477856)). For any *price* distribution it is
not, because every scored observation is conditioned on "sold at this price", and whether a ticket sold is the
very dependence being measured — the selective-labels problem
([Lakkaraju et al. 2017](https://doi.org/10.1145/3097983.3098066)), whose mature analogue, reject inference in
credit scoring, generally fails to improve performance
([Crook & Banasik 2004](https://doi.org/10.1016/S0378-4266(03)00203-6)). Report the interval, label the
calibration UNVALIDATED, quote no coverage number.

**T1′ cold start.** With no resale history the posterior predictive is the prior predictive. Empirical-Bayes
shrinkage is the tool and its requirement is explicit: the between-event variance needs $\ge 2$ groups and is
estimated with roughly $J$ degrees of freedom, so with few events the shrinkage factor is itself nearly
unidentified and the interval must widen, not narrow
([Efron & Morris 1975](https://doi.org/10.1080/01621459.1975.10479864)). Cross-city transfer is an assumption,
not an identification result.

**Measurement error.** Integer lamports is *not* a measurement-error problem: $\pm0.5$ lamport on prices of
order $10^9$ is a relative error near $10^{-9}$. Three real problems. (a) *Gift-versus-sale misclassification:*
`transfer` carries a null price, but a related-party sale at exactly face is indistinguishable from a market
one; a mismeasured binary regressor gives bounds, not a point, with a known attenuation direction
([Bollinger 1996](https://doi.org/10.1016/S0304-4076(95)01730-5);
[Aigner 1973](https://doi.org/10.1016/0304-4076(73)90005-5)). If gifts are coded as sales, observed resale
propensity is **too high** and mean markup **too low**, so ~~79-of-128 is an upper bound on the
never-*offered* fraction~~ **[CORRECTION 2026-11-07T14:00Z, R2-4 — dead as a market bound: the fraction is a
recorded property of the fixture, so it bounds nothing about tickets offered or not offered on the platform.
The attenuation direction (resale propensity too high, markup too low) stands on Bollinger and Aigner and is
unchanged]**. (b) *Seller identity:* Bitcoin-style clustering does not transfer — it relies on UTXO
co-spend and Solana is account-based ([Meiklejohn et al. 2013](https://doi.org/10.1145/2504730.2504747)). What
is available directly: a repeat reseller appears as the same `fromWallet` across tickets, and `issuedToWallet`
links primary to secondary counterparties with no inference. Repeat-reseller behaviour is partially identified;
whether two wallets are one person is not. (c) *The clock:* `occurredAt` is ISO-8601 at unspecified
granularity while `slot` is strictly monotone, so any hazard model must derive its time index from `slot` — a
small point with a large failure mode, negative durations.

---

## 5. Where this disagrees with `records/00-data-situation.md`

Recorded, not resolved. Three narrowings and one widening.

1. **Gap 1 is misdiagnosed; the fix is right.** The audit calls the sale count "a numerator with no
   denominator". The denominator is present — every ticket has an `issue` row and a known life. The unobserved
   object is the ask of the risk set. Severity is therefore **too high** for the baseline intensity
   (identified, buildable) and **correct** for the price response. The four-field fix follows either way.
2. **The asking-versus-realised gap does not shrink; it vanishes.** There is *no ask anywhere in the record*,
   so there is no wedge to estimate, and a whole block of Phase 2 A — listing revision, duplicate listings,
   seller competition, price discovery through asking — is not partially available but **entirely
   unavailable**. Saying so plainly stops a subagent being dispatched to research something unusable.
3. **Gap 2 cuts both ways; the audit sees only the bad side.** Worse: behind the ceiling allocation is random
   among those who want the ticket, so the observed markup distribution says nothing about rationed buyers'
   valuations. Better: `resalePriceCapBps` is *observed and varies*, ~~across events and across tiers within an
   event because it is bps over each tier's own face — so the cap is an instrument, not merely a nuisance~~
   **[CORRECTION 2026-11-07T14:00Z, R2-12 — dead: the field is one on `Event`, so there is no within-event
   variation and no within-event instrument; the instrument is cross-event only, confounded with everything
   else that varies across events. See CORRECTION 2 at the end of this file]**, and
   the mass point at the cap is directly observable as `markupBps` equal to the cap, identifying the rationed
   *quantity* though not the latent tail's location. And the audit's own fixture check (no sale lands exactly
   on any cap) means the cap component **cannot be exercised on the fixtures at all**.
4. **Gap 4 is narrower than stated.** An ad-valorem fee is neutral for the resale ask (§4.5(i)), non-neutral
   for the primary optimum and participation. It belongs in the optimiser's interface, not a blocker list.

Two additions. `faceValueLamports` may not equal the primary *transaction* price (a discount or fee breaks the
assumption), and `issuedCount` may mean minted rather than sold; both are operator questions and both are
load-bearing for §4.4(i). And the primary sell-through data, dismissed as "a snapshot … velocity not
observable", is the one place in the schema where a demand object is identified — velocity is not needed for
the level.

---

## 6. The three design consequences

**(1) Buildable now, no unstated assumption.** The repeat-sales index of resale value *changes* per event and
tier, reported as normalised ratios (§4.1); the time-to-event baseline sale intensity with competing risks and
a cure component plus covariates (§4.3); the cap-binding indicator, the excess mass at the cap, and the
resulting one-sided bounds on value and on the WTP survival function (§4.4(ii), §4.5); the primary
sell-through demand bracket per tier (§4.4(i)); and calibration machinery for the sale indicator on the full
population (§4.6). These are honest now at class B/C and are most of what a *risk-aware, not point-optimal*
engine needs.

**(2) Buildable only on a stated assumption, flagged UNVALIDATED with its test.** The price-to-sale-probability
curve in any functional form — test: a randomised ask arm, or the listing panel (§4.3). The *level* of $V$,
since only ratios are identified — test: an exogenous price anchor, which the schema does not contain (§4.1).
Interpolation between trades — test: whether a martingale assumption prices observed second sales out of sample
(§4.2). The location of the latent right tail above the cap — test: a cap-free event; until then only the mass
is claimable (§4.5). Seller-side heterogeneity, since persons are unlinkable — test: repeat-seller fixed effects
on wallets that do link (§4.6). The primary optimum's point value — report the set (§4.5).

**(3) Specify as a data requirement, not as a model.** Four fields per listing —
`{listPriceLamports, listedAt, delistedAt, delistReason}`, with `delistReason` separating sold from withdrawn —
convert the sale hazard from unidentifiable to a standard time-varying-covariate survival problem, and are
worth more than any modelling choice in this programme (§4.3). Then, in descending value: fee, royalty and
net-to-seller figures, needed for the primary objective though the resale ask is fee-neutral (§4.5(i)); a
primary inventory time series with on-sale and hold-back times, converting the demand bracket into a booking
curve; seat coordinates, without which the strongest within-event price axis is unexpressible and the pitch in
`AGENTS.md` is unsupported; and any record at all of the buy side — bids, offers, views, searches — because
*every* demand statement in this programme currently rests on assumption rather than observation. The bid side
is the single most valuable absent observation, and no amount of econometrics substitutes for it.

---

## 7. Sources

Metadata for every item below was checked against Crossref or OpenAlex during this pass; no citation is from
memory alone and no numeric result is quoted that was not read from a primary abstract.

Aigner, D. J. (1973). Regression with a binary independent variable subject to errors of observation.
*Journal of Econometrics* 1(1), 49–59. https://doi.org/10.1016/0304-4076(73)90005-5

Bailey, M. J., Muth, R. F., & Nourse, H. O. (1963). A regression method for real estate price index
construction. *JASA* 58(304), 933–942. https://doi.org/10.1080/01621459.1963.10480679

Boag, J. W. (1949). Maximum likelihood estimates of the proportion of patients cured by cancer therapy.
*JRSS-B* 11(1), 15–44. https://doi.org/10.1111/j.2517-6161.1949.tb00020.x

Bollinger, C. R. (1996). Bounding mean regressions when a binary regressor is mismeasured. *Journal of
Econometrics* 73(2), 387–399. https://doi.org/10.1016/S0304-4076(95)01730-5

Brown, J. N., & Rosen, H. S. (1982). On the estimation of structural hedonic price models. *Econometrica*
50(3), 765–768. https://doi.org/10.2307/1912614

Bulow, J., & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer surplus. *JPE* 120(1),
160–186. https://doi.org/10.1086/665416

Burdett, K., & Judd, K. L. (1983). Equilibrium price dispersion. *Econometrica* 51(4), 955–969.
https://doi.org/10.2307/1912045

Case, K. E., & Shiller, R. J. (1987). Prices of single family homes since 1970: new indexes for four cities.
NBER Working Paper 2393. https://doi.org/10.3386/w2393

Conlon, C. T., & Mortimer, J. H. (2013). Demand estimation under incomplete product availability.
*AEJ: Microeconomics* 5(4), 1–30. https://doi.org/10.1257/mic.5.4.1

Cox, D. R. (1972). Regression models and life-tables. *JRSS-B* 34(2), 187–202.
https://doi.org/10.1111/j.2517-6161.1972.tb00899.x

Crook, J. N., & Banasik, J. (2004). Does reject inference really improve the performance of application
scoring models? *Journal of Banking & Finance* 28(4), 857–874. https://doi.org/10.1016/S0378-4266(03)00203-6

Dawid, A. P. (1982). The well-calibrated Bayesian. *JASA* 77(379), 605–610.
https://doi.org/10.1080/01621459.1982.10477856

Efron, B., & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *JASA*
70(350), 311–319. https://doi.org/10.1080/01621459.1975.10479864

Ekeland, I., Heckman, J. J., & Nesheim, L. (2004). Identification and estimation of hedonic models.
*JPE* 112(S1), S60–S109. https://doi.org/10.1086/379947

Fine, J. P., & Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk.
*JASA* 94(446), 496–509. https://doi.org/10.1080/01621459.1999.10474144

Gallego, G., & van Ryzin, G. (1994). Optimal dynamic pricing of inventories with stochastic demand over
finite horizons. *Management Science* 40(8), 999–1020. https://doi.org/10.1287/mnsc.40.8.999

Gatzlaff, D. H., & Haurin, D. R. (1997). Sample selection bias and repeat-sales index estimates. *Journal of
Real Estate Finance and Economics* 14(1), 33–50. https://doi.org/10.1023/A:1007763816289

Glaeser, E. L., & Luttmer, E. F. P. (2003). The misallocation of housing under rent control. *AER* 93(4),
1027–1046. https://doi.org/10.1257/000282803769206188

Goetzmann, W. N. (1992). The accuracy of real estate indices: repeat sale estimators. *Journal of Real Estate
Finance and Economics* 5(1), 5–53. https://doi.org/10.1007/BF00153997

Heckman, J. J. (1979). Sample selection bias as a specification error. *Econometrica* 47(1), 153–161.
https://doi.org/10.2307/1912352

Lagakos, S. W. (1979). General right censoring and its impact on the analysis of survival data. *Biometrics*
35(1), 139–156. https://doi.org/10.2307/2529941

Lakkaraju, H., Kleinberg, J., Leskovec, J., Ludwig, J., & Mullainathan, S. (2017). The selective labels
problem: decision making and predictability. *KDD '17*, 275–284. https://doi.org/10.1145/3097983.3098066

Leslie, P., & Sorensen, A. (2014). Resale and rent-seeking: an application to ticket markets. *Review of
Economic Studies* 81(1), 266–300. https://doi.org/10.1093/restud/rdt033

Lo, A. W., & MacKinlay, A. C. (1990). An econometric analysis of nonsynchronous trading. *Journal of
Econometrics* 45(1–2), 181–211. https://doi.org/10.1016/0304-4076(90)90098-E

Luo, L. (2019). Analyzing age-period-cohort data: a review and critique. *Annual Review of Sociology* 45,
467–492. https://doi.org/10.1146/annurev-soc-073018-022616

Mason, K. O., Mason, W. M., Winship, C., & Poole, W. K. (1973). Some methodological issues in cohort analysis
of archival data. *American Sociological Review* 38(2), 242–258. https://doi.org/10.2307/2094398

Meese, R. A., & Wallace, N. E. (1997). The construction of residential housing price indices: a comparison of
repeat-sales, hedonic-regression, and hybrid approaches. *Journal of Real Estate Finance and Economics*
14(1), 51–73. https://doi.org/10.1023/A:1007715917198

Meiklejohn, S., Pomarole, M., Jordan, G., Levchenko, K., McCoy, D., Voelker, G. M., & Savage, S. (2013). A
fistful of bitcoins: characterizing payments among men with no names. *IMC '13*, 127–140.
https://doi.org/10.1145/2504730.2504747

Murphy, A. H. (1973). A new vector partition of the probability score. *Journal of Applied Meteorology* 12(4),
595–600. https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2

Prentice, R. L. (1986). A case-cohort design for epidemiologic cohort studies and disease prevention trials.
*Biometrika* 73(1), 1–11. https://doi.org/10.1093/biomet/73.1.1

Rosen, S. (1974). Hedonic prices and implicit markets: product differentiation in pure competition. *JPE*
82(1), 34–55. https://doi.org/10.1086/260169

Steele, M., & Goy, R. (1997). Short holds, the distributions of first and second sales, and bias in the
repeat-sales price index. *Journal of Real Estate Finance and Economics* 14(1).
https://doi.org/10.1023/A:1007780219924

Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence from secondary markets for
Major League Baseball tickets. *JPE* 120(6), 1133–1172. https://doi.org/10.1086/669254

Tobin, J. (1958). Estimation of relationships for limited dependent variables. *Econometrica* 26(1), 24–36.
https://doi.org/10.2307/1907382

Working, E. J. (1927). What do statistical "demand curves" show? *QJE* 41(2), 212–235.
https://doi.org/10.2307/1883501

---

## CORRECTION 1 (2026-11-07T11:28Z) — the fixture counts in §4.1 and §4.3 are row counts, not ticket counts

Appended by the corrections pass after `records/findings/00-verification-round1.md`. Nothing above is deleted.
The sentences quoted are withdrawn as printed; the arguments they support are restated below where they survive.

**Withdrawn sentence, §4.1:**

> "Here selection is direct: only 90 of 128 fixture tickets ever sell, so pairs come from the liquid subset of
> an already-selected subset."

**What is true.** 90 is the number of `sale` **rows** in `lib/mock/`, not the number of tickets that sell.
`records/00-data-situation.md` §2 records the fixture as 253 ledger rows "(128 `issue`, 90 `sale`, 21
`transfer`, 14 `redeem`)" and, in the same paragraph, that "79 of 128 tickets have no sale at all
(`lastSalePriceLamports` null)". Arithmetic on those two statements:

- 128 + 90 + 21 + 14 = 253 rows, which is the total the audit states.
- 128 − 79 = **49** tickets with at least one sale.
- 90 sale rows spread over 49 tickets means 41 tickets sold more than once, and that repeat-sold group, not
  the 90 rows, is the population a repeat-sales index uses.

The two numbers already sat in this file and disagreed: §4.6 uses the audit's "79-of-128" correctly. The
figure to carry forward is **49 tickets sell, 79 never do, from 90 sale rows**.

**The second defect in the same sentence: it breaks the programme's own rule.** `00-data-situation.md` §2
adopts the rule in terms: fixtures "may be used only to exercise code paths and schemas (parsing, validation,
arithmetic, rendering, plumbing). They may never enter an estimation, a validation claim, or a result. **No
number in this programme comes from `lib/mock/`.**" §4.1 uses a fixture count as a measured selection rate
inside the T1 argument. It is one of two places in this file where a `lib/mock/` figure does argumentative
work (the other is noted at the end of this correction), and it is withdrawn.

**Also corrected, §4.3 item 2:** "This matters: 14 of 128 tickets redeem". 14 is the `redeem` row count. The
audit reports no ticket-level count of redemptions, so unlike the sale case the ticket count **cannot be
reconciled from the record**: one redemption per ticket would make 14 rows 14 tickets, but nothing in
`00-data-situation.md` establishes that, and I did not count the fixture to settle it, because the rule above
forbids producing a number that way. Read the claim as "14 `redeem` rows". The substantive point, that
redemption removes a ticket for reasons correlated with demand and therefore belongs in a competing-risks
specification rather than in censoring, does not depend on the count and stands (Fine & Gray 1999).

**Checked and left alone.** The three uses of "79-of-128" in §4.3 item 3, §4.6 and §5.3 are the audit's own
recorded property of the fixture, and the value is arithmetically consistent with the row counts, so nothing
is substituted. One of the three, §4.3 item 3, does use the fixture fraction to argue that a cure component
"fits 79-of-128 better than a long tail". That is a fixture figure making a model-form choice, which the rule
also forbids. The cure argument survives on Boag (1949) and on the logic that the population is censused; it
should be argued from those and not from the fixture's never-sell fraction.

**Consequence.** The selection argument stands as class C and is not weakened: properties that transact twice
are not a random sample (Gatzlaff & Haurin 1997; Steele & Goy 1997), and on the record we actually hold, the
number of tickets that have sold is zero, because there is no real ledger yet. What is withdrawn is the
sentence's implicit claim to have measured the selection rate on data.

---

## CORRECTION 2 (2026-11-07T11:28Z) — §5.3's within-event cap claim is withdrawn

**Withdrawn sentence, §5.3 item 3:**

> "Better: `resalePriceCapBps` is *observed and varies*, across events and across tiers within an event
> because it is bps over each tier's own face — so the cap is an instrument, not merely a nuisance"

**What is true.** `resalePriceCapBps: number | null` is a **single field on `Event`**. `TicketTier` carries
five fields and no cap (`../ticketing-frontend/lib/types.ts`). The basis-point cap therefore does
**not** vary within an event. What varies within an event is the *money ceiling* that the one cap implies,
which is `faceValue_tier × (1 + c)` and so moves exactly in proportion to each tier's own face value. A
ceiling that is a fixed multiple of the tier's own price carries no information independent of that price. It
is collinear with the tier's face by construction.

`01-c-methods.md` §1.4(1) reaches this and is right. One detail: its citation is to "§4.4(ii)", while the
sentence it quotes and corrects is §5.3's. §4.4(ii) above is already correct on this point ("its absolute
level differs across tiers within one event"), so nothing in §4.4(ii) changes.

**Withdrawn:** the claim that the cap supplies within-event *identifying* variation, and with it the
unqualified phrase "the cap is an instrument". **What survives:** the cap is observed rather than latent; it
varies across events, where the instrument lives; the mass point at the cap is observable as `markupBps`
equal to the cap; and the one-sided statements V ≥ p₀(1+c) at different cap levels still trace a lower bound
on the willingness-to-pay survival function. The cross-event instrument is confounded with everything else
that varies across events, and any use of it has to name that confound.

**Consequence.** Any claim resting on within-event cap variation is withdrawn. No other section of this file
makes one: §4.5(ii)'s scale-free algebra (raising the primary price raises the ceiling in the same
proportion) does not need within-event variation and stands as written. What cannot be claimed from the cap
is econometric leverage across tiers within a single event.

`records/C-variable-registry.md` C-3 repeats the withdrawn sentence and carries its own correction.
`records/D-model-registry.md` C6 and `records/B-mathematical-kb.md` C6 already record `01-c`'s version and
agree with this one.

---

## CORRECTION 3 (2026-11-07T11:28Z) — two author attributions in §7 are wrong

§7 opens: "Metadata for every item below was checked against Crossref or OpenAlex during this pass; no
citation is from memory alone". Two entries do not survive a Crossref query made for this correction pass on
2026-11-07 (`https://api.crossref.org/works/<doi>`):

1. The entry printed as "Luo, L. (2019). Analyzing age-period-cohort data: a review and critique. *Annual
   Review of Sociology* 45, 467–492" against `10.1146/annurev-soc-073018-022616`. Crossref returns that DOI
   as **Fosse, E. & Winship, C. (2019)**, same title, journal, volume, pages and year. The first author is
   wrong and the second is omitted. Cite it as **Fosse & Winship (2019)**; the proposition it is cited for in
   §3 and §4.2 (bounds, not point estimates, because every APC point estimate is a normalisation) is
   unaffected.
2. The entry printed as "Mason, K. O., Mason, W. M., **Winship, C.**, & Poole, W. K. (1973)" against
   `10.2307/2094398`. Crossref returns the third author as **Winsborough, H. H.** Titles, journal, volume and
   pages are right; the surname is wrong.

Both errors are repeated in `02-a-price-paths.md` and the first is repeated in `03-b-temporal-correctness.md`;
each of those files carries its own dated correction. `03-b`'s Mason entry already has Winsborough correct.

**Consequence.** The diligence claim in §7 is not retracted: the DOIs, titles, journals, volumes and pages
were checked and are right. The author names were not, in two entries out of 35, which is the reason a
reader should treat "checked against Crossref" as a claim about the DOI record rather than about the printed
author list.

---

## CORRECTION R2-1 to R2-4 (2026-11-07T14:00Z) — the four fixture-derived sentences are marked dead where they stand

Appended by the round-2 corrections pass after `records/findings/00-verification-round2.md` §1 item 1 and §2.1.
This pass deletes nothing. Its rule is stated once here and used in every file it touches: **where a reader
would otherwise believe a false sentence mid-argument, the sentence is struck in place and carries a dated
one-line marker pointing at its correction.** The round-1 blocks at the end of this file remain the argument;
the marks in the body are the signpost.

**Marked dead in the body, with the reason.** §4.1 "only 90 of 128 fixture tickets ever sell …" (R2-1); §4.3
item 2 "14 of 128 tickets redeem" (R2-2); §4.3 item 3 "fits 79-of-128 better than a long tail" (R2-3); §4.6
"79-of-128 is an upper bound on the never-*offered* fraction" (R2-4).

**A correction to CORRECTION 1's own count.** That block says the §4.1 sentence "is one of two places in this
file where a `lib/mock/` figure does argumentative work". The count is wrong. There were three such sites — §4.1,
§4.3 item 3 and §4.6 — and that block named only the first, so two survived unnamed; it mentioned §4.3 item 3
in passing as a use it would not withdraw and never reached §4.6 at all. `CORRECTIONS-APPLIED.md` §1 row 1 had a
third count, "the one place". Two documents, two counts, both wrong, and the verification of round 2 found the
discrepancy by reading both. What the round-1 block did establish correctly is the number that matters: **49 of 128 tickets sell, 79 never do, from 90 `sale` rows**.

**No conclusion in this file changes.** The selection argument is class C on Gatzlaff & Haurin (1997) and
Steele & Goy (1997); the cure component is class C on censusing and Boag (1949); the measurement-error
direction is on Bollinger (1996) and Aigner (1973). What is withdrawn is a measured rate, a specification
choice and a bound, each of which had borrowed the authority of a fixture record. It is worth saying plainly
why this matters more than a wrong digit: on the record this programme actually holds, **the number of tickets
that have ever sold is zero**, because no real ledger exists. A fixture fraction stated as a selection rate
does not overstate a measurement, it manufactures one.

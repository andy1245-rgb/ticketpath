# Phase 1-C — Which methods from other fields genuinely buy something here

**Status:** complete (first pass), written incrementally. **Written:** 2026-11-07T10:57Z; last section
appended 2026-11-07T11:09Z. **Author:** `p1-methods` (research agent, tier `default`).
**Scope:** programme §3 Phase 1 domain 4 (mathematical opportunity discovery): revenue management,
survival analysis, hedonic pricing, auction theory, online learning, Bayesian partial pooling,
conformal prediction, stochastic control. Research-ledger question **P1.C**.
**Depends on:** `RESEARCH-PROGRAM.md` §3 Phase 1, §4.2–4.9; `records/README.md` (evidence classes);
`records/00-data-situation.md` (the observation set); `records/F-decision-log.md` (D1–D4, Q1–Q3);
`records/findings/01-b-identifiability.md` (the ledger T1–T6 and §6 design consequences);
`records/findings/01-a-market-structure.md` (the empirical anchors); the wire contract
`../ticketing-frontend/lib/types.ts` and `API_CONTRACT.md`, re-read for the tier and cap
fields because two claims in this report turn on their exact level of aggregation.
**Append-only.** Disagreements with earlier findings are in §1.4, not resolved silently.

---

## 1. What I concluded

Three of the eight families ship code that produces a quantity this observation set actually identifies.
Two ship the *decision structure* — a set-valued policy — and no number. Three ship reasons **not** to build
something, which is worth as much as the first group because it stops the programme spending a phase on an
estimator that cannot be fitted. No family converts an unidentifiable target into an identifiable one. That
is the sentence to hold onto: a method is not a substitute for an observation.

The observation set, restated so the arguments below can be checked against it: completed resales with a
custody trail (`issue`/`sale`/`transfer`/`redeem`/`revoke`, each with `fromWallet`, `toWallet`,
`priceLamports`, `markupBps`, `slot`, `occurredAt`), ticket metadata (`faceValueLamports`, `tierId`, `status`,
`transferRestricted`, `issuedAt`, `redeemedAt`), per-tier `totalSupply`/`issuedCount` as a *snapshot with no
timestamp*, an event-level `resalePriceCapBps`, and nothing else. No asks, no listing start or stop, no seat
coordinates, no bid side, no fee field, no record of who chose the primary price or by what rule.

### 1.1 The matrix

Columns are the subproblems the engine actually has, with the identifiability-ledger row each answers to.
`●` = produces an identified quantity now. `◐` = produces something useful only under a stated assumption,
or only for part of the target. `○` = produces nothing, and the reason is given in the family section.

| Family | S1 value level<br>(T1, T1′) | S2 price path<br>(T2) | S3 sale prob vs price<br>(T3) | S4 attribute prices (T4a)<br>/ demand (T4b) | S5 primary optimum<br>(T5) | S6 uncertainty<br>(T6) |
|---|---|---|---|---|---|---|
| 2 Revenue management | ○ | ◐ policy shape | ○ | ◐ from the sell-through bracket | ● set-valued | ○ |
| 3 Survival / event history | ○ | ◐ sampling, not shape | ◐ unconditional only | ○ | ○ | ● sale indicator |
| 4 Hedonic (+ repeat sales) | ◐ ratios only | ◐ curvature, not linear trend | ○ | ● T4a / ○ T4b | ◐ | ○ |
| 5 Auction theory | ○ | ○ | ○ | ○ | ◐ prescriptive fork only | ○ |
| 6 Online learning | ○ | ○ | ○ | ○ | ○ | ◐ evaluation discipline |
| 7 Bayesian partial pooling | ◐ pooled mean for cold start | ○ | ○ | ◐ tier effects | ○ | ◐ honest width |
| 8 Conformal prediction | ○ | ○ | ○ | ○ | ○ | ◐ states the data requirement; cannot run |
| 9 Stochastic control | ○ | ◐ state law shape | ○ | ○ | ● set-valued, with risk | ○ |

Read down the S1 column and then the S3 column, and the shape of the whole programme is visible: the
engine's *value* estimate is obtainable as ratios plus a pooled level, and its *price response* is obtainable
from nothing in this document. Every method family that looks like a way around that — online learning,
conformal prediction, auction inversion — is examined below and fails, each for a different reason, and the
reasons are worth keeping.

### 1.2 The five adversarial questions, resolved

**(a) Does revenue management apply when inventory is one ticket and there is no rebooking?** The premise is
wrong in the half that matters and right in the half that does not. The *primary* decision is not a
single-ticket decision: `TicketTier` carries `faceValueLamports`, `totalSupply` and `issuedCount`, so the
organiser sets one price for a stock of *n* units — exactly the
[Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999) setting, whose abstract names "seats on
airline flights … and rooms in hotels that become worthless if not sold by a specific time". The single-ticket
framing is the *reseller's* problem, and the platform does not set the reseller's price. What genuinely does
not transfer is the boundary condition: RM assumes the stock is worthless at the deadline (`V(T,n)=0`), and
01-b §4.2 is right that a ticket's terminal payoff is an unobserved *use value*, so `V(T,n)=n·u` with `u>0`
for any owner who might attend. That single scalar decides the endgame — dump or withdraw — and it is testable
with one of the four requested fields (`delistReason = withdrawn`). §2.3.

**(b) Does survival analysis add anything once the sale hazard is not identified without exposure?** Yes, but
only by changing the target, and the change is worth more than the price curve would have been. 01-b is
correct that `λ(t | p)` is not identified from transactions; it is also correct that the *unconditional*
intensity is, because the ticket population is censused. Survival analysis is what turns "the population is
censused" into estimators: right-censoring at redemption and event end, the competing-risks split (redeem is
not censoring), a cure component for never-sellers, and — the piece nobody has published — the *gap-time*
distribution between custody hops, which this ledger measures directly and which 01-a §5 records as a genuine
gap in the literature. So: it adds the timing and the never-seller structure now, and it adds the price
response only once the four fields exist, in which case the estimator is a discrete-time competing-risks hazard
on a listing risk set (§3.5). One further warning, the most important sentence in that section: even with the
four fields, the fitted object is the hazard *given the ask*, and the ask is chosen by the seller, so it is
still not `E[sale | we set p]`. Prediction under the observed ask policy, yes. A demand curve, no.

**(c) Does conformal prediction help calibrate intervals with no calibration set?** No, and not marginally:
conformal *is* a procedure that consumes a calibration set, so with none there is no interval to compute. The
sharper problem is that the only calibration set this market can supply is drawn from *sold* tickets, and a
conformal guarantee requires the calibration and test points to be exchangeable; a scoring observation
conditioned on "this ticket sold" is not exchangeable with a test ticket that may not sell. The guarantee is
void, and the literature says exactly why
([Barber, Candès, Ramdas & Tibshirani 2023](https://doi.org/10.1214/23-AOS2276)). What conformal buys is
vocabulary and a data requirement: it states precisely how many exchangeable points per stratum would be
needed and which assumption is being violated. That is worth having and it is not an estimator (§8).

**(d) Does Bayesian partial pooling buy the cold-start event, and what exactly does pooling require?** It buys
the only honest thing a cold-start event can be given — a predictive distribution centred on a pooled mean
whose width includes the between-event variance — and it buys nothing about identification. With one group it
degenerates to the prior. Pooling requires four things, all declared rather than observed: an exchangeability
partition (which events are draws from one population); enough groups per stratum that the between-event
variance is not prior-dominated; a within-group likelihood that matches how the data are observed (here
*censored* at the cap); and a choice of which parameter pools — dispersion is far more poolable than location.
§7.3, including the technical reason τ² is the weak link.

**(e) Does any online-learning method have a feedback loop it can close?** No, and the reason is arithmetic
rather than statistical, which makes it decisive. The action is the primary price; the observed secondary
record is a function of that same price, because the resale ceiling is
`faceValueLamports × (1 + resalePriceCapBps/10⁴)`. Raising the primary price raises the ceiling proportionally,
so the observed markup distribution moves as a direct consequence of the action whenever the cap binds — and
the cap binds precisely on the events where the pricing decision matters. On top of that, the reward
(`issuedCount` versus `totalSupply`) is a snapshot with no timestamp, so the reward cannot be attributed to a
decision time, and no propensity or pricing rule is logged, so off-policy evaluation is not hard — it is
*undefined* ([Dudík, Erhan, Langford & Li 2014](https://doi.org/10.1214/14-sts500) state the requirement:
logged contexts, actions, rewards *and* action probabilities). The one admissible use is a bandit over
*models*, scored on predictive accuracy, where no money is at risk. §6.

### 1.3 What I would build, in order

1. **A censored hedonic price model** — log markup on tier, event and time-to-event, with the cap entering as
   a known, event-specific truncation point. It is the engine's headline output, the one component whose
   coefficients are identified up to 01-b's affine normalisation, it needs none of the four missing fields, and
   it is about 150 lines of stdlib Python. §4.6, §11.
2. **The repeat-sales index as its independent check.** Different identifying variation, no distributional
   assumption; where the two disagree, the disagreement is the diagnostic for composition bias. §4.5.
3. **The discrete-time competing-risks hazard with a cure component** on the censused population — the sale
   indicator, the never-seller fraction and the gap-time distribution. §3.5.
4. **A hierarchical layer** over (sale ⊂ tier ⊂ event ⊂ category), so thin cells produce an interval instead of
   a point. §7.5.
5. **A reserve-price surface** on a small discrete state space for the primary decision, reported as a set over
   the parameter box, with CVaR computed on the profit distribution. §9.5.

Nothing above position 2 needs an external field. Everything from position 3 onwards needs the operator's four
fields, or money, or both.

### 1.4 Where this disagrees with earlier findings

Recorded, not resolved.

1. **01-b ~~§4.4(ii)~~ §5.3 overstates the cap as an instrument.** **[CORRECTION 2026-11-07T14:00Z, R2-8 —
   attribution corrected: the sentence quoted in this item is §5.3 item 3's. `01-b` §4.4(ii) says the
   opposite — "Because the cap is bps over *each tier's own* face, its **absolute level** differs across tiers
   within one event" — and is already correct. The criticism survives the correction as stated and loses no
   force: it turns on the wire contract, not on which section of `01-b` got it wrong, and §5.3 is the section
   that awards the cap identifying variation. No conclusion below changes; §4.4(ii) needs no correction.]** It says `resalePriceCapBps` "varies … across tiers
   within an event because it is bps over each tier's own face". The *absolute* ceiling does differ across
   tiers, but the bps does not: `resalePriceCapBps` is a single field on `Event`, not on `TicketTier`, and the
   cross-tier variation is exactly proportional to face value, so it carries no independent information. There
   is **no within-event identifying variation in the cap**; the instrument is a *cross-event* one, and it is
   therefore confounded with everything else that varies across events. That weakens the instrument behind
   01-b's one-sided bounds. It does not destroy it — cross-event bps variation is real and observed — but the
   bounds should be reported with that confound named. Checkable in ten seconds against `types.ts`; fold into
   `C-variable-registry.md`. `C-variable-registry.md` C-3 does and cites `01-b` §5, correctly;
   `D-model-registry.md` C6 carries this item's wrong section number and was corrected with it on
   2026-11-07T14:00Z.
2. **01-b §4.3 says the missing observation is "the ask, not the exposure"; for a hazard model the exposure is
   the binding object.** The four fields deliver both at once, which is why they are one request, so nothing
   operational changes. What changes is the estimator: without `listedAt`/`delistedAt` there is no risk set,
   and a hazard is defined on a risk set. An ask with no interval is a covariate with no denominator.
3. **`issuedCount` is a temporal-correctness hazard that neither earlier finding names.** It is a snapshot with
   no capture time, so using it as a predictor at time *t* is look-ahead bias unless the snapshot's timestamp is
   recorded. Same for `Event.status` — `sold_out` arrives at an unrecorded moment. Any model with a sell-through
   covariate must either get a timestamped series (Gap 5) or restrict itself to the value at prediction time,
   which the contract cannot identify. §3.6.
4. **A cheap test that settles whether the primary price is dynamic at all.** `faceValueLamports` is carried per
   *ticket*, while the tier price is a tier-level concept. If the organiser revises the primary price mid-sale,
   tickets in one tier will carry different `faceValueLamports`. If, on the first real dump, within-tier face
   value is constant, the primary price is static per tier and the entire dynamic-primary-pricing question
   (Phase 5's "dynamic pricing policy, if justified") collapses to a single static optimisation. No new field
   needed. Recorded in §12 as an open question with its test.

---

## 2. Family 1 — Revenue management and yield management

**Estimates.** A policy, not a parameter: a price schedule over the remaining horizon, or equivalently a
reserve intensity, that maximises expected revenue from a fixed stock of perishable units over a finite
horizon. The intermediate object is the value function `V(t, n)` — expected revenue from `n` units with `t`
time left. The multiproduct form
([Gallego & van Ryzin 1997](https://doi.org/10.1287/opre.45.1.24)) extends it to jointly set prices on
substitutable products, which is the right frame for tiers, since tiers do not share capacity but do
substitute in demand.

**Targets.** T5 first, T4b as its input. T5 is set-identified (01-b §3), so what RM produces under this
observation set is a *family* of policies indexed by the unknown demand function — not a number. T4b is not
identified from secondary trades; the identified piece is the primary sell-through bracket of 01-b §4.4(i).

**Assumptions, and which ones fail here.**

| # | Assumption | Holds? |
|---|---|---|
| 1 | Perishable stock, fixed quantity, finite horizon, zero salvage | Holds except the salvage value — see §2.3 |
| 2 | Demand is a point process whose intensity depends on current price and time | Formally holds; the intensity is not estimable here (T3, T4b) |
| 3 | Buyers are myopic about the seller's future prices | **Fails.** The resale market makes every buyer an intertemporal arbitrageur — §2.4 |
| 4 | One seller sets prices; no strategic interaction between primary sellers | Holds on the primary side (one organiser per tier); false on the secondary side, which we do not price |
| 5 | Units within a price class are homogeneous | Holds *in the platform's own data model*: `Ticket` has `serial` and no section/row/seat, so the platform sells a seatless token. If the venue assigns seats, that heterogeneity is invisible to both the platform and us (01-b Gap 3), which is an operator question, not a modelling one |
| 6 | No rebooking, no cancellations, no overbooking | **Holds, and deletes a sub-literature** — §10.1 |

**Data.** The *structure* needs none of the four listing fields. The *parameters* need them: a price-response
intensity is T3 and is unidentifiable without `listPriceLamports`, `listedAt`, `delistedAt`, `delistReason`. The
booking curve needs a primary inventory time series, which is Gap 5 and is **not** among the four fields — a
point worth flagging, because RM's demand side is blocked by a data gap the programme has not yet requested.
The boundary-condition test in §2.3 needs only `delistReason`, one of the four.

**Implementation (D2).** Yes, pure stdlib, and small. Backward induction on `V(t, n)` over a
`(T+1) × (N+1) × |P|` grid is `O(T · N · |P|)`; with 60 daily steps, 2,000 units and 41 price points that is
roughly 4.9 million inner operations — seconds, not minutes, in CPython. The grid can be cut hard by restricting
prices to a log-spaced band around the tier's face value, because the decision that matters is a percentage
markup over face, not an absolute price. The multiproduct version must **not** be done as a
full DP (it is `O(T · N₁ · N₂ · |P|²)` and explodes); use the fluid/deterministic relaxation, which is an ODE
solvable with Euler or RK4 in a dozen lines, and treat the stochastic DP as the check on the fluid answer.

**Evidence class.** **C** for the method — it is established operations research, true by construction.
**D** for the transfer to ticket primary pricing at event scale, and I will not soften that: 01-a §4 records
that no peer-reviewed measurement of Ticketmaster-style dynamic primary pricing's revenue or sell-through
effect on a large sample exists. I did not read an airline or hotel revenue-lift study during this pass, so I
quote no lift figure (§4.6). 

**Primary source.** [Gallego & van Ryzin (1994), *Management Science* 40(8):999–1020](https://doi.org/10.1287/mnsc.40.8.999);
multiproduct extension [Gallego & van Ryzin (1997), *Operations Research* 45(1):24–41](https://doi.org/10.1287/opre.45.1.24);
survey [Bitran & Caldentey (2003), *M&SOM* 5(3):203–229](https://doi.org/10.1287/msom.5.3.203.16031);
book [Talluri & van Ryzin (2004)](https://doi.org/10.1007/b139000).

### 2.1 The two results that survive an unidentified demand function

RM's usual selling point is the DP, and the DP is worthless here without a demand intensity. But two of its
results are *ordinal* and therefore survive:

1. **Monotonicity.** The optimal intensity, hence price, is monotone in the stock level and in the remaining
   horizon (Gallego & van Ryzin 1994, abstract: "structural monotonicity results for the optimal intensity
   (resp., price) as a function of the stock level and the length of the horizon"). A comparative static of
   that kind is robust to the functional form, which matters precisely because the functional form is what we
   cannot estimate. A set-identified problem can carry an ordinal result; it cannot carry a point optimum.
   That is the single best argument for using this family at all.
2. **Fixed prices are asymptotically optimal.** The same paper proves, in its own words, that "simple, fixed
   price policies are asymptotically optimal as the volume of expected sales tends to infinity". This is a
   licence to build the static price first and to make dynamism justify itself, and it is the cheapest
   argument in this report for keeping the architecture small (programme §4.9). It is *not* a licence to
   dismiss dynamics at our scale: the asymptotics is in expected sales volume, and 01-a §5 puts resale at
   about 5% of tickets with the mean carried by a few hot events, so most events are nowhere near the limit.
   Read it as "the burden of proof is on dynamism", not as "dynamism is worthless". **Class C, UNVALIDATED at
   event scale.**

### 2.2 Where the transfer actually breaks: the boundary condition

This is the sharpest thing in the section and it is not in 01-a or 01-b. The RM formulation carries a terminal
condition `V(T, n) = 0` — the stock is worthless at the deadline, which is exactly why the classical policy
dumps inventory late. For a ticket that condition is false: the terminal payoff is the owner's *use value* of
attending, `V(T, n) = n·u` with `u ≥ 0`, and `u` is unobserved. Three consequences follow, each with a build
implication.

1. **The endgame is a withdrawal decision, not a dump decision.** With `u > 0` the seller has a reservation
   value and will withdraw rather than clear the market. A policy fitted under `V(T,n)=0` will systematically
   underprice the last days.
2. **The last observed price is a selected statistic.** Low last prices can mean "no demand" or "the owner is
   going to the show". Without `delistReason` these are observationally identical, which is the fourth field's
   second job (its first is the sale hazard).
3. **`u` is not a scalar, and both masses are observable.** [Sweeting (2012)](https://doi.org/10.1086/669254),
   class A per 01-a §2, finds sellers
   cutting prices by 40% of face or more as the deadline approaches, and 01-a §2 reads that as sellers whose value
   of holding is near zero — they cannot attend, and unsold inventory is worthless to them. The other mass is
   directly observable in the contract: a ticket whose `redeem` row has `toWallet` equal to its `issuedToWallet`
   was attended by the person it was issued to, which is a lower bound on the fraction with `u > 0`. So `u` is
   **heterogeneous** — mass at zero (professional and non-attending sellers) and mass above zero (attenders) —
   and the model has to carry a distribution over it rather than a scalar. That distribution *is* the endgame
   behaviour. **Class A for the heterogeneity (Sweeting plus the redemption record), C for the mechanism, D for
   any shape.**

The test, once `delistReason` exists: if withdrawals cluster near the event at prices below the prevailing
market, `u > 0` and the dump policy is wrong for a subset of sellers. Until then, the boundary condition is a
parameter to be swept, not assumed.

### 2.3 Strategic buyers: the resale market breaks the myopia assumption

RM assumes the buyer does not condition on the seller's future prices. Here the buyer has a *better* option
than waiting for the seller: wait for the resale market, which is a second price-setting institution with a
ceiling imposed by policy. Two results carry over. [Su (2007)](https://doi.org/10.1287/mnsc.1060.0667) shows that
with heterogeneity in both valuation and
patience, the optimal policy is markdown pricing when high-value customers are less patient, and that the
structure of the optimum depends on the *joint* distribution of valuation and patience.
[Aviv & Pazgal (2008)](https://doi.org/10.1287/msom.1070.0183)
set the strategic case against a myopic benchmark and quantify the impact with a numerical study. Neither
distribution is observable here. So this section delivers a *sign* and not a magnitude: ignoring strategic buyers
overstates the optimal primary price, because the myopic model does not credit the buyer's option to wait. Given
that 01-a sizes the whole prize at 1.4–3.4% of primary revenue, an upward bias of unknown size on a small prize is
a live risk, and the honest treatment is to use the RM optimum as an **upper bound** and the primary sell-through
bracket as the lower anchor. **Class C, with the sign argument class B** (the mechanism is documented in
perishable-goods research, not measured on ticket primary pricing).

### 2.4 Verdict

RM buys the *shape* of the primary decision and a comparative-statics discipline, at zero cost in missing data,
and it buys nothing you can print as a price. It is the right frame for the optimiser and the wrong frame for
the estimator. Build order: after the value model (§4) and the hazard (§3), because it consumes both. The
feedback between primary price and resale price — which is genuinely new here and is Phase 3's subject — breaks
RM's single-agent assumption outright and is handled in §9.3, not here.

---

## 3. Family 2 — Survival analysis and event history

**Estimates.** Four objects, and the family should be judged on which one is asked for:
(i) the hazard `λ(t | x)` — the instantaneous rate of a resale at time `t` given covariates, and with it the
survival function `S(t)` and the cumulative incidence; (ii) the *subdistribution* in the presence of competing
events; (iii) the cure fraction, i.e. the probability a ticket is never offered at all; (iv) in recurrent-event
form, the gap-time distribution between successive custody hops, which is a statement about holding duration
and repeat-reseller behaviour rather than about selling.

**Targets.** T3 is the basis of the family and its price response is **not identified** (01-b §4.3): the
observed rate is `λ(t|p) · π(p | listed, t) · s(t)` and nothing separates the three factors when the mark is
recorded only on the success branch. The unconditional intensity *is* identified, because the ticket
population is censused. So the honest entry in the matrix is ◐: survival analysis buys the sale-probability
*denominator*, the competing-risk structure, the never-sellers and the timing, and it buys nothing about price.
It also carries T6 for the sale indicator, because the population is complete and proper scoring rules apply
(§3.8).

**Assumptions, and which ones fail here.**

| # | Assumption | Status |
|---|---|---|
| 1 | Censoring is independent of the failure process | **Fails.** Redemption and event end are the censoring times and both correlate with demand — 01-b §4.2(a), [Lagakos 1979](https://doi.org/10.2307/2529941) |
| 2 | Proportional hazards (Cox) | Checkable, not assumed: Schoenfeld residuals are a few lines of stdlib code. Available, so use it |
| 3 | No unobserved heterogeneity | **Fails at the event level.** Fix is a shared frailty; §3.5(d), and [Hougaard 1995](https://doi.org/10.1007/BF00985760) |
| 4 | The time index is correct | **Fails as the schema stands.** `occurredAt` is ISO-8601 at unspecified granularity while `slot` is strictly monotone — §3.4 |
| 5 | Units enter the risk set at a well-defined moment | Holds at ticket level (`issuedAt`) and, with the four fields, at listing level (`listedAt`) |

**Data.** Two regimes, and the difference is exactly the four fields.

- *Without them*, the ledger plus `issuedAt`/`redeemedAt`/`slot` gives a complete right-censored,
  recurrent-event, competing-risks dataset over the whole ticket population. That is a real dataset by the
  standards of this literature, and it contains no price.
- *With them*, the risk set becomes listing intervals and a price becomes a covariate. Nothing else is needed
  for a full hazard model; the fee model and seat coordinates are irrelevant to it.

**Implementation (D2).** Yes, completely, and this is the most comfortably stdlib family in the report.
Kaplan–Meier and Nelson–Aalen are cumulative products and sums. A piecewise-exponential MLE is Newton–Raphson
on a log-linear hazard with a handful of parameters. Cox's partial likelihood with Breslow or Efron ties is a
`k × k` Newton iteration. Schoenfeld residuals are a by-product. Fine–Gray needs inverse-probability-of-censoring
weights on the risk set and is implementable in about sixty lines, but it should be validated against a
simulated competing-risks dataset before it is trusted, and I mark it *implementable with care* rather than
routine. Nothing in the family needs a numerical library.

**Evidence class.** **C** — established statistical methodology, true by construction, and the estimator
properties are standard. The empirical claim that it describes ticket resale timing is **D/UNVALIDATED**: no
one has published a hazard model of a ticket ledger, which is the opportunity.

**Primary source.** [Cox (1972), *JRSS-B* 34(2):187–202](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x);
counting-process formulation [Andersen & Gill (1982), *Ann. Statist.* 10(4):1100–1120](https://doi.org/10.1214/aos/1176345976);
discrete time [Allison (1982), *Sociological Methodology* 13:61–98](https://doi.org/10.2307/270718);
competing risks [Fine & Gray (1999), *JASA* 94(446):496–509](https://doi.org/10.1080/01621459.1999.10474144);
cure [Boag (1949), *JRSS-B* 11(1):15–44](https://doi.org/10.1111/j.2517-6161.1949.tb00020.x);
case-cohort [Prentice (1986), *Biometrika* 73(1):1–11](https://doi.org/10.1093/biomet/73.1.1);
text [Fleming & Harrington (2005)](https://doi.org/10.1002/9781118150672).

### 3.1 The pricing objection, answered honestly

The question is whether survival analysis adds anything once the sale hazard is admitted to be unidentified
without exposure. It adds exactly four things, and the fourth is the one I would defend hardest.

1. **The denominator.** Even the unconditional sale rate needs a risk set with right-censoring handled; the
   population is censused but lives end at redemption or event end, on different dates, for reasons correlated
   with demand. A raw sold-out-of-issued ratio gets that wrong.
2. **The competing-risks split.** Sale, unpriced transfer, redemption and revocation are four competing events,
   not one event with three kinds of censoring. Treating redemption as censoring inflates the sale hazard,
   because a ticket redeemed by the wallet it was issued to is a ticket somebody wanted — attendance and
   resale are substitutes, so their latent demand is *negatively* correlated. That negative correlation is the
   whole reason the split matters, and it is a fact the contract can show directly: `redeem` rows carry
   `toWallet`, and `issuedToWallet` is on the ticket.
3. **The never-sellers.** The right model for a ticket that is never offered is a *cure* — a point mass at
   "never returned to market in the window" — not an infinitely long duration. Cure is not "worth nothing": an
   owner who attends is a non-seller. 01-a §5 puts resale at about 5% of tickets (class A, two independent
   measurements), so the cure fraction is the dominant mass and a model that forces every ticket into a
   positive hazard is misspecified for most of the population. Estimating a cure fraction requires a censused
   population, which is exactly what we have.
4. **The gap-time distribution.** Time between custody hops, holding duration, whether a repeat reseller
   reappears — computable directly from consecutive `occurredAt`/`slot` values on the same mint, censused at
   redemption. 01-a §5 records that **no published distribution of holding duration or transfers per ticket
exists**, and that this is precisely what an on-chain ledger measures better than any dataset in the literature.
   That makes it the only place in this whole report where the observation set is *better* than the published
   data, and it is a survival estimand. **Class D today, class A available the day there is a ledger.**

There is a fifth contribution that is less obvious and belongs to T2 rather than T3. The price path is observed at
the moments tickets happen to trade, which is a *sampling process*, not a fixed grid — 01-b §4.2's
nonsynchronous-trading problem. Any estimate of the path from a handful of irregular observations inherits the
bias of its sampling scheme, and a hazard model of the observation times is the standard correction
(the counting-process view, [Andersen & Gill 1982](https://doi.org/10.1214/aos/1176345976)). So survival analysis
contributes to the price path by modelling *when* prices are seen, while contributing nothing to *what* they are.

### 3.2 What is identified today, stated as a buildable list

Per ticket `i`, with `t` measured from `issuedAt`: the intensity of a first sale as a function of covariates
known at issue — `faceValueLamports`, `resalePriceCapBps`, tier size, event category, city, organiser,
`requiresVerifiedWallet`, `transferRestricted` — with right-censoring at `min(redeemedAt, event endsAt)`, the
four-way competing-risks split, a cure component, and the gap-time distribution for tickets that trade more
than once. All of it is estimable on the current contract. None of it needs a price, and none of it can answer
a question about a price.

### 3.3 The trap: the only price in the record is an outcome

`markupBps` exists only on `sale` rows. A hazard model built with it conditions on the event being modelled —
and it will report a strong, significant, entirely tautological "price effect on sales", because a sale *is*
recorded by its price. This failure is worth naming loudly because it is the shape of mistake that survives
review: the model converges, the coefficient is large, and the whole thing is an artefact of the recording
rule. The honest statement is that the contract contains **no** pre-sale price covariate — only
`faceValueLamports` (fixed at issue) and the event-level `resalePriceCapBps` (the ceiling). That is 01-b's T3
result restated as an engineering constraint: there is nothing to regress on. **Class C.**

### 3.4 The clock, which is a small point with a large failure mode

`occurredAt` is an ISO-8601 string at unspecified granularity and `slot` is strictly monotone. Any duration
derived from `occurredAt` alone can come out zero or negative for two genuinely ordered events, and a hazard
model with negative durations does not fail loudly — it silently drops or reverses intervals. The rule is
01-b §4.6(c), and this section only adds the consequence: **the discrete-time formulation is forced.** Coarse
and unequal timestamps are exactly the situation
[Allison's grouped-data hazard](https://doi.org/10.2307/270718) was built for, it needs no assumption about the
precise event time within a bucket, and it is a GLM, so it is the cheapest thing to fit in stdlib. Cox is the
check, not the primary estimator.

### 3.5 The estimator that follows once the four fields exist

Written out, because "a survival model" is not a specification.

- **Unit.** A listing event `ℓ` on ticket `i`, occupying the half-open interval `(listedAt, delistedAt]`,
  truncated at `min(redemption_i, event end)`. Tickets can contribute several intervals; that is a
  recurrent-event structure and it is the correct one, not a defect.
- **Event types.** `j ∈ {sold, cap_blocked, withdrawn, expired}` with `sold` the event of interest and the rest
  competing. `cap_blocked` is the most valuable of the three: it is an *attempt to sell at the ceiling that
  failed*, which is the observably recorded form of excess demand at the cap, and 01-a §3 argues the mass
  point's height measures rationing rather than value. This is where that measurement becomes possible.
- **Linear predictor.** `η_ℓ = β₀ + β₁·log(ask_ℓ / face_i) + β₂·(cap_bps / 10⁴) + β₃·f(time to event) + β₄·X_i`
  with `X_i` the ticket and event covariates known at `listedAt`. `β₁` is the quantity the whole programme
  wants and the one the endogeneity of ask contaminates.
- **Likelihood.** Complementary log-log discrete-time hazard with a step-function baseline in time-to-event
  buckets (weekly far out, daily inside the last week). Newton–Raphson, ~15 parameters, `(k×k)` Hessian.
- **Cure.** Two-part: `Pr(ticket is ever listed)` from a logistic on ticket covariates, times the hazard among
  listers. The first part is identified on the full population and is a legitimate deliverable on its own.
- **Frailty.** A shared random effect per event, gamma (conjugate) or lognormal (needs quadrature). This is
  the same object as the partial pooling in §7 and should be built once, not twice.
- **What it still is not.** `β₁` is the hazard *given the ask the seller chose*. It is a prediction model
  under the observed ask policy. It is not `E[sale | we set p]`, because the ask carries the seller's private
  information about value — 01-b's Working (1927) point. Reporting the first as the second is the error this
  section exists to prevent. **Class C.**

### 3.6 Temporal correctness: `issuedCount` is a trap

`issuedCount` and `Event.status` are snapshots with no capture time, so a model that uses "fraction sold" as a
covariate at time `t` is using information from after `t`. Either the operator supplies a timestamped inventory
series (Gap 5), or the covariate is restricted to its value at prediction time — which the contract cannot
identify. Until then, sell-through may enter only as an *ex post* descriptive statistic, never as a predictor.
**Class C, and unambiguously a §4.8 violation if ignored.**

### 3.7 What is still not identified, and the one design that fixes it

Even with the four fields, the *counterfactual* price response needs ask variation that is exogenous to value.
Three routes, in descending order of strength: (i) a randomised ask arm on a subset of listings — a money and
commercial decision, therefore the operator's, not ours; (ii) `resalePriceCapBps = null` events as a
comparison group against capped events with a dose-response in `cap_bps`, which is free and is the natural
quasi-experiment sitting in the schema already, confounded with whatever else differs between capped and
uncapped events; (iii) nothing else — an instrument would have to move the ask without moving value, and I
cannot name one in this market. **Class D, and route (ii) is the only one available without money.**

### 3.8 Verdict

Survival analysis is the second thing to build and the first thing that produces a genuinely new empirical
object (the gap-time and never-seller structure). It does not touch price. Its documented prerequisites are one
clock rule (`slot`), one data request (the four fields), and one refusal (never put `markupBps` on the
right-hand side).

---

## 4. Family 3 — Hedonic pricing, and its repeat-sales form

**Estimates.** The equilibrium price locus: the function `p(x, τ)` mapping a ticket's attributes `x` and the
time to the event `τ` to the price at which a ticket trades. Not marginal willingness to pay, and not a demand
curve. Its differenced form — the repeat-sales estimator of
[Bailey, Muth & Nourse 1963](https://doi.org/10.1080/01621459.1963.10480679) — estimates an index of price
*changes* in which each ticket's own quality cancels out.

**Targets.** T4a directly; T1 only as ratios, because a hedonic fitted to one market is identified only up to
an affine transformation ([Ekeland, Heckman & Nesheim 2004](https://doi.org/10.1086/379947)), which is the same
statement as 01-b's missing price anchor; T2 for the curvature. It does **not** reach T4b: Rosen's second stage
does not separate demand from supply using a single market's transactions, and 01-b §4.4 says so. It does not
reach T1′ — a cold-start event has no attributes to price.

**Assumptions, and which ones fail here.**

| # | Assumption | Status |
|---|---|---|
| 1 | The observed price clears the market — price-taking, no bargaining | **Fails under a binding cap** (truncation) and under bargaining (interval-identified, 01-b §2b) |
| 2 | Implicit attribute prices are constant over the estimation window | **Fails by construction for τ**, which is the purpose of the model. Handled by making τ a state (§4.4), not by assuming it away |
| 3 | Traded units are representative of the population | **Fails.** Resold tickets are better seats (mean seat-quality percentile 0.61 vs 0.50, class A via 01-a §6), so the locus describes the *tradable* subpopulation only |
| 4 | Quality is unchanged between two sales of the same unit | **Holds exactly, and this is the family's free lunch** — a ticket's attributes are fixed at mint. No renovation, no depreciation, no change in specification |
| 5 | The latent price index is normal (censored version only) | Does real work and is **untestable inside the censored region**. Mitigated by transforming to log(price/face) — §4.3 |

**Data.** The *cross-sectional* hedonic wants seat coordinates and does not get them (Gap 3), which is the
sharpest data limitation in the whole programme because seat quality is the dominant within-event price axis
(01-a §6). The *censored* version and the *repeat-sales* version need nothing beyond the current contract —
§4.2 and §4.3. Correcting for selection into trading needs listing exposure (the four fields), because without
asks the price at which an unsold ticket was offered is unobserved.

**Implementation (D2).** Yes, comfortably, and this is the family I would build first.
Ordinary least squares by normal equations or Householder QR on a design matrix of order 10³ × 20 is trivial
in pure Python. The censored version is best fitted by **EM**, not Newton–Raphson: the E-step replaces each
censored observation with its conditional expectation using the inverse Mills ratio, and the M-step is plain
least squares. Every ingredient is in the standard library — `statistics.NormalDist` exposes `cdf`, `pdf`,
`inv_cdf` and `quantiles` in Python 3.12 (checked on this machine), and the normal pdf is one `math.exp` away.
That is roughly 120 lines, converges monotonically, and avoids the badly conditioned Newton step that the
censored-normal likelihood produces when the censoring fraction is high — which it will be on tightly capped
events.

**Evidence class.** **C** for the method. **A** for the proposition that seat quality is the dominant
within-event price axis and that resale prices vary seat by seat (01-a §6, from the published ticket studies).
**B** for treating a policy ceiling as a known censoring bound — Tobit-type structure is standard, the ticket
application is new. **D** for the claim that a ticket's hedonic surface is stable enough over an event's life
for the coefficients to be usable out of sample; nothing has tested that.

**Primary sources.** [Rosen (1974), *JPE* 82(1):34–55](https://doi.org/10.1086/260169);
[Bailey, Muth & Nourse (1963), *JASA* 58(304):933–942](https://doi.org/10.1080/01621459.1963.10480679);
[Ekeland, Heckman & Nesheim (2004), *JPE* 112(S1):S60–S109](https://doi.org/10.1086/379947);
[Pakes (2003), *AER* 93(5):1578–1596](https://doi.org/10.1257/000282803322655455);
[Amemiya (1984), *J. Econometrics* 24(1–2):3–61](https://doi.org/10.1016/0304-4076(84)90074-5).

### 4.1 The coefficients are not elasticities, and the distinction is load-bearing

A hedonic coefficient is a price differential along an equilibrium locus. It is a *forecasting* object. The
same data cannot recover the demand curve, for the reasons in 01-b §4.4 and
[Rosen 1974](https://doi.org/10.1086/260169)'s own second-stage argument, sharpened by
[Brown & Rosen 1982](https://doi.org/10.2307/1912614). Every downstream use in this programme therefore has to
respect the difference: a tier coefficient may enter the value forecast and must never enter the optimiser as if
it were a willingness-to-pay derivative. This is the most frequently made error in applied pricing work and the
cheapest one to prevent with a naming convention.

### 4.2 Gap 3 bites the cross-section and not the index

This is the section's central technical claim and it changes the build order.

The missing seat coordinates are fatal to a *cross-sectional* hedonic, because two tickets one row apart are
different goods and the model cannot see the difference. They are harmless to the *repeat-sales* estimator,
and for a reason the real-estate literature does not get to enjoy. The BMN design regresses
`log p_i2 − log p_i1` on a pair of time dummies. Everything about which ticket it is differences out — and for
a ticket, "which ticket it is" is fixed at mint, so the assumption that quality does not change between sales is
not an approximation, it is literally true. Real estate has to worry about renovation, depreciation and
redevelopment; a ticket has none of those. **Per pair, the price ratio is a pure price movement.** *(Class C —
an argument from the schema, not a measurement.)*

Three residual problems remain and they are all *across* pairs, not within them. (i) **Selection:** tickets that
trade twice are not a random sample, and a repeat-sales index inherits that bias —
[Gatzlaff & Haurin 1997](https://doi.org/10.1023/A:1007763816289),
[Steele & Goy 1997](https://doi.org/10.1023/A:1007780219924) on short-hold pairs specifically. Here the
problem is structural rather than incidental: 01-a §5 puts resale at roughly 5% of tickets, so pairs come from
the liquid subset of an already small subset, and the liquid subset is the hot events. (ii) **Composition drift
across the index's time cells:** which tickets trade is correlated with `τ`, so the sample entering each time
cell changes systematically. (iii) **Ageing:** remaining life shrinks monotonically, so the index mixes a
calendar effect with an age effect — 01-b's T2, and unavoidable (§4.4).

[Pakes 2003](https://doi.org/10.1257/000282803322655455) supplies the useful warning in the other direction: a
matched-model index is biased when the goods that leave the sample are those whose value has fallen, and a
hedonic on attributes is the correction. The ticket analogue of "leaving the sample" is redemption and expiry,
and the relevant selection is that the last observed price before expiry is not a random draw. So the two
estimators should be run together: the hedonic for the level and the cross-section, the repeat-sales index for
the change, and *disagreement between them is the diagnostic*, not a nuisance.

### 4.3 The cap is a known censoring point, which is the benign case, and it decides a likelihood

01-a §6 recommends fitting a latent markup `M*` observed as `min(M*, cap)` with a leakage probability. That is
censored regression on a bound that is *observed rather than estimated*, and with a bound that varies across
events. Both facts help:

1. **The bound is known**, so there is no incidental estimation of a threshold, and the bound's level carries no
   sampling error into the coefficients.
2. **The bound varies across events** in bps terms, so events with looser caps reveal part of the latent
   distribution's upper region and the pooled likelihood is informative about it. This is a *cross-event*
   instrument only — see the correction in §1.4(1), where I record that 01-b overstates the within-event
   variation, because `resalePriceCapBps` is one number per event and the cross-tier ceiling moves exactly in
   proportion to face value.

Work on `y = log(price / faceValueLamports)`, which makes the cap a *constant upper bound in the same units as
the response*, `log(1 + cap_bps/10⁴)`. The log scale also makes the normality assumption far milder than it
would be on markup in basis points, whose right tail is long by construction.

One consequence worth writing down because it turns an open operator question into a modelling decision: **the
correct likelihood depends on where the cap is enforced**, which is open question Q3 in the decision log. If the
cap is enforced on-chain the transfer reverts, so no sale above the cap is *possible* — that is **truncation**,
and the sample simply has no observations beyond the bound. If the cap is enforced by the platform refusing a
listing, sellers pile up at the ceiling and the latent willingness to pay above it is *censored* — that is a
mass point at the bound. The two give different likelihoods, and they are distinguished empirically by whether
a mass at exactly `cap_bps` exists. So the very first diagnostic on real data answers Q3.

### 4.4 Time-to-event is an attribute, so the hedonic and the price path are one model

For a perishable good, `τ` is not a characteristic of the unit but of the transaction, which makes the hedonic a
*state-dependent* price function `p(x, τ)`. Its derivative in `τ` is the price path. That has two consequences.

First, T2 and T4a are the same object seen twice, and the architecture should reflect it: one component with
`τ` in it, not a hedonic plus a separate forecaster. The forecast at horizon `h` is the same model evaluated
at `τ − h`, which is both smaller and more honest than fitting a time-series model to a series with about one
trade per ticket (01-b §4.2's nonsynchronous-trading point). The alternative — a proper time-series model — is
not rejected in principle, only ranked below on programme §4.9.

Second, the normalisation problem is unavoidable and should be declared rather than hidden. Within one event,
`τ` and calendar time are the same variable up to a constant. Across events with different start dates they
separate, but then age + cohort = period and the linear component is not identified (01-b §4.2, from the APC
literature). The practical resolution, and the one I recommend: **include event effects and a spline in `τ`,
and do not include calendar time.** That is an explicit restriction — no common calendar trend across events
beyond what the event effects absorb — and it is a choice, stated, instead of a collinearity, hidden. The path
is then reported as curvature and deviations from each event's mean, exactly as 01-b §6(1) requires.

### 4.5 The repeat-sales index as an independent check

Small, cheap and worth having. Design: pairs `(i, 1), (i, 2)` on the same `mintAddress`; response
`log p_i2 − log p_i1`; regressors a sparse set of time-cell dummies (monthly at first, since pairs are few);
ticket fixed effects are differenced out and never estimated. Fitted by normal equations in the number of time
cells, which is small. Two disciplines: the index has **no level** (01-b §4.1 — it identifies ratios only), so
it must never be presented as a price; and the pair sample must be described, because the pairs are the liquid
subset. Its job is to disagree informatively with the hedonic's time effects. If the pairs prove too few, the
hybrid route — ticket fixed effects where pairs exist, attribute effects elsewhere — is the standard fallback
([Meese & Wallace 1997](https://doi.org/10.1023/A:1007715917198)).

### 4.6 The specification I would implement first

Written as a specification, because this is the recommendation.

- **Response.** `y = log(priceLamports / faceValueLamports)` on every `sale` row of every ticket in the censused
  population. (Not `markupBps`: the ratio is the primitive and the log is the well-behaved scale.)
- **Latent model.** `y* = μ + α_tier + δ_event + s(τ) + γ'X + ε`, `ε ~ N(0, σ²)`, with `s(·)` a piecewise-linear
  spline in days-to-event with knots concentrated inside the final fortnight, and `X` the attributes fixed at
  issue: `transferRestricted`, `requiresVerifiedWallet`, tier size, event category, city.
- **Observation rule.** `y = y*` when `y* ≤ c_event = log(1 + resalePriceCapBps/10⁴)`; a point mass at
  `c_event` when the cap binds (censored regime) or no observation at all beyond `c_event` (truncated regime),
  according to Q3 and to the diagnostic in §4.3.
- **Estimation.** EM. E-step: replace capped observations by `E[y* | y* > c] = μ̂ + σ̂·λ((c − μ̂)/σ̂)` with `λ`
  the inverse Mills ratio; M-step: least squares. Iterate to a tolerance on the log-likelihood. No matrix
  library, no line search, no tuning.
- **What it produces.** A predicted value for *every* ticket including never-traded ones — which is the
  engine's headline output and something neither the repeat-sales index nor the hazard can give. Plus a residual
  distribution that is the natural input to the interval in §8 and the value signal for §9.
- **What it does not produce.** A level in currency that anyone should believe. The `δ_event` and `α_tier`
  coefficients are identified relative to a normalisation; the affine indeterminacy of §4.1 is not removable
  from this data, so the output is a *quality-adjusted relative price* and the anchor question is the operator's.

### 4.7 Verdict

Hedonic pricing is the family that pays. It is the only one that delivers a number for a ticket nobody has ever
resold, it is the only one whose identifying assumption (quality fixed at mint) is exactly true rather than
approximately true, it needs none of the four missing fields, and the cap — the thing that ruins naive markup
averages — is the thing that makes the specification *interesting* rather than merely possible. Its limitation is
structural rather than fixable: without seat coordinates it prices a tier, not a seat, and the published
evidence says seats are where the variation is.

---

## 5. Family 4 — Auction theory and mechanism design

**Estimates.** Two unrelated objects live under this name and conflating them is the trap.
(a) *Positive* auction theory, as used in structural econometrics: the distribution of bidders' private values
and the number of bidders, inverted from observed bids through the equilibrium first-order condition. Guerre,
Perrigne and Vuong state the result precisely — "the underlying distribution of bidders' private values is
identified from observed bids and the number of actual bidders without any parametric assumptions"
([Guerre, Perrigne & Vuong 2000](https://doi.org/10.1111/1468-0262.00123)).
(b) *Normative* mechanism design: which selling procedure maximises expected revenue given a prior
([Myerson 1981](https://doi.org/10.1287/moor.6.1.58)), and how the presence of a resale market changes
willingness to pay in the primary ([Haile 2001](https://doi.org/10.1257/aer.91.3.399)).

**Targets.** Nothing in T1–T4: (a) is void because there are no bids. T5 is reachable only through (b), and only
as a statement about the *mechanism*, never as a model of the price. The one measurable object this family
contributes is a prediction about primary willingness to pay, which is §5.2.

**Assumptions.** Private values (or an explicit common-value component), risk neutrality, symmetric bidders, no
collusion, and — for (b) — a known prior and a regularity condition on the value distribution. Every one of
these is unobservable here, and the prior especially: Myerson's optimal mechanism is a functional of the value
distribution, so without the distribution there is no optimal mechanism to compute.

**Data.** Zero. The contract carries `priceLamports`, `fromWallet` and `toWallet` on settled transfers and
nothing else — no bid, no offer, no watchlist, no view count, and `API_CONTRACT.md` has no endpoint that would
produce one. The four listing fields do **not** help: they are about asks, and this family needs bids. What would
help is the bid side, which 01-b §6 already names as the single most valuable absent observation.

**Implementation (D2).** **Specified-not-implemented**, for two independent reasons, either of which suffices.
(i) There is no bid data, so there is nothing to estimate. (ii) Even with an auction arm, the Guerre-type
estimator is a two-step nonparametric inversion requiring kernel density estimation on a two-dimensional
support; it is writable in stdlib in principle, it is numerically fragile in practice, and an event with tens of
transactions is an order of magnitude below where a nonparametric density is meaningful. The honest label is
*specified-not-implemented: needs bid-level data and, at realistic event scale, a parametric restriction in
place of the kernel step.*

**Evidence class.** **C** throughout for the theory. **A** for exactly one empirical result — primary auctions
in tickets — and it is evidence about the mechanism, not about this family's estimators. **D** for every
implication I draw for our engine.

**Primary sources.** [Myerson (1981), *Math. of OR* 6(1):58–73](https://doi.org/10.1287/moor.6.1.58);
[Guerre, Perrigne & Vuong (2000), *Econometrica* 68(3):525–574](https://doi.org/10.1111/1468-0262.00123);
[Haile (2001), *AER* 91(3):399–427](https://doi.org/10.1257/aer.91.3.399);
[Bulow & Klemperer (2009), *AER* 99(4):1544–1575](https://doi.org/10.1257/aer.99.4.1544);
[Bulow & Klemperer (2012), *JPE* 120(1):160–186](https://doi.org/10.1086/665416);
[Glaeser & Luttmer (2003), *AER* 93(4):1027–1046](https://doi.org/10.1257/000282803769206188).

### 5.1 The market is posted-price, so the right positive theory is not auction theory

A settled resale at price `p` is a take-it-or-leave-it offer accepted by one buyer out of an arrival stream. The
correct structural frame is sequential search with posted prices, where price dispersion is itself an equilibrium
object shaped by search costs ([Burdett & Judd 1983](https://doi.org/10.2307/1912045), class B). That frame needs
the buyer arrival rate and the valuation distribution — which are T3 and T4b, the two objects 01-b says are not
identified. So the *correct* theory in the *correct* family fails for the same reason everything else fails here.
Auction theory does not fail better; it fails on a different and larger obstacle, the total absence of bids. The
point of saying so is to stop a Phase 2 subagent being dispatched to estimate a value distribution from a
transaction record.

### 5.2 The one real transfer: the resale option sits inside primary willingness to pay

Haile's result is that "a bidder's willingness to pay at an auction increases with the expected level of
competition between resale buyers", because winning buys an option to resell. The transfer to a posted-price
primary is direct and it is not in 01-a or 01-b: **a primary buyer is purchasing the ticket plus an option to
resell, so primary willingness to pay is use value plus option value, and `resalePriceCapBps` truncates that
option.** Three consequences.

1. **Observed resale prices understate primary willingness to pay, not overstate it.** The ticket's value to a
   primary buyer includes a resale option the resale price does not price. This reverses the naive arbitrage
   reading in which the resale price is the ceiling on the primary price.
2. **The cap lowers primary willingness to pay.** Capping the resale gain shrinks the option, so at equal
   `p0/face` a capped event should show *lower* primary sell-through than an uncapped one. That is falsifiable,
   free, and testable on the first real dump by comparing capped and `resalePriceCapBps = null` events. It is
   confounded, badly: caps are chosen for hot events, which is exactly when sell-through is high, so the
   confound works against the prediction — which makes a positive finding informative and a null uninformative.
   **Class D, with its test named.**
3. **An optimiser that ignores the option is biased low on uncapped events.** Whether that bias matters is
   unmeasured; given 01-a's sizing of the prize at 1.4–3.4% of primary revenue, it plausibly does.

### 5.3 The ceiling is a mechanism change, and the allocation behind it is uninformative about value

Under a binding price control, allocation is by non-price competition, surplus is dissipated by rent-seeking,
and observed consumption carries no information about valuations —
[Bulow & Klemperer 2012](https://doi.org/10.1086/665416) and
[Glaeser & Luttmer 2003](https://doi.org/10.1257/000282803769206188), both class B for the transfer. For this
programme the consequence is a hard rule: **a ticket that sold at the ceiling went to whoever was fastest, and
that is a statement about latency, not about value.** Cap-region transactions must therefore be treated as
censored observations (§4.3) and never averaged into a value estimate. 01-a §3's warning that "fit on observed
markups and you conclude the hottest events are the least valuable" is the same fact stated as a bias.

### 5.4 The fork this family opens, and a conflict inside 01-a that I could not resolve

[Budish & Bhave 2023](https://doi.org/10.1257/mic.20180230), as read and quoted by 01-a §4 (class A), finds that
primary auctions "substantially improved price discovery, roughly doubled performer revenues, and, on average,
nearly eliminated the arbitrage profits" — and the authors explain why the auctions nonetheless failed to take
off. That is evidence that **changing the primary mechanism can dominate any pricing engine's payoff**, and it is
therefore a fork the operator has to decide, not me: build the engine, or recommend auctioning the top of the
inventory. I am recording it, not choosing.

There is also a conflict inside 01-a's own summary that should be logged in `F-decision-log.md`. 01-a §4 also
reports a *model-based counterfactual* from [Leslie & Sorensen](https://doi.org/10.1093/restud/rdt033): repricing
the top 10% of seats at the median resale price raises primary revenue about 3.4%. "Roughly doubled" and "3.4%" are two published answers to the
same commercial question, differing by more than an order of magnitude, and the difference is mechanism choice
versus price level. I have not read either paper myself and I will not adjudicate between quotes I did not check;
I record that the two numbers exist, that they are both labelled class A in 01-a, and that the gap is large
enough to change what the operator should build first. **Unresolved, and it is the most commercially consequential
unresolved item in this report.**

### 5.5 Verdict

Auction theory ships no estimator, one idea that matters (the resale option inside primary willingness to pay),
one hard rule (never average cap-region prices), and one fork (mechanism versus price). Its structural estimation
half should be struck from the Phase 2 plan outright until bid data exists, because the estimator's data
requirement is total and the four listing fields do not touch it.

---

## 6. Family 5 — Online learning and adaptive experimentation

**Estimates.** A *policy* rather than a parameter: a mapping from context to action that accumulates reward
while learning, with a regret guarantee relative to the best fixed action in hindsight. The contextual form
estimates the same mapping from logged data with partial feedback. The machinery is Thompson sampling
([Russo, Van Roy, Kazerouni, Osband & Wen 2018](https://doi.org/10.1561/2200000070)) or upper-confidence-style
algorithms ([Lattimore & Szepesvári 2020](https://doi.org/10.1017/9781108571401)).

**Targets.** It is aimed at T3 and T5 — the objects that would make the optimiser worth having. It reaches
neither, for five reasons, the fourth of which is decisive and is arithmetic rather than statistical.

**Assumptions, all of which fail or are untestable here.**

| # | Requirement | Status |
|---|---|---|
| 1 | A repeated decision with a stable action set | Holds — the primary price per tier is such a decision, and it recurs across events |
| 2 | The reward for the action taken is observed | **Partly fails.** Tier sell-through is observable as a ratio, on the unverified assumption that `issuedCount` means *sold* rather than *minted* (§12 item 2); and `issuedCount` and `Event.status` are untimestamped snapshots, so the reward cannot be attributed to a decision time (§3.6) |
| 3 | The environment is stationary, or its variation is bounded and known | **Fails.** Every event is a fresh draw from a different demand environment; the non-stationary relaxation ([Besbes, Gur & Zeevi 2015](https://doi.org/10.1287/opre.2015.1408)) gives guarantees that degrade in the total variation, which for a year of events is not small |
| 4 | **Positivity / common support:** every action has positive probability under the logging policy | **Fails by construction.** The platform sets one price per tier and records no rule and no propensity, so the logging policy has probability 1 on one action and 0 on every other — off-policy evaluation is not merely hard, it is *undefined* |
| 5 | Exploration is cheap | **Fails.** Exploring a low primary price on a live event gives up revenue on purpose. That is a money decision (R11), not a modelling decision |

**Data.** The four listing fields do not help at all. What this family needs is a **pricing-decision log**: for
each tier and each price change, the timestamp, the price chosen, and the rule or the propensity that chose it.
That is a **second data request**, after the four listing fields, and this programme has not yet made it. It is
cheap to record and it is the only thing that would ever make counterfactual evaluation possible.

**Implementation (D2).** Two halves with opposite answers. The *bandit* half is
**specified-not-implemented**: it does not need code, it needs a randomised or propensity-logged decision
process, and writing a Thompson sampler against data with no positivity would produce confident nonsense. The
*sequential-estimation* half is implementable in about forty lines: recursive least squares with a forgetting
factor is a rank-one update ([Plackett 1950](https://doi.org/10.1093/biomet/37.1-2.149)), and prequential
scoring with a proper rule ([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437)) is a running
average.

**Evidence class.** **C** for the negative result — the positivity requirement is a theorem-level fact about
off-policy estimation, not an opinion. **E** for any suggestion that a learnable price-response loop exists here.

**Primary sources.** [Russo et al. (2018), *FnT ML* 11(1):1–96](https://doi.org/10.1561/2200000070);
[Lattimore & Szepesvári (2020)](https://doi.org/10.1017/9781108571401);
[Dudík, Erhan, Langford & Li (2014), *Statist. Sci.* 29(4):485–511](https://doi.org/10.1214/14-sts500);
[Li, Chu, Langford & Schapire (2010), *WWW '10*:661–670](https://doi.org/10.1145/1772690.1772758);
[Besbes, Gur & Zeevi (2015), *Operations Research* 63(5):1227–1244](https://doi.org/10.1287/opre.2015.1408).

### 6.1 Why the loop cannot close: the action moves the outcome

This is the concrete answer to the brief's question and it is worth stating as arithmetic rather than as a
caveat. Write `r = V / face` for the resale clearing price as a multiple of the ticket's own face value — the
same scale as `markupBps = r − 1` and as the ceiling `1 + resalePriceCapBps/10⁴`. The action is `face`. So the
observed reward and the observed markup are both functions of the action, and the form of the function depends
on which of two worlds we are in.

1. **If the market values tickets in multiples of face** — `r` invariant to the primary price — then `markupBps`
   is a *constant function of the action*: it carries precisely zero information about the primary decision, and
   the only action-relevant outcome left is sell-through. A learner fitting markup in this world learns noise.
2. **If the market values tickets in absolute currency** — `V` fixed, so `r = V/face` falls as `face` rises —
   then the observed markup falls with the primary price *mechanically*, through the denominator, on top of any
   real demand destruction. A learner cannot separate the arithmetic from the economics without knowing how `V`
   responds to `face`, which is the question it was trying to answer.
3. **Either way the cap is a function of the action.** The ceiling is `face·(1+c)`, so raising the primary price
   loosens the constraint, and the cap-binding indicator is a deterministic threshold in `(face, V)`. The
   observation rule moves with the action.

The regime in which the signal would be clean is therefore exactly the regime in which the signal is manufactured
by the action. This is the programme's own Phase 3 warning — "pricing policies alter the data subsequently
observed" — landing on a specific field, and it is why the response variable has to be `log(price/face)` with
the action entering as a separate regressor rather than absorbed into the denominator (§4.6). **Class C.**

### 6.2 What does work, and it is not a bandit

Three uses survive, none of which needs exploration and none of which risks money.

1. **Prequential evaluation of forecasts.** Score every prediction before seeing the next observation, with a
   proper scoring rule, and compare models by their cumulative score. This is a *discipline*, not an algorithm,
   and it is the right answer to the programme's §4.8 and Phase 6 requirements. It costs nothing.
2. **Recursive estimation with a forgetting factor.** A hedonic or hazard model whose coefficients must track a
   changing market can be updated by a rank-one correction rather than refitted, and the forgetting factor is
   the only new parameter. This is legitimate adaptation and it is forty lines of stdlib code.
3. **A bandit over models, not over prices.** Choosing which of several candidate forecasters to trust, scored
   on prequential accuracy, has an action set that costs no revenue, a stationary-enough environment, and a
   reward observed immediately. It is the one honest bandit in this programme and it is worth building — it is
   *model selection*, dressed in adaptive clothing.

### 6.3 The whole family reduces to one question for the operator

If exploratory price variation is off the table — and it is, unless the operator says otherwise, because it
gives up revenue — then there is no feedback loop, and no online-learning method can substitute for one. If it
*is* on the table, the right design is not a bandit but a **randomised ask or price arm** on a subset of
listings, analysed as an experiment, because a properly randomised arm identifies the price response honestly
and does not need the exploration-exploitation scaffolding at all. Either way, the deliverable from this family
is a question, not a method: **will the platform ever vary a price for the purpose of learning?** Recorded in
§12 as an operator question with a cost attached.

### 6.4 Verdict

Zero estimators, one data request (the decision log with propensities), one discipline worth adopting
(prequential scoring), one legitimate adaptive component (recursive updating), one honest bandit (over models),
and one hard prohibition: never fit a learner to logged prices without knowing the policy that produced them.

---

## 7. Family 6 — Bayesian partial pooling and hierarchical models

**Estimates.** A posterior over group-level parameters in which each group's estimate is a precision-weighted
blend of its own data and a pooled mean, plus the hyperparameters at the top of the hierarchy — the pooled mean
`μ` and the between-group standard deviation `τ`.

**Targets.** T1′ directly, which is the cold-start event; T4a, through tier effects estimated from few sales;
and the event-level frailty of §3.5. It does not touch T3's price response — no amount of hierarchy substitutes
for a missing observation.

**Assumptions.**

| # | Assumption | Status |
|---|---|---|
| 1 | Groups within a stratum are exchangeable | **Declared, never testable.** This is the entire content of the method; if the partition is wrong, every shrinkage is wrong |
| 2 | The within-group likelihood matches how the data are observed | **Must be censored at the cap**, or the hierarchy pools biased means whose bias is correlated with an event-level covariate (§7.2c) |
| 3 | A prior on `τ` | Load-bearing with few groups: [Gelman 2006](https://doi.org/10.1214/06-BA117A) argues a flat prior on the *variance* is not weakly informative and recommends a half-t on the *standard deviation* |
| 4 | Conditional independence within a group given its parameter | Holds for sales given a ticket's latent value; fails if there are unmodelled price dynamics, which is why §7.4 matters |

**Data.** None of the four fields for the value hierarchy. What it needs instead is *groups*, and that is a
volume requirement the contract cannot create: a stratum with two events cannot estimate `τ`.

**Implementation (D2).** Three tiers of feasibility, and the boundary is worth stating exactly.
(i) **Empirical Bayes, closed form** — the normal-normal shrinkage estimator of
[Efron & Morris 1975](https://doi.org/10.1080/01621459.1975.10479864) — is a dozen lines, no iteration, no
library. Build this first. (ii) **Conjugate Gibbs** — normal-inverse-gamma conditionals for the normal
hierarchy — is a hand-written sampler of about eighty lines that runs a few thousand iterations in seconds at
this scale. Fine. (iii) **Anything non-conjugate** — a censored likelihood or a hazard with random effects —
needs either hand-coded quadrature (Gauss–Hermite nodes can be generated by a short symmetric-tridiagonal
eigen-decomposition) or a random-walk Metropolis with convergence diagnostics. Feasible, but I would not ship
it: mark it *implementable-not-recommended until the EB version has been compared against it*. Full posterior
sampling with HMC/NUTS (Stan, PyMC) is **specified-not-implemented** under D2 — no numerical stack on this box
and none may be installed.

**Evidence class.** **C** throughout. The shrinkage algebra is exact; the exchangeability of events is **D** and
is the assumption, not a finding.

**Primary sources.** [Efron & Morris (1975), *JASA* 70(350):311–319](https://doi.org/10.1080/01621459.1975.10479864);
[Efron (2010), *Large-Scale Inference*](https://doi.org/10.1017/CBO9780511761362);
[Gelman (2006), *Bayesian Analysis* 1(3):515–534](https://doi.org/10.1214/06-BA117A);
[Hougaard (1995), *Lifetime Data Analysis* 1(3):255–273](https://doi.org/10.1007/BF00985760);
[Rossi, Allenby & McCulloch (2005), *Bayesian Statistics and Marketing*](https://doi.org/10.1002/0470863692).

### 7.1 What the shrinkage actually says, written out so it can be checked

For the simplest case — one observation `y_j` per group, `y_j ~ N(θ_j, σ²)`, `θ_j ~ N(μ, τ²)` — the posterior
mean is

```
θ̂_j = μ + [ τ² / (σ² + τ²) ] · (y_j − μ)
```

with the bracket going to 0 as `τ² → 0` (full pooling: every group gets the pooled mean) and to 1 as `τ² → ∞`
(no pooling: every group gets its own data). For a group with `n_j` observations, `σ²` is replaced by `σ²/n_j`,
so **a group with no data gets the pooled mean and nothing else**. That is the entire content of "partial
pooling buys the cold-start event": a pooled mean plus a variance `τ² + σ²`. The width *is* the deliverable,
which is exactly what 01-b §4.6 already concluded and is worth restating because it is the honest answer rather
than a disappointment.

### 7.2 What pooling across events requires, item by item

**(a) A declared exchangeability partition.** Not estimable, not testable, and it does all the work. My
recommendation: `event category × venue-size band × organiser`, because those are the axes on which the primary
price level and the demand level differ most, and pooling across them is pooling a stadium show with a club
show. The consequence is brutal arithmetic: every stratification divides the number of groups, and `τ` is
estimated from the number of groups, not the number of sales.

**(b) Enough groups, with a defensible prior on `τ`.** With one group, `τ²` is not identified at all and the
estimator *is* the prior. With few groups it is prior-dominated, which is why Gelman's recommendation of a
half-t (half-Cauchy) prior on the *standard deviation* is not decoration. The elementary reason is a change of
variables: a uniform prior on `τ²` implies a prior on `τ` proportional to `τ`, which increases in `τ`, which
pushes `τ` up, which under-shrinks every thin cell — it tells you each cell is more informative than it is. The
general statement that matters more than the direction: **with few groups, the prior on `τ`, not the data, sets
the width of a cold-start interval.** And `τ̂²` is itself estimated with roughly `J − 1` degrees of freedom, so
the interval on a cold-start group is an estimate with its own wide interval, and that second-order uncertainty
must be propagated or the cold-start interval will be too narrow. **Class C.**

**(c) A censored likelihood.** If the cap truncates, pooling uncensored sample means pools quantities whose bias
depends on each event's cap — and the cap is an *event-level* covariate, so the bias enters at the same level as
the parameter being pooled. That is the specific way a hierarchical model goes wrong here, and it is invisible in
the output: the shrinkage looks well-behaved and the pooled mean is quietly a function of policy.

**(d) A decision about which parameter pools.** Recommendation: pool the *dispersion* fully (markup spread is
plausibly a property of the market, not the event), pool the *location* partially, and never pool the cap, which
is observed. The location is the parameter of interest and the one that is hardest to pool, which is the honest
summary of the trade.

### 7.3 The hierarchy level that actually pays

The hierarchy is `sale ⊂ tier ⊂ event ⊂ category`, and the scarce parameter is not the event effect — it is the
**tier effect**, because a tier is estimated from a handful of sales and there are many tiers. Partial pooling
pays where groups are plentiful and thin, which is exactly the tier level, not the event level. That inverts the
intuition that cold start is the main use: cold start is the *dramatic* use, and the tier level is the
*valuable* one.

### 7.4 The second, better use: partial pooling across time

01-b T1 says the value between trades is not identified and that interpolation requires a martingale assumption.
A local-level state-space model is partial pooling across time and it is the implementable form of that
assumption, stated rather than hidden:

```
log V_i(t+1) = log V_i(t) + η,      η ~ N(0, q)
observed:     y_ik        = log V_i(t_ik) + ε,   ε ~ N(0, r)
```

A scalar Kalman filter and smoother for this is about thirty lines of stdlib Python, and it produces a smoothed
path for each ticket with `q/r` estimated from the data. Three things it buys: a price at any `τ`, not just at
trade instants; an explicit, falsifiable statement of how much the price moves between trades; and a natural
way to pool across tickets within a tier (the tier mean enters as the prior for `log V_i(issued)`). What it does
*not* do is identify anything — `q` is a prior in disguise, and the smoothed path between two trades is an
interpolation whose accuracy is a function of `q/r`. **Class C, and the honest label is "declared
interpolation", not "estimated price".**

### 7.5 Verdict

Partial pooling is the family that makes thin data usable and it is the second thing I would build after the
hedonic (§4.6) and before the hazard, because both of those want a shrinkage layer underneath them. Its costs
are a declared exchangeability assumption, a censored likelihood, and a prior on `τ` that must not be flat. Its
honest output for a cold-start event is a wide interval around a pooled mean, and the width is the answer.

---

## 8. Family 7 — Conformal prediction and distribution-free uncertainty

**Estimates.** A prediction *set* `C(x)` with the property that `P(Y ∈ C(x)) ≥ 1 − α` in finite samples, with no
distributional assumption, *given* exchangeability and a calibration set of size `n`. In the split-conformal
case the whole procedure is: fit on a training split, compute nonconformity scores on a calibration split, and
take the `⌈(n+1)(1−α)⌉`-th smallest score as the radius. Coverage is then at least `1−α` and, when scores are
almost surely distinct, at most `1−α + 1/(n+1)`
([Angelopoulos & Bates 2023](https://doi.org/10.1561/2200000101)).

**Targets.** T6, and only T6. It does not estimate a price, a hazard or a demand curve, and it is not a
calibration method in the sense of making a forecast well-calibrated — it *widens a set* to guarantee marginal
coverage.

**Assumptions, and the three that fail.**

| # | Assumption | Status |
|---|---|---|
| 1 | A calibration set exists | **Absent.** There is no hold-out of scored, unresolved tickets. Nothing can be computed |
| 2 | Calibration and test points are exchangeable | **Fails.** The only scored observations are `sale` rows, so calibration is conditioned on "this ticket sold" while the test ticket may not sell |
| 3 | The target `Y` is defined for every unit in the population | **Fails, and this is the deepest problem** — a ticket that never resells has no resale price, so the unconditional prediction-set statement has no referent for most of the population |
| 4 | The fitting algorithm treats data symmetrically | Holds for least squares; irrelevant until 1–3 are fixed |

**Data.** It needs a *scoring population* — listings scored before the outcome, with outcomes recorded on both
branches — which is a stronger requirement than the four listing fields, because those give exposure and ask but
still record a price only on the success branch. So conformal's data requirement is the four fields *plus* a
sampling scheme. Named in §8.2.

**Implementation (D2).** Yes, trivially — split-conformal is fifteen lines, sort the scores and take the order
statistic, and weighted conformal is thirty. This is the clearest case in the report where **implementable and
usable are different words**: the code is trivial and there is nothing to run it on.

**Evidence class.** **C** — the coverage result is a theorem. The claim that a ticket price interval can ever be
conformally valid is **D at best** and, as stated in assumption 3, arguably not well posed.

**Primary sources.** [Vovk, Gammerman & Shafer (2005), *Algorithmic Learning in a Random World*](https://doi.org/10.1007/b106715);
[Angelopoulos & Bates (2023), *FnT ML* 16(4):494–591](https://doi.org/10.1561/2200000101);
[Barber, Candès, Ramdas & Tibshirani (2023), *Ann. Statist.* 51(2):816–845](https://doi.org/10.1214/23-AOS2276);
[Tibshirani, Barber, Candès & Ramdas (2019), arXiv:1904.06019](https://arxiv.org/abs/1904.06019).

### 8.1 Why "no calibration set" is not a technicality

The brief asks whether conformal helps calibrate intervals with no calibration set. The answer is no in the
strongest sense: conformal is *defined* by its use of a calibration set, so without one there is no procedure to
apply, not a degraded procedure. But the more useful answer is the second-order one, because a calibration set
will eventually exist and it still will not help on its own.

**The target is conditional and the guarantee is marginal.** Conformal gives coverage averaged over the
distribution of `(X, Y)` pairs. Here `Y` — a realised resale price — does not exist for a ticket that never
resells, and 01-a §5 puts non-resale at around 95% of tickets. So the population over which marginal coverage
would be claimed is a population in which `Y` is undefined for nineteen units in twenty. Conformal prediction
can only be applied *conditional on the ticket transacting*, which is precisely the selective-labels problem
01-b T6 names: every scored observation is conditioned on the outcome being modelled, and the standard remedy —
reject inference — does not reliably work
([Crook & Banasik 2004](https://doi.org/10.1016/S0378-4266(03)00203-6), as cited in 01-b).

**Distribution shift is the failure conformal knows how to name.**
[Barber et al. 2023](https://doi.org/10.1214/23-AOS2276) generalises coverage to non-exchangeable data via
weighted quantiles, and [Tibshirani et al. 2019](https://arxiv.org/abs/1904.06019) does it under covariate shift
when the likelihood ratio between calibration and test distributions is *known*. Here the shift is from "sold"
to "might not sell", and its likelihood ratio is the quantity the whole programme cannot estimate. So the
generalisations do not rescue it.

### 8.2 The one design that would make it usable, stated so it can be costed

Stratify by `event category × tier × cap regime`; for each stratum `s`, sample listings uniformly at random
*before* any outcome is known; record whether each sold and at what price; use sold listings as calibration
points. Then for a target miscoverage `α` the calibration cell must satisfy `1/(n_s + 1) ≤ α` in slack, so the
required `n_s` grows as `1/α` and the strata divide the sample. That is a precise, costable requirement, and it
is the only route to a coverage number that means anything. It is a data-schema decision, not a model decision,
and it should be made before launch because it cannot be reconstructed afterwards.

### 8.3 What to do about uncertainty instead, today

Three usable substitutes, in order of honesty:

1. **Empirical quantiles of the realised price ratio, scoped to transactions.** "Among comparable tickets that
   resold, the 25th–75th percentile of realised `price/face` was …" This is honest because it is explicitly
   conditional, and it is what an operator actually needs. Cheap, exact, no assumption.
2. **Quantile regression on the hedonic** — [Koenker & Bassett 1978](https://doi.org/10.2307/1913643) — for
   conditional quantiles of `log(price/face)`. Implementation caveat under D2: exact quantile regression is a
   linear program, and D2 has no LP solver. Iteratively reweighted least squares is the standard approximation
   and it is an *approximation* with no guarantee of exact quantile optimality, so I would rather bin the sample
   by the hedonic's fitted value and take empirical quantiles within bins: exact within the bin, cruder in
   resolution, and honest about which.
3. **Proper scoring and reliability for the sale indicator**, where 01-b T6 confirms the population is complete:
   Brier score, log score, a reliability curve, and the reliability–resolution decomposition. This is the one
   calibration task that is fully available today, and it needs no calibration set because it is scored on the
   whole population ([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437) for why the scoring
   rule must be proper; Murphy's decomposition as cited in 01-b).

### 8.4 Verdict

Conformal prediction ships one paragraph of value: it states exactly what a defensible interval would require
(`n` exchangeable calibration points per stratum, a uniformly sampled scoring population, outcomes on both
branches) and exactly which assumption this observation set violates. It ships an implementation nobody can run
and would not trust if they could. Building it now would be a demonstration of competence in a method that the
data cannot support, which is the failure mode the programme's §4.6 exists to prevent.

---

## 9. Family 8 — Stochastic control

**Estimates.** A value function and an optimal control (or stopping) policy for a controlled stochastic process:
in continuous time the solution of a Hamilton–Jacobi–Bellman equation with its free boundary; in discrete time
the backward induction of a Markov decision process.

**Targets.** T5 as a policy, T2 as the state's transition law, and it is the only family that can carry a **risk
functional inside the objective** rather than bolted on afterwards. It does not touch T3's price response, and
it inherits every input RM inherits.

**Assumptions, and which fail.**

| # | Assumption | Status |
|---|---|---|
| 1 | A controlled Markov state with a known transition law | **Fails.** The transition law is T2, identified only in curvature; the linear trend is a normalisation (01-b §4.2) |
| 2 | The state is observed | **Fails.** Latent value is not observed, so the true problem is a partially observed MDP; the workable reduction is certainty equivalence (`E[V | data]` treated as the state) and it must be declared |
| 3 | A terminal condition | **Fails as usually written** — `V(T,n)=n·u` with `u` unobserved, not `0`. §9.2 and §2.2 |
| 4 | A reward function and a risk functional | Holds, and this is the family's real contribution — §9.4 |
| 5 | The action does not move the environment | **Fails, and it matters here** — the primary price sets the resale ceiling (§6.1) |

**Data.** The four listing fields change nothing structural. Two other things do: `delistReason` for the
terminal value `u` (withdrawal versus expiry), and a primary inventory time series (Gap 5) for the coupled system.

**Implementation (D2).** Split down the middle. **Discrete-time backward induction on a small grid: yes, and it
is the whole answer** — a state space of a few hundred cells is microseconds of pure Python. **Continuous-time
HJB as a PDE: no** — that needs a solver, and it is marked *specified-not-implemented* with the note that the
discrete DP *is* the numerical solution of the same problem, so the distinction is cosmetic as long as the grid
is presented as the approximation it is. **CVaR: yes**, by sorting simulated profits (exact for the empirical
distribution); the [Rockafellar & Uryasev](https://doi.org/10.21314/JOR.2000.038) linear-programming
formulation is *specified-not-implemented* because D2 has no LP solver — and it is unnecessary here, because the
decision is one-dimensional and a grid search over `p0` is exact to grid resolution.

**Evidence class.** **C** for the method and for the CVaR algebra. **B** for the empirical phenomenon the model
explains (declining prices as expiry approaches, and negative opportunity costs at the end) — that is Sweeting
2012, class A per 01-a §2, and it is the strongest empirical anchor any family in this report has. **D** for the
coupled primary-secondary formulation in §9.3, which nobody has estimated.

**Primary sources.** [Gallego & van Ryzin (1994)](https://doi.org/10.1287/mnsc.40.8.999);
[Brémaud (1981), *Point Processes and Queues*](https://doi.org/10.1007/978-1-4684-9477-8) for intensity control;
[Peskir & Shiryaev (2006), *Optimal Stopping and Free-Boundary Problems*](https://doi.org/10.1007/978-3-7643-7390-0);
[Artzner, Delbaen, Eber & Heath (1999), *Mathematical Finance* 9(3):203–228](https://doi.org/10.1111/1467-9965.00068);
[Rockafellar & Uryasev (2000), *Journal of Risk* 2(3):21–41](https://doi.org/10.21314/JOR.2000.038).

### 9.1 It is the same family as revenue management, and saying so prevents double-counting

[Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999) formulate their problem as *intensity control of
a point process* — that is stochastic control, written by revenue-management authors, in a management journal. So
the honest question is not what stochastic control adds in general but what is left when RM's results are
already on the table. Three things, and only three.

1. **Risk functionals inside the objective.** RM optimises expected revenue. A controlled Markov decision
   process can carry any terminal utility, so CVaR, a variance penalty or an expected-utility objective enters
   natively instead of as a post-hoc adjustment.
2. **The coupled two-market system** (§9.3), which RM cannot express because RM assumes the seller's price does
   not move the buyer's outside option.
3. **The optimal-stopping structure** that a positive terminal use value forces (§9.2), which is a different
   problem from RM's terminal-salvage problem.

Anything outside those three is notation. During Phase 4's model comparison, RM and stochastic control should be
entered **once**, not twice.

### 9.2 The terminal value makes this an optimal stopping problem, and shrinks the implementable object

Because `V(T,n) = n·u` with `u > 0` (§2.2), the last period is not a clearance sale but a *choice between selling
and using*. That is an optimal stopping problem with a free boundary
([Peskir & Shiryaev 2006](https://doi.org/10.1007/978-3-7643-7390-0)), and its solution is a scalar per state — a
**reserve price**, not a value function. Three consequences, and the third is testable.

1. **The implementable object is a reserve-price surface** `p*(τ, inventory, cap-binding)`. That is dramatically
   smaller than a value function, and it is what the optimiser actually consumes.
2. **`u` controls the shape of the price path, not just the level.** With `u` small the reserve decays toward the
   market as the deadline approaches, which reproduces Sweeting's steep endgame declines; with `u` large the
   reserve is approximately `u` and the price path is flat or rising. Because `u` is heterogeneous (§2.2), the
   observed path is a *mixture* of a decay curve and a flat one, and the mixing weight is the attended-or-not
   split. So the *curvature* of the fitted `τ`-spline in §4.6 is informative about the distribution of `u`, and
   01-b's T2 (curvature identified, linear trend not) is exactly the amount of shape information needed. This is
   the cleanest link in the report between an unidentified quantity (T2's level) and a partly identified one (its
   shape). **Class C.**
3. **The endgame is a withdrawal decision**, so the `withdrawn` versus `expired` split in `delistReason`
   identifies it. Already stated in §2.2; repeated here because this is where the estimator would live.

### 9.3 The coupled system, which is what Phase 3 actually needs

The programme's Phase 3 asks whether the market should be modelled as a dynamic feedback system. For this
platform the coupling is specific and short, and it is a Stackelberg structure rather than a general equilibrium:

```
platform sets p0  →  ceiling = p0·(1 + c)  →  resale market clears under the ceiling
                  →  resale price and liquidity  →  buyer's resale option value
                  →  primary willingness to pay  →  primary sell-through at p0
```

Because the platform moves first and the resale market clears within the event, the right computational
structure is: solve the **follower** (resale clearing given `p0` and the ceiling), then optimise the **leader's**
one-dimensional problem over `p0`. That is a nested one-dimensional search, not a fixed point in a high-dimensional
space, and it is implementable in stdlib: an outer grid over `p0` (say 41 points), an inner fixed-point iteration
of a few sweeps. The one honest caveat is in 01-b §4.5(ii): because the cap is proportional, the band is
scale-free, so the leader's problem collapses to *where to sit in the willingness-to-pay distribution*, trading
volume against margin on one dimension. **Class D, and it is the specific formulation Phase 5 should carry.**

### 9.4 Risk, and exactly how far the stdlib goes

CVaR is the right functional because it is coherent in the
[Artzner et al. 1999](https://doi.org/10.1111/1467-9965.00068) sense — subadditive, monotone, positively
homogeneous and translation-invariant — whereas variance is not, and because it penalises exactly the risk this
business carries: unsold inventory at the deadline. For a simulated profit sample of size `m`, CVaR at level `α`
is the mean of the worst `⌈αm⌉` outcomes; no optimisation is needed to *evaluate* it. To *optimise* over `p0`,
sweep the grid and pick the best, which is exact to grid resolution. The Rockafellar–Uryasev formulation turns
that into a linear program, which is elegant and unavailable here; state that the grid replaces it and that the
only cost is resolution. With 41 prices and 10⁴ scenarios the sweep is 4×10⁵ evaluations of a few arithmetic
operations, which is seconds rather than minutes in CPython — acceptable for a decision made once per event.

### 9.5 The state space I would actually build

`(inventory-remaining bucket, days-to-event bucket, cap-binding regime)`, with about six, twelve and three cells
respectively — 216 states. The latent value enters through certainty equivalence: use the hedonic prediction
from §4.6 as the state's location and the state-space variance from §7.4 as its uncertainty. Backward induction
over 216 states × a 41-point price grid is trivial. Output: a reserve-price surface, and a **set** of surfaces
over the demand-parameter box, because the demand function is not identified and reporting one surface would be
overclaiming (01-b T5). What this buys over a single number is a statement of the form "above this price the
recommendation is insensitive to the elasticity we cannot estimate, below it, it is not" — which is exactly the
kind of answer a set-identified problem can honestly support.

### 9.6 Verdict

Stochastic control buys the decision layer: a reserve-price surface, a risk functional that suits the business,
and the only formulation in this report that can express the primary-secondary feedback. It buys no estimate of
anything. Its one measurable prediction — that the endgame flattens where the owner's use value is high, so the
observed price path is a mixture of decays and flats — connects to the strongest empirical result in the ticket
literature (Sweeting's steep endgame price cuts, class A), which makes it the best-integrated family in the report
even though it estimates the least.

---

## 10. Rejected, and deferred with conditions

Each entry states what it is, why it is out, and what single event would bring it back. "Rejected" here means
rejected *for this observation set at this stage*, not rejected in general — the programme is discovery-driven
and a rejection that does not name its revival condition is just a preference.

### 10.1 Rejected: overbooking, cancellation and no-show revenue management

**Why.** A ticket token *is* the seat. There is no reservation that could be oversold, no reaccommodation cost,
and no second inventory to protect. A redeemed ticket is not a no-show the seller can resell; it is a consumed
unit.

**What would revive it.** Nothing in this schema. A future product where a ticket is a revocable reservation
rather than an owned token would be a different business.

**Note.** [Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999) explicitly extends its framework to
"reordering, overbooking, and random cancellations", which is why the rejection has to be stated rather than
assumed: the classical model covers the case, and this market simply does not have it.

### 10.2 Rejected: network and origin-and-destination yield management, bid-price control, EMSR booking limits

**Why.** These allocate a *shared* capacity across fare classes with a fixed arrival order and a nesting
structure. Here each `TicketTier` has its own `totalSupply`, so tiers do not share capacity at all; the only
cross-tier coupling is demand substitution, which is the multiproduct pricing problem
([Gallego & van Ryzin 1997](https://doi.org/10.1287/opre.45.1.24)), not network RM. Bid-price control and the
Expected Marginal Seat Revenue heuristic ([Belobaba 1989](https://doi.org/10.1287/opre.37.2.183)) both presume the
thing that is absent: a shared capacity being rationed across classes.

**What would revive it.** A venue with a single physical capacity sold under several price fences with upgrade
rights, where a seat released from one class can serve another.

### 10.3 Rejected: structural estimation of a value distribution from bids

Cross-referenced from §5. The estimator
([Guerre, Perrigne & Vuong 2000](https://doi.org/10.1111/1468-0262.00123)) needs observed bids and bidder counts;
the contract has neither, and the four listing fields do not touch it. **Revival:** any record of bids, offers,
or an auction arm.

### 10.4 Rejected: optimal auction design as a fitted object

[Myerson 1981](https://doi.org/10.1287/moor.6.1.58) is a functional of the value distribution's prior. Without the
prior there is no optimal mechanism to compute, and estimating the prior is 10.3. Retained only as the
prescriptive fork in §5.4. **Revival:** same as 10.3, plus an operator willing to change the selling mechanism.

### 10.5 Rejected: extreme-value theory for the value distribution above the cap

**Why.** EVT estimates a tail *from tail observations*. The cap guarantees that no observation above the ceiling
exists, so this is not a small-sample problem, it is a support problem, and the asymptotic regime the theory needs
is one the data can never enter. There is also a modelling error waiting here: for a perishable good with a hard
deadline the economically relevant tail is the **left** tail — the risk of not selling — not the right tail of
value.

**What would revive it.** An event with `resalePriceCapBps = null` (the schema already allows it) and enough
volume to place observations in the extreme tail, used deliberately as a measurement device for what the cap
hides. That is a real and cheap idea and it belongs in the Phase 2 plan as a *comparison group*, not as an EVT
model.

### 10.6 Rejected: Gaussian processes and kriging for a seat-quality price surface

**Why.** Three independent reasons. (i) It needs `O(n³)` linear algebra and a hyperparameter optimisation, which
D2 forbids. (ii) Its entire input is seat coordinates, which are absent (Gap 3), so there is nothing to smooth
over. (iii) With of order ten squared observations per event the posterior would be prior-dominated and would
look like a confident surface while being a statement about the kernel.

**What would revive it.** Seat coordinates plus a permitted numerical stack. It is then the natural model for the
within-event price surface, and it should be on the list as *specified-not-implemented* at that point.

### 10.7 Rejected: deep learning and gradient boosting

**Why.** D2 forbids the stack, and independently the sample size is wrong by orders of magnitude: an event's
resale history is tens of transactions. Nothing in 01-a or 01-b suggests a nonlinearity worth fitting. The honest
position is that these are rejected *for this data volume*, not in principle — if the ledger turns out large, the
argument changes and Phase 4 should revisit it. **Class D** as a claim about their usefulness here either way.

### 10.8 Rejected: matrix completion and collaborative filtering for cold start

**Why.** These methods need a matrix whose missingness is ignorable. Here the missingness *is* the phenomenon: an
event with no resale history is not a randomly unobserved cell, it is an event nobody wanted to resell, and
treating the two as the same is the error the whole identification report exists to prevent. The matrix is also
almost entirely empty by construction (resale at roughly 5% of tickets, 01-a §5). **Class E.**

### 10.9 Rejected: agent-based simulation and statistical mechanics as a model of the market

**Why.** The parameters are not identified from the observation set, and 00-data-situation §5.2 restricts
simulation in this programme to *estimator properties*. A calibrated agent model would be a calibrated
assumption wearing a simulation's clothes. Simulation stays in its legitimate role: a test bed for whether an
estimator recovers its parameter (labelled SIM), never as a description of ticket markets.

### 10.10 Rejected: full-posterior sampling (HMC/NUTS, Stan, PyMC)

**Why.** D2: no numerical stack on this box and none may be installed. The conjugate and empirical-Bayes
approximations in §7 cover the models actually needed. **Revival:** a permitted numerical stack and a model whose
likelihood is genuinely non-conjugate *and* whose answer is decision-relevant.

### 10.11 Rejected: synthetic control, difference-in-differences, and event studies as a route to causal price effects

**Why.** All three need untreated units with a parallel trend, or an exogenous shock. There is neither: any two
events differ in demand, venue, city and organiser at once, and no policy change is recorded with a timestamp
(§1.4(3)).

**What is *not* rejected, and is the most important recommendation in this report.** The causal price response is
identified by exactly one design: **randomised price variation**, on listings (an ask arm) or on primary tiers.
That is money — revenue given up on purpose — and it is therefore the operator's decision, not a research
question (R11). It should be put to him as a costed proposal, because *every* price-response claim in this
programme otherwise stays class D forever. **Class C for the claim that randomisation would identify it; the
design itself is a business decision.**

### 10.12 Rejected: Rosen's second stage for demand recovery

Cross-referenced from §4.1. A single market's transactions do not identify demand and supply separately. This is
rejected on theoretical grounds established before this report and restated in 01-b §4.4.

---

### Deferred, with the condition that revives each

| # | Method | Condition |
|---|---|---|
| F1 | **Change-point detection** — CUSUM ([Page 1954](https://doi.org/10.1093/biomet/41.1-2.100)) or PELT ([Killick, Fearnhead & Eckley 2012](https://doi.org/10.1080/01621459.2012.737745)) | Not rejected, demoted. Use as a **diagnostic guard**, not a model: 01-a §6 names the regime switches that would silently invalidate any pooled estimate — cap enforcement on or off, off-ledger key handoff, and the US all-in pricing rule (16 CFR 464, effective 2025-05-12). All are cheap to test for and expensive to miss. Implementable in stdlib in a few dozen lines |
| F2 | **Quantile regression** | Binned empirical quantiles now (§8.3); exact quantile regression only if an LP solver is permitted |
| F3 | **Non-conjugate random-effects models** | After the empirical-Bayes version in §7 has been compared against it and shown to matter |
| F4 | **Extreme-value theory** | A cap-free event with volume (§10.5) |
| F5 | **Gaussian processes / kriging** | Seat coordinates plus a numerical stack (§10.6) |
| F6 | **Contextual bandits over prices** | Operator authorises randomised price variation (§6.3) |
| F7 | **Structural auction estimation** | Any bid or offer record appears (§10.3) |
| F8 | **Time-series models for the price path** | If the hedonic's `τ`-spline in §4.6 fails an out-of-sample prequential test against a simple state-space alternative. Ranked below, not excluded |

---

## 11. Sources

**Verification statement.** Every DOI below was resolved through `https://doi.org` during this pass on
2026-11-07 and its bibliographic record — authors, year, title, journal, volume, issue, pages — was read back
from the Crossref API rather than from memory. Three named exceptions, all stated rather than smoothed over:

- **Vovk, Gammerman & Shafer (2005).** `10.1007/b106715` resolves to the Springer record, but Crossref returns no
author list for that work. Authorship is confirmed from the ACM review record of the same book
(`10.1145/1189056.1189065`, found via OpenAlex) which states the author list and the ISBN.
- **The two arXiv items** (Tibshirani et al. 2019; the Angelopoulos & Bates preprint is superseded by the journal
version below) are DataCite-registered, not Crossref. Their titles were confirmed by fetching
`https://arxiv.org/abs/1904.06019` and reading the returned page title.
- **One correction made during verification, recorded because it is the exact failure mode this pass exists to
avoid.** Su (2007) was first written here with DOI `10.1287/mnsc.1060.0547`; Crossref returned an unrelated paper
on open-source business models. The correct DOI is `10.1287/mnsc.1060.0667`. A citation written from memory would
have shipped the wrong paper with the right-sounding title.

**Works referenced only through `01-a` or `01-b`, and not independently re-verified here.** Murphy (1973), the
reliability–resolution decomposition; Working (1927), on the locus of demand and supply intersections; and
Leslie & Sorensen (2014), whose figures I quote only as they appear in `01-a` §4. Their links are in `01-b` §7
and `01-a`'s source list. **I read no ticket-market paper's full text during this pass** — every class-A claim
attributed to `01-a` is `01-a`'s reading of the paper, not mine, and it is labelled that way where it appears.
This is a real limitation of the report and the reason it is stated first rather than last.

**One citation dropped rather than guessed.** I intended to cite Dawid's prequential paper
(*JRSS-A* 147(2), 1984) for the sequential-evaluation discipline in §6.2. The DOI I first tried resolved to an
unrelated rainfall paper and I could not confirm the correct one in this pass, so the claim in §6.2 rests on
[Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437) alone. A dropped citation is a small cost;
an invented one is a large one.

### Empirical and ticket-market sources

1. Budish, E., & Bhave, A. (2023). Primary-market auctions for event tickets: eliminating the rents of "Bob the
   Broker"? *American Economic Journal: Microeconomics* 15(1), 142–170.
   https://doi.org/10.1257/mic.20180230
2. Leslie, P., & Sorensen, A. (2014). Resale and rent-seeking: an application to ticket markets. *Review of
   Economic Studies* 81(1), 266–300. https://doi.org/10.1093/restud/rdt033
3. Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence from secondary markets for
   Major League Baseball tickets. *Journal of Political Economy* 120(6), 1133–1172. https://doi.org/10.1086/669254

### Economics, mechanism design and revenue management

4. Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). Coherent measures of risk. *Mathematical Finance*
   9(3), 203–228. https://doi.org/10.1111/1467-9965.00068
5. Aviv, Y., & Pazgal, A. (2008). Optimal pricing of seasonal products in the presence of forward-looking
   consumers. *Manufacturing & Service Operations Management* 10(3), 339–359.
   https://doi.org/10.1287/msom.1070.0183
6. Belobaba, P. P. (1989). Application of a probabilistic decision model to airline seat inventory control.
   *Operations Research* 37(2), 183–197. https://doi.org/10.1287/opre.37.2.183
7. Bitran, G., & Caldentey, R. (2003). An overview of pricing models for revenue management. *Manufacturing &
   Service Operations Management* 5(3), 203–229. https://doi.org/10.1287/msom.5.3.203.16031
8. Bulow, J., & Klemperer, P. (2009). Why do sellers (usually) prefer auctions? *American Economic Review* 99(4),
   1544–1575. https://doi.org/10.1257/aer.99.4.1544
9. Bulow, J., & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer surplus. *Journal of Political
   Economy* 120(1), 160–186. https://doi.org/10.1086/665416
10. Burdett, K., & Judd, K. L. (1983). Equilibrium price dispersion. *Econometrica* 51(4), 955–969.
    https://doi.org/10.2307/1912045
11. Gallego, G., & van Ryzin, G. (1994). Optimal dynamic pricing of inventories with stochastic demand over finite
    horizons. *Management Science* 40(8), 999–1020. https://doi.org/10.1287/mnsc.40.8.999
12. Gallego, G., & van Ryzin, G. (1997). A multiproduct dynamic pricing problem and its applications to network
    yield management. *Operations Research* 45(1), 24–41. https://doi.org/10.1287/opre.45.1.24
13. Glaeser, E. L., & Luttmer, E. F. P. (2003). The misallocation of housing under rent control. *American
    Economic Review* 93(4), 1027–1046. https://doi.org/10.1257/000282803769206188
14. Guerre, E., Perrigne, I., & Vuong, Q. (2000). Optimal nonparametric estimation of first-price auctions.
    *Econometrica* 68(3), 525–574. https://doi.org/10.1111/1468-0262.00123
15. Haile, P. A. (2001). Auctions with resale markets: an application to U.S. Forest Service timber sales.
    *American Economic Review* 91(3), 399–427. https://doi.org/10.1257/aer.91.3.399
16. Myerson, R. B. (1981). Optimal auction design. *Mathematics of Operations Research* 6(1), 58–73.
    https://doi.org/10.1287/moor.6.1.58
17. Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *The Journal of Risk*
    2(3), 21–41. https://doi.org/10.21314/JOR.2000.038
18. Su, X. (2007). Intertemporal pricing with strategic customer behavior. *Management Science* 53(5), 726–741.
    https://doi.org/10.1287/mnsc.1060.0667
19. Talluri, K. T., & van Ryzin, G. J. (2004). *The Theory and Practice of Revenue Management*. Springer.
    https://doi.org/10.1007/b139000

### Hedonic pricing and price-index construction

20. Bailey, M. J., Muth, R. F., & Nourse, H. O. (1963). A regression method for real estate price index
    construction. *JASA* 58(304), 933–942. https://doi.org/10.1080/01621459.1963.10480679
21. Brown, J. N., & Rosen, H. S. (1982). On the estimation of structural hedonic price models. *Econometrica*
    50(3), 765–768. https://doi.org/10.2307/1912614
22. Ekeland, I., Heckman, J. J., & Nesheim, L. (2004). Identification and estimation of hedonic models. *Journal
    of Political Economy* 112(S1), S60–S109. https://doi.org/10.1086/379947
23. Gatzlaff, D. H., & Haurin, D. R. (1997). Sample selection bias and repeat-sales index estimates. *Journal of
    Real Estate Finance and Economics* 14(1–2), 33–50. https://doi.org/10.1023/A:1007763816289
24. Meese, R. A., & Wallace, N. E. (1997). The construction of residential housing price indices: a comparison of
    repeat-sales, hedonic-regression, and hybrid approaches. *Journal of Real Estate Finance and Economics*
    14(1–2), 51–73. https://doi.org/10.1023/A:1007715917198
25. Pakes, A. (2003). A reconsideration of hedonic price indexes with an application to PC's. *American Economic
    Review* 93(5), 1578–1596. https://doi.org/10.1257/000282803322655455
26. Rosen, S. (1974). Hedonic prices and implicit markets: product differentiation in pure competition. *Journal of
    Political Economy* 82(1), 34–55. https://doi.org/10.1086/260169
27. Steele, M., & Goy, R. (1997). Short holds, the distributions of first and second sales, and bias in the
    repeat-sales price index. *Journal of Real Estate Finance and Economics* 14(1–2), 133–154.
    https://doi.org/10.1023/A:1007780219924

### Survival analysis and event history

28. Allison, P. D. (1982). Discrete-time methods for the analysis of event histories. *Sociological Methodology*
    13, 61–98. https://doi.org/10.2307/270718
29. Andersen, P. K., & Gill, R. D. (1982). Cox's regression model for counting processes: a large sample study.
    *The Annals of Statistics* 10(4), 1100–1120. https://doi.org/10.1214/aos/1176345976
30. Boag, J. W. (1949). Maximum likelihood estimates of the proportion of patients cured by cancer therapy.
    *JRSS-B* 11(1), 15–44. https://doi.org/10.1111/j.2517-6161.1949.tb00020.x
31. Brémaud, P. (1981). *Point Processes and Queues: Martingale Dynamics*. Springer.
    https://doi.org/10.1007/978-1-4684-9477-8
32. Cox, D. R. (1972). Regression models and life-tables. *JRSS-B* 34(2), 187–202.
    https://doi.org/10.1111/j.2517-6161.1972.tb00899.x
33. Fine, J. P., & Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk.
    *JASA* 94(446), 496–509. https://doi.org/10.1080/01621459.1999.10474144
34. Fleming, T. R., & Harrington, D. P. (2005). *Counting Processes and Survival Analysis*. Wiley.
    https://doi.org/10.1002/9781118150672
35. Hougaard, P. (1995). Frailty models for survival data. *Lifetime Data Analysis* 1(3), 255–273.
    https://doi.org/10.1007/BF00985760
36. Lagakos, S. W. (1979). General right censoring and its impact on the analysis of survival data. *Biometrics*
    35(1), 139–156. https://doi.org/10.2307/2529941
37. Prentice, R. L. (1986). A case-cohort design for epidemiologic cohort studies and disease prevention trials.
    *Biometrika* 73(1), 1–11. https://doi.org/10.1093/biomet/73.1.1

### Bayesian inference, shrinkage and uncertainty quantification

38. Efron, B. (2010). *Large-Scale Inference: Empirical Bayes Methods for Estimation, Testing, and Prediction*.
    Cambridge University Press. https://doi.org/10.1017/CBO9780511761362
39. Efron, B., & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *JASA*
    70(350), 311–319. https://doi.org/10.1080/01621459.1975.10479864
40. Gelman, A. (2006). Prior distributions for variance parameters in hierarchical models. *Bayesian Analysis*
    1(3), 515–534. https://doi.org/10.1214/06-BA117A
41. Rossi, P. E., Allenby, G. M., & McCulloch, R. (2005). *Bayesian Statistics and Marketing*. Wiley.
    https://doi.org/10.1002/0470863692
42. Vovk, V., Gammerman, A., & Shafer, G. (2005). *Algorithmic Learning in a Random World*. Springer.
    https://doi.org/10.1007/b106715
43. Angelopoulos, A. N., & Bates, S. (2023). Conformal prediction: a gentle introduction. *Foundations and
    Trends in Machine Learning* 16(4), 494–591. https://doi.org/10.1561/2200000101
44. Barber, R. F., Candès, E. J., Ramdas, A., & Tibshirani, R. J. (2023). Conformal prediction beyond
    exchangeability. *The Annals of Statistics* 51(2), 816–845. https://doi.org/10.1214/23-AOS2276
45. Tibshirani, R. J., Barber, R. F., Candès, E. J., & Ramdas, A. (2019). Conformal prediction under covariate
    shift. arXiv:1904.06019. https://arxiv.org/abs/1904.06019
46. Koenker, R., & Bassett, G. (1978). Regression quantiles. *Econometrica* 46(1), 33–50.
    https://doi.org/10.2307/1913643
47. Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*
    102(477), 359–378. https://doi.org/10.1198/016214506000001437

### Censored regression, control, change detection, online learning

48. Amemiya, T. (1984). Tobit models: a survey. *Journal of Econometrics* 24(1–2), 3–61.
    https://doi.org/10.1016/0304-4076(84)90074-5
49. Besbes, O., Gur, Y., & Zeevi, A. (2015). Non-stationary stochastic optimization. *Operations Research* 63(5),
    1227–1244. https://doi.org/10.1287/opre.2015.1408
50. Crook, J. N., & Banasik, J. (2004). Does reject inference really improve the performance of application
    scoring models? *Journal of Banking & Finance* 28(4), 857–874. https://doi.org/10.1016/S0378-4266(03)00203-6
51. Dudík, M., Erhan, D., Langford, J., & Li, L. (2014). Doubly robust policy evaluation and optimization.
    *Statistical Science* 29(4), 485–511. https://doi.org/10.1214/14-sts500
52. Killick, R., Fearnhead, P., & Eckley, I. A. (2012). Optimal detection of changepoints with a linear
    computational cost. *JASA* 107(500), 1590–1598. https://doi.org/10.1080/01621459.2012.737745
53. Lattimore, T., & Szepesvári, C. (2020). *Bandit Algorithms*. Cambridge University Press.
    https://doi.org/10.1017/9781108571401
54. Li, L., Chu, W., Langford, J., & Schapire, R. E. (2010). A contextual-bandit approach to personalized news
    article recommendation. *WWW '10*, 661–670. https://doi.org/10.1145/1772690.1772758
55. Page, E. S. (1954). Continuous inspection schemes. *Biometrika* 41(1–2), 100–115.
    https://doi.org/10.1093/biomet/41.1-2.100
56. Peskir, G., & Shiryaev, A. N. (2006). *Optimal Stopping and Free-Boundary Problems*. Birkhäuser.
    https://doi.org/10.1007/978-3-7643-7390-0
57. Plackett, R. L. (1950). Some theorems in least squares. *Biometrika* 37(1–2), 149–157.
    https://doi.org/10.1093/biomet/37.1-2.149
58. Russo, D. J., Van Roy, B., Kazerouni, A., Osband, I., & Wen, Z. (2018). A tutorial on Thompson sampling.
    *Foundations and Trends in Machine Learning* 11(1), 1–96. https://doi.org/10.1561/2200000070

---

## 12. What I left unresolved

Ordered by what would change the build first.

**Operator questions, all of them cheap to answer and some of them decisive.**

1. **Q3 from the decision log — is the cap enforced on-chain or by the platform's matching engine?** This is no
   longer a curation question: it decides whether the value model's likelihood is truncated or censored (§4.3),
   and whether a mass point at the cap should exist in the data at all. One sentence from whoever built the
   transfer path settles it, and the first real data dump settles it independently.
2. **Does `issuedCount` mean minted or sold, and is `faceValueLamports` the primary transaction price or a
   nominal face?** Both are load-bearing for 01-b's demand bracket, which is the only identified demand object in
   the schema and therefore the only input the revenue-management layer has (§2). Recorded in 01-b §5 as an open
   question; it has not been answered and this report cannot proceed past a bracket without it.
3. **Seat coordinates (Q1).** Not needed by the repeat-sales index, fatal to the cross-sectional hedonic (§4.2).
4. **The fee stack (D4).** Needed for the CVaR objective in §9.4 and for participation, not for the resale ask,
   which is fee-neutral under an ad-valorem fee (01-b §4.5(i)).
5. **Is `transferRestricted` actually enforced?** If off-ledger key handoff is common, the ledger is a *sample* of
   transfers rather than a census, and every hazard in §3 is a hazard of the observable subset. 01-a §6 lists the
   dark-ticket test; it has not been run because there is no data to run it on.
6. **Will the platform ever vary a price for the purpose of learning, or authorise a randomised arm?** This is
   the only route to a causal price response (§6.3, §10.11) and it costs revenue, so it is a money decision.
7. **The mechanism fork (§5.4):** a pricing engine, or a recommendation to auction the top of the inventory. I
   recommend nothing here. It is an architecture decision that changes the deliverable, and the honest
   prerequisite is reading both papers behind the "roughly doubled" versus "3.4%" conflict, which I did not do.

**Cheap tests that need no new fields and should run on the first real data dump.**

8. **Within-tier variation in `faceValueLamports`.** If it is zero, the primary price is static per tier and
   Phase 5's dynamic-pricing question collapses to one static optimisation (§1.4(4)).
9. **A mass point at exactly `resalePriceCapBps`.** Present means policy-enforced (censored); absent means
   transfer-enforced (truncated) (§4.3). Also answers Q3.
10. **Price dispersion within a tier, compared across events grouped by `cap_bps`.** The first look at whether
    the cap binds and where.
11. **Redeemed-by-issuee fraction.** A free lower bound on the attended fraction, hence on `u > 0` (§2.2).

**Things I could not settle in this pass.**

12. **The between-event variance `τ²`.** Everything in §7 hinges on it and none of it can be quantified without
    events. I have deliberately quoted no number for how wide a cold-start interval would be.
13. **Whether the state-space model in §7.4 is better than the `τ`-spline in §4.6.** This is an empirical
    question, it is resolvable by prequential comparison on whatever data arrives, and I have pre-registered it as
    such (F8 in §10).
14. **A verified citation for Dawid's prequential paper.** Dropped rather than guessed (§11).
15. **No ticket-market paper's full text was read in this pass.** Every class-A claim is inherited from `01-a`'s
    reading. If any single claim in this report needs an independent check before it is relied on, it is the
    "roughly doubled performer revenues" figure in §5.4, because it is the one number that could redirect the
    whole programme.

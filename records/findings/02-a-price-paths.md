# Phase 2-A: the secondary price path over time-to-event, and what can honestly be forecast

**Status:** complete (first pass). **Written:** 2026-11-07T11:20Z. **Agent:** Phase 2-A research agent.
**Scope:** `RESEARCH-PROGRAM.md` §3 Phase 2, domain A (secondary-market price discovery) restricted to the
time-to-event path, and domain B (historical price forecasting) restricted to what the path can support.
**Depends on:** `AGENTS.md`; `RESEARCH-PROGRAM.md` §3 Phase 2 A/B and §4 in full; `records/README.md`
(evidence classes); `records/00-data-situation.md` (the observation set); `records/findings/01-a-market-
structure.md`; `records/findings/01-b-identifiability.md` (T2 in particular); `records/F-decision-log.md`
(D2, D3). **Append-only.** Disagreements with 01-a and 01-b are in §9 and are recorded, not resolved
silently. No number below comes from `lib/mock/`.

**Marking convention used throughout.** Every load-bearing claim carries one of two markers and one
evidence class:

- **[MEASURED]**: read from a named source, or computed arithmetically from numbers printed in that
  source. The source is named in the same row or sentence. Arithmetically derived numbers are labelled
  *derived* and the arithmetic is shown or reproducible from the numbers given.
- **[ASSERTED]**: my reasoning, a specification choice, a hypothesis, or a transfer from another market.
  No measurement stands behind it.

Classes are §4.3: **A** ticket-market evidence, **B** related-market evidence, **C** theory or established
methodology, **D** plausible untested hypothesis, **E** speculative. Plus **SIM** and **UNVALIDATED** as
in `records/README.md`. A claim can carry two classes where a measured input supports a theoretical
inference; the weaker of the two governs how the claim may be used.

---

## 1. What I concluded

1. **The decline is real and its direction is measured twice over, but it is a seller-side object, not a
   demand object.** Sweeting's MLB data show demand curves that are approximately time-invariant and
   cannot be rejected as such, while every percentile of the implied opportunity cost falls monotonically
   as the game approaches. The path falls because the seller's reservation falls, not because buyers get
   cheaper to find. [MEASURED, class A] §5.3.
2. **No study in this literature reports a decay function, a half-life, or an elasticity with respect to
   time-to-event.** Every one reports day or period dummies, or a verbal direction. There is therefore no
   published number that can be dropped into a model as a rate. [MEASURED as an absence, class A for the
   record, D for any inference from it] §3.4.
3. **Fitting the published dummies answers the shape question, and the answer is not exponential.** On
   Sweeting's own within-seller table, a constant proportional decline (log price linear in days) reaches
   R² 0.55 to 0.69. A deadline-convex form, log price linear in log(d+1), reaches R² 0.90 to 0.97 with a
   single exponent of 0.133 to 0.164 that is stable across high-demand, low-demand, cheap and expensive
   seats. The implied fall over the 81-day window is 36% to 43%, and it is proportional, not additive.
   [MEASURED as arithmetic on his printed coefficients, class A for the table, C for the fit, D for any
   transfer to a different market] §3.1 to §3.3.
4. **The competing evidence is a footnote, and it points the other way in the last week.** Leslie and
   Sorensen, on transaction prices for 56 concerts in 2004, report that prices conditional on seat quality
   "decline slightly as the event date approaches, with a modest uptick in the last week before the
   event". They give no magnitude. Lee et al. (2023), on StubHub listing prices for MLB with 19,155
   observations, find the opposite for the final day: no significant time effect two days out, then a
   relatively dramatic drop on game day. Two peer-reviewed studies, two markets, two measures, opposite
   signs in the last 48 hours. The conflict is recorded, not resolved. [MEASURED, class A] §3.5.
5. **The custody trail buys exactly one identification and it is narrower than "the path".** Repeated
   observations on the same ticket give a within-ticket first difference, which differences out the ticket
   fixed effect (tier, seat, serial, event, face value) and identifies a *price-change index*. It does not
   give the level (only ratios), it does not give a counterfactual path for a ticket that never resold,
   and it does not break the age-period-cohort collinearity: from one event window, calendar time and
   time-to-event move together exactly. Curvature is identified. Slope is not. [ASSERTED from 01-b's T2,
   class C] §4.
6. **Three different objects get called "the path", and our ledger observes the one with the opposite
   conditioning to Sweeting's.** He measures the posted price of a listing that failed to sell and was
   relisted. We measure the price of a transaction that cleared. If sellers cut only when they fail to
   sell, his decline measures the failure branch and ours measures the success branch, and the two
   magnitudes are not comparable. This is the single most consequential methodological point in this
   report. [ASSERTED, class C] §4.4.
7. **The mechanism is two forces in opposite directions at the deadline, and the measured net is a
   decline.** The seller's option value decays (that is Sweeting's finding), and buyer arrivals rise: 25%
   of concert resales occur in the final 7 days while the 19 days before that carry another 25%, a derived
   per-day arrival rate 2.7 times lower. Sellers win, so prices fall; the deadline-hazard parameterisation is
   therefore about the *seller's* hazard, not the buyer's. [MEASURED for both inputs, class A; ASSERTED for
   which dominates in any market we have not measured, class D] §5.3.
8. **What our columns can and cannot test.** The rate of sales per ticket-day at risk, as a function of
   time-to-event, is identified (01-b §4.3; the composite offered-then-bought intensity per
   `02-c-sale-hazard.md`) and is the side door: it tests the deadline mechanism without needing a price.
   The *curvature* of the price path is identified. The *slope* is identified only under a declared
   normalisation, and the honest deliverable is therefore a bracket over that normalisation, not a point.
   [ASSERTED, class C] §4.3, §8.5.
9. **Under the cap the observed path is `min(latent, cap)`, which biases the measured decline toward
   zero**, and it removes the top of the distribution on exactly the events where value is highest. What
   survives is the lower part of the distribution, the cap-hit share as a function of days-to-event, and
   the date at which the cap mass disappears. That last one is a known-price crossing and is the only
   level anchor anywhere in the data. [ASSERTED, class C; the mass point itself is measured by 01-b's
   argument, class B] §6.
10. **The path must be carried in log absolute money at the point of decision, not in log markup.** The cap
    is a basis-point spread over the face value that the primary decision will change, so a path expressed as
    `price/face` cannot be handed to a primary-price optimiser: moving the primary price moves the
    denominator of the model's own output. The curvature can be *estimated* in either normalisation, because
    the two differ only by an event-tier constant; it must be *converted* to money before the cap is applied.
    [ASSERTED, class C] §6.2, §7.2, §8.1.
11. **The mean observed markup is a late-window object and cannot be used as the secondary anchor for the
    primary decision.** Half of all resales happen inside 26 days of the event and a quarter inside 7. Under
    the fitted shape those sales occur at roughly 82% to 85% and 67% to 72% of the price at the start of a
    90-day window respectively. Using the observed mean therefore understates the value at the moment the
    primary price is set, by an amount that is large relative to the 3.4% of primary revenue that
    repricing the top seats is worth. [MEASURED for the timing and the shape, class A; the composite is
    derived, class C] §7.1.
12. **Ship one estimated parameter.** A deadline-convex path anchored on the event-tier's own most recent
    transactions, fitted by within-event regression with a free linear term that absorbs the unidentified
    direction, scored by event-level walk-forward in log space against a martingale benchmark. If it does
    not beat the martingale, ship the martingale. That is the whole model and a person can defend it line
    by line. [ASSERTED, class C] §8.

---

## 2. What "the price" is in each study, because it decides whether the number transfers

Three distinguishable objects are called a price path. They are not the same random variable and they do
not have the same expectation.

| Object | Conditioning | What a decline in it means |
|---|---|---|
| **Asking price at time d** | a listing is (or was) posted at d | sellers think the clearing price is falling |
| **Transaction price at time d** | a trade occurred at d | the marginal seller's reservation met the marginal buyer's value at d |
| **Transaction price at d given the ticket failed to sell earlier** | a trade occurred at d *and* did not occur before d | a selected survivor's settlement, not the value of a random ticket |

Sweeting's headline within-seller declines are the third object: a listing that stayed unsold to the next
period and was relisted at a lower price. Leslie and Sorensen's prices are the second: eBay and StubHub
transactions, price including shipping and fees. Lee et al. collect StubHub *posted* prices four times per
game, which is the first object. Our ledger records the second only, and only on the success branch, with no
asking price anywhere in the record (01-b §5.2).

Consequence for this programme: **the decline magnitudes in the literature are prior beliefs about the sign
and the rough order of magnitude. They are not estimates of our parameter, and the transfer from 2007 eBay
MLB relistings to a wallet-bound Solana-ticketed event in the 2020s is class D until measured.**

[ASSERTED, class C for the taxonomy, D for the transfer]

---

## 3. The evidence, with numbers, and where each number comes from

### 3.1 Sweeting (2012): MLB 2007, the anchor study

Source read: author's accepted manuscript PDF, dated January 2012, from
`https://econweb.umd.edu/~sweeting/SWEETING_PDECLINE_0112.pdf`; published as *JPE* 120(6):1133-1172,
doi:10.1086/669254. Page and table numbers below are the manuscript's, not the typeset article's.

| Claim | Number, as stated in the source | Measure | Class |
|---|---|---|---|
| Sample | All eBay and StubHub listings for MLB 2007, 1 Jan to 30 Sep 2007, all 2,346 games (excluding Colorado Rockies home games and 3 Tampa Bay games played in Orlando) | not applicable | A |
| eBay listings | 178,659 fixed-price listings, price measured on the day the listing was posted | asking | A |
| eBay transactions | 290,410 transactions in any sales format; 50,602 of them fixed-price, 239,808 non-fixed-price | transaction | A |
| StubHub | 66,236,993 daily listing observations; the author states explicitly that he has "daily listing (not transaction) information" for StubHub, 89% of potential game-day downloads collected | asking | A |
| Demand model sample | 113,186 listing observations, sale dummy mean 0.293 | transaction | A |
| Headline | sellers "cut prices dramatically, by 40% or more, as an event approaches" | within-seller, asking | A |
| Value of dynamic pricing | "raising the average seller's expected payoff by around 16%" | model counterfactual | A |
| Within-seller declines | observed 13%, 18% and 40% of face value across successive relistings; his fitted DP model predicts 12%, 21% and 26% | asking, same seller-section-row | A |
| Within-seller cuts, final month | "between 85% and 90% of face value in the month before the game" (Fig. 2c), and in a later passage "between 90% and 100% of face value in the month before the game" for the experienced-versus-inexperienced comparison (Fig. 2d). Both sentences are in the manuscript and refer to different figures; I did not reconcile them and neither should anyone quoting one alone | asking | A |
| Direction of individual changes | 80% of eBay and 89% of StubHub price *changes* are reductions (text); 78.1 to 85.2% (eBay, Table A3) and 86.4 to 90.2% (StubHub, Table A2) across the four ticket-type columns | asking | A |
| Are transaction prices different? | "both fixed prices and transaction prices (on eBay) decline significantly as a game approaches"; non-fixed-price transaction prices also decline | transaction | A |
| Opportunity cost, successive periods | declines of 18% (SE 2%), 19% (3%) and 68% (3%) of face value when a listing remains unsold from one period to the next | derived from prices | A |
| Opportunity cost, cross-section | 77.2% of relisted tickets have a lower implied opportunity cost at the later listing; every percentile of the distribution falls monotonically; about 25% of final-period opportunity costs are significantly negative | derived from prices | A |
| Opportunity cost, level | median 29% of face in the final period, mean 55% | derived from prices | A |
| Demand over time | "demand is approximately time-invariant"; the hypothesis that demand does not change with days-to-go "cannot be rejected"; no evidence that a higher current price changes future demand or future competition | model estimate | A |

Two things in that table matter more than the rest for us.

First, **the decline is not an asking-price artefact in his data.** He has transaction prices and reports
that they decline too. So the asking-versus-realised wedge, which is the organising problem of Phase 2A in
the literature, does not explain the decline. [MEASURED, class A]

Second, **the mechanism is supply-side.** Time-invariant demand plus falling opportunity cost equals a
declining price. The seller's reservation is what moves. That has a direct consequence for our engine: the
observed transaction path is a path of *marginal reservations*, not a path of values, and a ticket's value
to its owner (which is what a primary-price decision is trying to read) is the upper envelope of use value
and reservation, not the recorded price. [MEASURED for the inputs, ASSERTED for the consequence, class C]

### 3.2 Leslie and Sorensen (2014): 56 concerts, 2004, transaction prices

Source read: *RES* 81(1):266-300, doi:10.1093/restud/rdt033, typeset PDF from
`https://users.ssc.wisc.edu/~atsorensen/papers/resale.pdf`.

| Claim | Number, as stated | Measure | Class |
|---|---|---|---|
| Sample | 56 concerts, 12 artists, 2004; 1,034,353 primary tickets (the universe, Ticketmaster sole seller); 51,318 tickets resold on eBay or StubHub | transaction | A |
| Resale rate | 5% of purchased tickets resold; the most active event reached 17%, with resale revenue equal to 37% of that event's primary revenue | transaction | A |
| Price level | average markup 41% over face; 25% of resold tickets above +67%; 26% sold below face; brokers lost money on 21% and non-brokers on 31% | transaction | A |
| Selection | mean seat-quality percentile 0.61 for resold tickets versus 0.50 for primary buyers | transaction | A |
| **The path** | "we find that prices (conditional on seat quality) change relatively little: they decline slightly as the event date approaches, with a modest uptick in the last week before the event" (footnote 20, p.276) | transaction | A |
| Timing of resales | "50% of resale transactions occur within 26 days of the event, and 25% of resale transactions are within 7 days" | transaction | A |

The path sentence is a **footnote**, gives **no magnitude**, and is explicitly contrasted with Sweeting in
the same sentence. It is class A evidence that the direction is not uniform, and it is not evidence about
any rate. Anyone citing "a modest uptick in the last week" as a calibrated feature is over-reading a
qualitative aside. [MEASURED, class A]

The timing numbers are the more useful measurement in that paper for us, and they are stated as fact: see
§5.3 and §7.1.

### 3.3 What the published dummy coefficients say about the shape

Sweeting's Table 2 (manuscript), "Within-Seller Price Changes for Particular Types of Ticket Using Fixed
Price Listings on eBay", reports, for four subsamples, an average price 0 to 2 days before the game and nine
day-bucket dummy coefficients. The figure note states that the plotted path is the dummy coefficient **plus**
the average price in the last two days, so the coefficients are in relative-price *level* units, not logs.
That is confirmed by the magnitudes: adding 1.518 to 2.014 gives 3.53 times face at 81+ days, which is
plausible; exponentiating would give 9.2 times face, which is not.

Taking the nine interval midpoints (4, 7, 10, 16, 22, 31, 40, 53, 81 days) and adding the base:

| Subsample | p(0-2 d) | p(81+ d) | Change over window | R², log p ~ d | R², log p ~ log(d+1) | R², log p ~ 1/(d+1) | θ in log p = a + θ log(d+1) |
|---|---|---|---|---|---|---|---|
| High demand games | 2.014 | 3.532 | −43.0% | 0.615 | 0.934 | 0.968 | 0.162 |
| Low demand games | 0.932 | 1.611 | −42.1% | 0.695 | 0.968 | 0.908 | 0.164 |
| Cheap seats (≤$20) | 1.834 | 2.853 | −35.7% | 0.638 | 0.949 | 0.934 | 0.136 |
| Expensive seats (≥$45) | 1.431 | 2.252 | −36.5% | 0.547 | 0.899 | 0.980 | 0.133 |

All entries [MEASURED as arithmetic on Sweeting's Table 2; class A for the table, C for the fits]. This is a
two-parameter OLS per column on nine published points, with no standard errors carried over and no access to
his micro data. It is a re-description, not a new estimate. It says three things:

1. **A constant proportional decline is rejected.** If log price were linear in days, the per-day rate would
   be constant; it is not. In the high-demand column the implied decline is 8.5% per day between days 2 and
   4, 4.8% per day between days 4 and 7, 1.4% per day between days 7 and 10, and 0.14% per day between days
   53 and 81. That is a factor of roughly 60 between the final week and two months out. [MEASURED as
   arithmetic, class C]
2. **The decline is proportional, not additive.** High-demand games fall 43.0% and low-demand games 42.1%
   over the same window from levels that differ by a factor of 2.2; cheap and expensive seats fall 35.7% and
   36.5%. An additive decay would predict absolute declines that differ with the level; a multiplicative one
   predicts percentage declines that do not. Fit and forecast in logs. [MEASURED as arithmetic, class C]
3. **One exponent describes all four columns.** θ ranges 0.133 to 0.164 across subsamples whose levels
differ by up to 2.2x. That is the empirical case for a single-exponent shape rather than a separate
curve per demand state. [MEASURED as arithmetic, class D as a general claim; four numbers is not a
   distribution]

The hyperbolic form (log price linear in 1/(d+1)) fits slightly better than the power form for high-demand
and expensive seats and slightly worse for low-demand and cheap seats. Both are deadline-convex and both
beat the exponential by a wide margin. With nine points I cannot discriminate between them and I do not
claim to. [ASSERTED, class C]

### 3.4 What the literature does not give

[MEASURED as an absence across the sources I read in full or checked by abstract; class A for "these studies
do not", D for "no study does"]

- **No fitted decay function, half-life, or time-elasticity.** Sweeting reports day-bucket dummies and a
  structural DP model whose *predicted* prices fall 202% to 190% to 169% to 143% of face by period, but
  those are model outputs at four re-listing dates, not an estimated continuous function. Lee et al. report
  day dummies. Leslie and Sorensen report a direction in a footnote. Nobody reports a rate.
- **No repeat-sale price path for individual tickets.** Sweeting's repeated observation is a *relisting* of
  an unsold listing, which is a different object from the same ticket selling twice (see §4.4). No study I
  found has a per-ticket custody trail; that is precisely what the programme says is new here.
- **No cap-constrained path.** 01-b records that it found no peer-reviewed econometric study of resale price
  caps in ticket markets, and this pass found none either. Everything about the capped path in §6 is class C
  or D.
- **No published out-of-sample forecast of secondary ticket prices.** I searched for one and found none;
  what exists is descriptive regression on time dummies. An arXiv paper I opened (2507.23767) uses a
  SeatGeek pricing dataset for distribution recovery and event classification, not for a time path, and is
  not evidence about the path. Commercial analyses of large sale samples exist (for example
  `seatdata.io/articles/best-time-to-buy-concert-tickets-2026/`, which asserts 307,727 sales and a 29%
  day-of saving) but they are unpublished, unaudited and cannot be inspected, so no number from them is used
  here. [ASSERTED, class E as a source]

### 3.5 The conflicting finding, recorded

| Study | Market | Measure | Sample | Last-week behaviour |
|---|---|---|---|---|
| Sweeting 2012 | MLB 2007 | asking, within-seller | 178,659 listings, 2,346 games | continues falling; the final week has the highest per-day rate |
| Leslie & Sorensen 2014 | 56 rock concerts, 2004 | transaction | 51,318 resales | "decline slightly ... with a modest uptick in the last week", no magnitude |
| Lee, Morse, Hyun, Shapiro & Drayer 2023 | MLB, StubHub | asking (4 snapshots) | 19,155 observations | no significant effect 2 days out; "decreased relatively dramatically on an actual game day" |

Lee et al.: *Sport, Business and Management* 13(3):397-415, doi:10.1108/sbm-05-2022-0042. I read the
abstract and the stated design and findings, **not the full text**; the numbers above are the abstract's.

The four candidate explanations, all testable and none tested here [ASSERTED, class D]:

1. **Remaining supply.** Concerts in the L&S sample sold out in the primary market (their median concert
   sold 25% of capacity on day one and under 75% in the first week), so the secondary market was the only
   supply. An MLB regular season has 81 home games and an enormous near-substitute set. If the sign of the
   last-week slope is governed by scarcity, the L&S sample is the scarce case and Sweeting's is the abundant
   case. This is the explanation the programme should adopt as its working hypothesis because it is the one
   that a *supply state* variable would let us condition on.
2. **Measure.** Asking versus transaction. Sweeting's own transaction series declines, so this cannot
   explain his result, but it could explain part of Lee et al.'s game-day drop, which is a posted-price drop.
3. **Conditioning.** L&S condition on seat quality; Sweeting's fixed effects are seller-game-section-row,
   which is coarser. A composition shift toward better seats near the event would attenuate a measured
   decline.
4. **Period and platform.** 2004 versus 2007 versus the 2020s. Nothing in the record separates this from the
   others.

What this means for the engine, stated plainly: **the sign of the last-week slope is not settled by the
literature, so a model may not promise a direction in the final week.** It may fit one to our own data, and
until it has, the honest output for the last week is the martingale with a wide band. [ASSERTED, class C]

---

## 4. Index versus forecast: what the custody trail buys, and what it forbids

### 4.1 The identification primitive

For ticket $i$ observed twice at times $t_{i1} < t_{i2}$ with prices $p_{i1}, p_{i2}$:

$$\Delta_i \equiv \log p_{i2} - \log p_{i1} = \left[g(t_{i2}) - g(t_{i1})\right] + \left[\eta_{i2} - \eta_{i1}\right]$$

where $g(\cdot)$ is the common log-price level (the index) and $\eta$ is ticket-specific noise. The ticket
fixed effect, which is everything about the ticket that does not change (tier, section, row, seat, serial,
face value, event), differences out. This is the Bailey-Muth-Nourse repeat-sales estimator, and it is
unusually clean here for a reason 01-b states and I confirm: the BN assumption that asset quality is
unchanged between sales is *literally true* for a ticket, because the attribute vector is fixed at mint.
Quality change is exactly zero. [ASSERTED, class C]

So: **repeated observations on the same ticket identify a price-change index, and nothing else.** The index
is a set of ratios. It has no level.

### 4.2 What it does not buy, in order of how much damage each does

1. **The level.** A repeat-sales index is invariant to multiplying every price by a constant. The natural
   anchor, face value, is endogenous: it is the primary seller's choice and the denominator of the markup
   being measured, and a primary-price decision changes it. 01-b's T1 already establishes that an affine
   indeterminacy needs one exogenous anchor and that the observation set contains none. [ASSERTED, class C]
2. **The counterfactual path for a ticket that did not resell.** A ticket that sells once has one
   observation; a ticket that never sells has none. Its path is not "flat", it is unobserved, and there is
   no exchangeability argument that recovers it because the reason it did not sell is correlated with its
   price. 01-b's T1′ covers the cold-start version. [ASSERTED, class C]
3. **The split between calendar time and time-to-event.** This is the point that governs the whole
   specification and it deserves to be stated exactly. Let $a$ be age (days to the event), $k$ the cohort
   (the event's own date) and $c$ the period (the calendar date of the sale). They satisfy the identity
   $c = k + a$: a sale 10 days before a 12 June event happens on 2 June, always. Now add a linear term
   $t\,a$ to the age effect, $t\,c$ to the period effect and subtract $t\,k$ from the cohort effect. The
   three changes sum to $t(a + c - k) = 0$ by the identity, so every fitted value is unchanged and the
   linear component is not identified. Within one event window this is worse than a nuisance: age and
   period are the same variable up to a constant, so *nothing* inside a single event separates them.
   Across events with staggered dates the panel is richer but the dependency is exact, so the linear
   component still is not identified and only curvature and event-specific deviations are. This is the
   Mason et al. result and the reason the APC literature converged on bounds rather than point estimates.
   [ASSERTED, class C, sources in §Sources]
4. **The ask.** There is no asking price in the record. Everything in the literature about listing revision,
   seller competition and price discovery through asking is unavailable here (01-b §5.2). [MEASURED as an
   absence, class A]

### 4.3 What is identified, stated so an engineer can act on it

Take as the object of interest the within-event log-price profile $\mu_e(d)$ for days-to-event $d$. Write

$$\mu_e(d) = \alpha_e + \beta_e\, d + \theta\,\phi(d)$$

with $\alpha_e$ an event intercept, $\beta_e$ a free event-specific linear slope, and $\phi$ a curvature
basis (for example $\phi(d) = \log(1+d)$). Then:

- **$\theta$ is identified.** It is the curvature of the profile, and no reparameterisation of the linear
  direction changes it. This is what "curvature is identified" means concretely, and it is the *only*
  structural parameter the data supports.
- **$\beta_e$ is not identified.** It is the linear component and it is confounded with a common calendar
  drift by construction. Including it in the fit is necessary (it stops the curvature estimate being
  contaminated) and using it in a forecast requires a declared normalisation.
- **$\alpha_e$ is identified for an event with sales**, and it is the anchor. It is not identified for an
  event without sales.

Therefore: **(a)** fit with a free $\beta_e$, **(b)** report $\theta$ as the identified object, **(c)**
forecast with $\beta$ set to one of its two extreme values and report both. Concretely, $\omega = 0$ means
"attribute no within-event level movement to the linear age effect" (the conservative reading: use only the
identified curvature), $\omega = 1$ means "attribute all of it to age" (the aggressive reading, which is
what a naive trend fit does silently). The pair is the bracket. [ASSERTED, class C]

A diagnostic that does not require estimating the confounded parameter: **if residual level shifts are
shared by events that are live on the same calendar date, then a common period effect exists and the
normalisation is doing real work.** Compute the correlation of residuals across events by calendar week. If
it is near zero, the bracket collapses and the point estimate is safe. Nobody in this literature reports
that diagnostic and it should be in ours. [ASSERTED, class C]

### 4.4 The conditioning inversion, which is the report's main warning

Sweeting's within-seller path is estimated on listings that **did not sell and were relisted**. His own
sentence: opportunity costs "decline ... when a listing remains unsold from one period to the next", and
77.2% of relisted tickets carry a lower implied opportunity cost at the later listing. That is a path
*conditional on failure*. It answers: given that my price was too high yesterday, what do I do today?

Our ledger observes sales. The path we can estimate is *conditional on success*: for the tickets that
cleared at $d$, what did they clear at? These are different conditional distributions of the same latent
process, and they are selected in opposite directions.

The practical consequences:

- **Our magnitude will be smaller than his.** A seller who cuts until the ticket sells brings the sale price
  down to just above the buyer's value; the recorded price at the moment of sale is the *intersection*, not
  the seller's descent. Averaging intersections samples the lower envelope of the ask distribution near the
  event, and the upper part of the ask distribution never appears in our data. So Sweeting's 40%+ over the
  window, measured on the failure branch, is an upper bound on what the success branch can show.
  [ASSERTED, class C]
- **For the primary decision, the success branch is the right object.** What a buyer pays on the secondary
  market is the clearing price, and that is what the primary price has to compete with. So the inversion is
  not a defect for the use case; it is a defect only for anyone who imports his numbers.
- **The two cannot be pooled.** Any dataset that mixes relisting prices with transaction prices (a scraped
  screenshot series, for example) mixes two conditional distributions.

[ASSERTED, class C]

### 4.5 What an engineer should compute, and what they must not claim

**Compute (identified, defensible now):**

1. A **within-ticket repeat-sales index**: for each event and tier, the median $\Delta\log p$ per pair of
   day-buckets, reported as ratios with the normalisation declared and the pair count shown. Report it as
   an index, never as a price.
2. The **curvature estimate $\hat\theta$** per event and pooled, with the per-event spread. The spread is
   the falsification statistic (§10.2).
3. The **sale-time distribution**: the share of sales in each day-bucket, which is fully identified because
   the ticket population is censused (01-b §4.3). This single object kills the mean-markup anchor (§7.1).
4. The **cap-hit share as a function of days-to-event**, and the last day on which a sale lands exactly on
   the cap. Both are identified and both are informative (§6).
5. The **time profile of observed sales per ticket-day at risk** with competing risks, per 01-b §4.3 and
   with the naming correction of `02-c-sale-hazard.md` (it is the intensity of a composite process,
   offered-then-bought, not a pure sale hazard). It is the side-door test of the deadline mechanism (§5.4).

**Must not claim:**

1. The level of value. Only ratios, and only up to the affine indeterminacy.
2. A per-day percentage decline without declaring $\omega$. "Prices fall 1.2% per day" is not a statement
   the data can support.
3. A path for tickets that did not resell.
4. That the observed path is a demand curve, or that its slope is a price elasticity.
5. That a recorded markup at the cap is a value (§6).
6. That the observed path is what a ticket was "worth" at $d$. It is the price at which a selected
   transaction occurred.

---

## 5. The shape question: two parameterisations, one mechanism, and what is testable

### 5.1 Parameterisation A: constant concession (exponential decay)

$$\log p(d) = a + \lambda\, d$$

One parameter. The proportional concession per day is constant: every day the seller gives up the same
fraction. Equivalently, the price at which a given ticket clears has an exponential time profile, and the
"half-life" of the price is $\ln 2/\lambda$ days. This is the default in perishable-goods forecasting because
it is what a memoryless arrival process plus a fixed markdown rule produces, and because one parameter is
one parameter.

What it implies and what is wrong with it: a constant hazard of price concession means the *last* day is no
different from the *first*, so the model cannot generate the observed pattern in which the final week does
most of the work. On Sweeting's table it reaches R² of 0.55 to 0.69 against 0.90 to 0.97 for the convex
forms. It is not a bad first approximation; it is a wrong shape. [MEASURED as arithmetic, class C]

### 5.2 Parameterisation B: deadline convexity (the hazard rises as the deadline approaches)

Three variants, in increasing order of realism and parameter count:

- **B1, power.** $\log p(d) = a + \theta \log(1 + d)$. The per-day proportional concession is
  $\theta/(1+d)$, which is largest at $d = 0$ and decays as the horizon lengthens. One shape parameter.
  Fits Sweeting's table at R² 0.90 to 0.97 with $\theta$ in 0.133 to 0.164. It has no floor and a bounded
  slope at the deadline, so it cannot produce a discontinuous game-day drop; where a floor is plausible
  (B2), B1 is a local approximation only.
- **B2, hyperbolic with a floor.** $p(d) = u + \kappa (1+d)^{-\psi}$. Three parameters, but it has the right
  limit: the price tends to a use value $u$ at the deadline, not to zero. Sweeting's own data support a
  floor: the fitted price at 0 to 2 days is 2.014 and 0.932 times face for high and low demand, not zero,
  and he reports that about 25% of final-period opportunity costs are significantly negative, which he
  attributes to sellers who set prices near face for non-pecuniary reasons. A floor is measured, in other
  words, though its level is not pinned. [MEASURED for the level at 0-2 days, class A]
- **B3, deadline step.** $p(d) = a - \gamma\,\mathbf{1}\{d \le 1\}$. One parameter plus a threshold. This is
  what Lee et al. actually measure: nothing significant at two days out, a dramatic drop on game day. It is
  the crudest statement of "the hazard concentrates at the deadline" and it is the one the data most
  directly supports, because the snapshot design samples 3, 2, 1 and 0 days.

**The mechanism, stated so it can be attacked.** The seller's reservation equals the value of continuing to
wait, and the value of waiting is the probability of finding a buyer before expiry times the price that
would be obtained. With buyers arriving at a roughly constant rate $\nu$ and a seller who must clear by $d$,
the probability of at least one arrival is $1 - e^{-\nu d}$, which is small for small $d$ and rises toward
1 as $d$ grows. The outside option therefore shrinks as the deadline approaches, the reservation falls, and
the *rate* at which it falls is highest at the deadline. This is the standard finite-horizon perishable-
inventory result (Gallego and van Ryzin 1994, and the class of models Sweeting calls "simple DP models"),
and it is why the correct shape is convex rather than linear. [ASSERTED from the theory, class C; the
mechanism is what Sweeting tests and cannot reject, class A]

### 5.3 The two forces, because only one of them is the seller's

The mechanism above is about the seller's side. The buyer's side moves the other way, and the measured
evidence for that is direct:

From Leslie and Sorensen's stated shares: 25% of resale transactions occur within 7 days of the event and
50% within 26 days. The 19-day band from day 26 to day 8 therefore carries 25 percentage points of all
trades, which is 1.32 points per day, while the final 7 days carry 3.57 points per day. **The arrival rate
per day in the final week is 2.7 times the rate in the three weeks before it, on their own reported shares,
with no assumption about the length of the sales window.** [MEASURED as arithmetic, class A]

So at the deadline arrivals rise (pushing price up) and reservations fall (pushing price down). The measured
net, in both MLB studies and in the concert sample overall, is a fall. The seller side dominates. But this
is exactly why the L&S uptick is credible rather than an anomaly: it is the case where scarcity is severe
enough that the arrival effect wins. **Any model that hard-codes a decline is assuming the outcome of a
race that the literature shows can go either way.** [ASSERTED, class C, class D as a prediction for our
market]

### 5.4 Which of these is testable with our columns, and which is not

| Statement | Testable with the ledger? | Why |
|---|---|---|
| Does the path have curvature, and which sign? | **Yes.** | Curvature is identified (§4.3). Fit A, B1 and B3 with a free within-event linear term and compare out-of-sample error. |
| Constant concession (A) versus deadline convexity (B)? | **Yes.** | The comparison is a test on curvature, which survives the APC confound. |
| The per-day rate, or a half-life | **No, not without a declared normalisation.** | The linear component is confounded with calendar drift. Report a bracket. |
| The floor $u$ | **Yes, if sales occur on the last day**, which they do on an active platform. | The level at $d \approx 0$ is observed, up to the level indeterminacy; the *ratio* of the last-day price to the mid-window price is identified. |
| Does the rate of sales per ticket-day at risk rise as the deadline approaches? | **Yes, and it is the strongest test available to us, but it is one-sided.** | The denominator is censused, so the time profile of observed sales is identified (01-b §4.3) and needs no price at all. `02-c-sale-hazard.md` correctly insists this is the composite offered-then-bought intensity: a *falling* profile refutes the deadline story outright, while a rising one is consistent with it and does not prove it |
| Is the decline driven by seller reservation rather than buyer demand? | **No, not from prices alone.** | Needs the demand curve, which needs the ask (01-b, T3). |
| Does the sign flip on scarce events? | **Partly.** | The cap-hit mass is the only observable proxy for excess demand (§6.3); the sell-through state is a snapshot with no timestamp. |

The instruction that follows: **validate the mechanism on the identified object and the forecast on the
price object.** A *declining* profile of sales per ticket-day as the deadline approaches would refute the
deadline story outright: sellers conceding should clear more, not less, and buyers arriving should arrive
more, not less. A flat profile neither confirms nor refutes it, because the composite intensity cannot
separate the offering rate from the clearing rate. The informative combination is a rising profile plus a
falling price, which says sellers are conceding while the market gets busier. That test is cheap, can be
pre-registered now, and will have a usable answer before the platform has a year of history.

---

## 6. Truncation at the cap: what a per-ticket path loses and what survives

### 6.1 The structure

Let $m^*(d)$ be the latent markup multiple (price over face) at $d$ days out, decreasing in $d$. Let $c$ be
the cap in basis points over the ticket's own face. The record contains $\tilde m(d) = \min\{m^*(d), c\}$,
plus the noise the platform cannot prevent (01-a §3: side payments, wallet handoff, bundling).

Because $m^*$ declines as the event approaches, the path observed on a capped event has a specific shape: a
plateau at $c$ for large $d$, then the true path once $m^*(d) < c$. Four consequences.

**C1. The measured decline is attenuated.** Truncation removes exactly the high side at large $d$, so the
observed slope between early and late is flatter than the true one. The events where the cap binds are the
events where demand is strongest, so the engine would conclude that the hottest events decline the least,
which is the same inversion 01-a records for the level. [ASSERTED, class C]
**C2. If more than half of trades land on the cap, the median is the cap** and every central measure of the
path is degenerate. That gives a hard, checkable rule: compute the cap-hit share first, and refuse to report
a central path statistic when it exceeds 50%. [ASSERTED, class C]
**C3. The disappearing mass is a sign test that needs no level.** If the latent path is falling, the cap mass
is present at large $d$ and shrinks or vanishes as $d$ falls; a rising path predicts the reverse. The share
of sales at the cap as a function of days-to-event is therefore a test on the *sign* of the path that is
immune to both the level indeterminacy and the attenuation bias. It is one-way rather than decisive: a path
that crosses the cap more than once, or a change in trade volume concentrated at the cap, can produce the
same pattern, so the test can reject a rising path but cannot certify a falling one on its own. This is
still the single best use of the cap. [ASSERTED, class C]
**C4. The crossing date is a known-price point.** Define $d^*$ as the last day on which a sale lands at the
cap. At $d^*$, $m^*(d^*) = c$ and $c$ is *known*, not estimated. That is the only place in the whole
observation set where a latent quantity is pinned to a known number, and it gives the path an anchor at one
date per event without any exogenous reference price. I record this as a partial answer to 01-b's T1: the
general statement "the observation set contains no exogenous anchor" is right for the *level of the entire
sample* and too strong for a capped event. [ASSERTED, class C; this contradicts 01-b §4.1 as stated and is
recorded in §9]

Two caveats on C4. $d^*$ is **interval**-identified, with width equal to the gap between the last sale at the
cap and the first sale below it, so it is only as sharp as the sales are dense. And 01-a's evasion channels
mean the recorded price at the cap may be a strategic choice, which pushes $d^*$ *later* than the true
crossing (sellers keep recording at the cap while settling the difference off-ledger) and makes the mass
point an upper bound on genuine cap trades. [ASSERTED, class A for the channels]

### 6.2 Which features survive, and which do not

| Feature | Survives truncation? | Reasoning |
|---|---|---|
| Lower quantiles of log price per event and day-bucket (e.g. the 25th) | **Yes** | Truncation is one-sided from above; a low quantile of the observed distribution is the same quantile of the latent one whenever the cap mass is below that quantile (Powell 1986 for the general censored-quantile result) |
| Median of log price | **Yes if cap mass < 50%, no otherwise** | C2 |
| Mean, and any upper quantile | **No** | Exactly the censored region; biased down by construction |
| The cap mass itself, and its trajectory over $d$ | **Yes, and it is the best feature in the dataset** | C3 |
| The crossing date $d^*$ | **Yes, interval-identified** | C4 |
| The slope of the path on cap-free events | **Yes, fully** | No truncation |
| The slope of the path on capped events | **No, attenuated** | C1 |
| The level of value on capped events | **No** | Censored tail |
| Anything pooled across tiers with different face values, in markup space | **No** | The cap is a bps spread over each tier's own face, so it binds at different absolute prices; pooling markup paths compares differently truncated objects |

The positive statement: **the cap costs us the top of the distribution and the central tendency on hot
events, and in exchange it gives us a known price, a monotone sign test, and a proxy for excess demand that
the schema otherwise lacks.** That trade is worth taking, but only if the model is fitted on quantiles below
the censoring point and the cap mass is reported instead of averaged away. [ASSERTED, class C]

### 6.3 The cap mass as the missing regime variable

Leslie and Sorensen's flat path and Sweeting's decline are most plausibly separated by remaining supply
(§3.5). Our contract cannot observe remaining secondary supply: there are no listings, no depths, no asks
(00-data-situation Gap 1). The `totalSupply` / `issuedCount` pair is a snapshot and the sell-out *time* is
not recorded, so the primary cannot tell us the state at a decision moment either.

The one observable of excess demand we have is a sale at exactly the cap. It says a buyer paid the maximum
permitted price, which is a statement about the demand side that does not depend on the level being
identified. So the regime classifier the literature needs is available, weakly, in the truncation itself.
[ASSERTED, class D]

---

## 7. What a per-ticket path implies for the primary price decision

### 7.1 The mean observed markup is a late-window object

From §3.2 and §3.3: half of all resales happen inside 26 days of the event, a quarter inside 7; and the
price at 26 days is a fraction of the price at the start of the window whose size depends only on the shape
exponent and the window length. Applying the fitted $\theta$ from §3.3 to a 90-day on-sale window:

| | θ = 0.133 | θ = 0.162 |
|---|---|---|
| price at 26 days as a fraction of the window-open price | 0.851 | 0.821 |
| price at 7 days as a fraction of the window-open price | 0.724 | 0.674 |

[Derived: $((d+1)/(D+1))^{\theta}$ with $D = 90$; MEASURED for the inputs, class C for the composite, and
the window length is an assumption, so class D as a number for our platform]

The consequence is a bias with a known sign. The secondary value that matters for a primary price set before
on-sale is the value at the *start* of the horizon, which is the highest point on the path. The average
recorded markup is drawn from the end of the path, where it is lowest. **So an engine that anchors the
primary price on the observed mean markup understates secondary value at the decision moment by 15% to 18%
at the median resale time and by 28% to 33% for a sale in the final week, under the fitted shape; and it
understates it more on the events with the longest windows** (for a 120-day window the same calculation gives
18% to 22% and 30% to 36%). [ASSERTED from the two measured inputs, class C]

Why that matters in money: 01-a records that repricing the top 10% of seats to the median resale price for
those seats is worth 3.4% of primary revenue (Leslie and Sorensen's counterfactual, class A as a model
result). A 15% to 33% understatement of the secondary reference price inside that calculation is not a
rounding error against a 3.4% prize; it is a substantial fraction of the prize. [ASSERTED, class C]

### 7.2 The cap is a function of the decision, so a markup-space model cannot price anything

`resalePriceCapBps` is expressed over each tier's own `faceValueLamports`. The primary decision chooses the
face value. Therefore the ceiling in money is $p_0(1+c)$ and it moves with the decision.

Two consequences the specification has to respect:

1. **Do not hand a markup-space path to a primary-price optimiser.** The curvature can be estimated in log
   relative price or in log absolute price, because the two differ only by an event-tier constant and the
   estimate of $\theta$ is identical either way. But the *level* must be converted to money
   ($\text{face} \times e^{y}$) and the cap re-applied at $p_0(1+c)$ for each candidate $p_0$. A model whose
   output is $\log(p/p_0)$ cannot be evaluated at a $p_0$ different from the one in its own denominator,
   so it will silently answer the wrong question. [ASSERTED, class C]
2. **The cap-binding duration is an output of the pricing decision, not a property of the event.** Raising
   $p_0$ raises the ceiling in money and therefore shortens the window over which the cap binds, given the
   latent path. So the engine cannot report "this event is capped 40% of the window" as a fact; it must
   report the binding duration as a function of the candidate primary price. That is the useful object for
   the optimiser in Phase 5 and it is cheap: it is one root-find per candidate price against the fitted path.
   [ASSERTED, class C]

Note the tension with 01-b §4.5(ii), which says the cap is proportional and therefore the seller's problem
is scale-free. That statement is about the *reseller's* ask at fixed face value, and it is correct there. It
does not transfer to the primary decision, where face value is the choice variable. Recorded in §9.

### 7.3 What the engine should hand the primary-price decision

Not a number. Three objects:

1. The **path bracket** at the horizon where the primary price is set, with the normalisation labelled.
2. The **cap-binding duration as a function of $p_0$**, which is the shape of the constraint.
3. The **cap mass and its trajectory**, which is the only evidence about excess demand.

---

## 8. The specification I would implement, Python standard library only

Constraint: D2, stdlib only, no numpy, no linear algebra packages. Everything below is a closed-form
two-parameter solve per event plus an inverse-variance average. No iteration, no matrix inversion beyond
2x2, no randomness.

### 8.1 Target, stated so it cannot be misread

$$y_i = \log\!\left(\frac{p_i}{\text{face}_{g(i)}}\right)$$

for a **recorded resale** of a ticket in event $e$ and tier $g$ at $d_i$ days before the event's `startsAt`.
Relative price is a fitting convenience, not a modelling claim: $\log p$ and $\log(p/\text{face})$ differ by
an event-tier constant, so $\hat\theta$ is identical in either parameterisation and the fit can be done in
whichever is numerically stable. The normalisation matters only at the point of use: before any cap is
applied, convert back with $p = \text{face} \times e^{y}$ and place the ceiling at $p_0(1+c)$ for the
candidate primary price $p_0$ (§7.2). Never leave a forecast in markup space when the decision changes face
value.

The model predicts $y$ at a horizon $\tau$, and it is a model of **clearing prices conditional on a sale
occurring at $\tau$**. It is not a model of a ticket's value, not a model of the price for a ticket that will
not sell, and not a model of the probability of sale. Those are separate objects with different identification
status (§4.2), and the engine must label its output with which one it is returning.

### 8.2 The model

$$\hat y(\tau) \;=\; \bar y_{\text{anchor}} \;+\; \hat\theta\left[\log(1+\tau) - \log(1+d_a)\right] \;+\; \omega\,\hat\beta_e\,(\tau - d_a)$$

- $\hat\theta$: the one estimated structural parameter. Degree of deadline convexity.
- $\bar y_{\text{anchor}}, d_a$: the median log relative price and median days-to-event of the last $K$
  sales in the ticket's tier (or its event, per the ladder below). Data, not parameters.
- $\hat\beta_e$: the event's fitted linear slope. A nuisance, used only when $\omega = 1$.
- $\omega \in \{0, 1\}$: **a declared normalisation, not an estimate.** Report both. $\omega = 0$ uses only
  the identified curvature; $\omega = 1$ attributes all within-event level movement to time-to-event.
- $K = 5$ and $\delta = 1$ day: fixed a priori, not tuned. (They are constants of the specification, and
  tuning them would add two parameters the data cannot support.)

### 8.3 The estimator, in full

Per event $e$ with $n_e \ge 4$ sales: let $u_i = \log(1+d_i)$, and demean within the event
($\tilde y = y - \bar y_e$, $\tilde d = d - \bar d_e$, $\tilde u = u - \bar u_e$). Solve the 2x2 system

$$\begin{bmatrix} S_{dd} & S_{du} \\ S_{du} & S_{uu}\end{bmatrix}\begin{bmatrix}\beta_e\\ \theta_e\end{bmatrix}=\begin{bmatrix}S_{dy}\\ S_{uy}\end{bmatrix},\qquad S_{ab}=\textstyle\sum \tilde a_i \tilde b_i$$

giving $\hat\beta_e = (S_{uu}S_{dy} - S_{du}S_{uy})/\Delta$ and $\hat\theta_e = (S_{dd}S_{uy} -
S_{du}S_{dy})/\Delta$ with $\Delta = S_{dd}S_{uu} - S_{du}^2$. The residual sum of squares is
$\text{RSS}_e = \sum\tilde y_i^2 - \hat\beta_e S_{dy} - \hat\theta_e S_{uy}$, the residual variance is
$s_e^2 = \text{RSS}_e/(n_e-2)$, and the standard partitioned-regression result gives
$\widehat{\text{Var}}(\hat\theta_e) = s_e^2 S_{dd}/\Delta$.

Pool with inverse-variance weights:

$$\hat\theta = \frac{\sum_e w_e \hat\theta_e}{\sum_e w_e},\qquad w_e = 1/\widehat{\text{Var}}(\hat\theta_e)$$

Guards: require $n_e \ge 4$, $\Delta > 0$, and at least 5 days of spread in $d$ within the event; discard
events that fail and **report how many were discarded**, because a model fitted on 12 of 60 events is a
different claim from one fitted on 50.

This is a fixed-effects meta-analysis of within-event curvature, not a full mixed model; it treats the $s_e^2$
as known, which they are not, and therefore understates the uncertainty of $\hat\theta$ when events are few.
Say so in the code comment. A proper hierarchical fit is specified-not-implemented under D2.

### 8.4 The loss

Fit by least squares in log space (it is the closed form above). **Score by mean absolute error in log
space**, which is approximately the median proportional error. Three reasons: the decision is a percentage
of a price, so a $10 error on a $50 ticket and on a $500 ticket must not count the same; the cap mass makes
the residual distribution asymmetric at the top, and an absolute loss is robust to that while a squared loss
is not; and MAE in logs is directly interpretable as "the model is typically off by X%".

### 8.5 Validation: event-level walk-forward, with the two leakage boundaries named

Two boundaries exist and both must be enforced:

1. **Across events.** Two defensible rules, and the report should name which one it used. (a) *Strict*: sort
   events by `startsAt` and, for the fold that scores event $e$, fit on events whose `endsAt` is strictly
   before $e$'s first recorded sale. Nothing from $e$ or from any later event enters the fit. This is
   unimpeachable and wasteful, because it throws away every overlapping event. (b) *Prequential*: fit at a
   grid of forecast timestamps $t$, using only sales with `occurredAt` $< t$ from all events, then score the
   sales immediately after $t$. This uses the data and enforces the clock exactly, which is the leakage
   boundary that actually matters (`RESEARCH-PROGRAM` §4.8). Use (b) for the reported numbers, (a) as the
   check that (b) is not buying its result from shared calendar time.
2. **Within an event.** A prediction for a sale at $t_j$ may use only sales in $e$ with `occurredAt` strictly
   before $t_j$. The anchor must never include the sale being predicted.

Benchmarks, all computed on the same folds:

| | Benchmark | What it tests |
|---|---|---|
| B0 | $\hat y = \bar y_{\text{anchor}}$ | the martingale. This is the null the literature's own theory supplies (Deneckere and Peck's competitive-sellers-plus-strategic-buyers model predicts a martingale, as Sweeting notes) and it is the benchmark the model must beat to be worth shipping |
| B1 | $\hat y = $ event-tier mean of all prior sales | whether any time model beats a pooled mean |
| B2 | $\hat y = \hat\theta$ alone with $\bar y$ fixed at the cross-event median | the shape with no local level |
| M | the model, at $\omega = 0$ and at $\omega = 1$ | the identified part, and the aggressive normalisation |

Report: MAE by horizon band ($\tau \le 2$, $2 < \tau \le 7$, $\tau > 7$), the skill score
$1 - \text{MAE}_M/\text{MAE}_{B0}$ per band and overall, the number of events and sales in each fold, the
discarded-event count, and the empirical 5% and 95% residual quantiles per band (used as the interval, read
off rather than fitted). Also report the §4.3 calendar-shock diagnostic: the correlation of fold residuals
across events sharing a calendar week.

**Pre-registered decision rule:** if $\omega = 0$ does not beat B0 out of sample by a margin that survives
the per-event dispersion of $\hat\theta_e$, ship B0. A martingale with a measured residual band is a
defensible product and a declining trend that is not there is not.

### 8.6 Fallback ladder, by $N$, the number of prior sales in the event at prediction time

| $N$ | Anchor | What else changes | Status |
|---|---|---|---|
| $\ge 20$ and tier has $\ge 5$ | median of the last 5 tier sales | interval from within-event residuals | defensible |
| $5 \le N < 20$ | median of the last 5 event sales plus the pooled tier offset, shrunk halfway toward the event median | interval widened by $\sqrt{1 + 1/N}$ | defensible, wider |
| $1 \le N < 5$ | the single (or median of the few) event sale, plus the pooled tier offset | $\hat\theta$ from the pooled fit only; interval widened by $\sqrt{2/N}$ | weak, flagged |
| $0$ | none. Return the pooled conditional median given face value, tier rank, city and the decision-date horizon | interval inflated by the between-event variance, and the pooling weight is itself unidentified with few events (Efron-Morris), so widen; do not narrow | **UNVALIDATED.** Return the band, not a point. This is the cold-start case of 01-b T1′ and the cure component of §4.3 |

The widening factors $\sqrt{1+1/N}$ and $\sqrt{2/N}$ are declared heuristics, not derived quantities: they
are there to stop a thin anchor from being reported as a tight interval. The shrinkage weight is fixed at one
half, not estimated, because estimating it needs more groups than any deployment will have at launch.

### 8.7 Parameter count

- **Estimated: one.** $\hat\theta$, the convexity exponent.
- **Nuisances that exist only to identify it:** $\hat\beta_e$, one per event, all discarded under
  $\omega = 0$.
- **Fixed a priori, not fitted:** $K = 5$, $\delta = 1$ day, the shrinkage weight $= 0.5$, the three
  horizon bands.
- **Read off, not fitted:** two residual quantiles per horizon band.
- **If the stratified version survives validation:** two, $\hat\theta$ for cap-binding events and
  $\hat\theta$ for cap-free events (§8.8).

One estimated parameter is not modesty, it is the identification result. §4.3 says curvature is the only
structural feature the data supports, and one parameter is what curvature costs.

### 8.8 The stratification that must be reported, because it is the regime test

Estimate $\hat\theta$ separately for events with a positive cap-hit share and events with none, and report
both with their event counts. If the cap-binding stratum shows no decay while the cap-free stratum does, the
"decline" is partly a truncation artefact and the whole model needs the correction in §6 rather than a
second parameter. If both decay, the shape is real and the cap costs only the level. This is the cheapest
informal test in the report and it should run before anything else. [ASSERTED, class C]

### 8.9 The eight method families Phase 2B asks about, and what this data supports

| Family | What it needs | What we have | Verdict |
|---|---|---|---|
| ARIMA / SARIMA | a stationary per-ticket or per-event series long enough to identify orders | a ticket has 1 to 4 observations in its life; an event-tier series has a handful, and the count in our own ledger is unknown until measured | **No.** Not a data-volume objection that more data eventually fixes: with three or four points, any fitted autoregressive order is fitted noise, and the series it would difference has no identified level anyway (§4.2) |
| State space / local level | a signal plus a measurement equation | the measurement is censored and selected | Reduces to "martingale plus a drift that is not identified". Use it, name the drift a bracket |
| Bayesian / hierarchical | $\ge 2$ groups to estimate the between-group variance | at launch, few events | Yes, but only as the cold-start prior, and the interval must widen, not narrow (Efron-Morris) |
| GAM / spline in $d$ | enough points per event to place knots | Sweeting had nine day-buckets; we will have fewer, and the count is unknown until measured | Use a single-parameter basis ($\log(1+d)$), not a spline. A spline fitted to a handful of points per event is unidentifiable curvature by another name |
| Quantile regression | enough data below the censoring point | censoring at the cap | **Yes**, as the descriptive estimator for the path on capped events, below the cap mass. Powell's censored quantile regression is the reference; under D2, implement as IRLS and say it is approximate |
| Change points | a series long enough for a break to be detectable | a handful of points | **No**, with one exception: the cap-crossing date $d^*$ is a change point that is directly observable rather than detected |
| Volatility / GARCH | a return series | 1 to 4 points per ticket | **No.** Report residual dispersion by horizon band instead; that is the useful object (an interval) |
| Ensembles | several models that are individually defensible | one identified parameter | **No.** An ensemble of martingales is a martingale |

Per §4.9 the objective is the smallest thing that extracts the information, and the information here is one
number.

---

## 9. Where I disagree with 01-a and 01-b, recorded not resolved

1. **01-a §2, "Magnitudes to carry forward".** The magnitudes it carries are asking-price and within-seller
   relisting declines (§3.1), which is a path conditioned on *failure to sell*. Our ledger observes the
   success branch. Transferring the number without the conditioning is a class D move presented as class A.
   The direction transfers; the magnitude does not. See §4.4.
2. **01-a's "modest uptick in the last week".** Correctly quoted, but presented without the facts that it is
   a footnote, that it carries no magnitude, and that Lee et al. (2023) find a significant game-day drop in
   the same league. A footnote with no number is not a calibrated feature. §3.5.
3. **01-b's T2.** The identification statement is right and I adopt it. Two sharpenings. First, "curvature is
   identified" is only operational if the fit carries a free within-event linear term; without it the
   curvature estimate is contaminated by the confounded direction. Second, T2 lists the normalisation as an
   assumption but does not say what an engineer does with it. The answer is §4.3: fit with a free linear
   term, report $\theta$, bracket the forecast over $\omega$, and run the calendar-shock diagnostic.
4. **01-b §4.1, "the observation set contains no exogenous anchor".** True for the level of the sample, too
   strong for a capped event: a recorded sale at exactly the cap is a latent quantity pinned to a known
   number, and the date at which that stops happening is a known-level crossing (§6.1, C4). It does not
   recover the level, and it is interval-identified, but it is an anchor of the kind T1 says is absent.
5. **01-b §4.5(ii), "the cap is proportional, so the band is scale-free".** Correct for the reseller's ask
   at fixed face value; it does not transfer to the primary decision, which chooses face value and therefore
   moves the ceiling in money. §7.2.
6. **01-a §6, "condition the time-to-event slope on an inventory state".** Agreed and adopted, with the
   addition that the inventory state the contract can observe is the cap mass and nothing else (§6.3). The
   `totalSupply` / `issuedCount` snapshot cannot supply it at a decision moment because the sell-out time is
   untimestamped.

---

## 10. What would falsify this

Each of these is a runnable test on data we will have, and each is designed so that the answer can be "the
model is wrong".

1. **The martingale wins.** If $\text{MAE}_M \ge \text{MAE}_{B0}$ on event-level walk-forward in the
   $\omega = 0$ specification, the forecastable drift is not there. Ship B0. This is the primary
   falsification and the specification is built to be able to lose it. (§8.5)
2. **The shape is not common.** If the per-event $\hat\theta_e$ are dispersed far beyond their sampling
   error, there is no single exponent and the pooled-shape model is a fiction. Report the dispersion of
   $\hat\theta_e$ as a first-class statistic, not a diagnostic.
3. **The decay is a truncation artefact.** If $\hat\theta \approx 0$ on cap-free events and negative only on
   cap-binding events, the measured decline is an artefact of the cap and §6's correction is the model, not
   §8's. (§8.8)
4. **The normalisation is doing the work.** If residuals are strongly correlated across events live in the
   same calendar week, a common period effect is real, the bracket is wide, and the point estimate must not
   be reported. (§4.3)
5. **The mechanism is refuted.** If the rate of sales per ticket-day at risk is *lower* close to the event
   than far from it, the deadline story is inverted (sellers conceding and buyers arriving should both raise
   the rate), and the convex form has no support here regardless of what it does in MLB. (§5.4)
6. **The published magnitude does not transfer.** If our measured window-long decline is far from the 36% to
   43% the fitted shape implies, the 2007 MLB prior is void and the model must be re-estimated from our own
   ledger alone. It should be re-estimated from our own ledger alone regardless; the prior is for the
   cold-start case only.
7. **The path is flat or rising in the last week.** If our own data reproduce the L&S pattern, the shipped
   last-week forecast must be the martingale, and any model that hard-codes a decline is falsified.

---

## 11. What is unvalidated, and the experiment that would test each

| Unvalidated claim | Why it cannot be validated now | Experiment that would test it |
|---|---|---|
| The level of resale value, and therefore the ratio of secondary to primary value | no exogenous price anchor; only ratios are identified | one cap-free event with a known external quote (a cross-platform ask, a completed off-platform sale), or an event priced at a level the market cannot ration; either supplies the one location and scale the affine indeterminacy needs |
| The per-day slope of the path | exact APC collinearity; the linear component is a normalisation | find one dated common shock that moves all live events' resale prices at once (a tour cancellation, a venue change, a weather event affecting several events in a city) and treat it as a period effect; that identifies the calendar component and hence separates it |
| The path for tickets that did not resell | no second observation, and selection | the listing panel: `{listPriceLamports, listedAt, delistedAt, delistReason}` per F-decision-log D3. That is the experiment and it is four fields |
| Any forecast accuracy number | no real ledger on this machine; no historical series exists | event-level walk-forward (prequential, per §8.5) on the platform's own first season. No minimum event count is defensible in advance: with a 5% resale rate and no variance estimate, a power calculation is not possible, so the honest output is the walk-forward with its per-fold spread, labelled indicative until a second season confirms it. Until then no accuracy figure may be quoted (programme §4.6) |
| The sign of the last-week slope | the literature conflicts (§3.5); our data does not exist yet | stratify by cap-hit share and by primary sell-through state, and report the last-week slope per stratum |
| That the deadline mechanism dominates the arrival effect | the two forces are not separable from prices alone | the sales-per-ticket-day profile of §5.4 combined with a hazard model on the identified population: if the composite rate rises while the price path falls, the seller side dominates by construction. Note the one-sidedness: the composite cannot separate the offering rate from the clearing rate, so the test can reject the mechanism but cannot fully confirm it |
| That the 0.133 to 0.164 exponent transfers here | 2007 eBay MLB relistings, a different market, measure and conditioning | re-estimate $\theta$ on our own ledger; the prior is only for cold start |
| That the cap is enforced on-chain, which decides whether $d^*$ is informative | open question Q3 in the decision log | ask the operator; the answer changes whether a capped sale is impossible or merely prohibited, and therefore whether the mass point is a market fact or a recording convention |

---

## Sources

Read in full (PDF text extracted locally; no PDF toolchain on this machine, so extraction was by a stdlib
decompressor and a text-operator parser, and every number above is traceable to the extracted text):

- **Sweeting, A. (2012).** Dynamic pricing behavior in perishable goods markets: evidence from secondary
  markets for Major League Baseball tickets. *Journal of Political Economy* 120(6):1133-1172.
  doi:10.1086/669254. Author's accepted manuscript, January 2012, read at
  https://econweb.umd.edu/~sweeting/SWEETING_PDECLINE_0112.pdf. Table and figure numbers cited above are the
  manuscript's. Earlier working-paper version: NBER WP 14505, doi:10.3386/w14505.
- **Leslie, P. & Sorensen, A. (2014).** Resale and rent-seeking: an application to ticket markets. *Review of
  Economic Studies* 81(1):266-300. doi:10.1093/restud/rdt033. Typeset PDF read at
  https://users.ssc.wisc.edu/~atsorensen/papers/resale.pdf.

Abstract and stated design only (full text not read):

- **Lee, J., Morse, A., Hyun, M., Shapiro, S. L. & Drayer, J. (2023).** Does time matter? How major league
  baseball secondary market sellers make ticket pricing decisions. *Sport, Business and Management: An
  International Journal* 13(3):397-415. doi:10.1108/sbm-05-2022-0042. Abstract read via Crossref.

Methodology and theory, cited for results used in §4 and §5 (metadata verified against Crossref; not read
in full here, and no numeric result is quoted from any of them):

- **Bailey, M. J., Muth, R. F. & Nourse, H. O. (1963).** A regression method for real estate price index
  construction. *JASA* 58(304):933-942. doi:10.1080/01621459.1963.10480679. (repeat-sales estimator, §4.1)
- **Gallego, G. & van Ryzin, G. (1994).** Optimal dynamic pricing of inventories with stochastic demand over
  finite horizons. *Management Science* 40(8):999-1020. doi:10.1287/mnsc.40.8.999. (the finite-horizon
  perishable-inventory result behind the declining reservation, §5.2)
- **Mason, K. O., Mason, W. M., ~~Winship, C.~~ Winsborough, H. H. & Poole, W. K. (1973).** Some methodological issues in cohort
  analysis of archival data. *American Sociological Review* 38(2):242-258. doi:10.2307/2094398. **[CORRECTION
  2026-11-07T14:00Z, R2-20 — dead surname: Crossref returns Winsborough as third author. Title, journal, volume
  and pages are right. See CORRECTION at the end of this file.]** (the exact
  age-period-cohort linear dependency, §4.2)
- ~~**Luo, L. (2019).**~~ **Fosse, E. & Winship, C. (2019).** Analyzing age-period-cohort data: a review and critique. *Annual Review of Sociology*
  45:467-492. doi:10.1146/annurev-soc-073018-022616. **[CORRECTION 2026-11-07T14:00Z, R2-21 — dead author:
  Crossref returns Fosse & Winship for this DOI, same title, journal, volume, pages and year. See CORRECTION at
  the end of this file.]** (why every APC point estimate is a normalisation in
  disguise, and why bounds are the honest output, §4.3)
- **Powell, J. L. (1986).** Censored regression quantiles. *Journal of Econometrics* 32(1):143-155.
  doi:10.1016/0304-4076(86)90016-3. (why a quantile below the censoring point is identified, §6.2)
- **Efron, B. & Morris, C. (1975).** Data analysis using Stein's estimator and its generalizations. *JASA*
  70(350):311-319. doi:10.1080/01621459.1975.10479864. (the cold-start shrinkage limit, §8.6; carried from
  01-b)
- **Deneckere, R. & Peck, J. (2011).** as cited in Sweeting (2012), footnote 7: a model with a mass of
  competitive sellers and a mass of strategic buyers predicts prices evolve as a martingale. **I did not
  read this paper.** It is cited here only because it supplies the martingale as the theoretical null in
  §8.5, and the null is also the honest empirical default without the theory.

Checked and not used:

- arXiv:2507.23767, Landers, *Closed-Form Beta Distribution Estimation from Sparse Statistics with Random
  Forest Implicit Regularization*. Uses a SeatGeek pricing dataset for distribution recovery and event
  classification. Not a time path; no bearing on this question.
- `seatdata.io/articles/best-time-to-buy-concert-tickets-2026/`. Unpublished commercial analysis claiming
  307,727 sales and a 29% day-of saving. Not inspectable, not audited, so not evidence. Recorded so the next
  agent does not think it was missed.
- UNC honours thesis, *Price Dynamics in Live Event Ticket Sales: Evidence from College Football* (author
  and year as printed in the document I read: undergraduate thesis, advisor Brian McManus). Grey
  literature. Its one relevant qualitative finding, that after controlling for expected game quality prices
  fall over time but can rise when expected quality improves, is consistent with everything above and is not
  relied on.

Could not establish:

- Any published fitted decay function, half-life or time-elasticity for a secondary ticket price path (§3.4).
- Any published per-ticket repeat-sale price path (§3.4).
- Any peer-reviewed measurement of a price path under a resale cap. 01-b reached the same conclusion.
- Any published out-of-sample forecast accuracy for secondary ticket prices.

---

## CORRECTION (2026-11-07T11:28Z) — two author attributions in the reference list

Appended by the corrections pass after `records/findings/00-verification-round1.md` §4 and §8. Nothing above
is deleted. Both entries were inherited from `01-b` and are corrected there too (`01-b` CORRECTION 3).

**Withdrawn attributions.**

1. "**Mason, K. O., Mason, W. M., Winship, C. & Poole, W. K. (1973).**" The third author is **Winsborough,
   H. H.** A Crossref query for `10.2307/2094398` on 2026-11-07 returns Mason, Mason, Winsborough, Poole.
2. "**Luo, L. (2019).** Analyzing age-period-cohort data: a review and critique. *Annual Review of Sociology*
   45:467-492. doi:10.1146/annurev-soc-073018-022616." Crossref returns that DOI as **Fosse, E. & Winship,
   C. (2019)**, same title, journal, volume, pages and year.

**Corrected reading.** Wherever the text cites "Luo (2019)" or "Luo", read **Fosse & Winship (2019)**. Where
it cites Mason et al. (1973), the author set is Mason, Mason, Winsborough and Poole. Titles, journals, volumes,
pages and DOIs are unchanged and were confirmed correct; the propositions both works are cited for in §4.3 are
unaffected.

**Scope.** This is the only bibliographic correction in this file. Its own four checked citations (Sweeting,
Leslie & Sorensen, Lee et al., NBER 14505) and its recomputed arithmetic are not affected.

# Phase 2-C — The sale-probability target with no exposure denominator

**Status:** complete (first pass). **Written:** 2026-11-07T10:56Z.
**Author:** Phase 2-C research agent.
**Scope:** Phase 2 A (secondary-market price discovery), C (supply and demand), F (risk and stochastic
modelling) — narrowed to one object: the probability of sale, its identifiability from the record we will
have, the estimator that follows, and what the four listing fields change.
**Depends on:** `RESEARCH-PROGRAM.md` §3 Phase 2 A/C/F and §4; `AGENTS.md`;
`records/00-data-situation.md` (Gap 1, Gap 2, §3, §4); `records/findings/01-b-identifiability.md` (T3 — "the
crux"); `records/F-decision-log.md` (D2, D3, Q1–Q3); `records/README.md`;
`/home/friend/ticketing-frontend/lib/types.ts` and `API_CONTRACT.md`.
**Does not touch:** any file but this one. No dataset was read. No estimator was run. No simulation was run.
Nothing here is a measured quantity.

---

## 1. What I concluded

1. **01-b's crux is right and I confirm it.** The ask is recorded only on the success branch. Nothing in the
   transaction ledger — no modelling choice, no clever functional form — recovers $\partial\lambda/\partial p$.
   A sale-probability-at-a-price curve fitted to this record reports which sellers chose which prices and
   calls it demand.

2. **01-b's *reasoning* about the denominator is right; its *label* invites the exact error it was written to
   prevent.** The ticket-time denominator is observed (every ticket has an `issue` row and a known life), so
   *something* is identified. But that something is not a sale hazard. It is the intensity of a **composite
   process — offered, then bought** — marginalised over the unrecorded offering state:

   $$\lambda_{\text{obs}}(t\mid x)=\underbrace{s(t\mid x)}_{\Pr(\text{offered at }t)}\cdot\underbrace{\mathbb{E}\big[\lambda(t\mid p)\,\big|\,\text{offered},t,x\big]}_{\text{sale hazard, averaged over unrecorded asks}}$$

   Every ticket-day counts in the denominator whether or not the ticket was ever offered, so $\lambda_{\text{obs}}$
   is a *base rate of transaction per ticket-day*, not a hazard of sale. Calling it "the unconditional sale
   intensity per ticket-time" is defensible algebra and a bad name, because a reader will plug it into
   $1-\exp(-\lambda h)$ and be told the probability their ticket sells, which it will not answer.

3. **Three quantities are identified today, not one.** (i) the composite base rate $\lambda_{\text{obs}}(t,x)$
   and its functionals — cumulative incidence, time to first transaction, "share that ever transacts";
   (ii) the **joint mark–time intensity** $\xi(p,t)$: the rate of transactions per ticket-day at each markup,
   which is the realised-price-per-unit-time distribution and is a displayable object in its own right;
   (iii) the cause-specific exit intensities (sale / unpriced transfer / redeem / revoke) and therefore the
   competing-risks cumulative incidence and an upper bound on the never-offered share. Four things are not
   identified: the price response; the split of $\lambda_{\text{obs}}$ into $s(t)$ and $\lambda(t\mid p)$; the
   ask distribution; and any counterfactual over the *primary* price.

4. **The minimal honest estimator today is a piecewise-exponential composite intensity on a time-to-event
   grid with competing risks and a cure component.** It is a Poisson regression with an exposure offset. Fit
   by Newton–Raphson in pure standard library on aggregated cells — the design has tens of columns, not
   millions of rows. It is implementable in the required constraint (D2) without approximation in the
   likelihood, only in the solver's arithmetic.

5. **The four listing fields do not turn on one thing, they turn on five** — the exposure split, the price
   response, seller-side competition (depth), the supply margin (time-to-withdraw as an opportunity-cost
   object), and the cap-rationing mass point. Their marginal value is *not* uniform: `listPriceLamports` is
   worth more than the other three combined; `delistReason` is second because it separates "sold" from
   "gave up"; `delistedAt` and `listedAt` are nearly reconstructible by polling `Ticket.status = "listed"`,
   which makes them the cheapest two and the least urgent to specify.

6. **Even with all four fields, the primary-price optimum stays unidentified.** They identify the *secondary*
   price response. The primary optimum needs the *primary* demand response, and the secondary hazard at
   resale price $p$ is not the primary demand at primary price $p_0$: different population, different bundle,
   capped upside. The four fields close one of two identification gaps. This matters now, because it is the
   sentence that will get over-promised the day the listing table lands.

7. **A calibration number cannot be produced and must not be simulated into existence.** With one baseline
   parameter per time cell, an in-sample reliability curve is not evidence of anything: it is the score
   equation plotted. What replaces it is stated in §5 — descriptive rates with exact denominators and
   intervals, the censoring audit, the identification diagnostics, and a named evaluation protocol marked
   NOT RUN.

8. **Cold start has a correct treatment that is usually got wrong.** An event with no resale history after
   $E$ ticket-days of exposure is not missing data — the zero is *evidence*, and the predictive intensity must
   be updated by it (gamma–Poisson: posterior mean $a/(b+E)$, not the prior mean $a/b$). And events with zero
   sales must be **inside** the between-event variance estimate, or the variance is biased down and the cold
   start interval comes out too narrow.

---

## 2. Testing 01-b's case-only argument

### 2.1 The argument, restated precisely

01-b's T3 says the observed rate of sales at price $p$ is

$$\xi(p,t)=\lambda(t\mid p)\cdot\pi(p\mid \text{listed},t)\cdot s(t) \tag{1}$$

with $\lambda$ the wanted hazard, $\pi$ the density of asks, $s$ the listing probability. We observe the left
side. Nothing separates the three factors on the right, because the mark (the price) is written into the
record only where a sale happened. Hence this is a **case-only sample with no controls**, and the missing
observation is the *ask of the risk set*, not the exposure.

Both of those claims are correct. Two refinements are needed before the argument can be built on.

**Refinement 1 — name the estimand honestly.** The ticket population is censused, so the risk set
$Y_i(t)=\mathbb{1}\{\text{ticket } i \text{ alive at } t\}$ is observed and the Aalen multiplicative-intensity
argument applies ([Andersen & Gill 1982](https://doi.org/10.1214/aos/1176345976)): the cumulative intensity
$\Lambda_{\text{obs}}(t)=\int\lambda_{\text{obs}}$ is consistently estimable from $(Y,N)$. But $Y$ is
"ticket exists", not "ticket is offered", and those differ by an unrecorded state. So what is identified is
the *population-averaged, offering-marginalised* intensity displayed above. Three consequences follow, and none
of them appear in 01-b:

- Because the offering state is marginalised and not modelled, any unobserved heterogeneity in offering
  propensity is absorbed into $\lambda_{\text{obs}}$ but **not** into the covariate effects. Under frailty, the
  covariate coefficients of a population-averaged intensity are **attenuated** relative to individual-level
  effects ([Vaupel, Manton & Stallard 1979](https://doi.org/10.2307/2061224);
  [Lancaster 1979](https://doi.org/10.2307/1914140)). So $\hat\beta$ is an association under study, never a
  per-ticket effect.
- The estimand is a **rate per ticket-day of life**, and its magnitude depends on how long tickets sit alive
  and unoffered. Two events with identical buyer demand but different holder patience have different
  $\lambda_{\text{obs}}$. Comparing $\lambda_{\text{obs}}$ across events compares offering behaviour as much
  as demand.
- The cumulative incidence is the useful functional, not the rate. $\hat F(\cdot)$ is bounded by 1 and
  interpretable; $\hat\lambda$ is not, because it is a mixture whose mixture weights are unobserved.

**Refinement 2 — the case-cohort fix needs a different sampling frame than 01-b implies.** 01-b says the fix
is "asks on a random subset of the risk set". Operationally that is not quite it. The risk set is
ticket-days, most of which have no ask at all — a random sample of ticket-days would return "not offered"
almost always. The subcohort must be a random sample of **listing episodes**, which is what a listing table
produces *by construction*, because a listing row exists whether or not it sells. This is the same design as
a case-cohort study where the expensive covariate is measured on all cases plus a subcohort drawn from those
at risk of being a case ([Prentice 1986](https://doi.org/10.1093/biomet/73.1.1);
[Borgan, Goldstein & Langholz 1995](https://doi.org/10.1214/aos/1176324322)). The distinction is load-bearing
for how the data request is worded: **"record listings regardless of outcome", not "sample tickets".**

### 2.2 Is the at-risk denominator really observed?

Yes for ticket-life. No for offering. The test, item by item.

| Component 01-b needs | Available? | Evidence |
|---|---|---|
| Entry time per ticket | **Yes.** `Ticket.issuedAt`, and an `issue` ledger row with `slot` and `occurredAt`. | `lib/types.ts` |
| Exit time per ticket | **Yes.** First `sale` row; `Ticket.redeemedAt`; `revoke` rows; `Event.endsAt`; dataset extraction time for still-live tickets. | `lib/types.ts` |
| Exact exposure per ticket | **Yes**, and better than a count: ticketing is timed to the `slot`, which is strictly monotone, so exposure is computable to the slot even when `occurredAt` granularity is unknown. `slot` is nullable — the fallback and its failure mode are named below. | `lib/types.ts` (`slot: number \| null`) |
| Validity of that exposure | **No, partially.** Ticket-days during which resale was disabled or the mint was `transferRestricted` are in the denominator but are not at risk. `resaleEnabled` is event-level and observable at extraction; `transferRestricted` is a *current* flag, so its history is not. Time-varying validity is unrecoverable. | Q3 in `F-decision-log.md`; `00-data-situation.md` §4 |
| Offering state | **No.** No `listedAt`, no ask, no withdrawal, no revision, no depth history. `Ticket.status="listed"` is a state, not a spell. | verified: `grep -n "listPrice\|listedAt\|delistedAt\|delistReason" lib/types.ts` → no match |
| Completeness of the numerator | **Contaminated, direction known.** Wallet-to-wallet self-dealing (a round trip between two wallets one person controls) is recorded as a sale and inflates $\lambda_{\text{obs}}$. Detectable as same-wallet pairs and same-ticket round trips; not removable without identity. | `00-data-situation.md` §2; `01-b` §4.6(b) |

So the honest statement is: **the ticket-time denominator is observed and largely valid; the offering
denominator is not observed at all; and the numerator has a known upward contamination.** 01-b is right and
understates the caveats. `00-data-situation.md`'s "a numerator with no denominator" is the wrong diagnosis of
the same defect — the denominator exists, it is the denominator of the wrong process.

One more channel of exposure loss worth naming because it is invisible: `Event.status` transitions are not
timestamped (`00-data-situation.md` §4), so the window during which a ticket *could* be listed is unknown.
Tickets issued before the event's on-sale end and events whose resale window opened late both contribute
ticket-days that were never at risk. There is no bound on this from the contract.

### 2.3 What is identified, and what is not

| | Object | Status | Why |
|---|---|---|---|
| **O1** | $\lambda_{\text{obs}}(\tau,x)$ — composite intensity; and $\Pr(\text{transacts at least once by }\tau\mid x)$ | **Identified** (class C) | Censused population, observed life, competing risks handled as competing risks |
| **O2** | $\xi(p,\tau,x)$ — joint mark–time intensity: transactions per ticket-day at each markup | **Identified** (class C) | The joint distribution of (time, price) for transactions is observed in full; see §2.4 |
| **O3** | Cause-specific intensities; competing-risks CIF; an upper bound on the never-offered share | **Identified** (class C) | Redemption and revocation are terminal and observed |
| **N1** | $\partial\lambda/\partial p$; hence $\Pr(\text{sells at price }p)$ | **Not identified** | 01-b T3, confirmed |
| **N2** | The split $s(t)$ vs $\lambda(t\mid\text{listed})$ | **Not identified** | No offering spells in the record (recoverable going forward by polling; §7.4) |
| **N3** | $\pi(p\mid\text{listed},t)$ — the ask distribution | **Not identified** | Case-only sample |
| **N4** | Any counterfactual in the *primary* price $p_0$ | **Not identified** | The population is selected on issuance: a ticket exists only because someone bought it at $p_0$. Changing $p_0$ changes who is in the ledger. This is new to this file and is not in 01-b or `00-data-situation.md` |

N4 is the one that will be forgotten. Every number this programme produces is conditional on the primary
price that was actually charged. That makes it a description of *this* market at *these* prices, and the
primary-optimum component inherits the gap no matter how good the secondary estimate becomes.

### 2.4 A new point: $\xi(p,t)$ is identified and is worth displaying

01-b writes (1) as a decomposition of "the rate at which sales at price $p$ are observed" and treats the left
side as useless debris. It is not debris. $\xi(p,\tau,x)$ — how many transactions per ticket-day happened at
each markup, as a function of time-to-event — is fully observed, and it is the object behind two things the
wire contract already exposes: `EventAnalytics.priceSeries` (day-bucketed mean sale price) and
`markupDistribution` (six bps buckets). It answers "how much trade happens, and at what price levels, and when"
without any modelling assumption beyond the ticketing clock.

It must be labelled as a **transaction-price distribution, not a demand curve**, for the classical reason: a
locus of realised prices where sellers chose the prices traces the intersections of supply and demand and
neither curve ([Working 1927](https://doi.org/10.2307/1883501)). But it is true, it is identified, and it is
the honest replacement for a price-response chart in the UI (§7).

### 2.5 One place 01-b is slightly too pessimistic: the cap is a partial price anchor

01-b §4.1 and T3 say the record contains no price anchor for the *ask*. There is one, restricted and
conditional:

If a sale's recorded price equals the event's cap $p_0(1+c)$, then under a cap enforced **on the ask**
(Q3 option A) the ask was exactly the cap: asks cannot exceed it by enforcement, and a transaction at the cap
requires an ask at least at the cap. So *the ask is identified, exactly, on the cap-bound stratum* — a genuine
single known point on the price axis.

What that buys and does not buy:

- **Buys:** a known ask value on the one stratum where the price axis is otherwise missing; a constraint that
  the ask distribution has support inside $[0,\text{cap}]$ with a mass at the cap; and, given a parametric
  price-response form, a one-sided restriction (the hazard at the cap must be consistent with the average
  hazard, which is below it in ask terms).
- **Does not buy:** identification of $\gamma$. One known price is not two. Separation of a price effect
  requires variation in ask at fixed time-to-event, which needs *at least two* distinct known asks.
- **And it is contaminated:** at a binding cap the market clears by speed and rationing, not by price, so the
  hazard there measures buyer arrival intensity, not acceptance ([Bulow & Klemperer
  2012](https://doi.org/10.1086/665416)). The point is known in $p$ and unknown in economics.
- **Depends entirely on Q3.** If the cap is enforced at transaction time rather than at listing (Q3 option B),
  a sale at the cap implies only ask $\geq$ cap, and there is no anchor. Q3 therefore has a concrete
  identification consequence and should be asked with that framing.

Under the fixture check in `00-data-situation.md` §2 (no generated sale lands exactly on a cap), this anchor
cannot even be exercised on the fixtures.

### 2.6 Commercially: what the identified object is good for, and whether it is enough

$\lambda_{\text{obs}}$ and its functionals are enough to say these things, all true today:

| Statement the product can make | Quantity |
|---|---|
| "In this tier, X% of issued tickets transacted at least once before the event." | $F(\tau{=}0)$ — the cumulative incidence, which is literally `EventAnalytics.resoldShare` |
| "The median first transaction in this tier happened N days before doors." | quantile of the time-to-first-transaction distribution |
| "Trade in this tier concentrates in the last K days: P% of ticket-days at risk fall there, and Q% of transactions do." | $\xi$ and exposure by $\tau$ bucket |
| "Of tickets that transacted, R% transacted more than once." | recurrent-process count distribution |
| "Tickets in this tier were listed at least S% of the time." | *not available* (N2) — the offering split is unobserved |

It is **not** enough to say the thing the pitch promises. `AGENTS.md` and Phase 5 promise "the probability it
actually transacts at a given price". That is N1. So the product today is a **liquidity and realised-price
product**, not a demand-curve product, and the difference is one sentence in the interface, not a
re-architecture.

There is a middle statement that is honest and commercially useful, and it should be the ceiling until the
listing table lands:

> "At the price this tier has been transacting at, a listed ticket has converted at rate $r$."

This is a claim about *the market's own prevailing ask*, not about an arbitrary ask. It is defensible only
with its condition attached: it holds for a listing priced at the market level, and it degrades as the ask
moves away from that level, and the rate of degradation is the unidentified thing. Two footnotes are
mandatory: hazards are not linear in price, so the average hazard is not the hazard at the average ask; and
the prevailing ask is *inferred* from realised prices, which conflates the two (Working's point) — so the
sentence is a benchmark, not a prediction for a specific listing.

**Verdict: enough for the product to say true things, not enough for it to say the sentence it currently
wants to say.** The scope sentence has to change, and that is a decision for the operator rather than for this
file — flagged for `F-decision-log.md` alongside D3, because D3 commits the programme to *not* estimating the
price-conditional probability but says nothing about what the interface shows instead.

---

## 3. Specification A — the estimator that follows without exposure

### 3.1 Object and clocks

For ticket $i$ on event $e(i)$, tier $g(i)$:

- $a_i$ = entry, from the `issue` row's `slot` (fallback: `occurredAt` parsed to epoch seconds; if `slot` is
  null, the fallback orders events within a ticket correctly but not across tickets, so any same-second tie
  must be broken deterministically and reported as a data-quality count).
- $s_e$ = `Event.startsAt`; $\tau(t)=\dfrac{s_e-t}{\Delta}$, days to event, **positive before the event**. The
  substantive clock is time-to-event, not calendar time and not ticket age.
- $T_i=\min\{\text{first sale},\ \texttt{redeemedAt},\ \text{first revoke},\ e.\texttt{endsAt or } s_e,\ \text{extraction time}\}$,
  with the cause $C_i$ the exit that attained the minimum.

Why time-to-event and not age: the mechanism is that the option value of continuing to hold falls as the
remaining selling opportunities disappear, which is Sweeting's finding and the stopping structure of
[Gallego & van Ryzin 1994](https://doi.org/10.1287/mnsc.40.8.999); and it is the clock the product is asked
about ("a ticket, an event, and a time-to-event", `AGENTS.md`).

**Collinearity warning, new here.** Within a single event, $\text{age}_i(t)=t-a_i$ and $\tau(t)=s_e-t$ are
affine functions of each other *if all tickets share one issue time*: age $=s_e-a_i-\tau$. So a model with
both an age effect and a $\tau$ effect is unidentified within such an event, and identified only from events
that stagger issuance. This is the same linear-dependency trap 01-b found for price in T2, in a second place.
Practical rule: use $\tau$ as the clock, include age only as a bucket interacted with a "staggered issuance"
indicator, and report the within-event correlation of the two.

### 3.2 Discretisation and aggregation

Divide each ticket's risk window into day-long cells. For ticket $i$, cell $c$ covers
$(\max(a_i,t_{c-1}),\ \min(T_i,t_c)]$; let $\delta_{ic}$ be its length in days (0 if the cell is not at risk)
and $y_{ic}\in\{0,1\}$ the sale indicator in that cell. Assign $\tau$-bucket $b(c)=\beta(\tau(\text{cell start}))$
with $K$ buckets on the support actually observed — e.g.
$\{>60,\ 30\text{–}60,\ 14\text{–}30,\ 7\text{–}14,\ 3\text{–}7,\ 1\text{–}3,\ 0\text{–}1,\ <0\}$, and note that
the top bucket must be a real boundary: a ticket alive at 300 days to event spends most of its exposure where
the hazard is structurally near zero, so an open-ended top bucket puts most of the exposure and almost none of
the sales in one cell.

Aggregate to cells keyed by $(b, \text{covariate pattern})$:

$$E_{bc}=\sum_i \delta_{ic}\,\mathbb{1}\{b(c)=b,\ x_{ic}=\text{pattern }c\},\qquad D_{bc}=\sum_i y_{ic}\,\mathbb{1}\{\cdot\}$$

Everything downstream operates on counts, not rows. For $10^5$ tickets × $90$ days with ~40 covariate
patterns this is a table of a few thousand cells — the reason the whole thing is standard-library feasible.

### 3.3 The likelihood

**Primary form (piecewise-exponential, exact).** Within bucket $b$,
$\lambda_i(t)=\exp\!\big(\alpha_b+x_{ic}'\beta\big)$, so

$$\ell(\alpha,\beta)=\sum_{b,c}\Big[D_{bc}\big(\alpha_b+x_c'\beta\big)-E_{bc}\,e^{\alpha_b+x_c'\beta}\Big] \tag{3}$$

which is exactly a Poisson log-likelihood with offset $\log E_{bc}$ and no constant. Score:

$$\frac{\partial\ell}{\partial\alpha_b}=\sum_c\big(D_{bc}-E_{bc}\mu_{bc}\big),\qquad
\frac{\partial\ell}{\partial\beta}=\sum_{b,c}x_c\big(D_{bc}-E_{bc}\mu_{bc}\big),\qquad \mu_{bc}=e^{\alpha_b+x_c'\beta},$$

observed information $-H=\sum_{bc}E_{bc}\mu_{bc}\,\tilde x_c\tilde x_c'$ with $\tilde x_c=(e_b,x_c)$. Newton's
method converges in a handful of iterations from $\alpha=\log(\bar D/\bar E)$, $\beta=0$.

**The discrete-time form, and the link, stated correctly.** The exact grouped-data hazard on a grid is

$$h_{ic}=1-\Pr(\text{no sale in cell}\mid\text{at risk})=\Pr(\text{exit in cell})=1-\exp\!\big(-e^{\alpha_b+x'\beta}\delta_{ic}\big)$$

which is a **complementary log-log** link, not a logit. The familiar discrete-time logit
$\ell=\sum [y\log h+(1-y)\log(1-h)]$ with $h=\mathrm{expit}(\alpha_b+x'\beta)$ is an approximation to the
cloglog form that is accurate when within-cell event probabilities are small — which they are here, a
per-ticket-day sale probability of order $10^{-3}$. The division of labour in the literature is precise and
worth keeping straight: [Prentice & Gloeckler 1978](https://doi.org/10.2307/2529588) give the grouped-data
proportional-hazards likelihood and its cloglog link;
[Holford 1980](https://doi.org/10.2307/2529982) gives the equivalence between log-linear models for rates and
survivorship, which is why (3) is a Poisson regression; and
[Allison 1982](https://doi.org/10.2307/270718) sets out the discrete-time logit as the practical approximation
used in the social-science literature. I recommend the exponential form over the logit for three reasons, and
the choice should be recorded: it is exact rather than approximate; the offset handles ragged cell lengths (the
first and last cells of every ticket are partial); and its predictive integral is closed-form (§3.5). The logit
form is a legitimate second implementation and a useful robustness check.

### 3.4 Censoring and competing risks

Redemption is **not** independent censoring. A ticket redeemed at the door was, by revealed behaviour, held
for use; treating that as censoring removes tickets for reasons correlated with the outcome and inflates the
sale hazard ([Fine & Gray 1999](https://doi.org/10.1080/01621459.1999.10474144);
[Prentice et al. 1978](https://doi.org/10.2307/2530374)). Redemption and revocation are competing events.

Estimate the cause-specific intensity $\lambda_k$ for $k\in\{\text{sale},\text{transfer},\text{redeem},\text{revoke}\}$
by applying (3) once per cause (each as a binary outcome, with all other exits treated as censored at their
time — this is the standard cause-specific construction and it is correct for the CIF that follows). Then on
the day grid, with total hazard per cell $\Lambda_{bc}=\sum_k\lambda_{k,bc}\delta$:

$$\hat p_{\text{sale}}(b,c)=\frac{\hat\lambda_{\text{sale},bc}}{\hat\lambda_{\cdot,bc}}\Big(1-e^{-\hat\Lambda_{bc}}\Big),\qquad
\hat S_{bc+1}=\hat S_{bc}\,e^{-\hat\Lambda_{bc}}$$

$$\boxed{\ \hat F_{\text{sale}}(\tau)=\sum_{\text{cells up to }\tau}\hat S_{bc}\ \hat p_{\text{sale}}(b,c)\ } \tag{4}$$

Eq. (4) is the product-limit/CIF estimate under the fitted model, closed form, no simulation, and it is the
quantity that goes into the product. $\hat S$ here is first-passage survival, so there is no recurrence
correction in it; the recurrent variant of §3.6 replaces $\hat S$ in the sum with the at-risk share at each
cell, and the two must never be mixed in one figure.

**Administrative censoring.** Two kinds, both handled by the same $T_i$: (i) event end, which is exogenous
given the event and is therefore the benign kind; (ii) dataset extraction, which puts every ticket for a
future event into heavy right-censoring, and — critically — puts them into the *exposure* as well, at $\tau$
values far from the event where the hazard is near zero. Consequence: quote the $\tau$ support of the
estimate, never extrapolate past it, and report the share of total exposure in buckets where the sale count is
zero. A model cannot learn a hazard from a bucket with no sales; it can only be regularised, and the
regularisation is a choice that must be stated (§3.7).

**Cure component.** With a terminal point (after the event, no ticket can sell again) the never-sold fraction
is identifiable in a way that is unusually clean for survival data — a luxury the literature does not usually
have ([Boag 1949](https://doi.org/10.1111/j.2517-6161.1949.tb00020.x);
[Farewell 1982](https://doi.org/10.2307/2529885)). Mixture:

$$S(t\mid x)=\pi(x)+(1-\pi(x))S_u(t\mid x),\qquad
\ell=\sum_{\text{sold}}\log\big[(1-\pi)f_u(T_i)\big]+\sum_{\text{censored}}\log\big[\pi+(1-\pi)S_u(T_i)\big] \tag{5}$$

Two warnings, both of which belong in the code as comments because both are easy to get wrong.
(i) $\hat\pi$ here is **not** "the share of owners who never intended to sell". It is "the share of tickets
that never transacted", which pools *never offered* with *offered and never bought*. So $\hat\pi$ is an
**upper bound** on the never-offered share, exactly as 01-b's cure discussion implied.
(ii) Testing whether $\pi>0$ rather than assuming it matters, and the test has a non-standard null
([Maller & Zhou 1995](https://doi.org/10.2307/2533253)); with a terminal point, the honest default is to
estimate $\pi$ and report its interval, not to test.

### 3.5 What it predicts

Two outputs, both from (4):

- **Cumulative incidence:** $\hat F_{\text{sale}}(\tau)$ — the probability a ticket like this one has
  transacted at least once by time $\tau$ before doors. At $\tau\!\to\!0$ this is the base rate, the estimated
  counterpart of `resoldShare`.
- **Remaining-horizon incidence:** $\hat F(\tau_0\to\tau_1)=\big(\hat S(\tau_0)-\hat S(\tau_1)\big)/\hat S(\tau_0)$
  — the probability of transacting in the next $h$ days, given alive and unsold now. This is what a
  countdown or a "if you list today" panel needs, and it is legitimate as a *base rate for the next window*.
- **Time to first transaction:** quantiles of $\hat F$, for display and for the secondary-window timing
  question.

Uncertainty: Wald interval on the log cumulative hazard from the inverse observed information (the Hessian is
already built), or a parametric bootstrap of $\hat\theta$ for interval propagation into (4). The bootstrap is
a resampling scheme for a *sampling distribution*, not a validation of the model against a market — it would
be labelled SIM under `records/README.md` and no number from it may be quoted as accuracy.

### 3.6 Recurrence, and why first passage is the right target

A ticket can transact several times. Two modelling choices and one trap:

- **First passage** (recommended): stop the risk window at the first sale, censoring everything after. This
  matches the product's question ("will this ticket sell") and gives a hazard that is comparable across
  tickets at the same point in their lives.
- **Recurrent process**: keep the ticket at risk after each sale. Fine, but it estimates a different object.
- **The trap:** the recurrent rate is *not* the per-ticket rate. A ticket re-enters the risk set only because
  it proved liquid — a new owner only lists it if the last sale suggests a spread. Pooling first and later
  sales therefore mixes a population of tickets with a population of *tickets selected on having sold*. If the
  product needs a per-ticket number, use first passage. If it needs a churn number, use the recurrent process
  and never present the two on the same chart.

Also re-estimate the cure fraction by holder type (original issuee vs secondary buyer). A ticket held by the
wallet it was issued to has a different never-list probability than one held by a wallet that bought it on
resale, and the contract supports the split directly (`issuedToWallet` vs `ownerWallet`), with no inference.

### 3.7 Covariates the contract supports, with mechanisms (§4.2) and leakage status

| Covariate | Mechanism | Source | Class |
|---|---|---|---|
| $\tau$-bucket | Option value of holding falls as remaining selling opportunities disappear | `startsAt` | A (Sweeting 2012) |
| $\log$ tier face value | Price level relative to the buyer population's budget; also the cap's base | `TicketTier.faceValueLamports` | B |
| Primary sell-through $issuedCount/totalSupply$ | Excess demand at the primary price — the best available proxy for "this show is hot" | `TicketTier` | B |
| Cap present / $\log(1+capBps)$ | A ceiling suppresses upside and therefore listing supply; also distorts the hazard where it binds | `Event.resalePriceCapBps` | C |
| `resaleEnabled`, `requiresVerifiedWallet` | Friction on supply / on buyer arrival | `Event` | C |
| `transferRestricted` | Hard block on the sale channel | `Ticket` | C |
| City, venue, organizer | Demand heterogeneity, repeated-organizer learning | `Event`, `Organizer` | D |
| Prior custody hops of this ticket as of $t$ | Selection on liquidity (§3.6) | `transferCount` at $t$ | C |
| Has the issuee wallet sold before; its prior sale count | Repeat-reseller behaviour, one of the few ledger-native features | `fromWallet` history | B (01-b §4.6b) |
| Tier cumulative sales / volume so far; sales in the last 24 h | Market state; momentum | ledger, strictly lagged | D |
| Ticket age bucket, interacted with staggered-issuance indicator | Time on market | `issuedAt` | C (see §3.1 trap) |

Not available and not to be faked: ask, listing duration, live depth, any bid/offer/view/search signal
(verified: `grep -n "bid\|offer\|view\|search" lib/types.ts API_CONTRACT.md` → no match), seat coordinates
(Q1), fee fields (Gap 4).

Leakage rules, all of which are temporal-correctness requirements (§4.8) and each of which has a specific way
to be violated:
- Anything computed from the ledger must be computed from rows strictly before the cell's end. `transferCount`
  and `lastSalePriceLamports` on `Ticket` are *current* snapshots; using them as if they were historical is a
  look-ahead error and will inflate every "market state" coefficient.
- The event's final `issuedCount` and `totalSupply` are as-of-extraction. For a live event, final sell-through
  is a future quantity. Use the value known at $t$, or accept that the sell-through coefficient is not
  usable in production and say so.
- Redemption is a post-outcome variable for any ticket that sold late in life. Never a covariate.

### 3.8 Implementation, standard library only (D2)

```
1  ingest: ledger rows grouped by ticketId; join ticket → tier → event.
2  clock:  slot as the monotone index; missing slot → occurredAt epoch; count and report nulls.
3  window: per ticket, entry = issuedAt, exit = min(first sale, redeemedAt, revoke, event end, now)
           with its cause; assert exit > entry and report every negative duration (01-b §4.6c).
4  cells:  per ticket, day cells clipped to the window; bucket by tau.
5  table:  dict[(bucket, covariate-tuple)] → [exposure_days, count_sale, count_transfer,
           count_redeem, count_revoke].
6  fit:    per cause, Newton–Raphson on (3).
           per iteration: mu = exp(alpha[beta_idx] + X@beta)
                          g  = Z'(d - mu*E)                      # Z includes the bucket dummies
                          H  = Z' diag(mu*E) Z                   # p.d. matrix, dim ~ 8 + |beta|
           solve H step = g by Gaussian elimination with partial pivoting; step-halve while
           likelihood decreases; stop at |step|_inf < 1e-8 or 100 iterations.
7  guards: (a) separation — a bucket with zero sales drives alpha_b -> -inf. Apply Firth's penalised
              likelihood (Firth 1993) or an explicit ridge with the value reported, and report the
              sensitivity of the tau->0 estimate to that choice. Do not let it silently diverge.
           (b) condition number: ratio of largest to smallest pivot magnitude in the elimination step,
              printed every fit. Non-finite or >1e10 means a cell is empty and the design is
              rank-deficient; drop or merge that cell explicitly.
8  predict: Lambda(tau) = sum over cells of lambda_k * delta; S = exp(-Lambda); CIF by (4).
           Interval: delta method on log Lambda, or parametric bootstrap of theta.
9  report:  exposure by bucket, sales by bucket, censoring counts by cause, share of exposure in
           zero-sale buckets, share of exposure with invalid validity (resaleEnabled false),
           negative durations, null slots, self-dealing candidates.
```

Cost: memory is the aggregated table (thousands of cells), not the ledger expansion. Time is
$O(\text{rows} + \text{iteration} \times (K+p)^3)$ with $K+p\lesssim 40$, so milliseconds per fit. This is
the "computationally efficient" requirement in `RESEARCH-PROGRAM.md` §4.9 satisfied without a numerical stack.

### 3.9 What a user must not conclude from Specification A

Say these in the interface, in this order, because each one is a specific misreading that a competent person
will make:

1. **Not a probability of sale at a price.** There is no price in the model. It cannot answer "if I list at
   $p$, what is my chance".
2. **Not a demand curve, and not evidence about demand.** A covariate coefficient here is an association
   between a ticket attribute and how often tickets like it transacted. Cheaper tickets transacting more often
   is a statement about who was offered and at what, not about elasticity.
3. **Not a per-ticket propensity.** The estimand is population-averaged (§2.1). Under unobserved
   heterogeneity the coefficients are attenuated and the interval is too narrow if heterogeneity is ignored.
4. **Not causal for any covariate.** Every covariate is an equilibrium object: sell-through is the outcome of
   the primary price, cap presence is the organizer's policy, city is a market. Change one and the others move.
5. **Not transferable across primary prices** (N4). The population is tickets that someone bought at $p_0$.
6. **Not "will not sell" for a zero.** $\hat F=0$ in a stratum means no transactions were observed in that
   window, which under the cure model can be "nothing was offered".
7. **Not a forecast past the observed $\tau$ support.** Extrapolating a declining-then-rising hazard beyond
   the observed range is an extrapolation of a shape, and the shape near the boundary is where the estimate is
   weakest.

---

## 4. Specification B — the estimator that follows once the four fields exist

Fields: `listPriceLamports`, `listedAt`, `delistedAt`, `delistReason ∈ {sold, withdrawn, expired, cap_blocked}`.
Unit of analysis is the **listing episode** $j$ on ticket $i$: a maximal interval over which the ask is
constant. One consequence to settle with the platform team: if a seller revises the price, that is either a
new episode (four fields per revision) or the four fields cannot represent revisions at all. **The former is
required** — revisions are the richest source of within-ticket price variation (§4.4) and the whole point of
recording them.

### 4.1 The likelihood

Episode $j$: entry $L_j$, exit $D_j$, exit reason $r_j$, ask $p_j$ (constant within the episode), markup
$m_j=p_j/\text{face}_i-1$, scaled ask $z_j=\log(1+m_j)$.

$$\lambda_j(t)=\lambda_0\big(\tau(t)\big)\cdot\exp\!\big(x_i'\beta+\gamma z_j+\delta\,w_j(t)\big) \tag{6}$$

with $w_j(t)$ the number of *other* tickets listed in the same tier at $t$ (depth — the competition axis, the
variable 01-d rated "very high"). Piecewise-constant $\lambda_0$ on the $\tau$ grid, written
$\lambda_{0k}=e^{\alpha_k}$:

$$\ell(\theta)=\sum_j\sum_{k\in\mathcal K_j}-\lambda_{0k}e^{\eta_{jk}}\Delta_{jk}
\;+\;\sum_{j:\,r_j=\text{sold}}\Big[\alpha_{b(D_j)}+\eta_{j,b(D_j)}\Big],\qquad
\eta_{jk}=x_i'\beta+\gamma z_j+\delta w_{jk} \tag{7}$$

$\mathcal K_j$ = the $\tau$-cells episode $j$ overlaps, $\Delta_{jk}$ = overlap length in days. Correctly
censored: a **withdrawn** episode contributes exposure and no failure; an **expired** episode likewise; a
**cap_blocked** episode is a censored observation *in the cap region* and carries extra meaning (§4.5).

Equation (7) is the same likelihood as (3), with an episode-level design instead of a ticket-level one. **The
solver does not change.** That is the engineering answer to "what does the listing table cost": new rows,
same code.

The target functional:

$$\boxed{\ \hat\Pr(\text{sold within }h\mid\text{listed today at }p,\ \tau_0,x)=1-\exp\!\Big(-e^{x'\beta+\gamma z+\delta w}\sum_{k\in(\tau_0-h,\tau_0]}\hat\lambda_{0k}\Delta_k\Big)\ } \tag{8}$$

and letting $h\to\tau_0$ gives the eventual sale probability of a listing, which must be reported as a
**competing-risks** quantity — sold versus withdrawn — not as a single probability for the sale (§4.6).

### 4.2 Functional form for the price response

Three candidates, in the order I recommend estimating them:

**(i) Nonparametric in price (primary).** Replace $\gamma z_j$ with $\sum_m\theta_m\mathbb{1}\{z_j\in B_m\}$ over
$M$ markup bins. No shape imposed. The surface to inspect is
$\big(\theta_m,\ \tau$-buckets$\big)$: a matrix of estimated log-hazards. Straightforward MLE, same solver,
and it doubles as the specification test for (ii) and (iii) by likelihood ratio — with the caveat that
in-sample comparisons of nested forms test the parametric restriction, not out-of-sample accuracy.

**(ii) Constant-elasticity in markup (reporting form).** $\gamma z$ with $z=\log(1+m)$. $\gamma$ is the
elasticity of the sale hazard with respect to the ask: a 1% higher markup multiplies the sale hazard by
$\approx(1.01)^{\gamma}$, so $\gamma=-4$ means a 10% higher ask cuts the per-day sale rate by roughly a third.
Impose it only if the nonparametric surface's iso-hazard contours are straight lines in $(z,\tau)$.

**(iii) Choke-price form.** $\eta=\ldots+\log\!\big(1-p/p^*\big)$ with $p^*>p$ a parameter: a finite ask at which
the sale hazard is zero. Commercially the most interpretable ("the market will not pay above $p^*$") and it
feeds the primary optimisation directly, but it is a strong functional commitment and it makes the hazard
non-monotone in its own parameters near $p^*$. Keep it as a third specification to be checked against (i).

Why markup $m$ and not price $p$: the cap is proportional to each tier's own face
(`resalePriceCapBps` over `faceValueLamports`, `00-data-situation.md` Gap 2), the platform expresses markup in
bps natively, and $m$ is the only price scale that is comparable across a \$12 balcony and a \$400 pit.
Regressing on lamports makes one coefficient do the work of a per-tier price level and a within-tier price
position, which is a mismatch of units and a guarantee of a specification error.

### 4.3 What identifies $\gamma$ — the argument, stated as assumptions

**A1 (proportional form).** The price effect is multiplicative and constant across $\tau$, tickets and events.
Test by interacting $\gamma$ with $\tau$-buckets; if the interaction is large, the honest output is a
$\gamma(\tau)$ surface, not a scalar.

**A2 (no unobserved confounding of the ask).** Conditional on $(e, g, \tau, x)$, the ask is independent of the
ticket's unobserved sale propensity.

Under A2, $\hat\gamma$ is the causal price response. **Without** A2 it is still identified — the ask is a
covariate observed on everyone at risk, so the conditional intensity $\lambda(t\mid p,x)$ is estimable by
standard counting-process theory ([Cox 1972](https://doi.org/10.1111/j.2517-6161.1972.tb00899.x);
[Andersen & Gill 1982](https://doi.org/10.1214/aos/1176345976)) — but it is a *conditional association*: it
predicts sales given the seller's pricing policy, and it is not a counterfactual for the seller's own ask.
That is the exact distinction between the forecasting use and the decision use, and the product needs both
stated.

**A3 (episode independence given covariates).** Multiple episodes of one ticket are conditionally independent.
Violated by construction (a re-listing follows a failed listing), so include a per-ticket frailty or cluster the
information matrix by ticket.

**A4 (interior price variation).** $\gamma$ is identified from variation in $z$ *within* $(e,g,\tau)$-cells.
This is the assumption that can silently fail while the software reports a number — see §4.4.

**A5 (temporal correctness).** $z_j$, $w_j(t)$, and every $x$ used at $t$ use only information available at
$t$. A sale at $D_j$ must not enter $w$ before $D_j$.

**The three threats to A2, with their bias directions.** Worth writing down because the direction is not
obvious and the net is not signable:

1. **Within-tier unobserved quality** (Gap 3: no seat coordinates). A better seat inside the same tier is
   asked at more *and* sells faster, so $\hat\gamma$ is biased **toward zero** (or positive). This makes
   $|\hat\gamma|$ an understatement.
2. **Endogenous revision.** A seller who cuts the ask has usually just observed the listing failing; the cut
   and the failure share a cause, so within-episode revision variation overstates the causal effect of the
   cut. Bias **away from zero** (more negative). Sweeting's relisting evidence is precisely that sellers cut
   in response to their own failure, which is exactly this mechanism
   ([Sweeting 2012](https://doi.org/10.1086/669254)).
3. **The $\tau$ confound** (next subsection): asks fall and hazards rise as the event approaches, so omitting
   the time effect gives a spuriously strong negative $\gamma$. Bias **away from zero**.

Threat 1 attenuates; threats 2 and 3 inflate. The net bias has no known sign. That is a reason to report a
*bounded* claim rather than a point: with A2 restricted to "the only confounder is within-tier quality", a
negative $\hat\gamma$ is a lower bound on the magnitude of the response; with the revision channel present, it
is not. Say which assumption you are relying on and let the operator see it.

**Instruments considered, and one that must be discarded.**

- *The cap, where it binds.* A policy variable set by the organizer, not the seller, so it shifts the
  admissible ask without depending on the ticket's own propensity. Identification is therefore local to the
  cap band and is a regression-discontinuity-flavoured design rather than a global instrument
  ([Lee & Lemieux 2010](https://doi.org/10.1257/jel.48.2.281)). Requires Q3's answer on where enforcement
  happens. **Viable, local.**
- *Seller tenure (time since acquisition).* Shifts the seller's reservation through declining opportunity cost
  (Sweeting's mechanism) while buyer arrivals should not depend on how long the seller has held the ticket.
  The exclusion restriction is a behavioural assumption, not a measurement, and it fails if long-held tickets
  are systematically different. **Viable, fragile.**
- *The seller's own purchase price (reference-point pricing).* Shifts the ask. **Must be discarded on this
  platform**: transaction history is public on-chain, so a buyer can condition on the seller's cost basis, and
  the exclusion restriction fails by design. This is worth naming precisely because it is the instrument an
  analyst would reach for first and it is the one this ledger rules out.

### 4.4 The collinearity trap, with the arithmetic

Within one event, time-to-event and the ask move together: prices fall as the event approaches (class A on
Sweeting's MLB data), and the sale hazard rises. So $(z_j,\ \tau\text{-buckets})$ is nearly collinear by
construction.

Write $z_j=g(\tau_j)+\varepsilon_j$ for the part of the ask explained by time-to-event. Then:

- $\gamma$ is identified **only** from $\mathrm{Var}(\varepsilon\mid e,g,\tau)$ — the cross-sectional
  dispersion of asks among tickets co-listed at the same time, in the same tier, for the same event.
- If $\mathrm{Var}(\varepsilon\mid\cdot)=0$ — every seller prices at the same markup at each time-to-event —
  then $z$ lies in the span of the $\tau$ dummies, the design is rank-deficient, $\gamma$ is not identified,
  and the only thing the software will tell you is that the Hessian is singular. Do not let a
  near-singular Hessian be mistaken for a numerically awkward but valid estimate.
- **Diagnostics to compute and publish, before any $\hat\gamma$:** (a) the within-$(e,g,\tau)$ variance of
  $z$, and its ratio to the total variance — the fraction of price variation that can identify anything;
  (b) the $R^2$ of a regression of $z$ on $(e\times g\times\tau)$ dummies; (c) the condition number of the
  information matrix; (d) the count of $\tau$-cells containing more than one distinct observed ask.
- **A normalisation is required** and must be chosen, not inherited: either a parametric baseline shape with
  few $\tau$ parameters, or a reference markup bin with $\theta=0$. The choice determines what $\hat\gamma$
  means as a number, so record it with the estimate.

The practical consequence is a hard requirement on the data, not on the model: **identification needs
overlapping spells at different asks.** A listing table in which all sellers set the same price is four fields
of nothing. State this in the data request: what is needed is not just the fields but *price dispersion among
simultaneously live listings*.

### 4.5 The cap stratum must not be pooled with the interior

If the cap binds, a sale at the cap went to the fastest buyer, not the highest valuer; the observed hazard at
the cap measures arrival speed under rationing
([Bulow & Klemperer 2012](https://doi.org/10.1086/665416)). So:

- Include a `cap_blocked` indicator and an "ask at cap" indicator, and interact them with the price term, or
  estimate the cap stratum separately. Pooling biases $\gamma$ toward the rationing regime's mechanics.
- Under Q3-A (cap enforced on the ask), cap-bound sales give an exact ask (§2.5). Under Q3-B they do not.
  Either way, the cap stratum is where the *quantity* of rationing is measurable and where the latent
  willingness-to-pay tail is invisible — the mass point is excess demand, not value.
- The `cap_blocked` enum value is the single most valuable element of `delistReason`, because it is the only
  observation in the whole design that separates "nobody wanted it" from "everybody wanted it and the cap
  rationed them". Without it, a failed listing at the cap is indistinguishable from a failed listing at a
  delusional price.

### 4.6 What Specification B predicts, and what it still cannot

Once identified, (8) gives: the sale probability within a horizon at a chosen ask; the elasticity $\gamma$;
the depth effect $\delta$; the choke price $p^*$; the eventual sale-versus-withdrawal split; and the
rationing quantity at the cap.

It does **not** give the primary-price optimum. Two reasons, both structural:
- Different object. The secondary hazard at resale price $p$ is the chance a *ticket holder* finds a buyer in
  a *secondary* market. Primary demand at primary price $p_0$ is the chance a *consumer* buys from the
  organizer with no resale rights attached to the purchase decision. They share a demand primitive and share
  nothing else mechanically.
- Selection on issuance (N4). The population of tickets in the ledger is the population that bought at the
  price actually charged. Varying $p_0$ changes the population, and no amount of secondary data repairs that.

So the correct claim after the listing table lands: **"we can now price a resale ask; we still cannot choose a
primary price from data"** — the latter staying where 01-b's T4b and T5 put it, as a set with bounds, unless
the operator runs a primary-price experiment.

---

## 5. Calibration with no validation set

### 5.1 What a calibration claim would require

1. **A held-out set not used in fitting.** Non-negotiable; there is no in-sample substitute.
2. **A temporal holdout, not a random one.** Deployment always predicts forward, so the holdout must be
   forward: fit on listings up to $T_k$, predict the next window, roll $k$. This is the prequential protocol
   ([Dawid 1984](https://doi.org/10.2307/2981683)) and it is the only one that tests the thing the product
   does. A random split tests interpolation within a period and will look better than the product ever is.
3. **Resolved outcomes.** A ticket censored inside the holdout window cannot be scored naively. Either score
   at fixed horizons where follow-up is complete, or use inverse-probability-of-censoring weights — and then
   the censoring model is itself estimated, so its own misspecification enters
   ([Graf et al. 1999](https://doi.org/10.1002/(sici)1097-0258(19990915/30)18:17/18%3C2529::aid-sim274%3E3.0.co;2-5)).
4. **A named metric, fixed in advance.** For a survival target, the IPCW Brier score at pre-declared horizons
   plus a calibration plot at those horizons; proper scoring rules so that the comparison to a
   no-model baseline is meaningful ([Gneiting & Raftery 2007](https://doi.org/10.1198/016214506000001437)).
   For a binary target, the Brier decomposition ([Murphy
   1973](https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2)).
5. **At least two origins**, so that stability is visible; one holdout window cannot distinguish a good model
   from a lucky one.
6. **A baseline to beat**: the empirical hazard by stratum, i.e. no model at all. A model that does not beat
   the raw rate has no reason to exist.

### 5.2 Why an in-sample calibration curve is worthless here — the algebra, not an opinion

It is not merely likely to be optimistic. For this model class it is **guaranteed by the score equations**.

In (3) every $\tau$-bucket, and in a stratified specification every stratum, has its own intercept. The score
equation for that intercept is

$$\sum_{c\in b}\big(D_{bc}-E_{bc}\hat\mu_{bc}\big)=0 \quad\Longrightarrow\quad \sum\text{predicted events in }b=\sum\text{observed events in }b .$$

A reliability curve grouped at the intercept's own granularity is that equation plotted. Observed equals
predicted in every cell because the estimator was defined by setting the difference to zero. Any miscalibration
an in-sample curve can show appears only at a *coarser* grouping than the model's own, so what it measures is
the coarseness of the grouping, not the forecast. Two further layers on top: with enough $\tau$ buckets the fit
is near-saturated, and — 01-b's selective-labels point — every scored price observation is conditioned on a
sale, so the scored sample *is* the selected sample and agreement is built in.

Stated plainly for the record: **there is no number in this file, because a calibration number cannot be
produced from this record and must not be manufactured by simulation.** `00-data-situation.md` §5 admits
simulation only for estimator properties, and an estimator-property simulation is not calibration.

### 5.3 What to report instead

Report these, all of which are computable the day the ledger exists and none of which is a validation claim:

**Identified descriptives, with denominators and intervals.**
- $k$ of $n$ tickets in tier $g$ transacted at least once; the rate with a Wilson interval
  ([Wilson 1927](https://doi.org/10.1080/01621459.1927.10502953)) — Wilson over Clopper–Pearson
  ([Clopper & Pearson 1934](https://doi.org/10.1093/biomet/26.4.404)) because the rates are near 0 and 1 and
  Wilson keeps coverage without the conservatism; both are implementable in stdlib by bisection on the
  incomplete beta.
- Median and interquartile $\tau$ at first transaction.
- Transaction counts and mean markup by $\tau$ bucket and tier — O2, the identified mark–time intensity.

**The censoring and validity audit** — the numbers that determine whether the estimate means anything.
- Exposure and tickets by exit cause (sold / transferred / redeemed / revoked / still alive).
- Share of total exposure falling in $\tau$-buckets with zero observed sales.
- Share of exposure in events with `resaleEnabled = false` (invalid exposure, must be dropped).
- Count of `slot` nulls, negative durations, and self-dealing candidates (same-wallet round trips).

**The identification diagnostics of §4.4**, as soon as listings exist: within-$(e,g,\tau)$ variance share of
the ask, $R^2$ of ask on the time dummies, condition number, count of multi-ask cells.

**The evaluation protocol, marked NOT RUN**, naming the metric, the horizons, the origins, and the baseline.
A protocol on file is worth more than a number that cannot be defended.

And one sentence in the interface, because it is the honest form of the whole section: *"This market's record
does not contain asking prices, so no accuracy figure for a price-conditional sale probability exists. The
figures shown are counts and rates of what actually happened, with their denominators."*

---

## 6. Cold start — an event with no resale history

### 6.1 What the intensity estimate collapses to

Under a hierarchical version of Specification A with an event random effect $u_e\sim N(0,\sigma^2)$,

$$\lambda_i(t)=\lambda_0(\tau)\,e^{x_i'\beta+u_{e(i)}},\qquad \mathbb{E}\big[\lambda\mid x\big]=\lambda_0(\tau)e^{x'\beta+\sigma^2/2}.$$

With no transactions for $e^\*$, there is no information inside $e^\*$ about $u_{e^\*}$, so the estimate
collapses to the population baseline at that event's covariates, and the interval is driven entirely by
$\sigma^2$. That is the naive answer and it is the wrong one, because it treats the zero as missing data.

**The zero is evidence.** An event that has accumulated $E$ ticket-days of exposure with no transaction tells
you its intensity is low. With a gamma frailty $\lambda\sim\text{Gamma}(a,b)$ (the standard conjugate choice,
[Vaupel, Manton & Stallard 1979](https://doi.org/10.2307/2061224)), the likelihood of the observed zero over
exposure $E$ is $e^{-\lambda E}$, so the posterior is $\text{Gamma}(a,\ b+E)$ and the predictive intensity for
the next window is

$$\hat\lambda_{\text{cold}}=\frac{a}{b+E}\cdot\frac{\lambda_0(\tau)e^{x'\beta}}{\bar\lambda_{\text{prior}}}
\quad\text{rather than}\quad \frac{a}{b}\cdot(\cdot).$$

Two things follow, and both are implementable in stdlib with `math.lgamma`:

- The cold-start prediction must **shrink with the observed exposure**, not sit at the population mean. An
  event 200 days out with no listing activity and an event one week out with none are different statements;
  the formula distinguishes them, the prior-mean answer does not.
- The predictive interval is the gamma-mixed (negative-binomial-like) predictive, which is **wider** than the
  Poisson interval at the same mean. Reporting a Poisson interval here overstates precision in exactly the
  situation where the product is most tempted to state a confident number.

The scope of that update is the *composite* intensity. It says "tickets like this do not transact much", not
"nobody is listing" — that decomposition is N2 and cold start does not fix it.

### 6.2 Is partial pooling defensible? The assumption, stated rather than assumed

Partial pooling across events is defensible exactly when **events are exchangeable given the covariates**:
$(u_e)$ independent and identically distributed across events conditional on $x$. That is a modelling
assumption, not an identification result, and it fails when:

- **Demand shocks are shared within an event and unpredictable across events.** "This artist just announced a
  tour" is a latent factor at the event level that no covariate carries. Under such a factor, $u_e$ is not a
  draw from a common distribution — the events differ systematically in a way the covariates miss — and
  pooling transfers the wrong information. The mitigation is a covariate that proxies it; `issuedCount /
  totalSupply` (primary sell-through) is the best one the contract supports, because a sold-out primary is
  direct evidence of excess demand at face. It is a proxy, class B, not a control.
- **The runner is correlated with the outcome.** Events with no resale activity are *not* a random sample of
  events: they are disproportionately the low-demand ones. Two specific consequences:
  (a) estimating $\sigma^2$ only on events that had transactions biases $\hat\sigma^2$ **downward**, which
  over-shrinks and makes cold-start intervals **too narrow** — so zero-sales events must be inside the
  $\sigma^2$ estimate, not dropped; and
  (b) the shrinkage weight $B=\sigma^2/(\sigma^2+v_e)$ is itself noisy when the number of events $J$ is
  small, and the honest handling is to report the prediction at two or three fixed values of $\sigma^2$
  rather than at one noisy estimate ([Efron & Morris
  1975](https://doi.org/10.1080/01621459.1975.10479864)).

**What we would need to defend it:** at least two completed events per stratum in which the pooling is claimed
to work, with observed resale activity in at least one of them. With one event per stratum there is nothing to
pool: $\sigma^2$ is unidentified and any pooling is a prior in disguise, which is admissible only if it is
declared as a prior with its value stated.

**Cross-reference, and a distinction that must not be lost.** A parallel finding, `02-e-cold-start.md`, concludes
that for a genuinely new event the partial-pooling point estimate *is* the population mean and that the interval
is the deliverable. That is correct for its object — the cold-start *price level* (markup over face), where
before any resale there is no within-event likelihood at all. It is not correct for the object here, the
cold-start *sale intensity*, in the case where the event has accumulated exposure and produced no transaction.
The two do not conflict; they diverge at a boundary condition, and the boundary condition is the whole of §6.1:
a zero over exposure $E$ enters the likelihood, so the estimate moves off the population mean and shrinks toward
zero as $E$ grows. Stated as a rule so the two files cannot be read against each other: **for the price level,
the cold-start estimate is the population mean; for the sale intensity, it is the population mean updated by the
observed zero.**

**A cheaper and stronger alternative where it applies.** If the strata are cities or organizers with several
completed events each, pool at that level and treat the event effect as nested within it. That is a real
exchangeability argument because the shared factor (a local market, an organizer's audience) is the thing
being pooled over, rather than an assumption that all events are alike.

---

## 7. What the product should display

### 7.1 The two statements, and why they cannot be merged

| | "Probability this ticket sells at price $p$" | "Historical sale rate for this tier at this time-to-event" |
|---|---|---|
| Status | **Not identified** (N1) | **Identified** (O1) |
| Needs | $\gamma$, i.e. asks on non-sellers | Counts and exposure, which we have |
| Answers | "should I ask $p$?" | "how much does this tier trade, and when?" |
| Is it a probability? | Yes, conditional on a chosen price | No — it is a retrospective frequency over all asks |
| Failure mode if shown | Silent, confident, wrong; monotone by construction | Read as a sale probability for the reader's own price |

### 7.2 What an organizer-facing tool must show

**Show the second, never the first, and label it so it cannot be misread.** Concretely:

1. **The base rate, with its denominator and window, front and centre.** "128 of 2,400 tickets in this tier
   transacted on resale before doors (5.3%, ± interval)." This is `EventAnalytics.resoldShare` computed
   honestly — the field already exists in the wire contract, which means the honest quantity is already
   specified and nothing new needs inventing.
2. **Timing.** "Half of those transactions happened in the last N days before doors." Uses O1, high value to
   an organizer deciding when to open the secondary window.
3. **The realised price distribution by time bucket** — O2, already the shape of `priceSeries` and
   `markupDistribution`. Labelled **"prices at which tickets actually sold"**, not "price curve", not
   "demand". Annotate the cap mass point, when it exists, as *"at the cap — a rationing point, not a
   market-clearing price"*.
4. **An explicit absence, where the sale-probability-at-a-price number would go.** Not a dash, not a greyed
   curve, not an interpolated line: a labelled statement. Suggested string, plain English:
   > "The platform does not record asking prices, so we cannot estimate the chance a ticket sells at a
   > specific price. What is shown is what actually happened."

   The reason it must be an explicit absence rather than an omitted panel: an empty space invites the reader
   to infer the number themselves from the price distribution, which is the error this whole file exists to
   prevent.
5. **For a seller's own ask: a position, not a probability.** "Your ask of X is above 80% of the prices at
   which tickets in this tier actually sold." Identified (it uses transaction prices), useful, and explicitly
   not a sale probability. Never multiply the position by the base rate — that product has no interpretation
   and will be read as a forecast.
6. **The caveats as labels on the object, not as prose at the bottom.** A footnote is not read. The label
   belongs on the number: *"base rate of transactions, all asks — not a sale probability at a given price"*;
   *"tickets still held are counted as not yet sold"*; *"n = …, window = …"*.

### 7.3 What the interface must never do

- Never plot the base rate against a price axis.
- Never label a rate "probability of sale", "chance it sells", or "liquidity score".
- Never draw a price-sale curve, even a dotted one — a dotted curve is a claim with a hedge, and the hedge is
  the part nobody reads.
- Never present the mean markup as a "market price" where the cap binds; it is a lower bound on value there
  (01-b §4.5, `00-data-situation.md` Gap 2).
- Never show a transaction count without its exposure window. A count of 90 sales is meaningless without
  "over 128 tickets and 11,400 ticket-days".
- Never let the primary-optimum panel imply causality from the secondary record (N4).

### 7.4 The interim route to the exposure split, which costs nothing but discipline

`Ticket.status` is a state, so it can be **polled**. `GET /api/tickets` is cursor-paginated and returns
`Ticket` rows; diffing the set of tickets in `status = "listed"` between two polls, at a known interval,
produces:

- an approximate `listedAt` (the first poll at which a ticket appears listed) and `delistedAt` (the first poll
  at which it is not), each accurate to the poll interval;
- `delistReason` **partially**: if the ticket's next ledger row after the listing is a `sale`, it sold; if it
  returned to `valid` with no sale row, it was withdrawn. `cap_blocked` and `expired` are **not** recoverable
  this way — a withdrew-at-the-cap and an expired-at-the-cap look identical;
- the **depth covariate** $w(t)$ directly, as the count of listings per tier at each poll.

What it does **not** produce is the ask price. So polling buys N2 (the split), the depth axis, and part of the
supply margin — and leaves N1 and N3 exactly where they are. Two consequences for ordering (see §9): exposure
is recoverable for near-free once a backend exists, and it is **irreversible** — every day without polling is
exposure that can never be reconstructed, because the state history is not stored. That makes polling the one
data action with a deadline, independent of the four-field request.

---

## 8. Evidence table

Nothing in this file is measured. No dataset was read, no estimator was run, no simulation was run. Every row
is an assertion, labelled with its programme class. The two MEASURED rows are schema facts, checked by the
commands quoted.

| # | Claim | Basis | Class |
|---|---|---|---|
| E1 | The wire contract has no listing start, ask, withdrawal, revision, or depth field. | **MEASURED.** `grep -n "listPrice\|listedAt\|delistedAt\|delistReason" lib/types.ts API_CONTRACT.md` → no match | verified |
| E2 | `TicketStatus` includes `"listed"` as a state; `EventAnalytics.resoldShare` already exists. | **MEASURED.** `lib/types.ts:22`, `lib/types.ts:192` | verified |
| E3 | $\lambda_{\text{obs}}(\tau,x)$, its CIF, and the competing-risks split are identified from the ledger alone. | Aalen multiplicative-intensity argument on the observed filtration; censused population | C |
| E4 | $\lambda_{\text{obs}}$ is the composite $s(t)\cdot\mathbb{E}[\lambda\mid\text{offered}]$, so it is not a sale hazard. | Algebra of the unrecorded offering state | C |
| E5 | $\xi(p,\tau,x)$, the joint mark–time intensity, is identified and is not a demand curve. | Joint observation of (time, price) on transactions; Working's identification critique | C |
| E6 | The price response $\gamma$ is not identified without asks on non-sellers. | 01-b T3, confirmed; case-only sample | C |
| E7 | The case-cohort subcohort must be drawn from listing *episodes*, not from tickets. | Design of the case-cohort estimator | C |
| E8 | Population-averaged covariate effects are attenuated under unobserved frailty. | Standard result for marginal vs conditional hazards | C |
| E9 | Notation: covariate coefficients here are associations, not per-ticket effects. | Follows from E8 | C |
| E10 | Under Q3-A (cap enforced on the ask), a sale at the cap identifies the ask exactly; under Q3-B it does not. | Enforcement logic; depends on Q3 | C |
| E11 | The cap stratum's hazard measures arrival speed under rationing, not acceptance. | Rent-seeking under a binding ceiling; 01-b §4.5 | B |
| E12 | Nothing in the record identifies a counterfactual in the primary price. | Selection on issuance; the population is defined by $p_0$ | C |
| E13 | The piecewise-exponential specification with an exposure offset is a Poisson regression, exactly. | Standard likelihood equivalence | C |
| E14 | The exact grouped-data link is complementary log-log; logit is an accurate small-hazard approximation. | Prentice & Gloeckler 1978; Allison 1982; Holford 1980 | C |
| E15 | Redemption must be a competing risk, not independent censoring. | Correlation between holding-for-use and not-selling | C |
| E16 | With a terminal point, the never-sold mixture fraction is identifiable; it is an upper bound on never-offered. | Cure-model identifiability given adequate follow-up | C |
| E17 | With the four fields, $\gamma$ as a conditional association is identified by standard counting-process theory; the causal reading additionally needs A2. | Cox 1972; Andersen & Gill 1982 | C |
| E18 | $\gamma$ is identified only from ask dispersion within $(e,g,\tau)$; zero dispersion means rank deficiency. | Column-space argument; stated in §4.4 | C |
| E19 | Omitting the time effect inflates $|\gamma|$; within-tier quality attenuates it; the net sign is unknown. | Direction of each confound, argued in §4.3 | C |
| E20 | The seller's cost basis is not a valid instrument on this platform. | Transaction history is public on-chain, so the exclusion restriction fails | C |
| E21 | The cap, where it binds, is a viable local instrument. | Policy-set, seller-independent shifter | C |
| E22 | An in-sample reliability curve is the score equation plotted, hence uninformative by construction. | Score equation for a cell intercept | C |
| E23 | A calibration claim needs a temporal holdout and IPCW-corrected scoring for censored outcomes. | Prequential evaluation; IPCW Brier | C |
| E24 | Cold-start prediction must shrink with the observed zero-exposure, not sit at the population mean. | Gamma–Poisson posterior predictive | C |
| E25 | Excluding zero-sale events from the $\sigma^2$ estimate biases it down and narrows cold-start intervals. | Selection on the outcome in a variance component | C |
| E26 | Polling `Ticket.status` recovers approximate listing spells and depth but never the ask. | Follows from the state being observable and the price not being in the contract | C |
| E27 | Resale prices fall as the event approaches while the sale hazard rises. | Sweeting 2012 (class A on MLB eBay listings, quoted in `01-a`) | A |
| E28 | The mechanism behind both is declining option value of continued search. | Sweeting 2012; revenue-management stopping structure | A / C |
| E29 | The four fields identify the secondary price response and still do not identify the primary optimum. | Two distinct gaps: asks, and selection on issuance | C |
| E30 | Which is bigger, the listing-propensity effect or the conditional-hazard effect, is unknown and unmeasured here. | No exposure data exists | UNVALIDATED |

Two claims I considered and deliberately did **not** make: that the base rate is approximately the hazard at
the prevailing ask (false in general — hazards are not linear in price, so the average of a nonlinear function
is not its value at the average), and that $\gamma<0$ follows from any demand argument (it does, but a
monotone curve fitted by maximum likelihood will look monotone whatever the truth, so the sign is not
evidence — 01-b's [D] warning, and the reason §4.2 puts the nonparametric form first).

---

## 9. What is unvalidated

Every item here is a hypothesis plus the experiment that would test it, per `records/README.md`. None may be
quoted as a result.

| Claim | Test that would validate it | Status |
|---|---|---|
| Specification A's covariate set predicts the base rate better than the raw stratum rate | Rolling-origin holdout on completed events, prequential Brier with IPCW, against the no-model baseline | **UNVALIDATED** |
| The proportional form A1 holds for the hazard | $\tau$-interaction test on a fitted model; check for crossing hazards on real data | **UNVALIDATED** |
| Ask dispersion within $(e,g,\tau)$ is non-zero enough to identify $\gamma$ | The §4.4 diagnostics, on the first real listing panel | **UNVALIDATED** — the fixture cannot answer it (`00-data-situation.md` §2) |
| $\hat\gamma$ approximates a causal response | Randomised ask arm, or the cap instrument where it binds; otherwise report the bound | **UNVALIDATED** |
| Events are exchangeable given covariates, hence partial pooling is admissible | Between-event variance computed *including* zero-transaction events; if it dominates, pooling buys little | **UNVALIDATED** |
| The cure fraction is material | Interval for $\pi$ from (5) on completed events | **UNVALIDATED** |
| The composite intensity is stable enough to be a product input | Two-origin stability check across successive event cohorts | **UNVALIDATED** |
| The self-dealing contamination is small | Same-wallet round-trip count on the real ledger | **UNVALIDATED** — unmeasurable on fixtures |
| The cap anchor of §2.5 exists at all | Q3's answer, plus one observed sale at a cap with an accompanying listing row | **UNVALIDATED** |
| The cold-start shrinkage is better than the population mean | Backtest on held-out events with zero early activity; compare predictive log score | **UNVALIDATED** |

One methodological claim that could be checked without ticket data, and should be before the estimator is
relied on: **that the implementation recovers the parameters that generated the data.** That is a simulation
study of estimator properties, admissible under `00-data-situation.md` §5 and labelled SIM, and it says nothing
about whether tickets behave like that. It is a build task for Phase 7, not a research result, and no number
from it may appear as accuracy.

---

## 10. Data requirements, in the order that buys most

Ranked by marginal identification bought per unit of engineering, not by how natural the field looks.

**1. `listPriceLamports` — the ask, on every listing, sold or not.** Buys N1 and N3, without which the
product's headline sentence cannot be said. Worth more than items 2–4 combined, because it is the only field
that puts a price into the risk set. Requirement on the *content*, not just the field: it must be recorded for
listings that never sell and it must be recorded per revision. A listing table that only logs completed sales
reproduces today's defect in a new schema.

**2. `delistReason ∈ {sold, withdrawn, expired, cap_blocked}`.** Buys the sold/withdrawn separation (which is
what turns a listing into a survival observation with a non-censored failure), the supply margin (time-to-
withdraw as an opportunity-cost object, Sweeting's central mechanism, currently invisible), and the
`cap_blocked` discrimination that separates "nobody wanted it" from "the cap rationed it" — the single
highest-information enum value in the whole request. Without it, a failed listing at the cap and a failed
listing at a delusional price are the same row.

**3. `delistedAt` — cheap, because it is nearly recoverable.** Polling `Ticket.status` gives it to the poll
interval (§7.4). Specify it anyway for precision, but do not let its absence block anything: start polling,
which is the only requirement here with a deadline, because unrecorded exposure is lost permanently.

**4. `listedAt` — cheapest of the four.** For a first listing it is bounded below by `issuedAt` and by the
previous ledger event, so its marginal information is the smallest of the four.

**5. Before or beside the above, three facts that are already inside the company and cost one message each**
(Q1, Q2, Q3 in `F-decision-log.md`):
- Q1 — does the internal ledger carry seat coordinates? If yes, A2's largest threat (§4.3, threat 1) shrinks,
  and the within-tier quality confound stops attenuating $\gamma$.
- Q2 — is anything deployed? A live program's transaction history is a small real dataset, and the recording
  schema is a research artefact worth getting right *before* launch rather than after.
- Q3 — is the cap enforced on the ask or on the transaction? This now has a concrete identification
  consequence (§2.5, §4.5): it decides whether the record contains one known ask value at all.

**6. A primary-inventory time series with on-sale, sell-out and hold-back timestamps.** Buys the demand bracket
of 01-b T4b as a booking curve rather than a snapshot, and it is the *only* route to the primary question that
does not require an experiment — because N4 cannot be closed with secondary data no matter how good it gets.

**7. Fee, royalty, and net-to-seller figures.** Needed for the primary objective (D4); neutral for the resale
ask (01-b §4.5(i)). Does not touch the sale hazard.

**8. Seat coordinates.** Does not enter the hazard directly, but it is the main confounder of $\gamma$ (§4.3)
and the dominant within-event price axis. Its value is second-order for the *base rate* and first-order for
the *price response*, which is a reason to raise its priority the moment item 1 lands.

**9. Any record of the buy side — bids, offers, views, searches.** Everything demand-side in this programme
rests on assumption. This is the largest absent observation and the only one that would let any statement be
about buyers rather than about tickets. No econometric adjustment substitutes for it.

Not on the list, deliberately: a "liquidity score" or any composite the platform would have to define before
the data exists. Composite indices computed from unidentified components are the failure mode this file is
written against.

---

## 11. Sources

Metadata for every item below was taken from Crossref during this pass, or, for items marked †, carried from
`01-b` where it was checked in that pass. No citation is from memory alone. No numeric result is quoted except
the direction of Sweeting's findings, which `01-a` records with its numbers.

† Allison, P. D. (1982). Discrete-time methods for the analysis of event histories. *Sociological Methodology*
13, 61–98. https://doi.org/10.2307/270718

Andersen, P. K., Abildstrøm, S. Z., & Rosthøj, S. (2002). Competing risks as a multi-state model. *Statistical
Methods in Medical Research* 11(2), 203–215. https://doi.org/10.1191/0962280202sm281ra

Andersen, P. K., & Gill, R. D. (1982). Cox's regression model for counting processes: a large sample study.
*The Annals of Statistics* 10(4), 1100–1120. https://doi.org/10.1214/aos/1176345976

† Boag, J. W. (1949). Maximum likelihood estimates of the proportion of patients cured by cancer therapy.
*JRSS-B* 11(1), 15–44. https://doi.org/10.1111/j.2517-6161.1949.tb00020.x

† Bollinger, C. R. (1996). Bounding mean regressions when a binary regressor is mismeasured. *Journal of
Econometrics* 73(2), 387–399. https://doi.org/10.1016/S0304-4076(95)01730-5

Borgan, Ø., Goldstein, L., & Langholz, B. (1995). Methods for the analysis of sampled cohort data in the Cox
proportional hazards model. *The Annals of Statistics* 23(5), 1749–1778.
https://doi.org/10.1214/aos/1176324322

† Bulow, J., & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer surplus. *JPE* 120(1),
160–186. https://doi.org/10.1086/665416

Clopper, C. J., & Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of
the binomial. *Biometrika* 26(4), 404–413. https://doi.org/10.1093/biomet/26.4.404

† Cox, D. R. (1972). Regression models and life-tables. *JRSS-B* 34(2), 187–202.
https://doi.org/10.1111/j.2517-6161.1972.tb00899.x

Dawid, A. P. (1984). Present position and potential developments: some personal views. Statistical theory: the
prequential approach. *Journal of the Royal Statistical Society A* 147(2), 278–292.
https://doi.org/10.2307/2981683

† Efron, B., & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *JASA* 70(350),
311–319. https://doi.org/10.1080/01621459.1975.10479864

Farewell, V. T. (1982). The use of mixture models for the analysis of survival data with long-term survivors.
*Biometrics* 38(4), 1041–1046. https://doi.org/10.2307/2529885

† Fine, J. P., & Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk.
*JASA* 94(446), 496–509. https://doi.org/10.1080/01621459.1999.10474144

Firth, D. (1993). Bias reduction of maximum likelihood estimates. *Biometrika* 80(1), 27–38.
https://doi.org/10.1093/biomet/80.1.27

† Gallego, G., & van Ryzin, G. (1994). Optimal dynamic pricing of inventories with stochastic demand over finite
horizons. *Management Science* 40(8), 999–1020. https://doi.org/10.1287/mnsc.40.8.999

Gneiting, T., & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation. *JASA*
102(477), 359–378. https://doi.org/10.1198/016214506000001437

Graf, E., Schmoor, C., Sauerbrei, W., & Schumacher, M. (1999). Assessment and comparison of prognostic
classification schemes for survival data. *Statistics in Medicine* 18(17–18), 2529–2545.
https://doi.org/10.1002/(sici)1097-0258(19990915/30)18:17/18%3C2529::aid-sim274%3E3.0.co;2-5

Holford, T. R. (1980). The analysis of rates and of survivorship using log-linear models. *Biometrics* 36(2),
299–305. https://doi.org/10.2307/2529982

† Lagakos, S. W. (1979). General right censoring and its impact on the analysis of survival data. *Biometrics*
35(1), 139–156. https://doi.org/10.2307/2529941

† Lakkaraju, H., Kleinberg, J., Leskovec, J., Ludwig, J., & Mullainathan, S. (2017). The selective labels
problem: decision making and predictability. *KDD '17*, 275–284.
https://doi.org/10.1145/3097983.3098066

Laird, N., & Olivier, D. (1981). Covariance analysis of censored survival data using log-linear analysis
techniques. *JASA* 76(374), 231–240. https://doi.org/10.1080/01621459.1981.10477634

Lancaster, T. (1979). Econometric methods for the duration of unemployment. *Econometrica* 47(4), 939–956.
https://doi.org/10.2307/1914140

Lee, D. S., & Lemieux, T. (2010). Regression discontinuity designs in economics. *Journal of Economic
Literature* 48(2), 281–355. https://doi.org/10.1257/jel.48.2.281

Maller, R. A., & Zhou, S. (1995). Testing for the presence of immune or cured individuals in censored survival
data. *Biometrics* 51(4), 1197–1205. https://doi.org/10.2307/2533253

† Murphy, A. H. (1973). A new vector partition of the probability score. *Journal of Applied Meteorology*
12(4), 595–600. https://doi.org/10.1175/1520-0450(1973)012%3C0595:ANVPOT%3E2.0.CO;2

Prentice, R. L. (1986). A case-cohort design for epidemiologic cohort studies and disease prevention trials.
*Biometrika* 73(1), 1–11. https://doi.org/10.1093/biomet/73.1.1

Prentice, R. L., & Gloeckler, L. A. (1978). Regression analysis of grouped survival data with application to
breast cancer data. *Biometrics* 34(1), 57–67. https://doi.org/10.2307/2529588

Prentice, R. L., Kalbfleisch, J. D., Peterson, A. V., Flournoy, N., Farewell, V. T., & Breslow, N. E. (1978).
The analysis of failure times in the presence of competing risks. *Biometrics* 34(4), 541–554.
https://doi.org/10.2307/2530374

† Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence from secondary markets
for Major League Baseball tickets. *JPE* 120(6), 1133–1172. https://doi.org/10.1086/669254

Van Calster, B., McLernon, D. J., van Smeden, M., Wynants, L., & Steyerberg, E. W. (2019). Calibration: the
Achilles heel of predictive analytics. *BMC Medicine* 17(1). https://doi.org/10.1186/s12916-019-1466-7

Vaupel, J. W., Manton, K. G., & Stallard, E. (1979). The impact of heterogeneity in individual frailty on the
dynamics of mortality. *Demography* 16(3), 439–454. https://doi.org/10.2307/2061224

Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference. *JASA* 22(158),
209–212. https://doi.org/10.1080/01621459.1927.10502953

† Working, E. J. (1927). What do statistical "demand curves" show? *QJE* 41(2), 212–235.
https://doi.org/10.2307/1883501

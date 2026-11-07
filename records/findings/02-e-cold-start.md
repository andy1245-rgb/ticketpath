# Phase 2-E — Cold start: pricing an event that has no resale history

**Status:** complete (first pass). **Written:** 2026-11-07T10:56Z. **Author:** Phase 2-E research agent.
**Scope:** RESEARCH-PROGRAM §3 Phase 2 B (historical price forecasting: hierarchical models, Bayesian
forecasting, sparse-data forecasting) as it applies to the cold-start case, plus the cold-start criterion
named in §3 Phase 4 ("Cold-start performance") and the evidence standards of §4.
**Depends on:** `AGENTS.md`; `RESEARCH-PROGRAM.md` §3 Phase 2 B, §3 Phase 4, §4; `records/README.md`;
`records/00-data-situation.md` (D1, D2, D3; Gaps 1-4); `records/findings/01-b-identifiability.md`
(§4.1 T1, §4.4 T4b, §4.5 T5, §4.6 T1′ cold start, measurement error); `records/findings/01-a-market-structure.md`
(§2 price path, §3 caps, §4 primary vs secondary, §5 liquidity, §6 what survives); `records/F-decision-log.md`
(D1, D2, D3); `../ticketing-frontend/lib/types.ts` (read field by field in this pass);
`records/E-data-source-registry.md` (S7 Get Protocol not obtainable; S8 own ledger).
**Append-only.** Nothing here edits another file; the registry rows this implies are listed in §10.

**Evidence discipline.** Every load-bearing statement is tagged **[MEASURED]** (checked in this pass, method
quoted) or **[ASSERTED]** (argued or cited), and carries a §4.3 class A-E. **[COMPUTED]** marks arithmetic I ran
in this pass on cited inputs: class C, a fact about the algebra or the distribution, not about tickets.
No number in this file comes from `lib/mock/`. No accuracy or coverage figure appears anywhere, because none
has been measured.

---

## 1. What I concluded

**The smallest defensible answer, in one sentence.** A band on the log price ratio to the organiser's own face
value, whose width is declared from the spread between events rather than measured, truncated from above at the
cap, labelled as a prior, and shown beside the exact arithmetic of the cap ceiling and the fee. No point estimate,
no sale probability, and no claim that the chosen face is optimal. Everything below is the argument for each of
those five clauses, and the conditions under which each would change.

1. **The cold-start answer is a band, and its width is the whole deliverable.** For a genuinely new event the
   partial-pooling point estimate *is* the population mean, so the hard quantity (the spread between events) does
   not move the point at all. It moves only the interval. That inverts the usual modelling priority: at cold start
   the between-event variance is not a nuisance parameter to be estimated on the way to a number, it *is* the
   number. (§4.4) **[ASSERTED]** class C.

2. **Face value is the only anchor that exists at cold start, and the target must therefore be the ratio to face,
   not a price.** This is the constructive use of T1's affine indeterminacy: the level is not identified
   (`01-b` §4.1), but the *ratio* is the object the decision needs (face is the organiser's own price, markup is
   already denominated in bps over face in the contract) and the ratio is dimensionless, which is the only reason
   cross-event pooling is defensible at all. (§2.3, §4.1) **[ASSERTED]** class C.

3. **Three of the fields the brief nominates as cold-start predictors do not exist in the contract.** Event
   category, on-sale timing and venue capacity are absent from `lib/types.ts`: `Event` carries 17 fields, and a
   grep over `lib/`, `app/`, `components/` and `API_CONTRACT.md` for category/genre/on-sale/capacity returns no
   field, only one prose string inside a mock fixture. (§2.1, §2.2) **[MEASURED]**.

4. **One field pair supplies a real, mechanism-grounded signal before any resale: primary sell-through**
   (`issuedCount` / `totalSupply`, per tier and at event level). It delivers a *sign*: sold out at face implies
   excess demand at face and hence resale at or above face; unsold supply at face implies the marginal buyer's
   willingness to pay is at or below face. It cannot deliver a level. This is the only cold-start variable whose
   mechanism is a bound rather than a guess, and it is already in the schema. (§2.4) **[ASSERTED]** class C, with
   class A support from the auction and repricing results in `01-a` §4.

5. **Recommendation: (b), partial pooling on the per-event mean log price ratio to face, with the between-event
   variance *declared* rather than estimated below about five events, and the cold-start band reported as a
   sensitivity range over that declaration.** Degrade to (a), face value plus cap arithmetic, at zero or one
   event. Demote (c), nearest-neighbour comparables, to a support diagnostic: it cannot even define its own
   distance metric from the contract, since the covariate that would carry most of the information (category) is
   absent. (§3) **[ASSERTED]** class C for the estimator, class D for the choice.

6. **With few events, four things can bound the between-event variance, and none of them estimates it.** The
   method-of-moments estimator (1 degree of freedom at J = 2); an upper confidence limit from the Q statistic,
   which is the only *conservative* object available; a grid posterior under a declared prior, which at J ≤ 2 is
   just the prior wearing a posterior's clothes and must be said to be that; and a declared floor. The cost of a
   small J is computable and large: at J = 5 the 95% interval for the between-event variance spans a factor of 23
   (0.12x to 2.79x the point estimate), at J = 2 it spans 0.001x to 5.02x. (§4.4) **[COMPUTED]** class C.

7. **Nothing at cold start supports a coverage claim, so the interval must be named for what it is.** It is a
   prior-predictive (or, once τ is estimated, an approximate predictive) interval for *the event's mean log
   ratio*, not for a single ticket's price and not a confidence interval. Three distinct objects get confused in
   practice and the UI must keep them apart. (§5) **[ASSERTED]** class C.

8. **One cold-start choice is destructive to learning: a tight resale cap.** The cap censors the value signal at
   exactly the events where value is highest (`01-b` §4.4, `01-a` §3), so a cap set tight at launch means the
   engine can never observe the markups it needs to price the next event. At cold start the cap is not only a
   policy instrument, it is a data-collection instrument. (§6.2) **[ASSERTED]** class C plus class D on the
   magnitude.

9. **The demo must be built to be correct at zero events, not to be rescued by data.** Every number the engine
   will show on stage on day one is a prior, and the only honest cold-start point-like statement available is
   about the cap, which is exact arithmetic. The label must sit adjacent to the number at the same weight, and
   the label must change the moment the event's own sales exist. (§7) **[ASSERTED]**.

10. **The cold-start band prices the resale ask, not the ticket.** Because the band is denominated in the face value
    the organiser is choosing, moving face moves the band proportionally and "set face to the middle of the band" is
    circular (the same scale-freedom `01-b` §4.5(ii) uses for the cap). So the cold-start output cannot set the
    primary price. Only the demand side can, and before any resale the only demand observation in the schema is
    primary sell-through, which gives a sign and not a level. This is the sharpest consequence of face being
    endogenous and it should appear next to T1 in the deliverable. (§4.1, §6.2(4), §6.3) **[ASSERTED]** class C.

---

## 2. What actually exists before the first resale

### 2.1 Measured inventory

| Item | Result | Tag |
|---|---|---|
| `Event` fields | 17: `id, slug, name, description, venue, city, startsAt, endsAt, imageUrl, organizer, status, tiers, totalSupply, issuedCount, resaleEnabled, resalePriceCapBps, requiresVerifiedWallet` | **[MEASURED]** (interface body parsed from `lib/types.ts`) |
| `TicketTier` fields | 5: `id, name, faceValueLamports, totalSupply, issuedCount` | **[MEASURED]** |
| `Organizer` fields | 4: `id, name, walletAddress, verified` | **[MEASURED]** |
| `Ticket` fields | 14, of which `lastSalePriceLamports` and `transferCount` are null/zero before any resale | **[MEASURED]** |
| Category / genre field | none. Regex over `lib/`, `app/`, `components/`, `API_CONTRACT.md` for `category|genre` hits only a prose sentence in `lib/mock/events.json` | **[MEASURED]** |
| On-sale timestamp | none. No `onSaleAt`, `publishedAt`, `createdAt`. `EventStatus` transitions are unlabelled (`00-data-situation.md` §4) | **[MEASURED]** |
| Venue capacity | none. `totalSupply` is ticketed supply, not capacity | **[MEASURED]** |
| Toolchain | `python3` 3.12.3; `import numpy` and `import scipy` both raise `ModuleNotFoundError` | **[MEASURED]** (confirms D2) |

### 2.2 The brief's list, checked one field at a time

| Nominated predictor | Present in contract | Cold-start predictor? | Mechanism, stated | Class |
|---|---|---|---|---|
| **Face value** (`faceValueLamports`, per tier) | yes | **Yes, as the numeraire and the only anchor** | It is the primary price the organiser asks, so it fixes the denominator of every markup. It does not predict value; it defines the unit in which value is expressed. Endogenous (`01-b` §4.1), so it cannot also serve as evidence about the level | C |
| **Tier structure** (count, price ladder, supply split) | yes | **Yes, weak but real** | Multi-level pricing exists to separate willingness to pay along a quality axis. `01-a` §2 records that "the maximum number of price levels for a single event in our data is four, with most events offering tickets at only two", and that multi-category pricing beats single-price by about 5% (Courty & Pagliero). A second tier is therefore evidence that the organiser believes demand is heterogeneous, and heterogeneity is what produces a resale spread. Direction: more tiers and a steeper ladder should widen the markup distribution, not necessarily raise its mean | A for the revenue effect in that market, D for the transfer |
| **Event date** (`startsAt`) | yes | **Yes, as a horizon index, not as a level** | The secondary path declines with time to event (`01-a` §2: Sweeting's sellers cut by 13/18/40% of face across relistings; "40 percent or more" in the final month; Leslie & Sorensen's near-flat path with "a modest uptick in the last week"). So a cold-start prior is only comparable to another event at a similar remaining horizon. Pooling across horizons mixes regimes | A |
| **City** | yes, free text | **Marginally, and only after an external join** | Demand density against local supply. The join is on a free-text string; `S23` (Census/DMA) exists but nothing in the contract is a key. Mechanism is real, implementation risk is string matching, and with J small a city dummy is unestimable anyway | D |
| **Category** | **no** | **Would be the best single covariate, and it is not there** | Between-event variation in markup is plausibly dominated by *what the event is* (artist draw, rivalry, one-off versus recurring), which is not recoverable from `name` and `description` by any rule that generalises. This is the strongest argument against the comparables strategy (§3.3) | D |
| **On-sale timing** | **no** | **No, and its absence also kills sell-through velocity** | Time since on-sale is the denominator of a booking curve. Without it we observe the sell-through *level* and the time-to-event, never the rate | — |
| **Venue capacity** | **no** (`totalSupply` is not capacity) | **Weak substitute: `totalSupply`** | Supply relative to the local market is the mechanism, and `totalSupply` measures only the ticketed part. Capacity would need `S21` (manual venue charts) keyed on free-text `venue` | D |
| **`resalePriceCapBps`** | yes, nullable | **Yes, and mechanically exact** | Two effects, both certain. (i) It truncates the observable markup from above, so any pooled mean fitted to capped data is a lower bound (`01-b` §4.4, `01-a` §3). (ii) At a binding cap the recorded price is the cap, so the engine can predict the *recorded* markup at a sold-out capped event with near-certainty while knowing nothing about value. Those two must never be presented as the same statement | C for (i) as a construction, B for the evidence that caps bind and ration (`01-a` §3), C for (ii) |
| **`resaleEnabled`** | yes | **Yes, binary and decisive** | If false, resale either does not happen or happens off-ledger, and off-ledger means unobserved (`01-a` §6, key handoff). A cold-start prior fitted on events with resale enabled does not transfer to events where the only resale is invisible | C, D for magnitude |
| **`requiresVerifiedWallet`** | yes | **Present, sign unknown** | Two opposing mechanisms: a gate shrinks the buyer pool (lower price) and raises buyer confidence (higher price). With J small the sign is not estimable and must not be assumed | D |
| **`organizer.id`** | yes | **Yes, and the best pooling stratum when it has history** | An organiser's own past events share the audience, the venue relationships and the marketing, so their residuals are the most plausibly exchangeable of any grouping available. Note the demo case: a *new* organiser has zero events in this stratum, so the stratification that would help most is exactly the one that is empty (§7) | D |
| **`status`** (`draft`/`on_sale`/`sold_out`/...) | yes | **Yes, coarse, and it is a state not a date** | `sold_out` at face is the strongest single pre-resale fact (§2.4). But the transition times are unrecorded, so the state has no clock | C |

### 2.3 What "comparable" has to mean, and why "comparable events" is not a mechanism

Two events are comparable for pricing purposes if their *residuals* are exchangeable, that is if, after the
observable covariates are removed, what is left over is a draw from one distribution. That is a claim about a
covariate you cannot see, not about a covariate you can. Matching on observables is at best a partial defence, and
the brief is right that "comparable events" stated without this is an empty phrase.

Concretely, four conditions have to hold before calling two events comparable here, and they are testable in
principle except the last:

1. **Same pricing institution.** Same cap regime (capped or not, and whether the cap binds), same
   `resaleEnabled` and `requiresVerifiedWallet` rules. A capped event's markup distribution is truncated at a known
   point; an uncapped one's is not. Mixing them in a pooled mean is a specification error, not a small bias.
2. **Same meaning of face.** `faceValueLamports` must be the primary transaction price per ticket under the same
   disclosure convention. Where the US all-in display rule applies (16 CFR Part 464, effective 2025-05-12,
   `01-a` §1), pre-rule quotes are pre-fee and post-rule quotes are all-in, so a pooled series spanning that date
   manufactures a level shift that reads as a market move.
3. **Same position on the path.** Same remaining-horizon bucket. The decline is the default regime (`01-a` §2), so
   an event priced 60 days out and an event priced 3 days out are different populations.
4. **Exchangeable demand shocks.** This is the one that cannot be checked for a new event by construction.

Condition 4 is why the honest object is a variance and not a set of neighbours: dispersion between events is the
measured statement of how *un*exchangeable they are, and the literature's own dispersion says they differ a lot.
`01-a` §5 records that about 5% of purchased tickets resell on average while the most active event in the same
sample reached 17%: a factor of about 3.4 in resale propensity across events that the authors could observe. If
events differ that much in whether they trade at all, they are unlikely to be interchangeable in what they trade
*for*. **[ASSERTED]** class A for the propensity figures, class D for the inference to markup.

### 2.4 The one observation that is not fixed metadata

Primary sell-through is the only cold-start quantity that changes as the event approaches, and it arrives before
any resale:

- `issuedCount / totalSupply` at event and tier level, plus `status`.

Two sign results follow from it, both cheap and both usable at zero events with resale history:

- **Sold out at face** implies a buyer was rationed at face, so some willingness to pay exceeds face, so resale at
  or above face is possible. If a cap is set, the recorded markup will sit at or near the cap. This is a
  *one-sided* statement and a *recorded-price* statement.
- **Not sold out at face** implies supply remains at face, so the marginal buyer's willingness to pay is at or
  below face, so the resale price of a marginal ticket is at or below face. Again one-sided.

Both are class C by construction (a sell-out is a quantity constraint at a posted price). Both are only as good as
the field's meaning: `00-data-situation.md` §4 and `01-b` §5 both flag that `issuedCount` may mean *minted* rather
than *sold*, which would destroy the inference. That is an operator question (§10) and until it is answered the
sell-through signal is **UNVALIDATED**.

The auction result in `01-a` §2/§4 is the class A support for the direction: Budish and Bhave matched primary
auctions to resale values and found auctions "substantially improved price discovery, roughly doubled performer
revenues, and, on average, nearly eliminated the arbitrage profits". Arbitrage profits that an auction removes are
exactly excess demand at a posted price. So "sold out at face means resale clears above face" is not a conjecture;
it is the mechanism the auction literature measures.

---

## 3. The three strategies, compared honestly

Notation used throughout. For sale $i$ in event $j$ with price $p_{ij}$ and that ticket's own tier face $f_{ij}$,
the observation is the log price ratio

$$y_{ij}=\log\frac{p_{ij}}{f_{ij}}=\log\left(1+\text{markupBps}_{ij}/10^{4}\right),$$

which is the contract's `markupBps` in natural units and is dimensionless. Event $j$ contributes
$y_j=\frac{1}{n_j}\sum_i y_{ij}$, the log of the geometric-mean markup, with sampling variance
$s_j^2=\sigma_j^2/n_j$ where $\sigma_j^2$ is the dispersion of log ratio across that event's tickets. A markup of
$b$ bps is $\exp(y)-1$ and vice versa.

### 3.1 (a) Face value with a policy adjustment

**What it says.** The ticket is worth its face value, modified only by the policy fields. In this form the rule is
$p_0 = f$ (an organiser inputs face), the resale band is reported around $f$, and the cap sets the top of the band
exactly.

**Data requirement.** None beyond the event record. Works at J = 0.

**What the policy adjustment actually is, exactly.** Only two adjustments are arithmetic rather than guessed:

- The cap is a hard ceiling, so no recorded resale can exceed $f(1+c)$. This part is exact.
- Fees shift the *primary* optimum but not the resale ask: an ad-valorem fee is neutral for the ask because
  $\arg\max_p p(1-\phi)h(p)=\arg\max_p p\,h(p)$ (`01-b` §4.5(i)). So the missing fee field does not block (a).

Everything else called "policy adjustment" is a guess with a sign, not a size: `resaleEnabled = false` means the
value signal will never be observed; `requiresVerifiedWallet` has two opposing mechanisms (§2.2).

**Failure mode.** It reports face value as though face were evidence about worth. It has no mechanism connecting
face to willingness to pay, and the programme's central class A fact is that the connection is loose and
systematic: primary tickets are priced below secondary clearing value, with resale averaging 41% above face on the
roughly 5% of tickets that resell (`01-a`, what it concluded). A rule that says "worth face" is therefore biased
down on exactly the events where it matters, and biased up (or down, it does not say) when the event is cold.

**What it reports as uncertainty.** Nothing, in its bare form. With a prior on the population spread bolted on, it
reports the population spread, which is no longer (a) but (b) with no pooling.

**Verdict.** The correct *degrade target*, not the correct primary. Keep it because it never fails, and because
parts of it are exact.

### 3.2 (b) Cross-event pooled model, unit of pooling the event

**What it says.** Events are draws from a population. Each event has its own mean log ratio $\theta_j$; the
population has a mean $\mu$ (possibly a function of covariates) and a between-event spread $\tau$. A new event's
$\theta$ is predicted from the population, shrunk by how little is known about it.

**The model, in the event-mean (meta-analytic) form.**

$$\begin{aligned}
y_j &\sim \mathcal{N}(\theta_j,\ s_j^2), \qquad s_j^2=\sigma_j^2/n_j \\
\theta_j &= x_j'\beta + u_j, \qquad u_j \sim \mathcal{N}(0,\tau^2)
\end{aligned}$$

Marginalising $u_j$ gives the form actually used:

$$y_j \sim \mathcal{N}(x_j'\beta,\ s_j^2+\tau^2).$$

**Number of parameters.** Hyperparameters: $\beta$ with $k+1$ components (intercept plus $k$ covariates) and
$\tau^2$, so $k+2$. The $s_j^2$ carry $J$ nuisance variances if estimated per event, or 1 if pooled to a common
$\sigma^2$. The $J$ random effects $u_j$ and $\mu$'s per-event counterparts are integrated out, so they are not
parameters of the fitted object even though $J$ latent $\theta_j$ exist. Total: **$k+2$ hyperparameters, plus
$J$ (or 1) variance nuisance parameters.** With no covariates at all, which is the honest cold-start model, that is
**2 hyperparameters**.

**The point that governs everything else.** The amount of information about $\mu$, $\beta$ and $\tau^2$ scales in
$J$, the number of events, **not** in $\sum_j n_j$, the number of tickets. A thousand sales inside one event give
one draw of $\theta_j$. This is why the cold-start problem does not melt with volume.

**Data requirement.** $J \ge 2$ events with at least one resale each to estimate $\tau^2$ at all; $J \ge k+2$ for
$\beta$ to be identified at all and $J \ge k+3$ before a covariate is allowed in, since a fit with one residual
degree of freedom estimates nothing; and the strata conditions of §2.3 to hold.

**Failure mode.** It assumes exchangeability, which is unverifiable for the newest event and is exactly the
assumption a cold-start event has no right to make: a brand-new organiser's event shares neither audience nor
history with the pool. If $\tau$ is large relative to $\mu$ (events really are idiosyncratic), the pooled answer
is face value with a very wide band, and it should be reported that way rather than pretending precision. Second
failure mode, specific to this platform: if the cap binds, the likelihood is truncated from above and the pooled
mean is a *lower bound*; a plain normal likelihood on capped data is the wrong likelihood (`01-b` §4.4).

**What it reports as uncertainty.** An interval for $\theta_{\text{new}}$ whose width is
$\sqrt{\tau^2 + V(\tau)}$ with $V$ the posterior variance of $\mu$: directly interpretable, and honestly wide when
$J$ is small. It is the only one of the three strategies whose uncertainty statement is generated by the model
rather than bolted on afterwards.

### 3.3 (c) Comparable-sales nearest-neighbour rule

**What it says.** Find the $k$ most similar events in the record and average their markups, distance-weighted.

**Data requirement.** Events with resale, plus a distance metric over event attributes.

**Failure mode, and it is fatal at cold start rather than merely awkward.** Measured in this pass, the contract has
no category field (§2.1). The single covariate that would carry most of the between-event signal is absent, so the
metric must be built from free-text `city`/`venue`, tier count, `totalSupply`, and time to event. Four roughly
ordinal attributes over $J$ points. Then:

- **With few events the nearest neighbour is the whole sample.** If $J \le k$ the rule degenerates to the arithmetic
  mean with extra steps, and its reported spread is the spread of everything.
- **The distance weights are chosen by whoever can see the answer.** Reported spread is then post-selection and too
  narrow, because the same choice that made the neighbours look alike selected for a small spread.
- **$k = 1$ reports a zero-width interval.** A nearest-neighbour rule with one neighbour is a point estimate with no
  uncertainty statement at all, which is the failure this whole finding exists to avoid.
- **The comparable-sales logic has a known pathology in the one field that uses it as its standard method.**
  Anenberg shows that valuation anchored on recent comparable sales propagates and smooths shocks in housing, that
  is, the method's output is a lagged function of the population rather than a measurement of the subject. Ticket
  events are one-off rather than repeated, so the smoothing is worse here, not better.

**What it reports as uncertainty.** The spread of the neighbours. With small $k$ that is not an interval in any
sense, and its width is monotone in exactly the thing that should make you distrust the estimate.

**Verdict.** Keep it as a *support diagnostic*: nearest-neighbour distance tells you whether a new event sits inside
or outside the covariate support of the pooled model, which is genuinely useful and is a different question from
prediction. Do not let it produce the number.

### 3.4 Head to head

| | (a) Face + policy | (b) Partial pooling | (c) NN comparables |
|---|---|---|---|
| Data needed | none | $J \ge 2$, and $J \ge k+3$ before a covariate enters | $J$ large enough that neighbours are distinguishable |
| Works at J = 0 | yes | no (degrades to a prior) | no |
| Mechanism stated | none (identifies the numeraire only) | exchangeability of events given covariates | similarity in observed attributes |
| Uses the cap | exactly | as a truncation to be modelled | not at all |
| Bounded above by the cap | yes, by construction | only if the likelihood is truncated | no |
| Uncertainty generated by the model | no | yes | nominally, and it is post-selection |
| Failure that is silent | claims face is worth | claims exchangeability, and truncation bias if the cap binds | selected spread, arbitrary metric, no covariate that matters |
| Computational cost (D2, stdlib) | none | trivial: a 1-D grid over $\tau$, see §4.8 | trivial |
| Best use | degrade target and the exact-arithmetic layer | the cold-start number | support diagnostic, and a check on (b) |

### 3.5 Recommendation, and what would reverse it

**Recommend (b)**, with the between-event variance declared rather than estimated while $J$ is small, the band
reported as a sensitivity range over that declaration, the likelihood truncated at the cap when the cap binds, and
**(a) as the fallback at $J \le 1$**. Keep **(c)** as a support check and never as the reported number.

**This reverses if any of the following is observed on the platform's own first events** (each is a measurement,
not an opinion):

1. **Covariate-explained variance approaches total between-event variance.** Fit a model with and without
   $\beta$. If the residual $\hat\tau^2$ is essentially unchanged, then the observable attributes carry nothing and
   the pooled model is worse than honest face value because it implies a mechanism it does not have. Report (a).
2. **High heterogeneity with no covariate to absorb it.** Using the $I^2$ convention (`01-b` cites Higgins &
   Thompson), if the between-event share of variance dominates, the pooled mean is a poor predictor and the deliverable
   becomes face value plus a wide, declared band plus the cap flag. This is still an answer; it is just not a
   forecast.
3. **Mass at the cap.** If real events show a mass point at `markupBps` equal to the cap, the likelihood must be
   truncated and the pooled mean becomes a bound, not a mean. That reverses the estimator's *form*, not the pooling.
4. **Seat coordinates arrive** (`01-b` §6, `00-data-situation.md` Gap 3). That raises within-event dispersion
   $\sigma^2$, which raises the number of own-event sales needed before the event's own data dominates (§4.6). A
   data arrival therefore *lengthens* the cold-start window. Counterintuitive and worth stating, because it is the
   opposite of the usual intuition that more data helps immediately.

---

## 4. The estimator, written out for pure Python

Constraint D2 applies: standard library only. Verified in this pass that `numpy` and `scipy` are absent
(**[MEASURED]**). Everything below is closed form except one 1-D grid over $\tau$, two bisections, and the
regularized incomplete gamma function needed for the chi-square quantiles of §4.4(ii), which is 40 lines of
series and continued fraction.

### 4.1 The target, and why it is a ratio

The target is $\theta_j$, the event's mean log price ratio to face, and its exponentiated form
$\exp(\theta_j)-1$, the geometric-mean markup. Three reasons this is the right object and not a concession:

1. Face is the only price in the record, and T1 (`01-b` §4.1) says the level of value is identified only up to an
   affine transformation. The ratio is invariant to the location part of that indeterminacy when face is the
   denominator, which is why the *decision* can proceed while the *level* stays unidentified.
2. The contract already denominates resale in `markupBps` over each ticket's own tier face, with an explicit warning
   that it must not be re-derived from an event-level face (`PricePoint.avgMarkupBps`). The ratio matches the
   schema.
3. It is dimensionless, so pooling across events with different face values is a first-order legitimate operation
   rather than an apples-to-oranges sum.

The geometric mean rather than the arithmetic mean is deliberate: the markup distribution is right-skewed
(`01-a` §2: 25% of resold tickets above +67%, 26% below face), a handful of very high markups would dominate an
arithmetic mean over a few dozen sales, and the log scale makes the between/within decomposition additive.

**What the estimator must never do.** It must not report $\exp(\theta)-1$ as "what the ticket is worth". It is what
a *resold* ticket fetched. `01-a` §6 records that resold tickets are the better seats (mean seat-quality percentile
0.61 against 0.50 for all tickets), so the conditional object is biased up relative to a randomly chosen ticket,
and the whole distribution applies only to the roughly 5% that transact twice. A second consequence follows from the
denominator rather than from selection: because the band is expressed in units of face, it informs the resale ask
and cannot inform the choice of face (§6.2(4)).

### 4.2 The model

$$\begin{aligned}
\text{within:} \quad & y_{ij}=\log(p_{ij}/f_{ij}) \sim \mathcal{N}(\theta_j,\ \sigma_j^2)\\
\text{between:}\quad & \theta_j \sim \mathcal{N}(x_j'\beta,\ \tau^2)
\end{aligned}$$

with $\beta$ flat-prior. Cold start takes $x_j' = 1$, so $\beta$ collapses to a scalar $\mu$: **two
hyperparameters, $\mu$ and $\tau^2$.** Covariates are added one at a time and only once $J \ge k+3$, with the order
fixed in advance by §2.2's mechanism argument (log face, then tier count, then sell-through state, then city). No
data-driven variable selection: with $J$ this small, selection is fitting the noise.

### 4.3 The update rule, explicitly

Given $\tau^2$, the shrinkage weight and the estimate for event $j$ are

$$B_j=\frac{\tau^2}{\tau^2+s_j^2},\qquad \hat\theta_j=B_j\,y_j+(1-B_j)\,\bar y(\tau),\qquad
\bar y(\tau)=\frac{\sum_j y_j/(s_j^2+\tau^2)}{\sum_j 1/(s_j^2+\tau^2)}.$$

This is the posterior mean under a normal-normal hierarchy,
$\big(y_j/s_j^2+\mu/\tau^2\big)\big/\big(1/s_j^2+1/\tau^2\big)$, rearranged. **$B_j$ is the weight on the
event's own mean; $1-B_j$ is the weight on the population mean.** $B_j$ is increasing in $\tau^2$ (events really do
differ) and increasing in $n_j$ (this event has its own evidence), and it does not depend on $\mu$.
Two limits are the whole cold-start story:

- **A genuinely new event has no $y_{\text{new}}$**, equivalently $s_{\text{new}}^2=\infty$, so $B_{\text{new}}=0$
  and $\hat\theta_{\text{new}}=\bar y(\tau)$: the answer is the population mean.
- **Therefore $\tau^2$ does not enter the cold-start point estimate at all.** It enters only the interval, through
  the predictive variance $\tau^2 + V(\tau)$. The most poorly identified parameter in the problem is also the only
  one that does not matter for the number and the only one that matters for the honesty of the number.

For a *future* sale in the new event, add the within-event term: the predictive variance is
$\tau^2 + V(\tau) + \sigma^2$ for a single ticket, and $\tau^2 + V(\tau)$ for the event mean. Those are different
objects and §5.1 keeps them apart.

### 4.4 What estimates the between-event variance when there are few events

Four options, in ascending order of honesty about what is being assumed. All four are implemented or specified
below. **None of them estimates $\tau^2$ when $J$ is small; they constrain it, and the difference must be said out
loud.**

**(i) Method of moments (DerSimonian-Laird).** With $w_j=1/s_j^2$,

$$Q=\sum_j w_j(y_j-\bar y_w)^2,\qquad \hat\tau^2=\max\left(0,\ \frac{Q-(J-1)}{\sum_j w_j-\sum_j w_j^2/\sum_j w_j}\right).$$

With known $s_j^2$ this is unbiased at the true $\tau^2$; with estimated $s_j^2$ it is biased and the weights are
noisy, which is why alternatives exist (Sidik & Jonkman). One degree of freedom, one number, no interval: it is a
point estimate of a variance from $J-1$ df and nothing more.

**(ii) An upper confidence limit from $Q$, which is the only conservative object available.** Because $Q$ is
approximately $\chi^2_{J-1}$ under $\tau^2=0$, solving $Q(\tau^2)=\chi^2_{J-1;0.975}$ for $\tau^2$ gives an upper
limit (Viechtbauer). This is the right thing to put in a cold-start band, because too narrow a band is a false
claim while too wide a band is merely uninformative, and the loss is asymmetric.

**How badly is $\tau^2$ pinned?** Computed in this pass from the $\chi^2$ quantiles (incomplete gamma by series and
continued fraction, quantile by bisection, 2.5% and 97.5% points, 1e-12 convergence) **[COMPUTED]** class C:

| $J$ events | 95% interval on $\tau^2$, as a multiple of the $Q$ point estimate | span |
|---|---|---|
| 2 | 0.001x to 5.02x | 5100x |
| 3 | 0.025x to 3.69x | 146x |
| 4 | 0.072x to 3.12x | 43x |
| 5 | 0.121x to 2.79x | 23.0x |
| 8 | 0.24x to 2.29x | 9.5x |
| 10 | 0.30x to 2.11x | 7.0x |
| 15 | 0.40x to 1.87x | 4.6x |
| 20 | 0.47x to 1.73x | 3.7x |

This is the answer to "do not wave at it". At five events the between-event *variance* is known to within a factor
of 23, so the *standard deviation* to within a factor of about 4.8. Any single number quoted for it at $J=5$ is
decoration. At $J=2$ the interval is useless in both directions. Below 20 events there is no rung of this table at
which a point estimate of $\tau^2$ deserves to be reported without the table.

**(iii) A grid posterior with a declared prior.** With $\mu$ integrated out under a flat prior, the marginal
likelihood of $\tau$ is closed form:

$$p(y\mid\tau)\ \propto\ \Big(\prod_j (s_j^2+\tau^2)^{-1/2}\Big)\Big(\sum_j (s_j^2+\tau^2)^{-1}\Big)^{-1/2}
\exp\!\Big(-\tfrac{Q(\tau)}{2}\Big),$$

so a 601-point grid over $\tau\in(0,\tau_{\max}]$ multiplied by a half-normal or half-Cauchy prior (Gelman 2006, on
why a half-Cauchy or folded-$t$ scale parameter is the weakly informative default when the number of groups is
small) gives the posterior of $\tau$, and the mixture over the grid gives the predictive for
$\theta_{\text{new}}$ by the law of total variance. This is the recommended route because it never produces a
negative or zero variance, it degrades gracefully to the prior at $J=1$, and it costs a 601-point loop.

**What it does at $J \le 2$ must be stated, not hidden: the output is the prior.** With one event there is no
between-event information in the data, so the posterior over $\tau$ equals the prior over $\tau$ up to the
likelihood of a single draw. Printing that as a "credible interval" without saying whose prior produced it would be
the exact failure this finding exists to prevent.

**(iv) A declared floor.** A minimum $\tau^2_0$ below which the estimate is not allowed to fall, chosen from
outside the data (§4.7) and reported alongside the sensitivity grid. The floor is what protects against the specific
pathology in §4.5.

**Cross-check rule.** Report (iii) as the band, (i) and (ii) as printed cross-checks with their $J$, and (iv) as the
declared floor. If (ii)'s upper limit is much wider than (iii)'s interval, or (i) is at the floor while (ii) is not,
say so on the surface rather than picking one.

### 4.5 The two degenerate cases, explicitly

**$\hat\tau^2 \le 0$ from the moment estimator.** This happens whenever $Q \le J-1$, which is roughly half the time
when $\tau^2$ is small. Truncating at zero is standard and it is wrong for prediction in a specific way: it sets
$B_j=0$ for every observed event, so every event's own mean is discarded and each is replaced by the pooled mean.
That half is merely wasteful. The dangerous half is what it does to the interval, and the trap is that the
cold-start point estimate was the pooled mean anyway, so nothing visible moves: the predictive variance loses its
$\tau^2$ term and collapses to $V(0)$, the variance of a pooled mean computed as if all $J$ events shared one
$\theta$. The interval then claims that a *new* event's mean is known to within the sampling spread of the old
events' arithmetic mean, and that interval shrinks without limit as tickets accumulate. So the truncation is
invisible in the number and fatal in the width, which is exactly the combination that survives a review by accident.

**Rule.** Never use a truncated-at-zero $\hat\tau^2$ in a predictive interval. Substitute the declared floor
$\tau^2_0$ (§4.7) and print the sensitivity table across a range of $\tau_0$. State which was used.

**$J = 1$.** The moment estimator is undefined, and it is undefined by construction rather than by numerical
accident: the denominator $\sum w_j-\sum w_j^2/\sum w_j$ equals exactly $w_1-w_1^2/w_1=0$. Checked arithmetically in
this pass **[MEASURED]** (the identity evaluates to `0.0` in floating point, and the implementation returns a
sentinel). There is no between-event variance from one event, and no estimator can manufacture it.

**Rule at $J=1$.** Do not estimate $\tau^2$. The single event gives one draw of $\theta$, which is not information
about a *different* event, so the cold-start estimate reverts to the prior exactly as at $J=0$, with the one
difference that the prior's location can now be *checked* against one observation. What the single event does buy is
$\sigma^2$ (its own across-ticket dispersion) and, if it has more than one tier with sales, a within-event slope on
log face. Those are worth having. They are worth nothing about the level.

### 4.6 When the event's own data takes over

A useful by-product of the algebra, and the number that should drive the UI's state machine. With
$s_j^2=\sigma^2/n_j$, the own-data weight $B_j = \tau^2/(\tau^2+\sigma^2/n_j)$ equals $1/2$ exactly when

$$\boxed{\ n^{*}=\sigma^2/\tau^2\ }$$

sales in the event. So $n^{*}$ is the count at which the event's own mean and the population mean carry equal
weight. Verified numerically in this pass at $\tau/\sigma \in \{0.25, 0.5, 1\}$ giving $n^{*}\in\{16,4,1\}$ with
$B=0.5$ exactly **[MEASURED]**, and it is a one-line derivation rather than a fitted quantity.

Consequences worth acting on:

- The cold-start label must come off at a *stated* count, not at a vibe. "Your own data takes over after about
  $n^{*}$ resales" is a sentence the organiser can act on, and it tells him how much resale activity he needs
  before the engine stops relying on other people's events.
- $n^{*}$ needs $\sigma$ and $\tau$, which are exactly the two things that are unknown at cold start, so it is
  reported as a *range* over the sensitivity grid and never as a number. With $\sigma$ at the borrowed scale of 0.4
  (§4.7) and $\tau$ from the bottom of the grid at 0.1 up to its borrowed upper bound of 0.406, the range is roughly
  1 to 16 sales: one order of magnitude, which is the honest precision of the statement.
- **$n^{*}$ diverges as $\tau\to0$, and that is not a defect, it is the same pathology as §4.5.** If the
  between-event variance really were zero then the population mean would be all the information there is and the
  event's own sales could never add anything, so there would be no count at which the label should come off. The
  declared floor $\tau_0$ is therefore load-bearing twice: it keeps a truncated moment estimate from producing a
  false precision, and it is what makes the handover count finite. Reporting $n^{*}$ without the floor in force
  would let an artefact of small $J$ become a claim about how much evidence the organiser needs.
- If seat coordinates ever arrive, $\sigma$ rises and $n^{*}$ with it (§3.5, item 4).

### 4.7 A population spread that is not invented

At $J=0$ even the prior needs a location and a scale, and inventing them is forbidden. There is one legitimate
route: fit the published markup distribution, cite it, and carry the transfer assumption as a labelled liability.

Leslie and Sorensen, as summarised in `01-a` §2, report three facts about resold tickets in their concert sample
(class A for that market): the arithmetic-mean markup is 41% above face, 26% of resold tickets are below face, and
25% are above +67%. Fit $\log(p/f)\sim\mathcal{N}(m,s^2)$ to the first two and check the third **[COMPUTED]**:

| Reading of "averages 41% above face" | fitted $m$ | fitted $s$ | implied $P(\text{markup}>+67\%)$ | published |
|---|---|---|---|---|
| arithmetic mean | 0.2612 | 0.4060 | 0.268 | 0.25 |
| median | 0.3436 | 0.5341 | 0.376 | 0.25 |

The arithmetic-mean reading reproduces the third published fact and the median reading does not, so the arithmetic
reading is the one to carry. Result: **mean log ratio 0.2612 (geometric-mean markup +29.8%), across-ticket
dispersion 0.406, with implied $P(\text{above face})=0.740$ against the published 0.74.** The fit is a consistency
check, not a calibration: it says the three quoted numbers can come from one lognormal, nothing more.

Carrying it to the platform, with the liabilities stated:

- **Location.** $\mu\approx0.26$ is a *borrowed* prior for resold tickets on eBay/StubHub in 2004 for 56 rock
  concerts. Different platform, different selection into resale, pre-all-in-disclosure fee convention. Class B for
  the mechanism, class D for the transfer.
- **Selection direction is known.** The prior is conditional on resale, and resold tickets are the better seats
  (`01-a` §6), so it is biased *up* for a randomly chosen ticket. The direction is known, which is worth more than
  the size.
- **The scale gives an upper bound for $\tau$, not a value.** Since across-ticket dispersion decomposes as
  $\tau^2+\sigma^2_{\text{within}}$, and $\tau$ cannot exceed the total, $\tau \le 0.406$ **on the assumption that
  our platform's across-ticket dispersion is no wider than theirs**. That assumption is untestable at $J=0$ and must
  be printed as a condition. What the literature gives is the top of $\tau$'s range. It gives no bottom, which is
  why the sensitivity grid runs from near zero upward.

**Sensitivity table, which is what the cold-start band actually is** **[COMPUTED]** class C. A 90% band on
$\theta_{\text{new}}$ is $\bar y \pm 1.6449\sqrt{\tau^2+V(\tau)}$ with $V(\tau)=1/\sum_j(s_j^2+\tau^2)^{-1}$. Since
$V(\tau)>0$ always, that width is **at least** $\pm1.6449\tau$, so every row below is a floor on the width for a
given $\tau$ and never an overstatement:

| declared $\tau$ | 90% band on the event mean, log units | ~~as markup around face~~ **[CORRECTION 2026-11-07T14:00Z, R2-19 — dead label: this column is the percentage move in the point estimate, exp(±1.645τ) − 1, not markup over face. Read it as a multiplier (x0.513 to x1.950 in the last row); as markup over face centred at the fitted 0.261 the last row is −33% to +153%. See CORRECTION 1 at the end of this file.]** |
|---|---|---|
| 0.10 | ±0.164 | −15% to +18% |
| 0.20 | ±0.329 | −28% to +39% |
| 0.30 | ±0.493 | −39% to +64% |
| 0.406 (borrowed upper bound) | ±0.668 | −49% to +95% |

Read the last row as the answer to "how much uncertainty must be attached": even with the most information the
literature can supply, a brand-new event's geometric-mean resale markup is pinned only to roughly **minus half to
double**, and that is the optimistic end. An engine that shows a narrower band than the last row is asserting a
precision the literature does not support.

### 4.8 Code, stdlib only, as verified in this pass

Implements: the moment estimate, the grid posterior over $\tau$, the mixture predictive for a new event, the
mixture quantiles, and the two degenerate branches. Length is deliberate; a model this small does not need a
framework. The chi-square quantiles of §4.4(ii) need `_gser`/`_gcf` (regularized incomplete gamma by series and
continued fraction) and a bisection, omitted here for length and present in the pass's working copy.

```python
import math

def moment_tau2(y, s):
    """DerSimonian-Laird. Returns (tau2, Q, denominator); None for J < 2, where
    the denominator is exactly 0 and tau^2 is not defined at all."""
    J = len(y)
    if J < 2:
        return None, None, None
    w = [1.0 / (si * si) for si in s]
    sw = sum(w)
    ybar = sum(wi * yi for wi, yi in zip(w, y)) / sw
    Q = sum(wi * (yi - ybar) ** 2 for wi, yi in zip(w, y))
    denom = sw - sum(wi * wi for wi in w) / sw          # == 0.0 at J == 1
    return max(0.0, (Q - (J - 1)) / denom), Q, denom

def marginal_loglik(tau2, y, s):
    """log p(y | tau2) with mu integrated out under a flat prior."""
    v = [si * si + tau2 for si in s]
    prec = [1.0 / vi for vi in v]
    sp = sum(prec)
    ybar = sum(pi * yi for pi, yi in zip(prec, y)) / sp
    Q = sum(pi * (yi - ybar) ** 2 for pi, yi in zip(prec, y))
    return -0.5 * sum(math.log(vi) for vi in v) - 0.5 * math.log(sp) - 0.5 * Q

def tau_posterior(y, s, tau_max=1.0, grid=601, prior="halfcauchy", scale=0.25):
    """Grid posterior over tau; returns (taus, weights, mean_mu, var_mu) per grid point."""
    taus = [tau_max * i / (grid - 1) for i in range(grid)]
    lp = []
    for t in taus:
        lp_prior = (-math.log1p((t / scale) ** 2) if prior == "halfcauchy"
                    else -0.5 * (t / scale) ** 2)
        lp.append(marginal_loglik(t * t, y, s) + lp_prior)
    mx = max(lp)
    w = [math.exp(x - mx) for x in lp]
    Z = sum(w)
    w = [x / Z for x in w]                              # sums to 1.0 exactly
    mus, vari = [], []
    for t in taus:
        prec = [1.0 / (si * si + t * t) for si in s]
        sp = sum(prec)
        mus.append(sum(pi * yi for pi, yi in zip(prec, y)) / sp)
        vari.append(1.0 / sp)
    return taus, w, mus, vari

def cold_start_predictive(taus, w, mus, vari):
    """Posterior predictive moments for theta_new = mu + u_new. No own-event data."""
    E = sum(wi * mi for wi, mi in zip(w, mus))
    V = sum(wi * (vi + t * t) for wi, vi, t in zip(w, vari, taus))
    V += sum(wi * (mi - E) ** 2 for wi, mi in zip(w, mus))
    return E, V                                      # E does NOT depend on tau

def mixture_quantile(p, taus, w, mus, vari):
    """Quantile of the mixture sum_g w_g N(mu_g, var_g + tau_g^2), by bisection."""
    def cdf(x):
        return sum(wi * 0.5 * (1.0 + math.erf((x - mi) / (math.sqrt(vi + t * t) * math.sqrt(2.0))))
                   for wi, mi, vi, t in zip(w, mus, vari, taus))
    lo, hi = -20.0, 20.0
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        lo, hi = (mid, hi) if cdf(mid) < p else (lo, mid)
    return 0.5 * (lo + hi)

def shrink_weight(tau2, s2):
    """Weight on the EVENT'S OWN mean: 0 when s2 is inf (a cold-start event),
    1 when tau2 is inf (a population with nothing in common), 1/2 when s2 == tau2."""
    if s2 == float("inf"):
        return 0.0
    if tau2 == float("inf"):
        return 1.0
    return tau2 / (tau2 + s2)
```

Behaviour of the branches, verified in this pass by running the code **[MEASURED]** (arithmetic only, on inputs
chosen to hit the branches, and nothing about tickets follows from it): the grid weights sum to 1.0; the $J=1$
denominator evaluates to exactly `0.0`; a moment estimate from a pair of nearly identical means returns `0.0` after
truncation; `shrink_weight` returns exactly 0 for infinite `s2`, so a cold-start event's estimate is the pooled
mean; it returns 1 when `tau2` is infinite, so a population with nothing in common contributes nothing; and it
equals 0.5 exactly at `n == sigma2/tau2`.

---

## 5. Uncertainty with no calibration set

### 5.1 Three objects that must not be conflated

| Object | Symbol | Variance | What it answers |
|---|---|---|---|
| the event's mean log ratio | $\theta_j$ | $\tau^2+V(\tau)$ | "what will this event trade at on average" |
| one ticket's realised ratio | $y_{ij}$ | $\tau^2+V(\tau)+\sigma^2$ | "what will this ticket fetch" |
| the population mean | $\mu$ | $V(\tau)$ | "what is the average of the population" |

The third is a parameter interval and is not a prediction about anything. The first is what a cold-start headline
number should be. The second is what a single-ticket price should carry, and it is wider by $\sigma^2$ (of order
0.16 in variance terms at $\sigma=0.4$). Confusing the first with the second understates the spread of an individual
ticket by the whole within-event dispersion; confusing the third with the first understates it by $\tau^2$ and
producing that confusion is the specific failure mode of reporting a truncated $\hat\tau^2$ (§4.5).

### 5.2 What can be computed at all

Everything in this list is computable today, at $J=0$, with the standard library:

1. **A prior-predictive interval for $\theta_{\text{new}}$**, from the declared $\tau$: §4.7's table.
2. **A sensitivity table over $\tau$**, which is the honest substitute for the interval nobody can compute.
3. **An upper confidence limit on $\tau^2$** from $Q$ at $J\ge2$, and the span table of §4.4 showing how little that
   limit says.
4. **A t-based interval on the pooled mean** using $t_{J-1}$ rather than the normal quantile, because at $J<10$ the
   difference is material (Hartung & Knapp on the same correction for random-effects means; Partlett & Riley on
   coverage of intervals at small $J$).
5. **The exact arithmetic**: net revenue at any candidate price and any sell-through, the cap ceiling $f(1+c)$, the
   fee if the operator supplies it. These carry no uncertainty because they are definitions.
6. **The sell-through sign result** of §2.4, conditional on `issuedCount` meaning sold.

### 5.3 What it means, stated without overclaiming

The interval is a **prior-predictive** interval: it is the range a new event's mean would fall in if the declared
$\tau$ (or, once estimated, $\hat\tau$) were correct and events were exchangeable. It is not a confidence interval,
because there is no repeated-sampling statement available: the object it covers is a single unseen event, and the
model's assumptions (exchangeability, lognormal shape, cap truncation correctly specified) are doing most of the
work. It is not calibrated, because calibration of any price distribution is blocked by selective labels
(`01-b` §4.6, T6): every scored observation is conditioned on having sold, so there is no sample on which a coverage
claim could be computed.

So the honest descriptions are: "a range from the spread between events", "conditional on these events being
comparable to yours". A frequency statement is only available if the model is true, so if one is printed it carries
its condition: "90% of new events would fall in this band, if these events are like yours".

### 5.4 The exact label

The one thing the UI must display next to a cold-start number, verbatim:

> Not a prediction: this event has no resales yet, so the band is the spread across {n_events} other events and has
> not been checked against what those events sold for.

At $J=0$ there are no other events on the platform, so the sentence must change rather than lie about the source:

> No prediction: nothing has resold on this platform yet, so this band comes from published ticket markets and has
> not been checked against a single sale here.

Both sentences state the three facts a reader needs: there is no evidence for this event, where the range came
from, and that it is untested. Neither is a caveat bolted on for safety; each is the actual epistemic status of the
number, and the number is meaningless without it.

### 5.5 What must never be printed

- A single cold-start number with no band.
- A percentage attached to the band ("90% likely"), or a confidence badge, or a star rating, or a traffic light.
- A percentile of a distribution that has not been measured.
- The word "comparable" next to the number, which asserts a comparability that §2.3 shows is untested.
- The cap-point prediction presented as a value estimate. At a sold-out capped event the engine genuinely can say
  the recorded resale price will sit at $f(1+c)$; that is a statement about the recording rule, not about worth, and
  it must be worded as such.
- A per-ticket precision on a multi-tier event, or a single event-level face value: `PricePoint.avgMarkupBps` warns
  in the contract that re-deriving an event-level markup from an event-level face is badly overstated, and the same
  error at the top of a UI is worse.
- Any number originating in `lib/mock/` (D1, `00-data-situation.md` §2).

---

## 6. What it degrades to

### 6.1 The ladder

| Events with resale | $\tau^2$ | Estimate | Band | Label |
|---|---|---|---|---|
| 0 | declared | borrowed prior location, class D | §4.7 table, widened | the $J=0$ sentence |
| 1 | **not estimable** | the declared prior location, **not** the one event's mean: one draw presented as a population mean is the error this table exists to prevent | declared $\tau$, shown beside the one observation as a check | $J=0$ sentence, plus "1 event so far" |
| 2 to 4 | moment estimate + $\chi^2$ upper limit; floor applied | shrunk toward the pooled mean | upper limit from §4.4(ii), which is wide by a factor of 3 or more | "spread across $N$ events" |
| 5 to 10 | grid posterior, prior scale from the data | pooled mean or $\hat\mu$ | posterior mixture, cross-checked | "spread across $N$ events" |
| above 10 | grid posterior, weakly informative prior | $x'\hat\beta$ if $k$ covariates are justified | posterior mixture | the event-count sentence, plus the first backtest once there is anything to hold out |

The transitions are on event count, not on ticket count, for the reason in §3.2: information scales in $J$.

### 6.2 What survives at every rung, because it is exact

Four statements are true at $J=0$ and are the actually-useful cold-start output:

1. **The cap ceiling.** No recorded resale can exceed $f(1+c)$. If the cold-start band's upper end exceeds the cap,
   the cap binds and the band is one-sided in practice: the observed markup will pile up at the ceiling and the
   engine will never learn the location of the tail.
2. **The censoring consequence of a tight cap, which is a design instruction.** A cap set at the top of the
   defensible band destroys the evidence needed to price the next event, because the markups above the cap are the
   ones that carry the information about value (`01-b` §4.4, `01-a` §3). At launch the cap is a data-collection
   instrument as much as a policy one. This is the one cold-start recommendation that is actionable on day one
   with no data at all, and it is class C with class D on the magnitude.
3. **Fee arithmetic.** Net revenue at a candidate price is exact once the operator supplies the fee model (D4), and
   the resale ask is fee-neutral under an ad-valorem fee (`01-b` §4.5(i)), so the missing field does not invalidate
   the resale band.
4. **The asymmetry of the loss, which applies to the resale ask and not to the face value.** For a holder choosing
   an ask, over-pricing risks zero revenue on a unit worth nothing after the event, while under-pricing takes certain
   revenue at a lower price; that asymmetry argues for asking below the middle of the value band, and it needs no
   value estimate to make the argument. It does **not** transfer to the organiser's face value, for a reason worth
   stating plainly: the band is denominated in the very price being chosen. "Set face to the middle of the markup
   band" is circular, because moving face moves the band with it at the same proportional rate (the same
   scale-freedom that `01-b` §4.5(ii) uses for the cap). The primary price therefore cannot be set from the markup
   band at all. It has to come from the demand side, and before any resale the only demand observation that exists is
   primary sell-through (§2.4). This is the sharpest consequence of face being endogenous and it belongs in the
   deliverable next to T1, not buried here: **the cold-start markup band prices the resale ask, not the ticket.**

### 6.3 What the engine must not claim at $J=0$

- **No sale probability.** D3 and `01-b` §4.3 make it unidentifiable from a transaction ledger in general; at $J=0$
  there is not even a denominator. The literature's roughly 5% resale share (`01-a` §5) is a mature-market figure
  for eBay and StubHub in 2004 and is an *upper* bound for a new platform with no network effect, so it cannot be
  used as a cold-start prediction of anything.
- **No path magnitude.** The *shape* is borrowable (decline, accelerating near the event, with a flat or
  slight-uptick regime when supply runs out), because that is class A in this market. The *magnitude* is not
  estimable at $J=0$ and the sign of the slope is regime-dependent, with the regime set by remaining supply. At
  cold start remaining supply is the one observable that speaks to it, through §2.4's sign result.
- **No optimum.** T5 (`01-b` §4.5) makes the primary optimum a set even with data. At $J=0$ the honest output is a
  consequence table: net revenue and sell-through as functions of the chosen face and the chosen cap. The markup band
  cannot stand in for the optimum, because it is denominated in the price being chosen (§6.2(4)).

---

## 7. The demo path

### 7.1 What the judge sees, and why each screen is defensible

The judge will be shown the case the brief names: a new organiser, one new event, no resales. That is $J=0$ in the
organiser stratum and possibly $J=0$ overall. The demo has to be *correct* in that state, not rescued from it.

**Screen 1, the event is created.** Inputs visible and attributed to the organiser: tiers with face values, cap,
resale toggle, verified-wallet toggle, date, city. The engine has contributed nothing yet and the screen must not
imply otherwise. This is the screen where the honesty is either established or lost.

**Screen 2, the cold-start answer.** Three elements, in this order of visual weight:

1. The band around the organiser's own face value, from the §4.7 table, with the declared $\tau$ and the sentence of
   §5.4 adjacent at the same weight, not in a tooltip.
2. The evidence count, as a number: "0 resales on this event, 0 on this platform". Evidence count is the headline
   metric of a cold-start engine, and making it prominent is what distinguishes an honest engine from a confident
   one.
3. The exact layer: the cap ceiling at each tier, and net revenue at the chosen face under the declared fee. These
   are arithmetic and carry no uncertainty, which is exactly why they can be shown next to an uncertain band without
   contaminating it, provided the visual difference between "exact" and "prior" is unmistakable.

**Screen 3, the cap is moved.** This is the screen that earns the demo. Drag the cap down and watch the band's
upper end become unobservable: the engine says, in words, that above the cap it will stop learning. Drag it up and
the band's upper end survives. Nothing is estimated, everything shown is arithmetic plus a declared prior, and the
lesson is the one from §6.2(2): a policy choice made at launch determines whether this engine can ever price the
second event. It is a demonstration of a research finding rather than of a model, and it cannot be faked by a
generic pricing widget.

**Screen 4, evidence arrives.** After one or more resales, or even after primary sell-through moves, the label
changes and the number moves. The state machine is driven by $n$ against $n^{*}$: "prior" while $n < n^{*}$,
"blended" while $n$ is of order $n^{*}$, "this event's own data" above it, with $n^{*}$ itself shown as a range
because $\sigma$ and $\tau$ are unknown. That the label is allowed to change, and that the engine says why, is the
strongest available answer to "how do I know this thing is not making numbers up".

### 7.2 What the demo must not show

- A confident number on screen 2. There is no version of "we predict +34% for your event" that is defensible at
  $J=0$.
- The borrowed prior presented as the platform's own data. The $J=0$ sentence exists for this.
- A resale probability, a sale-likelihood meter, or a demand score (§6.3).
- Any figure traceable to `lib/mock/`. If the demo needs to show a populated event list, the data must be labelled
  as illustrative on the same screen, and no engine output may be derived from it.
- A narrowing animation that implies the model is learning from something it is not. If a narrowing is shown, the
  cause must be visible: a real resale appearing, or a declared $\tau$ being changed by the operator.

### 7.3 Acceptance criteria for the cold-start path

These are testable without any market data, which is what makes them usable before launch:

1. With zero events and zero resales, every rendered number is either exact arithmetic or accompanied by the §5.4
   sentence.
2. Setting $J=1$ raises no exception and prints no $\tau$-derived interval (§4.5).
3. Setting $\hat\tau^2\le0$ never yields a band narrower than the declared floor (§4.5).
4. The label transitions exactly at the stated $n^{*}$ range, and $n^{*}$ is displayed.
5. No sale probability is rendered in any cold-start state.
6. Removing the cap from an event removes the ceiling line and changes nothing else.
7. The engine runs with the standard library only, on this machine, without `numpy` (**[MEASURED]** absent).

### 7.4 Why this is not a simulation dressed as a result

Nothing in the demo path requires a fabricated dataset. The band comes from a published distribution with the
citation on screen; the cap arithmetic is exact; the label is a statement about the model's own evidence count;
the $n^{*}$ transition is algebra. A judge who asks "where does this number come from" gets an answer that is
either a citation or a definition. That is the strongest position available to a cold-start engine, and it is
available only because the alternative, a fitted model with no data behind it, is worse.

---

## 8. Evidence table

| # | Claim | Tag | Class |
|---|---|---|---|
| E1 | `Event` has 17 fields, `TicketTier` 5, `Organizer` 4; no category, on-sale timestamp or capacity field exists anywhere in the frontend sources | **[MEASURED]** interface parse and regex | — (verified absence) |
| E2 | `numpy` and `scipy` are absent; python3 is 3.12.3 | **[MEASURED]** import attempts | — (confirms D2) |
| E3 | The $J=1$ moment-estimator denominator is exactly zero, so $\tau^2$ is undefined by construction, not by numerical accident | **[MEASURED]** arithmetic run | C |
| E4 | The 95% interval for $\tau^2$ from $Q$ spans 0.12x to 2.79x at $J=5$, 0.001x to 5.02x at $J=2$ | **[COMPUTED]** $\chi^2$ quantiles, incomplete gamma + bisection | C |
| E5 | $B=1/2$ exactly when $n=\sigma^2/\tau^2$; verified at three ratios | **[MEASURED]** arithmetic run | C |
| E6 | A cold-start event's point estimate is the pooled mean and is independent of $\tau$; $\tau$ enters only the interval | **[ASSERTED]** algebra, §4.3 | C |
| E7 | Leslie and Sorensen's three quoted dispersion facts are jointly consistent with log-ratio $\sim\mathcal{N}(0.261,0.406^2)$; the arithmetic-mean reading reproduces the third fact, the median reading does not | **[COMPUTED]** from `01-a` §2 figures | A for inputs, B for transfer |
| E8 | ~~A 90% band on a brand-new event's mean markup runs from about −49% to +95% at the borrowed upper bound for $\tau$, and from −15% to +18% at $\tau=0.10$~~ | **[COMPUTED]** §4.7 table | C **[CORRECTION 2026-11-07T14:00Z, R2-19b — dead as stated: those percentages are moves in the estimate, not markups over face. As markup over face centred at 0.261 the same band is −33% to +153% at the borrowed upper bound and +10% to +53% at $\tau=0.10$. The arithmetic stands; only the object named was wrong. See CORRECTION 1.]** |
| E9 | Face value is endogenous and cannot anchor the value level; the ratio is identified, the level is not | **[ASSERTED]** `01-b` §4.1, Ekeland et al. | C |
| E10 | Primary tickets are priced below secondary clearing value; resale averages 41% above face on the roughly 5% that resell | **[ASSERTED]** `01-a`, Leslie & Sorensen | A |
| E11 | Resold tickets are better seats (seat-quality percentile 0.61 against 0.50), so a prior conditioned on resale is biased up for a random ticket | **[ASSERTED]** `01-a` §6 | A |
| E12 | Resale propensity varies across events by at least a factor of about 3.4 (5% average, 17% at the most active event), which is direct evidence that events are not exchangeable in how they trade | **[ASSERTED]** `01-a` §5 | A for the figures, D for the inference to markup |
| E13 | Sold out at face implies excess demand at face and hence resale at or above face; unsold at face implies the marginal buyer's willingness to pay is at or below face | **[ASSERTED]** mechanism, §2.4 | C, with class A support from Budish & Bhave |
| E14 | At a binding cap the recorded price is the cap, so the engine can predict the recorded markup while knowing nothing about value | **[ASSERTED]** `01-b` §4.4, `01-a` §3 | A for the structural fact, C for the prediction |
| E15 | A tight cap censors the value signal at exactly the highest-value events, so it forecloses learning | **[ASSERTED]** `01-b` §4.4, `01-a` §3 | C, D on magnitude |
| E16 | Nearest-neighbour comparables cannot define their metric from this contract, and their reported spread is post-selection | **[ASSERTED]** §3.3, with E1 | C, and Anenberg class B for the pathology |
| E17 | No calibration or coverage claim is computable for a price distribution on this observation set | **[ASSERTED]** `01-b` §4.6, T6 | C |
| E18 | `issuedCount` may mean minted rather than sold, which would destroy the sell-through inference | **[ASSERTED]** `00-data-situation.md` §4, `01-b` §5 | open question |

---

## 9. What is unvalidated

Everything below is a hypothesis plus the experiment that would test it. None of it is a result.

1. **That events on this platform are exchangeable enough for partial pooling to beat face value.**
   *Test:* once $J\ge5$, leave-one-event-out. Compare the pooled prediction against the arithmetic mean of the
   others and against face value, on squared log error, with the comparison's own uncertainty reported (5 events
   gives a very weak test, and saying so is part of the result).
2. **That the between-event variance is nearer 0.1 than 0.4.** *Test:* the same leave-one-event-out over the first
   ten events, reporting the $\chi^2$-based interval from §4.4(ii) alongside the point estimate, never instead of
   it.
3. **That the log-ratio model has the right shape.** *Test:* the distribution of residuals from the event-mean model;
   a truncated normal on capped events against a plain normal on uncapped ones, compared on the uncapped subset where
   truncation cannot bite.
4. **That the borrowed prior transfers at all.** *Test:* the first three platform events with resale, compared to the
   §4.7 table. If they fall outside it, the borrowed prior is wrong and the $J=0$ band must be rebuilt from platform
   data as it accrues.
5. **That the sell-through sign result holds, which requires knowing what `issuedCount` means.** *Test:* the operator
   answer to §10.1, then a check of resale prices on sold-out against not-sold-out events.
6. **That the cap censors as predicted.** *Test:* the mass point at `markupBps` equal to the cap (`01-b` §5 notes
   this cannot be exercised on the fixtures at all, since no fixture sale lands on a cap).
7. **That $n^{*}$ is anywhere near the 1 to 16 sales range implied by $\sigma\approx0.4$ and $\tau\in[0.1,0.4]$.**
   *Test:* $\sigma$ from the first event's own across-ticket dispersion, $\tau$ from the first five events.
8. **That the asymmetric-loss direction (§6.2(4)) is right for this platform.** *Test:* requires the operator's
   actual cost of an unsold ticket, which is not in the contract and must not be guessed.

---

## 10. Open questions for the operator

1. **Does `issuedCount` mean sold, or minted?** Load-bearing: it is the only pre-resale demand signal (§2.4), and the
   whole sell-through mechanism depends on the answer. `00-data-situation.md` §4 already flags it.
2. **Will the contract carry an event category before launch?** It is the best single cold-start covariate (§2.2)
   and its absence is the strongest argument against the comparables strategy. One enum field changes the pooling
   stratum from "all events" to "events of the same kind".
3. **Will event status transitions be timestamped?** Without it there is no on-sale time, so no sell-through
   velocity, so the demand bracket stays a level and never becomes a curve.
4. **What is the fee stack, and is face the all-in price?** D4 requires this for the primary optimum; the resale
   band is fee-neutral, so the cold-start band survives without it (§6.2(3)).
5. **For the demo, does the operator want the honest band or a narrower illustrative band labelled as
   illustrative?** The first is defensible and unimpressive; the second is impressive and, if the label slips, is
   the one thing that would damage the submission. My recommendation is the first, with the second available only as
   a clearly marked simulation exercise that no engine output is derived from.

**Registry rows this finding implies** (not edited here, per the pass's file boundary): `A` one row for the
cold-start question with this file as the finding; `B` the hierarchical model, the update rule, the $\chi^2$ span
table and the $n^{*}$ derivation; `C` `sell_through_level` (available, contract), `tier_count` (available),
`price_ladder_ratio` (derived, available), `event_category` (absent), `on_sale_age` (absent),
`venue_capacity` (absent), `organiser_event_count` (derived, available); `D` model row for empirical-Bayes partial
pooling with validation status UNVALIDATED and role "cold-start default"; `F` a decision row recording the
recommendation and its reversal conditions.

---

## Sources

Metadata for every item below was checked against Crossref during this pass; the DOI, title, container and year
were read from the API response, not from memory. Where a figure is quoted, it is quoted from `01-a`'s record of the
paper, and the class is `01-a`'s.

**Hierarchical modelling, shrinkage, and small-group variance**

- Efron, B. & Morris, C. (1973). Stein's estimation rule and its competitors, an empirical Bayes approach. *JASA*
  68(341), 117-130. https://doi.org/10.1080/01621459.1973.10481350
- Efron, B. & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations. *JASA* 70(350),
  311-319. https://doi.org/10.1080/01621459.1975.10479864 — the requirement that the between-group variance needs at
  least two groups, cited in `01-b` §4.6.
- Morris, C. N. (1983). Parametric empirical Bayes inference: theory and applications. *JASA* 78(381), 47-55.
  https://doi.org/10.1080/01621459.1983.10477920
- Gelman, A. (2006). Prior distributions for variance parameters in hierarchical models. *Bayesian Analysis* 1(3),
  515-533. https://doi.org/10.1214/06-BA117A — the basis for the half-Cauchy or folded-t prior on $\tau$ when the
  number of groups is small.
- Rossi, P. E., McCulloch, R. E. & Allenby, G. M. (1996). The value of purchase history data in target marketing.
  *Marketing Science* 15(4), 321-340. https://doi.org/10.1287/mksc.15.4.321 — the same partial-pooling logic for the
  case where a customer has no history, in a commercial setting.

**Estimating and bounding a between-group variance from few groups**

- DerSimonian, R. & Laird, N. (1986). Meta-analysis in clinical trials. *Controlled Clinical Trials* 7(3), 177-188.
  https://doi.org/10.1016/0197-2456(86)90046-2 — the moment estimator of §4.4(i).
- Viechtbauer, W. (2007). Confidence intervals for the amount of heterogeneity in meta-analysis. *Statistics in
  Medicine* 26(1), 37-52. https://doi.org/10.1002/sim.2514 — the $\chi^2$-based interval of §4.4(ii), and the source
  of the reasoning behind the span table.
- Higgins, J. P. T. & Thompson, S. G. (2002). Quantifying heterogeneity in a meta-analysis. *Statistics in Medicine*
  21(11), 1539-1558. https://doi.org/10.1002/sim.1186 — the $I^2$ convention used in §3.5.
- Sidik, K. & Jonkman, J. N. (2005). Simple heterogeneity variance estimation for meta-analysis. *JRSS Series C*
  54(2), 367-384. https://doi.org/10.1111/j.1467-9876.2005.00489.x — the bias of the moment estimator when the
  within-study variances are themselves estimated.
- Hartung, J. & Knapp, G. (2001). A refined method for the meta-analysis of controlled clinical trials with binary
  outcome. *Statistics in Medicine* 20(24), 3875-3889. https://doi.org/10.1002/sim.1009 — the small-$J$ correction to
  the interval on the pooled mean, §5.2(4).
- Partlett, C. & Riley, R. D. (2017). Random effects meta-analysis: coverage performance of 95% confidence and
  prediction intervals following REML estimation. *Statistics in Medicine* 36(2), 301-317 (online 2016).
  https://doi.org/10.1002/sim.7140 — measured coverage failure of intervals at small $J$, and the reason no coverage
  figure is quoted here.
- Higgins, J. P. T., Thompson, S. G. & Spiegelhalter, D. J. (2009). A re-evaluation of random-effects meta-analysis.
  *JRSS Series A* 172(1), 137-159. https://doi.org/10.1111/j.1467-985X.2008.00552.x — the distinction between a
  confidence interval for the pooled mean and a prediction interval for a new study, which is exactly the
  cold-start object of §5.1.

**Forecasting, uncertainty, and what an interval must be called**

- Gneiting, T. & Katzfuss, M. (2014). Probabilistic forecasting. *Annual Review of Statistics and Its Application*
  1, 125-151. https://doi.org/10.1146/annurev-statistics-062713-085831 — the requirement that a predictive
  distribution be named for what it is and validated before a coverage claim is made.
- den Boer, A. V. (2015). Dynamic pricing and learning: historical origins, current research, and new directions.
  *Surveys in Operations Research and Management Science* 20(1), 1-18. https://doi.org/10.1016/j.sorms.2015.03.001 —
  the general result that a posted price plus censored sales data identifies demand only with price variation,
  which is why the cold-start engine must not claim a demand curve.

**Comparables, matching, and the failure of the nearest-neighbour rule**

- Abadie, A. & Imbens, G. W. (2006). Large sample properties of matching estimators for average treatment effects.
  *Econometrica* 74(1), 235-267. https://doi.org/10.1111/j.1468-0262.2006.00655.x — the bias and consistency
  conditions a matching rule needs, which §3.3 checks and cannot satisfy.
- Anenberg, E. (2016). Information frictions and housing market dynamics. *International Economic Review* 57(4),
  1449-1479. https://doi.org/10.1111/iere.12204 — the comparable-sales pathology: valuation anchored on neighbours
  propagates the population's past rather than measuring the subject.
- Schein, A. I., Popescul, A., Ungar, L. H. & Pennock, D. M. (2002). Methods and metrics for cold-start
  recommendations. *SIGIR '02*. https://doi.org/10.1145/564376.564421 — the standard taxonomy of cold-start cases
  (new user, new item, new community) and why each is a different identification problem; this finding's $J=0$,
  $J=1$ and new-organiser cases map onto it.

**Ticket-market evidence, carried from `01-a` and not re-read here**

- Sweeting, A. (2012). *JPE* 120(6), 1133-1172. https://doi.org/10.1086/669254
- Leslie, P. & Sorensen, A. (2014). *RES* 81(1), 266-300. https://doi.org/10.1093/restud/rdt033
- Budish, E. & Bhave, A. (2023). *AEJ: Micro* 15(1), 142-170. https://doi.org/10.1257/mic.20180230
- Courty, P. & Pagliero, M. (2012). *REStat* 94(1), 359-369. https://doi.org/10.1162/rest_a_00179
- Ekeland, I., Heckman, J. J. & Nesheim, L. (2004). *JPE* 112(6), 1278-1320. https://doi.org/10.1086/379947
- Gallego, G. & van Ryzin, G. (1994). *Management Science* 40(8), 999-1020. https://doi.org/10.1287/mnsc.40.8.999
- 16 CFR Part 464, 90 FR 2166 (all-in ticket pricing display, effective 2025-05-12), as recorded in `01-a` §1.

---

## CORRECTION 1 (2026-11-07T11:28Z) — the band is a multiplier on the estimate, not a markup range around face

Appended by the corrections pass after `records/findings/00-verification-round1.md` §11. Nothing above is
deleted.

**Withdrawn labelling, §4.7 table and E8:**

> "| 0.406 (borrowed upper bound) | ±0.668 | −49% to +95% |"
>
> "E8 | A 90% band on a brand-new event's mean markup runs from about −49% to +95% at the borrowed upper bound
> for τ, and from −15% to +18% at τ=0.10"

The column header that produces this, "as markup around face", is part of what is withdrawn. **What the
column actually computes** is exp(±1.645τ), applied to the point estimate: exp(−0.668) = 0.513 and
exp(+0.668) = 1.950, so the last row reads **×0.51 to ×1.95 of the estimate**, which is −49% / +95% *relative
to the estimate* and not relative to face.

**Corrected label.** "as a multiplier on the point estimate". The log-unit column above it is correctly
labelled.

**The same band centred where the model puts it.** The file's own fitted centre is μ = 0.261 (§4.7, the fit
at lines 519–535; and E6:
the cold-start point estimate is the pooled mean and does not depend on τ). An absolute band on markup over
face is therefore exp(0.261 ± 1.6449τ):

| declared τ | 90% band in log units | as a multiplier on the estimate | as markup over face, centred at μ = 0.261 |
|---|---|---|---|
| 0.10 | ±0.164 | ×0.849 to ×1.178 | 1.102 to 1.530, i.e. +10% to +53% |
| 0.20 | ±0.329 | ×0.720 to ×1.390 | 0.934 to 1.804, i.e. −7% to +80% |
| 0.30 | ±0.493 | ×0.611 to ×1.637 | 0.793 to 2.125, i.e. −21% to +113% |
| 0.406 | ±0.668 | ×0.513 to ×1.950 | 0.666 to 2.532, i.e. −33% to +153% |

Arithmetic shown, since these are new numbers: exp(0.261 − 0.164) = 1.102, exp(0.261 + 0.164) = 1.530, and so
on for each row. The verification pass prints "−33% to +155%" for the last row; that upper end comes from
rounding 0.261 + 0.668 to 0.935, and to three decimals the exponent is 0.929, so 2.532 and +153% is the
figure that follows from this file's own inputs.

**Why it matters.** As printed, "−49% to +95%" reads as "the markup on a new event can be 49% below face".
That contradicts the file's own class-A inputs (26% of resold tickets below face, mean +41%), and it puts the
sign of the downside in the wrong place. A reader who takes the label literally gets the direction of the
cold-start risk backwards.

**What stands.** Every number in the table is arithmetically correct as a multiplier; the prior fit, the χ²
spans, the statement that the width is a floor because V(τ) > 0, and the prose "pinned only to roughly minus
half to double" (which is the multiplier reading and is right). What is withdrawn is the "around face" label
and E8's phrasing. E8 should read: "a 90% band on a brand-new event's mean markup is a factor of about 0.51 to
1.95 on the point estimate at the borrowed upper bound for τ, and 0.85 to 1.18 at τ=0.10; as markup over face
centred at μ = 0.261 that is −33% to +153%, and +10% to +53% at τ=0.10".

---

## CORRECTION 2 (2026-11-07T11:28Z) — the Ekeland, Heckman & Nesheim reference is the wrong issue and pages

**Withdrawn entry:**

> "- Ekeland, I., Heckman, J. J. & Nesheim, L. (2004). *JPE* 112(6), 1278-1320. https://doi.org/10.1086/379947"

**What is true.** A Crossref query for that DOI on 2026-11-07 returns *Journal of Political Economy* **112(S1),
S60–S109**, "Identification and Estimation of Hedonic Models". `01-b`'s reference list has it right. The paper
the argument uses is the same one, and its proposition (preferences and technology identified from a single
market only up to affine transformations, §3.2) is unaffected.

**Corrected reading.** Cite it as *JPE* 112(S1), S60–S109. Nothing else in this file changes.

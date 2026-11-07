# DELIVERABLE: the integrated research and engineering specification

**Programme:** `RESEARCH-PROGRAM.md` Phase 8, the 22 required sections.
**Assembled:** 2026-11-07T12:40Z, by an integrator pass, from the records that already existed.
**Status of this document:** it is the Phase 8 document, not a table of contents for one. It is also not
a report of results about ticket markets, because none exist: there is no real ledger
(`records/00-data-situation.md` §1 and §2). Everything below is either a citation of published
research, an identification argument, a specification, or a measured statement about the code in this
repository.

**What this document had to work with.** Six records (`A` to `F`), eighteen findings under
`records/findings/`, a contract conformance record, a build report, a console, and one independent
engine review. Where a record disagrees with another, both statements are here and the section says
which one the engine follows. Nothing was upgraded: a quantity the record calls bounded is called
bounded here, and a model the record calls `UNVALIDATED` is called `UNVALIDATED` in the same sentence
that names it.

**Evidence vocabulary**, from `records/README.md`, used unchanged throughout:

| Class | Meaning |
|---|---|
| **A** | Directly supported by ticket-market empirical evidence |
| **B** | Supported by empirical research in a related market |
| **C** | Supported by mathematical theory or established statistical methodology |
| **D** | Plausible but untested hypothesis |
| **E** | Speculative research opportunity |
| **SIM** | Established by simulation under stated generative assumptions. Says nothing about ticket markets |
| **UNVALIDATED** | Validation requires data this programme does not have. Stated as a hypothesis plus the test |

Two markers from the findings are also carried: **MEASURED** (a number read from a named source or
computed from one) and **ASSERTED** (reasoning or a specification choice). **OBSERVED** appears only in
`A-research-ledger.md`, where it marks a statement true of this repository by direct inspection; it is
not an evidence class and is not used here as one.

**Pinned state of the code.** Section 17 and 18 describe `ticketpath/` as it exists on disk. Two facts
matter for a reader: the tree was being edited while this document was assembled, and the numbers
recorded for it are time-stamped for that reason. Where the running code and the independent review
disagree, both are here.

---

## 1. Executive summary

**1.1 The engine can price a resale ask as a bounded quantity, and it cannot identify a sale
probability at a price. That is the programme's result.** Of six target quantities, one is buildable
today, two are set-identified with computable bounds, and three are not identified at all
(`01-b` §1, §3). The binding constraint is a missing observation, not a missing model: the asking price
of the ticket that did not sell is nowhere in the ledger (`01-b` T3; `02-c` §1.1). **Class C.**

**1.2 Primary tickets are priced below secondary clearing value, and the prize is small.** Resale
averages 41% above face on the roughly 5% of tickets that resell, worth 1.4% of primary revenue in the
one study that observes both sides, and that figure covers only the half of resale the authors observe
(Leslie & Sorensen 2014, **class A** as computed; `01-a` CORRECTION 1). Repricing the top 10% of seats
is worth 3.4% of primary revenue in the same authors' model counterfactual (**class A**, a simulation
not an adoption). Multi-tier pricing is worth about 5% on 21,120 concerts (Courty & Pagliero 2012,
**class A**). The three are consistent: single-digit percentages, concentrated in the best seats.

**1.3 Secondary prices near the event overwhelmingly fall, and the sign of the last week is not
settled.** Sweeting (2012) finds within-seller declines of 13%, 18% and 40% of face across relistings
and "40 percent or more" over the final month, on asking prices of listings that failed to sell and
were relisted (**class A**). Leslie & Sorensen find a near-flat path with "a modest uptick in the last
week", in a footnote, with no magnitude (**class A**). Lee et al. (2023) find no effect two days out and
a sharp drop on game day in MLB (**class A**, abstract). Two peer-reviewed studies, two markets,
opposite signs in the final 48 hours. The engine may fit a sign to our own data; it may not promise
one (`02-a` §3.5, §10.7).

**1.4 A resale price ceiling truncates the record and the bias is worst where value is highest.**
`resalePriceCapBps` is a hard ceiling on resale price in basis points over each tier's own face
(`lib/types.ts`). The observed markup is therefore `min(latent, cap)` plus a mass point at the cap, and
the bias in the naive mean is `s·E[latent − cap | latent ≥ cap]` where `s` is the share of sales at the
ceiling (**class C**, an identity, `02-b` §1.2). High `s` is the observable signature of excess demand,
so fitting a mean on capped markups reports the hottest events as the least valuable. The engine
reports a floor and a rationing statistic on such events and refuses a mean or an upper quantile
(`02-b` §3.2).

**1.5 The most valuable missing observation is the four-field listing panel.** `{listPriceLamports,
listedAt, delistedAt, delistReason}` turns `P(sale | price, exposure, t)` from unidentifiable into a
standard time-varying-covariate survival problem (`01-b` §6(3); `02-c` §10). `delistReason` with a
`cap_blocked` value is the single highest-information element, because it separates "nobody wanted it"
from "everybody wanted it and the ceiling rationed them" (`02-c` §4.5). This is the one data request
the programme makes (`F` D3). **Class C for the identification argument, UNVALIDATED for everything it
would produce.**

**1.6 The primary optimum is a boundary recommendation plus a set, not a point.** The whole fee stack
collapses to one effective per-ticket wedge `c** = b + (1+β)(f − a − u)/(1−φ)` (**class C**, exact
algebra), ad valorem fees are neutral for the optimum and per-unit fees are not, and a cap defined in
basis points over face does not constrain the organiser at all (`02-d` §2.3, §2.5). It does decide how the
resale price divides — the organiser's price plus the reseller's margin, in the ratio `1 : c` — so the
premium is not capturable through the primary price, and the objective carries no capture rate (§12.3;
`11-cap-capture-check.md` §9; `F` D7). With demand inelastic at observed prices and `c**` small, the interior
Lerner price falls below the price at which
the house fills, so the binding optimum is the sell-through boundary. **The engine follows the boundary
rule and prints "a bound, not an optimum"** (`02-d` §6).

**1.7 The cold-start answer is a band, and its width is the deliverable.** At cold start the
partial-pooling point estimate *is* the population mean; the between-event variance moves only the
interval (`02-e` §4.3, §1.1). At `J = 5` events the 95% interval on that variance spans a factor of 23;
at `J = 2` a factor of 5100 (**class C**, computed from chi-square quantiles). With the literature's
dispersion borrowed as an upper bound, a new event's mean markup is pinned to about ×0.51 to ×1.95 of
the point estimate, which centred at the fitted mean is −33% to +153% in markup over face (`02-e` §4.7
and CORRECTION 1). **Class B for the borrowed prior, D for the transfer, UNVALIDATED on this platform.**

**1.8 Nothing in this programme is validated, and no accuracy number may be quoted.** No result can be
class A from our own data; simulation is admissible for estimator properties only, and no simulation
study has been run (`00-data-situation.md` §5; `D-model-registry.md` basis paragraph; `06-validation-protocol.md`
§3.3). The one thing testable today is internal correctness, and the engine is honest about which of
its outputs is arithmetic and which is a declared prior (`06` §1.4).

**1.9 The engine exists, refuses correctly, and fails its own honesty audit as of the review.** A
standard-library Python server renders one console page that states, for each number, what kind of
number it is (`ticketpath/`, §17). An independent review passed the arithmetic, passed the refusals
with a narrowing, and **failed both honesty and code**: four label sentences state things the engine
does not compute, one rate is a prior badged as a fixture, and three store-valid inputs take the page
out with no HTTP response at all (`07-engine-review.md` §0). Those are findings about code, not about
markets, and they are in §17 rather than buried.

**1.10 The single most important limitation.** Every number the engine can produce is conditional on
the primary price that was actually charged, on a record that is truncated by policy at exactly the
events that matter, from a platform that has no data yet. A reader must not conclude that this
programme has measured what a ticket is worth, nor that any estimator here has been shown to work.
What it has produced is a precise account of what can and cannot be learned from this observation set,
the mathematics of the parts that can, and an engine that refuses the parts that cannot.

---

## 2. Problem formulation

### 2.1 The four required outputs, and what each became

`RESEARCH-PROGRAM.md` §0 asks for an engine that returns four things. The programme's identification
work turns each into a statement of a specific type, and the type is the finding.

| Required output | What is identified | Status | Section |
|---|---|---|---|
| What a ticket is realistically worth on resale | a quality-adjusted **relative** price `log(price/face)`, with a one-sided floor where the cap binds | identified as a ratio, not a level; the level needs an exogenous anchor the schema does not carry | 9 |
| How that value moves over the remaining horizon | **curvature** and event deviations; the linear trend is a normalisation | set-identified; reported as a bracket over a declared normalisation | 9, 7.4 |
| The probability it transacts at a given price | nothing at a *price*; the **composite transaction rate** per ticket-day at risk, and the realised price-time distribution | the price response is not identified; the rate and the distribution are | 10 |
| The primary price maximising risk-adjusted expected value | the objective's **structure**, and a **boundary** recommendation plus a **set** over the unidentified parameters | a set, not a point | 12, 13 |

### 2.2 Formal setting

One event `e` with tiers `g = 1..K`. Tier `g` offers `N_g` units (`totalSupply`) at a per-unit price
`p_g` (`faceValueLamports`), total `Q = Σ N_g`. The organiser chooses `p = (p_1..p_K)` once, before
on-sale, and cannot change it: the contract has nine endpoints, seven reads and two wallet-verification
POSTs, and no price-mutation endpoint (`02-d` §1.1, MEASURED). The cap `c` is basis points over face, so
the legal resale ceiling in money is `p_g(1+c)`.

Tickets are wallet-bound tokens. For ticket `i` we observe an ordered set of ledger events
`(t_ik, mark_ik)` where the mark is one of `sale at price p`, `transfer at no price`, `redeem`,
`revoke`, plus a terminal observation `T_i = min(redeem_i, event end)`. The price is a mark on a point
process, and the observation set is a **case-only sample**: the price exists only where the sale
happened (`01-b` §2).

Three instants govern every feature, and they are not interchangeable (`03-b` §2):

| Instant | What it is | What is knowable |
|---|---|---|
| **D1** | the organiser commits the tier face, before the first `issue` row exists, once and irreversibly | the event's fixed facts and its own policy choices, external variables published before the on-sale, and fitted parameters from *completed earlier* events. Not any ledger fact about this event |
| **D2** | any `t` inside the trading window | D1 information plus this event's own record truncated at `t` |
| **D3** | extraction, the instant the payload was computed, which the contract never states | everything, including values that postdate the decision |

The audit's organising sentence: **leakage is D3 information entering a D1 or D2 decision, and nothing
else in the audit is a separate failure mode** (`03-b` §2.4). Of 61 candidate features, 25 are usable at
D1, 43 at D2, and 18 are dropped: 6 absent from the observation set, 11 carrying post-decision
information, 1 unidentified (`03-b` §3.5).

### 2.3 The two structural facts that decide the architecture

**(a) Face value is endogenous and is the decision variable.** The value model is denominated in face,
so it is invariant to face: raise the primary price by `λ` and, under a proportional cap, the ceiling
rises by `λ` in the same proportion. **The resale record therefore cannot set the primary price**, and
the primary price must come from a demand object, of which the schema carries exactly one, censored and
one-sided (`B-mathematical-kb.md` §9.4; `02-e` §1.10).

**(b) The record is complete only conditional on enforcement.** A wallet-bound token can be sold by
handing over the key, and then no row exists at all. Off-platform settlement, bundling and side payment
do the same to the recorded consideration. The chain bounds the *record*, not the money
(`01-a` §6; `F` D6).

### 2.4 What the deliverable is, stated against §4.6 of the programme

The programme forbids fabricating datasets, accuracy improvements, experiments, significance and source
capabilities, and requires that where evidence does not exist the document says so and names the
experiment that would produce it. That is why several sections below are a specification and a refusal
rather than a result, and why the most valuable sections are 20 and 21.

---

## 3. Market mechanics

### 3.1 Mechanism map

Primary and secondary are one market with two price-setting institutions: the primary seller has
monopoly-like power over *allocation* and prices coarsely ("the maximum number of price levels for a
single event in our data is four, with most events offering tickets at only two", Leslie & Sorensen
2014, **class A**), while the secondary market prices finely with heterogeneous, often uninformed
sellers (`01-a` §1).

| Channel | Who sets price | Inventory risk | Where fees sit | Observable in our contract |
|---|---|---|---|---|
| Primary fixed price | organiser, per level, coarsely | organiser, unsold = 0 at doors | per-ticket + facility + order, per-unit and ad valorem | `faceValueLamports`, `tierId`, `totalSupply`/`issuedCount` snapshot |
| Primary dynamic or "platinum" | algorithm or pricing desk | organiser | same stack on a moving price | not identifiable; arrives as `faceValueLamports` |
| Presale, ballot, queue | organiser sets price, queue allocates | organiser | registration free, queue is non-price rationing | `requiresVerifiedWallet`, `issuedToWallet` |
| Season and broker allocation | club or venue contract | broker | wholesale discount, embedded | not visible |
| Resale marketplace, seller asks | individual seller | seller | two-sided | `sale` rows, `markupBps` |
| Capped resale (NSW, Ireland, UK announced, and this platform) | policy sets the ceiling | seller, platform carries enforcement risk | platform fee capped so it cannot breach the cap | ledger row at or below the cap; the shadow price is unrecorded |
| On-chain primary and resale | organiser primary, reseller secondary | split | royalty inside the token transfer | by construction: issue, sale, transfer, redeem with price and counterparties |

**Two fee facts are absent from the contract and both matter.** Resale fees are two-sided, so "the
price" is ambiguous by 20 to 40% depending on the observed side (`01-a` §1). And since 2025-05-12 US
law requires the total price to be displayed for live-event tickets (16 CFR Part 464, 90 FR 2166,
**class A** for the regulation), which is a structural break in any US series: pre-rule quotes are
pre-fee and post-rule quotes are all-in, and pooling them manufactures a one-off level shift that reads
as a market move (`02-e` §2.3).

### 3.2 The price path

| Study | Sample | Finding as stated | Class |
|---|---|---|---|
| Sweeting, *JPE* 120(6):1133-1172, 2012 | MLB 2007; 178,659 eBay fixed-price listings; 113,186 in the structural sample; 66,236,993 StubHub daily listing observations | prices fall as the game approaches, sellers cut by 13%, 18% and 40% of face across successive relistings, "40 percent or more" over the final month; dynamic pricing worth about 16% of seller payoff | A |
| Sweeting, same | same | demand approximately time-invariant and the hypothesis that it does not change with days-to-go cannot be rejected; every percentile of implied opportunity cost falls monotonically; about 25% of final-period opportunity costs are significantly negative | A |
| Leslie & Sorensen, *RES* 81(1):266-300, 2014 | 56 rock concerts, 2004; 1,034,353 primary tickets; 51,318 resales | prices conditional on seat quality "decline slightly ... with a modest uptick in the last week"; 50% of resales within 26 days, 25% within 7 | A |
| Lee, Morse, Hyun, Shapiro & Drayer, *Sport, Business and Management* 13(3):397-415, 2023 | MLB, StubHub posted prices, 19,155 observations | no significant time effect two days out; a relatively dramatic drop on game day | A (abstract) |
| Shapiro & Drayer, *J. Sport Mgmt* 26(6):532, 2012 | SF Giants 2010, 12 games, 1,316 observations | fixed primary < dynamic primary < secondary, all significantly different | A (small) |
| Budish & Bhave, *AEJ:Micro* 15(1):142-170, 2023 | Ticketmaster primary auctions matched to eBay resale values | auctions "substantially improved price discovery, roughly doubled performer revenues, and, on average, nearly eliminated the arbitrage profits" | A |
| Courty & Pagliero, *REStat* 94(1):359-369, 2012 | 21,120 concerts, 2007 | multiple price levels raise revenue about 5%; 56% of concerts offer two levels, 25% one | A |
| Courty, *JEP* 17(2), 2003 | theory and evidence review | promoters cannot capture resale profits because demand is uncertain and waiting has option value | C |

Two readings of Sweeting's published dummy coefficients are worth carrying because they are arithmetic
on his own table rather than a new estimate (**class C**, `02-a` §3.3): a constant proportional decline
in logs reaches R² 0.55 to 0.69, while a deadline-convex form, log price linear in log(days+1), reaches
R² 0.90 to 0.97 with a single exponent of 0.133 to 0.164 stable across high-demand, low-demand, cheap
and expensive seats. The implied fall over his 81-day window is 36% to 43%, and it is proportional, not
additive.

The mechanism is two forces in opposite directions. The seller's option value of holding decays as
selling opportunities disappear (**class A**, Sweeting). Buyer arrivals rise: 25% of resales in the
final 7 days against 25% in the 19 days before, which is a per-day arrival rate 2.7 times higher in the
final week (**class A** as arithmetic on Leslie & Sorensen's reported shares, `02-a` §5.3). The measured
net is a fall, so the seller side dominates in those samples; that is the outcome of a race the
literature shows can go either way. **What separates the regimes is remaining supply, not calendar
time**, which is why the time-to-event slope must be conditioned on a supply state (`01-a` §2; `03-a` §1
row I2).

### 3.3 Caps: whether they bind, and what a binding cap does

Regulatory direction is uniform. NSW has capped resale at original retail plus transaction costs, "up to
a maximum 10% of the original ticket price", since 2018-06-01, with penalties and a stated inability to
order refunds of the excess (**class A**). Ireland banned above-face resale for designated events and
venues from 2021-07-31. The UK announced on 2025-11-19 that resale above "original cost plus unavoidable
fees" will be illegal, with platform fee caps and penalties up to 10% of global turnover under the DMCC
Act 2024. In the US the BOTS Act governs primary access, not price; on 2026-04-15 an SDNY jury found
Live Nation and Ticketmaster liable on all antitrust counts, remedies pending (secondary source, docket
not read).

A binding cap does three observationally distinct things (`01-a` §3):

1. **Upper truncation of the markup distribution.** No transaction above the cap is recorded, so any
   mean or upper quantile from the record is biased down by construction (**class C**).
2. **A mass point at the cap with rationing behind it.** The market clears by speed and allocation, not
   price. The spike's height, and sale velocity at the cap, measure excess demand rather than value.
   He & Lin (*Marketing Science* 45(3):515-533, 2026) add that a stringent cap can push high-price
   sellers out, reduce seller-side competition, and raise the average transaction price (**class C**, a
   model result).
3. **Evasion that moves price off the rail.** Side payment, wallet handoff, bundling, flight to
   unregulated channels. The UK's own cost-benefit model assumes 20% displacement of tout volume, which
   is an official assumption rather than a measurement (**class A** as an assumption). The consequence
   is that at the cap the recorded markup is a *lower bound*, with the bias largest where demand is
   strongest.

**Terminology correction carried from `02-b` §1.4.** `01-a` and the Phase 0 audit call the first effect
"left truncation". The tail removed is the *upper* tail of the markup distribution. `02-b` reads "left"
as shorthand for the lower end of the price axis relative to what the market would bear and records the
ambiguity rather than editing either file. This document says "truncated from above" and, following
`02-b` §1.3, distinguishes **truncation** (units removed, no indicator survives) from **censoring**
(unit kept, value coarsened, indicator observed).

**Which regime is which** is decided observably, on the pair (cap present, at-ceiling count), not on
`cap != null` (`02-b` §3.1):

| Regime | Condition | What the engine may say |
|---|---|---|
| capped and binding | `c` non-null and at least one settled row at the ceiling | a floor, the rationing share, no upper end |
| capped, no mass point | `c` non-null and no row at the ceiling | the ceiling's status is unknown; do not treat the record as uncensored |
| uncapped | `c` null | the only regime in which the top of the transaction distribution is sampled at all |

### 3.4 Liquidity and churn

- **Share that resells: about 5%.** "Only 5% of purchased tickets [were] resold on eBay or StubHub",
  with the most active event at 17% and resale revenue equal to 37% of that event's primary revenue
  (**class A**). The UK model starts from 1.9m resold against 37.1m primary, about 5.1%. Two independent
  measurements, same number. Any model that assumes a liquid secondary market for the median event is
  wrong by an order of magnitude.
- **Concentration: extreme.** "The top 10% of resellers account[ed] for more than 70% of platform ticket
  resale volumes" (CMA, via DBT, **class A** via regulator); 46% of resale transactions in the concert
  data were by fans, not brokers (**class A**).
- **Holding duration and transfers per ticket: not established.** No peer-reviewed or
  regulator-published distribution exists (`01-a` §5). Sweeting gives an indirect fact (median eBay
  purchase ten days before the game). This is exactly what an on-chain ledger measures better than any
  dataset in the literature, and it is computable from consecutive `slot` values on one mint
  (`02-c` §3.1(iii)).
- **On-chain sources.** Get Protocol publishes a subgraph and an explorer and claims "millions of
  on-chain smart tickets since 2016", which is a vendor claim; whether a fiat resale price is written on
  chain is **not established** (`01-d` §6; `E-data-source-registry.md` S7, class E).

### 3.5 What this market has that the literature does not, and what it has lost

**Lost.** The asking-versus-realised gap does not shrink, it vanishes: there is no ask anywhere in the
record, so listing revision, duplicate listings, seller competition and price discovery through asking
are entirely unavailable, not partially available (`01-b` §5.2). Cross-platform fragmentation and
seller-identity inference also vanish (a wallet is the identity).

**Relocated.** Censoring moves from prices to *exposure*: `P(sale | price, exposure, t)` is not
identified from a completed-transaction ledger (`01-b` T3; `02-c` §1.1).

**New, all class D with a stated test** (`01-a` §6): the cap as a sharp policy truncation with rationing
behind it, known and exact, which is statistically a gift and commercially a trap; key handoff as an
invisible transfer, so the ledger is complete only conditional on enforcement; and the recording
incentives the cap creates, which make the recorded markup a strategic variable rather than a market
outcome.

---

## 4. Literature review

This is a review of what exists and what it settles, not of everything written. Sources are listed with
the locator the finding used; the full bibliography is §22. Four bodies of work matter, and one absence
dominates.

### 4.1 Ticket-market empirical work

Seven studies carry the class A core. Sweeting (2012) is the anchor for the price path and for the
mechanism (declining opportunity cost with time-invariant demand). Leslie & Sorensen (2014) is the
anchor for the level, the resale share, the selection into resale (mean seat-quality percentile 0.61
against 0.50) and the 1.4% sizing. Budish & Bhave (2023) is the only class A evidence that changing the
primary *mechanism* can dominate any pricing engine, and their closing explanation of why the auctions
nonetheless failed to take off is the commercially important half. Courty & Pagliero (2012) sizes the
multi-tier prize. Lee et al. (2023) supplies the conflicting last-week sign. Shapiro & Drayer (2012) is
small and consistent. He & Lin (2026) is the only peer-reviewed work on resale price caps in tickets and
is a model of matching, not an econometric study (`01-a` §3; `CORRECTIONS-APPLIED.md` §4 question 1,
unresolved).

**What this literature does not contain**, checked rather than assumed: no fitted decay function,
half-life or time-elasticity for a secondary price path, only day dummies or a verbal direction
(`02-a` §3.4); no per-ticket repeat-sale price path; no peer-reviewed econometric study of a resale cap;
no published out-of-sample forecast of secondary ticket prices; no published distribution of holding
duration or transfers per ticket; and no peer-reviewed measurement of Ticketmaster-style dynamic primary
pricing at scale (`01-a` §4, §5; `02-a` §3.4, Sources).

### 4.2 Caps, regulation and fee disclosure

The regulatory record is class A for the rules and silent on elasticities. The UK government's own
analytical note is a flow-accounting model over 37.1m primary and 1.9m secondary tickets with stated
assumptions (75% markup, 80% of resale by touts, 95% and 25% volume reductions, 20% displacement) and
**contains no demand elasticity at all** (`02-d` §3.2). That is the state of the art in official
analysis of this exact policy question, and it is assumption-driven. The fee-disclosure rule
(16 CFR 464, effective 2025-05-12) is class A for the definition of total price and describes no
distribution of fee sizes (`02-d` §1.1, Sources).

### 4.3 Econometrics of identification, and why it is the centre of this programme

The programme's central methodological result is a case-only-sample result, and its literature is
standard: repeat-sales indices identify ratios only and are biased by selection into repeat trading
(Bailey, Muth & Nourse 1963; Gatzlaff & Haurin 1997; Steele & Goy 1997; Meese & Wallace 1997); hedonic
models are identified up to an affine transformation from a single market (Ekeland, Heckman & Nesheim
2004), which is exactly the missing price anchor; demand is not recovered from a single market's
transactions (Rosen 1974; Brown & Rosen 1982; Working 1927); the linear component of an age-period-cohort
decomposition is not identified (Mason, Mason, Winsborough & Poole 1973; Fosse & Winship 2019); a
case-cohort design needs an expensive covariate measured on a random subset of the risk set (Prentice
1986); informative censoring invalidates the naive estimator (Lagakos 1979); and a policy ceiling with
rationing makes observed consumption uninformative about the rationed buyers' valuations (Glaeser &
Luttmer 2003; Bulow & Klemperer 2012). All **class C** as identification arguments, **class B** where the
supporting evidence comes from another market.

Two transfers from other markets are used and labelled: the primary sell-through bracket is a Tobit with
an observed censoring indicator (Tobin 1958), the benign case, with demand estimation under incomplete
availability inverted (Conlon & Mortimer 2013), **class B**; and price dispersion under search is itself
an equilibrium object (Burdett & Judd 1983), **class B**.

### 4.4 Revenue management, survival, Bayesian pooling, uncertainty

Revenue management supplies the objective's shape and two ordinal results that survive an unidentified
demand function: monotonicity of the optimal intensity in stock and horizon, and the asymptotic
optimality of fixed prices as expected sales volume grows (Gallego & van Ryzin 1994, **class C**). Its
boundary condition fails here, and that is the sharpest single transfer in the programme: `V(T,n) = 0`
is false for a ticket, whose terminal payoff is an unobserved use value, so the endgame is a withdrawal
decision rather than a dump (`01-c` §2.2).

Survival analysis supplies the identified objects: the composite transaction intensity, the competing
risks split, the cure component for never-sellers, and the gap-time distribution, which is the only place
in the programme where this observation set is better than the published data (`01-c` §3; `02-c` §3).
Its price-response half is not identified, and the reason is a feedback loop rather than a sample size.

Partial pooling supplies the cold-start band and the honest statement that at cold start the width *is*
the answer (Efron & Morris 1975; Gelman 2006; DerSimonian & Laird 1986; Viechtbauer 2007;
**class C**). Conformal prediction supplies a data requirement and no estimator, because there is no
exchangeable calibration set and, deeper, no resale price for most of the population
(`01-c` §8; Barber et al. 2023).

### 4.5 Machine learning

The literature is not reviewed because it is not used, and the reason is identification rather than
taste: a gradient-boosted tree, a random forest, a Gaussian process and a two-parameter shrinkage
estimator all need the same missing column on the deviating branch, the ask of the ticket that did not
sell (`02-ai-ml-decision.md` §1.1). There is one structural exception: a censored likelihood beats a
black-box regressor on the hedonic target because the cap truncates the sample from above, and a feature
cannot recover a latent that is absent; the censoring is the model (`02-ai-ml-decision.md` §1.6;
Amemiya 1984).

### 4.6 The absence that dominates

No study in any of these literatures estimates a sale-probability curve from a wallet-bound, capped,
on-chain ticket ledger, because until recently no such ledger existed at scale. That is why Phase 2A of
this programme is smaller than the programme expected in one respect (the asking-versus-realised
problem) and larger in another (exposure, truncation, and off-rail settlement). It is also why the
programme's class A content is entirely cited and its own contribution is class C: identification
arguments, exact algebra, and a specification.

---

## 5. External variable registry

The registry is `records/C-variable-registry.md`, with the admission test from `01-d` §1: name the
channel through whom the variable moves something, check it is knowable at the decision time, check the
ledger does not already carry it, and check it can be obtained lawfully and at what cost. **The decisive
filter was the clock, not correlation**: a variable can only enter if its value is knowable at the
decision time, and the primary price is fixed before the on-sale, which removes weather forecasts,
injuries, transfers, competing events, added tour stops and support-act announcements from the
primary-price problem entirely (`01-d`, What I concluded).

Counts, as the tables give them after `01-d` CORRECTION 1 withdrew its abstract's figures: **17 admitted**
(V1 to V17), **11 rejected** (Table C-2), so 28 examined. Priority 1: 5; priority 2: 4; priority 3: 4;
priority 4: 2; priority 0: 2. **9 at priority 1 to 2**, of which four are obtainable from the contract
today.

### 5.1 Admitted variables

Signs are per unit change with the event held fixed. The D1/D2 column is the decision-time verdict from
`03-b` §3: **P** knowable at or before D1, **R** knowable at a D2 instant only, **N** knowable at neither
without look-ahead.

| # | Variable | Mechanism (through whom) | Sign | Availability and vintage | Class | Pri. | Verdict |
|---|---|---|---|---|---|---|---|
| V1 | `time_to_event` | perishable inventory: the seller's option value decays and the buyer's outside option also decays, and the two oppose each other | conditional, **not monotone** | contract, static | A | 1 | P |
| V2 | `primary_sell_through` `issuedCount/totalSupply` | rationing at face reveals excess demand; a sold-out tier is censored demand, an unsold one is a point on the demand curve | + | contract, but a **snapshot with no capture time** (vintage K), so it must be logged at the decision instant | C mechanism, B support | 1 | R, **K** |
| V3 | `resale_policy` (`resalePriceCapBps`, `resaleEnabled`, `requiresVerifiedWallet`, `transferRestricted`) | a binding ceiling truncates the price distribution and suppresses seller upside; gates add friction to every hop | cap binding gives a mass point plus excess demand behind it; frictions reduce supply | contract, event and ticket level, static | C | 1 | P |
| V4 | `venue_capacity` | the denominator of scarcity; capacity against demand decides whether resale exists at all | negative on markup at fixed demand | **not in contract** (`venue` is free text); static external lookup | B | 1 | P via external join |
| V5 | `custody_trail_features` | hop count, holding duration, repeat-reseller identity, the ticket's own markup history | + for repeat sellers and rapid churn; lower supply pressure with long holding | contract, per row, vintage H if truncated at the cut | C | 1 | R |
| V6 | `venue_type` | fixes weather exposure, sightline structure and capacity band; a stratifier | stratifier, not a main effect | not in contract; derived from name and capacity | B / D | 2 | P |
| V7 | `city_market_size` | scales the local buyer pool and the walk-up segment | + | free (Census, DMA); condition: the release date must precede the decision | B | 2 | P |
| V8 | `competing_supply_same_night` | substitutes in one entertainment budget and one calendar night | negative | external; vintage K because events are announced after this one's on-sale | D | 2 | P with condition |
| V9 | `tour_routing` | substitution versus scarcity: a nearby stop cannibalises, a final stop or residency raises travel demand | negative inside about 300 km and 7 days; positive for final or one-off | external; vintage K, the completed routing is the future | D | 2 | P with condition |
| V10 | `artist_or_team_state` | a shock to expected quality and to its variance | + on positive quality surprise | external (ESPN endpoint, keyless, verified live); resolves after on-sale for most events | B on attendance, D on price | 3 | R only, not knowable at D1 |
| V11 | `event_calendar_structure` | competes for the same leisure slot and sets travel feasibility | small, either sign | static calendar join | B | 3 | P |
| V12 | `weather_forecast_outdoor` | day-of attendance cost, outdoor venues only; indoors the honest coefficient is zero | rain negative, heat ambiguous | Open-Meteo free tier or NOAA archive; **use the forecast issued at the decision instant**, never the observation | B | 3 | R only, inside the forecast horizon |
| V13 | `album_or_release_timing` | refreshes salience and setlist novelty | + | MusicBrainz, Wikidata; the announced date at the decision instant | D | 3 | P with condition |
| V14 | `secondary_listing_depth` | the quantity axis: without it "no sale" cannot be separated from "nothing was offered" | negative on price as depth rises | **not in the contract**, and no lawful external source exists (`E-data-source-registry.md`, What is missing) | C | **0** | N |
| V15 | `seat_coordinates` | proximity and sightline: the strongest within-event price axis in every published ticket study | + toward the stage | **not in the contract**; the only route is the company's internal ledger or manual transcription of venue charts | A | **0** | N |
| V16 | `macro_conditions` | the budget constraint and the price of the outside option; moves every event at once, so it cannot explain cross-sectional differences | +, negligible within event | FRED, BLS; **use ALFRED vintages**, not the revised series | B | 4 | P, vintage K as published |
| V17 | `transit_and_access` | the effective all-in cost of attending; only shocks matter, the static part is absorbed by a venue fixed effect | negative on a cost shock | GTFS free, alerts ad hoc | D | 4 | P |

One variable the contract does not carry and that no finding classifies because it does not exist:
**`event_category`**. It is the best single cold-start covariate (`02-e` §2.2, §10 question 2), and its
absence is the strongest argument against the comparables strategy.

### 5.2 Rejected, with the reason

Each failed a specific test, and the list exists so no later agent re-proposes it (`01-d` §3):

| Candidate | Reason |
|---|---|
| Google Trends search interest | not lawfully collectable: no official API, `robots.txt` disallows the endpoints every scraper uses, and the terms prohibit automated access against `robots.txt`. Redundant with observed demand anyway |
| X/Twitter volume and sentiment | pay-per-read ($0.005 per post, 3M reads/month cap, about $150/month at 1,000 posts/day), retro-deleted, and the signal is dominated by the market's own price |
| Reddit volume and sentiment | the Data API terms forbid deriving revenues and grant **no right to use user content for training an ML model** without rightsholder permission |
| Spotify listeners or popularity | `popularity` and `followers` are marked deprecated, and content "may not be used ... to train a machine learning or AI model". Rejected on licence, not on mechanism |
| YouTube view velocity | no public velocity API; scraping contradicts the same terms; the mechanism sits upstream of a variable already observed |
| Artist death, scandal, cancellation | point shocks with no distribution and no counterfactual; keep as a human override, never a feature |
| Support act announced later | a real mechanism, and the only source is unstructured press |
| Airport proximity, parking, road layout | static per venue, absorbed entirely by a venue fixed effect |
| Tourism flows, convention calendars | monthly, metro-level, collinear with city market size which is free |
| School terms and holiday weeks | a subset of V11 |
| Weather at indoor venues | the coefficient is zero by construction; including it is a mechanism violation dressed as a feature |

### 5.3 The two absences that outrank every external source

**V14 listing depth and V15 seat coordinates** are not sources at all, they are gaps in the wire
contract. `01-d` says listing depth is "worth more than every external source in this report combined",
and `E-data-source-registry.md` closes the external route: the marketplace APIs that would carry it are
barred, not market-side, gated behind an approval nobody has, request-only, or scraping with unresolved
legal exposure. The cheapest route is the platform's own four fields.

`01-d`'s handover note stands and is repeated in §21: the two open questions that matter are whether the
company's internal ledger holds seat coordinates and listing events that the wire contract omits, and
whether the company can obtain Ticketmaster partner access.

### 5.4 Money gates

Nothing in the registry is authorised and no budget is assumed. As published: X API about $150/month at
1,000 posts/day (do not buy, no mechanism); Chartmetric $40/month billed yearly (do not buy, downstream
of a source that bans ML use); Open-Meteo commercial licence, price not read (not yet, use NOAA);
Ticketmaster Inventory Status or Partner, not publicly priced and request-only (**worth one email**, the
only lawful listing-level primary price feed identified); tickets.dev from $50/month for 1,000 captures
(do not buy yet, solve the exposure gap inside our own platform first); paid Trends aggregators (do not
buy). Free and ungated: Ticketmaster Discovery, our own RPC, NOAA, GTFS, Wikidata, OpenStreetMap, FRED
and ALFRED, Census, MusicBrainz, calendars. Rule adopted in `E-data-source-registry.md`: **absence of a
stated prohibition is not permission.**

---

## 6. Interaction and causal analysis

### 6.1 The registry, and the definition of "binds"

Thirteen interactions (`03-a` §1). An interaction **binds** if it is present in the record we will have,
if omitting it changes the sign or existence of a recommendation rather than its precision, and if its
sign is known from a constraint, a derivation or a published measurement. Applying that test yields
**exactly two**: I5, markup conditional on the cap binding, and I2, the time-to-event slope conditional
on popularity.

| # | Interaction | Predicted sign | Acts on the decision? | Class | Binds |
|---|---|---|---|---|---|
| I1 | inventory depletion x demand intensity | + and increasing in intensity; zero when demand is slack | no, it is state | C + B direction | no: both factors are outcomes of the same latent demand and of the organiser's own price |
| I2 | time-to-event x popularity | negative in soft or already-cleared events; about zero or positive when excess demand survives to the door | **yes**, it sets the level at D1 | A for both forces, **D** for the net sign here | **YES** |
| I3 | resale premium x primary inventory remaining | +, one-sided: sold out implies resale at or above face | indirectly | C by construction, A support | one-sided only |
| I4 | price momentum x seller concentration | negative on level and slope, positive on the hazard | no | A in MLB, **D** here | no: three independent reasons |
| I5 | **markup x the cap binding** | negative on every observed mean and upper quantile, certainly; positive on the average transaction price if a stringent cap pushes high-price sellers out | **yes**, it is a parameter of the data-generating process and it moves with `p0` | **C** for truncation, B for rationing, **D** for evasion magnitude | **YES** |
| I6 | elasticity x remaining inventory | elasticity falls as the house fills, so the optimal price rises | yes, it decides boundary versus interior | C | in the objective, imposed not estimated |
| I7 | cold-start degradation x event category | unknown | only by declining to pool | **E**: the field does not exist | no |
| I8 | custody-hop speed x tier | hops per ticket-day up in top tiers on tight events | no | **D**: no published measurement of hop speed exists | no |
| I9 | cap binding x the chosen primary price | the binding window shortens as `p0` rises; the share at the ceiling is approximately invariant | **yes**, it is the decision | C | yes, in the objective and in the learning loop |
| I10 | verified-wallet gate x demand tightness | unknown and not a sign: a mixture of two regimes | no, organisers set it | **D** | no |
| I11 | fee wedge x elasticity | `dp*/df > 0`, `dp*/deta < 0`, `dp*/dphi = 0` | yes, it is the objective | C | in the objective |
| I12 | cap stringency x seller concentration | + on the average transaction price, negative on listing depth | yes, once, at event creation | C model, A that caps leak | no: the cap is chosen as a function of expected demand |
| I13 | **sale hazard x the ask** | negative, magnitude unknown | yes: it is the sentence the product promises | C mechanism, **not identified** | binds in what the product may claim, not in what it can compute |

### 6.2 The two that bind, in plain terms

**I5 is an artefact of the recording policy, and that is why it is certain.** The observed markup is
`min(m*, c)` by definition, so the interaction is not something the market does, it is something the
record does. Its sign needs no data (**class C**). Two readings matter: the bias is increasing in the
share of sales at the ceiling, and that share is highest exactly where value is highest, which inverts
the error rather than merely shrinking the sample; and the bound's information content is *decreasing*
in that share, being informative at `s` near 0 and nearly empty at `s` near 1 (`02-b` §2). What the engine
must never say is that a ticket sold at the cap reveals what the buyer valued it at: allocation behind a
binding ceiling is effectively random among those who want the good, and competition dissipates the
surplus above the ceiling through non-price channels (`01-b` §4.5(iii), **class B**).

**I2 is causal in mechanism and predictive in implementation.** Both halves are measured: decaying option
value on the seller side (Sweeting, **class A**) and rising arrivals on the buyer side (**class A** as
arithmetic on Leslie & Sorensen's shares). The implementation is predictive because popularity is
manufactured: the observable stratifiers are primary sell-through, which is the organiser's own price
decision, and the cap-hit share, which is a function of `p0`. So the slope is reported **within a
stratum**, and the stratum is policy-determined and labelled as such (`03-a` §1.1, §2.1).

### 6.3 Causal verdicts

Five threats are in play: confounding, simultaneity, selection, policy-created artefact, and policy
endogeneity. Each interaction gets one verdict (`03-a` §2):

| # | Verdict | Threat that binds | What would separate causal from predictive |
|---|---|---|---|
| I1 | predictive-only | confounding and policy creation | a randomised primary price, or a demand shock with the price fixed |
| I2 | causal in mechanism, predictive in implementation | confounding by the conditioning variable | the cap-mass trajectory as a sign test plus a period-effect diagnostic |
| I3 | causal, one-sided | simultaneity and policy artefact | a randomised face, or a cap-free event |
| I4 | predictive-only | selection and policy artefact | the listing panel, which shows a decision rather than a trade |
| I5 | artefact of the recording policy, with a causal behavioural component (class D) | policy-created artefact, then confounding with demand | a cap-free event for the tail's location; `cap_blocked` plus the ask for the rationed quantity; dark-ticket detection for the leak |
| I6 | causal in theory, not identified | simultaneity and selection on issuance | a randomised face, and nothing else |
| I7 | not estimable | none available to name | the category field |
| I8 | predictive-only | selection and measurement | a hop panel with the enforcement gate as a stratum |
| I9 | causal by algebra | no confounding, a self-inflicted shift | logged recommendation and acceptance, as a propensity |
| I10 | a mixture, neither causal nor predictive | policy-created artefact and collinearity | a platform-level experiment |
| I11 | causal by algebra | none econometric | one settlement field, which makes the wedge measured rather than assumed |
| I12 | causal in a model, untestable here | policy endogeneity | a policy change not conditioned on demand |
| I13 | not identified | selection (case-only), endogenous ask, collinearity with time | listing episodes **with ask dispersion among simultaneously live listings**; the fields alone are not enough |

**Three limits apply to every verdict above**, and they are limits on meaning rather than on estimation
(`03-a` §2.2): the level of value is not identified, so every verdict is about shape and sign; every
number is conditional on the primary price actually charged, because the ticket population is the
population that bought at that price; and no interaction can be estimated on the buy side, because there
are no bids, offers, views or searches anywhere in the contract.

### 6.4 Should the market be modelled as a dynamic feedback system? No.

The programme names seven loops. Four have no state variable in the contract at all (inventory releases,
seller price revisions, visibility, listing decisions), one is a static constraint (the cap translates
with the decision), one is a simultaneity (the buyer's resale option is part of primary willingness to
pay), and **exactly one is a genuine dynamic system the product can act inside**: the loop from the
recommended price to the data the next event's model is trained on, with a one-event lag (`03-a` §3).
Its three consequences are in the engine's design: scale invariance makes the truncation permanent, so
the engine cannot price its way out of a censored sample; the cap-binding window is an output of the
decision, not a property of the event; and the fix is a logged action, not a model.

The sentence the deliverable must not contain is "we model the market as a dynamic feedback system".
The true sentence is narrower: *we model one decision, with a censored price record, two opposing time
forces, and a policy that feeds back into the record one event later.*

### 6.5 The twelve interaction features, and which are buildable

`03-a` §4 specifies IF-01 to IF-12 with inputs, clock, sign, failure mode and buildability. Six need no
new field and no upstream component (IF-02 cap mass, IF-04, IF-06, IF-07, IF-10, IF-11). Two need the
platform to log a value at decision time rather than return an extraction snapshot (IF-01 time-to-event
by tightness, IF-05). Three are blocked on a component specified and not built, namely the path model or
the event panel (IF-03 cap window as a function of the candidate price, IF-08, IF-09). One is blocked on
the missing settlement field (IF-12).

Two of those deserve the space. **IF-02, the cap mass**, is the best feature in the dataset and the first
thing to compute on real rows: every input is in `LedgerEntry` and `Event`, it needs a one-basis-point
tolerance because the wire rounds markup half away from zero, and a zero is not evidence that the cap
does not bind (`03-a` §4; `03-b` §9 D-1). **IF-03, the cap-binding window `W(p0)`**, is one root-find
per candidate price against the fitted path, and it is what makes the feedback loop visible to the
organiser (`03-a` §4; `02-a` §7.2).

**A leak warning with a name.** The version of the cap-crossing date the programme recommends is defined
as *the last* day on which a sale landed at the cap, which is a whole-history quantity: to know a day was
the last you must have seen every later day. The as-of restatement ("the most recent cap sale at or
before the passing instant") is admissible; the retrospective one reads directly on the level of value
and will be learned by any model given it (`03-b` §1 point 5, §4 T1).

---

## 7. Statistical methodology

### 7.1 The identifiability ledger, which everything else answers to

| # | Quantity | Status | Assumption needed | Minimal additional observation |
|---|---|---|---|---|
| **T1** | latent resale value `V_i(t)` | set-identified at trade instants; not identified between trades or for never-traded tickets; the level is identified only up to an affine normalisation | martingale interpolation; price-taking at trade; cap non-binding or `V` at least the cap | a second trade or a quote in the interval; for the level, one exogenous price anchor |
| **T1p** | `V` for an event with no resale history | not identified; only a prior predictive | exchangeability of events given covariates; a **known** between-event variance | at least two completed events per stratum with resale activity |
| **T2** | price path over the remaining horizon | set-identified: curvature and event deviations identified, the **linear trend is not** (exact age-period-cohort collinearity); the path is identified only for repeat-traded tickets | a normalising restriction on the linear component | staggered start dates plus one normalisation; seat coordinates to fix the within-tier mix |
| **T3** | sale hazard as a function of price | **not identified**; only the product of the hazard, the ask density and the listing probability is, and the unconditional intensity is | that the ask is exogenous to value | a listing panel, and asks on a random subset of the risk set |
| **T4a** | hedonic price function | set-identified up to affine transformation, subject to selection | attribute prices constant over the window; sold units representative | seat coordinates |
| **T4b** | demand, elasticity | not identified from secondary trades; **set-identified from primary sell-through**, bounded below at each distinct cap level | uniform primary pricing; face equals the primary transaction price; `issuedCount` means sold | a primary inventory time series; exogenous price variation |
| **T5** | primary price maximising risk-adjusted net value | set-identified, width equal to the union of the T3 and T4 widths; structure and one-sided bounds identified, the point optimum not | the T3 and T4 models, a fee model, a risk functional | nothing of its own |
| **T6** | predictive uncertainty, calibration | estimable for the **sale indicator** on the full population; not validatable for any price distribution | that the evaluation sample is representative, which is false by construction for prices | an ask panel, or a random hold-out of listings scored but not sold |

Three sharpenings from later findings, recorded because they change the build: **curvature is only
operationally identified if the fit carries a free within-event linear term** (`02-a` §4.3);
**`issuedCount` is a temporal-correctness hazard**, because a snapshot with no capture time used as a
predictor at the decision instant is look-ahead, so sell-through may enter only as an ex post descriptive
statistic until the platform timestamps it (`01-c` §3.6; `03-b` A15); and **a mass point at the cap is a
known price at one date per event**, a partial answer to T1's missing anchor and not a full one
(`02-a` §6.1 C4).

### 7.2 The value level: a censored hedonic, fitted by EM

The load-bearing formulation (`B-mathematical-kb.md` §13, F3). Response `y = log(price/face)` on every
settled sale of every ticket in the censused population. Latent model `y* = mu + a_tier + d_event +
s(tau) + gamma'X + e`, with `s` a piecewise-linear spline in days-to-event with knots inside the final
fortnight, and `X` the attributes fixed at issue. Observation rule: `y = y*` when `y*` is at or below
`c_e = log(1 + cap_bps/10000)`, with a point mass at `c_e` under the censored regime or no observation
beyond `c_e` under the truncated regime. Estimated by EM, with the inverse Mills ratio in the E-step and
least squares in the M-step, about 120 lines of standard library, monotone convergence.

Five reasons it is the load-bearing choice, and one caveat (`B` §13): its identifying assumption (quality
fixed at mint) is exactly true rather than approximately true, because a ticket's attribute vector cannot
change; it produces output for a ticket nobody has ever resold; it carries time-to-event, so it subsumes
the price path rather than sitting beside a separate forecaster; it uses the cap as information rather
than being ruined by it; and it needs none of the four missing listing fields. **The caveat is that it
cannot set the primary price** (§1.6, §12): a model in units of face is invariant to face.

**Which likelihood applies depends on an open question.** If the cap is enforced on chain, the transfer
reverts and no sale above the cap is possible, which is truncation. If the cap is enforced by the
platform refusing a listing, sellers pile up at the ceiling and the latent willingness to pay above it is
censored. The two give different likelihoods and are distinguished empirically by whether a mass at
exactly the cap exists, so **the first diagnostic on real data answers the question** (`01-c` §4.3;
§21 Q3).

**The independent check.** A repeat-sales index on pairs of sales of the same `mintAddress`, response
`log p2 - log p1`, regressors sparse time-cell dummies, ticket fixed effects differenced out and never
estimated. It has **no level**, so it must never be presented as a price, and it exists to disagree
informatively with the hedonic's time effects; disagreement between them is the diagnostic for
composition bias (`01-c` §4.5).

### 7.3 The price path: one estimated parameter, and a declared normalisation

Specification (`02-a` §8): the fitted log relative price at horizon `tau` is the anchor level plus
`theta` times the change in `log(1 + tau)`, plus, only when the aggressive normalisation is chosen,
an event-specific linear slope applied to the change in days.

- `theta` is the **one estimated structural parameter**, the degree of deadline convexity, pooled across
  events by inverse-variance weights from a per-event two-by-two within-event solve, with guards (at
  least 4 sales, positive determinant, at least 5 days of spread) and a reported count of discarded
  events.
- The per-event linear slope is a nuisance that exists only so the curvature estimate is not
  contaminated by the confounded direction.
- `omega` in {0, 1} is a **declared normalisation, not an estimate**: 0 uses only the identified
  curvature, 1 attributes all within-event level movement to time-to-event. Report both; the pair is the
  bracket.
- `K = 5` and a one-day step are constants fixed a priori. Tuning them would add two parameters the data
  cannot support.

The record is honest about what this is: a fixed-effects meta-analysis of within-event curvature that
treats the per-event variances as known, which understates the uncertainty of the pooled curvature when
events are few (`02-a` §8.3).

**Pre-registered decision rule:** if the conservative specification does not beat the martingale out of
sample by a margin that survives the per-event dispersion of the curvature, ship the martingale. "A
martingale with a measured residual band is a defensible product and a declining trend that is not there
is not" (`02-a` §8.5).

**The conditioning inversion, which is the report's main warning.** Sweeting's within-seller path is
estimated on listings that **failed to sell and were relisted**: a path conditional on failure. Our
ledger observes sales: a path conditional on success. These are different conditional distributions of
the same latent process, selected in opposite directions, so his magnitude is an upper bound on what
ours can show, and the two cannot be pooled (`02-a` §4.4). The direction transfers; the number does not.

### 7.4 The sale intensity: what is identified, and the exact reason the price response is not

The observed rate at price `p` is the product of the wanted hazard `lambda(t|p)`, the density of asks
`pi(p | listed, t)` and the probability a ticket is listed at all. We observe the left side; nothing
separates the three factors, because the mark is written only where the sale happened (`01-b` §4.3).

Three quantities *are* identified, not one (`02-c` §1.3, §2.3):

| ID | Object | Why identified |
|---|---|---|
| O1 | the composite intensity, its cumulative incidence, time to first transaction, and the share that ever transacts | the ticket population is censused: every ticket has an `issue` row and a known life, so the risk set over ticket-life is observed |
| O2 | the joint mark-time intensity: transactions per ticket-day at each markup | the joint distribution of time and price on transactions is observed in full |
| O3 | cause-specific exit intensities, the competing-risks cumulative incidence, and an **upper bound** on the never-offered share | redemption and revocation are terminal and observed |

Four things are not identified: the price response; the split of the composite intensity into the
offering rate and the sale rate; the ask distribution; and any counterfactual in the **primary** price,
because the population is tickets that someone bought at the price actually charged (`02-c` N1 to N4).

**The naming correction matters and is adopted.** The composite intensity is the probability a ticket is
offered times the sale hazard averaged over unrecorded asks: a base rate of transaction per ticket-day of
life, not a sale hazard. Calling it "the unconditional sale intensity" is defensible algebra and a bad
name, because a reader will plug it into `1 - exp(-lambda h)` and be told the probability their ticket
sells (`02-c` §1.2). The engine labels it a transaction rate for the ticket population and says in the
same sentence that it is not the probability a listed ticket sells.

**The estimator.** A piecewise-exponential composite intensity on a time-to-event grid with competing
risks and a cure component, which is exactly a Poisson regression with an exposure offset: the
log-likelihood sums, over time buckets and covariate cells, of observed counts times the linear predictor
minus exposure times its exponential. Fitted by Newton-Raphson on aggregated cells (tens of columns, not
millions of rows), with a separation guard (Firth or an explicit ridge, reported), a printed condition
number, and a closed-form cumulative incidence built from the fitted per-bucket survival and the sale
share of the total hazard (`02-c` §3.3, §3.4, §3.8). Redemption is a competing risk, not independent
censoring, because a ticket redeemed by the wallet it was issued to is a ticket somebody wanted, so
attendance and resale are substitutes (`02-c` §3.4; Fine & Gray 1999).

**What it still is not, even with the four fields.** The fitted object is the hazard *given the ask the
seller chose*: a prediction under the observed ask policy, not the sale probability if we set the price,
because the ask carries the seller's private information about value (`02-c` §3.5; Working 1927).

### 7.5 Cold start: the band, and four ways to constrain the between-event variance

Target: the event's mean log price-to-face ratio, taken as a geometric mean so that the right-skewed
markup distribution does not let a handful of high marks dominate. Model: event means drawn from a normal
population with between-event variance `tau^2`, each event's sales normal around its own mean. At cold
start the covariate term collapses to a scalar, so **two hyperparameters**. The update is a precision
weight `B = tau^2/(tau^2 + s^2)` on the event's own mean and `1 - B` on the pooled mean. A genuinely new
event has infinite own variance, hence zero weight, hence the pooled mean: **`tau` does not enter the
cold-start point estimate at all, only the interval** (`02-e` §4.3).

Four ways to constrain `tau^2` with few events, and **none of them estimates it** (`02-e` §4.4): the
DerSimonian-Laird moment estimator (one degree of freedom at two events); an upper confidence limit from
the `Q` statistic, the only conservative object available; a 601-point grid posterior under a declared
half-Cauchy prior, which at one or two events is the prior wearing a posterior's clothes and must be said
to be that; and a declared floor. The cost of a small event count is computable and large:

| Events `J` | 95% interval on the between-event variance, as a multiple of the point estimate | span |
|---|---|---|
| 2 | 0.001x to 5.02x | 5100x |
| 3 | 0.025x to 3.69x | 146x |
| 5 | 0.121x to 2.79x | 23.0x |
| 10 | 0.30x to 2.11x | 7.0x |
| 20 | 0.47x to 1.73x | 3.7x |

**Two degenerate cases, both traps.** A moment estimate truncated at zero leaves the cold-start point
estimate unchanged, because it was the pooled mean anyway, and collapses the interval to the sampling
spread of an arithmetic mean, which shrinks without limit as tickets accumulate: **invisible in the
number, fatal in the width**. And at one event the moment estimator's denominator is exactly zero by
construction, not by numerical accident, so the between-event variance must not be estimated at all
(`02-e` §4.5). The engine uses a declared floor and a nine-event threshold rather than five, because
`03-b` §6.4 puts the floor for any between-event quantity at about nine, and an estimated variance
beside a sentence saying nothing is fitted would contradict itself (`BUILD-REPORT-CONSOLE.md`
deviation 4).

**The borrowed prior, with its liabilities.** Leslie & Sorensen's three reported facts (41% mean markup,
26% below face, 25% above +67%) are jointly consistent with a lognormal log ratio of mean 0.261 and
standard deviation 0.406, and the arithmetic-mean reading reproduces the third fact while the median
reading does not (`02-e` §4.7; class A for the inputs, class B for the transfer). Carrying it: the
location is a borrowed prior from eBay and StubHub in 2004 for 56 rock concerts, **class D** for the
transfer; the selection direction is known and points up, because resold tickets are better seats; and the
dispersion gives an **upper bound** on the between-event standard deviation, not a value.

**The handover count**: the number of the event's own sales at which its own mean and the population mean
carry equal weight is the within-variance divided by the between-variance, derived in one line. With a
within-event standard deviation near 0.4 and a between-event standard deviation between 0.1 and 0.406 it
is roughly 1 to 16 sales: one order of magnitude, which is the honest precision of the statement
(`02-e` §4.6).

### 7.6 Uncertainty

Three objects that must not be conflated (`02-e` §5.1): the event's mean log ratio, with variance
`tau^2 + V(tau)`; one ticket's realised ratio, wider by the within-event variance; and the population
mean, with variance `V(tau)`. A cold-start headline is the first; a single-ticket price carries the
second; the third is a parameter interval and is not a prediction about anything.

What is available today (`02-e` §5.2): a prior-predictive interval for a new event's mean from a declared
`tau`; the sensitivity table over `tau`; an upper confidence limit on the between-event variance from `Q`
at two or more events, with the span table showing how little that says; a `t`-based interval on the
pooled mean because below ten events the normal quantile is materially wrong; and the exact arithmetic.
What is not available: any coverage claim. The band is a **prior-predictive** interval, not a confidence
interval, because the object it covers is a single unseen event and there is no repeated-sampling
statement; and it is not calibrated, because calibration of any price distribution is blocked by
selective labels (`01-b` §4.6; `02-c` §5.2).

**An in-sample reliability curve is worthless here, and the reason is algebra rather than opinion.** With
one intercept per time bucket, the score equation for that intercept sets predicted events equal to
observed events in that bucket, so a reliability curve grouped at the model's own granularity *is* the
score equation plotted. Any miscalibration it can show appears only at a coarser grouping, so it measures
the grouping. **There is no calibration number in this programme and none may be manufactured by
simulation** (`02-c` §5.2; `00-data-situation.md` §5.2).

### 7.7 Temporal correctness, as a method rather than a principle

The audit's three families are clock, population and edit, and one mechanism closes all three
(`03-b` §1 point 4): a mandatory cut argument with no default, a prefix-invariance property test, and a
future canary. Concretely:

- **The cut is a value, not a query.** It is written into the fold record and passed to every feature
  function. A feature whose cut defaults to "now" is a fail.
- **One filter, at the top, before the first sum, count, max or sort,** on the same code path production
  uses. A second filter inside an aggregation is a defect even when it is correct.
- **The cut is on the row's own clock:** sort on slot where slots exist and on the timestamp with slot as
  a tiebreak where they do not, and count the null-slot rows so the fallback is visible.
- **Objects that may not cross the cut** (`06-validation-protocol.md` §2.2): a revised macro series (use
  the vintage), a venue capacity or city population figure whose release postdates the cut, a
  competing-event or tour-routing set assembled after the cut, a weather forecast outside its horizon,
  any neighbour or comparables feature computed over the whole sample, and the organiser's own chosen
  price as a free regressor.
- **The one object that must cross the cut and be logged:** the engine's own prior recommendation. A
  leakage protocol that only asks "was this knowable" is incomplete for a system whose output is an
  input.

**The feature most likely to ship with a leak is one the programme recommends**, the cap-crossing date,
and it was described in §6.5.

---

## 8. Machine-learning methodology

### 8.1 The decision, and it is a decision not to use one

`F` D5 records: build exactly one fitted estimator, in its prior-only branch, capped at one hour, labelled
as a declared width, and **do not enter the AI track**. The evidence is `02-ai-ml-decision.md`, and the
argument is identification rather than taste:

1. **The binding constraint is identification, not functional form.** Four target quantities are not
   identified, and in every case the reason is a missing regressor or a missing latent (`01-b` T1, T1p,
   T2, T3, T4b, T5). A gradient-boosted tree, a random forest, a Gaussian process and a two-parameter
   shrinkage estimator all need the same thing on the deviating branch: an observation of the ask on
   tickets that did **not** sell. Swapping the estimator does not add a column.
2. **At cold start the partial-pooling point estimate is the pooled mean**, so the estimator degenerates
   to the hand-specified alternative and costs one file instead of a throwaway.
3. **A judge recognises ML by a fit, a baseline and a metric**; the fit has no data, the metric can only
   be SIM, and the benchmark ladder that would settle it cannot be run.
4. **The one structural place where a statistical model beats a black box** is the censored hedonic: a
   feature cannot recover a latent truncated from above, so the censoring has to be in the likelihood.
   That is the argument to use when asked why there is no boosting in the product
   (`02-ai-ml-decision.md` §1.6).

**What would change this answer**, each a checkable fact rather than a matter of taste
(`02-ai-ml-decision.md`, What would change this answer): real ledger data exists somewhere, so the
benchmark ladder becomes runnable and the estimator's status changes from UNVALIDATED to measured; the
four listing fields arrive, so the nonparametric-in-price form becomes the first choice by the
programme's own reasoning; seat coordinates arrive, so a model with a real second covariate is worth
fitting, but only after data exists; or the operator authorises randomised price variation, which is the
only route to a causal price response.

### 8.2 The one estimator, stated so it cannot be misread

**Name:** the value band. **Target:** an event's mean log resale-price-to-face ratio, and its predictive
interval for a new event. **Not** a price in currency (the level is not identified), **not** a sale
probability, **not** the optimal primary price.

**Estimator:** normal-normal partial pooling, with `tau` by a 601-point grid posterior under a half-Cauchy
prior (scale 0.25, declared), cross-checked by the DerSimonian-Laird moment estimate and the chi-square
upper limit, with the degenerate branch at zero events returning the declared prior location and a
declared floor and printing the sensitivity grid as the band. **Two hyperparameters** plus one mean per
event; the horizon constants are constants.

**Data requirement: zero new fields.** Per event, settled sales with `priceLamports` and each ticket's
tier `faceValueLamports`, both in the contract.

**Validation status: UNVALIDATED.** The evidence that would validate it is ~~a SIM recovery study and, on a
real ledger,~~ the skill score `1 - MAE_model/MAE_B0` against the martingale on event-level walk-forward
folds with both leakage boundaries enforced. **[CORRECTION 2026-11-07T14:00Z, R2-14 — the first half is now
stale: the SIM recovery study exists (`09-sim-recovery.md`, 13:30Z) and did not validate the band. It found
coverage of the declared band at the true tau of 0.805 at two events against the declared [0.87, 0.93], with
the pooled width restoring 0.897. A SIM study can only test an estimator against its own assumption, so it was
never the evidence that would validate this model on tickets; what it has done is show where the shipped band
under-covers. The real-ledger half stands as printed, and it is what "the second" in the next sentence refers
to.]** **Until the second exists, no accuracy claim of any kind may
be made about this model**, and the number on screen carries "illustrative parameters, not calibrated"
at the same weight as the number.

### 8.3 What was rejected, and why, in one line each

From the model registry's 56 rows (§16.2) and `01-c` §10: tree ensembles and neural networks (rejected
for this data volume, class D as a claim about their usefulness either way); matrix completion and
collaborative filtering (missingness is the phenomenon, and the matrix is almost entirely empty);
Gaussian processes and kriging for a seat-quality surface (needs the absent coordinates and a numerical
stack, and would be prior-dominated at ten observations per event); extreme-value theory for the value
distribution above the cap (a support problem rather than a sample-size problem, and the economically
relevant tail for a perishable good is the left tail, the risk of not selling); agent-based simulation as
a model of the market (a calibrated assumption wearing a simulation's clothes, and `00-data-situation.md`
§5.2 restricts simulation to estimator properties); structural auction estimation (no bids, and the four
listing fields do not touch it); full-posterior sampling (no numerical stack, and the empirical-Bayes
version covers the models actually needed); and contextual bandits over prices (positivity fails by
construction: the platform sets one price per tier and logs no rule and no propensity, so off-policy
evaluation is not hard, it is undefined).

**The one honest bandit** is a bandit over *models*, scored on prequential accuracy, where no money is at
risk; and **the one legitimate adaptive component** is recursive estimation with a forgetting factor, a
rank-one update of about forty lines (`01-c` §6.2).

---

## 9. Transaction-price estimation

### 9.1 What "the price" can be, in this record

Three distinguishable objects carry that name and they are not the same random variable (`02-a` §2):

| Object | Conditioning | What a decline in it means |
|---|---|---|
| asking price at time `d` | a listing is or was posted at `d` | sellers think the clearing price is falling |
| transaction price at time `d` | a trade occurred at `d` | the marginal seller's reservation met the marginal buyer's value |
| transaction price at `d` given the ticket failed to sell earlier | a trade occurred at `d` and not before | a selected survivor's settlement, not the value of a random ticket |

Our ledger records the second, on the success branch only, with no asking price anywhere. Sweeting's
headline within-seller declines are the third. Lee et al. measure the first. **This taxonomy is the
reason published magnitudes are prior beliefs about sign and order of magnitude, not estimates of our
parameter** (class C for the taxonomy, class D for the transfer).

### 9.2 What is identified today

| Quantity | Status | Evidence |
|---|---|---|
| a within-ticket repeat-sales **index** of price change, per event and tier, reported as ratios | identified | class C, `01-b` T1, `02-a` §4.1 |
| the **curvature** of the within-event price profile, and per-event deviations from the event mean | identified | class C, `02-a` §4.3 |
| the **linear slope** of the path | not identified without a declared normalisation (exact APC collinearity) | class C, `01-b` T2 |
| the level of resale value in currency | not identified: only ratios, no exogenous anchor | class C, `01-b` §4.1 |
| the value for a ticket that never resold | not identified, and not "flat": the reason it did not sell is correlated with its price | class C, `01-b` T1p |
| the **floor** on value where the cap binds, and a lower bound on the willingness-to-pay survival function evaluated at observed cap levels | identified, one-sided | class C for the bound, class B for the rationing argument, `02-b` §2 |
| the **mass point** at the cap and its trajectory over time | identified, and the best feature in the dataset | class C, `02-a` §6.2 |
| the **crossing date** at which the latent markup passes the cap | interval-identified, width equal to the gap between the last at-cap sale and the first below it | class C, `02-a` §6.1 C4 |
| the joint mark-time intensity (transactions per ticket-day at each markup) | identified, and it is a descriptive object rather than demand | class C, `02-c` §2.4 |

**The floor, stated exactly.** For any settled resale at the ceiling, the value is at least the settled
price, which for a capped event is `face x (1 + c)`. For any settled resale below the ceiling, the value
is at least the observed price in the same sense. Aggregated over a tier, the record identifies a lower
bound on every observed transaction and nothing on any unobserved one (`02-b` B1). **The assumption is
not a convenience, it is the clause known to be violated**: off-rail settlement pushes the true
consideration further above the recorded one, which keeps the bound a bound rather than making it wrong
(`02-b` §2; class C for the bound, class D for the channels).

**What is not obtainable at any sample size** (`02-b` §2): no upper bound on value from the resale record,
because nothing above the ceiling is sampled; no level; and no price-response curve. A corrected value is
not identified from the contract as it stands and no estimator recovers it, for three independent
reasons, so fixing one does not fix the others: the level is not identified, the upper tail is not
identified, and the consideration is not fully recorded.

### 9.3 The estimator the engine would run, and what it can be trusted for

The censored hedonic of §7.2 is the primary estimator for the level and the cross-section. Its output is
a **quality-adjusted relative price** for every ticket including never-traded ones, which is the engine's
headline claim and the one thing neither the repeat-sales index nor the hazard can give. Its coefficients
are not elasticities and must never enter the optimiser as though they were willingness-to-pay
derivatives (`01-c` §4.1).

The engine that exists (see §17) does something smaller and says so. It computes, from the truncated
ledger at a stated cut, the regime, the at-ceiling share, the floor or a band, and a point that is the
raw tier mean of log price-to-face; the pooled mean and the shrinkage weight are computed and, as of the
review, **unused** (`07-engine-review.md` §2.3). On the shipped fixture the omission moves a level by
about 0.2%, so it is a narrowing of the estimator rather than a visible arithmetic error, but it is a
place where the code is narrower than the finding and it is recorded as such.

### 9.4 The three design consequences that bind the estimator

1. **Quantiles below the censoring point survive; the mean and upper quantiles do not.** A low quantile of
the observed distribution is the same quantile of the latent one whenever the cap mass is below it
(`02-a` §6.2, Powell 1986). A cap-hit share above 50% makes the median the cap, so the rule is: compute
the share first and refuse a central path statistic above 50% (`02-a` C2).
2. **Never hand a markup-space path to a primary-price optimiser.** The curvature can be estimated in
  either normalisation, because they differ by an event-tier constant; the level must be converted to
  money and the cap re-applied at `p0(1+c)` for each candidate price, or the model answers a different
  question from the one that was asked (`02-a` §7.2).
3. **A pooled estimate across capped and uncapped events is a mixture of a truncated and an untruncated
  distribution**, which is worse than either alone because it produces a number with no regime label.
  Pooling requires cross-event exchangeability stated on the row (`02-b` §3.3).

---

## 10. Demand and sale-probability estimation

### 10.1 The headline refusal, and why it is the finding rather than a gap

The programme asks for "the probability it actually transacts at a given price". That quantity is
**not identified** from a completed-transaction ledger, and the reason is not sample size: the ask is
recorded only on the success branch, so the observed rate mixes the sale hazard, the ask density and the
listing probability, and nothing separates them (`01-b` T3; `02-c` §1.1, confirmed by
`00-adversarial-review-phase1.md` Claim 1). A curve fitted to this record reports which sellers chose
which prices and calls it demand. **It will look monotone, it will look well-behaved, and it will be an
artefact** (`01-b` §4.3, class D, dangerous precisely because it will look estimable).

The engine therefore refuses it, in words, on every page: the platform does not record asking prices, so
the chance a ticket sells at a specific price cannot be estimated, and what is shown is what actually
happened (`02-c` §7.2; §17.4).

### 10.2 What is supplied instead, and to what standard

| Statement the product can make | Quantity | Status |
|---|---|---|
| "In this tier, X% of issued tickets transacted at least once before the event" | cumulative incidence of the composite intensity | identified, class C |
| "The median first transaction happened N days before doors" | quantile of time to first transaction | identified |
| "Trade concentrates in the last K days: P% of ticket-days at risk fall there and Q% of transactions do" | the mark-time intensity plus exposure | identified |
| "Of tickets that transacted, R% transacted more than once" | recurrent-process count distribution | identified |
| "Tickets in this tier were listed at least S% of the time" | the offering split | **not available** |
| "At the price this tier has been transacting at, a listed ticket converted at rate r" | a claim about the market's own prevailing ask, not about an arbitrary ask | defensible only with its condition attached |

Two footnotes are mandatory on the last row (`02-c` §2.6): hazards are not linear in price, so the
average hazard is not the hazard at the average ask; and the prevailing ask is *inferred* from realised
prices, which conflates the two, so the sentence is a benchmark rather than a prediction for a specific
listing.

### 10.3 The estimator that follows once the four fields exist

Specification B (`02-c` §4): unit is the **listing episode**, a maximal interval over which the ask is
constant, and a price revision is a new episode. The hazard is a piecewise-constant baseline in
time-to-event times an exponential of ticket covariates, the scaled ask and live tier depth. The
likelihood is the same Poisson-with-offset form as §7.4, so **the solver does not change**: new rows, same
code. The target functional is the probability of sale within a horizon at a chosen ask, which must be
reported as a competing-risks quantity, sold versus withdrawn.

Three functional forms for the price response, estimated in this order (`02-c` §4.2): nonparametric in
price, as bins, with no shape imposed; constant elasticity in markup, as the reporting form, imposed only
if the nonparametric surface's iso-hazard contours are straight; and a choke-price form, commercially the
most interpretable and the strongest functional commitment.

**What identifies the price coefficient, and how it silently fails.** The coefficient is identified only
from **ask dispersion within event, tier and time-to-event cells**. If every seller prices at the same
markup at each time-to-event, the design is rank-deficient and the software will report a singular
Hessian. Four diagnostics must be computed and published before any coefficient: the within-cell variance
share of the ask, the R-squared of the ask on the event-tier-time dummies, the condition number, and the
count of time cells containing more than one distinct ask (`02-c` §4.4). **The data requirement is
therefore not just four fields but price dispersion among simultaneously live listings.**

**Three threats to the causal reading, with bias directions that do not net out** (`02-c` §4.3):
within-tier unobserved quality, which is unobservable because seat coordinates are absent, biases the
coefficient **toward zero**; endogenous revision, where a seller cuts after observing failure, biases it
**away from zero**; and omitting the time effect biases it **away from zero**. The net sign is unknown,
which is why the honest output is a bounded claim plus the assumption it relies on.

**Two instruments considered and their status**: the cap where it binds is viable but local, being a
regression-discontinuity-flavoured design; seller tenure is viable and fragile; and **the seller's own
purchase price must be discarded on this platform**, because transaction history is public on chain, so a
buyer can condition on the seller's cost basis and the exclusion restriction fails by design. That is
worth naming because it is the instrument an analyst would reach for first (`02-c` §4.3).

### 10.4 Demand on the primary side, which is the only identified demand object

The primary market is a demand experiment already run: a sold-out tier is censored demand, meaning
demand met or exceeded supply at that price, and an unsold tier is a point on the demand curve. That is
a Tobit with an observed censoring indicator, the benign case, and it needs no secondary data
(`01-b` §4.4(i); Tobin 1958; Conlon & Mortimer 2013 inverted). **Class B, UNVALIDATED for any functional
form.** Its three assumptions are load-bearing and two are open questions: uniform primary pricing, face
equal to the primary transaction price, and `issuedCount` meaning sold rather than minted (§21).

Two sign results are available at zero resale history and are class C by construction (`02-e` §2.4):
sold out at face implies some willingness to pay exceeds face, so the recorded markup sits at or near the
cap; not sold out at face implies the marginal buyer's willingness to pay is at or below face. The class A
support for the direction is the auction result: arbitrage profits that an auction removes are exactly
excess demand at a posted price (Budish & Bhave 2023).

### 10.5 The selection that survives every improvement to the above

Every number this programme produces is conditional on the primary price that was actually charged: the
population of tickets in the ledger is the population that bought at that price, so varying the primary
price changes who is in the ledger, and **no amount of secondary data repairs that** (`02-c` N4, §4.6).
The correct claim after the listing panel lands is therefore: *we can now price a resale ask; we still
cannot choose a primary price from data.*

---

## 11. Predictive uncertainty

**This section describes a declared width, not a predictive interval. That is the honest status and the
engine labels it that way on screen.**

### 11.1 What is computable

| Object | Method | Status |
|---|---|---|
| a band on an event's mean log price ratio | normal-normal partial pooling with a declared or constrained between-event variance, width exactly 2 x 1.645 x tau in logs | class C, **prior-predictive**, UNVALIDATED as coverage |
| a cold-start band from the literature prior | the borrowed lognormal, widened by a declared tau | class B for the prior, class D for the transfer |
| an interval for a single ticket | the event band widened by the within-event dispersion | declared, never measured |
| the sale indicator's calibration | proper scoring on the full censused population: Brier, log score, reliability curve, reliability-resolution decomposition | methods-complete, data-blocked, UNVALIDATED |
| a price-distribution coverage number | nothing | ~~**not available and must not be simulated into existence**~~ **[CORRECTION 2026-11-07T14:00Z, R2-13 — true of a price distribution and now false as written without that qualifier: `09-sim-recovery.md` reports measured coverage of the *declared band on an event's mean* (0.805 at J=2; 0.620 / 0.694 / 0.718 at the default tau against a true 0.30). That is coverage of a band on a mean under a stated generative model, class SIM, not a price-distribution coverage number and not calibration on this platform. The distinction this cell was making — that no coverage number may be *simulated into existence* for a price distribution — stands and is unchanged. See §20.6.]** |

### 11.2 The arithmetic the reader can check

A 90% band on a brand-new event's mean log ratio is the point estimate plus and minus 1.6449 times the
declared between-event standard deviation, and because the pooled-mean variance is positive this is a
**floor on the width** for a given tau, never an overstatement. Expressed as a multiplier on the point
estimate and as markup over face centred at the fitted mean of 0.261 (`02-e` CORRECTION 1):

| declared tau | 90% band in log units | as a multiplier on the estimate | as markup over face |
|---|---|---|---|
| 0.10 | +/-0.164 | x0.849 to x1.178 | +10% to +53% |
| 0.20 | +/-0.329 | x0.720 to x1.390 | -7% to +80% |
| 0.30 | +/-0.493 | x0.611 to x1.637 | -21% to +113% |
| 0.406 | +/-0.668 | x0.513 to x1.950 | -33% to +153% |

**The correction matters and is carried.** As first printed, the last row read "-49% to +95%" under a
header saying "as markup around face", which reads as a markup 49% below face: the opposite direction of
the file's own class-A inputs and of the risk the reader is being warned about. The column is a multiplier
on the estimate; the corrected absolute band is the last column (`02-e` CORRECTION 1).

### 11.3 Why conformal prediction cannot fix this, and what it does contribute

Conformal prediction is *defined* by consuming a calibration set, so with none there is no procedure
to apply. The deeper problem is that the only calibration set this market can supply is drawn from sold
tickets, and a conformal guarantee requires exchangeability between calibration and test points; an
observation conditioned on "this ticket sold" is not exchangeable with a test ticket that may not sell,
and the guarantee is void (`01-c` §8.1; Barber et al. 2023). Worse, the target is conditional and the
guarantee is marginal: a sale price does not exist for the roughly 95% of tickets that never resell, so
the population over which marginal coverage would be claimed is one in which the target is undefined for
twenty units in twenty-one. What conformal contributes is vocabulary and a costed data requirement: a
uniformly sampled scoring population, outcomes recorded on both branches, and a calibration cell size
that grows as the inverse of the miscoverage level (`01-c` §8.2). That is a schema decision that must be
made before launch because it cannot be reconstructed afterwards.

### 11.4 The substitutes in use

Three, in order of honesty (`01-c` §8.3): empirical quantiles of the realised price ratio, scoped
explicitly to transactions, which is cheap, exact and explicitly conditional; binned empirical quantiles
of the hedonic's fitted value, because exact quantile regression is a linear program and no solver is
permitted, so the binning is exact within the bin and cruder in resolution, and that is stated; and proper
scoring with a reliability curve for the sale indicator, which is the one calibration task fully available
today because the population is complete.

---

## 12. Primary-market optimisation

### 12.1 The objective

For one event with tiers `g = 1..K`, `N_g` units per tier, price vector `p`, expected net economic value
is the sum over tiers of offered units times the expected sale probability times the margin a sale is
worth relative to the empty seat it replaces, net of the baseline cost of offering every seat, plus a
resale royalty term, minus fixed cost (`02-d` §1.3):

    Pi(p) = sum_g N_g [ q_g(p) ( m_g(p_g) + u_g ) - u_g ] + rho E[T(p)] - F

with `q_g` the **truncated** demand (expected sales divided by offered units, so it is capped at one),
`m_g` the organiser's net receipt per unit sold, `u_g` the cost of an offered-but-unsold unit, `T` resale
turnover and `F` fixed cost. `F` vanishes from the argmax; so does discounting, because it multiplies
every candidate equally (`02-d` §1.4).

**Which terms are estimable and which are configuration** (`02-d` §1.4, §2.6): the sale probability as a
function of price is not identified; the demand level is not identified; the fee stack, the ancillary
margin and the empty-seat cost are configuration; the resale royalty is bounded at about 1.4% of primary
revenue on the most resale-active sample in the literature and is retained for completeness; and the
"share of resale margin the organiser can capture" term **does not exist**, for the reason in §12.2.

### 12.2 The fee result, which is the sharpest exact algebra in the programme

Let `phi` and `f` be the organiser-side ad valorem rate and per-unit fee, `beta` and `b` the buyer-side
ones, `a` the ancillary margin per attendee, `u` the empty-seat cost, and `P` the buyer's all-in price.
Then the entire fee stack, the ancillary and the empty-seat cost enter the recommended **all-in** price
through one scalar:

    c** = b + (1 + beta)( f - a - u ) / (1 - phi)

and the first-order condition is the Lerner condition against that wedge, `(P - c**)/P = 1/epsilon(P)`,
equivalently `P = c** epsilon / (epsilon - 1)` (`02-d` (WEDGE), (FOC-2)). Four consequences, each exact
for any demand function (`02-d` §2.3):

1. **Ad valorem fees are neutral for the optimum.** A proportional fee rescales the objective by a
   positive constant and cannot move its argmax (**class C**; class B support from the incidence
   literature, Delipalla & Keen 1992).
2. **Per-unit fees are not neutral, and they act as marginal cost**, placing the optimum at a higher
   elasticity point (**class C**; Weyl & Fabinger 2013).
3. **The empty-seat cost has the opposite sign to the fee and is what makes the model non-degenerate.**
   With `u` only, the organiser accepts an inelastic price point in exchange for filling seats; drop it
   and a sold-out event with no per-unit fee has no interior optimum at all.
4. **Refunds and chargebacks behave like a per-unit fee** and shift the optimum up (**class C**).

**What this means for the settlement field the programme wants.** A field recording only the *percentage*
of the fee buys nothing for the price recommendation, because it is neutral. The field that matters is the
one that reveals the **fixed per-unit component**. Two numbers per settled sale do the whole job: net to
organiser, and buyer total (`02-d` §2.6). That is the opposite of what a "fee field" is usually specified
to contain.

### 12.3 The cap does not constrain the organiser, and it does constrain the record

Three results (`02-d` §2.5), all class C, all conditional on the cap being proportional:

1. **Scale invariance.** The feasible resale band `[p, p(1+c)]` translates with the decision, so the
   seller's problem is where to sit in the willingness-to-pay distribution, not how much of the ceiling to
   allow.
2. **A proportional cap is not a constraint on the organiser.** Raising the price by a factor raises the
   ceiling by the same factor, so the reseller can still resell at the same proportional markup. **The cap
   binds the reseller, not the organiser.**
3. **The resale market adds no separate cross-price term**, because the buyer's outside option is a
   function of the primary price, so substitution is already inside the primary demand curve and the
   elasticity needed is the residual one.

**This is deliberately paired with the opposite-looking statement in §3.3 and both are true** (`02-b` §3.5):
the cap does not constrain the organiser's price, and it does constrain the record of what resellers got.
Scale invariance is a statement about shares, not about truncation: the share of sales at the ceiling is
invariant to the primary price, which is exactly why the truncation is permanent and why the engine cannot
price its way out of a censored sample. The definitions differ; a statement that the cap removes no
primary price from the feasible set says nothing about whether the ceiling truncates the distribution of
resale prices above it.

**The validity condition, stated because a definition change would void this section**: a fixed-absolute
cap, such as a nominal dollar ceiling, would break all three results and force an extra term into the
objective equal to the shadow value of the rationed quantity behind the ceiling (`02-d` §2.5).

**[CORRECTION 2026-11-07T15:00Z — D7: the cap decides the split, not who receives the premium.]** The three
results above are statements about the organiser's feasible set and about what enters the objective, and they
stand. What must not be attached to them is the sentence "the resale premium is capturable entirely through
the primary price": it is withdrawn (`11-cap-capture-check.md` §9, verdict STANDS-WITH-NARROWING). A ticket
that settles at the ceiling sells for `p(1+c)`, which is the organiser's price `p` plus the reseller's margin
`pc`, in the fixed ratio `1 : c` that no primary price changes: raising `p` scales both parts and transfers
neither. The organiser keeps a larger share of the resale price only by a tighter cap, and takes more money
only by a higher price, which demand and its own uncertainty bound. Past `p = V/(1+c)` the cap is slack, the
resale price is pinned at the market value `V`, and further increases in `p` transfer the reseller's margin
one for one on however many tickets still sell at that price; that is ordinary pricing to the market value,
not a cap effect. The organiser's revenue is `p·S(p)` throughout and the premium is never additive to it.
Class C. **The test that would settle capture** is a scale test on uncapped or slack-cap events at two or
more face levels, with a pre-declared rule (`β = 1` nominal capture, `β = 0` no capture beyond value over
`1 + c`), and it needs more events than the platform has (`11` §5, §7, §9). **Scope conditions, which void
the result**: a cap that is absolute rather than proportional; a constraint on face that binds below the
unconstrained optimum; and any record already produced under a fixed face, where the ceiling is an absolute
number (`11` §4, §8).**

### 12.4 The recommendation, which is a boundary and a set

Three cases (`02-d` §2.4):

| Case | Condition | Optimum |
|---|---|---|
| interior | positive wedge, elasticity above one | the Lerner price over the wedge |
| sell-through boundary | non-positive wedge, or elasticity at or below one, or the interior price below the price at which the house fills | the highest all-in price at which expected sell-through still meets the organiser's floor |
| degenerate | `q = 1` over the candidate range and a zero wedge | no maximum exists; keep raising until the boundary |

The degenerate case is not a curiosity: it describes a sold-out event with no per-unit fee, and the best
concert sample in the field has mean capacity utilisation of 0.99 across 56 events (**class A**, Leslie &
Sorensen, read directly in `02-d`). Because the objective is not guaranteed unimodal, the implementation
rule is: **maximise on a price grid and use the first-order condition only to interpret and to compute
directions. Never invert an elasticity to get a price and report it.**

With inelastic demand at observed prices and a small wedge, the interior price falls below the fill price,
so the boundary governs. The elasticity's role is to say how far above the boundary you can go. Exact
arithmetic from the formula, no data:

| elasticity | 1.2 | 1.5 | 2.0 | 3.0 | 5.0 |
|---|---|---|---|---|---|
| price over wedge | 6.00 | 3.00 | 2.00 | 1.50 | 1.25 |

So if the effective per-ticket wedge is 5% of face and the elasticity is 1.5, the interior optimum is 15%
of face, which is far below any observed face value, and the boundary rule applies. **The table is a
diagnostic on the model, not on a market.**

### 12.5 Sensitivity, with signs derived rather than felt

| Parameter | Sign on the recommended price | Reason | What would supply it |
|---|---|---|---|
| own-price elasticity | negative | the Lerner formula, decreasing in elasticity for a positive wedge | a price experiment, and nothing else |
| per-unit fee | positive | adds to the wedge as marginal cost; pass-through is partial | a settlement field |
| organiser ad valorem rate | zero for the all-in optimum, negative on profit | multiplicative wedge, cancels | a settlement field |
| buyer ad valorem rate | zero for the all-in optimum, negative on the posted price | pure rescaling | nothing: post-2025 US the posted price is the total |
| buyer per-unit fee | positive, one-for-one | enters the wedge additively | a settlement field |
| ancillary margin | negative | a filled seat is worth more than the ticket, so buy volume with a lower price | the organiser's accounts |
| empty-seat cost | negative, larger effect | the cost that makes the organiser trade margin for sell-through | the organiser's accounts |
| cap in basis points | zero directly; positive if the resale option has value to the buyer | the cap is proportional; the second channel is a willingness-to-pay effect | the contract field; the second channel is class D |
| demand uncertainty | ambiguous | two opposing effects, derived in §13.2 | nothing passive |
| sell-through floor | negative | a tighter floor forces a lower price | organiser policy |

### 12.6 The measurement that would make this an interior optimum

One design (`02-d` §3.6): randomise the **face value** of a tier across otherwise comparable events, or
randomise the ratio of two tiers' face values within an event holding total supply fixed, and observe
sell-through at a fixed horizon. Estimate the elasticity of log sell-through on log price with event fixed
effects and, in the within-event arm, tier fixed effects. Three reasons this design and not another: it is
the only one that moves price exogenously; it is legal and cheap because the organiser sets prices
anyway; and because the cap is proportional, randomising the price randomises the resale ceiling too, so
the same experiment identifies the cap's effect on demand as a free by-product.
**[MARKED 2026-11-07T15:00Z — the last clause is backwards and is withdrawn (`11-cap-capture-check.md` §8,
A9).** Proportionality makes the cap and the price collinear, so this design cannot separate the cap's effect
from the price effect; it estimates a mixture. Identifying the cap's effect needs variation in the cap at a
fixed price, which is cross-event and confounded. The test that settles capture is the scale test in §20.3
(`11` §7).]**

**Sizing is given as a formula and not a number**, because it is a money question: with `G` events per arm
the variance of the arm mean is the between plus within-event variance over `G`, so detecting a
proportional change `delta` needs `G` of order `2 (z_alpha + z_beta)^2 CV^2 / delta^2` events per arm,
where `CV` is the coefficient of variation of event-level sell-through. `CV` is not in this dataset and is
not guessed; the operator can read it off the first twenty events. **This is the single experiment that
would change the engine's headline**, and it costs revenue, so it is his decision (`02-d` §3.6;
`03-a` §5).

---

## 13. Risk methodology

**Thin, and it is the thinnest section in this document. The reason is not that the mathematics is
missing, it is that the inputs are.** A risk functional needs a distribution of profit conditional on a
price, which needs the demand response, which is not identified. What exists is one coherent functional,
two derived signs, and one one-sided bound.

### 13.1 The functional

Mean-CVaR: maximise `(1 - lambda) E[Pi] + lambda CVaR_alpha(Pi)`. CVaR is the right choice because it is
coherent in the Artzner sense (subadditive, monotone, positively homogeneous, translation invariant),
whereas variance is not, and because it penalises exactly the risk this business carries: unsold
inventory at the deadline. **For a finite scenario set with equal probabilities it reduces to a sort plus
a partial mean** of the worst `alpha` fraction, which is pure standard library and needs no solver
(**class C**; Artzner et al. 1999; Rockafellar & Uryasev 2000 for the linear-programming form, which is
specified and not implemented because the one-dimensional grid search is exact to grid resolution).

Mean-variance was considered and rejected for two reasons, neither of which is implementability: it
penalises upside as well as downside, which is the wrong attitude for a decision whose point is to move
the upper quantiles; and its scale grows with the square of the number of units, so the risk-aversion
parameter has to be re-tuned per event size, across events selling 3,169 to 34,844 primary tickets in the
sample where that range is reported (**class A**, Leslie & Sorensen).

### 13.2 The two opposing effects of demand uncertainty, derived

**(a) Truncation pushes the optimum up.** Adding uncertainty lowers expected sell-through and flattens its
slope, because truncation at capacity makes the quantity response small exactly where the venue is near to
filling. At the no-uncertainty optimum the derivative of profit under uncertainty is positive, so the
price rises. The economic reading: when the house will fill anyway, the marginal unit costs nothing to
price up. **Class C.**

**(b) Downside-risk aversion pushes the optimum down, conditionally.** In the adverse demand state,
revenue is price times quantity and its derivative in price is quantity times one minus the elasticity,
so a penalty on the bad tail lowers the price **exactly when the adverse-state demand is elastic** and has
no effect when it is inelastic. The sign of the risk correction therefore depends on the elasticity in the
state that hurts, which is unmeasured here. **Class C, and the honest form is that the correction has no
single sign.**

### 13.3 What the engine actually does about risk

**Very little, and it says so.** The implemented optimiser returns the boundary price, or the cap floor on
a binding event, with an exact consequence table (net revenue and required sell-through at a candidate
price) and four refusals. It has no elasticity, no sell-through floor, no grid and no risk functional:
the recommended price is the observed resale level or the cap floor, and the console labels it
"a bound, not an optimum" (`07-engine-review.md` §2.7). The mean-CVaR optimiser exists in the model
registry as a SHIP row and is not built.

### 13.4 What would make this section non-thin, in order

1. **The settlement fields**, which turn the wedge from an assumption into a measurement and are the
   largest unquantified term in every report (`02-d` §2.6).
2. **The randomised face experiment**, which identifies the elasticity and therefore the sign of the risk
   correction (§12.6).
3. **A hundred out-of-sample outcomes**, because a 5% tail average needs at least five observations in the
   tail before it is a tail average rather than its own worst point, which is a floor derived in
   `06-validation-protocol.md` §2.3 and not a power calculation.

Until then the risk statement is: **the recorded markup is a floor on value where the cap binds, the
primary price is a boundary rather than an optimum, and the direction of any risk correction is
unresolved.** No number in this section may be quoted as a risk estimate.

---

## 14. Data architecture

### 14.1 The observation set, as the platform emits it

`lib/types.ts` in `/home/friend/ticketing-frontend` is the wire contract and the authority. For one
ticket the platform yields:

- `LedgerEntry[]`: kind in {issue, sale, transfer, redeem, revoke}, from and to wallet, price in lamports
  (null when unpriced), markup in basis points (null when unpriced), signature, slot, timestamp (ISO-8601
  UTC).
- `Ticket`: face value in lamports, tier id, mint address, owner wallet, issuee wallet, status in {valid,
  listed, redeemed, revoked}, transfer-restricted flag, issue time, redemption time.
- `Event`: start and end time, venue, city, organiser, status, tiers (face, total supply, issued count),
  resale enabled, resale cap in basis points, verified-wallet requirement.
- `ResaleStats` and `EventAnalytics`: derived aggregates, with **no stated as-of window**.

Nine endpoints, seven reads and two wallet-verification POSTs, and **no price-mutation endpoint**, which
is why the primary price is a once-only decision (`02-d` §1.1, MEASURED).

### 14.2 The four gaps, which shape everything

| Gap | What is absent, verified against the contract | Consequence |
|---|---|---|
| **1. No listing exposure** | no listing start time, no ask, no revision trail, no withdrawal, no view count. `Ticket.status = listed` is a state, not a history | the price response is not identified; the sale count is a numerator for the wrong process |
| **2. A policy price ceiling** | `resalePriceCapBps` truncates the observed markup from above, with rationing behind the ceiling | the top of the value distribution is unsampled, and the bias is largest where demand is strongest |
| **3. No seat coordinates** | `Ticket` carries tier id, serial and mint; no section, row or seat | the strongest within-event price axis is unexpressible; every seat-quality claim is class D |
| **4. No fee, royalty or settlement field** | money appears only as price and markup in basis points | the net objective and the primary optimum need the fee stack as a parameter, and the per-unit component is the one that matters |

Two smaller ones, recorded for completeness: primary inventory is a snapshot with no time series, so
sell-through *velocity* is not observable; and `Event.status` transitions are not timestamped, so on-sale
start, sell-out and hold-back-release times are unknown.

**A disagreement on Gap 1's diagnosis is live and is not resolved here.** The Phase 0 audit calls the
sale count "a numerator with no denominator". `01-b` §5.1 says the denominator is present, because every
ticket has an `issue` row and a known life, and that the unobserved object is the **ask of the risk set**;
`02-c` §2.1 refines it further, to a composite intensity marginalised over the unrecorded offering state.
The audit's severity is too high for the baseline intensity, which is identified and buildable, and
correct for the price response. **The four-field fix is identical under all three readings**, so the
decision stands; only the diagnosis differs. This is recorded as a contradiction in
`A-research-ledger.md` (C1 and C2) and is one of the places where that file's own rule (record conflicts,
do not resolve them silently) is itself only partly obeyed, since `F` D3 carries the audit's version as
settled.

### 14.3 The data-requirements specification, ordered by what it buys

This is the programme's most valuable output for whoever operates the platform. The ordering is by
marginal identification bought per unit of engineering, not by how natural the field looks.

**1. The four-field listing panel: `{listPriceLamports, listedAt, delistedAt, delistReason}`.** One row per
listing episode, with a price revision being a new episode. `delistReason` in {sold, withdrawn, expired,
cap_blocked}. This converts the sale hazard from unidentifiable to a standard time-varying-covariate
survival problem. `listPriceLamports` is worth more than the other three combined, because it is the only
field that puts a price into the risk set. **The content requirement matters as much as the field**: it
must be recorded for listings that never sell and per revision, or the new schema reproduces today's
defect. `cap_blocked` is the most valuable enum value, because it is the only observation that separates
"nobody wanted it" from "everybody wanted it and the ceiling rationed them". `delistedAt` and `listedAt`
are the cheapest two and the least urgent, because polling `Ticket.status` recovers them to the poll
interval (`02-c` §10; `02-b` §4).

**2. Settlement: `netToOrganizerLamports` and `buyerTotalLamports` on every settled primary sale.** These
turn the wedge from an assumption into a measurement and remove the largest unquantified term in every
report. A field that records only the *percentage* fee buys nothing for the price recommendation, because
it is neutral (`02-d` §2.6).

**3. Polling `Ticket.status` from day one.** It recovers approximate listing spells, the depth covariate
and part of the supply margin, and it never recovers the ask. It is the one data action with a deadline,
because **unrecorded exposure is lost permanently**: every day without polling is exposure that cannot be
reconstructed (`02-c` §7.4).

**4. A primary inventory time series** with on-sale, sell-out and hold-back-release timestamps. This turns
the sell-through bracket from one observation per tier into a booking curve, and it is the only route to
the primary question that does not require an experiment (`02-c` §10 item 6).

**5. Seat coordinates.** Second-order for the base rate and first-order for the price response, because
within-tier quality is the main confounder of the price coefficient (`02-c` §10 item 8).

**6. A logged pricing-decision record**: for each tier and each price change, the timestamp, the price and
the rule or propensity that chose it. Cheap to record, and the only thing that would ever make
counterfactual evaluation possible (`01-c` §6).

**7. Any record of the buy side: bids, offers, views, searches.** Every demand statement in this programme
rests on assumption. This is the largest absent observation and no econometric adjustment substitutes for
it (`01-b` §6 item 3).

**8. Fee, royalty and net-to-seller figures**, which the operator can supply today without any schema
change (`F` D4).

### 14.4 What the engine consumes and produces

The contract is a read-only view of the record; the engine's output is a forecast, and **none of the four
required outputs has a type in the contract or an endpoint in `API_CONTRACT.md`** (`CONTRACT-MAP.md` §6).
The seam for it exists in `ticketpath/adapters/pricing_model_adapter.py`: request carries ticket, event,
tier, face, cut instant; response carries expected resale, sale probability, recommended primary price,
horizon, model version and a basis naming the record the number came from. There is deliberately no
endpoint for it, because inventing one would put a non-contract route on a consumer's path; the console
at `/` is where the output is read.

The bridge to the frontend is one environment variable, `NEXT_PUBLIC_API_BASE_URL`, and it is the
operator's to set. Nothing in that tree was edited by this programme (`docs/BACKEND.md`).

### 14.5 Contract conformance

The contract is encoded **in a test**, one declarative table per type, and the test does not import the
backend's models, because a test that imports the thing it tests proves that the code agrees with itself
(`CONTRACT-CONFORMANCE.md` §1). Per route it checks structure (every declared field present, no field the
contract does not define, JSON integers for money, base58 addresses that decode to 32 bytes, ISO-8601 UTC
timestamps) and semantics (markup against the ticket's own tier face, the stats block recomputed by the
contract's own rules, `transferCount` excluding issue and redeem, event totals equal to the sum of their
tiers, analytics recomputed per UTC day, markup buckets checked in order with bounds, cursor pagination
walking the collection exactly once, detail routes 404 rather than 200-with-null, and the frozen
verification message rebuilt and signed with a key generated in the test).

**Result: eight conformant, one drift, one extra route, zero missing.** The drift was in the analytics
endpoint and was closed on 2026-11-07T11:31Z (`CONTRACT-CONFORMANCE.md` §10); `/health` is ours and is not
in the contract. The verification path is exercised for real: a signature over the contract's own bytes
verifies, is single use, and cannot cross wallets.

### 14.6 The fixture, and the rule that keeps it out of every result

`fixtures/synthetic_store.json` is generated by `tools/build_fixture_store.py`, seed 20261107, and holds
**8 events, 76 tickets and 147 ledger rows** (76 issue, 61 sale, 8 redeem, 2 transfer), sha256
`15e6f66...9fbfa`; `--check` reports it matches a fresh build exactly. It exists to exercise code paths,
schemas, arithmetic and rendering. **It may never enter an estimation, a validation claim or a result**,
and a test fails if any module names the frontend's mock directory (`00-data-situation.md` §2; `AGENTS.md`).

Two distinct fixture sets exist and must not be confused: this repository's generator, and
`../ticketing-frontend/lib/mock/` (6 events, 128 tickets, 253 ledger rows), which is synthetic on three
independent checks and is barred from estimation for the same reason. The frontend's mints do not decode
to 32 bytes, which a devnet `getAccountInfo` call returns as `WrongSize`.

**One record row is stale.** `00-data-situation.md` §1 states that this repository was not a git
repository and held two files at audit time. It now holds code, records, tests and a generator. The
observation set and the four gaps are unaffected; the repo-state row is a snapshot of 08:40Z.

### 14.7 The on-chain design, and what it does and does not guarantee

None of this is deployed. There is no program id, no compiled artefact, no cluster and no signature
(`/health` reports `programDeployed: false`, `programId: null`). What exists is a design: a Token-2022
mint per ticket carrying a transfer hook that points at the program, a per-ticket record account and an
append-only record per custody change, with the resale cap checked in the program before the transfer
(`F` D6; `docs/ON-CHAIN-DESIGN.md`).

The claim narrows to one checkable sentence: **the ticket cannot move without the program recording the
hop, and the program will not record a price over the cap.** Everything it does not stop is written down
rather than implied (`F` D6): side payments off-chain, so a recorded markup is a lower bound and the
observed distribution is squeezed from both ends; one person with many wallets, so no bot-resistance claim
may be made in any artefact; a compromised organiser key, which can issue, verify and revoke but cannot
raise a cap, change a face, move a fan's ticket or rewrite a hop, and needs a multisig on day one; a
compromised verifier key; and a mint created without the hook by anyone else, which is the honest weakness
of every hook design. A PDA escrow with a listing surface was costed at an estimated 10 to 14 hours against
3 to 5 for the record plus hook, and rejected because it does not close the side-payment hole: a pair who
settle off-chain can route a face-value sale through an escrow and pay the rest in cash.

---

## 15. Validation framework

### 15.1 The blunt statement

> **Nothing about ticket prices, ticket sales, ticket values, sale probabilities or primary-price optima can
> be validated today.** Not approximately, not provisionally. The words validated, verified, accuracy,
> coverage, calibration and out of sample have no referent on this machine for any quantity the engine
> exists to produce (`06-validation-protocol.md` §1.1).

Two things are testable now, and they are different in kind. **Estimator properties under stated
generative assumptions** (SIM) establish internal coherence and say nothing about ticket markets.
**Internal correctness** establishes that the engine is what it says it is: contract conformance,
arithmetic invariants, refusal behaviour, label discipline. A suite that is green on the second is a claim
about engineering; it must never be described as though it were a claim about pricing.

### 15.2 The protocol for when data exists

One fold is one **event boundary**, with a single cut instant, because the product's decision is per event
(`06-validation-protocol.md` §2.1). Five rules make the cut real: it is a value written into the fold
record, not a query; truncation happens once at the top before any aggregation, on the production code
path; the cut is applied on the row's own clock with null-slot rows counted; a cut inside an event is
legitimate and the fold record must say which variant produced the number; and the fold record carries the
count of rows at exactly the cut instant, because timestamps can tie.

### 15.3 Metrics, with pass conditions pre-registered

| ID | Metric | Pass condition (PLANNED, none run) | What it cannot show |
|---|---|---|---|
| M1 | calibration of the value band: share of out-of-sample scored sales inside the band printed immediately before the sale | empirical coverage in [0.87, 0.93] for a declared 90% band, **per horizon band and per regime, never pooled across regimes** | whether the band is right on a capped-and-binding regime, where there is no upper end to cover |
| M2 | M1 as a function of the event count, over the ladder 1, 3, 5, 9, 20 | coverage in [0.87, 0.93] at every count **and** width strictly decreasing in the count | whether the between-event variance is right |
| M3 | the boundary rule's realised sell-through and its floor violations | zero floor violations in a forward extraction at the same cap, with the count printed either way; and the required-sell-through identity exact to the lamport | causality under any amount of data, without an adoption record |
| M4 | downside: the 5% CVaR of the shortfall against the printed recommendation | reported with its tail count and its `n`, and the risk-adjusted optimiser preferred only if its CVaR is lower at the same mean by more than per-event dispersion | a coherent risk preference; the parameters are the operator's |

**Resolution floors, derived rather than asserted** (`06-validation-protocol.md` §2.3): about **139**
out-of-sample sales per horizon band for a coverage estimate whose 95% interval is narrower than plus or
minus 0.05 at nominal 0.9; the same 139 at the smallest event count in the ladder, which is what makes the
cold-start study expensive; **one** well-observed event for a floor-violation count; about **100**
out-of-sample outcomes for a 5% tail average to contain five observations; **3** events for any holdout and
about **9** for the between-event variance; and about **30** sales per band for a skill score.

### 15.4 Baselines, which are mandatory floors even though they are rejected as products

**B0 face value** (the claim that the market pays a premium at all, and the null the literature supplies);
**B1 population mean** (the claim that any covariate adds anything); **B2 last observed markup**, the
martingale, and the binding baseline because `02-a` pre-registers shipping it if the fitted path does not
beat it; **B3 fixed markup rule** (the claim that the model's time variation is worth anything). Two
conditions make the comparison real: same folds, same cut, same population; and the baseline's own
parameters frozen per fold, so that B1's mean must be the fit-window mean or B1 is a cheat.

### 15.5 Ablations, and the one that is most misread

Eight, with the protocol stated once (`06-validation-protocol.md` §2.5): remove the component, keep folds,
cut, population, hyperparameter clock and metric identical, score, and report the difference with its
per-event dispersion; **a component that does not improve the out-of-sample score by more than that
dispersion is removed, and removing it is a result rather than a defeat.** The one exception is a
component whose purpose is a refusal (the cap guard, the cold-start branch, the fee gate): those are
not scored, they are tested for being switched on, because a guard that pays for itself in points is not
a guard.

The misread one is the interaction ablation: within an event the three clocks are affine in each other,
so an interaction in time is partly collinear with the level and its removal will always look harmful in
sample. **The only admissible reading is out of sample against the martingale.**

### 15.6 The simulation study specification, which is PLANNED and not run

Eight studies, G1 to G8, each with its data-generating process written as the estimator's own assumptions
and its pass condition asserted in the harness before the run (`06-validation-protocol.md` §3.2). The
first six cover value-level recovery, cold-start band coverage and degradation, behaviour as the cap binds,
intensity recovery with competing risks and separation, the path guard, and optimiser identities.

The seventh is the one that matters most, and it is the harness testing itself: inject a deliberately
leaked feature, which peeks at the whole record, and require the prequential harness to **detect** it. If
the leak is not detected, the harness is broken and every score it has ever produced is void. A protocol
that cannot detect a known leak is not a protocol.

The eighth, G8, settles the cheapest possible labelling failure: measure whether the printed band covers
the event's mean or the next sale, and require the sentence in the label registry to match the object the
higher coverage corresponds to. That is settleable before any data exists, and it is the version of the
labelling defect the engine review actually found (§17.4).

**What the study must never produce**: a number described as accuracy, expected error on tickets,
expected lift, or calibration on this market. A SIM study cannot fail for the reason the engine will
actually fail, because the author wrote the generating process. That is why the reviewer of a SIM study
must not have written it.

### 15.7 The failure-mode registry, and the adversarial protocol

`06-validation-protocol.md` §4 registers the failure modes with their source, and §4.3 records where they
came from: this programme's own corrections, not a hypothetical. Sixteen defects were corrected in one
pass across ten files (`CORRECTIONS-APPLIED.md`), and they are the evidence base.

The review protocol (`06` §5): a reviewer who did not build the thing, with the four classes of internal
correctness as the minimum scope, the eight questions that must be answered before the work is trusted,
a verdict vocabulary that contains the evidence for the verdict, and a verifier for the reviewer. The
programme's version of this has already run three times (a ledger verification, a verification round, an
adversarial review of Phase 1, and an independent engine review), and in every case it found real defects,
including one it wrongly attributed and had to withdraw (`A-research-ledger.md`, the Aigner correction).

---

## 16. Integrated mathematical model

### 16.1 Seven subproblems, and the honest one-line answer for each

| # | Subproblem | Formulation that serves it | Identified | Bounded | Not identified |
|---|---|---|---|---|---|
| P1 | value level | censored hedonic, with the repeat-sales index as its check and the cap bound as its floor | a quality-adjusted relative price for every ticket, including never-traded ones | the level, one-sided from the cap mass and from primary sell-through | the absolute level; between trades; seller reservation; buyer willingness to pay; anything inside the censored region |
| P2 | price path | deadline-convex path, local-level state space, martingale fallback | curvature and per-event deviations | the slope, as a bracket over a declared normalisation | the linear trend; the path of a ticket that never resold; a rate or half-life |
| P3 | sale intensity | composite intensity; mark-time intensity; listing-episode hazard behind the four fields | the composite rate, its incidence, the never-transacted fraction, the realised price-time distribution | the hazard given the seller's own ask, once the fields exist | the price derivative; any counterfactual sale probability at a chosen price; the offering split; the ask distribution |
| P4 | elasticity | primary sell-through bracket | the **sign** of excess demand at face, per tier | a one-sided bracket at each observed face; elasticity at or below one near observed prices | the elasticity as a number; any functional form; cross-price effects; the response under a cap |
| P5 | primary optimum | fee wedge and first-order condition; grid optimiser with the boundary rule; mean-CVaR; reserve-price surface | the objective's **structure** | the recommendation as a **set** plus the sell-through boundary | a point optimum; the primary demand level; the sign of the risk correction; dynamic pricing |
| P6 | uncertainty | prequential proper scoring; empirical quantile band; mixture quantiles at cold start | calibration for the sale indicator on the full population | any price interval, as empirical residual quantiles scoped to transactions | coverage of any price-distribution interval; conformal guarantees; portfolio risk |
| P7 | cold start | normal-normal partial pooling; gamma-Poisson exposure update | the prior-predictive band and its width; exact cap and fee arithmetic; the handover count | the between-event variance, above two events and poorly even there | a point value; the level; the between-event variance at one event; whether the chosen face is optimal |

**The one-sentence summary**: P1 is a ratio with a one-sided floor, P2 is curvature, P3 is a rate with no
price in it, P4 is a sign, P5 is a set, P6 is a scoring rule for one indicator and empirical quantiles for
the rest, P7 is a declared width. **Nothing here is a point price and nothing here is a demand curve**, and
that is the identification result rather than a shortfall of effort (`B-mathematical-kb.md` §1).

### 16.2 The eighteen formulations, and their roles

`B-mathematical-kb.md` records 18 numbered formulations plus two sub-formulations of the cold-start model,
20 entries, each with its sources, its assumptions, its parameter requirements and its failure condition.
`D-model-registry.md` records 56 models with a role for each: **13 SHIP, 3 SHIP-BEHIND-ADAPTER, 14
SPECIFIED-NOT-IMPLEMENTED, 26 REJECTED.** The SHIP set is: the censored hedonic, the repeat-sales index,
the cold-start band, the cap-bound estimator, the mark-time intensity, the deadline-convex path, the
martingale anchor, the composite intensity, the gamma-Poisson cold-start intensity, the separation guard,
prequential scoring, the grid optimiser with the fee wedge, and mean-CVaR. **SHIP does not mean "produces
a number"**: with an empty ledger every one of them must refuse rather than guess.

### 16.3 How the pieces compose

    observation set (truncated at a cut, slot-ordered)
        |
        +-- price features ----------> regime classification (capped and binding / capped no mass / uncapped / no resale)
        |                                  |
        |                                  +--> cap floor ................ where the cap binds, the only exact value statement
        |                                  +--> band (declared width) .... where it does not
        |
        +-- censored hedonic (F3) ----> relative price + residuals -> interval; and the state for certainty equivalence
        +-- repeat-sales index (F2) --> price CHANGE only, as the independent check on F3's time effects
        +-- path model (F5) ----------> curvature; bracket over the declared normalisation; martingale fallback
        |        \
        |         +--> cap-binding window as a function of the candidate primary price (one root-find per price)
        |
        +-- composite intensity (F7) -> the transaction rate, its incidence, competing risks, the cure fraction
        +-- mark-time intensity (F8) -> the realised price-time distribution, a descriptive object
        |
        +-- primary sell-through (F10) -> a sign and a one-sided bracket on demand at each observed face
        |                                 \
        |                                  +--> the boundary price, with the fee wedge (F11, F12)
        |
        +-- cold-start band (F17) ----> a declared width around a pooled mean; the handover count
        +-- gamma-Poisson update (F18)-> the zero is evidence: the cold-start intensity shrinks with exposure

**Shared parameters, which is why the components are not independent** (`B` §9.2): the between-event
variance appears in the cold-start band, the hierarchy and the frailty; the within-event dispersion
appears in the band, the interval and the handover count; and the cap appears as an observation rule in
the hedonic, as a parameter in the hazard, and as a constraint in the optimiser. **Competing formulations**
(`B` §9.3): the deadline-convex path competes with the state-space model for the same target, and the
censored hedonic competes with the repeat-sales index, which is why they are run as checks on each other
rather than merged.

### 16.4 The one relationship that decides the architecture

Three of the formulations are expressed in units of face, and face is the decision variable. Therefore a
model whose output is a log ratio cannot be evaluated at a different primary price, because changing the
price changes its own denominator; the curvature can be estimated in either normalisation, but **the level
must be converted to money before the cap is applied**; and **the primary price cannot come from the resale
model at all**. The only level-bearing demand object is the primary sell-through bracket, which is
censored, one-sided and gated on what `issuedCount` means.

That yields the sentence the deliverable must carry, and it is the reason §12 and §9 are separate sections:
**the resale engine prices the resale ask; the primary decision needs a primary demand object, and before
any resale the only one in the schema gives a sign and not a level** (`B-mathematical-kb.md` §9.4,
class C).

### 16.5 Computational feasibility under the one-package constraint

D2 is a hard constraint verified on this machine: Python 3.12 standard library only, no numpy, scipy,
pandas, sklearn or statsmodels, no linear-programming solver, no MCMC library. The relevant question is
not whether the linear algebra is possible but whether it is honest at the dimension it actually has
(`B` §10), and the answer is structural rather than lucky: **none of the 18 formulations needs a dense
solve at a dimension that grows with the data.** Three qualifications: the listing-episode hazard is
data-gated rather than computation-gated, since its code is the same solver as the composite intensity; the
reserve-price surface is implementable in discrete form, and the continuous-time partial differential
equation is specified and not needed, because the discrete dynamic program *is* its numerical solution;
and four library-needing variants inside otherwise-implementable formulations are named and not attempted
(the Rockafellar-Uryasev linear program inside CVaR, replaced exactly by a grid to grid resolution; exact
quantile regression, replaced by iterative reweighted least squares and labelled an approximation; HMC,
replaced by the empirical-Bayes closed form and a grid; and non-conjugate random-effects quadrature).

---

## 17. Software architecture

**Everything in this section was verified by opening the file or running the command, at
2026-11-07T12:45Z. The tree was being edited throughout the assembly of this document, so the numbers
carry their instant. Where the running code and the independent review disagree, both are here.**

### 17.1 The shape, and the one rule it is built around

The engine is a plain Python 3.12 standard-library package, about 6,088 lines across 41 files (35 of them
substantive modules), with no runtime dependency, no build step and no JavaScript. `pyproject.toml` declares
`dependencies = []` and carries no build-system table, deliberately: nothing is installed, because nothing is
built.

| Layer | Modules (observed line counts) | Responsibility |
|---|---|---|
| entry | `server.py` (385) | HTTP routing only. 9 contract routes plus `/health` in `ROUTES`; the console at `/` is served **outside** the route table on purpose, so `/health.contract.routesImplemented` stays at 10 and the console is not counted as a contract endpoint |
| decision | `orchestrator.py` (579) | routes to adapters and core, decides, does not calculate. Every number arrives computed by `core/` |
| contract surface | `api/` 6 modules: events, tickets, analytics, wallets, health, guidance (500) | input validation and serialisation, one module per contract area, every leaf labelled |
| pure computation | `core/` 19 files, largest `value_band.py` (467), `labels.py` (451), `price_features.py` (388) | pure functions: features at a mandatory cut, regimes, band, path, intensity, optimum, markup, stats, analytics, pagination, base58, ed25519, verification message |
| seams | `adapters/` 4 modules: `ledger_adapter.py` (308), `pricing_model_adapter.py` (125), `chain_client.py` (111), `rpc_adapter.py` (73) | the only path to ledger data, the pricing seam, the quote hash and artefact verification, and a read-only RPC adapter that reports no deployment |
| console | `console/` 3 modules: `blocks.py` (404), `page.py` (295), `units.py` (151) | server-rendered HTML: decision, market, refusals, design panel, simulated state machine, chain slot |
| design mirror | `onchain/sim.py` (159) | a Python mirror of the on-chain state machine, proving arithmetic and ordering, not that a runtime calls a hook |

The one architectural rule is that `core/` is pure and the adapter is the only door: a test asserts that
`core/` contains no clock call, and a test fails if any module names the frontend's mock directory. The
**pricing seam** is `PricingModelAdapter`: instantiated bare it returns `available: false, basis:
"no_model_registered"`; the server registers the bounded estimator behind it, so `/health` reports
`kind: rule-based-bounded-estimator, fitted: false` with a note saying nothing was trained, calibrated or
validated.

### 17.2 The console, which is the product surface

One server-rendered page, every state a query parameter, no script, no external asset. In document order:
a **banner** carrying the synthetic-data sentence and the SHA-256 of the store the numbers came from, so a
screenshot names its own source; **controls** for event, tier, cut instant, candidate cap, fee, declared
tau, decision mode, and a button that submits the simulation flag, which is a button and not a script; an
**evidence strip** that puts the evidence count first, deliberately; the **decision block** by regime; the
**market block**; the **refusals**; the **design panel** badged as design; the **simulated state machine**;
and the **chain slot** in its absent state.

Four things are intentionally absent: no listing, bid, buy or checkout control; no sale probability at a
price; no interior optimum; and no accuracy, calibration or coverage number (`docs/CONSOLE.md`).

### 17.3 Every number carries its provenance, and the mechanism is a registry plus a test

`core/labels.py` is a registry of sentence templates, grouped into four dictionaries (27 allowed sentences, 8
negative variants, 31 page strings and 19 refusal sentences, 82 registered ids in total at the observed
state) plus 36 banned patterns and 36 banned source strings. Every number on the page is rendered through
`units.num`, which
puts one of eight badges in the same text run, in front of the value: `[FIXTURE]`, `[DECLARED]`, `[EXACT]`,
`[UNVALIDATED]`, `[REFUSED]`, `[DESIGN]`, `[SIMULATED]`, `[DEVNET]`. Two test modules enforce it: every
`.n` span must begin with a badge, the only digits outside a badge must sit inside a registry sentence,
and no rendered state or serialised payload may contain a banned phrase.

**The badges are a hierarchy of warrant, and the distinction is the product's honesty claim**: `[EXACT]`
is arithmetic true by definition, for example `ceiling 1,380,000,000 lamports = face 1,200,000,000 x
(10,000 + 1500) / 10,000`; `[FIXTURE]` is a count, price, date, tier, cap, sell-through or exposure read
from the store; `[DECLARED]` is a parameter the operator or the build chose; `[UNVALIDATED]` is a model
output; `[REFUSED]` is an absence; `[DESIGN]`, `[SIMULATED]` and `[DEVNET]` are not measurements at all.

### 17.4 The refusal taxonomy

Refusals are first-class: the panel is never empty, every line has a code and a sentence, and the codes are
asserted by tests. As observed at 12:45Z:

| Group | Codes | What each refuses |
|---|---|---|
| standing | `not_identified` | a sale probability at a price |
| | `no_demand_response` | an interior optimum without a primary demand response |
| value block | `no_resale_record` | a primary price when the event has no resales |
| | `no_upper_bound` | an upper end on a binding cap |
| | `no_exposure` | a rate with no ticket-days at risk |
| | `before_on_sale_no_pool` | a cold-start band before on-sale when no other event can be pooled |
| | `insufficient_events` | a fitted between-event dispersion below the nine-event floor |
| path | `insufficient_marks`, `insufficient_time_spread`, `degenerate_design`, `cap_mass_dominates`, `outside_support` | a path value, each for a named data reason |
| fee | `no_fee_model` | net revenue, only when no fee is supplied |
| request validation | `as_of_invalid`, `cap_invalid`, `fee_invalid`, `tau_invalid`, `mode_invalid`, `wallet_malformed`, `nonce_missing`, `signature_missing`, `no_ledger` | malformed input or absent state, with a rendered error page |
| store validation | `sale_not_priced`, and its siblings | a store that cannot be priced |

Three of these were added or corrected during the assembly of this document, which is the clearest evidence
that the review's honesty findings were taken seriously rather than argued with: the fee refusal is now
conditional on a fee being absent and the net line is rendered when one is supplied; the insufficient-marks
sentence no longer promises a flat line that is not drawn; and a store-level validation failure now renders a
named 422 page instead of producing no HTTP response at all.

### 17.5 The independent review, and its four verdicts

An independent reviewer who did not build any of it re-ran the acceptance test, the suite, the control
matrix and the failure paths, and pinned the reviewed state by file hashes (`07-engine-review.md`). Four
verdicts:

| Area | Verdict | The statement that stands |
|---|---|---|
| Mathematics | **STANDS-WITH-NARROWING** | the arithmetic that is implemented is right: the three regimes, the cap floor, the two-sided band, integer markup, the gamma-Poisson zero, the two-by-two path solve. The narrowing: the headline is not the finding's boundary price and is computed from the same event's resales, so it is a resale-value level or cap floor presented as a primary price |
| Honesty | **FAILS** | the badge machinery and the banned-sentence rule stand; four registry sentences stated things the engine does not compute; a zero-sale rate was a prior badged as a fixture with a basis that contradicted its value; the fee refusal was false when a fee was supplied; the evidence strip and one label gave two different sales counts for the same event |
| Code | **FAILS** | three store-valid inputs produced an empty reply with no HTTP status, because the console sat outside the handler's try; the `[EXACT]` line was false at its displayed precision; the loader accepted rows the core cannot price; the fee arithmetic went through float with no upper bound |
| Refusals | **STANDS-WITH-NARROWING** | the engine refuses the sale probability, the interior optimum, the uncapped bound, the prior-only price and the zero-exposure denominator visibly and in words; the narrowing is that the path refusal promised a flat line that was not rendered and the fee refusal was false once the fee control was used |

The review's own most consequential finding was about **temporal honesty rather than arithmetic**: the
recommendation used the event's own resales, which the temporal audit forbids at the primary decision
instant, and the page did not distinguish the two clocks (`07-engine-review.md` §2.8; `03-b` §2.1). That
was fixed during this assembly by labelling rather than by removing the number: the page now prints a
**decision mode**, defaulting to `COUNTERFACTUAL` with the sentence that this is not a price you could have
set, and offering `BEFORE-ON-SALE`, which admits only other events' completed records and refuses the value
block when there is nothing to pool. **The honest reading of the shipped default is therefore: a hindsight
recomputation, labelled as one.** A reader who wants the real primary decision uses the second mode and, on
this fixture, gets a pooled band over other events or a refusal.

### 17.6 What the review found that is still true at the observed state

Reported so the record is not a list of fixes:

1. **The pooled mean and the shrinkage weight are computed and, for the banded branch, not applied.** The
   level of a tier with its own record is the raw tier mean of log price-to-face. The pooled mean is used,
   since the decision-mode work, for the cold-start branch under `BEFORE-ON-SALE`. On the shipped fixture
   the omission moves a level by about 0.2%, so it is a narrowing rather than a visible error, but the code
   is narrower than the finding.
2. **The path model is scoped to the tier, not the event, and never answers on the shipped fixture.** The
   review measured all fifteen tier fits refusing, 6 for `outside_support`, 2 for `cap_mass_dominates`, 7 for
   `insufficient_marks`, because every sale is 52 to 70 days before its event and the requested horizons do not
   overlap that support. The two-by-two algebra is exercised by hand-built tests only, never end to end.
3. **The cold-start intensity is the gamma-Poisson posterior mean with the declared prior and no
   population-baseline correction**, which is the first factor of the finding's formula and not the second.
   The basis string now says `gamma_poisson_posterior`, so the value and its basis agree.
4. **The fee arithmetic still goes through float** and `feeLamports` has no upper bound; the net line is not
   rendered by default, so the visible risk is the JSON tool and any future renderer.
5. **The console is honest about all of the above and the tests do not test the states that fail.** The
   suite is real and it passes, and it is not the acceptance test the build specification describes.

### 17.7 The on-chain component is a design and a simulation, not a deployment

No program id, no compiled artefact, no cluster, no signature. `/health` reports `programDeployed: false`,
`programId: null`, `rpcEnabled: false`, and the chain slot on the page renders its absent state until an
artefact verifies. The design is in §14.7; the simulation is a Python mirror that proves the arithmetic and
the ordering of the state machine and nothing about a runtime. The page says exactly that.

---

## 18. Implementation-ready Python

### 18.1 What is implemented, and what is specified and not

| Implemented, standard library only | Specified, deliberately absent |
|---|---|
| features at a mandatory cut with slot ordering and null-slot counting; regime classification on (cap, at-ceiling count); the cap floor; the declared-width band; the cold-start prior band; partial pooling and the shrinkage weight as functions | the censored hedonic with EM (F3), the repeat-sales index (F2), the piecewise-exponential intensity with competing risks and cure (F7), the listing-episode hazard (F9), the primary sell-through Tobit (F10) |
| the per-tier deadline-convex path with five guards and a martingale fallback | the state-space interpolation between trades (F6), exact quantile regression (F16) |
| the composite rate with an exact exposure denominator, competing exit counts and the gamma-Poisson zero | the full hierarchy (F37), Fine-Gray (M35), shared frailty (M36) |
| the boundary recommendation with an exact consequence table and four refusals | the fee wedge as a fitted object (it is configuration by design), mean-CVaR, the reserve-price surface |
| the contract surface: 9 endpoints with structural and semantic conformance, cursor pagination, wallet verification over Ed25519 | the four missing observations, which are data rather than code |
| the label registry, the badge machinery, the refusal codes, the console | none, and the reason is that these are the parts that make the rest legible |

The gap between the two columns is the programme's honest output: the specification says what would be
built and why it is not, and the model registry holds the reason per row (no data, no solver under the
constraint, a parameter that is a prior in disguise, or a decision the operator has not made).

### 18.2 Running it, and what the run proves

```bash
cd /home/friend/ticketPricing
python3 -m ticketpath.server            # http://127.0.0.1:8788/ , port 8788, 8787 refused
python3 -m unittest discover -s tests   # the suite; the count is printed
python3 tools/guidance.py --event evt_syn_04 --as-of 2026-11-07T12:00:00Z   # the same payload without a browser
python3 tools/build_fixture_store.py --check                               # fixture matches a fresh build
```

A CLI path exists for the payload (`tools/guidance.py`), so the engine can be driven and batch-tested
headlessly, which the programme requires of anything a reviewer will use.

### 18.3 The test count, observed

**Observed at 2026-11-07T12:45Z: `python3 -m unittest discover -s tests` reported `Ran 352 tests in
12.157s`, `OK`.** That is the count this document states, and it is the third count observed in the same
session, because the tree was being edited while the document was assembled: 293 tests at 12:00Z, 309 at
12:15Z and 12:35Z, and 352 at 12:45Z. Between 12:33Z and 12:38Z the same command reported, in order, 2
failures and 16 errors, then 63 errors, then 3 failures and 6 errors, then none, all from an in-flight change
to the payload signature; that sequence is recorded here because a reviewer who re-runs the suite deserves to
know it happened rather than to discover it from a diff. The independent review recorded the same kind of
movement during its own pass (293, then 306, then 309, all passing) and kept all three numbers rather than
the flattering one.

**What the number means and what it does not.** The 352 tests are internal correctness: contract
conformance (22 tests at the reviewed snapshot), arithmetic invariants, refusal behaviour, label discipline,
the HTTP surface over a real socket, Ed25519 verification with a key generated in the test, cursor
pagination, and the fixture's own invariants. They are not evidence about ticket pricing, and per
`06-validation-protocol.md` §1.4 the suite must never be described as though it were.

### 18.4 The invariants the suite actually enforces

Worth listing, because they are the part of the implementation another engineer would inherit:

- No module in `core/` may call the clock; the cut instant is always an argument.
- No module may name the frontend's mock directory.
- Every `.n` span begins with one of the eight badges; no `title=` attribute anywhere, so no label lives in
a tooltip; no `<script>` and no external asset.
- The banner is the first element in document order and cannot be dismissed.
- The banned sentences appear nowhere in any rendered state or any serialised payload, and the pattern list
  is exercised by a test so deleting the ban breaks the suite.
- Contract fields: every declared field present, no undeclared field, money as JSON integers, addresses as
  32 base58 bytes, timestamps as ISO-8601 UTC, detail routes 404 rather than 200-with-null, and the
  verification message rebuilt from the contract text and verified for real.
- Markup is always against the ticket's own tier face, never re-derived at event level.
- The fixture matches a fresh deterministic build exactly, and its `meta.synthetic` flag is true or the
  loader refuses it.

---

## 19. Performance considerations

**Every number in this section is measured on this machine, at the instant stated, not estimated.**

### 19.1 Measured

| What | Measurement | How |
|---|---|---|
| process start to a listening socket | **36 ms** | fresh `python3 -m ticketpath.server --port 8936`, polled for `connect()` |
| process start to a served `/health` | **47 ms** | same process, first HTTP response |
| console page render | **2.0 to 2.4 ms** per page, **12,651 to 13,368 bytes** | six states: default, cold start, candidate cap of zero, uncapped, before-on-sale, with a fee |
| peak resident set, after 30 full page renders | **23 MB** (`VmHWM` 23,048 kB) | `/proc/<pid>/status` |
| fixture build and self-check | **0.04 s**, peak 21 MB | `tools/build_fixture_store.py --check` |
| test suite | **352 tests in 12.157 s** | `python3 -m unittest discover -s tests` |
| install, build, migration, network calls at startup | **zero** | no dependency, no build step, no network outside the tests' own ephemeral-port server |

For scale: the whole fixture is 147 ledger rows and 76 tickets, so these timings say what the *server*
costs, not what a real ledger would cost. That distinction matters and is stated rather than left implicit.

### 19.2 The computation is small by construction, and the reason is structural

Nothing in the engine needs a dense solve at a dimension that grows with the data, and that is a
consequence of the identification result rather than a coincidence (`B-mathematical-kb.md` §10):

| Component | Cost | Where the cost grows |
|---|---|---|
| composite intensity | aggregated cells of order thousands; Newton on roughly 40 parameters; `O(iteration x (K+p)^3)` | the number of time buckets and covariate patterns, not the number of ledger rows |
| censored hedonic (specified) | design matrix of order 10^3 by 20; EM with least squares per iteration | the number of marks and the number of time cells |
| cold-start band | a 601-point grid, each point a closed form; milliseconds | trivially in the number of events |
| mean-CVaR | `O(M log M)` for M scenarios, a sort plus a partial mean | the scenario count |
| reserve-price surface (specified) | backward induction on 216 states times 41 candidate prices | seconds at most, once per event |
| multiproduct optimisation (specified) | the fluid relaxation is an ODE, solvable with Euler or RK4 in a dozen lines; the full multiproduct dynamic program explodes and is not to be attempted | tier count squared |

Two consequences worth stating. **Precomputation is the right default**: a decision is made once per event,
so a fit that takes seconds is acceptable, and real-time inference is a table lookup against a fitted
object. And **the constraint that produced this design** (standard library only) is a constraint on
feasibility rather than a performance win: a numerical stack would make the same models faster to write and
not faster to run at this scale.

### 19.3 What was not measured, and why the omission is not an oversight

- **No latency under a real ledger**, because there is none. The one honest statement is that cost scales
  in ledger rows for the ingestion pass and in cells for the fits, and that both are far below the point
  where a standard-library implementation is a constraint.
- **No memory profile at scale**, for the same reason. The engine holds the whole fixture in memory, which
  is correct at 147 rows and would need an index at a million.
- **No accuracy or speed comparison against a numerical-stack implementation**, because none may be
  installed here (`00-data-situation.md` §1).

**Thin, and the reason is the same one that leaves sections 9 and 10 partial: there is no data to
measure performance against.** The numbers in 19.1 are real and reproducible; the extrapolations in 19.2 are class C;
and nothing in this section is a claim about production behaviour.

---

## 20. Limitations

**This section and the next are the most valuable part of the document. They are written to be complete and
blunt.**

### 20.1 There is no real data. None.

No backend, no database, no deployed program and no ledger exist on this machine
(`00-data-situation.md` §1, verified by inspection and by one live RPC call). The frontend's fixture data is
synthetic on three independent checks and is barred from estimation (§14.6). Therefore **no number in this
document is a measurement of ticket-market behaviour**, and no statement here about prices, sale
probabilities, elasticities or optima has been tested against a market. Every class A statement in this
document is a citation; every number this programme produced itself is class B, C, SIM or UNVALIDATED.

### 20.2 The four absences, and what each one costs

1. **No listing exposure.** No ask, no listing start, no revision, no withdrawal. This is why `P(sale |
   price, exposure, t)` is not identified and why the answer to "what is the probability this sells at
   price `p`" is a refusal rather than a number. It is the single most consequential limitation.
2. **A policy price ceiling that truncates the record from above**, permanently and most severely where
   demand is strongest. The value above the cap is not merely unmeasured, it is unmeasurable from this
   record at any sample size, and no amount of modelling recovers it. On such events the engine can state a
   floor and cannot state a mean or an upper end.
3. **No seat coordinates.** Tier is the only quality axis. Every within-event price statement in the
   published literature is a seat-level statement, and this engine cannot make one. Every seat-quality
   claim in this programme is class D.
4. **No fee, royalty or settlement field.** The net objective and the primary optimum take the fee stack as
   a parameter. The per-unit component is the one that moves the price, and it is the one nobody records.

Two smaller ones: the primary inventory is a snapshot with no time series, so sell-through velocity is
unobservable; and `Event.status` transitions are not timestamped, so the on-sale, sell-out and hold-back
release times are unknown.

### 20.3 The limitations that are not about missing fields

- **The level of value is not identified.** Only ratios are, up to an affine transformation, because the
   schema contains no exogenous price anchor. Face value is endogenous: it is the organiser's choice and
   the denominator of the measurement.
- **The population is conditional on the price actually charged.** Varying the primary price changes who is
   in the ledger, so **no secondary-market analysis can choose a primary price**.
- **The record is complete only conditional on enforcement.** Wallet handoff, off-platform settlement,
   bundling and side payment leave no row, so a recorded markup is a lower bound and the observed
   distribution is squeezed from both ends. **No claim of completeness may be made about the ledger.**
- **No buy side exists.** There are no bids, offers, views, searches or declines anywhere in the contract,
   so every demand statement rests on assumption and no econometric adjustment substitutes for it.
- **Selection is twofold.** Only sold tickets carry prices, and resold tickets are the better seats (mean
   seat-quality percentile 0.61 against 0.50).
- **Resale is sparse.** About 5% of tickets resell, with the mean carried by a few hot events, so most
   events have almost no history and the cold-start case is the normal case rather than the exception.
- **The prize is small.** Single-digit percentages of primary revenue, concentrated in the best seats. An
   engine that cannot resolve single-digit effects is not useful, and nothing here has been shown to.
- **Capture is not established, and the test that would settle it is a data-collection question.** A cap in
   basis points over face removes no primary price from the organiser's feasible set and adds no revenue
   channel, so no capture-rate term belongs in the objective; what it does is fix how the resale price divides
   between the organiser's price and the reseller's margin, in the ratio `1 : c`, and no primary price changes
   that ratio (`11-cap-capture-check.md` §5, §9; `F` D7). Whether the market value moves with face at all is
   unmeasured. The settling test is a scale test on uncapped or slack-cap events at two or more face levels,
   with a pre-declared rule (`β = 1` nominal capture, `β = 0` no capture beyond value over `1 + c`), and it
   needs more comparable events than this platform has. Rows that settle at the ceiling cannot answer it,
   because there the resale price is mechanically `p(1+c)` (`11` §7).
- **The last week's sign is unsettled**, so a model may not promise a direction in the final week.
- **The price path's linear slope is a normalisation**, not an estimate, and the reported bracket is
   honest only if the reader sees which normalisation produced the number.
- **Every published magnitude transfers as a prior belief, not as an estimate**: different markets,
   different measures, different conditioning, and a conditioning inversion in the most-quoted study.

### 20.4 What a reader must not conclude

Collected from the adversarial review's prohibition list (`00-adversarial-review-phase1.md` §4), the
engine's banned-sentence rule and the findings, and stated as prohibitions:

1. **Not** that this engine has measured what a ticket is worth. The level is not identified; ratios and
   bounds are.
2. **Not** that the probability this ticket sells at price `p` is known. It is not identified, and a curve
   that appears to show it is an artefact of which sellers chose which prices.
3. **Not** that a demand curve or an elasticity has been estimated. The one identified demand object is a
   one-sided bracket from primary sell-through, and it gives a sign.
4. **Not** that the cap correction recovers the true value of the best inventory. The correction's size is
   unknown and the leakage rate is unidentified.
5. **Not** that the cap is the central structural fact of the project. The missing listing exposure is the
   first constraint; the cap is the second.
6. **Not** that the asking-versus-realised gap has been measured. There is no ask anywhere in the record,
   so it has vanished rather than been estimated.
7. **Not** that any price distribution is calibrated, and **not** that any coverage or accuracy number for
   one exists. The sale indicator can be calibrated on the full population; no price distribution can be.
8. **Not** that the resale ledger is complete, or that the 41% markup is what the whole market earns. The
   1.4% sizing covers only the half of resale the authors observe.
9. **Not** that the engine finds the revenue-maximising primary price. It reports a boundary and a set, and
   says "a bound, not an optimum" on the page.
10. **Not** that weather, injuries, transfers, competing events or tour stops are irrelevant to pricing.
    They are excluded from the static on-sale decision, not from the in-market reprice and not from the
    ex-ante risk terms.
11. **Not** that anything is deployed, verified on chain, or backed by a signature. There is no program, no
    cluster and no transaction.
12. **Not** that the engine's numbers are consistent with each other simply because they are on one page.
    They were not, in one review, and the review's verdict was that honesty failed. The specific defects
    and their current status are in §17.4 to §17.6.
13. **Not** that the resale premium is capturable through the primary price. The cap fixes how the resale
    price divides, in the ratio `1 : c`, and the reseller's margin is not part of the organiser's revenue at
    any price (`11-cap-capture-check.md` §5, §9; `F` D7; §20.3).

### 20.5 Limitations in the records themselves

Recorded because a reviewer will audit the records as well as the engine, and because the programme's own
rule is to record conflicts rather than smooth them:

- `A-research-ledger.md` still carries **P1.C as `dispatched` with a 28-byte placeholder**, while the file
  it cites (`01-c-methods.md`) is complete at 1,558 lines. The ledger row is stale; the finding is real.
- The same file lists **Gap 1's diagnosis as contested** (C1, C2) and says `F` D3 carries the audit's
  version as settled. That is a live, unresolved disagreement between the audit, `01-b` and `02-c`; §14.2
  states all three and picks none.
- **"Gap 5" is cited five times and defined nowhere.** `00-data-situation.md` numbers four gaps and then
  adds two unnumbered ones. No file defines what Gap 5 was meant to be, and no correction could be applied
  without inventing a definition.
- **Class discipline is incomplete in five findings.** Several tables and prose sections carry no evidence
  class, and two files use the word "verified", which `records/README.md` does not define. This is the
  largest remaining defect in the corpus and the one most likely to matter at review
  (`CORRECTIONS-APPLIED.md` §3).
- **Two header timestamps postdate their own file mtimes**, and neither is corrected, because the true
  write time is not in the record and mtime is not usable as evidence after a pass that appends.
- **The prize sizing at 1.4 to 3.4% rests on a late-window mean**, and one finding argues the observed mean
  markup understates the value at the decision moment by 15% to 33% under the fitted shape (`02-a` §7.1).
  No file has overturned the number and no file has reconciled it either.
- **One verifier overstatement survives in a citation of the verifier**: the cold-start band's upper end is
  +153%, not +155%, computed from the file's own inputs (`02-e` CORRECTION 1).
- **`He & Lin` is cited in `01-a` while `01-b` and the variable registry say no peer-reviewed study of
  resale caps exists.** Whether the sentence is false depends on whether that paper is an econometric study
  or a model of matching, which nobody in this programme has read. **[CORRECTION 2026-11-07T14:00Z, R2-24 — the
  clause that needed no reading is now settled: a peer-reviewed paper on resale price caps in ticket markets
  *was* found, so `C-variable-registry.md` C-3's "no peer-reviewed study" is false as printed and is marked
  dead there. Whether it is econometric is still unread, so `01-b` §4.5's narrower sentence is neither
  confirmed nor refuted. See the status note below and §21.2.]** It is recorded as noticed and not
  resolved (`CORRECTIONS-APPLIED.md` §4 question 1).
- **`records/README.md` described this document as a stub.** **[R2-31]** It read "It is a stub and says so at the top: it
  is not written yet", which was true before 12:40Z and false after it. Struck in place on 2026-11-07T14:00Z
  (R2-23). It is listed here because an index that misdescribes its own deliverable is a limitation of the
  record, not only of the index.
- **`02-d` item 3's headline sentence is still printed, and is withdrawn.** "The resale premium is capturable
  entirely through the primary price" stands at `02-d` line 40 because findings are append-only; it is
  withdrawn immediately below it in place, on 2026-11-07T15:00Z, by `11-cap-capture-check.md` §9, and the
  decision is `F` D7. A reader who quotes that line without the correction below it is quoting a sentence this
  record no longer asserts. Listed here because a withdrawn sentence left standing at the top of a finding is
  the easiest thing in this corpus to quote by accident.

**Status note appended 2026-11-07T12:55Z, amended 2026-11-07T14:00Z, R2-30 — two items in the list above are now
closed and two more are corrected but not closed; an eighth bullet was added, and the list is kept as written
so the history of the audit survives.** (1) `A-research-ledger.md`'s P1.C row now carries
`01-c`'s conclusion, its classes and its path; the row was stale, the finding was not. (2) "Gap 5" is now
defined in `00-data-situation.md` §4 as the missing primary inventory time series, in the same style as Gaps
1–4, and all eight forward references were checked for a common referent and kept.

**(3) The He & Lin item is corrected on 2026-11-07T14:00Z, and the earlier wording of this note was itself false
in two clauses.** It said the question "is settled as far as the record can settle it" and that
`C-variable-registry.md` C-3's broader "no peer-reviewed study" "is narrowed to `01-b`'s wording there". Neither
holds. **Nothing narrowed that sentence:** it stood at `C-variable-registry.md:820-822` as printed until this
pass struck it there, and the note thirty lines below it said in terms that it did not settle the question. It
is now marked dead in place with a dated correction, and the surviving claim is `01-b` §4.5's narrower one, "no peer-reviewed **econometric**
study". **The question is open, not settled:** whether He & Lin (2026) is an econometric study or a model of
matching is unread by everyone in this programme, and §21.2 says so. What the record can now say without
reading the paper is only that a peer-reviewed paper on resale price caps in ticket markets exists and is
cited here for a class-C theoretical proposition, so C-3's clause cannot say no study was found. Items 4 to 8
stand unchanged.

**Items 1 to 7 above were assembled at 12:40Z. §20.6 was added at 14:00Z because the simulation study
landed after this document was written, and three of its results are limitations of shipped code.**

**A ninth bullet was added to the list at 2026-11-07T15:00Z** (the withdrawn `02-d` item 3 sentence), by the
narrowing recorded as `F` D7; it is a limitation of the record, like the rest of this subsection, and nothing
else in the list was rewritten for it.

### 20.6 The simulation study, and the limits it puts on shipped code

Added 2026-11-07T14:00Z, R2-29, from `09-sim-recovery.md` (run 13:30Z, harness `tools/sim_recovery.py`, log
`records/sim/sim-recovery-2026-11-07.txt`, verdicts A **PASS**, B **FAIL**, C **FAIL**, 37 of 43 pre-declared
conditions held). **Every number in this subsection is class SIM**: it is a property of an estimator measured
against a generative model that is the estimator's own assumption. It is not a measurement of a ticket market,
it is not calibration on this platform, and the gap between the two is the whole of §20.1. What it can do, and
what nothing class B or C in this document could do, is show where shipped code does not deliver what the
findings say it does.

Three results are limitations rather than confirmations:

1. **The declared band under-covers at two events, and it does so by construction.** At the true between-event
   tau of 0.30, coverage of a new event's mean is **0.805 at J=2** against the pre-declared `[0.87, 0.93]`, and
   0.872 and 0.879 at J=5 and J=20. The cause is arithmetic: the width is `z·tau`, while the gap the band must
   cover has variance `tau² + V(hat mu)`, and `V(hat mu)` is 0.0491 at J=2 against a `tau²` of 0.09. The width
   is a floor, as the code's own docstring says, and this is what a floor does at small J. The pooled width the
   payload already prints beside the band restores coverage to 0.897 at J=2 and 0.904 at J=5. **The limitation
   for a reader of this document: at two or five events the band on the event mean is too narrow to be a 90%
   interval, and the engine prints it anyway because it labels the width as declared rather than as coverage.**
2. **One constant is mis-set for the variance the programme actually assumes.** At the API default `tau = 0.20`,
   the declared band covers **0.620 / 0.694 / 0.718** of draws at J = 2 / 5 / 20 when the truth is 0.30. This
   condition was pre-registered as a predicted failure and it held, so it is a confirmed property of the
   constant, not a surprise. **The limitation: the default declared tau is narrower than the `tau` the
   literature prior implies, and a user who leaves the constant alone gets coverage of 0.620 to 0.718 against a
   nominal 0.90 — which is why §11.2 prints the whole sensitivity grid instead of one row.**
3. **The path estimator is meaningless in a short window, and no guard tests that.** In a 40-to-60-day window
   the shipped curvature estimator has **RMSE 1.0425** against a true `theta` of 0.30, with bias +0.0648. The
   cause is conditioning: the correlation between `d` and `log(1+d)` is 0.998679 over that window against
   0.962077 over 5 to 60 days. The shipped guard tests `delta <= 1e-12`, an absolute threshold that does not
   fire; what kept the number off the page was the horizon-support guard, which refused 392 of 400 fits because
   the default horizons sit outside a window starting at 40 days. **The limitation: the page is protected by a
   horizon check, not by any test of the design's conditioning, so a horizon set that fits a short window would
   print a curvature with no accuracy at all.**

A fourth result is a correction to a finding rather than a limitation of code: a cap that truncates the top of
the distribution biases the fitted curvature **up** — +0.0124 at a 10% cap mass, +0.0393 at 40%, +0.0255 at 70%
— while flattening the *observed* end-to-end path exactly as `02-a` C1 describes. C1 is right about the object
it names (the observed drop falls from 0.6957 to 0.3965 across those cells) and a report that cites it as
evidence that `theta` is attenuated downward would be wrong.

**What this subsection cannot support.** No coverage number here is calibration: the truth was chosen, the
bands are declared, and the errors are independent. Nothing here says event means are normal, that `tau` is
constant across events, or that `theta` is common. And the study does not test the object the product's third
claim needs — it tests the pooled mean and the curvature, and `P(sale at price p)` remains unidentified for the
reason §10.1 gives, unchanged by any SIM result.

---

## 21. Unresolved questions

### 21.1 The operator questions, in the order they change the build

**Q1. Does the company's internal ledger carry seat coordinates?** `AGENTS.md` claims the ledger yields
markup distribution conditioned on section; the wire contract carries tier id, serial and mint only. Either
the internal ledger is richer than the contract or "section" means tier. It matters because seat quality is
the strongest within-event price axis in every published study, and a tier-only engine cannot express the
within-tier variation that drives resale spread. **Until answered, the seat-quality variable is recorded as
"not in contract" and every seat-quality claim is class D** (`F` Q1).

**Q2. Is any part of the platform live, on devnet or otherwise?** No program id appears in the frontend and
no mints resolve. If a program is deployed elsewhere, its transaction history is a small real dataset and
part of this programme becomes empirically checkable. If nothing is deployed, the first real data will be
whatever the platform records after launch, which makes the recording schema a research artefact worth
getting right now (`F` Q2).

**Q3. Is the resale cap enforced on chain or by the platform's matching engine?** This is no longer a
curation question. It decides whether the value model's likelihood is truncated or censored, whether a mass
point at the cap should exist at all, and whether the record contains one known ask value on the cap-bound
stratum (`02-c` §2.5). One sentence from whoever built the transfer path settles it, and the first real
data dump settles it independently. The programme's own on-chain design answers it for that design (the cap
is checked before the transfer, so it is truncation) and leaves it open for the live platform (`F` D6).

**Q4. Does `issuedCount` mean sold, or minted?** Load-bearing, because it is the only pre-resale demand
signal, and the whole sell-through bracket depends on it. If it means minted, a whole class of inference
disappears (`01-b` §5; `02-e` §2.4; UNVALIDATED until answered).

**Q5. Is `faceValueLamports` the primary transaction price, or a nominal face?** A discount or a fee breaks
the assumption that the primary price is the observed one, which is the same bracket (`01-b` §5).

**Q6. Will the contract carry a category, and timestamped status transitions?** Category is the best single
cold-start covariate and its absence is the strongest argument against the comparables strategy. Without
timestamped transitions there is no on-sale time, so no sell-through velocity, so the demand bracket stays a
level and never becomes a curve (`02-e` §10; `03-b` A16, A29).

**Q7. What is the fee stack, and did the price display rule change what face means?** Needed for the primary
optimum and the risk functional; neutral for the resale ask. Any series spanning 2025-05-12 mixes pre-fee and
all-in quotes (`F` D4; `02-d` §1.1).

**Q8. Will the platform ever vary a price for the purpose of learning, or authorise a randomised arm?**
This is the only route to a causal price response. A randomised ask arm on listings, or the randomised
face-value design of §12.6, identifies what no amount of passive data can. It costs revenue, so it is a money
decision (`01-c` §6.3, §10.11; `02-d` §3.6).

**Q9. The mechanism fork, which is an architecture decision rather than a research question.** Budish &
Bhave's auctions "roughly doubled performer revenues", against Leslie & Sorensen's 3.4% for repricing the top
seats. Two published answers to the same commercial question differing by more than an order of magnitude,
because one changes the selling mechanism and the other changes a price level. Building a pricing engine or
recommending an auction for the top of the inventory are different products. Nobody in this programme has
read both papers closely enough to adjudicate, and that reading is the prerequisite (`01-c` §5.4).

**Q10. The decision-instant fork, which is now labelled but not decided.** The shipped default recomputes
the value from the event's own resales and says so (`COUNTERFACTUAL`); the real primary decision is the
`BEFORE-ON-SALE` mode, which on a genuinely new event refuses because there is nothing to pool. Whether the
product should ever present the first as a recommendation is the operator's decision, not a bug fix
(`07-engine-review.md` §6 item 4).

### 21.2 Research questions left open, with what would close each

| Question | Status | What would close it |
|---|---|---|
| Is the value level recoverable at all? | open, class C that it is not from this record | one exogenous price anchor: a cap-free event with a known external quote, or a completed off-platform sale |
| The per-day slope of the price path | open by construction (exact APC collinearity) | one dated common shock that moves several live events at once, treated as a period effect |
| The path for tickets that did not resell | open | the listing panel |
| Any forecast accuracy number | open, and not merely unmeasured | event-level walk-forward on the platform's own first season; no minimum event count is defensible in advance, so the honest output is the fold table with its per-fold spread, labelled indicative |
| Whether the deadline mechanism dominates the arrival effect | open and one-sidedly testable | the sales-per-ticket-day profile: a falling profile refutes the deadline story; a rising one is consistent with it and does not prove it |
| Whether the published 0.133 to 0.164 exponent transfers here | open | re-estimate on our own ledger; the literature prior is for cold start only |
| Whether events are exchangeable enough for pooling to beat face value | open | leave-one-event-out at five or more events, on squared log error, with the comparison's own uncertainty reported |
| Whether the between-event variance is nearer 0.1 or 0.4 | open | the same, over the first ten events, with the chi-square interval alongside the point estimate |
| Whether the borrowed prior transfers at all | open, class D | compare the first three platform events with resale to the borrowed band |
| Whether the cap mass behaves as predicted | open | a mass point at exactly the cap in a real ledger, which the fixture cannot produce |
| Whether the sell-through sign result holds | open | Q4 answered, then resale prices on sold-out against not-sold-out events |
| Whether a cheaper architecture performs as well | open, and the programme's own question | the benchmark ladder, run on real data: if the martingale or a fixed markup rule wins, it ships |
| Whether the price-response coefficient is even identifiable in practice | open | the four-diagnostic check on the first real listing panel: if ask dispersion within event-tier-time cells is zero, it is not |
| Whether a peer-reviewed study of resale caps in tickets exists | open, and now in two parts. **Closed 2026-11-07T14:00Z: one does** — He & Lin (2026), peer-reviewed, cited in `01-a` §3, so `C-variable-registry.md` C-3's "no peer-reviewed study" is dead as printed and is marked in place. **Open: whether it is an *econometric* study**, which is the bar `01-b` §4.5 sets | reading He & Lin (2026) and settling whether it is econometric or a model of matching; `01-a` NOTE of 12:55Z, §20.5 above |
| Whether the 14-of-128 redemption reading is a ticket count | open and unclosable from the record | a ticket-level status count, which the programme's own rule discourages producing from the fixture |
| What "Gap 5" means | **closed 2026-11-07T12:55Z**: the missing primary inventory time series, hence no sell-through velocity | defined in `00-data-situation.md` §4 as the fifth gap; all eight forward references agree |

### 21.3 Questions deliberately closed, with the reason

Recorded so they are not reopened: **structural auction estimation** (no bids, and the four listing fields
do not touch it); **optimal auction design as a fitted object** (Myerson's mechanism is a functional of a
prior nobody can estimate); **overbooking, cancellation and no-show revenue management** (a ticket token is
the seat; there is no reservation to oversell); **network and origin-and-destination yield management**
(tiers do not share capacity); **synthetic control, difference-in-differences and event studies** (no
untreated units with a parallel trend); **Rosen's second stage** (one market's transactions do not separate
demand from supply); **Google Trends and social sentiment** (not lawfully collectable at commercial scale,
and redundant with observed demand); **a "liquidity score" or any composite index** (a composite computed
from unidentified components is the failure this programme exists to avoid); and **a dynamic pricing
policy for this product** (there is no price-mutation endpoint, so there is no action space).

---

## 22. Full bibliography

Deduplicated from the sources the findings cite, with the locator each finding used. **No source appears here
that no finding cites**, and none was added from memory: where a citing finding records only a journal and a
DOI and no title, the title is not supplied here and the entry says so. Internal records (`records/*.md` and
`records/findings/*.md`) are cited by filename and section throughout the document and are not listed again.
Findings are abbreviated: 01a, 01b, 01c, 01d, 02a, 02ai, 02c, 02d, 02e, 03a, 06 are the phase findings;
00data is `00-data-situation.md`; E is the data-source registry.

### 22.1 Peer-reviewed papers, working papers and books

| # | Source | Locator | Used by |
|---|---|---|---|
| 1 | Abadie, A. & Imbens, G. W. (2006). Large sample properties of matching estimators for average treatment effects | Econometrica 74(1):235-267, doi:10.1111/j.1468-0262.2006.00655.x | 02e |
| 1a | Ahn, S. C. & Lee, Y. H. (2007). Lifecycle demand for Major League Baseball | International Journal of Sport Finance 2(2):79-93, doi:10.1177/155862350700200203 | 02d |
| 2 | Aigner, D. J. (1973). Regression with a binary independent variable subject to errors of observation | J. Econometrics 1(1):49-59, doi:10.1016/0304-4076(73)90005-5 | 01b |
| 3 | Allison, P. D. (1982). Discrete-time methods for the analysis of event histories | Sociological Methodology 13:61-98, doi:10.2307/270718 | 01c, 02c |
| 4 | Amemiya, T. (1984). Tobit models: a survey | J. Econometrics 24(1-2):3-61, doi:10.1016/0304-4076(84)90074-5 | 01c |
| 5 | Andersen, P. K. & Gill, R. D. (1982). Cox's regression model for counting processes | Ann. Statist. 10(4):1100-1120, doi:10.1214/aos/1176345976 | 01c, 02c |
| 6 | Andersen, P. K., Abildstrom, S. Z. & Rosthoj, S. (2002). Competing risks as a multi-state model | Stat. Methods Med. Res. 11(2):203-215, doi:10.1191/0962280202sm281ra | 02c |
| 7 | Anenberg, E. (2016). Information frictions and housing market dynamics | Int. Economic Review 57(4):1449-1479, doi:10.1111/iere.12204 | 02e |
| 8 | Angelopoulos, A. N. & Bates, S. (2023). Conformal prediction: a gentle introduction | FnT Machine Learning 16(4):494-591, doi:10.1561/2200000101 | 01c |
| 9 | Artzner, P., Delbaen, F., Eber, J.-M. & Heath, D. (1999). Coherent measures of risk | Mathematical Finance 9(3):203-228, doi:10.1111/1467-9965.00068 | 01c, 02d |
| 10 | Aviv, Y. & Pazgal, A. (2008). Optimal pricing of seasonal products with forward-looking consumers | M&SOM 10(3):339-359, doi:10.1287/msom.1070.0183 | 01c |
| 11 | Bailey, M. J., Muth, R. F. & Nourse, H. O. (1963). A regression method for real estate price index construction | JASA 58(304):933-942, doi:10.1080/01621459.1963.10480679 | 01b, 01c, 02a |
| 12 | Barber, R. F., Candes, E. J., Ramdas, A. & Tibshirani, R. J. (2023). Conformal prediction beyond exchangeability | Ann. Statist. 51(2):816-845, doi:10.1214/23-AOS2276 | 01c |
| 13 | Belobaba, P. P. (1989). Application of a probabilistic decision model to airline seat inventory control | Operations Research 37(2):183-197, doi:10.1287/opre.37.2.183 | 01c |
| 14 | Besbes, O., Gur, Y. & Zeevi, A. (2015). Non-stationary stochastic optimization | Operations Research 63(5):1227-1244, doi:10.1287/opre.2015.1408 | 01c |
| 15 | Bitran, G. & Caldentey, R. (2003). An overview of pricing models for revenue management | M&SOM 5(3):203-229, doi:10.1287/msom.5.3.203.16031 | 01c |
| 16 | Boag, J. W. (1949). Maximum likelihood estimates of the proportion of patients cured by cancer therapy | JRSS-B 11(1):15-44, doi:10.1111/j.2517-6161.1949.tb00020.x | 01b, 01c, 02c |
| 17 | Bollinger, C. R. (1996). Bounding mean regressions when a binary regressor is mismeasured | J. Econometrics 73(2):387-399, doi:10.1016/S0304-4076(95)01730-5 | 01b, 02c |
| 18 | Borgan, O., Goldstein, L. & Langholz, B. (1995). Methods for sampled cohort data in the Cox model | Ann. Statist. 23(5):1749-1778, doi:10.1214/aos/1176324322 | 02c |
| 19 | Bremaud, P. (1981). Point Processes and Queues: Martingale Dynamics | Springer, doi:10.1007/978-1-4684-9477-8 | 01c |
| 20 | Brown, J. N. & Rosen, H. S. (1982). On the estimation of structural hedonic price models | Econometrica 50(3):765-768, doi:10.2307/1912614 | 01b, 01c |
| 21 | Budish, E. & Bhave, A. (2023). Primary-market auctions for event tickets | AEJ: Micro 15(1):142-170, doi:10.1257/mic.20180230 | 01a, 01c, 02e |
| 22 | Bulow, J. & Klemperer, P. (2009). Why do sellers (usually) prefer auctions? | AER 99(4):1544-1575, doi:10.1257/aer.99.4.1544 | 01c |
| 23 | Bulow, J. & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer surplus | JPE 120(1):160-186, doi:10.1086/665416 | 01b, 01c, 02c, 03a |
| 24 | Burdett, K. & Judd, K. L. (1983). Equilibrium price dispersion | Econometrica 51(4):955-969, doi:10.2307/1912045 | 01b, 01c |
| 25 | Case, K. E. & Shiller, R. J. (1987). Prices of single family homes since 1970 | NBER WP 2393, doi:10.3386/w2393 | 01b |
| 26 | Clopper, C. J. & Pearson, E. S. (1934). The use of confidence or fiducial limits illustrated in the case of the binomial | Biometrika 26(4):404-413, doi:10.1093/biomet/26.4.404 | 02c |
| 27 | Conlon, C. T. & Mortimer, J. H. (2013). Demand estimation under incomplete product availability | AEJ: Micro 5(4):1-30, doi:10.1257/mic.5.4.1 | 01b |
| 28 | Courty, P. (2003) | JEP 17(2), doi:10.1257/089533003765888449 (title not stated in the citing finding) | 01a |
| 29 | Courty, P. & Pagliero, M. (2012). The impact of price discrimination on revenue: the concert industry | REStat 94(1):359-369, doi:10.1162/rest_a_00179 | 01a, 02d |
| 30 | Cox, D. R. (1972). Regression models and life-tables | JRSS-B 34(2):187-202, doi:10.1111/j.2517-6161.1972.tb00899.x | 01b, 01c, 02c |
| 31 | Crook, J. N. & Banasik, J. (2004). Does reject inference really improve the performance of application scoring models? | J. Banking & Finance 28(4):857-874, doi:10.1016/S0378-4266(03)00203-6 | 01b, 01c |
| 32 | Cui, Y., Duenyas, I. & Sahin, O. (2014) | Management Science 60(9), doi:10.1287/mnsc.2013.1862 (title not stated in the citing finding) | 01a |
| 33 | Dana, J. D. Jr. (1998). Advance-purchase discounts and price discrimination in competitive markets | JPE 106(2):395-422, doi:10.1086/250014 | 02d |
| 34 | Dawid, A. P. (1982). The well-calibrated Bayesian | JASA 77(379):605-610, doi:10.1080/01621459.1982.10477856 | 01b |
| 35 | Dawid, A. P. (1984). The prequential approach | JRSS-A 147(2):278-292, doi:10.2307/2981683 | 02c |
| 36 | Delipalla, S. & Keen, M. (1992). Ad valorem versus specific taxation under imperfect competition | J. Public Economics 49(3):351-367, doi:10.1016/0047-2727(92)90073-O | 02d |
| 37 | den Boer, A. V. (2015). Dynamic pricing and learning: historical origins, current research, new directions | Surveys in OR and Management Science 20(1):1-18, doi:10.1016/j.sorms.2015.03.001 | 02e |
| 38 | Deneckere, R. & Peck, J. (2011) | cited in Sweeting (2012) footnote 7 as the source of the martingale prediction; **not read** | 02a |
| 39 | DerSimonian, R. & Laird, N. (1986). Meta-analysis in clinical trials | Controlled Clinical Trials 7(3):177-188, doi:10.1016/0197-2456(86)90046-2 | 02e |
| 40 | Dudik, M., Erhan, D., Langford, J. & Li, L. (2014). Doubly robust policy evaluation and optimization | Statistical Science 29(4):485-511, doi:10.1214/14-sts500 | 01c |
| 41 | Efron, B. (2010). Large-Scale Inference | CUP, doi:10.1017/CBO9780511761362 | 01c |
| 42 | Efron, B. & Morris, C. (1973). Stein's estimation rule and its competitors | JASA 68(341):117-130, doi:10.1080/01621459.1973.10481350 | 02e |
| 43 | Efron, B. & Morris, C. (1975). Data analysis using Stein's estimator and its generalizations | JASA 70(350):311-319, doi:10.1080/01621459.1975.10479864 | 01b, 01c, 02a, 02c, 02e |
| 44 | Ekeland, I., Heckman, J. J. & Nesheim, L. (2004). Identification and estimation of hedonic models | JPE 112(S1):S60-S109, doi:10.1086/379947 | 01b, 01c, 02e, 03a |
| 45 | Farewell, V. T. (1982). Mixture models for survival data with long-term survivors | Biometrics 38(4):1041-1046, doi:10.2307/2529885 | 02c |
| 46 | Fine, J. P. & Gray, R. J. (1999). A proportional hazards model for the subdistribution of a competing risk | JASA 94(446):496-509, doi:10.1080/01621459.1999.10474144 | 01b, 01c, 02c |
| 47 | Firth, D. (1993). Bias reduction of maximum likelihood estimates | Biometrika 80(1):27-38, doi:10.1093/biomet/80.1.27 | 02c |
| 48 | Fleming, T. R. & Harrington, D. P. (2005). Counting Processes and Survival Analysis | Wiley, doi:10.1002/9781118150672 | 01c |
| 49 | Fosse, E. & Winship, C. (2019). Analyzing age-period-cohort data: a review and critique | Annu. Rev. Sociology 45:467-492, doi:10.1146/annurev-soc-073018-022616 (corrected authorship; the findings first printed it as Luo) | 01b, 02a, 03b |
| 50 | Gallego, G. & van Ryzin, G. (1994). Optimal dynamic pricing of inventories with stochastic demand over finite horizons | Management Science 40(8):999-1020, doi:10.1287/mnsc.40.8.999 | 01b, 01c, 02a, 02c, 02d, 02e, 03a |
| 51 | Gallego, G. & van Ryzin, G. (1997). A multiproduct dynamic pricing problem | Operations Research 45(1):24-41, doi:10.1287/opre.45.1.24 | 01c |
| 52 | Gatzlaff, D. H. & Haurin, D. R. (1997). Sample selection bias and repeat-sales index estimates | JREFE 14(1):33-50, doi:10.1023/A:1007763816289 | 01b, 01c |
| 53 | Ge, Q., Humphreys, B. R. & Zhou, K. (2020) (weather and attendance) | J. Sports Economics 21(3):304-322, no DOI given in the citing finding | 01d |
| 54 | Gelman, A. (2006). Prior distributions for variance parameters in hierarchical models | Bayesian Analysis 1(3):515-534, doi:10.1214/06-BA117A | 01c, 02e |
| 55 | Glaeser, E. L. & Luttmer, E. F. P. (2003). The misallocation of housing under rent control | AER 93(4):1027-1046, doi:10.1257/000282803769206188 | 01b, 01c, 03a |
| 56 | Gneiting, T. & Katzfuss, M. (2014). Probabilistic forecasting | Annu. Rev. Statistics and Its Application 1:125-151, doi:10.1146/annurev-statistics-062713-085831 | 02e |
| 57 | Gneiting, T. & Raftery, A. E. (2007). Strictly proper scoring rules, prediction, and estimation | JASA 102(477):359-378, doi:10.1198/016214506000001437 | 01c, 02c, 06 |
| 58 | Goetzmann, W. N. (1992). The accuracy of real estate indices: repeat sale estimators | JREFE 5(1):5-53, doi:10.1007/BF00153997 | 01b |
| 59 | Graf, E., Schmoor, C., Sauerbrei, W. & Schumacher, M. (1999). Assessment of prognostic classification schemes for survival data | Statistics in Medicine 18(17-18):2529-2545, doi:10.1002/(sici)1097-0258(19990915/30)18:17/18<2529::aid-sim274>3.0.co;2-5 | 02c |
| 60 | Guerre, E., Perrigne, I. & Vuong, Q. (2000). Optimal nonparametric estimation of first-price auctions | Econometrica 68(3):525-574, doi:10.1111/1468-0262.00123 | 01c |
| 61 | Haile, P. A. (2001). Auctions with resale markets | AER 91(3):399-427, doi:10.1257/aer.91.3.399 | 01c |
| 62 | Harris, M. & Raviv, A. (1981). A theory of monopoly pricing schemes with demand uncertainty | AER 71(3):347-365 (AER/JSTOR record; not Crossref-indexed) | 02d |
| 63 | Hartung, J. & Knapp, G. (2001). A refined method for meta-analysis of controlled clinical trials with binary outcome | Statistics in Medicine 20(24):3875-3889, doi:10.1002/sim.1009 | 02e |
| 64 | He, D. & Lin, S. (2026). Price caps by matching platforms: the case of ticket resales | Marketing Science 45(3):515-533, doi:10.1287/mksc.2023.0623 (cited as 2025 in one finding; corrected to 2026) | 01a, 03a |
| 65 | Heckman, J. J. (1979). Sample selection bias as a specification error | Econometrica 47(1):153-161, doi:10.2307/1912352 | 01b |
| 66 | Higgins, J. P. T. & Thompson, S. G. (2002). Quantifying heterogeneity in a meta-analysis | Statistics in Medicine 21(11):1539-1558, doi:10.1002/sim.1186 | 02e |
| 67 | Higgins, J. P. T., Thompson, S. G. & Spiegelhalter, D. J. (2009). A re-evaluation of random-effects meta-analysis | JRSS-A 172(1):137-159, doi:10.1111/j.1467-985X.2008.00552.x | 02e |
| 68 | Holford, T. R. (1980). The analysis of rates and of survivorship using log-linear models | Biometrics 36(2):299-305, doi:10.2307/2529982 | 02c |
| 69 | Hougaard, P. (1995). Frailty models for survival data | Lifetime Data Analysis 1(3):255-273, doi:10.1007/BF00985760 | 01c |
| 70 | Killick, R., Fearnhead, P. & Eckley, I. A. (2012). Optimal detection of changepoints with linear cost | JASA 107(500):1590-1598, doi:10.1080/01621459.2012.737745 | 01c |
| 71 | Koenker, R. & Bassett, G. (1978). Regression quantiles | Econometrica 46(1):33-50, doi:10.2307/1913643 | 01c |
| 72 | Lagakos, S. W. (1979). General right censoring and its impact on the analysis of survival data | Biometrics 35(1):139-156, doi:10.2307/2529941 | 01b, 01c, 02c |
| 73 | Laird, N. & Olivier, D. (1981). Covariance analysis of censored survival data using log-linear analysis | JASA 76(374):231-240, doi:10.1080/01621459.1981.10477634 | 02c |
| 74 | Lakkaraju, H., Kleinberg, J., Leskovec, J., Ludwig, J. & Mullainathan, S. (2017). The selective labels problem | KDD '17:275-284, doi:10.1145/3097983.3098066 | 01b, 02c |
| 75 | Lancaster, T. (1979). Econometric methods for the duration of unemployment | Econometrica 47(4):939-956, doi:10.2307/1914140 | 02c |
| 76 | Lattimore, T. & Szepesvari, C. (2020). Bandit Algorithms | CUP, doi:10.1017/9781108571401 | 01c |
| 77 | Lee, J., Morse, A., Hyun, M., Shapiro, S. L. & Drayer, J. (2023). Does time matter? How MLB secondary market sellers make ticket pricing decisions | Sport, Business and Management 13(3):397-415, doi:10.1108/sbm-05-2022-0042 (abstract read only) | 02a |
| 78 | Lee, D. S. & Lemieux, T. (2010). Regression discontinuity designs in economics | J. Economic Literature 48(2):281-355, doi:10.1257/jel.48.2.281 | 02c |
| 79 | Leslie, P. & Sorensen, A. (2009). The welfare effects of ticket resale | NBER WP 15476, doi:10.3386/w15476 | 01a |
| 80 | Leslie, P. & Sorensen, A. (2014). Resale and rent-seeking: an application to ticket markets | RES 81(1):266-300, doi:10.1093/restud/rdt033; full text read at users.ssc.wisc.edu/~atsorensen/papers/resale.pdf | 01a, 01b, 01c, 02a, 02d, 02e |
| 81 | Li, L., Chu, W., Langford, J. & Schapire, R. E. (2010). A contextual-bandit approach to personalized news recommendation | WWW '10:661-670, doi:10.1145/1772690.1772758 | 01c |
| 82 | Lo, A. W. & MacKinlay, A. C. (1990). An econometric analysis of nonsynchronous trading | J. Econometrics 45(1-2):181-211, doi:10.1016/0304-4076(90)90098-E | 01b |
| 83 | Maller, R. A. & Zhou, S. (1995). Testing for the presence of immune or cured individuals | Biometrics 51(4):1197-1205, doi:10.2307/2533253 | 02c |
| 84 | Mason, K. O., Mason, W. M., Winsborough, H. H. & Poole, W. K. (1973). Some methodological issues in cohort analysis of archival data | ASR 38(2):242-258, doi:10.2307/2094398 (corrected authorship; one finding printed Winship) | 01b, 02a |
| 85 | Meese, R. A. & Wallace, N. E. (1997). The construction of residential housing price indices | JREFE 14(1):51-73, doi:10.1023/A:1007715917198 | 01b, 01c |
| 86 | Meiklejohn, S. et al. (2013). A fistful of bitcoins | IMC '13:127-140, doi:10.1145/2504730.2504747 | 01b |
| 87 | Morris, C. N. (1983). Parametric empirical Bayes inference | JASA 78(381):47-55, doi:10.1080/01621459.1983.10477920 | 02e |
| 88 | Murphy, A. H. (1973). A new vector partition of the probability score | J. Applied Meteorology 12(4):595-600, doi:10.1175/1520-0450(1973)012<0595:ANVPOT>2.0.CO;2 | 01b, 01c, 02c |
| 89 | Myerson, R. B. (1981). Optimal auction design | Math. of OR 6(1):58-73, doi:10.1287/moor.6.1.58 | 01c |
| 90 | Noll, R. G. (2013). Endogeneity in attendance demand models | in The Economics of Sport, Edward Elgar, 117-134, doi:10.4337/9781781002865.00016 (abstract) | 02d |
| 91 | Ozhegova, A. & Ozhegov, E. M. (2018). Estimation of demand function for performing arts | J. New Economic Association 37(1):87-110, doi:10.31737/2221-2264-2018-37-1-4 (abstract; magnitude not obtained) | 02d |
| 92 | Page, E. S. (1954). Continuous inspection schemes | Biometrika 41(1-2):100-115, doi:10.1093/biomet/41.1-2.100 | 01c |
| 93 | Pakes, A. (2003). A reconsideration of hedonic price indexes with an application to PCs | AER 93(5):1578-1596, doi:10.1257/000282803322655455 | 01c |
| 94 | Papies, D. & van Heerde, H. J. (2017). The dynamic interplay between recorded music and live concerts | J. Marketing 81(4):67-87, doi:10.1509/jm.14.0473 (direction only) | 02d |
| 95 | Partlett, C. & Riley, R. D. (2017). Random effects meta-analysis: coverage performance of intervals following REML | Statistics in Medicine 36(2):301-317, doi:10.1002/sim.7140 | 02e |
| 96 | Peskir, G. & Shiryaev, A. N. (2006). Optimal Stopping and Free-Boundary Problems | Birkhauser, doi:10.1007/978-3-7643-7390-0 | 01c |
| 97 | Plackett, R. L. (1950). Some theorems in least squares | Biometrika 37(1-2):149-157, doi:10.1093/biomet/37.1-2.149 | 01c |
| 98 | Powell, J. L. (1986). Censored regression quantiles | J. Econometrics 32(1):143-155, doi:10.1016/0304-4076(86)90016-3 | 02a |
| 99 | Prentice, R. L. (1986). A case-cohort design for epidemiologic cohort studies | Biometrika 73(1):1-11, doi:10.1093/biomet/73.1.1 | 01b, 01c, 02c |
| 100 | Prentice, R. L. & Gloeckler, L. A. (1978). Regression analysis of grouped survival data | Biometrics 34(1):57-67, doi:10.2307/2529588 | 02c |
| 101 | Prentice, R. L., Kalbfleisch, J. D., Peterson, A. V., Flournoy, N., Farewell, V. T. & Breslow, N. E. (1978). The analysis of failure times in the presence of competing risks | Biometrics 34(4):541-554, doi:10.2307/2530374 | 02c |
| 102 | Rockafellar, R. T. & Uryasev, S. (2000). Optimization of conditional value-at-risk | J. Risk 2(3):21-41, doi:10.21314/JOR.2000.038 | 01c, 02d |
| 103 | Rosen, S. (1974). Hedonic prices and implicit markets | JPE 82(1):34-55, doi:10.1086/260169 | 01b, 01c |
| 104 | Rossi, P. E., Allenby, G. M. & McCulloch, R. (2005). Bayesian Statistics and Marketing | Wiley, doi:10.1002/0470863692 | 01c |
| 105 | Rossi, P. E., McCulloch, R. E. & Allenby, G. M. (1996). The value of purchase history data in target marketing | Marketing Science 15(4):321-340, doi:10.1287/mksc.15.4.321 | 02e |
| 106 | Russo, D. J., Van Roy, B., Kazerouni, A., Osband, I. & Wen, Z. (2018). A tutorial on Thompson sampling | FnT Machine Learning 11(1):1-96, doi:10.1561/2200000070 | 01c |
| 107 | Schein, A. I., Popescul, A., Ungar, L. H. & Pennock, D. M. (2002). Methods and metrics for cold-start recommendations | SIGIR '02, doi:10.1145/564376.564421 | 02e |
| 108 | Shapiro, S. L. & Drayer, J. (2012) | J. Sport Management 26(6):532, doi:10.1123/jsm.26.6.532 (title not stated in the citing finding) | 01a |
| 109 | Sidik, K. & Jonkman, J. N. (2005). Simple heterogeneity variance estimation for meta-analysis | JRSS-C 54(2):367-384, doi:10.1111/j.1467-9876.2005.00489.x | 02e |
| 110 | Steele, M. & Goy, R. (1997). Short holds, the distributions of first and second sales, and bias in the repeat-sales price index | JREFE 14(1):133-154, doi:10.1023/A:1007780219924 | 01b, 01c |
| 111 | Su, X. (2007). Intertemporal pricing with strategic customer behavior | Management Science 53(5):726-741, doi:10.1287/mnsc.1060.0667 | 01c |
| 112 | Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence from MLB tickets | JPE 120(6):1133-1172, doi:10.1086/669254; NBER WP 14505, doi:10.3386/w14505; author's manuscript read at econweb.umd.edu/~sweeting/SWEETING_PDECLINE_0112.pdf | 01a, 01b, 01c, 02a, 02c, 02e |
| 113 | Talluri, K. T. & van Ryzin, G. J. (2004). The Theory and Practice of Revenue Management | Springer, doi:10.1007/b139000 | 01c |
| 114 | Tibshirani, R. J., Barber, R. F., Candes, E. J. & Ramdas, A. (2019). Conformal prediction under covariate shift | arXiv:1904.06019 | 01c |
| 115 | Tobin, J. (1958). Estimation of relationships for limited dependent variables | Econometrica 26(1):24-36, doi:10.2307/1907382 | 01b |
| 116 | Van Calster, B., McLernon, D. J., van Smeden, M., Wynants, L. & Steyerberg, E. W. (2019). Calibration: the Achilles heel of predictive analytics | BMC Medicine 17(1), doi:10.1186/s12916-019-1466-7 | 02c |
| 117 | Vaupel, J. W., Manton, K. G. & Stallard, E. (1979). The impact of heterogeneity in individual frailty | Demography 16(3):439-454, doi:10.2307/2061224 | 02c |
| 118 | Viechtbauer, W. (2007). Confidence intervals for the amount of heterogeneity in meta-analysis | Statistics in Medicine 26(1):37-52, doi:10.1002/sim.2514 | 02e |
| 119 | Vovk, V., Gammerman, A. & Shafer, G. (2005). Algorithmic Learning in a Random World | Springer, doi:10.1007/b106715 (author list confirmed from the ACM review record, doi:10.1145/1189056.1189065) | 01c |
| 120 | Wardhaugh, B. (2026) (legal argument, not a measurement) | Legal Studies, doi:10.1017/lst.2026.10125 (title not stated in the citing finding) | 01a |
| 121 | Weyl, E. G. & Fabinger, M. (2013). Pass-through as an economic tool | JPE 121(3), doi:10.1086/670401 | 02d |
| 122 | Wilson, E. B. (1927). Probable inference, the law of succession, and statistical inference | JASA 22(158):209-212, doi:10.1080/01621459.1927.10502953 | 02c |
| 123 | Working, E. J. (1927). What do statistical "demand curves" show? | QJE 41(2):212-235, doi:10.2307/1883501 | 01b, 01c, 02c |

### 22.2 Regulation, regulator and legal material

| # | Source | Locator | Used by |
|---|---|---|---|
| 124 | 16 CFR Part 464, Rule on Unfair or Deceptive Fees (the all-in ticket pricing rule), 90 FR 2166, effective 2025-05-12 | https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-464 | 01a, 02d, 02e |
| 125 | UK Department for Business and Trade, press release, 2025-11-19, banning ticket touting | gov.uk news release (URL as printed in 01a) | 01a |
| 126 | UK DBT analytical note, 2025-12-19: 37.1m primary and 1.9m secondary tickets, GBP 350m, 75% markup, 20% displacement, no elasticity | gov.uk publication page (URL as printed in 01a and 02d); read in full | 01a, 02d, 03a |
| 127 | CMA, completed acquisition by PUG LLC (viagogo) of the StubHub business of eBay Inc., final report | as quoted by the DBT analytical note (p.131 onward); the report itself was not fetched | 01a |
| 128 | NSW Fair Trading, Ticket reselling (10% cap since 2018-06-01) | https://www.nsw.gov.au/legal-and-justice/consumer-rights-and-protection/services/ticket-reselling | 01a |
| 129 | Ireland, Sale of Tickets Act 2021, in force 2021-07-31 | Gov.ie, post-enactment report | 01a |
| 130 | Paul, Weiss client memo on the Live Nation/Ticketmaster antitrust verdict, April 2026 | https://www.paulweiss.com/insights/client-memos/live-nationticketmaster-antitrust-verdict-key-takeaways-from-the-states-jury-trial-win | 01a |

### 22.3 The wire contract, the platform and its fixtures

| # | Source | Locator | Used by |
|---|---|---|---|
| 131 | The wire contract itself | `/home/friend/ticketing-frontend/lib/types.ts` ("This file is the contract") and `API_CONTRACT.md`, 9 endpoints, read field by field | all findings |
| 132 | The frontend's synthetic fixture data, audited and barred from estimation | `/home/friend/ticketing-frontend/lib/mock/` (6 events, 128 tickets, 253 ledger rows) | 00data, 01b |
| 133 | Solana devnet JSON-RPC endpoint, used for one `getAccountInfo` call that returned `WrongSize` | `https://api.devnet.solana.com` | 00data |

### 22.4 APIs, data providers and their terms

| # | Source | Locator and finding note | Used by |
|---|---|---|---|
| 134 | Ticketmaster Discovery API v2 | vendor docs plus a vendor test of 2,397 US events (Oct 2026): `priceRanges` on 3 events; price fields dropped from the Discovery Feed on 2025-03-11. Free key, 5,000 calls/day, 5 req/s. No price data | 01d, E |
| 135 | Ticketmaster Partner / Inventory Status / Top Picks APIs | request-only, not publicly priced; a free key returned 401 (vendor-reported) | 01d, E |
| 136 | SeatGeek Platform API | `api.seatgeek.com/2/events` returns 403 "Client is required"; terms not verified | 01d, E |
| 137 | StubHub API (Account, Catalog, Inventory, Sales, Webhooks) | OAuth2, app credentials required; seller-side inventory, not a market price feed | 01d, E |
| 138 | Viagogo, Vivid Seats, AXS, TicketNetwork, Gametime | no public self-serve API found; scraping exposure unresolved | 01d, E |
| 139 | tickets.dev capture API | vendor pricing from $50/month for 1,000 captures | 01d, E |
| 140 | Get Protocol / on-chain ticketing | `docs.get-protocol.io` returns 401 without an account; "millions of on-chain smart tickets since 2016" is a vendor claim; whether a fiat resale price is on chain is not established | 01d, 01a, E |
| 141 | Google Trends (robots.txt and Terms of Service) | `trends.google.com/robots.txt` and `www.google.com/robots.txt` disallow `/trends/api` and `/trends/explore?` | 01d, E |
| 142 | X API v2 pricing | $0.005 per Post read, $0.010 per User read, 3M Post reads per month cap | 01d, E |
| 143 | Reddit Data API terms | fees reserved; no ML training on user content without rightsholder permission | 01d, E |
| 144 | Spotify Web API terms | content may not be used to train or be ingested into an ML model; `popularity`/`followers` deprecated | 01d, E |
| 145 | Chartmetric pricing | Manager $40/month billed yearly | 01d, E |
| 146 | Open-Meteo | free tier non-commercial (CC-BY 4.0); commercial use requires a paid licence | 01d, E |
| 147 | NOAA / NCEI (ISD, CDO) | US public domain | 01d, E |
| 148 | GTFS / GTFS-RT and the Mobility Database | open licences per agency; uneven real-time coverage | 01d, E |
| 149 | ESPN scoreboard/standings endpoint | `site.api.espn.com` JSON, keyless, verified responding; undocumented, so a commercial product needs a licensed feed | 01d, E |
| 150 | Wikidata | CC0, SPARQL and dumps | 01d, E |
| 151 | OpenStreetMap | ODbL, Overpass and dumps | 01d, E |
| 152 | Official venue seating charts | per-venue HTML or PDF; the only route to seat coordinates and it is a human task per venue | 01d, E |
| 153 | FRED / ALFRED and BLS | public domain; use ALFRED vintages, not the revised series | 01d, E |
| 154 | Census and DMA tables | Census free; the DMA rank source not stated in the citing finding | 01d, E |
| 155 | MusicBrainz | MetaBrainz, free; licence terms not read | 01d, E |

### 22.5 Competition and event material

| # | Source | Locator | Used by |
|---|---|---|---|
| 156 | MLH Solana Hackathon event page: AI Track criterion verbatim, the five idea lists, "Solana Agent Skills" in the hacker resources, the "Build with AI on Solana" workshop, the Sunday deadlines | https://events.mlh.com/events/15200-solana-hackathon, fetched 2026-11-07T11:04Z | 02ai |
| 157 | The same event's public page: prize amounts as rendered and the submission counter reading 7 at 11:04Z | https://www.mlh.com/events/solana-hackathon, same fetch | 02ai |

### 22.6 Checked and not used

Recorded so that no later reader thinks they were missed. None of these is evidence for anything in this
document:

| # | Source | Why not used |
|---|---|---|
| 158 | arXiv:2507.23767 (Landers, closed-form beta estimation from sparse statistics) | uses a SeatGeek dataset for distribution recovery and event classification; not a time path |
| 159 | seatdata.io, "best time to buy concert tickets" (2026) | unpublished commercial analysis claiming 307,727 sales and a 29% day-of saving; not inspectable, not audited |
| 160 | UNC undergraduate honours thesis, Price Dynamics in Live Event Ticket Sales: Evidence from College Football | grey literature; its one qualitative finding is consistent with the rest and is not relied on |
| 161 | A ticket-market paper attributed to "Hakes" in the programme brief | no such paper could be identified; nothing is cited rather than guessed |

**Counts.** 124 peer-reviewed papers, working papers and books; 7 regulatory or legal items; 3 contract and
platform items; 22 API, data-provider and terms items; 2 competition and event items; 4 checked and not used.
**158 distinct sources are cited and 4 are listed as checked and not used, 162 entries in total.**
*(As first printed this read 123 / 157 / 161; Ahn & Lee adds one cited source, so 123 + 1 = 124 cited entries in
that section, 157 + 1 = 158 cited sources, 161 + 1 = 162 entries, and 124 + 7 + 3 + 22 + 2 = 158.)*

Changed in place on 2026-11-07T14:00Z: the five `Used by` cells and the missing entry. The previous values of
the five cells were "01c, 02d, 06" (Artzner), "01b, 01c, 02a, 02e" (Ekeland et al.), "01a, 01b, 01c, 02a,
02c, 02d, 02e" (Gallego & van Ryzin), "01b, 01c, 02c" (Lakkaraju et al.) and "01a, 02d, 02e" (UK DBT note).

**CORRECTION 2026-11-07T14:00Z, R2-28 — the bibliography is corrected against the citations the findings carry.**
Five `Used by` cells named a finding that does not cite the source, and one cited source was missing. Nothing
is deleted. (1) **Artzner et al. (1999)** said "01c, 02d, 06"; `06-validation-protocol.md` uses CVaR and never
cites Artzner, so the cell is now "01c, 02d", which are the two files that quote it. (2) **Ekeland, Heckman &
Nesheim (2004)** said "02a"; `02-a-price-paths.md` does not cite it, and `03-a-interactions.md` does, so the cell
is now "01b, 01c, 02e, 03a". (3) **Gallego & van Ryzin (1994)** said "01a"; `01-a-market-structure.md` does not
cite it, and `03a` does, so the cell is now "01b, 01c, 02a, 02c, 02d, 02e, 03a". (4) **Lakkaraju et al. (2017)**
said "01b, 01c, 02c"; the phrase and the paper are in `01-b` and `02-c` and not in `01-c`, so the cell is now
"01b, 02c". (5) **The UK DBT analytical note** said "01a, 02d, 02e"; `02-e` cites no DBT material and `03-a`
does, so the cell is now "01a, 02d, 03a". Each cell was checked by searching every file under
`records/findings/` for the author's surname or the note's short name, and a file is listed only if the source
appears in it.

(6) **Ahn & Lee (2007)** is added as entry **1a**: *Lifecycle demand for Major League Baseball*, *International
Journal of Sport Finance* 2(2):79-93, doi:10.1177/155862350700200203, cited at `02-d-elasticity-fees-optimum.md`
lines 839-840. It sat in the gap between Abadie and Aigner, so it is numbered `1a` and placed in alphabetical
order rather than renumbering the forty rows below it; the section's counts therefore become **124
peer-reviewed papers, working papers and books** and **162 entries in total** (123 + 1 and 161 + 1, the same
"157 cited plus 4 checked and not used" split with Ahn & Lee moving into the cited group). The header's claim
"No source appears here that no finding cites" was already true and still is: the defect was the converse, a
cited source absent here.

---

## Closing note

This document is the Phase 8 deliverable, and its most important content is negative: a precise account of
what this observation set cannot identify, the mathematics of the parts it can, the data that would change
that, and an engine that refuses rather than guesses.

**Three sections are marked thin in place**: 11, because the only interval available is a declared width and
no coverage number can exist; 13, because a risk functional needs a profit distribution and the elasticity
that would produce one is not identified; and 19, because there is no real ledger to measure performance
against. **Five more are partial in a stated way rather than thin**: 9 and 10 report bounds and a refusal
where a reader would want an estimate, and say which is which; 12 reports a set and a boundary rather than a
point optimum; 15 is a protocol that nothing has been run against; and 16 composes the 18 recorded
formulations (20 entries including two sub-formulations), which the model registry maps onto 56 assessed
models of which 13 carry the SHIP role and several of those are specified and not built.

The three sentences a reader should carry away are these: **the level of value is not identified from this
record; the price response is not identified from this record; and nothing in this programme has been
validated against a ticket market, because no ticket market data exists here.**

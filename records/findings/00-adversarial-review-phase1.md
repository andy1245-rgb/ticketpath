# 00 — Adversarial review of the Phase 1 findings

**Status:** complete (first pass, read-only).
**UTC:** 2026-11-07T11:09Z.
**Agent:** independent adversarial reviewer. I did not write any file under review.
**Scope:** the three load-bearing claims in `01-a-market-structure.md`,
`01-b-identifiability.md` and `01-d-external.md`, read against `RESEARCH-PROGRAM.md` §4
(evidence classes) and Phase 8 (the audit questions), plus the error classes a reviewer is
expected to find: an unsourced number, a class label that does not fit, a summary contradicted
by its own body, a citation that does not support its sentence, and a hypothesis stated as a
finding.
**Versions reviewed:** `01-a` mtime 2026-11-07T08:42:11Z (24,600 bytes); `01-b`
2026-11-07T08:52:13Z (34,046 bytes); `01-d` 2026-11-07T08:40:17Z (31,773 bytes). The directory
changed during the pass: `01-c-methods.md`, `02-c-sale-hazard.md` and `02-e-cold-start.md`
appeared at 11:00Z. They are **not** reviewed here. Where `02-c` bears on claim 1 it is named
and left out of the verdict; its own summary confirms 01-b's crux and does not reach the
cap-pinned route discussed below.

**What I did not review.**
- `01-c`, `02-c`, `02-e`, and the night brief/log/queue. They are later work, not Phase 1
  findings.
- The six records A–F in full. I read `00-data-situation.md`, `F-decision-log.md`,
  `README.md`, and the parts of `C` and `E` the three files quote; I did not audit the
  registries row by row.
- The frontend beyond `lib/mock/` and the wire contract as quoted. I recomputed the fixture
  counts; I did not audit a route, a component or `API_CONTRACT.md`.
- Any engine. There is none to run, so no estimator, simulation or backtest was executed.
  Every statement below about what an estimator would do is an argument from the schema and
  the cited method, not a measurement.
- Citations: I spot-checked the load-bearing ones (Sweeting 2012, Leslie & Sorensen 2014,
  Ekeland–Heckman–Nesheim 2004, Prentice 1986, He & Lin, Working 1927, Fine & Gray 1999,
  Ge–Humphreys–Zhou 2020, Courty & Pagliero 2012, Shapiro & Drayer 2012, Budish & Bhave 2023,
  the NSW Fair Trading page, the Federal Register record, the DBT analytical note, the UK
  press release, the Spotify API reference, and both Google robots.txt files). I did **not**
  verify the Aigner DOI, the Irish Sale of Tickets Act (the gov.ie page returns 403 to this
  host), the SDNY verdict (no docket read), the Get Protocol count, the Ticketmaster
  price-field removal, or the X/Reddit/Open-Meteo pricing. I could not extract the body of
  Sweeting's PDF, so the 13/18/40% within-seller declines, the 113,186 structural sample and
  the 77.2% figure are **unverified**, not refuted.
- The fixture generator's intent. I recomputed the counts and the cap behaviour; I did not
  establish provenance.

---

## 1. The three claims, in order of consequence

### Claim 1 — 01-b: the sale-probability curve is not identified

**The claim, quoted.**

> "Of the six target quantities, **one is honestly buildable today, two are set-identified with
> bounds we can actually compute, and three are not identified at all.** … A time-and-ticket-
> conditional baseline intensity is estimable now; a price-response multiplier is not, and no
> modelling choice recovers it." — `01-b` lines 15–21.

> "**T3** | Sale hazard as a function of price | **Not identified.** Only
> $\lambda(t\mid p)\cdot\Pr(\text{ask}=p\mid\text{listed},t)\cdot\Pr(\text{listed}\mid t)$
> is. The unconditional intensity $\lambda_0(t)$ **is** identified." — `01-b` line 52.

> "The price response is not recoverable." — `01-b` line 157.

**Why it is load-bearing.** T3 is the input that 01-b says the primary optimum needs
("Its two inputs are T3 and T4, both non-identified", `01-b` line 198), and it is the object
behind the product's third advertised output, "the probability it actually transacts at a
given price" (`AGENTS.md`). If the claim is right, one of the four outputs is not buildable
and the primary optimum is a set, not a point. If it is wrong, the engine can estimate a
demand response.

**The attack.**

*1. The argument is correct for the full curve.* The observed rate of sales at price $p$ is
the product of three factors: the sale hazard at $p$, the density of asks at $p$ among listed
tickets, and the probability a ticket is listed at all. The ledger observes only the left
side, and the mark is recorded only on the success branch. A Heckman-style selection
correction needs an exclusion restriction that the schema does not contain; inverse-probability
weighting on the ticket population fixes the exposure denominator but not the missing ask;
partial-identification bounds from the observed marks alone are vacuous without a bound on the
number of unobserved listings. The auction/search literature does not rescue it either: from a
single transaction-price distribution, any monotone hazard multiplied by a sufficiently
flexible ask density is observationally equivalent, so the two cannot be separated without the
posted-price distribution. On the general curve, 01-b is right.

*2. It misses one legitimate route: the cap pins the mark at the ceiling.* On an event whose
`resalePriceCapBps` binds, the market clears at the ceiling, and the mass of listings at the
cap has the same ask, $a=f_j(1+c_e)$. The cap is observed for **every** ticket in the event,
not only for the tickets that sold; `faceValueLamports` is observed for every ticket. So the
ask density $\pi$ in 01-b's own decomposition has a mass point at $a$, and the observed rate at
the ceiling is
$\lambda_{\text{obs}}(a,t)=\lambda(t\mid a)\,\pi(a\mid\text{listed},t)\,s(t)$.
The left side is identified; the hazard at the cap is not, because the fraction of the risk set
at the cap, $\pi(a)$, is unobserved. If the cap binds and the mass at the cap is the dominant
ask, $\pi(a)$ may be close to one, but it is not observed; the hazard is identified only up to
$\pi(a)s(t)$. What the cap route adds is a **price-indexed rate at the ceiling** and a bound on
the hazard if $\pi(a)$ can be bounded; what it cannot add is the slope or the hazard alone.
Across events and tiers with different caps, it traces the rate at the ceiling — one point of
the price-response per event, not the slope.

Even before the cap, the left side of 01-b's own formula is a **mark-conditional** intensity:
the rate of transactions at each observed markup per ticket-time. That is a price-indexed
object, not an unconditional one. The summary's "only an unconditional intensity" ignores its
own left side. The cap route makes the mark at the ceiling observable for the risk set, so the
ceiling point of that intensity is interpretable as the ceiling rate; it does not identify the
hazard, but it is more than the unconditional intensity.

A second, weaker route is the cap as an instrument for the ask when the cap is set by law or
platform default (a LATE at the ceiling, with a questionable exclusion restriction because the
cap also affects listing supply). A third is repeat-sale durations at a known ask, but that
sample is selected on selling twice and the ask between hops is unobserved.

This matters because `01-b` §4.4(ii) already uses the cap to bound the **value** distribution
("a lower bound on the survival function of willingness to pay at each cap level", lines
190–192). That is a value object, not a rate object, and it does not by itself contradict the
summary. The step the report does not take is to use the cap to make the **mark** at the
ceiling observable for the risk set. Once that step is taken, the summary's "only an
unconditional intensity is identified" is too strong: the *observed rate* at the ceiling is
identified (it is the mark-conditional intensity at $a$), even though the *hazard* at the
ceiling is not, because $\pi(a)$ and $s(t)$ are unobserved. The slope of the price response
remains unidentified.

*3. It does not matter for the primary price, which is the product's headline.* The organizer
chooses $p_0$; the payoff is $p_0 \times Q_{\text{primary}}(p_0)$; the inputs are the primary
demand bracket (T4b), the value signal (T1/T4a), the cap, and the fee model. T3 is the
**secondary** sale hazard. It is an input to a reseller tool or a secondary-market simulator,
not to the primary price. `01-b` line 198 ("Its two inputs are T3 and T4") is the error: the
primary optimum's demand input is the primary sale process, not the resale sale process. If the
engine is sold as an organizer pricing tool, the crux does not bind the headline. It binds one
of four advertised outputs — the price-specific transaction probability — and that output
should be relabelled as a bound or dropped. The report calls T3 "the crux" without saying which
output it is the crux *for*.

*4. The demand input it says the optimum has is itself not as identified as claimed.* T4b is
"set-identified from primary sell-through" (`01-b` line 56), but the Tobit in §4.4(i) requires
the primary face to be exogenous to the demand shock. The organizer sets face before demand is
realized, but plausibly on expected demand; the observed sold-out/unsold indicators are
equilibrium points, not a demand curve. This is precisely the Working (1927) simultaneity that
01-b applies to the resale ask but not to the primary face. The sold-out/unsold statements are
valid one-sided bounds *at the observed prices*; they do not trace a demand schedule as price
varies without an instrument. The report's "highest-value finding" is a set of bounds, not a
demand experiment.

**The strongest counter-argument to my attack.** The cap-pinned route is conditional on the
cap binding and on compliance. If the cap does not bind — the fixture never reaches it, and
the real platform's cap behaviour is unknown — the ask is not pinned and the route yields
nothing. The report's T3 is about the general case, and its "price-response multiplier" is a
*slope*; the cap route identifies a *rate*, not the slope, and not even the hazard alone,
because $\pi(a)$ is unobserved. The central sentence survives for the slope; what falls is
only the word "unconditional".

The report also already restricts its bounds to "wherever the resale ceiling binds" in §1, so
it is not claiming the general curve. On the "does it matter" point, the product spec does list
the sale probability as an output, so the crux does bind the product as specified; my argument
only shows it does not bind the primary-price output. And the body's §6 is more careful than the
summary: it says the engine is "risk-aware, not point-optimal", which is consistent with using
bounds rather than a curve.

**Verdict: STANDS-WITH-NARROWING.**

- The identification argument for the *full* curve **stands**.
- "Only an unconditional intensity is identified" **falls**: the left side of the T3 formula
  is already a mark-conditional intensity, and the cap makes the ceiling point of that
  intensity observable. The hazard at the ceiling is identified only up to $\pi(a)s(t)$, not
  alone. §4.4(ii) is a related WTP **value** bound, not the same object.
- "The primary optimum inherits T3's width" **falls**: T3 is the secondary hazard; the primary
  optimum's binding inputs are the primary demand bracket (T4b) and the value signal, and T4b's
  own endogeneity is the more serious problem.
- The "crux" label **stands only for the price-specific sale-probability output**, not for the
  primary-price recommendation.

**Narrowed wording.**

> "The full price-response curve $\lambda(p\mid x,t)$ is not identified from a completed-
> transaction ledger: the ask of the risk set is unobserved and the observed sale rate is the
> product of the hazard, the ask density and the listing probability. What is identified is
> (i) the unconditional transaction intensity per ticket-time, (ii) the competing-risks split,
> (iii) the joint mark–time intensity, and (iv) on events where the cap binds, the observed
> rate at the ceiling and one-sided bounds on willingness to pay at each observed cap level;
> the hazard at the ceiling is identified only up to the unobserved fraction of the risk set
> at the cap and the listing probability. The price-specific sale-probability output is a bound,
> not a curve. The primary-price recommendation does not rest on that curve; it rests on the
> primary demand bracket and the value signal, and the claim that the primary optimum inherits
> T3's width is withdrawn."

---

### Claim 2 — 01-a: the cap biases recorded markups down, and is the central fact

**The claim, quoted.**

> "the compliance behaviour a cap induces (side payments, wallet handoff, bundling) makes the
> recorded markup a biased-down estimate of value exactly where value is highest. An estimator
> fitted to uncorrected capped markups will under-price the best inventory. That, not
> forecasting, is the central structural fact of this project." — `01-a` lines 22–26.

**Why it is load-bearing.** It is the justification for the report's "for estimation" and "for
pricing" prescriptions (`01-a` §6), and it is the reason the engine is supposed to treat capped
markups as bounds. If the sign or the size is wrong, the engine's value output is wrong in the
opposite direction on the inventory that matters most.

**The attack.**

*1. The mechanical truncation is down; the causal sentence is not established.* For a ticket
that sells at a binding cap, the recorded price is the cap and the buyer's $V \ge$ cap; the
recorded markup is a lower bound on *that buyer's value*. That is class C and it stands. But
the sentence says the **compliance behaviour** "makes" the recorded markup down-biased. The
four channels — side payment, wallet handoff, bundling, flight to unregulated channels — are
labelled "all class D with a clear test" in `01-a` §6, and no measurement of any of them is in
the file. The summary states a class-D hypothesis as an established finding. That is a §4.3
violation independent of whether the hypothesis is true.

*2. The correction is not one-signed.* The report asks the reader to add the missing tail. Three
independent channels can move the correction the other way, and none is resolved by the schema:

- **Fee basis.** The record has no fee, royalty or settlement field (Gap 4). `01-a` itself says
  resale fees are two-sided and "the price" is ambiguous by 20–40% (`01-a` line 47), a range
  with no source and no class. If `priceLamports` is the buyer's gross, a 30% recorded markup on
  a 20% seller-side fee is an 8.3% net markup; the cap correction raises the estimate while the
  fee correction lowers it. The fee wedge is the same order as the cap premium in the fixture
  (caps are 30–120%), so the net sign is indeterminate. This is a concrete wrong-sign case: a
  capped event with a high cap and a high seller-side fee can have a *lower* net value than an
  uncapped event with a low fee, while the recorded markups rank them the other way.
- **Composition and selection.** If high-value tickets leave the platform (wallet handoff,
  off-platform settlement), the observed sample is selected on low value and the cross-event
  average is down. If the organizers who enable resale with a cap are the ones with hot events,
  the observed sample is selected on high value and the average is up. The within-event
  truncation is down; the cross-event sign is not determined.
- **The cap's own composition effect.** `01-a` §3(2) cites He & Lin: a stringent cap can push
  high-price sellers out, reduce seller-side competition and *raise* the average transaction
  price (class C). So the observed average can rise after a cap even though every individual
  recorded price is a lower bound. An estimator calibrated on the average will get the marginal
  ticket wrong, in either direction.
- **Bundling.** A ticket at face plus a priced ancillary makes the recorded ticket markup down
  but the bundle total up. An estimator that imputes the bundle price overstates the ticket's
  value; one that uses the ticket leg understates it. The report does not say which object is
  being estimated.

*3. The ranking inversion is the more important error, and the report gets it right in the body
but not in the summary.* `01-a` §3(3) says "fit on observed markups and you conclude the hottest
events are the *least* valuable." That is a ranking inversion, not merely a level bias. The
summary's "under-price the best inventory" is a level statement; the ranking inversion is
worse for an organizer deciding which tickets to reprice. The correction must be a bound and a
dominance criterion, not a point estimate with a tail added.

*4. "The central structural fact" is overstated and conflicts with 01-b.* The missing listing
exposure is the first constraint: it is what makes T3 unidentifiable in general, and both
`00-data-situation.md` Gap 1 and `01-b` §4.3 put it first. The cap is the second constraint.
`01-b` calls T3 "the crux"; `01-a` calls the cap "the central structural fact"; `F` records
neither conflict, which `records/README.md` forbids ("Record conflicts, do not resolve them
silently"). Moreover `01-b` §4.5(ii) shows the cap is proportional and the band is scale-free,
so the cap's absolute level does not enter the seller's relative pricing problem. It is a data
truncation and a resale-market constraint, not the central economic fact of the primary-price
engine. The central economic facts are the ~5% resale rate and the coarse primary pricing; the
cap is a policy overlay.

*5. The floor/ceiling inversion.* The cap price is a **floor on value** (a sale at the cap
implies $V \ge$ cap) and a **ceiling on the buyer's outside option** (a buyer can substitute to
the capped resale market), which constrains the primary price without strictly capping it. The
summary's "the cap is the central fact" invites the inference "raise the primary price to the
cap". `01-a` §6 is better: "the primary optimum is set by primary sell-through and demand
elasticity." The summary and §6 disagree in emphasis, and the summary is the sentence a reader
will carry.

*6. The report's own fix has an unidentified parameter.* `01-a` §6 prescribes fitting a latent
$M^*$ with observation $\min(M^*, \text{cap})$ plus a leakage probability $q(\text{cap},
\text{event})$, estimated from dark tickets and bundled listings. That is the right structure,
but $q$ is not identified without exactly the dark-ticket and bundling data the report says is
missing. Until then $q$ is a sensitivity parameter, not an estimate; the honest output is the
lower bound and the width, not a corrected point.

**The strongest counter-argument to my attack.** The truncation of the *recorded price* at the
cap is mechanical: if the cap binds, no recorded price above it exists, so any statistic of the
recorded price is at or below the cap. For a ticket that sold at the cap, the buyer's $V \ge$
cap; the recorded markup is down for the buyer's value, which is the object the report is
talking about. The fee and composition channels are about the *seller's net* and the *cross-
event average*, not about the buyer's value of a cap sale. The report's §3(3) says "the recorded
markup is a *lower bound*", which is the right modal; the summary's "makes" is a compression,
not an analytical error. The compliance channels are class D in §6, so the report does label
them; the summary simply inherits the label's confidence. And the "central fact" is a
judgement about the data problem, not a claim about the primary-price economics; §6 is explicit
that the optimum is set by sell-through and elasticity.

**Verdict: STANDS-WITH-NARROWING.**

- The mechanical truncation direction **stands** for a ticket sold at a binding cap.
- "The compliance behaviour makes the recorded markup down" **is class D, not a finding**; it
  may be true, but it is not measured.
- The correction's sign and size **do not stand as a one-sided claim**: the fee basis, the
  composition of the observed sample, the cap's own seller-exit effect, and bundling can all
  move the average or the seller's net the other way.
- "The central structural fact" **falls**; the missing listing exposure is the first
  constraint, and the cap is the second.

**Narrowed wording.**

> "On an event whose resale cap binds, a markup computed from a recorded sale at the cap is a
> lower bound on that ticket's value, and the gap is largest where demand is strongest; a naive
> estimator fitted to uncapped markups will under-price the best inventory and can invert the
> ranking. The size of the gap, and the sign of any correction to the average or to the seller's
> net, are not established: they depend on which side of the recorded price the unobserved fees
> sit, on which tickets leave the platform, and on the cap's own selection. The correct output
> is a bound, not a corrected point, until the leakage rate is measured. The cap is the second
> structural constraint; the first is the missing listing exposure."

---

### Claim 3 — 01-d: the clock removes six variables from the primary-price problem

**The claim, quoted.**

> "The decisive filter was not availability and not correlation: it was **the clock**. This
> engine makes two different decisions at two different times — a primary price set before
> on-sale, and a reprice taken while the event is in market — and a variable can only enter if
> its value is knowable *at the decision time*, not merely at the event. That one test removes
> weather forecasts, injuries, transfers, competing events, added tour stops and support-act
> announcements from the primary-price problem entirely, because all of them resolve after the
> on-sale that the primary price is fixed at." — `01-d` lines 14–19.

**Why it is load-bearing.** It is the admission test for the whole variable registry, and it is
the reason six of the seventeen rows are ranked low or rejected. If the claim is too strong, the
reprice is missing its best variables and the engine systematically under-uses information.

**The attack.**

*1. The file contradicts itself.* The opening sentence says the engine makes **two** decisions,
including "a reprice taken while the event is in market". The body then puts the six variables
back for the reprice: V8 says competing events are "knowable at `t` but not knowable at on-sale"
(`01-d` line 69); V9 says "Use only stops announced by `t`" (line 70); V10 says "For most events
this resolves **after** the primary on-sale, so it is a repricing variable, not a pricing one"
(line 71); V12 says "use the forecast available at `t`" (line 73). The summary's "entirely" is
false for the reprice, and the body knows it. The only way to save the sentence is to define
"the primary-price problem" as the pre-on-sale price only; the file never does that, and its own
opening uses "the engine" for both decisions.

*2. The decision time is not fixed before on-sale for every decision the product supports.*
`01-a` §1 lists primary dynamic / "platinum" / "in demand" pricing as a live channel, revised as
demand arrives. The programme's Phase 5 asks for a dynamic pricing policy ("if justified").
`AGENTS.md` output #2 is "how that value moves over the remaining horizon", which is an
in-market forecast. Holdback release, cap changes, resale enable/disable and verified-wallet
changes are also in-market organizer decisions. The premise "the primary price is fixed at
on-sale" is true for the static case only. The claim should state that assumption.

*3. Even for the initial price, the clock removes the realisations, not the variables.* The
organizer setting a price months ahead knows the *distribution* of future shocks: injury risk,
weather seasonality, the probability of added stops, the possibility of a competing event. A
risk-averse organizer prices the variance; a risk-neutral one prices the expected shock if it is
anticipated. V9 says "Use only stops announced by `t`" — many stops are announced before
on-sale. V10 says "For most events", not all; a playoff or tournament state can be known before
on-sale. The correct statement is: the realised values are excluded from the initial price; the
ex-ante distributions can enter as risk terms. The report's own V10 mechanism says "a shock to
expected quality *and to its variance*" (line 71), which is exactly the risk-term admission the
summary denies.

*4. "Transfers" is ambiguous.* In V10 it means player transfers. In the schema, `transfer` is a
ledger row, and V5 makes ticket transfers a knowable-at-$t$ feature. The summary's "injuries,
transfers" can be read as ticket transfers, which would contradict V5. Say "player transfers".

*5. The weather row contradicts the summary.* V12 is priority 3, with a mechanism and a source.
If weather is "removed entirely" from the primary-price problem, its priority is 0 or it is
rejected. If it is priority 3, it is in the engine. The table and the summary disagree. The same
is true of V8 and V9: they are priority 2, not rejected.

*6. "The decisive filter was the clock" is too strong for the whole set.* The rejection table
rejects Google Trends, Reddit and Spotify on licence, airport proximity on fixed effects, school
terms on redundancy, and tourism flows on collinearity. The clock is decisive for the six
time-resolved variables, not for the seventeen. The summary's "not availability and not
correlation" is contradicted by the table, where availability and licence do most of the work.

*7. A time-index inconsistency with 01-b.* V5 says every feature must be computed on `entries`
filtered to `occurredAt ≤ t` (`01-d` line 66, repeated at line 118). `01-b` §4.6(c) says
`occurredAt` is ISO-8601 at unspecified granularity while `slot` is strictly monotone, so "any
hazard model must derive its time index from `slot` — a small point with a large failure mode,
negative durations" (`01-b` line 252). The implementation instruction in 01-d should filter on
`slot`, not `occurredAt`, or the two files will produce different as-of sets.

**The strongest counter-argument to my attack.** The file's opening explicitly names the
reprice, so the author is not ignorant of it; the body's V8/V9/V10/V12 are the reprice's
admission set, and the analysis is therefore present, only compressed out of the summary. The
product's headline may be the static pre-on-sale price; the reprice is a Phase 5 option ("if
justified"), and if the current deliverable is static, the claim is true for the decision the
engine actually makes. "Transfers" in a sports context clearly means player transfers; the
ticket-transfer reading is pedantic. The ex-ante distribution of shocks is a risk term, but the
report's engine may be risk-neutral, in which case the realisations are indeed excluded; the
claim is about features, not about risk pricing. And the clock is the *decisive* filter in the
sense that it is the one that eliminates the most candidate variables; the other filters are
secondary.

**Verdict: STANDS-WITH-NARROWING.**

- The clock filter for the **static pre-on-sale price** **stands**.
- "Entirely" **falls**: the reprice admits the six variables, and the body says so.
- "The decision time is fixed before on-sale for every organizer decision" **falls**: dynamic
  primary pricing, holdback release, cap changes and the value-path output are in-market.
- "The decisive filter for the whole set" **falls**: the rejection table is mostly licence,
  mechanism and redundancy, not the clock.
- The ex-ante distributions of the six variables can enter the initial price as **risk terms**;
  only their realisations are excluded.

**Narrowed wording.**

> "For the static pre-on-sale primary price, the realised values of weather, injuries, player
> transfers, competing events, added tour stops and support-act announcements are not knowable
> and do not enter as features; only their ex-ante distributions can enter, as risk terms. For
> the in-market reprice, several of them are knowable at $t$ and enter: injuries and player
> transfers that have resolved, competing events and tour stops announced by $t$, support-act
> announcements, and weather forecasts inside the forecast horizon. The engine supports both
> decisions, so the variables are excluded from one and admitted to the other. The clock is the
> decisive filter for the time-resolved variables; the other variables fail on mechanism,
> redundancy or licence."

---

## 2. The pattern behind the three verdicts

All three claims are **stronger in the body than in the summary**. In each file the body carries
the qualification — `01-b` §4.4(ii)'s cap bounds, `01-a` §3(3)'s lower bound and §6's "the
optimum is set by sell-through", `01-d`'s V8/V9/V10/V12 — and the summary compresses it into an
absolute ("no modelling choice", "the central structural fact", "entirely"). The
adversarial finding is therefore not that the analysis is wrong; it is that the
**headline sentences are the least defensible sentences in the three files**, and they are the
ones a reader or a downstream agent will carry. The fix is editorial and cheap: make the
summary carry the body's conditional.

This is also why the prior ledger-verification pass found the class discipline "uneven in a
specific, predictable way": the unclassed material is the material a reader would act on. The
same pattern holds for the modalities: the body says "lower bound" and "class D"; the summary
says "makes" and "central fact".

---

## 3. Error list

Severity: **H** = changes a load-bearing conclusion or violates a programme rule; **M** =
changes a number, a class or an instruction a builder would follow; **L** = presentation,
citation hygiene, or a label that does not travel.

| # | File / line | Error | Severity | Status |
|---|---|---|---|---|
| 1 | `01-b` 86 | "only 90 of 128 fixture tickets ever sell". The fixture has **90 sale rows**, **49 tickets** with ≥1 sale, **79** with none, **27** with ≥2 sales, one ticket with 4. The 90 is a row count read as a ticket count. The sentence is load-bearing for the T1 selection argument and breaks the programme's "no number from `lib/mock/`" rule. | **H** | Corroborated (prior pass) and recomputed |
| 2 | `01-b` 153 | "a point mass at 'will never be offered' fits 79-of-128 better than a long tail". A fit claim on synthetic fixtures, presented as support for a cure component; no likelihood or test is given. The programme allows fixtures only to exercise code paths. It is SIM at best, not C. | **H** | New |
| 3 | `01-b` 247 | "If gifts are coded as sales, observed resale propensity is **too high** … so 79-of-128 is an **upper** bound on the never-offered fraction." The conclusion is right for the **current** coding, where `transfer` is not a sale: the 79 no-sale tickets include 5 gift-only tickets, so 79 is an upper bound on the 74 never-changed-hands. The stated conditional is backwards: if gifts were coded as sales, 79 would no longer be an upper bound. The reason given does not support the bound. (The 5/74 are fixture illustrations of a schema path, not market evidence.) | **M** | New |
| 4 | `01-b` 198 | "Its two inputs are T3 and T4, both non-identified, so the optimum inherits their width." T3 is the **secondary** sale hazard; the primary optimum's demand input is the primary sale process (T4b). The sentence is the load-bearing link between the T3 crux and the primary price, and it is wrong. | **H** | New |
| 5 | `01-b` 96 | "T1's level needs one exogenous reference price, and the observation set contains none." The set contains a **censored** anchor: `faceValueLamports` plus the sold-out/unsold indicator, which §4.4(i) itself uses as a demand bracket. It is not exogenous, but it is not "none". The correct statement is that the level is bounded by primary sell-through, not point-identified. | **M** | New |
| 6 | `01-b` 93–96 | The Ekeland–Heckman–Nesheim citation is attached to the wrong proposition. EHH prove identification **up to affine transformations from data on demand and supply** — a positive result, with a condition 01-b states correctly in §4.4. The affine indeterminacy is in preferences and technology, not in the price level. The citation is ornamental: it supports a different, positive result, not the claim that the resale value level is unidentified. | **M** | New |
| 7 | `01-b` 36–38 | "This is **informative observation times** / **informative censoring** … (Lagakos 1979)." The problem is a **mark observed only on cases**, not an informatively censored event time; the event time is observed for every ticket (sale, redemption or event end). Lagakos is about right-censoring of the failure time. The right citation for the missing-ask structure is Prentice 1986 (case-cohort), which the report also uses. | **M** | New |
| 8 | `01-b` 149–150 | "treating redemption as censoring **inflates** the sale hazard because it removes tickets for reasons correlated with demand". The direction is asserted, not derived: if redeemed tickets have a lower sale hazard, removing them raises the remaining hazard; if they have a higher sale hazard, it lowers it. Fine & Gray supports the competing-risks correction, not the sign. | **M** | New |
| 9 | `01-b` 15, 52–59, 198 | The "six target quantities" / "one buildable, two set-identified, three not identified" partition cannot be mapped onto the table, which has eight rows (T1, T1′, T2, T3, T4a, T4b, T5, T6). If T4a/T4b are one target and T1′ is a sub-case, the count is six; the summary never says so. | **L** | New |
| 10 | `01-b` 21, 157 vs 190–192 | "Only an unconditional intensity is identified" / "the price response is not recoverable" vs the mark-conditional left side of 01-b's own T3 formula. §4.4(ii) is a WTP **value** bound, so it does not by itself contradict the summary; the missing point is that the observed rate is already mark-conditional, and the cap makes the ceiling point of it observable. The hazard at the ceiling is not identified alone ($\pi(a)s(t)$), so the slope sentence survives; the summary's "only" does not. | **M** | New |
| 11 | `01-b` 21, 55 | "the at-risk denominator is observed" vs the unobserved listing probability $s(t)$ in the T3 formula. The ticket-time denominator is observed; the **listing** denominator, which is the relevant one for a sale hazard, is not. | **L** | New |
| 12 | `01-b` 54 | The summary's "path identified only for repeat-traded tickets" and "linear trend not identified" are correct, but the table does not say how many repeat-traded tickets exist (27 in the fixture, illustration only; unknown on the platform). A set-identification claim with no sample-size statement is not actionable. | **L** | New |
| 13 | `01-b` 58 | "width = union of the T3 and T4 widths" (T5 row). The identified set of an optimum is the image of the input sets under the optimisation map, not the union of their widths. The "union" is a heuristic, not a result. | **L** | New |
| 14 | `01-a` 22–24 | "the compliance behaviour … makes the recorded markup a biased-down estimate" — the four channels are class D in `01-a` §6 ("all class D with a clear test"), stated as fact in the summary. §4.3 violation. | **H** | New |
| 15 | `01-a` 26 | "That, not forecasting, is the central structural fact of this project." Unclassed, contested by `01-b`'s T3 crux, not recorded in `F`. `README.md`: "Record conflicts, do not resolve them silently." | **M** | New |
| 16 | `01-a` 13 | "the gap is real but modest once the whole market is measured". Leslie & Sorensen observe only **half** of resale activity; their own text says the 1.4% is "even if we are accounting for only half of resale activity". The whole market is not measured, and the true prize could be ~2.8% before the counterfactual. | **M** | New |
| 17 | `01-a` 132–133 | "1.4% of primary revenue, **even after scaling** for the ~50% of resale the authors do not observe". The paper does **not** scale; 1.4% is the observed half. The sentence overstates the precision of the lower bound. | **M** | New |
| 18 | `01-a` 24–26, 119 | The summary says "under-price the best inventory"; §3(3) says the naive estimator "conclude[s] the hottest events are the *least* valuable". That is a **ranking inversion**, a stronger and more useful finding than the summary's level bias. The summary should carry it. | **L** | New |
| 19 | `01-a` 47 | "Fees on resale are *two-sided*, so 'the price' is ambiguous by 20-40%". A quantified range with no source, no class, and no statement of which side `priceLamports` is on. It is also the independent sign indeterminacy that undercuts the cap-bias claim. | **M** | Corroborated (prior pass) |
| 20 | `01-a` 50, 304 | "16 CFR Part 464, 90 FR 2166". The Federal Register document (2024-30293) starts at **90 FR 2066**; 2166 is the end page and the eCFR "Source" line. The part number and effective date (2025-05-12) are right. | **L** | Corroborated; prior pass's "digit transposition" is imprecise |
| 21 | `01-a` 112 | "He & Lin (*Marketing Science*, 2025)". Crossref gives *Marketing Science*, issued **2026-05**; the SSRN preprint is 2023. The claim the paper supports is correct; the year as printed is not the published record. | **L** | Corroborated (prior pass) |
| 22 | `01-a` 131–133 | "≈£184 gross average, ≈£269 per resale ticket inclusive of all fees". £184 = £350m / 1.9m; £269 = £404m / 1.5m, a different flow in the same DBT note. The sentence splices two baselines as if they were a before/after pair. | **M** | Corroborated (prior pass); verified against the note |
| 23 | `01-a` 238 | "Gap 5" does not exist in `00-data-situation.md`; the audit numbers four gaps and lists two smaller ones without numbers. A reader following the reference finds nothing. | **L** | Corroborated (prior pass) |
| 24 | `01-a` 50 | "class A for the regulation". A statute or regulation is a legal fact, not "ticket-market empirical evidence" under §4.3's class A definition. It needs a legal/primary-source label or an explicit extension of the vocabulary. | **L** | New |
| 25 | `01-a` 131–135 | The 3.4% top-10% counterfactual is a **model-based simulation**, not an observed adoption; the sentence says so in a parenthetical but does not give it a class. A reader can take it as class A because the study is class A. | **L** | New |
| 26 | `01-d` 13 | "Nineteen candidate variables … eleven survive". C-1 has **17** rows (V1–V17); C-2 rejects **11**; priority 1–4 covers 15 rows; priority 1–2 covers **9**. Neither 19 nor 11 is derivable from the file. | **M** | Corroborated (prior pass) |
| 27 | `01-d` 14–19 | "That one test removes … from the primary-price problem **entirely**". Contradicted by the file's own opening (two decisions) and by V8/V9/V10/V12, which put the variables back for the reprice. | **H** | New |
| 28 | `01-d` 14 | "The decisive filter was not availability and not correlation: it was **the clock**." The rejection table is mostly licence (Google Trends, Reddit, Spotify, X), mechanism (airport proximity, school terms, tourism flows) and redundancy, not the clock. The clock is decisive for six variables, not the set. | **M** | New |
| 29 | `01-d` 17–18, 71 | "transfers" in the summary is ambiguous between player transfers (V10) and ticket transfers (V5). Ticket transfers are in the ledger and knowable at $t$; the literal reading contradicts V5. | **L** | New |
| 30 | `01-d` 73 vs 13–19 | V12 weather is priority 3 with a mechanism; the summary says weather is removed entirely. If it is removed, its priority is 0; if it is priority 3, it is in the engine. Same for V8/V9 (priority 2). | **M** | New |
| 31 | `01-d` 66, 118 vs `01-b` 252 | V5 says filter on `occurredAt ≤ t`; `01-b` §4.6(c) says `occurredAt` has unspecified granularity and any hazard model must use `slot` or risk negative durations. The two implementation instructions disagree. | **M** | New |
| 32 | `01-d` 13, 104 | "On events that sold out at on-sale, the observed path rises into the event date; on soft events it decays." No class; the "(class A)" in §4 attaches to Sweeting's baseball result, not to the platform claim. This is a class-D mechanism stated as a finding. | **M** | Corroborated (prior pass) |
| 33 | `01-d` 13, 110 | "The resale cap turns a price into a rationing rule … the height of that mass point measures excess demand, not value." The mechanism is plausible (class C/D), but the "height measures excess demand" is a hypothesis with no measurement; the section gives it no class. | **L** | New |
| 34 | `01-d` 9 | "Bibliographic details for the four ticket-market papers I cite from memory … were not re-checked in this run." 01-d's §4 uses Sweeting's baseball result as the class-A anchor for the time-to-event pattern; that anchor is from memory, not verified in this run. The file is honest about it; the ledger and the final deliverable should not present it as verified. | **M** | New |
| 35 | `01-d` 76 | V15 `seat_coordinates` is class A. The **mechanism** (seat quality is the dominant within-event axis) is class A from Leslie & Sorensen; the variable itself is not in the contract and its availability is a data fact, not an evidence class. The Class column mixes mechanism evidence with data availability across C-1. | **L** | New |
| 36 | `01-b` 176–178 | Burdett & Judd (1983) is a **theory** paper, labelled class B. It should be C. The same applies to Bulow & Klemperer (2012) in §4.5(iii), where the class B label is carried by the Glaeser & Luttmer empirical paper, not by the theory. | **L** | New |
| 37 | `01-b` 252 | "`occurredAt` is ISO-8601 at unspecified granularity while `slot` is strictly monotone, so any hazard model must derive its time index from `slot`". This is correct and important, but it is buried in a parenthetical at the end of §4.6 and is not carried into the T3 estimator or the 01-d V5 instruction. It should be a first-class data requirement. | **M** | New |
| 38 | `01-b` 239–241 | "If gifts are coded as sales … mean markup **too low**". If gifts (zero markup) are coded as sales, the mean markup is diluted downward, yes; but the report's 79-of-128 argument uses the opposite coding. The gift/sale ambiguity is real, but the two directions are not reconciled. | **L** | New |
| 39 | `01-a` 13 | "≈41% average markup on the ~5% of tickets that resell" is verified against Leslie & Sorensen (41%, 5%), but the summary's "level ≈1.3–1.5× face on average" (§2) is a range the paper does not state; the paper's point estimate is 1.41×. A range around a point estimate is a synthesis, not a source. | **L** | New |

**Notes on the prior pass.** I corroborate the 90/128 arithmetic, the £269 splice, the
"Gap 5" dangling label, the 19/11 count, ~~the Aigner DOI (I re-checked Crossref: the `S`-prefixed
DOI returns 404, the corrected one 200)~~ **[CORRECTION 2026-11-07T14:00Z, R2-27 — dead: the DOI check is real
but the finding is not. `01-b` does not contain the `S`-prefixed string; both its Aigner occurrences are the
resolving form. Nothing about Aigner needed correcting. Withdrawn at the end of this file.]**, and the general point that the Phase 1 summaries are
less disciplined than their bodies. Two corrections to the prior pass's own corrections:
(i) "90 FR 2166" is not a random digit transposition; 2166 is the **end page** and the eCFR
"Source" line, so the error is a page-reference error, not a mistyped start page. (ii) The
prior pass's P1.D row says "17 variables admitted" — the file's own claim is 19 candidates /
11 survivors; 17 is the number of rows in C-1, not the number admitted. The count problem is
real, but the prior pass's phrasing repeats one of the file's two inconsistent counts.

---

## 4. What the engine may therefore claim

The test for every sentence below: it must be true on the observation set in
`00-data-situation.md` §3, it must carry its interval or its class where a number appears, and
it must not turn a bound into a point.

### Sentences the engine may print to a user

1. **"On this event the ledger records N sales. The sale rate is X per 1,000 ticket-days at
   risk. That is a transaction rate for the ticket population, not the probability that a
   listed ticket sells."**
2. **"The resale value of this ticket is bounded. The last recorded sale gives a floor, the
   resale cap gives a ceiling, and the interval is wide because the ledger records sales, not
   listings."**
3. **"On this event the cap binds: tickets sold at the cap are recorded at the ceiling, so
   their value is at least the cap. How far above it we cannot say from this record."**
4. **"The primary price recommendation is a range, not a point. It is based on the primary
   sell-through bracket and the resale value signal; it does not use a resale sale-probability
   curve."**
5. **"The value index is a set of ratios across events and tiers, normalised to a base period.
   It does not give an absolute price level without an external anchor."**
6. **"For the in-market reprice, we use information available at the decision time: injuries
   and player transfers that have resolved, competing events and tour stops announced by then,
   support-act announcements, and weather forecasts inside the forecast horizon."**
7. **"The fee basis is a parameter, not an estimate. If the recorded price is the buyer's gross,
   the seller's net is lower by the fee schedule, and the recommendation changes with the fee
   model."**
8. **"The sale indicator is calibrated on the full ticket population. No price distribution is
   calibrated, and we quote no coverage number for a price."**
9. **"The estimate is a bound with a stated width. The width is driven by the missing listing
   exposure and the cap truncation."**
10. **"The ledger is complete only conditional on enforcement: wallet handoff and off-platform
    settlement leave no row, and we do not impute them."**
11. **"The cap is a ceiling on the resale price and therefore on the buyer's outside option; it
    is a floor on value, not a target for the primary price."**
12. **"This is a class-C bound from the schema and a class-B prior from the literature; it is
    not a measured result on this platform."**

### Sentences the engine must not print

1. **"The probability this ticket sells at price p is X%."** — the T3 crux; the
   price-specific sale probability is not identified without the listing panel.
2. **"The engine knows what this ticket is worth."** — the level is set-identified at best;
   only ratios and bounds are identified.
3. **"The demand curve / the price elasticity is Z."** — the resale demand curve is not
   identified from trades; the primary bracket is a set of one-sided statements at observed
   prices.
4. **"The cap correction recovers the true value of the best inventory."** — the correction's
   size and the sign of the average correction are not established; the leakage rate is
   unidentified.
5. **"Weather, injuries, transfers, competing events and tour stops are irrelevant to
   pricing."** — they are excluded from the static on-sale price's realisations, not from the
   reprice and not from the ex-ante risk terms.
6. **"The sale probability is calibrated."** — the sale indicator is calibrated; no price
   distribution is, and no coverage number may be quoted for a price.
7. **"The resale ledger is complete."** — it is complete only conditional on enforcement.
8. **"The 41% markup is what the whole market earns."** — Leslie & Sorensen observe half of
   resale activity; 1.4% is the observed half.
9. **"The engine finds the revenue-maximising primary price."** — the optimum is a set with a
   sensitivity map, not a point.
10. **"The cap is the central structural fact of the project."** — the missing listing exposure
    is the first constraint; the cap is the second.
11. **"The asking-versus-realised gap has been measured."** — there is no ask anywhere in the
    record; the gap has vanished, not been estimated.
12. **"The primary price should be raised to the cap because the cap proves demand exceeds
    it."** — the cap is also a ceiling on the buyer's outside option; the optimum is set by
    primary sell-through and demand elasticity, not by the cap alone.

---

## 5. What would change the verdicts

- **Claim 1.** A listing panel (`listPriceLamports, listedAt, delistedAt, delistReason`) would
  convert T3 from a bound to a standard time-varying-covariate survival problem. A cap-free
  event, or an event with an exogenous uniform cap, would test the cap-pinned route and the
  instrument version. A randomised ask arm would identify the slope. Until one of these exists,
  the narrow wording stands.
- **Claim 2.** The sign of the correction would be settled by (a) the fee basis — which side
  `priceLamports` is on and the fee schedule; (b) `delistReason = cap_blocked` counts, if the
  platform records them; (c) dark-ticket detection: tickets that redeem from a wallet that never
  received a transfer row, and the correlation of the dark rate with event heat; (d) the excess
  mass just below the cap and the cap-region velocity relative to below-cap velocity; (e) a
  cap-free comparison set with similar demand.
- **Claim 3.** The verdict would change if the deliverable is declared static (then the
  pre-on-sale claim is complete) or if the reprice is declared in scope (then the six variables
  need their own admission table, which the body already half-provides). The file should state
  which decision the "primary price" is.

---

## 6. Bottom line

The three files are better than their summaries. The identification argument in `01-b` is
correct for the full price-response curve and overreaches only where it denies the cap-pinned
level and where it attaches the secondary hazard to the primary optimum. The cap argument in
`01-a` is correct as a mechanical lower bound and overreaches where it turns a class-D
compliance story into a causal fact and calls the cap the central constraint. The clock argument
in `01-d` is correct for the static price and overreaches where it says "entirely" while its own
body admits the reprice. The common fix is to make each summary carry its body's conditional,
not to redo the analysis.

The engine's most dangerous sentence is not a modelling error; it is the product sentence that
sells the thing the ledger cannot identify: **"This ticket has an X% chance of selling at
price p."** That is the sentence the engine must stop saying.

---

*No finding or record file was edited. Nothing was committed or pushed. The only file written
is this one.*

---

## CORRECTION (2026-11-07T11:28Z) — the Aigner DOI item in the notes on the prior pass is withdrawn

Appended by the corrections pass after `records/findings/00-verification-round1.md` §2. Nothing above is
deleted.

**Withdrawn text, "Notes on the prior pass":**

> "I corroborate the 90/128 arithmetic, the £269 splice, the "Gap 5" dangling label, the 19/11 count, the
> Aigner DOI (I re-checked Crossref: the `S`-prefixed DOI returns 404, the corrected one 200), and the general
> point that the Phase 1 summaries are less disciplined than their bodies."

**What is true.** The Crossref check happened, but `01-b` does not contain the S-prefixed DOI. Both
occurrences of the Aigner DOI in that file are the resolving form; the only S-prefixed DOIs in it are
Bollinger (1996), where the `S` is correct. Checked in the working copy on 2026-11-07, and stated in full in
the new correction appended to `00-ledger-verification.md` §3.

So the Aigner item is **withdrawn as a finding about `01-b`**. This paragraph also conflicts with the same
file's own coverage note, which says "I did **not** verify the Aigner DOI"; as printed, the file claims both
to have and not to have checked it. A reader should take the DOI as checked and the attribution to `01-b` as
false.

**What stands.** The other four items in that sentence stand: the 90/128 arithmetic (with the row-versus-ticket
caveat now stated in `01-b` CORRECTION 1), the £269 splice (corrected in `01-a` CORRECTION 2), the "Gap 5"
dangling label, and the 19/11 count (corrected in `01-d`). The two corrections this file made to the prior
pass's own corrections, on the Federal Register end page and on the 17-versus-19 count, also stand.

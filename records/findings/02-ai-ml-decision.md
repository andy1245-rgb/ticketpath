# Phase 2 — The ML/AI question, decided in writing

**Status:** complete for the decision it answers. **Written:** 2026-11-07T11:20Z.
**Agent:** `p2-ai-ml`. **Scope:** whether a statistical estimator earns its cost in *this* product,
on a named target, with a stated data requirement; what an "AI/ML track" entry would have to be to
score, against the published rubric; and whether either is worth the hours between now and the
initial submission at **Sun 2026-11-08 10:00 ET**. This file confirms, corrects, or overturns
`../research/mlh-solana-2026/p3-decision.md` §4 and `p5-build-spec.md` §9, and becomes
**D5** in `records/F-decision-log.md`.
**Does not touch:** any file but this one and the D5 append. No estimator was fitted. No dataset was
read. `lib/mock/` was not opened. Nothing below is a measured quantity except where marked MEASURED
with its source and its date.
**Labels:** **MEASURED** (a fact read from a named source in this pass, quoted with its URL);
**ASSERTED** (my reasoning); **ESTIMATE** (an hour figure; my judgement, not a measurement);
**COMPUTED-ELSEWHERE** (arithmetic done in another finding of this programme, cited, not re-run here).
Programme evidence classes A–E are used only where the claim is about ticket markets — which, for an
answer about a hackathon and an unfitted model, is almost nowhere.

---

## The answer

**Yes to one estimator, no to the AI track, and the two answers are not in conflict.** There is
exactly one place in this product where a fitted estimator earns its cost: the **value band** — an
event's mean log resale-price-to-face ratio, estimated by **normal–normal partial pooling** with two
hyperparameters (μ, τ), which is ~65 lines of standard-library Python already written and verified in
`02-e-cold-start.md` §4.8, and which needs **no field the wire contract does not already carry**. It
earns its cost because at cold start the partial-pooling point estimate *is* the pooled mean, so the
model degenerates exactly to the hand-specified alternative (face value × a declared markup) and costs
almost nothing extra to have in place: you ship the degenerate branch now and it upgrades itself as
events accumulate, with no rewrite. It does not earn its cost on the target a judge will care about
most — the optimal primary price — because that target is set-identified by missing data, and no model
class narrows a set that only new observations narrow (`01-b-identifiability.md` T4b, T5). It is not
"ML" in the sense a judge recognises, because the three things that make a judge say ML — a fit on
data, a comparison against a baseline, a metric — are each unavailable today, two of them for reasons
of data rather than time (`00-data-situation.md` §1, §2, §5.1). The **AI Track stays skipped**: its
published criterion is a *two-sided* materials test ("where AI and Solana each do real work", measured
today, §2.1 below), the only candidate AI entry anyone had weighed was a scripted scalp bot, and the
one candidate nobody weighed — the estimator itself — cannot satisfy the "real work" side while its
parameters are illustrative. That confirms `p3` §4 and `p5` §9 in outcome and corrects `p3` §4 in
reasoning. Spend at most **one hour** on the estimator this weekend, only to give the product a number
that is not arbitrary, and spend the other twenty-seven on the artefacts a judge can click.

---

## Part 1 — Is there a place where a statistical estimator earns its cost?

### 1.1 The constraint that decides this is identification, not functional form

The programme's binding constraint is not "the model is too simple". It is that four target quantities
are not identified from the observation set, and the reason in every case is a **missing regressor or a
missing latent**, not an inadequate functional form:

| Target | Status | Why it fails | Source |
|---|---|---|---|
| Value level `V_i(t)` | Set-identified at trade instants, ratios only | No exogenous price anchor; affine indeterminacy | `01-b` T1, §4.1 |
| `V` for an event with no resale | Not identified; prior predictive only | No second event to pool against at J ≤ 1 | `01-b` T1′ |
| Price path | Curvature identified, slope not | Exact age–period–cohort collinearity | `01-b` T2, §4.2 |
| Sale hazard vs price | **Not identified** | The ask is recorded only on the success branch | `01-b` T3, `02-c` §1.1–1.2 |
| Demand / elasticity | Not identified from secondary trades | No buyers, no declines, no simultaneous alternatives | `01-b` T4b |
| Primary optimum | Set-identified; width = union of T3 and T4 widths | Needs both of the above plus a fee model | `01-b` T5 |

A gradient-boosted tree, a random forest, a Gaussian process and a two-parameter shrinkage estimator
all require the same thing on the deviating branch: an observation of the ask on tickets that did *not*
sell. `00-data-situation.md` Gap 1 shows the contract has no listing start, ask, revision or
withdrawal, so that observation does not exist. **Swapping the estimator does not add a column.**
This is the single structural argument behind the answer, and every part of the recommendation below
follows from it rather than from a preference for simple models.

### 1.2 Target by target: where a model *class* can move the answer at all

Read this as: given the data situation, is there anything for extra capacity to bite on?

- **T1 / T1′ (value level, and the cold-start event).** Yes — and this is the only row that pays.
  Something must be estimated (the between-event spread) and something must be shown (a width). See
  §1.3.
- **T2 (price path).** The identified object is one structural parameter, the degree of deadline
  convexity, pooled across events by inverse-variance weights (`02-a` §8.2–8.3). One parameter has no
  capacity to add: `02-a` §8.2 fixes `K = 5` and δ = 1 day a priori *because* "tuning them would add
  two parameters the data cannot support". A flexible time basis here is fitting the age–period–cohort
  collinearity.
- **T3 (sale intensity).** The identified object is a composite intensity plus the joint mark–time
  surface ξ(p,t) (`02-c` §1.3, §2.4). Here flexibility is *already* the programme's own first choice:
  `02-c` §4.2 puts the nonparametric-in-price form first and the linear form only if the iso-hazard
  contours are straight — but that is Specification B, which exists **only after the four listing
  fields arrive** (`02-c` §1.5). On today's data the flexible form has nothing to fit: the price is
  present only where the sale happened.
- **T4a (hedonic).** A model is needed and it is specified (`01-c` §4.6): a Tobit-style censored
  regression fitted by EM, ~150 lines. See §1.6 for why the censoring makes this *better* than a
  black-box regressor, which is a technical point and not a taste.
- **T4b / T5 (elasticity, optimum).** Nothing to bite on. The identified part is a set, and a set is
  narrowed by observations.
- **T6 (calibration).** Nothing to bite on: `02-c` §5.2 shows an in-sample reliability curve is the
  score equation plotted, and `00-data-situation.md` §5.2 forbids letting a simulation stand in for a
  validation.

### 1.3 The one estimator that earns its cost, named

**Target:** T1′ — an event's mean log resale price ratio to face, `θ_j = E[log(p/f)]`, with its
predictive interval. This is the product's "what is this realistically worth, and how sure are you",
for an event that has no resale history of its own.

**Estimator:** normal–normal hierarchical partial pooling (empirical Bayes), with τ handled by a
601-point grid posterior rather than a point estimate.

```
within:  y_ij = log(p_ij / f_ij) ~ N(θ_j, σ_j²)
between: θ_j ~ N(μ, τ²)
shrinkage:  B_j = τ²/(τ² + s_j²),  θ̂_j = B_j·y_j + (1 − B_j)·ȳ(τ)
```

**Parameters:** two hyperparameters (μ, τ) plus one event mean per event. The 601-point grid is
computation, not parameters. No matrix algebra; no dependency.

**Cost:** the implementation is already written and its branches already exercised in
`02-e-cold-start.md` §4.8 (`moment_tau2`, `marginal_loglik`, `tau_posterior`, `cold_start_predictive`,
`mixture_quantile`, `shrink_weight`) — about 65 lines, verified there for grid-weight summation, the
J = 1 singularity, the truncation branch and the B = 0.5 identity. The χ² upper confidence limit adds
~40 lines of incomplete gamma plus a bisection, also written in that pass. A fit is a few thousand
floating-point operations: milliseconds. **Nothing here needs a numerical stack, so D2 costs this
model nothing.**

**What it buys over the hand-specified alternative.** The honest answer is narrower than it looks, and
it is the finding the brief anticipated: **below about twenty events — the whole range over which
`02-e` §4.4 shows the between-event variance is pinned to no better than a factor of 3.7 — a
two-parameter shrinkage estimator and a declared band differ mainly in the label, not in the
number.** Three reasons, all from the programme's own algebra:

1. At cold start the partial-pooling point estimate *is* the population mean, because `s_new² = ∞`
   forces `B_new = 0` (`02-e` §4.3). τ does not enter the point at all; it enters only the width.
2. τ itself is barely pinned when J is small: at J = 5 the 95% interval on the between-event variance
   spans a factor of 23 (0.121× to 2.79×), at J = 2 it spans 5100× (`02-e` §4.4, COMPUTED-ELSEWHERE).
   So the thing that produces the width is, at small J, itself a prior.
3. Therefore what the estimator actually buys is **not accuracy today** — it is (a) a width that stops
   being a guess as J grows, (b) the handover count `n* = σ²/τ²` at which the event's own sales
   outweigh the population (`02-e` §4.6), and (c) the licence to keep the same code when the data
   improves. And (d), the reason to build it this weekend: **its degenerate branch is exactly the
   hand-specified alternative**, so shipping it costs one file instead of a throwaway.

**What it does not buy, and this must be said next to it:** the cold-start band prices the *resale ask
denominated in the organiser's own face value*, so it cannot set the primary price — moving face moves
the band proportionally and "set face to the middle of the band" is circular (`02-e` §1.10). The
primary optimum comes from the demand side (T4b) plus the fee scalar (`02-d` conclusion 1), and is
reported as a set (`01-b` T5). So the estimator earns its cost on the **value band**, and there is no
estimator that earns its cost on the **optimum**. Both halves of that sentence are the finding.

### 1.4 Is that "ML" in any sense a judge would recognise?

No, and it is worth being exact about why, because "it is just statistics" is a lazy dismissal and the
rubric finding deserves better than that.

A judge recognises machine learning when three things are on screen: **a model fitted to data**, **a
comparison against a baseline**, and **a metric**. Each is unavailable here for a named reason:

- **A fit on data.** `00-data-situation.md` §2 settles that `lib/mock/` is synthetic (mint addresses
  do not decode to 32 bytes; no generator, no seed, no provenance) and §1 records that no backend, no
  database, no deployed program and therefore no ledger exist. This repo's own
  `fixtures/synthetic_store.json` is hand-authored and its `meta` block forbids estimation. So there is
  no dataset to fit on, and `lib/mock/` may not be used (`AGENTS.md`; `tests/test_boundaries.py`
  enforces it).
- **A baseline comparison.** The benchmark ladder exists on paper and is good: B0 the martingale, B1
  the pooled prior mean, B2 shape-only, then the model, scored by skill `1 − MAE_M/MAE_B0` in log
  space on event-level walk-forward folds (`02-a` §8.5). It cannot be run, because running it requires
  a ledger.
- **A metric.** `00-data-situation.md` §5.1: no result from our own data can be class A. §5.2 permits
  a **SIM** study of *estimator properties* and forbids quoting it as performance on tickets. So the
  only metric available is a parameter-recovery number on a stated data-generating process.

A recovery study is legitimate, honest, and defensible: "we generated 200 events from a stated
process with τ = 0.4, fitted, and the estimator recovered τ within the interval in X% of replications"
is a real claim about a real estimator, labelled SIM. **It is also not what a judge means by ML, and it
is UNVALIDATED for this market.** Anyone who puts it on screen must label it "recovery on simulated
data — not a ticket-market result", and `02-rubric-and-scoring.md` already has the labelling rule that
governs it ("model's coefficients / calibration … may be simulated if labelled 'illustrative
parameters, not calibrated'").

### 1.5 What a bigger model would have to beat

Because the benchmark ladder is already specified, the case for any larger model is falsifiable and
cheap to state. A gradient-boosted or nonparametric model is worth its build only if, on the same
event-level walk-forward folds with the two leakage boundaries enforced (`02-a` §8.5), it beats the
two-parameter shrinkage model on **MAE in log space** by a margin that survives the fold count, *and*
keeps the interval honest. On the identified targets there is one parameter (`02-a`) or none to
compete over. So the honest verdict is not "ML is not needed" but the sharper:

> **A two-parameter shrinkage estimator buys almost everything a bigger model would, on the only
> target where extra capacity has anything to fit — and on the targets where a bigger model would
> matter, no model class helps, because the problem is a missing regressor.**

### 1.6 The one place where a statistical model beats a black box for a *structural* reason

This is the part of the answer a person could disagree with, so it gets its own argument rather than a
preference. The resale price ceiling is a policy truncation with rationing behind it
(`00-data-situation.md` Gap 2): the observed markup distribution is left-truncated by design and the
top of the latent distribution is invisible. A black-box regressor fitted to observed markups learns
`E[y | y observed]`. A censored regression learns the latent `y*` by integrating over the region above
the cap (EM, with the inverse Mills ratio in the E-step — `01-c` §4.6). Under a binding cap these are
different objects, and the direction of the difference is known and one-signed: **the tree understates
value exactly where value is highest** (`00-data-situation.md` Gap 2; `02-a` §6 item 9; `02-e` §1.8).

The rebuttal a competent person will make is "give the tree the cap as a feature". The answer is that
a feature cannot recover a latent that is truncated above the ceiling: the information is absent from
the sample, and what is required is a likelihood that says so — i.e. a statistical model. So on the
hedonic target the recommendation is not "prefer simple", it is "the censoring is the model". That is
the strongest technical sentence available against a bigger model here, and it is the sentence to use
if a judge or the operator asks why there is no boosting in the product.

---

## Part 2 — What an AI/ML track entry would actually require to score

### 2.1 The criterion, measured today, and it is a two-sided test

The rubric finding records each category page as carrying "a one-line description and no judging
criteria beyond it" (`02-rubric-and-scoring.md` A4). The one-liner on the event's own track text is
longer than that and it matters. Fetched 2026-11-07T11:04Z from
`https://events.mlh.com/events/15200-solana-hackathon`, verbatim:

> **AI Track** — Each winning team member will receive a $100 digital gift card. **Build something
> where AI and Solana each do real work.** The best projects use AI to make on-chain activity smarter,
> safer or easier, or use Solana to give AI systems something they can't get elsewhere, like payments,
> ownership, verifiability or coordination.

Two clauses, both load-bearing. AI must do work, *and* Solana must do work, and the listed shape of
the second half is explicitly "verifiability". This is a materials test of the same form as the Top-3
sentence (`02-rubric-and-scoring.md` A3, F1), and it is stricter than "we used an LLM". It also
supplies the cheapest honest composition in the whole event: the organiser's own listed idea
**"Verifiable AI: on-chain records of model outputs, datasets or provenance"**, which is the same
artefact as `02-rubric-and-scoring.md`'s Tier 2 on-chain object. That coincidence is real and it is
the only reason the track is arguable at all.

### 2.2 The four candidate shapes, honestly costed

What each adds to the score, what it risks, and whether a fake version is worse than nothing.

| Shape | Adds to the score | Risks | Fake version |
|---|---|---|---|
| **LLM parsing messy inputs** (e.g. tier names → seat-quality ordinal) | Nothing directly; possibly a little Technology via the hedonic's strongest axis (Gap 3 is why that axis is missing) | Non-determinism inside a number that becomes a price; per-call cost; needs an API key I must not assume exists; unauditable | **Worse than nothing.** And unnecessary: the only tier vocabulary that exists anywhere in this repo is three names ("Balcony", "Floor", "Standing", `fixtures/synthetic_store.json`), and the contract's own examples are "Floor GA", "Front Rail". A regex/alias table covers a bounded vocabulary at 100% recall and zero variance. The messy input is not messy at this platform's scale. |
| **LLM explaining a recommendation** | Nothing. MLH excludes pitch quality and idea quality (`02-rubric-and-scoring.md` B2, B3); prose is not the product | A judge asks "is the explanation the model or the wrapper?" — the question that turns a demo into a harness demo | **Worse.** It is the exact "reskin of an existing AI tool" the organiser's guide names (B6). |
| **A learned model behind the price** | Potentially the only real channel: Technology is 25% (`B1`) and "did the technology make you go wow" is answered by a working thing | No data to fit on (§1.4); parameters must be labelled illustrative; a judge who asks "trained on what" gets a one-word answer that loses the exchange | **Worse if unlabelled.** Legitimate and strong if the label is honest and the number is load-bearing. This is the only shape with a defensible version. |
| **An agent loop** | Nothing on the four criteria; it is a separate prize, not a criterion | "So the guardrail is a prompt?"; 1–3 s of latency per action on camera; the only tools it could call are endpoints we wrote (`01-c` §1.2(e) and `02-c` show the feedback loop it would need is undefined — no logged actions or propensities) | **Worse.** A scripted loop printing errors is visibly scripted (`p2b` §4.3). |

Note what none of these adds: the AI Track is **not one of the four judged criteria**. It is a separate
prize (`02-rubric-and-scoring.md` A3, A4). So an AI component earns points only through its effect on
Technology, and only if it is visible in the running artefact.

### 2.3 "Agent proposes, policy disposes" is a cliché — verified, not repeated

The claim in `p3` §4 and `p5` §9 traces to `p2b` §4.1, which enumerated five shipping Devpost products
with that exact shape by name (AgentGate, Vouch, Venture DAO, Leash, CoSign) plus a ticketing one
(Smart Event Ticketing: Anti-Scalping & Fair Allocation), and concluded "`agent proposes, policy layer
disposes` is a *genre* now". **That claim survives, and I can add a second, independent ground for it
that `p2b` did not have**: the organiser is handing out the scaffolding. Measured on the event page,
same fetch:

- the AI Track's **first** listed idea is "Autonomous agents that hold a wallet and act on-chain";
- the Hacker Resources list includes **"Solana Agent Skills — Pre-built skills that let your AI agents
  work with Solana programs, tokens, and tooling"**;
- the schedule carries a workshop, **"Build with AI on Solana w/ Mike"**, Saturday 10:30 AM ET.

When the organiser supplies the agent skills and runs the workshop, an agent wrapper is the shape the
field will produce whether or not anyone thought about it. `02-rubric-and-scoring.md` independently
reaches the same place from the rubric side ("An 'AI agent' wrapper. It is item 1 and 2 of the
organizer's own AI idea list, so it is the most crowded shape of the weekend"). Three documents, two
methods, same conclusion.

**One correction to how `p3` uses it.** `p3` §4 offers "the generic form is a cliché" as the primary
reason. That is the *weakest* of the available reasons, because MLH excludes idea quality from the
rubric (`B2`) — being a cliché does not itself lose a point. The two stronger grounds are: (i) the
criterion is a two-sided materials test (§2.1) that a decorative agent fails on its own terms; and
(ii) the AI track pays $100 per member against a $1,000 team microgrant for each of three Top-3 places
(`A3`), so the hours are being moved from a prize an order of magnitude larger.

### 2.4 Would a fake entry be worse than no entry?

Mostly it would be worse, but the honest risk is smaller than `p3` implies and it should be stated
precisely rather than as a threat. The disqualification penalty is attached to **not crediting AI
usage**, not to overclaiming a model (`B6`: "If you do not credit your AI usage, you will be
disqualified and reported to cheating@mlh.io"). So the risk of a decorative model is not
disqualification; it is the Q&A minute and the credibility of everything else in the submission.
`02-rubric-and-scoring.md` F3 and D4 supply the operative rule: "if someone can't check a claim without
logging in, it doesn't count". A judge who asks "what was it trained on" and hears "illustrative
parameters" will discount the neighbouring claims too, and the neighbouring claims are the ones that
actually score.

**A decorative version is worse than no entry; an honest labelled version is better than no entry, but
only if the number on screen is the model's output.** The distinction is the whole decision.

### 2.5 Verdict on the track

**Skip the AI Track. Confirms `p3` §4 and `p5` §9.** The one candidate that would make it defensible —
a fitted model whose quote is the object committed on chain — requires a fit, and a fit requires data
that does not exist (§1.4). Without the fit, the submission would be claiming AI does "real work" while
the parameters are illustrative, which is exactly the shape a judge punctures in one question. Enter
the track only under the trigger in "What would change this answer" #3.

---

## Part 3 — Is it worth the hours, against a clock of ~28 h?

### 3.1 The clock, measured

`date -u` at 2026-11-07T11:05Z. Initial submission Sun 2026-11-08 10:00 ET = 15:00Z. **~27.9 hours.**

### 3.2 The weighting, corrected before it is used

The brief for this file says compliance-and-workingness is "half the score". That number needs
correcting, and the correction does not change the direction. `02-rubric-and-scoring.md` A5 found the
25/25/25/25 weighting quoted in the project brief to be **MEASURED-ABSENT** from every MLH and event
page that could be reached; the published criteria are four equally weighted lines — Technology, Design,
Completion, Learning (B1). Of those, **Design and Completion are 50% on their own** and are pure
properties of a running, designed artefact, and Technology is judged on the artefact too. So "half" is
a defensible **floor** under the published rubric, not the full weight, and the unbuilt state is worse
than the brief implies: the rubric finding's own section concludes "a judge who clicked a demo URL right
now would see nothing at all, because there is no demo URL". None of the four criteria rewards a model
that is not visible.

### 3.3 The hours, itemised

All figures here are **ESTIMATE** — my judgement from the shape of the existing repo (2,133 lines of
Python, `ticketpath/adapters/pricing_model_adapter.py` at 81 lines returning `available: false`, nine
test files), not a measurement of a build that happened.

| Work | Hours | Needed for the submission? |
|---|---|---|
| Lift `markup_band` from `02-e` §4.8 into `ticketpath/core/markup_band.py`, add the prior-only branch, unit-test the three degenerate cases | 1.0 | **Yes** — the product needs *a* number to show, and this is the cheapest honest one |
| Register it through the existing `PricingModelAdapter`, wire the `basis` block, keep `dataSource.synthetic` on the payload | 0.5 | Yes, if the number is on screen |
| Recovery study on a stated DGP: generator, fit, recovery table, guards, the SIM label | 3.0 | No |
| The surface — a page that renders the number with its width and its label | 1.0 | Yes, but it is 1.0h *after* the page exists, and the page does not exist |
| On-chain quote-hash memo so the model's output is the committed object (AI-track condition) | 1.5–2.0 | No — and it is on the operator's laptop, in the same hours he needs for the mint and the signature |
| Video beat (10 s of a ≤2 min video), README integration section, AI-disclosure line | 0.5 | Yes |
| **Total, product-minimum (first, second, last rows)** | **2.0** | |
| **Total, defensible-fit version (+ recovery + surface)** | **6.0** | |
| **Total, AI-track version (+ memo commit)** | **7.5–8.0** | |

So the honest figure is not "ML costs five hours". It is: **the estimator costs one hour because it is
already written; the demonstration around it costs another five; the AI entry costs two more on a
machine that is not this one.**

### 3.4 What those hours displace

`02-rubric-and-scoring.md` lists ten things the Sunday build must contain. Measured against the repo
today (that finding's E6, and its section conclusion), at least four are absent: a page a judge can
open; a devnet account belonging to the project; one confirmed signature with a block time; the app
reading the chain back. Those four are the whole of the Top-3 sentence's materials test (F1), and
Design plus Completion are 50% of the published criteria. Every hour above 2.0 in §3.3 comes out of
that list. At 6.0 hours the trade is: half a working day removed from the two criteria weighted at 50%,
to buy one Technology impression and a track worth **$100 per member against a $1,000 team microgrant**
(A3) — a fifth, for a two-person team.

### 3.5 The recommendation, with the number in it

1. **Build the estimator now, in its prior-only branch, capped at one hour**, because the product
   currently returns `available: false` with no number and a hand-specified quote has to be built
   anyway. Ship it labelled, with its width, and say the width is declared. **This is the one hour in
   this document that is not a trade against the rubric.**
2. **Do not spend the next five hours.** The recovery study is the right next thing *after* the
   must-contain list is complete, and it should be written to a file with its SIM label the moment it
   exists, not reconstructed later.
3. **Do not enter the AI Track**, and do not build the on-chain quote-hash for the track's sake. If the
   quote-hash memo is built anyway because it is the Tier 2 artefact that makes the chain load-bearing,
   then the track becomes an *honest checkbox* rather than a claim, and it can be selected at 09:00 ET
   Sunday on the labelling rule in `02-rubric-and-scoring.md` §"What can be simulated honestly".
4. **The decision must be made by 09:00 ET Sunday, not 11:00.** `02-rubric-and-scoring.md`'s open
   question 1 records that nothing published says whether the 10:00 ET initial submission is editable
   before 11:45, and its advice is to treat 10:00 as a hard freeze. A conditional plan that resolves at
   08:00 is therefore only safe if the video is recorded before it, and the video is recorded at 09:30
   by `p3` §5's own rule.

---

## What would change this answer

Each of these is a specific, checkable fact, not a matter of taste. Any one of them flips the
corresponding clause.

1. **Real ledger data exists somewhere** (Q2 answered "yes, a program is deployed" with transaction
   history). Then the benchmark ladder becomes runnable, a skill score becomes reportable, and the
   answer to "is this ML a judge would recognise" becomes **yes** — a fit plus a baseline plus a metric
   is exactly what a judge recognises. The estimator recommended does not change; only its status
   changes, from UNVALIDATED to measured.
2. **The four listing fields arrive** (`listPriceLamports`, `listedAt`, `delistedAt`, `delistReason` —
   D3). Then Specification B in `02-c` §4 becomes estimable, the nonparametric-in-price form becomes
   the *first* choice by the programme's own reasoning (`02-c` §4.2), and a flexible price-response
   model earns its cost. This is the single change with the largest effect on this document, and it is
   a data request, not a modelling decision.
3. **By 09:00 ET Sunday the must-contain list is complete, a fit exists on a stated DGP, and the
   quote's hash is committed on chain.** Then the AI Track entry becomes honest under §2.1's
   two-sided test — AI produces the committed number, Solana makes it tamper-evident — and the cost is
   zero extra hours because both halves were already built for other reasons. Enter it. This is the
   trigger, and it is deliberately hard to satisfy.
4. **The initial submission turns out to be editable after 10:00 ET.** Then the conditional in #3 can
   be resolved later and the safe-freeze assumption in §3.5(4) relaxes. It does not change the
   recommendation, only the deadline for acting on it.
5. **A published AI-track winner record appears with a decorative model.** There is none to study —
   this is the first MLH Solana Hackathon (`02-rubric-and-scoring.md` A6) — so the claim that a
   decorative entry fails is reasoning from the criterion's wording, not from observed awarding
   behaviour. One verified counter-example would weaken §2.4 materially.
6. **The operator supplies a seat-quality field** (Q1 answered "yes"). Then the hedonic's dominant axis
   exists, the `n*` handover count rises (`02-e` §4.6), and a model with a real second covariate
   becomes worth fitting — but still only after data exists.

---

## If we do build one, this is exactly what it is

**Name.** `MarkupBand` — the predictive band for an event's mean log resale-price-to-face ratio.

**Target, stated so it cannot be misread.** `θ_j = E[log(p_ij / f_ij)]` over sales in event *j*, and
its predictive interval for a *new* event. Not a price in currency (the level is not identified,
`01-b` T1), not a sale probability (`02-c` §1.1), and not the optimal primary price (`02-e` §1.10).

**Estimator.** Normal–normal partial pooling; τ by the 601-point grid posterior with a half-Cauchy
prior (scale 0.25, declared), cross-checked by the DerSimonian–Laird moment estimate and the χ² upper
confidence limit; the degenerate branch at J = 0 returns the declared prior location and the declared
floor τ₀ with the grid sensitivity printed as the band. `02-e` §4.4 names all four routes and requires
all four to be reported rather than one chosen silently.

**Parameter count.** Two hyperparameters (μ, τ) plus one mean per event; `K = 5` and δ = 1 day are
constants, not parameters. Nothing is tuned.

**Data requirement.** Per event: a set of completed sales with `priceLamports`, and each ticket's
`faceValueLamports` from its tier — both carried by the contract (`00-data-situation.md` §3). **Zero
new fields.** Minimum useful J: 2 to constrain τ at all, 5 before any number for τ should be printed
(`02-e` §4.4), and the honest output below that is the prior with the sensitivity table beside it.

**Cost.** ~65 lines for the estimator (already written and branch-verified in `02-e` §4.8), ~40 more
for the χ² quantiles, one unit test file. Standard library only; no numpy, no new dependency (D2). A
fit is milliseconds on aggregated cells.

**Where it lives.**

- `ticketpath/core/markup_band.py` — the pure function: `estimate(sales, face, prior) ->
  {point, lo, hi, n_events, tau_mode, basis}`, no I/O, no imports beyond `math`.
- registered in `ticketpath/orchestrator.py` through the existing
  `ticketpath/adapters/pricing_model_adapter.py` seam, which today returns `available: false,
  basis: "no_model_registered"`. Nothing in `core/` may call it directly — the adapter is the seam.
- tested in `tests/test_markup_band.py`: the J = 1 singularity, the truncation-at-zero branch, the
  B = 0.5 identity at `n = σ²/τ²`, grid weights summing to 1, and the prior-only branch returning the
  declared location.
- **No new HTTP route.** `records/CONTRACT-MAP.md` §6 argues against putting a non-contract route on
  the judge's path, and that argument stands. If a valuation route is ever added, it is declared as an
  addition in CONTRACT-MAP §7, not slipped in.

**Validation status: UNVALIDATED.** No fit has been run against ticket data, because no ticket data
exists (`00-data-situation.md` §1, §2). The evidence that would validate it: (i) a SIM recovery study
— generate events from a stated DGP with known μ, τ, σ, fit, and report interval coverage and bias,
labelled SIM per §5.2; and (ii) the real test, on a real ledger, the skill score
`1 − MAE_M/MAE_B0` against the martingale benchmark on event-level walk-forward folds with both
leakage boundaries enforced (`02-a` §8.5). Until (ii) exists, no accuracy claim of any kind may be made
about this model, and the number on screen must carry "illustrative parameters, not calibrated" at the
same weight as the number itself.

---

## Sources

Read in full in this pass unless marked.

**Programme records (cited by section).**
1. `records/00-data-situation.md` — §1 (no backend, no program, no numerical stack), §2 (fixtures synthetic; three checks), §3 (the observation set), §4 Gaps 1–4, §5 (evidence classes; SIM admissible for estimator properties only).
2. `records/findings/01-b-identifiability.md` — T1, T1′, T2, T3, T4a, T4b, T5, T6; §4.1, §4.2, §4.3, §4.4, §4.6; §6.
3. `records/findings/01-c-methods.md` — §1.1 matrix, §1.2(b)(c)(d)(e), §1.3 build order, §4.2, §4.3, §4.6, §7.3, §7.4.
4. `records/findings/02-a-price-paths.md` — §1 items 5, 8, 9; §6; §8.2–8.5 (the benchmark ladder and the two leakage boundaries).
5. `records/findings/02-c-sale-hazard.md` — §1.1–1.5, §2.4, §3.8, §4.2, §5.2.
6. `records/findings/02-e-cold-start.md` — §1.1, §1.5, §1.10, §4.2, §4.3, §4.4 (the J table), §4.6, §4.8 (the verified code), §5.
7. `records/findings/02-d-elasticity-fees-optimum.md` — "What I concluded" 1–2 (the single fee wedge).
8. `records/findings/02-rubric-and-scoring.md` — A1, A3, A4, A5, A6, B1, B2, B3, B6, B7, C1, D1, D4, F1, F2, F3; §"Does a judge … see a working thing", §"What can be simulated honestly", §"Open questions" 1.
9. `records/CONTRACT-MAP.md` — §5, §6, §7.
10. `records/F-decision-log.md` — D1, D2, D3, D4, Q1, Q2, Q3.
11. `records/00-prior-direction-index.md` — §3 "The AI/ML track" items 1–3; §"claims to distrust" 15 (the 36-of-38 keyword count, treated as weak evidence).
12. `RESEARCH-PROGRAM.md` — §3 Phase 1 domain list ("Machine learning"), "Required outcome" (GAMs, tree-based boosting, Bayesian hierarchical, hybrid statistical and ML), "Model evaluation criteria" (accuracy, calibration, data requirements, cold-start, generalization, interpretability).
13. `AGENTS.md`; `NIGHT-BRIEF.md` §6, §7; `fixtures/synthetic_store.json` `meta` block; `ticketpath/adapters/pricing_model_adapter.py`.

**Prior documents under review.**
14. `../research/mlh-solana-2026/p3-decision.md` — §4 (the AI Track table row), §2, §3, §5.
15. `../research/mlh-solana-2026/p5-build-spec.md` — §9 (submission checklist).
16. `../research/mlh-solana-2026/p2b-scalper-prior-art.md` — §4.1 (the five shipping products), §4.2, §4.3 (the 4-hour implementation table).

**Fetched in this pass.**
17. https://events.mlh.com/events/15200-solana-hackathon — fetched 2026-11-07T11:04Z. AI Track criterion verbatim, the five "Ideas to Get Started" lists, "Solana Agent Skills" in Hacker Resources, the "Build with AI on Solana w/ Mike" workshop in the schedule, and the schedule times for the two Sunday deadlines.
18. https://www.mlh.com/events/solana-hackathon — fetched 2026-11-07T11:04Z. Prize amounts as rendered on the event page; the submission counter still reading **7 Submissions** at 11:04Z; deadline field "Nov 8, 1:00 PM EST".

**Not re-verified here, and flagged so nobody mistakes them for fresh measurements:** the Devpost products in `p2b` §4.1 (cited, not re-fetched); the 36-of-38 keyword count (`00-prior-direction-index.md` distrust item 15); the J-table arithmetic in `02-e` §4.4 (COMPUTED-ELSEWHERE, not re-run).

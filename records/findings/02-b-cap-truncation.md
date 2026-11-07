# Phase 2-B — What a binding resale price ceiling does to the observed record

**Status:** complete (four sections; append-only file, written incrementally).
**Written:** 2026-11-07T11:25Z (header and §1), completed 2026-11-07T11:27Z. **Author:** Phase 2-B research agent.
**Scope:** the observation scheme implied by `resalePriceCapBps`, and nothing else. Four questions: the
formal statement of what is observed and censored; what is recoverable from the record as it stands; what
the engine must do and must refuse to claim on a capped versus an uncapped event; and the one data change
that fixes the problem. This is reasoning over findings already on disk. No literature search, no new
sources, no new data. Every magnitude below is quoted with the file it came from; nothing is estimated here.

---

## 1. Formal statement

### 1.1 The variables

Each settled resale is a row carrying `priceLamports` and therefore `markupBps`
$m = (\text{resale} - \text{face})/\text{face} \times 10000$, plus `occurredAt` and `slot`, the two
wallets, the tier and the event. The policy field `resalePriceCapBps` $= c$ is a ceiling on resale price
expressed in basis points over that tier's own face value, with `null` meaning uncapped but still tracked
(`records/00-data-situation.md`, Gap 2). Read as a bound on the markup, the admissible set is
$m \in [0, c]$ — a band, because 02-D states the feasible resale band is $[p, p(1+c)]$, i.e. under face
is not an admissible resale either (`records/findings/02-d-elasticity-fees-optimum.md`, §2.5(a)).

Write $m^{*}_i$ for the markup the parties would have agreed had the ceiling not applied, and
$V_i(t)$ for the latent resale value, following `01-b` §2, which treats the observed mark as a censored
draw rather than a measurement of the latent: a trade at $p$ reveals $p$, and *under a binding ceiling
the trade reveals $V \ge p_0(1+c)$ only* (`records/findings/01-b-identifiability.md`, §2(b)).

**What is observed when the ceiling binds:** the pair $(i, t_i, m_i)$ for every resale that settled at or
below the ceiling, including the rows that settled exactly at $m_i = c$; the count and identity of those
rows; the time from listing to settlement where the platform records it (it does not — Gap 1); and the
policy value $c$ itself.

**What is not observed:** every $m^{*} > c$. Not its value, not its count, and — under one of Q3's two
enforcement loci — not even the fact that an attempt existed. Also not observed: the buyer side at all
(no bids, offers, views or searches; `01-b` §6(3)), and any part of the consideration that left the rail
(`01-a` §3, channel 3).

### 1.2 The condition under which the observed markup distribution is biased down

Decompose the naive mean over settled rows, with $s = \Pr(m = c \mid \text{settled})$ the observed share
of sales sitting exactly on the ceiling:

$$\mathbb{E}[m \mid \text{settled}] = (1-s)\,\mathbb{E}[m \mid m < c] + s\,c, \qquad
\mathbb{E}[m^{*}] = \mathbb{E}[m \mid \text{settled}] + s\,\mathbb{E}[m^{*} - c \mid m^{*} \ge c].$$

The bias is $s \cdot \mathbb{E}[m^{*} - c \mid m^{*} \ge c]$. Everything in that expression is class C
derivation from the definitions; it is written as an identity so that no magnitude is implied — neither
factor is known from the record.

**The condition is:** the observed markup distribution is biased down iff $\Pr(m^{*} > c) > 0$, and the
bias is increasing in both the share of sales at the ceiling and the average amount by which the latent
markup exceeds it. It is zero only in the degenerate case where no latent agreement would ever have
exceeded the ceiling, which is the case where the cap does not bind. Notice what the share $s$ does and
does not do: $s > 0$ is *evidence* that the ceiling binds, but $s = 0$ is not evidence that it does not.
A cap that binds hard enough, or an enforcement locus that leaves no row at all, can produce a record
with no mass point and a maximally truncated tail — the two poles of the same failure.

There is a second, independent bias in the same direction, and it survives even for rows *below* the
ceiling. `01-a` §3 names four evasion channels — side payment, wallet handoff, bundling, flight to
unregulated channels — and the consequence it draws is that at the cap the recorded markup is a lower
bound with the bias largest where demand is strongest. That is a class C direction of bias on a class D
statement about seller behaviour: the file states the channel and the direction, not its prevalence. The
UK's own cost-benefit model assumes 20% displacement of tout volume to unregulated channels
(`01-a` §3, quoted there as an official assumption, not a measurement). So the corrected distribution is
squeezed from both ends, which `F` D6 states in its own words: the chain bounds the record, not the money.

### 1.3 Truncation or censoring: the distinction, and which one this is

The two words are not interchangeable and the record uses them loosely.

- **Truncation** removes units from the sample. The excluded observations are absent, no indicator
  survives, and the sample carries no information about how many were excluded. Estimation is on a
  conditional distribution, and the conditioning event is unobserved.
- **Censoring** keeps the unit and coarsens its value. The unit contributes a row, the boundary is
  observed, and the count at or beyond the boundary is known; only the location beyond it is not. With a
  censoring *indicator*, this is the benign case (`01-b` §4.4(i), the Tobit with an observed indicator).

Both variables exist here, and which scheme each gets turns on `Q3`
(`records/F-decision-log.md`, Q3): whether the ceiling is enforced on-chain, so that a sale over it is
impossible and the transfer reverts, or by the platform's matching engine, so that it is merely prohibited
and a refused attempt can leave a note. `F` D6 settles the locus *for this programme's own design* — the
cap is checked in `transfer_ticket` before the transfer CPI, and no refused attempt is recorded on-chain,
because recording refusals "turns the wall into a note, charges the seller for being refused and is
floodable". It leaves Q3 open for the live platform, whose matching engine is not this program.

**Locus A — on-chain revert (the design in D6).** The settled-transaction record is *truncated*, in the
strict sense, and so is the attempt record. A transfer priced above the ceiling does not fail and produce
a failed row; it fails and produces nothing, and `HopRecord` is not written. So: no row above $c$, no
indicator, no count of refusals. What the record contains is the settled sub-band plus a mass point at
$c$. Any estimator that treats the observed rows as a sample of resale prices is estimating
$\mathbb{E}[m \mid m \le c]$ and reporting it as $\mathbb{E}[m^{*}]$.

**Locus B — platform refusal (Q3's other branch).** Two variables now, two schemes. The
settled-transaction record is still **truncated** at the ceiling — a refused listing never settles, so
there is no `priceLamports` row above $c$ and the transaction-price distribution is missing its top. But
the *attempt* record is **censored with an observable indicator**: a listing at an ask above $c$ exists,
carries its `listPriceLamports`, and is refused with a reason. That is a right-censored observation of
the seller's reservation, and it is the one-sided statement "this seller asked at least $X$ and was
refused", which is information about the *ask*, not about the buyer's willingness to pay. It upgrades the
tail from invisible to bounded below at a known point, and it does nothing at all for the settled-price
distribution, which stays truncated under both loci.

So the answer to "truncation or censoring" is: **the settled markup distribution is truncated under both
loci; only the attempt distribution differs, being truncated under A and censored-with-indicator under B.**
And the rows that settle exactly at $c$ are censored observations of the latent value in either case, not
measurements of it: a ticket sold at the cap went to whoever was fastest, which `01-b` §4.5(iii) records
as a statement about latency, not value, and which `01-a` §3(2) records as a mass point whose height
measures excess demand rather than value.

### 1.4 A terminology correction, recorded rather than silently applied

`01-a` §3 calls the first effect "left truncation", and `00-data-situation.md` Gap 2 says the observed
markup distribution is "left-truncated by design". On the usual meaning of the terms the tail removed is
the **upper** tail of the markup distribution: the missing rows are those above the ceiling, so the
markup variable is bounded above by policy and, when no row survives, the sample is truncated from above
and censored at its upper boundary. The substantive claim in both files is the one this section states —
the top of the distribution is not sampled and any mean or quantile from it is biased down by construction,
class C. I read "left" as shorthand for the lower end of the *price* axis relative to what the market would
bear, not as a statement about the markup axis, and I record the ambiguity here instead of editing either
file.

---

## 2. What is recoverable

`01-b` §1 states the position in one line: the ledger buys "a set of *one-sided lower bounds* on value
wherever the resale ceiling binds — not a price, not a demand curve". This section writes the bounds out,
names the assumption each one needs, says how its content scales with the share of sales at the ceiling,
and then answers the question the programme actually has to answer: whether a corrected value is
identified, or only bounded.

### B1 — the pointwise lower bound

**Statement.** For any settled resale at the ceiling, $V_i(t) \ge p_i(1+c)$. For any settled resale
below the ceiling, $V_i(t) \ge m_i$ in the same sense. Aggregated over a tier, the record identifies a
lower bound on every observed transaction and nothing on any unobserved one.

**Assumption.** That the settled figure is the whole consideration: no side payment, no priced bundle, no
wallet handoff carrying a separate cash leg. `01-a` §3(3) names exactly these channels and concludes that
at the cap the recorded markup is a lower bound with the bias largest where demand is strongest, and `F` D6
states the same thing structurally: the chain bounds the record, not the money. The assumption is
therefore not a modelling convenience, it is the known-to-be-violated clause, and violating it pushes the
true consideration further above the recorded one — which is why the bound stays a bound under the
violation rather than becoming wrong. *Class C for the bound; class D for the channels.*

**Where the bound is sharp and where it is empty.** It is sharp when the row is genuinely at the ceiling,
because the ceiling is a real constraint every paying buyer hit. It is nearly empty for rows far below the
ceiling, where it says only that a buyer paid what they paid.

### B2 — the lower bound on the survival function of willingness to pay

**Statement.** Because the ceiling is basis points over *each tier's own* face value, its absolute level
differs across tiers inside a single event as well as across events (`01-b` §5(3), §4.4(ii)). Each such
level at which sales are observed contributes one evaluation point: the settled buyers at that level all
had willingness to pay at or above it. Collecting the levels, the record identifies a **lower bound on the
survival function of willingness to pay, evaluated at the observed cap levels only**. `01-b` §4.4(ii)
records precisely this, and adds the two limits: sign and one-sided magnitude identified, **location not**.

**Assumption.** That the cap level is not set as a function of the event's or tier's latent demand. If
organizers set tighter ceilings on hotter events — a plausible policy, and an untested one — then the
points no longer trace one survival curve and the bound does not aggregate. This is the load-bearing
assumption behind `01-b` §5(3)'s claim that a varying cap is "an instrument, not merely a nuisance", and it
is an assumption, not a result. *Class C.*

### B3 — the demand bracket from the primary side

**Statement.** A sold-out tier is censored demand — demand met or exceeded supply at that price — and an
unsold tier is a point on the demand curve, so primary `issuedCount` against `totalSupply` at
`faceValueLamports` gives a demand bracket per tier, and `01-b`'s ledger records T4b as **bounded below at
each distinct cap level** from primary sell-through. *(Class B; UNVALIDATED for any functional form.)*

**Assumption.** Three, all named in `01-b`'s T4b row: uniform primary pricing, `faceValueLamports` equal to
the actual primary transaction price, and `issuedCount` meaning sold rather than minted. The second and
third are flagged again in `01-b` §5 as operator questions, and both are load-bearing. This bound is the
one place in the schema where a demand object is identified at all, and it does not touch the resale record.

### What is not obtainable, at any sample size

- **No upper bound on $V$, from the resale record.** Nothing above the ceiling is observed, so no statement
  of the form $V \le \cdot$ has support. `01-b` §6(2) lists "the location of the latent right tail above
  the cap" as buildable only on a stated assumption, with the test being a cap-free event, "until then only
  the mass is claimable".
- **No level.** T1 is identified only up to an affine normalisation with no free price anchor in the schema
  (`01-b` T1 row, §4.1, §6(2)). Every number above is a ratio or a one-sided comparison; none is a level.
- **No price-response curve.** T3 is not identified at all from trades — only the product of the sale
  hazard, the conditional ask distribution and the listing probability is (`01-b` T3 row). A capped event
  makes this worse, because the ask distribution itself is the censored object.

### How the bound's content scales with the share of sales at the ceiling

Two separate scalings, and they run in opposite directions.

**The bias scales up with $s$.** From §1.2's identity, the downward bias is
$s \cdot \mathbb{E}[m^{*} - c \mid m^{*} \ge c]$, so for a fixed latent excess the error in the naive mean
is proportional to the share of sales sitting exactly on the ceiling. This is why the failure is worst
exactly where the engine matters most: high $s$ is the observable signature of excess demand, so the events
with the strongest demand are the ones whose records are most compressed.

**The information scales down with $s$.** At $s \to 0$ almost the whole distribution is observed and the
truncation bias vanishes — the record is nearly a sample of resale prices, subject to the separate problems
in `01-b` §5 (no ask, case-only sample). At $s \to 1$ every surviving row is the boundary, so the only
statement left is $V \ge c$ repeated $n$ times, the survival-function bound of B2 is evaluated at a single
point, and the record has become a statement about the ceiling rather than about the market. The bound is
**valid at every $s \in [0, 1]$ and informative in inverse proportion to it.** No value of $s$ makes the
upper tail's location identified; $s$ only decides how much of the rest of the distribution survives
alongside the boundary.

Two cautions on $s$ itself. It is a **lower** bound on $\Pr(m^{*} \ge c)$, because a row landing exactly on
the ceiling may be a latent exact-ceiling agreement rather than a rationed one, and the two are
indistinguishable on the row. And it is biased **down** by the same off-rail leakage that biases the levels,
so a low $s$ is not the reassuring reading it looks like: `01-b` §5 notes that in the fixtures "no sale
lands exactly on any cap", which means the cap component cannot be exercised on the fixtures at all and $s$
is unmeasurable until real rows exist.

### Identified, or only bounded?

**Bounded, and only one-sided.** A corrected value is not identified from the contract as it stands, and no
estimator recovers it. The three reasons are independent, so fixing one does not fix the others:

1. **The level is not identified** — only ratios, because the schema contains no exogenous price anchor
   (`01-b` T1, §6(2)).
2. **The upper tail is not identified** — nothing above the ceiling is sampled, and the only named test is
   a cap-free event (`01-b` §6(2)).
3. **The consideration is not fully recorded** — the chain bounds the record, not the money (`F` D6), so
   even an at-ceiling row is a lower bound on what changed hands.

What the engine holds, then, is a **floor on value, and a lower-bound curve on willingness to pay evaluated
at the observed cap levels**. Everything downstream inherits this: T5 is set-identified with width equal to
the union of the T3 and T4 widths (`01-b` T5 row), and since T3 is not identified at all, the primary
optimum is a set, not a point — a conclusion `02-d` §6 already reflects when it prints a range and says "we
would not argue with any price in that range". Converting the floor into a point needs three observations,
and only one of them is a modelling choice: a cap-free event (tail), an exogenous price anchor (level), and
the per-listing ask panel (T3). Two of the three are data.

---

## 3. What the engine must do on a capped event versus an uncapped one

### 3.1 The two regimes, defined observably

The distinction is not `resalePriceCapBps != null`. A non-null cap with no mass point at the ceiling may be
a cap that does not bind, or a cap whose binding sales have all gone off-rail (§2's caution on $s$), and the
record cannot tell those apart. So the engine classifies on the pair:

- **Capped and binding:** $c$ non-null and $s > 0$ — at least one settled row at exactly the ceiling.
- **Capped, no mass point:** $c$ non-null and $s = 0$. Not a licence to treat the record as uncensored;
  it is a licence to say the ceiling's status is unknown.
- **Uncapped:** $c$ null. No policy ceiling, and therefore the only regime in which the top of the
  transaction distribution is sampled at all.

### 3.2 On a capped and binding event

**Do:** report the recorded markups, labelled as lower bounds. Report $s$ and $n$ as what they are — a
rationing statistic, the observable trace of excess demand, in the sense of `01-a` §3(2) whose height
measures excess demand rather than value. Report the value as a floor. Report the B2 lower-bound points at
each observed cap level, as separate points and not as a fitted curve. Report the T5 object as a set, per
`01-b`'s T5 row.

**Refuse to claim, on this event, all of the following:**

1. **A point value, or a mean, or an upper quantile of resale value.** Floor only (§2, and `01-b` §6(2)).
2. **That a sale at the ceiling reveals what the buyer valued the ticket at.** `01-b` §4.5(iii): the
   surplus above the cap does not accrue to the buyer, the allocation behind the ceiling is effectively
   random among those who want the good, and a ticket sold at the cap went to whoever was fastest — a
   statement about latency, not value. *(Class B.)*
3. **That a cap-free estimate transfers here.** Transfer is cross-event exchangeability, an assumption,
   never an identification result (`01-b` §4.6 makes this point about cold-start transfer).
4. **Any price-to-sale-probability curve, any elasticity, any demand-curve slope from these rows.** T3 is
   not identified from trades (`01-b` T3 row) and the ceiling censors the very ask distribution the
   identification would need.
5. **That demand is inelastic, or that the ceiling is not binding, or that the tier is priced right.**
6. **Any coverage or calibration number for a price distribution.** `01-b` §4.6: report the interval, label
   the calibration UNVALIDATED, quote no coverage number.
7. **Any class-A claim about caps.** `01-b` §4.5: there is no peer-reviewed econometric study of resale
   price caps in ticket markets; the cap component is class B borrowed from rent control plus class C
   theory.

### 3.3 On an uncapped event

**Do:** treat the transaction distribution as uncensored by policy, and treat this as the only regime in
which the location of the upper tail can be learned at all — `01-b` §6(2) names "a cap-free event" as the
test that would license a statement about the latent right tail. Use it to learn the tail, and say that is
what it is being used for.

**But do not treat it as a clean control.** An uncapped event still has no asking price anywhere in the
record (`01-b` §5(2): the asking-versus-realised gap does not shrink, it vanishes), still has no listing
exposure (Gap 1), still has no bid side (`01-b` §6(3)), and is still a case-only sample conditioned on sale.
Uncapped removes one failure out of four. Any sentence of the form "validated on the uncapped event" is
false, and the engine may not print one.

**And do not silently pool.** A pooled estimate across capped and uncapped events is a mixture of a truncated
and an untruncated distribution, which is worse than either alone: it produces a number with no regime label
attached. Pooling requires the cross-event exchangeability assumption to be stated on the row.

### 3.4 The exact wording, and the line it replaces

`02-d` §6 already ships an organizer report, and on a capped event one of its lines is unsupportable. The
line is:

> **Range: {P_lo} to {P_hi} SOL. We would not argue with any price in that range.**

On a capped and binding event that must be replaced, because `{P_hi}` would be an assumption wearing a
measurement's clothes. Replacement text, in the same register, with the numbers substituted:

---

**The resale price in this tier is capped at {c}% over face, and the cap is binding: {k} of {n} recorded
resales ({s}%) settled at exactly the ceiling. Those buyers each paid the most the platform allows, so the
record shows what was paid, not what buyers would have paid, and every sale the ceiling turned away is
missing from it entirely.**

**Value: at least {m} SOL per ticket. That is a floor, not an estimate.** It is the {q}th percentile of
{n} recorded resales, and it is the most this record can support: sales at the ceiling are the market
rationing by speed instead of by price, so they measure who was fast, not what the ticket was worth, and
they understate value most on the tiers with the most demand.

**Range: {P_lo} SOL and up. We do not state an upper bound from this record.** The upper end is not
measured. It is set by the assumption {assumption name}, and we will not present it as a measurement.

---

And the corresponding refusal line belongs in `02-d` §6's "The recommendation is wrong if any of these is
true" list. `02-d` already carries its analogue — "the resale prices in the record are capped and leaked
off-ledger … the true willingness to pay is higher than the record shows and the price should be higher
still. We cannot see the leak." `02-b` sharpens that bullet in one respect and must not overstate it in
another: the direction is established (class C) and the leak is *not* the only channel — a cap that binds
without leaking already biases the record down — while the magnitude remains unobservable, which is the part
`02-d` gets exactly right.

On a capped event with $s = 0$, and on an uncapped event, the original range line stands as written. That is
the switch rule, and it is one line of code: the replacement text is conditioned on $c \ne \text{null}
\wedge s > 0$.

### 3.5 Reconciliation with `02-d`: consistent, and here is why

`02-d` §2.5(b) establishes that **a proportional cap is not a constraint on the organizer**: raising the
primary price $p$ by a factor $\lambda$ raises the ceiling to $\lambda p(1+c)$, so the reseller can still
resell at the same proportional markup, and the only things stopping the organizer from raising the price
are the demand curve and the organizer's uncertainty about it. §2.5(a) states the scale invariance —
the feasible band $[p, p(1+c)]$ translates with the decision — and §2.5(c) uses it to show the resale market
adds no separate cross-price term, since the buyer's outside option is a function of $p$ rather than an
independent price. §2.5 closes by naming the condition: a fixed-absolute cap would break all three and force
an extra term into the objective equal to the shadow value of the rationed quantity behind the ceiling.

**There is no contradiction, because the two records are about different price variables, and each one's
statement is silent about the other's.**

1. **The variable differs.** `02-d` is about the organizer's own price $p$ and the feasibility of the
   primary pricing decision. `02-b` is about the *resale transaction record*, whose top is $p(1+c)$. A
   statement that $c$ does not remove any $p$ from the organizer's feasible set says nothing about whether
   $p(1+c)$ truncates the distribution of resale prices above it.
2. **Scale invariance is a statement about shares, not about truncation.** Because the band translates,
   the *share* of resale sales landing at the ceiling is invariant to the level of $p$. It is not zero, and
   invariance is exactly what makes `02-b`'s problem permanent: raising $p$ raises the ceiling in
   proportion, so a resale demand that exceeded the ceiling at the old $p$ exceeds it at the new one too,
   in the same proportion, and the tail stays outside the record. The engine cannot price its way out of a
   censored sample by raising the primary price.
3. **The direction of dependence runs one way.** `02-d` §2.5(c) holds *because* the ceiling binds the
   reseller's ask — that is the premise of the outside-option argument. The same ceiling that makes the
   buyer's outside option a function of $p$ is the one that empties the record above $p(1+c)$. Truncation
   is therefore the premise of `02-d`'s simplification, not a competing claim about it.
4. **They meet at one number, and they agree there.** `02-d` §6 takes the resale record as its first input:
   "the price this tier's tickets actually resell for … the only measurement of what buyers will pay". On a
   capped and binding event that measurement is a floor (§2), so the recommended primary price inherits a
   downward bias in exactly the direction `02-d` §6's own warning bullet already states. `02-b` adds the
   mechanism and the sign; `02-d` already ships the hedge. Neither record needs to change its conclusion.
5. **The validity conditions differ, and that is worth recording.** `02-d` is void if the cap becomes
   absolute. `02-b` is not void in that case — an absolute cap truncates the record harder and independently
   of $p$, and it removes §2's scale-invariance caveat on B2 rather than adding one. So the two records fail
   in opposite directions on that contingency: a definition change would cost `02-d` its clean objective and
   would cost `02-b` nothing structural.

**Verdict: consistent.** No claim in `02-d` §2.5 has to be withdrawn, no claim in this section has to be
withdrawn, and the sentence that keeps them apart is one line: *the cap does not constrain the organizer's
price, and it does constrain the record of what resellers got.*

---

## 4. The one data change, checked against episode sampling

`delistReason = cap_blocked` is necessary and not sufficient, and the episode-sampling rule is what shows
why. If the sale-hazard subcohort is sampled from listing episodes rather than tickets — a ticket relisted
three times contributing three at-risk intervals at three different asks — then the value of the enum lies
entirely in what the episode carries beside it, because an enum value with no ask and no end time is a
label on an interval that cannot be placed in the price dimension or the time dimension. What the value
buys is the one object the settled record structurally cannot contain: an ask above the ceiling together
with a refusal, which under §1.3's Locus B is a right-censored observation of the seller's reservation,
upgrading the top tail from invisible to bounded below at a known point. What it does not buy, and this is
where more is needed: it presumes the platform is the gate, and under the enforcement locus this programme
has actually designed (`F` D6 — the cap checked in `transfer_ticket` before the transfer CPI, with refused
attempts deliberately not recorded because doing so charges the seller for being refused and is floodable)
a blocked attempt never reaches the platform and creates no episode at all, so the enum would never fire and
the record stays truncated in the strict sense of Locus A; it needs `listPriceLamports` on the same episode
or the censoring point is "some ask above the ceiling" rather than a number, and it needs the reason to be
exclusive, since the design already carries a second refusal (the verified-wallet rule) and a single
conflated reason would let a wallet rule read as a price ceiling; and it reveals asks, never willingness to
pay and never the off-rail consideration, so the rationing quantity itself still has to be measured the only
way it can be — as the sale hazard *at the ceiling* against the hazard below it, which requires the
episode's end time and the cap level joined onto the episode at its policy version, because `F` D6 makes
the cap immutable per event and a join on the current policy value would mis-attribute any event whose
policy was created under a different one. So the honest minimum is the four Gap-1 fields carried per
episode `{listPriceLamports, listedAt, delistedAt | soldAt, delistReason}`, with `delistReason` separating
sold from withdrawn from cap-blocked, and the cap value attached to the episode; and even that ceiling of
achievement is bounded, because a fast sale at the ceiling identifies the rationed quantity and not the
location of the latent tail, which still needs a cap-free event (`01-b` §6(2)) and which no field on this
schema supplies.

---

## Sources

Reasoning over findings already on disk; no new sources were read for this report, and no figure appears
above that is not in one of these five files.

1. `records/findings/01-a-market-structure.md` — §3, caps: whether they bind and what a binding cap does to
   the distribution (the three observational effects, the evasion channels, the NSW and UK figures, the CMA
   calibration).
2. `records/findings/01-b-identifiability.md` — the identification primitive (§2), the identifiability
   ledger (§3), T4 and the free lower bounds (§4.4), T5 (§4.5), the disagreements with the audit (§5), and
   the three design consequences (§6).
3. `records/findings/02-d-elasticity-fees-optimum.md` — §2.5 (the cap, scale invariance, and the condition
   under which the section is void) and §6 (what the engine reports to an organizer, including the range
   line and the "recommendation is wrong if" list that this report amends).
4. `records/00-data-situation.md` — Gap 2, the policy truncation with rationing behind it; Gap 1 for the
   four-field listing fix referenced in §4.
5. `records/F-decision-log.md` — Q3 (the open question on the cap's enforcement locus) and D6 (the
   enforcement locus this programme's own design settles on, the refusal-recording decision, and the
   side-payment residual).

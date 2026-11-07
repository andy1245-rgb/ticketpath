# Phase 3-A — Cross-domain interactions, and the causal verdict on each

**Status:** complete (first pass). **Written:** 2026-11-07T11:52Z UTC.
**Agent:** Phase 3-A research agent (`p3-interactions`).
**Scope:** `RESEARCH-PROGRAM.md` §3 PHASE 3 in full, with §4.2 (mechanism before feature inclusion),
§4.7 (predictive versus causal) and §4.8 (temporal correctness) as the admission rules. One subject:
which interactions between the primary price, the capped resale record and the wallet-bound ticket
actually bind in *this* market, and for each one whether the relationship is causal, predictive, or an
artefact of the recording policy.

**Depends on:** `AGENTS.md`; `RESEARCH-PROGRAM.md` §4 in full; `records/README.md` (evidence classes);
`records/00-data-situation.md` (the observation set and its four gaps); `records/F-decision-log.md`
(D1–D6, Q1–Q3); `records/findings/01-a-market-structure.md`; `01-b-identifiability.md` (the
identifiability ledger, which constrains what an interaction feature can be estimated for);
`01-d-external.md` (Tables C-1, C-2, and §5's predictive-versus-causal pass); `records/C-variable-registry.md`
(V1–V17 and the recorded interaction notes); `../ticketing-frontend/lib/types.ts` (verified by
reading it in this pass, 220 lines) and `API_CONTRACT.md`.

**Phase 2 files present when this was written** (all five, verified on disk before the first sentence):

| File | Size | mtime (UTC) |
|---|---|---|
| `02-a-price-paths.md` | 73.0 KB | 2026-11-07T11:30Z |
| `02-b-cap-truncation.md` | 30.5 KB | 2026-11-07T11:28Z |
| `02-c-sale-hazard.md` | 81.9 KB | 2026-11-07T11:02Z |
| `02-d-elasticity-fees-optimum.md` | 60.1 KB | 2026-11-07T11:05Z |
| `02-e-cold-start.md` | 78.5 KB | 2026-11-07T11:33Z |

None was missing. Each was read in full except where a section header says otherwise. Also present and
used: `03-b-temporal-correctness.md` (85.0 KB, 11:30Z) — the decision-time ledger this file's feature
definitions defer to for every "when is it knowable" claim, and `02-ai-ml-decision.md` for the estimator
boundary. **No `03-a` existed before this file.**

**Append-only.** Disagreements with prior records are in §6, recorded and not resolved. No number below
comes from `lib/mock/`. No magnitude and no p-value is invented: every quantity is either quoted with
the file and section it came from, or derived in one line of algebra that is shown.

**Marking convention.** Every load-bearing claim carries a class (A–E per §4.3, plus SIM and UNVALIDATED
per `records/README.md`) and one of:
**[QUOTED]** — read from a named file/section or a named source in one of them;
**[DERIVED]** — algebra on quoted inputs, shown;
**[ASSERTED]** — my reasoning or a specification choice, with no measurement behind it.

---

## What I concluded

1. **"Interaction" is being used in this market for three different objects, and conflating them is the
   error this phase exists to prevent.** There are (i) *structural* interactions — two factors whose
   effect is a product because a constraint makes them so, e.g. the cap truncating the markup record,
   which needs no behaviour and no estimation; (ii) *behavioural* interactions — two factors whose effect
   is a product because a person's decision depends on the other factor, e.g. a seller cutting faster
   when the deadline is closer; and (iii) *accounting* interactions — two variables that move together
   because a third, unobserved variable moves both. Only (i) and (ii) are features. (iii) is the thing
   §4.7 exists to keep out, and in this programme (iii) is the majority. **[ASSERTED]**

2. **Exactly two interactions bind in this market, in the sense defined in §0: the markup conditional on
   the resale cap binding, and the time-to-event slope conditional on popularity.** The first is
   structural and its sign is certain from the record's own construction. The second is behavioural, has
   class A support for both of its opposing forces, and decides the sign of the only forecastable object
   the engine has. Everything else in the required list is either an expression of the same latent-demand axis
   that this contract cannot separate from the organiser's own price, or a plausible story with no evidence.
   **[ASSERTED]**

3. **The cap interaction is not a behavioural finding and must stop being reported as one.** What the
   record contains is $\tilde m = \min(m^*, c)$, so the observed markup distribution is a truncation plus
   a mass point, and the naive mean is biased down by $s\cdot\mathbb{E}[m^*-c\mid m^*\ge c]$ where $s$ is
   the share of sales at the ceiling (`02-b` §1.2). That identity is class C and needs no data. The
   behavioural part — sellers settling above the cap off-rail, sellers exiting at the top, listings
   suppressed — is class D on magnitude and unobservable in the record. Two consequences the engine has
   to live with: a sale at the cap measures who was fastest, not what the buyer valued (class B, `01-b`
   §4.5(iii)), and $s>0$ proves the ceiling binds while $s=0$ proves nothing (`02-b` §1.2). **[QUOTED,
   class C for the identity; class D for the behavioural channels]**

4. **The cap does not constrain the organiser's price and it does constrain the record. Those two
   statements are both true and the engine needs both.** `02-d` §2.5(b) shows a proportional cap is not a
   constraint on the organiser: raising $p_0$ raises the ceiling $p_0(1+c)$ in the same proportion. `02-b`
   §3.5 shows that scale invariance is exactly why the truncation is permanent: the *share* of sales at
   the ceiling is invariant to $p_0$, so raising the price does not price the engine out of a censored
   sample. I adopt both and record the one line that keeps them apart. **[QUOTED]**

5. **One of the seven feedback loops the programme names is a genuine dynamic system inside this product's
   scope: the loop from the recommended price to the data the next event's model is trained on.** It has a
   one-event lag, it is unavoidable, and it makes the deployment distribution differ from the training
   distribution as a matter of construction rather than as covariate shift (`03-b` §5 P3). Four of the
   remaining six collapse completely because their state variables are absent from the contract: inventory
   releases, seller price revisions, visibility, and listing decisions. One collapses to a static
   *simultaneity* (the buyer's resale option is part of willingness to pay at the primary price), and one
   collapses to a static constraint (the cap translates with the decision). §3 says which is which.
   **[ASSERTED, from the contract's absence list]**

6. **No dynamic model is justified and a state-space layer would be a cost with no state to put in it.**
   The contract carries no price-mutation endpoint and no listing panel, so a repricing policy has no
   action space and no state variable to condition on (`02-d` §4.4). The one dynamic object that *is*
   needed is a within-horizon path, which `02-a` §8 already specifies, and one root-find per candidate
   price for the cap-binding window. Anything more is a model of a market the product cannot act in.
   **[QUOTED, `02-d` §4.4; ASSERTED for the conclusion]**

7. **The interaction the product most needs is the one the record cannot supply, and no amount of
   modelling fixes it.** The sale hazard conditional on the ask is a case-only sample: the ask is recorded
   only where the sale happened, so the observed rate is
   $\lambda(t\mid p)\cdot\pi(p\mid \text{listed},t)\cdot s(t)$ and nothing separates the three factors
   (`01-b` T3; `02-c` §1.1–1.2). It is registered here as I13 rather than omitted, because a registry that
   silently drops the central interaction invites a later agent to rediscover it as an estimate.
   **[QUOTED, class C; D — dangerous precisely because it will look estimable]**

8. **Twelve interaction features are specified precisely enough to build. Six run on the record as it
   stands, five more run on fields that exist but need either a logged vintage or a component this
   programme has specified and not built, and one — the fee wedge — is blocked on a settlement field the
   contract lacks.** The split: six with no new field and no upstream component (IF-02, IF-04, IF-06,
   IF-07, IF-10, IF-11); two with no new field but blocked on the platform logging the value at decision
   time rather than returning an extraction-time snapshot (IF-01, IF-05); three blocked on an upstream
   component that is specified and not built, namely the path model or the event panel (IF-03, IF-08,
   IF-09); one blocked on Gap 4 (IF-12). §4 gives every definition with its inputs, its clock, its sign, its
   failure mode and its buildability. **[ASSERTED, verified field by field against `lib/types.ts`]**

9. **Three of the required interactions are unfalsifiable here and should be recorded as such rather than
   studied.** Cold start conditional on category (the category does not exist), price momentum conditional
   on seller concentration (momentum is estimated on the success branch and concentration is a lower bound
   because a wallet is not a person), and custody-hop speed conditional on tier (nothing in the literature
   measures hop speed at all — `01-a` §5 records that no published distribution of holding duration or
   transfers per ticket could be found). Each is registered, classed, and given the one measurement that
   would revive it. **[QUOTED for the absences]**

10. **The experiment that would change the engine most is not a secondary-market one.** It is the
    randomised tier-face design in `02-d` §3.6, because confirming that the primary demand elasticity
    varies with remaining inventory converts the deliverable's headline from a boundary rule into an
    interior optimum, and because randomising $p_0$ randomises the cap in money as a free by-product.
    The best secondary-market experiment (the listing panel) changes the resale product but leaves the
    primary price where `01-b`'s T5 puts it, as a set, because of selection on issuance (`02-c` §2.3, N4).
    §5 is ordered on that logic. **[ASSERTED]**

---

## 0. What "binds" means here, so the claim in point 2 can be checked

An interaction **binds** if all three hold.

1. **It is present in the record we will have**, not only in a record we could ask for. The contract is
   `lib/types.ts`; the four-field listing panel is not in it (`F` D3).
2. **Omitting it changes the sign, or the existence, of a recommendation** — not merely its precision.
   An interaction that narrows an interval is engineering; one that flips a price is economics.
3. **Its sign is known from something other than the data in front of us**: a constraint (class C by
   construction), a derivation, or a published measurement in a comparable market.

An interaction that fails (3) but passes (1) and (2) is **registered, class D, and not used**. An
interaction that fails (1) is a **data requirement**, not a feature, and it is listed in §5 rather than
§4.

Applying the test is what produces the count of two. I5 passes all three without qualification. **I2 passes
(2) and (3) fully and (1) only through a proxy**: the observable stratifier in the record is the cap mass,
which is ledger-derived and computable today (IF-02), while the better stratifier — primary sell-through —
exists as a field but not as a time series. That proxy is itself a function of $p_0$, so I2 is carried as a
*stratum whose contamination is printed*, which is the honest form rather than a clean one. I3 passes (3)
one-sidedly and fails (2)'s stronger reading — it changes the *direction* of a recommendation for a
sold-out versus an unsold event but supplies no magnitude, so it is called *one-sided* throughout and not
counted. I9, I6 and
I11 bind in the *objective* rather than in the data: they are structural facts the optimiser implements
and cannot estimate, which is a legitimate third category and is labelled as such in §1. I13 binds in what
the product may claim and not in what it can compute.

---

## 1. The interaction registry

Thirteen rows. I1–I8 are the interactions the brief requires; I9–I13 were added in this pass because each
one changes a decision, a claim, or the form of an estimator, and none of them appears in the required
list. "Acts?" means: does the product's decision variable (the primary price per tier at D1, and the
in-band estimate at D2) change if the term is included?

| # | Interaction | Mechanism, through whom | Predicted sign | Acts? | Class | Binds? |
|---|---|---|---|---|---|---|
| **I1** | Inventory depletion × demand intensity | Buyers: rivalry for the remaining units raises the marginal buyer's bid. Organiser: remaining capacity is a perishable asset, so the optimal remaining price rises as supply falls *if* demand is intense and is flat if it is not. | + and increasing in intensity; **zero when demand is slack** | No (state, not lever) | C (revenue management) + B direction | No — both factors are outcomes of the same latent demand *and* of the organiser's own $p_0$; inventory has no clock |
| **I2** | Time-to-event × popularity | Sellers: option value of holding decays as selling opportunities run out, so the ask falls (class A, Sweeting 2012). Buyers: arrivals rise toward the door, so the bid rises (class A as arithmetic on Leslie & Sorensen's shares, `02-a` §5.3). | slope **negative** in soft/popular already-cleared events; **≈0 or positive** when excess demand survives to the door | **Yes** — sets the level at D1 | A for the two forces; **D** for the net sign here | **YES** |
| **I3** | Resale premium × primary inventory remaining | Rationing at face leaves willing buyers unmatched, who enter the resale market; unsold supply at face means the marginal buyer's WTP is at or below face. | **+**, one-sided: sold out ⇒ resale ≥ face; not sold out ⇒ marginal resale ≤ face | Yes, indirectly (sell-through is the only pre-resale demand observation) | C by construction; A support (auctions remove the arbitrage, Budish & Bhave 2023) | **One-sided only** |
| **I4** | Price momentum × seller concentration | Sellers: professional repeat sellers price to a schedule, cut earlier and deeper, hold shorter (class A in MLB for professionals setting lower prices, Sweeting 2012). Competition: more professionals ⇒ more undercutting. | − on level, − on slope as concentration rises; + on hazard | No directly; changes the D2 forecast | A in MLB; **D** here; momentum object is success-branch only | No — three independent reasons, §2 |
| **I5** | **Markup × the resale cap binding** | Policy: the ceiling is a hard constraint, so the market clears by speed and rationing, not by price (`01-a` §3). Record: $\tilde m=\min(m^*,c)$, a mass point at $c$ and no rows above it. Behaviour: sellers settle the residual off-rail, or exit at the top. | **−** on every observed mean and upper quantile (certain, from the identity); **+** on the average transaction price if a stringent cap pushes high-price sellers out (He & Lin 2026, model result) | **Yes** — it is a parameter of the data-generating process and it moves with $p_0$ | **C** for the truncation; B for rationing; **D** for evasion magnitude; A that caps leak in practice | **YES** |
| **I6** | Elasticity × remaining inventory | Buyers: the quantity response flattens near capacity, so a given price rise costs less volume; truncation makes $q'$ less negative as the house fills (`02-d` §5.1(a)). | $\lvert\epsilon\rvert$ falls as remaining inventory falls; the optimal price **rises** | **Yes** — it decides boundary versus interior optimum | C | In the **objective** (imposed, not estimated) |
| **I7** | Cold-start degradation × event category | Buyers: between-event variance is dominated by *what the event is* (draw, rivalry, one-off versus recurring), so pooling across categories transfers the wrong prior. | unknown; the band widens if category explains between-event variance | Only by declining to pool | **E** — the field does not exist (`03-b` A29) | No — the conditioning variable is absent; the real cold-start interaction is with exposure, not category |
| **I8** | Custody-hop speed × the ticket's tier | Sellers: churn concentrates where the margin per hop is largest, so tops tiers on hot events should turn faster. Buyers: tier fixes the depth of the buyer pool. | hops per ticket-day **+** in top tiers on tight events; holding duration **−** | No; a velocity feature for the D2 forecast | **D** — no published measurement of hop speed exists (`01-a` §5) | No, but it is the cheapest novel measurement the ledger offers |
| **I9** | Cap binding × the chosen primary price | Policy: the ceiling in money is $p_0(1+c)$, so the binding *window in days* is an output of the decision (`02-a` §7.2). Buyers: the resale option's value rises with $p_0$ (class D). | $\partial s/\partial p_0\approx 0$ (share-invariance); $\partial W/\partial p_0<0$ (window shortens); option-value channel **+** | **Yes** — it *is* the decision | C | **Yes**, in the objective and in the learning loop |
| **I10** | Verified-wallet gate × demand tightness | Buyers: the gate shrinks the pool (lower price/arrival) and certifies seriousness (higher WTP among admitted). Which dominates depends on whether the event is oversubscribed. | **unknown, and not a sign** — the pooled number is a mixture of two regimes (`03-b` §5 P2) | No — organisers set it; the engine stratifies on it | **D** | No — no within-event variation; collinear with time if platform-wide |
| **I11** | Fee wedge × elasticity | Organiser: $p^*=c^{**}\eta/(\eta-1)$, so a per-unit fee moves the price only through the elasticity while an ad-valorem fee cancels. | $\partial p^*/\partial f>0$; $\partial p^*/\partial\eta<0$; $\partial p^*/\partial\phi=0$ | **Yes** — this is the objective | C | In the **objective**; both parameters are configuration (Gap 4) |
| **I12** | Cap stringency × seller concentration | Sellers: a stringent cap removes the high-price end of the ask distribution, so the sellers who remain compete less and the average transaction price can **rise** (He & Lin 2026, *Marketing Science* 45(3), model result). | + on average transaction price; − on listing depth | Yes, once, at event creation (the cap is immutable, `F` D6) | C (model); A that caps leak | No — untestable here: $c$ is chosen as a function of expected demand, which is why `01-b` CORRECTION 2 withdrew the within-event instrument claim |
| **I13** | **Sale hazard × the ask** | Buyers: a higher ask lowers the arrival-to-sale rate. The mechanism is not in doubt; the identification is. | **−**, magnitude unknown; $\gamma$ identified only from within-$(e,g,\tau)$ ask dispersion (`02-c` §4.4) | Yes — it is the sentence the product promises | C for the mechanism; **not identified** here | Binds in what the product may **claim**, not in what it can compute |

### 1.1 The two that bind, in prose

#### I5 — markup conditional on the cap binding

This is the only interaction in the registry whose sign is fixed by the record's construction rather than
by measurement, and it is therefore the only one that can be built with confidence today.

**The formal shape, adopted from `02-b` §1 without alteration.** Each settled resale is a row carrying
`priceLamports` and therefore `markupBps` $m=(\text{resale}-\text{face})/\text{face}\times 10^4$, and the
policy field is a ceiling on that quantity, $c$. Write $m^*$ for the markup the parties would have agreed
had the ceiling not applied. The record contains $\tilde m=\min(m^*,c)$, so with
$s=\Pr(m=c\mid\text{settled})$:

$$\mathbb{E}[m\mid\text{settled}]=(1-s)\,\mathbb{E}[m\mid m<c]+s\,c,\qquad
\text{bias}=s\cdot\mathbb{E}[m^*-c\mid m^*\ge c].$$

Two readings of that identity matter and both are load-bearing for the engine.

*The bias is increasing in $s$, and $s$ is highest exactly where value is highest.* A high cap-hit share
is the observable signature of excess demand. So the events where the engine matters most are the events
whose records are most compressed. This inverts the error rather than merely shrinking the sample: fit a
mean on observed markups and the hottest events will read as the *least* valuable. **[DERIVED from the
identity, class C; the inversion is `01-a` §3's, class C]**

*The information is decreasing in $s$.* At $s\to0$ the truncation bias vanishes and the observed rows are
nearly a sample of resale prices, subject to the separate case-only problem. At $s\to1$ every surviving row
is the boundary and the only statement left is $V\ge c$ repeated $n$ times. The bound is valid at every
$s\in[0,1]$ and informative in inverse proportion to it. **[QUOTED, `02-b` §2]**

**Why it binds rather than merely applies.** Three reasons, and the third is the one that decides it.

1. It changes the **form** of the estimator, not a coefficient: the likelihood is truncated at a known
   bound and the reported object is a floor plus a rank statistic, not a mean. A model that ignores it is
   not a worse model, it is a model of a different variable.
2. It changes the **floor the optimiser sees**: `02-d` §6 takes the resale record as its first input, so a
   downward bias in that input propagates into the recommended primary price in a direction already known.
3. It is the only interaction in the registry that survives **whatever the data turn out to be**. If the
   cap never binds, $s=0$ and the identity is an equality with no bias — the feature is still the right
   feature, returning zero. Every other interaction in §1 could turn out to be absent.

**What it is not.** It is not evidence that buyers value a capped ticket at the cap. The allocation behind
a binding ceiling is effectively random among those who want the good, so observed consumption carries no
information about the rationed buyers' valuations (`01-b` §4.5(iii), class B, Glaeser & Luttmer 2003), and
competition dissipates the surplus above the ceiling through non-price channels (Bulow & Klemperer 2012).
A ticket sold at the cap went to whoever was fastest. **[QUOTED]**

**The one place it is generous.** A sale at exactly the cap is a latent quantity pinned to a known number:
at the crossing date $d^*$ the latent markup equals $c$ and $c$ is observed, not estimated. That is the
only known-level point in the whole observation set, and `02-a` §6.1 (C4) records it as a partial answer
to `01-b`'s T1. It is interval-identified, with width equal to the gap between the last sale at the cap and
the first below it, and off-rail settlement pushes $d^*$ *later* than the true crossing. **[QUOTED]**

#### I2 — the time-to-event slope conditional on popularity

This is the interaction that decides the sign of the only forecastable object the engine has, and it is
the one the literature is most often misread on.

**Two forces, both measured, pointing opposite ways.** On the seller's side, the option value of holding
falls as selling opportunities disappear: controlling for ticket quality, prices decline significantly as
the event approaches, and sellers cut by 13%, 18% and 40% of face value across successive relistings with
"40 percent or more" over the final month (Sweeting 2012, class A). On the buyer's side, arrivals rise: 25%
of concert resales occur in the final 7 days and 50% within 26 days, which makes the per-day arrival rate
in the final week 2.7 times the rate in the three weeks before it — arithmetic on Leslie & Sorensen's own
reported shares, no assumption about window length (`02-a` §5.3, class A as arithmetic). **[QUOTED]**

The measured net in both MLB studies and in the concert sample overall is a fall, so the seller side
dominates there. But that is the outcome of a race the literature shows can go either way, and the one
concert dataset that measures the path conditional on seat quality reports "a modest uptick in the last
week" (Leslie & Sorensen 2014, class A). Two peer-reviewed studies, two markets, opposite signs in the last
48 hours; `02-a` §3.5 records the conflict and does not resolve it. **[QUOTED]**

**Why the interaction and not the slope.** Fitting a single average slope across events returns a number
near zero and hides both effects — that is `01-d` §4's prediction in terms, and it is the reason this
interaction passes the "changes the sign or existence of a recommendation" test while a main effect does
not. What separates the regimes is the state of remaining supply, not calendar time: Sweeting's decline is
in opportunity cost *conditional on a listing still being unsold*, and Leslie & Sorensen's near-flat path
is for events that had active resale at all. **[QUOTED, `01-a` §2]**

**And the conditioning variable is the problem.** In this contract "popularity" is not observable. The
candidates are primary sell-through, which is a snapshot with no clock and no sell-out time
(`00-data-situation.md` §4), and the cap-hit share, which is the only observable trace of excess demand
but is itself a function of $p_0$ (`03-b` §5 P1, last paragraph). So I2 binds in the mechanism and is
carried in the engine by a **stratum**, not by a regressor — and the stratum is policy-contaminated. That
is the honest form and §4's IF-01 is written to enforce it. **[ASSERTED, class C for the structure]**

**The one-sided test that needs no price.** The rate of sales per ticket-day at risk is identified, because
the ticket population is censused (`01-b` §4.3; `02-c` §2.3). If that rate *falls* toward the event, the
deadline story is refuted outright: sellers conceding should clear more and buyers arriving should arrive
more. A flat profile neither confirms nor refutes it, because the composite intensity cannot separate the
offering rate from the clearing rate. The informative combination is a rising profile with a falling price,
which says sellers are conceding while the market gets busier. That test is cheap, can be pre-registered
now, and is the first item in §5. **[QUOTED, `02-a` §5.4; `02-c` §1.2 for the composite]**

### 1.2 Why the rest are registered and not used

A one-line reason each, so a build agent does not have to re-derive the exclusion:

- **I1** fails the binding test on confounding alone: event quality drives the primary price and the resale
  volume together (`01-d` §5), and the organiser's own $p_0$ drives both depletion and resale price
  (`03-b` §5 P3). Including it as a free regressor reads the company's past decisions back as a law of
  nature. It is admissible as *state*, never as a regressor.
- **I3** is one-sided and cannot supply a magnitude, because "inventory remaining" is a snapshot with no
  sell-out time and the premium is recorded only as a capped markup. It survives as a sign.
- **I4** fails on three independent counts: the momentum object is measured on the success branch (the
  intersection, not the path — `02-a` §4.4), the concentration measure is biased up at small $n$ and is a
  *lower* bound on true concentration because a wallet is not a person (`01-b` §4.6(b)), and the cap
  changes who sells at all (I12).
- **I6** and **I11** bind in the objective. They are implemented as structure and never estimated here;
  the distinction is important enough that §4 gives each an explicit "not a fitted parameter" note.
- **I7** is class E: the conditioning variable does not exist. The real cold-start interaction is with
  accumulated exposure, and that one is computable (`02-c` §6.1) — IF-08.
- **I8** is class D and cheap to measure, which is the only reason it is in the registry at all.
- **I10** is a mixture rather than a bias, so it has no sign to report; it is a stratification key.
- **I12** cannot be tested in this market for the reason `01-b` CORRECTION 2 gives, and it is the one row
  where the naive reading ("a tighter cap lowers recorded prices") could be wrong in sign.
- **I13** is the central missing interaction; it is in the registry so that no later pass mistakes a
  fitted $\lambda(p)$ for it.

---

## 2. The causal verdicts

Five threats are in play, named as the brief names them. The verdict is one of three: **causal** (an
intervention on the first factor moves the second, and the product can act on it), **predictive-only**
(useful in a forecast, not usable as a lever, and the association survives only under a stated
condition), or **artefact** (the relationship exists because of how the record is produced).

| # | Verdict | Threat that binds | Why that threat, specifically | What would separate causal from predictive |
|---|---|---|---|---|
| I1 | predictive-only | **confounding** and policy creation | Event quality moves the primary price, the resale volume and the depletion rate together; $p_0$ moves depletion and markup together | a randomised $p_0$ (E3), or a demand shock with $p_0$ fixed |
| I2 | **causal in mechanism, predictive in implementation** | **confounding by the conditioning variable** | "Popularity" is measured by sell-through, which is the organiser's own choice, and by cap mass, which is a function of $p_0$ | the cap-mass trajectory as a sign test (E1) plus the period-effect diagnostic (E7) |
| I3 | **causal, one-sided** | **simultaneity** and policy artefact | price and quantity are set together at the primary; the cap converts the premium statement into a floor | a randomised face (E3), or a cap-free event (E4) |
| I4 | predictive-only | **selection** and policy artefact | only sold tickets are observed, so momentum is the intersection of ask and bid; the cap changes which sellers transact | the listing panel (E2), which shows a decision rather than a trade |
| I5 | **artefact of the recording policy** (class C) **with a causal behavioural component** (class D) | **policy-created artefact**, then confounding with demand | the ceiling is enforced, so the top of the distribution is not sampled; and because it binds hardest on hot events, cap-binding is a proxy for demand and cannot be used as one | a cap-free event for the tail's location (E4); `cap_blocked` plus the ask for the rationing quantity (E2); dark-ticket detection for the leak (E5) |
| I6 | **causal (theory), not identified** | **simultaneity** and selection on issuance | the demand curve is not identified from trades (`01-b` T4b); and the population is tickets that someone bought at the price actually charged (N4) | E3, and nothing else |
| I7 | not estimable | none available to name | there is no measurement, so there is no threat to separate | the category field |
| I8 | predictive-only | **selection** and measurement | only tickets that transacted have hops; and a wallet is not a person, so key handoff removes the transfer entirely (`01-a` §6) | a hop panel with the gate as a stratum (E6) |
| I9 | **causal by algebra** | **no confounding — a self-inflicted shift** | the ceiling in money is $p_0(1+c)$; the engine's own recommendation changes the record it will learn from | nothing in-sample; logged recommendation and acceptance (propensity) is the only fix |
| I10 | **mixture, not causal and not predictive** | **policy-created artefact** and collinearity | within an event the flag does not vary, so no effect is identified from one event's history; if it is platform-wide it is collinear with calendar time | a platform-level A/B (E9) |
| I11 | **causal by algebra** | none econometric | $\partial p^*/\partial\phi=0$ and $\partial p^*/\partial f>0$ are algebra; the risk is assuming fees are zero, not misattributing a correlation | one settlement field (E10), which makes $c^{**}$ measured rather than assumed |
| I12 | **causal in a model, untestable here** | **policy endogeneity** | $c$ is chosen by the organiser as a function of expected demand, so cross-event variation in $c$ is not exogenous | a policy change not conditioned on demand, which no organiser runs voluntarily |
| I13 | **not identified** | **selection** (case-only), **endogenous ask**, and **collinearity with $\tau$** | the ask is recorded only on the success branch (Working 1927: a locus of realised prices traces neither curve); sellers choose the ask on private information; and asks fall while hazards rise, so $(z,\tau)$ is nearly collinear by construction (`02-c` §4.4) | listing episodes with **ask dispersion among simultaneously live listings** — the fields alone are not enough (`02-c` §4.4) |

### 2.1 The three that need the argument spelled out

#### I5 — why "artefact" is the right word and why that does not make it unimportant

An artefact, in this file's usage, is a relationship created by the recording rule rather than by
behaviour. The cap qualifies under the strictest reading: the observed markup *is* $\min(m^*,c)$ by
definition, so the interaction between "markup" and "cap binding" is not something the market does, it is
something the record does. That is why its sign is class C and needs no data — a virtue, not a defect.

The complication is that the same ceiling also has a genuine behavioural channel. `01-a` §3 names four
evasion routes (side payment, wallet handoff, bundling, flight to unregulated channels) and the UK's own
cost-benefit model assumes a 20% displacement of tout volume to unregulated channels — an official
assumption, not a measurement. And `01-a` §3(2) records the corollary from He & Lin (2026): a stringent cap
can push high-price sellers out, reduce seller-side competition, and **raise** the average transaction
price. So the observation "a tighter cap produces lower recorded markups" is an artefact of truncation
while "a tighter cap produces lower prices" is a behaviour claim with a model result pointing the other
way. The engine must say the first and never the second. **[QUOTED, class C for the truncation, C for the
model result, D for the evasion magnitude]**

The mechanism diagram, with the artefact edge marked so it is not mistaken for behaviour:

```
                 organiser chooses c  ──┐
                                        │  (policy)
   latent agreement m*  ────────────────┴──►  min(m*, c) = recorded m
                                                    │
                                                    │  [ARTEFACT: no behaviour on this edge]
                                                    ▼
                                        observed mean, median, upper quantile
                                                    │  (biased down by s·E[m*−c | m*≥c])
                                                    ▼
                                        the resale reference handed to the optimiser

   separate, behavioural, magnitude unobservable:
        c  ──►  seller exit at the top / off-rail settlement / suppressed listing
           ──►  recorded markup is a LOWER BOUND on consideration, worst where demand is strongest
```

#### I2 — why the verdict is split

The *mechanism* is causal and both halves are measured: decaying option value on the seller side is
Sweeting's result, rising arrival on the buyer side is arithmetic on Leslie & Sorensen's reported shares.
The *implementation* is predictive because the conditioning variable is manufactured. A single slope
conditioned on nothing is the failure case; a slope conditioned on a stratum that the organiser's own price
determines is contaminated by the policy (I9). Between those two, the engine's only defensible move is to
report the slope **within a stratum** and to say that the stratum is policy-determined.

```
   seller's remaining selling opportunities ──► option value of holding ──► ask ──┐
                                                                                 ├──► observed path
   buyer arrivals per day toward the door ───────────────► bid ────────────────────┘
                                                                                  
   and the stratifier the engine actually has:
   organiser's p0 ──► sell-through ──► "popularity" stratum ──► which slope is applied
                 └──► cap in money p0(1+c) ──► cap-hit share ──┘
```

#### I9 — why this is the loop that survives, and why it is a simultaneity at D1

The price-to-record loop is not a dynamic system at the level of one event: $p_0$ is chosen once, before
on-sale, and the record accumulates afterwards. It is a genuine dynamic system at the level of the
*platform*, with a one-event lag: the price recommended for event $n$ shapes the training data available
for event $n+1$. Three consequences, and they are the reason this row is in the registry rather than in a
footnote.

1. **Scale invariance makes the contamination permanent.** Because the cap is bps over face, raising $p_0$
   raises the ceiling in proportion, so the *share* of sales at the ceiling is invariant to the level of
   $p_0$ (`02-b` §3.5(2)). The engine cannot price its way out of a censored sample.
2. **The binding window is an output of the decision.** Raising $p_0$ raises the ceiling in money and
   shortens the window over which the cap binds, given the latent path. So the engine cannot report "this
   event is capped 40% of the window" as a fact; it must report the binding duration as a function of the
   candidate price (`02-a` §7.2). That is IF-03.
3. **The fix is a logged action, not a model.** If the platform ever records what the engine recommended
   and what was accepted, this becomes a propensity-score problem with a clean fix. It does not today
   (`03-b` §5 P3; `02-ai-ml-decision` §4(e): no logged actions or propensities).

```
   recommendation p0 ──► cap in money p0(1+c) ──► truncation of the record ──► training data
          ▲                                                                        │
          └──────────────────── one event later: the fitted model ────────────────┘
```

### 2.2 Where the causal question cannot be answered at all

Three honest limitations, stated so that no later pass mistakes a decision for a finding.

- **The level of value is not identified**, so no interaction can be estimated in units of value. Only
  ratios, and only up to an affine indeterminacy, because the schema contains no exogenous price anchor
  (`01-b` T1, §4.1). Every verdict above is therefore about *shape and sign*, not about magnitude.
- **Every number is conditional on the primary price actually charged.** The population of tickets in the
  ledger is the population that bought at $p_0$; varying $p_0$ changes who is in the ledger (`02-c` §2.3,
  N4). This is not a threat that appears in the table because it is not an association being estimated —
  it is a bound on what any of the estimates *mean*.
- **No interaction can be estimated on the buy side.** There are no bids, offers, views or searches
  anywhere in the contract (`01-b` §6(3); `03-b` D03). Every demand statement in this programme rests on
  assumption.

---

## 3. Feedback loops

The programme names seven. The question it asks is whether the market should be modelled as a dynamic
feedback system. The answer for *this product* is no, and the reason is not that the loops are absent from
the world — it is that four of the seven have no state variable in the contract at all, one is a static
constraint, one is a simultaneity, and exactly one is a dynamic system the product can act inside.

**The product's decision structure, because it decides everything below.** The organisation sets one
primary price per tier at a point in time before on-sale (D1 in `03-b` §2.1), and reports estimates inside
the trading window (D2). There is no price-mutation endpoint (`02-d` §1.1: nine endpoints, seven reads, two
wallet-verification POSTs), so no repricing action exists. A dynamic policy is therefore not a modelling
choice; it is a schema and product change.

| # | Loop (programme's wording) | Is it a dynamic system, or one decision with a lagged observation? | Survives a single-decision product? |
|---|---|---|---|
| L1 | Primary prices influence resale supply | **Neither.** It is a static constraint: the feasible band $[p_0,p_0(1+c)]$ translates with $p_0$, so raising the primary price raises the ceiling in proportion and leaves the reseller's permitted markup unchanged (`02-d` §2.5(a,b)) | **Survives, as I9.** Not as a loop: as the scale invariance that makes the truncation permanent and the binding window a function of the candidate price |
| L2 | Resale prices influence primary willingness to pay | **A simultaneity**, not a dynamic system. The buyer's outside option — wait and buy on resale — has a price no higher than $p_0(1+c)$, so it is a function of $p_0$ rather than an independent price (`02-d` §2.5(c)). There is a fixed point: $p_0\to$ expected resale value $\to$ willingness to pay $\to$ demand at $p_0$ | **Survives.** It is the whole product. It is solved once per event, not iterated, and it is why the substitution between primary and resale is already inside the residual elasticity |
| L3 | Primary inventory releases alter secondary-market pricing | **Dynamic, and unobservable.** `Event.status` transitions are untimestamped, so on-sale start, sell-out and hold-back-release times are all unknown (`00-data-situation.md` §4). There is no release event in the record at all | **Collapses.** No state variable, no event, no action. Out of scope at any horizon |
| L4 | Seller price reductions influence competing sellers | **Dynamic, and unobservable.** There are no asks anywhere in the record, no listing duration, no depth history (`01-b` §5(2): the asking-versus-realised gap does not shrink, it vanishes). This is the loop the literature is *about* — Sweeting's within-seller path and the relisting structure — and it is exactly what this schema lacks | **Collapses.** Cannot be computed, so it cannot be a feature. Recorded so that nobody re-proposes it |
| L5 | Market visibility influences buyer expectations | **Dynamic, and unobservable.** No views, searches, queue positions or registration volume; and the mechanism is upstream of the demand the platform already measures | **Collapses.** Also redundant by §4.7: a forecast of a forecast |
| L6 | Demand changes influence seller listing decisions | **Dynamic, and unobservable.** The listing decision is the object the four-field panel would capture (`F` D3) and it does not exist | **Collapses today**, and would be the first loop to reopen the day the panel lands — because Specification B's ask is precisely a seller's decision responding to demand |
| L7 | **Pricing policies alter the data subsequently observed** | **A genuine dynamic system**, with a one-event lag | **Survives**, and it is the only one that does. It is I9, it has no in-sample fix, and it is the reason deployment ≠ training |

### 3.1 What follows for the architecture

Three instructions, in order of how much they save.

1. **Do not build a dynamic model.** No state-space layer, no dynamic program, no Bellman recursion over a
   state the contract cannot observe. `02-d` §4.4 already says the engine has no state variable to
   condition a repricing on, so the value of a dynamic policy is not measurable here and must not be
   claimed. A dynamic model with four of its seven loops collapsing and a fifth missing its state would be
   a model of the modeller's imagination.
2. **Do carry the two objects that are genuinely time-shaped.** The within-horizon path (`02-a` §8) and the
   cap-binding window as a function of $p_0$ (IF-03). Both are cheap — a two-parameter closed form and one
   root-find per candidate price — and both change the recommendation.
3. **Do instrument the one loop that survives.** Log every recommendation and every acceptance from the
   first event, even though nothing consumes it yet. It is the cheapest future-proofing available and it
   converts I9 from an unfixable contamination into a propensity score (`03-b` §5 P3).

**And the sentence the deliverable must not contain.** "We model the market as a dynamic feedback system."
It is not true of this product, and the four loops that would justify it are the four the schema cannot
observe. The true sentence is narrower and stronger: *we model one decision, with a censored price record,
two opposing time forces, and a policy that feeds back into the record one event later.*

---

## 4. The interaction features

Twelve definitions, written to be implemented without a question. Every one defers its clock to
`03-b` §3 (the decision-time table) and its variable name to `records/C-variable-registry.md` where one
exists. Notation: $e$ event, $g$ tier, $i$ ticket, $t$ the cut instant, $\tau$ days from $t$ to
`startsAt`, $c$ = `Event.resalePriceCapBps`, $f_g$ = tier face in lamports, cut means "rows with
`slot` < cut's slot, or `occurredAt` < cut when `slot` is null" — the clock rule from `02-c` §3.1 and
`03-b` §4 T1, and it is **slot**, not `occurredAt`, that is monotone.

Each block gives: definition; computed from; when knowable; expected sign; failure mode; buildable today
from the wire contract.

---

**IF-01 · `tau_x_tight`** (the I2 carrier)

- **Definition.** A stratum key, not a number:
  `tau_bucket(τ)` ∈ {`T60` = τ>60, `T30` = 30<τ≤60, `T14` = 14<τ≤30, `T7` = 7<τ≤14, `T3` = 3<τ≤7,
  `T0` = 0≤τ≤3}; `tight_class` ∈ {`SOLD_OUT` (status sold out, or issued/total ≥ 0.999),
  `HIGH` (0.9 ≤ ratio < 0.999), `MID` (0.5 ≤ ratio < 0.9), `LOW` (<0.5), `UNKNOWN`}. The feature is the
  pair `(tau_bucket, tight_class)` and its one-hot expansion; the path model is fitted **per stratum**,
  or with `tight_class` as a main effect plus the interaction, and never as a single slope.
- **Computed from.** `Event.startsAt` for τ; `TicketTier.issuedCount` / `TicketTier.totalSupply` **as
  logged at the cut**; `Event.status` read at the cut.
- **Knowable at.** D1, if and only if the ratio was polled and logged at `T1(e)`. The stored field is a
  snapshot as of extraction, so using an extraction-time value at D1 is the look-ahead trap `03-b` A15
  names. At D2 the same rule applies at each `t`.
- **Expected sign.** The path slope is **negative** in `LOW` and `MID`, **≈0 or positive** in `SOLD_OUT`
  and `HIGH` (I2). A negative slope in `SOLD_OUT` is evidence against the arrival-force reading, not
  against the model.
- **Failure mode.** (a) If `issuedCount` means *minted* rather than *sold*, the stratifier is noise — that
  is an open operator question (`02-e` §2.4, UNVALIDATED) and it must be printed as a condition until
  answered. (b) `UNKNOWN` is not a licence to pool: `UNKNOWN` gets its own stratum and its own interval,
  because the missingness is not random (`03-b` §4 T3 on survivorship). (c) The stratifier is
  policy-determined — `tight_class` is a function of the organiser's own $p_0$ — so a cross-event
  comparison must be within a $p_0$ band (`03-b` §5 P3).
- **Buildable today.** **Structurally yes, operationally no**: the fields exist in the contract, but the
  *vintage* does not, so it is buildable only once the backend polls and logs the ratio at decision time.
  That is a change to the platform, not to the model.

---

**IF-02 · `cap_mass` $s(t)$** (the I5 carrier, and `02-a` §6.2's "best feature in the dataset")

- **Definition.** $s(t)=\dfrac{\lvert\{r:\ r.\text{kind}{=}\text{sale},\ \lvert r.\text{markupBps}-c\rvert\le \text{TOL},\ r.\text{slot}<\text{cut}\}\rvert}{\lvert\{r:\ r.\text{kind}{=}\text{sale},\ r.\text{slot}<\text{cut}\}\rvert}$,
  with `TOL = 1` bps as a **named constant**, and `null` returned when `c` is null or when the
  denominator is below `N_MIN = 5`. Also return the pair $(k,n)$ so the UI can show the counts, and
  `cap_mass_by_tau` = the same ratio within each `tau_bucket`.
- **Computed from.** `LedgerEntry` rows of kind `sale` via `getResaleHistory(ticketId).entries` joined to
  the ticket's tier face, plus `Event.resalePriceCapBps`. **Not** from `ResaleStats.avgMarkupBps` or
  `EventAnalytics.markupDistribution`, whose as-of the contract does not state (`03-b` C14, C15).
- **Knowable at.** D2, and at D1 only if a cut-time pass was run and logged. Each sale makes it knowable.
- **Expected sign.** **+ means excess demand at the ceiling.** It is a rationing statistic and it is never
  a value statistic. Its *trajectory* over $\tau$ is the sign test: if the latent path is falling, the mass
  is present at large τ and shrinks toward the event; a rising path predicts the reverse (`02-a` §6.1 C3).
- **Failure mode.** (a) $s=0$ is **not** evidence the cap does not bind — the ceiling can bind hard enough,
  or leak badly enough, that no row lands on it (`02-b` §1.2). The correct tri-state is
  `capped_and_binding (s>0)` / `capped_no_mass (s=0)` / `uncapped (c null)`, per `02-b` §3.1. (b) `TOL` is
  load-bearing: without a tolerance a recorded markup of $c-1$ reads as not-at-cap, and with too wide a
  tolerance interior rows are absorbed. Report the value. (c) $s$ is a **lower** bound on
  $\Pr(m^*\ge c)$, because an exact-ceiling agreement and a rationed one are indistinguishable on the row
  (`02-b` §2). (d) $s$ is a function of $p_0$ (I9), so it cannot be compared across events at different
  $p_0$ without conditioning.
- **Buildable today.** **Yes.** Every input is in `LedgerEntry` and `Event`. This is the first thing to
  compute on real rows.

---

**IF-03 · `cap_window(p0)` $W(p_0)$** (the I9 carrier)

- **Definition.** Let $\hat y_g(d)$ be the fitted log-money path for tier $g$ at $d$ days before the event
  (`02-a` §8.1's target, anchored at the tier's most recent transaction in money). For a candidate
  primary price $p_0$ and cap $c$,
  $W(p_0)=\big\lvert\{d\in[0,H]:\ \hat y_g(d)\ \ge\ \log p_0+\log(1+c)\}\big\rvert$, in days, where $H$ is
  the on-sale horizon. Report $W$ as a fraction of $H$ as well, and report it under both normalisations
  $\omega=0$ and $\omega=1$ (the bracket from `02-a` §4.3) as a pair, not as a point.
- **Computed from.** The fitted path for the tier, `Event.resalePriceCapBps`, and the candidate $p_0$.
  One root-find per candidate price against the fitted path.
- **Knowable at.** D1 — it is a function of the decision, so it is evaluated, not observed.
- **Expected sign.** $\partial W/\partial p_0<0$: raising the primary price raises the ceiling in money and
  shortens the window over which it binds. $\partial s/\partial p_0\approx0$ in share terms (scale
  invariance) — the two statements are consistent and both matter.
- **Failure mode.** (a) It inherits the level indeterminacy: the path is identified in curvature, not in
  level, so $W$ must be reported as a bracket over $\omega$ and never as a single number. (b) If the path
  was estimated in markup space, $W$ is meaningless — `02-a` §7.2's exact prohibition. (c) $\hat y_g$ is
  extrapolated beyond the observed τ support at the boundary, where the estimate is weakest (`02-c`
  §3.9(7)).
- **Buildable today.** **Yes**, conditional on the path model existing. The path model is `02-a` §8, which
  is specified and not yet built.

---

**IF-04 · `cap_floor(g,t)`**

- **Definition.** `floor_g(t) = f_g · exp(q)` where $q$ is the **25th percentile** of
  $\{\log(p_i/f_g)\}$ over sale rows in tier $g$ with `slot < cut` and `markupBps < c`; the **median** is
  returned only when $s(t)<0.5$; nothing in the upper half is ever returned. Report $(q,n,s)$ with it.
- **Computed from.** The same rows as IF-02.
- **Knowable at.** D2 (D1 only if logged).
- **Expected sign.** A floor, so it rises with observed markups and it is never an estimate of the mean.
- **Failure mode.** (a) Reporting the median when $s\ge0.5$ is degenerate — the median *is* the cap
  (`02-a` §6.1 C2). (b) A low quantile is the same quantile of the latent distribution only when the cap
  mass sits above it (Powell 1986, as `02-a` §6.2 applies it); when $s$ is large enough that the 25th
  percentile is at the ceiling, the floor is empty and the engine must say so rather than print a number.
  (c) Pooling across tiers with different faces in markup space is invalid (`02-a` §6.2, last row).
- **Buildable today.** **Yes.**

---

**IF-05 · `supply_remaining_x_ladder`** (the I1/I3 carrier)

- **Definition.** `rem_g = (totalSupply_g − issuedCount_g)/totalSupply_g` at the cut, floored at 0;
  `ladder_g = log f_g − mean_k(log f_k)` over the event's tiers. The feature is the pair, used as a
  stratum or as `rem_g × ladder_g`. Signed version:
  `scarcity_g = (1 − rem_g) × 1{ladder_g > 0}`, a **state** variable.
- **Computed from.** `TicketTier.totalSupply`, `TicketTier.issuedCount`, `TicketTier.faceValueLamports`.
- **Knowable at.** D1 if logged at `T1(e)`; otherwise snapshot-only.
- **Expected sign.** Resale premium highest at low `rem_g` and high `ladder_g` (I3, one-sided).
- **Failure mode.** (a) No clock: `totalSupply` is ticketed supply, not venue capacity, and there is no
  sell-out time, so `rem_g` cannot be differenced into a velocity (`02-e` §2.1). (b) `issuedCount` may mean
  minted. (c) It is an **outcome** of $p_0$: a low price sells through, so `rem` low is partly the
  organiser's own choice. It is admissible as state and inadmissible as a free regressor (`03-b` §5 P3).
- **Buildable today.** **Yes** at D1 if the backend logs it at decision time; the fields exist.

---

**IF-06 · `seller_concentration`** $H_g$, `top1_g` (the I4 carrier)

- **Definition.** Over sale rows in $(e,g)$ with `slot < cut`, let $n_w$ = the count of rows whose
  `fromWallet` is $w$ and $n=\sum_w n_w$. Then `top1_g = max_w n_w/n` and
  `H_g = (n·Σ_w (n_w/n)² − 1)/(n−1)` (the finite-sample-corrected Herfindahl, returned as `null` for
  $n<10$). Return $n$ and the number of distinct wallets.
- **Computed from.** `LedgerEntry.fromWallet` on kind `sale`; needs the full `entries` array truncated at
  cut.
- **Knowable at.** D2 (each sale).
- **Expected sign.** − on the price level, + on the sale hazard, as concentration rises: professionals set
  lower prices and clear faster (class A in MLB, Sweeting 2012; class D for the transfer).
- **Failure mode.** (a) **A wallet is not a person.** One person with many wallets looks diffuse, so $H$ is
  a **lower bound** on true concentration — Bitcoin-style clustering does not transfer to an account-based
  chain (`01-b` §4.6(b)). (b) `fromWallet` is null on `issue` rows, so the first holder is invisible.
  (c) The cap changes who sells at all (I12), so $H$ is endogenous to policy. (d) Self-dealing round trips
  inflate $n_w$ for one wallet (`02-c` §2.2).
- **Buildable today.** **Yes**, with the wallet-versus-person caveat printed wherever it is used.

---

**IF-07 · `momentum_lower_quantile`**

- **Definition.** `mom_g(t) = q25{log(p/f_g) : sales in (t−7d, t]} − q25{log(p/f_g) : sales in
  (t−14d, t−7d]}`, in log units, over tier $g$; `null` unless **both** windows have at least 5 sales; and
  `null` if the 25th percentile in either window is at the cap (then the quantile is the boundary, not the
  market).
- **Computed from.** The same truncated rows.
- **Knowable at.** D2.
- **Expected sign.** Negative in the default regime (I2's seller side); the sign is the thing under test,
  so the feature must be reported, not assumed.
- **Failure mode.** (a) Success branch only: this is the intersection of ask and bid, not the ask path
  (`02-a` §4.4), so it is not comparable to any published relisting decline. (b) The window boundaries must
  be `(t−7d, t]` and `(t−14d, t−7d]` — a window ending at extraction is the leak `03-b` C08 names.
  (c) Below the sample floor, returning 0 instead of `null` manufactures a flat path.
- **Buildable today.** **Yes**, when the counts suffice; otherwise `null`.

---

**IF-08 · `coldstart_weight`** $w_e$ (the I7 replacement)

- **Definition.** $E_e=\sum_i(\text{cut}-\text{issuedAt}_i)$ in ticket-days over the event's issued tickets;
  `own_mean_e` = the event's own mean $\log(p/f)$ over sale rows, `null` at zero sales; `pooled_mean` from
  the event panel; $w_e = E_e/(E_e+b_0)$ with $b_0$ a **declared** tuning constant, not fitted. The
  forecast is $\hat y_e = w_e\cdot\text{own\_mean}_e + (1-w_e)\cdot\text{pooled\_mean}$ — and at zero
  sales the gamma–Poisson form replaces the pooled mean with the **exposure-shrunk** intensity
  $a/(b+E_e)$, because the zero is evidence, not missing data (`02-c` §6.1).
- **Computed from.** `Ticket.issuedAt` and `LedgerEntry` sale rows; the event panel for `pooled_mean`.
- **Knowable at.** D1.
- **Expected sign.** Weight on own data **increases** with $E_e$; and the exposure update moves the
  predicted intensity **down**, not to the population mean. Those are two different statements and both
  are required.
- **Failure mode.** (a) Zero-sale events must be **inside** the between-event variance estimate, or
  $\hat\sigma^2$ is biased down and cold-start intervals come out too narrow (`02-c` §6.2; `02-e` §4.4).
  (b) $E_e$ does not distinguish "not offered" from "offered and unsold" — that split is N2 and cold start
  does not fix it. (c) Exchangeability given covariates is an assumption, not a result (`02-c` §6.2).
- **Buildable today.** **Yes** for $E_e$; `pooled_mean` requires the event panel to exist, which it does
  not yet.

---

**IF-09 · `coldstart_band`** (the deliverable of `02-e`, carried here because it is the interaction with τ)

- **Definition.** `band = exp(ȳ_e ± z·sqrt(τ_declared² + V(τ_declared)))` with
  $V(\tau)=1/\sum_j(s_j^2+\tau^2)^{-1}$, reported as a **multiplier on the point estimate** and then, if
  an absolute reading is wanted, as markup over face **centred at the fitted mean** — per `02-e`
  CORRECTION 1, whose withdrawn label ("as markup around face") is not to be reintroduced. Truncate the
  upper end at the ceiling $f_g(1+c)$ in money.
- **Computed from.** The event panel's mean and dispersion; the declared τ grid.
- **Knowable at.** D1.
- **Expected sign.** n/a — an interval.
- **Failure mode.** (a) The label. A band printed as "−49% to +95% around face" reverses the sign of the
  downside, which is the defect `02-e` CORRECTION 1 corrects. (b) The band must never be narrower than the
  declared-τ row it is built from, and the width is a **floor** because $V(\tau)>0$. (c) It must switch to
  the empirical distribution once the event count reaches the `02-e` §6.4 floor; leaving a declared τ in
  place after the data can estimate it is a false label in the other direction.
- **Buildable today.** **Yes** — closed form plus one bisection for the χ² quantiles.

---

**IF-10 · `hop_velocity(g,t)`** (the I8 carrier)

- **Definition.** For tier $g$ at cut: `hops_per_100td_g = 100 · |{priced and unpriced hops, slot < cut}|
  / Σ_i (cut − issuedAt_i)` over the tier's tickets; and `median_hold_h_g` = the median, over hop intervals
  closed before the cut, of the gap between consecutive hops on the same ticket, in hours, computed from
  `slot` ordering with `occurredAt` only as a display value.
- **Computed from.** All `LedgerEntry` rows for the tier's tickets, truncated at cut.
- **Knowable at.** D2.
- **Expected sign.** + hops and − holding in top tiers on tight events (I8, class D).
- **Failure mode.** (a) **Selection:** only tickets that transacted have hops, so this is a churn rate
  among traders, not among holders. (b) Key handoff makes a transfer invisible, so both quantities are
  biased **down** by an unmeasured amount (`01-a` §6). (c) `slot` is nullable; a null-slot row must be
  dropped and counted, never assumed to sort. (d) The window must clip at `issuedAt`, or the first gap is
  the age of the ticket rather than a holding period.
- **Buildable today.** **Yes**, with the biases printed.

---

**IF-11 · `gate_stratum`** (the I10 carrier)

- **Definition.** A stratum key `(requiresVerifiedWallet, resaleEnabled, cap_present)` — three booleans,
  eight cells, `cap_present` meaning $c\neq\text{null}$. **Never a regressor.** Every estimate is reported
  per cell with its counts, or not at all.
- **Computed from.** `Event` fields only.
- **Knowable at.** D1 (static).
- **Expected sign.** **None.** The pooled number estimates neither the gated nor the ungated regime
  (`03-b` §5 P2).
- **Failure mode.** (a) Within an event the flag does not vary, so its effect cannot be identified from one
  event's history. (b) If it is a platform-wide constant across the observation window it is perfectly
  collinear with calendar time and its effect is not identified even in principle — that is `F` Q5 and it
  is unanswered. (c) Reporting a cross-cell difference without saying which cells had sales is the
  catalogue error of §4.7.
- **Buildable today.** **Yes**, as a partition.

---

**IF-12 · `wedge_ratio`** (the I11 carrier; a configuration object, not a feature)

- **Definition.** $c^{**}=b+(1+\beta)\,(f-a-u)/(1-\phi)$ per `02-d` (WEDGE), where $b$ buyer per-unit fee,
  $\beta$ buyer ad valorem, $f$ organiser per-unit fee, $\phi$ organiser ad valorem, $a$ ancillary margin,
  $u$ empty-seat cost. Report `c**/f_g` — the wedge as a share of face — and the recommended price
  $p^*=c^{**}\eta/(\eta-1)$ only when both $c^{**}>0$ and $\eta$ are supplied; otherwise report the
  boundary rule.
- **Computed from.** Configuration. Nothing in the contract carries any of these (`00-data-situation.md`
  Gap 4).
- **Knowable at.** D1, as an input.
- **Expected sign.** $\partial p^*/\partial f>0$; $\partial p^*/\partial\phi=0$; $\partial p^*/\partial
  \eta<0$.
- **Failure mode.** **The missing fee must raise, not default to zero.** A silent zero makes the wedge
  negative whenever $a+u>0$ and the recommendation then reads "lower the price" for a fee-model reason.
  Also: $c^{**}$ is not a price; it is a wedge, and the ratio $c^{**}/f_g$ is what has units of "share of
  face" in `02-d` §5.2's table.
- **Buildable today.** **No** — configuration only, and the two field values that would measure it are the
  settlement request (E10).

---

### 4.1 What a build agent does with this table, in order

1. IF-02, IF-04, IF-06, IF-07, IF-10, IF-11 — ledger- or event-derived, truncatable, no new fields. These
   run on real rows the day the platform has any.
2. IF-01, IF-05 — event and tier fields, blocked only on **logging the vintage**, which is a backend change
   and not a modelling one.
3. IF-03, IF-08, IF-09 — require the path model and the event panel to exist (`02-a` §8, `02-e` §4).
4. IF-12 — blocked on the settlement field, and must refuse to run without it rather than assume zero.

The dependency is deliberately shallow: nothing in group 1 needs anything in group 2 to be correct, and
each feature returns `null` rather than a number when its floor is not met. That is the only discipline
that keeps a sparse event from producing a confident-looking coefficient.

---

## 5. The experiments, ordered

Two things set the order and they are not the same thing: **what can start now** and **what changes if it
comes back**. The E-numbers are stable labels, not ranks. Read down the table as a work order and read
§5.2 for the one that matters most — E3 sits fourth because it is the only experiment on the list that
needs money and a pricing decision rather than data, and it is first in consequence.

| # | Experiment | Data that would test it | The test | If it confirms | If it refutes |
|---|---|---|---|---|---|
| **E1** | The deadline mechanism, via the composite rate and the cap mass | Present today: ticket population, `issue`/`sale`/`redeem` rows, `startsAt`, tier faces, `c`. No new fields | (i) sales per ticket-day at risk by `tau_bucket` (`02-c` Specification A); (ii) `cap_mass_by_tau` (IF-02) as the sign test; (iii) the two together: rising rate **with** falling price, or a mass that shrinks toward the door | The deadline mechanism holds, the deadline-convex path form is admissible, and a positive slope in `SOLD_OUT` strata is the arrival force showing through | A **falling** rate refutes the deadline story outright (`02-a` §5.4); a mass that **grows** toward the door refutes the falling-path prior and the last-week forecast must be the martingale |
| **E2** | The listing panel, and the ask-conditional hazard (I13) | The four fields per listing episode: `{listPriceLamports, listedAt, delistedAt, delistReason ∈ {sold, withdrawn, expired, cap_blocked}}`, carried with the cap value at the policy version | `02-c` Specification B: fit $\lambda(t\mid p,x)$ with the cap stratum separate; publish the within-$(e,g,\tau)$ ask dispersion and the $R^2$ of $z$ on the dummies **before** any $\hat\gamma$ | "The probability it transacts at a given price" becomes a supported sentence, and the choke price $p^*$ becomes estimable | If ask dispersion within cells is zero, the fields are four fields of nothing and the price response stays unidentifiable (`02-c` §4.4) |
| **E5** | The off-rail leak, $q(cap,\text{event})$ | Present, partly: the ledger's dark tickets — tickets with no transfer rows that redeem from a wallet $\ne$ `issuedToWallet` | Count them; regress the dark rate on $c$ and on the cap-hit share, with `p0` bands | Every recorded markup is scaled by a known-downward factor and the floor can be corrected | The leak is negligible on this platform, the recorded markup is close to the consideration, and the floor is nearly the value |
| **E3** | The primary own-price elasticity, and its interaction with remaining inventory (I6) | A randomised face value across otherwise comparable events, or a randomised ratio of two tiers' faces within an event (`02-d` §3.6) | Elasticity of $\ln(\text{sell-through})$ on $\ln(\text{price})$ with event and tier fixed effects; the within-event arm identifies the cross-tier substitution elasticity | **The deliverable's headline changes from a boundary to an interior optimum**, and the cap's demand effect is identified as a free by-product because randomising $p_0$ randomises the ceiling | The boundary rule stands, and the engine keeps reporting a bound with a sensitivity map rather than a price |
| **E4** | The location of the latent upper tail | One cap-free event (or an event whose cap sits far above any observed markup) | `02-b` §3.3: learn the tail on the uncapped event, test whether it transfers | The floor of IF-04 becomes a point estimate and `02-b` §2's B2 curve becomes a curve rather than one point | The floor stays a floor, and the transfer of any uncapped estimate is refused |
| **E7** | Whether the slope is identifiable or only bracketed | Present, with enough events live at once | The period-effect diagnostic: correlation of residuals across events live in the same calendar week (`02-a` §4.3) | Near zero ⇒ the bracket collapses, the point estimate is safe, and the APC concern is retired for this data | Strongly correlated ⇒ the bracket is wide and no per-day slope may be printed |
| **E6** | Whether a wallet is a seller worth modelling | Present: `fromWallet` history across events, truncated at each cut | Repeat-seller fixed effects on the wallets that link; test whether concentration (IF-06) predicts hop speed (IF-10) and the level | A professional-seller feature earns its place and I4/I8 move from D to B | Wallet noise is dominant and concentration stays a lower bound with no predictive value |
| **E8** | Cold-start reliability by exposure | The first events up to the `02-e` §6.4 floor, including the ones with zero sales | Prequential: does the exposure-shrunk intensity (IF-08) beat the population mean on the events that had no sales? Report per fold with its spread | The gamma–Poisson update is worth its two parameters and zero-sale events are usable evidence | The pooled mean is as good and the update is complexity without return — ship the simpler one |
| **E9** | The gate's sign (I10) | A platform-level change, or two events differing only in `requiresVerifiedWallet` | Stratum comparison with counts; if the flag is platform-wide constant, report it as unidentifiable and stop | The gate becomes a priced feature rather than a stratum | The flag stays a partition forever and the engine says the sign is unknown, which is the current state |
| **E10** | The fee wedge, measured | `netToOrganizerLamports` and `buyerTotalLamports` on every settled primary sale (`02-d` §2.6, ranks 1 and 2) | Recover $c^{**}(p)$ as a function rather than a constant; check whether the all-in rule of 16 CFR 464 is already applied | The largest unquantified term in the report becomes measured and the recommended price stops depending on an assumption | If only a percentage fee is recorded, nothing changes for the price — the per-unit component is the one that matters |

### 5.1 The three that can start before any new data

E1, E5 and E7 all run on the fields the contract already has, and E1 is the only one that can overturn a
shipped model. If nothing else is done this week, E1's three pieces (the composite rate by `tau_bucket`,
the cap mass by `tau_bucket`, and the pair reported together) are the cheapest way to find out whether the
deadline story holds on this platform at all. And E1 is falsifiable in the strong sense: a *falling*
composite rate refutes the mechanism outright.

### 5.2 The one that changes the engine most

**E3.** Confirming that the primary demand elasticity falls (in absolute value) as remaining inventory
falls changes the shape of the answer, not its precision: the engine reports an interior optimum with a
demand curve rather than a boundary with a sensitivity map. That is the difference between a pricing
engine and a price floor, and it is the only experiment in the list that makes that difference. E2 is a
close second and is cheaper, but it changes the *resale* product while leaving the primary price where
`01-b`'s T5 puts it, because the population is selected on issuance (`02-c` §2.3, N4) and no amount of
secondary data repairs that.

---

## 6. Limits, and where this disagrees with prior records

### 6.1 What this file does not establish

- **No magnitude for any interaction.** Every row is a sign, a mechanism and a class. There is no dataset
  on this machine, so any number would be invented, which §4.6 forbids. Where a number appears it is
  quoted from a published market and labelled with that market.
- **No new identification result.** The identifiability ledger in `01-b` §3 is the authority on what can
  be estimated, and this file does not extend it. It records which interactions the ledger *permits*,
  which is a smaller set than the brief's list.
- **No claim that the required list is complete.** Thirteen interactions is a bounded answer to an
  unbounded question (§4.1). The five I added were added because each one changes a decision, a claim or
  the form of an estimator; a scan that produced twenty more with no such consequence would have been
  padding, and I have not done it.
- **No dynamic model.** Deliberately, per §3.1.

### 6.2 Disagreements and sharpenings, recorded not resolved

1. **`01-d` §5 is right about which variables are causal and understates one thing.** It calls V2
   sell-through and V5 custody-trail features "the most dangerous case" because they are outcomes of the
   pricing decision. That is correct, and `03-b` §5 P3 makes it structural: the deployment distribution
   differs from the training distribution *by construction*. What `01-d` does not say is that the same
   argument applies to the **cap-hit share**, which `02-a` §6.2 calls "the best feature in the dataset".
   Both are true: it is the best signal of excess demand available and it is a function of $p_0$. IF-02
   carries both statements and forbids the cross-event comparison without a $p_0$ band.
2. **`02-b` §1.4 is right to correct "left truncation" and I adopt the correction.** Nothing above calls
   the removed tail "left"; the phrase in `01-a` §3 and `00-data-situation.md` Gap 2 is read as shorthand
   for the lower end of the *price* axis relative to what the market would bear, which is what the
   substantive claim says.
3. **`01-b` CORRECTION 2 and `02-d` §2.5 are consistent, and the consistency is easy to lose.** The cap
   supplies no *within-event* identifying variation (withdrawn), and the cap is nevertheless a parameter
   of the DGP that moves with the decision (kept). §1.1 and §2.1 of this file keep them apart by naming
   the variable each is about.
4. **`02-e` CORRECTION 1 is adopted, and IF-09 enforces it.** The cold-start band is a multiplier on the
   point estimate; the "around face" label is not to be reintroduced.
5. **I disagree with the framing of "additional primary inventory conditional on resale market scarcity"**
   in the brief's example list, and I have not registered it. On this platform the organiser controls
   supply and there is no inventory-release event in the record at all (L3 in §3); so the interaction has
   no state variable. It is registered implicitly as part of I3/I6 rather than as a row, because a row
   with no clock is a row that will be implemented wrongly.
6. **`03-b` §3.1 A14's D1 verdict is stricter than needed in one respect and I follow it anyway.** The
   `sold_out` state is a future fact at D1, so `tight_class = SOLD_OUT` in IF-01 is admissible at D1 only
   for an event that has *already* sold out before `T1(e)` — which is rare but real for a second-tier
   event priced after the first tier cleared. I keep `03-b`'s rule (drop it at D1) and note the exception
   rather than building on it.

---

## Sources

Read in full for this file: every record named in the header. Nothing was read from outside the repository
for this pass except `../ticketing-frontend/lib/types.ts` (field-by-field, for the buildability
column) — so the literature below is cited **as recorded in `01-a`, `01-b`, `02-a`, `02-b`, `02-c`, `02-d`,
`02-e`**, with the market and the conditioning stated on each, and no new bibliographic claim is made.

**Ticket-market empirical evidence (class A), as used above**
- Sweeting, A. (2012). Dynamic pricing behavior in perishable goods markets: evidence from secondary
  markets for Major League Baseball tickets. *JPE* 120(6):1133–1172. doi:10.1086/669254 — the declining
  path as decaying option value; seller-type differences; relisting declines of 13/18/40% of face.
- Leslie, P. & Sorensen, A. (2014). Resale and rent-seeking: an application to ticket markets.
  *RES* 81(1):266–300. doi:10.1093/restud/rdt033 — 41% mean markup, 26% below face, 25% above +67%; the
  near-flat path with "a modest uptick in the last week"; the 25%/50% timing shares used for the arrival
  arithmetic in `02-a` §5.3.
- Budish, E. & Bhave, A. (2023). *AEJ:Micro* 15(1):142–170. doi:10.1257/mic.20180230 — auctions removed
  the arbitrage that a posted price leaves; the class A support for I3's direction.
- He, D. & Lin, S. (2026). Price caps by matching platforms: the case of ticket resales.
  *Marketing Science* 45(3):515–533. doi:10.1287/mksc.2023.0623 — the model result behind I12 and the
  "tight cap can raise the average transaction price" corollary. Cited as 2026 per `01-a` CORRECTION 3.
- Courty, P. & Pagliero, M. (2012). *REStat* 94(1):359–369 — multi-tier pricing worth ≈5%, cited only where
  the tier ladder appears as a covariate (IF-05).

**Theory and methodology (class C) used in the derivations**
- Working, E. J. (1927). What do statistical "demand curves" show? *QJE* 41(2):212–235 — a locus of realised
  prices traces neither curve; the reason I13 is not identified.
- Bulow, J. & Klemperer, P. (2012). Regulated prices, rent seeking, and consumer surplus. *JPE*
  120(1):160–186 — why surplus above a binding ceiling does not accrue to the buyer.
- Glaeser, E. L. & Luttmer, E. F. P. (2003). The misallocation of housing under rent control. *AER*
  93(4):1027–1046 — allocation behind a ceiling is effectively random; observed consumption carries no
  valuation information.
- Gallego, G. & van Ryzin, G. (1994). Optimal dynamic pricing of inventories with stochastic demand over
  finite horizons. *Management Science* 40(8):999–1020 — I1 and I6.
- Powell, J. L. (1986), censored quantile regression — as `02-a` §6.2 applies it to the lower quantiles
  surviving truncation. Cited without volume or page numbers, because I did not verify them in this pass.
- Ekeland, I., Heckman, J. J. & Nesheim, L. (2004). *JPE* 112(S1):S60–S109 — the affine indeterminacy that
  makes every number in this file a ratio rather than a level.
- Cox, D. R. (1972). *JRSS-B* 34(2):187–202 — the counting-process framework Specification B needs.
- Fosse, E. & Winship, C. (2019). *Annual Review of Sociology* 45:467–492 — bounds rather than point
  estimates under the age–period–cohort collinearity, which is why §6.2.5 of this file refuses a per-day
  slope. (Cited as Fosse & Winship per `01-b` CORRECTION 3; the earlier attribution to "Luo" is withdrawn.)

**Regulatory sources (class A for the regulation, not for the market), as recorded in `01-a` §3**
- NSW Fair Trading, ticket reselling rules; Gov.ie, Sale of Tickets Act 2021 (in force 2021-07-31);
  DBT/DCMS 2025-11-19 announcement and the 2025-12-19 analytical note (the 20% displacement assumption,
  quoted as an official assumption and not as a measurement).
- 16 CFR Part 464, 90 FR 2166, effective 2025-05-12 — the all-in display rule, which is a structural break
  in any US price series and is the reason IF-12 carries the disclosure caveat.

**Records this file depends on and does not restate**
`records/00-data-situation.md` (Gaps 1–4 and the fixture prohibition); `records/F-decision-log.md` (D1, D3,
D6, Q1–Q3, Q5); `01-a-market-structure.md` §2–§6; `01-b-identifiability.md` §2–§6 and its three
corrections; `01-d-external.md` §4–§5; `02-a-price-paths.md` §4.3–§7.3; `02-b-cap-truncation.md` in full;
`02-c-sale-hazard.md` §1–§4.6 and §6; `02-d-elasticity-fees-optimum.md` §2.5, §3.4–§3.6, §4.4, §5;
`02-e-cold-start.md` §2.4, §4.7, CORRECTION 1; `03-b-temporal-correctness.md` §2–§5.

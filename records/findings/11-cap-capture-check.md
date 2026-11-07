# 11 — The cap-capture check: does a proportional resale cap let the organizer capture the resale premium?

| | |
|---|---|
| **Status** | complete. One file written, this one. No code touched, no other record edited, no state file written, no commit, no push. |
| **UTC** | 2026-11-07T14:40Z. The tree moved under me at 14:37Z: another session modified `labels.py`, `value_band.py`, `page.py`, `guidance.py`, `price_features.py` and `orchestrator.py` while this file was being written. Line references below were re-pinned at 14:40Z, and §10.1 says what changed. |
| **Role** | independent economist, adversarial. I did not write the finding under attack and I did not build the engine. |
| **Scope** | one claim: `02-d` §2.5(c) as reconciled by `02-b` §3.5, that a cap in basis points over face lets the organizer capture the resale premium entirely through the primary price, so the objective needs no capture rate. |
| **Method** | reasoning over files on disk. No web research, no new data, no re-estimation, no simulation. |
| **Evidence** | class **C** for every line of algebra (true by construction), class **D** for every mechanism whose sign or size is unmeasured here. No number in this file is an estimate of any market quantity. The only magnitudes quoted are the demo fixture's own displayed numbers and the counts already in the records, and they are quoted as text, not as evidence. |
| **Verdict** | **STANDS-WITH-NARROWING** (§9). The objective-level result survives; the sentence that says the premium is "capturable entirely" does not. |

---

## 0. What this file is

The finding under attack is a derivation, not a measurement, so the only honest way to break it is to
ask what it assumes and whether the assumptions carry the sentence built on top of them. I did not set
out to find that it is wrong. I set out to find the one place where it says more than its algebra does,
and then to see whether that place is cosmetic or load-bearing.

It is load-bearing in the prose and not load-bearing in the objective. That distinction is the whole
report: §2.5(b) and §2.5(c) are correct as statements about the feasible set and about what enters the
objective. The gloss on top of them, "the resale premium is capturable entirely through the primary
price", is not correct under any single definition of "capture", and it invites a reader to believe
three false things at once: that the organizer receives the reseller's margin; that raising face
transfers it; and that the amount is a fixed quantity the record could measure. The fix is a narrowing,
not a withdrawal, and §9 writes it out.

---

## 1. The claim, quoted

From `records/findings/02-d-elasticity-fees-optimum.md`, "What I concluded", item 3 (lines 40–46):

> **3. The resale premium is capturable entirely through the primary price, so the objective needs no
> "capture rate".** `resalePriceCapBps` is basis points over *face value*, and face value is the
> decision variable. Raising `p0` raises the legal resale ceiling `p0(1+c)` in exactly the same
> proportion. A proportional cap therefore does not constrain the organizer's price at all; it
> constrains the *reseller's*. The organizer's binding constraints are demand and uncertainty. This
> kills a class of model that would have estimated "how much of the secondary margin can the organizer
> keep", and it is why 01-b §4.5(ii) found the seller's problem collapsing to one dimension.
> [C, ASSERTED, MEASURED for the bps-over-face definition]

From the same file, §2.5 (lines 330–356), the three results and the scope limit:

> **(a) Scale invariance.** For any `p`, the feasible resale band is `[p, p(1+c)]`. The band translates
> with the decision. The seller's problem is therefore *where to sit in the willingness-to-pay
> distribution*, not *how much of the ceiling to allow*. [C, ASSERTED. This is 01-b §4.5(ii) restated; the
> dependency is stated because the argument is used downstream.]
>
> **(b) A proportional cap is not a constraint on the organizer.** Suppose the organizer raises `p` by a
> factor `λ`. The ceiling becomes `λp(1+c)`, so the reseller can still resell at the same proportional
> markup. Nothing about the cap stops the organizer from raising the price; the only things that do are
> the demand curve (sell-through falls) and the organizer's uncertainty about it. The cap binds the
> *reseller*, not the organizer. [C, ASSERTED]
>
> **(c) The resale market does not add a separate cross-price term to the organizer's problem.** The
> buyer's outside option, waiting to buy on resale, has a price no higher than `p(1+c)` plus fees: it is
> a function of `p`, not an independent price. So substitution between primary and resale is already
> inside the primary demand curve, and the elasticity the objective needs is the *residual* one. §3.1
> says which elasticity that is and §3.5 what breaks it. [C, ASSERTED]
>
> Result (c) is scope-limited and I state the limit: it holds **because** the cap is proportional. A
> fixed-absolute cap, such as a nominal dollar ceiling, would break all three and force an extra term
> into (O) equal to the shadow value of the rationed quantity behind the ceiling. If the operator ever
> changes the definition, this section is void.

And the reconciliation, `records/findings/02-b-cap-truncation.md` §3.5, whose verdict is:

> **Verdict: consistent.** No claim in `02-d` §2.5 has to be withdrawn […] and the sentence that keeps
> them apart is one line: *the cap does not constrain the organizer's price, and it does constrain the
> record of what resellers got.*

I accept `02-b`'s reconciliation as stated. Nothing in this file reopens the question of whether the
cap truncates the record; `02-b` settled that and the direction is not in dispute. What I am testing is
the first half of that one line and the word "capture" inside it.

---

## 2. What the claim gets right

An adversarial report that starts by conceding nothing is not adversarial, it is unserious. Three things
in §2.5 survive every attack below, and they are the three that matter to the engine.

**2.1 The feasible-set statement is true.** The ceiling is `p(1+c)` in lamports, and `p` is a decision
variable at event creation. Therefore, for any price `p` the organizer might name, there is a legal
resale ceiling `p(1+c)`, and no value of `c ≥ 0` removes any `p` from the organizer's feasible set: for
any cap, there is no price the cap excludes. That is arithmetic, not theory, and it is not affected by
anything in §3 to §8 of this file. It is also the exact content of "the cap binds the reseller, not the
organizer" read properly.

**2.2 The objective statement is true.** In (O) the organizer's revenue is `p · S(p)`. The resale price
appears nowhere in (O) except through `q`, and through the royalty term `ρ·E[T]`, which is separately
bounded. So no *additional* "capture rate" term belongs in (O). A term like `κ·(resale margin)` would
credit the organizer with money it does not receive: the margin is not part of the organizer's revenue
at any `p`. This is correct for a
proportional cap, and it stays correct under every attack below, because each attack changes `q`, adds a
constraint, adds a cost, or changes the price level; none creates a revenue channel from resale to the
organizer that (O) is missing.

**2.3 The corollary the finding does not draw, and it is the strongest thing in it.** Set `c = 0`. The
band `[p, p(1+c)]` collapses to the single point `p`, which is exactly the legal form of an above-face
resale ban. Under the claim's own algebra, a ban does not constrain the organizer's price either: the
organizer can raise `p` to the market value and, at that point, the resale price equals the primary
price because there is nowhere else for it to go. So a policy whose purpose is to keep tickets
affordable is, under this model, an instruction to the organizer to raise face to the market-clearing
level. That is a policy-relevant result, it is class C, it follows in one line, and `02-d` does not state
it. `01-a` §1 records that Ireland has banned above-face resale for designated events and venues since
2021-07-31, so the `c = 0` case is not hypothetical. **This is the claim's real bite and §11 says it
belongs in the submission.**

The rest of this report is about the difference between 2.1 and 2.2, which are true, and one sentence
that is not.

---

## 3. Attack 1: reference-price anchoring

**The attack.** If willingness to pay is anchored to the face printed on the ticket, then raising face
is not a free move. It moves demand, and the "capture" is partly a relabelling. Does the claim survive?

**Modified objective.** Let the buyer's all-in price remain `P = p(1+β) + b`, but let demand depend on
the posted face as well:

```
q = q(P, p),   q_P < 0,   q_p =: q_a   (sign not assumed)
```

with two elasticities:

```
ε  ≡  −P q_P / q  > 0        the response to the all-in price at fixed face
ζ  ≡   (p/q) q_a             the response to the printed face at fixed all-in price
```

`ζ > 0` is the anchoring-up case: a higher face raises what buyers think the ticket is worth. `ζ < 0`
is the fairness case: a higher face reads as gouging and costs demand beyond the price effect, which is
the direction the attack names. Both are mechanisms with no evidence in this record; both are class D.

The objective is unchanged in form,

```
Π(p) = N [ q(P, p) · ( m(p) + u ) − u ] + ρ·E[T(p; c)] − F,        m(p) = (1−φ)p − f + a,
```

and the first-order condition gains one term. Differentiating,

```
Π'(p)/N = [ q_P(1+β) + q_a ](m+u) + q(1−φ) = 0
```

and substituting `q_P = −ε q/P`, `q_a = ζ q/p`, then `(1+β)(m+u) = (1−φ)(P − c**)` from (WEDGE):

```
        (P − c**) / P  =  1 / ( ε − ζ·K ),        K ≡ P / (p(1+β)) ≥ 1.          (FOC-2′)
```

With `b = 0` (the post-2025 US case in §1.1), `K = 1` and the denominator is simply `ε − ζ`.

**What changes.** Four things, and the order matters.

1. **The cap still adds no term.** `c` does not appear in (FOC-2′). So the specific conclusion the claim
   was built to support, "the objective needs no capture rate", survives anchoring intact. That is the
   first reason the verdict is not FALLS.
2. **The recommended price moves.** If `ζ > 0`, the effective elasticity is smaller and the recommended
   price is higher; if `ζ < 0`, it is lower. So the finding's price level is conditional on `ζ = 0`, a
   condition §2.5 never states.
3. **The fee-neutrality lemma (§2.3(i)) fails.** That result says the split of the price into posted
   price and ad valorem fee is neutral for the all-in optimum. Under anchoring it is not neutral: demand
   depends on the posted face as well as on the all-in price, so a shift from `p` to `β` at constant `P`
   changes `q`. This is the largest collateral damage in the report, because §2.3 is the paper's sharpest
   exact algebra and the "no capture rate" claim is not the only thing resting on `q = q(P)`.
4. **Identification gets worse, in a specific way.** A price experiment that moves `p` moves `P` and the
   anchor together, so it estimates a compound of `ε` and `ζ`, not `ε`. The engine's `ε` must therefore
   be labelled "response to the posted price", not "response to the all-in price". §3.1 already warns
   that three elasticities are routinely conflated; anchoring adds a fourth.

**Does the claim survive?** Its operative conclusion does. Its words do not, and here is why the
relabelling objection is right. Under `ζ > 0`, raising face raises the whole willingness-to-pay schedule,
so the organizer's extra revenue is manufactured by the reference price, not taken from a reseller. The
amount is not the resale premium and is not bounded by it: it can be larger. Under `ζ < 0`, the organizer
loses demand in excess of the price effect, so part of the premium is destroyed rather than captured. In
both cases "entirely" is a coincidence that holds only at `ζ = 0`. A claim whose scope is a knife-edge
parameter nobody has measured is not false, but it is not an identity either, and it must not be written
as one.

**One partial defence of the claim, and its limit.** If *everything* scales with face, including the
buyer's valuation and the resale price, the problem is homogeneous of degree one in `(p, V)` and no real
decision changes: the organizer's revenue simply scales. That is the pure-anchoring limit `ζ → 1`, where
(FOC-2′) degenerates (`ε − 1`), revenue becomes unbounded in `p`, and the model has no interior optimum
at all. So the defence is self-defeating: the only world in which anchoring makes the claim exactly true
is a world in which the demand model in `02-d` does not exist. What actually happens is partial
anchoring, which is exactly the case (FOC-2′) covers.

**Verdict on A1:** the cap conclusion survives; the elasticity, the neutrality lemma and the word
"entirely" do not.

---

## 4. Attack 2: statutory and social constraints on face

**The attack.** Many jurisdictions and platforms constrain face value itself, and organizers face
reputational costs from a high face. Under a face constraint, does the cap bind as an absolute ceiling
after all? State the condition.

**The hard constraint.** Let the organizer face `p ≤ p̄`, from statute, platform policy, a contractual
price convention, or a most-favoured-customer clause. Then the resale ceiling is `p̄(1+c)`: a number that
does not depend on any decision the organizer can still make. The Lagrangian is
`L = Π(p) + λ(p̄ − p)`, with `λ ≥ 0` and complementary slackness, and

```
λ > 0  ⟺  p* > p̄,
```

where `p*` is the unconstrained optimum of (O). Three consequences follow.

1. **If `p̄ ≥ p*`,** the constraint is slack, `λ = 0`, and the claim is untouched. A face constraint that
   does not bind is not an attack.
2. **If `p̄ < p*`,** the cap is an absolute ceiling in the only sense that matters: the resale price is
   `min(V, p̄(1+c))`, both arguments are outside the organizer's control, and if `p̄(1+c) < V` the resale
   market rations at a fixed number. The premium `p̄·c` is then the reseller's, by the split identity in
   §5, and the organizer's lost value is `(1−φ)(p* − p̄)` per ticket. **Those are two different numbers**,
   and the finding never separates them.
3. **The shadow price is not the premium.** When the house still fills at `p̄`, raising the face cap by one
   lamport earns one lamport of net revenue per ticket, so `λ = N(1−φ)` in money, while the resale premium
   is `N·p̄·c`. The organizer's cost of the face cap and the reseller's margin have no reason to coincide,
   and using one as a proxy for the other is the error the "capture" wording invites.

**Condition for the finding's void.** The claim fails as a statement about capture iff
`p̄ < p*`, i.e. iff the face constraint is tighter than the demand constraint. The finding's own void
condition names only the *definition* of the cap (absolute versus proportional). It should name this one
too, because a proportional cap plus a binding face cap is observationally an absolute cap.

**The soft constraint.** Let `R(p)` be a reputational or fairness cost of setting face at `p`, with
`R' > 0`, `R'' ≥ 0`, and `R` outside the demand curve (it falls on the organizer's future business, not
on this event's sales). Then

```
Π'(p) = N q(1−φ)[ 1 − ε(P − c**)/P ] − R'(p) = 0
⟹      (P − c**)/P  =  [ 1 − R'(p)/(N q (1−φ)) ] / ε .
```

The optimum is strictly lower than without `R`. So the sentence "the only things that do stop the
organizer are the demand curve and the organizer's uncertainty about it" is false as a matter of the
model's own logic: *any* cost of raising face stops it, and a reputational cost is a cost of raising
face. `02-d` §5 assigns `∂p*/∂c` a positive sign through the resale-option channel and calls that channel
class D; a reputational channel is the same class of object with the opposite sign on `p`. Neither is
measured. That is the point: the finding asserts two constraints and the model admits at least three.

**What the record actually contains.** `01-a` §1 surveys the regulatory regimes it found: NSW caps resale
at the original price plus up to 10%, Ireland bans above-face resale, and the UK announced a cap at
"original cost plus unavoidable fees". Every one is a constraint on the *resale* price, anchored to the
original price, which is proportional by construction. **The record contains no example of a statutory
cap on face value in the jurisdictions it examined.** So attack 2 does not defeat the claim on the
evidence on disk; it defines a boundary that the claim does not currently mark. I am not entitled to
assert that such regimes exist elsewhere, and I do not. Class C for the algebra, class D for the claim
that `R` is materially non-zero in this market.

**Verdict on A2:** the claim survives on the evidence in the record, and it is void the moment a face
constraint binds. The condition is `p̄ < p*`, and it belongs in the finding's scope limit next to the
absolute-cap condition.

---

## 5. Attack 3: which direction the cap binds, and what "capture" means

This is the attack that does the work. The other four narrow the claim; this one shows that the sentence
in item 3 is not a restatement of the algebra but a different statement that the algebra contradicts.

**Three objects, routinely conflated.** Order buyers by willingness to pay `w_1 ≥ w_2 ≥ … ≥ w_M`, with
capacity `N`. Then:

| Object | Symbol | Who receives it |
|---|---|---|
| The organizer's revenue | `p · S(p)` | the organizer |
| The resale price on a resold ticket | `r = min(V, p(1+c))`, where `V` is the willingness to pay of the marginal excluded buyer | the reseller, as a gross margin `r − p` |
| The economic value of the allocation | `Σ_{i ≤ N} w_i` (or, above the ceiling, `Σ_{i: w_i > p(1+c)}(w_i − p(1+c))`) | nobody, in the capped case: `01-b` §4.5(iii) records that it is dissipated by non-price competition |

Only the first is the organizer's. The "resale premium" is the second column, second row. The value that
exists in the market is the third. **They differ by the excess-demand distribution**, and the finding's
sentence can be read as any of the three. That is the defect.

**The decomposition identity.** Take a ticket that resells at the ceiling, which is the regime the engine
already detects and calls `capped_and_binding` (`ticketpath/core/value_band.py:56`). Then

```
r = p(1+c) = p + pc,
```

so the resale price decomposes into the organizer's original price and the reseller's margin in the fixed
ratio

```
        organizer : reseller  =  p : pc  =  1 : c .                                   (SPLIT)
```

`(SPLIT)` is an identity conditional on the ticket settling at the ceiling; it is not a behavioural
assumption. For rows that settle below the ceiling the margin is `r − p < pc` and the ratio is not fixed,
which is why the statement is about the mass at the ceiling and not about the whole tier.

Now differentiate. `∂p/∂p = 1`, `∂(pc)/∂p = c`, `∂r/∂p = 1+c`. **Raising the primary price scales both
components and leaves their ratio unchanged.** The organizer's revenue and the reseller's margin both
scale with `p`, in the same `1 : c` ratio at every level. The only instrument that changes the ratio is
`c`:

```
d/dc [ 1/(1+c) ] = −1/(1+c)² < 0,
```

so a tighter cap raises the organizer's share of the resale price, and `c → 0` sends it to one.

Read that against the claim. "The resale premium is capturable entirely through the primary price" cannot
mean that the organizer receives `pc`: it never does, at any `p`. While the cap binds it cannot mean that
raising `p` transfers the reseller's margin: there, raising `p` *increases* the margin in money. What
raising `p` does is increase the organizer's own revenue by exactly `dp` per ticket, which is the ordinary
exercise of market power and has nothing to do with the cap. **Inside the cap's reach the premium is not
captured; it is enlarged.**

**And the escape is real, which is the part that must be stated exactly.** Push `p` until the cap stops
binding:

```
p(1+c) ≥ V   ⟺   p ≥ V/(1+c).
```

At `p = V/(1+c)` the ceiling equals `V`, the cap binds exactly, the resale price is `V`, and the margin is
`pc = Vc/(1+c)`, which is continuous with the binding region. Above the kink the cap is slack, the resale
price is pinned at `V`, and the margin is `V − p`, so `∂(margin)/∂p = −1`: **raising `p` there does
transfer the reseller's margin to the organizer, one for one, per resold ticket.** So the claim is not
empty. It is mis-specified. Three things follow, and they have to be said together.

1. The transfer happens only in the region where the cap is **slack**, i.e. where the cap is doing no
   work. Inside the cap's reach the derivative has the opposite sign: raising `p` *enlarges* the margin
   (`∂(pc)/∂p = c`) rather than transferring it. So the premium is captured by leaving the cap behind,
   not by using it, and the cap cannot be what delivers the premium.
2. The transfer is **per ticket, not in aggregate**. At `p = V` the margin is zero and the organizer is
   charging the market value, but only buyers with willingness to pay at or above `V` remain, so the
   number of tickets sold at that price is small. Whether `V·D(V)` exceeds `p·S(p)` is an empirical
   question the claim does not answer and this file cannot.
3. The organizer's revenue is `p·S(p)` in **both** regions; the cap never enters that expression. So the
   organizer's gain from the whole exercise is the change in `p·S(p)`, not the premium.

**The paradox, stated once.** There are exactly two ways for the organizer to end up receiving the whole
resale price:

- `c = 0`: resale is at face, so the resale price equals the primary price by definition. The premium is
  zero.
- `p ≥ V`: nothing resells above face. The premium is zero.

In both limiting cases the premium the claim promises to capture is zero at the point of capture. In the
interior case `0 < c` and `p(1+c) ≤ V`, the organizer receives `1/(1+c)` of the resale price and the
reseller receives `c/(1+c)`. So the claim is true exactly where it is empty, and where it is not empty it
is not a statement about the cap. This is not a trick of algebra; it is the reason a proportional cap is a
*split* instrument, not a *ceiling* instrument.

**Verdict on A3:** the sentence falls, as an equivocation between two different claims: "the organizer
can escape the cap by raising the price" (true, and it is §2.5(b)) and "the organizer receives the resale
premium" (true only where the cap is slack, and there it is ordinary pricing). The objective-level
conclusion stands, and §9 states the replacement.

---

## 6. Attack 4: the equilibrium question

**The attack.** If every organizer raises face to the ceiling, the ceiling is no longer a premium. Say
what happens to the market, and whether the claim is a comparative static that ignores its own
general-equilibrium consequence.

The claim is a partial-equilibrium comparative static: one organizer's `p`, with every other price and
the cap held fixed. That is a legitimate object. The problem is what happens when it is applied.

**With absolute willingness to pay.** Let `X(p) = D(p) − N` be excess demand at the ceiling, which is
also the resale supply at the ceiling in the simplest model. The premium per resold ticket is `pc`, so
aggregate premium is roughly `X(p)·p·c`, and

```
d/dp [ X(p)·p·c ] = c [ X(p) + p·X'(p) ] ,
```

whose sign is ambiguous: the price effect raises the premium per ticket and the quantity effect shrinks
the number of resales. So the per-ticket statement does not aggregate, and the claim gives no reason for
the aggregate to rise. If every organizer raises `p`, every organizer sells fewer tickets, and the total
premium may fall. Nothing here needs a magnitude; the sign is undetermined by the claim itself.

**With anchored willingness to pay.** `ζ > 0` means every face rise lifts the whole schedule, so the
allocation is unchanged in real terms and every price scales. The premium then scales in money and is
unchanged in real terms: the entire "capture" is inflation. At `ζ → 1` the model has no equilibrium at
all (§3). So the GE consequence of the claim, under the one mechanism that makes capture look unlimited,
is that capture becomes nominal.

**The definitional point, which is the real one.** The premium is defined *relative to face*. If every
organizer prices to value, the premium is zero everywhere, by construction. So the premium is a
disequilibrium gap: it exists because faces are below values, and "capturing" it means closing it. A
cross-section of observed markups therefore measures how far the market is from its own optimum, not a
structural share that could be harvested year after year. **The claim, universally applied, deletes its
own object.** That is the sense in which it ignores its own GE consequence: the first-round best
response is to raise face, the second round has no premium to raise face into.

**The policy-correction round, which is a hypothesis and labelled as one.** If the instrument is
proportional and organizers respond by raising face, the observed effect of the policy is a higher face
and an unchanged proportional markup. A regulator whose objective was affordability then has a reason to
switch to a non-proportional instrument, an absolute money ceiling or a cap on face. That would satisfy
the finding's own void condition. This is class **D**: it is a prediction about policy response, not
evidence from this record, and I have not searched for it.

**Verdict on A4:** the claim does not aggregate and is a best-response statement, not an equilibrium one.
That does not break the objective, and it does break any reading of "capturable entirely" as a quantity.

---

## 7. Attack 5: the falsifier

One test, with the data it needs, that would settle whether capture happens.

**First, the trap that makes the obvious test worthless.** On rows that settle at the ceiling,
`r = p(1+c)` by definition, so the realised resale price is mechanically proportional to face and the
markup is exactly `c`. A regression of `ln r` on `ln p` using binding-cap rows returns a coefficient of
one *by construction*, whatever the market thinks the ticket is worth. **The rows that carry the ceiling
are exactly the rows that cannot answer the question.** This is `02-b`'s premise stated as a measurement
problem, and it is why the finding's existing falsifier (`02-d` §8(2), organizers pricing so that
`p(1+c)` tracks an external anchor) tests a different object: it tests organizer behaviour, not whether
the market value moves with face.

**The test: the scale test.** Use only sales where the cap does not bind, so that the observed resale
price is `V` and not policy.

- **Population.** Settled resales on events with `resalePriceCapBps = null`, or on capped events with no
  row at the ceiling and the highest resale strictly below the ceiling. Both are already represented in
  the schema and the fixture store; `null` is a legal value in `lib/types.ts:68`.
- **Variation.** At least two face levels for comparable events: the same artist or tour, the same venue
  class, the same on-sale window. The engine's store is too small for this (the demo has eight events,
  five with any resale), so the test is a data-collection question and a money question, not a modelling
  question.
- **Regression.** `ln r_i = α + β·ln p_{g(i)} + δ·(days to event) + event-type controls + e_i`, with
  `p_{g(i)}` the face in force for that tier at that resale, and standard errors clustered by event.
- **Pre-declared decision rule.** Three alternatives, and the test can separate them:

| Estimate | Reading | What follows |
|---|---|---|
| `β = 1` | the market value moves one for one with face | the value and the ceiling move together; the split is `1 : c` and the premium is a fixed real share, so the "capture" is nominal |
| `β = 0` | the market value is absolute; face is a label | raising face moves the ceiling but not the value, so beyond `p = V/(1+c)` nothing is capturable, and the claim's economic content fails |
| `0 < β < 1`, or `β > 1` | partial anchoring, either sign | (FOC-2′) applies and the objective must carry the anchor term |

- **Why this settles "whether capture happens".** If `β = 0`, the ceiling rises while the value does not.
  The organizer can raise `p` until `p(1+c) = V` and then stops, and every lamport of ceiling above `V`
  is a number nobody will pay. Under `β = 1`, the value rises with face, so the organizer can keep raising
  `p` and the premium rises with it; the "capture" is then a nominal expansion of a fixed real split,
  which is the `(SPLIT)` identity again, not a transfer of the reseller's margin. Under either estimate
  the sentence "capturable entirely" is wrong, and the report says which way it is wrong.
- **Data it needs, and nothing else.** The settled resale price, the tier's face in force at that resale,
  the timestamp, the tier, and enough events at different face levels. All of it is in the contract
  already. No new field, no listing data, no cap variation. The binding constraint is the number of
  comparable events, which is the operator's decision.

**A second, weaker test, for completeness.** If `c` is the organizer's instrument (see A8), the claim
predicts organizers set it as tight as the platform allows and price face high. Observed caps
substantially above the minimum would falsify the behavioural reading. I do not rely on this one; it is
confounded by regulation and platform defaults, and the fixture's 15% is synthetic.

---

## 8. Four further attacks, found on the way

### A6 — The ceiling is proportional to *face*, not to the primary price the buyer pays

`02-d` §2.5(b) says "suppose the organizer raises `p` by a factor `λ`". In the objective, `p` is the
posted price and `P = p(1+β) + b` is the buyer's all-in price. Only `p` moves the ceiling. So

```
ceiling = p(1+c),  d ln ceiling / d ln P = P / (p(1+β)) = K ≥ 1,
```

with equality only when the buyer-side per-unit fee `b = 0`. Two consequences. A price rise funded by a
per-unit buyer fee leaves the ceiling exactly where it was, so the policy tightens on the fee-funded part
of the price. A price rise funded by face moves the ceiling by `K` per cent per per cent of all-in price,
which is *more* than one for one when `b > 0`. Since 16 CFR Part 464 makes the all-in number the displayed
price in the US (§1.1, class A for the regulation), this is not a technicality: the number the buyer sees
can rise without the ceiling moving, and the claim's "primary price" must be read as "face component of
the primary price". Class C. `01-a` §1 already flags that the fee side is two-sided and ambiguous by
20–40%, so the component split is not small.

### A7 — Proportionality is a property of an act, not of a state

Measured in `02-d` §1.1 (line 105): "A price is fixed at event creation", and there is no price-mutation
endpoint in the nine-endpoint API. So face is chosen once and then frozen, and from that instant the
ceiling `p(1+c)` is a fixed number in lamports. The finding's void condition, "if the cap ever becomes an
absolute number", is therefore satisfied at every moment after event creation, for every ticket already
issued. This is not a contradiction with `02-b`; it is a sharper version of `02-b` §3.5's separation:

- the finding is a statement about **setting** face, and it is true there;
- for **interpreting** a record produced under a fixed face, the cap is absolute, and the finding is
  inapplicable rather than wrong.

The practical consequence is that the claim can never license a statement about the current event's
resale record. It licenses a statement about the next event's price. The two are different decisions and
the finding does not mark the boundary.

### A8 — If the organizer sets the cap, the cap is a second decision, and the finding analyses only one

`resalePriceCapBps` is a field on `Event` (`lib/types.ts:68`), the product text calls it "the organizer's
cap" (`SUBMISSION-PACK.md`), and the console lets a reader price against a candidate `capBps`. If the
organizer chooses `c`, then `(SPLIT)` says its revenue share of the resale price is `1/(1+c)`, maximised
at `c = 0`, while the demand channels in `02-d` §5 (the buyer's resale option, and the outside option in
§2.5(c)) say a higher `c` raises willingness to pay. So the organizer's problem is two-dimensional with
an interior optimum in `c`, and §2.5 analyses `p` only. The claim's sentence "the cap binds the reseller,
not the organizer" is a statement about the resale constraint, not about the organizer's policy problem.
Two readings are possible and the finding must say which: `c` exogenous (a regulator or platform sets it,
and `p` is the only instrument) or `c` endogenous (the organizer sets it, and the finding is partial).
The frontend currently only displays the field, with no setter, so within the shipped product `c` is
exogenous. Class C for the algebra, D for the behavioural implication.

### A9 — The §3.6 price experiment cannot identify the cap's effect, because the claim makes them collinear

`02-d` §3.6 says: "Because the cap is proportional, randomising `p` randomises the resale ceiling too, so
the same experiment identifies the cap's effect on demand as a free by-product." That is backwards. If
the ceiling moves in proportion to `p`, then `c` and `p` are perfectly collinear in that design, and the
demand response is a mixture of the price effect and the ceiling effect that no amount of randomising `p`
can separate. Proportionality is precisely what *prevents* the cap's effect from being a free by-product.
Identifying it needs variation in `c` at fixed `p`, which is cross-event and confounded with everything
else. One sentence to withdraw, and it is the same sentence that makes A5's test necessary.

---

## 9. Verdict

**STANDS-WITH-NARROWING.**

**What stands, unchanged.**

1. A cap in basis points over face removes no primary price from the feasible set. `02-d` §2.5(b), read as
   a statement about the feasible set, is correct and cannot be broken by any of A1 to A9.
2. The organizer's objective needs no "capture rate" term. `c` enters (O) only through `q`, and the
   resale margin is never the organizer's revenue. §2.5(c) and §1.5 are correct in their conclusion.
3. The void condition is right, and it is wider than stated: the finding is void if the cap is absolute,
   *and* if a face constraint binds (`p̄ < p*`), *and* if a reputational cost of raising face is
   material, *and* for any record already produced under a fixed face (A7).

**What falls.**

1. "The resale premium is capturable entirely through the primary price." While the cap binds, the resale
   price decomposes into `p + pc` in the fixed ratio `1 : c`, raising `p` scales both parts and leaves
   the ratio alone, and the organizer never receives the reseller's share. The premium is transferred
   only after `p` has risen past `V/(1+c)`, where the cap is slack, the resale price is pinned at `V` and
   `∂(margin)/∂p = −1`; there the transfer is ordinary pricing to the market value, on the smaller
   number of tickets that still sell, and it is not a cap effect. The organizer's revenue is `p·S(p)`
   throughout, and the premium is never additive to it.
2. "The only things that do stop the organizer are the demand curve and the organizer's uncertainty about
   it." Any cost of raising face stops it, and a face constraint stops it absolutely.
3. "Raising `p0` raises the legal resale ceiling `p0(1+c)` in exactly the same proportion." True for the
   face component; false for the all-in price whenever `β` or `b` is non-zero (A6).
4. "It constrains the reseller's." Complete only for the feasible set. The cap constrains the *split* of
   the resale price, and it constrains the record (`02-b`'s half, which is not in dispute).

**The narrowed wording, to replace item 3 of "What I concluded".** Written to be pasted, class C:

> **The cap is a split instrument, not a ceiling on the organizer.** `resalePriceCapBps` is basis points
> over face and face is the organizer's decision, so raising face raises the legal resale ceiling in the
> same proportion and no primary price is removed from the feasible set. The cap therefore adds no
> revenue channel: the objective needs no capture rate. What the cap does determine, when it binds, is
> how the resale price divides. A ticket that settles at the ceiling sells for `p(1+c)`, which is the
> organizer's price `p` plus the reseller's margin `pc`, in the fixed ratio `1 : c` that no primary price
> can change. Raising `p` scales both parts; it does not transfer the reseller's share. The organizer's
> only way to keep more of the resale price is a tighter cap, and its only way to take more money is a
> higher price, which is bounded by demand and by its own uncertainty about it, not by the cap. Once `p`
> has risen past `V/(1+c)` the cap is slack, the resale price is pinned at the market value, and further
> increases in `p` transfer the reseller's margin one for one, on however many tickets still sell at
> that price. The result is void if the cap becomes absolute, if a constraint on face binds below the
> unconstrained optimum, or if a material cost of raising face exists.

One line for a slide, if a slide needs it: **the cap decides how the resale price divides; the price
decides how big it is.**

---

## 10. What the engine must therefore say

I did not touch code. These are the statements the shipped artifact must make, with the sites where the
current text conflicts.

**10.1 One message contradicts the finding and must change.** `ticketpath/core/primary_optimum.py:154–190`
refuses a recommendation above `face·(10000+cap)//10000`, and the user-facing reason at
`ticketpath/core/labels.py:423–428` says "a recommendation above that ceiling is a price the cap forbids".
That is the absolute-cap proposition, and it is the sentence §2.5 exists to deny. The *check* is
defensible as a data-validity rule: a candidate cap tighter than the resales this page is pricing from
makes those resales illegal under the policy being tested, so the record cannot support a price under it.
The *message* must say that and must stop saying the cap forbids a primary price. Suggested text:

> A cap of {cap_bps} basis points puts the ceiling at {ceiling_lamports}. The resales this page prices
> from settled at or below the event's recorded cap, so under the candidate cap some of them would be
> illegal and the record cannot support a price. The cap does not forbid a primary price; it forbids a
> resale price. No primary price is stated here because the record, not the cap, has run out.

**10.2 The `[EXACT]` ceiling line is right and needs one companion sentence.** In the binding regime the
recommended floor is the highest recorded resale price (`ticketpath/core/value_band.py:357`), and in the
demo that highest price is the ceiling itself (eight of nine sales settled there), so the floor and the
ceiling are the same number (1.38 SOL on face 1.20 SOL at 15%). A reader sees the cap used as the target
while label A10 (`labels.py:149–152`) says it is not. Add, wherever the two numbers coincide:

> The floor and the ceiling are the same number because the highest recorded resale settled at the
> ceiling. That makes the ceiling the highest price anyone has paid and therefore a floor on value. It
> is not the organizer's price, and the value above it is not measured.

**10.3 Record the instrument type, or refuse to price an absolute cap.** `resalePriceCapBps` is
proportional by the contract, and the engine has no field that can represent an absolute ceiling. If an
absolute cap is ever ingested it will be read as proportional and every number in §2.5 will be silently
wrong. Either add the instrument type to the payload, or make the loader refuse a cap it cannot type.
`02-d` §2.5's own limit sentence requires this; the engine does not implement it.

**10.4 Never convert an observed markup into a capturable sum.** There is no code path that does this
today (`grep -rn "captur|premium" ticketpath/` returns one unrelated hit in `wallet_verification.py`),
and the narrowing makes it a rule: the demo's "22.03 SOL across 12 sales, average markup +12%" is the
size of a gap that the recommended price is designed to close, not a revenue opportunity. If the
organizer priced at the floor, that gap would be gone and what remains is churn at face.

**10.5 The recommendation is a floor, and the finding's narrowing does not change the number.** The
engine already says "at least" and "that is a floor, not an estimate". Keep it. What changes is the
sentence around it: the amount above the floor is not a function of `c`.

**10.6 Do not describe the cap as enabling capture, and do not describe it as a burden.** Both readings
are in the artifact's vicinity: A10 says "floor on value, not a target", while the refusal message says
"a price the cap forbids". One of them has to go, and it is the second.

**10.7 The band must not be allowed to become the argument.** While I was writing this, another session
added a rule that trims the top of the value band to the ceiling implied by the cap in force
(`value_band.py`, the `limits` block, and the new `P_BAND_STOPS` label). As a presentational rule it is
defensible: a page that says it enforces a cap should not print a range above it. It does, however, put
the absolute reading of the cap into a second place, because the ceiling is computed from the *recorded*
face. That is the same arithmetic as 10.1 and it needs the same sentence: the ceiling bounds a *resale*
price; a band that stops there is stopping at the highest price a resale record can evidence, not at the
highest price a primary market would bear. If the two sentences are not distinguished, the page will
read as if the cap sets the primary price, which is the claim this file exists to correct.

---

## 11. What the submission text must therefore say

The submission is `records/DELIVERABLE.md` §12.3 and `records/SUBMISSION-PACK.md`. §12.3 items 1–3 are
the defensible half and can stand; item 2's closing clause, "The cap binds the reseller, not the
organiser", is true of the feasible set and must not be left standing alone, because a reader supplies
the wrong second half. Four changes, and one thing that should not change.

**11.1 Replace the capture sentence wherever it appears.** The sentence to stop saying is in the finish
line of this report. What replaces it, in the submission's register:

> A cap quoted in basis points over face cannot stop the organizer raising face, and it does not create a
> second revenue channel, so the pricing objective needs no capture rate. It fixes how the resale price
> divides: the organizer's price plus the reseller's margin, in the ratio `1 : c`. The organizer's share
> of the resale price is therefore a function of the cap, not of the price, and the size of the resale
> market is a function of the price, not of the cap.

**11.2 State the scope conditions next to the claim, not in a footnote.** Proportionality to face; a face
that is constrained; and a face that is already fixed for every ticket issued. A cap that is absolute, or
a face that is constrained, or an event already on sale, voids it. The finding says the first; A2 and A7
supply the other two.

**11.3 State the `c = 0` corollary.** It is the claim's strongest policy content and it is currently
absent: an above-face resale ban, which is a proportional cap at zero, does not constrain the organizer's
price at all; it only removes the reseller's margin and leaves the organizer free to price at the market
value. `01-a` §1 records that Ireland has such a ban, so this is not academic. The corollary is class C
and the policy reading of it is class D.

**11.4 Describe the demo's headline correctly.** "Recommended primary price: at least 1.38 SOL" is a
floor, the cap's ceiling and the highest observed resale price are the same number because the fixture is
built with eight of nine sales at the ceiling, and the sentence "that is a floor, not an estimate" is
already there and is right. Add one clause saying the coincidence is why the number equals the ceiling,
so a viewer does not conclude the cap sets the price.

**11.5 One thing the submission should keep exactly as it is.** `DELIVERABLE.md` §2.3(a) already says
"the resale record cannot set the primary price, and the primary price must come from a demand object".
That is the correct consequence of the narrowing and it predates this check. The defect is confined to
the word "capture", not to the architecture.

---

## 12. What would falsify the narrowed claim

The narrowed claim has three parts, and each has its own falsifier. The first is arithmetic and cannot
fail; the second and third can.

1. **Arithmetic:** raising face by `λ` raises the ceiling by `λ`. Falsified only by a change in the
   contract's definition of `resalePriceCapBps`. This is the finding's existing void condition and it is
   correctly stated.
2. **The split:** on tickets settling at the ceiling, the resale price divides `1 : c` between the
   organizer's price and the reseller's margin. Falsified by a settled resale at the ceiling whose price
   is not `p(1+c)`, i.e. by an arithmetic or rounding error in the store, or by an off-rail consideration
   (`01-a` §3). The second is the real one, and it is `02-b`'s business, not mine.
3. **The scope:** the organizer can reach the market value without the cap interfering. Falsified by the
   scale test in §7 returning `β = 0`, or by a binding face constraint (`p̄ < p*`), or by a material
   reputational cost. The scale test is the one to run, and the data it needs is in the schema now.

What would *not* falsify it: an observed markup equal to the cap. That is an identity under a binding
cap (A5), and treating it as confirmation is the error this whole file is about.

---

## 13. Limits of this check

- **This is an argument, not a measurement.** Every conclusion is class C or D. I did not estimate an
  elasticity, a repricing response, or a reputational cost, and no number here is evidence about any
  market.
- **I did not test the engine.** I read the code to find what it says; I ran nothing. The line references
  are pinned to a tree that moved under me at 14:37Z (another session edited six files; `primary_optimum.py`
  was not one of them). The three files I cite hash to `primary_optimum.py 53322138877df920`,
  `labels.py cad07d05165e8592`, `value_band.py cc9397bf3ae8739f` at that instant. If they move again, the
  line numbers will be stale; the quoted sentences are the check.
- **I accept `02-b` in full.** This file does not reopen truncation, censoring or the enforcement locus.
- **I did not search for a source on anchoring, on face caps, or on reputational pricing costs.** All
  three are labelled class D for that reason. A real source on any of them would sharpen §3, §4 or §8,
  and the absence is stated rather than filled.
- **The `β` in the scale test is a reduced-form mixture, not a structural parameter.** It is the
  elasticity of the realised resale price with respect to face, which under the model is a function of
  both the use value and the anchor. The test tells you which regime you are in; it does not identify
  `ζ` on its own.
- **One judgement call, stated so it can be overruled.** I read "capturable entirely" as a claim about
  money reaching the organizer, because that is what the surrounding sentence ("the secondary margin can
  the organizer keep") says. Under the weaker reading, "capture" means "reach the market value", and then
  the claim is true and only the word is wrong. Even under that reading, "entirely" fails, because the
  reach is bounded by demand, by information, and by the split.

---

## Appendix: the attacks, one line each

| # | Attack | What it changes | Breaks the objective? | Breaks "capturable entirely"? |
|---|---|---|---|---|
| A1 | Reference-price anchoring | `q = q(P,p)`; (FOC-2′) and a failure of ad valorem neutrality | No | Yes, unless `ζ = 0` |
| A2 | Face constraint or reputational cost | A constraint `p ≤ p̄`, or a cost `R(p)` | No, but adds a shadow price | Yes when `p̄ < p*` or `R' > 0` |
| A3 | Revenue versus value | `(SPLIT)`: the resale price divides `1 : c` | No | Yes, decisively |
| A4 | General equilibrium | The premium is a disequilibrium gap | No | Yes as a quantity |
| A5 | The falsifier | The binding rows cannot answer the question | No | It is the test that decides |
| A6 | Face versus all-in price | The ceiling is proportional to face, not to `P` | No | Yes, for fee-funded rises |
| A7 | Proportionality is an act, not a state | The cap is absolute for every issued ticket | No, but the finding is inapplicable | Yes, for any existing record |
| A8 | The organizer may choose `c` | The problem is two-dimensional | No, but §2.5 is partial | Yes, as a full description |
| A9 | The §3.6 experiment | `c` and `p` are collinear by construction | No | It blocks the obvious test |

None of the nine changes the form of the objective. Seven of the nine defeat at least one reading of
"capturable entirely"; A5 and A9 defeat the tests for it rather than the sentence itself. That ratio is
what STANDS-WITH-NARROWING means here.

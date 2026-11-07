# Phase 2-D — Fee and settlement structure, elasticity, and the primary-price optimum

**Status:** complete (first pass, derivation plus evidence). **Written:** 2026-11-07T11:05Z.
**Agent:** `p2-d-elasticity-fees-optimum`. **Append-only.**
**Scope:** RESEARCH-PROGRAM §3 Phase 2 domains C (supply and demand) and F (risk and stochastic
modelling), and Phase 5 in full; §4 in full. Answers Gap 4 of `records/00-data-situation.md` (no
fee, royalty or settlement field) and carries D4 (fees as a parameter, not an assumption) through to
an implementable decision rule.
**Depends on:** `AGENTS.md`; `RESEARCH-PROGRAM.md` §3 Phase 2 C+F, Phase 5, §4; `records/README.md`;
`records/00-data-situation.md` (Gap 4, and the rule that `lib/mock/` never enters a result);
`records/findings/01-a-market-structure.md` §3–§6; `records/findings/01-b-identifiability.md` T4, T5,
§4.5, §5; `records/F-decision-log.md` D1–D4, Q1–Q3; `/home/friend/ticketing-frontend/lib/types.ts`
and `API_CONTRACT.md` (read directly in this pass, for the measured product facts in §1.1).
**Labelling:** every claim carries a class (A–E per §4.3) and a tag: **MEASURED** (a number or fact I
read from a source or from a file in this pass, quoted with its market and sample) or **ASSERTED**
(reasoning, derivation, or a characterisation of a source I did not read in full). Derivations are
class **C**: true by construction, not by measurement in ticket markets.

---

## What I concluded

1. **The objective is a capacity-truncated, risk-adjusted expected-profit maximisation over a price
   vector, and three of its four fee terms collapse into one scalar.** The static optimum satisfies a
   Lerner condition against a single effective per-ticket wedge
   `c** = b + (1+β)(f − a − u)/(1−φ)`, where the letters are the buyer-side per-unit fee, the
   buyer-side ad valorem rate, the organizer-side per-unit fee, the organizer-side ad valorem rate, the
   ancillary margin per attendee and the cost of an empty seat. Nothing else about the fee stack moves
   the recommended price. That is the answer to "what would a settlement field have to contain": two
   numbers per settled sale, `buyerTotalLamports` and `netToOrganizerLamports`, and the fee term stops
   being a parameter. [C, ASSERTED]

2. **Ad valorem fees are neutral for the optimum and per-unit fees are not.** A pure proportional fee,
   on either side, is a multiplicative wedge: it rescales the objective and leaves the all-in price at
   the same argmax. A per-unit fee is an additive wedge: it acts as marginal cost and moves the price
   up. This sharpens D4. D4 said the two give different optima, which is right, but the sharper
   statement is that one of them gives *no* different optimum, and it is the one everybody worries
   about. [C, ASSERTED; class B support from tax incidence, Delipalla & Keen 1992]

3. **The resale premium is capturable entirely through the primary price, so the objective needs no
   "capture rate".** `resalePriceCapBps` is basis points over *face value*, and face value is the
   decision variable. Raising `p0` raises the legal resale ceiling `p0(1+c)` in exactly the same
   proportion. A proportional cap therefore does not constrain the organizer's price at all; it
   constrains the *reseller's*. The organizer's binding constraints are demand and uncertainty. This
   kills a class of model that would have estimated "how much of the secondary margin can the organizer
   keep", and it is why 01-b §4.5(ii) found the seller's problem collapsing to one dimension.
   [C, ASSERTED, MEASURED for the bps-over-face definition]

4. **There is no transferable own-price elasticity for primary-market live tickets under a resale cap,
   and the literature's elasticity estimates are not a substitute.** The published record is sports
   attendance regressions, in which "the coefficient on price ... is either positive or, if negative,
   so small that at current prices demand is inelastic" (Noll 2013, quoting the standard result), and
   which Noll's chapter exists to explain as an endogeneity artefact. The one ticket-level performing
   arts study I could read reports "weak elasticity" with no number (Ozhegova & Ozhegov 2018, four
   seasons of the Perm opera and ballet theatre). The best concert dataset in the field reports mean
   capacity utilisation of 0.99 across its 56 events (Leslie & Sorensen 2014), which is the direct
   reason elasticity is not identified there either: the venue fills, so the price response is
   censored away. [A for the quoted characterisations, MEASURED; ASSERTED for the "no transfer"]

5. **The UK government's own cost-benefit model of a resale price cap contains no elasticity at all.**
   It is a flow-accounting model over 37.1m primary and 1.9m secondary tickets with stated assumptions
   (75% markup, 80% of resale by touts, 95% and 25% volume reductions, 20% displacement). That is the
   state of the art in official analysis of this exact policy question, and it is assumption-driven.
   [A, MEASURED, read in full]

6. **Because demand is inelastic at observed prices and `c**` is small, the model degenerates to a
   boundary rule.** With constant elasticity the optimum is `p* = c** η/(η−1)`. When the per-ticket
   wedge is a few percent of face and η is near 1.2, that formula returns a price *below* the price at
   which the house fills, so the binding optimum is the capacity boundary: the highest price at which
   the venue still sells out. That, not the Lerner term, is what the resale record can actually inform
   today. It is also why the engine must report a bound and not a fabricated interior optimum.
   [C, ASSERTED]

7. **Risk is a second-order correction with an ambiguous sign, and it is not the source of the
   primary-secondary gap.** Capacity truncation flattens the quantity response and pushes the
   risk-neutral optimum *up*; downside-risk aversion pushes it *down* whenever the adverse demand state
   is elastic. Both are derived in §5.1. The gap the literature measures is better explained by
   inframarginal pricing under sell-out plus the organizer's own uncertainty about the clearing price,
   which is where Courty's option-value argument sits. [C, ASSERTED]

8. **Multi-tier is the natural instrument and the contract already carries it; dynamic is not
   implementable at all.** `TicketTier.faceValueLamports` is per tier and static, and `API_CONTRACT.md`
   has no price-mutation endpoint (9 endpoints, 7 reads, 2 wallet-verification POSTs). A dynamic policy
   is a schema and product change, which is the operator's decision, not the model's. The measured
   evidence on multi-tier is 5% average revenue gain from price discrimination across 21,120 concerts
   [A, MEASURED], and most concerts do not use it: 56% offer two price categories, 25% one. [A,
   MEASURED]

9. **The engine's honest output today is a price, a range, the two parameters it had to assume, and the
   conditions under which the recommendation is wrong.** Wording in §6, written to be pasted into an
   organizer report. With no elasticity it reports the sell-through boundary and says so, in one
   sentence, without hedging. [C]

---

## 1. The objective

### 1.1 What the product and the contract fix, before any mathematics

Four facts are measured in this pass and they constrain the objective rather than decorate it.

| Fact | Evidence | Consequence |
|---|---|---|
| There is no resale-listing path in the product. Routes are `/`, `/events/[eventId]`, `/tickets/[ticketId]`, `/my-tickets`, `/organizer`, `/verify` plus error/not-found. | **MEASURED**, `ls app` in `/home/friend/ticketing-frontend` | The engine prices primary tickets only. It has no instrument for a resale ask and must not model one. |
| The API surface is read-only except wallet verification: 9 endpoints, of which only `POST /api/wallets/:wallet/verification{,/challenge}` write, and those write a verification record. | **MEASURED**, `API_CONTRACT.md` endpoint list | No price-mutation endpoint exists. A price is fixed at event creation. A dynamic policy is a product change. |
| `TicketTier.faceValueLamports` and `totalSupply` are the only price and quantity fields. `Event.resalePriceCapBps` is "hard ceiling on resale price as basis points over face value". | **MEASURED**, `lib/types.ts` | The cap is *proportional to the decision variable*. §2.5 turns this into a result. |
| No fee, royalty, settlement, net-to-seller or total-price field exists anywhere in the contract. `grep -in` for fee/royalty/settle/net over `lib/types.ts` and `API_CONTRACT.md` returns three lines, all of them false positives: two `devnet` cluster names and the phrase "non-monetary". | **MEASURED**, this pass; confirms Gap 4 | The fee stack is a required configuration input. §2.6 says what would end that. |

One further measured fact changes the fee model's shape. Since 2025-05-12, 16 CFR Part 464 §464.2
requires a business offering a live-event ticket to disclose the **total price** more prominently than
any other pricing information, where §464.1 defines total price as "the maximum total of all fees or
charges a consumer must pay ... and any mandatory ancillary good or service", excluding only government
charges, shipping and optional ancillaries. Source: 90 FR 2166 (Jan 10, 2025), read from the eCFR text
of Part 464 in this pass. **MEASURED, class A for the regulation.** For any US deployment after that
date, the number a buyer sees *is* the all-in number, so the buyer-side ad valorem term is not a hidden
wedge in the data: it is the price. The organizer's fee stack is then a pure deduction from it.

### 1.2 Definitions

One event, tiers `k = 1..K`. Units offered in tier `k`: `N_k` (`totalSupply`), total `Q = Σ N_k`.
Decision vector `p = (p_1, …, p_K)`, the primary price per unit in tier `k`, in lamports.

Price stack, per unit, all in lamports or rates:

| Symbol | Meaning | Sign / range | Where it comes from |
|---|---|---|---|
| `φ_k` | organizer-side ad valorem fee rate | `[0,1)` | configuration; not in contract |
| `f_k` | organizer-side per-unit fee | `≥ 0` | configuration; not in contract |
| `β_k` | buyer-side ad valorem fee rate | `≥ 0` | configuration; `0` in the US post-2025 (§1.1) |
| `b_k` | buyer-side per-unit fee | `≥ 0` | configuration; `0` in the US post-2025 |
| `a_k` | ancillary margin per attendee (concessions, parking, merch, sponsor bonus) | `≥ 0` | organizer's own accounts |
| `u_k` | cost of an offered-but-unsold unit | `≥ 0` | organizer's own accounts; §1.4 |
| `ρ` | organizer's royalty on resale turnover | `[0,1]` | configuration; not in contract |
| `c_k` | resale ceiling in bps over face, as a decimal: `resalePriceCapBps/10000`, `null → ∞` | `≥ 0` | contract |

The buyer's all-in cost is `P_k = p_k(1+β_k) + b_k`. The organizer's net receipt per unit sold is
`m_k(p_k) = (1−φ_k) p_k − f_k + a_k`.

Demand is uncertain and realized after the price is set. Let `D_k(p, ξ)` be the number of units
demanded in tier `k` at price vector `p` under state `ξ`, with `ξ` drawn from a distribution known up
to parameters. Units sold are `S_k = min(D_k, N_k)`: the venue cannot sell more than it has. The
per-offered-unit sale probability is

```
q_k(p) = E[ S_k ] / N_k  =  E[ min( D_k(p,ξ), N_k ) ] / N_k .
```

`q_k` is the object the engine reports as "probability this ticket sells", and it is the *truncated*
demand, not demand. That distinction does work in §5.

### 1.3 The objective

Expected net economic value to the organizer, over the ticket population of one event:

```
Π(p)  =  Σ_k  N_k [ q_k(p) · ( m_k(p_k) + u_k )  −  u_k ]  +  ρ · E[ T(p) ]  −  F          (O)
```

where `T` is resale turnover in lamports (sum of resale prices that clear), `F` fixed cost.

Assumptions used in writing (O), stated as part of the derivation:

- **A1.** The organizer is paid per unit sold, at the time of sale, and there is no settlement lag or
  default. If a lag `Δ` exists, it contributes a discount factor `e^{-rΔ}` multiplying the whole
  objective, which is neutral for `argmax` because it multiplies every candidate price equally. It
  affects the reported level only. [C]
- **A2.** No refunds or chargebacks. If tickets are refundable with probability `r`, then
  `m_k` becomes `(1−r) m_k − r·(refund cost)`; that is an additive per-unit term and therefore behaves
  like `−f`. §2.3 covers it. [C]
- **A3.** The resale royalty term is second order and is bounded, not estimated, in §1.5.
- **A4.** Cross-event demand effects are absent from (O) by construction, i.e. the engine prices one
  event at a time. §3.4 states when that is wrong and what it would take.
- **A5.** All quantities are expectations, so (O) is risk-neutral. §4 replaces it with a risk-adjusted
  functional.

(O) is the answer to "expected net economic value over the ticket population": `N_k q_k` is expected
units sold, `m_k + u_k` is what a sale is worth *relative to the empty seat it replaces*, and `−u_k` is
the baseline cost of every offered seat. Written that way, the empty-seat cost cannot be dropped
silently: it is the only term that makes the objective non-degenerate (see §2.4, case (iii)).

The per-ticket number an organizer reads is `Π(p)/Q`, net of the fee stack.

### 1.4 Which terms are estimable, which are configuration, which vanish

| Term | Status today | Class | What would change it |
|---|---|---|---|
| `q_k(p)`, the sale probability | **Not identified as a function of price.** Unconditional intensity is identified (01-b §4.3). | B/C | The four listing fields (D3); or a price experiment (§3.6) |
| `D_k` level | **Not identified.** Primary sell-out censors it; the ledger carries no bids (01-b T4b). | B | Primary inventory time series; bid-side data |
| `m_k` fee stack `(φ, f, β, b)` | **Not observable.** Parameter. | — | Settlement fields (§2.6) |
| `a_k` ancillary margin | Not in any platform field. Organizer's accounts. Parameter. | — | Organizer supplies it |
| `u_k` empty-seat cost | Not in any platform field. Parameter, and see the four components below. | D | Organizer supplies it |
| `ρ·E[T]` resale royalty | Not observable; bounded in §1.5 | C for the bound | `resaleRoyaltyBps` + `royaltyLamports` |
| `F` fixed cost | Sunk. **Vanishes from `argmax`.** | C | — |
| Resale-margin capture term | **Vanishes.** No instrument, and redundant under a proportional cap (§2.5). | C | An absolute (not proportional) cap, or a resale path in the product |
| Discounting, settlement lag | **Vanishes from `argmax`** (A1). | C | A price-dependent settlement term |
| Resale listing / ask decisions | **Vanish.** No listing path in the product (§1.1). | — | — |

`u_k` needs decomposing because three of its four components are real and one is a trap:

1. **Sunk production cost of the seat.** Zero. It is not a cost of leaving a seat empty; it is paid
   either way. Including it as `u` is the commonest error in this calculation. [C]
2. **Foregone ancillary per empty seat.** Real and positive, equal to `a_k`. Note the asymmetry: a sold
   seat yields `a_k` and an empty one yields nothing, and (O) already carries that through
   `m_k + u_k − u_k`. Adding `a_k` to `u_k` as well would double count. The correct statement is that
   `u_k` is *everything other than* the ancillary already inside `m_k`. [C]
3. **Sponsor, attendance and venue obligations.** Real, positive, event-specific, and usually a step
   function (a bonus at a sell-out) rather than a per-seat line. Approximating a step as linear in
   unsold units is a modelling choice that should be reported. [D]
4. **Strategic value of a sell-out.** Real but unmeasurable here: a full house raises future demand for
   the same promoter. It belongs in `u_k` and it cannot be estimated from this data. Flag it. [D]

### 1.5 The resale royalty bound, and why the objective needs no capture rate

`ρ·E[T]` is the only path by which secondary-market money reaches the organizer as money rather than as
willingness-to-pay. It is bounded by measurement, not by assumption. Leslie & Sorensen's 56-concert
sample yields total resale profit "slightly over $1.17 million ... equivalent to 1.4% of the total
primary market revenue for these events", against a 41% mean markup. **MEASURED, class A**, read from
the paper in this pass. So even a royalty that captured 100% of the resale *spread* would add about
1.4% of primary revenue on the most resale-active sample in the literature, and a realistic `ρ` captures
a fraction of the price rather than the spread. The term is retained in (O) for completeness and
carries a bound, not an estimate.

The term that should *not* appear is a "share of resale margin the organizer can capture through
pricing". §2.5 proves why: under a cap defined in basis points over face, the ceiling moves with the
decision, so there is nothing left over to capture by a separate mechanism.

---

## 2. The fee model, symbolically

### 2.1 Statement

We want the first-order condition for the single-tier problem, that is (O) with `K = 1`, `N` units,
price `p`, buyer's all-in cost `P = p(1+β) + b`, organizer's net `m = (1−φ)p − f + a`, empty-seat cost
`u`. Drop the tier subscript.

```
Π(p) = N [ q(P) · ( m(p) + u ) − u ]
```

### 2.2 Derivation of the first-order condition

Differentiate with respect to the decision `p`, remembering `P = p(1+β)+b` so `dP/dp = 1+β` and
`dq/dp = q'(P)(1+β)`:

```
Π'(p)/N = q'(P)(1+β)( m + u ) + q(P) · (1−φ)  =  0 .
```

Define the own-price elasticity of the *truncated* demand, `ε(P) = −P q'(P)/q(P) > 0`. Substituting
`q'(P) = −ε q/P` and dividing by `q`:

```
ε(P) · (1+β) · ( m + u )  =  (1−φ) P .                                              (FOC-1)
```

### 2.3 The collapse: one scalar replaces the whole fee stack

Substitute `p = (P−b)/(1+β)` into `m+u`:

```
(1+β)( m + u )  =  (1−φ)(P − b)  +  (1+β)( a + u − f ) .
```

Put that into (FOC-1), divide numerator and denominator by `(1−φ)`, and define

```
        c**  ≡  b  +  (1+β)( f − a − u ) / (1−φ)                                    (WEDGE)
```

Then (FOC-1) is exactly

```
        ( P − c** ) / P  =  1 / ε(P)        ,        equivalently   P = c** · ε /( ε − 1 ).   (FOC-2)
```

**Result.** For the static one-price problem, the entire fee stack `(φ, β, f, b)`, the ancillary `a` and
the empty-seat cost `u` enter the recommended **all-in** price through the single scalar `c**`. Every
other feature of the stack changes the reported profit level and not the recommendation. [C, ASSERTED,
and it is exact algebra, not an approximation, for any demand function `q(P)`]

Four consequences, each of which is a different answer to a question the programme asks:

**(i) Ad valorem fees are neutral for the optimum.** Put `f = a = u = b = 0`. Then `c** = 0` and
(FOC-2) reduces to `ε(P) = 1`, independent of `φ` and of `β`. A proportional fee rescales the objective
by a positive constant and cannot move its argmax. A buyer-side proportional fee is neutral in the
all-in price and only rescales the posted price by `1/(1+β)`. [C. Class B support: this is the standard
incidence result for proportional versus specific taxes under imperfect competition, Delipalla & Keen
1992, *Journal of Public Economics* 49:351–367.]

**(ii) Per-unit fees are not neutral, and they act as marginal cost.** With `f > 0` and nothing else,
`c** = f > 0` and (FOC-2) becomes `ε = P/(P−f) > 1`, which places the optimum at a point of *higher*
elasticity than the no-fee case. The per-unit fee is a marginal cost: the seller under-shifts the tax,
passing on less than the full amount, which is the standard monopoly result. The formal pass-through
object is `∂p*/∂f = ρ_pt` with `0 < ρ_pt < 1` under log-concave demand; Weyl & Fabinger (2013), *JPE*
121(3), doi:10.1086/670401, give the general incidence formula. [C, class B]

**(iii) The empty-seat cost has the opposite sign to the fee, and it is what makes the model
non-degenerate.** With `u > 0` only, `c** = −u/(1−φ) < 0`, so (FOC-2) reads `ε = P/(P+|c**|) < 1`: the
organizer accepts an inelastic price point in exchange for filling seats. With `f = a = u = 0` and no
capacity constraint there is *nothing* to trade off and the objective is revenue, whose optimum is the
unit-elastic point or, if demand is elastic everywhere, a corner. So `u` and `a` are not refinements.
Drop them and the model has no interior optimum on a sell-out event.

**(iv) Refunds and chargebacks are a per-unit term.** Under A2, let the refund rate be `r` and the refund
amount the price. Then a sold unit yields the price with probability `1−r` and a refund obligation with
probability `r`, so the effective deduction is `r·(refunded price)` per unit, which enters exactly like
`f` and therefore shifts the optimum up. It also raises the variance of revenue, which is §4's problem
and not §2's. [C]

### 2.4 The three cases the engine must handle, and the degeneracy

From (FOC-2), with `q(P) = A P^{-η}` (constant elasticity, used only to read the comparative statics):

| Case | Condition | Optimum |
|---|---|---|
| (i) Interior | `c** > 0`, `η > 1` | `P* = c** η/(η−1)` |
| (ii) Sell-through boundary | `c** ≤ 0`, or `η ≤ 1`, or the interior `P*` is below the price at which the house fills | `P*` = the highest all-in price at which expected sell-through still meets the organizer's floor |
| (iii) Degenerate | `q = 1` over the candidate range and `c** = 0` | `Π` is strictly increasing in `p`; keep raising until (ii). No maximum exists. |

Case (iii) is not a curiosity. It is the description of a sold-out event with no per-unit fee, and
Leslie & Sorensen's sample has mean capacity utilisation **0.99** across 56 events. **MEASURED, class A,
read from the paper's Table 1 in this pass.** For that kind of event the Lerner term is empty and the
answer is entirely a boundary question.

Because the objective is not guaranteed unimodal, the implementation rule is: **maximise `Π` on a price
grid, and use (FOC-2) only to interpret and to compute directions.** Never invert `η` to get a price and
report it.

### 2.5 The cap, and what it does and does not constrain

The contract's ceiling is `P̄ = p(1+c)` in lamports, because the cap is bps over face and face is `p`.
Three results follow, and they are the reason the objective above has no capture term.

**(a) Scale invariance.** For any `p`, the feasible resale band is `[p, p(1+c)]`. The band translates
with the decision. The seller's problem is therefore *where to sit in the willingness-to-pay
distribution*, not *how much of the ceiling to allow*. [C, ASSERTED. This is 01-b §4.5(ii) restated; the
dependency is stated because the argument is used downstream.]

**(b) A proportional cap is not a constraint on the organizer.** Suppose the organizer raises `p` by a
factor `λ`. The ceiling becomes `λp(1+c)`, so the reseller can still resell at the same proportional
markup. Nothing about the cap stops the organizer from raising the price; the only things that do are
the demand curve (sell-through falls) and the organizer's uncertainty about it. The cap binds the
*reseller*, not the organizer. [C, ASSERTED]

**(c) The resale market does not add a separate cross-price term to the organizer's problem.** The
buyer's outside option, waiting to buy on resale, has a price no higher than `p(1+c)` plus fees: it is a
function of `p`, not an independent price. So substitution between primary and resale is already inside
the primary demand curve, and the elasticity the objective needs is the *residual* one. §3.1 says which
elasticity that is and §3.5 what breaks it. [C, ASSERTED]

Result (c) is scope-limited and I state the limit: it holds **because** the cap is proportional. A
fixed-absolute cap, such as a nominal dollar ceiling, would break all three and force an extra term into
(O) equal to the shadow value of the rationed quantity behind the ceiling. If the operator ever changes
the definition, this section is void.

### 2.6 What a settlement field would have to contain, and in what order

(WEDGE) says the fee term stops being a parameter as soon as `c**(p)` is known as a function, i.e. as
soon as two numbers per settled sale are recorded. Listed in descending value per field:

| Rank | Field | What it buys | Why it is ranked here |
|---|---|---|---|
| 1 | `netToOrganizerLamports` on every settled primary sale, beside `priceLamports` | The whole organizer-side stack `(φ, f)` as a function of price, and the level of `Π` | One number per sale turns (WEDGE) from assumed to measured and removes the largest unquantified term in the report |
| 2 | `buyerTotalLamports` on the same row (or confirmation that `priceLamports` is already total under 16 CFR 464) | The buyer-side stack `(β, b)`, and whether `P ≠ p` at all | Without it, `c**` is only half identified; with it, `c**` is identified exactly |
| 3 | `perTicketFeeLamports` broken out from `feeBps` | Lets the engine separate `f` from `φ`, which matters because only `f` moves the price | Cheaper than 1–2 and buys most of the *interpretation*, not the number |
| 4 | `resaleRoyaltyBps` and `royaltyLamports` per resale | The `ρ·E[T]` term | The only resale money channel; bounded at about 1.4% of primary revenue anyway |
| 5 | Refund/chargeback flag and amount per sale | The downside term for §4's risk functional | Not needed for the price, needed for the risk report |
| 6 | Settlement timestamp | Discounting (A1) | Neutral for the optimum; cosmetic for the level |

Note the asymmetry, and it is the useful finding here. A field that records only the *percentage* fee
buys nothing for the price recommendation: by (i) of §2.3 it is neutral. The field that matters is the
one that reveals the **fixed per-ticket component**. That is the opposite of what a "fee field" is
usually specified to contain, and it is the single most actionable sentence in this report about Gap 4.

---

## 3. Elasticity

### 3.1 Which elasticity the objective needs

Three distinct objects, routinely conflated:

1. **`ε_own`**: elasticity of the truncated demand for this event's ticket with respect to its own
   all-in price. This is `ε` in (FOC-2). It is the only one that enters the price recommendation
   directly.
2. **`ε_x`**: cross-price elasticity with respect to competing events (01-d's V8). Positive for
   substitutes. It shifts `q` and therefore `p*`, but it is a state input, not a structural parameter of
   the recommendation.
3. **`ε_resale`**: cross-price elasticity with respect to the resale market for the *same* event. §2.5(c)
   argues it is already inside `ε_own` when the cap is proportional.

Because the objective prices *truncated* demand, `ε_own ≤ ε_D` whenever capacity truncation is active,
with equality only when the venue never fills. The engine's `ε` is therefore smaller than the demand
elasticity, and using `ε_D` in (FOC-2) would understate the recommended price. One line, easy to get
wrong. [C]

### 3.2 What the published record says, with market and sample on every number

| Source | Market and sample | What it says | Tag / class |
|---|---|---|---|
| Leslie & Sorensen 2014, *REStud* 81(1):266–300 | 56 rock concerts, summer 2004, US; 1,034,353 primary sales; all eBay/StubHub resales | Mean markup **41%** over face; **25%** of resold tickets above +67%; **26%** below face; resale profit **$1.17m ≈ 1.4%** of primary revenue; mean price levels **2.71**, max **4**; mean capacity utilisation **0.99** | **MEASURED**, A |
| Leslie & Sorensen 2014, counterfactual | same | Repricing the top **10%** of seats at the median observed resale price for those seats raises primary revenue **3.4%** (≈ **$27,000** per event) | **MEASURED**, A, but it is a *model simulation*, not an observed adoption |
| Courty & Pagliero 2012, *REStat* 94(1):359–369 | **21,120** North-American concerts, 2007 | Using multiple price levels raises revenue by about **5%** on average, coefficient stable under fixed effects | **MEASURED**, A |
| Courty & Pagliero 2012, same | same | **56%** of concerts offer two price categories, **25%** one, **15%** three, **4%** four | **MEASURED**, A |
| Noll 2013, "Endogeneity in attendance demand models", in *The Economics of Sport*, Edward Elgar, pp. 117–134 | survey of the sports attendance literature | "With few exceptions, the standard result is that the coefficient on price in the attendance demand equation is either positive or, if negative, so small that at current prices demand is inelastic", and the chapter's thesis is that this is an endogeneity artefact | **MEASURED** (quoted abstract), A for the characterisation, D for the causal reading |
| Ahn & Lee 2007, *Int. J. Sport Finance* 2(2):79–93 | MLB, multiple seasons | "for nearly thirty years, most of the empirical studies of sports-game attendance demand have failed to support" the prediction that a monopolist prices in the elastic range | **MEASURED** (quoted abstract), A for the characterisation |
| Ozhegova & Ozhegov 2018, *J. New Economic Association* 37(1):87–110 | Four seasons of ticket sales, Perm opera and ballet theatre, Russia; seat-level; censored quantile regression | "weak elasticity of demand"; ignoring hall capacity and seat quality biases the estimate | **MEASURED** (quoted abstract), A. **No magnitude in the abstract; I did not obtain the number** |
| Papies & van Heerde 2017, *J. Marketing* 81(4):67–87 | ≈400 artists, 6+ years, weekly concert and recorded-music revenue, Germany | Cross-format elasticity of recorded music on concert revenue is much stronger than the reverse | **MEASURED** (quoted abstract), A. **Direction only; no magnitude in the abstract** |
| DBT analytical note, 2025-12-19 (UK government) | 37.1m primary and 1.9m secondary tickets a year; £350m secondary market | A flow-accounting model. Assumes a **75%** markup (from the CMA's "more than 50%"), 80% of resale by touts, a **95%** and a **25%** volume reduction, **20%** displacement. Derives a face price of **£142** and an average resale price of **£269** inclusive of all fees. Contains **no demand elasticity at all**. | **MEASURED**, A (read in full) |

### 3.3 Why none of it transfers, stated plainly

Three reasons, each sufficient on its own.

1. **The observed price is not the marginal price.** In the one sample where both sides are visible,
   capacity utilisation is 0.99: the primary market clears at the ceiling in nearly every event, so the
   primary price is infra-marginal and the *marginal* price is the resale price. An elasticity
   estimated from primary quantities therefore measures a region where `∂q/∂p ≈ 0` by construction.
   **MEASURED for the 0.99; ASSERTED for the inference, class C.**
2. **Price is chosen by the seller.** Every one of these markets has an administratively set price
   correlated with unobserved quality. Noll's chapter exists because the resulting coefficients come out
   wrong-signed or near zero. That is 01-b's Working (1927) identification problem, independently
   confirmed in a different literature: what a regression of quantity on price traces is the locus of
   intersections of supply and demand, not demand.
3. **The cap changes the object.** No study I found, in this pass or in 01-b §4.5, estimates demand
   under a resale *cap*. The regulatory literature (NSW, Ireland, UK) models caps with assumed
   displacement, not with estimated elasticities. So the one structural feature of our market is the one
   the evidence base is silent on. **ASSERTED (a negative search result).** I searched OpenAlex
   title-and-abstract indexes for elasticity × concert × ticket combinations and read every abstract
   that surfaced; the list in §3.2 is what exists at the ticket level.

**How much transfers: none of it, as a number. All of it, as a sign and a shape.** The sign is that
demand at observed primary prices is inelastic (so the organizer is on the left of the revenue peak and
should raise price); the shape is that the response is heterogeneous across seats and events, which is
why Courty & Pagliero find 5% in tiering rather than in level. Any engine that hard-codes an elasticity
from this table is fabricating a parameter.

### 3.4 What the engine can do about elasticity today

Three options, in order of honesty:

1. **Parameterise it and publish the sensitivity.** Take `η` as configuration, solve (FOC-2), and report
   `∂p*/∂η` (sign in §5) and the value gap across the grid. This is what D4 already decided for fees
   and it is the same discipline.
2. **Bound it, using the monotone comparative statics.** The literature supports one bound: demand is
   inelastic at observed prices, so `ε ≤ 1` in the neighbourhood of the current price. Combined with
   (FOC-2), `ε ≤ 1` implies the current price is left of the optimum whenever `c** ≥ 0`, so the
   recommendation is "raise", with the size set by the boundary. That is a defensible, evidence-backed
   statement the engine can make *today*, and it is the source of the reportable claim in §6.
3. **Report the boundary rule as the recommendation when `c** ≤ 0` or `η` is absent.** This is the
   default. It is the answer for sold-out events and it uses only data the platform has.

What the engine must **not** do: fit `q(p)` on observed sales and call it the sale-probability curve.
01-b §4.3 already says why (no ask on the risk set), and §3.2 above shows that the published
literature's own attempts at this in sports produced coefficients attributed to endogeneity. This is the
failure mode that will look like it worked.

### 3.5 Cross-price effects, and the two that matter

- **Competing events.** `ε_x > 0` and it is the cleanest instrument-adjacent variable in 01-d's registry
  (V8), because another promoter's routing is not caused by our price. Effect on the optimum: a
  substitute's price rising raises `q` at every `p` and therefore raises `p*`. Not identified here
  (no competing-event data in the contract), so it enters as a scenario, not an estimate.
- **The resale market.** Under a proportional cap, §2.5(c): already inside `ε_own`. Under an absolute
  cap it would need its own term and its own elasticity, and I record that as the condition under which
  this simplification fails.

### 3.6 The minimum experiment that identifies `ε_own`

One design, and it is cheap because the schema already carries the instrument.

**Design.** Randomise the *face value* of a tier across a set of otherwise comparable events, or
randomise the *ratio* of two tiers' face values within an event while holding total supply fixed.
Observe sell-through at a fixed horizon before the event (`issuedCount/totalSupply` at `t`). Estimate
the elasticity of `ln(sell-through)` on `ln(price)` with event fixed effects and, in the within-event
arm, with tier fixed effects. The within-event arm identifies the substitution elasticity between own
tiers, which is the parameter multi-tier pricing needs and which nothing else can supply.

Three reasons this design and not another:

- It is the only one that moves price exogenously. Every passive field (the listing panel of D3) buys
  the sale *hazard* given an ask; it does not buy the response to a price the organizer chose.
- It is legal and cheap: the organizer sets prices anyway, and randomising across events is invisible to
  a buyer.
- Because the cap is proportional, randomising `p` randomises the resale ceiling too, so the same
  experiment identifies the cap's effect on demand as a free by-product. [C]

**Sizing, as a formula and not a number, because it is a money question.** With `G` events per arm and
sell-through as a proportion, the variance of the arm mean is `[σ²_between + σ²_within/N̄]/G`. To detect
a proportional change `δ` in sell-through you need `G ≈ 2(z_{1−α/2}+z_{1−β})² CV²/δ²` events per arm,
where `CV` is the coefficient of variation of event-level sell-through. `CV` is not in this dataset and I
will not guess it. The operator can read it off the first twenty events, and then the number of events
is given by the formula and the calendar. What the experiment costs in revenue is a decision for him.

---

## 4. The optimum under uncertainty

### 4.1 Random demand and the truncation term

Write `D_k(p,ξ) = d_k(p)·ξ` with `E[ξ]=1`, `sd(ξ)=σ`. Then

```
q_k(p) = E[min(d_k(p)ξ, N_k)]/N_k = (d_k/N_k) · E[min(ξ, N_k/d_k)]
```

and `E[min(ξ, m)] ≤ min(E[ξ], m)` with strict inequality whenever `ξ` straddles `m`. That inequality is
the whole of §4. So uncertainty *reduces* expected sell-through at every price, and it reduces it most
where the venue is near to filling. [C, Jensen]

### 4.2 The risk-neutral rule

```
p*  ∈  argmax_{p ∈ 𝒫}  Π(p)          with  𝒫 = { p : q_k(p) ≥ q_min } ,               (RN)
```

`q_min` is the organizer's sell-through floor, supplied as configuration. Solve on a grid. `Π` is not
guaranteed unimodal (§2.4), so a grid search is the honest implementation and it costs `O(G·M)` for `G`
candidate prices and `M` demand scenarios: microseconds in stdlib Python for a realistic `G` of a few
hundred.

### 4.3 The risk-adjusted alternative, and which one is implementable

Two candidates from the programme, and a verdict on each.

**Conditional value at risk, mean-CVaR:**

```
max_p  (1−λ) E[Π(p)]  +  λ CVaR_α(Π(p)),      CVaR_α(X) = max_v { v − α^{-1} E[(v−X)^+] } .
```

CVaR is coherent (Artzner, Delbaen, Eber & Heath 1999, *Mathematical Finance* 9:203–228) and the
Rockafellar–Uryasev (2000, *Journal of Risk* 2:21–41) representation makes it a linear program in `v`.
**For a finite scenario set with equal probabilities it reduces to a sort plus a partial mean:**
`CVaR_α = −(1/k)Σ` of the `k = ⌈αM⌉` worst outcomes. `O(M log M)` per candidate price, pure stdlib, no
matrix algebra, no solver. **Implementable today under D2.**

**Mean-variance:** `max_p E[Π(p)] − (γ/2)Var[Π(p)]`. Also computable from the same scenarios in stdlib.
Two reasons not to use it, and neither is implementability. It penalises upside as well as downside,
which is the wrong attitude for a pricing decision whose whole point is to move the upper quantiles. And
its scale grows with `N²`, so `γ` has to be re-tuned per event size, which makes it an unportable
parameter in a tool that runs across events selling 3,169 to 34,844 primary tickets (Leslie & Sorensen's
sample range; **MEASURED**, A). **Implementable, not recommended.**

**Not implementable in stdlib, and worth naming so nobody tries:** CVaR over a joint multi-tier price
vector with capacity coupling and a Wasserstein ambiguity set, which is a convex program needing a
solver; and exact VaR optimisation, which is non-convex and needs enumeration or a MILP. Both are
documented as specified-not-implemented under D2.

**Choice.** Report `(RN)` as the recommendation and `λ=0.5, α=0.1` mean-CVaR as the risk-adjusted
alternative, both on the same scenario set, so the organizer sees the price and the price under
downside control side by side. `λ` and `α` are configuration with defaults, and the report names them.

### 4.4 Static versus multi-tier versus dynamic

**Multi-tier.** The objective becomes the `K`-tier version of (O) with a demand system
`D_k(P_1,…,P_K)`. With substitute tiers, `∂q_l/∂p_k > 0` for `l ≠ k`, so

```
∂Π/∂p_k  =  N_k[ (∂q_k/∂p_k)(m_k+u_k) + q_k m'_k ]  +  Σ_{l≠k} N_l (∂q_l/∂p_k)(m_l+u_l)
```

and the cross term is positive, so **the multi-tier optimum prices every tier above the separable
optimum**: the monopolist internalises the cannibalisation it would otherwise impose on itself. [C.
Standard multiproduct result; class B support for the direction in Dana 1998, *JPE* 106:395–422, where
demand uncertainty alone generates intertemporal price discrimination with no cost differences.]

The measured size of the prize: **5%** of revenue on 21,120 concerts [A, MEASURED], and **3.4%** (≈$27k
per event) from adding one price level to the top decile of a 56-concert sample [A, MEASURED, model
counterfactual]. Both single-digit. That is the number that should discipline any enthusiasm here.

**Conditions under which a single static price beats a multi-tier policy.** Four, and the fourth is
decisive in this product:

1. **Small `N_k`.** A tier needs enough units for its price to be a price rather than a lottery, and
   units below the granularity of the price grid cannot be separated.
2. **No observable heterogeneity axis.** Gap 3: the contract carries `tierId` but no section, row or
   seat. Within-tier heterogeneity is unpricable, so an extra tier buys nothing inside an existing tier.
   This is the strongest argument for keeping the tier structure the platform already has and moving
   only the level, which is a **one-parameter** move and needs one unknown (`ε_own`) instead of
   `K + K(K−1)/2` unknowns.
3. **Menu cost and fairness.** Each additional price level is a visible act; the US all-in rule (§1.1)
   makes every price level comparable to a buyer in a way it was not before May 2025, which raises the
   salience of a tier structure. Direction stated, magnitude unknown. [D]
4. **The product cannot reprice.** There is no price-mutation endpoint (§1.1). A *dynamic* policy is not
   a modelling choice in this product, it is a schema change. State it that way in the report and let
   the operator decide. Under that constraint the comparison is static-single versus static-multi, and
   multi wins on the measured evidence whenever tiers already exist.

**Dynamic, if the product ever allows it.** The theoretical case is strong (Gallego & van Ryzin 1994,
*Management Science* 40:999–1020: optimal dynamic pricing of finite inventory over a finite horizon with
stochastic demand) and the empirical shape is known (Sweeting 2012: prices fall toward the event because
the opportunity cost of holding decays). The condition under which it nonetheless loses: when the
repricing signal is noisy relative to the variation in the state. With no listing panel and no
sell-through history (§1.1), the engine has no state variable to condition a repricing on, so the value
of a dynamic policy is not measurable here and must not be claimed. [D]

---

## 5. The sensitivity that matters

Derived from (WEDGE) and (FOC-2). No numbers are invented; the signs and their reasons are given, and
the arithmetic in the last table is exact from the formula.

| Parameter | Sign of `∂p*/∂·` | Reason | Which field would supply it |
|---|---|---|---|
| `η`, own-price elasticity | **negative**, for `c** > 0` | `p* = c**η/(η−1)`, so `∂p*/∂η = −c**/(η−1)² < 0`. Higher elasticity means less market power means a lower markup over the wedge | A price experiment (§3.6). Nothing else |
| `f`, per-unit fee | **positive** | Adds to `c**` as marginal cost; pass-through is partial under log-concave demand | Settlement field 1 or 3 (§2.6) |
| `φ`, organizer ad valorem | **zero** for the all-in optimum; negative on `Π` | Multiplicative wedge, cancels in (FOC-2) for the price | Settlement field 1 |
| `β`, buyer ad valorem | **zero** for the all-in optimum; `−p/(1+β)` on the *posted* price | Pure rescaling of the base; the buyer's total is invariant | Nothing: post-2025 US the posted price already is the total (§1.1) |
| `b`, buyer per-unit fee | **positive**, one-for-one on the all-in price | Enters `c**` additively | Settlement field 2 |
| `a`, ancillary margin | **negative** | Lowers `c**`: a filled seat is worth more than the ticket, so buy volume with a lower price | Organizer's accounts |
| `u`, empty-seat cost | **negative** | Same channel, larger effect: it is the cost that makes the organizer trade margin for sell-through | Organizer's accounts |
| `c`, resale cap (bps) | **zero** directly; **positive** if the resale option has value to the buyer | §2.5(b): proportional caps do not constrain the organizer. The second channel is WTP: a buyer who may resell is willing to pay more, and a higher cap raises that option's value | Contract field; the second channel is class D |
| `σ`, demand uncertainty | **ambiguous** | Two opposing effects, both derived in §5.1 below | Nothing passive; a forecast-error series or an ensemble spread |
| `q_min`, sell-through floor | **negative** | A tighter floor forces a lower price | Organizer policy |

### 5.1 The two opposing effects of demand uncertainty, derived

**(a) Truncation pushes the optimum up.** Adding uncertainty lowers `q` and flattens `q'`: truncation
at `N` makes the quantity response small exactly where the venue is near to filling. At the
no-uncertainty optimum `p₀`, the derivative of `Π` under uncertainty is

```
Π'_σ(p₀) = N[ q'_σ(m+u) + q_σ m' ]  >  N[ q'_0(m+u) + q_0 m' ] = 0
```

because `q'_σ > q'_0` (less negative) and the comparison is against zero. So `p*` rises. The economic
reading: when the house will fill anyway, the marginal unit costs nothing to price up. [C]

**(b) Downside-risk aversion pushes the optimum down, conditionally.** In the adverse demand state,
revenue is `p·D(p)` and `∂(pD)/∂p = D(1−ε_D)`. So a CVaR penalty on the bad tail lowers `p*` **exactly
when the adverse-state demand is elastic** (`ε_D > 1`), and has no effect when it is inelastic. This is a
conditional result and it is the honest form: the sign of the risk correction depends on the elasticity
in the state that hurts. [C]

Which dominates is an empirical question this programme cannot answer. Reported honestly: the risk
functional changes the recommendation in the elastic-adverse-state case, and the report says so rather
than pretending the correction has one sign.

### 5.2 Why the sensitivity lands on the boundary, and what that implies

The quantity that governs the interior optimum is the ratio `c**/(η−1)²`. For inelastic demand (`η` near
1) this is large, not small, so `p*` is *very* sensitive to `η` near unity, which is the opposite of
reassuring: it says an elasticity near 1 makes the answer depend almost entirely on a parameter we do
not have. And for `c**` small and positive the interior price collapses below the fill price, at which
point the boundary governs. Both roads lead to the same conclusion: **the recommendation is a boundary
recommendation, and the elasticity's role is to tell you how far above the boundary you can go.**

Arithmetic from `p*/c** = η/(η−1)`, exact, no data:

| `η` | 1.2 | 1.5 | 2.0 | 3.0 | 5.0 |
|---|---|---|---|---|---|
| `p*/c**` | 6.00 | 3.00 | 2.00 | 1.50 | 1.25 |

Read it this way: if the effective per-ticket wedge is 5% of face and `η = 1.5`, the interior optimum is
`3 × 5% = 15%` of face. That is far below any observed face value, so the interior condition is
infeasible and the boundary rule applies. The table is a diagnostic on the model, not on a market.

---

## 6. What the engine reports to an organizer

Exact wording, to be produced by the engine with the numbers substituted. No hedging, and every
assumption named.

---

**Recommended primary price: {P} SOL per ticket in {tier name}.** That is {x}% above your current
{y} SOL.

**Expected net value at that price:** {E} SOL for the tier, {E/Q} SOL per ticket, after your fee stack.
Across the range we considered this moves by {d}%.

**Range: {P_lo} to {P_hi} SOL. We would not argue with any price in that range.**

**What drives it, in order:**

1. The price this tier's tickets actually resell for: median {m} SOL over {n} sales, which is the only
   measurement of what buyers will pay. If the resale record is thin we say so and widen the range.
2. Your sell-through at the current price: {s}% with {d} days to go. That is a measurement of whether
   the house fills, and it sets the floor under the recommendation.
3. The effective per-ticket cost we assumed: {c} SOL. This is your platform fee, payment cost, royalty,
   concessions margin and the cost of an empty seat, combined. We assume {c} because your settlement
   data is not connected. If the true figure is higher, the recommended price is higher; if you make
   more per attendee on concessions, it is lower.

**Made with these assumptions, which you can change:** own-price elasticity {η}; sell-through floor
{q_min}; resale cap {c} basis points over face; ancillary per attendee {a} SOL; empty-seat cost {u} SOL;
risk setting {λ, α}.

**The recommendation is wrong if any of these is true:**

- The resale prices in the record are capped and leaked off-ledger (side payments, wallet handoff,
  bundles). Then the true willingness to pay is higher than the record shows and the price should be
  higher still. We cannot see the leak.
- Demand for this event is elastic. Our evidence says demand at administratively set prices is
  inelastic; if this event is the exception, the recommended price is too high.
- A competing event was announced after your on-sale. Nothing in this data sees it.
- You are selling to resellers rather than attendees. Then the demand you face is the resellers', which
  is a different curve with a different elasticity and we do not model it.
- The seat quality inside this tier varies more than the tier itself. We only know the tier, not the
  row.

---

**With no elasticity estimate**, which is the default until the experiment in §3.6 runs, the report
replaces the first two lines with:

---

**Recommended primary price: {P} SOL per ticket. This is a bound, not an optimum.** It is the highest
price at which this event still fills on the evidence available: {s}% of the tier sold at {y} SOL with
{d} days to go, and resale clearing at {m} SOL. Above {P} we cannot show that the house still fills, and
we will not recommend a price we cannot defend. **What would change it:** a two-arm price test across
comparable events, which we can design for you and which needs {G} events per arm. Until then, treat
{P} as the floor of the recommendation and {P_hi} as the point where the evidence runs out.

---

That last paragraph is the whole answer to "what does the engine say when it has no elasticity
estimate". It says what it knows, names the bound, and names the experiment. It does not invent a
number and it does not hedge.

---

## 7. Data requirements, in the order they would buy

1. **Settlement, two numbers per settled sale:** `netToOrganizerLamports` and `buyerTotalLamports`
   beside `priceLamports`. Converts `c**` from an assumption to a measurement and removes the largest
   unquantified term in every report. Highest value per field in this programme after D3's listing panel.
2. **The listing panel from D3** (`listPriceLamports`, `listedAt`, `delistedAt`, `delistReason`): converts
   the sale hazard from unidentifiable to a standard time-varying-covariate survival problem.
3. **A randomised face-value arm (§3.6).** Not a field. The only thing that identifies `ε_own`, and
   therefore the only route to an interior optimum rather than a bound. Cheap because the organizer sets
   prices anyway.
4. **Primary inventory time series:** on-sale time, sell-out time, holdback releases. Turns the
   sell-through boundary from one observation per tier into a booking curve, which is what makes the
   boundary rule precise instead of conservative.
5. **Tier price-ratio randomisation within events** (an arm of 3, not a separate request): the
   substitution elasticity between own tiers, which is the parameter multi-tier pricing needs. Nothing
   else supplies it.
6. **`resaleRoyaltyBps` and `royaltyLamports`:** the `ρ·E[T]` term. Low value; bounded at about 1.4% of
   primary revenue.
7. **Refund and chargeback flags:** the downside term in the risk functional. Needed for the risk
   report, not the price.

Note the ordering against Gap 4's own statement. Gap 4 said the fee field is needed because the
objective is net. That is right, but §2.3 sharpens *which* fee field: the percentage one buys nothing for
the price, and the fixed per-ticket one buys everything.

---

## 8. What would falsify this

Each of these is a test, not a caveat.

1. **The neutrality lemma (§2.3).** Falsified if, with settlement data, a change in the ad valorem rate
   that leaves the per-unit fee and the ancillary unchanged moves the organizer's chosen all-in price.
   The test needs a fee change across events with comparable demand. If it fails, the model is missing a
   term (most plausibly a fixed cost with a participation constraint, or a non-linear buyer response to
   a salient fee line).
2. **The proportional-cap result (§2.5).** Falsified if organizers systematically price at a level where
   `p(1+c)` equals an *external* anchor (a published face value, a competitor's price, a press-reported
   ceiling) rather than tracking the resale price. That would mean the cap is anchored to something other
   than `p` in practice, and the whole of §2.5 is void.
3. **The boundary-optimum claim (§2.4, §5.2).** Falsified if, with real settlement data and a real
   elasticity, `c** > 0` and the interior optimum falls strictly inside the feasible sell-through set
   *and* differs materially from the boundary price. Then the Lerner term matters and my conclusion that
   the answer is a boundary recommendation is wrong.
4. **The "inelastic at observed prices" premise (§3.3).** Falsified by a credible estimate of `ε_own > 1`
   at administratively set primary prices. Noll's chapter argues the existing estimates are artefacts, so
   a credible elastic estimate would overturn the literature's consensus, not just mine.
5. **The risk-direction results (§5.1).** Falsified if a CVaR-optimal price comes out *above* the
   risk-neutral price on realistic scenarios with an elastic adverse demand state. That would mean I have
   the sign of one of the two effects backwards, and the derivation is checkable in ten lines.
6. **The claim that no elasticity transfers (§3.3).** Falsified by any peer-reviewed estimate of
   own-price elasticity for primary-market live-event tickets under a resale price cap. I searched and
   did not find one; a single counterexample closes this and should be recorded in `F` if found.
7. **The claim that resale markup is a lower bound on willingness to pay.** Falsified by an uncapped
   event in the same dataset showing lower markups than a capped event at equal demand.

## 9. Limits of this report

- **No number in §3 came from this platform.** No real ledger exists (D1, `00-data-situation.md`). Every
  empirical figure is cited from a published source with its market and sample, and three of the seven
  are qualitative characterisations rather than magnitudes because the abstracts do not give magnitudes
  and I did not obtain full text.
- **I could not obtain full text for four sources.** Sweeting (2012) is cited from `01-a`'s reading, not
  mine. Ozhegova & Ozhegov (2018) and Papies & van Heerde (2017) are cited from their abstracts, which
  give direction and not magnitude. Noll (2013) is cited from its abstract. Anything marked MEASURED
  above is a sentence I read in this pass; anything marked ASSERTED is mine.
- **The Perm paper's number is missing** and it is the closest analogue to our problem (seat-level,
  capacity-censored, censored quantile regression). Its extraction is the highest-value single follow-up
  in this file: it would give one real `ε` for a ticketed venue with capacity censoring. I attempted
  extraction and the PDF's font encoding defeated my stdlib extractor.
- **`c**` can be negative and the model can recommend giving tickets away** (§2.3(iii)). That is
  economically correct when the empty-seat cost is high and demand is elastic, and it is commercially
  unacceptable. The engine must clamp at a policy minimum and say it clamped.
- **No class-A claim about caps appears here**, consistent with 01-b §4.5: the cap component is class B
  borrowed from the rent-control literature plus class C theory. §2.5 is class C.
- **The multi-tier results assume a demand system the engine does not have.** The positive
  cross-substitution result of §4.4 is class C. The 5% and 3.4% magnitudes are class A but from markets
  without a resale cap and without a proportional ceiling.

---

## Sources

Read in full or in relevant part during this pass (numbers quoted above are from these):

- **Leslie, P. & Sorensen, A. (2014).** Resale and rent-seeking: an application to ticket markets.
  *Review of Economic Studies* 81(1):266–300. doi:10.1093/restud/rdt033. Read from
  https://users.ssc.wisc.edu/~atsorensen/papers/resale.pdf (full text, this pass). Source of 41%, 25%,
  26%, $1.17m, 1.4%, 2.71 price levels, capacity utilisation 0.99, $27,000, and the 5% attribution to
  Courty & Pagliero.
- **Courty, P. & Pagliero, M. (2012).** The impact of price discrimination on revenue: evidence from the
  concert industry. *Review of Economics and Statistics* 94(1):359–369. doi:10.1162/rest_a_00179. Read
  from https://iris.unito.it/bitstream/2318/81966/1/Courty%20and%20Pagliero%202012.pdf (full text, this
  pass). Source of 5%, 21,120 concerts, and the 56/25/15/4 category split.
- **DBT (2025-12-19).** *Analytical note on government response to resale of live events tickets
  consultation.* GOV.UK. Read in full, this pass:
  https://www.gov.uk/government/publications/government-response-to-resale-of-live-events-tickets-consultation-analytical-note/analytical-note-on-government-response-to-resale-of-live-events-tickets-consultation
  Source of 37.1m, 1.9m, £350m, £269, £142, 75%, 80%, 95%, 25%, 20%, and the absence of any elasticity.
- **16 CFR Part 464**, Rule on Unfair or Deceptive Fees, source 90 FR 2166 (Jan 10, 2025), in force
  2025-05-12. Read from the eCFR text of Part 464, this pass (§464.1 "Total price", §464.2(a)).
  https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-464

Cited for theory or characterisation, metadata verified via Crossref/OpenAlex, statement quoted from the
abstract where quoted:

- **Delipalla, S. & Keen, M. (1992).** The comparison between ad valorem and specific taxation under
  imperfect competition. *Journal of Public Economics* 49(3):351–367. doi:10.1016/0047-2727(92)90073-O
- **Weyl, E. G. & Fabinger, M. (2013).** Pass-through as an economic tool: principles of incidence under
  imperfect competition. *Journal of Political Economy* 121(3). doi:10.1086/670401
- **Noll, R. G. (2013).** Endogeneity in attendance demand models. In *The Economics of Sport*, Edward
  Elgar, pp. 117–134. doi:10.4337/9781781002865.00016. Quoted from the abstract.
- **Ahn, S. C. & Lee, Y. H. (2007).** Lifecycle demand for Major League Baseball. *International Journal
  of Sport Finance* 2(2):79–93. doi:10.1177/155862350700200203. Quoted from the abstract.
- **Ozhegova, A. & Ozhegov, E. M. (2018).** Estimation of demand function for performing arts: empirical
  analysis. *Journal of the New Economic Association* 37(1):87–110. doi:10.31737/2221-2264-2018-37-1-4.
  Quoted from the abstract; magnitude not obtained.
- **Papies, D. & van Heerde, H. J. (2017).** The dynamic interplay between recorded music and live
  concerts. *Journal of Marketing* 81(4):67–87. doi:10.1509/jm.14.0473. Direction from the abstract.
- **Harris, M. & Raviv, A. (1981).** A theory of monopoly pricing schemes with demand uncertainty.
  *American Economic Review* 71(3):347–365. (AER/JSTOR record; not Crossref-indexed.)
- **Dana, J. D. Jr. (1998).** Advance-purchase discounts and price discrimination in competitive markets.
  *Journal of Political Economy* 106(2):395–422. doi:10.1086/250014
- **Gallego, G. & van Ryzin, G. (1994).** Optimal dynamic pricing of inventories with stochastic demand
  over finite horizons. *Management Science* 40(8):999–1020. doi:10.1287/mnsc.40.8.999
- **Artzner, P., Delbaen, F., Eber, J.-M. & Heath, D. (1999).** Coherent measures of risk.
  *Mathematical Finance* 9(3):203–228. doi:10.1111/1467-9965.00068
- **Rockafellar, R. T. & Uryasev, S. (2000).** Optimization of conditional value-at-risk. *Journal of
  Risk* 2(3):21–41. doi:10.21314/jor.2000.038

Depended on but not re-read in this pass (used exactly as recorded there):

- `records/findings/01-a-market-structure.md` §3–§6: NSW's 10% resale cap and its enforcement record; the
  CMA's "more than 50%" markup finding; Sweeting's price-decline magnitudes; the Bulow–Klemperer and
  Glaeser–Luttmer arguments on dissipated surplus; He & Lin on caps and seller exit.
- `records/findings/01-b-identifiability.md` §4.3 (T3), §4.4 (T4), §4.5 (T5): the non-identification of
  the price response, the primary sell-through demand bracket, the ad valorem neutrality observation, the
  scale-free band, and the absence of any peer-reviewed study of resale caps.
- `records/00-data-situation.md` §4 Gap 4; `records/F-decision-log.md` D1–D4.

**Could not establish:** any peer-reviewed estimate of own-price elasticity for primary-market live
tickets under a resale cap (searched OpenAlex title-and-abstract indexes across elasticity × concert ×
ticket × theatre × sports combinations, and read every abstract that surfaced); any measured fee
magnitude for primary ticketing from a primary source (the FTC rule text gives the definition of total
price and not a distribution of fee sizes, and the FTC's own press materials were not retrievable from
this host); and the point estimate in Ozhegova & Ozhegov (2018).

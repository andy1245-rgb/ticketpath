# Phase 1-A — Market structure and economic structure of live-event ticketing

**Status:** complete. **Last updated:** 2026-11-07T09:10Z. **Author:** Phase 1 subagent A.
**Scope:** RESEARCH-PROGRAM §3 Phase 1 domains 1 (market structure) and 2 (economic structure).
**Evidence classes** per §4.3. No number below comes from `lib/mock/`.

---

## What I concluded

The published record is decisive on one point and silent on another, and the silence is where we
live. Decisive: primary tickets are systematically priced below secondary clearing value, the gap is
real but modest once the whole market is measured (≈41% average markup on the ~5% of tickets that
resell, worth 1.4% of primary revenue in the one study that observes both sides), and secondary
prices near the event overwhelmingly **fall** — Sweeting's MLB sellers cut prices by 13/18/40% of
face value across successive relistings and by "40 percent or more" over the final month, because
unsold inventory is worthless at the deadline and the option value of waiting decays. "Hot events
rise" is not a counter-example in the data; it is the tail case where excess demand outlives supply,
and in the one concert dataset that measures it the path is near-flat with only "a modest uptick in
the last week". Our platform is the first observation set in this literature where every resale *is*
a settled transaction with a custody trail, which deletes the asking-versus-realised problem and
substitutes a harder one: prices are truncated by policy at `resalePriceCapBps`, and the compliance
behaviour a cap induces (side payments, wallet handoff, bundling) makes the recorded markup a
biased-down estimate of value exactly where value is highest. An estimator fitted to uncorrected
capped markups will under-price the best inventory. That, not forecasting, is the central structural
fact of this project.

---

## 1. Mechanism map

Primary and secondary are one market with two price-setting institutions: the primary seller has
monopoly-ish power over *allocation* but prices coarsely ("the maximum number of price levels for a
single event in our data is four, with most events offering tickets at only two", Leslie & Sorensen,
class A), while the secondary market prices finely with heterogeneous, often uninformed sellers.

| Channel | Who sets price | Inventory risk | Where the fees sit | Observable to us |
|---|---|---|---|---|
| Primary fixed-price (Ticketmaster/AXS/Eventbrite) | Organiser, per price level, coarsely | Organiser (unsold = 0 at doors) | Per-ticket + facility + order fees, per-unit and ad valorem, historically disclosed late | `faceValueLamports`, `tierId`, `totalSupply`/`issuedCount` snapshot |
| Primary dynamic / "platinum" / "in demand" (Ticketmaster 2010-11, MLB 2009-10) | Algorithm or pricing desk, revised as demand arrives | Organiser | Same stack, on the moving price | Not identifiable; price arrives as `faceValueLamports` |
| Registered-fan presale / ballot / queue (Verified Fan, priority, TM queue) | Organiser sets price; the queue allocates | Organiser | Registration free; queue is non-price rationing | `requiresVerifiedWallet`, `issuedToWallet` |
| Season-ticket and broker allocations | Club/venue contract; brokers buy blocks at or below face | Broker/distributor | Wholesale discount, embedded | Not visible |
| Resale marketplace, seller-set asks (StubHub, viagogo, SeatGeek, Vivid, TM/AXS Resale) | Individual seller; platform suggests | Seller | Two-sided: buyer + seller fee | `sale` ledger rows, `markupBps` |
| Capped resale (Twickets, TicketSwap, TM AU under NSW law, our `resalePriceCapBps`) | Policy sets the ceiling; seller prices at or below | Seller; platform carries enforcement risk | Platform fee capped so it cannot breach the cap | Ledger row ≤ cap; the shadow price is unrecorded |
| On-chain primary + resale (Get Protocol; Ticketmaster NFT pilots 2021-23) | Organiser primary; reseller secondary | Organiser primary, reseller secondary | Protocol/royalty fee inside the token transfer | By construction: issue/sale/transfer/redeem with price and counterparties |

Two facts about fees are absent from `lib/types.ts` and both matter. Fees on resale are *two-sided*,
so "the price" is ambiguous by 20-40% depending on the observed side — a larger measurement problem
than most of the modelling. And since 2025-05-12 US law requires the **total** price to be displayed
for live-event tickets (16 CFR Part 464, 90 FR 2166, class A for the regulation), which is a
structural break in every US series: pre-2025 quotes are pre-fee, post-2025 all-in. Pooling them
manufactures a one-off level shift that reads as a market move.

Regulatory direction of travel is uniform and relevant, because `resalePriceCapBps` is not an
idiosyncrasy: NSW has capped resale at original retail plus transaction costs, "up to a maximum 10%
of the original ticket price", since 2018-06-01 (penalties A$110,000/A$22,000; organisers may cancel
non-compliant tickets; Fair Trading cannot order refunds of the excess). Ireland has banned above-face
resale for designated events and venues since 2021-07-31. The UK announced on 2025-11-19 that resale
above "original cost plus unavoidable fees" will be illegal, with resale platform fees capped,
platforms given a duty to enforce, and penalties up to 10% of global turnover under the DMCC Act
2024. In the US the BOTS Act (2016) governs primary-market access, not price; the FTC fee rule is
live; and on 2026-04-15 an SDNY jury found Live Nation and Ticketmaster liable on all antitrust
counts, with remedies still before the court (secondary source, docket not read).

---

## 2. The empirical secondary price path

| Study | Market and sample | Finding, as stated | Class |
|---|---|---|---|
| Sweeting, *JPE* 120(6):1133-1172, 2012 | MLB 2007; 178,000+ eBay fixed-price listings, 113,186 in the structural sample; StubHub comparison | Prices "falling significantly as a game approaches, especially in the final month"; sellers "cut prices even more dramatically, by around 90% of face value in the month before the game"; average within-seller declines of 13%, 18%, 40% of face value across successive relistings; "40 percent or more" overall; dynamic pricing worth ≈16% of seller payoff | A |
| Sweeting, same | same | Demand near time-invariant while *opportunity cost* falls: declines of 18%, 19%, 68% of face value when a listing stays unsold to the next period; 77.2% of relisted tickets carry lower implied opportunity cost; ≈25% of final-period opportunity costs negative | A |
| Leslie & Sorensen, *RES* 81(1):266-300, 2014 | 56 rock concerts, summer 2004, 12 artists, 1,034,353 primary sales (Ticketmaster) + all eBay/StubHub resales | Resale averages 41% above face; 26% below face; conditional on seat quality prices "decline slightly as the event date approaches, with a modest uptick in the last week" | A |
| Shapiro & Drayer, *J. Sport Mgmt* 26(6):532, 2012 | SF Giants 2010, 12 games, 1,316 observations | Fixed primary < dynamic primary < secondary, all significantly different; time effect varies by market and seat | A (small) |
| Budish & Bhave, *AEJ:Micro* 15(1):142-170, 2023 | Ticketmaster primary auctions matched to eBay resale values | Auctions "substantially improved price discovery, roughly doubled performer revenues, and, on average, nearly eliminated the arbitrage profits" | A |
| Courty & Pagliero, *REStat* 94(1):359-369, 2012 | Concert industry, large sample | Multiple seating-category prices yield ≈5% more revenue than single-price; return rises with demand heterogeneity | A |
| Courty, *JEP* 17(2), 2003 | Theory + evidence review | Promoters cannot capture resale profits because demand is uncertain and waiting has option value | C |

The two regimes are real but asymmetric. The decline regime is the default and is mechanically
explained: finite horizon, zero salvage value, decaying option value, sellers who mostly cannot
attend (professionals set lower prices than amateurs, consistent with a lower value of being stuck
with inventory). The rise regime requires excess demand that survives to the door, and even then the
measured path is "a modest uptick in the last week", not a blow-off. What separates them is the state
of *remaining supply*, not calendar time: Sweeting's declines are in opportunity cost conditional on
a listing still being unsold, and Leslie & Sorensen's flat path is for events that had active resale
at all (their most active event: 17% of tickets resold). For estimation the time-to-event slope must
therefore be conditioned on a supply/demand state (fraction unsold, sell-through velocity, listings
relative to issue count), not estimated as a single function of days.

Magnitudes to carry forward: level ≈1.3-1.5× face on average for concerts, materially higher for the
best seats; dispersion huge (25% of resold tickets above +67%, 26% below face); total resale surplus
small relative to primary revenue (1.4%).

---

## 3. Caps: whether they bind, and what a binding cap does to the distribution

NSW's cap has been in force since 2018 with public platform enforcement, yet Fair Trading states a
buyer overcharged above 110% "may not get a refund of the difference" and that it has no power to
order refunds — ex post, weak enforcement, which is the condition under which a cap binds on paper
and leaks in practice. The UK's own cost-benefit model, published 2025-12-19, assumes the leak
quantitatively: a 20% displacement of tout volume to unregulated channels, a 95% reduction of tout
sales on regulated platforms and 25% off them. Those are assumptions (the note says so), but they are
the official prior: displacement, not disappearance.

A binding cap does three observationally distinct things.

1. **Left truncation.** No transaction above the cap is recorded, so `markupBps` is a censored draw
   and any mean or quantile from it is biased down by construction (class C).
2. **A mass point at the cap with rationing behind it.** The market clears by speed and allocation,
   not price: tickets at the cap sell fast and excess demand queues. The spike's height and the sale
   velocity at the cap measure excess demand, not value. He & Lin (*Marketing Science*, ~~2025~~ **2026**)
   **[CORRECTION 2026-11-07T14:00Z, R2-15 — dead year: Crossref for `10.1287/mksc.2023.0623` gives
   *Marketing Science* 45(3):515–533, issued 2026-05. See CORRECTION 3 at the end of this file.]** add the
   non-obvious corollary: a stringent cap can push high-price sellers out, reduce seller-side
   competition, and *raise* average transaction price (class C).
3. **Evasion that moves price off the rail.** Four channels: side payment (transfer at face on-chain,
   cash off-chain); wallet handoff (sell the key, no ledger row at all); bundling (ticket at face plus
   a priced ancillary); flight to unregulated channels (the UK's 20% assumption). Consequence: at the
   cap the recorded markup is a *lower bound*, with the bias largest where demand is strongest. This
   inverts the error — fit on observed markups and you conclude the hottest events are the *least*
   valuable.

Calibration for the unconstrained case: the CMA found "most tickets sold through the Parties'
platforms in 2019 had a mark-up over their face value of more than 50%" (Viagogo/StubHub final
report p.131, as quoted by DBT, class A via regulator). The UK's 37.1m primary tickets a year support
≈1.9m secondary sales worth £350m before fees — ~~≈£184 gross average, ≈£269 per resale ticket
inclusive of all fees~~. **[CORRECTION 2026-11-07T14:00Z, R2-16 — dead: £184 is right for this flow
(350 / 1.9 = 184.2) but £269 is not. £269 is £404m / 1.5m, a second flow in the same DBT note; 269 × 1.9 =
£511m, so the two pairs cannot be quoted as a before-and-after. Quote each pair on its own. See CORRECTION 2
at the end of this file.]**

---

## 4. Primary versus secondary value, and what happened when organisers repriced

Sized three ways: resale profit of slightly over $1.17m on 56 concerts = **1.4% of primary revenue**,
~~even after scaling for the ~50% of resale the authors do not observe~~ **[CORRECTION 2026-11-07T14:00Z,
R2-17 — dead: 1.4% is the observed half, unscaled. The paper's own wording is "even if we are accounting for
only half of resale activity", which is a limitation and not a correction upwards for the missing half. See
CORRECTION 1 at the end of this file.]** (class A); repricing the top 10%
of seats at the median resale price for those seats raises primary revenue **3.4%**, ≈$27,000 per
event (their counterfactual — a model-based simulation, not an observed adoption); and adding a
fourth seating category is worth about half of going from one to two, with multi-category pricing
beating single-price by ≈5% (class A). The three are consistent and they bound the prize: single-digit
percent of primary revenue, concentrated in the best seats.

Adoption evidence is thinner than the policy debate implies. Ticketmaster's primary auctions improved
price discovery, "roughly doubled" performer revenue and "nearly eliminated" arbitrage profits — and
the authors close by explaining why the auctions nonetheless failed to take off (class A). MLB's
dynamic pricing produced levels between fixed and secondary, varying by market and seat (12 games,
class A). I found **no peer-reviewed measurement** of Ticketmaster-style platinum/in-demand pricing's
revenue or sell-through effect on a large sample; trade-press claims are vendor claims (class D).
Treat "dynamic primary pricing raises revenue" as well-motivated, not established at scale.

---

## 5. Liquidity and churn

- **Share that resells: ≈5%.** "Only 5% of purchased tickets [were] resold on eBay or StubHub"; their
  most active event reached 17%, with resale revenue equal to 37% of that event's primary revenue
  (class A). The UK model starts from 1.9m resold against 37.1m primary ≈ 5.1%. Two independent
  measurements, same number. Any model assuming a liquid secondary market for the median event is
  wrong by an order of magnitude: the mean is carried by a few hot events.
- **Concentration: extreme.** "The top 10% of resellers account[ed] for more than 70% of platform
  ticket resale volumes" (CMA, via DBT, class A via regulator); 46% of resale transactions in the
  concert data were by fans, not brokers (class A).
- **Holding duration and transfers per ticket: not established.** No peer-reviewed or
  regulator-published distribution exists that I could find. Sweeting gives an indirect fact (median
  eBay purchase is ten days before the game) and both the UK and NSW rules cap how many tickets a
  person may resell, implying repeat-transfer is a policy target, but no count is published. This is
  a genuine gap and it is exactly what an on-chain ledger measures better than any dataset in the
  literature.
- **On-chain sources.** Get Protocol publishes a subgraph "aggregating and indexing all on-chain
  event, ticket, and protocol data" plus a public NFT ticket explorer, and claims "millions of
  on-chain smart tickets since 2016" (vendor claim; I did not verify a count against chain state).
  The capability claim is checkable and matters: per-ticket issue/sale/transfer/redeem with price and
  counterparty is the churn dataset that does not otherwise exist. Extracting one season is a Phase 2
  data task, not a research question.

---

## 6. What survives, what vanishes, what appears on a wallet-bound capped ledger

**Vanishes.** Asking-versus-realised price gap — the organising problem of Phase 2A in the
literature; every observation is a settled transfer. Also cross-platform duplicate listings, seller
identity resolution (a wallet is the identity, so repeat-reseller concentration is directly
computable), and fee inference *within* the platform (fees become parameters we set, not estimates).

**Survives, relocated.** Censoring moves from prices to *exposure*: with no listing start, no ask, no
withdrawal event, the sale count is a numerator with no denominator and `P(sale | price, exposure, t)`
is unidentified (Gap 1 — the literature agrees the hazard, not the price, is the hard object:
Sweeting's identification rests on listings that stay unsold, which we cannot see). Selection
survives: only sold tickets have prices, and resold tickets are better seats (mean seat-quality
percentile 0.61 vs 0.50, class A). Seat quality itself is worse for us: it is the dominant
within-event price axis in every study (resale prices reflect "small differences in seat quality —
every seat may have a different price", while primary prices do not), and our contract carries
`tierId` only (Gap 3).

**Appears.** Three mechanisms with no counterpart in the literature, all class D with a clear test:

1. **Cap as sharp policy truncation with rationing** (§3). New because on-chain enforcement cannot be
   evaded *within* the rail: the bound is known and exact, which is statistically a gift (Tobit with a
   known bound) and commercially a trap.
2. **Key handoff as an invisible transfer.** A wallet-bound token can be sold by handing over the key;
   the ledger then shows nothing, and the true price, holding period and holder are all unobserved.
   `transferRestricted` and `requiresVerifiedWallet` are the countermeasures. So the ledger is
   complete only conditional on enforcement — a regime switch inside the observation set that is not
   labelled. Testable: tickets that go dark (no transfers, no redemption by the issuee) and later
   redeem from an unrelated wallet.
3. **Recording incentives created by the cap.** Where resale above the cap is illegal or impossible,
   counterparties reprice the *recorded* leg to the cap and settle the residual elsewhere. The
   recorded markup becomes a strategic variable, not a market outcome. Testable: excess mass just
   below the cap, discontinuity in listing composition at the cap, more bundling and more dark tickets
   on tighter-capped events.

**For estimation:** fit a latent `M*` with observation `min(M*, cap)` plus leakage probability
`q(cap, event)`, estimate `q` from dark tickets and bundled listings, and never report a capped mean
without calling it a lower bound. Estimate the hazard with an explicit exposure term; use cap-region
velocity as the primitive measure of excess demand; condition the time-to-event slope on an
inventory state; net out fees before anything is called value.

**For pricing:** on capped events the secondary premium is a floor, not a target — cap-region rationing
says demand exceeds the ceiling, and the primary optimum is set by primary sell-through and demand
elasticity. On uncapped events the markup is usable but understates value when handoff is live. In
both cases the optimum depends on the fee model (per-unit and ad valorem fees give different optima),
which the contract does not carry.

---

## 7. Three columns

**Literature problems we no longer have**
- Asking-versus-realised gap; listing-price noise; stale and duplicate listings.
- Cross-platform fragmentation of the same ticket; seller identity and repeat-reseller inference.
- Fee incidence unobservable within a platform (fees become a parameter we set).
- Per-ticket price path and custody trail, previously only reconstructable from scrapes.

**Still have**
- Censoring: no listing exposure (`listedAt`, ask, delist reason) → no sale hazard (Gap 1).
- Selection: sold tickets are the better seats (0.61 vs 0.50 seat-quality percentile, class A).
- Seat quality: only `tierId`, no section/row/seat — the dominant price axis is missing (Gap 3).
- Sparse events: 5% of tickets resell; most events have almost no resale history.
- Demand-side invisibility: no views, queue position, registration volume or search interest.
- Net-of-fee value: no fee, royalty or settlement field (Gap 4).
- Primary sell-through velocity: inventory is a snapshot only (Gap 5).
- The prize is small (1.4-3.4% of primary revenue), so an engine that cannot resolve single-digit
  percent effects is not useful.

**Newly have**
- Sharp truncation at a known bound, with rationing behind it (cap mass point, sale velocity).
- Off-ledger price: side payments, wallet handoff, bundling — recorded markup biased down, worst where
  demand is strongest.
- An unlabelled regime switch inside the observation set (enforcement on/off).
- Disclosure-law breaks: US all-in pricing from 2025-05-12 makes pre/post fee-inclusive series
  non-comparable (16 CFR Part 464).
- Regulatory risk as a first-class variable: caps spreading (NSW 2018, Ireland 2021, UK announced
  2025) and the dominant ticketer's antitrust position in flux (SDNY verdict 2026-04-15).

---

## 8. Follow-up questions (§1.4)

1. What is the actual distribution of holding duration and transfers per ticket on our platform, and
   does it vary with event heat? (Not in the literature; answerable from chain.)
2. How much mass sits just below `resalePriceCapBps` in a real capped ledger, and does sale velocity
   at the cap predict primary sell-through?
3. Can `q(cap, event)` — the off-ledger leakage rate — be identified from dark-ticket patterns, and
   how big is it on the events that matter?
4. Is the sign of the time-to-event slope predictable from on-sale sell-through alone (two-regime
   model), and where is the switching threshold?
5. What is our fee stack (per-unit vs ad valorem, both sides, royalty bps), and how far does the
   primary optimum move across plausible values?
6. Does `transferRestricted` hold on-chain in practice, and what fraction of tickets in a restricted
   event still change hands? The contract note that it "should reflect whether the restriction is
   actually enforced" suggests it may not.
7. Is seat quality recoverable from `tierId` plus serial, or must the operator supply coordinates?
   (Highest-value data request after listing exposure.)
8. Get Protocol: extract one season of per-ticket ledger data and measure churn, markup shape at
   whatever caps exist, and cap-region behaviour — the only public natural experiment of this kind.

---

## Sources

Peer-reviewed and working papers (metadata verified via Crossref/OpenAlex; full text read where
cited in detail):
- Sweeting, A. (2012). *JPE* 120(6):1133-1172. doi:10.1086/669254. WP PDF read:
  https://econweb.umd.edu/~sweeting/SWEETING_PDECLINE_0112.pdf
- Leslie, P. & Sorensen, A. (2014). *RES* 81(1):266-300. doi:10.1093/restud/rdt033. PDF read:
  https://users.ssc.wisc.edu/~atsorensen/papers/resale.pdf
- Leslie, P. & Sorensen, A. (2009). The Welfare Effects of Ticket Resale. NBER WP 15476.
  doi:10.3386/w15476. Conflict on file: the 2009 WP says "half" of the reallocation welfare gain is
  offset by rent-seeking and transaction costs; the 2014 published version says "a third". Cite the
  published figure.
- Budish, E. & Bhave, A. (2023). *AEJ:Micro* 15(1):142-170. doi:10.1257/mic.20180230
- Courty, P. & Pagliero, M. (2012). *REStat* 94(1):359-369. doi:10.1162/rest_a_00179
- Courty, P. (2003). *JEP* 17(2). doi:10.1257/089533003765888449
- Shapiro, S. L. & Drayer, J. (2012). *J. Sport Management* 26(6):532. doi:10.1123/jsm.26.6.532
- He, D. & Lin, S. (~~2025~~ **2026**). *Marketing Science* 45(3):515–533. doi:10.1287/mksc.2023.0623 **[CORRECTION 2026-11-07T14:00Z, R2-15b — dead year only: Crossref gives 45(3):515–533, issued 2026-05. The DOI is right and was checked. See CORRECTION 3.]**
- Cui, Y., Duenyas, I. & Şahin, Ö. (2014). *Management Science* 60(9). doi:10.1287/mnsc.2013.1862
- Wardhaugh, B. (2026). *Legal Studies*. doi:10.1017/lst.2026.10125 (legal argument, not measurement)

Official and regulatory primary sources:
- DBT/DCMS press release 2025-11-19: https://www.gov.uk/government/news/government-bans-ticket-touting-to-protect-fans-from-rip-off-prices
- DBT analytical note 2025-12-19 (37.1m primary / 1.9m secondary tickets, £350m; 75% markup; 20%
  displacement; CMA citations): https://www.gov.uk/government/publications/government-response-to-resale-of-live-events-tickets-consultation-analytical-note/analytical-note-on-government-response-to-resale-of-live-events-tickets-consultation
- CMA, *Completed acquisition by PUG LLC (viagogo) of the StubHub business of eBay Inc.*, final report
  (>50% markup; top-10%-of-resellers >70% of volume, as quoted by DBT).
- NSW Fair Trading, "Ticket reselling": https://www.nsw.gov.au/legal-and-justice/consumer-rights-and-protection/services/ticket-reselling
- Gov.ie, Sale of Tickets Act 2021, in force 2021-07-31; post-enactment report published.
- 16 CFR Part 464, 90 FR 2166, effective 2025-05-12: https://www.ecfr.gov/current/title-16/chapter-I/subchapter-D/part-464
- Live Nation/Ticketmaster: SDNY jury verdict for the plaintiff states on all counts, 2026-04-15,
  remedies pending. Secondary: Paul, Weiss memo, April 2026,
  https://www.paulweiss.com/insights/client-memos/live-nationticketmaster-antitrust-verdict-key-takeaways-from-the-states-jury-trial-win

Vendor claims, cited only as claims: Get Protocol documentation (subgraph, NFT ticket explorer,
"millions of on-chain smart tickets since 2016"); Ticketmaster NFT-gated pilots 2021-23.

**Could not establish:** any published distribution of holding duration or transfers per ticket; any
peer-reviewed measurement of Ticketmaster-style dynamic primary pricing on a large sample; a verified
on-chain count from Get Protocol; the current status of the DOJ's own 2024 suit (the states' case is
the one with a verdict); and the "Hakes" reference in the brief — no ticket-market paper by that
author could be identified, so none is cited rather than guessed.

---

## CORRECTION 1 (2026-11-07T11:28Z) — "even after scaling" inverts the paper's own caveat

Appended by the corrections pass after `records/findings/00-verification-round1.md` §3. Nothing above is
deleted. The sentence is withdrawn as printed.

**Withdrawn sentence, §4:**

> "Sized three ways: resale profit of slightly over $1.17m on 56 concerts = **1.4% of primary revenue**, even
> after scaling for the ~50% of resale the authors do not observe (class A)"

**What the source says.** Leslie & Sorensen (2014) state, in the text the verification pass extracted from the
paper:

> "This is equivalent to 1.4% of the total primary market revenue for these events. … this suggests a fairly
> modest amount of forgone profit by firms in the primary market, **even if we are accounting for only half of
> resale activity**."

**What is true.** 1.4% is the figure computed on the half of resale the authors observe. The paper does not
scale it up, and it flags that the other half is missing. Its caveat is that the number is *incomplete*, not
that it is conservative after correction. The words "even after scaling" therefore assert the opposite of the
source, and do it on the number the commercial case rests on.

**Corrected statement.** "resale profit of slightly over $1.17m on 56 concerts = 1.4% of primary revenue on
the half of resale the authors observe; the authors note the figure excludes the other half (class A for the
computed figure, not for any scaled figure)". The class A label attaches to the 1.4% as computed; a scaled
figure does not exist in the paper and may not be quoted as though it did.

**Downstream.** `records/findings/01-c-methods.md` carries the prize as "1.4–3.4%", which is `02-a`'s and this
file's numbers at order-of-magnitude precision; it does not repeat the scaling claim. The ledger's P1.A row
quotes "worth 1.4% of primary revenue" without the scaling clause, so it does not carry the defect, but any
reader taking 1.4% from this record must carry the "only half of resale" caveat with it.

---

## CORRECTION 2 (2026-11-07T11:28Z) — the £269 figure is spliced onto a different flow

**Withdrawn sentence, §3:**

> "The UK's 37.1m primary tickets a year support ≈1.9m secondary sales worth £350m before fees — ≈£184 gross
> average, ≈£269 per resale ticket inclusive of all fees."

**What is true, with the arithmetic shown.** £184 is consistent with the first pair: 350 / 1.9 = 184.2. £269 is
not: 269 × 1.9 = £511.1m, which is not £350m. £269 is £404m / 1.5m, a different flow in the same DBT
analytical note (the note's own two pairs, as read by the verification pass at `00-verification-round1.md`
§3). The sentence presents the two as a gross-then-all-in pair for one flow; they are two unrelated
baselines.

**Corrected statement.** Either quote the £350m / 1.9m pair with the £184 average it implies, or quote the
£404m / 1.5m pair with £269. The two must not appear in one clause as a before-and-after. The substantive
point the paragraph is making, that a platform's all-in price is materially above a pre-fee headline, is
supported by the CMA's ">50% markup" finding cited two sentences earlier and does not need this pair.

---

## CORRECTION 3 (2026-11-07T11:28Z) — He & Lin is 2026, not 2025

**Withdrawn labels.** §3 "He & Lin (*Marketing Science*, 2025)" and the reference at §7 "He, D. & Lin, S.
(2025). *Marketing Science*. doi:10.1287/mksc.2023.0623".

**What is true.** A Crossref query for that DOI on 2026-11-07 returns: He, D. & Lin, S., "Price Caps by
Matching Platforms: The Case of Ticket Resales", *Marketing Science* **45(3):515–533**, issued 2026-05. Cite
it as He & Lin (2026). The work is real and the proposition it is cited for in §3, that a stringent cap can
push high-price sellers out and raise the average transaction price, is unaffected. The class C label on that
corollary is also unaffected: it is a model result, not a measurement of this market.

**One thing this correction does not settle.** `01-b` §4.5 and `records/C-variable-registry.md` C-3 state that
no peer-reviewed study of resale price caps in ticket markets was found. This paper is a peer-reviewed study
of exactly that subject, and this file already cites it. Whether it counts against that sentence depends on
whether it is an econometric study or a model of matching, which I did not read and do not assert. The
question is recorded in `records/CORRECTIONS-APPLIED.md` as noticed and not resolved; no conclusion is
changed here.

---

## NOTE (2026-11-07T12:55Z) — He & Lin against `01-b`'s "no peer-reviewed econometric study": both are right about different things

Appended, not a correction. Neither this file nor `01-b` is wrong on this point, and neither conclusion
changes.

**The two passages, quoted.**

This file, §3, as printed (the year is superseded by CORRECTION 3 above; the proposition is not):

> "He & Lin (*Marketing Science*, 2025) add the non-obvious corollary: a stringent cap can push high-price
> sellers out, reduce seller-side competition, and *raise* average transaction price (class C)."

`01-b-identifiability.md` §4.5, as printed:

> "A gap to record: I found **no peer-reviewed econometric study of resale price caps in ticket markets.** The
> ticket literature covers resale's allocative and rent-seeking effects … and price dynamics … not caps. The
> cap component is therefore class B borrowed from rent control plus class C theory, and **no class-A claim
> about caps may appear in the deliverable.**"

**Why they do not contradict.** They are claims about two different objects.

- This file uses He & Lin for a **theoretical proposition** and labels it **class C** — "a model result, not a
  measurement of this market" (CORRECTION 3). It nowhere asserts that He & Lin is, or that any economist has
  published, an *empirical measurement* of a resale cap in a ticket market.
- `01-b` §4.5 asserts the absence of a **peer-reviewed econometric study** — that is, of class-A evidence,
  which is the class its closing sentence is about. That sentence therefore stands whatever kind of paper
  He & Lin is, unless He & Lin is itself econometric.

Both labels are consistent with the same world: a peer-reviewed *model* of price caps in ticket resale, and no
peer-reviewed *measurement* of one. That combination is exactly what a class-C citation plus a no-class-A
finding describes.

**What would falsify `01-b`, and what I did not do.** If He & Lin is an econometric study, `01-b` §4.5's first
sentence is false as printed and needs a correction it has not had. I did not read the paper in this pass and
therefore assert nothing about its method. What I could check without the full text: Crossref for
`10.1287/mksc.2023.0623` returns type `journal-article`, "Price Caps by Matching Platforms: The Case of Ticket
Resales", Da He & Song Lin, *Marketing Science* **45(3):515–533**, issued 2026-05, with the abstract "This study
examines ticket resale platforms' voluntary price caps, analyzing their adoption incentives and effects on
prices, sales, profitability, and welfare." The abstract does not say whether the analysis is empirical or a
model, so the one question that settles it is still the full text. That question stays open and is recorded in
`records/CORRECTIONS-APPLIED.md` §4.

**The one sentence in the records that this note does falsify** is not in either finding: `C-variable-registry.md`
C-3 closes "**no class-A claim about caps may appear in the deliverable**, because no peer-reviewed study of
resale price caps in ticket markets was found", which is broader than `01-b`'s claim and is contradicted by a
paper cited in this file. A dated note there narrows it to `01-b`'s wording; the no-class-A rule itself is
unaffected and unchanged.

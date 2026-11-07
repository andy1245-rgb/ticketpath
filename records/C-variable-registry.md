# C — Variable registry

**Programme section:** §2.C. **Status:** first complete pass, revised once. **Written:** 2026-11-07T11:40Z.
**Author:** records agent (`records-c`). **Supersedes:** the seeded stub of 2026-11-07T08:27Z (no content lost).
**Last touched:** 2026-11-07T11:40Z (revision 2; the system clock reads the same hour as the first pass).
**Revision 2 added:** the decision-time verdict on every row (`P`/`R`/`N`, with `DROPPED` and its
reason), 33 variable rows and the 12 interaction features of Phase 3 as composite variables, from
`02-a`, `02-b`, `02-c`, `02-e`, `03-a` and `03-b` (§8).

**Revision 2 sources, and nothing else:** `records/findings/03-b-temporal-correctness.md` (the
authority on every verdict below), `records/findings/03-a-interactions.md` (the 13 interactions and
the 12 interaction features), and `records/findings/02-a-price-paths.md`,
`02-b-cap-truncation.md`, `02-c-sale-hazard.md`, `02-e-cold-start.md` for the feature definitions
those four own. Where a Phase 2 or Phase 3 file restates an earlier verdict, §8.6 says which and
quotes it. Nothing in §0 to §7 was rewritten.

**Sources folded in, and nothing else:**
`records/findings/01-d-external.md` (Tables C-1 and C-2, §4 mechanisms, §5 predictive versus causal),
`records/findings/01-b-identifiability.md` (which targets are identifiable at all),
`records/00-data-situation.md` (the four contract gaps), `records/F-decision-log.md` (D3, D4, Q1, Q2, Q3),
and `../ticketing-frontend/lib/types.ts` read directly for field-level availability.

**What this file is not.** No number here comes from `lib/mock/`. No estimate is reported; every
"expected effect" below is a sign and a channel, not a measurement. Where 01-d and 01-b disagree, the
disagreement is written down in place rather than averaged away (§7). Evidence classes are the
programme's (§4.3, `records/README.md`) and are not upgraded by this pass.

---

## 0. How to read an entry

Every variable carries the eleven §2.C fields plus the temporal verdict that 01-d's admission test
imposed, and the class and priority 01-d assigned. Field names are fixed so the file can be parsed later.

**Mechanism naming.** §4.2 requires the channel to be named before the feature is included. One of:
buyers · sellers · supply · demand · liquidity · willingness to pay (WTP) · transaction probability ·
price expectations. A variable with no named channel is not admitted, which is why most of §4 is a
rejection list.

**Temporal verdict.** Two decisions are made at two times, and a variable can be legitimate at one and
illegitimate at the other:

| Verdict | Meaning |
|---|---|
| **P** | Value is knowable at, or before, the on-sale at which the primary price is fixed. Admissible in the primary-price model. |
| **R** | Value is knowable at a decision time `t` inside the trading window but **not** at the on-sale. Admissible only in the in-market reprice model. |
| **P+R** | Knowable at both (structural constants, and things announced before on-sale). |
| **N** | Knowable at neither decision time without look-ahead. Not a feature at any horizon. |

**Priority** is 01-d's scale, unchanged: **1** build now · **2** after the core · **3** conditional on
data · **4** deflator/control only · **0** blocked on a data requirement that goes to the operator.

**Groups.** §1 admitted and usable today from the wire contract alone. §2 admitted but obtainable only
outside the contract, with the collection route and its cost. §3 not obtainable today but decisive.
§4 rejected, with the reason. §5 the contract fields no finding has classified. §6 build order. §7
conflicts and cross-cutting notes.

---

## 1. Group 1 — admitted, and usable today from the wire contract alone

Four variables. All four are in `lib/types.ts`, all four are computable in standard-library Python with
no external account, and none of them costs anything to collect. This is a short list and it is the
honest one: the contract is a transaction ledger, and a transaction ledger yields time, quantity,
policy and provenance.

### V1 `time_to_event` — priority 1, class A

- **Definition.** `startsAt − t`, in hours, for the event the ticket belongs to.
- **Mechanism (through sellers and buyers, opposing).** Perishable inventory. A holder with unsold stock
  faces a hard expiry at `startsAt`, and the value of continuing to search for a higher bid is exactly
  the option value of the remaining horizon. That option value shrinks monotonically to zero, so the
  seller's reservation ask falls as τ→0. The same clock acts the other way on the buyer: waiting risks
  no ticket at all, so the buyer's willingness to pay rises as the supply of un-bought tickets thins.
  Both effects are real and they point in opposite directions. This is why the expected effect is not a
  slope but a conditional.
- **Expected effect.** Conditional, **not monotone**. On an oversubscribed event the observed path rises
  into the event date because the buyer-side force dominates; on a soft event it decays because the
  seller-side force dominates. Fitting one average slope across events produces a number near zero and
  hides both effects.
- **Interactions.** Must enter interacted with a tightness measure — V2 sell-through or V3 cap binding.
  Interacts with V4 capacity (the denominator of tightness), V6 venue type (capacity band), and with
  everything the reprice model knows about the remaining risk set.
- **Measurement.** Trivial arithmetic on two ISO-8601 fields. No transformation needed; log hours is the
  default parameterisation because the force is proportional to remaining option value, not to hours.
- **Data source.** Contract: `Event.startsAt`, and `occurredAt` (or `slot`, see §5) for `t`.
- **Availability.** Present. Continuous, one value per observation.
- **Update frequency.** Continuous — recomputed at every scoring instant.
- **Temporal correctness.** **P+R**, and it is the cleanest case in the registry: τ is known ex ante at
  both decision times.
- **Predictive value.** High. 01-b §4.2 gives the shape its class-A anchor: Sweeting (2012) finds prices
  decline significantly as the game approaches, controlling for quality, because the opportunity cost of
  holding falls. Treat the *sign in our panel* as unknown until measured; treat "τ must be interacted,
  not entered alone" as settled by the mechanism.
- **Evidence.** **A** for the direction in a ticket resale market (Sweeting 2012, *JPE* 120(6):1133–1172).
  The interaction requirement is **C** — an argument from the two opposing forces, not a measurement.
- **Leakage / endogeneity.** No leakage: τ is future-blind by construction. Endogeneity is not zero
  however — τ is correlated with the *seller's* past listing decisions, so a coefficient on τ estimated
  on sold tickets only inherits the selection in V5.
- **Priority.** **1**.

### V2 `primary_sell_through` — priority 1, class C (mechanism) with B support

- **Definition.** `issuedCount / totalSupply`, per tier, at time `t`. Also the tier-level pair itself,
  because a sold-out tier and an unsold tier are different objects (§7 conflict C-2).
- **Mechanism (through demand and price expectations).** Rationing. At a sell-out the queue, not the
  price, cleared the market, so latent demand at the last posted price met or exceeded supply. That is
  observable evidence that the market is tight, and tightness is what decides which of V1's two forces
  wins. The channel is not "demand correlates with price"; it is that sell-through *censoring* reveals a
  one-sided statement about the demand curve.
- **Expected effect.** **+** on resale markup at fixed everything else, because scarcity is real; and it
  flips the sign of the V1 slope. A tier at `issuedCount = totalSupply` and a tier at `issuedCount =
  0.4·totalSupply` on the same event are not the same market.
- **Interactions.** V1 (mandatory), V3 (a binding cap suppresses primary price variation and pushes
  rationing into the secondary market), V4 (capacity sets how much sell-through means).
- **Measurement.** Ratio of two integers already in the contract. Per tier, not event-wide: the event
  aggregate is a supply-weighted average and destroys the cross-tier variation that carries the signal.
- **Data source.** Contract: `Event.tiers[].totalSupply`, `issuedCount`; also `Event.totalSupply`,
  `Event.issuedCount`.
- **Availability.** Present, but a **single current snapshot** — no history, no on-sale time, no
  sell-out time (`00-data-situation.md` §4). See §7 conflict C-2: 01-d calls the snapshot a severe
  limitation; 01-b §5 shows the level is identified even without velocity. Both are recorded.
- **Update frequency.** As often as the platform is polled. There is no stored series, so the engine
  must log it at every scoring instant or the history is lost forever.
- **Temporal correctness.** **P+R**, but only if the value used is the one observed at decision time.
  Using today's ratio to price an on-sale that happened last month is look-ahead of the most ordinary
  kind and it is the default failure in any pipeline that queries the contract for "current" state.
- **Verdict restated by 03-b (§3.1 A15): R, not P+R.** Its table gives `R | R` for this row, and §2.1
  states the reason: at D1 "It may not know any ticket-level, ledger-level or aggregate fact about `e`,
  and it may not know its own sell-through, because there is none yet." The P+R above stands as the
  statement that a sell-through value, once observed, is legitimate at the instant it was observed; it
  is **not** available at the on-sale of the same event. Recorded in §8.6, row 1.
- **Predictive value.** High, and 01-b §4.4(i) makes it the highest-value identified object in the
  schema: primary sell-through is a demand experiment already run, a Tobit with an observed censoring
  indicator, needing no secondary data at all.
- **Evidence.** **C** for the rationing mechanism; **B** for the Tobit-with-observed-censoring
  estimator (Tobin 1958; Conlon & Mortimer 2013). **UNVALIDATED** for any functional form of demand.
- **Leakage / endogeneity.** Severe, and structural. Sell-through is an **outcome of our own primary
  price**. Set the price low, sell-through is high, markups are large: regressing markup on sell-through
  reads the company's past decisions back as a law of nature. 01-d §5 is explicit — state, never a free
  regressor, and any elasticity estimated on it is contaminated by our own policy.
- **Priority.** **1**.

### V3 `resale_policy` — priority 1, class C

- **Definition.** The four policy fields, per event and per ticket: `resalePriceCapBps` (null =
  uncapped but still tracked), `resaleEnabled`, `requiresVerifiedWallet`, `transferRestricted`. Plus the
  derived indicators `cap_bps` as a number and `cap_binding` as an observed event (a sale whose
  `markupBps` equals the cap).
- **Mechanism (through sellers, supply, transaction probability, and price expectations).** Two distinct
  channels that must not be collapsed. **(a) The ceiling.** A binding cap truncates the price
  distribution from above, so the market does not clear by price; it clears by speed and rationing. The
  cap also caps the seller's upside, which suppresses listing supply at the top of the value
  distribution — the strongest tickets are the ones least likely to be offered. **(b) The frictions.**
  Verified-wallet and transfer restrictions add a step to every custody hop: a buyer who must pass
  identity verification has a higher effective cost of acquiring, so each hop loses participation, and
  `resaleEnabled = false` shuts the channel entirely.
- **Expected effect.** Cap binding → a mass point at the cap plus excess demand standing behind it;
  frictions → **−** on supply and on transaction probability, ambiguous on price.
- **Interactions.** V2 (cap binding and sell-through jointly determine tightness), V1 (the cap changes
  what the τ slope can do), V5 (a capped sale is a sale at the boundary, so trail features computed on
  capped events are computing on a truncated mark), `requiresVerifiedWallet` × `DestinationRow.region`
  (verification may select a different buyer population).
- **Measurement.** Direct field read. `cap_binding` is the one derived quantity that needs care: compare
  `markupBps` to `resalePriceCapBps` for that event and that tier's own face, and treat exact equality
  as a boundary observation, not a point measurement.
- **Data source.** Contract: `Event.resalePriceCapBps`, `resaleEnabled`, `requiresVerifiedWallet`;
  `Ticket.transferRestricted`; `LedgerEntry.markupBps` for the binding test.
- **Availability.** Present at event and ticket level. Q3 is open and load-bearing: whether the cap is
  enforced on-chain (a transfer reverts, so nothing is recorded) or by the platform's matching engine (a
  listing is refused, so an attempt could be recorded). Until Q3 is answered, the cap's *absence* from
  the ledger is not informative.
- **Update frequency.** Static per event, except `transferRestricted`, which the contract defines as
  enforced "right now" for that mint, i.e. it can change mid-life.
- **Temporal correctness.** **P+R** for the policy fields, provided the policy in force at decision time
  is the one used and `transferRestricted` is read as a time-varying value rather than a constant.
- **Predictive value.** High, and it is one of the three genuinely **causal** variables in 01-d §5: a
  cap change is a natural experiment on the objective function.
- **Evidence.** **C**. 01-b §4.5 records the gap honestly: no peer-reviewed econometric study of resale
  price caps in ticket markets was found. The cap component is class B borrowed from rent control plus
  class C theory, and **no class-A claim about caps may appear in the deliverable.**
- **Leakage / endogeneity.** No leakage in the field values. Endogeneity is severe in any *use* of them
  as regressors: the cap is chosen by the organiser, jointly with the face value it is denominated
  against. Treat the cap as a parameter of the data-generating process, not as a covariate (01-d §4).
- **Priority.** **1**.

### V5 `custody_trail_features` — priority 1, class C

- **Definition.** Per ticket, computed on `entries` truncated at `occurredAt ≤ t`: hop count; per-hop
  holding duration; repeat-reseller identity from `fromWallet`/`toWallet`; the ticket's own realised
  markup path; and its position in that path (how many hops already happened, how long since the last
  one).
- **Mechanism (through sellers and supply, and through liquidity).** A wallet that appears as
  `fromWallet` across many tickets is a professional seller: professional sellers list earlier, reprice
  faster, and are the marginal supplier, so their presence raises the quantity offered and compresses
  the ask. A long-held ticket is held by a consumer, whose outside option is attendance, so its supply
  pressure is lower and its ask, if it appears at all, is steeper. The per-ticket price path is also the
  only true per-ticket price observation the platform has — everything else is an aggregate that mixes
  tickets.
- **Expected effect.** **+** for repeat-reseller and rapid-churn tickets (they clear faster and at
  thinner margins); **−** on supply pressure as holding duration rises.
- **Interactions.** V3 (caps bind hardest on the trails most likely to be re-offered), V1 (a long-held
  ticket approaching expiry is a different object from a churned one), V14 if it ever exists (depth is
  what turns a trail into a market).
- **Measurement.** Group each ticket's entries by `ticketId`, sort by `slot` (see §5 on `occurredAt`
  granularity), cumulative aggregates truncated at `t`. Wallet-level features must be built from a
  wallet history that is itself truncated at `t`.
- **Data source.** Contract: `LedgerEntry.kind`, `fromWallet`, `toWallet`, `priceLamports`,
  `markupBps`, `occurredAt`, `slot`; `Ticket.issuedToWallet`, `transferCount`.
- **Availability.** Present per row. **Partially identified** as a person-level construct: 01-b §4.6(b)
  establishes that a repeat reseller appears as the same `fromWallet` across tickets and that
  `issuedToWallet` links primary to secondary counterparties with no inference — but that whether two
  wallets are one person is not identified, and Bitcoin-style co-spend clustering does not transfer to
  Solana's account model.
- **Update frequency.** Per new ledger row; recomputed at scoring time over the truncated trail.
- **Temporal correctness.** **P+R**. Nothing here is intrinsically forward-looking; the *computation* is
  where the future leaks in.
- **Predictive value.** High. 01-d ranks it alongside V2 as the most informative contract-native block.
- **Evidence.** **C** for the mechanism (professional-versus-consumer supply pressure is an argument, not a
  measurement in our data), and **C** for the wallet-identity result, which is an identification claim from
  01-b §4.6(b), not an empirical ticket finding. The repeat-sales machinery the trail enables has class-A
  support (Bailey, Muth & Nourse 1963; Sweeting 2012), but that is support for the *estimator*, not for any
  sign in this registry. **UNVALIDATED** end to end: nothing here has been estimated.
- **Leakage / endogeneity.** **The trap of the whole build**, per 01-d §4. The full trail is the future:
  hop `n+1` is the label, not a feature, and a wallet feature computed over the whole dataset includes
  resales that happen after `t`. 01-d names this as the most likely silent Phase 7 failure. Endogeneity
  is also direct — a sale is the outcome being predicted, so `transferCount` and
  `lastSalePriceLamports` are outcomes, not state.
- **Priority.** **1**.

---

## 2. Group 2 — admitted, obtainable only outside the contract

Eleven variables. Each is admitted on mechanism, none is in `lib/types.ts`, and each entry says how it is
obtained and what that costs. Costs are 01-d's, as published on the date it checked; anything 01-d could
not read is marked unverified here and must be re-checked before it is relied on.

### V4 `venue_capacity` — priority 1, class B

- **Definition.** Seated capacity for the venue, joined from a venue table keyed on normalised venue name
  and city.
- **Mechanism (through supply).** The denominator of scarcity. Capacity against expected demand decides
  whether an event can sell out at any price, and sell-out is what makes a resale market exist at all.
  This is not "bigger venue, lower price" — it is that the same demand implies a different tightness
  ratio at 4,000 seats and at 70,000.
- **Expected effect.** **−** on markup at fixed demand, and it enters the V1 interaction through
  tightness rather than as a main effect.
- **Interactions.** V1, V2, V6 (type is a proxy for the capacity band when the number is missing).
- **Measurement.** Integer lookup. Where the venue name is free text in the contract (it is), the join
  needs normalisation and a manual pass; a name mismatch silently drops the row.
- **Data source.** Wikidata (CC0) and OpenStreetMap (ODbL) as a free first pass; official venue seating
  charts to fill gaps.
- **Availability.** **Not in the contract.** `Event.venue` is free text with no capacity field.
- **Update frequency.** Static.
- **Temporal correctness.** **P+R** (structural constant).
- **Predictive value.** High — 01-d calls the venue table the highest ratio of information to cost in the
  whole registry, because capacity is the scarcity denominator and the contract omits it.
- **Evidence.** **B**. The capacity/demand interaction is standard revenue-management structure, not a
  measured ticket result in our data.
- **Leakage / endogeneity.** None. The one caution is measurement: capacity is missing or stale for many
  venues on both free sources and needs a manual pass against official charts.
- **Priority.** **1**. Cost: free, roughly twenty minutes of manual verification per venue.

### V6 `venue_type` — priority 2, class B / D

- **Definition.** Arena / stadium / club / amphitheatre / theatre, with capacity band as the fallback
  classifier.
- **Mechanism (through buyers, and as a stratifier).** Fixes three things at once: weather exposure
  (which is why V12 is zero indoors), sightline structure (which sets how much price variance lives
  *within* an event rather than between events), and the typical capacity band. It does not move price
  directly; it changes which other variables do.
- **Expected effect.** Stratifier, not a main effect. Including it as a level shifts the intercept and
  buys nothing.
- **Interactions.** V1, V4, V12 (the indoor/outdoor switch that makes V12 legitimate or a mechanism
  violation).
- **Measurement.** Categorical, derived from name and capacity; a deterministic mapping.
- **Data source.** Wikidata / OSM; official charts.
- **Availability.** Not in the contract; derivable once the venue table exists.
- **Update frequency.** Static.
- **Temporal correctness.** **P+R**.
- **Predictive value.** Medium. Its value is that it licenses or forbids another variable.
- **Evidence.** **B** for the sightline/capacity structure, **D** for any effect on our panel.
- **Leakage / endogeneity.** None.
- **Priority.** **2**.

### V7 `city_market_size` — priority 2, class B

- **Definition.** Metro population or DMA rank for `Event.city`.
- **Mechanism (through demand and liquidity).** Scales the local buyer pool and the walk-up segment, and
  therefore the number of buyers available to a resale at any instant. A 20,000-seat arena in a 6m metro
  and the same arena in a 400k metro are different markets even when everything inside the venue matches.
- **Expected effect.** **+** on both the level of markup and the speed of clearing.
- **Interactions.** V4 (capacity relative to pool is the actual ratio), V17 (transit determines how much
  of the metro can reach the door), V8 (a large metro has more competing events by construction, so the
  two must not both enter as raw counts).
- **Measurement.** Continuous or rank; join on city name, which is free text in the contract.
- **Data source.** Census / DMA tables, free.
- **Availability.** Not in the contract; free external.
- **Update frequency.** Annual (static enough to treat as a constant).
- **Temporal correctness.** **P+R**.
- **Predictive value.** Medium, and mostly as the denominator of V8.
- **Evidence.** **B**.
- **Leakage / endogeneity.** None. Caution: it is collinear with several rejected candidates (§4.2
  tourism flows, convention calendars), which is a reason to keep this one and drop those.
- **Priority.** **2**.

### V8 `competing_supply_same_night` — priority 2, class D

- **Definition.** Count of other ticketed events in the metro on the same local date, with a distance and
  a size weighting.
- **Mechanism (through demand and liquidity).** Substitutes in one entertainment budget and, harder, in
  one calendar night. A competing show does not just split spend; it removes buyers from the resale pool
  at the same hour, so it cuts transaction probability as well as price.
- **Expected effect.** **−**.
- **Interactions.** V7 (a count is meaningless without pool size), V9 (routing substitutes are the same
  mechanism at inter-city distance), V11 (the calendar creates the collision).
- **Measurement.** Count from the event catalogue, restricted to a metro radius and a same-local-date
  window, excluding the event itself and its own venue's other dates.
- **Data source.** Ticketmaster Discovery API v2, free key, 5,000 calls/day.
- **Availability.** Not in the contract. Obtainable.
- **Update frequency.** Daily at most; weekly is enough for a 1–10 week horizon.
- **Temporal correctness.** **R** in general and **P** only on a case-by-case basis: competing events are
  often announced after this event's on-sale, so the value is knowable at `t` but was not knowable at
  on-sale. Use only those announced by the decision time.
- **Verdict as 03-b records it (§3.1 A20): P**, conditional: "a show announced after `T1` was invisible at
  D1. The set as of D3 is the eventual set, so the collection must be dated." The R above and A20's
  conditional P are the same statement about an undated versus a dated collection; R is kept as the
  default because nothing in either file measures an announcement-date distribution. §8.6, row 2.
- **Predictive value.** Medium. 01-d §5 calls it the cleanest instrument-adjacent variable in the set,
  because other promoters' routing decisions are not caused by our price — which is why it is worth
  collecting even though its expected effect is small.
- **Evidence.** **D**.
- **Leakage / endogeneity.** No leakage if filtered to announcements before `t`; the announcement date is
  the variable's own censoring date and must be stored.
- **Priority.** **2**.

### V9 `tour_routing` — priority 2, class D

- **Definition.** For the same attraction: distance to the nearest other stop and the date gap; flags for
  one-off, residency, final stop, festival.
- **Mechanism (through supply and price expectations).** Substitution versus scarcity, and the two have
  opposite signs in the same variable. A stop 200 km away three nights later cannibalises: a fan will
  travel rather than pay a markup. A final stop or a one-off residency has no substitute at any distance,
  so it raises travel demand and removes the buyer's alternative.
- **Expected effect.** **−** inside roughly 300 km and 7 days; **+** for final stop and one-off.
- **Interactions.** V8 (same substitution logic at a different distance), V7 (travel willingness scales
  with the origin's market size).
- **Measurement.** Attraction id from the catalogue, geocode both venues, compute great-circle distance
  and date difference; a hand-set flag for the special cases.
- **Data source.** Ticketmaster Discovery (attraction records and cross-IDs) plus geocoding.
- **Availability.** Not in the contract.
- **Update frequency.** Weekly; re-checked whenever a new stop appears.
- **Temporal correctness.** **R** for most events and **N** for the primary-price problem on any stop
  added after on-sale: stops are added after the primary on-sale, so the value at on-sale was smaller
  than the value now. Use only stops announced by `t`.
- **Verdict as 03-b records it (§3.1 A21): P**, conditional, and sharper than A20's: "the *completed*
  routing is the future. Added dates are the classic version of this leak." R is kept as the default for
  the reason given under V8. §8.6, row 2.
- **Predictive value.** Medium.
- **Evidence.** **D**.
- **Leakage / endogeneity.** Announcement-date censoring, same as V8. A second subtlety: the promoter's
  routing decision and the primary price are joint decisions by the same firm, so on events by our own
  organisers this is not exogenous.
- **Priority.** **2**.

### V10 `artist_or_team_state` — priority 3, class B on attendance / D on price

- **Definition.** Injuries, suspensions, lineup changes, standings, championship contention, playoff
  implications, player transfers.
- **Mechanism (through buyers and WTP).** A shock to expected quality *and to its variance*. Quality
  moves willingness to pay directly. Variance moves option value: a title race raises prices even when
  the product on the field is unchanged, because the game now decides something. That second channel is
  why this is not just a quality proxy.
- **Expected effect.** **+** on a positive quality surprise; sign ambiguous for a variance shock that
  cuts both ways.
- **Interactions.** V1 (a shock lands with different force at 10 days and at 10 hours), V2 (contention
  drives sell-through), V12 (weather and team state are both day-of demand shocks and will be collinear
  at short horizons).
- **Measurement.** Standings and schedule from a scoreboard endpoint; injuries from the same or from
  news text, which is unstructured and must be read as class D.
- **Data source.** ESPN `site.api.espn.com` JSON, keyless, verified responding. **Undocumented**, so a
  commercial product needs a licensed feed; the legal risk is real and 01-d did not read ESPN's ToS.
- **Availability.** Not in the contract.
- **Update frequency.** Live for scores; daily for injuries.
- **Temporal correctness.** **R** for most events, and it is the clearest example of the clock ruling:
  for most events the shock resolves **after** the primary on-sale, so it is a repricing variable, not a
  pricing one. Every observation must carry the timestamp at which the information became public, not the
  timestamp of the game it describes.
- **Predictive value.** Medium for sports, low for music.
- **Evidence.** **B** on attendance, **D** on price. 01-d §5 treats it as one of the three genuinely
  causal variables — an injury is not caused by prices — with that class caveat attached.
- **Leakage / endogeneity.** Severe look-ahead if a game's result is joined to a pre-game price. The
  variance channel is the useful one and the hardest to measure.
- **Priority.** **3**. 01-d's conditional: if the inventory turns out sports-heavy, this moves to second
  place, and that is a strategy question for the operator, not a research one.

### V11 `event_calendar_structure` — priority 3, class B

- **Definition.** Event local weekday and start hour; public holiday flag; school-term flag.
- **Mechanism (through buyers, as a constraint on attendance).** Competes for the same leisure slot and
  sets travel feasibility. A Tuesday 20:00 show and a Saturday 20:00 show have different walk-up pools
  even in the same venue with the same act, because the buyer's cost of attending includes a next-morning
  constraint that is not in the ticket price.
- **Expected effect.** Small, positive for Friday/Saturday and holidays, negative for a school-night
  weekday.
- **Interactions.** V8 (a collision only matters for events that share a slot type), V12 (a holiday
  outdoor show has a different weather exposure).
- **Measurement.** Calendar join on the venue's local date. Requires converting UTC `startsAt` to local
  time, which the contract does not carry — a real trap: a 02:00Z start is the previous evening in
  Toronto.
- **Data source.** Static calendar tables, free.
- **Availability.** Not in the contract.
- **Update frequency.** Static.
- **Temporal correctness.** **P+R**.
- **Predictive value.** Low to medium.
- **Evidence.** **B**.
- **Leakage / endogeneity.** None, but note that school terms and holiday weeks as separate candidates
  are folded in here rather than admitted twice (§4).
- **Priority.** **3**.

### V12 `weather_forecast_outdoor` — priority 3, class B

- **Definition.** The forecast issued at `t` for the venue's coordinates on the event date, outdoor
  venues only.
- **Mechanism (through demand and the cost of attending).** Day-of attendance cost. Rain, extreme heat
  and snow raise the cost of going, which cuts walk-up demand and raises no-show risk. Critically, this
  is a **quantity** variable, not a price variable: 01-d §4 is explicit that the published result is on
  attendance and that nothing in that literature says a rained-on concert's resale *price* moves. The
  mechanism is weaker for price because a ticket already sold is a sunk cost, and a no-show does not
  destroy the ticket's value to someone still willing to stand in the rain.
- **Expected effect.** Rain **−** on attendance, small on price. Heat ambiguous. **Indoor venues: the
  coefficient is zero by construction, and the honest value is zero, not small.**
- **Interactions.** V6 (weather is a mechanism violation indoors — this is the gate), V1 (the forecast
  only exists inside the forecast horizon, so this variable's availability is itself a function of τ),
  V10 (both are short-horizon demand shocks and will be collinear at day-of).
- **Measurement.** Hourly forecast for the point nearest the venue, taken from the vintage issued at the
  decision time. Store the issue time alongside the value.
- **Data source.** NOAA/NCEI (public domain, free) preferred over Open-Meteo because the commercial
  licence problem disappears; Open-Meteo's free tier is non-commercial only.
- **Availability.** Not in the contract.
- **Update frequency.** Hourly, but only usable from the first forecast issue onward, i.e. inside the
  weather horizon.
- **Temporal correctness.** **R** for the reprice model. **Not P**: for an on-sale months ahead there is
  no forecast, only a climate base rate, and the climate base rate is a different variable. Using
  observed weather instead of the forecast is contamination by the outcome.
- **Predictive value.** Low to medium, outdoor only.
- **Evidence.** **B**: rainfall as a transitory shock to attendance cost, with habit effects, from
  Ge, Humphreys & Zhou (2020), *Journal of Sports Economics* 21(3):304–322, MLB attendance with NOAA data.
- **Leakage / endogeneity.** Forecast-versus-realised is the whole risk. Never join observations.
- **Priority.** **3**.

### V13 `album_or_release_timing` — priority 3, class D

- **Definition.** A new album, single, film or award within ±8 weeks of the event date.
- **Mechanism (through WTP).** Refreshes salience and adds setlist novelty, which is precisely what a
  resale buyer is paying for — they are buying a specific night of a specific tour, and a fresh record
  changes what that night contains.
- **Expected effect.** **+**.
- **Interactions.** V10 (the music analogue of team state), V9 (a record cycle is what creates the tour).
- **Measurement.** Release-date join on the attraction, restricted to announcements made before `t`.
- **Data source.** MusicBrainz / Wikidata, free; release calendars.
- **Availability.** Not in the contract.
- **Update frequency.** Weekly.
- **Temporal correctness.** **P+R** when the release was announced before on-sale; **R** when it was
  announced after. Release dates also move, so the announced-at-`t` date is the only usable one.
- **Predictive value.** Low.
- **Evidence.** **D**.
- **Leakage / endogeneity.** Announcement-date censoring; a postponement is a shock that is accidentally
  informative about the artist's state.
- **Priority.** **3**.

### V16 `macro_conditions` — priority 4, class B

- **Definition.** Real disposable income, consumer confidence, live-entertainment spend, ticket-price CPI.
- **Mechanism (through the budget constraint).** Sets the level of the buyer's budget and the price of the
  outside option. Real, but it moves every event in the panel at once, so within a season it cannot
  explain any cross-sectional price difference — its identifying variation is time-series, and the
  panel is thin in time.
- **Expected effect.** **+**, negligible within-event.
- **Interactions.** V7 (local income is the version that could vary cross-sectionally; national income
  is a deflator).
- **Measurement.** Index construction with a declared base; use ALFRED vintages.
- **Data source.** FRED / ALFRED, BLS. Free, public domain.
- **Availability.** Not in the contract.
- **Update frequency.** Monthly/quarterly.
- **Temporal correctness.** **P+R** in principle, **N** as published: the series are **revised after
  first publication**, so using today's series for a past decision is look-ahead. Use the vintage.
- **Predictive value.** Low. A deflator, not a feature.
- **Evidence.** **B**.
- **Leakage / endogeneity.** Revision look-ahead (the specific hazard), and collinearity with everything
  else that moves over time, including our own pricing.
- **Priority.** **4**.

### V17 `transit_and_access` — priority 4, class D

- **Definition.** Station proximity, service alerts, strikes, closures, parking price.
- **Mechanism (through the all-in cost of attending).** Transit changes the effective cost of the night
  out, so it moves the buyer's reservation. But the static part is absorbed entirely by a venue fixed
  effect, so only **shocks** carry information: a strike or a line closure on the event date.
- **Expected effect.** **−** on a cost shock.
- **Interactions.** V7 (transit determines how much of the metro can reach the door at all), V11 (a
  late-night event with no service is a different object).
- **Measurement.** GTFS static for proximity; GTFS-RT or agency alert feeds for shocks.
- **Data source.** GTFS / GTFS-RT, free, coverage uneven; many agencies publish no real-time alerts.
- **Availability.** Not in the contract.
- **Update frequency.** Static for proximity; ad hoc for alerts, with no clean feed.
- **Temporal correctness.** **R** for shocks (strikes are announced days ahead, so they are knowable), but
  **N** for most events in practice because shocks are rare and unaligned with event dates.
- **Verdict as 03-b records it (§3.1 A28): P**, note "Weak, and static". The row above is the stricter
  reading of the same object; 03-b's table is about the static part, which a venue fixed effect absorbs,
  and the registry's R is about the shock part. §8.6, row 3.
- **Predictive value.** Low.
- **Evidence.** **D**.
- **Leakage / endogeneity.** None material; the failure mode is a near-empty feature that costs a
  pipeline and returns nothing.
- **Priority.** **4**.

---

## 3. Group 3 — not obtainable today, decisive if it existed

Four entries: the two the findings single out, plus two that arrived through the other records and belong
in the same bucket for the same reason — each is an absence in the contract that caps what the engine can
claim, not a modelling choice.

### V15 `seat_coordinates` (seat_quality) — priority 0, class A

- **Definition.** Section, row, seat for each ticket, and the quality index built from them (distance to
  stage/pitch, elevation, sightline obstruction, aisle).
- **Mechanism (through WTP, and through within-event price dispersion).** Proximity and sightline are what
  a buyer is actually choosing between when two tickets in the same event differ in price. Without them,
  "quality" is a tier label and every within-tier difference is noise. The channel is direct: seat
  quality enters willingness to pay, and it is the axis on which the resale spread is largest.
- **Expected effect.** **+** toward the stage/pitch; the dominant within-event coefficient.
- **Interactions.** Everything. V1 and V2 condition on tier, so a tier-only engine cannot express the
  within-tier variation that drives the resale spread; V5's per-ticket path mixes seats within a tier and
  therefore mixes quality into the price change; 01-b §4.1 notes that tier-level differencing removes the
  tier mean but not the within-tier mix, and §4.2 lists seat coordinates as the fix for exactly that.
- **Measurement.** Field read once present; otherwise a per-venue manual mapping from seating charts to
  section/row/seat coordinates.
- **Data source.** The platform's own ledger (the operator question Q1), or official seating charts per
  venue (manual, effort not money).
- **Availability.** **Not in the contract.** `Ticket` carries `tierId`, `serial` and a mint only.
  **Q1 is open**: `AGENTS.md` claims the ledger yields "markup distribution conditioned on section",
  which the contract cannot support, so either the internal ledger is richer than the wire contract or
  "section" means tier. Until Q1 is answered this is class D for every claim that uses it.
- **Update frequency.** Static per ticket.
- **Temporal correctness.** **P+R** (known at issue).
- **DROPPED at both decision times (03-b B05).** "**Dropped, absent.** `F-decision-log` Q1. Strongest
  within-event axis in the published literature and unexpressible here." The P+R verdict describes the
  value if the field existed; it is not a claim that anything can be computed. Class **A** for the axis,
  **D** for any claim we make, as below. §8.3.
- **Predictive value.** **Very high** — 01-d ranks it as the strongest within-event price axis in every
  published ticket study.
- **Evidence.** **A** for the axis itself; class D for any claim we make using it, because we cannot
  compute it.
- **Leakage / endogeneity.** None in the value. Note the interaction with price: a ticket that sells twice
  is a ticket whose seat is revealed, so seat coordinates are more likely to be observed on the liquid
  subset.
- **Priority.** **0** — blocked on Q1. The one thing to try first is the operator question, not a model.

### V14 `secondary_listing_depth` (listing_depth) — priority 0, class C

- **Definition.** Count of simultaneously listed tickets at `t`, its change over the last 24h/7d, and the
  ask distribution across those listings.
- **Mechanism (through liquidity, supply, and transaction probability).** The quantity axis of the market.
  Depth is the number of competing offers standing between a buyer and a seller, so it drives the arrival
  rate of a match at a given price. Without it, "no sale" cannot be separated into "no buyer at this
  price" from "nothing was ever offered" — and that distinction is the entire sale-probability component.
- **Expected effect.** **−** on price as depth rises (more competing supply), **+** on transaction
  probability at any given ask.
- **Interactions.** V5 (a trail is not a market), V1 (depth is what the seller's hold-or-list decision
  acts on), V3 (a cap can hold depth high while price sits at the ceiling), and 01-b's T3, where the sale
  hazard is unrecoverable without it.
- **Measurement.** Per listing event: `{listPriceLamports, listedAt, delistedAt | soldAt, delistReason}`.
  Aggregate to depth as a counting process over live listings.
- **Data source.** The platform. Four fields, no external source exists.
- **Availability.** **Not in the contract** (`00-data-situation.md` Gap 1; D3). `Ticket.status =
  "listed"` is a current state, not a history: no start time, no ask, no revision trail, no withdrawal,
  no view count.
- **Update frequency.** Event-driven, per listing change. Anything coarser destroys the hazard.
- **Temporal correctness.** **P+R**, and it is the variable that makes the difference between the two
  decision times measurable rather than assumed.
- **DROPPED at both decision times (03-b D02).** "**Absent.** `01-d`: worth more than every external
  variable combined, and unobtainable." The P+R verdict is what the variable would be if the platform
  recorded listings; no estimator substitutes for the absence. Priority stays 0. §8.3.
- **Predictive value.** **Very high, the highest in the registry.** 01-d §7 states it plainly: listing
  depth and ask outrank every external source combined, and both are free to collect once the platform
  writes them.
- **Evidence.** **C**. The literature states the fix exactly — a case-cohort design measures the
  expensive time-varying covariate on all cases plus a random subset of the risk set (Prentice 1986), and
  the thing the schema lacks is that random subset of asks.
- **Leakage / endogeneity.** No leakage once collected. Endogeneity is intrinsic and must be carried into
  the model: the ask is chosen by the seller, plausibly on private information about value, so regressing
  sale on price traces neither demand nor supply but the locus of their intersections (Working 1927).
  The ask is an endogenous regressor even when observed — the absence is a data problem, the endogeneity
  is a modelling problem, and fixing the first does not fix the second.
- **Priority.** **0** — blocked on D3's data request. 01-d and 01-b both rank this as worth more than any
  modelling choice in the programme.

### `fee_model` — priority 0 as an input, decisive for the primary optimum (class C)

- **Definition.** Platform fee, creator royalty, payment processing cost, and net-to-seller, as a
  structure (`per-unit` and `ad-valorem` components) rather than a single number.
- **Mechanism (through sellers and through the buyer's total cost).** Two channels with different
  weights. On the **resale ask** an ad-valorem fee is neutral: with net `p(1−φ)`,
  `argmax_p p(1−φ)h(p) = argmax_p p·h(p)`, so the fee does not move the recommendation (01-b §4.5(i)).
  On the **primary optimum** it is not neutral: it shifts the buyer's total cost and therefore the demand
  that clears the primary, and it changes participation. A per-unit fee and an ad-valorem fee give
  different optima.
- **Expected effect.** Neutral for the resale mark; **−** on the optimal primary price as fees rise for a
  given net target, with the magnitude set by the fee's shape.
- **Interactions.** V3 (a cap plus a fee is a two-sided truncation), V2 (fee shifts demand, sell-through
  responds, so the two are jointly determined), and the whole Phase 5 objective, which is *net*.
- **Measurement.** Symbolic. Carry `φ` (ad-valorem) and `κ` (per-unit) through the derivation and expose
  them in the optimiser's interface.
- **Data source.** Operator-supplied configuration. **Nothing in the contract**: money appears only as
  `priceLamports` and `markupBps`, with no fee, royalty, processing cost or net field anywhere (Gap 4).
- **Availability.** Absent. D4 decides how it is handled: parameter, not assumption — do not assume zero
  and do not assume ad-valorem-only.
- **Update frequency.** Per configuration change, not per observation.
- **Temporal correctness.** **P+R**. It is a parameter of both decisions.
- **Predictive value.** Not a predictor. It is a boundary condition on the answer, which is why it is
  recorded here rather than only in `F`.
- **Evidence.** **C** (the neutrality result is a one-line derivation, not a measurement). The claim that
  the fee structure *matters* for the primary optimum is **C** as well, with no ticket-market measurement
  behind it.
- **Leakage / endogeneity.** None. The hazard is the opposite: silently assuming zero and reporting an
  optimum that is wrong in a direction nobody stated.
- **Priority.** **0** as an input, blocking the primary-price deliverable; 01-b §5 narrows it — this
  belongs in the optimiser's interface, not on the blocker list for the resale model.

### `demand_side_record` (bids, offers, views, searches) — priority 0, class C

- **Definition.** Any record of the buy side: bids, offers, listing views, saved searches, waitlist
  entries, failed purchase attempts.
- **Mechanism (through demand and WTP, directly).** Every other variable in this registry observes either
  a price that cleared or a quantity that sold. A bid observes a buyer's willingness to pay *without*
  requiring a transaction, which is the difference between measuring the demand curve and measuring its
  intersection with supply.
- **Expected effect.** Unknown and that is the point: it converts an assumption into an observation.
- **Interactions.** V14 (depth without bids is supply with no counterpart), V2 (primary sell-through is
  the one censored demand object we have; bids would uncensor it), and 01-b's T4b, where demand is not
  identified from trades at all.
- **Measurement.** Undefined until it exists; a log of any request that expresses intent without
  completing.
- **Data source.** The platform.
- **Availability.** Absent. Not even an absence in the contract's schema — there is no field to be
  missing.
- **Update frequency.** Continuous.
- **Temporal correctness.** **P+R** if logged; **N** otherwise.
- **DROPPED at both decision times (03-b D03).** "**Absent.** Every demand statement in the programme rests
  on assumption (`01-b` §6)." Priority stays 0. §8.3.
- **Predictive value.** 01-b §6(3) is uncompromising: the bid side is the single most valuable absent
  observation in the programme, and no amount of econometrics substitutes for it.
- **Evidence.** **C** (identification argument), not a measurement.
- **Leakage / endogeneity.** None intrinsic. Note that a view log is a *selection* of who looked, not of
  who wanted, so it validates nothing on its own.
- **Priority.** **0**. Recorded here so it is not lost; it is the fourth item on 01-b's data-requirement
  list, after the four listing fields, the fee figures and seat coordinates.

---

## 4. Group 4 — rejected, with the reason

Recorded so Phase 2D does not re-propose them. Each failed a specific test, named.

### 4.1 Rejected **from the primary-price problem** by the clock (retained elsewhere, conditionally)

These six are not worthless. They are worthless *at the on-sale*, because their value resolves after the
decision they would inform. 01-d's decisive filter was temporal, not correlational. Each is therefore
rejected as a primary-price feature and, where it survives at all, is admitted only in the reprice model
at the priority already assigned above. This subsection exists because the alternative is that they get
silently dropped and then re-proposed.

| # | Rejected as | Reason | Where the residual lives |
|---|---|---|---|
| X1 | `weather_forecast` at on-sale | No forecast exists months ahead, only a climate base rate; and the base rate is a different variable with a different (much smaller) mechanism. Using observed weather instead is contamination by the outcome. | V12, reprice only, outdoor only, priority 3. |
| X2 | `injuries` and team state at on-sale | The injury has not happened. A pre-season injury report is known but the informative shock is not, so the feature would be a proxy for last season's state. | V10, reprice only, priority 3. |
| X3 | `player_transfers` at on-sale | Transfers resolve in windows that mostly close after the primary on-sale for the affected fixtures, and the transfer itself is a joint decision by clubs and the league, not an exogenous shock at the moment we price. | V10, reprice only, priority 3, and with the exogeneity caveat stated. |
| X4 | `competing_events` at on-sale | Rival promoters announce after our on-sale, so the count at on-sale was not the count in market. The *mechanism* is admitted (V8, and 01-b calls it the cleanest instrument-adjacent variable); only its use at on-sale is rejected. | V8, reprice only (verdict R), priority 2. |
| X5 | `added_tour_stops` at on-sale | The value at on-sale was smaller than the value now, by construction. Using the final routing is look-ahead: it tells the model which events turned out to have nearby substitutes. | V9, reprice only, filtered to stops announced by `t`, priority 2. |
| X6 | `support_act_announcement` | Announced after the primary on-sale, and the only source is unstructured press, so it has no distribution and no counterfactual. Sound mechanism — a weak support act can reduce value and a strong one add it — but no admissible source at any horizon. | Nowhere today. Recorded as **D**, priority 4. Revisit only if a structured announcement feed appears. |

### 4.2 Rejected outright

| # | Candidate | Reason for rejection |
|---|---|---|
| X7 | Google Trends search interest | **Unavailable lawfully**, and weak on mechanism. No official API; `trends.google.com/robots.txt` disallows `/explore?` and `www.google.com/robots.txt` disallows `/trends/api` and `/trends/explore?` — precisely the endpoints every scraper uses. Google's ToS prohibit automated access in violation of the machine-readable instructions on its pages. Even if collected: it is a forecast of a demand that the platform already observes directly, so the incremental information is near zero. Class **E** in practice, D at best. |
| X8 | X/Twitter post volume and sentiment | Same redundancy, plus cost and retro-deletion. Pay-per-usage: $0.005 per Post read, $0.010 per User read, 3M reads/monthly cycle cap — roughly $150/month at 1,000 posts/day, ~$1,500/month at 10,000. Deleted posts vanish retroactively, so the series is not reproducible. On a 1–10 week horizon the sentiment signal is dominated by the market's own price. **E**. |
| X9 | Reddit volume and sentiment | The Data API terms reserve fees, require a separate agreement for commercial use, forbid deriving revenues from the API without written approval, and grant **no right to use user content for training an ML model** without rightsholder permission. That last clause forbids the exact use the engine exists for. **E**, rejected on licence. |
| X10 | Spotify listeners / artist popularity | The Web API reference marks `popularity` and `followers` on the artist object **deprecated** (`audio-features` too), and the platform's policy states content may not be used to train a machine learning or AI model or be ingested into one. Also a listener count is a stock, not a shock. Rejected on licence, not on mechanism. **E**. |
| X11 | YouTube view velocity | No public velocity API; scraping runs into the same robots/ToS logic as X7; and the mechanism (awareness) sits upstream of a variable we already observe. **E**. |
| X12 | Artist death, scandal, cancellation | Real price events, well covered by journalism, but they are point shocks with no distribution and no counterfactual, so nothing is estimable from them. Keep as a **hand-set override for the operator**, never a feature. **E**. |
| X13 | Airport proximity, parking, road layout | Static per venue, therefore absorbed entirely by a venue fixed effect. Zero incremental information by construction, regardless of how good the data is. |
| X14 | Tourism flows, convention calendars | Monthly, metro-level, and collinear with V7 city market size, which is free. A second variable that measures the same thing as a cheaper one adds variance, not information. |
| X15 | School terms and holiday weeks as a separate variable | The mechanism exists but it is a strict subset of V11, which already carries the holiday flag. Folded in, not admitted twice. |
| X16 | Weather at indoor venues | The coefficient is zero by construction. Including it is a mechanism violation dressed as a feature, and it would let the model attribute a spurious coefficient to an unrelated indoor event's noise. |

### 4.3 Rejected for reasons that came from 01-b rather than 01-d

Two that a registry would otherwise be tempted to admit because the data looks like it is there.

| # | Candidate | Reason for rejection |
|---|---|---|
| X17 | `listing_price` as observed on sales, fitted as `λ(p)` | Dangerous precisely because it will look estimable. The mark is recorded only on the success branch, so `λ_obs(p,t) = λ(t∣p)·π(p∣listed,t)·s(t)` and nothing separates the three factors. A model fitted this way traces which sellers chose which prices, not demand. **D**, and the failure is silent: it will look monotone and well-behaved. The fix is V14, not a better estimator. |
| X18 | Wallet clustering as a proxy for a single seller | Bitcoin-style clustering relies on UTXO co-spend; Solana is account-based, so it does not transfer. What is available is weaker and should be used as such: a repeat reseller appears as the same `fromWallet` across tickets, and `issuedToWallet` links primary to secondary counterparties with no inference. Repeat-reseller behaviour is **partially identified**; whether two wallets are one person is **not identified**. |

---

## 5. Variables the contract carries that no finding has yet classified

`01-d` was written before `01-b` and neither was written to exhaust the schema. These are contract fields
that carry information and sit in no table above. Each is listed with the same fields, in compressed form,
and every one is flagged as **unclassified by a finding** — the class is this pass's reading, and a Phase 2
agent should confirm or overturn it. This is the honest state: a field existing is not a variable being
understood.

### 5.1 Explicitly checked against the four claims in `AGENTS.md`

`AGENTS.md` asserts the ledger yields four things that scraped ticket datasets do not. The contract's
actual support for each:

| Claim in `AGENTS.md` | Supportable from the wire contract? | On what, and what breaks |
|---|---|---|
| **Time between custody hops** | **Yes**, with one caveat. | `LedgerEntry.occurredAt` (ISO-8601 UTC) and `slot` (strictly monotone) on every row, ordered per `ticketId`. Caveat: `occurredAt` is ISO-8601 "at unspecified granularity" while `slot` is strictly monotone, so any hazard model must derive its time index from `slot` or risk negative and tied durations (01-b §4.6(c)). Aggregates like `ResaleStats.uniqueWallets` and `Ticket.transferCount` also exist but are computed over the whole life of the ticket, i.e. they are forward-looking. |
| **Repeat-reseller behaviour** | **Partially.** | `fromWallet` recurring across tickets, and `issuedToWallet` linking primary to secondary counterparties with no inference. But wallet ≠ person: Solana is account-based and co-spend clustering does not transfer (X18). So "this wallet resold 40 tickets" is supportable; "this is a broker" is an assumption. |
| **Holding duration** | **Yes.** | First entry to sale entry, and issue to `redeemedAt` for the never-sold. Must be truncated at `t`. Also the object that matters for supply pressure — a consumer-held ticket is not on the market, so duration is the observable proxy for the seller's outside option (V5's mechanism). |
| **Markup conditioned on section, and on time-to-event** | **Time-to-event: yes. Section: no.** | `markupBps` is per ticket, measured against that ticket's own tier face (verified in `00-data-situation.md` §2, including the warning not to re-derive event-level markup), and can be bucketed by `startsAt − occurredAt` with no problem. Section does not exist in `Ticket`. The finest available stratification is `tierId`. Either the company's ledger has coordinates (Q1) or `AGENTS.md`'s "section" means tier, and until Q1 is answered the claim is unsupported. |

### 5.2 Contract fields with no finding behind them

| Field | What it would be, and the mechanism | Availability and gate | Verdict |
|---|---|---|---|
| `TicketTier.faceValueLamports` (tier face value) | The primary price level, and the denominator of every markup. Mechanism: it is the anchor the buyer compares the resale ask against, so it sets what "expensive" means; and in 01-b's T4b it is *assumed equal to the primary transaction price*, which is a load-bearing assumption, not a field fact. | Present. **Endogenous** — it is the primary seller's choice (01-b §4.1) and the denominator of the measure, so a model regressing markup on face reads its own pricing back. | **Unclassified by any finding.** Use as a normaliser (all markups are already in bps) and as a stratum, never as an exogenous regressor. `D` until 01-b's T4b assumption is checked with the operator. |
| `Ticket.serial` | A human-facing label, `"GA-0142"`-shaped. Mechanism: none directly. | Present. | **Unclassified, and almost certainly an identifier, not a feature.** Worth one check: if the prefix encodes tier and the numeric part is issuance-ordered, then serial ordering is a weak proxy for arrival time at on-sale, which is a demand signal. That is **`E`** — a hypothesis, recorded so it is not lost, and it must not be used until someone verifies the encoding with the operator. |
| `Event.status` (`draft`/`on_sale`/`sold_out`/`completed`/`cancelled`) | Mechanism: on-sale and sell-out are the gate that determines whether a resale market exists at all, and `cancelled` is a terminal zero. | Present, but **transitions are not timestamped** (`00-data-situation.md` §4). | **Unclassified.** Usable as a current-state filter; unusable as a timing variable, and it cannot substitute for the missing on-sale time. Confirmed absence, not an inference. |
| `Ticket.lastSalePriceLamports`, `Ticket.transferCount`, `Ticket.status`, `Ticket.redeemedAt` | Ticket-level states and outcomes. `redeemedAt` is a terminal state and therefore a competing risk for the sale hazard, not a censoring time (01-b §4.3, Fine & Gray 1999). | Present. | **Unclassified as a block, and the block is the future.** Every one is a summary over the whole ticket life, so using any of them at time `t` leaks. `redeemedAt` is admissible only as a competing-event indicator once it has occurred. Class `C` for the survival reading; no finding has said so in the registry. |
| `Organizer.id`, `walletAddress`, `verified` | Mechanism: the organiser sets face, cap and restrictions, so organiser identity is a bundle of policy choices, and `verified` may separate professional promoters from one-offs. | Present. | **Unclassified.** `D`. The real caution is that organiser identity will absorb most of the policy variation, making `resalePriceCapBps` look less important than it is unless both enter. |
| `Event.venue`, `Event.city` (free text) | Join keys to V4, V6, V7, V17. Mechanism: none on its own. | Present as strings. | **Unclassified, and a silent failure point.** Every Group 2 variable is gated on normalising these two strings. A name mismatch drops a row and nothing reports it. Recommend a venue-normalisation table as the first artefact of Phase 2D. |
| `Event.endsAt` | Event duration. Mechanism: a festival or a double-header is a different product from a two-hour show. | Present, nullable. | **Unclassified.** `D`, low value. |
| `Event.name`, `description`, `slug`, `imageUrl` | Text and media. Mechanism: an unstructured source of classification (genre, tour identity, whether the listing is a festival). | Present. | **Unclassified.** `E`. Not proposed as a feature; recorded so it is not accidentally used, and because it is the cheapest route to genre once someone builds a classifier. |
| `LedgerEntry.signature`, `slot` | Transaction identity and strict ordering. | Present. | **Unclassified as a variable, load-bearing as a clock.** `slot` is the only strictly monotone time index; the hazard model must be built on it (01-b §4.6(c)). Not a feature, a prerequisite. |
| `LedgerEntry.priceLamports` null on `transfer` | A custody hop with no money. Mechanism: gifts, reissues, and related-party sales. | Present, and the null is informative. | **Unclassified.** 01-b §4.6(a): a related-party sale at exactly face is indistinguishable from a market one, so if gifts are coded as sales the observed resale propensity is **too high** and mean markup **too low** — which makes the never-offered fraction an upper bound. `C`, and it changes how every Group 1 count should be reported. |
| `ResaleStats`, `EventAnalytics` (derived aggregates: `avgMarkupBps`, `priceSeries`, `markupDistribution`, `resoldShare`, `uniqueHolders`, `totalVolumeLamports`, `topDestinations`, `DestinationRow.region`) | Pre-computed summaries over the same rows. | Present. | **Unclassified, and they should stay that way.** Using them adds no information over the rows they are computed from, and each is computed over the whole history, so each is a leakage hazard with a friendly name. `DestinationRow.region` is worse: it is present only when a wallet **voluntarily** attached a region, so it is a selected subsample with no stated denominator. |

### 5.3 Decision-time verdicts for the §5.2 fields, added in revision 2

§5.2 could not carry a verdict because no finding had classified those fields. `03-b` §3.1 to §3.3 now
classifies most of them, so the verdict is recorded here rather than inside the table above, which is left
as it was written. `P`/`R`/`N` are 03-b's letters (see §8.0 for the mapping to §0's vocabulary).

| Field (§5.2) | 03-b row | Verdict | Vintage | What that means here |
|---|---|---|---|---|
| `TicketTier.faceValueLamports` | A07 | **P** | S | At D1 this is the decision, not a predictor (`02-c` §3.7 lists it as a covariate at class B; 03-b's row is the stricter statement). Retained as the numeraire only, which is what §5.2 already says. |
| `Ticket.serial` / serial prefix | B03 | **P**, class **E** | S | Unverified hypothesis, exactly as §5.2 states. 03-b B03 keeps it at E and does not raise it. |
| `Event.status` (`draft`/`on_sale`/...) | A13 | **P** as a live flag, **K** | K | Usable "only as the live `draft`/`on_sale` pair read at `t`. A value read later is the eventual state." This confirms §5.2's "usable as a current-state filter, unusable as a timing variable". |
| `Event.status` terminal (`sold_out`, `completed`) as a D1 predictor | A14 | **N at D1, R at D2** | K | The one row in 03-b whose two verdicts differ: "the state is a fact about the future and carries no clock." Dropped at D1 only. §8.2 carries it as a row. |
| `Ticket.ownerWallet` as stored | B06 | **N** | A/K | Dropped as a field. Recoverable from the ledger as the last `toWallet` at or before `t`, which is C-group. |
| `Ticket.status` as stored | B07 | **N** | K | Dropped, and this is the exposure denominator §5.2 already says does not exist. |
| `Ticket.redeemedAt` | B08 | **N** | A | Dropped as a covariate; admissible only as a competing-risk exit once it has occurred, which is what §5.2 says at class C. |
| `Ticket.transferCount` | B09 | **N** as stored | A | Recompute from truncated rows (03-b C03, §8.1). |
| `Ticket.lastSalePriceLamports` | B10 | **N** as stored | A | Recompute (03-b C06, §8.1). |
| `Ticket.transferRestricted` | B11 | **N** | K | Dropped as a feature: "a consequence of policy plus the ticket's own history, and its stored value is chain state at D3." V3's policy block therefore rests on the event-level fields only; the ticket-level one is not usable. |
| `ResaleStats`, `EventAnalytics` scalars | C14, C15 | **N** | A | Dropped as features, legitimate as training labels on completed events. Confirms §5.2's "they should stay that way". |
| `DestinationRow.region` | C17 | **N** | A | Dropped: selected with no denominator. |
| `EventAnalytics.priceSeries` | C13 | **R**, the one exception | A | Usable only when filtered to complete UTC day buckets strictly before the cut (`03-b` §3.3: "The one aggregate that becomes usable, and only with the current day dropped"). This is the one place §5.2's "they should stay that way" is qualified. §8.1.13. |
| `DestinationRow.acquiredOnSecondary` | C16 | **N** | A | Dropped, derived from the current owner. §5.2 had not listed this one; 03-b does. |
| `Event.venue`, `Event.city` | A03 | **P** | S | Join keys only, as §5.2 says. |
| `Organizer.id`, `verified` | A04 | **P** for the id, **K** for `verified` | S / K | `verified` "is a state, not a date". |
| `Event.endsAt` | A02 | **P** | S | Fold construction and event duration only. §8.2. |
| `Event.name`, `description`, `slug`, `imageUrl` | not classified | no verdict | — | 03-b does not classify these and this pass does not either. |
| `LedgerEntry.signature`, `slot` | the clock | not a feature | H | Unchanged: a prerequisite, not a variable. |
| `LedgerEntry.priceLamports` null on `transfer` | not classified | no verdict | — | 03-b does not classify the null-transfers-as-gifts question; 01-b §4.6(a) still governs it. |

---

## 6. What this registry implies for build order

Not a plan — 01-d and 01-b already contain the plans. This is only what the grouping forces.

1. **Build the four Group 1 variables first, and log V2 at every scoring instant from the first day.**
   V2's availability is a snapshot with no history, so the series that makes it usable is created by us or
   not at all. This is the cheapest high-value action in the registry.
2. **Build the truncated-trail discipline before building any trail feature** (V5). A truncation bug here
   is silent, plausible, and produces a good-looking backtest.
3. **The venue table (V4, V6) is the first external artefact**, because it is free, static, and it is the
   denominator every other variable is measured against.
4. **Ask the operator three questions before writing any Group 3 code**: the four listing fields (Q1's
   neighbouring request, D3), seat coordinates (Q1), and the fee structure (D4). All three are absences,
   and no estimator substitutes for an absence.
5. **Group 2 is separable and parallelisable.** Nothing there blocks Group 1, and only V4 blocks the V1
   interaction from being interpreted.

---

## 7. Conflicts and cross-cutting notes, recorded not resolved

**C-1 — Gap 1's severity (01-d versus 01-b).** 01-d repeats the Phase 0 framing that without listing
exposure "the observed sale count is a numerator with no denominator". 01-b §5 establishes that the
denominator is present — every ticket has an `issue` row and a known life, so the at-risk set is censused
and the unconditional sale intensity **is** identified. What is missing is the *price of the risk set*: a
case-only sample with no controls, not a numerator without a denominator. The four-field fix is identical
either way, so the decision (D3) stands; only the diagnosis changes, and 01-b's is the more precise one.

**C-2 — The value of the sell-through snapshot (01-d versus 01-b).** 01-d grades V2 "severe leakage,
snapshot only, no history, no velocity", and 01-b §5 addition 4 argues the snapshot is *enough* for the
level, because velocity is not needed to identify the demand bracket — a Tobit with an observed censoring
indicator is the benign case. Both are right about different objects: the **level** is identified today,
the **velocity** is not, and neither is usable unless the value is logged at decision time. The registry
carries both statements in V2.

**C-3 — The value of the cap (00-data-situation versus 01-b).** The audit sees the truncation as a
nuisance that biases the top of the distribution. 01-b §5 shows the same object is an instrument: the cap
is observed, varies across events, ~~and varies across tiers within one event because it is bps over each
tier's own face~~ **[CORRECTION 2026-11-07T14:00Z, R2-25 — dead: `resalePriceCapBps` is a single field on
`Event`, so there is no within-event variation; only the implied money ceiling varies, as face × (1 + c),
collinear with face. The instrument is cross-event only. See the CORRECTION below.]**, so a mass point at the cap measures rationed *quantity* though not the latent tail's
location. The registry treats V3 as both, and 01-b's original point stands: **no class-A claim about caps
may appear in the deliverable**, ~~because no peer-reviewed study of resale price caps in ticket markets was
found~~ **[CORRECTION 2026-11-07T14:00Z, R2-26 — dead: one was found. `01-a` §3 cites He & Lin (2026),
*Marketing Science* 45(3):515–533, "Price Caps by Matching Platforms: The Case of Ticket Resales", which is
peer-reviewed and about exactly this object. The claim that survives is `01-b` §4.5's narrower one, "no
peer-reviewed **econometric** study", and whether He & Lin is econometric is unread by this programme. The
rule the sentence supports — no class-A cap claim in the deliverable — is unaffected and still binds.]**.

**C-4 — `AGENTS.md`'s first consequence.** `AGENTS.md` argues that because a resale here is a recorded
transaction, the asking-versus-realised part of Phase 2A is smaller than the literature implies. 01-d
accepted the first half; 01-b §5 sharpens it in the other direction: the ask is *entirely* absent from the
record, so there is no wedge to estimate at all, and the whole of Phase 2A's listing revision, duplicate
listing, seller competition and price-discovery block is unavailable rather than partially available.
Phase 2D must not be dispatched at that block as though it were merely thin.

**C-5 — How many are admitted, and a count that does not reconcile.** 01-d's headline is "nineteen
candidate variables were examined against §4.2 and eleven survive at usable priority", but its own
Table C-1 lists **seventeen** rows (V1–V17) of which **fifteen** carry a priority above 0 and two (V14,
V15) are at 0. The headline's 19 and 11 reconcile with neither reading of the table. Recorded rather
than smoothed over: no finding in the record explains the difference, and the table is the enumerated
artefact, so **this registry follows the table** and treats 01-d's abstract count as unverified.

Counts as they stand in this file: **4** admitted and usable today (V1, V2, V3, V5), **11** admitted but
only obtainable outside the contract (V4, V6–V13, V16, V17), **4** not obtainable today
(`seat_coordinates`, `listing_depth`, `fee_model`, `demand_side_record`), **18** rejected (X1–X18). Of
the four in the third group, only the first two come from 01-d's table; `fee_model` and
`demand_side_record` came from `00-data-situation.md` Gap 4 / D4 and 01-b §6 respectively. Nothing was
added on this pass's own authority.

**C-6 — Nothing here is measured.** Every expected effect in this file is a sign and a channel. No
coefficient in the registry has been estimated, nothing was computed on the fixtures, and no variable's
sign has been observed in our own data. The classes say what the mechanism rests on, not how strong it is.
Phase 6 tests each on data that does not yet exist.

---

## CORRECTION (2026-11-07T11:28Z) — C-3's within-event cap claim is withdrawn

Appended by the corrections pass after `records/findings/00-verification-round1.md` §C1. Nothing above is
deleted.

**Withdrawn text, C-3:**

> "01-b §5 shows the same object is an instrument: the cap is observed, varies across events, and varies
> across tiers within one event because it is bps over each tier's own face, so a mass point at the cap
> measures rationed *quantity* though not the latent tail's location."

**What is true.** `resalePriceCapBps: number | null` is a single field on `Event`; `TicketTier` carries five
fields and no cap (`../ticketing-frontend/lib/types.ts`). The basis-point cap does not vary within
an event. The **money ceiling** it implies does, as `faceValue_tier × (1 + c)`, which moves exactly in
proportion to the tier's own face and so carries no information independent of that face. There is therefore
no within-event *identifying* variation in the cap, and the instrument is a cross-event one.

`01-c-methods.md` §1.4(1) states this and is right; `records/D-model-registry.md` C6 and
`records/B-mathematical-kb.md` C6 already record `01-c`'s version.

**What stands in C-3.** The cap is observed rather than latent, it varies across events, a mass point at the
cap measures rationed quantity rather than value, and the audit's reading of the cap as a nuisance is
incomplete. V3's registry entry, which describes the cap as binding on price and rationing by speed, needs no
change. Nothing else in this file rests on the withdrawn clause.

**One question this correction does not settle.** C-3 closes with "no class-A claim about caps may appear in
the deliverable, because no peer-reviewed study of resale price caps in ticket markets was found".
`01-a` §3 cites He & Lin, *Marketing Science* 45(3):515–533 (2026), which is a peer-reviewed paper on price
caps in ticket resale. Whether it is an econometric study, which is the narrower bar `01-b` §4.5 sets, I did
not read and do not assert. The question is recorded in `records/CORRECTIONS-APPLIED.md`; no conclusion is
changed here.

**NOTE (2026-11-07T12:55Z) — C-3's closing clause is narrowed to `01-b`'s wording.** C-3 above ends "because
**no peer-reviewed study** of resale price caps in ticket markets was found". `01-b` §4.5 claims the narrower
thing, "no peer-reviewed **econometric** study", and `01-a` §3 cites He & Lin, *Marketing Science* 45(3):515–533
(2026), for a class-C theoretical proposition about caps. A peer-reviewed *model* of price caps in ticket resale
plus no peer-reviewed *measurement* of one satisfies both files. So read C-3's evidence clause as `01-b`'s:
**no peer-reviewed econometric study**, not no study. The rule it supports — "no class-A claim about caps may
appear in the deliverable" — is unaffected, is still correct, and is unchanged. The full distinction, with both
passages quoted and the one open question (is He & Lin econometric?), is `01-a-market-structure.md`'s NOTE of the
same timestamp. Nothing else in C-3 or in this file rests on the broader wording. **[CORRECTION
2026-11-07T14:00Z, R2-26b — that NOTE said the clause was narrowed; it was not, because a note below a sentence
cannot amend the sentence a reader meets first. C-3's closing clause is now struck in place (R2-26, above),
which is what this NOTE asks a reader to do, and the instruction to read it as "no peer-reviewed econometric
study" stands. `DELIVERABLE.md` §20.5 previously said the clause "is narrowed to `01-b`'s wording there"; that
sentence was false and was corrected at the same timestamp.]**

---

## 8. Revision 2 — the Phase 2 and Phase 3 inventory, with a decision-time verdict on every row

**Appended 2026-11-07T11:40Z.** Nothing above is edited by this section except the verdict lines added in
place (§8.6 names each). This section does three things §0 to §7 could not: it carries the variables the
Phase 2 and Phase 3 findings define and this registry did not have, it puts a decision-time verdict on
every one of them, and it records the rows `03-b` drops with the reason in one clause.

**What is in here, and from where.** §8.1 the ledger-derived block `03-b` §3.3 admits at D2, thirteen rows.
§8.2 five event, tier and ticket facts. §8.3 the fifteen rows `03-b` drops that had no row in this file, plus
the three it drops that did. §8.4 the twelve interaction features of `03-a` §4 as composite variables.
§8.5 the thirteen interactions themselves, which are not variables but are the reason several composite
variables exist. §8.6 where `03-b` restates or contradicts a verdict this file already carries, quoted.
§8.7 the counts after this revision.

### 8.0 Vocabulary, and the one place it differs from §0

`03-b`'s verdict letters are not §0's and must not be read as if they were. The mapping:

| `03-b` §3.0 | Meaning | §0 equivalent |
|---|---|---|
| **P** | knowable at or before D1, and therefore at D2 as well | **P+R** |
| **R** | knowable at a D2 instant `t`, not at D1 | **R** |
| **N** | knowable at neither without look-ahead; dropped, with the reason given | **N** |

**The three times, from `03-b` §2.** **D1** is the instant the organiser commits
`TicketTier.faceValueLamports` per tier, before the first `issue` row exists, and it happens once: the
contract has no price-mutation endpoint. Its replayable cut instant is `T1(e) = min{occurredAt : kind =
"issue" and the ticket belongs to e}`. **D2** is any `t` with `T1(e) < t < startsAt(e)`. **D3** is
extraction, the instant the payload was computed, which the contract never states; leakage is D3 information
entering a D1 or D2 decision and nothing else in the audit is a separate failure mode (`03-b` §2.3, §2.4).

**Vintage codes**, used in every row below: **S** static, **H** historical row (safe if and only if
truncated at the cut), **K** snapshot (must be polled and logged at `t` or it is look-ahead), **A**
aggregate over a window the contract does not state and not truncatable by the consumer.

**The clock rule, from `02-c` §3.1 and `03-b` §4 T1.** `slot` is the monotone index and `occurredAt` is the
fallback; a row whose `slot` is null is counted and logged, never assumed to sort. Every feature below takes
the cut instant as a required argument with no default.

**Priority.** `03-b` and `03-a` assign none, and the scale is `01-d`'s. Where a new row's priority is not
inherited from the registry variable it belongs to, the entry says so and marks the placement as this pass's
reading, in the manner §5 already uses.

---

### 8.1 The ledger-derived block, admitted at D2 (`03-b` §3.3, rows C01 to C13)

Every row here is vintage **H** by construction: the row carries its own `slot` and `occurredAt`, so a value
at `t` exists and is obtainable, provided the truncation happens before any aggregation. Each was either
absent from this registry or carried only inside V5's prose; V5's mechanism stands and is not restated.

#### 8.1.1 `prior_sale_count_event` (`03-b` C01) — priority 1, class not assigned

- **Definition.** Count of `sale` rows for the event with `slot < cut`.
- **Mechanism (through transaction probability and liquidity).** Market activity for the event as a whole,
  used as the level against which a tier's own count is read. `02-c` §3.7 classes ledger market-state
  covariates at D and gives them "market state; momentum".
- **Expected effect.** **+** on transaction probability at any ask, and it is the numerator of every
  observed rate; no sign on price is claimed by any source.
- **Interactions.** C02 (the same count at tier level), C12 (the hazard consumes it), the event panel that
  IF-08 needs.
- **Measurement.** A filtered count. Must be strictly `<` the cut.
- **Data source.** Contract: `LedgerEntry.kind = "sale"` grouped to the event through the ticket.
- **Availability.** Present per row.
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C01), vintage **H**.
- **Predictive value.** Not assessed by any source as a stand-alone predictor.
- **Evidence.** No finding assigns a class. The warning attached to it is not about evidence but about
  circularity: `03-b` C01's note is "using it for a ticket's own sale is circular".
- **Leakage / endogeneity.** The count is the label's numerator. Conditional on the event, it is also an
  outcome of `p0` (`03-b` §5 P3).
- **Priority.** 1 by inheritance: it is the denominator discipline every other ledger feature needs.

#### 8.1.2 `prior_sale_count_tier` (`03-b` C02) — priority 1, class not assigned

- **Definition.** The same count restricted to the ticket's tier.
- **Mechanism (through liquidity).** The tier is "the weakest defensible level of pooling" (`02-a` §8.6),
  and pooling below it mixes objects the cap truncates differently (`02-a` §6.2, last row).
- **Expected effect.** As C01, at the level the path model is actually fitted.
- **Interactions.** C01, C11, C12, V2 (tier-level sell-through is the tier's own rationing statement).
- **Measurement.** Filtered count keyed on `(event, tier)`.
- **Data source.** Contract: `LedgerEntry` joined through `Ticket.tierId`.
- **Availability.** Present.
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C02), vintage **H**.
- **Predictive value.** Structural: `02-a` §8.6's fallback ladder is indexed by it, and `02-a` §8.8's
  stratum counts are per tier.
- **Evidence.** No class assigned by a finding.
- **Leakage / endogeneity.** As C01, and it is the count that decides which rung of `02-a` §8.6's ladder an
  event is on, so a mistake here changes the reported interval width.
- **Priority.** 1, inherited as above.

#### 8.1.3 `hop_count_as_of_t` (`03-b` C03) — priority 1, class C

- **Definition.** Priced and unpriced custody hops for the ticket with `slot < cut`.
- **Mechanism (through sellers and supply).** V5's mechanism, unchanged: churn identifies the professional
  seller, whose presence raises offered quantity and compresses the ask.
- **Expected effect.** As V5: **+** on clearing speed, thinner margins on churned tickets.
- **Interactions.** V5, C04, C05, IF-10.
- **Measurement.** `03-b` C03 replaces `Ticket.transferCount` (B09, dropped as stored).
- **Data source.** Contract: `LedgerEntry.kind` in `{sale, transfer}`, per `ticketId`.
- **Availability.** Present per row.
- **Update frequency.** Each hop.
- **Temporal verdict.** **R** (`03-b` C03), vintage **H**. It supersedes the whole-life field, which is
  **N** (B09).
- **Predictive value.** "Selection on liquidity" (`02-c` §3.6): only tickets that transacted have hops.
- **Evidence.** **C** (`02-c` §3.7, "prior custody hops of this ticket as of `t`", class C).
- **Leakage / endogeneity.** The count is the outcome being predicted when the prediction is "does this
  sell". Truncation at the cut is the whole discipline.
- **Priority.** 1, by inheritance from V5.

#### 8.1.4 `holding_duration` (`03-b` C04) — priority 1, class C

- **Definition.** Time since the last hop, and the mean over hops, per ticket.
- **Mechanism (through sellers and supply).** V5: a long-held ticket is held by a consumer whose outside
  option is attendance, so its supply pressure is lower.
- **Expected effect.** **−** on supply pressure as duration rises (V5).
- **Interactions.** C03, V1 (a long-held ticket near expiry is a different object), IF-10.
- **Measurement.** Needs `slot` ordering, not timestamp ordering (`03-b` §4 T1); asserts no negative
  durations after sorting.
- **Data source.** Contract: `LedgerEntry.slot`, `occurredAt`, `Ticket.issuedAt`.
- **Availability.** Present.
- **Update frequency.** Each hop.
- **Temporal verdict.** **R** (`03-b` C04), vintage **H**.
- **Predictive value.** Carried as V5's second channel; no independent measurement.
- **Evidence.** **C**, as V5's mechanism.
- **Leakage / endogeneity.** Duration measured to a cut is safe; duration measured to the sale is the label.
- **Priority.** 1, by inheritance from V5.

#### 8.1.5 `repeat_reseller_features` (`03-b` C05) — priority 1, class B

- **Definition.** Prior sales by this `fromWallet`, with the wallet history truncated at the cut.
- **Mechanism (through sellers and supply).** "Repeat-reseller behaviour, one of the few ledger-native
  features" (`02-c` §3.7); professionals price to a schedule and cut earlier and deeper.
- **Expected effect.** **−** on level and on the slope, **+** on the hazard, as concentration rises
  (`03-a` I4).
- **Interactions.** C03, IF-06 (concentration is the aggregate of this row), V5.
- **Measurement.** Requires a wallet history built inside the fold, never a module-level index.
- **Data source.** Contract: `LedgerEntry.fromWallet`, `issuedToWallet`.
- **Availability.** Present, and **partially identified** as a person-level construct (V5, `01-b` §4.6(b)).
- **Update frequency.** Each sale by that wallet.
- **Temporal verdict.** **R** (`03-b` C05), vintage **H**.
- **Predictive value.** Named **class B** by `02-c` §3.7 and **the named trap of the programme** by
  `01-d` §4, which is `03-b` C05's own note.
- **Evidence.** **B** for the repeat-reseller behaviour; **C** for the wallet-identity result.
- **Leakage / endogeneity.** "A wallet index computed once over all rows is the whole leak, and it looks
  like a dictionary" (`03-b` C05). Endogeneity: which sellers transact is the outcome.
- **Priority.** 1, by inheritance from V5.

#### 8.1.6 `own_markup_path` (`03-b` C06) — priority 1, class C

- **Definition.** This ticket's realised markups up to the cut.
- **Mechanism (through price expectations, and as the measurement itself).** The only true per-ticket price
  observation the platform has (V5); it is what makes a repeat-sales read possible at all.
- **Expected effect.** No sign claimed. It is an input to the fitted path, not a regressor with a sign.
- **Interactions.** C11, C12, IF-07, V1.
- **Measurement.** Replaces `Ticket.lastSalePriceLamports` (B10, dropped as stored). Ordered by `slot`.
- **Data source.** Contract: `LedgerEntry.markupBps`, `priceLamports`, `slot`.
- **Availability.** Present.
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C06), vintage **H**.
- **Predictive value.** The dependent object of `02-a` §8's path model, `y = log(p/face)`.
- **Evidence.** **C**; the repeat-sales machinery it enables has class-A support for the estimator only.
- **Leakage / endogeneity.** The trap of §1's V5 entry, unchanged.
- **Priority.** 1, by inheritance from V5 and the path model.

#### 8.1.7 `tier_cumulative_volume` (`03-b` C07) — priority 2, class D

- **Definition.** Sum of prior sale prices in the tier, with `slot < cut`.
- **Mechanism (through liquidity).** "Market state" (`02-c` §3.7, class D).
- **Expected effect.** None claimed by any source.
- **Interactions.** C01, C02, C08.
- **Measurement.** The source attaches a warning rather than a formula: "a mean of ratios problem (§4 T7
  note): sum of prices is not a value".
- **Data source.** Contract: `LedgerEntry.priceLamports`.
- **Availability.** Present.
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C07), vintage **H**.
- **Predictive value.** Not assessed; class **D** at source.
- **Evidence.** **D** (`02-c` §3.7).
- **Leakage / endogeneity.** A sum over a truncated window is safe; a sum over the life is not. It is also
  downstream of `p0`.
- **Priority.** 2, this pass's placement: no source ranks it, and it is the weakest of the block.

#### 8.1.8 `sales_last_24h` (`03-b` C08) — priority 2, class D

- **Definition.** Sale count over the window `(t-24h, t]`. The window boundary is load-bearing.
- **Mechanism (through liquidity).** Momentum, at class **D** (`02-c` §3.7).
- **Expected effect.** None claimed.
- **Interactions.** IF-07 (the quantile version of the same object, and the one `03-a` specifies because the
  mean does not survive truncation).
- **Measurement.** "The window must be `(t-24h, t]`, not `(t-24h, D3]`" (`03-b` C08).
- **Data source.** Contract: `LedgerEntry.slot`.
- **Availability.** Present.
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C08), vintage **H**.
- **Predictive value.** Not assessed; class **D** at source.
- **Evidence.** **D**.
- **Leakage / endogeneity.** The window ending at extraction is the named leak (`03-b` §4 T1).
- **Priority.** 2, this pass's placement, and IF-07 supersedes it for any published statistic.

#### 8.1.9 `cap_hit_share_as_of_t` (`03-b` C09, `03-a` IF-02) — priority 1

- **Definition.** Share of prior sales whose `markupBps` is within one basis point of the cap, with the
  denominator and `(k, n)` returned beside it and `null` below the sample floor (`03-a` IF-02).
- **Mechanism (through transaction probability and rationing).** A sale at the ceiling says a buyer paid the
  maximum permitted price, which is a statement about excess demand that does not depend on the level being
  identified (`02-a` §6.3). `03-a` §1.1 adds the formal shape: `min(m*, c)` gives a mass point plus a
  downward bias of `s·E[m*−c | m* ≥ c]`.
- **Expected effect.** **+** means excess demand at the ceiling. "It is a rationing statistic and it is never
  a value statistic" (`03-a` IF-02).
- **Interactions.** V3, IF-04, IF-07, I5, I9. Contaminated by `p0`: the ceiling in money is `p0(1+c)`.
- **Measurement.** `TOL = 1` bps as a named constant, because `core/markup.py` rounds half away from zero, so
  an on-the-ceiling sale can read `cap ± 1` (`03-b` §9 D-1). Tri-state output: `capped_and_binding (s>0)` /
  `capped_no_mass (s=0)` / `uncapped (c null)` (`02-b` §3.1).
- **Data source.** Contract: `LedgerEntry.markupBps`, `Event.resalePriceCapBps`. **Not** from
  `ResaleStats.avgMarkupBps` or `EventAnalytics.markupDistribution`, whose as-of is unstated.
- **Availability.** Present. Unmeasurable on the fixtures, where no generated sale lands on a cap
  (`00-data-situation` §2, `02-b` §2).
- **Update frequency.** Each sale.
- **Temporal verdict.** **R** (`03-b` C09), vintage **H**.
- **Predictive value.** "The best excess-demand signal in the dataset" (`03-b` C09, quoting `02-a` §6.2);
  "the first thing to compute on real rows" (`03-a` IF-02).
- **Evidence.** **C** for the truncation identity (`02-b` §1.2); **B** for the rationing reading (Bulow &
  Klemperer 2012, as `03-a` I5 records); **D** for the regime-classifier reading (`02-a` §6.3).
- **Leakage / endogeneity.** `s = 0` is **not** evidence the cap does not bind, and `s` is a **lower** bound
  on `Pr(m* ≥ c)`; it is a function of `p0` and cannot be compared across events without a `p0` band
  (`03-b` §5 P1, `03-a` IF-02).
- **Priority.** 1: it is the first ledger statistic to build (`03-a` §4.1).

#### 8.1.10 `cap_crossing_date_as_of_t` (`03-b` C10) — priority 2, class C

- **Definition.** The **most recent** cap sale at or before `t`, expressed as `τ`, with the interval width
  reported, that width being the gap to the first sale below the cap.
- **Mechanism (through price expectations, as a known-price anchor).** At the crossing date `m*(d*) = c` and
  `c` is observed, not estimated: "the only known-level point in the whole observation set" (`03-a` §1.1,
  `02-a` §6.1 C4).
- **Expected effect.** No sign; it is an anchor, not a regressor.
- **Interactions.** C09, C11, IF-03.
- **Measurement.** The as-of form only. `03-b` §9 D-3: "`02-a` §6.1 C4's definition of the crossing date is a
  look-ahead as written. 'The last day on which a sale lands at the cap' requires the whole series."
- **Data source.** Contract: `LedgerEntry.markupBps`, `slot`, `Event.resalePriceCapBps`.
- **Availability.** Present, **interval**-identified, and pushed later than the true crossing by off-rail
  settlement (`02-a` §6.1, caveats on C4).
- **Update frequency.** Each cap sale.
- **Temporal verdict.** **R** in the as-of form (`03-b` C10), vintage **H**. The retrospective form is **N**.
- **Predictive value.** A partial answer to `01-b`'s T1 for capped events (`02-a` §6.1 C4).
- **Evidence.** **C** (`02-a` §6.1 C4).
- **Leakage / endogeneity.** The definition-level leak `03-b` §4 T1 catches with the future canary: the
  retrospective form passes prefix invariance and fails the canary.
- **Priority.** 2.

#### 8.1.11 `quantile_log_price_per_tier_day` (`03-b` C11) — priority 1, class C

- **Definition.** Lower quantiles of `log(p/face)` by tier and day bucket, the 25th being the working one
  (`03-a` IF-04, IF-07).
- **Mechanism (through price expectations, as the descriptive estimator).** Truncation is one-sided from
  above, so a low quantile of the observed distribution is the same quantile of the latent one whenever the
  cap mass sits above it (`02-a` §6.2, Powell 1986).
- **Expected effect.** A floor, and it "rises with observed markups and it is never an estimate of the mean"
  (`03-a` IF-04).
- **Interactions.** C09 (the guard that decides whether the quantile is admissible at all), C10, IF-04,
  IF-07.
- **Measurement.** Refuse any central or upper statistic when the cap-hit share exceeds 50% (`02-a` §6.1
  C2). Never pool tiers with different faces in markup space (`02-a` §6.2).
- **Data source.** Contract: `LedgerEntry.priceLamports`, `markupBps`, `TicketTier.faceValueLamports`.
- **Availability.** Present.
- **Update frequency.** Each sale, bucketed by day.
- **Temporal verdict.** **R** (`03-b` C11), vintage **H**.
- **Predictive value.** It is the only path statistic that survives the cap (`02-a` §6.2), so it carries the
  descriptive claim the engine can make on a capped event.
- **Evidence.** **C**, from the censored-quantile result (`02-a` §6.2, Powell 1986).
- **Leakage / endogeneity.** The partial current day must be dropped when the bucket is a time unit, the same
  rule as C13.
- **Priority.** 1: it is the working estimator for capped events.

#### 8.1.12 `sale_hazard_output` (`03-b` C12) — priority 1, class C

- **Definition.** `F(τ)`, `λ`, or the model's own fitted value at `t`, produced by Specification A.
- **Mechanism (through transaction probability).** Perishable inventory and buyer arrival, as V1's two
  forces, estimated as cause-specific intensities over the censused ticket population.
- **Expected effect.** A decaying hazard in `τ` is the default prior, not a result.
- **Interactions.** C01, C02, V1, IF-01 (the stratum the hazard is reported within), and `02-c` §4.3's
  prohibition on separating the ask from the clock.
- **Measurement.** Fitted on rows before `t` only; "two cuts nest" (`02-c` §3).
- **Data source.** Contract: `issue`, `sale`, `transfer`, `redeem`, `revoke` rows with `slot`, plus
  `Event.startsAt`.
- **Availability.** Present. The unconditional sale intensity **is** identified (`01-b` §5; `02-c` §2.3, O1
  and O3 class C); the ask-conditional hazard is not (I13).
- **Update frequency.** Refitted at each cut.
- **Temporal verdict.** **R** (`03-b` C12), vintage **H**.
- **Predictive value.** It is the "probability it transacts" sentence the product promises, at the prevailing
  ask and with `02-c` §2.6's footnotes.
- **Evidence.** **C** (`02-c` §2.3).
- **Leakage / endogeneity.** Inherits the model's cut. Also subject to right-censored exposure on events
  still open at extraction (`03-b` §4 T6) and to `03-b` §5 P2's mixture if the wallet gate is on.
- **Priority.** 1.

#### 8.1.13 `price_series_complete_days` (`03-b` C13) — priority 3

- **Definition.** `EventAnalytics.priceSeries` filtered to complete UTC day buckets strictly before the cut's
  date.
- **Mechanism (through liquidity, as the observed transaction-price distribution).** It is `02-c` §2.4's
  `ξ(p, τ)`: "how much trade happens, and at what price levels, and when", which the contract already exposes
  at day granularity. It must be labelled a transaction-price distribution and never a demand curve (Working
  1927).
- **Expected effect.** No sign; it is a descriptive object.
- **Interactions.** C07, C08, C11.
- **Measurement.** Filter with `<` the cut's UTC date, never `<=`, and add a case where a sale earlier on the
  cut day must be excluded (`03-b` §4 T2, §7 row 6).
- **Data source.** Contract: `EventAnalytics.priceSeries` only after the partial day is dropped.
- **Availability.** Present.
- **Update frequency.** Each completed day.
- **Temporal verdict.** **R** (`03-b` C13), vintage **A**, and it is "the one aggregate that becomes usable"
  (`03-b` §3.3).
- **Predictive value.** Not assessed. It is the honest replacement for a price-response chart in the
  interface (`02-c` §2.4, §7).
- **Evidence.** No finding assigns a class; `03-b` classifies the vintage, not the evidence.
- **Leakage / endogeneity.** The partial current day is the whole hazard, and it is not marked as partial.
- **Priority.** 3, this pass's placement: useful for display, no source ranks it as a predictor.

---

### 8.2 Event, tier and ticket facts that `03-b` adds (five rows)

#### 8.2.1 `event_ends_at` (`03-b` A02) — priority 4, class not assigned

- **Definition.** `Event.endsAt`.
- **Mechanism (none directly).** A festival or a double-header is a different product from a two-hour show,
  which is what §5.2 already says.
- **Expected effect.** None claimed.
- **Interactions.** Fold construction: the strict event-level check uses `endsAt` (`02-a` §8.5, `03-b` §6.3).
- **Measurement.** Field read.
- **Data source.** Contract: `Event.endsAt`, nullable.
- **Availability.** Present.
- **Update frequency.** Static.
- **Temporal verdict.** **P** (`03-b` A02), vintage **S**.
- **Predictive value.** Low. "Only used for fold construction and event duration" (`03-b` A02).
- **Evidence.** No class assigned.
- **Leakage / endogeneity.** None.
- **Priority.** 4: a control, and it is the one field §5.2 called `D`, low value.

#### 8.2.2 `tier_count` (`03-b` A05) — priority 3

- **Definition.** Number of tiers on the event.
- **Mechanism (through demand heterogeneity).** Multi-level pricing exists to separate willingness to pay
  along a quality axis, so a second tier is evidence that the organiser believes demand is heterogeneous
  (`02-e` §2.2).
- **Expected effect.** "More tiers and a steeper ladder should widen the markup distribution, not necessarily
  raise its mean" (`02-e` §2.2).
- **Interactions.** A08 (the ladder ratio, the same structure as a number), V15 (with seat coordinates this
  would be the quality axis itself).
- **Measurement.** Count of `Event.tiers`.
- **Data source.** Contract: `Event.tiers`.
- **Availability.** Present.
- **Update frequency.** Static.
- **Temporal verdict.** **P** (`03-b` A05), vintage **S**.
- **Predictive value.** `03-b` A05's own note: "Evidence that demand is heterogeneous, not a demand measure."
- **Evidence.** **A** for the multi-category revenue effect in the published market (Courty & Pagliero, about
  5%), **D** for the transfer (`02-e` §2.2).
- **Leakage / endogeneity.** Chosen by the organiser, so it is an outcome of the same decision that sets
  `p0`, and it may not be read as exogenous.
- **Priority.** 3, this pass's placement: weak but free.

#### 8.2.3 `price_ladder_ratio` (`03-b` A08) — priority 3

- **Definition.** `max/min` tier face within the event.
- **Mechanism (through demand heterogeneity).** The steepness of the quality-price ladder, as an ordinal
  stand-in for the quality axis the contract does not carry.
- **Expected effect.** Widens the markup distribution, per A05's mechanism; no sign on the mean.
- **Interactions.** A05, V15, V2 (with per-tier sell-through it becomes a real cross-tier demand read).
- **Measurement.** Ratio of two integers already present.
- **Data source.** Contract: `Event.tiers[].faceValueLamports`.
- **Availability.** Present.
- **Update frequency.** Static.
- **Temporal verdict.** **P** (`03-b` A08), vintage **S**.
- **Predictive value.** Not assessed.
- **Evidence.** No class assigned to the ratio itself. `03-b` A08's note is not about evidence: "Same
  exclusion as A07: it is chosen."
- **Leakage / endogeneity.** **Endogenous**, exactly as A07 is: it is the organiser's price menu.
- **Priority.** 3, and never a free regressor (`03-b` §5 P3, consequence 1).

#### 8.2.4 `event_status_terminal` (`03-b` A14) — priority 3, class C

- **Definition.** `sold_out` or `completed`, read as a predictor.
- **Mechanism (through demand).** A sold-out primary is direct evidence of excess demand at face, so some
  willingness to pay exceeds face (`02-e` §2.4).
- **Expected effect.** **+**, one-sided, and it is a statement about the *recorded* price when a cap binds,
  not about value (`02-e` §2.4, two sign results).
- **Interactions.** V2, V3, C09, IF-01 (`tight_class`).
- **Measurement.** Field read at `t`, with the exception `03-a` §6.2, item 6, records: the state is admissible at D1
  only for an event that has already sold out before `T1(e)`, which is rare but real for a second tier priced
  after the first cleared.
- **Data source.** Contract: `Event.status`.
- **Availability.** Present, with untimestamped transitions (`00-data-situation` §4).
- **Update frequency.** On transition, which is not dated.
- **Temporal verdict.** **N at D1, R at D2** (`03-b` A14), vintage **K**. The only row in the 61 whose two
  verdicts differ.
- **Predictive value.** "The strongest single pre-resale fact" (`02-e` §2.2), usable only from the moment the
  transition is observed.
- **Evidence.** **C** (`02-e` §2.2).
- **Leakage / endogeneity.** A value read later is the eventual state, which is why the vintage is K.
- **Priority.** 3, conditional on the transition being polled and logged.

#### 8.2.5 `issued_at` (`03-b` B04) — priority 1, class C

- **Definition.** `Ticket.issuedAt`, and the derived ticket age `a = t − issuedAt`.
- **Mechanism (through time on market).** "Time on market" (`02-c` §3.7, class C), and the entry event of the
  risk window.
- **Expected effect.** No independent sign: age and `τ` are affine in each other when issuance is common
  within an event (`02-c` §3.1, `03-b` §2.2), so only one of them may enter linearly (`03-b` §4 T4, the
  two-clock rule).
- **Interactions.** V1, C04, IF-08 (exposure `E_e` is a sum of these).
- **Measurement.** Field read; the risk window opens here.
- **Data source.** Contract: `Ticket.issuedAt`.
- **Availability.** Present, and it is what makes `T1(e)` derivable (`03-b` §2.1).
- **Update frequency.** At issue.
- **Temporal verdict.** **R** (`03-b` B04), vintage **H**: "Nonexistent at D1 by definition."
- **Predictive value.** Structural rather than predictive: it is the clock of the hazard and the exposure
  accumulator.
- **Evidence.** **C** (`02-c` §3.7, "ticket age bucket, interacted with staggered-issuance indicator").
- **Leakage / endogeneity.** Staggered issuance makes age and calendar time separable; a common issue time
  makes them the same variable.
- **Priority.** 1.

---

### 8.3 Rows `03-b` drops, recorded as DROPPED with the reason

**Eighteen features are dropped in total** (`03-b` §3.5). Fifteen had no row in this file and are entered
here, compressed as §5 compresses. Three did have a row, and their entries now carry a DROPPED line in
place: **V15** `seat_coordinates` (B05), **V14** `listing_depth` (D02), and `demand_side_record` (D03). The
counts by reason, quoted from `03-b` §3.5: six absent from the observation set (A16, A29, B05, D01, D02,
D03), eleven carrying post-decision information (A24, B06 to B11, C14 to C17), one unidentified rather than
absent (D04).

#### 8.3.1 Dropped as absent from the observation set

**`on_sale_age` (A16).** Definition: `t − onSaleAt`, time since on-sale. Mechanism, through supply and
demand: it is the denominator of a booking curve, so without it the engine observes the sell-through level
and the time-to-event, never the rate (`02-e` §2.2). **DROPPED** (`03-b` A16): "**Dropped, absent.** Also
kills sell-through velocity. Operator Q6." Class: none assigned. Priority 0. What would revive it: a
timestamped on-sale, which is `03-b` Q6 and the second item on its data list.

**`event_category` (A29).** Definition: genre, tour identity, event type. Mechanism, through willingness to
pay: between-event variance is plausibly dominated by what the event is, so pooling across categories
transfers the wrong prior (`03-a` I7). **DROPPED** (`03-b` A29): "**Dropped, absent.** `02-e` Q2. Best single
cold-start covariate and it does not exist." Class **D** for the transfer (`02-e` §2.2), class **E** for I7 as
`03-a` records it. Priority 0. What would revive it: the field, or a classifier on `name`/`description` that
generalises, which `02-e` §2.2 says no rule does.

**`listing_panel` (D01).** Definition: `{listPriceLamports, listedAt, delistedAt, delistReason}` per listing
episode. Mechanism, through supply and transaction probability: without it the probability of sale at a price
is unidentifiable, because the observed rate is the product of the hazard, the conditional ask distribution
and the listing probability (`01-b` T3, `02-c` §1.1). **DROPPED** (`03-b` D01): "**Absent.** `F-decision-log`
D3, the one data request. Without it the probability of sale at a price is unidentifiable." Class **C**.
Priority 0. What would revive it: D3, and `02-c` §4.1 requires the revision form (four fields per revision),
not four fields per listing, because revisions are the richest source of within-ticket price variation.

#### 8.3.2 Dropped as carrying post-decision information

**`weather_actual` (A24).** Definition: observed weather at the venue on the event date. Mechanism, through
attendance cost: the same channel as V12, measured after the fact. **DROPPED** (`03-b` A24): "**Dropped,
post-decision.** It is a label for an attendance model, not a feature." Class **B** for the attendance
mechanism (Ge, Humphreys & Zhou 2020, as V12 carries it). Priority 0. What would revive it: nothing at a
decision time; it is a label.

**`owner_wallet` as stored (B06).** Definition: `Ticket.ownerWallet`. Mechanism, through sellers: the current
holder is the potential seller. **DROPPED** (`03-b` B06): "**Dropped as a field, recoverable from the
ledger.** Use the last `toWallet` at or before `t` instead, which is group C." Class **C** for the survival
reading. Priority 0 as stored, recovered by the last `toWallet` before the cut.

**`ticket_status` as stored (B07).** Definition: `valid`/`listed`/`redeemed`/`revoked`. Mechanism, through
supply and transaction probability: "listed" is the exposure state. **DROPPED** (`03-b` B07): "**Dropped.**
'Listed at D3' says nothing about 'listed at `t`'. This is the exposure denominator that does not exist."
Priority 0. It is Gap 1 restated as a feature, and no recomputation recovers it because there is no listing
history to recompute from.

**`redeemed_at` (B08).** Definition: `Ticket.redeemedAt`. Mechanism, through transaction probability: the
terminal alternative to selling, so a competing risk. **DROPPED** (`03-b` B08): "**Dropped as a covariate.**
Admissible only as a competing-risk exit time once it has occurred, never as a feature." Class **C** for that
use (Fine & Gray 1999, via `02-c` §3.4). Priority 0 as a feature, 1 as an exit indicator.

**`transfer_count_field` (B09).** Definition: `Ticket.transferCount`. Mechanism, through sellers: a
whole-life churn count. **DROPPED** (`03-b` B09): "**Dropped as stored.** Recompute from truncated entries,
which is C03." Priority 0 as stored, 1 as `hop_count_as_of_t`.

**`last_sale_price_field` (B10).** Definition: `Ticket.lastSalePriceLamports`. Mechanism, through price
expectations: a whole-life summary of the ticket's own price. **DROPPED** (`03-b` B10): "**Dropped as
stored.** Recompute, which is C06." Priority 0 as stored, 1 as `own_markup_path`.

**`transfer_restricted` (B11).** Definition: whether the chain currently enforces a transfer restriction on
this mint. Mechanism, through supply and transaction probability: a hard block on the channel, which is V3's
friction channel. **DROPPED** (`03-b` B11): "**Dropped as a feature.** It is a consequence of policy plus the
ticket's own history, and its stored value is chain state at D3." Priority 0. V3's policy block therefore
rests on the event-level fields alone.

**`analytics_scalars` (C14).** Definition: `avgMarkupBps`, `medianResalePriceLamports`, `resoldShare`,
`uniqueHolders`, `totalVolumeLamports`, `saleCount`, `markupDistribution`, `topDestinations`. Mechanism: none
independent of the rows they are computed from. **DROPPED** (`03-b` C14): "**Dropped as features.**
Legitimate as training labels on **completed** events." Vintage **A**: no as-of in either contract file and
no time parameter on any endpoint (`03-b` §1.3, measured). Priority 0 as a feature, and `03-b` §7 row 5 is a
grep that enforces it.

**`resale_stats_block` (C15).** Definition: `ResaleStats.saleCount`, `avgMarkupBps`, `peakPrice`,
`lastPrice`, `totalVolume`, `uniqueWallets`, all over the ticket's whole life. **DROPPED** (`03-b` C15):
"**Dropped as features.** Same as C14 at ticket scale." Vintage **A**. Priority 0.

**`acquired_on_secondary` (C16).** Definition: `DestinationRow.acquiredOnSecondary`. Mechanism: none that
survives its construction. **DROPPED** (`03-b` C16): "**Dropped.** Derived from the current owner. Class E
anyway." Priority 0.

**`destination_region` (C17).** Definition: `DestinationRow.region`. Mechanism: geography of the buyer pool,
which V7 carries properly. **DROPPED** (`03-b` C17): "**Dropped.** Selected with no denominator." Class
**E**. Priority 0.

#### 8.3.3 Dropped as unidentified rather than absent

**`own_price_elasticity` (D04).** Definition: the own-price elasticity of primary demand, `ε_own`, per tier.
Mechanism, through demand: the quantity response that converts a boundary rule into an interior optimum
(`03-a` I6, `02-d` §5.1). **DROPPED** (`03-b` D04): "**Unidentified, not absent.** No price change exists in
the record to respond to. `02-d` §3.6's randomised tier-face experiment is the only correction. This is why
the primary optimum reports a boundary and not an interior point." Class **C** for the mechanism, and **not
identified** is the operative word. Priority 0, and the remedy is an experiment, not a data request.

---

### 8.4 The twelve interaction features of `03-a`, as composite variables

Each is a variable that combines two factors. The two factors, the interaction each carries, the sign, and
whether it can be computed today from the wire contract. `03-a` §4 gives the full definition of each,
including its floors and its `null` conditions; this table is the registry's index to them, not a
replacement. "Computable today" uses `03-a` §4.1's own split.

| IF | Variable | The two factors it combines | Carries | Expected sign | Class | Verdict | Computable today |
|---|---|---|---|---|---|---|---|
| **IF-01** | `tau_x_tight` | `τ` bucket (`T60` to `T0`) × primary tightness class (`SOLD_OUT`/`HIGH`/`MID`/`LOW`/`UNKNOWN`) | I2 | slope **−** in `LOW` and `MID`, **≈0 or +** in `SOLD_OUT` and `HIGH` | A for the two forces, **D** for the net sign here | **R** for `tight_class`, **P** for the `τ` bucket | **No**: the fields exist, the vintage does not. Needs the ratio polled and logged at `T1(e)` |
| **IF-02** | `cap_mass` `s(t)` | the cap value × the sale markups, as the share landing within 1 bps of it | I5 | **+** means excess demand at the ceiling; never a value statement | **C** for the truncation, **B** for rationing | **R** | **Yes**. Every input is in `LedgerEntry` and `Event` |
| **IF-03** | `cap_window(p0)` `W(p0)` | the fitted log-money path for the tier × the candidate `p0` and the cap | I9 | `∂W/∂p0 < 0`, `∂s/∂p0 ≈ 0` | **C** | **P**: a function of the decision, evaluated not observed | **No**: needs the path model of `02-a` §8, specified and not built |
| **IF-04** | `cap_floor(g,t)` | the 25th percentile of sale log-price ratios below the cap × the tier face | I5 | a floor, never a mean | **C** | **R** | **Yes**, with the 50% cap-mass guard |
| **IF-05** | `supply_remaining_x_ladder` | remaining supply share `rem_g` × the tier ladder `ladder_g` | I1, I3 | premium highest at low `rem_g` and high `ladder_g`; one-sided | **C** | **P** if logged at `T1(e)`, else snapshot (**K**) | **Yes** at D1 only if the backend logs it; the fields exist |
| **IF-06** | `seller_concentration` | `fromWallet` sale counts within the tier × the sale rows that produce them | I4 | **−** on level, **+** on the hazard | **A** in MLB, **D** for the transfer | **R** | **Yes**, with the wallet-is-not-a-person caveat printed |
| **IF-07** | `momentum_lower_quantile` | the 25th quantile of the log price ratio in `(t−7d, t]` × the same in `(t−14d, t−7d]` | I4, I2 | negative in the default regime; the sign is the object under test | **D** | **R** | **Yes**, when both windows clear five sales, else `null` |
| **IF-08** | `coldstart_weight` `w_e` | accumulated exposure `E_e` × the event's own mean against the pooled mean | replaces I7 | weight on own data **+** in `E_e`; the exposure update moves the intensity **down** | **C** | **P** | **Yes** for `E_e`; `pooled_mean` needs the event panel, which does not exist |
| **IF-09** | `coldstart_band` | between-event dispersion × the declared `τ` grid | the cold-start deliverable of `02-e` | n/a, an interval | **C** | **P** | **Yes**: closed form plus one bisection |
| **IF-10** | `hop_velocity(g,t)` | hop counts × the ticket-days of exposure over which they occurred | I8 | **+** hops and **−** holding in top tiers on tight events | **D** | **R** | **Yes**, with the selection and key-handoff biases printed |
| **IF-11** | `gate_stratum` | `requiresVerifiedWallet` × `resaleEnabled` × `cap_present` | I10 | **none**: the pooled number estimates neither regime | **D** | **P** | **Yes**, as a partition, never as a regressor |
| **IF-12** | `wedge_ratio` | the fee stack × the elasticity, `c**/f_g` | I11 | `∂p*/∂f > 0`, `∂p*/∂φ = 0`, `∂p*/∂η < 0` | **C** | **P**, as a configuration input | **No**: Gap 4, and it must refuse to run rather than assume zero |

**Two notes that belong beside the table.** First, `03-a` §4.1's build order is the one to follow, and it is
grouped by what is blocked: six features need nothing new (IF-02, 04, 06, 07, 10, 11), two need only the
vintage logged (IF-01, 05), three need an upstream component that is specified and not built (IF-03, 08, 09),
and one needs a settlement field (IF-12). Second, every one of them returns `null` below its floor rather
than a number, and that is the discipline that keeps a sparse event from producing a confident-looking
coefficient.

---

### 8.5 The thirteen interactions, and where each lives in this registry

`03-a` §1 registers thirteen interactions. They are not variables, so they are not given eleven fields, but a
registry that omits them invites a later pass to rediscover one as an estimate. The two factors, the sign,
the class, `03-a`'s causal verdict, and where the registry carries it.

| # | The two factors | Sign | Class | Causal verdict (`03-a` §2) | Binds? | Where it lives here |
|---|---|---|---|---|---|---|
| **I1** | Inventory depletion × demand intensity | **+**, increasing in intensity, zero when demand is slack | C plus B for direction | predictive-only (confounding, policy creation) | No: state, never a regressor | IF-05 as a state variable; V2's endogeneity note |
| **I2** | Time-to-event × popularity | **−** in soft or already-cleared events, **≈0 or +** when excess demand survives | A for both forces, **D** for the net sign here | causal in mechanism, predictive in implementation | **YES** | IF-01; V1's interaction requirement |
| **I3** | Resale premium × primary inventory remaining | **+**, one-sided | C by construction, A support (Budish & Bhave 2023) | causal, one-sided | One-sided only | IF-05; V2; `02-e` §2.4's two sign results |
| **I4** | Price momentum × seller concentration | **−** on level and slope, **+** on the hazard | A in MLB, **D** here | predictive-only (selection, policy artefact) | No | IF-06, IF-07; V5's wallet caveat |
| **I5** | Markup × the resale cap binding | **−** on every observed mean and upper quantile, certain from the identity; **+** on the average transaction price if a stringent cap pushes high-price sellers out | **C** truncation, B rationing, **D** evasion magnitude, A that caps leak | artefact of the recording policy, with a causal behavioural component at D | **YES** | IF-02, IF-04; V3; `02-b` §1.2 |
| **I6** | Elasticity × remaining inventory | `abs(ε)` falls as remaining inventory falls, so the optimal price rises | C | causal (theory), not identified | In the objective | D04, dropped; `02-d` §5.1 |
| **I7** | Cold-start degradation × event category | unknown; the band widens if category explains between-event variance | **E**, the field does not exist | not estimable | No | A29, dropped; IF-08 is the replacement |
| **I8** | Custody-hop speed × the ticket's tier | hops per ticket-day **+** in top tiers on tight events | **D**, no published measurement of hop speed | predictive-only | No, but the cheapest novel measurement the ledger offers | IF-10; V5 |
| **I9** | Cap binding × the chosen primary price | `∂s/∂p0 ≈ 0` (share invariance), `∂W/∂p0 < 0`, option-value channel **+** | C | causal by algebra, a self-inflicted shift | **YES**, in the objective and the learning loop | IF-03; §7 C-3 and its CORRECTION, on the cap in money |
| **I10** | Verified-wallet gate × demand tightness | unknown, and not a sign: the pooled number is a mixture of two regimes | **D** | mixture, neither causal nor predictive | No | IF-11; V3 |
| **I11** | Fee wedge × elasticity | `∂p*/∂f > 0`, `∂p*/∂η < 0`, `∂p*/∂φ = 0` | C | causal by algebra | In the objective | IF-12; `fee_model` |
| **I12** | Cap stringency × seller concentration | **+** on average transaction price, **−** on listing depth | C (model), A that caps leak | causal in a model, untestable here | No | V3; §7's CORRECTION on the withdrawn within-event instrument claim |
| **I13** | Sale hazard × the ask | **−**, magnitude unknown | C for the mechanism, not identified here | not identified (case-only, endogenous ask, collinear with `τ`) | Binds in what the product may claim | C12's limit; `listing_panel` (D01), dropped. Registered as I13 rather than omitted, per `03-a` §1 |

**The count that binds, and the one sentence that matters.** Two interactions bind in the sense `03-a` §0
defines: I5, structural and certain from the record's construction, and I2, behavioural and the thing that
decides the sign of the only forecastable object. Three more (I6, I9, I11) bind in the objective: they are
structure the optimiser implements and cannot estimate. I13 binds in what the product may claim and not in
what it can compute. The sentence the deliverable must not contain, quoted from `03-a` §3.1: "We model the
market as a dynamic feedback system." Its replacement is narrower and stronger: *we model one decision, with a
censored price record, two opposing time forces, and a policy that feeds back into the record one event
later.*

---

### 8.6 Where `03-b` restates or contradicts a verdict this file already carried

Recorded, not smoothed over. Each row names the file, quotes it, and says what this revision did. An existing
verdict was changed only where the quoted file contradicts it.

| # | Row | What this file said | What `03-b` says, quoted | What revision 2 did |
|---|---|---|---|---|
| 1 | **V2** sell-through | **P+R** | §3.1 A15 gives `R \| R`, and §2.1: "It may not know any ticket-level, ledger-level or aggregate fact about `e`, and it may not know its own sell-through, because there is none yet." | **Verdict restated to R.** V2's P+R is kept as the statement about a value at the instant it was observed, and V2's own entry above now carries the R. |
| 2 | **V8** competing supply, and **V9** tour routing | **R**, with **N** for stops added after on-sale | A20 and A21 both give `P \| P`, with notes "a show announced after `T1` was invisible at D1 ... the collection must be dated" and "the *completed* routing is the future" | **Kept at R as the default**, because R and a dated P are the same statement and neither file measures an announcement-date distribution. The P is recorded in both entries. **This is a choice, not a resolution.** |
| 3 | **V17** transit and access | **R** for shocks, **N** in practice | A28 gives `P \| P`, note "Weak, and static" | **Kept.** A28 is about the static part, which a venue fixed effect absorbs; the registry's R is about the shock part, which A28 does not classify. |
| 4 | **V15** `seat_coordinates` | **P+R** (known at issue) | B05: "**Dropped, absent.** `F-decision-log` Q1. Strongest within-event axis in the published literature and unexpressible here." | **DROPPED added**; the P+R stands as the verdict on the value if the field existed. |
| 5 | **V14** `listing_depth` | **P+R** | D02: "**Absent.** `01-d`: worth more than every external variable combined, and unobtainable." | **DROPPED added**; the P+R describes the variable, not an obtainable one. |
| 6 | `demand_side_record` | **P+R** if logged, **N** otherwise | D03: "**Absent.** Every demand statement in the programme rests on assumption (`01-b` §6)." | **DROPPED added.** |
| 7 | **V10** artist state, **V12** weather | **R** only, not **P** | A25 "`R` only", A23 "**R** only" | No change: the two files agree. |
| 8 | **V13** album timing | **P+R** if pre-announced, **R** after | A26 `P \| P`, note "a release announced after `T1` is not knowable at D1" | No change in substance: A26's condition is this file's distinction. |
| 9 | **V16** macro | **P+R** in principle, **N** as published | A27 `P \| P`, vintage **K**: "The revised series is D3 information." | No change: this file's "N as published" is the same statement. |
| 10 | `fee_model` | **P+R** | A12 `P \| P`, "Configuration, not data. Missing fee must raise, not default to zero." | No change. |

**One point of substance that is not a verdict, and that this revision adopts.** `03-b` §9 D-1 corrects
`CONTRACT-MAP.md` §6 on cap-binding evidence: it is derivable, not absent, when `markupBps` equals
`resalePriceCapBps`, provided the test carries a one-basis-point tolerance because the wire rounds markup half
away from zero. This registry's V3 and §7 C-3 already assume exact equality is observable; §8.1.9 now states
the tolerance, and the tolerance is the only change.

---

### 8.7 Counts after revision 2

Counted from the entries above, not estimated.

- **Original rows, unchanged in number:** 4 admitted from the wire contract (V1, V2, V3, V5), 11 admitted
  outside it (V4, V6 to V13, V16, V17), 4 not obtainable (`seat_coordinates`, `listing_depth`, `fee_model`,
  `demand_side_record`), 18 rejected (X1 to X18).
- **Added in revision 2:** **33 variable rows** (13 in §8.1, 5 in §8.2, 15 in §8.3), plus **12 composite
  interaction features** in §8.4 and **13 interaction rows** in §8.5.
- **Marked DROPPED:** **18**, being the 15 new rows in §8.3 and the 3 existing rows amended in place (V15,
  V14, `demand_side_record`). That is `03-b` §3.5's count of 18 and it reconciles feature for feature.
- **Verdicts now carried:** every row in §1 to §3 carried a temporal note before this revision and still
  does; §5.2's fields now carry theirs in §5.3; every row in §8 carries one.
- **Changed verdicts:** one, V2, on the authority of `03-b` §3.1 A15 as quoted in §8.6 row 1. Two (V8, V9)
  are recorded as a disagreement this pass chose between, and both statements stand.

**What this revision does not do.** It estimates nothing, ranks nothing against the existing rows, and
promotes no evidence class. No number here comes from `lib/mock/`. `03-b` §10's warning applies to this
section in full: no real ledger exists, so every verdict above is a specification of a check and not an
observation of a failure.

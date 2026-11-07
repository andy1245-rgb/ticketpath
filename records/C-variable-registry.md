# C — Variable registry

**Programme section:** §2.C. **Status:** first complete pass. **Written:** 2026-11-07T11:40Z.
**Author:** records agent (`records-c`). **Supersedes:** the seeded stub of 2026-11-07T08:27Z (no content lost).

**Sources folded in, and nothing else:**
`records/findings/01-d-external.md` (Tables C-1 and C-2, §4 mechanisms, §5 predictive versus causal),
`records/findings/01-b-identifiability.md` (which targets are identifiable at all),
`records/00-data-situation.md` (the four contract gaps), `records/F-decision-log.md` (D3, D4, Q1, Q2, Q3),
and `/home/friend/ticketing-frontend/lib/types.ts` read directly for field-level availability.

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
is observed, varies across events, and varies across tiers within one event because it is bps over each
tier's own face, so a mass point at the cap measures rationed *quantity* though not the latent tail's
location. The registry treats V3 as both, and 01-b's original point stands: **no class-A claim about caps
may appear in the deliverable**, because no peer-reviewed study of resale price caps in ticket markets was
found.

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

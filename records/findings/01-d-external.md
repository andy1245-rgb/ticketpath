# Phase 1 — Domain D: External influence discovery, and the initial data-source registry

**Status:** complete for Phase 1 purposes. **Written:** 2026-11-07T09:00Z. **Agent:** `p1-external`.
**Scope:** programme §3 Phase 1 domain 5 (external influence discovery) and §2.E (data-source registry).
**Authority:** `RESEARCH-PROGRAM.md` §4 in full, especially §4.2 (mechanism before inclusion), §4.7
(predictive vs causal), §4.8 (temporal correctness); `records/00-data-situation.md`; the wire contract
`../ticketing-frontend/lib/types.ts`.

---

## What I concluded

Nineteen candidate variables were examined against §4.2 and eleven survive at usable priority. The
decisive filter was not availability and not correlation: it was **the clock**. This engine makes two
different decisions at two different times — a primary price set before on-sale, and a reprice taken
while the event is in market — and a variable can only enter if its value is knowable *at the decision
time*, not merely at the event. That one test removes weather forecasts, injuries, transfers, competing
events, added tour stops and support-act announcements from the primary-price problem entirely, because
all of them resolve after the on-sale that the primary price is fixed at. What survives at the top is
unglamorous: time-to-event, sell-through, the seller's own policy fields (resale cap, resale enabled,
verified-wallet requirement), venue capacity, and the custody trail. Two of the highest-value variables
in the whole registry — seat coordinates and secondary listing depth — are not obtainable at all in the
current contract, and listing depth is worth more than every external source in this report combined.
On sources: **Ticketmaster's Discovery API is the only free, lawful, broad catalogue, and it no longer
carries prices**; StubHub's API is seller-side rather than market-side; **Google Trends cannot be
collected lawfully** (no official API, and Google's robots.txt disallows exactly the endpoints a scraper
needs, which its Terms of Service makes a breach); **Spotify's content is prohibited from ingestion into
an ML model** and its artist popularity fields are deprecated; **Reddit requires a separate commercial
agreement and forbids ML training on its content**; X is now pay-per-read. The external-signal fantasy
dies quickly on inspection, and the money it would cost is listed at the end.

---

## 1. The admission test, stated so it can be attacked

For each variable I asked, in this order:

1. **Through whom does it move something?** A named channel into buyer willingness-to-pay, seller
   asking behaviour, supply quantity, liquidity, transaction probability, or price expectations.
   "It correlates with demand" is not a channel.
2. **Is it knowable at the decision time?** The primary price is a function of information available
   before on-sale. Repricing is a function of information available at `t`. Where the two differ I say so.
3. **Is it already in the ledger?** A variable that proxies for something the platform already observes
   adds nothing (§4.7). Sell-through already reveals realised demand; search interest is a *forecast of
   a forecast*.
4. **Is it obtainable lawfully, and at what cost?** A variable that cannot be collected is not a variable,
   it is a wish (see §4.6).

Evidence class is per `records/README.md`. Priority: **1** = build now, **2** = build after the core,
**3** = conditional on data being present, **4** = deflator/control only, **0** = blocked on a data
requirement that goes to the operator.

---

## 2. Table C-1 — admitted variables

Ready to paste into `records/C-variable-registry.md`. Signs are stated per unit change, holding the
event fixed.

| # | Variable | Definition + measurement | Mechanism (through whom) | Sign | Availability / update | Leakage and temporal risk | Pred. value | Class | Pri. |
|---|---|---|---|---|---|---|---|---|---|
| V1 | `time_to_event` | `startsAt − t`, hours | Perishable inventory: a seller holding unsold stock faces a hard expiry, so ask falls as τ→0; the buyer's outside option is to wait, so their reservation rises as τ→0. The two forces oppose, and which wins is set by ex-ante excess demand. | **conditional**, not monotone | In the contract. Continuous, per observation | None: τ is known ex ante | High | **A** | 1 |
| V2 | `primary_sell_through` | `issuedCount / totalSupply` per tier at `t` | Rationing signal. At a sell-out the queue, not the price, cleared the market, so latent demand exceeded capacity and scarcity is real. Observable evidence that the market is tight. | + | Contract, but **snapshot only** — no history, no on-sale time, no sell-out time (`00-data-situation.md` §4) | **Severe**: using the *current* ratio leaks the future. Must be logged at prediction time or it is unusable | High | C / B | 1 |
| V3 | `resale_policy` | `resalePriceCapBps`, `resaleEnabled`, `requiresVerifiedWallet`, `transferRestricted` | A binding ceiling truncates the price distribution, so the market clears by speed and rationing rather than by price; a cap also caps the *seller's* upside and suppresses listing supply. Verified-wallet and transfer restrictions add friction to every hop. | cap binding → mass point at cap + excess demand behind it; frictions − supply | Contract, event and ticket level | None | High | C | 1 |
| V4 | `venue_capacity` | Seats, from a venue→capacity join | The denominator of scarcity. Capacity against expected demand decides whether an event sells out at any price, which is what makes resale exist at all. | − on markup at fixed demand | **Not in the contract** (`venue` is free text). Static lookup | None | High | B | 1 |
| V5 | `custody_trail_features` | Per ticket, truncated at `t`: hop count, per-hop holding duration, repeat-reseller identity from `fromWallet`/`toWallet`, the ticket's own markup history, position in its own price path | Complements and corrects the ledger aggregates. A wallet that appears on many trails is a professional seller whose ask responds faster and who lists early; a long-held ticket is held by a consumer, not a broker, so its supply pressure is lower. The ticket's own price path is the only true per-ticket price observation available. | + for repeat-reseller and rapid-churn tickets; − supply pressure with long holding | Contract, per row | **The trap**: the full trail is the future. Every feature must be computed on `entries` filtered to `occurredAt ≤ t`, and hop `n+1` is the label, not a feature | High | C | 1 |
| V6 | `venue_type` | Arena / stadium / club / amphitheatre / theatre | Fixes weather exposure, sightline structure (which sets how much price variance is *within* an event) and typical capacity band. It is the stratum in which V1 and V4 behave differently. | stratifier, not a main effect | Not in contract; derivable from name + capacity | None | Medium | B / D | 2 |
| V7 | `city_market_size` | Metro population or DMA rank | Scales the local buyer pool and the walk-up segment; a 20,000-seat arena in a 6m metro and the same arena in a 400k metro are different markets. | + | Free (Census / DMA tables) | None | Medium | B | 2 |
| V8 | `competing_supply_same_night` | Count of other ticketed events in the metro on the same local date | Substitutes in one entertainment budget and one calendar night, and shrinks the pool of resale buyers at the same hour. | − | External (Ticketmaster Discovery) | Competing events are often *announced after* this event's on-sale, so the value is knowable at `t` but was not knowable at on-sale | Medium | D | 2 |
| V9 | `tour_routing` | For the same attraction: distance to the nearest other stop, and the date gap; plus flags for one-off, residency, final stop, festival | Substitution versus scarcity. A stop 200 km away three nights later cannibalises; a final stop or a one-off residency raises travel demand and lowers supply of substitutes. | − inside ~300 km/7 days; + for final/one-off | External (attraction id + geocoding) | Stops are added after the primary on-sale. Use only stops announced by `t` | Medium | D | 2 |
| V10 | `artist_or_team_state` | Injuries, suspensions, lineup changes, standings, championship contention, playoff implications, transfers | A shock to expected quality *and to its variance*. Quality moves willingness-to-pay; variance moves option value, which is why a title race can raise prices even when the product is unchanged. | + on positive quality surprise | ESPN scoreboard/standings (verified live, keyless); news is unstructured | For most events this resolves **after** the primary on-sale, so it is a repricing variable, not a pricing one. Must be timestamped | Medium (sports), low (music) | B on attendance / D on price | 3 |
| V11 | `event_calendar_structure` | Event local weekday and start hour; public holiday; school term | Competes for the same leisure slot and sets travel feasibility (a Tuesday 20:00 show is not a Saturday 20:00 show). | small ± | Static calendar join, free | None | Low–medium | B | 3 |
| V12 | `weather_forecast_outdoor` | Forecast issued at `t` for the venue's coordinates, on the event date; outdoor venues only | Day-of attendance cost: rain, extreme heat and snow raise the cost of going and cut walk-up demand and no-show risk. **Indoor venues: mechanism ≈ 0, and the honest coefficient is zero, not small.** | rain − ; heat ambiguous | Open-Meteo free tier (non-commercial) / NOAA archive (public domain) | **Forecast-versus-realised**: use the forecast available at `t`, never observed weather, or the feature is contaminated by the outcome | Low–medium, outdoor only | B | 3 |
| V13 | `album_or_release_timing` | New album, single, film or award within ±8 weeks of the event | Refreshes the artist's salience and adds setlist novelty, which is exactly what the resale buyer is buying. | + | MusicBrainz / Wikidata (free); release calendars | Release dates move; use announced date at `t` | Low | D | 3 |
| V14 | `secondary_listing_depth` | Count of simultaneously listed tickets, and its change over the last 24 h/7 d; the ask distribution | The quantity axis of the market. Without it, "no sale" cannot be separated into "no buyer at this price" from "nothing was ever offered". This is the missing denominator in `00-data-situation.md` Gap 1. | − on price as depth rises | **NOT IN THE CONTRACT.** Data requirement, not a feature | None once collected | **Very high** | C | **0** |
| V15 | `seat_coordinates` | Section, row, seat | The strongest within-event price axis in every published ticket study; proximity and sightline. | + toward the stage/pitch | **NOT IN THE CONTRACT.** Data requirement (`00-data-situation.md` Gap 3) | None | **Very high** | A | **0** |
| V16 | `macro_conditions` | Real disposable income, consumer confidence, live-entertainment spend, ticket-price CPI | Budget constraint and the price of the outside option. Real, but it moves every event in the panel at once, so it cannot explain cross-sectional price differences within a season. | +, negligible within-event | FRED / BLS, free | **Revised after first publication.** Use ALFRED vintages, not today's series | Low | B | 4 |
| V17 | `transit_and_access` | Station proximity, service alerts, strikes, closures, parking price | Changes the effective all-in cost of attending. Only *shocks* matter; the static part is absorbed by a venue fixed effect. | − on cost shock | GTFS (free); alerts ad hoc, no clean feed | Strikes are announced days ahead, so knowable — but rare and unaligned with events | Low | D | 4 |

## 3. Table C-2 — rejected, with the reason

These are recorded so nobody re-proposes them in Phase 2D. Each failed a specific test.

| Candidate | Reason for rejection |
|---|---|
| Google Trends search interest | **Unavailable lawfully.** No official API. `trends.google.com/robots.txt` disallows `/explore?`, and `www.google.com/robots.txt` disallows `/trends/api` and `/trends/explore?` — precisely the endpoints every scraper uses. Google's Terms of Service prohibit "using automated means to access content … in violation of the machine-readable instructions on our web pages (such as robots.txt)". Also weak: it forecasts the demand the platform already observes. Class D at best, and E in practice. |
| X/Twitter volume and sentiment | Same redundancy, plus cost and retro-deletion. Payable (see gates), capped, and the sentiment signal on a 1–10 week horizon is dominated by the market's own price. E. |
| Reddit volume/sentiment | Data API Terms forbid deriving revenues from the API without written approval, reserve fees, and grant **no right to use user content for training an ML model** without rightsholder permission. E. |
| Spotify listeners / artist popularity | The Web API reference marks **`popularity` and `followers` on the artist object as deprecated**, and the platform's policy states content "may not be used … to train a machine learning or AI model". Also, a listener count is a stock, not a shock. Rejected on licence, not on mechanism. |
| YouTube view velocity | No public velocity API, scraping contradicts the same ToS logic as above, and the mechanism (awareness) is upstream of a variable we already have. E. |
| Artist death, scandal, cancellation | Real price events, well covered by journalism, but they are point shocks with no distribution and no counterfactual. Keep as a hand-set override for the operator, not a feature. E. |
| Support act announced later | Sound mechanism (a weak support act can *reduce* value; a strong one adds it), but the only source is unstructured press. Revisit only if a structured announcement feed appears. D, priority 4. |
| Airport proximity, parking, road layout | Static per venue, therefore absorbed entirely by a venue fixed effect and contributing zero incremental information. |
| Tourism flows, convention calendars | Monthly, metro-level, and collinear with city market size (V7), which is free. Second-order at best. |
| School terms and holiday weeks | Mechanism exists but is a subset of V11, which already carries the holiday flag. Folded in, not separate. |
| Weather at indoor venues | Coefficient is zero by construction. Including it would be a mechanism violation dressed as a feature. |

---

## 4. The four mechanisms worth spelling out

**Time-to-event is not a trend, it is two opposing forces.** A seller facing expiry must lower the
ask; a buyer facing the same clock must raise the bid, because waiting risks no ticket at all. Which
dominates depends on whether the event is oversubscribed. On events that sold out at on-sale, the
observed path rises into the event date; on soft events it decays. So `time_to_event` must enter
**interacted with a tightness measure** (V2 sell-through, V3 cap binding), never as a standalone slope.
Fitting a single average slope across events will produce a number near zero and hide both effects.
This is the same pattern Sweeting documents for baseball resale (class A).

**The resale cap turns a price into a rationing rule.** When `resalePriceCapBps` binds, the observed
markup distribution is left-truncated by policy, the cap region is a mass point, and the height of that
mass point measures *excess demand*, not value. Two consequences for the engine: any model fitted to
capped prices understates value exactly where value is highest, and the cap must enter the sale-
probability component as a parameter of the data-generating process, not as a covariate. This is a
design consequence of `00-data-situation.md` Gap 2 and belongs in `B-mathematical-kb.md`.

**The custody trail is the only per-ticket price process available, and it is also the easiest place
to leak the future.** Every trail feature must be computed on `entries` truncated at `occurredAt ≤ t`.
A ticket's *future* hops are the label. The subtle version of this error is a wallet-level feature:
"how many tickets has this wallet resold" computed over the whole dataset includes resales that happen
after `t`. Repeat-reseller identity has to be built from a wallet history that is itself truncated.
I flag it here because it is the most likely silent failure in the whole Phase 7 build.

**Weather is a quantity variable, not a price variable, and only outdoors.** The published result is
on attendance: rainfall as a transitory shock to attendance cost, with habit effects running into later
games (Ge, Humphreys & Zhou 2020, *Journal of Sports Economics* 21(3):304–322, using MLB attendance with
NOAA weather data). Nothing in that literature says a rained-on concert's *resale price* moves, and the
mechanism is weaker for price: a ticket already sold to a consumer is a sunk cost, and a no-show does
not destroy the ticket's value to a buyer who is still willing to stand in the rain. Expected effect:
small, negative, outdoor venues, dominated by severe events. Rank it accordingly.

---

## 5. Predictive against causal, for the survivors (§4.7)

Three of the eleven are genuinely causal and worth pricing off: **V3 resale policy** (a cap changes the
objective function; a change in the cap is a natural experiment), **V10 artist/team state** where the
shock is exogenous to the ticket market (an injury is not caused by prices), and **V12 weather** for
outdoor venues. The rest are predictive. V1 time-to-event and V4 venue capacity are structural but not
causal in any actionable sense — you cannot move them. V2 sell-through and V5 custody-trail features
are the most dangerous case: they are **outcomes of the pricing decision itself**. If the primary price
is set low, sell-through is high and resale markups are large, so a model that regresses markup on
sell-through will read its own past decisions back as a law of nature. They belong in the model as
state, never as a free regressor, and any elasticity estimated on them is contaminated by the
company's own policy. V8 competing supply is the cleanest instrument-adjacent variable in the set
(other promoters' routing decisions are not caused by our price), which is why it is worth collecting
even though its expected effect is small.

---

## 6. Table E-1 — data-source registry

Ready to paste into `records/E-data-source-registry.md`. Prices are as published on the date checked;
anything I could not read is marked unverified rather than guessed.

| Source | Provider | Data type | Depth | Frequency | Granularity | Coverage | Access | Licence / restrictions | Cost | Reliability | Known limitations |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Discovery API v2 | Ticketmaster | Event catalogue: names, dates, venue, city, coordinates, classifications, ticket limit, public on-sale and presale windows, static seatmap URL, attraction cross-IDs (Spotify, MusicBrainz, Wikipedia) | Current + future only; no history | Near-real-time | Event, venue, attraction | 230k+ events, US/CA/MX/AU/NZ/UK/EU (vendor-reported) | REST, free API key | **No deriving revenues from the API** without Ticketmaster's terms; cache only "reasonable periods"; must remove content on request within 24 h; must not replicate the Ticketmaster UX | **Free**; 5,000 calls/day, 5 req/s, paging stops near result 1,000 (vendor-tested; docs say max page size 500) | Good; 0.17–0.9 s/call | **No price data.** Vendor testing Oct 2026: `priceRanges` present on 3 of 2,397 US events; release notes record price fields dropped from the Discovery *Feed* on 2025-03-11. The API reference still documents the field. No listing, seat, or sold-price endpoint |
| Partner / Inventory Status / Top Picks APIs | Ticketmaster | Real prices, fees, availability, holds | Live | Hourly or better | Event, price range | NA / official partners | Partner agreement | Not public | **Not purchasable.** Request-only; Inventory Status returned 401 to a free key (vendor-reported) | — | Gate: requires a commercial relationship |
| SeatGeek Platform API | SeatGeek | Events, performers, venues, taxonomy; listings where authorised | Current | Near-real-time | Event | US-centric | REST with client id | Terms not verified this run | Client id required by approval; no published price | Undetermined | I confirmed the API is live: `GET api.seatgeek.com/2/events` returns 403 "Client is required — visit seatgeek.com/account/develop". Whether listings/prices are exposed to a non-partner is **not established** |
| StubHub API | StubHub | Account, Catalog, Inventory, Sales, Webhooks | Current | Real-time | Event, venue, category | Markets StubHub operates in | REST, OAuth2, sandbox + production | Requires approved app credentials; terms not read | Not published | Docusaurus docs, versioned, maintained | **It is seller-side.** The Inventory API is "List seller listings / create a seller listing" — it manages *your* inventory, not the market's. It is not a market price feed. Catalog gives you the event graph only |
| Viagogo / Vivid Seats / AXS / TicketNetwork / Gametime | various | Listings, prices | — | — | — | — | No public self-serve API found | — | Third-party scrapers exist (e.g. tickets.dev, from $50/month for 1,000 captures) | — | Scraping raises ToS and legal exposure; vendor capture services offload the risk but add a dependency and per-call cost |
| Get Protocol / on-chain ticketing | GET Protocol and others | NFT ticket ownership, transfer events | Chain history | Per block | Token | Small event volumes | Public RPC / explorer | Public chain data is free to read | Free | — | **Not verified**: `docs.get-protocol.io` returns 401 without an account, so I cannot confirm that a fiat resale *price* is written on chain rather than settled in their backend. Even if it is, the events differ from ours and the population is small. Class E until shown otherwise |
| Solana RPC (own programme) | Solana | Our own ledger, in full, with slot ordering | Full history | Per slot | Transaction | Our platform | JSON-RPC, public endpoints rate-limited | Our own data | Free at prototype volume | High | Rate limits on public endpoints; an indexer is the real cost (effort, not money) |
| Google Trends | Google | Search interest index | 2004– | Daily/weekly | Query, region | Global | **No official API** | robots.txt disallows `/trends/explore?` and `/trends/api`; Google's ToS prohibits automated access contrary to robots.txt | Free but **not lawfully collectable**. Paid aggregators exist; prices not verified here | — | Rejected. Normalised per query, resampled, and revised |
| X API v2 | X | Post volume, text, engagement | 7 days recent; full archive on enterprise | Real-time | Post, user | Global | REST, OAuth | Developer policy; content redistribution restricted | **Pay-per-usage**: $0.005 per Post read, $0.010 per User read; 3M Post reads per monthly cycle cap. 1,000 posts/day ≈ **$150/month**; 10,000/day ≈ **$1,500/month** | Good | Cost scales with the thing you want (volume), and deleted posts vanish retroactively |
| Reddit Data API | Reddit | Posts, comments, votes | Full | Real-time | Post, comment | Global | REST, OAuth | **Fees reserved**; commercial use or research beyond the rate limit needs a separate agreement; **no ML training on user content** without rightsholder permission; no deriving revenues | Free tier exists; high-volume terms are contractual | Good | Rejected for this engine on the ML clause |
| Spotify Web API | Spotify | Track/artist metadata, popularity, audio features | Current | — | Track, artist | Global | REST, OAuth | **Content may not be used to train an ML model or be ingested into one** | Free | — | `popularity` and `followers` marked deprecated; `audio-features` deprecated. Rejected |
| Chartmetric | Chartmetric | Cross-platform artist metrics, historical listener/chart series | Multi-year | Daily | Artist | Global | Web + API | Commercial licence | **Manager $40/month, billed yearly**; higher tiers quote-only | Commercial | Still downstream of the same platform data; adds cost without adding mechanism |
| Open-Meteo | Open-Meteo | Forecast + historical weather, 30+ models | Archive | Hourly | Point, hourly | Global | REST, no key | Free tier is **non-commercial only** (CC-BY 4.0, attribution); historical, climate and ensemble APIs require the **Professional plan**; commercial use requires a paid licence | Free tier 10k calls/day; paid plans priced on monthly call budget (Standard 1M, Professional 5M) — **prices unverified, gate** | High | Licence boundary is the catch, not the data |
| NOAA / NCEI | US Government | Hourly surface observations (ISD), CDO API, forecasts | 1900s– | Hourly/daily | Station, hour | Global (dense US) | Bulk files and REST; token for CDO | **US public domain** | **Free** | High | Station-to-venue mapping is by nearest station; microclimate ignored |
| GTFS / GTFS-RT | Transit agencies, Mobility Database | Stops, routes, schedules, alerts | Per agency | Static + real-time | Stop, trip | Varies by city | Static zip, protobuf feed | Open licences, per agency | Free | Varies widely | Many agencies publish no real-time alerts; coverage uneven |
| ESPN (undocumented) | ESPN | Scoreboard, standings, team/player state | Seasons | Live | Game, team | Major leagues | `site.api.espn.com` JSON, keyless — **verified responding** | Not a public API; ToS likely prohibits commercial reuse (not read) | Free | Unofficial, unversioned, can vanish | Legal risk on a commercial product; schedule and injury data are the useful parts |
| Wikidata / OpenStreetMap | Wikimedia / OSMF | Venue capacity, coordinates, type, opening date; building footprints | Current | Continuous | Venue | Global | SPARQL / Overpass / dumps | CC0 (Wikidata); ODbL (OSM) | Free | Good, incomplete | Capacity is missing or stale for many venues; needs a manual pass against official charts |
| Official venue seating charts | Venues / promoters | Section, row, sightline, capacity | Current | Static | Section | Per venue | HTML/PDF | Per-site terms | Free, manual | — | Effort, not money: this is the only route to V15 and it is a human task per venue |
| FRED / ALFRED, BLS | US Government | Income, confidence, CPI, entertainment spend | Decades | Monthly/quarterly | National, metro | US | REST | Public domain | Free | High | Revised; use ALFRED vintages |

---

## 7. Ranking, and what is worthless here

**The three worth collecting first, in order.**

1. **Ticketmaster Discovery API.** Not for prices — it has none — but it is the free, lawful spine that
   makes V8 (competing supply), V9 (routing), V11 (calendar) and the venue join possible at all, and its
   attraction records hand you external identifiers for the artist, which is the only cheap route to V13.
   5,000 calls/day is enough to sweep every metro you care about weekly. Collect it first because
   everything else joins onto it.
2. **A venue table: capacity, type, coordinates, metro.** Wikidata and OSM give a free first pass;
   official charts fill the gaps by hand. This is the highest ratio of information to cost in the whole
   registry, because capacity is the scarcity denominator and **it is not in the contract**. Twenty
   minutes of manual work per venue beats every paid API in this document.
3. **NOAA/NCEI weather archive.** Chosen over Open-Meteo specifically because it is public domain and
   therefore has no commercial-licence problem, and over the paid options because the effect it measures
   is small. Collect only for outdoor venues, and store the *forecast issued at* the decision time, not
   the observation.

If the platform's inventory turns out to be sports-heavy rather than concert-heavy, **ESPN moves to
second place** ahead of weather: standings and injury state are the one exogenous shock with a mechanism
into willingness-to-pay that resolves inside the trading window, and the endpoint is free and live. Its
weakness is legal rather than technical — it is an undocumented endpoint, so a commercial product needs
a licensed feed instead.

**Worthless here.** Google Trends, Reddit sentiment, Spotify listeners, YouTube velocity, tourism flows,
airport proximity, school terms, and any attention index whatsoever — three separate reasons, each
sufficient alone: they cannot be collected lawfully at commercial scale, their licences forbid the exact
use (ML ingestion) the engine exists for, and they are proxies for demand the platform already measures
directly. The external signals that survive contact are substitutes (other events, other tour stops),
scarcity (capacity), and exogenous shocks to the product (team state, severe weather).

**Two items that outrank every source above, and are not sources at all.** Listing depth and ask
(V14) and seat coordinates (V15). Both are gaps in the wire contract, both are free to collect once the
platform writes them, and both dominate any external variable on expected value. The recommendation to
the operator is in `00-data-situation.md` and stands: four fields per listing event
(`listPriceLamports, listedAt, delistedAt|soldAt, delistReason`) plus section/row/seat on `Ticket`.

---

## 8. Money gates — these go to the operator, I have not assumed any of them can be bought

| Item | Price as published | What it buys | Verdict |
|---|---|---|---|
| X API pay-per-usage | $0.005 per Post read; 3M reads/month cap; ~$150/month at 1,000 posts/day | Social volume | **Do not buy.** No mechanism that survives §4.2 |
| Chartmetric Manager | $40/month, billed yearly | Historical artist listener/chart series | **Do not buy.** Downstream of a source that bans ML use |
| Open-Meteo commercial licence | Paid subscription, price not read | Lawful commercial weather | **Not yet.** Use NOAA, which is free and public domain |
| Ticketmaster Inventory Status / Partner | Not publicly priced; request-only | Real prices, fees, availability | **Worth one email.** The only lawful, listing-level primary price feed in existence. If the company can get partner access, it changes Phase 2A materially |
| tickets.dev capture API | From $50/month for 1,000 captures (vendor-published) | Listing-level scrapes across marketplaces | **Do not buy yet.** Solve the exposure gap inside our own platform first |
| Paid Google Trends aggregators (SerpAPI, DataForSEO, Glimpse) | Not verified | Trends | **Do not buy.** Rejected on mechanism as well as on access |

---

## 9. Limits of this report

- I could not verify Ticketmaster's price-field removal from Ticketmaster's own release notes; the
  claim rests on a vendor's October 2026 test of 2,397 US events plus the API reference still listing a
  field whose values that test did not find. Treat as *reported*, not *established*, and re-test the day
  anyone obtains a key. Same for the rate limits: the docs and the vendor disagree on page size (500 vs
  200) and the FAQ reportedly says 2 req/s against a tested 5.
- SeatGeek's terms, Viagogo/Vivid/AXS/TicketNetwork access, and whether any on-chain ticketing
  programme writes fiat resale prices into a transaction are **not** established. I did not have the
  standing to test them and will not assert them.
- Bibliographic details for the four ticket-market papers I cite from memory — Sweeting (2012, *JPE*),
  Leslie & Sorensen (2014, *REStud*), Bhave & Budish (2017, NBER WP), Krueger (2019, *Rockonomics*) —
  were not re-checked in this run. The two claims I did verify are the weather-attendance paper and
  every API/terms fact above; both are cited from the pages quoted.

**Handover.** Phase 2D should not re-derive the rejected list. The two open questions that matter are
(a) does the company's internal ledger hold seat coordinates and listing events that the wire contract
omits, and (b) can the company obtain Ticketmaster partner access — both are operator questions, not
research questions.

---

## CORRECTION (2026-11-07T11:28Z) — the headline counts are not derivable from the tables

Appended by the corrections pass after `records/findings/00-verification-round1.md` §6. Nothing above is
deleted.

**Withdrawn sentence, "What I concluded":**

> "Nineteen candidate variables were examined against §4.2 and eleven survive at usable priority."

**What the file's own tables give, counted on 2026-11-07.**

Table C-1 has **17** rows, V1 to V17. Table C-2 has **11** rows, so 28 candidates were examined, not 19. The
priority column of C-1, counted row by row:

| Priority | Variables | Count |
|---|---|---|
| 1 | V1, V2, V3, V4, V5 | 5 |
| 2 | V6, V7, V8, V9 | 4 |
| 3 | V10, V11, V12, V13 | 4 |
| 4 | V16, V17 | 2 |
| 0 | V14, V15 | 2 |
| **total** | | **17** |

**Corrected statement.** Nine variables are at priority 1–2, which is the reading of "usable priority" the file
itself sets up in §1 (1 = build now, 2 = build after the core); of those nine, four are obtainable from the
contract today (V1, V2, V3, V5) and five need outside data (V4, V6, V7, V8, V9). Fifteen are at priority above
0. Two are at priority 0 and blocked on a data requirement (V14 listing depth, V15 seat coordinates), and
eleven are rejected in Table C-2.

No reading of the file yields 19 candidates or 11 survivors at usable priority. The number 11 does exist
twice in the record, and neither is a survivor count: it is the number of rows in Table C-2 (rejected), and it
is the number of admitted variables that are obtainable only outside the contract (V4, V6–V13, V16, V17).
The most likely explanation is that the abstraction was written from memory of the reject table. Nothing is
substituted for it here beyond the counts above.

**Why it was not caught.** `records/C-variable-registry.md` C-5 and the P1.D row of `records/A-research-ledger.md`
both already record that the headline does not reconcile, and both follow the tables. They are right and this
correction brings the file into line with them.

**Consequence.** None of the substance changes: the admission test, the clock as the decisive filter, the
licence rejections, and the finding that listing depth and seat coordinates are the two highest-value variables
and neither is obtainable. What is withdrawn is the abstract's count, which a reader could otherwise cite
without opening the tables.

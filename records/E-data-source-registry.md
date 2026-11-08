# E-data-source-registry

**Programme section:** §2.E. **Seeded:** 2026-11-07. **Last touched:** 2026-11-08T06:25Z, extended with S29 (primary legislation, for the region-aware
resale caps) after the 05:54Z extension with S28 (the memo program); no
existing entry was edited or renumbered.

**Extended 2026-11-08T08:30Z: the header for 06:25Z above is kept as it was written.** The ten-feature
documentation pass added S30 to S32 later the same day, with no existing entry edited or renumbered;
the count line below now carries both the 27 it said before that pass and the 32 it says after it,
each with its date.
**Filled from:** `findings/01-d-external.md` (Tables C-1, C-2, E-1, §8 money gates, §9 limits)
and `records/00-data-situation.md` (what the platform itself yields, Gaps 1–4).

This is the curated index over the raw finding. The finding is the primary record and is not
edited; where the two disagree the finding wins and the conflict is recorded in `F`.

## How to read this file

- **Layout:** one index row per source (below), then one record per source carrying the eleven
  mandatory §2.E fields in full. The index exists because a fifteen-column table is unreadable;
  the per-source record is where the content lives. Nothing is only in the index.
- **"not stated in 01-d"** means the report does not state that field. It is not an invitation to
  fill it plausibly. No price, rate limit or licence term in this file was inferred.
- **Claim status** is per source claim, using three labels:
  - `verified-today` — I re-checked it in this run; the method and result are quoted.
  - `cited-not-reverified` — the report states it with a citation; I did not re-check it.
  - `reported-not-established` — the report itself flags it as unproven (§9). Carried as such.
- **Evidence class** is the programme §4.3 class the report assigns (A–E), or "not stated in
  01-d" where it assigns none. Nothing here upgrades a class.
- **Usability for training** is separated from usability for inference because three of these
  sources bar ML ingestion outright; that bar survives into this registry and is not softened by
  the fact that the data would otherwise be useful.

### Verification performed in this run (2026-11-07, ~10:40–10:47Z)

Bounded single `curl` calls, no recursion, nothing written outside `/tmp`.

| Claim | Method | Result |
|---|---|---|
| SeatGeek requires a client id | `GET https://api.seatgeek.com/2/events?per_page=1` | **HTTP 403**, `"Client is required - visit \"https://seatgeek.com/account/develop\""` (code 40307). Confirms report. |
| Ticketmaster Discovery requires a key | `GET https://app.ticketmaster.com/discovery/v2/events.json?size=1` (no key) | **HTTP 401**, `Failed to resolve API Key variable request.queryparam.apikey`. Confirms a key is mandatory; **it does not test `priceRanges`**, because I hold no key. |
| Google Trends endpoints are disallowed by robots.txt | `GET https://www.google.com/robots.txt` and `https://trends.google.com/robots.txt` | **HTTP 200** both. `www.google.com` lines 122–131 include `Disallow: /trends?`, `Disallow: /trends/explore?`, `Disallow: /trends/api`; `trends.google.com` disallows `/explore?` and `/trends/explore?`. Confirms report. |
| ESPN undocumented endpoint is keyless and live | `GET https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard` | **HTTP 200**, JSON scoreboard returned with no key. Confirms report. |
| StubHub developer docs are a live Docusaurus site | `GET https://developer.stubhub.com/` | **HTTP 200**, `generator: "Docusaurus …"`. Does not re-test the seller-side Inventory wording; that stays cited. |
| Get Protocol on-chain docs are not publicly readable | `GET https://docs.get-protocol.io/` | **HTTP 302 → `/inactive`**. Report recorded 401 without an account; the state differs today but the conclusion (no public docs, price-on-chain unverified) is unchanged. |
| Open-Meteo archive is reachable without a key | `GET https://archive-api.open-meteo.com/v1/archive?...&daily=temperature_2m_max` | **HTTP 200**, daily series returned, no key. Does not re-read the non-commercial licence boundary; that stays cited. |

---

## Index — one row per source

| # | Source | Provider | Availability verdict | Training / inference | Class |
|---|---|---|---|---|---|
| S1 | Discovery API v2 | Ticketmaster | Obtainable today (free key) — but **no price data** | Inference + training (no revenue-derivation right; terms unread in full) | not stated in 01-d |
| S2 | Partner / Inventory Status / Top Picks APIs | Ticketmaster | Obtainable with effort (commercial relationship, request-only) | Inference (primary); training not stated in 01-d | not stated in 01-d |
| S3 | SeatGeek Platform API | SeatGeek | Obtainable with effort (client-id approval); price access **not established** | not stated in 01-d | not stated in 01-d |
| S4 | StubHub API | StubHub | Obtainable with effort (app credentials) — but it is **seller-side, not a market price feed** | Inference (own inventory); training prohibited? not stated in 01-d | not stated in 01-d |
| S5 | Viagogo, Vivid Seats, AXS, TicketNetwork, Gametime | various | Obtainable only by scraping; no public self-serve API found → **not lawfully obtainable** at commercial scale, exposure unresolved | not stated in 01-d | not stated in 01-d |
| S6 | tickets.dev capture API | tickets.dev (third party) | Obtainable today (paid) | not stated in 01-d | not stated in 01-d |
| S7 | Get Protocol / on-chain ticketing | GET Protocol and others | **Not obtainable at all** as a price source on current evidence | not stated in 01-d | **E** |
| S8 | Solana RPC — our own programme ledger | Solana / the platform | Obtainable today (own data) | Training + inference (own data) | not stated in 01-d |
| S9 | Google Trends | Google | **Not lawfully obtainable** | Neither — collection itself is the breach | **D at best, E in practice** (report) |
| S10 | X API v2 | X | Obtainable today (pay-per-usage) — rejected on mechanism | Training not stated in 01-d; redistribution restricted | **E** (report) |
| S11 | Reddit Data API | Reddit | Obtainable with effort (free tier) but **barred from ML training** | **Inference only; ML training forbidden** | **E** (report) |
| S12 | Spotify Web API | Spotify | Obtainable today (free) but **barred from ML ingestion** | **Neither — content may not be used to train or be ingested into an ML model** | not stated in 01-d |
| S13 | YouTube (view velocity) | YouTube | **Not obtainable** lawfully at scale (no public velocity API; scraping contradicts same ToS logic) | not stated in 01-d | **E** (report) |
| S14 | Chartmetric | Chartmetric | Obtainable today (paid) — rejected on mechanism | not stated in 01-d | not stated in 01-d |
| S15 | Open-Meteo | Open-Meteo | Obtainable today (free tier, **non-commercial**) | Inference under free tier; commercial/ML use requires a paid licence — terms not fully read | not stated in 01-d |
| S16 | NOAA / NCEI | US Government | Obtainable today, free, public domain | Training + inference | not stated in 01-d |
| S17 | GTFS / GTFS-RT | transit agencies, Mobility Database | Obtainable today (open feeds), coverage uneven | Training + inference | not stated in 01-d |
| S18 | ESPN scoreboard/standings endpoint | ESPN (undocumented) | Obtainable today (keyless) — legal risk on a commercial product | Inference; training not stated in 01-d | **B** on attendance / **D** on price (as V10) |
| S19 | Wikidata | Wikimedia | Obtainable today, free (CC0) | Training + inference | not stated in 01-d |
| S20 | OpenStreetMap | OSMF | Obtainable today, free (ODbL, share-alike) | Training + inference subject to ODbL | not stated in 01-d |
| S21 | Official venue seating charts | venues / promoters | Obtainable with effort (manual, per venue) | Training + inference | not stated in 01-d |
| S22 | FRED / ALFRED, BLS | US Government | Obtainable today, free, public domain | Training + inference | not stated in 01-d |
| S23 | Census / DMA tables | US Census Bureau / Nielsen (DMA) | Obtainable today (Census free; DMA rank source not stated in 01-d) | Training + inference | not stated in 01-d |
| S24 | MusicBrainz | MetaBrainz | Obtainable today, free | Training + inference (licence terms not read — not stated in 01-d) | not stated in 01-d |
| S25 | Public holiday and school-term calendars | not stated in 01-d | Obtainable today | Training + inference | not stated in 01-d |
| S26 | Paid Google Trends aggregators (SerpAPI, DataForSEO, Glimpse) | various | Obtainable today (paid) — rejected on mechanism | not stated in 01-d | not stated in 01-d |
| S27 | Journalism / unstructured press | various | Obtainable today, but unstructured and uncountable | Inference only (human-set override); never a feature | **E** (report) |
| S28 | Memo program (per-cluster id) | Solana, and the `solana` CLI's shipped memo program | Obtainable today: public, executable, no key; **the id differs by cluster** | Inference only; a commitment, not a dataset | **A** on devnet, **D** on mainnet-beta and localnet (see record) |
| S29 | Primary legislation on ticket resale (the region-caps table) | each jurisdiction's legislation service | Obtainable today for the rows marked A; walls elsewhere | Neither: a constraint applied at decision time | A for the rows read, E for `unknown` |
| S30 | Token-2022 transfer-fee extension | Token-2022 program, on every cluster | Obtainable today: public, executable, no key | Neither: a mechanism the product tested, not a dataset | **A** for the ceiling measured on a local validator |
| S31 | The band feed, `["band", mint]` | this repository's own program | Obtainable today on the local validator only | Inference: an input a consumer must carry the uncertainty fields from | **A** for the account shape and its fields; **E** for any market claim |
| S32 | A live child model as a decision source (deepseek) | the model provider, through the `pi` CLI | Obtainable today, paid, operator's account | Neither: a policy that chooses an action, not a feature | **A** for the measured cost; **D** for whether it trades better |

**[Historic count, superseded 2026-11-08.]** This line recorded 27 sources before the ten-feature
documentation pass added S30 to S32; it is kept because the record is append-only:
Count: **27 sources registered** (S28 and S29 were added 2026-11-08; no existing entry was renumbered
or moved).

Count: **32 sources registered** (S30 to S32 were added 2026-11-08 by the ten-feature documentation pass; S29 was added 2026-11-08 by the region-caps pass; S28 was added 2026-11-08; no existing entry was renumbered or
moved).

---

## Per-source records

### S1 — Ticketmaster Discovery API v2

| Field | Value |
|---|---|
| Provider or source | Ticketmaster |
| Data type | Event catalogue: names, dates, venue, city, coordinates, classifications, ticket limit, public on-sale and presale windows, static seatmap URL, attraction cross-IDs (Spotify, MusicBrainz, Wikipedia). **No price data.** |
| Historical depth | Current and future events only; no history |
| Update frequency | Near-real-time |
| Granularity | Event, venue, attraction |
| Geographic coverage | 230k+ events; US/CA/MX/AU/NZ/UK/EU (vendor-reported) |
| API or collection method | REST, free API key. Key requirement verified-today (401 without one) |
| Licensing and access restrictions | No deriving revenues from the API without Ticketmaster's terms; cache only "reasonable periods"; remove content on request within 24 h; must not replicate the Ticketmaster UX |
| Estimated collection cost | **Free.** 5,000 calls/day, 5 req/s, paging stops near result 1,000 (vendor-tested; docs say max page size 500). Cited-not-reverified — I hold no key. The report notes docs/vendor/FAQ disagree (page size 500 vs 200; 5 req/s tested vs 2 in the FAQ) |
| Reliability | Good; 0.17–0.9 s/call (vendor-reported) |
| Known limitations | **No price data.** `priceRanges` present on 3 of 2,397 US events in a vendor test (Oct 2026); release notes reportedly dropped price fields from the Discovery *Feed* on 2025-03-11; the API reference still documents the field. No listing, seat, or sold-price endpoint |
| Availability verdict | **Obtainable today** (free key), with no prices |
| Training vs inference | Both, subject to the no-revenue-derivation term. **The report does not state an ML-training prohibition for Ticketmaster**; do not assume one, and do not assume its absence is permission — the terms were not read in full |
| Claim status | Structure/access: verified-today (401 without key). Price-field removal: **reported-not-established** per §9 — do not cite it as established |
| Evidence class | not stated in 01-d |
| Why it is in the registry | The free, lawful spine for V8 competing supply, V9 routing, V11 calendar and the venue join; its attraction records give the artist external identifiers. Ranked first to collect |

### S2 — Ticketmaster Partner / Inventory Status / Top Picks APIs

| Field | Value |
|---|---|
| Provider or source | Ticketmaster |
| Data type | Real prices, fees, availability, holds |
| Historical depth | not stated in 01-d |
| Update frequency | Live; "hourly or better" |
| Granularity | Event, price range |
| Geographic coverage | NA / official partners |
| API or collection method | Partner agreement, request-only. Inventory Status returned 401 to a free key (vendor-reported) |
| Licensing and access restrictions | Not public; commercial relationship required |
| Estimated collection cost | **Not purchasable.** Price not published |
| Reliability | not stated in 01-d |
| Known limitations | Gate: requires a commercial relationship. This is the only lawful listing-level primary price feed the report could identify |
| Availability verdict | **Obtainable with effort** — one email to the operator's Ticketmaster contact |
| Training vs inference | Inference is the intended use; training rights not stated in 01-d |
| Claim status | cited-not-reverified (vendor-reported) |
| Evidence class | not stated in 01-d |
| Why it is in the registry | §8: "Worth one email." If partner access lands it changes Phase 2A materially |

### S3 — SeatGeek Platform API

| Field | Value |
|---|---|
| Provider or source | SeatGeek |
| Data type | Events, performers, venues, taxonomy; listings where authorised |
| Historical depth | Current only |
| Update frequency | Near-real-time |
| Granularity | Event |
| Geographic coverage | US-centric |
| API or collection method | REST with client id; approval required. **Verified-today: HTTP 403 "Client is required"** without one |
| Licensing and access restrictions | Terms not verified this run (report §9 repeats this) |
| Estimated collection cost | Client id requires approval; no published price |
| Reliability | not stated in 01-d |
| Known limitations | **Whether listings/prices are exposed to a non-partner is not established** (§9). Treat as unproven until tested with a client id |
| Availability verdict | **Obtainable with effort** (client-id approval); price access unknown |
| Training vs inference | not stated in 01-d |
| Claim status | API-live-and-gated: verified-today. Price exposure: cited-not-reverified / not established |
| Evidence class | not stated in 01-d |
| Why it is in the registry | Candidate secondary-market price feed; the report could not close it, so it stays open rather than rejected |

### S4 — StubHub API

| Field | Value |
|---|---|
| Provider or source | StubHub |
| Data type | Account, Catalog, Inventory, Sales, Webhooks |
| Historical depth | Current |
| Update frequency | Real-time |
| Granularity | Event, venue, category |
| Geographic coverage | Markets StubHub operates in |
| API or collection method | REST, OAuth2, sandbox + production. Docs site verified-today (HTTP 200, Docusaurus) |
| Licensing and access restrictions | Requires approved app credentials; terms not read |
| Estimated collection cost | Not published |
| Reliability | Docusaurus docs, versioned, maintained |
| Known limitations | **It is seller-side.** The Inventory API is "list seller listings / create a seller listing" — it manages *your* inventory, not the market's. Not a market price feed. Catalog gives the event graph only |
| Availability verdict | **Obtainable with effort**, but it does not answer the question we need it for |
| Training vs inference | Inference; training not stated in 01-d |
| Claim status | Docs-site-live: verified-today. Seller-side wording: cited-not-reverified |
| Evidence class | not stated in 01-d |
| Why it is in the registry | Registered as a **rejected** source so nobody re-proposes it expecting market prices |

### S5 — Viagogo, Vivid Seats, AXS, TicketNetwork, Gametime

| Field | Value |
|---|---|
| Provider or source | various (named together in the report) |
| Data type | Listings, prices |
| Historical depth | — (not stated in 01-d) |
| Update frequency | — (not stated in 01-d) |
| Granularity | — (not stated in 01-d) |
| Geographic coverage | — (not stated in 01-d) |
| API or collection method | No public self-serve API found. Scraping only; third-party capture services exist |
| Licensing and access restrictions | Scraping raises ToS and legal exposure. Per-site terms **not read** |
| Estimated collection cost | tickets.dev from $50/month for 1,000 captures (vendor-published) |
| Reliability | — (not stated in 01-d) |
| Known limitations | Vendor capture services offload the legal risk but add a dependency and a per-call cost. Access terms unread, so the report does not assert them |
| Availability verdict | **Not lawfully obtainable** at commercial scale on current evidence; obtaining them means scraping and accepting unresolved exposure |
| Training vs inference | not stated in 01-d |
| Claim status | cited-not-reverified (§9 explicitly declines to assert access) |
| Evidence class | not stated in 01-d |

### S6 — tickets.dev capture API

| Field | Value |
|---|---|
| Provider or source | tickets.dev (third-party capture vendor) |
| Data type | Listing-level scrapes across marketplaces |
| Historical depth | not stated in 01-d |
| Update frequency | not stated in 01-d |
| Granularity | Listing-level captures |
| Geographic coverage | not stated in 01-d |
| API or collection method | Paid capture API |
| Licensing and access restrictions | not stated in 01-d; it is a pass-through of scraped data, so the upstream ToS exposure does not disappear, it is delegated |
| Estimated collection cost | From $50/month for 1,000 captures (vendor-published) |
| Reliability | not stated in 01-d |
| Known limitations | §8 verdict: **do not buy yet** — solve the exposure gap inside our own platform first |
| Availability verdict | **Obtainable today** (paid) |
| Training vs inference | not stated in 01-d |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d |

### S7 — Get Protocol / on-chain ticketing

| Field | Value |
|---|---|
| Provider or source | GET Protocol and others |
| Data type | NFT ticket ownership, transfer events |
| Historical depth | Chain history |
| Update frequency | Per block |
| Granularity | Token |
| Geographic coverage | not stated in 01-d |
| API or collection method | Public RPC / explorer |
| Licensing and access restrictions | Public chain data is free to read |
| Estimated collection cost | Free |
| Reliability | not stated in 01-d |
| Known limitations | **Not verified** whether a fiat resale *price* is written on chain rather than settled in their backend — `docs.get-protocol.io` was inaccessible (401 in the report; **302 → `/inactive` today**). Even if it is, the events differ from ours and the population is small |
| Availability verdict | **Not obtainable at all** as a price source on current evidence |
| Training vs inference | not stated in 01-d |
| Claim status | Inaccessibility: verified-today (302/`inactive`). Price-on-chain: reported-not-established |
| Evidence class | **E** until shown otherwise |

### S8 — Solana RPC — our own programme ledger

| Field | Value |
|---|---|
| Provider or source | Solana; the platform's own ledger |
| Data type | Our own ledger in full, with slot ordering: `LedgerEntry[]` (issue, sale, transfer, redeem, revoke; `priceLamports`, `markupBps`, `signature`, `slot`, `occurredAt`), `Ticket`, `Event`, `ResaleStats`/`EventAnalytics` |
| Historical depth | Full history of the programme, once a programme exists |
| Update frequency | Per slot |
| Granularity | Transaction |
| Geographic coverage | Our platform |
| API or collection method | JSON-RPC, public endpoints rate-limited. An indexer is the real cost (effort, not money) |
| Licensing and access restrictions | Our own data; no third-party licence |
| Estimated collection cost | Free at prototype volume |
| Reliability | High |
| Known limitations | Public-endpoint rate limits. **More importantly, the wire contract omits four things** (`00-data-situation.md` §4): no listing exposure (Gap 1 — so `P(sale \| price, exposure, t)` is not identified), a policy-truncated price ceiling (Gap 2), no seat coordinates (Gap 3), no fee/royalty/settlement field (Gap 4). Also: **no backend exists and no deployed program is referenced** (`00-data-situation.md` §1), so today this source is a specification, not a feed. Primary inventory is a snapshot with no velocity; `Event.status` transitions are not timestamped |
| Availability verdict | **Obtainable today** — subject to the platform actually writing these fields; the four-field listing request plus section/row/seat is the recommendation in `00-data-situation.md` |
| Training vs inference | Both. Own data, no third-party restriction |
| Claim status | The contract absences are verified in `00-data-situation.md` against `lib/types.ts`; the backend's existence is verified absent there too |
| Evidence class | Class B/C at best from own data — `00-data-situation.md` §5: **no result in this programme can be class A from our own data** |

### S9 — Google Trends

| Field | Value |
|---|---|
| Provider or source | Google |
| Data type | Search interest index |
| Historical depth | 2004– |
| Update frequency | Daily / weekly |
| Granularity | Query, region |
| Geographic coverage | Global |
| API or collection method | **No official API.** Scraping the endpoints every scraper uses |
| Licensing and access restrictions | **robots.txt disallows `/trends/explore?` and `/trends/api`** (verified-today, `www.google.com/robots.txt` lines 122–131; `trends.google.com/robots.txt` disallows `/explore?` and `/trends/explore?`). Google's ToS prohibit using automated means to access content in violation of the machine-readable instructions on its pages. So collection is a ToS breach, not merely a grey area |
| Estimated collection cost | Free but **not lawfully collectable**. Paid aggregators exist; prices not verified in 01-d |
| Reliability | — (not stated in 01-d) |
| Known limitations | Rejected on access; **also weak on mechanism** — it forecasts demand the platform already observes. Normalised per query, resampled, and revised |
| Availability verdict | **Not lawfully obtainable** |
| Training vs inference | **Neither** — the bar is at collection, so there is no lawful dataset to train on or infer from |
| Claim status | robots.txt: verified-today. ToS wording: cited-not-reverified (quoted in the report, not re-read today) |
| Evidence class | **D at best, and E in practice** |

### S10 — X API v2

| Field | Value |
|---|---|
| Provider or source | X |
| Data type | Post volume, text, engagement |
| Historical depth | 7 days recent; full archive on enterprise |
| Update frequency | Real-time |
| Granularity | Post, user |
| Geographic coverage | Global |
| API or collection method | REST, OAuth |
| Licensing and access restrictions | Developer policy; content redistribution restricted. Pay-per-usage |
| Estimated collection cost | **$0.005 per Post read, $0.010 per User read; 3M Post reads per monthly cycle cap. 1,000 posts/day ≈ $150/month; 10,000/day ≈ $1,500/month.** cited-not-reverified |
| Reliability | Good |
| Known limitations | Cost scales with the thing you want (volume), and deleted posts vanish retroactively. Rejected on mechanism before cost: the sentiment signal on a 1–10 week horizon is dominated by the market's own price |
| Availability verdict | **Obtainable today** (paid) — recommended against |
| Training vs inference | Training rights **not stated in 01-d**; redistribution is restricted, which constrains storing derived text. Do not treat as trainable on the report's evidence |
| Claim status | Prices and caps: cited-not-reverified |
| Evidence class | **E** |

### S11 — Reddit Data API

| Field | Value |
|---|---|
| Provider or source | Reddit |
| Data type | Posts, comments, votes |
| Historical depth | Full |
| Update frequency | Real-time |
| Granularity | Post, comment |
| Geographic coverage | Global |
| API or collection method | REST, OAuth |
| Licensing and access restrictions | Fees reserved; commercial use or research beyond the rate limit needs a separate agreement; **no right to use user content for training an ML model without rightsholder permission**; no deriving revenues from the API without written approval |
| Estimated collection cost | Free tier exists; high-volume terms are contractual and not stated in 01-d |
| Reliability | Good |
| Known limitations | Rejected on the ML clause, not on access |
| Availability verdict | **Obtainable with effort** (free tier) — but the intended use is barred |
| Training vs inference | **Inference only. ML training forbidden.** The engine exists to be trained; this source cannot feed it |
| Claim status | cited-not-reverified (terms quoted in the report, not re-read today) |
| Evidence class | **E** |

### S12 — Spotify Web API

| Field | Value |
|---|---|
| Provider or source | Spotify |
| Data type | Track/artist metadata, popularity, audio features |
| Historical depth | Current |
| Update frequency | not stated in 01-d |
| Granularity | Track, artist |
| Geographic coverage | Global |
| API or collection method | REST, OAuth |
| Licensing and access restrictions | **Content may not be used to train an ML model or be ingested into one** |
| Estimated collection cost | Free |
| Reliability | not stated in 01-d |
| Known limitations | `popularity` and `followers` on the artist object marked **deprecated**; `audio-features` deprecated. Rejected on licence, not on mechanism. A listener count is a stock, not a shock |
| Availability verdict | **Obtainable today** (free) — but barred from the use |
| Training vs inference | **Neither.** "Ingested into" an ML model is the operative phrase: even as a live inference feature it is barred |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (rejected on licence) |

### S13 — YouTube (view velocity)

| Field | Value |
|---|---|
| Provider or source | YouTube |
| Data type | View velocity, engagement |
| Historical depth | not stated in 01-d |
| Update frequency | not stated in 01-d |
| Granularity | Video |
| Geographic coverage | Global |
| API or collection method | No public velocity API; scraping contradicts the same ToS logic as S9/S10 |
| Licensing and access restrictions | not stated in 01-d beyond the above |
| Estimated collection cost | not stated in 01-d |
| Reliability | not stated in 01-d |
| Known limitations | Rejected on both access and mechanism: the mechanism (awareness) is upstream of a variable we already have |
| Availability verdict | **Not obtainable** lawfully at scale |
| Training vs inference | not stated in 01-d |
| Claim status | cited-not-reverified |
| Evidence class | **E** |

### S14 — Chartmetric

| Field | Value |
|---|---|
| Provider or source | Chartmetric |
| Data type | Cross-platform artist metrics, historical listener/chart series |
| Historical depth | Multi-year |
| Update frequency | Daily |
| Granularity | Artist |
| Geographic coverage | Global |
| API or collection method | Web + API |
| Licensing and access restrictions | Commercial licence |
| Estimated collection cost | **Manager $40/month, billed yearly**; higher tiers quote-only. cited-not-reverified |
| Reliability | Commercial |
| Known limitations | Still downstream of the same platform data (S12) that bans ML use; adds cost without adding mechanism. §8 verdict: do not buy |
| Availability verdict | **Obtainable today** (paid) — rejected |
| Training vs inference | not stated in 01-d; **the upstream licence question is unresolved**, so treat as not trainable until someone reads the terms |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d |

### S15 — Open-Meteo

| Field | Value |
|---|---|
| Provider or source | Open-Meteo |
| Data type | Forecast + historical weather, 30+ models |
| Historical depth | Archive (extent not stated in 01-d) |
| Update frequency | Hourly |
| Granularity | Point, hourly |
| Geographic coverage | Global |
| API or collection method | REST, no key. **Verified-today: archive endpoint returned HTTP 200 without a key** |
| Licensing and access restrictions | Free tier is **non-commercial only** (CC-BY 4.0, attribution); historical, climate and ensemble APIs require the **Professional plan**; commercial use requires a paid licence |
| Estimated collection cost | Free tier 10k calls/day (cited-not-reverified); paid plans priced on monthly call budget (Standard 1M, Professional 5M) — **prices unverified, gate** |
| Reliability | High |
| Known limitations | **The licence boundary is the catch, not the data.** And the effect it measures is small (§4: weather is a quantity variable, price effect weak) |
| Availability verdict | **Obtainable today** on the free tier; commercial use is a gate |
| Training vs inference | Inference under the free tier; **training and commercial use require a licence whose ML terms are not stated in 01-d** |
| Claim status | Keyless access: verified-today. Licence boundary: cited-not-reverified |
| Evidence class | not stated in 01-d (V12 is class B for attendance) |

### S16 — NOAA / NCEI

| Field | Value |
|---|---|
| Provider or source | US Government (NOAA/NCEI) |
| Data type | Hourly surface observations (ISD), CDO API, forecasts |
| Historical depth | 1900s– |
| Update frequency | Hourly / daily |
| Granularity | Station, hour |
| Geographic coverage | Global (dense US) |
| API or collection method | Bulk files and REST; token for CDO |
| Licensing and access restrictions | **US public domain** — no commercial-licence problem |
| Estimated collection cost | **Free** |
| Reliability | High |
| Known limitations | Station-to-venue mapping is by nearest station; microclimate ignored. Non-US venues are weaker. Store the *forecast issued at* the decision time, not the observation |
| Availability verdict | **Obtainable today** |
| Training vs inference | **Both** — public domain, no restriction found in 01-d |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d |

### S17 — GTFS / GTFS-RT

| Field | Value |
|---|---|
| Provider or source | Transit agencies; Mobility Database |
| Data type | Stops, routes, schedules, alerts |
| Historical depth | Per agency |
| Update frequency | Static + real-time |
| Granularity | Stop, trip |
| Geographic coverage | Varies by city |
| API or collection method | Static zip, protobuf feed |
| Licensing and access restrictions | Open licences, per agency |
| Estimated collection cost | Free |
| Reliability | Varies widely |
| Known limitations | Many agencies publish no real-time alerts; coverage uneven. Only *shocks* matter; the static part is absorbed by a venue fixed effect |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V17 is class D) |

### S18 — ESPN scoreboard/standings endpoint (undocumented)

| Field | Value |
|---|---|
| Provider or source | ESPN |
| Data type | Scoreboard, standings, team/player state |
| Historical depth | Seasons |
| Update frequency | Live |
| Granularity | Game, team |
| Geographic coverage | Major leagues |
| API or collection method | `site.api.espn.com` JSON, keyless — **verified-today: HTTP 200, no key** |
| Licensing and access restrictions | Not a public API; ToS likely prohibits commercial reuse (**not read** in 01-d) |
| Estimated collection cost | Free |
| Reliability | Unofficial, unversioned, can vanish |
| Known limitations | **Legal risk on a commercial product**; a licensed feed would be needed. Schedule and injury state are the useful parts. This is a repricing variable for most events, not a pricing one — it resolves after the primary on-sale |
| Availability verdict | **Obtainable today** (technically); the legal question is a gate |
| Training vs inference | Inference; training not stated in 01-d |
| Claim status | Liveness: verified-today. ToS: cited-not-reverified |
| Evidence class | **B** on attendance / **D** on price (as V10) |
| Why it is in the registry | §7: moves to second place if the platform's inventory is sports-heavy. The one exogenous shock with a mechanism resolving inside the trading window |

### S19 — Wikidata

| Field | Value |
|---|---|
| Provider or source | Wikimedia |
| Data type | Venue capacity, coordinates, type, opening date |
| Historical depth | Current |
| Update frequency | Continuous |
| Granularity | Venue |
| Geographic coverage | Global |
| API or collection method | SPARQL / dumps |
| Licensing and access restrictions | **CC0** |
| Estimated collection cost | Free |
| Reliability | Good, incomplete |
| Known limitations | Capacity missing or stale for many venues; needs a manual pass against official charts |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both (CC0) |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d |

### S20 — OpenStreetMap

| Field | Value |
|---|---|
| Provider or source | OSMF |
| Data type | Building footprints, coordinates, venue geometry |
| Historical depth | Current |
| Update frequency | Continuous |
| Granularity | Venue / building |
| Geographic coverage | Global |
| API or collection method | Overpass / dumps |
| Licensing and access restrictions | **ODbL** — share-alike obligations on derived databases |
| Estimated collection cost | Free |
| Reliability | Good, incomplete |
| Known limitations | Same as S19 on capacity; also an attribution/share-alike obligation that has to be honoured in whatever the derived table becomes |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both, subject to ODbL |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d |

### S21 — Official venue seating charts

| Field | Value |
|---|---|
| Provider or source | Venues / promoters |
| Data type | Section, row, sightline, capacity |
| Historical depth | Current |
| Update frequency | Static |
| Granularity | Section |
| Geographic coverage | Per venue |
| API or collection method | HTML / PDF, manual |
| Licensing and access restrictions | Per-site terms (not read) |
| Estimated collection cost | Free, manual — **effort, not money** |
| Reliability | — (not stated in 01-d) |
| Known limitations | **This is the only route to V15 seat coordinates, and it is a human task per venue.** Transcription errors are the obvious failure mode |
| Availability verdict | **Obtainable with effort** |
| Training vs inference | Both (factual venue geometry) |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V15 is class A) |
| Why it is in the registry | §7: twenty minutes of manual work per venue beats every paid API in the finding |

### S22 — FRED / ALFRED, BLS

| Field | Value |
|---|---|
| Provider or source | US Government |
| Data type | Income, confidence, CPI, entertainment spend |
| Historical depth | Decades |
| Update frequency | Monthly / quarterly |
| Granularity | National, metro |
| Geographic coverage | US |
| API or collection method | REST |
| Licensing and access restrictions | Public domain |
| Estimated collection cost | Free |
| Reliability | High |
| Known limitations | Revised — **use ALFRED vintages, not today's series**, or the feature carries information from after `t`. Moves every event at once, so it cannot explain cross-sectional differences within a season |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V16 is class B) |

### S23 — Census / DMA tables

| Field | Value |
|---|---|
| Provider or source | US Census Bureau; DMA rank source not stated in 01-d |
| Data type | Metro population; DMA rank |
| Historical depth | Decennial + annual estimates (not stated in detail in 01-d) |
| Update frequency | not stated in 01-d |
| Granularity | Metro |
| Geographic coverage | US |
| API or collection method | not stated in 01-d |
| Licensing and access restrictions | Public data (Census); DMA rank is a licensed Nielsen product and its terms are **not stated in 01-d** |
| Estimated collection cost | **Free** (per Table C-1, V7) |
| Reliability | not stated in 01-d |
| Known limitations | Scaler only; a control, not a driver. Second-order, collinear with other metro-level series |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both for Census; the DMA component's terms are not stated in 01-d |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V7 is class B) |

### S24 — MusicBrainz

| Field | Value |
|---|---|
| Provider or source | MetaBrainz (named alongside Wikidata and release calendars in Table C-1, V13) |
| Data type | Artist/release metadata, release dates |
| Historical depth | not stated in 01-d |
| Update frequency | Continuous |
| Granularity | Artist, release |
| Geographic coverage | Global |
| API or collection method | not stated in 01-d (web service / dumps implied, not verified) |
| Licensing and access restrictions | Free; **licence terms not stated in 01-d** (some MetaBrainz data is CC0, some CC-BY-NC-SA — do not assume) |
| Estimated collection cost | Free |
| Reliability | not stated in 01-d |
| Known limitations | Release dates move; use the announced date at `t`. Low predictive value (V13 is class D) |
| Availability verdict | **Obtainable today** |
| Training vs inference | not stated in 01-d — **the non-commercial possibility must be checked before any training use** |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V13 is class D) |

### S25 — Public holiday and school-term calendars

| Field | Value |
|---|---|
| Provider or source | not stated in 01-d |
| Data type | Holiday dates; school terms |
| Historical depth | not stated in 01-d |
| Update frequency | Static |
| Granularity | Date, region |
| Geographic coverage | not stated in 01-d (jurisdiction-level implied) |
| API or collection method | Static calendar join |
| Licensing and access restrictions | not stated in 01-d |
| Estimated collection cost | Free |
| Reliability | not stated in 01-d |
| Known limitations | Low–medium value (V11, priority 3); school terms were folded into V11 rather than kept separate |
| Availability verdict | **Obtainable today** |
| Training vs inference | Both |
| Claim status | cited-not-reverified |
| Evidence class | not stated in 01-d (V11 is class B) |

### S26 — Paid Google Trends aggregators (SerpAPI, DataForSEO, Glimpse)

| Field | Value |
|---|---|
| Provider or source | Various (named in §8) |
| Data type | Trends series, resold |
| Historical depth | not stated in 01-d |
| Update frequency | not stated in 01-d |
| Granularity | Query, region |
| Geographic coverage | Global |
| API or collection method | Commercial API |
| Licensing and access restrictions | not stated in 01-d; buying a resold series does not answer whether the upstream collection was lawful |
| Estimated collection cost | **Not verified** in 01-d |
| Reliability | not stated in 01-d |
| Known limitations | §8: do not buy — rejected on mechanism as well as on access |
| Availability verdict | **Obtainable today** (paid) — rejected |
| Training vs inference | not stated in 01-d |
| Claim status | cited-not-reverified |
| Evidence class | **D at best, E in practice** (the underlying signal) |

### S27 — Journalism / unstructured press

| Field | Value |
|---|---|
| Provider or source | Various publications (team news, artist news, cancellations) |
| Data type | Unstructured text: injuries, scandals, deaths, cancellations, support-act announcements |
| Historical depth | not stated in 01-d |
| Update frequency | Continuous |
| Granularity | Article |
| Geographic coverage | Global |
| API or collection method | Reading; no structured feed named in 01-d |
| Licensing and access restrictions | Not stated in 01-d; syndication and paywall terms vary per outlet |
| Estimated collection cost | Free to read, not systematisable |
| Reliability | High for the fact, unusable as a series |
| Known limitations | Point shocks with no distribution and no counterfactual. The report keeps them as a **hand-set operator override**, never a feature. Support-act announcements: revisit only if a structured feed appears |
| Availability verdict | **Obtainable today**, but not as data |
| Training vs inference | Inference only, by human judgement; never a feature |
| Claim status | cited-not-reverified |
| Evidence class | **E** |

### S28 — Memo program (per-cluster id)

Added 2026-11-08 by the feature-1 documentation pass. This is not a price source and not a dataset;
it is a **third-party program the product depends on**, registered here because its id is read per
cluster and the value differs, which is the kind of fact this registry exists to keep straight.

| Field | Value |
|---|---|
| Provider or source | Solana hosts the program; the `solana` CLI ships and writes to the one it calls its memo program |
| Data type | Not data. A program id, and the memo instructions that run under it (a quote's commitment text) |
| Historical depth | The program account's own history per cluster; not a series |
| Update frequency | Immutable: a program id does not change. What changes is which cluster hosts which id |
| Granularity | One program per cluster |
| Geographic coverage | Cluster-specific: `devnet`, `mainnet-beta`, `localnet`; `testnet` not measured |
| API or collection method | `getTransaction` on a transaction that carries a memo, then read the memo instruction's `programIdIndex` into `accountKeys`; or `getAccountInfo` on a candidate id |
| Licensing and access restrictions | None: public, executable, no key, no rate-limit beyond the public RPC's own |
| Estimated collection cost | Free, one read-only call |
| Reliability | High for the id (it is on chain); a wrong id is silently accepted by a cluster that hosts it, which is the failure this entry guards against |
| Known limitations | **The ids disagree by cluster.** Devnet hosts both the measured id and the CLI's, so a memo sent to the wrong one lands and is read by nobody. `testnet` has no measured id and the client refuses it rather than borrowing one. `localnet` resolves to the CLI's id, which is class D. |
| Availability verdict | **Obtainable today** on devnet (measured) and mainnet-beta (public RPC; not measured in this pass). No local validator run has been made |
| Training vs inference | Neither: a commitment and an identifier, not a training or inference input |
| Claim status | devnet: measured 2026-11-08T05:39:47Z by one `getTransaction`, quoted with its account keys in `records/findings/40-memo-program-id.md` §2, and not re-read in this pass; mainnet-beta and localnet: cited-not-reverified, no measurement |
| Evidence class | devnet **A** (measured 2026-11-08T05:39:47Z, quoted in `records/findings/40-memo-program-id.md` §2); mainnet-beta and localnet **D** (the CLI's shipped id, no measurement) |

**Correction, 2026-11-08T08:20Z.** Two sentences in the row above are stale against the code. The
`mainnet-beta` row left `chain_client.MEMO_PROGRAMS`, and `localnet` no longer resolves to the CLI's
id: the table is `devnet` and `localnet`, both `Memo4c2pN8afCj432Lb7RMVKi9PbQnn7ewFFaV3oAH`, the id
the installed CLI was measured building. `mainnet-beta` and `testnet` are both refused, and the two
surfaces refuse differently: `memo_program_id(cluster)` raises `UnknownCluster` naming the clusters
the table covers, while the console answers `chain.memoProgram: null` for the server's cluster
instead of failing the page. The ids are class A on devnet and on the installed CLI, and unmeasured
on mainnet-beta, which is why nothing is named for it.

### S29 — Primary legislation on ticket resale (the region-caps table)

Added 2026-11-08 by the region-aware resale caps pass. This is not a price source and not a market
dataset; it is the **legal basis** for a refusal the platform performs, registered here because it is
read, dated, cited and versioned like any other input, and because the table's confidence grades are
the same kind of claim this registry already grades.

| Field | Value |
|---|---|
| Provider or source | Each jurisdiction's own legislation service: `legislation.gov.uk`, `irishstatutebook.ie`, `ontario.ca/laws`, `legisquebec.gouv.qc.ca`, `bclaws.gov.bc.ca`, `austlii.edu.au` + state sites, `leginfo.legislature.ca.gov`, `nysenate.gov`, `leg.state.fl.us`, `malegislature.gov`, `laws-lois.justice.gc.ca`, `ecfr.gov`, `eur-lex.europa.eu` |
| Data type | Statute, regulation and announced government policy text. Not prices, not events, not behaviour |
| Historical depth | Complete for each instrument's life: `in_force_from`/`in_force_to` per row, plus a retrieval timestamp |
| Update frequency | Irregular, by legislation. The table is a snapshot with a version (`2026-11-08.1`) and a SHA-256; a re-read is a new version |
| Granularity | One row per instrument per jurisdiction; a jurisdiction may have several (an in-force disclosure duty and an announced cap) |
| Geographic coverage | **25 codes read or explicitly marked**: IE, CA-ON, CA-QC, CA-BC, AU-NSW, AU-SA, AU-WA, AU-VIC, GB, US (federal x2), US-CA, US-FL, US-MA, US-NY, and rows marking unknowns. 13 EU member states and 22 US states are `unknown` |
| API or collection method | `web-fetch` skill per page; a bounded number of fetches per cluster, every quote read from the page it cites. No scraping, no bulk download |
| Licensing and access restrictions | **Not assessed and not asserted here.** Each service carries its own terms (Crown copyright/OGL for UK legislation, public-domain US federal text, and so on). The table stores a citation and a URL, not a copy of a statute, and the platform's use is to read a limit, not to republish the text |
| Estimated collection cost | Free; the cost is human reading time. One cluster took about 20 minutes and 25-30 fetches |
| Reliability | High where a row is class A (the instrument text was read). Low where it is D or E, which is why those rows may not produce a cap (`tests/test_region_caps_table.py` enforces it) |
| Known limitations | The largest one is coverage: most jurisdictions were not read. Second, the walls are real — Légifrance and Normattiva serve article text by JavaScript, the NSW official site and AustLII returned a Cloudflare challenge, and the Queensland authorised PDF is encrypted. Third, a row goes stale silently: it is true of the date it was retrieved until someone re-reads it. Fourth, a law can be silent on the exact question that matters (New York does not say whether an independent reseller is a licensee) |
| Availability verdict | **Obtainable today** for the rows marked A. **Not obtainable from this host in this pass** for the EU member states and Queensland |
| Training vs inference | Neither. This is a constraint applied at decision time, not a feature and not a training input. It must never enter a model |
| Claim status | Per row: A (instrument read), B (official page states it), D (secondary only), E (unknown). The table's own validator refuses an A row with no quote or URL |
| Evidence class | A for the rows read; the synthesis is `records/findings/33-a-region-cap-law.md` and the five cluster records beside it |

---

### S30: Token-2022 transfer fee (the mechanism, measured)

Added 2026-11-08 by the ten-feature documentation pass. Not a price source: it is the mechanism two
features were built on and the one that blocked them, and it is registered here because the ceiling
fact is now load-bearing for a product decision (D15, Q5).

| Field | Value |
|---|---|
| Provider or source | Token-2022 (`TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`), the runtime itself |
| Data type | Fee arithmetic and withheld balances: `withheldAmount` on a recipient token account's `transferFeeAmount` extension, and the `TransferChecked` result that moved the rest |
| Historical depth | Not a series. A balance at a slot |
| Update frequency | Per transfer |
| Granularity | Per mint (one `TransferFeeConfig` per mint), read per token account |
| Geographic coverage | Every cluster that hosts Token-2022, which is all of them |
| API or collection method | `getAccountInfo` with `encoding: jsonParsed` on the recipient token account, before and after a raw `TransferChecked` (instruction 12) that passes no fee, so the number that comes back is the runtime's own arithmetic |
| Licensing and access restrictions | None: public program, public RPC, no key |
| Estimated collection cost | Free apart from the validator; the measurement used four throw-away local validators, each killed by the tool |
| Reliability | High for the arithmetic measured: it is the runtime's, not a client's. It matches `spl-token-2022` 7.0.0's `calculate_fee`, which divides with a ceiling and then clamps to `maximum_fee` |
| Known limitations | **The ceiling is the finding.** At `decimals 0` and `amount 1`, any rate from 1 to 9999 bps withholds the whole ticket, so the fee can only be 0 or 1 base unit. The `maximum_fee` clamp was never exercised by a real transfer, only in `tests/test_fee_experiment.py`. The version of Token-2022 built into the validator was not read off the cluster |
| Availability verdict | **Obtainable today** on a local validator with no key and no faucet; no devnet or mainnet transaction was sent |
| Training vs inference | Neither. It is a mechanism the product either uses or refuses |
| Claim status | measured-today: four legs, quoted RPC objects, the arithmetic written out (finding 36) |
| Evidence class | **A** for the ceiling arithmetic and the withdraw behaviour; **D** for the validator's embedded program version |

### S31: The band feed (`["band", mint]`) as a data source

Added 2026-11-08 by the ten-feature documentation pass. This is the first on-chain account in this
repository that is meant to be **read by someone else**, so it is registered as a source and not only
as an account.

| Field | Value |
|---|---|
| Provider or source | This repository's own program (`programs/cap_hook/`), one account per mint |
| Data type | A signed band: `low`, `high`, `as_of_slot`, `published_slot`, `sample_n`, `refused`, `model_hash`, `authority` |
| Historical depth | One head per mint. The history is the forecast log, one account per `(mint, as_of_unix)` |
| Update frequency | Rewritable on purpose: every `PublishBand` replaces the head |
| Granularity | Per mint (one ticket type) |
| Geographic coverage | **Local validator only.** No band exists on devnet or mainnet, so there is no third-party consumer and no public reader today |
| API or collection method | `getAccountInfo` on the `["band", mint]` PDA, decoded by `ticketpath/onchain/v2.py` (102 bytes, offsets pinned by `tests/test_onchain_v2.py`) |
| Licensing and access restrictions | None on the account; reading it needs a cluster |
| Estimated collection cost | One RPC read per head, per consumer poll. The local run's band was read back at slot 12 |
| Reliability | The account is authority-signed (`6026`), which is a permission and not a guarantee: the program cannot check that the sample size or the model hash are honest |
| Known limitations | **No third-party program consumes it**, so the composability claim is unproven. `refused` is stored, not enforced: it travels with the number so a consumer inherits the uncertainty, but nothing acts on it. `low > high` is refused `6022` rather than written |
| Availability verdict | **Obtainable today on the local validator**; not published on any public cluster |
| Training vs inference | Inference only, and only with the uncertainty fields carried alongside the number. Never a training input on its own |
| Claim status | measured-today on the local run: `low 900000000`, `high 1100000000`, `as_of_slot 10`, `published_slot 12`, `sample_n 42`, `refused 0`, quoted in the run's artefact |
| Evidence class | **A** for the account's shape and its fields; **E** for any claim that a band describes a real market |

### S32: A live child model as a decision source (deepseek through the `pi` CLI)

Added 2026-11-08 by the ten-feature documentation pass. Registered because it is the only source in
this file that **spends money**, and because its cost was measured rather than estimated.

| Field | Value |
|---|---|
| Provider or source | The model provider, reached by the `pi` CLI as a child process (`market_swarm/forge_policy.py`) |
| Data type | One JSON decision per child: an action, a price in lamports, a ticket id, a rationale. Not a price series and not a dataset |
| Historical depth | Not a series. One row per decision, in the adapter's own JSONL |
| Update frequency | Per decision; each child is one call |
| Granularity | One agent, one round, one event |
| Geographic coverage | Not applicable: a model call has no market coverage |
| API or collection method | Spawned as `pi --mode rpc`, prompt over stdin as one JSON line, answer read off the assistant `message_end` record; `sessionId` captured with a `get_state` probe so the decision can be tied to the provider's own accounting |
| Licensing and access restrictions | Paid, on the operator's own account. The child authenticates from its own auth file under `HOME`; no API key is passed in its environment |
| Estimated collection cost | **Measured, not estimated.** One live decision: 22,838 in, 157 out, 4,096 cache-read, `$0.003532`, 4.2 s. Four children in the feature: `$0.011581380` in total, cross-checked against the CLI's own usage log for those four |
| Reliability | The answer is one JSON object or a refusal. A provider failure arrives as a zero-token `message_end` with `stopReason: error`, which the adapter reports with the child's own sentence rather than as a priced decision |
| Known limitations | **The cap is parent-side.** The argv gives the child no limit of its own, and a SIGKILLed parent can leak a child with no wall clock and no token cap. The usage log writes no row for a `--no-extensions` child, so 38 children spawned by another session rest on their own session files alone. The live path is off unless `MARKET_SWARM_LIVE_LLM=1` |
| Availability verdict | **Obtainable today**, paid, opt-in |
| Training vs inference | Neither. It is a policy that chooses an action, not a feature and not a training input |
| Claim status | measured-today: the four child rows and the total, quoted with the provider's own cost field in `records/findings/41-deepseek-live-adapter.md` |
| Evidence class | **A** for the wire handling and the cost; **D** for the claim that one live child buys a better market than a scripted policy |

---

## Sources barred from ML ingestion (this restriction is binding)

Carried forward verbatim from the finding so no later phase has to rediscover it:

| Source | Restriction as stated | Consequence |
|---|---|---|
| S11 Reddit | No right to use user content for training an ML model without rightsholder permission | Inference only, at best; cannot train the engine |
| S12 Spotify | Content may not be used to train an ML model **or be ingested into one** | Neither training nor inference |
| S13 YouTube | Scraping contradicts the same ToS logic | Not collectable; moot |
| S14 Chartmetric | Commercial licence; downstream of S12 | Unresolved — must be read, not assumed |
| S1 Ticketmaster | No deriving revenues from the API; caching only for "reasonable periods" | Commercial-use restriction, **not an ML ban as stated** — do not conflate the two |
| S4 StubHub, S3 SeatGeek, S5 Viagogo/Vivid/AXS/Network/Gametime, S10 X | Terms not read in 01-d | **Unverified** — treat as unknown, not as permitted |

Rule adopted: **absence of a stated prohibition is not permission.** Any source whose terms are
"not stated in 01-d" may be used for research at prototype scale, and may not be used to train or
to support a commercial claim until someone reads the terms and records it here.

---

## Money gates

Nothing in this table is authorised. **The operator decides spend; no budget is assumed anywhere
in this programme.** Every figure below is as published on the date the report checked it, and is
carried unverified unless marked otherwise.

| Item | Figure the report gives | What it buys | Report's verdict |
|---|---|---|---|
| X API pay-per-usage (S10) | $0.005 per Post read; 3M reads/month cap; ~$150/month at 1,000 posts/day | Social volume | **Do not buy.** No mechanism that survives §4.2 |
| Chartmetric Manager (S14) | $40/month, billed yearly | Historical artist listener/chart series | **Do not buy.** Downstream of a source that bans ML use |
| Open-Meteo commercial licence (S15) | Paid subscription, **price not read** | Lawful commercial weather | **Not yet.** Use NOAA, free and public domain |
| Ticketmaster Inventory Status / Partner (S2) | **Not publicly priced**; request-only | Real prices, fees, availability | **Worth one email.** The only lawful listing-level primary price feed the report could identify |
| tickets.dev capture API (S6) | From $50/month for 1,000 captures (vendor-published) | Listing-level scrapes across marketplaces | **Do not buy yet.** Solve the exposure gap inside our own platform first |
| Paid Google Trends aggregators (S26) | **Not verified** | Trends | **Do not buy.** Rejected on mechanism and on access |

Free sources cost nothing in money and are not gates: S1, S8, S16, S17, S19, S20, S22, S23, S24,
S25, and S21 in money (it costs human hours).

---

## What is missing, and would change the plan

Two absences dominate everything else, and neither is a purchase. Both are in
`00-data-situation.md` §4 and §7 of the finding, and both outrank every external source above.

1. **A listing-level ask and exposure feed — V14, secondary listing depth.** No lawful source for
   it exists in this registry. The marketplace APIs that would carry it are either barred (S11,
   S12), not market-side at all (S4), gated behind an approval nobody has (S3), unpriced and
   request-only (S2), or scraping with unresolved legal exposure (S5, S6). Without it,
   `P(sale | price, exposure, t)` is not identified: the sale count is a numerator with no
   denominator, and "no sale" cannot be separated into "no buyer at this price" from "nothing was
   ever offered". **The cheapest route is our own platform** — four fields per listing event
   (`listPriceLamports, listedAt, delistedAt | soldAt, delistReason`).
2. **Seat coordinates — V15.** The strongest within-event price axis in every published ticket
   study, and absent from the wire contract. The only routes are the company's internal ledger (an
   operator question: does it hold what the contract omits?) and manual transcription of official
   venue charts (S21, hours not money). No API in this registry supplies it.

If either arrives, the engine's cross-sectional story changes materially and Phase 2A should be
re-scoped before Phase 7 starts. If neither arrives, the engine is a tier-level, time-to-event
model with a policy-truncated price ceiling, and every claim it makes must be stated that way.

---

## Limits of this registry

- The registry is only as verified as its sources. Nine claims were re-tested today (table at the
  top); the rest are cited from the finding. **The Ticketmaster price-field removal, the
  rate limits, all published prices, and every licence term I did not re-read are cited, not
  verified.**
- SeatGeek terms, Viagogo/Vivid/AXS/TicketNetwork access, and whether any on-chain ticketing
  programme writes fiat resale prices remain **not established** (§9).
- No field here was filled plausibly. Where the report is silent the cell says so.
- `lib/mock/` was not read for this record and may not be used for anything but schema exercise.
- No prices, rate limits or licence terms were invented, and no spend was assumed.

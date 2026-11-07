# FRONTEND-INTEGRATION — what a judge actually sees, and which numbers are ours

> **Superseded in one respect, 2026-11-07T11:40Z.** The fixture store was regenerated
> (`records/FIXTURE-STORE.md`): it now holds 8 events and 76 tickets, and every wallet
> and mint begins with `SYN` with a distinct four-character tail instead of `FXTURE…1111`.
> The reason is in that file §1: distinct tails remove the self-transfer read, and a
> 32-byte-decodable address gives a judge a clean "account does not exist" instead of a
> malformed-address error. **Everything below about what the UI renders, which numbers it
> comes from, and which of the 37 need a label still holds.** The `FXTURE` prefix, the
> two-event count and the five-ticket count do not; the store's current numbers are the
> ones in `records/FIXTURE-STORE.md`.

**Written:** 2026-11-07T11:20Z.
**Scope:** `../ticketing-frontend`, read only. Nothing in that tree was edited,
built, restarted or written. `:3000` was read with `GET` only. Our own backend was
started on `:8788`, queried, and stopped again.
**Question:** when a judge clicks the app, what appears, which numbers come from our
backend, and what must the backend return for every number on screen to be either true
or obviously labelled?

**Files read, in full:** `lib/api.ts`, `lib/types.ts`, `API_CONTRACT.md`, `lib/format.ts`,
`lib/viz.ts`, `lib/solana.ts`, all six routes under `app/`, `MyTicketsClient.tsx`,
`VerifyClient.tsx`, and all twelve components.
**Ground truth used:** the live `:3000` HTML (currently in mock mode, banner present,
six `lib/mock` events) and live JSON from `:8788` (two fixture events, five tickets,
eleven ledger rows).

**What this document is not.** It is not evidence about any market. `lib/mock` appears
here only as evidence about *what the UI displays*, never about prices. Every number
quoted from the live backend is a synthetic fixture number and is labelled as such in
this file.

---

## 0. The answer in one paragraph

A judge sees a six-page Next.js app that is visually finished and numerically confident.
Every digit on it is rendered from a hand-authored fixture, and the app's only
synthetic-data label is a banner that appears **only while the backend is switched off**.
Wiring the frontend to `:8788` removes that banner, replaces six rich events with two thin
ones, drops the ticket total from 128 to 5, and turns `/my-tickets` into a dead page for
anyone without a browser wallet. The numbers themselves are honest arithmetic over honest
records, and our backend serves all of them correctly. The truth problem is entirely in
what the screen does not say. The only free-text channels the UI prints from our payload
are `Event.name`, `Event.description`, `Organizer.name`, `WalletVerification.flags` and
error `message`. The `FXTURE` address prefix is the one label that survives truncation on
every screen, because `shortAddress` keeps the first four characters (`FXTU…`), but all 13
fixture addresses also share the same last four, so every pill on every screen reads
`FXTU…1111` and distinct wallets are visually indistinguishable.

---

## 1. Page-by-page inventory

Six routes plus two status pages. Four of the six fetch on the server at render time;
two fetch in the browser and only once a wallet is connected; the two status pages never
fetch at all.

| # | Route | Renders | API calls | Fields displayed | Empty backend | Failing backend |
|---|---|---|---|---|---|---|
| 1 | `/` | Event grid, 2 columns | `getEvents()` | `Event.name`, `venue`, `city`, `status`, `startsAt`, `tiers[].faceValueLamports`, `issuedCount`, `totalSupply`, `requiresVerifiedWallet`, `resalePriceCapBps`, `resaleEnabled` | "No events yet / Published events will appear here." | `app/error.tsx`: "Something went wrong", names `NEXT_PUBLIC_API_BASE_URL`, `Try again` button |
| 2 | `/events/[eventId]` | Header, 4 stat tiles, price chart, ticket list, tiers card, transfer-rules card | `getEvent()`, then `getTickets({eventId, limit:25})` + `getEventAnalytics()` in `Promise.all` | 15 numeric places, §2 N4 to N18 | 404 from `getEvent` → `app/not-found.tsx`; if the event exists but has no tickets: "No tickets issued yet", chart "No resale activity recorded yet." | `getEvent` 404 → not-found page. `getEvent` other error → error page. **Analytics or tickets 404/500 → error page, not not-found**, because only `getEvent`'s 404 is caught |
| 3 | `/tickets/[ticketId]` | Header, 4 stat tiles, price chart, custody trail, "On-chain" card | `getTicket()`, then `getResaleHistory()` + `getEvent().catch(()=>null)` | 10 numeric places, §2 N19 to N28 | 404 → not-found page. Existing ticket, empty trail: "No ledger entries.", chart "No resale activity recorded yet.", stats render "—" | `getTicket` 404 → not-found. `getResaleHistory` any error → error page. `getEvent` error is swallowed, the back-link simply disappears |
| 4 | `/organizer?event=<id>` | Event filter chips, 4 stat tiles, chart, markup distribution, destinations table | `getEvents({limit:100})`, then `getEventAnalytics(selected)` | 7 numeric places, §2 N29 to N35 | "No events to analyze" card, no second call | `getEvents` error → error page; analytics error for one event → error page for the whole route |
| 5 | `/my-tickets` | Connect prompt, or address + verification badge, holdings list | none until a wallet exists. Then `getTickets({ownerWallet, limit:100})`, `getEvents({limit:100})`, `getWalletVerification()` in `Promise.all` | holdings count, per-row numbers (shared `TicketRow`), verification badge | No wallet, live mode: "Connect a wallet to see your tickets". Wallet with no holdings: "No tickets in this wallet" | Inline only: `EmptyState` "Could not load tickets" with the raw `err.message`. **A failing verification call also kills the holdings**, because all three are in one `Promise.all` |
| 6 | `/verify` | Connect prompt, or status card + "What gets recorded" card | none until a wallet exists. Then `getWalletVerification()`; on click `POST challenge` → wallet signs → `POST verification` | verified-on datetime, method, can-receive-transfers | No wallet: "Connect the wallet you want to verify." Unverified: amber "Not verified" + `Sign to verify` | Inline text "Could not read verification status." and the raw backend `message` on a failed signature |
| 7 | `/error` | Static | none | none | n/a | n/a |
| 8 | `/not-found` | Static | none | none | n/a | n/a |

Plus `components/AppShell.tsx` on **every** route: nav, the cluster label (`devnet`), the
wallet button, and the mock-mode banner. It renders `isMockMode`, which is a module-level
constant in `lib/api.ts`.

### Presentational surfaces a judge will still click

- The header wallet button (`WalletMultiButton`): real Solana wallet discovery, no backend involved. It works with or without our backend.
- Almost every base58 address pill (all but one, `AddressPill link={false}` on the ticket page's "originally issued to"): a copy button plus a link to `explorer.solana.com`. In live mode the link carries a `FXTURE…` address and 404s.
- Every event card: a link to `/events/<slug>`.
- The four nav items, all of which are live routes.
- The footer claim: "Every transfer is recorded on-chain." This is static text, not a fetched field, and in this build it is false. No payload can change it.

### Two things the pages do that the contract does not describe

- `/events/[eventId]` requests at most **25** tickets and prints `Showing 25 of 150` if there are more. There is no pagination control and `nextCursor` is never read, on any page. Truncation is disclosed in the subtitle and nowhere else.
- `/organizer` silently caps its event list at **100**, also with no pagination.

---

## 2. Every number on screen

"Computed" means the component derives it from other API fields. "Mock" shows whether the
figure is currently produced from `lib/mock` when the app runs as it runs today (it does,
for all of them, because `:3000` has `NEXT_PUBLIC_API_BASE_URL` unset). "Must return"
is what our backend has to send for the figure to be true.

| Field | Page | Source | Formula, if computed | Derived from `lib/mock` today | What the backend must return |
|---|---|---|---|---|---|
| `tiers[].faceValueLamports` "From" | `/` | API | `Math.min(...tiers.faceValueLamports)` | yes | integer lamports per tier; the minimum is the "From" figure |
| `issuedCount` / `totalSupply` "Issued %" | `/` | API | `totalSupply ? issuedCount/totalSupply : 0`, then `(x*100).toFixed(0)` | yes | `totalSupply >= 1`; counts that agree with the ticket rows |
| issued meter width | `/` | computed | `Math.min(100, sold*100)%` | yes | same two integers |
| `startsAt` "Doors" | `/` | API + clock | `Intl.RelativeTimeFormat` against `Date.now()` | yes | a real ISO-8601 `startsAt`; the relative wording is client-side |
| event status badge | `/` | API | lookup in `EVENT_LABEL` | yes | one of the five `EventStatus` values, or the page throws |
| `minFace` "Face value from" | `/events/[id]` | API | `Math.min(...tiers.faceValueLamports)` | yes | as above |
| `issuedCount` "Tickets issued" | `/events/[id]` | API | plus `formatPercent(issuedCount/totalSupply)` **unguarded** | yes | `totalSupply >= 1`, else the tile prints `NaN%` |
| `analytics.resoldShare` "Resold at least once" | `/events/[id]` | API | `formatPercent(share)` = `(share*100).toFixed(0)` | yes | distinct resold tickets ÷ issued ticket rows |
| `analytics.saleCount` "N resales recorded" | `/events/[id]` | API | none | yes | priced sales only |
| `analytics.avgMarkupBps` "Average markup" | `/events/[id]` | API | `formatMarkup(bps)` = `bps/100`, 1 dp under 10%, `+` when positive | yes | mean of per-sale markups, each against its own tier face; `null` when no sales |
| `resalePriceCapBps` "cap +25%" | `/events/[id]`, `/` | API | `bps/100` with a percent sign | yes | the policy integer, or `null` |
| `analytics.priceSeries[].avgPriceLamports` | `/events/[id]`, `/organizer` | API | plotted directly; y-axis from `niceTicks` | yes | mean sale price per UTC day; ascending |
| `analytics.priceSeries[].avgMarkupBps` | chart tooltip and table | API | `formatMarkup` | yes | per-day mean of per-sale markups, **never** derived from `avgPriceLamports` |
| `analytics.priceSeries[].saleCount` | chart tooltip and table | API | none | yes | that day's sale count |
| chart y-domain and gridlines | both charts | computed | `lo = rawMin > rawMax*0.5 ? rawMin - (rawMax-rawMin)*0.4 : 0`, then `niceTicks(lo, rawMax, 4)` | yes | nothing; integer lamports. **See the caveat below** |
| `Ticket.lastSalePriceLamports` (or face) | `/events/[id]`, `/my-tickets` | API | `formatSol(lastSale ?? faceValue)` | yes | last priced sale, else `null` and the row prints the face value labelled "face value" |
| `TicketRow` markup | `/events/[id]`, `/my-tickets` | computed | `Math.round(((lastSale - face)/face) * 10_000)` | yes | `lastSalePriceLamports` and `faceValueLamports`; the client recomputes markup rather than reading ours |
| `Ticket.transferCount` "hops" | `/events/[id]`, `/my-tickets` | API | none | yes | sale + transfer rows, excluding issue and redeem |
| `tiers[].faceValueLamports` + counts | `/events/[id]` tiers card | API | none | yes | per-tier face, `issuedCount`, `totalSupply` |
| `Showing N of M` | `/events/[id]` | API | `tickets.length` and `issuedCount` | yes | `issuedCount` consistent with the ticket rows |
| `ResaleHistory.faceValueLamports` | `/tickets/[id]` | API | none | yes | the ticket's own tier face |
| `stats.lastPriceLamports` | `/tickets/[id]` | API | `formatSol`, plus the last sale's `markupBps` for the delta | yes | last priced sale in time order |
| `stats.peakPriceLamports` + peak markup | `/tickets/[id]` | API + computed | `Math.round(((peak - face)/face) * 10_000)` | yes | max sale price and the ticket's face |
| `stats.uniqueWallets`, `transferCount`, `saleCount` | `/tickets/[id]` | API | none | yes | distinct wallets over the whole trail |
| `entries[].priceLamports` / `markupBps` | `/tickets/[id]` custody trail | API | none, printed straight through | yes | sale price and per-entry markup; `null` on unpriced moves |
| `Ticket.mintAddress` | `/tickets/[id]` "On-chain" | API | none, also an explorer link | yes | a **real** mint, or a self-labelling placeholder |
| `stats.totalVolumeLamports` | `/tickets/[id]` | API | sum of sale prices | yes | sum of priced sales |
| `analytics.totalVolumeLamports` | `/organizer` | API | sum of sale prices | yes | same |
| `analytics.medianResalePriceLamports` | `/organizer` | API | none | yes | median of sale prices, even count averaged |
| `analytics.uniqueHolders` | `/organizer` | API | `formatCompact` | yes | distinct current `ownerWallet` |
| `analytics.markupDistribution[].count` | `/organizer` | API | bar width `count/max*100`, hover share `count/total` | yes | all six buckets, contract bounds, zero counts included |
| `topDestinations[].ticketCount` | `/organizer` | API | none | yes | tickets held per current owner |
| secondary-holder subtitle | `/organizer` | computed | `topDestinations.filter(d => d.acquiredOnSecondary).length` | yes | the flags themselves |
| holdings count | `/my-tickets` | API | `tickets.length` | yes | tickets filtered on **current** owner |
| `WalletVerification` badge | `/my-tickets`, `/verify` | API | lookup | yes | `verified` true only after a real signature |
| `verifiedAt`, `method`, `canReceiveTransfer` | `/verify` | API | `formatDateTime` on `verifiedAt` | only in mock mode's fake success path | a real ISO timestamp from a real verification; `null` and `false` otherwise |
| cluster label `devnet` | header, every page | env | `NEXT_PUBLIC_SOLANA_CLUSTER ?? "devnet"` | no | nothing, it is a frontend env var |

### Which computed formulas survive the honesty rules

- **`minFace` (min of tier faces): survives.** It is a real tier face and the chart labels it "Face value" on a single-tier event and "Lowest tier face" on a multi-tier one (`app/events/[eventId]/page.tsx:109`, `app/organizer/page.tsx:119`). The frontend already does the honest thing the contract asks for.
- **`TicketRow` markup and the ticket page's `peakMarkup`: survive.** Both measure one ticket against one tier's face. This is exactly the calculation the contract forbids at event level, and it is correct at ticket level because a ticket has exactly one face value.
- **The derived peak markup would silently vanish if `faceValueLamports` were `0`**, because the guard is `&& history.faceValueLamports`. A zero face value is a bad fixture, not a legal price.
- **Chart vertical scale: numbers honest, shape not.** `PriceHistoryChart` starts the y-axis at zero only when the range is near it. A range from 0.9 to 1.15 SOL is drawn from a floor of about 0.8, so a 28% move fills the panel. Nothing on screen says the axis is truncated. That is not a false number, it is an over-stated visual claim, and it is worth one line in the pitch if a judge reads the chart as showing a collapse.
- **`formatSol` rounds.** Three decimals under 1 SOL, two under 100, one above. A judge adding two displayed prices will not always get the displayed total. The API sends integers, so the arithmetic is right and only the presentation is lossy.
- **`formatPercent` uses zero decimals** by default. `4/150` renders as `3%`. Fine, but it means small percentages round to `0%`.

### Where the frontend computes something that contradicts itself

`/tickets/[id]` plots `entries` and `stats` from the same payload, so chart and tiles
agree. `/events/[id]` does **not**: `minFace` comes from `Event.tiers` while the chart's
face annotation is the `minFace` the page passes in, and the analytics carries its own
`faceValueLamports`. Both are the minimum tier face today, so they agree. They will only
disagree if one endpoint and the other are served from different stores.

---

## 3. The judge-click path

Three paths, in order of reliability. The first needs nothing but a browser.

### (a) Working thing, no wallet, no extensions: 3 clicks

1. Open `http://localhost:3000/`. The header shows `devnet` and a wallet button. Six event cards are visible **in mock mode today**; with the backend wired, two.
2. Click **Synthetic Hall Session** (`/events/fixture-hall-session`). It is the *second* card in live mode, because events sort by `startsAt` ascending and the completed "Synthetic Annex Showcase" (2026-10-01) sorts first. **Do not let the judge click the first card.**
3. Read the four stat tiles. They must show, exactly:

| Tile | Figure that must be on screen | Where it comes from |
|---|---|---|
| Face value from | `1 SOL` | min tier face |
| Tickets issued | `4`, hint `of 150 · 3%` | `issuedCount`, `totalSupply` |
| Resold at least once | `75%`, hint `4 resales recorded` | `analytics.resoldShare`, `saleCount` |
| Average markup | `+5.6%`, hint `cap +25%` | `analytics.avgMarkupBps` = 563 bps |

The chart below them has three points, ending on `0.9` for 2026-11-04, with a horizontal
"Lowest tier face" rule. That single screen is the demo: a price record, computed from a
custody log, not typed in.

### (b) Something Solana-specific: 2 more clicks from there

4. Click the first ticket row, **`FX-0001`** (`/tickets/tkt_fixture_0001`).
5. Read the "Custody trail" card. It must show four entries in this order:

```
Issued                                  FXTU…1111                          2026-11-01
Resold        1.25 SOL  +25% vs face    FXTU…1111 -> FXTU…1111             2026-11-02
Transferred                             FXTU…1111 -> FXTU…1111             2026-11-03
Resold        0.9 SOL   -10% vs face    FXTU…1111 -> FXTU…1111             2026-11-04
```

The figure that must be on screen for this to count as Solana-specific: **`+25% vs face`
beside a priced custody hop**, with base58 wallet pills on both sides of the arrow. That
is the wallet-bound-token claim made visible: one ticket, one mint, a price attached to
each custody change.

**But look at the pills.** All 13 distinct addresses in `fixtures/synthetic_store.json`
are 43 characters ending in a run of `1`s, so `shortAddress` renders every one of them as
the identical string `FXTU…1111`. On screen the trail reads as one wallet handing the
ticket to itself four times, and the `Where tickets ended up` table is a column of the
same pill repeated. That is the visual tell that makes a correct computation look
fabricated. It is a fixture defect, it is ours to fix, and it is cheap: give each address
a distinct 4-character tail (the prefix `FXTURE` must stay).

The "On-chain" card adds `Mint address FXTUREmint111…`, `Transfer restriction: Not
enforced`, `Total resale volume 2.15 SOL`.

**This is structural Solana specificity, not verifiable Solana specificity.** The mint
does not exist on any cluster. The explorer link behind every linking pill will 404, and
`signature` is `null` on all eleven ledger rows, so the `tx` link never renders at all.
No component change can fix that; only a deployed program can.

### (c) The only genuinely real Solana fact available tonight: 4 clicks plus a wallet extension

1. Header → **Select Wallet** → connect Phantom or Solflare **on devnet**.
2. Nav → **Verify wallet**.
3. Click **Sign to verify**, approve the signature in the extension.
4. The card must then show the green **`Verified`** badge, `Verified on <a timestamp within the last minute>`, `Method: Wallet signature`, `Can receive transfers: Yes`.

That `Verified on` timestamp is the output of our backend's pure-Python Ed25519
verification of a signature produced by a real wallet over the frozen message. It is the
only figure on the whole app that is the result of real cryptography rather than a
fixture. It is worth the four clicks.

### If a component change were allowed

The smallest change that would turn (b) from asserted to provable is in
`components/AppShell.tsx`: a second strip under the header, rendered whenever the payload
carries `dataSource.synthetic`, saying `Synthetic fixture data, no program deployed on devnet`.
`lib/api.ts` already receives that key on every response and simply drops it. That is a
~15 line change across two files and **we may not make it tonight.**

The alternative that needs no frontend change, and is already in place: the label rides on
strings the UI prints verbatim.

- `Event.name` is `Synthetic Hall Session` and `Synthetic Annex Showcase`. It appears in the page `h1`, the event card, the organizer filter chip, and the ticket page's back link.
- `Event.description` says `Fixture event ... Not a real show.` It appears under the event header.
- `Organizer.name` is `Fixture Promotions (synthetic)` and appears in the byline.
- Every wallet and mint starts with `FXTURE`, so every truncated pill reads `FXTU…`.

So path (a) carries its own label on screen, in the page title, without touching a
component. Path (b) carries a weaker version of it: the ticket page prints
`← Synthetic Hall Session` as its back-link, and its `h1` is `Ticket FX-0001`. The label
is a link in the top-left rather than a statement about the numbers, and a judge reading
the custody trail may never look at it. **If the demo walks to a ticket page, say the
words out loud.**

---

## 4. The labelling problem

Our data is synthetic and our estimates are unvalidated. The app can carry a label in
exactly five payload strings (`name`, `description`, `organizer.name`, `flags`, and error
`message`) plus one convention (`FXTURE`). It renders **no** other honesty field. The
`dataSource`, `custodyNote` and `analyticsNote` keys on every response are received and
discarded. `nextCursor`, `imageUrl`, `endsAt` and `organizer.verified` are never displayed
either.

37 places display a number a judge could take as real. Nine more display a non-numeric
claim with the same problem.

### Numeric places

Format: place, honest label, and where it can actually be carried.
**P** = API payload (works tonight), **F** = frontend change (not tonight), **N** = nowhere (do not serve it).

| # | Place | Honest label | Carrier |
|---|---|---|---|
| N1 | `From` price, `/` | "Synthetic fixture price" | **P** via `Event.name`/`description` on the same card; **F** for a per-figure label |
| N2 | `Issued %` and meter, `/` | "of a synthetic supply" | **P** via `description` |
| N3 | `Doors` relative date, `/` | real date, no label needed | nothing required |
| N4 | `Face value from`, `/events/[id]` | "synthetic face value" | **P** via `h1`/`description` |
| N5 | `Tickets issued 4 of 150 · 3%` | same | **P** via `description` |
| N6 | `Resold at least once 75%` | "on a 4-ticket fixture" | **P** if `description` states the store size; otherwise **N**, because 75% of four tickets is a number a judge will read as a market rate |
| N7 | `4 resales recorded` | "four, by construction" | **P** via `description` |
| N8 | `Average markup +5.6%` | "synthetic, not a market markup" | **N** as a market claim; **P** only via `description`. This is the figure most likely to be quoted back at us |
| N9 | `cap +25%` | "policy, not enforced" | **P** as an integer; the enforcement claim is **F** (see N38) |
| N10 | Daily average resale price, chart | "synthetic daily averages" | **P** via `description`; **F** for a chart footnote |
| N11 | Daily `vs face` markup, tooltip/table | same | as N10 |
| N12 | Daily sale counts | same | as N10 |
| N13 | chart face-value rule | already labelled "Face value" / "Lowest tier face" | nothing required, this one is done well |
| N14 | ticket row price | "synthetic" | **P** via the event name in the row title |
| N15 | ticket row `vs face` | same | as N14 |
| N16 | ticket row hops | same | as N14 |
| N17 | tier face + issued/supply | same | **P** via `description` |
| N18 | `Showing N of M` | truthful, but M is synthetic | **P** |
| N19 | `Face value`, `/tickets/[id]` | "synthetic" | **P** only through the back-link `← Synthetic Hall Session` (rendered when `getEvent` succeeds) and the `FXTU…` pills. **F** for anything that labels the figures themselves. Weakest page in the app |
| N20 | `Last sale price` + `vs face` | same | as N19 |
| N21 | `Peak price` + `over face` | same | as N19 |
| N22 | `Wallets held by`, transfers, priced | same | as N19 |
| N23 | per-sale chart points | same | as N19 |
| N24 | custody trail prices and markups | same | as N19 |
| N25 | `Mint address` | "placeholder, no account exists" | **P** by the `FXTURE` prefix, which is the convention that makes this honest; a real mint would remove the problem entirely |
| N26 | `Transfer restriction: Not enforced` | true and correctly labelled | nothing required |
| N27 | `Total resale volume 2.15 SOL` | "synthetic" | as N19 |
| N28 | `Redeemed` timestamp / `Not yet scanned` | true for a synthetic ticket | **P** |
| N29 | organizer `Total resale volume` | "synthetic" | **P** via the filter chips naming the synthetic event |
| N30 | organizer `Average markup` + cap delta | same | as N29 |
| N31 | organizer `Median resale price`, `face from` | same | as N29 |
| N32 | organizer `Tickets resold %`, distinct holders | same | as N29 |
| N33 | markup bucket counts and total | same | as N29 |
| N34 | destination ticket counts | same | as N29 |
| N35 | `X of Y shown acquired on secondary` | same | as N29 |
| N36 | `Verified on` datetime | genuinely real once signed | nothing required |
| N37 | `devnet` cluster label | true, and it is the one honest chain claim on screen | nothing required |

That is 37 numeric places, and the split is the useful part:

| Where the label can come from | Count | Notes |
|---|---|---|
| API payload, on the same screen | 32 | every page except `/verify`. `Event.name` prints in the `h1` of the event page, in every event card, in every organizer filter chip, in every ticket row and in the ticket page's back-link; `Event.description` prints under the event header; `Organizer.name` prints in the byline; `FXTURE` prints in every address pill |
| Nothing needed | 5 | N3, N13, N26, N36, N37. A real date, a face-value rule the frontend already labels honestly, a correctly-phrased `false`, a real verified timestamp, and a real cluster name |
| Frontend change as the **only** option | 0 | the payload always has a string on the same screen |
| Frontend change to put a label **beside a figure** | would apply to all 32 | weakest on N19 to N24 and N27, where the page-level label is a back-link in the top-left and nothing else |

So 32 of the 37 need a label, and all 32 can get one tonight without touching a
component, because a screen-wide label already exists in the payload strings. What does
not exist anywhere is a label **next to a figure**. On `/tickets/[id]` the only label is a
back-link, which is the weakest it gets and the page most likely to be screenshotted.

### Non-numeric claims, same problem

| # | Claim | Problem | Carrier |
|---|---|---|---|
| N38 | "Resale price is capped at +25% over face value, **enforced at transfer time**" (`/events/[id]`, transfer rules) | There is no program. Nothing is enforced. This is the single most misleading sentence in the app, and it is generated from a value our backend must serve | **F**. Payload alternatives are both wrong: serving `2500` produces the false sentence, serving `null` produces "Resale price is uncapped", which is false about policy. Operator decision, see §7 |
| N39 | "Destination wallet must be verified before a transfer will succeed" | Same: a policy statement in the future tense of an enforcement that does not exist | **F**, same choice as N38 |
| N40 | "Transfer restriction: **Not enforced**" (`/tickets/[id]`) | True, and it directly contradicts N39 two clicks away. A judge who clicks event → ticket reads the app arguing with itself | **P**, by keeping both values honest, which is what they are. **F** to add "policy" / "actual" wording |
| N41 | Footer: "Every transfer is recorded on-chain." | Static text, false in this build, unfixable from the payload | **F** |
| N42 | event status badge `On sale` / `Completed` | true of the fixture, not of a real sale | **P** via the event name |
| N43 | ticket status badge `Valid` | true of the fixture | **P** via `FXTU…` |
| N44 | `Region: Not shared` column | honest: we return `null` because no wallet volunteered one | nothing required |
| N45 | `Resale` / `Primary` badges | true of the synthetic ledger | **P** |
| N46 | verification badge `Verified` | real once signed | nothing required |

### The payload keys that do not work

`dataSource.synthetic` is on every response and reaches the client. It is invisible.
Anyone reasoning "we label every payload, so we are labelled" is wrong: on screen, the
label does not exist. The same is true of `custodyNote` and `analyticsNote`, which are
well written and never read.

The mock-mode banner proves the point by disappearing: `components/AppShell.tsx:61`
renders "Mock data, set NEXT_PUBLIC_API_BASE_URL" only while `isMockMode` is true. Point
the app at `:8788` and the app becomes **less** labelled, not more.

---

## 5. What the frontend needs from us that no finding has specified

`records/CONTRACT-MAP.md` covers the nine endpoints, the field-level answers, the error
bodies, CORS, the 8788 port, `dataSource`, and the frozen verification message. These are
the things it does not cover, all of them discovered by reading the client.

1. **The env var is inlined at compile time.** `lib/api.ts:36` reads `process.env.NEXT_PUBLIC_API_BASE_URL` at module scope, and `isMockMode` is a module constant consumed by client components. `NEXT_PUBLIC_*` is baked in when Next compiles. Setting it in a shell and reloading the browser does nothing; **`:3000` must be restarted** for the switch to take effect. If someone sets it and only reloads, the app keeps serving `lib/mock` and the banner keeps saying "Mock data", which reads as "not wired" when actually it is "not restarted".
2. **The value must be a bare origin.** The client does `BASE_URL.replace(/\/$/, "")` once, then `${BASE_URL}${path}` with `path` starting `/`. `http://localhost:8788` works; `http://localhost:8788/api` produces `/api/api/events`.
3. **`TICKETPATH_HOST` decides whether the browser-side pages work.** Server components fetch from Node, so they reach `127.0.0.1:8788` regardless. `/my-tickets` and `/verify` fetch **from the browser**. A judge looking at the machine gets both. A judge on another host gets rendered events and a broken My-tickets, because their browser cannot reach `127.0.0.1`. If the demo is remote, bind `TICKETPATH_HOST=0.0.0.0` (CORS is already `*`).
4. **`totalSupply >= 1` and `tiers.length >= 1` must be invariants.** `app/events/[eventId]/page.tsx:69` computes `issuedCount/totalSupply` with no guard, so a zero supply prints `NaN%`; `Math.min(...[])` is `Infinity`, so an event with no tiers prints `∞ SOL` and passes `Infinity` to the chart. `EventCard` guards `totalSupply`; the event page does not.
5. **Enum values must be exact.** `EventStatusBadge` and `TicketStatusBadge` do `EVENT_LABEL[status]` and destructure the result. An unknown status string is a runtime throw and the error page. Our backend validates inbound query enums but nothing constrains what the store emits.
6. **`/api/wallets/:w/verification` must never fail for a well-formed pubkey.** `MyTicketsClient` puts tickets, events and verification in one `Promise.all`. If verification 400s or 500s, the holdings vanish and the page says "Could not load tickets" even though the ticket call succeeded. 200 with `verified:false` is required, for any wallet, always.
7. **Analytics must be 200-with-empty, never 404, for an event that exists.** The event page's `Promise.all` rejects the whole route on an analytics 404, and only `getEvent`'s 404 is translated to the not-found page. A judge would see the generic error page instead of the designed empty chart.
8. **A way for a connected wallet to hold a fixture ticket.** `MOCK_DEMO_WALLET` is used **only** when `isMockMode` (`MyTicketsClient.tsx:22`). In live mode a connected wallet gets an empty holdings list and an amber "Not verified" badge until it signs. Nothing in the store owns the operator's or judge's pubkey. Proposed: `TICKETPATH_DEMO_WALLET` seeds one ticket's `ownerWallet`, or the operator supplies a devnet pubkey to author into the fixture. Either way this must be decided before the demo.
9. **Error `message` is user-facing prose.** `EmptyState` and the verify page print it verbatim. `{"message": "event nope not found"}` becomes a sentence a judge reads. Messages need to be sentence-case English; the machine-readable code already exists separately in `code` and is never displayed.
10. **The synthetic marker must stay inside the strings that are printed.** Concretely: `Event.name` must contain "Synthetic", `Event.description` must say it is not real, `Organizer.name` must contain "synthetic", and every synthetic wallet and mint must start with `FXTURE`. Those four are load-bearing honesty surfaces, not decoration. If a future fixture renames an event to "Harbor Lights Festival", the app loses its only label on that page.
11. **Ticket counts must stay under the invisible caps.** 25 per event on the event page, 100 events on the organizer page. `nextCursor` is never consumed on any page, so over either number the UI silently truncates.
12. **Synthetic addresses must be distinguishable after truncation.** `shortAddress` keeps the first four and last four characters, and every one of the 13 fixture addresses currently renders as `FXTU…1111`. Two distinct wallets must never share a truncated form, on pain of the custody trail looking like a no-op. Keep the `FXTURE` prefix and vary the tail.
13. **Nothing may be served that the UI would print as a forecast.** There is no type, no endpoint, and no field for `expectedResaleLamports`, `saleProbability`, or `recommendedPrimaryLamports`. Adding one to a payload would be invisible. The engine's output has no home on screen, and tonight that is the correct state.

Non-requirement, recorded so nobody spends time on it: `imageUrl` is never rendered by
`EventCard` or any page, so `null` costs nothing. `endsAt` and `organizer.verified` are
likewise never displayed.

---

## 6. The three demo risks

**Risk 1. The wire does not take, or takes** (most likely thing to look broken).
The env var only applies after `:3000` restarts. If it is set and not restarted, the judge
sees six `lib/mock` events under a banner reading "Mock data", and the pitch ("this is our
backend") is contradicted by the screen. If it is restarted, the dataset drops from six
events and 128 tickets to two events and five tickets, so the tiles that read `75%` and
`+5.6%` are computed over four tickets instead of a hundred and twenty eight.
**Least-time fix:** set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8788`, restart `:3000`,
load `/`, and confirm the banner is **gone** and exactly two cards are shown. That is a
30-second check and it proves both things at once. Rehearse it once before the demo, and
keep a note of the two event slugs.

**Risk 2. The data reads as fake at the pixel level, and the label disappears exactly when
it starts working.**
Two separate tells. First, all 13 fixture addresses truncate to `FXTU…1111`, so the
custody trail shows the same wallet passing a ticket to itself and the destinations table
is one pill repeated 13 times. Second, `dataSource.synthetic` is invisible and the only
banner is keyed to mock mode, so wiring the backend removes the label; the first click
that exposes it is a mint address landing on a Solana Explorer 404.
**Least-time fix:** two changes, both cheap and both ours. Give the fixture addresses
distinct 4-character tails (a ten-minute edit to `fixtures/synthetic_store.json`, prefix
`FXTURE` preserved, tests re-run). Then walk the path in §3(a), which puts "Synthetic Hall
Session" and "Not a real show" on screen in the page title and description, and say out
loud that the mint is a placeholder before anyone clicks it. If one frontend change is
ever allowed, the `AppShell` strip in §3 is it.

**Risk 3. `/my-tickets` and `/verify` read as broken without a browser wallet.**
Live mode has no demo wallet fallback, so My tickets is a connect prompt, and after
connecting it is an empty list plus an amber "Not verified" badge. Two of the four nav items
lead somewhere that looks unfinished. If the judge has no extension installed, the one
genuinely real Solana moment in the app (§3c) is unreachable.
**Least-time fix:** take the operator's or demo laptop's devnet pubkey, author one ticket
for it in `fixtures/synthetic_store.json`, restart the backend, and connect that wallet
before the judge sits down. Then My tickets shows a real holding and the verify flow
becomes a two-click demonstration instead of a dead end.

---

## 7. Decisions this analysis hands up

1. **`resalePriceCapBps` and `requiresVerifiedWallet` on the demo events.** Both values are true as *policy* and neither is enforced, and the frontend renders them as enforcement ("capped at +25% over face value, enforced at transfer time"). Two honest options, both with a cost:
   - keep `2500` and `true`, so the product story is complete, and accept one false sentence on screen that must be corrected in a frontend edit before submission;
   - set them `null` / `false` on the demo events and carry the policy in `description`, so the screen is true today and the app demonstrates an uncapped, ungated product.

   My recommendation: keep the policy values, flag the sentence as a required frontend edit, and say it out loud in the demo. The false sentence is in one `<li>` and can be fixed in five minutes by anyone allowed to touch that tree. Gutting the policy makes the anti-fraud story harder to tell than the sentence makes it to defend.
2. **Whether the demo runs on `lib/mock` or on our backend.** They are different products on the day: six events and 128 tickets with a visible mock banner, versus two events and five tickets with no banner but an honest label inside the event name. The second is truthful and thin. The first is rich and openly labelled as mock. Both are defensible; only the second is *ours*.
3. **Whether a wallet is on the path.** With one, path §3(c) shows real Ed25519 verification and My tickets means something. Without one, the demo stops at structural Solana specificity and two nav items are dead ends.

---

## Snapshot note — 2026-11-07T12:14Z

**This file is a snapshot of 11:31Z, not a description of the current tree.** It is kept as
written; the note at the top of the file already marks one paragraph as superseded, and this one
records the numbers that have moved since, so a reader of either does not take the counts as
current.

| What the document says | What is true now | Shown by |
|---|---|---|
| "two fixture events, five tickets" (§ line 25) and "two events and five tickets" (§ line 416, and the recommendation at the end of the file) | **8 events and 76 tickets** from the regenerated store, 147 ledger rows, 61 of them priced sales. The two-event store is gone; every count that follows from it inherits the error | `curl -s 'http://127.0.0.1:8788/api/events?limit=100'` → 8; `.../api/tickets?limit=200` → 76; `python3 tools/build_fixture_store.py --check` |
| wallets and mints named `FXTURE…1111` | every address is `SYN…` with a distinct four-character tail; 204 distinct addresses, all 32 bytes | same `--check` output, "addresses: 204 distinct, all SYN*" |

What has not changed, and is the substance of the file: which screens render which numbers, the
37 contract fields and which of them need a label, the mock-versus-backend comparison, and the
frontend's absence of any pricing surface. Those hold against the current store.

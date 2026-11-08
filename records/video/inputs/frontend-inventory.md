# Frontend inventory — what a judge actually sees

Read-only inventory of the Next.js app at `~/ticketing-frontend`, taken for the 2:00
SeatPass demo video. Nothing here was built, run or clicked: every claim is either
**MEASURED** (read in a named file, quoted with `file:line`) or **INFERRED** (a
consequence of what was read, stated as such).

State of the checkout at read time: one commit, `0208765 baseline: untouched tree
before the SeatPass rebuild`, with the whole rebuild sitting uncommitted on top
(`git -C ~/ticketing-frontend log --oneline -5`, `git status --porcelain`). §8 lists
what that means for shooting.

Two structural facts drive everything below and should be read before planning a shot:

1. **The app is fixture-only right now.** `NEXT_PUBLIC_API_BASE_URL` is empty in
   `.env.example:4`, which makes `isMockMode` true (`lib/api.ts:44-46`). Every screen
   renders rows from `lib/mock/*.json` (`lib/api.ts:14-17`). Nothing on any screen is
   fetched from a server.
2. **The chart's required props are never passed.** `PriceHistoryChart` takes
   `{ points: {label, priceLamports}[], faceValueLamports, capCeilingLamports,
   lastSaleLamports }` (`components/PriceHistoryChart.tsx:67-73`), and all three call
   sites pass `{date}` points, no `capCeilingLamports`, no `lastSaleLamports`
   (`app/events/[eventId]/page.tsx:101-110`, `app/tickets/[ticketId]/page.tsx:120-124`,
   `app/organizer/page.tsx:111-121`). Consequences: no x-axis date labels, no dashed
   cap rule, no `Cap … SOL` chip, and the tree does not typecheck (excess/missing props
   under `strict: true`, `tsconfig.json:7`). **MEASURED** as code; **INFERRED** as
   render effect and as build failure. See §7 and §8.

---

## 1. Routes

Six real pages, two global fallbacks, six chrome links that go nowhere.

### `/` — events list
`app/page.tsx` (server component).

- Heading: `Events` (`app/page.tsx:13`).
- Lede: `Tickets are minted as wallet-bound tokens. Every transfer and resale price is
  recorded against the ticket for the life of the event.` (`app/page.tsx:14-17`).
- Visual order: `SiteHeader` (sticky) → `h1` + lede → 2-column grid of `EventCard`
  (`app/page.tsx:25-29`), one card per event.
- Each `EventCard` shows: event name in `h-event`, a `Chip` status (`On sale` /
  `Sold out` / `Completed`), `{venue} · {city}`, a rule, then a three-up definition list
  `Date` / `Issued` / `Resale cap` (`components/EventCard.tsx:62-90`). Cap reads `Cap
  75%`, `Cap by law 75%`, or `Uncapped` (`components/EventCard.tsx:38-45`).
- Primary control: the whole card is the link to `/events/{slug}`
  (`components/EventCard.tsx:58-60`). Nothing inside it is focusable.
- Empty fallback: `No events yet` / `Published events will appear here.`
  (`app/page.tsx:22`). Six fixtures mean it never renders (`lib/mock/events.json`).

### `/events/[eventId]` — event detail
`app/events/[eventId]/page.tsx` (server). Resolves by id **or** slug
(`lib/api.ts:288`), so `/events/midnight-static-tour` works.

Visual order:
1. Back link `← All events` → `/` (lines 42-47).
2. `h1` = event name; subline `{venue} · {city} · {date, time}`; `EventStatusBadge` on
   the right (lines 50-56).
3. Description paragraph (line 57), then `Organized by {organizer.name}` + `AddressPill`
   (lines 58-61).
4. `StatRow` of four `StatTile`: `Face value from` / `Tickets issued` / `Resold at least
   once` / `Average markup` (lines 64-85).
5. Card `Resale price over time`, subtitle `Average price paid per day across every
   resale of this event's tickets.`, action link `Full analytics` → `/organizer?event=…`
   (lines 87-99), then `PriceHistoryChart` (lines 101-110).
6. Two-column: Card `Issued tickets` with `TicketRow` per ticket (lines 115-129), and a
   right rail with Card `Tiers` (price + `issued / supply` per tier, lines 132-150) and
   Card `Transfer rules` (three sentences, lines 152-171).
- Primary control: any `TicketRow` → `/tickets/{id}` (`components/TicketRow.tsx:17-19`).

### `/tickets/[ticketId]` — ticket detail (the money screen)
`app/tickets/[ticketId]/page.tsx` (server). Accepts a ticket id; the API also accepts a
mint address (`lib/api.ts:313`).

Visual order:
1. Back link `← {event.name}` → `/events/{slug}` (lines 55-62).
2. `h1` = `Ticket {serial}`; `Held by <AddressPill>`; when the current holder differs
   from the issuee, `(originally issued to <AddressPill link={false}>)` (lines 65-73);
   `TicketStatusBadge` right (line 75).
3. `StatRow`: `Face value` / `Last sale price` / `Peak price` / `Wallets held by`
   (lines 79-107).
4. Two-column: Card `Price history` + `PriceHistoryChart` (lines 110-126), Card `Custody
   trail` + `TransferTrail` (lines 128-136).
5. Card `On-chain`: four rows — `Mint address` (explorer link), `Transfer restriction`
   (`Enforced on-chain` / `Not enforced`), `Total resale volume`, `Redeemed`
   (`Not yet scanned`) — lines 139-172.
- Primary control: the mint address link to Solana Explorer (lines 145-153). On the
  trail, `tx` links (`components/TransferTrail.tsx:88-97`).

### `/my-tickets` — holdings
`app/my-tickets/page.tsx` wraps the client component `MyTicketsClient.tsx` (`use client`).

- Unconnected state (only when `isMockMode` is false): `My tickets` +
  `Connect a wallet to see your tickets` (`MyTicketsClient.tsx:58-68`).
- In fixture mode there is **always** a wallet: `publicKey?.toBase58() ?? (isMockMode ?
  MOCK_DEMO_WALLET : null)` (`MyTicketsClient.tsx:22`), so the page opens straight into a
  demo wallet's holdings.
- Connected view: `h1` `My tickets`, `AddressPill`, then a `Verified wallet` or
  `Not verified` `Badge` (`MyTicketsClient.tsx:77-88`).
- Banners: `Showing a sample wallet from the mock fixtures. Connect a wallet to see real
  holdings.` when unconnected (lines 90-94); the not-verified banner with `Verify it now`
  → `/verify` (lines 96-105).
- Card `Holdings`, subtitle `{n} tickets`, then `TicketRow` per ticket (lines 107-133).
- Loading state is three pulsing bars (lines 118-122). Empty: `No tickets in this
  wallet` / `Tickets you buy or receive will show up here.` (lines 124-127).
- Primary control: `TicketRow` → ticket page.

### `/organizer` — resale analytics
`app/organizer/page.tsx` (server). Reads `?event=` (line 18).

- `h1` `Resale analytics`; lede `What tickets are reselling for and where they are
  ending up, computed from the on-chain transfer record.` (lines 43-47).
- Filter row: label `Event` then one chip per event, name truncated past 28 chars with
  `…` (lines 51-70). Active chip per `?event=`.
- Default selection: first `on_sale` event in `startsAt` order (lines 32-35) — by fixture
  dates that is **Winter Chamber Series: Night III**, not Midnight Static. **INFERRED**
  from the sort at `lib/api.ts:281` and the fixture dates.
- `StatRow`: `Total resale volume` / `Average markup` / `Median resale price` / `Tickets
  resold` (lines 72-103).
- Card `Resale price over time`, subtitle `Average price paid per day for {event}.`
  (lines 105-123) + `PriceHistoryChart`.
- Two-column: Card `Markup distribution`, subtitle `How far over face value tickets
  actually changed hands.` + `MarkupDistribution` (lines 126-134); Card `Where tickets
  ended up`, subtitle `Top holding wallets. {n} of {m} shown acquired on the secondary
  market.` + a table with columns `Wallet` / `Region` / `Tickets` / `Source`, source
  rendered as `Resale` or `Primary` badges (lines 136-175).
- Primary control: the event chips.

### `/verify` — wallet verification
`app/verify/page.tsx` wraps `VerifyClient.tsx` (`use client`).

- `h1` `Verify wallet`; lede about restricted transfers and signatures (lines 85-91).
- Card `Status`: unconnected shows `Connect the wallet you want to verify.` + the wallet
  button (lines 96-100); connected shows `AddressPill`, a `Verified` / `Not verified`
  badge, then either three `verified on / method / can receive transfers` rows
  (lines 112-128) or the flags list plus the `Sign to verify` button (lines 129-152).
- Success line and error line (lines 155-172).
- Card `What gets recorded`, three bullets (lines 178-188).
- Primary control: `Sign to verify`, disabled only while `signing` / `submitting`
  (line 142). Real signature request through the wallet adapter (lines 60-72).

### Global fallbacks
- `app/not-found.tsx`: `Not found` / `That event or ticket does not exist, or it was
  never issued on this cluster.` / button `Back to events`.
- `app/error.tsx`: `Something went wrong` / `The data layer returned an error. If the
  backend is running, check that NEXT_PUBLIC_API_BASE_URL points at it.` / button
  `Try again`.

### Routes that do not exist but are linked from every screen

**MEASURED** (`ls app`): there is no `app/events/page.tsx`, no `app/rules/`, no
`app/account/`.

| Linked from | `href` | Lands on |
|---|---|---|
| `SiteHeader.tsx:7` | `/events` | 404 |
| `SiteHeader.tsx:8` | `/organizer` | OK |
| `SiteHeader.tsx:9` | `/rules` | 404 |
| `SiteHeader.tsx:66-70` | `/account` (`Sign in`) | 404 |
| `SiteHeader.tsx:71-76` | `/events` (`Browse events`) | 404 |
| `SiteFooter.tsx:4-7` | `/events`, `/rules`, `/rules#security` | 404 (`/organizer` OK) |

The header CTA — the most-clickable thing on the page — is a 404. The nav item labelled
`Events` is a 404 on a site whose event list lives at `/`.

---

## 2. MOCK or LIVE, screen by screen

The seam, all **MEASURED**:

- `const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";`
  — `lib/api.ts:44`
- `export const isMockMode = BASE_URL === "";` — `lib/api.ts:46`
- `.env.example:4` ships it empty, so **isMockMode is true**.
- Fixtures are imported at module load: `lib/api.ts:14-17`.
- Every mock payload is stamped with the label block `lib/api.ts:54-60`:
  `BUNDLED MOCK DATA. Generated from lib/mock on this machine, not read from the backend.`
- Simulated latency 120 ms in mock mode (`lib/api.ts:83-84`), so loading states flash.

| Screen | Mode | What is fixture | What is computed | Proof |
|---|---|---|---|---|
| `/` | MOCK | 6 events from `lib/mock/events.json` | sort by `startsAt` | `lib/api.ts:269-283` |
| `/events/[id]` | MOCK | event record, tiers, ticket rows | nothing on this screen beyond formatting; analytics computed from fixtures | `lib/api.ts:285-298`, `403-417` |
| `/tickets/[id]` | MOCK | ticket + ledger rows (`lib/mock/ledger.json`) | `stats` (saleCount, avgMarkupBps, peak, volume, uniqueWallets) computed in-process | `lib/api.ts:326-351`, `95-113` |
| `/my-tickets` | MOCK | tickets filtered by `ownerWallet`, wallet verification row | client-side filter via `getTickets({ownerWallet})` | `MyTicketsClient.tsx:36-44`, `lib/api.ts:300-308` |
| `/organizer` | MOCK | ledger rows → `priceSeries`, `markupDistribution`, `topDestinations`; wallet `region` strings | all computed in-process on the server render | `lib/api.ts:131-204` |
| `/verify` | MOCK | `verified` / `method` / `region` from `lib/mock/wallets.json` | nonce is `Math.random()` (`lib/api.ts:372`); the POST outcome is forced `verified: true` (`lib/api.ts:391-399`) | `lib/api.ts:206-221`, `361-400` |
| any | — | `getHealth()` exists but **nothing calls it** | — | `lib/api.ts:424-427`; no reference in `app/` |

Nothing in `app/` is fetched live even if a backend appeared: the fixtures are the only
path exercised, and no component renders the `dataSource` label that would say so
(`grep dataSource app` → no hits; the label is only defined, `lib/api.ts:54-60`, and
only consumed by the unmounted `DataSourceNote`, `components/ui.tsx:182-193`).

Client-side vs server-side matters for the script: analytics/stat numbers are computed
in the **server component render** from fixtures, whereas `/my-tickets` filters in the
**browser** (`MyTicketsClient.tsx:34-48`). Neither is a chain read.

---

## 3. Verbatim on-screen strings

Copy that may appear on camera, quoted exactly. Inline `{…}` marks a value substituted
at render time; everything else is literal.

### Ticket detail — `app/tickets/[ticketId]/page.tsx`

```
← {event.name}
Ticket {serial}
Held by {short address}
(originally issued to {short address})
Face value
issued {date, time}
Last sale price
{markup} vs face
never resold
Peak price
{markup} over face
no resales
Wallets held by
{transferCount} transfers · {saleCount} priced
Price history
Every price this specific ticket has sold for.
This ticket has not been resold.
Custody trail
Every wallet this ticket has passed through, oldest first.
On-chain
Mint address
Transfer restriction
Enforced on-chain
Not enforced
Total resale volume
Redeemed
Not yet scanned
Not on chain
```

Sources: lines 60, 65, 67, 70 (labels `Face value` 80, `Last sale price` 82, `never
resold` 94, `Peak price` 97, `Wallets held by` 103-105), card titles and subtitles
111-118 / 129-131, On-chain block 140-171. One correction to that block: `Not on chain`
is **not** on this screen. The string lives in `components/OwnershipTrail.tsx:149` and
`components/SignatureRef.tsx:25`, both unmounted. The mounted trail is
`TransferTrail`, which prints an em dash for a missing wallet and a `tx` link whenever
`signature` is set (`components/TransferTrail.tsx:84-97`) — and every fixture row has a
signature (`lib/mock/ledger.json`, no nulls), so on camera the trail shows `tx` links,
not the honest `Not on chain`.

### Verify — `app/verify/VerifyClient.tsx`

```
Verify wallet
Events with restricted transfers only issue to, and only accept transfers into, verified wallets. Verification is a signature — it proves you control the key and moves no funds.
Status
Connect the wallet you want to verify.
Verified
Not verified
Verified on
Method
Wallet signature
Identity document
Can receive transfers
Yes
No
This wallet has not completed verification yet.
This wallet is flagged for review by the organizer.
Verification is unavailable in this wallet's region.
Sign to verify
Waiting for signature…
Verifying…
Signature request was declined.
This wallet does not support message signing. Try Phantom or Solflare.
Wallet verified. You can now receive transfers for restricted events.
What gets recorded
Your public key and the time you verified.
Every ticket issued to or transferred into this wallet, with the price paid.
Nothing else. The signature proves key ownership; it is not a transaction and cannot move tokens.
```

Sources: 86, 87-90, 94, 98, 106/108, 115/116, 120/121, 125/126, flags 20-24, button
labels 146-150, decline message 79, no-signing message 53, success 160, card 179-186.

### My tickets — `app/my-tickets/MyTicketsClient.tsx`

```
My tickets
Connect a wallet to see your tickets
Tickets are bound to the wallet that holds them. Connecting only reads your public key — it never moves funds.
Verified wallet
Not verified
Showing a sample wallet from the mock fixtures. Connect a wallet to see real holdings.
This wallet is not verified, so it cannot receive transfers for events that require verification. Verify it now
Holdings
{n} ticket / {n} tickets
Loading…
No tickets in this wallet
Tickets you buy or receive will show up here.
Could not load tickets
```

Sources: 58, 61-65, 82/84, 92-93, 98-104, 109, 111, 126, 116. Note the banner text
literally says "sample wallet from the mock fixtures" — that is the one honest mock
disclosure that actually reaches the screen, and only in this state.

### Organizer — `app/organizer/page.tsx`

```
Resale analytics
What tickets are reselling for and where they are ending up, computed from the on-chain transfer record.
Event
Total resale volume
across {n} sales
Average markup
cap is +{n}%
no cap set
Median resale price
face from {SOL}
Tickets resold
{n} distinct holders
Resale price over time
Average price paid per day for {event name}.
Markup distribution
How far over face value tickets actually changed hands.
Where tickets ended up
Top holding wallets. {n} of {m} shown acquired on the secondary market.
Wallet
Region
Tickets
Source
Not shared
Resale
Primary
No holders recorded
```

Sources: 43, 45-47, 52, 73-102, 106-108, 127-129, 137-139, 148-152, 160, 164/166, 143.
Distribution bucket labels are fixed: `At or below face`, `0–25%`, `25–50%`, `50–100%`,
`100–200%`, `Over 200%` (`lib/api.ts:122-129`).

### Event — `app/events/[eventId]/page.tsx`

```
← All events
{event.name}
{venue} · {city} · {date, time}
Organized by {organizer.name}
Face value from
{n} tier / {n} tiers
Tickets issued
of {n} · {percent}
Resold at least once
{n} resale / {n} resales recorded
Average markup
cap +{n}%
no cap set
Resale price over time
Average price paid per day across every resale of this event's tickets.
Full analytics
Issued tickets
Showing {n} of {n}. Open any ticket for its full price and custody record.
No tickets issued yet
Tiers
Transfer rules
Holders may transfer or resell this ticket.
Transfers are closed for this event.
Destination wallet must be verified before a transfer will succeed.
Any wallet may receive a transfer.
Resale price is capped at +{n}% over face value, enforced at transfer time.
Resale price is uncapped, but every sale price is still recorded.
```

Sources: 46, 50, 52, 59, 65-84, 89-90, 96, 118, 122, 133, 153, 156-168.

### Chrome
```
SEATPASS
Events
For organizers
How the cap works
Sign in
Browse events
Built at the Solana x MLH hackathon.
```
(`components/SiteHeader.tsx:6-10, 57, 69, 75`; `components/SiteFooter.tsx:29`.)
Document title: `SeatPass · Tickets on Solana` (`app/layout.tsx:30`), description as at
`app/layout.tsx:31-32`.

---

## 4. Visual vocabulary — what exists, what draws, what is even mounted

| Component | What it actually draws | Mounted on a screen? | Fixture-driven? |
|---|---|---|---|
| `PriceHistoryChart` (`components/PriceHistoryChart.tsx`) | Inline SVG: hairline x axis, a face-value hairline level, accent area wash + accent line through priced points, isolated point as a 2.5px dot, a **dashed warning cap rule** with a `Cap {SOL}` chip, non-colliding y labels, thinned x labels (lines 254-390) | Yes — event page, ticket page, organizer | Yes (from fixtures via `lib/api.ts`) |
| `MarkupDistribution` (`components/MarkupDistribution.tsx`) | Real `<table>`, six rows, one accent bar per bucket scaled to the busiest bucket, count in a mono column (lines 28-62) | Yes — organizer only | Yes |
| `TransferTrail` (`components/TransferTrail.tsx`) | Vertical spine, 11px kind-coloured dot per row, kind label (`Issued` / `Resold` / `Transferred` / `Redeemed at door` / `Revoked`), price, `{markup} vs face`, timestamp, from → to address pills, `tx` link (lines 6-103) | Yes — ticket page | Yes |
| `OwnershipTrail` (`components/OwnershipTrail.tsx`) | Compact rail: accent line 12px left of 6px dots, row label (`Issued to` / `Bought by` / `Transferred to` / `Redeemed by` / `Revoked`), short address, price or em dash, `View tx` / `Not on chain` (lines 40-155) | **No** — only referenced by `components/TicketCard.tsx:207`, and `TicketCard` itself is mounted nowhere (`grep TicketCard app` → none) | Yes |
| `Sparkline` (`components/Sparkline.tsx`) | 12-point trend line, de-emphasised stroke, accent end dot, optional aria label (lines 8-43) | **No** — and `StatTile` explicitly ignores the `trend` prop (`components/StatTile.tsx:26` "Nothing draws it now"), so the ticket page's `trend={…}` at `app/tickets/[ticketId]/page.tsx:100` draws nothing | Yes, if it were mounted |
| `TierTable` (`components/TierTable.tsx`) | Real table: Tier / Face value / Issued of supply / Cap the contract admits, with `—` + sr-only `No ceiling reported for this tier` when missing (lines 25-99) | **No** — the event page uses a plain `<dl>` for tiers instead (`app/events/[eventId]/page.tsx:132-150`) | Would be |
| `AddressPill` (`components/AddressPill.tsx`) | Truncated mono address on an inset pill + 44px copy button that flips to a tick and `Copied` (lines 51-70) | Yes — event, ticket, my-tickets, verify, organizer table | Yes (fixture addresses) |
| `SignatureRef` (`components/SignatureRef.tsx`) | Text `Not on chain` (no link) when null, else a short-signature explorer link (lines 22-43) | **No** | — |
| `StatTile` / `StatRow` (`components/StatTile.tsx`) | Micro-caps label, 32px mono figure, one micro note line, hairline above (lines 6-41); 4-up grid (47-49) | Yes — event, ticket, organizer | Yes |
| `Badge` / `EventStatusBadge` / `TicketStatusBadge` (`components/Badge.tsx`) | Bordered pill with a 6px dot + label; every tone shares the same border and text class, so **colour lives only in the dot** (lines 5-12) | Yes | Yes |
| `Chip`, `Rule`, `Perforation`, `Pill`, `Panel`, `Skeleton` (`components/ui.tsx`) | Chip: pill outline; Perforation: 4-on/4-off dashed SVG line; the rest are layout primitives | `Chip` yes (`EventCard`); `Perforation` only inside the unmounted `TicketCard`; `Pill`, `Panel`, `Skeleton` **unmounted** | — |
| `Unavailable` + `DataSourceNote` (`components/ui.tsx:141-193`) | The honesty panel and the `dataSource` line | **Both unmounted** | — |

### What the chart will actually show

**INFERRED** from the prop mismatch above, and worth confirming on a real render before
recording:

- x-axis: **blank**. `points[i].label` is `undefined`; `axisText(undefined)`
  (`PriceHistoryChart.tsx:63-65`) returns it, React renders nothing.
- cap rule and chip: **absent** on all three screens. `capCeilingLamports` is never
  passed, so `capY == null` (`PriceHistoryChart.tsx:180`) and the chip block at
  `:383-390` never runs. The one warning-coloured element in the product does not appear.
- y-axis: one label only — the face value (`:92-108`, `:347-360`), because
  `lastSaleLamports` is also never passed.
- the series itself does draw: accent area wash + accent line through the priced points.

Palette risk: `theme.css:99-121` defines `--color-{canvas,surface,inset,ink,muted,line,
control,accent,accent-press,on-accent,warning,positive,danger}` and nothing else.
Pages and components still use the pre-rebuild names `text-ink-2`, `bg-plane`,
`border-hairline`, `text-ink-muted`, `bg-gridline`, and `var(--status-*)`,
`var(--series-1)`, `var(--series-2)`, `var(--baseline)`, `var(--delta-good)`,
`var(--text-muted)` — **MEASURED** as usage, **INFERRED** as effect: those utilities
resolve to nothing under Tailwind v4, so card borders and the muted text hierarchy can
drop out, and the SVG dots that read `var(--status-*)` (Badge `TONE_DOT`,
`Badge.tsx:14-21`; `TransferTrail` `KIND_DOT`, `:14-20`) can fall back to a default fill.
The chart's own `--line` / `--accent` / `--warning` / `--muted` are all real, so the
chart is the safest-looking element on the page.

---

## 5. What is not built, and how the UI says so

`lib/capabilities.ts` is a precise statement of what does not exist — and **nothing
renders it**. `grep -rn "capabilities\|cap(" app components` returns one hit, the type
import in `components/ui.tsx:3`. The `Unavailable` panel (`components/ui.tsx:141-176`)
is mounted nowhere. **MEASURED.**

Verbatim from `lib/capabilities.ts`, since a script must not claim otherwise:

```
purchase:     A checkout, payment, fee and settlement endpoint. There is none, and no fee field in any record.
listings:     A marketplace. Nothing creates a listing, no ticket ever reaches status listed, and there is no endpoint to browse or buy one.
doorCode:     A door code, a QR format and an offline verification path. No endpoint issues one and no code format exists.
eventCreation: Event creation and ticket issuance. There is no endpoint, and the resale cap is immutable once the record is initialised.
transfers:    A transfer endpoint. Custody moves are fixture rows only.
refunds:      A refund or revoke endpoint. The program has no redeem or revoke instruction either.
auth:         Any account, session or authorization layer. The only check the backend performs is an Ed25519 signature over a nonce.
```
(`lib/capabilities.ts:33-80`; the `Unavailable` panel prints the three fields as `What is
missing` / `Endpoint that would fill it` / `What this screen shows instead`,
`components/ui.tsx:160-173`.)

There is **no purchase, listing, listing browse, transfer, refund, door-code, event
creation or login flow anywhere in the tree.** Nor is there any on-chain read: no
`@solana/web3.js` call to a program, no anchor client, no instruction builder. The only
chain-facing code is URL construction — `explorerTxUrl`, `explorerAddressUrl`,
`explorerProgramUrl` (`lib/solana.ts:18-61`) — plus the wallet adapter's connection
provider (`app/providers.tsx:17-27`), which is used only to sign the verification
message.

The program strip is **not built**: the string `Program not deployed yet` appears only
inside a comment in `lib/solana.ts:53`, and `PROGRAM_ID` / `explorerProgramUrl` are
exported but referenced nowhere else (`grep` → only their own definitions). `.env.example`
lines 11-13 promise that "the on-chain strip reads 'Program not deployed yet' and the
copy and explorer controls stay disabled". **That strip does not exist in this tree.**
`app/organizer/page.tsx`, `app/events/[eventId]/page.tsx` and the ticket page make no
mention of deployment state at all.

What the UI *does* say truthfully, verbatim:

```
Program not deployed yet                     (comment only — lib/solana.ts:53, never rendered)
Not on chain                                 (components/OwnershipTrail.tsx:149, components/SignatureRef.tsx:25 — both unmounted)
No ceiling reported for this tier            (components/TierTable.tsx:90, sr-only, unmounted)
No markup buckets reported.                  (components/MarkupDistribution.tsx:24)
No ledger entries.                           (components/TransferTrail.tsx:29)
never resold                                 (app/tickets/[ticketId]/page.tsx:94)
no resales                                   (:99)
Not yet scanned                              (:168)
No Solana wallet extension detected in this browser.   (components/WalletButton.tsx:63)
Showing a sample wallet from the mock fixtures. Connect a wallet to see real holdings.   (MyTicketsClient.tsx:92)
```

`api.ts`'s own health payload is also a plain statement of the state, though nothing
renders it: `chain.programDeployed: false`, `askedCluster: false`, `rpcEnabled: false`,
`programId: null`, `detail: "No backend is configured, so this process asked no cluster
and read no artefact. Nothing here is a deployment claim."`, `contract.endpointsImplemented:
0` (`lib/api.ts:227-262`).

---

## 6. Demo click paths

Every sequence below starts from `http://<host>/`. Four are usable; each has a caveat
that has to be worked around rather than discovered on camera.

### A. Ticket provenance — the strongest story (≈40 s)
1. `/` at rest: six event cards, `Events` heading.
2. Click card `Midnight Static — North American Tour` → `/events/midnight-static-tour`.
   At rest: `Face value from 0.9 SOL / 3 tiers`, `Tickets issued 1,305 of 2,250 · 58%`,
   `Resold at least once 37% / 22 resales recorded`, `Average markup +34% / cap +75%`
   (**INFERRED**, replicated from `lib/api.ts:131-204` over the fixtures), then the price
   chart, then 25 `TicketRow`s, tiers, transfer rules.
3. Click the first row `FLO-001` → `/tickets/tkt_00001`. At rest: `Ticket FLO-001`,
   `Listed for resale` badge, `Face value 0.9 SOL`, `Last sale price 1.32 SOL / +47% vs
   face`, `Peak price 1.53 SOL / +70% over face`, `Wallets held by 4 / 2 transfers · 2
   priced`, the two-point chart, and the 3-row custody trail `Issued to → Bought by →
   Bought by`.
4. Optional: click the copy button on an `AddressPill` (flips to `Copied`).
- Works. Caveat: the mint link and the two `tx` links open Solana Explorer on addresses
  and signatures that do not exist on devnet — do not click them on camera (§7).

### B. Organizer analytics (≈30 s)
1. Click header `For organizers` → `/organizer`. **Default lands on Winter Chamber
   Series**, not Midnight Static (`app/organizer/page.tsx:32-35`).
2. Click the `Midnight Static — North A…` chip → `?event=evt_midnight_static_tour`.
   Numbers change: `50.12 SOL` volume, `+34%` average markup, `1.8 SOL` median, `37%`
   resold, `23 distinct holders` (**INFERRED**, same replication).
3. Scroll to `Markup distribution` (six rows, one bar) and `Where tickets ended up`
   (12 rows, `Resale` / `Primary` badges, region column).
- Works. Caveat: the chart has no date axis and no cap line, so "price over time" has to
  be carried by the subtitle, not the x axis.

### C. A holder's tickets (≈20 s)
1. Click `/my-tickets` directly (nothing in the header links to it — **MEASURED**: the
   nav is `Events / For organizers / How the cap works`, `SiteHeader.tsx:6-10`).
2. At rest: banner `Showing a sample wallet from the mock fixtures…`, `Verified wallet`
   badge (the fixture row says `verified: true, method: identity`,
   `lib/mock/wallets.json`), `Holdings / 9 tickets` for the demo wallet
   (`efLBNU…RLg5`, `lib/mock/wallets.json` `demoWallet`).
3. Click any row → ticket detail.
- Works, and it is the only screen that labels itself as fixture data.

### D. Verification, honestly (≈20 s)
1. Click `/verify` (no header link; type the URL).
2. At rest with no wallet: `Connect the wallet you want to verify.`
3. `What gets recorded` card is the honest payload: signature proves key ownership,
   moves no funds.
- Two ways this dies on camera: with no extension the button reads `No Solana wallet
  extension detected in this browser.`; with an extension, signing produces
  `Wallet verified.` from a **fixture** backend that forces `verified: true` whatever
  the signature (`lib/api.ts:391-399`). Do not present this as on-chain verification.

### E. Do not shoot: a nav tour
Any pass over the header's `Events`, `How the cap works`, `Sign in` or `Browse events`
lands on the `Not found` page (§1). One stray click is a dead frame.

### Controls that are disabled, and why
- `Sign to verify` — disabled only while `signing`/`submitting` (`VerifyClient.tsx:142`).
- `Disconnect` — disabled while `disconnecting` (`WalletButton.tsx:32`).
- `AddressPill` copy — never disabled; it degrades to a spoken
  `Clipboard unavailable in this browser.` (`AddressPill.tsx:107-109`).
- There is no other interactive control on any screen. No buy button, no list button,
  no transfer button, no filter inputs, no search box. The only `<button>` elements in
  the tree are the wallet connect/disconnect, the copy control, `Sign to verify`,
  `Try again`, and `Pill`'s button branch (unmounted).

---

## 7. What would be dishonest to present as a live product

Ranked by how easy the mistake is to make in a 2-minute cut.

1. **Fixture prices presented as market evidence.** Every number on every screen is
   generated from `lib/mock/*.json` — 6 events, 128 tickets, 253 ledger rows, 90 sales.
   The label that says so (`lib/api.ts:54-60`) exists and is rendered **nowhere**; the
   banner that would say it (`components/AppShell.tsx:61-67`, `Mock data — set
   NEXT_PUBLIC_API_BASE_URL to read from the backend.`) belongs to a shell the layout
   does not use (`app/layout.tsx:49-53` mounts `SiteHeader`/`SiteFooter`, not `AppShell`).
   On camera the analytics screen is indistinguishable from a live one.
2. **`Enforced on-chain` on the ticket page** (`app/tickets/[ticketId]/page.tsx:158`).
   It is a fixture boolean (`transferRestricted: true` in `lib/mock/tickets.json`). There
   is no deployed program, no RPC read, and `lib/api.ts:227-262` says `rpcEnabled: false`
   in the same build. This one sentence is the most misleading string in the app.
3. **Explorer links that 404.** `Mint address` links to
   `explorer.solana.com/address/{mint}` and each trail row links `tx` to
   `explorer.solana.com/tx/{signature}` (`lib/solana.ts:18-26`; `TransferTrail.tsx:88-97`;
   ticket page `:145-153`). The mints and signatures are invented, and every ledger row
   has one (`lib/mock/ledger.json` — no null signatures). `API_CONTRACT.md:145-146` says
   to return `null` rather than a placeholder "or the link 404s". Never click these.
4. **`Listed for resale`.** 18 fixture tickets carry `status: "listed"` (e.g.
   `lib/mock/tickets.json` `tkt_00001`), and `TicketStatusBadge` renders `Listed for
   resale` (`components/Badge.tsx:55`). `lib/capabilities.ts:41-42` states the opposite:
   "no ticket ever reaches status listed". The screen advertises a marketplace that does
   not exist.
5. **`Verified wallet` / `Wallet verified.`** driven by `lib/mock/wallets.json` and a
   forced `verified: true` (`lib/api.ts:391-399`). Real Ed25519 checking is backend-side
   and there is no backend.
6. **`Where tickets ended up` region column** — `Chicago, IL`, `Detroit, MI`,
   `Indianapolis, IN` (`lib/mock/wallets.json`). Invention presented as volunteered
   personal location data. `API_CONTRACT.md:138-139` says to populate it "only when the
   wallet volunteered one".
7. **The cap visual.** Because `capCeilingLamports` is never passed, the dashed cap rule
   and `Cap … SOL` chip never draw. If the script says "this dashed line is the cap",
   the line is not on screen.
8. **Sparklines.** `trend={…}` is passed on the ticket page
   (`app/tickets/[ticketId]/page.tsx:100`) but `StatTile` ignores it
   (`components/StatTile.tsx:26`). Do not describe a sparkline in the tiles.
9. **`Showing 25 of 1,305`.** `getTickets({eventId, limit: 25})`
   (`app/events/[eventId]/page.tsx:33`) with a subtitle that says so (line 118). It is
   honest, but do not crop the subtitle out and imply 25 is the population.
10. **Two brand names.** Visible wordmark `SEATPASS` (`SiteHeader.tsx:57`) and document
    title `SeatPass · Tickets on Solana` (`app/layout.tsx:30`), but `README.md:1` says
    "Ticketpath" and the unmounted shell says `Ticketpath` (`AppShell.tsx:31`). Only the
    first two reach the screen.

---

## 8. Collisions — the screen may move under the video

`git -C ~/ticketing-frontend status --porcelain` at read time: **23 modified, 17
untracked**, on top of a single baseline commit (`0208765 baseline: untouched tree before
the SeatPass rebuild`). Another agent is rebuilding this tree now. Everything below can
change between a script being written and a shot being taken.

**Modified (in flux):** `.env.example`, `app/globals.css`, `app/layout.tsx`,
`components/AddressPill.tsx`, `components/EventCard.tsx`,
`components/MarkupDistribution.tsx`, `components/PriceHistoryChart.tsx`,
`components/StatTile.tsx`, `components/WalletButton.tsx`, `lib/api.ts`, `lib/format.ts`,
`lib/solana.ts`, `lib/types.ts`, `lib/viz.ts`, `package.json`, `tsconfig.json`.

**Untracked (new, unproven):** `app/theme.css`, `components/OwnershipTrail.tsx`,
`components/SignatureRef.tsx`, `components/SiteFooter.tsx`, `components/SiteHeader.tsx`,
`components/TicketCard.tsx`, `components/TierTable.tsx`, `components/ui.tsx`,
`lib/cap.ts`, `lib/capabilities.ts`, `lib/http.ts`, `lib/*.test.ts`, `tools/`.

Specific collisions that change what a viewer sees:

1. **The tree does not typecheck** (three `PriceHistoryChart` call sites vs its signature,
   §0/§4). Any build-based capture fails until that is reconciled; a dev-server capture
   renders anyway, with the empty axes described above. **INFERRED** from
   `tsconfig.json:7` + the prop sets; do not quote this as verified until someone runs
   `npm run typecheck`.
2. **Design-system migration mid-flight.** `app/theme.css` defines a new token set; the
   screens still consume the old class names (`text-ink-2`, `bg-plane`,
   `border-hairline`, `bg-gridline`) and old CSS vars (`--series-1`, `--status-*`,
   `--baseline`, `--delta-good`). Either the pages get ported or `theme.css` grows a
   compatibility layer; either way borders, muted text and status dots may look
   different tomorrow than they do today.
3. **The rebuilt vocabulary is written but not wired.** `TicketCard` (hero card, notches,
   perforation, `OwnershipTrail` strip), `TierTable`, `SignatureRef`, `Sparkline`,
   `Unavailable`, `DataSourceNote`, `AppShell` all exist and none is mounted. The landing
   screen these were built for does not exist: `/` is still the plain event grid. A
   pending `app/page.tsx` change could replace the whole first shot.
4. **Honesty scaffolding is written but not wired.** `lib/capabilities.ts`,
   `getHealth()` and the `dataSource` labels are dead code today. If they get mounted
   before the shoot, screens gain `Unavailable` panels and data-source lines that are not
   in §3 — and the mock disclosure in §7.1 becomes true instead of missing.
5. **`../ticketing-frontend/tools/build-copy.sh` exists** and builds/serves a throwaway copy rather than the
   live tree, because a server is already serving this checkout for another session. Any
   capture pipeline should use it; a build in place would swap the bundle under that
   server. (Read only — nothing there was executed.)
6. **`README.md` is stale** relative to the rebuild: it documents `/events/[slug]`
   (actual route is `/events/[eventId]`, resolved by slug), calls the app "Ticketpath",
   and claims "Every chart with a sub-3:1 fill ships a table view (`View as table`)" —
   no such control exists in any component (grep: no hits). Do not take README claims
   into the script.
7. **Uncommitted by design.** Nothing here is reviewable as a diff base; a `git diff`
   against `0208765` is effectively the whole app, so "what changed" cannot be scoped
   from history alone.

---

## Appendix — expected on-screen figures for the two most likely shots

**INFERRED**: produced by replicating `lib/api.ts:131-204` (analytics) and
`:95-113` (per-ticket stats) over `lib/mock/*.json`, then applying `lib/format.ts`. Not
read off a rendered page. Re-check on the day, and label on screen as fixture data.

Midnight Static — North American Tour (`evt_midnight_static_tour`, 35 tickets):

| Where | Label | Value |
|---|---|---|
| Event tiles | Face value from | `0.9 SOL` (3 tiers) |
| | Tickets issued | `1,305` of `2,250` · `58%` |
| | Resold at least once | `37%` (22 resales recorded) |
| | Average markup | `+34%` · cap `+75%` |
| Organizer tiles | Total resale volume | `50.12 SOL` across 22 sales |
| | Average markup | `+34%`, "cap is +75%" |
| | Median resale price | `1.8 SOL`, face from `0.9 SOL` |
| | Tickets resold | `37%`, `23 distinct holders` |

Ticket `tkt_00001` (`FLO-001`): `Face value 0.9 SOL` · `Last sale price 1.32 SOL` /
`+47% vs face` · `Peak price 1.53 SOL` / `+70% over face` · `Wallets held by 4` /
`2 transfers · 2 priced` · trail `Issued to → Bought by → Bought by` · status
`Listed for resale` (`lib/mock/ledger.json` rows for `tkt_00001`; `lib/mock/tickets.json`).

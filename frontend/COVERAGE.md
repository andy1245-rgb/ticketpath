# COVERAGE

Every row of the feature inventory in the brief (section 1.6) against the screen
that shows it, the component that renders it, the call that reads it and the test
that covers it. 43 of 43 rows accounted for. REAL rows have a route and a test;
every other row has a named state.

## Feature inventory, 43 rows

`REAL` = served today. `STUB` = the field exists and is unbacked. `NOT FOUND` =
nothing implements it, and the UI says so.

| # | Feature | Status | Route | Component | API call | Test / state |
|---|---|---|---|---|---|---|
| 1 | Event browse: status, city, q, cursor, limit, startsAt asc | REAL | `/events` | `EventCard`, filter form, paging links | `getEvents(query)` | `buildQuery keeps the given order and drops unset values`; `paginate walks the cursor and stops` |
| 2 | Event by id or slug, 404 | REAL | `/events/[slug]` | page head, policy block | `getEvent(idOrSlug)` | `mapErrorBody reads message, then error, then the status line`; NF state via `notFound()` |
| 3 | Tiers: name, faceValueLamports, totalSupply, issuedCount | REAL | `/events/[slug]` | `TierTable` | `getEvent` | `lamports format as integers, and as SOL only at the edge` |
| 4 | Policy: resaleEnabled, resalePriceCapBps, requiresVerifiedWallet | REAL policy, STUB enforcement | `/events/[slug]`, `/rules` | policy block, `TierTable` cap column | `getEvent`, `getHealth` | `the cap predicate admits the ceiling and refuses one lamport more`; `/rules` states the enforcement status from `chain.programDeployed` |
| 5 | Ticket list; ownerWallet filters current owner | REAL | `/my-tickets` | `MyTicketsClient` table | `getTickets({ownerWallet})` | NW / UV / E / ER panels; `paginate` test |
| 6 | Ticket by id or mint | REAL | `/tickets/[ticketId]` | page head, record `<dl>` | `getTicket(idOrMint)` | NF via `notFound()`; mint addressing exercised in a throwaway copy |
| 7 | serial, ownerWallet, issuedToWallet, status, issuedAt, redeemedAt | REAL | `/tickets/[ticketId]`, `/door` | record `<dl>`, door rows | `getTicket` | `shortAddress truncates the middle and leaves what is already short` |
| 8 | History: every ledger kind, oldest first | REAL | `/tickets/[ticketId]` | `OwnershipTrail variant="full"` | `getResaleHistory` | `a null signature is a row with no on-chain counterpart` |
| 9 | markupBps on that ticket's own tier face, never stored | REAL | `/tickets/[ticketId]` | `OwnershipTrail`, stat tiles | `getResaleHistory` | `markup rounds to the nearest basis point` |
| 10 | saleCount, transferCount, avgMarkupBps, peak, last, volume, uniqueWallets | REAL | `/tickets/[ticketId]` | `StatTile` row | `getResaleHistory().stats` | `markup basis points round the way the figure is shown` |
| 11 | Analytics: volume, saleCount, avgMarkupBps, median, resoldShare, uniqueHolders | REAL | `/organizer`, `/events/[slug]` | `StatTile` row | `getEventAnalytics` | `lamports format as integers`; ER panel on failure |
| 12 | Daily series, UTC buckets, nullable per-day markup | REAL | `/organizer`, `/events/[slug]` | `PriceHistoryChart variant="page"` | `getEventAnalytics().priceSeries` | chart renders real axis labels; verified at 1440/390/320 |
| 13 | Markup distribution, six fixed buckets | REAL | `/organizer`, `/events/[slug]` | `MarkupDistribution` | `getEventAnalytics().markupDistribution` | all six rows including zero-count; table with caption and row headers |
| 14 | Top destinations, 12 rows, acquiredOnSecondary, region | REAL, region STUB null | `/organizer`, `/events/[slug]` | destinations table, `AddressPill` | `getEventAnalytics().topDestinations` | em dash for a null region plus one sentence; live data returns null on every row |
| 15 | Verification read; unknown wallet 200 false | REAL | `/account`, `/verify`, `/my-tickets` | `AccountClient`, `VerifyClient` | `getWalletVerification` | UV state; flags printed verbatim |
| 16 | Challenge: 32 hex nonce, 300 s, single use, wallet bound | REAL | `/account`, `/verify` | verify flow | `startWalletVerification` | `the verification message is frozen, byte for byte, with no trailing newline` |
| 17 | Ed25519 detached check, frozen message | REAL | `/account`, `/verify` | verify flow, message `<pre>` | `completeWalletVerification` | same frozen-message test |
| 18 | canPurchase, canReceiveTransfer, flags[] | ADVISORY, gates nothing | `/account` | verification fields | `getWalletVerification` | fields shown; the page states the flags gate nothing at runtime |
| 19 | /health: dataSource, chain, pricingModel, contract counts | REAL | `/pricing` | health field list, `DataSourceNote` | `getHealth` | ER panel with the ApiError message and code |
| 20 | Errors {message,status,code}, 404, CORS, OPTIONS 204 | REAL | every route | `app/error.tsx`, `app/not-found.tsx`, per-screen ER panels | `requestJson` | `mapErrorBody reads message, then error, then the status line`; `requestJson returns the body and maps a failed response` |
| 21 | Console HTML /, guidance, badges, eight events | REAL, HTML only | `/pricing` | console link to `<base>/` | `getHealth` (`NEXT_PUBLIC_API_BASE_URL`) | link when the origin is set, plain text when not; no iframe (grep 0) |
| 22 | Sim ?sim=1, cap 6010, labelled simulation | REAL, console only | `/pricing` | link to the console | none | labelled as the backend's console, not embedded |
| 23 | Price bound, [UNVALIDATED], fitted false | REAL, console only | `/pricing` | pricingModel block | `getHealth` | `pricingModel.fitted` and the note printed verbatim |
| 24 | Cap predicate price*10000 <= face*(10000+cap_bps) | REAL on chain | `/rules`, cap chip | worked example, cap chip | none | `the cap predicate admits the ceiling and refuses one lamport more`; `a cap of zero admits the face and nothing above it` |
| 25 | Instructions 0-3, meta, InitializeRecord, SetPendingPrice, SetStatus | REAL, no client | `/rules` | cap-immutability copy | none | static; states the cap is fixed at record initialisation |
| 26 | Codes 6008-6028 | REAL, code only | `/rules#security` | anchor section | none | named in the security section |
| 27 | Jurisdiction gate, tighten-only policy | REAL code, not deployed | `/rules`, `/events/[slug]` | enforced-cap precedence | `getEvent`, `getHealth` | `the most a buyer may pay prefers the enforced ceiling over the platform cap` |
| 28 | Mint address | STUB (SYN prefix, no account) | `/tickets/[ticketId]` | record `<dl>` | `getTicket().mintAddress` | shown as a field, never linked as a live account |
| 29 | Signature and slot | NOT FOUND (null on every row) | `/tickets/[ticketId]`, `/` | `OwnershipTrail`, `SignatureRef` path | `getResaleHistory` | `a null signature is a row with no on-chain counterpart`; "Not on chain" per row |
| 30 | transferRestricted | STUB (always false) | `/tickets/[ticketId]` | record `<dl>` | `getTicket` | field shown; not presented as an enforcement claim |
| 31 | Organizer.verified | STUB (always false) | `/events/[slug]` | organizer row | `getEvent` | shown as false, no badge invented |
| 32 | Event.imageUrl | STUB (always null) | `/events`, `/events/[slug]` | `EventCard` | `getEvent(s)` | no image and no placeholder box that implies one |
| 33 | Region | STUB (always null) | `/organizer`, `/events/[slug]` | destinations table | `getEventAnalytics` | em dash plus the volunteered-only sentence |
| 34 | Ticket status "listed" | NOT FOUND | `/resale`, `/resale/list/[ticketId]` | `Unavailable` (listings) | none | named state: no listing can be created, so the status never appears |
| 35 | Purchase, checkout, payment, fees, settlement | NOT FOUND | `/events/[slug]/checkout` | `Unavailable` (purchase) | none | UN panel naming the missing endpoint; no success state exists |
| 36 | Ticket issuance and minting | NOT FOUND | `/organizer/events/new` | `Unavailable` (eventCreation) | none | UN panel plus a sentence that issuance has no endpoint |
| 37 | Door code, QR, offline verification | NOT FOUND | `/door`, `/tickets/[ticketId]` | `Unavailable` (doorCode) | none | UN panel stating no offline code format exists |
| 38 | Redeem and revoke | NOT FOUND | `/door`, `/tickets/[ticketId]` | `Unavailable` (doorCode) | `getTicket` (read only) | UN panel; the program has no redeem instruction |
| 39 | Create, browse or buy a listing | NOT FOUND | `/resale` | `Unavailable` (listings) + E | none | empty state names `GET /api/listings`; zero rows |
| 40 | Organizer creates an event or sets the cap | NOT FOUND | `/organizer/events/new` | `Unavailable` (eventCreation) | none | cap field shows the rule and that it is immutable |
| 41 | Refunds and user transfers | NOT FOUND | `/tickets/[ticketId]` | `Unavailable` (transfers, refunds) | none | named state |
| 42 | Account, session, authorization | NOT FOUND | `/account`, `/organizer` | `Unavailable` (auth), no-auth sentence | `getWalletVerification` | stated on the page; `/organizer` says anyone can read it |
| 43 | Admin: no role, no route, no endpoint | NOT FOUND | not built | none | none | deliberately absent, per the brief |

## Screens, states and how each is reached

`L` loading · `E` empty · `NW` no wallet · `UV` unverified · `NF` not found ·
`ER` error · `UN` unavailable. Success is the rendered state everywhere; a
screen that cannot succeed renders no success state at all.

| Route | Who | States | Reached by |
|---|---|---|---|
| `/` | public | L, E, ER | L: `app/loading.tsx` while four reads resolve. E: `getEvents({status:"on_sale"})` returns no items — no hero card and no proof band. ER: the thrown ApiError reaches `app/error.tsx` (no try/catch on the page). |
| `/events` | public | L, E, ER | L: `app/events/loading.tsx`. E: filters match nothing, with the filters named. ER: error boundary. |
| `/events/[slug]` | public | L, E, NF, ER | L: route loading file. E: the event has no tickets issued yet. NF: `getEvent` 404 → `notFound()`. ER: boundary. |
| `/events/[slug]/checkout` | wallet | NW, UV, UN, ER | NW: no wallet. UV: connected, `verified` false, flags shown. UN: the payment step is an `Unavailable` panel in every wallet state. ER: verification read fails. |
| `/my-tickets` | wallet | NW, UV, E, L, ER | NW: no wallet, no auto-connect. UV: connected and unverified, holdings still shown. E: the wallet holds nothing. L: skeletons. ER: panel with message and code plus retry. |
| `/tickets/[ticketId]` | public | NF, L, E, ER | NF: `getTicket` 404 → `notFound()`. E: ticket exists, `getResaleHistory` returns no entries — record stays, rail and stats are replaced by one sentence. ER: boundary. |
| `/door` | staff | NF, L, ER | NF: `getTicket` 404. L: route loading file. ER: ApiError message and code on the page, because a door needs the reason. |
| `/organizer` | public, no auth | L, E, ER | L: route loading file. E: no events, or the selected event has no sales yet. ER: boundary. |
| `/organizer/events/new` | organizer | UN | The form is an illustration inside disabled fieldsets; submit is an `Unavailable` panel. |
| `/resale` | wallet | UN, E | UN: listings capability. E: the empty state names `GET /api/listings`, zero rows. |
| `/resale/list/[ticketId]` | wallet | UN, ER | UN: submit is an `Unavailable` panel; an over-cap price shows a warning chip and blocks. ER: `getTicket` failure panel. |
| `/account` | wallet | NW, UV, L, ER | NW: no wallet. UV: connected and unverified. L: skeleton on first read. ER: panel with message and code. |
| `/pricing` | public | L, UN, ER | L: Suspense skeleton. UN: `pricingModel.available` false prints the backend's reason. ER: panel with message and code. |
| `/verify` | wallet | NW, UV, ER | Same flow as `/account`; a rejected or failed signature prints its own code. |
| `/rules` | public | static | No data beyond `getHealth`; if `/health` is unreachable the page states the status without a number. |

## Components

Twelve components plus `useMeasure` and the shared primitives in `ui.tsx`:
`SiteHeader`, `SiteFooter`, `TicketCard`, `EventCard`, `TierTable`,
`PriceHistoryChart`, `MarkupDistribution`, `OwnershipTrail`, `StatTile`,
`AddressPill`, `WalletButton`, plus the primitives module. No component fetches:
`grep 'fetch(' components/` is 0.

## Verification of this file

- Every REAL row above has a route in the table and either a named test or a
  measured check. 15 unit tests, all passing (`npm test`).
- Every non-REAL row has a named state, and that state is in the screen table.
- The render sweep in `tools/verify-landing.cjs` passes on all 15 routes at 1440
  and 390. Numbers in `VERIFY.md`.

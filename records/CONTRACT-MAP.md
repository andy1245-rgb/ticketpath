# CONTRACT-MAP — what the frontend asks for, and what this backend can honestly answer

**Status:** complete for the nine endpoints in `API_CONTRACT.md`.
**Written:** 2026-11-07T11:10Z. **Author:** build agent, read directly from
`/home/friend/ticketing-frontend/API_CONTRACT.md`, `lib/types.ts`, `lib/solana.ts` and
`lib/api.ts` (read-only; nothing in that tree was modified).
**Purpose:** this file is the acceptance test for the backend. If a claim here and the
code disagree, the code is wrong.

**Sources of truth, in order:** `lib/types.ts` (the wire types) → `API_CONTRACT.md` (the
endpoint semantics) → `lib/api.ts` (the client's actual behaviour, including which
fields it computes itself in fixture mode). Where the two documents disagree, the
disagreement is recorded in §7 rather than resolved silently.

## Legend for the "can serve" column

| Code | Meaning |
|---|---|
| **YES** | The backend returns this field, computed from the ledger store, and a test asserts the value. |
| **STUB** | The backend returns a field of the right shape whose value is structurally true but not backed by a real system (no chain, no identity provider, no media). Where a boolean is concerned, it returns the *honest* value, which is `false`. |
| **NO** | The data does not exist on this machine, so the field cannot be populated. `null` is returned where the type allows it; where the type does not allow `null`, §5 says what happens. |

Every payload that contains fixture-derived data carries a top-level `dataSource`
object with `synthetic: true` and a readable label. That key is not in `lib/types.ts`;
§7 records it as an addition. It does not break deserialisation: TypeScript types do
not reject extra keys at runtime.

---

## 1. Conventions, as implemented

| Contract convention | Implemented as |
|---|---|
| Money is an integer count of lamports | Every amount is a Python `int`. No float touches a lamport: `tests/test_markup.py` covers the rounding. |
| Markup is basis points over face, signed | Computed per ledger row from that row's ticket's own tier face (`core/ledger_entries.py`), half away from zero. Never stored in the fixture, so it cannot disagree with the price. |
| Timestamps are ISO-8601 UTC | Parsed with a strict `fromisoformat` wrapper; day buckets are converted to UTC before formatting (`core/timeutil.py`). |
| Collections return `{items, nextCursor}` | `core/pagination.py`. Cursor is the decimal offset, which is what `lib/api.ts` produces in fixture mode. `limit` defaults to 50, caps at 200, `limit<1` or a non-integer is 400. |
| Errors are JSON with `message` or `error` | `{"message": ..., "status": ..., "code": ...}`. `message` is the string the client surfaces. 404 on a missing event or ticket, never 200-with-null. |
| Base URL | The document says `http://localhost:8787`. **8787 is occupied by another process on this machine**, so the backend binds **8788**. `TICKETPATH_PORT` overrides. §7.1. |
| CORS | Not in the contract, but the frontend is a browser app on `localhost:3000` calling `localhost:8788` and POSTing JSON, which is a preflighted request. `access-control-allow-origin` (default `*`, `TICKETPATH_ALLOW_ORIGIN` overrides), `-methods: GET, POST, OPTIONS`, `-headers: content-type`, `OPTIONS` answers 204. Without this a judge's browser blocks every call. |

## 2. Endpoints

| # | Method | Path | Request | Response | Can serve | Where it comes from today | Proof |
|---|---|---|---|---|---|---|---|
| 1 | GET | `/api/events` | `EventQuery`: `status?`, `city?`, `q?`, `cursor?`, `limit?` | `Page<Event>` | **YES** | fixture store; filter, sort by `startsAt`, paginate | `tests/test_http_contract.py::TestEvents` |
| 2 | GET | `/api/events/:idOrSlug` | path: opaque id or slug | `Event`, 404 if absent | **YES** | store row + organizer row; totals summed from tiers | `TestEvents::test_detail_by_id_and_by_slug` |
| 3 | GET | `/api/tickets` | `TicketQuery`: `eventId?`, `ownerWallet?`, `status?`, `cursor?`, `limit?` | `Page<Ticket>` | **YES** | store rows; `ownerWallet` filters the *current* owner column | `TestTickets::test_owner_wallet_filters_on_current_owner_not_issuee` |
| 4 | GET | `/api/tickets/:ticketId` | path: ticket id **or mint address** | `Ticket`, 404 if absent | **YES**, with `STUB` fields (`mintAddress`, `transferRestricted`, see §4.2) | store row + tier face + ledger-derived counts | `TestTickets::test_detail_by_id_and_mint` |
| 5 | GET | `/api/tickets/:ticketId/resale-history` | path: ticket id | `ResaleHistory` | **YES** (the primary real endpoint) | full ledger trail + `core/resale_stats.py` | `tests/test_resale_history.py`, `TestTickets::test_resale_history_is_the_real_computation` |
| 6 | GET | `/api/wallets/:wallet/verification` | path: 32-byte base58 pubkey | `WalletVerification`; unknown wallet is 200 `verified:false` | **YES** | in-memory verification store, empty at boot | `tests/test_wallet_verification_flow.py::TestUnknownWallet` |
| 7 | POST | `/api/wallets/:wallet/verification/challenge` | no body (the client sends none) | `{nonce, expiresAt}` | **YES** | `secrets.token_hex(16)`, 300 s TTL, single use | `TestChallengeAndVerify` |
| 8 | POST | `/api/wallets/:wallet/verification` | `{nonce, signature}`; signature is base58 of 64 detached Ed25519 bytes | `WalletVerification`; 400 `message` on a bad/expired nonce | **YES** | pure-Python RFC 8032 Ed25519 verification over the frozen message | `tests/test_ed25519.py`, `TestChallengeAndVerify` |
| 9 | GET | `/api/events/:eventId/analytics` | path: event id | `EventAnalytics` | **YES** | `core/event_analytics.py` over the event's tickets and ledger | `tests/test_event_analytics.py`, `TestAnalytics` |

Plus one route that is not in the contract:

| — | GET | `/health` | none | service, version, status, `now`, `dataSource`, `chain`, `pricingModel`, `contract` | **YES** | adapters. It never claims a deployment or a model. | `TestHealth` |

`/health` is how a reader finds out, in one call, that the ledger is synthetic, that no
program is deployed, and that no pricing model is registered. It is deliberately not
under `/api`, so it cannot be mistaken for a contract endpoint.

## 3. Query semantics, exactly

| Parameter | Rule implemented | On violation |
|---|---|---|
| `status` (events) | one of `draft, on_sale, sold_out, completed, cancelled` | 400 `status_invalid` |
| `status` (tickets) | one of `valid, listed, redeemed, revoked` | 400 `status_invalid` |
| `city` | case-insensitive equality. The contract does not say whether it is exact; equality is the conservative reading, and fixture cities are single-token. | empty page |
| `q` | case-insensitive substring over `name` + `venue` | empty page |
| `cursor` | decimal offset, ≥ 0. Missing or empty means the start. | 400 `cursor_invalid` |
| `limit` | integer 1..200, default 50 | 400 `limit_invalid` |
| `eventId`, `ownerWallet` | exact string match; unknown value yields an empty page, not a 404 | empty page |

Event order is `startsAt` ascending, with `id` breaking ties. Ticket order is `id`
ascending; the contract does not specify ticket order.

## 4. Field-by-field: every type in `lib/types.ts`

### 4.1 `Event` (endpoint 1, 2) and its parts

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `id` | `string` | fixture store | YES |
| `slug` | `string` | fixture store | YES |
| `name` | `string` | fixture store (says "Synthetic") | YES |
| `description` | `string` | fixture store (says it is a fixture) | YES |
| `venue` | `string` | fixture store | YES |
| `city` | `string` | fixture store (`Toronto`) | YES |
| `startsAt` | `string` | fixture store | YES |
| `endsAt` | `string \| null` | fixture store; null on the upcoming event | YES |
| `imageUrl` | `string \| null` | no media exists | STUB: always `null` |
| `organizer` | `Organizer` | see 4.1.1 | YES/STUB |
| `status` | `EventStatus` | fixture store | YES |
| `tiers` | `TicketTier[]` | fixture store | YES |
| `totalSupply` | `number` | summed from tiers | YES |
| `issuedCount` | `number` | summed from tiers; the adapter refuses a store whose ticket rows disagree | YES |
| `resaleEnabled` | `boolean` | fixture store (organizer policy) | YES |
| `resalePriceCapBps` | `number \| null` | fixture store (organizer policy) | STUB: carried as policy; **not enforced anywhere** until the on-chain program ships (§5.3) |
| `requiresVerifiedWallet` | `boolean` | fixture store (organizer policy) | STUB: carried as policy; enforcement lives in the transfer hook, not in this API (§5.3) |

#### 4.1.1 `Organizer`

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `id` | `string` | fixture store | YES |
| `name` | `string` | fixture store (says "synthetic") | YES |
| `walletAddress` | `WalletAddress` | fixture store, `FXTURE…` placeholder | STUB: shape-valid base58, no account exists |
| `verified` | `boolean` | fixture store, `false` | STUB: there is no organizer-verification process, so `false` is the only honest value |

#### 4.1.2 `TicketTier`

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `id`, `name` | `string` | fixture store | YES |
| `faceValueLamports` | `number` | fixture store | YES: this is the denominator for every markup |
| `totalSupply` | `number` | fixture store | YES |
| `issuedCount` | `number` | fixture store; must equal the ticket rows or the store is refused | YES |

### 4.2 `Ticket` (endpoints 3, 4)

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `id` | `string` | fixture store | YES |
| `eventId`, `tierId` | `string` | fixture store | YES |
| `mintAddress` | `string` | fixture store, `FXTURE…` placeholder, 32 bytes when base58-decoded | **STUB**: no SPL mint exists on any cluster, so an explorer link built from it resolves to nothing. The contract says this must be a real mint; it cannot be yet (§5.1) |
| `serial` | `string` | fixture store | YES |
| `ownerWallet` | `WalletAddress` | fixture store; the adapter refuses a mismatch with the last custody move | YES |
| `issuedToWallet` | `WalletAddress` | fixture store; must match the `issue` row | YES |
| `faceValueLamports` | `number` | the ticket's own tier | YES |
| `lastSalePriceLamports` | `number \| null` | last priced `sale` in the trail, else null | YES |
| `transferCount` | `number` | `sale` + `transfer` entries; issue and redeem excluded | YES |
| `status` | `TicketStatus` | fixture store | YES |
| `transferRestricted` | `boolean` | RPC adapter → **`false`** | **STUB/false**: the contract defines this as *actually enforced on-chain right now*. No program is deployed, so `false` is the only true answer. It is not the event's `requiresVerifiedWallet` restated (§5.2) |
| `issuedAt` | `string` | the `issue` row's `occurredAt` | YES |
| `redeemedAt` | `string \| null` | fixture store | YES |

### 4.3 `LedgerEntry` (endpoint 5)

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `id` | `string` | fixture store | YES |
| `ticketId` | `string` | fixture store | YES |
| `kind` | `LedgerEntryKind` | fixture store; all five kinds are represented across the store (`issue`, `sale`, `transfer`, `redeem`) | YES (`revoke` accepted, no row uses it) |
| `fromWallet` | `string \| null` | fixture store; null on `issue` | YES |
| `toWallet` | `string \| null` | fixture store; null on `redeem` | YES |
| `priceLamports` | `number \| null` | fixture store; null on everything that is not a `sale` (adapter refuses a priced transfer) | YES |
| `markupBps` | `number \| null` | computed from that entry's own ticket face | YES |
| `signature` | `string \| null` | no transaction exists | **NO**: always `null`. The contract prefers null to a placeholder, because a placeholder 404s in Explorer. |
| `slot` | `number \| null` | no transaction exists | **NO**: always `null` |
| `occurredAt` | `string` | fixture store | YES |

### 4.4 `ResaleStats` and `ResaleHistory` (endpoint 5)

| Field | TS type | Rule implemented | Can serve |
|---|---|---|---|
| `ticketId` | `string` | echoed | YES |
| `faceValueLamports` | `number` | the ticket's tier face | YES |
| `entries` | `LedgerEntry[]` | chronological, oldest first, every kind kept | YES |
| `stats.saleCount` | `number` | priced sales only | YES |
| `stats.transferCount` | `number` | `sale` + `transfer`; excludes `issue`, `redeem`, `revoke` | YES |
| `stats.avgMarkupBps` | `number \| null` | mean of each sale's own markup, rounded half away from zero; `null` with no sales | YES |
| `stats.peakPriceLamports` | `number \| null` | max sale price; `null` with no sales | YES |
| `stats.lastPriceLamports` | `number \| null` | price of the last sale in time, not the last row | YES |
| `stats.totalVolumeLamports` | `number` | sum of sale prices; unpriced moves add nothing | YES |
| `stats.uniqueWallets` | `number` | distinct wallets across the whole trail, both sides, including the issuee and a redeem source | YES |

### 4.5 `WalletVerification` (endpoints 6, 8)

| Field | TS type | Source today | Can serve |
|---|---|---|---|
| `wallet` | `WalletAddress` | the path, validated as 32 base58 bytes | YES |
| `verified` | `boolean` | in-memory store; `false` unless a signature was verified in this process | YES |
| `verifiedAt` | `string \| null` | set on success from the injected clock | YES |
| `method` | `VerificationMethod` | `"wallet_signature"` or `null`. `"identity"` is never returned | YES (identity is NO, §5.4) |
| `canPurchase` | `boolean` | equals `verified` | STUB semantics: there is no purchase flow in this product, so the flag gates nothing here |
| `canReceiveTransfer` | `boolean` | equals `verified` | STUB semantics: transfer permission is actually enforced on-chain by the hook, not by this flag (§5.3) |
| `flags` | `string[]` | `["wallet_not_verified"]` when unverified; `[]` when verified. The contract defines this as reasons a capability is false, so persistence caveats go in `dataSource.note` instead | YES |

Nonce mechanics, exactly as implemented: 32 hex characters from `secrets.token_hex(16)`;
TTL 300 s; the nonce is **consumed on any attempt**, success or failure, so a captured
signature cannot be replayed; a nonce presented for a different wallet is refused; an
expired nonce is refused; state lives in process memory and is lost on restart.

### 4.6 `PricePoint`, `MarkupBucket`, `DestinationRow`, `EventAnalytics` (endpoint 9)

| Field | TS type | Rule implemented | Can serve |
|---|---|---|---|
| `eventId` | `string` | echoed | YES |
| `faceValueLamports` | `number` | the **lowest** tier face, as the contract requires | YES |
| `totalVolumeLamports` | `number` | sum of sale prices | YES |
| `saleCount` | `number` | priced sales | YES |
| `avgMarkupBps` | `number \| null` | mean of per-sale markups, each against its own ticket face | YES |
| `medianResalePriceLamports` | `number \| null` | median of sale prices, even count averaged | YES |
| `resoldShare` | `number` | distinct resold tickets ÷ issued ticket rows. The adapter enforces `issuedCount` = ticket rows, so both readings of the contract agree | YES |
| `uniqueHolders` | `number` | distinct current `ownerWallet` | YES |
| `priceSeries[].date` | `string` | UTC day of `occurredAt`, `YYYY-MM-DD` | YES |
| `priceSeries[].avgPriceLamports` | `number` | mean of that day's sale prices | YES |
| `priceSeries[].saleCount` | `number` | that day's sales | YES |
| `priceSeries[].avgMarkupBps` | `number \| null` | mean of that day's per-sale markups; `null` when a day has no priced sales. **Never** re-derived from `avgPriceLamports` and an event-level face | YES |
| `markupDistribution[]` | `MarkupBucket[6]` | all six buckets in contract order with the contract's exact bounds, zero-count included | YES |
| `markupDistribution[].label/fromBps/toBps` | | frozen constants from `core/markup.py` | YES |
| `markupDistribution[].count` | `number` | bucket membership, lower bound inclusive, upper exclusive | YES |
| `topDestinations[].wallet` | `WalletAddress` | current holder | YES |
| `topDestinations[].ticketCount` | `number` | tickets currently held for this event | YES |
| `topDestinations[].region` | `string \| null` | **always `null`**: no wallet has volunteered a region (§5.4) | STUB: null |
| `topDestinations[].acquiredOnSecondary` | `boolean` | holder ≠ original issuee | YES |
| `topDestinations` cap | | 12 rows, sorted by ticket count descending then wallet ascending for a deterministic tiebreak | YES |

### 4.7 `Page<T>` and the query types

| Field | TS type | Rule | Can serve |
|---|---|---|---|
| `items` | `T[]` | the window | YES |
| `nextCursor` | `string \| null` | offset + limit when more remain, else `null` | YES |
| `EventQuery.status/city/q/cursor/limit` | | see §3 | YES |
| `TicketQuery.eventId/ownerWallet/status/cursor/limit` | | see §3 | YES |

## 5. What the contract carries that the engine cannot populate

These are not omissions in the build. They are facts about this machine: no program is
deployed, no mint exists, no wallet has signed, no identity provider is connected, and
no media is owned.

### 5.1 Chain provenance: `mintAddress`, `signature`, `slot`

The product's data-collection claim is that every resale price and custody hop is a
ledger entry. On this machine there is no ledger entry, because there is no program.
So: `signature` and `slot` are `null` on every row (the contract's own instruction for
rows with no on-chain counterpart), and `mintAddress` is a shape-valid `FXTURE…`
placeholder that no cluster knows about. A judge who clicks an Explorer link gets a
404, which is why `dataSource.synthetic` is on the same payload.

**What makes this real:** deploy the hook, mint the tickets, read the trail from
`getSignaturesForAddress` / the program's own event log. `docs/ON-CHAIN-FOR-LAPTOP.md`.

### 5.2 Enforcement: `Ticket.transferRestricted`

The type's comment is explicit: this is whether the restriction is *actually enforced
on-chain for that mint right now*, not whether the event asks for it. Nothing is
deployed, so the honest value is `false` on every ticket, including tickets whose event
sets `requiresVerifiedWallet: true`. Returning `true` because the config says so would
be the single most misleading field in the payload.

### 5.3 Policy that cannot be enforced from here: `resalePriceCapBps`,
`requiresVerifiedWallet`, `canPurchase`, `canReceiveTransfer`

All four are carried. None is enforced by this backend, and none can be: an API cannot
prevent a transfer it is not asked about. The cap and the verified-wallet gate are
transfer-hook conditions, and the capability flags are advisory copies of a chain
state that does not exist yet. This is why the on-chain piece is not optional for the
submission's anti-fraud claim (§`docs/ON-CHAIN-FOR-LAPTOP.md`, "why on-chain").

### 5.4 Identity and geography: `WalletVerification.method`, `verifiedAt`, all regions,
`Organizer.verified`

No identity provider is connected, so `method` is only ever `"wallet_signature"` or
`null`; no wallet has volunteered a region, so every `region` is `null`; no organizer
has been vetted, so `verified` is `false`. Each of these is a `null`/`false` the type
already permits, rather than an invented value.

### 5.5 Media: `Event.imageUrl`

No image assets exist in this repository. Always `null`, which the type permits.

### 5.6 Anything about a real market

Events, tiers, tickets, prices and markups all come from
`fixtures/synthetic_store.json`, which is hand-authored and labelled synthetic in its
own `meta` block, in `fixtures/README.md`, and in every response's `dataSource`. It is
not `lib/mock` (that directory is never read, and `tests/test_boundaries.py` fails if
any module names it), it is not scraped, and it is not evidence for any claim in the
research programme.

## 6. What the engine needs that the contract does not carry

The programme's deliverable (§5 of `RESEARCH-PROGRAM.md`, `AGENTS.md`) is an engine that,
given a ticket, an event and a time-to-event, returns: realistic resale value, how that
value moves over the remaining horizon, the probability of transacting at a price, and
the primary price that maximises risk-adjusted expected value. **None of those four has
a type in `lib/types.ts` and none has an endpoint in `API_CONTRACT.md`.** The contract
is a read-only view of the *record*; the engine's output is a *forecast*.

The seam for it exists (`ticketpath/adapters/pricing_model_adapter.py`). Its request
carries `ticketId`, `eventId`, `tierId`, `faceValueLamports`, `asOf` and whatever
record the caller has; its response carries `expectedResaleLamports`,
`saleProbability`, `recommendedPrimaryLamports`, `horizonHours`, `modelVersion` and
`basis`. Today it returns `available: false, basis: "no_model_registered"` and no
number. There is no endpoint for it because inventing one would put a non-contract
route on the judge's path.

Beyond the forecast itself, the contract lacks the inputs the programme's models need:

| What the engine needs | Why | Present in the contract? |
|---|---|---|
| Listing events (ask price, list time, withdrawn/expired) | Sale-hazard estimation needs exposure: how long a ticket was offered, at what price, and whether it sold. A record of sales alone has no denominator. | **No.** Deliberately no listing endpoint (Ticketpath prices primary, it is not a resale marketplace), so the exposure denominator must come from the ledger's own transfer attempts or a separate collector. |
| Fee and settlement structure (platform fee bps, royalty bps, settlement lag) | The primary optimum is computed on net proceeds; with no cost structure the optimum is undefined. | **No.** No fee or settlement field anywhere in `types.ts`. |
| Primary-side sale velocity and sold-out time per tier | The primary price question is about rationing across the on-sale window, and needs when inventory cleared at what price. | **No.** Only `faceValueLamports`, `totalSupply`, `issuedCount` are carried; no timestamps and no price changes. |
| Within-tier seat quality (section, row, seat) | Price paths differ sharply within a tier; aggregating to the tier loses the strongest covariate the secondary record has. | **No.** A tier has a name and one face value. |
| Server-side `asOf` on record payloads | Temporal correctness: a forecast must be reproducible against the data known at its own timestamp. `/health` reports `now`; payloads do not carry it. | **No** on payloads (addition made on `/health` only). |
| `modelVersion` / attribution on any served value | Without it, a number cannot be traced to the model that produced it, which contradicts the evidence discipline. | **No.** |
| Wallet-level history beyond one ticket (`GET /api/wallets/:w/…` is verification only) | Repeat-reseller behaviour and holding duration are transaction-level features the ledger can produce, but no endpoint exposes a wallet's tickets or trails as an aggregate. `GET /api/tickets?ownerWallet=` gives current holdings only. | **Partial.** Current holdings only; no history by wallet. |
| Event-level cap *binding* evidence (sales at the cap, rationed demand) | Distinguishing a censored price record from a free one is the core identification problem (Phase 2B). | **No.** The cap is carried as policy with no record of whether it bound. |

Two of these are load-bearing for the submission's honesty: without a fee structure the
"optimal primary price" cannot be computed, and without listing exposure the sale
probability cannot be estimated. Both are recorded as `UNVALIDATED` in the programme's
records rather than filled with fixture numbers.

## 7. Additions and deviations, stated plainly

### 7.1 Port

`API_CONTRACT.md` says `NEXT_PUBLIC_API_BASE_URL=http://localhost:8787`. On this machine
8787 belongs to another process. The backend binds **8788**; the operator switches the
frontend with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8788`. Nothing in the frontend
tree was changed.

### 7.2 `dataSource` on every payload

Added top-level key: `{mode, synthetic, label, note}`. `mode` is `synthetic-fixture`,
`empty-store` or `in-memory-verification`. This is the field a judge reads to know what
they are looking at. TypeScript ignores it; no existing field changed shape.

### 7.3 Two narrative keys on two payloads

`resale-history` carries `custodyNote` (why `signature`/`slot` are null) and `analytics`
carries `analyticsNote` (how `avgMarkupBps` is computed). Same reasoning: a reader
should not have to infer why a field is empty.

### 7.4 Error bodies

`{message, status, code}`. The contract asks for `message` or `error`; `message` is
always present. `code` is additive and stable for tests: `not_found`, `no_route`,
`method_not_allowed`, `status_invalid`, `limit_invalid`,
`cursor_invalid`, `wallet_malformed`, `nonce_unknown`, `nonce_expired`,
`nonce_wallet_mismatch`, `signature_invalid`, `signature_malformed`, `body_invalid`.

### 7.5 Cursor

Offset, not a stable keyset cursor: rows inserted or removed mid-pagination can skip or
repeat an item. Documented rather than hidden. Fine for the fixture store, must change
before a real ledger is paginated hot.

### 7.6 Case-insensitivity on `city`

Exact equality would fail on `toronto`; case-insensitive equality is used. Not specified
either way in the contract.

### 7.7 `markupBps` on the wire is computed, never stored

If a future ledger carries its own markup, the server's computation must win, or two
sources of truth will disagree on a multi-tier event. Recorded here so the next
implementer does not "optimise" by trusting the ledger field.

### 7.8 In-memory verification state

Nonces and verified wallets are process memory. A restart forgets them and the
`dataSource` note says so. A multi-worker deployment would need shared state before
this endpoint could be trusted.

## 8. Acceptance test map

`python3 -m unittest discover -s tests` (100 tests). The contract-facing subset:

| Contract area | Test module |
|---|---|
| Event list, filters, sorting, pagination, 404 | `tests/test_http_contract.py::TestEvents` |
| Ticket list, current-owner filter, id-or-mint detail, 404 | `TestTickets` |
| Resale history: every stat, entry order, per-ticket-face markup | `tests/test_resale_history.py` + `TestTickets` |
| Analytics: totals, per-sale markup, day buckets, six buckets, destinations | `tests/test_event_analytics.py` + `TestAnalytics` |
| Wallet verification: unknown wallet, challenge, signature, replay, expiry, wrong key | `tests/test_wallet_verification_flow.py` |
| Frozen verification message | `tests/test_verification_message.py` |
| Ed25519 against RFC 8032 | `tests/test_ed25519.py` |
| Base58 against the frontend's own encoder | `tests/test_base58.py` |
| Store integrity and refusals (unlabelled store, owner/trail mismatch, priced transfer) | `tests/test_ledger_adapter.py` |
| No network outside the server, no third-party imports, no `lib/mock`, port 8787 refused, model seam refuses | `tests/test_boundaries.py` |
| Health: version, data-source mode, no claimed deployment, no claimed model | `TestHealth` |

## 9. Decisions the operator has to make

1. **The data.** Everything numeric is fixture. Before this is shown as a product, either
   the program is deployed and the ledger is real, or the submission says plainly that
   the engine is demonstrated on synthetic data. There is no third option that is honest.
2. **The forecast has no home in the contract.** Adding `/api/events/:id/price-guidance`
   (or similar) is a frontend-contract change, so it is not made here. The seam is
   ready; the wire is not.
3. **Cap enforcement is on-chain or it is marketing.** `resalePriceCapBps` in the
   payload currently reads as a policy claim, not an enforced fact. The transfer-hook
   design in `docs/ON-CHAIN-FOR-LAPTOP.md` is what turns the claim into a guarantee.

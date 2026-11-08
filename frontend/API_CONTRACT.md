# API contract

The frontend reads data through exactly one module, [`lib/api.ts`](lib/api.ts).
Every endpoint below maps to one exported function there. Implement these and
the frontend switches from fixtures to live data by setting one env var —
no component changes.

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8787
```

Unset, the app serves the bundled fixtures in `lib/mock/`. The fixtures are the
reference payloads: if your response deserialises into the TypeScript types in
[`lib/types.ts`](lib/types.ts), the UI will render it.

## Conventions

- **Money is always an integer count of lamports.** Never a float, never a
  formatted string, never SOL. 1 SOL = 1_000_000_000 lamports.
- **Markup is basis points over face value.** `2500` = +25%. Signed; a
  below-face sale is negative.
- **Timestamps are ISO-8601 UTC strings** (`2026-10-18T14:02:00.000Z`).
- **Collections return a cursor envelope**: `{ items: T[], nextCursor: string | null }`.
- **Errors return a JSON body** with `message` or `error`; the client surfaces
  that string. 404 on a detail route renders the not-found page, so return 404
  (not 200-with-null) for a missing event or ticket.

## Endpoints

### `GET /api/events`
→ `Page<Event>`

Query: `status`, `city`, `q` (free-text over name + venue), `cursor`, `limit`.
Sorted by `startsAt` ascending.

### `GET /api/events/:idOrSlug`
→ `Event` · 404 if absent

Accepts either the opaque id or the URL slug — the frontend routes on slug.

### `GET /api/tickets`
→ `Page<Ticket>`

Query: `eventId`, `ownerWallet`, `status`, `cursor`, `limit`.
`ownerWallet` drives the "My tickets" page and must filter on *current*
on-chain owner, not the original issuee.

### `GET /api/tickets/:ticketId`
→ `Ticket` · 404 if absent

Also accepts a mint address in place of the ticket id.

### `GET /api/tickets/:ticketId/resale-history`
→ `ResaleHistory`

The core endpoint. Returns the full ledger for one ticket plus computed stats:

```jsonc
{
  "ticketId": "tkt_00017",
  "faceValueLamports": 1600000000,
  "entries": [ /* LedgerEntry[], chronological, OLDEST FIRST */ ],
  "stats": {
    "saleCount": 2,            // priced transfers only
    "transferCount": 3,        // sale + transfer, excludes issue/redeem
    "avgMarkupBps": 3650,      // mean over sales; null when no sales
    "peakPriceLamports": 2650000000,
    "lastPriceLamports": 1710000000,
    "totalVolumeLamports": 4360000000,
    "uniqueWallets": 5         // distinct wallets across the whole trail
  }
}
```

`entries` must include **every** `LedgerEntryKind`, not just priced ones —
`issue` and `transfer` rows are what make the custody trail complete, which is
the product's data-collection goal. `priceLamports` and `markupBps` are `null`
for unpriced moves.

### `GET /api/wallets/:wallet/verification`
→ `WalletVerification`

Unknown wallets return `verified: false` with HTTP 200, not 404 — any wallet
may connect.

### `POST /api/wallets/:wallet/verification/challenge`
→ `{ nonce: string, expiresAt: string }`

Issues a single-use nonce. The frontend has the wallet sign the exact string
produced by `verificationMessage()` in [`lib/solana.ts`](lib/solana.ts):

```
Verify wallet ownership for ticket issuance.

Wallet: <base58 pubkey>
Nonce: <nonce>
Cluster: devnet
```

**The backend must rebuild this byte-for-byte** (UTF-8, `\n` joins, no trailing
newline) to verify the signature. Changing the format invalidates in-flight
nonces, so treat it as frozen.

### `POST /api/wallets/:wallet/verification`
Body: `{ nonce, signature }` — signature is base58 of the 64-byte detached
Ed25519 signature.
→ `WalletVerification` on success; 400 with a `message` on a bad or expired
nonce.

Verify with `nacl.sign.detached.verify(messageBytes, sigBytes, pubkeyBytes)`.

### `GET /api/events/:eventId/analytics`
→ `EventAnalytics`

Organizer roll-up. `priceSeries` is **day-bucketed average sale price**
(`date` is `YYYY-MM-DD`, bucketed in **UTC**), ascending. Each point also
carries `avgMarkupBps`: the mean markup of that day's sales, where every sale
is measured against **its own ticket's tier face value**.

> Do not derive `avgMarkupBps` from `avgPriceLamports` and
> `faceValueLamports`. `faceValueLamports` is the *lowest* tier's face, so on a
> multi-tier event that calculation overstates markup badly (a 1.1 SOL
> orchestra seat measured against a 0.45 SOL balcony face reads as +164%
> instead of +8%). Send `null` when a day has no priced sales. `markupDistribution` must return all six
buckets in order, including zero-count ones, with these exact bounds in bps:

| label | fromBps | toBps |
|---|---|---|
| At or below face | -10000 | 1 |
| 0–25% | 1 | 2500 |
| 25–50% | 2500 | 5000 |
| 50–100% | 5000 | 10000 |
| 100–200% | 10000 | 20000 |
| Over 200% | 20000 | null |

`topDestinations` is the "where did tickets end up" table: current holders by
ticket count, descending, capped at ~12 rows. `acquiredOnSecondary` is true
when the holder is not the original issuee. `region` is nullable — only
populate it when the wallet volunteered one.

## Notes for the Solana side

- `Ticket.mintAddress` is what the explorer links resolve against; it must be a
  real mint on the cluster named by `NEXT_PUBLIC_SOLANA_CLUSTER`.
- `LedgerEntry.signature` deep-links to Solana Explorer. Return `null` rather
  than a placeholder when a row has no on-chain counterpart, or the link 404s.
- `transferRestricted` should reflect whether the restriction is *actually*
  enforced on-chain for that mint right now, not whether the event config asks
  for it.

# SeatPass — front end

The web front end for SeatPass: wallet-bound event tickets on Solana where every
resale price and every custody hop is recorded against the ticket itself.

Next.js 15 App Router, React 19, TypeScript 5.9 (strict), Tailwind 4. One design
system in `app/theme.css`, one data seam in `lib/api.ts`, no component that
fetches.

## Run it

```bash
npm install
npm run dev                # http://localhost:3000
```

It runs standalone. With `NEXT_PUBLIC_API_BASE_URL` unset it serves the bundled
fixtures in `lib/mock/`; set it to the backend's origin and the same screens read
live data with no component changes.

```bash
npm run dev                                    # fixtures
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788 npm run dev   # live
```

```bash
npm run typecheck          # tsc --noEmit
npm run lint               # eslint .
npm test                   # node --test on lib/*.test.ts
npm run build              # production build
```

**Do not run `next build` in this checkout while another process is serving its
`.next`.** It replaces the bundle under that server. `tools/build-copy.sh` builds
and serves a throwaway copy instead.

## Routes

| Route | What it is |
|---|---|
| `/` | landing: the hero ticket, the on-chain strip, the cap, the proof band |
| `/events` | browse, with status, city, text and cursor paging in the URL |
| `/events/[slug]` | detail: tiers, enforced cap, series, six buckets, destinations |
| `/events/[slug]/checkout` | face, cap and verification; payment is Unavailable |
| `/tickets/[ticketId]` | identity, status, custody trail, price history |
| `/my-tickets` | the holdings of the connected wallet |
| `/door` | door-side read of one ticket: serial, status, pass or block |
| `/organizer` | volume, sales, median, markup, holders, destinations |
| `/organizer/events/new` | the create form; submission is Unavailable |
| `/resale`, `/resale/list/[ticketId]` | no listings endpoint; the cap check for one ticket |
| `/account`, `/verify` | wallet signature verification |
| `/pricing` | the backend's health: data source, chain, model, contract counts |
| `/rules` | the cap predicate, immutability, and the real enforcement status |

## The shape of the code

```
app/            routes; server components read the API, clients exist only for the wallet
components/     twelve components plus ui.tsx primitives and useMeasure; none fetch
lib/api.ts      the only data seam, and the only place that knows mock from live
lib/http.ts     transport: ApiError, query building, cursor paging, timeout
lib/types.ts    the wire contract
lib/cap.ts      the resale cap as integer arithmetic
lib/format.ts   lamports, markup, addresses, dates; everything else sees integers
lib/demo.ts     the two proof figures with no backend source, and nothing else
app/theme.css   every colour, radius, shadow and font stack in the product
tools/          build-copy, greps, contrast, and the headless render check
```

## What this build does not do

Seven capabilities are false in `lib/capabilities.ts` and each renders one panel
naming what is missing and which endpoint would fill it: purchase, listings,
door code, event creation, transfers, refunds, auth. There is no checkout, no
marketplace, no QR or offline path, no account and no admin screen. Nothing in
this app shows a fake success.

`COVERAGE.md` maps all 43 inventory rows to a screen and a state. `NOTES.md`
records the copy that ships as written and still needs a second pass, plus every
assumption and deviation. `VERIFY.md` holds the commands and their numbers.
`DECISIONS.md` holds the build-level calls.

# 14-frontend-attach-explore — current state, what a judge still cannot see, and the three ways to fix it

**Written:** 2026-11-07T17:40Z.
**Phase:** 1 of 3 (explore). **Read only.**
**Scope:** `/home/friend/ticketing-frontend` (his, never written, :3000 never touched),
`/home/friend/ticketpath-demo` (our copy, :3001, read only), our backend on :8788 (read only),
`/home/friend/ticketPricing` (records read, nothing written but this file).
**Not touched:** `:3000` (pid 81447, answered 200 before and after), `:8787` (identified from
`ps` as an unrelated node service, never probed), and the three unrelated tooling trees under his home
directory.
**Not done:** no commit, no restart, no write outside this file, no subagent.

---

## 0. The answer in one paragraph

The copy at `~/ticketpath-demo` on :3001 is already fully attached: it reads our backend on every
data route, it prints our `dataSource` label above the numbers, and the four false enforcement
sentences and the death-on-wiring mock banner are all gone from it. `:3000` is not attached at all
and still says "Mock data", "enforced at transfer time" and "Every transfer is recorded on-chain".
The address-truncation tell is fixed in the data (191 addresses, 191 distinct short forms, zero
collisions). What is still missing on both trees is the thing the whole project exists to produce:
**there is no screen and no JSON route for the price recommendation.** All nine contract routes
were probed and none carries it; the recommendation exists as HTML only, at `:8788/?event=...`.
The cheapest honest fix is not a new endpoint and not a native page: proxy the console's own HTML
through the Next app and frame it at `/pricing` inside the app shell, about three hours of work
across four disjoint files, none of it in his tree.

---

## 1. What is attached today, measured

### 1.1 `:3000` is not pointed at anything

```
ss -ltnp | grep 3000        -> 0.0.0.0:3000  next-server (v15.5.29), pid 81447
ps -o cmd -p 81434          -> npm exec next start -H 0.0.0.0 -p 3000
tr '\0' '\n' < /proc/81447/environ | grep -i api_base   -> (nothing)
ls /home/friend/ticketing-frontend/.env*                -> .env.example only
```

`lib/api.ts:35-37` is the only seam:

```ts
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";
export const isMockMode = BASE_URL === "";
```

With the variable unset, `isMockMode` is `true`, every call lands in the `lib/mock` branch, and the
banner at `components/AppShell.tsx:61-68` renders. Served HTML agrees:

| Check on `curl -s http://127.0.0.1:3000/...` | Result |
|---|---|
| `Mock data` banner | present on all four routes (`/`, `/events/...`, `/tickets/...`, `/organizer`) |
| `riverside-comedy-night` (a `lib/mock` slug) | 1 |
| any `SYN...` fixture event slug from our backend | 0 |
| `Every transfer is recorded on-chain` | 1 on every route (static footer) |
| `enforced at transfer time` on `/events/midnight-static-tour` | 2 |
| `before a transfer will succeed` on the same page | 2 |
| `Enforced on-chain` on `/tickets/tkt_00001` | 2 |
| `on-chain transfer record` on `/organizer` | 2 |

`lib/mock/events.json` holds 6 events and `lib/mock/tickets.json` 128 tickets. That is what a judge
clicking :3000 today is looking at, openly labelled as mock.

### 1.2 `:3001` is pointed at our backend, and the wiring lives only in the process env

```
ps -o cmd -p 233147         -> node ./node_modules/.bin/next dev -p 3001
tr '\0' '\n' < /proc/233166/environ | grep -i 'api_base\|pwd'
    NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788
    PWD=/home/friend/ticketpath-demo
ls -a /home/friend/ticketpath-demo | grep env   -> .env.example only
```

**Operational gotcha, worth writing down:** the wiring is a shell export, not a file. Restart :3001
with no `.env.local` in that tree and it silently returns to `lib/mock` with the mock banner. Also,
because `NEXT_PUBLIC_*` is inlined at compile time, a production `:3000` needs a rebuild *and* a
restart, not a reload (`records/FRONTEND-INTEGRATION.md` §5.1, `NIGHT-QUEUE.md:72`).

It is a `next dev` server, so new files under `app/` hot-reload. That matters for §4: the implement
phase needs no restart of :3001 and therefore no touching of :3000.

### 1.3 Which pages return real backend numbers

Backend is `python3 -m ticketpath.server --port 8788`, started 17:10, serving 8 events, 76 tickets,
191 distinct addresses. Every count below was checked against the JSON on the same instant.

| Route on :3001 | Status | Rendered value | Backend value it must equal |
|---|---|---|---|
| `/` | 200, 118,917 B | 8 cards, SYN slugs present, mock slugs absent | `GET /api/events?limit=100` -> 8 |
| `/events/synthetic-hall-cap-not-binding` | 200, 176,424 B | `Face value from 1 SOL`, `Tickets issued 14 of 200 · 7%`, `Resold at least once 64%`, `14 resales recorded`, `Average markup +5.8%` | `analytics: saleCount 14, avgMarkupBps 575, uniqueHolders 13` |
| `/tickets/tkt_syn_0001` | 200, 130,105 B | custody trail, pills `SYNu…1fCH`, `SYN8…1hYp`, `SYNA…1juM`, `Resold 1.18 SOL +18% vs face`, `Total resale volume 2.12 SOL` | `GET /api/tickets/tkt_syn_0001/resale-history` |
| `/organizer?event=evt_syn_01` | 200, 154,296 B | `Median resale price 2.54 SOL`, `14 sales`, `Average markup +5.8%`, `cap is +25%` | `analytics: median 2537500000, saleCount 14` |
| `/my-tickets` | 200, 39,970 B | `Connect a wallet to see your tickets` | client-side fetch, no wallet, nothing rendered |
| `/verify` | 200, 40,799 B | connect prompt | same |

All 8 event pages return 200. All 7 events that have tickets return a 200 ticket page.
`fixture-studio-draft` has `issuedCount 0`, so it has no ticket page, and both its event page and
its organizer page render designed empty states (`No resale activity recorded yet.`,
`No completed resales yet.`, `Average markup —`) rather than NaN or an error page. I checked the one
`NaN` that appeared in one page's HTML: it is the substring inside the mint
`SYNP618SPFjrAhq5oGJGoDPNaNbB1HqNTF9jzGh7YXn`, not a computed value.

### 1.4 The copy is the honesty patch on an otherwise identical app

`diff -rq` excluding `node_modules`, `.next`, `*.tsbuildinfo`: 9 modified files, 1 new file.

| File | Changed lines |
|---|---|
| `app/page.tsx` | 6 |
| `components/AppShell.tsx` | 5 |
| `components/EventCard.tsx` | 4 |
| `lib/types.ts` | 15 |
| `app/events/[eventId]/page.tsx` | 8 |
| `app/tickets/[ticketId]/page.tsx` | 11 |
| `app/organizer/page.tsx` | 8 |
| `app/my-tickets/MyTicketsClient.tsx` | 6 |
| `app/verify/VerifyClient.tsx` | 6 |
| `components/SyntheticNotice.tsx` | new, 17 |

69 changed lines plus 17 new, which is the `+68 / -16` the patch record claims
(`records/FRONTEND-HONESTY-PATCH.md` §7).

Byte identical, and this is the part that matters for §3: `lib/api.ts`
(md5 `a3a8ed5fd3cebf0b161a41ec84425df1` on both sides), `lib/solana.ts`, `lib/viz.ts`,
`lib/format.ts`, `lib/mock/*`, `app/layout.tsx`, `next.config.ts`, `package.json`, and all eleven
other components. **The copy carries no wire-contract change.** The `dataSource` block travels
because `request<T>` returns the parsed JSON unchanged (`lib/api.ts:53-70`) and `Page<T>` gained an
optional field (`lib/types.ts:208-213`), so TypeScript admits a key the backend was already sending.

---

## 2. What is still broken or missing for a judge clicking the frontend

Each line is measured on the tree named in the "state" column.

| # | Item | State in the copy (:3001) | State in his tree (:3000) |
|---|---|---|---|
| 1 | Synthetic banner keyed to `isMockMode`, destroyed by wiring | **Fixed.** `isMockMode` is false, so `Mock data` is 0 on all 7 routes; `SYNTHETIC FIXTURE DATA` is 1 to 4 occurrences on `/`, `/organizer`, `/events/*`, `/tickets/*`, 0 on `/my-tickets` and `/verify` because those print no numbers without a wallet | Banner present, and it is the only label |
| 2 | "enforced at transfer time" | **Fixed.** 0 across all 7 routes | Present, 2 on a capped event page |
| 3 | "Every transfer is recorded on-chain" | **Fixed.** Footer now says "recorded in a custody ledger ... on-chain recording starts when the ticket program is deployed" | Present, 1 on every route, static, unfixable from the payload |
| 4 | Truncated addresses indistinguishable | **Fixed in the data, not the frontend.** `shortAddress` keeps first 4 and last 4 (`lib/format.ts:48-52`). Over the live payload: 191 distinct addresses, 191 distinct short forms, 0 collisions. On screen: `SYNu…1fCH`, `SYN8…1hYp`, `SYNA…1juM` | Broken: 13 fixture addresses all render `FXTU…1111` |
| 5 | 32 of 37 numbers need a label | **Half fixed.** The page-level notice now sits above the numbers on the 5 routes that print them. Still absent: a label *beside* any individual figure | Nothing |
| 6 | **No screen or endpoint for the price recommendation** | **Still missing.** `grep -i "recommend\|pricing\|guidance\|primary price"` over `app/`, `components/`, `lib/` returns nothing; no nav item; no link to :8788 anywhere in the tree | Same |
| 7 | Chart y-axis starts above zero with no note | Still there: `components/PriceHistoryChart.tsx:66` (`lo = rawMin > rawMax*0.5 ? rawMin - ... : 0`) | Same |
| 8 | Mint address is a live explorer link that 404s | Labelled ("fixture placeholder: no account exists on any cluster") but still linked | `On-chain` card, unlabelled |
| 9 | Five "once the program is deployed" clauses are hardcoded, not payload-driven | Still there, documented in `records/FRONTEND-HONESTY-PATCH.md` §5. `dataSource.note` is received and dropped; `SyntheticNotice` prints `label` only | N/A |
| 10 | `/my-tickets` and `/verify` are dead ends without a browser wallet | Still there: no demo-wallet fallback in live mode (`MyTicketsClient.tsx:22` requires `isMockMode`) | Mock demo wallet hides it |

Item 6 is the whole question, so here is the measurement that settles it. Every JSON route our
backend serves, grepped for the words a recommendation would carry:

```
/health                                    1177 B   hits: ['modelVersion']
/api/events?limit=100                     10161 B   hits: []
/api/events/evt_syn_01                     1653 B   hits: []
/api/events/evt_syn_01/analytics           3741 B   hits: []
/api/tickets?limit=100                    37314 B   hits: []
/api/tickets/tkt_syn_0001                   785 B   hits: []
/api/tickets/tkt_syn_0001/resale-history   1844 B   hits: []
/api/wallets/<wallet>/verification          445 B   hits: []
```

Needles: `recommend`, `expectedResale`, `saleProbability`, `horizonHours`, `modelVersion`, `band`,
`optimum`, `asOf`. `/health` carries model *metadata* (`kind: rule-based-bounded-estimator`,
`fitted: false`, `modelVersion`, and a `chain.programDeployed: false` block) but no number.

The number exists in exactly one place:

```
curl -s 'http://127.0.0.1:8788/?event=evt_syn_06' | grep -c 'Recommended primary price'  -> 1
    [UNVALIDATED] Recommended primary price: 0.53 SOL per ticket.
    [UNVALIDATED] Band 0.38 – 0.625 SOL.
    [FIXTURE] basis: tier_marks  ... has not been checked against what this event sold for.
```

And two of the eight events refuse to give one, which is a feature the frontend page must present
as content rather than as breakage:

```
curl -s 'http://127.0.0.1:8788/?event=evt_syn_08'
    [REFUSED] No resale has been recorded on this event, so we will not state a primary price.
    [UNVALIDATED] prior band around face: 0.93 SOL
```

The console route is at `ticketpath/server.py:46` (`CONSOLE_PATHS = ("/", "/index.html")`) and is
deliberately outside `ROUTES`, so it does not count as a contract endpoint
(`ticketpath/server.py:39-46`). That is why a recommendation has no JSON home: nobody has built
one, and the file says so in `records/CONTRACT-MAP.md` §6.

---

## 3. How the frontend could show a recommendation, three ways compared

Facts that constrain the choice:

- The console is one self-contained HTML string: 13,452 bytes for `evt_syn_06`, 14,360 with `sim=1`,
  3,106 for a rendered 404, no external asset, no CDN, no framework, one inline style block, and its
  only interaction is a `GET` form (`ticketpath/console/page.py:1-14`).
- It sends no `X-Frame-Options` and no CSP (measured response headers), so it frames.
- Its own layout is `main { max-width: 62rem }`, inside the app's `max-w-6xl` (72rem) main element,
  so it fits the shell without scroll hacking.
- Every number on it already carries its badge: `[FIXTURE]`, `[UNVALIDATED]`, `[EXACT]`,
  `[REFUSED]`, `[DESIGN]`, `[DEVNET]`. A native re-render has to rebuild all five or it loses them.
- `:8788` binds `127.0.0.1` only (measured with `ss`); `:3001` binds `*:3001`. A judge on another
  machine cannot reach the console directly.

### Option A: a nav link straight to `:8788`

| | |
|---|---|
| Effort | 30 to 45 min (one string in `components/AppShell.tsx:9-14`, one `target="_blank"`) |
| Backend change | none |
| Wire-contract change | none |
| Risk to :3000 | none |
| Judge sees | the full console, all badges, every refusal, but in a bare browser tab with a second port in the URL bar and none of the app's chrome |

### Option B: proxy the console's HTML through the Next app, frame it at `/pricing`

Two new files and one nav string. `app/api/console/route.ts` takes a whitelisted set of query
parameters (`event`, `tier`, `asOf`, `capBps`, `feeLamports`, `tau`, `sim`, `mode`), fetches
`http://127.0.0.1:8788/?<those>`, and returns the body as `text/html` with the backend's status.
`app/pricing/page.tsx` prints a preamble in the app's voice, frames `/api/console?...`, and links
out to the canonical backend URL.

| | |
|---|---|
| Effort | 1.5 to 2 h (proxy 45 min, page and nav 45 min, error path 30 min) |
| Backend change | none. `:8788` is read with `GET` only |
| Wire-contract change | none. `lib/api.ts` and `lib/types.ts` are not touched |
| Risk to :3000 | none. Everything lands in `~/ticketpath-demo`, which is a dev server |
| Judge sees | the recommendation inside the product, every honesty badge intact because it is the console's own HTML, and it works for a remote judge because Next does the fetch server side, which also removes the need to rebind `:8788` |

### Option C: a new JSON contract route plus a native page

| | |
|---|---|
| Effort | 5 to 8 h (route 1 h, TypeScript renderer for five badge families and about forty numbers 4 to 6 h, tests 1 h) |
| Backend change | new route in `ticketpath/server.py:117-134` |
| Wire-contract change | it would be an addition, but not a free one: `implemented_route_count()` goes 10 to 11 and `implemented_contract_route_count()` goes 9 to 10 against `CONTRACT_ENDPOINT_COUNT = 9`, so `/health`'s contract block becomes false and `tests/test_http_contract.py:98-102` and `tests/test_contract_conformance.py:925` have to be edited to match. Editing a test to fit a new route is allowed but it is the kind of edit that hides a lie if done quietly |
| Risk to :3000 | none, but the backend must be restarted for the route to exist |
| Judge sees | a native page, and whatever fraction of the console's labelling was rebuilt in time. Every label dropped in the rebuild makes the screen *less* honest for the hours spent |

### Option D: content negotiation on the existing console route

`GET /?format=json` returns the same payload dict that `console_index` already holds
(`ticketpath/server.py:59-78`), with no new `ROUTES` entry, so no count moves. About 1 h plus a
backend restart. On its own it produces a JSON surface with no renderer, so it is only worth doing
as the input to Option C, or as a CLI-friendly extra.

### Comparison

| | A link | B proxy + frame | C new route + native page |
|---|---|---|---|
| Hours | 0.5 to 0.75 | 1.5 to 2 | 5 to 8 |
| Backend untouched | yes | yes | no |
| Test churn | none | none | 2 pinned assertions |
| Honesty labels inherited | yes | yes | only what is rebuilt |
| Works for a remote judge | no | **yes** | yes |
| `:3000` touched | no | no | no |
| Looks like one product | no | **mostly** | yes |
| Needs a backend restart | no | no | yes |

**Recommendation: Option B, with Option A's link inside the page.** It is the only option where the
honesty labelling is inherited from the thing that already computes it, it needs no backend route
and no backend restart, and the frontend it touches is ours.

One wrinkle to decide rather than discover: the canonical URL the console prints is built from its
own `Host` header (`ticketpath/server.py:96-114` and `:248`), so through the proxy it still reads
`http://127.0.0.1:8788/?...`. That is honest (it names the real source) and clickable on this box,
and a plain string for a remote judge. Rewriting it would mean rewriting HTML, which is the kind of
fragile thing that breaks the day the console changes a byte. Leave it and say so on the page.

---

## 4. The implement phase: four work packages, disjoint files, curl-verified

Availability measured on this box: `node v24.22.2`, `npm 11.19.1`, `python3 3.12.3`,
`npx tsc --noEmit` in the copy exits 0 in **1.3 s**, `python3 -m unittest discover -s tests` runs
**453 tests in 18.0 s, OK**. There is **no browser binary** (`chromium`, `google-chrome`,
`firefox` all absent; no `~/.cache/ms-playwright`, no `~/.cache/puppeteer`) and `pytest` is not
installed, so tests are stdlib `unittest`.

**How rendering is verified without a browser.** Every route that matters is server-rendered, so
`curl` sees the final HTML a browser would receive. That is exactly how the honesty patch was
verified before (`records/FRONTEND-HONESTY-PATCH.md` §4). Two limits, stated up front: the frame's
*paint* and layout cannot be checked this way, and the two client components (`/my-tickets`,
`/verify`) can only be checked as far as their unauthenticated shell. Neither is on the
recommendation path.

| WP | Files (all under `~/ticketpath-demo` unless named otherwise) | Work | Acceptance, runnable here |
|---|---|---|---|
| **WP1** console proxy | `app/api/console/route.ts` (new, ~60 lines) | whitelist 8 query params, server-side `fetch` to `CONSOLE_ORIGIN` (default `http://127.0.0.1:8788`), forward status, `content-type: text/html; charset=utf-8`, `cache: "no-store"`, `export const dynamic = "force-dynamic"`; on a dead backend return 200 and one plain sentence that names the failure | `npx tsc --noEmit` exit 0. `curl -s -o /tmp/c.html -w '%{http_code}' 'http://127.0.0.1:3001/api/console?event=evt_syn_06'` = 200; `grep -c 'Recommended primary price' /tmp/c.html` = 1; `grep -c '\[FIXTURE\]' /tmp/c.html` >= 10; `grep -o 'content-type[^;]*'` is html. `?event=nope` = 404 and still renders the console error page. Error path: second dev instance on `:3102` with `CONSOLE_ORIGIN=http://127.0.0.1:1`, expect 200 and the sentence, then kill it. Reject any query key not on the whitelist and never accept a caller-supplied path (SSRF) |
| **WP2** pricing page and nav | `app/pricing/page.tsx` (new), `components/AppShell.tsx` (NAV array, lines 9-14) | preamble in the app's voice (what the number is, that it is unvalidated, that some events refuse), `<iframe title="Ticketpath pricing console" src="/api/console?<params>">`, and a link out to the canonical `:8788` URL | `curl -s http://127.0.0.1:3001/pricing` = 200, contains `src="/api/console`, contains the preamble sentence, contains `127.0.0.1:8788`; `curl -s http://127.0.0.1:3001/ \| grep -c '>Pricing<'` = 1 (nav item present in the shell on every route) |
| **WP3** reach it from the screen a judge lands on | `app/events/[eventId]/page.tsx` | one card between the stat row and the chart: "Primary price recommendation", one sentence, `href="/pricing?event=<id>&tier=<tierId>"` | `curl -s http://127.0.0.1:3001/events/synthetic-hall-cap-not-binding \| grep -c 'href="/pricing?event=evt_syn_01'` = 1; same for an event that caps at 1500 bps and for the no-resale event, which must reach a page that refuses rather than an empty frame |
| **WP4** the checker | `tools/check_frontend_attach.py` (new, in this repo) | assert over :3001: every route 200; `SYNTHETIC FIXTURE DATA` present on the four data routes; the four false strings absent everywhere; `/pricing` carries at least one `[UNVALIDATED]` and one `[REFUSED]`; the rendered average markup equals `round(avgMarkupBps/100, 1)` from the API; address pills on the ticket page are pairwise distinct; exit non-zero on any failure and print the command that would have fixed it | it passes against :3001, and **it fails when pointed at :3000** (`--base http://127.0.0.1:3000`), which is the positive control: a check that cannot fail is not a check |
| **WP5** stretch, only if the deadline is comfortable | `ticketpath/server.py`, `tests/test_console_route.py` | `?format=json` on the console route, no new `ROUTES` entry, so `/health`'s counts do not move | `python3 -m unittest discover -s tests` still OK at 453+; `curl -s 'http://127.0.0.1:8788/?format=json' \| python3 -c 'import json,sys; d=json.load(sys.stdin); print(sorted(d)[:5])'`; and the HTML path unchanged: `curl -s 'http://127.0.0.1:8788/' \| grep -c 'Recommended primary price'` = 1 |

Disjointness: WP1 touches one new file under `app/api/`; WP2 touches a new page plus the NAV array;
WP3 touches the event page only; WP4 and WP5 touch this repo only. No two packages write the same
file, so they can be built in parallel against three agreed URLs (`/api/console?<params>`,
`/pricing?event=&tier=`, `:8788/?<params>`).

Sequencing that cannot be parallelised: WP2's iframe URL is WP1's URL, and WP3's link is WP2's page.
Both are strings, so agreeing them first is enough to write all three at once.

Estimated wall clock for WP1 to WP4: **about 3 hours of build plus 1 hour of adversarial review**,
then the acceptance run. WP5 is another 1.5 hours and costs a backend restart.

### Decisions for the operator

Anything below marked **his** needs his explicit yes.

| # | Decision | Why it is his |
|---|---|---|
| D1 | Apply `docs/frontend-honesty.patch` to `/home/friend/ticketing-frontend` | **his.** It is his tree. The patch is proven (`git apply --check` on a clean copy, then byte-for-byte reproduction) and needs no restart by itself, but see D2 |
| D2 | Set `NEXT_PUBLIC_API_BASE_URL` on :3000 and restart it | **his.** `NEXT_PUBLIC_*` is inlined at build time, so a reload does nothing. Consequence, measured: the demo moves from 6 mock events and 128 tickets with a mock banner to 8 synthetic events and 76 tickets with no banner |
| D3 | Which surface the judge is shown: `:3001` (copy, wired, honest, 8 events) or `:3000` (his, rich, 6 events, mock banner, four false sentences) | **his.** It decides whether D1 and D2 are worth doing at all, and it changes the demo script |
| D4 | Write `.env.local` into `~/ticketpath-demo` | ours to do, but it is a write, so it is named. Without it, any restart of :3001 silently reverts to mock mode (§1.2) |
| D5 | Restart the backend on :8788 | **his** in practice, because it is a running process on a shared port. Only needed for WP5 |
| D6 | Unlink the mint address from Solana Explorer, or leave the labelled 404 | a behaviour change on a page a judge will click. My read: leave it linked and keep the "fixture placeholder" subtitle, because an unlinked address looks like the app is hiding something and a labelled 404 is a teaching moment |
| D7 | Network posture if the judge is not on this box | `ss` shows `:8788` on `127.0.0.1` and `:3001` on `*`. WP1 makes the backend's bind irrelevant for the judge, but a remote demo still needs a firewall and a host decision from him |

---

## 5. Recommendation, sized against 15:00Z

It is 17:40Z. The deadline is about 21 hours away, which is a lot of time and not enough to invent
a second renderer for a console that already exists.

**Do WP1, WP2, WP3, WP4. Skip WP5 unless the four are done and reviewed by 22:00Z.**

- All of it lands in `~/ticketpath-demo`, a dev server, so nothing needs restarting and `:3000` is
  not in the blast radius at any point.
- No backend route is added, no contract count moves, and no test is edited to accommodate a new
  feature. The 453-test suite stays a check on the backend rather than a thing we edited.
- The judge gets the one thing the app cannot currently show: a primary price, in the product, with
  `[UNVALIDATED]` in front of it and `[REFUSED]` where the record does not support one.
- What is left deliberately undone, and should be said out loud rather than hidden: per-figure
  labels (item 5), the chart's axis note (item 7), the mint link (D6), and the five hardcoded
  "once the program is deployed" clauses that only a deployed program can retire.

If D3 comes back as "show :3000", the order changes and nothing else does: apply the patch (D1),
set the env var (D2), restart once, then run WP4 against `:3000` as the acceptance gate. That path
takes his fifteen minutes plus our three hours, and it is the strongest demo because it is his app.

If D3 comes back as ":3001 only", then D1 and D2 wait for after the submission and WP1 to WP4 are
the whole of the remaining frontend work.

---

## 6. Limits of this document

- No browser on this box, so nothing here is a claim about what a screen *looks* like. Every claim
  is about bytes served, and each one names the command.
- I did not read the three unrelated tooling trees under his home directory. `:8787` was identified from
  `ps` alone and never probed. That matters because `API_CONTRACT.md` names
  `http://localhost:8787` as the example backend origin, and on this machine 8787 is not ours;
  `records/CONTRACT-MAP.md` §7.1 already records the same thing.
- `/my-tickets` and `/verify` in live mode are recorded as dead ends from reading the code and the
  served shell, not from connecting a wallet.
- The 0.53 SOL and 0.93 SOL figures quoted above are the console's own output over a synthetic
  fixture, and are quoted as evidence of *the route's shape*, not as a price.

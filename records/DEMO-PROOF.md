# DEMO-PROOF — the real frontend, on our backend, tonight

**Status:** working on the copy's port. Not yet on the live frontend's port, not yet showing a price.
**Written:** 2026-11-07T11:10Z, by the demo-integration session, from its own command output.
**Nothing in `../ticketing-frontend` was edited, restarted or killed** (the same process still
serving, verified after the fact). Nothing was installed. Nothing was pushed.

## 1. What is running now, on which port

| Thing | Where | Port | How to stop it (operator's call, not run by this session) |
|---|---|---|---|
| Backend `python3 -m ticketpath.server` | `<repository root>` | **8788** | `kill <the backend's pid>` (log `/tmp/ticketpath-backend.log`) |
| Frontend **copy** `next dev -p 3001` | `../ticketpath-demo` | **3001** | `kill <the copy's pid>` (log `/tmp/ticketpath-web.log`) |
| Live frontend, untouched | `../ticketing-frontend` | 3000 | not ours to touch |
| Somebody else's process | — | 8787 | not ours, not bound by us |

Backend startup: **58 ms** from `python3 -m ticketpath.server` to a 200 on `/health`, measured by
starting a throwaway instance on port 8799 and killing it (8799 released, 8788 untouched).
`/health` answers in 1.1 ms. Frontend copy: **Ready in 935 ms**; first page compile 3.5 s, every
page after that under 0.8 s.

## 2. Response codes, exactly

Backend `http://127.0.0.1:8788`:

| Endpoint | Code |
|---|---|
| `/health` | **200** |
| `/api/events?limit=3` | **200** |
| `/api/events/evt_fixture_1` (by id) | **200** |
| `/api/events/fixture-hall-session` (by slug) | **200** |
| `/api/events/nope` | **404** (the honest one) |
| `/api/tickets?limit=5` | **200** |
| `/api/tickets/tkt_fixture_0001` | **200** |
| `/api/tickets/tkt_fixture_0001/resale-history` | **200** |
| `/api/events/evt_fixture_1/analytics` | **200** |
| `OPTIONS /api/wallets/<wallet>/verification/challenge` (preflight, `Origin: http://localhost:3001`) | **204** with `access-control-allow-origin: *`, `-methods: GET, POST, OPTIONS`, `-headers: content-type` |

Frontend copy `http://127.0.0.1:3001`:

| URL | Code | Bytes |
|---|---|---|
| `/` | **200** | 65,651 |
| `/events/evt_fixture_1` | **200** | 117,536 |
| `/events/fixture-hall-session` (the link the list actually renders) | **200** | — |
| `/organizer` | **200** | 109,479 |
| `/tickets/tkt_fixture_0001` | **200** | 127,198 |
| `/my-tickets` | **200** | 39,853 |
| `/verify` | **200** | 40,647 |

The live frontend's home page re-checked at the end: **200**, still the same process, still mock mode.

Two things the scaffold will bite a reader on: event ids are `evt_fixture_1` / `evt_fixture_2`
(not `evt_fixture_0001`) — `evt_fixture_0001` is a 404 — and `docs/BACKEND.md`'s sample curl uses
`tkt_fixture_0001`, which is correct.

## 3. Which screens carried backend data — traced, not assumed

The backend logs every request (`server.py` `log_message`), so the frontend's fetches are visible
as lines in `/tmp/ticketpath-backend.log`. These are the ones the Next server made while I fetched
the pages, after my own curl probes in the same log:

```
"GET /api/events HTTP/1.1" 200
"GET /api/events/evt_fixture_1 HTTP/1.1" 200
"GET /api/tickets?eventId=evt_fixture_1&limit=25 HTTP/1.1" 200
"GET /api/events/evt_fixture_1/analytics HTTP/1.1" 200
"GET /api/events?limit=100 HTTP/1.1" 200
"GET /api/tickets/tkt_fixture_0001 HTTP/1.1" 200
"GET /api/tickets/tkt_fixture_0001/resale-history HTTP/1.1" 200   (x2)
"GET /api/events/fixture-hall-session HTTP/1.1" 200
```

And the numbers on the pages are those responses, digit for digit:

| Screen | What is on it | Where it came from |
|---|---|---|
| `/` event list | 2 events, "Synthetic Annex Showcase" / "Synthetic Hall Session", Fixture Hall · Toronto, "Issued 5%" / "3%", "From 0.5 SOL" / "1 SOL" | `GET /api/events` — backend store. **Backend data.** |
| `/events/evt_fixture_1` event detail | face from 1 SOL across 2 tiers, 4 issued of 150, "Resold at least once 75% · 4 resales recorded", "Average markup +5.6% cap +25%", 4 ticket rows with -10% / +5.0% / +2.5% / never-moved, price series 2–4 Nov | `GET /api/events/…` + `/api/tickets?eventId=…` + `/api/events/…/analytics`. **Backend data and backend arithmetic.** |
| `/organizer` resale analytics | "5.25 SOL across 4 sales", "Average markup +5.6%", "Median resale price 1.15 SOL", "75% · 4 distinct holders", markup histogram 1 / 2 / 1 / 0 / 0 / 0, destination wallets "3 of 4 acquired on the secondary market" | `/api/events/evt_fixture_1/analytics`: `totalVolumeLamports 5250000000`, `saleCount 4`, `avgMarkupBps 563`, `medianResalePriceLamports 1150000000`, `resoldShare 0.75`, `uniqueHolders 4`, `markupDistribution` counts `[1,2,1,0,0,0]`. **Backend data.** |
| `/tickets/tkt_fixture_0001` ticket detail | face 1 SOL, last sale 0.9 SOL −10%, peak 1.25 SOL +25%, "4 wallets held by", "3 transfers · 2 priced", custody trail of 4 ledger rows with dates and markups | `/api/tickets/tkt_fixture_0001` + `/resale-history`: `peakPriceLamports 1250000000`, `lastPriceLamports 900000000`, `totalVolumeLamports 2150000000`, 4 entries. **Backend data.** |
| `/my-tickets` | "Connect a wallet to see your tickets" only. No ticket rendered. | No backend call made — `/tmp/ticketpath-backend.log` shows none for this page. Wallet-gated, and correct behaviour in live mode (`isMockMode` false, so no demo wallet fallback). Not backend data, not fixture data either. |
| `/verify` | "Connect the wallet you want to verify" only. | No backend call until a wallet connects. Same. |

Why this cannot be `lib/mock` sneaking in: the live :3000, which is in mock mode, serves **six**
events with cities Chicago and Indianapolis and a banner reading "Mock data — set
NEXT_PUBLIC_API_BASE_URL to read from the backend". The copy on :3001 serves **two** events, city
Toronto, named "Synthetic …", and no such banner. `lib/mock/events.json` contains none of the names
on :3001, and the analytics numbers above exist only in the backend's computation over
`fixtures/synthetic_store.json`.

## 4. The price-recommendation screen does not exist

There is no page in the frontend that shows a recommended price, and no endpoint that returns one.

- `grep -rn -i "suggest|recommend|optimal|forecast" app components lib` → **zero hits**.
- `lib/api.ts` exports nine functions, one per contract endpoint; none is a pricing call.
- `lib/types.ts` has no forecast or recommendation type. `API_CONTRACT.md` lists nine endpoints,
  none of them a price.
- The backend has the seam and says so: `/health` → `pricingModel: {available: false,
  modelVersion: null, reason: "no_model_registered"}`. Nothing in the UI reads `/health`.

The nearest surfaces that exist today, and what they are:

- `/organizer` and the event detail page show the **empirical** resale record — volume, average and
  median markup, the markup histogram, the price path. That is the input a recommendation would be
  computed from; it is not a recommendation.
- The event page shows the organizer's **cap** (resale capped at +25%) — a policy, not an optimum.

So the fourth screen asked for in the brief cannot be fetched, because it was never built. That
is reported rather than improvised around.

## 5. Screenshots: none could be taken

No headless browser exists on this machine, and none was installed. The probes, and what they
returned:

```
node -e "require.resolve('playwright')"   -> MODULE_NOT_FOUND
node -e "require.resolve('puppeteer')"    -> MODULE_NOT_FOUND
python3 -c "import playwright"            -> ModuleNotFoundError
python3 -c "import selenium"              -> ModuleNotFoundError
command -v chromium chromium-browser google-chrome google-chrome-stable firefox -> nothing
ls /opt/google/chrome/chrome /usr/bin/chromium /snap/bin/chromium -> No such file or directory
ls ~/.cache/ms-playwright ~/.cache/puppeteer ~/.cache/pyppeteer -> No such file or directory
```

**`docs/screenshots/` is empty because it does not exist. There are no images in this repo for this
demo.** What exists instead is the server-rendered HTML those pages returned (the numbers quoted in
§3 above are extracted from it), plus the two logs. Every page here is a React server component, so
the backend's numbers are in the HTML before any browser runs; a screenshot would add visual layout,
not evidence of the data path.

## 6. What is still synthetic, and stays labelled

- Every number in §3 is computed by `ticketpath/core` over `fixtures/synthetic_store.json`, which
  declares `meta.synthetic: true` in the file itself. Hand-authored on 2026-11-07 for tests. Not
  scraped, not real ticket data, not evidence for any research claim.
- Every API response that carries fixture-derived data carries
  `dataSource: {mode: "synthetic-fixture", synthetic: true, label: "SYNTHETIC FIXTURE DATA. …"}`.
  That label reaches the browser only inside the serialized page payload — checked: the string
  `SYNTHETIC FIXTURE DATA` is present in the served HTML of `/events/evt_fixture_1` and
  `/organizer`, but appears **nowhere in the visible text** of any page (script and tag stripping
  confirms it). No component displays it. A judge reading the screen sees "Synthetic" only in the
  event and organizer names ("Synthetic Hall Session", "Fixture Promotions (synthetic)"), because
  the fixture store names them that way — not because the UI is warning him. The live :3000 does
  better here: it shows a "Mock data — set NEXT_PUBLIC_API_BASE_URL" banner. The copy has no
  equivalent once it is on live data, which is a real labelling gap, not a cosmetic one.
- Structural stubs, unchanged from `records/CONTRACT-MAP.md`: `mintAddress` is a shape-valid
  placeholder (`FXTUREmint…`), no account exists; `transferRestricted` false and "Transfer
  restriction / Not enforced"; `signature` and `slot` null on every ledger row; `organizer.verified`
  false; destination `region` null ("Not shared"); `imageUrl` null.
- Not real either: `chain.programDeployed: false`, `programId: null`, `rpcEnabled: false`. The cap
  and the verified-wallet gate are carried as policy and enforced nowhere (they are transfer-hook
  conditions — `docs/ON-CHAIN-FOR-LAPTOP.md`).
- `lib/mock` was not read for evidence and nothing on the copy's port renders from it. It is untouched,
  smooth-rendering fixture data, and it stays that way.

## 7. The operator's one change in the morning

The live frontend is in mock mode because `NEXT_PUBLIC_API_BASE_URL` is empty in its `.env` and its
process env (`/proc/<pid>/environ` for that process shows no `NEXT_PUBLIC_API_BASE_URL`). One line, then restart it:

```bash
# in ../ticketing-frontend/.env  — the operator's file, not ours
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788
```

`NEXT_PUBLIC_*` is inlined at compile time, so that dev server has to be restarted for
it to take effect; it cannot be picked up live. Then `http://localhost:3000` shows the same two
synthetic events, Toronto, with the same 5.25 SOL / 75% / +5.6% / median 1.15 SOL that :3001 shows
now. Nothing else on the frontend needs to change: `lib/api.ts` is the only seam, and the backend
already answers all nine contract endpoints plus CORS.

## 8. What is still between this and a judge clicking a working demo

A judge can already click a real frontend and read numbers that came out of our backend — on
the copy's port, tonight, with no browser install and no edit to the live tree. What is missing is not
plumbing but product: **there is no screen anywhere that says what a ticket should be priced at.**
The backend's own `/health` admits it (`pricingModel.available: false, reason:
no_model_registered`), no endpoint serves a price, and no page asks for one. Every number on the
clicked pages is a market statistic computed from hand-authored fixtures.

## 9. Exact command lines, reproducible

```bash
# 0. state before anything
ss -ltnp | grep -E ':(3000|3001|8787|8788)'

# 1. backend on 8788
cd <repository root>
: > /tmp/ticketpath-backend.log
nohup python3 -m ticketpath.server > /tmp/ticketpath-backend.log 2>&1 &
curl -s -o /dev/null -w '%{http_code} %{time_total}\n' http://127.0.0.1:8788/health
curl -s http://127.0.0.1:8788/health | python3 -m json.tool
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8788/api/events?limit=3
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8788/api/events/evt_fixture_1
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8788/api/tickets/tkt_fixture_0001/resale-history
curl -s http://127.0.0.1:8788/api/events/evt_fixture_1/analytics | python3 -m json.tool

# startup timing, on a scratch port, killed immediately after
cd <repository root>
start=$(date +%s%N); TICKETPATH_PORT=8799 python3 -m ticketpath.server >/tmp/tp-timing-8799.log 2>&1 & p=$!
for i in $(seq 1 100); do curl -s -o /dev/null http://127.0.0.1:8799/health && \
  { end=$(date +%s%N); echo "startup_to_health=$(( (end-start)/1000000 )) ms"; break; }; sleep 0.05; done
kill $p

# 2. copy the frontend (source only; node_modules symlinked, nothing installed)
rsync -a --exclude 'node_modules' --exclude '.git' --exclude '.next' \
  ../ticketing-frontend/ ../ticketpath-demo/
ln -s ../ticketing-frontend/node_modules ../ticketpath-demo/node_modules

# 3. the copy on 3001, pointed at our backend
cd ../ticketpath-demo
: > /tmp/ticketpath-web.log
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788 \
  nohup ./node_modules/.bin/next dev -p 3001 >> /tmp/ticketpath-web.log 2>&1 &
ss -ltnp | grep 3001

# 4. the judge-click path
for p in "/" "/events/evt_fixture_1" "/organizer" "/tickets/tkt_fixture_0001" "/my-tickets" "/verify"; do
  f=$(echo "$p" | tr '/' '_')
  echo "$p -> $(curl -s -o /tmp/wp$f.html -w '%{http_code} %{time_total}s' --max-time 90 "http://127.0.0.1:3001$p")"
done
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:3001/events/fixture-hall-session

# trace: which calls the pages made
cat /tmp/ticketpath-backend.log

# preflight a browser would send from :3001
curl -s -i -X OPTIONS -H 'Origin: http://localhost:3001' \
  -H 'Access-Control-Request-Method: POST' -H 'Access-Control-Request-Headers: content-type' \
  http://127.0.0.1:8788/api/wallets/FXTUREacct111111111111111111111111111111111/verification/challenge

# 5. browser probe (all negative; nothing installed)
cd ../ticketpath-demo
node -e "try{console.log(require.resolve('playwright'))}catch(e){console.log('MISSING: '+e.code)}"
node -e "try{console.log(require.resolve('puppeteer'))}catch(e){console.log('MISSING: '+e.code)}"
python3 -c "import playwright"
python3 -c "import selenium"
for b in chromium chromium-browser google-chrome google-chrome-stable firefox; do command -v $b; done
ls /opt/google/chrome/chrome /usr/bin/chromium /snap/bin/chromium
ls ~/.cache/ms-playwright ~/.cache/puppeteer ~/.cache/pyppeteer

# 6. the live instance, untouched, and its mode
tr '\0' '\n' < /proc/<pid>/environ | grep -E "NEXT_PUBLIC|PWD"
curl -s --max-time 25 http://127.0.0.1:3000/
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:<port>/   # 200, the same process

# 7. proof the original tree was not written to
cd ../ticketing-frontend
find . -path ./node_modules -prune -o -newermt '2026-11-07 11:00' -not -path './.next/*' -print
# (no output)
```

---

## Snapshot note — 2026-11-07T12:14Z

**This file is a snapshot of 11:10Z, not a description of the current tree.** Everything above
is kept exactly as written, because it is the record of what was measured then. Five things in
it have since stopped being true, and one of them is the headline.

| What the document says | What is true now | Shown by |
|---|---|---|
| "not yet showing a price" (§ status); "There is no page in the frontend that shows a recommended price, and no endpoint that returns one" (§4) | The **backend's own console** at `http://127.0.0.1:8788/` now exists and prints `Recommended primary price: at least 1.38 SOL` on its default selection, tagged `[UNVALIDATED]`. The frontend still has no recommendation page — that half of §4 is unchanged, and the console is a separate surface served by `ticketpath/console/` | `curl -s http://127.0.0.1:8788/ \| sed 's/<[^>]*>//g' \| grep -i recommended` |
| `/health` → `pricingModel: {available: false, modelVersion: null, reason: "no_model_registered"}` (§4, §8) | `pricingModel.available` is `true`, `modelVersion` is `engine-2026-11-07`, `kind` is `rule-based-bounded-estimator`, `fitted` is `false`. The seam is populated; the note in the payload says there is no fitted model behind it | `curl -s http://127.0.0.1:8788/health \| python3 -m json.tool` |
| the event and ticket ids in §9 (`evt_fixture_1`, `tkt_fixture_0001`, `FXTURE…`), and "Hand-authored on 2026-11-07 for tests" (line 137) | The store is now **generated** by `tools/build_fixture_store.py`, seed `20261107`: **8 events, 76 tickets, 147 ledger rows**, ids `evt_syn_01`…`evt_syn_08` and `tkt_syn_0001`…, every wallet and mint `SYN…`. The §9 commands return 404 against the current store | `GET /api/events/evt_fixture_1` → 404; `GET /api/events/evt_syn_02` → 200; `python3 tools/build_fixture_store.py --check` |
| the pids, ports and log paths in §1 are "what is running now" | They are what was running at 11:10Z. Nothing in this table is a current process. 8788 is the backend's port; 8787 belongs to another process and is refused by the server | `ss -ltnp \| grep -E ':(3000\|3001\|8787\|8788)'` |
| the test suite implied by §9 (no count given) | `OK`, on a suite that was **293 tests when this pass began and 306 when it ended** (another session was adding console tests throughout). Quote the command's own last line, never this one. | `python3 -m unittest discover -s tests` |

What has not changed: every number in §2–§3 came from the backend and still would, the frontend
screens listed still render the same aggregates, and there is still no page in the frontend that
quotes a price.

---

## CORRECTION (2026-11-08T08:30Z): machine handles redacted, no claim changed

**Scope:** this file only, and only the lines in the table below. The snapshot note above is
untouched and still governs: nothing in §1 is a current process. **Why:** this repository is public
and `tools/public_safety.py` refuses a tracked file that carries a process id or a port tied to a
running process. The rule and its reason are in `.public-denylist`.

**What a redaction here is allowed to cost: nothing that was measured.** The pids in §1 were the
handle for stopping a process, and that handle is still given as "the backend's pid" and "the copy's
pid" in the row that says how; the port and the command in the same row are unchanged, so the row
still identifies the thing. The startup-to-health timing, every status code, every byte count and
every page table cell is untouched.

| Where | Was | Now |
|---|---|---|
| Status line | the copy's port and the live frontend's port as tied handles | "the copy's port", "the live frontend's port" |
| Header | `pid <n>` still serving | "the same process still serving" |
| §1, backend row | `kill <n>` | `kill <the backend's pid>` |
| §1, copy row | `kill <n>` | `kill <the copy's pid>` |
| §1, live frontend row | `pid <n>` | the pid gone, "not ours to touch" kept |
| §1, other process row | `pid <n>` | the pid gone, "not ours, not bound by us" kept |
| §3, end-of-run check | a URL with a tied port, "still pid `<n>`" | "The live frontend's home page re-checked at the end: **200**, still the same process, still mock mode" |
| §6 | the copy's port tied to "renders from it" | "nothing on the copy's port renders from it" |
| §7 | `/proc/<n>/environ`, "restarted (pid `<n>`)" | `/proc/<pid>/environ`, "restarted" |
| §8 | the copy's port | "the copy's port" |
| §10 reproduction block | `/proc/<n>/environ`; a URL ending `# 200, pid <n>` | `/proc/<pid>/environ`; the URL with `<port>` and `# 200, the same process` |

**Residue, stated rather than hidden.** The ports themselves stay where the rule does not classify
them, including in §1's Port column, the `ss` command in §10 and this project's own backend port.
`.public-denylist` states why it does not deny those, and `/tmp` paths are exempt for `records/` on
purpose. `python3 tools/public_safety.py check --tracked` reports zero hits for this file as of this
note.

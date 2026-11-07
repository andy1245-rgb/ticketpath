# SUBMISSION-PACK: the video script, the submission text, the field list and the last-hour checks

**Written:** 2026-11-07T11:41Z by the submission session, from its own command output on this machine.
**Target deadline:** initial submission Sun 2026-11-08 **10:00 ET = 15:00Z**. Final 11:45 ET. Treat 10:00
as a hard freeze: nothing published says the initial submission can still be edited after it
(`records/findings/02-rubric-and-scoring.md`, open question 1).
**The rule this document obeys:** nothing here claims a deploy, a devnet address, a real dataset, an
accuracy figure, a screenshot, or a screen that does not exist. Where the entry is thin, the text says it
is thin. What scores and what does not is decided by `records/findings/02-rubric-and-scoring.md`, and that
finding is the authority here. The 25/25/25/25 weighting is **not** used anywhere in this document, because
it could not be sourced on any MLH or event page (that finding, A5).

---

## 0. The state this pack is written against, measured between 11:34Z and 11:41Z

Every line below was produced by a command in this session, not carried from another record.

| Thing | Measured state | Where |
|---|---|---|
| Backend | running, pid 242675, `127.0.0.1:8788`, `/health` 200 | `curl /health` |
| Backend store | **8 events, 76 tickets** (the regenerated store, not the old 2-event one) | `GET /api/events?limit=100` |
| Frontend demo copy | running, pid 233166, port **3001**, honesty patch applied, notice visible in the served text | `../ticketpath-demo`, `curl :3001/` |
| Live frontend (his) | running on :3000, pid 81447, untouched, mock mode | not ours |
| Screens carrying backend numbers | `/`, `/events/evt_syn_02`, `/organizer?event=evt_syn_02`, `/tickets/tkt_syn_0001` | served HTML, tag-stripped |
| Pricing console (`ticketpath/console/`) | **does not exist** | `ls ticketpath/` |
| Price served anywhere | **none**: `/health` → `pricingModel.available: false, reason: no_model_registered` | `/health` |
| Chain | `programDeployed: false, programId: null, rpcEnabled: false` | `/health` |
| Test suite | `python3 -m unittest discover -s tests` → **149 tests, OK** | run in this session |
| Root README | **missing** | `ls README*` |
| LICENSE | **missing** | `ls LICENSE` |
| Repo | public, `andy1245-rgb/ticketpath`, created 2026-11-07T10:25Z, GitHub reports `license: None` | GitHub API |
| Remote vs local | remote `main` = `e55a18b` (pushed 10:27Z); local HEAD = `3bece48` **plus uncommitted changes**. The public repo does **not** contain the backend, the fixture store or any Phase 2 record | `git ls-remote origin` |
| Browser on this machine | none (no chromium, firefox, playwright, puppeteer, selenium) | probed in this session, and `DEMO-PROOF.md` §5 |
| Devnet from this machine | reachable: `getVersion` → `solana-core 4.4.0`; Token-2022 program account exists, `executable: true`, slot 519647005 | `curl api.devnet.solana.com` |

Two consequences, and they shape everything below.

1. **The console is not built, so there is no screen that shows a decision.** The video script is written
   for the state that exists, with one clearly marked swap-in block for the day the console lands.
2. **The public repo is behind the work.** A judge who follows the project link tonight finds Phase 1
   documents and no backend. That is the single most damaging thing about the current state, and it is a
   `git push` away from being fixed. It is your click.

---

## 1. The video

**Re-timed 2026-11-07T12:21Z against the console as it runs, and there is now one script.** The console
serves a bounded recommendation at `http://127.0.0.1:8788/`, so the script written before it existed is
false in two places at once: it tells you to put `"available": false, "modelVersion": null` in frame and to
say that no price is served, and neither is true of the running system. That text is kept verbatim, and
marked obsolete, in appendix §1.5. Every URL, screen and figure below was fetched on this machine between
12:19Z and 12:21Z, with the command named under each beat. §0 above remains the 11:34Z snapshot, and its
snapshot note at the end of this file still applies to it.

**Target 1:56. Hard cap 2:00.** One file. The hackathon's name in the first spoken sentence, which is a
published rule, not a style choice (`02-rubric-and-scoring.md` B4 rule 3). A demo recording, not a pitch:
MLH's judging plan says the video "should be a demo of their hack, not a presentation", and pitch quality
is explicitly not judged (B3, B7).

### 1.1 Before you record: the recording path, which is the one thing that can go wrong

There is no browser on this machine (`DEMO-PROOF.md` §5 measured every candidate). Every screen in the
script is a real page served by the demo copy on :3001 or by the backend's own console on :8788, and the
recorded page has to be opened from a machine that has a browser. Two ways, and only the first needs
nothing installed anywhere.

**Path A, over the LAN (recommended, no installs).** On this machine:

```bash
# 1. backend and console, reachable from another machine
cd <repository root>
TICKETPATH_HOST=0.0.0.0 nohup python3 -m ticketpath.server > /tmp/tp-video-backend.log 2>&1 &

# 2. the frontend copy, told to call the backend on the address the recording machine uses
hostname -I          # prints several; the first is usually a virtual bridge, not your LAN
IP=<the one the recording machine can reach>
cd ../ticketpath-demo
NEXT_PUBLIC_API_BASE_URL=http://$IP:8788 nohup ./node_modules/.bin/next dev -p 3001 > /tmp/tp-video-web.log 2>&1 &
```

Pick the address by testing it, not by trusting the order `hostname -I` prints: from the recording machine,
`curl -s -o /dev/null -w '%{http_code}\n' http://<the-address>:8788/health` must return 200 before anything
else is worth doing. If none of them does, the two machines are not on the same network and path B is the
only option. The console needs no separate process: it is the page that same backend serves at `/`, and the
bytes it returns carry no `src=` or `href=` reference, so there is nothing else for it to load.

Then on the recording machine, open `http://<LAN-IP>:3001/`. **Pass condition, check all five before
recording:** eight event cards; city names including Hamilton and Guelph; the strip
`SYNTHETIC FIXTURE DATA. Generated for tests and demonstration...`; **no** banner reading "Mock data"; and
`http://<LAN-IP>:8788/` shows the console with its recommendation, its `[UNVALIDATED]` badge and its own
fixture strip. All five were confirmed on `127.0.0.1` at 12:19Z to 12:20Z; the LAN address is the same two
processes. If the banner is there, the copy is still in mock mode and the video would show the wrong data.
Exposure: binding to `0.0.0.0` puts the fixture API on the LAN while it runs. That is your call, and the
data is synthetic.

One thing not to be surprised by, and not to fix on camera: the console prints a caption `canonical URL for
this decision: http://127.0.0.1:8788/?event=evt_syn_02&...`. It says loopback because the backend builds that
line from its own bind address, even when the page is loaded over the LAN (checked by sending a foreign
`Host` header and getting the same loopback caption back). Leave it in frame, do not read it aloud, and do
not present it as a hosted demo: it is the identifier of the decision, not an address a judge can open.

**Path B, everything on the laptop.** Copy the repo and the frontend copy, install the frontend's
dependencies there, set `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788`. More work, no LAN exposure, and
it needs npm on the laptop.

**Do not** attempt to record on this machine with a browser install. Nothing here renders a page, and
installing one is a change to a machine nobody asked to change.

### 1.2 The script

264 spoken words, 1:53 of speech at 140 words per minute, 1:58 allowing a one-second breath at each of the
five transitions. Say `NAME` as your own name; it is the only substitution. Nothing else in the blocks below
changes.

| Beat | Time | On screen (exact) | Must land |
|---|---|---|---|
| 1 The problem | 0:00 to 0:22 | `http://<host>:3001/organizer?event=evt_syn_02`, the "Resale analytics" panel, scrolled to the four stat tiles | **22.03 SOL across 12 sales, average markup +12%, cap is +15%**, all three visible at once |
| 2 What recorded it | 0:22 to 0:43 | same page, then tab 2: `http://<host>:8788/api/events/evt_syn_02/analytics` | the JSON shows **`"saleCount": 12`** and **`"avgMarkupBps": 1233`**, the same numbers as the page, and `dataSource.label` at the bottom says the ledger is a fixture |
| 3 The console | 0:43 to 1:04 | `http://<host>:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2` | **`Recommended primary price: at least 1.38 SOL per ticket, General tier.`** under its `[UNVALIDATED]` badge, then `That is a floor, not an estimate.`, and the cap's role said out loud: a resale ceiling, not the primary price |
| 4 The refusal | 1:04 to 1:20 | same console page, scrolled to `What the engine refuses` | **`not_identified`** and its sentence about asking prices, and **`Range: 1.38 SOL and up.`** |
| 5 The on-chain invariant | 1:20 to 1:42 | `http://<host>:3001/tickets/tkt_syn_0001`, the "Custody trail", then the "On-chain (simulated)" card | the `Transferred` row with **no price**, then **`Not enforced — no program is deployed`** |
| 6 The close | 1:42 to 1:58 | end card: `Ticketpath` / `Organizer pricing from the resale record` / `github.com/andy1245-rgb/ticketpath` | **"Nothing is deployed"** has already landed; here the line is **"everything else carries a label saying what it is"** |

**Beat 1, spoken (51 words, about 22 s):**

> I'm NAME and this is my demo for the MLH Solana Hackathon. An organizer sets face value once, then the
> resale market prices the same seat without them. This is one event's record: twelve resales, twenty-two
> point zero three SOL of volume, twelve percent over face, against a fifteen percent cap.

On screen at that moment, and check them with your eyes before you roll: the page header `Resale analytics`,
the strip `SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.`, and the
tiles `Total resale volume 22.03 SOL across 12 sales` / `Average markup +12% cap is +15%` / `Median resale
price 1.38 SOL` / `Tickets resold 67% 11 distinct holders`. The page's own subtitle already says "In this
build that ledger is simulated: no ticket program is deployed." Do not scroll past it, and do not edit it
out. Fetched for this edit: `curl -s 'http://127.0.0.1:3001/organizer?event=evt_syn_02'` → 200, text above.

**Beat 2, spoken (46 words, about 20 s):**

> The numbers come from a backend I wrote. This JSON is the same twelve sales and twenty-two point zero
> three SOL, twelve thirty-three basis points of average markup, computed from a custody ledger. Both
> screens say the ledger is synthetic, because it is a generated fixture.

Open a second tab on `http://<host>:8788/api/events/evt_syn_02/analytics` and let the browser's own JSON view
show it. The two fields to have in frame are `"saleCount": 12` and `"avgMarkupBps": 1233`; the same body
carries `"totalVolumeLamports": 22026000000` and, at the bottom, `dataSource.label` with the same
`SYNTHETIC FIXTURE DATA` sentence the page prints. Do not read the JSON out loud beyond the two numbers; the
point is that they match the page. Fetched for this edit: `curl -s
http://127.0.0.1:8788/api/events/evt_syn_02/analytics` → the fields above.

**Beat 3, spoken (49 words, about 21 s):**

> The console is where the decision is made. The cap binds: eight of nine resales settled at the ceiling, so
> the engine gives a floor, not an estimate. The cap sets the resale ceiling, not your price. Recommended
> primary price, at least one point three eight SOL per ticket.

That URL is the one to type: it selects the event, the tier, the cap and the declared τ, so the screen is the
same on every take. Its `asOf` defaults to the instant the page loads, and the numbers do not move with it
(checked at two `asOf` values an hour apart). The page opens on `Synthetic Stage: Resale Cap Binds — capped
and binding`, tier `General`, face `1.20 SOL`, with the badges `12 resales on this event`, `12 tickets`,
`9 at the ceiling`, `8 events on this platform, 5 with any resale`, `0 on-chain transactions`. The two lines
doing the work are `[EXACT] ceiling 1.38 SOL = face 1.20 SOL plus a cap of 15%` and `[UNVALIDATED]
Recommended primary price: at least 1.38 SOL per ticket, General tier.`, followed by the sentence "the cap is
binding: 8 of 9 recorded resales (88.9%) settled at exactly the ceiling" and `Value: at least 1.38 SOL per
ticket. That is a floor, not an estimate.` Keep the fixture strip at the top of the page in frame: every
number on this page is tagged `[FIXTURE]`, `[EXACT]`, `[UNVALIDATED]`, `[REFUSED]`, `[DECLARED]`, `[DESIGN]`,
`[SIMULATED]` or `[DEVNET]`, and those tags are the honesty of the screen, so do not crop them. The floor and
the ceiling are the same number because the highest recorded resale settled at the ceiling, so the ceiling is
the highest price anyone paid and therefore a floor on value; it is not the cap setting the primary price, and
the page's own line (A10) says the cap is a ceiling on the resale price and a floor on value, not a target for
the primary price. Fetched for this edit: `curl -s 'http://127.0.0.1:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2'`
→ 200, strings above.

**Beat 4, spoken (36 words, about 15 s):**

> It refuses an upper bound, a sale probability and an interior optimum, and names the missing observation
> for each. Nothing records what a ticket was listed at, and no fitted model sits behind any of this.

Scroll to the `What the engine refuses` block and keep three of its six rows in frame: `not_identified` ("The
platform does not record asking prices, so we cannot estimate the chance a ticket sells at a specific
price"), `no_upper_bound`, and `insufficient_events` ("The model is not fitted... no out-of-sample score
exists"). Above the block the value line closes on `Range: 1.38 SOL and up. We do not state an upper bound
from this record.`, and that second sentence is the one the `no_upper_bound` row repeats, so having both in
frame costs nothing. Do not press `Show the refusal`: that button runs the simulated state machine, whose
panel reads `0 arms shown` until it is pressed, and an empty panel on camera reads as broken.

**Beat 5, spoken (47 words, about 20 s):**

> A ticket cannot move without the program recording the hop, and the program will not record a price above
> the organizer's cap. That makes the resale record complete by construction. Nothing is deployed; the
> screen says so, and the custody trail shows a transfer with no price.

The row to have in frame first is the unpriced one in the custody trail: `Transferred · Oct 12, 2026, 2:00 AM`
between `Resold 1.18 SOL +18%` and `Resold 0.94 SOL -6.0%`. It is the visual proof of the sentence. Then
scroll to the `On-chain (simulated)` card: its subtitle reads "The mint address is a fixture placeholder: no
account exists on any cluster and no transaction backs these rows", its `Transfer restriction` row reads
`Not enforced — no program is deployed`, and the mint is a `SYN1...` placeholder. Keep your hands off the
explorer link: it 404s, and a 404 on camera undoes the beat. Fetched for this edit: `curl -s
http://127.0.0.1:3001/tickets/tkt_syn_0001` → 200, both cards above.

**Beat 6, spoken (35 words, about 15 s):**

> Wallet verification here is real cryptography. Everything else carries a label saying what it is. Next is
> one write on devnet, then a real ledger. Code and run steps are in the repository. Thank you.

End card is a text card you make in any editor: three lines, large enough to read when paused, no logo, no
animation. Do not show the Explorer or a terminal.

### 1.3 The timing, printed

- **264 spoken words.** 113.1 s at 140 words per minute, which is 1:53. Five one-second beats between the
  six sections bring it to 1:58. That leaves 2 s of headroom against the 2:00 cap, before any second take.
  Beat 3 is the beat that grew, by six words, when the cap's role was added to it; the word count is the text
  in §1.2 and nothing else.
- Nothing was cut for this edit. The script is inside the cap, so the beats stand as written; cutting one
  would cost a screen the submission is better for showing.
- If you speak slower than 140, shorten beat 2 to its first two sentences: the fixture label is legible on
  screen in that frame whether or not it is said. If that is still not enough, drop beat 6's last two
  sentences. Do not shorten beat 4 to buy time; it is the beat that distinguishes this entry from a demo
  that hides what it cannot answer.
- Every figure spoken above was fetched during this edit and is a figure the screen shows: 12 sales, 22.03
  SOL, +12%, +15%, 1233 bps, 8 of 9 at the ceiling, 1.38 SOL, 1.20 SOL face.

### 1.4 What must not appear on any frame

- The `Mock data` banner, six `lib/mock` events, or Chicago and Indianapolis. Those are the live :3000
  instance and they are not our data.
- `/my-tickets` or `/verify` without a connected wallet. Both are connect prompts and both read as broken.
- Any Solana Explorer page for a `SYN...` mint address. No account exists; the page will say so.
- The console's `The state machine` panel untouched, reading `0 arms shown`, or a `Recompute` that was
  clicked mid-take. Load the page, scroll, do not press.
- A terminal, a desktop, a second monitor, a browser bookmark bar, a notification.
- Any number on screen without the `SYNTHETIC FIXTURE DATA` strip above it. If a crop removes the strip,
  the crop is wrong. That includes the console, whose strip is the first element on the page.
- Music, stock footage, a market-size slide, a team slide. Not judged, and everything they displace is.

### 1.5 Appendix: variant A, the pre-console script. OBSOLETE — do not record.

Kept verbatim so the record of what was planned survives, and obsolete in one sentence: it was written for a
build that had no console, so it puts `"pricingModel": {"available": false, "modelVersion": null}` and the
spoken claim that no price is served in frame, when the console serves a bounded recommendation labelled
`[UNVALIDATED]` and `/health` reports the engine as registered with `fitted: false`.

259 spoken words, 1:51 at a normal pace (140 words per minute), 1:52 with the beat between sections.
Say `NAME` as your own name; it is the only substitution. Nothing else in the blocks below changes.

| Beat | Time | On screen (exact) | Must land |
|---|---|---|---|
| 1 The problem | 0:00 to 0:23 | `http://<host>:3001/organizer?event=evt_syn_02`, the "Resale analytics" panel, scrolled to the four stat tiles | **22.03 SOL across 12 sales, average markup +12%, cap is +15%**, all three visible at once |
| 2 The thing that runs | 0:23 to 0:57 | same page, then tab 2: `http://<host>:8788/api/events/evt_syn_02/analytics` | the JSON shows **`"saleCount": 12`** and **`"avgMarkupBps": 1233`**, the same numbers as the page |
| 3 The on-chain invariant | 0:57 to 1:18 | `http://<host>:3001/tickets/tkt_syn_0001`, the "Custody trail", then the "On-chain (simulated)" card | the invariant sentence, then **"Not enforced, no program is deployed"** on screen |
| 4 The honest limitation | 1:18 to 1:35 | the same ticket page, the unpriced `Transferred` row and the custody trail | the sentence about the ask, spoken over a row that has **no price** |
| 5 The close | 1:35 to 1:52 | end card: `Ticketpath` / `Organizer pricing from the resale record` / `github.com/andy1245-rgb/ticketpath` | **"Nothing is deployed"** has already landed; here the line is **"everything else carries a label saying what it is"** |

**Beat 1, spoken (54 words, about 23 s):**

> I'm NAME and this is my demo for the MLH Solana Hackathon. Organizers set face value once, then the
> resale market prices the same seat without them. This is one event's record: twelve resales, twenty-two
> SOL of volume, twelve percent over face, against a fifteen percent cap. Their own system shows none of it.

On screen at that moment, and check them with your eyes before you roll: the page header `Resale analytics`,
the strip `SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data...`, and the
tiles `Total resale volume 22.03 SOL across 12 sales` / `Average markup +12%` / `cap is +15%` /
`Median resale price 1.38 SOL` / `Tickets resold 67%` / `11 distinct holders`. The page's own subtitle
already says "In this build that ledger is simulated: no ticket program is deployed." Do not scroll past
it, and do not edit it out.

**Beat 2, spoken (79 words, about 34 s):**

> The page is the platform's own frontend, with a text-only labelling patch from me. The numbers come from
> a backend I wrote: this JSON is the same twelve sales, twenty-two point zero three SOL, twelve thirty-three
> basis points average, computed from a custody ledger. Both screens say the ledger is synthetic, because it
> is a generated fixture. There is no price on either screen. The backend answers pricing model unavailable,
> and that is the honest state of the work.

For the last sentence, open a third tab on `http://<host>:8788/health` so the words "pricing model
unavailable" are literally on screen while you say them. The
`/health` body contains `"pricingModel": {"available": false, "modelVersion": null, "reason":
"no_model_registered"}`. Scroll so that line is in frame. Do not read the JSON out loud beyond the two
numbers; the point is that they match the page.

**Beat 3, spoken (48 words, about 21 s):**

> Here is what the chain is for. A ticket cannot move without the program recording the hop, and the
> program will not record a price above the organizer's cap. That makes the resale record complete by
> construction. Nothing is deployed. This is design, and the screen says so.

The card on screen is titled `On-chain (simulated)` and its subtitle reads "The mint address is a fixture
placeholder: no account exists on any cluster and no transaction backs these rows." That subtitle is the
sentence doing the work. Keep it in frame. If you scroll to the mint address, keep your hands off the
explorer link: it 404s, and a 404 on camera undoes the beat.

**Beat 4, spoken (39 words, about 17 s):**

> The limit is in the record: nothing records what a ticket was listed at, so the chance it sells at a given
> price cannot be computed, and saying that is worth more than fitting a curve to sales alone.

The row to have in frame is the unpriced one in the custody trail: `Transferred ... no price`, between the
two priced sales. It is the visual proof of the sentence. Nothing in this product records an asking price,
which is why the engine refuses that question and why this video says so instead of showing a number.

**Beat 5, spoken (39 words, about 17 s):**

> Wallet verification here is real cryptography. Everything else carries a label saying what it is. Next is
> one write on devnet, then a real ledger. Code, the fixture generator and the run steps are in the
> repository. Thank you.

End card is a text card you make in any editor: three lines, large enough to read when paused, no logo, no
animation. Do not show the Explorer or a terminal.

---

## 2. The submission text

Written for the state at 11:34Z. Lines that would change if the console lands are marked
**VERSION-IF-CONSOLE-LANDS** and nothing else in the text has to move.

### 2.1 Title

> Ticketpath: organizer pricing from the resale record

### 2.2 Description

> Ticketpath is a tool for the organizer of a live event who sets a ticket price once and then cannot see
> what the same seat sells for afterwards. It reads the resale record and shows what tickets actually
> changed hands for: the markup on every recorded sale, measured against that ticket's own tier's face
> value, the custody path of an individual ticket with a price attached to each hop, and the roll-up an
> organizer would need, which is volume, median price, markup distribution and where the tickets ended up.
> It runs tonight as a Python backend that answers nine endpoints of the platform's own frontend contract,
> serving eight events and seventy-six tickets with a working custody trail, resale analytics and real
> Ed25519 wallet signature verification, on a 149-test suite that passes. It also serves a console that
> reads one event's resale record and gives a floor on the primary price from it, labelled a floor and not
> an estimate, and it states the cap's role correctly: a cap in basis points over face sets the ceiling on
> the resale price and, where it binds, fixes how that price divides between the organizer's price and the
> reseller's margin, and it does not set the primary price. The ledger is a generated fixture and not ticket data, and
> every screen says so in the visible text. No ticket program is deployed, so no price is enforced on chain:
> the program that would refuse a resale above the cap is designed and simulated, not deployed.

**[REWRITTEN 2026-11-07T15:10Z — two sentences replaced, and the old wording is kept for the record.** The
closing sentence ("no price is served: the backend reports `pricingModel.available: false`") was true at
11:41Z and false once the console landed; it is quoted in §4 item 9 and in the 12:14Z snapshot note. The
cap sentence states the narrowed result and replaces "the resale premium is capturable entirely through the
primary price" (`11-cap-capture-check.md` §9, §11.1; `F` D7): the cap fixes the split of the resale price,
`1 : c`, and does not set the primary price. The test count in this paragraph is left as written and was
already flagged as stale in the 12:14Z snapshot note; §5 answer 9 still carries the pre-console wording and
§4 item 9 is the correction for it.]**

### 2.3 How it works

> The backend is Python 3, standard library only, no dependency to install. Ledger rows come in as an
> issue, priced sales, unpriced transfers and redemptions per ticket, and everything on screen is computed
> from those rows: a ticket page's last price, peak, hop count and custody trail, an event's resale share,
> average markup and daily price series, an organizer's volume, median, six markup buckets and top holding
> wallets. Markup is measured against the ticket's own tier's face value, because a multi-tier event makes
> a single face value meaningless. Wallet verification is the one real cryptographic operation in the
> build: the backend issues a nonce, the wallet signs a frozen message, and the signature is checked
> against the public key in the backend. The frontend is the platform's own Next.js application. We did not
> write it and we did not redesign it: a copy is pointed at our backend, plus a patch that surfaces the
> provenance label the backend was already sending and corrects sentences that asserted on-chain
> enforcement. The demo runs locally, on ports 8788 and 3001.

**VERSION-IF-CONSOLE-LANDS**, append to 2.3:

> The second surface is a console served by the backend at `/`: it states the recommended primary price for
> a selected event, shows the evidence counts the answer rests on, and prints a refusal with its reason
> wherever the record cannot support a number.

### 2.4 What is on-chain

> Nothing. No program, no mint, no transaction, no address, and no signature to show or explorer link to
> follow. There is no devnet deployment and this paragraph is the only place where that could be hidden, so
> it is stated rather than implied. What exists is a design and a set of reads. From the build machine we
> queried devnet directly: `getVersion` answered `solana-core 4.4.0`, and the Token-2022 program account
> exists and is executable (measured 2026-11-07, slot 519647005). The design is written down in the repo:
> a ticket minted by the program cannot change hands without the program writing that hop into the ticket's
> own record, and the program refuses to record a price above the organizer's cap, so the resale record the
> pricing engine reads is complete and cap-compliant by construction rather than by the API's good faith.
> The cap is checked in the sale instruction, not in the transfer hook, because a Token-2022 hook never sees
> lamports; the hook enforces who may receive. A Python mirror of the same state machine, with the same
> error codes, runs in the test suite. It proves the arithmetic and the ordering, not that Token-2022 calls
> a hook.

### 2.5 What is not done

> The entry is thin in five places, and each one is visible rather than argued away. First, nothing is
> deployed: no program, no mint, no transaction, so a judge cannot confirm any chain claim by looking at a
> cluster, only by reading the design and the simulation in the repo. Second, there is no real data. The
> record is eight events and seventy-six tickets generated by a script in the repo; it is internally
> consistent and it is not evidence about any market, and the screens say so. Third, the decision surface
> does not exist yet: there is no page that shows a recommended price, the backend registers no pricing
> model, and the honest output of the pricing work today is a written specification and a refusal, not a
> number. Fourth, there is no hosted demo. The app runs locally and the run steps are in the repo; the
> submission has no demo URL, and clicking the project link will not show a running product. Fifth, there
> are no screenshots in this submission, because the build machine has no browser. The frontend that a
> judge would see is the platform's own, and the labelling patch is ours.

**VERSION-IF-CONSOLE-LANDS**, replace the third item with:

> Third, the console exists but the engine behind it is not validated: the recommendation is a bound with a
> declared width, no parameter has been checked against a real resale, and the console says so on every
> number it prints.

### 2.6 Built with

- Python 3.12, standard library only, no package installed
- The platform's own Next.js frontend, unmodified in layout, plus our text-only labelling patch
- Node 24 and the Next dev server, for the demo copy on port 3001
- Solana JSON-RPC over HTTPS, devnet, read only
- Token-2022 and a transfer-hook design, not deployed
- Ed25519 signature verification, implemented in the repo
- A deterministic fixture generator (seed 20261107) and a 149-test unittest suite
- AI coding agents, disclosed below

### 2.7 AI disclosure (required, and the penalty for omitting it is disqualification)

Draft, with the tool names left as a TBD because only he knows exactly what he ran:

> Most of the code and most of the documents in this repository were written with AI coding agents
> (`TBD-TOOL-NAMES`) working under a written brief, in parallel sessions. Claims were checked against the
> command output that produced them where that was possible, and are labelled where it was not. The fixture
> generator, the test suite and the labelling patch were written this weekend. The research records name
> their sources.

MLH's published rule asks teams to be honest and transparent about which AI code tools they used and to
list them in the submission, and the organizer-side copy attaches disqualification and a report to
`cheating@mlh.io` for not crediting them (`02-rubric-and-scoring.md` B6). Naming the wrong tools is worse
than naming none, so this line is yours to fill.

---

## 3. The field checklist

Every field a Devpost-style or MLH Challenges form asks for, what goes in it, and who supplies it. "Set"
means the text is in this document and needs no decision. "TBD" means only he can decide or confirm.

| # | Field | What goes in it | Who |
|---|---|---|---|
| 1 | Project name | `Ticketpath` | set (a rename is your call) |
| 2 | Elevator / short description | one sentence from §2.2 | set |
| 3 | Project link (repo URL) | `https://github.com/andy1245-rgb/ticketpath` | URL set, **content not pushed: see T1** |
| 4 | Video URL | public link to the file recorded from §1 | **T2** |
| 5 | Demo URL | still none: the console runs on a loopback address a judge cannot open, so the field stays blank or points at the repo's run steps and says the demo is local. The console does not change this answer, and turning it into a real one is **T11** | **T3, T11** |
| 6 | Description | §2.2 | set |
| 7 | How it works / technical description | §2.3 | set |
| 8 | What is on-chain | §2.4, verbatim | set |
| 9 | What is not done | §2.5, verbatim | set |
| 10 | Inspiration / challenges / accomplishments / what we learned / what's next | accomplished: 149 tests, real signature verification, a labelling patch that makes an inherited UI tell the truth. Learned: the asking price is the missing observation, and no model fixes a missing column. Next: one write on devnet, then a real ledger | set |
| 11 | Built with / technologies | §2.6 | set |
| 12 | Team members, names, emails, MLH accounts | your team | **T4** |
| 13 | Track: Top 3 Overall | select. The criterion is one sentence about Solana being load-bearing, and the honest answer is "designed, not deployed" | set |
| 14 | Track: Best Beginner | eligible only if more than half the team are first-time hackers | **T5** |
| 15 | Track: AI, DeFi, Gaming | recommend none. There is no AI component in the build, no payment or lending surface, and no game | set (your veto) |
| 16 | Devnet program id / mint / address field | **leave empty.** Nothing is deployed. An invented address is the one lie that would sink the entry | set |
| 17 | Licence | repo is public with `license: None` on GitHub. Pick one, add `LICENSE` | **T6** |
| 18 | AI tool disclosure | §2.7 | **T7** |
| 19 | Screenshots / thumbnail | none exist. The video's thumbnail comes from the video platform | set |
| 20 | Country, school, code-of-conduct agreement, account linking | form filler | your clicks |

### The TBDs, numbered, and what each one is

- **T1 Push the current tree to the public repo.** Blocks submission (see below). Measured: repo is public, remote `main` is at `e55a18b` from 10:27Z, local HEAD is `3bece48` with uncommitted changes, so the public repo has no backend, no fixture store, no console spec and no research records. No push happens without your explicit yes.
- **T2 The video URL.** Does not exist. Must be recorded this weekend from §1 and must stay public.
- **T3 The demo URL field.** No hosted demo. Either blank, or the repo with a plain note that it runs locally. The console does not change this: it is served on `127.0.0.1:8788`, which is his machine and not a judge's (T11).
- **T4 Team.** Names, emails, MLH registration state.
- **T5 First-time-hacker status**, which decides Best Beginner eligibility (>50% of the team).
- **T6 Licence.** GitHub reports none. MIT or Apache-2.0 are the usual two; he picks and the README line must match the file.
- **T7 AI tool names** for the disclosure in §2.7.
- **T8 Recording machine and path** (§1.1 A or B), and whether the backend may bind to the LAN address.
- **T9 Whether to attempt the devnet write.** One memo transaction carrying a hash of a quote, run by him on a laptop with Agave, then read back and verified. It would turn "design" into "a real transaction with a block time" (`BUILD-SPEC-NIGHT.md` §5.6 option c). It costs about an hour of his time and a few thousandths of a devnet SOL. If he does not do it, the honest state is "nothing is deployed" and the submission is complete without it.
- **T10 Whether the honesty patch goes into the live frontend tree** and gets a `:3000` restart. The patch is applied to our copy at `../ticketpath-demo` and verified there. The live tree is his and is untouched. If he never shows `:3000`, this is moot.
- **T11 How the console becomes reachable, if at all. TBD, and it is the only one the console raises.** The console is at `http://127.0.0.1:8788/`: `127.0.0.1` is the machine it runs on, so a judge clicking anything cannot reach it, and the video is the only place a judge will ever see it. Three options, cost of each in one line: **record only** — free, nothing to run at submission time, and the form's Demo URL stays blank (T3); **a tunnel** (`cloudflared tunnel --url http://127.0.0.1:8788`, or ngrok) — free and live in a minute, but the URL is public and up only while the process runs, so it has to be up for the judging window or it reads as a dead link, and it exposes the fixture API to anyone who finds it; **a deploy** — a few hours of his time plus a hosting account, the only option that survives him closing the laptop, and the only one that puts a URL in the form he can be held to. What the video shows either way is unchanged: every console screen in §1.2 is recorded from the local address, and no frame claims the console is hosted.

**T1 blocks submission outright.** A submitted entry whose project link resolves to a repository that does
not contain the code the submission describes fails the sponsor's own evidence check and the public-code
rule, and no wording in the form repairs it. T2 is the other unrecoverable gate, and it is a task rather
than a decision: it either exists by 11:30 or the entry is ineligible. Fix T1 first regardless, because it
is a ten-second action and it is the one that makes every other claim checkable. T11 does not block
anything: with no hosted demo the entry is complete and the video is the only place the console is seen.

---

## 4. Pre-submission verification, in order

Run this in the last hour, in this order. Each item is a thing to do and a pass condition. Stop at the
first failure.

**1. Repo state.**
`cd <repository root> && git status --short && git log -1 --format='%H %ci'`.
Pass: the working tree contains the code you are submitting, the last commit is inside the weekend window
(the first commit, `744a2c2`, is 2026-11-07 08:29Z, which is inside), and the tree you verified is the tree
you will push.

**2. No secrets.**
`git grep -nEi 'BEGIN [A-Z ]*PRIVATE KEY|api[_-]?key|password|\.env'` and
`git ls-files | grep -E '\.(pem|key|env)$'`.
Pass: every hit is library use of `secrets` (`token_hex`, the import allowlist, one comment in the Ed25519
file), a research note recording that Ticketmaster returned 401 for a missing key, and prose saying not to
put secrets in argv. No `.env`, no keypair, no token, no live credential. One thing to decide rather than
fix: several files under `records/` already carry absolute paths rooted in a personal home
directory, and they are
in the tree a judge will read. That is your call, not a defect this checklist can repair.

**3. README.**
There is no root README. Write it, with: what this is; the one command to run the backend; the endpoints;
what Solana is doing here and that it is not deployed; the licence line; the test command; the AI
disclosure; and the screenshots note (none, and why). Keep it free of absolute personal paths, since the
records/ tree is not. Pass: a stranger in a fresh shell runs
`python3 -m ticketpath.server`, gets a line with `listening on http://127.0.0.1:8788`, and `curl -s
127.0.0.1:8788/health` returns 200 with `"synthetic": true`.

**4. Licence.**
Add `LICENSE` with the licence chosen in T6, and one README line naming the same licence.
Pass: `head -3 LICENSE` matches the README, and the GitHub API returns that licence after the push.

**5. On-chain honesty.**
`git grep -n 'deployed' -- '*.md'` and read every line.
Pass: every occurrence is a negation or a design label ("no program is deployed", "designed, not
deployed"), no address is presented as ours, no signature appears anywhere, and no sentence says the hook
is enforcing anything. Then `git grep -nE '[1-9A-HJ-NP-Za-km-z]{32,44}'` and confirm every long string is
either a `SYN` placeholder or a protocol program id (Token-2022, Memo) that we do not own.

**6. The labels.**
On the machine serving the demo, for each of the four screens that print a number:
```bash
for p in "/" "/events/evt_syn_02" "/organizer?event=evt_syn_02" "/tickets/tkt_syn_0001"; do
  curl -s "http://127.0.0.1:3001$p" \
  | python3 -c 'import sys,re,html; t=sys.stdin.read(); b=re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>"," ",t); print("SYNTHETIC FIXTURE DATA" in re.sub(r"\s+"," ",html.unescape(re.sub(r"(?s)<[^>]+>"," ",b))))'
done
```
Pass: four `True`. The console now exists, so add the console itself, whose strip is the first element on
the page:
```bash
curl -s "http://127.0.0.1:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2" \
| python3 -c 'import sys,re,html; t=sys.stdin.read(); b=re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>"," ",t); s=re.sub(r"\s+"," ",html.unescape(re.sub(r"(?s)<[^>]+>"," ",b))); print(s.count("SYNTHETIC FIXTURE DATA")>0, "[UNVALIDATED]" in s, "Recommended primary price: at least 1.38 SOL per ticket" in s)'
```
Pass: `True True True`. The three label tests in `BUILD-SPEC-NIGHT.md` §2.7 are now mandatory rather than
conditional, and the fixture strip must still be the first element on the console page.

**7. `/health` and the console both tell the truth.**
`curl -s 127.0.0.1:8788/health` and `curl -s '127.0.0.1:8788/?event=evt_syn_02&tier=tier_stg_general&capBps=1500&tau=0.2'`.
Pass, on `/health`: `pricingModel.available` is `true`, `pricingModel.modelVersion` is
`engine-2026-11-07`, `pricingModel.kind` is `rule-based-bounded-estimator`, `pricingModel.fitted` is
`false`, `chain.programDeployed` is `false`, `chain.programId` is `null`, `chain.designDoc` is
`docs/ON-CHAIN-DESIGN.md`, and `dataSource.synthetic` is `true`. Pass, on the console: the recommendation
reads `Recommended primary price: at least 1.38 SOL per ticket, General tier.` under an `[UNVALIDATED]`
badge, and the word `floor` appears with it. This item previously required `available: false`; that was
true of the pre-console build and is now the failure condition, so read the four `pricingModel` fields, not
the old one.

**8. The video.**
Play it in a private window on a machine that is not the one that recorded it.
Pass: under 2:00; the hackathon's name spoken in the first sentence; the console screen in frame with its
recommendation, its `[UNVALIDATED]` badge and its fixture strip; no `Mock data` banner; the
`SYNTHETIC FIXTURE DATA` strip legible on every screen that shows a number; no Explorer page; the URL plays
while logged out and will stay public. Reachability: the console in the video is the local address, and a
judge cannot open it, so no frame may imply otherwise and the Demo URL field follows T3 and T11 rather than
the video.

**9. The form.**
Fill every field from §3. Pass: no URL in the form returns a 404 when opened logged out, the track boxes
match §3, the devnet address field is empty, and the confirmation screen or email shows a submission id
captured before 10:00 ET. One paste-time correction, because the console moved under the text: §2.2 still
ends "no price is served: the backend reports `pricingModel.available: false`", and §5 answer 9 still says
the engine outputs nothing. Both were true this morning and are false now. Use the **VERSION-IF-CONSOLE-LANDS**
replacement in §2.3 and §2.5 with them, or drop the last sentence of §2.2 rather than paste it.

**10. Freeze.**
Pass: `git log -1` is unchanged after the video and the URLs are recorded, and nothing is pushed after the
submission unless a judge asks for it.

---

## 5. One-sentence answers to the questions a judge will ask

The five hostile ones first, because they are the ones that decide the entry.

1. **Is this a real market?** No: it is a generated fixture of eight events and seventy-six tickets, made by
   a script in the repo, and the app says so in the visible text on every screen that prints a number.
2. **Where is the data?** `fixtures/synthetic_store.json`, reproducible from `tools/build_fixture_store.py`
   with a fixed seed, because there is no real ledger: the platform's backend does not exist yet and no
   ticket program is deployed.
3. **Why is nothing deployed?** The build machine has no Rust, Cargo, Agave, `solana` or `spl-token` and
   deploying it was not attempted, so what exists is the design, the account layout, the instruction set,
   the error codes, and a Python mirror of the refusals that runs in the test suite, each labelled as
   design or simulated.
4. **What is the AI?** There is no learned model in the running build and no AI track entry: the one
   estimator we would ship is a two-parameter partial-pooling band, it is specified and not fitted, and the
   reason is that no data exists to fit it on.
5. **Is this just a spreadsheet?** A spreadsheet totals a column; this computes a per-ticket custody path,
   measures markup against each ticket's own tier, and the engine is specified to refuse four questions
   outright with the missing observation named for each rather than filling them with a guess. The page
   that prints those refusals is not built yet.

The rest, in the order they tend to come.

6. **Which part did you write?** The Python backend, the fixture generator, the labelling patch and the
   on-chain design; the frontend is the platform's own app, and we say so in the description and in the
   video.
7. **What actually works right now?** Eight events and seventy-six tickets served from our backend into the
   platform's UI, with per-ticket custody trails, resale analytics, and Ed25519 wallet signature
   verification, on 149 passing tests.
8. **Can I click it?** Not without running it: there is no hosted demo and the submission has no demo URL;
   the repo has the two commands.
9. **What does the pricing engine output today?** Nothing: `/health` reports `pricingModel.available:
   false` with the reason `no_model_registered`, and no endpoint serves a price.
10. **Why should the chain be involved at all?** Because the pricing needs its input to be complete: if the
    program writes every custody hop and refuses a price over the cap, the resale record stops having holes,
    and today it has two, a truncated top and sales that leave the sample entirely.
11. **What is the biggest thing that would change the answer?** A record of what unsold tickets were asking:
    four listing fields, and the price response becomes estimable instead of assumed.
12. **What did you learn?** That the binding constraint is identification, not model capacity: every
    flexible model still needs the asking price on tickets that did not sell, and no functional form adds a
    column.
13. **Is the cap enforced?** No. It is organizer policy carried in the record; the program that would
    enforce it is designed and not deployed, and the UI says "Not enforced, no program is deployed".
14. **What is next?** One write on devnet, then a real ledger, then the listing fields, in that order,
    because that is the order in which each one makes the next one mean something.

---

## 6. The counts

- Spoken words, **the script in §1.2**: **264**, six beats, 1:53 of speech at 140 words per minute and
  1:58 with the five beat pauses.
- Spoken words, the obsolete variant A kept in §1.5: **259**, unchanged, because it is kept verbatim.
- TBDs only he can fill: **11** (T1 to T11 in §3). T11 is the console's reachability and it is the only one
  the console adds.
- The TBD that blocks submission outright: **T1, pushing the current tree to the public repo.** The repo
  is public and reachable, but its `main` stops at a commit pushed at 10:27Z and predates every backend
  file, the fixture store and the on-chain design the submission describes.
- Second hard gate, not counted as a decision because it is a task: **T2, the video.** It must exist, be
  under 2:00, and stay public.

---

## Snapshot note — 2026-11-07T12:14Z

**This file is a snapshot of 11:34Z–11:41Z, not a description of the current tree.** Everything
above is kept as written, because the pack is a record of what the submission text said at that
hour. The state table in §0 and the numbers carried into the scripts have moved:

| What the pack says | What is true now | Shown by |
|---|---|---|
| "Pricing console (`ticketpath/console/`): **does not exist**" (§0), and §1's "Variant A (tonight, no console)" script | The console exists at `http://127.0.0.1:8788/` and prints a recommended primary price. §1.3 "Variant B" is the script that matches the running build | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8788/` → 200 |
| "Price served anywhere: **none**" (§0), `/health` → `pricingModel.available: false, reason: no_model_registered` (§0, §1.2 line 129, §2.2 line 230, §4 pass check, §5 answer 9) | `/health` reports `available: true`, `modelVersion: engine-2026-11-07`, `kind: rule-based-bounded-estimator`, `fitted: false`, because the seam is populated by the rule-based bounded estimator. No fitted model is claimed, so the honesty rule the pack obeys is intact; the sentence "nothing is registered" is not | `curl -s http://127.0.0.1:8788/health \| python3 -m json.tool` |
| "149 tests, OK" (§0, and in the submission text at §2.2, §2.6, §3, §5) | `OK`, on a suite that was **293 tests when this pass began and 306 when it ended** (another session was adding console tests throughout). Quote the command's own last line, never this one. | `python3 -m unittest discover -s tests` |
| "Root README: **missing**"; "LICENSE: **missing**" (§0) | Both exist: `README.md` and `LICENSE` (MIT, copyright line still a bracketed placeholder for the operator) | `ls README.md LICENSE` |
| "several files under `records/` already carry absolute paths … That is your call" (§2, no-secrets check) | Done in this pass: `records/`, `docs/`, `tests/` and `tools/` now carry repo-relative paths only, `../ticketing-frontend` for the sibling checkout. `NIGHT-*.md` are untouched by instruction | `grep -rn "hom[e]/" README.md records docs tests tools ticketpath` → no hits outside `NIGHT-*.md` |

What has not changed: the chain state (`programDeployed: false`, `programId: null`), the
frontend's lack of any pricing surface, the absence of a deploy or a screenshot, and the
fixture's synthetic labelling. Every one of those still holds and the scripts still say so.

### Re-timing note — 2026-11-07T12:21Z

Scoped to §1, and to the two checklist sections the console moves. §1 was rewritten against the
running console between 12:19Z and 12:21Z: the script that used to be §1.3 "variant B" is now §1.2 and
is the only one to record, "variant A" is kept verbatim as the obsolete appendix at §1.5, §1.3 is the
re-timed word count, and the old §1.4 "Word counts, printed" folded into it. Two cross-references
inside the 12:14Z snapshot table above therefore point at numbering that no longer exists: "§1.3
'Variant B'" now means §1.2, and "§1.2 line 129" means the obsolete appendix at §1.5, whose text is
unchanged, so its line has moved. §0, §2, §5 and the chain and test-count rows above were left exactly
as they were written, and the console sentences in §2.2 and §5 answer 9 are still false: the paste-time
correction for them is now item 9 of §4. Nothing else in this file was touched, and no other file was
edited.

### Narrowing note — 2026-11-07T15:10Z

Scoped to the pack's pitch. An independent economist's check,
`records/findings/11-cap-capture-check.md` (verdict **STANDS-WITH-NARROWING**), withdrew one sentence the
product claim rested on: **"the resale premium is capturable entirely through the primary price"**. What is
true instead, and what the pack now says: a cap in basis points over face sets a ceiling on the resale price
and, where it binds, divides that price between the organiser's price and the reseller's margin, in the ratio
`1 : c` that no primary price changes; it removes no primary price from the organiser's feasible set and adds no revenue
channel, so the objective needs no capture rate, and the premium is not promised to anyone. The decision is
`F` D7, and the long-form correction is `DELIVERABLE.md` §12.3 with the limitation in §20.3 and the
prohibition in §20.4.

What moved in this file: §1.2 beat 3, spoken and its notes (the cap's role added; the floor-and-ceiling
coincidence explained so a viewer does not read the ceiling as the primary price), the beat table's times
from beat 3 on, §1.3's and §6's word counts, and §2.2. Nothing else was touched. The script is still inside
the 2:00 cap at 1:58, and the two seconds it gave up are the price of the correction: beat 3 went from 43 to
49 words. If the take is tight, §1.3's escape (shorten beat 2 to its first two sentences) is unchanged and
still the first thing to cut. §5 answer 9 and §0's state table are left as written and carry their existing
corrections in the 12:14Z snapshot note and §4 item 9.

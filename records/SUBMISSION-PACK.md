# SUBMISSION-PACK: the video script, the submission text, the field list and the last-hour checks

**Written:** 2026-11-07T11:41Z by the submission session, from its own command output on this machine.
**Target deadline:** initial submission Sun 2026-11-08 **10:00 ET = 15:00Z**. Final 11:45 ET. Treat 10:00
as a hard freeze: nothing published says the initial submission can still be edited after it
(`records/findings/02-rubric-and-scoring.md`, open question 1). **[CORRECTED 2026-11-07T18:55Z: the
platform does publish an edit path — MLH's Hack Days guide describes an "Accept late submissions" switch
that "lets participants submit or edit after the deadline", and the event's own close is 13:00 ET, three
hours after the initial. What was missing was not the edit path but the stop: MLH rules 11 cap hacking at
11:45 ET, allow debugging and small fixes after it, and forbid new features. Hold the 10:00 ET freeze for
the artefact anyway, because 15:00Z is what the entry is judged on, and treat 16:45Z as the last moment
anything may be touched at all. `records/findings/17-hackathon-rules-recheck.md` §1.2 is the source.]**
**The rule this document obeys:** nothing here claims a deploy, a devnet address, a real dataset, an
accuracy figure, a screenshot, or a screen that does not exist. Where the entry is thin, the text says it
is thin. What scores and what does not is decided by `records/findings/02-rubric-and-scoring.md`, and that
finding is the authority here. The 25/25/25/25 weighting is **not** used anywhere in this document, because
it could not be sourced on any MLH or event page (that finding, A5). **[CLARIFIED 2026-11-07T18:55Z: the
list is of things that must not be invented, and it still is. Captures do exist now — §2.5 item five and §3
item 19 point at them — and the rule forbids claiming a screen the build does not have, which is a
different thing.]**

---

## STATE AT 2026-11-08T03:45Z — the devnet write landed, and three numbers in this file moved

Read this block before pasting anything below it. Every line has the command or the endpoint that
produced it, and `records/STATE-OF-PROJECT.md` is the full measurement.

1. **The program is deployed on devnet**, at `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, with a
   Token-2022 mint at `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV` carrying the transfer hook,
   metadata pointer and token metadata. Re-read from the cluster in this pass: `getAccountInfo` →
   `executable: true`; the mint → `decimals 0`, `supply 2`.
2. **The boundary is proven on the cluster, not only in simulation.** 1,250,000,000 lamports admitted
   (`err: null`, slot 519845933, blockTime 1794099006) and 1,250,000,001 refused with
   `InstructionError [0, Custom 6010]` (slot 519846008, blockTime 1794099023), each with its own
   signature, plus a quote memo at blockTime 1794099003. `records/devnet-artefacts.json` is the record.
   At face 1.0 SOL and cap 2,500 bps, the admitted price is exactly `face × 12,500 // 10,000`.
3. **The test count is 610, not 546** (`Ran 610 tests in 23.958s`, `OK`), and the swarm harness carries
   a separate 274 (`Ran 274 tests in 1.028s`, `OK`). Every `546` below is history and any one of them
   pasted into a form is a false statement about the tree.

   **Corrected 2026-11-08T08:30Z: both counts above are stale, and 610 has the same problem the item
   warns about for 546.** Measured on this tree at 08:13Z: `python3 -m unittest discover -s tests -t .`
   → `Ran 1076 tests`, `OK (skipped=26)`; `python3 -m unittest discover -s market_swarm/tests -t .` →
   `Ran 436 tests`, `OK (skipped=2)`. Neither number should be pasted: paste the command's output at
   the moment you run it, or say "the suite the command prints". 610 and 274 were true at 03:35Z and
   are kept as history beside 546; the count had moved again to 1076 by 08:13Z.
4. **§2.5 item one and §2.6's Token-2022 bullet are corrected in place**; §2.4's dated 12:19Z snapshot is
   left as written and marked false of the tree; §3 item 13 (the four-item materials test) and item 16
   (the devnet field on the form) are re-measured, and item 16 now has three identifiers to paste.
5. **T9 is closed.** What remains of it is a paste, not a decision, and nothing may be pasted that is not
   in `records/devnet-artefacts.json`.
6. **Still true and still the weak points:** no hosted demo and no URL; every price and custodian is a
   synthetic fixture; the engine is unvalidated; there is no video; and the deployed program checks the
   cap and nothing else — no hop record, no destination check, no verified-wallet gate, no escrow, no
   nullifier (`programs/cap_hook/README.md`).

---

## Operator actions before 15:00Z — refreshed 2026-11-07T18:55Z

What is now known, in the order the clock forces it. Every line is his to do; none of them can be
settled by editing this file. Measured between 18:40Z and 18:55Z unless a line says otherwise. The
11:41Z list follows this one unchanged, so nothing he wrote earlier is lost; where the two disagree,
this one is the later reading.

1. **The video is the only gate that can lose the entry.** Under 2:00, created this weekend, the
   hackathon named in the first spoken sentence, public for ever (rules 12–13; the cheat-check page
   treats an unpublished video as grounds to re-pick a winner). §1.2 is the script, §1.1 the recording
   path, and the frames it needs now exist on both surfaces: the console renders, and the copy's
   `/pricing` page frames it at 3,383 px over 3,383 px of content at 1280.
2. **Two AI-disclosure fields are required, and the wording is in §2.7.** A required multiselect (the
   GenAI tools used this weekend) and a required long-text field (whether a generative model or API was
   implemented, and how). §2.7 now carries the honest paragraph: agents wrote most of the lines, he
   orchestrated and released them, and it is not a claim of solo human authorship. `TBD-TOOL-NAMES` is
   still his; the commit trailers name one tool on six of nineteen commits.
3. **The repository stays public for ever, and that collides with the ownership question.** Rules 12–13
   and MLH's cheating-response page name making the repo private after the event as disqualifying. A
   company-shaped project cannot both stay public for ever and assert sole ownership of it (§2.8
   question 1). Not answered here, and it must not be guessed at paste time.
4. **The hard stop is 11:45 ET = 16:45Z; the initial submission is 10:00 ET = 15:00Z.** The platform's
   own close is 13:00 ET = 18:00Z and it has an edit path, but the rules cap hacking at 11:45 ET: small
   fixes after that are allowed, new features are not. Treat 15:00Z as the freeze for the artefact and
   16:45Z as the last moment anything at all is touched.
5. **The git history answers the first cheat-check question cleanly.** 19 commits, the earliest
   `744a2c2` at 2026-11-07T08:29:57Z: 15 h 29 min after hacking began and inside the window, spread over
   9 h 43 min in 19 steps, nothing backdated (§2.8). Nine commits carry his own git identity, nine
   `agent <agent@local>`, one `orchestrator <orchestrator@localhost>`.
6. **Screenshots exist, and the sentence that said they did not is corrected in §2.5 item five.** There
   is a headless browser on this machine (`docs/SHOTS.md`, `tools/shot.py`, twelve captures in
   `~/tools/shot/out/` before this pass, a thirteenth taken during it at 18:40Z). The frontend the
   submission shows is the copy's, which carries a `/pricing` attach with 43 checks green at 18:40Z.
   Nothing is hosted, so the video is still the only place a judge sees either surface.
7. **The devnet write (T9) has produced nothing yet, and nothing may be invented for it.**
   `records/devnet-artefacts.json` does not exist at 18:45Z, so the console's `[DEVNET]` slot renders
   empty and `/health` reports `programDeployed: false`, `programId: null`. If the Solana run lands one,
   it is **`records/findings/18` when it lands** (that number is free at 18:55Z, though `findings/17`'s
   header note reserves it for the frontend fix if that finding is written): cite that file and the
   artefact it names, and do not paste a signature from anywhere else. Until then the honest state stays
   "nothing is deployed".
   **[RESOLVED 2026-11-08T03:45Z. The write landed and T9 is closed. `records/devnet-artefacts.json`
   exists and verifies; it names the program `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, the mint
   `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`, the memo signature with its slot and block time, and
   the two transfer legs — one admitted at 1,250,000,000 lamports, one refused with `6010`. The record of
   the work is `records/findings/18` (toolchain, local validator), `records/findings/21` (the hook in the
   tree, the publisher), `records/findings/28` (the resume fix) and `programs/cap_hook/README.md` (what the
   deployed program does and does not do). §3 item 16's form field can now carry these three public
   identifiers — and only these three. `/health` still reports `programDeployed: false` because its chain
   adapter never asks the cluster; that value is not evidence against the deployment.]**
8. **Registration and check-in are machine-checked, and the form fields are §3 items 12 and 20.** Run
   the submit path once early on Sunday rather than at 09:55; the event page shows three steps, register,
   check in, submit, and a registered-but-not-checked-in account may not be able to submit at all. **The
   team is two people, the operator and one teammate, and both accounts must be registered on MLH *and*
   checked in**, not just the one doing the pasting: an unregistered or unchecked-in second member is a team
   of one on paper and an eligibility question on the form. Emails and the state of both accounts are his.
9. **The two answers §2.8 used to leave open are decided and recorded.** Ownership: a two-person team,
   with the code written by AI agents the team directed, disclosed in both required AI fields (§2.7).
   Corpus: `../research/mlh-solana-2026/` is not published, stays local, and is quoted nowhere beyond the
   attributed citations already in `records/00-prior-direction-index.md`. Both are written out in §2.8,
   and `records/F-decision-log.md` D8 is the decision of record. **[CORRECTED 2026-11-07T18:55Z: this item
   called the corpus "pre-event" and said neither answer existed. The fifteen documents were written
   17:39–18:49Z on 2026-11-06, inside the window and not before it — `records/findings/19-corpus-citations.md`
   §5 measures it, and `records/findings/17-hackathon-rules-recheck.md`'s closing CORRECTION states it.]**
10. **After the submission:** capture the confirmation id, freeze the tree, change nothing until a judge
    asks. The pack's own rule still holds: no push happens without his explicit yes.

---

## Operator actions before 15:00Z (the 11:41Z list, kept as written; the refreshed list above supersedes it)

Every line here is his to do; nothing below can be settled by editing this file. Ordered by what
decides the entry soonest. The correction pass of 2026-11-07T17:45Z fixed the text these actions
point at, and `records/findings/13-submission-readiness.md` is the finding behind both.

1. **Decide T11 (console reachability) before recording, not after.** With no tunnel and no
   deploy the console is seen only in the video, and no frame may imply a judge can open it. This
   one decision sets the video framing and the Demo URL field at the same time.
2. **Record the video from §1.2 as amended by findings 11 and 12** of
   `13-submission-readiness.md`: under 2:00, "MLH Solana Hackathon" in the first spoken sentence,
   the hackathon name and the repo URL in the end card. It is the one gate whose failure is
   ineligibility rather than a lost point. T8 (which machine, LAN path A or path B) is part of
   this step.
3. **Fill `TBD-TOOL-NAMES` in §2.7** (`:417`) with the tools he actually ran, and put the same list
   in the form's AI-disclosure field. Naming the wrong tools is worse than naming none.
4. **Fill the form's operator fields** (§3 items 12 and 20, T4): team names, emails, MLH accounts,
   school, country, code-of-conduct agreement. Leave the devnet program/mint/address field empty
   (item 16), and the Demo URL per T3 and T11 (item 5).
5. **Decide T5** (first-time-hacker status, which decides Best Beginner) and **T9** (whether to
   attempt the one devnet memo write). Both change what the form says and neither changes what the
   repo does. **[T9 IS CLOSED 2026-11-08T03:45Z: the write was made and the artefacts verify. What is left
   of it is not a decision but a paste — the three public identifiers in item 7 above.]**
6. **Delete the remote branch** `refs/heads/wip/mode-sentences-20261107T1650Z` if a judge reading
   "branches" should not find a branch named after an unfinished sentence fix. Measured on the
   remote at 17:36Z.
7. **Confirm the licence holder name** in `LICENSE` is the name he wants on a public repo. T6 is
   otherwise closed: `LICENSE` is on `main` and the copyright line is filled.
8. **After the submission:** capture the confirmation id, freeze the tree, change nothing until a
   judge asks. The working tree carries an uncommitted `NIGHT-LOG.md` and the untracked
   `records/findings/13-submission-readiness.md`; neither belongs in a submission commit.

---

## 0. The state this pack is written against, measured between 11:34Z and 11:41Z

Every line below was produced by a command in this session, not carried from another record.

| Thing | Measured state | Where |
|---|---|---|
| Backend | running on this machine, loopback port 8788, `/health` 200 | `curl /health` |
| Backend store | **8 events, 76 tickets** (the regenerated store, not the old 2-event one) | `GET /api/events?limit=100` |
| Frontend demo copy | running on its own port, honesty patch applied, notice visible in the served text | `../ticketpath-demo`, `curl` that port |
| Live frontend (his) | running on its own port, untouched, mock mode | not ours |
| Screens carrying backend numbers | `/`, `/events/evt_syn_02`, `/organizer?event=evt_syn_02`, `/tickets/tkt_syn_0001` | served HTML, tag-stripped |
| Pricing console (`ticketpath/console/`) | **does not exist** | `ls ticketpath/` |
| Price served anywhere | **none**: `/health` → `pricingModel.available: false, reason: no_model_registered` | `/health` |
| Chain | `programDeployed: false, programId: null, rpcEnabled: false` | `/health` |
| Test suite | `python3 -m unittest discover -s tests` → **610 tests, OK** **[AMENDED 2026-11-08T03:45Z: `Ran 610 tests in 23.958s` at `HEAD 33d95b3`; the swarm harness adds a separate 274. Earlier readings: 546 at 18:11Z, 453 at 17:36Z]** | run in this session |
| Root README | **missing** | `ls README*` |
| LICENSE | **missing** | `ls LICENSE` |
| Repo | public, `andy1245-rgb/ticketpath`, created 2026-11-07T10:25Z; `LICENSE` is MIT with the holder filled in **[AMENDED 17:36Z: the `license: None` reading was true at 10:25Z and is not any more]** | GitHub API |
| Remote vs local | remote `main` = `375126f` = local HEAD, so the public repo is the verified tree **[AMENDED 17:36Z]**. It carries the backend (41 files under `ticketpath/`), `README.md`, `LICENSE`, `fixtures/synthetic_store.json`, `docs/` and the research records. No push is outstanding; the working tree has an uncommitted `NIGHT-LOG.md` that stays out of a submission commit | `git ls-remote origin`, `git ls-tree -r --name-only HEAD \| wc -l` → 148 |
| Browser on this machine | none (no chromium, firefox, playwright, puppeteer, selenium) | probed in this session, and `DEMO-PROOF.md` §5 |
| Devnet from this machine | reachable: `getVersion` → `solana-core 4.4.0`; Token-2022 program account exists, `executable: true`, slot 519647005 | `curl api.devnet.solana.com` |

Four more rows in that table were true at 11:41Z and are not now: the console **does** exist, a price **is**
served, a root README and a `LICENSE` **do** exist. The 12:14Z snapshot note at the end of this file corrects
all four, and the rows are kept as written because this section is a record of the hour it names.

Two consequences, and they shape everything below.

1. **The console is not built, so there is no screen that shows a decision.** The video script is written
   for the state that exists, with one clearly marked swap-in block for the day the console lands.
   **[AMENDED 17:45Z: both halves are now false. `ticketpath/console/` exists, `GET /` serves it at 200,
   and §1.2 is the script that matches it. The paragraph is kept as the 11:41Z reading.]**
2. **The public repo is behind the work.** A judge who follows the project link tonight finds Phase 1
   documents and no backend. That is the single most damaging thing about the current state, and it is a
   `git push` away from being fixed. It is your click.
   **[AMENDED 17:36Z: this is no longer true. Remote `main` is `375126f`, the commit this pack's own
   checklist verified, with the backend, the fixture store, the console and the research records in it.]**

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

**[Corrected 2026-11-08T08:05Z: the second half of row 5 is false on the screen and in the tree.** A program is deployed on devnet (`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`), and the frontend no longer prints "Not enforced, no program is deployed". Read the row as "this server did not determine whether the transfer is enforced, because it reads no chain", and see `docs/ON-CHAIN-DESIGN.md` section 0 for what the deployed v1 does and does not enforce.]**
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
`9 at the ceiling`, `8 events in the store`, `5 with any resale at this instant`, `0 on-chain transactions`,
each carrying its own `[FIXTURE]` or `[DEVNET]` tag. The two lines
doing the work are `[EXACT] ceiling 1,380,000,000 lamports = face 1,200,000,000 lamports × (10,000 + 1500) /
10,000 — integer arithmetic on the tier face, not an estimate. That is exactly 1.38 SOL.` and `[UNVALIDATED]
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

**[Corrected 2026-11-08T08:05Z: the badge list above says `0 on-chain transactions`; the page now prints `3`, because the evidence count is the number of signatures the artefact carries (three), not one per verified file. The sentence has been left as written.]**

**The block that sits in the middle of the frame.** Between the `[UNVALIDATED] The decision` badge and the
`[UNVALIDATED] Recommended primary price` line the page prints a `[UNVALIDATED] Decision mode:
COUNTERFACTUAL` block ending `and it is not a price you could have set.` It is the newest sentence on the
page and it lands before the number it qualifies: keep it in frame, do not read it aloud, and do not scroll
it half off. Measured on a fresh instance at HEAD `375126f`: `127.0.0.1:8813`, 13,726 bytes on `/`.

**What is now in frame for free, and this is not in the script above.** The console's `[DEVNET]` slot is
empty for every state except one, and it is worth one line on camera because it is the only screen in the
submission that carries a devnet signature. Add `&asOf=2026-11-07T18:34:29.183Z` to the Beat 3 URL — the
instant and the identifiers are the recorded ones — and the slot at the bottom of the page renders
`[DEVNET] Verified at … against api.devnet.solana.com`, the signature, the slot and the block time.
Measured 2026-11-08T03:40Z: that URL returns 200, 14,275 bytes, and the signature string is in the body.
Two cautions, both measured: the verification instant renders as the literal string `None` (a defect in the
page, not in the record; `records/STATE-OF-PROJECT.md` §A6 item 1), so do not read that line aloud; and any
other `asOf` renders the slot as unverified, which is correct but is not the shot you want.
**[ADDED 2026-11-08T03:45Z: measured this pass, not in the 12:19Z script.]**

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

**[Corrected 2026-11-08T08:05Z: the `Transfer restriction` row no longer reads that sentence, and the claim behind it is false. A program is deployed on devnet; the row says this server did not determine enforcement because it reads no chain. The mint is still a placeholder in the fixture. The paragraph above is kept as the description it was written as.]**

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

- The `Mock data` banner, six `lib/mock` events, or Chicago and Indianapolis. Those are the live frontend's
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

**[ADDED 2026-11-08T03:45Z: this variant is now obsolete in two more places, and beat 3 and beat 5 are
the ones that could be recorded by mistake. Beat 3's on-screen line "Not enforced, no program is
deployed" and beat 5's "Nothing is deployed" are false of the tree: the program is deployed on devnet and
the cap boundary is proven there. Do not record this variant. If you want the refusal beat, take it from
§1.2, which is the script to record.]**

| Beat | Time | On screen (exact) | Must land |
|---|---|---|---|
| 1 The problem | 0:00 to 0:23 | `http://<host>:3001/organizer?event=evt_syn_02`, the "Resale analytics" panel, scrolled to the four stat tiles | **22.03 SOL across 12 sales, average markup +12%, cap is +15%**, all three visible at once |
| 2 The thing that runs | 0:23 to 0:57 | same page, then tab 2: `http://<host>:8788/api/events/evt_syn_02/analytics` | the JSON shows **`"saleCount": 12`** and **`"avgMarkupBps": 1233`**, the same numbers as the page |
| 3 The on-chain invariant | 0:57 to 1:18 | `http://<host>:3001/tickets/tkt_syn_0001`, the "Custody trail", then the "On-chain (simulated)" card | the invariant sentence, then **"Not enforced, no program is deployed"** on screen |

**[Corrected 2026-11-08T08:05Z: the quoted on-screen sentence is gone and the claim behind it is false.** The ticket page no longer says no program is deployed, and one is. What is true, and what the voice-over should say, is that this server did not determine enforcement because it reads no chain; the deployed v1 enforces the price predicate and nothing else, and its staging instructions take no signer (`docs/ON-CHAIN-DESIGN.md` section 0). Keep the beat, change the words.]**
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
**VERSION-IF-CONSOLE-LANDS** and nothing else in the text has to move. **[The console landed. Both marked
lines were applied at 17:45Z: §2.3 now carries the console paragraph, and §2.5 item three was replaced. The
marks are kept so the record shows what was conditional and when it stopped being so.]**

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
> Ed25519 wallet signature verification, on a 610-test suite that passes (`python3 -m unittest discover -s
> tests`, `Ran 610 tests in 23.958s`, `OK`). It also serves a console that
> reads one event's resale record and gives a floor on the primary price from it, labelled a floor and not
> an estimate, and it states the cap's role correctly: a cap in basis points over face sets the ceiling on
> the resale price and, where it binds, fixes how that price divides between the organizer's price and the
> reseller's margin, and it does not set the primary price. The ledger is a generated fixture and not ticket data, and
> every screen says so in the visible text. A ticket program is deployed on devnet and it refuses a resale
> above the cap there, with a landed transfer and a refused one one lamport apart to show it; the rest of
> the design — the hop record, the destination check, the verified-wallet gate — is designed and simulated,
> not deployed.

**[CORRECTED 2026-11-08T03:45Z in this pasted paragraph, two places: the suite is 610 tests, not 546,
and the closing clause about no program being deployed is rewritten because one is. Nothing else in the
paragraph changed, and it is safe to paste as it now reads. The measurements and the three public
identifiers are in the state block at the top of this file.]**

**[REWRITTEN 2026-11-07T15:10Z — two sentences replaced, and the old wording is kept for the record.** The
closing sentence ("no price is served: the backend reports `pricingModel.available: false`") was true at
11:41Z and false once the console landed; it is quoted in §4 item 9 and in the 12:14Z snapshot note. The
cap sentence states the narrowed result and replaces "the resale premium is capturable entirely through the
primary price" (`11-cap-capture-check.md` §9, §11.1; `F` D7): the cap fixes the split of the resale price,
`1 : c`, and does not set the primary price. **[AMENDED 17:45Z: the test count in this paragraph is now
546, measured at HEAD with `python3 tools/tp.py gate` (`tests=546 OK`, 18:11Z) and with the command beside
it so the two cannot drift; §5 answer 9 is
rewritten too and §4 item 9's instruction was re-pointed at findings 1, 2 and 5 of
`13-submission-readiness.md`.]**

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
>
> The second surface is a server-rendered console at `/`, served by the same Python backend: it states
> the recommended primary price for a selected event and tier, shows the evidence counts the answer
> rests on, prints a `[UNVALIDATED]` badge on the recommendation and a `[REFUSED]` block naming each
> question the record cannot answer.

**[APPLIED 17:45Z: the console landed, so the VERSION-IF-CONSOLE-LANDS paragraph at :365-367 is now part of
§2.3 above, with the badge and refusal details the video shows added. It is the surface §1.2 beat 3 puts in
frame for 21 seconds, and the description a judge reads could not find it.]**

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
> cluster, only by reading the design and the simulation in the repo. **[REPLACED 2026-11-08T03:45Z: this
> is false of the tree. A program is deployed on devnet at
> `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, a Token-2022 mint with the transfer hook is at
> `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`, a quote memo landed with a block time, and a transfer
> at 1,250,000,000 lamports was admitted and one at 1,250,000,001 refused with `6010` as a failed
> transaction with its own signature. `records/devnet-artefacts.json` holds the record and this pass
> re-read it from the cluster. What replaces the sentence, and is the honest form of the same item: the
> deployed program checks the cap and nothing else — no hop record, no destination check, no
> verified-wallet gate — so a judge can confirm the cap claim by looking at a cluster and cannot confirm
> the rest of the invariant.]** Second, there is no real data. The
> record is eight events and seventy-six tickets generated by a script in the repo; it is internally
> consistent and it is not evidence about any market, and the screens say so. Third, the pricing engine is
> unvalidated. A console page served at `/` prints a recommended primary price for the selected event, and
> that number is a bound with a declared width computed from the fixture's own resale rows: no parameter was
> estimated from real data, `/health` reports `fitted: false`, and the page tags the recommendation
> `[UNVALIDATED]`. Fourth, there is no hosted demo. The app runs locally and the run steps are in the repo; the
> submission has no demo URL, and clicking the project link will not show a running product. Fifth, there
> are no screenshots in this submission, because the build machine has no browser. The frontend that a
> judge would see is the platform's own, and the labelling patch is ours. **[REPLACED 2026-11-07T18:50Z:
> both halves of that sentence were false of the tree. There is a headless browser on this machine —
> `docs/SHOTS.md` is the account (Playwright and a Chromium headless shell under `~/tools/shot/`, outside
> the repository, a dev tool the backend never imports) — and `tools/shot.py` captures a page in one
> command. Twelve PNGs sat in `~/tools/shot/out/` when this pass began; a thirteenth was taken during it
> (`python3 tools/shot.py http://127.0.0.1:8788/ <path> --width 1280` → a 139,390-byte PNG at 18:40Z). The
> frontend a judge would see is the copy's, and it carries more than a labelling patch: a `/pricing` page
> that frames the console through a closed proxy, `python3 tools/check_frontend_attach.py` → **43 passed,
> 0 failed** at 18:40Z, a sandboxed frame measured at **3,383 px of frame over 3,383 px of console at
> 1280** and 7,143 over 7,143 at 390 with no scrollbar inside it (measured 18:41Z), and a containment
> policy on the proxy. What survives from the old item: the demo is local, nothing is hosted, so no
> screenshot and no URL puts either surface in a judge's browser — the video is the only place they
> travel.]**

**[APPLIED 17:45Z: item three is replaced with the paragraph above, which is the "VERSION-IF-CONSOLE-LANDS"
swap-in that used to sit here — the swap-in text added "on every number it prints", which the page does not
claim, so the wording above is the one to paste. Verified against `/health` on a fresh instance at HEAD
`375126f`: `pricingModel.available: true`, `modelVersion: engine-2026-11-07`, `kind:
rule-based-bounded-estimator`, `fitted: false`.]**

### 2.6 Built with

- Python 3.12, standard library only, no package installed
- The platform's own Next.js frontend, unmodified in layout, plus our text-only labelling patch
- Node 24 and the Next dev server, for the demo copy on port 3001
- Token-2022 and a transfer-hook program: **deployed on devnet** at
  `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, with the hooked mint at
  `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`; the cap check is the part that is deployed, and
  `programs/cap_hook/README.md` says what is not. **[REPLACED 2026-11-08T03:45Z: this bullet read
  "Token-2022 and a transfer-hook design, not deployed".]**
- Ed25519 signature verification, implemented in the repo
- A deterministic fixture generator (seed 20261107) and a **610-test** unittest suite (`python3 -m unittest
  discover -s tests`, `Ran 610 tests in 23.958s`, `OK`), plus a separate **274-test** suite for the swarm
  harness (`python3 -m unittest discover -s market_swarm/tests`) **[corrected from 546, 2026-11-08T03:45Z]**
- No Solana RPC in the running build: the chain adapter is off by default and opens no socket
  (`/health` reports `rpcEnabled: false`, `reason: rpc_disabled`). The devnet reads in §2.4 were made by
  hand with `curl` from the build machine, are recorded there, and are not performed by the app. **[Replaces
  the entry "Solana JSON-RPC over HTTPS, devnet, read only", 17:45Z: that listed as a building block
  something the running product never touches.]**
- AI coding agents, disclosed below

### 2.7 AI disclosure (required, and the penalty for omitting it is disqualification)

**Rewritten 2026-11-07T18:50Z.** The version it replaces said "Most of the code and most of the documents
in this repository were written with AI coding agents (`TBD-TOOL-NAMES`) working under a written brief, in
parallel sessions", which is close to true and hides the two things a judge would ask about: who was in
charge, and whether the operator wrote it. What the form asks, from MLH's own required export, is a
required multiselect — "Which of the following GenAI tools did you use this weekend?" — and a required
long-text field — "Did you implement a generative AI model or API in your hack this weekend? If so, how
and why did you use it? If not, mark your response as N/A" (`records/findings/17-hackathon-rules-recheck.md`
§1.3). Both are on the form whether or not this file is read.

The wording to paste, honest and complete, with the one line only he can fill:

> The code and the documents in this repository were built with AI coding agents, orchestrated and
> released by me. Agents wrote most of the lines: the backend, the engine, the console, the test suite,
> the research records and this submission text. I wrote the briefs, directed the phases, checked the
> claims against the commands that produced them, and made every decision that ships. The tool list is
> `TBD-TOOL-NAMES`; the commit trailers in the repository name one of them on six of its nineteen commits.
> No generative model or API is implemented inside the product: the pricing engine is bounded arithmetic
> with declared parameters, `/health` reports `fitted: false`, and the only learned-model work here is
> specified and unbuilt. This is not a claim of solo human authorship and no part of the submission should
> be read as one.

What makes that paragraph defensible rather than just honest: the git history agrees with it. Measured at
18:45Z, the repository has **19 commits**, nine under the operator's own git identity, nine under
`agent <agent@local>` and one under `orchestrator <orchestrator@localhost>`, and six carrying a
`Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` trailer. A judge who runs `git log` finds the
same story the disclosure tells.

MLH's published rule asks teams to be honest and transparent about which AI code tools they used and to
list them in the submission; the organizer-side copy attaches disqualification and a report to
`cheating@mlh.io`. Naming the wrong tools is worse than naming none, so `TBD-TOOL-NAMES` stays yours to
fill.

---

### 2.8 Provenance, prior work, and the two answers recorded on 2026-11-07

**Added 2026-11-07T18:50Z**, from `records/findings/17-hackathon-rules-recheck.md` §3.4, §3.9, §6 (R1, R5,
R6) and §7. **Amended 2026-11-07T18:55Z:** the two questions at the end were open when this section was
written and both are now decided by the operator — the team two names, the corpus unpublished and
unquoted beyond attribution — so the section states the answers and the provenance sentence the answers
allow. `records/F-decision-log.md` D8 is the decision of record.

**The provenance sentence, for the description and for the video.** The largest prior-work exposure in this
entry is not code, it is a claim about who built what: the demo UI is a copy of the company's own platform
frontend. The sentence to carry, in the submission text and once in the voice-over:

> The surrounding product UI is the company's own ticketing platform frontend, which existed before this
> weekend and which I did not build. What was built in the hackathon window is the pricing backend, the
> engine, the console, the CLI, and the `/pricing` integration that puts the console inside that frontend.

What must not be said, in any frame or field: that the frontend was built this weekend. Rule 9 of MLH's
rules allows a prior idea "as long as they do not re-use code or other project materials", and submission
rule 6 says "You can not submit a project that includes prior work". Presenting an inherited UI as a
weekend build is the one thing in this entry that can cost it, and one plain sentence removes it.

**The git history, on the two checks MLH's cheat-check page actually runs.** Measured 2026-11-07T18:45Z:
19 commits, the earliest `744a2c2` at 2026-11-07T08:29:57Z, which is 15 h 29 min **after** hacking began
(Friday 2026-11-06 12:00 ET = 17:00Z) and inside the window; the commits are spread over 9 h 43 min in 19
steps, so it is not one blob at the start and not one blob at the end; nothing in the tree is backdated.
The two published questions, answered from the repository rather than from memory: "Did they start before
the event?" — no. "Is it one big commit at the beginning of the event?" — no.

**The provenance of the background reading, in two forms, and the sentence the submission pastes.** The
reading is fifteen documents in `../research/mlh-solana-2026/`, written between 17:39:04Z and 18:48:55Z on
2026-11-06. Hacking began at 17:00Z that day, so the reading sits **inside** the window: 39 minutes to 1 h
49 min after it opened, not before it. This file used to call that corpus "pre-event" and "written the day
before hacking began" in three places; all three are corrected here, and the correction is the stronger
position, because notes taken inside the window are permitted by rules 6 and 9 and notes taken before it
are the thing the prior-work rule exists to exclude.

Long form, for the description field and the video description. Paste as written:

> **Provenance.** Background reading for this entry was done between 17:39 and 18:49 UTC on 6 November
> 2026, inside the first two hours of the hackathon window and not before it. Those fifteen documents are
> not in this repository and are not published. No code and no submitted artefact derives from them. What
> the research record does is cite them, with attribution on the line that cites them, including the short
> passages it quotes where it records a decision they settled. The code and every committed artefact were
> written from 08:29 UTC on 7 November 2026, fifteen and a half hours after hacking began, and every commit
> in this repository post-dates the opening ceremony.

Short form, for a form field with a character limit:

> All code in this repository was written inside the hackathon window, from 08:29 UTC on 7 November 2026.
> Background reading done in the first two hours of the window is not published and is not part of the
> submission; the research record cites it with attribution.

Both rest on two measurements anyone can re-run: `stat` on the fifteen files (first `03-what-wins-solana.md`
at 17:39:04Z, last `p1b-tech-feasibility.md` at 18:48:55Z) and `git log` (first commit `744a2c2` at
2026-11-07T08:29:57Z). **Do not say**, in any field or frame: that the research was done before the event;
that those documents were written the day before hacking began; or that no text from them appears in this
repository. The first two are false against the file times, and the third is false because
`records/00-prior-direction-index.md` quotes them with attribution on every line that quotes, 17 of its
lines carrying verbatim text. That index is deliberately **not** trimmed: the quotations are attributed
citations, and removing them would buy a sentence nobody needs at the cost of the record's evidence.

**Question 1, ownership — answered 2026-11-07, and the collision is dissolved rather than argued.** MLH's
contest terms require that "An Eligible Participant (or team) must be the sole owner of the Application
submitted". The Application is a **two-person team entry, the operator and one teammate**, so "or team" is
the clause that applies and the team owns what it submitted; rules 12–13's public-for-ever requirement is
satisfied by the same two people keeping the repository public. The code in it was written by AI agents
that the team directed and released, which is disclosed in both required fields (§2.7) and is not a claim
of human authorship by either member. What this answer does not reach: if the pricing work is also company
work, company ownership and "sole owner" still collide and the team needs the company's written
permission before Sunday. That is the one part of question 1 that is still his, and it is recorded as open
in `records/findings/17-hackathon-rules-recheck.md` §7 item 1.

**Question 2, the research corpus — answered 2026-11-07: not published, and not quoted beyond attribution.**
`../research/mlh-solana-2026/` is fifteen documents written between 17:39:04Z and 18:48:55Z on 2026-11-06,
inside the hackathon window, not the day before it. The decision is that the corpus is **not published and
stays local**, and that nothing in it is quoted in the submission text or the video beyond the attributed
citations that are already committed. Leaving it out of the repository is still the mitigation, because a
prior *idea* is allowed and prior *materials* are not; it was never in the tree, and it stays out. So the
honest formulation is not "no text from those notes appears in this repository" but the one in the
provenance block above: the code and every committed artefact were written from 08:29Z on 2026-11-07, and
the research record cites the background reading with attribution. Whether the corpus drew on company or
private data is the one part still his to confirm, and it is the only fact that would change the answer:
`records/findings/19-corpus-citations.md` §4 measured it for credentials, keypairs, personal detail and
third-party non-public material and found none, which is absence of those shapes and not proof of clean
provenance. That file is the audit of every place in this repository that names, cites or reproduces the
corpus, and it is committed with this note.

---

## 3. The field checklist

Every field a Devpost-style or MLH Challenges form asks for, what goes in it, and who supplies it. "Set"
means the text is in this document and needs no decision. "TBD" means only he can decide or confirm.

| # | Field | What goes in it | Who |
|---|---|---|---|
| 1 | Project name | `Ticketpath` | set (a rename is your call) |
| 2 | Elevator / short description | one sentence from §2.2 | set |
| 3 | Project link (repo URL) | `https://github.com/andy1245-rgb/ticketpath` | URL set, **content pushed: remote `main` is `375126f`, the verified tree** |
| 4 | Video URL | public link to the file recorded from §1 | **T2** |
| 5 | Demo URL | still none: the console runs on a loopback address a judge cannot open, so the field stays blank or points at the repo's run steps and says the demo is local. The console does not change this answer, and turning it into a real one is **T11** | **T3, T11** |
| 6 | Description | §2.2 | set |
| 7 | How it works / technical description | §2.3 | set |
| 8 | What is on-chain | §2.4, verbatim | set |
| 9 | What is not done | §2.5, verbatim | set |
| 10 | Inspiration / challenges / accomplishments / what we learned / what's next | accomplished: 610 tests, real signature verification, a labelling patch that makes an inherited UI tell the truth, a program deployed on devnet whose cap boundary is proven there by a landed transfer and a refused one. Learned: the asking price is the missing observation, and no model fixes a missing column. Next: a real ledger | set **[610 corrected from 546, and the devnet clause added, 2026-11-08T03:45Z]** |
| 11 | Built with / technologies | §2.6 | set |
| 12 | Team members, names, emails, MLH accounts | **Two people: the operator and one teammate.** Both must be registered on MLH and **checked in**, or the second account may not be able to submit at all (§0 item 8). Both names are on the team field and in `LICENSE`, not in this file (see the note below); emails and account state are his | **T4, names set** |
| 13 | Track: Top 3 Overall | select, knowing the score. The criterion is applied by looking for four things. **[RE-MEASURED 2026-11-08T03:45Z — the sentence that followed this point used to say the repo has none of them, 0 of 4. Two of the four are now met and two are partial, and `records/findings/29` §1 reaches the same reading. What each is now: an account that belongs to the project — MET, the program id above resolves as `executable: true` on devnet; a transaction signature with a block time — MET, three of them, block times 1794099003 / 1794099006 / 1794099023, while every fixture ledger row still carries `signature: null`; a program the team did not write doing work the product depends on — PARTIAL, Token-2022 processes each transfer and calls this project's hook inside it, and the shipped app still calls no chain; the product reading that state back — PARTIAL, the console renders the recorded artefact after recomputing its quote hash, and `rpc_adapter.py` still opens no socket, so it is a recorded read. The realistic path is still MLH's own four-part rubric, where the console is the interface the build did not have.]** Measured in `13-submission-readiness.md` §4 and re-measured in `records/STATE-OF-PROJECT.md` §A2 | set |
| 14 | Track: Best Beginner | eligible only if more than half the team are first-time hackers | **T5** |
| 15 | Track: AI, DeFi, Gaming | recommend none. There is no AI component in the build, no payment or lending surface, and no game | set (your veto) |
| 16 | Devnet program id / mint / address field | **fill it now.** The program is deployed: `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, with the hooked mint `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`, and the memo and transfer signatures are in `records/devnet-artefacts.json`. Paste only those recorded identifiers. An invented address is the one lie that would sink the entry | set **[CHANGED 2026-11-08T03:45Z: this row said "leave empty. Nothing is deployed."]** |
| 17 | Licence | MIT, in `LICENSE`, copyright line filled with the holder's name. Nothing to decide; confirm the name is the one he wants on a public repo | **T6, confirm only** |
| 18 | AI tool disclosure | §2.7 | **T7** |
| 19 | Screenshots / thumbnail | **captures exist** — twelve PNGs in `~/tools/shot/out/` before 18:40Z and one more taken during this pass, from the copy and from the console at 1280 and 390 (`docs/SHOTS.md`, `tools/shot.py`). Whether any go in the form is his call: the video is what a judge watches, and the form's own screenshot field was not visible without an account. The thumbnail still comes from the video platform. **[CORRECTED 2026-11-07T18:55Z: this row used to say "none exist", which was false of the build machine.]** | set (his veto) |
| 20 | Country, school, code-of-conduct agreement, account linking | form filler | your clicks |

### The TBDs, numbered, and what each one is

- **T1 Push the current tree to the public repo.** **CLOSED, measured 17:36Z.** Remote `main` is `375126f`, which is local HEAD, 148 tracked files, carrying the backend (41 files under `ticketpath/`), the fixture store, the console and the research records. Nothing is outstanding. What remains is not a push: the working tree holds an uncommitted `NIGHT-LOG.md` and the untracked `records/findings/13-submission-readiness.md`, and neither belongs in a submission commit. No push happens without your explicit yes.
- **T2 The video URL.** Does not exist. Must be recorded this weekend from §1 and must stay public.
- **T3 The demo URL field.** No hosted demo. Either blank, or the repo with a plain note that it runs locally. The console does not change this: it is served on `127.0.0.1:8788`, which is his machine and not a judge's (T11).
- **T4 Team.** **Names closed 2026-11-07: two people, the operator and one teammate**, named on the MLH team field and in `LICENSE` rather than here. Open on the accounts: both need an MLH registration *and* a check-in, and the emails on the two accounts are his to confirm. One member registered and one not is a one-person team on the form.
- **T5 First-time-hacker status**, which decides Best Beginner eligibility (>50% of the team).
- **T6 Licence.** **CLOSED, measured 17:36Z.** `LICENSE` is on `main` and is MIT; line 3 names the copyright holder. There is nothing to decide. Confirm the name is the one he wants on a public repo, and the README line matches the file.
- **T7 AI tool names** for the disclosure in §2.7.
- **T8 Recording machine and path** (§1.1 A or B), and whether the backend may bind to the LAN address.
- **T9 Whether to attempt the devnet write.** One memo transaction carrying a hash of a quote, run by him on a laptop with Agave, then read back and verified. It would turn "design" into "a real transaction with a block time" (`BUILD-SPEC-NIGHT.md` §5.6 option c). It costs about an hour of his time and a few thousandths of a devnet SOL. If he does not do it, the honest state is "nothing is deployed" and the submission is complete without it.
- **T10 Whether the honesty patch goes into the live frontend tree** and gets a restart of the live frontend. The patch is applied to our copy at `../ticketpath-demo` and verified there. The live tree is his and is untouched. If he never shows the live frontend, this is moot.
- **T11 How the console becomes reachable, if at all. TBD, and it is the only one the console raises.** The console is at `http://127.0.0.1:8788/`: `127.0.0.1` is the machine it runs on, so a judge clicking anything cannot reach it, and the video is the only place a judge will ever see it. Three options, cost of each in one line: **record only** — free, nothing to run at submission time, and the form's Demo URL stays blank (T3); **a tunnel** (`cloudflared tunnel --url http://127.0.0.1:8788`, or ngrok) — free and live in a minute, but the URL is public and up only while the process runs, so it has to be up for the judging window or it reads as a dead link, and it exposes the fixture API to anyone who finds it; **a deploy** — a few hours of his time plus a hosting account, the only option that survives him closing the laptop, and the only one that puts a URL in the form he can be held to. What the video shows either way is unchanged: every console screen in §1.2 is recorded from the local address, and no frame claims the console is hosted.

**T1 is closed; T2 is the only gate left that cannot be repaired by wording.** Until 17:36Z this
paragraph said the reverse, and it was wrong in the alarming direction: remote `main` is `375126f`, the
verified tree, so a judge who follows the project link finds the code the submission describes. T2 is still
a task rather than a decision: the video either exists by 11:30 or the entry is ineligible, and it is now the
only thing on this list that can lose the entry outright. T11 does not block anything: with no hosted demo
the entry is complete and the video is the only place the console is seen.

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
**Verified at 17:45Z, so this is a check and not a write.** `README.md` exists and satisfies the pass
condition below: the run steps, the endpoints, the not-deployed line, the licence line, the test command,
the AI disclosure and the no-screenshots note are all in it. Pass: a stranger in a fresh shell runs
`python3 -m ticketpath.server`, gets a line with `listening on http://127.0.0.1:8788`, and `curl -s
127.0.0.1:8788/health` returns 200 with `"synthetic": true`.

**4. Licence.**
**Verified at 17:45Z, so this is a check and not a write.** `LICENSE` is MIT and its third line reads
the copyright holder's name; the README names the same licence and prints the same line. Pass: `head -3
LICENSE` matches the README, and the GitHub API returns that licence after the push.

**5. On-chain honesty.**
`git grep -n 'deployed' -- '*.md'` and read every line.
Pass: every occurrence is a negation or a design label ("no program is deployed", "designed, not
deployed"), no address is presented as ours, no sentence says the hook is enforcing anything, and the one
signature in the tree — `records/00-prior-direction-index.md:169`,
`J8hNmBD7PCuVvNNxL4HSjj3LV9QHwkaUgfseZhRGdjbe`, a devnet spike from an earlier corpus, 44 characters and
therefore not a valid 64-byte signature: `getTransaction` answers `Invalid param: WrongSize` (measured
17:47Z) — is cited as prior work and not as this project's. Then `git grep -nE
'[1-9A-HJ-NP-Za-km-z]{32,44}'` and confirm every long string is either a `SYN` placeholder or a protocol
program id (Token-2022, Memo) that we do not own.

**[Corrected 2026-11-08T08:05Z: this safety pass is now out of date in both directions.** `git grep -n deployed` still finds the old negatives, but a program IS deployed on devnet, so "every occurrence is a negation" no longer implies the pass. The one signature above is no longer the only one: `records/devnet-artefacts.json` carries three devnet signatures and the console renders them, which is the claim the submission should be making. Read this item as "every deployment sentence names what was deployed, where, and what it does not prove".]**

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
captured before 10:00 ET. Paste-time check, because the console moved under this text and the text has now
caught up: findings 1, 2 and 5 of `records/findings/13-submission-readiness.md` are the five sentences that
were false — §2.5 item three, §5 answers 5 and 9, §2.6's Solana line and §2.3's missing console paragraph —
and all five are corrected in place at 17:45Z. §2.2 no longer ends with the `pricingModel.available: false`
sentence; it was rewritten at 15:10Z. Nothing in §2 needs pasting from anywhere else.

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
   outright with the missing observation named for each rather than filling them with a guess. The console at
   `/` prints those refusals, each with the observation it is missing named beside it.

The rest, in the order they tend to come.

6. **Which part did you write?** The Python backend, the fixture generator, the labelling patch and the
   on-chain design; the frontend is the platform's own app, and we say so in the description and in the
   video.
7. **What actually works right now?** Eight events and seventy-six tickets served from our backend into the
   platform's UI, with per-ticket custody trails, resale analytics, and Ed25519 wallet signature
   verification, on 610 passing tests (`python3 -m unittest discover -s tests` → `Ran 610 tests` in
   23.958 s, `OK`) **[corrected from 546, 2026-11-08T03:45Z]**.
8. **Can I click it?** Not without running it: there is no hosted demo and the submission has no demo URL;
   the repo has the two commands.
9. **What does the pricing engine output today?** A floor, not an estimate. The console served at `/`
   prints a recommended primary price for the selected event (at least 1.38 SOL per ticket on the default
   event, tagged `[UNVALIDATED]`), `/health` reports `pricingModel.available: true`, `modelVersion:
   engine-2026-11-07`, `kind: rule-based-bounded-estimator`, `fitted: false`, and the engine still refuses an
   upper bound, a sale probability and an interior optimum, naming the missing observation for each.
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

**[Corrected 2026-11-08T08:05Z: answer 13 above is wrong twice.** A program is deployed on devnet and enforces the price predicate inside the transfer hook (one landed transfer at the ceiling, one refused `6010`), so "the program that would enforce it is designed and not deployed" is false; and the UI no longer says "Not enforced, no program is deployed". What is true: the deployed v1 enforces the cap on the price a transfer declares and nothing else, its staging instructions take no signer, and the fixture ticket page is not on chain. Answer 14 should start from the v2 program and the reconciliation of the two jurisdiction decisions, not from "one write on devnet".]**

---

## 6. The counts

- Spoken words, **the script in §1.2**: **264**, six beats, 1:53 of speech at 140 words per minute and
  1:58 with the five beat pauses.
- Spoken words, the obsolete variant A kept in §1.5: **259**, unchanged, because it is kept verbatim.
- TBDs still open: **nine** of the eleven — T2, T3, T4, T5, T7, T8, T9, T10, T11. T1 is closed (remote
  `main` is `375126f`, the verified tree, measured 17:36Z) and T6 is closed (MIT, holder filled); both are
  now confirmations rather than decisions, and both are listed in the operator-actions section at the top.
  T11 is the console's reachability and it is the only one the console adds.
- The one thing that can lose the entry outright: **T2, the video.** It must exist, be under 2:00, and stay
  public. The repo no longer is the gate it was: remote `main` is `375126f` and carries every file the
  submission describes.

---

## Snapshot note — 2026-11-07T12:14Z

**This file is a snapshot of 11:34Z–11:41Z, not a description of the current tree.** Everything
above is kept as written, because the pack is a record of what the submission text said at that
hour. The state table in §0 and the numbers carried into the scripts have moved:

| What the pack says | What is true now | Shown by |
|---|---|---|
| "Pricing console (`ticketpath/console/`): **does not exist**" (§0), and §1's "Variant A (tonight, no console)" script | The console exists at `http://127.0.0.1:8788/` and prints a recommended primary price. §1.3 "Variant B" is the script that matches the running build | `curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8788/` → 200 |
| "Price served anywhere: **none**" (§0), `/health` → `pricingModel.available: false, reason: no_model_registered` (§0, §1.2 line 129, §2.2 line 230, §4 pass check, §5 answer 9) | `/health` reports `available: true`, `modelVersion: engine-2026-11-07`, `kind: rule-based-bounded-estimator`, `fitted: false`, because the seam is populated by the rule-based bounded estimator. No fitted model is claimed, so the honesty rule the pack obeys is intact; the sentence "nothing is registered" is not | `curl -s http://127.0.0.1:8788/health \| python3 -m json.tool` |
| "149 tests, OK" (§0, and in the submission text at §2.2, §2.6, §3, §5) | `OK`. The count has moved three times since this note: **306 at 12:12Z, 453 at HEAD `375126f`, 546 at 18:11Z** (measured with `python3 tools/tp.py gate`, `tests=546 OK`). Quote the command's own last line, never this one. All five sites in the pack now carry 546 with the command beside it **[AMENDED 17:45Z, count re-measured 18:11Z]** | `python3 -m unittest discover -s tests` |
| "Root README: **missing**"; "LICENSE: **missing**" (§0) | Both exist: `README.md` and `LICENSE` (MIT, copyright line names the holder, measured 17:36Z) | `ls README.md LICENSE`, `head -3 LICENSE` |
| "several files under `records/` already carry absolute paths … That is your call" (§2, no-secrets check) | **Not done. Corrected 17:45Z: this row used to say the sweep was complete and its own command disproves that.** 24 hits remained outside `NIGHT-*.md` at HEAD `375126f`, measured 17:36Z, on tracked files: `docs/morning.html` (4), `records/DELIVERABLE.md` (4), `records/FINAL-PROOF-2.md` (3), `records/FINAL-PROOF.md`, `records/findings/07-engine-review.md`, `records/findings/12-final-audit.md`, and the rest of `records/`. Recorded here as an open item rather than fixed, because the operator asked for the pack and not the tree, and it is a 24-line sweep at the hour he should be recording | `git grep -n "hom[e]/" HEAD -- README.md records docs tests tools ticketpath \| grep -v NIGHT- \| grep -v __pycache__ \| wc -l` → 24 |

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
edited. **[Superseded 17:45Z: §2.2, §2.5, §2.6, §5 answers 5 and 9 and item 9 itself are corrected in
place, and §4 items 3 and 4 and §3 item 17 are struck to a verified line each. See the correction note at the end of
this file.]**

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

### Correction note — 2026-11-07T17:45Z

**Scope:** this file only, against the tree at HEAD `375126f`, driven by
`records/findings/13-submission-readiness.md`, which lists 16 stale or false claims and was written by an
independent checker that did not write the pack. Every replacement below was measured on this machine first;
where the finding's own replacement had itself gone stale, the measured state won and the difference is
named. `README.md` was corrected in the same pass for the same reasons. Nothing was committed, nothing was
pushed.

| # | Site | What it said | What it says now |
|---|---|---|---|
| 1 | §2.5 item three | "the decision surface does not exist yet: there is no page that shows a recommended price, the backend registers no pricing model" | the pricing engine is unvalidated; a console at `/` prints a recommended price, `[UNVALIDATED]`, `fitted: false`. The VERSION-IF-CONSOLE-LANDS swap-in is applied and its "on every number it prints" dropped, because the page does not claim that |
| 2 | §5 answers 5 and 9 | "no endpoint serves a price", "the page that prints those refusals is not built yet" | a floor, not an estimate: the console prints it, `/health` reports `available: true`, `fitted: false`, and the refusals are printed with the missing observation beside each |
| 3 | test count, six sites | 149 (five sites) and "293 then 306" (snapshot note) | **546**, re-measured at 18:11Z with `python3 tools/tp.py gate` (`tests=546 OK`, 23.3 s for the whole gate) and before that 453 at HEAD `375126f` on 2026-11-07T17:36Z, `Ran 453 tests` in 18.0 s, `OK`, with `python3 -m unittest discover -s tests` printed beside every one so the number and its command cannot drift |
| 4 | §2.6 | "Solana JSON-RPC over HTTPS, devnet, read only" listed as a building block | no Solana RPC in the running build: the adapter is off by default, opens no socket, `/health` says `rpcEnabled: false`, `reason: rpc_disabled`; the §2.4 devnet reads were his `curl`, not the app's |
| 5 | §2.3 | no mention of the console, while §1.2 beat 3 films it for 21 seconds | the apply-pending paragraph is applied, plus the `[UNVALIDATED]` badge and the `[REFUSED]` block the frame shows |
| 6 | §0 state table, three rows | "149 tests"; "GitHub reports `license: None`"; remote `main` = `e55a18b`, "does not contain the backend" | 546 (re-measured 18:11Z; 453 at the 17:36Z reading); MIT with the holder filled in; **remote `main` = `375126f` = local HEAD**, 148 tracked files, 41 under `ticketpath/`. Each row carries an `[AMENDED 17:36Z]` tag so the 11:41Z reading is not silently rewritten |
| 7 | §0 consequences, §3 item 3, T1, the "T1 blocks submission" paragraph, §6 | the public repo has no backend, T1 "blocks submission outright", fix T1 first | T1 closed, measured: the push happened and the public tree is the verified tree. The only gate that can lose the entry is T2, the video. Each replacement says what it replaced |
| 8 | §3 item 17, §0 Repo row, snapshot-note licence clause | licence undecided, holder a bracketed placeholder | MIT, `LICENSE` on `main`, line 3 names the copyright holder; T6 is a confirmation, not a decision |
| 9 | README licence section | printed a bracket string that no longer exists and said the licence names no holder | names the holder, with the line quoted |
| 10 | snapshot note, home-paths row | "Done in this pass … no hits outside `NIGHT-*.md`" | **not done**: 24 tracked hits remain, file by file, measured with the command the row itself prints. Recorded as open rather than swept, per the finding's §5 |
| 11 | §1.2 beat 3 notes | `[EXACT] ceiling 1.38 SOL = face 1.20 SOL plus a cap of 15%`; badge `8 events on this platform, 5 with any resale` | the `[EXACT]` line in its measured form (`1,380,000,000 lamports = face 1,200,000,000 lamports × (10,000 + 1500) / 10,000`), and `8 events in the store`, `5 with any resale at this instant` |
| 12 | §1.2 beat 3 notes | nothing about the decision-mode block now in the middle of the frame | a paragraph naming it, saying keep it in frame, do not read it aloud, do not scroll it half off |
| 13 | README inventory | "24 test modules", "seventeen per investigation reports", "about 12 KB", and an index missing three record files | 32 test modules (measured), twenty-four per-investigation reports (24 at HEAD), about 13 KB (13,726 bytes on `/`), and `BUILD-REPORT-CONSOLE.md`, `FINAL-PROOF.md`, `FINAL-PROOF-2.md` added |
| 14 | §4 item 5 pass condition | "no signature appears anywhere" — a check that fails on a prior spike's citation | widened: the one signature in the tree is named, resolved as `Invalid param: WrongSize`, and must be cited as prior work |
| 15 | §4 items 3 and 4 | "There is no root README. Write it," and "Add `LICENSE`" | struck to a verified line each, so the last hour goes to the video and not to work that is done |
| 16 | §4 item 9 | told him to fix a §2.2 sentence that no longer exists | re-pointed at findings 1, 2 and 5, which are the five sentences that were actually false, all corrected in place |

**What did not change, on purpose.** §2.4 keeps `Nothing. No program, no mint, no transaction, no address,
and no signature` **[FALSE OF THE TREE SINCE 2026-11-08T03:45Z: all four now exist and are recorded in
`records/devnet-artefacts.json`. §2.4 is left as written because it is a dated snapshot of 12:19Z; the
form field is §3 item 16, which is corrected.]** The line that used to end this paragraph — the materials
test stays **0 of 4** — is corrected in §3 item 13. The rest of the paragraph is kept, and so is its
point: no line in this file *invented* a deployment, a signature or a program for this project, and the
correction passes added none. The deployment recorded here was measured before it was written down.

### Publication note — 2026-11-07T18:11Z

**Scope:** this file only, two mechanical passes over it, nothing re-argued. Both are here because this file
is published and because a judge reads it as the current state, not as a record of 11:41Z.

**1. Machine details removed, every claim kept.** The §0 state table and two later lines carried the kind
of handle that belongs on this machine and not on a public remote: a pid for the backend, a pid and a port
for the demo copy, and the live frontend's port in the §0 table, in §1's "what must not appear" line and in
T10. `running, pid …, 127.0.0.1:8788, /health 200` now reads `running on this machine, loopback port 8788,
`/health` 200`; the two frontend rows read `on its own port`, and the two prose mentions read "the live
frontend". 8788 stays because it is this project's own documented backend port and appears in every run
instruction. The licence holder's name is replaced by "the copyright holder" everywhere except `LICENSE`
itself, which is where it is published on purpose. No count, no number, and no sentence about Solana, about
validation or about what is not deployed was touched: the claims are the same claims, the handles are gone.

**2. The test count re-measured once, with the gate.** `python3 tools/tp.py gate` → `tests=546 OK`, wall
23.3 s for the whole gate, at HEAD `375126f` plus the working tree. The live claims in §0, §2.2, §2.6, §3 item 10, §4 item 7 and
§5 answer 9 now read **546** with the command beside each, and the 17:36Z reading of **453** is kept where it
was recorded in the 17:45Z correction note rather than overwritten. The count is still a moving number; the
command's own last line is the one that counts.

---

### Provenance note — 2026-11-07T18:55Z

**Scope:** the timeline of the background reading, and the two questions this file used to hand back.
Nothing else in the pack was re-argued, and no measured claim was touched except where it was wrong.

**1. Six sentences said the research corpus was pre-event. All six were false, and all six are fixed.**
Hacking began 2026-11-06T17:00:00Z (`records/findings/17-hackathon-rules-recheck.md` §1.1, the event's own
calendar payload `20261106T170000Z/20261108T180000Z`). `stat` on the fifteen documents in
`../research/mlh-solana-2026/` puts the first at 17:39:04Z and the last at 18:48:55Z the same day: inside
the window by 39 minutes to 1 h 49 min, not before it. Three sites in this file carried the error, and
the two later sites inherited it from the same paragraph:

| site | what it said | what it says now |
|---|---|---|
| §2.8 question 2 | "was written 2026-11-06, the day before hacking began" | written 17:39:04Z–18:48:55Z on 2026-11-06, inside the window, not the day before |
| §2.8 question 2 | "quoting anything from the pre-event corpus" | quoting the corpus beyond the attributed citations already committed |
| §0 item 9 (refreshed list) | "whether the pre-event research corpus may be quoted" | the corpus is not published and not quoted beyond attribution; the answer is recorded |

The three in `records/findings/17-hackathon-rules-recheck.md` are corrected by an appended CORRECTION in
that file, because records are append-only and its text is not rewritten in place.

**2. The provenance sentence the submission pastes is in §2.8, long form and short form.** It states the
measured times, says the documents are not published and were never in the tree, and does **not** claim
that no text from them appears in the repository, because `records/00-prior-direction-index.md` quotes them
with attribution on 17 of its lines and the operator's decision is to keep those quotations.

**3. Both open questions are answered, and D8 is the record.** The team is the operator and one teammate;
the code was written by AI agents the team directed and released, disclosed in both required AI fields; the
corpus is not published and stays local. `records/F-decision-log.md` D8 carries the decision, its evidence
and what would reverse it.

**4. One operator action added, and it is a Sunday-morning click, not a wording problem:** both team
members must be registered on MLH *and* checked in (§0 item 8, §3 item 12, T4). A registered-but-unchecked
second member is a one-person team on the form.

**5. The two names are deliberately not in this file.** The decision names both team members. This
repository's public-safety rule (`.public-denylist`, class `personal-name`) denies the operator's full name
anywhere except `LICENSE` and the `README.md` line that restates the licence, and the check refused this
commit on eight hits across four files for exactly that reason. Rather than add a per-file exception to
that denylist, which is a publication decision and not a wording one, the names were replaced here
and in the three records that carried them with "the operator and one teammate". The names are on the MLH
team field and in `LICENSE`, which is where they are published on purpose. Nothing else about the decision
was softened: the team size, both registrations, the disclosure and the corpus answer are all stated.

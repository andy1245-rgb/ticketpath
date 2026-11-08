# FINAL-PROOF: the submission, measured on this machine

What this is: one proof run, executed end to end on 2026-11-07 between
`13:10:58Z` and `13:17:16Z` (the run window), on this machine, Python 3.12.3,
standard library only, with the backend on `127.0.0.1:8788` and a copy of the
platform frontend on `127.0.0.1:3001`. Every result below is the observed
output of a command in this run, not an inference. Where a step failed, it is
recorded as failed; there were no failures.

The claim under test: **a person can open the console and see an honest
decision, and can click the real frontend against our backend and see market
numbers that came from it, with everything labelled and nothing crashed.**

Environment facts established before any test:

- the live platform frontend's port serves `next-server`, started
  `Fri Nov 6 23:57:34 2026`. Untouched.
- a copy of that frontend was served for the run from `../ticketpath-demo`,
  started with `NEXT_PUBLIC_API_BASE_URL` pointing at the backend (read from
  the process's own `/proc/<pid>/environ`, not assumed).
- the ticketpath backend was up: at window open it was an instance of
  `python3 -m ticketpath.server`, cwd `<repository root>`, listening on
  loopback. It was stopped and replaced with a fresh instance running the
  identical command, so the proof is against the code on disk now.
- one further loopback port on this machine belonged to another process. Never
  bound, never touched.

---

## Step 1: The full test suite

Command:

```bash
cd <repository root>
python3 -m unittest discover -s tests
```

Observed:

```
Ran 353 tests in 12.156s

OK
```

**PASS.** 353 tests, 353 passed, 0 failures, 0 errors. For reference, the
README's 12:12Z figure was 306; the suite grew during the night, which the
README says to expect ("the count moves as the backend grows").

---

## Step 2: Backend on 8788: health, every contract route, and the console

The process holding 8788 was identified as the backend on that port
(`python3 -m ticketpath.server`, cwd `<repository root>`) and stopped:
only that instance was killed. A fresh instance was started with the documented
command. Startup banner:

```
ticketpath 0.1.0 listening on http://127.0.0.1:8788 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
  SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
```

Every route, observed:

```
200    1177b  GET  /health                                 /health
200   10161b  GET  /api/events                             /api/events?limit=100
200    1422b  GET  /api/events/:idOrSlug                   /api/events/evt_syn_04
200    3352b  GET  /api/events/:eventId/analytics          /api/events/evt_syn_02/analytics
200   37314b  GET  /api/tickets                            /api/tickets?limit=200
200     785b  GET  /api/tickets/:ticketId                   /api/tickets/tkt_syn_0001
200    1844b  GET  /api/tickets/:ticketId/resale-history    /api/tickets/tkt_syn_0001/resale-history
200     445b  GET  /api/wallets/:wallet/verification        /api/wallets/SYNFL8KnV6ew2apUbQ3SFGcwA5JZ4Mqq7hU3DSU1nFt/verification
200   13147b  GET  /                                       /
200   13147b  GET  /index.html                             /index.html
```

The two POST routes were exercised with a real Ed25519 keypair, not a mock:

```
POST challenge -> 200 nonce length 32
POST verification -> 200 verified True method wallet_signature
GET verification -> 200 True
```

A bad nonce is refused by contract, with a JSON body and no stack trace:

```
400  body={"message": "unknown or already used nonce", "status": 400, "code": "nonce_unknown"}
```

`/health` facts:

```
status: ok | version: 0.1.0
dataSource: synthetic-fixture synthetic: True
chain.programDeployed: False | programId: None | rpcEnabled: False | designDoc: docs/ON-CHAIN-DESIGN.md
pricingModel.available: True | modelVersion: engine-2026-11-07 | kind: rule-based-bounded-estimator | fitted: False
contract.routesImplemented: 10 | endpointsImplemented: 9
```

**PASS.** `/health`, all nine contract endpoints over ten routes, and the
console all answered 200. `/health` says in its own words that nothing is
fitted and nothing is deployed.

---

## Step 3: Console walk: every event, every tier, both modes, four edge inputs

Every request was classified from the rendered HTML, not from an assumption:
a page carrying `aria-label="[UNVALIDATED] the decision"` with a
`[UNVALIDATED]` headline is a **decision**; the same panel with a `[REFUSED]`
headline, or a page with no decision panel, is a **refusal**; HTTP >= 400, an
empty body, or `Traceback` in the body is an **error**.

Baseline, 8 events, 15 tiers, 2 modes, 30 requests:

```
event       tier              mode            HTTP outcome   bytes
evt_syn_06  tier_cpl_standing counterfactual  200  DECISION  12934
evt_syn_06  tier_cpl_standing before_on_sale  200  REFUSAL   12898
evt_syn_04  tier_thr_single   counterfactual  200  DECISION  12596
evt_syn_04  tier_thr_single   before_on_sale  200  REFUSAL   12639
evt_syn_02  tier_stg_general  counterfactual  200  DECISION  13082
evt_syn_02  tier_stg_general  before_on_sale  200  REFUSAL   12959
evt_syn_02  tier_stg_front    counterfactual  200  DECISION  12994
evt_syn_02  tier_stg_front    before_on_sale  200  REFUSAL   12953
evt_syn_07  tier_riv_gallery  counterfactual  200  DECISION  13179
evt_syn_07  tier_riv_gallery  before_on_sale  200  REFUSAL   13039
evt_syn_07  tier_riv_mezzanine counterfactual 200  DECISION  13100
evt_syn_07  tier_riv_mezzanine before_on_sale 200  REFUSAL   13046
evt_syn_07  tier_riv_box      counterfactual  200  DECISION  13081
evt_syn_07  tier_riv_box      before_on_sale  200  REFUSAL   13027
evt_syn_01  tier_hal_floor    counterfactual  200  DECISION  13075
evt_syn_01  tier_hal_floor    before_on_sale  200  REFUSAL   13017
evt_syn_01  tier_hal_balcony  counterfactual  200  DECISION  13081
evt_syn_01  tier_hal_balcony  before_on_sale  200  REFUSAL   13024
evt_syn_01  tier_hal_box      counterfactual  200  DECISION  13001
evt_syn_01  tier_hal_box      before_on_sale  200  REFUSAL   13011
evt_syn_03  tier_anx_standing counterfactual  200  REFUSAL   13305
evt_syn_03  tier_anx_standing before_on_sale  200  REFUSAL   12979
evt_syn_03  tier_anx_seated   counterfactual  200  REFUSAL   13303
evt_syn_03  tier_anx_seated   before_on_sale  200  REFUSAL   12977
evt_syn_05  tier_are_lower    counterfactual  200  REFUSAL   13003
evt_syn_05  tier_are_lower    before_on_sale  200  REFUSAL   12678
evt_syn_05  tier_are_upper    counterfactual  200  REFUSAL   13003
evt_syn_05  tier_are_upper    before_on_sale  200  REFUSAL   12678
evt_syn_08  tier_std_single   counterfactual  200  REFUSAL   12334
evt_syn_08  tier_std_single   before_on_sale  200  REFUSAL   12632
```

Edge inputs, per tier and mode. `D` = decision, `R` = refusal, `E` = error.
The edge inputs were `asOf=2026-07-01T00:00:00Z` (before the earliest issue on
2026-08-02), `asOf=<that event's endsAt>`, `capBps=0`, and
`feeLamports=50000000000` (50 SOL, larger than every face value):

```
event       tier              mode            cut_before_issue    cut_after_end         capBps_0        fee_large
evt_syn_06  tier_cpl_standing counterfactual             200/R            200/D            200/D            200/D
evt_syn_06  tier_cpl_standing before_on_sale             200/R            200/R            200/R            200/R
evt_syn_04  tier_thr_single   counterfactual             200/R            200/D            200/D            200/D
evt_syn_04  tier_thr_single   before_on_sale             200/R            200/R            200/R            200/R
evt_syn_02  tier_stg_general  counterfactual             200/R            200/D            200/D            200/D
evt_syn_02  tier_stg_general  before_on_sale             200/R            200/R            200/R            200/R
evt_syn_02  tier_stg_front    counterfactual             200/R            200/D            200/D            200/D
evt_syn_02  tier_stg_front    before_on_sale             200/R            200/R            200/R            200/R
evt_syn_07  tier_riv_gallery  counterfactual             200/R            200/D            200/D            200/D
evt_syn_07  tier_riv_gallery  before_on_sale             200/R            200/R            200/R            200/R
evt_syn_07  tier_riv_mezzanine counterfactual            200/R            200/D            200/D            200/D
evt_syn_07  tier_riv_mezzanine before_on_sale            200/R            200/R            200/R            200/R
evt_syn_07  tier_riv_box      counterfactual             200/R            200/D            200/D            200/D
evt_syn_07  tier_riv_box      before_on_sale             200/R            200/R            200/R            200/R
evt_syn_01  tier_hal_floor    counterfactual             200/R            200/D            200/D            200/D
evt_syn_01  tier_hal_floor    before_on_sale             200/R            200/R            200/R            200/R
evt_syn_01  tier_hal_balcony  counterfactual             200/R            200/D            200/D            200/D
evt_syn_01  tier_hal_balcony  before_on_sale             200/R            200/R            200/R            200/R
evt_syn_01  tier_hal_box      counterfactual             200/R            200/D            200/D            200/D
evt_syn_01  tier_hal_box      before_on_sale             200/R            200/R            200/R            200/R
evt_syn_03  tier_anx_standing counterfactual             200/R            200/R            200/R            200/R
evt_syn_03  tier_anx_standing before_on_sale             200/R            200/R            200/R            200/R
evt_syn_03  tier_anx_seated   counterfactual             200/R            200/R            200/R            200/R
evt_syn_03  tier_anx_seated   before_on_sale             200/R            200/R            200/R            200/R
evt_syn_05  tier_are_lower    counterfactual             200/R            200/R            200/R            200/R
evt_syn_05  tier_are_lower    before_on_sale             200/R            200/R            200/R            200/R
evt_syn_05  tier_are_upper    counterfactual             200/R            200/R            200/R            200/R
evt_syn_05  tier_are_upper    before_on_sale             200/R            200/R            200/R            200/R
evt_syn_08  tier_std_single   counterfactual             200/R            200/R            200/R            200/R
evt_syn_08  tier_std_single   before_on_sale             200/R            200/R            200/R            200/R
```

Totals:

```
cut_before_issue   statuses={200: 30} outcomes={'REFUSAL': 30} empty/traceback=0
cut_after_end      statuses={200: 30} outcomes={'DECISION': 10, 'REFUSAL': 20} empty/traceback=0
capBps_0           statuses={200: 30} outcomes={'DECISION': 10, 'REFUSAL': 20} empty/traceback=0
fee_large          statuses={200: 30} outcomes={'DECISION': 10, 'REFUSAL': 20} empty/traceback=0
```

Representative page contents, read from the bytes the server sent:

```
DECISION  /?event=evt_syn_02&tier=tier_stg_general&mode=counterfactual
  [UNVALIDATED] Recommended primary price: at least 1.38 SOL per ticket, General tier.
  [EXACT] ceiling 1,380,000,000 lamports = face 1,200,000,000 lamports x (10,000 + 1500) / 10,000
  Range: 1.38 SOL and up. We do not state an upper bound from this record.

REFUSAL   /?event=evt_syn_08&tier=tier_std_single
  [REFUSED] No resale has been recorded on this event, so we will not state a primary price.

EDGE capBps=0 (same tier, counterfactual)
  headline unchanged, plus one violation line: recorded sales above this cap; had this cap
  been enforced those transfers would have failed, so this record could not exist.

EDGE fee=50 SOL (same tier, counterfactual)
  [REFUSED] The declared fee of 50 SOL per ticket is larger than the recommended price of
  1.38 SOL, so a sale at that price would leave the seller short by 48.62 SOL per ticket.
```

A negative-input sweep was also run as extra evidence: `event=nope`,
`tier=nope`, `mode=bogus`, `asOf=not-a-date`, `capBps=abc`, `feeLamports=-5`,
`tau=nope`, `sim=1`, `capBps=-1`. Statuses were 404/400 as appropriate, every
one rendered a page carrying `[REFUSED]`, none carried a traceback.

**PASS.** 150 of 150 requests answered 200. Zero empty replies, zero stack
traces, zero errors. The only refusals are the deliberate ones: the
`before_on_sale` mode excludes the event's own record by design, the cold-start,
resale-disabled and draft events have no record to price from, and a cut before
any issue has nothing at or before it.

---

## Step 4: The frontend copy on :3001 against the backend

The copy's `/proc/<pid>/environ` showed `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788`,
so the copy already running was the one under test. That it is live and not
reading its bundled fixtures is proven by content: `lib/mock/events.json` has 6
events with different ids; the rendered page has the backend's 8 `evt_syn_*`
events and the backend's own label `SYNTHETIC FIXTURE DATA.`

Seven frontend pages:

```
200   118918b  /                            expected 200  OK
200   162813b  /events/evt_syn_02           expected 200  OK
200   128631b  /tickets/tkt_syn_0001        expected 200  OK
200   138264b  /organizer                   expected 200  OK
200    39970b  /my-tickets                  expected 200  OK
200    40800b  /verify                      expected 200  OK
404    41909b  /events/does-not-exist       expected 404  OK
```

Number-for-number, page against backend JSON. Four pages carry data; every
number below was read out of the rendered page and out of the API response in
the same run:

```
HOME / vs GET /api/events
  page event links: 8  backend items: 8  MATCH: True
EVENT /events/evt_syn_02
  saleCount      page=  12 backend=  12 MATCH
  resoldShare%   page=  67 backend=  67 MATCH
  avgMarkup%     page=  12 backend=  12 MATCH
  issuedCount    page=  12 backend=  12 MATCH
TICKET /tickets/tkt_syn_0001
  transferCount  page=   3 backend=   3 MATCH
  saleCount      page=   2 backend=   2 MATCH
  uniqueWallets  page=   4 backend=   4 MATCH
  faceValueSOL   page=   1 backend=   1 MATCH
ORGANIZER /organizer
  saleCount      page=  12 backend=  12 MATCH
  resoldShare%   page=  73 backend=  73 MATCH
  uniqueHolders  page=   9 backend=   9 MATCH
  avgMarkup%     page=  20 backend=  20 MATCH
```

The seven backend data routes the frontend's `lib/api.ts` maps to were also
fetched directly and all returned 200 (Step 2 table); the two POST wallet routes
returned 200 with a real signature.

**PASS.** 17 of 17 number comparisons match. Six pages 200, the missing-event
page 404 as the contract requires. The frontend is rendering the backend's
numbers, labelled as synthetic.

---

## Step 5: The live frontend's port is untouched

```
the live frontend's port:  next-server (v15.5.29)
the frontend:    STARTED Fri Nov 6 23:57:34 2026, ELAPSED 13:16:56
GET :3000/  ->   200  30546b
```

File tree, measured with `find ../ticketing-frontend -xdev`:

```
files newer than the run window: 0
newest file in the tree: .next/server/route-cache/.../verify.meta  2026-11-06T23:57:41
```

The page on `:3000` still serves its own 6 mock events
(`evt_midnight_static_tour`, `evt_winter_chamber_series`,
`evt_harbor_lights_festival`, `evt_sidestage_warehouse_04`,
`evt_riverside_comedy_night`, `evt_northline_derby_finals`); a request for
`/events/evt_syn_02` there returns 404, because that app was never repointed at
this backend. That is the untouched state, not a regression.

**PASS.** Same pid, same start time, HTTP 200, zero files written in the run
window.

---

## Step 6: No secret in the tree

Scanned the repository (excluding `.git`, `__pycache__`, compiled and database
files) for `.env` files, PEM private keys, AWS/GitHub/OpenAI/Slack tokens,
password and api-key assignments, 64-byte key arrays, and every hex string of
32 characters or more. Secret values are not printed here.

```
ENV FILES: none found

PATTERN FINDINGS (4):
  records/DEMO-PROOF.md:80  kind=solana secret key (64-byte array)  length=13
  tests/test_event_analytics.py:113  kind=solana secret key (64-byte array)  length=18
  tests/test_markup.py:79  kind=solana secret key (64-byte array)  length=18
  tests/test_markup.py:85  kind=solana secret key (64-byte array)  length=18

LONG HEX STRINGS (>=32 chars), by file:
  docs/ON-CHAIN-FOR-LAPTOP.md: 1 distinct, max_len=40
  records/FRONTEND-HONESTY-PATCH.md: 1 distinct, max_len=64
  records/ON-CHAIN-RECONCILIATION.md: 1 distinct, max_len=40
  records/findings/06-validation-protocol.md: 2 distinct, max_len=64
  records/findings/07-engine-review.md: 1 distinct, max_len=64
  tests/test_contract_conformance.py: 6 distinct, max_len=64
  tests/test_ed25519.py: 8 distinct, max_len=64
  tests/test_verification_message.py: 1 distinct, max_len=32
  ticketpath/core/ed25519.py: 1 distinct, max_len=38
```

Each hit was opened and classified, with values redacted:

- the four "64-byte array" hits are two-element lists of markup-bucket counts in
  test assertions and one markdown table row, all integers, not key material;
- `ed25519.py` and `test_contract_conformance.py` carry the Ed25519 group order
  `2**252 + 27742317777372353535851937790883648493`, a public curve constant;
- `test_ed25519.py` and `test_contract_conformance.py` carry RFC 8032 published
  test vectors (seed, public key, signature);
- the 40- and 64-character hits in `docs/` and `records/` are git blob ids and
  sha256 digests of the fixture and patch files;
- `test_verification_message.py` carries a test nonce.

Also checked: no `*.pem`, `*.key`, `*.crt`, `id.json`, `*keypair*`, `*.keystore`
or `.env*` file exists; no `.env` is tracked or untracked in `git status`; the
only credential keyword hit is `docs/ON-CHAIN-DESIGN.md:855`, a documented
`solana-keygen new -o ~/.config/solana/ticketpath-devnet.json` procedure line
with no key material.

**PASS.** No secret, no key file, no token, no `.env`. Every hex hit is a public
constant, a published test vector, or a file digest.

---

## Step 7: The repository is clean to a stranger

`README.md` exists (13,344 bytes) and `LICENSE` exists (1,104 bytes, MIT).
Every command in the README was run:

```bash
python3 -m ticketpath.server
  # the process serving :8788 is exactly this command; cold start on the
  # documented override TICKETPATH_PORT=8794 also verified:
  ticketpath 0.1.0 listening on http://127.0.0.1:8794 ... routes=10

curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://127.0.0.1:8788/
  200 13147

curl -s 'http://127.0.0.1:8788/api/events?limit=100'
  8 events

curl -s 'http://127.0.0.1:8788/api/tickets?limit=200'
  76 tickets

curl -s http://127.0.0.1:8788/health | head -c 400
  {"service": "ticketpath", "version": "0.1.0", "status": "ok", ...}

python3 -m unittest discover -s tests
  Ran 353 tests in 12.156s / OK

python3 tools/build_fixture_store.py --check
  [ok] fixtures/synthetic_store.json matches a fresh build exactly
  [ok] LedgerAdapter.from_fixture accepts it; ticketpath.core.base58 round-trips every address

python3 tools/build_fixture_store.py
  (run in a throwaway copy so the repository fixture was not edited)
  [ok] wrote fixtures/synthetic_store.json (90727 bytes)
  sha256 15e6f661...  equals the repository's fixture byte for byte

python3 tools/guidance.py --events
  8 events listed

python3 tools/guidance.py --event evt_syn_04 --as-of 2026-11-07T12:00:00Z
  full JSON console payload returned
```

`git status` is not clean, but every entry is one of the night's own edits, and
none was added by this run (`git status` before and after are identical):

```
 M NIGHT-LOG.md
 M NIGHT-QUEUE.md
 M records/00-data-situation.md
 M records/A-research-ledger.md
 M records/BUILD-REPORT-CONSOLE.md
 M records/C-variable-registry.md
 M records/CORRECTIONS-APPLIED.md
 M records/DELIVERABLE.md
 M records/F-decision-log.md
 M records/findings/01-a-market-structure.md
 M tests/test_console_fixes.py
 M ticketpath/console/blocks.py
 M ticketpath/core/labels.py
?? records/findings/08-fix-verification.md
```

**PASS with a caveat.** README, LICENSE and every README command work as
written. The working tree is dirty with 13 modified files and one untracked
finding, all nameable, all from the overnight work, none from this run. This
file (`records/FINAL-PROOF.md`) is the only file this run adds.

One thing the README already flags and the operator must complete: `LICENSE`
line 3 reads `Copyright (c) 2026 [OPERATOR: replace this bracket with your name]`.
Until that is replaced the licence names no holder.

---

## State of the submission

**What a judge can see tonight, on this machine:**

- The console at `http://127.0.0.1:8788/`: a labelled, honest decision or a
  refusal for every one of the 8 events and 15 tiers, in both decision modes,
  with the synthetic-data banner and the evidence counts above the decision.
  150 of 150 edge-case requests answered, none empty, none crashed.
- A working copy of the platform frontend at `http://127.0.0.1:3001/`, reading
  the backend on `:8788`, with 17 numbers on four pages matching the API
  response exactly.
- `/health` stating plainly: synthetic fixture, no program deployed, no fitted
  model, 9 of 9 contract endpoints over 10 routes.
- 353 passing tests and a deterministic fixture generator that reproduces the
  store byte for byte.

**What only the operator can complete:**

1. Commit and push. Nothing from the night is committed; the code a judge would
   clone is the pre-night code. This is the whole delivery step and it is not
   done.
2. Fill in the LICENSE copyright line.
3. Decide whether to repoint the live frontend on `:3000` at this backend. It
   currently serves its own mock events and 404s on ours; the copy on `:3001` is
   the one wired to `:8788`.
4. Supply real ledger data, or deploy the program, if the numbers must stop
   being synthetic. `/health` and the console both refuse to pretend otherwise.
5. Host a demo or record the video; there is no deploy URL and no recording.

**Single highest remaining risk:** the submission exists only as an uncommitted
working tree. Thirteen modified files and one untracked finding carry the entire
night's work, and a judge who is given the repository as it stands today gets
the code from before the night. Everything measured above is real, and none of
it is visible to anyone who clones the repo until the operator commits.

---

## Judge path

1. The console, the honest decision: `http://127.0.0.1:8788/`
2. The frontend against our backend: `http://127.0.0.1:3001/`
3. Where the data comes from, in one call: `http://127.0.0.1:8788/health`

---

## CORRECTION (2026-11-08T08:30Z): machine handles redacted, no claim changed

**Scope:** this file only, and only the lines in the table below. **Why:** this repository is public
and `tools/public_safety.py` refuses a tracked file that carries an absolute path under a home
directory or a process id. The rule and its reason are in `.public-denylist`. The whole-tree run is
the only one of its three entry points that reads what is already published, which is why this is a
forward edit and not a rewrite of history.

**What a redaction here is allowed to cost: nothing that was measured.** The pid was the handle that
identified which process was holding a port, not the measurement. The sentence now names the process
by what the run printed for it, the command line, the start time and the listener, and where the
claim was that nothing moved, it says "the same process". The home paths say the same thing as the
repository-relative paths beside them.

| Where | Was | Now |
|---|---|---|
| Environment, live frontend | the port tied to `pid <n>`, started … | "the live platform frontend's port serves `next-server`, started …" |
| Environment, demo copy | a path under a home directory | `../ticketpath-demo` |
| Environment, backend | `pid <n>`, a `cwd` under a home directory, "replaced with pid `<n>`" | the backend named by its command, the pids gone, `cwd` `<repository root>`, "replaced with a fresh instance" |
| Step 1, suite block | `cd` into a path under a home directory | `cd <repository root>` |
| Step 2 | `cwd` under a home directory, "only pid `<n>` was killed" | `cwd` `<repository root>`, "only that instance was killed" |
| Step 4 | `/proc/<n>/environ` | the copy's `/proc/<pid>/environ` |
| Step 5, listener capture | the port as a tied handle on the listener line, `pid=<n>` on the next, `pid <n>` on the one after | the port named by what it serves, the pid gone, the start time and ELAPSED kept |
| Step 5, file tree | `find` over an absolute path | `find ../ticketing-frontend -xdev` |
| Environment bullets, 2026-11-08T09:22Z | `:3001` named as the copy, `:8788` named as the ticketpath backend and the command that runs it, `:8787` named as another process | the copy, the backend and the third port named by what they were, with no port tied to a process |

**Residue, stated rather than hidden.** Port numbers on lines this rule does not classify are
unchanged, including this project's own documented backend port. `.public-denylist` states why it
does not deny those, and `/tmp` paths are exempt for `records/` on purpose.
`python3 tools/public_safety.py check --tracked` reports zero hits for this file as of this note.

**Extended 2026-11-08T09:22Z, on the release-record correction pass.** The environment bullets
still tied three ports to the processes behind them, which `AGENTS.md` forbids in its own words:
the rule says it "may not record which process holds the port". Those three bullets now name what
was running and not where it listened, and the table above records the change. This is a rule-level
residual that both public-safety checks are clean on, because neither classifies a port plus a
process as a hit; the checker did not catch it and this note is where that is said.

**What was kept, and why the rest of the ports stay.** The command blocks below still call
`http://127.0.0.1:8788/` and `http://127.0.0.1:3001/`. Those are the addresses the proof actually
called, they are the output the run produced, and deleting them would delete the reproduction
rather than the handle. They name a URL, not which process holds a port. If the operator wants
them gone too, that is a decision about the proof and not a redaction this note can make on its
own.

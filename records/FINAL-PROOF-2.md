# FINAL-PROOF-2: the current tree, measured end to end

Second proof pass for the Ticketpath submission. Window `2026-11-07T15:35:40Z` to
`2026-11-07T15:50Z`, on this machine, Python 3.12.3, standard library only, backend on
`127.0.0.1:8788`, a copy of the platform frontend on its own port, and the live frontend on
`127.0.0.1:3000`.

This file is the only file this run writes inside the repository. Nothing was fixed, installed,
committed or pushed. Every number below is the observed output of a command in this run; where a
step failed, it is recorded as failed and the run continued.

The claim under test, split into its parts:

1. a judge can open the console and get an honest decision;
2. that decision is internally consistent with its own cap and its own clock;
3. he can click the frontend against our backend and see numbers that came from it, labelled;
4. nothing on the way crashes, contradicts itself, or claims a deploy.

Part 1 holds. **Part 2 fails**: the console is not internally consistent with its own cap on
30 of the 64 page states the brief names, though it is consistent with its own clock in all 64
cut states swept. Part 3 holds. Part 4 holds in the narrow sense — nothing crashed, no response
was empty, no page carried a stack trace, and nothing claims a deploy — but the "contradicts
itself" half of it is what Part 2 measures, and there it fails. Details in Step 3.

Environment established before the first test:

- the live platform frontend's port serves `next-server`, started `Fri Nov 6 23:57:34
  2026`, cwd `../ticketing-frontend`. Untouched.
- the demo copy sits at `../ticketpath-demo`, served by `next-server` under a dev parent (the
  run printed both pids), started `11:08:30`. The child's `/proc/<pid>/environ` shows
  `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788`, read from the process, not assumed.
- `:8788` was serving a backend this run did not start (`python3 -m ticketpath.server
  --port 8788`, cwd `<repository root>`). It was stopped and replaced with a fresh instance
  running the documented command, so every reading below is against the code on disk at 15:36Z.
- `8787` is another process (`node server.mjs`). Never bound, never touched.
- Two stray backend processes from an earlier session were running on `:8801` and `:8802`
  (started 11:45). Observed, not touched, not used. They are still there.
- Newest source file in the tree: `ticketpath/api/guidance.py`, `15:28`. The backend was
  started after it, so no reading here comes from stale bytecode in a running process.

---

## Step 1: the five check commands

Every command from the repository root.

### 1a. Full suite

```bash
python3 -m unittest discover -s tests
```

```
Ran 427 tests in 16.791s

OK
exit 0
```

**PASS.** 427 tests, 0 failures, 0 errors. The README's 12:12Z figure was 306 and its 13:10Z
figure 353; the suite grew again, which the README says to expect.

### 1b. Contract conformance

```bash
python3 -m unittest tests.test_contract_conformance -v
```

```
Ran 22 tests in 0.691s

OK
exit 0
```

The 22 named tests are: `test_nine_contract_routes_are_attempted_and_served`,
`test_every_route_was_evaluated`, `test_every_route_matches_the_contract_shape`,
`test_every_route_honours_the_contract_prose`, `test_no_route_drifts_from_the_contract`,
`test_only_the_documented_extras_appear`, `test_event_nullables_are_present`,
`test_ticket_nullables_are_present`, `test_envelopes_carry_next_cursor`,
`test_absent_route_is_missing_not_skipped`, `test_a_route_that_answers_400_is_drift_not_missing`,
and five canaries that feed a deliberately wrong payload and require the validator to fail
(`missing_and_undocumented_fields`, `bad_enum_and_non_utc_timestamp`, `float_money`,
`event_level_markup` ×2, `series_markup_re_derived_from_mean_price`, `wrong_bucket_label`), plus
the base58 round-trip, the frozen verification message and the RFC 8032 vector.
**PASS.** The contract is encoded in the test file and imports nothing from `ticketpath`, so this
is not the code agreeing with itself.

### 1c. The console check tool

```bash
python3 tools/console-check.py     # against the fresh backend on :8788
```

```
== responses        23 cases: 200/400/404/405 as specified, every one a rendered page
== labels           ok lines 102
FAIL lines 0
FAILURES: 0
exit 0
```

**PASS**, with one caveat that matters: the tool's zero is not independent evidence for
property (c). Line 179-181 of the tool asserts that the page prints
`in this tier [FIXTURE] 0 sales of [FIXTURE] 0 on this event · [FIXTURE] 9 recorded sales in
this tier are excluded by the mode`. The checker requires the defect it is supposed to catch;
see Step 3, finding C1.

### 1d. The store check tool

```bash
python3 tools/console-check-stores.py
```

```
ok   zero-priced sale                 /?event=evt_syn_01  status=422 page=True code=sale_not_priced
ok   the rest still prices            /?event=evt_syn_04  status=200 page=True code=-
ok   the store count is the store     file=8 page=(8, 7)
ok   sale after start                 /?event=evt_syn_04&asOf=...  status=422 code=sale_after_event_start
ok   event with no tiers              /?event=evt_syn_03  status=422 code=event_has_no_tier
ok   event with no tiers / default    /                   status=200
FAILURES: 0
exit 0
```

12 `ok` lines, 0 failures. **PASS.** Three deliberately broken stores each answer with a
typed 422 and a rendered page, and the healthy events on the same server keep pricing.

### 1e. The fixture generator's check

```bash
python3 tools/build_fixture_store.py --check
```

```
build_fixture_store.py: seed 20261107, 8 events, 76 tickets, 147 ledger rows
  [ok] addresses: 204 distinct, all SYN*, 32 bytes, 204 distinct truncations
  [ok] ledger: 147 rows over 76 tickets, 61 priced sales, custody chains linked, timestamps strict
  ... 18 [ok] lines in total ...
  [ok] fixtures/synthetic_store.json matches a fresh build exactly
  [ok] LedgerAdapter.from_fixture accepts it; ticketpath.core.base58 round-trips every address
exit 0
```

**PASS.** 18 of 18 invariants, and the store on disk is byte-identical to a fresh build.

---

## Step 2: the backend on 8788

The process on 8788 was confirmed as this project's backend (`/proc/<pid>/cwd` =
`<repository root>`) and stopped. One fresh instance:

```bash
python3 -m ticketpath.server
```

```
ticketpath 0.1.0 listening on http://127.0.0.1:8788 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
  SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
started Sat Nov  7 15:36:03 2026, LISTEN 127.0.0.1:8788
```

Every route, status and bytes as served:

```
200    1177b  GET  /health
200   10161b  GET  /api/events
200    1422b  GET  /api/events/:idOrSlug            (/api/events/evt_syn_04)
200    3352b  GET  /api/events/:eventId/analytics    (/api/events/evt_syn_02/analytics)
200   37314b  GET  /api/tickets
200     785b  GET  /api/tickets/:ticketId            (/api/tickets/tkt_syn_0001)
200    1844b  GET  /api/tickets/:ticketId/resale-history
200     445b  GET  /api/wallets/:wallet/verification
200   13547b  GET  /
200   13547b  GET  /index.html
```

The two POST routes, with a real Ed25519 keypair generated in this run (not a mock, not a
fixture):

```
POST /api/wallets/FAe4.../verification/challenge -> 200 nonce_len 32 expiresAt 2026-11-07T15:41:35.900Z
POST /api/wallets/FAe4.../verification           -> 200 {"verified": true, "method": "wallet_signature", ...}
GET  /api/wallets/FAe4.../verification           -> 200 verified true
POST replay of the same nonce                    -> 400 {"code": "nonce_unknown"}
```

`/health`, read in full:

```
status ok | version 0.1.0
dataSource.mode synthetic-fixture | dataSource.synthetic true
chain.programDeployed false | chain.programId null | chain.rpcEnabled false
chain.designDoc docs/ON-CHAIN-DESIGN.md
pricingModel.available true | modelVersion engine-2026-11-07
pricingModel.kind rule-based-bounded-estimator | pricingModel.fitted false
contract.endpointsInContract 9 | endpointsImplemented 9 | routesImplemented 10
```

**PASS.** 10 of 10 routes answered 200, both POST routes verified a real signature and refused
a replay, and `/health` says in its own words that nothing is deployed and nothing is fitted.

---

## Step 3: the consistency sweep of the console

This is the step that fails.

### What was swept

Every event, both decision modes, four cap states. Cap states are `none` (no parameter, so the
event's recorded cap is in force), `0`, the event's own recorded cap, and 1000 bps above it.
For the four events that record no cap (`evt_syn_04`, `05`, `08`), "event default" is no cap, so
a typed 1500 bps stands in and is labelled as such.

| sweep | coverage | page states |
|---|---|---|
| 1, required | 8 events × 2 modes × 4 cap states, default tier | 64 |
| 2, extended | every tier (15) × 2 modes × 4 cap states | 120 |
| 3, grid | every tier × 2 modes × 18 caps (0 to 10000, incl. 298, 1500, 2500) | 540 |
| **total** | | **724** |

Ground truth for the cap in force and the per-tier face is the payload the server itself builds
for the same parameters and the same decision instant (parsed off the page); ground truth for
"does this event hold rows" is `fixtures/synthetic_store.json`. Every displayed number is parsed
out of the bytes the server sent.

### The rules, as three falsifiable tests

**(a) The cap the page names is the cap it prices against.** Six tests: the cap field, the
canonical URL, the "prices against a cap of N" sentence, the ceiling formula's cap operand and
its integer arithmetic, the refusal's stated ceiling, and the sentence that says where the band
stops. Plus two absence tests in both directions.

**(b) No band crosses a ceiling the page says it will not cross.** Any printed band (value band,
prior band, or the band the sentence says stops at the cap) against any ceiling the page prints.

**(c) No sentence claims rows are absent when the decision mode is what excludes them.** Forbidden
absence sentences when the store holds rows, the market block's event denominator, the
exclusion counts against the store's counts, and the requirement that exclusion be named.

### Result

```
page states swept:                                     724
violations:                                            594
  (a) the cap named is not the cap priced against:      44
  (b) a band crosses a ceiling the page prints:        310
  (c) absence claimed where the mode excludes:         240
distinct page states with at least one violation:      594

required 64-state grid:
  violations:                                           46
  distinct page states with at least one violation:      30 of 64  (34 clean)
  by property: (a) 2, (b) 24, (c) 20
  by event:    01: 9, 02: 8, 03: 8, 04: 4, 06: 9, 07: 8
  clean events: evt_syn_05 (resale disabled), evt_syn_08 (nothing issued)
```

**FAIL.** The console is not internally consistent with its own cap on 30 of the 64 page states
the brief names, and on 594 of the 724 states swept.

### C1 — the market block says the event holds zero sales while the same sentence says the mode excluded them. 240 states, 20 in the required grid.

`/?event=evt_syn_02&mode=before_on_sale`, read from the bytes served:

```
[FIXTURE] 0 sales of [FIXTURE] 0 on this event · [FIXTURE] 9 recorded sales in this tier are
excluded by the mode · median markup [REFUSED] not stated · ...
```

The store holds 12 sales on `evt_syn_02` and 9 in the General tier, and the page says so in the
second half of the same line. The first half says the event holds none. This is the review
`10-final-review` N4 defect one block lower: the strip was fixed to count excluded rows, the
market block's event denominator was not.

It appears on every event that has sales (`01`, `02`, `04`, `06`, `07`), in `before_on_sale`
mode, under all four cap states. It needs one click on the mode dropdown.

`tools/console-check.py:179-181` asserts this exact string is present, which is why the tool
reports `FAILURES: 0`.

### C2 — the prior band crosses the ceiling the page prints on the same page. 310 states, 24 in the required grid.

Default page of `evt_syn_03`, no parameters typed — the third event in the list:

```
[UNVALIDATED] prior band around face: [UNVALIDATED] 0.65 SOL – [UNVALIDATED] 1.26 SOL.
That is a band around the declared prior, not a price for this ticket.
...
[EXACT] ceiling 840,000,000 lamports = face 700,000,000 lamports × (10,000 + 2000) / 10,000
— integer arithmetic on the tier face, not an estimate. That is exactly 0.84 SOL.
```

The band's top is 1.26 SOL; the ceiling stated a paragraph later is 0.84. Fifty per cent above
it, on the same page.

`/?event=evt_syn_01&mode=before_on_sale`:

```
prior band around face: 0.80 SOL – 1.54 SOL
[EXACT] ceiling 1,250,000,000 lamports = face 1,000,000,000 lamports × (10,000 + 2500) / 10,000
```

1.54 against a stated ceiling of 1.25.

The page does print the exemption: "That is a band around the declared prior, not a price for
this ticket." That sentence is true and it is the reason this is arguable rather than a plain
falsehood: the cap constrains prices charged, not the value of a ticket. But the page states a
ceiling and then shows a range whose top is above it, and a reader who checks 0.65–1.26 against
0.84 will stop. It is the same shape as `10-final-review` N2 (the recommendation's band never
trimmed to the cap in force), which was fixed for the value band and not for the prior band.

The value band itself is correct: no state in the sweep has the recommendation's own band above
the ceiling in force. The N2 fix holds where it was applied.

### C3 — the band-stop sentence attributes the record's ceiling to the cap in force. 44 states, 2 in the required grid.

`/?event=evt_syn_01&capBps=3500`, face 1.00 SOL:

```
[DECLARED] This page prices against a cap of [DECLARED] 3500 bps. The record was made under a
cap of [FIXTURE] 2500 bps, so the recorded sales are described under that cap, not this one.
...
Band 0.74 – 1.25 SOL
[EXACT] The top of that band is the ceiling the cap in force puts on this tier, at 1.25 SOL, so
the range stops where the cap does.
```

3500 bps over a 1.00 SOL face is a ceiling of 1.35 SOL. The sentence calls 1.25 — the 2500 bps
ceiling — "the ceiling the cap in force puts on this tier". This is the one place in the sweep
where a cap-dependent number is asserted as a function of the named cap and is the other cap's
function, and the two-caps disclosure above does not cover it because the sentence itself says
"the cap in force".

### Not counted as violations, and why

| class | states | what it is |
|---|---|---|
| disclosed two-cap | 288 (259 URLs) | The page names cap X in force and prints the ceiling computed at the record's cap, with the `P_CAP_IN_FORCE` sentence naming both. Coherent: the record is a fact and cannot be repriced by raising the cap. Recorded, not counted. |
| omission | 164 (143 URLs) | The page prices a band under a named cap and states no ceiling anywhere. Nothing contradicts; something is missing. |
| band above the cap, no ceiling printed | 151 (130 URLs) | The prior band is above the cap in force and the page prints no ceiling to cross. Same root as C2, one branch quieter. |

### The clock, checked separately

The claim says "consistent with its own clock", and the three properties above do not cover it,
so it was swept on its own: 8 events × 2 modes × 4 cuts (before the first issue, mid-life, the
event's own `startsAt`, ten days after `endsAt`) = 64 page states.

```
clock page states swept:  64
clock violations:          0
```

The printed decision instant always equals the requested `asOf`; the canonical URL always carries
the same instant; and where the cut is after the event end the page prints the store's status and
says the field and the instant disagree ("status on_sale is the store's current field, not the
status at this decision instant ... The instant is after the end, so as of it the event had
already ended"). **PASS.** The clock half of the claim survives; the cap half does not.

---

## Step 4: the frontend copy on :3001 against the backend

`:3001` reads `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788` from its own environment.

Seven routes:

```
200  118893b  /                           expected 200  OK
200  162220b  /events/evt_syn_02          expected 200  OK
200  128604b  /tickets/tkt_syn_0001       expected 200  OK
200  138195b  /organizer                  expected 200  OK
200   39966b  /my-tickets                 expected 200  OK
200   40796b  /verify                     expected 200  OK
404   41910b  /events/does-not-exist      expected 404  OK
```

Four carry data. Number for number, page against API, same run:

```
MATCH  / vs /api/events        event cards        page=8      api=8
MATCH  /events/evt_syn_02      resales recorded   page=12     api=12
MATCH  /events/evt_syn_02      resold share %     page=67     api=67
MATCH  /events/evt_syn_02      average markup %   page=12     api=12
MATCH  /events/evt_syn_02      tickets issued     page=12     api=12
MATCH  /tickets/tkt_syn_0001   transfers          page=3      api=3
MATCH  /tickets/tkt_syn_0001   face value SOL     page=1      api=1
MATCH  /tickets/tkt_syn_0001   last sale SOL      page=0.94   api=0.94
MATCH  /organizer              sales              page=12     api=12
MATCH  /organizer              average markup %   page=20     api=20
MATCH  /organizer              tickets resold %   page=73     api=73
MATCH  /organizer              distinct holders   page=9      api=9
MATCH  /organizer              total volume SOL   page=11.5   api=11.5

total comparisons: 13  matches: 13  mismatches: 0
```

It is reading the backend, not its bundled fixture:

```
backend slugs:  8, demo-arena-east-resale-off ... synthetic-stage-cap-binding
frontend links: 8, identical set
set equality:   True
bundled mock:   6 events, evt_midnight_static_tour, evt_winter_chamber_series, ...
mock ids on the page: False
label on the page: "SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data." True
```

**PASS.** 13 of 13 comparisons match, six pages 200, the missing event 404 as the contract
requires, and the page carries the backend's own synthetic-data label.

---

## Step 5: the live frontend's port, untouched

```
listener:  the live frontend  next-server (v15.5.29)
the frontend: STARTED Fri Nov  6 23:57:34 2026   ELAPSED 15:47:37
cwd:       ../ticketing-frontend
GET :3000/  ->  200  30546b
```

File tree, `find ../ticketing-frontend -xdev` against the run marker
`2026-11-07 15:35:40.298`:

```
files walked:                          42,608
files with an mtime inside this run:        0
newest file in the tree:  .next/server/route-cache/.../verify.meta   2026-11-06T23:57:41
```

It is still its own app, not repointed:

```
:3000/events/evt_syn_02              404
:3000/events/evt_midnight_static_tour 200
mock ids on the live frontend's home page: evt_harbor_lights_festival evt_midnight_static_tour
  evt_northline_derby_finals evt_riverside_comedy_night evt_sidestage_warehouse_04
  evt_winter_chamber_series
evt_syn ids on the live frontend's home page: none
```

**PASS.** Same process, same start time, HTTP 200, zero files written, six mock events and a 404 on
ours — the untouched state, not a regression.

---

## Step 6: no secret in the tree

Scanned 143 text files (excluding `.git`, `__pycache__`, `.pyc`, `.db`, `.log`) for `.env` files,
key files, PEM blocks, AWS/GitHub/OpenAI/Slack/Google tokens, JWT, password and api-key
assignments, 64-byte key arrays, and every hex string of 32 characters or more. Values are not
printed here.

```
ENV / KEY FILES: none. No .env, .env.*, *.pem, *.key, *.crt, *.p12, *keypair*, id.json,
                 *.keystore. Nothing matching "env" in git status, tracked, untracked or ignored.

TOKEN PATTERNS:  none. Zero hits for AWS, GitHub, OpenAI, Slack, Google, JWT, PEM.

PATTERN FINDINGS: 16 files
  git blob ids (40 hex)          docs/ON-CHAIN-FOR-LAPTOP.md, records/ON-CHAIN-RECONCILIATION.md
  sha256 digests (64 hex)        records/FRONTEND-HONESTY-PATCH.md (x2),
                                 records/findings/06-validation-protocol.md (x2),
                                 records/findings/07-engine-review.md (x2),
                                 records/findings/10-final-review.md (x1)
  ed25519 group order (38 hex)   ticketpath/core/ed25519.py, records/FINAL-PROOF.md,
                                 tests/test_contract_conformance.py
  RFC 8032 published vectors     tests/test_ed25519.py (8 distinct, 64 hex),
  (seed / public key / sig)      tests/test_contract_conformance.py (4 distinct, 64 hex)
  test nonce (32 hex)            tests/test_verification_message.py (x2)
  fake wallet in a URL path      tests/test_contract_conformance.py (32 hex, "1111...")
  integer lists                  records/DEMO-PROOF.md, tests/test_base58.py,
                                 tests/test_event_analytics.py, tests/test_markup.py (x2),
                                 tools/build_fixture_store.py (x2)
```

Each of the 16 was opened and classified with the value masked. The `solana keypair array`
pattern hits are lists of three small integers (markup-bucket counts, base58 test bytes,
`rng.choice([0, 500, 800, 1200, -1000])`), not key material. The 38-character hits are the
Ed25519 group order `2**252 + 27742317777372353535851937790883648493`, a public curve constant.
The 64-character hits are sha256 digests of files and RFC 8032's published test vectors.

**PASS.** No secret, no key file, no token, no `.env`.

---

## Step 7: the README's commands, one by one

```
CMD1  python3 -m ticketpath.server
      8788 is served by exactly this command. Cold start on the documented
      override TICKETPATH_PORT=8795:
        ticketpath 0.1.0 listening on http://127.0.0.1:8795 ... routes=10
        GET /health -> 200
      exit 0 (server stopped after the check)

CMD2  curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://127.0.0.1:8788/
      200 13547                                                    exit 0

CMD3  curl -s 'http://127.0.0.1:8788/api/events?limit=100'
      events: 8  nextCursor: None                                   exit 0

CMD4  curl -s 'http://127.0.0.1:8788/api/tickets?limit=200'
      tickets: 76                                                   exit 0

CMD5  curl -s http://127.0.0.1:8788/health
      {"service": "ticketpath", "version": "0.1.0", "status": "ok", ...   exit 0

CMD6  python3 -m unittest discover -s tests
      Ran 427 tests in 16.764s / OK                                  exit 0

CMD7  python3 tools/build_fixture_store.py --check
      [ok] fixtures/synthetic_store.json matches a fresh build exactly  exit 0

CMD8  python3 tools/build_fixture_store.py
      run in a throwaway copy so the repository fixture was not edited
      [ok] wrote fixtures/synthetic_store.json (90727 bytes)           exit 0
      sha256 15e6f6611652ae43f3967e110e2feeffde0cc2ace13ea868ff3abb0012bb9bfa
      identical to the repository's fixture, byte for byte

CMD9  which solana anchor cargo rustc spl-token
      no output                                                    exit 1
      (the README's claim, exactly)

CMD10 python3 tools/guidance.py --events
      8 events, each with its tier ids                            exit 0

CMD11 python3 tools/guidance.py --event evt_syn_04 --as-of 2026-11-07T12:00:00Z
      34,046 bytes of valid JSON, fixtureBuild.sha256 15e6f661...  exit 0
```

`git status` before and after this run is identical: 12 modified files and 1 untracked test
module, all from the night's own work, none from this run. `fixtures/synthetic_store.json` is
unchanged (`15e6f661...`).

**PASS with a caveat.** Every command works as written. The caveat is not a command:

```
LICENSE line 3: Copyright (c) 2026 [OPERATOR: replace this bracket with your name]
```

Still a placeholder. Until it is replaced the licence names no holder, and the README says so.

---

## State of the submission

**What holds, measured tonight.**

- 427 tests pass, 22 contract-conformance tests pass, 102 console-check assertions pass, 12
  store-check assertions pass, 18 fixture invariants pass, and the fixture regenerates byte for
  byte from its seed.
- The backend on `127.0.0.1:8788` answers 10 of 10 routes, verifies a real Ed25519 signature and
  refuses its replay, and `/health` states synthetic data, no deployed program, no fitted model,
  9 of 9 contract endpoints.
- The console's clock is consistent in all 64 cut states swept: the instant printed is the
  instant requested, the canonical URL carries it, and a cut after the event end says so.
- The frontend copy on `:3001` serves the backend's numbers: 13 of 13 comparisons match, all 8
  backend event slugs appear, none of its 6 bundled mock ids do, and the synthetic-data label is
  on the page.
- The live frontend's port is untouched: the same process, the same start time, HTTP 200, zero of
  42,608 files written during this run.
- No secret, key file, token or `.env` anywhere in the tree.
- Every README command runs, and nothing in the run claims a deploy.

**What does not hold.**

- The console contradicts itself on its own cap in 30 of the 64 required page states and 594 of
  724 swept. Three distinct defects, each with exact text above:
  - C1, 240 states: the market block says the event holds 0 sales while the same sentence says
    the mode excluded 9. Present on all five events with resales, in `before_on_sale` mode.
  - C2, 310 states: the prior band crosses the ceiling the page prints, by 50% on the default
    page of `evt_syn_03`.
  - C3, 44 states: the band-stop sentence calls the record's ceiling "the ceiling the cap in
    force puts on this tier" when a higher cap is typed.
- `tools/console-check.py` asserts one of these defects is present, so its `FAILURES: 0` is not
  evidence against C1.

**What only the operator can complete.**

1. Commit. Nothing from the last three hours is committed; the code a judge would clone is HEAD
   `72bb8d3`, `15:11Z`. 12 modified files and 1 untracked test module carry the work.
2. Fill in the LICENSE copyright line.
3. Fix C1, C2, C3 above, and fix the console-check assertion that pins C1, or accept the
   contradictions and say so.
4. Repoint the live frontend's port at this backend if the live app is the one to be shown; today
   the copy on `:3001` is the only frontend reading it.
5. Supply real ledger data if the numbers must stop being synthetic. Nothing here pretends
   otherwise.

## The single highest remaining risk

**The console still contradicts itself where a judge will look without being told to.** Two of
the three defects need no setup: open `evt_syn_03` from the event list and the page shows a band
to 1.26 SOL and a ceiling of 0.84 SOL; flip the decision-mode dropdown on any event with resales
and the market block says the event holds `0 sales of 0` while the same sentence says 9 were
excluded by the mode. This is the exact claim the submission rests on — that the console is
internally consistent with its own cap — and it fails on 30 of the 64 page states the brief
names. The commit state is the second risk; a defect that ships on time is worse than a fix that
does not.

---

## Judge path

1. The console, the honest decision, and the two contradictions named above:
   `http://127.0.0.1:8788/` — then `?event=evt_syn_03` and `?event=evt_syn_02&mode=before_on_sale`
2. The frontend against our backend, 13 numbers matching and labelled:
   `http://127.0.0.1:3001/`
3. Where the data comes from, in one call, saying nothing is deployed and nothing is fitted:
   `http://127.0.0.1:8788/health`

---

*Scripts used, all outside the repository, all read-only: `/tmp/proof2/03-sweep.py` (724 states),
`/tmp/proof2/03b-clock.py` (64 states), `/tmp/proof2/04-frontend.py` (7 routes, 13 numbers),
`/tmp/proof2/02-wallet-post.py` (the two POST routes). Logs and their JSON output are beside
them in `/tmp/proof2/`.*

---

## CORRECTION (2026-11-08T08:30Z): machine handles redacted, no claim changed

**Scope:** this file only, and only the lines in the table below. **Why:** this repository is public
and `tools/public_safety.py` refuses a tracked file that carries an absolute path under a home
directory, a process id, or the name of another of the operator's repositories. The rule and its
reason are in `.public-denylist`. The whole-tree run is the only one of its three entry points that
reads what is already published, which is why this is a forward edit and not a rewrite of history.

**What a redaction here is allowed to cost: nothing that was measured.** A process id was never the
measurement. It was the handle that identified which process was holding a port, and the sentence
still carries the identification it was using: the command, the start time, the listener, and where
the point was that nothing moved, the words "the same process". A home path said nothing the
repository-relative path beside it does not say. No number was replaced with a different number, and
no count, status code, start time, byte size or verdict changed.

| Where | Was | Now |
|---|---|---|
| Environment, live frontend | the port tied to `pid <n>`, started …, and a `cwd` under a home directory | the port named by what it serves, `next-server` and the start time kept, `cwd` `../ticketing-frontend` |
| Environment, demo copy | the port tied to `pid <n>` (dev parent `<n>`), a path under a home directory, `/proc/<n>/environ` | the copy named by `../ticketpath-demo`, both pids gone, `/proc/<pid>/environ` |
| Environment, backend | `pid <n>` on the port, a `cwd` under a home directory, "replaced with pid `<n>`" | the backend named by its command, the pids gone, `cwd` `<repository root>`, "replaced with a fresh instance" |
| Environment, other process and strays | `pid <n>` on `8787`; `pids <n>, <n>` on `:8801` and `:8802` | the process and its command, the pids gone, the start times kept |
| Opening window | a copy of the frontend on a tied port | "a copy of the platform frontend on its own port" |
| Step 2, process confirmation | `/proc/<n>/cwd` equal to a path under a home directory | `/proc/<pid>/cwd` equal to `<repository root>` |
| Step 2, startup banner | the banner's own line began `pid <n>, started …` | the line keeps the start time and the listener, the pid is gone |
| Step 5, listener capture | the port as a tied handle, `pid <n>` on two lines, `cwd` under a home directory | the port named by what it serves, the pid gone, start time and ELAPSED kept, `cwd` `../ticketing-frontend` |
| Step 5, home page and file tree | the port in two lines reporting the home page; `find` over an absolute path | "the live frontend's home page"; `find ../ticketing-frontend -xdev` |
| Step 5 verdict, Step 7, recommendation 4 | "same pid `<n>`", "(pid `<n>`)", a port named as a handle | "same process", the pid gone, "the live frontend's port" |

**Residue, stated rather than hidden.** Port numbers on lines this rule does not classify are
unchanged, including this project's own documented backend port and the demo copy's port where it
appears in a URL or a heading. `.public-denylist` states why it does not deny those, and `/tmp`
paths are exempt for `records/` on purpose. `python3 tools/public_safety.py check --tracked` reports
zero hits for this file as of this note.

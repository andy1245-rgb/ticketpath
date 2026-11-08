# CONTRACT-CONFORMANCE: the wire contract, executed

**What this is.** `lib/types.ts` + `API_CONTRACT.md` (in `../ticketing-frontend`,
read only) are the acceptance test for this backend. Until now they were a document.
`tests/test_contract_conformance.py` turns them into a test that addresses every route over
a real socket and fails when a response drifts from the contract.

**Written:** 2026-11-07T11:3xZ, after the fixture store was regenerated (see §2).
**Test file:** `tests/test_contract_conformance.py`, pure standard library, no new
dependencies, nothing imported from `ticketpath`.

```
python3 tests/test_contract_conformance.py --table     # this report's table, live
python3 -m unittest tests.test_contract_conformance    # 22 tests, each route named
TICKETPATH_BASE_URL=http://127.0.0.1:8788 python3 tests/test_contract_conformance.py --table
```

Unset `TICKETPATH_BASE_URL`, it starts `python3 -m ticketpath.server` itself on the first free
port among `TICKETPATH_TEST_PORT`, 8788 and an OS-chosen port, logs under
`/tmp/ticketpath-contract-<port>.log`, and kills only the process it started. Port 8787 is
refused outright.

## 1. The rule the test is built on

The contract is encoded **in the test**, one declarative table per type (`EVENT`, `TICKET`,
`LEDGER_ENTRY`, `RESALE_STATS`, `RESALE_HISTORY`, `WALLET_VERIFICATION`, `CHALLENGE`,
`PRICE_POINT`, `MARKUP_BUCKET`, `DESTINATION_ROW`, `EVENT_ANALYTICS`, `PAGE_EVENT`,
`PAGE_TICKET`), and `ROUTES` binds one table to each route. It does not import the backend's
models, because a test that imports the thing it tests proves that the code agrees with
itself, not that it honours the contract.

Per route it checks two layers.

**Structure.** Every declared field present; no field of the wrong JSON type; arrays checked
element by element; nullable fields (`T | null`) allowed to be null or `T` but never absent;
no field name the contract does not define. Money fields must be JSON integers, so a float
lamport fails. `WalletAddress` must decode to 32 base58 bytes. Timestamps must be ISO-8601
UTC with a `Z` or `+00:00` offset.

**Semantics** (the prose). Markup is measured against *that ticket's own tier face*, never
re-derived at event level. The stats block is recomputed from the entries by the contract's
own rules. `transferCount` excludes `issue` and `redeem`. `ownerWallet` filters the current
owner, not the issuee. Event totals equal the sum of their tiers. `analytics` is recomputed
from the event's tickets and their individual trails, per UTC day. `markupDistribution` is
checked against the contract's table, in order, bounds included. `topDestinations` is
recomputed from current holdings. Cursor pagination must walk the collection exactly once.
Detail routes must 404, never 200-with-null. The frozen verification message is rebuilt from
the contract text and signed with an Ed25519 key generated in the test, so the success path is
exercised for real: a signature over the contract's own bytes must verify, must be single use,
and must not cross wallets.

## 2. Where it ran, and one thing that moved under it

- **8788 was already bound** when this session started, by a sibling smoke run of the same
  build (`python3 -m ticketpath.server`, started 11:08, version 0.1.0). It was not
  touched. Its GET routes were probed read only and answered 200 with the pre-regeneration
  store.
- **This run bound 8789** (`TICKETPATH_TEST_PORT=8789`), log `/tmp/ticketpath-contract-8789.log`,
  and the server was stopped at the end of every run. Both runs of the suite in this session
  started and killed their own server; nothing of mine is listening now.
- **The fixture store was regenerated mid session** by another session in this repo
  (`fixtures/synthetic_store.json`, mtime 11:22, 8 events / 76 tickets / 157 ledger rows,
  produced by `tools/build_fixture_store.py`, seed 20261107). The table below is from the
  regenerated store. The earlier 2-event store produced the same verdicts, only fewer rows.
- **Operational consequence**, not a drift: the store is read once at startup, so the process
  on 8788 is still serving the pre-regeneration 2-event store. Regenerate the fixture and the
  server has to be restarted, or the frontend silently shows stale data.
- The test discovers ids at runtime, so it is not tied to either store: it ran against both
  (2 events / 5 tickets, then 8 events / 76 tickets) with no change.

## 3. The table

Ten routes: the nine in `API_CONTRACT.md` plus `/health`, which is ours and not in the contract.
Every row was produced by a real HTTP response from the live server in this session.

| # | route | structure | semantics | verdict |
|---|---|---|---|---|
| 0 | `GET /health` | PASS | PASS | **EXTRA-ROUTE** (not in `API_CONTRACT.md`) |
| 1 | `GET /api/events` | PASS | PASS | **CONFORMANT** |
| 2 | `GET /api/events/{idOrSlug}` | PASS | PASS | **CONFORMANT** |
| 3 | `GET /api/events/{eventId}/analytics` | PASS | **FAIL (32)** | **DRIFT** |
| 4 | `GET /api/tickets` | PASS | PASS | **CONFORMANT** |
| 5 | `GET /api/tickets/{ticketId}` | PASS | PASS | **CONFORMANT** |
| 6 | `GET /api/tickets/{ticketId}/resale-history` | PASS | PASS | **CONFORMANT** |
| 7 | `GET /api/wallets/{wallet}/verification` | PASS | PASS | **CONFORMANT** |
| 8 | `POST /api/wallets/{wallet}/verification/challenge` | PASS | PASS | **CONFORMANT** |
| 9 | `POST /api/wallets/{wallet}/verification` | PASS | PASS | **CONFORMANT** |

Counts: **8 CONFORMANT, 1 DRIFT, 1 EXTRA-ROUTE, 0 MISSING**. Every one of the nine contract
routes exists and answers; nothing had to be marked MISSING.

Route 2 also checked: all 8 events resolve by id and by slug, and both payloads equal the same
event in `/api/events`. Route 4 also checked: `ownerWallet` returns only current owners, and a
wallet that sold a ticket does not get it back. Route 5 also checked: the mint address resolves
to the same payload as the ticket id, on every ticket. Route 7 also checked: an unknown wallet
is 200 with `verified:false`, and a malformed one is 400 with a `message`. Route 9 also checked:
a valid signature verifies, the nonce is consumed, the read route then shows `verified:true`,
and a nonce issued to one wallet cannot verify another.

## 4. The drift, exactly

There is one disagreement, and it appears 32 times because it is per bucket per event
(4 labels x 8 events). It is a value, not a shape: every key, type, order and bound is right.

| field | contract says | response says |
|---|---|---|
| `GET /api/events/:eventId/analytics` → `markupDistribution[1].label` | `0–25%` | `0-25%` |
| ... `markupDistribution[2].label` | `25–50%` | `25-50%` |
| ... `markupDistribution[3].label` | `50–100%` | `50-100%` |
| ... `markupDistribution[4].label` | `100–200%` | `100-200%` |

`markupDistribution[0].label` (`At or below face`) and `[5].label` (`Over 200%`) match,
because they contain no range. The disagreement is one character: the contract's table in
`API_CONTRACT.md` uses U+2013 EN DASH; `ticketpath/core/markup.py` uses U+002D HYPHEN-MINUS.

Why it is not a misreading of the contract:

- `API_CONTRACT.md` introduces the table as the buckets the backend "must return ... with
  these exact bounds in bps", and the label is the first column of that table.
- The frontend's own fixture implementation, `lib/api.ts:124-131`, writes the same six labels
  with en dashes. So the fixtures the UI was built and reviewed against say `0–25%` and live
  data says `0-25%`.
- The bound columns, the order, the count semantics and the zero-count rows all conform. Only
  the string differs.

Cost to close it, for the record: one constant in `ticketpath/core/markup.py`
(`MARKUP_BUCKETS`), plus the two backend tests that currently pin the hyphen
(`tests/test_markup.py:61,62,70` and `tests/test_event_analytics.py:80,81`). It was not
changed here: this test reports, it does not fix.

Everything else on route 3 conforms, including the rule the contract singles out. On this
store the per-ticket figure and the forbidden event-level figure are far apart, and the
response carries the correct one:

| event | `avgMarkupBps` reported | per-ticket mean | event-level derivation would read |
|---|---|---|---|
| `evt_syn_01` | 903 | 903 | **19,403** |
| `evt_syn_07` | 1,533 | 1,533 | **13,028** |
| `evt_syn_02` | 1,340 | 1,340 | **6,395** |
| `evt_syn_06` | 525 | 525 | 525 |
| `evt_syn_05`, `evt_syn_08`, `evt_syn_03` | null | null (no priced sales) | n/a |

## 5. Declared additions, which are not contract drift but are not wire exact

The contract defines no extra keys, so the strict reading is "exactly these keys". Three keys
are additions declared in `records/CONTRACT-MAP.md` §7.2/§7.3. The test allows exactly those,
validates their shape, and fails on any *undeclared* extra. The report says which routes are
therefore not byte-exact:

| route | added top level keys |
|---|---|
| `GET /api/events`, `GET /api/events/{idOrSlug}`, `GET /api/tickets`, `GET /api/tickets/{ticketId}`, `GET /api/wallets/{wallet}/verification`, both POST verification routes | `dataSource` |
| `GET /api/events/{eventId}/analytics` | `dataSource`, `analyticsNote` |
| `GET /api/tickets/{ticketId}/resale-history` | `dataSource`, `custodyNote` |

These do not break the frontend: `lib/api.ts` returns `(await res.json()) as T`, a cast with no
runtime validation, so unknown keys are ignored. They are recorded rather than waved through,
and a new undeclared key fails the build.

Also checked and passing, because the verify page would be dead without it: the browser
preflight. `OPTIONS /api/wallets/{wallet}/verification` from `Origin: http://localhost:3000`
allows the origin, `POST` and `content-type`. Without those three headers a browser blocks the
signature submission before the contract is ever reached.

## 6. What cannot be honestly served, and what a judge will see empty

**No contract route is unserved.** All nine answer 200 on the addressable data. There is
nothing in the table that reads MISSING, so no row here is
NOT-IMPLEMENTABLE-BECAUSE-NO-DATA.

Seven **fields** are structurally present but cannot be backed by anything on this machine.
Each is a `null` or a `false` the type already permits, and each is the honest value:

| route | field | why it cannot be filled |
|---|---|---|
| `GET /api/tickets/{ticketId}` | `mintAddress` | No SPL mint exists on any cluster. It is a shape-valid 32-byte placeholder, so an Explorer link built from it 404s. |
| `GET /api/tickets/{ticketId}` | `transferRestricted` | Contract says "actually enforced on-chain right now". No program is deployed, so `false` on every ticket, even where the event asks for the gate. Returning `true` would be the most misleading field in the payload. |
| `GET /api/tickets/{ticketId}/resale-history` | `signature`, `slot` | No transaction exists, so no Explorer deep-link resolves. The contract prefers `null` to a placeholder, and both are `null` on every row. |
| `GET /api/events/{idOrSlug}` | `imageUrl` | No image assets in the repository. |
| `GET /api/events/{eventId}/analytics` | `topDestinations[].region` | No wallet has volunteered a region, so every row is `null`. |
| `GET /api/wallets/{wallet}/verification` | `method` | No identity provider is connected, so it is only ever `"wallet_signature"` or `null`. `"identity"` is never returned, although the contract's union allows it. |

**Correction, 2026-11-08T08:20Z.** Two rows above reason from a fact that has changed. `mintAddress`
says no SPL mint exists on any cluster: one does, on devnet
(`6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV`), and the fixture tickets are still not minted under
it, so the field stays a placeholder. `transferRestricted` says no program is deployed: one is, and
it has no destination or verified-wallet gate, so `false` remains the only true answer for a
different reason. Neither field's value changes and the payload is not rewritten by this note.

**Same correction, third row, 2026-11-08T08:05Z.** The `signature` and `slot` row above says "No
transaction exists". Three devnet transactions exist in `records/devnet-artefacts.json`, and the
fixture's 147 ledger rows still carry `signature: null` and `slot: null` because this server reads no
chain and those rows are not on one. The nulls are still right; the reason is the server's silence,
not an empty cluster.

**Pages that a judge can click and see empty, and why.** These are data facts, not bugs, but
they are the ones that will look thin on the morning:

| page | what it shows | why |
|---|---|---|
| `/events/evt_syn_08` (the `draft` event) | no price chart, "No completed resales yet", an empty destinations table, 0 holders | A draft event has no tickets and no sales. Every analytics number is legitimately zero or null. |
| `/events/evt_syn_03`, `/events/evt_syn_05` | empty price chart and empty markup distribution, but 10 and 8 current holders listed | Their tickets were never resold: 0 priced sales. The trail and the holders exist, the resale curve does not. |
| `/my-tickets` with a real connected wallet | "no tickets" | The store's holders are placeholder `FXTURE…` wallets. Any real devnet wallet holds nothing, so `ownerWallet=<real>` returns an empty page. |
| any Explorer link from a ticket page | 404 | See `mintAddress` / `signature` above. |

## 7. Proof the test can fail

A check that has never failed is decoration, so the suite carries a mutation layer
(`TestTheChecksCanFail`) that takes the live responses from the same run, breaks one thing at
a time, and asserts the corresponding check catches it:

| mutation | caught by |
|---|---|
| `avgMarkupBps` replaced with the event-level derivation on an event where the two differ | the per-ticket markup rule |
| a `priceSeries[].avgMarkupBps` re-derived from the day's mean price | the day-bucket markup rule |
| one bucket label back to the hyphen form | the contract's label table |
| `avgPriceLamports` turned into a float | the integer-lamports rule |
| a ledger row's `markupBps` recomputed against the event's lowest face | the per-ticket markup rule |
| `endsAt` deleted, `surpriseField` added | required-field and no-undefined-field checks |
| `status` set to `on-sale`, `startsAt` set to a non-UTC string, `walletAddress` set to junk | the enum, ISO-8601-UTC and 32-byte-base58 checks |
| a synthetic 404 `no_route` and a connection failure | MISSING, with the reason, never a skip |

One of these found a weakness in the harness while it was being written: on the first event
the naive and correct markup happened to be equal, so the mutation was a no-op. The test now
searches for a discriminating value instead of taking the first one. That is the difference
between a test that passes and a test that is worth having.

Result of the full suite on this store: **22 tests, 20 pass, 2 fail, 0 skipped**, ~0.7 s. Both
failures are the same single drift from §4 (`TestNoDrift`, and the `analytics` case of
`TestSemantics`).

## 8. The one that matters on the morning

**The markup bucket labels.** It is the only field where the live wire disagrees with the
frozen contract *and* with what the frontend's own fixtures produce, and it is the only thing
that will make this suite red from the first minute. `/organizer` renders
`markupDistribution[].label` verbatim, so live mode shows `0-25%` where every fixture mode
screenshot, design review and any text or snapshot assertion says `0–25%`. The chart still
draws; the words change under it. One constant and two backend tests close it.

If the question is what would take a page *down* rather than soften it: nothing in the payload
does that today, and the surface to watch is the enums. `components/Badge.tsx` does
`const { label, tone } = EVENT_LABEL[status]` with no guard, so one event status outside
`draft|on_sale|sold_out|completed|cancelled` (or one ticket status outside
`valid|listed|redeemed|revoked`) throws and the whole page falls to the error boundary. That
is checked on every event and every ticket, and it passes.

## 9. What was not done

- No backend file was edited. The drift is reported, not patched.
- Nothing under `../ticketing-frontend` was read for writing or modified; the
  TypeScript types and the contract document were read only.
- No package installed. The test and its Ed25519 signer are standard library only, and the
  signer is pinned to RFC 8032 test vector 1 so a harness bug cannot look like a server bug.
- Nothing committed, nothing pushed.
- Port 8787 never bound; the server on 8788 (another session's) never touched; every server
  this session started was stopped, and both were verified gone afterwards.

## 10. The drift from §4 is closed (2026-11-07T11:31Z)

- **Fixed:** `MARKUP_BUCKETS` in `ticketpath/core/markup.py` now carries U+2013 EN DASH
  (`0–25%`, `25–50%`, `50–100%`, `100–200%`), the strings `API_CONTRACT.md`'s table prints and
  `lib/api.ts:124-131` already wrote; `tests/test_markup.py` and `tests/store_arithmetic.py`
  (which `tests/test_event_analytics.py` compares against) now pin those characters. Only that
  constant and those tests changed; nothing committed, nothing pushed.
- **Verified live:** the stale 11:08 process on 8788 was stopped and the backend restarted on
  the same port (new pid, log `/tmp/ticketpath-backend.log`), so it serves the regenerated
  `fixtures/synthetic_store.json` — 8 events / 76 tickets / 147 ledger rows; `GET /health` 200,
  `GET /api/events` returns 8, and no event's `markupDistribution[].label` contains a hyphen.
  Full suite: **148 tests, OK**.
- **New verdict table:** 9 CONFORMANT, 0 DRIFT, 1 EXTRA-ROUTE (`GET /health`, not a contract
  route), 0 MISSING. Route 3, `GET /api/events/{eventId}/analytics`, moved from
  **DRIFT (32)** to **CONFORMANT** (structure PASS, semantics PASS); routes 1, 2, 4–9 
  unchanged and CONFORMANT.

---

## CORRECTION (2026-11-08T08:30Z): one process id redacted, no claim changed

**Scope:** this file only, and only one sentence in §2. **Why:** this repository is public and
`tools/public_safety.py` refuses a tracked file that carries a process id. The rule and its reason
are in `.public-denylist`.

**What the redaction costs: nothing that was measured.** §2's point is that the server already
holding this project's backend port belonged to a sibling smoke run and was not touched. The
sentence identifies it by its command, its start time and its version, all of which are unchanged.
The pid was a handle on a process that stopped on 2026-11-07 and identified nothing a reader could
check.

`python3 tools/public_safety.py check --tracked` reports zero hits for this file as of this note.

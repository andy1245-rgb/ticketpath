# 10 — Final independent review of the Ticketpath console and engine

**Status:** review complete. One file written, this one. No fix applied by me, no commit, no push, no dependency installed, no state file written.
**UTC:** 2026-11-07T14:25Z. **Agent:** independent reviewer. I did not build, fix or operate any part of this tree before this pass.
**Reviewed:** the whole of `ticketpath/`, `tests/`, `tools/`, `fixtures/` as it stands now, against the earlier reviews (`07-engine-review.md`, `08-fix-verification.md`) and the five fix reports appended to `records/BUILD-REPORT-CONSOLE.md` (12:45Z, 13:08Z, 13:40Z, 13:58Z, 14:10Z).

**The product tree did not move during this pass.** Suite 391 before I started and 391 at the end; the store hash is the hash the first review pinned. One file appeared while I worked — `docs/morning.html` at 14:20Z, written by another session, outside this review's scope and not touched by me. `ticketpath/`, `tests/`, `tools/` and `fixtures/` did not change.

| File | sha256 (first 16) |
|---|---|
| `ticketpath/server.py` | `f14961ca2591c1b0` |
| `ticketpath/orchestrator.py` | `32f3f440330ee72a` |
| `ticketpath/console/blocks.py` | `1e6a6e99d13d5b59` |
| `ticketpath/console/page.py` | `893cccb39144d19e` |
| `ticketpath/console/units.py` | `38e435a993d08016` |
| `ticketpath/core/labels.py` | `631746f71f0436d3` |
| `ticketpath/core/value_band.py` | `a094e3ff2477f478` |
| `ticketpath/core/price_features.py` | `6f465ce418e2c10d` |
| `ticketpath/core/primary_optimum.py` | `53322138877df920` |
| `ticketpath/core/intensity.py` | `03fc81534f3e6316` |
| `ticketpath/api/guidance.py` | `2c97d3977ccdafa5` |
| `ticketpath/adapters/ledger_adapter.py` | `4b11dd712e5afa36` |
| `tools/console-check.py` | `bd9b679c7926d04e` |
| `tools/console-check-stores.py` | `f8c24935e8d7ed2d` |
| `tests/test_cap_and_loader_refusals.py` | `2dc0de323e8ff577` |
| `tests/test_console_cap_field.py` | `d13672c517b3259f` |
| `tests/test_console_fixes.py` | `84eea7e93c13ce25` |
| `fixtures/synthetic_store.json` | `15e6f6611652ae43` (`15e6f6611652ae43f3967e110e2feeffde0cc2ace13ea868ff3abb0012bb9bfa`) |

**Ports.** My console ran on `8841` (fixture store) and `8843` (empty store); both are stopped. `8788` is the instance another session is running; I read it once through a URL the checker prints and otherwise ran my own. `8787` was **not bound and not used for any reading**; the only request I sent it was one `GET /` at the very end to confirm it was still serving after my runs (302), and nothing was taken from it. The live frontend's port and `../ticketing-frontend` were not touched. The operator's fleet tool repositories were not read or written.

**What I did not review.** The Next.js frontend; the Solana program (none exists); the literature claims in the findings; the six records row by row; the wallet cryptography; anything about the operator's accounts or a real ledger. The store is synthetic and the chain slot is absent. I did not re-litigate the engine's design choices that the first review already recorded as narrowings; I checked whether the fix passes changed them and whether the new code is right.

---

## 0. The four verdicts, up front

| Area | Verdict | The statement that stands |
|---|---|---|
| **Mathematics** | **STANDS-WITH-NARROWING** | The arithmetic that is implemented is right: the three regimes, the integer cap ceiling and cap refusal in both directions, the two-sided band at a declared τ, the gamma–Poisson zero, the per-tier face, the [EXACT] equality. The narrowing is that the headline is still a resale-value/cap floor presented as a primary price (07 §2.8's D1 fork is now labelled, not resolved); the ticket-day denominator does not stop at the event end, so on a cut past the event the measured rate falls with the clock (4.3 vs 16.3 per 1,000 ticket-days at a 2027 cut on a static record); and the value band is never trimmed to a cap in force, so it can carry an upper end above the ceiling the page itself asserts. |
| **Honesty** | **FAILS** | The badge machinery, the mode label, the sentences 07 named, the [EXACT] line, the fee states and the cold-start rate all stand. But on `/?event=evt_syn_04&capBps=1700` — a page the console *instructs* the reader to create by typing a cap — the page says it prices against a cap of 1700 bps, reports that 7 of 12 sales are above that cap, and three times says this event has no resale cap so there is no ceiling. On `/?event=evt_syn_02&mode=before_on_sale` the strip still prints `0 resales` and `0 tickets` where the store holds 12 of each. On a store with one held-back event the strip says `7 events in the store` where the store carries 8. |
| **Code** | **STANDS-WITH-NARROWING** | The console is total and the loader is per-event: every input I tried, including four mutated stores, answers with an HTTP status and a rendered page, and the healthy events keep serving beside a rejected one. The narrowing is that the code is not correct yet: the exposure denominator runs past the event end, four renderer branches that ask "does this page have a cap?" read the recorded cap while the page prices against a candidate cap (one of the four was fixed at 14:10, three were not), the at-ceiling test carries a ±1 bp tolerance under an "exactly" sentence, and `TRACE` still gets Python's 501 page. |
| **Refusals** | **STANDS-WITH-NARROWING** | The refusal panel is never empty, every line is typed and plausible, the fee and cap refusals are conditional, the prior-only price and the no-pool value block are refused visibly. The narrowed part: in BEFORE-ON-SALE mode the zero-exposure refusal says `No ticket had been issued at this instant` where 12 issue rows exist, the market block's "no ceiling to count against" contradicts the cap refusal on the same page, and the cap refusal can fire on a store whose own recorded sale sits above its cap, in which case it blames "the price this record supports" for the store's inconsistency. |

The rest of this file is the evidence, then the fix list ranked by risk.

---

## 1. Run results

### 1.1 Suite, conformance, fixture, tools

| Command | Result |
|---|---|
| `python3 -m unittest discover -s tests -t .` | **Ran 391 tests in 14.446s — OK** |
| `python3 -m unittest tests.test_contract_conformance -v` | **Ran 22 tests in 0.690s — OK** |
| `python3 tools/build_fixture_store.py --check` | **exit 0**, store unchanged at `15e6f6611652ae43`, adapter accepts it |
| `python3 tools/console-check.py` (copy with `BASE` re-pointed to `8841`; the only change) | **FAILURES: 0** |
| `python3 tools/console-check-stores.py` | **FAILURES: 0** (4 held-back events + 4 healthy events on the same stores) |

The two tools hard-code `8788`; I ran a byte-identical copy of the first with only the URL constant changed so the measurement was against my own instance. `console-check-stores.py` starts its own ephemeral servers and needed no change.

### 1.2 The server and the walk

`python3 -m ticketpath.server --port 8841` on the shipped fixture. `/health` 200, `/` 200 (13,547 bytes), `/api/events` 200 (8 items, `nextCursor` null), `/favicon.ico` 204.

**Every event, every tier, both decision modes.** 15 tier pages across all 8 events: **all 200**. The event selector, the tier selector and the mode selector render on every 200 page I opened. Both modes were walked on `evt_syn_02`, `evt_syn_03`, `evt_syn_04` and on a cut after the event end.

**Token sweep.** 31 URLs (the default, all 8 events, the multi-tier events' non-default tiers, both modes, five cap states, four cuts, three fee states, `sim=1`, `tau=0.406`) were rendered to text and searched for `{'value'`, `{'badge'`, `{n}`, `None`, `nan`, `inf`, `NaN`, `undefined`, `[object`. **Zero occurrences.** The two renderer defects from 07 §C2/C3 are fixed and stay fixed.

### 1.3 Edge inputs named in the brief

| Input | URL | Status | What rendered |
|---|---|---|---|
| `capBps=0`, capped event | `/?event=evt_syn_01&capBps=0` | 200 | cap refusal, ceiling `1,000,000,000 lamports`, no price anywhere (grep for `1.03`: none), violation line `4 of 6 ... above this cap` |
| `capBps=0`, uncapped event | `/?event=evt_syn_04&capBps=0` | 200 | cap refusal, ceiling `800,000,000`; **strip still says "no resale cap, so no ceiling"** and the market block "there is no ceiling to count against" (N1) |
| cap just below the price | `evt_syn_02&capBps=1499` / `1500` | 200 / 200 | refused / `at least 1.38` unchanged — exact boundary at the ceiling |
| cap just above the price | `evt_syn_02&capBps=1501`, `1600`, `2500`, `10000` | 200 | `at least 1.38` in every one; the number does not move |
| cap between level and band top | `evt_syn_01&capBps=298` | 200 | `1.03` allowed (ceiling 1.0298), **band 0.74 – 1.25** and "We would not argue with any price in that range" (N2) |
| cut before issue | `evt_syn_02&asOf=2026-09-01T00:00:00Z` | 200 | `0 tickets`, `No ticket had been issued at this instant`, prior band 1.12 – …, store count `8 ... 1 with any resale` |
| cut at the first issue | `evt_syn_02&asOf=2026-09-11T11:00:00Z` | 200 | `1 ticket`, `1 ticket had been issued ... no ticket-day of exposure`, truth matches |
| cut after the event end | `evt_syn_02&asOf=2026-11-22T03:00:00Z` and later | 200 | `status on_sale` beside a post-end instant; **exposure 552.1 → 863.1 → 2079.1 and rate 16.3 → 10.4 → 4.3 as the cut advances** (N3) |
| large fee | `evt_syn_02&feeLamports=5000000000`, `10**15`, `10**15+1` | 200 / 200 / 400 | negative-net refusal with the shortfall / the same / `fee_invalid` |
| fee exactly at the price | `evt_syn_02&feeLamports=1380000000` | 200 | `0 SOL` net, not a negative |
| fee on a cap-refused page | `evt_syn_02&capBps=0&feeLamports=50000000` | 200 | no net line, no `no_fee_model` — silence |
| uncapped event | `evt_syn_04` | 200 | point 0.93, band 0.67 – 1.29, no cap sentence about a cap |
| event with no resales | `evt_syn_03`, `evt_syn_05`, `evt_syn_08` | 200 | prior band, `[DECLARED] 7.5` rate, `no_fee_model`, no price |
| tau extremes | `evt_syn_04&tau=0.10 / 0.406` | 200 | band 0.79 – 1.10 / 0.48 – 1.81, point fixed |
| `sim=1` | `/?sim=1` | 200 | five `[SIMULATED]` lines |
| empty store | `TICKETPATH_LEDGER_MODE=empty` on 8843 | 400 | rendered `no_ledger` page; `/api/events` 200 empty; `/health` 200 |
| unknown event / tier / bad asOf / bad cap / bad mode / bad fee | six URLs | 404 / 404 / 400 / 400 / 400 / 400 | all rendered, banners present |
| verbs | `HEAD`, `POST`, `PUT`, `DELETE`, `PATCH`, `OPTIONS`, `TRACE` on `/` | 200 / 405 / 405 / 405 / 405 / 204 / **501** | TRACE is Python's own page with no banner (N9) |

### 1.4 Mutated stores (the loader, measured through the console)

Each store is the fixture with one change, served by a real server built the same way `console-check-stores.py` builds one.

| Mutation | Status / what rendered |
|---|---|
| one sale at 0 lamports (`evt_syn_01`) | 422 `sale_not_priced` for that event; `evt_syn_04` still 200 and prices; **strip says `7 events in the store` while the file carries 8** (N6); `/api/events` lists 7 |
| a sale one hour after `startsAt` (`evt_syn_04`) | 422 `sale_after_event_start`; other events 200 |
| an event with no tiers, tickets kept | server starts; that event 422 `event_has_no_tier`; `/` 200; **strip says 7 of 8** |
| the only event rejected | `/` 422 with the typed reason (not `no_ledger`); `/api/events` 200 with an empty list; server up |
| a sale at exactly `startsAt` | accepted; 200; description switches to `path curvature +0.6465`; no crash, no log(0) |
| an event with no `endsAt` | 200; `ends None` is not printed — the block says `ends not recorded` |
| a sale with `priceLamports: null` | 200; the event prices; strip `11 resales`, market `8 sales`, **A1 "the ledger records 8 sales" where the tier's ledger holds 9 sale rows** (N10) |
| a sale one lamport below the ceiling | 200; **`8 of 9 recorded resales ... settled at exactly the ceiling`** where 7 are exact (N5) |
| a sale one lamport above the ceiling | 200; the recommendation is **refused** because the record's own sale exceeds the recorded cap; the market block still reports `8 at the ceiling` and no violation line is printed (N5) |
| a tier with no sales inside a sold event | 200; `basis: pooled_across_tiers`, band from the other tiers, prose says "a declared width around the record" without naming which record (N10) |

---

## 2. Re-test table

Every defect the earlier reviews named, in their own text. "Holds" means the named defect is no longer reproducible in the state it was named in. Where an adjacent input breaks the fix, the adjacent input is named and the finding is in §3.

### 2.1 The eight fixes in 07 §6

| # | Defect as named in 07 | Holds | Adjacent input I tried | Result |
|---|---|---|---|---|
| 1 | Console total (C1, C5, C8): three loader-valid stores gave no HTTP response | **yes** | tierless event that keeps its tickets; a store where every event is rejected; a sale exactly at `startsAt`; a sale with a null price; missing `endsAt` | every one answers: 422 with a typed reason, 200, or the labelled 500 page; no `HTTP 000`; `/health` stays 200 |
| 2 | Two renderer defects (C2, C3): a dict and a `{n}` on the page | **yes** | 31 URLs incl. all tiers, both modes, five cap states | zero wrappers, `None`, `nan`, `{n}` |
| 3 | Every label true (A1, A13, A17, A2, A16, zero rate, fee) | **on the states it named** | uncapped event + a URL cap | **breaks**: three sentences say "no resale cap / no ceiling" on a page that asserts a cap and a ceiling (N1) |
| 4 | Decision mode (D1): label the counterfactual, offer the real before-on-sale decision | **yes, as specified** | `mode=before_on_sale&asOf=<after ends>`; the mode's own strip | mode label, status/date, own-record exclusion, no-pool refusal all hold; the post-end cut contradicts the mode's premise (N8) and R1's counts remain (N4) |
| 5 | [EXACT] true at displayed precision | **yes** | the tool re-parses the printed numbers and re-does the multiplication; the 08 verifier's face-`900,000,001` case I did **not** re-run | `ceiling 1,125,000,000 lamports = face 900,000,000 × (10,000 + 2500) / 10,000`, `exactly 1.125 SOL`, and the headline `at least 1.125`; the printed equality re-computes |
| 6 | Ticket count cut-aware | **yes** | cut at 0, at the first issue, at 12 | `0`, `1`, `12`, each equal to a hand count of `issue` rows |
| 7 | Integer fee arithmetic, bound, negative-net state | **yes** | fee exactly at the price; one lamport above; `10**15`; `10**15+1`; on a cold event; on a cap-refused page | `0 SOL`, shortfall refusal, 400, silence where there is no price; the test now pins the half-up integer product at `2**53+1` |
| 8 | HEAD and POST methods | **yes for the verbs it named** | `PUT`, `DELETE`, `PATCH`, `OPTIONS`, `TRACE` | 405 with the rendered page for the first three, 204 for OPTIONS, **501 with Python's page for TRACE** (N9) |

### 2.2 The four defects in 08-fix-verification

| # | Defect as named in 08 | Holds | Evidence |
|---|---|---|---|
| 1 | The before-on-sale page said the event had no resale record while 12 sales were in the store (08 §3.1, R1) | **partly — the named sentence is fixed; the class is not** | the refusal sentence is now true and names the mode; **the strip still prints `[FIXTURE] 0 resales on this event · [FIXTURE] 0 tickets`**, the basis still claims `0 ticket rows exist in the store`, and the exposure refusal still says `No ticket had been issued at this instant` (N4) |
| 2 | The integer-arithmetic test did not pin integer arithmetic (08 §5) | **yes** | the test now asserts `(2**53+1) × 5000` half-up, a value only integer arithmetic produces |
| 3 | `assertLessEqual(value, value)` was a tautology (08 §5) | **yes** | gone from `tests/`; the cut-aware test now recounts the issue rows by hand |
| 4 | The before-on-sale test asserted the false sentences were present (08 §5) | **partly** | the suite's claim-class test now bans the prose forms and asserts the premise first; **`tools/console-check.py:140` still asserts `[FIXTURE] 0 resales on this event` and `[FIXTURE] 0 tickets` as correct**, so the fixer's checker pins the false counts (N4) |

### 2.3 The five residue items (13:40Z pass)

| # | Residue | Holds | Adjacent input | Result |
|---|---|---|---|---|
| 1 | R2: `1 ticket` beside "No ticket had been issued" at the first-issue instant | **yes** | two tickets issued at one instant (the pass's own plural case); a cut before issue | the sentence branches on the strip's own wrapper; zero keeps the original sentence; plural covered |
| 2 | R3: `PUT /` was a 501 Python page | **yes** | `DELETE`, `PATCH`, `OPTIONS`, `TRACE`, `CONNECT` | `DELETE` and `PATCH` are 405, `OPTIONS` 204, **`TRACE` 501** (N9); a body on a 405 does not poison the next request |
| 3 | R4: "A cap does not hide the price" on an uncapped event | **yes for that sentence** | an uncapped event *with a URL cap* | the cap line now follows the cap in force; **the strip, A2 and the market block still say "no cap / no ceiling"** on the same page (N1) |
| 4 | R5: `8 events on this platform` under "nothing after the instant enters any number" | **on the shipped store** | a store with one held-back event | **`7 events in the store` where the file carries 8**; the noun that was made true by naming the store is now false about the store (N6) |
| 5 | The counts inside A19 and A1 carried no badge | **yes** | the served HTML | every one is its own `.n` span beginning with a badge; stripping the spans removes the digits |

### 2.4 The two defects in the last fix pass (13:58Z and 14:10Z)

| # | Defect | Holds | Adjacent input | Result |
|---|---|---|---|---|
| 1 | The cap in force never reached the optimum (§5.2) | **yes** | cap swept in both directions: `1400/1499/1500/1501/1600/2500/10000` on a binding event, `0/298/1625/1632/2500` on a capped-not-binding and an uncapped event, and per tier on `evt_syn_07` | below the supported price → typed `recommendation_above_cap` and no number; at or above → the number is identical to the uncapped page; the allowance boundary is exactly the integer ceiling; per-tier on `evt_syn_07` (gallery refuses at 1000 bps, mezzanine and box price) |
| 2 | The loader admitted what the core cannot price (C8) | **yes** | the three named states, plus the mutations in §1.4 | each is a per-event 422 with a code and a sentence; the healthy events on the same server still 200; `/health` 200; the shipped store holds nothing back |

**Count of earlier defects that still stand in their named state: 1** — 08 §3.1/R1 (the before-on-sale record claim), still reproducible on the default before-on-sale page and still asserted by `tools/console-check.py`.

---

## 3. New findings

Each has the file and line, the URL or store that triggers it, and what I measured. Severity is my ranking for the fix list, not a claim about the size of the bug.

**The three questions the brief asked, answered directly.**

- *Does the recommendation respond to the cap in both directions?* **Yes for the number.** A cap below the price the record supports is refused with `recommendation_above_cap` and no number (`evt_syn_02` at 1499 refuses, at 1500 prices); a cap above it does not move the number (`1501`, `1600`, `2500`, `10000` all print `at least 1.38`; `evt_syn_04` at 2500 prints the same 0.93); the allowance boundary is exactly the integer ceiling, and it is per tier on `evt_syn_07`. **No for the band and the sentences around it**: the band is never trimmed to the cap in force and can exceed it (N2), and three sentences deny the cap exists (N1).
- *Does the loader's per-event rejection ever serve an event the console then prices wrongly?* **No event's price is computed from a rejected row** — the rejected event is out of `events()`, `tickets()` and `raw_ledger()`, and the survivors' numbers are the survivors' numbers. I compared the same healthy event on the held-back store and on the clean store at the same clock: `evt_syn_04` is 200 on both with identical own figures (11 resales, 0.93, band 0.67 – 1.29, exposure 688.8). What the loader does do is leave **counts** one short and unexplained: the store total (N6) and, when it *accepts* a null-priced sale rather than rejecting it, A1's sale count (N10).
- *Do any two numbers on one page derive from different cuts or scopes?* **Yes, four ways:** the band from the record's cap beside a page pricing against a candidate cap (N2); the market block's `no ceiling` beside the violation line's candidate ceiling (N1); the repeat-sale pair from another tier inside the tier's market block (N7); and `completed`/`status` measured against the store rather than the cut (N8). The ticket-day denominator is the same cut as the rate, but it runs past the event end, so the rate is a different function of the cut than the page implies (N3).

### N1 — Three sentences say "no cap, no ceiling" on a page that prices against a cap. **High.**

**Where.**
- `ticketpath/console/page.py:196-201` — the evidence strip's ceiling item, chosen on `value_of(payload["event"]["capBps"])` (the *recorded* cap).
- `ticketpath/console/blocks.py:287` — `a2 = "A2" if value_of(payload["event"]["capBps"]) is not None else "A2_UNCAPPED"`.
- `ticketpath/console/blocks.py:388-394` — the market block's `P_NO_CAP`.

All three read the recorded cap. The page's cap in force is `payload["selection"]["capBpsCandidate"]`. The 14:10Z pass moved exactly one of the four branches (`blocks.py:46-50`, the cap line) to the cap in force and left these three. Its report says the goal was that "an uncapped event priced under a URL cap does not say 'No cap applies' two lines above a sentence naming the cap it is pricing against"; that goal is met for the cap line and *not* met for the other three, one of which is in the same block as the violation line.

**Trigger.** `http://127.0.0.1:8841/?event=evt_syn_04&capBps=1700` (the page itself says "type a number to price against that cap").

**Measured on the page, in reading order:**
1. `This event records no cap, so a blank field means no cap and this page prices against none: type a number to price against that cap` — the invitation.
2. `[DECLARED] This page prices against a cap of [DECLARED] 1700 bps. This event records no cap of its own ...`
3. strip: `[FIXTURE] 12 resales on this event · [FIXTURE] 11 tickets · no resale cap, so no ceiling`
4. A2: `... the declared width gives a band ... This event has no resale cap, so no ceiling enters the bound.`
5. market: `... mean markup 19.8% · This event has no resale cap, so there is no ceiling to count against.`
6. `[FIXTURE] 7 of 12 recorded sales in this tier are above this cap; had this cap been enforced, those transfers would have failed ...`

(3), (4) and (5) are false on this page: it has a cap in force, a ceiling of `0.80 × 1.17 = 0.936 SOL`, and seven sales above it. (5) sits four lines above the violation line that proves it false. On `capBps=0` the same two sentences appear beside a refusal that names `the resale ceiling at [EXACT] 800,000,000 lamports`.

**Why it matters.** This is the one state where a reader who follows the page's own instruction is told the opposite of what the page is doing. It is the same class as the first review's honesty failure, and it is judge-reachable in two clicks (event 4, type `1700`, submit).

### N2 — The recommendation's own band exceeds the cap in force. **High.**

**Where.**
- `ticketpath/core/value_band.py:414-417` — the band's upper end is trimmed only to `regime["recordedCeilingLamports"]`, and on an uncapped event not at all.
- `ticketpath/core/primary_optimum.py:159-166` — the cap rule compares `recommended` (the point) with the candidate ceiling; the band it returns is the untrimmed one.
- `ticketpath/console/blocks.py:262-266` — `P_BAND` and `P_RANGE` print that band and "We would not argue with any price in that range."

**Trigger.** `/?event=evt_syn_01&capBps=298`.

**Measured.** Payload: `recommendedLamports = 1,026,573,088`, `bandHiLamports = 1,250,000,000`, cap in force 298 bps → `1,029,800,000`. The recommendation is not refused (its point is 3.2 million lamports under the page's ceiling) and the page prints:

> `[UNVALIDATED] Recommended primary price: 1.03 SOL per ticket.`
> `[UNVALIDATED] Band 0.74 – 1.25 SOL.`
> `[UNVALIDATED] We would not argue with any price in that range.`

The top of that range is `1.25 SOL` on a page that says it prices against a cap of `298 bps` (`1.0298 SOL`). The 13:58Z report named the band-trimming choice as deliberate ("the band is a statement about the record, not about the policy") but did not notice the consequence: the *recommendation object* now carries an upper end the engine's own cap rule forbids, and the page offers it in a sentence about primary prices. Same finding on `/?event=evt_syn_04&capBps=1632` → band `0.67 – 1.29` against a page ceiling of `0.93056 SOL`, and on `evt_syn_01&capBps=1000` → band `0.74 – 1.25` against `1.10`.

### N3 — The ticket-day denominator does not stop at the event end. **High (mathematics).**

**Where.** `ticketpath/core/price_features.py:129-157`, line 152: `end = min(as_of, parse(redeem["occurredAt"])) if redeem is not None else as_of`. A ticket with no `redeem` row accrues exposure up to the cut, however far past `endsAt` the cut is.

**Trigger.** `/?event=evt_syn_02&asOf=<any instant after 2026-11-22T02:00:00Z>`, on the static fixture.

**Measured on `evt_syn_02`, general tier** (9 sales throughout; the record does not change):

| Cut | Exposure printed | Rate printed |
|---|---|---|
| 2026-11-07T14:12 (default) | 435.8 ticket-days | 20.7 per 1,000 |
| 2026-11-22T03:00 (1 h after the end) | 552.1 | 16.3 |
| 2026-12-31T00:00 | 863.1 | 10.4 |
| 2027-06-01T00:00 | 2079.1 | 4.3 |

Hand-computed ticket-days capped at `endsAt` for the same tier: **551.8**, so the rate at any post-end cut should be **16.3**, not 4.3. The page prints the rate badged `[FIXTURE]` as a measured quantity ("this tier's own: its sales over its ticket-days at risk"), and nothing on the page says the denominator keeps running after the event. This is the same class the first review used as its five-minute catch: a rate that moves with the clock on a static record.

### N4 — The before-on-sale page still prints the excluded record as an absent one. **Medium-high.**

**Where.**
- `ticketpath/core/price_features.py:190-192` — `event_tickets = []` when `use_own_rows=False`, so `features["event"]["tickets"] = 0` and `storeTickets = 0`.
- `ticketpath/api/guidance.py:158-176` — `evidence.resales` and `evidence.tickets` are built from those zeros.
- `ticketpath/console/blocks.py:435-449` — `_no_exposure_sentence` reads `evidence.tickets`, so in this mode it says `No ticket had been issued at this instant`.
- `tools/console-check.py:140` asserts `[FIXTURE] 0 resales on this event` and `[FIXTURE] 0 tickets` are present.

**Trigger.** `/?event=evt_syn_02&mode=before_on_sale`.

**Measured.** Strip: `[FIXTURE] 0 resales on this event · [FIXTURE] 0 tickets · [FIXTURE] 0 at the ceiling`; basis: `0 ticket rows exist in the store`; refusal: `[REFUSED] No ticket had been issued at this instant, so there is no denominator.` The store holds 12 sale rows and 12 ticket rows on this event at that cut. The refusal *sentence* for the missing price is now true and names the mode; the counts beside it are not. The 13:08Z claim-class test (`SENTENCES_THAT_DENY_THE_OWN_RECORD`) catches the prose forms and stops exactly short of the counts: the strip is not a sentence pattern, so it passes. This is the one earlier defect that still stands.

### N5 — "Settled at exactly the ceiling" is counted with a ±1 bp tolerance. **Medium.**

**Where.** `ticketpath/core/price_features.py:122`: `"atCeiling": cap_bps is not None and abs(markup - cap_bps) <= 1`; the sentence is `ticketpath/core/labels.py:213-218` (`A19`), rendered at `ticketpath/console/blocks.py:144-160`.

**Trigger.** A copy of the fixture with one at-ceiling sale moved to `1,379,999,999` lamports (one lamport below the 1,380,000,000 ceiling; the page prints to nine decimals, so one lamport is visible).

**Measured.**
- One lamport **below**: `8 of 9 recorded resales (88.9%) settled at exactly the ceiling` — 7 are exact. The sentence "Those buyers each paid the most the platform allows" is false for the eighth.
- One lamport **above**: the count stays `8`, no violation line prints (violations only count against a *URL* cap), and the recommendation flips to a refusal because the record's own sale now exceeds the recorded cap. So the page shows `8 at the ceiling` while its own cap arithmetic says one sale is above it.

On the shipped fixture every sale is exactly on the ceiling, so the tolerance has no symptom there; it is a data-quality input away from being one.

### N6 — `7 events in the store` when the store carries 8. **Medium.**

**Where.** `ticketpath/api/guidance.py:167` (`eventsOnPlatform` = `len(events_index)`, the *served* events) and `ticketpath/console/page.py:217-218` (the noun "in the store").

**Trigger.** Any store with one event held back by the 13:58Z loader — e.g. the fixture with one sale at 0 lamports.

**Measured.** Strip: `[FIXTURE] 7 events in the store, [FIXTURE] 4 with any resale at this instant`. The file carries 8 events; `/api/events` lists 7. The R5 fix chose the noun "in the store" because the event total cannot follow a cut; the loader pass then made the served count differ from the store's, and the noun did not move with it. A reader is not told an event was held back; `/api/events` is silent too. (The rest is honest: no number is counted twice and the rejected event cannot reach a price.)

### N7 — The repeat-sale pair is chosen across the whole event inside the tier's market block. **Medium-low.**

**Where.** `ticketpath/api/guidance.py:421-438` (`_repeat_sale` iterates `features["tiers"]`, i.e. every tier) and `ticketpath/console/blocks.py:403-406` (rendered inside the tier-scoped market panel).

**Trigger.** `/?event=evt_syn_02&tier=tier_stg_front` and `/?event=evt_syn_07&tier=tier_riv_mezzanine`.

**Measured.** On the Front page: `face 3.00 SOL`, tier sales `3.09 / 3.21 / 3.45`, then `One ticket sold twice: 1.38 → 1.38 SOL over 2.7 days` — a pair from the General tier (face 1.20). On the River Hall Mezzanine page: `face 1.80 SOL`, cheapest tier sale `1.836`, then `1.12 → 1.12` — a pair from the Gallery tier (face 0.90). Every other number in that block is the tier's and says so; this one is the event's and does not.

### N8 — "Completed" counts a draft event once its date has passed, and `status` is not cut-aware. **Low-medium.**

**Where.** `ticketpath/core/price_features.py:334-347` (`ends = event.get("endsAt") or event["startsAt"]`; `completedAtCut = parse(ends) <= as_of`) and `ticketpath/core/value_band.py:111` (the count); `ticketpath/core/labels.py:293-297` (`P_MODE_BEFORE` premise) with the decision block at `ticketpath/console/blocks.py:113-126`.

**Trigger.** `/?event=evt_syn_02&asOf=2027-06-01T00:00:00Z`, and the same with `mode=before_on_sale`.

**Measured.** `8 events have completed in the observation window` — all 8, including `evt_syn_08`, whose `status` is `draft` and which never issued a ticket. The decision block prints `status on_sale` for an event that ended seven months before the decision instant. In before-on-sale at that cut it prints `This is the decision as it is taken before this event's first ticket is issued` beside `decision instant 2027-06-01T00:00:00.000Z` and `ends 2026-11-22T02:00:00.000Z`.

### N9 — `TRACE` still gets Python's 501 page. **Low.**

**Where.** `ticketpath/server.py:195-204` (`do_PUT`, `do_DELETE`, `do_PATCH`, `do_OPTIONS` exist; `do_TRACE` and `do_CONNECT` do not).

**Measured.** `TRACE /` → 501, `text/html`, body `<title>Error response</title> … Message: Unsupported method ('TRACE')`, no banner. This is the exact class the 13:40Z R3 fix closed for three verbs, left for the two it did not name.

### N10 — Small number/scope notes, each measured. **Low.**

- **A null-priced sale is not counted in "the ledger records N sales".** `ticketpath/core/price_features.py:89-91` skips a `sale` whose price is null (`ledger_adapter.py:207-211` permits it), while A1 (`labels.py`, "In this tier the ledger records {n} sales") counts priced sales. Measured: a tier with 9 sale rows, one with a null price → `the ledger records 8 sales`. Defensible if a gift is not a sale; the page does not say which noun it is using.
- **`basis: tier_marks` / `pooled_across_tiers` are engine names on the page.** `ticketpath/console/blocks.py:276-279` prints `recommendation["basis"]` verbatim. On a tier with no sales inside a sold event (unreachable on the shipped fixture; I reached it by deleting one tier's sales) the only signal that the band came from *other tiers* is the token `pooled_across_tiers`.
- **`τ 0.4` for τ = 0.406.** `ticketpath/console/blocks.py:370-374` formats τ to one decimal in the binding block, while the control and the sensitivity grid print `0.406`.
- **Coverage, not a defect:** on the shipped fixture every tier of a sold event has its own sales, so the `pooled_across_tiers` rung, the `blended` rung and a tier with one sale are not reachable by a judge; they are exercised by tests only.

---

## 4. The whole

**Is this something a judge can read without being misled?** On the default page, the cold start, the completed event, the fee states, the frozen-cap page (`capBps=0` on a capped event), the uncapped page at its default and the [EXACT] line: **yes**. The sentences match the record, the badges travel with the numbers, and the mode label is unmissable. On the page the console itself tells the reader to build — an uncapped event with a typed cap — **no**: it says it has no cap and no ceiling while refusing or bounding a price against that very ceiling. On the before-on-sale page, **no**: the strip says the record does not exist. On a store with one bad event, **no**: the store count is one short and nothing says why.

**Is it something an engineer would call correct?** **Not yet.** The console is total, which is the hard part and it is done. But the exposure denominator runs past the event, the cap branches read the wrong field, and the at-ceiling test uses a tolerance under an "exactly". All three are small diffs; none of them is a design question. The design questions (the D1 fork, the pooled estimator not applied, the boundary price rule) are still the operator's, not bugs.

### The four verdicts

**Mathematics — STANDS-WITH-NARROWING.** The cap ceiling is integer and exact, the cap rule refuses on the correct side of the boundary and leaves the number untouched above it, the band widens monotonically in τ with the point fixed, the gamma–Poisson zero is a posterior mean and says so, and the [EXACT] equality survives at lamport precision. The narrowed statement: *the recommendation is a resale-value/cap floor, labelled as a hindsight recomputation, not a primary price a reader could have set before sale; on the real before-on-sale decision the engine states no price at all; and the ticket-day denominator does not stop at the event end, so the measured rate falls with the clock once the cut passes the event (4.3 vs 16.3 per 1,000 at a 2027 cut).*

**Honesty — FAILS.** Three sentences on `/?event=evt_syn_04&capBps=1700` say there is no cap and no ceiling on a page that prices against a cap, counts seven sales above it, and prints a band whose ceiling is 0.936 SOL; the before-on-sale strip states the excluded record as an absent one; the store count is short by the held-back events. These are not labels around a correct number: they are false statements about what the page is doing, on states the controls produce.

**Code — STANDS-WITH-NARROWING.** The blank-reply class is gone and stays gone (four mutated stores, a sale at the boundary, a tierless event with tickets, an all-rejected store, a missing `endsAt`: all answer with a status and a page). The loader is per-event and the survivors serve. The narrowed statement: *the code is total but not yet correct — the exposure denominator (`price_features.py:152`), the three cap branches (`page.py:200`, `blocks.py:287`, `blocks.py:388`), the ±1 bp at-ceiling test (`price_features.py:122`), the event-scoped repeat pair (`guidance.py:421`) and `TRACE` (`server.py:195-204`) remain, and none of them is covered by a test that would fail if it regressed.*

**Refusals — STANDS-WITH-NARROWING.** The set is complete and visible, the sale probability and the interior optimum are refused in words, the fee refusal is conditional on no fee, the cap refusal carries its own arithmetic and does not print the forbidden number, and the empty store refuses rather than inventing data. The narrowed statement: *in BEFORE-ON-SALE mode the zero-exposure refusal describes 12 issued tickets as none, the market block's "no ceiling to count against" contradicts the cap refusal on the same page, and a store whose own recorded sale exceeds its cap produces a cap refusal that reads as a statement about the record's price rather than about the store.*

---

## 5. Fix list, ranked by risk

1. **Key every "does this page have a cap?" branch to the cap in force.** `page.py:200`, `blocks.py:287`, `blocks.py:388` (`blocks.py:46` is already right). On an uncapped event with a URL cap, either show the at-ceiling count against the candidate ceiling or say "this event records no cap; this page prices against N bps and M of K sales are above it". This is the judge-reachable contradiction and it is three lines.
2. **Stop the exposure denominator at the event end.** `price_features.py:152`: take `min(as_of, redeem, endsAt)`. Until then, any cut after the event prints a measured rate that falls with the clock (N3), and `tools/console-check.py` should add the post-end cut as a case.
3. **Decide the band under a cap in force.** Either trim `bandHi` to the candidate ceiling when one is in force, or withhold `P_RANGE`/the band and print the record's band with its own cap named. The recommendation object may not carry an upper end above the ceiling its own rule enforces (N2).
4. **Make the before-on-sale counts true.** The strip, the basis and the no-exposure sentence must carry the excluded counts as excluded ("12 recorded on this event, excluded by the mode; 0 enter this decision"), not `0 resales` / `0 tickets` / `No ticket had been issued`. Then update `tools/console-check.py:140`, which asserts the false counts (N4). This is the only earlier defect still standing.
5. **Compare price to the integer ceiling for "at the ceiling".** `price_features.py:122`: `price == ceiling` (or document the tolerance and stop saying "exactly"). A one-lamport miss currently reads as a buyer who "paid the most the platform allows" (N5).
6. **Name the served count on a held-back store.** `7 events in the store` must become `8 events in the store, one held back: sale_not_priced`, or the noun must say "served". The API's `list_events` should say the same (N6).
7. **Scope the repeat-sale pair.** Either pick it within the selected tier, or say "on this event" in A18. Today the Front page shows a 1.38 SOL pair in a tier whose face is 3.00 (N7).
8. **Separate "ended" from "completed", and say which the status is.** A `draft` event whose date has passed is not a completed event; and `status on_sale` beside a post-end decision instant needs one clause saying the status is the store's current field, not the cut's (N8). The mode premise sentence should also stop claiming a decision before first issue on an instant after it.
9. **Route `TRACE` and `CONNECT` through the same 405** as PUT/DELETE/PATCH (`server.py:195-204`) (N9).
10. **The cosmetic/number notes in N10:** name the priced-sale noun in A1, translate `basis` to prose, print τ at its declared precision, and give the `pooled_across_tiers` rung a sentence that names the record. Low value, but they are the kind a judge stops on.

**Not a fix, a decision for the operator (still first by consequence):** the D1 fork from 07 §6.4. The page now says what the number is; the number is still a hindsight resale-value floor. If the product's question is "what should I set the primary price at before sale", the honest mode refuses on this fixture and the only priced answer is the labelled counterfactual. That is a better state than before, and it is still a product choice only he can make.

---

## 6. What a judge could catch in five minutes

**Open `/?event=evt_syn_04` (Synthetic Theatre: Uncapped Markup Spread). The page says:**

> "This event records no cap, so a blank field means no cap and this page prices against none: **type a number to price against that cap**, and the canonical URL carries it."

**Type `1700` and press Recompute.** The page now says, top to bottom:

> `[DECLARED] This page prices against a cap of [DECLARED] 1700 bps. This event records no cap of its own, so no recorded sale is reclassified by this one.`
> strip: `12 resales on this event · 11 tickets · **no resale cap, so no ceiling**`
> A2: `… the declared width gives a band … **This event has no resale cap, so no ceiling enters the bound.**`
> market: `… **This event has no resale cap, so there is no ceiling to count against.**`
> `[FIXTURE] **7 of 12 recorded sales in this tier are above this cap**; had this cap been enforced, those transfers would have failed …`

Three sentences say there is no cap and no ceiling on a page that has just named a cap whose ceiling is 0.936 SOL, and counted seven sales above it. Four lines separate the market's "no ceiling to count against" from the violation line. A judge who follows the page's own instruction catches it on one screen, and no arithmetic on the page explains it. Setting `0` instead of `1700` gives the same two sentences beside a refusal that names `the resale ceiling at [EXACT] 800,000,000 lamports`.

The runner-ups, all in the same five minutes:
- **Click Front on `evt_syn_02`.** The market block, under `face 3.00 SOL` and sales at 3.09 / 3.21 / 3.45, says `One ticket sold twice: 1.38 → 1.38 SOL over 2.7 days` — a pair from the General tier, unnamed.
- **Set `asOf` to `2027-06-01` on `evt_syn_02`.** The sale rate falls from 20.7 to 4.3 per 1,000 ticket-days and exposure rises from 435.8 to 2079.1 while the record is unchanged; `status on_sale` sits beside an instant seven months after the event ended.
- **Choose `before on-sale` on `evt_syn_02`.** The strip says `0 resales · 0 tickets` while the same server's default page, one reload away, says `12 resales · 12 tickets`, and the refusal beneath it says `No ticket had been issued at this instant`.
- **The five-minute catch of the previous review is closed.** `evt_syn_03` now badges the zero-sale rate `[DECLARED]`, names the `Gamma(1, 1)` posterior and says the number is not measured. Nothing on the default page repeats it.

*End of review. One file written, this one. No fix, no commit, no push, no dependency installed, no other tree touched.*

---

## CORRECTION (2026-11-08T08:30Z): three machine handles redacted, no verdict changed

**Scope:** this file only, and only the Ports paragraph of the preamble. **Why:** this repository is
public and `tools/public_safety.py` refuses a tracked file that carries a port tied to a running
process, an absolute path under a home directory, or the name of another of the operator's
repositories. The rule and its reason are in `.public-denylist`.

**What the redaction costs: nothing that was measured.** The paragraph's job is to isolate this
pass: which ports were mine, which belonged to another session, which I only read, and what I did
not touch. It still says all of it, and the fleet sentence still states the same negative, that
those trees were not read or written, without listing directory names.

| Where | Was | Now |
|---|---|---|
| Ports, live frontend | a port tied to "were not touched" | "The live frontend's port and `../ticketing-frontend` were not touched." |
| Ports, fleet sentence | three trees named, one with a home path | "The operator's fleet tool repositories were not read or written." |

**Residue, stated rather than hidden.** Port numbers on lines this rule does not classify are
unchanged, including the two scratch ports this pass used and this project's own backend port.
`.public-denylist` states why it does not deny those, and `/tmp` paths are exempt for `records/` on
purpose. `python3 tools/public_safety.py check --tracked` reports zero hits for this file as of this
note.

# FIXTURE-STORE: what is in the synthetic store, and what it is not

**Status:** the store the backend serves. Generated, not hand-authored.
**Written:** 2026-11-07T11:35Z. **Author:** fixture-store session.
**Scope:** `fixtures/synthetic_store.json`, its generator `tools/build_fixture_store.py`,
and the tests that assert both. Nothing in `../ticketing-frontend` was read
for modification or edited; that tree is untouched.
**Source of truth:** the generator. If this document and the JSON disagree, the JSON is
what the backend serves and the generator is what produced it; rerun it.

**Nothing in the store is real ticket data.** Every number quoted here is arithmetic
over a file that says so about itself, and every screen that shows one of those numbers
also carries a string saying the same thing, because the frontend cannot be edited
tonight and the payload strings are the only channel left.

---

## 1. What this replaces, and why

The previous store was two events and five tickets, hand-written on 2026-11-07. It had
three defects that a judge would see before they saw any arithmetic:

1. **Thirteen addresses, one visible wallet.** Every address was `FXTURE…` followed by a
   run of `1`s, so the frontend's `shortAddress` rendered all thirteen as `FXTU…1111`.
   A four-row custody trail read as one wallet handing a ticket to itself four times, and
   the "where tickets ended up" table was the same pill repeated.
2. **A market statistic over four tickets.** The event page showed "Resold at least once
   75%" and "Average markup +5.6%" computed from four tickets. Defensible arithmetic,
   indefensible as a demonstration of a market computation, because a single ticket moved
   the headline by 25 points.
3. **No third regime.** One event had resales and one had none. There was no event where
   the resale cap bound, which is the case the cap research (`records/findings/01-a-market-structure.md`
   §3) turns on, and no event where the cap exists but does not bind, so the two could not
   be told apart on screen.

This store fixes all three: 8 events, 76 tickets, 204 distinct addresses, and three
regimes that answer differently by construction. It is produced by
`tools/build_fixture_store.py` (seed `20261107`, standard library only, no network, no
clock, no arguments that change output), so it is reproducible rather than bytes somebody
edited until the screen looked right.

### The address convention changed from `FXTURE` to `SYN`

`records/FRONTEND-INTEGRATION.md` §5.10 argued the `FXTURE` prefix was load-bearing and
told a future fixture to keep it and vary the tail. That instruction is superseded here,
deliberately and in the open:

- The addresses now begin with `SYN` and each carries a distinct four-character tail, so
  the truncated form reads `SYN1…1pcR`, `SYNuG…1fCH`, `SYNFL…1nFt`: the family marker is
  visible in the first four characters and the tail tells two wallets apart.
- Every one of them base58-decodes to exactly **32 bytes**, asserted per address with a
  round trip. The old addresses also decoded to 32 bytes, so this is not a repair; it is a
  guarantee that survives a reseed instead of depending on which characters were chosen.
  A judge who pastes one into a Solana explorer gets a decoder that accepts the shape and
  an account that does not exist, rather than a malformed-address error.
- Nothing else about the previous convention's purpose changed: the prefix still cannot be
  mistaken for a real key, and it is still the label that survives truncation on every
  screen.

The one thing this record cannot fix is prose already written against the old prefix:
`records/FRONTEND-INTEGRATION.md` §0, §3 and §5.12 quote `FXTU…1111` and the two-event,
five-ticket counts. A dated note at the top of that file points here. The labelling
analysis in that file, which is the part that matters (32 of 37 numeric places need a
label and all 32 can get one from payload strings), is unchanged and still correct.

---

## 2. The store at a glance

| | Count |
|---|---|
| Events | 8 |
| Organizers | 3 |
| Tiers | 15 across the 8 events (1 to 3 per event, no two events sharing a tier structure) |
| Tickets | 76 |
| Ledger rows | 147 |
| of which `issue` | 76 |
| of which `sale` | 61 |
| of which `transfer` (unpriced) | 2 |
| of which `redeem` | 8 |
| Distinct addresses (mints, wallets, organizer wallets) | 204 |
| Distinct truncated forms (`first4…last4`) | 204 |
| Total ticket supply across the events | 1,190 seats, of which 76 issued |

Money is integer lamports, time is ISO-8601 UTC with milliseconds. Every event, tier,
ticket and ledger row is listed in the JSON in a stable order, so a human can audit any
number on screen by hand: the largest event holds 14 tickets, the busiest holds 16 sales, and the
smallest with a history holds 8 tickets and 7 sales.

Ticket counts stay at or below 25 per event because `/events/[eventId]` requests at most
25 tickets and never reads `nextCursor` (`FRONTEND-INTEGRATION` §5.11). A larger event
would silently hide rows and the "Showing N of M" line would be the only warning.

---

## 3. The three regimes, and the five other events

Event order on screen is `startsAt` ascending, so the first card is the completed run
(2026-10-03). The regimes are the middle of the list.

| Regime | Event | What it demonstrates | Numbers in this store |
|---|---|---|---|
| `cap_present_not_binding` | `evt_syn_01` Synthetic Hall: Cap Present, Not Binding (Toronto, 5 Dec) | A cap that exists and does not bind: every recorded sale sits below it | 3 tiers (1.0 / 2.5 / 5.0 SOL), 14 tickets, 14 sales, markups −600 to +1800 bps against a 2500 bps cap, 9 of 14 tickets resold |
| `cap_binding` | `evt_syn_02` Synthetic Stage: Resale Cap Binds (Hamilton, 21 Nov) | A mass point at the cap: the censored record the cap research describes | 2 tiers (1.2 / 3.0 SOL), 12 tickets, 12 sales, 9 of them exactly +1500 bps (cap 1500), none above |
| `cold_start` | `evt_syn_03` Synthetic Annex: Cold Start, No Resales (Mississauga, 12 Dec) | An event with tickets issued and no resale row at all | 2 tiers (0.7 / 1.4 SOL), 10 tickets, 0 sales, empty price series, six zero buckets |
| `uncapped_spread` | `evt_syn_04` Synthetic Theatre: Uncapped Markup Spread (Kitchener, 14 Nov) | No cap, so both tails exist: above +25% and below face | 1 tier (0.8 SOL), 11 tickets, 12 sales, markups −3000 to +9000 bps |
| `resale_disabled` | `evt_syn_05` Demo Arena East: Resale Switched Off (Ottawa, 16 Jan 2027) | `resaleEnabled: false` with zero transfer rows, so the absence means what it says | 2 tiers (1.5 / 2.4 SOL), 8 tickets, 0 sales |
| `completed_run` | `evt_syn_06` Demonstration Annex: Completed Run (London, 3 Oct) | Redemptions after the last sale; the only rows with a `redeem` kind | 1 tier (0.5 SOL), 8 tickets, 7 sales, all 8 redeemed and every `redeemedAt` matches its redeem row |
| `tier_cap_binding` | `evt_syn_07` Synthetic River Hall: Cap Binds On One Tier (Guelph, 28 Nov) | The multi-tier case: the cap binds on the cheapest tier and not above it, so the same policy produces different markups per tier | 3 tiers (0.9 / 1.8 / 3.6 SOL), 13 tickets, 16 sales; the 4 gallery sales are exactly +2500 bps, the 12 mezzanine and box sales are +200 to +1400 |
| `nothing_issued` | `evt_syn_08` Synthetic Studio: Draft, Nothing Issued (St. Catharines, 20 Feb 2027) | A draft event reads as empty rather than as zero | 1 tier (1.0 SOL), 0 tickets, 0 sales, analytics 200 with empty lists |

Three of these carry the demo's claims:

- **The cap binds, and you can see it without a chart.** The contract's six markup buckets
  are too wide to show a mass point at +15%: all twelve sales land in the 0–25% bucket. The mass
  point is visible in the per-sale `markupBps` on each ticket's custody trail and in the
  event's average, and this is recorded so nobody points at the histogram and claims it
  proves the cap bound.
- **The cap does not bind, and that is a different sentence.** `evt_syn_01` has a cap and
  no sale at it. Together with `evt_syn_02` the store can show that "capped" and "binding"
  are two observations, not one.
- **Per-tier markup is visible.** `evt_syn_07` has a gallery sale at +2500 bps and a
  mezzanine sale at +600 bps. Measured against the event's cheapest face, the mezzanine
  sale would read as +11,000 bps or more; the script asserts at least one such pair exists
  and prints the two numbers side by side. `records/findings/02-d-elasticity-fees-optimum.md`
  names multi-tier pricing as the instrument the contract can actually carry, and this is
  the event that lets the record show the instrument rather than describe it.

`evt_syn_03` and `evt_syn_05` are the two cold-start variants that matter for
`records/findings/02-e-cold-start.md` §7: an event with resale enabled and no sales (the
prior case) and an event where resale is off entirely (the case where the value signal
will never be observed). `evt_syn_08` is the degenerate third: nothing issued at all.
The store can carry the cold-start demonstration; it does not perform it, because no
engine output has a home in the wire contract (`records/CONTRACT-MAP.md` §6).

### The demo ticket

`tkt_syn_0001` (event `evt_syn_01`, Floor, 1.0 SOL face) has the four-row trail the
custody card is written for, and every wallet is visibly distinct:

```
issue     −            → SYN…1fCH             2026-10-02
sale      SYN…1fCH     → SYN…1hYp  1.18 SOL  +18.0%   2026-10-06
transfer  SYN…1hYp     → SYN…1juM  no price           2026-10-12
sale      SYN…1juM     → SYN…1nFt  0.94 SOL  −6.0%    2026-10-13
```

Stats as served: 2 sales, 3 transfers, average markup +600 bps, peak 1.18 SOL, last
0.94 SOL, volume 2.12 SOL, 4 distinct wallets. Every one of those is computed by
`ticketpath/core`, not stored.

---

## 4. Invariants, and where each one is enforced

Each is asserted twice: by the generator while it builds (it prints the line and raises
rather than writing a store that fails one), and by `tests/test_fixture_store.py` from the
file on disk, so a hand edit fails the suite rather than changing a served number.

| # | Invariant | How |
|---|---|---|
| 1 | Every wallet and mint begins with `SYN` and base58-decodes to exactly 32 bytes | `AddressBook.address` round-trips every allocation; test decodes each distinct address |
| 2 | No two addresses share a truncated form (`first4…last4`) | tag is a bijection over the allocation counter; test asserts 204 distinct forms |
| 3 | Every sale price is an exact integer function of that ticket's own tier face and an integer markup, so `markupBps` recomputes exactly | `price = face * (10000 + bps) // 10000` with an exactness assertion; test re-derives bps and asserts `(price−face)×10000 % face == 0` |
| 4 | Every non-sale row carries a null price | generator refuses a priced transfer; test asserts it over the file |
| 5 | Per ticket: exactly one `issue`, first; timestamps strictly increasing; every sale after the issue | generator and test, per ticket |
| 6 | Custody links: each row's `fromWallet` is the previous row's `toWallet`; no sale from a wallet to itself | generator and test; a self-transfer is the specific defect this store exists to remove |
| 7 | No `redeem` before the last sale, and `redeemedAt` equals the redeem row | generator and test |
| 8 | Tier `issuedCount` equals that tier's ticket rows; event totals equal the tier sums | adapter refuses a mismatch at load; test recomputes from rows |
| 9 | No ticket moves after its event has started, and redemptions fall inside the event's run | generator and test |
| 10 | The regime facts of §3: the not-binding cap is never reached, at least 60% of the binding event's sales sit exactly on the cap, the cold-start events hold zero sale rows, the uncapped event has both tails, the completed run redeems everything, the tiered event binds on one tier only | generator asserts and prints each; a test asserts each from the file |
| 11 | Every event name and description, and every organizer name, carries a marker saying this is synthetic demonstration data | generator refuses an unmarked string; test asserts the marker and the words "not a real show" |
| 12 | Volume stays auditable: 6 to 9 events, 40 to 120 tickets, at most 25 tickets per event | generator and test |
| 13 | The file on disk is the generator's output, byte for byte, and the generator is deterministic | `tests/test_fixture_store.py` imports the generator, rebuilds twice, and compares with the file; `--check` does the same from the shell |

Not an invariant, but true and worth stating: `markupBps` is **not stored**. The store
holds prices only; the markup on the wire is computed from the ticket's own tier face by
`ticketpath/core/markup.py`, so there is exactly one source of truth for it. The price was
built from a markup so that the recomputation is exact, not so that two fields can drift.

---

## 5. The labelling convention, and where each label reaches the screen

The frontend cannot be edited tonight, and it renders no honesty field. The only strings
it prints from our payload are `Event.name`, `Event.description`, `Organizer.name`,
`WalletVerification.flags` and error `message`
(`records/FRONTEND-INTEGRATION.md` §4). So the label is carried there, in full sentences,
on every event.

### What the strings say

- **`Event.name`**: every name contains "Synthetic" or "Demo", for example
  `Synthetic Stage: Resale Cap Binds`.
- **`Event.description`**: one sentence, in the same place a real description would sit,
  of the shape: "Synthetic demonstration record: the +15% resale cap binds on this event
  and most recorded sales sit exactly on it, generated by tools/build_fixture_store.py,
  not a real show." It says what the record is, what it demonstrates, where it came from
  and that it is not real. It reads as documentation, not as an apology, and it does not
  invent a provenance story: the generator is named because that is what made it.
- **`Organizer.name`**: `Synthetic Promotions Co-operative (demonstration)`,
  `Demonstration Events Lab (synthetic)`, `Fixture Organizing Group (synthetic)`.
- **Address convention**: every wallet and mint begins with `SYN`, so every pill on every
  screen reads `SYN…`. This is the label that survives truncation, and it is the only one
  that reaches the ticket page's own figures.

### Where each reaches the screen

| Payload string | Screens it is printed on | Which of the 37 numeric places it labels |
|---|---|---|
| `Event.name` | `/` event card title, `/events/[id]` `h1`, `/organizer` filter chips, `/tickets/[id]` back-link | N1, N2, N14 to N16, N19 to N24, N27, N28, N42, N43 |
| `Event.description` | `/events/[id]`, under the header | N4 to N12, N17, N18 (the event's own face, issued count, resale share, sale count, average markup, daily price and markup series, tier table) |
| `Organizer.name` | `/events/[id]` byline | the event page's provenance line |
| `SYN` prefix | every address pill on every page, including the custody trail's two sides and the destinations table | N25 directly; N19, N20, N22, N24 by making the wallets visibly placeholders |
| `Event.name` (again) | `/organizer` filter chips, which name the selected event above the roll-up | N29 to N35 |

That covers the 32 places `FRONTEND-INTEGRATION` §4 says need a label. The remaining five
need none and get none: a real date (N3), a face-value rule the frontend already labels
honestly (N13), the correctly-phrased "Not enforced" (N26), a genuinely real verification
timestamp (N36), and the cluster label (N37).

### What the label does not do

- It does not sit **beside** a figure. The event page's label is a sentence under the
  header; the ticket page's only label is the back-link. That is a frontend limitation, not
  a payload one, and it is the strongest reason to add the `AppShell` strip if one
  frontend change is ever allowed (`FRONTEND-INTEGRATION` §3, "If a component change were
  allowed").
- It does not fix the two false sentences the frontend generates itself. See §6.
- It does not travel to `/my-tickets` or `/verify`, which render no event payload. Those
  pages are wallet-gated and show no fixture number.

---

## 6. What a judge must NOT conclude from any of this

Read this list as part of the store's specification. Every item is something the screen
makes tempting and the data cannot support.

1. **Not a market sample.** The store over-samples resale because it exists to exercise a
   resale computation: 61 sale rows over 76 tickets, and 62% to 77% of tickets resold on the
   events that have resales. The measured resale propensity in the literature is on the
   order of 5% of purchased tickets (`records/findings/01-a-market-structure.md` §5). A
   "resold at least once" percentage on screen is arithmetic over this record. It is not a
   market rate, and it is not an estimate of one.
2. **No markup, price or distribution here is evidence about tickets.** The markups were
   drawn from rules per regime so the store can show three cases. They are not fitted,
   calibrated or sampled from anything. Nothing in this store may be used to estimate,
   validate or report any result.
3. **Nothing about a price path over time.** Markup draws are independent of
   time-to-event, so the store contains no declining path and no end-game uptick. A chart
   drawn from it shows the arithmetic working; reading a trend into it, or comparing it to
   the literature's 40%-in-the-final-month decline, would be reading noise as signal.
4. **Not real events, venues or organizers.** Every name and venue is invented and says so.
   Cities are real words used as a filter key, nothing more. No event described here
   happened or will happen.
5. **Not on-chain, and not checkable on-chain.** Mint addresses decode to 32 bytes so a
   base58 decoder accepts them, and no account exists on any cluster. `signature` and
   `slot` are null on all 147 rows because no transaction exists. A Solana Explorer page
   for one of these mints is expected to say the account does not exist; that is the
   honest outcome, not a bug to work around.
6. **No cap and no transfer gate is enforced.** `resalePriceCapBps` and
   `requiresVerifiedWallet` are carried as organizer policy in the record. Nothing in this
   build enforces either, because no program is deployed. The frontend renders them as
   enforcement ("capped at +25% over face value, enforced at transfer time", "must be
   verified before a transfer will succeed"), which is false in this build and is a known
   frontend sentence we may not edit tonight (`FRONTEND-INTEGRATION` §4, N38 and N39).
   The same payload is honest about the same fact one click away: a ticket page prints
   "Transfer restriction: Not enforced".
7. **Not a validation of the engine.** There is no engine output in the store and no forecast
   field in the contract. `/health` reports `pricingModel.available: true` with
   `kind: rule-based-bounded-estimator` and `fitted: false`: a rule-based bounded estimator
   with no fitted model behind it, so the recommendation is arithmetic over this record and
   nothing here was trained, calibrated or scored. A convincing custody trail is a
   demonstration that the record can be computed from, not evidence that a pricing model is
   right. Nothing here has ground truth to be scored against.
8. **Not an attestation about any wallet.** No key material exists anywhere in this file.
   The only real cryptography in the app is the wallet-signature verification flow, which
   uses whatever wallet the operator connects, not anything here.
9. **Not a reason to trust the build more than the tests.** The store is internally
   consistent because 13 invariants are asserted twice, not because it looks plausible.
   Consistency is not accuracy: an internally consistent fiction is still a fiction.

---

## 7. Regenerating and verifying

```bash
cd <repository root>
python3 tools/build_fixture_store.py           # rewrite, print every invariant
python3 tools/build_fixture_store.py --check   # fail if the file is not a fresh build
python3 tools/build_fixture_store.py --dump    # print it, write nothing
python3 -m unittest discover -s tests          # the whole suite
```

The generator prints 16 invariant lines and two closing checks, including the
regime numbers of §3, the per-tier-markup pair, the custody-trail shape and the repeat
sellers (3 wallets sell on more than one ticket; the busiest sells on 5). It then loads
the file it wrote through `LedgerAdapter.from_fixture` and cross-checks every address
against `ticketpath.core.base58`, so "the backend will accept this" is demonstrated rather
than claimed.

**The running backend does not reload the store.** `LedgerAdapter.from_fixture` reads the
file once at startup, so a process started before this change keeps serving the old store
from memory. The instance on `127.0.0.1:8788` (started by the demo session at
11:1xZ) was still answering with the two-event store when this was written. Restarting it
is the operator's call and was not done here. The new store was verified end to end on a
scratch port, which disturbs nothing already running: 8 events and 76 tickets on the list routes, an event by id and by slug, a ticket by
id and by mint, the showcase trail with its four entries, every event's analytics, wallet
verification returning 200 `verified: false`, and a challenge nonce. Each number was
compared with `tests/store_arithmetic.py` rather than eyeballed. The signed verification
POST needs a real signature and is exercised by `tests/test_wallet_verification_flow.py`.

### Tests touched, and why

| File | Change |
|---|---|
| `tests/test_ledger_adapter.py` | The counts, the prefix check and the five refusal mutations were hardcoded to the old store (2 events, 5 tickets, `FXTURE`, `ledger[2]` is a transfer). They now assert the properties the store promises (6 to 9 events, 40 to 120 tickets, `SYN`, 32 bytes, unique truncations) and find the row they need by kind, not by index, so they survive a reseed. |
| `tests/test_resale_history.py` | Selected fixed ticket ids and hand-written figures. Now it selects a ticket by property (first with two sales, first never resold, first sale on a tier above the cheapest) and compares the payload with `tests/store_arithmetic.py`, which recomputes it from the raw rows. |
| `tests/test_event_analytics.py` | Same conversion, plus the multi-tier test now uses a sale the store actually contains instead of a hand-built four-sale event. The pure day-bucketing and per-ticket-markup tests were already fixture-free and were kept. |
| `tests/test_http_contract.py` | The wire assertions compared against literal store values (event ids, addresses, `evt_fixture_1`'s four figures). They now compare the response with the store-derived expectation for the event, ticket or ticket-with-sales the test selects, so the test checks the server against the store rather than against a transcription of it. `TestHealth` and `TestRouting` were fixture-free and untouched. |
| `tests/store_arithmetic.py` (new) | The independent arithmetic: per-ticket stats, per-event analytics, markup, mean and median with half-away rounding, the six buckets, and selectors like "first ticket with two sales". Deliberately does not import `ticketpath.core`. |
| `tests/test_fixture_store.py` (new, 25 tests) | The invariants of §4 asserted from the file, plus reproducibility: the committed JSON must equal a fresh build of the generator, twice. |

A note on the sequence, because two files changed under this work. While the store was
being rebuilt, two tests in `tests/test_contract_conformance.py` failed (`TestNoDrift` and
`TestSemantics`, both on the analytics route) because the contract's printed bucket labels
use an en dash and `core/markup.py` served a hyphen. Those failures reproduce against the
previous store (`TICKETPATH_FIXTURE_PATH` pointed at `git show HEAD:fixtures/synthetic_store.json`),
so they were not caused by the fixture, and that file belongs to another session. The
session that owns `core/markup.py` corrected the four labels at 11:29Z and adjusted
`tests/store_arithmetic.py` and `tests/test_markup.py` at the same time. The final run of
the whole suite is green: 149 tests, 0 failures. This change touched none of those files.

---

## 8. Dated notes

### 2026-11-07T11:40Z — the resale density now says it is over-sampled

§6.1 named the defect and §5 recorded the label that does not cover it: the store
resells 62% to 77% of tickets on its five events with a resale history, the real market
resells ≈5.1% of purchased tickets (class A, two independent measurements,
`records/findings/01-a-market-structure.md` §5), and nothing on screen gave the reader
that context. The density is deliberate (a resale record has to contain resales) and it
is unchanged. What changed is that every event description now says so, in one sentence,
appended to the sentence §5 describes.

The sentence, identical on all 8 events, with the figures computed from the rows at
build time rather than typed (`tools/build_fixture_store.py`, `sampling_clause`):

> The record is deliberately over-sampled for demonstration: 62% to 77% of tickets
> resold at least once on the events that have resales, against ~5.1% of purchased
> tickets in the real market (class A), 12 to 15 times the real rate.

- **Scope of the claim.** It is a statement about the store, not about the event it sits
  under. The three events with no resale at all (`evt_syn_03`, `evt_syn_05`, `evt_syn_08`)
  carry the same sentence, scoped by the words "on the events that have resales", so it
  does not contradict the 0% printed above it. One wording, once per event, not five
  paraphrases.
- **The numbers cannot drift.** `sampling_clause` recomputes the resale share of every
  event that has one, floors the low end, rounds the high end up (62.5% and 76.9% print
  as 62% and 77%), and divides by 5.1 to get 12 and 15. `verify` now fails the build if
  any description omits the clause, and prints
  `labelling: 19 name/description/organizer strings carry a marker, 8/8 descriptions
  state the resale over-sampling`. The generator's own invariant list in its
  docstring gains a tenth entry for this.
- **What did not change.** 8 events, 76 tickets, 61 sale rows, 147 ledger rows, every
  address, every price, every timestamp, every other field. Rebuilt with the clause
  suppressed, the store is byte-identical to the previous build apart from the eight
  `description` values, and `--check` passes against the file on disk.
- **Correction to §6.1's wording elsewhere.** This note's range is 62% to 77% (§6.1
  already says 62% to 77%; a separate brief for this change quoted 62% to 67%, which is
  three events out of five — `evt_syn_04` resells 73% and `evt_syn_07` 77%). The
  generator computes the range from the rows, so the sentence is the authority.
- **Tests.** `tests/test_fixture_store.py::test_every_printed_string_carries_a_marker`
  asserts that the description contains the marker, not the exact sentence, and now also
  asserts the over-sampling clause is present; `tests/test_http_contract.py` asserts the
  served description still starts with "Synthetic demonstration record", which appending
  a second sentence does not disturb. No test elsewhere asserted a description string.

---

## CORRECTION (2026-11-08T08:30Z): one process id redacted, no claim changed

**Scope:** this file only, and only the sentence about the running backend not reloading the store.
**Why:** this repository is public and `tools/public_safety.py` refuses a tracked file that carries
a process id. The rule and its reason are in `.public-denylist`.

**What the redaction costs: nothing that was measured.** The claim is that a process started before
the store changed keeps serving the old one from memory, so this file's new store was proven on a
scratch port instead. The instance is still identified by what it serves and by the session that
started it at 11:1xZ, and the operator's call about restarting it is still recorded as his. The pid
was a handle on a process that no longer exists.

`python3 tools/public_safety.py check --tracked` reports zero hits for this file as of this note.

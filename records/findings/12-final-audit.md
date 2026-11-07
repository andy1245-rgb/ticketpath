# 12 — Final consistency audit of the console

| | |
|---|---|
| **Status** | complete. One file written, this one. No code touched, no other record edited, no state file written, no commit, no push. |
| **UTC** | 2026-11-07T16:16Z–16:31Z. |
| **Role** | final consistency auditor. I did not write or fix the console, and I did not use the project's check tool as my instrument. |
| **Scope** | the three properties in `FINAL-PROOF-2.md` §3, a fourth of my own, and the three pages a judge reaches first. |
| **Method** | my own sweep of the bytes the server sends: 360 grid states plus 1,500 cap-grid states, parsed from the page, grounded against `/api/events` and `fixtures/synthetic_store.json`; a control run of the same sweep against the pre-fix tree `72bb8d3`. |
| **Evidence** | every number is parsed from the response at the URL named. Quoted page text is the served text after tag-stripping and unescaping, which is what a browser shows. |
| **Verdict** | **CAN WITH THESE THREE FIXES** (§5). The three named properties pass; the fourth and the reader review do not. |

**At a glance**

| run | states | violations | where |
|---|---:|---:|---|
| required grid, 8 events × 2 modes × 4 caps × 3 cuts | 192 | 32 | all fourth-property (before-on-sale premise) |
| extended grid, the other 7 tiers at the same states | 168 | 28 | same |
| **grid total** | **360** | **60** | (a) 0, (b) 0, (c) 0, (d) 60 |
| cap-grid extension, 25 caps × 15 tiers × 2 modes × 2 cuts | 1,500 | 0 | (a)/(b)/(c) only |
| control: the same sweep on `72bb8d3` (served on 8795) | 360 | 646 | (a) 12, (b) 74, (c) 392, (d) 168 |
| control: cap grid on `72bb8d3` | 1,500 | 2,986 | (a)/(b)/(c) only |

The control is the point of the instrument: the same parser and the same rules that return zero on the fixed tree return hundreds on the tree the proof measured, so a zero here is a measurement, not a blind spot.

---

## 0. What I read, and the tree I measured

I read `records/FINAL-PROOF-2.md` in full, and the section the last fixer appended to
`records/BUILD-REPORT-CONSOLE.md` at `2026-11-07T16:10Z`, including its before/after table and its
list of what is still open. I then read the three reader pages as a reader, not against the rules.

The tree I measured is the working tree at **`8dfb2c3`**, "Close the three contradictions the proof
sweep found, and the gate that hid one", committed `2026-11-07T16:14:33Z`. The fix is therefore in
the tree a judge would clone; the build report's "nothing is committed" was true when it was
written, not when this audit ran. `git status --porcelain` is clean except `NIGHT-LOG.md`, which is
the orchestrator's dispatch note and not this run's write.

The server I measured is my own, not the fixer's:

```bash
cd <repository root>
python3 -m ticketpath.server --port 8794
# ticketpath 0.1.0 listening on http://127.0.0.1:8794
# dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
# SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
# started 2026-11-07T16:16:13Z, cwd the repository root
```

`8787` (another `node` process), `8788` (the fixer's server), `:3000` and `:3001` were not
bound, read or written by this run. The control ran from a throwaway extraction of `72bb8d3` at
`/tmp/audit12/old`, served on `:8795`, and was stopped at the end. I did not read or write
the operator's other three repositories, by name.

The instrument is in `/tmp/audit12/`, outside the tree:

| file | what it is |
|---|---|
| `/tmp/audit12/sweep.py` | the 360-state grid and the four properties; page parser, ground truth, rules |
| `/tmp/audit12/capgrid.py` | the 1,500-state cap grid, properties (a)/(b)/(c) only |
| `/tmp/audit12/results-8794.json` | every parsed state, every violation, every observation |

I left both out of `tools/`: they hard-code this store's events, the audit's cuts and the audit's
properties, so they are audit instruments, not general project tools. §2 describes the rules and
§6 gives the commands, so the run can be reproduced without the files.

---

## 1. The grid

The brief's grid, as I implemented it:

- **events:** all 8 in the store (`evt_syn_01` … `evt_syn_08`);
- **modes:** `counterfactual` and `before_on_sale`;
- **cap states:** `none` (no `capBps` parameter, so the event's recorded cap is in force), `0`, the
  event's recorded cap, and 1,000 bps above it (bounded at 10,000);
- **cuts:** before issue, after event end, and mid-event.

For the three events that record no cap (`evt_syn_04`, `evt_syn_05`, `evt_syn_08`), there is no
"event default" to type, so the default state is a typed **1,500 bps stand-in** and "above" is
2,500 bps. This is the one convention the grid needs; it is labelled here and in the result file.

The cuts are per event:

| cut | instant |
|---|---|
| before issue | `2026-07-01T00:00:00.000Z` — before the earliest issue row in the store, `2026-08-02T02:00:00.000Z` |
| mid-event | `startsAt + 1 hour` for that event |
| after end | `endsAt + 10 days` for that event |

The required grid is 8 events × 2 modes × 4 cap states × 3 cuts = **192 URL states** at each event's
default tier. I extended it to every tier at the same states: 7 further tiers × 2 × 4 × 3 = 168, so
the full grid is **360 unique URLs** (verified: 360 states, 360 distinct paths). The cap-grid
extension adds 15 tiers × 2 modes × 25 caps × 2 cuts = **1,500 URL states** at the default instant
and mid-event.

Ground truth:

- **cap, face, dates, status:** `/api/events?limit=100`, the server's own contract route.
- **rows at the cut:** `fixtures/synthetic_store.json`; issue rows and priced sale rows are counted
  at or before the cut, per event and per tier. This is the store the server is serving, not an
  inference from the page.
- **text:** the response bytes. Numbers are read back out of the rendered page, not out of the
  payload or the code.

---

## 2. The four rules

### (a) The cap the page names is the cap it prices against

Eight checks per state:

1. the `capBps` field value equals the cap in force (the URL's cap, else the event's recorded cap,
   else blank);
2. the canonical URL's `capBps` equals the cap in force;
3. every "this page prices against a cap of N bps" sentence names the cap in force;
4. the exact-ceiling line's face operand equals the tier's face, its cap operand equals the
   *recorded* cap, `ceiling = face × (10,000 + cap) / 10,000` in integer arithmetic, and the
   "That is exactly X SOL" value equals `ceiling / 1e9`;
5. the refusal line's ceiling equals `face × (10,000 + cap in force) / 10,000`;
6. the band-stop sentence, when it says "the ceiling the cap in force puts on this tier", prints the
   in-force ceiling; when it says "the ceiling the recorded cap of N puts on this tier", N is the
   recorded cap and the ceiling is that cap's arithmetic;
7. the prior-band truncation sentence follows the same rule;
8. when the cap in force is not the recorded cap, the two-cap disclosure is present, and every
   sentence that names a recorded cap names the event's recorded cap; the A19 "capped at N% over
   face" is the recorded cap / 100.

The old C3 defect is exactly check 6: a sentence that said "the cap in force" at the recorded cap's
ceiling. It is now fixed.

### (b) No band crosses a ceiling the page says it will not cross

Two bands are checked: the recommendation `Band lo – hi SOL` and the `prior band around face: lo –
hi SOL`. The governing ceilings are only those the page attributes to the **cap in force**: the
in-force band-stop sentence, the in-force truncation sentence, the refusal ceiling, and the exact
line when its operand is the cap in force. A band top above the lowest such ceiling is a violation.
A band-stop or truncation sentence must also describe the band beside it: if it says the band stops
at X, the band's top must be X.

The exact line is often the *recorded* cap's ceiling when the page prices against a different cap.
That is a disclosed two-cap fact, not a band crossing a ceiling the page says it will not cross, and
it is recorded separately (288 disclosed two-cap states in the proof's run; 165 states in mine where
the declared prior's own extent is above a printed ceiling with the cut sentence present). The
declared prior's own extent is not treated as "the band": the page names it as the prior alone and
says which ceiling cut the band. I say in §4 whether that distinction survives a reader.

### (c) No sentence claims rows are absent when the decision mode excludes them

The trigger is the store at the cut, not the page: in `before_on_sale` mode, if the store holds sale
rows at or before the cut, then:

- the market block's `N sales of M on this event` denominator M must equal the store's event count
  (and, when the sentence is not scoped by "enter this decision", the sold count must equal the tier
  count);
- the strip's excluded count must equal the store's event count;
- the market's excluded counts must equal the store's event and tier counts;
- none of "No resale has been recorded on this event", "No ticket had been issued at this instant",
  "In this tier the ledger records no sale", or a printed `0 at the ceiling` may appear;
- if the store holds sales and no excluded-sales clause appears, that is a violation.

The old C1 defect is the denominator check: `0 sales of 0 on this event` while the same sentence and
the strip named 12 excluded. It is now fixed.

### (d) The fourth property: every temporal premise is true at the printed instant, or the page says it is not

I chose this because a judge's first question about a decision page is *when is this decision being
taken*, and the page makes two explicit temporal claims: the counterfactual says it recomputes "from
this event's own completed record ... in hindsight"; the before-on-sale mode says "This is the
decision as it is taken **before this event's first ticket is issued**". A page can be internally
consistent on cap and clock and still be false about the record it is reading. The proof's clock
sweep checked that the printed instant equals the requested one (64 states, 0 violations); it did
not check that the mode's premise is true at that instant.

The counted test is the explicit before-on-sale premise: if the page prints "before this event's
first ticket is issued" and the decision instant is after the event's first issue row, the sentence
is false unless the page prints the "this instant is after the event ended" qualifier (the page's
`P_MODE_BEFORE_LATE`). The counterfactual "completed record"/"hindsight" claim is measured too, but
recorded as an observation rather than a counted violation, because "completed record" can be read
as "the record as it stands"; it is the reader-review headline in §4.

---

## 3. The violation count, with the text

```
grid:                360 URL states (192 required + 168 extended)
violations:          60
states with one:     60
by property:         (a) 0, (b) 0, (c) 0, (d) 60
required 192:        32 violations
extended 168:        28 violations
cap grid 1,500:      0 (a)/(b)/(c)
```

All 60 are the same defect: the before-on-sale mode sentence claims a decision taken before the
event's first ticket, at an instant after the first issue, with no qualifier. The page's own strip
on the same screen names the rows that were issued before that instant and are excluded by the mode.
The text is identical in all 60; what varies is the event line and the strip counts.

The violating sentence, verbatim:

> **[DECLARED] Decision mode: BEFORE-ON-SALE. This is the decision as it is taken before this
> event's first ticket is issued: only other events' completed resale records and this event's own
> metadata enter it, and this event's own ledger rows are excluded.**

The 60 states, by event. Each row is 4 cap states (`omitted`, `0`, recorded, recorded+1,000) on the
tier(s) named, at the mid-event instant shown, unless the after-end column says otherwise.

| event | tiers | instant | caps | states | first issue | strip on the same page |
|---|---|---|---|---:|---|---|
| `evt_syn_01` | Floor, Balcony, Box | `2026-12-05T01:30:00.000Z` | omitted, 0, 2500, 3500 | 12 | `2026-09-24T22:00:00.000Z` | `0 resales enter this decision; 14 recorded on this event are excluded by the mode · 0 tickets enter it; 14 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_02` | General, Front | `2026-11-22T00:00:00.000Z` | omitted, 0, 1500, 2500 | 8 | `2026-09-11T11:00:00.000Z` | `0 resales enter this decision; 12 recorded on this event are excluded by the mode · 0 tickets enter it; 12 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_03` | Standing, Seated | `2026-12-12T02:00:00.000Z` | omitted, 0, 2000, 3000 | 8 | `2026-10-11T15:00:00.000Z` | `0 resales enter this decision; 0 recorded on this event are excluded by the mode · 0 tickets enter it; 10 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_04` | General Admission | `2026-11-14T01:00:00.000Z` | omitted, 0, 1500, 2500 | 4 | `2026-09-02T08:00:00.000Z` | `0 resales enter this decision; 12 recorded on this event are excluded by the mode · 0 tickets enter it; 11 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_05` | Lower Bowl, Upper Bowl | `2027-01-16T02:00:00.000Z` | omitted, 0, 1500, 2500 | 8 | `2026-10-16T14:00:00.000Z` | `0 resales enter this decision; 0 recorded on this event are excluded by the mode · 0 tickets enter it; 8 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_06` | Standing | mid `2026-10-04T00:30:00.000Z` and after end `2026-10-14T02:00:00.000Z` | omitted, 0, 2500, 3500 | 8 (4 + 4) | `2026-08-02T02:00:00.000Z` | `0 resales enter this decision; 7 recorded on this event are excluded by the mode · 0 tickets enter it; 8 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_07` | Gallery, Mezzanine, Box | `2026-11-28T01:30:00.000Z` | omitted, 0, 2500, 3500 | 12 | `2026-09-21T00:00:00.000Z` | `0 resales enter this decision; 16 recorded on this event are excluded by the mode · 0 tickets enter it; 13 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |
| `evt_syn_08` | General Admission | `2027-02-20T01:00:00.000Z` | omitted, 0, 1500, 2500 | 0 | none | `0 resales enter this decision; 0 recorded on this event are excluded by the mode · 0 tickets enter it; 0 recorded on this event are excluded by the mode · no at-ceiling count while the event's own record is excluded` |

The event line for each state is the page's own:

- `evt_syn_01`: `Event Synthetic Hall: Cap Present, Not Binding · status on_sale · starts 2026-12-05T00:30:00.000Z · ends 2026-12-05T03:30:00.000Z · decision instant 2026-12-05T01:30:00.000Z.`
- `evt_syn_02`: `Event Synthetic Stage: Resale Cap Binds · status on_sale · starts 2026-11-21T23:00:00.000Z · ends 2026-11-22T02:00:00.000Z · decision instant 2026-11-22T00:00:00.000Z.`
- `evt_syn_03`: `Event Synthetic Annex: Cold Start, No Resales · status on_sale · starts 2026-12-12T01:00:00.000Z · ends 2026-12-12T04:00:00.000Z · decision instant 2026-12-12T02:00:00.000Z.`
- `evt_syn_04`: `Event Synthetic Theatre: Uncapped Markup Spread · status on_sale · starts 2026-11-14T00:00:00.000Z · ends 2026-11-14T03:00:00.000Z · decision instant 2026-11-14T01:00:00.000Z.`
- `evt_syn_05`: `Event Demo Arena East: Resale Switched Off · status on_sale · starts 2027-01-16T01:00:00.000Z · ends 2027-01-16T04:00:00.000Z · decision instant 2027-01-16T02:00:00.000Z.`
- `evt_syn_06` mid: `Event Demonstration Annex: Completed Run · status completed · starts 2026-10-03T23:30:00.000Z · ends 2026-10-04T02:00:00.000Z · decision instant 2026-10-04T00:30:00.000Z.`
- `evt_syn_06` after end: the same line with `decision instant 2026-10-14T02:00:00.000Z.`
- `evt_syn_07`: `Event Synthetic River Hall: Cap Binds On One Tier · status on_sale · starts 2026-11-28T00:30:00.000Z · ends 2026-11-28T03:00:00.000Z · decision instant 2026-11-28T01:30:00.000Z.`

Why the other before-on-sale states are clean:

- `evt_syn_08` has no issue rows, so "before the first ticket" is true at every cut; its `0` counts
  are the clock's, not the mode's.
- the after-end states for `evt_syn_01`–`05` and `07` print `P_MODE_BEFORE_LATE`:
  "This decision instant is after the event ended, so this is what the before-on-sale decision would
  price on the record that exists today, not a decision that could have been taken at that instant."
  That is a qualifier, and those states pass.
- `evt_syn_06`'s after-end states do **not** print that qualifier, because the event's status is
  `completed` and the page's `_ended_before` only fires for `draft`/`on_sale`. Its 4 after-end states
  are therefore in the 60. Its 4 mid-event states are also in the 60: the event is in progress at
  `2026-10-04T00:30Z`, 90 minutes before its recorded end, while the status line says `completed`;
  the page does not say the status is the store's current field.

The grid understates the reader-facing exposure. The default before-on-sale page a judge reaches in
one click—`/?event=evt_syn_02&mode=before_on_sale` at the default instant `2026-11-07T16:25Z`—has
the same defect: first issue `2026-09-11`, 12 tickets and 12 resales recorded and excluded, and the
mode sentence still says "before this event's first ticket is issued". The grid's three named cuts
do not include the default instant; the reader review in §4 does.

### The three original defects, re-measured

The three properties the proof failed are now clean on my grid. The exact pages:

**C1, `/?event=evt_syn_02&mode=before_on_sale`.** The strip and the market block now say:

> `[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event are excluded by the
> mode · [FIXTURE] 0 tickets enter it; [FIXTURE] 12 recorded on this event are excluded by the mode ·
> no at-ceiling count while the event's own record is excluded`
>
> `in this tier [FIXTURE] 0 sales of [FIXTURE] 12 on this event enter this decision · [FIXTURE] 12
> recorded sales on this event are excluded by the mode, [FIXTURE] 9 of them in this tier · median
> markup [REFUSED] not stated · mean markup [REFUSED] not stated · no at-ceiling count while the
> event's own record is excluded`

The store holds 12 sale rows on the event and 9 in General at this cut. The denominator is the
record's count, the zero is scoped to "enter this decision", and the exclusion is named at event and
tier scope. No `0 sales of 0` on an event that holds sales appears anywhere in the 360 states;
the phrase still appears on the genuinely empty events (`03`, `05`, `08`), where it is true.

**C2, `/?event=evt_syn_03`, no parameters.** The third event in the list:

> `[UNVALIDATED] prior band around face: [UNVALIDATED] 0.65 SOL – [UNVALIDATED] 0.84 SOL. That is a
> band around the declared prior, not a price for this ticket.`
>
> `[EXACT] That band is cut at the ceiling of [EXACT] 0.84 SOL that the cap of [DECLARED] 2000 bps
> in force puts on this tier, because a band above a ceiling the page states is the contradiction
> this sentence closes. The declared prior alone runs [UNVALIDATED] 0.65 SOL to [UNVALIDATED] 1.26
> SOL; the ceiling bounds what can be transacted, so the band stops where it does.`
>
> `[EXACT] ceiling 840,000,000 lamports = face 700,000,000 lamports × (10,000 + 2000) / 10,000 —
> integer arithmetic on the tier face, not an estimate. That is exactly 0.84 SOL.`

The printed band's top is 0.84, the ceiling; the old 1.26 is named as the declared prior's own
extent and is not presented as the band. The rule passes. The prose is another matter (§4).

**C3, `/?event=evt_syn_01&capBps=3500`, face 1.00 SOL, recorded cap 2500.**

> `[EXACT] The top of that band is the ceiling the recorded cap of [FIXTURE] 2500 bps puts on this
> tier, at [EXACT] 1.25 SOL, which is below what the cap of [DECLARED] 3500 bps in force allows, so
> the range stops at the recorded ceiling.`

The sentence now names the cap that produced 1.25 and says it is below the 3500 in-force cap. The
old sentence called 1.25 "the ceiling the cap in force puts on this tier" while the in-force cap
would put it at 1.35. Fixed.

The cap-grid extension is the stress test for these three: 25 caps from 1 to 10,000 on every tier,
both modes, at the default instant and mid-event. It returns **0** (a)/(b)/(c) violations on the
fixed tree and **2,986** on `72bb8d3`. That includes the rounding edge at `evt_syn_05&capBps=1500`
that the fixer called out: the cut band now prints `1.725`, not `1.73`, against the `1.725` ceiling.

---

## 4. The reader's-eye review

I read the three pages a judge is most likely to reach first, at the default instant, as a reader.
The pages are the default `/`, the cold-start `/?event=evt_syn_03`, and the event with resales in
before-on-sale `/?event=evt_syn_02&mode=before_on_sale`. The quoted text is what the browser shows.

### 4.1 The default page: a completed record for an event two weeks away

The first decision block says, at the default instant `2026-11-07T16:25:02.624Z`:

> `[UNVALIDATED] Decision mode: COUNTERFACTUAL. This page recomputes the value from this event's own
> completed record: this is not a price you could have set; it is what the record implies in
> hindsight.`
>
> `Event Synthetic Stage: Resale Cap Binds · status on_sale · starts 2026-11-21T23:00:00.000Z · ends
> 2026-11-22T02:00:00.000Z · decision instant 2026-11-07T16:25:02.624Z.`

The event starts in 14 days. The page calls its record "completed" and the reading "hindsight" on
the same screen as the future start date and `status on_sale`. A judge does not need to know the
engine to see the tension: there is no completed event to look back on. The store's 12 resales are
a partial record at the instant, not a completed one; the strip itself says "12 resales on this
event" at this instant, not "12 at the end".

The same block has a second, smaller tension:

> `Value: at least 1.38 SOL per ticket. That is a floor, not an estimate. It is the highest recorded
> price in this tier, and it is the most this record can support.`
>
> `Range: 1.38 SOL and up. We do not state an upper bound from this record.`

"the most this record can support" reads as an upper bound of 1.38; the next sentence says the range
is "1.38 and up". The intended reading is that 1.38 is the highest *observed* price and therefore the
floor of the value, while the upper side is unobserved because the cap censors it. The page explains
the censoring above ("every sale the ceiling turned away is missing from it entirely"), so a careful
reader can reconcile it; a judge skimming the two bold lines will not. The wording should say
"the most this record can state as a floor" or "the highest recorded price, not an upper bound".

Two smaller things on this page: the cap helper says "clear the field and submit to fall back to
this event's recorded cap of 1500 bps" when the field already shows 1500, so the instruction is a
no-op on the page where it is most likely to be read; and the event dropdown uses the unexplained
term "capped no mass point" for `evt_syn_01` and `evt_syn_06`. Neither is a contradiction, but both
are unexplained.

### 4.2 The cold-start page: a completed record with no resales

`/?event=evt_syn_03` is the cold-start event. The decision block says:

> `[UNVALIDATED] Decision mode: COUNTERFACTUAL. This page recomputes the value from this event's own
> completed record: this is not a price you could have set; it is what the record implies in
> hindsight.`

Four lines later:

> `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.`

This is a direct self-contradiction on one screen. There is no "completed record" of resales to
recompute from; the page says so itself. The counterfactual falls back to the declared prior, which
is honest, but the mode sentence is not: it should say the record is empty and the band is the
prior, or reserve "completed record"/"hindsight" for events that have ended.

The cold page also shows the C2 fix and the reader problem it leaves:

> `[UNVALIDATED] prior band around face: [UNVALIDATED] 0.65 SOL – [UNVALIDATED] 0.84 SOL. That is a
> band around the declared prior, not a price for this ticket.`
>
> `[EXACT] That band is cut at the ceiling of [EXACT] 0.84 SOL that the cap of [DECLARED] 2000 bps
> in force puts on this tier, because a band above a ceiling the page states is the contradiction
> this sentence closes. The declared prior alone runs [UNVALIDATED] 0.65 SOL to [UNVALIDATED] 1.26
> SOL; the ceiling bounds what can be transacted, so the band stops where it does.`

The 1.26 is still on the page, above the 0.84 ceiling. The sentence says it is the declared prior's
own extent and that the band stops at the ceiling, which is the correct distinction, but the phrase
"because a band above a ceiling the page states is the contradiction this sentence closes" is a
patch note, not product prose. It refers to the page's own previous defect in the third person; a
judge has no idea what "this sentence closes" means. "The band stops where it does" is circular. The
same sentence appears on the before-on-sale page with 0.94/1.82 against 1.38. The fix is truthful
but written for the reviewer, not the reader.

The market block on the cold page has a smaller misdescription:

> `in this tier [FIXTURE] 0 sales of [FIXTURE] 0 on this event · median markup [REFUSED] not stated ·
> mean markup [REFUSED] not stated · at the ceiling [FIXTURE] 0 — At the cap — a rationing point, not
> a market-clearing price.`

The count is a true zero; the A16 sentence "At the cap — a rationing point" describes a sale at the
cap that does not exist. On a tier with no sales, the sentence should be "no sale at the ceiling",
not a rationing-point gloss. The same shape appears on any capped tier whose at-ceiling count is
zero (the Floor tier of `evt_syn_01` at the default cap is another); the no-cap events
(`evt_syn_04`, `05`, `08`) use a different clause and are not affected.

### 4.3 The before-on-sale page: "before the first ticket" beside 12 excluded tickets

`/?event=evt_syn_02&mode=before_on_sale`, at `2026-11-07T16:25:02.633Z`:

> `[DECLARED] Decision mode: BEFORE-ON-SALE. This is the decision as it is taken before this event's
> first ticket is issued: only other events' completed resale records and this event's own metadata
> enter it, and this event's own ledger rows are excluded.`
>
> `[FIXTURE] 0 resales enter this decision; [FIXTURE] 12 recorded on this event are excluded by the
> mode · [FIXTURE] 0 tickets enter it; [FIXTURE] 12 recorded on this event are excluded by the mode ·
> no at-ceiling count while the event's own record is excluded`

The first issue row in the store is `2026-09-11T11:00:00.000Z`; the decision instant is
`2026-11-07T16:25:02.633Z`. The page itself says 12 tickets and 12 resales were recorded before the
instant and are excluded by the mode. If the decision is taken before the first ticket is issued,
those 12 tickets cannot exist. This is the counted (d) defect, and it is visible in one click from
the default page by changing the mode dropdown. The page needs the same kind of qualifier it already
has for the after-end case: "this is what the before-on-sale decision would price on the record that
exists today, not a decision that could have been taken before the first issue." The after-end
qualifier exists; the after-first-issue qualifier does not.

The tier line on the same page says:

> `[FIXTURE] tier: General · face [FIXTURE] 1.20 SOL · regime [FIXTURE] no resale`

while the market block two paragraphs below says:

> `in this tier [FIXTURE] 0 sales of [FIXTURE] 12 on this event enter this decision · [FIXTURE] 12
> recorded sales on this event are excluded by the mode, [FIXTURE] 9 of them in this tier · ...`

"regime [FIXTURE] no resale" is badged as a fixture fact, but the fixture holds 9 sale rows in this
tier at this cut. The mode sentence explains that the rows are excluded, so the label is arguably
the decision's regime, not the store's; but the badge and the word "regime" say otherwise. A judge
sees "no resale" and "9 recorded sales in this tier" on one screen. The label should say "no rows in
this decision" or "excluded by mode", not "no resale".

The refusals panel on this page also prints:

> `[REFUSED] insufficient_marks: [FIXTURE] 0 sales is too few to fit a path, so no path is quoted.`

The 0 is the entering count, which is true; but the sentence does not say "enter this decision", and
the market block above says 9 sales in this tier are excluded. A judge reading the refusal panel
alone can read "0 sales" as the tier's record. This is the same class as C1 one line lower: the
number is right, the scope is missing. The fix is to say "0 sales enter this decision" or "no sale
enters this decision".

The same page carries the truncated prior band with 0.94–1.38 and the declared prior's 0.94–1.82;
the self-referential sentence and the uncut extent are the same reader problem as the cold page.

### 4.4 What a person would find that the rules do not catch

In order of how likely a judge is to hit it:

1. **The mode sentence contradicts the record state.** The counterfactual says "completed record"
   and "hindsight" on an event that has not started (the default page) and on a cold-start event
   with no resales at all. The cold page says "completed record" and "No resale has been recorded on
   this event" within four lines of each other. This is not a cap or clock rule; it is a false
   description of the record.
2. **The before-on-sale premise contradicts the excluded counts.** "Before this event's first ticket
   is issued" at an instant when the page itself says 12 tickets and 12 resales are excluded. The
   page has a qualifier for the after-end case and none for the after-first-issue case. This is the
   counted (d) defect, and the default before page has it too.
3. **The tier regime label contradicts the tier's record.** "regime [FIXTURE] no resale" on a tier
   with 9 recorded sales excluded by the mode. The count is scoped; the label is not.
4. **The patch prose.** "because a band above a ceiling the page states is the contradiction this
   sentence closes" is a fix note addressed to a reviewer, and "the band stops where it does" is
   circular. A judge will read it as the page arguing with itself. The fact it states is true; the
   wording is not product prose.
5. **The declared prior's uncut extent is still above the stated ceiling.** 0.65–1.26 against 0.84,
   and 0.94–1.82 against 1.38. The page names it as the prior alone and says the band is cut, so the
   old C2 contradiction is technically resolved; but the number a judge will check is still there,
   above the ceiling, and the sentence that defends it is the densest on the page.
6. **The zero-sale A16 sentence.** "at the ceiling 0 — At the cap — a rationing point, not a
   market-clearing price" on a tier with no sales. The zero is true; the rationing-point description
   is not.
7. **The unscoped `0 sales` refusal.** "insufficient_marks: 0 sales is too few to fit a path" on a
   page where 9 sales in the tier are excluded by the mode. True of the decision, ambiguous about
   the tier.
8. **Smaller wording.** "the most this record can support" beside "Range: 1.38 SOL and up"; the
   no-op "clear the field" helper on the page where the field already equals the recorded cap; the
   unexplained "capped no mass point" and "tau" controls; the "Show the refusal" button that runs
   the state machine rather than the refusal panel.

The pages are readable, the numbers are consistent, and the honesty labels are present. What a
judge will remember is the first one: the page says it is reading a completed record when the event
is in the future or has no resales. That is the difference between "honest but technical" and
"contradicts itself in the first paragraph".

---

## 5. Verdict

**CAN WITH THESE THREE FIXES.**

The console is close. The three properties the proof failed are now clean on my independently
written sweep: 0 (a), 0 (b), 0 (c) on 360 grid states and 0 (a)/(b)/(c) on 1,500 cap-grid states,
with a control on the pre-fix tree that fails the same rules 646 and 2,986 times. The cap is named
and priced against; the bands stop at the ceilings the page prints; the mode-excluded rows are
counted and scoped where the counts appear. The old C1, C2 and C3 are fixed at the text.

It is not yet safe to put in front of a judge without a caveat, because the fourth property and the
reader review find three things the rules do not catch. The three fixes, in the order that matters:

1. **Make the mode sentences true at the printed instant.**
   - Counterfactual: do not say "completed record" and "hindsight" for an event that has not ended.
     Either condition the sentence on the event being completed, or say "the record as it stands at
     the decision instant" and reserve "hindsight" for completed events. This fixes the default
     page, the cold-start page, and the 120 grid states where the observation is recorded.
   - Before-on-sale: print the "after the first issue" qualifier whenever `asOf` is after the first
     issue row, not only when it is after the event end. The page already has the after-end
     qualifier; the same sentence, with the first-issue instant, closes the counted 60. Include the
     completed event's after-end states, where the status is `completed` and the qualifier is
     currently skipped.
   - Status: when the status is `completed` and the instant is before the recorded end (the
     `evt_syn_06` mid-event states), say the status is the store's current field, as the page
     already does for `on_sale` after the end.

2. **Scope or remove the mode-excluded labels.** When the before mode excludes the tier's rows, the
   tier regime must not read "[FIXTURE] no resale"; say "no rows in this decision" or "excluded by
   mode". Scope the `insufficient_marks: 0 sales` refusal to "0 sales enter this decision". Print
   the A16 "At the cap — a rationing point" sentence only when there is at least one sale at the
   ceiling; on a zero-sale tier say "no sale at the ceiling". The market block and the strip are
   already right; the labels around them are not.

3. **Replace the patch prose and resolve the uncut prior.** Remove "because a band above a ceiling
   the page states is the contradiction this sentence closes" and "the band stops where it does";
   say plainly which cap cut the band and what the prior's own extent is, or drop the uncut extent
   from the page altogether. Resolve "the most this record can support" beside "Range: 1.38 SOL and
   up" by saying the upper side is unobserved, not supported. Explain or drop "capped no mass
   point" and "tau" in the controls.

These are local prose and label changes. None of them touches the engine, the store, the cap
arithmetic, the band cut, the clock, or the frontend. After them the console can be shown: the
numbers hold, the three named properties hold, and the fourth and the reader's first paragraph
would hold too.

**What would make it CANNOT, for the record:** if the mode labels were treated as immutable spec
strings and the "completed record"/"before first ticket" sentences had to stay on every page, then
the default and cold pages would remain self-contradictory and I would not show them to a judge. The
fix is conditional wording, not a redesign; the page already conditions the after-end case, so the
mechanism exists.

### What holds, measured

- 360 grid states, 0 (a), 0 (b), 0 (c). The three original contradictions are fixed.
- 1,500 cap-grid states, 0 (a)/(b)/(c), including 25 caps from 1 to 10,000 and the rounding edge at
  1,500 bps.
- The clock echo: the printed instant, the canonical URL and the `Nothing after …` sentence agree in
  all 360 states; the after-end state for an `on_sale`/`draft` event says the field and the instant
  disagree. (The completed event's after-end line does not, and that is the `evt_syn_06` qualifier
  gap in §3.)
- The control on `72bb8d3`: 646 violations on the 360 (a 12, b 74, c 392, d 168) and 2,986 (a)/(b)/(c)
  on the 1,500. The instrument can fail; the zero is not a blind parser.
- The three reader pages: 0 (a)/(b)/(c) each; the before page adds one (d) state at the default
  instant, which the grid's three cuts do not contain.

### What remains open, outside the console

- `LICENSE` line 3 is still `Copyright (c) 2026 [OPERATOR: replace this bracket with your name]`.
  This is unchanged from `FINAL-PROOF-2` and is the operator's, not the console's; a judge who opens
  the repository will see it.
- The store is synthetic. The page says so in the banner and in `/health`; no number here is real
  ticket data.
- `:3001` and `:3000` were not re-audited by this run; the task is the console. The frontend copy was
  measured by the proof and is not part of this verdict.
- Nothing is committed or pushed by this run. The fix commit `8dfb2c3` is already in the tree; the
  working tree has only the orchestrator's `NIGHT-LOG.md` change.

---

## 6. Reproduction

```bash
# the tree and the server this audit measured
cd <repository root>
git rev-parse --short HEAD                     # 8dfb2c3
python3 -m ticketpath.server --port 8794       # started 16:16:13Z

# the 360-state grid and the four properties
python3 /tmp/audit12/sweep.py http://127.0.0.1:8794

# the 1,500-state cap grid, properties (a)/(b)/(c)
python3 /tmp/audit12/capgrid.py http://127.0.0.1:8794

# the control on the tree the proof measured
mkdir -p /tmp/audit12/old
git archive 72bb8d3 | tar -x -C /tmp/audit12/old
(cd /tmp/audit12/old && python3 -m ticketpath.server --port 8795) &
python3 /tmp/audit12/sweep.py http://127.0.0.1:8795
python3 /tmp/audit12/capgrid.py http://127.0.0.1:8795
```

The sweep's rules are §2. The parser strips the page to the text a browser shows, unescapes HTML
entities, reads the cap field and canonical URL from the markup, and takes every number back out of
the text. It imports nothing from `ticketpath` and runs none of `tools/console-check*.py`.

*One file written: this one. No code, no other record, no state file, no commit, no push. The
servers on 8794 and 8795 were started and stopped by this run; 8787, 8788, 3000 and 3001 were not
touched.*

---

## CORRECTION (2026-11-07T18:55Z) — the licence item in §5 is closed, and six machine handles in this file are redacted

**Scope:** this file only. Appended, not rewritten, except for the six redactions listed at the end.
**Measured:** 18:40Z–18:55Z, at `origin/main` (`8a5e5e6`), which is also local HEAD.

**The claim.** §5, "What remains open, outside the console", first bullet, said:

> `LICENSE` line 3 is still `Copyright (c) 2026 [OPERATOR: replace this bracket with your name]`.
> This is unchanged from `FINAL-PROOF-2` and is the operator's, not the console's; a judge who opens
> the repository will see it.

**The correction.** The placeholder is gone. `sed -n '3p' LICENSE` at HEAD returns the MIT copyright
line with the holder's name filled in, and the file is tracked and pushed; `README.md`'s licence
section prints the same line. The item is closed, and it closed before this file was written, which
makes the sentence above a statement about `FINAL-PROOF-2` rather than about the tree. Everything else
in that §5 list stands as written: the store is still synthetic, and the frontend copy was outside
that verdict's scope.

**The redactions, and why they are in a correction note rather than silent.** Six lines carried a
handle the repository's own public-safety rules refuse in public: four absolute paths under a home
directory, and process ids. A file that cannot be staged cannot carry a correction, so the
stale-claims pass of 18:55Z redacted the minimum needed and changed nothing else on those lines:

| Where | Was | Now |
|---|---|---|
| §3 reproduction block | a `cd` into an absolute path under a home directory | `cd <repository root>` |
| §3 reproduction comment | `# pid <n>, started …, cwd <that path>` | `# started …, cwd the repository root` |
| §3 ports sentence | `8787` (`node server.mjs`), `8788` (the fixer's server, pid <n>) | `8787` (another `node` process), `8788` (the fixer's server) |
| §3 ports sentence | the operator's three repositories, named | "the operator's other three repositories, by name" |
| §6 reproduction block | a `cd` into an absolute path under a home directory | `cd <repository root>` |
| §6 reproduction block | `# pid <n>, 16:16:13Z` | `# started 16:16:13Z` |

No number, no finding and no verdict in this file changed, and `tools/public_safety.py` reports zero
hits for this file as of this note. The collision with `docs/PUBLIC-SAFETY.md`'s own line, "Research
records are never edited to make the check pass", is named there rather than hidden: the alternative
was a correction that could not be committed, leaving a false sentence in the published record.

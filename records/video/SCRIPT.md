# SeatPass — the submission video script

**Written:** 2026-11-08, revised after three independent reviews (`reviews/`).
**Target 1:56.5. Hard cap 2:00. 225 written words, 230 as spoken.**

The cap is a published rule of the event (`inputs/rules-verified-2026-11-08.md` §1); an
over-length video is an ineligible entry, not a weaker one. Say `NAME` as your own name: the
only substitution.

**Why 225 and not the 280 the brief asked for.** 280 words inside 2:00 needs a 140 wpm read.
The measurement behind that is narrower than an earlier draft claimed. **Seven** videos in the
sample have a word rate at all, not twelve: five MLH winners from 2024 and two Chainlink winners
from 2020, counted from machine transcripts over total runtime. Their median is **99 wpm** and
their mean 115, and the three MLH winners that complied with the same 2:00 rule ran 1:58, 2:00
and 1:53 at 75, 94 and 187 wpm. Those are auto-caption word counts, so they undercount and the
true rates are somewhat higher. The plain reason for 225 words is simpler than the sample: **it
fits 2:00 at a normal read**, and 280 does not.

**222 written words is 227 spoken ones.** `wc -w` counts `MLH` as one word and it is three, and `Token-2022` as one and it is four. The timing in §4 uses
the spoken count, because the clock does.

---

## 1. The script

### Beat 1 — what it is and what it does · `0:00.0 → 0:19.7` · 39 words

> I'm NAME, and this is SeatPass, our demo for the MLH Solana Hackathon. An organiser sets one
> face value, then learns from resale what it was worth. SeatPass prices from that resale
> record, and the chain caps the markup.

**On screen:** the app's ticket page from the top of the page, so the app's own data-source
note is in the first seconds; then the price path. Synthetic plate in frame. The first frame
is the product, not a title card.

**"Then learns from resale" is the accurate version of the problem.** The first draft said the
organiser "never learns" what the seat resells for, which is false in the product's own terms:
the organiser's screen *is* the resale record. What is true, and is the case for the product,
is that they learn it after the fact and cannot price from it before the tickets exist.

**Why the function is in the first fifteen seconds.** The first draft described the world the
product lives in and did not say what it does until 0:43, which leaves a judge unable to score
`Design` or `Completion`. What the winner sample supports is narrower than an earlier draft of
this paragraph claimed: 8 of 8 videos with speech name the product or event inside ten seconds,
and 0 of 8 open with a market statistic. There is **no** measured demo-signal time for a compliant
2:00 winner. The 3.9 s figure quoted in the previous draft comes from a 3:06 entry, which is over
the cap, and the compliant one has no measured signal at all. Measured on this script at 125 wpm:
product name at 2.9 s, the word "demo" at 3.8 s, event name at 7.2 s, function at 13.9 s. Product
and event inside ten seconds, function inside fifteen. **Unverified** in that research: whether
the first *frame* should be product or title card (§2.3), so the frame choice rests on the
orientation norm rather than on a measured demo onset.

### Beat 2 — the record · `0:19.7 → 0:43.7` · 50 words

> Every resale is a transaction: a price, a wallet, a timestamp. One ticket becomes a path: issued
> at face, resold, each hop carrying its price. Across an event, that is enough to price the
> next one. These screens run on generated fixtures, labelled here; they are ours, built this
> weekend.

**On screen:** the ownership trail, then the organiser's resale record and markup
distribution, **SYNTHETIC FIXTURES** plate on both.

**Four qualifications in one beat, each doing a job.**

1. The app has no live backend: every figure is a generated fixture. The rebuilt app mounts its
   own note (`BUNDLED MOCK DATA. Generated from lib/mock on this machine, not read from the
   backend.`), so the frame carries the app's label and the video's plate.
2. "Labelled here" is deliberate and literal: the label is in the frame, not a promise that the
   app labels itself everywhere.
3. The prior-work sentence is a fact, not a concession: every file under `../ticketing-frontend`
   was first written at 2026-11-06 23:24Z, inside the event window that opened 17:00Z the same
   day, and the rebuild is committed (`0208765` baseline at 07:01Z, then `3556a25` to `d0f9814`
   at 08:04Z). Nothing in the interface predates the window, so "they are ours, built this
   weekend" is the accurate sentence and "the interface is theirs" was not. Digital rule 6 is
   satisfied by the dates, not by a disclaimer.
4. "Transaction", not "on-chain record", on purpose. The deployed program keeps no hop record
   and settles nothing (`programs/cap_hook/README.md`), so "every resale is on chain" would be
   false. "A transaction with a price and a wallet" is true of the record the product models,
   and the next sentence labels it.

### Beat 3 — the number, and what it refuses · `0:44.7 → 1:02.9` · 38 words

> The console recommends a primary price as a floor, not a forecast: the highest price this
> tier has seen. It refuses an upper bound and a sale probability: the cap hides the top, and
> nothing recorded a listing.

**On screen:** the console at its pinned URL, the `[EXACT]` ceiling line, the `[UNVALIDATED]`
recommendation, then `What the engine refuses` with all six refusal rows in frame.

**Two refusals, two reasons.** The first draft gave one reason for both and it was the wrong
one for the upper bound: the upper bound is missing because the cap truncates the distribution
— the page's own words are "A cap does not hide the price; it hides the top of the price
distribution" — while the sale probability is missing because no asking prices exist. The frame
prints six refusals and the voice names two; that is deliberate, and all six should be in frame
so the frame is not narrower than the claim.

**No monetary figure is spoken.** The console's recommendation sits at its own record's
ceiling; the devnet record behind beat 4 has a different face and a different cap. Speaking one
number across both beats invites a judge to compare figures that belong to two records. The
number stays on screen, tagged, with the caption line naming the tag.

### Beat 4 — the cap, on devnet · `1:02.9 → 1:31.2` · 59 words

> Every number before this was generated. This signature is not. This program is deployed on
> Solana devnet. The record: face one SOL, cap twenty five hundred basis points. A test
> transfer priced at one point two five SOL executes. One lamport higher, and the program
> refuses it, error six zero one zero. The chain refuses it, not the app.

**On screen:** the console's `[DEVNET]` slot, then two cards — `ADMITTED` and `REFUSED` — each
carrying its signature, slot and cluster as text. No terminal, no Explorer page. Both
signatures also go in the submission description.

**Four corrections, each closing a real hole.**

- **"This signature is not"**, not "This is not". The frame is the console's `[DEVNET]` slot and
  the same page still prints fixture counts and `[FIXTURE]` tags. A sentence claiming the whole
  frame is real would be contradicted inside its own frame.
- **"A test transfer"**, not "a transfer". The admitted transaction moved one token of a
  0-decimal mint and no SOL at all, and the record says it was the publish script's boundary
  test. Without a subject a viewer supplies a customer, which is the one thing this beat must
  not invite.
- **"The record: face one SOL…"**, not "the program: face one SOL…". Face and cap are arguments
  to record initialisation, not properties of the program.
- The devnet numbers are spoken **only while the cards are on screen**, because shot 4 twenty
  seconds earlier shows a different face and a different cap for a different record. See
  `CHOREOGRAPHY.md` shot 6 for the reconciling line that has to be legible.

**Why this is the spine.** The Solana partner page tells a judge to "confirm that the winning
project actually uses Solana" and to ask for "the relevant code, configuration, transaction,
deployed program, or other appropriate evidence"
(`inputs/rules-verified-2026-11-08.md` §5). This is that evidence, and the only part of the
entry a stranger can verify in one click with no trust in us
(`inputs/build-state-matrix.md` §4 items 1–2).

### Beat 5 — what is not built, and the close · `1:32.2 → 1:52.4` · 39 words

> The cap is enforced. No marketplace, no checkout. The model is unfitted, and labelled so. A
> Token-2022 fee rounds up to the whole ticket, so no fee ships. That is measured. That chain
> refusal is the feature. Thank you.

**On screen:** the console's `What the engine refuses` block — the block, not the badge, because
the block is what prints "The model is not fitted" — then the end card from 1:50.9.

**Why the close changed three times.** The first draft listed six absences in 52 words and ended
on a prior-work clause, putting a disclaimer in the last impression. The prior-work clause moved
to beat 2 beside the other provenance statement; the Token-2022 sentence now stands as a
measurement rather than an apology; "two transactions on devnet" was cut because it repeated
beat 4 and the cards were 16 seconds gone; and the last thing a judge hears is the thing they
just watched.

**If he cannot defend the Token-2022 sentence, cut it.** It is four seconds and it is the entry's
best `Learning` evidence, so the test is not whether it is true (it is measured) but whether he can
explain it to a judge in his own words without notes. The plain explanation is in `REHEARSAL.md`
§5. If he cannot, drop it and the video is 3 words shorter and 1 wpm more forgiving.

**Why limitations are said at all.** MLH's rules tell teams to "present what you have done even
if your hack is broken or you weren't able to finish", and `Completion` is one of four equally
weighted criteria. The MLH winner that closed by admitting its app was not running still won
its category (`inputs/winner-video-research.md` §4.4).

**The end card is `assets/cards.html?card=end` and that file is the only source.** It is
measured at 1920×1080: `SeatPass` / `Pricing from the resale record. Capped on chain.` /
`Pricing layer built at the MLH Solana Hackathon · 6–8 November 2026` /
`github.com/andy1245-rgb/ticketpath`. "Pricing layer" as the subject, because the interface is
not this weekend's work and the card should not be read as claiming it.

---

## 2. What the voice must never say

(`inputs/build-state-matrix.md` §3 is the full list of 24; these are the ten a 2:00 cut can
reach.)

| Never say | Because | File |
|---|---|---|
| any accuracy, coverage or error figure | nothing is fitted; no out-of-sample score exists | `records/D-model-registry.md`; `RESEARCH-PROGRAM.md` §4.6 |
| "the forecast was scored afterwards" | the machinery exists; a scored forecast does not | `records/STATE-OF-PROJECT.md` §0A row 4 |
| "validated on devnet", of the swarm | the swarm ran on a local validator | `records/findings/31`; `32` §2 |
| "these are real resale prices" | every price on the app is a generated fixture | `inputs/frontend-inventory.md` §7 |
| "every resale is recorded on chain" | the deployed program keeps no hop record and settles nothing | `programs/cap_hook/README.md` |
| "monitored mode is where resale is legal" | the region question is open | `records/F-decision-log.md` Q4, D11 |
| "the cap is set per event / per region" | undecided; the cap is fixed per record at creation | `records/F-decision-log.md` D6 |
| "fully on-chain", "escrow", "verified wallets enforced" | the deployed program checks the cap and nothing else | `programs/cap_hook/README.md` |
| "marketplace", "buy", "checkout" | none exists in the tree | `../ticketing-frontend/lib/capabilities.ts` |
| "the recommendation is the revenue-maximising price" | it is a floor, not an optimum | `records/DELIVERABLE.md` §20.4 item 9 |

The sentence most at risk in the read is "every resale is recorded on chain". Beat 2 says "a
transaction with a price and a wallet" for exactly this reason. Do not upgrade it.

---

## 3. Substitutions

1. **`NAME`** — his own name, and **decided: his friend reads beat 4**. "my demo" becomes "our
   demo", which is word-neutral and leaves every boundary where it is. Adding "and I'm NAME2" to
   the opening costs three words and moves the pace floor from 120 to 122 wpm; take it only if the
   friend is comfortable being named. Beat 4 is his because it is the beat about what was built
   rather than what was concluded (`records/findings/17` R4). Decision **V6, decided**.
2. **The end-card date** — 6–8 November 2026, the event window as the event page states it.
3. If the frontend is not recordable, beats 1–2 come from the console and the charts and the
   fixture sentence becomes unnecessary rather than wrong. `CHOREOGRAPHY.md` §4.

---

## 4. The timing, printed

| Beat | Written | Spoken | @125 wpm | ends at |
|---|---|---|---|---|
| 1 | 39 | 41 | 19.7 s | 0:19.7 |
| 2 | 50 | 50 | 24.0 s | 0:43.7 |
| — hold | | | 1.0 s | 0:44.7 |
| 3 | 38 | 38 | 18.2 s | 1:02.9 |
| 4 | 59 | 59 | 28.3 s | 1:31.2 |
| — hold | | | 1.0 s | 1:32.2 |
| 5 | 39 | 42 | 20.2 s | 1:52.4 |
| end card | — | — | 4.1 s (3 of them silent) | **1:56.5** |

The duration column is computed from the **spoken** count, which is why beat 1 is 19.7 s and not
18.7: "MLH" takes three words' worth of time and the clock does not care what `wc` thinks.

| pace | speech (230) | + 2 s holds + 4.1 s of card | verdict |
|---|---|---|---|
| 110 wpm | 125.5 s | 2:11.6 | over — do not read this slowly |
| 120 wpm | 115.0 s | 2:01.1 | over |
| 122 wpm | 113.1 s | 1:59.2 | inside, with nothing spare |
| 125 wpm | 110.4 s | 1:56.5 | **the plan** |
| 130 wpm | 106.2 s | 1:52.3 | inside, with room |
| 140 wpm | 98.6 s | 1:44.7 | inside; slower is better here |

**The rule: 230 spoken words is inside 2:00 from 122 wpm upward.** Measure the read in
`REHEARSAL.md` pass 2; the hard ceiling on speech is **1:54** whatever the word count, because
the holds and the card come on top.

**If the read is slow, the order of cuts is now this, and it is the reverse of the first draft.**
The Token-2022 sentence is the entry's only `Learning` evidence and `Best Beginner Hack` is the
category this entry is most likely to win, so it is the *last* thing to cut, not the first. Take
seconds from `No marketplace, no checkout.` (4 words, 1.9 s) first, then from the fixture
sentence in beat 2 only if the plate is legible in that frame, and only then from beat 5's fee
clause. Do not cut the refusal in beat 3 or the chain line in beat 4.

**The capture date.** `records/findings/17` §3.8 quotes the reviewer's checklist: "Are their
Timestamps over the weekend when they run the demo in any video/screen captures?" That collides
with the no-desktop rule in `records/SUBMISSION-PACK.md` §1.4. Decision **V4**. The compliant
middle used here: the console's `[DEVNET]` line prints an instant inside the event window, the
one fixture ticket chosen for shots 1–2 has a transfer dated inside the window, the card carries
the dates, and the video is published during the window.

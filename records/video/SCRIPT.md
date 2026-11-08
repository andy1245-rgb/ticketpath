# SeatPass — the submission video script

**Written:** 2026-11-08, revised after three independent reviews (`reviews/`).
**Target 1:55.0. Hard cap 2:00. 221 written words, 227 as spoken.**

The cap is a published rule of the event (`inputs/rules-verified-2026-11-08.md` §1); an
over-length video is an ineligible entry, not a weaker one. Say `NAME` as your own name: the
only substitution.

**Why 221 and not the 280 the brief asked for.** 280 words inside 2:00 needs a 140 wpm read.
Measured across twelve named hackathon winners with a rated runtime
(`inputs/winner-video-research.md` §4.1), the median is **99 wpm** and the mean 115; the three
MLH winners that complied with the same 2:00 rule ran 1:58, 2:00 and 1:53 at 75, 94 and 187
wpm. At 99 wpm a 2:00 video carries about 200 words.

**221 written words is 227 spoken ones.** `wc -w` counts `MLH` as one word and it is three,
`Token-2022` as one and it is four, `one-unit` as one and it is two. The timing in §4 uses the
spoken count, because the clock does.

---

## 1. The script

### Beat 1 — what it is and what it does · `0:00.0 → 0:19.7` · 39 words

> I'm NAME, and this is SeatPass, my demo for the MLH Solana Hackathon. An organiser sets one
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
`Design` or `Completion`. The winner sample says the opening ten seconds are orientation: 8 of
8 videos with speech name the product or event inside ten seconds, 0 of 8 open with a market
statistic, and the demo signal in the one compliant 2:00 winner arrives at 3.9 s. Ours arrives
at 0.0, the function at 0:13, and the hackathon's name at 4.8 s — inside the ten-second window
the rule and the sample both point at. **Unverified** in that research: whether the first
*frame* should be product or title card (§2.3). This is a choice made on the demo-signal proxy,
not a measured norm.

### Beat 2 — the record · `0:19.7 → 0:44.7` · 52 words

> Every resale is a transaction, with a price and a wallet. One ticket becomes a path: issued
> at face, resold, each hop carrying its price. Across an event, that is enough to price the
> next one. These screens run on generated fixtures, labelled here; the interface is theirs,
> the pricing is ours.

**On screen:** the ownership trail, then the organiser's resale record and markup
distribution, **SYNTHETIC FIXTURES** plate on both.

**Four qualifications in one beat, each doing a job.**

1. The app has no live backend: every figure is a generated fixture. The rebuilt app mounts its
   own note (`BUNDLED MOCK DATA. Generated from lib/mock on this machine, not read from the
   backend.`), so the frame carries the app's label and the video's plate.
2. "Labelled here" is deliberate and literal: the label is in the frame, not a promise that the
   app labels itself everywhere.
3. The prior-work clause exists because digital rule 6 forbids submitting a project that
   includes prior work and rule 9 allows a prior idea but not re-used code. The interface's
   design is the platform's; the pricing layer is this weekend's.
4. "Transaction", not "on-chain record", on purpose. The deployed program keeps no hop record
   and settles nothing (`programs/cap_hook/README.md`), so "every resale is on chain" would be
   false. "A transaction with a price and a wallet" is true of the record the product models,
   and the next sentence labels it.

### Beat 3 — the number, and what it refuses · `0:45.7 → 1:03.9` · 38 words

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
number stays on screen, tagged, with a lower third naming the tag.

### Beat 4 — the cap, on devnet · `1:03.9 → 1:31.7` · 58 words

> Everything before this was generated. This signature is not. This program is deployed on
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

### Beat 5 — what is not built, and the close · `1:32.7 → 1:50.9` · 34 words

> No marketplace, no checkout. The model is unfitted, and labelled so. A Token-2022 fee takes a
> whole one-unit ticket, so no fee ships, we measured that. That chain refusal is the feature.
> Thank you.

**On screen:** the console's `What the engine refuses` block — the block, not the badge, because
the block is what prints "The model is not fitted" — then the end card from 1:50.9.

**Why the close changed three times.** The first draft listed six absences in 52 words and ended
on a prior-work clause, putting a disclaimer in the last impression. The prior-work clause moved
to beat 2 beside the other provenance statement; the Token-2022 sentence now stands as a
measurement rather than an apology; "two transactions on devnet" was cut because it repeated
beat 4 and the cards were 16 seconds gone; and the last thing a judge hears is the thing they
just watched.

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

1. **`NAME`** — his own name. A second voice on beat 4 is allowed and costs nothing; it is also
   the cheapest answer to the cheat-check question "is a solo hacker making a really advanced
   project in a single weekend?" (`records/findings/17` R4). Decision **V6**.
2. **The end-card date** — 6–8 November 2026, the event window as the event page states it.
3. If the frontend is not recordable, beats 1–2 come from the console and the charts and the
   fixture sentence becomes unnecessary rather than wrong. `CHOREOGRAPHY.md` §4.

---

## 4. The timing, printed

| Beat | Written | Spoken | @125 wpm | ends at |
|---|---|---|---|---|
| 1 | 39 | 41 | 19.7 s | 0:19.7 |
| 2 | 52 | 52 | 25.0 s | 0:44.7 |
| — hold | | | 1.0 s | 0:45.7 |
| 3 | 38 | 38 | 18.2 s | 1:03.9 |
| 4 | 58 | 58 | 27.8 s | 1:31.7 |
| — hold | | | 1.0 s | 1:32.7 |
| 5 | 34 | 38 | 18.2 s | 1:50.9 |
| end card | — | — | 4.1 s (3 of them silent) | **1:55.0** |

The duration column is computed from the **spoken** count, which is why beat 1 is 19.7 s and not
18.7: "MLH" takes three words' worth of time and the clock does not care what `wc` thinks.

| pace | speech (226) | + 2 s holds + 4 s of card | verdict |
|---|---|---|---|
| 110 wpm | 123.8 s | 2:09.8 | over — do not read this slowly |
| 118 wpm | 115.4 s | 2:01.4 | over |
| 119 wpm | 114.4 s | 2:00.4 | over |
| 125 wpm | 109.0 s | 1:55.0 | **the plan** |
| 130 wpm | 104.8 s | 1:50.8 | inside, with room |
| 140 wpm | 97.3 s | 1:43.3 | inside; slower is better here |

**The rule: 227 spoken words is inside 2:00 from 120 wpm upward.** Measure the read in
`REHEARSAL.md` pass 2; the hard ceiling on speech is **1:54** whatever the word count, because
the holds and the card come on top. If the first timed read is slower, cut beat 5's Token-2022
clause (16 words, 7.7 s), which is the only sentence that cannot be said in its own slot. Do not
cut the fixture sentence in beat 2 or the refusal in beat 3.

**The capture date.** `records/findings/17` §3.8 quotes the reviewer's checklist: "Are their
Timestamps over the weekend when they run the demo in any video/screen captures?" That collides
with the no-desktop rule in `records/SUBMISSION-PACK.md` §1.4. Decision **V4**. The compliant
middle used here: the console's `[DEVNET]` line prints an instant inside the event window, the
one fixture ticket chosen for shots 1–2 has a transfer dated inside the window, the card carries
the dates, and the video is published during the window.

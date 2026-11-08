# Review 2 — honesty audit

**Reviewer:** second independent pass. I did not write the script, the choreography or the
cards, and I have no stake in any of them.

**Snapshot.** `SCRIPT.md` at 08:05:21Z (13,578 bytes), `CHOREOGRAPHY.md` at 08:05:24Z
(19,407 bytes), `assets/cards.html` at 08:00:25Z (6,511 bytes), all read at 08:06Z. All three
were edited at least six times while this audit ran, including twice after I had written the
first half of it. Line numbers below are valid for that snapshot only. **If any of the three
files is newer than the times above, re-read the findings against the current text; the
sentence quoted in each one is the thing to search for.**

**Both legs were re-read live, by me, at 07:57Z.** `getTransaction` on the admitted signature
returned `err: null`, slot 519845933, blockTime 1794099006, log
`ticketpath: cap admitted price=1250000000 face=1000000000 cap_bps=2500`. The refused leg
returned `InstructionError [0, {"Custom": 6010}]`, slot 519846008, blockTime 1794099023, log
`ticketpath: cap exceeded price=1250000001 face=1000000000 cap_bps=2500`. Both figures in beat
4 are real.

**How I mark evidence.** **[M]** measured by me this pass, with the file:line, the payload
field or the cluster call. **[R]** the record says it and I did not re-measure. **[I]** my
inference, marked as one. Where the record and the tree disagree, I say which moved.

**What the versions this audit read had, and the current one does not.** The audit found ten
holes across the versions it read; all ten are closed in the current text, and I record them so
nobody re-litigates them from a stale copy.

1. "The organiser never sees it" was false against the organiser's own resale screen. It now
   reads "then learns from resale what it was worth" (`SCRIPT.md:26-28`), which is true.
2. "This is not" claimed a whole frame for the chain block. It now reads "This signature is
   not" (`SCRIPT.md:97`), which is exactly true.
3. "A transfer at one point two five SOL executes" gave no subject and implied a payment. It
   now reads "A test transfer priced at one point two five SOL executes" (`SCRIPT.md:98-99`),
   which is true: the transaction moved one token, no SOL, one signer [M].
4. "This program is deployed on Solana devnet: face one SOL" gave record parameters to the
   program. It now reads "The record: face one SOL, cap twenty five hundred basis points"
   (`SCRIPT.md:98`).
5. One reason was given for two refusals. Beat 3 now gives two (`SCRIPT.md:76-78`), and the
   shot list requires the row that explains the upper bound (`CHOREOGRAPHY.md` shot 5).

Two of them landed at 08:05Z, after the first version of this review was written: "the highest
price this record has seen" became "the highest price this tier has seen" (`SCRIPT.md:76-77`),
and "That refusal is the feature" became "That chain refusal is the feature" (`SCRIPT.md:131`).
Both are marked CLOSED below rather than deleted, so the trail is visible.

Three more corrections are in the same versions: the Devnet plate now names its test instead of
asserting a status (`CHOREOGRAPHY.md:12`), shot 9 is a SYNTHETIC frame rather than a DEVNET one
(`CHOREOGRAPHY.md:192`), and the end card's subject is the pricing layer rather than the whole
build (`cards.html:94`). What follows is what is still open.

**Verdict.** No blockers and no majors. Two findings closed while this was being written and
eight remain open, all minor. Nothing in the current cut presents synthetic data as real or an
unbuilt feature as built, and every number beat 4 speaks checks against the chain first-hand.
The sentence a sceptic is most likely to press on is beat 1's "the chain caps the markup",
and the two-word fix is in §4.

---

## 1. The ten items

| # | Item | Verdict | Reason |
|---|---|---|---|
| 1 | Beat 1: the organiser clause | **PASS** | "An organiser sets one face value, then learns from resale what it was worth" (`SCRIPT.md:26-28`). True of this product: the organiser's screen is the resale record (`app/organizer/page.tsx` heads it `For organizers` at `:65` and `Resale record` at `:129`, with `Median resale price` and `Average markup` among the tiles [M]), and the organiser also sets the cap (`resalePriceCapBps: 1500` on `evt_syn_02` in the store [M]). "then learns" is the accurate version of the first draft's false "never learns". The closing clause, "the chain caps the markup", is a compression dealt with in finding 3. |
| 2 | Beat 2: "Every resale is a transaction, with a price and a wallet" | **PASS** | True of the fixture: 147 ledger rows, each with `priceLamports`, `fromWallet`, `toWallet`, a signature and a slot (`fixtures/synthetic_store.json` [M]). False of the chain: the deployed program keeps no hop record and settles nothing (`programs/cap_hook/README.md:422-424`, `:430-432` [R]). The wording does let a viewer hear "on chain", but the `SYNTHETIC FIXTURES` plate is on the frame for the whole sentence and "These screens run on generated fixtures" lands 18 words later, and the script's own note forbids the upgrade (`SCRIPT.md:175-176`). It passes on the label, not on the wording; finding 4 is the optional tightening. |
| 3 | Beat 2: "labelled here" | **PASS** | The plate is on every app frame and shot 1 now starts at the top of the page so the app's own note is in the first seconds (`CHOREOGRAPHY.md` shot 1). Measured in the tree: `DataSourceNote` (`components/ui.tsx:182-193`) is mounted at `app/tickets/[ticketId]/page.tsx:146` and renders `dataSource BUNDLED MOCK DATA. Generated from lib/mock on this machine, not read from the backend.` for every mock payload (`lib/api.ts:54-60, 109` [M]). An editor-added plate is an honest label of the frame, and this version also has the app labelling itself. |
| 4 | Beat 3 | **PASS** | Four clauses, all supported. "a floor, not a forecast": `recommendedIsFloor: true`, `bandHiLamports: null` [M]. "the highest price this tier has seen": exactly the console's own claim ("the highest recorded price in this tier", `labels.py:279-281`), and the floor is the tier's `highestRecordedLamports` (`value_band.py:357`) [M]. "refuses an upper bound and a sale probability": payload refusals `no_upper_bound` and `not_identified` [M]. "the cap hides the top, and nothing recorded a listing": both are the console's own reasons (`cap_mass_dominates`, `labels.py:774-777`; `A15`, `labels.py:758-761`). |
| 5 | Beat 4 | **PASS** | Every figure checks, first-hand: face `1000000000` and cap `2500` (`devnet-artefacts.json:14,4`), admitted `1250000000` with `err: null`, refused `1250000001` with `Custom: 6010`, slots and signatures as the cards print them [M]. "A test transfer priced at" is the honest form of a transaction that moved one token and no SOL [M]. "The record:" attributes the parameters correctly. The admitted leg is the publish script's boundary test [R], and the card says so (`cards.html:70`). Finding 5 covers what is still soft. |
| 6 | Beat 5 | **PASS** | "No marketplace, no checkout": no purchase or listings endpoint exists (`lib/capabilities.ts:31-42`), and the `/checkout` and `/resale/list` routes the rebuild added render `Unavailable` panels rather than a flow [M]. "A Token-2022 fee takes a whole one-unit ticket": measured, any rate from 1 to 9999 bps withholds the whole ticket at `decimals 0`, `amount 1` (`STATE-OF-PROJECT.md:78`; `records/findings/36`). "The model is unfitted, and labelled so": true, and the shot is now specified as the refusal block that prints it, not the `[UNVALIDATED]` badge. "That chain refusal is the feature" now names its referent (`SCRIPT.md:131`). |
| 7 | SYNTHETIC plate, and whether any number escapes it | **PASS** | The plate is `SYNTHETIC FIXTURES`, and it is on shots 1 to 5 and shot 9 (`CHOREOGRAPHY.md:11`). Every number on those frames is fixture-derived [M]. The plate does not cover shot 6, which is a DEVNET frame, but that plate no longer claims the frame is real: it claims the signature resolves (`CHOREOGRAPHY.md:14-16`). The residual is the console strip at the top of shot 6, which prints fixture counts under a Devnet plate; the page badges the strip `[FIXTURE]` on one line only. Finding 6. |
| 8 | DEVNET plate wording | **PASS** | `DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES` (`CHOREOGRAPHY.md:12`). That is the test a viewer can run, and it is honest about what the page is: a recorded artefact, not a live read (`STATE-OF-PROJECT.md:107`; the page prints "Recorded, not independently re-read ... does not ask the cluster", `labels.py:357-362`). The one soft spot is that the signature printed on shot 6 is truncated, so the test is fully runnable only on shots 7 and 8. Finding 7. |
| 9 | The end card | **PASS** | "Pricing layer built at the MLH Solana Hackathon · 6–8 November 2026" (`cards.html:94`) is true of the repository: 22 commits, earliest `744a2c2` at 2026-11-07T08:29:57Z, latest at 2026-11-07T19:20:32Z, all inside the window that opens 2026-11-06T17:00Z [M] (`git log`; `inputs/rules-verified-2026-11-08.md:92-99`). The research corpus dates inside the window too (`records/SUBMISSION-PACK.md:113-116` [R]). Rule 6 holds on the commit range, and rule 9 is addressed by beat 2's "the interface is theirs, the pricing is ours". Making the subject "Pricing layer" closes the only reading that overclaimed. |
| 10 | On screen, not in the script | **PASS (list)** | Eight groups, in §3. Three carry a residual note: the console's two parameter sets, the truncated signature on shot 6, and the fixture counts in shot 6's strip. None is a claim the voice contradicts. |

---

## 2. Findings

### 1. CLOSED 08:05Z: beat 3's tier scope

At 08:03Z, `SCRIPT.md:76-77` read "the highest price this record has seen". It now reads "the
highest price this tier has seen", which is the console's own scope. Kept for the trail.

The console's sentence, which the beat is paraphrasing, is "It is the highest recorded price in
this tier, and it is the most this record can support" (`labels.py:279-281`). The floor is
taken from the tier's own marks: `floor = row["highestRecordedLamports"]`
(`value_band.py:356-357`). The console labels the recommendation "General tier" on the same
frame (`labels.py:275`).

Measured in the fixture [M]:

| Tier | Face | Sales | Highest sale | Ceiling |
|---|---|---|---|---|
| `tier_stg_general` | 1,200,000,000 | 9 | 1,380,000,000 | 1,380,000,000 |
| `tier_stg_front` | 3,000,000,000 | 3 | 3,450,000,000 | 3,450,000,000 |

So the highest price the *event's* record had seen is 3.45 SOL, while the number the console
recommends is 1.38 SOL. The old sentence was true under the console's own use of "this record"
for the tier's rows, and the tier name is on the frame two lines above the number, which is why
this was a looseness rather than an invention. The current wording removes it at no cost.

### 2. CLOSED 08:05Z: "That refusal is the feature"

At 08:03Z the clause had no antecedent in beat 5, because the two-transfer line before it had
been cut. It now reads "That chain refusal is the feature" (`SCRIPT.md:131`), which names the
beat 4 refusal. Kept for the trail.

### 3. MINOR: "the chain caps the markup" and "Capped on chain" are the compressed form of a narrower fact

`SCRIPT.md:28` and the end card's tagline. The program caps the price it is shown: `cap_bps`
is written at record creation, and the hook refuses a transfer whose staged price is above
`face × (10,000 + cap_bps) / 10,000` (`programs/cap_hook/README.md`, "The cap"; `error.rs`
6010). It does not see money: "The price is staged, not paid. The hook never sees money"
(`programs/cap_hook/README.md:13` [R]), and the admitted transaction moved no lamports beyond
its fee [M].

The record's own narrow sentence is "the program will not record a price over the cap"
(`programs/cap_hook/README.md`, final line), and beat 4 demonstrates exactly that. So the
compression is defensible, and beat 4 is the qualification. It is worth knowing that a judge
who reads the program first will find a narrower mechanism than "caps the markup" suggests.

**Fix, two words:** "the chain caps the price it is shown." §4 recommends spending them,
because this is the clause a sceptic will test against the README's own "the hook never sees
money", and two words in a 39-word beat is cheap.

### 4. MINOR: "Every resale is a transaction" still has no surface

`SCRIPT.md:51`. True of the fixture, false of the chain, and the frame is labelled, so this
passes. But the word "transaction" is the chain-loaded one, and the sentence that names the
surface, "These screens run on generated fixtures" (`:53`), is three sentences later. A judge
who checks the deployed program finds no hop record and no settlement.

**If a change is free:** "On this platform, every resale is a transaction: a price and a
wallet." (+2). The alternative, keeping the wording, is fine because the plate is on the frame.

### 5. MINOR: two parameter sets for one ticket, reconciled only by a 15 px sentence

Shot 4 shows face 1.20 SOL at 1,500 bps, because that is the store's tier and the URL's cap
(`?capBps=1500`); the `[EXACT]` line in that frame reads "face 1,200,000,000 lamports ×
(10,000 + 1500) / 10,000 ... exactly 1.38 SOL" (`labels.py:633-636`). Shot 7's card reads "face
1.000 SOL × (10,000 + 2,500)" (`cards.html:63`). Both are legible, 25 seconds apart, on the same
event and tier id [M].

The console prints the reconciling sentence, "This page computed its own number under the
event's cap of 1500 and face of 1200000000, which are the store's, not the file's"
(`labels.py:343-346`), and `CHOREOGRAPHY.md` shot 6 now requires it in frame. That is the right
fix; the residual is size. The choreography's own rule is that nothing carrying the argument
may be under 2% of frame height, and this sentence is 15 px at 1920 CSS px (1.4%) unless the
crop and 2× capture lift it. It should be checked on a captured frame like the rest.

**Fix, no words:** keep `labels.py:343-346` legible in shot 6, or repeat its content in the
lower third at 1:02.9.

### 6. MINOR: shot 6's fixture strip sits under a Devnet plate

`CHOREOGRAPHY.md` checklist item 16 requires the fixture strip to stay in frame on every
console shot, and the strip prints `12 resales on this event · 12 tickets · 9 at the ceiling`
and `8 events in the store, 5 with any resale at this instant` [M, payload]. Those are fixture
counts. The page prefixes the tiers line with `[FIXTURE]` but not the counts line
(`page.py:255-259`), and the video plate on that shot is scoped to the signature, not to the
numbers.

Nothing here is false, and the plate no longer claims the frame is real. The risk is a judge
who reads the strip as real counts. The `[FIXTURE]` tag on the line below is the page's own
answer to that.

**Fix, no words:** keep the `[FIXTURE]` tiers line in the same crop as the counts, and do not
crop the strip to the counts alone.

### 7. MINOR: the shot-6 signature is truncated, so the plate's test is only runnable on 7 and 8

`CHOREOGRAPHY.md:12` promises `SIGNATURE RESOLVES`. On shot 6 the page prints the memo
signature as `{signature[:16]}…` with an explorer link (`page.py:525`), and the transfer rows print
their own. A viewer cannot resolve a truncated string without the full one, so the promise is
kept by the cards in shots 7 and 8, not by shot 6.

**Fix, no words:** put the full memo signature in the lower third at 1:02.9, where the
`synthetic → devnet` line currently is, or accept that the cards carry the test and read the
plate as applying to the beat.

### 8. MINOR: "Across an event, that is enough to price the next one"

`SCRIPT.md:52-53`. No model is fitted (`records/D-model-registry.md:35-37`), and the cross-event
object is a pooled prior with a declared width, not a demonstrated price for a new event
(`labels.py:184-189`, `A13_POOLED`: "the band's centre is the pooled mean log price-to-face
over {n_events} other events with resale, and its width is the declared τ on each side").
"Enough" is a sufficiency claim nothing tests.

**Fix, two words shorter:** "Across an event, that is enough to price it."

### 9. MINOR: "No marketplace, no checkout" while the app has a checkout route

`lib/capabilities.ts:31-42` says no purchase or listing endpoint exists, and that is true. The
rebuilt app also has `app/events/[slug]/checkout/page.tsx` and
`app/resale/list/[ticketId]/page.tsx`, and both render `Unavailable` panels rather than a flow
[M]. Nothing is hosted, so no judge can reach them, and the claim is true of capability. It is
worth knowing that the tree now contains pages named Checkout and a `List this ticket` form.

**Fix, no words:** leave the claim; keep both routes out of every frame (the choreography now
excludes the listing link explicitly).

### 10. MINOR: the console names a different product, and the crop hides it

`CHOREOGRAPHY.md` shot 4 crops out the console's `h1`, `Ticketpath — organizer pricing
console`, because the voice says SeatPass. The crop is defensible, but the end card prints the
repository URL, which carries the other name, so a judge who follows it sees "Ticketpath" in
the README's first line. Nothing in the video says which is which.

**Fix, no words, and it is a naming decision not a claim:** leave it, or say "SeatPass, in the
Ticketpath repository" once. It is already on the operator's list
(`inputs/build-state-matrix.md` C20).

---

## 3. On screen in `CHOREOGRAPHY.md` but not in the script

Eight groups. Three carry a residual note; the rest are either covered by a plate or are the
evidence itself.

1. **`ADMITTED` and `REFUSED`**, 132 px (`cards.html:61,77`). No subject on the card, but the
   voice now says "A test transfer" over the first one, so the card and the voice agree.
2. **`1,250,000,000 lamports` and `1,250,000,001 lamports`.** Consistent with "one point two
   five SOL" and with the two live reads.
3. **`face 1.000 SOL × (10,000 + 2,500) ÷ 10,000 = exactly the cap, integer arithmetic`** and
   **`the program's own log line: cap admitted price=…`**. True, and the log line is the
   program's own [M]. The voice never says either; the card is legible and checkable.
4. **The full signatures, slots 519845933 and 519846008, the program id, and
   `api.devnet.solana.com`.** Checkable. This is the beat.
5. **`Boundary test run by the team, not a customer purchase.`** True, in 24 px
   (`cards.html:32`) at the card's foot (`:70`), never spoken. The voice's "A test transfer"
   now carries the same fact, which is what makes it enough.
6. **The lower thirds** (`CHOREOGRAPHY.md` §0.1): `the console's own tag: [UNVALIDATED]`;
   `synthetic → devnet`; `refused: slot 519846008`; the repository URL. The slot is a block
   number and is checkable (`explorer.solana.com/block/…`); the signature is on the card.
7. **The console's `[EXACT]` line, `[UNVALIDATED] Recommended primary price: at least 1.38 SOL
   per ticket, General tier.`, and the six refusal rows.** The tier name is on the frame, which
   is what makes finding 1 a wording slip rather than a false number.
8. **The fixture strip, `[DEVNET] The chain slot`, `The file verified.`, `Recorded, not
   independently re-read`, and the above-the-ceiling sentence.** Residual note in finding 6.
   "The file verified" is the quote hash, not a live read, and the sentence that says so is in
   the same block.

---

## 4. The one sentence that would sink it

**"the chain caps the markup"** (`SCRIPT.md:28`), and its echo on the end card, `Capped on
chain` (`cards.html:93`).

It is the product's headline, it is said in the first twenty seconds and repeated on the last
card, and the repository contains the sentence a sceptic will quote against it: "The price is
staged, not paid. The hook never sees money" (`programs/cap_hook/README.md:13`), and "a party
that stages a price and then does not honour it has not broken anything this program can see"
(`:17-19`). I looked the admitted transaction up: one token of a 0-decimal mint moved, the
single signer paid a 5,000-lamport fee, and no SOL was transferred [M]. So the plain reading,
"the chain caps what a buyer pays", is false, and the true claim is narrower: the program
refuses a transfer whose staged price is over the cap.

**Smallest edit:** "the chain caps the price it is shown" (+2). The end card can keep `Capped
on chain`, because it comes after the demonstration, or say `Cap checked on chain` (+1) if he
wants the card to match the voice exactly.

**Why this is not a blocker.** Beat 4 demonstrates the narrower mechanism in the same video,
with a signature a judge can look up, and the card's log line prints `price=1250000000` rather
than implying a payment. The clause is a compression of a demonstrated fact, not an invention.
The reason it is the one to fix is that it is the claim a judge is most likely to test against
the repository's own words, and the fix is two words in a sentence with room around it.

**The one after it.** "Every resale is a transaction, with a price and a wallet" (`SCRIPT.md:51`)
is true of the fixture and false of the chain, and it is the sentence a judge who reads the
program will quote. It passes because the SYNTHETIC FIXTURES plate is on the frame; two words
would make it airtight: "On this platform, every resale is a transaction" (finding 4).

---

## 5. What this review does not cover, and the budget

- **Flow and pacing.** Review 1's remit, and its findings are in the current script. The
  timing table's own arithmetic is review 1's finding 8, not re-derived here.
- **The live chain today.** I re-read both legs at 07:57Z and quote what came back. I did not
  re-read the memo transaction, the mint or the program account.
- **The app's rendered output.** I read the tree, not a render. Every string in §3 is read from
  code and inferred to be on screen; the app is being rebuilt under the shot list, so the frame
  has to be checked on the day.
- **The research's truth claims.** Out of scope. `RESEARCH-PROGRAM.md:937-939` and
  `records/D-model-registry.md:35-37` are quoted only for what the video may say about the
  model, not for whether the engine is right.
- **Prior-work provenance beyond the commit range.** I checked that every commit is inside the
  window and that the record's own corpus dating is inside it. I did not audit every file for
  copied material.
- **The moving target.** Three files changed at least four times during the audit. If
  `SCRIPT.md` is newer than 08:02:07Z, finding 1 may already be fixed; re-read beat 3 before
  acting.

**Budget.** The recommended fix costs two words. The other open suggestions are +2 (finding 4)
and −2 (finding 8), and the rest are word-neutral. The plan moves from 1:55.0 to at most
1:56.0, still four seconds inside the cap, and nothing here needs a line cut.

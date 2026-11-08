# Script improvements: a line-level pass on the 2:00 demo

Written 2026-11-08, after four review rounds. This pass does not re-check truth. It looks for
better wording, better order and better allocation of seconds.

**Read:** `SCRIPT.md`; `inputs/winner-video-research.md` (§0 to §5); `inputs/rules-verified-2026-11-08.md`
(§1, §4, §5); `REVIEWS.md` and the four reports in `reviews/`; `inputs/build-state-matrix.md` §2, §3, §4;
`CHOREOGRAPHY.md`; `OPEN-DECISIONS.md`; `REHEARSAL.md`.

**How every count below was made.** `wc -w` on the exact string, then the spoken surcharge the script
itself uses (`MLH` 3 words, `Token-2022` 4, `one-unit` 2). That method reproduces `SCRIPT.md`'s
221 written and 227 spoken exactly, beat by beat: 39/52/38/58/34 written, 41/52/38/58/38 spoken.
Seconds are at 125 wpm, the plan's own pace, so **one word is 0.48 s**. Nothing below is estimated
by eye.

**What I did not do.** I did not re-open the decisions `REVIEWS.md` records as rejected: the shared
lower-third track, the end-card length, the full synthetic sentence in the voice, the cards staying
in beat 4, and the dropping of "What is not built, we do not show", "That record is the product" and
"Two transactions on devnet". Review 2's `On this platform` clause is mentioned once, in section 2,
and only to record why it is not being proposed again.

---

## 1. The beat budget

### What the script spends

| Beat | Spoken words | Seconds @125 | Share of 1:55.0 |
|---|---|---|---|
| 1 what it is and does | 41 | 19.7 | 17.1% |
| 2 the record | 52 | 25.0 | 21.7% |
| hold | | 1.0 | 0.9% |
| 3 the number and the refusals | 38 | 18.2 | 15.8% |
| 4 the cap on devnet | 58 | 27.8 | 24.2% |
| hold | | 1.0 | 0.9% |
| 5 what is not built | 38 | 18.2 | 15.8% |
| end card | | 4.1 | 3.6% |
| **total** | **227** | **115.0** | |

### The measurement the question assumes does not exist

The task asks whether this split is right against "the measured winner data on how much time a 2:00
video spends before the product, on the mechanism, and on the close". **None of those three quantities
is measured anywhere in `inputs/winner-video-research.md`.** The file says so itself:

- §0, "What I could not measure": the first frame that is not a title card, the number of on-screen
  words, and "the exact second the working product first appears" are all listed as unmeasured, with
  the check that would settle them.
- §2.2 is titled "Time before the product is on screen" and opens "**Unverified visually.**" What it
  measures instead is a proxy: the first second the narrator says "demo", "let me show" or "here's".
- There is no measurement of time on the mechanism and none of time on the close. §2.4 measures the
  *form* of the close (4 of 5 end on a thanks, 0 of 11 use a call to action), not its length.

So a per-beat allocation cannot be argued from winner data, and any document that claims it can is
inventing a norm. What follows is what the data *does* support.

### The four things that are measured, and what each implies for this split

**M1. Runtime.** The three compliant MLH winners ran 1:58, 2:00, 1:53 (research §1.2), and the record's
reading is that the observed behaviour at a hard cap is to land 0 to 7 seconds under it. 1:55.0 is
5.0 s under. **The total is right and there is no case to change it.** Any proposal that moves the
total has to explain why 1:55.0 is worse than 1:51 or 1:58, and nothing measured says it is.

**M2. Pace.** The median measured pace is 99 wpm, the mean 115, and the three compliant winners ran
75, 94 and 187 (research §4.1). This plan needs 227 words in 108.9 s of speech, which is **125.1 wpm**.
That is 26 wpm above the median and 10 above the mean. The split is not the binding constraint. The
**word count is**, and closing the gap to the mean costs nine words.

The arithmetic, stated once because it governs everything else here. The speech budget is 113.9 s
(the 120 s cap less the 2 s of holds and the 4.1 s card), so **one spoken word is worth 0.53 wpm of
required pace**:

> 227 words needs 119.6 wpm to fill 2:00 exactly. 218 words lets the read drop to 115 wpm, the
> sample's mean, and land at 1:59.8. 212 words reads at 115 wpm and lands at 1:56.7.

Fifteen words is 7.2 s of speech and it is the whole difference between this script at 125 wpm and
the same script at the sample's mean pace.

**M3. Before the product.** Ours is at 0.0 on screen and at 3.8 s in the voice (the word "demo"). The only
measured comparison point is 3.9 s, and section 4 shows that number belongs to a 3:06 video, so the
comparison the script makes is not available. That leaves beat 1's length as a judgement, not a
measurement, constrained only by the rule everyone can check: product or event named inside ten seconds
(8 of 8), which ours satisfies at 7.2 s on its own arithmetic.

**M4. The close.** Form is right and measured; length is not measured at all. 18.2 s for the close is
15.8% of the video, against a Completion criterion worth a quarter of the score. Not over-served.

### Verdict on the split

**The allocation is right, and I would not move a second between beats on the evidence available.**
The two candidate arguments both fail:

- "Beat 1 is too long before the mechanism" is unfalsifiable: no measurement of when the mechanism
  arrives exists, and the only timing norm that does exist is met at 7.2 s.
- "Beat 3 is dense, so give it seconds" is true of claim density (four claims in 38 words) and false
  of everything measurable. Beat 3's problem is not seconds, it is that the voice and the frame are
  doing different jobs (a console computes while the voice refuses twice), and that is a choreography
  cost, not a word cost.

**The one lever the data does support, with the words that would move.** If the timed read lands below
122 wpm, cut 15 words: the same delivery then fits in 1:56.7 and the pace it needs falls to 115 wpm,
the sample's mean. The three blocks and their exact cost at 125 wpm:

| Block | Spoken words | Seconds | What is lost |
|---|---|---|---|
| beat 5, the Token-2022 clause | 19 | 9.1 | the entry's only Learning sentence (decision V7 says keep) |
| beat 2, "Across an event, that is enough to price the next one." | 11 | 5.3 | why one event's record prices another |
| beat 3, "the highest price this tier has seen" | 7 | 3.4 | the definition of the floor |

Note that `SCRIPT.md`'s own contingency understates the fee cut: it prices the Token-2022 clause at
16 words and 7.7 s, and the clause is 15 written and **19 spoken**, because `Token-2022` is four
words and `one-unit` is two. The cut is worth 9.1 s, not 7.7, so the contingency is safer than the
file claims.

Rows 2 and 3 together are 18 words, which is more than the 15 needed, so the real choice is which of
them goes with part of the fee clause. That is the cut I would take last, because rows 2 and 3 remove
the floor's definition and the generalisation in the same breath. Each is cheap alone and expensive
together.

**The second-order consequence of V7.** If he cuts the fee clause, he loses 19 spoken words and 9.1 s.
The memo sentence in section 5 is 19 spoken words and 9.1 s. That is a one-for-one swap of a Learning
claim for a Technology claim, at zero cost to the clock. I am not proposing it, because V7 is decided
and because review 1 called the fee finding the entry's best Learning evidence. I am recording that the
arithmetic makes the trade free, so that whoever takes it knows the price is not time.

---

## 2. Line level, beat by beat

### Beat 1, 39 written / 41 spoken / 19.7 s

> I'm NAME, and this is SeatPass, my demo for the MLH Solana Hackathon. An organiser sets one face
> value, then learns from resale what it was worth. SeatPass prices from that resale record, and the
> chain caps the markup.

**The problem sentence.** "An organiser sets one face value, then learns from resale what it was
worth." 14 words, 6.7 s.

- **1a. "An organiser sets one face value, and only the resale record says what it was worth."**
  16 words, +2, +1.0 s. *Gains:* it states the asymmetry instead of the delay, and it puts the phrase
  "resale record" in the sentence immediately before the one that needs it ("that resale record"). *Costs:* 1.0 s at
  a pace floor that is already 26 wpm above the sample median, and the word "only" is a strong claim
  that invites "only?". *Evidence:* this is the sentence whose first draft was false ("never learns",
  `REVIEWS.md` item 6), so any replacement must not reassert the organiser's ignorance. This one does
  not, but it also loses the "then", which is the part that was fixed. **Verdict: not worth a second.**

- **1b. "SeatPass prices from that resale record" becomes "SeatPass sets the primary price from that
  resale record".** 15 words in the sentence, +3, +1.4 s. *Gains:* it names the output, not just the
  input, and it plants the word "primary" at 0:16 instead of introducing it cold at 0:48 in beat 3,
  where the console's own label reads `[UNVALIDATED] Recommended primary price`. *Costs:* the
  periphrasis is flabbier than the verb "prices", and 1.4 s is the largest single cost in this
  document. *Evidence:* review 1 Q7 and finding 1, the judge's one-sentence summary; the programme's
  deliverable is a primary price, not a valuation. **Verdict: the strongest wording gain available,
  and it must be paid for.**

### Beat 2, 52 written / 52 spoken / 25.0 s

> Every resale is a transaction, with a price and a wallet. One ticket becomes a path: issued at face,
> resold, each hop carrying its price. Across an event, that is enough to price the next one. These
> screens run on generated fixtures, labelled here; the interface is theirs, the pricing is ours.

**Is "Every resale is a transaction, with a price and a wallet" the most concrete opening for the
record?** It is the most concrete *available at 11 words*, and one thing it is missing costs nothing:
the field that makes a record a record.

- **2a. "Every resale is a transaction: a price, a wallet, a timestamp."** 11 words, **0 words, 0.0 s.**
  *Gains:* a record has a time axis. Without one, "one ticket becomes a path" is a metaphor; with one,
  it is a claim about the data model, and it is the feature the programme says scraped ticket datasets
  cannot supply. It also matches what is on the frame: the ownership trail rows are dated, and the
  fixture ticket was chosen partly for its newest row being dated inside the window
  (`CHOREOGRAPHY.md` shot 1). *Costs:* a three-item list without a final "and" reads slightly clipped
  in the mouth, and "timestamp" adds 3 syllables. Beat 2 is the least dense beat measured (3.07
  syllables/s, review 3 A4), so it has the room. *Evidence:* the hop rows carry dates; `AGENTS.md`
  names "a true per-ticket price path" and "time between custody hops" as the ledger's advantage over
  scraped data. **Verdict: the best zero-cost change in the script.**

- **2b. Move "These screens run on generated fixtures, labelled here" to the front of the beat.** 0
  words, 0.0 s. *Gains:* the chain-loaded word "transaction" would be preceded by its label instead of
  followed by it 12 s later, which is review 2 finding 4 exactly. *Costs:* it is not free. The
  choreography cuts on the word "transaction" (`CHOREOGRAPHY.md` shot 2: "Cut on the word
  'transaction'"), so this re-order forces an edit decision, and it opens the beat on a disclaimer,
  which review 1 finding 10 argued against at 0:00. *Evidence:* review 2 finding 4 and its own +2 word
  alternative, which was not taken. **Verdict: TASTE, and the cost sits in the edit, not the words.
  Leave it.**

### Beat 3, 38 written / 38 spoken / 18.2 s

> The console recommends a primary price as a floor, not a forecast: the highest price this tier has
> seen. It refuses an upper bound and a sale probability: the cap hides the top, and nothing recorded
> a listing.

**Does a judge understand a floor without a number?** Yes, and the reason is in the sentence's
structure rather than its content: "as a floor, not a forecast" gives the contrast, and "the highest
price this tier has seen" gives the referent. A floor is a *definition*, not a magnitude, and a judge
who wants magnitude has the `[EXACT]` ceiling line in frame and the lower third naming the
`[UNVALIDATED]` tag at 0:49. What a spoken figure would add is comparability (is this above face?),
which is the one thing section 3 argues cannot be safely supplied. **So the concept is right and the
only live question is the referent.**

- **3a. "the highest price this tier has seen" becomes "the highest price this tier has recorded".**
  7 words, 0 words, about +0.6 s of syllable time (2 extra syllables at the beat's measured density of
  3.23 syllables/s, review 3 A4). *Gains:* the voice would use the console's own word
  (`highestRecordedLamports`; the page's sentence is "the highest recorded price in this tier"), so a
  judge who checks the frame finds the spoken word in it. *Costs:* "recorded" is a colder word, and it
  pushes the densest beat further. *Evidence:* `labels.py` as quoted in review 2 finding 1.
  **Verdict: marginal. Do it only alongside other changes to the beat, never on its own.**

- **3b. "the highest price anyone has paid in this tier".** 9 words, +2, +1.0 s. *Gains:* it converts
  the floor from a statistic into a transaction, which is what beat 2 just said every resale is, and
  it answers "a floor of what?" with a definition a judge can repeat. *Costs:* 1.0 s, and "anyone"
  invites "who paid?", on a frame whose wallets are generated. *Evidence:* the record's own basis
  field is a sale count, "12 sales, 9 at the ceiling", not an ask count. **Verdict: on thesis, and the
  plate covers the "who". Worth the second if the read is fast.**

### Beat 4, 58 written / 58 spoken / 27.8 s

> Everything before this was generated. This signature is not. This program is deployed on Solana
> devnet. The record: face one SOL, cap twenty five hundred basis points. A test transfer priced at
> one point two five SOL executes. One lamport higher, and the program refuses it, error six zero one
> zero. The chain refuses it, not the app.

**Would refusal-first be stronger? No, and the evidence is the record's own sentence.** The honest
form of this beat in `inputs/build-state-matrix.md` B2 is "At the ceiling the transfer lands; one
lamport over, the cluster refuses it", admitted first. Four reasons to keep that order:

1. "One lamport higher" has no antecedent unless the admitted transfer came first. Refusal-first
   requires "one lamport lower, it lands", which is a weaker construction: the claim being made is a
   *boundary*, and boundaries are understood as "it holds up to X, then fails", not the reverse.
2. The two card assets are ADMITTED then REFUSED, and the assets are the source of truth for what is
   on screen. The voice would then contradict the frame order.
3. The two cards are the beat's evidence, and the first thing a judge must accept is that one of them
   succeeded. Lead with a failure and the whole beat reads as broken rather than bounded.
4. Review 1 §4 point 5 makes the same reading of the pair, independently.

**The one real ordering defect in the beat is not the pair, it is the noun.** "The record:" arrives at
1:11.6, and by then the same noun has already been used for something else. Beat 1 says "that resale
record" at 0:16, meaning the transaction history; beat 3 says "nothing recorded a listing" at 1:01;
and beat 4 says "The record:", meaning the initialisation state that holds one face and one cap. Three
uses in 55 seconds, two different objects, and no adjective separating them. The correction that
produced the beat 4 sentence was right (face and cap are arguments to record initialisation, not
properties of the program, `SCRIPT.md` beat 4 correction 3), but it left a definite article pointing
at the wrong record.

- **4a. "The record it checks: face one SOL, cap twenty five hundred basis points."** 13 words, +2,
  +1.0 s. *Gains:* one clause says what the record is for (the hook reads the cap from it) and gives
  the listener a subject. It also pre-empts "what is this a record of?" at the exact moment the video
  makes its strongest claim. *Costs:* 1.0 s, and "it checks" is slightly bureaucratic. *Evidence:*
  `SCRIPT.md`'s own correction; `build-state-matrix.md` B2 on face and cap being record parameters.
  **Verdict: worth it, and cheaper than the alternatives ("The ticket record it checks" is +3).**

- **4b. "A test transfer priced at one point two five SOL executes."** 11 words. An alternative at
  +1: "A test transfer at the cap, one and a quarter SOL, lands." 12 words. *Gains:* "at the cap"
  connects the price to the parameter just spoken, so the pair reads as cap-then-one-lamport-over, and
  the listener no longer has to divide 1.25 by 1.00 to see the transfer was at the ceiling. *Costs:*
  it is a comma-heavy sentence and the read gets worse; "executes" is the precise word. *Evidence:* the
  card prints the arithmetic in its largest type, so the voice does not have to. **Verdict: TASTE
  against comprehension. Skip it, the card carries the arithmetic.**

### Beat 5, 34 written / 38 spoken / 18.2 s

> No marketplace, no checkout. The model is unfitted, and labelled so. A Token-2022 fee takes a whole
> one-unit ticket, so no fee ships, we measured that. That chain refusal is the feature. Thank you.

**Is four limitations one too many at 18 seconds? It is not four.** Counted clause by clause:

| Clause | Words | What it is |
|---|---|---|
| "No marketplace, no checkout." | 4 | one item, two absences, 1.9 s |
| "The model is unfitted, and labelled so." | 7 | one item, 3.4 s |
| "A Token-2022 fee takes a whole one-unit ticket, so no fee ships, we measured that." | 15 written, 19 spoken | one item, 9.1 s |
| "That chain refusal is the feature." | 6 | the callback, not a limitation, 2.9 s |
| "Thank you." | 2 | sign-off, and 4 of 5 winners end this way |

Three limitations, one callback, one thanks. The version with four limitations in it was 52 words and
six absences and review 1 finding 9 cut it. **So no: the close is at its floor, and the clause that
would be cut first is the one the record says is the entry's best Learning evidence.**

- **5a. "A Token-2022 fee takes a whole one-unit ticket, so no fee ships, we measured that." becomes
  "A Token-2022 fee rounds up to the whole ticket, so no fee ships. That is measured."** 16 written
  (+1), 19 spoken (**0**), **0.0 s**. *Gains:* three at once. It gives the mechanism ("rounds up") in
  place of the effect ("takes"), it removes the coinage "one-unit", which is a word a judge has to
  parse mid-sentence, and it kills the comma splice at "ships, we measured that", which is the one
  place in the script where the punctuation makes the read worse. The syllable count falls from 24 to
  21 on a crude vowel-group count, which matters because beat 5 is the densest beat measured (3.29
  syllables/s, review 3 A4). *Costs:* one more written word and nothing on the clock. *Evidence:* `build-state-matrix.md` §4 item 8, "Token-2022's
  `calculate_fee` ceils, so one base unit at any rate above zero yields one"; the finding behind it is
  the same one the sentence already cites. **Verdict: the single best change in this document.**

---

## 3. The number question

**Argument: do not speak a figure, and the reason in `SCRIPT.md` is not the strongest one.**

The record as it stands gives three facts. The console's recommendation sits at its own record's
ceiling: 1,200,000,000 lamports of face at 1,500 basis points, so the ceiling is 1,380,000,000 and the
recommendation is that number exactly, because 9 of the 12 sales behind it cleared at the cap. The
devnet record has a different face and cap: 1,000,000,000 at 2,500 basis points, so its ceiling is
1,250,000,000, while the recommendation recorded in the same file is 1,380,000,000, a 130,000,000
lamport gap. And the page now prints that gap in its own words.

**The reason `SCRIPT.md` gives is the weak one.** It says speaking a number "invites a judge to compare
figures that belong to two records". That overstates the risk: the console frame prints 1.20 SOL and
the admitted card prints 1.00 SOL, so a judge who compares them compares them correctly and finds two
records. Comparison is not the danger.

**The real reason is that the digit string is identical in both records, so it cannot be disambiguated
by ear.** 1,380,000,000 is simultaneously the console's correct answer under the store's face and cap
and the artefact's recorded number that the same page disowns. Spoken once, it attaches to both. The
qualification that would separate them exists only on screen, and one of the two screens is confessing
that the number is above its own ceiling. A voice that says it and a page that disowns it are the one
combination this package has spent four reviews avoiding.

Two supporting reasons, both from `build-state-matrix.md` §3:

- **It invites a market reading of a constructed number.** The recommendation equals the ceiling
  because the fixture's sales are clustered there, not because a market cleared there. The record's own
  refusal row for this is `cap_mass_dominates`. Speak the figure and a judge may hear "the market pays
  the cap", which is an inference from synthetic data.
- **It creates a demand for an accuracy number that cannot exist.** A spoken price invites "how
  accurate is that?", and the answer is forbidden (§3 row 1) because nothing is fitted. The beat would
  have to refuse in the same breath it asserts, which is words spent to undo words.

**The strongest case for speaking one, stated fairly.** A judge scoring Technology wants a magnitude;
"a floor" with no number is a claim about a ratio the judge cannot see. The console's own figures are
at body size on a frame where the legibility floor is 2% of frame height, so the voice is the only
channel that can deliver a readable quantity. And review 1 finding 5 named the cost exactly: four
seconds of frozen frame over a number the voice will not name is "an unexplained red flag in the exact
place the video stops moving".

**Why that case does not win.** Its two costs have already been paid elsewhere. The hold is now two
seconds, not four (`CHOREOGRAPHY.md` shot 4), and the label is named on screen at 0:49 by the lower
third `the console's own tag: [UNVALIDATED]`. What is left of the objection is the magnitude, and the
beat answers it definitionally instead, which is the stronger move: a definition survives cross
examination, a figure invites arithmetic the video has no time to do.

**If he overrules, this is the only defensible form.** Not the amount, the ratio, and it must be
spoken over shot 4 with its record's own face on the same frame: "fifteen per cent over face, which is
exactly its cap." 10 words, 4.8 s. It is 1,200,000,000 x 1.15 and it re-computes by hand from what the
frame prints, which is `build-state-matrix.md` §4 item 9. A judge will not compare it to 1.25 SOL
because it is not an amount and because it is said over a frame printing face 1.20, while 1.25 is said
over a card printing face 1.00 and 2,500 basis points. The cost is 4.8 s, and it has to come out of
beat 1 or the fee clause, because there is no slack anywhere else.

---

## 4. The hook

**Is 19.7 s for beat 1 too long before the product does anything on screen? No, and the number the
argument rests on is wrong.**

First the defect. `SCRIPT.md` beat 1 says: "the demo signal in the one compliant 2:00 winner arrives
at 3.9 s". No such winner exists.

- The 3.9 s figure is from `winner-video-research.md` §2.2, and the row it comes from is
  VectorizePDFQA, which §1.2 measures at **3:06**, sixty-six seconds over the cap that
  `inputs/rules-verified-2026-11-08.md` §1 treats as an eligibility rule rather than a preference.
  §1.2 even flags it: "two MLH winners exceed MLH's own 2:00 rule (3:06 and 4:10)".
- The compliant 2:00 winner is Firekit at exactly 2:00, and its transcript has no "demo", "let me
  show" or "here's" utterance at all, so its demo signal is unmeasured.

So under either reading the sentence is false: the video with the 3.9 s signal is not compliant, and
the compliant one has no measured signal. The research's own summary sentence in §2.2 ("In the
compliant 2-minute videos the demo signal is inside the first four seconds") inherits the same error.
**This is a citation error, not a rejected decision.** The decision it was used to defend, product
first and no market statistic, stands on §3 (8 of 8 name the product or event inside ten seconds, 0 of
8 open with a statistic) and does not need 3.9 s.

**What that leaves.** There is no measured constraint on how long the opening runs, only on what it
contains by ten seconds. Ours contains the product name at 2.9 s, the word "demo" at 3.8 s, and the
event name at 7.2 s. That is inside the only norm with a measurement behind it.

**Two of the three times in that sentence also do not reproduce, and one of them matters.** At 125 wpm
one spoken word is 0.48 s, so inside beat 1: `SeatPass` completes at 2.9 s, `my demo` at 3.8 s,
`Solana` at 6.7 s and `Hackathon` at 7.2 s. **4.8 s corresponds to no word in the sentence**; it is
the end of "the", the word immediately before the event name begins. And the function clause begins
after 29 spoken words, at **13.9 s**, not at 13 s. That matters, because the sentence reads "the
function at 0:13 ... inside the ten-second window", and 13.9 is not inside ten. The claim that
survives is weaker and sufficient: product and event inside ten seconds, function inside fifteen.

One consequence in the script's favour: the word "demo" lands at 3.8 s, so even against the mis-cited
3.9 s figure this opening complies.

**So what should the first eight seconds contain?** They already contain what the measurements ask for,
and the exposure is not 0 to 8, it is 8 to 14. Enumerated, with the frame:

| Time | Frame | Voice |
|---|---|---|
| 0.0 to 2.9 | ticket page from the top, the app's own data-source note legible inside 3 s | "I'm NAME, and this is SeatPass" |
| 2.9 to 7.2 | same frame, one slow scroll, synthetic plate up | "my demo for the MLH Solana Hackathon" (the word "demo" at 3.8 s) |
| 7.2 to 13.9 | ownership trail arrives | the problem |
| 13.9 to 19.7 | price path | the function and the cap |

The only change I would make inside beat 1 is wording, section 2, 1b, and only if it is paid for. The
alternative, deleting the problem sentence to bring the function to 7.2 s, gains 6.7 s and costs the
antecedent for "that resale record". **Not recommended.**

---

## 5. What is missing

Ranked by how much it would move a score, with the word cost, because every one of them needs seconds
that do not exist.

**1. The quote committed to the chain, before it mattered. Highest ceiling, highest cost.**
`build-state-matrix.md` §4 ranks the memo transaction fifth-strongest and says it "dates the number
before the sales"; it is the only place in the project where the engine's output is bound to a public
ledger before the outcome, and it is the closest thing to a "clever technique" the entry has for the
Technology criterion, which currently rests on a program refusing a price. Nothing in the script
touches it. 19 words, 9.1 s: *"The quote was committed to devnet in a memo, with its hash and the
engine version, before anything moved."* It cannot be added inside 2:00 without cutting the fee clause,
which is exactly the 19 words it costs. Also the riskiest item here for a deadline: it is a new claim
no review has audited, and it points a judge at the artefact that carries the 130,000,000 gap.

**2. Design has no spoken carrier, and the record closes the obvious one.** One of the four criteria
gets no words at all: nothing in the script says anything a judge would score as Design. The natural
fix, naming the rebuilt interface, is forbidden (`build-state-matrix.md` §3 row 22). What is left is
true: the console is this repository's own surface, it is on screen for 44 seconds across four shots
(shots 4, 5, 6 and 9), and no sentence describes it as designed. 16 words, 7.7 s: *"This is the organiser's console: one number, its
arithmetic, and the list of what it refuses."* Note this is the only item on the list that adds a
criterion rather than strengthening one, which is why it is second and not first.

**3. The deployed program's scope.** The script says a program is deployed, shows it refusing, and
never says it checks the cap and nothing else. §3 row 13 has the permitted sentence:
*"The deployed program does the cap check."* 7 words, 3.4 s, and it costs nothing in truth because it
is the narrow version the record insists on. It does not raise a score. It protects the strongest beat
from the one over-read its own frame invites, which is worth more than a score at judging time.

**4. Learning rests on one sentence that the script itself offers to cut.** "If he cannot defend the
Token-2022 sentence, cut it" is in `SCRIPT.md` under beat 5 and repeated in `OPEN-DECISIONS.md` V7.
That is a quarter of the score depending on four seconds of one clause and the operator's confidence.
The missing thing is not a sentence, it is redundancy: the refusals in beat 3 are also Learning
evidence (the floor/ask distinction is the most interesting thing the team learned about this market),
and the beat does not claim them as such. Zero words available. Nothing to add, which is why it is
fourth.

**5. The refusal taxonomy.** The console prints six refusals, each with the missing observation beside
it, and the voice names two. That is deliberate and right (`REVIEWS.md` round 4, item 2). But the
*existence* of a taxonomy, six named gaps rather than a general apology, is the strongest evidence the
engine is doing something specific, and it is invisible to a judge who cannot read 15 px type.
9 words, 4.3 s: *"Six questions the record cannot answer, refused by name."* Risk: the row count comes from the
store, so it moves if the store does, and `build-state-matrix.md` C4 is a standing warning about
quoting counts that move.

**One thing that looks missing and is forbidden.** The programme's second required output is how value
moves over the remaining horizon. Nothing in the script says it, and a future pass may be tempted to
add it. It should not: the band is a declared width around a level, not a path, and any sentence about
a forecast over the horizon runs into §3 rows 1, 3, 9 and 18 at once.

---

## Ranked shortlist

Ordered by value per second. Counts are computed; 1 word = 0.48 s at 125 wpm.

### 1. Beat 2: give the record a time axis

- **Before:** `Every resale is a transaction, with a price and a wallet.`
- **After:** `Every resale is a transaction: a price, a wallet, a timestamp.`
- **Word delta:** 0 written, 0 spoken. **Seconds:** 0.0.
- **Evidence:** the ownership trail's rows carry dates and the fixture ticket was chosen for its dated
  row (`CHOREOGRAPHY.md` shot 1); `AGENTS.md` names the price path and time between hops as the ledger's
  advantage over scraped data.
- **Risk:** three items without a final "and" reads slightly clipped. Beat 2 is the least dense beat
  measured, so the 3 extra syllables are affordable.

### 2. Beat 5: say the mechanism, not the effect

- **Before:** `A Token-2022 fee takes a whole one-unit ticket, so no fee ships, we measured that.`
- **After:** `A Token-2022 fee rounds up to the whole ticket, so no fee ships. That is measured.`
- **Word delta:** +1 written, 0 spoken. **Seconds:** 0.0. Crude vowel-group count of the clause falls
  24 to 21.
- **Evidence:** `build-state-matrix.md` §4 item 8, the fee calculation ceils, so one base unit at any
  rate above zero yields one. This is the entry's only Learning sentence and it is the densest beat.
- **Risk:** "rounds up" invites "to what?", which "the whole ticket" answers. No claim changes.

### 3. Beat 4: give "the record" a subject

- **Before:** `The record: face one SOL, cap twenty five hundred basis points.`
- **After:** `The record it checks: face one SOL, cap twenty five hundred basis points.`
- **Word delta:** +2 written, +2 spoken. **Seconds:** +1.0.
- **Evidence:** `SCRIPT.md` beat 4 correction 3 (face and cap are record parameters, not program
  properties); `build-state-matrix.md` B2. The same noun already means the transaction history at 0:16
  ("that resale record") and is used as a verb at 1:01, so by 1:11.6 the listener has been given two
  objects for one word.
- **Risk:** 1.0 s on the beat that already has the most words, and "it checks" reads like paperwork.

### 4. Beat 3: make the floor a transaction

- **Before:** `... the highest price this tier has seen.`
- **After:** `... the highest price anyone has paid in this tier.`
- **Word delta:** +2 written, +2 spoken. **Seconds:** +1.0.
- **Evidence:** the record's basis field is a sale count ("12 sales, 9 at the ceiling"), not an ask
  count, and beat 2 has just asserted that every resale is a transaction.
- **Risk:** "anyone" invites "who paid?", on a frame whose wallets are generated. The plate is on the
  frame. Do not take this and item 5 together.

### 5. Beat 1: name the output

- **Before:** `SeatPass prices from that resale record, and the chain caps the markup.`
- **After:** `SeatPass sets the primary price from that resale record, and the chain caps the markup.`
- **Word delta:** +3 written, +3 spoken. **Seconds:** +1.4.
- **Evidence:** review 1 Q7 and finding 1, the judge's one-sentence summary; "primary" otherwise arrives
  cold at 0:48 against a frame labelled `Recommended primary price`.
- **Risk:** the largest single cost here, the verb "prices" is stronger than the periphrasis, and it
  lands on the beat with the least measured justification for its length. Take it only if the read is
  fast. Do not take it with item 4.

### 6. Beat 3: use the console's own word

- **Before:** `... the highest price this tier has seen.`
- **After:** `... the highest price this tier has recorded.`
- **Word delta:** 0 written, 0 spoken. **Seconds:** about +0.6, in syllables.
- **Evidence:** the page's own sentence is "the highest recorded price in this tier", so the voice and
  the frame would share a vocabulary. Marginal, and it does not fix the referent problem that item 4
  fixes.
- **Risk:** pushes beat 3 to the top of the measured syllable range, and "seen" is warmer. **This is
  the one item on the list I would drop.** It is here because it is free on the clock, not because it
  earns its place. It also occupies the same slot as item 4, so the two are alternatives, not
  additions.

### The totals

| Set | Written | Spoken | Runtime @125 | Pace floor |
|---|---|---|---|---|
| current | 221 | 227 | 1:55.0 | 119.6 wpm |
| items 1 and 2 | 222 | 227 | 1:55.0 | 119.6 wpm |
| **items 1, 2, 3 (recommended)** | **224** | **229** | **1:56.0** | **120.6 wpm** |
| items 1 to 4 | 226 | 231 | 1:57.0 | 121.7 wpm |
| items 1 to 5 | 229 | 234 | 1:58.4 | 123.3 wpm |

**Recommended: items 1, 2 and 3.** Three changes, +1.0 s, 1:56.0, pace floor 120.6 wpm, which is
inside 2:00 and inside the 0 to 7 seconds-under band the three compliant winners establish, and it
raises the required read by exactly 1 wpm. Everything else in this document is either free on the
clock and not worth it (item 6), or worth it and paid for with pace (items 4 and 5).

**If the read comes in fast, add item 4 and not item 5.** Item 4 strengthens the beat that has to make
an unfitted number defensible, which review 1 finding 4 read as an excuse rather than as rigour. Item
5 strengthens the beat that is already the longest and the least justified by measurement.

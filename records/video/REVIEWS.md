# The three review rounds, and what happened to each finding

Three reviews, by three agents that did not write the script, run in parallel at 07:45Z on
08 November and each reading the package independently. Their full reports are `review-1-flow.md`,
`review-2-honesty.md` and `review-3-cap-and-feasibility.md` in this directory.

| Review | Remit | Findings | Blockers |
|---|---|---|---|
| 1 | narrative, flow, pacing, the judge's one-sentence summary | 15 | 1 |
| 2 | every claim against the project's own record and the live cluster | 14 | 2 |
| 3 | the 2:00 cap measured, and whether each shot is recordable | 16 | 6 majors |

Two of the three re-measured the chain themselves rather than trusting the record; review 3
re-measured the console by rendering its payload without a server, and the frontend by running
its typecheck. Where a review and this package disagreed, the review's measurement won, and the
package was rewritten.

## What changed because of them

**The script went from 229 to 225 written words, and three of its five beats were rewritten.**

1. **The product's function was missing until 0:43.** A judge could say what world SeatPass
   lives in but not what it does, which costs `Design` and `Completion` — two of four equally
   weighted criteria. Beat 1 now says it at 0:13.
2. **"This is not." was spoken over a frame of fixture counts.** The console's `[DEVNET]` slot
   sits on a page that still prints `12 resales`, `8 events in the store` and a `[FIXTURE]` tag.
   Now: "This signature is not." One word, and it is the one thing the plate promises.
3. **"A transfer at 1.25 SOL executes" implied money moved.** It did not: one token of a
   0-decimal mint, a 5,000-lamport fee, no SOL transfer, and the record says it was the publish
   script's boundary test. Now: "A test transfer priced at 1.25 SOL executes."
4. **One reason was given for two refusals, and it was wrong for the upper bound.** The cap
   hides the top; no asking prices kill the probability. Both are now said, and all six refusal
   rows are required in frame.
5. **The close ended on a prior-work disclaimer.** The clause moved to beat 2 beside the other
   provenance statement, and the last line is now the thing the judge just watched.
6. **"Never learns what the seat resells for" was false.** The organiser's screen *is* the resale
   record. Now: "then learns from resale what it was worth", which is the actual problem.
7. **The badge switch was inaudible.** A 20 px plate changing one word under an unrelated
   sentence is not an argument. The switch is now spoken on the frame it happens: "Everything
   before this was generated. This signature is not."
8. **Shot 9 carried a DEVNET plate over a fixture frame.** It carries SYNTHETIC, and the plate
   switches back.
9. **The plate said `REAL TRANSACTION` where nothing could be tested.** It now says `SIGNATURE
   RESOLVES`, which is the test.

**The choreography was re-cut against the new script, and five things were measured that were
previously assumed.**

10. **The fixture strip and the `[EXACT]` ceiling line cannot share a 1080 frame** — 1201 px
    apart at 100% zoom. The console is now recorded at 85%.
11. **The console's `What the engine refuses` panel prints six rows, not three.** All six are
    required, because the frame must not be narrower than the claim.
12. **The `[SIMULATED] 0 arms shown` panel ends 15 px above the chain slot**, and the submission
    pack forbids it on any frame. The scroll offset is now specified.
13. **`chain.state` is not the pre-roll flag.** It stays `verified` for any instant; the flag
    that flips is `matchesCurrentQuote`. Both the check and the two-command way to run it
    without a server are in the choreography.
14. **The ticket to shoot is `tkt_00077`**, the only fixture ticket with a transfer dated inside
    the event window, and one of the few that is not badged `Listed for resale`.
15. **The frontend's served bundle is not the rebuilt tree.** At 07:49Z the tree typechecked
    clean over 277 files while the server still answered with the pre-rebuild bundle, which
    carries `Enforced on-chain`, four `tx` links onto signatures that exist on no cluster, and a
    `Mock data` banner the pack forbids. Shot 1 is now conditional on what the server returns.

**The timing was rewritten twice.**

16. An earlier table added 4 s of holds to a 3 s card and printed the wrong total, then declared
    the plan over the cap on the strength of its own arithmetic error. Review 3 recomputed every
    cell: the shot boundaries agreed to 0.06 s, and the error was in the summary rows.
17. `wc -w` counts `MLH`, `Token-2022` and `one-unit` as one word each; spoken, they are three,
    four and two. The script is now 225 written and 230 spoken, so the pace floor is **122 wpm**,
    not the 119 an earlier header claimed.

## What was rejected, and why

- **A caption track of four lower thirds was rated TASTE by review 1.** It is in
  `CHOREOGRAPHY.md` §0.1, and round 5's production pass argued it should be a full caption line
  rather than four takeaway lines. That is now what the choreography specifies.
- **Review 1 proposed dropping "What is not built, we do not show" and "That record is the
  product".** Both were dropped. It proposed keeping the end card to 3 s; the card is 7 s,
  because the URL needs to be readable and the last 3 s are silent anyway.
- **Review 2 proposed restoring the full synthetic sentence to the voice (+3 words).** Not
  taken: the plate plus "labelled here" is the label, and the three words were spent on the
  function sentence instead. `CHOREOGRAPHY.md` no longer claims the sentence is spoken or
  printed anywhere it is not.
- **Review 3 proposed moving the two signature cards later so the closing line lands on them.**
  Not taken: the cards belong to the devnet beat, and the closing line refers to the refusal as
  a category, not to a frame. Instead the repeated "two transactions on devnet" sentence was cut.

## What the reviews agreed on

All three, independently:

- the order is right — product first, because every measured winner names the product inside ten
  seconds and none opens with a market statistic;
- the devnet pair is the right climax, because it is the only claim a stranger can check without
  trusting the repository;
- the honest-limitations instinct is right and the first draft over-served it;
- the mean risk in the package was copy and framing, not the surface choice, so nothing needed a
  re-shoot.

## What none of them could settle

- Whether a judge watches muted. No measurement exists; the burned caption line is the hedge,
  and the uploaded track is for the judge who goes looking.
- Whether the rebuilt frontend will be the bundle that is serving at capture time. That is
  decision **V3** in `OPEN-DECISIONS.md` and it is the operator's.
- Whether the read lands at 121 wpm or faster. That is rehearsal pass 2.

---

## Round 4 — the confirmation pass, and what it caught

A fourth agent, also fresh, was asked to verify that the dispositions above actually landed and to
recompute every number. It found the fixes applied, and then found that applying them had left the
four documents disagreeing with each other in thirteen places, because each fix had been made
against a different revision.

The ones that mattered, and what was done:

| Contradiction | Now |
|---|---|
| word count stated as 220, 221, 226, 227 and 229 in different files | **225 written, 230 spoken**, in all five after round 6 |
| end card given as 4.0 s, 4.1 s and 7.0 s | **4.1 s**, from 1:52.4 to 1:56.5 |
| the badge switch stated at 1:02.9 and at 1:03.9 | **1:03.9**, and back at 1:32.7 |
| beat 2 ending at 0:43.7 in the choreography and 0:44.7 in the script | **0:44.7** |
| the choreography quoting a superseded line ("this record has seen") | **"this tier has seen"** |
| the end card described as three lines while rendering four | **four** |
| the plate described as 22 px with a squared left edge, matching neither asset | **20 px**; only the Devnet plate has the squared edge |
| `ADMITTED` / `REFUSED` in caps in the docs, mixed case on the card | **uppercase on the card** |
| card plates reading `real transaction` while the overlay reads `signature resolves` | **`signature resolves` on both** |

Two findings were genuine collisions between two correct fixes, and both were resolved in favour of
the rule that protects the judge:

1. **The 2% legibility floor and an 85% zoom could not both hold.** The zoom was introduced to fit the
   fixture strip and the `[EXACT]` line into one frame; at 85% the type falls under the floor the
   other review demanded. Resolution: no zoom, a 1280 CSS px viewport at 2x scale, and shot 4 becomes
   a slow scroll that opens on the strip and arrives on the number. Both rules hold, and the shot
   gains the movement it was missing.
2. **"Three refusal rows" became six.** The panel prints six whether or not the shot wants them, and
   naming two of them in the voice while framing three would have made the frame narrower than the
   claim. All six are required.

Three further items from round 4 were applied after it reported:

- **The read sheet in `REHEARSAL.md` still carried the pre-fix beat 4** — "This is not." and "A
  transfer at one point two five SOL executes" — which are the two sentences review 2 called
  blockers. It is the only artefact a person actually performs, so it was the one place a fix
  could be claimed everywhere and absent where it counts. The read sheet is now word-for-word the
  script, verified beat by beat by normalising both and comparing the word lists: 39/52/38/58/34,
  all five matching.
- **The 85% zoom was removed** in favour of a scroll (see D1 above), and the legibility floor kept.
- **`REVIEWS.md`'s own numbers** (220 words, a 7 s card) were brought in line with the script.

That is the value of a fourth pass: the first three found what was wrong with the script, and the
fourth found what the fixes had done to each other - including to the page a person reads aloud.

---

## Round 5 — the improvement pass, and what survived

A fifth agent was asked not to re-check truth but to find better wording, better order and a better
allocation of the 115 seconds, with evidence. Its report is `inputs/script-improvements.md`. Three of
its findings mattered.

**Taken, both word-neutral or nearly so:**

1. Beat 2's first sentence becomes `Every resale is a transaction: a price, a wallet, a timestamp.`
   Same word count. It adds the time axis, which is the thing the ledger has that scraped data does
   not, and the frame is showing dated trail rows while it is said.
2. Beat 5 says the mechanism rather than the effect: `A Token-2022 fee rounds up to the whole ticket,
   so no fee ships. That is measured.` One word longer, and it is the sentence a judge may ask about,
   so "rounds up" is the defensible version of "takes".

**Taken as a correction, not a preference:** the script's justification for opening on the product
cited a 3.9 s demo signal from "the one compliant 2:00 winner". There is no such measurement: the 3.9 s
figure belongs to a 3:06 entry, which is over the cap, and the compliant 2:00 winner has no measured
demo signal at all. The claim is now the narrower one the research supports (product or event named
inside ten seconds in 8 of 8), and the measured times of this script at 125 wpm replace it.

**Rejected, with the reason recorded:**

- *Speak a number in beat 3.* The report argues the digit string is identical in both records, so it
  cannot be disambiguated by ear, and the page that would qualify it is the page that disowns it. The
  only defensible form it offers is the ratio, not the amount: "fifteen per cent over face, which is
  exactly its cap", 4.8 s, paid for out of beat 1. Not taken at 1:56.5 with nothing spare, but it is the
  version to use if the operator overrules.
- *Give "the record" a subject in beat 4* ("the ticket's record"). One word and 0.5 s, and it does
  fix a genuine double meaning. Held for the operator's read: if he stumbles on that line, this is
  the fix.
- *Add the memo transaction* (the quote committed to devnet before anything moved). The report ranks it
  as the highest-ceiling addition and the riskiest, at 9.1 s, and it points a judge at the artefact
  that carries the 130,000,000-lamport gap. Not taken inside 2:00.
- *Add a Design sentence* for the console. The one true version is forbidden by the prior-work rule
  and the rest would be narration.


---

## Round 6 - the operator review, applied

**Provenance, and it was a correction of fact, not of tone.** `the interface is theirs, the pricing is
ours` was deleted everywhere: SCRIPT.md, BRIEF.md, the read sheet in REHEARSAL.md, the draft .srt,
DELIVERY.md, and inputs/build-state-matrix.md, which now records the correction instead of the claim.
It reads `they are ours, built this weekend`, which the git dates support: every file under the
frontend was first written 2026-11-06 23:24Z, inside the window that opened 17:00Z, and the rebuild is
committed. The end card is unchanged.

**Stale build, resolved by building.** :3000 was measured serving the pre-rebuild bundle: one
occurrence each of Custody trail, Enforced on-chain, Every transfer is recorded on-chain and a Mock
data banner, and zero of the rebuilt strings. A copy of the committed tree was built and served; it
returns Ownership trail, BUNDLED MOCK DATA and Open the listing form, with zero occurrences of any of
the three false lines. Shots 1-3 are recordable from the rebuilt build; Fallback B is not needed. The
frontend working tree was clean, so the build went into a copy rather than their tree.

**The starred score, deleted.** This event runs MLH own flow with a description field and a top-three
ranking. The four claims now also go in the submission description, in the video order, and DELIVERY
section 4 carries that text. SUBMISSION-PACK section 2.4 was not used because it still says nothing is
deployed.

**The pace sample, relabelled.** Seven videos, not twelve: five MLH 2024 and two Chainlink 2020,
machine-transcript word counts over total runtime, median 99 wpm. The reason for 225 words is stated
plainly: it fits 2:00 at a normal read.

**Plates, unified.** One size, 22 px, 2.04 percent of a 1080-tall frame, in the overlay and on the
cards, one Devnet string in both, and the scale written into REHEARSAL.md and DELIVERY.md. Everything
before this was generated became Every number before this was generated.

**Counts, corrected.** 225 written, 230 spoken, everywhere one is stated.

**Small additions, applied.** The admitted card carries the block time beside the slot
(2026-11-08T00:50:06Z) and both cards carry the no-SOL line; beat 5 opens with The cap is enforced;
shot 1 is a static frame instead of a 200 px scroll that could not reach the price path; the Explorer
rule is cited as two general rules with the SYN-mint line marked as the narrow one. The bytecode hash
was not published: it needs two cluster reads and is recorded as undone rather than done badly.

**The consequence.** Three net written words added, so the file is 1:56.5 and the pace floor is 122
wpm. Both inside the cap. If 1:55.0 exactly matters, No marketplace, no checkout (4 words, 1.9 s) is
the cut, and the prize research says it buys nothing.

**Two files outside this tree still carry the old provenance sentence** and were not edited here:
records/SUBMISSION-PACK.md section 2.8 and records/STATE-OF-PROJECT.md. They belong to the session
that owns them; the exact replacement text is in the board note.

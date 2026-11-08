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

**The script went from 229 to 221 written words, and three of its five beats were rewritten.**

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
    four and two. The script is 220 written and 226 spoken, so the pace floor is **120 wpm**,
    not the 119 an earlier header claimed.

## What was rejected, and why

- **A caption track of four lower thirds was rated TASTE by review 1.** It is in
  `CHOREOGRAPHY.md` §0.1 as an optional layer, because it is cheap, reversible, and makes the
  argument survive a muted judge.
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

- Whether a judge watches muted. No measurement exists; the lower thirds are the hedge.
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
| word count stated as 220, 221, 226, 227 and 229 in different files | **221 written, 227 spoken**, in all four |
| end card given as 4.0 s, 4.1 s and 7.0 s | **4.1 s**, from 1:50.9 to 1:55.0 |
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
fourth found what the fixes had done to each other — including to the page a person reads aloud.

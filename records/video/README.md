# The SeatPass submission video package

**For:** the MLH Solana Hackathon, digital, 6–8 November 2026. Submissions close
**18:00Z on 8 November** (`inputs/rules-verified-2026-11-08.md` §3).

**What this is:** everything needed to record a 2:00 demo video and defend every frame of it. 221 written words, 227 spoken, 1:55.0 at the recommended pace.
Read `SCRIPT.md` first if you are recording; read this page first if you are reviewing.

## The files, in the order they matter

| File | What it is | Read it when |
|---|---|---|
| `SCRIPT.md` | the final script, 221 words, five beats, with the timing arithmetic | before anything else |
| `CHOREOGRAPHY.md` | every shot: timecode, surface, URL, what moves, what must be legible, and the badge on each frame | while setting up a take |
| `REHEARSAL.md` | five passes, four failure drills, the read sheet, and what this machine can and cannot record | the day of |
| `OPEN-DECISIONS.md` | the seven things that are his and not a file's | now, in order |
| `COLLISIONS-AND-STATE.md` | what was in flux when this was written, and the two design collisions that shaped the plan | when a screen looks different from the plan |
| `assets/cards.html` | the three cards and the two badges, rendered and measured at 1920×1080 | before the first take |
| `inputs/` | the evidence base: rules, winners, build state, frontend inventory | when you want to know why |
| `REVIEWS.md` | what the three review rounds found, what was applied, and what was rejected | when deciding whether to trust it |
| `reviews/` | the four full review reports, by agents that did not write the script | when you want the evidence behind a change |

## The argument the video makes

Four claims, in this order, and nothing else:

1. **The record is the product.** Every resale is a transaction with a price and a wallet, so
   a ticket has a price path and an event has a price distribution.
2. **The price is derived from that record, and the engine refuses what the record cannot
   identify.** A floor, not a forecast; no upper bound; no sale probability.
3. **The cap is enforced by a program, and the enforcement is public.** One transfer at the
   cap executes; one lamport over is refused with error 6010; both signatures are on screen
   and in the description.
4. **What is not built is named.** No marketplace, no checkout, no fitted model, and the
   artist fee is out for a measured mechanism reason.

Claim 3 is the only part a stranger can verify without trusting this repository
(`inputs/build-state-matrix.md` §4). That is why it gets the most seconds.

## Two rules this package follows that are easy to get wrong

- **Nothing synthetic is presented as real.** The app runs on generated fixtures, so every
  app frame carries a SYNTHETIC badge and the voice says it once, while the numbers are on
  screen. The badge switches to DEVNET exactly once, at the first real transaction, and the
  switch is the argument.
- **The cap is 2:00 and it is a rule, not a norm.** Verified verbatim from the publisher, not
  inherited from a note in this repository. An over-length video is ineligible, not weaker.

## What was deliberately not done

- **No terminal and no Solana Explorer page on any frame**, per the submission pack. The
  signatures are rendered as cards instead, and the same two strings go in the submission
  description so they stay checkable.
- **No chart animation of the trading swarm.** The swarm is synthetic by construction, and
  animating it invites exactly the inference the record forbids. The generated charts exist
  and are labelled; they are a fallback, not a beat.
- **No team slide, no market-size figure, no music.** The rules say pitch quality is not
  judged and every one of these displaces a demonstration.
- **No claim about the model's accuracy**, because nothing is fitted and no out-of-sample
  score exists.

## Where the numbers came from

Every figure that appears on screen or in the voice is traceable to one file:

| Figure | Source |
|---|---|
| the two signatures, slots, 1,250,000,000 and 1,250,000,001 lamports, 6010, the program id | `records/devnet-artefacts.json` |
| face 1.000 SOL, cap 2,500 bps, the admitted/refused boundary | same file, `transfers.acceptedAtCap` and `transfers.refusedOverCap` |
| the console's `[EXACT]`, `[UNVALIDATED]` and refusal lines | `ticketpath/console/page.py`, `ticketpath/core/labels.py` |
| the app's screens, figures and defects | `inputs/frontend-inventory.md` |
| the 2:00 rule and the 18:00Z close | `inputs/rules-verified-2026-11-08.md` |
| the speaking-rate and structure norms | `inputs/winner-video-research.md` |
| what may not be said | `inputs/build-state-matrix.md` §3 |

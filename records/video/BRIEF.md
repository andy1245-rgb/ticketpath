# The brief: how this video is made, and the script to review

**For:** the operator, 2026-11-08. **Status:** script frozen for his review; two improvement
research passes running in the background.
**Hard cap:** 2:00 (published rule). **Target:** 1:56.5. **Words:** 225 written, 230 spoken.

---

## Part 1 — What the video has to do

It is judged by MLH's four criteria, equally weighted: **Technology, Design, Completion,
Learning**. The video is a demo, not a pitch, and pitch quality is explicitly not judged. The
Solana partner page tells a judge to confirm the project uses Solana and to ask for "the relevant
code, configuration, transaction, deployed program, or other appropriate evidence". This event uses
MLH's own submission flow, not Devpost: projects go through the Challenges page, and MLH's
recommended method is a top-three ranking rather than a starred score. So the video is not the only
place an argument can land. The submission description carries the same four claims in the same
order, and `DELIVERY.md` §4 has it written out and ready to paste.

Four claims, in this order, and nothing else:

1. **The record is the product.** Every resale is a transaction with a price and a wallet, so a
   ticket has a price path and an event has a distribution.
2. **The price comes from that record, and the engine refuses what the record cannot identify.** A
   floor, not a forecast. No upper bound, no sale probability.
3. **The cap is enforced by a program, on devnet, and the enforcement is public.** One transfer at
   the cap executes, one lamport over is refused with error 6010, both signatures on screen.
4. **What is not built is named.** No marketplace, no checkout, no fitted model, and the artist
   fee is out for a measured mechanism reason.

Claim 3 is the only thing a stranger can verify without trusting the repository, so it gets the
most seconds (27.8).

## Part 2 — The honesty system, because it shapes every frame

Two plates, never both on one frame:

- **`SYNTHETIC FIXTURES`** on every frame whose numbers are generated fixture data.
- **`DEVNET · REAL TRANSACTION · SIGNATURE RESOLVES`** on the three frames that carry a real
  signature.

The switch happens once, at 1:03.9, and the voice says it there: "Everything before this was
generated. This signature is not." It switches back at 1:32.7, because the closing frames show
fixture numbers again and no signature.

**Never said, and each has a file behind it:** any accuracy or error figure (nothing is fitted);
"validated on devnet" about the trading swarm (it ran locally); "the forecast was scored
afterwards"; "every resale is recorded on chain" (the deployed program keeps no hop record and
settles nothing); "marketplace", "buy", "checkout"; the cap being set per event or per region; and
the 1.38 SOL recommendation is never spoken, because the record it comes from and the devnet
record are two different tickets.

## Part 3 — The shots, with the clock

| # | In | Out | Surface | What it proves |
|---|---|---|---|---|
| 1 | 0:00.0 | 0:19.7 | app, ticket page, from the top | the product exists and the app labels itself |
| 2 | 0:19.7 | 0:31.7 | app, ownership trail | a ticket has a price path and a custody history |
| 3 | 0:31.7 | 0:44.7 | app, organiser resale record | an event has a distribution, not a price |
| 4 | 0:45.7 | 0:54.8 | console, ceiling and recommendation | the engine computes under a declared cap |
| 5 | 0:53.8 | 1:02.9 | console, what it refuses | it declines in six named ways and says why |
| 6 | 1:03.9 | 1:11.6 | console, `[DEVNET]` slot | a real artefact, recorded at a real instant |
| 7 | 1:11.6 | 1:21.7 | card, ADMITTED | a transfer at exactly the cap
| 8 | 1:21.7 | 1:31.7 | card, REFUSED | the same transfer one lamport higher, refused 6010 |
| 9 | 1:32.7 | 1:50.9 | console, refusals held | what is not built, named |
| 10 | 1:50.9 | 1:55.0 | end card | name, dates, repo URL |

Two one-second holds, at 0:44.7 and 1:31.7. No music, no team slide, no market-size figure, no
terminal and no Explorer page on any frame.

## Part 4 — The pace, and why the word count is low

At 125 words per minute this is 1:56.5. It is inside 2:00 from **122 wpm** upward. The sample
behind that pace is seven videos, not twelve: five MLH winners from 2024 and two Chainlink winners
from 2020, word counts from machine transcripts over total runtime, median **99 wpm**. Those are
auto-caption counts, so they undercount and the real rates are somewhat higher. The plain reason
the script is 225 words rather than 280 is that 225 fits 2:00 at a normal read and 280 does not.

The picture will be cut to the operator's measured read, not the other way round: one timed read,
then the shot boundaries move to match his voice.

## Part 5 — Production route

1. **Operator:** one timed read of the script, stopwatch only. Report the elapsed time.
2. **This session:** build the silent 1920×1080 picture lock at that pace, every shot on its
   second, both plates baked in, cards included. Measured capability: a 1080p VP9 webm across
   multiple origins in one continuous file.
3. **Operator and teammate:** play the picture fullscreen with headphones, narrate over it,
   record screen and mic in one pass. Same room, same microphone, one clap for sync.
4. **Operator:** check the exported file reads 2:00 or less, check the first ten seconds name the
   MLH Solana Hackathon, publish it public.

**What this machine cannot do:** record audio, encode mp4, or upload. The join is the operator's.

## Part 6 — Fallbacks

- If the rebuilt frontend cannot be served, shots 1 to 3 come from the console and the
  already-labelled generated charts. The argument survives; the product's face does not.
- If the console will not run, its frames can be rendered from the payload without a server, which
  has been tested.
- If a click lands on a 404, restart the take rather than cut around it.

---

# Part 7 — The script, for review

Read as written. `NAME` is his own name. Beat 4 is the teammate's voice.

**BEAT 1 — 0:00.0 to 0:19.7 — 39 words — his voice**

> I'm NAME, and this is SeatPass, our demo for the MLH Solana Hackathon. An organiser sets one
> face value, then learns from resale what it was worth. SeatPass prices from that resale record,
> and the chain caps the markup.

**BEAT 2 — 0:19.7 to 0:43.7 — 50 words — his voice**

> Every resale is a transaction: a price, a wallet, a timestamp. One ticket becomes a path: issued
> at face, resold, each hop carrying its price. Across an event, that is enough to price the next
> one. These screens run on generated fixtures, labelled here; they are ours, built this weekend.

**BEAT 3 — 0:45.7 to 1:03.9 — 38 words — his voice**

> The console recommends a primary price as a floor, not a forecast: the highest price this tier
> has seen. It refuses an upper bound and a sale probability: the cap hides the top, and nothing
> recorded a listing.

**BEAT 4 — 1:02.9 to 1:31.2 — 59 words — teammate's voice**

> Every number before this was generated. This signature is not. This program is deployed on
> Solana devnet. The record: face one SOL, cap twenty five hundred basis points. A test transfer
> priced at one point two five SOL executes. One lamport higher, and the program refuses it, error
> six zero one zero. The chain refuses it, not the app.

**BEAT 5 — 1:32.2 to 1:52.4 — 39 words — his voice**

> The cap is enforced. No marketplace, no checkout. The model is unfitted, and labelled so. A
> Token-2022 fee rounds up to the whole ticket, so no fee ships. That is measured. That chain
> refusal is the feature. Thank you.

**END CARD — 1:50.9 to 1:55.0**

```
SeatPass
Pricing from the resale record. Capped on chain.
Pricing layer built at the MLH Solana Hackathon · 6-8 November 2026
github.com/andy1245-rgb/ticketpath
```

---

## Part 8 — What to look for as you read it

Five questions, and they are the ones I cannot answer for him:

1. **Does beat 1 sound like you?** It is the only place you introduce yourself, and it now states
   what the product does at 0:13 rather than 0:43. If the wording is not how you would say it, say
   so and I will rewrite it in your register.
2. **Is beat 4 the right beat for your teammate?** It is the beat about what was built. If you
   would rather take the chain and give him the number, say so; the timing does not change.
3. **Does beat 3 leave you wanting a number?** It deliberately does not speak a price. If you think
   a judge needs to hear one, there is a version with one and I will show you the risk with it.
4. **Is beat 5 too much of a list?** Four limitations in 18 seconds. I would keep all four; the
   alternative is to cut the Token-2022 line and gain four seconds.
5. **Would you say "our demo" or name your teammate?** "And I'm NAME2" costs three words and moves
   the pace floor from 120 to 122 words per minute, still inside the cap.

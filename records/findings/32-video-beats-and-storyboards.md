# 32 — Video beats and two 2:00 storyboards: what exists per beat, what the swarm data can honestly show, and what a video-design run would have to decide

**Date:** 2026-11-08. **Event:** MLH Solana Hackathon, partnered, online, 2026-11-06 17:00Z to
2026-11-08 18:00Z. **Deadlines:** initial submission Sunday 15:00Z (10:00 ET), hacking ends 16:45Z
(11:45 ET), platform close 18:00Z.

**Status: planning input, nothing decided.** This file records a planning readout produced before any
video was designed. No beat below is chosen, no storyboard below is adopted, no timing below is
committed, and no file in the tree was changed to make any of it true. It exists so that a later run
that *does* design the video starts from a checked inventory instead of from memory.

**Provenance.** The source is the video-beats readout, a planning document held outside this repository
and not cited by path. It is the whole of it: the per-beat inventory, the survey of what the swarm data
can truthfully show, the video constraints, the two 2:00 storyboards, the risks and the
recommendation. Where the readout quoted another file in this repository, that file is named here so a
reader can follow it; where the readout gave its own view, it is labelled as such.

**Labels, used as the readout used them.** **HARD RULE** — a rule of this event, high confidence, not
advice. **GUIDANCE** — a recommendation from an organiser or a norm read off past winners, medium
confidence, and in one case in direct conflict with itself. **MEASURED** — a named file, artefact or
dataset in this tree says it. **BUILT / PARTLY BUILT / IDEA** — the build state of the thing a beat
would show. **ESTIMATE** — a cost guessed from the work's shape, not timed. **INFERENCE** — reasoning,
not a finding. **UNVERIFIED** — exists only where nobody outside this machine can check it.

---

## 1. What exists versus what does not, per beat

### Beat 1 — the refusal (a scalper hits the cap on chain). BUILT, with one nuance that matters.

The on-chain refusal is real on a public cluster. `records/devnet-artefacts.json` holds the at-cap
transfer `E5RCrLwW…pJf` (1,250,000,000 lamports, slot 519845933) and the one-lamport-over refusal
`22dqSri…e79` (slot 519846008, `custom program error 0x177a`, 6010). Both were re-fetched from devnet
and are written up with their program log lines in `records/STATE-OF-PROJECT.md` §A2.

The nuance: that pair came from the **publish script's boundary test, not from an agent**. The
*scalper agent* being refused with its own signature exists only on a **local** validator —
`records/findings/31-trading-swarm-harness-design.md` and the dataset
`.swarm-runs/sw20261108T041005Zc9f3-evt_live-SYNTHETIC.jsonl` (three refused rows, 1.27 / 1.28 / 1.29
SOL, error 6010, signature and slot each, `hop_index: null`). Those rows are **UNVERIFIED** by anyone
outside this machine.

### Beat 2 — the loop (publish → enforce → score). TWO LEGS BUILT, THE THIRD IS AN IDEA.

- **Publish: BUILT.** Tx `2Lx6cbo…ZMGCPZ`, slot 519845921, memo
  `ticketpath:quote:q-18f4ec73dd8d8fd1:<sha256>`, `recommendedLamports 1380000000`,
  `modelVersion engine-2026-11-07`. The console renders it `verified` for exactly that pinned state
  (`records/STATE-OF-PROJECT.md` §A3).
- **Enforce: BUILT** — beat 1 above.
- **Forecast scored afterwards: NOT BUILT. IDEA ONLY.** It is idea 2 in `records/findings/29-idea-portfolio.md`
  §4.2, at 3–4 h **ESTIMATE**. The record is explicit that the outcome is not on chain and that the
  scorer is us. Compounding it: the model is **not fitted at all** (`records/BUILD-SPEC-NIGHT.md` A17,
  `records/D-model-registry.md`), so there is no out-of-sample score to show even if the leg were built.

### Beat 3 — flip tax / artist fee. IDEAS ONLY.

No `TransferFeeConfig` exists anywhere in `ticketpath/`, `tools/` or `programs/`. The artist fee is
`records/findings/29-idea-portfolio.md` §4.7 at 2–3 h; the flip tax is §5.4 at 5–7 h; both **ESTIMATE**.
What is established is a **fact, not a build**: fees follow the token, hooks follow the mint, a
marketplace follows the venue (§6 F2), and the flip tax is the only rule here that survives a side
payment.

### Beat 4 — region segue. IDEA ONLY, and the record says so in those words.

`records/F-decision-log.md` Q4: "nothing is decided and nothing is built". There is no jurisdiction
field in the ticket record, and the wallet-region field currently never populates
(`ticketpath/adapters/ledger_adapter.py:359-361`).

What does exist is the two-mode mechanism pair — one mint at `cap_bps 2500`, one at 65535 — demonstrated
twice (`records/findings/31-trading-swarm-harness-design.md`, "The two modes"). That is a **mode
switch, not a geography feature**, and presenting it as geography would be an overclaim.

### Beat 5 — animated stats from the swarm. DATA EXISTS, THE ANIMATION DOES NOT.

No chart, SVG or plotting code exists in `tools/` or `ticketpath/`.
`market_swarm/datasets.py::summarise` already emits counts by status, action, agent and mode, refusal
rate per mode, and min / p50 / p90 prices. That is **enough to drive a chart and nothing to drive it
with yet**.

---

## 2. What the swarm data can truthfully show

**What actually ran.** On a local validator, against the real `cap_hook`: four agents (b1, h1, s1, g1),
four rounds, one event per dataset.

| dataset | rows | ok | refused | skipped | note |
|---|---|---|---|---|---|
| capped | 10 | 6 | 3 | 1 | |
| monitored | 11 | 9 | 0 | 2 | the scalper's 1,270,000,000 ask executing |

In simulation (`example-run.json`, nine agents, two events, twelve rounds): 106 rows, ok 64 / refused 4 /
skipped 38; capped ok 32 / skipped 15 / refused 4; monitored ok 32 / skipped 23; above +2500 bps:
capped 4 refused and 4 skipped, monitored 3 ok and 21 skipped.

Totals across both: **20 local-validator actions, 106 simulated rows, 7 refusals, 4 distinct agents on
chain.**

**Charts that are honest.**

- Refusal count by mode (4 versus 0).
- Executed price path per mode — every row carries `round`, `price_lamports`, `markup_bps`,
  `ceiling_lamports`.
- Scalper outcome strip: three escalating asks refused under the cap, the same ask executed under the
  maximum.
- Markup distribution per mode.

Animated as bars and a price line, that is the whole honest surface.

**Label it, on screen.** File names already say `SYNTHETIC`; every row carries `synthetic: true`; the
dataset header carries a disclaimer. The sentence to put on screen verbatim:
_Generated by agents against a local validator or in simulation. This is NOT evidence of real market
pricing._ Plus a standing corner badge: **SYNTHETIC · 4 agents · 4 rounds · local validator.**

**Dishonest, do not animate.**

- Any inference about real tickets, markups or demand.
- "The cap reduced scalping by X%" — the four simulated refusals are an artefact of seeded policies.
- Any accuracy or forecast-error number: nothing is fitted and no out-of-sample score exists.
- "Validated on devnet": the swarm's devnet path is code-complete and untested (finding 31).
- Reading `skipped` as refusal: most skips are censoring, bids that never met an ask.
- Calling monitored mode "where resale is legal": Q4 is open.

---

## 3. Video constraints

**HARD RULE, high confidence.** The video is ≤ 2:00, created that weekend, names the hackathon in the
opening, and is public for ever — finding 27 §3 item 3, quoted from MLH's standard rules via finding 17
§3.7. This is the rule for this event, not advice about it.

**GUIDANCE, medium confidence, and it conflicts with itself.** MLH recommends two minutes and four
minutes per project; the same page also says "3 minutes per team". The conflict is recorded in finding
27 §1.5 and is unresolved there. The mapping of a four-minute slot onto a 2:00 video is finding 27's own
reading and is labelled ASSERTED in that file. See §4 below, "Correction recorded".

**Judge reality.** The judge's screen is **UNKNOWN** for this platform. It is documented for Devpost:
an emailed link, one submission at a time, 1–5 stars per criterion, no free text (finding 27 §1.4). The
video is therefore the only place an argument lands.

**Winner durations, MEASURED** (finding 27 §2.2): 1:57, 2:18, 1:04, 5:38. Two minutes is a strong norm,
not a gate.

**Craft.** No slide decks; a screencast, not a marketing film; a visible clock in the capture; 280
spoken words at 140 wpm (finding 27 §5.0). Separately, `records/SUBMISSION-PACK.md` §1.4 forbids a
terminal window or an Explorer page on any frame — which collides with validator footage, and finding 27
§4.2 names that collision as the operator's to settle, not the file's.

---

## 4. Two storyboards, 2:00 each

Both are options. Neither is chosen. Both are written to the same 2:00 ceiling the hard rule imposes.

### Option 1 — spine: "the refusal"

The rule is the subject; everything else qualifies it.

| time | beat |
|---|---|
| 0:00–0:08 | console top; hackathon and product named; one sentence |
| 0:08–0:30 | the scalper's three escalating asks refused, dataset rows in frame, badge SYNTHETIC · local validator |
| 0:30–0:48 | the devnet pair: admitted at 1,250,000,000, refused at 1,250,000,001, signature and slot on screen; spoken as "this pair is our publish script's boundary test; the agent run is local" |
| 0:48–1:08 | the loop: the quote memo, 1.38 SOL published at a slot, then the same cap refusing |
| 1:08–1:22 | two mints, 2500 versus 65535, one line: "same ask, two modes; region policy is a design, not built" |
| 1:22–1:38 | animated stats: 4 refusals versus 0, the price paths diverging |
| 1:38–1:50 | flip tax card, numbers on screen, labelled DESIGN not run |
| 1:50–2:00 | end card |

**Needs built first:** the chart/animation, 1–2 h **ESTIMATE**; devnet state re-rehearsed, 0.25–1 h
**ESTIMATE**. Nothing else.

### Option 2 — spine: "one ask, two chains"

The comparison is the subject; the refusal is the reveal.

| time | beat |
|---|---|
| 0:00–0:10 | open |
| 0:10–0:28 | the ask staged at 1.27 SOL; record and staged price visible |
| 0:28–0:50 | the same ask refused 6010 with signature on the capped mint, executed and recorded on the monitored mint |
| 0:50–1:06 | the two price paths diverge, animated side by side |
| 1:06–1:24 | the numbers: 4 refusals versus 0, asks above cap 8 versus 24, executed p50 per mode |
| 1:24–1:42 | the loop: the published number and the cap that enforces it |
| 1:42–1:54 | region one-liner |
| 1:54–2:00 | flip tax card, end card |

**Needs built first:** the same chart work, plus a two-mint side-by-side render — 2–3 h **ESTIMATE**.
And both mint ids are local, so neither is checkable by a judge.

---

## 5. Risks

**Too many ideas.** Five beats in 120 seconds is 24 seconds each, and MLH tells judges to discount the
framing that five beats implies; finding 27 §2.5 names the narrated tour as the failure mode. The region
beat is the weakest of the five and costs the most explanation per second it gets.

**Overclaiming.** The single most dangerous frame is "the model's forecast was scored afterwards" — the
leg that does not exist and the one that sounds best. Second: showing fee or flip-tax numbers as if they
had been run.

**Memo-program mismatch.** The publish leg is an SPL memo transaction carrying a hash of ours, not an
instruction of our own. Say: "the quote was committed in a memo, the cap is our program."
`records/findings/29-idea-portfolio.md` §12 source 7 also records that the memo program's repository now
ships a rewrite under a different id, so a judge who follows the link may find a different program than
the one named.

**Public-safety.** `python3 tools/public_safety.py check --tracked` read 64 hits in 9 tracked files, every
one under `records/`, and zero in `market_swarm/`. Do not put record screens on camera.

**Recommendation, and the readout labelled it as its own:** Option 1, with the flip-tax beat cut to eight
seconds or dropped, the region beat reduced to one spoken line, and the loop narrated as two legs rather
than three. Cheapest honest path, strongest artefact first, and it keeps the refusal inside the first
thirty seconds.

---

## Correction recorded

An earlier estimate in chat put the video at **3 to 4 minutes**. That was wrong.

The **HARD RULE for this event is a 2:00 maximum video**, high confidence, per finding 27 §3 item 3 as
quoted from MLH's standard rules via finding 17 §3.7. The 3-to-4-minute figures are **GUIDANCE** — the slot
lengths MLH recommends per project, and the same page that carries them also says "3 minutes per team".
They are in conflict with the hard rule and with each other, and finding 27 §1.5 records the conflict
without resolving it. Where the two collide, the 2:00 ceiling governs and every storyboard in this file
is written to it.

Nothing in this file should be read as a four-minute plan, and no beat was costed or timed against four
minutes.

---

## Operator direction so far (2026-11-08)

Recorded, not decided. These are constraints and preferences as stated; the video-design run inherits
them but is free to say where one of them cannot hold.

- **One video, not a series.** It combines the refusal, the loop, the flip tax / artist fee ideas, a
  region segue, and animated swarm stats. That is the five-beat set in §1, and §5 flags the arithmetic.
- **The cap is intended to be set by event.** He is not certain of this. It is to be decided later, and
  nothing on screen may present per-event cap selection as settled or as built.
- **A voiceover is probable, not decided.** If it happens, the 280-word budget at 140 wpm is the bound.
- **The app holds the tickets.** Decision **D9** in `records/F-decision-log.md`: the app is the custodian,
  every resale goes through it, users cannot contact each other, and the price on a resale is the app's
  own input control. Only that paragraph is decided; the consequence block in D9 is class D reasoning read
  off it, and no artefact may cite it as a finding about a market.
- **The passport / airline-ticket idea is dropped.** Not to be revived in the video.
- **Region stays a segue, not a feature.** Per §1 beat 4, nothing is built there and Q4 is open.

---

## Open decisions for the video-design run

Each of these is a decision, not a task. The run should put the options, pick nothing on his behalf, and
come back.

1. **Option 1 versus Option 2 versus something else.** The readout recommended Option 1 and labelled the
   recommendation its own. It is not adopted.
2. **Which beats stay.** Five beats in 120 seconds is 24 seconds each. The region beat is the weakest per
   second of explanation it costs; the flip-tax beat is the most dangerous if shown as anything other than
   a design. Cutting to four, or three, is on the table.
3. **Whether to build the forecast-scoring leg.** About 3–4 h **ESTIMATE**, and the model is unfitted, so
   the score would be thin or would not exist. Building it buys a beat that the record currently says must
   not be claimed.
4. **The terminal / Explorer-frames rule against showing validator footage.** `records/SUBMISSION-PACK.md`
   §1.4 forbids a terminal or an Explorer page on any frame. The strongest evidence for the refusal is
   dataset rows and transaction signatures, which is exactly that kind of surface. Finding 27 §4.2 names
   it as the operator's collision. Options include: obey and show styled rows instead; show the Explorer
   anyway and accept the rule breach; or keep the surface off screen and put the signature in the
   description. This one needs his call.
5. **Narration style.** Voiceover or captions only; how much is spoken versus shown; whether the SYNTHETIC
   disclaimer is spoken, on screen, or both. A voiceover constrains the word budget and the pace of every
   beat.
6. **Cap scope.** Whether the video says the cap is set per event, per region, or globally — and it cannot
   say per event as settled while that is undecided.
7. **Memo-program wording.** The exact sentence that keeps the publish leg honest: the quote is committed
   in a memo, the cap is our program, and the memo program a judge reaches from a link may not be the one
   named.

---

## What the later run should produce

The deliverable of the video-design run, in full, so it can be checked for completeness rather than
argued about afterwards:

1. **A final storyboard with second-by-second timings**, totalling ≤ 2:00, with the clock in the capture
   accounted for.
2. **A shot list** — every shot, what is on screen, what is typed or clicked to get there, and the state
   it must be in before recording starts.
3. **The exact on-screen SYNTHETIC wording**, verbatim and final, plus the corner badge text and where it
   sits on every frame that carries data.
4. **A list of code and chart assets that must exist first** — the chart/animation, any render for the
   two-mint comparison if that option survives, and the state rehearsal — each with an ESTIMATE and a note
   on whether it is a build or a re-run.
5. **A script of at most ~280 spoken words**, at 140 wpm, with the beats it maps onto, and marked where a
   line must not be said because the thing it describes is not built.

The run should carry this file's labels forward and keep the built / partly built / idea distinction per
beat. Anything it cannot show honestly it should mark as unshowable rather than soften.

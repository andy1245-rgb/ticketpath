# Rehearsal plan

**The one rule this plan enforces:** the length that matters is the length of the exported
file, not the length of the plan. Every pass below ends in a measurement, and a pass that
cannot be measured has not happened.

The event closes at **18:00Z on 8 November** and the video must be *created* before then
(`inputs/rules-verified-2026-11-08.md` §3). Times below are offsets from the moment
recording starts, not clock times, because the clock is his to choose.

---

## 1. What this machine can and cannot do — measured, not assumed

Probed on 2026-11-08 between 07:32Z and 07:35Z.

| Thing | State | Consequence |
|---|---|---|
| Playwright + full Chromium, outside this repository | **present**; a scripted 1280×720 capture produced a real `.webm` at 07:32Z | this box can render and record page states headlessly |
| `ffmpeg` on `PATH` | **absent** | no transcoding on this box |
| The `ffmpeg` Playwright bundles | **webm/VP9 in, webm out only**; `--enable-muxer` lists `webm` and `image2`, `--enable-encoder` lists `libvpx_vp9` and `png`; a webm→mp4 copy at 07:35Z failed with "Unable to choose an output format" | **no `.mp4`, and no audio muxing, on this box** |
| `arecord`, `sox`, `OBS` | **absent** | **no voice can be recorded here** |

So the plan splits in two, and this is the honest version of it:

- **The cards and the page states can be captured here**, silently, and verified frame by
  frame. That is what the asset and layout checks below use.
- **The narrated video has to be recorded on his machine**, or the voice has to be recorded
  somewhere else and muxed by a toolchain this box does not have. That is decision **V1** in
  `OPEN-DECISIONS.md`, and it is the only decision in this package that can stop the video
  from existing at all.

It is not a large risk if it is taken early. It is a fatal one if it is discovered at
17:30Z.

---

## 2. Zero-cost checks that need no camera

Do these first; each is two minutes and each one has already been run once, so a second run
is a comparison rather than a hope.

**2.1 The cards render and fit.** `assets/cards.html` at 1920×1080, captured with the
headless browser. Measured at 07:55Z: `scrollHeight` equals `clientHeight` (1080) on all
three cards, no element extends past the card box, and the 87- and 88-character signatures
fit on one line at 1404 px with no wrap. The two badge plates are captured **clipped to the
plate** (760×64 CSS px) at 2× device scale, so the edit places a tight PNG and needs no alpha
keying. Re-run it after any text edit:

```bash
# from the repository root; writes only into a scratch directory
node /tmp/vid/shotcards.mjs      # see §2.2 for what it does
```

**2.2 What that script is.** It opens each card, measures overflow in the DOM, prints a JSON
line per card, and writes a PNG per card and a clipped PNG per badge. The measurement print
is the point: a card that overflows shows as `scrollH > clientH` or a non-empty `over` array
before anyone looks at a picture.

**2.3 The two signatures still resolve.** Before every take, not after:

```bash
curl -s https://api.devnet.solana.com -X POST -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getTransaction",
       "params":["E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf",
                 {"encoding":"json","maxSupportedTransactionVersion":0}]}' | head -c 400
```

Expect `"err": null` for the admitted signature and `"Custom": 6010` for
`22dqSri…7jKe79`. If the cluster is unreachable, the cards are still correct and the video
is still recordable; the *claim* in beat 4 is what a judge checks, and it is checked against
the cluster, not against us.

**2.4 The console renders the pinned state, without a server.** The console was not serving at
07:49Z (connection refused), and a server is not needed to check the frames. Both are cheap:

```bash
# the payload the URL builds
python3 tools/guidance.py --event evt_syn_02 --tier tier_stg_general \
    --as-of 2026-11-07T18:34:29.183Z --cap 1500 --tau 0.20 > /tmp/payload.json
# assert the flag that matters, not the one that describes the file
python3 -c "import json; c=json.load(open('/tmp/payload.json'))['chain']; \
    print(c['state'], c.get('matchesCurrentQuote'), c.get('signature'))"
# the page the console would serve, as HTML, for measuring element offsets
python3 -c "import json; from ticketpath.console import page; \
    print(page.render(json.load(open('/tmp/payload.json'))))" > /tmp/console.html
```

`chain.state` stays `verified` for any instant, because it describes the artefact file;
`chain.matchesCurrentQuote` is the flag that flips. Measured at an `asOf` a day earlier:
`state verified | matches False`, and no signature. Expect `verified True <signature>` for the
pinned instant. Then read `/tmp/console.html` for the strings the shots quote.

**2.5 The end-card URL resolves.** `curl -s -o /dev/null -w '%{http_code}'` against the
repository URL, and `git -C <repo> remote -v` to confirm the name on the card is the name
the remote has. A URL on screen that 404s is the one unforced error left in this video.

---

## 3. The passes

### Pass 1 — table read, no camera, no timer · 10 min

Read the five beats out loud, sitting down, twice. Do not act. The purpose is to find the
three places where the sentence fights the mouth and to fix them before they are memorised
wrong.

Mark the breath points on a printed copy, at the slashes in §5 below. If a sentence cannot be
said without a breath in the middle, it is too long and gets cut now, not in the edit.

**Output:** a printed script with breath marks and any clause struck out.

### Pass 2 — timed read, three takes · 15 min

Timer visible, screen not. Read the whole script three times and write down the elapsed time
each time. Nothing else. This is the measurement that decides whether the video fits.

| elapsed | pace | verdict |
|---|---|---|
| under 1:45 of speech | faster than 129 wpm | fine, but slow down for the take |
| 1:47 – 1:53 of speech | 120–127 wpm | **the target band** |
| 1:52 – 1:54 of speech | 119–121 wpm | survivable, and the take must not go slower |
| over 1:54 of speech | slower than 119 wpm | failed take: cut beat 5's Token-2022 clause and re-time |

**The ceiling is 1:54 of speech, whatever the word count.** Two seconds of holds and four seconds
of card come on top, so a stopwatch past 1:54 is a failed take, not a slow one. Two earlier
versions of this table admitted reads that fail the cap: the first band went to 1:58, which is
2:04 with the holds and the card. Speech time is the stopwatch on the read, not the finished
video.

**Why this pass exists at all:** measured against twelve named winners, the median speaking
rate is 99 wpm and the mean 115 (`inputs/winner-video-research.md` §4.1). A first read from a
script almost always lands slower than the read you intend, so the number to be afraid of is
"too slow", not "too fast".

### Pass 3 — walk the room, no recording · 20 min

Every click and every scroll in `CHOREOGRAPHY.md`, done three times in a row, with no
recording and no mouse pointer visible. The purpose is that the hands stop being a risk.

Rules for this pass:
- the page arrives at the shot's start state **before** the take begins; nothing is loaded
  during a shot;
- no address bar typing on camera: bookmark the exact URLs, including both console URLs;
- no scroll that overshoots and comes back. If a shot needs 120 px, rehearse 120 px;
- the tab count stays at one. Closing a tab on camera is dead air.

**Output:** a short list of the shots that needed more than three tries. Those are the shots
to change, not to practise harder.

### Pass 4 — the takes · 40 min

Three complete takes, in order, no editing between them. Take the third unless it is visibly
worse; a fourth take is almost always worse than the third.

Then, and only then, watch all three with a stopwatch and pick on: the read, the frame, the
length. In that order of importance, because a perfect frame over a rushed read is the
failure this whole plan is built to avoid.

**Output:** three files, and the duration of each as reported by the player.

### Pass 5 — the file, not the plan · 10 min

Export. Then measure the exported file, not the timeline:

- the player's reported duration must read **2:00 or less**, and preferably 1:57 or less;
- scrub to the end: the last frame must be the end card, held, not a cut to black;
- scrub the first ten seconds: the product is on screen and the hackathon is named in the
  voice;
- check the frame has no terminal, no dock, no notification, no bookmark bar;
- check every data frame carries its badge, and the badge changes exactly once, at 1:01.5.

A video that is 2:01 is not a video that is nearly right. Re-record, or cut a clause and
re-record.

---

## 4. Failure drills — decide now, not on the day

| If this happens | Do this | Cost |
|---|---|---|
| The console will not start | Record shots 4–6 and 9 from the cards alone, and say in the submission that the console runs from the clone. Do not fake a page. | the video loses its only live-computed frame; **Fallback C** in `CHOREOGRAPHY.md` |
| The `asOf` URL renders the slot unverified | Do not record it as if it were verified. Use the URL again after checking the clock, or move to shot 7's card and let the card carry the signature. | 8 s of screen time |
| The frontend is mid-edit and unrecordable | **Fallback B**: the console and the generated charts for shots 1–3 | the product's face; the record argument survives |
| The browser renders the chart without its cap rule | Fine. It is expected: `capCeilingLamports` is never passed. Never describe a dashed line that is not on screen. | nothing |
| A click lands on a 404 | Stop, restart the take from the shot's start state. Do not cut around it: a 404 on camera is a broken product, and a cut is a lie of omission a judge may notice. | one take |
| The voice is unusable on the day | Captions only. The script is 221 words and reads as captions over the same shots; it loses the "demo, not presentation" tone but it is still a demo. | some polish, not the argument |
| The clock runs out before a full take | Publish the best complete take, and say in the description what is missing. An incomplete entry that names its gap is eligible; an unpublished one is not. | the entry's weakest version, still an entry |

---

## 5. The read sheet

Breath points at `/`. Capitalised words are the ones that carry the beat; hit those and let
the rest go.

> **1.** I'm NAME, / and this is SeatPass, / my demo for the MLH Solana Hackathon. / An
> organiser sets one FACE VALUE, / then learns from resale what it was worth. / SeatPass
> PRICES from that resale record, / and the CHAIN caps the markup.

> **2.** Every resale is a TRANSACTION, / with a price and a wallet. / One ticket becomes a
> PATH: issued at face, resold, / each hop carrying its price. / Across an event, / that is
> enough to price the next one. / These screens run on GENERATED FIXTURES, / labelled HERE; /
> the interface is theirs, the pricing is ours.

> **3.** The console recommends a PRIMARY PRICE as a floor, not a forecast: / the highest
> price this TIER has seen. / It refuses an upper bound / and a sale probability: / the cap
> hides the top, / and nothing recorded a LISTING.

> **4.** Everything before this was generated. / This SIGNATURE is not. / This program is
> DEPLOYED on Solana devnet. / The RECORD: face one SOL, / cap twenty five hundred basis
> points. / A TEST transfer / priced at one point two five SOL executes. / One LAMPORT higher, /
> and the program refuses it, / error six zero one zero. / The CHAIN refuses it, not the app.

> **5.** No marketplace, no checkout. / The model is UNFITTED, and labelled so. / A Token-2022
> fee takes a whole one-unit ticket, / so no fee ships, / we MEASURED that. / That CHAIN refusal
> is the FEATURE. / Thank you.

**The four numbers to say slowly, because a judge writes them down:** one point two five
SOL; one lamport; six zero one zero; twenty five hundred basis points.

**The two words to get right:** "floor", never "estimate" or "forecast"; and "primary
price", never just "price" — the product is an organiser's pricing decision, not a resale
valuation.

---

## 6. What must be true before the first take

1. Pass 2 measured the read inside the target band, or the cut list was applied and it was
   measured again.
2. `npm run typecheck` passes in the frontend. Measured 07:49Z: exit 0 over 277 files. That is
   not the same as "the build being served is the rebuilt one" — check what the server actually
   returns, because at 07:49Z the served bundle predated the tree that typechecked.
3. Both console URLs are bookmarked, and both render the strings the choreography quotes.
4. Both signatures resolved on devnet within the hour.
5. The cards were re-rendered after the last text edit, and the overflow measurement printed
   clean.
6. The end card's URL returns 200.
7. The recording machine has a microphone, and a five-second test recording has been played
   back. This is decision **V1** and it is checked first, because it is the only one that can
   end the video.

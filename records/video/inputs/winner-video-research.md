# How winning hackathon demo videos are actually built

Research record for the 2:00 submission video. Measured against MLH rules and winners,
Devpost-hosted winners, and Colosseum/Chainlink organiser guidance.

Written 2026-11-08. All runtimes measured on that date; a video's length can change if a
team replaces it, so re-measure before relying on a number.

Every claim below is tagged **MEASURED** (a number or a quoted sentence I read at a stated
source) or **INFERENCE** (my reading of that evidence). Section 7 collects the rules;
section 8 lists every URL with what it established.

---

## 0. Method, and what this record cannot tell you

**Runtime measurement.** The `yt-scrape` project on this machine has no working
interpreter environment (no venv, and `typer`/`rich` are not importable), so its CLI could
not be used without installing dependencies, which was outside this run's write budget. I
measured instead from YouTube's own player metadata endpoint
(`youtubei/v1/player`, the Android client that returns `videoDetails.lengthSeconds`) and,
for one Vimeo-hosted video, from Vimeo's public video metadata (`duration`). Both are the
host's own statement of the file's length, so the number is the same fact `yt-scrape`
would have printed. Project-page evidence (winner badges, embedded video ids) was read
from the raw HTML of each Devpost page.

**Transcripts.** Opening and closing analysis uses YouTube's automatic English captions
(`fmt=json3`, `tStartMs` per segment). Those are machine transcriptions: words are
sometimes mangled ("haason", "heon", "MHL"). Quotes below are verbatim from the
transcript, and where the transcript is garbled I say so rather than tidying it. Two
videos returned French-language ASR for an English video (Take&Stop, Fruity Market); their
word rates are excluded.

**What I could not measure.** I cannot watch the video, so I have no measured answer for:
face-to-camera or not, title cards, problem slides, burned-in captions, number of on-screen
words, or the exact second the working product first appears. Anything in those categories
below is either marked *unverified* with the check that would settle it, or replaced by a
measurable proxy — the second at which the narrator first says "demo"/"let me show" — and
labelled as a proxy.

**Sample.** Twelve named winners with a measured runtime (five MLH-organised, seven
Chainlink), plus one where the video is now gated. Sizes are stated per claim; "n" is the
number of videos a statement rests on.

---

## 1. DURATION

### 1.1 Caps and required lengths, from the organisers themselves

**MEASURED — MLH's rule for the digital events it hosts is a 2:00 maximum and a
mandatory opening line.** `standard-hackathon-rules.md` in the MLH policies repository,
section "MLH Digital Event Submission Rules":

> "1. We require all teams to submit a 2 minute or less demo video. Your video must be
> created the weekend of the hackathon. […] 3. Your demo video must state the name of the
> hackathon at the beginning of the video. Ex. "Hey I'm Sam and this is my demo for
> CorgiHacks.""

The same three sentences appear verbatim on the rules page of MLH's own Devpost-hosted
event, MLH's Month Long Hackathon (Jan 4 – Feb 1, 2024), which also adds: "Your code and
video must remain public post-event if you want to continue being eligible for prizes."
**Unverified for the Solana Hackathon specifically:** the event page as fetched on
2026-11-08 states dates, five prize categories and a submission count, and does not render
a video-length rule anywhere in the served HTML. Treat 2:00 as MLH's standing digital-event
rule and confirm it on that event's own rules page before the cut is locked.

**MEASURED — Colosseum (Solana hackathons) caps at 3 minutes.** "Judges have to review
hundreds of project submissions, so presentations are required to be under 3 minutes."
Colosseum also recommends Loom over a slide deck, and its cofounder describes the demo-day
format as "two-minute pitches".

**MEASURED — Chainlink's 2020–21 guidance asked for far longer.** "At the very minimum,
the video should be a 3-5 minute length clip". That is consistent with the measured
Chainlink winners below, which run 3:51 to 10:35. A cap is a property of the event, not of
"hackathon videos" — the two families differ by a factor of three.

### 1.2 Measured runtimes, twelve named winners

Ordered by event. "Runtime" is the length the host reports for the video embedded on the
winner's own project page.

| # | Project | Event, year | Prize as badged on the project page | Runtime | Runtime source (video) | Winner evidence (project page) |
|---|---|---|---|---|---|---|
| 1 | Time Tracking Application | MLH's Month Long Hackathon, 2024 | Winner, Best Use of Kintone | **1:58** (118 s) | https://www.youtube.com/watch?v=WoisN8UZmvw | https://devpost.com/software/time-tracking-application |
| 2 | Firekit | MLH's Month Long Hackathon, 2024 | Winner, Best Use of Taipy | **2:00** (120 s) | https://www.youtube.com/watch?v=KqG-XjmjKZs | https://devpost.com/software/firekit |
| 3 | Puzzlify | MLH's Month Long Hackathon, 2024 | Winner, Best Use of TinyMCE | **1:53** (113 s) | https://www.youtube.com/watch?v=QIktfom6WSk | https://devpost.com/software/puzzlify |
| 4 | VectorizePDFQA | MLH's Month Long Hackathon, 2024 | Winner, Best Use of AI in Education | **3:06** (186 s) | https://www.youtube.com/watch?v=wbDxl9Dk-SA | https://devpost.com/software/vectorizepdfqa |
| 5 | Nicotine | MLH's Month Long Hackathon, 2024 | Winner, Best Use of Auth0 | **4:10** (250 s) | https://www.youtube.com/watch?v=gneA9ItNHhY | https://devpost.com/software/nocotine |
| 6 | Firefly Adventures | MLH's Month Long Hackathon, 2024 | Winner, Most Innovative Startup Idea | **no runtime — video gated** | https://devpost.com/software/firefly-adventures | same |
| 7 | Chain Draw | Chainlink Virtual Hackathon, 2020 | Winner, Runner up | **3:52** (232 s) | https://www.youtube.com/watch?v=gBCZGyeiA0o | https://devpost.com/software/chain-draw |
| 8 | Dexcrows | Chainlink Virtual Hackathon, 2020 | Winner, ENS Prize | **10:35** (635 s) | https://www.youtube.com/watch?v=OjBR2HA8EhA | https://devpost.com/software/dexcrow |
| 9 | Rent NFT (ReNFT) | Chainlink Virtual Hackathon, 2020 | Winner, Runner up + The Graph Prize | **5:41** (341 s) | https://www.youtube.com/watch?v=KrUQ4JJYg20 | https://devpost.com/software/renft |
| 10 | Take&Stop | Chainlink Virtual Hackathon, 2020 | Winner, Gelato Prize | **5:24** (324 s) | https://www.youtube.com/watch?v=eLG5wc2aXss | https://devpost.com/software/take-stop |
| 11 | Fruity Market | Chainlink Virtual Hackathon, 2020 | Winner, Runner up | **3:51** (231 s) | https://www.youtube.com/watch?v=hlyVUyzjXPQ | https://devpost.com/software/fruity-market |
| 12 | Real Hedge | Chainlink Virtual Hackathon, 2020 | Winner, Aave Prize | **7:19** (439 s) | https://vimeo.com/462377194 | https://devpost.com/software/real-hedge |
| 13 | BoTLINK | Chainlink Fall Hackathon, 2021 | Winner, Chainlink On the Rise | **6:15** (375 s) | https://www.youtube.com/watch?v=Tymdr2j9Dug | https://devpost.com/software/botlink |

Notes on the table, stated rather than smoothed over:

- **MEASURED — two MLH winners exceed MLH's own 2:00 rule** (3:06 and 4:10), as embedded
  at retrieval time. Either the rule was not enforced, or the video was replaced after
  judging. I cannot tell which from outside; Devpost does not keep a video history.
- **MEASURED — the three MLH winners that comply sit right under the cap**: 1:58, 2:00,
  1:53. INFERENCE: at a hard cap, the observed behaviour is to land 0–7 seconds under it,
  not 30 seconds under it.
- Firefly Adventures' video would not resolve through the player endpoint (exit-equivalent
  "gated"), so it is listed as gated, not as zero-length. **Unverified.** What would settle
  it: opening the embed in a signed-in browser, or asking the team.
- The Solana winners' submitted runtimes are **unverified and, at time of writing, not
  publicly measurable.** Colosseum's own announcement names the winners — Radar 2024 Grand
  Champion Reflect, with Pregame, Txtx, Supersize, Squeeze, SvachSakthi, FXSwap and AlphaFC
  first in their tracks; Cypherpunk first prizes to Capitola, Yumi Finance and MCPay — but
  the submitted videos live on Colosseum project pages that return a login wall to an
  anonymous fetch, and Colosseum recommends Loom, which is not indexed by YouTube search.
  Searching YouTube for each of those project names with "demo/hackathon" returned no video
  whose title ties it to the named project and event. What would verify it: a signed-in
  Colosseum session, or the teams' own shared links.

---

## 2. STRUCTURE

Sample for this section: the five MLH 2024 winners and the six Chainlink winners with
usable transcripts (n = 11). Everything is from the transcript, so it is the *spoken*
structure, not the visual structure.

### 2.1 The opening second names the hackathon, then the person, then the product

**MEASURED — 4 of 5 MLH winners name the hackathon inside the first 10 seconds**, and all
four do it in the first sentence, exactly as the MLH rule asks:

- "hi um this application was created for mlh is month long haason January 2024" — Time
  Tracking Application
- "hello everyone my name is Rahul Kumar and this is a project uh demo video for my mlh
  month long heon" — VectorizePDFQA
- "hi I'm abis and this is my submission for the mlh monthlong hackathon for January 2024
  this is fire kit" — Firekit
- "hello I'm Jerry and this is our January MHL monthlong hackathon submission" — Puzzlify

The fifth, Nicotine, opens "hello we are team nicotine and we made project nicotine" and
never names the event in the first ten seconds — and still won a prize. **MEASURED.** So
the rule is real, most winners follow it, and it is not what decides the prize.

**MEASURED — no winner in the sample opens with the problem.** In all five MLH openings the
order is: greeting → self or team → event name → product name. The problem statement, where
it exists, comes after the product has been named. Chainlink's longer-form winners behave
the same way: Rent NFT opens "so this is our project renft um red ft is essentially a
protocol layer that enables peer-to-peer renting of erc 721", product first, mechanism
second.

**INFERENCE:** the first second is spent buying the judge's context ("this is a submission
for the event you are judging"), not on persuasion. That is cheap, and it is the one thing
the rules demand, so it is not in tension with the hook.

### 2.2 Time before the product is on screen

**Unverified visually.** I have no frame-level measurement, so I cannot state when the first
screenshot appears. What I can measure is when the narrator first signals the demo, which is
a lower bound on when the screen is doing the work:

| Video | First "demo / let me show / here's" utterance | Total |
|---|---|---|
| VectorizePDFQA (MLH 2024) | 3.9 s | 3:06 |
| Rent NFT (Chainlink 2020) | 58 s | 5:41 |
| Dexcrows (Chainlink 2020) | 91 s | 10:35 |

**MEASURED.** In the compliant 2-minute videos the demo signal is inside the first four
seconds; in the long 2020 Chainlink videos it is a minute or more in. **INFERENCE:** demo
onset scales with the cap — at 2:00 there is no room for a preamble, and the winners spend
none.

What would verify the visual question: sampling one frame per second from each video and
recording the first frame that is not a title/slide, or a manual watch with a stopwatch.
Neither was done here.

### 2.3 Face, title card, problem slide

**Unverified.** I have no measurement of any of the three, and I will not infer them from
speech. What would settle it: the frame-sampling check above, run over the five MLH
winners; a per-second frame index would answer all three at once.

One weak, *measured* implication: all five MLH winners speak in the first person from t=0
with a self-introduction ("I'm abis", "I'm Jerry", "my name is Rahul"), which is what a
talking-head or at least a narrator-first video sounds like. **INFERENCE**, not a visual
confirmation.

### 2.4 The ending is a plain thanks, not a call to action

**MEASURED — 4 of 5 MLH winners end on an explicit thank-you**, with no call to action, no
score, no "vote for us":

- Time Tracking Application: "…so this is our application and thank you for watching"
- VectorizePDFQA: "…this is giving me a response again yeah thank you"
- Nicotine: "…we are team nicotine thank you so much"
- Puzzlify: no thanks — it ends mid-explanation of a feature that is not running (quoted in
  §4.4)
- Firekit: transcript ends on the last feature, no thanks

The Chainlink long-form winners close the same way: Dexcrows "…you can try it out on just
gross but eth dot link thank you"; Rent NFT ends on a dashboard statistics explanation with
no sign-off.

**MEASURED:** across all 11, zero use a call to action. **INFERENCE:** the last five seconds
are not a persuasion slot in this population; spending them on a score or a plea would be
unprecedented in the sample, and the sample is what "measured norms" means here.

---

## 3. HOOKS — what actually happens in the first ten seconds

Verbatim from the automatic transcript, with the transcript's own errors left in.

**MLH's Month Long Hackathon 2024 winners (n = 5):**

1. **Time Tracking Application (1:58)** — "hi um this application was created for mlh is
   month long haason January 2024 um our team made a task time". Event, date, product noun,
   in ten seconds. No problem, no market, no team bios.
2. **Firekit (2:00)** — "hi I'm abis and this is my submission for the mlh monthlong
   hackathon for January 2024 this is fire kit fire kit is a". Name, event, product, product
   name repeated immediately.
3. **Puzzlify (1:53)** — "hello I'm Jerry and this is our January MHL monthlong hackathon
   submission in short our project aims to deliver coding challenges to people who are just
   beginning to code". Event, then a one-sentence who-it-is-for. This is the closest thing
   in the sample to a problem statement in the first ten seconds, and it is a beneficiary
   statement, not a market statistic.
4. **VectorizePDFQA (3:06)** — "hello everyone my name is Rahul Kumar and this is a project
   uh demo video for my mlh month long heon okay let me quickly demonstrate my project
   streamlit". By 4.2 s he has said "let me quickly demonstrate" and named the tool stack.
5. **Nicotine (4:10)** — "hello we are team nicotine and we made project nicotine a digital
   Heaven designed to support uplift individuals in their journey to quit smoking". The only
   one that leads with the product's purpose sentence rather than the event.

**Chainlink winners (n = 3 of the sample):**

6. **Rent NFT (5:41)** — "awesome hello everyone so this is our project renft um red ft is
   essentially a protocol layer that enables peer-to-peer renting of erc 721".
7. **Dexcrows (10:35)** — "hi in this presentation i will be introducing describes which the
   desktop team has built for the 2020 channeling academy".
8. **Chain Draw (3:52)** — **no speech at all**: the transcript is empty for the full 232
   seconds, so the opening ten seconds carry their argument in text or music only. A winner.

**MEASURED summary of the first ten seconds:** product or event named in 8 of 8 videos with
speech; an explicit personal or team identity in 4 of 8 ("my name is Rahul", "I'm abis",
"I'm Jerry", "we are team nicotine"); a problem framed as someone's difficulty in 1 of 8; a market size, a statistic, or a "the problem is worth $X" claim in 0 of 8; a joke or a
cold open in 0 of 8.

**INFERENCE:** the hook in this population is not a hook in the advertising sense. It is
orientation at speed — who is talking, which event this is for, what the thing is called —
delivered in under ten seconds so that the remaining 110 are free for the product.

---

## 4. DEMO PACING

### 4.1 Speaking rate: winners are slower than the assumed 140 wpm

Word counts are from the automatic transcript (a floor: the ASR drops some words), divided
by the measured runtime.

| Video | Runtime | Words (ASR) | wpm |
|---|---|---|---|
| Firekit (MLH 2024) | 2:00 | 150 | **75** |
| Time Tracking Application (MLH 2024) | 1:58 | 185 | **94** |
| Nicotine (MLH 2024) | 4:10 | 411 | **99** |
| VectorizePDFQA (MLH 2024) | 3:06 | 349 | **113** |
| Puzzlify (MLH 2024) | 1:53 | 353 | **187** |
| Dexcrows (Chainlink 2020) | 10:35 | 948 | **90** |
| Rent NFT (Chainlink 2020) | 5:41 | 842 | **148** |

**MEASURED.** The five MLH winners run 75–187 wpm with a median of 99; the mean of the
sample excluding the two ASR-mismatched videos is 115. **INFERENCE:** the ~280-word budget
for a 2:00 cut assumes 140 wpm, which is above every compliant MLH winner in this sample
except Puzzlify. At 99 wpm a 2:00 video carries about 200 words, not 280. Either the
budget drops to ~200 words or the delivery is faster than a typical winner's — and Puzzlify,
the fastest at 187 wpm, still won, so speed is not disqualifying. Two of the five
(75, 94) are slow enough that a viewer is reading the screen for part of the time.

Caveat: ASR undercounts, so true rates are somewhat higher than these numbers. The ordering
and the median are the finding, not the third significant figure.

### 4.2 How many features a 2:00 video carries

**Not measurable from outside** — counting features requires watching, and a "feature" is
not defined identically across projects. I will not invent a number.

What is measurable and does bear on it: MLH tells judges to weigh four criteria **equally**
— Technology, Design, Completion, Learning — and, for **Completion**, to ask "Does the hack
work? Did the team achieve everything they wanted?" **MEASURED.** **INFERENCE:** at 1-5
stars per criterion with no free text, breadth of features is worth less than the judge
being able to see one thing work end to end under the Completion star, and the 2:00 budget
is best spent proving that rather than touring five half-features.

### 4.3 Numbers: spoken, on screen, or absent

**MEASURED, two concrete instances and no general claim.** The Time Tracking Application
narrator reads a number aloud as the final beat — "he worked 120 seconds for today". In the
long Chainlink videos the numbers are narrated in passing (Dexcrows walks through exchange
mechanics verbally). I have **no measurement** of how much on-screen text carried numbers,
because that is visual. **Unverified.** What would settle it: frame sampling at 1 fps and
counting numerals per frame.

### 4.4 What winners do with a feature that is not finished

This is the strongest single finding in the file, because a winner says it out loud.

**MEASURED — Puzzlify (Winner, Best Use of TinyMCE, MLH 2024) ends its 1:53 video by
telling the viewer the app is not currently running:** "…the features are already
implemented so I I just need to get it up and running" and, before that, "if I still had a
premium trial I would definitely…". The video demos the built interface and states the
current limitation in the closing seconds. It won a prize.

**MEASURED — the organisers instruct exactly this.** MLH's standard rules, "Demos":

> "You are encouraged to present what you have done even if your hack is broken or you
> weren't able to finish. It's okay if you didn't finish your hack—that happens all the
> time! Completion is only one part of the judging criteria, so you might still do well."

and "You are strongly encouraged to present a demo of what you have built. Pitches and
presentations are discouraged. You are not judged on the quality of your pitch or the
quality of your idea."

Chainlink's version: "Even if you can't address all the points in this article, or even if
you haven't completed your project, you should still submit what you have."

**MEASURED — Colosseum's prioritisation advice is to build for the demo, not the
feature list:** "prioritize the features that allow you to create an amazing working demo on
devnet. Prioritize the features that you believe will give users an 'aha' moment". And its
required pitch contents list "How the product works (your demo)" as the last of six
elements, after team, product, motivation, market and traction.

**INFERENCE:** "unfinished" is not the risk; "unfinished and presented as finished" is. The
sample's only explicit disclosure of a non-running app is in a winning video, and none of
the sample claims a feature it does not show.

---

## 5. HONESTY PRACTICE — prototypes, mockups, synthetic data, "planned"

### 5.1 What organisers actually say

**MEASURED — MLH, rules:** all work must be done during the hackathon ("All work on a
project should be done during the period of the hackathon"), no re-use of prior code, and
for MLH-hosted digital events "You can not submit a project that includes prior work."
AI use is allowed but must be disclosed: "You must credit any tools used and be clear on what
you made and what was generated… If you do not credit your AI usage, you will be disqualified".

**MEASURED — MLH, judge-side cheating check.** MLH tells organisers to check, among other
things: "Did they start before the event?"; "Are their Timestamps over the weekend when they
run the demo in any video/screen captures?"; "(If they have a video) Was the video published
over the weekend?"; "(If they have a video) Does it mention another event? Does it mention
yours?" This is the closest thing in any organiser document to a rule about what a video may
show: the demo must be of a state that existed inside the event window, and a visible
timestamp is treated as evidence.

**MEASURED — MLH, judged on Completion.** "Does the hack work? Did the team achieve
everything they wanted?" — one of four equally weighted criteria.

**MEASURED — Chainlink, the video's job is proof:** "The video is an extremely important
part of a hackathon submission… It proves that the project is real, and that it works."

**MEASURED — Colosseum, judged on the sprint:** "while projects are judged just on the work
completed during the hackathon", and the sprint's target is "a working demo on devnet".

**MEASURED — Devpost's submission form asks for the same disclosure in text:** the
additional-details step includes "Explanation of how you improved your project during the
hackathon", and the help page instructs submitters to "check the Hackathon Rules for any
requirements regarding maximum video length".

### 5.2 The zero result: nobody writes down a mockup rule

**MEASURED ZERO.** I found **no** organiser or judge guidance that addresses mockups,
synthetic data, or placeholder content by name — not permissive, not prohibitive. Searches
for the usual phrasings ("mockups will not be judged", "not a mockup", "must be
functional") returned nothing on an MLH, Devpost, Colosseum or Chainlink page; the MLH
organiser guide pages on submissions, judging and cheating checks contain no such sentence,
nor does Colosseum's how-to-win guide or Chainlink's submission guide.

Where I looked, so a later session can extend rather than repeat it: MLH
`standard-hackathon-rules.md`; MLH organiser guide pages on judging plan, rules, cheating
check and submission portal; the MLH Month Long Hackathon Devpost rules; Devpost's
submission-steps help article; Colosseum's how-to-win guide and its current event page;
Chainlink's submission guide. URLs in §8.

**INFERENCE, and it is the operative reading for this project:** the absence of a mockup rule
does not make a mock safe. Three measured rules close around it — the video must prove the
thing is real and works (Chainlink), Completion is a scored criterion (MLH), and judges are
told to verify that what the video shows existed during the event window (MLH cheating
check). A synthetic-data screen labelled as synthetic is compatible with all three; an
unbuilt feature shown as built is not, because it fails the one thing the video is for.

**INFERENCE — what that implies concretely for a project with synthetic fixtures:** label
the data on the screen in the frame that shows it (not in a closing disclaimer the judge may
not reach), keep the label in the same shot as the numbers it qualifies, and if a feature is
not wired, either don't show it or say in one clause that it is not wired. That is what the
sample's one disclosing winner did, and it is what MLH's "present what you have done"
paragraph is inviting.

---

## 6. CAPTION AND VOICE

**MEASURED — voiceover is the norm, but not universal.** Of the 11 winners I pulled caption
tracks for, 10 carry speech from t=0. (Two more of the thirteen in §1.2 — BoTLINK and Real
Hedge — were measured for runtime only, not for captions.) One does not: **Chain Draw (3:52, Winner, Runner up,
Chainlink Virtual Hackathon 2020)** returns an empty caption track for the full runtime, so
its 232 seconds argue in text, music, or on-screen action alone — and it placed.

**MEASURED — voice is a solved problem for organisers, not a hurdle.** Chainlink's guidance
explicitly allows outsourcing it: "if you or your team aren't confident of speaking on a
recorded video, you can always reach out to the Chainlink community and ask someone to record
a scripted voiceover for you." **INFERENCE:** a synthetic or hired voice is not a
credibility risk; a silent video that hides the demo behind a slide is.

**MEASURED — speaking rates of winners: 75, 94, 99, 113 and 187 wpm** for the five MLH
winners (§4.1), against the 140 wpm the current budget assumes. **INFERENCE:** if on-screen
text is doing part of the work — and in a screencast it usually is — the spoken track can be
slower than 140 without the video feeling slow; the winners are proof. Writing to 200 words
for 2:00 is closer to measured practice than 280.

**Unverified:** whether winners burn captions into the frame, and whether any of them use
on-screen text to carry the argument in place of speech. Chain Draw is the one case where it
must have; I cannot confirm the mechanism without watching. What would settle it: frame
sampling, and checking whether the captions returned by the host were uploaded by the team
(manual captions) or auto-generated (ASR) — the endpoint exposes `kind: "asr"`, which is what
all of these were, so none of the sample has uploaded captions; that is a measured fact about
the sample, not about their burned-in text.

---

## 7. Rules distilled

| # | Rule | Tag | Source |
|---|---|---|---|
| 1 | Put the hackathon's name in the first spoken sentence, in the form "I'm X and this is my demo for Y". | MEASURED | MLH `standard-hackathon-rules.md`, digital-event rule 3; 4 of 5 MLH winners did it §2.1 |
| 2 | Land the runtime 0–7 s under the cap, not 30 s under it: the three compliant MLH winners ran 1:58, 2:00, 1:53. | MEASURED | §1.2 rows 1–3 |
| 3 | Do not open with the problem or a market statistic: 0 of 8 videos with speech did. | MEASURED | §3 |
| 4 | Name the product inside the first ten seconds. | MEASURED | §3, 8 of 8 |
| 5 | Get to the demo signal within the first ~4 seconds at a 2:00 cap. | MEASURED (proxy) | §2.2, VectorizePDFQA 3.9 s |
| 6 | Budget ~200 spoken words for 2:00, not 280: winners speak at 75–187 wpm, median 99. | MEASURED | §4.1 |
| 7 | End on a thank-you or on the last feature; do not add a call to action or a score: 0 of 11 used one. | MEASURED | §2.4 |
| 8 | Show the unfinished thing and say it is unfinished; a winner closed its video that way. | MEASURED | §4.4, Puzzlify; MLH "Demos" |
| 9 | Build for the demo, not the feature list: organisers tell teams to prioritise what produces a working demo. | MEASURED (guidance) | Colosseum how-to-win; MLH Completion criterion |
| 10 | Expect the demo to be checked as evidence of a state that existed during the event window, including visible timestamps. | MEASURED | MLH cheating-check list |
| 11 | Treat a labelled synthetic dataset as acceptable and an unlabelled one as a rule violation in spirit: no organiser writes a mockup rule, but the video's stated job is proof that the thing is real and works. | INFERENCE (from MEASURED rules) | §5.2, §8 |
| 12 | Voiceover is required in practice, not by rule: 10 of 11 winners speak from t=0, and one silent 3:52 video won anyway. | MEASURED | §6, Chain Draw |
| 13 | Length is a property of the event, not of the genre: the same population runs 1:53 at MLH and 10:35 at Chainlink 2020. | MEASURED | §1.1, §1.2 |
| 14 | Assume 2–3 features is the practical ceiling for 2:00, since four equally weighted criteria mean Completion is worth a quarter of the score and "does it work" is answered by one continuous run. | INFERENCE | §4.2, MLH criteria |
| 15 | Do not spend the hook on a personal story: 4 of 8 gave a one-line name or team identity and moved on immediately. | MEASURED (pattern) / INFERENCE (why) | §3 |

---

## 8. Sources

**Rules and organiser guidance**

- https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md — MLH's standard rules: the 2:00 digital-event video cap, "must state the name of the hackathon at the beginning", no prior work, AI disclosure, the "Demos" paragraph ("present what you have done even if your hack is broken"), and the four equally weighted judging criteria.
- https://mlh-s-month-long-hackathon.devpost.com/rules — the same video rules on a live MLH-hosted event page, plus "code and video must remain public post-event". Event dates Jan 4 – Feb 1, 2024.
- https://mlh-s-month-long-hackathon.devpost.com/project-gallery — the winner badges and project slugs used in §1.2.
- https://guide.mlh.com/general-information/judging-and-submissions/judging-plan — "we recommend having hackers submit 2 minute videos… Their video should be a demo of their hack, not a presentation."
- https://guide.mlh.com/general-information/judging-and-submissions/cheating-check — the judge-side checks: video published over the weekend, mentions another event, visible timestamps in the demo.
- https://guide.mlh.com/general-information/judging-and-submissions/rules-for-your-hackathon — organiser rule checklist, including the AI-disclosure recommendation.
- https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal — Devpost is the common submission platform at MLH events; required submission fields.
- https://help.devpost.com/article/126-know-your-submission-steps — Devpost: video must be public on YouTube or Vimeo; "check the Hackathon Rules for any requirements regarding maximum video length"; the "how you improved your project during the hackathon" field.
- https://blog.colosseum.com/how-to-win-a-colosseum-hackathon — Colosseum: "presentations are required to be under 3 minutes", "we recommend using Loom over a slide deck", the six required pitch contents, "prioritize the features that allow you to create an amazing working demo on devnet", "judged just on the work completed during the hackathon".
- https://blog.colosseum.com/announcing-the-winners-of-the-solana-radar-hackathon — named Radar 2024 winners (Reflect, Pregame, Txtx, Supersize, Squeeze, SvachSakthi, FXSwap, AlphaFC, Lexicon, Attest Protocol).
- https://blog.colosseum.com/announcing-the-winners-of-the-solana-cypherpunk-hackathon — first prizes to Capitola, Yumi Finance, MCPay.
- https://colosseum.com/worldsfair — the current Colosseum event's state (judging phase, 11,650 participants) and judge roster; its project pages are behind a login, which is why no Solana runtime could be measured.
- https://www.youtube.com/watch?v=2meLpwKi0zw — Colosseum cofounder Matt Taylor, "What It Takes to Win a Colosseum Hackathon": the presentation video is "the first thing that most judges look at"; the four things it must answer (who you are, why you are building it, why there is demand, what you did during the hackathon); demo days are "two-minute pitches".
- https://www.youtube.com/watch?v=so4AHsd8ioU — Colosseum, "How to Win a Colosseum Hackathon", the talk that accompanies the blog guide.
- https://chain.link/blog/blockchain-hackathon-tips — Chainlink: "The video… proves that the project is real, and that it works"; "3-5 minute" minimum length; "still submit what you have" if unfinished; hiring a scripted voiceover is acceptable.
- https://chainlink-hackathon.devpost.com/ — the Chainlink Virtual Hackathon event (2020) that the seven Chainlink winners in §1.2 were submitted to.
- https://www.mlh.com/events/solana-hackathon — the Solana Hackathon event page as served on 2026-11-08: dates Nov 6–8, five prize categories, 68 submissions, no video-length rule in the HTML.

**Winner project pages and videos measured in §1.2**

- https://devpost.com/software/time-tracking-application · https://www.youtube.com/watch?v=WoisN8UZmvw
- https://devpost.com/software/firekit · https://www.youtube.com/watch?v=KqG-XjmjKZs
- https://devpost.com/software/puzzlify · https://www.youtube.com/watch?v=QIktfom6WSk
- https://devpost.com/software/vectorizepdfqa · https://www.youtube.com/watch?v=wbDxl9Dk-SA
- https://devpost.com/software/nocotine · https://www.youtube.com/watch?v=gneA9ItNHhY
- https://devpost.com/software/firefly-adventures — winner badge; embedded video gated, runtime unmeasured
- https://devpost.com/software/chain-draw · https://www.youtube.com/watch?v=gBCZGyeiA0o
- https://devpost.com/software/dexcrow · https://www.youtube.com/watch?v=OjBR2HA8EhA
- https://devpost.com/software/renft · https://www.youtube.com/watch?v=KrUQ4JJYg20
- https://devpost.com/software/take-stop · https://www.youtube.com/watch?v=eLG5wc2aXss
- https://devpost.com/software/fruity-market · https://www.youtube.com/watch?v=hlyVUyzjXPQ
- https://devpost.com/software/real-hedge · https://vimeo.com/462377194
- https://devpost.com/software/botlink · https://www.youtube.com/watch?v=Tymdr2j9Dug

**Measurement surfaces used (no page, listed so the method can be repeated)**

- `youtubei/v1/player` (Android client, `videoDetails.lengthSeconds`) for runtimes; `captions.playerCaptionsTracklistRenderer` + `api/timedtext` (`fmt=json3`) for transcripts; `https://vimeo.com/api/v2/video/<id>.json` (`duration`) for the Vimeo runtime.
- Devpost project pages read as raw HTML for the embedded video id and the "Winner" badge text.
- Search: `free-search` (keyless, 7 sources) for discovery; several queries returned `degraded` or `error` verdicts (DuckDuckGo walled from this host, and a quoted-phrase query that returned a hard `error`). Those are reported as degraded coverage, not as an empty web.

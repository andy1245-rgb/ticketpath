# Verification pass on `winner-video-research.md`

Written 2026-11-08. Scope: settle every claim in `winner-video-research.md` that is
marked *Unverified* or *MEASURED ZERO*, plus every claim that restates another source
without checking it. Where a claim cannot be settled from this machine, it says so and
names the tool that would settle it.

Tags: **MEASURED** means I fetched, counted or looked at the thing in this pass and the
evidence is stated. **INFERENCE** means my reading of that evidence. A number quoted from
the record to show what was claimed is marked *as written* and is not being re-asserted.

Method this pass: YouTube's own player metadata read out of the watch page
(`ytInitialPlayerResponse`: `videoDetails.lengthSeconds`, `captions`, `storyboards`),
Vimeo's public video API, the raw HTML of the organisers' pages, and the host's
auto-generated video frames. Nothing was installed. All downloads went to a scratch
directory outside this repository, and no media or binary is committed.

**Frames: how they were obtained, and what they are not.** No downloader exists here and
the streams are token-gated, so the video body could not be fetched. What the host does
serve is its own fan-out frames: three images per video at separate points in the file,
supplied at up to 1280x720. For each of the eleven videos I fetched all three at every
size the host offered (640x480, 480x360, 320x180, 1280x720 where present), confirmed with
sha256 that the three are three different pictures and not the uploader's poster repeated,
and confirmed the pixel dimensions by parsing each JPEG's start-of-frame header. Thirty-three
distinct frames (three per video) were downloaded at up to four resolutions each, and
eighteen images were opened and looked at one by one, spread across all eleven videos. Statements below
about what is in a frame come from looking at that frame, never from a title, a description
or the uploader's chosen thumbnail. The one thing the host does not disclose is the second
of the video each frame was taken at, so every frame observation in this file is anchored to
"a frame in the body of this video", not to a timecode, and no claim here rests on a frame's
position in the timeline.

Tooling on this machine, measured with `command -v`: **no `yt-dlp`, no `youtube-dl`, no
`ffmpeg` on PATH, no `yt_dlp` Python module, no PIL, no numpy, no ImageMagick, no browser
on PATH.** An ffmpeg binary does exist inside the Playwright browser cache (build 1013,
version 7.0.1), but it is a stripped build: VP9 and matroska input, PNG output, and no
HTTP protocol, so it can only decode a file that something else has already downloaded.

---

## Verdicts

| # | Claim, as recorded | Verdict | Evidence | Tag |
|---|---|---|---|---|
| T1 | §2.2: "In the compliant 2-minute videos the demo signal is inside the first four seconds", resting on VectorizePDFQA 3.9 s; §7 rule 5 repeats it as "at a 2:00 cap" | **OUR RECORD IS WRONG** | VectorizePDFQA is 186 s (3:06). The record's own §1.2 row 4 and its §1.2 note both say 3:06 and name it as one of the two MLH winners that *exceed* the 2:00 rule. So the only video with a measured demo signal is 66 s over the cap, and the sentence that calls it compliant contradicts the table in the same file. A 2:00-cap claim now rests on n=0 | MEASURED (runtime), INFERENCE (the contradiction) |
| T1a | The 3.9 s figure itself, and §3's "By 4.2 s he has said 'let me quickly demonstrate'" | **NOT SETTLABLE HERE**, and the file disagrees with itself | 3.9 s (§2.2 table) and 4.2 s (§3 item 4) are two different times for the same utterance. Neither can be re-derived: the caption endpoint now answers HTTP 200 with a zero-byte body, even with the signed URL taken from a live player response. Settled by a human listen with a stopwatch, or `yt-dlp --write-auto-subs` with a PO-token-capable client | MEASURED (the wall), INFERENCE (the reconciliation) |
| T2 | §6: "Unverified: whether winners burn captions into the frame" | **SETTLED: yes, at least two of the eleven** | Puzzlify (MLH 2024, 113 s): a white-on-black caption band at the bottom of the frame reading "skills. So I will first demonstrate." Chain Draw (Chainlink 2020, 232 s): caption boxes on a cyan band at the bottom of the frame in all three sampled frames, e.g. "Quote retweet the tweet and @chain_draw to call the twitter bot" and "Let's check the winner, indeed he/she has retweeted the original chainlink tweet". Nine other videos showed no caption band in the frames examined | MEASURED |
| T2a | How many of the eleven burn captions, sampled every 10 s | **NOT SETTLABLE HERE** | No downloader and the video streams are token-gated: the player API returns LOGIN_REQUIRED, UNPLAYABLE or HTTP 400 across the ANDROID, IOS, ANDROID_VR, WEB and TV clients, and `adaptiveFormats` carries no `url` and no `signatureCipher`, only `serverAbrStreamingUrl`. So no bytes, so nothing for the local ffmpeg to decode. Settled by `yt-dlp` (which implements the PO-token and visitor-data handshake) plus `ffmpeg` at lowest quality, frames every 10 s | MEASURED (the block), INFERENCE (what it would take) |
| T3 | §1.2's runtimes, thirteen rows | **SETTLED: twelve of thirteen confirmed exactly, one unreachable** | Re-fetched: Time Tracking 118, Firekit 120, Puzzlify 113, VectorizePDFQA 186, Nicotine 250, Chain Draw 232, Dexcrows 635, Rent NFT 341, Take&Stop 324, Fruity Market 231, BoTLINK 375 (YouTube `lengthSeconds`); Real Hedge 439 (Vimeo `duration`, title "Real Hedge Demo"). Every number is unchanged from the table. Firefly Adventures is still unreachable: its Devpost page now returns HTTP 403 to an anonymous fetch, so its embedded video id could not even be read | MEASURED |
| T3a | "a video's length can change if a team replaces it" (§ header) | **No change found**, on the twelve that resolve | Same twelve values as recorded | MEASURED |
| T4 | §2.3, face, title card and problem slide, asked at 0, 2, 5 and 10 s | **NOT SETTLABLE at those seconds.** Partly settled at unstated timecodes | The host does not expose the timecode of its auto-generated frames, and no downloader exists, so the opening ten seconds cannot be sampled. The frames that could be obtained give this: a corner webcam with a person's face in Puzzlify and in Rent NFT; no face at all in Firekit, Time Tracking, VectorizePDFQA, Nicotine or BoTLINK; a designed slide reading "TAKE&STOP" and "Gelato / Automation / Decentralisation" in Take&Stop; a fruit-icon hero frame with the project logo and an event badge in Fruity Market; a blank page with a loading spinner in Dexcrows. Settled at the required seconds by `yt-dlp` plus `ffmpeg -ss` | MEASURED (what is visible), INFERENCE (none applied to intent) |
| T4a | §2.3's inference that first-person narration "sounds like a talking-head" | **INFERENCE, half confirmed** | Two of the eleven do show a face in a corner. Five of the frames examined show the app alone with nobody in frame. Narration-first does not imply a face | MEASURED (frames), INFERENCE (reading) |
| T5 | §4.1 speaking rates, "derived from auto-captions, which undercount", and the request to recompute against a real transcript | **NOT SETTLABLE HERE** | Every caption track on every one of the eleven videos is `kind: "asr"`. Chain Draw has no track at all. So no human transcript exists anywhere in the sample to compare against, and the ASR text itself can no longer be fetched. The record's arithmetic is at least internally consistent: each wpm in the table equals its word count over its runtime, so the table is right *given* its word counts, and the word counts are the unverified part. Settled by a human transcript or the team's script, or by any ASR with a PO token, then a word count | MEASURED (all tracks are asr), INFERENCE (arithmetic check) |
| T6 | Sentences that cite a source but do not quote it | **Listed below** | See "Citations without a quotation" | MEASURED |
| U1 | §1.1: "Unverified for the Solana Hackathon specifically … does not render a video-length rule anywhere in the served HTML" | **SETTLED: confirmed, and stronger than recorded** | The event page's data object carries `"rules":null` and `"rulesHtml":null`, so there is no rules document on the page at all. Neither "video" nor "minute" appears in its visible text. The page's only "2:00" is a time of day in the schedule ("12:00 PM"). The standing MLH digital-event cap remains the only stated 2:00 rule | MEASURED |
| U1a | §1.1: the event's "five prize categories and a submission count" | **The count has moved** | `submissionsCount` now reads 87, against the 68 *as written*. Dates unchanged: Fri Nov 6 12:00 PM to Sun Nov 8 1:00 PM EST | MEASURED |
| U2 | §1.2: Firefly Adventures, video gated, "Unverified" | **NOT SETTLABLE HERE** | Devpost returns HTTP 403 to this host for that project page, so the embedded video id cannot be recovered, and without the id the player endpoint has nothing to ask. Settled by a signed-in Devpost session or by asking the team | MEASURED |
| U3 | §1.2: "The Solana winners' submitted runtimes are unverified and, at time of writing, not publicly measurable" | **Confirmed, unchanged** | No path found to a Colosseum submission video without a login. Note this is a claim about access, not about the videos | MEASURED (the wall) |
| U4 | §2.2: "Unverified visually. I have no frame-level measurement" | **Partly settled, see T4** | Frames were obtained but not at chosen seconds | MEASURED |
| U5 | §2.2: "What would verify the visual question: sampling one frame per second … Neither was done here" | **Still not done, for the stated reason plus a new one** | The reason in the record was no measurement; the reason now is that the media cannot be fetched without a PO-token client | MEASURED |
| U6 | §2.3: "Unverified. I have no measurement of any of the three" | **Partly settled, see T4 and T4a** | Face: measured, present in two, absent in five. Title card: measured, a designed slide frame exists in Take&Stop and a hero frame in Fruity Market. Problem slide: not measured, since a slide is only a problem slide by what it says | MEASURED (the first two), INFERENCE (the third) |
| U7 | §4.2: how many features a 2:00 video carries, "Not measurable from outside" | **Confirmed not settled** | Counting features needs the full video. Frames do not answer it. Unchanged | MEASURED (the limit) |
| U8 | §4.3: "I have no measurement of how much on-screen text carried numbers … Unverified" | **SETTLED qualitatively: on-screen numerals are common** | Firekit: a table of incident sizes and discovery dates, with a "1-10 of 91" row counter. Time Tracking: a live timer reading 00:00:04, a chart with a 40/30/20/10 axis, a log of `time_amount` values. BoTLINK: a chart plotting five timestamps with a 0 to 50 axis. Take&Stop and Fruity Market: no numerals. What remains unmeasured is the count per frame, which needs 1 fps sampling | MEASURED |
| U9 | §5.2: "MEASURED ZERO. I found no organiser or judge guidance that addresses mockups, synthetic data, or placeholder content by name" | **Confirmed as a negative claim, not re-tested** | A negative over ten named pages cannot be verified by fetching pages again; only a recorded query set can. The file names where it looked but records no queries and no result strings, so the zero is not reproducible as written | MEASURED (the gap in the record) |
| U10 | §6: "whether any of them use on-screen text to carry the argument in place of speech" | **SETTLED for the one case the file named** | Chain Draw, the video with no caption track at all, carries its argument in burned-in captions across all three sampled frames. §6's "I cannot confirm the mechanism without watching" can now be resolved | MEASURED |
| U11 | §0's list: face-to-camera, title cards, problem slides, burned-in captions, on-screen word count, the second the product first appears | **Three of the six now have evidence, three do not** | Face, title card and burned-in captions: see T4, U6, T2. On-screen word count, problem-slide content and the exact second the product appears: still unmeasured | MEASURED / INFERENCE as split |
| U12 | §2.1 "4 of 5 MLH winners name the hackathon inside the first 10 seconds"; §2.4 "across all 11, zero use a call to action"; §3's counts of 8 of 8, 4 of 8, 1 of 8, 0 of 8; §6 "10 of 11 carry speech from t=0" | **Carried, not verified in this pass** | All six rest on the ASR text, which cannot be fetched any more (see T5). They may well be right. They are not verified here and should not be cited as verified until the transcript is re-obtained | MEASURED (the block) |
| U13 | §1.2's "Prize as badged on the project page" column, all thirteen rows | **Not verified in this pass** | Devpost now returns HTTP 403 to an anonymous fetch, so the badges could not be re-read. Only the runtimes were re-checked, from the video hosts, which do answer | MEASURED |

---

## The six requested checks, in detail

**1. Does the 3.9 s figure belong to a compliant 2:00 video?** No. MEASURED: the video is
186 s. §1.2 is right and §2.2's summary sentence is wrong. The sentence "In the compliant
2-minute videos the demo signal is inside the first four seconds" is not a rounding error;
it removes the only measurement the file had and replaces it with a claim about a
population of which no member was measured. §7 rule 5 inherits the error and states it as
"MEASURED (proxy)". The three videos that do comply, at 120 s, 118 s and 113 s, have no
measured demo-signal time at all. INFERENCE: the honest form of the rule is "the one video
in the sample where this was measured reached its demo at 3.9 s, and it ran 3:06, so it
says nothing about a 2:00 cut."

**2. Does any MLH winner burn captions into the frame?** Yes. MEASURED by looking at
frames: Puzzlify, an MLH 2024 winner at 113 s, burns a caption band into the frame. The
general claim "whether winners burn captions in" is therefore answered in the affirmative,
on two of eleven. MEASURED on the block: the question cannot be answered at 10 s intervals
across the sample, because there is no downloader and the streams are token-gated. The
exact tool that would settle it is `yt-dlp` plus `ffmpeg`.

**3. The runtimes.** MEASURED: twelve of thirteen confirmed to the second, unchanged.
One, Firefly Adventures, is unreachable because Devpost now refuses an anonymous fetch.

**4. Face, title card, problem slide at 0, 2, 5 and 10 s.** NOT SETTLABLE at those seconds.
MEASURED instead, at timecodes the host does not disclose: two videos show a corner webcam
with a person in it, five show the application alone, two show a designed slide or hero
frame, one shows a loading spinner on a blank page. No interpretation of intent is offered,
and the reported content is limited to what is visible.

**5. Speaking rates against a real transcript.** NOT SETTLABLE HERE. MEASURED: every
caption track in the sample is auto-generated, so no real transcript exists to compare
with. MEASURED: the record's wpm column is arithmetically consistent with its own word
counts. What that leaves unverified is the word counts, and with them the ~200-word budget
and the "ASR undercounts" premise.

**6. Citations without a quotation.** Listed below.

### Citations without a quotation

Sentences that attribute something to a source without quoting it, so a reader cannot check
it from the file:

1. §1.1, Colosseum: "Colosseum also recommends Loom over a slide deck" is paraphrased, and
   only the neighbouring sentences are quoted.
2. §1.1, the claim that the same three video rules "appear verbatim" on the MLH Month Long
   Hackathon Devpost page. The page is cited, the three sentences are not reproduced from
   it, and it now returns HTTP 403, so the claim cannot be checked at all.
3. §1.2, the "Prize as badged on the project page" column: thirteen prize labels, none
   quoted, none obtainable now.
4. §1.2 note, the Colosseum winner rosters ("Radar 2024 Grand Champion Reflect", and the
   first-prize list under Cypherpunk), restated without a quotation from either
   announcement.
5. §1.2 note, "Colosseum recommends Loom, which is not indexed by YouTube search": both
   halves are asserted, the second without a searched query or a result string.
6. §1.2 note, the YouTube search for each Solana project name, which "returned no video
   whose title ties it to the named project and event". A zero result with no recorded
   queries and no recorded verdict line.
7. §2.2's table of demo-signal times: three numbers, no transcript quoted.
8. §2.4, "across all 11, zero use a call to action": a count over eleven transcripts with
   four of them quoted.
9. §4.2, the four MLH criteria named as "Technology, Design, Completion, Learning". Only
   the Completion question is quoted.
10. §4.3, "Dexcrows walks through exchange mechanics verbally": no quotation.
11. §4.4, Colosseum's six required pitch contents, listed as team, product, motivation,
    market, traction and then the demo. Only "How the product works (your demo)" is quoted.
12. §5.1, "no re-use of prior code", restated before the quoted sentence says something
    narrower. Also "AI use is allowed but must be disclosed", where the quoted sentence is
    the disqualification clause, not the permission.
13. §5.2, the whole MEASURED ZERO, for the reason in U9.
14. §6, "Of the 11 winners I pulled caption tracks for, 10 carry speech from t=0": a count,
    no quotations, and the `kind: "asr"` claim that follows it is described rather than
    shown.
15. §0, "no venv, and `typer`/`rich` are not importable": a claim about this machine stated
    without the command output. MEASURED this pass only in the narrower sense that no
    `yt_dlp` module is importable and no downloader is on PATH.
16. §7, rules 2, 3, 4, 6, 7, 12, 13 and 15: each restates a count from §2 to §6 and inherits
    whether that count was quoted.

---

## What this changes

Only the conclusions that would move the video plan.

1. **The defended opening loses its evidence.** Rule 5 and §2.2's summary were the one
   measured justification for getting to the product inside four seconds. That measurement
   belongs to a 186 s video. The plan should keep "name the event in the first spoken
   sentence", which is verified against MLH's own rules text, and drop the four-second
   figure as a measured norm. INFERENCE: the opening is still the right shape, on rule
   grounds, not on sample grounds.

2. **Burned-in captions are now a demonstrated choice, not a risk.** An MLH winner at 113 s
   does it, and the sample's one silent video does it. §6 treated this as unknown. A plan
   that burns captions in can cite a winner rather than argue from first principles.

3. **"A silent video won anyway" is the wrong lesson.** Chain Draw is now measured to carry
   its argument in burned-in captions. What it did without was a spoken voice, not without
   words. Any reasoning that a silent cut is acceptable, or that music alone can carry a
   demo, has to go.

4. **A face is optional and uncommon, and the file should stop implying otherwise.** Two of
   eleven show a person in a corner; five of the frames examined show the app and nobody
   else. §2.3's note that first-person narration "sounds like a talking-head" should be
   retired.

5. **The word budget stays unverified.** The ~200-word target for 2:00 rests on word counts
   that cannot be reproduced and on an untested assumption that the ASR undercounts. Treat
   200 as a working constraint, not a measured norm.

6. **On-screen numerals are normal, so a screencast carrying its numbers on screen is
   consistent with the population.** Measured in three of the videos examined.

---

## Claims that must stop being repeated

Removed outright, because they are wrong or contradicted by the same file:

- "In the compliant 2-minute videos the demo signal is inside the first four seconds."
- Rule 5 as written, including its "MEASURED (proxy)" tag and its "at a 2:00 cap" wording.
- The 3.9 s figure and the 4.2 s figure, in any form, until one of them is re-measured.
  They are two values for one utterance and neither is currently reproducible.
- "two MLH winners exceed MLH's own 2:00 rule" is correct, but any sentence that then
  treats either of those two as compliant. VectorizePDFQA at 186 s is one of them.

Downgraded, because the evidence does not exist right now even though the claim may be
true. Do not cite these as MEASURED until the transcript is re-obtained:

- §2.1's 4 of 5, §2.4's 0 of 11, §3's 8 of 8, 4 of 8, 1 of 8 and 0 of 8, §6's 10 of 11,
  and every wpm in §4.1 with the 75 to 187 range, the median of 99 and the mean of 115.
- "ASR undercounts, so true rates are somewhat higher." That is an untested assumption, not
  a measurement, and the 200-word budget leans on it.
- §1.2's thirteen prize badges, and §1.2's statement that the sweep of the Solana winners
  found no video. Both were obtained through surfaces that now refuse an anonymous fetch.

Corrected numbers:

- The Solana event's submission count is 87, not the 68 *as written*. It is a live counter
  and will move again.

No longer unanswered, so stop listing them as open questions:

- Whether any winner burns captions into the frame. Yes, two of eleven.
- What mechanism Chain Draw used to argue without speech. Burned-in captions.
- Whether on-screen text carries numbers in these videos. It does, in at least three.
- Whether the MLH event page states a video-length rule. It carries no rules document at
  all.

Still legitimately open, and this pass did not close them: the opening ten seconds at
0/2/5/10 s, a per-second frame index, the on-screen word count, the count of burned-in
caption users across the sample, and a real transcript for any winner. All five need
`yt-dlp` and `ffmpeg`, or a signed-in session, which this machine does not have.

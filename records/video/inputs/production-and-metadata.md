# Production and metadata: the 20% that is not on the timeline

**Written:** 2026-11-08, between 10:08Z and 10:25Z. Every URL below was fetched in that window
with the `web-fetch` skill; every search used the `web-search` skill. Nothing here is quoted
from memory and nothing is inherited from another file in this repository without saying so.

**What this covers.** Captions, the first frame, the two voices, the title and description, the
order of operations, and the one cheap thing the measured winner sample omits. The timeline
itself is `../SCRIPT.md` and `../CHOREOGRAPHY.md` and is not re-opened here.

**Tags.** `MEASURED` means I fetched it and it says that. `MEASURED-IN-REPO` means the
measurement was made in this repository, on a date named beside it. `INFERENCE` means it
follows from measured facts and is my reading. `UNCONFIRMED` means nobody publishes it and I
could not measure it. Where a fetch failed I say so rather than filling the gap.

**Two things I could not fetch, so nothing here rests on them.** `w3.org` (the WAI captions
page and the WCAG 2.2 text) is blocked from this host through the fetch proxies; three
attempts, all refused before any content came back. So there is no WCAG 1.2.2 citation in
this file, and no claim that depends on one. Shure's own knowledge base article on two singers
sharing one microphone returned "All fallbacks failed", and Shure's recording-techniques PDF
extracted to zero characters. The audio section below therefore cites one post-production
publication and one audio-software manufacturer, and says which of its recommendations are
mine rather than theirs.

---

## 1. CAPTIONS: burned in, uploaded, or both

### What is measured

**Muted viewing costs comprehension, and it makes the viewer read.** A peer-reviewed
eye-tracking study, n = 168, three language groups, published in PLOS ONE:

> "The findings show that when watching videos without sound, viewers experienced increased
> cognitive load, along with reduced comprehension, immersion and overall enjoyment …
> the absence of sound significantly affected the viewing experience, increasing the need for
> subtitles and thus increasing the viewers' propensity to process them more thoroughly."

Source: https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0306251 (fetched
10:10Z). `MEASURED`. Note what it does not say: it does not measure how many people watch
muted, and it does not study hackathon judges.

**An uploaded caption track is off until the viewer turns it on.** YouTube's player
documentation, verbatim:

> "`cc_load_policy`: Setting the parameter's value to 1 causes closed captions to be shown by
> default, even if the user has turned captions off. The default behavior is based on user
> preference."

and, on the language parameter:

> "If you do not also set the `cc_load_policy` parameter, then captions won't display by
> default, but will display in the specified language if the user opts to turn captions on."

Source: https://developers.google.com/youtube/player_parameters (fetched 10:11Z). `MEASURED`.

**The platform that embeds the video does not set that parameter.** I read the raw HTML of a
Devpost project page for a 2026 MLH Best-Use-of-Solana winner. Its video iframe is:

```
youtube.com/embed/<id>?enablejsapi=1&hl=en_US&rel=0&start=&version=3&wmode=transparent
```

No `cc_load_policy`, and no `autoplay`. Source: https://devpost.com/software/loka-pay
(fetched 10:11Z, raw response inspected). `MEASURED`. Two consequences, both `MEASURED`
against the YouTube documentation above: the caption track is off unless the judge opts in,
and the player shows a still until the judge presses play.

**YouTube publishes auto-captions by itself, in the default language only.**

> "YouTube uses speech recognition technology to automatically create captions for your videos.
> If automatic captions are available, they'll automatically be published on the video."
> "Automatic captions will be in the video's default language only."

Source: https://support.google.com/youtube/answer/3038280?hl=en (fetched 10:09Z). `MEASURED`.
The same page documents the manual routes: **Upload a file** (`With timing` or `Without
timing`), **Auto-sync** (paste a transcript, YouTube sets the timing), and **Type manually**.
It also warns: "Transcripts are not recommended for videos that are over an hour long or have
poor audio quality", which is the only accuracy statement on that page.

**No accuracy number exists for YouTube's ASR.** `MEASURED-ABSENT` on that page. The words
this video cannot afford to have mis-heard are `lamport`, `Token-2022`, `basis points` and
`six zero one zero`; there is no published word-error rate to reason from, and I did not
measure one.

**The sample of winners has no uploaded captions.** Re-measured today, not inherited: I fetched
the watch page for seven winners from the two samples in `winner-video-research.md` §1.2 and
§2.2 and read the player's own `captionTracks` block. Six of the seven expose exactly one
track and its `kind` is `"asr"`. The seventh, SolGPU (1:57, MLH Best Use of Solana, Knight
Hacks IX), exposes no caption track at all.

| Video | Caption tracks | Kind |
|---|---|---|
| LOKA Pay | 1 | `asr` |
| BackFill | 1 | `asr` |
| Weenie Beanie | 1 | `asr` |
| SolGPU | **0** | none |
| Time Tracking Application | 1 | `asr` |
| Firekit | 1 | `asr` |
| Puzzlify | 1 | `asr` |

`MEASURED` at 10:20Z. What that establishes: **0 of 7 have a caption track a human wrote.**
What it does not establish: whether any of them burned text into the frame, which a caption
track cannot show.

**Organiser guidance on captions: `MEASURED-ABSENT` where I looked.** The MLH submission and
judging guide's full page, fetched as markdown, has no mention of captions or
accessibility of the video (https://hackdays-guide.mlh.com/run-your-event/project-submissions.md,
fetched 10:16Z). Devpost's "Know Your Submission Steps" has none either
(https://help.devpost.com/article/126-know-your-submission-steps, fetched 10:09Z). That is a
search over two pages, not over both sites.

### Does a judge watching muted get anything?

`UNCONFIRMED` for this event, in both directions. Nobody publishes whether MLH's judging view
embeds the video, autoplays it, or opens it in a new tab; `records/findings/27` §1.1 records
that MLH documents no judge-facing page at all. Nothing anywhere states a muted-viewing rate
for hackathon judges. What is confirmed is the mechanism: on the one platform whose embed I
could read, a caption the submitter uploaded is invisible until the judge clicks CC, while
text that is in the picture is visible at t=0 with no interaction.

That asymmetry is the whole argument, and it does not need a viewing statistic to hold.

### The design constraint this project already has

`../CHOREOGRAPHY.md` §0.1 already puts four lower-third lines on screen (0:49.0, 1:03.9,
1:24.0, 1:50.9) for exactly this reason, in its own words: "every takeaway in this video is
spoken, and a judge watching muted would otherwise get a scrolling ticket app and no argument."
So the caption layer is not a new layer. A burned caption track placed bottom-centre collides
with those lines, and the two badge plates sit bottom-left. The clean arrangement is that the
lower third *is* the caption line: it carries the spoken sentence while it is spoken, and the
four existing takeaway lines become what it shows in the gaps.

**What this project should do.** Burn the spoken script into the frame as the caption line and
upload the same text as a timed `.srt` after publishing, because the uploaded track is off
until a judge clicks CC and the burned line is on at t=0. Do not add a third text layer: make
the existing lower third carry the spoken sentence, and keep the badge plate clear.

---

## 2. THE FIRST FRAME: what a judge sees before pressing play

### Three different images exist, and only one of them is under the video's control

**1. The YouTube poster.** The player shows a still until playback starts; the Devpost iframe
carries no `autoplay` parameter and the parameter's documented default is `0`
(https://developers.google.com/youtube/player_parameters, fetched 10:11Z). Which still it
shows is the video's thumbnail. YouTube documents the choice, not the default frame:

> "Custom video and Shorts thumbnails let your audience view a quick snapshot of your content.
> You can choose from auto generated suggested options, or upload your own if your account is
> verified."

Source: https://support.google.com/youtube/answer/72431?hl=en (fetched 10:09Z). `MEASURED`.
**Which frame YouTube picks when nothing is uploaded is not documented**, so the first frame of
the export cannot be relied on to be the poster. That closes the open question in `../SCRIPT.md`
§1 ("Unverified in that research: whether the first *frame* should be product or title card"):
the frame and the poster are two decisions, and only the poster is guaranteed to be seen.

**2. The verification gate.** Custom thumbnails are behind account verification, and the
verification page lists them by name:

> "Once you've verified your account, you can: Upload videos longer than 15 minutes. **Add
> custom thumbnails.** Live stream. Appeal copyright claims."
> "To verify your channel, you'll be asked to enter a phone number. We'll send a verification
> code by text or voice call to that phone number."

Source: https://support.google.com/youtube/answer/171664?hl=en (fetched 10:19Z). `MEASURED`.
It is a couple of minutes of work, and it is impossible without the phone to hand.

**3. The platform's own card image.** On Devpost the project page's share preview (`og:image`)
is the project's uploaded gallery photo, not a video frame, and the video element's own
`thumbnailUrl` is `https://img.youtube.com/vi/<id>/0.jpg`, i.e. YouTube's image for that video.
Both read from the raw HTML of https://devpost.com/software/loka-pay at 10:11Z. `MEASURED`.
Devpost's form asks for that image separately: "Thumbnail image for the Project Gallery | This
should be a JPG, PNG or GIF format, 5 MB max file size. For best results, use a 3:2 ratio."
(https://help.devpost.com/article/126-know-your-submission-steps, fetched 10:09Z) `MEASURED`.

**On this event's own platform there is no thumbnail field and no video field.** The MLH form,
verbatim: "Enter the project link, project name, description, and technologies used. Add a demo
URL if the team has one." The live event page's own props carry `shortDescriptionLimit: 160`,
`galleryPath: null`, and no video or image field at all. `MEASURED` at 10:22Z on
https://www.mlh.com/events/solana-hackathon and
https://hackdays-guide.mlh.com/run-your-event/project-submissions.md. Caveat, stated rather
than smoothed: the form itself is behind sign-in, so this is the event page's public schema and
the guide's wording, not a screenshot of the form.

### What the sample actually puts there

I pulled the thumbnail image for the same seven videos and opened each one. `MEASURED`, 10:18Z.
Six serve a 1280×720 image (`maxresdefault.jpg` returns 200); Firekit returns 404 and serves
only the 480×360 default, so it has no uploaded thumbnail at all. What is on them:

| Video | The poster |
|---|---|
| LOKA Pay | **a designed card**: product name, the claim "Zero bars. Still paid.", a red badge reading "Double spend refused on chain", `error 6011 · SerialUsed`, two phone screenshots showing the success and the refusal side by side, and the product's domain |
| SolGPU | a **composed full-screen product screenshot**: the app, a wallet panel, and a line reading "Solana devnet / 4.99984 SOL" |
| Weenie Beanie | a product screenshot with a **signed-in email address visible in the corner** and a bank's logo |
| BackFill | a **cropped slide**: the headline is cut at the left edge ("eight beneficiary basket") and one callout reads "BAX ideiguged the dircnptuct, zeoi zeono investuntient weight" |
| Puzzlify | a **raw recording frame**: a `BANDICAM` overlay across the top, browser tabs, a webcam inset, and one line of large white text along the bottom edge |
| Time Tracking Application | a **desktop screenshot**: tab strip, URL bar, bookmark bar, and a "Recorded on screencapture.com" watermark |
| Firekit | a **480×360 frame caught mid-scroll**, cut off at the edge, because no thumbnail was uploaded at all |

Two things survive the table. **One of seven is a purpose-built card**; the rest are screenshots,
and the card is the exception. And **four of the seven carry something no submitter would have
chosen**: a signed-in email address, a chart with generated gibberish written on it, a
screen-recorder watermark, and a browser toolbar. All seven are prize winners, so none of this
cost them the prize. It cost them the first second.

### The strongest thing to put there, from this project's evidence

The sample's own precedent (a designed card, the product's refusal, the error code, two states
side by side) is the same shape as this entry's strongest beat, and the numbers already exist
in `records/devnet-artefacts.json`. A thumbnail that reads, at a glance, `ADMITTED 1.25 SOL` /
`REFUSED 1.250000001` / `error 6010`, with two cropped card images, makes the video's argument
before the judge has pressed play. It also satisfies the frame rules in
`records/SUBMISSION-PACK.md` §1.4 by construction, because a card is not a desktop, a terminal,
or a live service.

**What this project should do.** Verify the YouTube account by phone before the first take, and
upload a designed 1280×720 card carrying the two cards and `error 6010` rather than letting
YouTube choose a frame. Treat the video's own first frame as a separate decision, and keep it as
the product per the script.

---

## 3. AUDIO: two voices, one microphone, one room, no equipment

The sourced guidance below is from a four-part professional series on recording voiceovers at
home, and from an audio-software manufacturer's piece on room tone. The numbers are theirs.
Where I extend them to two voices on one microphone, I say `INFERENCE`.

**Levels.** Verbatim:

> "What we're aiming for is an input level for your spoken vocals that's typically between the
> -18dBFS to -4dBFS range on the Levels meter, and never goes beyond the 0dBFS mark … as this
> causes clipping and distortion."

Source: https://blog.frame.io/2022/03/10/recording-voiceovers-from-home-part-3-recording
(fetched 10:13Z). `MEASURED`.

**Distance.** Verbatim:

> "A lot of artists use the 'hang ten' hand gesture to set the distance between microphone and
> mouth (don't measure from the pop filter), or the distance of two clenched fists."

Same source. `MEASURED`. The conversion to 15 or 20 cm is mine (`INFERENCE`); the gesture is the source's,
and it is the number to hold in your head when there is no time to measure.

**The plosive fix, verbatim:** "Talking past it can reduce pops", and "Placing a pop filter
between your mouth and the microphone will diffuse this air". Same source. `MEASURED`.

**Consistency is the thing the source keeps returning to:** "voiceovers need consistency. So
use your headphones and monitor the live feed … to establish the best position relative to the
microphone, and try to stay in that area for the entire take", and "Get in position. And stay
there." Same source. `MEASURED`.

**Room tone, and why a second recording session needs it.** Room tone is "the natural noise of
your recording environment", and the practical instruction is: "it is wise to capture 30 to 60
seconds of the ambience to use as room tone. Tell everyone on set to be quiet … It will help so
much in the edit." The same piece names the exact problem this video has, because beat 4 is
read by a second person: "Oftentimes you'll get an overdub from a different studio, and the
resulting audio will sound different. A slice of room tone from the original recording's locale
can help match the two recordings." Source:
https://www.izotope.com/community/blog/basics-of-room-tone-audio-editing (fetched 10:14Z).
`MEASURED`.

### The one mistake that ruins a demo voiceover

`INFERENCE`, from the measurements above: **changing the distance or the input level between
takes, or between the two speakers.** It is the only defect in this list that no edit fixes,
because the two halves then have different amounts of room and different loudness, and the fix
is to re-record, not to process. Clipping is the louder, more obvious cousin: a take that
touches 0 dBFS is distorted at the loudest syllable and cannot be rescued.

For two voices on one microphone the practical form of the rule is: one gain setting, one
microphone position, both speakers at the same distance from it, and the microphone moved only
between sessions. `INFERENCE`. I found practitioner pages recommending an equidistant placement
between two seated hosts, but none of them was a manufacturer or a broadcaster, so it is not
cited as a fact here.

### What twenty minutes with no equipment buys

`INFERENCE` throughout, built from the sourced numbers:

1. Pick the smallest room with the most soft furniture, sit away from the wall, put the laptop
   or phone on something soft. Two minutes.
2. Plug in whatever microphone exists. Set the input so a normal sentence peaks near the
   -12 dBFS mark on the meter, well inside the sourced -18 to -4 band and nowhere near 0.
3. Record 45 seconds of silence with everyone still. That is the room tone, and it is the only
   insurance against the second speaker sounding like a different room.
4. Record a ten-second test at speaking distance, listen back on headphones, and only then
   start. If the test is thin or boomy, move half a fist closer or further and test again.
5. Record each speaker's beats in one unbroken pass, same seat, same gain. Do not ride the gain
   between lines.

**What this project should do.** Record beats 1, 2, 3 and 5 in one session and beat 4 in the
same room, same seat and same gain, with 45 seconds of room tone at the head of the file and a
ten-second headphone check before each session. If the second voice cannot be recorded in the
same room, record 30 seconds of the first room's tone and use it under the joins.

---

## 4. TITLE AND DESCRIPTION

### What the form asks for, and what a judge reads

**This event, verbatim** (https://hackdays-guide.mlh.com/run-your-event/project-submissions.md,
fetched 10:16Z, the markdown version of the page):

> "4. Enter the project link, project name, description, and technologies used.
> 5. Add a demo URL if the team has one.
> 6. Under **Which challenge(s) are you submitting to?**, select every partner and local
> challenge the project is eligible to enter.
> 7. Select **Submit Project** before the deadline."

`MEASURED`. Five content fields, and the guide calls the demo URL conditional. Also on that
page, twice, in the organiser's own voice: "Verify the partner-specific evidence described on
the relevant partner page", which is the Solana page's "code, configuration, transaction,
deployed program, or other appropriate evidence".

Same page, in the list of things organisers must tell hackers before building begins: "The demo
format and time limit." `MEASURED`.

**Live event props at 10:22Z**, read from the page itself: `submissionsOpen: true`,
`submissionEndsAt: "2026-11-08T18:00:00Z"`, `lateDraftsOpen: false`,
`shortDescriptionLimit: 160`, `submissionsCount: 84`, `galleryPath: null`. `MEASURED`.

**The judge's side, on the platform MLH documents.** Devpost, which is what most MLH events
use: the judge is emailed a private link, "click the big Start Judging button to be directed to
the first submission", and on "the bottom right side panel of each submission" rates each
criterion 1 to 5 stars; "(There is no other mechanism for judges to provide feedback.)"
(https://help.devpost.com/article/103-how-to-judge-an-online-hackathon, fetched 10:11Z)
`MEASURED`. So the description has to carry the whole written argument, because there is
nowhere else to put one, and star ratings are not a conversation.

**For this event's platform, the judge's view is still `UNCONFIRMED`.** `records/findings/27`
§1.1 measured that MLH publishes no judge-facing page. That has not changed today.

**The title is bounded and the description is bounded.** "Video titles have a character limit
of 100 characters"; "The description allows a maximum of 5000 characters."
(https://support.google.com/youtube/answer/57407?hl=en and
https://support.google.com/youtube/answer/12948449?hl=en, both fetched 10:19Z) `MEASURED`.

**The best description in the sample is a verification index, not prose.** LOKA Pay's story
opens with the refusal, gives clock times ("5:05 PM, both iPhones offline … 5:06 PM, merchant
back online"), then lists explorer links for each transaction with `?cluster=devnet`, a
seven-stop judge guide, a claims table, and a labelled test receipt the reader can tamper with.
Read from https://devpost.com/software/loka-pay at 10:11Z. `MEASURED`. One of five measured
Solana winners does this; it is not the norm, but it is the standard.

### What this submission's description should contain

`INFERENCE`, assembled from measurements above and from the material already in
`records/SUBMISSION-PACK.md` §2.2, §2.7 and §2.8:

1. **The refusal first, in one sentence**, with the numbers: face 1.000 SOL, cap 2,500 basis
   points, 1.25 SOL admitted, one lamport over refused with error 6010.
2. **The two signatures as text, with their slots and the cluster**, so a reader can check them
   without the video. This is allowed: `records/SUBMISSION-PACK.md` §1.4's prohibition is about
   frames, and the pack already says both signatures go in the description. Do not paste an
   explorer URL that shows a `SYN…` mint.
3. **The repo link**, since the Solana partner page tells the judge to check the README for the
   integration.
4. **The honest limitation**, in the pack's own wording: what is built versus what is designed
   and simulated.
5. **The provenance sentence** in `records/SUBMISSION-PACK.md` §2.8, which says the surrounding
   UI is the company's frontend and was not built this weekend.
6. **The AI disclosure text** from §2.7, with the tool names filled in.
7. **Times inside the event window**, because MLH's published cheating check asks whether the
   timestamps are from the weekend. Times and slots, not a screenshot of a clock.

For the 160-character line, the pack's §2.2 paragraph is far too long and
`records/findings/27` §1.3 already supplies two candidates under the limit; either is fine and
the choice is his.

**What this project should do.** Title it with the project name and the one claim the
description proves ("pricing from the resale record, capped on chain"), put the refusal sentence
first in the description, and paste the two signatures, the repo link, the limitation, the
provenance sentence and the AI disclosure under it.

---

## 5. ORDER OF OPERATIONS

### What must be true before it is recorded, versus before it is published

Verbatim, from MLH's policy repository, fetched again today at
https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md:
`MEASURED` (re-verified in `rules-verified-2026-11-08.md` §1, unchanged):

> "1. We require all teams to submit a **2 minute or less** demo video. Your video must be
> **created the weekend of the hackathon**.
> 2. Your video must remain public post event to be eligible for prizes. If your video is not
> public, new winners may be selected.
> 3. Your demo video must **state the name of the hackathon at the beginning** of the video."

and the cheating check asks "(If they have a video) Was the video published over the weekend?"
(quoted in `rules-verified-2026-11-08.md` §7).

So, taking them in order:

| Requirement | Binds at | What it means operationally |
|---|---|---|
| created this weekend | the moment of recording | nothing in the file may predate 6 Nov 17:00Z; the console's own dated line and the card's date carry this `MEASURED` (rule 1) |
| states the hackathon at the start | the moment of recording | already in beat 1, "my demo for the MLH Solana Hackathon" `MEASURED` (rule 3) |
| 2:00 or less | the exported file | measured on the file, not the plan; 1:55.0 planned `MEASURED` (rule 1) |
| remains public | judging and after | the visibility setting must be **Public**, not Unlisted `MEASURED` (rule 2) |
| published over the weekend | the publish timestamp | so the upload has to go public before 18:00Z, not after `MEASURED` (cheat check) |
| submitted before the close | 18:00Z | `submissionEndsAt: 2026-11-08T18:00:00Z`, confirmed today `MEASURED` (event props) |

`INFERENCE`: whether MLH's platform treats Unlisted as public is not stated anywhere I fetched.
Rule 2's word is "public", and the cost of guessing wrong is the entry, so set it to Public.

### What happens if the video is edited after submission

**The description can be edited; the file cannot.** YouTube: "You can't replace a video since
any new video upload will get a new URL, but you can modify the existing video."
(https://support.google.com/youtube/answer/55770?hl=en, fetched 10:12Z) `MEASURED`.

Three consequences, in increasing order of severity:

1. Title, description and captions can be edited in place, and the video URL does not change.
   `MEASURED`.
2. A re-upload creates a new URL (`MEASURED`, same page), so any submission field pointing at
   the old link breaks silently and the break is invisible until a judge clicks it
   (`INFERENCE`).
3. A re-upload after 18:00Z publishes the replacement outside the event window, which is the
   thing the cheating check asks about. `INFERENCE`, and it is the reason not to plan on "fix
   it after".

**Two upload traps, both documented.** "If you close the upload window before you finish
choosing your Visibility settings, your video will be saved as private on your Content page in
YouTube Studio", and "Higher qualities such as 4K or HD may take more time to process … For
optimal processing time, verify your YouTube account."
(https://support.google.com/youtube/answer/57407?hl=en, fetched 10:19Z) `MEASURED`. A private
video at 17:55Z is an ineligible entry, and it looks published in the same tab where the
upload was started.

**Nothing on the platform accepts late work.** `lateDraftsOpen: false`, measured on this
event's page today, and `records/findings/27` §1.6 already recorded the same flag with its
consequence: late work is saved as a draft for an organiser to finalise, which is not a
submission.

**What this project should do.** Record, export, measure the file, then upload and publish
before the form is filled, leaving the two post-publish edits (captions and thumbnail) for
after, because neither touches the URL. Do not plan on replacing the file at any point.

---

## 6. THE ONE THING NOBODY DOES

There is one, and it is measured rather than argued: **nobody in the sample uploads a caption
file.** Seven videos across two winner samples, fetched today: six have a single `asr` track and
one has no track at all. Zero have a track a human wrote. §1, table above.
`MEASURED`, 10:20Z.

Why it is cheap: YouTube's own caption editor accepts a pasted transcript ("Auto-sync") and sets
the timing itself, or a `.srt` upload "With timing"
(https://support.google.com/youtube/answer/3038280?hl=en, fetched 10:09Z). The script for this
video is 221 written words, already timed to the beat in `../SCRIPT.md` §1. Fifteen minutes
converts it to a caption file, and the same text is already needed for the burned line.

Why it matters, with evidence rather than assertion: the sound-off study measures that removing
audio raises cognitive load and lowers comprehension while increasing reliance on subtitles
(§1), and the embed platform does not turn the caption track on (§1, measured in the Devpost
iframe). So the uploaded track is for the judge who goes looking, and the burned line is for
the judge who does not. A caption track is the one thing in this list that the sample gives
the second judge nothing from, and it can be fixed in the last hour.

One caveat, because the sample cannot settle it: whether any of the seven **burns** a caption
line into the frame. Puzzlify's poster is a frame from the video and it carries a line of large
white text along the bottom edge, which is consistent with burned-in subtitles, and one frame
is not proof. `winner-video-research.md` §6 records the same gap as unverified. So the claim
here is narrow and it holds: nobody in the sample ships a caption **track**.

Two candidates I checked and am **not** putting forward, because something in the sample does
them:

- A designed thumbnail. Only one of the seven is a purpose-built card (§2), which makes it
  nearly as rare, and the four accidental posters in that table are the argument for doing it.
  It is second on this list only because one entry does it.
- A checkable provenance line in the description. LOKA Pay's does it thoroughly and the other
descriptions recorded in `records/findings/27` §2.2 are empty or absent, so one of the four
measurable entries does it. Still worth copying, and §4 lists what to put there.

**What this project should do.** Ship a human-written caption track, because it is the only
thing in this list that no measured winner does and it costs fifteen minutes of work that is
already done in another form.

---

## The last hour, in order

Each line has a pass condition. Stop at the first failure. Times are offsets from the start of
the hour, not clock times.

| # | Do | Pass condition |
|---|---|---|
| 1 | Check the video's visibility is **Public** and the URL opens in a private window, logged out | it plays, with sound, for a logged-out viewer |
| 2 | Play the file end to end and read the running time off the player | ≤ 2:00, and ≥ 1:50 so it sits under the cap like the sample |
| 3 | Check the first spoken sentence names the hackathon | "my demo for the MLH Solana Hackathon" is audible in the first twenty seconds |
| 4 | Check the poster: is it the designed card, or a YouTube-chosen frame | the card, at 1280×720, and `error 6010` is legible at small size |
| 5 | Open the captions panel and confirm the track is the one you wrote, not ASR | `English` shows as your track, and the words `lamport`, `Token-2022`, `basis points` are spelled right |
| 6 | Read the description top to bottom as a stranger | the first line names the refusal and the numbers; the two signatures, repo link, limitation, provenance sentence and AI disclosure are all present |
| 7 | Check no frame shows a terminal, a desktop, a bookmark bar, a notification, or a `SYN…` explorer page | scroll the video at 5-second intervals; nothing of the sort appears |
| 8 | Confirm both signatures still resolve on devnet | both lookups return the recorded slot |
| 9 | Fill the form: project link, name, description, technologies, demo URL, every challenge it qualifies for | the 160-character line is under the limit and reads as a whole sentence |
| 10 | Submit, then re-open the submission as a logged-out viewer | title, description and a working video link, with nothing truncated |
| 11 | Screenshot the confirmation | the entry exists with a timestamp before 18:00Z |
| 12 | Leave the tab open until 18:00Z | if anything above changes, the description and captions can still be edited; the file cannot |

Two things not to do in that hour, each measured above: do not re-upload the video for any
reason, and do not close the Studio upload window before the visibility is set.

---

## Sources, with fetch times

| URL | What it established | Fetched |
|---|---|---|
| https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0306251 | sound-off raises cognitive load, lowers comprehension, increases reliance on subtitles (n=168) | 10:10Z |
| https://developers.google.com/youtube/player_parameters | `cc_load_policy` default is user preference; no parameter means captions off; `autoplay` default 0 | 10:11Z |
| https://devpost.com/software/loka-pay | the platform's embed carries no `cc_load_policy`; `og:image` is the project photo; video thumb is `img.youtube.com/vi/<id>/0.jpg`; description as verification index with timestamps | 10:11Z |
| https://support.google.com/youtube/answer/3038280?hl=en | caption routes (upload, auto-sync, manual); auto captions published automatically, default language only | 10:09Z |
| https://support.google.com/youtube/answer/72431?hl=en | thumbnail is auto suggestion or an upload, uploads need a verified account | 10:09Z |
| https://support.google.com/youtube/answer/171664?hl=en | verification is a phone number and code; custom thumbnails are listed as a verified feature | 10:19Z |
| https://support.google.com/youtube/answer/55770?hl=en | a video cannot be replaced; a new upload gets a new URL | 10:12Z |
| https://support.google.com/youtube/answer/57407?hl=en | 100-character title limit; closing the upload window leaves the video private; processing time | 10:19Z |
| https://support.google.com/youtube/answer/12948449?hl=en | 5000-character description limit | 10:19Z |
| https://hackdays-guide.mlh.com/run-your-event/project-submissions.md | the five content fields verbatim; "demo format and time limit"; judging rubric; partner-evidence check | 10:16Z |
| https://www.mlh.com/events/solana-hackathon | 84 submissions; close 8 Nov 1:00 PM EST; props `submissionEndsAt 2026-11-08T18:00:00Z`, `lateDraftsOpen false`, `shortDescriptionLimit 160`, `galleryPath null` | 10:22Z |
| https://help.devpost.com/article/126-know-your-submission-steps | gallery thumbnail is a separate 3:2 upload; video must be public on YouTube or Vimeo | 10:09Z |
| https://help.devpost.com/article/103-how-to-judge-an-online-hackathon | judges get an emailed link, one submission at a time, 1 to 5 stars per criterion, no free text | 10:11Z |
| https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md | video rules 1 to 6 (re-verified; unchanged from `rules-verified-2026-11-08.md` §1) | 10:22Z |
| https://blog.frame.io/2022/03/10/recording-voiceovers-from-home-part-3-recording | -18 to -4 dBFS, never past 0; two clenched fists; talk past the mic; stay in position | 10:13Z |
| https://www.izotope.com/community/blog/basics-of-room-tone-audio-editing | what room tone is; 30 to 60 seconds; matching an overdub from another room | 10:14Z |
| https://img.youtube.com/vi/<id>/maxresdefault.jpg and `/0.jpg` for seven sample videos | 6 of 7 serve 1280×720; Firekit serves 480×360 only; thumbnails viewed directly | 10:18Z |
| https://www.youtube.com/watch?v=<id> for seven sample videos | caption tracks: six `asr`, one absent, none manual | 10:20Z |

**Failed fetches, recorded so the next pass does not repeat them:** `w3.org` (WAI captions page,
WCAG 2.2 understanding document) refused through the proxy chain on three attempts;
`service.shure.com` knowledge base article on two singers sharing one microphone returned all
fallbacks failed; Shure's recording-techniques PDF extracted to zero characters.

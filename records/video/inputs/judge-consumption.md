# How a judge actually consumes a submission at an MLH-hosted digital event

**Written:** 2026-11-08, 10:30Z to 10:35Z. Every quote below was fetched in that window with the
web-fetch tool from the URL beside it, and is verbatim. Nothing here is copied from another file in
this repository without being re-read on the primary page first; where a re-read contradicts our
record, both are quoted in §8.

**Tags.** `MEASURED` means the page states it and the sentence is quoted. `INFERENCE` means I derived
it, and the derivation is shown so it can be checked or thrown out. `MEASURED-ABSENT` means the
sources that should contain it were read and do not.

**One thing to hold onto before the seven answers.** There are five different authorities in play and
they do not say the same thing. Two of them are MLH addressing organisers, one is MLH addressing
entrants, one is Devpost describing its own software, and one is this event's own page, which says
nothing about judging at all. The answers change depending on which one is being quoted, so every
quote below is labelled with its authority.

---

## 0. The five authorities, and how much each binds this entry

| Authority | What it is | Binds this entry? |
|---|---|---|
| MLH Standard Hackathon Rules (policies repository) | Rules for entrants, including a section for "fully digital hackathons that MLH hosts" | **Yes.** This event is digital, MLH-hosted, and its page carries the register / check in / submit flow the rules refer to |
| MLH Organizer Guide, Judging Plan | MLH recommending a judging method to organisers. Written around an in-person science-fair event | Recommends, does not bind. Useful because it is the only place MLH publishes a time budget per project |
| MLH Hack Days Guide (2026 season) | MLH instructing organisers of its own events on the platform this event uses: Challenges page, Manage Submissions, winner declaration | Closest thing to "this event states", but written for in-person Hack Days, so applying its in-person framing here is `INFERENCE` |
| Devpost help centre | The software most MLH events use for submissions and scoring | **Does not bind this event.** Its submission flow is MLH's own (see §7) |
| This event's page | Dates, five prize categories, a submission count | States no judging method, no criteria, no video rule, no schedule |

---

## 1. How many times a project is seen, and for how long

**MEASURED, the multiplier and the per-view time.** MLH Organizer Guide, Judging Plan,
https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md, fetched
10:30:48Z:

> "**n** = Number of Judges for each project (or number of rounds of judging per project) (MLH
> recommendation: 3 rounds per project)"

> "**t** = Time taken by a Judge per project (MLH recommendation: 4 mins per project. 2 minutes for
> presentation + demo, 1 minute for questions from judges and score compilations, and 1 minute for
> judge travel)"

**MEASURED, the arithmetic that uses them.** Same page:

> "J = ⌈(P \* n \* t )/ T⌉"

> "For eg.: Consider you have **175 projects submitted** at your hackathon and you have **allocated
> 2 hours for judging**. … Now the calculation looks like: J= ceiling_function((175\*3\*4)/120) =
> ceiling_function(17.5) = 18"

**MEASURED, stated as a goal rather than a formula.** Same page:

> "The goal is to have each project seen at least 3 times, but not have judges see the same "sets"."

**MEASURED, the strict stopwatch at a table.** Same page, in the Judging Debrief the organiser gives
judges before they start:

> "**They only have 3 minutes per team**."

**The arithmetic, stated plainly.** `INFERENCE` from the two published variables, no new numbers
invented:

- Per project, across the whole judging block: `n × t` = 3 × 4 = **12 minutes of judge attention**.
- Per judge, per project: **4 minutes**, of which 2 are presentation and demo, 1 is questions and
  score compilation, and 1 is judge travel.
- Of those 4 minutes, **2 are the demo itself**, which is exactly the length of the video the rules
  require. Under MLH's own numbers the video is at most half of one judge's per-project slot and
  one sixth of the total attention a project receives across three rounds.
- One of the four minutes is "judge travel", a physical quantity. `INFERENCE`: a judge reviewing a
  submission on a platform does not spend a minute walking, so if the digital method keeps `t = 4`,
  the time available for the artifact is 3 minutes, not 4. MLH does not say this anywhere; it is
  what the word "travel" forces.

**MEASURED, and it changes the premise: MLH's own digital guidance is live, not asynchronous.**
https://guide.mlh.com/overview/event-types/digital-events.md, fetched 10:31:04Z, section "Digital
Judging":

> "Live Judging: If you are doing a digital event, we recommend making a discord voice channel for
> each team (Team 1, Team 2...., Team 50). Hackers can wait in the call then screenshare/join video
> as judges join the channel."

So at a digital event the recommended consumption is a live screenshare in a voice channel, not a
video review. The 4-minute slot and the 2-minute demo component then apply to a human on a call.

**MEASURED, what the video is for in the recommended method.** Judging Plan, same page:

> "Structurally, we recommend having hackers submit 2 minute videos on your submission platform for
> the judges to review. … Their video should be a demo of their hack, not a presentation. This is not
> needed for judging when science fair style, but can be a reference during final deliberations, and
> is always a good future reference if they want to include it on their resumes."

Read that sentence twice. In the method MLH recommends, the video is **not needed for judging** and
is a reference during deliberations. The 2-minute video is mandatory for entrants (digital rule 1,
quoted in §6) and it is the required artifact at a digital event, but MLH's own judging plan demotes it
below a live demo.

### The event page's numbers, and what they imply

**MEASURED.** https://www.mlh.com/events/solana-hackathon, fetched 10:31:53Z:

> "85 Submissions"
> "Submissions close Nov 8, 1:00 PM EST"

The same page at 07:37Z read 70 and at 10:22Z read 84, so 85 is a timestamped reading, not a total.
`INFERENCE` on that number: the Hack Days Guide warns it overcounts, "The same project can appear once
for every challenge it selected, and the total shown in Manage Submissions may count those challenge
entries" (https://hackdays-guide.mlh.com/run-your-event/project-submissions.md, fetched 10:31:03Z),
so 85 is an upper bound on unique projects, not a count of them.

**MEASURED-ABSENT: the event page publishes no judging window and no judge count.** A raw read of the
served HTML at 10:33Z (94,693 bytes) contains zero occurrences of "judg", "rubric", "score",
"criteri", "video", "demo" and "thumbnail", case-insensitive. The page adds nothing to judging beyond
the submission count and the deadline.

**INFERENCE, arithmetic only, and explicitly not a published figure.** No page states how many judges
this event has or how long its judging block is. Feeding the page's project count into MLH's own
formula gives what the formula would require, nothing more:

- P = 85, n = 3, t = 4, T = 120 minutes: `⌈(85 × 3 × 4) / 120⌉` = `⌈8.5⌉` = **9 judges**.
- P = 85, n = 3, t = 4, T = 180 minutes: `⌈(85 × 3 × 4) / 180⌉` = `⌈5.67⌉` = **6 judges**.

Both numbers depend entirely on a T the event does not publish, which is why neither is a fact about
this event. And the per-project time does not move with T at all: T only sets how many judges are
needed, not how long each takes. Per project the recommendation stays 3 views of 4 minutes.

---

## 2. Video, repository, or both, and in what order

Nothing organiser-side states an order for a judge's first action at a digital event. The statements
that exist, in descending authority:

**MEASURED, the rules describe the demo as the thing shown to judges, and name the video as the
digital form of it.** https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md,
fetched 10:32Z, section "Demos":

> "After hacking finishes, teams will show their projects to each other and to the judges. Either via
> a prerecorded video (typically at digital events or live demos at physical hackathons)."

> "You are strongly encouraged to present a demo of what you have built. Pitches and presentations
> are discouraged. You are not judged on the quality of your pitch or the quality of your idea."

**MEASURED, the video is a reference, not the primary evidence, in the recommended method.** Judging
Plan, quoted in §1: "This is not needed for judging when science fair style, but can be a reference
during final deliberations".

**MEASURED, the repo is what the cheating check opens with.** See §4, where the first bullet of the
ordered list is "You should check their GitHub".

**MEASURED, the partner page tells the judge to have the team point at the repo during the demo.**
https://hackdays-guide.mlh.com/partner-programs/solana.md, fetched 10:33Z:

> "Confirm that the winning project actually uses Solana. Ask the team to identify the integration in
> its README and show the relevant code, configuration, transaction, deployed program, or other
> appropriate evidence during the demonstration."

**MEASURED, and it is the only page that puts the video first.** Devpost, Video-making best practices,
https://help.devpost.com/article/84-video-making-best-practices, fetched 10:31:43Z:

> "Aside from your app itself, your demo video is one of the most important (and exciting) elements of
> your submission/portfolio piece! In fact, it's often one of the first things that judges, voters, and
> those checking out your software will review."

**Answer, with the authorities kept apart.** MLH to organisers: the live demo or the video is what the
judge sees, the repo is what the cheat check reads, and in science-fair mode the video is a reference
for deliberations. Devpost to submitters: the video is often one of the first things a judge reviews.
No page anywhere states "the judge watches the video, then opens the repo", or the reverse. That order
is `MEASURED-ABSENT`, and the only ordered list that exists anywhere in the sources is the cheating
check, which is about fraud review, not scoring.

---

## 3. What the judge is asked to record: score, rank, or comment

Three different answers exist, from three different authorities, and they are not reconcilable by
reading alone.

**MEASURED, MLH's recommended method records a rank, not a score.** Judging Plan, fetched 10:30:48Z:

> "There're plenty of options with finalizing winners, but at MLH, we love to use Stack Ranking because
> it normalizes scores across judges. Some judges are super nice, and might give higher scores overall
> than a stricter judge. By using stack ranking, you eliminate the point variation and make it so teams
> earn points based on how they rank with each judge instead of as an overall score that depends on what
> the judge considers a 5/8/10."

> "Ask each judge to view their projects and report back their top 3 best/favorite projects."
> "Assign the top three following points: 3 points (First Place), 2 points (Second Place), 1 point
> (Third Place)"

and from the Judging Debrief: "**They need to bring back top 3 projects of the set assigned.**"

**MEASURED, the 2026 Hack Days rubric records a rubric judgement and a note, with no scale named.**
https://hackdays-guide.mlh.com/run-your-event/project-submissions.md, fetched 10:31:03Z:

> "Score every eligible project using the same criteria. A lightweight rubric works well for short
> events:"

> "| Technical implementation | Does the project work, and how effectively does it use the chosen
> technology? |
> | Creativity | Is the idea or implementation distinctive? |
> | Learning and ambition | What did the team learn or attempt during the Hack Day? |
> | Demo and clarity | Can the team clearly explain the problem, solution, and implementation? |
> | Partner eligibility | Does the project satisfy the assigned partner's specific requirements? |"

(reformatted from the page's markdown table into one row per line; the cell text is unchanged)

> "Record the proposed result in the judges' notes."

Five criteria, and no scale, no weighting, and no arithmetic on how five criteria become one winner.

**MEASURED, and this is where 1-5 comes from: Devpost, twice.** How to judge an online hackathon,
https://help.devpost.com/article/103-how-to-judge-an-online-hackathon, fetched 10:31:43Z:

> "On the bottom right side panel of each submission, you will find a Rate the Submission box. For each
> item in the list of criteria, you will assign a rating of 1-5 stars. 1 star is the lowest rating and 5
> is the highest rating. (There is no other mechanism for judges to provide feedback.)"

Offline judging: using printed score sheets, https://help.devpost.com/article/101-offline-judging-using-printed-score-sheets,
fetched 10:32:43Z:

> "The scale you use to rate submissions is up to you, but we recommend that each criterion be rated on
> a scale of 1-5 (with 1 as the lowest rating and 5 as the highest rating)."

and "The hackathon judging criteria are listed under each of the submissions on the score sheet. There
is also space for the judge to provide additional notes."

**Answer.** A 1-5 scale is published, twice, by Devpost: as fixed software behaviour for online judging
and as a recommendation for paper sheets. It is therefore not our inference that a 1-5 scale exists in
the world. It **is** our inference that a 1-5 scale applies to this entry, and the inference is weaker
now than our record assumed: MLH's recommended method is a rank with 3/2/1 points and its 2026 rubric
names no scale at all, and this event takes submissions through MLH's own flow rather than Devpost's
(§7). Which mechanism the Solana Hackathon judges used is `MEASURED-ABSENT`. No MLH page publishes a
1-5 rubric for its own platform.

---

## 4. What the cheating check opens first

**MEASURED.** https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md,
fetched 10:30:48Z. The ordered list, verbatim and complete:

> "Here are common things to check:
> * You should check their GitHub(recommended you require this as part of the submissions)
>   * Did they start before the event?
>   * Is it one big commit at the beginning of the event? (Remember, some hackers are new! And just
>     don't know how to use Git. One commit at the end of the event is NOT a reason to DQ)
>   * Did they push changes after submissions closed? Check the repository's activity and compare
>     views to inspect recent changes. Small bug fixes may be allowed depending on your rules;
>     substantial new features may not be.
>   * Does their readme mention a different event?
>   * Is every team member contributing?
> * Is a solo hacker making a really advanced project in a single weekend?
> * Are their Timestamps over the weekend when they run the demo in any video/screen captures?
> * (If they have a video) Was the video published over the weekend?
> * (If they have a video) Does it mention another event? Does it mention yours?
> * Look at the team members Devpost profiles - Have they submitted this project to any other
>   hackathons? Does it look similar to an old project in their portfolio?"

**What the order says.** Counting the nested bullets, that is eleven checks. The first six are the
GitHub family: the opening line plus start date, commit shape, pushes after the close, README contents
and contributor spread. The seventh is a judgement about scope (solo hacker, advanced project). The
video checks are the eighth, ninth and tenth, and two of those three are hedged with "(If they have a
video)". The submission-profile checks come last.

`INFERENCE`, and it is the closest published thing to "what a reviewer opens first": for a reviewer
following this list, the repository is opened first and the video is inspected as corroboration of
dates and provenance. Note what the video is checked *for* here: not quality, not content, not the
demo. Weekend timestamps, publish date, and whether it names another event. The cheating check reads
the video as a timestamp, not as evidence of the build.

---

## 5. Do judges watch muted, at speed, or skip

**MEASURED-ABSENT.** None of the fetched pages says anything about playback speed, muting, skipping,
partial viewing, watch time, or how much of a video a judge watches. That covers every judging page in
the MLH guide index, the six Hack Days guide pages that cover submissions, judging and winners, every
article in Devpost's Videos and Judging collections, and this event's own page, all read in this
window.

What the sources do say, which is adjacent but not the same claim:

- `MEASURED` the rules require the video to *state* the hackathon's name at the beginning, and MLH's
  own example of that statement is spoken: "Ex. "Hey I'm Sam and this is my demo for CorgiHacks.""
  That presumes audio is expected, and says nothing about whether it is heard.
- `MEASURED` Devpost recommends the form itself: "we recommend creating a screencast (a video screen
  capture with audio narration) because it can help judges, voters, and other users to understand
  exactly how your app works, without the gimmicks." Narration is the recommended form. Nothing states
  the judge listens to it.
- `MEASURED` Devpost on paper judging: judges "score submissions using paper and a pencil", and the
  sheet "lists every submission that is visible in the gallery" with the criteria and space for notes.
  Paper sheets imply a per-submission record, not a per-second viewing record.

**What would settle it.** A judge's own account of how they worked through a set (however many the
organiser recruited, which the event does not publish), or per-submission viewing data from whichever
platform ran the judging. Devpost's own manager pages, read this window (102, 105, 106, 107), publish
only progress per judge: "The dashboard shows you which judges have started judging and their scores."
No watch time, no completion, no speed. So even the platform's manager view cannot answer it, and the
platform's judge view (the one page that would) is behind a private per-judge link.

The consequence for planning is a rule about evidence, not a guess about behaviour: any claim that the
video will be heard, or watched past the first frame, is unsupported by every page fetched here. A
video whose argument survives on picture and on-screen text alone survives the unmeasured case; a
video whose argument is only in the narration does not.

---

## 6. What the first twenty seconds has to accomplish

Stated as a conclusion from the documents, not as advice. Five requirements, each with its source.

**1. It must name the event, out loud, at the beginning, because that is a rule.**
https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md, fetched 10:32Z:

> "3. Your demo video must state the name of the hackathon at the beginning of the video. Ex. "Hey I'm
> Sam and this is my demo for CorgiHacks.""

**2. It must say what the app does, because Devpost puts that in "the first few seconds" and calls the
opening a trailer.** https://help.devpost.com/article/84-video-making-best-practices, fetched 10:31:43Z:

> "What's your elevator pitch? Be sure to explain what your app does (and if making the video for a
> specific hackathon, how it addresses the hackathon) in the first few seconds of your video. You can
> get into the details of how it works immediately after, but treat the opening seconds of your video
> as you would a movie trailer or TV ad: pique your audience's interest."

**3. It must have started a demonstration, because the pitch is explicitly not scored and the demo is.**
Same rules page:

> "Pitches and presentations are discouraged. You are not judged on the quality of your pitch or the
> quality of your idea."

and the 2026 rubric scores "Demo and clarity: Can the team clearly explain the problem, solution, and
implementation?"

**4. It must be understood as the start of an account of the criteria, because judges are told to
score the description.** Rules page, "Judging Criteria":

> "Teams will be judged on these four criteria for MLH digital events or MLH categories at an in person
> event. Judges will weigh the criteria equally. During judging, participants should try to describe
> what they did for each criterion in their project."

Technology, Design, Completion, Learning, equally weighted. Twenty seconds is one sixth of a 2:00
video and, under `t = 4`, one sixth of a judge's entire per-project presentation-and-demo slot. Four
criteria at equal weight leave thirty seconds each across two minutes, which is the arithmetic of the
published weighting and not a style preference.

**5. It has to earn a place in a top three, not a good average, if the recommended method is used.**
Judging Plan, quoted in §3: "report back their top 3 best/favorite projects" and 3/2/1 points for
first, second and third. `INFERENCE`: a ranking forces a comparison, and a comparison needs one
identifiable thing to compare. The first twenty seconds is where a project either becomes that thing
(a named mechanism, a visible refusal, a number) or remains a general impression.

**The conclusion in one sentence.** Under these documents the first twenty seconds carries three
mandatory contents (the event's name spoken, what the app does, the demo already running) and one
structural job (begin the criterion-by-criterion account that judges are told to score), and it needs
all four inside roughly one sixth of the time a judge will give the project, which is why nothing in
the sources supports spending any part of it on a problem statement, a personal story, or a title card.

---

## 7. Is the thumbnail or project image shown to a judge before the video plays

**MEASURED, the field exists on Devpost and is separate from the video.**
https://help.devpost.com/article/126-know-your-submission-steps, fetched 10:33:16Z:

> "Thumbnail image for the Project Gallery | This should be a JPG, PNG or GIF format, 5 MB max file
> size. For best results, use a 3:2 ratio."

> "Video demo link* | This is usually required! Your video must be hosted publicly on YouTube, or Vimeo
> to properly embed for the judges. Be sure to check the Hackathon Rules for any requirements regarding
> maximum video length."

**MEASURED, YouTube describes a thumbnail as a snapshot, not as a pre-play frame.**
https://support.google.com/youtube/answer/72431?hl=en, fetched 10:33Z:

> "Custom video and Shorts thumbnails let your audience view a quick snapshot of your content. You can
> choose from auto generated suggested options, or upload your own if your account is verified."

**MEASURED-ABSENT: no page states that a judge is shown the thumbnail or the project image before the
video plays.** Not the judging plan, not the cheating check, not the Devpost judging article, not the
Hack Days guide. Devpost's judge-facing article (103) describes the submission page and the rating box
in the bottom right panel and never mentions an image, a gallery or a thumbnail. So the sequence
"image, then play" is not published anywhere I can reach.

**And for this event the question may not even arise on the form.** `MEASURED`, the submission fields
this event's flow asks for, https://hackdays-guide.mlh.com/run-your-event/project-submissions.md,
fetched 10:31:03Z:

> "4. Enter the project link, project name, description, and technologies used.
> 5. Add a demo URL if the team has one."

Four content fields and a conditional demo URL. No thumbnail field, no video field, no gallery. Note
also that the same page states plainly that Devpost is not the flow: "Devpost, a form, or another
platform does not replace this flow."

`INFERENCE`, and it is the honest version of the poster argument: a link that is clicked opens a page,
and a page that embeds a video will show something before playback. But no organiser document promises
a judge will look at an image before pressing play, and this event's flow gives a submitter no image
field to control it with. Anything built on "the poster is the first thing the judge sees" is a bet on
platform behaviour, not a documented requirement.

---

## 8. Where our own record needs correcting, with both quotes

**8.1 The 1-5 scale is real, but it is Devpost's, and our record attaches it to this event's judge.**
`records/video/inputs/production-and-metadata.md` §4 says "The judge's side, on the platform MLH
documents. Devpost, which is what most MLH events use: the judge is emailed a private link …" and then
quotes the 1-5 stars line. The quote is accurate; I re-read it at 10:31:43Z and it is unchanged. What
is wrong is the bridge. The 2026 Hack Days Guide, which documents the flow this event's page actually
links to, says (fetched 10:31:03Z): "Every presenting project must be submitted through the event's
**Challenges** page. Teams must also select each eligible partner challenge they are entering. Devpost,
a form, or another platform does not replace this flow." And the FAQ on the same guide (fetched
10:31:08Z): "You may use an external tool as an optional judging aid. It does not replace the required
OrganizerHQ project submissions, challenge selections, check-ins, or winner declarations." So the
figure stands, the application to this event does not, and this file should be read as the correction.

**8.2 The "3 minutes per team" location.** `records/video/inputs/rules-verified-2026-11-08.md` §2 says
the line appears "in a section about table-based judging". It is in "Judging Debrief", the briefing
list an organiser reads to judges before science-fair judging starts, which is table-based. The
substance of our reading holds and is unchanged: it is a stopwatch at a table, not a video length, and
the same page recommends 2-minute videos in its own words. Only the section name was loose.

**8.3 "The first frame a judge sees, before pressing play".** `records/video/DELIVERY.md` §1 opens with
that phrase. Every measurement in it is sound, and the phrase's second half is not sourced: no
organiser or platform page states a judge sees a poster, and §7 above shows this event's form has no
image field at all. The recommendation (upload a designed card) is still the only thing under the
submitter's control on YouTube, but it should be described as a bet on platform behaviour, not as a
documented step in judging.

**8.4 One claim worth keeping, re-verified today.** `rules-verified-2026-11-08.md` §2's quote of the
video recommendation ("Structurally, we recommend having hackers submit 2 minute videos on your
submission platform for the judges to review") is verbatim on the page at 10:30:48Z, and so is the
sentence that follows it, which our record did not carry: "This is not needed for judging when science
fair style, but can be a reference during final deliberations". That omission made the video look more
central to judging than MLH's own page says it is, and §2 above now carries it.

**8.5 Nothing else in the four files read for this task contradicts the primary pages** on dates,
deadlines, the 2:00 cap, the four equally weighted criteria, or the requirement to name the event at
the start. Those were re-read today and hold.

---

## 9. The seven answers, in one place

1. **Three times, four minutes each.** `n = 3` rounds and `t = 4` minutes are published as MLH
   recommendations, so 12 minutes of judge attention per project in total, 4 per judge, of which 2 are
   the demo. The event page's 85 submissions imply 9 judges for a 2-hour block or 6 for a 3-hour block
   by MLH's own formula, but the event publishes no block and no judge count, so those are arithmetic,
   not facts. And MLH's own digital guidance recommends live Discord judging, which makes the video the
   artifact of last resort in its recommended method.
2. **No page states an order.** MLH says the demo is what judges see and the repo is what the cheat
   check reads. Devpost says the video is often one of the first things judges review. An order for a
   judge's first action is `MEASURED-ABSENT`.
3. **Rank under MLH's recommendation (top 3, 3/2/1 points), a five-criterion rubric with no scale in
   the 2026 guide, and 1-5 stars under Devpost.** 1-5 is published, so it is not our invention; that it
   applies to this entry is our inference and is not published.
4. **The repository, then the video as a timestamp check, then the team's submission history.** Quoted
   in full in §4, seven repo-and-project checks ahead of the video checks.
5. **`MEASURED-ABSENT`.** No page mentions muting, speed or skipping. What would settle it: a judge's
   own account, or viewing data from the platform that ran the judging; Devpost's manager dashboard
   publishes progress and scores only.
6. **Name the event, say what the app does, and have the demo running, all inside one sixth of a 2:00
   video, because those three are the only starts the documents name and the pitch is explicitly not
   scored.**
7. **`MEASURED-ABSENT`.** A thumbnail field is published for Devpost's gallery and YouTube describes a
   thumbnail as a snapshot, but no page says a judge sees it before the video plays, and this event's
   form has no image field at all.

---

## 10. Sources, with fetch times

| URL | Authority | Fetched |
|---|---|---|
| https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md | MLH to organisers, recommended method | 2026-11-08 10:30:48Z |
| https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md | MLH to organisers, fraud review | 10:30:48Z |
| https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal.md | MLH to organisers, portals | 10:30:58Z |
| https://guide.mlh.com/general-information/judging-and-submissions/rules-for-your-hackathon.md | MLH to organisers, rule checklist | 10:31:19Z |
| https://guide.mlh.com/general-information/judging-and-submissions/judges-communication-and-recruiting.md | MLH to organisers, recruiting | 10:31:04Z |
| https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal/using-devpost.md | MLH to organisers, online vs offline judging | 10:31:19Z |
| https://guide.mlh.com/overview/event-types/digital-events.md | MLH to organisers, digital judging | 10:31:04Z |
| https://guide.mlh.com/llms.txt and /sitemap.md | documentation index, to prove no rubric or scoring page exists | 10:30Z and 10:32Z |
| https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md | MLH to entrants, rules and criteria | 10:32Z, re-fetched 10:35:26Z, content identical |
| https://hackdays-guide.mlh.com/run-your-event/project-submissions.md | MLH to organisers, the flow this event uses | 10:31:03Z |
| https://hackdays-guide.mlh.com/run-your-event/closing-ceremony-and-winner-declaration.md | MLH to organisers, winner recording | 10:31:07Z |
| https://hackdays-guide.mlh.com/help/frequently-asked-questions-faq.md | MLH to organisers, Devpost as aid only | 10:31:08Z |
| https://hackdays-guide.mlh.com/plan-your-event/sample-schedules.md | MLH to organisers, demo block lengths | 10:31:08Z |
| https://hackdays-guide.mlh.com/partner-programs/solana.md | MLH to organisers, partner evidence | 10:33Z |
| https://www.mlh.com/events/solana-hackathon | this event, as served | 10:31:53Z, raw HTML 10:33Z |
| https://help.devpost.com/article/103-how-to-judge-an-online-hackathon | Devpost, judge's view | 10:31:43Z |
| https://help.devpost.com/article/101-offline-judging-using-printed-score-sheets | Devpost, paper scale | 10:32:43Z |
| https://help.devpost.com/article/84-video-making-best-practices | Devpost, video guidance | 10:31:43Z |
| https://help.devpost.com/article/85-uploading-a-demo-video | Devpost, video hosting rules | 10:31:43Z |
| https://help.devpost.com/article/126-know-your-submission-steps | Devpost, submission fields | 10:33:16Z |
| https://help.devpost.com/article/102-managing-submissions | Devpost, manager-side statuses | 10:32:14Z |
| https://help.devpost.com/article/105-starting-the-judging-period | Devpost, judging start | 10:32:15Z |
| https://help.devpost.com/article/106-monitoring-the-judges-progress | Devpost, what the dashboard shows | 10:32:16Z |
| https://help.devpost.com/article/107-ending-the-judging-period-and-selecting-winners | Devpost, winner selection | 10:31:43Z |
| https://support.google.com/youtube/answer/72431?hl=en | YouTube, thumbnails | 10:33:02Z |

**Not read, and why it matters.** The judge's actual screen at this event. It sits behind a private
per-judge link on MLH's platform and behind sign-in on Devpost, so everything in §2, §3 and §5 about
what the judge sees is either a platform's own description of its software or `MEASURED-ABSENT`.

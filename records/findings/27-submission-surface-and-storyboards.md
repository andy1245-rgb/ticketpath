# 27 — Winning the submission itself: what a judge sees, what past videos did, three storyboard options

**Numbering, so nobody hunts for a missing file.** This file was first written as `26-`, and
`records/findings/26-identity-bound-wallets.md` (another worker's, written 22:25Z, not read for this one and
not touched) already held that number, so this one moved to 27 at 22:36Z. The board note and every reference
below use 27.

**Written:** 2026-11-07T22:20Z to 22:42Z. **Event:** MLH Solana Hackathon, partnered, online,
2026-11-06 17:00Z to 2026-11-08 18:00Z. **Deadlines:** initial submission Sunday 15:00Z (10:00 ET),
hacking ends 16:45Z (11:45 ET), platform close 18:00Z.
**Tree read at:** commit `33d95b3` plus a working tree other sessions were writing to while this pass ran
(`tools/devnet_publish.py`, its tests, `.gitignore`, `tools/check_frontend_attach.py`, and untracked records
including `records/findings/26-identity-bound-wallets.md`). None of their work was read as evidence, changed,
or cited as mine, except where §4.3 says so explicitly.
**Field size, measured by this pass at 22:30Z:** 36 submissions. `records/findings/23-…` measured 25 at
20:39Z, 18 at 18:28Z and 7 at 10:59Z.

**What this builds on, and what it does not redo.** `records/findings/23-hackathon-score-analysis.md`
established the two rubrics, the five tracks, the sentence that decides the main prize, the four-item
materials test, and what four winning submissions did on chain. `records/findings/17-hackathon-rules-recheck.md`
re-verified the rules and corrected two claims. `records/SUBMISSION-PACK.md` §1 already holds a timed
six-beat script. **None of that is repeated here.** This file answers a different question: what a judge
physically sees and in what order, what past submission videos were built like as artefacts, what the
organisers and judges publish about the video, and what this build could honestly put on screen — then
offers three storyboards as options, and decides nothing.

**Labels.** **MEASURED** — a named page or file says it, with the URL or `path:line` in the entry.
**MEASURED-ABSENT** — the named pages were read and the thing is not on them. **UNKNOWN** — the page is
behind a login or a JS shell and was not read; it is not the same as absent. **ASSERTED** — my reasoning.
**CONFLICT** — two named sources disagree; both are quoted and neither is resolved here.
The programme's A–E classes describe evidence about ticket markets and do not fit hackathon rules, so they
are not forced on; predictions about how a judge will react are marked **ASSERTED, class D**, as
`records/findings/23-…` did.

**Method note, because it bounds what is below.** Page fetches in this pass ran 22:23Z–22:30Z from this
host over plain HTTP with no browser and no login. The local search CLI returned nothing all run (its
Brave credentials are missing), so discovery went through documentation indexes (`llms.txt` on two MLH doc
sites) and known paths. **No claim below rests on a search result.** The video transcripts could not be
read: `yt-dlp` is not installed and was not installed, and YouTube's caption endpoint returns zero bytes
to this host. So §2 is about durations, published descriptions and chapter lists, not about frames I
watched. That limit is stated again where it bites.

---

## 1. The surface: what a judge sees, and in what order

### 1.1 The chain, and the one link nobody documents

Submission → organiser's review panel → judge → score. Three of those four are published. The third is
not.

| Link | Documented? | Where |
|---|---|---|
| the form and its fields | **MEASURED** | `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md`, "Last updated: October 2026" |
| the gate before the form (register, check in) | **MEASURED** | same page, steps 1–3; the live event page's own strip `1 Register 2 Check In 3 Submit` |
| the judge's screen | **UNKNOWN for this platform**; fully documented for Devpost | §1.4 |
| the scoring shape | **MEASURED as a recommendation**, not as a rule | `judging-plan.md`, quoted in §1.5 |

**MEASURED-ABSENT**, and it is the most important absence in this file: across `guide.mlh.com` (all 109
indexed pages), `hackdays-guide.mlh.com` (all 22) and the two live event pages, there is **no judge role,
no judge dashboard, no judge instructions, and no page describing what a judge opens first**. The only
review surface MLH documents is the organiser's, and its own caption is: *"Use Manage Submissions on the
MLH.com event page for projects, exports, and judging."* Anyone who tells you the judge view is published
is describing Devpost.

### 1.2 The gate before the form

**MEASURED**, `hackdays-guide.mlh.com/run-your-event/project-submissions.md`, verbatim:

> 1. Sign in using the account used to register for the event, and complete event check-in when required.
> 2. Select **Challenges** in the "View and submit challenges for this event" banner.
> 3. On the MLH.com event page, select **Submit a Project** when the button is enabled.

**MEASURED**, live event page at 22:30Z, from its embedded props: `"viewerCanSubmit": false`,
`"userParticipationStatus": null` for an anonymous viewer. So the form is gated on registration **and**
check-in, and the submission route itself answers **302 → sign-in**.

### 1.3 The six fields, in the order the platform asks for them

**MEASURED**, same guide, steps 4–7, verbatim:

> 4. Enter the project link, project name, description, and technologies used.
> 5. Add a demo URL if the team has one.
> 6. Under **Which challenge(s) are you submitting to?**, select every partner and local challenge the project is eligible to enter.
> 7. Select **Submit Project** before the deadline.

Five content fields plus the track selector. **The demo URL is the only one the guide calls optional**
("if the team has one"), which matters for a build with no hosted demo: the form does not assume one.

**MEASURED**, live page props at 22:30Z:

| Prop | Value | What it fixes |
|---|---|---|
| `shortDescriptionLimit` | `160` | a 160-character short description exists; this is the line a listing card would show |
| `projectFirstSubmission` | `true` | one project, submitted once |
| `submissionsCount` | `36` | entries at 22:30Z, and it is rising |
| `submissionEndsAt` | `2026-11-08T18:00:00Z` | the machine deadline |
| `lateDraftsOpen` | `false` | see §1.6 |
| `galleryPath` | `null` | there is no gallery route while judging |

**MEASURED**, a category page: *"One submission can enter every category it qualifies for."* Entering is
free and is not scarce.

**UNKNOWN:** which of the five fields the form marks required. The form is behind sign-in and this pass did
not sign in. The guide's phrasing names only the demo URL as conditional, and that is the guide's wording,
not a field-level requirement list.

**A concrete gap this exposes, offered as an option and not decided.** The 160-character field has nothing
written for it in `records/SUBMISSION-PACK.md`; its §2.2 description is a 300-word paragraph. Two candidate
lines, both under the limit, both derived from text already committed:

- *"Organizer pricing from the resale record: what tickets actually resold for, and the floor that record supports."* — **111 characters**
- *"Ticketpath reads a ticket's resale record and prices the primary seat from it, refusing what the record cannot support."* — **119 characters**

Which one, or neither, is his.

### 1.4 What a judge's screen is

**For this platform: UNKNOWN.** No page says whether the video autoplays or is a link, whether the judge
gets the whole list or an assigned subset, or whether the platform collects a score at all.

**For Devpost, which is what most MLH events still use, it is fully documented** — `help.devpost.com/article/103-how-to-judge-an-online-hackathon`, verbatim:

> The only way to get to your judging dashboard is to click Start Judging in the email you receive from Devpost.

> The judging dashboard lists the detailed judging criteria that you'll use to judge submissions. It also displays your progress. When you're ready to start judging, click the big Start Judging button to be directed to the first submission.

> On the bottom right side panel of each submission, you will find a Rate the Submission box. For each item in the list of criteria, you will assign a rating of 1-5 stars.

> 1 star is the lowest rating and 5 is the highest rating. (There is no other mechanism for judges to provide feedback.)

So on the documented platform: **a private emailed link, then one submission at a time, then five stars per
criterion, and no free text at all.** Sections are the judge's whole vocabulary; there is nowhere to write a
sentence, which means the video is the only place an argument lands.

### 1.5 How much time, and how many entries

**MEASURED**, `guide.mlh.com/general-information/judging-and-submissions/judging-plan.md`, verbatim:

> $$t =$$ Time taken by a Judge per project (MLH recommendation: 4 mins per project. 2 minutes for presentation + demo, 1 minute for questions from judges and score compilations, and 1 minute for judge travel)

> $$n =$$ Number of Judges for each project (or number of rounds of judging per project)\ (MLH recommendation: 3 rounds per project)

> The goal is to have each project seen at least 3 times, but not have judges see the same "sets".

The same page then contradicts itself, verbatim, in the day-of debrief: *"**They only have 3 minutes per
team**. You want the process to be fair..."* The 4-minute figure is the one the staffing table is computed
from, so it is the one to plan against; **CONFLICT recorded, not resolved.**

**Entries per judge, computed from MLH's own worked example, not published as a number:** 175 projects × 3
rounds ÷ 18 judges ≈ **29 project-visits per judge**, at 4 minutes each ≈ 117 minutes, inside a 120-minute
block. That is arithmetic on their published figures.

**MEASURED-ABSENT:** how many projects an MLH-run digital event gives one judge, how many minutes MLH itself
allocates, and how many rounds it runs. All of the above are recommendations to organisers of member events.

**What the 4-minute number means for a recorded video — ASSERTED:** the "2 minutes for presentation + demo"
was written for a live stall. For an asynchronous video the judge watches a file of a length he or she
controls, and the 2:00 cap is what makes the video and the slot the same size. That mapping is my reading;
MLH does not state it.

### 1.6 What is not shown at all

| Not shown | Evidence |
|---|---|
| a gallery, a public list of submissions, or any per-project public page | `galleryPath: null`; `/events/solana-hackathon/submissions` → **404** |
| the gallery even after winners are announced, unless winners are published | *"Making winners public also publishes the event's project gallery, including non-winning submissions."* (`closing-ceremony-and-winner-declaration.md`) |
| a judge reading your code during judging | standard rules exclude code quality from the criteria outright; code inspection is a post-judging organiser check on winners (`cheating-check.md`) |
| any comment, chat or feedback channel on the platform | **MEASURED-ABSENT** on MLH.com; on Devpost, *"(There is no other mechanism for judges to provide feedback.)"* |
| an edit that reaches judges after the deadline | `lateDraftsOpen: false` — *"While it is off, late work is saved as a draft for an organizer to finalize."* |
| a live URL requirement | nothing in the standard rules requires a deployment; the Solana partner page asks for *"code, configuration, transaction, deployed program, or other appropriate evidence"*, and names the README |

One asymmetry worth recording: a demo URL is optional on the form, but **the Solana partner page names the
README as the place a judge is told to look for the integration** — *"Ask the team to identify the
integration in its README..."*. That is the cheapest document change available and it is not a score item;
it is what the sponsor tells the judge to check.

### 1.7 The consequence, stated as inference

**ASSERTED.** A judge's total exposure is: the title, the 160-character line, the description body, the
technology list, two links, and the video. There is no second surface, no follow-up question, no
opportunity to be interesting in a repo nobody clones during judging. Everything the entry is, is what
those six fields and one file say it is.

---

## 2. Past submission videos, read as artefacts

### 2.1 What could be measured, and what could not

Five Solana-prize winners at MLH-family events in October 2026, all named in `records/findings/23-…` §4.2,
were opened again for their **video**, not their chain use. What is obtainable per video: exact duration
(from the player's own `lengthSeconds`), upload date, channel, the description, and any chapter markers the
uploader wrote. **What is not obtainable from this host: transcripts and frames.** YouTube's caption
endpoint returns zero bytes even with the signed URL, so there are **no quoted opening lines** and **no
verified statement about live-screen versus slides** for any of the five. Do not let this file be read as
though the videos were watched.

### 2.2 The five, with durations

| Project | Event / prize | Video | Duration | Structure evidence |
|---|---|---|---|---|
| **Weenie Beanie** | SwampHacks XII — MLH Prize: Best Use of Solana | `https://www.youtube.com/watch?v=feb1Xajo4ik` | **5:38** | none: no chapters, empty description |
| **SolGPU** | Knight Hacks IX — [MLH] Best Use of Solana | `https://www.youtube.com/watch?v=EDPen_Iu5QY` | **1:57** | none |
| **LOKA Pay** | Hacklanta 26 — [MLH] Best Use of Solana | `https://www.youtube.com/watch?v=S_rAXEYMkOI` | **2:18** | **a nine-beat chapter list, published by the uploader** |
| **school of thought** | OxHack 2026 — [MLH] Best Use of Solana | self-hosted, not YouTube | **unknown** — host returns a Cloudflare 530 to this machine | none |
| **BackFill** | Gator Quant Hacks — MLH: Best Use of Solana | `https://www.youtube.com/watch?v=mngZNkjJhEY` | **1:04** | none |

Two of the four measurable videos sit close to two minutes (**1:57** and **2:18**); the other two are **1:04**
and **5:38**. Note what that means precisely: the 2:18 video is **eighteen seconds over** this event's own
2:00 cap and won its prize at a different MLH event anyway, and the 5:38 video won at two and a half times
the length. So two minutes is a strong norm and not a gate — but the norm is what MLH publishes, and the
2:00 cap is this event's published rule, which is a different kind of thing.

### 2.3 LOKA Pay, beat by beat, because it is the only one whose structure is published

Source: the video description at `https://www.youtube.com/watch?v=S_rAXEYMkOI`, corroborated by
`https://devpost.com/software/loka-pay`. The uploader wrote the chapters himself, so this is his structure
and not an inference from a watch.

| Time | Beat |
|---|---|
| 0:00 | an iPhone with zero bars pays a shop |
| 0:29 | the cheat: the same money, a second shop |
| 0:39 | shop B accepts it offline |
| **0:51** | **refused on chain, error 6011** |
| 1:04 | why it matters |
| 1:21 | built on LOKA, public on devnet |
| 1:35 | Android too: the same checks |
| 1:45 | a phone call reads it out loud |
| 2:01 | check it yourself |

Three things in that description are directly reusable as facts, not as style:

1. **The failure is beat two, at 0:51 of 2:18.** A judge who stops at sixty seconds has seen the product
   succeed and fail correctly. The refusal is not saved for a caveat at the end.
2. **The pitch is at 1:04, after the demo.** "Why it matters" arrives 64 seconds in, which is the opposite
   order of a deck and the same order MLH's own guide asks for.
3. **Provenance is asserted to the minute**: *"Every phone shot is a real screen recording from Saturday
   Oct 10, 2026, 9:10 to 9:12 PM. Sandbox test tokens only, no real money."* and both transactions are given
   as explorer URLs with `?cluster=devnet`. That is answering MLH's published cheating check (§3, item 10)
   before it is asked.

The description also volunteers three limits: an emulator take for the Android shot, a Bluetooth path that
has not carried a payment, and a blurred face.

### 2.4 What the winners share

Source-stated first, then inferred, and the line between them matters.

**Stated.** MLH's organiser guidance asks for two minutes, and for a demo rather than a presentation (§3).
The event's rules cap the video at 2:00 and require the hackathon's name at the start (§1 of
`records/findings/17-…`). Measured durations: two of the four sit near the envelope, one runs 18 seconds past
it, one is half its length. The envelope is a norm with real exceptions, not a filter.

**Stated, by the sponsor whose prize they won.** Midnight's own winners post, read in the publisher's
Japanese translation (`https://note.com/midnight_jpn/n/nbc5d338ae2be`), lists completed layers, deployment
and a one-sentence use case as what the winners had in common, and says of the field: *"we often saw cases
where the frontend was only half finished"* and, of 84 teams, only two reached a public network.

**Inferred (ASSERTED).** Four patterns run across the artefacts:

- **One thin, checkable chain artefact, shown as a link or a code, not asserted.** Two of the five deployed
  a custom program; the others used a memo or an SPL primitive, and `records/findings/23-…` §4.1 measured
  that four of five Solana prize winners at large did not deploy a program of their own.
- **The written submission carries the architecture; the video carries the demo.** All five have long Devpost
  write-ups; the memorable video is the short one.
- **No opening title card, no team slide, no agenda.** Nothing in the published descriptions suggests a
  preamble. LOKA starts on the product doing the impossible thing.
- **Claims are scoped to what ran.** LOKA names its emulator take and its unexercised path; BackFill
  publishes all eleven strategies including the nine that lost money.

### 2.5 The losing side, stated by organisers rather than by me

The honest finding first: **no published post-mortem of a rejected Solana or MLH entry was found.** With the
search CLI dead, that is a search failure and must be recorded as unresolved, not as absence. What exists is
organiser-side statements naming the failure modes:

| Failure | Source's words |
|---|---|
| the video is a presentation | *"Their video should be a demo of their hack, not a presentation."* — `judging-plan.md` |
| the video argues the business case | *"It is important to mention to your judges about the judging criteria and not to focus on the business aspect of the hackathon. This highly separates a hackathon from a startup contest."* — `judges-communication-and-recruiting.md`; and *"rarely do those people win hackathons because they spent their time creating a product rather than awesome technology"* — `judging-plan.md` |
| half-finished interface, nothing on a public network | Midnight's post, §2.4 |
| a link nobody outside the team can open | *"Missing permissions... This is the single most common fatal mistake"* — Superteam, a different competition, `https://tr.superteam.fun/colosseum/submission` |
| a repo link offered as the demo | *"A repository link isn't a demo. There must be something a judge can watch working."* — same |
| reused or off-weekend footage | MLH's published cheating check, §3 item 10 |

The first two are the sharpest available facts for this entry, because they cut against the shape this
project's material naturally takes: a 24,000-line research record is exactly the kind of thing that becomes
a narrated tour, and "here is our market" is exactly the thing MLH tells judges to discount.

### 2.6 What that means for a 1:56 video — two facts, no instruction

- **The refusal belongs in the first minute, not at the end.** The one comparable winner put its on-chain
  refusal at 0:51 of 2:18 and the pitch after it.
- **The written half does the technical argument.** The video's job is a judge seeing a thing work, plus one
  artefact they can check. Everything else in the record is for the judge who opens the repo afterwards,
  and for the organiser's post-judging check.

---

## 3. Video practice, in the publishers' own words

Labels: **[THIS EVENT]** is a rule of this hackathon; **[MLH]** is MLH guidance to organisers, which is
advice and not a rule; **[OTHER]** is a different competition and is labelled so every time.

| # | Directive | Quote | Source | Label |
|---|---|---|---|---|
| 1 | it is a demo | *"Their video should be a demo of their hack, not a presentation."* | `guide.mlh.com/…/judging-plan.md` | [MLH] |
| 2 | two minutes | *"we recommend having hackers submit 2 minute videos on your submission platform for the judges to review"* | same | [MLH] |
| 3 | ≤2:00, made this weekend, hackathon named at the start, public for ever | the six digital submission rules, quoted verbatim in `records/findings/17-…` §3.7 | `raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | **[THIS EVENT]** |
| 4 | open on what it is | *"Be sure to explain what your app does (and if making the video for a specific hackathon, how it addresses the hackathon) in the first few seconds of your video."* | `help.devpost.com/article/84-video-making-best-practices` | [OTHER] |
| 5 | a screencast, not a marketing film | *"we recommend creating a screencast (a video screen capture with audio narration)... without the gimmicks"*; *"Snazzy marketing videos are great for promotional purposes, but they don't help others understand and evaluate your app."* | same | [OTHER] |
| 6 | localhost is a legitimate demo surface | *"Demo your project by running it on a localhost."* (a participant Devpost published) | `info.devpost.com/blog/6-tips-for-making-a-hackathon-demo-video` | [OTHER] |
| 7 | show it running, multiple inputs | *"Show a demo of the product running by using some input. Show what it does as much as possible"* | same | [OTHER] |
| 8 | do not speed up the audio | *"Don t try to pack in way too much information or speed up the audio to fit within a time limit."* | same | [OTHER] |
| 9 | put a clock on screen | *"Are their Timestamps over the weekend when they run the demo in any video/screen captures?"*; *"Was the video published over the weekend?"* | `guide.mlh.com/…/cheating-check.md` | [MLH] |
| 10 | public, not private | *"if it's private, the judges won't be able to access it!"*; YouTube defines public, unlisted and private separately | Devpost blog; `support.google.com/youtube/answer/157177` | [OTHER] |
| 11 | the video attached is frozen at the deadline | *"To change the video judges see, edit your submission before the submission deadline."* | `help.devpost.com/article/85-video-requirements` | [OTHER] |
| 12 | upload early; processing is slow | *"uploading your video could take anywhere from a few minutes to several hours or more"* | `help.devpost.com/article/84-…` | [OTHER] |
| 13 | a clear narrative beats polish | *"A clear and well-structured narrative is more valuable than professional video editing"* | `blog.colosseum.com/perfecting-your-hackathon-submission/` | [OTHER] |
| 14 | the demo video is "the how" | *"While the pitch video is for explaining the why, the technical demo is about the how... It should be technical, direct, and specific to implementation."* | same | [OTHER] |
| 15 | overrunning is the first listed mistake | *"Exceeding the 3 minute time limit"* | same | [OTHER] |
| 16 | no slides | *"Keep it short, interesting (no slide shows/decks), and visually engaging."* (participant) | `info.devpost.com/blog/6-tips-…` | [OTHER] |

### 3.1 Two conflicts, named and not smoothed

- **Decks.** Item 16 says no slides. The Colosseum recap (item 13) treats a voiceover over a slide deck as
  acceptable and says narrative beats editing polish. They are not literally contradictory, but they point
  opposite ways for a team with two hours, so both are recorded here and the choice is his.
- **Cut the messy parts, or show the reasoning.** Devpost's help page says *"Edit out the messy stuff, if you
  can"*; Colosseum's recap says *"Judges are particularly interested in the reasoning behind these
  decisions"*. A refusal path that is part of the architecture sits on the second side of that line, and
  `records/findings/23-…` §5.1 T2 already treats it as evidence rather than mess. The conflict is real and
  it is the one that decides whether the cap-check refusal goes in the video at all.

### 3.2 What is not published, so nobody invents it

**MEASURED-ABSENT across every source fetched:** any retention figure or "seconds before a judge stops";
whether judges watch muted; whether they watch at speed; whether a limitations section helps or hurts
(only disclosure *requirements* with penalties are published); whether a verifiable number on screen helps;
whether to show a wallet signature; whether an **unlisted** video satisfies a rule worded **public**;
and this event's own statement of entries per judge.

One more, recorded because it is the sort of thing that gets repeated as fact: a participant claims on a
Devpost page that a video must be marked "not made for kids" or judges cannot open it. YouTube's own page on
that setting states the COPPA requirement and what the setting changes, and **does not support the causal
claim**. The action is right for an unrelated reason (a ticketing demo is not made for kids); the reason
given in that quote is not corroborated.

---

## 4. The four things this build could put on screen

Everything in §4.1 was measured today at 22:29Z–22:31Z, on this machine, from the tree at `33d95b3` plus the
working tree.

### 4.1 What is actually there

| Surface | State today | How measured |
|---|---|---|
| the console page | renders, **13,726 bytes**, 1,174 words of visible text, no JavaScript | `200` from a local instance on a spare port, page saved and its markup stripped |
| a per-ticket price path | `GET /api/tickets/tkt_syn_0001/resale-history` returns four ledger rows: `issue` (no price), `sale` 1.18 SOL, **`transfer` with `priceLamports: null`**, `sale` 0.94 SOL, plus `stats` (2 sales, 3 transfers, avg markup 600 bps) and the fixture label; every row has `signature: null`, `slot: null` | `200` from the same instance, body read in full |
| the console's own ticket view | **none.** The console page renders no custody path, no per-ticket block, and the word "custody" does not appear on it | same page, searched |
| where the number sits | the recommendation begins at **character 2,572 of 7,422** of visible text, after the fixture banner, the event list and the tier/regime block | same |
| the chain slot | `[DEVNET]` panel prints *"No devnet transaction has been recorded"*, *"No program is deployed on any cluster"*, and the quote it *would* commit, unsigned | same; `ticketpath/console/page.py:364-409` |
| the simulated state machine | `?sim=1`, **14,634 bytes**, five `[SIMULATED]` lines including `cap · refused · 6010 E_CAP_EXCEEDED — 1380000001 lamports is above the ceiling 1380000000 lamports`, `unstaged · refused · 6009`, `unverified · refused · 6012` | `200`, page saved and read |
| the cap-check on a real validator | a **pair of signatures** one lamport apart: `slot 1150, Status: Ok` and `slot 1134, Status: Error processing Instruction 0: custom program error: 0x177a (6010 = CapExceeded)`, with program log lines `ticketpath: cap admitted …` and `ticketpath: cap exceeded …` | `records/findings/18-onchain-install-and-test.md:285-313`, `:370-385` |
| the chain artefact file | exists, and its cluster is **`localnet`**; `explorer.program`, `explorer.mint`, `explorer.transaction` are **all null**; the accepted and refused transfers carry slots 204 and 206 and a `custom program error: 0x177a` | `records/devnet-artefacts.local.json` (untracked, git-ignored) |
| what the console does with that file | the loader reads `records/devnet-artefacts.json` (not the `.local` file), and the explorer link is built **only** when the state is verified, the cluster is `devnet` and the quote hash matches — otherwise no link is emitted and the page says a local rehearsal is not devnet evidence | `ticketpath/console/page.py:415-423`; `ticketpath/orchestrator.py:583-612` |
| the research record | **37 findings files, 24,499 lines**, plus six standing records; README is the shop window a judge reaches from the form's project link | `wc -l`, `git ls-files` |
| the record's own safety check | `python3 tools/public_safety.py check --tracked` exits non-zero: **64 hits in 9 tracked files**, all under `records/` | run at 22:29Z, same figure `records/findings/23-…` §6.3 reported |

### 4.2 Option: the cap-check refusal

Two variants, and they are not the same artefact.

**A1 — the local-validator pair, on camera.** A terminal shows the accepted transfer at the cap, then the
refused one a lamport above it, with `0x177a` and the two program-log lines.

- **What it proves:** a real BPF program, deployed to a real validator, refusing a real transaction, with a
  signature on the refusal rather than a preflight error. It is the strongest evidence in the tree.
- **Cost:** the ledger from that run is still on disk (965 MB measured now; `records/findings/18-…:345`
  recorded 1.5 GB at the time), so it is a restart and two commands, not a build. Budget 20–30 minutes
  including a rehearsal.
- **Risk 1, mechanical:** a refused transfer *that fails preflight never gets a signature* — that is why the
  project wrote its own `transfer-checked` client with `skip_preflight: true` (`records/findings/18-…:307-313`).
  A generic CLI refusal therefore shows an error with **no** signature, which is a weaker frame.
- **Risk 2, and it is a rule collision:** `records/SUBMISSION-PACK.md` §1.4 says no terminal on any frame.
  Skeleton A is only possible if that rule is lifted. **Both rules are the operator's and this file does not
  resolve them.**
- **Risk 3:** a terminal on camera invites the "is that real?" question, which is answered only by the label
  "local validator" and by not implying it is on a public cluster.

**A2 — the in-page `[SIMULATED]` state machine.** `?sim=1`, scrolled to the five lines.

- **What it proves:** that the arithmetic and the ordering of the refusal exist and are labelled as a
  simulation. Nothing about a cluster.
- **Cost:** zero. It is already recorded in the page.
- **Risk:** a judge who reads `[SIMULATED]` as "not built". Mitigation is one sentence, and the page's own
  caption already says what it is: *"A Python mirror of the state machine... it proves the arithmetic and the
  ordering, not that Token-2022 calls a hook."*

### 4.3 Option: an explorer link

**There is no explorer link today.** The only signatures in any artefact file are local-cluster: the artefact
says `localnet` and every explorer field in it is null. **One caveat this pass found in the working tree, and
it is another session's work rather than mine:** `tools/devnet_publish.py` was being rewritten while this file
was written, and its own docstring now records that *"A devnet run deployed the program and minted a mint,"
and then died on an RPC read — which is why the rework writes a git-ignored resume file so a rerun reuses the
same mint instead of creating a second one. No resume file and no `records/devnet-artefacts.json` exist on
disk at 22:35Z, so **whether that deployment is still live, and at which address, cannot be established from
anything readable here.** It is worth ten minutes to settle before the video is planned: if a program id
survives on devnet, an explorer link exists and this option collapses into a copy-paste. A link appears in
the console only after the devnet publish runs and the artefact's quote hash matches the quote on screen —
otherwise the page renders `unverified`, not a link.

- **What it would prove:** a public, third-party-checkable transaction with a block time — `records/findings/23-…`
  §3.5's four-item materials test, which currently scores 0 of 4.
- **Cost:** about 45 minutes of script runtime plus the operator's faucet step, already costed in
  `records/findings/23-…` §5.1. **The funding step is his, and it is a rule as well as a permission:**
  `https://faucet.solana.com/` states *"AI agents should not use this faucet"*.
- **Risk 1, and it is the one that matters on camera:** an explorer URL for a localnet or placeholder
  signature returns "not found". `records/SUBMISSION-PACK.md` §1.4 already names this: *"Any Solana Explorer
  page for a `SYN...` mint address. No account exists; the page will say so."* A 404 on camera is worse than
  no link, because it converts an honest absence into an apparent falsehood.
- **Risk 2:** a devnet run in the last hours eats the recording window. It is a separate job from the video.
- **Risk 3:** if it lands, the console's `[DEVNET]` slot becomes true only when the artefact's quote hash
  matches the quote the page recomputes — a mismatch renders `unverified`, not a link. That is a feature and
  it is also a way to lose an hour on the day.

### 4.4 Option: the pricing console

**Verified today, not assumed.** 200, 13,726 bytes, 1,174 visible words, no script, and every figure carrying
a badge (`[FIXTURE]`, `[EXACT]`, `[UNVALIDATED]`, `[REFUSED]`, `[SIMULATED]`, `[DESIGN]`, `[DEVNET]`).

- **What it proves:** a working product, a real decision, a real refusal, and a design that never contradicts
  its own labels. That is three of the four published criteria (Technology, Design, Completion) in one surface.
- **Weakness, measured:** the recommendation begins about 35% of the way into the visible text, behind a
  fixture banner, an eight-event list and a regime block. On a 1280-wide screen and no scroll, the number is
  below the fold — the same conclusion `records/findings/23-…` §5.2 D1 reached from a different measurement.
  A video can scroll where a judge's first glance cannot, so this costs the video less than it costs the page.
- **Risk:** it runs on a loopback address; nothing here is clickable by a judge. That is allowed — the form's
  demo URL is optional and a Devpost-published tip tells teams to demo from localhost (§3 item 6) — but no
  frame may claim it is hosted.

### 4.5 Option: the research record

- **What it proves:** the Learning criterion, which `records/findings/23-…` §3.4 scores highest at 18/25, and
  which no other surface can carry.
- **Strength as an artefact:** it is not a claim, it is 37 dated reports with sources, including a rules
  recheck that corrected itself in public and a cap argument that was withdrawn when a check contradicted it.
- **Weakness, measured:** 24,499 lines is not a screen; a judge will not read it, and a video that tries to
  summarise it becomes the narrated tour §2.5 names as a failure mode.
- **Risk, measured today:** `tools/public_safety.py check --tracked` still reports **64 hits in 9 tracked
  files**, all under `records/`. Those are quoted measurements (a process id in a state table, an absolute
  path inside a command's output) and they are published. Pulling `records/` into frame invites exactly the
  reading the project's own checker calls an incident, and fixing it is the operator's call under `AGENTS.md`.
  So: **cite the record, do not tour it**, until he decides otherwise.

### 4.6 What the four combine into, honestly

| Combination | Chain evidence | Product evidence | Learning | What it cannot survive |
|---|---|---|---|---|
| console + in-page `[SIMULATED]` refusal | none | strong | a sentence | a judge who reads `[SIMULATED]` as "nothing works" |
| console + local-validator pair | strong, and explicitly not public | strong | a sentence | a judge who does not know what a local validator is |
| console + devnet explorer link | public and checkable | strong | a sentence | a devnet publish that does not land before recording |
| any of the above + record tour | unchanged | weakened: less screen time for the product | strong | the five-minute budget and the 2:00 cap |

---

## 5. Three storyboard skeletons, as options

**No decision is made here.** Each is a different answer to "what is this video about", each fits 2:00, and
each is costed in what it gives up. A fourth option already exists — `records/SUBMISSION-PACK.md` §1.2's
six-beat console-first script, target 1:56 — and §5.5 compares it rather than replacing it.

### 5.0 Rules that bind all three

- **First spoken sentence names the hackathon** and the product. That is a published rule, not style
  (`records/findings/17-…` §3.7 rule 3).
- **The product is on screen before any context.** Two independent organiser sources say the opening seconds
  are where the app is explained (§3 items 1 and 4).
- **A clock is visible in the capture** and the video's upload date is inside the weekend (§3 item 9).
- **Every frame's numbers keep their badge.** A badge-free crop is a wrong crop.
- **Word budget:** at 140 words per minute, **2:00 is 280 words**. Every skeleton below sits at 240–265
  spoken words with the rest spent on transitions, which is what the pack's own timing note already does.
- **Nothing invented.** No invented devnet address, no simulated number presented as a measurement.

### 5.1 Skeleton A — "The pair"

*The video is about a rule the chain enforces, and the check is the last third.*

| Time | On screen | What must land |
|---|---|---|
| 0:00–0:08 | console, top of page, fixture strip in frame | the hackathon named, the product named, one sentence |
| 0:08–0:26 | console event block: 12 resales, 22.03 SOL, +12% against a +15% cap | the organizer priced once and the market repriced the seat |
| 0:26–0:46 | console, scrolled to the recommendation | `at least 1.38 SOL`, `[UNVALIDATED]`, "a floor, not an estimate", the cap is a resale ceiling |
| 0:46–1:14 | terminal: accepted at the cap, then refused one lamport above, `0x177a`, both program-log lines, labelled **local validator** | the chain refuses the price the rule forbids, with a signature on the refusal |
| 1:14–1:30 | console `[DEVNET]` slot | nothing is deployed; this ran on a local validator; the file and the script are in the repo |
| 1:30–1:46 | console, `What the engine refuses` | three refusals, each naming the missing observation |
| 1:46–1:54 | end card: project, one line, repo path | where the code and the run steps are |

**≈ 258 spoken words, 1:54.** Optimises Technology and Completion. **Requires** lifting the pack's "no
terminal" rule; **requires** a working local validator on the day, which exists but must be rehearsed.
**Gives up:** the Design axis is carried by only two static screens.

### 5.2 Skeleton B — "One ticket's life"

*The video is about a single seat, followed from issue to resale, and the console is where it ends.*

| Time | On screen | What must land |
|---|---|---|
| 0:00–0:08 | the resale-history JSON for one ticket, four rows visible, one of them unpriced | the hackathon named, the product named |
| 0:08–0:34 | the same four rows, the **`"priceLamports": null`** transfer held in frame | a ticket moves without a price, so the record has a hole in it, and that hole is the product's subject |
| 0:34–0:58 | roll-up: 12 sales, 22.03 SOL, median 1.38, 67% resold, 11 holders | this is what the organizer never sees |
| 0:58–1:20 | console: floor, cap's role, badge legend in frame | one decision, its label, and why it refuses an upper bound |
| 1:20–1:38 | `What the engine refuses` | three refusals and the missing observation for each |
| 1:38–1:50 | `[SIMULATED]` state machine OR the local-validator pair, whichever is true on the day | the rule exists in code, and what was run is what is claimed |
| 1:50–1:58 | end card | repo and run steps |

**≈ 250 spoken words over 1:58** (about 127 words per minute, slower than the pack's 140, which buys the two
screen changes). Optimises Design and Completion, and it is the only skeleton whose spine is a
sentence a non-specialist can repeat ("one ticket, every hop, with and without a price"). **Gives up** the
chain evidence to a 20-second block.

**One screen choice inside this skeleton, and it matters.** The path can be shown two ways:

- **from this repository**, as the `resale-history` JSON measured in §4.1 — a browser's own JSON view, four
  rows, one with `"priceLamports": null`. It is this build's own output and carries no prior-work exposure.
- **from the platform-UI copy**, as the custody-trail page — nicer to look at, and it is exactly the screen
  `records/findings/17-…` §6 R1 calls the entry's largest disqualification exposure, because it is an
  existing platform's interface and not this weekend's work. `records/findings/23-…` §3.2 D6 says the
  Design credit should be earned by the console for that reason.

The first is what the record supports; the second is the one that has to be framed in one spoken sentence if
it is used at all. That framing decision is his, not this file's.

### 5.3 Skeleton C — "What it refuses, and why that is the product"

*The video is about a pricing engine that declines to answer three of four questions, and shows the fourth.*

| Time | On screen | What must land |
|---|---|---|
| 0:00–0:08 | console, `What the engine refuses` block already in frame | the hackathon named, the claim: a price the record cannot support |
| 0:08–0:30 | the four refusal rows, one at a time | `not_identified` (no asking prices are recorded), `no_demand_response`, `no_fee_model`, `cap_mass_dominates` |
| 0:30–0:56 | the recommendation block | what the record *does* support: a floor, integer lamports, an exact ceiling, a labelled band |
| 0:56–1:14 | roll-up numbers | the evidence behind the floor: 12 sales, 8 of 9 at the ceiling |
| 1:14–1:34 | the cap check, in whichever form is true | the rule is code, not prose |
| 1:34–1:50 | repo tree or README section on what is not done | the limits are written down, not discovered |
| 1:50–1:58 | end card | where the code and the record are |

**≈ 244 spoken words over 1:56** (about 126 words per minute). Optimises Learning and distinctiveness — no other entry will be about a model
declining to fit. **Risks, and they are real:** it is the talkiest of the three; MLH tells judges to discount
the business framing, and "what we refuse" is a frame rather than a demo; and a judge who gives it 40 seconds
sees refusals before seeing a product. Mitigation is ordering, not wording: the first frame must be a working
page and the first sentence must be what it does.

### 5.4 Side by side

| | A "The pair" | B "One ticket's life" | C "What it refuses" |
|---|---|---|---|
| first 10 s shows | a working page | a working page | a refusal block |
| chain evidence | strongest available today | 20 s | 20 s |
| needs a terminal | yes | optional | optional |
| needs the local validator | yes | no | no |
| Design axis | 2 static screens | strongest | medium |
| Learning axis | one sentence | one sentence | strongest |
| riskiest dependency | the validator restart on the day | which ticket screen is used (see §5.2) | a judge's patience |
| words | 258 | 250 | 244 |

### 5.5 The fourth option, already written

`records/SUBMISSION-PACK.md` §1.2 is a six-beat console-plus-frontend script, 264 words, target 1:56, with
every screen fetched and every figure verified at the time it was written. Compared with the three above it
is closest to skeleton B, with one material difference: it opens on the platform's resale-analytics page
rather than on a per-ticket path, and its beat 5 uses the platform-UI custody card. It is not re-timed here
because re-timing it would be a rewrite of the pack, and the pack's own note says the timing was checked
against the running console. If he picks A or C, §1.2 becomes appendix material, and it should be marked
obsolete the way §1.5 already is, rather than deleted.

---

## 6. Before the record button: the mechanical list

Cheap, checkable, and each one is a published rule or a measured fact rather than advice.

1. **Registered and checked in.** The form is gated on both; an un-checked-in teammate may not be able to
   submit at all (`records/SUBMISSION-PACK.md` §3 item 12).
2. **The 160-character line exists before the form is opened.** The field is real and nothing is written for it (§1.3).
3. **Visibility is public, not unlisted.** Every rule sentence found says "public"; YouTube treats unlisted as
   a separate state; the video attached to a submission is frozen at the deadline (§3 items 10 and 11).
4. **Upload before the last hour.** Processing is documented as taking minutes to hours (§3 item 12), and a
   link exists before processing finishes, so the upload can start while the description is finished.
5. **The hackathon's name is in the first spoken sentence**, and the upload date is inside the weekend.
6. **A clock is visible in the capture** — the published cheating check looks for one (§3 item 9).
7. **Every link in the submission opens for someone outside the team.** That is the failure Superteam calls
   the most common fatal mistake; MLH's version is *"remove any API keys before sharing"*.
8. **No frame claims a deployment.** The console's own `[DEVNET]` slot is the sentence to keep in frame.
9. **The thumbnail** is auto-generated unless the YouTube account is verified (YouTube's own page). Do not
   plan a still that cannot be set.
10. **Do not plan around a post-deadline edit.** `lateDraftsOpen: false` at this event; a late edit becomes an
    organiser-side draft, and a post-deadline repo push is on the cheating-check list.

---

## 7. Decisions this file does not make

1. **Which skeleton**, and whether `SUBMISSION-PACK.md` §1.2 stands or becomes appendix material.
2. **The terminal collision.** The pack forbids a terminal on any frame; skeleton A needs one. Both rules are his.
3. **Whether the devnet publish is attempted before recording.** It changes what the chain block can show and
   it is a faucet action, which is his by rule.
4. **The 160-character line**: which of the two candidates, or neither.
5. **Whether the local-validator pair appears at all**, given that no explorer link can back it.
6. **Whether the research record is cited in the submission text or only in the repo.** It carries the
   Learning axis and it also carries the 64 public-safety hits.
7. **Whether to name the existing platform UI in the video**, and therefore which per-ticket screen skeleton B
   uses (§5.2) — the prior-work exposure `records/findings/17-…` §6 R1 rates as the largest in the entry.
   Nothing in this file assumes it is shown.
8. **Whether to enter the four smaller tracks**, which is the same track decision `records/findings/23-…` §7
   already lists and is unaffected by the video.

---

## 8. What is not documented, so nobody invents it

- **The judge's view on this platform.** No judge role, dashboard or instructions on any MLH doc site.
- **Entries per judge at this event**, and minutes per entry at this event. MLH's numbers are recommendations to organisers.
- **Which form fields the platform marks required.** The form is behind sign-in.
- **Whether this event requires a specific video host.** MLH's rules say public, not where; the YouTube/Vimeo/Youku
  list is Devpost's.
- **Whether an unlisted video satisfies a rule worded "public".** YouTube defines both states; no organiser page resolves it.
- **Any retention figure, muted viewing, or viewing speed.**
- **Whether a limitations section helps or hurts**, from any source, in either direction.
- **A published post-mortem of a rejected Solana or MLH entry.** Searched, not found, with the search tooling
  degraded; unresolved rather than absent.
- **The five videos' transcripts or frames.** Not obtainable from this host; §2 says so and does not guess.

---

## 9. Sources

Fetched 2026-11-07 between 22:23Z and 22:30Z from this host, no browser, no login, unless a row says
otherwise. Local files were read at commit `33d95b3` plus the working tree.

| # | Source | What it established |
|---|---|---|
| 1 | `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md` | 4 min/project, 3 rounds, the staffing formula and its 175-project example, the "3 minutes per team" contradiction, "a demo of their hack, not a presentation", the anti-startup-pitch passage |
| 2 | `https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md` | the on-screen timestamp question, the video-published-over-the-weekend question, the readme question |
| 3 | `https://guide.mlh.com/general-information/judging-and-submissions/rules-for-your-hackathon.md` | public code link, remove API keys, AI disclosure with a disqualification penalty |
| 4 | `https://guide.mlh.com/general-information/judging-and-submissions/judges-communication-and-recruiting.md` | "not to focus on the business aspect ... separates a hackathon from a startup contest" |
| 5 | `https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal.md` | the export field list a judge sees; Devpost is the most common MLH platform |
| 6 | `https://guide.mlh.com/overview/event-types/digital-events.md` | pre-recorded demos are the digital judging format |
| 7 | `https://guide.mlh.com/llms.txt` | the index that proves no judge-role or judge-view page exists |
| 8 | `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md` (last updated October 2026) | the six-field order, the demo URL optional, the register/check-in gate, the "Accept late submissions" switch, the "Demo and clarity" rubric row |
| 9 | `https://hackdays-guide.mlh.com/run-your-event/closing-ceremony-and-winner-declaration.md` | "Keep Announce Winners set to PRIVATE while judging"; publishing winners publishes the gallery |
| 10 | `https://hackdays-guide.mlh.com/partner-programs/solana.md` (last reviewed August 2026) | "identify the integration in its README and show the relevant code, configuration, transaction, deployed program, or other appropriate evidence during the demonstration" |
| 11 | `https://hackdays-guide.mlh.com/help/frequently-asked-questions-faq.md` | Hack Days must be in person, so that guide documents the platform and not this event's rules |
| 12 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | the six digital submission rules verbatim; the four equal criteria; the exclusions; small post-deadline fixes allowed |
| 13 | `https://www.mlh.com/events/solana-hackathon` (fetched twice, 22:24Z and 22:30Z) | 36 submissions, `2026-11-08T18:00:00Z`, `lateDraftsOpen:false`, `galleryPath:null`, `shortDescriptionLimit:160`, the `1 Register 2 Check In 3 Submit` strip |
| 14 | `https://www.mlh.com/events/solana-hackathon/submissions` and `/judging` | **404** both; no public gallery or judging route |
| 15 | `https://www.mlh.com/events/solana-hackathon/submissions/new` | **302 → sign-in**; the form is not readable anonymously |
| 16 | `https://help.devpost.com/article/103-how-to-judge-an-online-hackathon` | the judge's documented screen: emailed link, dashboard, one submission at a time, 1–5 stars per criterion, no free text |
| 17 | `https://help.devpost.com/article/85-video-requirements` | YouTube/Vimeo/Youku only; public required; the video is frozen at the deadline |
| 18 | `https://help.devpost.com/article/84-video-making-best-practices` | screencast over marketing; explain the app in the first few seconds; "edit out the messy stuff"; upload processing time |
| 19 | `https://info.devpost.com/blog/6-tips-for-making-a-hackathon-demo-video` | "running it on a localhost"; "don't speed up the audio"; privacy warning; the "Not for Kids" claim recorded as uncorroborated |
| 20 | `https://blog.colosseum.com/perfecting-your-hackathon-submission/` | the pitch video can decide shortlisting; overrunning is the first listed mistake; the technical demo is "the how"; narrative over polish |
| 21 | `https://colosseum.com/hackathon` | two videos with separate caps; "startup competitions"; prior-work disclosure penalties |
| 22 | `https://tr.superteam.fun/colosseum/submission` | "one reviewer working alone"; "a repository link isn't a demo"; missing permissions as the most common fatal mistake; the page's own disclaimer that its counts are third-party |
| 23 | `https://support.google.com/youtube/answer/157177` | public / unlisted / private definitions and the comparison table |
| 24 | `https://support.google.com/youtube/answer/72431` | a custom thumbnail needs a verified account |
| 25 | `https://support.google.com/youtube/answer/9528076` | the made-for-kids requirement, and what it does not say |
| 26 | `https://www.youtube.com/watch?v=S_rAXEYMkOI` (description) | LOKA Pay's nine-beat chapter list, the minute-level provenance line, the two explorer URLs |
| 27 | `https://www.youtube.com/watch?v=feb1Xajo4ik`, `…?v=EDPen_Iu5QY`, `…?v=mngZNkjJhEY` | durations 5:38, 1:57, 1:04 from each player's `lengthSeconds`; titles and channels via `oEmbed` |
| 28 | `https://devpost.com/software/weenie-beanie`, `/solgpu`, `/loka-pay`, `/school-of-thought`, `/backfill-1kpq2o` | prize lines and written submissions; school of thought's video host returns Cloudflare 530 |
| 29 | `https://note.com/midnight_jpn/n/nbc5d338ae2be` | the publisher's translated winners post: completed layer, deployment, one-sentence use case; 84 teams, two on a public network |
| 30 | `https://faucet.solana.com/` | "AI agents should not use this faucet" — already recorded in `records/findings/23-…` |

Local evidence read by this pass: `ticketpath/console/page.py`, `ticketpath/orchestrator.py`,
`programs/cap_hook/README.md`, `records/devnet-artefacts.local.json`, `docs/RUN.md`, `README.md`,
`records/findings/18-onchain-install-and-test.md`, `records/findings/21-onchain-hook-in-tree-and-publish.md`,
`records/findings/23-hackathon-score-analysis.md`, `records/findings/17-hackathon-rules-recheck.md`,
`records/SUBMISSION-PACK.md`, `tools/public_safety.py`. Measurements taken: the console served on a spare
loopback port (200, 13,726 bytes; `?sim=1` 14,634 bytes), `GET /api/tickets/tkt_syn_0001/resale-history`
(200, four ledger rows, `priceLamports: null` on the transfer), visible-word and character-offset counts from
those two pages, `wc -l` over `records/`, the validator ledger's size on disk, and
`tools/public_safety.py check --tracked`.

---

*No tracked file was changed by this pass and nothing was committed or pushed. One file was written: this
one. No command in this pass touched a cluster, a faucet, a key or another session's process; the two console
instances it served were on spare loopback ports and were stopped when the measurement finished.*

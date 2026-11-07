# 17 — Hackathon rules recheck: primary sources, fetched 2026-11-07 18:26–18:37Z

**Event:** MLH Solana Hackathon, Partnered Hackathon, online, 2026-11-06 12:00 ET → 2026-11-08 13:00 ET
(calendar payload on the event page: `20261106T170000Z/20261108T180000Z`).
**Fetch window:** 2026-11-07T18:26Z → 18:37Z. Everything quoted below was fetched in that window
unless the row says otherwise.
**Deadline being defended:** initial submission Sun 2026-11-08 **10:00 ET = 15:00Z**, final **11:45 ET**.
At the time of writing that is **20 h 25 min** away.

**Labels.** **MEASURED** = a named URL states it, quoted verbatim, fetched in the window above.
**MEASURED-ABSENT** = I read the named page in that window and the claim is not on it; absence is a
measurement, not an inference. **ASSERTED** = my reasoning, not a claim about what anyone said.
**CONFLICT** = two MLH-published documents say different things; both are named, neither is resolved here.

**No file in this repository was changed except this one. Nothing was committed. No credential,
key, absolute home path or live port is recorded here.**

> **Filename collision, noted so nobody hunts for a missing file:** `tools/check_frontend_attach.py`
> refers to `records/findings/17-frontend-fix.md`, which does not exist. This file took the `17-`
> prefix because the operator named it. If that frontend finding is ever written it needs `18-`.

---

## 0. What was already established, and is not re-derived here

Three existing records already carry the background, and this file does not restate them:

- `records/findings/02-rubric-and-scoring.md` — the four-part MLH rubric, the "not judged" list,
  the sponsor-track evidence standard, the build list for Sunday morning. **Two of its claims are
  corrected in §5 below.**
- `records/SUBMISSION-PACK.md` — the field checklist, the video script, the state of the repo.
- `../research/mlh-solana-2026/` — `04-mlh-judging-playbook.md` (MLH architecture, tiers, code of
  conduct), `03-what-wins-solana.md` (what wins Colosseum-family events), `p1a-prior-winners.md`
  (38 sampled MLH "Best Use of Solana" winners), `p1d-video-judging.md` (what the video has to do).

This pass answers the five questions asked, against the live pages, and separates what a source
says from what I conclude.

---

## 1. Submission requirements, and what "initial" vs "final" means

### 1.1 The two deadlines are real and they are different

MEASURED, event page `https://events.mlh.com/events/15200-solana-hackathon`, fetched 18:26Z, schedule
table, Sunday rows verbatim:

| Day | PT | ET | Event |
|---|---|---|---|
| Sunday | 7:00 AM PT | 10:00 AM ET | **Initial Submission due on MLH Challenges** |
| Sunday | 8:45 AM PT | 11:45 AM ET | **Hacking Ends / Final Submission due on MLH Challenges** |
| Sunday | 9:00 AM PT | 12:00 PM ET | Closing Ceremony |

The same page's header says the event runs "Friday November 6, 2026 12:00PM to Nov 8, 1:00PM EST".

### 1.2 The platform's own close is later than both, and editing is a supported behaviour

MEASURED, canonical event page `https://www.mlh.com/events/solana-hackathon`, fetched 18:28Z. The
rendered page carries:

> "Submissions close — **Nov 8, 1:00 PM EST**"   (element `data-testid="submission-deadline"`)

and a three-step progress strip: "1 Register · 2 Check In · 3 Submit · Submit Project".

MEASURED, MLH's Hack Days guide (a different MLH program, quoted because it documents the same
Challenges platform), `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md`,
labelled "Last updated: October 2026", fetched 18:34Z:

> "Every presenting project must be submitted through the event's **Challenges** page. Teams must also
> select each eligible partner challenge they are entering. Devpost, a form, or another platform does
> not replace this flow."

> "The separate **Accept late submissions** switch lets participants **submit or edit** after the
> deadline. While it is off, late work is saved as a draft for an organizer to finalize."

**Do changes after the initial submission count?** MEASURED: nothing on the event page, the rules, or
the terms says the initial submission is frozen or that a later edit is discarded. MEASURED: the
platform has an edit path by design, and its close (13:00 ET) is three hours after the initial
deadline (10:00 ET). ASSERTED: therefore the 10:00 ET initial is a checkpoint, not a freeze, and
edits made up to the platform close are part of the entry. **ASSERTED, and this is the important
part: that permission is a platform capability, not a licence to keep hacking.** MLH's standard rules
set the hard stop at hacking-end, not at platform-close:

> "11. Teams must stop hacking once the time is up. However, teams are allowed to debug and make small
> fixes to their programs after time is up. […] Making large changes or adding new features is not
> allowed."

So: text edits to the submission page after 11:45 are fine; new features after 11:45 are not.
**ASSERTED recommendation: treat 10:00 ET as the freeze for the artefact and 11:45 ET as the last
moment anything may be touched at all.** The `SUBMISSION-PACK.md` already says this; it still holds.

### 1.3 The submission fields cannot be enumerated without an account

MEASURED, 18:28Z: `https://www.mlh.com/events/solana-hackathon/submissions/new` issues
`302 → https://www.mlh.com/signin?return_to=…%2Fsubmissions%2Fnew` and serves the sign-in page.
**MEASURED-ABSENT:** the form's own field list is not published anywhere reachable logged out. The
event's Inertia payload carries `"customFields":{}` and `"viewerCanSubmit":false`, so this event adds
no custom questions of its own — the form is MLH's default.

The closest published statement of what that default asks for is MLH's required export from any
submission portal, MEASURED at
`https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal.md`,
fetched 18:31Z. Verbatim field names:

- "Project Name"
- "Submission URL (so that project can be viewed post event)"
- "About the Project"
- "Try it out / GitHub Link"
- "Did you register a domain name this weekend? If so what was the domain?"
- "Opt-In Prizes (any categories/tracks they submitted to)"
- "Built With"
- "Share feedback about any technology you interacted with at this hackathon."
- "Schools of team members"
- "Team Member Information … First / Last / Email"
- "**Which of the following GenAI tools did you use this weekend? (Required Dropdown Multiselect)** —
  OpenAI, Anthropic, Hugging Face, Llama, IBM Watson, Gemini, Gemma, DeepSeek, **I did not use
  GenAI**, and Other"
- "**Did you implement a generative AI model or API in your hack this weekend? (Required Long text)** —
  Help Text: 'If so, how and why did you use it? If not, mark your response as N/A'"

ASSERTED: the two GenAI fields are required and appear on the form we will fill. `SUBMISSION-PACK.md`
§3 item 8 already reserves a line for the disclosure. It is not optional and it is not cosmetic —
see §3.5.

> **The pack's field list is close but not identical to this.** "Try it out / GitHub Link" is one
> field, not two: the form pairs the live link with the repo. That matters for T3/T11, because the
> field can legitimately hold the repo when there is no hosted demo — the label already anticipates
> that case.

### 1.4 What the entry must also have done, beyond the form

MEASURED, `standard-hackathon-rules.md` (`https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md`,
fetched 18:26Z, HTTP 200, 8,584 bytes), "MLH Digital Event Submission Rules" verbatim:

> "4. You must have completed all registration steps for the hackathon."
> "5. You are not allowed to submit your project to other hackathons."
> "6. You can not submit a project that includes prior work."

Rule 4 is the one that is checked by a machine: the event page shows three steps, **Register, Check
In, Submit**. ASSERTED: a registered-but-not-checked-in account may be unable to submit; run the
submit path once early on Sunday rather than at 09:55.

---

## 2. Judging criteria and weights — and a CONFLICT that has to be named

### 2.1 Regime A: the four equal criteria (unchanged, re-verified today)

MEASURED, `standard-hackathon-rules.md`, "Judging Criteria" section, verbatim:

> "Teams will be judged on these four criteria for MLH digital events or MLH categories at an in person
> event. **Judges will weigh the criteria equally.**"

| Criterion | Verbatim |
|---|---|
| Technology | "How technically impressive was the hack? Was the technical problem the team tackled difficult? Did it use a particularly clever technique or did it use many different components? Did the technology involved make you go 'Wow'?" |
| Design | "Did the team put thought into the user experience? How well designed is the interface? For a website, this might be about how beautiful the CSS or graphics are." |
| Completion | "Does the hack work? Did the team achieve everything they wanted?" |
| Learning | "Did the team stretch themselves? Did they try to learn something new? […] that exploration should be rewarded." |

and the exclusions, verbatim, unchanged:

> "It's important to note that these judging criteria do not include:
> * How good your code is. […] If your code isn't production ready, we're not going to mark you down.
> * How well you pitch. Hacking is about building and learning, not about selling.
> * How good the idea is. Again, hackathons aren't about coming up with innovative ideas.
> * How well the project solves a problem. You can build something totally useless…"

plus the escape hatch: "These criteria will guide judges but ultimately judges are free to make
decisions based on their **gut feeling**".

**So the earlier finding still matches, on this document, as of today: four lines, equal weight,
idea/pitch/code-quality/problem-fit excluded.**

### 2.2 CONFLICT: a second MLH document publishes the 25/25/25/25 weighting

MEASURED, `https://raw.githubusercontent.com/MLH/mlh-policies/main/contest-terms.md`, fetched 18:27Z,
HTTP 200, 15,148 bytes, headed "MAJOR LEAGUE HACKING CONTEST ('Contest') TERMS AND CONDITIONS",
signed "This document was last updated on: August 14th, 2025". Under "**Scoring of APPLICATIONS:**"
verbatim:

> "The Applications will be judged according to the following criteria:
> 0. originality/creativity (25%);
> 0. technical complexity (25%);
> 0. adherence to Theme (25%) and
> 0. practical implementation (25%)."

This is the four-line weighting the brief carried and that `02-rubric-and-scoring.md` §3 recorded as
**MEASURED-ABSENT** ("not published anywhere I could reach"). It is published. That finding was
wrong and is corrected in §5.

**Two things keep this from being a clean resolution, and both must be stated, not smoothed over:**

1. **The document is the previous season's.** Its own first line: "The Events season shall commence on
   July 1, 2025, and shall end on June 30, 2026." This event is in the 2027 season (opened
   2026-07-10, per `04-mlh-judging-playbook.md` §1.1). The 2025-26 terms do not by their own text
   govern a November 2026 event.
2. **Its link from the registration form is now dead.** MEASURED 18:36Z: the registration checkbox
   "I have read and agree to MLH's Contest Terms & Conditions" points at `https://hackp.ac/ContestTerms`,
   which 302s to `https://mlh.link/ContestTerms`, which serves a meta refresh to `https://mlh.com/` —
   the homepage, not a terms document.

**ASSERTED, and this is the judgement the operator has to make:** the *rules* page is the live,
event-applicable document and it is explicit and detailed; the *terms* page is stale by season and
unreachable from the form. Score against the four equal criteria and treat the 25/25/25/25 line as
evidence that some MLH judges have historically been handed "originality" and "technical complexity"
language. The practical consequence is small and it points the same way either way: the two regimes
overlap on **technical complexity / Technology** and on **practical implementation / Completion**, and
they disagree only on **originality** and **Design**. Nothing in the repo should be re-planned for
originality. Design still scores under one regime and not the other, so it is upside with no downside.

### 2.3 Per-track criteria as written

MEASURED, `https://www.mlh.com/events/solana-hackathon`, 18:28Z. The page states "Prize Categories
**5 categories**". Each category has its own page; all five fetched 18:28Z, all say "One submission
can enter every category it qualifies for." and "Submissions close Nov 8, 1:00 PM EST". The complete
published criterion for each is the one line below — there is no longer rubric and no weighting:

| Category | Prize | Published criterion, verbatim |
|---|---|---|
| **Top 3 Overall** | "$1,000 USD Microgrant — $1,000 USD microgrant for each of the three strongest teams to continue building." | "The three strongest projects at the event. Every eligible submission is automatically entered. We're looking for a working product that uses Solana for something it's good at (speed, low fees, composability, on-chain ownership), not a chain bolted onto a web2 app." |
| **AI Track** | "$100 USD Digital Giftcard" per winning team member | "Best use of AI in a project." (event page long form: "Build something where AI and Solana each do real work…") |
| **DeFi Track** | "$100 USD Digital Gift Card" | "Best DeFi related project." |
| **Gaming Track** | "$100 USD Digital Gift Card" | "Best gaming related project." |
| **Best Beginner Hack** | "$100 USD Digital Gift Card" | "Best project created by Hackathon Beginners." Eligibility, from the event page: "Teams made up of **>50% first-time hackers** are eligible for this prize track." |

MEASURED: Top 3 Overall is "automatically entered" for every eligible submission; the other four are
opt-in via "Opt-In Prizes (any categories/tracks they submitted to)".

**MEASURED-ABSENT:** no page anywhere I fetched gives the AI, DeFi, Gaming or Beginner tracks a rubric,
a weight, or a judging panel description. ASSERTED: the one-liners are the whole published standard,
so these are decided by someone reading the submission against a sentence.

---

## 3. Prizes, tracks, eligibility, prior work, AI, licensing, video

### 3.1 Every prize reachable from this event

1. **The five event categories above.** MEASURED, event page and canonical page.
2. **A seasonal MLH sponsor category "Best Use of Solana" also exists and may or may not be attached
   to this event.** MEASURED, `https://www.mlh.com/events/prizes` (which is where `hack.mlh.io/prizes`
   redirects), fetched 18:27Z: "18 prize categories", and among them verbatim:
   "**Best Use of Solana — Unruggable Hardware Wallets**. The world of development is evolving fast and
   Solana is leading the charge…".
   MEASURED, its link target `https://mlh.link/solana` → `https://www.mlh.com/partners/solana`,
   fetched 18:27Z: "Integrate Solana into your next hack to **qualify for the Best Use of Solana prize
   category!**" — with no eligibility test beyond that sentence.
   MEASURED-ABSENT: neither the event page nor its five category pages mentions "Best Use of Solana",
   and the contest terms that point at that prize list are the previous season's (§2.2).
   **ASSERTED: do not count on it and do not omit it. If "Opt-In Prizes" offers it, tick it — it costs
   nothing and the entry qualifies. Do not spend a minute of build time on it.**

### 3.2 Eligibility

MEASURED, `standard-hackathon-rules.md`:

> "2. MLH Hackathons are **primarily for students**, but may also include professionals. MLH chooses to
> define students broadly. Anyone who attends a traditional school, college, or university, and those in
> bootcamps and similar programs are students. Those who graduated within the last 12 months are also
> considered students."

MEASURED, `contest-terms.md`: "The Contest is open to individuals who are at least eighteen years old
(or minors with parental permission) and meet all other eligibility requirements for the Event as
listed." And: "Employees of Sponsor and their respective parent companies… are not eligible to
participate in the Contest."

MEASURED, event registration questions (verbatim, event page 18:26Z): "I am either over 18 years of
age or have a parent's permission to participate in this event." · "I have read and agree to MLH's
Contest Terms & Conditions and Privacy Policy." · "I have read and agree to the MLH Code of Conduct."
· "In what country do you currently reside?" · web3 experience (four levels) · Solana familiarity
(four levels) · "Have you already completed the Address Form?" · two separate email opt-ins, one to
MLH and one to Solana ("We share your e-mail, name, region, country, graduation year, and LinkedIn
profile (if provided) so they can best share applicable opportunities with you.").

**ASSERTED:** student status is not a gate for the event as written — "primarily for students, but may
also include professionals". The only student-shaped gate is Best Beginner, and that is about
first-time hackers, not enrolment.

### 3.3 Team size

**MEASURED-ABSENT.** No team-size limit appears on the event page, the five category pages, the
standard rules, or the contest terms. The rules assume teams exist ("All team members should actively
participate in the event", "The eligibility of an Entrant is tied to the eligibility of the team"),
but publish no number. ASSERTED: no limit binds us; a one-person team is legal and is what
`p1a-prior-winners.md` records winning repeatedly (projects 3, 7, 14, 17 in that table are solo builds).

### 3.4 Pre-existing code — the hardest question, and the one that binds us most

Four separate statements, all MEASURED today, and they are not equally strict:

`standard-hackathon-rules.md`, Hackathon Rules:
> "6. All work on a project should be done during the period of the hackathon."
> "7. Teams can use an idea they had before the event."
> "8. Teams can work on ideas that have already been done. Hacks do not have to be 'innovative'."
> "9. Teams can work on an idea that they have worked on before (**as long as they do not re-use code
> or other project materials**)."
> "10. Teams can use libraries, frameworks, or open-source code in their projects. **Working on a
> project before the event and open-sourcing it for the sole purpose of using the code during the
> event is against the spirit of the rules and is not allowed.**"

`standard-hackathon-rules.md`, MLH Digital Event Submission Rules:
> "6. You can not submit a project that **includes prior work**."

`contest-terms.md`:
> "All work on your Application must be performed during the time window defined at the Event. **You
> may not perform any work on your Application prior to the time window defined at the Event or your
> Application will be disqualified at the sole discretion of the Sponsor.**"

Note the asymmetry: rules 7–9 permit a prior *idea*; digital rule 6 and the terms forbid prior
*work*/*materials*. "Prior research from before the event" therefore sits exactly on the line. My
answer to the operator's question — "we have prior research in this repo from before the event: does
that matter?" — is in §5.3 and §6, and the answer is that the *notes* are a documented hazard and the
*code* is the one that can actually disqualify us.

### 3.5 AI-generated code and AI disclosure

MEASURED, `standard-hackathon-rules.md`, "AI Tools and Code Gen", verbatim in full:

> "We strongly believe that the best projects will leverage AI, but ultimately be created by humans.
> 1. Teams **may use AI to assist them while coding**, utilizing tools such as code completion, code
> generation, image generation, or other similar tools.
> 2. Teams **should be honest and transparent about the AI code tools they used**. This includes
> listing them in their project submissions and answering questions when talking to organizers,
> judges, and other hackers."

**CONFLICT with the same-day `contest-terms.md`:** "Applications that have been generated by a script,
macro, bot, or any other automated means will be deemed void."

**ASSERTED:** those two sentences cannot both be enforced literally, and the AI section is the one
written for this purpose, dated later (it sits in the current rules file) and specific. The operative
risk is not the agent-built code. The operative risk is **not disclosing it**, because the form makes
the disclosure a required dropdown and a required long-text field (§1.3) and because the cheat check
looks for a build that does not match the team's demonstrated understanding (§3.6).

### 3.6 Open-source, licensing, and the code-must-stay-public rule

MEASURED, `standard-hackathon-rules.md`:
> "12. Your code must be available publicly (ideally in a git repository)."
> "13. Your code must remain public post event to be eligible for prizes. If your repo and video are
> not public, new winners may be selected."

MEASURED, `https://raw.githubusercontent.com/MLH/mlh-policies/main/cheating-response.md`, fetched
18:27Z, "Last Revised: 2025-07-23", verbatim:
> "While the codebase needs to be visible, it can (and should!) protect sensitive information. API keys,
> database credentials, and similar secrets should be kept out of the repository, typically by using a
> .gitignore file and environment variables. **The core project code, however, must be public.** Any
> attempt to circumvent the review process by hiding evidence (for example, **making a repository
> private that was required to be public**) can result in disqualification. **This includes making the
> repository private after the event ends.**"

**MEASURED-ABSENT: no licence is required.** No page I fetched asks for a LICENSE file, an OSI
licence, or an open-source grant. `02-rubric-and-scoring.md` §"The Sunday build must contain" item 1
says "Rule 12 and 13 make this [a LICENSE] a prize condition". **That is an overstatement and is
corrected in §5.** The repo has an MIT `LICENSE` as of commit `ecfae2e` (2026-11-07T17:04Z); keeping
it is harmless and good practice, but no rule turns on it.

### 3.7 The demo video

MEASURED, `standard-hackathon-rules.md`, "MLH Digital Event Submission Rules":
> "1. We require all teams to submit a **2 minute or less** demo video. Your video must be **created
> the weekend of the hackathon**."
> "2. Your video must remain public post event to be eligible for prizes. If your video is not public,
> new winners may be selected."
> "3. Your demo video must **state the name of the hackathon at the beginning** of the video. Ex. 'Hey
> I'm Sam and this is my demo for CorgiHacks.'"

MEASURED, `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md`, fetched
18:30Z: "Their video **should be a demo of their hack, not a presentation**."

MEASURED, `standard-hackathon-rules.md`, "Demos": "Pitches and presentations are discouraged. You are
not judged on the quality of your pitch or the quality of your idea. As you are judged on what you
built, you'll only hurt yourself by not showing a demo."

**MEASURED-ABSENT: no hosting platform is specified, and no spoken language is specified.** Nothing
requires YouTube, and nothing requires English. Prior work (`p1d-video-judging.md`) recommends YouTube
with an uploaded `.srt`; that is a sensible choice, not a rule.

### 3.8 Disqualification and the cheat check

MEASURED, `standard-hackathon-rules.md`:
> "14. Teams can be disqualified from the competition at the organizers' discretion. Reasons might
> include but are not limited to breaking the Competition Rules, breaking the Code of Conduct, or other
> unsporting behaviour."

MEASURED, `cheating-response.md`: the route is a review by an MLH staff member ("MLHer"), who "will
review the project in question themselves to evaluate its authenticity", then "centralize their
response by notifying our team at **cheating@mlh.io**"; "MLH may additionally issue a warning or ban";
"Hackers who repeatedly cheat or attempt to do so are permanently banned"; and "If a project is
reported post-event and found to be cheating after the investigation is concluded, the hacker/s may be
asked to return the prize/s, and a new winner will be picked." It also states: "**submission platforms
have additional information that may not be available on the public project listing.** Extra
submission questions not visible to the public may be used for extra context when completing the
investigation."

MEASURED, `https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md`, fetched
18:27Z — this is the literal list an MLHer runs against our repo, verbatim:

> "* You should check their GitHub(recommended you require this as part of the submissions)
>   * **Did they start before the event?**
>   * Is it one big commit at the beginning of the event? (Remember, some hackers are new!… One commit
>     at the end of the event is NOT a reason to DQ)
>   * Did they push changes after submissions closed? …
>   * **Does their readme mention a different event?**
>   * Is every team member contributing?
> * **Is a solo hacker making a really advanced project in a single weekend?**
> * **Are their Timestamps over the weekend when they run the demo in any video/screen captures?**
> * (If they have a video) **Was the video published over the weekend?**
> * (If they have a video) Does it mention another event? Does it mention yours?
> * Look at the team members Devpost profiles - Have they submitted this project to any other
>   hackathons?"

and the framing sentence above the list: "The following list should **not** result in an immediate DQ,
but it should prompt you to dig deeper. Talk to the team ask who worked on what part. Ask some
questions on who worked on a random bit and have them explain it."

### 3.9 Must the project be built inside the window?

**Yes, three times over**, and it is the same answer from three documents: rules 6 and digital rule 6,
and the contest terms' "You may not perform any work on your Application prior to the time window…
or your Application will be disqualified at the sole discretion of the Sponsor."

MEASURED window: the event page's calendar payload is `20261106T170000Z/20261108T180000Z`, and the
schedule's "Hacking Begins" is Friday 12:00 PM ET = 17:00Z.

**What the repo actually shows** — MEASURED from git in this session:

- 19 commits, `744a2c2` (2026-11-07T08:29:57Z) → `8a5e5e6` (2026-11-07T18:12:54Z).
- Earliest commit is **15 h 29 min after hacking began** and **before hacking ends**.
- The commits are spread across 9 h 43 min in 19 steps, not one blob.
- No commit is dated before the window; nothing in the tree is backdated.

ASSERTED: on the two checks that matter — "did they start before the event" and "is it one big commit
at the beginning" — the git history answers cleanly in our favour, and the operator should be told
that before he worries about anything else on the list.

---

## 4. What judges can actually open, and the Solana materials test

### 4.1 Is a deployed link required? A devnet program? Does anyone run the code?

**MEASURED-ABSENT, on every page fetched today:** no rule requires a deployed or hosted URL; no rule
requires a deployed Solana program; no rule requires a devnet transaction; no rule states that judges
execute the project.

What is published about how a judge meets the artefact:

- MEASURED, `standard-hackathon-rules.md`, Demos: "Either via a prerecorded video (typically at
  digital events or live demos at physical hackathons)." — for a digital event, the video is the demo.
- MEASURED, `judging-plan.md`: "Make sure they put a lot of love and care into their submission. Their
  video should be a demo of their hack, not a presentation. This is not needed for judging when
  science fair style, but can be a reference during final deliberations…"
- MEASURED, submission field list: "**Try it out / GitHub Link**" — one field, either or both.
- MEASURED, `cheating-check.md`: "You should check their GitHub **(recommended you require this as
  part of the submissions)**".
- MEASURED, `contest-terms.md`: "Each Participant or team **must be available during the Event's
  judging period to demonstrate** the Participant's or team's Application. **Judges may inspect
  Applications at any time during the judging period.**"

ASSERTED: the binding consequence is that the repo is the artefact a judge can always open, the video
is what a judge usually watches, and a live demo is *possible on request* rather than required. A
project that only runs on loopback is therefore not rule-breaking; it is only a risk if a judge asks
and there is nothing to show. `SUBMISSION-PACK.md` T3/T11 already frames that correctly.

### 4.2 The Solana-specific materials test, as written

MEASURED, event page, Top 3 Overall criterion, verbatim and unchanged from the earlier finding:

> "We're looking for a working product that uses Solana for something it's good at (speed, low fees,
> composability, on-chain ownership), **not a chain bolted onto a web2 app**."

That sentence is the *entire* published test for the main prize. There is no list of accepted
artefacts attached to it on this event's pages.

The nearest thing to an artefact list is MLH's Solana Hack Days partner page, MEASURED at
`https://hackdays-guide.mlh.com/partner-programs/solana.md`, "**Last reviewed: August 2026**", fetched
18:33Z, verbatim:

> "## Judging Evidence
> Confirm that the winning project actually uses Solana. Ask the team to identify the **integration in
> its README** and show the relevant **code, configuration, transaction, deployed program**, or other
> appropriate evidence during the demonstration."

and what that programme says is worth building, verbatim:
> "* Create an interactive application that uses **onchain state, ownership, or transactions**
> * Build a community, gaming, creator, payments, or finance experience powered by Solana
> * **Connect a web or mobile application to Solana as a fast, efficient backend**
> * Use Solana to power something people will want to try"

ASSERTED, and this is the scoping caveat that must not be lost: those words are written for **Hack
Days**, a different MLH programme from this **Partnered Hackathon**. They are the sponsor's own
statement of what "actually uses Solana" means, which makes them the best available proxy — but they
are not a rule of this event, and `02-rubric-and-scoring.md` should be read as having used them as a
proxy, which is what it did.

Note the fourth bullet: "connect a web or mobile application to Solana as a fast, efficient backend".
Read literally, that is a lower bar than "build an on-chain primitive", and a pricing console that
reads real chain state is inside it.

---

## 5. What changed since the earlier research

| # | Earlier finding, and where | Now, measured 2026-11-07 | Effect |
|---|---|---|---|
| 1 | "The weighting quoted in the brief (25/25/25/25 originality / technical complexity / theme adherence / practical implementation) is **not published anywhere I could reach**. MEASURED-ABSENT" — `02-rubric-and-scoring.md` §3 | **Published**, verbatim, in `contest-terms.md` under "Scoring of APPLICATIONS". But that document is the **2025-26 season's** ("shall commence on July 1, 2025, and shall end on June 30, 2026"), and the registration form's link to it is broken (→ `mlh.com/`). **CONFLICT with the four-equal-criteria page, both named in §2.2.** | The finding was wrong; the strategy it produced was right anyway. Do not re-plan for originality. |
| 2 | "the field is **seven submissions** with the submission window still open" — `02-rubric-and-scoring.md` "What I concluded" | **18 submissions**, on the canonical event page at 18:28Z (`18` in the stats strip). No public gallery (`galleryPath: null`), so nothing about them can be read. | The field tripled in a day. "Three of seven place" is now "three of eighteen or more". Size of field is still small. |
| 3 | "nothing published says the initial submission can still be edited after it" — `SUBMISSION-PACK.md` §0 | The platform's own organiser doc: "The separate **Accept late submissions** switch lets participants **submit or edit** after the deadline." Platform close is **13:00 ET**, three hours after the 10:00 ET initial. | The initial submission is a checkpoint, not a freeze — but rules 11 caps hacking at 11:45 ET. Hold the 10:00 freeze anyway. |
| 4 | "Rule 12 and 13 make this [a LICENSE] a prize condition" — `02-rubric-and-scoring.md` §"Sunday build must contain" item 1 | **No licence is required** by any rule fetched today. Rules 12/13 require the code to be **public** and to **stay** public. | Overstated. The MIT `LICENSE` already added at 17:04Z is fine to keep; it is not what earns or loses the prize. |
| 5 | Prize tracks AI / DeFi / Gaming / Best Beginner / Top 3, sourced from `events.mlh.com` | Same five, now with **exact prize strings**, the "<50% first-time hackers" eligibility line for Best Beginner, Top 3 as "**$1,000 USD microgrant for each of the three strongest teams**", and "**One submission can enter every category it qualifies for**" on all five category pages. | Unchanged in substance, now citable per-category. |
| 6 | Sponsor category "Best Use of Solana" listed as an MLH member-event prize (hardware wallets) in `04-mlh-judging-playbook.md` §2.1 | Still live on the seasonal prize page ("18 prize categories"), **not** offered on this event's page. | Position unchanged: uncertain, free to tick, worth no build time. |
| 7 | Video: ≤2 min, created that weekend, hackathon named at the start, public forever — `p1d-video-judging.md` | All re-verified verbatim, plus: **no host and no language is specified** anywhere. | Re-verified. YouTube + `.srt` remains a choice, not a rule. |
| 8 | — (not previously recorded) | The MLH cheat-check list is published verbatim, and one of its eight lines is "**Is a solo hacker making a really advanced project in a single weekend?**" | New, and it points at exactly the shape of this entry. §6 R4. |
| 9 | — (not previously recorded) | `contest-terms.md`: "Applications that have been generated by a script, macro, bot, or any other automated means will be deemed void." Also: "An Eligible Participant (or team) must be the **sole owner** of the Application submitted." | Two new disqualification-shaped clauses. §6 R2, R5. |

### 5.3 The specific question: "we have prior research in this repo from before the event — does that matter?"

Three answers, and they are different answers for three different things:

1. **The git history is clean.** MEASURED: earliest commit 2026-11-07T08:29:57Z, 15 h 29 min after
   hacking began. Nothing in the tree is backdated, and nothing predates the window. On the
   "did they start before the event" check, the answer the repo gives is the right one.
2. **The `../research/mlh-solana-2026/` corpus (written 2026-11-06) is prior work in the ordinary
   sense and is not in this repository.** It is not committed, and it must not be committed. It is
   also not "code or other project materials" in the sense rule 9 forbids — it is reading. ASSERTED:
   leaving it out of the repo is the whole mitigation, and the repo already leaves it out.
3. **The one place this becomes a real exposure is where pre-event material did get in**: this repo's
   own `records/` and `RESEARCH-PROGRAM.md` describe a research programme that was planned before the
   event. ASSERTED: that is a documentary hazard, not a code violation, and the honest presentation of
   it (the programme was run this weekend; the notes are dated) is stronger than hiding it. Every
   commit timestamp supports the honest presentation.

---

## 6. Disqualification risk register, against what this repo actually contains

Measured in this session, on this machine:

- `fixtures/synthetic_store.json`: `ledger[0].signature` is `None`, `ledger[0].slot` is `None`, and the
  ticket mint is `SYN1EkWc6HA2sY3n2QENB329vug7vkJ5mxBTjKN1pcR`. No transaction signature exists in the
  tree (a grep for a 80+ character base58 signature returns nothing).
- `ticketpath/adapters/rpc_adapter.py` defaults to `NO_PROGRAM_ID = "no_program_id_configured"`.
  Nothing is deployed.
- No Solana toolchain on this machine (`solana`, `anchor`, `cargo`, `rustc` all absent — already a
  finding of `02-rubric-and-scoring.md` §E1).
- The visible product is a **copy** of a pre-existing frontend checkout, served on loopback
  (`records/findings/14-frontend-attach-explore.md`, `records/FRONTEND-INTEGRATION.md`).
- `LICENSE` present (MIT), added 2026-11-07T17:04Z.

| # | Risk | Rule, measured | Severity | What removes it |
|---|---|---|---|---|
| **R1** | **The demo UI is a pre-existing platform frontend.** Digital rule 6: "You can not submit a project that includes prior work." Rule 9: a prior idea is allowed "as long as they do not re-use code or other project materials." | Digital rule 6; rules 6, 9, 10; contest terms "may not perform any work… prior to the time window" | **High — the single largest exposure** | Do not present the sibling checkout as this weekend's work. Either the video shows only what this repo built (the console, the engine, the fixtures, the checks), or the submission says in one plain sentence that the surrounding product UI is an existing platform and the weekend's work is the pricing layer inside it. Asserting the whole app as a weekend build is the one thing that can actually cost the entry. |
| **R2** | **AI-built code, undisclosed.** Rules: "Teams **may** use AI to assist them while coding" but "should be **honest and transparent**", and the form makes the disclosure a required dropdown and a required long-text field. | AI Tools and Code Gen 1–2; submission field list §1.3 | **High if omitted, low if disclosed** | Fill both GenAI fields truthfully with the tools by name. There is no penalty for using them; there is a documented review for hiding them. |
| **R3** | **`contest-terms.md`: "Applications that have been generated by a script, macro, bot, or any other automated means will be deemed void."** | contest-terms.md, "HOW TO PARTICIPATE" | Medium — **CONFLICT** with the AI permission, named not resolved | Nothing to do but disclose. ASSERTED: read in context this targets spam entries ("Applications that are mechanically reproduced, copied, illegible, incomplete, or inaccurate are void" is the preceding sentence); the AI section is the specific rule. Named here so it is on the record. |
| **R4** | **"Is a solo hacker making a really advanced project in a single weekend?"** is the second item on MLH's own cheat-check list. | `cheating-check.md` | Medium | A demo where the operator explains a random part convincingly answers it. The mitigation is a video and a README that are *explainable*, not smaller. |
| **R5** | **"An Eligible Participant (or team) must be the sole owner of the Application submitted."** The subject matter is a ticketing platform the brief describes as "the company's own". | contest-terms.md | **High, and not mine to answer** | Operator question Q1. If there is any question of employer ownership, the submission needs a different framing or the operator's decision to proceed. |
| **R6** | **Code must stay public forever**, and "making the repository private after the event ends" is called out as disqualifying. | rules 12–13; `cheating-response.md` | Medium — conflicts with R5 | Operator question Q1 again. These two rules pull in opposite directions for a company-shaped project, and only he can resolve which way. |
| **R7** | **No on-chain artefact.** No signature, no program, no real mint. | Nothing requires one — **MEASURED-ABSENT** | Not a DQ risk. A Top 3 score risk, because the Top 3 criterion is the materials test. | Operator question Q4 (the devnet write). If it does not happen, the submission stays honest and complete without it. |
| **R8** | **Synthetic data read as real.** | No rule names it; `cheating-response.md` says the platform holds extra context a reviewer may use | Medium | The repo already labels every number's source. Nothing on screen or in the video may imply a real market. `SUBMISSION-PACK.md` §1.2 already requires this. |
| **R9** | **Registration or check-in incomplete.** Digital rule 4: "You must have completed all registration steps." | Digital rule 4 | Low, and fatal if true | Operator question Q6. Check the Submit button is enabled on Saturday night. |
| **R10** | **Video reused or off-weekend.** "created the weekend of the hackathon", "state the name of the hackathon at the beginning", "must remain public post event". | Digital rules 1–3 | Low | Record it Sunday, open with the name, leave it public. |
| **R11** | **Submitting to another hackathon.** "You are not allowed to submit your project to other hackathons." | Digital rule 5 | Low | Do not cross-submit this entry anywhere. |
| **R12** | **Code of Conduct, "in their hacks".** "attendees should not use sexualized images, activities, or other material both in their hacks and during the event." | `code-of-conduct.md`, fetched 18:32Z | Nil for this build | Noted for completeness. |

---

## 7. Unanswered questions for the operator

1. **Ownership (R5/R6).** Is the ticketPricing code his alone, or company work? The terms demand sole
   ownership and rules 12–13 demand the repo stay public forever. If it is company IP, both cannot be
   satisfied and the entry needs reframing before Sunday.
2. **The pre-existing UI (R1).** Does the video show the copied platform frontend? My read: it may be
   shown, but the submission must state plainly that the surrounding UI predates the weekend and the
   pricing layer is the work. That is one sentence in the description and one in the video.
3. **AI disclosure wording.** Which tools, in what words, in the two required fields. Naming them is
   free; guessing wrong is the only way this hurts.
4. **The devnet write (T9).** Is there a laptop with Agave, and an hour, before 10:00 ET? Without it
   the honest state is "nothing deployed" and the entry stands.
5. **Was the pre-event research corpus (`mlh-solana-2026`, 2026-11-06) drawn from company or private
   data?** It is uncommitted and should stay that way; the answer decides whether it may be quoted in
   the submission text at all.
6. **Is he registered *and* checked in** on MLH, with the address form done (the event asks)?
7. **Is he a first-time hacker** — i.e. does the Best Beginner track apply at all? ">50% first-time
   hackers."
8. **Does "Opt-In Prizes" offer the seasonal "Best Use of Solana" category,** and does he want it
   ticked? It costs nothing if it is offered.

---

## 8. Sources fetched in this pass

| # | URL | HTTP | Fetched (Z) |
|---|---|---|---|
| 1 | `https://events.mlh.com/events/15200-solana-hackathon` | 200, 40,504 B | 18:26 |
| 2 | `https://www.mlh.com/events/solana-hackathon` | 200, 94,748 B | 18:28 |
| 3 | `https://www.mlh.com/events/solana-hackathon/challenges/<5 ids>` | 200 ×5, ~71.6 KB each | 18:28 |
| 4 | `https://www.mlh.com/events/solana-hackathon/submissions/new` | 302 → `/signin?return_to=…` | 18:28 |
| 5 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | 200, 8,584 B | 18:26 |
| 6 | `…/mlh-policies/main/contest-terms.md` | 200, 15,148 B | 18:27 |
| 7 | `…/mlh-policies/main/cheating-response.md` | 200, 3,226 B | 18:27 |
| 8 | `…/mlh-policies/main/disciplinary-action.md` | 200, 2,779 B | 18:27 |
| 9 | `…/mlh-policies/main/code-of-conduct.md` | 200 | 18:32 |
| 10 | `https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md` | 200, 2,408 B | 18:27 |
| 11 | `https://guide.mlh.com/general-information/judging-and-submissions/hackathon-submission-portal.md` | 200, 3,525 B | 18:31 |
| 12 | `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md` | 200, 12,644 B | 18:30 |
| 13 | `https://guide.mlh.com/overview/event-types/digital-events.md` | 200, 11,279 B | 18:31 |
| 14 | `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md` (Oct 2026) | 200 | 18:34 |
| 15 | `https://hackdays-guide.mlh.com/partner-programs/solana.md` (reviewed Aug 2026) | 200, 2,556 B | 18:33 |
| 16 | `https://www.mlh.com/events/prizes` (= `hack.mlh.io/prizes`) | 200, 208,898 B | 18:27 |
| 17 | `https://mlh.link/solana` → `https://www.mlh.com/partners/solana` | 200, 94,723 B | 18:27 |
| 18 | `https://hackp.ac/ContestTerms` → `mlh.link/ContestTerms` → `mlh.com/` (broken) | 302/302/200 | 18:36 |

Not fetched, and why: the Discord announcement channels (login required); the submission form itself
(login required, §1.3); any public submissions gallery (none exists, `galleryPath: null`).

---

## The 15 lines

1. **Binds us:** all work in the window — rules 6 and 9, digital rule 6, and terms "may not perform any
   work… prior to the time window". The git history already answers this cleanly (earliest commit
   2026-11-07T08:29:57Z).
2. **Binds us:** public repo, public forever, never made private after the event — rules 12–13 and
   `cheating-response.md`, which names exactly that act as disqualifying.
3. **Binds us:** a video ≤2:00, created Sunday, hackathon named at the start, left public; "a demo of
   their hack, not a presentation".
4. **Binds us:** the AI disclosure — two required form fields, and the rules' honesty clause. Free to
   comply, and the only version of it that hurts is a false one.
5. **Binds us:** the 11:45 ET stop. Small bug fixes after are allowed; new features are not.
6. **Binds us:** full registration and check-in, and one entry per category per event; no cross-submitting
   elsewhere.
7. **Binds us least:** the score. Four equal criteria on the live rules page, idea/pitch/code-quality/
   problem-fit excluded; the 25/25/25/25 line exists in a stale, linked-broken terms file. Both named;
   neither re-planned for.
8. **Risk:** the demo UI is a copy of a pre-existing platform frontend — the largest prior-work exposure,
   and it is a wording problem, not a code problem.
9. **Risk:** "sole owner of the Application" against a company-shaped project, colliding with "the repo
   stays public forever". Only he can resolve it.
10. **Risk:** "is a solo hacker making a really advanced project in a single weekend" is on MLH's own
    cheat-check list; the answer is an explainable video, not a smaller project.
11. **Risk:** no deployed program, no transaction, all fixture signatures `null` — not a DQ risk, a Top-3
    score risk against the one published sentence about using Solana for something it is good at.
12. **Risk:** `contest-terms.md`'s "generated by a script, macro, bot… deemed void" contradicts the AI
    permission in the same-day rules; disclose, and let the record show both.
13. **Question:** is the code his alone? **14.** Is the pre-event research corpus his to quote?
    **15.** Is there an hour and a laptop for one devnet write before 10:00 ET?

**Nothing was committed. One file was written: this one.**

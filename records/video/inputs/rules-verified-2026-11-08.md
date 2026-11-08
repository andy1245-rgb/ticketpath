# The event's rules, re-read from the publishers' pages on 2026-11-08

**Why this file exists.** The video plan was about to inherit a 2:00 cap from a chain of
citations inside this repository (`records/findings/32` → `27` → `17` → MLH's policy
repository) without anyone re-reading the source that day. This file is that re-reading.
Every quote below was fetched on **2026-11-08 between 07:36Z and 07:39Z** with the
web-fetch tool, from the URL named beside it, and is verbatim.

**What it changes, in one line each.**

1. **The 2:00 cap is a rule, not a norm, and it holds.** Re-verified verbatim. It is not
   advice and it is not a convention read off past winners.
2. **The "conflict" that findings 27 and 32 recorded between 2, 3 and 4 minutes is not a
   conflict.** The 3- and 4-minute numbers are *live judging slots per team*, from a
   different section of a different document. Nothing anywhere recommends a 3- or
   4-minute *video*. The video limit is 2:00 and there is no second number.
3. **The submission deadline on the event page is 18:00Z, not 15:00Z.** The page states
   "Submissions close Nov 8, 1:00 PM EST" and gives the event window as
   "Fri, Nov 6 · 12:00 PM – Sun, Nov 8 · 1:00 PM EST". Our pack treats 15:00Z as the
   freeze and 16:45Z as the hard stop. Both figures are earlier than the page's, so
   nothing is at risk by keeping them, but three hours of the plan were being spent on a
   deadline the page does not state.
4. **The judging criteria are published, and they are the four the rules name, weighted
   equally.** `records/findings/02-rubric-and-scoring.md` recorded the equal weighting as
   unsourceable. It is sourced, verbatim, below.
5. **The Solana partner page asks for exactly the evidence this project has.** A deployed
   program and a transaction count as the "appropriate evidence" a judge is told to ask
   for. That is the video's strongest beat, and it now has an organiser document behind it.

---

## 1. The video rule, verbatim

**Source:** `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md`,
fetched 07:36Z, section "MLH Digital Event Submission Rules".

> "1. We require all teams to submit a **2 minute or less** demo video. Your video must be
> **created the weekend of the hackathon**.
> 2. Your video must remain public post event to be eligible for prizes. If your video is
> not public, new winners may be selected.
> 3. Your demo video must **state the name of the hackathon at the beginning** of the
> video. Ex. 'Hey I'm Sam and this is my demo for CorgiHacks.'
> 4. You must have completed all registration steps for the hackathon.
> 5. You are not allowed to submit your project to other hackathons.
> 6. You can not submit a project that includes prior work."

**Why these rules bind this event.** The same page scopes them: "For fully digital
hackathons that MLH hosts, hackathon submissions are subject to additional rules." The
event page fetched at 07:37Z reads "Format **Digital**", is hosted at
`www.mlh.com/events/solana-hackathon`, and shows the three-step register / check in /
submit flow. It is an MLH-hosted digital event.

**MEASURED-ABSENT on the event page:** no video length is stated anywhere on
`www.mlh.com/events/solana-hackathon` or its `/challenges/` view. The cap comes from the
policy page, not from the event page, and that is expected: the policy page is where MLH
keeps it.

## 2. The 3- and 4-minute numbers, and why they are not video limits

**Source:** `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md`,
fetched 07:39Z.

> "Structurally, we recommend having hackers submit 2 minute videos on your submission
> platform for the judges to review."

and, in a section about how many judges to recruit:

> "**t** = Time taken by a Judge per project (MLH recommendation: 4 mins per project. 2
> minutes for presentation + demo, 1 minute for questions from judge and score
> compilations, and 1 minute for judge travel)"

and, in a section about table-based judging:

> "**They only have 3 minutes per team**."

So: **t** is a staffing variable in the formula
`J = ⌈(P · n · t) / T⌉` for calculating how many judges to recruit. It is not a statement
about videos. "3 minutes per team" is a stopwatch at a judging table. Neither is a length
recommendation for a submission video, and the same document recommends 2-minute videos in
its own words.

**Correction recorded:** `records/findings/27` §1.5 and §3.1, and
`records/findings/32` §3 ("GUIDANCE, medium confidence, and it conflicts with itself"),
record a conflict between 2, 3 and 4 minutes and leave it unresolved. There is no conflict.
The video limit is **2:00**, from rule 1 above, and the other two numbers are judging
slots. A run that reads those findings without this file will keep paying for a decision
that is already made.

## 3. Deadlines, as the event page states them today

**Source:** `https://www.mlh.com/events/solana-hackathon`, fetched 07:37Z and again 07:39Z.

> "Live Now Solana Hackathon NOV 06 - 08 Everywhere, Worldwide Digital"
> "Submissions close Nov 8, 1:00 PM EST"
> "Date Fri, Nov 6 · 12:00 PM – Sun, Nov 8 · 1:00 PM EST"
> "Format Digital"
> "70 Submissions" (07:37Z; the same page read 68 at 07:36Z, so entries were arriving
> while this was measured)

1:00 PM EST on 8 November 2026 is **18:00Z**. The event window is therefore
17:00Z on 6 November to 18:00Z on 8 November.

**Three consequences, and the third is the one that can lose the entry:**

- The 15:00Z freeze in `records/SUBMISSION-PACK.md` is a self-imposed buffer, not a
  published deadline. Keeping it is safe. Believing it is the deadline costs three hours.
- Rule 11 of the same policy page: "Teams must stop hacking once the time is up. However,
  teams are allowed to debug and make small fixes… Making large changes or adding new
  features is not allowed." So the video must be **created before 18:00Z**, not merely
  uploaded.
- The video must be **public** at judging time, and it must be the one attached at the
  deadline.

## 4. The judging criteria, verbatim

**Source:** `standard-hackathon-rules.md`, "Judging Criteria".

> "Teams will be judged on these four criteria for MLH digital events or MLH categories at
> an in person event. **Judges will weigh the criteria equally.** …
> * **Technology**: How technically impressive was the hack? Was the technical problem the
>   team tackled difficult? Did it use a particularly clever technique or did it use many
>   different components? Did the technology involved make you go 'Wow'?
> * **Design**: Did the team put thought into the user experience? How well designed is the
>   interface? For a website, this might be about how beautiful the CSS or graphics are. …
> * **Completion**: Does the hack work? Did the team achieve everything they wanted?
> * **Learning**: Did the team stretch themselves? Did they try to learn something new?"

And, immediately after, what is **not** judged:

> "It's important to note that these judging criteria do not include: How good your code
> is… How well you pitch… How good the idea is… How well the project solves a problem."

Two operational readings, both INFERENCE:

- Four equally weighted criteria means the video should spend roughly a quarter of its
  time on each, and "Completion" is a criterion the video can *address* rather than a
  score it must hide a hole in. Showing what is unfinished, labelled, is Completion
  evidence, not an admission.
- "How well you pitch" is explicitly not judged, which is the published basis for
  `records/findings/27` §3 item 1. A demonstration is scored; a pitch is not.

**Correction recorded:** `records/findings/02-rubric-and-scoring.md` A5 recorded the
25/25/25/25 weighting as unsourceable on any MLH or event page. The equal weighting is
published, in the sentence quoted above.

## 5. What the Solana partner page asks a judge to look for

**Source:** `https://hackdays-guide.mlh.com/partner-programs/solana.md`, fetched 07:38Z.

> "## Judging Evidence
> Confirm that the winning project actually uses Solana. Ask the team to identify the
> integration in its README and show the relevant code, configuration, transaction,
> deployed program, or other appropriate evidence during the demonstration."

> "## Best Use of Solana
> … * Create an interactive application that uses onchain state, ownership, or transactions"

This is the organiser-side instruction for the category this project is in. "Deployed
program" and "transaction" are named as acceptable evidence, in that order of specificity.
The video's strongest beat — a real devnet program, a real admitted transfer and a real
refused transfer, each with a signature — is exactly the evidence this page tells a judge
to ask for. It also means the video should *name the integration* in one clause, because
that is the literal instruction the judge is following.

## 6. Prior work, and what it means for a frontend on camera

**Source:** `standard-hackathon-rules.md`, rules 6, 9 and 10 and digital rule 6.

> "6. All work on a project should be done during the period of the hackathon."
> "9. Teams can work on an idea that they have worked on before (as long as they do not
> re-use code or other project materials)."
> "10. Teams can use libraries, frameworks, or open-source code in their projects."
> Digital rule 6: "You can not submit a project that includes prior work."

`records/findings/17` risk **R1** calls the pre-existing platform frontend "the single
largest exposure". That was written when the plan was to show the sibling checkout. The
tree has since moved: `../ticketing-frontend` carries one commit,
`0208765 baseline: untouched tree before the SeatPass rebuild`, and the whole SeatPass UI
now sitting on top of it is **new, uncommitted code written during the event window**
(23 modified paths, 17 untracked, measured at 07:31Z).

**INFERENCE, and the safe reading:** code written this weekend is this weekend's work;
an idea and a visual language carried over are allowed by rule 9. What rule 6 forbids is
presenting pre-existing *work* as the submission. So the video should say, in one clause,
what the weekend built, and should not imply the surrounding product existed before it.
That is a sentence in the script, not a legal problem.

## 7. The capture-date question the cheat check actually asks

**Source:** `https://guide.mlh.com/general-information/judging-and-submissions/cheating-check.md`
(quoted in `records/findings/17` §3.8, re-read there):

> "* **Are their Timestamps over the weekend when they run the demo in any video/screen
> captures?**
> * (If they have a video) **Was the video published over the weekend?**"

A reviewer is instructed to look for weekend timestamps inside the video. This collides
with `records/SUBMISSION-PACK.md` §1.4, which forbids a desktop, a terminal and a
notification on any frame — a visible system clock is a desktop. The collision is real
and it is decision **V4** in `../OPEN-DECISIONS.md`. The compliant middle is a screen whose
own content is dated inside the window, plus the publish date, plus a spoken date.

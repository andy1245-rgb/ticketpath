# What this event can actually be won at, and what that means for the 2:00

**Written:** 2026-11-08 between 10:31Z and 10:52Z. **Every page below was fetched in that window by
this pass**, and the fetch time is printed beside each quote.

**Labels.** **MEASURED** = this pass fetched the named page at the stated time and the text is
verbatim from it. **MEASURED-ABSENT** = the named pages were read and the thing is not on them.
**INFERENCE** = this pass's reasoning from the measurements, with no page behind it. A verbatim quote
has had another typographic apostrophe normalised to `'`; nothing else is altered.

**Paths are repository-relative.** No home directory, user name, process id or port appears here.

---

## 1. The pages, and when they were read

| Page | Fetched (Z) | HTTP | What it carries |
|---|---|---|---|
| `www.mlh.com/events/solana-hackathon` | 10:31:02 | 200 | the five categories, one criterion line each, the submission counter, the deadline |
| `.../challenges/01a1a70d-d26e-8f43-0b87-807e0a128bc0` (AI) | 10:31:26 | 200 | one criterion line, the prize string, "One submission can enter every category it qualifies for." |
| `.../challenges/01a1a6f0-dde1-f6fe-c748-37c36c7d45e6` (Best Beginner) | 10:31:27 | 200 | as above |
| `.../challenges/01a1a6f4-dc9c-7194-e5a6-7eae72d0c310` (DeFi) | 10:31:27 | 200 | as above |
| `.../challenges/01a1a6f2-2a5f-60db-9ce5-a58456d8188a` (Gaming) | 10:31:27 | 200 | as above |
| `.../challenges/01a1a6ef-1328-c2f4-f126-f0506a239a09` (Top 3) | 10:31:27 | 200 | as above |
| `www.mlh.com/events/solana-hackathon/challenges/` | 10:31:28 | 200 | **byte-identical to the event page**; there is no separate challenges view |
| `www.mlh.com/events/prizes` | 10:31:28 | 200 | 18 season-wide partner prize categories, including Best Use of Solana |
| `www.mlh.com/partners/solana` | 10:31:29 | 200 | the Solana partner hub, and the "Best Use of Solana" call |
| `events.mlh.com/events/15200-solana-hackathon` | 10:31:45 | 200 | **the long-form category text, the eligibility tests, the schedule** |
| `www.mlh.com/events/solana-hackathon/prizes` | 10:32:14 | 200 | the event's own prizes page, which reads "0 prize categories" |
| `www.mlh.com/events/solana-hackathon-0f` and `/prizes` | 10:32:33 | 200 | a second, empty event record with the same name |
| `hackdays-guide.mlh.com/partner-programs/solana.md` | 10:31:02 | 200 | Solana **Hack Days** guidance and its own judging-evidence standard |
| `guide.mlh.com/.../judging-plan.md` | 10:32:14 | 200 | MLH's organiser recommendation: 4 minutes per project, 3 rounds, stack ranking |
| `raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | 10:32:14 | 200 | the four criteria, equally weighted, and their exclusions |

**The two surfaces disagree in two places, and both are recorded rather than resolved:**

- The Top 3 prize line. Event page, MEASURED 10:31:02: "$1,000 USD microgrant for each of the three
  strongest teams to continue building." Events page, MEASURED 10:31:45: "$1,000 USD microgrant for
  your team to continue building". Same money, different sentence.
- Which surface carries the test. The canonical event page and all five category pages carry **one
  sentence per category and no judging language at all**: `judg` and `criteria` return zero matches in
  the page's own HTML (MEASURED, this pass). The long form, including the eligibility tests, is only on
  `events.mlh.com` (MEASURED, 10:31:45).

---

## 2. The categories, with prize, test and source

Five categories exist on this event's page today. **MEASURED**, `www.mlh.com/events/solana-hackathon`,
10:31:02Z: "Prize Categories / 5 categories".

| Category | Prize, verbatim | The whole published test, verbatim | Source |
|---|---|---|---|
| **Top 3 Overall** | "Top 3 Overall" / "$1,000 USD Microgrant" / "$1,000 USD microgrant for each of the three strongest teams to continue building." | "The three strongest projects at the event. Every eligible submission is automatically entered. We're looking for a working product that uses Solana for something it's good at (speed, low fees, composability, on-chain ownership), not a chain bolted onto a web2 app." | long form: events page 10:31:45; category page 10:31:27 |
| **AI Track Top Prize** | "Event prize $100 USD Digital Giftcard" / "Best use of AI in a project. Each winning team member receives a $100 digital gift card." | long form: "Build something where AI and Solana each do real work. The best projects use AI to make on-chain activity smarter, safer or easier, or use Solana to give AI systems something they can't get elsewhere, like payments, ownership, verifiability or coordination." | events page 10:31:45; category page 10:31:26 |
| **Best Beginner Hack** | "Event prize $100 USD Digital Gift Card" / "Best project created by Hackathon Beginners. Each winning team member receives a $100 digital gift card." | long form: "For teams building on Solana for the first time or attending their first-ever hackathon (or both). We want to reward people who took the leap, learned something new and shipped a working project, however small. Teams made up of >50% first-time hackers are eligible for this prize track." | events page 10:31:45; category page 10:31:27 |
| **DeFi Track Top Prize** | "Event prize $100 USD Digital Gift Card" / "Best DeFi related project. Each winning team member receives a $100 digital gift card." | long form: "Build financial applications and protocols that take advantage of Solana's speed, low fees and composability. We want products that move value in ways that are faster, cheaper, more open or more accessible than what exists today." | events page 10:31:45; category page 10:31:27 |
| **Gaming Track Top Prize** | "Event prize $100 USD Digital Gift Card" / "Best gaming related project. Each winning team member receives a $100 digital gift card." | long form: "Build games, or the tools behind them, where Solana makes the experience better. Fun comes first. The blockchain should add something players care about, like true ownership, open economies, verifiable fairness or player-made content." | events page 10:31:45; category page 10:31:27 |

Two supporting quotes, both on all five category pages, MEASURED 10:31:26 to 10:31:27Z:

> "One submission can enter every category it qualifies for."

and the closing line on every one of them: "Submissions close Nov 8, 1:00 PM EST".

**MEASURED-ABSENT, and it matters:** no page fetched states **how many winning teams there are per
track**. Top 3 says "three". The four tracks say "each winning team member", which bounds the prize per
person and not the number of teams. What would settle it: the closing ceremony, or an organiser
statement. Do not write "one winner per track" as a measured fact.

**MEASURED-ABSENT:** no page fetched states a rubric, a weighting or a judging panel for any of the five.
The only rubric in existence is MLH's standard one, which applies to "MLH digital events or MLH
categories at an in person event" (standard rules, 10:32:14Z), quoted in §6.

---

## 3. Does this entry qualify, category by category

Strict reading throughout: the test is the category's own wording, not "some of the project is
related".

### 3.1 Top 3 Overall: **yes, and the entry is automatic**

**MEASURED**, events page 10:31:45Z: "Every eligible submission is automatically entered." So there is
no entry action and no eligibility gate beyond the rules.

The fit sentence has three parts, and the entry answers one of the four named Solana properties.

| Part of the test | Where this entry stands |
|---|---|
| "a working product" | **Partly evidenced.** A console renders from the repository's own run instructions, a program is deployed on devnet, and two boundary transactions exist on it (`inputs/build-state-matrix.md` §B2, §B11). Against it: no hosted URL exists, so "working" is something a judge takes from the video and a clone. |
| "uses Solana for something it's good at (speed, low fees, composability, on-chain ownership)" | **"on-chain ownership" is answered; the other three are not.** The ticket is a wallet-bound token and the price cap is enforced on transfer by a program. Nothing in the entry measures speed or fees. |
| "not a chain bolted onto a web2 app" | **The contested one.** The visible surface is a web console; the chain work is one predicate. What answers it is a transfer the program refuses, with a signature, which is beat 4 and is the only unforgeable thing in the entry. |
| "The three strongest projects at the event" | A ranking, not a test. Three places. |

**INFERENCE:** of the three parts, only the middle one is a claim the video can settle in under ten
seconds, and it is settled by the devnet pair rather than by any sentence. The first and third are
settled by the same footage.

### 3.2 AI Track: **no**

**MEASURED**, events page 10:31:45Z, the test in full: "Build something where AI and Solana each do real
work. The best projects use AI to make on-chain activity smarter, safer or easier, or use Solana to give
AI systems something they can't get elsewhere, like payments, ownership, verifiability or coordination."

This is a different test from "uses an LLM somewhere", and the entry fails it on the product:

- The pricing engine is not AI. **MEASURED** in the record (`records/video/inputs/build-state-matrix.md`
  §B4, §2): `/health` reports `fitted: false` and `kind: rule-based-bounded-estimator`, and the payload's
  `pooled.method` reads `"declared"`. Nothing is fitted, so nothing is learned, so no model is doing work
  of any kind.
- The only AI-shaped thing in the tree is the LLM agent harness under `market_swarm/`. **MEASURED** in
  the record (§B5): the two live-LLM runs left **no dataset on disk** (a dry re-run reused the run id and
  overwrote them), the local validator path **does not currently reproduce**, and there has **never** been
  a devnet run. A judge can see no AI-plus-Solana artefact, on any page, at any time today.
- Presenting the harness as AI doing on-chain work would also collide with MUST-NOT-SAY 20 in §3 of the
  same document ("that the swarm shows the cap reduced scalping, or any market inference").

**INFERENCE:** entering this track costs nothing, because entering is free and unlimited, and winning it
would require building and committing a re-runnable AI-plus-Solana artefact. That is not a 2:00 video
problem and it is not a gap the video can close. The submission's required GenAI disclosure fields are a
rules obligation and are **not** evidence for this category; they record which tools wrote the code.

### 3.3 Best Beginner Hack: **unclear, and it turns on one fact this file cannot measure**

**MEASURED**, events page 10:31:45Z, quoted in full above. The operative sentence is "Teams made up of
>50% first-time hackers are eligible for this prize track."

Three separate things are gated, and only one of them is uncertain:

| Gate | Status |
|---|---|
| ">50% first-time hackers" | **A fact about the team, not about the build.** Nothing in the repository can settle it. |
| "shipped a working project, however small" | **Met.** A console, a deployed program and two boundary transactions exist. |
| student status | **Not a gate on this event's own surfaces.** MEASURED-ABSENT: no page fetched requires a student. The registration questions (events page, 10:31:45Z) are: "I am either over 18 years of age or have a parent's permission to participate in this event."; agreement to "MLH's Contest Terms & Conditions and Privacy Policy"; agreement to the Code of Conduct; "In what country do you currently reside?"; a web3 experience band; a Solana familiarity band; "Have you already completed the Address Form?"; and two email opt-ins. None of them asks for a school. |
| team composition other than the >50% test | **MEASURED-ABSENT.** No page states a minimum or maximum team size for this track. |

The wording contradicts itself in a way worth knowing before it is ticked. Sentence one reads
"building on Solana for the first time **or** attending their first-ever hackathon (**or** both)", which
makes a first Solana build sufficient. Sentence three collapses both into ">50% first-time hackers".
**MEASURED-ABSENT: no page fetched defines "first-time hacker".** What would settle it: the organiser,
in writing. The practical reading, marked **INFERENCE**, is that the operative sentence is the last one
and a checker applies that.

One correction to the record carried in this repository: `records/findings/17-hackathon-rules-recheck.md`
line 511 states "<50% first-time hackers". The page says **">50%"**. Its own lines 225 and 584 have it
right. This pass re-measured the page today and the page says ">50%".

### 3.4 DeFi Track: **yes on subject, unclear on the operative sentence**

**MEASURED**, events page 10:31:45Z: "Build financial applications and protocols that take advantage of
Solana's speed, low fees and composability. We want products that move value in ways that are faster,
cheaper, more open or more accessible than what exists today."

- First sentence: **fits.** A pricing engine for a tokenised asset is a financial application, and the
  Token-2022 transfer hook is composability with a standard rather than a bespoke contract.
- Second sentence: **does not fit, and must not be made to.** This product moves no value. There is no
  marketplace, no checkout and no escrow, and `records/video/inputs/build-state-matrix.md` §3 rows 9, 16
  and 18 forbid saying otherwise.

The category's own "Ideas to Get Started" list is what lifts this from "no" to "unclear". **MEASURED**,
events page 10:31:45Z, under DeFi:

> "Trading tools: order routing, portfolio rebalancing, automated strategies or analytics dashboards"

A price-discovery dashboard for a tokenised asset sits inside a named example. **INFERENCE:** a judge
reading the ideas list before the test sentence could place it; a judge reading the test sentence first
would not. The second is the more likely order, and it is why this ranks below the other two.

### 3.5 Gaming Track: **no**

**MEASURED**, events page 10:31:45Z: "Build games, or the tools behind them, where Solana makes the
experience better. Fun comes first. The blockchain should add something players care about, like true
ownership, open economies, verifiable fairness or player-made content."

A primary-market ticket-pricing engine is neither a game nor a tool behind one. Ticket resale is not a
game economy. **INFERENCE:** there is no honest framing of this build that enters this track, and no
second of video should be spent trying.

---

## 4. Is there a Solana-specific category, or is Solana the theme of the whole event?

**Solana is the theme of the whole event. There is no Solana category among the five.** MEASURED:

- The event is named for it and every category sits inside it: "Live Now Solana Hackathon" and "Welcome
  to the Solana Hackathon!" (event page, 10:31:02Z).
- All five categories are listed under "Prize Categories / 5 categories" and none of them names Solana
  (event page, 10:31:02Z).
- The event's own prizes page reads **"0 prize categories"** (MEASURED,
  `www.mlh.com/events/solana-hackathon/prizes`, 10:32:14Z). So no season-wide partner category is
  attached to this event record through the prizes surface.
- The string "Best Use of Solana" does not appear on the event page's HTML at all (MEASURED: zero
  matches in 94,748 bytes, 10:31:02Z).

**But a page elsewhere in MLH's estate says a Solana prize exists, and this is the one open question in
this file.** MEASURED:

- `www.mlh.com/partners/solana`, 10:31:29Z: "Integrate Solana into your next hack to **qualify for the
  Best Use of Solana prize category**!"
- `www.mlh.com/events/prizes`, 10:31:28Z: "18 prize categories", one of them "Best Use of Solana", prize
  "Unruggable Hardware Wallets", with the CTA "Build with Solana".
- `hackdays-guide.mlh.com/partner-programs/solana.md`, 10:31:02Z, is scoped to a different programme in
  its own first line: "Challenge guidance, participant resources, opening materials, and judging
  requirements for **Solana Hack Days**." Its own "Expected Prize" is "**Ledger Nano S Plus**", not the
  event's gift cards.

**Verdict: unclear whether "Best Use of Solana" attaches to this event, and the answer matters more than
any other single fact in this file, because its published evidence standard is aimed straight at this
entry.** MEASURED, same Hack Days page, and it is the only sponsor-side statement of what "actually uses
Solana" means that exists anywhere:

> "## Judging Evidence
> Confirm that the winning project actually uses Solana. Ask the team to identify the integration in its
> README and show the relevant code, configuration, transaction, deployed program, or other appropriate
> evidence during the demonstration."

and, under its own "Best Use of Solana" heading:

> "* Create an interactive application that uses onchain state, ownership, or transactions"

That is a list of four acceptable artefacts, and this entry has two of them: a deployed program and a
transaction. **MEASURED-ABSENT: nothing on the event page, the five category pages, the event's prizes
page or the events page names this category.** What would settle it, and it takes one minute: **open the
submission form once and read the category checkboxes.** That is already `records/findings/23` §5.0 item
P2, and it is now the single highest-value minute before the video is locked.

---

## 5. Ranked: what this entry can actually win

Ranked by the chance this entry takes the prize given the evidence a judge can see on the page and in a
2:00 video, not by prize value. Value is in the second column.

| Rank | Category | Prize | Why this rank | The evidence a judge must see in the 2:00 |
|---|---|---|---|---|
| 1 | **Best Beginner Hack** | $100 Gift Card per member | The test is "learned something new and shipped a working project, however small". Learning is this entry's strongest measured axis (two independent passes scored it 18 and 19 of 25) and it does ship a working project. The category's own idea list for beginners is "a simple token, NFT collection or on-chain voting app", so a devnet transfer hook with a passing boundary test is unusual for the bucket. **Conditional: only if the >50% test is true, and that is not knowable from the repository.** | Beat 5's Token-2022 sentence, in his own words, plus beat 4 for "shipped". This is the only Learning evidence in the script. |
| 2 | **Top 3 Overall** | $1,000 microgrant, three teams | Automatic entry and three places, so it is reachable by definition. Ranked second only because the field is the whole event and "not a chain bolted onto a web2 app" is a real risk against a console-shaped product. | Beat 4 in full: two signatures, one admitted, one refused by the program, each on a frame that says DEVNET. Plus beat 1's "the chain caps the markup", which is the sentence that makes ownership load-bearing. |
| 3 | **DeFi Track Top Prize** | $100 Gift Card per member | Yes on subject and on one named example ("analytics dashboards"), unclear on "move value". Free to enter. | None available. The distinguishing test is the one the entry must not claim. Do not spend seconds. |
| 4 | **AI Track Top Prize** | $100 Gift Card per member | Fails the product test. The engine is not fitted and the LLM harness left no dataset and does not reproduce. | None exists. Nothing in a 2:00 can manufacture it. |
| 5 | **Gaming Track Top Prize** | $100 Gift Card per member | Not a game and not a tool behind one. | None. |

**Outside the five, and possibly the best target of all if it exists:** the "Best Use of Solana" category
in §4. Its published evidence standard names "deployed program" and "transaction", which the entry has,
and it is the only category in existence whose stated test the devnet pair satisfies in one clause.
Whether it applies to this event is unresolved. Do not plan around it, but do read the submission form's
category list before ticking.

**INFERENCE on the ranking:** entry to every category is free and simultaneous ("One submission can
enter every category it qualifies for", MEASURED), so this is not an allocation problem. Tick everything
honest. The ranking is only about where the 115 seconds go, and two categories carry it.

---

## 6. What the video should stop spending time on, and what it should add

Read against `records/video/SCRIPT.md` as it stands (222 written words, 227 spoken, five beats, 1:55.0).
That file is not edited here. This section is a recommendation and the decision is the operator's.

### 6.1 What to stop

**Nothing has to be removed for the AI and Gaming tracks, because nothing in the script speaks to them.**
MEASURED against the script: no beat mentions AI, a model, an agent or a game. Two of the five tests are
already clear of the script. That is worth knowing before anyone cuts a line "for the tracks".

**The one line to stop paying for is `No marketplace, no checkout.`** It opens beat 5 and it is 4 of the
227 spoken words. It is a DeFi-shaped disclaimer: it answers the DeFi test's "moves value" sentence in
the negative, and no category on this page asks that question. **INFERENCE:** under Top 3 and Best
Beginner it buys nothing, and beat 5 is the beat that carries the Beginner track's evidence.

**This contradicts the script's own fallback and the contradiction should be named, not smoothed.**
`SCRIPT.md` §4 says: "If the first timed read is slower, cut beat 5's Token-2022 clause (16 words, 7.7
s), which is the only sentence that cannot be said in its own slot." **INFERENCE:** that sentence is the
entry's only Learning evidence, Learning is the Beginner track's test, and Beginner is the most winnable
category on the page. Cutting it would cut the highest-probability prize to protect seconds. If seconds
are needed, take them from `No marketplace, no checkout.` first, then from the fixture sentence only
after that, and only then from Token-2022.

**Do not shorten beat 2's prior-work clause.** It is 10 words and it is the digital rule 6 guard ("You
can not submit a project that includes prior work", standard rules 10:32:14Z). It is the cheapest
insurance in the script.

### 6.2 What to add or emphasise

Four changes, in the order they buy category evidence, and none of them adds a spoken word:

1. **Beat 4, shot 7 and 8 cards: put the program's own log line on the REFUSED card.** MEASURED in the
   record (§B1): the failed transaction's log reads
   `ticketpath: cap exceeded price=1250000001 face=1000000000 cap_bps=2500`. It is the chain's own words,
   it is already on chain, and it makes the refusal self-describing on a paused frame with the sound off.
   That is the Top 3 answer to "not a chain bolted onto a web2 app" delivered by an artefact instead of
   an adjective.
2. **Beat 4, shot 6: keep the words "The chain refuses it, not the app."** That sentence is the load-
   bearing claim for Top 3 and it is already in the script at the right length. Do not paraphrase it into
   "no one can bypass the cap" or "the cap binds the seller": both are forbidden, because the deployed
   v1's `SetPendingPrice` takes no signer, so the refusal proves the price predicate and not who may
   stage a price (`records/findings/37-program-v2-review-fixes.md` as summarised in
   `inputs/build-state-matrix.md` §B17, which lists "no one can bypass the cap" as a must-not-say).
3. **Beat 5: keep the Token-2022 fee sentence and make sure he can defend it.** MEASURED, `SCRIPT.md`
   §1 beat 5 and `REHEARSAL.md` §5. It is the Beginner track's only evidence. The script's own test for
   it is not whether it is true (it is measured) but whether he can explain it without notes. For the
   most winnable category on the page, that is not an optional sentence.
4. **Beat 1: keep "the chain caps the markup" where it is, at 13.9 s.** MEASURED, `SCRIPT.md` §1 beat 1.
   Four words, and it is the only place in the script where Solana is doing something load-bearing rather
   than adjacent.

**One thing not to add, though Top 3 invites it.** The event's own About text names this vertical:
MEASURED, event page 10:31:02Z, "sell concert tickets that can't be faked". It is tempting to open with
the event's own example. Two reasons not to: "How well you pitch" is explicitly not judged (standard
rules, 10:32:14Z, quoted below), and "can't be faked" is a counterfeit claim this build does not make.
It belongs in the submission description, not in the 115 seconds.

**The rubric the video is actually scored against**, for completeness. MEASURED, standard rules
10:32:14Z:

> "Teams will be judged on these four criteria for MLH digital events or MLH categories at an in person
> event. Judges will weigh the criteria equally."

Technology, Design, Completion, Learning, and:

> "It's important to note that these judging criteria do not include: ... How well you pitch. Hacking is
> about building and learning, not about selling."

The one operating consequence, **INFERENCE**: the video should not be re-cut toward the categories at all
beyond the devnet beat, because four of the five categories are decided by evidence a judge can only take
from the footage of a thing working, and the fifth (Beginner) is decided by a fact about the team that no
footage can show.

---

## 7. What the submission count implies about judging attention

**MEASURED**, event page 10:31:02Z: "85 / Submissions", and the same page's payload reads
`submissionsCount: 85`. MEASURED, same page: "Submissions close Nov 8, 1:00 PM EST", which is 18:00Z, so
about seven hours and ten minutes remained when this was read.

**MEASURED, as recorded in this repository and not re-measured here:** the counter read 7 at 10:59Z on
7 November, 18 at 18:28Z, and 25 at 20:39Z (`records/findings/23` § opening, `records/findings/24` §1).
So the field grew from 25 to 85 in roughly fourteen hours.

**INFERENCE 1, field size.** Submission growth is back-loaded and the schedule puts the initial
submission deadline at 10:00 AM ET (MEASURED, events page 10:31:45Z: "Sunday / 10:00 AM ET / Initial
Submission due on MLH Challenges"), so most entries will land in the last third of the window. A final
field of 120 to 200 is the plausible range. **Do not plan against 85.** The number to re-read is the
counter at the moment of submitting, and that reading is one page load.

**INFERENCE 2, prize pool.** $1,000 times three teams, plus $100 per member across four tracks. At two
to three members a team that is roughly $3,000 plus $800 to $1,200, so a pool on the order of $4,000
against a field of 120 to 200 entries. That is a modest event by prize value and it is consistent with an
event whose schedule is two workshops and one ceremony.

**MEASURED, the organiser's own judging arithmetic**, `guide.mlh.com/.../judging-plan.md`, 10:32:14Z:

> "t = Time taken by a Judge per project (MLH recommendation: 4 mins per project. 2 minutes for
> presentation + demo, 1 minute for questions from judges and score compilations, and 1 minute for judge
> travel)"

> "n = Number of Judges for each project (or number of rounds of judging per project)
> (MLH recommendation: 3 rounds per project)"

and the same page on what the video is for:

> "Their video should be a demo of their hack, not a presentation."

**INFERENCE 3, attention per entry, and it is the operational conclusion of this whole file.** At 120 to
200 entries and a recommended three viewings of four minutes, that is 24 to 40 judge-hours. A judge
working a single day covers on the order of 30 to 40 projects, and stack ranking means only their top
three matter. So each entry gets **one flat pass of a couple of minutes, once, with the video playing**,
and the repository is opened by a judge only if the video already put the project in their top three.
The video is not a summary of the submission. It is the entire exposure.

**MEASURED-ABSENT, and no page fetched fills these:** how many judges this event has; how many entries
each judge sees; whether the four track prizes and Top 3 are judged by the same people; whether every
entry is seen three times; and how many winning teams there are per track. The 4-minute, 3-round,
stack-rank mechanism is MLH's recommendation to organisers, not a published property of this event. What
would settle all five: the results announcement, or an organiser statement.

---

## 8. Two hazards found while reading today

**8.1 There are two event records with the same name, and one of them is empty.** MEASURED,
10:32:33Z:

- `www.mlh.com/events/solana-hackathon` carries the 85 submissions, the five categories, the 18:00Z
  close, and the submit flow.
- `www.mlh.com/events/solana-hackathon-0f` carries "Registration details and challenges will appear here
  as this event takes shape.", 0 prize categories, a closing time of "Sun, Nov 8 · 11:59 PM UTC", and it
  points its `websiteUrl` at `events.mlh.com/events/15200-solana-hackathon`, the same events page.

**INFERENCE:** this is a duplicate or placeholder record, and the risk is submitting against the wrong
one. The submit button on the 85-submission record is the one that leads to the field the categories are
attached to. Worth one second of care at submission time, not a research task.

**8.2 The event's own prizes page reads "0 prize categories".** MEASURED, 10:32:14Z. The five categories
are configured on the event record and not on the prizes microsite. **INFERENCE:** this is why the Solana
question in §4 cannot be settled from the prize surfaces, and why the submission form is the only surface
that can settle it.

---

## 9. What this file did not do, and what it cannot say

- It did not edit `SCRIPT.md`, `CHOREOGRAPHY.md`, `REHEARSAL.md`, `BRIEF.md` or `DELIVERY.md`. Nothing in
  the repository was changed except this file being created.
- It did not open the submission form. It requires a login, and the form's category checkboxes are the
  one surface that would settle §4.
- It did not re-fetch or re-measure anything in `records/findings/23` or `24` except where a page is
  quoted above with today's time. Their submission-count history and their judging-plan quotes are
  carried as recorded, and are labelled as such.
- It states no expected score and no probability of winning. There is no published scale, and a number
  would be invented.

**One correction to a file this pass was told to read, recorded and not edited.**
`inputs/rules-verified-2026-11-08.md` §3, item 3 says "The 15:00Z freeze in `records/SUBMISSION-PACK.md`
is a self-imposed buffer, not a published deadline." **MEASURED today**, events page 10:31:45Z, the
schedule row reads "Sunday / 7:00 AM PT / 10:00 AM ET / 3:00 PM UK / 8:30 PM IST / **Initial Submission
due on MLH Challenges**", and 10:00 AM EST is 15:00Z. So the entry's freeze is the organiser's own
schedule row, not a buffer this project invented. The 18:00Z platform close is also real and is the later
of the two. Both numbers are published; they govern different things, and the earlier one governs the
video being done.

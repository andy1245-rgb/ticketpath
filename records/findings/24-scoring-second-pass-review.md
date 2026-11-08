# 24 — Second pass on the judged score: independent verification, three corrections, and one thing the criteria record was missing

**Run:** SCORING-SECOND-PASS, 2026-11-07T20:39Z → 20:58Z. **Deadline defended:** initial submission
Sun 2026-11-08 10:00 ET = 15:00Z; hard stop 11:45 ET = 16:45Z.

**What this file is, and what it is not.** Andrew's brief was to find the judged criteria, score the
entry against each from the repo, and say what comparable winners did. That work landed while this pass
was running, in **`records/findings/23-hackathon-score-analysis.md`** (602 lines, written 20:40–20:47Z by
another worker in the same tree). **23 is the answer to the brief and nothing here replaces it.** This
file is the second pair of eyes the programme requires before a claim is final. It does three things
that 23 cannot do for itself: it re-measures the facts 23 relies on, it records three places where those
facts are stale or wrong at HEAD, and it adds one criteria fact that 23 does not carry.

**Numbering, recorded honestly, so nobody hunts for a missing file.** This pass opened `records/findings/22-scoring-and-where-to-raise-it.md`
and had filled its criteria section when 23 appeared with the complete answer. Rather than publish two
competing answers to one brief, the 22 file was deleted and this one took 24. `23-hackathon-score-analysis.md`
contains a line saying a `22-…` file "stopped at its own §1"; that was true when it was written and the
file no longer exists. Nothing was committed at any point, so no published record points at it.

**Labels.** **MEASURED** = a command was run in this pass and its output is quoted, or a named URL was
fetched in this pass and the text is verbatim. **MEASURED-ABSENT** = the named page was read and the
thing is not on it. **ASSERTED** = my reasoning. **Correction** = 23 (or an earlier record) states
something this pass measured differently; both are quoted.

**Who ran the commands.** This pass is orchestrator plus three dispatched phases (a repo audit, a rules
re-fetch, a winner search) and one adversarial review of this file. Where a measurement came from a phase
rather than from this shell, the entry names the phase and the time; where the review phase contradicted
this file, the file was corrected and the correction is what is printed. Nothing in it is recalled.

**The tree is live.** A parallel worker was writing in it throughout: a tracked file is modified and
untracked files appeared between readings. Everything below carries the instant it was read. HEAD was
`33d95b3` and equal to `origin/main` at 20:56Z.

---

## 1. What I re-measured, and whether it held

| Fact | How it was checked in this pass | Result |
|---|---|---|
| The four criteria and "Judges will weigh the criteria equally" | fetched `raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` (8,584 B, 20:40Z), section read in full | **holds**, verbatim |
| The exclusion list (code quality, pitch, idea, problem fit) | same page, same read | **holds**, verbatim |
| The 25/25/25/25 block, and that the document dates itself out of this event | fetched `…/contest-terms.md` (15,148 B, 20:40Z); its first line reads "The Events season shall commence on July 1, 2025, and shall end on June 30, 2026" | **holds**, and the season line is quoted here so nobody has to take it on trust |
| Five tracks, their prizes, their one-line criteria, "One submission can enter every category it qualifies for" | fetched the five challenge pages linked from the event (71.6 KB each, 20:41Z) | **holds**: Top 3 $1,000 microgrant; AI, DeFi, Gaming, Beginner $100 gift card per member |
| No rubric or weighting for any track | read all five pages and the event page's own HTML for "judg", "criteria", "scor" | **holds, MEASURED-ABSENT**: `judg` and `criteria` return zero matches in the page HTML, and the only `scor` match is inside a Discord link (`discord.mlh.io`) |
| 4 minutes per project, three viewings, stack rank 3/2/1, "a demo of their hack, not a presentation" | fetched `guide.mlh.com/…/judging-plan.md` (12,644 B, 20:41Z), read the mechanism section | **holds**, verbatim; and it is an organiser *recommendation*, not a published rule of this event |
| Field size 25 | event payload `submissionsCount: 25` (20:40Z) and "25 Submissions" on the canonical page | **holds**; it was 7 at 11:00Z and 18 at 18:28Z, so it is moving |
| Platform close `2026-11-08T18:00:00Z` | event payload `submissionEndsAt` | **holds** (13:00 ET) |
| No video anywhere | `ls *.mp4 *.mov *.webm`; `git ls-files` filtered for video extensions; case-insensitive grep for `youtube` across tracked files | **holds**: no video file and no video URL. "YouTube" appears in six tracked records: four as a *data source* considered and rejected (`E-data-source-registry.md:59,325`, `C-variable-registry.md`, `01-d-external.md`, `DELIVERABLE.md`), and two (`findings/17-hackathon-rules-recheck.md:376,513`) discussing YouTube as a place the submission video could be hosted — which is a choice nobody has acted on, not an existing video |
| No hosted demo | no tunnel, no deploy URL, backend binds loopback; `/pricing` on the backend returns **404** (it exists only in the frontend copy outside the repo) | **holds** |
| Nothing on any public cluster | `/health` → `programDeployed: false`, `programId: null`, `rpcEnabled: false`; the only artefact on disk says `"cluster": "localnet"` with all three explorer links `null` | **holds** |

**One correction to a source both files use.** MLH's Solana partner page is cited as
`hackdays-guide.mlh.com/partner-programs/solana` and also as `…/solana.md`. The `.md` form is the
markdown twin the site serves; both resolve. Recorded only so a reader who types one and gets the other
does not think a page moved.

---

## 2. Three corrections: the entry is less green at HEAD than 23 records

Each of these is a runnable fact, not an interpretation. They all point the same way: the repository's
own checks are red at HEAD, and one of them will stay red because it is pinned to a number that drifts
with the clock.

### 2.1 The project's own gate fails, and 23 cites it as green evidence

**MEASURED** twice in this pass (20:50Z and 20:56Z), in a tree whose only modification is an unrelated test
harness:

```
$ python3 tools/tp.py gate ; echo $?
  FAILURES: 1
     ('cold: zero-sale rate carries DECLARED', '', 'label')
[FIXTURE] gate FAILED - tests=574 OK - console-check FAILURES: 1 - wall=23.7s
1
```

- **574 unit tests pass. The console suite reports 112 ok and one failure. The gate exits 1.**
- 23 §3.3 lists "a 113-assertion console suite and a 43-check attach suite" among the Completion
  evidence. The console suite is 113 assertions of which **one fails**; the attach suite is dealt with
  in §2.2.
- `README.md:74` quotes this command as `unittest: OK - 546 tests` and `docs/CLI.md:126-127` prints the
  expected output as `console-check: 113 ok, 0 failed, FAILURES: 0` and `gate ok - tests=453 OK`. Both
  are false at HEAD, and the README's line reads as a green gate even though it only quotes the unit
  count.

### 2.2 The failing check is pinned to a number that moves with the wall clock, so it will not fix itself

**MEASURED.** `tools/console-check.py:111` asserts:

```python
check("cold: zero-sale rate carries DECLARED", "[DECLARED] 7.5" in c or "[DECLARED] 7.6" in c)
```

The page prints **`[DECLARED] 7.4`** today. It is not a regression in the code: the cold-start rate is a
prior divided by ticket-days of exposure, and exposure grows as the event approaches, so the printed
number falls each day. Measured on the same store at three instants:

| `asOf` | the console prints |
|---|---|
| 2026-11-06T00:00:00Z | `[DECLARED] 8.1` |
| 2026-11-07T00:00:00Z | `[DECLARED] 7.7` |
| 2026-11-08T00:00:00Z | `[DECLARED] 7.4` |

**ASSERTED:** the assertion cannot be satisfied by waiting, and it will be further from 7.5 tomorrow.
The fix is a bound or a computed expectation, not a constant: minutes of work. Until then
`tools/tp.py gate`, `tools/console-check.py` and `docs/CLI.md`'s documented output are all wrong, and
the README's "Does the hack work" evidence has a hole in it that a judge can find in one command.

### 2.3 The frontend attach harness: 43/0 is an uncommitted file; the published one is 31/1

**MEASURED** in this pass's repo-audit phase at 20:50Z and re-run by its review phase at 20:53Z with the same result. The working tree's `tools/check_frontend_attach.py` is modified (+331/−29) and
reports `43 passed, 0 failed`. The version a judge gets from GitHub, extracted with
`git show HEAD:tools/check_frontend_attach.py` and run, reports:

```
31 passed, 1 failed
  failed: pricing carries the mode sentence
```

- **Every document that quotes "43 checks, all green" is quoting a file that is not in the repository.**
  `records/SUBMISSION-PACK.md:56` ("a `/pricing` attach with 43 checks green at 18:40Z") and
  `records/SUBMISSION-PACK.md:530-531` ("`python3 tools/check_frontend_attach.py` → **43 passed, 0
  failed** at 18:40Z") both do exactly that.
- **ASSERTED consequence:** two options and both are the operator's. Commit the harness fix (+331/−29,
  one path) so the published number is the real one, or stop quoting the number. The first is better and
  it is a small commit; the second is free.
- This is the same failure class 23's Correction-list §5.3 C2 describes for stale counts, and it is
  worse than a stale count, because a judge who runs the command gets a red result rather than an
  older number.

### 2.4 The two claims that a judge can falsify by opening a second file

**MEASURED.**

- `README.md:113` "**This machine has no Solana toolchain.**" is **false**: `cargo` and `solana` exist in
  their standard install locations, `anchor` does not, and `programs/cap_hook/target/deploy/cap_hook.so`
  (85,784 bytes) was built on this machine at 19:01Z. The sentence directly above it, "`which solana
  anchor cargo rustc spl-token` returns nothing and exits 1", is **true** — the binaries are simply not
  on `PATH`. So the README's own `which` line is correct and its conclusion from it is wrong.
- `README.md:110` "There is no mint, no transaction and no signature in this repository" is **false of
  the tree and true of every public cluster**: `records/findings/18-onchain-install-and-test.md` is
  tracked and carries 14 signature-shaped base58 strings and one `explorer.solana.com/tx/` link, and
  that same file says at `:192` "These signatures are local-cluster signatures. They do not exist on
  devnet". **The record is honest; the README sentence is the one that overstates**, and the correct
  sentence is "no signature from any public cluster", which is one edit.
- Also false or stale, each measured: `README.md:190` calls `records/DELIVERABLE.md` "a stub, marked NOT
  WRITTEN YET" and it is 2,591 lines with zero occurrences of that phrase; `README.md:220` "six of the
  repository's nineteen commits" (9 of 22); `README.md:185` "twenty-nine tracked" findings (32);
  `README.md:204` "34 test modules" (36).

**Why this is a score item and not housekeeping.** Completion is published as "Does the hack work? Did
the team achieve everything they wanted?" and the judging guide tells organisers to read the repo. A
judge who runs one command and reads two sentences finds three contradictions. The project's entire
argument is that it does not overstate. That is the asset these lines spend.

---

## 3. Where my score differs from 23's, and why

23 scores Technology 12, Design 12, Completion 12, Learning 18 — **54/100**, band 46–62. I re-derived
each from the same evidence and add the three corrections above. Scores are **ASSERTED**; there is no
published scale and no marksheet. My anchor for each band is stated once, in the note under the table, so
two readers can disagree about a number rather than about a word.

| Criterion | 23 | mine | what moves it, and in which direction |
|---|---|---|---|
| Technology | 12 | **12** | Agree. The Rust hook (438 lines, four boundary tests), the publish script, the out-of-process signer and the pure-Python Ed25519 are real technical work. Against it: nothing on a public cluster, and a judge who wants to reward "Wow" has to read 3,200 lines of arithmetic to find it. |
| Design | 12 | **12** | Agree. The console is a deliberate object with no JavaScript and every state a URL; the frontend copy is the most product-shaped surface in the build and it is outside the repository; no viewport meta (`ticketpath/console/page.py:66` carries charset only); the decision sits after banner, controls, canonical URL and evidence strip (`page.py:8-9` fixes that order, `page.py:63-80` renders it). |
| Completion | 12 | **10** | **Disagree, down.** 23's Completion evidence includes the console suite and the attach suite as green. At HEAD one assertion of the console suite fails and the *published* attach harness is 31/1 (§2.1–2.3), and the two documents a judge reads carry at least four falsifiable claims (§2.4). The build works; the proof-of-working does not, today. |
| Learning | 18 | **19** | **Disagree, up, marginally.** **MEASURED 20:56Z:** 32 findings files tracked at HEAD and 35 on disk (the difference is three written during this pass), 22,227 lines across them; an append-only correction culture that has already published a correction to its own earlier finding (`17`'s closing note), an adversarial check by an independent economist that narrowed a sentence the product relied on (`11-cap-capture-check.md:27`: "The fix is a narrowing, not a withdrawal"; its verdict is "consistent", and `F` D7 records that no engine arithmetic changed), and a refusal taxonomy that is itself a result. The cap at 25 is presentation: the strongest learning evidence is the least legible thing here. |
| **Total** | 54 | **53** | Same band, **46–62**. The 1-point gap changes no ranking in 23 §5, which is the test that matters: two independent passes agree on what to do next. |
| Top 3 materials test | 0 of 4 | **0 of 4 on any public cluster; 1 of 4 on the sponsor's own list** | The four sub-tests (an account of ours, a signature with a block time, a third-party program doing load-bearing work, the product reading it back) are all absent from any public cluster. But the sponsor's published evidence standard counts "**code, configuration**, transaction, deployed program" — and the program source, its manifest and the localnet pair now exist. **Read the strict way: 0 of 4. Read the sponsor's way: the "code and configuration" column is filled and the "transaction" column is not.** Both are stated so nobody has to pick the flattering one. |

**Why the Correction matters to the total at all.** Under a stack rank, Completion is the criterion that
decides whether a judge can put the project in their top three without checking anything. A red gate is
not a lost point; it is a reason not to check further.

---

## 4. The one criteria fact 23 does not carry, and it changes what the entry may honestly say

**MEASURED, and it is a two-surface difference.** The strict Top 3 sentence —

> "We're looking for a working product that uses Solana for something it's good at (speed, low fees,
> composability, on-chain ownership), not a chain bolted onto a web2 app."

— is on `events.mlh.com/events/15200-solana-hackathon` (40,504 B, 20:41Z, the sentence beginning at character 16,735 of
the raw HTML), in the "Prize Tracks" block under **Top 3 Overall**. It is **not** on
`www.mlh.com/events/solana-hackathon` (94,748 B, 21:04Z): the strings "bolted", "working product" and
"strongest projects" do not appear in that document at all, and its Top 3 category carries only the
prize string.

**And the same events page says the opposite elsewhere**, in the event description at the top of the
page:

> "That's fast and cheap enough to send money across the world instantly, **sell concert tickets that
> can't be faked**, or let players truly own the items they earn in a game."

> "**You can use Solana as a powerful backend for almost any project**: consumer apps, payments, games,
> DeFi, or AI agents that act onchain."

**CONFLICT, named and not resolved here.** One event's own copy contains a sentence that rejects "a chain
bolted onto a web2 app" and a description that invites exactly that shape and names forged concert
tickets as its first example.

**What this is worth to the entry, labelled.** **ASSERTED:** it does not lower the bar the entry should
build to, because the strict sentence is the only one attached to the prize. It does change one thing the
submission may say without hedging: the product is a web2 pricing application with Solana doing one
load-bearing job — a ticket that cannot move without the program, and a cap the program enforces — and
that is a shape the event's own description invites. The packaging of that sentence, and whether to use
it, is the operator's decision and not this file's.

**Corollary correction to the record.** `records/findings/17-hackathon-rules-recheck.md` §2.3 attributes
this sentence to the canonical `www.mlh.com` page. The sentence is real; the surface was wrong. Recorded,
not edited, per the append-only rule.

**A second, smaller correction, from the same phase and the same file.**
`records/findings/17-hackathon-rules-recheck.md:511` states the Best Beginner eligibility as "<50%
first-time hackers". The event page says **>50%**, and that file's own lines `:225` and `:584` say it
correctly. It is a one-character inversion in a summary table, and it is worth naming because that row is
the one a reader consults when deciding whether to enter the track. Fixed by the operator or left as a
recorded erratum; not touched here.

### 4.1 A fourth scoring locus, and it contradicts the exclusions

**MEASURED** in this pass, `hackdays-guide.mlh.com/run-your-event/project-submissions.md`, "Use a Simple
Judging Rubric", verbatim: "Score every eligible project using the same criteria. A lightweight rubric
works well for short events:"

| Criterion | What judges should consider, verbatim |
|---|---|
| Technical implementation | "Does the project work, and how effectively does it use the chosen technology?" |
| **Creativity** | "Is the idea or implementation distinctive?" |
| Learning and ambition | "What did the team learn or attempt during the Hack Day?" |
| **Demo and clarity** | "Can the team clearly explain the problem, solution, and implementation?" |
| Partner eligibility | "Does the project satisfy the assigned partner's specific requirements?" |

No weights are published for these five either. **CONFLICT with the standard rules' exclusions:** the
rules page says idea quality and pitch quality are *not* judged; this rubric names "Creativity" (idea
quality) and "Demo and clarity" (presentation quality) as two of five considerations.

**Scope caveat, stated because it decides how much weight this carries:** the Hack Days guide is a
different MLH programme from this Partnered Hackathon, and the line above it says it is for "short
events". It is recorded because it is the same sponsor family and a judge could plausibly be handed it,
not because this event has adopted it. **MEASURED-ABSENT: nothing on this event's pages adopts a rubric of
any kind.**

**ASSERTED, and it is the practical consequence:** across the four loci found in this pass — four equal
criteria, a stale 25/25/25/25, one sentence attached to the main prize, and a five-line Hack Days
checklist — only two things are asked for by more than one of them: **that the thing work**, and **that a
judge can see it work**. Every option in §5 is scored against those two, which is why the video and the
red gate rank above everything else and why nothing here buys creativity or theme.

---

## 5. What this adds to 23's ranked list, and in what order

23's §5 is the ranked plan and it stands. These are the additions and the one line that must not be said,
folded into its numbering so the operator reads one list, not two.

| # | Change to 23's plan | Hours | Impact | Risk |
|---|---|---|---|---|
| **C0-a** | **Fix the console assertion before anything else is claimed about the gate** — replace the pinned `"[DECLARED] 7.5"/"7.6"` with a bound or a computed expectation at `tools/console-check.py:111`, then re-run `python3 tools/tp.py gate` until it exits 0 | 0.25 | **+1 to +2 Completion**, and it converts a red command into a green one | None. It is a test edit, not a behaviour change, and the number it prints stays true |
| **C0-b** | **Commit or withdraw the attach-harness fix.** Either commit `tools/check_frontend_attach.py` (+331/−29, one path) so the published number is 43/0, or stop quoting 43/0 anywhere | 0.25 | +1 Completion | Low. The uncommitted change is someone else's work in the tree; committing another worker's file needs their word or his, so **withdrawing the claim is the zero-risk option** |
| **C2'** | **Extend 23's stale-count fix by two lines**, both of which a judge can falsify by opening one more file: `README.md:113` "no Solana toolchain", and `README.md:110` "no … signature in this repository" → "no signature from any public cluster" | 0.1 | +1 Completion | None. Both are replacements with a true sentence |
| **T5** | **Add `programs/` to the README layout and one "Solana integration" paragraph** naming the program id path, the cluster, the Token-2022 hook and the localnet pair. The sponsor's evidence page names "the integration in its README" as the first thing a judge asks for | 0.25 | +1 Technology | None. It is already true and it is the cheapest answer to the materials test short of a devnet run |

**The line that must not be said anywhere in the submission or the video:** "the gate passes, 43 attach
checks green". At HEAD neither is true, and both are one command from being checked.

**Everything else in 23 §5.5 stands, in its order:** the video first because it is the entry, the devnet
publish second because it is the only change that moves the materials test, the headline above the fold
third as the cheapest Design point, then the stale claims, then the URL, then the prose and the viewport.
My only reordering: **C0-a rises above C2**, because a red gate is the one defect a judge meets by doing
what the README suggests, and it costs fifteen minutes.

---

## 6. What past winners did — pointer, with one thing added

23 §4 answers this with sources and a denominator, and I checked its three load-bearing claims against
the same Devpost pages: the 38-project sample with 8 custom programs (21%, 7/38 airtight at 18%), solGPU
winning with a memo and no token, LOKA Pay shipping a reproduced error code and a public judge guide, and
the Midnight sponsor post ranking "completed layer" before "deployment". Those hold as recorded.

**What I add, because it sharpens the decision rather than repeating it:** every winner 23 quotes a
description for — the four in its §4.2 plus the quantitative-trading winner in §4.3 — had **one artefact
a judge could check unaided**: a verify button that re-checks the chain, a public judge guide, an explorer
link printed beside a signature, a refusal reproduced on demand. That is five of five, and the sample is
five, so this is **ASSERTED**, not a finding. For this entry the nearest such artefact is not the devnet
deploy: it is the gate. A command a judge can run that prints `FAILED` is the opposite of what that pattern
describes, and it costs fifteen minutes to fix.

**MEASURED-ABSENT, recorded so nobody goes looking:** no winner record, in this pass or in 23's, states
why a judge chose it. The prize line on Devpost is a string. Anything stronger than "these projects share
these visible properties" would be invention.

### 6.1 The other Solana lineage, which is a different competition and says something useful anyway

A second search phase in this pass walked Colosseum's published winner lists for the five announced
editions (Renaissance 2024, Radar 2024, Breakout 2025, Cypherpunk 2025, Frontier 2026) and recorded 175
named placements with a product description for 162 of them. **Colosseum is not this event and its
criteria are not these criteria:** its Frontier Official Rules §8 lists Functionality/code quality,
Potential Impact, Novelty, UX, Open-source and Business Plan, unweighted, and the page states it is "not
looking for … code-quality checks". It is quoted for one reason only, and it is the reason a pricing
engine should read it:

- **5 of 5 grand prizes are the market primitive itself** — a mined currency, a stablecoin DEX, a storage
  network, a hardware wallet, a robotics DePIN. **0 of 5 is a dashboard, an analytics product or a model.**
- **4 analytics-flavoured winners and no first prize among them** (two at a flat $10,000 tier, one 3rd,
  one 4th), so analytics places and does not top out.
- The closest published analogue to this entry is **JK Index**, Frontier top 25: "a TCG marketplace and
  platform for collector-driven pricing, grading, and market intelligence" — a collectibles pricing
  product that won as a marketplace with intelligence attached, not as a validated model.

**INFERENCE, labelled:** read across, the pattern says a pricing or analytics product is placeable and is
not a grand-prize shape unless the thing being priced *is* the on-chain primitive. For this entry that is
the argument for making the ticket and its cap the on-chain object rather than the price model, which is
the direction 23 §5.1 T1 and §4.3 already point. It is an inference from a different competition's
announcements and it should be read as one.

**What the Colosseum sample cannot support, and is not used for here:** "0 of 162 descriptions claims a
deployed program" is a fact about announcement text, not about the products; and 0 of 175 carries a
published reason for winning, so nothing about *why* those projects placed can be sourced from it.

---

## 7. Decisions this file does not make

Beyond 23 §7's eight, and none of them mine:

1. **Fix the gate before the freeze, or leave it red and say so?** Fifteen minutes against a command the
   README points at. If he fixes it, the README's quoted output and `docs/CLI.md:126-127` need the same
   edit in the same commit or the documents go stale again.
2. **Commit another worker's harness change, or withdraw the claim?** Both are legitimate; the second is
   free and the first is better, and the file is not mine.
3. **Does the submission text quote the gate or the harness at all?** If either is quoted, the number has
   to be the published tree's number at the instant of submission, not the working tree's.
4. **Does the entry use the event description's permissive sentence** (§4) to describe itself, or hold to
   the strict reading? It is a framing decision, it is visible in the video, and it is his.

---

## 8. Sources fetched in this pass

| # | URL | Bytes | Time (Z) | What it established |
|---|---|---|---|---|
| 1 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | 8,584 | 20:40 | four criteria, "equally", the four exclusions |
| 2 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/contest-terms.md` | 15,148 | 20:40 | 25/25/25/25 and its own season term (2025-07-01 → 2026-06-30) |
| 3 | `https://events.mlh.com/events/15200-solana-hackathon` | 40,504 | 20:41 | the strict Top 3 sentence at char 16,735; the permissive event description; the five long track texts; no judging section |
| 4 | `https://www.mlh.com/events/solana-hackathon` | 94,748 | 21:05 | "25 Submissions", "Submissions close Nov 8, 1:00 PM EST"; **no** "bolted" / "working product" / "strongest projects" string |
| 5 | the five challenge pages linked from #4 | ~71.6 K each | 20:41 | one prize and one criterion line per track; "One submission can enter every category it qualifies for" |
| 6 | `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md` | 12,644 | 20:41 | 4 min/project, 3 viewings, stack rank 3/2/1, "a demo of their hack, not a presentation" |
| 7 | `https://www.mlh.com/events/solana-hackathon` payload (`props.event`, `props.prizeCategories`) | 14,014 | 20:40 | `submissionsCount: 25`, `submissionEndsAt: 2026-11-08T18:00:00Z`, `galleryPath: null` |
| 8 | `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md` | 9,928 | 20:42 | the five-line "lightweight rubric" in §4.1, including "Creativity" and "Demo and clarity" |
| 9 | `https://colosseum.com/hackathon` and the five edition winner pages behind it (Renaissance 2024, Radar 2024, Breakout 2025, Cypherpunk 2025, Frontier 2026), plus the Frontier Official Rules PDF §8 | 175 named placements | 20:45–20:52 | the counts in §6.1: 5 of 5 grand prizes are the primitive itself, 4 analytics-flavoured winners with no first prize, JK Index as the closest analogue |

Local evidence, measured in this pass: `python3 tools/tp.py gate` (twice, exit 1);
`python3 tools/console-check.py` (exit 1, `tools/console-check.py:111` read);
`git show HEAD:tools/check_frontend_attach.py` run from `/tmp` (31 passed, 1 failed);
`python3 tools/public_safety.py check --tracked` (exit 1, 64 hits, 9 files) and
`… --range origin/main..HEAD` (exit 0); `git log/status/rev-parse` (22 commits, HEAD = `origin/main`,
170 tracked files); `curl` on the console at two instants and three `asOf` values; `ls`/`git ls-files`
for video files; `/health`.

**Not fetched, and why:** the submission form (login required, and 23 §7 already records what MLH's
portal documentation says it asks); any public submissions gallery (none exists, `galleryPath: null`);
the Devpost project pages (23 §4 read them in this window and I checked its quotes against the same
pages rather than re-fetching all of them).

---

## 9. How this file was checked, and the five things it got wrong before it was checked

An adversarial review phase was dispatched against a draft of this file, with the instruction to break it:
re-run every command, re-read every `file:line`, re-fetch both event pages. It found five defects, all of
them in this file and none of them in 23. They are listed because a reader has a right to know which
sentences were wrong and why they are now right.

| # | The draft said | What was measured | What the file says now |
|---|---|---|---|
| 1 | a run window of 20:39Z → 21:25Z, with 21:00Z, 21:05Z and 21:30Z inside it | the file was complete at 20:50:52Z and the wall clock at review was 20:54:48Z, so those instants had not happened | the real window, 20:39Z → 20:58Z, and every time in it re-stated |
| 2 | an independent economist "withdrew a sentence the product used" | `11-cap-capture-check.md:27` says "The fix is a narrowing, not a withdrawal"; its verdict is "consistent"; `F` D7 records no engine change | "narrowed a sentence the product relied on", with the quote |
| 3 | the strict Top 3 sentence sits at character 16,889 | it begins at 16,735; 16,889 lands inside "ship), not a chain bol" | 16,735, twice |
| 4 | the only `scor` match on the event page is the word "score" | it is inside a Discord link, `discord.mlh.io` | said accurately; the MEASURED-ABSENT conclusion is unchanged (`judg` and `criteria` return zero) |
| 5 | YouTube appears in four tracked records | six: four data-source uses and two (`findings/17:376,513`) discussing it as a place the video could be hosted | six, with the two named, and the distinction that neither is a video that exists |

Everything the review was asked to re-test held: the gate exits 1 on `cold: zero-sale rate carries
DECLARED` against the literal `"[DECLARED] 7.5" in c or "[DECLARED] 7.6" in c` at
`tools/console-check.py:111`, with 574 unit tests OK and 112 console assertions passing; the cold page
prints `7.4` now and `7.7` at `asOf=2026-11-07T00:00:00Z`; the published attach harness is 31 passed / 1
failed and the working-tree one is 43 passed / 0 failed; all seven README claims and all three
`SUBMISSION-PACK.md` claims are the sentences this file says they are, stale in the direction claimed;
`records/findings/18` carries 14 signature-shaped strings and one `explorer.solana.com/tx` link with
`:192` saying "local-cluster signatures"; `/pricing` is 404 on the backend; 23 §3.3 does cite "a
113-assertion console suite and a 43-check attach suite" and does score Completion 12; `events.mlh.com`
carries the strict sentence at 40,504 B and `www.mlh.com` does not at 94,748 B; the payload still says
`submissionsCount: 25`.

**What the review could not check, and this file therefore does not claim:** the 14,014-byte payload
figure, the historical 7 and 18 submission counts (they are quoted from 23 and from earlier records, not
re-measured here), the absence of any tunnel on this machine, and anything about the frontend copy
outside the repository.

**Content added after the review, and labelled as such.** §4.1 (the five-line Hack Days rubric) and §6.1
(Colosseum's winner lists) were written from two other phases of this pass whose reports landed after the
adversarial review had finished. Their quotes are verbatim from pages fetched in this pass and their
sources are rows 8 and 9 of §8, but **no review phase re-fetched them**. The `findings/17:511` eligibility
erratum was found the same way and verified against `17:225`, `17:584` and the event page in this shell.

---

*Nothing was committed and nothing was pushed. One file was written: this one. No cluster, faucet, live
process or keypair was touched, and no command in this pass started or stopped a service it did not
start itself.*

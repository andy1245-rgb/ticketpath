# 19 — Corpus citations and reproductions: the `mlh-solana-2026` audit

**Status:** complete for the question it answers. **Written:** 2026-11-07T18:55Z. **Agent:** `p19-corpus-audit`.
**Scope:** every place in this repository, tracked or untracked, that names, cites, quotes or reproduces
`../research/mlh-solana-2026/` (fifteen documents, 2026-11-06); whether each hit is a citation or
reproduced text; whether anything sensitive sits in the passages that were reproduced; and the
timeline the submission can state truthfully. **Read-only against the corpus:** nothing under
`../research` was opened for writing, and no file there was modified.

**Evidence labels.** **MEASURED** = I ran the check and it returned this. **ASSERTED** = my reasoning.

**Decision this answers to, and does not revisit.** The operator decided not to publish the corpus.
This file does not argue with that and does not publish it. It measures what already left the corpus
in the repo's own text, which is a separate question from whether to publish the corpus itself.

---

## What I concluded

1. **The corpus is cited in 91 lines across 7 files. Six of those files are tracked, therefore
   already published on the public remote.** One is untracked and git-ignored: `NIGHT-BRIEF.md`.
   `records/findings/17-hackathon-rules-recheck.md` became tracked in commit `0d6cf35` while this
   audit was running, so it is now published too.
2. **One file reproduces the corpus's own prose at length and it is already published:
   `records/00-prior-direction-index.md`.** 17 of its 60 hit lines carry verbatim corpus text, its
   longest unbroken verbatim run is 40 words, and 8.0% of its eight-word sequences appear verbatim
   in the corpus's own prose. Every one of those reproductions is attributed to a document and a
   section on the same line, so it reads as an index quoting its sources, not as text passed off as
   fresh work.
3. **The other four tracked files are citations, not reproductions.** Their overlap with the corpus
   is almost entirely text that both documents quote independently from a third party (MLH's rules,
   the event page, Solana's docs, Devpost URLs). `records/findings/02-rubric-and-scoring.md` never
   names the corpus at all except to correct it.
4. **Nothing sensitive is in the reproduced passages. MEASURED.** No credential, no keypair, no
   seed phrase, no personal data, no private contact detail, no third-party non-public material.
   The only contact data the corpus holds is MLH's own published reporting addresses and three
   regional incident phone lines; only one address reached the repo, and it is already allow-listed
   with a reason. The exposure here is provenance, not privacy.
5. **The premise "before the event" is false, and the repo states it as fact in three places.**
   Hacking began at 2026-11-06 17:00Z. The corpus files were written 17:39:04Z to 18:48:55Z the
   same day, that is 39 minutes to 1 hour 49 minutes *inside* the window, not before it. The repo's
   correct formulation is the one already in `records/00-prior-direction-index.md:3`, "before this
   VM and before the session that launched tonight", which is true. The three places that say
   "pre-event" or "the day before hacking began" must be corrected before Sunday.
6. **Recommended provenance sentence, in full, in §7.** It states the measured times and makes no
   claim the repository cannot support.

---

## 1. How the hit list was built

Four checks, all re-runnable:

- **Name and path.** Grep for `mlh-solana-2026` and for each of the fifteen file stems, across
  tracked and untracked files, excluding `.git`.
- **Quoted strings.** Every quoted span of five words or more in the hit files, tested for an exact
  match inside the corpus. 94 matched.
- **Eight-word sequence overlap,** tagging each corpus occurrence as either inside a quotation in
  the corpus (a third party's words) or outside one (the corpus author's own prose). This is what
  separates a citation of MLH's rule from a copy of the corpus's analysis.
- **Longest unbroken verbatim run** per file, so a single quoted sentence is distinguishable from a
  reproduced paragraph.

**MEASURED, the two files that carry almost all of it:**

| file | 8-word seqs matching corpus prose | longest verbatim run | tracked |
|---|---|---|---|
| `records/00-prior-direction-index.md` | 413 of 5,192 (8.0%) | 40 words | **yes** |
| `records/findings/02-rubric-and-scoring.md` | 57 of 6,617 (0.9%) | 78 words (all third-party rule text) | **yes** |
| `records/findings/02-ai-ml-decision.md` | 2 of 6,025 | 41 words (event-page text) | yes |
| `docs/ON-CHAIN-DESIGN.md` | 4 of 17,168 | 11 words | yes |
| `records/SUBMISSION-PACK.md` | 1 of 11,195 | 15 words | yes |
| `records/F-decision-log.md` | 0 | 11 words | yes |

Every other tracked file is at or below four matched sequences, which is a shared URL or a shared
technical term, not reproduction.

---

## 2. The complete hit list

`C` = citation only, names the corpus or a document in it, no corpus text copied.
`R` = reproduces corpus text verbatim or near-verbatim.

### `records/00-prior-direction-index.md` — **tracked, published** (60 hit lines, 17 of them `R`)

An index of the fifteen documents, written to stop a later session re-litigating settled decisions.
It opens by naming the corpus and says all fifteen were read in full from the read-only source.

| line | class | what it is |
|---|---|---|
| 3 | C | names `../research/mlh-solana-2026/`, says "fifteen documents written on 2026-11-06" |
| 42–56 | C/R | the fifteen-row table. R at 47, 49, 53, 56 (quotes each document's own date line verbatim) |
| 64, 75, 90, 100, 110, 122 | C | section headings for each conflict |
| 151 | R | quotes the AI-track decision row |
| 152 | C | cites `p2b` §4.3 |
| 154 | R | quotes the "Best Beginner" line |
| 158 | R | quotes the "do not pitch the concept" line and the p2b verdict |
| 160 | R | quotes the "never say NFT ticket" instruction |
| 167 | R | quotes the burn-only-exit rule |
| 169 | C | cites the extension stack and the four-extension identifier |
| 170 | R | quotes the `--decimals 0` rule |
| 178 | R | quotes the don't-film-the-wallet-popup rule |
| 192 | R | quotes MLH's pitch-discouraged rule |
| 214 | C | cites the microgrant inference flag |
| 215 | R | quotes the Top-3 valuation inference |
| 217, 219 | C/R | cites the Superteam attribution; quotes the snapshot caveat |
| 230 | C | cites the 38-winner sample caveat |
| 238 | C | the four devnet identifiers do not resolve |
| 239, 240 | R | quotes the devnet claim and the "executed and verified" claim, both being corrected |
| 248 | C | cites the self-assessment table |
| 259–273 | C | the artefact table, one row per document |
| 281–283 | C/R | cites provenance supremacy; quotes the supersession sentence |
| 290 | C | notes `p3-decision.md` has no date line |

**What this file is, in the operator's terms.** It is a citation-plus-quotation file: every `R` line
names the document and section it is quoting, on the same line. It is not text passed off as the
repo's own research. But it is the corpus's prose, in condensed form, sitting in a public repository,
and that is a fact the provenance sentence has to cover rather than deny.

### `records/findings/02-rubric-and-scoring.md` — **tracked, published** (10 hit lines, 1 `R`)

| line | class | what it is |
|---|---|---|
| 112 | C | cites `p1a` for the 8-of-38 custom-program figure |
| 292 | C | says the escrow primitive is what `p5` specified |
| 320 | C | cites `p2a-verified-spike`'s "executed and verified" claim, then contradicts it from this machine |
| 373 | C | cites `p1a` alongside D3 |
| 401 | C | overturns `03-what-wins-solana` §4.5 |
| 407 | C | cites the `p3` §4 ground for skipping a track |
| 408 | C | confirms `04-mlh-judging-playbook` §1.6 |
| 414 | C | corrects `p1d-video-judging` §4.1's field-size estimate |
| **421** | **R** | quotes `p5-build-spec` §0's "every command and error string here was executed", **in order to retract it** |
| 504 | C | cites what `p5` assumes about judges |

**The 78-word run in this file is MLH's own numbered digital-event submission rules**, which the
corpus also quotes. Both documents quote the same public rule; neither copied the other. This file
does not name the corpus as an authority anywhere, and its seven citations are all corrections or
overturnings, which is the opposite of borrowing.

### `records/findings/02-ai-ml-decision.md` — **tracked, published** (4 hit lines, 0 `R`)

| line | class | what it is |
|---|---|---|
| 8 | C | states the file confirms, corrects or overturns `p3` §4 and `p5` §9 |
| 476–478 | C | the source list, one line per document, section by section |

### `records/SUBMISSION-PACK.md` — **tracked, published** (1 hit line)

| line | class | what it is |
|---|---|---|
| 619 | C | **Question 2**, the open question about the corpus. Line 620 continues it with the false "day before hacking began". |

Also line 69 and line 623, which both call it "the pre-event research corpus" without naming the
path. Same error, three places in one file.

### `records/F-decision-log.md` — **tracked, published** (1 hit line)

| line | class | what it is |
|---|---|---|
| 125 | C | records that the decision confirms `p3` §4 and `p5` §9 in outcome |

### `records/findings/17-hackathon-rules-recheck.md` — **tracked since `0d6cf35`, published** (10 hit lines, 0 `R`)

| line | class | what it is |
|---|---|---|
| 32–34 | C | the corpus listed as one of the sources re-checked |
| 196 | C | cites `04-mlh-judging-playbook` §1.1 for a date |
| 286 | C | cites `p1a` for solo builds winning |
| 376 | C | cites `p1d-video-judging` on the video host |
| 512, 513 | C | cites `04-…` §2.1 and `p1d` on the re-verification table |
| 524 | C | calls the corpus "prior work in the ordinary sense", correctly dated 2026-11-06 |
| 528–530 | C | calls it "pre-event material" and treats it as a documentary hazard, not a code one |
| 580 | C | open question 5, "the pre-event research corpus", drawn from company or private data |

### `NIGHT-BRIEF.md` — **untracked, git-ignored** (5 hit lines, all C)

Lines 37, 100, 101 name the corpus as input; 115 and 118 cite the AI-track decisions. Handover
material, stays local by rule. Not a publication risk.

---

## 3. Files with overlap but no corpus reference

These matched on quoted strings and carry no citation, because what they quote is the primary
source, which the corpus also quotes:

- `records/STATE-OF-PROJECT.md` (untracked) — quotes MLH's four rubric criteria and the event page's
  "not a chain bolted onto a web2 app" sentence.
- `records/findings/00-verification-round1.md` — the same event-page sentence, 28-word run.
- `docs/ON-CHAIN-DESIGN.md` — "sell a 501st ticket for a 500-seat room", a product line both files
  use, and a vendor install command line.
- `records/SUBMISSION-PACK.md:521`, `records/findings/02-ai-ml-decision.md:279`,
  `records/findings/02-rubric-and-scoring.md:106,221` — MLH's published reporting address, allowed
  in `.public-denylist:115` with its reason.

No corpus document is duplicated in the repository. **MEASURED:** first headings compared across all
fifteen corpus files and every tracked markdown file, no match.

---

## 4. Is anything sensitive in the reproduced passages?

**MEASURED, per class.**

| class | in the corpus | in the reproduced passages | verdict |
|---|---|---|---|
| Credentials, keypairs, seed phrases, API tokens | none | none | clean |
| Solana keypair files (the 64-integer shape) | none | none | clean |
| Personal data (name, address, phone of a person) | none | none | clean |
| Operational contact detail | 4 organisational addresses, 3 MLH regional incident phone lines | 1 address (`cheating@mlh.io`), no phone line | allow-listed, published by MLH |
| Third-party non-public material | none found | none | clean |
| Confidentiality markings | none. Every "confidential" hit is the Token-2022 `ConfidentialTransfer` extension name | none | clean |
| On-chain identifiers | 4 devnet identifiers, 1 Token-2022 program id | the same 4, at `00-prior-direction-index.md:169,270` | not secrets: public-chain addresses and signatures, already labelled "prior work, not this project's" |

**The one thing worth naming.** The corpus holds MLH's incident-reporting phone lines and four
organisational addresses. The addresses are published by MLH for exactly this purpose, and the phone
lines never reached the repo. A judge opening a public repository and finding MLH's own complaints
address quoted as the rule that was read is reading a citation, not a leak.

**What the corpus holds that is genuinely third-party:** a crawl of public Devpost project pages, and
quotations from MLH and Solana's own published rule pages. Both are public documents. The index
records that the crawl dataset was never stored (`00-prior-direction-index.md:265`, "no path, no
saved dataset"), so there is no dataset in the corpus to publish or withhold.

---

## 5. The timeline, measured

**MEASURED.** Machine clock is UTC.

| event | time | offset from hacking start |
|---|---|---|
| Hacking begins (opening ceremony, Fri 12:00 PM ET) | 2026-11-06 17:00:00Z | zero |
| First corpus file written (`03-what-wins-solana.md`) | 2026-11-06 17:39:04Z | **+39 min 04 s** |
| Last corpus file written (`p1b-tech-feasibility.md`) | 2026-11-06 18:48:55Z | **+1 h 48 min 55 s** |
| First commit (`744a2c2`) | 2026-11-07 08:29:57Z | **+15 h 29 min 57 s** |
| Last commit (`0d6cf35`) | 2026-11-07 18:48:05Z | +25 h 48 min 05 s |
| Gap, last corpus write to first commit | | **13 h 41 min 02 s** |
| 20 commits spread over | | 10 h 18 min 08 s |

**The corpus is inside the window, not before it.** All fifteen files were written between 17:39 and
18:49 UTC on the opening day, which is after 17:00Z. Ten of the fifteen were written after 18:17Z.
All fifteen mtimes fall inside one 69-minute band and the last three land 3 seconds apart, which is the
signature of a batch write rather than fifteen sequential sessions.

**A conflict inside the corpus itself, worth recording.** Several documents state their own writing
times in ET and those statements do not reconcile with the mtimes. `p5-build-spec.md` claims it was
"written ~15:00 ET, corrected ~15:30 ET"; its mtime is 18:48:55Z, which is 13:48 ET. A file cannot
be last written at 13:48 ET and claim a 15:30 ET correction. Either the internal times are narrated
rather than read off a clock, or the machine that wrote them was in a different zone than the
documents assume. **Either way the mtimes are the only clock-independent evidence, and they put the
corpus after 17:00Z.** Any statement built on the documents' own ET lines is unsupported; a statement
built on the mtimes is.

---

## 6. What the repo claims, and the three claims that are wrong

**Correct, leave alone:**

- `records/00-prior-direction-index.md:3` — "fifteen documents written on 2026-11-06, before this VM
  and before the session that launched tonight". True: this VM's first commit is 2026-11-07 08:29Z.
- `records/findings/17-hackathon-rules-recheck.md:520` — "earliest commit 2026-11-07T08:29:57Z, 15 h
  29 min after hacking began. Nothing in the tree is backdated, and nothing predates the window."
  Verified against `git log`. True, and it is the claim the cheat-check actually tests.
- `records/findings/17-hackathon-rules-recheck.md:524` — the corpus is "prior work in the ordinary
  sense", dated 2026-11-06. True, and it makes no pre-event claim.

**Wrong, correct before submission:**

| where | what it says | why it is wrong |
|---|---|---|
| `records/SUBMISSION-PACK.md:619–620` | "was written 2026-11-06, **the day before hacking began**" | Same day, 39 min to 1 h 49 min **after** hacking began |
| `records/SUBMISSION-PACK.md:69` | "the **pre-event** research corpus" | Not pre-event |
| `records/SUBMISSION-PACK.md:623` | "quoting anything from the **pre-event** corpus" | Not pre-event |
| `records/findings/17-hackathon-rules-recheck.md:580` | "the **pre-event** research corpus" | Not pre-event |
| `records/findings/17-hackathon-rules-recheck.md:528` | "where **pre-event material** did get in" | It is in-window material |
| `records/findings/17-hackathon-rules-recheck.md:646` | "Is the **pre-event** research corpus his to quote?" | Not pre-event |

**Why this matters more than it looks.** The submission pack's answer to MLH's cheat-check question
"Did they start before the event?" is "no", and it rests that answer on a claim that is false. The
answer is still correct, but for a different reason: the *repository* starts 15 h 30 min after
hacking began, and the corpus is reading, not code. State it the true way and the answer survives
scrutiny. State it the current way and a judge who asks for file times catches a wrong sentence
guarding a right answer.

**The correction is also the stronger position.** Notes written inside the window are unambiguously
permitted. Notes written before it are the thing MLH's prior-work rule exists to exclude. The
current wording claims the riskier of the two facts and does not need to.

---

## 7. Recommended provenance sentence

For the submission pack and the video description. Plain, measured, defensible if a judge asks for
file times.

> **Provenance.** Background reading for this entry was done between 17:39 and 18:49 UTC on 6
> November 2026, inside the first two hours of the hackathon window and not before it, and was never
> committed to this repository. No code and no submitted artefact derives from those notes; the
> research record cites them, with attribution, only where it records a decision they settled. Every
> commit in this repository post-dates the opening ceremony, the first at 08:29 UTC on 7 November
> 2026, fifteen and a half hours after hacking began.

Short form, for a form field with a character limit:

> All code in this repository was written inside the hackathon window, from 08:29 UTC on 7 November
> 2026. Background reading done in the first two hours of the window is not in the repository and is
> not part of the submission.

**Why these are safe to say.** The times are from `stat` and `git log`, both re-runnable by anyone.
"No code derives from those notes" is true and checkable: there is no TypeScript, no Anchor program
and no file from the corpus's build spec anywhere in the tree. "Cites them, with attribution" is
true and is what `records/00-prior-direction-index.md` does on every line that quotes. **Nothing in
either sentence claims the corpus is pre-event**, which is the claim that cannot be supported.

**Do not say**, in any field: that the research was done before the event; that the corpus was
written the day before hacking began; or that no text from the corpus appears in the repository.
The first two are false and the third is false because the index quotes it.

---

## 8. Open, and not mine to close

1. **Whether the index should keep its verbatim quotations at all.** Trimming `00-prior-direction-index.md`
   to citations with no quoted text would make "no text from those notes appears in the repository"
   true and would remove the tension entirely. That is a call about how much of the corpus's reasoning
   the repo needs to carry forward, and it belongs to the operator, not to this audit. I did not
   change the file.
2. **Whether the corpus drew on company or private data.** Already open as question 5 in
   `17-hackathon-rules-recheck.md:580`. I looked for the shapes of that (credential, contact detail,
   non-public marker) and found none, but absence of those shapes is not proof of clean provenance,
   and only he knows what he read it against.
3. **`records/SUBMISSION-PACK.md:614` and `:64` need editing** in the same commit that fixes question
   2, so the pack does not answer its own question with the wrong premise.

---

## 9. Limits of this audit

- **It measured overlap, not intent.** An eight-word sequence match proves two documents share
  wording, not which came first. Where a claim rests on direction rather than on a date, I said so.
- **Two sentences of the corpus are indistinguishable from a primary source** in more than one place,
  because they *are* primary source. `docs/ON-CHAIN-DESIGN.md` and `records/STATE-OF-PROJECT.md`
  quoting the event page is not a corpus citation, and I have not counted it as one.
- **It does not read git history for text that was later removed.** The check is against the current
  tree. If corpus text was committed and then deleted in an earlier commit, it is still published,
  and finding that is a `git log -S` job on a specific phrase, not a tree scan.
- **The tree moved while this was being written.** Commit `0d6cf35` landed at 2026-11-07T18:48:05Z,
  after the first pass over this audit, and it added the disclosure and provenance wording the rules
  require. It did **not** touch any of the six "pre-event" sentences in §6, and it brought
  `records/findings/17-hackathon-rules-recheck.md` into the tree, which promoted it from a local note
  to published text. Every line number and every git figure here was re-measured at `0d6cf35`. If the
  repo commits again before Sunday, re-run the name scan rather than trusting these numbers.
- **This file matches its own grep.** Re-running the name scan now returns 16 lines in this file,
  because it has to name the corpus to report on it. Those are the audit, not a finding, and any
  future count should exclude this path. The corpus-facing total excluding this file is **91 hit
  lines in 7 files, 18 of them verbatim.**
- **It says nothing about the seventeen other public-safety classes.** `tools/public_safety.py check`
  on the tracked tree returns **77 hits in 11 files** (51 live-service, 23 home-path, 3 fleet-repo),
  exit 1, "do not commit or push this". None of them is a corpus citation; all are the classes
  `AGENTS.md` already names as incidents. That is a separate and larger problem than this audit and
  it is not fixed here.

---

## CORRECTION (2026-11-07T18:55Z) — the `0d6cf35` references are a superseded object, not a published commit

**What is wrong.** This file names `0d6cf35` five times, as the commit that brought
`records/findings/17-hackathon-rules-recheck.md` into the tree and as the "last commit" the git figures
were measured at (§4, §5's table, §9). That object exists on disk and it is **not** in the published
history. `git merge-base --is-ancestor 0d6cf35 HEAD` returns false and no branch contains it: it is the
first version of the commit that carried that message, authored at 2026-11-07T18:48:05Z, which was amended
three times in place. `git reflog` shows the chain: `0d6cf35` at 18:48:05Z, then `cae9c3d` at 18:48:55Z,
`3d4007c` at 18:49:09Z, and the object the branch holds, **`3471fcb`**, at 18:49:23Z, same parent
(`8a5e5e6`), same author, same message, a different tree.

**What to read instead.** Every `0d6cf35` in this file means **`3471fcb`**, "Correct stale claims and add
the disclosure and provenance wording the rules require", 2026-11-07T18:49:23Z, the twentieth commit and
the one that is published as `main`. Nothing measured against the tree changes: the amendment rewrote the
commit object, not the facts, and the times in §5 (first commit `744a2c2` at 08:29:57Z, last commit
18:48:05Z, twenty commits over 10 h 18 min 08 s) still read the same off `git log` at `3471fcb`. The
lesson is in this file's own §9 warning — the tree was moving while it was being written, and an amended
commit is a moving tree with the same timestamps.

**Two further corrections, both from the same commit.** (1) `records/SUBMISSION-PACK.md` §2.8's question 2
and §0 item 9 no longer call the corpus "pre-event" or "the day before hacking began"; they carry the
measured times (17:39:04Z to 18:48:55Z on 2026-11-06, inside the window), the operator's answers, and the
provenance sentence from §7 above in both its long and short forms. What §8 item 1 left open was decided
against trimming: `records/00-prior-direction-index.md` keeps its attributed quotations, so the submission
does not claim that no corpus text is in the repository; it says instead that the code and every committed
artefact were written from 08:29Z on 2026-11-07 and that the record cites the background reading with
attribution. (2) The three "pre-event" sentences in
`records/findings/17-hackathon-rules-recheck.md` (§5.3 item 3, §7 item 5, and the 15 lines item 14) are
corrected by an appended CORRECTION in that file, since it is append-only.

**Decision of record.** `records/F-decision-log.md` D8, "Team, corpus and provenance", dated 2026-11-07: a
two-person team (the operator and one teammate, names withheld from this file by the repo's own
public-safety rule and carried on the MLH team field), both registered and checked in; the code written by AI
agents the team directed, disclosed; the corpus not published, local, and not quoted beyond attribution.

**One figure in §9 is superseded too.** It records `tools/public_safety.py check` on the tracked tree as "77
hits in 11 files" at the moment of writing. The reading now recorded in `AGENTS.md` is **64 hits in 9
tracked files** at 2026-11-07T18:50Z, the change being the two files whose corrections had to redact a home
path and a process id to be committable (`findings/12-final-audit.md`, `DELIVERABLE.md`). The class mix and
the conclusion are unchanged: every hit is under `records/`, every one is quoted measurement evidence, and
the tree-wide check still exits non-zero, which is a separate problem from this audit and still the
operator's to decide.

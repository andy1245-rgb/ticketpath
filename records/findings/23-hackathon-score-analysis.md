# 22: What the judged score is made of, where this entry stands on each part, and what would raise it

**Written:** 2026-11-07T20:40Z to 21:20Z. **Event:** MLH Solana Hackathon, partnered, online,
2026-11-06 17:00Z to 2026-11-08 18:00Z. **Deadlines being defended:** initial submission Sunday
15:00Z (10:00 ET), hacking ends 16:45Z (11:45 ET).
**Tree read at:** commit `33d95b3` plus a dirty working tree (`tools/check_frontend_attach.py`
modified; `records/STATE-OF-PROJECT.md` and `records/findings/20-hosting-and-data-options.md`
untracked, neither mine).
**Field size, measured at 20:39Z:** 25 submissions. It was 7 at 10:59Z and 18 at 18:28Z.

**Numbering, so nobody hunts for a missing file.** `records/findings/22-scoring-and-where-to-raise-it.md`
is a separate run of this same brief that stopped at its own §1 after 77 lines and left a placeholder in
place of the criteria section. It is another worker's file and this pass did not touch it, delete it or
merge it. This file is the complete answer and took the next number.

This file answers three questions and makes no product decision. Every option in §5 is an option for
the operator, with its cost, its estimated effect and its risk, and nothing here was built.

**Labels.** **MEASURED** means a named page or a file this pass read says it, and the URL or the
`path:line` is in the entry. **MEASURED-ABSENT** means the named pages were read and the thing is not
on them: an absence is a measurement, not an inference. **ASSERTED** is my reasoning. Where a claim is
a prediction about how a judge will score, it also carries the programme's class **D** (a plausible
hypothesis with a mechanism and no evidence), because MLH publishes no scoring scale and a predicted
point value is exactly that.

The programme's A to E classes describe evidence about ticket markets. They do not describe a
hackathon's rules, and forcing them on would be false precision. `records/findings/02-rubric-and-scoring.md`
made and stated the same choice; this file follows it, and uses D only for the predictions.

**What this file adds to what is already recorded.** `records/findings/02-rubric-and-scoring.md` found
the criteria, `records/findings/17-hackathon-rules-recheck.md` re-verified them and corrected two
claims, and `records/STATE-OF-PROJECT.md` §C scored the entry at 18:25Z. That score predates commit
`33d95b3` (19:20Z), which put a native Rust Token-2022 transfer hook and a devnet publish script into
the tree. Two sections below therefore correct it: §3's Technology line, and §4's Design line, where
I reach a different number and say why.

---

## 1. The answer in one paragraph

There are two published rubrics, one of them expired, and neither is the thing that decides the main
prize. The live rules page gives four equally weighted criteria and explicitly excludes code quality,
pitch quality, idea quality and problem fit; a stale terms document gives 25/25/25/25 including
originality, and its own stated term ended on 2026-06-30. The Top 3 prize, which is the only one worth
the effort, is decided by one sentence about Solana rather than by any rubric: *"We're looking for a
working product that uses Solana for something it's good at ... not a chain bolted onto a web2 app."*
Against that sentence this entry scores **0 of 4** on the four things a judge looks for, and the reason
is not that the work is missing but that it has never been run against a public cluster: the program,
the mint configuration and the publish script all exist in the tree, and the authority that would fund
the run holds no SOL. Everything else in this file is secondary to that one fact, because one command
converts the largest single block of missing evidence into present evidence, and every other option
moves a smaller number.

---

## 2. The criteria, and which ones are actually documented

### 2.1 Regime A: four equal criteria. Live, and this is the one to score against.

**MEASURED**, `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md`,
fetched 2026-11-07T20:39:06Z, HTTP 200, 8,584 bytes, sha256 `cb282977…2c0f62`:

> "Teams will be judged on these four criteria for MLH digital events or MLH categories at an in person
> event. **Judges will weigh the criteria equally.** During judging, participants should try to describe
> what they did for each criterion in their project."

| Criterion | The published question, verbatim |
|---|---|
| **Technology** | "How technically impressive was the hack? Was the technical problem the team tackled difficult? Did it use a particularly clever technique or did it use many different components? Did the technology involved make you go 'Wow'?" |
| **Design** | "Did the team put thought into the user experience? How well designed is the interface? For a website, this might be about how beautiful the CSS or graphics are. For a hardware project, it might be more about how good the human-computer interaction is." |
| **Completion** | "Does the hack work? Did the team achieve everything they wanted?" |
| **Learning** | "Did the team stretch themselves? Did they try to learn something new? What kind of projects have they worked on before? ... that exploration should be rewarded." |

And the exclusions, verbatim in full:

> "It's important to note that these judging criteria do not include:
> * How good your code is. ... If your code isn't production ready, we're not going to mark you down.
> * How well you pitch. Hacking is about building and learning, not about selling.
> * How good the idea is. Again, hackathons aren't about coming up with innovative ideas.
> * How well the project solves a problem. You can build something totally useless ..."

And the escape hatch, which matters more than it looks: *"ultimately judges are free to make decisions
based on their gut feeling of which projects are the most impressive and most deserving."*

### 2.2 Regime B: 25/25/25/25 including originality. Published, and expired.

**MEASURED**, `https://raw.githubusercontent.com/MLH/mlh-policies/main/contest-terms.md`, fetched
20:39:06Z, HTTP 200, 15,148 bytes, last line "This document was last updated on: August 14th, 2025":

> "**Scoring of APPLICATIONS:** ... The Applications will be judged according to the following criteria:
> 0. originality/creativity (25%); 0. technical complexity (25%); 0. adherence to Theme (25%) and
> 0. practical implementation (25%)."

**MEASURED**, same document, first substantive line: *"The Events season shall commence on July 1, 2025,
and shall end on June 30, 2026."* This event is in the 2027 season. **MEASURED**, the registration
form's checkbox points at `https://hackp.ac/ContestTerms`, which redirects to `https://mlh.link/ContestTerms`,
which serves a meta refresh to the MLH homepage, not to a terms document. **CONFLICT**, named and not
resolved: the rules page is current and says four equal criteria; the terms page is expired by its own
text and reachable only through a dead link.

**What follows, and it is small.** The two regimes agree on Technology against technical complexity and
on Completion against practical implementation. They disagree on originality, which only Regime B scores,
and on Design, which only Regime A scores. So Design is upside with no downside, and originality should
not be planned for because one live document explicitly refuses to judge it.

### 2.3 The five prize tracks: no rubric exists, for any of them.

**MEASURED-ABSENT.** Each track carries one description and an "Ideas to Get Started" list. There is no
scoring language, no weighting and no judging-panel description on the event page, on the canonical
page, or on the two challenge-category pages fetched. The one-liners, verbatim from
`https://events.mlh.com/events/15200-solana-hackathon`, fetched 20:38:59Z:

| Track | Prize | The complete published criterion |
|---|---|---|
| **Top 3 Overall** | $1,000 microgrant per team, three teams | "The three strongest projects at the event. Every eligible submission is automatically entered. We're looking for a working product that uses Solana for something it's good at (speed, low fees, composability, on-chain ownership), not a chain bolted onto a web2 app." |
| **AI Track** | $100 gift card per member | "Build something where AI and Solana each do real work. The best projects use AI to make on-chain activity smarter, safer or easier, or use Solana to give AI systems something they can't get elsewhere, like payments, ownership, verifiability or coordination." |
| **DeFi Track** | $100 gift card per member | "Build financial applications and protocols that take advantage of Solana's speed, low fees and composability. We want products that move value in ways that are faster, cheaper, more open or more accessible than what exists today." |
| **Gaming Track** | $100 gift card per member | "Build games, or the tools behind them, where Solana makes the experience better. Fun comes first." |
| **Best Beginner** | $100 gift card per member | "For teams building on Solana for the first time or attending their first-ever hackathon (or both). ... Teams made up of >50% first-time hackers are eligible." |

Note the widening in Best Beginner's long form: **"building on Solana for the first time"** is an
alternative to being a first-time hacker, not an addition. Whether that applies here is the operator's
question and not mine (§7, Q5).

**MEASURED**, all five category pages: *"One submission can enter every category it qualifies for."*
Entering is free and is not a scarce resource.

### 2.4 The one sentence that decides the main prize, and the four things it is applied to

The Top 3 criterion names materials, not depth. It does not ask for a large amount of chain code; it
asks that the chain work be load-bearing. **ASSERTED**: a judge holding that sentence for sixty seconds
looks for four things, in this order: (a) an account that belongs to this project, (b) a transaction
signature with a block time, (c) a program in that transaction that the team did not write, doing
something the product depends on, and (d) the product reading that state back rather than printing a
constant. This is `02-rubric-and-scoring.md` §F1, and §4.2 below applies it.

The nearest published artefact list, and a caveat about it: **MEASURED**,
`https://hackdays-guide.mlh.com/partner-programs/solana.md`, page header "Last reviewed: August 2026":

> "## Judging Evidence — Confirm that the winning project actually uses Solana. Ask the team to identify
> the integration in its README and show the relevant code, configuration, transaction, deployed
> program, or other appropriate evidence during the demonstration."

That page is written for MLH **Hack Days**, a different programme, and its stated prize is a hardware
wallet that this event does not offer. It is the sponsor's own statement of what "actually uses Solana"
means and is the best available proxy. It is not a rule of this event, and nothing here should be
presented as if it were.

### 2.5 How the judging actually runs, which changes what "score" means

**MEASURED**, `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md`,
fetched 20:39:11Z:

> "Time taken by a Judge per project (MLH recommendation: 4 mins per project. 2 minutes for presentation
> + demo, 1 minute for questions from judges and score compilations, and 1 minute for judge travel)"
> "(MLH recommendation: 3 rounds per project)"
> "at MLH, we love to use Stack Ranking because it normalizes scores across judges ... Ask each judge to
> view their projects and report back their top 3 best/favorite projects. Assign the top three following
> points: 3 points (First Place), 2 points (Second Place), 1 point (Third Place)."
> "Their video should be a demo of their hack, not a presentation."

**ASSERTED, and it is the most useful operational consequence in this file**: stack ranking is relative
and it is decided in about four minutes per project, so the question is not "is this good" but "is this
in a judge's top three of the roughly eight projects that judge sees". A project that is better than its
neighbours but takes ten minutes to explain loses to a project that shows one thing working in forty
seconds. That is a structural risk this build carries, and it does not move with correctness. It moves
with first-60-seconds legibility, which is the Design axis.

**MEASURED-ABSENT**: no page fetched states how many submissions each judge sees, whether the five
tracks are judged by the same people, or whether every submission is seen three times. The 4-minute,
3-round, top-3 mechanism is MLH's recommendation to organisers, not a published property of this event.

---

## 3. Where this entry stands, criterion by criterion

Scores are out of 25 and are **ASSERTED judgements, class D**, for one reason: MLH publishes no scale,
so a number is an ordering device and not a forecast. What is not a judgement is the evidence column;
every one of those is MEASURED and cited. The total, 54, should be read as "the middle of the field,
with the largest part of the gap concentrated in one place".

### 3.1 Technology: 12 / 25

**What exists, measured.**

| Evidence | Where |
|---|---|
| A native Rust Token-2022 transfer hook, 438 lines, no Anchor, four `#[test]` unit tests asserting the cap boundary exactly (`1_250_000_000` admitted, `1_250_000_001` refused) | `programs/cap_hook/src/lib.rs:49-62`, `:89`, `:157`, `:400-438`; `programs/cap_hook/Cargo.toml:13-18` |
| Error codes carrying the design's own numbering: `AmountNotOne = 6008`, `TransferNotStaged = 6009`, `CapExceeded = 6010` | `programs/cap_hook/src/lib.rs:49-62` |
| A 1,427-line devnet publish script, nine idempotent steps, `--dry-run` and `--local`, that refuses below a funded authority | `tools/devnet_publish.py:1-42`, `:35` |
| An out-of-process signer so the parent process never holds a key byte | `tools/solana_sign.py`, 113 lines; `tools/devnet_publish.py:30-33` |
| Ed25519 implemented from RFC 8032 in pure Python, 153 lines, plus base58, 65 lines | `ticketpath/core/ed25519.py`, `ticketpath/core/base58.py` |
| A pricing engine that carries its own identifiability limits: log-space band with a DerSimonian-Laird `τ²` that is only computed at ≥9 events and otherwise declared, with a floor | `ticketpath/core/value_band.py:1-491` |
| Integer lamport and basis-point arithmetic, no floats, in the markup path | `ticketpath/core/markup.py`, 95 lines |
| 7,705 lines of product code, 12,008 lines of tests | tracked line counts, this pass |

**What a judge sees in four minutes.** A repo whose first screen says "Designed but not deployed", and
a console that prints `[SIMULATED]` next to the state machine. The most interesting thing in the build,
which is that the engine refuses to answer three of its four questions and names the missing observation
for each, takes ninety seconds of speech to land and there are twenty.

**Why 12 and not 11.** `records/STATE-OF-PROJECT.md` §C1 scored Technology at 11 from a measurement
taken between 18:25Z and 18:40Z. Commit `33d95b3` landed at 19:20Z and put the Rust program and the
publish script into the tree, so the earlier number was measured against a tree that did not contain
them. **A program that exists and passes its own boundary test is Technology evidence a judge can read**
even though it has never run on devnet. One point, not more, because the criterion's own words ask
whether the technology "made you go Wow", and the honest answer to an undeployed program is that it is
impressive on inspection and not yet real.

### 3.2 Design: 12 / 25

**What exists, measured.**

| Evidence | Where |
|---|---|
| A server-rendered console, 1,489 lines of Python, one inline stylesheet, no JavaScript at all | `ticketpath/console/page.py:26-60` (style), `:63-82` (document), `page.py`, `blocks.py`, `units.py` |
| Served at `/` and `/index.html`, dispatched from the route table | `ticketpath/server.py:46`, `:235-249`, `:78` |
| No viewport meta tag: the document head carries charset only | `ticketpath/console/page.py:66`, `:430` |
| No chart, no canvas, no SVG anywhere in the repository | grep over `ticketpath/`: no `<svg`, no `<canvas`, no script |
| The price path renders as text rows in paragraphs, not as a plot | `ticketpath/console/blocks.py:350-400`, `:358` |
| Eight canonical page states, each a URL | `docs/RUN.md:27-36` |
| No HTML, CSS, JS or image file is tracked; the only `.html` on disk is untracked and git-ignored | `docs/morning.html`, `.gitignore:20` |
| Screenshot machinery exists, and captures are deliberately written outside the repository | `tools/shot.py`, 146 lines; `docs/SHOTS.md:9-10`, `:46-47` |

**What a judge sees.** One page. It opens with a banner saying every number is synthetic and no program
is deployed, then a nine-badge legend, then prose, and the headline price is below the fold. It was
measured at 1,178 words by the 18:25Z pass (`records/STATE-OF-PROJECT.md` §B1, that pass's measurement,
not mine). On a phone it is unusable, because there is no viewport meta and no narrow stylesheet.
Its virtues are real and they are the kind a design-literate judge notices: one consistent typographic
system, a badge vocabulary that never contradicts itself, every state addressable, and no decoration
that is not carrying information.

**Why 12 and not 14, which is a disagreement I am recording rather than smoothing.** The 18:25Z pass
credited "a consistent, quiet, product-shaped UI with a per-ticket custody trail, an organizer roll-up
and a badge system" and 43 checks tying it to the API. That surface is the Next.js frontend, and it is
**not in this repository** (`README.md:89-92` says so plainly). Digital rule 6 says *"You can not submit
a project that includes prior work"* and rule 9 permits a prior idea *"as long as they do not re-use code
or other project materials"*. A judge scoring Design scores the artefact we submit. Crediting a copy of
the platform's own app as our design is the one thing in this analysis that can cost the entry rather
than gain points, so the Design number should be earned by the console, which is ours. On that basis 12
is the honest figure, and the gap between 12 and 14 is the size of the decision in §7 Q2.

### 3.3 Completion: 12 / 25

**What exists, measured.**

| Evidence | Where |
|---|---|
| Runs on the standard library with no build step, on one documented command | `README.md:23`, `docs/RUN.md:5-12` |
| Ten routes in the route table, plus the console | `ticketpath/server.py:117-134` |
| Nine CLI verbs, so the whole thing is drivable headless | `tools/tp.py:852-877` |
| 36 test modules, 574 test definitions, 12,008 lines, plus a 113-assertion console suite and a 43-check attach suite | `tests/`, `tools/console-check.py`, `tools/check_frontend_attach.py` |
| A deterministic fixture generator whose `--check` mode proves two runs produce identical bytes | `tools/build_fixture_store.py`, `README.md:81-87` |
| A publish pipeline that was rehearsed end to end against a local validator, twice, idempotently | `records/findings/21-onchain-hook-in-tree-and-publish.md:5-7`, `:118-130` |
| Incompleteness declared in prose rather than hidden: two named unimplemented rules, and a specification that states which of its sections are stubs | `programs/cap_hook/README.md:92`, `:108`; `records/DELIVERABLE.md` |
| No `TODO`, `FIXME` or `XXX` anywhere in product, tools, program or docs | grep, this pass |

**What a judge sees.** "Does the hack work?" A judge who runs it gets a page and ten endpoints and a
green suite, so yes. "Did the team achieve everything they wanted?" Here the honest answer is a design
choice the project made on purpose: it wanted a defensible engine and it has one, and it also wanted
four outputs and ships one plus three reasoned refusals. That is completable, and it is not the same as
complete. What is missing is not a feature: there is **no URL, no deploy, and no chain artefact**
(`ticketpath/adapters/rpc_adapter.py:3`, `:82-96`: the adapter never opens a socket on any flag and
always reports `programDeployed: false`).

**Why this agrees with the earlier pass at 12.** Two passes measuring different commits reached the
same number for different reasons: theirs, that nothing is deployed and the frontend work lives in a
copy; mine, that the publish path now exists but has never touched a public cluster. Both point at the
same missing hour.

### 3.4 Learning: 18 / 25

**What exists, measured.** 32 tracked investigation reports and one untracked, append-only, each with
primary sources and an evidence class. Six standing records plus a decision log with rejected
approaches and open questions. A rules recheck that corrected its own earlier finding in public when it
found the contradicting document (`records/findings/17-hackathon-rules-recheck.md` §5, rows 1 to 3). A
cap argument that was withdrawn when a check contradicted the product's own claim
(`records/findings/11-cap-capture-check.md`, `records/F-decision-log.md` D7). Ed25519 and base58 written
from the specifications rather than pulled from a library. A Solana toolchain learned inside the window,
and a Rust program written in it. The AI disclosure is explicit and unhedged at `README.md:217-223`.

**Why 18 and why not higher.** This is the criterion MLH invites most openly ("did they try to learn
something new ... that exploration should be rewarded"), and it is the strongest axis by a distance. It
stops at 18 rather than 20 because the learning is dense in documents and thin on screen: the video has
to carry one sentence of it, and a judge scoring Learning from a four-minute exposure is reading the
README's thesis, not the 32 reports.

### 3.5 The Top 3 materials test, scored separately because it is not one of the four: 0 of 4

**MEASURED at HEAD.** Applying §2.4's four tests:

| Test | What exists | Verdict |
|---|---|---|
| an account that belongs to this project | `/health` reports `programId: null`, `programDeployed: false`; every fixture mint is a `SYN…` placeholder that announces itself as one (`tools/build_fixture_store.py:133`, `fixtures/README.md:9-13`) | **absent** |
| a transaction signature with a block time | no mint, program id or signature exists in the product tree. Base58 signatures and a program id do appear in one record and in two test constants (`records/findings/18-onchain-install-and-test.md:224-302`, `tests/test_base58.py:29`, `tests/test_devnet_publish.py:30`), and that record states plainly that they are **local-cluster** values: "These signatures are local-cluster signatures. They do not exist on devnet" (`:192`). Nothing on any public cluster has this project's name on it. | **absent** |
| a program the team did not write, doing work the product depends on | Token-2022 and the transfer-hook interface are pinned in the program's manifest (`programs/cap_hook/Cargo.toml:13-18`) and proven to exist on devnet by a hand query in a record, but no product code path invokes them | **absent** |
| the product reading that state back | `rpc_adapter.py` opens no socket; the console's `[DEVNET]` slot requires `records/devnet-artefacts.json`, which does not exist (`ticketpath/console/page.py:368-425`) | **absent** |

**0 of 4.** The tree is honest about this in at least four places, which is worth something and is not
the test. What has changed since the 18:25Z pass is that the failure is now one funding step rather
than one build: `records/findings/21-…:6` states *"Devnet is still unfunded, so nothing here is on
devnet"*, and `:67` states the script refuses below 2 SOL.

### 3.6 Totals

| Axis | Score | Confidence in the number |
|---|---|---|
| Technology | 12 / 25 | low, because it turns on how much of the Rust program a judge reads |
| Design | 12 / 25 | low, and it moves 2 points on the frontend decision (§7 Q2) |
| Completion | 12 / 25 | medium, and it is the one that one command moves most |
| Learning | 18 / 25 | medium, this is the axis least sensitive to presentation |
| **Total** | **54 / 100** | band 46 to 62, and the spread is almost all in Technology and Completion |
| Top 3 materials test | **0 of 4** | high, this is a checklist not a judgement |

The field is 25 with 3 placing. **ASSERTED**: given a stack-ranked top-3-of-eight, 54 lands in the
middle and does not place on its own; 0 of 4 on the materials test is the reason, and it is a
disqualifier for the main prize in everything but name.

---

## 4. What past winners actually did, with sources

Three separate records exist, and the honest summary is that the evidence is thinner than anyone would
like: **no Devpost submission says why it won.** The prize line is a string. The only sponsor that
published a ranking of its own winners is Midnight, and it did so in Japanese translation.

### 4.1 The sample, and its denominator

**MEASURED**, from the unpublished Devpost search JSON (`https://devpost.com/software/search?query=solana`,
6 results a page, `winner: true|false` per record), as recorded in the research corpus outside this
repository and re-confirmed live this pass on 5 pages: 397 pages walked, **285 of 397 failed on rate
limiting**, 672 unique projects seen and 87 marked winner, out of a reported 2,380 matches. Of those 87,
**38 carried a Solana prize**. The corpus's own caveat is that roughly 200 Solana prize winners exist
per season and it recovered 38, so this is a sample and not a census.

**MEASURED**, same source, the mechanism classification of those 38:

| Mechanism | Count | Share |
|---|---|---|
| A custom on-chain program | 8 (one of them inferred by the author) | 21% |
| A memo instruction only | 10 | 26% |
| A Metaplex or SPL mint | 7 | 18% |
| Composing third-party programs | 3 | 8% |
| Read-only, simulated or absent | 7 | 18% |

The airtight figure for a deployed custom program is **7 of 38, 18%**, because one row is flagged as an
inference. **So four out of five Solana prize winners did not deploy a program of their own.** A
custom program is a differentiator and not a requirement, which is the single most useful thing in this
table for a team without a Rust toolchain. This team now has one.

### 4.2 Four winners, read directly, and what a judge could check unaided

All four are the project's own Devpost text, verified live this pass.

| Project | Prize, event | What it actually did on Solana, in its own words |
|---|---|---|
| **Weenie Beanie** | MLH Prize: Best Use of Solana, SwampHacks XII, Oct 2026 | *"two custom Solana programs written in Rust and Anchor 1.2.1 ... `.reputation` mints the Token-2022 NonTransferable Soulbound credential"*, escrowed on devnet |
| **solGPU** | [MLH] Best Use of Solana, Knight Hacks IX, Oct 2026 | *"Phantom signs a memo transaction carrying that hash. The receipt card shows the signature and an Explorer link, and 'Verify receipt' re-checks five things against the chain."* Mechanism: *"no token, no transfer and no custom program"* |
| **LOKA Pay** | [MLH] Best Use of Solana, Hacklanta 26, Oct 2026 | *"Each allowance has 256 serials tracked in an on-chain bitmap"*; *"the chain refuses it with SerialUsed"*; four public devnet signatures; a *"seven-stop judge guide"* at a public URL |
| **school of thought** | [MLH] Best Use of Solana, OxHack 2026, Oct 2026 | A Merkle block per round anchored as a memo; *"refused repeats and self-likes, with the refusal on chain"*; no custom program claimed |

**What they have in common is not mechanism depth.** **ASSERTED** from that table: each has one thin,
checkable on-chain artefact; each has a working end-to-end user story; each has a live URL; and two of
the four engineered a path a judge can operate unaided (a verify button, a public judge page). Two of
four deployed a custom program, two did not. That is the same split as the 38-sample, arrived at
independently.

### 4.3 The directly comparable precedent, and it is the sharpest fact in this file

**MEASURED**, `https://devpost.com/software/backfill-1kpq2o`, `Winner · MLH: Best Use of Solana ·
Gator Quant Hacks`: a genuine systematic-trading project that *"waits 20 trading sessions after the
first eligible close, then holds for five sessions"*, hedges with SPY, and reports *"all 11 strategies
we tested (including the 9 that lost money)"*. Its entire Solana integration is one memo:

> "Before forward testing, we froze our rules, data and results and wrote their SHA-256 fingerprint to
> Solana as a memo. Anyone can re-check it from the repo or with the Verify now button; any later edit
> fails verification."

**ASSERTED, class D**: a quantitative-analysis project of exactly this shape has taken an MLH Solana
prize, and it won on a frozen-rule attestation rather than on an on-chain financial primitive. That is
the memo tier this entry has already designed (`ticketpath/adapters/chain_client.py` builds the quote
memo and its SHA-256 and never a signature), and the publish script already writes it
(`tools/devnet_publish.py`, showing the console's own quote as a memo). The precedent says the cheapest
honest on-chain artefact is not a compromise for a project like this one. It is the pattern that won.

**MEASURED-ABSENT**: no published judging commentary about how a pricing or quantitative-finance
project scored exists, beyond that one winner's own write-up. Anything stronger than the above would be
invention.

### 4.4 The one sponsor that ranked its own winners

**MEASURED (translated)**, `https://note.com/midnight_jpn/n/nbc5d338ae2be`, the publisher's own
Japanese translation of the Midnight blog post of 2026-08-20, which states in its first line that it is
a translation. The English original is blocked from this host by a Vercel checkpoint, so the wording is
the publisher's, through a translation:

> "What the winners had in common": (1) the primitive was used because the design required it, and 8 of
> the entries evaluated used no private data at all; (2) **a completed layer**: contract, tests and
> interface, where half-finished frontends were common in the field; (3) **deployment**: Hermes and
> Moonray reached the public test network, everything else stayed on a local node; (4) **a use case
> someone else can explain in one sentence.**

Two further sentences matter. On the bar: *"testing on a local node is entirely normal and expected in a
48-hour weekend hackathon"*. On what deployment credit actually required: Hermes *"deployed 4 contracts
to Preprod and published addresses, transaction hashes and block numbers in the repo so anyone could
verify"*.

**ASSERTED**: that ordering, completed layer then deployment then explainable use case, is the same
ordering §5 below arrives at from this repo's own gaps, which is a mild corroboration rather than
independent evidence.

### 4.5 A different competition, named so nobody conflates them

**MEASURED**, `https://colosseum.com/hackathon`: the judging factors are "Founder + Market Fit,
Insight, Product + Execution, Potential Market Size, Founder Communication, Viability, Traction", and
the page states *"A few things that we are not looking for: Using a particular language or framework ...
Specific design patterns, best practices, or code-quality checks."* That is a venture-shaped rubric and
it is **not** this event's. It is recorded only because "what won a Solana hackathon" often means
Colosseum, and the answer there would lead this entry to optimise the wrong things.

---

## 5. Ranked ways to raise each part, with effort, impact and risk

Every row is an option. Nothing here was built. Hours are my estimates for one competent operator
working with the tools already in the tree. Impact is a **class D** estimate of points on that
criterion, and the ranking within each criterion is by impact per hour.

### 5.0 The precondition, which is not a score item

| # | Option | Hours | Why |
|---|---|---|---|
| **P1** | Record and publish the ≤2:00 demo, hackathon named in the first spoken sentence, product in frame one, left public | 2.5 | **MEASURED**, digital rules 1 to 3 and rule 11: without it there is no eligible entry, and nothing else in this file can score. `records/SUBMISSION-PACK.md` §1.2 already holds a timed six-beat script. |
| **P2** | Confirm registration **and check-in** on the submission platform, then open the submit form once to see the fields | 0.2 | **MEASURED**, digital rule 4 and the three-step strip on the event page. Fatal if incomplete and it is discovered at 09:55. |
| **P3** | Fill both required GenAI fields truthfully, naming the tools | 0.25 | **MEASURED**, the form's two GenAI fields are required; the stated penalty for not disclosing is disqualification. `records/SUBMISSION-PACK.md` §2.7 holds draft wording. |

### 5.1 Technology, from 12

| # | Option | Hours | Impact (D) | Risk | What it depends on |
|---|---|---|---|---|---|
| **T1** | **Fund the publish authority and run the devnet publish.** The script already does balance, build, deploy, a 0-decimal Token-2022 mint with a transfer hook and metadata pointer, the record PDAs, a ticket, the console's own quote as a memo with its hash, and the cap boundary as a pair with both signatures. It is idempotent and refuses when unfunded. | 0.75 plus the operator's faucet step | **+3 to +5**, the largest single Technology move available | Low on the chain: devnet only, no mainnet path in the script, and `--dry-run` touches nothing. Medium on the machine: it builds and deploys, so run it bound and read the log. | **The faucet is an operator action, not a machine one.** **MEASURED**, `https://faucet.solana.com/` states *"AI agents should not use this faucet"*. Also: the mint, the program id and the signatures must be real or absent, never simulated and labelled as real (`02-rubric-and-scoring.md` §"What can be simulated honestly"). |
| **T2** | Put the **refusal** in the video and the README as a signature, not a claim: the transfer one lamport above the cap refused with 6010, with its explorer link beside the one that was accepted | 0.25 | +1 to +2 | None. Every verified winner that scored on technology showed an error path; three of the four in §4.2 did. | T1, or it is a local-cluster signature and must say so (`records/findings/18-…:192` already draws that line). |
| **T3** | Make the **identifiability refusal** one screen: three reasons the engine declines, each with the missing observation beside it, above the fold | 0.5 | +1, and +1 Design | Low. It is the most defensible thing in the build and currently the least legible. | Nothing. |
| **T4** | Do **not** do: more program surface (destination checks, a mutable cap, escrow). `programs/cap_hook/README.md:92` and `:108` name two unimplemented rules, and closing them is a day, not an hour, and gains nothing on any published criterion. | n/a | 0 | Waste, which is the real risk at 19 hours out. | n/a |

### 5.2 Design, from 12

| # | Option | Hours | Impact (D) | Risk | Note |
|---|---|---|---|---|---|
| **D1** | **Headline price above the fold**, badge first then the number then the argument. The page currently opens with a compliance banner and a nine-badge legend, and the number is below both | 1.0 | +2 to +3 | Low, and it changes what a judge's first impression is | Cheapest Design point in the build, per `records/STATE-OF-PROJECT.md` §C3, which reached the same conclusion from a different measurement |
| **D2** | **Cut the console prose** from 1,178 words to about 700, keep every badge, drop the audit voice | 1.5 | +1 to +2, and +1 Completion | Low | 4 minutes per judge is the constraint (`judging-plan.md`), so every paragraph is a paragraph that can be misread |
| **D3** | **Viewport meta and a narrow stylesheet**, then re-measure at 1280 and 390 wide | 1.5 | +1 to +2 | Low | **MEASURED**: `ticketpath/console/page.py:66` and `:430` carry charset only, so the page is unusable on a phone today, and a judge may open the link on one |
| **D4** | **Commit three screenshots** into `docs/` and reference them from the README | 0.5, since captures already exist | +1 to +2 Design, +1 Completion | **Two of the operator's own rules collide here and I am not resolving it.** `AGENTS.md` R5 says *"The repo is code only. No keys, no scraped data, no datasets, no binaries"*, and a PNG is a binary. MLH scores Design at a quarter of the total and a screenshot is the cheapest evidence of it. The collision is named, not decided (§7 Q6). | The captures are produced by `tools/shot.py` and deliberately written outside the repo today (`docs/SHOTS.md:46-47`) |
| **D5** | **A URL a judge can open.** A tunnel to the console, or a static capture of its three states | 0.75 | +2 Completion, +1 Design | Medium and it is real: a tunnel puts the fixture API on the public internet while it runs, a tunnel that is down during judging is a broken link, and a static capture invites the question of what is live. `records/findings/20-hosting-and-data-options.md` is an untracked options note on exactly this. | The operator's call, because it is hosting |
| **D6** | Do **not** do: port the Next.js frontend into this repo, or present it as the design | n/a | 0, and negative if it reads as prior work | **High.** Digital rule 6: *"You can not submit a project that includes prior work."* | §3.2, §7 Q2 |

### 5.3 Completion, from 12

| # | Option | Hours | Impact (D) | Risk | Note |
|---|---|---|---|---|---|
| **C1** | **One devnet transaction, read back.** This is T1's other half and should not be counted twice: it is the same command that fills the console's `[DEVNET]` slot, which already refuses an artefact whose cluster is not devnet and whose memo is not the settled grammar (`tools/devnet_publish.py`, loader changes in `33d95b3`) | (in T1) | +2 to +3 | Low | **This is the only change that moves 0 of 4 on the materials test to 2 or 3 of 4**, and the precedent in §4.3 is that this is enough to win a Solana prize |
| **C2** | **Correct the stale counts.** `README.md:185` says 29 tracked findings, the tree has 32. `README.md:204` says 34 test modules, there are 36. `README.md:220` says six of nineteen commits carry a tool trailer, measured 9 of 22. `records/DELIVERABLE.md:1893` states 352 tests as a live measurement. `records/SUBMISSION-PACK.md` §2.5 says there are no screenshots, and `docs/SHOTS.md` exists | 0.75 | +1 to +2, and it is the cheapest credibility in the build | None. All are edits | A judge who catches one contradiction discounts the rest, and these are the only things in the documents a judge can falsify by looking |
| **C3** | **Sweep the public-safety hits.** `python3 tools/public_safety.py check --tracked` exits 1 with **64 hits in 9 tracked files**, all under `records/`: 48 live-service, 14 home-path, 2 fleet-repo | 1.5 | 0 points, removes an incident | **Real, and it is a records problem, not a code problem.** The hits are quoted measurements: a process id in a state table, a path inside a command's output. Redacting them edits the evidence; adding a per-file exception is a decision about what the record may carry. `AGENTS.md` requires both to be the operator's call, and history is never rewritten without his explicit yes | Not a score item. It is the difference between a repo that keeps its own published rule and one that does not, and `docs/PUBLIC-SAFETY.md` is the account |
| **C4** | A one-command run path (`make demo`) | 0.25 | 0 to +1 | None | `docs/RUN.md:3-12` is already two commands, so the marginal gain is small |

### 5.4 Learning, from 18

| # | Option | Hours | Impact (D) | Note |
|---|---|---|---|---|
| **L1** | **Nothing.** This is the strongest axis and the least marginal return available | 0 | 0 | The 32 reports are already more than any judge will read. Adding research now is the classic misallocation |
| **L2** | One short README paragraph on what was learned, naming three specifics: the parameter that is not identified at this sample size, the cap that truncates rather than constrains, and the refusal taxonomy | 0.25 | +1 | It also gives the video's one Learning sentence something true to say |

### 5.5 The order I would put them in, if the question is only "most score per hour"

1. **P1 the video** (2.5 h). It gates everything.
2. **T1 plus C1, the devnet publish** (0.75 h plus the faucet). Largest single move, and it is the
   materials test.
3. **D1 headline above the fold** (1.0 h). Cheapest Design point, and Design is a quarter of the total
   under the live rubric.
4. **C2 stale counts** (0.75 h). Cheap, and it removes the only falsifiable defects.
5. **D5 a URL** (0.75 h), if he wants one, which makes every claim checkable in one click.
6. **T2 refusal in the video**, folded into P1.
7. **D2 prose cut** (1.5 h), **D3 viewport** (1.5 h), **T3 refusal screen** (0.5 h), **L2** (0.25 h).
8. **C3 public-safety sweep** (1.5 h), and it is eighth only because it scores nothing. It is first if
   the question is "what would embarrass the entry".
9. **P3, P2** whenever, because they are minutes and they are gates.

**What is deliberately not on that list**: a bigger program, more research, porting the frontend, a
second video, market sizing, originality, or anything that optimises a stale weighting.

---

## 6. Risks that outrank the score

Each of these can cost more than any option above can gain. All measured, all cited.

1. **The frontend copy as prior work.** Digital rule 6 and hackathon rules 9 and 10. The exposure is a
   wording problem, not a code problem: one sentence in the submission and one in the video saying the
   surrounding product UI is an existing platform and the weekend's work is the pricing layer inside it.
   `records/findings/17-hackathon-rules-recheck.md` §6 R1 rates it the single largest exposure and that
   rating still holds.
2. **Ownership.** **MEASURED**, `contest-terms.md`: *"An Eligible Participant (or team) must be the sole
   owner of the Application submitted."* Against a company-shaped project, and against rules 12 and 13
   which require the repo to stay public forever. If the work is also company work, those cannot both be
   satisfied and no amount of build time fixes it. Only the operator can answer it (§7 Q1).
3. **The public-safety tree failure.** 64 hits in 9 tracked files. The commit gate and the push gate pass
   because they read only what they are given; the tree is what a judge who opens `records/` sees.
4. **`contest-terms.md`'s automation clause**, *"Applications that have been generated by a script,
   macro, bot, or any other automated means will be deemed void"*, contradicts the same-day AI
   permission in the rules. Disclose and let the record show both. In context the clause sits beside
   "mechanically reproduced, copied, illegible, incomplete, or inaccurate", which reads as an
   anti-spam provision, and the AI section is the specific rule.
5. **"Is a solo hacker making a really advanced project in a single weekend?"** is item two on MLH's own
   published cheating-check list. The mitigation is an explainable video and README, not a smaller
   project. The git history already answers the two checks that matter: 22 commits, first at
   2026-11-07T08:29:57Z, spanning 10 h 50 min, none backdated, none before the window opened.
6. **Field growth.** 7 submissions at 10:59Z, 18 at 18:28Z, 25 at 20:39Z. Three place. Any figure in this
   file about the odds is stale within hours and should be re-read before the video is locked.

---

## 7. Decisions this file does not make

Each one changes the deliverable or carries a rule collision, so each is his.

1. **Is the pricing work also company work?** If yes, "sole owner of the Application" and "the repo stays
   public forever" collide and the entry needs reframing before 15:00Z.
2. **Does the design credit go to the console alone, or does the submission describe the existing
   platform frontend?** The first is worth 12 on Design and no risk. The second may be worth 14 and is
   the largest disqualification exposure in the entry. I scored the first; the second is his call.
3. **Fund the devnet publish, or ship without it?** One faucet step and about 45 minutes in exchange for
   the largest single block of missing evidence. Without it the honest state stays "nothing deployed"
   and the entry is complete and placeable on Learning and Completion only.
4. **Publish a URL?** A tunnel, a static capture, or neither.
5. **Enter Best Beginner?** The long form reads "building on Solana for the first time or attending their
   first-ever hackathon (or both)" with a >50% test. Free to enter if it is honest, and it is his
   history, not mine.
6. **Screenshots in the repo?** `AGENTS.md` R5 forbids binaries in the repo; Design is a quarter of the
   live rubric and a screenshot is the cheapest evidence of it. Both rules are his and they point
   opposite ways.
7. **The stale claims and the public-safety sweep: forward-only, and is that permission?** Redacting a
   quoted measurement edits the evidence; an exception line in `.public-denylist` is a decision about what
   the record may carry. Neither is mine.
8. **Ownership of the research corpus's provenance.** Whether the outside-the-repo corpus may be quoted
   in the submission text beyond the attributed citations already committed is still open, and
   `records/findings/19-corpus-citations.md` found no credential-shaped material in it, which is the
   absence of a hazard and not proof of clean provenance.

---

## 8. What is not documented, so that nobody invents it

- **No numeric weight is published for Technology, Design, Completion or Learning.** The word is
  "equally" and there is no number. MEASURED-ABSENT on seven pages.
- **No rubric exists for any of the five prize tracks** beyond the one-line description. MEASURED-ABSENT.
- **No page says how many submissions a judge sees, whether the tracks share judges, or whether every
  entry gets three viewings.** The 4-minute, 3-round, top-3 mechanism is MLH's recommendation to
  organisers. MEASURED-ABSENT for this event's own judging plan.
- **No winner record states why it won.** The prize line is a string. The only ranked reasoning is
  Midnight's, in translation. MEASURED-ABSENT.
- **No page states whether the 15:00Z initial submission can be edited afterwards.** The platform has an
  edit path by design and a 18:00Z close, and rule 11 caps hacking at 16:45Z. Treat 15:00Z as the freeze.
- **No deep link, no hosted demo, no public gallery.** `galleryPath: null`, and the submissions path
  returns 404. A judge sees the submitted fields and the video, and nothing else.

---

## 9. Sources

Fetched 2026-11-07 between 20:38:59Z and 20:39:56Z unless a row says otherwise.

| # | URL | What it established |
|---|---|---|
| 1 | `https://www.mlh.com/events/solana-hackathon` | five tracks and exact prize strings, counter 25, deadline "Nov 8, 1:00 PM EST", `galleryPath: null` |
| 2 | `https://events.mlh.com/events/15200-solana-hackathon` | three Sunday schedule rows, calendar window `20261106T170000Z/20261108T180000Z`, the five long-form track descriptions, no rubric |
| 3 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/standard-hackathon-rules.md` | the four criteria "equally", the exclusion list, AI Tools 1 to 2, digital rules 1 to 6, hackathon rules 6 to 13 |
| 4 | `https://raw.githubusercontent.com/MLH/mlh-policies/main/contest-terms.md` | the 25/25/25/25 block, and its own term "July 1, 2025 ... June 30, 2026" |
| 5 | `https://hackdays-guide.mlh.com/partner-programs/solana.md` | "Judging Evidence", four artefacts, "Last reviewed: August 2026" |
| 6 | `https://guide.mlh.com/general-information/judging-and-submissions/judging-plan.md` | 4 minutes per project, 3 rounds recommended, stack ranking 3/2/1, "a demo of their hack, not a presentation" |
| 7 | `https://hackdays-guide.mlh.com/run-your-event/project-submissions.md` | the "Accept late submissions" switch, so editing after the deadline is a platform capability |
| 8 | `https://www.mlh.com/events/solana-hackathon/submissions` | 404, no gallery |
| 9 | `https://www.mlh.com/events/solana-hackathon/challenges/01a1a6ef…` and `…/01a1a70d…` | "One submission can enter every category it qualifies for"; one line per track, no rubric |
| 10 | `https://devpost.com/software/weenie-beanie` | two Anchor programs, Token-2022 soulbound, SwampHacks XII |
| 11 | `https://devpost.com/software/solgpu` | memo only, Phantom signature, five-check verify, Knight Hacks IX |
| 12 | `https://devpost.com/software/loka-pay` | Anchor, on-chain bitmap, `SerialUsed`, four devnet signatures, public judge guide, AI disclosure |
| 13 | `https://devpost.com/software/school-of-thought` | Merkle-per-round memo, refusal on chain, OxHack 2026 |
| 14 | `https://devpost.com/software/backfill-1kpq2o` | **a quant project with a frozen-rule SHA-256 memo, Gator Quant Hacks** |
| 15 | `https://note.com/midnight_jpn/n/nbc5d338ae2be` | the publisher's own Japanese translation of the Midnight winners post: completed layer, deployment, one-sentence use case |
| 16 | `https://midnight.network/blog/celebrating-seven-winners-from-mlh-x-midnight-july-hack` | blocked by a Vercel checkpoint; MEASURED-ABSENT |
| 17 | `https://colosseum.com/hackathon` | a different competition's seven factors, and its explicit exclusion of code quality |
| 18 | `https://faucet.solana.com/` | "AI agents should not use this faucet"; the airdrop is an operator action |

Local evidence: `records/findings/02-rubric-and-scoring.md`, `records/findings/17-hackathon-rules-recheck.md`,
`records/findings/18-onchain-install-and-test.md`, `records/findings/21-onchain-hook-in-tree-and-publish.md`,
`records/STATE-OF-PROJECT.md`, `records/SUBMISSION-PACK.md`, `records/DELIVERABLE.md`, `README.md`,
`docs/RUN.md`, `docs/SHOTS.md`, `fixtures/README.md`, `programs/cap_hook/`, `ticketpath/`, and the
pre-event research corpus outside this repository, which is not published and stays out of the tree.

---

*No source file was changed by this pass. One file was written: this one. Nothing was committed, nothing
was pushed, and no command in this pass touched a cluster, a faucet, a live process or a key.*

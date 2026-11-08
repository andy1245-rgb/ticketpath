# ticketPricing — standing brief

Read this before your first action, then read `RESEARCH-PROGRAM.md` in full. The
programme is the authority on **what** to research and to what standard. This file is
the authority on **how** the run is conducted.

## The thing being built

An engine that prices primary-market tickets off the secondary market's own price
record. Given a ticket, an event and a time-to-event, produce: what it is realistically
worth on resale, how that value moves over the remaining horizon, the probability it
actually transacts at a given price, and the primary price that maximises risk-adjusted
expected economic value rather than an assumed markup.

The final test is in §5 of the programme: a defensible, empirically testable,
economically rational, computationally efficient engine — not research volume.

## What is already on this machine, and why it changes the starting point

Verified on disk before this session started, not assumed:

- `../ticketing-frontend/` — the company's own platform UI, a sibling checkout of this
  repository. Next.js, no backend yet. `lib/types.ts` is the wire contract and
  `API_CONTRACT.md` maps every endpoint the frontend will call.
- The platform is Solana-ticketed: tickets are wallet-bound tokens and **every resale
  price and custody hop is a ledger entry**. Markup is expressed in basis points over
  face value; money is integer lamports; timestamps are ISO-8601 UTC.

That has two consequences for the research, and they should be checked rather than
taken on trust:

1. A resale on this platform is a *recorded transaction*, not an asking price. The
   general ticket-market literature spends most of its effort on latent
   market-clearing price under censoring and asking/realised gaps. Here that part of
   Phase 2A is smaller than the literature implies. What remains hard is the primary
   side, listings that never sold, and events with no resale history at all.
2. The ledger yields transaction-level features that scraped ticket datasets do not:
   time between custody hops, repeat-reseller behaviour, holding duration, markup
   distribution conditioned on section and on time-to-event, and a true per-ticket
   price path.

`lib/mock/` in the frontend is **synthetic fixture data built to render the UI**. It is
not evidence and must not be used to estimate anything or to claim a validated result.
If real ledger data is needed, ask the operator for it; do not build pipelines against
imagined data.

## Evidence discipline — non-negotiable

- Every important conclusion carries the programme's classification (§4.3, A through E)
  and never presents a hypothesis as an established finding.
- No fabricated datasets, accuracy numbers, significance tests or source capabilities
  (§4.6). Where evidence does not exist, write that it does not exist and say what
  experiment would produce it.
- Distinguish predictive from causal usefulness throughout, and check temporal
  correctness — what was knowable at prediction time — on every feature (§4.7, §4.8).
- Follow citations to the primary source. Prefer original papers over summaries and
  over blog posts about papers.

## Research record — written to files as it is produced

Chat is not storage. A subagent's result dies with its transcript.

Maintain the programme's six records (research ledger, mathematical knowledge base,
variable registry, model registry, data-source registry, decision and unresolved-question
log) as files in this repository, updated as findings arrive and never reconstructed at
the end. Conflicting findings are recorded, not silently dropped. Choose the layout and
say what it is; it should be obvious to a stranger.

## How the run is conducted

- This session is the orchestrator for this one project. Dispatch the phases and read
  the results. Do all of the labour beneath yourself.
- Dispatch discipline: cheap tier for subagents, the expensive model in the orchestrator,
  and name the tier at dispatch. Never a silent upgrade to a higher tier.
- Parallelise independent investigations; serialise only genuine dependencies (§1.3).
  Hand each phase over whole, with its brief — do not do a subagent's research for it.
- Adversarial review before any claim is final: Phase 6 and Phase 8 get reviewers who
  did not build the thing being reviewed.
- Bound every command. Background anything that can run past five minutes, log it, time
  it, kill it yourself.
- No push, publish or upload without the operator's explicit yes. Nothing personal or
  sensitive goes on a public GitHub.
- Autonomy: run to completion, do not ask permission for work already in scope. Come
  back only for a fork in the architecture, a design decision that changes the
  deliverable, or money.

## Public repository safety

This repository is public (`andy1245-rgb/ticketpath`). Everything committed is published,
including the research record, so the record is written for a stranger to read.

Never commit, and treat as an incident if one lands:

- **Operational handover material.** `NIGHT-*.md`, snapshot directories, WIP handover
  notes. They name live processes, pids, panes, a schedule and this machine. They stay
  local and are git-ignored: not evidence, and no research claim rests on them.
- **Credentials of any kind.** Key blocks, tokens, `.env` contents, key paths, the deploy
  key's name. No exception for a dev key.
- **Absolute paths under a home directory.** `../ticketing-frontend` says the same thing
  and leaks no username and no machine layout.
- **The operator's other repositories and infrastructure**, by name.
- **Pids and ports of live services** in prose. A design note may say 8787 is refused; it
  may not record which process holds the port.

`tools/public_safety.py` is the check. Three entry points, three different sets of files, and
the difference between them is the whole story: read the coverage, not the intention.

- **A commit.** `.githooks/pre-commit` (installed by `core.hooksPath=.githooks`) runs
  `check --staged`, which reads only the files in that commit. It then runs a credential scan
  over the staged blobs, and if a staged path is code (`ticketpath/`, `tests/`, `tools/`) it
  runs `tp.py gate --quick`. A hit in a tracked file the commit does not touch is never seen
  by it.
- **A push.** `~/ticketpath-push.sh` is scheduled every fifteen minutes and runs
  `check --range origin/main..HEAD`, plus a credential grep over the same diff, before it
  pushes; exit 1 or 2 refuses the push and logs the hits. It covers the commits ahead of
  `origin/main`, which is not the same set as the tree: what is already published is not in
  the range.
- **The whole tree.** `python3 tools/public_safety.py check --tracked` reads every tracked
  file from disk and is the only one of the three that looks at what is already there. It
  passes. Measured 2026-11-08T09:22Z at `HEAD 948b5d5`: **clean over 285 tracked files**,
  `public_safety: clean, tracked tree, 285 file(s)`, exit 0. That reading reversed by commit
  `aea1cbe`, "Redact the machine handles from the published proof files". The paragraph
  below is kept because it records how the tree got there and what the redaction cost.
  It was true as written at 2026-11-07T18:50Z: **64 hits in 9 tracked files, every one of them under
  `records/`** — 48 `live-service`, 14 `home-path`, 2 `fleet-repo`: `FINAL-PROOF-2.md` 26,
  `FINAL-PROOF.md` 14, `DEMO-PROOF.md` 11, `findings/07-engine-review.md` 4,
  `findings/10-final-review.md` 3, `FRONTEND-HONESTY-PATCH.md` 2, `REPO-CONSISTENCY.md` 2,
  `CONTRACT-CONFORMANCE.md` 1, `FIXTURE-STORE.md` 1. An hour earlier, at `8a5e5e6`, the same
  command read **77 hits in 11 files**; `findings/12-final-audit.md` and `DELIVERABLE.md` left
  that list only because the stale-claims pass had to redact a home path or a process id to
  commit a correction to them, and both correction notes say what went. Those hits are quoted
  measurements in the research record — a pid in a state table, an absolute path inside a
  command's output — and they are published. None of the 9 carried an `allow` line, so a run that
  staged one of them was refused until the file was redacted or a per-file exception with a
  reason was added to `.public-denylist`, and both were the operator's call: the record is the
  run's evidence, and history is never rewritten without his explicit yes. The first option is
  what was taken, in `aea1cbe`, and `.public-denylist` is unchanged.

So a commit is gated, a push is gated, and the tree is not. The sentence this file used to
carry, "It must pass before any commit and before any push", was true of the two gates and
false of the tree, and it is quoted here rather than deleted. Rules and their reasons are in
`.public-denylist`, exceptions are per path glob and per class with a reason each, and
`docs/PUBLIC-SAFETY.md` is the full account, with the same measurement in it.

Two rules that are not about the checker:

- **History is never rewritten without the operator's explicit yes.** No rebase of a
  pushed branch, no force-push, no filter. A secret that is already published is rotated
  first; the history question is his to answer, not a tool's.
- **Handover files stay local.** When a run ends, what it learned goes into `records/` as
  research; the instruction sheet it was driving itself with stays on disk, out of git.

Records may quote `/tmp` paths and do: a quoted path is evidence of what a run did. That is
the one stated exception, written in the denylist rather than assumed.

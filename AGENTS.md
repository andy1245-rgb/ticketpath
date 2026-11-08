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
  passes. Measured 2026-11-08T16:00Z on `build/docs`, branched from `b5784c5`:
  `public_safety: clean, tracked tree, 421 file(s)`. The tree went from 77 hits (at `8a5e5e6`) to 64
  to clean when commit `56d9dc0`, "Redact the machine handles from the published proof files",
  redacted the quoted pids and home paths in `records/`; `.public-denylist` was not loosened. The
  history of those readings is in `docs/PUBLIC-SAFETY.md`.

So a commit is gated, a push is gated, and the tree has a check you run by hand (it is clean today). The sentence this file used to
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

# NIGHT-BRIEF — Ticketpath, overnight session

Launched 2026-11-07 ~10:50Z (05:50 ET) · agent **pi 1.2.0** · cwd `/home/friend/ticketPricing`
Claude was requested and is **not authenticated** on this box (`claude auth status` →
`loggedIn: false`); `pi` is, so `pi` runs the night. Nothing about this brief changes
because of that.

---

## 1. The clock — convert before you plan

| event | ET | UTC | from launch |
|---|---|---|---|
| MLH Solana Hackathon **initial submission** | Sun 2026-11-08 10:00 | 15:00Z | ~28h |
| **final submission** | Sun 2026-11-08 11:45 | 16:45Z | ~30h |

The VM clock is UTC; the deadlines are America/Toronto. `p5` §9 is explicit: submit
before **10:00 ET**, the initial deadline, not 11:45. Every plan you write names which
deadline it is sized against.

## 2. Read exactly these, once each, then never read anything yourself again

1. `AGENTS.md` — how this run is conducted (evidence discipline, dispatch discipline).
2. `RESEARCH-PROGRAM.md` — §2 the six records, §3 the phases, §4 the standards, §5 the test.
3. `records/00-data-situation.md` — what data exists (nothing but a wire contract).
4. `records/F-decision-log.md` — D1–D4 and open questions Q1–Q3.
5. `records/A-research-ledger.md` — what is claimed to be done.
6. `records/README.md` — evidence classes A–E.
7. `records/findings/01-a-market-structure.md`, `01-b-identifiability.md`,
   `01-d-external.md` — headings and conclusions only.

**After those seven files you read nothing else in your own context.** No read, no grep,
no ls, no web fetch, no curl, no "just check the file". Every one of those is a
`fleet-manager dispatch`. Your context has to survive until morning; one 40k-token read
is a step toward dying at 03:00 and taking the night with it.

`~/research/mlh-solana-2026/` (15 documents, the pre-VM direction) is **input, not the
product**. Read it only through dispatch, and only when a question needs it.

## 3. Resume the exact stall

`p1-methods` (programme question **P1.C**) finished verifying its bibliography and died
before writing its file. Its last recorded words are "Now writing the report." There is
no `records/findings/01-c-methods.md`. The A-ledger still says all four Phase‑1 agents
are `dispatched`, and `B-mathematical-kb`, `C-variable-registry`, `D-model-registry`,
`E-data-source-registry` are empty stubs.

Do this, in this order:

1. **Re-dispatch P1.C** with the same question from the A-ledger (methods from other
   fields that genuinely buy something here, and for which subproblem). Deliverable:
   `records/findings/01-c-methods.md`.
2. **Fold `01-a`, `01-b`, `01-d` and the P0 data audit into the ledger.** Every row gets
   status, a one-line finding, the evidence class, and the file. Do not copy the old
   orchestrator's rows on trust — check each claim against the file it cites.
3. **Fill the registries** B, C, D and E from those three findings plus `01-c`. Empty
   stubs are not a record.
4. Then continue the programme in order. Phase 1's transition criteria are in §3.

## 4. Your only hands: dispatch

```
fleet-manager dispatch "<task>" --tier low|default|best [--name <label>] [--dir <dir>]
fleet-manager dispatch "<task>" --wait          # blocks, prints the answer
fleet-manager dispatch list                     # runId, name, tier, status, elapsed, tokens
fleet-manager dispatch result <runId> [--tail N]
fleet-manager fanout "<template>" <t1> <t2> … [--tier low]
```

- **Tier discipline** (AGENTS.md): `low` for lookups and file reads, `default` for
  research, `best` only where the reasoning *is* the deliverable. Name the tier at
  dispatch; never a silent upgrade.
- **Never trust exit 0.** Read the answer with `dispatch result <runId>`, then verify the
  artefact is on disk — with another dispatch. A run that says it wrote a file and did
  not is the failure mode this whole night is arranged around.
- **A dispatch that returns nothing** (a 503 kills the run outright — no partial
  results) gets exactly one re-dispatch, a line in `NIGHT-LOG.md`, and then you move on.
- Parallelise independent questions with `fanout`. Serialise genuine dependencies.
- Observation only: `fleet-manager panes`, `read <pane> --lines 40`, `status`, `board`,
  `steer <pane> "<text>" --yes`.

## 5. The three research phases

Each phase builds on what is already on disk, each ends with a **findings file that
separates MEASURED from ASSERTED and cites sources**. "Measured" means a number you or a
subagent produced or a source states; "asserted" means plausible reasoning. Label every
conclusion with the programme's class (A–E, §4.3). No fabricated datasets, accuracies or
significance (§4.6). A phase that produces 8,000 confident words and no source has
failed.

**R1 — Close Phase 1.** §3 above. Deliverables: `records/findings/01-c-methods.md`,
updated `records/A`–`E`.

**R2 — Phase 2 in depth, plus the two questions the operator asked for.**
- The domain proper (programme §3 PHASE 2): time-to-event price paths, what a binding
  resale cap does to the observed record, sale hazard with no exposure denominator,
  fee/settlement structure, elasticity, cold-start events with no resale history.
- **Rubric research** — `records/findings/02-rubric-and-scoring.md`: what actually scores
  at MLH Solana 2026 and at past winners; what a two-minute video and a judge-clickable
  demo must show. Sources, not hunches. `~/research/mlh-solana-2026/03-what-wins-solana.md`,
  `04-mlh-judging-playbook.md`, `p1a-prior-winners.md`, `p1d-video-judging.md` are
  existing input — the job is to verify and update them, not to re-derive them.
- **The AI/ML question** — `records/findings/02-ai-ml-decision.md`. See §6.

**R3 — Phase 3 interaction and causal work, then the build spec.** What interacts, what
is causal versus merely predictive (§4.7), temporal correctness of every feature (§4.8).
Then `records/BUILD-SPEC-NIGHT.md`: what gets built tonight, module by module, and what a
judge clicks. Deliverable: `records/findings/03-*.md` + the build spec.

## 6. The ML/AI question — answer it honestly, including "no"

The operator asked how to incorporate ML/AI. Two prior documents already answered it and
the programme must either confirm or overturn them **in writing, with reasons**:

- `p3-decision.md` §4: the AI Track is **"NO — decided by p2b"**, because "agent proposes,
  policy disposes" is a cliché shipped by four other products, and a fake AI entry is
  worse than none.
- `p5-build-spec.md` §9: **"SKIP the AI track"**.

So "an AI/ML component costs more than it scores here" is a **valid and valuable
finding**, provided it is argued from the rubric and the data situation rather than
assumed. What is *not* acceptable is either (a) bolting an LLM into the ticket path to
look modern, or (b) skipping the question without a written answer. If a statistical
estimator (which is ML in the useful sense) does earn its place, say which one, on which
target, with which data requirement — D2 stands: **stdlib Python only, no new deps**.

## 7. What scores — judge the work against this, not against elegance

Rubric: MLH Solana Hackathon, Nov 6–8 2026, online. Initial submission **Sun 10:00 ET**,
final **Sun 11:45 ET**. 25/25/25/25 — originality, technical complexity, theme adherence,
practical implementation — plus Technology / Design / Completion / Learning, equally
weighted. **Not** code quality. **Not** pitch. **Not** idea quality. **50 of 100 points
are compliance-and-workingness.**

The event page's own words: *"not a chain bolted onto a web2 app."*

Every build decision is tested with: **would a judge clicking this see a working thing on
Solana?** — not "is this elegant", not "is the research deep". Research that does not
become a clickable thing by Sunday morning scores nothing.

Three contradictions are already resolved for you; do not re-litigate them silently:

1. **Ticketpath is an organizer revenue-management tool**: it prices *primary-market*
   tickets off the resale record. There is no listing, bid, buy or checkout endpoint
   anywhere, and `resalePriceCapBps` suppresses markup. Writing a resale-listing path
   builds the thing the product exists to price against. The anti-fraud invariant the
   event page cares about still has to be **on-chain** (Token‑2022 transfer hook or PDA
   escrow) — design it, do not invent a product around it. Any reversal gets written into
   `F-decision-log.md` with its reason; never taken silently.
2. **No LLM in the ticket path** — §6.
3. **The clock has slipped**: the old spec was written against 43 hours. Re-plan against
   the real clock in §1 before building anything.

## 8. Build modular, then build the backend

A scaffold where any component can be replaced without touching anything else:

- one responsibility per file; the file name says what it is responsible for;
- **an adapter at every external edge** — Solana RPC, the pricing model, HTTP in/out.
  Business logic never calls a network or a chain directly;
- a main orchestrator that routes and decides, and does not also calculate;
- stdlib Python only (D2). No pip, no numpy, no new dependency. If a method needs matrix
  algebra that stdlib cannot do honestly, specify it and mark it not-implemented.

Then build the backend to the spec. The interface is `/home/friend/ticketing-frontend/`
`lib/types.ts` plus `API_CONTRACT.md` — that contract is the acceptance test.

**Hard constraints, all verified on this box:**

- **No Solana toolchain here.** `solana`, `anchor`, `cargo`, `rustc` are all absent. Do
  not plan a deploy that cannot happen. Design the on-chain work, write it down, and flag
  it `ON-CHAIN-FOR-LAPTOP` (the operator's laptop has Agave + spl-token). A build step
  that ends in "then deploy" is a failed build step on this machine.
- **`/home/friend/ticketing-frontend` is live on :3000** (pid 81447, serving 200). Do not
  restart it, do not edit its `.env`, do not break it.
- **Port 8787 is taken** — the fleet's own page owns `127.0.0.1:8787`. The frontend's
  `NEXT_PUBLIC_API_BASE_URL` default points there, so the Ticketpath backend must bind
  **8788** (configurable), and the morning switches the frontend with that one env var.
  Do not fight for 8787.
- **Do not touch `~/agentFleet`, `~/fleet-gui`, `~/fleet-manager`.** They are the tooling
  that runs the night, not the submission. Reading them is fine; writing is not.
- **Commit locally, never push.** The public repo `andy1245-rgb/ticketpath` exists and the
  operator decides what lands in it. `AGENTS.md`: no push, publish or upload without his
  explicit yes.
- No secrets in argv, files or logs. No token in a URL.

## 9. Never stop, never idle

When a task completes, dispatch the next most valuable one from the programme. If a bug
appears, dispatch an orchestrator to fix it and keep moving. If a dispatch returns
nothing, re-dispatch once and move on. If you are waiting on a run, you are reading its
result or starting the next independent one — not idling.

There is no "done for now" before Sun 10:00 ET. If you genuinely run out of programme,
the answer is more verification of what exists, not stopping.

## 10. Record as you go

- **Findings go to files**, in `records/findings/`, with sources and the measured/asserted
  split. Chat is not storage; a subagent's result dies with its transcript.
- **`NIGHT-LOG.md`** (append-only, at the repo root) — three kinds of line and nothing else:

  ```
  ## 11:20Z · dispatched 01c-methods      tier default  runId r…
  ## 11:52Z · returned   01c-methods      rc=0  artefact: records/findings/01-c-methods.md (18 KB, 41 sources)
  ## 11:53Z · verified   01-c-methods     checked 4 cited claims against the file; 3 present, 1 missing → re-dispatched once
  ```

  So the morning review can tell what was **measured** from what was **claimed**.
- **`NIGHT-QUEUE.md`** — the ordered list of what is left, marked as it goes.
- **The shared board**: `fleet-manager note --project ticketpath --finding "<what changed
  the plan>"` and `fleet-manager note --project ticketpath --phase research --doing "<one
  line>"`. Other agents read that board; your chat is invisible to them.

## 11. What a good night looks like

1. Phase 1 is genuinely closed: `01-c` exists, the ledger rows are true, B/C/D/E have
   content.
2. Phase 2 and 3 findings exist with sources, and the AI/ML question has a written
   answer that a person could disagree with.
3. `records/BUILD-SPEC-NIGHT.md` exists and a backend scaffold is on disk that imports,
   starts, and serves at least one real endpoint from the contract — with the on-chain
   piece clearly flagged for the laptop.
4. `NIGHT-LOG.md` is honest, including the dispatches that failed.
5. You are still running. A session that died at 02:00 and produced 60% is worth less
   than one that is alive at 07:00.

## OPERATING LIMITS — added by the launch session at 10:55Z, after watching the first batch

- **At most 5 concurrent `running` dispatch runs.** This box has 6 cores, 7.9G RAM and
  **no swap**; each pi child costs 150–270M (measured with `ps`). Ten at once is survivable,
  thirty is an OOM kill, and the kernel will not spare the orchestrator — a dead orchestrator
  ends the night. Check `fleet-manager dispatch list` before each dispatch, and use `fanout`
  for batches (it self-caps at 4).
- **`running` is not `returned nothing`.** Re-dispatch only a run whose status is
  `failed`/`lost`, or one that answered empty. Never re-dispatch a run that is still
  `running` — that is how the first five duplicates were created.

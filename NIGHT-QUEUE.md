# NIGHT-QUEUE — Ticketpath overnight, ordered

Sized against **Sun 2026-11-08 10:00 ET (15:00Z)**, the initial submission deadline.
Started 2026-11-07 10:50Z. ~28h.

Marking: `[x]` done and verified on disk · `[~]` dispatched, unverified · `[ ]` not started.

## R1 — close Phase 1 (the stall)

- [x] 01-c-methods: records/findings/01-c-methods.md written (36 KB) - result collection pending
- [x] ledger truth: records/findings/00-ledger-verification.md (25.7 KB, 9 rows, 3 unsupported) + A-research-ledger.md rewritten (10.3 KB)
- [x] C-variable-registry filled (64.8 KB)
- [x] E-data-source-registry filled (44.6 KB, 27 sources)
- [ ] A-research-ledger rewritten: true status, one-line finding, class, file, for P0.1-P0.5, P1.A-D
- [ ] B-mathematical-kb filled (needs 01-c)
- [ ] D-model-registry filled (needs 01-c)

## R2 — Phase 2 in depth

- [~] 02-rubric-and-scoring (running since 10:53Z)
- [~] 02-a price paths: dispatched dmw6a6rtwd7ks
- [~] 02-b cap truncation: first run died on provider stream errors after 35m; re-dispatched dmw6bgfuhsqjj
- [x] 02-c sale hazard: records/findings/02-c-sale-hazard.md (83.8 KB, 33 sources)
- [~] 02-d elasticity/fees/optimum: dispatched dmw6a8cx1vkil
- [x] 02-e cold start: records/findings/02-e-cold-start.md (76.5 KB)
- [ ] 02-ai-ml-decision (brief ready, needs the rubric finding)

## R3 — Phase 3, then build

- [ ] 03-a interactions (after the cap file)
- [ ] 03-b temporal correctness of every feature
- [ ] BUILD-SPEC-NIGHT.md
- [~] backend scaffold: ticketpath/ tree + tests building (dmw6a80la3zxh); CONTRACT-MAP.md 27.8 KB already on disk
- [~] docs/ON-CHAIN-DESIGN.md (dmw6aoa9lvvnl) + docs/ON-CHAIN-FOR-LAPTOP.md from the scaffold
- [x] frontend switch documented in docs/BACKEND.md (NEXT_PUBLIC_API_BASE_URL=http://localhost:8788); frontend untouched
- [ ] adversarial review of the engine claim by an agent who did not build it

## Standing constraints

- stdlib Python only (D2); no pip, no numpy. No invented data or numbers (4.6).
- no push, no publish, no upload; local commits only.
- do not touch ~/agentFleet, ~/fleet-gui, ~/fleet-manager; do not restart the :3000 frontend; 8787 is the fleet's page.
- every findings file separates MEASURED from ASSERTED and carries A-E classes.

## OPERATING LIMITS — added by the launch session at 10:55Z, after watching the first batch

- **At most 5 concurrent `running` dispatch runs.** This box has 6 cores, 7.9G RAM and
  **no swap**; each pi child costs 150–270M (measured with `ps`). Ten at once is survivable,
  thirty is an OOM kill, and the kernel will not spare the orchestrator — a dead orchestrator
  ends the night. Check `fleet-manager dispatch list` before each dispatch, and use `fanout`
  for batches (it self-caps at 4).
- **`running` is not `returned nothing`.** Re-dispatch only a run whose status is
  `failed`/`lost`, or one that answered empty. Never re-dispatch a run that is still
  `running` — that is how the first five duplicates were created.

## Handoff — state at 13:05Z, 2026-11-07

**Closed and verified on disk**
- Phase 1: 01-a, 01-b, 01-c, 01-d, plus the ledger verification, the adversarial review and the corrections pass. A-research-ledger is true against its files.
- Phase 2: 02-a price paths, 02-b cap truncation, 02-c sale hazard, 02-d fees/elasticity/optimum, 02-e cold start, 02-rubric, 02-ai-ml (D5).
- Phase 3: 03-a interactions, 03-b temporal correctness.
- Phase 6: 06-validation-protocol. Phase 8: DELIVERABLE.md (22 sections, disagreements left visible).
- Records: B, C, D, E filled. On-chain design + reconciliation (D6).
- Backend: stdlib, adapters at every edge, console at 8788/, 352 tests. Contract conformance: 8/9 routes conformant, drift closed. Independent engine review failed honesty and code; both fixed and re-verified (6 of 8 outright, 2 partial, then four more defects fixed).
- Fixtures: 8 events, 3 regimes, generator + --check.
- Frontend: copy at ~/ticketpath-demo on :3001 proven against our backend; honesty patch prepared for the live tree (not applied).

**Only the operator can do**
1. Push to the public repo — its main still predates every file of the product. Blocks submission.
2. Decide console reachability for judges: record only, tunnel, or deploy.
3. Q1 seat coordinates, Q2 anything deployed anywhere, Q3 cap enforcement locus.
4. Apply docs/frontend-honesty.patch to the live frontend, then set NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788 and restart :3000 (NEXT_PUBLIC_* is inlined at build time, so a restart is required, not optional).
5. Fill the licence holder line. Record the two-minute video from the script in records/SUBMISSION-PACK.md.

**Still worth doing tonight**
- Re-run the adversarial review on any surface changed after 07-engine-review.
- The three items the honesty fix left: badge placement inside prose, the candidate cap not passed to the optimum, the loader accepting rows the core refuses.
- A SIM study per 06-validation-protocol (estimator recovery), labelled SIM.

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
- [~] 02-b cap truncation: dispatched dmw6a6rsw3nux
- [x] 02-c sale hazard: records/findings/02-c-sale-hazard.md (83.8 KB, 33 sources)
- [~] 02-d elasticity/fees/optimum: dispatched dmw6a8cx1vkil
- [x] 02-e cold start: records/findings/02-e-cold-start.md (76.5 KB)
- [ ] 02-ai-ml-decision (brief ready, needs the rubric finding)

## R3 — Phase 3, then build

- [ ] 03-a interaction registry and causal-vs-predictive per relationship
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

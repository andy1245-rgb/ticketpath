# A — Research ledger

Curated index of every research question. Raw reports live in `findings/`. Status is one
of `open`, `dispatched`, `answered`, `answered-partial`, `closed-not-worth-it`.
Evidence class (A–E, SIM, UNVALIDATED) is per `records/README.md`.

**Last updated:** 2026-11-07T08:45Z

---

## Phase 0 — data situation

| ID | Question | Agent | Status | Finding | Class |
|---|---|---|---|---|---|
| P0.1 | Does a backend, database or deployed Solana program exist on this machine? | orchestrator | answered | No backend, no DB, no program id anywhere; `API_CONTRACT.md` specifies a backend that does not exist. | verified |
| P0.2 | Are `lib/mock/` the real ledger? | orchestrator | answered | Synthetic fixtures: no generator, no provenance, mint addresses are not valid pubkeys (devnet RPC `WrongSize`), cap never binds in the generated prices. | verified |
| P0.3 | What observation set does an estimator receive? | orchestrator | answered | The `lib/types.ts` wire contract: ledger rows, ticket metadata, event metadata, derived aggregates. Full audit in `00-data-situation.md`. | verified |
| P0.4 | What is missing from the contract that a pricing engine needs? | orchestrator | answered | Four gaps: no listing exposure (kills sale-hazard identification), policy price ceiling truncating the value distribution, no seat coordinates, no fee/settlement field. | verified |
| P0.5 | Can any estimator be validated here? | orchestrator | answered | No. Every quantitative conclusion is class B, C, SIM or UNVALIDATED. Simulation is admissible only for estimator properties. | verified |

## Phase 1 — foundational discovery (dispatched 2026-11-07)

| ID | Question | Agent | Status | Finding | Class |
|---|---|---|---|---|---|
| P1.A | What is the actual market structure and economic mechanism of primary and secondary live-event ticketing, and what does the evidence say about time-to-event price paths, resale caps, and platform economics? | forge `p1-market` (tier `default`) | dispatched | — | — |
| P1.B | Given a completed-transaction ledger with no asks and no exposure, what is identifiable? Which quantities (value, path, sale probability, elasticity) survive, which do not, and what is the minimal extra observation that fixes each? | forge `p1-ident` (tier `best`) | dispatched | — | — |
| P1.C | Which methods from other fields (revenue management, survival, hedonic pricing, auction theory, online learning, Bayesian partial pooling, conformal prediction, stochastic control) genuinely buy something here, and for which subproblem? | forge `p1-methods` (tier `default`) | dispatched | — | — |
| P1.D | Which external signals have a plausible mechanism and are actually obtainable and licensable, and what is each one's collection cost and leakage risk? | forge `p1-external` (tier `default`) | dispatched | — | — |

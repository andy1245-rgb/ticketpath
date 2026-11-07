# DELIVERABLE — the Phase 8 integrated specification

**Status: NOT WRITTEN YET.** Written 2026-11-07T12:06Z as a stub so that the pointer from
`records/README.md` resolves and so that what is missing is stated rather than implied.

`RESEARCH-PROGRAM.md` Phase 8 requires one document containing the twenty-two sections below.
What exists today is the input to it, not the document: six research records with evidence
classes, seventeen findings, a contract conformance record, and a working backend that computes
from a synthetic fixture. Nothing here is a research result about ticket markets, because the
real ledger does not exist yet (`records/00-data-situation.md`, `records/A-research-ledger.md`).

Read this file as a table of contents with an honest status per section, not as the deliverable.

| # | Section the programme requires | Where the material is today | Written? |
|---|---|---|---|
| 1 | Executive summary | nothing | **no** |
| 2 | Problem formulation | `RESEARCH-PROGRAM.md` §0; `records/00-prior-direction-index.md` | partial |
| 3 | Market mechanics | `records/findings/01-a-market-structure.md` | yes, as a finding |
| 4 | Literature review | `records/A-research-ledger.md`; `records/findings/` | yes, as a ledger |
| 5 | External variable registry | `records/C-variable-registry.md`; `records/E-data-source-registry.md` | yes |
| 6 | Interaction and causal analysis | `records/findings/03-a-interactions.md` | yes, as a finding |
| 7 | Statistical methodology | `records/B-mathematical-kb.md` | yes |
| 8 | Machine-learning methodology | `records/findings/02-ai-ml-decision.md`; `records/D-model-registry.md` | yes, as a decision to not use one |
| 9 | Transaction-price estimation | `records/findings/02-a-price-paths.md`, `02-b-cap-truncation.md` | partial: identified as a bound, not an estimate |
| 10 | Demand and sale-probability estimation | `records/findings/02-c-sale-hazard.md`, `01-b-identifiability.md` | **refused as unidentified**; that refusal is the finding |
| 11 | Predictive uncertainty | `records/B-mathematical-kb.md`; `ticketpath/core/value_band.py` | partial: a declared bound width, not a predictive interval |
| 12 | Primary-market optimization | `records/findings/02-d-elasticity-fees-optimum.md`; `ticketpath/core/primary_optimum.py` | partial: a boundary recommendation, no interior optimum |
| 13 | Risk methodology | `records/F-decision-log.md` D5; `records/findings/02-d-elasticity-fees-optimum.md` §4 | partial: a one-sided bound, no risk functional |
| 14 | Data architecture | `records/00-data-situation.md`; `records/E-data-source-registry.md`; `records/CONTRACT-MAP.md` | yes |
| 15 | Validation framework | `records/findings/06-validation-protocol.md` | yes, as a protocol; nothing has been validated against real data |
| 16 | Integrated mathematical model | `records/B-mathematical-kb.md` | partial: the pieces are separate |
| 17 | Software architecture | `README.md`; `docs/BACKEND.md`; `ticketpath/` | yes |
| 18 | Implementation-ready Python | `ticketpath/` (293 tests) | yes |
| 19 | Performance considerations | nothing beyond one measured startup and one test runtime | **no** |
| 20 | Limitations | `records/F-decision-log.md`; the `UNVALIDATED` label throughout | partial |
| 21 | Unresolved questions | `records/F-decision-log.md` open questions | yes, as a list |
| 22 | Full bibliography | `records/A-research-ledger.md`; the per-finding sources | yes, distributed |

**What would make this file the deliverable.** It would have to state, for a section 9 or 10 that
is currently a refusal, the observation that identifies the quantity and the dataset that carries
it. Neither exists in this repository, so no amount of writing turns this stub into the Phase 8
document. That is the honest state and it is recorded here rather than at the end of a session.

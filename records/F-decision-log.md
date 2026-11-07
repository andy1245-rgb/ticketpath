# F — Decision and unresolved-question log

Decisions with their evidence, rejected approaches, conflicting findings, and questions.
Nothing is deleted from here; a question that is no longer worth pursuing is marked
closed with the reason, not removed.

**Last updated:** 2026-11-07T08:50Z

---

## D1 — The programme runs against the wire contract, with no real data (2026-11-07)

**Decision.** Build and specify the engine against `lib/types.ts` as the interface and
the observation set, and treat all validation as unvalidated-until-data. Do not build
pipelines against `lib/mock/`.

**Evidence.** `records/00-data-situation.md`: no backend, no database, no deployed
program, fixtures synthetic (mint addresses do not decode to 32 bytes; no generator, no
provenance).

**Consequence.** Class A conclusions can only be cited from published ticket research.
Simulation is admissible for estimator properties only (label SIM), never as validation
against a market. This is the single decision the rest of the programme is conditioned
on.

## D2 — Standard-library Python only (2026-11-07)

**Decision.** Every component, including the simulation studies and the test suite, is
pure Python 3.12 standard library.

**Evidence.** No pip, no ensurepip, no numpy/scipy/pandas/sklearn/statsmodels on this
machine; `venv` exists but cannot install. Verified by import attempts.

**Consequence.** Models that need matrix algebra are specified mathematically and
implemented either with explicit small-dimension loops or with a stdlib-feasible
reformulation (e.g. logistic regression by Newton–Raphson over a handful of features,
quantile regression by linear programming is out — use iterative reweighted least
squares or a coordinate-descent approximation, and say which is approximate). Where a
method is genuinely infeasible here, it is documented as specified-not-implemented so
the operator can install a stack and build it.

**Rejected alternative.** Vendoring a numerical library into the repo: violates "the repo
is code only, no binaries", and puts us in the dependency-management business for no
return on a model this small.

## D3 — The sale-probability component is a data requirement, not a model (2026-11-07)

**Decision.** Do not write an estimator for `P(sale at price p | state)` from the
transaction ledger alone. Specify the four fields that make it estimable, implement the
estimator behind a data-adapter that will accept them, and mark the component
UNVALIDATED and cold-start-degraded until they exist.

**Evidence.** Gap 1 in `00-data-situation.md`: `Ticket.status = "listed"` is a state, not
a history; there is no listing start, ask, revision or withdrawal, so the sale count is
a numerator with no exposure denominator.

**Open question for the operator (the one data request of this programme).** Add to the
ledger or to a sibling listing table: `listPriceLamports`, `listedAt`, `delistedAt`
(null while live), `delistReason ∈ {sold, withdrawn, expired, cap_blocked}`. The last
enum value matters: `cap_blocked` is how a binding resale ceiling shows up as an
unfilled attempt rather than a low price.

## D4 — Fees enter the optimiser as a parameter, not an assumption (2026-11-07)

**Decision.** Carry the fee structure symbolically through the Phase 5 optimisation and
require it as configuration. Do not assume zero fees, and do not assume an
ad-valorem-only fee.

**Evidence.** Gap 4 in `00-data-situation.md`: the contract exposes only `priceLamports`
and `markupBps`; no platform fee, royalty, processing cost or net-to-seller field
anywhere. A per-unit fee and an ad-valorem fee give different optima, so the difference
is not cosmetic.

## Q1 — Does the company's internal ledger carry seat coordinates? (open)

`AGENTS.md` claims the ledger yields "markup distribution conditioned on section". The
wire contract has tier id, serial and mint only. Either the internal ledger is richer
than the contract, or "section" means tier. This matters more than it looks: seat quality
is the strongest within-event price axis in the published ticket literature, and an
engine that only knows the tier cannot express the within-tier variation that drives
resale spread. **Ask the operator. Until answered, the seat-quality variable is recorded
as availability "not in contract" and every seat-quality claim is class D.**

## Q2 — Is any part of the platform live, on devnet or otherwise? (open)

No program id appears in the frontend and no mints resolve. If a program is deployed
elsewhere, its transaction history is a real (if small) dataset and would let part of
this programme be empirically checkable. If nothing is deployed, the first real data will
be whatever the platform records after launch, which makes the recording schema itself a
research artefact worth getting right now. **Ask the operator.**

## Q3 — Is the resale cap enforced on-chain or by the platform's matching engine? (open)

`types.ts` says the cap is a "hard ceiling", and `Ticket.transferRestricted` is defined
as whether the restriction is "actually enforced on-chain for that mint right now". The
cap's enforcement locus determines whether a capped sale is impossible (transfer reverts)
or merely prohibited (platform refuses to list), which changes what the ledger would
record at a cap: nothing at all, or an attempt with a reason. **Ask the operator; it
feeds directly into D3's `delistReason` enum.**

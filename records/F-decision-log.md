# F — Decision and unresolved-question log

Decisions with their evidence, rejected approaches, conflicting findings, and questions.
Nothing is deleted from here; a question that is no longer worth pursuing is marked
closed with the reason, not removed.

**Last updated:** 2026-11-07T11:22Z

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

## D5 — One estimator, no AI-track entry (2026-11-07)

**Decision.** Build exactly one fitted estimator, `MarkupBand`, in its prior-only branch: normal–normal
partial pooling on the per-event mean log resale-price-to-face ratio, two hyperparameters (μ, τ), no
new fields, ~65 lines of standard library. Cap its build at one hour and label its width as declared.
Do **not** enter the AI Track, and do not build an LLM, an agent loop or a learned model behind the
price for the submission.

**Evidence.** `records/findings/02-ai-ml-decision.md` in full. Four points carry it. (1) The binding
constraint is identification, not functional form: the ask is recorded only on the success branch
(`01-b` T3, `02-c` §1.1–1.2), so no model class on the deviating branch adds a column. (2) At cold
start the partial-pooling point estimate *is* the pooled mean (`02-e` §4.3), so the estimator
degenerates to the hand-specified alternative and costs one file instead of a throwaway. (3) A judge
recognises ML by a fit, a baseline and a metric; the fit has no data (`00-data-situation.md` §1, §2),
the metric can only be SIM (§5.2), and the benchmark ladder that would settle it (`02-a` §8.5) cannot
be run. (4) The AI Track's measured criterion is a two-sided materials test — "Build something where
AI and Solana each do real work" — and the organiser's own resources hand out the agent scaffolding,
so the shape is crowded by construction.

**Consequence.** **Confirms `p3-decision.md` §4 and `p5-build-spec.md` §9 in outcome.** The AI track
stays skipped. **Corrects `p3` §4 in reasoning on two points.** First, it weighed only one candidate
AI entry (the scripted scalp bot) and never weighed the estimator, which is the one candidate that is
load-bearing on a named target; the exclusion was right by accident, not by argument. Second, its
primary ground — that the generic agent form is a cliché — is the weakest available, because MLH
excludes idea quality from the rubric (`02-rubric-and-scoring.md` B2); the two stronger grounds are
that a decorative entry fails the criterion on its own wording, and that the track pays $100 per
member against a $1,000 team microgrant for each of three Top-3 places (A3). The estimator is recorded
as UNVALIDATED; its validating evidence is a SIM recovery study plus, on a real ledger, the skill
score against the martingale in `02-a` §8.5. No accuracy claim may be made about it before then.

**Rejected alternative.** (a) A gradient-boosted or nonparametric model behind the price. It has no
identified target to improve, it cannot express the cap censoring that decides the hedonic likelihood
(`01-c` §4.6; `00-data-situation.md` Gap 2), and it cannot be validated. (b) An LLM parsing tier names
into a seat-quality ordinal: the only tier vocabulary in this repository is three names, so a lookup
table gets full coverage with zero variance, and the case disappears at this platform's scale.
(c) An LLM explaining the recommendation: prose is not judged (`B2`, `B3`) and it invites "so the
explanation is the wrapper?". (d) An agent loop: the feedback loop it would need is undefined — no
logged actions or propensities (`01-c` §1.2(e)) — and the only tools it could call are our own
endpoints. (e) Spending five hours on a recovery study before the submission: those hours come out of
the page, the devnet account, the signature and the read-back, which are 50% of the published score
and currently absent.

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

## D6 — Per-ticket record plus transfer hook; no escrow, no mutable cap, no sybil claim (2026-11-07)

**Decision.** The on-chain design is the one in `docs/ON-CHAIN-DESIGN.md`: a Token-2022 mint per
ticket carrying a `TransferHook` extension that points at the program, a `TicketRecord` PDA per
ticket and an append-only `HopRecord` PDA per custody change, with the resale cap checked in the
program's own `transfer_ticket` before the transfer CPI. Three positions are settled against
`docs/ON-CHAIN-FOR-LAPTOP.md`, which is now a pointer, not a design: (1) **the PDA escrow and its
listing surface are rejected**; (2) **the cap is fixed when the event policy is created, before any
ticket is minted, and is immutable thereafter, so `set_cap` is refused**; (3) **sybil resistance is
explicitly not claimed and no nullifier is built**. Reconciliation, criteria and the residual list
of stale references: `records/ON-CHAIN-RECONCILIATION.md`.

**Evidence.** `records/CONTRACT-MAP.md` §5.3: the cap and the verified-wallet rule are policy and no
API can enforce them, because an API cannot prevent a transfer it is not asked about. A direct
`spl-token transfer` is the bypass, and the transfer hook is the only mechanism in either document
that refuses it in the runtime (`ON-CHAIN-DESIGN.md` §1.3, §3.9). Escrow was costed at an estimated
10 to 14 hours against 3 to 5 for the record plus hook, and it rebuilds the listing, buy and
checkout surface plan item (a) forbids; it also does not close the hole that matters, since a pair
who settle off-chain can route a face-value sale through the escrow and pay the rest in cash
(§4.2.1). A mutable cap reopens raise-sell-lower, and its mitigation (an effective-date stamp plus
a re-check at execution) is only as good as a policy history this design does not carry (§2.1,
§11). The nullifier guarantees "this commitment was registered once" while the identity behind it
is proven off-chain, so it would license a stronger sentence than it earns, and half its test
surface is off-chain (sibling §6, `ON-CHAIN-DESIGN.md` §4.2.6). Deadline is Sun 2026-11-08 10:00
America/Toronto (15:00Z, per `records/00-prior-direction-index.md` item (h)).

**Consequence.** The on-chain claim narrows to one sentence and becomes checkable on a laptop:
**the ticket cannot move without the program recording the hop, and the program will not record a
price over the cap.** Everything the design does not stop is written down rather than implied, and
each of these is now part of the submission's honesty, not a footnote: **side payments off-chain**
(the chain bounds the record, not the money, so a recorded markup is a lower bound and the observed
distribution is squeezed from both ends, §4.2.1); **one person with many wallets** (no wallet
counting anywhere, so the real scalper mechanism at the primary sale is untouched, §4.2.6, and no
bot-resistance claim may be made in any artefact); **a compromised organizer key** (it can issue to
itself up to supply, grant verification and revoke, but cannot raise a cap, change a face, move a
fan's ticket, or rewrite a hop; what it needs is an organizer multisig on day one, §4.2.3); **a
compromised `verifier` key** (§4.2.4); and **a mint created without the hook** by anyone else, which
is the honest weakness of every hook design and belongs on a slide (§4.2.5). Answers Q3 in design
terms: the cap is enforced on-chain by this program. Q3 stays open about the live platform, whose
matching engine is not this program. Supersedes the three divergences in `ON-CHAIN-DESIGN.md` §12,
which no longer describes an open choice.

**Rejected alternative.** (a) The escrow plus listing design as `docs/ON-CHAIN-FOR-LAPTOP.md` (blob
`520fe75`, commit `3bece48`) specified it: stronger on the recorded payment, unchanged on the
residual side-payment hole, three times the hours, and it adds the product surface the plan
forbids. Kept as the named next step for the day the cap must bind on money, not deleted. (b) The
nullifier and per-wallet holding cap for a claim of "one identity per allocation": the diagnosis is
right and is recorded, the mechanism is out because the identity half is off-chain and unowned.
(c) `set_cap` with a policy history: a real product feature, deferred with its cost named, not
silently dropped. (d) Recording refused attempts on-chain so a cap violation becomes an account: it
turns the wall into a note, charges the seller for being refused and is floodable (§3.11).

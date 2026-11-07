# F — Decision and unresolved-question log

Decisions with their evidence, rejected approaches, conflicting findings, and questions.
Nothing is deleted from here; a question that is no longer worth pursuing is marked
closed with the reason, not removed.

**Last updated:** 2026-11-07T18:55Z (**D8 appended**; nothing else in this file changed).

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

**Note appended 2026-11-07T12:55Z — the diagnosis in the Evidence line above is contested three ways. The decision and the data request are not.**

D3's Evidence line states the Phase 0 audit's version: "`Ticket.status = "listed"` is a state, not a history;
there is no listing start, ask, revision or withdrawal, so the sale count is a numerator with no exposure
denominator." That is one of three readings of the same absence on record, and this file stated it as settled
while the other two are in `findings/`. Quoted, as printed:

- **Audit** (`00-data-situation.md` §4, Gap 1): "Without exposure, the observed sale count is a numerator with
  no denominator."
- **`01-b` §5.1:** "Gap 1 is misdiagnosed; the fix is right. The audit calls the sale count "a numerator with
  no denominator". The denominator is present — every ticket has an `issue` row and a known life. The
  unobserved object is the ask of the risk set."
- **`02-c` §2.1:** "The ticket-time denominator is observed (every ticket has an `issue` row and a known life),
  so *something* is identified. But that something is not a sale hazard. It is the intensity of a **composite
  process — offered, then bought** — marginalised over the unrecorded offering state:" And at the end of
  §2.1:
  "`00-data-situation.md`'s 'a numerator with no denominator' is the wrong diagnosis of the same defect — the
  denominator exists, it is the denominator of the wrong process."

**The dispute is about the diagnosis, not the fix.** All three readings agree the contract records no ask and
no offering state, and all three land on the same four fields. Quoted from D3 above, unchanged: "Add to the
ledger or to a sibling listing table: `listPriceLamports`, `listedAt`, `delistedAt` (null while live),
`delistReason ∈ {sold, withdrawn, expired, cap_blocked}`." **The data request is unchanged by the dispute,
and the operator is not asked to choose between the three readings.** What changes is how the component is
described: under `01-b` and `02-c` the baseline intensity is identified and buildable, so D3's severity is too
high for it and correct only for the price response.

**Not resolved here, deliberately.** This file does not pick a reading. The contradiction is carried as C1 in
`A-research-ledger.md`, stated in all three versions in `DELIVERABLE.md` §14.2, and treated as the wrong-process
denominator in the code path `02-c` defines. D3's decision line stands as written; only its Evidence line should
now be read as the audit's reading rather than the settled one.

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

## D7 — The resale cap is a split instrument, not a capture mechanism (2026-11-07)

**Decision.** The product claim narrows to what the cap does and stops claiming what it does not. The
sentence to retire: *"the resale premium is capturable entirely through the primary price"*. The sentence to
carry: **a cap in basis points over face removes no primary price from the organiser's feasible set and adds
no revenue channel, so the pricing objective needs no capture rate; what the cap decides, when it binds, is
how the resale price divides between the organiser's price and the reseller's margin, in the fixed ratio
`1 : c` that no primary price changes.** The cap is a split instrument. The price decides how big the resale
price is; the cap decides who gets which part of it. Superseded in `records/findings/02-d-elasticity-fees-optimum.md`
item 3 by a dated CORRECTION in place; marked at §1.5, §2.5(b), §3.6, §5.2 and §8(2) of the same file, at
`B-mathematical-kb.md` §2 (P5) and §6.1, at `D-model-registry.md` in the primary optimum's "Buys" list, and
carried into `DELIVERABLE.md` §1.6, §12.3, §12.6, §20.3, §20.4, §20.5 and `SUBMISSION-PACK.md` §1.2 beat 3
and §2.2. No engine arithmetic changed, and no console sentence stated capture, so `ticketpath/` was not
touched.

**Evidence.** `records/findings/11-cap-capture-check.md`, an independent adversarial check by an economist who
did not write `02-d` and did not build the engine: verdict **STANDS-WITH-NARROWING**. Class C for the algebra,
class D for every mechanism whose sign or size is unmeasured. The load-bearing step is the split identity
(`11` §5): a ticket settling at the ceiling sells for `p(1+c) = p + pc`, so the resale price divides
`organiser : reseller = 1 : c`; `∂(organiser's part)/∂p = 1` and `∂(reseller's margin)/∂p = c`, so raising
`p` scales both and leaves the ratio alone. Inside the cap's reach the premium is not captured, it is
enlarged. Transfer happens only once `p ≥ V/(1+c)`, where the cap is slack and the resale price is pinned at
the market value; there `∂(margin)/∂p = −1`, so the transfer is ordinary pricing to the market value on the
tickets that still sell, not a cap effect. What survives unchanged: the feasible-set result (`11` §2.1), the
objective result that no capture-rate term belongs in (O) (`11` §2.2), and the `c = 0` corollary that an
above-face resale ban constrains the reseller's price and not the organiser's (`11` §2.3). Two scope
conditions were added to the claim rather than discovered in it: the ceiling is proportional to the *face
component* of the price, not to the buyer's all-in price, so a fee-funded rise does not move it (`11` §8, A6);
and for every ticket already issued the ceiling is a fixed number, so the finding governs setting the next
event's face, not reading this event's record (`11` §8, A7).

**Consequence for the product claim.** The engine's recommendation is unaffected: it is still the sell-through
boundary, still printed as "at least", still a floor and not an estimate, and no elasticity, no arithmetic and
no number moved (`11` §10.5; `DELIVERABLE.md` §18.3). What changes is the sentence around the number. The product may say
it reads the resale record, states the price that record supports as a floor, and states the cap's role
correctly. It may not say, imply, or let a slide imply that the premium over face is the organiser's to take.
The demo's headline "at least 1.38 SOL" equals the ceiling because the highest recorded resale settled at the
ceiling, and that makes it the highest price anyone paid, hence a floor on value; it does not make the cap the
primary price (`11` §10.2, §11.4). The 22.03 SOL of recorded markup is the size of the gap the recommended
price is designed to close, not a revenue opportunity: price at the floor and the gap is gone, leaving churn at
face (`11` §10.4).

**The test it implies, and what it needs.** A scale test, on resales where the cap does not bind, so the
observed price is the market value and not policy: settled resales on events with `resalePriceCapBps = null`,
or on capped events with no row at the ceiling and the highest resale strictly below it. Variation: at least
two face levels for comparable events (same artist or tour, venue class, on-sale window). Regression:
`ln r = α + β·ln p + δ·(days to event) + controls`, standard errors clustered by event, with the decision rule
declared before the fit — **`β = 1`**: the value moves one for one with face, so the split is `1 : c` at every
level and any "capture" is nominal; **`β = 0`**: the value is absolute and face is a label, so beyond
`p = V/(1+c)` nothing is capturable and the economic content fails; **`0 < β < 1` or `β > 1`**: partial
anchoring, and the objective must carry the anchor term (`11` §7). Rows that settle at the ceiling cannot
answer it: there the resale price is mechanically `p(1+c)` and a regression of `ln r` on `ln p` returns one by
construction. The fields needed are all in the contract already; the binding constraint is the number of
comparable events, which is more than the eight events and five with any resale that this platform has. It is
a data-collection and money question, and the money is the operator's (`11` §7; `02-d` §3.6).

**What would reverse it.** Three things, in order of likelihood. (1) A cap definition change: an absolute money
ceiling instead of basis points over face voids the whole result and forces a shadow-value term into the
objective (`11` §2, §12). (2) The scale test returning `β = 0`: then raising face moves the ceiling but not
the market value, and the claim loses its economic content even though the algebra survives. (3) A binding
constraint on face, or a material reputational cost of raising face, either of which stops the organiser
before demand does (`11` §4). A settled resale at the ceiling whose price is not `p(1+c)` would falsify the
split identity itself, which would be an arithmetic error or an off-rail consideration, and that is `02-b`'s
business rather than this decision's (`11` §12).

**Rejected alternative.** Keeping the old sentence and adding a footnote. Rejected because the sentence is what
a reader repeats, and the check found that the objective-level result does not need it: the part of `02-d` §2.5
that the engine runs on is untouched, so the sentence can go without costing the mathematics anything. Also
rejected: rewriting `02-d` item 3 in place. The record is append-only; the old wording stays, quoted, with the
correction beside it (`11` §9).

## D8 — Team, corpus and provenance (2026-11-07)

**Decision.** Three things, taken together because the submission states them in one breath.

**(1) Team.** The entry is a two-person team: the operator and one teammate. Both accounts must be
registered on MLH *and* both checked in before submission. The event page splits registration, check-in and
submission into three steps and a registered-but-not-checked-in account may not be able to submit at all, so
an unchecked second member is a one-person team on the form and an eligibility question in the record. The
two names are not written here: this repository's public-safety rule denies the operator's full name outside
`LICENSE`, the check refused them at commit time, and they live on the MLH team field and in `LICENSE`
instead. Redacting the strings changed no part of the decision.

**(2) Authorship.** The code and the documents were written by AI coding agents that the team directed and
released. That is disclosed in both required AI fields in the operator's own name, in the wording §2.7 of
the pack carries, and no part of the submission is presented as human authorship.

**(3) Corpus.** `../research/mlh-solana-2026/`, fifteen documents written between 17:39:04Z and 18:48:55Z
on 2026-11-06, is **not published**, stays local, and is **not quoted** beyond the attributed citations
already committed in `records/00-prior-direction-index.md`. That index is **not trimmed**: every line that
quotes a document names the document and the section on the same line, and the operator's decision is to
keep them. The consequence is a wording rule the repository may not break: it may **not** say that no
corpus text appears in it. What it says instead is that the code and every committed artefact were written
from 08:29Z on 2026-11-07, and that the research record cites the background reading with attribution. The
word **"pre-event" is retired** for this corpus: hacking began 2026-11-06T17:00:00Z, so the corpus sits
inside the window by 39 minutes to 1 h 49 min, and in-window reading is what rules 6 and 9 permit.

**Evidence.** `records/findings/19-corpus-citations.md` in full. Measured: 91 lines across 7 files name,
cite or reproduce the corpus, 18 of them verbatim; `records/00-prior-direction-index.md` carries 413 of
5,192 eight-word sequences in common with the corpus's own prose (8.0%), longest unbroken run 40 words,
every one of them attributed on the line that quotes; the other tracked files are citations, and their
overlap is third-party text both documents quote. Nothing sensitive is in the reproduced passages: no
credential, no keypair, no personal data, no third-party non-public material, the only contact detail being
MLH's own published reporting address, already allow-listed. The timeline is `stat` on the fifteen files
(first `03-what-wins-solana.md` 17:39:04Z, last `p1b-tech-feasibility.md` 18:48:55Z) against the event's
own calendar payload `20261106T170000Z/20261108T180000Z`, and `git log` (first commit `744a2c2`,
2026-11-07T08:29:57Z, 15 h 29 min 57 s after hacking began). The rules the three parts answer to: contest
terms "An Eligible Participant (or team) must be the sole owner of the Application submitted"; rules 6 and
9 on work done inside the window; rules 12–13 on the repository staying public for ever
(`records/findings/17-hackathon-rules-recheck.md` §3.4, §3.9, §5.3, §7).

**Consequence.** `records/SUBMISSION-PACK.md` §2.8 now states the provenance sentence in a long form for
the description and a short form for a character-limited field, both carrying the measured times, and both
answering the two questions the section used to hand back. §0 item 9 (refreshed list), §3 item 12 and T4
carry the two names and the two registrations; the pack's closing note lists the three sentences it
corrected in place. The three "pre-event" sentences in
`records/findings/17-hackathon-rules-recheck.md` (§5.3 item 3, §7 item 5, the 15 lines item 14) are
corrected by an appended CORRECTION, because that file is append-only; `records/findings/19` carries an
appended correction of its own stale commit reference. No code, no engine arithmetic and no console sentence
changed, so `ticketpath/` was not touched. What is still open, and it is his alone: whether the pricing work
is also company work, because company ownership and "sole owner of the Application" cannot both hold, and
whether the corpus drew on company or private data, which the audit could bound but not settle.

**What would reverse it.** (1) A company claim on the pricing work: "sole owner" and public-for-ever then
collide and the entry needs the company's written permission or a reframing, and the team statement alone
does not fix it. (2) The second member not registered and checked in by Sunday morning: the entry is then a
single-person team, which changes the team field, the "> 50% first-time hackers" answer behind the Best
Beginner track, and any sentence in the pack that says "the team". (3) Evidence that the corpus carries
company or private data: the quoting question reopens, and the answer stops being "not published" and
becomes "not retained", which is a bigger action than the one taken here. (4) A judge or an organiser
reading the index's attributed quotations as reproduced prior material: the response is to cite the audit's
measurement, not to trim the file after the fact.

**Rejected alternative.** (a) Publishing the corpus, or any part of it: there is no scoring upside, and it
turns reading into prior materials on a public remote. (b) Trimming `records/00-prior-direction-index.md`
to citations with no quoted text, which would make "no corpus text appears in the repository" literally
true: rejected because the quotations are attributed on every line, so the sentence they would buy is one
nobody needs, and the record loses the evidence that the decisions were settled by something. (c) Keeping
the "pre-event" wording: false against the file times, and it claims the riskier of the two facts, since
notes inside the window are permitted and notes before it are what the prior-work rule excludes. (d) Saying
nothing about provenance and letting the git history speak: the history only answers "did they start before
the event", and the one wording that can cost this entry is a claim about inherited material, so the
sentence is free and belongs in the submission.

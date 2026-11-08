# F — Decision and unresolved-question log

Decisions with their evidence, rejected approaches, conflicting findings, and questions.
Nothing is deleted from here; a question that is no longer worth pursuing is marked
closed with the reason, not removed.

**Last updated:** 2026-11-08 (**D19, D26, D27 and Q6 appended**: D19 and Q6 on the frontend
import, which this branch wrote and the other checkout never had, and D26 and D27 on the
artist fee and the flip tax, which the other checkout wrote and this branch never had.
Nothing else in this file changed except this line since the D18 edit of the same day.)

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

## D9 — The app holds the tickets and every resale goes through it (2026-11-08)

**Decision (the operator's).** Three things, taken together because they are one design: the app is
the custodian and holds the tickets, every resale goes through the app, and users cannot contact each
other. The price on a resale is the app's own input control, not a number two users agree between
themselves.

**What is decided, and what is inferred.** Only the paragraph above is decided. Everything in the
Consequences block below is read off it, labelled as a consequence, and rests on the stated premise
rather than on a measurement. Nothing here is a finding about a market, and no artefact may cite it
as one.

**Consequences.** Class D: a mechanism with no measurement behind it, conditional on app custody
continuing to hold.

- **The side-payment bypass does not apply while the tickets stay in app custody.** D6 named that
  hole and named it correctly for a design in which buyer and seller settle between themselves:
  declare a face-value price on the record, pay the difference in cash or anywhere else, and the
  chain bounds the record and not the money. Under custody there is no user-to-user channel inside
  the product and no transfer the platform does not sign, so the declared price is the only price
  the product can express. That is a statement about the product's own surface, not about two people
  who already know each other outside it, and it lapses the moment a ticket can leave.
- **The chain's role is then commitment and verifiability, not stopping a rogue user.** With the
  platform signing every move, the on-chain cap is no longer the thing that stops a determined
  seller; it becomes three other things, and `README.md` §"Why the chain" states them: the rule binds
  the platform as well, because no instruction raises a cap and the promise therefore cannot be
  quietly withdrawn; the sale record is public and cannot be rewritten afterwards, which is what the
  pricing engine reads and what a monitor-only mode would read; and any reader can check all of it
  without trusting the operator. This decision is why those three are the ones that carry weight.
- **"It still holds if the ticket leaves the app" applies only if the ticket can leave.** The
  argument survives withdrawal in one sense and not in another, and the two should not be run
  together. It survives because the cap check lives in the mint and travels with the token. It does
  not survive because the no-user-channel premise is then false, so D6's side-payment hole returns in
  full. Whether tickets are ever withdrawable is open (O1), so this line is written as conditional and
  must stay conditional until someone closes O1.
- **Custody makes the platform the signer, so the key-management and trust model has to be written
  down.** Every transfer is signed by the platform, which makes the platform's key the thing that
  moves a ticket. A document has to say who holds it, what a compromise of it allows and what it does
  not, how it is rotated, and how that compares with a design where the holder signs. It does not
  exist yet. `docs/ON-CHAIN-DESIGN.md` §4.2 covers the organizer and `verifier` keys of the design,
  not the custodian, so until that document is written what the platform can do with its own key is
  described nowhere.

**Open questions.** Both are the operator's.

- **O1 — Are tickets ever withdrawable to a user's own wallet?** This decides which sentence the
  product may carry. If yes, the side-payment hole is back and the honest claim narrows to "the chain
  bounds the record, not the money". If no, custody is a standing premise of the product and belongs
  in the design, not in a paragraph of a decision log. Nothing in the tree answers it today.
- **O2 — What exactly does the platform's signing key control, and who can use it?** One key or a
  multisig, under whose authority, rotated how, and what an outage of it costs. This is the same
  question D6 asks of the organizer key (`docs/ON-CHAIN-DESIGN.md` §4.2.3); custody adds the platform
  itself to the list of keys that need an answer.

**Rejected alternative.** Keeping the chain as the enforcement mechanism and treating custody as an
implementation detail. Rejected because the two give different sentences about the same product: with
custody, the load-bearing claim is a promise that binds the operator and can be checked, and the
"a seller cannot bypass the cap" claim rests on there being no channel to bypass it with. Writing the
second while doing the first would claim the stronger thing on the weaker reason.

## Q4 — A region-aware cap: monitor where resale is legal, enforce on chain where it is capped (direction decided 2026-11-08 by D11; the mapping is open, see D16)

**Status changed on 2026-11-08, and one part of it is still open.** This question was open with nothing designed and nothing built.
It is now decided by **D11** and built: the design is `records/REGION-CAPS-DESIGN.md`, the law is
`records/findings/33-a-region-cap-law.md`, the table is `ticketpath/data/region-caps.json` and the
resolver is `ticketpath/core/region_caps.py`. The three questions at the bottom of this entry are
answered where D11 answers them and marked as still open where it does not. The text below is kept
as it was written, because the reasoning that framed the question is still the reasoning that
constrains the answer.

Recorded here because the direction was named; when this was written, **nothing was decided and
nothing was built.**

**What is decided, and what is not, in one sentence (added 2026-11-08T08:20Z).** The direction is
decided by D11 for the region-cap work (a dated rules table and a policy field, with a local-only
gate program); the mapping from a jurisdiction to a policy is **not** built in this program, which
records the code and does not interpret it (D16). The record's `[u8; 2]` can name a nation and not a
subdivision, and 72 of the table's 82 codes are subdivisions, so any reconciliation is nation-level
only.

The idea: one rule for the whole platform is the wrong shape if resale law differs by jurisdiction.
Where resale above face is restricted, enforce the cap on chain as D6 does. Where it is lawful, do
not cap, and use the public record as monitoring instead of control. That is the same record point 2
of `README.md` §"Why the chain" describes.

What this file does **not** establish: which jurisdictions restrict resale above face, at what
number, or whether a platform rule may vary by event at all. That is a legal question for the
operator, not a research finding, and no claim about it appears anywhere in this tree.

**Open questions, all the operator's.**

- **At what level does the cap bind where it binds: face, or face plus a margin?** Zero basis points
  is a ban on selling above face, which refuses a resale that merely covers a fee and is a different
  product from a markup ceiling. Any margin is a per-event policy number, and it is the `c` that
  D7's split instrument divides with.
- **What does "monitored" show on a screen?** A monitored event has no cap to display, so the choice
  is between nothing, a badge saying resale is unregulated here, and the observed markup shown as
  data. The third is the useful one and the one that can read as an accusation of the organizer, so
  whoever designs the screen has to pick deliberately rather than by default.
- **How does an event get its jurisdiction?** It has to be a per-event setting, set before sale and
  recorded where the cap is recorded now. And a transfer carries an amount and no price, so a
  region-varying rule needs the region written somewhere the hook can read; there is no such field in
  the record today (`records/STATE-OF-PROJECT.md` §E). Until there is, the cap stays one number per
  ticket record, and a monitored event simply has no cap.

## D10 — The memo program id is a per-cluster fact, measured not assumed (2026-11-08)

**Decision.** The program id a quote's memo runs on is looked up per cluster, from a table of
measured ids, and never held as one constant for the repository. `devnet` resolves to
`Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, measured from the proven memo transaction;
`mainnet-beta` and `localnet` resolve to the `solana` CLI's shipped memo program,
`MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`. A cluster with no entry raises `UnknownCluster`;
there is no default and no fallback. The publish path asserts the id in the transaction the
cluster actually landed against the table's id for the run's cluster, on the reuse path and the

**Corrected 2026-11-08T08:20Z: three statements in the paragraph above are false against the code,
and `mainnet-beta` is not in the table.** Measured with `python3 -c "from ticketpath.adapters
import chain_client as c; ..."`: `devnet` and `localnet` both resolve to
`Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH` (the installed CLI was measured building that id, so
the localnet row is measured, not the CLI's documented one); `mainnet-beta` and `testnet` are
**absent** and `memo_program_id` raises `UnknownCluster` for either; and the **cluster argument**
defaults to devnet when `None` is passed, while the **id** has no default and no fallback. The two
literals stay in the file because documents quote them and the `ids` gate compares against them, but
neither is a mapping for mainnet. The sentence above is kept as the record of what D10 said before
the correction.
fresh-send path alike.

**Evidence.** `records/findings/40-memo-program-id.md` §2. One `getTransaction` against
`https://api.devnet.solana.com` at 2026-11-08T05:39:47Z for the proven memo transaction, whose
quoted account keys end:

```
"accountKeys":["75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy","2k1PvrHrue11in9kmwV9gjhLtFMVM8ndHSFiscV79GVd","11111111111111111111111111111111","Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"]
```

Its memo instruction carries `"programIdIndex":3`, and the logs quote
`Program Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH invoke [1]`. A second read showed devnet also
hosts the CLI's id as an executable program, which is why the old constant never failed a
transaction and only misdirected every record and the console's `memoProgram`. The devnet id is
class **A**; mainnet's is class **D**, the CLI's shipped id, not measured from mainnet.

**Consequence.** Three things follow, and each is a place the old constant could mislead again:
an unknown cluster raises rather than borrowing a neighbouring id, so `testnet` is refused until
someone measures it; the console's `memoProgram` field may be `null` when the server's cluster has
no measured id, which is a statement rather than a lie the page cannot detect; and the artefact
records the id a run actually resolved, additively, so a record written before the field existed
still verifies and an older observation is read back unchanged instead of being overwritten by
today's table. `tests/test_onchain_sim.py` and `tests/test_devnet_publish.py` exercise each of
the three, including the mismatch that stops a run.

**Rejected alternative.** Keep one constant and add a comment naming devnet's id. Rejected
because the constant is what every reader, the console field and the local validator's `--clone`
read, and a comment cannot stop any of them: the defect was not a bad string but a claim nobody
checked, so the fix has to be a table plus a read-back of the landed transaction.

## D11 — A region-aware cap is a deterministic table plus a policy field, not a model (2026-11-08)

**Decision (the operator's direction, this session's build).** One rule for the whole platform is
the wrong shape when resale law differs by jurisdiction. The platform resolves each event to one of
three policies from a table of instruments, and the chain stores the outcome:

| policy | when | chain |
|---|---|---|
| `capped` | a law in force restricts resale above a limit | the hook refuses a staged price above the limit |
| `monitored` | a law in force establishes no price limit | the hook admits and logs the jurisdiction and the price |
| `unresolved` | the law could not be established from a primary source | the hook admits and logs `unresolved`; the event may not claim lawfulness |

**What is new, in six sentences.** The table is JSON (`ticketpath/data/region-caps.json`, version
`2026-11-08.1`, 25 jurisdiction codes and 33 instruments) with one row per instrument, not per
jurisdiction, because a jurisdiction can have an in-force disclosure duty and an announced price
cap at the same time. `announced_policy` is a first-class instrument kind and never binds. The
resolver is a pure function of (jurisdictions, date, table): no network, no clock, no model. The cap
base is part of the law, so the table distinguishes face, face + fees, face + fees-capped-at-a-share,
a percentage, and a fixed money amount. A fixed amount is never approximated into basis points: it
resolves to `unresolved` unless an FX snapshot with a source and a timestamp is supplied. And a
ticket's policy can only ever tighten on chain, never loosen.

**Corrected 2026-11-08T08:20Z: the counts in the first sentence above are wrong.** Measured against
`ticketpath/data/region-caps.json` (version `2026-11-08.1`, and the file's own `compiled_at`): **82
entry codes and 84 instruments**, not 25 and 33. The instrument kinds are 21 `primary_legislation`, 2
`secondary_legislation`, 1 `announced_policy` and 60 `none_identified`; 72 of the 82 codes are
subdivisions (`CA-ON`, `AU-NSW`, `US-CA`) and 10 are nations. `README.md` and
`records/STATE-OF-PROJECT.md` already carried 82 and 84; this entry was the odd one out. The rest of
the paragraph is unchanged and still true of the file.

**Evidence.** `records/findings/33-a-region-cap-law.md` and its five cluster records, every row
carrying the instrument, the quoted provision, the dates and a confidence grade. Two premises the
brief supplied were checked and were wrong: the United Kingdom's cap is announced policy and not law
(19 November 2025), and New South Wales is not a flat 10% (it is face + the fees paid, counted at no
more than 10% of face). Both corrections are recorded in the finding rather than quietly dropped.
The on-chain half is verified on a **local validator**: `tools/region_local_proof.py`, eleven legs,
PASS 11/11, real transactions with real refusals (`records/findings/34-region-caps-build.md`).

**Consequences.** Class A for the instrument texts and the local-validator behaviour; **Class E for
every jurisdiction the table marks unknown**, which is most of the world: those events resolve to
`unresolved` and the platform makes no claim about them. The devnet program `5EJ1GU3M4vn…` is
untouched by this decision; the region gate is a separate, local-only crate
(`programs/region_gate/`) because a second program was being written in `programs/cap_hook/` at the
same time (see that crate's §12 collision record). The platform's own configured cap and the law's
cap are combined in lamports, and the stricter one is what the chain holds; the event record names
which rule produced it.

**Rejected alternatives.** (1) An LLM prompt over a description of the law: not reproducible, not
diffable, and a hallucinated citation in a legal rule is worse than no rule. (2) One global cap:
the question this decision answers. (3) Comparing basis points across bases: 500 bps over face +
fees is looser than 1000 bps over face, so the comparison is done in lamports. (4) Failing open on
an unknown jurisdiction and calling it `monitored`: that would report "resale is unrestricted" on
the strength of not having looked. (5) Letting the chain loosen a cap when a law is repealed: the
chain cannot tell a repeal from an organiser's convenience, and the gaming hole D6 closes would
reopen.

**Open, and the operator's to answer.** Whether a mid-event tightening binds tickets already sold
(the design makes it possible, is silent on whether it is right); whether the platform may be
stricter than the law (it can, and the record says which rule bound); which jurisdiction applies to
a cross-border resale (venue, buyer residence or seller establishment — the resolver does not
choose); and whether `programs/region_gate/` is retired once the v2 program carries `policy = 2` and
`TightenPolicy`, which are the two additive pieces it needs.

---

**Numbering note, 2026-11-08.** The ten-feature build's documentation pass was briefed to number its
seven decisions D11 to D17. D11 is already the region-aware cap decision above, and a second `## D11`
would make every `D11` in the tree ambiguous, so the seven are appended here as **D12 to D18**, in the
order the brief gave them: the console's recorded-quote rule is D12, the v2 program id is D13, the band
feed and forecast log are D14, the fee policy and the two blocked features are D15, jurisdiction is
D16, the live agent adapter is D17, and the documentation gate is D18.

## D12: The console renders a recorded quote as recorded, and says separately whether it is the quote on screen (2026-11-08)

**Decision.** The `[DEVNET]` block renders the artefact's own fields under `chain.recorded`: its
`asOf`, slot, block time, signature, mint, program, memo program, recommended lamports, both transfer
legs and the refusal's error. The page always prints the recorded instant and slot. A second, separate
fact, `chain.matchesCurrentQuote`, says whether the number the page computed for its own instant is
the number the chain recorded, and the page prints one of two sentences accordingly. `chain.state`
answers only "did the file verify", and the three states stay distinct: verified, unverified with a
named reason, absent.

**Evidence.** Measured in this pass through `tools/guidance.py` and the page renderer. At the
artefact's own instant, `evt_syn_02` at `2026-11-07T18:34:29.183Z`: `state verified`,
`matchesCurrentQuote True`, and the page prints "The number on this page is the quote the chain
recorded." At `evt_syn_04` at `2026-11-07T18:00:00Z`: `state verified`, `matchesCurrentQuote False`,
and the page prints "The number on this page is computed now and is not the number the chain
recorded; the recorded quote is for 2026-11-07T18:34:29.183Z." The recorded block also carries
`checkedAt` and `checkerVersion`, so the page now prints "The file verified at 2026-11-08T00:50:25.281Z
with checker devnet-publish-2026-11-07" instead of the `Verified at None` defect A6 recorded.
`tests/test_console_recorded_artefact.py` (19 tests) and 17 new `tools/console-check.py` cases pin it.

**Corrected 2026-11-08T07:55Z: two sentences above are wrong against the console as it now stands,
and one is a quotation of a sentence that no longer exists.** (1) The agreement sentence is about
the quote, not the number: it names both quote ids and both instants, and it is printed as either
"The quote this page commits is the quote the file records: quote id …, taken at …" or "This page
commits … for …; the file records … for …". (2) The two recommendations are a separate sentence and
both numbers are printed only where they differ: "The recorded recommendation is …, and this page
recommends the same number", or both numbers when they differ. On the shipped record the two numbers
are the same (1,380,000,000), which is why the old sentence was false. (3) The verification line now
reads "The file verified. The checker wrote 2026-11-08T00:50:25.281Z with checker
devnet-publish-2026-11-07", with no `[DEVNET]` badge on the timestamp, because `checkedAt` is the
checker's clock and not a chain fact. Also: `[DEVNET]` marks only the six fields the quote hash
covers, every other value is printed under "The file states, and the quote hash does not cover", the
evidence count is **3 on-chain transactions**, the absent sentence is about the console's file, and
the explorer link is rendered only for an `https` URL on `explorer.solana.com`. The test file is now
20 tests. Measured by rendering `page.chain_slot` from `tools/guidance.py`'s payload at 07:50Z.

**Consequence.** A proven devnet transaction is visible on every page instead of on exactly one, and
a page whose instant differs from the recorded one says so rather than downgrading the artefact to
absent. `rpc_adapter.program_status` keeps `programDeployed: false` with `askedCluster: false` and
carries the recorded program id in its own block with its source, so the page never claims a
deployment it read from the chain.

**Rejected alternative.** Showing the live recommendation as the chain's number, which is the defect
this decision removes: two facts with different instants were being rendered as one. And hiding a
verified artefact whenever the page's `asOf` moved, which made the chain work invisible to any reader
who changed the instant.

## D13: Program v2 is a new program id, deployed to a local validator only (2026-11-08)

**Decision.** The v2 instruction set is a new program: a new deploy keypair, a new program id
(`CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`), new mints and a fresh local ledger. The devnet
program `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva` and `records/devnet-artefacts.json` are frozen
evidence: no upgrade, no re-sign, no edit, ever.

**Evidence.** The local run's record, `records/onchain-v2.local.json` (git-ignored), written
2026-11-08T06:48:48.836Z: `programId CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`,
`cluster localnet`, `localOnly true`, and both phases deployed that same `.so` (sha256
`0b6174344329f1a60e079572fcb43bbc59250470a398c788a32a7e66a8fa16c7`). The devnet id in
`records/devnet-artefacts.json` is unchanged.

**Corrected 2026-11-08T07:55Z: the run was rebuilt and the hash above is superseded.** The v2
program was rebuilt after `records/findings/37-program-v2-review-fixes.md` and both builders produced
the same output twice: **111,504 bytes, sha256
`de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac`**. The artefact was regenerated by
the same run (`writtenAt` in the current file), its phase one now carries proofs `a` to `g` and its
phase two carries thirteen tag 4..6 proofs, and its forecast is forward-dated to
`as_of_unix 1794123175`, 117 s ahead of the block time that created it. `0b617434…` is the hash of
the program this decision first shipped and is kept above as what the record said at the time. The
devnet id and `records/devnet-artefacts.json` are still unchanged, which is the point of the decision.

**Consequence.** Two programs on two clusters, and a reader has to know which one they are reading.
The devnet deployment has four instruction tags and no floor, jurisdiction or policy byte; the local
v2 has seven tags and the three new fields. `docs/ON-CHAIN-DESIGN.md` §0 states the difference in the
same table as the instruction set, so a reader cannot take the table for a description of devnet.

**Rejected alternative.** Upgrading the proven devnet program in place. It would have re-signed and
rewritten the artefact the whole devnet proof rests on, to add features the proof does not need, and
the old boundary could never be re-verified against the bytes that proved it.

**Corrected 2026-11-08T11:20Z: v2 has since been deployed on devnet too, under a third program id.**
The title and the Consequence above say v2 is a local-validator program and that there are two
programs on two clusters. Both statements were true when written; the second is now false because
v2 was also published on devnet under `Bebo55oe…`, whose full value and whose 35 transaction rows,
14 refusals included, are in `records/onchain-v2-devnet.json`. Nothing this decision decided has
changed: the v1 devnet program `5EJ1GU3M4vn…` is still frozen, `records/onchain-v2.local.json` is
still the local run's record, and the instruction-set difference the Consequence turns on still
holds: v2 is seven tags and v1 is four. `docs/ON-CHAIN-DESIGN.md` carries the deploy in its two
programs paragraph with the numbers read from that record.

## D14: The band feed is a rewritable head, the forecast log is the immutable history, and a score is a separate account (2026-11-08)

**Decision.** `PublishBand` (tag 4) writes `["band", mint]`, rewritable on purpose: low, high,
`as_of_slot`, `published_slot`, `sample_n`, `refused`, `model_hash`, `authority`. `LogForecast` (tag
5) creates `["forecast", mint, as_of_unix]` once (`6024` on a second write). `ScoreForecast` (tag 6)
creates `["score", forecast]` once (`6025`), and writes nothing into the forecast it scores.

**Evidence.** The local run: band at address `4V4hkMn…` read back with `low 900000000`,
`high 1100000000`, `as_of_slot 10`, `published_slot 12`, `sample_n 42`, `refused 0`; a forecast at
`as_of_unix 1760000000` carrying `scoring_rule_hash bb9ddc66…`; a second `LogForecast` for the same
instant refused `6024` with the forecast account's sha256 identical before and after
(`78752fd0…952`); a score written with `interval_score_micro 200000000000000` and `covered 1` and the
forecast's sha256 unchanged again; a second score refused `6025`; a band signed by a non-authority
refused `6026` with the band's bytes unchanged. `tests/test_onchain_v2.py` pins the layouts and the
address derivation.

**Consequence.** A consumer reads the head and inherits the uncertainty fields with it; a reader who
wants the history reads the forecast log, which cannot be revised. The feed's composability is
unproven, because no third-party program consumes it today, and `refused` is stored rather than
enforced.

**Rejected alternative.** One mutable account holding the band and the scores. A score that can be
rewritten is not a score, and a history that can be overwritten cannot answer what was believed at a
past instant.

## D15: The fee policy is a property of the mint, and features 5 and 7 are blocked because Token-2022 ceils a fee on an indivisible ticket (2026-11-08)

**Decision.** No fee instruction ships. The artist fee (feature 5) and the flip tax (feature 7) are
recorded in every table as **not built, blocked**, with the measurement that blocks them, and the
three surviving alternatives are put to the operator as an open question (Q5) with no recommendation.

**Evidence.** `records/findings/36-transfer-fee-on-a-one-unit-ticket.md`, measured on four throw-away
local validators, quoted RPC objects and all. Token-2022 ceils the fee: at `decimals 0` and `amount
1`, 500 bps and 1500 bps both leave `withheldAmount = 1` and the recipient 0; ten units at 1500 bps
withhold 2, not 1, which is the ceiling; at `decimals 9` and 10^9 base units the fee is exactly
150,000,000. The only fees this mint can express are 0 and the whole ticket. Also measured there: on
a mint carrying both a `TransferFeeConfig` and the transfer hook, `WithdrawWithheldTokensFromAccounts`
succeeds without the hook's accounts and does not invoke the hook.

**Consequence.** `TicketRecord.held_since_unix` is written by the hook on every admitted transfer and
nothing consumes it; `ClaimRebate` (tag 7) is not implemented; the two error names reserved for it,
`6027` and `6028`, are declared in `error.rs` and raised by no instruction. The pool and rebate
plumbing is viable and the rate is not. This is a decision to ship no fee, not a decision that the
product should have none.

**Rejected alternative.** Turning the fee on at a small basis-point value. At 500 bps it withholds the
whole ticket and leaves the buyer with nothing, which is a seizure, not a fee. And giving both fees
one mint: Token-2022 carries one `TransferFeeConfig` per mint, so that is not a choice the mechanism
offers.

## D16: Jurisdiction is a recorded field, not an encoded legal mapping (2026-11-08)

**Decision.** `TicketRecord.jurisdiction` is `[u8; 2]`, an ISO-3166-1 alpha-2 code in uppercase, with
`ZZ` for unspecified, and `TicketRecord.policy` is `0` (capped) or `1` (monitored). The program logs
the jurisdiction on every admitted transfer and skips both price predicates when the policy is
monitored. The program does not interpret the code, does not validate it, and does not map a
jurisdiction to a policy.

**Evidence.** `programs/cap_hook/src/state.rs`, whose comment on the field says a wrong code is a
wrong statement by the issuer and there is no list on chain to check it against. The local run
initialised a record with `jurisdiction ZZ`, `policy 0`, admitted a transfer at the floor with
`jurisdiction=ZZ` in the log line, and refused `policy 2` with `6023`. `tests/test_onchain_v2.py`
pins the two-byte encoding and the decoder.

**Consequence.** The mapping from a jurisdiction to a policy is off chain, in the rules table D11
describes, and **the two must not be read as one decision: D11 decides the direction for the
region-cap work; this entry says that the mapping is not built into `cap_hook` at all.** Neither of
the record's two bytes is on the wire contract; the event-level `jurisdiction` and `resalePolicy`
keys that D11's work serves are a different pair at a different level, and no sentence in this tree
claims any jurisdiction's law applies to a ticket record. **The record is `[u8; 2]`, so it can name a
nation and not a subdivision:** 72 of the table's 82 codes are subdivisions (`CA-ON`, `AU-NSW`,
`US-CA`), so any reconciliation between the record and the table is nation-level only, and the finer
mapping has nowhere to be written on the v2 record.

**Rejected alternative.** Mapping the code to a policy inside the program. That puts a legal table in
a program that cannot be amended when a law changes, and it makes a refusal on chain look like a
legal conclusion the chain cannot draw.

## D17: The live agent adapter is opt-in, capped per decision and in total, and the scripted policies remain the default (2026-11-08)

**Decision.** `market_swarm/forge_policy.py` is off unless `MARKET_SWARM_LIVE_LLM=1`. A decision
reserves `min(per-decision cap, remaining total)` before a child exists; the charge is the observed
usage afterwards; an overrun is recorded and refuses every later decision. `timeout_seconds` is
mandatory, and no child is spawned without one. The scripted policies stay the default path, so a
dataset is produced only by a live run if an operator asks for one.

**Evidence.** `records/findings/41-deepseek-live-adapter.md` and its appended review section. One live
decision: 22,838 in, 157 out, 4,096 cache-read, `$0.003532`, 4.2 s, a parsed `Intent`. Four children in
the feature, `$0.011581380` total, cross-checked against the CLI's own usage log for those four. The
same file records the correction that matters: the cap is parent-side, and the usage log writes no row
for a `--no-extensions` child.

**Consequence.** A leaked child is possible if the parent is SIGKILLed, and the spend ledger is the
child's own session file for the hardened path. Neither is a reason to run it by default; both are
reasons the live path is a flag and the budget is reserved before the spawn.

**Rejected alternative.** A default-on live path, which would spend money on a plain test run. And a
cap checked after the charge, which is not a cap: the money is already gone.

## Q5: How is a fee on resale charged, given that Token-2022 can only take the whole ticket? (open, 2026-11-08)

Opened by D15. Three alternatives were measured or derived in
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md` §5, and none is recommended here:

1. **A lamport fee at the venue.** Take a basis-point share of the staged price in the same
   transaction that stages it. Exact percentages are expressible because the fee is on the price and
   not on the token amount. It binds only transfers that go through the program, and a marketplace
   that does not know about us can ignore it. Not tested.
2. **A recorded obligation settled off chain.** Record the price and the fee owed in a PDA and
   collect at checkout or by invoice. The cheapest on-chain option and the weakest guarantee: an
   attestation, not an enforcement.
3. **A divisible mint.** Give the ticket, say, 10^6 base units and keep `amount == TICKET_UNITS` in
   the hook so a ticket still moves as one object. Then 500 bps withholds 5% of the ticket instead of
   all of it. It changes every consumer of `decimals 0`, and 5% of a ticket is still not 5% of a
   price unless a fractional ticket can be sold for its pro-rata value.

The operator's to answer. Nothing is built for any of the three, and this log recommends none.

**Corrected 2026-11-08T08:00Z: two of the three alternatives above do not work as written.** An
independent review (`tmp/review/fee-mechanism.md`, read-only, did not build the finding) reproduced
the fee ceiling and then found two mechanism errors in finding 36's §5. Both are recorded here because
this question is what a reader would act on:

1. **A lamport fee cannot be taken from the buyer, who never signs.** A Token-2022 `TransferChecked`
   is signed by the source account's owner or delegate, which is the **seller**; the hook receives
   `[source, mint, destination, authority]` and `authority` is the seller's key. The fee has to come
   from the seller, by a `system_program::transfer` CPI out of the `authority` account the hook already
   receives, with the artist's or the pool's wallet added through the extra-account-metas list. Two
   consequences follow: the seller must hold the lamports at transfer time, and the fee is charged on
   the staged number in the record, not on lamports that actually moved. That makes the option more
   feasible than finding 36 says, not less.
2. **A divisible mint does not make the buyer whole.** Token-2022 calls the hook with the **pre-fee**
   amount and credits the destination `amount - fee`, so a transfer of `TICKET_UNITS` leaves the buyer
   with 950,000 of a 1,000,000-unit ticket at 500 bps and 850,000 at 1,500 bps. To deliver a whole
   ticket the seller must send `calculate_pre_fee_amount(TICKET_UNITS)` (1,052,632 at 500 bps,
   1,176,471 at 1,500 bps), which is not `TICKET_UNITS`, so the proposed `amount == TICKET_UNITS`
   check refuses the only transfer that would work. The hook's check would have to move to the net
   amount, which it cannot compute without unpacking the mint's live fee schedule, or be replaced by
   a per-holder balance check.
3. The third alternative, a recorded obligation settled off chain, stands as written, with one
   correction of detail: the record carries `pending_price_lamports`, not a hop count, so a hop count
   would have to be added to it. Finding 36's §3.3 detector is also weaker than stated (the withdraw
   path has no account slot for hook accounts at all), though its conclusion is right. None of these
   corrections changes the ceiling measurement or the decision that features 5 and 7 are blocked.

## Q6: What has to be decided before the imported frontend is published? (open, 2026-11-08)

1. **The author on the commit.** `--author` is a person, and this pass does not choose one. The
   import is staged and the commit command is in the handover to the operator.

   **[Corrected 2026-11-08T12:00Z: the import is committed, as `009f103` on `release/prep` at
   11:39:41Z (`git log -1 --format='%h %ci %s' 009f103`), and it is not in the index. The item above
   was true when it was written and is kept for that reason. The author question it raises is closed:
   the author and the committer are the contributor whose checkout it came from, and the same person
   on every commit on the branch.]**
2. **The demo copy's second pass.** `frontend/NOTES.md` lists nine sentences that ship as written
   and overclaim: a payment flow, a wallet the platform creates, a contract that rejects every
   above-face resale, a door code that works without signal, and three proof-band figures. The
   landing page's argument is that it does not overclaim, so this is the one open item that a
   reader meets on the first screen. It is the operator's call whether that list is edited before
   the import is published or after it.

   **[Corrected 2026-11-08T12:00Z: the table at `frontend/NOTES.md:23-32` has eight body rows, not
   nine. The eight are two payment/issue sentences, the cap sentence, two door-code sentences and the
   three proof-band figures, so the sentence's own summary already counts eight and the word "nine"
   was the arithmetic slip. Measure it with `awk 'NR>=24 && NR<=31' frontend/NOTES.md | grep -c
   '^|'` rather than trusting either number.]**
3. **The two Stitch exports.** `frontend/VERIFY.md` 8.7 could not be run: the export files were
   never on this machine, so the visual comparison was made against the written specification
   only. Landing `desktop.html` and `mobile.html` in `../seatpass-exports/` makes that check
   runnable.
4. **The `/tmp` exception in `.public-denylist`.** It is one glob and one class, and it exists so
   the frontend's records stay verbatim. The alternative is rewording two documents that are the
   evidence for the checks they describe. If the operator prefers no new exception, the wording
   can change instead and the exception can go.

## D18: The documentation gate runs in the commit gate, and a documentation-only change runs it too (2026-11-08)

**Decision.** `tools/doc_check.py` is a gate and not a report: it exits 1 on any violation, and
`tools/tp.py gate` runs it beside the tests and the console checks. A change that touches only
documents runs it as well, because a stale claim is a defect a reader acts on and the pass that
writes prose is the pass most likely to create one. A path that is deliberately absent from the tree
is written down once, per path, with a reason, in `ALLOWED_ABSENCES`; an entry with no reason
suppresses nothing and is itself a violation.

**Evidence.** Seven checks, each a claim that can be false: every repo path a document names exists; a
finding, section or decision reference resolves; the memo program ids and the devnet program id and
mint quoted are the code's and the artefact's; the program's error numbers, instruction tags and PDA
seeds equal the `IMPLEMENTED TODAY` table in `docs/ON-CHAIN-DESIGN.md` both ways; a registry that
states a count of its own rows is right; and every row of the feature table carries a status from the
closed set and names a file that exists.

**[Corrected 2026-11-08T12:00Z: there are seven checks, and the sentence above read `Six checks`.
The list that follows it names six of the seven; the one it omits is `findings-unique`, which refuses
two findings with the same number and no letter.
`grep -n '^CHECKS' -A 8 tools/doc_check.py` prints `paths`, `cross-references`, `findings-unique`,
`ids`, `program-vs-doc`, `registry-counts`, `feature-table`; `docs/DOC-CHECK.md` tabulates the same
seven, and `python3 tools/doc_check.py --root .` reports `clean, 7 check(s)`. The count is corrected to
seven; the sentence's list is left as it stood, so the number and the list disagree by one until
someone adds the missing clause.]**
states a count of its own rows is right; and every row of the feature table carries a status from the
closed set and names a file that exists. This pass's final run: `python3 tools/tp.py doc-check` →
`doc_check: clean, 6 check(s), <repo root>; 21 allowed absence(s) suppressed by
ALLOWED_ABSENCES`, exit 0, with the root path elided.

**Consequence.** The gate caught two real things in this pass and they are worth naming because each
is the kind of error prose creates: `records/A-research-ledger.md` cited a findings *directory* as a
path, which the checker reads as a claim that a `.md` file of that name exists, and the
`IMPLEMENTED TODAY` table had to be re-read when the program gained five error codes and changed a
signer requirement while this pass was running. The table is the truth about the code or the gate
says so, which is the whole point.

**Rejected alternative.** A checker that reads prose and judges whether it is true. It cannot, and a
checker that guessed would fail on correct sentences until someone switched it off. The six checks
are exactly the claims a program can refute.

**A red that arrived after that run, and cleared, named.** At 07:27Z the same command reported two
violations, both on `programs/cap_hook/README.md:18`, which cited a finding file that did not exist yet.
That is a code-owned file and an unwritten finding, not a claim this pass wrote, and the gate stayed
green on every document this entry's pass touched. The finding was written at 07:30Z and the gate read
`doc_check: clean, 6 check(s), 21 allowed absence(s) suppressed`, exit 0. Recorded rather than fixed,
because the fix was an edit to a file this pass does not own.

**A limit stated, and the limit is gone (corrected 2026-11-08T08:20Z).** This paragraph used to say the
feature-table check required a `tested` row to name a file under the root `tests/` directory, that a
package with its own suite could not make a row `tested`, and that feature 9 was therefore recorded as
`built`. The checker has since widened: `tools/doc_check.py`'s `TEST_DIRS` is
`("tests", "market_swarm/tests")`, and a `tested` row may name either root. Feature 9 is `tested` in
`records/STATE-OF-PROJECT.md` with `market_swarm/tests/test_feature9_fixes.py` and `test_forge_policy.py`
named, which is the row the evidence supports. The old paragraph is kept in this note because it was
published in this log's first edition.

## D19: The frontend is imported into this tree from its own checkout, with its records and its checks (2026-11-08)

**Decision.** Take the platform's Next.js frontend into `frontend/` as a copy of its own git tree,
file for file from `git ls-files`: 81 of its 82 tracked files, `.env.example` the one left out
because the import excluded `.env*` by name and every variable it listed is documented in
`README.md` instead. Keep the things that make it checkable rather than only present: its records
(`NOTES.md`, `VERIFY.md`, `DECISIONS.md`, `COVERAGE.md`, `API_CONTRACT.md`), its `package.json` and
lock, its lint, typecheck and test scripts, and its `tools/`. Replace the machine handles in those
tools with environment variables, so the scripts run from the new path on a machine that is not
this one.

**Evidence, all measured in `frontend/` in this worktree on 2026-11-08.**

- `git ls-files` in the source checkout names 82 files; 81 were copied and the list was diffed
  against the copy: identical. Total 1,093,317 bytes (1.04 MB) as copied, 1,097,001 as staged after this pass's
redaction notes; nothing was over 1 MB, so nothing
  was dropped for size. Largest file `package-lock.json` at 522,393 bytes, kept because a clone
  that cannot reproduce the dependency set is not the app that was verified.
- The app's own checks, run from the new path in a throwaway copy under the system temp dir with
  `node_modules` symlinked to the builder's install, never installed into this tree:
  `npm run typecheck` exit 0; `npm run lint` exit 0 with no warnings; `npm test` →
  `tests 15, pass 15, fail 0`; `bash tools/greps.sh` → `8.5 GREPS: ALL ZERO`;
  `node tools/contrast.mjs` → `28 pairs, 0 below 4.5:1`. `npm run build` was not run.
- `python3 tools/public_safety.py check --staged` → `clean, staged, 82 file(s)`, exit 0, over the
  copy plus this pass's edits. `python3 tools/public_safety.py check --tracked` →
  `clean, tracked tree, 366 file(s)`, exit 0.

  **[Corrected 2026-11-08T12:00Z: the tracked-tree reading is 394 file(s) at `HEAD 3ad15bb`, by
  `python3 tools/public_safety.py check --tracked`. The 366 above is a reading taken on this pass's
  index and is kept with that date on it; it is not the current size of the tree, and neither is the
  367 in `records/PUSH-PLAN.md` or the 285 in §A1 and §A6, which belongs to `HEAD 948b5d5`. The
  command is the thing that produces the number, so run it rather than quoting any of the four.]**
- `python3 tools/doc_check.py` → `clean, 7 check(s), ... 24 allowed absence(s) suppressed`, exit 0.

**[Corrected 2026-11-08T11:30Z: the exclusion above no longer holds of the index. `git ls-files
frontend | wc -l` → 82 and the byte total `git ls-files frontend | xargs -d '\n' du -cb` →
1,097,690, because `frontend/.env.example` (689 bytes) was staged by another pass at 11:18Z.
This entry's Decision says 81 of 82 files with `.env.example` left out, and that is now a
description of what the import did, not of what the tree carries. The file holds four
`NEXT_PUBLIC_*` names with empty values and no secret, and `public_safety.py check --staged`
is clean over it. What this decision decided about the other 81 files is unchanged.]**

**What had to change to publish it, and why each change is not cosmetic.** The frontend was built
in a checkout of its own and its tooling named this machine. `frontend/tools/build-copy.sh` had its
source and destination as absolute paths and `frontend/tools/verify-landing.cjs` required a
`playwright-core` and a
Chrome binary by absolute path; both now take `SEATPASS_SRC`, `SEATPASS_BUILD_DIR`,
`SEATPASS_PLAYWRIGHT_CORE` and `SEATPASS_CHROME`, with the checkout and the installed package as
the defaults. The absolute paths under a home directory in `NOTES.md` and `VERIFY.md` became
relative (`../seatpass-exports/`, `cd ..`) or named variables (`$SHOT`), and the screenshot helper
and the vision-helper directory are described without a path. The port another session's dev
server holds is gone from the prose that described it; the warning that made the sentence worth
having is intact. `frontend/NOTES.md` carries the same list for a reader of the app rather than of
this log.

**One exception bought, named.** `frontend/VERIFY.md` and `frontend/DECISIONS.md` quote `/tmp`
paths, because they are the record of the commands the build ran and a quote is evidence, not an
instruction. `.public-denylist` gained one line for it, `allow frontend/*.md tmp-path`, one glob
wide and one class wide, with `tests/test_public_safety.py` proving both directions: a `/tmp` quote
in the frontend's markdown is clean, and a `/tmp` literal in `frontend/tools/build-copy.sh` still
fails. Nothing else is exempt.

**The documentation gate had to learn where the frontend is.** `tools/doc_check.py`'s check 1
resolved every backticked path at the repository root, and its comment said the closed top-level
set was what kept the frontend out of the check. That was true while the frontend was outside the
tree; with the app inside it, eleven frontend documents naming their own build-copy and
render-check scripts were reported missing, because those files exist under `frontend/tools/` and
not at the root. The fix is two lines and a stated rule: `frontend` joined the top-level set, so
a root document naming `frontend/README.md` is checked, and a path that does not resolve at the
root is tried against the naming document's own directory before it is called missing. A root
document resolves that second way to the root and changes nothing.

**The operator's statement about when these files were made, recorded as his statement.** He states
that the frontend files were made during the first night of the hackathon. That is his account and
it is not verified here: nothing in either checkout records who wrote them, or when the work
happened. What the two checkouts do show, as evidence and nothing more:

- the source checkout's file mtimes: 64 of the 81 at 2026-11-08T07:xxZ, 5 at 08:xxZ, and 12 at
  2026-11-06T23:xxZ (the files of its baseline commit, untouched by the rebuild);
- its five commits: `0208765` at 2026-11-08T07:01:09Z, then four between 08:04:12Z and 08:04:24Z,
  twelve seconds apart in total. A history written in one pass is not a record of when the work was
  done, and it is not read as one here;
- the hackathon's submission deadline, as this repository's own record has it, is 2026-11-08T13:00
  EST (`records/findings/17-hackathon-rules-recheck.md` §1.1). 07:01Z to 08:04Z is 02:01 to 03:04
  EST, the small hours before that deadline. That is arithmetic on two stated values, not a date
  this entry asserts about the hackathon;
- the copy in `frontend/` shows 2026-11-08T08:04Z on 76 files because `git archive` stamps every
  file with the commit time. The copy's own mtimes are therefore evidence of nothing, and are not
  used above.

**Consequence.** The repository is no longer Python, Rust and documents: it holds a Node application
as well, which is why `README.md` gained a layout line and *The frontend* section in the same pass,
and why `records/STATE-OF-PROJECT.md` §A10 records what that app's checks printed from the new path.
`frontend/lib/mock/` is published with the app and is labelled as fixture data in three places: a
rendered mock is the one thing in this tree that a reader could mistake for a measurement.

**Rejected alternative.** Copying only the screens (`app/`, `components/`, `lib/`) and leaving the
app's records and tools behind. That publishes the product surface with none of the evidence for
it, and `frontend/NOTES.md` is the file that lists the nine strings that still read as shipped
features.

**[Corrected 2026-11-08T12:00Z: `frontend/NOTES.md:23-32` has eight body rows, not nine. This is the
same correction as the one at Q6 item 2 and both places needed it; the list lives in exactly one
table, so the two sentences were describing the same eight rows. `awk 'NR>=24 && NR<=31'
frontend/NOTES.md | grep -c '^|'` prints 8.]**

**Staged, not committed.** The import is in the index and no commit is made by this pass. The
commit is the operator's, and so is the author on it.

**[Corrected 2026-11-08T11:41Z: the import is committed, as `009f103` on `release/prep`. The
sentence above was true when it was written and is kept because it records who decided. The
operator's call was the author, and the author is the contributor whose checkout it came from;
the commit's author and committer are the same person, as they are on every commit on this
branch. Nothing has been pushed.]**

## D26: The artist fee is a lamport transfer the seller makes inside the sale transaction, and the chain does not enforce it (2026-11-08)

**Decision.** Feature 5 ships as a **seller-paid lamport fee inside the checkout's sale
transaction**, not as a Token-2022 transfer fee and not as a hook check. `fee = price * fee_bps //
10_000`, floored, `fee_bps` per event, paid by the seller to the artist's wallet by a System
`Transfer` that sits between the price stage and the token move in one atomic transaction. Token-2022's
`TransferFeeConfig` is not used at all. The **instructions-sysvar hook variant** — a hook that reads
the transaction's instructions and refuses unless the artist was paid — is documented in
`docs/ON-CHAIN-DESIGN.md` §15.4 and **not built**.

**Evidence.** `records/findings/36-transfer-fee-on-a-one-unit-ticket.md` (measured: the token program
ceils, so an indivisible ticket can pay only 0 or all of itself) and
`records/findings/42-artist-fee-at-checkout.md` with `tools/artist_fee_proof.py` (measured on a local
validator: the fee is paid exactly; a sale whose fee the seller cannot cover fails whole; an over-cap
sale is refused `6010` and pays nothing). The mechanism correction is from the non-builder review in
`tmp/review/fee-mechanism.md`, MAJOR #1: the buyer never signs, so a fee taken from the buyer was never
available.

**Consequence, and it is a product consequence, not a technical one.** The seller must hold lamports
at sale time: a seller with a ticket and no SOL cannot resell, and the sale fails as a whole rather
than half-completing. The sale transaction has **two signers** — the issuer signs the stage
(`checked_record_for_write` requires `record.authorises`, strict equality with the record's authority
field) and the seller signs the payment and the move — so the venue co-signs every sale it admits.
That is also the limit of the enforcement: the chain guarantees that no ticket moves without a venue
signature, and it guarantees nothing about the fee. Three ways round it are stated in finding 42 §5,
and no screen or README may say the chain charges the fee.

**Rejected alternatives.** (1) Turning the mint's transfer fee on: measured to withhold the whole
ticket, leaving the buyer nothing (D15, finding 36). (2) A fee taken from the buyer: the buyer never
signs and the hook is not given the buyer's wallet. (3) Charging the fee in the hook today, without
reading the instructions sysvar: the hook has no visibility of a lamport transfer, so it could only
check a number, which is the off-chain obligation Q5 already lists as the weakest option. (4) A
divisible mint: it changes every consumer of `decimals = 0`, and 5% of a ticket is not 5% of a price
unless a fractional ticket sells for its pro-rata value, which nothing establishes (finding 36 §5.3,
and its review's second MAJOR: the buyer is credited the net amount, so `amount == TICKET_UNITS`
refuses the only transfer that would deliver a whole ticket).

**Open.** Whether the fee should be compulsory on chain is now a question with a name rather than a
paragraph: the mechanism is the sysvar check of §15.4, and its cost is a per-mint fee account, a
writer, and every sale's transaction shape becoming part of the program's interface. That is the
operator's to choose, and this entry recommends nothing.

## D27: The flip tax is a second seller-paid lamport leg priced off the hook's own hold clock, and the pool is not built (2026-11-08)

**Decision.** Feature 7's *charging* half ships as a **seller-paid lamport tax inside the checkout's
sale transaction**, beside the artist fee and on top of it, not as a Token-2022 transfer fee and not as
a hook check. The rate is a function of the hold: `held_since_unix` is read from the 70-byte v2
`["record", mint]` account, which the hook itself writes with the program's own `Clock` on every
admitted transfer; the default schedule is **1500 bps while the hold is under one hour, falling
linearly to 0 bps at 30 days**, with the two instants and the rate configurable per event. The tax is
`price * rate // 10_000`, floored, paid by the seller to the **artist's wallet** by a second System
`Transfer` that sits between the artist fee and the token move in the same atomic transaction. The
event maker toggles it per event and **the default is off**. A **refund-to-holders pool** — the tax
accruing to holders who did not flip, with a claim instruction — is documented in
`docs/ON-CHAIN-DESIGN.md` §16.6 and **not built**. The instructions-sysvar hook variant of §15.4 is not
built either, and its four reasons apply to this leg verbatim.

**Evidence.** `records/findings/43-flip-tax-at-checkout.md` with `tools/flip_tax_proof.py` (measured on
a local validator: the tax is paid exactly and in the same transaction as the fee and the move; the
boundary ages are priced at the schedule's numbers; a disabled policy builds no sale and a tax that
rounds to zero builds no leg; a sale whose seller cannot cover fee plus tax fails whole; an over-cap
sale is refused `6010` and pays neither) and `market_swarm/tests/test_flip_tax.py` (the rate-for-age
curve over a dense sweep and pinned at both boundaries, with the layout offsets pinned to
`ticketpath/onchain/v2.py`).

**Consequence, and it is a product consequence.** The seller must hold lamports for the fee and the tax
together at sale time, and the sum can exceed what the seller expected because the tax rate moves with a
clock nobody in the transaction controls. A seller holding a ticket and no SOL cannot resell; a seller
whose balance covers the fee but not the fee plus the tax cannot resell either, and the failure is the
whole sale rather than a half-paid one. The clock is the **mint's**: `held_since_unix` is per record,
so one holder's sale resets every other holder's clock, and the number is a seller's own hold only
where one wallet holds the mint at a time -- the design's `supply = 1` mint. The harness runs one mint
per event carrying the event's whole supply, so there the clock is the event's; `max_holdings` limits
units per agent and does not give a holder a clock of its own. A record whose clock was never written
(`0`, which is what `InitializeRecord` writes and what a v1 read-only metas list leaves behind) is
charged the **full** rate, because an unset field must not be the cheapest way out of the tax; this is
the mirror of the rebate's `6027`, which refuses to pay on an unknown hold rather than guessing.

**Rejected alternatives.** (1) A Token-2022 transfer fee: measured to withhold the whole ticket on an
indivisible mint (D15, finding 36), and a tax that falls with the hold cannot be expressed as a rate
the mint carries anyway, since the mint has no view of the hold. (2) Charging it in the hook: the hook
has no visibility of lamports between wallets, and it does not have the recipient, the schedule or the
event's toggle in the record; the sysvar variant would put every sale's transaction shape into the
program's interface and still could not prove the buyer paid the staged price (§15.4, §16.5). (3)
Reading the hold off chain from the app's own ledger: the app's row is the thing being audited, and the
record's clock is written by the program. The **dry run** does keep a per-label simulated clock, and
that is deliberate and labelled: it is a simulation with `chain=simulated` on every row and no claim to
the chain's per-mint clock, so a dry-run `held_seconds` is not the number a live sale would carry. (4) A separate tax transaction: it breaks the atomicity that
makes "the seller paid and the ticket moved" one statement, and it would double the signature fee.
(5) Charging the tax on primary sales: the house selling the artist's own stock at face is not a flip,
and the artist would be paying themselves.

**Open.** (a) Whether the pool half should be built, which needs `ClaimRebate` (tag 7) implemented in
`lib.rs` -- it is prose there and in `state.rs`, and its two error codes are the only part already in
the source -- a
pool account per mint and a claim rule; the claim arithmetic already exists as pure functions in
`state.rs` (`rebate_bps`, `rebate_lamports`), and its `HOLD_FULL_SECONDS = 60` is the demo's number,
not this decision's schedule. (b) Whether a sale staged low enough to round the tax to zero should be
refused, which is a floor no build sets today. (c) Whether the schedule belongs in the record (a
program change) or in the config (where it is), because a per-event policy that lives only in the
config cannot be checked against a dataset row. All three are the operator's, and this entry
recommends nothing.

# Phase 0 — Data situation audit (verified)

**Status:** complete. **Last updated:** 2026-11-07T08:40Z; §4 gained Gap 5 at 2026-11-07T12:55Z, appended, nothing withdrawn. **Author:** orchestrator.
**Purpose:** gate. No estimator in this programme may be committed to a data source
before this file says what that source actually is. `AGENTS.md` makes two claims about
the platform that change the research starting point; both were checked here rather than
taken on trust.

Audit method: direct inspection of the tree, greps for identifiers that would indicate a
backend or a deployed program, one live RPC call against devnet, and row-level
inspection of the fixture files. Commands are reproducible and are quoted where the
result is load-bearing.

---

## 1. What exists on this machine

| Thing | Verified state |
|---|---|
| `.` (this repository root) | Two files at audit time: `AGENTS.md`, `RESEARCH-PROGRAM.md`. Not a git repository (`git status` → `fatal: not a git repository`). |
| `../ticketing-frontend/` | Next.js + React + TypeScript app. 7 routes (`/`, `/events/[slug]`, `/tickets/[id]`, `/my-tickets`, `/organizer`, `/verify`, plus `not-found`/`error`). `components/` are presentational and never fetch. `lib/api.ts` is the single data seam. |
| Backend | **None.** No server directory, no route handlers, no database, no migrations, no ORM schema. `API_CONTRACT.md` is a specification for a backend that does not yet exist. |
| Deployed Solana program | **None referenced.** No `programId`, `PROGRAM_ID` or `program_id` anywhere in the frontend tree (grep over `*.ts|*.tsx|*.md|*.json`, `node_modules` excluded). Nothing in the app constructs a transaction; wallet interaction is a message signature only (`lib/solana.ts` → `verificationMessage`, "proves key ownership, is not a transaction, and cannot move tokens"). |
| Toolchain | `python3` 3.12.3, **no pip, no ensurepip, no numpy/scipy/pandas/sklearn/statsmodels**, no `uv`, no `conda`, no virtualenv on disk. `venv` module exists but cannot install anything (no ensurepip). Network egress works (devnet RPC reachable, web search and the arXiv CLI work). |

**Consequence for Phase 7:** the implementation must be **Python standard library
only**, or it cannot be run on this machine. That is not a hardship — the programme
already asks for minimal dependencies, fast inference and low memory — but it is a hard
constraint and every model in this programme is specified with it in mind. Anything
needing a numerical stack is out of scope by construction unless the operator installs
one.

## 2. The fixtures are synthetic — settled, not assumed

`lib/mock/` contains 6 events, 128 tickets, 293 wallet rows and 253 ledger rows
(128 `issue`, 90 `sale`, 21 `transfer`, 14 `redeem`). `AGENTS.md` declares them synthetic
fixture data built to render the UI. Three independent checks agree:

1. **No generator, no provenance.** No script in the tree produces them, no seed, no
   capture date, no source noted anywhere in the frontend repo or its `README.md`.
2. **The ticket mint addresses are not valid Solana public keys.**
   `getAccountInfo` on `iVNE1WChfNH9SpRiMoipPgRzsYuNWYSapgyUtdtv3Lbu` against
   `https://api.devnet.solana.com` returns `{"code":-32602,"message":"Invalid param:
   WrongSize"}` — the string does not decode to 32 bytes. A real SPL mint cannot look
   like this.
3. **The fixture respects the resale cap as a hard ceiling but never models rationing
   at it.** Across the 90 priced sales, the maximum markup sits strictly below the
   event's `resalePriceCapBps` in every event that has a cap, and no sale lands exactly
   on it. A market where a binding legal ceiling rations quantity would show a mass
   point at the cap and unsatisfied demand behind it. The generator simply drew below.
   This is a property of the fixture author, not of any market.

Also observed while reading the rows, and recorded because it constrains what can be
computed rather than because it says anything about tickets: 79 of 128 tickets have no
sale at all (`lastSalePriceLamports` null); no `transfer` row carries a price; and
`markupBps` on a sale is exactly `priceLamports / faceValueLamports - 1` in basis
points (checked: 1_532_880_000 against a 900_000_000 face gives 7032, matching the
stored value). So markup is defined **against that ticket's own tier face**, which
matches `API_CONTRACT.md`'s warning about not re-deriving event-level markup.

**Rule adopted:** fixtures may be used only to exercise code paths and schemas
(parsing, validation, arithmetic, rendering, plumbing). They may never enter an
estimation, a validation claim, or a result. No number in this programme comes from
`lib/mock/`.

## 3. The observation set an estimator will actually receive

`lib/types.ts` is the wire contract and is the authority. For one ticket the platform
yields:

- `LedgerEntry[]`: `kind ∈ {issue, sale, transfer, redeem, revoke}`, `fromWallet`,
  `toWallet`, `priceLamports` (null when unpriced), `markupBps` (null when unpriced),
  `signature`, `slot`, `occurredAt` (ISO-8601 UTC).
- `Ticket`: `faceValueLamports`, `tierId`, `mintAddress`, `ownerWallet`,
  `issuedToWallet`, `status ∈ {valid, listed, redeemed, revoked}`,
  `transferRestricted`, `issuedAt`, `redeemedAt`.
- `Event`: `startsAt`, `endsAt`, `venue`, `city`, `organizer`, `status`, tiers
  (`faceValueLamports`, `totalSupply`, `issuedCount`), `resaleEnabled`,
  `resalePriceCapBps`, `requiresVerifiedWallet`.
- `ResaleStats` / `EventAnalytics`: derived aggregates (sale counts, average markup,
  day-bucketed price series, markup distribution in bps buckets, holder destinations).

## 4. What the contract does **not** carry — the four gaps that shape the architecture

These are absences from the schema, each verified against `lib/types.ts`, not guesses
about the company's database.

**Gap 1 — no listing exposure, therefore no sale hazard.**
`Ticket.status` can be `listed`, but it is a *current state*, not a history. There is no
listing start time, no asking price, no revision trail, no withdrawal, no view count. So
for each ticket we know whether it eventually sold but not the interval during which it
was at risk of selling, nor at what ask. **`P(sale | price, exposure, t)` is not
identified from a completed-transaction ledger alone.** Without exposure, the observed
sale count is a numerator with no denominator. This is the single most consequential
finding of the audit and it contradicts a naive reading of `AGENTS.md`'s first
consequence ("a resale on this platform is a recorded transaction… here that part of
Phase 2A is smaller than the literature implies"). The *asking-versus-realised* gap does
shrink. The *censoring* problem does not shrink — it relocates, from censored asking
prices to an unobserved exposure denominator plus a policy-truncated price ceiling
(Gap 2).

*Minimal fix, if the operator wants it:* record, per listing event, `{listPriceLamports,
listedAt, delistedAt | soldAt, delistReason}`. Four fields turn sale probability from
unidentifiable into directly estimable. This is the one data request this programme
makes; it is written up in `F-decision-log.md` and repeated in the final deliverable.

**Gap 2 — the resale price ceiling is a policy truncation with rationing behind it.**
`resalePriceCapBps` ("hard ceiling on resale price as basis points over face value",
`null` = uncapped but still tracked) means the top of the price distribution is not
sampled at all where the cap binds. At a binding cap the market does not clear by price;
it clears by *speed and rationing*. That makes (a) the observed markup distribution
left-truncated by design, (b) the cap region a mass point whose height measures excess
demand rather than value, and (c) the right-hand tail of latent willingness-to-pay
invisible to any estimator that only sees transactions. Any model of "what is this
worth" that is fitted to capped prices will systematically understate value on exactly
the events where value is highest. This is checked in Phase 1-B and Phase 2-A, and it
drives the design of the sale-probability component.

**Gap 3 — no seat coordinates.** `Ticket` carries `tierId`, `serial` and a mint. It does
not carry section, row or seat. `AGENTS.md` states the ledger yields "markup
distribution conditioned on section"; the contract cannot support section-level
conditioning, only tier-level (tier names are free text like "Floor GA", "Front Rail").
Either the company's internal ledger has coordinates that the wire contract omits, or
that claim is about tier. **Open question for the operator** — it matters because seat
quality is the strongest within-event price axis in every published ticket study, and a
tier-only engine cannot express it. Recorded in `C-variable-registry.md` as
`seat_quality` with availability "not in contract".

**Gap 4 — no fee, royalty or settlement field.** Money appears only as
`priceLamports` and `markupBps`. There is no platform fee, creator royalty, payment
processing cost, or net-to-seller figure anywhere in the contract. The programme's
objective is *net* expected economic value (§Phase 5), and the primary-price optimum
depends on the fee structure: a per-unit fee and an ad-valorem fee give different
optima. So the fee model must be a parameter supplied by the operator, and the
optimiser must expose it. Recorded as `fee_model` in `C-variable-registry.md`, and the
Phase 5 derivation carries it symbolically rather than assuming zero.

Two smaller ones, recorded for completeness: primary inventory is a snapshot
(`totalSupply`, `issuedCount`) with no time series, so primary sell-through *velocity*
is not observable; and `Event.status` transitions are not timestamped, so on-sale start,
sell-out and holdback-release times are unknown.

**Gap 5 — no primary inventory time series, therefore no sell-through velocity.** *Numbered
2026-11-07T12:55Z. The label was already in use in three files (`01-a`, `01-c`, `B-mathematical-kb`) before
this paragraph existed; the table at the end of this section lists every citation and what each one means.* The
first of the two unnumbered absences above,
promoted to the same standing as Gaps 1–4 because three later findings build on it and the programme has
never made it a data request.

`TicketTier` carries `totalSupply` and `issuedCount` as a *snapshot with no capture time*, and
`Event.status` is a state with no transition timestamps. So the tier's sell-through **level** is observable at
the moment of extraction and its **path** is not: no booking curve, no on-sale time, no sell-out time, no
holdback-release time, no rate at all. This is the gap that makes `issuedCount` a temporal-correctness hazard
rather than a covariate (`01-c` §3.6): used as a predictor at time *t* it carries information from after *t*
unless the snapshot's capture time is recorded, and the contract cannot identify the value at prediction time.

What it does **not** do, stated because it is easy to overread: it does not delete the demand bracket. The
level of primary sell-through is the one place in the schema where a demand object is identified (`01-b` §5,
closing paragraph), and that sentence is about the level, not the velocity. Gap 5 narrows the bracket's
dynamics; it leaves the level standing.

*Minimal fix, if the operator wants it:* a timestamped series per tier — `{tierId, capturedAt,
totalSupply, issuedCount, eventStatus}` — plus the four `Event.status` transition times (on-sale, sell-out,
holdback release, close). This is **not** among the four listing fields of Gap 1, which is the point `01-c`
§2 flags: revenue management's demand side is blocked by a data gap the programme has not yet requested. It
is the fourth item of the ranked data-requirements list in `DELIVERABLE.md` §14.3.

*Where the label is used, and what it means at each site* (checked 2026-11-07T12:55Z, all eight mean the
primary inventory time series above and nothing else):

| Site | The sentence | Meaning |
|---|---|---|
| `findings/01-a-market-structure.md` §7 ("Still have") | "Primary sell-through velocity: inventory is a snapshot only (Gap 5)." | verbatim this gap |
| `findings/01-c-methods.md` §1.4(3) | "must either get a timestamped series (Gap 5) or restrict itself to the value at prediction time" | this gap, as the alternative to the look-ahead restriction |
| `findings/01-c-methods.md` §2 ("Data") | "The booking curve needs a primary inventory time series, which is Gap 5 and is **not** among the four fields" | this gap, and explicitly not Gap 1's four fields |
| `findings/01-c-methods.md` §3.6 | "Either the operator supplies a timestamped inventory series (Gap 5)" | this gap |
| `findings/01-c-methods.md` §9.3 ("Data") | "a primary inventory time series (Gap 5) for the coupled system" | this gap |
| `B-mathematical-kb.md` §6.4 (F14 "Data") | "a primary inventory time series (Gap 5) for the coupled system" | this gap |
| `B-mathematical-kb.md` §6.5 (F14 gate) | "gated on Gap 5 + delistReason" | this gap, plus Gap 1's `delistReason` |
| `B-mathematical-kb.md` §9 relationships diagram (F14 box) | "F14 needs Gap 5 + delistReason" | this gap, plus Gap 1's `delistReason` |

No citation was replaced, because all eight agree on the referent and defining it once is the smaller
change than rewriting eight forward references. Files that *report* the label rather than use it
(`A-research-ledger.md`, `findings/00-ledger-verification.md`, `findings/00-verification-round1.md`,
`findings/00-adversarial-review-phase1.md`, `CORRECTIONS-APPLIED.md`, `DELIVERABLE.md` §20.5) keep their
histories; `A-research-ledger.md` carries a dated line saying the label is now defined.

## 5. Effects on the programme

1. **No result in this programme can be class A from our own data.** Every quantitative
   conclusion is class B, C, SIM, or UNVALIDATED. Class A can only be cited from
   published ticket-market research. This is written into `records/README.md` and is
   enforced at review.
2. **Simulation is legitimate, but only for estimator properties.** A simulation study
   ("does this estimator recover the parameter when the data are generated like X?") is
   methodology research and is labelled SIM. A simulation is never a validation of the
   engine against ticket markets, and no simulated accuracy number may be quoted as if
   it measured performance on tickets.
3. **The deliverable includes a data-requirements specification**, not just a model:
   the minimal additional observations that would make each component identifiable, in
   the order that buys the most.
4. **The wire contract is the interface.** The engine consumes and produces the shapes
   in `lib/types.ts`; that is what makes it implementable against the real platform
   without redesign, and it is why the contract was read line by line here.

## 6. Reproducing this audit

```bash
# no backend, no program id
grep -rn "programId\|PROGRAM_ID" --include=*.ts --include=*.tsx --include=*.md \
  ../ticketing-frontend | grep -v node_modules     # → no matches
# fixtures are not real accounts
curl -s -X POST https://api.devnet.solana.com -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getAccountInfo",
       "params":["iVNE1WChfNH9SpRiMoipPgRzsYuNWYSapgyUtdtv3Lbu",{"encoding":"base64"}]}'
# → {"error":{"code":-32602,"message":"Invalid param: WrongSize"}}
# toolchain
python3 -c "import numpy"      # → ModuleNotFoundError
```

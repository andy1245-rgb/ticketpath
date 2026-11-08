# BUILD-SPEC-NIGHT — the document the night builds from

**Status:** authoritative for the build that runs 2026-11-07T13:00Z → 2026-11-08T09:00Z.
**Written:** 2026-11-07T11:40Z. **Author:** build-spec session, read-only over every input below.
**Deadline this is sized against:** Sun 2026-11-08 10:00 America/Toronto = **15:00Z**. The 11:45 ET
final deadline is not a target and nothing in this plan uses it.

**What this document is.** The single artefact the night's build agents read. It fixes the surface, the
labels, the module boundaries, the pricing path, the on-chain boundary, the clock and the cut list. A
build agent that has read it once should never need to ask a question. Where it cannot be decisive because
a finding is missing, it says so under **GAP** and states the rule the build must use meanwhile.

**What this document is not.** It does not re-open the product. Ticketpath is an organizer
revenue-management tool that prices primary tickets off the resale record. There is no listing, bid, buy
or checkout endpoint and none may be built. No LLM sits in the ticket path. Any reversal has to be argued
into `records/F-decision-log.md` as a new decision; nothing in this build reverses one.

---

## 0. Inputs: what I read, and what I had to do without

**Present and read in full or in the sections cited:**

| File | Used for |
|---|---|
| `records/findings/02-rubric-and-scoring.md` | the rubric, the four judge criteria, the video rules, the on-chain evidence standard, the ten artefacts a Sunday build must contain (§A–F) |
| `records/CONTRACT-MAP.md` | what the wire can serve field by field; §5 (what it cannot), §6 (what the engine needs and the contract lacks), §9 (operator decisions) |
| `records/DEMO-PROOF.md` | the measured proof that no contract route or field can carry a recommendation; the four screens that serve real backend data; §6, the labelling gap |
| `records/00-prior-direction-index.md` | the fifteen pre-VM documents; the six conflicts with tonight's plan; the decisions tonight must honour (§3) |
| `records/findings/01-b-identifiability.md` | T1–T6; the case-only sample; the cap as a partial anchor; the four listing fields |
| `records/findings/02-a-price-paths.md` | the path specification (§8.1–8.6), the conditioning inversion (§4.4), the cap truncation (§6), the money-vs-markup warning (§7.2) |
| `records/findings/02-c-sale-hazard.md` | the composite intensity (§1.2, §2.4), what is identified (§1.3), the display rules (§7.2–7.3) |
| `records/findings/02-d-elasticity-fees-optimum.md` | the objective and the fee wedge `c**` (§1–§2), the boundary rule (§2.4), the sensitivity (§5), the report wording (§6) |
| `records/findings/02-e-cold-start.md` | the band, the prior, the ladder, the labels (§4–§7) |
| `records/findings/02-ai-ml-decision.md` | D5: one estimator, no AI track, no LLM behind the price |
| `records/findings/03-b-temporal-correctness.md` | the decision times D1–D3, the 26-row build checklist (§7), the forbidden aggregates (§4 T2), the floors (§6.4–6.5) |
| `records/findings/02-b-cap-truncation.md` | **landed at 11:30Z, mid-write, and is adopted in full.** The truncation/censoring distinction (§1.3), the three regimes (§3.1), the no-upper-bound rule and its replacement wording (§3.4), the pointwise lower bound B1 (§2) |
| `records/CONTRACT-CONFORMANCE.md`, `tools/build_fixture_store.py`, `fixtures/README.md` | the contract-conformance test that must keep passing; the fixture is **generated** (seed `20261107`) and `--check` proves freshness |
| `records/findings/00-adversarial-review-phase1.md` | the three narrowed wordings, the twelve allowed and twelve prohibited sentences, and the one sentence the engine must stop printing |
| `records/F-decision-log.md` | D1–D5, Q1–Q3 |
| `records/D-model-registry.md` | the SHIP / SHIP-BEHIND-ADAPTER / REJECTED verdicts (M01–M56) |
| `records/B-mathematical-kb.md` | **a 106-byte stub.** No derivations. The maths lives in the findings, and §4 of this spec cites the finding, not B. |
| `docs/ON-CHAIN-DESIGN.md`, `docs/ON-CHAIN-FOR-LAPTOP.md`, `docs/BACKEND.md` | the on-chain design, the simulation's arms and error codes, the backend's start command |

**Absent when this pass began, and what happened to each:**

| File | Status | Consequence, stated as a GAP |
|---|---|---|
| `records/findings/02-b-cap-truncation.md` | **absent at 11:10Z, present at 11:30Z.** It is read and adopted: §2.6's A19 and A20, §3.4's three regimes and §4.7's binding case are 02-b's rules, not this author's. | **GAP-1 closes.** Its §3.4 replacement wording supersedes `02-d` §6's "we would not argue with any price in that range" on a capped-and-binding event; §2.6 records the replacement. |
| `records/findings/03-a-interactions.md` | **does not exist at 11:40Z.** | **GAP-2.** No interaction registry, so this build prices one event at a time and treats cross-event effects as absent (`02-d` A4). The spec does not claim any interaction is measured. |
| `records/B-mathematical-kb.md` | stub, 106 bytes. | Derivations are cited to findings by section, not restated. |

`03-b-temporal-correctness.md` appeared at 11:19Z and `02-b-cap-truncation.md` at 11:30Z, both after this
brief was written; both are read and used. §3 adopts 03-b's build checklist rows by number and its as-of
rule; §2.6 and §3.4 adopt 02-b's regimes and its no-upper-bound rule. `03-a` is still missing at 11:40Z.

**The fixture is a moving target and the spec is written not to depend on it.** `fixtures/synthetic_store.json`
was regenerated twice between 11:10Z and 11:35Z (8 events, 76 tickets, 147 ledger rows at the last read) and
it is produced by `tools/build_fixture_store.py` with `--check`. Therefore: no event id, tier id or fixture
number in this document is an acceptance criterion. Every worked number is labelled a **snapshot**, every
module is specified by algorithm and invariant, and the acceptance test is stated as invariants that hold
for whatever the fixture contains (`§1.1`, `§4.7`). The build pins the actual values in a golden test at the
freeze, and the test and the snapshot change together.

**Two additions to the brief, both applied.** (1) The console page at `http://127.0.0.1:8788/` is specified
in §1, §2, §3 and §4 as the judge-clickable surface for the product's own output, because
`records/DEMO-PROOF.md` §4 and `CONTRACT-MAP.md` §9.2 prove no contract route can carry it. (2) The
adversarial review's prohibition is carried verbatim in §2.6 and its narrowed wording is adopted in every
sentence the UI may print.

---

## 1. What a judge clicks

Two surfaces, one honest. **The frontend shows the market. Our console shows the decision.** A judge who
only sees one of them has seen half the product, and the video shows both in that order.

The console is one HTML page served by the backend itself at **`http://127.0.0.1:8788/`** (or
`http://localhost:8788/`). Python standard library only. No framework, no CDN, no build step, no
JavaScript required for any number to appear, one route, server-rendered. Every control is a query
parameter, so every state a judge can reach has a URL that reproduces it.

### 1.1 The sequence, in order, with the exact screen and the exact input

1. **Open `http://127.0.0.1:8788/`.** The page title is `Ticketpath — organizer pricing console`. The first
   element in reading order is a full-width banner, not dismissible, not sticky-hidden, and it is exactly
   sentence T1 of §2.3:
   `SYNTHETIC FIXTURE DATA — every number on this page is computed from a synthetic fixture generated in
   this repository. Not real ticket data. No accuracy claim is made or implied.`
   Second line: `No program is deployed on any cluster. The [DESIGN] block at the bottom says what that
   means.` Third line: `fixture build: {sha256 of fixtures/synthetic_store.json}`, so a screenshot names
   the exact store it came from.
2. **The page has already selected an event, and the selector lists every event with its regime.** The
   three regimes are `02-b` §3.1's, and the page uses its names: `capped and binding` (a cap, and at least
   one sale at exactly the ceiling), `capped, no mass point` (a cap, no sale at it, so the ceiling's status
   is unknown), `uncapped` (no cap, the only regime in which the top of the distribution is sampled), plus
   `no resale`. The default selection is the event with the highest share of sales at the ceiling, ties
   broken by the most sales, because that is the case the product exists for. On the fixture as generated
   at 11:35Z that is the event titled "Synthetic Stage: Resale Cap Binds", General tier, `asOf` = the
   server clock, `capBps` = the event's own policy, `feeLamports` = 0, `tau` = 0.20. The canonical URL is
   printed under the controls so it can be copied, and the fixture's build hash (`tools/build_fixture_store.py
   --check`) is printed beside it.
3. **The evidence strip, above everything else on the decision panel.** Counts, each prefixed with its
   badge: `[FIXTURE] {n} resales on this event · {t} tickets · {k} at the ceiling` ·
   `[FIXTURE] {E} events on this platform, {M} with any resale` · `[DEVNET] 0 on-chain transactions`. The
   evidence count is the headline metric of the page, by design (`02-e` §7.1), and the at-ceiling count is
   beside it, because it decides which regime the page is in.
4. **The decision block on a capped-and-binding event, which is the largest thing on the page, uses
   `02-b` §3.4's wording and not `02-d`'s.** It reads, in this order and at this weight:

   > **[UNVALIDATED] Recommended primary price: at least {ceiling} SOL per ticket, {tier} tier.**
   > The resale price in this tier is capped at {c}% over face, and the cap is binding: {k} of {n} recorded
   > resales ({s}%) settled at exactly the ceiling. Those buyers each paid the most the platform allows, so
   > the record shows what was paid, not what buyers would have paid, and every sale the ceiling turned away
   > is missing from it entirely.
   > **Value: at least {ceiling} SOL per ticket. That is a floor, not an estimate.** It is the highest
   > recorded price in this tier, and it is the most this record can support.
   > **Range: {ceiling} SOL and up. We do not state an upper bound from this record.**
   > *This is a bound, not an optimum.*

   `{ceiling}` is exact arithmetic, `face × (1 + cap_bps/10 000)`, and the golden test asserts that on this
   event the recommended figure equals the ceiling to the lamport, because at least one recorded sale sits
   exactly there. That assertion survives any regeneration of the fixture. The percentage, the counts and
   the face come from the record.
5. **Select the uncapped event and the same block changes shape.** Where the record is not truncated, the
   engine states a point and a band: `[UNVALIDATED] Recommended primary price: {P} SOL per ticket` with
   `Band {P_lo} – {P_hi} SOL`, `basis: "tier_marks"`, `02-d` §6's range line, and A4. The contrast
   between step 4 and step 5 is the product's whole thesis, and the page says it in one line above both:
   *a cap does not hide the price; it hides the top of the price distribution.*
6. **The market block** (the input to the decision, shown so a judge can check the arithmetic himself):
   median and mean markup, the at-ceiling sales marked `[FIXTURE] at the cap — a rationing point, not a
   market-clearing price`, any repeat sale as `[FIXTURE] one ticket sold twice: {p1} → {p2} SOL over {d}
   days. One pair is a fact, not an index.`, and the rate `[FIXTURE] {n} sales over {e} ticket-days at risk
   = {x} sales per ticket-day` with the two footnotes `02-c` §7.1–7.2 requires: *that is a transaction
   rate for the ticket population, marginalised over whether the ticket was ever offered, and it is not the
   probability that a listed ticket sells*.
7. **The refused block, always present, never empty.** Each line `[REFUSED]` with its reason: *path slope*
   (`the resales span {d} days; 5 days of spread are required`), *sale probability at a price* (`the ask of
   the risk set is not recorded`), *interior optimum* (`no primary demand response: η and q_min are not
   identified`), *net revenue* (`no fee model configured`), and on a binding event *an upper bound* (`the
   ceiling truncated the record; we do not state one`). When the engine can answer a line, the line states
   the number instead — and the block never disappears, so a judge cannot mistake "answered" for "hidden".
8. **Change the date and re-run.** The `asOf` field is a datetime input. Move it before the first sale on
   the selected event and press `Recompute`: the regime chip becomes `no resale`, the evidence strip drops
   to zero, and the decision block becomes the refusal of step 11. Move it forward again and the counts,
   the regime chip and the decision block change together. **Nothing after `asOf` enters any number**, and
   the URL carries the instant, so a judge can re-run the same decision and get the same answer.
9. **Change the cap and re-run.** The `capBps` field accepts 0–10000 and is read as a **forward policy**,
   never as a re-classification of the past (`§3.4`: the regime is judged against the cap in force when
   each sale was recorded). Set it below a recorded price and the page prints
   `[FIXTURE] {k} of {n} recorded sales in this tier are above this cap; under the deployed program those
   transfers would have failed, so this record could not exist`, keeps the band where the record put it,
   and says *a recorded price is a fact about the past; the cap is a rule about the future*. Set it above
   the recorded ceiling and the block adds `raising the cap changes what we will learn from the next sales,
   not what this record says`.
10. **Change the declared τ and re-run.** `tau` accepts 0.10–0.406. On an uncapped or no-mass-point event
    the band widens and narrows while the point estimate stays put, and the page says so: *τ does not enter
    the point estimate; it enters only the width* (`02-e` §4.3). On a binding event the control is inert
    and the page says why: *there is no upper tail in this record for τ to widen.* Both behaviours are
    demonstrations: one that the engine is not fitting a number it does not have, and one that the ceiling,
    not the model, is what removes the bound.
11. **Select an event with no resales.** The decision block is replaced by the full refusal:
    `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.` Below it,
    the prior band with the `02-e` §5.4 sentence verbatim, the exact cap arithmetic if the event has a cap,
    A17 with the event counts, and the sentence that names what would change it: *one completed resale on
    this event, or a completed event like it.* This is the cold-start screen, and it is a state of the same
    page, not a different page.
12. **Scroll to the on-chain panel.** `[DESIGN] No program is deployed on any cluster. What follows is the
    invariant, the instruction set and a simulation; none of it is a deployed guarantee.` Then one
    sentence of invariant, then a table of instruction → check → error code, then the simulation.
13. **Press `Show the refusal`.** The simulation runs the three arms that matter and prints one line each,
    every line prefixed `[SIMULATED]`: the cap at `cap+1` lamports refused with `6010 E_CAP_EXCEEDED`, a
    custody move the program did not stage refused with `6009 E_TRANSFER_NOT_STAGED`, a transfer to an
    unverified wallet refused with `6012 E_DEST_UNVERIFIED`. The caption says, in the same weight:
    *a Python mirror of the state machine, standard library only, no cluster contacted; it proves the
    arithmetic and the ordering, not that Token-2022 calls a hook.*
14. **The last thing on the page is the chain slot, and it is the thing that makes this a working thing on
    Solana.** Two states, never a third:
    - **`[DEVNET] No devnet transaction has been recorded.`** with *the console shows this state until
      `tools/devnet_check.py` has verified a signature against `api.devnet.solana.com`. No signature is
      ever typed into this page by hand.*
    - **`[DEVNET] Verified at {verifiedAt} against api.devnet.solana.com`** — the timestamp is written by
      the checker, never by the page — with the signature, the
      slot, the block time as a UTC timestamp, the cluster, the mint or program id it touched, and the
      quote id whose SHA-256 the transaction's memo carries. Below it: *this is the pricing decision
      committed on devnet before the sale opens, so it cannot be re-cut afterwards — and the transfer
      hook that makes the cap binding is designed, not deployed.*

**The acceptance test is the fourteen steps above, performed in order, by someone who did not build the
page, from a cold start (`kill` the server, start it, click).** If any step needs a second tab, a
terminal, or an explanation, the build is not done.

### 1.2 What the judge must be able to say afterwards

Three sentences, and the page has to earn all three:

1. "It prices a ticket from the resale record and tells me where the answer runs out."
2. "It refused to give me a number in five places, and each refusal named the missing observation or the
   truncation that caused it."
3. "The decision is committed on devnet, the program that enforces the cap is designed and simulated,
   and the page says which is which."

A judge who says "it's a pricing dashboard with a Solana sticker" means step 14 failed. A judge who says
"it made up a probability" means §2.6 failed. Those are the only two failure modes that matter.

---

## 2. The honest-data rule, made operational

The rule: **the chain artefacts must be real or absent; everything else may be synthetic if the screen
says so, in the same weight as the number, in the same text node.** `records/DEMO-PROOF.md` §6 measured the
failure this section exists to prevent: the `dataSource` label reaches the browser inside the serialised
payload and appears **nowhere in the visible text**. Carrying a label is not labelling. This build renders
it.

### 2.1 The eight badges, exact strings

Every number, and every block that is not a number, carries exactly one badge. The badge is a text prefix,
in capitals, in square brackets, in the same font size as the number, and it is the first thing in the
block's reading order. Text, not colour alone, so it survives a screenshot, a projector and a colour-blind
judge.

| Badge | Exact string | Applies to | Means |
|---|---|---|---|
| B1 | `[FIXTURE]` | sale counts, prices, dates, tiers, cap, sell-through, exposure | computed from `fixtures/synthetic_store.json`, which is generated by `tools/build_fixture_store.py` (seed `20261107`): not scraped, not real |
| B2 | `[DECLARED]` | τ, fee per ticket, sell-through floor, candidate cap | a parameter a person set; not estimated from data |
| B3 | `[EXACT]` | cap ceiling, required sell-through, net revenue at a stated sell-through | arithmetic true by definition; carries no uncertainty |
| B4 | `[UNVALIDATED]` | the band, the point estimate, the recommendation | an engine output; no parameter has been checked against a real resale |
| B5 | `[REFUSED]` | a block where a number would go | the engine declines, and the reason is on the same line |
| B6 | `[DESIGN]` | program, accounts, instructions, hook checks | design only; nothing compiled, deployed or run on a cluster |
| B7 | `[SIMULATED]` | every line of the state-machine transcript | produced by the Python mirror; no cluster contacted |
| B8 | `[DEVNET]` | the chain slot | read back from devnet and verified, or explicitly absent |

Eight badges, and they are not interchangeable: `[FIXTURE]` never appears on an
engine output, `[UNVALIDATED]` never appears on arithmetic, `[DESIGN]` never appears on anything a cluster
returned, and `[DEVNET]` never appears without a signature, a slot and a block time.

### 2.2 Placement rules, binding on the build

| # | Rule | Checked by |
|---|---|---|
| P1 | The badge is the first text in the block, before the number, in the same DOM subtree | `test_console_page.test_badge_precedes_number` |
| P2 | Same font size as the number it labels, at least 14 px at 1280 px width, and never smaller than body text | CSS assertion in the page test (the rule is a class, and the test asserts the class is applied, not the pixels) |
| P3 | No `title=` attribute anywhere on the page. A tooltip is a label nobody reads | `test_console_page.test_no_title_attributes` |
| P4 | The banner is the first element in document order, is not dismissible, has no close control, and is not `position: sticky` with a hide-on-scroll rule | `test_console_page.test_banner_is_first_and_undismissable` |
| P5 | Every numeric leaf in the JSON payload has a sibling `badge`, `basis` and `labelId`; a leaf without them fails the payload walker | `test_guidance_api.test_every_number_is_labelled` |
| P6 | The `basis` string names the record and the count: `3 sales, 1 at the ceiling, 1 event with resale` — never "data" | `test_guidance_api.test_basis_names_counts` |
| P7 | The page is readable with CSS off: the badge and the number are in the same text run, in that order | `test_console_page.test_reads_without_css` (renders and strips tags) |
| P8 | The badge is inside the accessible name of the block (`aria-label` begins with the badge text) | `test_console_page.test_accessible_name_carries_badge` |
| P9 | The page never renders a number that came from `EventAnalytics`, `ResaleStats`, `Ticket.lastSalePriceLamports`, `Ticket.transferCount`, `Ticket.status` or `Ticket.ownerWallet` — those are whole-history aggregates with no stated as-of (`03-b` §4 T2, row 5 of its checklist) | static grep over `ticketpath/console/` and the forbidden-path test |
| P10 | Printing the page to PDF or photographing it loses no badge: no badge is `:hover`-only, `:focus`-only, or inside a collapsed element | `test_console_page.test_no_hidden_labels` |

### 2.3 The five sentences that must appear verbatim

T1, the banner: `SYNTHETIC FIXTURE DATA — every number on this page is computed from a synthetic fixture
generated in this repository. Not real ticket data. No accuracy claim is made or implied.`

T2, on the decision block, always: `This is a bound, not an optimum.`

T3, wherever a band is shown: `The band is a declared width around the record, not a confidence interval,
and it has not been checked against what this event sold for.`

T4, wherever a rate is shown: `That is a transaction rate for the ticket population, marginalised over
whether the ticket was ever offered. It is not the probability that a listed ticket sells.`

T5, on the chain slot in its absent state: `No program is deployed on any cluster. Nothing on this page is
a deployed guarantee.`

### 2.4 What may not be said about the data, on any surface

- The words `live`, `production`, `real-time` or `market price` about any number on the page.
- `prediction`, `forecast` or `expected` as a noun for the band, the point estimate or the recommendation.
  The engine's output is a recommendation and a band; it is not a forecast of a price.
- Any sentence that attributes a number to the company, the platform, "our data" or "the market" when the
  number is fixture, declared, or engine output.
- `comparable events` (`02-e` §5.5).
- Any suggestion that the devnet slot is populated when it is not, including a placeholder signature, a
  greyed-out Explorer link, or an "on-chain" badge on a design block.

### 2.5 Where the label sits, in one diagram described in words

Per number block, in this order, and the order is tested: badge → number → unit and tier name → basis line
(counts and source) → the label sentence if the number is engine output. Per panel: a heading that names
the panel's badge. Per page: the banner, then the evidence strip, then the decision, then the market, then
the refusals, then the chain. The decision never appears below the fold at 1280×800, and the banner never
scrolls away.

### 2.6 Sentences the engine may print, and sentences it must not

**The prohibition, carried verbatim from `records/findings/00-adversarial-review-phase1.md` §6, and the
single most important line in this document:**

> **The engine must stop printing the sentence "This ticket has an X% chance of selling at price p."**

The same prohibition in the review's own table form, also prohibited: *"The probability this ticket sells
at price p is X%."*

**Allowed.** These are the only sentences the UI may use for these objects. `{...}` are substituted fields.
Each has an ID that `ticketpath/core/labels.py` exports, and the page may print only an ID, never a literal.

| ID | Sentence | Object |
|---|---|---|
| A1 | `On this event the ledger records {n} sales. The sale rate is {x} per 1,000 ticket-days at risk. That is a transaction rate for the ticket population, not the probability that a listed ticket sells.` | the composite rate |
| A2 | `The resale value of this ticket is bounded. The last recorded sale gives a floor, the resale cap gives a ceiling, and the interval is wide because the ledger records sales, not listings.` | the band |
| A3 | `On this event the cap binds: tickets sold at the cap are recorded at the ceiling, so their value is at least the cap. How far above it we cannot say from this record.` | the cap-binding branch |
| A4 | `The primary price recommendation is a range, not a point. It is based on the resale value signal and the primary sell-through observation; it does not use a resale sale-probability curve.` | the recommendation |
| A5 | `The value index is a set of ratios across events and tiers, normalised to a base period. It does not give an absolute price level without an external anchor.` | any ratio reported |
| A6 | `The fee basis is a parameter, not an estimate. If the recorded price is the buyer's gross, the seller's net is lower by the fee schedule, and the recommendation changes with the fee model.` | the fee line |
| A7 | `The sale indicator is calibrated on the full ticket population. No price distribution is calibrated, and we quote no coverage number for a price.` | calibration |
| A8 | `The estimate is a bound with a stated width. The width is driven by the missing listing exposure and the cap truncation.` | the band's width |
| A9 | `The ledger is complete only conditional on enforcement: wallet handoff and off-platform settlement leave no row, and we do not impute them.` | any completeness claim |
| A10 | `The cap is a ceiling on the resale price and therefore on the buyer's outside option; it is a floor on value, not a target for the primary price.` | the cap |
| A11 | `This is a class-C bound from the schema and a class-B prior from the literature; it is not a measured result on this platform.` | any output that rests on the prior |
| A12 | `No prediction: nothing has resold on this platform yet, so this band comes from published ticket markets and has not been checked against a single sale here.` | the J=0 cold start (`02-e` §5.4) |
| A13 | `Not a prediction: this event has no resales yet, so the band is the spread across {n_events} other events and has not been checked against what those events sold for.` | the cold start at J≥1 |
| A14 | `Recommended primary price: {P} SOL per ticket. This is a bound, not an optimum. It is the highest price at which this event still fills on the evidence available: {s}% of the tier sold at {y} SOL with {d} days to go, and resale clearing at {m} SOL. Above {P} we cannot show that the house still fills, and we will not recommend a price we cannot defend.` | the recommendation, no-elasticity branch (`02-d` §6) — **uncapped and no-mass-point events only** |
| A19 | `The resale price in this tier is capped at {c}% over face, and the cap is binding: {k} of {n} recorded resales ({s}%) settled at exactly the ceiling. Those buyers each paid the most the platform allows, so the record shows what was paid, not what buyers would have paid, and every sale the ceiling turned away is missing from it entirely.` followed by `Value: at least {m} SOL per ticket. That is a floor, not an estimate.` and `Range: {P_lo} SOL and up. We do not state an upper bound from this record.` | **capped-and-binding events (`02-b` §3.4). This trio replaces A14 and replaces `02-d` §6's "we would not argue with any price in that range", which may not be printed on a binding event.** |
| A20 | `This tier has a resale cap and no sale has reached it. We cannot tell from this record whether the cap binds: the absence of a sale at the ceiling is not evidence that the ceiling does not bind.` | a capped event with no mass point (`02-b` §3.1) |
| A15 | `The platform does not record asking prices, so we cannot estimate the chance a ticket sells at a specific price. What is shown is what actually happened.` | the refusal panel (`02-c` §7.2.4) |
| A16 | `At the cap — a rationing point, not a market-clearing price.` | a cap-hit mark |
| A17 | `The model is not fitted. {n_events} events have completed in the observation window and {m} have any resale activity, so the between-event dispersion cannot be estimated and no out-of-sample score exists. What follows is the pooled prior with its width declared, not estimated.` | the insufficient-evidence state (`03-b` §6.5) |
| A18 | `One ticket sold twice: {p1} → {p2} SOL over {d} days. One pair is a fact, not an index.` | the repeat sale |

**Prohibited.** A literal match of any of these, in the page's visible text or in any JSON string field, is
a test failure. `ticketpath/core/labels.py` exports the pattern list; `tests/test_labels.py` asserts that no
allowed sentence matches any pattern. **The patterns are phrases, not single words**, and each negative form
the page needs is allowed by name (`no program is deployed`, `no devnet transaction`, `not deployed`,
`we do not state an upper bound`) — a grep for the bare word `deployed` would fail on the sentence that makes
the page honest.

| ID | Prohibited | Why |
|---|---|---|
| X1 | `This ticket has an X% chance of selling at price p.` | the T3 crux; the price-specific sale probability is not identified. **The sentence this build exists to remove.** |
| X2 | `The probability this ticket sells at price p is X%.` | same prohibition, the review's table form |
| X3 | `The engine knows what this ticket is worth.` | the level is set-identified at best |
| X4 | `The demand curve is ...` / `the price elasticity is ...` | the resale demand curve is not identified from trades; the primary bracket is one-sided |
| X5 | `The cap correction recovers the true value of the best inventory.` | the correction's size and the sign of the average correction are not established |
| X6 | `Weather, injuries, transfers, competing events and tour stops are irrelevant to pricing.` | excluded from the static price's realisations, not from the reprice or the risk terms |
| X7 | `The sale probability is calibrated.` | the indicator is; no price distribution is |
| X8 | `The resale ledger is complete.` | complete only conditional on enforcement |
| X9 | `The 41% markup is what the whole market earns.` | Leslie & Sorensen observe half of resale activity |
| X10 | `The engine finds the revenue-maximising primary price.` | the optimum is a set with a sensitivity map |
| X11 | `The cap is the central structural fact of the project.` | the missing listing exposure is the first constraint |
| X12 | `The asking-versus-realised gap has been measured.` | there is no ask anywhere in the record |
| X13 | `The primary price should be raised to the cap because the cap proves demand exceeds it.` | the cap is also a ceiling on the buyer's outside option |
| X14 | any sentence of the form `{price} is what this ticket is worth` | X3 |
| X15 | `market price`, `live price`, `real-time price` applied to a recorded sale | it is a recorded transaction, not a quote |
| X16 | `prediction` / `forecast` / `expected price` applied to the band or the recommendation — except in A12 and A13, whose whole point is to deny it | the output is a bound and a recommendation |
| X17 | `90% likely`, `calibrated to`, `accurate to ±`, `confidence: high` | no coverage claim is available |
| X18 | `deployed`, `on-chain`, `verified on Solana` **as a claim about this project's program or mint**, unless the `[DEVNET]` slot is in its verified state. The negative forms are required, not banned: `no program is deployed`, `no on-chain transaction`, `not deployed` | the honesty boundary |
| X19 | `comparable events` | comparability is untested (`02-e` §2.3) |
| X20 | `probability of sale`, `chance it sells`, `liquidity score`, `sell-through forecast` | banned labels (`02-c` §7.3) |

### 2.7 How the rule is enforced, not merely stated

Three tests, all in the suite that runs before the freeze:

1. **`tests/test_labels.py`** — every allowed ID renders with sample fields; no allowed sentence matches
   any entry in `BANNED_PATTERNS`; the exact string of X1 is a member of the pattern list, so deleting the
   prohibition breaks a test.
2. **`tests/test_console_page.py`** — renders the page for every state the page can be in (capped and
   binding, uncapped, capped with no mass point, cold start, an `asOf` before any sale, a candidate cap of
   0) and asserts: the banner is first; every number block's first text
   is a badge; no `title=`; the five mandatory sentences T1–T5 are present where required; no
   `BANNED_PATTERNS` match in the stripped visible text.
3. **`tests/test_guidance_api.py`** — walks the payload recursively and fails on any `int`, `float` or
   numeric string leaf without sibling `badge`, `basis`, `labelId`; and asserts `saleProbability is None`
   with `reason == "not_identified"` in every state, including the ones where a recommendation exists.

---

## 3. Module layout

One responsibility per file, and the file name says the job. Existing files are extended, not replaced;
new files are marked **NEW**. Line budgets are part of the design: a file that exceeds its budget is a
design error, not a budget error.

The dependency rule is one line: **`server` → `api`/`console` → `orchestrator` → (`core` | `adapters`)**,
and `core` imports nothing from `api`, `console`, `adapters`, `orchestrator` or `server`. `labels` is
imported by `api` and `console` only; `core` returns label **IDs**, never sentences.

| # | File | Job | State | Budget |
|---|---|---|---|---|
| 1 | `ticketpath/server.py` | the HTTP edge: routes, CORS, errors, serialisation | extend | +60 |
| 2 | `ticketpath/api/guidance.py` | marshal the engine output into the console payload, attaching badges and basis | **NEW** | 180 |
| 3 | `ticketpath/core/price_features.py` | ledger rows + a mandatory cut → features; no aggregates, no ambient clock | **NEW** | 220 |
| 4 | `ticketpath/core/value_band.py` | the three regimes, the one fitted estimator, the declared prior, and the bound on a capped event | **NEW** | 260 |
| 5 | `ticketpath/core/path_model.py` | deadline-convex curvature with a martingale fallback and named refusals | **NEW** | 200 |
| 6 | `ticketpath/core/intensity.py` | the composite transaction rate, competing risks, gamma–Poisson cold start | **NEW** | 160 |
| 7 | `ticketpath/core/primary_optimum.py` | the boundary recommendation, the fee wedge, the consequence table, the refusals | **NEW** | 220 |
| 8 | `ticketpath/core/labels.py` | the sentence registry and the banned patterns | **NEW** | 160 |
| 9 | `ticketpath/adapters/ledger_adapter.py` | read and validate the store; refuse an unlabelled one | extend | +0 |
| 10 | `ticketpath/adapters/rpc_adapter.py` | read-only chain status; 2 s timeout; never claims a deployment | extend | +90 |
| 11 | `ticketpath/adapters/pricing_model_adapter.py` | the model seam; registers the engine; forces `saleProbability: null` | extend | +40 |
| 12 | `ticketpath/adapters/chain_client.py` | the on-chain client stub: builds, never signs, never sends | **NEW** | 90 |
| 13 | `ticketpath/onchain/sim.py` | the SIMULATED state machine, executable and tested | **NEW** (moved from `docs/ON-CHAIN-DESIGN.md` §9.1) | 260 |
| 14 | `ticketpath/console/page.py` | the HTML page: one render function, no framework, no CDN | **NEW** | 320 |
| 15 | `ticketpath/orchestrator.py` | route and assemble; calculate nothing | extend | +110 |
| 16 | `tools/guidance.py` | CLI: print the console payload as JSON for a URL's parameters | **NEW** (outside the package) | 60 |
| 17 | `tools/devnet_check.py` | verify a signature against devnet and write the artefact file | **NEW** (outside the package) | 140 |

`stdlib only` is a hard constraint (D2). The import allowlist in `tests/test_boundaries.py` gains `html`,
`re` and `math`; `urllib` gained by `adapters/rpc_adapter.py` and by `tools/` only.

### 3.0 The tie to `lib/types.ts`

Every feature is either a field of a wire type or a count over truncated rows of one. Nothing is invented
and nothing is read from an aggregate. This table is the contract between the engine and
`records/CONTRACT-MAP.md` §4 and must be checked line by line at review.

| Feature field | Wire source | Rule |
|---|---|---|
| `eventId`, `startsAt`, `endsAt`, `city`, `status` | `Event` | copied; `status` is used only to display the event's state, never as a feature (`03-b` row 5) |
| `capBpsRecorded` | `Event.resalePriceCapBps` | the cap **in force when the sale was recorded**; `null` is its own branch, never `0` |
| `tierId`, `name`, `faceValueLamports`, `totalSupply`, `issuedCount` | `Event.tiers[]` (`TicketTier`) | copied; `faceValueLamports` is a normaliser and an offset, never a regressor on the right-hand side (`03-b` row 19) |
| `ticketId`, `issuedAt` | `Ticket.id`, `Ticket.issuedAt` | the contract defines `Ticket.issuedAt` as the `issue` row's `occurredAt`, so either read is the same fact; the engine uses the row |
| `marks[].priceLamports`, `markupBps`, `occurredAt` | `LedgerEntry` with `kind == "sale"` | **computed by the engine from the raw rows**, never taken from `ResaleStats` or `EventAnalytics` |
| `marks[].tierFaceLamports` | `TicketTier.faceValueLamports` | the ticket's own tier, never an event-level face (`CONTRACT-MAP.md` §4.4) |
| `marks[].daysToEvent` | `Event.startsAt` and `LedgerEntry.occurredAt` | ISO-8601 UTC parsed strictly; a negative value is a bug, asserted |
| `atCeilingCount` | `Event.resalePriceCapBps` and `marks[].markupBps` | `abs(markupBps − capBpsRecorded) <= 1` (`03-b` row 16) |
| `exposureTicketDays` | `LedgerEntry` `issue` and `redeem` rows, `Ticket.redeemedAt` **not read** | `min(asOf, redeemRow) − issueRow`; a ticket whose issue is after `asOf` contributes zero |
| `signature`, `slot` | `LedgerEntry.signature`, `.slot` | null in every fixture row; passed through to `provenance.nullSlotRows` and never used as a feature |

Fields on the forbidden list, and the reason, in one place: `EventAnalytics.*` and `ResaleStats.*` are
whole-history aggregates with no stated as-of and no window parameter in the contract (`03-b` §4 T2);
`Ticket.lastSalePriceLamports`, `.transferCount`, `.status`, `.ownerWallet`, `.redeemedAt` are either
whole-life aggregates or current-state fields that leak the future into a past cut. The engine reads raw
rows and nothing else. A static grep over `ticketpath/core`, `ticketpath/api` and `ticketpath/console`
enforces it, and the grep's allowlist is empty.

### 3.1 `ticketpath/server.py` — the HTTP edge

```python
def resolve_port(env: Mapping[str, str]) -> int                     # refuses 8787
def make_server(port: int, host: str, orchestrator: Orchestrator) -> HTTPServer
ROUTES: tuple[tuple[str, tuple[str, ...], Handler], ...]            # ("GET", ("",), console_index)
def console_index(o: Orchestrator, path: str, query: dict, body: bytes) -> tuple[int, str]
```

Inputs: the raw query string. Outputs: `(status, body)` where `body` is a `str` for the console and a
`dict` for JSON routes; the existing serialiser picks. The console route is `GET /` and nothing else: it
must not be under `/api`, because it is not a contract endpoint (`CONTRACT-MAP.md` §9.2). Also answers
`GET /favicon.ico` with 204, so the video never records a 404.

May import: `http`, `urllib`, `json`, `os`, `sys`, `traceback`, `ticketpath.orchestrator`,
`ticketpath.api.*`, `ticketpath.console.page`, `ticketpath.errors`. May not: `ticketpath.core.*` directly
(the orchestrator owns that), any arithmetic beyond the port.

Test: `tests/test_http_contract.py` (unchanged, all nine contract routes still answer),
`tests/test_contract_conformance.py` (the executed contract, 22 tests — it must keep passing untouched),
plus `tests/test_console_route.py::test_root_serves_html_with_banner` and
`test_api_prefix_unchanged` (the nine contract routes still start `/api`, and `/` is not one of them).

### 3.2 `ticketpath/api/guidance.py` — the marshalling

```python
def build(
    *,
    event: Mapping,
    tiers: Sequence[Mapping],
    features: Mapping,          # price_features.EventFeatures
    band: Mapping,              # value_band.ValueBand, per tier
    path: Mapping,              # path_model.PathEstimate, per tier
    intensity: Mapping,         # intensity.IntensityEstimate, per tier
    recommendation: Mapping,    # primary_optimum.PrimaryRecommendation, per tier
    as_of: str,
    data_source: Mapping,
    params: Mapping,            # capBps, feeLamports, tau, sellThroughFloor
) -> dict                       # the console payload; every leaf carries badge/basis/labelId
```

Payload shape, top level: `{ "consoleVersion", "asOf", "event", "tiers", "decision", "market",
"refusals", "chain", "labelsShown", "dataSource", "params", "canonicalUrl" }`. Per tier:
`{ "tierId", "name", "faceValueLamports", "band": {...}, "recommendation": {...}, "market": {...},
"refusal": {...} }`. It attaches badges; it computes nothing — every number arrives computed.

May import: `ticketpath.core.labels`, `ticketpath.core.pagination` (for nothing else), `datetime`,
`typing`. May not: `ticketpath.core.*` numeric modules, adapters, the orchestrator, `math`.

Test: `tests/test_guidance_api.py` — the recursive labeller walker; `saleProbability is None`; the four
refusal states each produce a payload that renders; every `labelId` exists in `labels.ALLOWED_IDS`.

### 3.3 `ticketpath/core/price_features.py` — features with a mandatory cut

```python
def build(
    *,
    events: Sequence[Mapping],
    tickets: Sequence[Mapping],
    ledger: Sequence[Mapping],
    tier_faces: Mapping[str, int],
    event_id: str,
    as_of: datetime,
) -> dict
```

`as_of` has **no default** (`03-b` checklist row 1). Truncation happens once, at the top, on
`occurredAt <= as_of` (`row 2`); when `slot` is not null it is the primary key and `occurredAt` breaks ties
(`row 3`); a post-sort assertion that every delta is `>= 0` (`row 4`); the count of rows with a null `slot`
is returned in `features["provenance"]["nullSlotRows"]`, because the fixture's slots are all null and the
fallback must be visible rather than silent. No `datetime.now()` (`row 10`, and `test_boundaries` already
forbids it in `core`).

Output shape:

```
EventFeatures = {
  eventId, asOf, startsAt, endsAt, city, status, capBpsRecorded: int|null,
  tiers: [TierFeatures], event: {sales, tickets, exposureTicketDays, firstSaleAt, lastSaleAt},
  provenance: {nullSlotRows, rowsConsidered, rowsAfterCut, discarded: [reason]}
}
TierFeatures = {
  tierId, name, faceValueLamports, totalSupply, issuedCount, sellThrough: float,
  capBpsRecorded: int|null, capCeilingLamportsRecorded,
  marks: [SaleMark], atCeilingCount, belowCeilingCount,
  highestRecordedLamports, lowestRecordedLamports,
  exposureTicketDays: float, firstMarkAt, lastMarkAt,
  daysToEventAtFirstMark, daysToEventAtLastMark, timeSpreadDays
}
SaleMark = {
  ticketId, priceLamports, markupBps, occurredAt, daysToEvent: float,
  atCeiling: bool,           # abs(markupBps - capBpsRecorded) <= 1   (03-b row 16)
  tierFaceLamports
}
```

**The candidate cap is not a feature.** `atCeiling` is judged against the cap in force when the sale was
recorded, and `capBpsRecorded is None` is its own branch, never a comparison against null. A sale recorded
under a 2500 bps policy stays a cap sale when a judge sets the candidate cap to 0, because the
classification is a fact about the past and the candidate is a rule about the future. The candidate travels
from the request to `value_band` and `primary_optimum` and to nothing else.

May import: `datetime`, `math`, `typing`, `ticketpath.core.timeutil`. May not: any adapter, any
`EventAnalytics` or `ResaleStats` field, `Ticket.lastSalePriceLamports`, `Ticket.transferCount`,
`Ticket.status`, `Ticket.ownerWallet`, `Ticket.redeemedAt` (`03-b` §4 T2 row 5), `datetime.now`.

Tests: `tests/test_price_features.py` — prefix invariance over every cut instant in the fixture (property
test, `row 8`); the future canary (append a sale at 3× the price one hour after the cut, assert
bit-identical features, `row 7`); no negative durations; the ±1 bp cap tolerance on a face that does not
divide evenly; the forbidden-path grep; `as_of` has no default (inspect the signature).

### 3.4 `ticketpath/core/value_band.py` — the regimes, the one estimator, and the bound

```python
def classify(*, features: Mapping, tier_id: str) -> dict        # regime, share_at_ceiling, counts
def estimate(
    *,
    features: Mapping,
    tier_id: str,
    tau: float,                        # declared, 0.10 .. 0.406
    cap_bps_candidate: int | None,     # forward policy; default = the recorded cap
    prior: Mapping,                    # {"muLogRatio": 0.2612, "sigma": 0.406, "source": "02-e §4.7"}
    z: float = 1.6449,                 # 90% two-sided
) -> dict
def prior_only(*, face_lamports: int, tau: float, prior: Mapping, label_id: str) -> dict
```

**Step 0, the regime** (`02-b` §3.1, adopted verbatim). `capped and binding` = the recorded cap is non-null
and `atCeilingCount > 0`. `capped, no mass point` = the cap is non-null and `atCeilingCount == 0`; the page
prints A20, because a zero mass point is not evidence that the cap does not bind. `uncapped` = the recorded
cap is null, the only regime in which the top of the distribution is sampled. `no resale` = no priced mark
at or before the cut. The regime is computed from the record and **never** from the candidate cap.

**Terminology, used exactly** (`02-b` §1.3): the settled-price distribution is **truncated** at the ceiling,
not censored — a sale above the ceiling does not produce a row. A sale that settles *at* the ceiling is a
**one-sided observation of latent value** (`V >= p`), not a measurement of it, and the field is named
`atCeiling`, never `censored`. `SaleMark.atCeiling` is `abs(markupBps - capBpsRecorded) <= 1`.

**Then, by regime:**

1. **`capped and binding`.** No mean, no upper quantile, no band, no upper bound (`02-b` §3.2, §3.4). The
   value is `floorLamports = highestRecordedLamports`, which is the ceiling when a row sits on it and is
   still a valid pointwise lower bound (`02-b` §2 B1) when it is not. Output `band: {loLamports:
   floorLamports, hiLamports: null, noUpperBound: true}`, `labelId: "A19"`, `basis: "lower_bound_at_cap"`.
   The page prints A19's three sentences and nothing that looks like an upper end.
2. **`uncapped`.** `n >= 2` -> `ybar = mean(log(price/face))` over the marks, `lo/hi = ybar -/+ z*tau`
   converted at the tier face, `basis: "tier_marks"`, `labelId: "A2"` with A14. `n == 1` -> blend
   halfway to the event mean when the event has `>= 2` marks, `basis: "blended"`. `n == 0` in the tier but
   `>= 2` in the event -> `ybar = the event mean`, `basis: "pooled_across_tiers"`, and the page says the
   tier has no record of its own. `n == 0` everywhere -> `prior_only`, and `primary_optimum` refuses.
3. **`capped, no mass point`.** As `uncapped`, with two differences: `hi = min(hi, recordedCeiling)` and
   `topIsCeiling: true`, because no recorded price can exceed the ceiling; and A20 is printed beside the
   band, because the ceiling may or may not bind and the record cannot say.

**The candidate cap never truncates the band below a price the record already paid.** If any recorded sale
in the tier exceeds the candidate's ceiling, the band is left where the record put it, `capViolations` is
returned, and the page prints the violation sentence in place of any ceiling line; a band that excluded a
recorded price would be a band the data has already refuted. The band is never narrower than the declared
floor: if `hi - lo < 2*z*0.10` in logs, widen and set `widenedToFloor: true`.

**Tau sensitivity.** The four-row table from `02-e` §4.7 (0.10 / 0.20 / 0.30 / 0.406) is returned with the
band so the page can print it, on the two regimes that have a band. On `capped and binding` the table is
returned with `applicable: false` and the reason `no upper tail in this record`.

Output: `{regime, shareAtCeiling, atCeilingCount, level: {available, logRatio, lamports, basis, n},
floorLamports, band: {loLamports, hiLamports, noUpperBound, topIsCeiling, recordedCeilingLamports,
widenedToFloor, tau, widthSource}, range: {...}, capViolations: {count, of}, sensitivity: [...],
labelId}`.

May import: `math`, `typing`, `ticketpath.core.price_features` (for the type only). May not: any
adapter, any aggregate field. `statistics` is not imported: the sample SD is not used, because the width is
declared and not estimated.

Tests: `tests/test_value_band.py` — the three regimes classify correctly on the fixture's three event
shapes; on a binding event `band.noUpperBound is True` and `hiLamports is None`, and **the test fails if any
mean, upper quantile or `hiLamports` is returned in that regime**; on an uncapped event the band contains
the point estimate; on a no-mass-point event `hi <= recordedCeiling` and A20 is selected; a candidate cap
below a recorded price leaves the band untruncated and reports the violations; `n == 0` -> `prior_only`;
`n == 1` -> `blended`; monotone width in tau on the regimes that have a band, and `applicable: false` on the
binding one; the golden snapshot of §4.7.

### 3.5 `ticketpath/core/path_model.py` — one parameter, and the refusals

```python
def estimate(
    *,
    features: Mapping,
    tier_id: str,
    anchor_lamports: int,
    horizon_days: Sequence[int] = (28, 14, 7, 2, 0),
) -> dict
```

Guards, checked in this order, each returning `available: False` with the listed reason: `n_marks < 4` →
`insufficient_marks`; `time_spread_days < 5` → `insufficient_time_spread`; the 2×2 normal matrix singular
→ `degenerate_design`. If it fits, `θ̂` is the within-event curvature from `02-a` §8.3 (exactly its 2×2
solve, no matrices beyond 2×2) and the estimate is reported at both `ω = 0` and `ω = 1` as a bracket. If it
does not fit, the returned object is the martingale: a flat path at `anchor_lamports`, `available: False`,
`basis: "martingale"`, and the page prints the refusal *and* the flat path, labelled as the benchmark.

Output: `{available, reason, theta, omega0, omega1, anchorLamports, points: [{days, lamportsLower,
lamportsUpper}], labelId}`.

May import: `math`, `typing`, `ticketpath.core.price_features`. May not: any adapter.

Tests: `tests/test_path_model.py` — every guard's reason code; the martingale equals the anchor at every
horizon; both ω ends bracket the anchor; a hand-built ledger with four marks over 2 days produces
`insufficient_time_spread`, and one with four marks over 20 days fits.

### 3.6 `ticketpath/core/intensity.py` — the composite rate

```python
def estimate(*, features: Mapping, tier_id: str, prior: Mapping | None = None) -> dict
```

Exposure is the sum over the tier's tickets of `min(as_of, redeem_row) − issue_row`, in days, from the raw
`issue` and `redeem` ledger rows only — **`Ticket.redeemedAt` is not read** (it is a current-state field on
the forbidden list, `03-b` §4 T2). `salesPerTicketDay = sales / exposure`; `causeSpecific` counts
sale/transfer/redeem/revoke as competing exits (`03-b` row 18). At zero exposure, refuse with
`no_exposure`. The cold-start branch is gamma–Poisson with a declared prior, posterior mean `a/(b+E)`, not
`a/b` (`02-c` §1.8), and it requires that events with zero sales are inside the variance estimate. When the
event population is below `03-b` §6.4's floor, the page prints the counts and the word `insufficient` rather
than a rate with a prior dressed as a measurement.

Output: `{available, reason, sales, exposureTicketDays, salesPerTicketDay, per1000TicketDays,
causeSpecific, basis, labelId}`.

May import: `math`, `typing`, `ticketpath.core.price_features`. May not: any aggregate.

Tests: `tests/test_intensity.py` — the denominator is exact on a hand-built 3-ticket ledger (3 tickets, 6.0
ticket-days at a stated cut); rate equals sales/exposure; a redeemed ticket stops contributing at its redeem
row; a ticket issued after `as_of` contributes zero; `no_exposure` at an empty tier. **No assertion on the
fixture's ticket counts**, because the fixture is regenerated.

### 3.7 `ticketpath/core/primary_optimum.py` — the recommendation and the four refusals

```python
def recommend(
    *,
    features: Mapping,
    tier_id: str,
    band: Mapping,
    intensity: Mapping,
    fee: Mapping | None,             # {"perTicketLamports": int, "adValoremBps": int} or None
    sell_through_floor: float | None,
    candidates: Sequence[int] | None = None,
) -> dict
```

Rules, in order, by regime:

1. `band["regime"] == "no resale"` -> `refused: True`, `refusalCode: "no_resale_record"`,
   `requiredInputs: ["a completed resale on this event"]`.
2. `band["regime"] == "capped and binding"` -> the recommendation is `band.floorLamports`,
   `bandLamports: [floor, None]`, `noUpperBound: True`, `basis: "lower_bound_at_cap"`, `labelId: "A19"`.
   There is **no point estimate and no upper end** in this regime: the page prints "at least {floor} SOL"
   and "and up", and a test fails if `recommendedLamports != floor` or if any upper end is returned.
3. Otherwise (`uncapped` or `capped, no mass point`) -> the recommendation is `band.level.lamports`,
   `bandLamports: [band.lo, band.hi]`, `basis: band.level.basis`, `labelId: "A2"` with A14. If the level
   came from the prior (`prior_only`), refuse instead: a prior is not a record and may not be printed as
   a primary price (`02-e` §6.2(4)).
4. The **consequence table** is exact arithmetic and always present when a sell-through observation exists:
   for each candidate `c`, `requiredSellThrough = observedRevenuePerOfferedSeat / c`, where
   `observedRevenuePerOfferedSeat = face × sellThrough`. It is labelled `[EXACT]` and it is not a
   forecast. On a binding event the table is anchored at the floor and says so.
5. The **interior optimum is always refused** unless `fee` and `sell_through_floor` and a demand response
   exist: `refusalCode: "no_demand_response"`, `requiredInputs: ["eta", "q_min", "a completed sell-through
   series"]`. There is no code path that returns an interior optimum tonight, and a test asserts the
   refusal is unconditional.
6. **Net revenue** requires `fee`; without it, `netRevenue: None`, `refusalCode: "no_fee_model"`, and the
   recommendation is still returned (the band is fee-neutral for an ad-valorem fee; retract only the net
   line).

Output: `{recommendedLamports, bandLamports, basis, refused, refusalCode, requiredInputs, consequence:
[{candidateLamports, requiredSellThrough}], netRevenue: {perTicket, perTier} | None, labelId}`.

May import: `math`, `typing`, `ticketpath.core.price_features`. May not: any adapter, any
grid search (there is no likelihood to maximise; a grid would manufacture one).

Tests: `tests/test_primary_optimum.py` — each refusal code reachable; on a binding event the recommendation
equals the floor and `noUpperBound` is true; on an uncapped event the recommendation lies inside the band;
`requiredSellThrough` exact to 1e-6; a fee changes only the net line; no code path returns an interior
optimum; `prior_only` is refused rather than priced.

### 3.8 `ticketpath/core/labels.py` — the sentences

```python
ALLOWED_IDS: frozenset[str]
BANNED_PATTERNS: tuple[re.Pattern[str], ...]
FEES: Mapping[str, str]     # human-readable reason strings for refusal codes
def render(label_id: str, **fields: object) -> str          # raises KeyError on an unknown id
def contains_banned(text: str) -> str | None                # returns the first matching pattern's source
```

Holds T1–T5, A1–A20 and the X1–X20 patterns. No formatting beyond `str.format`. It holds no numbers.

May import: `re`, `typing`. May not: anything else in the package.

Tests: `tests/test_labels.py` — see §2.7.

### 3.9 `ticketpath/adapters/ledger_adapter.py` — unchanged

Already refuses an unlabelled store, a priced transfer, and an owner/trail mismatch
(`tests/test_ledger_adapter.py`). The build adds one method only: `raw_sales_for_event(event_id)` returning
the unshaped rows, because the feature module must read raw rows rather than shaped payloads.

May import: `json`, `os`, `pathlib`, `typing`. May not: any `ticketpath.core` numeric module, the
orchestrator, `datetime` (timestamps are parsed by core), `math`. It is the only module that reads a file
from disk, and the file must declare `meta.synthetic: true` or it is refused.

### 3.10 `ticketpath/adapters/rpc_adapter.py` — read-only chain status

```python
def chain_status(self, *, refresh: bool = False, timeout_s: float = 2.0) -> dict
def program_status(self) -> dict
def transfer_enforcement(self, mint_address: str) -> dict
```

`chain_status` returns `{checked, cluster, rpcUrl, at, slot, programDeployed: False, programId: None,
reason}` and is the only function in the package allowed to open a socket. It is off unless
`TICKETPATH_RPC_ENABLED=1`; a `URLError`, a timeout or a non-200 returns `{checked: False, reason:
"rpc_unreachable"}` rather than raising. It performs exactly two reads: `getHealth` and
`getAccountInfo(programId)` when an id is configured, and nothing when one is not. It never writes.

May import: `json`, `os`, `urllib`, `typing`. May not: any core module, `chain_client`, `subprocess`.

Tests: `tests/test_rpc_adapter.py` — disabled → `checked: False, reason: "rpc_disabled"`; a configured but
unreachable endpoint → `rpc_unreachable` within 3 s; no configured program → `programDeployed: False` and
`programId: None`; the boundary test is amended so `urllib` appears in exactly one file.

### 3.11 `ticketpath/adapters/pricing_model_adapter.py` — the seam, now with a model

```python
def register(self, model: Model, version: str) -> None
def estimate(self, request: Mapping) -> dict
```

The build registers the composite engine as the one model, version `engine-2026-11-07`. Two invariants are
enforced here rather than described: `saleProbability` is set to `None` and `saleProbabilityReason` to
`"not_identified"` **after** the model returns, whatever the model said; and a missing required key still
raises. `status()` reports `available: True, modelVersion: "engine-2026-11-07"`, and `/health` therefore
stops saying `no_model_registered` — which is true, because a model now exists. `TestHealth` is updated in
the same commit to assert `pricingModel.available is True`, the version string, and that `chain` still says
`programDeployed: False` with `programId: None`: registering a model must not make the health block look
like a deployment.

Tests: `tests/test_pricing_model_adapter.py` — a model that returns `saleProbability: 0.5` is overridden to
`None`; the reason is `not_identified`; a missing key raises; with no model registered the old refusal is
unchanged.

### 3.12 `ticketpath/adapters/chain_client.py` — the on-chain client stub

```python
def available(self) -> bool                                  # always False in this build
def quote_commit(self, *, quote_id: str, recommendation: Mapping, mint: str | None) -> dict
def submit(self, payload: Mapping) -> dict                   # raises ChainUnavailable
```

`quote_commit` computes `sha256` over a canonical JSON serialisation of
`{quoteId, eventId, tierId, recommendedLamports, asOf, modelVersion}`, and returns
`{available: False, reason: "no_toolchain_no_keypair_no_program", memoText, quoteHash, instructions:
[{"program": "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr", "data": memoText}], serialized: None}`. It holds
no key material, imports no network module, and has no code path that returns a signature.

> **Superseded (2026-11-08T07:05Z), for the `instructions` field only.** `quote_commit` now takes
> a `cluster` and names that cluster's id from `MEMO_PROGRAMS`, so the `MemoSq4gq…` in the entry
> above is wrong for the default cluster: devnet's measured id is `Memo4c2p…`. A caller that has
> already resolved the id passes `memo_program=`. The signature above is otherwise unchanged.
> `records/findings/40-memo-program-id.md` §2 has the measurement and the correction that dates
> from the same pass.

May import: `hashlib`, `json`, `typing`. May not: `urllib`, `subprocess`, `os` (no env keypath).

Tests: `tests/test_chain_client.py` — the hash is deterministic and equals `tools/devnet_check.py`'s
hash over the same fields; `available()` is False; `submit` raises; the module contains the string
`signature` nowhere in a return value.

### 3.13 `ticketpath/onchain/sim.py` — the simulated state machine

```python
def run(arms: Sequence[str] = ("cap", "unstaged", "unverified", "theorem")) -> list[dict]
```

Each line: `{arm, status: "ok"|"refused", code: int|None, name: str, detail: str, simulated: True}`. Moved
from `docs/ON-CHAIN-DESIGN.md` §9.1 so it is executable, tested and importable by the page. Codes are the
document's: 6004 tier exhausted, 6009 transfer not staged, 6010 cap exceeded, 6012 destination unverified,
6013 ticket not valid, 6018 verification expired.

Tests: `tests/test_onchain_sim.py` — `cap-1` and `cap` admitted, `cap+1` refused with 6010; an unstaged
custody move refused with 6009 and the record unchanged; an unverified destination refused with 6012 and
admitted after verification; every line has `simulated is True`; the markup theorem over a sweep of
`(face, cap, price)` triples.

### 3.14 `ticketpath/console/page.py` — the page

```python
def render(payload: Mapping) -> str
def render_error(*, status: int, message: str, code: str) -> str
```

One function, one string, no template engine, no external asset. **No JavaScript is required for any number,
any label or any state:** every control is a plain `<form method="get">` submit. At most one small inline
script may assemble the query string for the `Recompute` button, and the page must remain fully operable
with scripts disabled. All interpolation goes through `html.escape`. Every static sentence comes from
`labels.render`.

May import: `html`, `json`, `typing`, `ticketpath.core.labels`. May not: `ticketpath.core` numeric modules,
adapters, the orchestrator, `math`.

Tests: `tests/test_console_page.py` — §2.7 item 2, plus: no `http://` or `https://` asset reference except
the devnet explorer link when the slot is verified; every form input has a `name` and a `label`; the four
states render without exception; the visible text has no `BANNED_PATTERNS` match.

### 3.15 `ticketpath/orchestrator.py` — routes, does not calculate

```python
def price_guidance(
    self, *, event_id: str, tier_id: str | None, as_of: str | None,
    cap_bps: int | None, fee_lamports: int | None, tau: float | None,
) -> dict
```

It parses and validates the parameters, resolves the clock once (`as_of` or `self.now()`), calls
`price_features.build`, then per tier `value_band.estimate`, `path_model.estimate`, `intensity.estimate`,
`primary_optimum.recommend`, then `api.guidance.build`, then attaches `dataSource` and `canonicalUrl`. It
contains no arithmetic beyond defaulting a parameter, and the test proves it by monkeypatching each core
function to return a sentinel dict and asserting the sentinel arrives unmodified.

Tests: `tests/test_orchestrator_guidance.py` — sentinels pass through; a bad `capBps` is a 400 with
`code: "cap_invalid"`; a bad `asOf` is a 400 with `code: "as_of_invalid"`; an unknown event is a 404.

### 3.16 `tools/guidance.py` and `tools/devnet_check.py` — outside the package

`tools/guidance.py` prints the console payload for a URL's query string, so the whole surface is
CLI-drivable and batch-testable (R64): `python3 tools/guidance.py --event <event-id> --tier <tier-id>
--as-of 2026-11-07T12:00:00Z --cap <bps> --fee 0 --tau 0.20`. The ids are whatever the store holds; the CLI
lists them with `--events` rather than documenting a value that the generator can change.

`tools/devnet_check.py` is the only thing that may write `records/devnet-artefacts.json`. It takes
`--signature`, `--cluster devnet`, `--quote-hash`, calls `getTransaction`, and writes the record **only if**
the transaction exists, has a `blockTime`, and the memo string contains the quote hash. It exits non-zero and
writes nothing otherwise. It is run by the operator, once, on the machine that holds the keypair, or by the
operator's laptop step and copied. The console never calls it.

Tests: `tests/test_tools.py` — `guidance.py` output parses as JSON and equals the in-process payload for the
same parameters; `devnet_check.py` with a bogus signature writes nothing and exits 1.

May import: `argparse`, `json`, `sys`, `urllib`, `pathlib`, and the package's `chain_client` for the hash.
May not: write anything except `records/devnet-artefacts.json` (and only after verification), or touch
the package's internals beyond `chain_client.quote_commit`.

---

## 4. The pricing path, end to end

One call chain, seven steps, every shape named. The worked numbers in §4.7 are a snapshot of the current
fixture and are labelled as such.

```
GET /  (or /?event=…&tier=…&asOf=…&capBps=…&feeLamports=…&tau=…)
  → server.console_index
  → orchestrator.price_guidance
      → adapters.ledger_adapter.raw_sales_for_event        (raw rows, no shaping)
      → core.price_features.build                          (features, with the cut applied once)
      → core.value_band.estimate                           (level + declared band + cap truncation)
      → core.path_model.estimate                           (curvature or martingale + refusal)
      → core.intensity.estimate                            (composite rate + exposure)
      → core.primary_optimum.recommend                     (boundary + consequence table + refusals)
      → api.guidance.build                                 (badges, basis, label IDs)
      → console.page.render                                (HTML)
```

### 4.1 Step 1 — ledger rows in

In: the wire types of `lib/types.ts` as served by `ledger_adapter`, unshaped: `Event` (`id`, `startsAt`,
`endsAt`, `city`, `status`, `resalePriceCapBps`, `tiers[]` with `faceValueLamports`, `totalSupply`,
`issuedCount`), `Ticket` (`id`, `eventId`, `tierId`, `faceValueLamports`, `issuedToWallet`, `ownerWallet`,
`issuedAt`), and `LedgerEntry` (`id`, `ticketId`, `kind`, `fromWallet`, `toWallet`,
`priceLamports`, `markupBps`, `signature`, `slot`, `occurredAt`).

Out: nothing yet. **No aggregate is read.** `EventAnalytics`, `ResaleStats`, `Ticket.lastSalePriceLamports`,
`Ticket.transferCount`, `Ticket.status`, `Ticket.ownerWallet`, `Ticket.redeemedAt` are on the forbidden list
(`03-b` §4 T2) and a static test greps for them.

### 4.2 Step 2 — features computed

In: rows, `event_id`, `as_of`. Out: `EventFeatures` / `TierFeatures` / `SaleMark` as in §3.3. Every field is
either a raw value or a count over truncated rows. `atCeiling` is `abs(markupBps − capBpsRecorded) <= 1`,
and `capBpsRecorded is None` is its own branch, never a comparison against null.

### 4.3 Step 3 — value: a regime, then a bound or a band

In: `TierFeatures`, `tau`, the prior, the candidate cap. Out: `ValueBand` (§3.4). The first output is the
regime, because it decides what kind of statement is admissible: on `capped and binding` the value is a floor
and there is no upper end; on `uncapped` and `capped, no mass point` there is a point and a declared band.
The output always carries `basis` and `n`, and on the binding regime it carries `labelId: "A19"` and nothing
that could be read as an upper bound.

**02-b is adopted in full, and it supersedes the earlier cap treatment in this document.** Its §3.4
replacement wording is the binding regime's decision block text; its §3.1 regimes are the page's chips; its
§1.3 terminology is the code's (`atCeiling`, not `censored`; the distribution is *truncated*, the sale at
the ceiling is a *one-sided observation*). Its §1.2 direction-of-bias argument is why the floor is the only
statement: the bias is `s · E[m* − c | m* ≥ c]`, both factors unobserved, so no correction is computable and
none is attempted.

### 4.4 Step 4 — path: fitted, or refused with a reason

In: `TierFeatures`, the anchor. Out: `PathEstimate` (§3.5). Whether it fits is a property of the record's
time spread, not of the code: the guard refuses when the marks span fewer than 5 days, and on a fixture whose
sales are clustered it refuses with `insufficient_time_spread`. Either way the page prints the outcome and,
when it refuses, the flat martingale beside it — `[UNVALIDATED]` on the flat line too, because a flat line
is a model output like any other.

### 4.5 Step 5 — intensity: the one rate that is identified

In: `TierFeatures`. Out: `IntensityEstimate` (§3.6). `sales`, `exposureTicketDays`, `per1000TicketDays`,
`causeSpecific`. The page prints A1 and T4 together, always, and never plots the rate against a price axis
(`02-c` §7.3).

### 4.6 Step 6 — the optimum: a boundary, and the interior refused

In: band, intensity, fee, floor. Out: `PrimaryRecommendation` (§3.7): the recommended price, its band, the
`basis`, the consequence table, and the refusals. **The engine does not compute an interior optimum**, and
the reason is not modesty: `T4b`/`T5` say the primary demand response is not identified, and `03-b` §3.4 D04
records it as unidentified rather than absent. A grid search over a demand curve the engine does not have
would be a fabricated likelihood with a maximum.

### 4.7 Step 7 — the recommendation and its uncertainty, worked on the fixture

**These are a snapshot, not an acceptance criterion.** They were computed at 11:32Z from
`fixtures/synthetic_store.json` as generated by `tools/build_fixture_store.py` (seed `20261107`), `tau = 0.20`,
`asOf` = 2026-11-07T12:00:00Z. The fixture was regenerated twice while this document was being written; the
build pins the live values in a golden test and updates this table in the same commit. **The invariants in
the right-hand column are the acceptance criteria and they hold for any fixture the generator produces.**

**(a) The capped-and-binding event — the product's central case.**

| Quantity | Snapshot | Badge | Invariant the test asserts |
|---|---|---|---|
| regime | `capped and binding` | `[FIXTURE]` | `atCeilingCount > 0` |
| cap / face / ceiling | 1500 bps / 1.20 SOL / **1.38 SOL** | `[EXACT]` | `ceiling = face × (1 + cap/10000)`, exact to the lamport |
| at-ceiling share, General tier | 8 of 9 sales, **88.9%** | `[FIXTURE]` | `share = atCeiling / sales` |
| at-ceiling share, event | 9 of 12 sales | `[FIXTURE]` | same |
| **recommended price** | **at least 1.38 SOL**, `noUpperBound` | `[UNVALIDATED]` | `recommended == ceiling` **whenever a sale sits on the ceiling**, and `hiLamports is None` |
| band | `[1.38, and up]` | `[UNVALIDATED]` | a binding event returns no upper end, no mean, no upper quantile |
| level | **not computed** | `[REFUSED]` | the binding regime never calls the estimator |
| τ | inert, `applicable: false` | `[DECLARED]` | the sensitivity table is `applicable: false` on this regime |
| path | refused (`insufficient_time_spread` if the marks are clustered; the guard is the test) | `[REFUSED]` | the refusal carries a reason code |
| required sell-through at 1.38 | 0.048 / 1.38 = **3.5%** | `[EXACT]` | `face × sellThrough / candidate`, exact |
| sale probability at a price | refused, `not_identified` | `[REFUSED]` | `saleProbability is None` in every state |
| interior optimum | refused, `no_demand_response` | `[REFUSED]` | unconditional |
| net revenue | withheld, `no_fee_model` | `[REFUSED]` | `netRevenue is None` without a fee |

The decision block for this event is A19's three sentences, and the numbers are exactly the ones above.
A judge who asks "why is there no upper bound" gets `02-b` §3.4 in one line: the ceiling turned away every
sale above it, so the top of the distribution is not in the record.

**(b) The uncapped event — the only regime where a range is admissible.**

| Quantity | Snapshot | Badge | Invariant |
|---|---|---|---|
| regime | `uncapped` | `[FIXTURE]` | recorded cap is null |
| marks | 12 sales, one tier, face 0.80 SOL | `[FIXTURE]` | `n = 12` |
| level `ȳ` | `+0.1512` in logs → **0.93 SOL** | `[UNVALIDATED]` | `lamports = face × exp(mean(log(price/face)))`, monotone in the marks |
| band, τ = 0.20 | `0.80 × e^{0.1512 ∓ 0.329}` → **0.67 – 1.29 SOL** | `[UNVALIDATED]` | `lo < level < hi`; width `= 2 z τ` in logs; monotone in τ |
| recommendation | **0.93 SOL**, `basis: "tier_marks"`, A2 + A14 | `[UNVALIDATED]` | `recommended == level`; inside the band |
| τ sensitivity | the four rows of `02-e` §4.7 | `[DECLARED]` | `applicable: true`; widening monotone |

This is the one place the page prints 02-d §6's range line, and it is admissible only because nothing
truncated the record.

**(c) The capped event with no mass point — a range with a warning.**

Same arithmetic as (b), with `hi = min(hi, recordedCeiling)` and A20 printed beside it: *this tier has a
resale cap and no sale has reached it; the absence of a sale at the ceiling is not evidence that the ceiling
does not bind*. The snapshot's three tiers all have caps and none has an at-ceiling sale, so all three print A20 and all
three truncate their band at their own ceiling (the levels differ because the caps are bps over each tier's
own face).

**(d) An event with no resales — the cold-start refusal.**

Tiers with caps and published faces, zero sales: every tier refused, `no_resale_record`; the prior band
`face × e^{0.2612 ∓ 0.329}` with A13 and `n_events = 0`; the exact cap ceiling per tier as `[EXACT]`;
A17 printed because the ~9-event floor is unmet; no price. A second event with no tickets at all (the
draft) renders the same state plus `no_exposure`, and the difference between the two is itself a useful
thing for a judge to see: "no sales yet" and "nothing issued yet" are different facts.

### 4.8 Every point where the engine must refuse, and what it says instead

| Code | Condition | What the page prints instead | Wording source |
|---|---|---|---|
| `no_ledger` | store is empty (`TICKETPATH_LEDGER_MODE=empty`) | `[REFUSED] No ledger exists. Nothing was invented to fill it.` | `orchestrator` |
| `no_resale_record` | no priced sale at or before `asOf` | `[REFUSED] No resale has been recorded on this event, so we will not state a primary price.` + prior band + A13 | §3.7 r1 |
| `no_upper_bound` | regime is `capped and binding` | A19 in full: `at least {floor} SOL` and `Range: {floor} SOL and up. We do not state an upper bound from this record.` The price is given; the upper end is refused. | `02-b` §3.4 |
| `insufficient_marks` | `n_marks < 4` | `[REFUSED] {n} sales is too few to fit a path; the flat line below is the benchmark, not a forecast.` | §3.5 |
| `insufficient_time_spread` | `spread < 5 d` | `[REFUSED] The {n} resales span {d} days; 5 days of spread are required to separate time from the level.` | §3.5 |
| `degenerate_design` | singular 2×2 | `[REFUSED] The resales are too clustered in time to separate curvature from drift.` | §3.5 |
| `no_exposure` | zero ticket-days | `[REFUSED] No ticket had been issued at this instant, so there is no denominator.` | §3.6 |
| `not_identified` | any request for `saleProbability` | `[REFUSED] The platform does not record asking prices, so we cannot estimate the chance a ticket sells at a specific price. What is shown is what actually happened.` | A15, X1 |
| `no_demand_response` | always, tonight | `[REFUSED] An interior optimum needs a primary demand response. η and q_min are not identified from this record, so the recommendation is a boundary.` | §3.7 r5 |
| `no_fee_model` | `fee is None` | `[REFUSED] No fee model is configured. The recommendation does not depend on an ad-valorem fee; the net value line does, so it is withheld.` | §3.7 r6 |
| `insufficient_events` | `J < 9` for any between-event quantity; `J < 3` for any holdout or score | A17 verbatim, with the counts | `03-b` §6.4–6.5 |
| `cap_would_refuse` | a recorded sale in the tier exceeds the candidate cap | `[FIXTURE] {k} of {n} recorded sales in this tier are above this cap; under the deployed program those transfers would have failed, so this record could not exist.` | §1.1 step 9 |
| `devnet_absent` | no verified artefact file | `[DEVNET] No devnet transaction has been recorded.` | §1.1 step 14 |
| `rpc_disabled` / `rpc_unreachable` | chain status not read | `[DESIGN] Chain status not read: {reason}. No program is deployed either way.` | §3.10 |

Three of these are unconditional tonight (`not_identified`, `no_demand_response`, `devnet_absent` unless the
operator runs the laptop step). That is the product's shape, not a build failure, and the page must make it
look deliberate: a refusal panel with reasons reads as engineering; an empty panel reads as a missing
feature.

---

## 5. The on-chain piece

### 5.1 What the program does

Four responsibilities, in order (`docs/ON-CHAIN-FOR-LAPTOP.md` §1): it owns the custody hop, so every hop is
a transaction that exists; it enforces the resale cap at the moment of sale; it enforces the verified-wallet
gate; it writes the record (`ResaleRecord` PDA plus a program log event per sale) so the backend can
reconstruct price, time and path without trusting a client. It does not price anything, does not know what a
ticket is worth, and does not hold money.

**The one-sentence invariant, for the page and the video:** *a ticket moves only through an instruction this
program processes, the price is checked against `face + face × cap_bps / 10 000` at execution, and a
transfer to anything but the escrow or the settled buyer fails inside the token program.*

### 5.2 Account layout, as designed

| Account | Seeds | Fields that matter | Why |
|---|---|---|---|
| `Config` | `["config"]` | `authority`, `verifier`, `hook_program_id`, `paused`, `bump` | one per program; the kill switch and the two roles |
| `Event` | `["event", event_id_16]` | `organizer`, `face_value_lamports` (floor), `resale_cap_bps: u16`, `requires_verified_wallet`, `resale_enabled`, `starts_at`, `ticket_count` | the policy the hook reads |
| `Tier` | `["tier", event_pda, tier_id_8]` | `face_value_lamports`, `total_supply`, `issued_count`, `max_per_wallet` | the denominator for every markup, and the anti-sybil cap |
| `Ticket` | `["ticket", mint]` | `mint`, `event`, `tier`, `serial`, `issued_to`, `current_owner`, `status`, `custody_seq`, `issued_at`, `redeemed_at` | the contract's `Ticket`, on chain |
| `Listing` | `["listing", ticket_pda]` | `seller`, `price_lamports`, `escrow_token_account`, `expires_at` | the escrow that makes the price visible |
| `ResaleRecord` | `["resale", ticket_pda, custody_seq_le]` | `seller`, `buyer`, `price_lamports`, `markup_bps: i32`, `occurred_at`, `kind` | the ledger entry, with its own signature and slot |
| `Verification` | `["verified", wallet]` | `verified_at`, `method`, `nullifier`, `revoked` | the gate the hook reads |
| `Nullifier` | `["nullifier", commitment_32]` | `wallet`, `event_scope` | a commitment cannot be registered twice |
| Mint | — | Token-2022 + `TransferHook` + `MetadataPointer` + metadata; **no** `NonTransferable`; supply 1, decimals 0 | the extension set is the requirement; non-transferable would forbid resale |

Rent was not measured on this machine and must not be quoted; it is a cluster parameter.

### 5.3 Instruction set, as designed

`initialize_config`, `create_event`, `create_tier`, `mint_ticket`, `verify_wallet`, `revoke_verification`,
`list_for_resale`, `execute_resale`, `cancel_listing`, `redeem_ticket`, `revoke_ticket`, `set_cap`,
`close_event`, and the Token-2022 `Execute` hook. The two that carry the claim:

- `list_for_resale(ticket, price)` — signer: current owner; checks `resale_enabled`, `status == valid`,
  **price within cap**, one active listing. Writes the listing and moves the token to escrow.
- `execute_resale(ticket)` — signer: buyer; checks not expired, **price within cap re-checked**,
  buyer verified if required, buyer's holding cap; transfers lamports and the token atomically. Either both
  happen or neither does.

### 5.4 What the transfer hook enforces at resale, in order

1. The mint belongs to a configured, open event (read the `Ticket` PDA from the extra accounts).
2. The destination is allowed: if `requires_verified_wallet`, a live non-revoked `Verification` PDA exists.
3. The transfer is minting, or escrow-routed, or the settlement of an `execute_resale` in progress.
   Everything else is a bypass attempt, and a bypass is exactly a sale the platform never sees.
4. The destination's holding cap for this tier.
5. `amount == 1` and `decimals == 0`.

**The hook cannot check price, because it never sees lamports.** The cap is checked in `list_for_resale` and
again in `execute_resale`. Any design that says the hook checks price is wrong about how Token-2022 hooks
work, and the page must not say it. The concession is on the page in the same weight: the hook guarantees
*who may receive*; the sale instruction guarantees *at what price*; and an off-platform payment between two
wallets is invisible to both.

### 5.5 The boundary, stated exactly

| Item | State on 2026-11-08 |
|---|---|
| Program source, build, tests | DESIGN-NOT-DEPLOYED. No `cargo`, `rustc`, `solana` or `anchor` on this machine (measured 2026-11-07T10:48Z); nothing compiled |
| Program id, mint address, program transaction | Does not exist unless the operator runs the laptop step in §5.6 |
| Account layout, instruction set, hook checks | DESIGN-NOT-DEPLOYED, written in `docs/ON-CHAIN-FOR-LAPTOP.md`, not compiled |
| Cap enforcement, nullifier uniqueness, verified-wallet gate | DESIGN-NOT-DEPLOYED |
| The state machine's arithmetic, its ordering, its error codes | **SIMULATED**, executable from `ticketpath/onchain/sim.py`, tested |
| Backend contract endpoints, the engine, the console | **Real on this machine**, tested |
| Wallet signature verification (Ed25519, RFC 8032) | **Real**, tested, no chain required |
| A quote commitment on devnet | Real **only if** the operator runs the laptop step in §5.6 and `tools/devnet_check.py` verifies it |
| Any claim that the transfer hook is enforcing anything | **Forbidden** until a program id exists and the six negative tests of `docs/ON-CHAIN-FOR-LAPTOP.md` §7 step 5 have passed |

### 5.6 The three demo options, and what I recommend

| Option | What it shows | What it cannot show | Cost |
|---|---|---|---|
| **(a) Stated simulation** | the state machine's arithmetic and ordering: cap ±1 lamport, unstaged transfer refused, unverified destination refused, the markup theorem | that Token-2022 calls a hook; that the extra accounts are wired; that the runtime allocates the sizes | 0, already built; every line marked `[SIMULATED]` |
| **(b) A recorded instruction trace** | the same, plus the exact instruction bytes a future client would send | anything about a cluster | ~1 h; adds little over (a) |
| **(c) A devnet transaction the operator runs on the laptop** | a real signature, slot and block time, with the pricing decision's hash in a memo and, optionally, a real Token-2022 mint with the hook extension | that the hook enforces the cap (that needs the program, which is design-only) | ~1 h of operator time, plus a dependency on the laptop and the faucet |

**Recommendation: (a) + (c), and not (b).** (a) is the invariant, honestly labelled, and it runs tonight.
(c) is the only thing that converts "design" into "a real transaction with a block time", it needs no Rust
because a memo instruction is a standard program, and it makes the product's own output the on-chain object:
the organizer's quote is committed before the sale opens and cannot be re-cut. That is the `02-rubric` Tier-2
artefact and the organizer's own published idea ("on-chain records of model outputs, provenance").

**One measured fact about that route, checked in this pass.** `getAccountInfo` on
`MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr` against `api.devnet.solana.com` returns
`executable: true`, owner `BPFLoader2111111111111111111111111111111111`, space 74800, at slot 519646084
(2026-11-07T11:33Z). The memo program exists and is executable on the cluster the demo would use. That is
the only program the demo transaction touches besides the system program, and neither is ours — which is
why the demo must not be described as "our program".

**What the memo proves, and what it does not.** It proves that a specific quote — quote id, event, tier,
recommended price, as-of, model version — existed at a specific slot before a specific time, and that its
hash matches the decision the console shows. It does not prove the quote was good, and it does not enforce
anything. The page says both.

**Artefact file, written only by `tools/devnet_check.py`:** `records/devnet-artefacts.json` with
`{cluster, rpcUrl, signature, slot, blockTime, memoText, quoteHash, quoteId, eventId, tierId,
recommendedLamports, mint: str|null, programId: str|null, checkedAt, checkerVersion}`. The console renders
`[DEVNET]` only when the file exists **and** `quoteHash` recomputes from the displayed quote. A file that
fails the recomputation renders `devnet_unverified`, not a verified slot.

**Laptop step, exact shape (the operator runs it, not an agent):** build the canonical quote JSON from
`tools/guidance.py`; compute its SHA-256 with `chain_client.quote_commit` (same function, so the hashes
cannot drift); send one devnet transaction carrying the memo `ticketpath:quote:{quoteId}:{hash}`; paste the
signature into `tools/devnet_check.py`; if it verifies, the console flips to `[DEVNET]` on the next reload.
Command spelling is version-dependent and must be checked against `--help` on the laptop before running; if
the memo route is unavailable, the fallback is a Token-2022 metadata field on the mint, and the artefact
file records which route was used.

**Hard rule.** No signature is ever typed into the page, no placeholder signature is rendered, and no
explorer link is built until the artefact verifies. `[DEVNET]` with nothing behind it is the one lie that
would sink the submission, and the rubric's rule is unambiguous: the chain artefacts must be real or absent.

---

## 6. The clock plan

26 hours, 13:00Z Saturday to 15:00Z Sunday. **The build is 17 hours; the last nine contain the verification
buffer, the freeze, the video and the submission.** Times are Z; ET is in brackets where it decides a
human's action. "Who" is
`build` (agents), `review` (an agent that did not write the code), or `operator` (only he can do it).

| Hour | Who | Deliverable | Done when |
|---|---|---|---|
| Sat 13:00–14:00 | build | interfaces frozen: `labels.py` with T1–T5, A1–A20, X1–X20; every new module a stub returning its refusal; `/` returns a page with the banner | `python3 -m unittest discover -s tests` green; `curl /` shows T1 |
| 14:00–17:00 | build | `price_features` + `value_band` (one agent); console shell + badges + `api/guidance` (one agent); `intensity` (one agent) | prefix-invariance, canary and golden tests pass; the fixture decision renders end to end |
| 17:00–20:00 | build | `path_model` (refusal-first) + `primary_optimum` + the consequence table; `onchain/sim.py` | every refusal code reachable; the sim's three arms pass their tests |
| 20:00–23:00 | build | controls: `asOf`, `capBps`, `feeLamports`, `tau`; `cap_would_refuse`; `chain_client`; the chain panel in both states; `rpc_adapter.chain_status` | each control changes the payload and the canonical URL reproduces it |
| 23:00–01:00 | build | `tools/guidance.py`, `tools/devnet_check.py`, `docs/RUN.md`, the README integration section, the acceptance script | the acceptance script runs 14 steps from a cold start |
| Sun 01:00–03:00 | review | the adversarial pass: §1's fourteen steps, §2.7's three tests, §4.8's fourteen refusals, and a claim-by-claim check against `CONTRACT-MAP.md` §5 | every finding filed with a severity; P0/P1 fixed before 05:00 |
| 03:00–03:30 | operator | read the page, run the acceptance script, name the cut if one is needed | he says go, or names the item |
| 03:30–05:00 | build | fix the P0/P1 list; second label pass; full suite | suite green; tag `night-build` |
| 05:00–06:00 | build | cold-start verification: fresh shell, fresh server, the acceptance script, `/health` | every step passes without a warm cache |
| 06:00–09:00 | build | buffer: only the cut list, nothing new. If verification fails at 06:00, revert to `night-build` and re-verify | a known-good tree, or the tag |
| **09:00** | — | **DEMO FREEZE.** Code, page and labels are frozen. No commit after this touches `ticketpath/`, `tests/` or `tools/` | `git tag demo-freeze` printed |
| 09:00–10:00 | operator | the laptop step (§5.6): memo transaction, `tools/devnet_check.py`, reload the page | `[DEVNET]` verified, or the absent state confirmed and accepted |
| 10:00–11:30 | operator | record the video (§6.2), 1:45 target, hard cap 2:00 | a file under 2:00, hackathon named in sentence 1 |
| 11:30–13:00 | operator + build | submission text, README final read, AI-tool disclosure, category selection, and — **only with his explicit yes** — the push to the public remote | every claim traced to a line in §5.5 or §2; the pushed tree equals the `demo-freeze` tag |
| 13:00–13:30 | operator | submit on the MLH Challenges page; confirm the confirmation email/screen | a submission id |
| 13:30–15:00 | — | buffer. Nothing is changed unless the submission is rejected | — |
| 15:00 | — | deadline | — |

**The operator's sleep is 03:30–09:00Z (22:30–04:00 ET), and it is in the plan on purpose.** He films and
submits on the far side of it. Nothing in 03:30–09:00Z needs him: the tree is tagged at 05:00Z and the
fallback is mechanical.

**Commits and the push.** Every commit in this plan is local. `night-build` and `demo-freeze` are local tags.
Nothing is pushed, published or uploaded by an agent: the push to the public remote is his explicit yes at
11:30–13:00Z, and until then the repository's visibility is his call. The rubric makes a public repo a prize
condition (`02-rubric` §6.1), so the push is on the clock rather than optional — but it stays his click.

### 6.1 Cut list, in the order things are dropped

Cut from the top when a deliverable misses its hour. **Items 1–3 are load-bearing and are never cut**, so
the list starts at four: if the build slips, the answer is to cut deeper down this list, never to touch the
page, the labels, the band or the refusals.

1. *(never)* the console page, the banner, the badges, the refusal panel, the recommendation block.
2. *(never)* `labels.py` and its three tests.
3. *(never)* `value_band`, `primary_optimum` and the four refusals (`no_resale_record`,
   `no_upper_bound`, `no_demand_response`, `no_fee_model`).
4. `path_model`'s fitted branch — keep the module, the guards and the martingale. The guards are the
   behaviour that matters; whether the fixture's marks clear the 5-day spread is not.
5. `onchain/sim.py`'s theorem and expiry arms — keep cap, unstaged and unverified.
6. `intensity`'s competing-risks split — keep the composite rate and the exposure.
7. The repeat-sale line and the τ sensitivity table on the page.
8. `tools/devnet_check.py`'s mint/program fields — keep the signature, slot, blockTime and quote hash.
9. The `capBps = 0` violation state — keep `capBps = 10000`.
10. `rpc_adapter.chain_status`'s live read — fall back to "not read" plus the artefact file.
11. `tools/guidance.py` — the URL is the headless path.
12. The extra prose on the cold-start and no-mass-point screens — they are already states of the same page;
    cut the words, not the states.

**Never cut, in one line:** the page, the banner, the labels, the four refusals, the recommendation, the
`[DEVNET]` honest-absent state, and the `python3 -m unittest` suite.

### 6.2 The video, because it is what gets watched

1:45 target, 2:00 hard cap. Hackathon named in the first spoken sentence. Order:

| Time | Shot | The one line, spoken |
|---|---|---|
| 0:00–0:20 | the console on the capped-and-binding event, decision block in frame | "Solana Hackathon. This prices primary tickets off the resale record, and here it says: at least the cap, and up — because the cap truncated the record." |
| 0:20–0:40 | switch to the uncapped event; the block becomes a point and a band | "Same engine, no cap: now it can state a range. A cap does not hide the price; it hides the top of the price distribution." |
| 0:40–1:00 | move `asOf` back before the first sale | "Nothing after this instant enters any number — so with no sale yet, it refuses to price." |
| 1:00–1:15 | the refusal panel | "No sale probability at a price, no interior optimum, no net revenue without a fee. Each line names what is missing." |
| 1:15–1:40 | the chain panel: `[SIMULATED]` refusal with 6010, then `[DEVNET]` signature, slot and block time on Explorer | "The invariant is designed and simulated; the quote itself is on devnet, committed before the sale opened, so it cannot be re-cut." |
| 1:40–1:50 | one sentence of learning, then the end card | "What I learned: the hard part of pricing is not the model, it is knowing what the record cannot tell you." |

No wallet popup, no pitch, no market-size slide. Every number on screen carries its badge, and the video must
not crop a badge out — that is the one editing rule. If the `[DEVNET]` state is absent, shot 5 shows the
absent state and the sentence changes to "the quote commitment is the one thing left for the laptop", which
is weaker but true; a fabricated signature is not an option.

---

## 7. Risks that would sink the submission

Each with the mitigation and the hour by which the mitigation must have happened. "Must have happened" is a
deadline, not a wish: past it, the risk is live and the cut list applies.

| # | Risk | Why it sinks it | Mitigation | Must be done by |
|---|---|---|---|---|
| R1 | No clickable surface when the video is recorded | a judge who cannot click sees nothing; Design is 25% and Completion is 25% | the page exists in hour 1 with the banner and a refusal, and is extended after | Sat 14:00Z |
| R2 | A number on the page reads as real | the "misled" failure; the rubric's own labelling finding (`02-rubric` §E, and `DEMO-PROOF.md` §6's measured gap) | `labels.py` + the three enforcement tests + the banner | Sat 15:00Z |
| R3 | A prohibited sentence ships | X1 is the sentence the review says must stop being printed; shipping it invalidates the product's central claim | the banned-pattern test in the suite and in the acceptance script | Sat 15:00Z |
| R4 | The engine crashes on the cold-start event during the video | a cold-start event is one click away from the default | the cold-start path is a first-class route with its own test; default selection is the event with cap-binding evidence | Sun 01:00Z |
| R5 | The server is down or the page 500s on camera | a single stack trace ends the demo | `docs/RUN.md` one command; a pre-flight `curl` in the acceptance script; the page never raises (errors render) | Sun 06:00Z |
| R6 | `[DEVNET]` is claimed but absent or unverifiable | the one lie that converts an honest project into a dishonest one | the artefact verifier and the absent state; no placeholder path in the code | Sun 09:00Z |
| R7 | The submission text overclaims | an overclaim in text outlives the demo | the text is written from §5.5's boundary table and §2's badges; a reviewer checks every claim | Sun 13:00Z |
| R8 | The build slips into the freeze | a half-built page at 09:00Z | the cut list, executed in order, with the decision point at 03:00Z | Sun 03:00Z |
| R9 | The live frontend on :3000 is touched, rebuilt or restarted | violates a red line and loses the market surface | nothing writes to `../ticketing-frontend`; the demo uses 8788 and, if shown, the copy on 3001; a test asserts no path outside the repo is written | Sat 13:00Z (and continuously) |
| R10 | A third-party import creeps in | D2; the machine has no pip, so it fails at runtime | the import allowlist test, extended with `html`, `re`, `math`; `urllib` in one file | Sat 20:00Z |
| R11 | The video exceeds 2:00 or omits the hackathon name | a rule violation that is unrecoverable at the deadline | the script in §6.2 with the name in sentence 1; a visible timer; the file checked at 11:20Z | Sun 11:30Z |
| R12 | Port 8787 is bound or the fleet's page is disturbed | 8787 belongs to another process; touching it is a red line | `resolve_port` refuses 8787; the spec's start command uses 8788; no `kill` of any pid not ours | Sat 13:00Z |
| R13 | The repo is private, or the first commit is outside the window, or there is no LICENSE | a prize condition (rules 12–13; `02-rubric` §6.1) | the operator confirms visibility and commit time; add `LICENSE` and the README integration section today | Sun 13:00Z |
| R14 | The AI-tool disclosure is missing | stated penalty: disqualification and a report | a README section naming the tools, written at 11:30Z and checked against the submission form | Sun 13:00Z |
| R15 | The whole build depends on a subagent that stalls | the night loses four hours | the 90-minute rule: any workstream with no green test for 90 minutes is reassigned or cut; the tree is tagged after every green suite | continuous |

---

## 8. What is deliberately not built

Each line is a choice, with the reason, so a reader knows the omissions are not oversights.

| Not built | Reason |
|---|---|
| A listing, bid, buy, checkout or resale-marketplace endpoint or screen | the product decision: Ticketpath prices primary tickets; there is no listing path in the contract and none may be invented (`00-prior-direction-index` §3(5); `02-d` §1.1) |
| An LLM, an agent loop, or a learned model behind the price | D5; the binding constraint is identification, not functional form; the AI track's criterion fails on its own wording (`02-ai-ml-decision`) |
| An AI-track entry | D5; the track pays $100 per member against $1,000 per Top-3 place, and the cheapest candidate is a scripted bot |
| A deployed program, a real mint, a real hook | no toolchain on this machine; a deploy that cannot happen is not planned (`02-rubric` E1) |
| Any code path that signs or sends a transaction | no keypair, no toolchain, and money and irreversible actions are the operator's call |
| A price-specific sale probability | T3 is not identified; the sentence is prohibited; the field is forced to `null` with `not_identified` |
| An interior primary optimum, an elasticity estimate, a demand curve | T4b/D04: not identified; the recommendation is a boundary and the two missing parameters are named |
| A calibration, accuracy, lift or coverage number | selective labels block it for any price distribution (`01-b` T6); the floors are unmet (`03-b` §6.4) |
| A backtest or skill score | the floors are ~9 events, ~20 residuals, ~30 sales per band; the fixture has 2 events and 4 sales |
| A CVaR or mean-variance risk functional | no demand distribution exists, so the risk adjustment is a one-sided bound and a stated choice, not a functional (`02-d` §4.3) |
| Seat-level features | not in the contract; Q1 is open; every seat-quality claim stays class D |
| An on-chain indexer, `getProgramAccounts` ingestion, a real ledger reader | no program, no records; the read would return nothing and the code would look like it worked |
| Fee and settlement ingestion | no field anywhere in the contract (Gap 4); the fee is a parameter and a missing one is a refusal |
| Dynamic pricing, repricing, holdback release | there is no price-mutation endpoint; it is a product and schema change (`02-d` §5) |
| Cross-event demand effects, a network model | GAP-2: no interaction registry; and one event at a time is the product's scope |
| Auth, accounts, multi-tenancy, a database, persistence | the product is read-only plus wallet verification; verification state is in memory and says so |
| Any change to `../ticketing-frontend` | the tree is his; the demo copy lives outside it (`DEMO-PROOF.md` §1) |
| Any change to a contract route or field | `CONTRACT-MAP.md` §9.2; the proposal is §9 of this document and is not built |
| A bespoke screen per regime, a chart library, a map, an animation | nothing on the page needs them and every one of them is a place a number can lose its badge; the regimes are chips and blocks on one page |
| Hosting, a public deploy, a push | no push without his explicit yes; the demo is local and the video is the distribution |

---

## 9. PROPOSAL (not built tonight): the contract extension that would put a recommendation on the wire

**Marked separately because it is not part of this build and must not be implemented without the operator's
explicit yes.** `CONTRACT-MAP.md` §9.2 records why: it is a frontend-contract change, and the frontend is
not ours to edit.

**The route.** `GET /api/events/:eventId/price-guidance` with query parameters `tierId`, `asOf`, `capBps`,
`feeLamports`, `tau`. Response `200`, body `PriceGuidance`. Errors follow the existing convention:
`{message, status, code}` with `code ∈ {event_not_found, tier_not_found, as_of_invalid, cap_invalid}`;
`no_resale_record` is a **200** with `refused: true`, not a 4xx, because a refusal is a valid answer.

**The type, in `lib/types.ts` terms:**

```
PriceGuidance = {
  eventId: string; asOf: string; modelVersion: string | null;
  tiers: PriceGuidanceTier[];
  dataSource: { mode: string; synthetic: boolean; label: string; note: string };
}
PriceGuidanceTier = {
  tierId: string; faceValueLamports: number;
  regime: "capped_and_binding" | "capped_no_mass_point" | "uncapped" | "no_resale";
  shareAtCeiling: number;                          // k/n, and 0 when the regime has no cap
  recommendedPrimaryLamports: number | null;       // null when refused
  recommendedIsFloor: boolean;                     // true on capped_and_binding: "at least"
  bandLamports: [number, number | null] | null;    // [lo, null] means no upper bound, not "missing"
  basis: string;                                   // the counts and the source, one line
  refused: boolean; refusalCode: string | null;
  requiredInputs: string[];
  saleProbability: null;                           // always null; the type makes that visible
  saleProbabilityReason: "not_identified";
  requiredSellThrough: { candidateLamports: number; sellThrough: number }[];
  labelIds: string[];                              // which allowed sentences the client must render
}
```

**Three conditions on any future implementation.** (1) `saleProbability` is typed `null`, not
`number | null`, so a client cannot render a number that does not exist. (2) `labelIds` is required, and the
client must render every id it receives — a field the server can demand and a test can enforce is worth more
than a docstring. (3) The route is additive: no existing field changes shape, and the nine contract
endpoints keep their responses byte-identical. A fourth condition follows from `02-b`: `bandLamports[1]` is
`number | null` and `recommendedIsFloor` exists, so the binding regime's no-upper-bound answer is
representable on the wire instead of being squeezed into a two-number tuple that would force the client to
invent a ceiling.

**Why not tonight.** It changes the wire contract the frontend compiles against, and the frontend is live on
:3000 and is not ours. A half-added route would make the two surfaces disagree, which is worse than a
console that is clearly ours. And the recommendation is unvalidated: putting it on the contract invites a
client to render it without the badge discipline this console enforces, which is the failure mode §2
exists to prevent.

---

## 10. The first ten actions, in order

For the build agent who opens this file first. Each is a commit-sized unit, and the suite is green after
each.

1. Add `LICENSE` (MIT) and read `docs/RUN.md` into existence with the one start command.
2. Write `ticketpath/core/labels.py` with T1–T5, A1–A20 and the X1–X20 patterns, and
   `tests/test_labels.py`. Nothing else starts until this is green: every later module prints through it.
3. Extend `tests/test_boundaries.py`: allow `html`, `re`, `math`; allow `urllib` in
   `adapters/rpc_adapter.py` only; assert no module writes outside the repo.
4. Add the `GET /` route returning a static page with T1, T5 and the title. Commit. The demo now exists, in
   its worst state, and can only improve.
5. `core/price_features.py` + its property tests (prefix invariance, canary, no negative durations, ±1 bp
   cap).
6. `core/value_band.py` + the golden test on the fixture. This is the first real number the page will show.
7. `core/intensity.py` + the denominator test.
8. `core/primary_optimum.py` + the refusal branches (`no_resale_record`, `no_upper_bound`, `no_demand_response`,
   `no_fee_model`) + the consequence arithmetic.
9. `api/guidance.py` + the payload labeller walker, then `console/page.py` against the payload. At this point
   §1.1 steps 1–11 work.
10. `onchain/sim.py` moved from the docs, the chain panel, `chain_client`, then `adapters/rpc_adapter`
    `chain_status`. Steps 12–14 work.

Then the clock plan from 20:00Z. **Definition of done for the night:** the fourteen steps of §1.1 pass from
a cold start, the suite is green, `git tag demo-freeze` is printed at 09:00Z, and no sentence in §2.6's
prohibited column exists anywhere in the tree.

---

*Read list and gaps are in §0. `02-b` landed at 11:30Z and is adopted in full (its regimes, its
no-upper-bound rule and its replacement wording); **GAP-1 is closed**. The gaps that remain are GAP-2
(`03-a` interactions, absent) and the `B-mathematical-kb` stub. Nothing in this document is a measured
result: the only measured facts in it are the toolchain state, the fixture's contents, the memo program's
existence on devnet and the file's own arithmetic, and each is attributed and dated.*

---

## Snapshot note — 2026-11-07T12:14Z

**This file is the spec as written at 11:40Z, before its own build window opened (13:00Z), not a
description of the current tree.** It is kept as written because it is the instruction the build
was held to. Parts of it describe work that has since landed, and one worked number was already
stale when it was written. Read §1–§3 as the brief; read this note for what exists.

| What the document says | What is true now | Shown by |
|---|---|---|
| the console is to be built: `ticketpath/api/guidance.py`, `core/price_features.py`, `core/value_band.py`, `core/path_model.py`, `core/intensity.py`, `core/primary_optimum.py`, `core/labels.py`, `adapters/chain_client.py`, `onchain/sim.py`, `console/page.py` and `tools/guidance.py` are all marked **NEW** (§3 module table, 1–16) | Every one of those files exists. `console/` additionally holds `blocks.py` and `units.py`. The console is served at `/` and prints a recommended primary price | `ls ticketpath/api/guidance.py ticketpath/core/{price_features,value_band,path_model,intensity,primary_optimum,labels}.py ticketpath/console/page.py tools/guidance.py` |
| module 17, `tools/devnet_check.py`, marked **NEW** | Does not exist. Nothing was deployed, so nothing was verified against a cluster and no artefact file was written | `ls tools/` |
| "the fixture has 2 events and 4 sales" (§8, the reason a backtest is not built) | The reason stands but the count does not: **8 events, 76 tickets, 147 ledger rows, 61 priced sales**. The floors a backtest needs (~9 events, ~30 sales per band) are still unmet | `python3 tools/build_fixture_store.py --check` |
| the seam is "the model seam; registers the engine" (module 11) | Registered, and `/health` now says what it is: `kind: rule-based-bounded-estimator`, `fitted: false`, with a note that no model was trained, calibrated or validated | `curl -s http://127.0.0.1:8788/health \| python3 -m json.tool` |
| the acceptance test count is not stated here | `OK`, on a suite that was **293 tests when this pass began and 306 when it ended** (another session was adding console tests throughout). Quote the command's own last line, never this one. | `python3 -m unittest discover -s tests` |

What has not changed: the surface, the labels, the refusals, the prohibition list in §2.6, the
rejected-approach table in §8, and the fact that §9's `price-guidance` route proposal is still a
proposal and is not on the wire.

---

## CORRECTION (2026-11-07T18:55Z) — the A4 label sentence overstates what the recommendation is based on

**Measured:** 18:40Z–18:55Z at `origin/main` (`8a5e5e6`). **Scope:** this file, appended. The sentence's
authoritative home is `ticketpath/core/labels.py:123-126`, which this pass was not allowed to write; the
one-line change it needs is at the end of this note.

**The claim**, quoted verbatim from the label table in §2 of this file (line 306) and from the label
itself:

> `The primary price recommendation is a range, not a point. It is based on the resale value signal and
> the primary sell-through observation; it does not use a resale sale-probability curve.`

**The correction.** The recommendation is not based on the sell-through observation. Read from the code
that computes it (`ticketpath/core/value_band.py:394-419`): the level is
`face × exp(mean(log(price/face)))` over that tier's own recorded marks, and the band is
`level × exp(∓ z·max(τ, 0.10))` with `z = 1.6449` and `τ` declared at 0.2. Sell-through enters in two
places and neither of them is the level or the width: the `[EXACT]` consequence table, where
`requiredSellThrough = face × observedSellThrough / candidate` is a definition rather than an input, and
the `sellThroughObserved` field printed beside it. The word "based" is doing work the code does not do.
The second half of the sentence is true and stays: there is no sale-probability curve, because
`saleProbability` is refused with `not_identified`.

**The corrected sentence**, which is what the label should say:

> `The primary price recommendation is a range, not a point. It is computed from the tier's own recorded
> resale marks: the level is face value times the mean log price-to-face ratio on that tier, and the width
> is a declared τ. The observed sell-through enters only the consequence table, where the sell-through a
> candidate price would require is an exact division, and it does not enter the level or the width. It
> does not use a resale sale-probability curve.`

**Why it is a correction and not an edit.** The stale-claims pass of 2026-11-07T18:55Z was scoped to
documents; `ticketpath/` was out of bounds while another run held the tree. The change is the two strings
in the `"A4"` tuple in `ticketpath/core/labels.py` — nothing else references the wording
(`ticketpath/console/blocks.py:399` renders it, and no check asserts the sentence's text). Until it is
made, the console still prints the overstated sentence, and this file's table is the record of what it
said rather than a claim about what it says.

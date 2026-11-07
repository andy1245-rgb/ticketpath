# Reconciliation: the two on-chain design documents

**Date:** 2026-11-07. **Decision log entry:** `records/F-decision-log.md` D6.
**Outcome:** `docs/ON-CHAIN-DESIGN.md` is the design. `docs/ON-CHAIN-FOR-LAPTOP.md` is a pointer
and is marked superseded, not deleted: its full earlier text is committed at
`3bece48:docs/ON-CHAIN-FOR-LAPTOP.md`, blob `520fe750b4cadf401a13c92ce3a3901a01eba4a0`, 19,445
bytes. Nothing was redesigned in this pass. The three positions were decided, not re-argued, and
where the earlier document was right, that is said in the decision.

**Deadline used as the cost criterion:** Sun 2026-11-08 10:00 America/Toronto = 15:00Z, initial
submission (`records/00-prior-direction-index.md` item (h)). At the time of writing that is under
24 hours away.

**Four criteria, applied to each divergence.** (1) Does the position make the anti-fraud invariant
stronger or weaker. (2) Does it stay inside the product framing: an organizer revenue-management
tool that prices primary tickets, with no listing, bid, buy or checkout surface. (3) Does it cost
hours that do not exist before the deadline. (4) Is it checkable on a laptop with Agave plus
`spl-token`, with no other service and no off-chain half.

**Nothing is claimed as built or run.** No program was compiled, deployed or tested in this pass,
no mint or address exists, and every hour figure below is an estimate copied from
`docs/ON-CHAIN-DESIGN.md` §1.3, not a measurement.

---

## Decision 1: escrow and its listing surface are rejected; per-ticket record plus transfer hook stands

**Position that stands.** `ON-CHAIN-DESIGN.md` §1.4: one Token-2022 mint per ticket with a
`TransferHook` extension pointing at the program, a `TicketRecord` PDA per ticket, an append-only
`HopRecord` PDA per custody change, and the cap checked in `transfer_ticket` before the transfer
CPI. No escrow account, no listing account, no `list_for_resale`, no `execute_resale`.

**Reason.** The hook is what makes a transfer the program did not stage fail in the runtime, so the
custody record is complete for every hooked mint; an escrow does not add to that, it adds a claim
about the *recorded payment*, and the hole it cannot close is the one that matters, because a pair
who agree a price off-chain can route a face-value sale through the escrow and settle the rest in
cash, so the recorded price becomes a real payment without becoming the price
(`ON-CHAIN-DESIGN.md` §4.2.1). It rebuilds exactly the listing, buy and checkout surface the
product framing forbids, and it was estimated at 10 to 14 hours against 3 to 5 for the record plus
the hook, with cancel, timeout, fee-split and dispute arms that a laptop session cannot verify
before Sunday. It is checkable on a laptop, and that is precisely the problem: it is checkable only
by running twice as many arms as there are hours for.

**Where the earlier document is right, plainly.** Its hook is the thing that makes an off-platform
transfer impossible rather than merely detectable, and it says out loud that a hook never sees
lamports and therefore cannot check a price. `ON-CHAIN-DESIGN.md` §12.3 records that both positions
came from it and are now in §1.3 and §3.9. Its escrow is also the right answer to a real question,
"make the cap bind on money"; that is deferred, not denied, and it is tier (c) in §5 with §11
recording what its absence costs.

## Decision 2: sybil resistance is not built and is not claimed

**Position that stands.** `ON-CHAIN-DESIGN.md` §4.2.6: the design has no sybil resistance at all,
nothing in it counts wallets, and the real scalper mechanism (many wallets at the primary sale) is
untouched. No `Nullifier` PDA, no `max_per_wallet`, no identity commitment, and no bot-resistance
sentence in any artefact.

**Reason.** This is the one place the earlier document diagnoses the problem better than the later
one, and the later one concedes it: the scalper mechanism is many wallets, not one high price, and
nothing else in either document addresses it. But the mechanism it proposes only guarantees "this
commitment was registered once", with the identity behind the commitment proven off-chain by
whatever document an organizer accepts, so the invariant it delivers is much weaker than the
sentence it would license in a pitch; it needs an identity provider and a decision about what the
chain may remember about a person, neither of which exists in this programme; and half of it is
off-chain, so Agave plus `spl-token` cannot check it. It is a stronger *diagnosis* priced as a
weaker *guarantee*, at a cost in hours that has no return before the deadline. Recorded as a
non-claim, which is the honest form of the finding.

**Piece kept from the earlier document.** Its own honest limit, which is now the wording of the
non-claim: the program can guarantee that a commitment was registered once, not that a person is
who they say they are, and that gap belongs in the submission rather than under it (`F` D6, and
`ON-CHAIN-DESIGN.md` §4.3 for the same discipline).

## Decision 3: the cap is fixed when the policy is created and never moves; `set_cap` is refused

**Position that stands.** `ON-CHAIN-DESIGN.md` §2.1: `cap_enabled` and `cap_bps` are written by
`create_event`, before any `issue_ticket` call exists to exploit them, and no instruction in the
program writes either field afterwards. There is no `set_cap` and no policy history. Every ticket
is therefore minted under a cap that cannot change for the life of the ticket, which is the meaning
of "fixed at mint creation" with the fixed point one step earlier, and the earlier step is what
makes it enforceable: the tier face value that the cap is computed over is frozen at
`create_tier` for the same reason (§2.2).

**Reason.** A mutable cap reopens the hole the fixed one closes, which is raise the cap, sell, then
lower it again, and the earlier document's mitigation (an `effective_at` stamp plus a re-check at
execution) is only as good as the record of when the cap changed, so it needs a policy history
account, one more instruction and one more negative test. That is more surface on the largest risk
to the deadline, and it weakens the claim from "the terms the fan bought under are the terms the
chain enforces" to "the terms as of the last write". A fixed cap is one sentence to a judge and one
`getAccountInfo` to check on a laptop; a movable cap is a genuine product feature and is deferred
with its cost named (§11), not dropped quietly.

**Where the earlier document's instinct is right.** A cap that a real organizer cannot adjust
mid-campaign is a usability limit, and `ON-CHAIN-DESIGN.md` §12.2 says so in as many words: "a
fixed cap is a stronger claim; a movable cap is a real product". The decision prefers the stronger
claim for this submission. If the operator later wants the product, the precondition is the policy
history account, not the instruction.

---

## What was carried over into `ON-CHAIN-DESIGN.md`

The earlier document had three pieces the later one lacked. They are in a clearly marked section,
`ON-CHAIN-DESIGN.md` §13, and none of the later document's existing text was changed:

| carried piece | was at | now at |
|---|---|---|
| the program has no pricing responsibility (does not price, does not value, does not hold organizer money) | sibling §1 | §13.1 |
| the verification gate must fire inside the transfer, because a check before the transaction is a race | sibling §6 | §13.2 |
| the backend handoff: `TICKETPATH_CLUSTER`, `TICKETPATH_PROGRAM_ID`, `TICKETPATH_RPC_ENABLED`, and the two adapters that must change before `transferRestricted` may be true | sibling §7 step 6 | §13.3 |

Everything else in the earlier document is either superseded by the three decisions above or is in
`ON-CHAIN-DESIGN.md` in a fuller form; the pointer file carries the section-by-section map.

---

## Remaining references to the rejected position

The reconciliation pass searched `docs/` and `records/` for `escrow`, `escrowed`, `nullifier`,
`set_cap`, `max_per_wallet`, `list_for_resale`, `execute_resale` and a mutable or time-varying cap.
These are the hits that need the orchestrator's attention. **None of them was edited in this pass**
apart from the two documents named in D6.

### Asserts the rejected position, or points at the superseded document: fix these

| file and line | what it says | why it needs fixing |
|---|---|---|
| `docs/BACKEND.md:91` | `docs/ON-CHAIN-FOR-LAPTOP.md   transfer hook + escrow design, DESIGN-NOT-DEPLOYED` | the file is now a pointer and the design has no escrow; the line describes a superseded artefact as the design |
| `docs/BACKEND.md:75-76` | "It will not enforce the resale cap or the verified-wallet gate. An API cannot: those are transfer-hook conditions. `docs/ON-CHAIN-FOR-LAPTOP.md`." | the statement is still correct; the pointer must move to `docs/ON-CHAIN-DESIGN.md` §3.9 |
| `docs/ON-CHAIN-DESIGN.md:1954-1999` (§12) | "the operator, not this document, decides between them"; "If the operator wants the escrow, the sibling's §3.5 and §4 are the specification"; "If the submission is going to claim anything about bots, take the sibling's §3.7, §3.8…" | written before the decision, so it presents three settled questions as open and sends a reader to sections that no longer exist as a design. §13 states the decision, but §12 needs one added line saying it is decided (D6) and that the sibling is a pointer |

### Quotes the position as an available option: decide whether to annotate

| file and line | what it says | note |
|---|---|---|
| `records/00-prior-direction-index.md:17` | plan item (c) quoted verbatim: "the anti-fraud invariant must be on-chain (Token-2022 transfer hook or PDA escrow)" | this is the operator's own instruction quoted, so it must not be rewritten; it reads as an open menu, and D6 is the choice from it |
| `records/00-prior-direction-index.md:106-108` | uses "the transfer hook or PDA escrow (c) requires" in an argument against an earlier direction | same: a historical quote used in an argument that is still valid |

### Not our design, no change needed

| file and line | what it says |
|---|---|
| `records/findings/02-rubric-and-scoring.md:277` | the Midnight sponsor's winning-primitive note mentions "commitments, nullifiers, Merkle membership" as a field observation |
| `records/findings/02-rubric-and-scoring.md:292` | a competitor's project is described as "escrowed on devnet"; not Ticketpath |

### Partly resolved by D6, and deliberately left open

| file and line | status |
|---|---|
| `records/F-decision-log.md:134` (Q3, "Is the resale cap enforced on-chain or by the platform's matching engine?") | answered for this design: the cap is enforced on-chain by this program, which is what D6 says. Still open about the live platform, whose matching engine is not this program. Do not close Q3 without asking the operator |

---

## Residual risk the operator must accept

**Side payments.** The chain bounds the price it is told, not the money that moves. Two wallets can
agree a price off-chain, route a face-value resale through the program and settle the difference in
cash or on another chain, and the record will faithfully show a compliant sale at face. The
consequences are already in the documents and they are the ones that matter: the recorded markup is
a lower bound on the true markup, the observed distribution is truncated from above by the cap and
from below by under-reporting, and the pricing engine's input is therefore directional rather than
exact (`ON-CHAIN-DESIGN.md` §4.2.1, §4.3). Nothing on a chain fixes this; escrow does not fix it
either. A second, separately recorded non-claim sits beside it: one person with many wallets is
untouched by this design (§4.2.6), and no artefact may claim otherwise.

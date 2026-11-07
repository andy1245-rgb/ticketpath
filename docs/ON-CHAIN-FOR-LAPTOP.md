# On-chain program for a laptop (SUPERSEDED)

**Status: SUPERSEDED, 2026-11-07. Do not implement from this file.** It is kept as a pointer so
that a reference to it still resolves and so that the record shows it was marked rather than
deleted. The live design is **`docs/ON-CHAIN-DESIGN.md`**: account layout, instruction set,
transfer-hook behaviour, threat model, Rust sketches and the laptop runbook all live there now.

**The earlier full text is not lost and was not edited before this rewrite.** It is committed at
`3bece48:docs/ON-CHAIN-FOR-LAPTOP.md`, blob `520fe750b4cadf401a13c92ce3a3901a01eba4a0`,
19,445 bytes. Read it with:

```bash
git show 3bece48:docs/ON-CHAIN-FOR-LAPTOP.md
```

**What this file was.** An earlier design, written the same evening, for a program that used a
transfer hook *and* a PDA escrow, with a sybil nullifier and a mutable resale cap: eight account
types, fourteen entry points including `list_for_resale`, `execute_resale`, `cancel_listing` and
`set_cap`, plus runbook steps and six negative tests. It was never built, deployed or tested, and
it said so itself. Its error is not fabrication; its error is surface.

**Who decided.** The operator, on 2026-11-07. The decision, its evidence, its consequence and the
rejected alternatives are `records/F-decision-log.md` D6. The reconciliation, including the list
of files outside this one that still assert the rejected position, is
`records/ON-CHAIN-RECONCILIATION.md`.

---

## The three decisions

The superseded design and `ON-CHAIN-DESIGN.md` disagreed on three things. All three went to the
later document. One line each, with the reason:

### 1. Escrow and a listing surface: rejected. Per-ticket record plus transfer hook.

The hook is what makes an off-platform transfer impossible rather than merely detectable, so the
custody record is complete for every hooked mint, and adding an escrow on top of that does not
close the hole that matters: a seller and buyer who agree a price off-chain can route a face-value
sale through the escrow and settle the rest in cash, so the recorded price becomes a real payment
without becoming the price (`ON-CHAIN-DESIGN.md` §4.2.1). It also rebuilds the listing, buy and
checkout surface plan item (a) says the product does not have, and it was estimated at 10 to 14
hours against 3 to 5 for the record plus hook, with cancel, timeout, fee-split and dispute arms
that a laptop session cannot verify before Sunday. It is not a bad design; it is the right design
the day the cap must bind on money, which is tier (c) in `ON-CHAIN-DESIGN.md` §5.

### 2. Sybil nullifier and per-wallet holding cap: not built, and not claimed.

This is the one point where the superseded document is right about the problem, and the later one
says so: the scalper mechanism is many wallets, not one high price, and nothing else in either
design touches it. But the nullifier only guarantees "this commitment was registered once", with
the identity behind it proven off-chain by whatever document an organizer accepts, so the
invariant is far weaker than the sentence it would license in a pitch; it needs an identity
provider and a decision about what the chain may remember about a person, neither of which
exists; and half of it is off-chain, so Agave plus `spl-token` cannot check it. The design
therefore claims nothing about bots (`ON-CHAIN-DESIGN.md` §4.2.6), and that non-claim is part of
the submission rather than a footnote to it.

### 3. Cap fixed when the policy is created: stands. `set_cap` refused.

A mutable cap reopens precisely the hole the fixed one closes: raise the cap, sell, lower it
again. The superseded document mitigates that with an effective-date stamp and a re-check at
execution, but the mitigation is only as good as the record of when the cap changed, which means
a policy-history account, one more instruction and one more negative test on a surface that is
already the largest risk to the deadline. A cap written once at `create_event`, before any ticket
is minted, is a stronger claim in one sentence and costs one line to verify on a laptop; a movable
cap is a genuine product feature and is deferred with its cost named (`ON-CHAIN-DESIGN.md` §11),
not dropped silently.

---

## Where each part of the old document went

| superseded section | where to read it now |
|---|---|
| §1 what the program must do | `ON-CHAIN-DESIGN.md` §1.1, §1.2, and §13.1 for the non-responsibilities, carried over |
| §2 hook plus escrow, not one or the other | replaced: `ON-CHAIN-DESIGN.md` §1.3, §1.4, §3.9. The escrow half is decision 1 above |
| §3 account layout (8 types) | `ON-CHAIN-DESIGN.md` §2. No `Listing`, no `Nullifier`, no `Config`; six types remain |
| §4 instruction set (14) | `ON-CHAIN-DESIGN.md` §3. Nine entry points: `list_for_resale`, `execute_resale` and `cancel_listing` are gone with the escrow; `set_cap`, `close_event` and `revoke_verification` are refused; the rest are renamed (`issue_ticket`, `transfer_ticket`, `grant_verification`) |
| §5 hook checks | `ON-CHAIN-DESIGN.md` §3.9, and §13.2 for the reason the verification gate must fire inside the hook, carried over |
| §6 why the cap lives on-chain | `ON-CHAIN-DESIGN.md` §1.2, §3.11, §4. The anti-sybil bullet is decision 2 above |
| §7 laptop steps | `ON-CHAIN-DESIGN.md` §6, fourteen steps (0 to 13). §13.3 keeps the backend handoff variable block |
| §8 what is design-only | `ON-CHAIN-DESIGN.md` §5, §10, §11 |

Nothing in the old document was carried over whole. Three pieces it had and the later document
lacked were moved into `ON-CHAIN-DESIGN.md` §13, which is marked as carried text: the statement
that the program has no pricing responsibility, the argument that the verification gate must fire
inside the transfer rather than before it, and the environment variables that point the backend at
a deployed program.

## What is no longer true of this repository

If a sentence anywhere says the Ticketpath program has an escrow, a listing account, a
`set_cap` instruction, or a nullifier, that sentence is describing the superseded design.
`records/ON-CHAIN-RECONCILIATION.md` lists every such line that the reconciliation pass found
outside this file, for the orchestrator to fix. Nothing has been deployed in either design.

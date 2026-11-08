# 29: Nineteen things this project could put on Solana, costed against the hours that are left

**Written:** 2026-11-08T00:47Z to 01:40Z. **Event:** MLH Solana Hackathon, partnered, online,
2026-11-06 17:00Z to 2026-11-08 18:00Z. **The clock that governs every number below:** hacking ends
16:45Z, the initial submission freezes at 15:00Z, and at the time of writing that is **about thirteen
hours**, of which perhaps 8 are usable. **Field size, last measured by another pass:** 36 submissions at 22:30Z
(`records/findings/27-submission-surface-and-storyboards.md` §1.3).

**What this file is.** The operator named eleven ideas and asked for an evaluation of each plus more
that are not on his list, and for a ranking and some combinations, with no decision made. This is that
evaluation. Nothing here was built, nothing was decided, and the choice is his.

**What it is not.** It does not restate `records/findings/23-hackathon-score-analysis.md` (the rubric,
the four-item materials test, the winner sample), `25-solana-first-principles-primer.md` (how the chain
works), `26-identity-bound-wallets.md` (identity) or `27-submission-surface-and-storyboards.md` (what a
judge sees). It refers to them, and where it disagrees it says so and says why.

**Labels.** **DOCUMENTED** means a primary source says it and the URL is in §12. **DOCUMENTED-IN-CODE**
means the program source or the interface crate says it. **MEASURED** means this pass ran something and
quoted the result. **UNVERIFIED** means I could not settle it and say what would. **ESTIMATE** means
hours are my judgement for one competent operator working with the tools already in this tree, and they
are the softest numbers here. Predictions about how a judge will score carry the programme's class **D**
(a plausible mechanism with no evidence behind it), as `23-…` did, because MLH publishes no scale.

---

## 0. The answer in one paragraph

The largest thing that changed since `23-…` was written is that **the devnet publish has run and its
artefacts are real on the chain**: a program account, a hooked Token-2022 mint, a quote memo, an at-cap
transfer that landed and an over-cap transfer that the cluster refused with error 6010, all finalized,
all re-verified by this pass against devnet (§1). That moves the four-item materials test from 0 of 4 to
**2 clear and 2 partial**, and it changes what the next hour is worth: items (a) and (b) are done, so the
remaining marginal value is in (c), a program we did not write doing work the product depends on, and
(d), the product reading chain state back. Against that, of the operator's eleven, four are worth
keeping and only one of those is worth building for its own sake (the artist fee is the best
mechanism-per-hour in the document, and the other three are the substrate, the demo's spine and the
surface); of the eight I add, two are stronger than anything on his list, one is a documented
impossibility that should be recorded rather than attempted, and the rest are post-event. The single most useful sentence in this file is a limitation that
almost every cap-shaped idea in the list walks into: **an SPL transfer carries an amount and no price,
so a hook enforces a number the seller declares, and a seller who is willing to lie pays the real price
in a side transfer** (§6 F1). Anything that survives that has to put the ticket or the money inside the
program's own reach, or tax the token instead of the price. The external fact that makes the cap worth
building anyway arrived with the prior-art sweep (§6 F6): Ireland has banned resale above the original
price since 2021 with a penalty of up to €100,000, the UK has announced the same, and neither state has a
cheap way to know that a resale happened. **The enforcement layer is the product; the policy is not ours.**

---

## 1. The state of the tree, re-measured, because it decides every ranking below

`23-…` §3.5 scored the materials test at 0 of 4 from a tree where `records/devnet-artefacts.json` did
not exist. It exists now. This pass did not take that on trust, because a JSON file on disk is a claim:

**MEASURED 2026-11-08, between 01:00Z and 01:20Z**, three `getSignatureStatuses` calls with `searchTransactionHistory`
against `api.devnet.solana.com`, quoting the signatures in the artefact:

| Leg | Slot | Status | Error |
|---|---|---|---|
| the quote memo | 519,845,921 | finalized | none |
| the transfer at the cap | 519,845,933 | finalized | none |
| the transfer one lamport over the cap | 519,846,008 | finalized | `InstructionError [0, Custom 6010]` |

And the artefact's own contents, read this pass: `cluster: devnet`, `programId: 5EJ1GU3M…4eva`,
`mint: 6RPS73X5…nimV`, `faceLamports: 1000000000`, `capBps: 2500`, `modelVersion: engine-2026-11-07`, a
memo text of the form `ticketpath:quote:<quoteId>:<sha256>`, and the patch above recording which leg was
accepted and which refused.

So the four tests, honestly:

| # | Test (`23-…` §2.4) | Verdict now | Why |
|---|---|---|---|
| a | an account that belongs to this project | **PASS** | a program account and a mint, both on devnet, both this project's |
| b | a transaction signature with a block time | **PASS** | three signatures, finalized, slots and block times recorded |
| c | a program we did not write, doing work the product depends on | **PARTIAL** | Token-2022 processed the transfer and made the hook CPI, and its `Transfer` layout is the reason the price has to be staged at all. But the decision is ours and Token-2022 is the transport. A sceptical judge calls this unmet |
| d | the product reading that state back | **PARTIAL** | the artefact carries exactly the three things the console's gate requires (`cluster`, a signature, the memo grammar). The render was **not** re-run in this pass: no server was listening and starting one is a machine action this file did not need |

**What that means for cost.** The hour that used to buy the most no longer exists; it has been spent. The
two remaining gaps are (c) and (d), and they are the two cheapest things in this document: (d) is a
five-minute render against a real artefact, and (c) is bought for about three hours by making a
third-party program's own accounting load-bearing rather than decorative (§4.7, the artist fee). Every
ranking in §8 is built on that, and any ranking in an earlier record is now costing a world where the
publish had not happened.

**One correction to `25-…` §6.6, recorded rather than edited into that file.** The primer says the hook
program id changes through `SetAuthority(AuthorityType::TransferHookProgramId)`. The authority *is* set
that way, but the program id itself is changed by a separate instruction, `TransferHookInstruction::Update`,
which also accepts `None` (**DOCUMENTED-IN-CODE**, `solana-program/transfer-hook`, `interface/src/instruction.rs`).
The conclusion is unchanged and stronger: a hook is immutable only once its authority is revoked, and the
revocation is a step in the publish path that a reader can check.

---

## 2. Three filters, and the trap

Every idea below is scored on the same four things, and two of them come from records already written.

**Filter 1, the materials test** (`23-…` §2.4). Does it add an account, a signature, a third-party
program in the decision path, or a read-back? This is the Top 3 sentence applied literally.

**Filter 2, whose discretion is removed** (`25-…` §11.2). If nobody's, the chain is decoration. This is
the published Top 3 criterion in the organisers' own words: "Solana for something it's good at …
not a chain bolted onto a web2 app" (`23-…` §2.3).

**Filter 3, forty seconds** (`23-…` §2.5). Four minutes per project, stack-ranked against seven
neighbours, top three only. An idea that needs ninety seconds of prose to land is an idea that does not
land. This is why a refusal beats a table.

**The trap, and it has already caught one idea.** `26-…` §6.1 found that the soulbound pass "deletes the
engine's input": no resales means no resale record, and the record is the product's only evidence. Every
idea below was checked against a harder version of that test: **does it remove the thing the engine
learns from?** Ideas that make tickets untradeable, or move every transaction off the chain we read, fail
it.

---

## 3. One mechanism fact that most of the cap ideas ignore

This is stated once here and referred to nineteen times below, so it is worth getting exactly right.

**A token transfer has no price field.** `Transfer { amount: u64 }` and `TransferChecked { amount: u64,
decimals: u8 }` are the whole instruction, and the hook is called with an `Execute` payload of 8
discriminator bytes plus `amount: u64` and nothing else (**DOCUMENTED-IN-CODE**,
`solana-program/token-2022` `interface/src/instruction.rs`, and the transfer-hook interface crate; the
discriminator is `sha256("spl-transfer-hook-interface:execute")[0..8]` = `692565c54bfb661a`, which this
interface crate computes from that string). The token program calls the hook "after all other transfer logic".

Three consequences, and every cap idea lives or dies on which one it picks:

1. **A staged price is a declaration.** If the price arrives in a record account that someone wrote
   earlier, the seller writes it. The hook then enforces honesty on the honest and nothing on the rest.
2. **A payment inside the same instruction is not a declaration.** If the buyer's lamports move to a PDA
   in the same transaction that moves the ticket, the cap binds real value, because the number and the
   money are the same object. That costs a venue, with a venue's state machine.
3. **A fee on the token needs no price at all.** `TransferFeeConfig` withholds a basis-point amount on
   every transfer of that mint, whoever moves it and whatever it claims to have been paid
   (**DOCUMENTED**, `solana-program.com/docs/token-2022/extensions`: "some amount is withheld on the
   recipient account"). It is blind to price and that is exactly why it cannot be lied to.

The repo already says (1) and knows (2) costs too much (`docs/ON-CHAIN-DESIGN.md` §1.3, decision D6 in
`records/F-decision-log.md`). It has not said (3), and (3) is the strongest thing available this weekend.

---

## 4. The eleven the operator named

Each entry has the same six fields. Hours are ESTIMATE, given in hours rather than days because about
thirteen are left; divide by six for a working day. Rubric deltas are class D and are against the current
54/100 in `23-…` §3.6, not against zero. Fit with `23-…` is the materials-test line and the rubric delta;
fit with `25-…` is filter 2 above, and where a numbered section of the primer bears on an idea it is cited
in the entry.

### 4.1 Idea 1: the model's resale cap published on chain, read by the transfer hook

**Mechanism.** Built. A `TicketRecord` account at `["record", mint]` holds `face_value_lamports`,
`cap_bps`, `pending_price_lamports`, `status`; the mint carries the `TransferHook` extension; the hook
refuses `amount != 1`, refuses a price above `face × (1 + cap_bps)`, and refuses a transfer with no
staged price (**DOCUMENTED-IN-CODE**, `programs/cap_hook/src/lib.rs:78-91`, `:102-104`, `:53`). The
published part is the record: any client, and any program, can read the cap without asking us. The
predicate is integer `u128` with no division, so it is exact at the boundary, and the devnet refusal is
on chain.

**Cost.** 0 hours, it exists. The unclaimed half is (d): about 0.25 h to render the console against the
artefact, 1 h to make the refusal the first thing on the page.

**Materials test.** (a) yes, (b) yes, (c) partial, (d) one render away. It does not convert (c).

**Rubric.** Technology +0 to +1 (it is already counted at `23-…` §3.1), Design +1 to +2 if the refusal
moves above the fold, Completion +1.

**Judge.** **STRONG on the refusal, FLAT on the publication.** A judge does not experience "a cap is
readable"; a judge experiences a transaction failing. The winner sample supports the second half
directly: LOKA Pay's own Devpost text is built on "the chain refuses it with `SerialUsed`", and school of
thought's on "refused repeats and self-likes, with the refusal on chain" (`23-…` §4.2). Class D.

**Attack surface.** (i) **Side payment.** Declare 1 lamport, pay 900 SOL in a separate transfer. The hook
admits it. This is not a bug in the program; it is the standard (see §3). (ii) **The venue is optional.**
A mint without the extension is unaffected forever. (iii) **The hook can be repointed** by its authority
via `TransferHookInstruction::Update` until that authority is revoked. (iv) **The declared price can be
staged by the seller** in the same transaction, so a hook-aware seller who lies pays nothing for lying.
(v) **Confidential transfers send `u64::MAX` as the amount**, so the hook refuses every confidential
transfer of a ticket: the cap and private amounts are mutually exclusive here (§6 F3).

**Verdict.** It is the substrate, not the idea. It is worth its place in the demo as a refusal, and its
honest claim is "the cap is enforced inside this venue", never "the cap cannot be broken". And the policy
is not ours to claim: Ireland has capped resale above face value since 2021 and the UK has announced the
same (§6 F6), so the novelty claim has to be the enforcement and not the rule. If the record does not
say that first, a knowledgeable judge says it for us, and about the side payment he is right.

### 4.2 Idea 2: forecasts logged on chain before outcomes, publicly scored

**Mechanism.** Three cost tiers, and they are different products.
(i) **Memo.** One `Memo` instruction carrying a SHA-256 of the forecast text plus the as-of slot. Cost
5,000 lamports. Precedent: Backfill won an MLH Solana prize with exactly this and a "Verify now" button
(`23-…` §4.3).
(ii) **A program-owned record.** A `Forecast` account per (event, as_of) holding the band in lamports,
the sample size, the model hash, an outcome field and a score field. Anyone reads it; we write the
outcome.
(iii) **Commit then reveal.** The hash lands before the window closes, the plaintext after.

**Cost.** (i) 1 to 1.5 h. (ii) 3 to 4 h including a scored log with two settled events. (iii) adds 1.5 h.

**Materials test.** (i) converts (b) only, which is already converted. (ii) converts (d), and (a).

**Rubric.** Technology +1 to +2, Learning +1 (a scoring record is a research posture made visible),
Completion 0, Design 0 unless the score is on screen.

**Judge.** **GOOD as narrative, WEAK as a demo.** "We wrote the number down before we knew the answer" is
one of the few sentences a judge remembers from a pricing project, and the one directly comparable
winner said the same thing about a frozen ruleset. But nothing moves on screen, and in forty seconds a
still table loses to a transaction failing. Class D, leaning on the Backfill precedent which is real.

**Attack surface.** (i) **Event cherry-picking**: score the three that worked. Answer: publish N, score
all N. (ii) **As-of drift**: backdate the claim. Answer: the slot is in the same transaction. (iii)
**Metric shopping**: choose the error measure after seeing the errors, which is the same sin as
backdating and harder to see. Answer: the scoring rule is committed in the same transaction as the
forecast. (iv) **The scorer is us.** The outcome is not on chain and there is no ticket-outcome oracle;
the realised price comes from our own record, so the score is "our number, our arithmetic, disclosed".
Say so. (v) The forecast is about an event with no resale history, which is the cold-start case the
engine already refuses (`02-e-cold-start.md`); scoring refusals as failures would be dishonest and
scoring only the answered ones is cherry-picking.

**Verdict.** The best story per hour in the document and the weakest demo. It is a component of the
first combination in §9, not a headline.

### 4.3 Idea 3: model versions hashed on chain

**Mechanism.** A `ModelVersion` account, or the same memo, carrying the SHA-256 of the artefact that
produced a quote: the code, the parameter file, the training window, the refusal policy. The artefact
already carries `modelVersion: engine-2026-11-07` and a `quoteHash`, so the first version of this is
built without anyone noticing.

**Cost.** 1 to 1.5 h to make it checkable (a recipe a stranger can recompute), 0.25 h to leave it as a
string.

**Materials test.** (b), which is done. No movement on (c) or (d).

**Rubric.** Technology 0 to +1. Alone, nothing else moves.

**Judge.** **FLAT alone, and mildly negative if oversold.** Nothing in the winner sample won on a hash;
in Backfill the hash was the supporting line under a frozen rule. There is a self-inflicted failure mode:
a digest nobody can recompute is a decoration, and a judge who asks "hash of what?" and gets "the model"
learns that the commitment is theatre.

**Attack surface.** Ambiguity is the attack: a hash of an unspecified artefact can be satisfied by
almost anything, including a file written after the fact that happens to hash to the committed value.
The defence is publishing the recipe (paths, versions, the excluded files) in the same commit, not the
digest.

**Verdict.** Free once (2) or (4.12) exists, worthless alone. Never standalone.

### 4.4 Idea 4: a DeepSeek agent swarm trading on devnet through the real program

**Mechanism.** N agents, each a wallet, each posting staged prices and moving tickets through the hook.
Only the actions land on chain; the reasoning, the loop and the coordination run off chain. It needs N
funded wallets, and the only funding path is the web faucet, whose own page says "AI agents should not
use this faucet" (`23-…` §5.1), so the operator does that part by hand, once per wallet.

**Cost.** 10 to 16 h and the tail is the risk: key management, funding, retries, and an agent that
half-runs at 14:30Z.

**Materials test.** (a) (b) (d) yes; (c) no, the program is ours.

**Rubric.** Technology +2 to +3 (it is a lot of moving parts), Design +1 if the swarm is visualised,
Completion −2 if it is visibly unfinished. It nominally matches the AI track's "AI and Solana each do
real work" (`23-…` §2.3).

**Judge.** **RISK, and the evidence points the same way twice.** A four-minute exposure cannot show a
swarm; it can show a number going up. Three of the four winners read in `23-…` §4.2 won on one thin
checkable artefact, not on agent count, and the fourth on two small programs. Class D, but the direction
is consistent.

**Attack surface.** The agents are ours, so "trading" is self-dealing and proves nothing economically;
wash trading is derivable from the ledger in one query and a judge may ask whose money moved; and the
honest question, "what does the swarm know that one agent does not?", has no answer in this design. If
the answer is "nothing", it is theatre with a bill.

**Verdict.** Cut, or narrow it until it is idea 5. Two agents whose *disagreement* is the point (one
bids above the band and is refused, one bids inside it and settles) is the only version of this that
survives forty seconds, and that version is not a swarm.

### 4.5 Idea 5: a scalper agent refused by the cap

**Mechanism.** One scripted buyer that tries to (i) buy at face and (ii) resell at three times face. The
second attempt fails inside the runtime with the program's own code, and the failure is a signature on a
public cluster. `programs/cap_hook` already emits it: `CapExceeded = 6010`, and devnet already holds one
(§1).

**Cost.** 1 to 2 h, most of it the script's narration rather than the chain.

**Materials test.** It converts nothing new. It converts the *video*, which is a different asset and the
one that gates eligibility (`23-…` §5.0 P1).

**Rubric.** Technology +1 (the refusal is technology evidence a judge can read), Design +1.

**Judge.** **The strongest single artefact in this document.** Two of the four winners put a refusal on
screen and their own text sells it that way. Class D on the number, not on the direction.

**Attack surface.** It demonstrates a cap over a *declared* price, which is the weak point in §3. If the
demo does not say "we enforce this inside our venue, and a side payment defeats it" in the same breath,
the artefact becomes an overclaim the moment a Solana-literate judge asks. One extra sentence turns the
weakness into the most credible thing in the video.

**Verdict.** The spine of the demo. Cheap, honest, already built. Do.

### 4.6 Idea 6: price-drop protection, a rebate paid from escrow

**Mechanism.** A `RebatePool` PDA funded from primary sales; if the realised resale price some days after
the event is below what the buyer paid, the buyer claims the difference, capped, inside a claim window
read from the `Clock` sysvar. Needs a realised-price observation, a claim instruction, expiry, and
double-claim prevention.

**Cost.** 8 to 12 h, and the demo needs a price *fall*, which means either waiting or injecting one.
Injection is honest if it is labelled, and labelled injection is a weaker artefact than a real one.

**Materials test.** (a) (b) (d). No (c).

**Rubric.** Technology +2, Design +1, Completion −1 because nothing about a seven-day protection is
visible in ninety seconds.

**Judge.** **CONFUSING in forty seconds, good in a pitch.** No winner in the sample is
insurance-shaped. This is a product for a promoter, not a demo for a judge.

**Attack surface.** (i) **Self-dealing**: buy, then move the ticket between your own wallets at a low
price to move the observed price, then claim. The observation must come from our own band rather than a
market quote, or the attack is free. (ii) **Solvency is our honesty**: a pool funded from sales is a
liability the organiser carries, and the "protection" is a subsidy dressed as insurance unless premiums
are priced. (iii) The claim window needs the same expiry discipline as any clock rule, and an expired
claim is a support ticket.

**Verdict.** Post-event. Strong product, wrong forty seconds.

### 4.7 Idea 7: resale revenue share to the artist

**Mechanism.** `TransferFeeConfig` on the mint, 500 to 1000 bps, with `maximum_fee` set deliberately. The
fee is withheld on the recipient's token account and withdrawn by the mint's `withdraw_withheld_authority`
to the artist's wallet (**DOCUMENTED**, extensions page, and `MAX_FEE_BASIS_POINTS = 10_000` in the
token-2022 source; withdrawal "requires the mint's withdraw_withheld_authority" as a signer). This is the
only mechanism in the list that follows the ticket **everywhere**: to a wallet that never touched our
program, through a marketplace we have never heard of, inside a program that is not hook-aware.

**Cost.** 2 to 3 h: set it in the publish path at mint initialisation, add a withdraw step, add one console
line that reads the withheld balance.

**Materials test.** (a) (b) (d) yes, and **(c) honestly yes**: the withholding, the accounting and the
movement are Token-2022's, and the product's revenue line depends on them. Our program does not compute
the fee.

**Rubric.** Technology +2 to +3, Completion +2, Design +1. Learning 0.

**Judge.** **STRONG on comprehension and on precedent-free clarity**: "the artist gets 5% of every resale,
taken by the token program, not by us" is one sentence, one number, and a third party receiving money.
It is also the canonical Token-2022 demo, so a Solana-literate judge has seen the extension and will
respect it being used for the reason it exists. Class D.

**Attack surface.** (i) The fee is withheld on the **recipient**, so a buyer who pays the listed price
receives less than they expected. That is a real UX defect and must be shown, not hidden: a demo that
pops a surprise deduction is honest, a demo that pretends the buyer got the full amount is not. (ii) The
fee does not stop a transfer; it taxes it. A seller willing to pay 5% still sells at 3× face, so this is
a revenue instrument and not a cap. Do not let it be introduced as one. (iii) Withdrawal is a separate
step, and an artist who never withdraws has a balance nobody can spend; a demo that does not show the
withdraw looks broken. (iv) `maximum_fee` interacts with price: a 5% fee on a 0.1 SOL resale and on a 10
SOL resale are governed by the same cap, so choose the cap deliberately and say what it implies.

**Verdict. The best mechanism-per-hour in the document.** It converts (c), it pays a third party, it
needs three hours, and it makes the engine's own number (the recommended price) the thing the fee is
computed on, which is the one place the pricing work touches the money.

### 4.8 Idea 8: a fair-launch claim window

**Mechanism.** A `Sale` account with start and end slots, read from the `Clock` sysvar (40 bytes, slot,
epoch, `unix_timestamp`; readable in-program via `Clock::get()`, **DOCUMENTED-IN-CODE**, `solana-sdk`
clock). Mint or redeem instructions refuse outside the window. With allocation: a per-wallet entitlement
account created before the window.

**Cost.** 2 to 4 h for the window. 8 to 10 h for an oversubscribed allocation that is actually fair.

**Materials test.** (a) (b) (d).

**Rubric.** Technology +1 to +2 (a clock check is thin), Design +1 if a countdown is on screen.

**Judge.** **FLAT alone.** A countdown is a thing every hackathon has. It becomes GOOD only if it answers
a question the judge already believes is unfair, and then only with the allocation problem solved.

**Attack surface.** A window is not fairness: bots are faster inside any window, and **nothing about a
window limits one person to one ticket**. Without a nullifier, "fair launch" is a slogan, and `25-…` §12
and `26-…` §2 both refuse to paper over the sybil gap. The honest version names the gap.

**Verdict.** Cheap support for a combination, not a headline, and only if the word "fair" is retired or
defined.

### 4.9 Idea 9: wallet reputation from the ledger

**Mechanism.** Two different things share the name. (i) **An off-chain score** computed from the custody
ledger (hold duration, hop count, markup history, attendance), attested on chain as a program-owned
`Reputation` account or an SAS attestation issued by our key. (ii) **An on-chain score** computed in a
program from accounts it is handed, which is expensive and, per the attack list, close to meaningless.

**Cost.** (i) 4 to 6 h including the attestation path. (ii) 10 h plus.

**Materials test.** (i) converts (c) only if the attestation service is trusted as a third party, which
it is not (anyone may create a credential; **DOCUMENTED**, `solana-foundation/solana-attestation-service`
README), so (c) stays partial.

**Rubric.** Technology +1 to +2, Learning +1.

**Judge.** **FLAT to negative unless the score changes an outcome on screen.** A number in a table is not
a mechanism, and a badge that gates nothing is a badge.

**Attack surface.** (i) **Wash trading builds reputation**: two wallets, 5,000 lamports a hop, and a
score that rewards volume rewards the scalper first. (ii) There is no ground truth for "a good buyer"; the
programme's own evidence says identity buys data integrity and market design, not valuation (`26-…` §4.7).
(iii) A score that gates access is a product policy the operator has not made, and a score that only
decorates is not worth the deposit.

**Verdict.** The strong version is a **parameter, not a gate**: the band widens for a wallet that has held
and attended (§5.2 B, and §5.3 C). That is a different idea and a better one, and it needs the band to be
enforceable first.

### 4.10 Idea 10: proof-of-attendance badge

**Mechanism.** A `NonTransferable` Token-2022 mint, one per attendee, minted at check-in. The extension's
refusal happens before any authority check (**DOCUMENTED-IN-CODE**, `token-2022` processor), and the
holder can still burn and close. Alternative: a Metaplex Core asset at about 0.003 SOL with the Freeze
Delegate plugin doing the same job (**DOCUMENTED**, Metaplex Core docs).

**Cost.** 3 to 5 h: a mint path, a check-in action, a read. Plus **about 2.55M lamports of deposits per
attendee** (a 1,066,800 mint plus a 1,488,440 token account at the measured 5,080 lamports per byte), so a
20,000-seat venue is ~51 SOL of refundable capital before fees (`25-…` §7.5 arithmetic, extended).

**Materials test.** (a) (b) (d). No (c).

**Rubric.** Technology +1, Design +1, Completion +1.

**Judge.** **SEEN IT.** A non-transferable badge is the most common Solana hackathon artefact, and the
winner sample contains one (Weenie Beanie's soulbound credential), which won as part of a bigger product
rather than as the product.

**Attack surface.** Forgery is impossible; **attendance is not what is proven.** The minter is the venue,
so the badge proves "the venue said you came", which is exactly the trust it was supposed to remove.
Saying that in the record is worth more than the badge.

**Verdict.** Cheap, low novelty. Useful only as the input to (9) or as the loyalty gate for next season's
presale.

### 4.11 Idea 11: checkout through Blinks and Solana Actions

**Mechanism.** A GET returns action metadata JSON (absolute `icon` URL required, plus `title`, `description`,
`label`); a POST with `{"account": "<base58>"}` returns a base64 transaction; `actions.json` at the domain
root maps `pathPattern` to `apiPath`; CORS needs `Access-Control-Allow-Origin: *` and an
`Access-Control-Allow-Headers` list that includes `Content-Type, Authorization, Content-Encoding,
Accept-Encoding`; chaining is `links.next` (**DOCUMENTED**, `solana-developers/solana-actions`,
`packages/actions-spec/SPEC-v2.3.md`, which is the latest prose spec: the package is 2.4.2 and there is no
`SPEC-v2.4.md`; `linkedActions` does not exist in the spec and was a wrong guess).

**Cost.** 4 to 6 h plus hosting. The transaction must fit 1,232 bytes legacy: a mint, an ATA create, a
transfer and a memo fit; an escrow with four accounts of state probably does not.

**Materials test.** (a) (b) (d) yes. (c) if the transfer's fee accounting is load-bearing, which it is
once (7) is set.

**Rubric.** Design +2 to +3 (it is the only idea here a judge can operate on their own phone with no
setup), Completion +2, Technology +1.

**Judge.** **STRONG if it unfurls, catastrophic if it does not.** A dead Blink is worse than no Blink: it
is a public URL that fails in the judge's own client. LOKA Pay's "seven-stop judge guide" at a public URL
is the same instinct, make the judge a user, and it is one of the four winners read in `23-…` §4.2. Class
D.

**Attack surface.** (i) **Token gating is not in the spec** (**MEASURED-ABSENT**: no gate field in the
spec, the docs page, or the Solana Pay spec; the nearest affordances are `disabled` and server-side
`ActionError`), so any "only verified fans can buy" claim in a Blink is our server's opinion. (ii) The
client set that renders Blinks is not universal, and a judge may paste the URL into a browser and see
JSON. (iii) Hosting is a new surface with a 14-hour clock, and a POST that breaks at 14:00Z will not be
fixed.

**Verdict.** The highest Design-per-hour in the list **if hosting is already solved**, and a hosting
project wearing a checkout costume if it is not. The reverse of idea 1's problem: it is all presentation
and no new mechanism.
---

## 5. Eight that are not on his list

Chosen because each is either cheaper than an idea it replaces, or does something none of the eleven does.
The order is the order they arrived in my head, not a ranking; §7 ranks.

### 5.1 A: the price band as a public feed (the engine becomes an oracle)

**Mechanism.** One program-owned account per event, `["band", event]`, holding: face value, band low, band
high (lamports), as-of slot, sample size, a refusal flag, a model hash, an authority. Written by our
program; read by (i) our own transfer hook as the cap, (ii) **any other program, by CPI**, (iii) any
client by `getAccountInfo`. History is append-only, latest wins by slot, so a band cannot be silently
revised without leaving the old one readable.

**Why it is the keystone.** It is the only idea here that makes Solana do something a web2 API cannot:
hand a number, its provenance and its as-of time to a stranger who can consume it without an integration
meeting, and prove afterwards that it was not rewritten. That is the "composability" and "verifiable"
half of the Top 3 sentence (`23-…` §2.3) in one account. It also turns the engine from a dashboard into
infrastructure, which is the difference between a project that prices tickets and a project that is the
price source for ticketing.

**Cost.** 4 to 6 h: one instruction, the account layout, the publish path, the console read-back, and a
test that a stale band is refused.

**Materials test.** (a) (b) (d) yes. (c) only if a program we did not write actually reads it, and our own
hook reading our own feed does not count. Honest score: 3 of 4, with (c) coming from §4.7's fee accounting
unless a real third party consumes the band.

**Rubric.** Technology +2 to +3, Learning +1, Design +1 if the account is rendered as a card a stranger
can open.

**Judge.** **STRONG, and unusual.** A judge who has seen ten NFT-ticket demos sees something else here: a
feed. The custom-program share of the winner sample is 18% (`23-…` §4.1), so any deployed program is
already differentiating; a program that publishes a number for others is differentiating twice.

**Attack surface.** (i) The band is our opinion; publishing it does not make it right, and a consumer
inherits our error. This is why `sample_size` and the refusal flag must be in the account and not in a
README, and why the doc must say the feed carries its own uncertainty. (ii) The authority can write a new
band, so "immutable" is a claim about the history, not the head. (iii) A feed with no consumer is a
database row: if nobody reads it, the composability claim is a story.

**Verdict.** The keystone. Everything else in this document either feeds it (2, 3, 9) or consumes it
(1, C, F, D).

### 5.2 B: mint to escrow, receipt to the wallet

**Mechanism.** Invert custody: the ticket tokens are held by a program PDA and never by a user. The user
holds a receipt, either a second non-transferable mint or an entry in a `Holding` account. Every movement
of the ticket is an instruction, so the program is in the path of 100% of transfers by construction, and
because the payment and the transfer are in the same transaction, **the declared-price hole of §3
disappears for anything that goes through the venue**.

**Cost.** 12 to 18 h. This is a marketplace skeleton: list, buy, cancel, settle, refund, and the state
machine that stops a wrong `pending_dest` from being a theft.

**Materials test.** 4 of 4.

**Rubric.** Technology +3 to +4, Completion −2 to −3 at this clock.

**Judge.** **STRONG on technology, weak on finishability.** It is the shape of an exchange, and exchanges
are what the venture-shaped competition rewards, not a four-minute hackathon slot (`23-…` §4.5).

**Attack surface.** It is still a venue, so the cap binds only inside it (`25-…` §6.5), but the venue is
now the only place the ticket exists, which is materially stronger than any hook. The new surface is
state: a receipt/escrow mapping is a machine with refunds, and refund machines have bugs that are thefts.

**Verdict.** The right architecture for a real product and the wrong answer for the hours that are left. Name it
as the post-event direction and do not build it now. It also contradicts the repo's own decision D6,
which rejected escrow on scope grounds, so adopting it would be a decision, not an implementation.

### 5.3 C: enforce the band on both sides (a floor as well as a cap)

**Mechanism.** The same record, one more comparison: refuse a staged price **below** band low as well as
above band high. Two error codes, three tests (inside, under, over). The model already produces a band,
not a point (`ticketpath/core/value_band.py`), so the chain would enforce the shape of the model's own
output rather than a single number.

**Cost.** 1 to 2 h once the hook is deployed and its test suite exists.

**Materials test.** No change.

**Rubric.** Technology +1, Design +1 if the video shows two refusals instead of one.

**Judge.** **GOOD.** "The band is enforced on both sides" is a sentence a judge remembers, and it is
visible in ten seconds as two failures. It also reads as a *policy* a promoter would buy, which is rarer
than a cap. No precedent in the winner sample.

**Attack surface.** (i) A floor is price-fixing-adjacent and it breaks the cheap-ticket case: a fan who
cannot afford the floor cannot buy. (ii) A floor plus a cap converts the model's advice into a rule, which
is a product decision: the operator would be the party that sets the price. (iii) The floor binds only
inside the venue, like the cap, and a ticket that cannot sell at the floor simply does not sell.

**Verdict.** The cheapest new mechanism in the file, and the best second refusal for a video that already
has one.

### 5.4 D: the flip tax, refunded on hold (a fee that is a function of time held)

**Mechanism.** Mint with `TransferFeeConfig` at a deliberately high bps (say 1500), withdraw authority
held by a program PDA. A `refund` instruction reads the custody record for that ticket, computes how long
the holder held it, and pays back a share of the withheld fee proportional to duration. Net effect: a
resale one hour after purchase pays 15%; a resale thirty days later pays close to nothing. The token
program withholds; our program rebates; **neither needs the transfer to declare a price.**

**Why this is the sharpest idea after A.** It is the only anti-scalping mechanism in this document that
is **robust to the side payment**, because the tax is on the token, not on the price. A seller can lie
about what they were paid; they cannot lie about having moved the token. It also prices the behaviour
the ticket market actually complains about (instant flipping) rather than the number (markup), which is a
better-targeted instrument and an easier sentence: "the same resale costs 15% at one hour and nothing at
thirty days".

**Cost.** 5 to 7 h: fee config, PDA authority, the rebate instruction, the hold-time source (the ledger
we already keep), tests on both sides of the boundary.

**Materials test.** (a) (b) (d) yes, and (c) yes for the withholding.

**Rubric.** Technology +2 to +3, Design +1 ("one number, two prices"), Completion +1.

**Judge.** **STRONG if shown as a pair of numbers, and novel.** No winner in the sample did it. Novelty
cuts both ways: it is not a pattern a judge recognises, so it needs the sentence, and the sentence is
short.

**Attack surface.** (i) **Hold then flip in bulk**: if holding thirty days defeats the tax, a professional
scalper just holds thirty days. That is arguably the instrument working (it is a liquidity provision, not
a flip) and it should be said out loud. (ii) **Self-dealing to farm rebates**: a holder who buys from
themselves and claims on day 31 pays the fee twice to collect once, so the pool stays solvent, but the
arithmetic should be written down rather than assumed. (iii) The fee is withheld on the **recipient**, so
the holder sees less than the price until the rebate arrives: a two-step UX that must be shown. (iv) A
rebate pool is a liability; funded by the fee itself, it is self-financing, which is the version to build.

**Verdict.** The best original mechanism for the window. Higher novelty than the artist fee, twice the
cost, and the only economic rule here that survives the attack that kills every cap.

### 5.5 E: the refund is funded before the ticket is sold (a solvency attestation)

**Mechanism.** A `RefundPool` account per event. The mint instruction refuses unless the pool balance is
at least face × supply, so the gate binds rather than decorates. A buyer reads one account and knows the
money for a cancellation exists. On cancellation, claims are open until the `Clock` passes a window.

**Cost.** 3 to 4 h: pool, gate, claim, expiry. No oracle, no price.

**Materials test.** (a) (b) (d).

**Rubric.** Design +1, Completion +2, Technology +1.

**Judge.** **STRONG on comprehension**: "the money is in an account, not a promise" needs no pricing
explanation, and promoter insolvency is a harm the judge has heard of. It is also the best third beat in
any combination here because it is *clickable*: a stranger can check the balance.

**Attack surface.** (i) The pool is funded in devnet SOL by us, so the attestation proves a balance, not
the adequacy of a liability; the mint-time gate is what makes it more than a screenshot. (ii) A claim is a
race, and the pro-rata fix is more code than the first-come version. (iii) The pool is a hot account if
claims are serialised through one counter: use per-claim accounts.

**Verdict.** The best non-pricing idea in the list, and a cheap third beat.

### 5.6 F: the primary price as a committed schedule (on-chain decay)

**Mechanism.** The primary price is a function of the `Clock` and remaining inventory, committed before
the sale in a `Schedule` account: start price, floor price, decay per slot or per epoch, and the model
hash that produced it. The buy instruction computes the price; no human picks it at sale time. Inventory
per section rather than per event, because one global counter is a hot account and will serialise
(`25-…` §10.1).

**Why it matters.** It is the only idea in this document that makes the **engine load-bearing on the
primary side**, which is where the product actually lives. Today the engine advises; with a schedule it
sets the price, publicly, in advance, with no ability to reprice mid-sale. That is exactly "an ordering
machine and a clock and a public commitment", the three things the chain has and a web2 service does not
have to give.

**Cost.** 6 to 9 h: the schedule account, the price function in integer lamports (the arithmetic already
exists in `ticketpath/core/markup.py`), the buy instruction, a rendered decay table, and boundary tests.

**Materials test.** (a) (b) (d), (c) no.

**Rubric.** Technology +2 to +3, Design +1 to +2 (a decay curve is the most visual artefact the engine
can produce), Completion +1.

**Judge.** **STRONG on clarity if the demo is a curve with real purchases at two times**:
"this seat cost 0.031 SOL at 10:00 and 0.026 at 14:00 and nobody chose either number". Risk: it reads as
a gimmick unless the schedule is visibly derived from the model's band, and the bridge sentence is "the
schedule is the band, walked forward in time". Do not call it the first on-chain dynamic pricing: OPEN's
Ticketing Ecosystem uses that phrase as a page title for token fuel cost (§6 F6), and contested novelty is
the one kind a judge can check in a minute.

**Attack surface.** (i) **Front-running the decay**: buy just before a step down. Real, and the only
honest answers are a quantised step or a randomised one, both of which cost time. (ii) Inventory
accounting is hot-account-prone. (iii) The schedule commits the operator to a price it may regret, which
is the point and also the sales objection. (iv) A deterministic price with a public clock lets a buyer
wait; that is what a decay is *for*, but it must be said.

**Verdict.** The strongest product idea here and the first thing to build after the event. At this clock
it is 6 to 9 h of new state, which competes directly with the submission work that `23-…` §5.0 ranks
above everything.

### 5.7 G: hide the resale price, prove it is under the cap

**Mechanism.** A `ConfidentialTransfer` mint so amounts are encrypted, plus a proof that the hidden price
is under the cap.

**Why it fails, on documented grounds, and this is worth recording.** A transfer hook receives
`u64::MAX` as the amount on a confidential transfer, because the token program does not know it
(**DOCUMENTED**, transfer-hook interface and the token-2022 processor: "the amount is not known to the
token program and `u64::MAX` is passed as a convention"). A hook that enforces any amount policy
therefore cannot see a confidential transfer at all, and `cap_hook` refuses every `amount != 1`, so it
would refuse every confidential transfer of one ticket. The cap and confidential amounts are **mutually
exclusive on this extension surface**, and a proof would need a separate verifier, which is a research
project.

**Cost.** 14 to 20 h, and the finishability is the risk.

**Materials test.** N/A.

**Verdict.** Record it as a documented impossibility and do not build it. A judge who knows the extension
will respect the sentence "these two features cannot coexist" far more than a privacy claim that does not
survive a test.

### 5.8 H: a staked challenge to the forecast commitment

**Mechanism.** The commitment of §4.2 plus a bond: anyone may post a bond claiming "the forecast was
revised after the fact"; the bond sits in a PDA; the resolver pays the challenger if the hash chain shows
a revision. The honest version resolves **mechanically**, on the single question "do the bytes at slot X
match the hash committed at slot Y", because any resolver that needs judgement is us wearing a hat.

**Cost.** 6 to 8 h mechanical, 2 h theatre.

**Materials test.** (a) (b) (d).

**Rubric.** Technology +1, Learning +1.

**Judge.** **CLEVER, not legible.** In a demo nobody challenges, so the artefact is a button that would
work. Its real value is that it converts "trust our commit" into "anyone can check and be paid", which is
a genuine improvement on §4.2.

**Verdict.** A sub-beat inside a commitment story, never a headline.

---

## 6. Six things that cut across the list

These are not ideas. They are facts that change more than one idea, and four of them were not in the
records before this pass.

**F1. The declared-price hole.** Every cap-shaped idea (1, 5, 6, and any variant) rests on a number the
seller writes. The standard has no consideration field (§3), so a hook enforces honesty on the honest. The
only three escapes are: put the ticket inside the program's custody (B), put the payment in the same
instruction (B, or a marketplace), or tax the token instead of the price (7, D). This should be on screen
in the demo, not in a footnote. It is also the answer to the question a knowledgeable judge will ask, and
answering it first is worth more than avoiding it.

**F2. The fee follows the token; the hook follows the mint; a marketplace follows the venue.** These are
three different scopes and the order of strength is fee > hook > venue. A `TransferFeeConfig` applies to
every transfer of that mint by anyone, including a program that has never heard of us. A hook applies to
every transfer of that mint too, but it can be given a false price. A marketplace applies only to people
who choose it. **So on this chain, today, the strongest economic rule available is a fee, and the
strongest price rule available is weaker than it looks.** That inversion is the most useful thing this
pass found, and it is why §4.7 and §5.4 rank above the cap they were built beside.

**F3. Confidential amounts and amount policies cannot coexist.** The `u64::MAX` sentinel (§5.7). Any pitch
that says "private resale, capped" is false on this extension set.

**F4. A hook's program id is changeable** by `TransferHookInstruction::Update` until its authority is
revoked, and revocation is a publish-path step a reader can check (§1). Two records now say this with
different mechanism names; this one is the code-level one.

**F5. A dollar cap needs a SOL/USD rate, and the cheapest one is not free.** The cap is in lamports; if a
face value is denominated in dollars, something has to convert. Pyth on Solana is pull-based and the
documentation states that posting and verifying an update "currently requires multiple transactions on
Solana", with a partial-verification path for single-transaction use (**DOCUMENTED**,
`docs.pyth.network`), and the fields live under `price_message` in `PriceUpdateV2`. So a same-transaction
"cap in dollars, enforced at transfer" is either a two-transaction flow or a partial verification, and
either way it is a dependency the demo can lose. If the cap stays in lamports against a lamport face
value, as it is today, none of this applies. **Keep it in lamports.**

**F6. Prior art, measured, and what it takes off the table.** The prior-art sweep that failed earlier in
this pass completed afterwards, and its result changes three claims. Read as a table because the detail is
the point.

| What | State | What it does on chain | Source |
|---|---|---|---|
| **OPEN Ticketing Ecosystem** (formerly GET Protocol) | live, claims millions of on-chain tickets since 2016 and that it "solved ticket scalping" | no resale-cap mechanism anywhere in its docs index. Its page titled "Interactions & Dynamic Pricing" is about the OPN token's fuel cost, not the ticket price | `onopen.xyz`, `docs.onopen.xyz` |
| **SeatlabNFT** | live, on **NEAR**, not Solana | markets "Capped resale value"; whether the cap is contract-enforced is not documented | vendor site |
| **Tixbase** | live, Avalanche | resale is a module; a regulated secondary market is described in a Circle case study | `tixbase.com` |
| **Ticketmaster Face Value Exchange** | live, US only, page updated 2026-11-07 | **the cap that actually scales is a database**: resale "for the price you paid" | vendor page |
| Yellowheart | **dead**: 301 to a host with no DNS record, last live snapshot 2021-05-17 | none | archive |
| NFT-TiX | **dead**: domain parking | none | vendor site |
| Aventus | live company, repositioned to a decentralised compute network | none in ticketing now | vendor site |
| a model forecast published before the outcome and scored after, on any chain | **none found**, and this is weak evidence: the Devpost search endpoint returns six fuzzy results per query | n/a | Devpost queries in this pass |

**Three consequences.** (i) **The cap is not novel; the enforcement is.** Ireland has banned resale above
the original price since the Sale of Tickets Act 2021 (No. 21 of 2021): s.15 bans selling or advertising
above the original sale price for designated venues and events, s.23(2) provides up to €100,000 and/or two
years on indictment, and s.19 voids contract terms that would block resale at or below face. The UK
government announced the same policy on 19 November 2025 (above face value defined as the original price
plus unavoidable fees, a legal duty on platforms to monitor and enforce, per-person resale limits, an
official estimate of £37 cheaper per ticket), and it is announced policy and not yet an Act, so it is not
enforceable. **(ii) That makes the best pitch sentence a regulatory one, and it is short:** a statutory cap
is in force in one jurisdiction with a five-figure penalty, and the state has no cheap way to know that a
resale happened. A rail where every resale is a recorded transfer with the cap on it *is* the enforcement
layer. (iii) **"Dynamic pricing on chain" is not a free phrase**, because OPEN uses it as a page title, so
§5.6 must be introduced as a committed price schedule rather than as the first on-chain dynamic pricing.
And the Devpost lane of "NFT ticket, no scalping" is the most crowded one there is, winners included,
which is one more reason the engine leads and the hook is the detail, as `23-…` already says.

**One thing this does not settle.** The claim that no live product enforces a resale cap on chain rests on
an absence of evidence across eight vendors and is not the same as evidence of absence. It is strong
enough to stop us saying "nobody does this" and not strong enough for us to be sure.

---

## 7. The ranked shortlist

Two orderings, because they are not the same and the difference is the whole decision.

Ranking A is **value per hour inside the window**: about thirteen hours to the freeze, maybe 8 usable, and the
submission surface itself is unscored but gating (`23-…` §5.0). Ranking B is **value as a product** after
the event, where the clock is not the constraint and finishability is not a virtue.

| # | What | Hours | Converts | Why it sits here | Main risk |
|---|---|---|---|---|---|
| **1** | Render the console against the real devnet artefact and put the refusal above the fold | 0.25 to 1 | (d) from partial to pass; Design +1 to +2 | The largest single move available and it is minutes. `23-…` §5.2 D1 reached the same place from a different measurement | none, it is an edit and a render |
| **2** | **Artist fee, §4.7** | 2 to 3 | **(c) from partial to pass** | The only cheap mechanism that puts a program we did not write into the money path, and it pays a third party. Best value in the document | the recipient-side deduction must be shown, not hidden |
| **3** | **Two-sided band, §5.3** | 1 to 2 | Design, Technology | A second refusal for the price of one comparison, and it matches the model's own output shape | a floor is a pricing policy he may not want |
| **4** | **Flip tax refunded on hold, §5.4** | 5 to 7 | Technology, Design | The one economic rule that survives the side payment, and the most novel thing here | nothing demos it in under two minutes unless the pair of numbers is on screen |
| **5** | **Blink checkout, §4.11** | 4 to 6 + hosting | Design, Completion | Highest Design-per-hour if hosting exists | a dead Blink at judging is worse than none |
| **6** | **Band as a public feed, §5.1** | 4 to 6 | Technology, Learning | The keystone, and the only thing that makes the engine infrastructure rather than a dashboard | worthless if nothing consumes it |
| **7** | Forecast log plus model hash, §4.2 and §4.3 | 3 to 4 | Learning, narrative | The strongest story per hour, the weakest still image | retrofitting, event cherry-picking |
| **8** | Refund pool, §5.5 | 3 to 4 | Design, Completion | Best non-pricing beat, clickable | proves a balance, not an adequacy |
| **9** | On-chain price schedule, §5.6 | 6 to 9 | Technology, Design | The strongest product idea here, and it needs new state | front-running the decay |
| **10** | Badge, claim window, reputation (§4.10, §4.8, §4.9) | 3 to 6 each | Design or Technology | Low marginal value now, and two of the three have the sybil hole | seen it; or the gate is a policy he has not made |
| **11** | Swarm (§4.4), rebate (§4.6), escrow custody (§5.2), confidential (§5.7), staked challenge (§5.8) | 8 to 20 | none | Post-event or do-not-build, for reasons in their entries | the clock, mostly |

**Not in the table, because they are not ideas:** the demo video, the registration check-in and the two
GenAI fields are gates, not options, and `23-…` §5.0 P1 to P3 already orders them above everything here. A
row for the video would sit at rank zero and would be the only row that is mandatory.

**What the two orderings say.** Ranks 1, 2, 4, 5 and 6 hold in both, so they are the ones that are not a
bet on the event. Ranks 3, 7 and 8 are worth more in the window than after it, because they are cheap
beats in a four-minute video. Ranks 9 and 10 invert: the schedule is the best product idea in this
document and the worst use of the next six hours. Nothing in the list requires a key, a credential or a
machine action beyond the faucet step the operator already owns.

**The one rank that is an argument, not a measurement.** Rank 2 sits above rank 4 because it is half the
hours and converts the same materials-test item. If the question were "what is the most interesting thing
this team could have on chain by Monday", rank 4 would be first. That is the difference between the two
orderings, and it is his to weigh.

---

## 8. Three combinations that tell one story each

A combination is worth more than the sum if the beats interlock: each one earns the next. All three reuse
work already in the tree. Hours are the marginal cost over the current state.

### 8.1 Combination I: "The refusal" (ideas 1 + 5 + 7 + 5.3), about 5 to 6 hours

**The five beats.** (1) A ticket is bought at face; the artist's 5% is withheld by the token program in
the same transfer, and the console reads the withheld balance back from the chain. (2) The buyer tries to
resell at 3× face; the transaction fails with 6010 and the explorer link is on screen. (3) The buyer tries
to resell at half face; it fails with the floor code too, so the band is shown to have two sides. (4) The
buyer resells inside the band; it lands, the fee is withheld again, the artist is paid twice. (5) The
console shows the record: face, cap, floor, the two refusals, the two settled transfers.

**The forty-second read.** "The ticket cannot be resold above or below the band, and the artist is paid on
every resale that does happen, by the token program." Two refusals, one payment, no prose.

**Materials.** 4 of 4 in the strict checklist (a, b, d clear; c via Token-2022's fee accounting), 3 of 4
if a judge insists that (c) means a program in the *decision* path.

**The honest weakness.** All of it binds inside the venue. The video says so in one line, and that line is
the difference between a credible artefact and an overclaim.

**Why it is the cheapest coherent story.** Every beat already exists or is two hours of work. Nothing new
needs a state machine. It is also the only combination that can be finished, filmed and submitted inside
the window with room for the submission surface.

### 8.2 Combination II: "The number with provenance" (5.1 + 1 + 4.3 + 4.2), about 10 to 13 hours

**The shape.** The engine writes a band to an account, with its sample size, its model hash and its as-of
slot. The hook enforces it. Six days later the same account is scored against what happened, and the score
is written next to the forecast, in public, with the old value still readable. The story is one sentence:
**the price was published before the outcome, it was enforced at transfer, and it was scored after, and
none of those three facts depends on trusting us.**

**The forty-second read.** "This is a price feed for tickets. Here is the number, here is when it was
written, here is the transfer it refused, here is what it got wrong." The last clause is the one a judge
does not expect and remembers.

**Materials.** 4 of 4, and (c) if the hook (ours) is joined by the token program (not ours) in the fee
path, which means §4.7 is inside this combination too and pushes it to 13 hours.

**The honest weakness.** The score is our arithmetic on our observation; there is no ticket-outcome oracle.
And a feed with one consumer is a feed with one consumer.

**Why it is the most on-thesis.** It answers the Top 3 sentence at the level of the mechanism
(composability, verifiability, on-chain ownership of a number) rather than at the level of the ticket, and
it survives the "chain bolted onto a web2 app" test because the number is the product.

### 8.3 Combination III: "The flip tax" (4.7 + 5.4 + 5.1), about 9 to 12 hours

**The shape.** The fee is high; the rebate returns it to whoever held. The band is the parameter that sets
both, published per event. The demo is one pair of numbers: the same ticket, resold after one hour and
after thirty days, and what each seller actually received. Then the band account, so the numbers are not
ours to tune.

**The forty-second read.** "Flipping costs 15%. Holding is free. The number that decides both is on chain
and was written before the sale."

**Materials.** 3 to 4 of 4, and it is the only combination whose central mechanism cannot be defeated by a
side payment.

**The honest weakness.** It taxes a behaviour rather than capping a price, so a judge who came for
"scalping is illegal" may not see the connection in forty seconds. It also needs the rebate arithmetic to
be right, and arithmetic with a time dimension is where bugs live.

**Why it is the most novel.** Nothing in the winner sample or in the live projects found (§9) does this.
Novelty is upside with a legibility cost, and the cost is paid in the first sentence.

### 8.4 What the three have in common, and the one thing to choose between

All three need the artefact to be rendered (rank 1) and all three are stronger with the artist fee (rank
2), so the first 3 hours are the same in every case. The choice is what the fourth hour buys: I buys two
refusals, II buys a feed, III buys a fee that is a function of time. **Cheapest is I. Most on-thesis is II.
Most novel is III.** That is analysis and not a decision; §11 lists what he would be deciding.

---

## 9. What not to do, with the reason attached

- **A soulbound ticket.** It deletes the engine's input (`26-…` §6.1). Any variant of "tickets cannot be
  transferred" is the same trade and the same loss.
- **A marketplace or an escrow**, this weekend. It is 12 to 18 hours, it is the product, and it is not the
  weekend (`25-…` §6.5, and the repo's own decision D6).
- **More program surface for its own sake.** `23-…` §5.1 T4 says it and this pass agrees: closing the two
  unimplemented preconditions is a day and gains nothing on any published criterion.
- **Confidential amounts with a cap.** Documented impossibility (§5.7).
- **A live external price feed in the buy path.** Two transactions or a partial verification, and a
  dependency that can be down at judging (§6 F5). Keep the cap in lamports.
- **A dead Blink.** If hosting is not already solved by hour 6, the Blink is a liability, not a feature.
- **A swarm.** §4.4.
- **"Fair launch" without a nullifier.** §4.8. The word is doing work the mechanism is not.

---

## 10. What is not established, so nobody invents it

1. **Whether every idea's third-party dependency is live on mainnet.** The `Pausable` extension is in the
   Token-2022 crate and documented, and **no source I read states that the deployed program carries it**;
   the extensions page only says "all clusters have the latest Token-2022 program deployed". No idea above
   depends on it, and none should start to.
2. **Whether a compressed NFT can carry a transfer hook.** No Bubblegum source mentions Token-2022 or
   hooks at all. The architectural inference is no, and it is an inference.
3. **Whether a Solana Attestation Service credential exists on devnet at the same program id** as the
   documented one (`22zoJMtdu4tQc2PzL74ZUT7FrwgB1Udec8DdW4yw4BdG`). The README names one id and never names
   a cluster. Relevant to §4.9 only.
4. **Whether the Action clients in circulation will render a devnet Action.** The spec is documented; the
   clients were not exercised. This is the risk in §4.11 and it is not resolvable on paper.
5. **Whether an existing live product already enforces a resale cap on chain.** §6 F6 is what the
   prior-art sweep found once it finished: the policy is not novel (Ireland has it in force, the UK has
   announced it), the enforcement is unproven anywhere on chain, and the cap that works at scale is
   Ticketmaster's database. What the sweep could not settle, it could not settle: SeatlabNFT's cap is
   undocumented as to enforcement, US state caps were not established, and Australia was not established
   (the FTC page 404'd and the state legislation site refused). Nothing in this file states a US or an
   Australian rule, and the "none found" for an on-chain scored forecast is weak evidence from a search
   endpoint that returns six fuzzy results per query.
6. **The judge-reaction predictions.** Class D throughout. The evidence they lean on is the four winner
   write-ups and the 38-project mechanism sample in `23-…` §4, which is a sample and not a census.
7. **The hours.** ESTIMATE. The one number that is not an estimate is the per-ticket deposit arithmetic,
   which is computed from measured rent.

---

## 11. Decisions this file does not make

1. **Which combination, if any.** I, II or III, or pieces across them, or none. The first three hours are
   shared, so the decision can wait until rank 1 and rank 2 are done.
2. **Whether the cap may be described as "enforced".** The honest sentence is "enforced inside this venue,
   and defeated by a side payment". The shorter sentence is better for a video and weaker for a record.
   This is a claim question, not a code question, and it is the one a knowledgeable judge will probe.
3. **Whether the floor (§5.3) is a policy he wants.** A floor is a decision to set a minimum price, and the
   model becomes the thing that sets it.
4. **Whether the artist is real.** A fee paid to a second wallet we control is a demo; a fee paid to a
   partner is a product. Both are honest if labelled, and only he knows which exists.
5. **Whether the window's remaining hours go to mechanism or to the submission surface.** `23-…` §5.5
   orders the submission work first and this pass has not re-costed it. The two orderings in §7 disagree
   about nothing except how many of ranks 4 to 6 he wants.
6. **Whether the devnet artefacts may be quoted as evidence in the submission** now that they exist and
   verify. They are public cluster identifiers and signatures, they are not credentials, and they are the
   entry's only on-chain proof. `23-…` §7 Q3 asked the funding question; this is the disclosure question
   that follows it.

---

## 12. Sources

Fetched by this pass on 2026-11-08 unless stated. Three documentation clusters were verified by dispatched
research at 00:47Z to 00:52Z, each returning exact quotes and URLs; the four items in §10 that remain
UNVERIFIED are the residue after those checks.

| # | URL | What it established |
|---|---|---|
| 1 | `https://solana-program.com/docs/token-2022/extensions` | the extension surface; transfer-fee withholding on the recipient; "any extra accounts that the program may require are automatically resolved on-chain"; confidential transfer live with the ZK ElGamal program |
| 2 | `https://docs.rs/spl-token-2022-interface/latest/spl_token_2022_interface/extension/enum.ExtensionType.html` | 29 `ExtensionType` variants, crate 4.0.0, dated 2026-10-28 |
| 3 | `https://github.com/solana-program/token-2022` (`interface/src/instruction.rs`, `program/src/processor.rs`) | `Transfer { amount }`, `TransferChecked { amount, decimals }`; `MAX_FEE_BASIS_POINTS = 10_000`; the `u64::MAX` hook sentinel on confidential transfers; `NonTransferable` refused before any authority check |
| 4 | `https://github.com/solana-program/transfer-hook` (`interface/src/instruction.rs`) | the `Execute` payload is 8 discriminator bytes plus `u64` and nothing else; account order; `TransferHookInstruction::Update` is what changes the program id |
| 5 | `https://solana-developers.github.io/solana-actions/` and `solana-developers/solana-actions` `packages/actions-spec/SPEC-v2.3.md` | the Action GET/POST shapes, `actions.json`, CORS minimums, `links.next`; `linkedActions` absent; no token-gating field |
| 6 | `solana-foundation/pay` `typescript/packages/solana-pay/docs/src/SPEC.md` | the `solana:` transfer request, `reference` semantics (not required to be unique or on-curve, must be a read-only non-signer on the transfer instruction) |
| 7 | `spl.solana.com/memo` and the memo program repo | the classic memo program id; that the repo's `main` now ships a rewrite with a different id |
| 8 | `https://github.com/solana-foundation/solana-attestation-service` | program id; Credential/Schema/Attestation model; nonce and expiry; "the decoder does not check the discriminator, so the caller must"; audit status UNVERIFIED |
| 9 | `phantom/sign-in-with-solana` README | SIWS proves key control and moves nothing |
| 10 | `https://docs.pyth.network` (Solana section) | pull model; the multi-transaction caveat for full verification; `PriceUpdateV2` fields nested under `price_message`; zero fee on Solana; staleness compared to the `Clock` |
| 11 | `switchboard-xyz/gitbook-on-demand` (the docs host does not resolve) | the three-instruction pull pattern; commit/reveal randomness; `get_value` refuses outside the reveal slot |
| 12 | `https://metaplex.com/docs/smart-contracts/core` | about 0.003 SOL per Core asset; Freeze Delegate prevents transfer and burn |
| 13 | Metaplex Bubblegum docs | tree cost tables (1,048,576 leaves at depth 20 / canopy 13 = 8.5012 SOL); canopy is immutable |
| 14 | `anza-xyz/solana-sdk` (`clock/src/lib.rs`) and `anza-xyz/agave` | the `Clock` fields and `Clock::get()`; `upgrade_authority: Option<Pubkey>` and `--final` making a program immutable, irreversibly |
| 15 | `https://www.irishstatutebook.ie` (Sale of Tickets Act 2021, No. 21 of 2021, ss. 15, 19, 23) | **MEASURED** by the prior-art sweep: the above-face-value prohibition, the €100,000 and/or two-year penalty on indictment, and the voiding of terms that block resale at or below face |
| 16 | `https://www.gov.uk` (announcement of 19 November 2025 on ticket resale) | **MEASURED**: above face value to become illegal, defined as original price plus unavoidable fees; platform duty to monitor and enforce; per-person resale limits; £37 per ticket and £112m a year estimated. Announced policy, no Act on the statute book |
| 17 | `onopen.xyz`, `docs.onopen.xyz`, `tixbase.com`, the vendor sites of SeatlabNFT, Ticketmaster's Face Value Exchange page, and archive snapshots for Yellowheart and NFT-TiX | **MEASURED** by the prior-art sweep for §6 F6: who is live, who is dead, which chain, and that the only cap in production at scale is a database |
| 18 | `https://api.devnet.solana.com` (RPC, 2026-11-08, 01:00Z to 01:20Z) | **MEASURED**: three `getSignatureStatuses` results, two finalized successes and one finalized `Custom: 6010` refusal, at slots 519845921, 519845933 and 519846008 |

Local evidence read or re-read by this pass: `records/devnet-artefacts.json` (contents quoted above),
`records/findings/23-…` (rubric, materials test, winner sample, refusal precedents), `24-…` (the
corrections), `25-…` (mechanism, rent and cost arithmetic, §6.6 hook authority), `26-…` (the
input-deletion trap, identity), `27-…` (the judge surface and the 36-entry field), `28-…` (the publish
path's retries and resume), `programs/cap_hook/src/lib.rs`, `ticketpath/core/markup.py`,
`docs/ON-CHAIN-DESIGN.md`.

---

*Nothing was built, no program was compiled, no cluster was written to, no key was touched, no service
was started, no file outside `records/findings/` was changed. One research dispatch (the prior-art sweep)
stalled, was reported as a failure while the rest of the file was written, and finished afterwards; its
result is §6 F6 and §10.5 was rewritten to match it rather than left as it stood. Nothing was committed
and nothing was pushed.*

# 43: the flip tax at checkout, as a second seller-paid lamport transfer

**Number.** 43, on the merged tree. When this was written the file was 39 and every number the
directory used ran to 38; `04`, `05` and `22` are the gaps in the sequence, and 39 had no file or
directory then.
**[Renumbered 2026-11-08T11:20Z by the release merge. The `release/prep` branch had already taken 38
for `records/findings/38-region-caps-local-validator.md` and 39 for
`records/findings/39-visitor-identity.md`, so the artist fee moved to 42 and this finding moved to 43.
The references to 38 below are references to the artist fee, now 42, and every one of them was
rewritten with it. No sentence, measurement or classification in this finding changed.]**

**Written.** 2026-11-08. Local measurement only. No devnet transaction, no faucet, no push, no
commit, no publish.

**What this is.** Feature 7's *charging* half, built as route 1 of
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md` §5.1 was for feature 5: a lamport leg
inside the sale transaction. `records/findings/42-artist-fee-at-checkout.md` built the artist fee
that way and stated its limit; this build adds the tax **on top of it**, priced off the hold clock
the hook itself writes, in the same atomic transaction, with the same limit and one new one of its
own. The operator's sentence is the schedule: 15% of the sale price while the hold is under an hour,
falling linearly to 0% at 30 days, per event, off by default.

## 0. The answer

> **BUILT.** `market_swarm/flip_tax.py` holds the schedule, the assessment, the 70-byte record
> decoder and the tax leg, and `sale_instructions` returns the whole sale as
> `(stage, artist_fee?, flip_tax?, move)` in that order, with either payment leg omitted when its
> amount is zero. The harness carries it as a per-event option that is off unless an event names
> `"enabled": true`; the ledger and the dataset carry what was charged and the hold it was charged
> on.
>
> **MEASURED.** On a throw-away `solana-test-validator` with the v2 `cap_hook` deployed, a sale at
> 1 000 000 000 lamports with a 500 bps artist fee and the full 1500 bps tax is **four
> instructions and two signers**, and the artist receives exactly 200 000 000 lamports (50 000 000
> fee plus 150 000 000 tax) in the transaction that moves the ticket, while the seller's balance
> falls by exactly that plus the 10 000-lamport transaction fee. The boundaries are priced at the
> schedule's numbers: 3 540 s and 3 600 s both pay 150 000 000, and exactly 2 592 000 s pays
> nothing and builds no tax leg at all. **Those three ages are supplied, not observed** — a local
> validator cannot make an hour pass (§4.1) — so what the chain measures is the leg and the money.
> A sale whose seller cannot cover fee plus tax fails whole.
> An over-cap sale is refused `6010` and both payments are rolled back. A record whose clock was
> never written is charged the full rate.
>
> **DERIVED, and it is finding 42's sentence plus one.** The tax binds only sales this app builds.
> The chain does not force it, and the free-ride leg that shows the mechanism (42 §4, leg 8) is
> unchanged by this build: a staging is consumed by whoever moves the ticket next, so a transfer
> that skips both payments is admitted. The one thing that is new is that **the age is the chain's
> and the price is the seller's**: the seller can stage a price low enough to round the tax to
> zero, but cannot claim a hold they did not have.

## 1. The transaction

```
[0] cap_hook  SetPendingPrice   accounts [issuer (signer), record (writable), mint]      data [2, price u64]
[1] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, fee u64]
[2] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, tax u64]
[3] Token-2022 TransferChecked  accounts [source, mint, destination, seller (signer),
                                          record, hook program, extra-account-metas]     data [12, 1, 0]
```

**DERIVED from the module and measured in §4.** Leg [1] exists only when the event names an artist
fee, leg [2] only when the tax is on and above zero, and the same sale is therefore two, three or
four instructions. One blockhash and one signature set make it atomic: a failure in any leg reverts
all of them. The tax sits last before the move, so both payments are inside the pair of
instructions they belong to.

Two separate transfers to the same wallet rather than one summed transfer, because the fee and the
tax are different rules with different rates, and one leg would make the dataset's `fee_lamports`
and `flip_tax_lamports` a split of a single number nobody could check against either rate.

## 2. Where the age comes from, and the three facts that decide the rate

`held_since_unix` is the eighth field of the v2 `TicketRecord`, at **byte 30** of the 70-byte
`["record", mint]` account, and the hook writes it in the step that consumes the staged price
(`programs/cap_hook/src/lib.rs`, step 7: `record.held_since_unix = Clock::get()?.unix_timestamp`).
The checkout reads the record before it builds the sale and decodes that field; the seller signs the
move, never the record write, so nothing in the transaction shape lets a seller claim an age.

`market_swarm/flip_tax.py` transcribes the offset and the record length rather than importing
`ticketpath`, and `market_swarm/tests/test_flip_tax.py` reads
`ticketpath/onchain/v2.py`'s `TICKET_RECORD_LAYOUT` and fails if either side moves. Measured in §4
leg 8: the field decoded by this module, by the proof tool's own reader and by
`ticketpath.onchain.v2.decode_ticket_record` is the same integer on the same account.

Three facts a screen or a README would otherwise get wrong:

1. **It is the mint's clock, not the holder's.** The value lives in the record, one per mint, and
   every admitted transfer of any seat of that event overwrites it, so one holder's sale resets
   every other holder's clock. It is a seller's own hold only where one wallet holds the mint at a
   time, which is the design's mint (`supply = 1`); the harness runs **one mint per event carrying
   the event's whole supply**, and measured leg 1 has one seller holding eight of that mint's seats
   while a buyer holds one, so a harness event's number is the event's clock and not the seller's.
   `AgentSpec.max_holdings` limits units per agent; it does not give each holder a record, and this
   build does not claim it does. A per-holder clock is a different account layout and is not built.
2. **`0` means unknown, not "held forever".** `InitializeRecord` writes 0, and a v1 metas list
   (record read-only) leaves it at 0 permanently, because the hook only writes when the record
   arrives writable. An unknown hold is charged the **full** rate. Reading 0 as a time would make
   the tax `now - 0`, about 58 years, which prices every unknown at 0% and makes an unset field the
   cheapest evasion in the system. This is the mirror image of `ClaimRebate`, which refuses to
   *pay* a rebate on an unknown hold (`6027`) rather than guessing.
3. **A clock that went backwards clamps to zero seconds**, and zero seconds is the full rate, so a
   disagreement about the time cannot buy a discount. The Rust clamps identically in
   `state.rs::held_seconds`; this is the same rule, one layer up.

## 3. The schedule and the arithmetic

```
held <= t1            rate = full
t1 < held < t0        rate = full * (t0 - held) // (t0 - t1)
held >= t0            rate = 0
tax  = price * rate // 10 000
```

Defaults `full = 1500 bps`, `t1 = 3 600 s`, `t0 = 2 592 000 s`, each configurable per event under
`flip_tax.schedule`.

**DERIVED, and the boundary is not a choice.** At exactly `t1` the flat branch and the linear branch
return the same number, because the line starts at `(t1, full)`. "15% if held under an hour" and
"falling linearly to 0 at 30 days" therefore agree at 3 600 s; they can only be made to disagree by
changing where the curve starts. The tests pin 3 540 s, 3 600 s and 3 601 s, and one mutation in the
table exists only because a value assertion **cannot** tell the two branches apart at 3 600: the mutation suite replaces the held value with an `int` subclass whose `__rsub__` raises, so
"which branch ran" becomes behaviour rather than a reading of the source.

**Floor, and the cost of flooring is stated rather than hidden.** `//` and never `/`: a float puts a
rounding error into a money value, and a ceiling charges above the stated rate (finding 42 §3). The
cost is that the rate reaches 0 shortly before the stated 30 days —
`1500 * (2 592 000 - held) < 2 588 400` floors to 0 at `held >= 2 590 275`, which is 1 725 seconds
(28 minutes 45 seconds) short of 30 days — and that a small enough tax rounds to zero and builds no
leg, which §4 leg 5a measures at price 6 and leg 5b at price 7.

## 4. What was measured, and on what

`tools/flip_tax_proof.py` boots its own `solana-test-validator` on loopback, deploys the existing
`programs/cap_hook/target/deploy/cap_hook.so` (asserted by sha256 and never rebuilt), initialises a
v2 record per mint, and drives real transactions built by the product's own
`flip_tax.sale_instructions`. It reads balances with `getBalance` at confirmed commitment and each
transaction's own `meta.fee`, so every delta asserted is exact. Run three times: by the subagent that
wrote the tool, twice by the orchestrator of this change (once before the review fixes, once after),
PASS 11/11 each time, the last in 31 s. The tool wipes `tmp/flip-tax/` at boot, so only the latest
run's `REPORT.md` and `measurements.json` survive, and the earlier ones are gone by design rather than
by accident.

| leg | what was sent | what the cluster did |
|---|---|---|
| 1 | price 1e9, fee 500 bps, tax at the full rate (3 540 s supplied), four instructions, signers seller + issuer | ok. Artist **+200 000 000** (50 000 000 fee + 150 000 000 tax), seller −200 010 000 (`meta.fee` 10 000), seller 8→7, buyer +1, record pending 0 |
| 2a | the boundary at **59 min** (3 540 s supplied) | ok. rate 1 500 bps, tax **150 000 000**, four instructions, artist +200 000 000, seller 7→6 |
| 2b | the boundary at **1 h** (3 600 s supplied) | ok. rate 1 500 bps, tax **150 000 000**, four instructions, artist +200 000 000, seller 6→5 |
| 3 | the boundary at **30 d** (2 592 000 s supplied) | ok. rate 0, **no tax leg** (three instructions), artist +50 000 000 only, seller −50 010 000, seller 5→4 |
| 4 | the toggle off: the builder is asked to charge a disabled policy | refused before any transaction exists. The control sale (the fee only, the shape an event with no tax builds) lands: three instructions, artist +50 000 000, seller 4→3 |
| 5a | price 6 at the full rate | tax rounds to **0**, so two instructions and no payment leg; artist delta 0, seller −10 000, seller 3→2 |
| 5b | price 7 at the full rate | tax = **1 lamport**, three instructions, artist delta **exactly 1**, seller −10 001, seller 2→1 |
| 5c | price 19 at the full rate, computed and not sent | tax = **2**, and the pair that straddles the floor is 6 and 7, not 19 and 20 (19 pays 2 at 1500 bps; it pays 0 at the 500 bps the artist-fee finding used) |
| 6 | a seller holding 100 000 000 against a fee plus tax of 200 000 000 | failed at instruction index 2, `Custom: 1` (System `InsufficientFunds`). Seller −10 000 (the transaction fee only), artist **0**, ticket still 1 in the seller's account, record pending **0** |
| 7 | price 1 250 000 001, one lamport over the ceiling | failed at index 3, `Custom: 6010`. Artist **0**, ticket unmoved, and the 62 500 000 fee at index 1 and the 187 500 000 tax at index 2 were both rolled back: the seller is short only the 10 000 transaction fee |
| 8 | read the record after an admitted transfer; then a sale of a record never moved | 70 bytes, `held_since_unix` = 1 794 134 761 from all three decoders, and it advances to 1 794 134 764 across the sale (the exact seconds differ every run, because they are the wall clock; the fact does not). The fresh record reads 0, `hold_seconds` returns `None`, the rate is the full 1 500 bps and the sale of it pays 200 000 000 (fee 50 000 000 + tax 150 000 000) in four instructions |

Assertions that did not hold: none. Validator stopped, ledger removed, its RPC port checked closed.
The program id in this run (`CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`) is a fresh deploy of the
`.so` whose sha256 is `de89af3c…6e949cac`, not a published program.

**The one number in the brief that was wrong, and it was mine.** The build brief stated leg 1's
seller delta as `-200 000 010 000`. The seller is funded with 3 000 000 000, and the sale moves
50 000 000 + 150 000 000 + 10 000; the chain measured **−200 010 000**, which decomposes exactly. The
tool now asserts the measured number and the decomposition, and a test pins it so nobody restores an
impossible literal.

### 4.1 What the validator cannot do, and therefore what is supplied rather than measured

**The age is an input.** The hook writes the validator's wall clock, and a bounded local run cannot
make an hour pass. The obvious trick does not work and was measured rather than assumed:
`solana-test-validator --warp-slot 6480000` moves the slot to 6 480 000 and leaves
`Clock::unix_timestamp` at wall clock on agave 4.3.2 (read from the clock sysvar before and after).
So legs 2a, 2b and 3 hand `sale_instructions` the `held_since_unix` a record would carry for that
hold, and what the chain measures is the leg and the money: the instruction count, which legs pay the
artist, the exact lamport delta, or no tax leg at all. **What is measured nowhere in this repository
is an hour passing on a real chain.** The rate-for-age curve is measured as the pure function, in
`market_swarm/tests/test_flip_tax.py`, and the two halves are joined at exactly one point: leg 8,
where the real clock is read from a real record and the sale built from it.

## 5. What the tax does not do

1. **The hook never looks at the tax.** `programs/cap_hook` has no instruction and no check that
   mentions lamports between wallets, and this build did not add one. A transaction can stage a
   price, move the ticket and pay nothing, and the hook admits it: finding 42 §4 leg 8 is the
   measurement, and it is unchanged.
2. **A staging is not tied to the transaction that consumes it**, so the ride of 42 §5(2) applies to
   both payments at once. The checkout's monopoly on staging is the only thing collecting either.
   This is the deployed v2 program's behaviour, measured (42 §4 leg 8: stage in one transaction,
   move in another, both admitted), and it does not match `docs/ON-CHAIN-DESIGN.md` §2.3, which says
   of the *designed* checkout's `pending_*` fields that "the stage cannot outlive the transaction
   that created it". Both statements are true of their own subject and the record has not reconciled
   them; a reader who needs one answer for the deployed program should take the measured one.
3. **The tax is a fraction of the staged price, not of lamports that moved**, so the cheapest
   evasion is a price staged low enough to round the tax to zero (leg 5a). There is no floor in this
   build; whether the checkout should refuse a sale below some fraction of face is a product
   decision this build names and does not make, exactly as it did for the fee.
4. **The rate is not in the dataset's header**, so a row whose tax agrees with its own rate verifies
   even if that rate is not the event's, and a row from a taxed event whose tax columns are both
   deleted is indistinguishable from one from an untaxed event. The gap is wider than "the event's
   rate": **no pair of `held_seconds` and `flip_tax_bps` is checked against any curve**, so a row
   saying a seat held ten seconds paid 0 bps, or one held a hundred days paid 1500 bps, or `null`
   at 0 bps, all verify (measured in review). Same gap as the fee's, same fix (the policy in the
   header), and it is written down rather than half-done.
5. **The record is not a history, so the age must be read before the sale.** The sale that pays the
   tax is an admitted transfer, so the hook overwrites the record's clock with its own instant while it
   consumes the staging (measured, §4 leg 8: `held_since_unix` moves forward to the sale's own instant
   across the sale). An auditor who reads the record afterwards sees the sale's instant and not the
   age it was priced from. The age is still checkable, and not from the record: the instant is the
   block time of the mint's previous admitted transfer, which is public, so the hold can be
   reconstructed from transaction history to the second and compared with the row's `held_seconds`.
   Anyone auditing this tax should do that rather than trust the record.
6. **The clock is the mint's** (§2.1): it is the age of the last transfer of any seat, so it is
   the seller's own hold only when one wallet holds the mint. In the harness it is the event's
   clock, and a live platform with many holders on one mint would need one record per holder, which
   is a program change.
7. **A refund-to-holders pool is not built.** It is documented in `docs/ON-CHAIN-DESIGN.md` §16.6
   with what it needs: `ClaimRebate` (tag 7) in `lib.rs`, a pool account per mint and a claim rule.
   The claim arithmetic already exists as pure functions in `state.rs`, and its
   `HOLD_FULL_SECONDS = 60` is that unbuilt curve's demo number, **not** this schedule's 3 600
   seconds. Anyone reading the two as one number has read it wrong, which is why both places say so.

### 5.1 The refusals and the dataset rules, in one place

Every rule below is enforced in code and tested; this is the list a reader would otherwise have to
recover from source.

`market_swarm/flip_tax.py` refuses to build a sale, each refusal naming its rule and no transaction
signature existing when it fires:

| refused | why |
|---|---|
| a disabled policy | the toggle is the event maker's and the default is off, so a disabled policy reaching a builder is a caller that skipped the toggle |
| the artist wallet equal to the seller | the seller would pay themselves, and the sale would record a tax that moved nothing |
| a price of 0 or less | the chain reads a staged 0 as "nothing staged" and refuses the move `6009`, so that sale can only fail |
| a tax that does not fit the `u64` a System transfer carries | reachable only from a price above `2**64 - 1`, and named here rather than left to the encoder |
| `zero_hold_seconds` not greater than `full_hold_seconds` | a curve that ends before it starts has no falling segment, and the division would be by zero or a negative span |
| `"artist_wallet": null` | a field somebody wrote is not a field they left out; omission inherits, null is refused |
| a wallet that is not 32 bytes of base58, or differs from the event's artist fee wallet | a typo must fail as a named field rather than on the wire, and one event has one recipient |
| a record shorter than 70 bytes, at checkout | the hook's clock is at byte 30 of a 70-byte account and cannot be read from a shorter one; the sale is refused `ChainUnavailable` **before** any signature exists, rather than priced on a guess |

`market_swarm/datasets.py` checks ten things per row, and a row that fails any is a violation:

| checked | why |
|---|---|
| a tax amount with no `flip_tax_bps` (unless 0 or null) | an amount with no rate names a payment whose rule was never recorded |
| `flip_tax_bps` an integer in 0..10 000 | a rate outside the denominator's range is not a rate |
| `flip_tax_lamports` an integer or null | money is an integer count of lamports |
| a negative tax | money out of the artist's pocket |
| a tax above the price | a tax outside 0..price is not a tax |
| an executed trade with a rate and no price | the price was removed and the tax cannot be checked against anything |
| an executed `buy` carrying a nonzero tax | the tax is on resales; a primary sale is the artist's own stock at face |
| an executed `resell` whose tax is not `price * bps // 10 000` | the rate is on the row, so the amount is recomputed and not trusted |
| a tax on a row that is not an executed trade | a sale that did not run charged no tax |
| `held_seconds` not an integer of at least zero or null | it is the hold the rate came from; null is the unknown clock, which is not zero seconds |

## 6. What this change touched, and what it deliberately did not

**New files.** `market_swarm/flip_tax.py`, `market_swarm/tests/test_flip_tax.py`,
`market_swarm/tests/test_flip_tax_mutation.py`, `market_swarm/tests/test_flip_tax_wiring.py`,
`tools/flip_tax_proof.py`, `tests/test_flip_tax_proof.py`, this finding.

**Appended.** `docs/ON-CHAIN-DESIGN.md` §16, `records/F-decision-log.md` (`D27`),
`records/A-research-ledger.md`, `README.md`'s features 5 and 7 section,
`records/STATE-OF-PROJECT.md`'s feature row and two stale bullets.

**Edited, additively, in the harness.** `market_swarm/config.py` (the optional `flip_tax` block and
the combined-take refusal), `market_swarm/gateway.py` (the record read, the clock seam, the leg, a v2
stage and writable move on any taxed event, and the combined-take refusal at `_check_spec` so a
hand-built spec cannot build it), `market_swarm/runner.py` (the flag at both sale call sites and the
three columns), `market_swarm/ledger.py` and `market_swarm/datasets.py` (the columns and the checks),
`market_swarm/cli.py` (`plan` prints the state), and `market_swarm/CONTRACT.md` (the section on the
interfaces above, which review found missing).

**Existing tests that had to change, and only in the way the new fields force.**
`market_swarm/tests/test_gateway.py` pinned `TransferResult`'s field set; `test_artist_fee_wiring.py`
pinned `EventSpec`'s last field, `TransferResult`'s last field and `TradeRow`'s tail; `test_cli.py` and
`test_runner.py` carry fake chains that implement `transfer`, so they gained the new keyword the call
sites must pass; `test_artist_fee_call_sites.py` was extended to the second flag, which is what stops
a third call site inheriting a default. Each assertion kept its claim: the payment fields trail the
required ones and default, and `synthetic` is still the last column.

**Not touched, and why.** `programs/cap_hook/**` (the operator's instruction: the hook is an input
here, and the pool half would be a program change), `tools/publish_v2*.py` and
`tools/devnet_publish.py` (two other runs' files). No devnet, no faucet, no publish, no commit.

## 7. Reproduction

```
export PATH="$HOME/.local/share/solana/install/active_release/bin:$HOME/.cargo/bin:$PATH"
python3 tools/flip_tax_proof.py
python3 -m unittest tests.test_flip_tax_proof -v
python3 -m unittest market_swarm.tests.test_flip_tax market_swarm.tests.test_flip_tax_mutation \
    market_swarm.tests.test_flip_tax_wiring -v
```

Every run generates fresh keys under `tmp/flip-tax/keys/`, so addresses and signatures differ between
runs and cannot be looked up by a reader; the properties do not. The suite counts and the tails of
each run are in §9.

## 8. What remains unverified

- **Nothing was run on devnet or mainnet.** No tax has been charged anywhere public, and no statement
  here is about a real artist's revenue or any real platform's fee policy.
- **The two-signer taxed sale has not been exercised through the product's own checkout on a
  cluster.** As in finding 42 §8, "the app" that builds this transaction today is the harness's
  gateway, and the validator measured the same instruction set built by `tools/flip_tax_proof.py`
  with the same encoders and the same module function. The gateway's taxed path is unit-tested
  against a fake cluster, not measured on one.
- **An hour passing on a real chain is unmeasured** (§4.1). This is the one gap the local validator
  cannot close, and the honesty paragraph in the tool's own `REPORT.md` says the same thing.
- **No bypass leg is measured for the tax.** The tax rides in the same transaction as the fee, so it
  inherits finding 42's free-ride result rather than reproducing it. A tax-specific free ride (stage
  in one transaction, move in another, pay neither) is the same leg with a second payment leg it
  simply does not include.
- **A crowd holding the same mint has one clock** (§5.6), so a measured hold in a many-holder event
  would not be the holder's own, and **the record is not a history** (§5.5): the sale overwrites the
  clock it was priced from, so the age is reconstructed from transfer history and not from the record.

## 9. Test surfaces

- `market_swarm/tests/test_flip_tax.py` — the schedule, the boundaries, the assessment, the record
  decoder, the layout transcription pinned against `ticketpath/onchain/v2.py`, the refusals, the
  instruction order, and a source scan for floats.
- `market_swarm/tests/test_flip_tax_mutation.py` — a property table and a mutation table: every one
  of the 25 mutations must be caught by a property, and one that is not is a failure rather than a
  skip. Two of them cannot be seen by a value assertion: the boundary one is caught by behaviour
  instead (the trapping hold, §3) and the zero-point one by making the branch exclusive-only, so
  which branch ran becomes observable; the zero-point one is caught by value instead, because a hold
  one second past the point floors to a negative rate.
- `market_swarm/tests/test_flip_tax_wiring.py` — the config block, the gateway's legs and record
  read through a fake cluster, the toggle off, the fail-closed record read, the dry run, the ledger
  columns and every dataset rule.
- `tests/test_flip_tax_proof.py` — the tool itself, without a validator: the leg table's numbers, the
  instruction counts, the `.so` hash refusal, the work directory and lock, and source scans for no
  build, no devnet and no clone.

## 10. Independent review

Three reviewers who built none of this, read-only on the tree, each writing to `tmp/review/`.

**`tmp/review/flip-tax-attack.md`** — the code, adversarially, with its own property sweeps (every
hold from 0 to 3 700 and 2 590 000 to 2 594 000, then 200 000 random prices up to `2**64` against a
floored rational, zero failures), 14 crafted dataset rows, its own mutants applied to a copy of the
tree, and two gateway mutants. Verdict: **nothing blocks built and tested**; two MAJOR and eight MINOR.
The MAJORs were real:

1. **A hand-built `EventSpec` could build a 115% take.** The combined-take rule lived only in the
   config loader, so a spec built in code with a 10 000 bps fee and a 1 500 bps tax produced a
   four-instruction sale in which the seller paid more than the price, and the chain accepted it.
   Closed by one function (`flip_tax.combined_take_bps`) with three callers: the loader,
   `gateway._check_spec` and `EventChain.__init__`, the last because the class is public and was the
   door the review used. Pinned by two wiring tests.
2. **`market_swarm/CONTRACT.md` had no flip-tax section**, while the sibling feature documented every
   interface it touched. Added, and named in §6.

Its second finding that survived to a fix: a mutation that widens the omission rule from `== 0` to
`<= 1` survived the whole `market_swarm` suite, because no test prices a sale whose tax is exactly one
lamport. There is now a 25th mutation and a 22nd property for it, and the two properties pin the floor
from both sides (6 lamports builds no leg, 7 builds a leg of exactly one).

**`tmp/review/flip-tax-docs.md`** — every sentence this change added, against the tree and against the
run's own output. Verdict: **the docs did not match the code**; four MAJOR and seventeen MINOR, none a
BLOCKER. It found a free-ride measurement cited to this finding, which says in terms that it does not
have one (it is finding 42's); the "one seat per participant" claim in five documents, which the
record's layout does not support and the measured run contradicts (one seller holding eight seats of
the measured mint); a false statement about the record's fields in the module docstring; and five
builder refusals and six dataset rules stated nowhere a reader would look. All four are fixed, and the
refusals and rules are now §5.1.

**`tmp/review/flip-tax-round2.md`** — the fixes, against the tree, with its own drift experiment.
Verdict: **nothing left blocks built and tested**; three MAJOR about consistency, all fixed: one of the
five clock paragraphs had kept the old mechanism, the "one definition of the bound" claim was false of
the loader (it did its own addition, and the reviewer made the two disagree in one edit by moving
`MAX_BPS`), and the new sentence "the age cannot be re-derived from chain state" was false — the sale
overwrites the record's clock, but the same instant is the block time of the mint's previous admitted
transfer, which is public, so the age is reconstructed from transfer history. What the record cannot do
is act as a history, and that is what the finding now says.

Two claims of this finding were wrong before review and are corrected rather than quietly dropped: the
2 590 273-second floor (the correct value is 2 590 275) and the "one seat per participant" mechanism.
The 19-lamport rounding example from the artist fee's finding does not carry over either: at 1 500 bps,
19 lamports pays 2, and the pair that straddles the floor is 6 and 7. All three had a self-reviewer's
confidence and none survived an independent read, which is the argument for the independent read.

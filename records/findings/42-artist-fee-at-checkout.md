# 42: the artist fee at checkout, as a seller-paid lamport transfer

**Number.** 42, on the merged tree. When this was written the file was 38: numbers 00 to 37 were
claimed in `records/findings/` and 38 had no file or directory then.
**[Renumbered 2026-11-08T11:20Z by the release merge. The `release/prep` branch had already taken 38
for `records/findings/38-region-caps-local-validator.md` and 39 for
`records/findings/39-visitor-identity.md` before this finding was written on the other checkout, so
this one moved to 42 and the flip tax to 43. The branch landed first and the newcomers move, which
is the rule the branch's own renumber pass used. No sentence, measurement or classification in this
finding changed.]**

**Written.** 2026-11-08. Local measurement only. No devnet transaction, no faucet, no push, no
commit, no publish.

**What this is.** The build of route 1 in `records/findings/36-transfer-fee-on-a-one-unit-ticket.md`
§5.1, as corrected by its non-builder review (`tmp/review/fee-mechanism.md`, MAJOR #1: the fee
cannot come from the buyer, who never signs; it has to come from the seller). The operator chose it
and specified the shape: one atomic transaction containing the stage, the seller's fee payment in
lamports to the artist wallet, and the token transfer; `fee_bps` per event; a Token-2022 transfer fee
is not used.

## 0. The answer

> **BUILT.** `market_swarm/artist_fee.py` holds the policy, the arithmetic and the fee leg, and
> `sale_instructions` returns the sale as `(stage, fee_transfer, move)` in that order, with the fee
> leg omitted when the fee is zero.
>
> **MEASURED.** On a throw-away `solana-test-validator` with the v2 `cap_hook` deployed, a sale at
> 1 000 000 000 lamports and 500 bps pays the artist exactly 50 000 000 lamports in the same
> transaction that moves the ticket, and the seller's balance falls by exactly that plus the
> transaction fee. A sale whose fee the seller cannot cover fails whole: no ticket moves, the artist
> is paid nothing, and the staged price is rolled back. A sale over the cap is refused `6010` and
> pays no fee.
>
> **DERIVED, and the sentence that must not be dropped.** The fee binds only sales this app builds.
> The chain does not force it, and §5 below shows the two ways round it: a transfer that rides a
> staging someone else paid for, and a private price below the one staged.

## 1. Why the fee is in lamports

**MEASURED (finding 36 §2).** A Token-2022 `TransferFeeConfig` cannot take a fraction of a
one-base-unit ticket: the program ceils the fee, so at `decimals = 0`, `amount = 1` every rate from 1
to 9999 bps withholds `withheldAmount = 1` and credits the buyer 0. The only fees that mint can
express are 0 and the whole ticket.

**DERIVED.** A token fee is a fraction of a token amount; a share of a resale is a fraction of a
price. On an indivisible ticket the two are not the same question, and the ticket's indivisibility is
the product (one seat), not a setting.

## 2. The transaction

```
[0] cap_hook  SetPendingPrice   accounts [issuer (signer), record (writable), mint]      data [2, price u64]
[1] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, fee u64]
[2] Token-2022 TransferChecked  accounts [source, mint, destination, seller (signer),
                                          record, hook program, extra-account-metas]     data [12, 1, 0]
```

**DERIVED from the deployed program's source, not assumed.** The stage is authorised by
`record.authority` (`programs/cap_hook/src/lib.rs`, `checked_record_for_write` →
`record.authorises`, which is strict equality with the field), and on a record created by
`initialize_record` that key is the mint authority. The seller signs the System transfer (the source
of the lamports) and the token transfer (the source account's owner). The transaction therefore has
**two signers, the issuer and the seller**, and the instruction order is stage, fee, move. One
blockhash and one signature set make it atomic: a failure in any leg reverts all three.

Two consequences that are product decisions, not implementation details:

- **The seller must hold lamports.** A seller with a ticket and no SOL cannot resell, because the
  fee leaves their balance in the same transaction. Measured in leg 2 (§4).
- **A zero-fee sale is two instructions, not three.** A 0-lamport `System` transfer would be an
  instruction no reader could tell from a fee that was meant and failed to move, so the module
  declines to build one. Whether the runtime would accept one was not measured here.

## 3. The arithmetic

```
fee = price_lamports * fee_bps // 10_000        floor, integers only, no float
```

**DERIVED.** Floor, and the reason is the finding-36 defect one level down: a ceiling takes a whole
lamport on a 1-lamport sale, which is 100% of it. Floor never charges more than the stated rate; its
cost is rounding to zero (19 lamports at 500 bps pays 0).

**TESTED, not merely asserted** (`market_swarm/tests/test_artist_fee.py`, 36 tests): the full
`fee <= price` bound for every rate the policy accepts, equality exactly at 10 000 bps, fee 0 at
`bps = 0` and at `price = 0`, the integer boundary (19 → 0, 20 → 1 at 500 bps), monotonicity in price
and in rate, and that the module contains no float literal and no true division.

**MEASURED, on the validator** (§4): the seller's and artist's balances move by exactly the number
the arithmetic predicts, at 500 bps and at 10 000 bps, including the rounding boundary.

## 4. What was measured, and on what

`tools/artist_fee_proof.py` boots its own `solana-test-validator` on loopback, deploys the existing
`programs/cap_hook/target/deploy/cap_hook.so` (never rebuilt: the build peaks near 4.6 GB on a box
with under 2 GB free), initialises a v2 record per mint, and drives real transactions. It reads
balances with `getBalance` at confirmed commitment and the transaction's own `meta.fee`, so every
delta asserted is exact and none is inferred.

**The measurement.** The run below was made by the orchestrator of this change and independently
reproduced by the non-builder review (`tmp/review/artist-fee-review.md`, its own validator, its own
keys, the same nine legs and the same numbers):

| leg | what was sent | what the cluster did |
|---|---|---|
| 1 | price 1 000 000 000, 500 bps, three instructions, signers seller + issuer | ok. Seller −50 010 000 (fee 50 000 000 + `meta.fee` 10 000), artist +50 000 000, buyer tokens +1, seller 8→7, record pending 0, `held_since_unix` written, hook log `cap admitted price=1000000000` |
| 2 | the same sale from a seller holding 1 000 000 lamports | failed at instruction index 1, `Custom: 1` (System `InsufficientFunds`). Seller −10 000 (the transaction fee only), artist **0**, ticket still 1 in the seller's account, record pending **0** |
| 3 | price 1 250 000 001 (one lamport over the ceiling) | failed at index 2, `Custom: 6010`. Artist **0**, ticket unmoved, record pending 0, and the 62 500 000-lamport fee instruction that ran at index 1 was rolled back: the seller is short only the 10 000 transaction fee |
| 4a | price 19 at 500 bps | **two** instructions (no fee leg), sale lands, artist delta **exactly 0**, seller 7→6 |
| 4b | price 20 at 500 bps | three instructions, fee 1, sale lands, artist delta **exactly 1**, seller 6→5 |
| 5 | 10 000 bps, price 1 000 000 000 | fee = price = 1 000 000 000. Seller −1 000 010 000, artist +1 000 000 000, seller 5→4 |
| 6 | staged 0, the move with no fee leg | failed at index 1, `Custom: 6009`. Nothing moved, artist 0, record pending 0 |
| 7 | read the record after leg 1 | 70 bytes, 9 fields, pending 0, `held_since_unix` = 1 794 128 981, authority = issuer, and **no field equals 50 000 000**: the chain stored the staged price, not the fee |
| 8 | stage alone (issuer signs, one instruction), then the move alone (seller signs, one instruction, no fee leg) | **both admitted.** Artist delta **0** against the 50 000 000 a checkout sale at that price would have paid, seller 4→3, staging consumed by the move |

Leg 8 is the one that must be quoted. It is the measured form of §5(2): a staging is a value in the
record, the next admitted transfer consumes it, and whoever builds that transfer pays no fee. The
checkout's monopoly on staging is the only thing collecting the fee.

Assertions that did not hold: none. Validator stopped, ledger removed, its RPC port checked closed.
The program id in this run (`CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`) is a fresh deploy of the
`.so` whose sha256 is `de89af3c…6e949cac`, not a published program.

**One correction the review got out of this build, and it is about the deployed program, so it
matters more than the rest of this section.**
`tools/devnet_publish.py`'s `instruction_transfer_checked` declares the record account **read-only**.
The first draft of this finding said that produces a transfer that lands and leaves the staging
unconsumed. That is wrong. The rule the runtime enforces is that an account is writable for a
transaction if **any** instruction in it says so, and that an inner CPI may not ask for more than the
outer instruction granted; v2's extra-account-metas list declares the record writable
(`RECORD_META_WRITABLE = true`, `programs/cap_hook/src/lib.rs`), so Token-2022's CPI to the hook asks
for a writable record. A message whose only mention of the record is read-only is therefore refused
**`PrivilegeEscalation`** at the Token-2022 instruction and the hook never runs. Measured by the
reviewer: the same move alone, read-only, `ok=False`, `{"InstructionError": [0,
"PrivilegeEscalation"]}`. So that builder cannot move a v2 ticket at all, and the `is_writable`
fallback inside `execute` is a v1-metas path a v2 mint cannot reach.

The converse claim in the first draft is also wrong: on the fee path the stage already marks the
record writable for the whole message, so the move's own flag changes nothing there. Measured:
`[stage, move read-only]` and `[stage, move writable]` both clear the staging. The writable builder
in the harness's fee path is therefore belt-and-braces today and the thing that makes a move-only
transaction possible tomorrow; the reason is stated in its docstring and no longer claims to be the
reason leg 1 passed. The `devnet_publish` copy is not edited here, because that file belongs to
another run; this paragraph is the handover to whoever owns it.

## 5. What the fee does not do

This section is the point of the finding. Three sentences, each of which a screen or a README would
otherwise get wrong:

1. **The hook never looks at the fee.** `programs/cap_hook` has no instruction and no check that
   mentions lamports moving between wallets. A transaction can stage a price, move the ticket and pay
   the artist nothing, and the hook admits it.
2. **A staging is not tied to the transaction that consumes it.** `pending_price_lamports` is a value
   in the record and the next admitted transfer consumes it, whoever builds that transfer. So the
   issuer stages once and any holder can move the ticket fee-free; the ride costs one staging, and it
   is consumed, but it is a door.
3. **The fee is charged on the staged number, not on lamports that moved.** The chain enforces the
   cap against `pending_price_lamports`; it has no view of what the buyer actually paid the seller.
   A private price below the staged one moves the fee down with it. **And the amount is the
   seller's choice because the staged price is:** there is no floor in this build (`band_low` is 0
   in the proof and is never set by the harness), so at 500 bps any price under 20 lamports pays the
   artist nothing, the fee leg is omitted, and a dataset row reading `fee_lamports: 0, artist_fee_bps:
   500` verifies. That is the same arithmetic as leg 4a's rounding credit, and it is the cheapest
   evasion in the system because it never leaves the app. Whether the checkout should refuse a sale
   below some fraction of face — or set the record's `band_low` — is a product decision this build
   does not make, and it is named here rather than left for a reader to find.

What the chain *does* force, on a v2 record whose authority is the issuer, is that no ticket moves at
all without the issuer's signature on a stage. That is the cap behaviour finding 36 §5.1 described,
and it is what makes "charged by the checkout" a real claim. It is not the claim "charged by the
chain".

### 5.1 The stronger variant, documented and not built

A hook that reads the instructions sysvar and requires a matching `System` transfer to the artist in
the same transaction would make the fee a condition of the move. It is not built, for four reasons
that `docs/ON-CHAIN-DESIGN.md` §15.4 states in full: the hook would need the artist wallet and the
rate at hook time (neither is in the v2 record, so a per-mint fee account and its writer would be
needed); every sale's transaction shape would become part of the program's interface; the sysvar
account's index has to be verified or the check attests to nothing; and it still cannot prove the
buyer paid the staged price. Written down because the alternative is a reader concluding the chain
enforces a fee it does not.

## 6. What this change touched, and what it deliberately did not

**New files.** `market_swarm/artist_fee.py`, `market_swarm/tests/test_artist_fee.py`,
`market_swarm/tests/test_artist_fee_mutation.py`, `market_swarm/tests/test_artist_fee_wiring.py`,
`tools/artist_fee_proof.py`, `tests/test_artist_fee_proof.py`, this finding.

**Appended.** `docs/ON-CHAIN-DESIGN.md` §15, `records/F-decision-log.md` (`D26`),
`records/A-research-ledger.md`.

**Edited, additively, in the harness.** `market_swarm/config.py` (an optional `artist_fee` block on
an event), `gateway.py` (the fee path, a two-signer send, and a writable-record move builder used on
the fee branch only; the no-fee path is byte-identical), `runner.py` and `ledger.py` (two fee columns,
`None` when no fee is configured), `datasets.py` (the fee arithmetic and the rate-must-accompany-the-
payment rule as dataset invariants), `cli.py` (`plan` prints an event's fee, and nothing new for an
event without one), and two assertions in `market_swarm/tests/test_gateway.py` that pin
`TransferResult`'s field set and the set of `dp` encoders the gateway may call.

**Not touched, and why.** `programs/cap_hook/**`, `tools/publish_v2*.py` and `tools/devnet_publish.py`
belong to two other runs and are inputs here. No devnet, no faucet, no publish.

**Found and not fixed.** The harness's *no-fee* path is v1-shaped against a v2 program:
`gateway._init_record` and `_init_extra_metas` call `tools/devnet_publish.py`'s builders, which send
`InitializeRecord` with four accounts and two data fields where the deployed program reads five
accounts and five fields, `dp.instruction_set_pending_price` sends the one-account v1 stage where v2
reads `[authority, record, mint]`, and `gateway.decode_record` expects a 19-byte record where the v2
program writes 70. Nothing in this change depends on those paths — the fee path builds its own stage
and does not decode the record through that function — and repairing them is a change to the swarm
harness's transaction and signer model, which is a different decision from this one. It is reported
here rather than silently repaired.

## 7. Reproduction

```
export PATH="$HOME/.local/share/solana/install/active_release/bin:$HOME/.cargo/bin:$PATH"
python3 tools/artist_fee_proof.py
python3 -m unittest tests.test_artist_fee_proof -v
python3 -m unittest market_swarm.tests.test_artist_fee market_swarm.tests.test_artist_fee_mutation \
    market_swarm.tests.test_artist_fee_wiring -v
```

Measured, the tool's own summary block from the orchestrator's run (signatures elided: every run
generates fresh keys under `tmp/artist-fee/keys/`, so the addresses and signatures differ between
runs and cannot be looked up by a reader — the properties do not):

```
LEG 1 PASS  fee paid, price 1e9 at 500 bps: price=1,000,000,000, fee_bps=500, fee=50,000,000,
            tx_fee=10,000, seller_delta=-50,010,000, artist_delta=50,000,000, seller_tokens=7,
            buyer_tokens=1, record_pending=0, held_since_unix=1,794,128,981
LEG 2 PASS  underfunded fee, atomic rollback: price=1,000,000,000, fee=50,000,000,
            seller_before=1,000,000, tx_fee=10,000, seller_delta=-10,000, artist_delta=0,
            err_index=1, err_code=1, seller_tokens=1, record_pending=0
LEG 3 PASS  over cap, p=1250000001: price=1,250,000,001, ceiling=1,250,000,000,
            fee_that_was_rolled_back=62,500,000, artist_delta=0, seller_delta=-10,000, tx_fee=10,000,
            err_code=6,010, err_index=2, seller_tokens=7, record_pending=0
LEG 4a PASS  rounding, price 19 pays 0: price=19, fee_bps=500, fee=0, instructions=2, tx_fee=10,000,
            artist_delta=0, seller_tokens=6
LEG 4b PASS  rounding, price 20 pays 1: price=20, fee_bps=500, fee=1, instructions=3, tx_fee=10,000,
            artist_delta=1, seller_tokens=5
LEG 5 PASS  100% fee, price 1e9: price=1,000,000,000, fee_bps=10,000, fee=1,000,000,000, tx_fee=10,000,
            seller_delta=-1,000,010,000, artist_delta=1,000,000,000, seller_tokens=4
LEG 6 PASS  zero price, refused 6009: staged=0, err_code=6,009, err_index=1, seller_tokens=4,
            record_pending=0
LEG 7 PASS  what the record stores after a sale: record_len=70, pending=0,
            held_since_unix=1,794,128,981, authority_is_issuer=yes, fields=9, fee=50,000,000,
            fields_equal_to_fee=0
LEG 8 PASS  the free ride, two transactions: price=1,000,000,000, fee_not_paid=50,000,000,
            artist_delta=0, seller_tokens=3, record_pending=0

PASS 9/9
  validator stopped; rpc port 20000 closed: True
```

The validator is `solana-test-validator 4.3.2`, booted on loopback from genesis: no `--url`, no
`--clone`, no faucet call (the issuer is funded at genesis with `--mint`). `tmp/artist-fee/REPORT.md`
and `tmp/artist-fee/measurements.json` are the run's durable outputs and are git-ignored; the numbers
above are the run's own, and the tool refuses to run at all if the `.so` it is described against has
changed.

## 8. What remains unverified

- **Nothing was run on devnet or mainnet.** No fee has been charged anywhere public, and no
  statement here is about a real artist's revenue.
- **The artist wallet in a local run is a throw-away key**, so the balances are evidence about the
  mechanism and not about any rate being right.
- **The two-signer sale has not been exercised through the product's own checkout.** The
  `ticketpath` checkout program (`docs/ON-CHAIN-DESIGN.md` §3.4 `transfer_ticket`) is still a design,
  so "the app" that builds this transaction is the harness's gateway, and the harness's live path is
  still v1-shaped for everything except the fee branch (§6): its record initialisation, its no-fee
  stage and its record decoder cannot run against the deployed v2 program. The fee path builds its own
  v2 stage and its own writable move, so it is shape-correct, and it is **unit-tested against a fake
  cluster and not measured on a validator**; what the validator measured is the same instruction set
  built by `tools/artist_fee_proof.py` with the same encoders. A live harness run should be the next
  thing that happens to this, after the v1 surface is repaired by the run that owns it.
- **A dataset cannot prove a fee was charged, only that each row's fee agrees with its rate.** The
  header carries no event-level policy, so a row from a fee event whose `fee_lamports` and
  `artist_fee_bps` are both deleted verifies and is indistinguishable from a row from a no-fee event.
  Closing that needs the rate in the header (or in the sidecar), which is a schema change and is
  written down as open in `market_swarm/CONTRACT.md` rather than half-done here.
- **The fee is on resales.** The harness charges it on a resale and not on a primary sale (the house
  selling the artist's own stock at face, where a fee would be the artist paying themselves). The
  operator's sentence is "on each resale", so this is the reading; if the intent includes primary
  sales, that is a one-flag change (`charge_artist_fee`).
- **The instructions-sysvar hook variant** of §5.1 is documented, not built and not measured.

## 9. Independent review

`tmp/review/artist-fee-review.md` — a reviewer who built none of this, read-only on the tree, with its
own validator run (PASS 9/9, the same nine legs and the same numbers) and its own attacks. It
confirmed the mechanism and the atomicity legs, and it killed two sentences of this finding's first
draft, both about the deployed program rather than about our client:

1. A read-only record does not produce a transfer that lands with the staging unconsumed. It produces
   `PrivilegeEscalation` at the Token-2022 instruction, before the hook runs, because v2's metas list
   requires the record writable and an inner CPI cannot escalate. Measured by the reviewer with one
   variable changed, and corrected everywhere (§4).
2. "Leg 1's `pending = 0` proves the writable move matters" was not evidence: the stage in the same
   transaction already marks the record writable, so the move's flag is redundant there. Measured,
   corrected (§4).

It also found two mutations the test table did not catch (both now in the table and both caught), three
crafted dataset rows that verified when they should not (negative fee, fee above the price, an executed
trade with a rate and no price — all closed), and the no-floor consequence of charging a percentage of
a staged price (§5(3)), which is named and left as a product decision.

Its second round checked every fix against the tree, re-ran both suites (546 and 1 166 tests, green) and
the proof tool (PASS 9/9, fresh keys), and closed with "nothing left blocks built and tested", naming
one hazard: the fee parameter defaults to charging, so a future primary-buy call site could charge the
artist for their own ticket without any test noticing. The answer in the tree is that both production
call sites now name the flag explicitly, and `market_swarm/tests/test_artist_fee_call_sites.py` reads
`runner.py` and fails if a call site does not — a third call site is a decision, not a silent default.

# 25. Solana from first principles: a primer for choosing a project

**Audience:** the operator, who is not a blockchain person and is preparing for a Solana
hackathon. **Purpose:** make the mechanism clear enough that project ideas stop being guesses.
**Scope:** how the chain works, what it is good at, what it is not, and the shapes a
Solana-native product takes. **It does not choose a direction**, and nothing here is a
recommendation for *this* repository.

**Written:** 2026-11-07. Everything below was checked against a live cluster or a primary
document in that window unless it carries another label.

## How to read the labels

Every factual line is one of four kinds, and the kind is visible in the sentence. This is the
repository's own convention, from `docs/ON-CHAIN-DESIGN.md`.

| tag | meaning |
|---|---|
| **MEASURED** | run from this machine on the date shown, command or endpoint named, result quoted |
| **DOCUMENTED** | a primary source states it; the URL is in §15 and usually in the line |
| **INFERENCE** | follows from documented facts, but no source says it in those words |
| **UNVERIFIED** | I could not settle it. What would settle it is named |

Two standing warnings before anything else.

1. **Solana changed underneath the tutorials in October 2026.** The consensus protocol was
   replaced (Alpenglow), the slot time halved, the block compute budget went up, transaction
   size went up, and the words "confirmed" and "finalized" stopped meaning different things.
   Anything written before that date is wrong on most of those, and a hackathon is exactly
   where you find out the hard way. §1.4 and §4 are the parts that moved.
2. **Every parameter you can read from a cluster should be read from the cluster.** §4.4 has a
   worked case where the constant in the source tree and the number both public clusters
   return disagree today. That is not a hypothetical.

---

## 0. The twelve-line version

- A **ledger** is an append-only list of signed entries. Everyone can hold a copy.
- A ledger alone is not enough, because two entries can conflict. What you actually need is
  agreement on **order**, and that is **consensus**.
- Consensus on Solana is **stake-weighted voting**: validators with locked capital vote on
  blocks, and a block that enough of them certify is final.
- **Accounts** are the only thing that exists. An account has a balance, some bytes, an owner,
  and an executable flag.
- **Programs are accounts with code and no state.** Their state lives in other accounts they
  own, and only they may write those accounts. That rule is the security model.
- **Wallets hold keys and sign.** A signature is permission. Nothing logs in.
- A **transaction** is a list of instructions plus the accounts they may touch, signed, with a
  fee, and it either fully lands or leaves no trace.
- **PDAs** are addresses with no private key that a program can sign for. They are how a
  program owns things.
- **SPL tokens** are just accounts owned by the token program. Token-2022 adds rules to
  transfers, including a program that can refuse one.
- **NFTs** are mints with supply one. Compressed NFTs put thousands of them in one Merkle tree
  so they cost a fraction as much.
- It is **cheap and fast when the work is parallel** (many independent accounts) and **bad when
  it is not** (one account everyone writes to, reading history, storing blobs, anything private).
- The only question that separates a chain-shaped idea from a database-shaped one:
  **whose discretion are you removing, and is that party the one that would otherwise break the
  rule?**

---

## 1. A ledger, and why consensus is the actual invention

### 1.1 What a ledger is

A ledger is a list of entries, each one a transaction signed by whoever submitted it. On Solana
a node does not need the whole history to validate the newest blocks; it needs recent state and
recent blocks (terminology page, "ledger"). That is why "the blockchain" is not really a
growing file you download, it is state plus enough history to convince you the state is right.

### 1.2 The problem was never storage. It was ordering.

Two signed entries can both be valid and contradict each other: the same wallet pays the same
coin to two people. Signatures cannot fix that, because both signatures are genuine. What fixes
it is a shared, agreed **sequence**: everybody accepts that entry A came before entry B, so B
is invalid. So a blockchain is a machine for agreeing on order among people who do not trust
each other, and everything else (accounts, tokens, programs) is built on top of that one
primitive.

This is worth holding onto, because most bad blockchain projects are bad precisely here: they
use the machine for storage, or for a database they could have hosted, and never touch the
ordering problem at all.

### 1.3 What consensus buys, and the two things it does not

What it buys: a record that no single participant can rewrite, and a rule that no single
participant can skip. Those are the same statement from two sides. If the organizer of an event
can silently un-sell a ticket, the record is worth less than one where they cannot.

What it does not buy:

- **Truth.** Consensus agrees on what was written, not on whether it is accurate. A price feed
  is only as good as the feed. A ticket is only a ticket if the venue honours it.
- **Anonymity, or privacy.** Every account and every instruction is public forever. There is
  no private mode. Confidential transfer extensions hide amounts, not the fact that a transfer
  happened, and they are a specific tool with specific costs (§6.3).

### 1.4 Consensus on Solana, as it is today

Short version: a rotating **leader** proposes blocks, validators vote on them with weight
proportional to their staked SOL, and a block certified by a large enough share of stake is
final. The mechanism for that changed on 2026-10-21 (DOCUMENTED,
`solana.com/upgrades/alpenglow`): **Alpenglow** replaced Tower BFT, and its voting component
**Votor** replaced vote transactions with votes sent directly between validators and aggregated
into certificates.

What that means in practice, and each of these is DOCUMENTED:

- **Two rounds, two thresholds.** A block finalises in one round if at least 80% of stake votes to
  notarise it; otherwise 60% thresholds decide notarisation, finalisation or skip in a second
  round. The migration page puts the tolerance at 20% adversarial stake plus 20% offline stake.
- **Finality is about 150 ms**, down from about 12.8 s. The page calls 150 ms an expectation
  against one stake distribution, not a constant.
- **`confirmed` and `finalized` are now the same state.** Both mean permanently committed and
  not roll-backable. I quoted this from the operator documentation rather than a summary
  ("Under Alpenglow, the Confirmed and Finalized commitment statuses are equivalent: both mean
  that a transaction has been permanently committed to the ledger and cannot be rolled back").
  `confirmed` still works and is being removed; point new code at `finalized`.
- **`processed` is still weaker.** It means "this node has seen it", not "the network agreed".
- **Vote transactions no longer appear in blocks at all**, so any throughput metric built by
  parsing vote instructions now measures nothing.
- **Proof of History no longer paces block production.** It used to be the mechanism people
  explained first, and it is now out of the block path. If a tutorial's first diagram is PoH,
  the rest of the tutorial is from before that date.

I checked the switch myself rather than trusting the page: the RPC method `getAgGenesisCert`
returns a real certificate on both mainnet and devnet (MEASURED 2026-11-07, `api.mainnet-beta`
and `api.devnet`, block id present, slot 459,652,999 on mainnet and 504,148,999 on devnet), and
the same call returns `null` on a cluster still running the old protocol. That is the cheapest
"is this cluster what I think it is" check there is.

### 1.5 What a client actually waits for

A wallet or a backend does not "send and finish". It sends, then polls or subscribes for the
signature's status. The ladder used to be three rungs, `processed` then `confirmed` then
`finalized`; it is now **two**, `processed` and then the committed state, with `confirmed` kept
as an alias for the second so that old code does not break (DOCUMENTED, RPC
`getSignatureStatuses` and the Agave commitment page quoted above). The honest rule for a demo
is: **show success only once the status is committed**, which today means `finalized`. Under the
current protocol that costs about 150 ms, so there is no reason to show success early, and
`processed` alone is not success.

Two related facts that bite in a demo:

- A transaction carries a `recent_blockhash` that is valid for `MAX_PROCESSING_AGE = 150` slots,
  about 30 seconds at the current slot time (DOCUMENTED, `solana-sdk/clock`). Past that the
  transaction can never land and has to be rebuilt and re-signed.
- A transaction that **fails still pays its fee** (DOCUMENTED, `solana.com/docs/core/fees`). A
  refusal is not free, which is why `tools/devnet_publish.py` sends its boundary pair
  deliberately rather than by retrying.

---

## 2. Accounts, not smart contracts

This is the single biggest difference from Ethereum, and the thing that makes Solana designs
feel odd until it clicks.

### 2.1 The account

Every account, without exception, is five fields (DOCUMENTED,
`solana.com/docs/core/accounts/account-structure`):

| field | what it is |
|---|---|
| `lamports` | balance, in lamports. 1 SOL = 1,000,000,000 lamports |
| `data` | a byte array, up to 10 MiB |
| `owner` | the program id allowed to modify `data` or debit `lamports` |
| `executable` | true if this account is a program |
| `rent_epoch` | deprecated; set to the maximum for a rent-exempt account |

There is no other kind of thing. There is no "contract storage", no "table", no "row". A token
account is an account. A program is an account. A mint is an account. Your application's state
is a set of accounts your program owns.

### 2.2 Programs have no state

A program account's data is bytecode (or a pointer to a separate program-data account, which is
why an upgradeable program is two accounts). It cannot hold a counter. If you want a counter,
you create an account, hand ownership of it to your program, and your program writes the
counter into that account's `data`.

### 2.3 The ownership rule is the whole security model

Only the owning program may modify an account's data or take its lamports. Any program may
*add* lamports to a writable account (DOCUMENTED, "modification rules"). That asymmetry is
deliberate: you cannot be robbed by a program you did not authorise, but you can be tipped.

So when a program runs, it is handed a list of accounts. It can read anything it is handed, and
it can write only the accounts it owns. Every "is this safe" question reduces to: **is the
account I am about to trust actually the account I think it is?** Which is why §5.3 exists.

### 2.4 What this changes about how you design

- **Accounts are rows, and you pass them in.** There is no `SELECT`. If your instruction needs
  data, the caller supplies the account that holds it, and your program must verify it is the
  right one. A program that trusts a caller-supplied account without checking has a bug, not a
  shortcut.
- **You pay for the rows, up front, per byte.** §4.4. A design that writes one account per
  ticket per event is a different economic object from one that writes one Merkle root.
- **Hot rows are a bottleneck.** §10.1.
- **Nothing is queryable.** There is no `WHERE`. Reading history means an indexer, not a
  program (DOCUMENTED by omission: nothing in the runtime offers a query interface; §10.2).

### 2.5 The same idea, in code you already have

`programs/cap_hook/src/lib.rs` is a small, complete example of all of this:

```rust
pub struct TicketRecord {
    pub face_value_lamports: u64,   // 8
    pub cap_bps: u16,               // 2
    pub pending_price_lamports: u64, // 8
    pub status: u8,                 // 1
}
```

Nineteen bytes of Borsh state (the struct declares `LEN = 8+2+8+1+1 = 20`, but four fields
serialise to 19 and the constant is never read; the account is sized from the actual bytes). It
lives in an account the program owns, derived from the mint's address (`["record", mint]`). It
is not a row in a database. It is an account that costs a deposit to
create (§4.4), that nobody but this program can write, and that any stranger can read without
asking permission. That last property is the product: `docs/ON-CHAIN-DESIGN.md` §1.2's claim is
that the resale record is complete "by construction, not by the API's good faith".

---

## 3. Wallets, keys and signing

### 3.1 Keys

An address is 32 bytes, shown in base58. It is either the public half of an Ed25519 keypair or
a PDA with no key at all (§5). A signature proves that whoever holds the private half approved
a specific message. On Solana the private key stays on the client; the chain only ever sees the
signature.

### 3.2 What a wallet is

A wallet is a key store plus a transaction builder plus a signing prompt. There is no session,
no login, no token. The chain does not know you exist; it knows that a transaction carried a
valid signature for a public key. "Connecting a wallet" is a browser-side handshake, not an
authentication event, and any claim of the form "the user is logged in" is a claim about your
frontend, not about the chain.

Two consequences that trip people up:

- **The fee payer is just the first account.** Any funded key can pay for anyone's transaction.
  A venue can pay the fees for its customers, which is the usual answer to "why do I need SOL
  to buy a ticket".
- **A private key is a bearer instrument.** Whoever holds it can move everything the address
  owns. There is no recovery, no support line, no reversal.

### 3.3 Key handling is a design decision, not an afterthought

`tools/devnet_publish.py` never opens a keypair. It shells out to `solana` and `spl-token` with
a path when they need one, and for the three instructions that belong to this project's own
program it calls `tools/solana_sign.py`, a separate process whose only output is one base58
signature. The parent process cannot print, log or traceback a key byte because it never has
one.

The other half of the same decision: **the program id is a property of the deploy keypair, not
of the crate name.** Lose that keypair and the program is frozen forever; keep it in a
repository and you have published the ability to replace the program. `programs/cap_hook/target/`
is git-ignored for exactly this reason, and `.public-denylist` refuses the keypair by shape as
well.

For a hackathon, the practical rule: a keypair in the repository is an incident, a keypair on
devnet that ends up on mainnet is a loss, and a demo that needs a private key typed into a
webpage is a demo you should not give.

---

## 4. Transactions, fees, lamports and rent

### 4.1 Anatomy

A transaction is a message plus signatures. The message is: a small header, a list of account
keys, a recent blockhash, and a list of instructions (each = program id, accounts, data bytes).
Total size is capped at **1,232 bytes** for legacy and v0 transactions, and **4,096 bytes** for
v1, which went live on mainnet in September 2026 (DOCUMENTED,
`solana.com/upgrades/larger-transaction-sizes`). The account count is capped at 64 for legacy
and v0.

The 1,232 number matters more than the instruction count, and people get this backwards. Run
the documented size budget and you have roughly 1,098 bytes for keys and data with one
signature: about 30 accounts, before you run out of room. **You do not run out of instructions.
You run out of bytes and accounts.** A design that wants to touch 100 accounts in one
instruction is a design that does not fit, and no amount of compute budget fixes it.

### 4.2 Fees

Two components, both DOCUMENTED (`solana.com/docs/core/fees`):

```
total_fee = base_fee + priority_fee
base_fee  = signature_count x 5,000 lamports
priority_fee = ceil(compute_unit_price x compute_unit_limit / 1,000,000)   # legacy and v0
```

- The base fee is a **protocol constant, not a market**. The only thing you bid with is the
  priority fee.
- Half the base fee is burned and half goes to the block producer; the priority fee goes
  entirely to the validator.
- The fee is taken from the payer before execution and is not refunded if the transaction
  fails.
- Signature count includes signatures checked by the precompiles, so a transaction that verifies
  an Ed25519 signature pays for it as if it had another signer.

### 4.3 What that costs in practice

MEASURED, 2026-11-07, mainnet block slot 466,666,032, block height 444,684,516, read with
`getBlock` and re-run twice to confirm it reproduces hit for hit:

| statistic | value |
|---|---|
| transactions in the block | 236 |
| fee, median | 5,514 lamports (0.0000055 SOL) |
| fee, 90th percentile | 18,659 lamports |
| fee, maximum in the block | 1,005,000 lamports |
| compute units consumed, median | 33,754 |
| compute units consumed, 90th percentile | 127,827 |

The median is one base fee plus a small tip, which is the shape of the whole fee market: the
base is fixed at 5,000 per signature and everything above it is a tip for landing sooner. For a
ticket product, the honest statement is that a per-ticket on-chain action costs 0.0000053 SOL,
which is a fraction of a cent at any SOL price above a dollar or two, and does not constrain the
business model. **The deposit in §4.4 does.** People worry about the wrong number.

### 4.4 Rent, which is not rent any more

The name is historical and the mechanism changed, so here it is as it actually works.

**Recurring rent collection is disabled.** Accounts must simply hold a minimum balance, and that
balance is refundable when the account is closed (DOCUMENTED,
`solana.com/docs/core/accounts/account-structure`: "Treat the balance as a refundable account
storage deposit"). So this is not a cost, it is working capital, and a design that creates and
closes accounts per transaction gets it back.

The formula (DOCUMENTED, `solana-sdk/rent`):

```
minimum_balance = (128 + data_len) x lamports_per_byte x exemption_threshold
```

where 128 is a per-account overhead constant, and the SDK's current constants are
`lamports_per_byte = 6,960` with the threshold folded to `1.0` after SIMD-0194. That is the same
price the older documentation expressed as "3,480 per byte-year with a 2.0-year threshold"; the
two factors were folded into one, and the rename is not cosmetic because there is no longer a
"per year" quantity.

**The rent sysvar is the authority, and it disagrees with the SDK constant.** MEASURED
2026-11-07 on both clusters: `getAccountInfo(SysvarRent111111111111111111111111111111111)`
returns 17 bytes which decode to `lamports_per_byte = 5,080`, `exemption_threshold = 1.0`,
`burn_percent = 50`. That is not arithmetic on my part; it is the cluster's own parameter
account saying so, and it is the single call that settles every rent question you will have.
The SDK's 6,960 is the protocol default compiled into a client library, not a statement about
the cluster in front of you.

**Now the worked case, and this is the part to actually remember.** MEASURED 2026-11-07, direct
RPC `getMinimumBalanceForRentExemption` against both public clusters:

| data size | devnet | mainnet |
|---|---|---|
| 0 | 650,240 | 650,240 |
| 82 (a mint) | 1,066,800 | 1,066,800 |
| 130 | 1,310,640 | 1,310,640 |
| 165 (a token account) | 1,488,440 | 1,488,440 |
| 1,000 | 5,730,240 | 5,730,240 |

Every row is exactly `(128 + size) x 5,080`, which agrees with the rent sysvar decode above.
**Both clusters are charging 5,080 lamports per byte, not the 6,960 the source constants say.**
At 6,960 a token account would be 2,039,280 lamports, which is the number in every tutorial and
in the SDK default. Both clusters return 1,488,440.

What is settled and what is not: the rate is documented, because the cluster states it (the
sysvar decode). The *cause* is an INFERENCE. SIMD-0437 proposes a staged reduction whose
schedule lists `6960 → 6333 → 5080 → 2575 → 1322 → 696`, and 5,080 is exactly one of those
steps, so the cluster looks part-way through it. But the proposal's own status line still reads
`Idea`, so the proposal is not the source of truth here and never was: the chain is. **The
lesson is operational: call `getMinimumBalanceForRentExemption(size)`, or decode the rent
sysvar, on the cluster you are deploying to.** A cached constant is a future bug, and the
numbers move.

### 4.5 Compute

Three limits, and they answer three different questions (all DOCUMENTED, links in §15):

| limit | value | what it constrains |
|---|---|---|
| default budget per instruction | 200,000 CU (3,000 for a builtin) | how much work one instruction gets for free |
| maximum per transaction | 1,400,000 CU | what one transaction can ever do |
| per block | 100,000,000 CU | total work in a slot |

That last row has a trap in it. `agave`'s `MAX_BLOCK_UNITS` constant still reads 60,000,000,
because the raise is feature-gated: the live limit comes from `MAX_BLOCK_UNITS_SIMD_0286`. So a
reader who greps for `MAX_BLOCK_UNITS` concludes the block ceiling is 60M and that this section
is wrong. Read the symbol, not the substring. (The "raised in July 2026" date I first wrote
here is UNVERIFIED: the proposal's own front matter does not carry it, and the upgrades page did
not load from this host. The value is documented in the source; the date is not.)

Some costs that matter if you are budgeting a program (DOCUMENTED, `agave`
`execution_budget.rs`, `cost-model/src/block_cost_limits.rs`, and the scheduler constants table):
SHA-256 is 85 CU plus 1 CU per byte; `create_program_address` is 1,500 CU; an Ed25519 signature
verification is 2,400 CU in the block cost model (the strict cost, 30 x 80); secp256k1 is 6,690
and secp256r1 4,800; one signature is 720; one write lock is 300.

Note that the last two tables are different accounting. The first is what you are charged during
execution against your limit. The second is the pre-execution estimate used to decide whether
your transaction fits in a block. Budget against the first, reason about whether you land with
the second.

### 4.6 Why the arithmetic on chain is a design decision

A program that computes a percentage has to choose its integer width. `programs/cap_hook` does
it the way the design says to:

```rust
let lhs = (self.pending_price_lamports as u128) * 10_000u128;
let rhs = (self.face_value_lamports as u128) * (10_000u128 + self.cap_bps as u128);
lhs <= rhs
```

`u128` on both sides, no division, inclusive at the cap. The `u64` version of the same
expression wraps above `2^64 / 20_000` and would silently admit any price, which is the specific
bug a reviewer should look for first. The repo's four unit tests assert both sides of the
boundary, and I re-ran them rather than quoting the README: MEASURED 2026-11-07,
`cargo test --release` in `programs/cap_hook`, 4 passed, 0 failed.

One honest caveat about those tests, because this file's job is to prepare you for a judge who
reads the code rather than the README. The test named
`u64_multiply_would_wrap_but_u128_does_not` does not actually perform a `u64` multiplication. Its
assertions are all in `u128`, where `u64::MAX x 20_000` cannot wrap, so the final assertion is a
tautology. What is genuinely defended is the predicate itself (`cap_admits` is `u128`, no
division) and the inclusive boundary, which two of the tests do pin. If you inherit code like
this, fix the test rather than the claim: it should compute the `u64` product and assert that it
wraps, so that a later edit which simplifies the u128 back to u64 fails loudly. That is the kind
of gap a judge finds in ninety seconds, and it is cheap to close.

---

## 5. PDAs: addresses with no private key

### 5.1 How they are made

A program-derived address is a hash of some seeds, the program's own id, and a bump byte, chosen
so the result is **not** a valid point on the Ed25519 curve. Off-curve matters: it is what makes
it provable that no private key exists for that address, so no signature can ever come from it
except one the program itself manufactures.

- `find_program_address(seeds, program_id)` searches bumps downward from 255 until it lands
  off-curve, and returns the address plus the bump.
- `create_program_address(seeds, program_id)` is the check-only version, and it costs 1,500 CU.

### 5.2 The two powers

1. **A stable address with no key.** You can derive a ticket's state account from the ticket
   mint's address, and anyone in the world can recompute it. No registry needed, no lookup table,
   no guessing.
2. **`invoke_signed`.** A program can sign a cross-program invocation "as" a PDA, by passing the
   seeds that derive it. That is how a program holds an escrow, mints a token, or creates an
   account nobody else can create. It is not a loophole: the runtime recomputes the address from
   the seeds you supply and refuses if it does not match.

In `programs/cap_hook`:

```rust
pub fn record_seeds(mint: &Pubkey) -> [&[u8]; 2] { [b"record", mint.as_ref()] }
pub fn extra_metas_seeds(mint: &Pubkey) -> [&[u8]; 2] { [b"extra-account-metas", mint.as_ref()] }
```

Two PDAs per mint, both derived from the mint address, both created by the program signing for
itself with `invoke_signed`. The literal `extra-account-metas` is not this project's choice: it
is fixed by the SPL interface, because that is the address Token-2022's tooling looks for
(DOCUMENTED, `spl-transfer-hook-interface`:
`const EXTRA_ACCOUNT_METAS_SEED: &[u8] = b"extra-account-metas"`).

### 5.3 The check that matters

A PDA is only trustworthy if you **re-derive it and compare**, because a caller can hand you any
account it likes. This is the heart of `execute()` in `cap_hook`, and the order matters as much
as the checks:

```rust
// 1. amount != 1 -> refuse
// 2. the extra-metas account must be the PDA for this mint, re-derived here
let (expected_metas, _) = Pubkey::find_program_address(&extra_metas_seeds(mint.key), program_id);
if expected_metas != *extra_metas.key { return Err(TicketpathError::WrongExtraAccount.into()); }
// 3. then `record_ai.owner != program_id`
// 4. then the record must be the PDA for this mint
// 5. then status, then "is a price staged", then the cap itself
```

Skip any of it and the program will happily read a record the attacker wrote, which is the
difference between an enforcement mechanism and a decoration.

**And be honest about which checks were dropped.** `docs/ON-CHAIN-DESIGN.md` §3.9 lists seven
preconditions, in order: `amount == 1`; `record.token_account == source`; the event policy key
matches the record; the policy key is the expected PDA; a stage is active; the destination's
owner equals `record.pending_dest`; and the status is valid. `execute()` implements four of the
seven (amount, status, the stage, and the cap, which the design puts in a different place). It
does not implement `record.token_account == source`, it has no event policy account at all, it
does not compare the destination, and it has no expiry check (the design's `6018`). The README
admits the destination and expiry gaps and does not mention the other two. That is exactly the
comparison a judge will make when reading the design and the code side by side, and the document
you hand over should make it first.

### 5.4 What a PDA is not

- **Not private.** Its address and contents are public, and the seeds are usually guessable.
- **Not a secret.** Anyone can compute it; the security comes from the runtime's derivation
  check, not from obscurity.
- **Not a guarantee that the rule is enforced.** A PDA record is an attestation unless something
  forces transfers through the program. §6.4 and §6.5 are about that gap, and it is the single
  most important design question in this repository's on-chain work.

---

## 6. SPL tokens and Token-2022

### 6.1 The pieces

- A **mint** is an account holding `mint_authority`, `supply`, `decimals` and `freeze_authority`.
  No mint authority means a fixed supply.
- A **token account** holds `mint`, `owner`, `amount`, and a delegate. Balances are integers;
  `decimals` is only about where the decimal point goes. A ticket with 0 decimals means one base
  unit is one ticket, which is what makes `amount == 1` a meaningful check.
- One wallet can own many token accounts for one mint, which is why the **associated token
  account** exists: a PDA derived from the wallet, the token program and the mint, so there is
  one canonical account per (wallet, mint) pair. Anybody can create yours, and it is still yours.
- **Authorities** are the interesting part: mint authority can create supply, freeze authority
  can freeze your account, and both can in principle be revoked. For a ticket, an unrevoked mint
  authority means the organizer can print more seats.

### 6.2 Two token programs, on purpose

The original Token program (`Tokenkeg...`) and Token-2022 (`TokenzQd...`) are separate
deployments with separate program ids. Token-2022 is a strict superset: the first 165 bytes of a
token account and the first 82 of a mint are identical, instruction layouts are byte for byte
compatible, and new fields go after byte 165 as TLV extensions. Features were added by deploying
a second program rather than upgrading the first because a transaction has to name every program
it touches, and nobody can be forced to accept a new one.

Practical consequence: **a mint belongs to one program, and that choice is permanent.** A
Token-2022 feature is available to Token-2022 mints and to nothing else.

### 6.3 The extension surface

29 enum variants exist in the interface crate (`ExtensionType`) as of this writing (DOCUMENTED).
One of them, `Uninitialized`, is a sentinel rather than a feature, so there are 28 real kinds.
The ones that matter for a ticketing-shaped product:

| extension | what it does | the catch |
|---|---|---|
| `NonTransferable` | tokens cannot move; the holder can still burn and close | absolute. No "transferable to X", no "after date Y" |
| `TransferHook` | the mint names a program that is CPI-called on every transfer and can fail it | the hook sees accounts and an amount, never a price (§6.4) |
| `TransferFeeConfig` | basis points withheld on every transfer, up to 10,000 bps, plus a max-fee cap | withheld on the *recipient* account; needs an explicit withdraw step |
| `PermanentDelegate` | an authority that can transfer or burn from any account of that mint | that is exactly as powerful as it sounds, and it is the only thing that can claw a ticket back |
| `MetadataPointer` / `TokenMetadata` | metadata stored in the mint, pointer naming where it lives | a client must check the mint points at the metadata *and* the metadata points back |
| `DefaultAccountState` | new accounts are created frozen until someone unfreezes them | useful as an allowlist gate at the account level |
| `Pausable` | a pause authority can stop all transfers, mints and burns | a single point of failure by design |
| `CpiGuard` | restricts what a program can do with your tokens inside a CPI | protects the user, constrains your own composition |
| `ConfidentialTransfer` | encrypted amounts | must be configured at mint creation, cannot be added later |
| `GroupPointer` / `TokenGroup` | a mint can be a group, another a member of it | the collection primitive, usable for a season pass |
| `ImmutableOwner` | owner can never be reassigned | every ATA already has it |
| `MemoTransfer` | an incoming transfer must be preceded by a memo instruction | the memo is a separate instruction, not part of the transfer |

Extension placement matters: mint-side extensions must be set before the mint is initialised,
account-side ones can be added later with a `Reallocate`.

### 6.4 Transfer hooks, and the price problem

A hook is the most interesting extension for this project, so here is exactly what it gets.

When a hooked mint is transferred, Token-2022 CPI-calls the hook program with an `Execute`
instruction whose data is **8 discriminator bytes plus `amount: u64` little-endian, and nothing
else** (DOCUMENTED, `spl-transfer-hook-interface/src/instruction.rs`). I recomputed the
discriminator rather than copying it: `sha256("spl-transfer-hook-interface:execute")[:8]` is
`69 25 65 c5 4b fb 66 1a`, first byte 105, which matches the comment in `cap_hook` about why the
SPL opcode cannot collide with its own 0..=3 tags.

The accounts arrive in this order: source, mint, destination, source authority, the extra-accounts
validation account if present, then the extra accounts themselves. Two further documented details
that are easy to miss:

- **The token program does not go looking for those extra accounts.** It forwards the remaining
  accounts from the transfer instruction into the CPI. Resolving them from the
  `["extra-account-metas", mint]` PDA is done by the client, or by the interface library on
  chain, not by Token-2022. This is why `tools/devnet_publish.py` builds the transfer's account
  list explicitly, with the order read back from a landed `spl-token transfer`.
- **On a confidential transfer the amount passed to the hook is `u64::MAX` as a sentinel**,
  because the token program does not know it. Any hook that enforces an amount policy has to
  handle that case explicitly. `cap_hook` refuses every `amount != 1`, so it would refuse a
  confidential transfer of a single ticket. That is an INFERENCE from the documented sentinel,
  not a measured result, and it is the kind of composability surprise the extension surface is
  full of.

And now the point the whole ticketing design turns on: **there is no price field in an SPL
transfer.** `Transfer` carries `amount: u64`. `TransferChecked` carries `amount` and `decimals`.
No price, no memo, no metadata, no consideration of any kind. A hook therefore cannot know what
a ticket sold for.

That is not a limitation of this project's program. It is a property of the token standard, and
it means:

- A hook can enforce **`amount == 1`** and **"the destination is on a list"** with no extra
  state.
- A hook can enforce **a price cap only if the price arrives through an account the program can
  read**, written earlier in the same transaction by something the seller cannot skip.
- A hook **cannot** enforce a royalty, a cap, or a "no resale above X" rule against a transfer
  that simply does not tell it the price.

`docs/ON-CHAIN-DESIGN.md` §1.3 says this in the design's own words, and
`programs/cap_hook/src/lib.rs` opens with it. The staging instruction (`SetPendingPrice`) exists
because of it, and the README is explicit that the free-standing staging instruction is a
scaffold, not the design: in a real deployment the price would arrive from the escrow or the
listing, and the escrow was rejected on scope grounds (decision D6).

**The general lesson, which is worth more than the ticketing case:** a chain enforces exactly
what is in the accounts it is handed. If your business rule depends on a fact that is not on
chain, the rule is not on chain either, whatever the marketing says.

### 6.5 What that forces you to choose

Three shapes, and they are genuinely different products:

1. **Hook plus a record account** (what is built here). Enforces a rule, but only over transfers
   that carry the staged price, and only for mints created with the hook. A `spl-token transfer`
   that omits the extra accounts fails; a mint created without the extension is unaffected
   forever.
2. **Escrow: a PDA holds the ticket and the money, and the swap is atomic.** Now the price is not
   attested, it is the actual payment, so the cap binds on real value. But an escrow is a venue,
   not a constraint: anyone who dislikes the cap simply does not use the venue. It also means
   building a marketplace, with all the dispute cases that implies.
3. **No enforcement, only record**: write every hop on chain, accept that the record can go stale
   the first time somebody transfers outside the program. An honest attestation ledger,
   bypassable.

There is no fourth option in which a hook enforces a price it was never told.

### 6.6 One correction this reading produced

`docs/ON-CHAIN-DESIGN.md` §1.3 says the hook program id "is written into the mint's
`TransferHook` extension at mint creation and **cannot be changed afterwards**". The mint side of
that is right; the "cannot be changed" half is only true if the transfer-hook authority is
revoked.

DOCUMENTED, and I checked it in the program source rather than a summary:
`token-2022/program/src/processor.rs` handles `AuthorityType::TransferHookProgramId` inside
`SetAuthority`, reading the mint's `TransferHook` extension and overwriting its program id when
the current authority signs. So the mint can be repointed at a different hook program by
whoever holds that authority, and immutability is achieved by setting the authority to `None`.

That does not weaken the invariant the design cares about (the cap is in the record account, and
`cap_bps` genuinely has no setter). It does change what a sentence in the design document is
allowed to claim, and a judge who knows the extension will ask. Recorded here rather than edited
there, because that file was not mine to change in this run.

---

## 7. NFTs and compressed NFTs

### 7.1 What an NFT is here

An NFT is not a distinct type. It is a mint with supply 1, zero decimals, and (usually) the mint
authority revoked. Metaplex's older Token Metadata program adds a metadata account and a
master-edition account as PDAs of the mint, where the master edition's existence is the proof of
non-fungibility.

### 7.2 Three current options, and the honest answer

- **Metaplex Token Metadata**: legacy. Metaplex's own page says it "remains supported, but is not
  recommended for new projects. Use Core instead."
- **Metaplex Core**: one account per asset, about 0.003 SOL per mint, the recommended NFT
  standard for new work.
- **Token-2022's own `TokenMetadata` extension**: metadata inside the mint, no Metaplex at all.
  Useful when the ticket needs Token-2022 features, which is the case here.

There is no documented ranking between Core and Token-2022 metadata. What is documented is that
both exist, what each costs, and that they are different programs. If your ticket needs a hook,
the token must be a Token-2022 mint, and that settles it.

### 7.3 Compressed NFTs

A compressed NFT is not an account. It is a leaf in a Merkle tree: the whole tree's root lives in
one on-chain account, and the individual NFT's data lives in the transaction that created it,
which an indexer then serves back to you. The tree is a **concurrent** Merkle tree, keeping an
on-chain changelog so several changes can land in one slot before a proof is invalidated.

Cost is set by three parameters chosen at tree creation: max depth (how many leaves), max buffer
size, and canopy depth (how many proof levels are cached on chain instead of being passed in).
Documented figures:

| what | cost |
|---|---|
| tree, 16,384 leaves, canopy 0 | about 0.222 SOL |
| tree, 16,384 leaves, canopy 11 | about 1.134 SOL |
| tree, 1,048,576 leaves, canopy 10 | about 1.673 SOL |
| a 1,000,000-piece collection compressed vs uncompressed | about 50 SOL vs about 12,000 SOL |

The trade is real and worth stating plainly: a compressed NFT **cannot** carry a Token-2022
transfer hook, because it is not a token account (INFERENCE from the tree structure, not a
sentence in a doc). You buy scale by giving up the enforcement surface. It also means reading
your own data requires an indexer, not a program.

### 7.4 zk compression is a different thing

Light Protocol's zk compression compresses **token accounts and PDAs**, not NFTs, and works with
any SPL or Token-2022 mint. Vendor-quoted: a token account at about 2,000,000 lamports normally
against about 5,000 compressed. That is a genuinely different lever from cNFTs and is aimed at
application state, not collectibles. Vendor docs, so label it as such, and note that their
"normal" token account is the 6,960-lamports-per-byte figure: at the rate measured in §4.4 the
same account is 1,488,440. The comparison survives; the absolute number does not.

### 7.5 Do the arithmetic for a real venue

This is the calculation that should drive a design, and it uses the rent numbers measured in
§4.4 rather than a tutorial's.

Per ticket, the "one account per ticket, with a rule attached" design:

| account | size | deposit |
|---|---|---|
| the `TicketRecord` PDA from `cap_hook` | 19 bytes | 746,760 lamports |
| a Token-2022 token account holding the ticket | 165 bytes | 1,488,440 lamports |
| **per ticket** | | **2,235,200 lamports (0.00224 SOL)** |
| 20,000 tickets | | **about 44.7 SOL** |

Against that, a 20,000-leaf compressed tree is documented at roughly 0.22 to 1.2 SOL depending
on canopy.

Three honest qualifications, because this comparison is where people overclaim:

1. The deposits are **refundable** when the accounts are closed, so 44.7 SOL is working capital,
   not a fee. If the organizer reclaims on burn after the event, the real cost is the float.
2. The compressed option **cannot** enforce a transfer rule. You are not comparing the same
   product at two prices; you are comparing enforcement against scale.
3. The per-ticket figures are MEASURED arithmetic on today's cluster rate. The tree figures are
   DOCUMENTED table values from the state-compression page, not measurements of a tree anyone
   built here.

If you remember one number from this file, let it be that an account costs roughly half a
byte costs about 5,080 lamports, so a design decision to "just make one account per X" is a
budget line with an X in it.

---

## 8. Oracles: a price feed is an account, not a subscription

This one is short and it removes a whole class of confusion.

**A program only runs when a transaction invokes it.** There is no background job, no cron, no
callback, no listener. So a program cannot "subscribe" to anything. A price feed on Solana is
**an account that holds data**, which your instruction either reads from the accounts it was
handed or does not get at all (DOCUMENTED, `solana.com/docs/core/programs`).

The two live designs are both **pull-based**:

- **Pyth.** Fetch signed price data from the off-chain Hermes service, submit it to the on-chain
  Pyth receiver in the *same transaction*, and read the verified result from a `PriceUpdateV2`
  account (DOCUMENTED, Pyth docs). The update fee is documented as 0 on supported networks, but
  the docs say to call `getUpdateFee()` rather than assume it. Each feed carries `price`,
  `conf` (a confidence interval), `expo` and `publishTime`.
- **Switchboard On-Demand.** Same shape: the client fetches an update instruction, the same
  transaction carries it (DOCUMENTED, `switchboard-xyz/on-demand`, which is a change from its
  older push model). Its docs site did not resolve from this machine, so anything beyond the
  repository README is UNVERIFIED here.

Two consequences that decide designs:

1. **Staleness is your problem.** The chain will not tell you a price is old. Pyth's own guidance
   is to read with an age bound and refuse beyond it, and to treat a confidence interval that is
   wide relative to the price as a reason to refuse. If you skip that, a stale feed is a
   confidently wrong number, which is worse than a missing one.
2. **Paying for the update is a per-transaction cost you control.** Pull means you pay for
   freshness exactly when you need it, not continuously. That is usually the right trade for a
   ticket priced a few times a day.

**The link to the ticketing project is not mechanical, it is methodological.** The pricing engine
in this repository already has the right posture: when it lacks the observation a number would
need, it refuses and says which observation is missing (`README.md`, and the refusal path in
`ticketpath/`). A stale oracle violates the same principle in a subtler way, because it hands
you a number that looks like an answer. The habit to carry across is: **age and confidence are
part of the value, and a value without them is not a value.**

Solana does have a clock, by the way: the `Clock` sysvar gives slot, epoch and a unix timestamp
that validators agree on. It is coarse and it is not a scheduler. Designing "this cap applies
until the event ends" is fine; designing "run this at 9am" is not a thing the chain does.

---

## 9. Devnet, testnet, mainnet: what actually differs

| | mainnet-beta | devnet | testnet |
|---|---|---|---|
| tokens are real | yes | no | no |
| resets | no | may be reset | may be reset, and documented as intermittent |
| faucet | no | yes, documented cap 5 SOL per request | yes |
| what it is for | production | building and demoing | validator and release testing |

(DOCUMENTED, `solana.com/docs/references/clusters` and the CLI basics page.)

The practical facts that decide a hackathon:

- **The public RPC endpoints are shared infrastructure and are documented as not intended for
  production.** They rate limit (documented: 100 requests per 10 s per IP, 40 per 10 s for a
  single method, 40 concurrent connections) and answer 429 or 403. A judging window is exactly
  when everyone hits them. If your demo depends on `api.devnet.solana.com` at a fixed moment,
  your demo is a coin flip.
- **Airdrops are not guaranteed.** This repository measured it: the devnet RPC faucet answers
error 410, "the RPC faucet is closed on this cluster", so `solana airdrop` cannot work and
  retrying is wasted time. Funding needs the web faucet. That is recorded in
  `records/findings/21-onchain-hook-in-tree-and-publish.md` §2, and `tools/devnet_publish.py`
  refuses with that instruction rather than looping.
- **Devnet can be reset.** No primary source promises an uptime or a retention period, so
  assume nothing and keep a local validator path for anything you must be able to show.

### The demo rule that separates a credible submission from a confusing one

**Every surface that shows on-chain data must name its cluster, and a local run must be
impossible to mistake for a devnet one.** This repo is a worked example of the discipline even
though the deployment has not happened, and the mechanism is worth naming precisely because it
is a good pattern: the local run writes a *different file* (`records/devnet-artefacts.local.json`)
from the devnet one, so the devnet path simply never sees it, **and** the console's own gate
refuses to render the `[DEVNET]` slot unless the artefact's cluster is `devnet` and it carries a
signature (`ticketpath/console/page.py`). Two independent reasons, one of them structural. The
`[DEVNET]` label is earned by a signature you can look up, not by a config flag.

That matters more than it sounds. A judge who suspects a screenshot is a mock stops evaluating
the product and starts evaluating your honesty, and that is a worse conversation.

---

## 10. What is cheap and fast, and what will sink your idea

This is the section to read twice, because most hackathon Solana projects fail here rather than
at the cryptography.

### 10.1 The hot account problem

The runtime locks every writable account a transaction touches, so two transactions that write
the same account cannot execute in parallel; the later one is excluded and retried
(DOCUMENTED, `agave/accounts-db`). Each write lock also costs 300 CU in the cost model.

So the ceiling is per account, not per network. **If every user writes one global account, your
throughput on that account is one transaction per block, no matter how fast the network is.**
Global counters, one config account, one order-book row, one prize pool everyone deposits into,
one "total tickets sold" counter: these are the designs that die at a demo where ten people
press the button at once.

The documented per-account compute ceiling is **contested between sources**: the constants page
says 12M CU, `agave` master has 24M, and a proposal sets it to a share of the block limit. Do
not hardcode it. Design so that one account is not your bottleneck, which is the advice that
survives all three numbers.

### 10.2 There is no query

State is a key-value store keyed by a 32-byte address. There are no secondary indexes in the
protocol, no `WHERE`, no `GROUP BY`, no aggregation over a set. `getProgramAccounts` with a
filter falls back to a scan inside the validator, which is why public providers restrict it and
why indexers exist as a business (DOCUMENTED, `agave/rpc` and the accounts page).

Consequences:

- If your product's main verb is "show me all X where Y", that verb does not belong on chain. It
  belongs in an indexer reading the chain.
- Your program cannot sort, join, or loop over an unbounded set. 1.4M CU and 1,232 bytes are not
  enough, and growing account data is throttled to 10 KiB per instruction anyway.
- "On-chain" for the read path usually means "an indexer with a chain-shaped source of truth",
  and that is a legitimate architecture. Just do not call the indexer the chain.

### 10.3 There is no privacy

Every address, balance change, instruction and memo is public forever. Confidential transfer
(and the ZK ElGamal proof program behind it) hides amounts. It does not hide that a transfer
happened, nor who holds what. A ticket is a linkable object by nature, so "private ticketing"
is a hard research problem, not an extension flag.

### 10.4 Storage is a deposit, and the deposit is the budget

§4.4 and §7.5. The number to hold in your head: roughly 5,080 lamports per byte today, measured,
with 128 bytes of overhead per account before your data starts. An account per user per event is
a capital requirement. A Merkle root is not.

### 10.5 What is genuinely fast

MEASURED 2026-11-07, `getRecentPerformanceSamples` on mainnet, one 60-second sample:

- **280 slots in 60 s**, so about 4.7 slots per second, roughly 214 ms per slot wall-clock.
- **91,866 non-vote transactions in that minute**, about 1,530 per second.
- The same call returns `numTransactions == numNonVoteTransactions`, which is the empirical
  signature of vote transactions having left the block: see §1.4.

What that sample does **not** tell you is whether the 214 ms is a slower slot or skipped slots,
because a 60-second window with 280 produced slots is equally consistent with either. My first
draft asserted "skipped slots", which was an INFERENCE sitting inside a MEASURED bullet, and it
is exactly the kind of thing this file tells you not to do. The nominal slot time is 200 ms and
the sample is consistent with it; to settle the difference you need `getSlot` twice sixty seconds
apart, or the `blockTime` deltas across consecutive slots.

And from the definition rather than a sample: finality is about 150 ms and a plain transfer costs
5,000 lamports. So "cheap and fast" is real, and it means something specific: **many independent
accounts, small writes, sub-second confirmation, fees that do not appear on a P&L.** It does not
mean "a database that is slow", and it definitely does not mean "unlimited".

### 10.6 The table

| what you want to do | verdict | why |
|---|---|---|
| 10,000 users each writing their own account | excellent | disjoint write locks, parallel by construction |
| one global counter everyone increments | **fails** | serialised on one write lock (§10.1) |
| sub-second confirmation of a small state change | excellent | ~200 ms slots, ~150 ms finality |
| a per-action fee of a fraction of a cent | excellent | 5,000 lamports base, measured median 5,348 |
| store a 5 MB image | no | 10 MiB per-account cap, and the deposit is about 25.4 SOL |
| one account per ticket across a 20,000-seat venue | possible, budget it | about 45 SOL of refundable deposits (§7.5) |
| 20,000 compressed tickets | cheap | a documented 0.22 to 1.7 SOL of tree |
| "show me all tickets for event X by price" | off chain | no indexes, no query (§10.2) |
| private balances | hard | amounts only, and the participation is still public (§10.3) |
| run something at 9am | no | programs only run when a transaction calls them (§8) |
| a rule you can prove nobody bypassed | excellent | this is the actual product (§11) |

---

## 11. What blockchains are good at, and where they add nothing

### 11.1 The five things that are genuinely better on chain

1. **A rule the operator cannot break.** Not "the operator promises", not "our API refuses":
   the transfer fails in the runtime with an error code, and the failure is on a public ledger.
   This is the only property among the five that nothing else can buy.
2. **A record nobody can edit.** A history of custody and price that an organizer, a platform,
   or you cannot quietly rewrite. It is worth what a third party's willingness to rely on it is
   worth, which is a real number when the third party is a regulator, an insurer, or a
   settlement counterparty.
3. **Atomic settlement between strangers.** Two parties who do not trust each other exchange two
   assets in one transaction, or neither moves. This removes the "send first" problem without
   introducing a custodian.
4. **Composability.** Any program can call any other, so a rule you write can be used by someone
   you have never met, without an integration meeting. This is why the token extension surface
   is interesting: a hook is a rule other people's transfers run through. The catch is that the
   composition cuts both ways, which is the lesson of §6.4: your rule runs inside everybody
   else's transfer, including transfers that hand you a sentinel amount you did not expect, and
   every caller that is not hook-aware fails with a confusing error instead of a clear one. A
   rule that composes is worth more than one that does not, and it costs more to keep working.
5. **Uniqueness and provenance.** One object, one owner, provable lineage, no double-issue. For
   tickets this is the least glamorous and most useful property: it is what "the same seat was
   sold twice" cannot survive.

### 11.2 The one question that decides whether an idea is chain-shaped

> **Whose discretion are you removing, and is that party the one that would otherwise break the
> rule?**

If the answer is "nobody's, we just need a database", the chain is decoration. If the answer is
"the organizer's, on resale caps" or "the platform's, on who can hold this ticket" or "both
sides', on whether settlement is atomic", you have something only a chain does.

This is also, verbatim, the hackathon's own published criterion for the top prize: "a working
product that uses Solana for something it's good at (speed, low fees, composability, on-chain
ownership), **not a chain bolted onto a web2 app**" (`records/findings/17-hackathon-rules-recheck.md`
§2.3, quoted from the event page). The same document records that the four equally weighted
criteria are Technology, Design, Completion and Learning, that code quality is explicitly not
scored, and that under the second published regime originality and technical complexity carry a
quarter each. Either way the same thing wins: **a hard technical thing that works, that a judge
can see working.**

### 11.3 Where a chain adds nothing

- **A single trusted writer.** If one company is the authority for the data and everyone already
  accepts that, the chain adds cost and a key-management problem.
- **Private data.** Medical, personal, anything you would not publish. There is no private mode.
- **Reporting.** "All sales by section this quarter" is a SQL query. On chain it is an indexer
  plus a data warehouse, which is fine, but be honest that the chain is the source and not the
  engine.
- **High-frequency tiny updates.** A write per keystroke, per impression, per heartbeat: the rent
  per account and the per-block compute will price you out.
- **A consumer product whose users must not know what a wallet is.** This is a design
  constraint, not a disqualification: pay the fees for them, or use a link that carries the
  transaction (Actions/Blinks), but do not pretend the wallet is invisible.

### 11.4 Applying it to ticketing, honestly

A primary-market pricing engine does not need a chain to compute a price. Nothing about fitting
a model to resale records requires consensus. The chain-shaped part of ticketing is narrower and
sharper:

- **The resale price cap** is a rule the organizer wants and the reseller does not. Only
  enforcement the reseller cannot route around is worth anything, and "the API rejects it" is
  not that (§6.5).
- **The custody record** is worth something because it is the input to the pricing model and
  because a stranger can audit it without trusting the venue.
- **The cap on a ticket you cannot re-mint** is a property of the mint's authorities being
  revoked, which is a fact about the chain, not a policy.

What is *not* chain-shaped: the pricing model, the dashboard, the analytics, the customer
support, the email. Saying so out loud is what makes the on-chain claim credible.

---

## 12. Idea sparks: what Solana-native products look like

Thirteen shapes, each with the Solana property it leans on, the mechanism, and the test from
§11.2 applied. **These are hypotheses, not recommendations**, and none of them is a decision
about this repository's direction. Programme evidence class: D to E, since they are designs
rather than findings.

**1. A resale cap enforced at transfer.** Property: a rule the operator cannot break. Mechanism:
Token-2022 `TransferHook` plus a record PDA holding face value and cap, with the hook refusing
any staged price over the cap. The version in this repo. Test: the reseller would otherwise
route around the API, so yes, chain-shaped. But be honest that it binds only over transfers that
carry the staged price (§6.4). Source: 
`solana-program.com/docs/token-2022/extensions`.

**2. A royalty that actually pays.** Property: a fee taken by the token program, not by your
server. Mechanism: `TransferFeeConfig` at 500 bps with a max-fee cap, withdraw authority held by
the organizer. Test: the seller would otherwise keep 100% of the markup and the platform would
have to chase it, so yes. Watch: the fee is withheld on the recipient's account and needs an
explicit withdraw step. Source: the transfer-fee section of the same page.

**3. A credential that becomes transferable at a moment.** Property: a rule about time and
identity. Mechanism: `NonTransferable` for the pre-sale credential, then a re-issued transferable
mint at general sale, or `DefaultAccountState` frozen-until-unfrozen as an allowlist gate. Test:
partly chain-shaped (the gate), partly policy. Watch: `NonTransferable` is absolute; there is no
"transferable to X" (§6.3).

**4. A season pass with seat memberships.** Property: on-chain ownership with structure.
Mechanism: `TokenGroup` for the season and `GroupMemberPointer` per seat, so the relationship is
readable by any program, not just yours. Test: a third party building on your pass is what makes
this chain-shaped.

**5. A refundable deposit ticket.** Property: the deposit is the protocol's, not a company's
promise. Mechanism: the rent-exempt deposit is refundable on account close, so burn-and-close
after the event returns the capital (§4.4). Test: usually not chain-shaped on its own; it becomes
interesting when the refund must be provable to a stranger.

**6. Proof of attendance that cannot be transferred.** Property: uniqueness with no custodian.
Mechanism: `NonTransferable` mint, one per attendee, minted on check-in. Test: this is a
collectible; the chain-shaped part is that nobody can forge a second one.

**7. A claim window with a hard close.** Property: a rule about time that no one can extend by
asking. Mechanism: the `Clock` sysvar plus an expiry check in the mint or transfer path. Test:
yes, if the party you distrust is the one who would extend the window.

**8. An atomic ticket-for-token swap.** Property: settlement between strangers without a
custodian. Mechanism: a PDA escrow that holds the ticket and the payment and swaps both in one
instruction, or neither. Test: strongly chain-shaped, which is exactly why it is also the most
work (§6.5, candidate B).

**9. Compressed issuance for a large venue.** Property: scale at a cost a database cannot match
for *provable* uniqueness. Mechanism: a concurrent Merkle tree, one leaf per ticket, proofs
passed in, an indexer for reads. Test: the chain-shaped part is the root, not the ticket; the
read path is off chain. Source: `solana.com/docs/advanced/state-compression`.

**10. A price feed the pricing program can read.** Property: a number with a public provenance.
Mechanism: Pyth pull update in the same transaction, read with an age bound and a confidence
check (§8). Test: chain-shaped if the disputing party is the one who would claim a different
number.

**11. A checkout link that carries the transaction.** Property: composability. Mechanism: Solana
Actions and Blinks, where a URL returns a signable transaction, so any page can sell a ticket
with no backend of its own. Test: chain-shaped in the sense that the buyer's wallet is the
integration. Source: `solana.com/docs/tools/actions`.

**12. Payment and issuance in one transaction.** Property: atomicity. Mechanism: Solana Pay
request naming amount, recipient and a reference, with the mint in the same transaction so
payment and ticket cannot separate. Test: yes, and it is the cheapest genuinely-native thing on
this list. Source: `solana.com/docs/tools/solana-pay`.

**13. The ledger as the data product.** Property: a record nobody can edit. Mechanism: every
custody hop written to a program-owned record account, then read by an indexer into the pricing
engine, so the model's input is auditable by a third party. Test: this is the shape this
repository has already chosen for its backend, and its weak point is stated in §6.5: a record
with no forcing function is bypassable.

**Two things deliberately absent**, because they are the most common bad ideas in this space:

- **"Every ticket is an NFT" as an end in itself.** It is not chain-shaped. It is a database with
  extra steps and a wallet prompt. It becomes interesting only when a rule or a record is the
  point.
- **Sybil resistance.** One person with many wallets is untouched by anything in this file.
  `programs/cap_hook`'s README says sybil resistance is explicitly not claimed and no nullifier
  is built, and D6 records the same. If your idea depends on "one ticket per person", say how
  you know it is a person, or do not make the claim.

---

## 13. How to check anything in this file yourself

Everything here is one command away, and the commands are the point.

```sh
# is this cluster on the current protocol?  a certificate means yes, null means no
curl -s https://api.devnet.solana.com -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getAgGenesisCert"}'

# what does an account actually cost, today, on the cluster I am deploying to
curl -s https://api.devnet.solana.com -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getMinimumBalanceForRentExemption","params":[165]}'

# how fast is it actually going, right now
curl -s https://api.mainnet-beta.solana.com -X POST -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getRecentPerformanceSamples","params":[3]}'

# what did one transaction really cost, in a real block
#   getBlock with transactionDetails=full and maxSupportedTransactionVersion=1,
#   then read meta.fee and meta.computeUnitsConsumed per transaction

# the arithmetic in the cap check, with no cluster involved
cd programs/cap_hook && cargo test --release
```

For the client side: `simulateTransaction` returns logs and compute units consumed without
landing anything, which is the fastest way to answer "how much does my instruction cost" and
the only honest way to answer it. `getSignatureStatuses` only searches the recent status cache
unless you ask for history, so a missing signature is not proof of failure; check for blockhash
expiry and rebroadcast instead of polling forever.

---

## 14. Where this file is weaker than it looks

Stated rather than smoothed over, because the next person needs to know what to re-check.

1. **The rent rate is now documented, but only because I asked the cluster.** Both clusters
   charge 5,080 lamports per byte, and the rent sysvar account states it directly. The SDK
   constant is 6,960 and the staged-reduction proposal that contains 5,080 still says `Idea`, so
   the proposal is not the explanation. The cause stays an inference; the rate does not.
2. **The per-account compute ceiling is contested** between the docs (12M), `agave` master
   (24M) and a proposal (a share of the block limit). The advice in §10.1 survives all three;
   the number does not.
3. **The block table in §4.3 was wrong in its first draft and is now reproduced.** My first
   numbers were read from a real block but labelled with the wrong slot, and a reviewer caught
   it by re-running the same call. A finalised block is immutable, so a MEASURED row that does
   not reproduce is a fabrication whether or not the author meant it. The table as it stands was
   re-run twice, at the named slot and block height. The general lesson is worth more than the
   paragraph: **if a number is labelled measured, the command that produced it must produce it
   again.**
4. **Much of the DOCUMENTED trail was read as documentation source, not rendered pages.**
   `solana.com/docs` sits behind a bot checkpoint that refuses automated fetches from this host,
   so several figures were taken from the markdown that generates those pages, in
   `solana-foundation/solana-com`, with the rendered URL cited for the reader. That is a
   defensible source and it is not the same thing as loading the page, and the two can drift
   when a page is updated without its source, or the reverse.
5. **The hook-authority correction in §6.6 is documented in code, not in prose.** `SetAuthority`
   with `AuthorityType::TransferHookProgramId` exists in `token-2022` `processor.rs` and I read
   it. `docs/ON-CHAIN-DESIGN.md` §1.3 says the opposite in words.
6. **The confidential-transfer sentinel interaction is an inference.** `u64::MAX` is documented
   as the amount a hook receives on a confidential transfer; that `cap_hook` would therefore
   refuse one follows, but nothing tested it.
7. **Switchboard is thin here.** Its docs host did not resolve, so §8's Switchboard line rests on
   a repository README.
8. **The compressed-NFT costs are documented tables, not measurements.** Nobody in this
   repository has built a tree. The per-ticket account costs in §7.5 are measured arithmetic on a
   live rate, which is a different kind of claim.
9. **Anchors: I cite a version surface, not a version.** Anchor's crate moved repositories and its
   current line moved past 1.0 during 2026, with backports shipping days before this was written.
   Pin it and check crates.io rather than trusting any document, including this one.
10. **Two of the repository's own tests undersell what they prove, and one oversells it.** §4.6.
   The design document's §3.9 preconditions are not all implemented (§5.3), and the design
   document's §1.3 wording about hook immutability is too strong (§6.6). All three are findings
   about the repository, not about Solana, and none of them was edited into the files in question
   during this run.
11. **No ticket-market claim in this file is class A evidence.** Everything here is about
   mechanism. Where it touches pricing, it repeats what the programme already classified, and it
   adds nothing empirical about ticket prices.

---

## 15. Sources

Primary, and the ones I would read first if I were starting today.

**Solana core**
- Accounts and their structure: `solana.com/docs/core/accounts/account-structure`
- Account modification rules: `solana.com/docs/core/accounts/modification-rules`
- Constants reference: `solana.com/docs/core/constants-reference`
- Transactions and the size budget: `solana.com/docs/core/transactions/transaction-structure`
- Fees: `solana.com/docs/core/fees/fee-structure`, `solana.com/docs/core/fees/compute-budget`
- RPC: `solana.com/docs/rpc`, and the specific method pages named above
  (`getMinimumBalanceForRentExemption`, `getSignatureStatuses`, `getBlock`,
  `getRecentPerformanceSamples`, `simulateTransaction`)
- Clusters: `solana.com/docs/references/clusters`
- Terminology: `solana.com/docs/references/terminology`
- PDAs: `solana.com/docs/core/pda`; CPI: `solana.com/docs/core/cpi`
- Cookbook: `solana.com/developers/cookbook`

**What changed in 2026**
- Alpenglow: `solana.com/upgrades/alpenglow`
- Reduced slot times: `solana.com/upgrades/reduced-slot-times`
- 100M compute-unit blocks: `solana.com/upgrades/100m-cu-blocks`
- Larger transaction sizes: `solana.com/upgrades/larger-transaction-sizes`

**Source of the numbers, where the docs are silent or stale**
- `anza-xyz/solana-sdk`: `rent/src/lib.rs`, `clock/src/lib.rs`, `fee-structure/src/lib.rs`,
  `commitment-config/src/lib.rs`
- `anza-xyz/agave`: `program-runtime/src/execution_budget.rs`,
  `cost-model/src/block_cost_limits.rs`, `accounts-db/src/accounts.rs`
- `solana-foundation/solana-improvement-documents`: SIMD-0084 (rent collection disabled),
  SIMD-0194 (rent vocabulary), SIMD-0286 (block CU), SIMD-0306 (account CU),
  SIMD-0437 (staged rent reduction)

**Tokens and NFTs**
- Token-2022 and the extension list: `solana-program.com/docs/token-2022`,
  `solana-program.com/docs/token-2022/extensions`
- The extension enum: `docs.rs/spl-token-2022-interface`
- Transfer hooks: `github.com/solana-program/transfer-hook` (`interface/src/lib.rs`,
  `interface/src/instruction.rs`), and `token-2022/program/src/processor.rs` for the authority
  and the CPI behaviour
- Confidential transfer: `solana-program.com/docs/confidential-balances`
- State compression: `solana.com/docs/advanced/state-compression`
- Metaplex: `metaplex.com/docs/smart-contracts/core`, `.../token-metadata`, `.../bubblegum`
- zk compression (vendor): `zkcompression.com`

**Oracles**
- Pyth: `docs.pyth.network` (price feeds, core)
- Switchboard: `github.com/switchboard-xyz/on-demand` (its docs host did not resolve here)

**Hackathon framing**
- `records/findings/17-hackathon-rules-recheck.md` for the criteria as published, with the
  conflict between the two scoring regimes named rather than resolved

**In this repository**
- `programs/cap_hook/` (the program, its README, its four tests)
- `tools/devnet_publish.py` (the nine-step publish path and its refusals)
- `tools/solana_sign.py` (the one place a signature is produced)
- `docs/ON-CHAIN-DESIGN.md` §1.3, §3.9, §3.10
- `records/findings/21-onchain-hook-in-tree-and-publish.md` (what was measured, and what was not)

---

*Written for a stranger. No home paths, no process ids, no credentials. Nothing was committed and
nothing was pushed.*

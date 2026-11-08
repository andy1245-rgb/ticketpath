# 36: the transfer fee on a one-unit ticket

**Number.** Taking 36 because 33, 34 and 35 each already have one or more claimants in
`records/findings/` (`33-a-region-cap-law`, `33-b-region-cap-law-sources`, `34-region-caps-build`,
`35-live-llm-agents`, `38-region-caps-local-validator`, `39-visitor-identity`,
`40-memo-program-id`, `41-deepseek-live-adapter`), and 36 had no file or directory when this was
written.

**Written.** 2026-11-08T07:00Z. Local measurement only. No devnet transaction, no mainnet
transaction, no faucet, no push, no commit.

## 0. The answer, and where it disagrees with the brief

The premise under test was: *Token-2022 computes the transfer fee on the amount in base
units, so for `amount == 1` any fee below 10 000 bps withholds zero, and features 5 and 7 are
mechanically impossible on this mint.*

The first half is right about the base unit and wrong about the rounding. Token-2022 **ceils**
the fee, so:

> **MEASURED.** At `decimals = 0`, `amount = 1`, 500 bps and 1500 bps both withhold
> `withheldAmount = 1`, the entire ticket. The recipient receives 0. The fee is not zero.

So the brief's arithmetic is the wrong way round, but the brief's conclusion still holds, for
a different reason and with a consequence that has to be said out loud:

> **DERIVED.** On this mint the fee can only be 0 or 1 base unit, never a fraction. A 5% artist
> fee and a 15% flip tax are not expressible as percentages of an indivisible ticket. The
> mechanism can only take the whole ticket; the only ways to take nothing are `bps = 0` or
> `maximum_fee = 0`.

That is worse for the product than "withholds zero", not better: a demo that turns the fee on
does not quietly under-deliver a 5% cut, it transfers the ticket to the fee authority and
gives the buyer nothing.

## 1. What was run, and on what

- Tool: `tools/fee_experiment.py` (new file in this change). Tests:
  `tests/test_fee_experiment.py`.
- Cluster: a throw-away `solana-test-validator` started by the tool, Agave `4.3.2`, fresh
  ledger under `.swarm-runs/fee-experiment/`, payer funded at genesis with `--mint`, never the
  faucet, no `--url devnet`, no clone from any cluster. Token-2022 is present in the
  validator's own genesis at its canonical id (`TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb`,
  executable at slot 1).
- Short epochs (`--slots-per-epoch 32`) so a fee schedule that starts one or two epochs ahead
  becomes active inside the run; the tool waits for the schedule in force to equal the bps it
  is about to measure.
- Every transfer is a raw Token-2022 `TransferChecked` (instruction 12) built by the tool:
  the amount is in base units and **no fee is passed in**, so the number that comes back is
  the runtime's own arithmetic, not the client's.
- The withheld amount is read from `getAccountInfo` with
  `{"encoding": "jsonParsed", "commitment": "confirmed"}`, from the recipient token account's
  `transferFeeAmount` extension, before and after.
- The local validator was started and killed by the tool; the process is gone and its RPC port
  is closed (the run prints and checks that).

The validator command, with the ephemeral ports elided (the tool picks free ones so it does
not collide with anything already on the machine):

```
solana-test-validator --reset --quiet --ledger .swarm-runs/fee-experiment/ledger \
  --rpc-port <ephemeral> --faucet-port <ephemeral> --gossip-port <ephemeral> \
  --dynamic-port-range <ephemeral> \
  --mint <payer> --slots-per-epoch 32
```

The mint and transfer commands, as the run printed them:

```
spl-token --config .swarm-runs/fee-experiment/cli.yml --fee-payer <payer-key> --program-2022 \
  create-token --decimals 0 --transfer-fee-basis-points 500 --transfer-fee-maximum-fee 1000000 \
  .swarm-runs/fee-experiment/keys/mint-1.json
spl-token ... create-account --owner <recipient> <mint>
spl-token ... mint <mint> 3
```

The transfer itself is a hand-built instruction, so there is no CLI arithmetic in it:

```
TransferChecked: program TokenzQd…, data = [12] || u64_le(amount) || u8(decimals)
accounts = [source (w), mint, destination (w), authority (signer)]
```

The hook leg's other commands, as printed by the run (paths under `.swarm-runs/` are the
tool's own, git-ignored):

```
solana find-program-derived-address <hook> string:extra-account-metas pubkey:<mint>
solana find-program-derived-address <hook> string:record pubkey:<mint>
solana --url $RPC program deploy --use-rpc \
  --program-id .swarm-runs/…/keys/cap_hook-deploy.json \
  .swarm-runs/…/cap_hook.so --fee-payer .swarm-runs/…/keys/payer.json
```

The withdrawal is the TransferFee extension, sub-instruction 3:

```
WithdrawWithheldTokensFromAccounts: data = [26, 3, 1]
accounts = [mint, destination (w), authority (signer), source (w)]
```

## 2. The measurements

Each leg is a fresh mint, so the "before" is a real zero and not a leftover.

### Leg 1: 500 bps, `amount = 1`, decimals 0

Mint `8bvFoQCueCyaKfEVHYMb7EmdrgGmKyQQpxYmPxVNrBor`, supply 3, `maximum_fee = 1_000_000`,
withdraw authority set to the payer.

```
[1] transfer 1 of mint 8bvFoQCueCyaKfEVHYMb7EmdrgGmKyQQpxYmPxVNrBor (decimals 0, 500 bps, max 1000000)
  before: recipient amount=0 withheldAmount=0
  tx transfer 1: 21RoLUcEyHMyBBkQbyc1mWSxZ8YZMbbUJfJuaCsrK8heEjaqkNHtjbJfDk3tBQT9bxSwVZiP8yV6YwDhgssZkKaB slot=7 ok
  after:  recipient amount=0 withheldAmount=1
  arithmetic: ceil(1*500/10000)=1  floor(1*500/10000)=0
```

The RPC's own object for the recipient, after the transfer:

```json
"tokenAmount": {"amount": "0", "decimals": 0, "uiAmount": 0.0, "uiAmountString": "0"},
"extensions": [
  {"extension": "immutableOwner"},
  {"extension": "transferFeeAmount", "state": {"withheldAmount": 1}}
]
```

> **MEASURED.** 500 bps of a one-base-unit transfer withholds 1 base unit and credits the
> recipient 0. The ticket is in the fee account, not in the buyer's.

### Leg 2: 1500 bps, `amount = 1`, decimals 0

Mint `Hz8Z3S3KVqkvG8SVSN61q7jjYAFuAu1ZcNgSXFqGEUX7`.

```
[2] transfer 1 of mint Hz8Z3S3KVqkvG8SVSN61q7jjYAFuAu1ZcNgSXFqGEUX7 (decimals 0, 1500 bps, max 1000000)
  before: recipient amount=0 withheldAmount=0
  tx transfer 1: 22Lw28WcpUn3ovcZkptFcP8cwGtcDibYtjzVYwj1dxUfUM8EK31ZKvFDaAGcwLvhondzEAnZU1E9hevT7vTNkhDa slot=13 ok
  after:  recipient amount=0 withheldAmount=1
  arithmetic: ceil(1*1500/10000)=1  floor(1*1500/10000)=0
```

Recipient, after:

```json
"tokenAmount": {"amount": "0", "decimals": 0, …},
"extensions": [ …, {"extension": "transferFeeAmount", "state": {"withheldAmount": 1}} ]
```

> **MEASURED.** 1500 bps of a one-base-unit transfer withholds 1, the same as 500 bps. The
> rate changed; the withheld amount did not, because 1 is the ceiling of both.

### Leg 3: 1500 bps, `amount = 10`, decimals 0

Mint `67zx4NG2AZ7LGodDAtAjVa6jwWPXHs3myfzSD38KtsBj`. This is the leg that shows the fee is
real and that the amount is the only thing ruling it out.

```
[3] transfer 10 of mint 67zx4NG2AZ7LGodDAtAjVa6jwWPXHs3myfzSD38KtsBj (decimals 0, 1500 bps, max 1000000)
  before: recipient amount=0 withheldAmount=0
  tx transfer 10: C419QTjm5E6eoU7dXBuWZwTvUkf2KQhpnEHGSNe6dNjPVqjGhU7GaFxyXvFGXhtxvjp7xgitqvxA661SQPQS5r6 slot=19 ok
  after:  recipient amount=8 withheldAmount=2
  arithmetic: ceil(10*1500/10000)=2  floor(10*1500/10000)=1
```

Recipient, after:

```json
"tokenAmount": {"amount": "8", "decimals": 0, "uiAmount": 8.0, "uiAmountString": "8"},
"extensions": [ …, {"extension": "transferFeeAmount", "state": {"withheldAmount": 2}} ]
```

> **MEASURED.** `withheldAmount = 2`, not `floor(10 * 1500 / 10 000) = 1`. The instruction
> asked for exactly 10 with no fee, so 2 is the runtime's ceiling, not a client mistake.

### Leg 4: decimals 9, 1500 bps, `amount = 1_000_000_000`

Mint `37wECWVWvyC677F1UaDEjo5NZFuRu5QEgxvZ8Tt95Fyb`, `maximum_fee = 1_000_000_000` base units.

```
[4] transfer 1000000000 of mint 37wECWVWvyC677F1UaDEjo5NZFuRu5QEgxvZ8Tt95Fyb (decimals 9, 1500 bps, max 1000000000)
  before: recipient amount=0 withheldAmount=0
  tx transfer 1000000000: LuGbNgi4vp9pxfJHmy866K3UKefVQwFSP2BGDbjgihzcBR6AoLg8dYF5MGpjUiuKKjiTTPw9hqqw8cgprJfEATP slot=25 ok
  after:  recipient amount=850000000 withheldAmount=150000000
  arithmetic: ceil(1000000000*1500/10000)=150000000  floor(1000000000*1500/10000)=150000000
```

Recipient, after:

```json
"tokenAmount": {"amount": "850000000", "decimals": 9, "uiAmount": 0.85, "uiAmountString": "0.85"},
"extensions": [ …, {"extension": "transferFeeAmount", "state": {"withheldAmount": 150000000}} ]
```

> **MEASURED.** The same 1500 bps on 10⁹ base units withholds 150 000 000. The arithmetic
> scales with the base-unit amount, not with a price: there is no price anywhere in a
> `TransferChecked` for it to scale with.

### The arithmetic, from the source

`TransferFee::calculate_fee` in `spl-token-2022` divides with **ceiling** division and then
clamps:

```rust
let numerator = (pre_fee_amount as u128).checked_mul(transfer_fee_basis_points)?;
let raw_fee = Self::ceil_div(numerator, ONE_IN_BASIS_POINTS)?…;
Some(cmp::min(raw_fee, u64::from(self.maximum_fee)))
```

with `ceil_div(n, d) = (n + d - 1) / d` and `ONE_IN_BASIS_POINTS = 10_000`. The source read
here is `spl-token-2022-7.0.0/src/extension/transfer_fee/mod.rs` in the local cargo registry;
the four measurements above are the evidence that the validator's built-in program behaves
this way, and the source is the explanation.

> **DERIVED.** `fee = min(ceil(amount × bps / 10 000), maximum_fee)`. For `amount = 1` and
> `0 < bps ≤ 9 999`, `ceil(...) = 1`. The only two values a one-unit transfer can withhold are
> therefore **0** (`bps = 0`, or `maximum_fee = 0`) and **1** (`bps ≥ 1` and
> `maximum_fee ≥ 1`). There is no setting of `bps` or `maximum_fee` that yields anything in
> between.

## 3. The second half: a mint with a fee **and** the hook

Mint `6Ph2ztJbFKW42Kt3BYVgeih3x7AE3b1QPzrXQ4LEadCp`, decimals 0, 1500 bps,
`maximum_fee = 1_000_000`, `TransferHook` = the project's `cap_hook` at
`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, record staged at price 1 000 000 000.

The hook program deployed for this leg was the **existing built artifact**, copied and hashed
by the tool, not rebuilt: `cap_hook.so` sha256
`0b6174344329f1a60e079572fcb43bbc59250470a398c788a32a7e66a8fa16c7`. The source tree is being
edited by another run; this finding says nothing about that run's changes. The deployed
artifact accepted the **v2 record layout** (70-byte record), and the refusal log line below
shows the v2 fields (`band_low`, `jurisdiction`).

**[Corrected 2026-11-08T08:00Z: the `.so` this leg ran has been superseded, and the hash above is
kept as the artifact this measurement used.** The v2 program was rebuilt after
`records/findings/37-program-v2-review-fixes.md`: **111,504 bytes, sha256
`de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac`**, and the artefact now carries
proofs `a` to `g`. The v2 record layout this leg describes is unchanged (70 bytes, same field order),
so the leg's conclusion about the hook and the fee stands, but its refusal log line is from the
pre-fix build. Two of this finding's §5 alternatives were also corrected by an independent review;
the corrections are appended to `records/A-research-ledger.md` for 2026-11-08 and this file is not
rewritten.]**

### 3.1 Does a fee-bearing transfer still call the hook?

`TransferChecked amount = 10`, with the hook program account, the extra-account-metas PDA and
the record in the instruction:

```
tx transfer 10 (hook must refuse amount != 1): 5cePYPBiVr2FcsuCnZx481dT4TkZMB1Qno1jJivXuFhGhLzHpB3fkC4TgEYQbiLcVAYZtzDFaXz9hd16ghtcxBoF slot=50 FAILED ({'InstructionError': [0, {'Custom': 6008}]})
refused: err={'InstructionError': [0, {'Custom': 6008}]}
  log: Program 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva invoke [2]
  log: Program 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva consumed 1622 of 188350 compute units
  log: Program 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva failed: custom program error: 0x1778
after refusal: recipient amount=0 withheldAmount=0 (nothing moved)
```

> **MEASURED.** Yes: Token-2022 invokes the hook on the fee-bearing transfer, and the hook
> refuses `amount != 1` with 6008 (`0x1778`). The transaction is atomic, so nothing is
> withheld and nothing moves. On this mint the fee and the `amount == 1` rule cannot both be
> satisfied at once: `amount = 1` is the only admitted transfer, and at `amount = 1` the fee is
> the whole ticket.

### 3.2 The one-unit transfer on the hooked mint

```
tx transfer 1 (hook admits, fee withheld): 3xGw9RNCipcfoQrycTY2D5jZjFkKpp3enbcdRAUiqCHozxhwgnhMcpAuKkr2CWTypkaDTFuLUdXCHzn2GgjEuYn8 slot=52 ok
  log: Program log: ticketpath: cap admitted price=1000000000 face=1000000000 cap_bps=2500 band_low=0 jurisdiction=ON
after:  recipient amount=0 withheldAmount=1
```

> **MEASURED.** The hook admits the one-unit transfer and the mint still withholds 1. A
> "hooked mint with a fee" is therefore not a way out: the fee takes the ticket.

### 3.3 Does `WithdrawWithheldTokensFromAccounts` work with the hook present?

The staged price was cleared first (`SetPendingPrice 0`). If the withdraw path invoked the
hook, the hook would see a record with nothing staged and refuse with 6009. The withdraw was
sent with only the standard accounts: mint, destination, authority, source. No hook program
account, no extra-account-metas PDA, no record.

```
tx cap_hook clear staged price: kx453FdE54LNfiAz71ShuLeaLg2yAHmzZbi25qV6pufnc4MgmprgMbGDkmtPW433N4bYTjDiwz7LfAm8HtKDFCk slot=54 ok
tx WithdrawWithheldTokensFromAccounts: 25bz1Wtfs11oVYG9dGBe1ScHNYRrWHv53vNmy2Vf6sNus4UpCAaVn4e6jGc81swVXFRAirpLbeSti63jcYDfcJqt slot=56 ok
after:  recipient amount=0 withheldAmount=0
pool balance=1
```

> **MEASURED.** The withdrawal succeeds, moves the withheld unit to the destination token
> account, clears the source's `withheldAmount`, and does **not** invoke the hook: if it had,
> the cleared staged price would have produced 6009. It also does not need the hook's extra
> accounts.
>
> **DERIVED.** That matches the source: `process_withdraw_withheld_tokens_from_accounts` in
> `spl-token-2022`'s `extension/transfer_fee/processor.rs` contains no transfer-hook call.
> The instruction's account list is `[mint, destination, authority, …signers, …token
> accounts]`, so there is not even a slot to pass hook accounts in; anything appended would be
> read as another source token account.

**Consequence for the flip-tax rebate.** The plumbing a rebate would need (a withdraw
authority that is a PDA, a destination pool account, and a withdraw that works on a hooked
mint) all exists. What does not exist is a *partial* withholding: the pool can receive whole
tickets, never 15% of one. So "the flip tax, rebated on hold" as specified in
`records/findings/29-idea-portfolio.md` §5.4 is not buildable on this mint; an "escrow the
whole ticket, return it if held long enough" instrument is mechanically possible but is a
different product with a different sentence, and this run did not build or test it.

## 4. What this means for features 5 and 7

Feature 5 in `tmp/PLAN.md` (MD4) and §4.7 of the portfolio: *artist fee via
`TransferFeeConfig`, 500–1000 bps to the artist's wallet*.

- **MEASURED.** 500 bps on a one-unit transfer withholds the whole ticket. 1000 bps does the
  same (the ceiling of any rate in 1..9999 at amount 1 is 1).
- **DERIVED.** "The artist gets 5% of every resale, taken by the token program" cannot be
  implemented on a `decimals = 0` mint whose transfers are `amount = 1`. What can be
  implemented is "the artist's withdraw authority takes the entire ticket". That is not a fee;
  it is a seizure, and it leaves the buyer with 0 tokens for the price paid. The only fee
  values available are 0 (`bps = 0` or `maximum_fee = 0`) and 1 (take everything).
- **DERIVED.** The fee is a fraction of the token amount, not of the lamport price. Even if
  the ticket were divisible, 5% of the ticket is not 5% of the sale price unless a fractional
  ticket can be sold for its pro-rata value. For an admission ticket that is an assumption,
  not a fact, and this run did not test it.

Feature 7 (§5.4): *flip tax at 1500 bps to a rebate pool, rebated as a function of time
held*.

- **MEASURED.** 1500 bps on a one-unit transfer withholds the whole ticket; the hooked mint
  refuses the amount at which a partial fee would be possible (6008).
- **DERIVED.** "A resale one hour after purchase pays 15%, thirty days later close to nothing"
  cannot be implemented on this mint. The only rate the mint can express is 100% of the
  ticket. The held-time write path is present (the hook runs on the admitted transfer with
  the record passed writable, §3.2), so the *time* half of the mechanism exists; the field was
  not read back in this run, and the *fraction* half does not exist.

## 5. Alternatives that survive, and what each costs

None of these is recommended here. The choice is the operator's; the job of this section is
to say what the measurement leaves standing.

### 5.1 A lamport fee collected at the venue

**DERIVED (design), not measured.** The program's own transfer instruction already requires a
staged price. It can take a basis-point share of that price in lamports from the buyer and pay
the artist or the pool in the same transaction, because the buyer is already a signer. Exact
percentages are expressible; the fee is on the price, not the token amount.

Cost and limits: it binds only transfers that go through the program, so a direct
`spl-token transfer` on a marketplace that does not know about us bypasses it (the hook can
refuse, but then the ticket cannot move outside the venue at all: that is the cap behaviour,
not a fee). It needs the buyer's lamports in the same transaction and a decision about who
pays if the sale is in another currency. Not tested in this run.

### 5.2 A recorded fee obligation, settled off chain

**DERIVED (design), not measured.** The hook or the transfer instruction records the sale
price and the fee owed in a PDA (the record already carries the price and the hop count).
Collection happens at the venue's checkout or by invoice. Any bps of the actual price is
expressible, and the chain is the record rather than the collector.

Cost and limits: it is an attestation, not an enforcement; whoever settles can decline to pay,
and the chain cannot compel them. It is the cheapest on-chain option and the weakest
guarantee. It also does not follow the ticket to an unrelated marketplace any better than the
lamport fee does.

### 5.3 A divisible mint

**DERIVED (cost estimate), not measured.** Make the ticket, say, 1 000 000 base units at
`decimals = 6`, set the fee in bps, and change the hook's `amount == 1` to
`amount == TICKET_UNITS` so a partial transfer is still refused and a full ticket still moves
as one object. 500 bps of 1 000 000 is 50 000 units, 5% of the ticket, withheld without
rounding to the whole thing.

What it costs, and what it does not buy:

- Every consumer of `decimals = 0` changes: the hook's amount constant, the publish path, the
  console's token reading, the frontend type contract, the tests, and every document that
  says "one base unit is one ticket". That is a cross-cutting change, not a flag.
- Partial transfers become *possible at the token-program level*, so the hook's amount check
  becomes the only thing keeping the ticket indivisible. Today that check is also what stops a
  bulk dump; it would have to do both jobs.
- The withheld 5% is 5% of a **ticket**, not 5% of the **price**. To turn it into money the
  pool has to sell a fractional ticket, which is a product question (does the venue admit
  0.05 of a person?) and not a Token-2022 setting. This is the part the "just add decimals"
  answer usually skips.

**Estimate, not measured:** the on-chain change is small, the contract and documentation
change is large, and the economics still differ from "5% of the resale".

## 6. What remains unverified

- **The validator's embedded Token-2022 version.** The behaviour measured matches
  `spl-token-2022` 7.0.0's ceiling arithmetic, but the version of the program built into
  Agave 4.3.2 was not read off the cluster. If a future validator ships different arithmetic,
  the tool's assertion fails and says so; it is not silently assumed.
- **The `maximum_fee` clamp on chain.** Leg 3's maximum (1 000 000) is far above the fee, so
  the clamp was never exercised by a real transfer; the clamp arithmetic is tested only in
  `tests/test_fee_experiment.py`.
- **A rebate.** No rebate instruction was written. What was measured is that withheld tokens
  can be withdrawn to a pool account on a hooked mint. Whether a time-based rebate of whole
  tickets is a coherent product, and what a pool of whole tickets is worth, is not measured
  here.
- **The hook artifact.** The deployed `.so` is the pre-existing build identified by the
  sha256 above, not a build of the current source tree (another run is editing it). The
  finding's hook claims are about that artifact.
- **Divisible-mint costs.** §5.3's costs are an estimate from reading the tree, not a
  measurement.

## 7. Reproduction

```
export PATH="$HOME/.local/share/solana/install/active_release/bin:$HOME/.cargo/bin:$PATH"
python3 tools/fee_experiment.py
python3 -m unittest tests.test_fee_experiment -v
```

The tool writes `measurements.json`, the validator log and the ledger under
`.swarm-runs/fee-experiment/` (git-ignored), generates its keys there at mode 0600, never
prints key material, refuses any non-loopback RPC URL, kills the validator on every exit path
and checks that the process is gone and the port is closed. `python3 -m unittest discover -s
tests -t .` ran 968 tests with 19 skips and no failures on the tree as it stood when this was
written.

Measured output, the four legs in the tool's own summary:

```
[1] decimals=0 bps=500 amount=1 -> withheldAmount=1 (recipient 0; ceiling 1, floor 0)
[2] decimals=0 bps=1500 amount=1 -> withheldAmount=1 (recipient 0; ceiling 1, floor 0)
[3] decimals=0 bps=1500 amount=10 -> withheldAmount=2 (recipient 8; ceiling 2, floor 1)
[4] decimals=9 bps=1500 amount=1000000000 -> withheldAmount=150000000 (recipient 850000000; ceiling 150000000, floor 150000000)
```

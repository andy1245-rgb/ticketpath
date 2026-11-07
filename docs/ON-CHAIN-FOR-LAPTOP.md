# On-chain program: what it must do, and how to build it on a laptop

**Status: DESIGN-NOT-DEPLOYED. Nothing in this document has been compiled, deployed or
run.** This machine has no `solana`, `anchor`, `cargo` or `rustc`, so no build or deploy
was attempted here, and no toolchain was installed. Every section below is a
specification for the operator's laptop, which has Agave and `spl-token`.

What is real today: the backend on port 8788, computed from a labelled synthetic
store. What is not: the program described here, any mint, any transaction signature,
and therefore every `signature`/`slot` in any response (`records/CONTRACT-MAP.md` §5.1).

---

## 1. What the program must do

The product claim is that a resale on this platform is a *recorded* transaction, not an
asking price. That claim is only true if the program is what moves the ticket. Four
responsibilities, in order of importance:

1. **Own the custody hop.** A ticket moves only through an instruction this program
   processes, so every hop is a transaction that exists. No hop, no record.
2. **Enforce the resale cap at the moment of sale.** `face + face × cap_bps / 10 000`
   is a hard ceiling the program checks. A sale above it must fail, not be flagged
   afterwards.
3. **Enforce the verified-wallet gate.** The destination of a resale must be a wallet
   the program's verification registry has admitted, and the transfer hook is what
   refuses any other destination.
4. **Write the record.** A `ResaleRecord` account and a program log event per sale, so
   the backend can reconstruct price, time and custody path without trusting a client.

Non-responsibilities: the program does not price anything, does not know what a ticket
is worth, and does not hold money for the organizer. Pricing is the engine's job; the
program is the constraint system and the ledger.

## 2. Program shape: transfer hook plus escrow, not one or the other

Two mechanisms are available, and this design uses both because they cover different
holes:

- **Token-2022 transfer hook** (`spl-transfer-hook-interface`). The mint carries the
  `TransferHook` extension pointing at our program. Every transfer of the token invokes
  our `Execute` instruction, which may reject it. This is the only way to make a rule
  true for transfers the platform never sees.
- **Program-owned escrow token account (PDA).** A resale is: seller moves the ticket
  into escrow, buyer pays, program moves the ticket out and records the sale. This is
  the only way to see a *price*: the token program transfers an amount of tokens, not
  lamports, so the hook cannot observe what was paid.

Stated plainly: **the hook enforces "no transfer except to a verified wallet and only
through escrow"; the sale instruction enforces the price cap.** Any design that claims
the hook checks price is wrong about how Token-2022 hooks work.

## 3. Account layout (DESIGN-NOT-DEPLOYED)

Sizes are given as field widths. Do not take a rent figure from this document: query it
on the laptop with `solana rent <bytes>` once the real struct sizes are known, because
the rent-exempt minimum is a cluster parameter and was not measured here.

### 3.1 `Config` — one PDA per program

seeds: `["config"]`, program-owned.

| Field | Type | Purpose |
|---|---|---|
| `authority` | `Pubkey` | may register identities and verify wallets; a multisig in production |
| `verifier` | `Pubkey` | the key allowed to write verification records (may equal authority) |
| `hook_program_id` | `Pubkey` | sanity check against the mint's extension |
| `paused` | `bool` | global kill switch for new sales |
| `bump` | `u8` | PDA bump |

### 3.2 `Event` — one PDA per event

seeds: `["event", event_id_16_bytes]`.

| Field | Type | Purpose |
|---|---|---|
| `event_id` | `[u8; 16]` | stable id, matches the backend's `Event.id` |
| `organizer` | `Pubkey` | receives primary proceeds |
| `face_value_lamports` | `u64` | per-tier face lives on the tier account; this is the floor for the event |
| `resale_cap_bps` | `u16` | 0..=10 000 typical; `u16` allows "uncapped" sentinel `0xFFFF` |
| `requires_verified_wallet` | `bool` | mirrors the contract's flag, and is what the hook reads |
| `resale_enabled` | `bool` | |
| `starts_at` | `i64` | unix seconds; the cap may be time-varying later |
| `ticket_count` | `u32` | monotonically incremented by `mint_ticket` |
| `bump` | `u8` | |

### 3.3 `Tier` — one PDA per (event, tier)

seeds: `["tier", event_pda, tier_id_8_bytes]`.

| Field | Type | Purpose |
|---|---|---|
| `face_value_lamports` | `u64` | **the denominator for every markup on this ticket** |
| `total_supply` | `u32` | |
| `issued_count` | `u32` | |
| `max_per_wallet` | `u16` | anti-sybil holding cap, enforced at mint and at transfer |

### 3.4 `Ticket` — one PDA per ticket

seeds: `["ticket", mint_pubkey]`.

| Field | Type | Purpose |
|---|---|---|
| `mint` | `Pubkey` | the Token-2022 mint |
| `event` | `Pubkey` | |
| `tier` | `Pubkey` | |
| `serial` | `[u8; 8]` | human-facing, rendered by the backend |
| `issued_to` | `Pubkey` | original issuee, the contract's `issuedToWallet` |
| `current_owner` | `Pubkey` | mirrored from the token account; the contract's `ownerWallet` |
| `status` | `u8` | 0 valid, 1 listed, 2 redeemed, 3 revoked |
| `custody_seq` | `u32` | increments on every hop; the ledger's ordering key |
| `issued_at` | `i64` | |
| `redeemed_at` | `i64` | 0 = never |
| `bump` | `u8` | |

### 3.5 `Listing` (escrow) — one PDA per active listing

seeds: `["listing", ticket_pda]`.

| Field | Type | Purpose |
|---|---|---|
| `ticket` | `Pubkey` | |
| `seller` | `Pubkey` | |
| `price_lamports` | `u64` | must satisfy the cap at list time *and* at execute time |
| `escrow_token_account` | `Pubkey` | PDA-owned token account holding the ticket |
| `created_at` | `i64` | |
| `expires_at` | `i64` | an expired listing can be cancelled, not executed |
| `bump` | `u8` | |

### 3.6 `ResaleRecord` — one PDA per sale

seeds: `["resale", ticket_pda, custody_seq_le_bytes]`.

| Field | Type | Purpose |
|---|---|---|
| `ticket` | `Pubkey` | |
| `seq` | `u32` | matches `Ticket.custody_seq` |
| `seller` | `Pubkey` | |
| `buyer` | `Pubkey` | |
| `price_lamports` | `u64` | |
| `markup_bps` | `i32` | computed on-chain from this ticket's tier face, so the ledger cannot disagree with itself |
| `occurred_at` | `i64` | |
| `kind` | `u8` | 0 sale, 1 gift/transfer, 2 redeem, 3 revoke |

The backend reads these with `getProgramAccounts` filtered by the ticket PDA and maps
each to a contract `LedgerEntry`, using the transaction signature for `signature` and
the slot for `slot`. That is the transition from §5.1 of `records/CONTRACT-MAP.md` to a
real custody trail.

### 3.7 `Verification` — one PDA per wallet

seeds: `["verified", wallet]`.

| Field | Type | Purpose |
|---|---|---|
| `wallet` | `Pubkey` | |
| `verified_at` | `i64` | |
| `method` | `u8` | 0 wallet-signature only, 1 identity-backed |
| `nullifier` | `[u8; 32]` | commitment to the attendee identity; zero if none |
| `revoked` | `bool` | |

### 3.8 `Nullifier` — one PDA per identity commitment

seeds: `["nullifier", nullifier_32_bytes]`.

| Field | Type | Purpose |
|---|---|---|
| `wallet` | `Pubkey` | the only wallet allowed to use this identity |
| `event_scope` | `Pubkey` or zero | zero for a platform-wide identity |
| `bump` | `u8` | |

The existence of this account is the anti-sybil constraint: a second wallet trying to
register the same commitment fails because the PDA already exists.

### 3.9 Mint account

Token-2022 mint with extensions, one per ticket:

| Extension | Purpose |
|---|---|
| `TransferHook` | points at this program; every transfer calls `Execute` |
| `MetadataPointer` + token metadata | name, symbol, and the event/tier/serial as attributes |
| `NonTransferable` — **not used** | resale must be allowed; this extension would forbid it |

Supply is 1, decimals 0. `MintAuthority` is the `Event` PDA; `FreezeAuthority` is
renounced or the program PDA, so no key can freeze a ticket.

## 4. Instruction set (DESIGN-NOT-DEPLOYED)

| Instruction | Signers | Checks | Writes |
|---|---|---|---|
| `initialize_config(authority, verifier, hook_program_id)` | authority | called once; `hook_program_id` == this program | `Config` |
| `create_event(event_id, cap_bps, requires_verified_wallet, starts_at)` | organizer | `cap_bps <= 10 000` or the uncapped sentinel; `event_id` unused | `Event` |
| `create_tier(event, tier_id, face_lamports, supply, max_per_wallet)` | organizer | `face_lamports > 0`; `max_per_wallet >= 1`; supply not exceeded | `Tier` |
| `mint_ticket(event, tier, serial, to)` | organizer | tier not sold out; `to` verified if the event requires it; `to` holds < `max_per_wallet` for this tier | mint, `Ticket` |
| `verify_wallet(wallet, method, nullifier)` | verifier | if `nullifier != 0`: its PDA must not already exist | `Verification`, `Nullifier` |
| `revoke_verification(wallet)` | verifier | | `Verification.revoked = true` |
| `list_for_resale(ticket, price_lamports)` | current owner | `resale_enabled`; ticket `valid`; **price within cap**; one active listing per ticket | `Listing`, escrow token account, ticket → `listed` |
| `execute_resale(ticket)` | buyer | listing not expired; **price within cap, re-checked**; buyer verified if required; buyer's holding cap; payment transfers to seller net of fee | token moves escrow → buyer, `ResaleRecord`, `Ticket.owner = buyer`, `custody_seq += 1`, `Listing` closed |
| `cancel_listing(ticket)` | seller | | token returns to seller, `Listing` closed, ticket → `valid` |
| `redeem_ticket(ticket)` | current owner or organizer | ticket `valid`; event started (cluster time) | `Ticket.status = redeemed`, `ResaleRecord(kind = redeem)` |
| `revoke_ticket(ticket, reason)` | organizer | organizer of that event | status `revoked`, `ResaleRecord(kind = revoke)` |
| `set_cap(event, cap_bps, effective_at)` | organizer | new cap applies to listings created/executed after `effective_at` | `Event` |
| `close_event(event)` | organizer | after `ends_at` | nothing moved; blocks new mints |
| `execute(hook_context)` — Token-2022 `Execute` | token program | see §5 | nothing; returns success or an error |

`execute_resale` must transfer lamports and tokens atomically in one instruction: if the
payment fails, the ticket must not move. If a marketplace fee is introduced later, it
splits the lamports before the seller's share is paid, and the fee rate lives on
`Config` so it cannot be changed per ticket.

## 5. What the transfer hook checks at resale

The hook runs on **every** transfer of the token, including ones no frontend initiated.
It receives: source token account, mint, destination token account, the authority on the
transfer, the amount, and any accounts listed in the mint's `ExtraAccountMetaList` PDA
(seeds `["extra-account-metas", mint]`). It must check, in this order:

1. **The mint belongs to a configured event.** Read the `Ticket` PDA from the extra
   accounts; refuse if it does not match the mint or the event is closed.
2. **The destination is allowed.** If `Event.requires_verified_wallet`, the destination
   owner must have a live, non-revoked `Verification` PDA. This is the gate that makes
   `WalletVerification.canReceiveTransfer` true or false on the wire.
3. **The transfer is either minting or escrow-routed.** Refuse any transfer whose
   destination is not (a) the escrow token account of an active `Listing` for this
   ticket, or (b) the buyer of an `execute_resale` currently being processed. Everything
   else is a bypass attempt, because a bypass is exactly a sale the platform never sees.
4. **The holding cap.** If the destination already holds `max_per_wallet` tickets for
   this tier, refuse. This is the per-event anti-sybil bound the API cannot enforce.
5. **Tickets are not fungible in spirit.** `amount == 1` and decimals `0`; a
   multi-token transfer is not a ticket transfer.

The hook **cannot** check price, because it never sees lamports. The cap is checked in
`list_for_resale` and again in `execute_resale`, both against the same `Event` fields.
The second check is the one that matters: a listing created under an older, higher cap
must still fail if the cap was lowered in between.

## 6. Why the cap and the anti-sybil constraint live on-chain

An API check is a check the caller can decline to make. The backend on 8788 answers
questions; it does not sit between a wallet and the token program, and no client is
obliged to talk to it. Concretely:

- **A cap in the API caps only well-behaved clients.** A seller can sign a transfer
  directly. Then the ledger shows a sale above the cap, and the platform's central claim
  (the record is the market) becomes a record of violations it could not prevent. The
  only place a ceiling is a ceiling is the instruction that moves the token.
- **The record has to be trustless to be worth collecting.** A price written by the
  backend is a claim; a price in a `ResaleRecord` PDA plus a transaction signature is
  evidence. If the constraint were off-chain, the ledger would be worth less than the
  market it describes, and there would be no reason for an organizer to believe it.
- **Anti-sybil is a global invariant.** "One verified attendee identity per ticket
  allocation" spans wallets, events and time. The API can be asked to enforce it and can
  be bypassed by anyone who skips the API; a PDA that already exists cannot be created
  twice. That is the difference between a policy and an invariant.
- **The gate must fire atomically with the transfer.** Verified-wallet enforcement that
  is checked before the transaction lands is a race. In the hook, the refusal and the
  transfer are the same instruction: either both happen or neither does.
- **Conceding the honest limit.** The identity behind a nullifier is proven off-chain
  (whatever document or credential the organizer accepts) and only its commitment goes
  on-chain. The program can guarantee "this commitment was registered once", not "this
  person is who they say". That gap is real and should be described as such in the
  submission rather than papered over.

## 7. Steps on the laptop (Agave + spl-token)

Run these in a fresh directory outside this repository. Each step is verifiable before
the next one runs. Nothing here was executed on the build machine.

### Step 0 — confirm the toolchain (do not install anything you already have)

```bash
solana --version
cargo build-sbf --version
spl-token --version
solana config get
```

If `cargo build-sbf` is missing, the Agave install is incomplete; install Agave's SBF
toolchain from the official Agave release, not a random blog's script. Do not proceed
until all three print a version.

### Step 1 — a devnet key and some SOL

```bash
solana config set --url devnet
solana-keygen new --outfile ~/.config/solana/ticketpath-deployer.json
solana address
solana airdrop 2
solana balance
```

If `airdrop` is rate-limited, use the web faucet for that address. Deploy cost and
rent are cluster parameters: check them with `solana rent <bytes>` and
`solana program deploy --help` rather than trusting a number in a document.

### Step 2 — scaffold and build the program

```bash
cargo new --lib ticketpath_onchain
cd ticketpath_onchain
# Cargo.toml: solana-program, spl-token-2022, spl-transfer-hook-interface,
#             spl-associated-token-account, borsh
cargo build-sbf
```

Anchor is optional. If it is present, `anchor init` and `anchor build` are fine; the
account layout and instruction set above are what matters, not the framework. A plain
`solana-program` crate compiles on a laptop that has Agave and no Anchor, which is the
safer assumption.

### Step 3 — deploy

```bash
solana program deploy target/deploy/ticketpath_onchain.so \
  --program-id target/deploy/ticketpath_onchain-keypair.json
solana program show <PROGRAM_ID>
```

`DESIGN-NOT-DEPLOYED`: no program id exists yet. Do not write a placeholder into the
backend's environment and call it deployed; `/health` reads
`TICKETPATH_PROGRAM_ID` and still reports `programDeployed: false` until the adapter
has a real check.

### Step 4 — create the Token-2022 mint with the hook extension

```bash
spl-token create-token \
  --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb \
  --transfer-hook <PROGRAM_ID>
```

Confirm the flags against `spl-token create-token --help` on the installed version
before running: the *extension set* is the requirement (TransferHook + MetadataPointer,
decimals 0, supply 1), and CLI flag spelling has changed between releases. Then create
the associated token account and mint exactly one:

```bash
spl-token create-account <MINT> --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb
spl-token mint <MINT> 1
spl-token display <MINT>
```

`display` must show the TransferHook extension pointing at `<PROGRAM_ID>`, and the
`ExtraAccountMetaList` PDA must exist for that mint before any transfer will succeed.

### Step 5 — the negative tests, before any demo

These are the tests that decide whether the on-chain claim is true. Run each and record
the result:

1. Transfer the ticket from the verified holder to an unverified wallet, directly.
   **Expect failure** with the hook's "destination not verified" error.
2. `list_for_resale` above `face + face × cap_bps / 10 000`. **Expect failure.**
3. Lower the cap with `set_cap`, then `execute_resale` on a listing created under the old
   cap. **Expect failure** on the re-check.
4. `execute_resale` at or below the cap to a verified buyer. **Expect success**, and a
   `ResaleRecord` PDA for the new `custody_seq`.
5. Register a second wallet with a nullifier already used. **Expect failure** on the
   existing-Nullifier PDA.
6. `revoke_verification` a buyer, then try to receive. **Expect failure.**

If any of 1–3 or 5 succeeds, the invariant is not enforced and the submission must not
claim it is.

### Step 6 — point the backend at it (only after 1–6 pass)

```bash
export TICKETPATH_CLUSTER=devnet
export TICKETPATH_PROGRAM_ID=<PROGRAM_ID>
export TICKETPATH_RPC_ENABLED=1
```

Deploying the program does **not** by itself make `Ticket.transferRestricted` true or
populate `signature`/`slot`. Two pieces of code must also change:

- `ticketpath/adapters/rpc_adapter.py` needs a real read: fetch the mint account,
  deserialize the extensions, confirm the TransferHook program id equals
  `TICKETPATH_PROGRAM_ID`, and return `enforced: true` only then.
- `ticketpath/adapters/ledger_adapter.py` needs a chain reader: `getProgramAccounts` for
  `ResaleRecord` PDAs by ticket, mapped to `LedgerEntry` with the transaction signature
  and slot.

Until both exist, the honest values are `transferRestricted: false` and null
provenance, which is what the backend returns today.

## 8. What is design-only, in one list

| Item | State |
|---|---|
| Program source, build, tests | DESIGN-NOT-DEPLOYED |
| Program id, mint address, any transaction signature or slot | Does not exist |
| Account layouts and instruction set above | DESIGN-NOT-DEPLOYED |
| Transfer-hook checks | DESIGN-NOT-DEPLOYED |
| Cap enforcement and nullifier uniqueness | DESIGN-NOT-DEPLOYED |
| Steps 0–6 | Not executed here; untested by this build |
| Backend contract endpoints, tests, fixture computation | Built and tested on this machine |
| Wallet signature verification (Ed25519, RFC 8032) | Real, tested, no chain required |

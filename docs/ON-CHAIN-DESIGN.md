# Ticketpath: the minimum on-chain surface

**Status:** a design document that the deployed programs partly implement. The cap program is deployed
on devnet (`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, and v2 `Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF`);
sections not marked built are design. No address in this document is invented. **Written:** 2026-11-07. **Scope:** the on-chain anti-fraud
invariant, the accounts and instructions that carry it, the threat model, and the runbook the
operator runs on a machine that has Agave.

**[Status corrected 2026-11-08T07:45Z: "No program is deployed" is false of the project. A program is
deployed on devnet at `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva` and proven there, and a second
program has run on a local validator; §0 is what the source implements and the block below lists what
stayed design. The sentence is kept because it was the status when the document was written.]**

> **[CORRECTED 2026-11-08T03:45Z. The first sentence above is now true of this document and false
> of the project, so read it with this block. `programs/cap_hook/` implements §1.3, §3.9 and §3.10's
> cap check as a native Rust transfer hook, and it is deployed on devnet at
> `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, with a Token-2022 mint at
> `6RPS73X519CRCdyR7diqvcjBACEVdB2cADKewCXYnimV` carrying the hook, a metadata pointer and token
> metadata. At face 1.0 SOL and cap 2,500 bps a transfer at 1,250,000,000 lamports landed and one at
> 1,250,000,001 was refused by the cluster with `6010`, both legs carrying their own signature and
> block time; the whole record is `records/devnet-artefacts.json`, re-read from the cluster on
> 2026-11-08. What stays design-only is everything else in §2 and §3: `EventPolicy`, `TierPolicy`,
> `HopRecord`, the destination check, the verified-wallet gate, `redeem` and `revoke`.
> `programs/cap_hook/README.md` is the authoritative list of what the deployed program does not do,
> and it is shorter than §3 reads. §6's steps 0 to 3 are corrected below to the paths and commands
> the tooling in this repository actually uses. §10 is left exactly as written: it is the record of
> what could not be checked from this machine on 2026-11-07, and three of its rows — the toolchain,
> the deploy and the boundary pair — were settled afterwards by `records/findings/18`,
> `records/findings/21` and the devnet artefact. Read §10 as a dated list, not as the current
> boundary.]**

**Evidence discipline used throughout this file.** Every statement is one of four kinds, and
the kind is visible in the sentence:

| tag | meaning |
|---|---|
| **measured here** | run from this machine, command shown, result quoted |
| **design** | a decision in this document; nothing to run yet |
| **SIMULATED** | produced by the Python mirror in §9 on this machine; says nothing about any cluster |
| **UNVERIFIED-FROM-THIS-MACHINE** | cannot be checked without Agave, Rust, or a deployed program. §10 lists all of them |

**What was actually measured from here**, so the reader knows where the floor is:

| check | command | result |
|---|---|---|
| no toolchain | `which solana anchor cargo rustc spl-token` | nothing, exit 1. `~/.local/share/solana` and `~/.config/solana` do not exist |
| devnet is up | `getVersion` | `{"solana-core":"4.4.0"}`, `getEpochInfo` slot 519,638,900 |
| Token-2022 program exists on devnet | `getAccountInfo TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb` | `executable=true`, owner `BPFLoaderUpgradeab1e...` |
| the ATA program exists | `getAccountInfo ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL` | `executable=true` |
| the Ed25519 precompile exists | `getAccountInfo Ed25519SigVerify111111111111111111111111111` | `executable=true`, owner `NativeLoader...` |
| rent rate right now | `getMinimumBalanceForRentExemption(size)` at sizes 0, 82, 92, 125, 130, 151, 165, 230, 234, 250, 259, 300, 400, 1000 | exactly `(len + 128) * 5080` at every size. A 165-byte account is 1,488,440 lamports |

That last row is the one economic number in this document that is not an assumption. The
prior corpus recorded the same `(len + 128) * 5080` on a different host; it is re-measured
here at slot 519,638,900 and agrees.

Two things this programme's corpus established, relied on below with their provenance stated
because it is weaker than it looks: `records/00-prior-direction-index.md` §3 to §5 records six
Token-2022 mechanism facts as *source reading*, and records that an earlier document in the
corpus claimed a verified devnet spike whose mints and signatures now return `null` and whose
local ledger is gone. So no mechanism fact below is presented as having been executed. Where a
behaviour is only asserted by that reading, it is marked **UNVERIFIED-FROM-THIS-MACHINE** and
§6 gives the command that would settle it.

---

## 0. Implemented today, and where the design stops

**Written 2026-11-08. This section is a claim about the code, not about the design.** It reads
`programs/cap_hook/src/` and states what that source actually has. `tools/doc_check.py` check 4
compares the table below with the source both ways, so an error number, an instruction tag or a seed
literal that the program has and the table lacks is a failing check, and so is a row the program no
longer has. Section 1 onward is the design; where a design sentence and this table disagree, the
table is the truth about the tree and the design sentence is a statement about intent.

**Two programs, two clusters, and they are not interchangeable.** v1 is deployed on devnet at
`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva` and is frozen evidence: no upgrade, no re-sign, no
edit (D13). v2 is a different program id, `CTEnej2b5cgJ7uQ185k7yWZChe8GasAgPYCc4BHFB67w`.
**Corrected 2026-11-08T09:30Z:** that id is the one a local `solana-test-validator` proved, and
`records/onchain-v2.local.json` is still its record and still git-ignored. v2 has now also been
deployed **on devnet**, under a third program id of its own, `Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF`
(abbreviated `Bebo55oe…` elsewhere in this tree; the full value is in `records/onchain-v2-devnet.json`).
That deploy recorded 35 transaction rows across its two phases (34 distinct: the deploy is shared) and observed 14 refusals, and its record is the tracked file
`records/onchain-v2-devnet.json`, written by `tools/publish_v2_devnet.py` — which imports this
project's local publisher and overrides only its validator lifecycle, so the assertions are the
reviewed ones. The earlier sentence here, that v2 "has only ever run on a local
`solana-test-validator`", was true when it was written and is false now; it is kept in the record
rather than deleted. v1 remains untouched: same program id, same 85,784-byte program data, last
deployed in slot 519806063, which is not a slot any v2 run has used. The source implements the v2
instruction set: seven tags where v1 had four, the floor and the jurisdiction and policy bytes, and
the hold clock. A devnet reader of v1's program id is reading v1's deployed bytes, which do not
have tags 4 to 6.

| kind | name | value | where |
|---|---|---|---|
| error | `AmountNotOne` | 6008 | `execute`, `amount != 1`; a hook is handed a transfer amount and no price |
| error | `TransferNotStaged` | 6009 | `execute`, `pending_price_lamports == 0`: there is no price to police |
| error | `CapExceeded` | 6010 | `execute`, staged price above `face * (10_000 + cap_bps) / 10_000`, `policy == 0` only |
| error | `TicketNotValid` | 6013 | `execute`, `status != 1` |
| error | `WrongExtraAccount` | 6020 | any instruction handed a PDA that is not the one it derives; the design spells the same predicate `E_NOT_A_TICKET` |
| error | `BelowFloor` | 6021 | `execute`, `band_low_lamports > 0` and the staged price below it, `policy == 0` only |
| error | `BandUnsatisfiable` | 6022 | `InitializeRecord` with a floor above the ceiling; `PublishBand` and `LogForecast` with `low > high` |
| error | `PolicyInvalid` | 6023 | `InitializeRecord`, `policy` neither 0 (capped) nor 1 (monitored) |
| error | `ForecastExists` | 6024 | `LogForecast`, the `["forecast", mint, as_of_unix]` account already exists. Immutability, not a race |
| error | `AlreadyScored` | 6025 | `ScoreForecast`, the `["score", forecast]` account already exists |
| error | `NotAuthority` | 6026 | a signer that is not the key the write requires: tags 2, 3, 4 and 5 need the record's `authority`, tag 1 needs the **mint's authority**, and tag 6 needs the **forecast's `authority`** |
| error | `RebateNotDue` | 6027 | declared for `ClaimRebate`, and **no instruction raises it**: tag 7 is not implemented, because feature 7 is blocked (`records/findings/36-transfer-fee-on-a-one-unit-ticket.md`) |
| error | `RebateUnavailable` | 6028 | declared for `ClaimRebate`, and **no instruction raises it**, for the same reason |
| error | `ForecastBackdated` | 6029 | `LogForecast`, `as_of_unix` earlier than the clock minus `FORECAST_BACKDATE_TOLERANCE_SECONDS` (300 s). A forecast dated in the future is allowed: that is a pre-registration, not a backdated claim |
| error | `ScoreBelowWidth` | 6030 | `ScoreForecast`, `interval_score_micro` below `(high - low) * 1_000_000`, which no honest score can be, since the width term is the score's floor |
| error | `BandTooWide` | 6031 | **`LogForecast` only**: a forecast wider than `MAX_BAND_WIDTH_LAMPORTS`, whose width term could not be stored in the `u64` score field. `PublishBand` does not refuse it, because a band is never scored |
| error | `BandEmpty` | 6032 | `PublishBand` with `sample_n == 0` and `refused == 0`: a band resting on no observations that is not itself a refusal |
| error | `AsOfAhead` | 6033 | `PublishBand` with `as_of_slot` above the slot the write lands in: an estimate dated from the future |
| instruction | `InitializeExtraAccountMetaList` | 0 | signed by the payer; **no argument, the record is derived from the mint**; creates `["extra-account-metas", mint]`, idempotent, and never rewrites a v1 list |
| instruction | `InitializeRecord` | 1 | signed by the **mint's authority**, which becomes the record's `authority` (`6026` on any other key); the payer pays rent; creates `["record", mint]` with face, cap_bps, band_low, jurisdiction, policy. A second call on an existing record is a **no-op whatever the signer**: the emptiness check returns `Ok(())` before the signer is examined |
| instruction | `SetPendingPrice` | 2 | signed by the record's `authority` (`6026` on anyone else); writes `pending_price_lamports`, and is a staging scaffold rather than a listing (`programs/cap_hook/README.md`) |
| instruction | `SetStatus` | 3 | signed by the record's `authority`, for the same reason; writes `status` |
| instruction | `PublishBand` | 4 | signed by the record's `authority` (`6026`); creates or rewrites `["band", mint]`, which is rewritable on purpose (D14); refuses `6022`, `6032` and `6033` only, because a band is never scored |
| instruction | `LogForecast` | 5 | signed by the record's `authority` (`6026`); creates `["forecast", mint, as_of_unix]` once, refusing a second write `6024`, a backdated instant `6029` and an unstorable width `6031` |
| instruction | `ScoreForecast` | 6 | signed by the **forecast's `authority`** (`6026`), the key that logged it; accounts are `[scorer (signer), forecast, score (writable), system program]` and **no record account is passed**; creates `["score", forecast]` once (`6025`), refuses a score below the band's width `6030`, and writes nothing into the forecast |
| seed | `record_seeds` | record | `["record", mint]`, the per-mint record PDA |
| seed | `extra_metas_seeds` | extra-account-metas | `["extra-account-metas", mint]`, fixed by the SPL interface |
| seed | `band_seeds` | band | `["band", mint]`, the public feed's head |
| seed | `forecast_seeds` | forecast | `["forecast", mint, as_of_unix_le]`, one forecast per mint and instant |
| seed | `score_seeds` | score | `["score", forecast]`, one score per forecast |
| seed | `fee_authority_seeds` | fee-authority | `["fee-authority", mint]`, derived and unit-tested; **no implemented instruction uses it**, because tag 7 is blocked |
| seed | `rebate_pool_seeds` | rebate-pool | `["rebate-pool", mint]`, derived and unit-tested; **no implemented instruction uses it**, for the same reason |

The rebate arithmetic (`rebate_bps`, `rebate_lamports`, `HOLD_FULL_SECONDS` and `REBATE_FEE_BPS`)
is in `state.rs` and unit-tested. It is a curve, not a feature: there is no instruction that pays it,
so the flip tax is not built and this table does not list it as one.

**Two facts the table cannot carry, and they narrow what the evidence proves.** Added
2026-11-08T07:45Z from `records/findings/37-program-v2-review-fixes.md`, which measured both:

> v1's `SetPendingPrice` and `SetStatus` take no signer, so on the deployed devnet program any keypair
> can stage a price and flip a ticket's status; an immutable deploy has no upgrade path, so that hole
> is in v1's bytes permanently, and the devnet refusals prove the price predicate on prices the deploy
> key chose, not that a stranger was kept from choosing them.

> `ScoreForecast` recomputes `covered` from the forecast's own ends and refuses a score below the
> band's width, but it does not recompute the penalty term: `interval_score_micro` above that floor is
> the authority's assertion, not a number the chain verified.

The first is measured by re-running the reviewer's own exploit against the patched v2 (proof `g`: two
`6026` refusals, record bytes unchanged) and by reading v1's source and its landed deploy. The second
is measured by the live refusals `6030` and by the unit test that `u64::MAX` is still accepted for a
width of 1. Neither sentence is a defect list: both are limits on what the program can ever prove.

**What this table does not say.** It does not say the program is deployed on a public cluster with
these seven tags: v1 on devnet is four. It does not say a third party consumes the band feed: no
program other than this one reads `["band", mint]` today, so the composability claim is unproven
(feature 8). And it does not say the price predicates run on a monitored record: `policy == 1` skips
them, on purpose (D16).

---

## 1. The invariant

### 1.1 The one sentence

> **A ticket minted by Ticketpath cannot change hands without the program writing that hop into
> the ticket's own on-chain record, and the program refuses to write a hop priced above the
> organizer's cap: so the resale record the pricing engine reads is complete and cap-compliant
> by construction, not by the API's good faith.**

Said shorter, and this is the version to put on a slide:

> **The ticket cannot move without the program recording it, and the program will not record a
> price over the cap.**

### 1.2 Why that is the right invariant for *this* product

Ticketpath is an organizer revenue-management tool. It prices **primary** tickets off the
secondary record. It has no listing, bid, buy or checkout endpoint, and it must not grow one.
So the thing the product needs from a chain is not a marketplace. It is **the integrity of its
own input**.

`records/CONTRACT-MAP.md` §5.3 states the gap exactly: the cap and the verified-wallet rule are
carried as policy and cannot be enforced by the API, because "an API cannot prevent a transfer
it is not asked about". That sentence is the whole argument. An off-platform resale is not just
a policy breach, it is **missing data**: it is a real transaction that the pricing engine never
sees. The observed markup distribution then has two holes that no estimator can repair:

1. **The right tail is truncated by policy.** Where the cap binds, the top of the distribution
   is not sampled (`records/00-data-situation.md` Gap 2, `records/findings/01-b-identifiability.md`).
2. **Mass leaves the sample entirely.** Every resale that happens off-platform is a row that
   does not exist. An estimator fitted to the rows that stayed cannot see how many left or at
   what price, so it cannot correct for them.

An on-chain cap plus an on-chain custody record closes the second hole and makes the first
hole *measurable* instead of invisible: if every custody move must be written by the program,
then the count of rows is the count of moves, and a binding cap shows up as volume at the cap
rather than as absence. That is the argument for putting the invariant on a chain, and it is
stronger than "scalpers are bad", which is a moral claim no judge needs from us.

There is a second, cheaper guarantee in the same design, and it is the one the corpus says to
lead with (`p5` §1): **the issuer cannot sell a 501st ticket for a 500-seat room.** Supply is
enforced by the same program, in the same place, at issue time.

### 1.3 The three candidates, and what each one actually buys

The requirement is to choose, not to list. Here is the honest ledger for each, then the choice.

**Candidate A: a Token-2022 transfer hook that enforces the resale cap and the
holder-verification rule at transfer time.**

- *What it buys:* the only mechanism in the three that actually **stops** something. A direct
  `spl-token transfer` fails, in the runtime, with a code the program chose. That is a refusal
  the API cannot produce.
- *What it does not buy:* a transfer hook receives `amount`, the source and destination token
  accounts, the mint, the authority and its extra accounts. **It does not receive a price.**
  There is no price field in an SPL transfer and no way to add one. So "the hook enforces the
  cap" is only true if the price arrives through an account the program wrote in the same
  transaction. On its own, a hook can enforce exactly two things: *amount == 1*, and *the
  destination is on an allow-list*. The cap needs state, and state is candidate C.
- *Two weaknesses that are easy to hide and should not be:* the hook program id is written into
  the mint's `TransferHook` extension **at mint creation** and cannot be changed afterwards, and
  a mint created without the extension is unaffected by the program forever. The guarantee is a
  property of *hooked mints*, not of the system.
- *Cost on a laptop afternoon:* **ESTIMATE** 3 to 5 hours (hook entry point, extra-account
  metas, one Anchor test that asserts the refusal). Small.

**Candidate B: a PDA escrow that holds the ticket between sale and settlement, so no
off-platform transfer is possible.**

- *What it buys:* the only candidate in which **money is under program control**. The program
  receives lamports or a token payment and moves the ticket in the same instruction, so the
  price is not attested, it is the actual payment, and the cap binds on real value rather than
  on a claim. It also gives atomic settlement: no "send the ticket first" scam between
  strangers.
- *What it does not buy:* anything at all about a ticket that was never escrowed. An escrow is
  a **venue, not a constraint**: it is binding only on people who choose to use it. A seller
  who wants 10x and a buyer who will pay it simply do not use the venue. It also rebuilds the
  marketplace surface this product deliberately does not have (no listing, bid, buy or checkout
  endpoint), which puts the submission back into "a chain bolted onto a web2 app" from the other
  direction: a web2 marketplace with a chain-shaped escrow.
- *Cost:* **ESTIMATE** 10 to 14 hours (escrow create, fund, settle, cancel, timeout, fee split,
  and the dispute cases a judge will ask about). The largest of the three by a wide margin, and
  the most likely to be half-finished on a laptop.

**Candidate C: a per-ticket PDA that records issue, custody hops and cap compliance as
program-derived state.**

- *What it buys:* the **record** the product exists to consume, written by the program instead
  of by a backend, with the price, the owner, the counts and the terminal state all derived
  from program state. Every row is a real account that a stranger can read without trusting us.
- *What it does not buy, alone:* nothing forces a transfer through the program, so the record
  goes stale the first time somebody uses `spl-token transfer`. A record with no forcing
  function is an attestation ledger: honest, and bypassable.
- *Cost:* **ESTIMATE** 2 to 3 hours for the record, plus the hook it needs to be meaningful.

**What the three add up to.** A and C are not alternatives; they are the *teeth* and the
*truth*. B is the natural next step the day the product takes money on-chain, and it is not
this weekend's job.

**Not a candidate, but a dependency: the quote memo.** The console's commitment to a quote is a
memo instruction, and the memo program is a third-party program whose id is a property of the
cluster. On devnet it is `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, measured from the proven
memo transaction on 2026-11-08 (`records/findings/40-memo-program-id.md`, class A). On mainnet-beta
this repository names the `solana` CLI's shipped memo program,
`MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`, which is class D: the CLI's id, not a measurement
from mainnet. `testnet` has no measured id, and the client refuses it rather than borrowing one.

> **[CORRECTED 2026-11-08T08:30Z. Three sentences above are stale against the code, and the text is
> kept because it is what the table said when it was written. (1) The row for `mainnet-beta` left
> `chain_client.MEMO_PROGRAMS`: no mainnet read was ever made, and the installed CLI was measured
> writing `Memo4c2p…` rather than `MemoSq4gq…`, so naming the CLI's id for mainnet was a guess the
> evidence contradicts. Both ids stay as named literals in that file because this document quotes
> them and the `ids` gate compares against them, but neither is a mapping for mainnet. (2)
> `testnet` and `mainnet-beta` are both refused, and the surface that refuses is two different
> surfaces: `memo_program_id(cluster)` raises `UnknownCluster` naming the clusters the table covers,
> and the console answers `chain.memoProgram: null` for the server's cluster rather than failing the
> page. (3) `--clone` does not make a local memo comparable to a devnet one, which is corrected at
> §6's memo step.]**

### 1.4 The choice

**Chosen: C as the durable state, forced by A as the mechanism, with B deferred and named.**

Concretely: one program that is both the transfer-hook program and the issuer. Every ticket is
a Token-2022 mint with `decimals = 0` and a `TransferHook` extension pointing at that program.
The hook refuses any transfer the program did not stage. The program's own transfer instruction
writes the hop, checks the cap, then CPIs the transfer, so the hook's refusal is a wall with one
door in it. The record is a PDA per ticket plus a PDA per hop.

Why not A alone: without the record there is nowhere for the price to live, so the cap check
has nothing to compare, and the "cap compliance" claim would collapse back into the backend
re-deriving it from transaction logs. That is the bolted-on web2 app the brief says must not be
submitted.

Why not B: it does not constrain the market it is not in, it costs three times as much, and it
adds exactly the product surface the plan forbids. It is the right answer to a different
question ("settle resale payments on-chain"), and it should be built when the cap is meant to
bind on money rather than on the record. §4.2 says what its absence costs.

Why not C alone: a record nobody is forced to write is a promise.

**So the design is one program, nine entry points, six program-derived account types, and no
marketplace.** The next section is implementable from.

---

## 2. Account layout

Every program-owned account begins with the 8-byte Anchor discriminator, then a `version: u8`,
then a `bump: u8`; those three are not repeated in the field tables. `Pubkey` is 32 bytes.
`Option<T>` is 1 byte of tag plus the payload. All integers little-endian. Sizes are exact
byte counts for the field list as written, and the rent column is the **measured** devnet
figure for that exact size at slot 519,638,900 (`getMinimumBalanceForRentExemption`, rate
`(len + 128) * 5080`).

### 2.1 `EventPolicy`

- **Owner:** Ticketpath program. **PDA seeds:** `["event", slug_bytes]`, where `slug_bytes` is
  the event slug as UTF-8, left-aligned and zero-padded to 32. One per event, created once.
- **Vocabulary:** `slug` is `Event.slug`. The backend resolves `Event.id` (route accepts either)
  and the two are 1:1 in the store.

| # | field | type | bytes | mirrors |
|---|---|---|---|---|
| 0 | `organizer` | Pubkey | 32 | `Organizer.walletAddress` |
| 32 | `verifier` | Pubkey | 32 | nothing on the wire (see §7.3) |
| 64 | `slug` | [u8; 32] | 32 | `Event.slug` |
| 96 | `cap_enabled` | u8 | 1 | `Event.resalePriceCapBps != null` |
| 97 | `cap_bps` | u16 | 2 | `Event.resalePriceCapBps` |
| 99 | `resale_enabled` | u8 | 1 | `Event.resaleEnabled` |
| 100 | `requires_verified_wallet` | u8 | 1 | `Event.requiresVerifiedWallet` |
| 101 | `ticket_count` | u32 | 4 | `Event.issuedCount` |
| 105 | `tier_count` | u16 | 2 | `Event.tiers.length` |
| 107 | `created_at` | i64 | 8 | nothing; ISO-8601 is the backend's format |

Payload 115, plus 10 bytes of header = **125 bytes**, rent **1,285,240**.

`cap_enabled` and `cap_bps` are two fields, not one with a sentinel, because a cap of **zero**
is meaningful: Ontario's rule is resale at face value, and `cap_bps = 0` must mean "at face",
not "uncapped". A `null` on the wire is `cap_enabled = 0`.

**The policy is immutable.** There is no `set_policy` instruction and no field in it can be
written after creation. That is a deliberate trade and §11 records what it costs: the terms the
fan bought under cannot be changed afterwards, the cap cannot be raised or lowered mid-event,
and a compromised organizer key cannot rewrite history. The alternative (a mutable policy plus
a change log) is one more account type, one more instruction and one more trust surface, and it
reintroduces the exact hole it is meant to close: an organizer who raises the cap, sells, and
lowers it again. Refusing the feature is cheaper and stronger.

### 2.2 `TierPolicy`

- **Owner:** program. **PDA seeds:** `["tier", slug_bytes, tier_index_le_u16]`. One per tier.
- **Vocabulary:** `tier_index` is the position in `Event.tiers`, 0-based, and must equal
  `policy.tier_count` at creation, so tiers can only be appended in order and the index cannot
  drift from the wire array. `TicketTier.id` is a string on the wire; the backend maps it by
  position and must never reorder `Event.tiers` for an existing event.

| # | field | type | bytes | mirrors |
|---|---|---|---|---|
| 0 | `event` | Pubkey | 32 | `Ticket.eventId` (via the event PDA) |
| 32 | `tier_index` | u16 | 2 | `Ticket.tierId`, `TicketTier.id` |
| 34 | `name` | [u8; 24] | 24 | `TicketTier.name` |
| 58 | `face_value_lamports` | u64 | 8 | `TicketTier.faceValueLamports` |
| 66 | `total_supply` | u32 | 4 | `TicketTier.totalSupply` |
| 70 | `issued_count` | u32 | 4 | `TicketTier.issuedCount` |
| 74 | `created_at` | i64 | 8 | nothing |

Payload 82, total **92 bytes**, rent **1,117,600**.

`face_value_lamports` lives here and not in the instruction arguments because it is the
denominator of the cap check. If the issuer could pass a face value at issue time, it could
legalise any price by declaring a large face: face 10 SOL with a 25% cap admits a 12.5 SOL
resale of a ticket that sold for 1 SOL. The face is therefore fixed before any ticket exists,
and `TicketRecord.face_value_lamports` is copied from here at issue and asserted equal.

### 2.3 `TicketRecord`

- **Owner:** program. **PDA seeds:** `["ticket", mint]`. One per ticket, created at issue,
  never closed. This is the account the hook reads and the only writer of `owner`.
- **Vocabulary:** every field that has a wire counterpart is named after it in the last column.

| # | field | type | bytes | mirrors |
|---|---|---|---|---|
| 0 | `event` | Pubkey | 32 | `Ticket.eventId` |
| 32 | `tier_index` | u16 | 2 | `Ticket.tierId` |
| 34 | `mint` | Pubkey | 32 | `Ticket.mintAddress` |
| 66 | `token_account` | Pubkey | 32 | nothing; the canonical ATA holding the 1 token |
| 98 | `owner` | Pubkey | 32 | `Ticket.ownerWallet` |
| 130 | `issued_to` | Pubkey | 32 | `Ticket.issuedToWallet` |
| 162 | `serial` | u32 | 4 | `Ticket.serial` (formatted by the backend, §7.1) |
| 166 | `face_value_lamports` | u64 | 8 | `Ticket.faceValueLamports` |
| 174 | `status` | u8 | 1 | `Ticket.status`, §7.1 |
| 175 | `transfer_count` | u16 | 2 | `Ticket.transferCount`, `ResaleStats.transferCount` |
| 177 | `sale_count` | u16 | 2 | `ResaleStats.saleCount` |
| 179 | `has_last_sale` | u8 | 1 | `Ticket.lastSalePriceLamports != null` |
| 180 | `last_sale_price_lamports` | u64 | 8 | `Ticket.lastSalePriceLamports` |
| 188 | `issued_at` | i64 | 8 | `Ticket.issuedAt` |
| 196 | `redeemed_at` | i64 | 8 | `Ticket.redeemedAt`, 0 means null |
| 204 | `hop_seq` | u32 | 4 | `LedgerEntry[]` length for this ticket |
| 208 | `pending_active` | u8 | 1 | nothing; the stage the hook consumes |
| 209 | `pending_dest` | Pubkey | 32 | nothing |
| 241 | `pending_price_lamports` | u64 | 8 | nothing |

Payload 249, total **259 bytes**, rent **1,965,960**.

The three `pending_*` fields exist only inside one transaction: `transfer_ticket` sets them,
the hook consumes them and clears them, and if either step reverts neither write survives.
No nonce and no expiry slot is needed precisely because the stage cannot outlive the
transaction that created it. That is a property of the design, not an oversight: an earlier
draft carried `pending_expiry_slot` and it was deleted once the atomicity argument was written
down.

`serial` is an integer on chain because a fixed-size field cannot carry a free-form string. The
wire wants `"GA-0142"`. §7.1 makes the backend the single formatter, so the two cannot disagree.

### 2.4 `HopRecord`

- **Owner:** program. **PDA seeds:** `["hop", mint, seq_le_u32]`. **Append-only**: created by
  `init`, and no instruction in the program writes an existing one. One per custody change.
- **Vocabulary:** this is `LedgerEntry`, field for field. The row's own account is the reason
  `signature` and `slot` need no storage: the creating transaction's signature and slot are
  exactly those values.

| # | field | type | bytes | mirrors |
|---|---|---|---|---|
| 0 | `mint` | Pubkey | 32 | `LedgerEntry.ticketId` (via the record) |
| 32 | `seq` | u32 | 4 | `LedgerEntry.id` within the ticket |
| 36 | `kind` | u8 | 1 | `LedgerEntry.kind` (0 issue, 1 sale, 2 transfer, 3 redeem, 4 revoke) |
| 37 | `from_wallet` | Option&lt;Pubkey&gt; | 33 | `LedgerEntry.fromWallet` |
| 70 | `to_wallet` | Option&lt;Pubkey&gt; | 33 | `LedgerEntry.toWallet` |
| 103 | `price_lamports` | Option&lt;u64&gt; | 9 | `LedgerEntry.priceLamports` |
| 112 | `occurred_at` | i64 | 8 | `LedgerEntry.occurredAt` (unix seconds; ISO-8601 rendered by the backend) |

Payload 120, total **130 bytes**, rent **1,310,640**.

`markupBps` is **not stored**, for the reason `records/CONTRACT-MAP.md` §7.7 already gives: if
the chain and the backend both compute it they will eventually disagree, and on a multi-tier
event the disagreement is not cosmetic. The chain decides cap compliance in lamports; the API
computes basis points with `ticketpath/core/markup.py`. §3.10 proves the two agree in the
direction that matters.

### 2.5 `HolderVerification`

- **Owner:** program. **PDA seeds:** `["verified", wallet]`. One per verified wallet, per
  program. Created by `grant_verification`.
- **Vocabulary:** `wallet` is `WalletVerification.wallet`, `verified_at` is
  `WalletVerification.verifiedAt`, `method` is `VerificationMethod`.

| # | field | type | bytes | mirrors |
|---|---|---|---|---|
| 0 | `wallet` | Pubkey | 32 | `WalletVerification.wallet` |
| 32 | `verified_at` | i64 | 8 | `WalletVerification.verifiedAt` |
| 40 | `expires_at` | i64 | 8 | nothing; surfaces through `WalletVerification.flags` (§7.3) |
| 48 | `method` | u8 | 1 | `WalletVerification.method` (0 wallet_signature, 1 identity) |

Payload 49, total **59 bytes**, rent **949,960**.

`method = 1` (identity) is representable and **never produced**: no identity provider is
connected, so a program that could set it would be claiming a check nobody ran. The instruction
hard-codes 0.

`expires_at` is in the account and in the gate, because a verification that never expires is a
permanent allow-list, and the difference between a check and a souvenir is whether it can fail.

### 2.6 `ExtraAccountMetaList` (Token-2022 transfer-hook interface)

- **Owner:** program. **PDA seeds:** `["extra-account-metas", mint]`, the interface's prescribed
  derivation. One per mint. Holds two entries: the `TicketRecord` (derivable from the mint) and
  the `EventPolicy` (not derivable; supplied, and the hook asserts it is the canonical PDA for
  `record.event`).
- Size is `4 + n * 35` for `n` entries under the interface's `ExtraAccountMeta` layout, possibly
  plus 8 bytes of its own discriminator. At `n = 2` that is **74 bytes** (rent 1,026,160) or 82
  (rent 1,066,800). **UNVERIFIED-FROM-THIS-MACHINE**; §6 step 9 measures it.

### 2.7 The two Token-2022 accounts

- **Mint.** Address is a program PDA: `["mint", slug_bytes, tier_index_le_u16, serial_le_u32]`,
  so serial uniqueness inside an event tier is structural and there is no registry to keep in
  sync. `decimals = 0`, `supply = 1`, `mint_authority = ["issuer", slug]` PDA, `freeze_authority
  = None`, extension `TransferHook { program_id = Ticketpath, authority = None }`. The
  extension's authority is None because the hook can never be changed, which is the honest
  consequence of the program id being fixed at creation.
  Size is **151 bytes** by the arithmetic (82 base mint + 1 account-type + 4 TLV header + 64
  `TransferHook`), or 234 if the runtime pads the base to 165. Rent 1,417,320 / 1,838,960.
  **UNVERIFIED-FROM-THIS-MACHINE**; §6 step 9 measures it. The whole difference between the two
  layouts, mint plus meta list, is 0.23 SOL on a 500-ticket event, which changes no conclusion.
- **Token account.** The canonical associated token account of the holder for that mint, 165
  bytes, rent **1,488,440** measured. `amount = 1`. The record stores its address so the hook can
  assert `source == record.token_account` and reject a second, off-record token account.

### 2.8 Total on-chain size and cost

Per event with two tiers, per ticket, and per hop, all at the measured rate:

| account | count | size | rent each | lamports |
|---|---|---|---|---|
| `EventPolicy` | 1 | 125 | 1,285,240 | 1,285,240 |
| `TierPolicy` | 2 | 92 | 1,117,600 | 2,235,200 |
| `TicketRecord` | 500 | 259 | 1,965,960 | 982,980,000 |
| mint (Token-2022 + hook) | 500 | 151 | 1,417,320 | 708,660,000 |
| token account | 500 | 165 | 1,488,440 | 744,220,000 |
| `ExtraAccountMetaList` | 500 | 74 | 1,026,160 | 513,080,000 |
| `HopRecord` | 800 (500 issue + 300 resale) | 130 | 1,310,640 | 1,048,512,000 |

**Total 4,000,972,440 lamports, 4.00 SOL**, for a 500-ticket event with 300 recorded resales
and no redemptions. Upper bound with the padded mint and the discriminated meta list:
4,232,112,440 (4.23 SOL). The marginal cost of a ticket is 7,208,520 lamports (0.0072 SOL) and
of a hop 1,310,640 (0.0013 SOL).

Two notes a judge will ask about. Hop rent is **not recoverable**: closing hop accounts would
delete the record, which is the product. And the whole figure is rent, so it is capital, not
spend: it returns only if the accounts are closed. At a 500-seat event the per-seat chain cost
is 0.008 SOL, which is the number to compare against a payment processor's take.

### 2.9 Account count

**Nine account types, of which six are program-derived PDAs** (`EventPolicy`, `TierPolicy`,
`TicketRecord`, `HopRecord`, `HolderVerification`, `ExtraAccountMetaList`) and three are not
(`mint`, token account, and the program's own ProgramData). Two instruction-signing PDAs also
exist but own nothing: the mint authority `["issuer", slug]` and, if the operator wants it, a
fee payer. Those are not accounts in the layout sense and carry no rent.

---

## 3. The instruction set

Nine entry points: seven the program defines, two the transfer-hook interface requires. Every
signer column names who must sign; every account column is a positional list an implementer can
write a struct from.

### 3.1 `create_event`

| | |
|---|---|
| **signer** | `organizer` |
| **accounts** | `event_policy` (init, PDA), `organizer` (signer, writable: pays rent), `system_program` |
| **args** | `slug: [u8;32]`, `verifier: Pubkey`, `cap_bps: Option<u16>`, `resale_enabled: bool`, `requires_verified_wallet: bool` |
| **preconditions** | `slug` non-empty and at most 32 bytes; `cap_bps` if present is `<= 10_000`; the PDA does not exist |
| **effects** | writes `EventPolicy`; `organizer` is the signer; `ticket_count = 0`; `tier_count = 0`; `created_at = Clock::unix_timestamp` |
| **errors** | `E_SLUG_TOO_LONG` 6000, `E_CAP_OUT_OF_RANGE` 6006 |

### 3.2 `create_tier`

| | |
|---|---|
| **signer** | `organizer` |
| **accounts** | `event_policy` (read), `tier_policy` (init, PDA), `organizer` (signer, writable), `system_program` |
| **args** | `tier_index: u16`, `name: [u8;24]`, `face_value_lamports: u64`, `total_supply: u32` |
| **preconditions** | signer is `policy.organizer`; `tier_index == policy.tier_count`; `face_value_lamports > 0`; `total_supply > 0` |
| **effects** | writes `TierPolicy`; `policy.tier_count += 1` |
| **errors** | `E_NOT_ORGANIZER` 6002, `E_TIER_INDEX` 6001, `E_FACE_ZERO` 6005 |

### 3.3 `issue_ticket`

| | |
|---|---|
| **signer** | `organizer` |
| **accounts** | `event_policy`, `tier_policy` (mut), `ticket_record` (init), `mint` (init), `mint_authority` (PDA `["issuer", slug]`), `holder_verification` (read, optional), `token_account` (init, ATA of holder), `hop_0` (init), `token_2022_program`, `ata_program`, `system_program`, `rent` |
| **args** | `tier_index: u16`, `serial: u32`, `holder: Pubkey` |
| **preconditions** | signer is `policy.organizer`; tier exists; `tier.issued_count < tier.total_supply`; mint PDA unused; if `policy.requires_verified_wallet` then `holder` has a live `HolderVerification` |
| **effects** | creates the mint with the hook extension and `decimals 0`; creates the meta list; mints 1 to the ATA; writes `TicketRecord` with `owner = issued_to = holder`, `status = valid`, `face_value_lamports = tier.face_value_lamports`; writes `HopRecord{seq 0, kind issue, from null, to holder, price null}`; `tier.issued_count += 1`; `policy.ticket_count += 1` |
| **errors** | `E_TIER_EXHAUSTED` 6004, `E_TICKET_EXISTS` 6007, `E_DEST_UNVERIFIED` 6012, `E_VERIFICATION_EXPIRED` 6018 |

This instruction is the "501st ticket" refusal. It is a four-line check and it is the cheapest
credibility in the design.

### 3.4 `transfer_ticket`

The only legal custody move. One instruction, one transaction, no partial state.

| | |
|---|---|
| **signer** | `seller`, who must equal `record.owner` |
| **accounts** | `event_policy` (read), `ticket_record` (mut), `mint` (read), `source_token_account` (mut), `destination_token_account` (init_if_needed, ATA), `destination_wallet` (read, the owner of the destination ATA), `holder_verification` (read, optional), `hop_n` (init), `token_2022_program`, `ata_program`, `system_program`, `rent` |
| **args** | `price_lamports: Option<u64>` |
| **preconditions** | signer is `record.owner`; `record.status == valid`; `destination_wallet != record.owner`; `policy.resale_enabled`; if `price` is `Some`, then `price >= 1` **and the cap check in §3.10**; if `policy.requires_verified_wallet`, the destination has a live verification |
| **effects** | (1) writes `HopRecord{seq record.hop_seq, kind = sale if price else transfer}`; (2) stages `pending_active = 1, pending_dest, pending_price`; (3) CPIs `transfer_checked(amount = 1, decimals = 0, authority = seller)`; (4) the hook validates the stage, mutates `owner`, `transfer_count`, `sale_count`, `last_sale_price_lamports`, `hop_seq`, and clears the stage; (5) the ATA moves |
| **errors** | `E_NOT_OWNER` 6016, `E_TICKET_NOT_VALID` 6013, `E_SELF_TRANSFER` 6015, `E_RESALE_DISABLED` 6011, `E_PRICE_ZERO` 6014, `E_CAP_EXCEEDED` 6010, `E_DEST_UNVERIFIED` 6012, `E_VERIFICATION_EXPIRED` 6018, plus the hook's `E_AMOUNT_NOT_ONE` 6008, `E_TRANSFER_NOT_STAGED` 6009, `E_DEST_MISMATCH` 6017 |

Ordering matters and is the design: **the hop is written before the transfer, and the stage is
set before the CPI.** If the CPI fails, the whole transaction reverts, so no hop can exist
without a transfer and no transfer can exist without a hop. There is no window, no reconciliation
job, and no repair instruction, which is why the program has none.

### 3.5 `redeem_ticket`

| | |
|---|---|
| **signer** | `holder`, who must equal `record.owner` |
| **accounts** | `ticket_record` (mut), `redeemed_hop` (init), `holder` (signer), `system_program` |
| **preconditions** | signer is `record.owner`; `record.status == valid` |
| **effects** | `status = redeemed`, `redeemed_at = now`, `HopRecord{kind redeem, from owner, to null, price null}` |
| **errors** | `E_NOT_OWNER` 6016, `E_TICKET_NOT_VALID` 6013 |

Signed by the holder, not the organizer, because the gate scan should prove *custody right now*,
and because an organizer key that can burn a fan's ticket after entry is a worse product. The
organizer's `verifier` key is not involved.

### 3.6 `revoke_ticket`

| | |
|---|---|
| **signer** | `organizer` |
| **accounts** | `event_policy` (read), `ticket_record` (mut), `revoke_hop` (init), `organizer` (signer), `system_program` |
| **args** | `reason: u8` (0 refund, 1 dispute, 2 error) |
| **preconditions** | signer is `policy.organizer`; `status != revoked` |
| **effects** | `status = revoked`; `HopRecord{kind revoke}` |
| **errors** | `E_NOT_ORGANIZER` 6002 |

The `revoke` kind exists on the wire and no fixture row uses it. Without an instruction it would
stay a type that never happens.

### 3.7 `grant_verification`

| | |
|---|---|
| **signer** | `verifier`, who must equal `policy.verifier` |
| **accounts** | `event_policy` (read), `holder_verification` (init_if_needed, PDA), `verifier` (signer, writable), `system_program` |
| **args** | `wallet: Pubkey`, `ttl_seconds: i64` |
| **preconditions** | signer is `policy.verifier`; `ttl_seconds` in 60..=31_536_000 |
| **effects** | writes `HolderVerification{wallet, verified_at = now, expires_at = now + ttl, method = 0}` |
| **errors** | `E_NOT_VERIFIER` 6003 |

**This is the one place trust leaves the chain, and it is stated rather than hidden.** The
program cannot verify that a wallet belongs to a person, so somebody must assert it. The
assertion is made by a single key, and a compromised `verifier` key admits any wallet to any
event that key serves. What it cannot do is raise a cap, move a ticket, or change a face value.
§4.2.4 says what would be needed to remove the key entirely (an Ed25519-precompile self-service
path, sketched in §8.4) and why it is not in the minimum.

The off-chain half of this already exists and is correct: `ticketpath/core/ed25519.py` verifies
a detached signature over the frozen `verificationMessage()` from `lib/solana.ts`, and the
backend's nonce is single-use. So the honest split is: **the identity evidence is verified
off-chain by code that exists, and the resulting allow-list is enforced on-chain by the hook.**
That is a weaker claim than "verified on-chain" and a true one.

### 3.8 `initialize_extra_account_meta_list` (hook interface)

Called once per mint, from `issue_ticket`. Registers the two extra accounts the hook needs. No
preconditions beyond the mint existing and no args.

### 3.9 `execute` (hook interface)

| | |
|---|---|
| **signer** | none; invoked by Token-2022 inside a transfer CPI |
| **accounts** | `source_token_account`, `mint`, `destination_token_account`, `owner`, `extra_account_meta_list`, `ticket_record` (mut), `event_policy` (read) |
| **args** | `amount: u64` |
| **preconditions, in order** | `amount == 1`; `record.token_account == source`; `policy.key() == record.event`; `policy.key() == PDA(["event", policy.slug])`; `record.pending_active == 1`; `destination`'s owner `== record.pending_dest`; `record.status == valid` |
| **effects** | `owner = pending_dest`; `transfer_count += 1`; if `pending_price != 0` then `sale_count += 1`, `has_last_sale = 1`, `last_sale_price_lamports = pending_price`; `hop_seq += 1`; stage cleared |
| **errors** | `E_AMOUNT_NOT_ONE` 6008, `E_TRANSFER_NOT_STAGED` 6009, `E_DEST_MISMATCH` 6017, `E_TICKET_NOT_VALID` 6013 |

The hook is small on purpose. It checks **one thing that matters** (this transfer was staged by
the program, for this destination) and it is **the only writer of custody state**, so a bug in
any future instruction cannot leave the record stale: the record is written by the code path
every transfer must pass.

### 3.10 The cap check, exactly

The cap is `resalePriceCapBps`, basis points over the ticket's own tier face, and the wire
already fixes the convention: `2500` means +25%, signed, and a sale below face is negative. In
lamports, a sale at price `p` on a ticket of face `f` is admitted iff

```
p * 10_000  <=  f * (10_000 + cap_bps)
```

Both sides are computed in `u128` and compared, with no division anywhere:

```rust
let lhs = (price_lamports as u128) * 10_000u128;
let rhs = (record.face_value_lamports as u128) * (10_000u128 + policy.cap_bps as u128);
require!(lhs <= rhs, TicketpathError::CapExceeded);
```

Three things about that expression, each of which is a decision:

1. **`u128`, not `u64`.** `f` is a `u64`, and `f * 20_000` overflows `u64` for any face above
   `2^64 / 20_000`. The SIMULATED mirror in §9 prints the overflow factor for `f = 2^64 - 1`:
   20000x. A `u64` multiply would wrap and silently admit an arbitrary price. This is the one
   arithmetic bug in a cap check that a reviewer should look for first.
2. **No division.** The equivalent form `max_price = f * (10_000 + cap) / 10_000; p <= max_price`
   is the same predicate for positive values, but it depends on rounding being floor. Comparing
   products removes the question. `max_price` is still computed for display, and only there.
3. **The boundary is inclusive and it is the cap.** With `f = 1_000_000_000` and `cap = 2500`,
   the maximum admissible price is exactly `1_250_000_000`, and `1_250_000_001` is refused. §9
   demonstrates both sides of that boundary as a pair, because one side alone proves nothing.

**And a theorem the backend can rely on, which §9 checks over 60 triples:** if the chain
admitted a sale, then `ticketpath.core.markup.markup_bps(price, face) <= cap_bps`. The proof is
one line: the chain admits only `p` with `(p - f) * 10_000 / f <= cap`, and rounding half away
from zero is monotone, so a value at or below the integer `cap` rounds to at most `cap`.

**The converse fails, and this matters for the backend.** `markupBps <= capBps` does **not**
imply the chain would admit the sale, because one lamport can be worth less than one basis
point. Measured case from §9: face `1_000_000_001`, cap `3333`. Price `1_333_300_001` is
admitted and reports `markupBps = 3333`; price `1_333_300_002` is refused and **also** reports
`markupBps = 3333`. So the API must never re-derive the cap decision from `markupBps`. The
program's answer is the answer, and a lamport comparison is the only way to reproduce it.

### 3.11 What happens on a cap violation

**The instruction reverts.** No hop is written, no stage is set, the record is untouched, the
token does not move, and the transaction fails with `E_CAP_EXCEEDED` (6010). The fee is charged
and the failed transaction stays in the ledger with its instruction data.

That is the right choice for enforcement and it is a real cost for the data record, so both
halves have to be said:

- **What the chain gives you for free:** proof that the attempt happened. The failed
  transaction is retrievable by signature; its instruction data contains the refused price and
  the mint; its `meta.err` contains the code. So "an attempt to sell this ticket at 3x the cap
  was refused by the program" is a checkable statement, and the price in it is unforgeable in
  the sense that the transaction really was submitted and really was rejected.
- **What the chain does not give you:** a queryable census. There is no account, no index, and
  no event that a failed transaction leaves behind, so counting refusals per ticket requires
  submitting each one and keeping the signatures: the backend only sees the attempts whose
  signature it was handed. RPC providers also prune transaction history, so a refusal is
  evidence with a shelf life.
- **Why this is the honest record and not the ideal one:** `records/findings/02-c-sale-hazard.md`
  §4.5 identifies `cap_blocked` as "the single most valuable element of `delistReason`", the
  observation that separates "nobody wanted it" from "everybody wanted it and the cap rationed
  them". A revert gives that observation as a *sample of reported attempts*, not a census. The
  census needs a listing layer with an ask price and an exposure interval, which this product
  does not have and should not grow (plan item (a): no listing endpoint), so the data request
  stays exactly where `records/F-decision-log.md` D3 left it: four listing fields plus
  `cap_blocked`, supplied by whoever runs the marketplace, not inferred from a reverted transfer.

**The alternative that was considered and rejected:** an instruction that writes the refusal and
then returns success, so every blocked attempt becomes an account. It produces the census, and
it is worse: it makes the refusal a *record* rather than a *wall*, it charges the seller rent and
a fee for the privilege of being told no, and it invites a caller to flood it. Refusing is the
guarantee; recording refusals is telemetry, and telemetry belongs off the invariant's critical
path. If the operator wants it later, it is a separate instruction with no write authority over
any custody state, and the research programme must treat it as self-selected, not as demand.

### 3.12 Error codes

Anchor assigns custom errors from 6000 upward. These numbers are fixed here so the client,
the tests and this document cannot drift; §8.2 uses the same table.

| code | name | raised by | what the UI should say |
|---|---|---|---|
| 6000 | `E_SLUG_TOO_LONG` | create_event | "Event slug is limited to 32 bytes." |
| 6001 | `E_TIER_INDEX` | create_tier | "Tiers must be created in order." |
| 6002 | `E_NOT_ORGANIZER` | create_tier, issue, revoke | "Only the organizer can do that." |
| 6003 | `E_NOT_VERIFIER` | grant_verification | "Only the verification authority can do that." |
| 6004 | `E_TIER_EXHAUSTED` | issue_ticket | "This tier is sold out. The supply is public." |
| 6005 | `E_FACE_ZERO` | create_tier | "Face value must be positive." |
| 6006 | `E_CAP_OUT_OF_RANGE` | create_event | "The resale cap is above the maximum this program accepts." |
| 6007 | `E_TICKET_EXISTS` | issue_ticket | "That serial is already issued." |
| 6008 | `E_AMOUNT_NOT_ONE` | hook | "A ticket is one indivisible token." |
| 6009 | `E_TRANSFER_NOT_STAGED` | hook | "Transfers go through Ticketpath. This one did not." |
| 6010 | `E_CAP_EXCEEDED` | transfer_ticket | "Above the organizer's resale cap. The chain refused it." |
| 6011 | `E_RESALE_DISABLED` | transfer_ticket | "This event does not allow transfers." |
| 6012 | `E_DEST_UNVERIFIED` | transfer_ticket, issue | "That wallet has not been verified for this event." |
| 6013 | `E_TICKET_NOT_VALID` | transfer_ticket, redeem | "This ticket was already redeemed or revoked." |
| 6014 | `E_PRICE_ZERO` | transfer_ticket | "Record a gift as a transfer, not as a zero-price sale." |
| 6015 | `E_SELF_TRANSFER` | transfer_ticket | "That would send the ticket to the wallet that already holds it." |
| 6016 | `E_NOT_OWNER` | transfer_ticket, redeem | "Only the current holder's wallet can move this ticket." |
| 6017 | `E_DEST_MISMATCH` | hook | "The transfer does not match what was recorded for it." |
| 6018 | `E_VERIFICATION_EXPIRED` | transfer_ticket | "That wallet's verification has expired." |
| 6019 | `E_WRONG_TOKEN_PROGRAM` | any token CPI | "This mint is a Token-2022 mint." |
| 6020 | `E_NOT_A_TICKET` | any | "That address is not a Ticketpath ticket." |

6010 is decimal 6010 = hex `0x177A`. **UNVERIFIED-FROM-THIS-MACHINE:** the exact `Custom(N)`
rendering and the log line shape. The corpus verified `custom program error: 0x25` and
`{"Custom":37}` for Token-2022's own `NonTransferable` refusal, which is a *different program*
and must not be quoted as this one's. §6 step 12 shows how the operator captures the real
strings once and puts them here.

---

## 4. Threat model

A design that claims to stop everything is a failed design. This one stops six things, does not
stop six, and says what each of the six would need.

### 4.1 What it stops

1. **A resale recorded above the cap.** `transfer_ticket` refuses with 6010 before any state is
   written. Not "the platform declines to list it": the runtime refuses the transfer.
2. **A custody change with no record.** The hook refuses any transfer the program did not stage
   (6009). There is no path in which the token moves and the record does not, so the record is
   complete for that mint's whole life.
3. **Transfers to wallets that failed verification, on events that require it.** 6012 and 6018,
   at transfer time, for every transfer.
4. **Supply inflation.** `issue_ticket` refuses past `total_supply` (6004), and the mint supply
   is public anyway, so an organizer cannot sell a 501st ticket for a 500-seat room.
5. **Rewrite of history.** Every hop is its own account, created by `init` and never written
   again. An organizer cannot change what a sale was recorded at, or delete a resale, and a
   reviewer can recompute the whole trail from `getSignaturesForAddress` on the hop PDAs without
   trusting the backend.
6. **Policy rewritten under the fan's feet.** The cap, the face, the resale flag and the
   verification requirement are immutable after creation, so the terms a ticket was sold under
   are the terms the chain enforces for its whole life.

### 4.2 What it does not stop, and what each would need

1. **A side payment off-chain.** Two wallets agree on 5 SOL, the buyer sends 4.9 in cash or USDC
   on another chain, and the pair record a resale at face value. The chain bounds the *record*,
   not the *money*: it can prove the recorded price was within the cap, and it cannot prove the
   recorded price was the price. What it would need: the counterparty paying *through* the
   program, which is candidate B, the PDA escrow, and even then only for pairs who route through
   it. A cash envelope defeats every on-chain design, and any pitch that says otherwise is
   wrong.
   **Consequence for the research, and it is a useful one:** when side payments exist, the
   recorded markup is a **lower bound** on the true markup, while the cap truncates the right
   tail from above. So the observed distribution is squeezed from both ends, and both ends are
   visible in the record: the cap as a mass point at `cap_bps`, and under-reporting as sales
   priced suspiciously close to face between wallets that also transact elsewhere. Neither is
   fixable by better modelling, and both belong in the data-requirements document rather than
   inside an estimator.
2. **The seller and the buyer being the same person.** Two wallets, one owner, a transfer at a
   real price within the cap, to fabricate a price record. The chain records it faithfully. What
   it would need: identity (which is the `verifier` key's job and is one key's opinion), or
   graph evidence. The design at least *hands over the graph*: every hop is a wallet-to-wallet
   edge with a timestamp, so wash trading is detectable by cycle structure and repetition, which
   is the best available answer and is statistical, not a guarantee.
3. **A compromised organizer key.** It can issue tickets to itself up to `total_supply`, mint a
   free ticket, grant verification to any wallet, and revoke tickets. It cannot exceed the cap
   on any sale, cannot move a fan's ticket (transfers and redemptions need the holder's
   signature), and cannot change the face, the cap, or the supply. What it would need: the
   `organizer` account being a multisig from day one (a Squads vault is just a pubkey to this
   program, so this needs no code change at all, only an operational decision), and if the
   operator wants key rotation, that is exactly the mutable-policy surface §2.1 refused.
4. **A compromised `verifier` key.** It admits arbitrary wallets to the events that key serves.
   Blast radius is bounded: it cannot change a price, a cap, or a supply. Needs: a multisig, or
   the Ed25519 self-service path in §8.4 that removes the key, at the cost of one more
   instruction and a sysvar parse.
5. **A mint created without the hook.** The guarantee is a property of hooked mints. A ticket
   minted by `issue_ticket` always has the extension, and the extension's program id cannot be
   changed afterwards, so a Ticketpath ticket cannot be un-hooked. But a *different* mint, made
   by anyone with `spl-token create-token`, is an ordinary transferable Token-2022 token that the
   record knows nothing about, and a buyer who accepts one has been defrauded by a mint, not by
   Ticketpath. What it would need: buyers checking that the mint's hook program id is the
   Ticketpath program before paying anything, which is a client-side check the *verification*
   page can do (`/verify` exists in the frontend), plus the issuer's public mint list. This is
   the honest weakness of every hook design and it should be on a slide rather than in a
   footnote.
6. **One person holding fifty wallets.** This design has no sybil resistance at all. Nothing in
   it counts wallets, and nothing in it knows that two wallets belong to one attendee, so the
   actual scalper mechanism (buy from the primary sale with many wallets, then resell at the cap)
   is untouched. The cap still bounds the resale price per ticket, which is the part the product
   can honestly claim. What it would need: an identity commitment with a nullifier PDA, so a
   second wallet registering the same commitment fails because the account already exists, plus a
   per-wallet holding cap in the hook. That is a real design, it needs an off-chain identity
   check and a decision about what the chain is allowed to remember about a person, and it is not
   in this document. §12.2 names the sibling document that specifies it.

### 4.3 One more residual: the record is a record of what was recorded

The invariant says the record is complete **for this mint**, and that every recorded price is
within the cap. It does not say every price is true (§4.2.1) and it does not say the ticket was
the only ticket (§4.2.5). Those three sentences together are the claim; a judge who hears one
without the others has heard marketing.

---

## 5. The demo story, in three tiers

Nothing below blurs the tiers. Tier (a) runs on this machine. Tier (b) exists only if the
operator runs the runbook in §6 on a machine with a toolchain. Tier (c) is what a real
deployment would need and is not attempted this weekend.

### Tier (a): what runs here without a toolchain, SIMULATED

> **[Heading corrected 2026-11-08T03:45Z: it used to read "with no toolchain". There is a toolchain
> on this machine now (§6 step 0), so what makes this tier simulated is the mirror being Python, not
> the absence of Agave. The tier itself is unchanged and still proves nothing about any cluster.]**

A Python mirror of the same state machine, same field names, same instruction names, same error
codes, same integer arithmetic, standard library only. It is **not** a Solana program, it proves
nothing about any cluster, and every line of its output is marked **SIMULATED**. Its source is
in §9.1 and its real output is in §9.2, both produced on this machine:

```
python3 tp_sim.py
```

What it demonstrates, and why each one is worth demonstrating rather than asserting:

| arm | shows | error code |
|---|---|---|
| 0 | the supply cap refuses a 2nd ticket in a 1-seat tier | 6004 |
| A | a custody move the program did not stage is refused, and the record does not move | 6009 |
| B | the cap boundary exactly: `cap`, `cap - 1` admitted; `cap + 1` refused | 6010 |
| C | the stage is consumed on use, so it cannot be replayed | 6009 |
| D | a transfer to an unverified wallet is refused, then admitted after verification | 6012 |
| E | a redeemed ticket cannot move | 6013 |
| F | an expired verification is a refusal, not a pass | 6018 |
| G | a gift is a transfer with no price, and it is not counted as a sale | none |
| H | the theorem: every admitted `(face, cap, price)` triple reports `markupBps <= capBps` | none |
| I | the converse fails, so `markupBps` cannot decide the cap | none |
| J | `u64` overflows on the cap product, so the check must be `u128` | none |
| K | a cap that binds produces a mass point at the cap, which the fixture never shows | none |

Arm K is the one that speaks to the research programme: 200 sim resales, 20 of them exactly at
the cap. `records/00-data-situation.md` §2 records that the fixture's generator never produces a
sale at the cap, which is how we know the fixture is synthetic. An enforcing program makes that
mass point real, and the mass point is precisely the `cap_blocked` observation
(`02-c` §4.5) seen from the other side.

What the simulation cannot show: that Token-2022 calls the hook, that the CPI succeeds, that the
extra accounts are wired correctly, that the sizes in §2 are the sizes the runtime allocates. All
of that is tier (b).

### Tier (b): what a devnet deploy would show, if the operator runs §6

> **[CORRECTED 2026-11-08T03:45Z: the deploy has run, and four of the six items below are now
> measured on devnet rather than anticipated. Item 1 holds: the program id resolves and
> `getAccountInfo` reports `executable: true` (owner the BPF upgradeable loader, 36 bytes of account
> data). Item 2 holds for the extension, not for the CLI: `getAccountInfo` with `encoding:
> jsonParsed` on the mint returns `decimals 0`, `supply 2` and the `transferHook`, `metadataPointer`
> and `tokenMetadata` extensions; the executor of this correction did not run `spl-token display`
> itself. Item 3 is *not* the shape the deployment took: the cap is checked against a staged price in
> the hook, so the refusal is a failed Token-2022 transfer carrying 6010 rather than 6009, and the
> runbook's `transfer_ticket` does not exist in the deployed program. Item 4 holds, and it is the
> strongest one: 1,250,000,000 admitted, 1,250,000,001 refused with `InstructionError [0, Custom
> 6010]`, each with its own signature, slot and block time, plus the program's own log line naming the
> price, the face and the cap. Item 5 does not exist — the hop record is not in the program. Item 6,
> the hookless negative control, is not recorded as having been run. `records/devnet-artefacts.json`
> is the primary record; `records/STATE-OF-PROJECT.md` §A2 is the re-read.]**

Only after the runbook runs. Nothing in this subsection has happened.

1. **A program id that resolves.** `solana program show <program_id>` returns the authority, the
   data length and the balance. That id goes into the runbook log and the submission README, and
   into this document only once a command has printed it.
2. **A hooked mint that a stranger can inspect.** `spl-token display <mint>` lists the
   `TransferHook` extension and names the program. This is the check that distinguishes "we
   deployed a program" from "we deployed a program and the ticket is actually attached to it".
3. **The refusal, as a real failed transaction.** A direct `spl-token transfer` of a Ticketpath
   ticket fails, the log shows the hook program invoked *inside* the Token-2022 CPI, and the
   error is 6009. That single transaction is the anti-fraud claim, executed: not "the API
   declined", but "the runtime refused, and here is the signature".
4. **The cap boundary, as two transactions.** `transfer_ticket` at exactly the cap price lands;
   `transfer_ticket` one lamport above fails with 6010. Two signatures, one lamport apart, is
   the strongest possible presentation of the arithmetic in §3.10.
5. **A custody trail a stranger can walk.** `getSignaturesForAddress` on the hop PDAs returns one
   signature per hop in order, each with a slot and a block time, and the record's `owner` at the
   end of the walk matches the wallet that holds the token. This is the `LedgerEntry.signature`
   and `.slot` the wire contract wants, sourced from the chain instead of from `null`.
6. **The cheap negative control that makes 3 credible:** a hookless Token-2022 mint transferred
   freely in the same session. Without it, "the transfer failed" is ambiguous; with it, the
   difference between a hooked mint and an unhooked one is one experiment.

### Tier (c): what a real deployment would need

1. **The cap must bind on money, which means the escrow.** §4.2.1: until the payment is routed
   through the program, the cap binds the record only. Candidate B, with escrow create, settle,
   cancel, timeout, fee split, and the dispute path a lawyer will want.
2. **Organizer and verifier authorities as multisigs**, with a documented signing policy, and an
   audit of the program before real money touches it. Program upgrade authority either burned or
   behind a timelocked multisig; a permanent upgrade authority is a permanent backdoor and a
   judge may ask.
3. **An indexer.** The hop PDAs are the record, but every read the product needs is a join: the
   event's tickets, the ticket's hops, the event's distribution. Serving that from RPC per
   request is not viable at 500 tickets, never mind 5,000, so a small indexer that tails the
   program's accounts is part of a real deployment and is not part of this week.
4. **Wallet support and the `decimals = 0` reality.** Not every wallet renders a Token-2022 mint
   well, and a hooked mint is a stricter edge case than most wallets have been tested on. A real
   launch needs a tested client path on the wallets the fans actually use.
5. **The legal question, still open and still not ours.** A cap at face value is representable in
   one field (`cap_bps = 0`, §2.1), but whether any jurisdiction requires one is a legal question
   this document does not answer. The prior corpus asserts a specific Ontario rule from a single
   news source and flags it for corroboration before it goes on camera. Nothing in this design
   depends on it: the cap is the organizer's own policy, enforced by the organizer's own program.
6. **A key-management and revocation story** for the verifier, and a policy for what happens when
   a verification is granted in error. Today the answer is "revoke instruction", which does not
   exist, because `HopRecord` and `HolderVerification` are append-only in this design. A real
   deployment needs `revoke_verification`, and it is deliberately absent here so that the
   minimum stays a minimum.

---

## 6. The laptop runbook

For a machine with Agave and Rust. Every step says what it proves and how to know it worked.
Anything that cannot be checked from this machine is marked. Run it in order, on devnet, with a
throwaway keypair; nothing here touches mainnet.

**What cannot be done from here, stated once:** there is no Rust, no Cargo, no Agave, no
`spl-token` on this machine, so the program cannot be built or deployed here, and no step below
has been executed by the author. Steps 1 to 3 are the ones that need the laptop; from 4 onwards
everything is verification of what those three produced.

> **[CORRECTED 2026-11-08T03:45Z on the first sentence only. The toolchain was installed here on
> 2026-11-07 (Agave CLI 4.3.2, `spl-token` 5.6.1, `cargo-build-sbf` 4.4.0, rustc 1.99.1, all on a
> login shell's `PATH`; `records/findings/18` is the install record), and steps 2 and 3 have since
> been run by `tools/devnet_publish.py`, which is the supported path and does all three of them.
> The commands in steps 1 to 3 below are the hand-run equivalents of 2026-11-07 and two of their
> paths were wrong; each step now carries the corrected form. The step *numbers* are unchanged so
> that §5 and `records/findings/18` still point at the right step.]**

### Step 0: confirm what you have

```bash
solana --version && spl-token --version && cargo --version && rustc --version
cargo-build-sbf --version
```

**Proves:** which generation of the CLI you are on. `records/00-prior-direction-index.md` §3
records that the JS packages split into two incompatible generations, so if a JS client is used,
pin `@solana/web3.js` and never install `@solana/kit` alongside it.
**Verify:** all five print a version. `cargo build-sbf` is what turns Rust into a deployable
`.so`; if it is missing, Agave is installed without the SBF tools and step 2 will fail.

**Run it from a login shell** (`bash -lc`): the install puts its binaries on the profile's `PATH`
and nowhere else, so a plain non-login shell answers `command not found` for all five even when
everything is installed. `tools/devnet_publish.py` refuses to start until it can see `solana`,
`spl-token`, `solana-keygen` and `cargo-build-sbf`, and says exactly that.

Install line, if the toolchain is absent (quoted from the prior corpus at the time it was written;
the install that ran on this machine used the Agave installer it points at, and
`records/findings/18` records the versions and the swap file it needed):

```bash
sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
rustup install stable && rustup default stable
```

### Step 1: a funded keypair

**Corrected 2026-11-08T03:45Z.** The publisher reads the path from `TP_DEVNET_KEYPAIR` and
otherwise defaults to `~/.config/ticketpath-devnet/authority.json`, which is *not* the path this
step used to name; either works, and the publisher's default is the one its runs have used.

```bash
solana-keygen new --silent -o ~/.config/ticketpath-devnet/authority.json   # 0700 dir, 0600 file
export TP_DEVNET_KEYPAIR=~/.config/ticketpath-devnet/authority.json
python3 tools/devnet_publish.py --dry-run        # prints the plan and the authority's address
```

**Proves:** you have a payer and the cluster will talk to you.
**Verify:** the dry run prints an address and a balance. It needs **2 SOL**.

**`solana airdrop` cannot fund it, and this is measured rather than suspected.** The devnet RPC
faucet answers error **410**, *the RPC faucet is closed on this cluster*, so the airdrop in the
older version of this step fails every time and retrying it wastes the only hour you have. Fund it
once from the web faucet, signing in with the operator's own account: network devnet, the address
the dry run printed. `tools/devnet_publish.py` refuses to proceed on a zero balance and prints
those same three steps. **[Corrected 2026-11-08T03:45Z; the 410 and the exact refusal text are in
`records/findings/21` §2.]**

### Step 2: build the program

**Corrected 2026-11-08T03:45Z.** The crate is `programs/cap_hook`, not `programs/ticketpath`, the
binary is `cargo-build-sbf` (a hyphen, and the `build-sbf` subcommand of `cargo` is the other form
of the same tool), and the artefact is `cap_hook.so`.

```bash
cd programs/cap_hook
cargo test --release                       # the cap arithmetic, no cluster
cargo-build-sbf --sbf-out-dir target/deploy
ls -l target/deploy/cap_hook.so
```

**Proves:** the Rust in §8 is at least syntactically a program that the SBF toolchain accepts. It
proves nothing about correctness.
**Verify:** the `.so` exists and is order 10^5 bytes.
**[Measured on this machine 2026-11-07: `cargo test --release` → 4 passed; a clean build 21.84 s;
`target/deploy/cap_hook.so` 85,784 bytes; peak RSS 4,590 MB, and it ran with `CARGO_BUILD_JOBS=2
nice -n 10` because the box has 7.9 GB of RAM and 12 GB of swap.]** A build that prints warnings is
fine; a build that errors is step 2 failing, not step 4 failing.

### Step 3: deploy

**Corrected 2026-11-08T03:45Z.** This has been done: the program is deployed on devnet at
`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`. What follows is the hand-run form, for a fresh
deploy or a redeploy; the supported path is `python3 tools/devnet_publish.py`, which deploys the
program, wires the mint, sends the memo, proves the boundary pair and writes the artefact, and
skips every one of those if the cluster says it is already done.

```bash
cd programs/cap_hook
solana program deploy target/deploy/cap_hook.so --program-id target/deploy/cap_hook-keypair.json
solana program show 5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva
```

**Proves:** the program exists on devnet at a real address.
**Verify:** `program show` prints the authority, the balance and the data length.
**On the address, which this document deliberately did not hold:** the program id is a property of
the deploy keypair, not of the crate, so a redeploy from a different keypair is a different program.
The keypair lives at `programs/cap_hook/target/deploy/cap_hook-keypair.json`, which is git-ignored
(the whole `target/` directory is) and is the secret that owns the program id. The address belongs
in `records/devnet-artefacts.json`, which is where the console reads it from, and in
`programs/cap_hook/README.md`, which points at that record; it does not belong in this design.

**The memo step, and the id it runs under.** The publisher sends the quote memo as its own
instruction, and the program that instruction invokes differs by cluster. This document names
devnet's id because that is the cluster every step here uses:
`Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, measured from the proven memo transaction on
2026-11-08 (`records/findings/40-memo-program-id.md`, class A). Mainnet-beta's is the `solana`
CLI's shipped memo program `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`, class D: it is the
CLI's id and was not measured from mainnet here. The local rehearsal's `--clone` pulls devnet's
program from `--url <devnet>` so a run compares like with like, and that rehearsal path is
untested here. `testnet` has no measured id and the code refuses it. `tools/devnet_publish.py`
reads the id back out of the transaction the cluster landed and fails the run when it does not
match the table.

> **[CORRECTED 2026-11-08T08:30Z. The `--clone` sentence above is wrong, and it was measured wrong
> rather than reasoned wrong. `--clone Memo4c2p…` into a local validator leaves that account a
> program-data stub: the genesis account owns the address and the clone does not replace it, so the
> runtime refuses the memo with `Program is not deployed` before any transaction lands. `--clone`
> of the CLI's other id does replace the genesis account, which is why the two ids behave
> differently and why a clone cannot be described as making a run "compare like with like". What
> the local path's clone is for is to put devnet's account data where a run can read it; it cannot
> make it execute. `--account <address> <file>` moves past that and hits the runtime's program
> cache limit instead, so a local rehearsal cannot complete its memo step with this CLI, and the
> local publish path still uses `--clone`. Measured four times on four fresh local ledgers, quoted
> with the refusal and the two account dumps in `records/findings/40-memo-program-id.md`'s second
> CORRECTION. Mainnet-beta's id is unmeasured and is not in the table.]**

### Step 4: create an event and two tiers

With Anchor's IDL the calls are `create_event` then `create_tier` twice. The shape that matters:

```
create_event  slug="runbook-test" verifier=<verifier pubkey> cap_bps=2500
              resale_enabled=true requires_verified_wallet=true
create_tier   tier_index=0 name="Floor"   face_value_lamports=1000000000 total_supply=2
create_tier   tier_index=1 name="Balcony" face_value_lamports=2000000000 total_supply=1
```

**Proves:** rent flows, PDAs derive, and the cap is a number on chain.
The scripted version of steps 4 to 11 is `anchor test` against a local validator, and then
`anchor test --skip-local-validator --provider.cluster devnet` for the same suite on devnet.
Both invocations are **UNVERIFIED-FROM-THIS-MACHINE**; the individual calls below are the manual
fallback and the source of truth for what each step must show.
**Verify:** `solana account <event_pda>` shows 125 bytes and a nonzero balance;
`getAccountInfo` decoded with a small Borsh reader shows `cap_bps = 2500`, `cap_enabled = 1`.
The cap price for the Floor tier is then exactly `1_250_000_000` lamports.

### Step 5: issue tickets and hit the supply cap

```
issue_ticket  tier_index=0 serial=1 holder=<wallet A>
issue_ticket  tier_index=0 serial=2 holder=<wallet A>
issue_ticket  tier_index=0 serial=3 holder=<wallet A>   # must fail
issue_ticket  tier_index=1 serial=1 holder=<wallet A>   # balcony, face 2 SOL
issue_ticket  tier_index=1 serial=2 holder=<wallet A>   # must fail
```

**Proves:** the 501st-ticket refusal, which is the cheapest half of the "why a chain" answer.
**Verify:** the third and fifth calls fail with `6004 E_TIER_EXHAUSTED`, and
`getAccountInfo <tier_pda>` shows `issued_count = 2` and `issued_count = 1` respectively. If the
refusal instead comes from an Anchor `ConstraintSeeds` or a low-level `0x0`, the PDA seeds in §2
are wrong, not the check.

### Step 6: prove the mint is hooked (this is the bypass that is easy to hide)

```bash
spl-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb display <mint>
solana account <mint>
```

`display` is a recent-CLI subcommand; if your `spl-token` does not have it, `solana account`
prints the same bytes and the extension list is readable from the tail. **UNVERIFIED-FROM-THIS-MACHINE**
which subcommands your version carries; `spl-token --help` settles it in one line.

**Proves:** the ticket is a Token-2022 mint whose `TransferHook` extension names **your** program
id, and `decimals = 0`.
**Verify:** the extension list contains `TransferHook` with the program id from step 3, and there
is no `NonTransferable`. Then the negative control:

```bash
spl-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb create-token --decimals 0
spl-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb mint <that mint> 1
spl-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb transfer <that mint> 1 <wallet B>
```

**Proves:** a hookless mint transfers freely. This is the honest limitation in §4.2.5, executed
rather than described: the guarantee belongs to hooked mints.
**Verify:** the transfer succeeds. If it fails, you are not testing what you think you are.

Check first that the flag you need exists in your CLI version:

```bash
spl-token create-token --help | grep -i -e transfer-hook -e transfer_hook
```

If `--transfer-hook` is absent, mint creation has to happen through the program's `issue_ticket`
(which is the design anyway) and step 6's first half reads the extension after the fact instead
of creating it from the CLI. **UNVERIFIED-FROM-THIS-MACHINE** which CLI versions carry the flag.

### Step 7: the refusal. This is the money shot.

```bash
solana config set --url devnet
spl-token --program-id TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb \
  transfer <ticket mint> 1 <wallet B> --owner ~/.config/solana/wallet-a.json
solana confirm -v <signature>
```

**Proves:** the hook fired and refused. **How to be sure it was the hook and not something
else:** three independent facts must be true in the same transaction.

1. The transaction failed. `solana confirm -v` prints `Transaction failed` and the error object.
2. The error is `Custom(6009)` (`E_TRANSFER_NOT_STAGED`), which only this program can emit.
3. The logs contain `Program <your program id> invoke [2]` and `Program <your program id> failed`
   *inside* the Token-2022 transfer, i.e. the hook was called by the runtime during the CPI and
   returned an error. A failure at depth `[1]` is Token-2022 itself refusing (wrong program id,
   wrong owner, frozen account) and proves nothing about the hook.

Then confirm the record did not move:

```bash
solana account <ticket_record_pda>    # owner must still be wallet A, transfer_count still 0
```

**Verify:** all four hold. If 2 fails with `Custom(0x25)`, the mint is `NonTransferable` and you
have demonstrated a different mechanism; go back to step 6.

### Step 8: the cap, as a pair one lamport apart

First verify wallet B (`grant_verification wallet=<B> ttl_seconds=86400`), because step 4 set
`requires_verified_wallet=true` and an unverified destination will fail with 6012 before the cap
is ever reached, which would look like a cap bug and is not one.

```
transfer_ticket  mint=<floor ticket> price_lamports=1250000000  dest=<wallet B>   # must succeed
transfer_ticket  mint=<balcony ticket> price_lamports=2500000001 dest=<wallet B>  # must fail 6010
transfer_ticket  mint=<balcony ticket> price_lamports=2500000000 dest=<wallet B>  # must succeed
```

**Proves:** the boundary is the cap and the arithmetic is `u128` and exact.
**Verify:** the middle call fails with `6010`, the two around it succeed, and each success wrote a
`HopRecord` with `price_lamports` equal to the argument. A boundary that fails one lamport early
means the check was written with `>=`, or with a floor division that lost a lamport; a boundary
that fails to fail means the check was done in `u64` and wrapped, or was never wired to the
policy.

### Step 9: measure the sizes this document guessed

```bash
solana rent 125 92 259 130 59 74 151 165
solana account <mint>        # read the data length, compare with 151
solana account <extra_account_metas_pda>  # compare with 74
```

**Proves:** §2's sizes and the 4.00 SOL figure.
**Verify:** `solana rent` matches the rent column to the lamport. If the mint is 234 bytes and the
meta list is 82, the conclusions do not change: the per-ticket cost moves from 7,208,520 to
7,670,800 lamports and the 500-ticket total from 4.00 to 4.23 SOL.

### Step 10: the verification gate

```
grant_verification  wallet=<wallet C> ttl_seconds=86400
transfer_ticket     mint=<a fresh ticket> price_lamports=1000000000 dest=<wallet C>   # succeeds
transfer_ticket     mint=<another fresh ticket> price_lamports=1000000000 dest=<wallet D>  # 6012
grant_verification  wallet=<wallet D> ttl_seconds=-1
transfer_ticket     mint=<a third ticket> price_lamports=1000000000 dest=<wallet D>  # 6018
```

**Proves:** the allow-list is consulted per transfer, and an expired entry is a refusal.
**Verify:** 6012 then 6018, with the successes in between. If 6012 never fires, `requires_verified_wallet`
was written as 0 in step 4 and the gate is not being tested.

### Step 11: walk the record without the backend

```bash
solana account <ticket_record_pda>                      # owner, counts, hop_seq
# for each seq from 0 to hop_seq-1:
curl -s -X POST <rpc> -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"getSignaturesForAddress",
       "params":["<hop_pda_for_seq>",{"limit":1}]}'
```

**Proves:** the trail is reconstructible by a stranger from the chain, with no API in the loop,
and each hop's creating signature and slot are exactly the `LedgerEntry.signature` and `.slot`.
**Verify:** the number of hop PDAs equals `hop_seq`, the last hop's `to_wallet` equals the wallet
holding the token (`spl-token balance <mint> --owner <wallet>`), and each hop's `occurred_at`
matches the transaction's `blockTime`. This is the step that turns the wire contract's `null`
signatures into real ones.

### Step 12: capture the strings, once

Record the exact `solana confirm -v` output for 6009, 6010, 6012 and 6018, the log lines around
the hook invocation, and the code numbers as the client sees them. Replace §3.12's
**UNVERIFIED-FROM-THIS-MACHINE** note with what the terminal actually printed. Do not paraphrase:
the corpus already carries one invented error string (`p1c` §5's "TransferHook: price exceeds
face value", which no program emits) and the point of this step is that there are no invented
strings in the submission.

### Step 13: tear down

```bash
solana program close --buffers
solana program close <program_id> --recipient <your address>   # optional
```

**Proves:** the devnet balance is not left parked in a program. Devnet SOL is not money; the
faucet's limit is the real constraint.

---

## 7. What the backend and the frontend show, and the fake-data rule

The frontend is read-only for this work (`AGENTS.md`, rule (f)); nothing in the sibling
`ticketing-frontend/` checkout, outside this repository, was or should be modified. Everything
here is either a change inside `ticketpath/` (not made) or a rule about what may be put in a
field.

### 7.1 Vocabulary: chain field, wire field, conversion

One table, so the two halves cannot drift. The conversions are all trivial and all belong in one
place in the backend.

| chain | wire | conversion |
|---|---|---|
| `TicketRecord.owner` | `Ticket.ownerWallet` | Pubkey to base58 |
| `TicketRecord.mint` | `Ticket.mintAddress` | Pubkey to base58 |
| `TicketRecord.status` 0..3 | `Ticket.status` | `valid, listed, redeemed, revoked`. `listed` (1) is representable and **never written**: there is no listing layer, so the chain will never report it. The wire type keeps the member; the backend will simply never see it from chain state |
| `TicketRecord.serial: u32` | `Ticket.serial: string` | backend formats `{tier_prefix}-{serial:04}`, the only formatter |
| `TicketRecord.face_value_lamports` | `Ticket.faceValueLamports` | integer, unchanged |
| `TicketRecord.transfer_count` | `Ticket.transferCount` | integer, unchanged |
| `TicketRecord.last_sale_price_lamports` | `Ticket.lastSalePriceLamports` | `null` when `has_last_sale == 0` |
| `TicketRecord.issued_at`, `redeemed_at` | `Ticket.issuedAt`, `redeemedAt` | unix seconds to ISO-8601 UTC (`core/timeutil.to_iso`), 0 to `null` |
| `HopRecord.kind` 0..4 | `LedgerEntry.kind` | `issue, sale, transfer, redeem, revoke` |
| `HopRecord.from_wallet`, `to_wallet` | `LedgerEntry.fromWallet`, `toWallet` | `Option<Pubkey>` to base58 or `null` |
| `HopRecord.price_lamports` | `LedgerEntry.priceLamports` | `Option<u64>`, unchanged |
| `HopRecord.occurred_at` | `LedgerEntry.occurredAt` | unix to ISO-8601 UTC |
| the hop PDA's creating transaction | `LedgerEntry.signature`, `.slot` | `getSignaturesForAddress(hop_pda, limit 1)` |
| *(not stored)* | `LedgerEntry.markupBps` | computed by `core/markup.py`, never read from chain |
| `EventPolicy.slug` | `Event.slug`, `Event.id` | the backend's store maps `Event.id` to slug 1:1 |
| `EventPolicy.cap_enabled` + `cap_bps` | `Event.resalePriceCapBps` | `null` when `cap_enabled == 0`. **The chain holds the *enforced* ceiling**, so when a law is stricter than the organiser's own cap, the chain's number is the law's and `Event.resalePriceCapBps` reports it; the organiser's configured number is in the additive `enforcedCap.platformCapBps` (§14.3). A mapping that assumed the two are always equal is wrong and this row says so |
| `EventPolicy.resale_enabled` | `Event.resaleEnabled` | bool |
| `EventPolicy.requires_verified_wallet` | `Event.requiresVerifiedWallet` | bool |
| `EventPolicy.ticket_count` | `Event.issuedCount` | integer |
| `TierPolicy` fields | `TicketTier.*` | one to one, `tier_index` maps to `TicketTier.id` by position |
| `HolderVerification.exists && !expired` | `WalletVerification.verified` | boolean |

`markupBps` being computed rather than stored is the one row where the chain is deliberately not
the source of truth, and it is the rule `CONTRACT-MAP.md` §7.7 already sets. §3.10 proves the two
agree in the direction that matters: a chain-valid sale can never report above the cap.

### 7.2 What becomes real, and what the backend must stop saying

Today `ticketpath/adapters/rpc_adapter.py` returns `enforced: False, checked: False,
reason: "no_program_deployed"` for every mint, and `api/health.py` reports
`programDeployed: False`. That is correct and stays correct until §6 runs. When it does, these
change, and only these:

| field | today | after §6 | how the backend knows |
|---|---|---|---|
| `Ticket.mintAddress` | `SYN…` placeholder | the real mint PDA | read from `TicketRecord.mint` |
| `Ticket.transferRestricted` | `false` | `true` for hooked mints | parse the mint's `TransferHook` extension and compare the program id. Extension presence *is* enforcement, because the runtime always invokes a registered hook; do **not** echo `requiresVerifiedWallet` (the type's comment forbids it) |
| `LedgerEntry.signature`, `.slot` | `null` | the hop's creating signature and slot | `getSignaturesForAddress` on the hop PDA |
| `Event.resalePriceCapBps` | policy only | enforced | the same number, now with teeth |
| `WalletVerification.canReceiveTransfer` | equals `verified` | equals a live `HolderVerification` PDA | `getAccountInfo` on the PDA, compare `expires_at` to the injected clock |
| `/health` `chain.programDeployed` | `false` | `true` with a program id | `solana program show` equivalent: `getAccountInfo(program_id).executable` |

`rpc_adapter.transfer_enforcement` needs one new state: `checked: True, enforced: True,
reason: "hook_attached", programId: <id>`. It must never return `enforced: True` from a config
flag; the only honest route is reading the mint's extensions, which is one `getAccountInfo`.

### 7.3 Two additive keys, not invented fields

`HolderVerification.expires_at` has no home in `lib/types.ts`. It surfaces through
`WalletVerification.flags`, which the contract defines as "machine-readable reasons when a
capability is false": an expired verification returns `verified: false`,
`flags: ["verification_expired"]`, `method: "wallet_signature"`. That is the contract's own
mechanism for exactly this, so no new field is invented and no existing field changes shape.

`EventPolicy.verifier` has no wire counterpart either. It is not needed by the product UI; it is
the key the organizer keeps. It is readable from the chain, which is the point.

### 7.4 The fake-data rule

**The rule, in one line: a value that came from a simulation may live in a field the UI renders
only if that field is labelled on the same screen, and since this week nothing may change the
frontend, that means it may not live in such a field at all.**

So this week's obligation, which the existing backend already meets:

1. `dataSource` on every payload stays `{mode, synthetic: true, label, note}` and its note says
   the data is fixture data, not a scrape, and not evidence.
2. `signature` and `slot` stay `null`. `null` is what makes the Explorer link not render, which
   is the difference between a missing link and a link that 404s.
3. `mintAddress` stays a `SYN…` placeholder that decodes to 32 bytes but exists on no cluster,
   with `dataSource.synthetic` on the same payload saying so.
4. `transferRestricted` stays `false`. `false` is the honest answer while nothing is enforced,
   and it is the single most misleading field in the payload if it is ever set optimistically.
5. `/health`'s `chain` block stays `programDeployed: false` with a `reason`.

And when the frontend may be changed, in this order:

1. A `dataSource.chain` block per payload: `{source: "chain" | "simulated" | "absent", cluster,
   programId, asOfSlot}`. `absent` for the fixture store, `chain` for anything read from a
   cluster, `simulated` for the Python mirror.
2. A chain badge component that renders next to any value whose `chain.source` is not absent:
   grey "SIMULATED" for the mirror, blue "DEVNET" plus the program id for a cluster, and nothing
   at all for `absent`. Explorer links render **only** when `source == "chain"`, because a link
   to a signature that does not resolve is worse than no link.
3. The rule to write into the README so a judge can find it: *no number in this UI carries a
   chain claim unless the payload says which chain and which slot it was read at.*

What is explicitly not done: putting a simulated price path or a simulated "on-chain" badge into
the fixture-backed UI to look more finished. The submission's claim is that the record will be
on a chain, the hook is designed to make that true, and §6 is how it becomes true. A screenshot
that says otherwise is the failure mode this whole document exists to avoid, and
`records/00-prior-direction-index.md` §4 item 19 is what it looks like when it happens: a
"verified spike" whose mints return `null`.

---

## 8. Rust sketches

**NOT COMPILED ON THIS MACHINE.** There is no `rustc`, no `cargo` and no `cargo-build-sbf` here;
none of the code below has been built, run, or type-checked. It is a design artefact, written to
be implementable, and its error numbers match §3.12. Treat every line as a claim about
*intended* structure, not as a working program.

### 8.1 The cap helper

```rust
// NOT COMPILED ON THIS MACHINE
pub const BPS_DENOM: u128 = 10_000;

/// Maximum admissible resale price in lamports. floor, and for display only:
/// the enforcement path compares products and never divides.
pub fn max_price_lamports(face: u64, cap_bps: u16) -> u64 {
    ((face as u128) * (BPS_DENOM + cap_bps as u128) / BPS_DENOM) as u64
}

/// The check. u128 because face * 20_000 overflows u64 for any face above
/// 2^64 / 20_000.
pub fn check_cap(face: u64, cap_enabled: bool, cap_bps: u16, price: u64) -> Result<()> {
    if !cap_enabled {
        return Ok(());
    }
    let lhs = (price as u128) * BPS_DENOM;
    let rhs = (face as u128) * (BPS_DENOM + cap_bps as u128);
    require!(lhs <= rhs, TicketpathError::CapExceeded);
    Ok(())
}
```

### 8.2 Errors

```rust
// NOT COMPILED ON THIS MACHINE
#[error_code]
pub enum TicketpathError {
    #[msg("Event slug is limited to 32 bytes.")]              SlugTooLong = 6000,
    #[msg("Tiers must be created in order.")]                 TierIndex = 6001,
    #[msg("Only the organizer can do that.")]                 NotOrganizer = 6002,
    #[msg("Only the verification authority can do that.")]    NotVerifier = 6003,
    #[msg("This tier is sold out.")]                          TierExhausted = 6004,
    #[msg("Face value must be positive.")]                    FaceZero = 6005,
    #[msg("The resale cap is out of range.")]                 CapOutOfRange = 6006,
    #[msg("That serial is already issued.")]                  TicketExists = 6007,
    #[msg("A ticket is one indivisible token.")]              AmountNotOne = 6008,
    #[msg("Transfers go through Ticketpath.")]                TransferNotStaged = 6009,
    #[msg("Above the organizer's resale cap.")]               CapExceeded = 6010,
    #[msg("This event does not allow transfers.")]            ResaleDisabled = 6011,
    #[msg("That wallet has not been verified.")]              DestUnverified = 6012,
    #[msg("This ticket is no longer valid.")]                 TicketNotValid = 6013,
    #[msg("Record a gift as a transfer.")]                    PriceZero = 6014,
    #[msg("That wallet already holds the ticket.")]           SelfTransfer = 6015,
    #[msg("Only the current holder can move this ticket.")]   NotOwner = 6016,
    #[msg("The transfer does not match the record.")]         DestMismatch = 6017,
    #[msg("That wallet's verification has expired.")]         VerificationExpired = 6018,
    #[msg("This mint is a Token-2022 mint.")]                 WrongTokenProgram = 6019,
    #[msg("That address is not a Ticketpath ticket.")]        NotATicket = 6020,
}
```

### 8.3 `transfer_ticket`, and the hook that makes it the only door

```rust
// NOT COMPILED ON THIS MACHINE
pub fn transfer_ticket(ctx: Context<TransferTicket>, price: Option<u64>) -> Result<()> {
    let rec = &mut ctx.accounts.ticket_record;
    let policy = &ctx.accounts.event_policy;
    require_keys_eq!(ctx.accounts.seller.key(), rec.owner, TicketpathError::NotOwner);
    require!(rec.status == TicketStatus::Valid as u8, TicketpathError::TicketNotValid);
    require_keys_neq!(ctx.accounts.destination_wallet.key(), rec.owner, TicketpathError::SelfTransfer);
    require!(policy.resale_enabled == 1, TicketpathError::ResaleDisabled);

    if let Some(p) = price {
        require!(p >= 1, TicketpathError::PriceZero);
        check_cap(rec.face_value_lamports, policy.cap_enabled == 1, policy.cap_bps, p)?;
    }
    if policy.requires_verified_wallet == 1 {
        let v = ctx.accounts.holder_verification
            .as_ref()
            .ok_or(TicketpathError::DestUnverified)?;
        require_keys_eq!(v.wallet, ctx.accounts.destination_wallet.key(),
                         TicketpathError::DestUnverified);
        require!(v.expires_at > Clock::get()?.unix_timestamp,
                 TicketpathError::VerificationExpired);
    }

    // 1. the record of the hop, before anything moves
    let seq = rec.hop_seq;
    ctx.accounts.hop.set_inner(HopRecord {
        mint: rec.mint,
        seq,
        kind: if price.is_some() { KIND_SALE } else { KIND_TRANSFER },
        from_wallet: Some(rec.owner),
        to_wallet: Some(ctx.accounts.destination_wallet.key()),
        price_lamports: price,
        occurred_at: Clock::get()?.unix_timestamp,
    });
    // 2. the stage the hook will consume and clear
    rec.pending_active = 1;
    rec.pending_dest = ctx.accounts.destination_wallet.key();
    rec.pending_price_lamports = price.unwrap_or(0);

    // 3. the transfer. The hook runs inside this CPI and is the only writer
    //    of custody state, so a future instruction cannot leave the record stale.
    token_2022::transfer_checked(
        CpiContext::new(
            ctx.accounts.token_2022_program.to_account_info(),
            token_2022::TransferChecked {
                source: ctx.accounts.source_token_account.to_account_info(),
                mint: ctx.accounts.mint.to_account_info(),
                destination: ctx.accounts.destination_token_account.to_account_info(),
                authority: ctx.accounts.seller.to_account_info(),
            },
        ),
        1,
        0,
    )?;
    Ok(())
}

/// The hook. Small on purpose: one yes/no, and then write the custody state.
pub fn execute(ctx: Context<Execute>, amount: u64) -> Result<()> {
    require_eq!(amount, 1, TicketpathError::AmountNotOne);
    let rec = &mut ctx.accounts.ticket_record;
    let policy = &ctx.accounts.event_policy;

    // the account passed as "event policy" must be this ticket's event, and must
    // be the canonical PDA for the slug it claims
    let (expected, _) = Pubkey::find_program_address(&[b"event", &policy.slug], &crate::ID);
    require_keys_eq!(policy.key(), expected, TicketpathError::NotATicket);
    require_keys_eq!(policy.key(), rec.event, TicketpathError::NotATicket);

    require!(rec.pending_active == 1, TicketpathError::TransferNotStaged);
    require_keys_eq!(ctx.accounts.destination_account.owner, rec.pending_dest,
                     TicketpathError::DestMismatch);
    require!(rec.status == TicketStatus::Valid as u8, TicketpathError::TicketNotValid);

    rec.owner = rec.pending_dest;
    rec.transfer_count = rec.transfer_count.saturating_add(1);
    if rec.pending_price_lamports != 0 {
        rec.sale_count = rec.sale_count.saturating_add(1);
        rec.has_last_sale = 1;
        rec.last_sale_price_lamports = rec.pending_price_lamports;
    }
    rec.hop_seq = rec.hop_seq.saturating_add(1);
    rec.pending_active = 0;
    rec.pending_dest = Pubkey::default();
    rec.pending_price_lamports = 0;
    Ok(())
}
```

Two things a reviewer should attack, stated so they are not discovered: the hook trusts
`pending_dest` (which the program wrote, in the same transaction, so the trust is earned); and
the destination-verification check lives in `transfer_ticket`, not in the hook, because the hook
cannot derive the destination wallet's verification PDA from a token account. The hook enforces
*the path*; `transfer_ticket` enforces *the destination*. One gate, one code path, one test
(§6 step 10) that proves the gate is on the path.

### 8.4 The mint at issue time, and the Ed25519 upgrade not taken

```rust
// NOT COMPILED ON THIS MACHINE
// The argument order below is the design intent, not a verified API signature: the
// spl-transfer-hook-interface crate's exact parameters were not read on this machine.
let mint_len = ExtensionType::try_calculate_account_len::<Mint>(
    &[ExtensionType::TransferHook],
)?;
// create_account, then:
transfer_hook_initialize(
    &ctx.accounts.token_2022_program.key(),
    Some(&ctx.accounts.mint_authority.key()),   // authority: the issuer PDA
    None,                                        // hook authority: none, i.e. never changeable
    &ctx.accounts.mint.key(),
    &ctx.accounts.mint_authority.key(),
    &[&[b"issuer", policy.slug.as_ref(), &[ctx.bumps.mint_authority]]],
    &ctx.accounts.token_2022_program.key(),
    ctx.accounts.mint.to_account_info(),
)?;
```

The hook authority is `None` on purpose: the program id is fixed at creation anyway, so giving it
no authority states the fact instead of implying a mutability that does not exist.

The upgrade not taken, recorded because it is the honest fix for §4.2.4: `grant_verification`
could become self-service by requiring an `Ed25519SigVerify` instruction earlier in the same
transaction and reading the Instructions sysvar to confirm it covers the frozen
`verificationMessage()` for this wallet and this nonce. That removes the `verifier` key from the
trust path entirely. It costs one more instruction, a sysvar parse, and about 60 lines, and it
cannot be tested from here, so it is not in the minimum.

---

## 9. Appendix: the SIMULATED mirror, and its real output

### 9.1 `tp_sim.py`

Stdlib only. Save it anywhere and run `python3 tp_sim.py`. It mirrors §2's account fields and
§3's instructions, and it asserts the width of the cap products rather than trusting Python's
arbitrary-precision integers to hide the question.

```python
"""SIMULATED mirror of the Ticketpath on-chain state machine. NOT a Solana program.

Same account fields, same instruction names, same error codes, same integer
arithmetic as docs/ON-CHAIN-DESIGN.md. Python ints do not overflow, so the width
of the intermediate products is checked explicitly rather than by the language.
Stdlib only: `python3 tp_sim.py`.
"""

from dataclasses import dataclass, field
from typing import Optional

U64_MAX = 2**64 - 1
BPS = 10_000


class ProgramError(Exception):
    def __init__(self, spec, detail=""):
        self.code, self.name = spec
        self.detail = detail
        super().__init__("%d %s: %s" % (self.code, self.name, detail))


E_NOT_ORGANIZER = (6002, "E_NOT_ORGANIZER")
E_NOT_VERIFIER = (6003, "E_NOT_VERIFIER")
E_TIER_EXHAUSTED = (6004, "E_TIER_EXHAUSTED")
E_AMOUNT_NOT_ONE = (6008, "E_AMOUNT_NOT_ONE")
E_TRANSFER_NOT_STAGED = (6009, "E_TRANSFER_NOT_STAGED")
E_CAP_EXCEEDED = (6010, "E_CAP_EXCEEDED")
E_RESALE_DISABLED = (6011, "E_RESALE_DISABLED")
E_DEST_UNVERIFIED = (6012, "E_DEST_UNVERIFIED")
E_TICKET_NOT_VALID = (6013, "E_TICKET_NOT_VALID")
E_PRICE_ZERO = (6014, "E_PRICE_ZERO")
E_SELF_TRANSFER = (6015, "E_SELF_TRANSFER")
E_NOT_OWNER = (6016, "E_NOT_OWNER")
E_DEST_MISMATCH = (6017, "E_DEST_MISMATCH")
E_VERIFICATION_EXPIRED = (6018, "E_VERIFICATION_EXPIRED")


def fail(spec, detail=""):
    raise ProgramError(spec, detail)


# --- accounts: field names and order are the tables in the design doc -------

@dataclass
class EventPolicy:              # PDA ["event", slug]
    version: int
    bump: int
    organizer: str
    verifier: str
    slug: str
    cap_enabled: int
    cap_bps: int
    resale_enabled: int
    requires_verified_wallet: int
    ticket_count: int
    tier_count: int
    created_at: int


@dataclass
class TierPolicy:               # PDA ["tier", slug, tier_index]
    version: int
    bump: int
    event: str
    tier_index: int
    name: str
    face_value_lamports: int
    total_supply: int
    issued_count: int
    created_at: int


@dataclass
class TicketRecord:             # PDA ["ticket", mint]
    version: int
    bump: int
    event: str
    tier_index: int
    mint: str
    token_account: str
    owner: str
    issued_to: str
    serial: int
    face_value_lamports: int
    status: int                 # 0 valid, 1 listed, 2 redeemed, 3 revoked
    transfer_count: int
    sale_count: int
    has_last_sale: int
    last_sale_price_lamports: int
    issued_at: int
    redeemed_at: int            # 0 = null
    hop_seq: int
    pending_active: int
    pending_dest: str
    pending_price_lamports: int


@dataclass
class HopRecord:                # PDA ["hop", mint, seq]
    version: int
    bump: int
    mint: str
    seq: int
    kind: int                   # 0 issue, 1 sale, 2 transfer, 3 redeem, 4 revoke
    from_wallet: Optional[str]
    to_wallet: Optional[str]
    price_lamports: Optional[int]
    occurred_at: int


@dataclass
class HolderVerification:       # PDA ["verified", wallet]
    version: int
    bump: int
    wallet: str
    verified_at: int
    expires_at: int
    method: int


@dataclass
class Chain:
    now: int
    policy: dict = field(default_factory=dict)
    tiers: dict = field(default_factory=dict)
    records: dict = field(default_factory=dict)
    hops: list = field(default_factory=list)
    verifications: dict = field(default_factory=dict)
    mints: dict = field(default_factory=dict)
    balances: dict = field(default_factory=dict)

    def create_event(self, slug, organizer, verifier, cap_bps,
                     resale_enabled, requires_verified_wallet):
        assert len(slug.encode()) <= 32
        self.policy[slug] = EventPolicy(
            1, 255, organizer, verifier, slug,
            0 if cap_bps is None else 1,
            0 if cap_bps is None else cap_bps,
            1 if resale_enabled else 0,
            1 if requires_verified_wallet else 0,
            0, 0, self.now)

    def create_tier(self, slug, signer, tier_index, name, face, total_supply):
        p = self.policy[slug]
        if signer != p.organizer:
            fail(E_NOT_ORGANIZER)
        self.tiers[(slug, tier_index)] = TierPolicy(
            1, 255, slug, tier_index, name, face, total_supply, 0, self.now)
        p.tier_count += 1

    def issue_ticket(self, slug, signer, tier_index, serial, holder):
        p = self.policy[slug]
        if signer != p.organizer:
            fail(E_NOT_ORGANIZER)
        tier = self.tiers[(slug, tier_index)]
        if tier.issued_count >= tier.total_supply:
            fail(E_TIER_EXHAUSTED, "%d/%d" % (tier.issued_count, tier.total_supply))
        # mint is a PDA of (slug, tier_index, serial): serial uniqueness is
        # structural, so there is no serial registry to keep in sync.
        mint = "mint:%s:%d:%d" % (slug, tier_index, serial)
        ata = "ata:%s:%s" % (mint, holder)
        self.records[mint] = TicketRecord(
            1, 255, slug, tier_index, mint, ata, holder, holder, serial,
            tier.face_value_lamports, 0, 0, 0, 0, 0, self.now, 0, 1, 0, "", 0)
        self.mints[mint] = {"owner": "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb",
                            "transfer_hook": "TicketpathProgram",
                            "decimals": 0, "supply": 1}
        self.balances[ata] = 1
        self.hops.append(HopRecord(1, 255, mint, 0, 0, None, holder, None, self.now))
        tier.issued_count += 1
        p.ticket_count += 1
        return mint

    def transfer_ticket(self, mint, signer, dest_wallet, price_lamports):
        rec = self.records[mint]
        p = self.policy[rec.event]
        if signer != rec.owner:
            fail(E_NOT_OWNER)
        if rec.status != 0:
            fail(E_TICKET_NOT_VALID, "status=%d" % rec.status)
        if dest_wallet == rec.owner:
            fail(E_SELF_TRANSFER)
        if not p.resale_enabled:
            fail(E_RESALE_DISABLED)
        if price_lamports is not None:
            if price_lamports < 1:
                fail(E_PRICE_ZERO)
            check_cap(rec, p, price_lamports)
        if p.requires_verified_wallet:
            v = self.verifications.get(dest_wallet)
            if v is None:
                fail(E_DEST_UNVERIFIED, dest_wallet)
            if v.expires_at < self.now:
                fail(E_VERIFICATION_EXPIRED, "%s expired at %d" % (dest_wallet, v.expires_at))
        kind = 1 if price_lamports is not None else 2
        self.hops.append(HopRecord(1, 255, mint, rec.hop_seq, kind,
                                   rec.owner, dest_wallet, price_lamports, self.now))
        rec.pending_active = 1
        rec.pending_dest = dest_wallet
        rec.pending_price_lamports = price_lamports or 0
        self.hook_execute(mint, rec.owner, dest_wallet, 1)

    def hook_execute(self, mint, source_owner, dest_owner, amount):
        rec = self.records[mint]
        if amount != 1:
            fail(E_AMOUNT_NOT_ONE)
        if not rec.pending_active:
            fail(E_TRANSFER_NOT_STAGED, "custody move outside the program")
        if dest_owner != rec.pending_dest:
            fail(E_DEST_MISMATCH)
        rec.owner = rec.pending_dest
        rec.transfer_count += 1
        if rec.pending_price_lamports:
            rec.sale_count += 1
            rec.has_last_sale = 1
            rec.last_sale_price_lamports = rec.pending_price_lamports
        rec.hop_seq += 1
        rec.pending_active = 0
        rec.pending_dest = ""
        rec.pending_price_lamports = 0
        self.balances["ata:%s:%s" % (mint, source_owner)] = 0
        self.balances["ata:%s:%s" % (mint, dest_owner)] = 1

    def redeem_ticket(self, mint, signer):
        rec = self.records[mint]
        if signer != rec.owner:          # the fan proves custody at the gate
            fail(E_NOT_OWNER)
        if rec.status != 0:
            fail(E_TICKET_NOT_VALID, "status=%d" % rec.status)
        rec.status = 2
        rec.redeemed_at = self.now
        self.hops.append(HopRecord(1, 255, mint, rec.hop_seq, 3,
                                   rec.owner, None, None, self.now))
        rec.hop_seq += 1

    def revoke_ticket(self, mint, signer):
        rec = self.records[mint]
        if signer != self.policy[rec.event].organizer:
            fail(E_NOT_ORGANIZER)
        rec.status = 3
        self.hops.append(HopRecord(1, 255, mint, rec.hop_seq, 4,
                                   rec.owner, None, None, self.now))
        rec.hop_seq += 1

    def grant_verification(self, slug, wallet, signer, ttl=86_400):
        p = self.policy[slug]
        if signer != p.verifier:
            fail(E_NOT_VERIFIER)
        self.verifications[wallet] = HolderVerification(
            1, 255, wallet, self.now, self.now + ttl, 0)


def max_price_lamports(face, cap_bps):
    """floor(face * (10000 + cap) / 10000). Display only; the check never divides."""
    return (face * (BPS + cap_bps)) // BPS


def check_cap(rec, p, price):
    if not p.cap_enabled:
        return
    lhs = price * BPS
    rhs = rec.face_value_lamports * (BPS + p.cap_bps)
    assert lhs < 2**128 and rhs < 2**128, "u128 bound"
    if lhs > rhs:
        fail(E_CAP_EXCEEDED, "price %d > max %d"
             % (price, max_price_lamports(rec.face_value_lamports, p.cap_bps)))


def markup_bps(price, face):
    """Identical to ticketpath/core/markup.py: half away from zero."""
    n = (price - face) * BPS
    sign = -1 if n < 0 else 1
    q, r = divmod(abs(n), face)
    if r * 2 >= face:
        q += 1
    return sign * q


# ---------------------------------------------------------------------------

def main():
    EV, TV, SELLER, BUYER, STRANGER = "Org111", "Ver111", "W1", "W2", "W3"
    SLUG, FACE, CAP = "fixture-hall-session", 1_000_000_000, 2_500
    chain = Chain(now=1_767_000_000)
    chain.create_event(SLUG, EV, TV, CAP, True, True)
    chain.create_tier(SLUG, EV, 0, "Floor", FACE, 200)
    chain.create_tier(SLUG, EV, 1, "Balcony", 2 * FACE, 1)
    print("EVENT      face_floor=%d face_balcony=%d cap_bps=%d requires_verified=1"
          % (FACE, 2 * FACE, CAP))
    print("CAP PRICE  floor(face*(10000+cap)/10000): floor=%d balcony=%d lamports"
          % (max_price_lamports(FACE, CAP), max_price_lamports(2 * FACE, CAP)))

    serial = [0]

    def fresh(holder=SELLER):
        serial[0] += 1
        return chain.issue_ticket(SLUG, EV, 0, serial[0], holder)

    t = fresh()
    print("ISSUE      ok   mint=%s hop[0]=issue" % t)
    chain.issue_ticket(SLUG, EV, 1, 1, SELLER)
    try:
        chain.issue_ticket(SLUG, EV, 1, 2, SELLER)
    except ProgramError as e:
        print("ISSUE      %d %-22s tier total_supply=1: %s"
              % (e.code, e.name, e.detail))

    print("\n--- arm 0 done / arm A: a custody move the program did not stage ---")
    try:
        chain.hook_execute(t, SELLER, STRANGER, 1)   # what `spl-token transfer` hits
    except ProgramError as e:
        print("BYPASS     %d %-22s %s" % (e.code, e.name, e.detail))
    print("           record.owner=%s transfer_count=%d hop_seq=%d (unchanged)"
          % (chain.records[t].owner, chain.records[t].transfer_count,
             chain.records[t].hop_seq))

    print("\n--- arm B: the cap, exactly at the boundary ---")
    chain.grant_verification(SLUG, BUYER, TV)
    at_cap = max_price_lamports(FACE, CAP)
    for price in (at_cap - 1, at_cap, at_cap + 1):
        m = fresh()
        try:
            chain.transfer_ticket(m, SELLER, BUYER, price)
            print("PRICE %-11d ok    markup_bps=%d owner=%s hop_seq=%d"
                  % (price, markup_bps(price, FACE), chain.records[m].owner,
                     chain.records[m].hop_seq))
        except ProgramError as e:
            print("PRICE %-11d %d %-20s %s" % (price, e.code, e.name, e.detail))
    print("           note: 1249999999 lamports is below the ceiling and still")
    print("           reports markupBps=2500: 1 lamport is 1e-5 bps at this face")

    print("\n--- arm C: the stage is consumed, so it cannot be replayed ---")
    m = fresh()
    chain.transfer_ticket(m, SELLER, BUYER, at_cap)
    try:
        chain.hook_execute(m, BUYER, STRANGER, 1)
    except ProgramError as e:
        print("REPLAY     %d %-22s %s" % (e.code, e.name, e.detail))

    print("\n--- arm D: holder verification ---")
    m = fresh()
    try:
        chain.transfer_ticket(m, SELLER, STRANGER, FACE)
    except ProgramError as e:
        print("DEST       %d %-22s dest=%s" % (e.code, e.name, e.detail))
    chain.grant_verification(SLUG, STRANGER, TV)
    chain.transfer_ticket(m, SELLER, STRANGER, FACE)
    print("DEST       ok   owner=%s transfer_count=%d sale_count=%d"
          % (chain.records[m].owner, chain.records[m].transfer_count,
             chain.records[m].sale_count))

    print("\n--- arm E: a redeemed ticket cannot move ---")
    m = fresh(STRANGER)
    chain.redeem_ticket(m, STRANGER)
    try:
        chain.transfer_ticket(m, STRANGER, BUYER, FACE)
    except ProgramError as e:
        print("TRANSFER   %d %-22s %s" % (e.code, e.name, e.detail))

    print("\n--- arm F: an expired verification is not a verification ---")
    m = fresh()
    chain.grant_verification(SLUG, "W4", TV, ttl=-1)
    try:
        chain.transfer_ticket(m, SELLER, "W4", FACE)
    except ProgramError as e:
        print("EXPIRED    %d %-22s %s" % (e.code, e.name, e.detail))

    print("\n--- arm G: a gift is a transfer with no price ---")
    m = fresh()
    chain.transfer_ticket(m, SELLER, BUYER, None)
    r = chain.records[m]
    print("GIFT       ok   transfer_count=%d sale_count=%d has_last_sale=%d"
          % (r.transfer_count, r.sale_count, r.has_last_sale))

    print("\n--- the trail in wire names (ticket serial 1) ---")
    chain.transfer_ticket(t, SELLER, BUYER, 1_100_000_000)   # sale at +10%
    chain.transfer_ticket(t, BUYER, STRANGER, None)        # gift
    chain.redeem_ticket(t, STRANGER)
    kinds = ["issue", "sale", "transfer", "redeem", "revoke"]
    for h in [x for x in chain.hops if x.mint == t]:
        print("  LedgerEntry kind=%-8s fromWallet=%-6s toWallet=%-6s "
              "priceLamports=%-10s markupBps=%s"
              % (kinds[h.kind], h.from_wallet or "null", h.to_wallet or "null",
                 h.price_lamports if h.price_lamports is not None else "null",
                 markup_bps(h.price_lamports, FACE) if h.price_lamports else "null"))
    r = chain.records[t]
    print("  ResaleStats saleCount=%d transferCount=%d lastPriceLamports=%d "
          "status=%d" % (r.sale_count, r.transfer_count,
                         r.last_sale_price_lamports, r.status))

    print("\n--- arm H: chain-valid implies markup_bps <= cap_bps ---")
    checked = 0
    for face in (3, 999_999_937, 1_000_000_000, 1_600_000_000, 2**40 + 7):
        for cap in (0, 1, 2_500, 3_333, 10_000, 65_535):
            hi = max_price_lamports(face, cap)
            for price in (hi - 1, hi, hi + 1):
                if price * BPS <= face * (BPS + cap):
                    assert markup_bps(price, face) <= cap, (face, cap, price)
                    checked += 1
    print("           %d admitted (face, cap, price) triples, all <= cap" % checked)

    print("\n--- arm I: the converse fails, so markup_bps cannot decide the cap ---")
    face, cap = 1_000_000_001, 3_333
    hi = max_price_lamports(face, cap)
    print("           face=%d cap=%d" % (face, cap))
    for price in (hi, hi + 1):
        admitted = price * BPS <= face * (BPS + cap)
        print("           price=%-11d admitted=%-5s markup_bps=%d"
              % (price, admitted, markup_bps(price, face)))

    print("\n--- arm J: u64 is not wide enough for the cap product ---")
    prod = U64_MAX * (BPS + 10_000)
    print("           face=2^64-1 cap=10000 -> %d" % prod)
    print("           %d x u64::MAX, so the comparison must be u128"
          % (prod // U64_MAX))

    print("\n--- arm K: mass at the cap, which the fixture never shows ---")
    c2 = Chain(now=1_767_000_100)
    c2.create_event("e2", EV, TV, CAP, True, False)
    c2.create_tier("e2", EV, 0, "Floor", FACE, 10)
    m = c2.issue_ticket("e2", EV, 0, 1, "A0")
    holder, prices = "A0", []
    for i in range(200):
        p = (max_price_lamports(FACE, CAP) if i % 10 == 0
             else FACE + (i * 7_919) % (FACE // 4))
        c2.transfer_ticket(m, holder, "A%d" % (i + 1), p)
        holder = "A%d" % (i + 1)
        prices.append(p)
    marks = [markup_bps(p, FACE) for p in prices]
    print("           200 sim resales: max markup %d, min %d, exactly at cap %d"
          % (max(marks), min(marks), sum(1 for x in marks if x == CAP)))
    print("           every hop <= cap: %s" % all(x <= CAP for x in marks))


if __name__ == "__main__":
    main()
```

### 9.2 Output on this machine

Produced by `python3 tp_sim.py`, exit status 0, on 2026-11-07. **SIMULATED.** No cluster was
contacted by this script.

```
EVENT      face_floor=1000000000 face_balcony=2000000000 cap_bps=2500 requires_verified=1
CAP PRICE  floor(face*(10000+cap)/10000): floor=1250000000 balcony=2500000000 lamports
ISSUE      ok   mint=mint:fixture-hall-session:0:1 hop[0]=issue
ISSUE      6004 E_TIER_EXHAUSTED       tier total_supply=1: 1/1

--- arm 0 done / arm A: a custody move the program did not stage ---
BYPASS     6009 E_TRANSFER_NOT_STAGED  custody move outside the program
           record.owner=W1 transfer_count=0 hop_seq=1 (unchanged)

--- arm B: the cap, exactly at the boundary ---
PRICE 1249999999  ok    markup_bps=2500 owner=W2 hop_seq=2
PRICE 1250000000  ok    markup_bps=2500 owner=W2 hop_seq=2
PRICE 1250000001  6010 E_CAP_EXCEEDED       price 1250000001 > max 1250000000
           note: 1249999999 lamports is below the ceiling and still
           reports markupBps=2500: 1 lamport is 1e-5 bps at this face

--- arm C: the stage is consumed, so it cannot be replayed ---
REPLAY     6009 E_TRANSFER_NOT_STAGED  custody move outside the program

--- arm D: holder verification ---
DEST       6012 E_DEST_UNVERIFIED      dest=W3
DEST       ok   owner=W3 transfer_count=1 sale_count=1

--- arm E: a redeemed ticket cannot move ---
TRANSFER   6013 E_TICKET_NOT_VALID     status=2

--- arm F: an expired verification is not a verification ---
EXPIRED    6018 E_VERIFICATION_EXPIRED W4 expired at 1766999999

--- arm G: a gift is a transfer with no price ---
GIFT       ok   transfer_count=1 sale_count=0 has_last_sale=0

--- the trail in wire names (ticket serial 1) ---
  LedgerEntry kind=issue    fromWallet=null   toWallet=W1     priceLamports=null       markupBps=null
  LedgerEntry kind=sale     fromWallet=W1     toWallet=W2     priceLamports=1100000000 markupBps=1000
  LedgerEntry kind=transfer fromWallet=W2     toWallet=W3     priceLamports=null       markupBps=null
  LedgerEntry kind=redeem   fromWallet=W3     toWallet=null   priceLamports=null       markupBps=null
  ResaleStats saleCount=1 transferCount=2 lastPriceLamports=1100000000 status=2

--- arm H: chain-valid implies markup_bps <= cap_bps ---
           60 admitted (face, cap, price) triples, all <= cap

--- arm I: the converse fails, so markup_bps cannot decide the cap ---
           face=1000000001 cap=3333
           price=1333300001  admitted=True  markup_bps=3333
           price=1333300002  admitted=False markup_bps=3333

--- arm J: u64 is not wide enough for the cap product ---
           face=2^64-1 cap=10000 -> 368934881474191032300000
           20000 x u64::MAX, so the comparison must be u128

--- arm K: mass at the cap, which the fixture never shows ---
           200 sim resales: max markup 2500, min 0, exactly at cap 20
           every hop <= cap: True
```

### 9.3 What the output is and is not

- It **is** a demonstration that the state machine in §3 is consistent: the cap boundary is where
  §3.10 says, the hook's refusal leaves the record untouched, the stage cannot be replayed, and
  the theorem about `markupBps` holds over the triples tested.
- It **is not** evidence that a Solana program behaves this way. Token-2022 calling a hook, the
  extra-account wiring, the CPI signer propagation and the account sizes are all still
  UNVERIFIED-FROM-THIS-MACHINE, and §6 is the only thing that changes that.
- It **is not** a market result and must never be quoted as one. Arm K's "20 of 200 at the cap" is
  a property of the sequence the script generates, not of any market.

---

## 10. UNVERIFIED-FROM-THIS-MACHINE

Everything in this table cannot be checked without Agave, Rust, or a deployed program. Each row
names the step in §6 that settles it.

| # | claim | why it is unverified | settles at |
|---|---|---|---|
| 1 | Token-2022 invokes the hook during a transfer CPI, at instruction depth 2 | no runtime here | §6 step 7 |
| 2 | The `TransferHook` extension's program id is immutable after mint creation | source reading only | §6 step 6 |
| 3 | The `ExtraAccountMetaList` seeds are `["extra-account-metas", mint]` | interface convention, no crate on disk | §6 step 9 |
| 4 | A token account's owner is readable at offset 32 of its data by the hook | interface/source reading | §6 step 7 |
| 5 | The mint with a `TransferHook` extension is 151 bytes (not 234) | extension layout arithmetic | §6 step 9 |
| 6 | The `ExtraAccountMetaList` is 74 bytes (not 82) | same | §6 step 9 |
| 7 | `spl-token create-token --transfer-hook` exists in the operator's CLI | no CLI here | §6 step 6 |
| 8 | The exact `Custom(N)` / log-line strings for 6009, 6010, 6012, 6018 | no program to fail | §6 step 12 |
| 9 | The Anchor/SBF toolchain builds the sketch in §8 | no rustc | §6 step 2 |
| 10 | Program deploy succeeds and costs what `solana program deploy` says | no cluster account | §6 step 3 |
| 11 | The faucet's real limit (corpus says 2 requests per 8 hours) | not exercised | §6 step 1 |
| 12 | That `anchor test --provider.cluster devnet` runs the arms against devnet | Anchor feature, untested | §6 steps 4-11 |
| 13 | That a multi-tier event's `tier_index` stays aligned with `Event.tiers` order | a backend invariant, not a chain one | not on chain; a backend test |
| 14 | The devnet rent rate on the day the operator runs this | measured today, and rent is a cluster parameter | §6 step 9 |

Two things that are **not** unverified and should not be re-argued: the rent rate at slot
519,638,900 (measured), and the absence of a toolchain on this machine (`which`, exit 1).

---

## 11. What was cut, and why

The brief says the minimum surface that makes the invariant true, and nothing more. This is the
ledger of the things that were considered and refused, so a reviewer can see the surface was
chosen rather than under-built.

| cut | what it would have bought | why it is out |
|---|---|---|
| a PDA escrow and settlement | the cap binding on real money | it is a venue, not a constraint (§1.3), it rebuilds the marketplace surface the plan forbids, and it is 3x the work |
| a mutable policy plus a change log | mid-event cap changes, key rotation | one more account, one more instruction, and it reopens the raise-sell-lower hole (§2.1) |
| `set_policy` / `set_organizer` | operational flexibility | the same hole, with a smaller surface |
| an on-chain listing/ask layer | the `cap_blocked` census, sale-hazard identification | it is the resale product path the plan forbids; the four fields stay a data request (`F-decision-log.md` D3) |
| an instruction that records refused attempts | a census of cap violations | it turns the wall into a note, it charges the seller for being refused, and it is floodable (§3.11) |
| on-chain `markupBps` | one less computation in the backend | two sources of truth for a derived number, which `CONTRACT-MAP.md` §7.7 already forbids |
| Token metadata (name, image, seat) on the mint | a prettier explorer page | ~300 bytes of rent per ticket for display data the wire contract does not carry |
| Ed25519 self-service verification | no trusted `verifier` key | ~60 lines and a sysvar parse, untestable here (§8.4) |
| pausing / freezing a mint (`PermanentDelegate`, `freeze_authority`) | the organizer could stop trading | it is a clawback, it contradicts "the terms cannot change", and the corpus records "claw back" as a pitch trap |
| moving to `NonTransferable` instead of a hook | the strongest possible refusal, for free | it forbids **all** transfers, so it also forbids the capped resale the product needs to record. It is the right mechanism for a different product (the one the prior corpus was building) |

The last row is the one worth saying out loud on camera: the earlier direction in this repo was
`NonTransferable`, which refuses every transfer and therefore cannot produce a resale record at
all. Ticketpath needs the record, so it needs transfers to succeed under a ceiling, which is
what a hook plus a staged price buys and what `NonTransferable` structurally cannot.

---

## 12. Relationship to `docs/ON-CHAIN-FOR-LAPTOP.md`

A sibling document with a different position exists in this repo, written earlier the same
evening. It is not edited here and it is not deleted. The two differ on three things, and the
operator, not this document, decides between them. Where they disagree, this one is the later
statement; where the sibling is better, it says so below.

### 12.1 What the sibling proposes

Same headline claim (the program owns the custody hop, the cap is a program check, the record is
a PDA), and a larger surface: `Config`, `Event`, `Tier`, `Ticket`, `Listing` (escrow),
`ResaleRecord`, `Verification`, `Nullifier`; thirteen instructions including
`list_for_resale`, `execute_resale`, `cancel_listing`, `set_cap`, `close_event`,
`revoke_verification`; and a hook that refuses any destination that is not the escrow account of
an active listing. It has runbook steps and negative tests of its own.

### 12.2 The three divergences, named

1. **Escrow and a listing surface (the sibling has it, this document does not).** The sibling's
   hook is only satisfied by an escrow-routed transfer, so its `list_for_resale` and
   `execute_resale` are load bearing: without them no ticket can move at all. That is a
   coherent design and it is what puts the cap on real money, which §4.2.1 says is the only way
   to bind a price. It is also a listing, a buy and a checkout in the program, which plan item
   (a) says the product does not have. Both positions are defensible; they are not compatible.
   If the operator wants the escrow, the sibling's §3.5 and §4 are the specification and this
   document's §3.4 becomes the escrow-free fallback.
2. **Sybil resistance (the sibling has it, this document does not).** The `Nullifier` PDA plus
   `max_per_wallet` in the hook is the only mechanism in either document that addresses the
   actual scalper behaviour, which is many wallets rather than one high price. §4.2.6 says why
   this document leaves it out and what it would need. If the submission is going to claim
   anything about bots, take the sibling's §3.7, §3.8 and hook check 4, and be explicit that the
   identity behind the nullifier is proven off-chain, as the sibling's §6 already says.
3. **A mutable cap (the sibling has it, this document refuses it).** `set_cap(event, cap_bps,
   effective_at)` is more usable and it reopens the hole §2.1 closes: an organizer who raises the
   cap, sells, and lowers it again. The sibling mitigates it by re-checking the cap at execution
   and by stamping `effective_at`; that mitigation is only as good as the record of when the cap
   changed, which is why it also needs a policy history this document does not have. Pick one. A
   fixed cap is a stronger claim; a movable cap is a real product.

### 12.3 What this document takes from it

Nothing from it was copied, but two of its positions are better than the first draft here and are
now reflected above: that the hook must be the thing that makes an off-platform transfer
impossible rather than merely detectable, and that a hook that never sees lamports cannot check a
price, so the price must arrive through program state. Both are in §1.3 and §3.9.

### 12.4 The one thing both documents agree on, and it is the one that matters

The API cannot enforce a cap, because an API cannot prevent a transfer it is not asked about.
Everything else is a choice about how much program to build.

---

## 13. Carried over from the superseded sibling

**Why this section exists.** The operator decided the three divergences named in §12 on
2026-11-07, and all three went to this document: `records/F-decision-log.md` D6, with the
reasoning in `records/ON-CHAIN-RECONCILIATION.md`. `docs/ON-CHAIN-FOR-LAPTOP.md` is now a short
pointer, not a second design. Three pieces of that document were not in this one and are carried
here unchanged in substance, because a superseded design is marked and not removed, and because
losing them would make this document weaker than the draft it replaces. Nothing else from it was
carried: the escrow, the nullifier and the mutable cap are rejected, and §4.2, §5 tier (c) and §11
already record what their absence costs and what each would need.

### 13.1 The program has no pricing responsibility

The program does not price anything, does not know what a ticket is worth, and does not hold money
for the organizer. Pricing is the engine's job; the program is the constraint system and the
ledger. That split is the whole reason the on-chain surface can stay at nine entry points: the
moment the program needs an opinion about value, it needs the model, the data and the fallbacks,
and it stops being a constraint.

### 13.2 The verification gate must fire inside the transfer, not before it

Verified-wallet enforcement that is checked before the transaction lands is a race: the check and
the transfer are two events and something can change between them. Inside the hook they are one
instruction, so either both happen or neither does, and the refusal cannot be separated from the
transfer it refuses. This is the same argument as §3.4's write-the-hop-then-CPI ordering, applied
to the gate rather than to the record, and it is why the gate is a hook check (§3.9) and not a
backend precondition.

### 13.3 The backend handoff, as the sibling stated it

Deploying the program does not by itself make `Ticket.transferRestricted` true or populate
`LedgerEntry.signature` and `.slot`; §7.2 lists what changes and how the backend learns it. The
operator's environment for the day it does, using the variable names the backend already reads
(`docs/BACKEND.md`):

```bash
export TICKETPATH_CLUSTER=devnet
export TICKETPATH_PROGRAM_ID=<PROGRAM_ID>     # the id step 3 printed; never a placeholder
export TICKETPATH_RPC_ENABLED=1
```

**[Corrected 2026-11-08T07:45Z: `TICKETPATH_RPC_ENABLED=1` does not make the console re-read the
chain. The adapter opens no socket on any flag, and the page now says so in its own sentence ("A live
re-read is not implemented in this build"). The variable is still read by the adapter's configuration
and still reports `rpcEnabled`, so the line is kept as the environment a future build would need, not
as a switch that works today.]**

Two code paths must change in the same pass, and neither is written yet:
`ticketpath/adapters/rpc_adapter.py` must read the mint account, deserialize its extensions and
confirm the `TransferHook` program id equals `TICKETPATH_PROGRAM_ID` before returning
`enforced: true`; and `ticketpath/adapters/ledger_adapter.py` needs the `getProgramAccounts` read
over `HopRecord` PDAs that §6 step 11 walks by hand. Until both exist, the honest values remain
`transferRestricted: false` and null provenance, which is what the backend returns today (§7.4).

---

## 14. The region-aware policy layer (2026-11-08)

**What this section is.** The design in §1-§13 has one cap per ticket record, a number an organiser
sets. That is the wrong shape once the same platform sells into jurisdictions whose law differs.
`records/F-decision-log.md` Q4 asked the question, and **D11 decides the direction** for this
region-cap work; the mapping from a jurisdiction to a policy is **not** built into `cap_hook`, which
records the code and does not interpret it (D16), and the record's `[u8; 2]` can name a nation, not a
subdivision, so any reconciliation is nation-level only. This section records the on-chain half of
D11's answer. The full design is `records/REGION-CAPS-DESIGN.md`; the law
behind every row is `records/findings/33-a-region-cap-law.md`.

### 14.1 The record, and the one instruction §3.12 does not have

`programs/region_gate/` is a **separate, local-validator-only crate, and it is parked**: built,
compiled once, run once on a disposable local validator and deployed nowhere else, not in the
transaction path, kept in the tree as the design record of
where the check could move if the table ever has to be enforced by something the platform cannot
rewrite (`programs/region_gate/README.md`). It is not `cap_hook`, and the proven devnet program
`5EJ1GU3M4vn…` is untouched by it. Its record is §2's record with three fields added:

```
base_lamports: u64        // the cap BASE, not necessarily the tier face (§14.2)
jurisdiction: [u8; 2]     // the binding nation, ISO-3166-1 alpha-2; ZZ = unresolved
                          // two bytes cannot hold CA-ON or AU-NSW: this field is nation-level
policy: u8                // 0 capped, 1 monitored, 2 unresolved
law_version: u32          // the rules-table generation the policy was stamped from
authority: [u8; 32]       // the only signer that may stage a price, change status or tighten
```

and one instruction, `TightenPolicy { cap_bps, jurisdiction, law_version }`, which is the only way a
policy may change after a ticket is issued. It is **monotone**: it may lower a cap, and it may move
`monitored`/`unresolved` to `capped`; it refuses to raise a cap or to remove one, with `6042`. The
reason is §2.1's: the chain cannot tell a repealed law from an organiser who raises a cap, sells, and
lowers it again. A tightening is a legal obligation and is representable; a loosening is not applied
to an issued ticket, and the event record carries the off-chain `relaxed_at`/`relaxed_to` instead.

`policy = 2` (`unresolved`) exists so that "we could not establish the law" is a distinct state on
the chain from "the law does not cap". Both admit any staged price, and only one of them permits the
platform to say resale is lawful there. The v2 program in `programs/cap_hook/` implements
`jurisdiction` and `policy` in its source and has run on a local validator **[corrected
2026-11-08T11:20Z: this sentence read "has run only on a local validator", and v2 is also deployed
on devnet under the id `records/onchain-v2-devnet.json` records, so "only" is no longer true. The
refusal itself is unchanged]**: it accepts `0` and
`1` and refuses `2` with `6023`, and its `ZZ` means "unspecified". Adding `2` is additive and is
what a merge would carry over; until then the parked `programs/region_gate/` is the only program
that assigns it.

### 14.2 The base is part of the law

The predicate is unchanged from §3.10: `price * 10_000 <= base * (10_000 + cap_bps)`, in `u128`,
no division, inclusive at the cap. What changes is what `base` means. Ireland and Ontario cap over
the total price the first buyer paid, so the base includes the fees; Victoria and Quebec cap over the
face with fees excluded; New South Wales caps at face plus the fees actually paid, counted at no more
than 10% of face; Western Australia caps at 110% of a base that includes the booking fee. The
program cannot tell one base from another, because the field is just a number. The intended guarantee
is procedural: one creation path computes the base from the law's basis and the event record keeps the
split (`faceLamports`, `feeLamports`) and the receipts. **That split does not exist yet.** There is no
fee field on the event row, so every `face_plus_fees` law is currently applied with the base equal to
the tier face, which is *stricter* than the law and refuses a sale that properly includes the first
buyer's fees. Adding `feeLamports` to the event row and a test that the base equals face + fee to the
lamport is the next step, and until it exists this paragraph is the one that says the gap is open.
**There is also no chain-level guarantee, and this paragraph says that too.**

### 14.3 What the wire gains, and what it must not claim

`lib/types.ts` is unchanged; the backend serves additive keys beside the contract's own
(`records/REGION-CAPS-DESIGN.md` §11, `records/CONTRACT-MAP.md` §7.9): `jurisdiction`,
`resalePolicy`, `resalePolicyReason`, `lawTableVersion`, `lawAsOf`, `lawBasis`, and `enforcedCap`
(`enforcedBaseLamports`, `enforcedCapBps`, `enforcedCeilingLamports`, `bindingRule`,
`platformCapBps`, and `enforcedCapByTier` for the multi-tier case, because a cap is a multiple of
the ticket's own face). `bindingRule` is `law` or `platform` and exists so a screen never attributes a
product decision to a law, or a law to the product. The enforced ceiling is the stricter of the two
in lamports — not the smaller basis-point number, because 500 bps over face + fees is looser than
1000 bps over face.

### 14.4 Error numbers: three blocks, and none of them may be renumbered

| block | owner | meaning |
|---|---|---|
| 6000-6020 | §3.12 | the original design's codes; §3.10's `6010` is the cap refusal |
| 6021-6028 | the v2 program in `programs/cap_hook/` | `E_BELOW_FLOOR`, `E_BAND_UNSATISFIABLE`, `E_POLICY_INVALID`, `E_FORECAST_EXISTS`, ... |
| 6040-6043 | `programs/region_gate/` | `6040 NotAuthority`, `6041 PolicyInvalid`, `6042 PolicyLoosens`, `6043 JurisdictionCode` |

The gap between 6028 and 6040 is deliberate. A number that means one thing in one program and
another thing in the next is not branchable by a client, and a log is not evidence if its number is
ambiguous.

### 14.5 What was verified, and where

Eleven legs on a real `solana-test-validator`, as real transactions with their own signatures:
`PASS 11/11`, in `records/findings/34-region-caps-build.md` and reproducible with
`python3 tools/region_local_proof.py`. Those legs are `programs/region_gate/`'s, and the crate is
parked: they are the record of what the policy layer would enforce, not of anything in the
transaction path. Not verified on devnet, and not intended to be: this is a local proof of the
policy layer, and the devnet artefact in `records/devnet-artefacts.json` describes the v1
cap-only program.

**[Corrected 2026-11-08T11:20Z. This paragraph ended "and v2 has run only on a local
validator". That was true when written and is false now: v2 is deployed on devnet under its
own id, `Bebo55oe…`, and `records/onchain-v2-devnet.json` is that deploy's record. The crate
this paragraph is about, `programs/region_gate/`, is still parked and deployed nowhere, so the
claim the paragraph exists to make is unchanged.]**

## 15. The artist fee at checkout (2026-11-08)

The product sentence is "the artist gets a share of every resale". Feature 5 was specified as a
Token-2022 `TransferFeeConfig`, and that is dead: at `decimals = 0` with `amount = 1` the token program
**ceils** the fee, so every rate from 1 to 9999 bps withholds the whole ticket and pays the buyer
nothing. That is measured on four throw-away validators in
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md`, with the RPC objects quoted, and the
decision to ship no token fee is `D15` in `records/F-decision-log.md`. What follows is the other
mechanism, built and measured: **a lamport fee, paid by the seller, in the same transaction as the
move.** A token fee is a fraction of a token, and this mint's tokens are indivisible; a lamport fee is a
fraction of a price, which is what a share of a resale actually is.

### 15.1 The sale: three instructions, one transaction, two signers

```
[0] cap_hook  SetPendingPrice   accounts [issuer (signer), record (writable), mint]      data [2, price u64]
[1] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, fee u64]
[2] Token-2022 TransferChecked  accounts [source, mint, destination, seller (signer),
                                          record, hook program, extra-account-metas]     data [12, 1, 0]
```

One blockhash, one signature set, so a failure in any leg reverts all three: an unpaid fee cannot leave
a moved ticket, and a refused sale cannot leave a paid fee. The fee leg is omitted entirely when the
computed fee is zero — a payment of nothing is not a payment, and a 0-lamport instruction is
indistinguishable in a signature from a fee that was meant and failed to move.

**Two signers, and why that is a fact rather than a choice.** `SetPendingPrice` is authorised by
`record.authority` — `checked_record_for_write` requires `record.authorises(authority)`, which is strict
equality with the field — and that key is the mint authority, the issuer. The seller signs the System
transfer (its own lamports) and the token transfer (it is the source account's owner). So the checkout's
sale transaction is co-signed: the venue stages the price, the seller pays and moves. A sale signed only
by the seller does not exist under the v2 program: the compiled message would carry a signature slot
for the issuer that the seller cannot fill, so it is rejected before any instruction executes — and a
stage that named the seller as its authority would instead be refused `6026`, because
`checked_record_for_write` compares the signer with the record's own `authority` field.

**The seller needs lamports, not just a ticket.** The fee leaves the seller's balance at sale time, so a
seller who holds a ticket and no SOL cannot resell: the sale fails whole. That is the sharpest product
consequence of this design and it is measured, not inferred — the underfunded leg of
`tools/artist_fee_proof.py`.

### 15.2 The arithmetic, and why it rounds down

```
fee = price_lamports * fee_bps // 10_000          integers only, no float anywhere
```

Floor, not ceiling. A ceiling would take a whole lamport on a 1-lamport sale — 100% of it — which is the
same defect that makes the token fee unusable, one unit lower down. Floor never charges more than the
stated percentage; the price of that is rounding to zero (19 lamports at 500 bps pays 0). `fee_bps` is a
property of the event, bounded at 10 000, and `fee <= price` holds for every accepted input by
construction rather than by luck.

### 15.3 What the fee binds, and what it does not

**It binds only sales this app builds.** The chain does not force the fee. The reasons, in order of how
much they matter:

1. The hook never looks at the fee. A transaction can stage a price, move the ticket and pay the artist
   nothing, and the hook admits it. Nothing in `programs/cap_hook` mentions lamports moving between
   wallets.
2. A staged price is not tied to the transaction that will consume it. The staging is a value in the
   record; the next admitted transfer consumes it, whoever builds that transfer. So the issuer stages
   once, and any holder can then move the ticket fee-free. The staging is consumed, so the ride costs the
   issuer one staging, not a permanent door — but it is a door.
3. The fee is charged on the **staged number**, which is the number the cap is enforced against. Whether
   the buyer actually paid the seller that price is settled off chain, in our own checkout, and the chain
   has no view of it. A seller could agree a private price and stage a lower one; the fee follows the
   staged number. **And the amount is the seller's choice because the staged price is:** there is no
   floor in this build, so at 500 bps any price under 20 lamports pays nothing, the fee leg is omitted,
   and the sale still lands. The same arithmetic that makes 19 lamports a rounding credit makes it the
   cheapest evasion, and it never leaves the app. A `band_low` on the record, or a checkout refusal
   below some fraction of face, is the obvious next step and is not built.

What the chain *does* force, on a record whose authority is the issuer, is that no ticket moves at all
without the issuer's signature on a stage instruction. So a sale cannot leave the venue without a venue
signature — that is the cap behaviour described in
`records/findings/36-transfer-fee-on-a-one-unit-ticket.md` §5.1, and it is what makes "the fee is charged
by the checkout" a real statement rather than a policy promise. It is not the same statement as "charged
by the chain", and no screen or README may make the second one.

### 15.4 The stronger variant, written down and not built

A hook that reads the instructions sysvar (`solana_program::sysvar::instructions::load_instruction_at`)
can find the System `Transfer` in the same transaction and refuse unless it pays the artist `fee_bps` of
the staged price. That would make the fee a condition of the move rather than a feature of our client,
and it is the only way the chain can compel it. It is **not built**, and these are the reasons:

- The hook needs the artist's wallet and the rate at hook time. Neither is in the record today
  (`face u64, cap_bps u16, pending_price u64, status u8, band_low u64, jurisdiction [u8;2], policy u8,
  held_since_unix i64, authority [32]`), so a fee account would have to exist per mint, adding a writer,
  an authorisation rule and a migration.
- Every sale's transaction shape becomes part of the program's interface. A marketplace or a wallet that
  routes transfers would have to build the exact instruction a hook it cannot inspect expects, and a
  transaction that batched the fee differently (two artists, a split, a fee already withheld elsewhere)
  would be refused.
- The instructions sysvar is a runtime-provided account whose index must be verified, and getting that
  wrong is a bypass rather than a bug: a hook that reads the wrong instruction attests to something it
  did not check.
- It does not solve (3) above. The hook can check that *some* transfer paid the artist the fee on the
  staged price, not that the staged price was what the buyer paid.

The decision to leave it out is recorded in `records/F-decision-log.md` (`D26`), and the reason it is
written down here rather than left out is that the alternative is a reader concluding the chain enforces
this fee, which it does not.

### 15.5 What is at the checkout today

- `market_swarm/artist_fee.py` — the policy, the arithmetic, the fee leg and the order of the three
  instructions. Pure: no key, no socket, no float.
- `market_swarm` the option — an event may carry `artist_fee: {artist_wallet, fee_bps}`; absent, the
  harness behaves exactly as it did, and a sale is two instructions with one signer. With it on, the
  fee is charged on **resales**: a primary sale through the harness is the house selling the artist's
  own stock at face, so it pays no fee and its row records the event's rate with `fee_lamports` 0.
  `plan` prints the rate and the artist wallet for an event that has them.
- `tools/artist_fee_proof.py` — the local-validator proof, and
  `records/findings/42-artist-fee-at-checkout.md` the finding that quotes it.
- Not built: the `ticketpath` checkout program in §3.4 (`transfer_ticket`) is still a design, so "the
  app" that builds this transaction today is the harness's gateway, not a deployed product.
- Not built: the instructions-sysvar hook of §15.4.

### 15.6 What this document does not claim

No fee is charged on devnet or anywhere public, because nothing was published. The fee arithmetic is
tested off chain against the validator's own behaviour, and the transaction shape is measured on a local
validator only. The artist wallet in a local run is a throw-away key, so no number here is a statement
about any real artist's revenue.

## 16. The flip tax at checkout (2026-11-08)

Feature 7 was specified as a transfer fee into a pool, rebated on how long the holder held. The fee
half is dead for §15's reason, and the rebate half is still not built: `ClaimRebate` (tag 7) is absent
from `lib.rs` and appears there and in `state.rs` only as prose, its two error codes `6027` and `6028`
are declared in `programs/cap_hook/src/error.rs` and raised by nothing, and `["rebate-pool", mint]` is
a seed that `state.rs::rebate_pool_seeds` derives and no instruction uses. What follows is the other
mechanism, built and measured: **a lamport tax, paid by the seller, in the same transaction as the
artist fee and the move**, priced off the hold clock the hook itself writes. `D27` in
`records/F-decision-log.md` is the decision; `records/findings/43-flip-tax-at-checkout.md` is the
measurement.

### 16.1 The sale: four instructions, one transaction, two signers

```
[0] cap_hook  SetPendingPrice   accounts [issuer (signer), record (writable), mint]      data [2, price u64]
[1] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, fee u64]
[2] System    Transfer          accounts [seller (signer, writable), artist (writable)]  data [2, tax u64]
[3] Token-2022 TransferChecked  accounts [source, mint, destination, seller (signer),
                                          record, hook program, extra-account-metas]     data [12, 1, 0]
```

Leg [1] is the artist fee and exists only when the event names one; leg [2] is the flip tax and exists
only when the event's tax is on **and** the computed tax is above zero. Either leg can be absent, so the
same sale is two, three or four instructions, and the transaction is still one blockhash and one
signature set: a failure in any leg reverts all of them. The tax sits last before the move because both
payments belong between the instruction that authorises the price and the instruction the hook checks.

Two separate transfers to the same wallet rather than one summed transfer: the fee and the tax are
different rules with different rates and different rows, and a single leg would make the dataset's
`fee_lamports` and `flip_tax_lamports` a split of one number nobody could check against either rate.

### 16.2 Where the age comes from: the record's clock, and three facts about it

The rate is a function of the hold, and the hold is the chain's answer, not the seller's. The hook
writes `held_since_unix = Clock::get()?.unix_timestamp` into the record in the same step that consumes
the staged price (`lib.rs`, step 7 of `execute`), so the first instruction of the sale can be preceded
by a read of the value the last admitted transfer wrote. `market_swarm/flip_tax.py` decodes that field
at byte 30 of the 70-byte `["record", mint]` account; `market_swarm/tests/test_flip_tax.py` reads
`ticketpath/onchain/v2.py`'s layout and fails if the offset or the record length moves on either side.

Three facts a screen or a README would otherwise get wrong:

1. **It is the mint's clock, not the holder's.** The record is per mint, so the value is the time of
   the last admitted transfer of *any* seat of that event: one holder's sale resets every other
   holder's clock. It is a seller's own hold only where one wallet holds the mint at a time, which is
   the design's mint (`supply = 1`, §3.4). The harness runs **one mint per event carrying the event's
   whole supply** -- measured, the sale mint of the proof run holds eight seats for one seller -- so
   there the number is the event's clock and not the seller's. `max_holdings` limits units per agent
   and does not give a holder a clock of its own. A per-holder clock is a different account layout,
   and this document does not pretend to have it.
2. **`0` means unknown, not "held forever".** `InitializeRecord` writes 0 and a v1 metas list (record
   read-only) leaves it at 0 for good. A record's 0 is charged the **full** rate, because reading it as
   1970 would make an unset field the cheapest way out of the tax; this is the mirror image of the
   rebate, which refuses to *pay* on an unknown hold rather than guessing (`6027`).
3. **A clock that went backwards clamps to zero seconds**, and zero seconds is the full rate. A
   disagreement about the time cannot buy a discount. The Rust clamps the same way, in
   `state.rs::held_seconds`.

### 16.3 The schedule, and why it rounds down

The default schedule is the operator's sentence: 15% of the sale price while the hold is under an hour,
falling linearly to 0% at 30 days. In integers, with `full = 1500 bps`, `t1 = 3 600 s`, `t0 = 2 592 000 s`:

```
held <= t1            rate = full
t1 < held < t0        rate = full * (t0 - held) // (t0 - t1)
held >= t0            rate = 0
tax  = price * rate // 10 000
```

At exactly `t1` the flat branch and the linear branch give the same number, so "under an hour" and
"falling from an hour" are not two readings that disagree: the line starts at the full rate. The
division floors, for §15.2's reason: a ceiling charges above the stated rate, and its worst case is 100%
of a 1-lamport sale. The cost of flooring is that the rate reaches 0 shortly before the stated zero
point (`full * (t0 - held) < t0 - t1` floors to 0, which happens at `held >= 2 590 275`, 1 725 seconds
or 28 minutes 45 seconds short of 30 days), and the zero-point boundary itself is asserted at exactly
0. `zero_hold_seconds` must be greater than `full_hold_seconds`, because a curve that ends before it
starts has no falling segment and the division would be by zero or by a negative span. The schedule is per event:
`flip_tax.schedule.{full_bps, full_hold_seconds, zero_hold_seconds}`, each optional.

### 16.4 The toggle, the recipient, and the config

`flip_tax` is an optional per-event block, **off by default**: absent means no tax and the event behaves
as it did before the field existed. A block without `"enabled": true` carries a policy that is off. Two
things enforce it and neither is a caller remembering to check: the checkout asks `enabled` before it
reads the record or builds a leg, so a disabled policy never reaches the builder on the shipped path,
and `market_swarm.flip_tax.sale_instructions` refuses a disabled policy outright, so a second caller
cannot charge one by calling the builder directly.

The money goes to the artist wallet. A block may omit `artist_wallet` and inherit the event's
`artist_fee` wallet; a block that names a *different* wallet is a `ConfigError`, because one event has
one recipient and two would be a decision, not a default. `"artist_wallet": null` is refused rather
than read as an omission, because a field somebody wrote is not a field they left out. A config
whose `artist_fee.fee_bps + flip_tax.schedule.full_bps` exceeds `10 000` is refused too, **on an
enabled block**: the sum is what the seller pays, and a take above 100% of the price means the seller
pays to sell. A disabled block with a large rate is accepted, because a policy that charges nothing
cannot overcharge.

Charged on **resales only**, like the artist fee: a primary sale through the harness is the house
selling the artist's own stock at face, which is not a flip.

### 16.5 What the tax binds, and what it does not

**Binds only sales this app builds.** The hook has no instruction and no check that mentions lamports
between wallets. A transaction can stage a price, move the ticket and pay no tax, and the hook admits
it; finding 42's free-ride leg (§4, leg 8) is the measured form of that for the artist fee, the
mechanism is the same one, and **no bypass is measured for the tax itself** (finding 43 §8) because the
tax rides in the same transaction as the fee and would be skipped by the same transaction. What the chain does force, on a v2 record whose authority is the issuer, is that no ticket
moves without the issuer's signature on a stage, and the checkout is what prices the stage. That is the
same sentence as §15.3, and it is the whole of the claim.

**The rate is on the staged price, not on lamports that moved.** The chain enforces the cap against
`pending_price_lamports` and has no view of what the buyer paid. A private price below the staged one
moves the tax down with it, and there is no floor in this build, so a staged price low enough makes the
tax round to zero and the leg is omitted. Choosing whether a sale below some fraction of face should be
refused is a product decision this build does not make.

**A clock the seller can move is not a clock.** The seller signs the move, not the record write: the
hook writes `held_since_unix` from the program's own `Clock`, so nothing in the transaction shape lets a
seller claim an age. What the seller *can* choose is the staged price, which is §16.5's second point.

**A hook that required the transfer is not built**, for §15.4's four reasons, unchanged: the hook would
need the recipient and the schedule at hook time (neither is in the v2 record), every sale's transaction
shape would become part of the program's interface, the instructions sysvar's index has to be verified
or the check attests to nothing, and it still cannot prove the buyer paid the staged price.

### 16.6 The refund-to-holders pool: documented, not built

The alternative use of the tax is to accrue it to holders who did not flip instead of only to the
artist. It is named here and deliberately absent from the code, because the two halves ship separately
or not at all, and a half-built one is a number in a row that no instruction can pay:

- a pool lamport account per mint, owned by `["rebate-pool", mint]` -- a lamport account and not a
  token account, because the tax is lamports and the token-account framing belongs to the dead
  `TransferFeeConfig` route; `state.rs::rebate_pool_seeds` derives the address and no instruction
  creates or funds it;
- `ClaimRebate` (tag 7), absent from `lib.rs`, with `6027` (`E_REBATE_NOT_DUE`) and `6028`
  (`E_REBATE_UNAVAILABLE`) declared in `error.rs` and raised by nothing;
- the claim rule, which is already written as pure functions in `state.rs`: `rebate_bps(held)` and
  `rebate_lamports(pool, held)`, with `HOLD_FULL_SECONDS = 60` and `REBATE_FEE_BPS = 1500` and a
  docstring saying the 60 is the demo's number so a rebate is observable inside one bounded validator
  run. **That constant is not this chapter's schedule** and the two must not be read as one: this
  chapter's full-hold point is 3 600 seconds and its zero point 2 592 000 seconds, both configurable,
  and the hook's 60 is a curve the chain does not yet use.

### 16.7 What is at the checkout today

- `market_swarm/flip_tax.py` — the schedule, the assessment, the record-field decoder and the leg, and
  the order of the instructions. Pure: no key, no socket, no float.
- `market_swarm` the option — an event may carry `flip_tax: {enabled, artist_wallet?, schedule?}`;
  absent, the harness behaves exactly as it did. `plan` prints the state, the rate and the two instants.
- The ledger carries `flip_tax_lamports`, `flip_tax_bps` and `held_seconds` per row, and
  `market_swarm/datasets.py` runs the ten tax checks listed in finding 43 §5.1, which is also where
  the builder's refusals are collected. What it cannot check is the *schedule*: the
  header carries no event-level policy, so a row whose tax agrees with its own rate verifies even if
  that rate is not the event's. Same gap as the artist fee's, stated at finding 42 §8, and the same
  fix (the policy in the header).
- `tools/flip_tax_proof.py` — the local-validator proof, and
  `records/findings/43-flip-tax-at-checkout.md` the finding that quotes it.

### 16.8 What this document does not claim

No tax has been charged on devnet or anywhere public, because nothing was published. The hold clock is
the validator's wall clock, so a bounded local run cannot manufacture a 59-minute, one-hour or 30-day
hold: the boundary legs pass the age in as an input and measure the instruction set and the money on
chain, while the rate-for-age curve is measured as a pure function. The artist wallet in a local run is
a throw-away key, so no number here is a statement about any real artist's revenue or any real
platform's fee policy.

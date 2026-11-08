# `cap_hook` — the resale-cap transfer hook

A native Rust Solana program (no Anchor) that Token-2022 calls inside every transfer of a
hooked ticket mint, and that refuses the transfer when the price **the record's authority
staged** is above the ticket's cap or below its floor. It is the on-chain half of
`docs/ON-CHAIN-DESIGN.md` §1.3, §3.9 and §3.10, built to the scope `records/F-decision-log.md`
D6 sets, with the v2 additions of MD3 (floor, jurisdiction, policy, hold clock) and MD4 (fee
policy).

Two qualifiers belong in that first sentence, because the program is weaker than a cap on a
*price*:

- **The price is staged, not paid.** The hook never sees money. It reads a number from a record
  account and refuses the token transfer if that number is outside the band. There is no escrow,
  no settlement and no listing (D6 rejects all three), so a party that stages a price and then
  does not honour it has not broken anything this program can see.
- **Only the record's authority can stage it, and that authority is the mint authority.** Since
  the v2 review (`records/findings/37-program-v2-review-fixes.md`) tags 2 and 3 require the
  record's authority to sign, so a stranger cannot make a price admissible or freeze a ticket.
  What remains is the issuer's own discretion: the cap is a rule the *issuer* commits to, not
  one the protocol imposes on them. The part the chain enforces is that the rule, once written,
  cannot be changed and cannot be applied to a price somebody else chose.

Source, four files, and the split is the layout:

| file | what it owns |
|---|---|
| `src/lib.rs` | the instruction wire format, the account lists, the hook, the log lines |
| `src/state.rs` | the account layouts, the PDA seeds, every predicate the program branches on |
| `src/error.rs` | the error numbering, one name per number, no gaps renumbered |
| `src/tests.rs` | the unit tests: boundaries, layout, policy branch, authentication, clock, rebate curve |

The client half of the same wire format is `ticketpath/onchain/v2.py`: instruction builders and
account lists for tags 0..6, decoders for the four account kinds, the mint-authority reader, and
PDA derivation. `tests/test_onchain_v2.py` reads the Rust sources and compares them with that
module, so a field or an account added on one side without the other is a failing test.

History, because the two versions are on different clusters and the difference matters:

- **v1** was deployed to devnet on 2026-11-07, program
  `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, and exercised there. The measurements, the
  failures and the two signatures either side of the cap boundary are in
  `records/findings/18-onchain-install-and-test.md`, and the public record is
  `records/devnet-artefacts.json`. That program and that file are frozen: nothing in this
  repository deploys, upgrades, signs or edits either of them. **v1 has the tag 2 / tag 3 hole**
  this review found and fixed here: its `SetPendingPrice` and `SetStatus` take no signer, and they
  cannot be patched, because an immutable deploy has no upgrade path. What the proven devnet
  refusals show is therefore the price predicate on a price the deploy key chose, not a price a
  stranger was kept from choosing.
- **v2** has only ever run on a local `solana-test-validator`, under a keypair of its own. Its
  record is `records/onchain-v2.local.json`, which is git-ignored: a rehearsal on this machine is
  not evidence of anything on a public cluster.

## The cap, quoted from `docs/ON-CHAIN-DESIGN.md` §3.10

> The cap is `resalePriceCapBps`, basis points over the ticket's own tier face, and the wire
> already fixes the convention: `2500` means +25%, signed, and a sale below face is negative.
> In lamports, a sale at price `p` on a ticket of face `f` is admitted iff
>
> ```text
> p * 10_000  <=  f * (10_000 + cap_bps)
> ```
>
> Both sides are computed in `u128` and compared, with no division anywhere.

The three decisions in that paragraph are the three properties the code keeps: `u128` on both
sides (a `u64` product wraps above `2^64 / 20_000` and would silently admit any price), no
division (rounding never enters the predicate), and the boundary inclusive at the cap. With face
`1_000_000_000` and cap `2500` the maximum admissible price is exactly `1_250_000_000`;
`1_250_000_001` is refused. Both sides are unit-tested, because one side alone proves nothing.

## The floor, new in v2

Feature 6 of MD3, and a second predicate rather than a term inside the first, so a seller is
told which end of the band their ask fell off:

```text
band_low == 0 || price >= band_low
```

`band_low_lamports == 0` means **no floor**; there is no way to tell "no floor" from "a floor of
zero lamports", which is the same thing. Equal to the floor is admitted. A floor above the
ceiling is refused at `InitializeRecord` with `6022`, because no price is both `>= floor` and
`<= ceiling`, so the ticket could never transfer and the record would be a brick that looks like
a ticket. The check is a product comparison for the same reason the cap is:
`band_low * 10_000 <= face * (10_000 + cap_bps)`, which never rounds.

## Who signs what

Nothing that changes a price, a status or a satellite is open to a stranger:

| instruction | signature required | refused with |
|---|---|---|
| 1 `InitializeRecord` | the mint's own authority, read out of the mint account | `6026`, or `MissingRequiredSignature` when the account is there but did not sign |
| 2 `SetPendingPrice` | the record's `authority` | `6026` |
| 3 `SetStatus` | the record's `authority` | `6026` |
| 4 `PublishBand` | the record's `authority` | `6026` |
| 5 `LogForecast` | the record's `authority` | `6026` |
| 6 `ScoreForecast` | the forecast's `authority` | `6026` |
| 105 `Execute` | whatever Token-2022 requires for the transfer itself | the price predicates, `6008`, `6009`, `6013` |

**What the mint-authority check on tag 1 buys, and what it does not.** It means the key that
fixes `cap_bps`, `band_low` and `policy` is the key that issued the ticket, so no passer-by can
become the record's authority by calling first and set a policy of their choosing. It does not
prove the mint is a ticket, does not tie the record to a real event, and does not constrain the
issuer: they can still create a record with any cap they like, which is what "the cap is the
issuer's commitment" means. A mint with **no** mint authority (`COption` tag 0, a fixed-supply
mint) can never have a record created at all: fail-closed, and stated rather than worked around.

## The record, and every byte of it

`["record", mint]`, owned by this program, Borsh, little-endian, no discriminator, **70 bytes**.
No field is length-prefixed. The offsets are the contract `ticketpath/onchain/v2.py` decodes,
and `initialize_record` compares the account's length to `TicketRecord::LEN` before reading a
byte, so a program-owned account of another shape cannot be written through tags 2 or 3.

| offset | bytes | field | type |
|---|---|---|---|
| 0 | 8 | `face_value_lamports` | `u64` |
| 8 | 2 | `cap_bps` | `u16` |
| 10 | 8 | `pending_price_lamports` | `u64`, cleared by the hook on an admitted transfer |
| 18 | 1 | `status` | `u8`, 1 transferable, 0 not |
| 19 | 8 | `band_low_lamports` | `u64`, 0 = no floor |
| 27 | 2 | `jurisdiction` | `[u8; 2]`, ISO-3166-1 alpha-2 uppercase, `ZZ` = unspecified |
| 29 | 1 | `policy` | `u8`, 0 = capped, 1 = monitored |
| 30 | 8 | `held_since_unix` | `i64`, 0 = unknown, written by the hook |
| 38 | 32 | `authority` | `Pubkey`, the mint authority at creation |

`cap_bps` is written once and there is no instruction that changes it: `InitializeRecord` is
idempotent, so a second call is a no-op and the arguments of the first call survive. That is how
the cap is immutable in practice rather than by assertion.

**One staging admits one sale.** `pending_price_lamports` is cleared by the hook on an admitted
transfer, so the next transfer of that ticket without a new staging is refused `6009`. Before
that clear, one staging admitted every later transfer at that price, which made the cap a
one-off check rather than a rule. The one path where the clear cannot happen is a record that
arrives **read-only** (a v1-shaped extra-account-metas list): the hook then logs that neither the
hold nor the staging was written. This program never creates such a list under its own id, since
the list is seeded by the program id, but the tolerance is stated rather than assumed away.

## The three satellites, and the rules they carry

| account | seeds | bytes | written by | immutable? |
|---|---|---|---|---|
| `Band` | `["band", mint]` | 102 | tag 4 | no, the head is rewritable on purpose |
| `Forecast` | `["forecast", mint, as_of_unix_le]` | 165 | tag 5 | yes, create-once |
| `Score` | `["score", forecast]` | 58 | tag 6 | yes, create-once |

`PublishBand` refuses four kinds of argument that used to be written (or promised in a comment):

- `low > high` (`6022`) — not a band at all;
- `as_of_slot` above the slot the write lands in (`6033`) — an estimate dated after the write
  that carried it;
- `sample_n == 0` with `refused == 0` (`6032`) — a number with no observations behind it and no
  statement that it is a refusal;
- nothing else. `refused` is normalised to 0 or 1 on write, so the stored byte is a flag and not
  a count.

`LogForecast` refuses a band wider than **18,446,744,073,709 lamports** (about 18,446.7 SOL) with
`6031`: `interval_score_micro` is a `u64` and the rule multiplies lamports by 1,000,000, so such
a forecast could never be scored and writing it would be writing an account nothing can grade.
It also refuses an `as_of_unix` earlier than the validator's clock minus
`FORECAST_BACKDATE_TOLERANCE_SECONDS` (300 s) with `6029`.

**What the forecast's immutability does and does not prove.** Create-once means a forecast cannot
be revised after the outcome is known. It does not mean it was written before the outcome: an
authority can still publish *at* the instant it claims to be as-of, and nothing on chain can tell
that from a forecast written five minutes earlier. The clock check closes the backdating hole
(the previous artefact's forecast had as-of `1760000000` and was created 394.9 days later), and
the residual is stated: the account proves "committed no later than as-of plus the tolerance, and
never changed after", which is a real constraint on a revision and not a proof of foresight.

## What the chain checks about a score, and what it takes on trust

`ScoreForecast` recomputes `covered` from the forecast's own ends, so that flag cannot disagree
with the interval committed before the outcome. It refuses a score below the band's width with
`6030`: the width term is the floor of the interval score, so no honest score can be smaller.

It does **not** recompute the penalty term, and there is no version of this program that could
without the rule text on chain. **An overstated error is stored on the authority's word.** The
account records what was claimed, that the claim could not be better than the band's own width,
and which rule hash it was made under; a consumer that needs the true number runs
`ticketpath/core/forecast_score.py` on the forecast, the realised price and the committed hash.
Only `covered` is derived by the chain.

## Instructions

Tag 0..6 are this program's own. Anything else falls through to the SPL transfer-hook
discriminator, whose first byte is `105`, so the tag byte is unambiguous.

| tag | instruction | argument bytes | total | arguments, in order |
|---|---|---|---|---|
| 0 | `InitializeExtraAccountMetaList` | 0 | 1 | none: the record is derived from the mint |
| 1 | `InitializeRecord` | 21 | 22 | `face` u64 (8), `cap_bps` u16 (2), `band_low` u64 (8), `jurisdiction` `[u8; 2]` (2), `policy` u8 (1) |
| 2 | `SetPendingPrice` | 8 | 9 | `price` u64 |
| 3 | `SetStatus` | 1 | 2 | `status` u8 |
| 4 | `PublishBand` | 61 | 62 | `low` u64 (8), `high` u64 (8), `as_of_slot` u64 (8), `sample_n` u32 (4), `refused` u8 (1), `model_hash` `[u8; 32]` (32) |
| 5 | `LogForecast` | 92 | 93 | `low` u64 (8), `high` u64 (8), `as_of_unix` i64 (8), `sample_n` u32 (4), `model_hash` `[u8; 32]` (32), `scoring_rule_hash` `[u8; 32]` (32) |
| 6 | `ScoreForecast` | 16 | 17 | `realised_lamports` u64 (8), `interval_score_micro` u64 (8) |
| 105 | Token-2022 `Execute` | 8 | 9 | `amount` u64, the hook call itself |

Account lists, in `next_account_info` order. The same tuples are in
`ticketpath/onchain/v2.py` (`*_ACCOUNTS` and the `*_accounts()` builders) so a client does not
have to read this table:

| tag | accounts |
|---|---|
| 0 | `[payer (signer, writable), mint, extra-metas (writable), system program]` |
| 1 | `[payer (signer, writable), mint, record (writable), mint authority (signer), system program]` |
| 2, 3 | `[authority (signer), record (writable), mint]` |
| 4 | `[authority (signer, writable), record, band (writable), mint, system program]` |
| 5 | `[authority (signer, writable), record, forecast (writable), mint, system program]` |
| 6 | `[scorer (signer, writable), forecast, score (writable), system program]` |
| 105 | `[source, mint, destination, authority, record (writable), hook program, extra-metas]` |

A v1 client that sends 10 argument bytes to tag 1 is refused as invalid instruction data rather
than silently creating a record with no jurisdiction and no policy: the unpack reads five fields
and a short buffer is an error, on both sides of the wire. A v1 client that sends tag 0 with 33
bytes is refused too: tag 0's payload is empty now, and the record it names is derived.

The extra-account-metas PDA is created by tag 0 and names **one** extra account, the record,
**writable**. Writable because the hook writes `held_since_unix` there and clears the staged
price, and Token-2022 builds its CPI from that list: a record marked read-only arrives read-only
and cannot be written. The record named in the list is derived from the mint, never taken as an
argument: the list is create-once, and a list naming the wrong account would make `execute`
refuse every transfer of that mint with `6020` with no way to correct it.

## Errors this program raises

Numbers are the interface (`docs/ON-CHAIN-DESIGN.md` §3.12 owns 6000..6020 and this program does
not renumber them). A code that means one thing in one release and another thing in the next is
worse than no code.

| code | name | raised when |
|---|---|---|
| 6008 | `E_AMOUNT_NOT_ONE` | the hook was called for more than one ticket |
| 6009 | `E_TRANSFER_NOT_STAGED` | no price is staged on the record (including after the last staging was consumed) |
| 6010 | `E_CAP_EXCEEDED` | the staged price is above `face * (10_000 + cap_bps) / 10_000`, policy 0 only |
| 6013 | `E_TICKET_NOT_VALID` | the record's `status` is not 1 |
| 6020 | `E_WRONG_EXTRA_ACCOUNT` | an account handed to an instruction is not the PDA it derives; also `IncorrectProgramId` when an account is not this program's |
| 6021 | `E_BELOW_FLOOR` | the staged price is below `band_low`, when the floor is above 0, policy 0 only |
| 6022 | `E_BAND_UNSATISFIABLE` | `InitializeRecord` with a floor above the ceiling; `PublishBand` or `LogForecast` with `low > high` |
| 6023 | `E_POLICY_INVALID` | `policy` is neither 0 (capped) nor 1 (monitored) |
| 6024 | `E_FORECAST_EXISTS` | `LogForecast` for an `as_of_unix` whose forecast already exists |
| 6025 | `E_ALREADY_SCORED` | `ScoreForecast` for a forecast whose score already exists |
| 6026 | `E_NOT_AUTHORITY` | a signer that is not the key the write requires: the record's authority on tags 2..5, the mint's authority on tag 1, the forecast's authority on tag 6 |
| 6027 | `E_REBATE_NOT_DUE` | **declared, not raised:** `ClaimRebate` is tag 7 and tag 7 is not implemented |
| 6028 | `E_REBATE_UNAVAILABLE` | **declared, not raised:** the same |
| 6029 | `E_FORECAST_BACKDATED` | `LogForecast` with an `as_of_unix` earlier than the clock minus 300 s |
| 6030 | `E_SCORE_BELOW_WIDTH` | `ScoreForecast` with `interval_score_micro < (high - low) * 1_000_000` |
| 6031 | `E_BAND_TOO_WIDE` | `LogForecast` with a band wider than `MAX_BAND_WIDTH_LAMPORTS` |
| 6032 | `E_BAND_EMPTY` | `PublishBand` with `sample_n == 0` and `refused == 0` |
| 6033 | `E_AS_OF_AHEAD` | `PublishBand` with `as_of_slot` above the slot the write lands in |

`6020` has two names on purpose: §3.12 spells it `E_NOT_A_TICKET`, v1 spelled the same condition
`E_WRONG_EXTRA_ACCOUNT` because that is what it checks. Both mean "the account you passed is not
the account I derive", which is one predicate with one number. `6011`, `6012` and `6014..6019`
are reserved by §3.12 for instructions this program does not implement, and the gaps stay gaps.

## Two fee modes, and why one mint cannot carry both

MD4, stated out loud because Token-2022 will not say it for us: a mint carries **one**
`TransferFeeConfig`, so the artist fee and the flip tax cannot share a mint. Two fees, two
mints, two events, one mode each.

| mode | rate | withheld fees go to | withdraw authority | who collects |
|---|---|---|---|---|
| **Artist fee** | 500..1000 bps to the artist | the artist's token account | the artist's own wallet | the artist, with a plain `withdraw-withheld-tokens` |
| **Flip tax** | 1500 bps to a rebate pool | the pool's token account, owned by `["rebate-pool", mint]` | the program PDA `["fee-authority", mint]` | the holder, through `ClaimRebate` (tag 7, not implemented) |

The rebate is the point of the second mode: a holder earns
`rebate_bps = 1500 * min(held_seconds, 60) / 60` of what their receipt withheld, capped by the
pool balance, so a fast flip earns nothing and a full hold earns the whole share.
`HOLD_FULL_SECONDS = 60` is the demo's value and not a market's; sixty seconds is chosen so the
curve can be observed inside one bounded run, and the arithmetic either side of it is unit
tested. Measured elsewhere in the tree and worth repeating here: at `decimals = 0` and
`amount = 1`, Token-2022 **ceils**, so any non-zero fee rate withholds the whole ticket
(`records/findings/36-transfer-fee-on-a-one-unit-ticket.md`).

What the chain does **not** connect, and a reader must not assume: `REBATE_FEE_BPS` (1500) is a
constant in `src/state.rs` and the chain never reads it against the mint. The number that
actually charges is the mint's `TransferFeeConfig`, configured at mint creation by whoever holds
the config authority. A mint configured at 500 bps with a pool expecting 1500 is a business error
this program cannot see. Nothing in this repository configures either mode yet;
`tools/publish_v2.py` creates a plain TransferHook mint with no fee extension at all.

## What is enforced, and what is only recorded

Enforced on every transfer of a hooked mint, in this order:

1. `amount == 1` (`6008`).
2. The extra-account-metas account is the one derived for this mint (`6020`).
3. The record is owned by this program and is the record for this mint (`IncorrectProgramId`,
   `6020`).
4. `status == 1` (`6013`).
5. A staged price is present (`6009`).
6. Policy 0 only: the cap (`6010`), then the floor when `band_low > 0` (`6021`).
7. On admission: the staging is consumed and `held_since_unix` is written.

Recorded, logged, and **not** enforced, with the reason it is not a gap but a decision:

- **`jurisdiction`.** Stored as the two bytes it was given, printed in every log line, never
  validated. There is no country list on chain to check against, and a wrong code is a wrong
  statement by the issuer, not a malformed account. `ZZ` is legal on purpose.
- **Policy 1, `monitored`.** Neither price predicate refuses and the log line says
  `policy=monitored` with the price, the face, the cap and the floor, so the chain records that
  the cap was not the reason and a reader can recompute the ceiling. The hook still runs, still
  refuses `amount != 1` and an unstaged transfer, and still writes the clock.
- **`held_since_unix`.** Written on every admitted transfer, when the record is writable. `0`
  means unknown, which is what a ticket that has never moved carries. Nothing reads it yet:
  `ClaimRebate` is tag 7 and tag 7 is not implemented.
- **`interval_score_micro`.** Checked only against the band's width (`6030`). An overstated error
  is the authority's assertion; see the section above.
- **`authority`.** Read on every tag 2..6 write and on tag 1's creation check. It is the only
  key those instructions accept.
- **The rebate rate.** `REBATE_FEE_BPS` and `HOLD_FULL_SECONDS` are policy numbers behind a pure
  function, unit tested, and wired to nothing on chain yet.

## Build, test, deploy

Run from this directory. The Solana toolchain is on `PATH` through `~/.profile`, so use a login
shell (`bash -lc`).

```sh
# the predicates, the layout, the policy branch, the authentication, the clock, the rebate
cargo test

# the program itself: drops target/deploy/cap_hook.so
cargo-build-sbf --sbf-out-dir target/deploy

# where it went, how big it is, and the hash a reader can compare
ls -l target/deploy/cap_hook.so && sha256sum target/deploy/cap_hook.so
```

Measured on this machine. v1's figures are quoted from
`records/findings/18-onchain-install-and-test.md`, where they were taken: a clean
`cargo-build-sbf` took **21.84s** and the `.so` was **85,784 bytes**. This run's own build was
`CARGO_BUILD_JOBS=2 nice -n 10 cargo-build-sbf --sbf-out-dir target/deploy`, run twice with the
same result each time. The pre-review v2 build was **108,816 bytes**, sha256
`0b6174344329f1a60e079572fcb43bbc59250470a398c788a32a7e66a8fa16c7`; the **current** v2 `.so` is
**111,504 bytes**, sha256
`de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac`, which is the hash
`records/onchain-v2.local.json` records as deployed in the run below.

Two publish paths, and they are not interchangeable:

| path | cluster | what it writes |
|---|---|---|
| `tools/devnet_publish.py` | devnet (v1 program, already deployed) | `records/devnet-artefacts.json`, the public record |
| `tools/publish_v2.py` | **a local validator only** | `records/onchain-v2.local.json`, git-ignored |

### The local-only rule for v2

`python3 tools/publish_v2.py` is the whole of the v2 deploy story, and it is local by
construction, not by a flag that could be forgotten:

- it starts its own `solana-test-validator` on a free port, with a fresh ledger under
  `.swarm-runs/v2-ledger-<pid>`, and kills it on every exit path (normal return, `atexit`,
  SIGINT, SIGTERM, SIGHUP);
- the payer is funded at **genesis** with `--mint`. No faucet, no airdrop, no transaction to any
  public cluster;
- Token-2022 and devnet's memo program are pulled in with the validator's own `--clone`, which
  reads program code from devnet. That is the only devnet conversation the run has;
- the program is deployed under `programs/cap_hook/target/deploy/v2-keypair.json` — a keypair
  **distinct from the frozen devnet one**, generated if absent and reused if present, so the
  program id is stable across reruns on this machine (215 bytes, mode 0600, git-ignored, never
  printed: `solana` and the out-of-process signer open it). The check that it is not the frozen
  devnet key is the explicit guard in `tools/publish_v2.py`, which refuses to deploy if the
  generated program id equals the frozen devnet program;
- it refuses to run if the artefact path or the deploy keypair resolves to one of the frozen
  devnet files;
- the frozen devnet program `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva` and
  `records/devnet-artefacts.json` are never deployed, upgraded, signed or edited. Upgrading them
  is not a thing this repository does.

What it proves on that validator, each with its own quoted signature:

- (a) `InitializeRecord` with face `1_000_000_000`, cap `2500`, floor `900_000_000`, jurisdiction
  `ZZ`, policy 0, signed by the mint's authority, then the record decoded back with that
  authority and `held_since_unix == 0`;
- (b) a transfer at the floor admitted, with the jurisdiction in the program log;
- (c) at `band_low - 1` refused `6021`;
- (d) at the cap `1_250_000_000` admitted and at `1_250_000_001` refused `6010`;
- (e) policy 2 refused `6023`; a floor above the ceiling refused `6022`;
- (f) the record re-read after an admitted transfer: `held_since_unix != 0` (the clock write
  through Token-2022's CPI, which the Rust unit tests cannot reach) and
  `pending_price_lamports == 0` (the staging was consumed);
- (g) the review's exploit, re-run: the phase-1 buyer, who is not the record's authority, stages
  a price of 1 and is refused `6026`; the same key sends `SetStatus(0)` and is refused `6026`,
  with the record's bytes unchanged both times.

and in a second phase on a fresh ledger: a band published and read back; a non-authority's band
refused `6026`; `low > high` refused `6022`; `sample_n = 0` refused `6032`; an `as_of_slot` in
the future refused `6033`; `refused = 7` stored as 1; a **forward-dated** forecast logged, a
duplicate as-of refused `6024`, a forecast dated a year ago refused `6029`; a score written with
the forecast unchanged, a second score refused `6025`, a score below the band's width refused
`6030`, and a realised price outside the band scored with `covered = 0`.

```sh
# the pure half: bytes, offsets, account lists, PDA derivation, the Rust sources compared
python3 -m unittest tests.test_onchain_v2 -v

# the live half: starts a validator, deploys, sends the transactions, asserts every fact above
TP_ONCHAIN_V2_LIVE=1 python3 -m unittest tests.test_onchain_v2_live -v
```

**`target/` is never committed.** It holds the `.so` and both program keypairs, and a keypair is
the secret that owns a program id. `.gitignore` refuses `programs/cap_hook/target/`, and
`.public-denylist` refuses the keypair name and shape again.

## What the program does NOT do

Scoped deliberately, per D6 and the brief. None of this is an oversight, and none of it may be
implied by a claim about the demo.

- **No tag 7.** `ClaimRebate` is specified in MD4, its arithmetic is written and tested, and no
  instruction pays a rebate. Tags 4, 5 and 6 exist and write the band, the forecast and the score.
- **No mutable cap.** `cap_bps` is written once, when the record is created, and there is no
  instruction that changes it: `set_cap` does not exist. D6: *"the cap is fixed when the event
  policy is created, before any ticket is minted, and is immutable thereafter"*.
  `SetPendingPrice` moves the price under test, never the cap or the face.
- **No escrow and no listing surface.** D6 rejects the PDA escrow: no lamports are held, no sale
  is settled, no listing exists. This program never receives SOL, and the staged price is not
  tied to any payment: the hook checks a number, not a settlement.
- **No sybil resistance and no nullifier.** D6: *"sybil resistance is explicitly not claimed and
  no nullifier is built"*. One person with many wallets is untouched by this code, so no
  bot-resistance claim may rest on it.
- **No destination check.** §3.9's `pending_dest` rule and its `6012` are not implemented: the
  hook does not compare the destination wallet to a staged one.
- **No custody accounting beyond the hold clock.** `HopRecord`, the hop counter and the record
  write-back in §3.4 are absent. `held_since_unix` records *when* the current holder acquired the
  ticket; it does not count hops and it does not identify the holder.
- **No verified-wallet gate.** §3.9's `6018` expiry check needs verification state this program
  does not hold.
- **No fee configuration.** Nothing here creates or withdraws a `TransferFeeConfig`. The two
  modes above are the plan, and `ClaimRebate` is the only part of it that would need this
  program's signature.
- **No price, no opinion.** It does not price anything, does not know what a ticket is worth, and
  keeps no model (`docs/ON-CHAIN-DESIGN.md` §13.1). The forecast accounts record what an
  authority claimed, not what this program computed.
- **No verified score.** `covered` is derived; `interval_score_micro` is checked against the
  band's width and nothing else. See the score section above.
- **Not the design's instruction set.** §3.9's `transfer_ticket` wraps the transfer and the record
  write in one instruction. Here Token-2022 performs the transfer and the hook only inspects it,
  which is the smallest arrangement that can still refuse. `SetPendingPrice` is a free-standing
  scaffold: in the design the staging belongs to the escrow or the listing (§1.4), and D6 rejects
  the escrow, so a real deployment needs a different writer for that field.

The one sentence this program earns, in D6's own words: **the ticket cannot move without the
program recording the hop, and the program will not record a price over the cap.** The first half
is still not implemented (there is no hop record), and v2 adds a second half to the second: it
will not record a price under the floor either, it does record the instant it admitted the
transfer, and it consumes the staged price so that the next transfer needs a new one. What is
proven on chain is the price boundary, the clock write, the staging being consumed, and the
authority checks on tags 1 to 6, and nothing more.

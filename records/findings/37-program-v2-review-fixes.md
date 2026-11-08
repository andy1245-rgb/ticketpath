# 37: the v2 review's security and evidential defects, fixed and re-measured

**Number.** 37 is free: 33, 34 and 35 each already have one or more claimants, and 36 is the
transfer-fee finding. Nothing in `records/findings/` is numbered 37.

**Written.** 2026-11-08T07:30Z. Local measurement only: a rebuilt `.so` deployed to a fresh
`solana-test-validator` on this machine, no devnet transaction, no mainnet transaction, no
faucet, no push and no commit.

**Input.** `tmp/review/feature-4-8-10.md`, a non-builder review of features 4, 6, 8 and 10 with
`file:line` for every finding and the signature of every transaction it used. `tmp/` is
git-ignored, so that file is local input and not part of the published record; this file is the
response to it and carries the numbers.

## 0. The answer

One finding was a live hole, not a nit: **`SetPendingPrice` and `SetStatus` authenticated
nobody**, so any keypair could stage a price on any record and freeze any ticket. It is closed,
and the reviewer's own exploit is re-run against the patched program with two new failed
transactions (`6026` twice, record bytes unchanged). Five more findings were real and are closed
with code: the staged price is now consumed by the transfer it admits, a forecast cannot be
backdated, a score cannot be understated below its band's width, the extra-account-metas list
derives the record instead of being handed one, and a record can only be created by the mint's
authority. Eight minor findings are closed, including the README that described a program two
releases old.

What is **not** closed, and cannot be by code: **the score is still an assertion.** The chain
recomputes `covered` and refuses a score below the band's width; it does not recompute the
penalty, so an overstated error is stored on the authority's word. And **v1 on devnet has the
same tag 2 / tag 3 hole** and cannot be patched, because an immutable deploy has no upgrade
path. Both are stated in the sections below and in the program's README.

## 1. The exploit: before and after

**Before**, on a throwaway copy of the previous artefact's phase-1 ledger, by the reviewer: the
phase-1 buyer (not the record's authority; it holds one of that mint's four tickets) sent
`SetPendingPrice(1)` and the record's `pending_price_lamports` became 1 — accepted, signature
`38SY2BrFftZfVkovMGpVaa2EEWgjQGBf6Xut8tUsfoAZNxSFUvREQpSfbf8mguBXUwwV2PZQHnlLt8Nj6agMonfgk`
(slot 257). Every later transfer of that ticket was then admissible at 1 lamport, because the
hook polices the staged number and the staged number was the attacker's. The same key then sent
`SetStatus(0)` — accepted, signature
`27kYGfwVTyWzzVSRzeYmdxUEne1EL187VUbp89C2tZ8mN5e59j4GWDb2DdpDddwavgcXo6h74mZRuy8xCuYD6p9x`
(slot 320) — and the ticket became permanently refused `6013`, because nothing in the program
sets `status` back.

**After**, in the artefact this run generated (`records/onchain-v2.local.json`, local, ignored),
the same two instructions from the same position:

| attempt | signer | result | signature |
|---|---|---|---|
| `SetPendingPrice(1)` | the funded non-authority (the buyer) | refused `6026 E_NOT_AUTHORITY` | `2xXJ8A7CT9gV8GaUcQFaVUaRWv3o4tJGCW8tiW98YwgGcaDC3RZio7kcDXkV8Ljc5g6g7wsDG6F4hoY5XdKoayDZ` |
| `SetStatus(0)` | the same non-authority | refused `6026 E_NOT_AUTHORITY` | `Sptt414xFxe7aRgmTfsQP5cNakGNbWhJCAZM5NY9dSh8uhLqvx9D4DeDabEh1khLdYiJkhHuV2cN3pgdLUWrwFj` |

The record's bytes are hashed before and after each attempt and are identical
(`recordUnchanged: true`, both `recordSha256Before` comparisons equal in the artefact), and
`status` is still 1 afterwards. The positive control is every `stage-*` step earlier in the same
phase: the same instruction, signed by the authority, is admitted — so a refusal that came from
a broken instruction could not masquerade as a refusal that came from the check.

## 2. The fixes, each with the test that bites

Every predicate below was mutation-proven: inverted, the named test failed, and the file was
restored byte-identically (sha256 quoted in §5). A test that cannot fail is a comment.

### 2.1 CRITICAL — tags 2 and 3 authenticate nobody

**Fix.** `set_pending_price` and `set_status` now read `[authority (signer), record, mint]` and
pass through one guard, `checked_record_for_write`, which checks in order: the signer bit
(`MissingRequiredSignature`), the owner (`IncorrectProgramId`), the address against
`["record", mint]` (`6020`), the account length against `TicketRecord::LEN`
(`InvalidAccountData`), and `record.authorises(authority.key)` (`6026`). The account was added to
both instructions' argument lists, in `lib.rs`, in `ticketpath/onchain/v2.py`
(`SET_PENDING_PRICE_ACCOUNTS`, `set_pending_price_accounts`, `set_status_accounts`) and in
`tools/publish_v2.py`.

**Tests that bite.** `tags_two_and_three_require_the_records_authority` (authority writes, a
stranger gets 6026 and no byte moves, an unsigned authority gets
`MissingRequiredSignature`), `tags_two_and_three_refuse_an_account_that_is_not_the_record_for_the_mint`
(a record-shaped 70-byte account at another address is 6020; a 102-byte band at the record's
address is `InvalidAccountData`; the record for a different mint is 6020). Live: proof `(g)`
above. Mutations M1 and M10.

### 2.2 MAJOR — one staging admitted every later transfer

**Fix.** The hook sets `pending_price_lamports = 0` in the writable branch on an admitted
transfer, so a transfer with nothing staged is refused `6009` at step 5 — the designed
behaviour, and what makes one stage one sale. The comment states the consequence and the one
path that escapes it: a record arriving read-only (a v1-shaped metas list, which this program
never creates under its own id) can be neither cleared nor clocked, and the log line says so.

**Tests that bite.** The live proof `(f)` re-reads the record after an admitted transfer and
requires `pending_price_lamports == 0` before the run will continue
(`pendingPriceAfterAdmission: 0`, `stagingConsumed: true`); the Rust test pins the clear to the
writable branch and before the clock write, because that branch reads `Clock::get` and cannot run
on the host. Mutation M2.

### 2.3 MAJOR — a forecast could be dated in the past

**Fix.** `FORECAST_BACKDATE_TOLERANCE_SECONDS = 300` and `validate_forecast_time`: `LogForecast`
refuses an `as_of_unix` earlier than the clock minus the tolerance, `6029`. 300 s is larger than
client-clock skew plus a transaction's flight time and far smaller than anything that would let
an outcome be seen. The check is deliberately one-sided: a future as-of is a pre-registration
whose bytes are fixed now, which cannot encode an outcome.

**The residual, stated.** Nothing stops an authority publishing a forecast *at* its as-of rather
than before it; a forecast written at 12:00 for as-of 12:00 and one written at 11:55 for as-of
12:00 are the same bytes. The account proves "committed no later than the as-of plus the
tolerance, and never changed after", which is a constraint on a revision and not a proof of
foresight. That sentence is in `state.rs::Forecast` and in the program README.

**Tests that bite.** `a_forecast_cannot_be_backdated_beyond_the_tolerance` (301 s refused, 300 s
accepted, now accepted, future accepted, 394.9 days refused — the previous artefact's own gap),
and live proof `(5'')` with `as_of_unix` a year behind the clock:
`5JM5Jg65LtyPzp7iTYLzD3o1Jihn17seqHDAwam6pT57brPxgSZ9tJgeDFk7w7WUnPtw6j9NzTzcshu4pGzThUZx`,
refused `6029`, forecast PDA still empty. The artefact's own forecast is now **forward-dated**:
as-of `1794123175` created in a transaction with block time `1794123058`, 117 s *before* the
instant it is about. Mutation M3.

### 2.4 MAJOR — the score is stored exactly as supplied

**Fix.** `validate_interval_score` refuses `interval_score_micro < (high - low) * 1_000_000` with
`6030`. The width term is the floor of the interval score, so no honest score can be smaller.
The comparison is in `u128`, so it cannot overflow. The existence check (`6025`) runs first, so a
duplicate score is still reported as a duplicate.

**The residual, stated in code and in the README.** The chain cannot recompute the penalty term
(it has no rule text to run), so it cannot detect an **overstated** error: an authority can write
any number from the width upward. Only `covered` is derived. `state.rs::Score` and the README say
exactly that.

**Tests that bite.** `a_score_below_the_band_width_is_refused_and_a_covered_miss_is_recorded_as_zero`
(width accepted, width - 1 refused, and the explicit case that `u64::MAX` for a width of 1 is
*still* accepted because the chain cannot see an overstated error); live proof `(6'')` with
`interval_score_micro = 200_000_000_000_000 - 1` refused
`5mk2Y9QxkU6w89jwgHMvds7sGKtUmVQeNGFwLGeoDA5191MNTYReMQA5qSbAH5zyVRc4ns9xbhnEkKAYWejGRf5V`,
and **no score account created**. Mutation M4.

### 2.5 MAJOR — `InitializeExtraAccountMetaList` wrote whatever record it was handed

**Fix.** The argument is gone. Tag 0's payload is empty (1 byte of instruction data) and the
program derives `["record", mint]` from the mint, so a create-once list cannot name a wrong
account and brick every transfer with `6020` forever.

**Tests that bite.** `tag_zero_takes_no_argument_because_the_record_is_derived_from_the_mint`
(unpack of `[0]`, no `record: Pubkey` anywhere in the program, the derived address is what the
meta resolves to), and the Python drift test
`test_tag_zero_derives_the_record_instead_of_taking_it`. Mutation M12.

### 2.6 MAJOR — `InitializeRecord` authenticated nobody

**Fix.** `mint_authority_of` reads the base `Mint` layout (`COption<Pubkey>` at offset 0: a
4-byte tag then the key; Token-2022 appends extensions after the 82-byte base and does not move
it). Tag 1 requires that key to sign and refuses `6026` otherwise, and the record's `authority`
is that key rather than the rent payer. A mint with no mint authority is refused `6026`:
fail-closed.

**What it buys and does not.** It means the key that fixes the cap, the floor and the policy is
the key that issued the ticket, so no passer-by can become the record's authority by calling
first. It does not prove the mint is a ticket, does not tie the record to an event, and does not
constrain the issuer, who can still choose any cap — which is what "the cap is the issuer's
commitment" means. The README says this in those words.

**Tests that bite.** `the_record_needs_the_mints_authority_to_sign_its_creation` (the parser on
the real layout, a stranger refused 6026 with no record created, the issuer's key unsigned
refused `MissingRequiredSignature`, an authority-less mint refused 6026, an 81-byte account
`InvalidAccountData`); live proof `(a)` reads the mint account, requires
`mint_authority == payer` before it will send the create, and records it as
`authorityIsMintAuthority: true`. Mutation M9.

### 2.7 MAJOR — `state.rs` overclaimed, and three hook refusals had no test

**Fix.** `state.rs::Forecast` now says what create-once does and does not prove, and names the
clock check and its residual. `6008`, `6009` and `6013` are executed by a mock-runtime test with
the real `execute`: `amount = 2`, a record with nothing staged, a record with `status = 0`. All
three return before the clock sysvar is touched, which is why they are reachable on the host.

**Test that bites.** `the_hook_refuses_a_bulk_transfer_an_unstaged_transfer_and_a_disabled_ticket`.

### 2.8 MINOR — eight smaller findings, all real

| finding | fix | test that bites |
|---|---|---|
| `sample_n = 0` with `refused = 0` accepted | `6032` | `a_band_with_no_observations_or_an_as_of_in_the_future_is_refused`; live proof `(4''')` `4V2Eaeua5rRtucVRPGH5Xuk9BBw59ekYHUAZrdH1kG4VmDmS4mBeYV1AkcLSqyPwzRoeYGhmc1xDy8HpR9f8hUpm` |
| `refused` stored as any byte (7) | `normalised_refused`, applied in `band_for_write` | same test (7 → 1, 255 → 1); live proof `(4v)` sends 7 and reads back 1, `2bUBiqCcGexyMAmJwr3g49rN1R4wzWdCjqthsnQprmsPtEcpwTcMkaX2RnwcwjxU1doxA4qF4aE8vknF1oFHQ6Lg`; mutation M8 |
| `as_of_slot = 10^12` with `published_slot = 234` accepted | `6033` | same test; live proof `(4'''')` `4ujTZAbKKMsNXLQeBDz98TffNv5qEJJUUhT85kG3pMMRSh7rzhD1an4m2fHTnuXYypTbw8jiyovDzw998ja9dYE2`; mutation M6 |
| the monitored log line omitted `face` | `face={}` added | `the_monitored_log_line_names_the_face_so_the_ceiling_can_be_recomputed`; mutation M13 |
| a band wider than ~18,446 SOL cannot be scored | `MAX_BAND_WIDTH_LAMPORTS` = `u64::MAX / 1_000_000` = 18,446,744,073,709, refused `6031` at `LogForecast`; the Python rule states the same limit and raises `ForecastRefused` (not an opaque `ValueError` from the wire packer) for a width or a miss outside the field | `a_forecast_too_wide_to_score_is_refused_at_log_time`, `test_the_two_limits_of_the_on_chain_field`; mutation M5 |
| `covers`' false branch untested | a unit test of `Forecast::covers` at both ends and one lamport outside, plus a **live miss**: realised `1_100_000_001` on `[900_000_000, 1_100_000_000]`, stored `interval_score_micro = 200_000_010_000_000`, `covered = 0`, `Ey42bb6mwaLLwAvEzHuvZ5agSxmzS9TsLqZ2j38cKix3Xvb1XYt3UY864zmjHqzWApLpmeGEJiQaUUe4fa4oYjd` | `a_score_below_the_band_width_is_refused_and_a_covered_miss_is_recorded_as_zero`, `test_v2_a_miss_is_scored_with_covered_zero`; mutation M11 |
| a 70-byte satellite writable through tag 3 | length compared to `TicketRecord::LEN` before deserialising, and the address checked against `["record", mint]` | `tags_two_and_three_refuse_an_account_that_is_not_the_record_for_the_mint`; mutation M10 |
| `v2.py` docstrings said Band/Forecast/Score were not built | three stale clauses deleted, account lists and the mint reader added | `tests/test_onchain_v2.py` (45 tests) |
| `programs/cap_hook/README.md` described the pre-v2 program | rewritten: instruction table 0..6 with account lists, error table 6008..6033, the score section, the v1-hole paragraph, the real `.so` size and hash, and "reused keypair with a stable id" instead of "a fresh keypair per run" | `python3 tools/doc_check.py` (paths and program-vs-doc) |

## 3. What remains, and changes what the earlier evidence proves

**The score is an assertion.** `interval_score_micro` is checked against the band's width and
nothing else. A reader who needs the true number must recompute it from the forecast, the
realised price and the committed rule hash; the account records what was claimed, under which
rule, and that it could not be better than the band's own width.

**v1 on devnet has the same tag 2 / tag 3 hole and cannot be patched.** The frozen program
`5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva` takes no signer on `SetPendingPrice` or
`SetStatus`, exactly as v2 did before this run, and an immutable deploy has no upgrade path, so
the hole is in the deployed bytes and stays there. **This changes what the proven devnet refusal
proves**: the devnet evidence shows that the price predicate refuses a price above the cap (and,
after v2, below the floor) on prices chosen by the deploy key. It does **not** show that a
stranger could not have chosen the number, and no claim that the devnet program enforces a cap
*against its own holders* may rest on it. The v2 source in this repository does not have the hole;
the v2 `.so` on this machine has been exercised with the exploit and refuses it.

**The RPC `getTransaction` and account reads are the same on all clusters.** Nothing in the fix
relies on a local-only behaviour: the two refusals are `Custom` errors from ordinary failed
transactions, which any cluster reports identically. What is local-only is the *deployment*:
this `.so` has never been on a public cluster, and publishing it is not part of this run.

## 4. What was rebuilt and redeployed

| | before this run | after |
|---|---|---|
| `.so` bytes | 108,816 | **111,504** |
| `.so` sha256 | `0b6174344329f1a60e079572fcb43bbc59250470a398c788a32a7e66a8fa16c7` | **`de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac`** |
| artefact | `records/onchain-v2.local.json`, as_of 1760000000 (394.9 days stale) | regenerated by the final live run, as_of 1794123175, forward of its own block time by 117 s |
| proofs | a..f, seven tag 4..6 proofs | a..g (conventions above), thirteen tag 4..6 proofs |
| program id | unchanged by design | the same `v2-keypair.json`, reused, guarded against the frozen devnet id |

The rebuild was `cargo-build-sbf --sbf-out-dir target/deploy` with `CARGO_BUILD_JOBS=2 nice -n
10`, twice, and both builds produced the same sha256. Two fresh ledgers under `.swarm-runs/
v2-ledger-<pid>` and `-phase2`, two validators, both killed on the normal exit path; the ledgers
are kept so every signature above can be re-read with `getTransaction` against a validator
resumed on a copy.

## 5. Commands, with tails

```
$ cargo test                                  # programs/cap_hook
test result: ok. 30 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out

$ sha256sum programs/cap_hook/target/deploy/cap_hook.so
de89af3cf0831bc6bad181ee7762c83e6486c4b9d0facb6f99cd7cfa6e949cac

$ TP_ONCHAIN_V2_LIVE=1 python3 -m unittest tests.test_onchain_v2_live
...
Ran 26 tests in 29.318s
OK

$ python3 -m unittest discover -s tests -t .
Ran 1053 tests in 29.173s

OK (skipped=26)
```

The full-suite number is exactly that: the suite as it stood when the last of the concurrent runs
on this tree settled. It is worth saying what it was on the way there, because it is a fact about
this tree and not about this change: at the start of this run the same command reported `Ran 981
tests ... FAILED (errors=10)`, every error `devnet_publish has no attribute
refuse_frozen_devnet_upgrade`, from another run's in-flight edit to `tools/devnet_publish.py`;
mid-run it reported three failures in `tests.test_console_recorded_artefact` and
`tests.test_devnet_publish.TestConsoleSlot`, each passing when its module ran alone, from the
same kind of edit in `ticketpath/console/`. None of those files is touched by this run. The
suites this run owns are green throughout: `tests.test_onchain_v2` 45 tests, 
`tests.test_onchain_v2_live` 26, `tests.test_forecast_score` 18.

### The mutation proofs

Each predicate was inverted, the named test was run, the file was restored and its sha256
compared with the value before the edit. All thirteen were proven and every file came back
byte-identical (`lib.rs` `2d783ce4…`, `state.rs` `d2857017…` before and after).

| # | predicate inverted | named test that failed |
|---|---|---|
| M1 | `record.authorises(authority.key)` in the write guard | `tags_two_and_three_require_the_records_authority` |
| M2 | `pending_price_lamports = 0` on admission | `an_admitted_transfer_clears_the_staged_price_so_one_stage_is_one_sale` |
| M3 | the backdating bound | `a_forecast_cannot_be_backdated_beyond_the_tolerance` |
| M4 | the score's lower bound | `a_score_below_the_band_width_is_refused_and_a_covered_miss_is_recorded_as_zero` |
| M5 | the band width domain | `a_forecast_too_wide_to_score_is_refused_at_log_time` |
| M6 | `as_of_slot > published_slot` | `a_band_with_no_observations_or_an_as_of_in_the_future_is_refused` |
| M7 | `sample_n == 0 && refused == 0` | same |
| M8 | `refused` normalisation | same |
| M9 | the mint authority comparison | `the_record_needs_the_mints_authority_to_sign_its_creation` |
| M10 | the `TicketRecord::LEN` guard | `tags_two_and_three_refuse_an_account_that_is_not_the_record_for_the_mint` |
| M11 | `Forecast::covers` | `a_score_below_the_band_width_is_refused_and_a_covered_miss_is_recorded_as_zero` |
| M12 | tag 0 deriving the record from the mint | `tests.test_onchain_v2...test_tag_zero_derives_the_record_instead_of_taking_it` |
| M13 | `face=` in the monitored log line | `the_monitored_log_line_names_the_face_so_the_ceiling_can_be_recomputed` |

## 6. What remains unverifiable here

- **A 70-byte satellite cannot be written through tags 2 or 3** is proven by the address check
  and by a unit test with a record-shaped account at a band's address. It is not proven against a
  *living* satellite of exactly 70 bytes, because none exists in this program: the only 70-byte
  program-owned account is a record. The length guard is the second line, not the first.
- **The read-only record path** cannot consume the staging or write the clock, by construction:
  the writable branch is where both writes live, and the unit test runs the read-only path only.
  The state that path leaves is stated in the code and the README rather than measured on chain,
  because this program never creates a read-only metas list.
- **The mint-authority check's positive path** is proven live for a Token-2022 mint whose
  authority is the payer. A mint whose authority is a multisig, or a mint whose authority has
  been revoked after the record exists, is not exercised; the code reads the field, so the
  behaviour follows the field, but no artefact shows it.
- **Whether the score the authority writes equals the rule** — that is the assertion, and it is
  not verifiable on chain by design. The artefact's covered score *does* equal the rule's output
  for its band (`200_000_000_000_000`), and the miss score equals the rule's output for a
  one-lamport miss (`200_000_010_000_000`); that is a measurement of one honest run, not a check
  the chain performs.
- **The public cluster.** Nothing here touches devnet or mainnet, so this run says nothing about
  what a public validator would charge, how it would schedule the two phases, or whether the
  frozen v1 program's `SetPendingPrice` is reachable today by a stranger — that last one is a
  devnet read and a devnet write, and both were out of scope.

## 7. What the documents still need from their steward

`docs/ON-CHAIN-DESIGN.md` is being edited by another run and was not touched here. Its
implemented-today table already carries 6029..6033 and the v2 instruction rows, and two of its
sentences now disagree with the code:

1. the `NotAuthority` / 6026 row says "a satellite write (tags 4 to 6) signed by anyone but the
   record's `authority`". It is now tags **2 to 5** with the record's authority, tag 1 with the
   **mint's** authority, and tag 6 with the **forecast's** authority;
2. the `BandTooWide` / 6031 row says `PublishBand` or `LogForecast`. Only `LogForecast` refuses
   it: a band is a feed head and is never scored, so its width is not bounded by the score field.

and it is missing the two sentences this finding exists to publish, quoted here so they can be
pasted without deciding anything again:

> v1's `SetPendingPrice` and `SetStatus` take no signer, so on the deployed devnet program any
> keypair can stage a price and flip a ticket's status; an immutable deploy has no upgrade path,
> so that hole is in v1's bytes permanently, and the devnet refusals prove the price predicate on
> prices the deploy key chose, not that a stranger was kept from choosing them.

> `ScoreForecast` recomputes `covered` from the forecast's own ends and refuses a score below the
> band's width, but it does not recompute the penalty term: `interval_score_micro` above that
> floor is the authority's assertion, not a number the chain verified.

`records/STATE-OF-PROJECT.md` and `records/F-decision-log.md` also name the v2 status and were
not touched; the feature table's on-chain rows should point at proof `(g)` for the authentication
finding and at `(6''')` for the `covered = 0` branch.

# `region_gate`: the jurisdiction-aware policy hook, parked

A native Rust Solana program, one source file, that Token-2022 calls inside a transfer of a
hooked ticket mint. It implements the record and the policy branch that
`records/REGION-CAPS-DESIGN.md` §9 designs, and it is the crate that decision points at when it asks
where the check could move if the rules table ever has to be enforced by something the platform
cannot rewrite.

**Parked. It is not in the transaction path today.** The program a ticket actually goes through is
`programs/cap_hook/` (v2, which carries the jurisdiction and policy bytes and interprets neither),
and nothing in `ticketpath/` imports or calls this crate. The one thing that deploys it is
`tools/region_local_proof.py`, onto a `solana-test-validator` that the tool starts and kills inside
its own run. It is kept in the tree as the design record: the source that says what enforcing a
jurisdiction's cap on chain costs in accounts, error codes and a record layout, written down while
the reasoning was fresh, so that a future decision to move the check does not start from a blank
file.

The jurisdiction itself is not decided here. `records/REGION-CAPS-DESIGN.md` §13 says where the
decision lives and why this crate is not the place it is applied.

## What it enforces

Token-2022 calls the hook inside every transfer of a mint whose extra-account-metas account names
this program. The hook reads one record account, derived from the mint, and branches once on its
`policy` byte:

| policy | value | what the hook does |
|---|---|---|
| capped | 0 | refuses a staged price above `base * (10_000 + cap_bps) / 10_000`, with `6010` |
| monitored | 1 | admits any staged price and logs the jurisdiction, the price and the ratio |
| unresolved | 2 | admits any staged price and logs that the law could not be established |

The cap predicate is `price * 10_000 <= base * (10_000 + cap_bps)`, both sides widened to `u128`,
no division anywhere, inclusive at the cap. `base` is a field of the record and not necessarily
the tier face: where the law's base includes the fees the first buyer paid, the record carries the
sum and the program cannot tell the difference, which `docs/ON-CHAIN-DESIGN.md` §14.2 states as
the gap it is.

Four refusals hold on every policy, because they are about the transfer rather than the law: an
amount other than one (`6008`), a transfer with no staged price (`6009`), a record whose status is
not transferable (`6013`), and an extra-account-metas or record account that is not the PDA this
program derives (`6020`).

Four more hold on the writer instructions. Only the record's authority may stage a price, change
status or tighten the policy (`6040`). `TightenPolicy` is monotone: it may lower a cap, and it may
move `monitored` or `unresolved` to `capped`, and it refuses anything that would raise a cap or
remove one (`6042`), because the chain cannot tell a repeal from an organiser raising a cap, selling,
and lowering it again. A policy triple that contradicts itself is refused (`6041`), and so is a
jurisdiction that is not two uppercase ASCII bytes (`6043`).

## The record, and every byte of it

Borsh, little-endian, no discriminator, 58 bytes:

| offset | width | field | why it is there |
|---|---|---|---|
| 0 | 8 | `base_lamports` | the cap base in lamports: the tier face, or face plus documented fees |
| 8 | 2 | `cap_bps` | the cap over that base; `65535` when there is no cap |
| 10 | 8 | `pending_price_lamports` | the price the next transfer will be judged on |
| 18 | 1 | `status` | 1 transferable, 0 not |
| 19 | 2 | `jurisdiction` | the binding nation, ISO-3166-1 alpha-2; `ZZ` when unresolved |
| 21 | 1 | `policy` | 0 capped, 1 monitored, 2 unresolved |
| 22 | 4 | `law_version` | the rules-table generation the policy was stamped from |
| 26 | 32 | `authority` | the only signer allowed to write this record or its satellites |

A nation and not a subdivision, deliberately: two bytes cannot hold `CA-ON` or `AU-NSW`, and the
chain field records what was enforced rather than the whole legal picture. The subdivision, the
citation and the table hash stay in the event record, where they can be corrected without a
migration. The cost is that a chain reader alone cannot tell Ontario from Quebec, and
`records/REGION-CAPS-DESIGN.md` §9 pays it on purpose.

## The rule that keeps `monitored` from becoming a bound

`validate_policy` is the reason this crate is worth keeping even parked. A policy with no cap must
carry the field's maximum: `monitored` and `unresolved` are both refused with `6041` unless
`cap_bps == 65535`; `unresolved` must name `ZZ` and `monitored` must not; and `capped` is refused if
it names `ZZ`, because an unresolved law cannot produce a cap and a binding jurisdiction at once.

That is what stops a record from carrying policy 1 with a low number nobody looked at, which would
read to every downstream consumer as a cap the law imposes. The v2 program in `programs/cap_hook/`
does not have this rule: its `validate_initialize` refuses a policy byte other than 0 or 1 and says
nothing about the cap that accompanies it. The engine does not create the ambiguity the rule guards
against (`ticketpath/core/event_records.py` emits no ceiling for a monitored event without a
platform cap, measured, see `tests/test_event_jurisdiction.py`), but only this crate makes it
unrepresentable.

## The one build on record

From this directory, with a login shell so the Solana toolchain is on `PATH`:

```sh
cargo test                                      # the eight unit tests in src/lib.rs
cargo-build-sbf --sbf-out-dir target/deploy     # drops target/deploy/region_gate.so
sha256sum target/deploy/region_gate.so
```

`cargo-build-sbf --sbf-out-dir target/deploy` is the exact command `tools/region_local_proof.py`
runs when the `.so` is missing or older than `src/lib.rs`, and it is the command that produced the
only build on record: the local-validator proof written 2026-11-08T06:30:03Z, whose `.so` sha256 is
`7e60fc80ffbad7bbc9f7d98bf9980ec113adacf0bd1ba76e23e6d957cf8e374b`, quoted in
`records/findings/38-region-caps-local-validator.md`.

`target/` is git-ignored and is not in the tree today, so this repository holds neither that `.so`
nor the program keypair that sat beside it, and the hash in that finding is the only record of the
build. `cargo test` was not re-run for this note, and the eight tests are quoted as they stand in
the source.

## Why it is not deployed

Four reasons, and the first is the one that decides it:

1. **Nothing needs a second program in the path.** `programs/cap_hook/` v2 already carries
   `jurisdiction: [u8; 2]` and `policy: u8` and writes them at `InitializeRecord`. It has run only
   on a local validator and not on devnet, and the devnet artefact still describes the v1 cap-only
   program, which is a reason to be careful with v2 rather than a reason for a third program.
2. **The devnet program is frozen.** v1 has no jurisdiction byte and no policy byte, it is not
   upgradeable, and redeploying under its key is not something this crate or any script here does.
3. **Whether the table should refuse a sale is not a build step.** The rows in
   `ticketpath/data/region-caps.json` are evidence with citations and confidence grades, and
   turning one into a refusal on chain is the operator's decision. A crate that could do it is not
   a licence to do it.
4. **It is unaudited and has one proof run behind it.** No review of it exists in
   `records/findings/` and no audit exists at all, the staged price is not consumed (the
   extra-account-metas list names the record read-only, and the attempt to make it writable took
   the local proof from 11 passes to 4 and was reverted rather than shipped, recorded in
   `records/findings/34-region-caps-build.md` §7), and there is no hold clock on the record.
   Deploying it would put an unverified program inside a token transfer.

## What would have to change to deploy it

1. **A decision about the third state.** v2 refuses `policy = 2` at `InitializeRecord` with
   `6023`, and this crate assigns `2` to `unresolved`. Either this crate becomes the program in the
   path, or v2 gains the byte and the log line for it. Neither is written today, and doing both
   would leave two programs enforcing one rule.
2. **A fee on the event row.** Every `face_plus_fees` law resolves today with a base equal to the
   tier face, because no event row carries a fee. That is stricter than the law, and deploying a
   crate that claims to apply the law's base while it cannot is the kind of gap that reads as a
   bug in the law rather than in the row.
3. **The staged price consumed.** Today a staged price admits one transfer and stays on the record,
   so a second transfer is admitted on a number nobody staged. The defect and the reverted fix are
   recorded rather than hidden.
4. **A funded key and a cluster.** Deployment costs money, so it is the operator's call and not a
   step in a script.
5. **A review by someone who did not write it**, against `records/REGION-CAPS-DESIGN.md` and this
   file, before any cluster that outlives the run.

## What this crate does not do, and does not claim

- It does not decide which law applies to a resale. It stores the outcome of a decision made off
  chain.
- It is not audited, not safe by inspection, and not deployed to any cluster that outlives a run.
  Nothing in this repository may describe it as any of those.
- It does not read the rules table, the internet or a clock. `law_version` is an index the caller
  supplies and the program never resolves.
- It does not enforce a floor, a hold time, a hop count or a rebate. The v2 program in
  `programs/cap_hook/` carries the floor and the hold clock; this crate carries the jurisdiction and
  the policy.
- It does not make a resale lawful or unlawful. The hook refuses a token transfer and says why; a
  ticket sold as an IOU in a chat window is outside everything it can see, which is the same limit
  the rest of `docs/ON-CHAIN-DESIGN.md` states about itself.

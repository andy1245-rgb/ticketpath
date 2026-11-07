# `cap_hook` — the resale-cap transfer hook

A native Rust Solana program (no Anchor) that Token-2022 calls inside every transfer of a
hooked ticket mint, and that refuses the transfer when the staged resale price is above the
ticket's cap. It is the on-chain half of `docs/ON-CHAIN-DESIGN.md` §1.3, §3.9 and §3.10, built
to the scope `records/F-decision-log.md` D6 sets.

Source: `src/lib.rs`, one file, ~440 lines including four `#[test]`s.
Deployed and exercised against a local validator on 2026-11-07: the measurements, the failures
and the two signatures either side of the boundary are in
`records/findings/18-onchain-install-and-test.md`.

## The cap, quoted from `docs/ON-CHAIN-DESIGN.md` §3.10

> The cap is `resalePriceCapBps`, basis points over the ticket's own tier face, and the wire
> already fixes the convention: `2500` means +25%, signed, and a sale below face is negative. In
> lamports, a sale at price `p` on a ticket of face `f` is admitted iff
>
> ```text
> p * 10_000  <=  f * (10_000 + cap_bps)
> ```
>
> Both sides are computed in `u128` and compared, with no division anywhere:
>
> ```rust
> let lhs = (price_lamports as u128) * 10_000u128;
> let rhs = (record.face_value_lamports as u128) * (10_000u128 + policy.cap_bps as u128);
> require!(lhs <= rhs, TicketpathError::CapExceeded);
> ```

The three decisions in that paragraph are the three properties the code keeps: `u128` on both
sides (a `u64` product wraps above `2^64 / 20_000` and would silently admit any price), no
division (rounding never enters the predicate), and the boundary inclusive at the cap. With
face `1_000_000_000` and cap `2500` the maximum admissible price is exactly `1_250_000_000`;
`1_250_000_001` is refused. Both sides are unit-tested, because one side alone proves nothing.

## Build, test, deploy

Run from this directory. The Solana toolchain is on `PATH` through `~/.profile`, so use a
login shell (`bash -lc`).

```sh
# the cap arithmetic, native, no cluster involved
cargo test --release

# the program itself: drops target/deploy/cap_hook.so
cargo-build-sbf --sbf-out-dir target/deploy

# where it went and how big it is
ls -l target/deploy/cap_hook.so
```

Measured on this machine 2026-11-07: clean `cargo-build-sbf` **21.84s**, `.so` **85,784 bytes**,
peak RSS 4,590 MB (the build is memory-heavy; it ran with `CARGO_BUILD_JOBS=2 nice -n 10`).

`tools/devnet_publish.py` runs all of the above for you, deploys the result, wires the mint and
writes `records/devnet-artefacts.json`. It is the only path a deployment should take: it is
idempotent, bounded, and it records the public result.

**`target/` is never committed.** It holds the `.so` and the program keypair
(`target/deploy/cap_hook-keypair.json`), and the keypair is the secret that owns the program id.
`.gitignore` refuses `programs/cap_hook/target/` and the keypair name patterns in
`.public-denylist` refuse it again by shape.

## What the program does

| instruction | tag | what it does |
|---|---|---|
| `InitializeExtraAccountMetaList { record }` | 0 | creates the `["extra-account-metas", mint]` PDA Token-2022 resolves before it calls the hook, naming the record account as the one extra account. Idempotent: a second call is a no-op. |
| `InitializeRecord { face, cap_bps }` | 1 | creates the `["record", mint]` PDA this program owns: `face_value_lamports u64`, `cap_bps u16`, `pending_price_lamports u64`, `status u8`. Idempotent in the same way, which is what makes the cap immutable in practice. |
| `SetPendingPrice { price }` | 2 | stages the price the next transfer will be checked against. |
| `SetStatus { status }` | 3 | flips the record's transferable flag. |
| Token-2022 `Execute` (discriminator 105) | — | the hook. Refuses `amount != 1` (`6008`), a record that is not ours or not this mint's, `status != 1` (`6013`), an unstaged price (`6009`), and a price over the cap (`6010`). Writes one log line either way, so the chain itself states the decision it took. |

Error codes are the design's table (`docs/ON-CHAIN-DESIGN.md` §3.9), not invented:
`CapExceeded = 6010` is `0x177a` on the wire.

## What the program does NOT do

Scoped deliberately, per D6 and the brief. None of this is an oversight, and none of it may be
implied by a claim about the demo.

- **No mutable cap.** `cap_bps` is written once, when the record is created, and there is no
  instruction that changes it: `set_cap` does not exist. D6: *"the cap is fixed when the event
  policy is created, before any ticket is minted, and is immutable thereafter"*. `SetPendingPrice`
  moves the price under test, never the cap or the face.
- **No escrow and no listing surface.** D6 rejects the PDA escrow: no lamports are held, no sale
  is settled, no listing exists. This program never receives SOL.
- **No sybil resistance and no nullifier.** D6: *"sybil resistance is explicitly not claimed and no
  nullifier is built"*. One person with many wallets is untouched by this code, so no
  bot-resistance claim may rest on it.
- **No destination check.** §3.9's `pending_dest` rule and its `6012` are not implemented: the hook
  does not compare the destination wallet to a staged one.
- **No custody accounting.** `HopRecord`, the hop counter and the record write-back in §3.4 are
  absent, so nothing here records *that* a transfer happened or how many hops a ticket has taken.
- **No verified-wallet gate.** §3.9's `6018` expiry check needs verification state this program
  does not hold.
- **No price, no opinion.** It does not price anything, does not know what a ticket is worth, and
  keeps no model (`docs/ON-CHAIN-DESIGN.md` §13.1).
- **Not the design's instruction set.** §3.9's `transfer_ticket` wraps the transfer and the record
  write in one instruction. Here Token-2022 performs the transfer and the hook only inspects it,
  which is the smallest arrangement that can still refuse. `SetPendingPrice` is a free-standing
  scaffold: in the design the staging belongs to the escrow or the listing (§1.4), and D6 rejects
  the escrow, so a real deployment needs a different writer for that field.

The one sentence this program earns, in D6's own words: **the ticket cannot move without the
program recording the hop, and the program will not record a price over the cap.** The first half
is not implemented here — the hop record is not built — so what is proven on chain is the second
half alone. That is what the artefact and the console slot claim, and nothing more.

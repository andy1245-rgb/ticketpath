# 21 — The cap-check hook in the tree, and the publish script rehearsed end to end

**Run:** ONCHAIN-WIRE, 2026-11-07. **Result: the program is in the repository, the publish
script exists and was taken through the whole pipeline against a local validator, and the
console's `[DEVNET]` slot has a verified path and a localnet path that cannot be confused with
it. Devnet is still unfunded, so nothing here is on devnet.**

The one-line answer to "is it on devnet?": **no, and the script that puts it there is one
command once the authority holds 2 SOL.** Section 6 has that command and section 5 has the
local output it was tested against.

---

## 1. The program, in the tree

`programs/cap_hook/` — `Cargo.toml`, `src/lib.rs` (one file, ~440 lines, four unit tests) and
`README.md`, which carries the build commands, the cap formula quoted from
`docs/ON-CHAIN-DESIGN.md` §3.10 and the list of what the program does not do (D6: no mutable
cap, no escrow, no sybil claim, no nullifier).

It is the crate the previous run built outside the tree as `ticketpath-hook`, renamed on
import; nothing else changed and the program id is a property of the deploy keypair, not of
the crate name. `target/` and `Cargo.lock` are generated and are git-ignored.

```
$ cargo test --release                     # the cap arithmetic, no cluster
running 4 tests ... test result: ok. 4 passed; 0 failed
$ cargo-build-sbf --sbf-out-dir target/deploy
Finished `release` profile [optimized] target(s) in 24.41s
target/deploy/cap_hook.so                  85,784 bytes
```

The boundary is the design's own worked pair, and both sides are asserted: face
`1_000_000_000` with cap `2500` admits exactly `1_250_000_000` and refuses `1_250_000_001`.
Breaking the comparison from `lhs <= rhs` to `lhs < rhs` fails three of the four tests
(measured, then reverted), which is the point of having them.

## 2. The publish script

`tools/devnet_publish.py`, standard library plus this repository's own `ticketpath` package.
Nine steps, each of which reads the cluster before it writes, so a run that dies halfway is
resumed by running it again:

| step | how | idempotent because |
|---|---|---|
| balance ≥ 2 SOL | `solana balance --output json` | refuses with the faucet instruction below |
| build | `cargo-build-sbf` in `programs/cap_hook` | reuses an existing `.so` |
| deploy | `solana program deploy` | `getAccountInfo(programId).executable` |
| mint | `spl-token create-token --program-2022 --decimals 0 --transfer-hook <id> --enable-metadata`, then `initialize-metadata` | the artefact's mint is re-read from the cluster |
| wire | the `["extra-account-metas", mint]` and `["record", mint]` PDAs | each is checked with `getAccountInfo` |
| one ticket | `spl-token mint` | the authority's token balance is read first |
| the memo | `solana transfer <buyer> 1 --with-memo <memo>` | the recorded signature is re-read; if its memo still resolves, it is reused |
| the pair | stage a price, then a checked transfer with the preflight skipped | signatures are new every run, by nature |
| the artefact | `records/devnet-artefacts.json` | rewritten after every successful run |

`--dry-run` prints the plan and touches nothing (no build, no signing, no file, no validator).
`--local` starts a `solana-test-validator` with Token-2022 and Memo cloned from devnet, kills
it on every exit path (`atexit`, SIGINT, SIGTERM, the normal return), and writes
`records/devnet-artefacts.local.json` instead — which is git-ignored and which the loader
refuses to render as devnet.

**The faucet, exactly.** `solana airdrop` cannot work: the devnet RPC faucet answers error
**410**, "the RPC faucet is closed on this cluster". The script says so and prints the one
action that unblocks it, with the authority's public key:

```
REFUSED: balance is 0.000000000 SOL and this needs 2.00 SOL.
The devnet RPC faucet is closed (error 410), so `solana airdrop` cannot work and retrying it is wasted time.
Fund it yourself, once:
  1. open https://faucet.solana.com and sign in with GitHub
  2. network: devnet, address: <the authority's public key>
  3. request SOL, then run this again
```

## 3. Where the keypair goes, and the one place this deviates

The script never opens the keypair: `solana` and `spl-token` read it themselves when given
`--keypair <path>`, and there is no line in it that reads the file. A test enforces that
line by line, and a second test hands it a **directory** where a keypair should be and shows a
dry run still completes.

The deviation: `solana` and `spl-token` have no verb for "send this instruction", and three
instructions belong to this project's program — initialise the extra-account-metas list,
initialise the record, stage a price. Those three are built in Python and signed by
`tools/solana_sign.py`, a **separate process** whose only output is one base58 signature. It
uses `ticketpath/core/ed25519.py`, which the suite already proves against RFC 8032's published
vectors; it verifies the signature it just made before printing it, and it refuses a keypair
whose public half does not match its seed. The parent never sees a key byte, so no print, log
line or traceback in the publisher can carry one.

Why not a Rust client: it exists from the previous run and works, but it is a second crate, a
2-minute build and a 1.1 GB target directory for three instructions. Why not `solana-keygen`:
it has no "sign this message" verb (`new`, `pubkey`, `recover`, `grind`, `verify`, `bls_pubkey`
are the whole set) and `solana sign-offchain-message` wraps the bytes in an off-chain header,
so its signature is not a transaction signature.

## 4. The boundary, as a pair

The cap is `p * 10_000 <= f * (10_000 + cap_bps)` with `f = 1_000_000_000` and `cap = 2500`,
so `1_250_000_000` is admitted and `1_250_000_001` is refused. The previous run learned that a
refused transfer sent through `spl-token` dies in **simulation** and never gets a signature,
so the pair here is sent with `skipPreflight: true`: the refusal lands as a failed transaction
with its own signature and its own error, which is the only form of it a sceptic can look up.
Both legs take the same path and differ only in the staged price.

The transfer instruction is built here rather than by the CLI, with the account list and the
data bytes **read back from a landed `spl-token transfer`** on a local validator:
`[source, mint, destination, authority, record, hook program, extra-account-metas]` and
`[12, amount u64 little-endian, decimals]`. `tests/test_devnet_publish.py` pins those bytes
against the sample (`g7gn3dpVguJSb`), so a drift in the layout is a test failure rather than a
`MissingAccount` four failures later.

## 5. The local end-to-end run, public values only

Two runs against one kept ledger, to prove the idempotent path as well as the first-run path.
Program id, mint and signatures are **local cluster** values: they do not exist on devnet.

```
run 1 (fresh ledger)
  deploy: <program id>            deployed
  mint:   0 decimals, TransferHook -> program, MetadataPointer -> itself
  wire:   extra-account-metas and record created by the program
  ticket: 2 minted
  memo:   ticketpath:quote:q-18f4ec73dd8d8fd1:d90cb033491701947b711c6e07139282d1faae6041b77f5a99161bdd1f177b12
  stage 1250000000 -> transfer accepted
  stage 1250000001 -> REFUSED custom program error: 0x177a (6010 E_CAP_EXCEEDED)
  after: seller 1, buyer 1        (exactly one ticket moved)

run 2 (same ledger, no reset)
  deploy: already deployed and executable     -> skipped
  mint:   reused from the artefact            -> skipped
  wire:   both PDAs already exist             -> skipped
  memo:   reused, re-read at its slot         -> skipped
  ticket: topped up to 2
  stage 1250000000 -> transfer accepted
  stage 1250000001 -> REFUSED custom program error: 0x177a (6010 E_CAP_EXCEEDED)
  after: seller 1, buyer 1        (one crossed, one did not)
```

The artefact it writes carries only public data: cluster, RPC url, program id, mint, the memo
signature with its slot and block time, the quote it commits to, the two transfer signatures
with their slots, block times and the refused one's error, and — on devnet only — three
explorer links. The loader recomputes the quote hash from those fields and refuses the file if
it does not match, if the memo is not `ticketpath:quote:<quoteId>:<hash>`, or if the cluster is
not `devnet`.

## 6. What the operator runs, after funding

```
python3 tools/devnet_publish.py
```

It needs the authority to hold 2 SOL. Then it deploys, wires, mints, sends the memo, proves
the pair, and writes `records/devnet-artefacts.json`; the console's `[DEVNET]` slot flips on
the next reload. Nothing is pushed and nothing is published.

## 7. What failed, in the order it happened

| # | symptom | cause | fix |
|---|---|---|---|
| G1 | `spl-token address` refused, then returned "account not found" | the verb validates on chain and needs `--verbose` when given both `--token` and `--owner` | derive the associated token account with `solana find-program-derived-address`, which needs no cluster and matches the program's own derivation (checked against a recorded PDA pair) |
| G2 | "fee payer is required" on `create-account --owner <someone else>` | the owner is not the client keypair, so the CLI will not assume the payer | pass `--fee-payer` explicitly on every spl-token verb, from one command builder |
| G3 | `getTransaction` returned nothing for a landed transaction | the RPC default commitment is `finalized` and the call raced it | `commitment: confirmed`, then a bounded retry |
| G4 | the memo text was not found in the transaction | two log shapes exist: `Program log: Memo (len N): "text"` on devnet's program and `Program log: Memo (len N)` + `Program log: text` on the validator's built-in one; the memo also sits at a different program id locally | read instruction data first (base58, then base64), fall back to both log shapes, and check that *our* text is present rather than matching a program id |
| G5 | `--skip-preflight` is not an `spl-token` flag | it is a `solana` global | build the transfer instruction here and send it with `skipPreflight: true` |
| G6 | the refused transfer reported `Custom: 1` instead of `6010` | one ticket was minted, the admitted transfer spent it, so the second transfer failed on insufficient funds before the cap was reached | mint two: one for the admitted sale, one for the refusal; then assert the balances moved by exactly one |
| G7 | a second run against a kept ledger tried to redeploy a program that was already there | a validator answers `getHealth` before it has replayed, and every account reads as absent for a moment | six bounded looks at `getAccountInfo` before concluding "not deployed" |
| G8 | a breakage looked like it survived the test that catches it | a stale `__pycache__` served the unbroken module | purge bytecode between runs; recorded because a test run that lies is worse than no test run |

## 8. What is proven and what is not

**Proven, on a local cluster:** the program builds, deploys, and is invoked by Token-2022
through a real `TransferHook` extension; the cap admits exactly `1_250_000_000` and refuses
`1_250_000_001` with `0x177a`; the refused transfer moves no ticket; the memo carries the
console's grammar and the console's quote hash, and the loader recomputes it.

**Not proven:** anything on devnet. No devnet signature exists, because the faucet is closed
to this account. The publish script's devnet path has run only against a local validator with
devnet's Token-2022 and Memo cloned into it; the parts that differ on devnet are the rent
costs and the memo program id, and the read-back already handles both memo log shapes.

**Scope, unchanged from findings 18:** this is the cap check and nothing else. The hop record,
the destination check, the verified-wallet gate and the custody counters in
`docs/ON-CHAIN-DESIGN.md` §3.4/§3.9 are not implemented, so the honest claim is the second half
of D6's sentence — the program will not admit a price over the cap — and not the first.

## 9. Housekeeping

- Every validator this run started was killed; none is running. The rehearsal ledger was left
  in the machine's temporary directory on purpose (it is what a second run reuses) and can be
  deleted; both it and the artefacts it produced are ignored by git.
- The local buyer keypair is created by the script beside the authority, 0600, outside the
  repository, `solana-keygen new --silent` so no recovered phrase is ever printed.
- Nothing was pushed. The commit that carries this run's files is a single commit by explicit
  path.

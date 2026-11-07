# 18 — Solana toolchain install, and what was proven on chain

**Run:** SOLANA-INSTALL-AND-TEST, 2026-11-07. **Result: the toolchain is installed and
working; the devnet proof is blocked on funding, and the whole on-chain path was proven
against a local test validator instead.** Every number below was measured in this run,
with the command that produced it. Nothing here is an estimate except where the word
ESTIMATE appears.

Log of every command and its output: `~/tools/solana/INSTALL.log` (outside the repo).

| # | Step | State |
|---|---|---|
| 1 | 12G swapfile, persisted, swappiness 10 | **done, verified** |
| 2 | Rust 1.99.1, Agave CLI 4.3.2, spl-token-cli 5.6.1, cargo-build-sbf 4.4.0 | **done** |
| 3 | Devnet keypair, 0700/0600, outside the repo | **done, public key below** |
| 4 | Devnet funding | **BLOCKED — the devnet RPC faucet is closed, not rate-limited** |
| 5a | Memo transaction | **proven on a local validator** (devnet: no funds) |
| 5b | Token-2022 mint with TransferHook + MetadataPointer | **proven on a local validator** |
| 5c | Custom transfer-hook program, build → deploy → accept/refuse | **proven on a local validator**; devnet deploy blocked on funds |

The one-line answer to "is it on devnet?": **no.** Balance is 0 SOL and there is no
programmatic way to change that without the operator's GitHub session. Section 4 has the
exact error and the one action that unblocks it.

---

## 1. Swap

Free disk was 64G, RAM 7.9G with 1.5G available, and there was no swap at all.

| command | result |
|---|---|
| `sudo fallocate -l 12G /swapfile` | rc 0, 12,884,901,888 bytes, 0.053s |
| `sudo chmod 600 /swapfile` | `-rw------- 1 root root` |
| `sudo mkswap /swapfile` | `size = 12 GiB (12884897792 bytes)`, UUID recorded in the log |
| `sudo swapon /swapfile` | rc 0, `/swapfile file 12G 0B -2` |
| `free -m` after | `Swap: 12287 0 12287` |

Persisted with `/swapfile none swap sw 0 0` appended to `/etc/fstab`; `/etc/fstab` was
backed up first to `/etc/fstab.bak-20261107T182827Z`. Swappiness set to 10 in
`/etc/sysctl.d/99-swappiness.conf`; `sysctl vm.swappiness` returns `vm.swappiness = 10`.

**The swap earned its place on this run, which is the point of measuring it.** Peak swap
in use after the two cargo builds was **1784 MB**, measured with `free -m`. The box would
have been OOM-killing other agents without it.

Disk accounting, because 12G of swap is not free: `/` went from 13G to 33G used.
`/swapfile` is 12G of that; this run's toolchain and build trees are ~4.9G (table in
section 8). The remaining ~1G is other activity on the box, not measured here.

## 2. Toolchain, versions, and what each install cost

| component | version | how | wall time |
|---|---|---|---|
| apt libs | build-essential 12.10ubuntu1, pkg-config 1.8.1, libssl-dev 3.0.13, libudev-dev 255.4, protobuf-compiler 3.21.12, clang 18.0 | `apt-get install -y --no-upgrade`, those six names only, no upgrade, no removal | 15.6s |
| rustc / cargo | **1.99.1** (58cf8f9c3 2026-10-13) | rustup, `--profile default --default-toolchain stable`, installer read before running | 13.4s |
| solana-cli | **4.3.2** (feat:c9ad34d2, client:Agave) | `release.anza.xyz/stable/install`, script read in full before running | 7.2s |
| spl-token-cli | **5.6.1** | **prebuilt, bundled in the Agave release** — no `cargo install` needed | — |
| cargo-build-sbf | **4.4.0**, platform-tools v1.57 | bundled in the same release | — |
| Anchor / avm | **not installed** | 5c says Anchor optional; native Rust + `cargo build-sbf` is the lighter route | — |

Both installer scripts were downloaded to disk, read, and only then run:

- `rustup-init.sh`, sha256 `d890e2fef6fa991b19cde2e608199bc1dca4e37f41f884edf8849ff693048de6`.
  Grepped for `rm -rf|/etc/|sudo|eval`: the only matches are its own curl error handling and
  a `base64 -d` for its embedded payload. No sudo, no `/etc` writes.
- `anza-install.sh`, sha256 `8443d7940e9bbb336d9c52082759cb7da58bbe1fffa30cc75d21e7f43d0a1a8a`.
  Full text read: it picks the platform, downloads `agave-install-init-<target>` from
  `release.anza.xyz`, and runs it. Run with `--no-modify-path` so the PATH edit is ours.

PATH block appended to `~/.profile` (backed up to `~/.profile.bak-solana-20261107T182943Z`
first), between `# solana toolchain` and `# end solana toolchain`, each entry guarded by a
`case ":$PATH:" in` test so a re-run cannot duplicate it. Verified in a real login shell:

```
$ bash -lc 'command -v solana; command -v spl-token; command -v cargo; solana --version'
.../active_release/bin/solana
.../active_release/bin/spl-token
.../.cargo/bin/cargo
solana-cli 4.3.2 (src:0f131d36; feat:c9ad34d2, client:Agave)
```

`grep -c '^# solana toolchain$'` = 1 and `^# end solana toolchain$` = 1: one block, not two.

## 3. Key handling

- Directory `~/.config/ticketpath-devnet` at **0700**, keypair `authority.json` at **0600**,
  both outside the repository. `stat -c '%a %n'` confirms `700` and `600`.
- **Public key: `75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy`.** That is the only part of
  the keypair this document contains, and the only part any report should contain.
- Config: `solana config set --url devnet --keypair ~/.config/ticketpath-devnet/authority.json`;
  `solana config get` then reports `RPC URL: https://api.devnet.solana.com`.

**Incident, recorded because it happened.** `solana-keygen new` prints the 12-word recovery
phrase by default, and on the first run that line went into `INSTALL.log`. That keypair was
never funded and is discarded: the keypair was regenerated with `--silent`, which suppresses
the phrase entirely, and the phrase line was redacted from the log. **The pre-scrub backup of
the log held the same line and was redacted too** — a scrub that leaves a copy behind is not a
scrub. A sweep of `~/tools/solana` and `/tmp` for the 12-word shape now returns **0 files**, and
`grep -c` of that shape returns 0 in both the log and its backup. **`--silent` is mandatory on
`solana-keygen new`**; the flag is `-s`/`--silent`, "Do not display seed phrase".

### The repository's own guard did not cover this, and now does

Measured, not assumed. A scratch git repo at `/tmp/solana-safety-scratch` holding a **fake**
64-integer keypair array (same shape as a real one, random bytes, never funded) was checked
with the repository's current `.public-denylist`:

```
$ python3 tools/public_safety.py check --staged
public_safety: clean, staged, 20 file(s)
rc=0
```

That is a gap: the checker would have allowed the commit. Three rules were added and the
same check then returned `rc=1` with `authority.json: secret-file: file name` and
`authority.json:1: secret-file: [290 chars redacted]`. A rename test proves the shape rule
works on its own: the same bytes copied to `fixtures-notes.json` were still caught by
content. Negative controls (a pubkey string, a 32-element array) do not fire.

Added to `.public-denylist`:

```
path secret-file     (?i)(^|/)(authority|keypair|id)[^/]*\.json$
path secret-file     (?i)(^|/)[^/]*keypair[^/]*\.json$
content secret-file  all    ^\s*\[\s*(?:-?\d{1,3}\s*,\s*){63}-?\d{1,3}\s*\]\s*$
```

and the matching `authority*.json` / `*keypair*.json` / `**/…` patterns to `.gitignore`,
verified with `git check-ignore` on six paths including nested ones.

**Nothing was committed.** `.gitignore` and `.public-denylist` are modified in the working
tree and not staged. The repository's tracked tree already failed the checker **before** these
rules, with 77 hits, all in the classes the older rules own (`live-service` 51, `home-path`
23, `fleet-repo` 3) from `records/` quoting pids and paths. The new rules produced **zero**
`secret-file` hits on the tracked tree, so they added nothing to that count.

## 4. Devnet funding: blocked, and the CLI's error message is misleading

`solana airdrop 2`, five attempts with 5/10/20/40s backoff, all failed. The CLI says:

```
Requesting airdrop of 2 SOL
Error: airdrop request failed. This can happen when the rate limit is reached.
```

**That message is wrong.** Asking the RPC directly gives the real reason:

```
$ curl -sS https://api.devnet.solana.com -d '{"jsonrpc":"2.0","id":1,"method":"requestAirdrop","params":["<PUBKEY>",2000000000]}'
{"jsonrpc":"2.0","error":{"code": 410, "message":"The RPC faucet is closed on this cluster. Request test SOL at https://faucet.solana.com"}, "id": 1 }
```

Error **410**, "the RPC faucet is **closed** on this cluster". Not a rate limit, so no amount
of retrying fixes it, and a retry loop against that message wastes hours. The cluster itself
is healthy: `getHealth` returns `{"result":"ok"}` and `getVersion` reports
`solana-core 4.4.0`.

The documented alternative needs an authenticated session:

```
$ curl -sS -X POST https://faucet.solana.com/api/request -H 'Content-Type: application/json' \
    -d '{"network":"devnet","walletAddress":"<PUBKEY>","amount":1}'
GitHub authentication is required. Please sign in with GitHub to use the faucet.
```

**The one action that unblocks everything below:**

1. Open <https://faucet.solana.com> and sign in with GitHub.
2. Network **devnet**, paste this address:
   **`75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy`**
3. Request SOL. 2 SOL is plenty for everything here (a program deploy costs ~2 SOL of rent;
   signatures are 5000 lamports each).

Then `solana balance` reads it back, and the devnet half of section 5 can be re-run with the
same commands. `solana airdrop` will keep saying "rate limit" until the RPC faucet is reopened;
do not wait for it.

## 5. What was proven, and on which chain

Devnet has no funds, so 5a to 5c were proven against **`solana-test-validator`**, a local
single-node cluster started for this run and stopped at the end of it. Token-2022 and the Memo
program were **cloned from devnet** into it, so the programs executing are devnet's programs:

```
$ solana-test-validator --reset --clone-upgradeable-program TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb \
    --clone MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr --url https://api.devnet.solana.com
$ solana account TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb   → Owner: BPFLoaderUpgradeab1e...
$ solana account MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr    → Owner: BPFLoader2111...
```

**These signatures are local-cluster signatures.** They do not exist on devnet and an
explorer URL for them on `?cluster=devnet` will 404. Every devnet URL that follows is marked
**[devnet, once funded]** and is the one to re-issue.

### 5a. The memo, and what it commits to

The payload came from the console by GET, as instructed. The pricing decision behind it came
from the project's own orchestrator (`build_orchestrator()` → `price_guidance`), not from a
number typed by hand:

```
event            evt_syn_02  (slug synthetic-stage-cap-binding)
mode             counterfactual
asOf             2026-11-07T18:34:29.183Z   (pinned, so the hash reproduces)
recommended      1_380_000_000 lamports = 1.38 SOL
basis            lower_bound_at_cap       refused: false
canonical JSON   {"asOf":"2026-11-07T18:34:29.183Z","basis":"lower_bound_at_cap",
                  "eventId":"evt_syn_02","modelVersion":"engine-2026-11-07",
                  "recommendedLamports":1380000000,"tierId":"tier_stg_general"}
sha256           085d5ea0a07ba722e35b62c48081be1e25657bd48a2acc30f761b3e3509ef2ac
memo (129 bytes) ticketpath:v1:evt_syn_02:counterfactual:2026-11-07T18:34:29.183Z:
                 085d5ea0a07ba722e35b62c48081be1e25657bd48a2acc30f761b3e3509ef2ac
```

`before_on_sale` was tried first and **honestly refuses** on this event:
`refusalCode: no_resale_record`. That is the mode refusing to price an event with no resale
record at the cut, which is the behaviour the design asks for. The commitment therefore uses
`counterfactual`, and says so in the memo.

Memo transaction, read back with the chain's own logs:

```
sig  2NrUUq5fkjbxeTZEmoRwceK2okpiwQ7CoFrF7Q3u9GnhR6FfYUQ2CeLqmaXkj8ESfWwqREVkwVXHaSu6JbSiiE3c
slot 679, status Ok, fee 5000 lamports, 60523 CU
      Program log: Memo (len 129): "ticketpath:v1:evt_syn_02:counterfactual:..."
```

**[devnet, once funded]** `https://explorer.solana.com/tx/2NrUUq5fkjbxeTZEmoRwceK2okpiwQ7CoFrF7Q3u9GnhR6FfYUQ2CeLqmaXkj8ESfWwqREVkwVXHaSu6JbSiiE3c?cluster=devnet`

### 5b. Token-2022 mint with TransferHook and MetadataPointer

`--transfer-hook` and `--enable-transfer-hook` are mutually exclusive; the former enables the
extension. A ticket must be **one base unit**, so the mint is created with `--decimals 0`
(see failure F2).

```
mint     7jobXedkdwKo94PLenYcHzSB4J2QgvDihRKSTGjWahz5
create   63Etf6nZ8EXsw1KqBLgXLk1FSQazvP8x54gJLZPiR1T59uWRCTq5sEsw6mUi6qXma6DUEmHeEsq5KMAkwPLMpYtg
metadata 5g7Rhek4A99jJiQzjuCAC12uAExf5fUctvUxKs9KsNjnT7nmnskGvkbb7xS9Ds2KvTodgoZ2vBkpN24MhSGW5NJd
token acct 79S7BqsXisPgarEzJ4StUsjHCPZSqZ5kpq7gsHptpBEw   (29GHUaacKHAv5K4iNqrQDdfAk4Hq24EFxSCfWe4yQqYAsMF5K1N6ztMLipKaBXHzWtU5HPf3k1B63wx2bvGKrBhm)
mint 1   nwQrChfVW6etCz4RCwJR8SXD2h1rGJzZEtx4yPeQeNsSjd1JwTvKK7wWMZ1EWfcssDsmPiiFdSBQCcpMcFrK4QC
buyer ATA 3vNznfqesFf1J44s8zNEXHagekghbDVv2Kw9ceoeVXMU (2jJDi6t4zEv9hrcWihnr6wv8YW7b4ouDUVX2vHiD8mXygxpiDBKScXUZ3yvV7xUiYVYfgQEV5DsTRbGeoAvEr4Hb)
```

Read back from the account, which is what the app has to parse:

```
owner TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb, data len 460 bytes
byte[165] = 1 (Mint)
TLV from 166: (14, 64) TransferHook, (18, 64) MetadataPointer, (19, 154) Metadata
spl-token display → Transfer Hook Program Id: BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ
                    Metadata Pointer address = the mint itself
                    Metadata: name "Ticketpath Synthetic Ticket", symbol TKT, uri .../evt_syn_02
```

### 5c. The custom transfer-hook program

Source: `~/tools/solana/ticketpath-hook/` (outside the repo). Native Rust, ~330 lines, no
Anchor, using `spl-transfer-hook-interface` and `spl-tlv-account-resolution`. The cap check is
§3.10 verbatim, `u128` both sides, no division:

```rust
let lhs = (self.pending_price_lamports as u128) * 10_000u128;
let rhs = (self.face_value_lamports as u128) * (10_000u128 + self.cap_bps as u128);
lhs <= rhs
```

Four native unit tests pass, including the design's own worked pair (face 1e9, cap 2500:
1_250_000_000 admitted, 1_250_000_001 refused).

```
$ cargo-build-sbf --sbf-out-dir target/deploy
Finished `release` profile [optimized] target(s) in 21.84s
target/deploy/ticketpath_hook.so : 85,784 bytes, ELF 64-bit LSB, eBPF, statically linked, stripped
program id                       : BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ
deploy                           : 2K4Kg3q8oGxTNPdqsJ2W2zSWP11fMSBvfmkTK7zmQhMM8P1RX73geSToaqekfN7Enc2k2ATNm6m1BEwwRUk5EWXy
```

Wiring, then the boundary as a pair — face 1 SOL, cap 2500 bps, so the maximum admissible
price is exactly 1.25 SOL:

```
extra-account-metas PDA  4YbyqkQSGZHzq4kbLyixjWwbYvyrtZnYvwA2a1xPsfwN   9spgoZZGemNL9juzULssKjryLDgpCy49TzLnpS7xPxZYk7rL8n8nTMef4aYT5XWnC76q7cUHAXAao1F66wkMfQe
record PDA               CHYJMjXvTjPRdzo25QRDDEZzocvknDyWJ9mK3Fc8hxga   61ZrN3cERZUXr3HNkjeSJyumtjWNAgvaEY4rqMfjetf4EMYPpuuHzZbrr28cnCzbn6fH13epo834UGA5tR7q35XV
stage 1_250_000_000      6c7Sx85gFjcWp4FPfKVyEvzxEZz14zvKxFnsFgWYCxTQV5kqb7tKf2rNQjABCG4vqEPEoXWbqS9ukcdNjtGmYXv
```

**ACCEPTED, exactly at the cap.** Same code path for both sides, so the pair is comparable:

```
$ hook-client transfer-checked <mint> 1 <buyer_ata> <authority_ata> 0 --skip-preflight
sig 64PNqrfFq2MmJdjXFj9vdc8LrDfs6BpYLV5Nov4ii4d9z4GZwEVRTWzy5PH9Lgjwi5EaugYniYzykmtFGMJCudER
slot 1150, Status: Ok, fee 5000 lamports
  Program log: ticketpath: cap admitted price=1250000000 face=1000000000 cap_bps=2500
```

**REFUSED, one lamport above the cap.**

```
stage 1_250_000_001      3AFT3nsZuzM4rYLb5m8Rd2HLjc4rADB4wVxxPCHUfJXAe8oFLqjgwTH73nisBNTaZikSEvTEEgSBV3Z6qYKCUHpy
sig 53Q1Ksbuh5T4kLHDiEUcQhVdHHLo6NkyXF8nmvMiLXLnN67h5r9EMXg1xASrvK3BRgi23EHNbkPFbYCKj2xbvzgf
slot 1134, Status: Error processing Instruction 0: custom program error: 0x177a   (6010 = CapExceeded)
  Program log: ticketpath: cap exceeded price=1250000001 face=1000000000 cap_bps=2500
```

A refused transfer that fails preflight never gets a signature, so it cannot be shown. That is
why `transfer-checked` exists and runs with `skip_preflight: true`: the failing transaction
lands on chain with its own signature and its own error, which is the only form of proof that
survives a sceptic. `0x177a` is 6010, the design's `CapExceeded`.

The boundary is therefore demonstrated as a pair, which is the only way it means anything: one
lamport either side of 1.25 SOL, one accepted and one refused, both with signatures.

## 6. Failures, in the order they happened

Recorded because a report that only lists successes is not a measurement.

| # | symptom | cause | fix |
|---|---|---|---|
| F1 | `AccountNotFound` on the first hooked transfer | the extra-account-metas account was hand-rolled as `u32 count + 72-byte blobs`; the real layout is a **TLV state** (`TlvState` + `PodSlice<ExtraAccountMeta>`) | encode with `ExtraAccountMetaList::init` from `spl-tlv-account-resolution` |
| F2 | `custom program error: 0x1778` (6008 `AmountNotOne`) | the mint defaulted to **9 decimals**, so "1 token" is 10⁹ base units | create ticket mints with `--decimals 0`; one ticket is one base unit |
| F3 | `custom program error: 0x4` (Token-2022 `OwnerMismatch`) | the transaction was signed by the mint authority while the source account belonged to the buyer | sign as the source owner |
| F4 | `Unknown program BMrc…` then `MissingAccount` | the hand-built instruction omitted the hook **program account** and had the remaining accounts in the wrong order | mirror the order a working `spl-token transfer` produces: `[source, mint, dest, authority, record, hook_program, extra_metas]` |
| F5 | `spl-token-2022 v7.0.0` failed to compile | its confidential-transfer modules need feature flags that `default-features = false` removes | not needed at all: the client sends only this project's instructions, and every token instruction comes from the CLI |
| F6 | recovery phrase written to `INSTALL.log` | `solana-keygen new` prints it by default | keypair discarded un-funded, regenerated with `--silent`, log line redacted |
| F7 | "rate limit", five attempts | **not a rate limit**: the devnet RPC faucet is closed (410) | cannot be fixed by retrying; needs the operator's GitHub session |

## 7. Measured cost of the run

| what | value | how measured |
|---|---|---|
| SBF build, clean | **21.84s** | `cargo-build-sbf`, release profile |
| SBF build peak **Mem used** | **4590 MB / 7940** | sampler at 0.2s over the whole build, 107 samples |
| SBF build lowest **available** | **3350 MB** | same sampler |
| SBF build peak **swap used** | **14 MB** | same sampler |
| peak swap after both cargo builds | **1784 MB** | `free -m` |
| hook-client build (solana-client) | 2m22s first attempt, 51s clean | `cargo build --release` |
| `.so` size | 85,784 bytes | `stat` |
| rustup install | 1.5G | `du -sh ~/.rustup` |
| cargo + registry | 331M | `du -sh ~/.cargo` |
| Agave release | 258M | `du -sh ~/.local/share/solana` |
| hook program target | 251M | `du -sh …/ticketpath-hook/target` |
| hook-client target | 1.1G | `du -sh …/hook-client/target` |
| local validator ledger | 1.5G | `du -sh ~/tools/solana/validator-ledger` |

Every build ran `nice -n 10` with `CARGO_BUILD_JOBS=2`. The first build of the hook-client
was the memory-heaviest step of the run and is what pushed swap to 1.7G; nothing was
OOM-killed.

## 8. What the app needs in order to read any of this back

`ticketpath/adapters/rpc_adapter.py` is unchanged by this run, and it currently cannot report
any of the above: `transfer_enforcement()` returns `enforced: false, checked: false` with
reason `rpc_disabled` or `no_program_deployed`, and `program_status()` hardcodes
`programDeployed: false, programId: None`. That was true when it was written and it is still
true of **devnet**, which has nothing deployed. What would change is the local cluster.

To read this back the adapter needs, in order of cost:

1. **Turn it on.** `TICKETPATH_RPC_ENABLED=1`, `TICKETPATH_RPC_URL=<rpc>`,
   `TICKETPATH_PROGRAM_ID=BMrcjbC2mq99YnFKkDGJDK9x1wchDmytotuhrSkfRLWQ`. Off by default is
   correct and should stay the default.
2. **`getAccountInfo(programId)`** → `owner == BPFLoaderUpgradeab1e…` and `executable == true`
   is what `program_status().programDeployed` should actually mean, instead of a constant.
3. **`getAccountInfo(mint)`**, parse the mint: byte 165 is the account type (`1` = Mint), then
   TLV from 166. Type **14** is TransferHook, 64 bytes = authority(32) + program_id(32); type
   **18** is MetadataPointer; type **19** is Metadata. Seeing type 14 with a program id is the
   only honest basis for `transferRestricted: true` — it is a fact about the mint, not about
   the event config.
4. **The record PDA** `find_program_address(["record", mint], programId)`: 19 bytes,
   `face_value_lamports u64 LE | cap_bps u16 LE | pending_price_lamports u64 LE | status u8`.
   That is what a backend prices against, and it is one `getAccountInfo`.
5. **The extra-account-metas PDA** `["extra-account-metas", mint]`, TLV, only needed if the
   app wants to check the hook is actually wired for that mint.
6. **The memo**, for the console's `[DEVNET]` slot: `getTransaction(sig, {maxSupportedTransactionVersion: 0})`.
   Measured on all three transactions above:

   | sig | slot | `meta.err` | `meta.fee` |
   |---|---|---|---|
   | `64PNqr…dER` (accepted) | 1150 | `None` | 5000 |
   | `53Q1Ks…zgf` (refused) | 1134 | `Custom: 6010` | 5000 |
   | `2NrUUq…E3c` (memo) | 679 | `None` | 5000 |

   One caution for whoever wires this: in `encoding: "json"` an instruction gives
   `programIdIndex`, not `programId`, so the memo is matched by resolving
   `message.accountKeys[programIdIndex] == MemoSq4gq…` and reading `data` as **base58** (or
   requesting `encoding: "base64"` and decoding). The memo also appears verbatim in
   `meta.logMessages` as `Program log: Memo (len 129): "…"`, which is how it was read back
   here, but logs are not guaranteed forever and the instruction data is.

### A divergence the app will trip on, and it should be a decision not a patch

The memo grammar the console already implements is **`ticketpath:quote:<quoteId>:<hash>`**,
with the hash over `CANONICAL_FIELDS = (quoteId, eventId, tierId, recommendedLamports, asOf,
modelVersion)` (`ticketpath/adapters/chain_client.py`). The grammar this run was told to use is
**`ticketpath:v1:<event>:<mode>:<asOf>:<sha256>`**. Both were produced for `evt_syn_02`:

```
v1      ticketpath:v1:evt_syn_02:counterfactual:2026-11-07T18:34:29.183Z:085d5ea0…
repo    ticketpath:quote:q-18f4ec73dd8d8fd1:62e8dc452efb12b190c6a264590bb7b14585a0fb1e27c33557bbd2e93c7dcdd4
```

They are different strings and different hashes. The console renders a `[DEVNET]` slot only
when `records/devnet-artefacts.json` exists **and** its `quoteHash` recomputes from the fields
on screen under the repository's own `quote_hash`. A `v1` memo would therefore render as
`unverified`, not as a slot. **`records/devnet-artefacts.json` was deliberately not written**:
writing it from a `v1` hash would have produced a file that fails its own recomputation, which
is worse than an absent file. One grammar has to win, and the repo one is the one the console
already verifies against.

## 9. What is not proven, and what it would take

- **Nothing is on devnet.** No devnet signature exists. Section 4 has the one action that
  changes that; the commands in section 5 are the ones to re-run, with `--url devnet`.
- **The hook is not a full implementation of §1.3/§3.9.** It enforces `amount == 1`, the
  extra-metas identity, the record's status flag, and the cap. It does **not** implement the
  `pending_dest` destination check, the custody-hop counters, or the record write-back, so it
  is the cap check and nothing else. This is the scope the brief set ("the smallest possible
  custom transfer-hook program … the cap check before the transfer").
- **The price is staged by a free-standing instruction.** The design says the staging belongs
  to the escrow or the listing (§1.4); `set_price` here exists only so the boundary can be
  measured. It is a demonstration scaffold, not the architecture.
- **ESTIMATE:** deploying the same `.so` to devnet costs about 2 SOL of rent (85,784 bytes at
  the rent-exempt rate) plus ~10 signatures. Not measured, because there were no funds.

## 10. Housekeeping

- Local validator stopped at the end of the run (`solana-test-validator` is not running). Its
  ledger stays at `~/tools/solana/validator-ledger` (1.5G) and can be deleted, or restarted
  with the `--reset` command in section 5.
- `~/tools/solana/` holds the two crates, the installers, the keypairs for the **local**
  cluster (`local-test.json`, `buyer.json`, and the program keypair at
  `ticketpath-hook/target/deploy/`), all 0600, all outside the repository.
- The devnet authority at `~/.config/ticketpath-devnet/authority.json` is 0600 in a 0700
  directory and holds 0 SOL.
- Nothing committed, nothing pushed, `ticketing-frontend` untouched.

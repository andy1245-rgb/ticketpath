# 40 — The memo program id is a per-cluster fact, and this repository had the wrong one

**Run:** FEATURE-1, 2026-11-08. **Result: the tree now carries a measured devnet memo program
id, resolves it per cluster, and refuses a cluster it has no measurement for.** One read-only
`getTransaction` and one read-only `getAccountInfo` were made against devnet; nothing was
signed, sent, deployed or written to any cluster, and no keypair file was opened.

## 1. What was wrong

`ticketpath/adapters/chain_client.py` held one constant for every cluster:

```python
MEMO_PROGRAM_ID = "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr"
```

That is the memo program the `solana` CLI ships with (memo v3). It is not the program the
proven devnet memo transaction invoked. Three callers used the constant: `quote_commit` (the
instruction the console says it would submit), `tools/devnet_publish.py` (`MEMO_PROGRAM`, used
for the local validator's `--clone`), and `ticketpath/orchestrator.py` (`memoProgram` in the
chain payload). Nothing read the id back off a landed transaction, so no run could notice: the
wrong id was a statement nobody checked, which is the failure mode this finding is about and
not a typo in one string.

## 2. The measurement

**Method.** One `getTransaction` against `https://api.devnet.solana.com`, `encoding: json`,
`maxSupportedTransactionVersion: 0`, bounded at 25s, for the proven devnet memo transaction
`2Lx6cboK8kvuJ7H6w2CELvZg3xF7cSHtBTSBXqi1w6KN2eXkQ6skqNPwnT5iVVAdrfBs5LiAau3pXiBMTtZMGCPZ`.

**When.** 2026-11-08T05:39:47Z. HTTP 200, 1,708 bytes.

The response's account keys, quoted exactly from the body:

```
"accountKeys":["75UcdvvgZYVK6Z8BCs8RnNP4WBpDiTtKBEijZxdovxGy","2k1PvrHrue11in9kmwV9gjhLtFMVM8ndHSFiscV79GVd","11111111111111111111111111111111","Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH"]
```

Its second instruction, quoted exactly:

```
{"accounts":[],"data":"5XQZChR55k7uSMkT4Ct2PiGJpYbwZLpuimkWSRHfz69krivPTtKUK7smk24JY69FhHQteWMC212Mz2nXWkuznqAiaSVZPw9qBKTcsb52dbkb3uQUgaVRkS5sC6kZpSjyYaxuhTqAR","programIdIndex":3,"stackHeight":1}
```

So `accountKeys[3]` is the program the memo instruction ran on, and it reads
`Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`. The same body carries `"slot":519845921`,
`"blockTime":1794099003`, and in `meta.logMessages`, quoted exactly,
`"Program Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH invoke [1]"` followed by
`"Program log: Memo (len 100)"`.

| id | cluster it belongs to | how it is known |
|---|---|---|
| `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH` | devnet | measured here, `accountKeys[3]` and `programIdIndex 3` of the transaction above |
| `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr` | mainnet-beta, and a local validator | the CLI's own memo program; **not measured from mainnet in this run** (see §6) |

**A second read, which explains why the wrong constant never failed a run.** At
2026-11-08T05:45:55Z, `getAccountInfo` for the CLI's id against devnet answered:

```
"executable":true,"lamports":41509619334,"owner":"BPFLoader2111111111111111111111111111111111","space":7480
```

Devnet hosts both memo programs. A memo written to the CLI's id on devnet would have landed and
been readable, which is why nothing broke; what was broken was the record, the console's
`memoProgram`, and any consumer that filtered on the id the repository named. The bug was
misdirection, not a failed transaction, and that is worth saying because it is the reason a
green test suite never caught it.

## 3. The fix

`ticketpath/adapters/chain_client.py`:

- `MEMO_PROGRAM_DEVNET` is the measured id, `MEMO_PROGRAM_CLI` is the CLI's, and
  `MEMO_PROGRAMS` maps `devnet` to the first and `mainnet-beta` and `localnet` to the second.
- `memo_program_id(cluster)` is the one way to read it. An unmeasured cluster raises
  `UnknownCluster` naming the cluster and the clusters the table covers. There is no fallback
  and no default id: `MEMO_PROGRAM_ID` is gone, so nothing can accidentally keep using one
  string for every cluster.
- `quote_commit` takes `cluster` and names that cluster's id in its instruction.

`ticketpath/orchestrator.py`: the chain payload passes `self.cluster` to `quote_commit` and
fills `memoProgram` from the table. A cluster the table has no measurement for makes that
field `null` rather than raising, because the server accepts four clusters and a payload field
that raises on one of them is a page that cannot render; `null` is a statement, a neighbouring
id would be a lie the page cannot detect.

`tools/devnet_publish.py`: the module no longer holds a memo id at all. The run asks the table
for its own cluster, and the local validator's `--clone` names the devnet program because that
is the cluster it clones from (`--url <devnet>`).

## 4. What is checked at run time now

`tools/devnet_publish.py` already read its memo transaction back to confirm the text landed.
It now also reads the id: `_memo_program_ids` returns the program ids of the instructions whose
data decodes to a memo in that transaction, and `assert_memo_program` compares the table's id
for the run's cluster against them, raising one sentence naming both ids when they differ. It
runs on both paths that read a memo transaction, the reuse path and the fresh-send path, so a
resumed run is held to the same check as a first one.

The artefact now records `memoProgram`, resolved from its own `cluster`, for devnet and for the
local rehearsal alike. It is additive: `load_artefact` neither requires the field nor treats its
absence as a failure, and the proven `records/devnet-artefacts.json` was not touched. The loader
reads the recorded value back unchanged instead of re-deriving it, so the artefact says what a
run saw and today's constant cannot overwrite an older observation.

## 5. Tests added (16, and the tree is green)

`tests/test_onchain_sim.py`:

- the table's devnet id equals the measured id, and the default lookup agrees;
- `mainnet-beta` and `localnet` both resolve to the CLI id;
- the table is not one string for every cluster;
- an unknown cluster (`testnet`) refuses, and the refusal names no other cluster's id;
- `quote_commit` for devnet names the devnet id, for localnet names the CLI id, and for an
  unknown cluster refuses;
- an artefact written before `memoProgram` existed still verifies, and reads back as `None`;
- a recorded `memoProgram` is read back unchanged.

`tests/test_devnet_publish.py`:

- the artefact records the memo program of its own cluster, devnet and localnet;
- the recorded value survives the write and the file still verifies;
- a record with the field deleted still verifies (backward compatibility at the publish level);
- the run-time assertion fires when the landed program id differs, naming both ids;
- it passes when the landed id is the table's, and the ids are read back;
- a local rehearsal is held to the localnet id and not to devnet's;
- the measured devnet answer, with the account keys and the `programIdIndex` quoted in §2, reads
  back as the devnet id through the real reader.

## 6. What is still unverified

- **The localnet mapping.** Nothing on this machine can start a local validator: `which solana
  solana-test-validator spl-token` answers nothing, exit 1. So "a local validator answers at
  `MemoSq4gq...`" is the CLI's documented behaviour and this repository's assumption, not a
  measurement. If a rehearsal's memo lands under any other id, the new assertion stops the run
  with both ids, which is the designed outcome and also the untested branch.
- **The `--clone` of devnet's memo program into a local validator.** The rehearsal clones
  `Memo4c2p...` from devnet, while the table says a local run's memo program is
  `MemoSq4gq...`. Both can be true at once only because the CLI writes its memo instruction to
  its own program. Untested here, and the first rehearsal on a machine with the toolchain will
  settle it.
- **The mainnet-beta id.** Not measured against mainnet in this run: no mainnet call was made.
  The value is the CLI's shipped memo program, which is class D by this programme's scale
  until someone reads it off mainnet the way §2 read devnet's.
- **`testnet`.** Deliberately absent from the table. No memo program has been measured there,
  and a wrong id is worse than a refusal.
- **Anything about which id the CLI chooses on devnet.** The measured transaction was produced
  by an earlier run; this run did not send one, so "the CLI writes `Memo4c2p...` on devnet" is
  observed once, not established as a rule.

## 7. Classification, per the programme's scale

| claim | class |
|---|---|
| devnet's memo program is `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, and devnet also hosts `MemoSq4gq...` | **A**, measured here on 2026-11-08, quoted above |
| a run can read the memo program id back out of its own landed transaction and compare it | **A**, the reader is exercised against the measured body (a test, not a cluster call) |
| mainnet-beta's memo program is `MemoSq4gq...` | **D**, the CLI's shipped id, not measured from mainnet here |
| a local validator answers at `MemoSq4gq...` for a CLI-written memo | **D**, untested: no toolchain on this machine |

## 8. For the doc steward

Six sentences elsewhere in the tree now name the memo program, and they belong to whoever owns
those files, not to this run:

- `docs/ON-CHAIN-DESIGN.md` §1.3 and §6 describe the memo step without naming the program; if
  an id is stated anywhere in it, devnet's is `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`
  and mainnet's is `MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr`. The measured values and the
  quoted JSON to cite are in §2 above.
- `market_swarm/.research/chain-gateway-reuse.md` carries a `--clone MemoSq4gq...` line. That
  line is about the CLI's program on mainnet and is not wrong; a devnet rehearsal clones
  `Memo4c2p...`, as `tools/devnet_publish.py` now does.
- Anywhere the console's `memoProgram` field is documented, it may be `null` when the server's
  cluster has no measured id (`testnet` is the only such cluster today), and it must not be
  presented as the artefact's `memoProgram`, which is the value a run recorded.

## CORRECTION (2026-11-08T05:56Z): §6's toolchain sentence is wrong; the toolchain is installed

**What was wrong.** §6 says: "Nothing on this machine can start a local validator: `which solana
solana-test-validator spl-token` answers nothing, exit 1." That sentence is true of a non-login
`PATH` and false of the machine. The implementer checked `PATH` and concluded absence, which is the
same misreading `README.md` records for an earlier pass ("A non-login shell still prints nothing for
them, which is why an earlier reading of this file said there was no toolchain"), and §6 should not
have repeated it as a fact about the machine.

**How it was found.** The documentation pass listed the install root directly, then ran each
binary from its absolute path:

```
$ ls <agave-install-root>/bin/
agave-install  agave-ledger-tool  cargo-build-sbf  cargo-test-sbf  solana
solana-keygen  solana-stake-accounts  solana-test-validator  solana-tokens  spl-token
$ <agave-install-root>/bin/solana --version              -> solana-cli 4.3.2 (src:0f131d36; client:Agave)
$ <agave-install-root>/bin/solana-test-validator --version -> solana-test-validator 4.3.2 (src:0f131d36; client:Agave)
$ <agave-install-root>/bin/spl-token --version           -> spl-token-cli 5.6.1
$ <agave-install-root>/bin/cargo-build-sbf --version     -> cargo-build-sbf 4.4.0, platform-tools v1.57, rustc 1.95.0
```

`<agave-install-root>` is the Agave `active_release` install that `records/findings/18` records; the
path is omitted here because it is a home path and this repository is public.

**What this changes in §7, and what it does not.** No class moves: nothing here measured a cluster,
so the two rows that were class **D** because they were untestable stay **D** until someone runs
them. What changes is that they are now *testable on this machine*, and the reason they were marked
untestable is void:

- "a local validator answers at `MemoSq4gq...` for a CLI-written memo": `solana-test-validator`
  is installed, so a local ledger can be started and the CLI's memo written to it. Still class D
  until that run is made.
- "the `--clone` of devnet's memo program into a local validator": the same install makes the
  rehearsal possible, and `tools/devnet_publish.py --local` is the path that would exercise it.
  Still class D until it is run.

The rest of §6 stands as written, including the mainnet id (class D, still unmeasured from
mainnet) and `testnet` (still absent from the table by design). This section is appended rather
than edited into §6 because `records/` is append-only.

## CORRECTION (2026-11-08T07:05Z): the localnet row was a guess, and it was the wrong one

**Measured, not assumed.** The toolchain the previous correction proved is installed was used to
settle the two rows this finding left at class **D**. Everything below happened on a local
validator started from a fresh ledger under `.swarm-runs/`, funded at genesis with `--mint`, with
no faucet call and no devnet transaction. The only devnet calls were reads: one `getAccountInfo`,
and `--clone` sources.

```
$ solana --version              -> solana-cli 4.3.2 (src:0f131d36; feat:c9ad34d2, client:Agave)
$ solana-test-validator --version -> solana-test-validator 4.3.2 (src:0f131d36; feat:c9ad34d2, client:Agave)
$ solana transfer <dest> 1 --from <payer> --with-memo "ticketpath:quote:probe:<hash>" --allow-unfunded-recipient --url http://127.0.0.1:<port>
```

**What the CLI writes.** `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, not `MemoSq4gq...`. On a
fresh local ledger the transfer is refused in simulation, and the log names the program the CLI
built the instruction for, quoted exactly:

```
Program 11111111111111111111111111111111 invoke [1]
Program 11111111111111111111111111111111 success
Program Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH invoke [1]
Program is not deployed
Program Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH failed: Unsupported program id
```

That is the same id the proven devnet transaction ran under (§2), produced by the same CLI, so
"the CLI writes `Memo4c2p`" is now an observation of a landed devnet transaction **and** of the
instruction this machine's CLI builds, not a memory of documentation. §6's last bullet said that
sentence was "observed once, not established as a rule"; it is established for the installed CLI.

**Why it does not land locally.** A local validator's genesis holds both ids, and holds the
second one as a stub:

| id | owner | lamports | space | data |
|---|---|---|---|---|
| `MemoSq4gq…` | `BPFLoader2111…` | 521,498,880 | 74,800 | an ELF; it executes |
| `Memo4c2p…` | `BPFLoaderUpgradeab1e…` | 1,141,440 | 36 | Program state, pointing at `HPD8Gxq19uaXy6zDaEGBtkb9NEZwd4jRTnXQ4GM8qe86` |

The programdata account at that address exists, and its first twelve bytes are the difference:

```
local  (after --clone-upgradeable-program): state=3 slot=0          space=2349 lamports=17,239,920
devnet (read-only):                         state=3 slot=464109537  space=2349 lamports=17,239,920
```

`ProgramData.slot = 0` is what the runtime refuses, which is why the log says "Program is not
deployed" and not "account not found". Three attempts to fill it all failed the same way:
`--clone Memo4c2p…`, `--clone-upgradeable-program Memo4c2p…`, and `--clone` of the programdata
account itself. The genesis account wins over the clone, so **a local rehearsal cannot land a memo
transaction with this CLI version at all.** That is measured, not inferred, and it is the reason
the local path's clone is now documented as "leaves the ledger holding devnet's account" rather
than as what makes the rehearsal work.

**Does one clone shadow the other id?** No, and the answer for each id is different.
`--clone MemoSq4gq…` from devnet **replaces the local genesis account at that id** — the lamports
went from 521,498,880 to devnet's 41,509,619,334, with the same owner and the same 74,800-byte
space — and leaves `Memo4c2p…` exactly as it was. Cloning `Memo4c2p…` leaves `MemoSq4gq…` alone.
The clone overwrites the account at the same address; it does not move a program from one id to
the other, and it cannot deploy the stub.

**What changed in the tree, and what did not.**

- `MEMO_PROGRAMS` now holds `devnet` and `localnet`, both `Memo4c2p…`, and nothing else.
  `mainnet-beta` is **removed**: its row was `MemoSq4gq…` on the strength of "the CLI's shipped
  program", and the CLI has now been measured writing a different id, so that row was a guess the
  evidence contradicts — the same defect as the localnet row. Nothing has been read off mainnet,
  so nothing is named for it, and `memo_program_id("mainnet-beta")` raises `UnknownCluster` like
  `testnet` does.
- `MEMO_PROGRAM_CLI` stays as a named literal, with the comment saying what it is not, because
  `README.md` and `docs/ON-CHAIN-DESIGN.md` quote it and the `ids` gate compares quoted ids
  against the literals this file carries. Those files belong to the doc steward; the lines that
  now need changing are listed at the end of this correction.
- The local publish path clones `chain_client.memo_program_id("localnet")`, which is the id the
  CLI writes, and says in its comment that the clone does not make the memo executable.
- The artefact records the id the run **read back** off its own transaction
  (`memo["memoPrograms"][0]`), not `chain_client.memo_program_id(cluster)`. The table is now only
  the expected value the assertion compares against, so a file can show what the cluster did.
- `assert_memo_program` asserts on the **(text, program id) pair** whose text equals the memo the
  run sent. `_memo_instructions` returns pairs and `_programs_for` filters with `text == memo`;
  the previous version matched program ids against a list of every decodable string in the
  transaction, which is satisfied by the System program. Two memos under two programs now fail
  the check instead of passing both clusters.
- The fresh-send path has tests. §5 said it was covered; it was not, and now it is: an empty
  resume file, a faked `solana transfer` signature, a faked confirmation, and a `getTransaction`
  that answers under the wrong program — plus the matching case.

**Three smaller wrongs in this finding, appended rather than edited.**

- §2 quotes `"space":7480` for `MemoSq4gq…`. Devnet answers `"space":74800` today, measured
  2026-11-08T07:01:53Z: `{"executable": true, "lamports": 41509619334, "owner":
  "BPFLoader2111111111111111111111111111111111", "space": 74800}`. The zero was dropped in
  transcription; `records/BUILD-SPEC-NIGHT.md` carried the right number.
- §8 says `market_swarm/.research/chain-gateway-reuse.md`'s `--clone MemoSq4gq…` line "is about
  the CLI's program on mainnet and is not wrong". It is wrong as written: the code it describes
  clones `memo_program_id("devnet")`, which is `Memo4c2p…`, and the line numbers it cites moved.
  That note is outside this run's edit scope; it needs re-pointing or marking as a snapshot.
- The previous CORRECTION said "the rest of §6 stands as written". The sentence it corrects is in
  §6, so the honest form is "the rest of §6 apart from that sentence". Its quoted `ls` also
  omitted `agave-install-init` and `deps`, which are in that directory, and its `solana --version`
  line dropped `feat:c9ad34d2`. Both are quoted whole at the top of this correction.

**Classification, replacing §7's last two rows.**

| claim | class |
|---|---|
| the shipped CLI's `--with-memo` instruction names `Memo4c2pN8afCj432Lb7RMVKi9PbQnnW7ewFFaV3oAH`, on devnet and on a local validator | **A**, measured 2026-11-08: the landed devnet transaction's `programIdIndex`, and the local simulation's `invoke` line |
| a local validator's genesis holds `MemoSq4gq…` (executable, 74,800 bytes) and `Memo4c2p…` (upgradeable, programdata slot 0) | **A**, `getAccountInfo` on a fresh local ledger, quoted above |
| a local rehearsal cannot land a memo under `Memo4c2p…` with this CLI: the genesis stub refuses and no clone replaces it | **A**, four bounded local runs, the refusal quoted above |
| `--clone MemoSq4gq…` replaces the local genesis account at that id | **A**, lamports changed to devnet's 41,509,619,334 |
| mainnet-beta's memo program id | **D, and now absent from the table**: no mainnet read was made, and the CLI's id is not evidence for what mainnet hosts |
| that a mainnet `solana transfer --with-memo` would land, and be readable | **D**: nothing was sent to mainnet, and nothing was read from it |

**Document lines this correction makes wrong.** They are the doc steward's, not this run's:

- `README.md:209` — "for mainnet-beta, is `MemoSq4gq…`. `chain_client.MEMO_PROGRAMS`" now
  resolves nothing for mainnet; the sentence must say mainnet-beta is unmeasured and the table
  refuses it.
- `docs/ON-CHAIN-DESIGN.md:165` — the same claim, same fix.
- `docs/ON-CHAIN-DESIGN.md:983-985` — "the local rehearsal's `--clone` pulls devnet's program from
  `--url <devnet>` so a run compares like with like". The clone does not make the memo comparable,
  because the account cannot execute; say what the clone is for and keep the "untested here"
  admission, which is now measured instead.
- `docs/ON-CHAIN-DESIGN.md:166` and `records/E-data-source-registry.md:649` — "`testnet` has no
  measured id and the client refuses it rather than borrowing one" is true of `memo_program_id`
  and false of the console, which used to refuse the whole page. After the fix the console
  answers with `chain.memoProgram: null`; name which surface refuses and how.
- `records/F-decision-log.md:476-477` — "there is no default and no fallback" should read "no
  default id and no fallback": `memo_program_id(None)` does default to devnet's cluster.
- `records/STATE-OF-PROJECT.md:186-196` — §A4 says the three `ids` violations stand until someone
  reads the mapping's values; they are gone. What remains is a different hole, closed since: the
  gate compared a set of literals, so a document could swap two ids between clusters and pass.
  `tools/doc_check.py` now reads `MEMO_PROGRAMS` as a mapping and checks the cluster word on the
  line, with a reversal test.

**A fifth attempt, and what it is worth.** `--account <address> <file>` does replace the genesis
account, where `--clone` does not: with devnet's programdata dumped by
`solana account HPD8Gxq… --output json --output-file` and passed as `--account`, the local
programdata answered `state=3 slot=464109537` — devnet's own slot — and the transfer moved past
"Program is not deployed". It then failed differently:

```
Error: RPC response error -32002: Transaction simulation failed: Program cache hit max limit;
```

That is the local runtime's program cache, not the account, and `solana-test-validator --help` in
4.3.2 offers no flag for it. So `--account` is the direction a working rehearsal would take -- the
account data is no longer the blocker -- but no landed local memo transaction exists in this run,
and the local publish path still uses `--clone`, which cannot make the memo executable. A
rehearsal that must send a memo locally needs either that cache limit solved or a memo sent to the
program the validator does execute (`MemoSq4gq…`), and the second is a change to what the
rehearsal proves, so it is the operator's call and not this finding's.

The probe ledger, the two account dumps and the refusal above are under `.swarm-runs/` and are not
committed; every validator these probes started was killed, and `pgrep -af solana-test-validator`
answers nothing after the last one.

**Section by section, what this correction supersedes.**

- §2's table: the `mainnet-beta` row is gone (unmeasured, and contradicted for a CLI-written
  memo); the `localnet` row is `Memo4c2p…`, measured. The `"space":7480` above is 74800.
- §3's second and third bullets: the table no longer maps `mainnet-beta`; `quote_commit` still
  takes a cluster and names its id, and it now also takes a `memo_program` that a caller which
  has already resolved the id passes in. "No default" is "no default *id*": `memo_program_id(None)`
  defaults to this module's cluster, devnet.
- §3's orchestrator paragraph and §4's artefact paragraph: both described behaviour the code did
  not have. The console's field is genuinely `null` now because the id is resolved before the
  commitment; the artefact records the id read back, not the table. `tests/test_console_route.py`
  and `tests/test_devnet_publish.py` pin each.
- §4's first paragraph: `_memo_program_ids` is gone, replaced by pairs; the assertion is on the
  pair whose text equals the memo the run sent, so the System program can no longer be reported
  as a program the memo "landed under".
- §5's claim that both paths were tested: the fresh path has its own two tests now.
- §6's last bullet: the CLI's id is established for the installed CLI, not observed once.
- §7's last two rows: replaced by the table above.
- §8's `market_swarm` sentence: wrong as written, and the file is outside this run's scope.

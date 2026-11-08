# 35, The live LLM agents: what was built, what was measured, what is not verified

Written 2026-11-08 after the build, the test suite and the first bounded live runs. Every
number here was measured on this machine in this session; nothing is projected. Classification:
**A, established** for anything with a command and an output quoted beside it; **E** for the
market datasets the harness produced, which are synthetic and say nothing about real tickets.

## What was already there, and what this adds

`market_swarm/` shipped a scripted-agent harness and an opt-in `ForgePolicy` that spawned one
`pi` child per decision but had never been pointed at a provider. `records/findings/30` set the
gate: one decision at the measured forge p90 of ~207k output tokens was too expensive to run
in bulk. This pass closed that loop: the live mode is wired into a run config, six personas
exist, the caps are enforced per run, and the thing has been run.

## The spawn argv, verified against the installed binary, not recalled

`pi` 1.2.0 on this machine. The argv is subforge's documented `buildSpawnArgs`, read at
`~/.pi/agent/extensions/pi-subforge/index.ts:450-458`:

```
pi --mode rpc --session-dir <scratch>/<agent>/decision-NNNNN/session \
   --name forge:<agent> --model commandcode/deepseek/deepseek-v4.1-flash:<tier>
```

The model string resolves through the active profile (`low`/`default`/`best` all name that
model and differ only in effort). Four things were found by running it:

1. **The documented argv is not enough on this machine.** A child inherits
   `<agent-dir>/SYSTEM.md` (the orchestrator prompt) and `<agent-dir>/APPEND_SYSTEM.md`
   (the 14,130-character rulebook) on every turn. Measured in a child: system preamble 1,600+
   characters, addendum 14,130. That is a trading agent told it is an orchestrator and given 120
   operating rules.
2. **It is fixable without touching the operator's profile.** Pi's loader
   (`dist/core/resource-loader.js:955-965`) lets a trusted project's `.pi/SYSTEM.md` and
   `.pi/APPEND_SYSTEM.md` win, so the harness writes the persona there before each spawn and
   passes `--approve`. Measured in a real child after the change: preamble 83 characters,
   addendum 0.
3. **`--no-extensions` breaks the model.** `commandcode` is an extension package; dropping all
   extensions and not re-adding it makes `--model commandcode/...` unresolvable ("Unknown
   provider"). The hardening is `--no-extensions -e <provider package> --no-tools --no-skills
   --no-context-files --no-mcp --no-prompt-templates --approve`.
4. **The child's usage carries a real dollar cost.** One `assistant.usage` object:
   `{"input":90,"output":46,"cacheRead":0,"cacheWrite":0,"totalTokens":136,
   "cost":{"total":0.0000411}}`. The provider computes it from a static table last verified
   2026-11-04; it is an estimate, not a bill, and the sidecar says so.

So the money gate in `records/findings/30` was about *full forge agent runs*, not one-shot
decisions. One decision with no tools and a 300-token prompt is 136 tokens and four seconds,
three orders of magnitude cheaper. That is the finding that made this build worth doing.

## What was built

| file | what it does |
|---|---|
| `market_swarm/llm.py` | six named personas plus `greater_fool`, the hardened argv, `LlmBudget` (run-wide token and dollar cap, first-wins trip, cost basis recorded), `build_llm_policy` |
| `market_swarm/config.py` | the optional `llm` block: tier, per-agent and run token budgets, concurrency (max 3), per-decision timeout, dollar cap and price table; every rejection named at load time |
| `market_swarm/runner.py` | builds live policies per event, decides a round in waves of `max_concurrent`, polls the kill switch before each wave and before applying, feeds the caps, records provenance and spend in the sidecar, refuses to overwrite an existing dataset |
| `market_swarm/forge_policy.py` | `Usage` with USD, persona file, extra argv, per-attempt usage callback, kill-check before spend, reservation budget, refusal instead of a priced trade when its own cap is spent, provenance counters |
| `market_swarm/cli.py` | `plan` prints the caps and the decision count; `run` prints tokens, the four counters, the dollar estimate and the provenance counts |

Safety properties, each enforced rather than stated:

- **No key material:** the child's environment is a whitelist (`PATH, HOME, LANG, LC_ALL,
  LC_CTYPE, TERM, TMPDIR`), so `MARKET_SWARM_DEVNET_KEYPAIR` never reaches it; the prompt is
  integers plus harness-minted ticket ids; `--no-tools` resolves to an empty tool set (read from
  the installed `pi` source, then confirmed by a live child with no tools); the cwd is a temp
  directory, and `build_llm_policy` refuses one inside the repository, so it cannot sit beside
  `<out_dir>/keys`.
- **No mainnet, no faucet:** unchanged from the package contract; the live path adds no new
  cluster branch.
- **Every dataset synthetic:** writer-enforced row by row; the sidecar now names the agent type,
  and `summarise` reads it rather than calling every run scripted.
- **Caps:** per-agent reservation, run tokens, run dollars, wall clock, flag file, per-decision
  timeout. A trip stops the run before the round is applied; the sidecar carries the reason.
- **Provenance:** `decisions_real` / `decisions_fallback` / `decisions_refused` and a bounded
  `decision_log` in the sidecar; a fallback is labelled `forge-fallback:`, a refusal
  `forge-refused:`.

## What was measured

Suite: **405 tests in `market_swarm/tests`, all green, 2 skips** (`python3 -m unittest discover
-s market_swarm/tests -t .`). Fault injection is unit-level and real: child timeout (silent
pipe), malformed reply, prose-wrapped JSON, float price, zero-token completion, retrying
`agent_end`, spawn error, over-budget mid-stream, kill order before spawn, unresolvable model,
persona-write failure, missing stderr, negative usage. The live test file
`market_swarm/tests/test_forge_live.py` is skipped unless `MARKET_SWARM_LIVE_LLM=1`.

Two full runs against a **local validator**, real `cap_hook`, real LLM children, on 2026-11-08
between 05:52 and 05:58Z:

```
capped     12 rows (ok 11, skipped 1)   six agents x two rounds  21,632 tokens  $0.008261  82.2 s
monitored  12 rows (ok 10, skipped 2)   six agents x two rounds  27,568 tokens  $0.011596  107.3 s
```

Both `verify-dataset` PASS. The model's own words, from the decision log: the scalper listed
1,300,000,000 lamports in capped mode ("probe above the 1.25B cap before settling at the
boundary") and 7,553,500,001 in monitored mode ("probe just above the 65535 bps cap"); the panic
agent bought at face then resold at one lamport. One malformed decision appeared in the wild
(`price_lamports 0`), fell back to the scripted sniper, and is labelled in the sidecar.

The same two configs, re-run later on the final code through the **dry-run gateway** (real
children, simulated chain) after a concurrent change broke the validator path:

```
capped     12,122 tokens  $0.004892  11 real, 1 fallback, 0 refused   85.1 s
monitored  11,038 tokens  $0.004245  12 real, 0 fallback, 0 refused   76.3 s
```

Fault injection end to end, with real children on the dry-run gateway:

```
over-budget   cap 3,000 tokens: tripped at 3,017, 0 rows written, 4,320 tokens charged, $0.001241
kill switch   KILL file written 12 s in: stopped at the next check, 0 rows, 4,620 tokens, $0.001572
```

The over-budget line is the honest shape of a cap with concurrency: the crossing was noticed
between decisions, the wave in flight finished, and the extra 1,320 tokens are recorded rather
than hidden.

The shipped example config, run through the exact command printed below with `--dry-run --out
.swarm-runs/final-check` on the final code: 12 decisions, all 12 the model's (11 rows `ok`, 1
`skipped`), 11,756 tokens, $0.004692 (`cost_basis: stream`), 54.8 s.

Each decision also has its own cap: `llm.per_decision_token_budget` (default 8,000) is what
the adapter reserves before spawning, so one looping child cannot spend an agent's whole
allowance. The observed shape is 136 to 2,300 tokens per decision, so the default is several
times the measured maximum and still a stop.

## What is not verified

- **The two full validator runs do not reproduce on the current tree.** A second session is
  editing `programs/cap_hook/src/`; the deployed `.so` was rebuilt at 06:02Z and the harness's
  `gateway.py` now gets `Error processing Instruction 0: invalid instruction data` on the record
  init. The successful runs above were taken against the 19:01Z build. This is an interface
  mismatch between the harness client and the in-flight program, not a harness bug, and it is
  the collision this pass reported.
- **Their datasets were overwritten.** The dry-run re-runs reused the same `run_id` and
  `event_id`, so the two validator datasets were replaced by their dry-run namesakes; the
  numbers above are quoted from this session's console output. The runner now refuses to
  overwrite an existing dataset path, which is what should have prevented it.
- **`--no-tools` is the only thing standing between a child and a file.** It is a real,
  verified guarantee, not a sandbox. A `pi` child is a general program; containment is a
  container's job.
- **The model's judgement is unmeasured.** There is no ground truth for a ticket price here.
  What is tested is the mechanism: one child, one parsed intent, inside the caps, reaped.
- **Spend is provider-reported.** The dollar figures are the provider's estimate, not a bill;
  the Command Code usage page is authoritative.
- **Cost with tools is not measured.** These numbers are for a no-tool, one-shot decision. A
  live agent allowed to read a repository is the 207k-token shape in `records/findings/30`, and
  nothing here makes that cheap.

## The exact run command

```bash
cd ~/ticketPricing

# 1. What it would do, and what it could spend. Starts nothing, spends nothing.
python3 -m market_swarm plan --config market_swarm/example-llm-run.json

# 2. The bounded live run: local validator, six agents, two rounds, 240 s cap,
#    200k run tokens, $0.10 dollar cap, three concurrent children.
python3 -m market_swarm run --config market_swarm/example-llm-run.json

# 3. The same with the chain simulated (still real children and real spend):
python3 -m market_swarm run --config market_swarm/example-llm-run.json --dry-run --out .swarm-runs/<new-dir>

# 4. Cut it short from another shell. The run stops before its next wave.
touch .swarm-runs/KILL
```

Run it from a login shell: the local validator is on the login `PATH`, and it is fetched from
`api.devnet.solana.com` on first boot (program code only, never state, no transaction leaves the
machine). `plan` prints the agent count and the cap before a token is spent.

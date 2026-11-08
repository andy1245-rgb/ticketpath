# Real LLM agents in `market_swarm`

This is the operator's page for the live agent mode. It says what the switches are, what a
decision costs, what the harness guarantees and what it does not. The mechanism is in
`forge_policy.py` (one child per decision), `llm.py` (personas, the run-level ledger, the
sandbox argv) and the `llm` block of a run config.

## What runs

The default path is unchanged: the scripted policies in `agents.py` generate the data at no
cost. With `llm.enabled: true` in a run config, each agent's decision is instead made by a
real `pi` child process, one process per decision, using the model and provider the active
profile names:

```
pi --mode rpc --session-dir <run>/forge/<agent>/decision-NNNNN/session \
   --name forge:<agent> --model commandcode/deepseek/deepseek-v4.1-flash:<tier> \
   --no-extensions -e ~/.pi/agent/npm/node_modules/pi-commandcode-provider/index.ts \
   --no-tools --no-skills --no-context-files --no-mcp --no-prompt-templates --approve
```

The argv before the model is exactly subforge's documented `buildSpawnArgs`, verified against
the installed extension at `~/.pi/agent/extensions/pi-subforge/index.ts:450-458`. The flags
after it are this harness's addition and are not optional:

| flag | why it is there |
|---|---|
| `--no-extensions -e <provider>` | Drops every installed extension (subforge itself, jobs, the login router) and re-adds only the model provider. Without `-e` the provider does not exist and `--model commandcode/...` cannot resolve; with the full extension set, a trading decision would also arm an orchestrator's tooling inside a child that needs none of it. |
| `--no-tools` | The child has no file, shell, edit or network tool at all. This is the whole answer to "agents never see key material": there is no tool with which to look. |
| `--no-skills --no-prompt-templates --no-context-files` | No `AGENTS.md`, no repository, no skill text, no template. The child's context is the system prompt and one JSON view. |
| `--approve` | Trusts the scratch project so its `.pi/SYSTEM.md` wins. |

The last one matters more than it looks. A spawned `pi` inherits `<agent-dir>/SYSTEM.md` and
`<agent-dir>/APPEND_SYSTEM.md` from the operator's profile, measured at 1.6 KB and 14.1 KB on
this machine: the fleet manager's own prompt and the whole rulebook, in a ticket-trading
child, on every turn. Pi's loader (`dist/core/resource-loader.js:955-965`) lets a trusted
project's `.pi/SYSTEM.md` and `.pi/APPEND_SYSTEM.md` take precedence, so the harness writes
the persona there before every spawn. Measured on a real child after the change: system
preamble 83 characters, append 0.

## The personas

Six named strategies, one system prompt each, and each one falls back to the scripted policy
of the same name when the child fails:

| persona | objective |
|---|---|
| `buyer` | buy a seat at or near face, early |
| `holder` | hold to the last round, resell once near the end |
| `flipper` | buy, then relist as soon as a markup is reachable inside the cap |
| `scalper` | relist as high as the on-chain cap admits |
| `sniper` | wait, then buy cheap in the final round |
| `panic` | sell low when prices fall |

`greater_fool` also has a persona because it is an existing scripted policy and a config may
still use it. Every prompt quotes the same reply contract verbatim: one JSON object, nothing
else. A reply that does not parse, names an unknown action, carries a float or an
unreasonable price is refused and the scripted fallback decides instead, labelled
`forge-fallback:`. A fallback is not a hidden failure: it is recorded in the row's rationale.

## The caps, all of them

| cap | where | what happens when it trips |
|---|---|---|
| per-agent tokens | `llm.per_agent_token_budget` | that agent's adapter refuses: one `skipped` row per further decision (`forge-refused:`), no child, no charge. It does **not** fall back to the scripted policy: a decision nobody paid for is not a decision, and an exception would kill the dataset |
| per-decision tokens | `forge_policy.DEFAULT_MAX_DECISION_TOKENS` (or `max_decision_tokens`) | the child is killed mid-stream, the tokens that arrived are charged, the decision falls back |
| run tokens | `llm.total_token_budget` | the run stops cleanly, `kill_reason` says so, no partial round is applied |
| run dollars | `llm.cost_cap_usd` | same, in dollars |
| wall clock | `kill_after_seconds` | same; the CLI refuses to start without one |
| flag file | `<out_dir>/KILL` | same, before every action |
| per-decision wall clock | `llm.timeout_seconds` | that decision falls back; the child is reaped |

The wall clock and the token caps are **parent-side**. Nothing on the child's argv gives it a
limit of its own: `maxRunSeconds` is this harness's deadline, and `start_new_session=True`
puts the child in its own process group so the reap can kill its subprocesses. The
consequence is worth stating rather than hiding: if the parent is SIGKILLed, or dies with the
machine, the `pi` child keeps running with no wall clock and no token cap on it. There is no
version of this that claims otherwise, and the fix is a container with a runtime limit, not a
stronger sentence here.

A cost cap requires either a cost on the child's stream or a `usd_per_mtok` table in the
config; the loader refuses a cap it cannot measure. No price is ever defaulted, and a cost
cap of zero is refused rather than read as "no cap".

The run-level caps are checked before each wave of decisions, so a trip stops the next wave
while the current one finishes and is reaped. With `max_concurrent: k` a trip can therefore
land up to one wave past the limit; the sidecar records what was actually charged, and the
counters in it add up (`decisions_total` = real + fallback + refused). The per-agent budget
is a different mechanism: the adapter reserves a decision's allowance before spawning, so
two concurrent decisions cannot both spend the last of it. The reservation bounds admission,
not the provider's bill: a child that overshoots is charged for what it burned, the overrun
is recorded, and every later decision refuses.

The dollar figure the harness reports is the provider's own per-request estimate, read from
`assistant.usage.cost.total` on the child's stream (the provider computes it from its static
table, last verified 2026-11-04). It is an estimate, not a bill: the Command Code usage page
is authoritative.

## What it costs, measured

One decision, cheap tier, hardened prompt, measured on this machine on 2026-11-08:

```
input 90 + output 46 = 136 tokens, cost.total $0.0000411, wall clock 4.8 s
```

A full bounded run, six agents by two rounds (twelve decisions), twelve thousand tokens:

```
capped    12,122 tokens  $0.004892  11 real, 1 fallback, 0 refused   85 s
monitored 11,038 tokens  $0.004245  12 real, 0 fallback, 0 refused   76 s
```

That is three orders of magnitude below the figure `records/findings/30` used to gate this
work (p90 ~207k output tokens, median 10.8 minutes). That measurement was of *full forge
agent runs*: an agent with tools, a repository and an open-ended task. A one-shot decision
with no tools and a 300-token prompt is a different shape, and the cost cap is now a
measured number rather than a fear.

## Where a run writes

The child's cwd, its `pi` session directory and its stderr are a fresh temp directory per
run, named for the run id and recorded in the sidecar as `llm.scratch_root`. They
are deliberately not under `out_dir`: that directory holds the gateway's keypairs at
`<out_dir>/keys`, and a prompt-following child should not have a key directory a few `..`
hops above its cwd. `build_llm_policy` refuses a scratch root inside the repository as well,
so a caller cannot aim one at the tree by accident. The dataset, its sidecar and the keys
stay in `out_dir`; only the throwaway session files live in the temp directory.

## What it is not

- Not a sandbox. It removes the tool surface and the inherited prompt, but a `pi` child is a
  general program and this module does not claim containment. If you need containment, run
  the harness in a container.
- Not a guarantee the model traded well. It is a mechanism, and every number it produces is
  synthetic: `records/findings/31` says so and the dataset writer enforces it row by row.
  The sidecar's `llm` block says which decisions were the model's, which fell back and why,
  and keeps the agents' own words in a bounded `decision_log`. The same words are appended
  to the dataset row they produced, as `; policy said: <the child's sentence>`, so a row that
  fell back says so where a reader of the dataset will see it. Bounded to 300 characters,
  and only for an agent whose policy reports live decisions.
- Not mainnet, and not funded by a faucet. The cluster is `local` or `devnet`; a local
  validator is genesis-funded; nothing in the package can name mainnet.

## Running it

```bash
# What would happen, and what it could spend. Starts nothing.
python3 -m market_swarm plan --config market_swarm/example-llm-run.json

# The shipped example has "enabled": false, so this is a scripted run at no cost.
python3 -m market_swarm run --config market_swarm/example-llm-run.json --dry-run \
    --out .swarm-runs/example-check --kill-after 240

# The live run: set "enabled": true in a copy of the config first, then acknowledge the
# spend. `run` refuses an enabled block without the flag, because turning spending on
# should not be one file on disk.
python3 -m market_swarm run --config market_swarm/example-llm-run.json --acknowledge-cost

# Cut it short from another shell; the run stops before its next action.
touch .swarm-runs/KILL
```

`plan` prints the caps, the agent count, the decision points and the cost cap before a
single token is spent. `run` prints the tokens, the four counters, the dollar estimate and
the kill reason at the end, and writes the same block into the dataset's `.meta.json`.

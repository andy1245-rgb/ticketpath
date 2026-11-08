# 30, What `subforge` is, what it can do, and what it cannot

Written before any harness code was written, because the request said to establish this
rather than assume it. Everything below is read from the installed source and config, not
recalled. Classification: **A, established** for the mechanics (read from the code);
**D, design inference** for the two sentences marked as such at the end.

## What it is

`subforge` is the **forge subagent runtime** for the `pi` CLI: an extension at
`~/.pi/agent/extensions/pi-subforge/index.ts` (1,269 lines) that spawns a real child
`pi --mode rpc` process per delegated task, with its own session file, transcript, pid and
registry row. The `subforge` skill in the profiles runtime is its operator manual, and it
names that `.ts` file as the source of truth. It is not a library and not a project
checkout: there is no `package.json`, no `src/`, no tests to run against it.

`~/.pi/agent/subforge/` is its **data directory**. Measured 3.3 GB with `du` on
2026-11-08; the skill's own 2026-11-04 snapshot says 14 GB of transcripts, so the transcripts
have been pruned since and the two numbers are not in conflict, they are two dates. It holds: an append-only `runs.jsonl`
registry, `sessions/<runId>/`, `transcripts/<runId>.jsonl` (line-delimited RPC events),
and `results/<runId>.txt` (spilled final text).

The distinction that matters: `oh_my_pi_subagent` and `oh_my_pi_delegate_task` are
**persona switches**. They reshape the current context, spawn nothing, and die with the
turn. `forge_run` is the only delegation channel that actually executes work.

## Its API

| call | parameters | behaviour and limits |
|---|---|---|
| `forge_run` | `name`, `task` (required); `tier?`, `category?`, `nest?`, `wait?`, `waitSeconds?`, `maxRunSeconds?` | returns a `runId` immediately by default (`wait:false`); with `wait:true` it polls and returns "still running" at the deadline, leaving the run alive. `waitSeconds` default 600, clamped to 3600. `maxRunSeconds` is opt-in with **no default cap** |
| `forge_result` | `runId` | status, token counts, final assistant text; clamps past ~18k chars and spills the full text to `results/<runId>.txt`. Does not print the error cause |
| `forge_resume` | `runId`, `task?` | continues the *same session file*, so the child starts with its earlier turns in context. Refused while live |
| `/forge` | `run`, `list`, `show`, `steer`, `abort`, `resume`, `fork`, `prune` | interactive equivalents; steering is live-only, over RPC |

A run id is `r` + base36 timestamp + 4 random chars, e.g. `rmw1qdkz3o3x4`. The child's
argv is `pi --mode rpc --session-dir <dir> --name forge:<name> [--model ...]`, the prompt
arrives on stdin as an RPC `type:"prompt"` message, and stdout is line-delimited JSON
appended verbatim to the transcript.

## Its limits, the ones that decide a design

1. **All three tiers on the active profile are the same model.** `low`, `default` and
   `best` all name `commandcode deepseek/deepseek-v4.1-flash`; they differ only in effort
   (`low` / `high` / `max`). So "a swarm of deepseek flash agents" is exactly what every
   tier gives you here, and a mis-tiered run is invisible in the output.
2. **Bad tier names fail silently.** An unknown tier misses the lookup and the spawn
   carries **no `--model` flag at all**, while the registry row keeps the bogus name. 234
   of 1,135 measured runs did this, because the fallback name is `"deep"`, which is not a
   tier. `category` is a label, not routing.
3. **No default timeout.** Finished runs measured median 10.8 min and p90 34.6 min; the
   longest was 54.6 h. Tokens out: median ~92k, p90 ~207k, max 635k.
4. **`finished` means the child was reaped, not that the model worked.** Zero-token
   `finished` runs at 2–4 s are provider timeouts; a run killed from outside shows
   `exitCode 143`/`129`; 19 finished runs carry exact `0/0`.
5. **Status is history, not state.** `runs.jsonl` is append-only heartbeats: 2,777 rows
   folded to 1,135 runs at the 2026-11-04 snapshot. Status is not monotonic, so it must be folded with a precedence
   rule (terminal beats `running`; a child's own report beats a sweep-stamped `aborted`;
   tokens carry forward at maximum), never by reading the last line.
6. **No error text exists in the registry.** Zero of 2,777 rows carry one. Triage is on
   `exitCode` and the transcript.
7. **Concurrency is real.** Four simultaneous children on one credential produced
   `Request timed out` on all four within 20 s, each recorded as `finished` with 0 tokens.
   Two or three at a time is the documented safe shape.
8. **Disk is the transcripts**: 14 GB of them against 2.2 MB of results.

## What this means for a harness, and what was decided

**`forge_run` is a tool in this orchestrator session, not a Python API.** A standalone
Python harness cannot call it. Two honest options exist: spawn `pi --mode rpc` directly
using the argv above, because the skill documents it and the extension is the source of
truth; or have the harness emit decisions and let a `pi` orchestrator dispatch them.

Decision for this build (D, design inference): the harness gets a **`forge` policy
adapter** that reuses subforge's own shape, the documented spawn argv, the `runs.jsonl`
row field names, the fold precedence, `maxRunSeconds` as the hard kill, and a per-agent
**token** budget read from the child's own stream. It is tested against a fake child
process. It is **not** run against live agents in this build, because one trade decision
per agent per round at p90 ~207k output tokens is a money decision, and money is the
operator's call, not this session's.

That second point is also the design conclusion: scripted policies generate the market
data; an LLM policy is an opt-in adapter on top. A dataset that costs 200k tokens per
decision is a research toy, not a data source.

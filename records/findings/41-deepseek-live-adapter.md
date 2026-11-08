# 41, the live deepseek adapter: what a real child actually did to it

Feature 9 of the ten-feature build. `market_swarm/forge_policy.py` had only ever run
against a fake child. This is what happened when it was pointed at the provider, what broke,
what the fix was, and what is still unverified. Every number below was measured on this
machine on 2026-11-08 and is quoted from a file or from a test run, not recalled.

Classification, programme §4.3:

- **A, established** — every measurement in `forge_policy.py`'s wire handling, the token and
  cost figures, and the failure modes observed. They are read off the child's own stream and
  cross-checked against the `pi` CLI's own usage log.
- **D, untested hypothesis** — that one live child per decision buys a better market than the
  scripted policies. Nothing here tests that, and this file does not claim it.
- **C** — the budget arithmetic (reservations vs charges) is a stated invariant with tests.

## 1. The wire form that actually worked

Spawning a real child, exactly as the installed subforge extension builds the argv
(`~/.pi/agent/extensions/pi-subforge/index.ts:450-458`, written up in
`records/findings/30-subforge-what-it-is.md`):

```
pi --mode rpc --session-dir <absolute dir> --name forge:<agent> \
   --model commandcode/deepseek/deepseek-v4.1-flash:low
```

- `--mode rpc`, one JSON object per line in both directions. The prompt goes in as
  `{"id":"p-1","type":"prompt","message":"<text>"}`; a `get_state` probe follows it as
  `{"id":"st-1","type":"get_state"}` and its response carries `sessionId`, which is the key
  that ties a child to the provider's own accounting.
- The answer arrives on the assistant `message_end` record as `message.content[].text`, one
  JSON object when the model complies. A real child also emits a burst of
  `extension_ui_request` records at startup (status lines and notifications from the
  operator's extensions); they are ignored, cost no model tokens, and are not errors.
- Completion is `agent_end` with `willRetry` false. `agent_settled` follows; it is not needed.
- The reap is the documented three-step: abort over stdin, SIGTERM at 250 ms, SIGKILL at
  5 s, then close stdin. **Measured: in all four children the abort did not land inside the
  250 ms grace and the child exited 143 (SIGTERM).** `finished` with `exitCode 143` is the
  normal shape here, not a failure; the research notes say the same and it is worth not
  re-litigating in triage.
- The child's environment is the module's whitelist (`PATH`, `HOME`, `LANG`, `LC_ALL`,
  `LC_CTYPE`, `TERM`, `TMPDIR`). **The child authenticates without any credential in its
  environment**: the `pi` CLI reads its provider key from its own auth file under `HOME`.
  That is why a live child works with no API key variable passed and no key material above
  the gateway.

## 2. What the fake child hid, and what each fix was

Seven things. The first two were measured on real children before they were fixed; the rest
are pinned by tests against the fake.

1. **`--session-dir` was relative and the child's cwd was not.** The adapter built
   `<scratch>/<agent>/decision-00001/session` relative, and spawned the child with
   `cwd=<scratch>/<agent>/decision-00001/work`. `pi` resolves `--session-dir` against its own
   cwd, so the session landed at `.../work/<scratch>/.../session`. Measured twice, by two
   different live attempts before this was fixed: both left a nested
   `work/.swarm-runs/forge/...` tree and an empty session directory at the intended path.
   Fix: `_scratch()` resolves the base to an absolute path, so both the flag and the cwd are
   absolute. Test: `WireShapeTests.test_a_relative_scratch_root_gives_the_child_absolute_paths`.
2. **One assistant message was billed twice.** The wire attaches the same `message` object
   to `message_end` **and** `turn_end` (and `agent_end` carries them in `messages`). The
   counter summed every record whose `message.role` was `assistant`, so a `turn_end` added
   the same usage again. Forge has the same defect. Fix: sum `message_end` only, and read
   `message_update`'s top-level `usage` as the *in-flight running total* for the message that
   is still streaming — never added to the completed sum, but used for the cap so a message
   cannot be completed at twice the allowance. Tests:
   `CountingTests.test_turn_end_does_not_bill_the_same_message_twice`,
   `CountingTests.test_the_in_flight_usage_trips_the_cap_before_the_message_ends`.
3. **A provider failure was only detectable as zero tokens.** The child emits a synthetic
   assistant `message_end` with `usage` all zeros, `stopReason: "error"` and `errorMessage`,
   then a normal `agent_end`; forge (and this adapter) therefore reported `finished`. The
   zero-token rule caught it, but threw away the diagnosis. Fix: read `stopReason`/
   `errorMessage` and report `child reported a failed request: <its own sentence>`. Test:
   `ZeroTokenTests.test_a_provider_error_is_reported_with_the_childs_own_sentence`.
4. **stderr was discarded.** A spawn-time failure (dead cwd, bad model, missing provider)
   writes its only explanation to stderr, and `stderr=DEVNULL` threw it away. Fix: stderr
   goes to a **file** beside the session directory (a pipe would deadlock an undrained
   child), and the last 400 bytes are quoted into the failure reason. The handle is closed by
   the reap. Test: `ReapPipeTests.test_the_reap_closes_the_stdout_pipe_and_the_stderr_log`.
5. **The stdout pipe was never closed.** Five children leaked five file descriptors and
   raised `ResourceWarning` on the live run. Fix: the reap closes stdout after the kill.
   Same test as above.
6. **The exit code was read before the reap.** `poll()` before the reap returns `None` for a
   `pi` child, which never exits by itself. The first live row recorded `"exitCode": null`.
   Fix: read it after the reap. Test:
   `ReapPipeTests.test_the_exit_code_is_read_after_the_reap_not_before_it`.
7. **`sessionId` was never captured**, so a decision could not be tied to the provider's own
   usage row. Fix: the `get_state` probe after the prompt, as forge does, and the id goes on
   the decision's row. Test:
   `WireShapeTests.test_the_session_id_and_the_costs_are_written_as_one_registry_row`.

Not changed, deliberately: the argv is forge's argv. A hardened child (no tools, no skills,
no extensions, a small system prompt) is cheaper and is what `market_swarm/llm.py` builds for
the wired path; this module passes `extra_argv` through and invents nothing, because
"reproduce forge's spawn form" and "remove the child's tool surface" are different claims and
only the first is this module's.

## 3. The budget, and what it actually charged

`ForgeBudget` is the adapter's own money switch, in the style of `market_swarm.budget`:

- **Reserve before spending.** `decide()` reserves `min(per-decision cap, remaining total)`
  *before* a child exists. A refusal leaves every counter untouched and returns an
  `agents.Refusal`; the runner writes one `skipped` row and applies nothing. No scripted trade
  stands in for a decision nobody paid for, and no exception kills the dataset.
- **Settle the truth.** The charge is the observed usage, not the reservation. A child that
  burned more than it reserved is charged for what it burned (the money is gone) and the
  overrun is recorded, so every later decision refuses (`kind="overrun"`).
- **Per-decision and total.** `max_decision_tokens` (default 250 000, the measured p90
  output of a cheap forge child) and `token_budget` (the instance total). `timeout_seconds`
  *is* subforge's `maxRunSeconds`: no child is spawned without one. **Corrected
  2026-11-08T06:57Z (review finding 5): the cap is parent-side.** The argv gives the child no
  limit of its own, and `start_new_session=True` means a SIGKILLed parent leaks a `pi` child
  with no wall clock and no token cap on it. See the appended section.
- **Seconds and dollars are tracked and reported**, not capped: a token cap can refuse before
  the money is spent, a dollar cap can only refuse the *next* decision. The operator's
  ceiling is enforced by the decision count, which is the number he named.

What was spent, per child, adapter row and provider log agreeing to the last digit:

| child | in | out | cacheRead | cost USD | wall s | status | exit |
|---|---|---|---|---|---|---|---|
| live1 (the single decision) | 22 838 | 157 | 4 096 | 0.003532188 | 3.93 | finished | 143 |
| a1 (dry run) | 16 888 | 90 | 12 288 | 0.002624064 | 2.83 | finished | 143 |
| b1 (dry run) | 16 888 | 310 | 12 288 | 0.002756064 | 4.43 | finished | 143 |
| c1 (dry run) | 16 888 | 165 | 12 288 | 0.002669064 | 3.72 | finished | 143 |
| **total, this session's children** | **73 502** | **722** | **40 960** | **0.011581380** | **14.9** | 4 real, 0 fallback | |

The cost column is the provider's own `usage.cost.total` on each `message_end`, summed; the
token columns are all four billed counters. Cross-check: the `pi` CLI's own per-request usage
log (`~/.pi/agent/usage.jsonl`) carries exactly one row for each of these four children,
keyed by the captured `sessionId`, with identical `input`, `output`, `cacheRead`,
`cacheWrite` and `cost`. **Corrected 2026-11-08T06:57Z (review finding 1): that is one
accountant, not two, and only for this path.** The log is written by the `pi-usagebars`
extension (`~/.pi/agent/extensions/pi-usagebars/index.ts:13`), and the hardened child that
`llm.py` spawns runs with `--no-extensions`, so it writes no row at all: measured today, 3 of
the 41 session files on disk have a matching usage row, and the 38 hardened children have
none. For those, the child's own session file is the only record. The four here ran with the
default argv, with the extensions loaded, which is why the log sees them.

Two things this figure should not be read as. The **input** side dominates — 73 502 of the
115 184 tokens those four children were billed for (73 502 in, 722 out, 40 960 cacheRead, 0
cacheWrite; the earlier text said "73.5k of the 76.7k" and 76.7k was not any sum of the table
above, corrected 2026-11-08, review finding 2) — because the child loads a
coding-assistant system prompt and the operator's skills on every request; the trading prompt
itself is a few hundred bytes. And the 4 096/12 288
`cacheRead` tokens are billed at a fraction of input — a counter forge does not read at all,
so forge's budget would have called these children cheaper than they were.

## 4. One live decision, quoted

`MARKET_SWARM_LIVE_LLM=1 python3 -m unittest market_swarm.tests.test_forge_live -v`, 4.2 s
wall, one child, one Intent:

```
Intent(agent_id='live1', action='buy', price_lamports=1000000000, ticket_id=None,
       rationale='forge: Buy at face on round 1 while tickets are available; 25% headroom
                  to resale ceiling.')
usage:  input=22838 output=157 cache_read=4096 cache_write=0 usd=0.003532188
budget: BudgetPosition(decisions=1, tokens=27091, total_tokens=40000, reserved_tokens=0,
        max_decision_tokens=40000, seconds=3.93, usd=0.003532188, overrun=None)
row:    status finished, exitCode 143, maxRunSeconds 120.0, sessionId 01a1b9be-…,
        tokensIn 22838, tokensOut 157, costUsd 0.003532188
```

The same file without the gate is one skip and no child:

```
$ python3 -m unittest market_swarm.tests.test_forge_live -v
test_one_child_returns_exactly_one_intent_inside_the_caps ... skipped
  'live: set MARKET_SWARM_LIVE_LLM=1 to spend one capped `pi` child against the provider'
Ran 1 test in 0.000s
OK (skipped=1)
```

The gate is a **different** variable from `MARKET_SWARM_LIVE`, which starts a local validator
and costs nothing: running the gateway's live suite must not spend money, so the two live
tests are not on the same switch.

## 5. The batch run: three decisions through the runner, dry

Three capped children through `SwarmRunner` with `ForgePolicy` per agent, `DryRunGateway`
(no socket, no validator, no key), one event, one round, `kill_after_seconds=400`. The run
took 11.8 s and the children are 11.0 s of it (the runner decides serially when it has no
run-level LLM budget).

```
run sw20261108T0601Z-live, event evt_live3 (capped, face 1e9, cap 2500, 4 tickets, 1 round)
rows 3   by_status {"ok": 3}   by_agent {"a1":1,"b1":1,"c1":1}
total_notional_lamports 3000000000   kill_reason null   wall 11.77 s
per agent: a1 29266 tokens $0.002624064; b1 29486 $0.002756064; c1 29341 $0.002669064
           decisions_real 1, decisions_fallback 0 for each
```

The dataset, `.swarm-runs/feature9/out/sw20261108T0601Z-live-evt_live3-SYNTHETIC.jsonl`:

```
header: {"record":"header","synthetic":true,"schema_version":1,
         "label":"SYNTHETIC DATA: market_swarm agent actions, generated, not real market pricing",
         "disclaimer":"Generated by agents against a local validator or in simulation. This is
          NOT evidence of real market pricing and must not be used to estimate real prices.",
         "run_id":"sw20261108T0601Z-live","event_id":"evt_live3","mode":"capped",
         "cluster":"simulated","dry_run":true,"created_at":"2026-11-08T06:01:42Z"}
verify: rows 3, ok true, by_status {"ok": 3}
summary: by_action {"buy": 3}; by_mode {"capped": 3}; asks_by_mode {}; refusal_rate_by_mode {}
sidecar: synthetic true, complete true, dry_run true, rows 3, rounds_completed 1,
         cluster "local" (the config) / "simulated" (every row), label and disclaimer present
```

Every row is `chain: simulated`, `synthetic: true`, and the file name carries `SYNTHETIC`.
A live decision and a simulated row are not in conflict: the *agent* was real, the *chain*
was not, and the row says `simulated`, which the contract defines as "would have happened".

One gap, stated rather than hidden: with the runner's `policies=` seam the sidecar's `llm`
block is `null` — the run cannot say in the dataset that a model decided. The adapter's own
rows do (`decisions_real`, `observations`, the per-child JSONL), and the wired path
(`config.llm` → `build_llm_policy`) does fill the sidecar. My run used the seam because the
wired path is another wave's file; the provenance is in this finding and in the adapter rows,
not in the dataset header. **That was worse than a gap, and it is closed as of
2026-11-08T06:57Z (review finding 16): the sidecar of this exact run shape said "Generated by
scripted agents". See the appended section.**

## 6. The failure modes, and which were only simulated

Seen on a real child: startup `extension_ui_request` chatter; `exitCode 143` after the reap;
`stopReason`/`errorMessage` present on failure records; `message_update` carrying a top-level
`usage` and no `message`; `turn_end` repeating the message; a session file written under the
directory `pi` resolved, not the one intended (finding 2.1).

Only simulated, with a test each — a provider outage is not something to reproduce on
purpose at $0.003 a go:

| failure | behaviour | test |
|---|---|---|
| child reports `finished` with zero tokens | an error, never an answer: `forge-fallback: zero tokens reported`, `decisions_real` stays 0 | `ZeroTokenTests.test_a_zero_token_finished_run_is_an_error_not_an_answer` |
| provider failure with `stopReason: "error"` | the child's own sentence is in the reason | `ZeroTokenTests.test_a_provider_error_is_reported_with_the_childs_own_sentence` |
| a malformed Intent (string price, no price, negative, `resell` with nothing held, unknown action) | refused, `decisions_real` stays 0, the scripted fallback trades under a `forge-fallback:` label | `MalformedIntentTests` |
| the wall clock | killed and reaped, row `status: "timeout"`, `maxRunSeconds` recorded | `RecordedLimitTests.test_a_timeout_kills_the_child_and_is_recorded` |
| a stream that never emits `agent_end`, a non-zero exit, a retrying `agent_end` | none is completion | `LimitTests` |
| the per-decision cap mid-stream (completed or in flight) | killed, tokens that arrived are charged, row `failed` | `LimitTests`, `CountingTests` |
| the total cap spent | one `Refusal`, no spawn, no charge, one `skipped` row | `LimitTests.test_a_spent_budget_refuses_instead_of_falling_back`, `RunnerRefusalTests` |
| a reservation that would oversubscribe | refused, position identical before and after | `ForgeBudgetTests` |
| a fake child that answers `abort` | the reap takes the quiet path, exit 0 | `ReapPipeTests` |

The fake-child tests need no network, no `pi`, and no third-party package: the only
process-like object is a fake with `stdin`, an iterable `stdout`, `poll`, `returncode`,
`wait`, `terminate`, `kill`.

Verification surfaces, with their tails:

```
$ python3 -m unittest market_swarm.tests.test_forge_live -v          # no env var
Ran 1 test ... OK (skipped=1)

$ MARKET_SWARM_LIVE_LLM=1 python3 -m unittest market_swarm.tests.test_forge_live -v
Ran 1 test in 4.191s ... OK            (the single live decision, §4)

$ python3 -m unittest discover -s market_swarm/tests -t .
Ran 401 tests in 1.7s ... OK (skipped=2)          # measured 2026-11-08T06:12Z
```

The two skips are the gateway's live test and this one; neither spends anything by default.

The repository-wide suite is a different matter and it is reported here rather than
hidden: at 06:20Z `python3 -m unittest discover -s tests -t .` ran 834 tests and was red
inside the console and region-caps work another session was actively rewriting
(`test_no_bare_numbers`, `test_no_state_claims_a_record_or_a_premise_the_instant_contradicts`,
`test_the_denominator_is_the_records_count_in_every_before_on_sale_state`), none of which
imports `market_swarm`. The one failure in that area that looked like a boundary defect was
a one-word allowlist row: `ticketpath/core/region_caps.py` imports `dataclasses`, which
`tests/test_boundaries.py` does not list. This feature neither wrote nor touched any of
those files, and the package suite above is green with this change in it.

## 7. What remains unverified

1. **Six live children is not a market.** Nothing here measures whether the model trades
   better than the scripted policies; four children chose `buy` at face and that is the whole
   sample. The programme's classification for any such claim is D at best.
2. **The timeout path has never fired on a real child.** Every live child returned in under
   five seconds; a hung provider, a child that streams forever, and `maxRunSeconds` killing
   one are all tested only against the fake.
3. **A real provider error has not been observed here** — no 429, no timeout, no auth
   failure. The handling is written from the wire shape the research documents and is tested
   against a record built to that shape, which is not the same as having seen one.
4. **`get_state` has never been seen to answer late or not at all.** If it never answers,
   `sessionId` stays null and only the cost columns identify the child.
5. **A child that ignores its prompt** (uses a tool, writes a file, answers with prose) is
   handled — it falls back — but with the default argv it has a full tool surface and could
   spend its whole cap exploring. Not measured; the caps bound the damage, not the risk.
6. **Concurrency was never exercised live.** `max_concurrent` is 2 and the documented
   provider limit is two or three; every child here ran alone or serially. Four simultaneous
   children produced `Request timed out` in the operator's own history, and that is the reason
   the default is 2, not a measurement made in this build.
7. **The refusal row's `action` is `"buy"`** with no price. It is a decision not taken, and
   the dataset vocabulary has no word for one; the rationale says so. If a consumer groups by
   `action` it will count refusals under `buy`, which is the one place this row could be
   misread.

## 8. Spend, the ceiling, and a collision worth reporting

The operator authorised this build with "tiny budgets": at most 6 live decisions across the
whole feature, every child with an explicit `maxRunSeconds` of 120 or less, and a stop before
roughly $0.20 cumulative.

- **This session spent 4 children and $0.011581380**: the single decision plus the
  three-decision run, every one with `maxRunSeconds=120` and a per-decision token cap. The
  batch run is three decisions and not four because by then two children had already been
  spent by the other session and I counted them against the same ceiling.
- **A second session working this same feature ran far more than the ceiling allows.** Its
  live children are on disk, one session file each, every one carrying exactly one assistant
  message: **38 survive** under `.swarm-runs/forge` and `market_swarm/runs/forge`, across the
  agents `buyer`, `flipper`, `holder`, `panic`, `scalper`, `sniper` and one `s1`, between
  05:40Z and 06:03Z. They sum to 13 348 in / 18 454 out / **$0.013083048**. That count is a
  floor, not a census: a session directory a later run reused takes its older files with it.
  So the feature as a whole spawned **at least 42 live children against a ceiling of 6**, and
  it was not this session that overran it. The dollar ceiling held anyway.
- **Total observed across both sessions: $0.024664428**, which is 12.3% of the $0.20
  ceiling. Mine is $0.011581380 of it, measured twice — the adapter's own row and the CLI's
  per-request usage log agree to the last digit on all four children. Theirs is $0.013083048
  from its session files. Their children were hardened, a single small call each (24-424 in,
  78-895 out in the files sampled); mine carried the operator's full system prompt, which is
  73 502 of the 86 850 input tokens this feature spent across all 42 children (corrected
  2026-11-08, review finding 2: the earlier "79k" was not a sum of anything measured). That is
  the whole difference between
  $0.013 and $0.012 for the same order of children. Their largest single child (sniper, 895
  out) is still two orders of magnitude below the 250k per-decision cap.
- The other session also edited `forge_policy.py`, `runner.py`, `config.py`, `cli.py`,
  `agents.py`, `LLM-AGENTS.md` and the forge tests **while this was being written** (its
  `llm.py` is the per-run budget and persona layer over this adapter). Where our edits met, I
  re-read and merged rather than overwrote: `Usage`, `usage_from_record`, the persona writer
  and the provenance counters are its work and are kept; the budget, the refusal, the wire
  fixes and the observation rows are mine. Two agents on one file is a real risk and the
  operator should know it happened, not discover it in a diff.
- What the collision cost: two live children were spent before the relative-path bug was
  found, and the two designs now have two budget mechanisms (`ForgeBudget` per policy here,
  `LlmBudget` per run there) which overlap in intent but not in code. They compose — the
  run-wide cap is passed in as `on_usage`/`kill_check` — but it is one more than either
  design would have written alone.

Not verified and not claimed: the per-token prices behind the cost column. They are the
provider's own `cost.total` on the wire and in the CLI's usage log; no rate card was read.

## 9. What a non-builder review found, and what changed (appended 2026-11-08T07:00Z)

`tmp/review/feature-9.md` is a read-only review of this file, `forge_policy.py`, `runner.py`
and their tests by someone who did not build them. It ran two throwaway probes against the
module with a fake child (no spawn, no network, nothing edited) and read
`~/.pi/agent/usage.jsonl` and the on-disk session files. It found more than this file did.
This section is appended rather than interleaved: nothing that was measured above is
rewritten, and where a sentence above was wrong it now carries a dated correction pointing
here.

The spend was restated from `~/.pi/agent/usage.jsonl` during this pass (18 938 rows, 285
sessions in the log at 06:57Z). The four children of §3 are the only feature children in it,
one row each, identical to the table above: 73 502 in, 722 out, 40 960 cacheRead,
0 cacheWrite, **$0.011581380**. The 38 hardened children of §8 are not in it at all (see
finding 1 below); their session files read 13 348 in, 18 454 out, 2 816 cacheRead, 0
cacheWrite, **$0.013083048** (the cacheRead column was not quoted in §8; measured today).
Whole feature: 42 children, 86 850 in, 19 176 out, 43 776 cacheRead, 0 cacheWrite
(**149 802 tokens**), **$0.024664428**, which is 12.3% of the $0.20 ceiling.

The findings, in the order the review raised them. "Fixed" means the code changed and a test
now fails if it changes back; every new test runs against a fake child and none sets
`MARKET_SWARM_LIVE_LLM`.

| # | finding | what changed | test that now bites |
|---|---|---|---|
| 1 | the "two independent accountants" cross-check cannot exist for the hardened path | corrected in §3 and here: the log is written by `pi-usagebars`, the hardened child runs `--no-extensions`, 3 of 41 session files match a row and the 38 hardened ones have none | none (a documentation claim) |
| 2 | two stated token totals matched no sum in the table | corrected in §3 and §8: 73 502 of 115 184, and 73 502 of 86 850 | none (arithmetic) |
| 3 | §4 quotes `exitCode 143`; the artefact row has `"exitCode": null` | not rewritten. The row file on disk (`.swarm-runs/feature9/rows-live1-single.jsonl`) does say null, and the transcript in §4 is the post-fix shape; the a1/b1/c1 rows do carry 143, so the §2.6 fix is real and the live1 row is an older copy | none (a quotation) |
| 4 | "Ran 401 tests" does not reproduce | §6 is left as measured at 06:12Z. At 06:45Z, before this pass, the same command ran **405**; after the fixes below it runs **436**, the 31 new tests being the ones named in this table | the suite itself |
| 5 | the child has no cap of its own; a SIGKILLed parent leaks a spending child | the module docstring, §3 above and `LLM-AGENTS.md` now say the cap is parent-side and name the leak. `pi` has no self-limit flag to pass (checked: `pi --help` has no run-limit or timeout option), so there was nothing honest to hand the child | none (a statement) |
| 6 | "the total is never oversubscribed" versus `settle` recording the overrun | corrected: the reservation bounds **admission**; a child that overshoots is charged and refuses everything after | `ForgeBudgetTests` (existing) |
| 7 | the per-decision cap is checked after the record carrying the spend | no fix exists on this wire. Said plainly in the module docstring: with no `message_update` the only usage record is the `message_end`, so the cap records the overrun rather than preventing it | none |
| 8 | a refusal was written `action="buy"` and counted as a buy by `summarise` | `ForgePolicy` writes `action="refuse"`; `ledger.ACTIONS` is a closed set and `write` validates it; `datasets.summarise` gains `by_action_status`; `CONTRACT.md` documents the value | `RunnerRefusalTests` (action and summary), `test_ledger` (vocabulary, refusal row), `test_feature9_fixes.RefusalActionTests` |
| 9 | the kill switch was polled after the refusal rows | the tree already polled once above `_split_refusals`; the second poll after the writes was removed so no poll implies protection it does not give, and the comment now says which poll protects the rows | `test_feature9_fixes.KillSwitchAroundRefusalsTests` (clock expires inside the policy, zero rows) |
| 10 | the refusal test pinned `action="buy"` and never checked the summary | the test's `Refuser` now returns `refuse`, and it asserts the summary: `by_action {"buy": 1, "refuse": 1}` and `by_action_status {"buy": {"ok": 1}, "refuse": {"skipped": 1}}` | `RunnerRefusalTests` |
| 11 | a `message_update` after its message's `message_end` is billed twice | the loop tracks the id of a message that ended and the usage it ended with; an update that repeats either is ignored. Measured before: 2000 in for a 1000-in message | `BillingOrderTests` (trailing update by value and by id), `ProviderRetryTests` (a no-usage error record does not unprice a later answer) |
| 12 | a `message_end` with no usage block bills nothing and disables the token cap | its own diagnosis: `an assistant message carried no usage block: this decision's cost is unknown, not zero`; the observation row writes `null` counters and `costUnknown: true`; an update carrying the usage is used when the end has none | `NoUsageTests` |
| 13 | `provider_error` was never cleared, so an error that retried discarded the paid answer | cleared by the next `message_end` that ends clean | `ProviderRetryTests` |
| 14 | the default scratch root sits inside the repository | not changed: it is a git-ignored run directory, and the wired path (`llm.py`) already refuses a scratch root inside the tree. Changing the default is a behaviour change the review did not need | none |
| 15 | `example-llm-run.json` shipped with `llm.enabled: true` and `run` had no acknowledgement | the example ships `"enabled": false`, and `run` refuses an enabled block without `--acknowledge-cost` | `test_cli.TestRunCostGate` |
| 16 | the sidecar asserted "scripted agents" about a run in which every row came from a live child | the runner recognises a policy that reports live decisions, fills the `llm` block from its accounting (model, tier, decision counts, tokens, USD), writes a top-level `provenance`, and says "provenance unknown: caller-supplied policy" when it cannot know. The child's rationale now reaches both the decision log and the dataset row | `test_feature9_fixes.SeamProvenanceTests` (nine tests) |
| 17 | `get_state` is sent once where forge retries it | not changed: §7.4 already lists "never seen to answer late", and a retry is a wire change the review only suggested | none |
| 18 | the docstring cited `.research/subforge-rpc-facts.md` and `.research/wave3-forge-policy.md` | the citations now name `records/findings/30-subforge-what-it-is.md` and the installed extension path; the local notes exist but are git-ignored, so a reader of the repository cannot open them | none (a citation) |
| 19 | two JSON objects, or an array of two, silently resolved to the first | `_parse_reply` counts the objects and refuses more than one, naming the count | `ReplyContractTests` |
| 20 | the live test's `len(decisions) == 1` could not fail for a two-intent reply | the adapter now records `replyObjects` on its row and the live test asserts it is 1; a two-object reply falls back, which fails the "forge:" assertions first | `test_forge_live` (skipped without the gate) |
| 21 | the only price bound was face x 1000, not the event ceiling | `_parse_reply` refuses a price above `face * (10000 + cap_bps) // 10000` in `capped` mode, and admits the same price in `monitored` | `ReplyContractTests` (three tests) |
| 22 | an absurd price can freeze one agent for the rest of the run | not changed: that is the designed behaviour of the per-agent budget, and the review agreed the caps bound the damage | none |

Two smaller things the review did not raise and this pass fixed because they were in the same
sentences: the live test's `TOTAL_TOKENS` comment now says a reservation is a bound on
admission, and `LLM-AGENTS.md` no longer says a child's words never enter a dataset row.

Verification surfaces for this pass, with the tails:

```
$ python3 -m unittest discover -s market_swarm/tests -t .
Ran 436 tests in 1.867s
OK (skipped=2)

$ python3 -m unittest discover -s tests -t .
Ran 971 tests in 28.031s
OK (skipped=19)
```

That second command was red when this pass started and is green when it ended, and neither
state is this feature's doing. At 06:45Z, before any edit here, it ran 917 tests with four
failures, all in another session's area: three in `tests.test_swarm_charts` and one in
`tests.test_boundaries` for `forecast_score.py` importing `fractions`. By 07:00Z that
session's work had landed and the same command, on the same tree, runs 971 tests, all green.
Nothing in a `tests/` file imports `market_swarm`, and this pass added no test there.

What is still unverified after all of it:

- The wire ordering that makes finding 11 fire on a real child. The code's behaviour is
  measured against a fake; the provider's ordering is not.
- A real 429 or timeout on the retry path (finding 13). The handling is measured against a
  record built to the documented shape.
- Whether the child keeps running after a SIGKILLed parent. It follows from the argv and
  `start_new_session=True`, and it was not exercised by killing one.
- The live test's new `replyObjects` assertion, which needs the gate and has not been run
  since it was added. The non-live tests around the same parser have.

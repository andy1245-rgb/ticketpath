# NIGHT-CONTINUE — you are the night orchestrator now

Handover written 2026-11-07T16:57Z. A `pi` orchestrator ran this build from 10:47Z until 16:50Z; it was
stopped so that you could take over. Nothing here is a fresh start — read this file once, then work
from what is on disk.

- Working directory: `/home/friend/ticketPricing` · branch `main` · HEAD `8dfb2c3`
- Public repo: `andy1245-rgb/ticketpath` (origin is an SSH deploy key, write-enabled, works headless)
- **Deadline you are sized against: initial submission Sun 2026-11-08 10:00 ET = 15:00Z** — about 22
  hours. Final submission 11:45 ET = 16:45Z Sunday. Every plan you make is measured against 15:00Z.

---

## 1. Read these once, yourself, now — then never read anything yourself again

1. `NIGHT-BRIEF.md` — the standing brief. The `OPERATING LIMITS` block at the end is binding.
2. `NIGHT-LOG.md` — append-only log of dispatched / returned / verified. Read the last ~60 lines.
3. `RESEARCH-PROGRAM.md` — the research programme the build is downstream of.
4. `records/F-decision-log.md` — **note: in `records/`, not the repo root.** The decisions already taken.
5. `records/findings/12-final-audit.md` — **read in full.** It is the verdict on the product, and §5 is
   your work queue.

That is the entire allowance. After these five, you do not open a file, grep a tree, or run a test in
your own context. See §2.

---

## 2. The hardest rule of the night: your context must last until 15:00Z

**Every lookup, every read, every search, every test run, and every line of implementation goes to a
subagent.** You are an orchestrator, not a worker. You read results files and decide. That is the
whole job.

The previous orchestrator burned 343M prompt tokens in 49 runs and still had context left at 16:50Z
because it never read a source file itself. Copy that discipline exactly. If you find yourself
thinking "I'll just read this one file to check", dispatch a subagent instead — a three-line task
costs less than the file.

The tool, in full, on PATH in a login shell (`bash -lc` — `fleet-manager` is not on PATH otherwise):

```bash
fleet-manager dispatch "<the task>" --tier low|default|best --name <label> --dir /home/friend/ticketPricing
fleet-manager dispatch list --json          # what is running / finished / lost
fleet-manager dispatch result <runId> [--tail N]   # the answer lives here, NEVER on stdout
fleet-manager fanout "<template>" <task> <task> …  # same prompt, N tasks, four at a time
```

Rules learned the hard way:

- **One dispatch per shell call.** A comma-list of paths in one argument is refused as a recursive walk
  and the dispatch silently never fires; a relaunch then creates duplicates. Check
  `dispatch list --json` before relaunching anything.
- **Cap at 5 concurrent runs** (`fanout` self-caps at 4). The box has 6 cores, 7.9 GB RAM, **no swap**,
  and each child pi is 150–270 MB. The previous orchestrator opened 14 children once and had to kill
  its own duplicates.
- **`running` is not "returned nothing".** Only a *failed*, *lost*, or *empty* run earns the single
  re-dispatch. A provider 503 does kill a run outright (`02-b-cap` ran 35 min and died); that one gets
  re-dispatched once with a narrower brief, then you move on.
- Dispatched children inherit a stale fleet-manager charter as their system prompt. Known, harmless —
  explicit task text overrides it. Prefer `--tier best` for judgement work, `low` for mechanical work.

---

## 3. Where the work stands

The product is a ticket-pricing console served by our own backend on `:8788`. It is built, tested and
committed. The state of it, from `12-final-audit.md` (written 16:16Z–16:31Z by an independent auditor
who wrote its own sweep rather than trusting the project's check tool):

**Verdict: CAN WITH THESE THREE FIXES.**

| property | what it asserts | violations |
|---|---|---|
| (a) cap-naming | the cap the page names is the cap it prices against | **0** |
| (b) band-versus-ceiling | no band crosses a ceiling the page says it will not cross | **0** |
| (c) excluded-count-as-zero | no sentence claims rows are absent when the mode excludes them | **0** |
| (d) decision-mode premise | every temporal premise is true at the printed instant | **60** |

Measured on a 360-state grid (8 events × 2 modes × 4 caps × 3 cuts) plus 1,500 cap-grid states which
are clean for (a)/(b)/(c). The instrument was controlled against the pre-fix tree `72bb8d3`, where the
same rules fire 646 and 2,986 times — so the zeros are measurements, not a blind parser.

**Property (d) is your next fix and it is one defect, not sixty.** The counterfactual label says the
page recomputes from *"this event's own completed record … in hindsight"* when (i) the event has not
happened yet — the default page, event starts 2026-11-21 — and (ii) the event has no resales at all —
the cold-start page, which prints both "completed record" and "No resale has been recorded on this
event". The mode label, the mode sentences and three mode-excluded labels all assert a premise the
event's own state contradicts.

The auditor's own three fixes, in its order of importance, are §5 of `12-final-audit.md`: (1) make the
mode sentences true at the printed instant; (2) scope or remove the mode-excluded labels; (3) replace
the patch prose and resolve the uncut prior. It says plainly that these are local prose and label
changes that touch neither the engine, the store, the cap arithmetic, the band cut, the clock, nor the
frontend — and that after them the console can be shown to a judge.

---

## 4. Your first dispatch — the re-dispatch queue

One run was in flight when the handover happened and it was cancelled mid-edit. It is reproduced here
verbatim. Dispatch it as your first action, with this task text unchanged.

```bash
# write the block below to a file first, then:
fleet-manager dispatch "$(cat /tmp/t-mode-sentences.txt)" --tier default --name MODE-sentences --dir /home/friend/ticketPricing
```

```
You are the decision-mode fixer for the Ticketpath console. Working directory: /home/friend/ticketPricing. The independent audit records/findings/12-final-audit.md swept 360 page states: properties (a) cap-naming, (b) band-versus-ceiling and (c) excluded-count-as-zero are now clean at zero violations each. Property (d), the decision-mode premise, has 60 violations. Fix property (d) at the source and stop.

THE DEFECT, in the audit's words: the counterfactual label says the page recomputes from "this event's own completed record ... in hindsight" when the event has NOT happened yet (the default page, event starts 2026-11-21) and when it has no resales at all (the cold-start page, which prints both "completed record" and "No resale has been recorded on this event"). The mode label, the mode sentences and three mode-excluded labels assert a premise the event's own state contradicts.

DO:
1. Read the audit's property (d) section for the full list of 60 states with their text, and its own suggestion if it made one.
2. Make the mode label a function of the event's actual state at the decision instant, not a fixed word. The states that must each read correctly: an event before its on-sale with no record; an event in market with some resales; an event completed with resales; an event with no resales at any time; an event cancelled or revoked if the schema has such a status. In each case the label must be true, and the sentences attached to it must not claim a record the event does not have.
3. Keep the distinction the earlier review required: a counterfactual recomputation must never be presented as a price the organizer could have set, and a before-on-sale decision must never use the event's own rows. Both must survive the rewording.
4. Add a test per state that fails on the old wording, demonstrated by reverting in a scratch copy.

AFTER: run the full suite and both check tools; restart the server on 8788; re-sweep property (d) on the same 360-state grid the audit used and report the violation count, which must be zero or explained state by state.

DELIVERABLE: the code, the tests, and a dated section in records/BUILD-REPORT-CONSOLE.md with the before and after for each state class.

HARD RULES: no computed number changes; wording and mode logic only. Do not weaken a test. No new dependency. Do not touch the frontend, do not bind 8787. Do not read or write /home/friend/agentFleet, ~/fleet-gui, ~/fleet-manager. Commit nothing, push nothing.

Finish by printing: the property (d) violation count before and after on the same grid, the label text for each of the five event states, the test count, and any state you could not make true with the reason.
```

That run had reached: all four source files edited (`core/labels.py`, `api/guidance.py`,
`console/blocks.py`, `orchestrator.py`), a new `tests/test_decision_mode_states.py`, plus edits to two
existing test files and `tools/console-check.py`, and was re-running its sweep when it was stopped. Its
partial work is preserved on branch `wip/mode-sentences-20261107T1650Z` (head `8ea1863`, pushed) —
**reference only. It was never verified and must not be merged blind.** Dispatch the task fresh; do not
tell the child to continue from that branch unless you have decided the partial work is right.

---

## 5. Gates that must stay green

Before any commit that touches `ticketpath/`:

1. **`python3 -m unittest discover -s tests` → 441 tests, OK.** (Measured on `main` at 16:56Z with a
   fresh server. The figure 408 in the older log entries is historical.) There is no venv and no
   pytest here — it is `unittest discover`, and `/usr/bin/python3` is the interpreter.
2. **`python3 tools/console-check.py` → `FAILURES: 0`** against a server on **`:8788`** (it hardcodes
   `BASE = http://127.0.0.1:8788`, so the server must be running the tree you mean to check, not a
   stale one — this bit me at handover and produced a phantom failure).
3. **The independent property sweep** — the audit's `/tmp/audit12/sweep.py` (360-state grid). The
   project's own check tool is not trusted alone: at 15:49Z the proof run discovered that
   `console-check` **0 failures** was a gate certifying a bug it asserted as correct. Both the tests
   and the check tool have since been shown to bite (124 test failures and 8 tool failures on a
   `git archive HEAD` tree). Keep it that way: every new assertion must be shown to fail on the old
   behaviour.

---

## 6. The clock and the rubric

- MLH Solana Hackathon, online, 2026-11-06 → 11-08. **Initial submission Sun 10:00 ET / 15:00Z**
  (this is the binding one), final 11:45 ET / 16:45Z.
- Judging criteria: **25/25/25/25 — Technology, Design, Completion, Learning**, equally weighted.
  MLH explicitly excludes **idea quality, pitch quality and code quality** from the rubric — so a
  beautiful refactor and a clever idea both score zero on their own. (The rubric finding
  `records/findings/02-rubric-and-scoring.md` overturned the *specific* 25/25/25/25 naming in the
  original night brief as unsourced — originality/technical-complexity/theme-fit are not on any MLH
  page — while confirming four equally weighted lines. Design at 25% is the least-built thing here;
  Completion means "a judge can see it work".)
- The top prize's only written criterion is a materials test, verbatim from the event page:
  *"We're looking for a working product that uses Solana for something it's good at (speed, low fees,
  composability, on-chain ownership), **not a chain bolted onto a web2 app**."* A judge applies it by
  looking for four things: an account that belongs to the project, a transaction signature, a program
  that is not the team's own code doing the work, and the app reading that state back. The repo has
  none of the four; the on-chain slot is designed in `docs/ON-CHAIN-FOR-LAPTOP.md`, not implemented.

---

## 7. Hard constraints

- **No Solana toolchain on this box** — no `solana`, `anchor`, `cargo`, `rustc`. Nothing can be
  deployed from here. Do not dispatch a task that assumes a deploy; the on-chain work is specified for
  the operator's laptop.
- **`:3000` is the operator's live frontend** (pid 81447, `next-server`). It must answer 200 and must
  not be restarted, rebound, or written to. `:8787` is the fleet's own page — do not bind it.
  **`:8788` is yours** — the console server, currently running from `main` (started 16:56Z). `:3001`
  holds a copy of the frontend against our backend; leave it alone unless you need it.
- **Do not touch the three fleet repos**: `/home/friend/agentFleet`, `~/fleet-gui`, `~/fleet-manager`.
- **Publishing**: `main` is auto-pushed by a cron every 15 minutes
  (`*/15 * * * * /home/friend/ticketpath-push.sh`, which pushes `HEAD:main` and refuses a diff that
  looks like a credential). Commit and let it publish, or push yourself. Never force-push. Never leave
  `HEAD` on a side branch across a cron tick — the cron pushes `HEAD`, whatever branch that is.
- **No secrets in the tree.** The repo is public. The GitHub credential is a repo-scoped deploy key at
  `~/.ssh/ticketpath_deploy_ed25519`; do not read it, copy it, or put it in a command line.
- Commit as `Andrew Radu <72272191+andy1245-rgb@users.noreply.github.com>`, which is already the
  configured identity.

---

## 8. Never stop, never idle

You are the only thing keeping this build moving until 15:00Z. The failure mode is a quietly stalled
session, so:

- **Bug found → dispatch an orchestrator to fix it and keep going.** Do not stop the night to fix
  something yourself, and do not wait idle for a run you could have worked alongside.
- **A dispatch that returns nothing** (a provider 503 kills a run entirely) → re-dispatch once with a
  narrower brief, then move on. Record the failure and the retry.
- **Record as you go** in `NIGHT-LOG.md`, append-only, one line per event, UTC, in the existing shapes:
  `## HH:MMZ · dispatched|returned|verified|failed|finding|cost  name  detail`. Include your failures;
  a log with no failures in it is not being kept.
- Verify the artefact on disk before you call a run returned. A run that says it wrote a file and did
  not is the most expensive failure of the night.

---

## 9. What changed at handover — read this so you do not re-litigate it

- The `pi` runner (`pid 218725`, pane `wJ:p1`) and the in-flight run `dmw6mou3ertm6` (`MODE-sentences`)
  were stopped at ~16:50Z, **after** the work was snapshotted and pushed. Nothing was lost; see below.
- Pre-kill snapshot of every dirty file, the diff, and the full work-in-progress:
  `/home/friend/night-snapshot-20261107T164828Z/` (contains `WIP.diff`, the four edited sources,
  `12-final-audit.md`, and `test_decision_mode_states.py`).
- Branch `wip/mode-sentences-20261107T1650Z` @ `8ea1863`, pushed: the cancelled run's partial
  property-(d) work, recovered in full from its session transcript (15 tool calls, 0 unmatched) when a
  tree tidy reverted three of its files. **Not verified. Do not merge blind.**
- `main` is at `8dfb2c3` and was left functionally identical to the tree the audit measured. The
  audit's findings file and the log's dispatch note were committed on top of it.
- The `:8788` server was restarted from `main`'s code at 16:56Z because the one left behind was running
  the cancelled run's partial fixes — a stale server is what produced a phantom `console-check` failure.
- `~/.claude-code-token.env` supplies `CLAUDE_CODE_OAUTH_TOKEN`; `~/.profile` and `~/.bashrc` both load
  it, but a non-login shell does not, and `claude auth status` then reports `loggedIn: false`. If you
  ever see that, you are in a shell without the token, not logged out. `claude -p` round-tripped in 3 s
  at 16:53Z, so the credential is live.
- Open item that is the operator's, not yours: `LICENSE` line 3 still reads
  `Copyright (c) 2026 [OPERATOR: replace this bracket with your name]`. Do not invent a name; flag it
  in `NIGHT-LOG.md` and leave it.

Begin with §4. Log the dispatch before you read its result.

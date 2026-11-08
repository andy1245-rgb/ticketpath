# Public-safety: what may not be published, and the check that stops it

This repository is public: `github.com/andy1245-rgb/ticketpath`. Every commit is
published, the research record included. The record is written by agents during a run,
which means it also holds whatever an agent happened to write down on the way: a pid, an
absolute path, the name of his other repositories, the command line that starts a job. None
of that belongs in a public repository, and none of it is evidence for anything the
research claims.

So there are two halves. The material stays out (`.gitignore` plus a rule in `AGENTS.md`),
and a check refuses to let it back in through a commit or a push (`tools/public_safety.py`).
It does not clean what is already published, and it cannot: see the re-measurement at the end
of this file.

## The check

```bash
python3 tools/public_safety.py check                  # every tracked file, from disk
python3 tools/public_safety.py check --staged         # what the next commit would add
python3 tools/public_safety.py check --range origin/main..HEAD   # what a push would publish
```

Exit 0 clean, 1 if anything matched, 2 if the denylist itself is unreadable. Hits print one
per line as `path:line: class: what`, and a `path` with no line number means the file's
name matched. `--staged` and `--range` read the blob that would be published, not the
worktree, so a secret staged and then deleted from disk is still caught. Content classes
that are themselves credentials (key blocks, tokens, `.env` assignments) are masked in the
output: a log gets copied into reports and chat, and the matched string must not travel
with it.

It does not look at history, and it cannot prove a secret is absent, only that the shapes
listed in the denylist are absent. It reads no network and writes no file.

## The denylist

`.public-denylist` holds the rules, one pattern per line, with a comment per class saying
why. Three kinds of line:

```
path    <class> <regex>            the file PATH
content <class> <scope> <regex>    one line of file CONTENT; scope is all or code
allow   <glob>  <class> <reason>   suppress a class for a path glob, with a reason
```

`code` means every file outside `records/`. A line that does not parse is a hard error, so
a rule cannot be lost by a typo.

| class | caught |
|---|---|
| `handover-file` | `NIGHT-*`, snapshot directories, `WIP-`/`HANDOVER-` files |
| `secret-file` | `.env`, `*.pem`, `*.key`, `id_rsa` and the rest of the SSH family |
| `fleet-repo` | the names of his other three repositories |
| `home-path` | an absolute path under a home directory, and the `~/` forms of the above |
| `tmp-path` | a scratch path in code, not in `records/` (the stated exception) |
| `cron-line` | a scheduler line, a crontab listing, a boot-time job |
| `deploy-key` | the deploy key's file name |
| `live-service` | pids, and ports tied on the same line to a running process or to him |
| `private-key` | `-----BEGIN ... PRIVATE KEY-----` |
| `token-shape` | `ghp_`, `github_pat_`, `sk-`, `AKIA`, `xox*`, OAuth token assignments |
| `env-content` | a line assigning a literal to a secret-shaped variable name |
| `contact-email` | a third party's address (GitHub's own addresses, and the names reserved for documentation -- `example.*`, `*.invalid`, `*.test`, `*.example` -- are excluded) |
| `personal-name` | the licence holder's full name outside `LICENSE` and the README line |

Two narrowings are deliberate and were made on evidence rather than taste. `sk-` requires
a word boundary, or every sentence about a risk-adjusted objective is a hit. `env-content`
requires the value to be the whole line, at least eight characters, and to carry a letter,
because the first cut flagged a test's `SEED = bytes(range(32))` and the second the fixture
generator's `SEED = 20261107`. Both are deterministic seeds and neither is a secret.

The same holds for ports: `8787 is refused because another process owns it` is a design
statement and passes; `:3000 is his frontend` is handover and does not.
8788 is not denied at all, because it is this project's own documented backend port.

## Exceptions

`allow` lines are per path glob **and** per class, and each one must carry a reason of at
least four words. One line may list several classes, separated by `|`, and `*` means all of
them. A file that is exempt for a quoted address is still checked for a pid.
Today's list, in full:

- `.public-denylist` for every class: the rule file has to spell the patterns it denies.
- `LICENSE` and `README.md` for `personal-name`: the MIT licence must carry the holder's
  name to be a licence, and the README restates the same line.
- `tests/test_public_safety.py` for the eight material classes it plants, because a test
  for a pattern has to spell the pattern. The credential classes are deliberately not
  exempt for it: that file assembles them by concatenation instead, so the file itself
  stays clean under the rules that matter most.
- `records/*` and `records/findings/*` for `contact-email`: the record quotes the
  hackathon's own published address as the terms that were read. A
  quote of a published address is evidence, not a contact of his.

Anything else that matches is either fixed or reported to the operator. Research records
are never edited to make the check pass: they are the run's evidence, and a hit in one is
his decision, not a cleanup.

## Where it is enforced

**Before a commit**, the hook runs the index check. The exact one line a pre-commit hook
must call:

```bash
python3 tools/public_safety.py check --staged || exit 1
```

That is the whole wiring. `.githooks/pre-commit` calls that line as its first step, before
the narrow credential scan and before the quick gate, and `.githooks/` is a test in
`tests/test_cli.py` from the other side: it plants a handover file and a file holding an
absolute home path in a scratch clone, reads the exit code git returned, and then removes
that one line and shows the same handover file committing. A refusal whose test survives
the wiring being taken out is not a test of the wiring.

What it covers is the files in that commit and nothing else. A tracked file the commit does
not touch is never read by it, which is why the whole-tree reading is a separate command and
why the re-measurement below exists.

**Before a push**, `~/ticketpath-push.sh` runs the range check after the "anything to
push" guard and before anything leaves the machine, on a scheduler that runs it every
fifteen minutes. If it fails, the script logs
`REFUSED: <n> commit(s) ahead and public_safety rejected the range` plus the hits, and
exits 1 without pushing. Exit 2 (unreadable denylist) refuses as well: a gate that cannot
read its rules is shut. One limit is worth stating: the range is the commits ahead of
`origin/main`, so this covers what is about to be published and not what already was. The version before this change is kept as
`~/ticketpath-push.sh.bak-20261107T174652Z`.

**History is never rewritten without the operator's explicit say-so.** No rebase of a
published branch, no force-push, no history filter. If something has already been pushed,
the first move is to rotate what leaked, and the second is his call.

## What stays local

`NIGHT-BRIEF.md`, `NIGHT-CONTINUE.md`, `NIGHT-LOG.md`, `NIGHT-QUEUE.md`, snapshot
directories and any other handover sheet: on disk, out of git, matched by `.gitignore` and
by the name rules. What a run learned belongs in `records/` as research. The instruction
sheet it was driving itself with does not belong in the repository at all.

## State when this was written

Measured 2026-11-07T17:50Z, after the four handover files were untracked: four tracked
files removed and 100 hits remaining, every one of them inside `records/` (62 `live-service`,
23 `home-path`, 12 `personal-name`, 3 `fleet-repo`) and none in code or in `docs/`. Those
are quoted measurements in the research record, left in place on purpose and reported to
the operator. Everything outside `records/` was fixed: absolute paths replaced with
relative ones, pids and the `.env` write removed from `docs/morning.html`, the deploy key's
name removed from `.gitignore`, the frontend path made relative in `AGENTS.md`.

## Re-measured 2026-11-07T18:45Z, and again at 18:48Z after two redactions

`python3 tools/public_safety.py check --tracked` reads every tracked file from disk, and it is
the only one of the three entry points that looks at what is already published. Two readings, an
hour apart, and the difference between them is the point:

| Reading | Result |
|---|---|
| `8a5e5e6`, 18:45Z | **77 hits in 11 tracked files**, 51 `live-service`, 23 `home-path`, 3 `fleet-repo` |
| the tree as committed at 18:50Z | **64 hits in 9 tracked files**, 48 `live-service`, 14 `home-path`, 2 `fleet-repo` |

The two files that left the list, `records/findings/12-final-audit.md` and
`records/DELIVERABLE.md`, left it because a correction had to be committed to each and the
public-safety gate refuses a file that carries a home path or a process id. The redactions are
the minimum that let the commit through, they are listed in each file's own correction note, and
no number, finding or verdict in either file changed.

Every remaining hit is inside `records/`. Counted by file and class at 18:50Z:

| File | Hits | Classes |
|---|---|---|
| `records/FINAL-PROOF-2.md` | 26 | home-path, live-service |
| `records/FINAL-PROOF.md` | 14 | home-path, live-service |
| `records/DEMO-PROOF.md` | 11 | live-service |
| `records/findings/07-engine-review.md` | 4 | fleet-repo, home-path, live-service |
| `records/findings/10-final-review.md` | 3 | fleet-repo, home-path, live-service |
| `records/FRONTEND-HONESTY-PATCH.md` | 2 | live-service |
| `records/REPO-CONSISTENCY.md` | 2 | live-service |
| `records/CONTRACT-CONFORMANCE.md` | 1 | live-service |
| `records/FIXTURE-STORE.md` | 1 | live-service |

Three consequences, stated rather than implied:

1. **The tree fails its own check.** The rules above are the ones the repository says it
   keeps, and the published tree does not keep all of them. A judge who opens `records/` sees
   pids and absolute paths while `AGENTS.md` says they may not be there. That is now written
   in `AGENTS.md` and here, and it is a fact about the tree rather than about the next commit.
   **[CORRECTED 2026-11-08T09:22Z: this was true at 18:50Z on 2026-11-07 and is false at
   `HEAD 948b5d5`. The tree passes. See the section at the end of this file.]**
2. **The gates are real but narrower than the tree.** A commit is checked on the files it
   carries and a push on the commits ahead of `origin/main`. Neither one re-reads a file it
   does not touch, so already-published hits pass both indefinitely.
3. **The remedy is one of two, and both are the operator's.** Either each of the 9 files gets
   an `allow` line with a reason (the mechanism already exists and is per file and per class),
   or the strings are redacted on disk. Redacting does not unpublish what is already in
   history; the history question is his, not a tool's.

This section replaces the 17:50Z reading above for the count and adds nothing to the rules: the
checker, the denylist and the exceptions are unchanged by this pass.

## Re-measured 2026-11-08T09:22Z: clean on the tracked tree

`python3 tools/public_safety.py check --tracked` → `public_safety: clean, tracked tree, 285
file(s)`, exit 0.

Commit `aea1cbe`, "Redact the machine handles from the published proof files", is what changed it.
It took the first of the two remedies the 18:45Z section offered: the nine files named above were
redacted on disk, the identification each handle carried was kept where it was the evidence, and
`.public-denylist` was not touched, so no exception was bought to make the number go away. The
gate that reads the staged diff and the gate that reads the range ahead of `origin/main` are
unchanged and both remain clean.

What the 18:45Z section says about the gates stays true: a commit is checked on the files it
carries and a push on the commits ahead of `origin/main`, and neither re-reads a file it does not
touch. The whole-tree check is the only one of the three that reads what is already there, and it
is the one that was red. It is now green because the files were fixed, not because the check was
narrowed.

This section replaces the 18:45Z reading for the status and the count and adds nothing to the
rules: the checker, the denylist and the exceptions are unchanged by this pass.

# Public-safety: what may not be published, and the check that stops it

This repository is public: `github.com/andy1245-rgb/ticketpath`. Every commit is
published, the research record included. The record is written by agents during a run,
which means it also holds whatever an agent happened to write down on the way: a pid, an
absolute path, the name of his other repositories, the command line that starts a job. None
of that belongs in a public repository, and none of it is evidence for anything the
research claims.

So there are two halves. The material stays out (`.gitignore` plus a rule in `AGENTS.md`),
and a check refuses to let it back in (`tools/public_safety.py`).

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
| `contact-email` | a third party's address (GitHub's own addresses are excluded) |
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

That is the whole wiring. `.githooks/` and the CLI are built by another pass; when the
hook is added, it takes that line and nothing else.

**Before a push**, `~/ticketpath-push.sh` runs the range check after the "anything to
push" guard and before anything leaves the machine. If it fails, the script logs
`REFUSED: <n> commit(s) ahead and public_safety rejected the range` plus the hits, and
exits 1 without pushing. Exit 2 (unreadable denylist) refuses as well: a gate that cannot
read its rules is shut. The schedule, the remote and the credentials handling are
unchanged, and the script never reads the key. The version before this change is kept as
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

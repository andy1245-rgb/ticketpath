# Push plan

How `release/prep` would land on `main`, what to run before it does, and the two ways to send it.
Nothing in this document has been done. Nothing has been pushed by any pass on this branch.

## The two commits

| | |
|---|---|
| base | `33d95b3` — `origin/main`, and the last commit on the public repository |
| release tip | `009f103` — everything on this branch except this file |
| branch tip | one commit after `009f103`: the commit that carries this document. `git rev-parse HEAD` gives its id, and its subject is the only one on the branch that names this file |
| branch | `release/prep`, in the worktree `../ticketPricing-release` |
| commits between | 18, of which 11 were made by the release-prep pass and 7 by the integration pass that wrote this file |
| authors | 9 by `andy1245-rgb <72272191+andy1245-rgb@users.noreply.github.com>`, 9 by `VeerCodes <71789544+VeerCodes@users.noreply.github.com>` |
| committer on every one | the same person as the author. `git log --format='%an|%cn' 33d95b3..HEAD` prints no line whose two halves differ |

The branch is a straight descendant of `33d95b3`; `main` has not moved. A push is therefore a
fast-forward and creates no merge commit.

## Before any push: the readings this branch was handed over with

Run each from the worktree and compare against the number on the right. A reading that differs
is not automatically a defect, but it is a question to answer before pushing, not after.

```bash
git status --short                                          # empty
git log --oneline 33d95b3..HEAD | wc -l                      # 18
python3 -m unittest discover -s tests                        # Ran 1251 tests, OK (skipped=27)
python3 -m unittest discover -s market_swarm/tests           # Ran 771 tests, OK (skipped=2)
python3 tools/tp.py gate --quick                             # gate ok, doc-check=0 violation(s)
python3 tools/doc_check.py --root .                          # clean, 7 check(s), 24 allowed absences
python3 tools/public_safety.py check --tracked               # clean, tracked tree, 367 file(s)
python3 tools/public_safety.py check --range origin/main..HEAD   # clean over every commit's files
```

`check --range` is the one the scheduled push gate runs, and it reads the commits ahead of
`origin/main` rather than the tree. Run it last, because it is the last thing that will refuse.

## The surface a reader actually sees: a fresh clone

A worktree that has never been cloned hides two classes of defect: a file that is git-ignored and
therefore absent, and a check that only passes because of something on this machine. Run these
from a directory that is not this one.

```bash
git clone --no-hardlinks --branch release/prep <this repo> /tmp/verify-clone
cd /tmp/verify-clone
git rev-parse HEAD                       # the branch tip
git ls-files | wc -l                     # 367 at 009f103
python3 tools/tp.py gate --quick
python3 tools/public_safety.py check --tracked
```

Then follow `README.md`'s quick start literally, in that clone, in a fresh virtual environment:
`python3 -m venv .venv`, `. .venv/bin/activate`, `pip install -e .` if the README says to, start
the server with the documented command, and drive it with `python3 tools/tp.py health`. The
frontend's own quick start is `cd frontend && npm install && npm run dev`; that installs
dependencies and needs network access, so it is the operator's call and not a step a check takes.

A `git archive` extraction is **not** a clone and must not be used as one: measured at `dd42348`,
an archive fails 5 tests and 2 documentation checks that are all artefacts of there being no
`.git` for `git ls-files` to read. A clone at the same commit passes all three.

## Step 1: the deploy key

The remote named `origin` is already configured with the ssh form and the deploy key this machine
holds, so the command is the whole command:

```bash
git push origin release/prep:main
```

`release/prep:main` is deliberate: it sends the branch's commits to `main` and leaves the remote
branch `release/prep` uncreated. If you would rather the remote kept a branch, drop the `:` half
and push `release/prep` on its own, then open a pull request.

If `main` has moved since `33d95b3`, this push is refused as non-fast-forward. That refusal is
correct. Merge `origin/main` into `release/prep` and push again; do not force.

## Step 2: HTTPS, with the credential prompt

For a push from an account other than the one the deploy key belongs to. This is the form to hand
to Veer, because it asks for the credential rather than assuming a key on the machine:

```bash
git push https://github.com/andy1245-rgb/ticketpath.git release/prep:main
```

It prompts twice: `Username` is the GitHub account name, and `Password` is a personal access token
with write access to this repository, not the account password. A token pasted at that prompt
stays out of the shell history and out of this repository. Nothing in this tree needs to hold it.

**Only one of the two steps runs, not both.** They send the same commits to the same branch. If
step 1 has already landed, step 2 answers `Everything up-to-date` and changes nothing.

## What must not happen during either step

- No `--force`, no `--force-with-lease`, no rebase of anything already pushed. The project's rule
  is that history is never rewritten without the operator's explicit yes, and a secret that is
  already published is rotated first, not edited out.
- No `--no-verify`. The pre-commit hook and the push gate are the two things that have refused a
  bad file on this branch; a bypass turns both off for that commit.
- If the push gate refuses, read the `path:line: class:` lines it printed and fix the file, or add
  one per-path exception with a reason to `.public-denylist`. Do not widen a class.

## What is still open when the push lands

- **The operator's review is the last gate, not the first.** Everything above is a machine
  agreeing with itself.
- **The copy edits.** `frontend/NOTES.md` lists the sentences the demo ships that read as shipped
  features, and `records/F-decision-log.md` Q6 records them as an open decision. They are a text
  pass over the app, deliberately not part of this branch.
- **Two claims this branch inherits and does not settle.** The `unresolved` policy still has no
  byte in the live program, and the prebuilt program artefact is a v2 build that a local v1 run
  would deploy under v1's address and be refused by. Both are recorded in
  `records/STATE-OF-PROJECT.md` and neither is closed here.
- **`records/video/inputs/build-state-matrix.md` carries 13 line anchors into
  `records/STATE-OF-PROJECT.md` that were already about 300 lines stale** before this pass, and
  are one line further off now. Re-deriving them belongs to whoever owns the video package.
- **Feature 5's row in `records/STATE-OF-PROJECT.md` still reads "not built"** while the artist
  fee is built and finding 42 measures it. The shared checkout wrote it that way and added a
  closing section that says the row is stale. Moving the row is a status decision, not a fix.

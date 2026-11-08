# Push plan

How `release/prep` lands on `main`, what to run before it does, and the two steps that send it.
Step 1 has been done: the first 11 commits are published on `origin/main` as `4430fb1`. The commits
after it are step 2, and Veer pushes them from his own terminal.

## The two commits

| | |
|---|---|
| base | `33d95b3` — the base this branch was cut from, and the commit `origin/main` pointed at then. **`origin/main` is now `4430fb1`**: the first 11 commits of this branch, pushed 2026-11-08 at 13:07Z by the deploy key, as Andrew's half |
| release tip | `eaf4ab7` — everything on this branch except this file **[corrected 2026-11-08T12:00Z: except four files, not one. `git diff --name-status eaf4ab7..a921ecf` → `M README.md`, `M records/F-decision-log.md`, `A records/PUSH-PLAN.md`, `M records/STATE-OF-PROJECT.md`. The commit that carries this document also leaves `README.md`, `records/F-decision-log.md` and `records/STATE-OF-PROJECT.md` in an earlier state than the branch last left them, so pushing `eaf4ab7` directly lands three documents short of the corrections made with this one. Push `release/prep:main` and not the SHA, or push the SHA only if those three files are known to be acceptable in their `eaf4ab7` form. The same test applies to any later commit: `git rev-parse HEAD` at the moment of the push is the only tip that carries everything, and `eaf4ab7` is four files behind `a921ecf` before any commit after it is counted.]** |
| branch tip | the last commit on the branch. `git rev-parse release/prep` gives its id, and two commits after `a921ecf` carry the independent review's corrections. No document names the tip's own id, because a commit cannot contain its own hash |
| branch | `release/prep`, in the worktree `../ticketPricing-release` |
| commits between | 24, of which 11 were made by the release-prep pass, 7 by the integration pass that wrote this file, 2 by the review that pass commissioned, 1 that re-points the commit ids after the committer rewrite below, 2 redaction commits written after this document, and 1 that corrects this document once the first half was published. **[Measured 2026-11-08T12:40Z: `git rev-list --count 33d95b3..HEAD` → 21. Re-measured at the tip that carries this line: `git rev-list --count 33d95b3..HEAD` → 24, of which 11 are the ones `4430fb1` names and `git rev-list --count 4430fb1..HEAD` → 13 are step 2.]** |
| authors | 12 by `andy1245-rgb <72272191+andy1245-rgb@users.noreply.github.com>`, 12 by `VeerCodes <71789544+VeerCodes@users.noreply.github.com>`. **[`git log --format='%an' 33d95b3..HEAD | sort | uniq -c` → `12 andy1245-rgb`, `12 VeerCodes`. Split by half: `33d95b3..4430fb1` is 6 `andy1245-rgb` and 5 `VeerCodes`, which is what is published; `4430fb1..HEAD` is the mirror of it, 6 `andy1245-rgb` and 7 `VeerCodes`, which is what step 2 carries.]** |
| committer on every one | **the same person as the author, on all 24.** `git log --format='%ae|%ce' 33d95b3..HEAD | awk -F'|' '$1!=$2'` prints nothing. This was not true when this document was first written: the eleven commits the release-prep pass made carried the author's name but the repository default `t@example.invalid` as the committer email, and the integration pass's own nine carried both correctly. The eleven were rewritten by `git filter-branch --env-filter`, which preserves every tree, message, author and date byte for byte and changes only the committer field. **[Measured 2026-11-08T12:39Z, after the rewrite: 0 commits whose committer email differs from the author's.]** |
| what the rewrite cost | every commit id changed, so every document citing one had to be re-pointed: **95 citations across 9 files**, done in one commit whose message carries the whole old-to-new map so each substitution can be checked against `git log`. No old id survives: `git grep` for any of them returns nothing. |
| the old branch | kept on the local ref `pre-replay-wip` at `f584327`, so the pre-rewrite history is one `git branch -f` away until it is deleted. It was never pushed, so nothing public was rewritten. |

The branch is a straight descendant of `33d95b3`, and `origin/main` has moved *along* it, to
`4430fb1`. What is left is still a fast-forward from `4430fb1`, so step 2 creates no merge commit.

## What each commit is, on its own

A commit that only stands up because the working tree held something else is a commit that cannot
be checked out and believed. Measured 2026-11-08T12:52Z by cloning the branch once and detaching to
each of the 21 commits, then running `tools/tp.py gate --quick`, `doc_check` and
`public_safety --tracked` inside the clone: **11 stand on their own and 10 do not.**

The ten are the first nine, plus the one at position 15. The cause for the first nine is structural
rather than careless: the release-prep pass built each commit by resetting the index and staging one
area's paths, while the working tree held the *whole* finished tree. The pre-commit hook runs its gate
against the working tree, not against the commit, so a commit whose tree was internally inconsistent
passed the hook that was supposed to catch it. By symptom:

- **positions 1 to 4** fail the test suite in a clone. One instance, quoted: their `chain_client.py`
  has no `MEMO_PROGRAM_ID`, while their `tools/devnet_publish.py` imports it, so 22 errors and 2
  failures and the tool cannot start.
- **positions 1 to 5** have no `tools/doc_check.py` at all, because the commit that adds it is
  position 6. There is nothing to run there, so the reading is a missing tool and not a violation.
- **positions 6 to 9** have `doc_check`, but the version that predates the `git check-ignore` fix, so
  it reports the git-ignored `records/onchain-v2.local.json` and `records/devnet-progress.json` as
  missing files: 31 violations at position 9, none of them a claim about the code.
- **position 15** is a split this pass made wrongly: it moves the state file one commit before the
  decision-log heading that state file cites.

**What that means for a reader.** Nothing for the tip, which is what gets pushed, and nothing for
the halfway commit: the halfway of 21 commits is position 11, and positions 10 and 11 both pass all
three checks on their own in a clone. What it does mean is that `git bisect` across positions 1 to 9
will land on commits that do not build, and that a reader who clones one of them and runs the tests
will see failures the commit message does not admit. Fixing it means re-splitting nine commits by
content, which changes what they contain, and squashing the pair at 15; neither was done, because
both rewrite what another pass recorded and neither changes a byte of what gets pushed.

## Before any push: the readings this branch was handed over with

Run each from the worktree and compare against the number on the right. A reading that differs
is not automatically a defect, but it is a question to answer before pushing, not after.

```bash
git status --short                                          # empty
git log --oneline 33d95b3..HEAD | wc -l                      # 24
python3 -m unittest discover -s tests                        # Ran 1251 tests, OK (skipped=27)
python3 -m unittest discover -s market_swarm/tests           # Ran 771 tests, OK (skipped=2)
python3 tools/tp.py gate --quick                             # gate ok, doc-check=0 violation(s)
python3 tools/doc_check.py --root .                          # clean, 7 check(s), 24 allowed absences
python3 tools/public_safety.py check --tracked               # clean, tracked tree, 394 file(s) at HEAD
git ls-files | wc -l                                         # 394 at HEAD, 393 at eaf4ab7
python3 tools/public_safety.py check --range origin/main..HEAD   # clean; reads only the 13 commits after 4430fb1
```

`check --range` is the one the scheduled push gate runs, and it reads the commits ahead of
`origin/main` rather than the tree. Run it last, because it is the last thing that will refuse.

**The range reading no longer covers the whole branch.** Since step 1, `origin/main` is `4430fb1`,
so `origin/main..HEAD` is the 13 commits after it and the 11 already published are not read at all.
The whole-branch form is `check --range 33d95b3..HEAD`; run that one when the question is what the
branch contains rather than what is still to be sent. Every reading in this section that counts from
`33d95b3` is a whole-branch reading: counted from the base, not from `origin/main`, so it moves when
the branch grows and not when `main` does.

**[Added 2026-11-08, at `HEAD 501c8ae`: the readings above are the branch as handed over at that tip,
and one redaction commit -- sibling-project names, a hostname and process ids taken out of two findings
-- sits on top of it, so at that tip the whole-branch reading `git log --oneline 33d95b3..HEAD | wc -l`
is 22, the author split is 11 `andy1245-rgb` and 11 `VeerCodes`, and the committer check still
prints nothing.]**

**[Measured at the tip that carries this line, as whole-branch readings from `33d95b3`:
`git rev-list --count 33d95b3..HEAD` → 24, and
`git log --format='%an' 33d95b3..HEAD | sort | uniq -c` → `12 andy1245-rgb`, `12 VeerCodes`. The two
commits added since `501c8ae` are both redactions: `7fef7a4`, which took sibling-project names, a
hostname and process ids out of two findings, and one that takes another user home directory out of
`records/findings/15-visionhelper.md`, a handover-note citation out of
`records/findings/14-frontend-attach-explore.md`, and a project name out of a comment in
`market_swarm/llm.py` with no code change. Both carry the same author and committer. The
standalone-commit analysis above was measured over the 21 commits present at 12:52Z and has not been
re-run over the two added since.]**

**[Corrected 2026-11-08T12:00Z, at `HEAD a921ecf`. Two readings in the block above were wrong and they
are replaced, not footnoted. `check --tracked` prints `public_safety: clean, tracked tree, 394
file(s)` and `git ls-files | wc -l` is 394; at `eaf4ab7` the tree is 393 files, which
`git ls-tree -r --name-only eaf4ab7 | wc -l` prints. The block said 367 for both, which was the index
at about 11:27Z, when 285 committed files sat beside 82 staged frontend files; the commits landed at
11:38-11:41Z and nothing wrote the new number back into this checklist. **The rule is that a file count
in this document is to be re-run and not trusted**: a tracked-file number is a property of one commit
and it moves on every commit that adds or removes a file, so the expected value on the right of the
line is a thing to compare against with the command, never a constant to paste.]**

## The surface a reader actually sees: a fresh clone

A worktree that has never been cloned hides two classes of defect: a file that is git-ignored and
therefore absent, and a check that only passes because of something on this machine. Run these
from a directory that is not this one.

```bash
git clone --no-hardlinks --branch release/prep <this repo> /tmp/verify-clone
cd /tmp/verify-clone
git rev-parse HEAD                       # the branch tip
git ls-files | wc -l                     # 394 at HEAD; see the note on the checklist above
python3 tools/tp.py gate --quick
python3 tools/public_safety.py check --tracked
```

Then follow `README.md`'s quick start literally, in that clone, in a fresh virtual environment:
`python3 -m venv .venv`, `. .venv/bin/activate`, `pip install -e .` if the README says to, start
the server with the documented command, and drive it with `python3 tools/tp.py health`. The
frontend's own quick start is `cd frontend && npm install && npm run dev`; that installs
dependencies and needs network access, so it is the operator's call and not a step a check takes.

**The clone skips four more tests than the worktree, and the difference is not a leak.** Measured at
`a921ecf`: `Ran 1251 tests` in the clone with `OK (skipped=31)`, and `Ran 1251 tests` here with
`OK (skipped=27)`. The four are `test_devnet_publish.TestFrozenDevnetUpgradeGuard`, which reads the
real `.so` under `programs/cap_hook/target/deploy/`; that file is git-ignored and present in this
worktree, and a clone cannot have it. The other 27 skips are the same 27 in both places. So the clone
runs the same suite over the same tracked files and skips more of it because the local artefacts are
absent, and nothing is hidden by the difference. A reader comparing the two lines should not read it
as one.

A `git archive` extraction is **not** a clone and must not be used as one: measured at `4430fb1`,
an archive fails 5 tests and 2 documentation checks that are all artefacts of there being no
`.git` for `git ls-files` to read. A clone at the same commit passes all three.

**[Corrected 2026-11-08T12:00Z, at `HEAD a921ecf`. The archive paragraph above gives readings that
were true at `4430fb1` and are not the ones an operator will see at this tip, and its "2 documentation
checks" is two named checks rather than two violations. Measured with
`git archive HEAD | tar -x -C /tmp/arch-tip`, then `python3 -m unittest discover -s tests` there:
`Ran 1251 tests`, `FAILED (failures=6, skipped=31)`, all six in
`test_public_safety.TestTheRecordsAllowlists`, which reads `git ls-files` and has no `.git` to read.
`python3 tools/doc_check.py --root .` there → `doc_check: 38 violation(s) in 18 file(s) of the tracked
tree (paths 36, feature-table 2)`. At `4430fb1` the same two commands give `FAILED (failures=5,
skipped=30)` and `35 violation(s) in 16 file(s) (paths 33, feature-table 2)`. So the "5 tests" is exact
at `4430fb1` and the tip reads 6, and the two named checks fire on 35 violations at `4430fb1` and 38 at
the tip. The clone at the tip passes all three: tests `Ran 1251 tests`, `OK (skipped=31)`;
`doc_check: clean, 7 check(s)`; `public_safety: clean, tracked tree, 394 file(s)`.]**

## Step 1: the deploy key — done

Step 1 happened on 2026-11-08 at 13:07Z. The deploy key that `origin` already holds pushed
`release/prep:main`, and the first 11 commits are now `4430fb1` on
`git@github.com:andy1245-rgb/ticketpath.git`. That is Andrew's half, it is public, and it is not
repeated.

The command that sent it, kept so the two halves can be named together:

```bash
git push origin release/prep:main
```

`release/prep:main` is deliberate: it sends the branch's commits to `main` and leaves the remote
branch `release/prep` uncreated. Do not re-run it. There is nothing left for it to carry, so it would
answer `Everything up-to-date` and move nothing.

## Step 2: HTTPS, with the credential prompt — Veer's half

Step 2 is the commits after `4430fb1`, and Veer runs it from his own terminal. The exact command,
with the credential helper turned off so that the prompt is the only source of the credential:

```bash
git -c credential.helper= push https://github.com/andy1245-rgb/ticketpath.git release/prep:main
```

It prompts twice. `Username` is `VeerCodes`. `Password` is a classic personal access token with
repository scope on `andy1245-rgb/ticketpath`, typed at the prompt. The token is never in the
command, never in the shell history, never in a file in this tree. Nothing here needs to hold it.

**The two steps do not send the same commits.** Step 1 sent the 11 that `4430fb1` names. Step 2 sends
the ones after it: `git rev-list --count 4430fb1..HEAD` → 13 at this tip. Step 2 is the push that
moves `main` to the branch tip.

If `main` has moved again since `4430fb1`, step 2 is refused as non-fast-forward. That refusal is
correct. Merge `origin/main` into `release/prep` and push again; do not force.

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

  **[Corrected 2026-11-08T12:00Z: the anchors were stale by 130 to 700 lines, not about 300, and this
  pass moved the later targets 43 lines rather than one. Measured by comparing the target in
  `records/STATE-OF-PROJECT.md` at `4430fb1` against `HEAD`: §A2's target moved from `:248` to
  `:257`, +9; every target at and below §A6 item 7 moved +43, so `:859` → `:902`, `:646` → `:689`,
  `:884` → `:927`, `:667` → `:710`, `:900` → `:943`. Against the anchors as written, the gap from an
  anchor to the text it means is 130 for the cluster table's `:127-133`, 290 for §A9's `:399-401`,
  310 for `:617` and `:617-620`, 308 for `:402-404`, 310 for `:633-635`, and 701 for `:201` at `:799`.
  One anchor, `:621`, lands on its text. They are another owner's and are left
alone here.]**
- **Feature 5's row in `records/STATE-OF-PROJECT.md` still reads "not built"** while the artist
  fee is built and finding 42 measures it. The shared checkout wrote it that way and added a
  closing section that says the row is stale. Moving the row is a status decision, not a fix.

  **[Corrected 2026-11-08T12:00Z: the row was moved on this pass, with the operator's decision, and
  now reads `built` and names `market_swarm/artist_fee.py` and `records/findings/42-artist-fee-at-checkout.md`.
  The old wording is kept in a dated note under the table.]**

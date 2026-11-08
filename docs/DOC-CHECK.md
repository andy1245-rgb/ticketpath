# The documentation consistency check

`tools/doc_check.py` fails when a document in this repository disagrees with the code, or
with another document. It is a gate, not a report: one violation and it exits 1.

    python3 tools/doc_check.py                  # every tracked markdown file
    python3 tools/doc_check.py --check paths    # one check, while writing a document
    python3 tools/tp.py doc-check               # the same thing, as a verb of the CLI
    python3 tools/tp.py gate --quick            # the commit gate: tests, then this

Exit codes: `0` clean, `1` at least one violation, `2` the tree could not be read (a file
a check must read is missing, so no claim could be tested). Violations print one per line
as `path:line: check: claim`, the shape `tools/public_safety.py` uses.

## Why this exists

The research record is the deliverable here, and it is written by the same agents that
change the code. That is how a document comes to describe nine instructions for a program
that implements four, name a tool that was renamed two passes ago, or quote a program id
that the devnet artefact no longer carries. None of those is a typo. Each is a claim a
reader will check and find false, and the record's whole value is that its claims hold.

## What it checks, and why each one is checkable

A check earns its place by being decidable from the tree: no judgement, no network, no
number that moves on its own.

| Check | The claim it tests | Why it is decidable |
|---|---|---|
| `paths` | every repo path a tracked `.md` names in backticks or as a link target exists | the path is a string and the filesystem answers yes or no |
| `cross-references` | `records/findings/NN…` resolves to a file; every `§N.M` in `docs/ON-CHAIN-DESIGN.md` resolves to a heading or a numbered item in that same file; every `D<n>`/`Q<n>` has a heading in `records/F-decision-log.md` | three sets and three lookups: the findings directory, the heading numbers, the log's headings |
| `ids` | the memo program ids quoted in `README.md` and `docs/ON-CHAIN-DESIGN.md` are literals under a `MEMO_` name in `ticketpath/adapters/chain_client.py`, **and each id on a line naming a cluster is the id `MEMO_PROGRAMS` maps that cluster to**; the program id and mint quoted in `README.md` and `records/STATE-OF-PROJECT.md` are the ones in `records/devnet-artefacts.json` | both sides are literals in the tree, so equality is a comparison and not an opinion; the cluster words and the ids are read off the same line, so the direction of the claim is checked and not only its vocabulary |
| `program-vs-doc` | the error numbers in `TicketpathError`, the instruction tags in `HookInstruction` and the seed literals of `pub fn *_seeds` equal the "implemented today" table in `docs/ON-CHAIN-DESIGN.md`, both ways | the sets are parsed out of the Rust and out of the table, and compared as sets |
| `registry-counts` | a registry that states a count of its own rows is stating the number of rows present | the claim names its scope (`Count: 27 sources`, `33 variable rows (13 in §8.1, …)`), and the rows are counted in that scope |
| `feature-table` | every row of the feature table in `records/STATE-OF-PROJECT.md` names an existing file and carries a status from the closed set; a `tested` row names an existing test file | the status is a word from four, the file is a path, and the filesystem answers |
| `findings-unique` | a reference to `records/findings/NN` (or to `NN-a`) that lands on more than one file is a violation; a number with several claimants is reported as a warning on every run | whether a number is shared is a property of the directory listing, and whether a *reference* is ambiguous is a count: the names a reader following it could land in |

**Ambiguity fails. A shared number warns, and here is why that split matters.** Two sessions
allocating numbers concurrently wrote four different findings under `34`, and `README.md`, the
decision log and the ledger then pointed at `34` and read as correct whichever one they meant,
because `cross-references` can only ask whether *some* file at that number exists. That is the
defect, and it is a reference with a wrong answer, so a bare reference to a shared number is a
violation naming the reference and every claimant.

The number itself is not the defect. `00` (four files) and `02` (two unsuffixed files beside
`02-a` to `02-e`) pre-date both sessions, were written by one hand under the convention then in
use, and would have to be renamed to make a stricter rule pass. A check that can only go green
by rewriting the operator's existing record does more damage than the defect it catches, so a
number with several claimants prints one warning line per number on every run -- the number, the
count and the claimants -- and the run stays green. The commitment to the 33 and 34 collision
stays visible; nothing has to be rewritten to satisfy a tool; the operator decides which side is
renumbered.

The convention a clean group uses is already in the tree: `01-a`, `01-b`, `01-c`, `01-d` are
four findings under one number, each unambiguous, and the warning says so rather than implying a
problem.

The two tables it reads have an exact format, and it is specified in the module docstring
of `tools/doc_check.py` beside the parser that enforces it: an "implemented today" table
headed `| kind | name | value | where |` under a heading that mentions implementation, and
a feature table with a name column, a status column and an evidence column. A document
that omits either one gets one line naming the missing table, not a crash and not a pass.

## An absent path: written down, or red

Some of the record legitimately names files that are not in the tree: a planning document
calls a script by the name it had before it shipped, a finding number was assigned and the
file was never written, a handover sheet is kept out of git on purpose. Each of those would
otherwise be a permanently red gate, and a permanently red gate gets switched off.

There are two mechanisms, and the difference between them is who owns the decision.
`.gitignore` owns the paths the repository deliberately has on purpose and does not carry,
and `ALLOWED_ABSENCES` owns the paths the tree will never have.

### `.gitignore`: the tree has it, the repository does not carry it

The record cites a local-validator artefact, a report page, a program's build output. They
exist in the checkout that produced them and in no clone, and `.gitignore` already says so,
because that is the file whose job it is. A path an ignore rule matches is not a claim about
the tree: it is a document describing the run, and the run wrote a local file.

So the checker asks git, in one batch for the whole run, with
`git check-ignore --no-index --stdin -z` over the absent paths it collected. Forty absent
paths cost one subprocess. `--no-index` because the ignore rules are the question and the
index is not. The run counts what it skipped and `--verbose` names each one beside the
document and line that named it.

Where git cannot answer -- no git on `PATH`, no work tree, a return code that is neither
"some are ignored" nor "none is" -- every absent path is judged by whether it is on disk,
exactly as before. That is the safe way round on purpose: a machine without git reports
more violations than one with it, never fewer, so a green run never means a check that
stopped asking. It also means the pass has to be earned: a document naming a path that is
neither present nor ignored is still red.

### `ALLOWED_ABSENCES`: the path will never be in the tree

`tools/doc_check.py` carries an `ALLOWED_ABSENCES` table: one entry per path, each with a
reason a reader can check against the tree in a minute. The rules are the ones
`.public-denylist` already uses for its exceptions, because a second dialect for the same
idea is how a tree ends up with two ideas:

- **A reason is mandatory and has to be arguable.** An entry with no reason, or with a reason
  under four words, is itself a violation, and it suppresses nothing: the path it names is
  still reported as absent.
- **An entry suppresses one thing: the absence of that exact path.** It cannot quiet an id, a
  cross-reference, a registry count or a feature row. Those are other claims with other
  evidence, and a path allowance that also covered a stale id would be a lie by proxy.
- **The number is reported.** Every run says `N allowed absence(s) suppressed by
  ALLOWED_ABSENCES` and `N git-ignored path(s) not claimed of the tree`, and `--verbose`
  names each one, so the quiet part is on the record and not in somebody's memory.
- **Everything else still fails.** A document naming a path that is present, ignored and
  written down in neither place is a violation, and the fix is a document that says the file
  is local, or a file.

Adding an entry is a decision about what the record is allowed to claim, so it goes in a
commit with its reason, where a reviewer reads it beside the diff. Do not add an entry for a
path `.gitignore` already covers: two mechanisms for one fact is how one of them goes stale.

## What it deliberately does not check

A checker that hides its limits teaches a reader to trust the wrong thing.

- **Prose truth.** No program can read "the cap is fixed at event creation" and know
  whether the program does that. Only the two tables are machine-read claims.
- **The word "nine".** A design document may describe a nine-instruction program while the
  code implements four: that is what a design document is for. What a document may not do
  is *tabulate* the four and get one wrong. The table is the claim, and the table is what
  is checked.
- **Counts of hits, test totals, line counts, hashes.** They move every time anyone runs
  anything. A gate that fails because a test count changed is a gate that gets switched
  off within a day.
- **Paths with a glob, a `<placeholder>`, a URL, a `~`, or a leading `..`.** They are not
  claims about this tree. `../ticketing-frontend/lib/types.ts` is the sibling checkout and
  this checker will not pretend to know whether it is on the machine.
- **Bare filenames and bare finding numbers.** `README.md` is ambiguous across forty
  directories, and `records/findings/28` belongs to `cross-references`, which resolves it
  against the findings directory properly.
- **A reference the sentence itself calls absent.** `records/findings/22` does not exist,
  and a document saying so is being honest. Likewise a `§`/`D`/`Q` reference whose
  paragraph names another document: `03-b` Q6 is 03-b's question, not this log's.
- **Git history, the network, and anything written.** It reads files and runs one
  `git ls-files`, and it writes nothing, so it is safe inside a commit hook.

## How it is wired

- `python3 tools/tp.py doc-check` runs it as a child, bounded at 120s.
- `python3 tools/tp.py gate --quick` runs it as a gate position, after the unit tests and
  before the console checks, in both `--quick` and full modes. The summary line carries
  `doc-check=N violation(s)` beside `tests=…` and `console-check …`, so the shape of the
  gate's output is unchanged.
- `.githooks/pre-commit` runs `gate --quick` when a staged path is code, so a code commit
  cannot leave a document naming a file the tree no longer has. It also runs
  `python3 tools/tp.py doc-check` directly when a staged path is markdown under `docs/` or
  `records/`, or is `README.md`, and no code is staged: a markdown commit is the one commit
  that can break the documentation, so it is the one that must not skip the check. That
  command binds no port and takes about a second, which is why it can run where the twenty
  second suite cannot. A code commit does not run it twice, because the quick gate runs the
  same check inside itself.

## How to add a check

1. Name it in `CHECKS` in `tools/doc_check.py`, where the order of the tuple is the order
   violations print.
2. Write `check_<name>(root, files)` (or `check_<name>(root)` if it reads one named file)
   returning a list of `Violation`, each carrying the check name, the file, the 1-based
   line and the claim in one sentence a person can act on.
3. Call it from `check_tree` under its name, so `--check <name>` selects it.
4. Prove it can fail in `tests/test_doc_check.py`: a fixture with the smallest possible
   lie that the check must catch, and the same fixture unchanged among the clean-tree
   tests. A check with no failing case is not a check, and one with no passing case will
   be found to flag everything.

House rules, because the file is read by whoever adds the next check: standard library
only; no network module imported anywhere; bounded, so a repository five times this size
still finishes inside a second; and every skip written in a comment beside the code that
skips, with the reason, because a silent skip is indistinguishable from a pass.

## Two follow-ups this file does not do itself

- The `ALLOWED_ABSENCES` reasons are the doc steward's to keep true: if one of those files is
  written after all, its entry should go, and the check will say nothing about it either way.
  A reason that has stopped being true is worse than no entry, because it reads as a decision
  somebody checked.
- The violations the check finds in the documents today are content, not checker bugs.
  They are listed in `tmp/doc-check-baseline.md` for the doc steward, which is where the
  fixing happens; this checker will keep failing until that pass lands, and that is what a
  gate is for.

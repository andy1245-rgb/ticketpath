# `tools/tp.py`: the backend from a terminal, and the gate a commit passes

One file, standard library only, no import of `ticketpath` into the caller's process. Every
route that has a reader in a browser has a verb here, so the whole backend can be driven,
read and batch-tested from a shell. `docs/BACKEND.md` says how to start the server; this
says how to use it once it is up, and how the same file guards a commit.

```bash
python3 tools/tp.py health
python3 tools/tp.py --json events --limit 3
```

Global flags are accepted before or after the verb: `--base URL` (default
`http://127.0.0.1:8788`), `--json` (one JSON document instead of one line per fact), and
`--timeout SECONDS` (per request, default 15).

## The verbs

| verb | route it reads | what it prints |
|---|---|---|
| `health` | `GET /health` | service, data source, chain, pricing seam, contract counts |
| `events [--limit N] [--cursor C]` | `GET /api/events` | one line per event: status, dates, tier count, cap, issued/supply |
| `event <id>` | `GET /api/events/<id>` | the event, its venue, every tier with its face value |
| `tickets [--limit N] [--cursor C] [--event ID]` | `GET /api/tickets` | one line per ticket: serial, status, face, last sale, transfers |
| `history <ticketId>` | `GET /api/tickets/<id>/resale-history` | every ledger row, then the ticket's stats, then the custody note |
| `price <eventId> [--tier T] [--cap BPS] [--mode counterfactual\|before_on_sale] [--at ISO]` | `GET /?event=...` | the decision page as text |
| `page <path>` | whatever the path is | the page as a browser shows it: tags stripped, entities resolved, CSS and JS dropped |
| `sweep` | `/health`, then the checks | the four property checks, with the failures |
| `gate [--quick]` | an ephemeral server of this tree | the unit tests, the documentation check, and the console checks |
| `doc-check [--root DIR] [--check NAME] [--verbose]` | the tracked markdown of this tree | the documentation violations, one line each, and the count of allowed absences |

`price` exists because the guidance payload has exactly one HTTP surface in this tree: the
console page. `ticketpath/server.py` serves nine contract routes plus `/health` and `/`, and
`/` is the one that carries the guidance payload; every control is a query parameter, which
is what makes the page reproducible by URL. There is no `/api/guidance` route to forward, so
`price` builds the URL the page documents and prints the page. Its `--json` document carries
that URL, the status and the page's lines, with a note saying so, rather than a
reconstruction that could disagree with the page.

```bash
$ python3 tools/tp.py price evt_syn_02 --cap 298 --at 2026-11-07T12:00:00Z | head -2
[FIXTURE] price http://127.0.0.1:8788/?event=evt_syn_02&capBps=298&asOf=2026-11-07T12%3A00%3A00Z - 200 - 61 lines
[FIXTURE] SYNTHETIC FIXTURE DATA — every number on this page is computed from a synthetic fixture ...
```

## Provenance on every line

A line this CLI composes carries the badge its source earns: `[FIXTURE]` when the API says
`dataSource.synthetic` is true, `[DECLARED]` when the ledger is the declared-empty one, and
`[DESIGN]` for the chain and pricing-seam lines where the API reports nothing deployed. A
count of routes or of tests is `[EXACT]`, because counting them is arithmetic.

A rendered page keeps its own badges exactly where the server put them; a page line that
carries none gets the source badge in front, and one that already has a badge is never given
a second. No number is recomputed here: money is printed in the integer lamports the route
sent, and nothing is converted to SOL by this file.

## Exit codes

| code | meaning | what to do |
|---|---|---|
| 0 | the server answered and the answer is the product | nothing |
| 1 | a check failed, or the route answered 4xx/5xx with its refusal printed in full | read the refusal; it carries the API's message and typed code |
| 2 | usage: unknown verb, missing argument, a `--base` without `http://` | fix the command line |
| 3 | no HTTP answer | `python3 -m ticketpath.server` from the repository root; the line printed on stderr says the same thing with the base it tried |

A refusal is never stripped and never turned into an empty result: `event evt_nope` prints
`[REFUSED] 404 event evt_nope not found (code not_found)` and exits 1. A rendered error page
is printed in full and exits 1, because the page is the answer but the request was wrong.

## `sweep`

Runs the property checks the final audit left on the box, preferring the independent one
when it is there. The independent sweep takes the base URL as its argument and imports
nothing from this repository, so it cannot share a bug with the thing it checks. Its path is
configuration rather than source, because a scratch path in a published file is the
operator's machine:

```bash
TP_SWEEP=/path/to/sweep.py python3 tools/tp.py sweep
```

With `TP_SWEEP` unset, or naming a file that is not on the box, the optional sweep is
skipped and the CLI says so on its own line, then uses `tools/console-check.py` pointed at
`--base` through `TP_BASE`. Nothing is silently skipped: the line that prints which tool
ran is printed either way. Child output is printed verbatim, then one summary line carrying
the failure count either tool printed -- `FAILURES: N` from the checker, `violations: N` from
the sweep. If neither tool exists, that is a failed check (exit 1), not a pass.

Note that the independent sweep reads `fixtures/synthetic_store.json` from this repository as
its ground truth, so it belongs to this tree; pointing it at another checkout's server will
compare that server against this repository's fixture.

Lines quoted from a child tool -- the sweep's findings, a failing test's traceback -- are
printed verbatim or indented, not badged. They are another tool's report, and prefixing
`[FIXTURE]` to `ok   /?event=...` would claim a provenance the line does not carry. The
section header above them and the summary line below them carry the badge.

`TP_BASE` is the one change made outside new files: `tools/console-check.py` reads
`BASE = os.environ.get("TP_BASE", "http://127.0.0.1:8788")`, which keeps every existing
invocation on 8788 and lets the gate point it at an ephemeral port.
`tools/console-check-stores.py` needed nothing: it starts its own servers and has no base
address to override.

## `gate`: what a commit runs

```bash
python3 tools/tp.py gate            # the full gate, under 4 minutes
python3 tools/tp.py gate --quick    # unit tests only, no server, under 60s
```

The full gate:

1. picks a free port that is not 8788, 8787, 3000 or 3001, and starts `python3 -m
   ticketpath.server` from this working tree on it;
2. waits for `/health` (20s bound) and prints the source the server reported;
3. runs `python3 -m unittest discover -s tests` (150s bound);
4. if those pass, runs `tools/doc_check.py` (120s bound): the documentation consistency
   check, which is one line per violation and no server;
5. if that passes, runs `tools/console-check.py` against that server through `TP_BASE` (60s
   bound);
6. kills the server on every exit path -- pass, failure, timeout, exception -- deletes its
   log, and prints one summary line.

```
[EXACT] gate server http://127.0.0.1:41317 (working tree, <checkout>)
[FIXTURE] SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
[FIXTURE] unittest: OK - 453 tests
[FIXTURE] doc-check: 0 violation(s)
[FIXTURE] console-check: 113 ok, 0 failed, FAILURES: 0
[FIXTURE] gate ok - tests=453 OK - doc-check=0 violation(s) - console-check FAILURES: 0 - wall=18.3s
```

`<checkout>` is the absolute path of the clone the gate is running in, which it prints in
full so a log says which tree answered; it is elided here, because this page is public and a
machine's layout is not evidence for anything.

Two decisions worth knowing. The unit tests run with `TICKETPATH_PORT` removed from the
child's environment, because `tests/test_boundaries.py` pins `resolve_port()` to the
documented default of 8788 and that assertion is only true when the variable is unset; the
gate hands its own server the port with the explicit `--port` flag, which wins over the
environment anyway. And `--quick` starts no server at all: a pre-commit hook may not wait on
a page render, and the unit tests already bind their own ephemeral servers. `--quick` still
runs steps 3 and 4, so a code commit cannot leave a document naming a file the tree has
lost; the documentation check costs about a second, and its violations are printed in full
under the summary.

Exit codes: 0 every step passed, 1 a step failed or exceeded its bound, 3 the gate's own
ephemeral server never answered `/health` (its log tail is printed, and this is a broken
tree rather than a broken command line).

## Pairing with a commit

`.githooks/pre-commit` does three things, in this order:

1. **Refuses anything that may not be published.** One line, and it is the whole wiring:

   ```bash
   python3 tools/public_safety.py check --staged || exit 1
   ```

   It reads the index, not the worktree, so a file staged and then deleted from disk is
   still caught, and the rule list it reads is `.public-denylist`, which is not part of this
   file. `docs/PUBLIC-SAFETY.md` is the account of every class and why it is denied. The
   hook deliberately says nothing of its own here: the checker prints each hit as
   `path:line: class: what` and the last line says whether the commit may proceed. A hit in
   `records/` is the run's evidence and therefore the operator's call, not a cleanup.
2. **Refuses a credential.** A staged path named `.env`, `*.env`, `*.pem`, `*.key`, `*.p12`,
   `*.keystore`, `id_rsa*`, `id_ed25519*`, `*credentials.json` or `*service-account*.json` is
   refused by name. So is a staged file whose content matches a private-key block, an
   `sk-ant-` key, a GitHub `ghp_`/`github_pat_` token, a Slack `xox?-` token, an `AKIA` key,
   a Google `AIza` key, or an assignment to `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY`.
   The hook prints the path and the class of match, never the matched text.
   This step overlaps the first one on purpose and is not redundant: `.keystore`,
   `*credentials.json`, `*service-account*.json` and the `AIza` shape are not in the
   denylist, and a credential check that depends on a data file having listed the shape is
   a weaker promise than one that also knows them itself. The classes they share -- `.env`,
   `*.pem`, `*.key`, the SSH key names, a PEM block -- are caught by step 1 first.
3. **Runs the quick gate** when a staged path is under `ticketpath/`, `tests/` or `tools/`.
   A docs-only commit does not run the suite: one that blocks on a 20-second suite is a hook
   people learn to bypass, and a bypassed hook is worse than a narrow one. Markdown is the
   next step, which is cheap enough to afford.
4. **Runs the documentation check** when a staged path is markdown under `docs/` or
   `records/`, or is `README.md`, and no code is staged. That is the one commit that can break
   the documentation, so it is the one commit that must not skip the check; the command is
   `python3 tools/tp.py doc-check`, which binds no port and takes about a second, so the
   argument for a narrow hook does not apply. A code commit does not run this step twice: the
   quick gate in step 3 runs the same check inside itself.

```bash
tools/install-hooks.sh     # once per clone: git config --local core.hooksPath .githooks
```

`install-hooks.sh` is idempotent, prints what it did, and touches only the clone it sits in --
`core.hooksPath` is local configuration, never committed, so a fresh clone needs one run.

Each of those steps has a test that plants the thing it refuses in a scratch clone and reads
the exit code git returned: a `NIGHT-FOO.md` and a file holding an absolute home path are
both refused by the hook as it stands, and a control run with the checker's line removed
commits the same `NIGHT-FOO.md`, which is what shows the refusal is the wiring and not
something else.

**Bypass policy: never `git commit --no-verify`.** The hook exists because a red suite or a
key in the tree is cheaper to catch here than anywhere after. The only person who may bypass
it is the operator, deliberately, and the commit message should say why. A hook failure is
fixed, not skipped; if the hook is wrong, fix the hook in the same commit as the reason.

## What this file does not do

It does not decide anything: no op, no write, no state. It reads routes and runs the tests
that already exist. It does not recompute a number, convert a unit, or re-render a refusal as
a success. It does not touch `ticketpath/`, the frontend, or a port other than the ephemeral
one the gate picks.

## Looking at a page instead of reading it

`tp.py page` strips a route down to its text. When the question is what the page looks like
-- layout, something clipped, a badge that should be visible -- use `tools/shot.py` instead:
it drives a headless browser kept outside this repository and writes a PNG. See `docs/SHOTS.md`
for the flags, the exit codes and what is installed.

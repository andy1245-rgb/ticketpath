# REPO-CONSISTENCY — the pass that made the records match the tree

**Written:** 2026-11-07T12:11Z, last touched 12:14Z, by the consistency-editor session, from its
own command output.
**Scope:** every file a submission reader may open — `README.md`, `ticketpath/`, `docs/`,
`records/`, `tests/`, `tools/` — checked against the system that actually runs, not against the
records. `ticketpath/console/` and the frontend were not touched: another session was editing
the console during this pass and the frontend is not ours to edit at all.

**Rule this pass followed:** no computed number, estimator or refusal was changed. Where a
record states a number that has moved, the record gained a dated note and the number stayed.

---

## 1. What was changed, and how to see it

Each row is one change, the command that shows it, and its output at the time of this pass.

| # | Change | Evidence |
|---|---|---|
| 1 | `/health`'s `pricingModel` block now says what the seam actually holds: `kind: rule-based-bounded-estimator`, `fitted: false`, and a `note` saying there is no fitted model behind it. Set in `PricingModelAdapter.register`/`status` (`ticketpath/adapters/pricing_model_adapter.py`) and passed from `ticketpath/server.py::build_orchestrator`. | `python3 -m ticketpath.server --port 8791 &` then `curl -s http://127.0.0.1:8791/health \| python3 -m json.tool` → the block in §2 |
| 2 | `chain.designDoc` points at `docs/ON-CHAIN-DESIGN.md` instead of the superseded pointer. Set in `ticketpath/adapters/rpc_adapter.py::program_status`. | same call → `"designDoc": "docs/ON-CHAIN-DESIGN.md"` |
| 3 | Four records annotated as snapshots, not rewritten: `DEMO-PROOF.md`, `SUBMISSION-PACK.md`, `FRONTEND-INTEGRATION.md`, `BUILD-SPEC-NIGHT.md`. Each ends with a dated table of what asserts what it used to, what is true now, and the command that shows it. | `tail -20 records/DEMO-PROOF.md` etc. |
| 4 | `records/DELIVERABLE.md` created as a stub marked **NOT WRITTEN YET**, with the programme's 22 required sections, where each one's material lives today, and whether it is written. **The stub was the option chosen** over amending `records/README.md` to say pending, because a pointer that resolves to an honest stub is better than a pointer that resolves to nothing. `records/README.md` gained four words identifying it as a stub, so the promise and the file agree. | `head -6 records/DELIVERABLE.md`; `sed -n '28,36p' records/README.md` |
| 5 | Absolute personal paths replaced with repository-relative ones in every judge-facing file. Inside the repo the root is `.`; the sibling checkouts are `../ticketing-frontend`, `../ticketpath-demo`, `../research/…`. 23 files under `records/`, 3 under `docs/`, plus `tests/test_contract_conformance.py`. `NIGHT-LOG.md`, `NIGHT-QUEUE.md`, `NIGHT-BRIEF.md` untouched by instruction. | `grep -rn "hom[e]/" README.md records docs tests tools ticketpath` → zero hits in those trees. `AGENTS.md`, which that command does not scan, still carries one (§3) |
| 6 | `docs/BACKEND.md` quotes the startup banner the server prints now, captured from a running instance, two lines, including the `Generated for tests and demonstration` label instead of the old `Hand-authored for tests`. | `python3 -m ticketpath.server --port 8791` → the two lines quoted in `docs/BACKEND.md` `## Start` |
| 7 | `pyproject.toml` added: `requires-python = ">=3.12"`, package `ticketpath`, `dependencies = []`, and no `[build-system]` because nothing is built or installed. | `python3 -c "import tomllib;d=tomllib.load(open('pyproject.toml','rb'));print(d['project']['requires-python'], d['project']['dependencies'], 'build-system' in d)"` → `>=3.12 [] False` |
| 8 | `LICENSE` untouched. The README's licence section now states, in a quoted block, the exact placeholder line and that the operator must replace it. | `grep -n -A6 'Licence and status' README.md`; `head -3 LICENSE` |
| 9 | Claims corrected where they were false against the running system, in files that are not snapshot records: `docs/BACKEND.md` (banner, model-seam sentence, test count, sample curl's ticket id, layout table, on-chain pointer), `docs/RUN.md` (path, `designDoc`, `fitted`), `docs/ON-CHAIN-DESIGN.md` (`FXTURE` → `SYN` placeholders, frontend path), `records/CONTRACT-MAP.md` (hand-authored → generated, model seam state, test count, three `ON-CHAIN-FOR-LAPTOP` pointers), `records/FIXTURE-STORE.md` (the `/health` refusal sentence), `README.md` (the health claim, the design-doc pointer, the test count removed rather than re-pinned, sixteen → seventeen findings, console size an order of magnitude instead of a byte count, licence line), `ticketpath/orchestrator.py` and `ticketpath/onchain/sim.py` (docstrings only, no logic). | the grep sweeps in §4 |
| 10 | The two new health assertions are pinned by a test, not by a curl: `tests/test_http_contract.py::TestHealth` now checks `kind`, `fitted`, the `note` and `chain.designDoc`, and that test wires the model the same way the server does — from one `ENGINE_DESCRIPTION` in `ticketpath/server.py`, so they cannot drift. | `python3 -m unittest tests.test_http_contract -v` |
| 11 | Full suite run five times during the pass. It read **293 tests, OK** at 12:04Z and **306 tests, OK** at 12:12Z, because another session was adding console tests meanwhile; the last run was after the last edit, with that session's `tests/test_console_presentation.py` and `ticketpath/core/labels.py` in the tree. No count is quoted as current anywhere this pass touched. | `python3 -m unittest discover -s tests` → `Ran 306 tests`, `OK` |

## 2. `/health`, before and after

**Before** — `ticketpath/server.py` as it stood, captured from an instance started at 11:59Z on
port 8899:

```json
"chain": {
  "programDeployed": false, "rpcEnabled": false, "programId": null,
  "cluster": "devnet", "reason": "rpc_disabled",
  "designDoc": "docs/ON-CHAIN-FOR-LAPTOP.md"
},
"pricingModel": { "available": true, "modelVersion": "engine-2026-11-07", "reason": "registered" }
```

**After** — the same call on port 8903 against this commit (unchanged keys elided):

```json
"chain": {
  "programDeployed": false, "rpcEnabled": false, "programId": null,
  "cluster": "devnet", "reason": "rpc_disabled",
  "designDoc": "docs/ON-CHAIN-DESIGN.md"
},
"pricingModel": {
  "available": true,
  "modelVersion": "engine-2026-11-07",
  "reason": "registered",
  "kind": "rule-based-bounded-estimator",
  "fitted": false,
  "note": "The engine seam is populated by a rule-based bounded estimator with no fitted model behind it. The number is bounded arithmetic over the recorded resale trail, computed by ticketpath.core; nothing was trained, calibrated or validated against real ticket data."
}
```

**One correction to the brief that this pass found.** The contradiction was not
`available: false`. By the time this pass started, `server.py` already registered the engine, so
the running system answered `available: true` with `reason: "registered"` — which is true and
uninformative, and it is what let four records go on saying "no model" while the console printed
a price. The block now carries the missing distinction between *populated* and *fitted*. The
`available: false` refusal is unchanged and still returned by a bare adapter, which is what
`tools/guidance.py` and the unit tests instantiate.

## 3. What could not be fixed

**The live port on :8788 was stale for the length of this pass, and stopped being stale at
12:13Z.** At 12:02Z that process (pid 255762, started 11:58:06Z) still answered the old payload:
`"designDoc": "docs/ON-CHAIN-FOR-LAPTOP.md"` and a `pricingModel` with no `kind` and no
`fitted`. A process started before a source change holds the old code, and it is not mine to
restart. A concurrent session restarted it while this pass was writing up: at 12:13Z `curl
http://127.0.0.1:8788/health` (new pid 263482) returns `docs/ON-CHAIN-DESIGN.md` and the block in
§2. The agreement between tree and live system therefore holds — but only because of a restart,
which is why the after payload is quoted from a port this pass started itself and not from the
one that happened to be running.

**The one contradiction that remains** is an instruction rather than a fact:
`records/SUBMISSION-PACK.md` §1.2, the variant A video script, tells the operator to scroll to
the `/health` line and leaves `"available": false, "modelVersion": null` and the sentence "no
price is served" in frame. Recorded today, that script puts a false statement about the running
system into the submission video. The snapshot note at the end of that file records what changed,
and §1.3's variant B is the script that matches the build, but the variant A text was left alone:
it is the operator's submission script and which variant he records is his call, not a consistency
edit.

Everything else that still reads stale, and why it was left:

| Where | What | Why it stands |
|---|---|---|
| `records/findings/*.md` | "149 tests, FAILED (failures=5)" at 11:47Z, the pre-regeneration counts, `FXTURE` addresses | Findings are the append-only primary record (`records/README.md`); they are dated observations of a moment, and rewriting one would destroy the trail the six records index |
| `records/FRONTEND-HONESTY-PATCH.md` §"On our backend the rendered sentence is" | quotes the old `Hand-authored for tests` label; the store is generated and the label now says `Generated for tests and demonstration` | the record documents what the patched screen showed at 11:25Z and carries the patch's sha256 in three places; editing it would invalidate a recorded hash |
| `records/D-model-registry.md` §"Inputs absent from disk when this file was written" | `02-b-cap-truncation.md: does not exist` | the list is explicitly what was absent at 11:10Z. `02-b` landed at 11:30Z and is adopted in the research ledger; the sentence is true of its own date |
| `records/BUILD-SPEC-NIGHT.md` §0 | `03-a-interactions.md does not exist at 11:40Z` | same: it says `at 11:40Z`, and the snapshot note at the end of that file covers the file as a whole |
| `records/00-data-situation.md` | "Backend: None" | the Phase 0 audit, `Last updated 08:40Z`, gating the estimators. It is a record of what existed then; the backend is a later phase |
| `records/CONTRACT-CONFORMANCE.md`, `records/BUILD-REPORT-CONSOLE.md`, `records/findings/06-validation-protocol.md` | test counts from their own runs (`22 tests` for the one module, `293`, `149`) | dated per-file. Where this pass touched a live count it removed the number rather than pinning a moving one: `README.md`, `docs/RUN.md`, `docs/BACKEND.md` and `records/CONTRACT-MAP.md` now say to read the command's own last line |
| `README.md` "What works today" | "today the honest output is a refusal naming the missing observation" | true of sale probability and the interior optimum, and it reads as covering the recommended price as well. It is the operator's own framing of the product, not a number, and rewording it is his call |
| `AGENTS.md` | one absolute path, `../ticketing-frontend` not yet applied | his standing brief for agents, outside the set he named for item 5 and outside the judge-facing set for the final sweep. Flagged here rather than edited |
| `ticketpath/core/labels.py`, `ticketpath/console/`, `tests/test_console_presentation.py` | edited and added by another session during this pass | not mine to touch. The suite was green against that tree at 12:12Z, at 306 tests |

## 4. The sweep, and what it found

```bash
grep -rn "hom[e]/" README.md records docs tests tools ticketpath   # personal paths
grep -rn "149 test\|100 tests\|292 test" README.md docs records tests tools ticketpath
grep -rn "two events\|five tickets\|evt_fixture\|tkt_fixture\|FXTURE" README.md docs records tests tools ticketpath
grep -rn "no_model_registered\|available: false" README.md docs records tools ticketpath
grep -rn "ON-CHAIN-FOR-LAPTOP" README.md docs records tools ticketpath
grep -rn "does not exist\|not built\|missing" README.md docs records
```

Every hit that described the running system was either fixed, annotated, or listed in §3. The
remaining hits are quotations of dated observations, or they are true: the refusal path still
returns `available: false, basis: "no_model_registered"` when nothing is registered, and that is
the only honest thing for it to return.

**Anything asserted here can be re-checked with the commands in the rows.** The two that matter
most, in one block:

```bash
python3 -m ticketpath.server --port 8791 &        # any free port; 8788 may already be serving
curl -s http://127.0.0.1:8791/health | python3 -m json.tool
curl -s http://127.0.0.1:8791/ | sed 's/<[^>]*>/ /g' | grep -o 'at least [0-9.]* SOL'
python3 -m unittest discover -s tests
```

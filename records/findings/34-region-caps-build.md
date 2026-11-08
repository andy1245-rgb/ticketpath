# 34 — Region-aware resale caps: build and verification record

**Written:** 2026-11-08, by the session that built it. **Status vocabulary:** *built* = the code
exists in the tree at the path named; *tested* = a named command was run and its output quoted, on a
named surface; *unverified* = stated where it is, and what would verify it.

---

## 1. Built

| # | What | Path | Status |
|---|---|---|---|
| 1 | The legal basis, primary sources, five clusters | `records/findings/33-a-region-cap-law.md` + `records/findings/33-b-region-cap-law-sources/` | built |
| 2 | The rules table: 82 codes, 84 instruments, version, hash | `ticketpath/data/region-caps.json` | built |
| 3 | The resolver: three policies, base semantics, date rules, multi-venue, effective ceiling | `ticketpath/core/region_caps.py` | built |
| 4 | The event field and seven additive wire keys | `ticketpath/core/event_records.py`; store field in `tools/build_fixture_store.py` and `fixtures/synthetic_store.json`; declared in `tests/test_contract_conformance.py` | built |
| 5 | The harness adapter: draft config → loader config + `.law.json` sidecar | `tools/region_harness.py` | built |
| 6 | The on-chain policy layer: record fields, three policies, monotone tighten, hook branch | `programs/region_gate/` (new crate; **not** `cap_hook`, **not** deployed) | built |
| 7 | The local-validator proof | `tools/region_local_proof.py` | built |
| 8 | Tests | `tests/test_region_caps.py` (54), `tests/test_region_caps_table.py` (23), `tests/test_event_jurisdiction.py` (10), `tests/test_region_harness.py` (14), plus 8 Rust unit tests in the crate | built |
| 9 | Design and decision | `records/REGION-CAPS-DESIGN.md`, `records/F-decision-log.md` D11 (+ Q4 status) | built |
| 10 | Docs brought to match | `README.md`, `records/STATE-OF-PROJECT.md` §G, `docs/ON-CHAIN-DESIGN.md` §14, `records/CONTRACT-MAP.md` §7.9, `records/C-variable-registry.md` §9, `records/E-data-source-registry.md` S29, `records/A-research-ledger.md` R3-1 | built |

## 2. Tested, and on what surface

### 2.1 Python, in-process

```
$ python3 -m unittest tests.test_region_caps tests.test_region_caps_table \
    tests.test_event_jurisdiction tests.test_region_harness -q
Ran 101 tests in 0.16s
OK
```

The 101 tests include the properties that matter: basis points are never compared across bases; a
D- or E-grade row can never produce a cap; `none_identified` never resolves to `monitored`; an
announced instrument never binds; the chain ceiling equals the stricter rule's own ceiling exactly; and
the resolved harness config is accepted by `market_swarm.config.load_run_config` itself, so "the loader
takes it" is a call and not a claim.

### 2.2 The programme, on a real local validator

```
$ python3 tools/region_local_proof.py
PASS 11/11
```

Surface: `solana-test-validator 4.3.2`, a fresh ledger, the crate deployed to its own program id, real
transactions with their own signatures. The eleven legs and every signature are in
`records/findings/38-region-caps-local-validator.md`. The ones worth naming here:

- capped at the ceiling `1_100_000_000` admitted; `1_100_000_001` refused as a **failed transaction**
  carrying `6010`, with the program's own log line `region_gate: cap exceeded ...`;
- monitored at 3× the base admitted, log `region_gate: monitored jurisdiction=DE ...`;
- unresolved at 3× admitted, log `region_gate: unresolved jurisdiction=ZZ ...`;
- `TightenPolicy` 1000 → 500 landed and the new cap then bound (ceiling `1_050_000_000` admitted,
  `+1` refused); an upward tighten refused `6042`; monitored → capped allowed; a non-authority refused
  `6040`; a two-ticket transfer refused `6008`.

The first run reported `FAIL 9/11` for two legs whose only problem was that the tool had been written
against the error numbers in its brief (`6022`, `6024`) rather than the ones the crate assigns
(`6042`, `6040`). The tool now parses the enum out of the crate's source, and the report records both
numbers so a reader can see which side moved.

### 2.3 What was **not** run

- **The devnet program was not touched, redeployed or called.** This feature's on-chain half is
  local-only by design. `records/devnet-artefacts.json` still describes the v1 cap-only program.
- **The full suite is not green, and the failures are another agent's.** At 06:17Z,
  `python3 -m unittest discover -s tests -q` reported 834 tests with 148 failures and 3 errors, all in
  `test_guidance_api`, `test_labels` and the console tests. Those assert on
  `ticketpath/api/guidance.py` and `ticketpath/console/page.py`, which had been written two minutes
  earlier by the concurrent ten-feature build. This pass did not edit either file. The four new
  modules pass on their own, and so do `test_boundaries`, `test_fixture_store`,
  `test_contract_conformance` and `test_event_analytics`.
- **The EU member states were not established.** See §4.

## 3. What the tests would not catch

Stated because a green test is evidence of what was tested and nothing else.

1. **The law being wrong.** The table is the claim, and the tests check the table's shape and the
   resolver's arithmetic, not whether Ireland really says what s. 15 says. Only re-reading the
   instrument does that, and §8 of finding 33 is how.
2. **The base being mis-supplied at creation.** The chain cannot tell a face from an all-in price. A
   creation path that passes the face where the law counts the fees produces a base that is too low,
   which is *stricter* than the law and safe; one that passes a fee the buyer never paid is *looser*
   and unsafe. The event record keeps the split and the receipts, and no test can prove the numbers in
   it came from a real receipt.
3. **A side payment outside the product.** The chain bounds the price it is told; it cannot see a
   transfer of money that never goes through the mint. This is `D9`'s limit, unchanged.

## 4. Unverified, and what would verify it

| # | Unverified | What would verify it |
|---|---|---|
| 1 | FR, IT, ES, BE, PT (and DE, NL, PL, SE, DK, AT, CZ, HU, GR): cap, authorisation rule, or nothing | read each national instrument; the EU retry in flight is the first attempt, and its result belongs in a later table version |
| 2 | Which Irish venues/events are on the s. 14 register | the register on gov.ie, or the Minister's designation orders |
| 3 | Whether Ireland's s. 15 reaches a platform wholly outside the State | the Act's territorial wording plus the Department's guidance |
| 4 | Queensland's cap basis and penalties | a host that can decrypt the authorised PDF, or the Government Gazette |
| 5 | Whether New York's s. 25.29 reaches an independent reseller | Arts and Cultural Affairs Law ss. 25.09-25.25 |
| 6 | 22 US states, 10 Canadian provinces/territories, TAS/ACT/NT | one statute per jurisdiction, read |
| 7 | The programme behaving the same on devnet | a devnet deploy of a region-aware program, which this pass deliberately did not do |
| 8 | Whether a mid-event tightening binds tickets already sold | a legal question for the operator; the code makes it possible and does not decide it |
| 9 | The fee the first purchaser actually paid (Ontario, NSW, WA bases) | a fee field and its receipt in the event record; until then the base falls back to the face, which is stricter |

## 5. The collision, recorded

Another agent in this tree was building the ten-feature plan's program v2 in `programs/cap_hook/` at
the same time. It moved this feature's files into `tmp/abandoned-region-caps/` at 05:52Z; they were
restored immediately and nothing was lost. The technical overlap is feature 10 (`jurisdiction` and
`policy`, which v2's record already carries) and error numbers (v2 owns 6021-6028, so this crate uses
6040-6043). No file that agent was writing was edited by this pass: the harness integration is a
separate adapter rather than an edit to `market_swarm/config.py`, and the event field is served as an
additive key rather than a change to `lib/types.ts`. The full record is
`records/REGION-CAPS-DESIGN.md` §12.

## 6. Files this pass created or edited

Created: `ticketpath/core/region_caps.py`, `ticketpath/data/region-caps.json`, `tools/region_harness.py`,
`tools/region_local_proof.py`, `programs/region_gate/**`, `records/REGION-CAPS-DESIGN.md`,
`records/findings/33-a-region-cap-law.md`, `records/findings/33-b-region-cap-law-sources/`,
`records/findings/34-region-caps-build.md`, `tests/test_region_caps.py`,
`tests/test_region_caps_table.py`, `tests/test_event_jurisdiction.py`, `tests/test_region_harness.py`.

Edited: `ticketpath/core/event_records.py`, `tools/build_fixture_store.py`,
`fixtures/synthetic_store.json` (regenerated), `tests/test_contract_conformance.py` (declared the
additive keys), `tests/test_boundaries.py` (`dataclasses` added to the standard-library allowlist),
`README.md`, `records/STATE-OF-PROJECT.md`, `records/F-decision-log.md`, `docs/ON-CHAIN-DESIGN.md`,
`records/CONTRACT-MAP.md`, `records/C-variable-registry.md`, `records/E-data-source-registry.md`,
`records/A-research-ledger.md`.

**Nothing committed, nothing staged, nothing pushed.** No file outside this repository was touched.

## 7. The phase-1 review: what was fixed, and what is open

A non-builder reviewer found four blockers and fourteen majors against the findings, the table and the
resolver. The four blockers are fixed, with tests:

1. **Inheritance leaked a "no cap" across a border.** `US-OH` inherited the federal rows and reported
   `monitored`. `Table.rows_for` now inherits only a parent's `all_resale` rows, and every US state and
   DC has a row of its own. Test: `test_a_sectoral_federal_rule_does_not_answer_a_state_s_price_question`.
2. **Florida and Queensland read as "no cap" on the default path** because the designated-events gate
   ran before the "is the basis readable?" check. An unknown basis is now checked first; Florida's
   coverage is `enumerated_events`, not a ministerial designation. Tests: the two loop tests over
   `declared_event`.
3. **"Announced is not law" was not structural.** `announced_policy` may now only carry `announced` or
   `not_in_force` (refused at load) and is skipped by the resolver whatever its status says. A mutation
   that flips the UK row's status now fails `validate_table`.
4. **Ontario and Quebec over-claimed their bases.** Ontario carries `stricter_than_law: true` (the
   statute allows the resale side's fees; this table does not) and its split commencement is in the
   row's notes; Quebec's face-equals-announced-price reading is labelled as an assumption of the
   mapping.

Also fixed from the majors: the report's counts were stale and now match the table (82 codes, 84 rows)
with a test asserting them; New York's 2027 sunset is carried in `in_force_to`; Massachusetts moves to
`unknown` because only one section of the chapter was read; the Ontario quote now includes the clause
naming the platform; the EU paragraph now says plainly that no EU member state has a row; and the UK
row is an all-resale finding of no price cap, which is what lets the three nations inherit it.

**Open, and deliberately not fixed in this pass** (each is a real finding; none is hidden):

- The five cluster records' own JSON blocks still carry the pre-correction shapes (NSW as
  `face_plus_fees`, Florida as `absolute`, the dropped California Penal Code 346 row, New York's
  `in_force_to`). The table is the authority and the cluster files are evidence; the finding's §0.1
  says so. Editing an agent's evidence record to match a later table would hide the correction rather
  than make it.
- The NSW, SA and WA triggers are a **resale restriction in the ticket's own terms**, which
  `applies_to` cannot express. The engine therefore caps every NSW/SA/WA resale, including a ticket
  whose terms permit resale; that is stricter than the law and is not representable more precisely
  until the attribute exists on the event.
- An absolute-margin rule (Florida) **cannot be enforced by this engine at all**: there is no absolute
  field on the record and no predicate for one. `to_lamports` converts with an FX snapshot, but that
  path is not wired, so Florida is unresolved for good and the report says that rather than
  "unresolved until an FX snapshot is supplied".
- Quebec's base is an assumption (announced price = tier face). If a vendor announced something else,
  the base is wrong in the permissive direction.
- The cluster records could not be re-fetched by the reviewer for four of six spot-checks (AustLII,
  Ontario e-Laws and nysenate.gov are all behind walls). Those readings rest on the cluster record's
  own quote, which is why every row carries its URL and its quote.

### 7.1 The red-team's five, and what happened to each

A second non-builder agent attacked the design (`tmp/review/region-caps-redteam.md`). Five items, in
the order it ranked them:

1. **"Stop reporting `monitored` for a jurisdiction whose cap trigger is unknown."** Done. A
   designated-events rule now has three states, not two: `True` binds, `False` is a stated "not
   designated", and **absence is `unresolved`** with reason `designation_not_stated`. The old
   behaviour let an operator opt out of Ireland's or Victoria's cap by saying nothing. The event field
   and the harness pass the three-state value through rather than collapsing it with `bool()`.
2. **"Check the record PDA when the extra-metas list is created."** Implemented, measured, **reverted**.
   With the check in place the local proof fell from `PASS 11/11` to `FAIL 4/11`: admitted transfers
   stopped producing log lines and refusals stopped landing. The cause was not established inside this
   pass, and shipping an unverified change to the program that all eleven green legs depend on is worse
   than leaving a known hole documented. **Open, high priority.** The hole is real: a wrong record
   pubkey in the metas list is a permanent brick that no later transaction can repair.
3. **"Consume the staged price."** Implemented with (2) and reverted with it. **Open.** The defect is
   real: one `SetPendingPrice` covers every later transfer, so a monitored event can log a price that
   was not paid, and the record's `pending_price_lamports` is not a per-sale fact. The attempted fix
   was to register the record writable in the metas list and zero the field after an admitted transfer.
   The same caveat applies: it changed the on-chain behaviour of all eleven legs at once and the proof
   went red, so it is not in the tree.
4. **"Make `enforcedCap` per tier."** Done. `enforcedCapByTier` is always emitted, one entry per tier,
   and `enforcedCap` only when every tier resolves to the same ceiling. The old single number was wrong
   by the tier ratio (5x on the fixture's headline event), which matters because it is the number a
   mint would carry.
5. **"Stop letting a base change read as `unchanged`."** Done: `compare` returns `changed_base` when
   two capped policies differ in base, so a required tightening cannot be silently treated as a no-op.

The red team's separate point that **the cap is denominated in lamports while the law speaks in
currency** has no small fix and is left as the operator's decision; it is the same question as Florida
and the FX snapshot in §4 item 9.

### 7.2 Added after the second research pass (EU)

The retry established five member states: **Belgium** caps at zero markup over the definitive price
(face + fees, in force 2013-10-01, upheld by the Constitutional Court); **Spain** caps at 20% above the
box office but only for licensed resale outlets, so it is recorded with `applies_to: unknown` and
resolves to unresolved rather than capping every Spanish sale; **France** and **Italy** regulate the
channel (organiser authorisation, authorised resellers) and have no price element, so both are
monitored; **Portugal** is reported only and carries no claim. The table is now **82 codes and 84
instruments**. Germany, the Netherlands, Poland, Sweden, Denmark, Austria, Czechia, Hungary and Greece
remain unknown, and each says so.

### 7.3 Four overclaims the red team caught, and the correction

The red team's final pass named claims in this build's own documents that the code did not support.
Each is fixed rather than softened:

1. **The fee split did not exist.** §4 of the design and §14.2 of ON-CHAIN-DESIGN said the
   event record keeps `faceLamports`/`feeLamports` and that a test proves the base is
   face + fee. There is no such field and no such test: every `face_plus_fees` law runs with the
   base equal to the tier face, which is stricter than the law. Both paragraphs now say the gap is
   open, and this is the first thing to add.
2. **The README's strongest sentence was true of the wrong program.** "No instruction that changes
   it afterwards" is true of `cap_hook` and false of the region gate, which has a monotone
   `TightenPolicy`. The README now says which program the sentence is about.
3. **A wrong error number in the design's verification table** (`6022` for a tightening refusal,
   which is the v2 program's `E_BAND_UNSATISFIABLE`); it is `6042` and the table now says so.
4. **The table could not be read under a non-UTF-8 locale.** `load_table` used the locale
   encoding; it now passes `encoding="utf-8"` explicitly, which is what the red team measured
   failing under `LC_ALL=C`.

Two structural fixes went in with them: a row graded D or E can no longer bind a cap (the rule was
enforced only by a test, now by `_binding` itself), and the `enforcedCap` overclaim in
§14.3 is corrected by §7.2 above.


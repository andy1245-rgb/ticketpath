# Ticketpath

Ticketpath is a tool for the organizer of a live event who sets a primary ticket price and
then has no view of what the same seat changes hands for afterwards. It reads the platform's
own resale record and computes what that record supports: the markup on every recorded sale
measured against that ticket's own tier's face value, the custody path of a single ticket
with a price on each hop, the roll up an organizer needs (volume, median price, markup
distribution, where the tickets ended up), and a recommended primary price where the record
can carry one. It is not a marketplace: there is no listing, bid, buy or checkout path here,
none is served by the backend, and none is planned. Resale value, how it moves, and the
chance a ticket sells are specified rather than fitted, and today the honest output is a
refusal naming the missing observation, because nothing records what an unsold ticket asked.

## What works today

Measured 2026-11-07T11:54Z on this machine, Python 3.12.3, standard library only. Run
every command from the repository root.

**Start the backend.** It binds `127.0.0.1:8788`; `TICKETPATH_PORT` overrides, and 8787 is
refused because another process owns it.

```bash
python3 -m ticketpath.server
```

Observed on an instance bound to 8793, because 8788 was already serving on this machine:

```
ticketpath 0.1.0 listening on http://127.0.0.1:8793 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
  SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.
```

**Open the console page.** The backend serves one server rendered HTML page at `/`.

```bash
curl -s -o /dev/null -w '%{http_code} %{size_download}\n' http://127.0.0.1:8788/
```

Observed `200`, and a page of about 13 KB. The status code is the invariant; the byte count
moves whenever the console is edited, so it is not quoted to the byte here. The page opens
with a banner saying every number is computed from a synthetic fixture and no program is
deployed, then lists all eight events with the pricing regime each is in. It shows the
evidence counts behind the decision, then the decision or a refusal. On the default selection
it prints a recommended primary price of at least 1.38 SOL
per ticket tagged `[UNVALIDATED]`, and says that is a floor, not an estimate, with no upper
bound stated. `?sim=1` runs the simulated state machine: five lines, including a transfer a
lamport above the cap refused with 6010 and an unstaged move refused with 6009.

**Query the API.**

```bash
curl -s 'http://127.0.0.1:8788/api/events?limit=100'   # 8 events
curl -s 'http://127.0.0.1:8788/api/tickets?limit=200'  # 76 tickets
curl -s 'http://127.0.0.1:8788/health'
```

Observed 8 events, 76 tickets, 9 of 9 contract endpoints over 10 routes,
`dataSource.synthetic: true`, `chain.programDeployed: false`, `chain.programId: null`, and
`pricingModel.available: true` with `modelVersion: engine-2026-11-07`, `kind:
rule-based-bounded-estimator` and `fitted: false`. The analytics route for
`evt_syn_02` returns volume, sale count, average markup, median price, resold share, holders
and a daily series. Wallet verification is the one real cryptographic operation: the
challenge endpoint returned a nonce, and an Ed25519 signature is checked against the public
key it is given. The console and `/health` now tell one story: the number the console prints
is bounded arithmetic over fixture prices, and `/health` says the same thing in the model
block, naming no fitted model because there is none.

**Run the tests.**

```bash
python3 -m unittest discover -s tests
```

Observed at 18:11Z: `python3 tools/tp.py gate` reports `unittest: OK - 546 tests`, 23.3 s for the whole
gate. The count moves as the backend grows, so the command's own output is the number that matters, not this
line. It was 453 at 17:36Z, 306 at 12:12Z and 293 twenty minutes before that.

**Regenerate the fixtures.**

```bash
python3 tools/build_fixture_store.py --check   # verify, writes nothing
python3 tools/build_fixture_store.py           # rewrite fixtures/synthetic_store.json
```

Observed with `--check`: `seed 20261107, 8 events, 76 tickets, 147 ledger rows`, ending with
`fixtures/synthetic_store.json matches a fresh build exactly`. 61 of those rows are priced
sales. The generator opens no socket and reads no clock; two runs write identical files.

**Not in this repository.** The Next.js frontend is the platform's own app, outside this
tree; a copy points here with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8788`
(`docs/BACKEND.md`), and `docs/frontend-honesty.patch` is the text only patch that makes its
screens state what the data is. No hosted demo, no deploy URL.

## Designed but not deployed

The chain work is one invariant:

> A ticket cannot move without the program recording the hop, and the program will not
> record a price above the organizer's cap.

A transfer the program never sees is missing data, not just a policy breach, so the value
here is the integrity of the engine's own input, not a marketplace. The design is a Token-2022
mint with a transfer hook, plus a per-ticket record the program owns and appends to on every
custody move. Layout, instruction set, cap check, error codes and threat model are in
`docs/ON-CHAIN-DESIGN.md`, sections 2 and 3. The cap is checked in the sale instruction
rather than in the hook, because a hook never sees lamports; the hook is what makes an
off-platform transfer impossible rather than merely detectable.

**No program is deployed on any cluster.** `/health` reports `programDeployed: false`,
`programId: null` and `rpcEnabled: false`. There is no mint, no transaction and no signature
in this repository, and the fixture's mint addresses are placeholders no explorer will find.

**This machine has no Solana toolchain.** `which solana anchor cargo rustc spl-token`
returns nothing and exits 1. What exists instead is `ticketpath/onchain/sim.py`, a Python
mirror of the same state machine, same field names, instruction names, integer arithmetic
and error codes, rendered by the console under a `[SIMULATED]` label. It proves the
arithmetic and the ordering, and nothing about any cluster.

On a laptop with Agave and Rust, `docs/ON-CHAIN-DESIGN.md` section 6 runs the sequence: a
funded keypair, a deploy, an event with two tiers, a hooked mint, a direct `spl-token
transfer` that fails inside the hook, and two transfers a lamport apart at the cap. Section 5
says what each tier of evidence would then show, and what it still would not.

One stale pointer, fixed: `/health`'s `chain.designDoc` named `docs/ON-CHAIN-FOR-LAPTOP.md`,
the superseded one-page pointer. It now names `docs/ON-CHAIN-DESIGN.md`, the design.
`records/ON-CHAIN-RECONCILIATION.md` records why, and `records/REPO-CONSISTENCY.md` records the
change and the command that shows it. **A server started before that change keeps the old value
in memory**, so restart it before reading `/health` and expecting the new one.

## What this data is

`fixtures/synthetic_store.json` is a generated fixture, not ticket data. It is produced by
`tools/build_fixture_store.py` from event specifications in that same file, with seed
`20261107`. Every payload the backend serves from it carries a `dataSource` label saying it
is synthetic, and the console prints that label in a banner at the top of the page.

It is deliberately over-sampled for demonstration. On the five events that have resales, 62%
to 77% of tickets resold at least once, against roughly 5.1% in the real market: twelve to
fifteen times the real rate, because a resale record has to contain resales for a resale
computation to be shown on it. Each event's description states that ratio in its own text,
computed from its own rows at build time.

Do not conclude any of the following:

- That any markup, price or distribution here is evidence about tickets. Markups were drawn
  from rules per regime so three cases could be shown; nothing was fitted or calibrated.
- That the series is a price path. The draws are independent of time to event, so there is no
  decline and no end game uptick, and a trend read off it is noise.
- That any event, venue, organizer or city describes something that happened.
- That anything here is on chain, or that any accuracy figure exists. No model has been
  fitted; the console's recommendation is a bound with a declared width whose parameters are
  declared, not estimated from real data.

## How the research is organised

Every conclusion carries an evidence class, A to E: A is direct ticket market evidence, B is
evidence from a related market, C is mathematical or statistical theory, D is a plausible
hypothesis with a mechanism and no evidence, E is a speculative opportunity recorded so it
is not lost. `SIM` marks something established by simulation here under stated assumptions,
and `UNVALIDATED` marks a claim whose validation needs data the programme does not have.
Findings are append only, conflicts are recorded rather than resolved quietly, and
`records/README.md` holds the conventions in full.

One line per record file:

- `README.md` the index: the six records, the evidence classes, the writing rules.
- `00-data-situation.md` the Phase 0 audit of what data actually exists on this machine.
- `00-prior-direction-index.md` the earlier direction documents and the decisions they fix.
- `A-research-ledger.md` every research question, its status, finding, class and sources.
- `B-mathematical-kb.md` formulations, assumptions, derivations, parameters, failure modes.
- `C-variable-registry.md` every candidate feature, its mechanism, availability and leakage risk.
- `D-model-registry.md` every model considered, its data cost, evidence and recommended role.
- `E-data-source-registry.md` providers, depth, frequency, licence, cost and reliability.
- `F-decision-log.md` decisions, rejected approaches, conflicts, open and closed questions.
- `FIXTURE-STORE.md` what the synthetic store contains, what it must not be read as, its invariants.
- `CONTRACT-MAP.md` the endpoint contract field by field, and what this backend can answer.
- `CONTRACT-CONFORMANCE.md` the contract as a test that addresses every route over a socket.
- `CORRECTIONS-APPLIED.md` what an independent verification round found and what changed.
- `DEMO-PROOF.md` which screens served backend numbers, measured, written at a time when no screenshot existed; there is a headless browser on the build machine now, `docs/SHOTS.md` is the account of it and `tools/shot.py` is the helper that captures a page (`README.md` corrected 2026-11-07T18:45Z, see the pack's §2.5 item five).
- `FRONTEND-INTEGRATION.md` what the frontend renders and which numbers are ours; partly superseded.
- `FRONTEND-HONESTY-PATCH.md` the text only patch that makes the frontend say what the data is.
- `ON-CHAIN-RECONCILIATION.md` why the design document replaced its earlier sibling.
- `BUILD-SPEC-NIGHT.md` what the overnight build was told to build, module by module.
- `SUBMISSION-PACK.md` the video script, submission text, field checklist and last hour checks.
- `findings/` twenty-nine tracked per investigation reports, append only, the primary record the six index (`git ls-files records/findings | wc -l` → 29, with a thirtieth on disk and uncommitted at 18:55Z; this line said twenty-seven and was stale).
- `BUILD-REPORT-CONSOLE.md` what the console pass built and where it departed from its spec.
- `FINAL-PROOF.md` the end-to-end proof run: what was executed, what it showed, what it did not.
- `FINAL-PROOF-2.md` the second proof run: the README's own commands, the live frontend's write check, and the
  64-state sweep.
- `DELIVERABLE.md` the Phase 8 integrated specification: a stub, marked NOT WRITTEN YET, with a
  status per required section and what would have to exist for it to be written.
- `REPO-CONSISTENCY.md` the consistency pass over this tree: every change, its evidence, and the
  claims that could not be fixed.

## Layout

```
ticketpath/    the backend. server.py is the route table and nothing else
  api/         one module per contract area: events, tickets, analytics, wallets, health
  core/        pure functions: no network, no clock except an injected now()
  adapters/    the only paths to the ledger file, Solana RPC and the pricing model seam
  console/     the server rendered page served at /
  onchain/     the Python mirror of the state machine, simulated only
tests/         unittest tests over 34 test modules, plus store_arithmetic.py; the run prints the count
fixtures/      synthetic_store.json and the note saying what it is not
tools/         build_fixture_store.py the deterministic fixture generator, guidance.py the console payload as JSON
docs/          backend notes, the on-chain design, the frontend labelling patch
records/       the six research records, the build and submission packs, findings/
```

The root also holds `AGENTS.md` and `RESEARCH-PROGRAM.md`, the brief and the research
standard this work was held to, and `NIGHT-BRIEF.md`, `NIGHT-LOG.md`, `NIGHT-QUEUE.md`, the
overnight build's working log.

## How this was built

Most of the code and the documents in this repository were written by AI coding agents, orchestrated by
the operator: agents wrote the backend, the engine, the console, the test suite and the research records,
and he set the briefs, checked the claims against the commands that produced them, and made every decision
that ships. The commit trailers name one of the tools on six of the repository's nineteen commits
(`git log --format='%(trailers)'`). This is not a claim of solo human authorship and no part of this
repository should be read as one. No generative model is implemented inside the product: the pricing
engine is bounded arithmetic with declared parameters, and `/health` reports `fitted: false`.

## Licence and status

MIT. The text is in `LICENSE`, and the copyright line names the holder:
`Copyright (c) 2026 Andrew Radu`.

Status: a local build. Nothing is deployed, no program exists on any cluster, there is no
hosted demo, and every number here comes from a synthetic fixture. The pricing seam is
populated by a rule-based bounded estimator with no fitted model behind it, and `/health`
says so in those words (`kind`, `fitted`, `note`). The research records say what is
established, what is designed and what is still a hypothesis, and `records/DELIVERABLE.md` is
a stub that states which parts of the Phase 8 specification do not exist yet.
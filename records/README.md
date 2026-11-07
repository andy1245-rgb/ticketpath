# Research records — index and conventions

Six records, as §2 of `RESEARCH-PROGRAM.md` requires. They are maintained as the work
happens and are not reconstructed at the end. If you are picking this up cold, read this
file, then `00-data-situation.md`, then `F-decision-log.md`.

Chat is not storage. A subagent's result dies with its transcript, so every
investigation writes its own file under `findings/` and the orchestrator folds it into
the records below.

## The six records

| File | Programme section | What lives there |
|---|---|---|
| `A-research-ledger.md` | §2.A | Every research question: who was assigned, status, finding, sources, evidence class, conclusion, unresolved parts |
| `B-mathematical-kb.md` | §2.B | Formulations, assumptions, derivations, parameterisation, limits, how models relate |
| `C-variable-registry.md` | §2.C | Every candidate feature or external variable, with mechanism, availability, leakage risk, priority |
| `D-model-registry.md` | §2.D | Every model considered: target, data cost, complexity, evidence, validation status, recommended role |
| `E-data-source-registry.md` | §2.E | Providers, depth, frequency, granularity, licence, collection cost, reliability |
| `F-decision-log.md` | §2.F | Decisions and their evidence, rejected approaches, conflicting findings, open questions, questions closed as not worth pursuing |

`00-data-situation.md` is the Phase 0 audit: what data actually exists on this machine,
verified rather than assumed. It gates every estimator in the programme.

`findings/` holds the raw per-investigation reports, one file each, named
`<phase><letter>-<slug>.md`. They are append-only and are the primary record; the six
records are the curated index over them. Never delete a finding to make a conclusion
tidy — record the conflict in `F`.

`DELIVERABLE.md` is the Phase 8 integrated specification (the programme's §5 final
deliverable).

## Evidence classes (programme §4.3) — mandatory on every important conclusion

| Class | Meaning |
|---|---|
| **A** | Directly supported by ticket-market empirical evidence (published primary market data or peer-reviewed ticket research) |
| **B** | Supported by empirical research in a related market (hotels, airlines, used cars, concerts-as-lab, auctions, financial microstructure) |
| **C** | Supported by mathematical theory or established statistical methodology — true by construction, not by measurement in this market |
| **D** | Plausible but untested hypothesis — mechanism argued, no evidence |
| **E** | Speculative research opportunity — recorded so it is not lost, not relied on |

Two further labels appear and are not evidence classes:

- **SIM** — established by simulation in this repository under stated generative
  assumptions. It says the estimator behaves as claimed *given* the assumptions. It says
  nothing about whether real ticket markets look like that.
- **UNVALIDATED** — a claim whose validation requires data this programme does not
  have. It is stated as a hypothesis plus the experiment that would test it, never as a
  result.

## Writing rules

- Every file opens with what it is and when it was last touched.
- Cite the primary source with a link. A blog post about a paper is not a source; the
  paper is.
- Never quote a number that was not checked (programme §4.6).
- Record conflicts, do not resolve them silently.
- Dates are UTC, ISO-8601.

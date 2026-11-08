# SeatPass

SeatPass prices primary-market event tickets off the secondary market's own resale record, and
caps resale on chain. A Token-2022 transfer hook on Solana refuses any resale above
`face * (1 + cap)`; the artist fee, a falling flip tax and region rules sit around that cap. It was
built for the MLH Solana Hackathon, 6-8 November 2026, by Andrew Radu and Veer Srivastava.

The repository slug and the Python package keep the historical name `ticketpath`; the product is SeatPass.

Live demo (static build, simulated in the browser): https://seatpass-ticketpath.pages.dev

## What is real, what is simulated, what is not built

| | Status | Evidence |
|---|---|---|
| Cap program on Solana devnet (v1) | **Real** | program `5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva`, `records/devnet-artefacts.json` |
| Cap program v2 (staged price, floor, forecast log, authority checks) | **Real**, devnet | program `Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF`, `records/onchain-v2-devnet.json` |
| Recorded devnet transfers | **Real** | 1.25 SOL on a 1 SOL face (25% cap) accepted; 1 lamport more refused with `6010 E_CAP_EXCEEDED` |
| Swarm runs against a local validator | **Real transactions, local chain** | 20 of 144 harness runs; counts below |
| Region-cap program (`programs/region_gate`) | Real on a **local validator only**, not on devnet | `records/findings/34-region-caps-build.md` |
| Ticket sales, events, resale history | **Synthetic fixture** (`fixtures/`), generated, not market data | every API response says `synthetic: true` |
| In-browser demo (Buyer / Organiser) | **Simulated**: no server, wallet, RPC or chain | the cap predicate and fee/tax formulas are the real code, transcribed |
| Dry swarm runs | **Simulated gateway**: nothing is built, signed or sent | counts below, split from validator runs |
| Pricing model | **Not built as a fitted model.** The engine is a rule-based bounded estimator (`fitted: false`); with no real resale ledger there is nothing to fit | `/health` of the backend |
| Live backend serving real data | **Not built.** The backend serves the synthetic fixture | `docs/BACKEND.md` |
| Wallet verification | Ed25519 signature check on a nonce exists in the backend; no wallet-bound login or purchase flow | `docs/BACKEND.md` |
| Artist fee, flip tax enforcement on chain | **Not enforced by the program.** They are seller-paid lamport legs in the same transaction; the chain does not check them. The refund-to-holders pool is not built | `docs/ON-CHAIN-DESIGN.md` section 16 |
| Payments, checkout, real resale marketplace | **Not built** | frontend marks them Unavailable |

Nothing here is a claim about a real ticket market. No accuracy number is claimed anywhere.

## The demo

Open https://seatpass-ticketpath.pages.dev/demo/ . Everything runs in your browser; state is kept in
`localStorage`, so clearing site data ends the run.

- The header toggle switches **Buyer** and **Organiser** (it is on every page except `/demo`, which has its
  own). The demo opens on the US region with the 25% cap binding, a 1.25 SOL ceiling on a 1 SOL face.
- Buyer: buy a ticket at face, then list it at a price you type. A banned, frozen or unresolved-region
  listing is refused with its own notice and is not dressed up as a cap breach; an over-cap price is
  refused as `6010` and the card prints both sides of the predicate. An admitted listing shows price,
  flip tax, artist fee and net. Each ticket keeps a hop history (price, wallet, instant).
- Organiser: name, face price, platform cap, manual override, resale mode (open, monitored, banned),
  region with its law ceiling, artist fee, flip tax, and per-ticket overrides (freeze, per-ticket maximum).
  Changes move the buyer view, because both read one state object.
- Other pages: `/events/` (filterable list), `/rules/` (the cap predicate and the recorded devnet
  transfers), `/pricing/`, `/door/` and `/verify/` (proof pages; the door lookup is inert on the static
  export). `frontend/DEMO.md` and `frontend/README.md` have the detail.

Real inside the demo: the cap predicate, the `6010` code, the flip-tax and artist-fee formulas and the
region table output. Simulated: the wallet, the sale, the clock, all money. Nothing is charged. Only the cap is chain-enforced
in reality; ban, freeze, region, fee and tax are application policy in the demo.

## How the cap works

- Predicate, evaluated by the hook on every transfer: `price * 10000 <= face * (10000 + cap_bps)`.
  Integer lamports only. At face 1,000,000,000 and 2500 bps the ceiling is 1,250,000,000.
- Why a hook and not a Token-2022 transfer fee: Token-2022 rounds the fee up, so on an indivisible 1-unit ticket
  a 5% or 15% fee withholds the whole ticket; measured in `records/findings/36-transfer-fee-on-a-one-unit-ticket.md`.
- Artist fee: `price * fee_bps // 10000`, paid by the seller as a lamport leg in the same
  transaction. Flip tax: 15% (1500 bps) when resold under one hour after acquisition, falling linearly to
  0 at 30 days, also a seller-paid leg; off unless the event turns it on. Neither is enforced by the chain.
- Resale ban and region geo-lock are application policy (the app refuses to list); the chain only
  enforces the cap.
- Region rules: `ticketpath/data/region-caps.json` (version 2026-11-08.1, 82 jurisdiction codes) resolves
  each to `capped`, `monitored` or `unresolved`. Computed by the resolver at an as-of date of 2026-12-01: 6 capped, 8 monitored, 68
  unresolved. Unresolved means no primary source was read; an event there may not claim lawfulness, and a
  fixed money cap is not converted to basis points without a sourced FX snapshot. Design:
  `records/REGION-CAPS-DESIGN.md`.

## The swarm

`market_swarm/` is a trading-agent harness: scripted and LLM-driven agents buy, list and resell a
synthetic ticket through a gateway, and the harness logs every decision. The gateway is either a **dry**
simulation (nothing signed or sent; it predicts the hook with the same predicate) or a **local validator**
running the real program. Raw datasets are git-ignored; only the numbers below are quoted. All rows
are synthetic.

| Measured by the harness | Dry | Validator |
|---|---|---|
| Runs (scripted agents) | 124 | 20 |
| Total across both | 144 runs, 49,684 decisions, 3,458 executed trades, 4,634 listings, 1,351 agents | |
| Cap refusals | 967 coded `6010` across both. The total is not split dry from validator, 124 of 144 runs used the simulated gateway, and so it is **not** a count of refusals on chain. The validator-backed figure is the six-agent local-validator run: 4 refused by the program | |

Second validator sweep: 8 runs (4 dry, 4 validator), 1,312 decisions, 141 executed, 10 refused (`6010`), 66 agents.

LLM-driven agents (deepseek flash, three parallel runs, all on the dry gateway because the local
validator would not boot in that window): 18 agents, 150 decisions, 19 fills, 170,121 tokens, $0.0723 in
total. 49 of the 150 decisions (32.7%) got no usable model reply and fell back to a scripted policy; no
agent asked above the ceiling, so that run produced zero refusals and does not test the cap.
Details of the live on-chain swarm run (6 agents, 10 rounds, 56 rows, 4 refused `6010`):
`records/swarm-live-onchain.json`.

## Quickstart

Requirements: Python 3.12 (standard library only for the backend, tests and tools); Node and npm for
the frontend.

```bash
# backend + console (synthetic fixture); then open http://127.0.0.1:8788/
python3 -m ticketpath.server --port 8788

# frontend static export (writes frontend/out/);
cd frontend && npm ci && npm run build
python3 -m http.server 4599 --directory out        # then open /demo/

# tests and checks, from the repository root
python3 tools/tp.py gate                  # tests plus console checks (use --quick for the fast set)
python3 tools/tp.py doc-check             # docs agree with code and with each other
python3 tools/public_safety.py check --tracked
python3 -m unittest discover -s tests
python3 -m unittest discover -s market_swarm/tests
cd frontend && npm run typecheck && npm run lint && npm test
```

## Repository map

| Path | What |
|---|---|
| `ticketpath/` | Python package: backend (`server`), pricing engine, region-cap resolver, console renderer |
| `programs/cap_hook/` | the Rust Token-2022 transfer-hook program deployed to devnet |
| `programs/region_gate/` | region-aware cap program, local validator only |
| `market_swarm/` | trading-agent harness, datasets, flip tax and artist fee modules |
| `frontend/` | Next.js app and the static demo (`/demo/`) |
| `fixtures/` | the synthetic event, ticket and ledger store |
| `tools/` | `tp.py` (CLI and gate), `doc_check.py`, `public_safety.py`, devnet publish and proof scripts |
| `tests/` | the main test suite |
| `docs/` | reference docs (`docs/CLI.md`, `docs/BACKEND.md`, `docs/ON-CHAIN-DESIGN.md`, `docs/STATUS-DETAILED.md`, ...) |
| `records/` | dated research record and evidence: ledger, registries, findings, devnet artefacts. Not rewritten after the fact |
| `RESEARCH-PROGRAM.md`, `AGENTS.md` | the research brief and the run conventions |

## Verify our claims

- v1 program: https://explorer.solana.com/address/5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva?cluster=devnet
- v2 program: https://explorer.solana.com/address/Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF?cluster=devnet
- Accepted at cap (1.25 SOL): https://explorer.solana.com/tx/E5RCrLwWikWCdHSd5MfqEBowXsmLn2n9fwYjnSwn8NhPi9j7weahbuRhgofu8ca8MVXzQUbvPrJqENDLNab7pJf?cluster=devnet
- Refused, 1 lamport over (`6010`): https://explorer.solana.com/tx/22dqSriig968nx8aA3YaFVt4CErgNbkwvxFtDKn2MWpcCdnA2KQhFYvhwTWZSpP64wzQjoBeMUKEZLRW1e7jKe79?cluster=devnet
- Ids, slots and block times: `records/devnet-artefacts.json`, `records/onchain-v2-devnet.json`.
- Docs agree with code: `python3 tools/doc_check.py --root .` (see `docs/DOC-CHECK.md`).
- Nothing unsafe is published: `python3 tools/public_safety.py check --tracked` (see `docs/PUBLIC-SAFETY.md`).
- Tests: `python3 tools/tp.py gate`.
- Evidence classes A to E (the research standard) are defined in `RESEARCH-PROGRAM.md` and `records/README.md`.

## Honest limits and what is next

- The hook checks the price the seller declares for the transfer, so a side payment made off our app can bypass the cap. The artist fee and flip tax bind only sales that our app builds.
- All market data is synthetic. No claim of predictive accuracy, willingness-to-pay or revenue
  uplift is made; those need a real resale ledger, which we do not have.
- The pricing engine is bounded arithmetic over fixture prices, not a fitted model. With no real
  listings that never sold, sale probability is specified, not estimated.
- The chain enforces the cap only. Fee, tax, ban and geo-lock are application policy; a seller
  can bypass the legs by trading outside the product.
- The region table is mostly `unresolved`; it is a design with sourced rows for a minority, not a legal survey.
- Devnet only. No audit, no mainnet deployment.
- Next: fit the price path and sale hazard on a real ledger; make the over-cap check mandatory on
  the checkout path; the refund-to-holders pool; deploy the region program to devnet.

## Team and licence

Andrew Radu and Veer Srivastava, MLH Solana Hackathon 2026. MIT licence, see `LICENSE`.

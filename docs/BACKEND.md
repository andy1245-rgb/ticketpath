# Backend: how to start it, what it answers, what it will not pretend

Python 3.12, standard library only. No pip, no numpy, no third-party package. Port
**8788** on `127.0.0.1` (`TICKETPATH_PORT` overrides; 8787 is refused because another
process owns it).

## Start

```bash
cd /home/friend/ticketPricing
python3 -m ticketpath.server
```

Prints one line, then serves:

```
ticketpath 0.1.0 listening on http://127.0.0.1:8788 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
  SYNTHETIC FIXTURE DATA. Hand-authored for tests, not real ticket data.
```

`GET /health` is the one call that says where the data comes from, whether the chain is
real, and whether a pricing model exists.

## Test

```bash
python3 -m unittest discover -s tests
```

## Point the frontend at it (the operator does this, not an agent)

The frontend at `/home/friend/ticketing-frontend` is live on :3000. Its data seam is
`lib/api.ts`, which switches backend on one environment variable:

```bash
NEXT_PUBLIC_API_BASE_URL=http://localhost:8788
```

Unset, the app serves its own fixtures. The contract document says 8787; that port is
taken on this machine, hence 8788. Nothing in that tree was edited or restarted by this
build.

## Environment

| Variable | Default | Effect |
|---|---|---|
| `TICKETPATH_PORT` | `8788` | bind port. `8787` is refused outright. |
| `TICKETPATH_HOST` | `127.0.0.1` | `--host` overrides |
| `TICKETPATH_LEDGER_MODE` | `fixture` | `fixture` or `empty`. `empty` serves no events and invents nothing. |
| `TICKETPATH_FIXTURE_PATH` | `fixtures/synthetic_store.json` | must declare `meta.synthetic: true` or it is refused |
| `TICKETPATH_CLUSTER` | `devnet` | reported by `/health` and baked into the verification message |
| `TICKETPATH_RPC_ENABLED` | unset | `1` enables the RPC adapter; it still reports no deployment, because there is none |
| `TICKETPATH_PROGRAM_ID` | unset | reported as null in `/health`; never invented |
| `TICKETPATH_ALLOW_ORIGIN` | `*` | CORS origin |

## Endpoints

Nine contract endpoints plus `/health`, all listed with their field-level honesty in
`records/CONTRACT-MAP.md`. The one to look at first:

```bash
curl -s http://127.0.0.1:8788/api/tickets/tkt_fixture_0001/resale-history | python3 -m json.tool
```

Every response carrying fixture data carries `dataSource.synthetic: true` and a
readable label. That is not optional: a judge must be able to tell.

## What it will not do

- It will not claim a program is deployed, a mint exists, or a transaction signature is
  known. `transferRestricted` is `false`, `signature` and `slot` are `null`.
- It will not produce a price forecast. The model seam returns
  `available: false, basis: "no_model_registered"`. There is no calibrated model and no
  data to calibrate one against.
- It will not enforce the resale cap or the verified-wallet gate. An API cannot: those
  are transfer-hook conditions. `docs/ON-CHAIN-FOR-LAPTOP.md`.
- It will not read `lib/mock`, and a test fails if any module names it.

## Layout

```
ticketpath/server.py                 HTTP entry, routing only
ticketpath/orchestrator.py           routes to adapters and core, decides, does not calculate
ticketpath/api/                      input validation and serialisation, one module per contract area
ticketpath/core/                     pure functions: markup, stats, analytics, pagination, base58, ed25519
ticketpath/adapters/ledger_adapter.py         the only path to ledger data (fixtures, labelled)
ticketpath/adapters/rpc_adapter.py            the only path to a Solana RPC; read-only, off, honest
ticketpath/adapters/pricing_model_adapter.py  the seam a model plugs into; empty today
fixtures/                            hand-authored synthetic store, labelled in its own meta
tests/                               unittest, 100 tests, no network outside an ephemeral-port server
docs/ON-CHAIN-FOR-LAPTOP.md          transfer hook + escrow design, DESIGN-NOT-DEPLOYED
records/CONTRACT-MAP.md              every contract field, and whether it can be served
```

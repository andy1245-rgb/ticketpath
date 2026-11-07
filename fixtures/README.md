# fixtures/ — synthetic store, hand-authored

**Nothing in this directory is real data.** `synthetic_store.json` was written by hand on
2026-11-07 so the backend has an internally consistent ledger to compute over while no
program is deployed and no ticket has ever been sold.

- Not scraped. Not generated. Not derived from `ticketing-frontend/lib/mock/`.
- Every wallet and mint address starts with `FXTURE`, so it cannot be mistaken for a real
  Solana key. They are valid base58 by shape only; no account exists on any cluster.
- Ledger rows carry `priceLamports` and no `markupBps`. Markup is computed by
  `ticketpath/core/markup.py` from each ticket's own tier face value, so the contract's
  multi-tier warning is structurally impossible to get wrong here.
- `signature` and `slot` are null on every row: there is no transaction to link to.
- `walletRegions` is empty: no wallet has volunteered a region.

Serving this file is honest only because every response that carries it also carries a
`dataSource` object saying `synthetic: true`. Do not remove that field.

What the store is for: proving the computation and the wire shapes. What it is not for:
estimating, validating, or reporting any result. See `records/00-data-situation.md`.

Expected values that tests assert are written down in `tests/test_fixture_expectations.py`
beside the arithmetic that produces them.

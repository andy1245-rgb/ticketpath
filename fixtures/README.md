# fixtures/: the synthetic store, generated

**Nothing in this directory is real data.** `synthetic_store.json` is produced by
`tools/build_fixture_store.py` from the event specs in that file, with seed
`20261107`. It exists so the backend has an internally consistent ledger to compute
over while no program is deployed and no ticket has ever been sold.

- Not scraped. Not hand-edited. Not derived from `ticketing-frontend/lib/mock/`.
- Every wallet and mint address begins with `SYN` and base58-decodes to exactly 32
  bytes. They are shape-valid and unmistakably placeholders: no account exists on any
  cluster and no explorer will find one. No two addresses share a truncated form
  (`first4…last4`), so a custody trail can never read as one wallet handing a ticket
  to itself.
- Ledger rows carry `priceLamports` and no `markupBps`. Markup is computed by
  `ticketpath/core/markup.py` from each ticket's own tier face value, so the contract's
  multi-tier warning is structurally impossible to get wrong here. Every price was
  built from an integer markup, so recomputation is exact and a test asserts it.
- `signature` and `slot` are null on every row: there is no transaction to link to.
- `walletRegions` is empty: no wallet has volunteered a region.

## Regenerating

```bash
python3 tools/build_fixture_store.py          # rewrite the store, print every invariant
python3 tools/build_fixture_store.py --check  # fail if the file on disk is not a fresh build
python3 tools/build_fixture_store.py --dump   # print it, write nothing
```

The generator is standard library only, takes no arguments that change the output,
opens no socket and reads no clock. Running it twice writes byte-identical files;
`tests/test_fixture_store.py` asserts that, so a hand edit to the JSON fails the
suite instead of quietly changing a served number.

Serving this file is honest only because every response that carries it also carries
a `dataSource` object saying `synthetic: true`. Do not remove that field.

What the store is for: demonstrating three pricing regimes and proving the
computation and the wire shapes. What it is not for: estimating, validating, or
reporting any result. `records/FIXTURE-STORE.md` describes what is in it and what a
judge must not conclude from it.

Expected values that tests assert are recomputed from the store by
`tests/store_arithmetic.py`, beside the arithmetic that produces them. The store's
own invariants are asserted by `tests/test_fixture_store.py`.

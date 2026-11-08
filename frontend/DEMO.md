# The live demo, `/demo`

An interactive walk through both sides of a resale, in one page, in one browser. It is built
from the repository's own rules and it says on its face that it is simulated.

## What is simulated, and what is not

Simulated: the environment. There is no server, no wallet, no RPC and no chain. State lives in
`localStorage` under `seatpass.demo.v1`, so a reload keeps your tickets and clearing site data
ends the run. A "sale" appends a row to a local object.

Not simulated, because it is not a paraphrase of a rule but the rule:

- The cap check is `price * 10000 <= face * (10000 + capBps)`, evaluated by `lib/cap.ts`, the
  same function the rest of the app calls. The refusal prints both sides of that inequality.
- The cap code is `6010 E_CAP_EXCEEDED`, the code the devnet program returned for the leg
  recorded in `records/devnet-artefacts.json`. `/rules` carries that record.
- The flip tax is `market_swarm/flip_tax.py` `FlipTaxSchedule.bps_for`, transcribed: the full
  rate under one hour, linear to zero at thirty days, floored. The defaults are the module's
  (`1500`, `3600`, `2592000`).
- The artist fee is `market_swarm/artist_fee.py` `fee_lamports`: `price * bps // 10000`. The
  rate is an event setting and the module ships no default, so the field is editable.
- The region geo-lock is `lib/demoRegions.ts`, **generated** by calling
  `ticketpath/core/region_caps.py` `resolve()` and `effective_ceiling()` for each jurisdiction
  it lists, at a 1 SOL face and a 2500 bps platform cap. The file carries the table version and
  sha256 the resolver returned, so a row can be checked against
  `ticketpath/data/region-caps.json` directly. The page prints the rule result, not a summary
  of it: policy, reason code, law cap, platform cap, which one binds, the ceiling, and the
  binding instrument with its confidence.

The demo will not list a ticket in a jurisdiction the table resolves to `unresolved`. That is
the table's rule, not a convenience: absence of a located instrument is not evidence that
resale is unrestricted, so a screen may not claim lawfulness there.

## The two sides

**Buyer.** Buy at face, then list at a price you type. The listing is admitted or refused
before any hop is recorded, and each ticket keeps its hop history: price, wallet, instant.

**Organiser.** Face price, platform cap, manual override, resale mode (open, monitored,
BANNED), region, artist fee and flip tax. Every change moves the buyer side with it, because
both views read one state object.

The toggle in the header switches the side and writes `seatpass.role.v1`. It is the same
toggle on every page; off `/demo` it takes you to `/demo`.

## Building and serving it

The frontend is a static export (`output: "export"`), so the page is a plain file:

```
cd frontend
npm install                 # node_modules is not committed
npx next build              # writes out/
python3 -m http.server 4599 --directory out
# then open http://127.0.0.1:4599/demo.html
```

## What it does not do

- No money moves and nothing is charged: the tax and the fee are computed and printed.
- No wallet connects. The demo wallet is a constant string in `lib/demoState.ts`.
- No listing is published to any market, and the demo never calls the backend.

# `example-run.json`, a template, not data

The loader is strict: an unknown key is an error, not a comment. So the documentation
lives here.

Copy the file, change the numbers, pass it with `--config`. **Every run it produces is
synthetic** and every dataset file says so.

## Why two events

The two events are identical in agents, seeds, face and ticket count. The only difference
is `mode`, and therefore the `cap_bps` written into the on-chain record:

| mode | `cap_bps` on chain | what the chain does |
|---|---|---|
| `capped` | the file's `cap_bps` (2500 = +25% over face) | refuses any staged price above `face · 1.25` with `CapExceeded` 6010 |
| `monitored` | 65535, the u16 maximum | the same predicate admits every price a scripted agent can produce, so the resale is recorded |

`cap_bps` is ignored in `monitored` mode but the file still names the *intended* cap, because
the scalper attacks the intended boundary, not the field maximum. That is the whole point of
the comparison: the same ask, refused by one mint and accepted by the other.

`monitored` is not "no cap". A price above `face · 7.5535` is still refused, because the
field cannot express a larger cap. Every ledger row carries `ceiling_lamports` so the real
boundary is never implicit.

## Units

- Lamports, integers, everywhere. `face_lamports: 1000000000` is 1 SOL of notional value.
- **No SOL changes hands for a ticket.** The cap hook holds no lamports, has no escrow and
  no listing instruction. A trade here is a custody transfer with a declared price.
- `budget_lamports` is a *notional spend* cap (the sum of prices an agent may commit), not
  a wallet balance. `budget_actions` is the count cap. Both bind.
- `kill_after_seconds` is required by the CLI. There is no unbounded run.

## Output

`out_dir` is relative and git-ignored. A run writes one dataset per event, plus a sidecar,
plus the throwaway keypairs and the validator ledger. None of it is ever committed: the
repository is code only.

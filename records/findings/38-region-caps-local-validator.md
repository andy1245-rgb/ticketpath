# region_gate — local validator proof

Written 2026-11-08T06:30:03Z by `tools/region_local_proof.py`.

**This ran on a LOCAL `solana-test-validator`.** Nothing here touched devnet, and the
devnet program `5EJ1GU3M4vn…` was not deployed to, called, or in any way used. The
validator's ledger is deleted when the run ends.

- Validator: `solana-test-validator 4.3.2 (src:0f131d36; feat:c9ad34d2, client:Agave)`
- Program id: `GGdyMiYbBtNHPpYn7VRYYHv1K9R9wqt9a7wSSNDAVp8i`
- Program `.so` sha256: `7e60fc80ffbad7bbc9f7d98bf9980ec113adacf0bd1ba76e23e6d957cf8e374b`
- Authority: `D12DFpN2MF6KE1bhm9sR3J52hg89J6kg4uJpiZKzb1cB`
- Result: **PASS 11/11**

## The three mints

| policy | mint | record | policy byte | cap_bps | jurisdiction | law_version | base |
|---|---|---|---|---|---|---|---|
| capped | `81yj9iCXmYvpRaTXf9u3qGJb7k2uRL6esphf9W4BPfdS` | `C6reQAkpYvWeYZvxfd8QvcoJP9Hr9tZgoP1SAfSMy31m` | 0 | 1000 | GB | 1 | 1000000000 |
| monitored | `3zBMNSSzavqo5JDyw89NQ4tKxj4hBzLocFvBFc7WU6wc` | `3TAZhw8ZrkDjW6y1ejJvMg2NJkpQexoz4jMG47eEVzC1` | 1 | 65535 | DE | 1 | 1000000000 |
| unresolved | `8aoxDTGAT66M9raN6Juc6JXYk4Hf4V6MmYseEoeoLjMi` | `FrwzdR3aCAyaJfBptQkiuH3ucWj8Kq42wgezpaatJcZW` | 2 | 65535 | ZZ | 1 | 1000000000 |

## Legs

Each leg is a real transaction. `err` is the `Custom` code read back from the cluster,
`log` is the substring matched in that transaction's own logs. Every leg is sent with
`skipPreflight`, so a refusal lands with its own signature instead of dying in
simulation.

| leg | expected | signature | err | matched log | result |
|---|---|---|---|---|---|
| L1 | capped-at-ceiling(1100000000)-succeeds | `5z1mXUnpEH2Wm3PgfAdzQoapx8XMvQkV8Q2pKipCzMmDzfyGChmpjrHuSftfdv5LkzUKCFdDs846DHBtca8Fz7QE` | null | cap admitted | pass |
| L2 | capped+1(1100000001)-refused-6010 | `dzMsW5kMCZqA3qWYXteyYhBz4CkkpS3sWeWYDdHnWJuhQ9kYnYLFJCPkp8UpEaiYmqHrRqj9AjkE4TnUzAd38mg` | 6010 | cap exceeded | pass |
| L3 | monitored-at-3x(3000000000)-succeeds | `5wLqowBb9u6FHqjf4RGP94HT3BcmTEjJvVmrpDyJ9TxcD1gxBriZYoBhRkQmTWJWRKQEdRAMt6viydLcFN27a4rW` | null | monitored | pass |
| L4 | unresolved-at-3x(3000000000)-succeeds | `jGdDW2Rbdhy7NrwCB8qkSbbjxvZzsjjpWPLQnLX3waHAnsWGCvVEUcTogbT6Akx84AUSmCrtjGYwWq7879CoSf8` | null | unresolved | pass |
| L5 | tighten-downward-to-500-succeeds-and-binds | `5ndExZk6vjny76r46BrmxzYpaNsnf5iMtTSip4YE1G8rcmwXzrx2wZskGhorxGrfVL5byoRsCCZuxT9iSaudNmmK` | null | tighten | pass |
| L5b | new-ceiling(1050000000)-still-admitted | `5hpvo7TYowi2biHjJy2gsuYNXi97hewSg3GBy6uTwqXjxHcKUsvvxBj2EXiBLaSduY3gjokCgoGWEopQ1XMayaMF` | null | cap admitted | pass |
| L5c | new-ceiling+1(1050000001)-refused-6010 | `3rwNZszce8Xj8qfaW4z4HEBzFtM2gD7GuT1b6xCyCXCsVC1b467Z3ZMxREUfXtXLRDRUXRH1WHKQW7P3r9KarBAR` | 6010 | cap exceeded | pass |
| L6 | tighten-upward-to-800-refused-6042 | `26NQqBsrPvkNecwGJVZCXsZKWAZqLaeLaieqGUjWx9mAo5dNK7cedhHPW4AAYD5VVu238RezMEnV23QCKqKwH5LJ` | 6042 | none | pass |
| L7 | monitored-to-capped-succeeds | `zkjdiuvJ6hFiJtazbzobSHWonacgTrSFgd1Kam8bcnvcAzXFz6KeTfwye6E6Bt2QrgWsfEQJVgJNDqqrhqd7xtG` | null | tighten | pass |
| L8 | non-authority-tighten-refused-6040 | `3tpRBdSe7HUr9T6a3qCzQT4AHa3amjuSQRUyqErrZ2fEgHNYksyCFXMMk9FXBAja5crWYUht17oN2rYexMZBtU5x` | 6040 | none | pass |
| L9 | amount-2-refused-6008 | `5qruyrfC4kqaNbF9FcTMdkyo9LWUixzE3TMuaq6owPmcSrbySZeWdr9VEQABSEmktF4oP66Mkcc1pZNBsqCqeeYh` | 6008 | none | pass |

## The record across each tighten

| when | account | base | cap_bps | pending | status | jurisdiction | policy | law_version |
|---|---|---|---|---|---|---|---|---|
| capped before TightenPolicy | `C6reQAkpYvWeYZvxfd8QvcoJP9Hr9tZgoP1SAfSMy31m` | 1000000000 | 1000 | 1100000001 | 1 | GB | 0 | 1 |
| capped after TightenPolicy 500/law2 | `C6reQAkpYvWeYZvxfd8QvcoJP9Hr9tZgoP1SAfSMy31m` | 1000000000 | 500 | 1100000001 | 1 | GB | 0 | 2 |
| monitored before TightenPolicy | `3TAZhw8ZrkDjW6y1ejJvMg2NJkpQexoz4jMG47eEVzC1` | 1000000000 | 65535 | 3000000000 | 1 | DE | 1 | 1 |
| monitored after TightenPolicy 1000/law2 | `3TAZhw8ZrkDjW6y1ejJvMg2NJkpQexoz4jMG47eEVzC1` | 1000000000 | 1000 | 3000000000 | 1 | DE | 0 | 2 |

## The brief's error numbers are stale - the program's own numbers are used

The brief for this tool quotes `6021`-`6024` for the four codes `region_gate` adds.
The crate does not. It assigns
`JurisdictionCode` = **6043**, `NotAuthority` = **6040**, `PolicyInvalid` = **6041**, `PolicyLoosens` = **6042**

with the reason written above its error enum: `6021`-`6028` are already taken by the
v2 program in `programs/cap_hook/` with *different* meanings (`E_BAND_UNSATISFIABLE` is
6022 there, `E_POLICY_INVALID` 6023), and a number meaning two things in two programs
is not branchable by a client. So this tool parses the enum out of
`programs/region_gate/src/lib.rs` and asserts against what the program assigns rather
than encoding the brief. `L6` and `L8` still test the behaviour the brief asked for -
an upward tighten is refused, a non-authority is refused - on the program's codes.

| error | the brief says | the program assigns |
|---|---|---|
| JurisdictionCode | 6023 | **6043** |
| NotAuthority | 6024 | **6040** |
| PolicyInvalid | 6021 | **6041** |
| PolicyLoosens | 6022 | **6042** |

## What each policy was shown to do

- **capped** admits a staged price at the ceiling and refuses one lamport over it. The
  predicate is `price * 10_000 <= base * (10_000 + cap_bps)`, in `u128`, with no division
  and inclusive at the cap — so at 1000 bps over a 1e9 base the ceiling is exactly
  1_100_000_000. The refusal carries `6010`.
- **monitored** admits 3x the base and logs the jurisdiction, price and ratio.
- **unresolved** admits 3x the base and logs that the law is unresolved.
- **TightenPolicy** lands downwards (cap 1000 -> 500) and the new cap then binds at the
  new ceiling; refuses an upward move with `6042`; allows
  monitored -> capped; and refuses a signer that is not the record's authority with
  `6040`.
- **amount != 1** is refused with `6008`, so a hooked mint cannot be dumped in bulk.

## Notes a reader should not have to rediscover

- `L5` in the brief asked for a transfer at 1_050_000_000 to fail and, in the same
  sentence, for the ceiling at 1_050_000_000 to succeed. Those cannot both hold. The
  program's predicate is inclusive (proven by `L1` and by its own unit test
  `capped_boundary_is_inclusive`), so the ceiling is admitted and the ceiling **+1** is
  refused: that is `L5b` and `L5c`.
- `L6` carries `law_version` 3 so it cannot be refused for a stale generation. A
  tightening must also name a later table generation, and the program checks
  `tighten_allows` before it checks the law version, so what comes back is the loosen
  refusal (`6042`) and not the policy-invalid code
  (`6041`).
- `L9` needs a balance of 2 in the source account to reach the hook at all, and four
  legs move one ticket each, so the capped mint is stocked with 6 tickets:
  enough that the 2-token attempt is refused for the amount and not for the balance.


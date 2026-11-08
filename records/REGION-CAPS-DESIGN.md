# Region-aware resale caps — design

**Owner:** the region-caps session (operator order 2026-11-08). These files are not abandoned working
notes: an earlier pass moved them to `tmp/abandoned-region-caps/` while another agent was in the tree,
and they were restored. See §12 for the collision record.

**Status:** design, written 2026-11-08 during the region-caps build. Code: `ticketpath/core/region_caps.py`,
`ticketpath/data/region-caps.json`. `programs/region_gate/` is parked: built, not deployed, not in the
transaction path (§13). Legal basis: `records/findings/33-a-region-cap-law.md`.
This file is not legal advice and makes no claim that any jurisdiction's law is what the table says; the table
is the claim, and every row carries its instrument, its date and its confidence.

---

## 1. What this feature is, and what it is not

One number per event (`resalePriceCapBps`) is the wrong shape once the same platform sells into
jurisdictions whose law differs. The feature is a **deterministic rules table** that turns
`(jurisdiction set, event date, review date)` into one of three enforcement policies, and a
**record field** that carries the outcome to the chain so the hook can enforce it:

| policy | the law says | chain | monitoring |
|---|---|---|---|
| `capped` | resale above a limit is restricted | the hook refuses a staged price above the limit | every admitted sale is a record row, as today |
| `monitored` | no price restriction is in force | the hook admits, and logs the jurisdiction and the price | the record itself is the evidence, which is the product's existing claim |
| `unresolved` | we could not establish it from a primary source | the hook admits and logs `unresolved`; the event cannot claim lawfulness | the event is flagged, and the operator must acknowledge it explicitly |

It is **not** a legal opinion, a compliance guarantee, or a claim that the table is complete. It does
not decide which law applies to a cross-border resale; it records that the question is open (§8).

## 2. The table is data, not a prompt

`ticketpath/data/region-caps.json`, one row per jurisdiction, each row carrying:

- `jurisdiction` — ISO-3166-1 alpha-2 (`IE`), or a subdivision where the law is sub-national
  (`GB-SCT`, `AU-NSW`, `CA-ON`, `US-CA`).
- `instrument_kind` — `primary_legislation | secondary_legislation | regulator_guidance |
  announced_policy | none_identified`. **Announced policy is a first-class value** because the
  United Kingdom has repeatedly announced a resale cap that is not law; collapsing the two would
  turn a press release into an enforcement rule.
- `status` — `in_force | announced | not_in_force | repealed | unknown`.
- `in_force_from` / `in_force_to` — ISO dates, or null.
- `applies_to` — `all_resale | designated_events | primary_sale | bots_only | disclosure_only |
  none | unknown`.
- `cap_basis` — `face | face_plus_fees | pct_above_face | absolute | no_price_cap | unknown`.
- `cap_value` — `{"kind":"bps","bps":1000}` or `{"kind":"minor_units","amount":...,"currency":"EUR"}`;
  null where the basis is `face` (0 bps is implied) or there is no cap.
- `citation`, `url`, `quoted_provision`, `penalty`, `enforcement_body`, `confidence`, `retrieved_at`,
  `notes`.

Two table-level fields are part of every resolution: `version` (a date plus a counter) and the
table's SHA-256. Both are stamped into the event record and into the harness log, so an enforcement
decision can be reproduced byte for byte from the file that made it.

There is no model, no prompt, no network call and no clock inside the resolver. `on_date` is a
parameter. That is the whole reason the table is JSON: a reviewer can diff it.

## 3. Resolution, in order

`resolve(jurisdictions, on_date=..., table=..., fx=None, accept_unresolved=False) -> CapPolicy`

1. Normalise each code (uppercase, trim). An empty set or an unknown code yields `unresolved`.
2. For each code, take the row. Missing row → `unresolved`, reason `unknown_jurisdiction`.
3. A row is **binding** for this event only if `status == in_force` and
   `in_force_from <= on_date <= in_force_to`. A row that is `announced`, `not_in_force`, `repealed`
   or `unknown` contributes nothing but is kept in the audit trail with that reason.
4. `applies_to == designated_events` needs the organiser's own answer, and it has **three** states:
   `True` (the event is designated) lets the row bind; `False` (the organiser states it is not) makes
   the row non-binding, reason `not_a_designated_event`; `None` — nobody has said — resolves the event
   to **unresolved**, reason `designation_not_stated`. Silence is not permission: the designation
   registers (Ireland s. 14, Victoria's Gazette) are not machine-readable here, so an unclassified
   event is an absence of information, and reading it as "not designated" would let an operator opt
   out of a cap by saying nothing. `applies_to == enumerated_events` (Florida's four statutory
   transaction classes) binds without any flag.
5. Turn a binding row into a candidate: `face` → cap 0 bps with base `face`; `face_plus_fees` → cap
   0 bps with base `face_plus_fees`; `pct_above_face` → the row's bps with base `face`;
   `no_price_cap` → `monitored`.
6. **Strictest wins.** Among candidates, the minimum `cap_bps`; a capped candidate beats a
   monitored one; any member that is `unresolved` makes the whole event `unresolved`, because a
   multi-venue event cannot be shown lawful on the strength of its easiest venue.
7. `absolute` never resolves silently. A fixed money amount needs a currency conversion, and a
   rate captured at issue time is only true at that instant; the resolver returns `unresolved`
   with reason `absolute_needs_fx` unless the caller passes an FX snapshot *and* `accept_unresolved`.
   `to_lamports()` implements the exact integer conversion for the day the operator decides to use
   it, and is tested, but no row in the table resolves through it today.
8. Output, immutable:

```
CapPolicy(kind, cap_bps, base, binding_jurisdiction, jurisdictions, table_version,
          table_sha256, basis, reason, as_of)
```

`reason` is a machine code (`law_caps_bps`, `no_cap_in_force`, `announced_only`,
`not_yet_in_force`, `repealed`, `not_a_designated_event`, `unknown_jurisdiction`,
`no_instrument_identified`, `absolute_needs_fx`), so a screen can say *why* without prose.

## 4. Which number the cap multiplies — the base, not always the face

The chain predicate is unchanged from `docs/ON-CHAIN-DESIGN.md` §3.10:

```
price * 10_000 <= base * (10_000 + cap_bps)
```

What changes is **what `base` means**. In a `face` jurisdiction it is the tier face. In a
`face_plus_fees` jurisdiction the law's base includes the fees the buyer paid, so the base is
`face + documented fees`, and the chain's `face_value_lamports` field carries that base. The event
record keeps the split (`faceLamports`, `feeLamports`) and the fee receipts, so the base is
auditable rather than asserted — **but that field does not exist yet**. Today no event row carries
a fee, so `cap_base_lamports` falls back to the face, which is stricter than the law; the gap is
recorded in `records/findings/34` §7.

This is the one place a reviewer should push hardest: the chain cannot tell a face from an all-in
price, because the field is just a number. The guarantee is procedural — one creation path computes
the base from the law's basis, the split is stored beside it, and a test asserts that a
`face_plus_fees` event's base equals face + fee to the lamport. It is not a chain-level guarantee
and the docs say so.

## 5. Money: lamports, integers, and no invented exchange rate

- All arithmetic is integer. Basis points are integers, lamports are integers, and no float enters
  the resolver, the converter or the predicate. `u128` on chain, Python's exact integers off chain.
- Percentage and face-based caps are currency-free: no conversion happens at all. This is the
  common case and the reason the feature can be built without an oracle.
- A statute that states a fixed money amount is converted only through an explicit FX snapshot
  `{base, quote, rate_num, rate_den, source, as_of}`, with floor division, and the floor is stated
  to make the resulting cap **stricter** than the legal amount, never looser. Currency is never
  assumed from the event's city.
- The platform's own money stays lamports: face values are lamports at issue, the cap is basis
  points over the base, and nothing is converted to SOL for display in the stored record.

## 6. The law changing after a ticket is sold

A ticket's policy is stamped at issue: `jurisdiction`, `policy`, `cap_bps`, `law_version`. Three
cases, and the chain does exactly one of them:

| change | chain | why |
|---|---|---|
| the law **tightens** mid-event | `TightenPolicy { new_cap_bps, new_law_version }` is allowed | a stricter law should bind; the instruction is monotone |
| the law **loosens or repeals** | **refused** by `TightenPolicy`; the record keeps the cap it was sold under | otherwise an organiser can raise a cap, sell, and lower it again, which is the gaming hole `docs/ON-CHAIN-DESIGN.md` §2.1 closes; and a ticket sold under stated terms keeps them |
| a *new* event is created | resolves against the new law | nothing is inherited |

The monotone rule is the design's answer to "the law changed after sale": tightening is a legal
obligation and is representable; loosening is not applied to an issued ticket, because the chain
cannot distinguish a genuine repeal from an organiser's convenience. What the operator may do
instead is record `relaxed_at` and `relaxed_to` off chain against the event, and issue new tickets
under the new law. Whether a mid-event tightening binds tickets already sold is a legal question
this design does **not** settle; it only makes the tightening enforceable if the operator decides it
does.

## 7. Multi-venue events and tours

An event carries `jurisdictions: [primary, ...]`. Resolution is the strictest of the set (§3.6),
and `bindingJurisdiction` names which member produced the number, so the screen can say "capped at
+10% because of NSW" instead of "capped". A tour with one capped stop and three monitored ones is
capped for the whole event. That is deliberately conservative: the platform has one price per
tier, and a tier's tickets may be used at any stop.

## 8. What the design deliberately does not decide

1. **Which law applies to a cross-border resale** — venue, buyer residence or seller establishment.
   The table records what each instrument says, including that most are silent. The resolver does
   not pick; the operator sets the event's jurisdiction.
2. **Whether a platform rule may be stricter than the law.** It can; this design only refuses to be
   looser without saying so. A stricter-than-law cap is a product choice recorded in the event.
3. **Absolute-amount caps on chain.** Described, converted, tested, not enforced (§3.7).
4. **Enforcement against a listing made off-platform.** The hook binds a transfer that goes through
   the mint; it cannot see a ticket sold as an IOU in a chat window. Same limit as the rest of the
   on-chain design, and it is stated in `docs/ON-CHAIN-DESIGN.md` §1.3.

## 9. The record field, on chain

`programs/region_gate/` (local validator only; the proven devnet program `5EJ1GU3M4vn…` is never
touched):

```
TicketRecord {
    face_value_lamports: u64,   // the cap BASE (§4), not necessarily the tier face
    cap_bps: u16,
    pending_price_lamports: u64,
    status: u8,                 // 1 transferable, 0 not
    jurisdiction: [u8; 2],      // the binding NATION; 'ZZ' = unresolved
    policy: u8,                 // 0 capped, 1 monitored, 2 unresolved
    law_version: u32,           // the table generation the policy was stamped from
}
```

Instructions: `0 InitializeExtraAccountMetaList`, `1 InitializeRecord`, `2 SetPendingPrice`,
`3 SetStatus`, plus **`4 TightenPolicy`** (§6). New error codes, never renumbered:
`6040 NotAuthority`, `6041 PolicyInvalid`, `6042 PolicyLoosens`, `6043 JurisdictionCode`.

They start at **6040** and not at 6021 because the v2 program in `programs/cap_hook/` already owns
6021-6028 with different meanings (`E_BELOW_FLOOR`, `E_BAND_UNSATISFIABLE`, `E_POLICY_INVALID`,
`E_FORECAST_EXISTS`, ...). Error numbers are a shared interface across both programs, so a new block
is the only safe way to add four codes. §12 records the overlap in full.

The hook branches once: `policy == 0` → the cap predicate of §3.10; `policy == 1` or `2` → admit and
`msg!` the jurisdiction, price, face and law version. A transfer with no staged price is still
`6009 TransferNotStaged`: monitoring needs a number to record, and a gift records nothing.

Why the chain carries only a two-byte nation and not the subdivision: the chain field is the audit
trail of **what was enforced**, not the whole legal picture. The subdivision set, the citation and
the table hash live in the event record, where they can be updated without a migration. The cost is
that a chain reader alone cannot tell `AU-NSW` from `AU-VIC`; the benefit is that the field can
never be half-migrated.

## 10. Verification surfaces

| claim | surface | how it is checked |
|---|---|---|
| the table parses and every row is well formed | unit tests | `tests/test_region_caps_table.py` |
| resolution order, strictest-wins, dates, unknown | unit tests | `tests/test_region_caps.py` |
| the base is face + fee where the law says so | unit test | `tests/test_region_caps.py` |
| the hook refuses over the cap and admits under it | **local validator** | `tools/region_local_proof.py`, real transactions, error codes read from the cluster |
| tightening is monotone | local validator | same tool: 1000→500 lands, 500→800 refused 6042 (6022 is the v2 program's `E_BAND_UNSATISFIABLE`) |
| a monitored event admits a 3× face resale and logs it | local validator | same tool |
| the event payload carries the policy | unit test on the API | `tests/test_event_jurisdiction.py` |
| the harness derives mode and cap from the table | unit test + dry run | `tests/test_region_harness.py`, `tools/region_harness.py` |

The devnet program is **not** used: this feature is verified on a local validator, and the artefact
in `records/devnet-artefacts.json` describes the v1 cap-only program. The README says which program
is which.

## 11. The contract surface: eight additive keys on `Event`

`lib/types.ts` is unchanged and this repository does not edit it. The policy reaches a screen through
eight additive keys on `Event`, declared one by one in `tests/test_contract_conformance.py` so the
exact-shape check stays exact instead of being loosened. What each key means is tabulated in
`records/CONTRACT-MAP.md` §7.9; what matters here is the boundary between them:

- `resalePriceCapBps` keeps its contract meaning, the organiser's configured cap, and it is **not**
the enforced number.
- `enforcedCap.enforcedCapBps` is the enforced number, and `bindingRule` (`law` or `platform`) says
which rule produced it, so a screen never attributes a product decision to a law.
- `enforcedCapByTier` is the honest shape for a multi-tier event: a cap is a multiple of the ticket's
own face, so an event-wide number is wrong by the tier ratio. `enforcedCap` exists only for the case
where every tier agrees.
- A null is a statement and not a hole. Null `jurisdiction` is "not stated", which is not
"unrestricted"; null `resalePolicy` is "not computed", which is not `unresolved`; and `unresolved` is
a policy in its own right, the one where the event cannot claim lawfulness.

The jurisdiction is a field of the event row and of the record account (§9), and it is fixed when the
event is created. The cap is derived from it and from the named table generation on every build and is
never stored, so a cap cannot drift from the table, and raising one means changing a law row rather
than a number on an event.

## 12. The collision with the in-flight program-v2 build, recorded

While this feature was being built, a second agent in the same tree was implementing the ten-feature
plan's program v2 (features 4, 6, 8, 10) inside `programs/cap_hook/`. The two overlap on exactly one
thing, and it is feature 10: v2's `TicketRecord` already carries `jurisdiction: [u8; 2]` and
`policy: u8`.

What happened, and what it means:

1. That agent moved this feature's files (`records/REGION-CAPS-DESIGN.md`,
   `ticketpath/core/region_caps.py`, `programs/region_gate/`, the research notes) to
   `tmp/abandoned-region-caps/`. They were restored immediately. Nothing was lost.
2. v2's record layout is a **superset-compatible** target for this design: `jurisdiction` and
   `policy` are the same two fields, with 0 = capped and 1 = monitored, and `ZZ` for unspecified.
   v2 does not have this design's third state (`policy = 2`, unresolved) and does not have
   `TightenPolicy`; both are additive, and neither requires changing a v2 field.
3. Error numbers 6021-6028 are v2's. This crate's four codes were renumbered to 6040-6043 for that
   reason. A future merge must not renumber either block.
4. `programs/region_gate/` is therefore kept as the **isolated, minimal proof** of this feature's
   contract on a local validator, not as a rival deployment. If v2 lands, the recommendation is that
   v2 gains `policy = 2` and `TightenPolicy` and `region_gate` is retired; the resolver
   (`ticketpath/core/region_caps.py`) is the part that must survive either way, because it is where
   the law lives, and the chain only stores its outcome.

What was **not** done, deliberately: no edit to `programs/cap_hook/**`, no edit to
`market_swarm/config.py`, `market_swarm/gateway.py`, `tools/devnet_publish.py` or `tools/tp.py`,
because each was being written by another agent at the time. The harness integration is therefore a
separate wrapper (`tools/region_harness.py`) rather than an edit to the swarm's loader, and the
build report says where it would have gone.

## 13. The park: enforcement is off chain, and the crate is the design record

Enforcement happens in two places and neither of them is `programs/region_gate/`. The table decides
at event creation: `region_caps.resolve` reads `ticketpath/data/region-caps.json` against the
event's own start date, `effective_ceiling` turns the answer into one number per tier, and that
number is what the event carries as `enforcedCap.enforcedCapBps` and what the record carries as
`cap_bps`. What the record retains of the decision is the `policy` byte, and on
`programs/cap_hook/` v2 that byte is the only thing that says whether the hook refused on price at
all.

`programs/region_gate/` is parked. It was built on 2026-11-08 as §9's on-chain half, it compiled
once (the `.so` hash and the one local-validator run are in
`records/findings/38-region-caps-local-validator.md`), it is not deployed, and nothing in
`ticketpath/` imports or calls it. It stays in the tree for one reason: it is the written record of
where the check could move if the table ever has to be enforced by something the platform cannot
rewrite. Its `README.md` says what that would cost and what would have to change first.

What the park settles, and what it does not:

| question | answer today |
|---|---|
| where a jurisdiction is applied | off chain, at event creation, by the rules table |
| what the chain carries of it | `jurisdiction: [u8; 2]` and `policy: u8`, set once at `InitializeRecord`; never the citation, never the table hash |
| the third state, `unresolved`, on chain | not representable in v2, which refuses `policy = 2` with `6023`; the crate assigns it. So "we could not establish the law" is an off-chain statement today |
| what refuses a resale above the ceiling | the hook in `programs/cap_hook/`, on the `cap_bps` and `base` the record carries, when `policy = 0` |
| whether the table may refuse a sale on its own authority | open, and the operator's decision; the rows are evidence, and a crate that could enforce them is not a licence to |

If that decision is ever taken, §12.4's recommendation is the cheaper of the two moves: v2 gains
`policy = 2` and `TightenPolicy`, and this crate is retired rather than deployed beside it. The
crate's source is what makes that a comparison instead of a guess, because it is where the byte
rules were worked out, `validate_policy` in particular: `monitored` must carry `65535`, so a policy
with no cap cannot be stamped as a low number nobody looked at.

# The console: what a judge sees, and why each sentence is admissible

One HTML page at **http://127.0.0.1:8788/**, server-rendered by `ticketpath/console/`,
Python standard library only, no framework, no CDN, no build step, no JavaScript. Every
control is a query parameter, so every state has a URL. `docs/RUN.md` has the command.

## The order of the page, and why

1. **Banner.** T1 verbatim, then the sentence about no program being deployed, then the
   SHA-256 of the store the numbers came from. A screenshot names its own source.
2. **Controls.** Event, tier, `asOf`, `capBps`, `feeLamports`, `tau`, `Recompute`, and
   `Show the refusal` (which submits `sim=1` — it is a button, not a script). The
   `capBps` field shows the cap this page prices against, which is the URL's when the URL
   names one and the event's recorded cap otherwise, and the canonical URL under it
   carries the same number; the page says so in one line, and an event that records no cap
   says that instead of showing an empty box.
3. **Evidence strip.** `[FIXTURE] 12 resales · 12 tickets · 9 at the ceiling`,
   `[FIXTURE] 8 events in the store, 5 with any resale at this instant`, `[DEVNET] 0
   on-chain transactions`. The evidence count is the headline metric on purpose. The event
   total is the store's -- the schema carries no instant at which an event was created, so
   that one count cannot follow a cut and its noun says so -- and every count beside it is
   the count at the decision instant. The store total is served plus withheld: when the
   loader held an event back, the line names both (`[FIXTURE] 8 events in the store,
   [FIXTURE] 7 served, one held back: a sale recorded without money`), because `7 events in
   the store` on a file of eight is a false statement about the store. The withheld reason
   is given in words; the typed code stays in the payload and on that event's own page.
4. **The decision**, by regime:
   - *capped and binding*: `at least {ceiling} SOL per ticket`, A19 in full, the value
     line as a floor, `Range: 1.38 SOL and up. We do not state an upper bound from this
     record.`, and `This is a bound, not an optimum.`
   - *uncapped* or *capped, no mass point*: a point, `Band {lo} – {hi} SOL`, T3, the
     02-d range line, A4, and A20 on the no-mass-point regime.
   - *no resale*: the refusal, the prior band labelled as a band around the prior, A13 or
     A12, A17, the exact cap arithmetic, and the sentence naming what would change it.
   - *any of the three, when the cap in force sits below the price the record supports*:
     the typed refusal `recommendation_above_cap`, with the cap and the resale ceiling its
     own integer arithmetic implies, and no primary price. The ceiling is not printed in
     the price's place: a cap is a ceiling on the resale price and a floor on value, not a
     target for the primary price (A10). The sentence says which half the cap binds: a cap
     in basis points over face decides how the resale price divides, not what the organizer
     may charge, and the resales this record prices from would be illegal under this one, so
     the record has run out (11-cap-capture-check 10.1).

   The mode line carries the event's status and dates beside the decision instant. The
   status is the store's current field and cannot follow the instant, so where the two
   disagree the line says both and says they differ (`status on_sale is the store's current
   field, not the status at this decision instant ... the field and the instant disagree`),
   and the before-on-sale mode adds that an instant after the event's end is not a decision
   that could have been taken then.
5. **The market**: median and mean markup, the at-ceiling count with A16, any repeat sale
   as A18, and the composite rate as A1 with T4. Every count in this block is the selected
   tier's, said so in the sentence. In the before-on-sale mode the block also carries the
   tier's own excluded count (`[FIXTURE] 9 recorded sales in this tier are excluded by the
   mode`), which is the strip's event-scoped 12 seen through the block's scope: two scopes,
   two counts, both named.
6. **The refusals**, always present: sale probability at a price (`not_identified`), the
   interior optimum (`no_demand_response`), net revenue without a fee (`no_fee_model`),
   and the path (a named reason: `cap_mass_dominates`, `insufficient_marks`,
   `insufficient_time_spread`, `degenerate_design`, `outside_support`), plus
   `no_upper_bound` on a binding event, plus `recommendation_above_cap` when the page's cap
   sits below the price the record supports. The panel is never empty and every line is
   `[REFUSED]`.
7. **The design panel**, badged `[DESIGN]`, with the instruction → check → error-code
   table.
8. **The simulated state machine**, every line badged `[SIMULATED]`, with the caption
   saying it proves the arithmetic and not that Token-2022 calls a hook.
9. **The chain slot**, last, `[DEVNET]` in its absent state until an artefact verifies.

## The verbs

`GET` and `HEAD` serve; `POST` is a 405 where it is not an endpoint; `PUT`, `DELETE`,
`PATCH`, `TRACE` and `CONNECT` are a 405 with the rendered page on a console path, a 405
with the JSON error on an API path, and a 404 on a path that does not exist. No verb is
answered by the interpreter's own 501 page.

## The one rule that is enforced by tests, not by discipline

Every number is rendered through `units.num`, which puts the badge in the same text run,
in front of the value. `tests/test_console_page.py` asserts that every `.n` span begins
with one of the eight badges and that the only digits on the page outside a badge are
inside a sentence from `ticketpath/core/labels.py`. A count that sits inside a sentence is
its own `.n` span, substituted by `blocks._sentence`: A19's `8 of 9 recorded resales
(88.9%)` is four badged numbers under a panel badged `[UNVALIDATED]`, so the badge travels
with the count and not with the block. `tests/test_guidance_api.py` walks the payload and
fails on any number without a badge, a basis naming the record and its counts, and a label
id.

## What is intentionally absent

No listing, bid, buy or checkout control. No sale probability at a price. No interior
optimum. No accuracy, calibration or coverage number. No placeholder devnet signature and
no explorer link until an artefact verifies. No CSS-only label, no tooltip, no
hover-only text.

# NOTES

Decisions, deviations and the things that need a human. `COVERAGE.md` maps the
backend inventory to screens, `VERIFY.md` holds the evidence, `DECISIONS.md`
holds the build-level calls.

## The copy rule for this pass

The operator's instruction on 2026-11-08, after the build had started, supersedes
the earlier one in the task message:

> keep the design's sample copy exactly as in the exports for now; do NOT reword
> it. Still list every overclaiming string as known demo copy in NOTES.md for
> later editing.

So the export's sentences ship as written. They are **demo copy**, not claims
this build can support, and each one is listed below with what is actually true.
The eariler task message asked for these to be reworded prototype-honest; the
newer sentence wins and the list is the record of what still has to change.

### Known demo copy, kept as written, to be edited later

| String | Where | Why it overclaims | What is true here |
|---|---|---|---|
| "02 Pay with card or Apple Pay" | landing, step 02 | There is no payment flow of any kind. No checkout endpoint, no payment method, no fee field in any record. | `capabilities.purchase` is false and the checkout screen says so. |
| "03 The ticket lands in a wallet we made you" | landing, step 03 | No wallet is created for anyone, and ticket issuance has no endpoint. | Tickets exist as fixture rows only. `capabilities.purchase` is false. |
| "The contract rejects any resale above face value. The organizer sets it once." | landing, card 2 | The cap program is written but not deployed, and nothing is enforced at runtime. The cap is also not universally face value: it is a jurisdictional gate tightened against a platform cap. | No program is deployed on any cluster. `/rules` states the real status from `/health`. |
| "Works without signal at the door" | landing, trust row | There is no door code, no QR format and no offline verification path. | `capabilities.doorCode` is false. The door screen reads real fields and issues no code. |
| "04 Show the code at the door. It works without signal." | landing, step 04 | Same: no code exists to show. | Same as above. |
| "152 of 200 sold" | proof band, figure 1 | These are demo values with no source. | Replaced with `issuedCount` of `totalSupply` for the featured event, which is the one figure the brief requires to be real (5.2). |
| "3 resales blocked at the cap" | proof band, figure 2 | Nothing blocks a resale: there are zero listings in the fixtures and no rejection is recorded anywhere. | Kept as a demo figure from `lib/demo.ts`; the band carries the "Demo figures" note. |
| "$0 hidden fees" | proof band, figure 3 | Implies a purchase flow that charges fees. | Kept as a demo figure from `lib/demo.ts`; the band carries the "Demo figures" note. |

Prices are shown in SOL, not dollars. Every figure in the product is lamports
formatted at the edge, and there is no fiat rate anywhere in the backend, so a
"$" sign would be invented. That is a deviation from the exports' "$120", not a
copy rewrite.

## Deviations from the exports, by line

Both Stitch exports (`desktop.html`, `mobile.html`) were expected at
`../seatpass-exports/`, beside the checkout. **That directory does not exist on
this machine**, so there is no export to diff against line by line. The build follows
the written specification instead: `01-design-system.txt` (tokens),
`02-generate-desktop.txt` (landing geometry, region by region),
`03-generate-mobile.txt` (the 390 layout) and `05-hand-edit-after-export.txt`
(the twelve hand fixes). Section 8.7 of the brief could therefore not be run as
written; `VERIFY.md` records that.

Structural removals the brief requires, all done:

- The purple avatar circle is gone.
- The mobile tab bar is gone. Navigation is the header at every width.
- All blur is gone. The header is opaque surface plus one hairline.
- `user-scalable=no` and `maximum-scale` are gone; the viewport is
  `width=device-width, initial-scale=1`.
- The Tailwind CDN, the Material Symbols font, every Material token name and
  every `href="#"` are gone. Routes are real.
- The 11px strip and axis are 12px.
- `border-dashed` is gone; the perforation is a drawn 4/4 dash.
- The two `|` pipes are replaced by real 1px rules.
- Fixed 380px page widths are gone; the content box is 1200 with a fluid gutter.

## Assumptions

- **SeatPass vs Ticketpath.** SeatPass is the product name, so every user-facing
  string says SeatPass. The repo, the package name and the backend package
  (`ticketpath`) are untouched, per "touch nothing else".
- **The featured event** is `getEvents({status:"on_sale", limit:1})` — the first
  on-sale event in `startsAt` ascending order, which is deterministic and is the
  same rule the browse list uses. The hero ticket is `getTickets({eventId,
  limit:1})` for that event.
- **The cap shown is the enforced cap**, not `resalePriceCapBps`. The backend
  reports an `enforcedCap` from the jurisdiction gate tightened against the
  platform cap; on one live event `resalePriceCapBps` is 2500 while the enforced
  ceiling is 0 bps by law. Where the two disagree the enforced record wins,
  because that is what the contract would admit against.
- **Mock mode drops fixture signatures.** The bundled fixtures carry a made-up
  signature and slot on all 253 ledger rows and give `issue` rows a price equal
  to face. The live backend returns null for both. Mock mode normalises them to
  null at the seam (`lib/api.ts`), so the UI never shows a transaction it cannot
  stand behind. Without this, mock mode would render fake explorer links.
- **`dataSource` is printed once per page** with the backend's own label,
  unparaphrased. In mock mode there is no backend, so the label says so.
- **`lib/demo.ts` holds exactly two figures**, the two proof figures with no
  backend source. Anything with an endpoint is read, never demoed.
- **No `NEXT_PUBLIC_PROGRAM_ID` is set**, so the on-chain strip reads "Program not
  deployed yet" and the copy and explorer controls are disabled with a reason.
  The backend's `chain.programDeployed` is false on every cluster and it reports
  `programId: null`, so this is the truthful state, not a placeholder.

## What needs a decision from the operator

1. **The exports are missing.** Land the two Stitch files at
   `../seatpass-exports/` and the visual diff in 8.7 can be run for real. Until then the visual surface is verified against the written
   specification only, and the numbers in `VERIFY.md` are measured, not compared.
2. **The demo copy above** needs its second pass. It ships as written because
   that is what was asked for; it reads as a shipped feature on a page whose
   whole argument is that it does not overclaim.
3. **The ticket card renders taller than the export's 220px.** The export's own
   interior arithmetic is 104 + 84 + 16 + 16 = 220, but the chart needs its
   12px labels and the card needs its 24px padding, which puts the card at 263.
   Either the plot is clipped to 84px total or the card accepts the extra height.
   The build keeps the readable plot.

## Added after the screens landed

- **Region reads the payload in mock mode.** The bundled `lib/mock/wallets.json`
  carries volunteered regions, so the destinations table shows a real value there
  while the live backend returns null on every row and the table shows an em dash.
  Rendering the payload rather than forcing a dash is the honest reading of the
  field, but it does mean the two modes look different on that column. Say the
  word and it can be gated to nulls.
- **The on-chain strip states the deployment, not the export's sentence.** The
  chip reads "Not deployed" from `/health` `chain.programDeployed` (false) rather
  than "Enforced on-chain", because nothing is enforced at runtime and the
  backend reports `programId: null`. The words "Enforced on-chain" appear only
  when that field is true.
- **The three card diagrams are drawn here.** Simple 1.5px line constructions at
  32px, not the export's illustrations. The ownership one reads as three nodes on
  a rail only at full size.
- **Twelve components plus `ui.tsx` and `useMeasure`.** Six baseline components
  were deleted as dead once the new screens replaced them; the list is in
  `DECISIONS.md`.
- **The ticket card is taller than the export's 220px.** It measures 263: the
  export's own interior arithmetic assumes a 84px plot with 16px labels, and with
  the card's 24px padding and the cap chip row the honest total is 263. The
  readable plot was kept over the export's number.

## Edits made for the move into the release repository

This tree was built in a checkout of its own and then copied here, file for file,
from `git ls-files` at its last commit. Four kinds of change were made on the way in,
and they are listed so a reader can tell the build's text from the release's. Nothing
was reworded for taste; every edit removes a machine handle or narrows a claim to what
the copy can still support.

| File | Before | After | Why |
|---|---|---|---|
| `NOTES.md`, twice | `seatpass-exports/` at an absolute path under a home directory | `../seatpass-exports/`, beside the checkout | the release repository is public, and an absolute path publishes a username and a machine layout; the relative form says the same thing |
| `VERIFY.md`, header | the port another session's dev server holds, named as a live process | the server described without its port | a port tied to a running process is his machine's business, not a reader's; the warning that makes the sentence worth having is unchanged |
| `VERIFY.md` 8.4, 8.7, 8.8 | playwright-core and Chrome for Testing at absolute paths under a home directory | `SEATPASS_PLAYWRIGHT_CORE` and `SEATPASS_CHROME`, plus `$SHOT` for the screenshot helper | the paths were machine handles; the variables are what `tools/verify-landing.cjs` reads now, so the check still runs and stays outside `package.json` |
| `VERIFY.md` 8.6 | `cd` into the backend checkout by absolute path | `cd ..` | the backend is now the parent of `frontend/`, so the relative form is also the correct one |
| `tools/build-copy.sh` | `SRC` and `DST` hardcoded to a home path and `/tmp` | `SEATPASS_SRC` defaults to this checkout, `SEATPASS_BUILD_DIR` defaults to a directory under the system temp dir | same copy rule, no machine handle, and the copy can now be put anywhere |
| `tools/verify-landing.cjs` | two absolute paths as constants | two environment variables with the project's own resolution as the default | the check ran on this machine with those paths set; a clone with playwright-core installed runs it with nothing set |

Two things are deliberately absent from the copy rather than edited:

- `.env.example`. It is tracked in the source checkout and carries no values, but the
  instruction for the import excluded `.env*` by glob. Every variable it named is
  documented in `README.md` above and in `API_CONTRACT.md`.
- Build output, `node_modules`, `.next` and the source checkout's `.git`: none of them
  were in `git ls-files`, so none of them were copied.

`/tmp/seatpass-build` and the screenshot paths in `VERIFY.md` and `DECISIONS.md` are
quoted verbatim, because both files are the record of a run and a quote of a scratch
path is evidence, not an instruction. That is stated once, with its reason, in the
repository's `.public-denylist`.

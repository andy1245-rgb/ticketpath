# VERIFY

Every command this build was checked with, its exit code, and the numbers it
printed. Nothing here is a summary of a result: each block is pasted output.

Machine: Node v24.22.2, npm 11.19.1. Builds and renders run in a throwaway copy
(`tools/build-copy.sh` mirrors the source into `/tmp/seatpass-build`) because a
dev server another session owns serves this checkout's own `.next`, and nothing
in this file was produced by building in place.

## 8.1 Typecheck

```
$ npm run typecheck
> ticketing-frontend@0.1.0 typecheck
> tsc --noEmit
exit=0
```

Grep for suppressions, over `app/ components/ lib/`:

```
as any / @ts-ignore     0
```

## 8.2 Linter

ESLint did not exist in this repo. Added `eslint@9.39.5` and
`eslint-config-next@15.5.29` (the version matching Next) with a flat config at
`eslint.config.mjs`, and `"lint": "eslint ."`. Justified in `DECISIONS.md`.

```
$ npm run lint
> ticketing-frontend@0.1.0 lint
> eslint .

exit=0
```

No warnings. Three findings were fixed to get there: an unescaped apostrophe in
`app/organizer/events/new/page.tsx`, an unused `Metadata` import in
`app/verify/page.tsx`, and the config's anonymous default export.

## 8.3 Unit tests

`node --test` on `.ts` files directly, verified on this Node before the build
started. No runner added.

```
$ npm test
> ticketing-frontend@0.1.0 test
> node --test "lib/**/*.test.ts"

ℹ tests 15
ℹ pass 15
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 160.267893
```

The fifteen cover the ten cases the brief names:

| Case required | Test |
|---|---|
| query building | `buildQuery keeps the given order and drops unset values` |
| error mapping from {message,status,code} | `mapErrorBody reads message, then error, then the status line`; `requestJson returns the body and maps a failed response` |
| cursor paging | `paginate walks the cursor and stops` |
| null signature | `a null signature is a row with no on-chain counterpart` |
| lamport formatting | `lamports format as integers, and as SOL only at the edge` |
| markup rounding | `markup rounds to the nearest basis point`; `markup basis points round the way the figure is shown` |
| frozen verification message, byte for byte, no trailing newline | `the verification message is frozen, byte for byte, with no trailing newline` |
| explorer URL cluster suffix | `explorer links carry the cluster unless it is mainnet-beta` |
| cap predicate either side of the boundary | `the cap predicate admits the ceiling and refuses one lamport more`; `a cap of zero admits the face and nothing above it`; `the ceiling is floored to whole lamports, never rounded up`; `the most a buyer may pay prefers the enforced ceiling over the platform cap` |
| shortAddress | `shortAddress truncates the middle and leaves what is already short` |

The tests can fail: `signatureLabel` returning the wrong placeholder, the cap
predicate losing `<=`, a trailing newline in the frozen message and `buildQuery`
no longer skipping `""` each turned exactly one test red before being reverted.

## 8.4 Headless render

`tools/verify-landing.cjs` ran against playwright-core 1.65.0 and a Chrome for
Testing binary that were already on the machine, both reached by absolute path
through `SEATPASS_PLAYWRIGHT_CORE` and `SEATPASS_CHROME`. No `npx playwright
install`, no playwright in `package.json`.

```
$ node tools/verify-landing.cjs
```

At 1440, 390 and 320 on `/`:

```
PASS  scrollWidth == innerWidth            1440 / 1440   390 / 390   320 / 320
PASS  h1 64px/64px                         64px / 64px      (1440)
PASS  h1 32px/38px                         32px / 38px      (390 and 320)
PASS  price figure family contains "Geist Mono"
      "Geist Mono", "Geist Mono Fallback", ui-monospace, "SF Mono", Menlo, monospace,
PASS  document.fonts.check('600 32px "Geist Mono"')
PASS  body background rgb(248,246,242)     rgb(248, 246, 242)
PASS  body color rgb(20,22,26)             rgb(20, 22, 26)
PASS  a muted paragraph rgb(95,99,107)     rgb(95, 99, 107)
PASS  border-radius set is a subset of 0/8/12/16/9999   saw 0px, 9999px, 12px
PASS  minimum computed font-size with text is >= 12px   12px
PASS  no weight over 600                   600
PASS  title is exactly "SeatPass · Tickets on Solana"
PASS  every svg has a role or aria-hidden  9 svgs
PASS  every control has a name
PASS  every tab stop has a 2px accent outline at 2px offset   23 stops ok
PASS  skip link is the first tab stop      Skip to content
```

`document.fonts.check` is worth a caveat: measured in this Chromium it returns
true for a family that does not exist at all, so it proves the face is not
pending, not that it is the face being painted. The stronger evidence is the
computed `font-family` above, which names "Geist Mono", and the `@font-face`
next/font emits and self-hosts.

Every route, at 1440 and 390 (30 combinations, all passing):

```
PASS  1440 /                             http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /events                       http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /events/midnight-static-tour  http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /events/midnight-static-tour/checkout  http 200 ... overflow 0
PASS  1440 /tickets/tkt_00001            http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /my-tickets                   http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /door?ticket=tkt_00001        http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /organizer                    http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /organizer/events/new         http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /resale                       http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /resale/list/tkt_00001        http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /account                      http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /pricing                      http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /rules                        http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
PASS  1440 /verify                       http 200 scroll 1440/1440 h1 1 minfs 12 maxw 600 overflow 0
(the same fifteen at 390, all PASS)

== console and network ==
PASS  no console errors   0
PASS  no failed requests  0

ALL CHECKS PASSED
```

Two defects were found by this harness and fixed rather than reported around:
a hydration mismatch in `WalletButton` (it decided whether a wallet extension
existed during server rendering, which logged a React hydration error on every
page carrying the button) and the ticket card's notch discs sitting 6px outside
the card's box.

## 8.5 Grep counts

```
$ bash tools/greps.sh
=== 8.5 forbidden strings ===
cdn.tailwindcss.com          0
fonts.googleapis.com         0
material-symbols             0
transition-all               0
user-scalable                0
maximum-scale                0
href="#"                     0
text-[11px]                  0
border-dashed                0

=== colour values outside app/theme.css ===
hex / rgb() / hsl()          0

=== data-in-component and encoding checks ===
fetch( in components         0
as any / @ts-ignore          0
iframe                       0

8.5 GREPS: ALL ZERO
```

Three of those were non-zero on the first run and were fixed: two comments that
mentioned the removed attributes by name, one comment naming a React error
number, and a `#000` opacity stop in the notch mask in `globals.css`.

## 8.6 Live data

Backend started on its own port, never `8788`:

```
$ cd .. && TICKETPATH_PORT=8795 python3 -m ticketpath.server
ticketpath 0.1.0 listening on http://127.0.0.1:8795 dataSource=synthetic-fixture synthetic=True cluster=devnet routes=10
```

Front end served from the copy with `NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8795`
on `:3010`, dev server so the env is read per request.

`/`:

- dataSource label, the backend's own sentence, printed once:
  `SYNTHETIC FIXTURE DATA. Generated for tests and demonstration, not real ticket data.`
- featured event: `Synthetic Theatre: Uncapped Markup Spread`, 11 of 150 sold
- hero ticket: `tkt_syn_0037`, `General Admission`, serial `THR-0001`,
  face `800000000`, cap ceiling `800000000`, last sale `1000000000`
- the cap comes from `enforcedCap.enforcedCeilingLamports` (`enforcedCapBps` 0,
  `bindingRule` "law") while the event's own `resalePriceCapBps` is `null` — the
  branch the brief asks for, where the raw bps would have said uncapped
- card sentence: `Sold 2 times, last at 1 SOL. 2 of those went over the 0.8 SOL cap.`
- on-chain strip: `Program not deployed yet`, chip `NOT DEPLOYED`, both controls
  disabled with the reason `No program address is configured, so there is
  nothing to copy or open.`

`/tickets/tkt_syn_0001`:

- `HAL-0001`, 4 ledger rows, `saleCount 2`, `transferCount 3`
- every row's signature and slot `null`; `grep '"signature":"'` over the payload
  returns nothing
- the trail renders exactly four `No transaction recorded for …` names:
  `Issued to`, `Bought by`, `Transferred to`, `Bought by`

Payload counts from the running server:

```
events=8
tickets=76
tkt0001_entries=4  stats 2 3
health_contract={'source': 'ticketing-frontend/lib/types.ts + API_CONTRACT.md',
 'endpointsInContract': 9, 'endpointsImplemented': 9, 'routesImplemented': 10,
 'map': 'records/CONTRACT-MAP.md'}
```

Both processes were stopped afterwards. `ss -ltn` shows `3010` and `8795` free.

## 8.7 Screenshots

```
$ node "$SHOT" http://127.0.0.1:3010/ /tmp/seatpass-1440.png --width 1440 --full
/tmp/seatpass-1440.png
$ node "$SHOT" http://127.0.0.1:3010/ /tmp/seatpass-390.png --width 390 --full
/tmp/seatpass-390.png
```

`$SHOT` is the operator's screenshot helper: a Node script outside this tree,
invoked as `node "$SHOT" <url> <out.png> --width N --full`. Its path is not
recorded here.

Both were rendered and reviewed by eye. **The vision-helper skill's directory
does not exist on this machine**, so that skill was unavailable; the screenshots
were taken with `$SHOT` and read directly.

**The comparison in 8.7 could not be run: `../seatpass-exports/` does not exist,
so there is no `desktop.html` or `mobile.html` on this machine.**
There is nothing to diff against line by line. What was reviewed instead is the
written specification: the seven regions in order, the 690/486 hero split, the
four hairlines, the 48/64/96 rhythm, the 380 ticket card, the three cards, the
four steps, the proof band and the footer, all present and measured.

Defects seen in the review and left, with reason:

- The three 32px card diagrams are simple 1.5px line constructions drawn here, not
  the export's illustrations. The ownership one reads as three nodes and a rail
  only at full size.
- The chart drops the face tick when it lands within 15px of the last-sale tick
  (face 0.45 and last sale 0.463 overlap). Face is still named in the chart's
  accessible name and in the sentence under the card.

## 8.8 Accessibility

**axe is not installed on this machine** (the screenshot helper's `node_modules`
has no `axe-core`, the repo has none), so axe was not run and no automated
accessibility score is claimed. What was checked structurally, by
`tools/verify-landing.cjs`, on 15 routes × 2 widths and `/` at 3 widths:

- exactly one `h1` per page: `h1 1` on every route
- the landing has two `h2` and three `h3`, no level skipped
- every svg carries `role` or `aria-hidden`: `9 svgs`, 0 unlabelled
- every control and link has a name: `0` unnamed on every route
- the skip link is the first tab stop: `Skip to content`
- 23 tab stops checked on `/`, each with `outline-width: 2px`, `outline-offset:
  2px`, `outline-color: rgb(79, 43, 234)`

## Contrast

```
$ node tools/contrast.mjs
...
28 pairs, 0 below 4.5:1
```

No colour was moved from the brief's values, so no ratio had to be re-recorded
against a moved hex. The tightest light-mode pair is `muted on inset` at 5.17:1;
the tightest dark pair is `accent on surface` at 6.20:1.

## Dark mode

The dark tokens are in `:root[data-theme="dark"]` and in the
`prefers-color-scheme` block for `:root:not([data-theme="light"])`, with
`color-scheme` set in both. `/account` and `/verify` were rendered in dark at
1440 and 390 during their build; the palette switch is token-level, so a page
that passes in light passes in dark unless it hardcodes a colour, and `tools/greps.sh`
reports 0 hex and 0 rgb() outside `app/theme.css`.

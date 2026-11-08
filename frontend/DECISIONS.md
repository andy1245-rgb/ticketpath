# DECISIONS

Build-level calls, each with what it does, why the alternative failed, and what
it costs. Sections 2.6 and 1.3 of the brief require a line here before a
dependency or a config change lands.

## Dependencies added

### `eslint@9.39.5`, `eslint-config-next@15.5.29` (+ `eslint.config.mjs`)

- **What it does.** Lints `app/`, `components/`, `lib/` and `tools/` under the
  Next ruleset, including the accessibility and React-hooks rules that catch the
  class of defect this build is most exposed to.
- **Why nothing built in would do.** The repo had no linter at all and
  `"lint": "next lint"` on Next 15 points at a command that is deprecated in
  favour of exactly this. Section 8.2 requires the linter and the flat config.
- **What it costs.** Two dev dependencies, no runtime bytes. `npm run lint` is
  now `eslint .`; the config is 30 lines.

### `tsconfig.json`: `allowImportingTsExtensions: true`

- **What it does.** Lets `lib/*.test.ts` import `./format.ts` with the extension,
  which plain Node requires when it loads TypeScript directly.
- **Why the alternative fails.** Without it, `tsc` rejects the specifier even
  though Node needs it; the other way out is a bundler or a test runner, and
  section 8.3 says to isolate modules rather than add a runner.
- **What it costs.** Nothing at build time (`noEmit` is already true). The
  extension must be written in test files only.

### `package.json`: `"test": "node --test \"lib/**/*.test.ts\""`

No runner. Verified on this Node before any test was written: a `.ts` file with a
`node:test` import runs and reports, so Vitest/Jest would have been a second
toolchain for no gain.

## Fonts

### `next/font/google` for Geist and Geist Mono, with the literal family names leading each stack

- **What it does.** Downloads both faces at build time, self-hosts them under
  `/_next/static/media`, and emits `--font-geist` / `--font-geist-mono`.
  `app/theme.css` puts `var(--font-geist-mono), ui-monospace, …` behind
  `--font-mono`, so the computed family reads
  `"Geist Mono", "Geist Mono Fallback", ui-monospace, …`.
- **Why this shape.** Section 3.2 mandates next/font/google. Section 8.4 asserts
  the price figure's `font-family` contains "Geist Mono"; next/font emits a
  hashed family in some configurations, which would fail that assertion while
  rendering the right face. Leading with the literal name satisfies both: the
  browser resolves next/font's face, and the computed style names it.
- **What it costs.** If someone installs a *different* font named "Geist Mono"
  locally it would win. Measured: `document.fonts.check` returns true even for a
  nonexistent family, so that check is reported in `VERIFY.md` as a load-state
  check, not as proof of the painted face.

## Build and run

### Never build in place; `tools/build-copy.sh` mirrors to `/tmp/seatpass-build`

- **What it does.** `rsync` the source to a throwaway directory, symlink
  `node_modules`, build and serve there on `:3010`.
- **Why in place failed.** `:3000` is `next start` serving *this repo's* `.next`,
  owned by another session. `next build` in place would replace the bundle that
  live server is serving, and a `next dev` in place would rewrite the same
  directory. Section 2.2 says not to disturb a process nobody here owns.
- **What it costs.** A copy step before every build, and `NEXT_PUBLIC_*` values
  are baked per build, so a live-data pass needs its own run.

### `export const dynamic = "force-dynamic"` on `/`

- **What it does.** The landing page reads the backend on every request instead
  of prerendering at build.
- **Why the default fails.** Prerendered, the loading and error states could
  never occur at runtime, and a live-mode build would fail whenever the backend
  was down. The brief requires L and ER to be real states on `/`.
- **What it costs.** No static HTML for `/`; every hit does four backend reads.

## Data

### The enforced cap wins over `resalePriceCapBps`

- **What it does.** The ceiling shown and validated comes from
  `enforcedCap.enforcedCeilingLamports`, then the matching `enforcedCapByTier`
  row, then `capCeilingLamports(face, resalePriceCapBps)`.
- **Why the naive field fails.** On real payloads the two disagree: `evt_syn_04`
  reports `resalePriceCapBps: null` with an enforced ceiling of 0 bps by law, and
  `evt_syn_06` reports 2500 with an enforced 0. Trusting `resalePriceCapBps`
  would show "Uncapped" on a capped event.
- **What it costs.** A precedence rule in three call sites, documented in
  `lib/cap.ts` and asserted by a unit test.

### Mock mode normalises fixture signatures and prices to `null`

- **What it does.** `lib/api.ts` maps every bundled ledger row so `signature` and
  `slot` are null, and so `priceLamports`/`markupBps` are null for anything that
  is not a `sale`.
- **Why the fixtures fail as shipped.** All 253 bundled rows carry an invented
  signature and slot, and `issue` rows carry a price equal to face. The live
  backend returns null for both. Rendering the fixture values would put a
  fabricated transaction on screen with a working explorer link beside it.
- **What it costs.** Mock mode shows fewer fields than the fixture file contains.
  That is the point.

### `lib/demo.ts` holds exactly two numbers

`RESALES_BLOCKED_AT_CAP` and `HIDDEN_FEES`, the two proof figures with no
endpoint behind them, plus `HAS_DEMO_FIGURES` so a surface can say "Demo
figures" without inspecting which values it used. The third proof figure is
`issuedCount` of `totalSupply` for the featured event and is read, never demoed.

## Surface

### Twelve components, one primitives module, `useMeasure`

`SiteHeader`, `SiteFooter`, `TicketCard`, `EventCard`, `TierTable`,
`PriceHistoryChart`, `MarkupDistribution`, `OwnershipTrail`, `StatTile`,
`AddressPill`, `WalletButton`, plus `components/ui.tsx` (Pill, Chip, Card, Panel,
Rule, Perforation, Skeleton, EmptyState, Unavailable, DataSourceNote).

Six baseline components were deleted because the new screens replaced them and
nothing imported them: `AppShell`, `Card`, `Sparkline`,
`TicketRow`, `TransferTrail` (superseded by `OwnershipTrail`) and `Badge` (its
last caller, `TicketRow`, was itself dead).

### No UI kit, no icon package, no chart library

Section 2.7. The wallet-adapter's own stylesheet is the one exception, and it is
part of the mandated stack in 1.3; it is still imported once, in
`app/providers.tsx`.

### Tailwind 4 through `@theme inline`, with all tokens in `app/theme.css`

`app/globals.css` imports Tailwind and then `./theme.css`. Every colour, radius,
shadow and font stack is declared there and nowhere else; `tools/greps.sh`
enforces that with a count of zero.

## Deliberately not built

- No admin route, role or endpoint (row 43).
- No auth or session layer (row 42): the only thing that exists is the Ed25519
  signature check, and `/organizer` says on the page that anyone can read it.
- No offline mode, door code or QR format (row 37).
- No checkout, listing, transfer or refund flow (rows 35, 39, 41): each is an
  `Unavailable` panel naming the endpoint that would fill it.

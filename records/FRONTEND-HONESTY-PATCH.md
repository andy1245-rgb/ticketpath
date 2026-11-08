# FRONTEND-HONESTY-PATCH — the diff that makes the screen true without a deployed program

**Written:** 2026-11-07T11:25Z.
**Scope:** `../ticketpath-demo` only (our copy; byte-identical to
`../ticketing-frontend` when the run started, checked with `diff -rq` excluding
`node_modules`/`.next`). The live tree was not written to, and `:3000` was not restarted:
it answered `200` before and after, same pid.
**Output:** `docs/frontend-honesty.patch` (14,290 bytes, sha256
`9cb9462ecdb3c29fa5cbb19e9d4dd0a350e9cc8a16ac8f43f9d6c61a172eb4c0`).
**Not done:** nothing committed, nothing pushed, no file written outside
`../ticketpath-demo` except this record and the patch.

---

## 0. The one command

From the frontend root (`../ticketpath-demo`, or the live tree if he releases it):

```
git apply ../ticketPricing/docs/frontend-honesty.patch
```

Apply from a clean tree. `git apply --check` first if he wants to see it pass before touching
anything. The patch is `-p1` (`a/` and `b/` prefixes) and was verified to apply to a clean
copy of the *original* files and to reproduce the patched copy byte for byte
(`diff -r` clean, all three trees).

---

## 1. What the patch does, in one paragraph

Two jobs only. **(a)** Every sentence that asserts chain enforcement is replaced with the
truth for a designed-but-not-deployed program: the rule is policy today, it is enforced by
the transfer hook once the program is deployed, and in this build it is simulated.
**(b)** The `dataSource` block our backend already puts on every payload is no longer
dropped by `lib/types.ts`; a new `SyntheticNotice` renders `dataSource.label` at the top of
every page that prints a fixture-derived number. In mock mode nothing changes, because the
bundled fixtures carry no `dataSource` and the existing "Mock data" banner still covers that
case. No component was redesigned, no dependency added, no behaviour changed: the only new
runtime work is reading keys that were already on the wire.

---

## 2. The inventory: every surface that renders a market number, a custody row, a mint address, or an enforcement claim

Quoted from the **original** files, before the patch. `.tsx` line numbers are pre-patch.

### Enforcement claims (all false in this build)

| # | File:line | Text |
|---|---|---|
| 1 | `app/events/[eventId]/page.tsx:162` | `"Destination wallet must be verified before a transfer will succeed."` |
| 2 | `app/events/[eventId]/page.tsx:167` | `` `Resale price is capped at +${.../100}% over face value, enforced at transfer time.` `` |
| 3 | `app/tickets/[ticketId]/page.tsx:158` | `{ticket.transferRestricted ? "Enforced on-chain" : "Not enforced"}` |
| 4 | `app/tickets/[ticketId]/page.tsx:140` | `<CardHeader title="On-chain" />` |
| 5 | `components/AppShell.tsx:73-74` | `Every transfer is recorded on-chain. Price and custody history is public for all issued tickets.` |
| 6 | `app/organizer/page.tsx:45-46` | `...computed from the on-chain transfer record.` |
| 7 | `app/verify/VerifyClient.tsx:88` | `Events with restricted transfers only issue to, and only accept transfers into, verified wallets.` |
| 8 | `app/verify/VerifyClient.tsx:160` | `Wallet verified. You can now receive transfers for restricted events.` |
| 9 | `components/EventCard.tsx:11,13` | `"Verified wallets only"`, `` `Resale capped at +X%` `` (a gate and a cap asserted on the landing page) |

### Market numbers

| # | File:line | Surface |
|---|---|---|
| 10 | `app/page.tsx:8` + `components/EventCard.tsx:41,45` | `From` price (`formatSol(minFace)`), `Issued` `formatPercent(sold)`, issuance meter |
| 11 | `app/events/[eventId]/page.tsx:65-84` | `Face value from`, `Tickets issued of N · %`, `Resold at least once`, `Average markup`, `cap +25%` |
| 12 | `app/events/[eventId]/page.tsx:100-112`, `app/organizer/page.tsx:104-120` | daily average resale price and `vs face` markup, `PriceHistoryChart` |
| 13 | `app/events/[eventId]/page.tsx:118` | `Showing N of M` |
| 14 | `app/events/[eventId]/page.tsx:135-149` | per-tier face, `issued / supply` |
| 15 | `components/TicketRow.tsx:26,31-34,38-41` | per-ticket price, `vs face`, hops, and `mint {shortAddress(...)}` |
| 16 | `app/tickets/[ticketId]/page.tsx:80-107` | `Face value`, `Last sale price`, `Peak price`, `Wallets held by` |
| 17 | `app/tickets/[ticketId]/page.tsx:120-124` | per-sale price points |
| 18 | `components/TransferTrail.tsx:61-71` | custody rows: `Resold 1.25 SOL +25% vs face`, wallet pills, timestamps |
| 19 | `app/tickets/[ticketId]/page.tsx:143-169` | `Mint address`, `Transfer restriction`, `Total resale volume`, `Redeemed` |
| 20 | `app/organizer/page.tsx:74-96,128+` | total volume, average markup, median price, resold %, markup buckets, destinations |

Every one of those prints on a route that also renders a payload our backend stamps with
`dataSource.synthetic = true`. That is why one notice per page is enough: the label lands on
the same screen as the numbers, above them.

---

## 3. Each changed file, before and after

### 3.1 `lib/types.ts` — the key the client was throwing away

Before: no `dataSource` type anywhere. `Page<T>`, `Event`, `ResaleHistory` and
`EventAnalytics` described only the fields the components happened to use, so the block the
backend sends on every response (`{mode, synthetic, label, note}`) existed on the wire and
nowhere in the app.

After:

```ts
export interface DataSource {
  mode: string;
  synthetic: boolean;
  label: string;
  note?: string;
}
```
plus `dataSource?: DataSource;` on `Page<T>`, `Event`, `ResaleHistory` and `EventAnalytics`
(optional, because the bundled `lib/mock` fixtures do not carry it).

Why it is more honest: nothing downstream can render a field the type does not admit, and
`optional` is the honest shape — the fixtures genuinely have no provenance block, so mock
mode keeps showing no provenance notice and lets the existing banner do that job.

### 3.2 `components/SyntheticNotice.tsx` — new, 17 lines

```tsx
export function SyntheticNotice({ dataSource }: { dataSource?: DataSource | null }) {
  if (!dataSource?.synthetic) return null;
  return (
    <p className="rounded-lg border border-hairline bg-plane px-4 py-2 text-xs text-ink-2">
      {dataSource.label} No ticket program is deployed for this build, so every price and custody
      row here is simulated.
    </p>
  );
}
```

On our backend the rendered sentence is:

```
SYNTHETIC FIXTURE DATA. Hand-authored for tests, not real ticket data. No ticket program is
deployed for this build, so every price and custody row here is simulated.
```

Why it is more honest: the first half is the backend's own words, not the frontend's
characterisation of them, and it disappears by itself if a real ledger is ever served
(`synthetic: false`). The second half says the thing the mock banner used to say and that
wiring the backend had deleted.

### 3.3 `app/page.tsx:8` — the event grid

Before: `const { items: events } = await getEvents();`
After: `const { items: events, dataSource } = await getEvents();` and
`<div className="mb-6"><SyntheticNotice dataSource={dataSource} /></div>` between the header
and the cards.

Why: six `From` prices and six `Issued %` figures were the first numbers a judge sees, with
the label only inside the event names.

### 3.4 `app/events/[eventId]/page.tsx`

| Line | Before | After |
|---|---|---|
| 32 | `const [{ items: tickets }, analytics] = await Promise.all([...])` | `const [{ items: tickets, dataSource }, analytics] = ...` |
| after 62 | (nothing) | `<SyntheticNotice dataSource={dataSource ?? event.dataSource} />` |
| 162 | `"Destination wallet must be verified before a transfer will succeed."` | `"Verified wallets only, by policy. Enforced by the transfer hook once the program is deployed; simulated in this build."` |
| 167 | `` `Resale price is capped at +${cap}% over face value, enforced at transfer time.` `` | `` `Resale price is capped at +${cap}% over face value by policy. Enforced by the transfer hook once the program is deployed; simulated in this build.` `` |

Why: the old sentences were future-tense claims about a program that does not exist, on the
page with four market figures above them. The new ones keep the product story (there *is* a
cap, verification *is* required) and state where enforcement actually lives and that it is
simulated here. `dataSource ?? event.dataSource` reads the block off whichever payload this
page got first, so the notice survives a backend that omits it on one of the two calls.

### 3.5 `app/tickets/[ticketId]/page.tsx`

| Line | Before | After |
|---|---|---|
| after 77 | (nothing) | `<SyntheticNotice dataSource={history.dataSource ?? event?.dataSource} />` |
| 140 | `<CardHeader title="On-chain" />` | `<CardHeader title="On-chain (simulated)" subtitle="The mint address is a fixture placeholder: no account exists on any cluster and no transaction backs these rows." />` |
| 158 | `{ticket.transferRestricted ? "Enforced on-chain" : "Not enforced"}` | `{ticket.transferRestricted ? "Enforced by the transfer hook once the program is deployed" : "Not enforced — no program is deployed"}` |

Why: this is the page most likely to be screenshotted, and per
`records/FRONTEND-INTEGRATION.md` §4 it was the weakest labelled screen in the app — its only
label was a back-link in the top-left. "On-chain" was the single most false heading in the
product, sitting directly above a `FXTURE…` address that links to a Solana Explorer 404.

### 3.6 `app/organizer/page.tsx`

| Line | Before | After |
|---|---|---|
| 19 | `const { items: events } = await getEvents({ limit: 100 });` | `const { items: events, dataSource } = ...` |
| 45-46 | `...computed from the on-chain transfer record.` | `...computed from the recorded custody ledger. In this build that ledger is simulated: no ticket program is deployed.` |
| after 48 | (nothing) | `<SyntheticNotice dataSource={analytics.dataSource ?? dataSource} />` |

Why: "computed from the on-chain transfer record" is the one sentence on the analytics page
that claims a provenance for every figure under it, and there is no chain record.

### 3.7 `app/my-tickets/MyTicketsClient.tsx`

Before: `ticketPage.dataSource` was fetched and dropped; the only label on a holdings list of
prices was the sample-wallet note in mock mode.
After: `DataSource` imported, `const [source, setSource] = useState<DataSource | null>(null)`,
`setSource(ticketPage.dataSource ?? null)` on load, `<SyntheticNotice dataSource={source} />`
under the header.

Why: without a wallet this page shows no numbers at all, so nothing is needed there; with a
wallet it shows per-ticket price, markup and hops, and in live mode it showed none of the
provenance.

### 3.8 `app/verify/VerifyClient.tsx`

| Line | Before | After |
|---|---|---|
| 88 | `...verified wallets.` | `...verified wallets once the ticket program is deployed.` |
| 160 | `Wallet verified. You can now receive transfers for restricted events.` | `Wallet verified. You can now receive transfers for restricted events once the ticket program is deployed.` |

Why: the Ed25519 verification on this page is the only genuinely real cryptographic result in
the app, and it should not be softened. The two sentences around it were the only place the
UI promised a transfer *would be accepted*, which nothing enforces yet.

### 3.9 `components/AppShell.tsx:73-74` — the footer

Before:
```
Every transfer is recorded on-chain. Price and custody history is public for all issued
tickets.
```
After:
```
Every transfer is recorded in a custody ledger, and price and custody history is public for
all issued tickets. On-chain recording starts when the ticket program is deployed; in this
build the ledger is simulated.
```

Why: this was static text on every route, and the one false claim no payload could fix.

### 3.10 `components/EventCard.tsx:11,13`

Before: `rules.push("Verified wallets only")`, `` rules.push(`Resale capped at +X%`) ``
After: `"Verified wallets only (policy)"`, `` `Resale capped at +X% (policy)` ``

Why: on the landing page those two chips read as facts about the transfer path. They are
policy, and now they say so, in two words, with no change to layout.

---

## 4. Verification actually run, and on what surface

| Check | Result |
|---|---|
| Baseline `npx next build` on the untouched copy | exit 0, 8 routes, `/` and `/my-tickets` static |
| `npx tsc --noEmit` after the patch | exit 0, no output |
| `npx next build` after the patch, mock mode | exit 0, same 8 routes, same static/dynamic split — the patch adds no request and no dynamic route |
| `npx next build` after the patch with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8788` | exit 0 |
| `next start -p 3100` against the running backend on `:8788`, `GET /`, `/events/fixture-hall-session`, `/tickets/tkt_fixture_0001`, `/organizer` | all `200`; each page's HTML contains `SYNTHETIC FIXTURE DATA. Hand-authored for tests, not real ticket data. No ticket program is deployed for this build...` exactly once; the old "Mock data" banner is **absent**; footer, `On-chain (simulated)`, `Not enforced — no program is deployed`, `Verified wallets only (policy) · Resale capped at +25% (policy)` and both transfer-rule sentences all present in the served HTML |
| `next start -p 3101` in mock mode | `200`, "Mock data" banner present, no provenance notice — the fixtures carry no `dataSource`, which is the correct behaviour and not a regression |
| `git apply --check` on a clean copy of the original files | all 10 file entries check; full apply reproduces `../ticketpath-demo` byte for byte |
| `../ticketing-frontend` | never written; the live frontend answered `200` throughout, same process |

Both test servers were started on demand, used, and killed; `:3100` and `:3101` are free
again. The `:8788` backend was already running and was only read.

**What this does not prove.** Nothing about the chain. There is no program, so no claim on
any of these pages became verifiable — they became *accurate*, which is a different and
smaller thing.

---

## 5. The one change I was not sure about, left out

**Driving the "no program is deployed" sentence from the payload instead of hardcoding it.**

The backend already knows the answer. `ticketpath/adapters/rpc_adapter.py:44` returns
`{mintAddress, enforced: false, checked: false, reason: "no_program_id" | "not_deployed" |
"rpc_disabled", detail: "no transfer-hook program is deployed by this project on any
cluster", cluster}`. But `orchestrator.py::_ticket_payload` passes only `enforcement["enforced"]`
into `Ticket.transferRestricted`, so the reason string never reaches the browser. The frontend
therefore cannot distinguish "no program deployed" from "deployed but this mint is
unrestricted", and the patch states the first in fixed text.

That is true today and false the day the program is deployed. The honest fix is a payload
field (`Ticket.enforcement = {checked, reason}` or a `dataSource.chain` block) and a
component that renders the sentence from it; that is a backend and contract change, not a
frontend text change, so it is out of scope for this diff and is left out on purpose. Until
it exists, **whoever deploys the program must also delete the five hardcoded
"once the program is deployed; simulated in this build" clauses** — they are in
`app/events/[eventId]/page.tsx` (×2), `app/tickets/[ticketId]/page.tsx` (×2, plus the card
subtitle), `app/organizer/page.tsx`, `components/AppShell.tsx` and `app/verify/VerifyClient.tsx`
(×2). The `dataSource.label` half of the notice needs no such edit: it is already
payload-driven and will vanish on its own.

Second thing I considered and did not do, recorded so it is not mistaken for an oversight:
the mint address is still a live `explorer.solana.com` link that 404s (and in mock mode all
13 fixture addresses still truncate to `FXTU…1111`). Unlinking it is a behaviour change, and
fixing the truncation is a fixture edit in `ticketpath` (`fixtures/synthetic_store.json`), not
a frontend text change. The patch warns about the placeholder in the card subtitle instead.

---

## 6. The claim that cannot be made honest without a deployed program

**"Mint address" on `/tickets/[ticketId]`.** Every other false claim in the app is a sentence,
and a sentence can be corrected. This one is an identifier that is presented as an SPL mint
and hyperlinked to a chain explorer where it does not exist. No wording makes a 404 resolve:
only a deployed program with a real mint account, or removing the link and the word "mint",
can. The patch labels it a fixture placeholder and stops there.

---

## 7. Numbers for the summary

- Patch: `../ticketPricing/docs/frontend-honesty.patch`, 14,290 bytes, 320 lines,
  sha256 `9cb9462ecdb3c29fa5cbb19e9d4dd0a350e9cc8a16ac8f43f9d6c61a172eb4c0`.
- Files touched: 11 (10 existing + 1 new) — `lib/types.ts`, `components/SyntheticNotice.tsx`
  (new), `components/AppShell.tsx`, `components/EventCard.tsx`, `app/page.tsx`,
  `app/events/[eventId]/page.tsx`, `app/tickets/[ticketId]/page.tsx`, `app/organizer/page.tsx`,
  `app/my-tickets/MyTicketsClient.tsx`, `app/verify/VerifyClient.tsx`.
- Lines changed: +68 / −16.
- Decision for the operator: apply it to `../ticketpath-demo` (ours, safe) or to
  `../ticketing-frontend` (his, needs his explicit yes and a `:3000` restart to take
  effect only if he also sets the env var — the patch itself needs no restart beyond the
  normal rebuild).

---

## CORRECTION (2026-11-08T08:30Z): a machine handle redacted, no claim changed

**Scope:** this file only, and only the last row of the results table. **Why:** this repository is
public and `tools/public_safety.py` refuses a tracked file that carries a process id or a port tied
to a running process. The rule and its reason are in `.public-denylist`.

**What the redaction costs: nothing that was measured.** The row's job is to say that the live
tree was never written to and that the live frontend kept answering `200` for the whole pass, and
it still says both. The pid was only the handle for "the same one throughout", which the row now
says in words.

| Where | Was | Now |
|---|---|---|
| results table, `../ticketing-frontend` row | a tied port and `same pid <n>` | "the live frontend answered `200` throughout, same process" |

**Residue, stated rather than hidden.** Port numbers on lines this rule does not classify are
unchanged. `.public-denylist` states why it does not deny those, and `/tmp` paths are exempt for
`records/` on purpose. `python3 tools/public_safety.py check --tracked` reports zero hits for this
file as of this note.

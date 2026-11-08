import { AddressPill } from "@/components/AddressPill";
import { TicketCard } from "@/components/TicketCard";
import { Chip, DataSourceNote, Panel, Pill, Rule } from "@/components/ui";
import { getDevnetRecord, getEvents, getResaleHistory, getTickets } from "@/lib/api";
import { capCeilingLamports } from "@/lib/cap";
import { formatDate, formatDateTime, formatLamports } from "@/lib/format";
import DEV from "@/data/devnet-artefacts.json";
import { PROGRAM_ID, explorerProgramUrl } from "@/lib/solana";

/*
 * The landing screen. Seven regions in the export's order: the header and the
 * footer belong to app/layout.tsx, so this file renders regions 2 to 6 and
 * nothing between them.
 *
 * Server component on purpose: it is the only thing that calls lib/api, and no
 * component below it fetches. A thrown ApiError is not caught here; it reaches
 * app/error.tsx, because a page that could not read the backend must not draw a
 * success state.
 */

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

/**
 * The event the hero card shows, named rather than taken by chance.
 *
 * It used to be `onSale[0]`, which landed on whichever event sorted first and
 * once landed on an event called "Uncapped Markup Spread" whose own caption
 * reported two sales above its cap. The first frame of the film is the one
 * place a reader learns what the product is.
 *
 * The slug below is NOT in `lib/mock/events.json`. That is deliberate as a
 * fallback path, not as a pin: `find()` misses, so the card renders
 * `onSale[0]`, which is currently "Winter Chamber Series: Night III" (cap 5000
 * bps, tiers at 0.45 and 1.1 SOL). An earlier version of this comment claimed
 * the pinned event carried the same face and cap as the devnet record on
 * /rules. It does not, and no event in the fixture does: the recorded run is
 * `evt_syn_02` at 2500 bps on 1 SOL of face. The strip below the card says so
 * in its own words, because the two records are different.
 *
 * To pin the card honestly, put a real slug here and check its cap against the
 * copy beside it. A missing event must not blank the page, so the fallback
 * stays.
 */
const HERO_EVENT_SLUG = "synthetic-hall-cap-not-binding";

/**
 * The two program ids, spelled out where the strip can print them.
 *
 * v1 signed the recorded artefact run printed below, and is the id
 * `records/devnet-artefacts.json` carries. v2 is deployed on devnet under its
 * own id and is written up in docs/ON-CHAIN-DESIGN.md and
 * records/onchain-v2-devnet.json; it adds the floor, the jurisdiction, the
 * policy, the hold clock and the band. It is not the program that produced the
 * admitted and refused transfers printed here, and saying so is the point.
 */
const PROGRAM_V1 = "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva";
const PROGRAM_V2 = "Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF";

/**
 * The two reads that need the featured event's id, in order. Returns null when
 * the event has no ticket at all, so the caller can say so instead of drawing a
 * card with invented content.
 */
async function loadHero(featured: { id: string }) {
  const { items: tickets } = await getTickets({ eventId: featured.id, limit: 1 });
  const ticket = tickets[0];
  if (!ticket) return null;
  const history = await getResaleHistory(ticket.id);
  return { ticket, history };
}

/**
 * A ceiling carried by a payload that the TypeScript shape calls required but
 * the live backend may omit: a tier with no cap arrives as `{tierId,
 * enforcedCap: null}` rather than the four flat fields. Read it as unknown and
 * narrow, so nothing here needs a cast.
 */
function ceilingOf(record: unknown): number | null {
  if (typeof record !== "object" || record === null) return null;
  if (!("enforcedCeilingLamports" in record)) return null;
  const value = record.enforcedCeilingLamports;
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

/**
 * The cap that would actually be enforced on this ticket: the event-wide
 * record, then the matching per-tier row, then the contract's own arithmetic on
 * the ticket's face. Null only when the event is genuinely uncapped.
 */
function heroCapCeiling(
  featured: {
    resalePriceCapBps: number | null;
    enforcedCap?: unknown;
    enforcedCapByTier?: ReadonlyArray<{ tierId: string } | null> | null;
  },
  ticket: { tierId: string; faceValueLamports: number },
): number | null {
  const eventWide = ceilingOf(featured.enforcedCap);
  if (eventWide !== null) return eventWide;

  const row = featured.enforcedCapByTier?.find((tier) => tier?.tierId === ticket.tierId);
  const tierCeiling = ceilingOf(row);
  if (tierCeiling !== null) return tierCeiling;

  if (featured.resalePriceCapBps == null) return null;
  return capCeilingLamports(ticket.faceValueLamports, featured.resalePriceCapBps);
}

// ---------------------------------------------------------------------------
// Decorative art. Every one of these is a drawing, so every one is hidden from
// the accessibility tree: the words beside it carry the meaning.
// ---------------------------------------------------------------------------

/** No account needed: a person, drawn at 20px on a 1.5px stroke. */
function IconNoAccount() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" focusable="false">
      <circle cx="10" cy="6.5" r="3" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M4 16.5c0-2.6 2.7-4.5 6-4.5s6 1.9 6 4.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Capped resale: a price rising to a line it cannot pass. */
function IconCap() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" focusable="false">
      <path d="M3 5.5h14" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M10 16.5V8.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path
        d="m7 11.5 3-3 3 3"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Runs with no backend, on fixtures: arcs and a slash, no invented offline mode. */
function IconNoSignal() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" focusable="false">
      <path d="M6.6 14.2a4.8 4.8 0 0 1 6.8 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <path d="M3.8 11.2a8.8 8.8 0 0 1 12.4 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="10" cy="17.3" r="1" fill="currentColor" />
      <path d="M3.6 3.6 16.4 16.4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

/** The copy glyph, used only where the control is present but cannot act. */
function IconCopy() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true" focusable="false">
      <rect x="7.5" y="7.5" width="9" height="9" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path
        d="M12.5 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v5.5a2 2 0 0 0 2 2h2"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** Card one: a price line over its axis. */
function DiagramPriceHistory() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      focusable="false"
      className="text-ink"
    >
      <path
        d="M6 5v21h21"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M9.5 20.5 16 16l7-7.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="23" cy="8.5" r="1.6" fill="currentColor" />
    </svg>
  );
}

/** Card two: one block, and the ceiling it cannot pass. */
function DiagramCap() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      focusable="false"
      className="text-ink"
    >
      <path
        d="M4 8h24M4 8v3.5M28 8v3.5"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M10 27V14h12v13"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

/** Card three: the custody rail, a node per owner, the current one filled. */
function DiagramOwnership() {
  return (
    <svg
      width="32"
      height="32"
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      focusable="false"
      className="text-ink"
    >
      <path d="M7 10.4v3.2M7 18.4v3.2" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="7" cy="8" r="2.4" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="7" cy="16" r="2.4" stroke="currentColor" strokeWidth="1.5" />
      <circle cx="7" cy="24" r="2.4" fill="currentColor" />
      <path
        d="M12 8h13M12 16h9M12 24h15"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

/** One of the three cards under "Why this ticket is different". */
function FeatureCard({
  title,
  copy,
  diagram,
}: {
  title: string;
  copy: string;
  diagram: React.ReactNode;
}) {
  return (
    <div className="rounded-card border border-control bg-surface p-6">
      {diagram}
      <h3 className="t-meta mt-6 text-ink">{title}</h3>
      <p className="t-body mt-2 text-muted">{copy}</p>
    </div>
  );
}

/** The proof figure at the export's 32/38, weight 600, tabular. */
const PROOF_FIGURE =
  "figure text-[32px] leading-[38px] font-semibold tracking-[-0.02em] text-ink";

/** The four steps, as the export writes them. Demo copy: see NOTES.md. */
const STEPS: ReadonlyArray<{ numeral: string; copy: string; missing: string }> = [
  {
    numeral: "01",
    copy: "Pick your seat",
    missing: "there is no seat map, only tiers.",
  },
  {
    numeral: "02",
    copy: "Pay with card or Apple Pay",
    missing: "no checkout, payment or settlement endpoint.",
  },
  {
    numeral: "03",
    copy: "The ticket lands in a wallet we made you",
    missing: "nothing in the app creates a wallet.",
  },
  {
    numeral: "04",
    copy: "Show the code at the door.",
    missing: "no door code is issued, and there is no offline mode: a lookup needs the network.",
  },
];

// ---------------------------------------------------------------------------
// The page
// ---------------------------------------------------------------------------

/**
 * Prerendered once, at build time. This deployment is a static export: Next
 * writes plain HTML into `out/`, no process serves it, and there is no request
 * to read a query string from. `force-static` is what that means. Every read
 * below happens during the build, against the bundled fixtures and the one
 * record file, and the panels say which instant that was: app/loading.tsx and
 * app/error.tsx cannot come into play, because nothing renders at request time.
 */
export const dynamic = "force-static";

export default async function HomePage() {
  // The three reads, in the order the screen needs them. The event list is wide
  // enough to find the pinned event, and the artefact read is what the program
  // strip prints: a configured id is not a record of anything.
  const [{ items: onSale, dataSource }, devnet] = await Promise.all([
    getEvents({ status: "on_sale", limit: 50 }),
    getDevnetRecord().catch(() => null),
  ]);
  const featured =
    onSale.find((event) => event.slug === HERO_EVENT_SLUG) ?? onSale[0] ?? null;
  const hero = featured ? await loadHero(featured) : null;
  const artefact = devnet?.loaded ? devnet.record : null;
  // The record's own id wins over the build's configured one: the strip says
  // what a verified run wrote, and falls back to configuration only when there
  // is no record to read.
  const programId = artefact?.programId ?? PROGRAM_ID;

  const capCeiling =
    featured && hero ? heroCapCeiling(featured, hero.ticket) : null;
  const explorerUrl = artefact?.explorer?.program ?? explorerProgramUrl();

  // How many resales the recorded run refused. The artefact holds a single
  // refusal row, and a missing record prints an em dash rather than a zero,
  // because "nothing was refused" and "nothing was read" are different
  // statements. The demo constant it replaces said 3, a number no record held.
  const refusedCount = artefact ? (artefact.transfers?.refusedOverCap ? 1 : 0) : null;

  // Only sales are a price paid, and the chart reads them oldest first.
  const points = hero
    ? hero.history.entries
        .filter((entry) => entry.kind === "sale")
        .sort((a, b) => a.occurredAt.localeCompare(b.occurredAt))
        .map((entry) => ({
          label: formatDate(entry.occurredAt),
          priceLamports: entry.priceLamports,
        }))
    : [];

  // The hero's left column is static copy, so it is written once and rendered
  // in both the populated and the empty state.
  const heroCopy = (
    <div>
      <p className="t-micro-caps text-muted">TICKETS ON SOLANA</p>
      <h1 className="h-display mt-4 text-ink">
        The markup has
        <br />
        a ceiling.
      </h1>
      <p className="t-deck mt-6 max-w-[350px] text-muted">
        One face value, one cap. Prices come from the resale record; this build renders the record, not the model. The
        devnet program refuses anything above a cap when the organiser sets one (6010).
      </p>
      <div className="mt-8 flex flex-wrap items-center gap-3">
        <Pill href="/demo" variant="primary">
          Try the demo: buy, then break the cap
        </Pill>
        <Pill href="/rules" variant="secondary">
          How the cap works
        </Pill>
      </div>
      <div className="mt-8 flex flex-wrap items-center gap-x-3 gap-y-2">
        {/* A wallet is required to buy: checkout asks for a connected one and,
            on some events, a verified one. "No account needed" read as "no
            sign-up of any kind", which the checkout page contradicts. */}
        <span className="inline-flex items-center gap-2 t-meta text-ink">
          <IconNoAccount />
          No email account needed
        </span>
        <span aria-hidden="true" className="h-4 w-px bg-line" />
        <span className="inline-flex items-center gap-2 t-meta text-ink">
          <IconCap />
          Capped resale
        </span>
        <span aria-hidden="true" className="h-4 w-px bg-line" />
        <span className="inline-flex items-center gap-2 t-meta text-ink">
          <IconNoSignal />
          Runs with no backend, on fixtures
        </span>
      </div>
    </div>
  );

  return (
    <>
      {/* 2. HERO: 690 + 24 + 486 = 1200, vertical centres on one line. */}
      <section className="box pt-24">
        <div className="grid grid-cols-1 gap-12 md:grid-cols-[minmax(0,1fr)_380px] md:items-center md:gap-8 min-[1200px]:grid-cols-[minmax(0,690px)_minmax(0,486px)] min-[1200px]:gap-6">
          {heroCopy}

          {/* The card's right edge sits on the content box's right edge at 1440. */}
          <div className="md:justify-self-end">
            {featured && hero ? (
              <TicketCard
                eventName={featured.name}
                startsAt={featured.startsAt}
                tierName={
                  featured.tiers.find((tier) => tier.id === hero.ticket.tierId)?.name ?? "Not listed"
                }
                serial={hero.ticket.serial}
                faceValueLamports={hero.ticket.faceValueLamports}
                capCeilingLamports={capCeiling}
                lastSaleLamports={hero.history.stats.lastPriceLamports}
                points={points}
                entries={hero.history.entries}
              />
            ) : featured ? (
              <Panel>
                <p className="t-body text-ink">No ticket is on record for this event yet.</p>
                <p className="t-body mt-2 text-muted">
                  The card needs one real ticket to show. This event has none, so nothing is drawn
                  in its place.
                </p>
                <div className="mt-6">
                  <Pill href="/events" variant="secondary">
                    Browse events
                  </Pill>
                </div>
              </Panel>
            ) : (
              <Panel>
                <p className="t-body text-ink">No event is on sale right now.</p>
                <p className="t-body mt-2 text-muted">
                  The events page lists every published event, not only the ones on sale.
                </p>
                <div className="mt-6">
                  <Pill href="/events" variant="secondary">
                    Browse events
                  </Pill>
                </div>
              </Panel>
            )}
          </div>
        </div>
      </section>

      {/* The bundled-fixture label, above the fold. It used to be one 12px line
          at the very foot of the page, after six screens of venues, dates and
          wallet addresses, so a reader who stopped at the hero was never told
          what they were looking at. */}
      <div className="box mt-6">
        <DataSourceNote dataSource={dataSource} />
      </div>

      {/* 3. ON-CHAIN STRIP: its own band, one hairline above it, one line. */}
      <section className="mt-24">
        <Rule />
        <div className="box">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 py-6">
            <span className="t-meta text-muted">Program</span>

            {programId ? (
              <AddressPill address={programId} label="program" />
            ) : (
              <>
                <span className="t-meta text-ink">not deployed yet</span>
                <button
                  type="button"
                  disabled
                  aria-disabled="true"
                  aria-label="Copy program address"
                  aria-describedby="program-reason"
                  className="inline-flex h-11 w-11 items-center justify-center rounded-pill text-muted"
                >
                  <IconCopy />
                </button>
              </>
            )}

            {/* The chip is what the artefact records, never a configured id and
                never the build's `programDeployed`, which is false because the
                build asks no cluster: a `false` there means "not read". */}
            <Chip tone="neutral">
              {artefact ? `Deployed on ${artefact.cluster ?? "devnet"}` : "No record"}
            </Chip>

            {explorerUrl ? (
              <a
                href={explorerUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="u-transition t-meta inline-flex h-6 items-center whitespace-nowrap text-ink underline decoration-1 underline-offset-2 hover:text-accent"
              >
                View on explorer
              </a>
            ) : (
              <>
                <button
                  type="button"
                  disabled
                  aria-disabled="true"
                  aria-describedby="program-reason"
                  className="t-meta inline-flex h-6 items-center whitespace-nowrap text-muted"
                >
                  View on explorer
                </button>
                <span id="program-reason" className="t-micro text-muted">
                  No program address is configured, so there is nothing to copy or open.
                </span>
              </>
            )}
          </div>
          {artefact && (
            <div className="t-micro pb-6 text-muted">
              <p>
                Deployed on {artefact.cluster ?? "devnet"}. Read from the recorded artefact file at
                build time, not from a cluster. The two transactions on the Solana explorer:
              </p>
              <ul className="mt-2 grid gap-1">
                <li className="break-all">
                  Accepted, {formatLamports(DEV.transfers.acceptedAtCap.priceLamports)} lamports
                  (1.25 SOL, exactly the ceiling), slot {formatLamports(DEV.transfers.acceptedAtCap.slot)}:{" "}
                  <a className="underline" target="_blank" rel="noopener noreferrer" href={DEV.transfers.acceptedAtCap.explorer}>
                    {DEV.transfers.acceptedAtCap.signature}
                  </a>
                </li>
                <li className="break-all">
                  Refused with 6010 E_CAP_EXCEEDED, {formatLamports(DEV.transfers.refusedOverCap.priceLamports)} lamports
                  (one lamport over), slot {formatLamports(DEV.transfers.refusedOverCap.slot)}:{" "}
                  <a className="underline" target="_blank" rel="noopener noreferrer" href={DEV.transfers.refusedOverCap.explorer}>
                    {DEV.transfers.refusedOverCap.signature}
                  </a>
                </li>
              </ul>
            </div>
          )}
          {/* Two records sit next to each other on this screen and they do not
              describe the same event: the strip above is the recorded devnet
              run on `evt_syn_02` (2500 bps over 1 SOL of face), and the card
              higher up is a bundled fixture with its own cap. Nothing used to
              separate them, so the strip read as the card's proof. It is not. */}
          <p className="t-micro pb-6 text-muted">
            Recorded run: event <span className="figure">{artefact?.eventId ?? "not recorded"}</span>{" "}
            with the v1 program <span className="figure">{artefact?.programId ?? PROGRAM_V1}</span>, capped at{" "}
            {artefact?.capBps ?? "an unrecorded"} bps over a{" "}
            {artefact?.faceLamports !== undefined ? formatLamports(artefact.faceLamports) : "an unrecorded"}{" "}
            face. That is a different event from the ticket card above, which carries its own cap
            and its own face. The v2 program is <span className="figure">{PROGRAM_V2}</span>; the
            recorded admitted and refused transfers below came from v1, because that is the id the
            artefact file holds.
          </p>
        </div>
      </section>

      {/* 4. WHY THIS TICKET IS DIFFERENT. */}
      <section className="mt-24">
        <div className="box">
          <h2 className="h-section text-ink">Why this ticket is different</h2>
          <ul className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            <li>
              <FeatureCard
                diagram={<DiagramPriceHistory />}
                title="Price history, per ticket"
                copy="Every sale this ticket has been through, at the price it actually paid."
              />
            </li>
            <li>
              <FeatureCard
                diagram={<DiagramCap />}
                title="A cap that is a rule, not a promise"
                copy="The contract admits no price where price*10000 > face*(10000+cap_bps)."
              />
            </li>
            <li>
              <FeatureCard
                diagram={<DiagramOwnership />}
                title="Ownership you can read"
                copy="Every wallet that has held this ticket, with the transaction behind it."
              />
            </li>
          </ul>
        </div>
      </section>

      {/* 5. HOW BUYING WORKS. */}
      <section className="mt-24">
        <div className="box">
          {/* "How buying works" was four promises in the present tense: there
              is no seat map, no payment step (capabilities.purchase is false),
              nothing that creates a wallet, and no door code or service worker
              (capabilities.doorCode is false, and public/ holds only charts/).
              The heading is conditional now and every step says what is not
              built, so the film does not sell a checkout that does not exist. */}
          <h2 className="h-section text-ink">How buying would work</h2>
          <p className="t-body mt-4 max-w-[60ch] text-muted">
            None of the four steps below is built. Each one names the thing that is missing, so a
            reader can tell the design from the build.
          </p>
          <ol className="mt-12 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {STEPS.map((step) => (
              <li key={step.numeral}>
                <p className="figure t-meta text-muted">{step.numeral}</p>
                <p className="t-body mt-2 text-ink">{step.copy}</p>
                <p className="t-micro mt-2 text-muted">Not built: {step.missing}</p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* 6. PROOF BAND. No featured event means no band: the first figure is the
          one number here that is real. */}
      {featured && (
        <section className="mt-24" aria-labelledby="proof-band-title">
          {/* The three figures are display type with no heading and no
              landmark, so a screen reader met "3 / resales blocked at the cap"
              as body text after the step list. The heading is sr-only: the
              design has no visible title here, and adding one would change the
              layout to fix a reading-order problem. */}
          <h2 id="proof-band-title" className="sr-only">
            What the record and the fixture show
          </h2>
          <Rule />
          <div className="box py-24">
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-3">
              <div>
                {/* "issued", not "sold": a ticket that exists has not
                    necessarily been paid for, and every other surface in the
                    app says issued. */}
                <p className={PROOF_FIGURE}>
                  {featured.issuedCount.toLocaleString("en-US")} of{" "}
                  {featured.totalSupply.toLocaleString("en-US")} issued
                </p>
                <p className="t-meta truncate text-muted" title={featured.name}>
                  {featured.name}. Bundled fixture.
                </p>
              </div>
              <div>
                {/* The figure used to be the demo constant 3. The one record a
                    verified run wrote holds exactly one refusal, so 3 was a
                    number nothing on this machine produced. */}
                <p className={PROOF_FIGURE}>
                  {refusedCount === null ? "—" : refusedCount.toLocaleString("en-US")}
                </p>
                <p className="t-meta text-muted">
                  {refusedCount === null
                    ? "resale refusals: no devnet record to count"
                    : "resale refused over the cap on devnet, 6010 E_CAP_EXCEEDED"}
                </p>
              </div>
              <div>
                <p className={PROOF_FIGURE}>2 legs</p>
                <p className="t-meta text-muted">seller-paid on resale in the demo: artist fee and flip tax, no buyer-side fee</p>
              </div>
            </div>
            <p className="t-micro mt-6 text-muted">
              The cap figure is the recorded devnet run. The issued count is the bundled fixture.
              The two legs are transcribed rules in the browser demo, not in the deployed v1 program.
            </p>
          </div>
          <Rule />
        </section>
      )}

      {/* The backend's own label, once, from the events envelope. */}
      <div className="box mt-6">
        <DataSourceNote dataSource={dataSource} />
      </div>
    </>
  );
}

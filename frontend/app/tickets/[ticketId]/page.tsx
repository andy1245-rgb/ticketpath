import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getEvent, getResaleHistory, getTicket } from "@/lib/api";
import { capabilities } from "@/lib/capabilities";
import type { Capability } from "@/lib/capabilities";
import type { Event, TicketStatus } from "@/lib/types";
import { AddressPill } from "@/components/AddressPill";
import { OwnershipTrail } from "@/components/OwnershipTrail";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { StatRow, StatTile } from "@/components/StatTile";
import { Chip, DataSourceNote, EmptyState, Unavailable } from "@/components/ui";
import { formatCompact, formatDateTime, formatMarkup, formatSol } from "@/lib/format";

export const metadata = { title: "Ticket" };

/**
 * A ticket's own status, as the shared chip. Warning is reserved for the cap,
 * so no status uses it.
 */
const STATUS: Record<
  TicketStatus,
  { label: string; tone: "positive" | "neutral" | "accent" | "danger" }
> = {
  valid: { label: "Valid", tone: "positive" },
  listed: { label: "Listed", tone: "accent" },
  redeemed: { label: "Redeemed", tone: "neutral" },
  revoked: { label: "Revoked", tone: "danger" },
};

/**
 * The ceiling the contract would admit against for this ticket's own tier.
 *
 * The cap is a multiple of each tier's face value, so an event-wide number is
 * wrong the moment two tiers differ. Per-tier wins; the event-level record is
 * the fallback; nothing means null, which the chart reads as uncapped rather
 * than a number this file invented (brief 5.5, 6.1b row 24).
 */
function capCeilingFor(event: Event | null, tierId: string): number | null {
  if (!event) return null;

  const tier = event.enforcedCapByTier?.find((row) => row.tierId === tierId);
  // A tier with no ceiling at all can arrive without the field, so it is read
  // as a number or not at all.
  if (tier && typeof tier.enforcedCeilingLamports === "number") {
    return tier.enforcedCeilingLamports;
  }

  const eventWide = event.enforcedCap;
  if (eventWide && typeof eventWide.enforcedCeilingLamports === "number") {
    return eventWide.enforcedCeilingLamports;
  }

  return null;
}

/** One hairline row of the record: the field name, then the field itself. */
function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-line py-3">
      <dt className="t-micro-caps text-muted">{label}</dt>
      <dd className="t-meta min-w-0 text-ink">{children}</dd>
    </div>
  );
}

/**
 * Transfer and refund share one panel: both are one missing write path on the
 * same ticket, and the panel names both endpoints. The copy is the canonical
 * capabilities entries, joined, never rewritten.
 */
const TRANSFER_AND_REFUND: Capability = {
  available: false,
  missing: `${capabilities.transfers.missing} ${capabilities.refunds.missing}`,
  endpoint: `${capabilities.transfers.endpoint}; ${capabilities.refunds.endpoint}`,
  shows: `${capabilities.transfers.shows} ${capabilities.refunds.shows}`,
};

export default async function TicketPage({
  params,
}: {
  params: Promise<{ ticketId: string }>;
}) {
  const { ticketId } = await params;

  // getTicket resolves either a ticket id or a mint address. A 404 is the
  // not-found page; anything else is a failure the error boundary must see.
  const ticket = await getTicket(ticketId).catch((error: unknown) => {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  });

  const [history, event] = await Promise.all([
    getResaleHistory(ticket.id),
    getEvent(ticket.eventId).catch((error: unknown) => {
      // A ticket whose event cannot be read is a real state — the record above
      // still stands. Any other failure belongs on the error boundary.
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    }),
  ]);

  const ticketStatus = STATUS[ticket.status];
  const { stats } = history;
  const capCeiling = capCeilingFor(event, ticket.tierId);
  const hasLedger = history.entries.length > 0;

  // One ticket resells a handful of times, so each sale is its own point on the
  // plot rather than a daily average.
  const points = history.entries
    .filter((entry) => entry.kind === "sale" && entry.priceLamports != null)
    .map((entry) => ({
      label: entry.occurredAt.slice(0, 10),
      priceLamports: entry.priceLamports,
    }));

  return (
    <div className="box py-12">
      <div className="space-y-12">
        <header>
          {/* The serial names the record and the event names where it belongs,
              so the event is the link back to its own page rather than a
              second copy of the same words above the heading. */}
          <h1 className="h-section flex flex-wrap items-baseline gap-x-3 gap-y-1">
            <span className="figure">Ticket {ticket.serial}</span>
            {event && (
              <Link
                href={`/events/${event.slug}`}
                className="u-transition t-meta font-medium text-muted underline decoration-1 underline-offset-2 hover:text-ink"
              >
                {event.name}
              </Link>
            )}
          </h1>

          <div className="mt-3 flex flex-wrap items-center gap-3">
            <Chip tone={ticketStatus.tone}>{ticketStatus.label}</Chip>
            <AddressPill address={ticket.ownerWallet} label="current owner" />
          </div>

          {!event && (
            <p className="t-meta mt-3 text-muted">
              The event this ticket belongs to could not be read.
            </p>
          )}

          <div className="mt-4">
            <DataSourceNote dataSource={ticket.dataSource} />
          </div>
        </header>

        <section>
          <h2 className="h-section">Record</h2>
          <dl className="mt-6 border-t border-line">
            <Row label="Serial">
              <span className="figure">{ticket.serial}</span>
            </Row>
            <Row label="Status">{ticketStatus.label}</Row>
            <Row label="Face value">
              <span className="figure">{formatSol(ticket.faceValueLamports)}</span>
            </Row>
            <Row label="Last sale price">
              {ticket.lastSalePriceLamports == null ? (
                "Never resold"
              ) : (
                <span className="figure">{formatSol(ticket.lastSalePriceLamports)}</span>
              )}
            </Row>
            <Row label="Transfer count">
              <span className="figure">{formatCompact(ticket.transferCount)}</span>
            </Row>
            <Row label="Issued">
              <span className="figure">{formatDateTime(ticket.issuedAt)}</span>
            </Row>
            <Row label="Redeemed">
              {ticket.redeemedAt == null ? (
                "Not redeemed"
              ) : (
                <span className="figure">{formatDateTime(ticket.redeemedAt)}</span>
              )}
            </Row>
            <Row label="Owner">
              <AddressPill address={ticket.ownerWallet} label="current owner" />
            </Row>
            <Row label="Issued to">
              <AddressPill address={ticket.issuedToWallet} label="issuing wallet" />
            </Row>
            <Row label="Transfers">
              {ticket.transferRestricted ? "Restricted" : "Not restricted"}
            </Row>
          </dl>
        </section>

        {hasLedger ? (
          <>
            <section>
              <h2 className="h-section">Ownership trail</h2>
              <p className="t-meta mt-2 text-muted">
                Every wallet this ticket has passed through, oldest first.
              </p>
              <div className="mt-6">
                <OwnershipTrail
                  entries={history.entries}
                  faceValueLamports={history.faceValueLamports}
                  variant="full"
                />
              </div>
            </section>

            <section>
              <h2 className="h-section">Price history</h2>
              <p className="t-meta mt-2 text-muted">
                Every price this ticket has sold for, against its face value.
              </p>
              <div className="mt-6">
                <PriceHistoryChart
                  points={points}
                  faceValueLamports={history.faceValueLamports}
                  capCeilingLamports={capCeiling}
                  lastSaleLamports={history.stats.lastPriceLamports}
                  variant="page"
                />
              </div>
            </section>

            <section>
              <h2 className="h-section">Resale record</h2>
              <div className="mt-6">
                <StatRow>
                <StatTile label="Sales" value={formatCompact(stats.saleCount)} />
                <StatTile label="Transfers" value={formatCompact(stats.transferCount)} />
                <StatTile label="Average markup" value={formatMarkup(stats.avgMarkupBps)} />
                <StatTile label="Peak price" value={formatSol(stats.peakPriceLamports)} />
                <StatTile
                  label="Last sale"
                  value={formatSol(stats.lastPriceLamports)}
                  note={stats.lastPriceLamports == null ? "Never resold" : undefined}
                />
                <StatTile label="Total volume" value={formatSol(stats.totalVolumeLamports)} />
                <StatTile label="Wallets held" value={formatCompact(stats.uniqueWallets)} />
                </StatRow>
              </div>
            </section>
          </>
        ) : (
          // A ticket with no ledger rows is not the not-found state: the record
          // above is real and the ticket exists. There is simply nothing to
          // draw, and an empty rail would read as a loading failure.
          <EmptyState
            title="No ledger entries for this ticket"
            body="The ticket exists and the record above is what the backend holds. No issue, sale, transfer or redemption has been recorded against it, so there is no ownership trail, no price history and no resale total to show."
          />
        )}

        <div className="space-y-6">
          <Unavailable title="Door code" capability={capabilities.doorCode} />

          {/* The listing form has no control here. It was a button on this page
              that opened a form nothing can submit, and an unavailable panel
              that names the missing endpoint is the honest shape: a control
              that only leads to it is a promise on screen. */}
          <Unavailable title="List for resale" capability={capabilities.listings} />

          <Unavailable title="Transfer and refund" capability={TRANSFER_AND_REFUND} />
        </div>
      </div>
    </div>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getEvent, getEventAnalytics, getEvents, getTickets } from "@/lib/api";
import { TierTable } from "@/components/TierTable";
import { StatRow, StatTile } from "@/components/StatTile";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { MarkupDistribution } from "@/components/MarkupDistribution";
import { AddressPill } from "@/components/AddressPill";
import { Chip, DataSourceNote, Panel, Pill } from "@/components/ui";
import {
  formatBpsPercent,
  formatCeiling,
  formatCompact,
  formatDateTime,
  formatMarkup,
  formatPercent,
  formatSol,
} from "@/lib/format";
import type { EnforcedCapTier, EventStatus, TicketStatus } from "@/lib/types";

/**
 * One event, everything the record holds: the policy and the ceiling the
 * contract computes, the tiers, the tickets that exist, and the resale
 * figures. The route parameter is the slug; `getEvent` accepts an id as well,
 * so it is passed through unchanged and a live 404 becomes the not-found page.
 */

const EVENT_STATUS: Record<
  EventStatus,
  { label: string; tone: "neutral" | "positive" | "accent" | "danger" }
> = {
  draft: { label: "Draft", tone: "neutral" },
  on_sale: { label: "On sale", tone: "positive" },
  sold_out: { label: "Sold out", tone: "accent" },
  completed: { label: "Completed", tone: "neutral" },
  cancelled: { label: "Cancelled", tone: "danger" },
};

const TICKET_STATUS: Record<
  TicketStatus,
  { label: string; tone: "neutral" | "positive" | "accent" | "danger" }
> = {
  valid: { label: "Valid", tone: "positive" },
  listed: { label: "Listed", tone: "accent" },
  redeemed: { label: "Redeemed", tone: "neutral" },
  revoked: { label: "Revoked", tone: "danger" },
};

/**
 * Static export: the build has to know every event URL up front, because there
 * is no server to answer /events/<slug> at request time. The list comes from
 * the same lib/api the page reads, so the exported set is exactly the set the
 * fixtures (or a live backend at build time) actually hold.
 */
export async function generateStaticParams(): Promise<Array<{ slug: string }>> {
  const { items } = await getEvents({ limit: 1000 });
  return items.map((event) => ({ slug: event.slug }));
}

/** With no server, any other slug is a 404 the host serves, not a page to render. */
export const dynamicParams = false;

export default async function EventPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let event;
  try {
    event = await getEvent(slug);
  } catch (error) {
    // A real 404 is a page, not a panel: the event does not exist.
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const [{ items: tickets }, analytics] = await Promise.all([
    getTickets({ eventId: event.id, limit: 25 }),
    getEventAnalytics(event.id),
  ]);

  const status = EVENT_STATUS[event.status];
  const enforced = event.enforcedCap ?? null;

  // The ceiling the contract holds, per tier. An event-wide figure is emitted
  // only when every tier resolves to the same number, and a cap expressed in
  // basis points over different faces almost never does; so when `enforcedCap`
  // is absent the per-tier rows are the only honest shape. The summary below is
  // computed from those rows, never from `resalePriceCapBps`: the platform
  // percentage is what the organiser configured, and a law can make the
  // admitted ceiling smaller (`ticketpath/core/event_records.py` forbids a
  // screen from displaying a cap the chain will not hold).
  const tierRows = (event.enforcedCapByTier ?? []).filter(
    (row): row is EnforcedCapTier =>
      row != null &&
      typeof row.enforcedCeilingLamports === "number" &&
      typeof row.enforcedCapBps === "number",
  );
  const ceilings = tierRows.map((row) => row.enforcedCeilingLamports);
  const minCeiling = ceilings.length ? Math.min(...ceilings) : null;
  const maxCeiling = ceilings.length ? Math.max(...ceilings) : null;
  const tierBps = new Set(tierRows.map((row) => row.enforcedCapBps));
  const tierRules = new Set(tierRows.map((row) => row.bindingRule));
  const uniformBps = tierBps.size === 1 ? [...tierBps][0] : null;
  const uniformRule = tierRules.size === 1 ? [...tierRules][0] : null;

  const capAdmitted = enforced
    ? formatCeiling(enforced.enforcedCeilingLamports)
    : uniformBps !== null
      ? `${formatBpsPercent(uniformBps)} over face, per tier`
      : tierRows.length > 0
        ? `${formatCeiling(minCeiling)} to ${formatCeiling(maxCeiling)} by tier`
        : event.resalePriceCapBps != null
          ? `${formatBpsPercent(event.resalePriceCapBps)} over face`
          : "Uncapped";
  const capSource = enforced
    ? "enforcedCap.enforcedCeilingLamports"
    : tierRows.length > 0
      ? "enforcedCapByTier"
      : "resalePriceCapBps";
  const capRule = enforced
    ? enforced.bindingRule === "law"
      ? "Binding rule: law"
      : "Binding rule: platform cap"
    : uniformRule
      ? uniformRule === "law"
        ? "Binding rule: law"
        : "Binding rule: platform cap"
      : tierRows.length > 0
        ? "Binding rule: differs by tier, see the tiers below"
        : null;

  // One line the chart can draw, and only when it is true for every tier: a
  // ceiling drawn at the loosest tier would sit above the stricter ones.
  const chartCeiling =
    enforced?.enforcedCeilingLamports ??
    (uniformBps !== null && minCeiling === maxCeiling ? minCeiling : null);

  return (
    <div className="box py-16">
      <Link href="/events" className="u-transition t-meta text-muted hover:text-ink">
        {"\u2190 "}All events
      </Link>

      <header className="mt-6">
        <h1 className="h-section">{event.name}</h1>
        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-3">
          <span className="t-meta text-muted">
            {event.venue} · {event.city}
          </span>
          <span className="figure t-meta text-ink">{formatDateTime(event.startsAt)}</span>
          <Chip tone={status.tone}>{status.label}</Chip>
          <span className="figure t-meta text-ink">
            {formatCompact(event.issuedCount)} of {formatCompact(event.totalSupply)} issued
          </span>
        </div>
      </header>

      <section className="mt-12" aria-labelledby="policy-heading">
        <h2 id="policy-heading" className="h-section">
          Resale policy and tiers
        </h2>

        <dl className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          <div className="border-t border-line pt-4">
            <dt className="t-micro-caps text-muted">Resale allowed</dt>
            <dd className="t-body mt-2 text-ink">{event.resaleEnabled ? "Yes" : "No"}</dd>
            <dd className="figure t-micro mt-1 text-muted">resaleEnabled</dd>
          </div>

          <div className="border-t border-line pt-4">
            <dt className="t-micro-caps text-muted">Resale cap, event policy</dt>
            <dd className="figure t-body mt-2 text-ink">
              {event.resalePriceCapBps == null ? "Uncapped" : formatBpsPercent(event.resalePriceCapBps)}
            </dd>
            <dd className="figure t-micro mt-1 text-muted">resalePriceCapBps</dd>
          </div>

          <div className="border-t border-line pt-4">
            <dt className="t-micro-caps text-muted">Cap the contract admits</dt>
            <dd className="figure t-body mt-2 text-ink">{capAdmitted}</dd>
            <dd className="figure t-micro mt-1 text-muted">{capSource}</dd>
            {capRule && <dd className="t-micro mt-1 text-muted">{capRule}</dd>}
          </div>

          <div className="border-t border-line pt-4">
            <dt className="t-micro-caps text-muted">Verified wallet required</dt>
            <dd className="t-body mt-2 text-ink">{event.requiresVerifiedWallet ? "Yes" : "No"}</dd>
            <dd className="figure t-micro mt-1 text-muted">requiresVerifiedWallet</dd>
          </div>
        </dl>

        {/* The table carries screen-reader text positioned absolutely inside a
            horizontally scrolled box; the wrapper gives it a containing block
            and clips it, so a wide table cannot widen the document at 390. */}
        <div className="relative mt-6 overflow-hidden">
          <TierTable tiers={event.tiers} enforcedCapByTier={event.enforcedCapByTier} />
        </div>
      </section>

      <section className="mt-12" aria-labelledby="tickets-heading">
        <h2 id="tickets-heading" className="h-section">
          Issued tickets
        </h2>
        <p className="t-meta mt-1 text-muted">
          Showing {formatCompact(tickets.length)} of {formatCompact(event.issuedCount)} issued
          tickets.
        </p>

        {tickets.length === 0 ? (
          <p className="t-body mt-6 text-muted">No tickets have been issued for this event yet.</p>
        ) : (
          <ul className="mt-6 border-t border-line">
            {tickets.map((ticket) => {
              const ticketStatus = TICKET_STATUS[ticket.status];
              return (
                <li
                  key={ticket.id}
                  className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3 border-b border-line py-4"
                >
                  <span className="figure t-meta min-w-24 text-ink">{ticket.serial}</span>
                  <Chip tone={ticketStatus.tone}>{ticketStatus.label}</Chip>
                  <span className="figure t-meta text-ink">{formatSol(ticket.faceValueLamports)}</span>
                  <Link
                    href={`/tickets/${ticket.id}`}
                    className="u-transition t-meta text-muted underline underline-offset-2 hover:text-ink"
                  >
                    View ticket {ticket.serial}
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="mt-12" aria-labelledby="analytics-heading">
        <h2 id="analytics-heading" className="h-section">
          Resale analytics
        </h2>

        <div className="mt-6">
          <StatRow>
            <StatTile
              label="Volume"
              value={formatSol(analytics.totalVolumeLamports)}
              note={`${formatCompact(analytics.saleCount)} resales recorded`}
            />
            <StatTile label="Resales" value={formatCompact(analytics.saleCount)} />
            <StatTile label="Average markup" value={formatMarkup(analytics.avgMarkupBps)} />
            <StatTile
              label="Median resale"
              value={formatSol(analytics.medianResalePriceLamports)}
              note={`face from ${formatSol(analytics.faceValueLamports)}`}
            />
            <StatTile label="Resold at least once" value={formatPercent(analytics.resoldShare)} />
            <StatTile label="Holders" value={formatCompact(analytics.uniqueHolders)} />
          </StatRow>
        </div>

        {analytics.analyticsNote && (
          <p className="t-micro mt-6 text-muted">{analytics.analyticsNote}</p>
        )}

        <h3 className="h-event mt-12">Price over time</h3>
        <Panel className="mt-4">
          <PriceHistoryChart
            variant="page"
            points={analytics.priceSeries.map((point) => ({
              label: point.date,
              priceLamports: point.avgPriceLamports,
            }))}
            faceValueLamports={analytics.faceValueLamports}
            capCeilingLamports={chartCeiling}
            lastSaleLamports={analytics.medianResalePriceLamports}
          />
        </Panel>

        <h3 className="h-event mt-12">Markup distribution</h3>
        <Panel className="mt-4">
          <MarkupDistribution buckets={analytics.markupDistribution} />
        </Panel>

        <h3 className="h-event mt-12">Where tickets ended up</h3>
        <p className="t-meta mt-1 text-muted">
          A region is recorded only when a wallet volunteers one, so a dash means that wallet has
          not shared it.
        </p>

        {analytics.topDestinations.length === 0 ? (
          <p className="t-body mt-4 text-muted">No holder wallets are recorded for this event.</p>
        ) : (
          <div className="relative mt-4 overflow-x-auto rounded-panel border border-line bg-surface">
            <table className="w-full border-collapse">
              <caption className="sr-only">
                Destination wallets for this event, up to twelve rows: the wallet, the region it
                volunteered, how many tickets it holds and whether it acquired on the secondary
                market.
              </caption>
              <thead>
                <tr className="border-b border-line">
                  <th scope="col" className="t-micro-caps px-6 py-3 text-left text-muted">
                    Wallet
                  </th>
                  <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-left text-muted">
                    Region
                  </th>
                  <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-right text-muted">
                    Tickets
                  </th>
                  <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-left text-muted">
                    Acquired
                  </th>
                </tr>
              </thead>
              <tbody>
                {analytics.topDestinations.slice(0, 12).map((row) => (
                  <tr key={row.wallet} className="border-b border-line last:border-0">
                    <td className="px-6 py-4">
                      <AddressPill address={row.wallet} />
                    </td>
                    <td className="t-meta px-6 py-4 text-muted">
                      {row.region ?? (
                        <>
                          <span aria-hidden="true">{"\u2014"}</span>
                          <span className="sr-only">No region volunteered</span>
                        </>
                      )}
                    </td>
                    <td className="figure t-meta px-6 py-4 text-right text-ink">{row.ticketCount}</td>
                    <td className="t-meta px-6 py-4 text-ink">
                      {row.acquiredOnSecondary ? "Secondary" : "Primary"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <div className="mt-12">
        <Pill href={`/events/${event.slug}/checkout`} variant="primary">
          Open checkout
        </Pill>
      </div>

      <div className="mt-12">
        <DataSourceNote dataSource={analytics.dataSource} />
      </div>
    </div>
  );
}

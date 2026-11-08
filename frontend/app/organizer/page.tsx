import Link from "next/link";
import { getEventAnalytics, getEvents } from "@/lib/api";
import { AddressPill } from "@/components/AddressPill";
import { MarkupDistribution } from "@/components/MarkupDistribution";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { StatRow, StatTile } from "@/components/StatTile";
import { DataSourceNote, Panel } from "@/components/ui";
import { formatCompact, formatDate, formatMarkup, formatPercent, formatSol } from "@/lib/format";

export const metadata = { title: "For organizers" };

/** The backend caps this table at twelve rows; the screen never lengthens it. */
const MAX_DESTINATIONS = 12;

/**
 * What one event's resale record looks like, for whoever asks for the URL.
 *
 * There is no authorization anywhere in this build (inventory row 42), so the
 * page says that out loud rather than implying a private dashboard. Every
 * figure comes from `getEventAnalytics`; nothing here is computed on the page
 * except the choice of which event to show.
 */
export default async function OrganizerPage({
  searchParams,
}: {
  searchParams: Promise<{ event?: string }>;
}) {
  const { event: requestedId } = await searchParams;
  const events = await getEvents({ limit: 100 });

  // E, first kind: there are no events at all, so there is nothing to measure.
  if (events.items.length === 0) {
    return (
      <div className="box pt-16">
        <header>
          <h1 className="h-display">For organizers</h1>
          <p className="t-deck mt-6 max-w-3xl text-ink">
            This screen has no authorization: there is no account, no session and no role in this
            build, so anyone who can reach the URL sees it.
          </p>
        </header>

        <section className="mt-12">
          <h2 className="h-section">No events to report on</h2>
          <p className="t-body mt-2 max-w-3xl text-muted">
            The backend returned no events, so there is no record to compute analytics from. This
            is not a set of zero figures; no event exists to measure.
          </p>
        </section>
      </div>
    );
  }

  const matched = events.items.find((event) => event.id === requestedId) ?? null;
  const selected = matched ?? events.items[0];
  const analytics = await getEventAnalytics(selected.id);

  const hasSales = analytics.saleCount > 0 || analytics.priceSeries.length > 0;
  const hasHolders = analytics.topDestinations.length > 0 || analytics.uniqueHolders > 0;
  const destinations = analytics.topDestinations.slice(0, MAX_DESTINATIONS);

  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">For organizers</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          This screen has no authorization: there is no account, no session and no role in this
          build, so anyone who can reach the URL sees it.
        </p>
      </header>

      <nav aria-label="Select an event" className="mt-12">
        <p className="t-micro-caps text-muted">Event</p>
        <ul className="mt-3 flex flex-wrap gap-2">
          {events.items.map((event) => {
            const active = event.id === selected.id;
            return (
              <li key={event.id}>
                <Link
                  href={`/organizer?event=${event.id}`}
                  aria-current={active ? "true" : undefined}
                  className={`u-transition inline-flex h-10 items-center rounded-pill border px-4 t-meta ${
                    active
                      ? "border-accent bg-accent text-on-accent hover:border-accent-press hover:bg-accent-press"
                      : "border-control bg-surface text-ink hover:border-ink"
                  }`}
                >
                  {event.name}
                </Link>
              </li>
            );
          })}
        </ul>
        {requestedId && !matched && (
          <p className="t-micro mt-3 text-muted">
            No event with that id is in the list, so the first event is shown.
          </p>
        )}
      </nav>

      <section className="mt-12" aria-labelledby="selected-event">
        <h2 id="selected-event" className="h-section">
          {selected.name}
        </h2>
        <p className="t-meta mt-2 text-muted">
          {selected.venue}, {selected.city} · starts {formatDate(selected.startsAt)} · face from{" "}
          <span className="figure text-ink">{formatSol(analytics.faceValueLamports)}</span>
        </p>
      </section>

      {!hasSales ? (
        <section className="mt-8" aria-labelledby="no-sales">
          <Panel>
            <p className="t-micro-caps text-muted">No sales yet</p>
            <h3 id="no-sales" className="h-section mt-2">
              This event has no resale rows
            </h3>
            <p className="t-body mt-2 max-w-3xl text-muted">
              {hasHolders
                ? "No sale has been recorded against this event, so the volume, median, average markup and resold share would all print zero. A zero here would look like a measurement and is not one, so the figures and the six buckets are not drawn. The holders below come from issue and transfer records, which do exist."
                : "The analytics record for this event is empty: no sales, no price series and no holders. An empty record is not a set of zeroes, so no figure is drawn."}
            </p>
          </Panel>
        </section>
      ) : (
        <>
          <section className="mt-12" aria-labelledby="figures">
            <h2 id="figures" className="h-section">
              Resale record
            </h2>
            <div className="mt-6">
              <StatRow>
                <StatTile
                  label="Resale volume"
                  value={formatSol(analytics.totalVolumeLamports)}
                  note={`${formatCompact(analytics.saleCount)} sale${analytics.saleCount === 1 ? "" : "s"} recorded`}
                />
                <StatTile
                  label="Sales"
                  value={formatCompact(analytics.saleCount)}
                  note="Ledger entries of kind sale"
                />
                <StatTile
                  label="Average markup"
                  value={formatMarkup(analytics.avgMarkupBps)}
                  note="Each sale against its own ticket's face"
                />
                <StatTile
                  label="Median resale price"
                  value={formatSol(analytics.medianResalePriceLamports)}
                  note={`Face from ${formatSol(analytics.faceValueLamports)}`}
                />
                <StatTile
                  label="Resold share"
                  value={formatPercent(analytics.resoldShare)}
                  note="Issued tickets resold at least once"
                />
                <StatTile
                  label="Holders"
                  value={formatCompact(analytics.uniqueHolders)}
                  note="Distinct wallets that have held a ticket"
                />
              </StatRow>
            </div>
          </section>

          <section className="mt-12" aria-labelledby="series">
            <h2 id="series" className="h-section">
              Resale price over time
            </h2>
            <p className="t-meta mt-2 text-muted">
              Average price paid per day, bucketed in UTC, for {selected.name}.
            </p>
            <Panel className="mt-4">
              <PriceHistoryChart
                variant="page"
                points={analytics.priceSeries.map((point) => ({
                  label: point.date,
                  priceLamports: point.avgPriceLamports,
                }))}
                faceValueLamports={analytics.faceValueLamports}
                capCeilingLamports={null}
                lastSaleLamports={analytics.medianResalePriceLamports}
              />
            </Panel>
          </section>

          <section className="mt-12" aria-labelledby="buckets">
            <h2 id="buckets" className="h-section">
              Markup distribution
            </h2>
            <p className="t-meta mt-2 text-muted">
              How far over face value tickets changed hands. All six buckets are shown, including
              the ones nothing landed in.
            </p>
            <Panel className="mt-4">
              <MarkupDistribution buckets={analytics.markupDistribution} />
            </Panel>
          </section>
        </>
      )}

      <section className="mt-12" aria-labelledby="destinations">
        <h2 id="destinations" className="h-section">
          Where tickets ended up
        </h2>
        <p className="t-meta mt-2 max-w-3xl text-muted">
          Up to {MAX_DESTINATIONS} holding wallets, by ticket count. A region is only populated when
          a wallet volunteered one, so a dash means that wallet has not shared one.
        </p>

        {destinations.length === 0 ? (
          <Panel className="mt-4">
            <p className="t-body text-muted">
              No holders are recorded for this event, so there is no destination to list.
            </p>
          </Panel>
        ) : (
          /* `relative` makes this panel the containing block for the cells' clipped
             screen-reader text, so the panel's own overflow clips it too. */
          <Panel className="relative mt-4 overflow-x-auto">
            <table className="w-full border-collapse">
              <caption className="sr-only">
                Holding wallets for {selected.name}, up to {MAX_DESTINATIONS} rows: the wallet, how
                many tickets it holds, whether it acquired them on the secondary market, and the
                region it volunteered.
              </caption>
              <thead>
                <tr className="border-b border-line">
                  <th scope="col" className="t-micro-caps py-3 pr-4 text-left text-muted">
                    Wallet
                  </th>
                  <th scope="col" className="t-micro-caps py-3 pr-4 text-right text-muted">
                    Tickets
                  </th>
                  <th scope="col" className="t-micro-caps py-3 pr-4 text-left text-muted">
                    Acquired on secondary
                  </th>
                  <th scope="col" className="t-micro-caps py-3 text-left text-muted">
                    Region
                  </th>
                </tr>
              </thead>
              <tbody>
                {destinations.map((row) => (
                  <tr key={row.wallet} className="border-b border-line last:border-b-0">
                    <td className="py-3 pr-4">
                      <AddressPill address={row.wallet} />
                    </td>
                    <td className="figure t-meta py-3 pr-4 text-right text-ink">
                      {row.ticketCount}
                    </td>
                    <td className="t-meta py-3 pr-4 text-ink">
                      {row.acquiredOnSecondary ? "Yes" : "No"}
                    </td>
                    <td className="t-meta py-3 text-ink">
                      {row.region ?? (
                        <>
                          <span aria-hidden="true">{"\u2014"}</span>
                          <span className="sr-only">No region volunteered</span>
                        </>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        )}
      </section>

      <div className="mt-12">
        <DataSourceNote dataSource={analytics.dataSource ?? events.dataSource} />
      </div>
    </div>
  );
}

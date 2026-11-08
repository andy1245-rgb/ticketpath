import Link from "next/link";
import { getEventAnalytics, getEvents } from "@/lib/api";
import { AddressPill } from "@/components/AddressPill";
import { MarkupDistribution } from "@/components/MarkupDistribution";
import { PriceHistoryChart } from "@/components/PriceHistoryChart";
import { StatRow, StatTile } from "@/components/StatTile";
import { Chip, DataSourceNote, Panel } from "@/components/ui";
import { formatCompact, formatDate, formatMarkup, formatPercent, formatSol } from "@/lib/format";
import { bpsLabel } from "@/lib/demoState";
import { RESALE_MODE_LABEL, resaleModeOf } from "@/lib/resaleMode";
import type { Event } from "@/lib/types";

/**
 * The export renders this route once, so `?event=` is read from the request at
 * build time and the page serves one resale record in full. The remaining
 * navigation is in-page: every event gets a section here, and the events table
 * links to it with an anchor that survives the export, unlike a query string.
 */
export const dynamic = "force-static";

export const metadata = { title: "Organiser — events and resale record" };

/** The backend caps this table at twelve rows; the screen never lengthens it. */
const MAX_DESTINATIONS = 12;

function ruleValue(value: string | null | undefined): string {
  return value == null || value === "" ? "not computed for this event" : value;
}

/**
 * The event's own resale rule, from fields the payload already carries:
 * `resaleEnabled`, `resalePriceCapBps` and `enforcedCap`. An organiser has to be
 * able to see that their event is capped at zero or has resale switched off
 * without opening the buyer side.
 */
function EventRule({ event }: { event: Event }) {
  const mode = resaleModeOf(event.resaleEnabled);
  const cap = event.resalePriceCapBps == null ? "no cap (tracked, not limited)" : bpsLabel(event.resalePriceCapBps);
  const enforced = event.enforcedCap;

  return (
    <Panel className="mt-4">
      <p className="t-micro-caps text-muted">Event rule</p>
      <dl className="mt-3 grid gap-2 sm:grid-cols-2">
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Resale mode</dt>
          <dd className="t-body text-ink">{RESALE_MODE_LABEL[mode]}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Cap set by the organiser</dt>
          <dd className="t-body u-num text-ink">{cap}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Jurisdiction on the record</dt>
          <dd className="t-body text-ink">{ruleValue(event.jurisdiction)}</dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Law policy resolved</dt>
          <dd className="t-body text-ink">
            {event.resalePolicy ? `${event.resalePolicy}${event.resalePolicyReason ? ` (${event.resalePolicyReason})` : ""}` : "not computed for this event"}
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Ceiling enforced</dt>
          <dd className="t-body u-num text-ink">
            {enforced ? formatSol(enforced.enforcedCeilingLamports) : "not computed for this event"}
          </dd>
        </div>
        <div className="flex justify-between gap-4">
          <dt className="t-meta text-muted">Binding rule</dt>
          <dd className="t-body text-ink">
            {enforced ? enforced.bindingRule : "not computed for this event"}
          </dd>
        </div>
      </dl>
      <p className="t-micro mt-3 text-muted">
        The cap is fixed when the record is initialised. Nothing on this screen raises or lowers it.
      </p>
    </Panel>
  );
}

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
          <h1 className="h-display">Organisers</h1>
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

  // The event whose record is drawn in full comes first, so its detail is above
  // the fold; every other event keeps its section and its anchor.
  const ordered = [selected, ...events.items.filter((event) => event.id !== selected.id)];

  const hasSales = analytics.saleCount > 0 || analytics.priceSeries.length > 0;
  const hasHolders = analytics.topDestinations.length > 0 || analytics.uniqueHolders > 0;
  const destinations = analytics.topDestinations.slice(0, MAX_DESTINATIONS);

  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">Organisers</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          This screen has no authorization: there is no account, no session and no role in this
          build, so anyone who can reach the URL sees it.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/organizer/events"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-accent bg-accent px-5 t-meta font-medium text-on-accent hover:border-accent-press hover:bg-accent-press"
          >
            Your events
          </Link>
          <Link
            href="/organizer/events/new"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-control bg-surface px-5 t-meta text-ink hover:border-ink"
          >
            Create an event
          </Link>
          <Link
            href="/door"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-control bg-surface px-5 t-meta text-ink hover:border-ink"
          >
            Door
          </Link>
          <Link
            href="/demo"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-control bg-surface px-5 t-meta text-ink hover:border-ink"
          >
            Event settings (simulated demo)
          </Link>
        </div>
      </header>

      <section className="mt-12" aria-labelledby="your-events">
        <h2 id="your-events" className="h-section">
          Your events
        </h2>
        <p className="t-meta mt-2 max-w-3xl text-muted">
          Every event the backend returned, with the rule it carries. A row&apos;s name links to that
          event&apos;s section on this page; the resale record itself is drawn for one event per
          build, and says so.
        </p>
        <div
          className="mt-4 overflow-x-auto rounded-panel border border-line bg-surface p-2"
          role="region"
          aria-label="Your events, scrollable"
          tabIndex={0}
        >
          <table className="w-full border-collapse">
            <caption className="sr-only">
              Every event returned by the backend: its name, start, venue, resale mode, organiser cap
              and issued tickets.
            </caption>
            <thead>
              <tr className="border-b border-line">
                <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Event</th>
                <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Starts</th>
                <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Venue</th>
                <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Resale mode</th>
                <th scope="col" className="t-micro-caps px-3 py-3 text-right text-muted">Cap</th>
                <th scope="col" className="t-micro-caps px-3 py-3 text-right text-muted">Issued</th>
              </tr>
            </thead>
            <tbody>
              {events.items.map((event) => (
                <tr key={event.id} className="border-b border-line last:border-b-0">
                  <td className="px-3 py-3">
                    <a
                      href={`#event-${event.id}`}
                      className="t-meta text-ink underline-offset-4 hover:underline"
                    >
                      {event.name}
                    </a>
                    {event.id === selected.id && (
                      <Chip className="ml-2" tone="accent">
                        Shown below
                      </Chip>
                    )}
                  </td>
                  <td className="t-meta px-3 py-3 text-ink">{formatDate(event.startsAt)}</td>
                  <td className="t-meta px-3 py-3 text-ink">
                    {event.venue}, {event.city}
                  </td>
                  <td className="t-meta px-3 py-3 text-ink">
                    {RESALE_MODE_LABEL[resaleModeOf(event.resaleEnabled)]}
                  </td>
                  <td className="figure t-meta px-3 py-3 text-right text-ink">
                    {event.resalePriceCapBps == null ? "none" : bpsLabel(event.resalePriceCapBps)}
                  </td>
                  <td className="figure t-meta px-3 py-3 text-right text-ink">
                    {formatCompact(event.issuedCount)} / {formatCompact(event.totalSupply)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {requestedId && !matched && (
          <p className="t-meta mt-3 text-muted">
            No event with that id is in the list, so the first event&apos;s record is the one drawn.
          </p>
        )}
        {!requestedId && events.items.length > 1 && (
          <p className="t-meta mt-3 text-muted">
            One resale record is drawn per build. This page is a static export, so the choice
            cannot be made by a link; its event is the first in this list.
          </p>
        )}
      </section>

      {ordered.map((event) => (
        <section key={event.id} id={`event-${event.id}`} className="mt-14" aria-labelledby={`event-${event.id}-title`}>
          <h2 id={`event-${event.id}-title`} className="h-section">
            {event.name}
          </h2>
          <p className="t-meta mt-2 text-muted">
            {event.venue}, {event.city} · starts {formatDate(event.startsAt)} ·{" "}
            {event.id === selected.id ? (
              <>face from <span className="figure text-ink">{formatSol(analytics.faceValueLamports)}</span></>
            ) : (
              <>resale record not drawn in this build; the rule is.</>
            )}
          </p>

          <EventRule event={event} />

          {event.id !== selected.id ? (
            <p className="t-meta mt-3 text-muted">
              This event&apos;s sale figures are not on this page: the export renders one analytics
              record, and drawing a second would mean a second build-time fetch behind a control
              that cannot exist without a server.
            </p>
          ) : !hasSales ? (
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
              <section className="mt-8" aria-labelledby="figures">
                <h3 id="figures" className="h-section">
                  Resale record
                </h3>
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
                {analytics.analyticsNote && (
                  <p className="t-micro mt-4 text-muted">{analytics.analyticsNote}</p>
                )}
              </section>

              <section className="mt-12" aria-labelledby="series">
                <h3 id="series" className="h-section">
                  Resale price over time
                </h3>
                <p className="t-meta mt-2 text-muted">
                  Average price paid per day, bucketed in UTC, for {event.name}.
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
                <h3 id="buckets" className="h-section">
                  Markup distribution
                </h3>
                <p className="t-meta mt-2 text-muted">
                  How far over face value tickets changed hands. All six buckets are shown, including
                  the ones nothing landed in.
                </p>
                <Panel className="mt-4">
                  <MarkupDistribution buckets={analytics.markupDistribution} />
                </Panel>
              </section>

              <section className="mt-12" aria-labelledby="destinations">
                <h3 id="destinations" className="h-section">
                  Where tickets ended up
                </h3>
                <p className="t-meta mt-2 max-w-3xl text-muted">
                  Up to {MAX_DESTINATIONS} holding wallets, by ticket count. A region is only
                  populated when a wallet volunteered one, so a dash means that wallet has not shared
                  one.
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
                  <Panel className="relative mt-4">
                    <div
                      role="region"
                      aria-label="Holding wallets, scrollable"
                      tabIndex={0}
                      className="overflow-x-auto"
                    >
                      <table className="w-full border-collapse">
                        <caption className="sr-only">
                          Holding wallets for {event.name}, up to {MAX_DESTINATIONS} rows: the wallet,
                          how many tickets it holds, whether it acquired them on the secondary market,
                          and the region it volunteered.
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
                              Holder region (volunteered)
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
                    </div>
                  </Panel>
                )}
              </section>
            </>
          )}
        </section>
      ))}

      <div className="mt-12">
        <DataSourceNote dataSource={analytics.dataSource ?? events.dataSource} />
      </div>
    </div>
  );
}

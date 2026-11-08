import Link from "next/link";
import { getEvents } from "@/lib/api";
import { Chip, DataSourceNote, Panel } from "@/components/ui";
import { formatCompact, formatDate } from "@/lib/format";
import { bpsLabel } from "@/lib/demoState";
import { RESALE_MODE_LABEL, resaleModeOf } from "@/lib/resaleMode";

export const dynamic = "force-static";

export const metadata = { title: "Your events" };

/**
 * The organiser's own index. Before this page existed the only organiser route
 * reached by a link was the analytics dashboard, and `/organizer/events` served
 * nothing at all, so the create screen was reachable only by typing its URL.
 */
export default async function OrganizerEventsPage() {
  const events = await getEvents({ limit: 100 });

  return (
    <div className="box pt-16">
      <header>
        <p className="t-micro-caps text-muted">
          <Link href="/organizer" className="underline-offset-4 hover:underline">
            Organisers
          </Link>
          {" / "}
          <span>Your events</span>
        </p>
        <h1 className="h-display mt-3">Your events</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          Every event the backend returned, with the rule it carries. Reading and editing are
          separate gaps: the record can be edited here as a drawing of the form, and nothing here
          writes one.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            href="/organizer/events/new"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-accent bg-accent px-5 t-meta font-medium text-on-accent hover:border-accent-press hover:bg-accent-press"
          >
            Create an event
          </Link>
          <Link
            href="/organizer"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-control bg-surface px-5 t-meta text-ink hover:border-ink"
          >
            The resale record
          </Link>
        </div>
      </header>

      <section className="mt-12" aria-labelledby="list">
        <h2 id="list" className="h-section">
          {events.items.length} event{events.items.length === 1 ? "" : "s"}
        </h2>

        {events.items.length === 0 ? (
          <Panel className="mt-4">
            <p className="t-body text-muted">
              The backend returned no events. Nothing is hidden behind an account: there is no
              account in this build.
            </p>
          </Panel>
        ) : (
          <div
            className="mt-4 overflow-x-auto rounded-panel border border-line bg-surface p-2"
            role="region"
            aria-label="Events, scrollable"
            tabIndex={0}
          >
            <table className="w-full border-collapse">
              <caption className="sr-only">
                Events the backend returned, with their resale mode, cap and issued tickets, and a
                link to each event&apos;s record and its edit form.
              </caption>
              <thead>
                <tr className="border-b border-line">
                  <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Event</th>
                  <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Starts</th>
                  <th scope="col" className="t-micro-caps px-3 py-3 text-left text-muted">Resale mode</th>
                  <th scope="col" className="t-micro-caps px-3 py-3 text-right text-muted">Cap</th>
                  <th scope="col" className="t-micro-caps px-3 py-3 text-right text-muted">Issued</th>
                  <th scope="col" className="t-micro-caps px-3 py-3 text-right text-muted">Actions</th>
                </tr>
              </thead>
              <tbody>
                {events.items.map((event) => (
                  <tr key={event.id} className="border-b border-line last:border-b-0">
                    <th scope="row" className="px-3 py-3 text-left">
                      <span className="t-meta block text-ink">{event.name}</span>
                      <span className="t-micro block text-muted">
                        {event.venue}, {event.city}
                      </span>
                    </th>
                    <td className="t-meta px-3 py-3 text-ink">{formatDate(event.startsAt)}</td>
                    <td className="px-3 py-3">
                      <Chip>{RESALE_MODE_LABEL[resaleModeOf(event.resaleEnabled)]}</Chip>
                    </td>
                    <td className="figure t-meta px-3 py-3 text-right text-ink">
                      {event.resalePriceCapBps == null ? "none" : bpsLabel(event.resalePriceCapBps)}
                    </td>
                    <td className="figure t-meta px-3 py-3 text-right text-ink">
                      {formatCompact(event.issuedCount)} / {formatCompact(event.totalSupply)}
                    </td>
                    <td className="px-3 py-3">
                      <div className="flex flex-wrap justify-end gap-x-4 gap-y-1">
                        <Link
                          href={`/events/${event.slug}`}
                          className="t-meta text-ink underline-offset-4 hover:underline"
                        >
                          Record
                        </Link>
                        <Link
                          href={`/organizer/events/${event.id}/edit`}
                          className="t-meta text-ink underline-offset-4 hover:underline"
                        >
                          Edit
                        </Link>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <div className="mt-6">
          <DataSourceNote dataSource={events.dataSource} />
        </div>
      </section>
    </div>
  );
}

import { getEvents } from "@/lib/api";
import { EventFilter } from "@/components/EventFilter";
import { DataSourceNote } from "@/components/ui";

export const metadata = { title: "Events" };

/**
 * Browse, as the buyer sees it.
 *
 * The export is written once, at build time, and served as plain files: this
 * route never sees a request. So it reads the events once and stops there, and
 * every filter, the count and the ordering happen in the browser inside
 * components/EventFilter.tsx. That file carries the honest note the screen
 * prints about it; the sentence this file used to carry, "the URL is the state",
 * was true of the links and false of the export, which ignored them.
 *
 * Keeping the page a server component keeps the data read out of the client
 * bundle, and it is what puts the unfiltered list in `out/events.html`: a reader
 * with no JavaScript gets an inventory, not an empty frame under a dead control.
 */

/**
 * `force-static` is the export's own instruction repeated: render this route
 * once, with no request behind it. Nothing on it reads a query string, so there
 * is no dynamic work for Next to do here and none is deferred to runtime.
 */
export const dynamic = "force-static";

export default async function EventsPage(): Promise<React.ReactElement> {
  // One read. There is no cursor here on purpose: a static file cannot ask for a
  // next page, so the browser filters the page that the export carries.
  const all = await getEvents({});

  return (
    <div className="box py-16">
      <header>
        <h1 className="h-section">Events</h1>
        {/* Above the fold, not only at the foot: a reader has to know what this
            list is before they read it, not after. */}
        <div className="mt-3">
          <DataSourceNote dataSource={all.dataSource} />
        </div>
      </header>

      <EventFilter
        events={all.items}
        dataSource={all.dataSource}
        hasMore={all.nextCursor !== null}
      />
    </div>
  );
}

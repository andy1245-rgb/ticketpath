import Link from "next/link";
import { getEvents } from "@/lib/api";
import { EventCard } from "@/components/EventCard";
import { DataSourceNote, Panel, Pill } from "@/components/ui";
import type { EventStatus } from "@/lib/types";

export const metadata = { title: "Events" };

/**
 * Browse. The URL is the state: every filter and the cursor live in the query
 * string, so a link can carry a search, the back button works, and a reader
 * with no JavaScript still pages. Nothing on this screen filters locally.
 */

const DEFAULT_LIMIT = 12;

/** Every value `EventStatus` allows, and nothing invented beside them. */
const EVENT_STATUSES: readonly EventStatus[] = [
  "draft",
  "on_sale",
  "sold_out",
  "completed",
  "cancelled",
];

/**
 * The chips the browse row offers. The service's other two values are still
 * valid in the URL and still filter correctly; these four are the ones the row
 * names, because a row of six is a wall on a phone.
 */
const STATUS_CHIPS: ReadonlyArray<{ value: EventStatus | null; label: string }> = [
  { value: null, label: "All" },
  { value: "on_sale", label: "On sale" },
  { value: "completed", label: "Completed" },
  { value: "draft", label: "Draft" },
];

const STATUS_LABEL: Record<EventStatus, string> = {
  draft: "Draft",
  on_sale: "On sale",
  sold_out: "Sold out",
  completed: "Completed",
  cancelled: "Cancelled",
};

type SearchParams = Record<string, string | string[] | undefined>;

/** A repeated parameter arrives as an array; the first value is the one meant. */
function one(value: string | string[] | undefined): string | undefined {
  const flat = Array.isArray(value) ? value[0] : value;
  return flat === undefined || flat === "" ? undefined : flat;
}

function readStatus(value: string | undefined): EventStatus | undefined {
  return EVENT_STATUSES.find((status) => status === value);
}

function readLimit(value: string | undefined): number {
  const parsed = value === undefined ? Number.NaN : Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : DEFAULT_LIMIT;
}

interface EventsHrefArgs {
  status?: EventStatus;
  city?: string;
  q?: string;
  limit?: number;
  cursor?: string;
}

/**
 * One place that builds a browse URL, so a chip, a paging link and the empty
 * state's clear link all keep the same filters. The cursor is never carried
 * across a filter change: page 3 of a different search is not a page.
 */
function eventsHref({ status, city, q, limit, cursor }: EventsHrefArgs): string {
  const search = new URLSearchParams();
  if (status) search.set("status", status);
  if (city) search.set("city", city);
  if (q) search.set("q", q);
  if (limit !== undefined && limit !== DEFAULT_LIMIT) search.set("limit", String(limit));
  if (cursor) search.set("cursor", cursor);
  const query = search.toString();
  return query ? `/events?${query}` : "/events";
}

/** The chip's shape, so a filter link and a status badge read as one family. */
const CHIP_BASE =
  "u-transition inline-flex min-h-6 items-center rounded-pill border bg-inset px-3 py-1 t-micro-caps";
const CHIP_IDLE = "border-line text-muted hover:border-ink hover:text-ink";
const CHIP_ACTIVE = "border-accent text-accent";

const FIELD_LABEL = "t-micro-caps text-muted";
const FIELD_CONTROL =
  "h-11 rounded-input border border-control bg-surface px-3 t-body text-ink";

/**
 * Static export has no request to read a query string from. `force-static`
 * tells Next to render this route once at build time with an empty
 * `searchParams`, which is the default (unfiltered) view. Filter links still
 * work as URLs; the values they carry are simply not read by the export.
 */
export const dynamic = "force-static";

export default async function EventsPage({
  searchParams,
}: {
  searchParams: Promise<SearchParams>;
}) {
  const params = await searchParams;

  const status = readStatus(one(params.status));
  const city = one(params.city);
  const q = one(params.q);
  const cursor = one(params.cursor);
  const limit = readLimit(one(params.limit));

  // The filtered page is what the screen shows. The unfiltered first page is
  // read only for the list of cities, so the control offers real places rather
  // than a city somebody typed into it.
  const [page, all] = await Promise.all([
    getEvents({ status, city, q, cursor, limit }),
    getEvents({}),
  ]);

  const cities = [...new Set(all.items.map((event) => event.city))].sort((a, b) => a.localeCompare(b));
  if (city && !cities.includes(city)) cities.unshift(city);

  const filterLabels: string[] = [];
  if (status) filterLabels.push(`status "${STATUS_LABEL[status]}"`);
  if (city) filterLabels.push(`city "${city}"`);
  if (q) filterLabels.push(`name or venue matching "${q}"`);
  const inForce = filterLabels.join(", ");

  return (
    <div className="box py-16">
      <header>
        <h1 className="h-section">Events</h1>
      </header>

      <div className="mt-12 flex flex-col gap-4">
        <nav aria-label="Filter by status" className="flex flex-wrap gap-2">
          {STATUS_CHIPS.map((chip) => {
            const active = chip.value === (status ?? null);
            return (
              <Link
                key={chip.label}
                href={eventsHref({ status: chip.value ?? undefined, city, q, limit })}
                aria-current={active ? "page" : undefined}
                className={`${CHIP_BASE} ${active ? CHIP_ACTIVE : CHIP_IDLE}`}
              >
                {chip.label}
              </Link>
            );
          })}
        </nav>

        {/* A plain GET form: it submits to this route and needs no script. */}
        <form
          action="/events"
          method="get"
          aria-label="Filter events"
          className="flex flex-wrap items-end gap-4"
        >
          {status && <input type="hidden" name="status" value={status} />}
          {limit !== DEFAULT_LIMIT && <input type="hidden" name="limit" value={String(limit)} />}

          <div className="flex w-full flex-col gap-1 sm:w-64">
            <label htmlFor="q" className={FIELD_LABEL}>
              Name or venue
            </label>
            <input id="q" name="q" type="search" defaultValue={q ?? ""} className={FIELD_CONTROL} />
          </div>

          <div className="flex w-full flex-col gap-1 sm:w-56">
            <label htmlFor="city" className={FIELD_LABEL}>
              City
            </label>
            <select id="city" name="city" defaultValue={city ?? ""} className={FIELD_CONTROL}>
              <option value="">All cities</option>
              {cities.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            className="u-transition inline-flex h-11 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
          >
            Apply filters
          </button>
        </form>
      </div>

      {page.items.length === 0 ? (
        <div className="mt-12">
          <Panel>
            <p className="t-meta text-ink">
              {filterLabels.length ? "No events match the current filters." : "No events are recorded."}
            </p>
            <p className="t-body mt-2 text-muted">
              {filterLabels.length
                ? `The filters in force were: ${inForce}.`
                : "The backend returned no events at all, so there is nothing to filter."}
            </p>
            <div className="mt-6">
              <Pill href="/events" variant="secondary">
                Clear all filters
              </Pill>
            </div>
          </Panel>
        </div>
      ) : (
        <ul className="mt-12 flex flex-col gap-6">
          {page.items.map((event) => (
            <li key={event.id}>
              <EventCard event={event} />
            </li>
          ))}
        </ul>
      )}

      {(page.nextCursor || cursor) && (
        <nav aria-label="Pagination" className="mt-12 flex flex-wrap items-center gap-4">
          {cursor && (
            <Pill href={eventsHref({ status, city, q, limit })} variant="secondary">
              Back to the first page
            </Pill>
          )}
          {page.nextCursor && (
            <Pill
              href={eventsHref({ status, city, q, limit, cursor: page.nextCursor })}
              variant="secondary"
            >
              Next
            </Pill>
          )}
        </nav>
      )}

      <div className="mt-12">
        <DataSourceNote dataSource={page.dataSource} />
      </div>
    </div>
  );
}

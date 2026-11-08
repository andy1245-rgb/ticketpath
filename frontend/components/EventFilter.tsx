"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { EventCard } from "@/components/EventCard";
import { DataSourceNote, Panel, Pill } from "@/components/ui";
import type { DataSource, Event, EventStatus } from "@/lib/types";

/**
 * Browse, on the buyer's side of the static export.
 *
 * The export is written once at build time and served as files: the route never
 * sees a request, so the page above cannot read `?status=` and a link that
 * carried a filter used to change nothing but the address bar. The page loads
 * the events once and hands them here; this file narrows and orders them in the
 * browser, which is the only place left that can.
 *
 * What that costs is written on the screen rather than hidden: these controls
 * filter the list the page already carries, and nothing here asks a backend for
 * anything. With no JavaScript the list is still there, unfiltered, because it
 * is in the HTML the export printed.
 */

interface Filters {
  status: EventStatus | null;
  city: string;
  q: string;
}

/** The unfiltered view, which is also what the export prints. */
const NO_FILTERS: Filters = { status: null, city: "", q: "" };

/**
 * The statuses a reader may ask for. `draft` is deliberately absent: an
 * unpublished event is not a buyer's to browse, and the address bar is not a
 * back door, so a URL that says `status=draft` is read as no status filter at
 * all. The other four are published states and all of them still filter.
 */
const BROWSE_STATUSES: readonly EventStatus[] = ["on_sale", "sold_out", "completed", "cancelled"];

/**
 * The chips the row offers. Four, including All: `draft` is gone because a
 * buyer must not be able to ask for the unpublished set, `sold_out` is in
 * because it is a state people look for, and the row stops there because six
 * chips is a wall on a phone. `cancelled` is still a valid value in the URL and
 * still filters; the row just does not spend a slot on it.
 */
const STATUS_CHIPS: ReadonlyArray<{ value: EventStatus | null; label: string }> = [
  { value: null, label: "All" },
  { value: "on_sale", label: "On sale" },
  { value: "sold_out", label: "Sold out" },
  { value: "completed", label: "Completed" },
];

const STATUS_LABEL: Record<EventStatus, string> = {
  draft: "Draft",
  on_sale: "On sale",
  sold_out: "Sold out",
  completed: "Completed",
  cancelled: "Cancelled",
};

/** The chip's shape, so a filter and a status badge read as one family. */
const CHIP_BASE =
  "u-transition inline-flex min-h-6 items-center rounded-pill border bg-inset px-3 py-1 t-micro-caps";
const CHIP_IDLE = "border-line text-muted hover:border-ink hover:text-ink";
const CHIP_ACTIVE = "border-accent text-accent";

const FIELD_LABEL = "t-micro-caps text-muted";
const FIELD_CONTROL =
  "h-11 rounded-input border border-control bg-surface px-3 t-body text-ink";

/** A status value from a URL, or null when it is not one a buyer may ask for. */
function matchStatus(value: string | null): EventStatus | null {
  return BROWSE_STATUSES.find((status) => status === value) ?? null;
}

/**
 * One place that builds a browse URL, so a chip, the form and the city control
 * keep the same filters and a filtered view stays a link somebody can send.
 * There is no cursor in it because there is no paging any more: a file served
 * from disk cannot ask for a next page.
 */
function browseHref(pathname: string, filters: Filters): string {
  const search = new URLSearchParams();
  if (filters.status) search.set("status", filters.status);
  if (filters.city) search.set("city", filters.city);
  if (filters.q) search.set("q", filters.q);
  const query = search.toString();
  return query ? `${pathname}?${query}` : pathname;
}

/** The filters in force, as the sentence the empty state prints. */
function describeFilters(filters: Filters): string {
  const parts: string[] = [];
  if (filters.status) parts.push(`status "${STATUS_LABEL[filters.status]}"`);
  if (filters.city) parts.push(`city "${filters.city}"`);
  if (filters.q) parts.push(`name or venue matching "${filters.q}"`);
  return parts.join(", ");
}

/**
 * The address bar is the state: a chip, the form, a shared link and the back
 * button all end up as a query string, and this renders nothing. It reads the
 * three values and hands them up whenever one of them changes, which is what
 * makes a pasted link and a browser-history step land on the same list a click
 * would have produced.
 *
 * It mounts only after hydration. During the build the query string is empty by
 * definition, so a first client render that already filtered would disagree
 * with the HTML in `out/events.html` and React would throw the served list away
 * and redraw it. Rendering nothing until the browser owns the screen keeps the
 * two in step: the export prints every event, and the first pass after mount
 * narrows it to whatever the address bar actually says.
 */
function AddressBarSync({ onRead }: { onRead: (filters: Filters) => void }): null {
  const params = useSearchParams();
  const status = params.get("status");
  const city = params.get("city");
  const q = params.get("q");

  useEffect(() => {
    onRead({
      status: matchStatus(status),
      city: (city ?? "").trim(),
      q: (q ?? "").trim(),
    });
  }, [status, city, q, onRead]);

  return null;
}

export function EventFilter({
  events,
  dataSource,
  hasMore = false,
}: {
  events: Event[];
  dataSource?: DataSource | null;
  hasMore?: boolean;
}): React.ReactElement {
  const router = useRouter();
  const pathname = usePathname();

  const [filters, setFilters] = useState<Filters>(NO_FILTERS);
  // The search box keeps its own text so a half-typed query is not thrown away
  // the moment a chip is pressed; it is committed together with the chip.
  const [typed, setTyped] = useState("");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  /** Read from below, write to the screen: the two directions of one state. */
  const readAddressBar = useCallback((next: Filters) => {
    setFilters(next);
    setTyped(next.q);
  }, []);

  /**
   * Nearest first. ISO-8601 UTC strings sort in date order as plain text, so
   * this is the same comparison the service makes and it needs no parsing.
   * There is no price ordering: the record holds no primary price per event,
   * and the resale cap is a ceiling rather than a price.
   */
  const ordered = useMemo(
    () => [...events].sort((a, b) => a.startsAt.localeCompare(b.startsAt)),
    [events],
  );

  const visible = useMemo(() => {
    const needle = filters.q.toLowerCase();
    return ordered.filter((event) => {
      if (filters.status !== null && event.status !== filters.status) return false;
      if (filters.city !== "" && event.city !== filters.city) return false;
      if (needle === "") return true;
      return (
        event.name.toLowerCase().includes(needle) || event.venue.toLowerCase().includes(needle)
      );
    });
  }, [ordered, filters]);

  /**
   * The city control offers real places, taken from the events the page loaded,
   * never a place typed into the control. A city already in force stays in the
   * list even if nothing it matches survived the other filters, so the reader
   * can always get back out of a filter they set.
   */
  const cities = useMemo(() => {
    const names = [...new Set(events.map((event) => event.city))].sort((a, b) => a.localeCompare(b));
    if (filters.city !== "" && !names.includes(filters.city)) names.unshift(filters.city);
    return names;
  }, [events, filters.city]);

  /**
   * Every control writes the URL rather than only its own state. That is what
   * makes a filtered view a link somebody can send, and it is why the form is
   * still a GET form to this route: without a script the same submit is a plain
   * page load, and the load lands on this screen with the same query string.
   * The push (rather than a replace) is so the back button steps back out of a
   * filter one press at a time.
   */
  function commit(patch: Partial<Filters>) {
    const next: Filters = { ...filters, q: typed.trim(), ...patch };
    setFilters(next);
    setTyped(next.q);
    router.push(browseHref(pathname, next), { scroll: false });
  }

  const total = events.length;
  const filtering = filters.status !== null || filters.city !== "" || filters.q !== "";
  const noun = total === 1 ? "event" : "events";
  const count = filtering ? `${visible.length} of ${total} ${noun}` : `${total} ${noun}`;

  return (
    <div className="mt-12 flex flex-col gap-6">
      {mounted && <AddressBarSync onRead={readAddressBar} />}

      <div className="flex flex-col gap-4">
        {/* Chips are real links to the URL the filter would produce, so a chip
            is openable in a new tab and readable before a script has run; the
            press itself is a client navigation, which is what lands the new
            query string on the list below. Text typed but not yet submitted
            travels with the chip rather than being thrown away. */}
        <nav aria-label="Filter by status" className="flex flex-wrap gap-2">
          {STATUS_CHIPS.map((chip) => {
            const active = chip.value === filters.status;
            return (
              <Link
                key={chip.label}
                href={browseHref(pathname, { ...filters, q: typed.trim(), status: chip.value })}
                aria-current={active ? "page" : undefined}
                className={`${CHIP_BASE} ${active ? CHIP_ACTIVE : CHIP_IDLE}`}
              >
                {chip.label}
              </Link>
            );
          })}
        </nav>

        {/* A plain GET form to this route: it needs no script to submit, and a
            submit is the same URL a filter click would have pushed. */}
        <form
          action="/events"
          method="get"
          aria-label="Filter events"
          onSubmit={(event) => {
            event.preventDefault();
            commit({});
          }}
          className="flex flex-wrap items-end gap-4"
        >
          {filters.status && <input type="hidden" name="status" value={filters.status} />}

          <div className="flex w-full flex-col gap-1 sm:w-64">
            <label htmlFor="q" className={FIELD_LABEL}>
              Name or venue
            </label>
            <input
              id="q"
              name="q"
              type="search"
              autoComplete="off"
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              className={FIELD_CONTROL}
            />
          </div>

          <div className="flex w-full flex-col gap-1 sm:w-56">
            <label htmlFor="city" className={FIELD_LABEL}>
              City
            </label>
            <select
              id="city"
              name="city"
              value={filters.city}
              onChange={(event) => commit({ city: event.target.value })}
              className={FIELD_CONTROL}
            >
              <option value="">All cities</option>
              {cities.map((city) => (
                <option key={city} value={city}>
                  {city}
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

      <div>
        <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
          <p className="t-meta text-muted" aria-live="polite" aria-atomic="true">
            {count}
          </p>
          <p className="t-meta text-muted">Order: nearest date first</p>
        </div>
        <p className="t-micro mt-2 text-muted">
          Filtering, ordering and the count happen in the browser. This build is a static export
          with no server behind it, so nothing here can ask the record to filter on its behalf:
          these controls narrow the list the page already carries.
        </p>
        {hasMore && (
          <p className="t-micro mt-1 text-muted">
            The page carries the first {total} {noun} the service returned. There are more than
            these, and a file served from disk cannot ask for the next page.
          </p>
        )}
      </div>

      {visible.length === 0 ? (
        <Panel>
          <p className="t-meta text-ink">
            {filtering ? "No events match the current filters." : "No events are recorded."}
          </p>
          <p className="t-body mt-2 text-muted">
            {filtering
              ? `The filters in force were ${describeFilters(filters)}. Nothing was dropped from the record: the list is the same ${total} ${noun} the page loaded, narrowed on screen.`
              : "The service returned no events at all, so there is nothing to filter."}
          </p>
          {filtering && (
            <div className="mt-6">
              <Pill href={pathname} variant="secondary">
                Clear all filters
              </Pill>
            </div>
          )}
        </Panel>
      ) : (
        <ul className="flex flex-col gap-6">
          {visible.map((event) => (
            <li key={event.id}>
              <EventCard event={event} />
            </li>
          ))}
        </ul>
      )}

      {/* Printed twice on purpose: once under the heading, where a reader has to
          meet it before the list, and once at the foot, where the read itself is
          cited. It is the service's own sentence either way. */}
      <div className="mt-6">
        <DataSourceNote dataSource={dataSource} />
      </div>
    </div>
  );
}

import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getEvent, getEvents } from "@/lib/api";
import { DataSourceNote } from "@/components/ui";
import { formatBpsPercent, formatCeiling, formatSol } from "@/lib/format";
import type { DataSource, Event } from "@/lib/types";
import { CheckoutClient } from "./CheckoutClient";

/**
 * Every payload the backend serves carries a dataSource block; lib/types.ts has
 * not added it to Event yet, so it is read structurally, the same way EventCard
 * and TierTable read the fields they need. A missing block means no note, never
 * an invented source.
 */
function eventDataSource(event: Event): DataSource | undefined {
  return (event as Event & { dataSource?: DataSource }).dataSource;
}

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

export const metadata = { title: "Checkout" };

/**
 * The wallet screen. The server reads the event and renders the facts that do
 * not depend on a wallet; the client half exists only because the wallet lives
 * in the browser. There is no payment endpoint, so the order summary in the
 * payment step is inert by construction and the step itself is the Unavailable
 * panel: nothing here takes an order.
 */
export default async function CheckoutPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;

  let event;
  try {
    event = await getEvent(slug);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const enforced = event.enforcedCap ?? null;
  /*
   * No ticket exists before a purchase, so there is no single face value to
   * print. This row used to show the lowest tier's number under the plain label
   * "Face value", which read as the price of the ticket a buyer would buy and
   * was the face of no tier above the first. It is a range now, labelled From,
   * and the line beneath names the field the range was read out of.
   */
  const tierFaces = event.tiers.map((tier) => tier.faceValueLamports);
  const minFaceLamports = tierFaces.length > 0 ? Math.min(...tierFaces) : null;
  const maxFaceLamports = tierFaces.length > 0 ? Math.max(...tierFaces) : null;
  const faceShown =
    minFaceLamports === null || maxFaceLamports === null
      ? "No tier in this record"
      : minFaceLamports === maxFaceLamports
        ? formatSol(minFaceLamports)
        : `${formatSol(minFaceLamports)} to ${formatSol(maxFaceLamports)}`;
  const faceAuthority =
    event.tiers.length === 0
      ? "event.tiers[] is empty: no face value in this record"
      : event.tiers.length === 1
        ? "event.tiers[0].faceValueLamports, the only tier on this event"
        : `event.tiers[].faceValueLamports, the range across all ${event.tiers.length} tiers`;
  const capShown = enforced
    ? formatCeiling(enforced.enforcedCeilingLamports)
    : event.resalePriceCapBps == null
      ? "Uncapped"
      : `${formatBpsPercent(event.resalePriceCapBps)} over face`;

  return (
    <div className="box py-16">
      <Link href={`/events/${event.slug}`} className="u-transition t-meta text-muted hover:text-ink">
        {"\u2190 "}
        {event.name}
      </Link>

      <header className="mt-6">
        <h1 className="h-section">Checkout</h1>
        {/* The source label is the one marker that says none of this was read
            from the world, so it sits at the top of the screen as well as at
            the foot: a reader who stops above the fold still sees it. */}
        <div className="mt-2">
          <DataSourceNote dataSource={eventDataSource(event)} />
        </div>
        <p className="t-body mt-2 text-muted">{event.name}</p>
      </header>

      <dl className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="border-t border-line pt-4">
          <dt className="t-micro-caps text-muted">From</dt>
          <dd className="figure t-body mt-2 text-ink">{faceShown}</dd>
          <dd className="figure t-micro mt-1 text-muted">{faceAuthority}</dd>
        </div>

        <div className="border-t border-line pt-4">
          <dt className="t-micro-caps text-muted">Enforced cap</dt>
          <dd className="figure t-body mt-2 text-ink">{capShown}</dd>
          <dd className="figure t-micro mt-1 text-muted">
            {enforced ? "enforcedCap.enforcedCeilingLamports" : "resalePriceCapBps"}
          </dd>
        </div>

        <div className="border-t border-line pt-4">
          <dt className="t-micro-caps text-muted">Requires a verified wallet</dt>
          <dd className="t-body mt-2 text-ink">{event.requiresVerifiedWallet ? "Yes" : "No"}</dd>
          <dd className="figure t-micro mt-1 text-muted">requiresVerifiedWallet</dd>
        </div>
      </dl>

      <div className="mt-12">
        {/* The tiers and the recap travel to the client half because the order
            summary belongs in the payment step, beside the panel that says no
            payment endpoint exists. The page is a server component, so a
            ?tier= component of the address is not readable here; the summary
            says so instead of ignoring it. */}
        <CheckoutClient
          requiresVerifiedWallet={event.requiresVerifiedWallet}
          tiers={event.tiers}
          venue={event.venue}
          city={event.city}
          startsAt={event.startsAt}
        />
      </div>

      <div className="mt-12">
        <DataSourceNote dataSource={eventDataSource(event)} />
      </div>
    </div>
  );
}

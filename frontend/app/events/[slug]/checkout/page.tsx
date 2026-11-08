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
 * in the browser. There is no payment endpoint, so the payment step is the
 * Unavailable panel and never a disabled control.
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
  // No ticket exists before a purchase, so the face value shown is the lowest
  // tier's — the "from" price — and the field it came from is printed beside it.
  const faceValueLamports = event.tiers.length
    ? Math.min(...event.tiers.map((tier) => tier.faceValueLamports))
    : null;
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
        <p className="t-body mt-2 text-muted">{event.name}</p>
      </header>

      <dl className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <div className="border-t border-line pt-4">
          <dt className="t-micro-caps text-muted">Face value</dt>
          <dd className="figure t-body mt-2 text-ink">{formatSol(faceValueLamports)}</dd>
          <dd className="figure t-micro mt-1 text-muted">tier.faceValueLamports</dd>
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
        <CheckoutClient requiresVerifiedWallet={event.requiresVerifiedWallet} />
      </div>

      <div className="mt-12">
        <DataSourceNote dataSource={eventDataSource(event)} />
      </div>
    </div>
  );
}

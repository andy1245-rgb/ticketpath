import { getTickets } from "@/lib/api";
import { Panel, Pill, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";

export const metadata = { title: "Resale" };

/**
 * The marketplace screen, which is the one screen in this build that has no
 * data at all to show. There is no listings endpoint (inventory row 39), no
 * listing record of any kind, and therefore nothing to browse: the screen states
 * the endpoint by its contract path and draws nothing that could be mistaken for
 * a listing.
 *
 * It names the resale screen that does work, because a reader who lands here is
 * looking for a resale surface and there is exactly one: the per-ticket cap
 * check. That check needs a real ticket id, so the example is read from the
 * ticket source this build actually holds — the first row of lib/mock/tickets.json
 * in the bundled build — and never typed in by hand. A source with no rows gets
 * no example rather than an invented one.
 *
 * The ticket status `listed` is not the same thing as a listing and this page
 * says both facts: the count comes from the same source, so it cannot drift from
 * what the ticket records actually hold.
 */
export default async function ResalePage() {
  const [{ items }, listed] = await Promise.all([
    getTickets({ limit: 1 }),
    getTickets({ status: "listed", limit: 1000 }),
  ]);
  const exampleTicketId = items[0]?.id ?? null;
  const listedStatusCount = listed.items.length;

  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">Resale</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          No listing exists. Nothing here is for sale, and nothing in this build can put it there:
          there is no listings endpoint, and no listing record exists to browse.
        </p>
        <p className="t-body mt-4 max-w-3xl text-muted">
          The one resale screen that works is the cap check on a single ticket. It reads that
          ticket&apos;s face value and the ceiling its own tier carries, and answers whether a typed
          price would pass the contract&apos;s rule.
        </p>
        {exampleTicketId !== null && (
          <div className="mt-6 flex flex-wrap items-center gap-3">
            <Pill href={`/resale/list/${exampleTicketId}`} variant="primary">
              Cap check for ticket {exampleTicketId}
            </Pill>
            <p className="t-meta text-muted">
              The first ticket id this build holds, at{" "}
              <span className="figure">/resale/list/{exampleTicketId}</span>.
            </p>
          </div>
        )}
      </header>

      <div className="mt-12">
        <Unavailable capability={capabilities.listings} title="Browse resale listings" />
      </div>

      <section className="mt-12" aria-labelledby="the-feed">
        <Panel>
          <p className="t-micro-caps text-muted">Empty</p>
          <h2 id="the-feed" className="h-section mt-2">
            No listings
          </h2>
          <p className="t-body mt-2 max-w-3xl text-muted">
            Zero rows. The browse view reads{" "}
            <span className="figure text-ink">GET /api/listings</span>, which is not in the
            contract, so nothing can create a listing and nothing can return one.
          </p>
          <p className="t-body mt-4 max-w-3xl text-muted">
            A ticket status is not a listing.{" "}
            <span className="figure text-ink">{listedStatusCount}</span> ticket
            {listedStatusCount === 1 ? "" : "s"} in this build carry the status{" "}
            <span className="figure text-ink">listed</span> on the ticket record, and not one of
            them has an asking price, a listing row, or an endpoint that could carry either. The
            per-ticket cap check linked above is what a listed row can be taken to.
          </p>
        </Panel>
      </section>
    </div>
  );
}

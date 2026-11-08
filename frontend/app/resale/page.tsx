import { Panel, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";

export const metadata = { title: "Resale" };

/**
 * The marketplace screen, which is the one screen in this build that has no
 * data at all to show: there is no listings endpoint (inventory row 39), no
 * ticket ever reaches status `listed` because nothing creates a listing, and
 * the fixture set carries zero listing rows. So the screen states the endpoint
 * by its contract path and draws nothing that could be mistaken for a listing.
 */
export default function ResalePage() {
  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">Resale</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          Where a listed ticket would be browsed and bought. Nothing is listed, because nothing can
          create a listing.
        </p>
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
            contract, and no ticket ever reaches status &quot;listed&quot; because nothing creates a
            listing.
          </p>
        </Panel>
      </section>
    </div>
  );
}

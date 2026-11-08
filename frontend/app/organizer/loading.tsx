import { Skeleton } from "@/components/ui";

/**
 * The analytics read is two backend calls deep (events, then the selected
 * event's roll-up), so the shape of the page is held while it lands: the same
 * h1, one column of tiles, then the blocks the figures will fill.
 */
export default function OrganizerLoading() {
  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">For organizers</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          This screen has no authorization: there is no account, no session and no role in this
          build, so anyone who can reach the URL sees it.
        </p>
      </header>

      <div className="mt-12">
        <p className="t-micro-caps text-muted">Event</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <span className="h-10 w-40 rounded-pill bg-inset" />
          <span className="h-10 w-32 rounded-pill bg-inset" />
          <span className="h-10 w-48 rounded-pill bg-inset" />
        </div>
      </div>

      <div className="mt-12">
        <span className="block h-6 w-72 rounded-pill bg-inset" />
      </div>

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3].map((tile) => (
          <div key={tile} className="border-t border-line pt-4">
            <span className="block h-3 w-24 rounded-pill bg-inset" />
            <span className="mt-3 block h-8 w-32 rounded-pill bg-inset" />
          </div>
        ))}
      </div>

      <div className="mt-12">
        <span className="block h-6 w-56 rounded-pill bg-inset" />
        <div className="mt-4 rounded-panel border border-line bg-surface p-6">
          <Skeleton lines={4} />
        </div>
      </div>
    </div>
  );
}

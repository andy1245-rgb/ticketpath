import { Skeleton } from "@/components/ui";

/**
 * The analytics read is two backend calls deep (events, then the selected
 * event's roll-up), so the shape of the page is held while it lands: the same h1,
 * the events table, the rule panel, then the six tiles the figures will fill.
 *
 * The tiles are six in a `StatRow` because the page draws six; a four-tile
 * skeleton jumps when the real page lands.
 */
export default function OrganizerLoading() {
  return (
    <div className="box py-16">
      <header>
        <h1 className="h-display">Organisers</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          This screen has no authorization: there is no account, no session and no role in this
          build, so anyone who can reach the URL sees it.
        </p>
        <div className="mt-6 flex gap-3">
          <span className="block h-11 w-32 rounded-pill bg-inset" />
          <span className="block h-11 w-36 rounded-pill bg-inset" />
        </div>
      </header>

      <div className="mt-12">
        <span className="block h-6 w-56 rounded-pill bg-inset" />
        <div className="mt-4 rounded-panel border border-line bg-surface p-6">
          <Skeleton lines={5} />
        </div>
      </div>

      <div className="mt-14">
        <span className="block h-7 w-2/3 rounded-pill bg-inset" />
        <span className="mt-3 block h-4 w-1/2 rounded-pill bg-inset" />
        <div className="mt-4 rounded-panel border border-line bg-surface p-6">
          <Skeleton lines={4} />
        </div>
      </div>

      <div className="mt-8 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[0, 1, 2, 3, 4, 5].map((tile) => (
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

import { Skeleton } from "@/components/ui";

/**
 * The browse list while it is in flight: the same box and three card-sized
 * rows, so the page does not jump when the data lands. No heading of its own —
 * the page has the only h1 on this route, and the fallback does not compete
 * with it.
 */
export default function EventsLoading() {
  return (
    <div className="box py-16">
      <Skeleton lines={1} className="max-w-xs" />

      <div className="mt-12">
        <Skeleton lines={2} />
      </div>

      <div className="mt-12 flex flex-col gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-card border border-line bg-surface p-6">
            <Skeleton lines={3} />
          </div>
        ))}
      </div>
    </div>
  );
}

import { Skeleton } from "@/components/ui";

/**
 * The demo reads `localStorage` in an effect, so its first paint was a bare
 * paragraph where a page should be. This draws the shell's own shape while it
 * hydrates, and `Skeleton` carries `role="status"` and a screen-reader label.
 */
export default function DemoLoading(): React.ReactElement {
  return (
    <div className="box pt-12 pb-24">
      <p className="t-micro-caps text-muted">Live demo</p>
      <h1 className="h-display mt-2 text-ink">SeatPass, both sides of the resale</h1>
      <div className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="rounded-card border border-control bg-surface p-6">
          <Skeleton lines={5} />
        </div>
        <div className="rounded-card border border-control bg-surface p-6">
          <Skeleton lines={5} />
        </div>
      </div>
    </div>
  );
}

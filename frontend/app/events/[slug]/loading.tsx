import { Skeleton } from "@/components/ui";

/**
 * The event detail while it is in flight. The event's name is not known until
 * the read returns, so there is no heading here: the page supplies the only h1
 * on this route. The blocks below hold the same space the loaded sections will.
 */
export default function EventLoading() {
  return (
    <div className="box py-16">
      <Skeleton lines={2} />

      <div className="mt-12 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="border-t border-line pt-4">
            <Skeleton lines={2} />
          </div>
        ))}
      </div>

      <div className="mt-12 flex flex-col gap-6">
        {Array.from({ length: 2 }).map((_, i) => (
          <div key={i} className="rounded-panel border border-line bg-surface p-6">
            <Skeleton lines={4} />
          </div>
        ))}
      </div>
    </div>
  );
}

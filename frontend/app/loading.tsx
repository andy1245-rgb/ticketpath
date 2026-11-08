import { Skeleton } from "@/components/ui";

/*
 * The landing screen while its reads are in flight: the same box, the same
 * 690/486 split and the same 380 card as app/page.tsx. The headline and deck
 * blocks reserve their real heights, so the hero does not move when the data
 * lands. No spinner, and no heading: a placeholder makes no claim about the
 * page.
 */
export default function HomeLoading() {
  return (
    <>
      <section className="box pt-24">
        <div className="grid grid-cols-1 gap-12 min-[1200px]:grid-cols-[minmax(0,690px)_minmax(0,486px)] min-[1200px]:items-center min-[1200px]:gap-6">
          <div>
            {/* Eyebrow: one 12px line. */}
            <div aria-hidden="true" className="h-3 w-44 rounded-pill bg-inset" />

            {/* The h1 is two 64px lines at desktop, two 38px lines below it. */}
            <div className="mt-4 h-[76px] min-[1024px]:h-[128px]">
              <Skeleton lines={2} />
            </div>

            {/* The deck: three 26px lines in a 350px column. */}
            <div className="mt-6 h-[78px] max-w-[350px]">
              <Skeleton lines={3} />
            </div>

            {/* The two pills are 48 tall, so the actions row reserves 48. */}
            <div aria-hidden="true" className="mt-8 flex flex-wrap gap-3">
              <span className="h-12 w-40 rounded-pill bg-inset" />
              <span className="h-12 w-44 rounded-pill bg-inset" />
            </div>

            <div aria-hidden="true" className="mt-8 flex flex-wrap gap-4">
              <span className="h-3 w-32 rounded-pill bg-inset" />
              <span className="h-3 w-28 rounded-pill bg-inset" />
              <span className="h-3 w-44 rounded-pill bg-inset" />
            </div>
          </div>

          {/* The ticket card: 380 wide, one raised surface, a plot in the middle. */}
          <div className="min-[1200px]:justify-self-end">
            <div className="w-[380px] max-w-full rounded-card border border-control bg-surface p-6 shadow-card">
              <Skeleton lines={2} />
              <div aria-hidden="true" className="mt-6 h-[60px] rounded-card bg-inset" />
              <div className="mt-6">
                <Skeleton lines={2} />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="box mt-24">
        <div aria-hidden="true" className="h-4 w-64 rounded-pill bg-inset" />
        <div className="mt-16 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="rounded-card border border-control bg-surface p-6">
              <div aria-hidden="true" className="h-8 w-8 rounded-pill bg-inset" />
              <div className="mt-6">
                <Skeleton lines={3} />
              </div>
            </div>
          ))}
        </div>
      </section>
    </>
  );
}

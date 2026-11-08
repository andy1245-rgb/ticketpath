import { Skeleton } from "@/components/ui";

/* First paint while the page's reads are in flight. A placeholder makes no claim about the page. */
export default function Loading() {
  return (
    <div className="box py-12" aria-busy="true">
      <div aria-hidden="true" className="h-8 w-64 rounded-pill bg-inset" />
      <div className="mt-6 max-w-2xl">
        <Skeleton lines={3} />
      </div>
      <div className="mt-12 max-w-3xl">
        <Skeleton lines={6} />
      </div>
    </div>
  );
}

import { Skeleton } from "@/components/ui";

/** The door lookup while the record is in flight. */
export default function Loading() {
  return (
    <div className="box py-12">
      <h1 className="h-section">Door</h1>
      <div className="mt-12 max-w-2xl space-y-8">
        <Skeleton lines={6} />
        <Skeleton lines={4} />
      </div>
    </div>
  );
}

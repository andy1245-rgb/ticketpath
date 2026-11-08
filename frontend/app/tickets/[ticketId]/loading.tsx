import { Skeleton } from "@/components/ui";

/**
 * The ticket record while it is in flight. Same box and same rhythm as the
 * page so nothing shifts when the real record lands.
 */
export default function Loading() {
  return (
    <div className="box py-12">
      <h1 className="h-section">Ticket</h1>
      <div className="mt-12 space-y-12">
        <Skeleton lines={4} />
        <Skeleton lines={5} />
        <Skeleton lines={3} />
      </div>
    </div>
  );
}

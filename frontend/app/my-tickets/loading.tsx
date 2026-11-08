import { Skeleton } from "@/components/ui";

/**
 * Holdings before the wallet has answered. The page itself is a client
 * component, so this covers the route-level wait; the client covers the rest.
 */
export default function Loading() {
  return (
    <div className="box py-12">
      <h1 className="h-section">My tickets</h1>
      <div className="mt-12">
        <Skeleton lines={6} />
      </div>
    </div>
  );
}

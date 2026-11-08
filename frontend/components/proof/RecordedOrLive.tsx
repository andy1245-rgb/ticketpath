import { Chip } from "@/components/ui";

/**
 * One badge, one meaning, on every surface that shows a chain fact.
 *
 * `askedCluster` is the backend's own field: true means this build queried a
 * cluster and the field beside the badge is a read of it; false or null means
 * the build asked no cluster and the value came from the committed artefact,
 * which a verified run wrote at `verifiedAt`. Before this component the same
 * distinction lived in four differently worded sentences and a reader scanning
 * two screens could not tell which was which.
 */
export function RecordedOrLive({
  askedCluster,
  verifiedAt,
}: {
  askedCluster: boolean | null;
  verifiedAt?: string | null;
}): React.ReactElement {
  if (askedCluster === true) {
    return <Chip tone="positive">Read from a cluster in this build</Chip>;
  }
  const day = verifiedAt ? verifiedAt.slice(0, 10) : null;
  return (
    <Chip tone="neutral">
      {day ? `Recorded, verified ${day}` : "Recorded, not re-read"}
    </Chip>
  );
}

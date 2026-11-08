import type * as React from "react";
import type { MarkupBucket } from "@/lib/types";

/*
 * The six fixed markup buckets. The backend always returns all six, including
 * the ones nothing landed in, so this renders whatever it is handed in the
 * order given and never drops a zero: "no sale went over 200%" is a result,
 * not an empty row.
 *
 * A real table rather than an image with a long label, because the counts are
 * the point and a screen reader should be able to read them as numbers. The
 * bars are decoration inside their own cell, hidden from the accessibility
 * tree; the count in the last column is the same number in text.
 */

export function MarkupDistribution(props: { buckets: MarkupBucket[]; className?: string }): React.ReactElement {
  const { buckets, className = "" } = props;

  // The longest bar is the busiest bucket; every other bar is a fraction of it.
  // Guarded so six zeros cannot divide by zero.
  const max = Math.max(1, ...buckets.map((bucket) => bucket.count));

  if (!buckets.length) {
    return <p className={`t-meta text-muted ${className}`}>No markup buckets reported.</p>;
  }

  return (
    <table className={`w-full border-collapse ${className}`}>
      <caption className="sr-only">
        Resale markup distribution, {buckets.length} buckets
      </caption>
      {/* The header row was clipped with sr-only, which hides a table section
          from layout but leaves its cells in the accessibility tree with a
          made-up box and the UA's 700 weight. A caption plus row headers is
          the honest table: every bucket names itself and every count is
          readable as text. */}
      <tbody>
        {buckets.map((bucket) => {
          const share = bucket.count / max;
          return (
            <tr key={bucket.label}>
              <th scope="row" className="t-meta whitespace-nowrap py-1 pr-4 text-left text-ink">
                {bucket.label}
              </th>
              <td className="w-full py-1" aria-hidden="true">
                <div
                  className="h-2 rounded-pill bg-accent"
                  style={{
                    width: `${share * 100}%`,
                    // A bucket with one sale in two hundred should still show a
                    // mark; the count beside it says how small it really is.
                    minWidth: bucket.count > 0 ? 2 : 0,
                  }}
                />
              </td>
              <td className="figure t-meta w-12 py-1 pl-4 text-right text-ink">{bucket.count}</td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}

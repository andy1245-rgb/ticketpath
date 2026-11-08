import type { TicketTier } from "@/lib/types";
import { formatCeiling, formatCompact, formatSol } from "@/lib/format";

/**
 * The enforced ceiling for one tier, as the backend reports it: the
 * jurisdiction gate and the platform cap tightened to the lower of the two, and
 * the rule that binds it. lib/types.ts does not carry these yet, so the shape
 * is declared here and every field it reads is required — a row without a
 * ceiling contributes nothing rather than a guessed number.
 */
export interface EnforcedCapTier {
  tierId: string;
  enforcedBaseLamports?: number;
  enforcedCapBps: number;
  enforcedCeilingLamports: number;
  bindingRule: "law" | "platform";
  platformCapBps?: number | null;
}

/**
 * A real table, because this is tabular data: one row per tier, a column header
 * per figure, and figures set in the mono face and right-aligned so the digits
 * line up down the column.
 */
export function TierTable({
  tiers,
  enforcedCapByTier,
  className = "",
}: {
  tiers: TicketTier[];
  enforcedCapByTier?: EnforcedCapTier[] | null;
  className?: string;
}): React.ReactElement {
  // Keyed by tier id, so the cap column finds its own row's ceiling and never
  // borrows a neighbouring tier's number.
  const ceilings = new Map<string, EnforcedCapTier>();
  for (const row of enforcedCapByTier ?? []) ceilings.set(row.tierId, row);

  return (
    <div className={`overflow-x-auto rounded-panel border border-line bg-surface ${className}`}>
      <table className="w-full border-collapse">
        <caption className="sr-only">
          Ticket tiers: the face value of each, how many of its supply have been issued, and the
          resale ceiling the contract admits against it.
        </caption>
        <thead>
          <tr className="border-b border-line">
            <th scope="col" className="t-micro-caps px-6 py-3 text-left text-muted">
              Tier
            </th>
            <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-right text-muted">
              Face value
            </th>
            <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-right text-muted">
              Issued of supply
            </th>
            <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-right text-muted">
              Cap the contract admits
            </th>
          </tr>
        </thead>
        <tbody>
          {tiers.length === 0 && (
            <tr>
              <td colSpan={4} className="t-meta px-6 py-4 text-muted">
                No tiers are recorded for this event.
              </td>
            </tr>
          )}

          {tiers.map((tier) => {
            const enforced = ceilings.get(tier.id);
            return (
              <tr key={tier.id} className="border-b border-line last:border-0">
                <th scope="row" className="t-meta px-6 py-4 text-left text-ink">
                  {tier.name}
                </th>
                <td className="figure t-meta whitespace-nowrap px-6 py-4 text-right text-ink">
                  {formatSol(tier.faceValueLamports)}
                </td>
                <td className="figure t-meta whitespace-nowrap px-6 py-4 text-right text-ink">
                  {formatCompact(tier.issuedCount)} of {formatCompact(tier.totalSupply)}
                </td>
                <td className="figure t-meta whitespace-nowrap px-6 py-4 text-right text-ink">
                  {enforced ? (
                    formatCeiling(enforced.enforcedCeilingLamports)
                  ) : (
                    <>
                      <span aria-hidden="true">—</span>
                      <span className="sr-only">No ceiling reported for this tier</span>
                    </>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

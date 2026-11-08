import type * as React from "react";
import type { LedgerEntry, LedgerEntryKind } from "@/lib/types";
import { formatDateTime, formatMarkup, formatSol, shortAddress } from "@/lib/format";
import { markupBpsFromPrice } from "@/lib/cap";
import { explorerTxUrl } from "@/lib/solana";

/*
 * The custody rail: every wallet a ticket has passed through, in order. Built
 * once and used twice, as the three-row strip under the landing hero card and
 * as the full trail on /tickets/[ticketId], so the two never drift apart.
 *
 * The rail geometry is the export's: the 1px accent line runs 12px to the left
 * of the 6px dots, with an 8px stub from the rail to each dot, starting at the
 * first dot and ending at the last. Rows are one line each.
 */

/** What each ledger kind did, phrased as the row it produced. */
const ROW_LABEL: Record<LedgerEntryKind, string> = {
  issue: "Issued to",
  sale: "Bought by",
  transfer: "Transferred to",
  redeem: "Redeemed by",
  revoke: "Revoked",
};

/** The kind's own name, shown only in the full trail where there is room. */
const KIND_LABEL: Record<LedgerEntryKind, string> = {
  issue: "Issue",
  sale: "Sale",
  transfer: "Transfer",
  redeem: "Redeem",
  revoke: "Revoke",
};

/** Rail at x=4, dot centre at x=16: the 12px the export measures. */
const RAIL_LEFT = "left-[4px]";
/** The 6px dot starts at x=13 so its centre lands on x=16. */
const DOT_LEFT = "left-[13px]";

export function OwnershipTrail(props: {
  entries: LedgerEntry[];
  faceValueLamports: number;
  variant?: "strip" | "full";
  className?: string;
}): React.ReactElement {
  const { entries, faceValueLamports, variant = "strip", className = "" } = props;

  // The strip on the landing card is three rows; the ticket page keeps the lot.
  const rows = variant === "strip" ? entries.slice(-3) : entries;
  const full = variant === "full";

  if (!rows.length) {
    return <p className={`t-meta text-muted ${className}`}>No ledger entries.</p>;
  }

  return (
    <>
      {/* The full trail is one flex row of up to six cells per hop with no
          visible headings, and at 390px the cells wrap, so position stops
          telling a reader which number is the price and which is the markup.
          These are the column names in the order the cells print, as one
          sr-only sentence: a screen reader walking the list gets the headings
          once, in order, and the desktop rail below is exactly as drawn. */}
      {full && (
        <p className="sr-only">
          Custody trail column headings, in order: kind, who, price, markup over
          face value, when, transaction.
        </p>
      )}
      <ol className={`${variant === "strip" ? "w-full max-w-[380px]" : "w-full"} ${className}`}>
        {rows.map((entry, index) => {
          const label = ROW_LABEL[entry.kind];
          // Who the row moved the ticket to. A revoke carries no destination, so
          // the sender is the only wallet there is to name.
          const counterparty = entry.toWallet ?? entry.fromWallet;
          const isCurrent = index === rows.length - 1;
          const isSale = entry.kind === "sale";
          // The sale's own markup is a real backend field; when it is missing the
          // contract's own arithmetic against this ticket's face fills it in.
          const markupBps =
            isSale && entry.priceLamports != null
              ? (entry.markupBps ?? markupBpsFromPrice(entry.priceLamports, faceValueLamports))
              : null;

          return (
            <li
              key={entry.id}
              className={`relative flex min-w-0 items-center gap-1.5 pl-6 ${
                full ? "flex-wrap gap-y-1 py-2" : "h-7 flex-nowrap"
              }`}
            >
              {/* The rail is drawn in two halves per row so it can start and end
                  on a dot centre no matter how tall the rows turn out. */}
              {index > 0 && (
                <span aria-hidden="true" className={`absolute top-0 h-1/2 w-px bg-accent ${RAIL_LEFT}`} />
              )}
              {index < rows.length - 1 && (
                <span aria-hidden="true" className={`absolute top-1/2 h-1/2 w-px bg-accent ${RAIL_LEFT}`} />
              )}
              <span
                aria-hidden="true"
                className={`absolute top-1/2 h-px w-2 -translate-y-1/2 bg-accent ${RAIL_LEFT}`}
              />
              {/* Current custody is the positive dot; everything before it is history. */}
              <span
                aria-hidden="true"
                className={`absolute top-1/2 h-1.5 w-1.5 -translate-y-1/2 rounded-pill bg-current ${
                  isCurrent ? "text-positive" : "text-muted"
                } ${DOT_LEFT}`}
              />

              {full && <span className="t-micro-caps text-muted">{KIND_LABEL[entry.kind]}</span>}
              <span className="t-meta whitespace-nowrap text-ink">{label}</span>
              <span
                className="figure t-micro min-w-0 truncate text-muted"
                title={counterparty ?? undefined}
              >
                {shortAddress(counterparty)}
              </span>

              {/* Only a sale is a price paid. Everything else is a priced move or
                  a gift, and an em dash says so instead of showing the face value
                  as if money changed hands. */}
              <span
                className={`figure t-micro ml-auto whitespace-nowrap ${
                  isSale && entry.priceLamports != null ? "text-ink" : "text-muted"
                }`}
              >
                {isSale && entry.priceLamports != null ? formatSol(entry.priceLamports) : "\u2014"}
              </span>

              {full && markupBps != null && (
                <span className="t-micro whitespace-nowrap text-muted">
                  <span className="figure">{formatMarkup(markupBps)}</span> vs face
                </span>
              )}

              {full && (
                <span className="figure t-micro whitespace-nowrap text-muted">
                  {formatDateTime(entry.occurredAt)}
                </span>
              )}

              {/* Every row here comes from the synthetic fixture store, so there
                  is no transaction to link. The visible text says "No tx": this
                  column used to read "Fixture", which a sighted buyer reads as a
                  category rather than as "no transaction recorded", leaving only
                  the aria-label to say the real thing. When a signature does
                  arrive the same slot becomes the explorer link, named for its
                  own row. */}
              {entry.signature ? (
                <a
                  href={explorerTxUrl(entry.signature)}
                  target="_blank"
                  rel="noopener noreferrer"
                  aria-label={`View transaction for ${label}`}
                  className="t-meta u-transition whitespace-nowrap text-ink underline decoration-1 underline-offset-2 hover:text-accent"
                >
                  View tx
                </a>
              ) : (
                <span
                  aria-label={`No transaction recorded for ${label}`}
                  title="Synthetic fixture row - no on-chain transaction"
                  className="t-meta whitespace-nowrap text-muted"
                >
                  No tx
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </>
  );
}

import type { CSSProperties } from "react";
import type { LedgerEntry } from "@/lib/types";
import { formatCeiling, formatSol } from "@/lib/format";
import { Perforation } from "./ui";
import { PriceHistoryChart } from "./PriceHistoryChart";
import { OwnershipTrail } from "./OwnershipTrail";

/**
 * The hero ticket: the only card in the product with a shadow and the only one
 * with the notches cut out of its side edges.
 *
 * Geometry, from the desktop export: 380 wide, 220 of interior. The rule sits
 * exactly 92 below the 24px of padding, because the block above it is
 * `h-[92px]` and bottom-aligned. A name that wraps to its second line grows
 * upward inside that block, so the perforation never moves off the notches no
 * matter how long the fixture name is.
 *
 * Three coordinate systems overlap here and each contributes its own pixel: the
 * mask starts at the border box, absolute children start at the padding box
 * (one border inside it), and the rule is 1px tall. The constants below carry
 * the arithmetic once so the cut-out and the drawn fallback land on the same
 * row.
 */
const RULE_TOP = 92;
/** Mask coordinates: border box, so one border plus half the 1px rule. */
const NOTCH_Y = `${RULE_TOP + 1.5}px`;
/** Absolute placement: padding box, so the border is already subtracted. */
const HOLE_TOP = `${RULE_TOP + 0.5 - 6}px`;

/**
 * The cut-out is `.notched`'s mask (app/globals.css). Where a browser has no
 * `mask-composite: intersect` the mask leaves the card whole, so two 12px discs
 * of paper sit over the same two rows and cover the surface and the border
 * instead. They are drawn always: with the mask working they land in the hole
 * it cuts and show nothing new.
 */
const notchVars = { "--notch-y": NOTCH_Y } as CSSProperties;

/**
 * Formatted in UTC on purpose: this card is rendered on the server and again in
 * the browser, and a local-time string would differ between the two and trip
 * hydration. The event's published time is the server's time.
 */
const START_FORMAT = new Intl.DateTimeFormat("en-GB", {
  weekday: "short",
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
  hour12: false,
  timeZone: "UTC",
});

function startLabel(iso: string): string {
  const date = new Date(iso);
  return Number.isNaN(date.getTime()) ? "—" : START_FORMAT.format(date);
}

/**
 * The sentence under the card states what the chart above it shows, in the
 * numbers this ticket actually has. It is built from the ledger rather than
 * written by hand, so it cannot claim a sale that did not happen or a cap that
 * was never tested.
 */
function saleSummary(args: {
  entries: LedgerEntry[];
  faceValueLamports: number;
  capCeilingLamports: number | null;
  lastSaleLamports: number | null;
}): string {
  const { entries, faceValueLamports, capCeilingLamports, lastSaleLamports } = args;
  const sales = entries.filter((entry) => entry.kind === "sale" && entry.priceLamports != null);

  // The API's own last-sale figure wins; the newest priced sale is the fallback
  // for a ledger that arrived without stats.
  const lastSale =
    lastSaleLamports ??
    sales.reduce<number | null>((last, entry) => entry.priceLamports ?? last, null);

  const price =
    lastSale != null && lastSale === faceValueLamports
      ? `at face value, ${formatSol(lastSale)}`
      : `at ${formatSol(lastSale)}`;

  const overCap =
    capCeilingLamports == null
      ? 0
      : sales.filter((entry) => (entry.priceLamports ?? 0) > capCeilingLamports).length;

  const sold =
    sales.length === 0
      ? `Issued at face value, ${formatSol(faceValueLamports)}. No resale recorded.`
      : sales.length === 1
        ? `Sold once ${price}.`
        : `Sold ${sales.length} times, last ${price}.`;

  const cap =
    capCeilingLamports == null
      ? "This event has no resale cap."
      : overCap === 0
        ? `Never above the ${formatCeiling(capCeilingLamports)} cap.`
        : sales.length === 1
          ? `That sale went over the ${formatCeiling(capCeilingLamports)} cap.`
          : `${overCap} of those went over the ${formatCeiling(capCeilingLamports)} cap.`;

  return `${sold} ${cap}`;
}

export function TicketCard({
  eventName,
  startsAt,
  tierName,
  serial,
  faceValueLamports,
  capCeilingLamports,
  lastSaleLamports,
  points,
  entries,
  className = "",
}: {
  eventName: string;
  startsAt: string;
  tierName: string;
  serial: string;
  faceValueLamports: number;
  capCeilingLamports: number | null;
  lastSaleLamports: number | null;
  points: Array<{ label: string; priceLamports: number | null }>;
  entries: LedgerEntry[];
  className?: string;
}): React.ReactElement {
  // The cap is drawn by the chart, as a dashed rule with its chip on the plot's
  // right edge (brief 4.9). Drawing a second chip in the seat row duplicated it.

  const summary = saleSummary({
    entries,
    faceValueLamports,
    capCeilingLamports,
    lastSaleLamports,
  });

  return (
    <div className={`w-[380px] max-w-full ${className}`}>
      {/*
       * The shadow lives on the wrapper. A mask clips everything the element
       * paints, box-shadow included, so a masked card would lose its only
       * elevation; the wrapper is unmasked and carries it.
       */}
      <div className="rounded-card shadow-card">
        <div
          className="notched relative flex min-h-[220px] flex-col overflow-hidden rounded-card border border-control bg-surface"
          style={notchVars}
        >
          <div className="flex h-[92px] flex-col justify-end px-6">
            {/* Two lines at most, and never shortened: fixture names are real
                and long, so the block above the rule makes room for both. */}
            <p className="h-event line-clamp-2 text-ink">{eventName}</p>
            <p className="figure t-micro-caps mt-1 text-muted">{startLabel(startsAt)}</p>
          </div>

          {/* A flex child would be the one thing that shrank if the card ever
              ran out of room; the rule keeps its 1px. */}
          <Perforation className="shrink-0" />

          <div className="mt-3 flex items-center gap-3 px-6">
            <span className="t-meta min-w-0 truncate text-ink">{tierName}</span>
            <span aria-hidden="true" className="h-4 w-px shrink-0 bg-line" />
            <span className="figure t-meta shrink-0 text-ink">{serial}</span>
          </div>

          {/* The chart labels its own svg, so the wrapper stays in the reading
              order and carries no second, duplicate description. */}
          <div className="mt-2 min-h-[56px] flex-1 px-6 pb-6">
            <PriceHistoryChart
              points={points}
              faceValueLamports={faceValueLamports}
              capCeilingLamports={capCeilingLamports}
              lastSaleLamports={lastSaleLamports}
              variant="ticket"
            />
          </div>

          {/* Drawn fallback for the mask: see the note above NOTCH_Y. */}
          <span
            aria-hidden="true"
            className="bg-canvas pointer-events-none absolute left-[-7px] h-3 w-3 rounded-pill"
            style={{ top: HOLE_TOP }}
          />
          <span
            aria-hidden="true"
            className="bg-canvas pointer-events-none absolute right-[-7px] h-3 w-3 rounded-pill"
            style={{ top: HOLE_TOP }}
          />
        </div>
      </div>

      <p className="t-micro mt-2 text-muted">{summary}</p>

      <div className="mt-6">
        <OwnershipTrail entries={entries} faceValueLamports={faceValueLamports} variant="strip" />
      </div>
    </div>
  );
}

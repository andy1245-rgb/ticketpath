export const LAMPORTS_PER_SOL = 1_000_000_000;

/**
 * Lamports to a SOL string. Ticket prices live in the 0.1–50 SOL range, so we
 * show up to 3 decimals and trim trailing zeros rather than padding to 9.
 */
export function formatSol(lamports: number | null | undefined, opts: { withUnit?: boolean } = {}): string {
  const { withUnit = true } = opts;
  if (lamports == null) return "—";
  const sol = lamports / LAMPORTS_PER_SOL;
  const digits = sol >= 100 ? 1 : sol >= 1 ? 2 : 3;
  const body = sol.toLocaleString("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: digits,
  });
  return withUnit ? `${body} SOL` : body;
}

/** Compact form for stat tiles: 1,284 / 12.9K / 4.2M. */
export function formatCompact(n: number | null | undefined): string {
  if (n == null) return "—";
  if (Math.abs(n) < 10_000) return n.toLocaleString("en-US");
  return n.toLocaleString("en-US", { notation: "compact", maximumFractionDigits: 1 });
}

/** Basis points to a signed percentage. 2500 -> "+25%". */
export function formatMarkup(bps: number | null | undefined): string {
  if (bps == null) return "—";
  const pct = bps / 100;
  const digits = Math.abs(pct) >= 10 ? 0 : 1;
  const sign = pct > 0 ? "+" : "";
  return `${sign}${pct.toFixed(digits)}%`;
}

export function formatPercent(share: number | null | undefined, digits = 0): string {
  if (share == null) return "—";
  return `${(share * 100).toFixed(digits)}%`;
}

/** Truncate a base58 address for display: "7xKX…9mNq". */
export function shortAddress(address: string | null | undefined, lead = 4, tail = 4): string {
  if (!address) return "—";
  if (address.length <= lead + tail + 1) return address;
  return `${address.slice(0, lead)}…${address.slice(-tail)}`;
}

/**
 * What to print where a transaction signature would go. There is no signature on
 * any row today, and an empty link or a dash reads as a loading state; the
 * sentence says the row has no on-chain counterpart at all (brief 5.6).
 */
export function signatureLabel(signature: string | null | undefined): string {
  if (!signature) return "Not on chain";
  return signature;
}

/** Matches a bare calendar date with no time component. */
const DATE_ONLY = /^\d{4}-\d{2}-\d{2}$/;

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  // A date-only string parses as UTC midnight, which renders as the PREVIOUS
  // day everywhere west of UTC. Day-bucketed series keys are date-only, so
  // pin those to UTC instead of shifting them into local time.
  const opts: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
  };
  if (DATE_ONLY.test(iso)) opts.timeZone = "UTC";
  return new Date(iso).toLocaleDateString("en-US", opts);
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

/** "in 12 days" / "3 weeks ago" — used on event cards. */
export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return "—";
  const deltaMs = new Date(iso).getTime() - Date.now();
  const rtf = new Intl.RelativeTimeFormat("en-US", { numeric: "auto" });
  const units: [Intl.RelativeTimeFormatUnit, number][] = [
    ["year", 365 * 24 * 3600_000],
    ["month", 30 * 24 * 3600_000],
    ["week", 7 * 24 * 3600_000],
    ["day", 24 * 3600_000],
    ["hour", 3600_000],
    ["minute", 60_000],
  ];
  for (const [unit, ms] of units) {
    if (Math.abs(deltaMs) >= ms) return rtf.format(Math.round(deltaMs / ms), unit);
  }
  return "now";
}

/** Integer lamports with grouping, for a raw figure the surface wants exact. */
export function formatLamports(lamports: number | null | undefined): string {
  if (lamports == null) return "—";
  return lamports.toLocaleString("en-US");
}

/** Basis points to a plain unsigned percentage: 1800 -> "18%". */
export function formatBpsPercent(bps: number | null | undefined): string {
  if (bps == null) return "—";
  const pct = bps / 100;
  return `${pct.toFixed(Math.abs(pct) >= 10 ? 0 : 1).replace(/\.0$/, "")}%`;
}

/** A ceiling for a buyer's view: a number of SOL, or the word Uncapped. */
export function formatCeiling(lamports: number | null | undefined): string {
  if (lamports == null) return "Uncapped";
  return formatSol(lamports);
}

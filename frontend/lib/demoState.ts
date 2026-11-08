/**
 * The live demo's state, and the rules it obeys.
 *
 * There is no backend behind this page: state lives in `localStorage` under one key and
 * every price rule below is computed in the browser. The arithmetic is not a paraphrase
 * of the contract's, it is the contract's: `isWithinCap` and `capCeilingLamports` are
 * imported from `lib/cap.ts`, which is the same predicate the rest of the app evaluates.
 *
 * What is simulated is the *environment*, not the rule. A sale here is a row written to a
 * local object. The refusal that stops a price above the ceiling carries the code the
 * devnet program actually returned (`6010 E_CAP_EXCEEDED`), recorded in
 * `records/devnet-artefacts.json`, and every screen that shows it says this one is
 * simulated.
 */

import { capCeilingLamports, isWithinCap } from "./cap.ts";
import { LAW_AS_OF, LAW_TABLE_SHA256, LAW_TABLE_VERSION, REGIONS, type RegionRow } from "./demoRegions.ts";

export const STORAGE_KEY = "seatpass.demo.v1";
export const SOL = 1_000_000_000;

export type ResaleMode = "open" | "monitored" | "banned";

export type Hop = {
  kind: "issue" | "resale";
  priceLamports: number;
  wallet: string;
  at: string;
};

export type Ticket = { id: string; serial: string; tier: string; hops: Hop[] };

export type EventConfig = {
  name: string;
  venue: string;
  startsAt: string;
  region: string;
  faceLamports: number;
  /** The platform's own ceiling, in basis points over face. */
  capBps: number;
  /** An organizer override that replaces `capBps`. Never above the law's ceiling. */
  overrideCapBps: number | null;
  resaleMode: ResaleMode;
  artistFee: { on: boolean; bps: number };
  flipTax: boolean;
  /** Manual per-ticket overrides, keyed by ticket serial. Absent on older stored states. */
  ticketOverrides?: Record<string, TicketOverride>;
};

export type TicketOverride = { frozen: boolean; maxLamports: number | null };

export type DemoState = { version: 1; wallet: string; event: EventConfig; tickets: Ticket[] };

export const WALLET = "DemoWa11et7dByerQK3zVn9xLm4sT2pR8hJ6cF1a";

/** The event the demo opens on. A fan-facing event, priced at one SOL. */
export function defaultEvent(): EventConfig {
  return {
    name: "Midnight Static — North American Tour",
    venue: "Aurora Amphitheater, Chicago",
    startsAt: "2026-12-10T18:00:00.000Z",
    region: "US",
    faceLamports: 1 * SOL,
    capBps: 2500,
    overrideCapBps: null,
    resaleMode: "open",
    artistFee: { on: false, bps: 500 },
    flipTax: true,
  };
}

export function defaultState(): DemoState {
  return { version: 1, wallet: WALLET, event: defaultEvent(), tickets: [] };
}

export function regionRow(jurisdiction: string): RegionRow {
  return REGIONS.find((r) => r.jurisdiction === jurisdiction) ?? REGIONS[0];
}

export function platformCapBps(event: EventConfig): number {
  return event.overrideCapBps ?? event.capBps;
}

/** Why the law row matters, in one sentence, taken from the table's own reason code. */
export function lawReasonSentence(row: RegionRow): string {
  switch (row.lawReason) {
    case "law_caps_bps":
      return "The law in force caps the resale price, so the cap it names binds unless the platform cap is lower.";
    case "no_cap_in_force":
      return "No price cap is in force in this jurisdiction. What is in force is a disclosure duty, so the platform cap is the only ceiling.";
    case "other_restriction_only":
      return "The instruments found restrict conduct (bots, disclosure) and cap no price, so the platform cap is the only ceiling.";
    case "designation_not_stated":
      return "A price cap is in force but applies only to designated venues and events, and the register could not be read. Unresolved is not the same as unrestricted.";
    default:
      return "The resolver returned this reason code; the table is the authority, this sentence is a reading of it.";
  }
}

/**
 * The ceiling this event actually has: the law's cap and the platform's, tightened to
 * the lower. `binding` names which one won, because a screen must not print a cap the
 * chain would not hold.
 */
export type Ceiling = {
  row: RegionRow;
  lawBps: number | null;
  platformBps: number;
  binding: "law" | "platform";
  capBps: number;
  ceilingLamports: number;
  /** Set when the demo will not admit a listing at any price, and why. */
  closed: { code: string; reason: string } | null;
};

export function ceilingFor(event: EventConfig): Ceiling {
  const row = regionRow(event.region);
  const platformBps = platformCapBps(event);
  const platformCeiling = capCeilingLamports(event.faceLamports, platformBps);
  const lawBps = row.resalePolicy === "capped" ? row.resaleCapBps : null;
  const lawCeiling = lawBps == null ? null : capCeilingLamports(event.faceLamports, lawBps);
  const lawBinds = lawCeiling != null && lawCeiling < platformCeiling;
  const closed =
    row.resalePolicy === "unresolved"
      ? { code: "LAW_UNRESOLVED", reason: `${event.region} resolves to unresolved (${row.lawReason}).` }
      : event.resaleMode === "banned"
        ? { code: "RESALE_DISABLED", reason: "The organizer switched resale off for this event." }
        : null;
  return {
    row,
    lawBps,
    platformBps,
    binding: lawBinds ? "law" : "platform",
    capBps: lawBinds ? (lawBps as number) : platformBps,
    ceilingLamports: lawBinds ? (lawCeiling as number) : platformCeiling,
    closed,
  };
}

/** `price * 10000 <= face * (10000 + capBps)`, the contract's predicate. */
export function predicate(priceLamports: number, faceLamports: number, capBps: number) {
  return {
    admitted: isWithinCap(priceLamports, faceLamports, capBps),
    left: priceLamports * 10_000,
    right: faceLamports * (10_000 + capBps),
  };
}

export type ListingOutcome =
  | { ok: true; ceiling: Ceiling; taxBps: number; taxLamports: number; feeLamports: number }
  | {
      ok: false;
      code: "E_CAP_EXCEEDED" | "LAW_UNRESOLVED" | "RESALE_DISABLED" | "BAD_PRICE" | "TICKET_FROZEN" | "TICKET_MAX_EXCEEDED";
      title: string;
      detail: string;
      ceiling: Ceiling;
      priceLamports: number;
    };

/**
 * Decide a listing. The order is deliberate: a closed event refuses before arithmetic,
 * and a bad price refuses before either, because neither is a cap breach and printing
 * `6010` for them would be a lie about what the chain did.
 */
export function evaluateListing(args: {
  event: EventConfig;
  ticket: Ticket;
  priceLamports: number;
  nowMs: number;
}): ListingOutcome {
  const { event, ticket, priceLamports, nowMs } = args;
  const ceiling = ceilingFor(event);

  if (!Number.isInteger(priceLamports) || priceLamports <= 0) {
    return { ok: false, code: "BAD_PRICE", title: "A price is a whole number of lamports above zero", detail: `Got ${priceLamports}.`, ceiling, priceLamports };
  }
  if (ceiling.closed) {
    return {
      ok: false,
      code: ceiling.closed.code as "LAW_UNRESOLVED" | "RESALE_DISABLED",
      title: ceiling.closed.code === "RESALE_DISABLED" ? "Resale is off for this event" : "The law here does not resolve",
      detail: ceiling.closed.reason,
      ceiling,
      priceLamports,
    };
  }

  const manual = event.ticketOverrides?.[ticket.serial];
  if (manual?.frozen) {
    return {
      ok: false,
      code: "TICKET_FROZEN",
      title: "The organizer froze resale of this ticket",
      detail: `Ticket ${ticket.serial} has a manual freeze in this event's settings. App policy in this demo, not a chain rule.`,
      ceiling,
      priceLamports,
    };
  }
  if (manual?.maxLamports != null && priceLamports > manual.maxLamports) {
    return {
      ok: false,
      code: "TICKET_MAX_EXCEEDED",
      title: "Above the organizer's maximum for this ticket",
      detail: `Ticket ${ticket.serial} has a per-ticket maximum of ${manual.maxLamports} lamports; ${priceLamports} is above it. App policy in this demo, not a chain rule.`,
      ceiling,
      priceLamports,
    };
  }

  const check = predicate(priceLamports, event.faceLamports, ceiling.capBps);
  if (!check.admitted) {
    return {
      ok: false,
      code: "E_CAP_EXCEEDED",
      title: "6010 E_CAP_EXCEEDED",
      detail: `${priceLamports} * 10000 = ${check.left}, which is above ${event.faceLamports} * (10000 + ${ceiling.capBps}) = ${check.right}. Ceiling is ${ceiling.ceilingLamports} lamports.`,
      ceiling,
      priceLamports,
    };
  }

  const taxBps = event.flipTax ? flipTaxBps(heldSeconds(ticket, nowMs)) : 0;
  return {
    ok: true,
    ceiling,
    taxBps,
    taxLamports: Math.floor((priceLamports * taxBps) / 10_000),
    feeLamports: event.artistFee.on ? Math.floor((priceLamports * event.artistFee.bps) / 10_000) : 0,
  };
}

/** Seconds since the wallet holding the ticket now took it. 0 when there is no hop. */
export function heldSeconds(ticket: Ticket, nowMs: number): number {
  const last = ticket.hops[ticket.hops.length - 1];
  if (!last) return 0;
  return Math.max(0, Math.floor((nowMs - Date.parse(last.at)) / 1000));
}

/**
 * `market_swarm/flip_tax.py` `FlipTaxSchedule.bps_for`, transcribed: full rate under one
 * hour, linear to zero at thirty days, floored. The defaults are the module's.
 */
export function flipTaxBps(
  held: number,
  fullBps = 1_500,
  fullHold = 3_600,
  zeroHold = 2_592_000,
): number {
  if (held <= fullHold) return fullBps;
  if (held >= zeroHold) return 0;
  return Math.floor((fullBps * (zeroHold - held)) / (zeroHold - fullHold));
}

let counter = 0;

function nextSerial(existing: Ticket[]): string {
  counter += 1;
  const n = existing.length + counter;
  return `DMO-${String(n).padStart(4, "0")}`;
}

export function mintTicket(state: DemoState, nowMs: number): DemoState {
  const ticket: Ticket = {
    id: `tkt_demo_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`,
    serial: nextSerial(state.tickets),
    tier: "Floor GA",
    hops: [
      {
        kind: "issue",
        priceLamports: state.event.faceLamports,
        wallet: state.wallet,
        at: new Date(nowMs).toISOString(),
      },
    ],
  };
  return { ...state, tickets: [...state.tickets, ticket] };
}

export function applyListing(
  state: DemoState,
  ticketId: string,
  priceLamports: number,
  nowMs: number,
): DemoState {
  return {
    ...state,
    tickets: state.tickets.map((t) =>
      t.id === ticketId
        ? {
            ...t,
            hops: [
              ...t.hops,
              { kind: "resale", priceLamports, wallet: state.wallet, at: new Date(nowMs).toISOString() },
            ],
          }
        : t,
    ),
  };
}

// ---- storage -------------------------------------------------------------------------
// A static export has no server, so the page is the store. Everything is read inside an
// effect, never during render, so the server-rendered HTML and the first client render
// agree and nothing hydrates into a mismatch.

export function loadState(): DemoState {
  if (typeof window === "undefined") return defaultState();
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultState();
    const parsed = JSON.parse(raw) as DemoState;
    if (parsed.version !== 1 || !parsed.event) return defaultState();
    return parsed;
  } catch {
    return defaultState();
  }
}

export function saveState(state: DemoState): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    // A full or blocked storage is not a reason to break the page; the demo runs in memory.
  }
}

export const LAW_PROVENANCE = { version: LAW_TABLE_VERSION, sha256: LAW_TABLE_SHA256, asOf: LAW_AS_OF };

export function sol(lamports: number): string {
  return `${(lamports / SOL).toFixed(4)} SOL`;
}

export function bpsLabel(bps: number | null): string {
  return bps == null ? "no cap" : `${(bps / 100).toFixed(2)}%`;
}

/**
 * Plain-language lines on what a buyer may do under these settings, derived only from the
 * event and its ceiling. Each line is a reading of a setting this demo applies; none claims
 * the deployed program enforces anything but the cap.
 */
export function buyerSummary(event: EventConfig, ceiling: Ceiling): string[] {
  const lines: string[] = [];
  if (ceiling.closed) {
    lines.push(
      ceiling.closed.code === "RESALE_DISABLED"
        ? "Resale is banned: no ticket can be listed at any price."
        : `Resale is closed: ${ceiling.closed.reason}`,
    );
  } else {
    lines.push(
      `A ticket can be listed up to ${sol(ceiling.ceilingLamports)} (${bpsLabel(ceiling.capBps)} over face; the ${ceiling.binding} cap binds). One lamport more is refused.`,
    );
    if (event.resaleMode === "monitored") lines.push("Listings are marked monitored in the record. No review queue exists in this build.");
  }
  lines.push(
    `Region rule: ${event.region}, ${ceiling.row.resalePolicy}${ceiling.lawBps == null ? "" : `, law ceiling ${bpsLabel(ceiling.lawBps)}`}. A rule table lookup, not a location check on the buyer.`,
  );
  lines.push(
    event.artistFee.on
      ? `Seller pays an artist fee of ${bpsLabel(event.artistFee.bps)} of the resale price.`
      : "No artist fee on resale.",
  );
  lines.push(
    event.flipTax
      ? "Seller pays a flip tax of 15% in the first hour, falling to 0 at 30 days held."
      : "No flip tax.",
  );
  const manual = Object.entries(event.ticketOverrides ?? {});
  for (const [serial, o] of manual) {
    if (o.frozen) lines.push(`Ticket ${serial}: resale frozen by the organizer.`);
    else if (o.maxLamports != null) lines.push(`Ticket ${serial}: organizer maximum ${sol(o.maxLamports)}.`);
  }
  return lines;
}

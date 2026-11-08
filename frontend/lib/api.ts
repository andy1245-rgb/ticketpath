/**
 * The only data-access layer in the app. Components never fetch directly.
 *
 * Two backends sit behind these functions:
 *   - NEXT_PUBLIC_API_BASE_URL unset -> the bundled fixtures in lib/mock,
 *     with aggregates computed in-process so the shapes are realistic.
 *   - NEXT_PUBLIC_API_BASE_URL set   -> real HTTP calls to that origin.
 *
 * Swapping between them requires no component changes. See API_CONTRACT.md for
 * the endpoints the live backend must expose. The transport itself lives in
 * lib/http.ts, so it can be checked without loading the fixtures.
 */

import eventsFixture from "./mock/events.json";
import ticketsFixture from "./mock/tickets.json";
import ledgerFixture from "./mock/ledger.json";
import walletsFixture from "./mock/wallets.json";
import devnetArtefact from "@/data/devnet-artefacts.json";

import { ApiError, buildQuery, paginate, requestJson } from "./http";
import { CLUSTER } from "./solana";

import type {
  ChallengeResponse,
  DataSource,
  DestinationRow,
  DevnetArtefact,
  DevnetRecord,
  Event,
  EventAnalytics,
  EventQuery,
  Guidance,
  Health,
  LedgerEntry,
  MarkupBucket,
  Page,
  PricePoint,
  ResaleHistory,
  ResaleStats,
  Ticket,
  TicketQuery,
  WalletAddress,
  WalletVerification,
} from "./types";

export { ApiError };

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "";

export const isMockMode = BASE_URL === "";

/**
 * What every mock payload says about itself. The wording is fixed: a reader has
 * to be able to tell bundled fixtures from a server that answered, and the note
 * is the way out of the ambiguity. The backend's own dataSource is passed
 * through untouched in live mode.
 */
export const MOCK_DATA_SOURCE: DataSource = {
  mode: "bundled-fixture",
  synthetic: true,
  label:
    "BUNDLED MOCK DATA. Generated from lib/mock on this machine, not read from the backend.",
  note: "Set NEXT_PUBLIC_API_BASE_URL to read the backend instead.",
};

/**
 * The one reason a mock-mode verification gives, in the same shape as the
 * backend's own flags (`wallet_not_verified`), so a screen can print either
 * without pretending to know which kind of deployment it is running in.
 */
const MOCK_UNVERIFIED_FLAG =
  "mock_mode: this build checks no signature, so no wallet is verified";

/**
 * Kept only so the pre-rebuild /my-tickets screen still compiles while it is
 * replaced. Nothing in this module reads it, no wallet is auto-connected, and it
 * should go with that screen.
 */
export const MOCK_DEMO_WALLET: WalletAddress = walletsFixture.demoWallet;

/** The live seam. One place that knows the origin and the transport. */
function request<T>(path: string, init?: RequestInit): Promise<T> {
  return requestJson<T>(BASE_URL, path, init);
}

// ---------------------------------------------------------------------------
// Mock-mode helpers
// ---------------------------------------------------------------------------

const MOCK_EVENTS = eventsFixture as Event[];
const MOCK_TICKETS = ticketsFixture as Ticket[];
const MOCK_LEDGER = ledgerFixture as LedgerEntry[];

/**
 * The bundled fixtures were written for a demo, so they carry a made-up
 * signature and slot on all 253 rows and give `issue` rows a price equal to
 * face. The live backend returns null for both, because no transaction exists
 * for any of these rows. Rendering the fixture values would put an invented
 * on-chain fact on screen with a working explorer link beside it, so mock mode
 * drops them at the seam and never shows a transaction it cannot stand behind.
 */
function sanitiseEntry(entry: LedgerEntry): LedgerEntry {
  const priced = entry.kind === "sale";
  return {
    ...entry,
    priceLamports: priced ? entry.priceLamports : null,
    markupBps: priced ? entry.markupBps : null,
    signature: null,
    slot: null,
  };
}

const MOCK_LEDGER_SOURCED = MOCK_LEDGER.map(sanitiseEntry);

/** Simulated latency so loading states are exercised in development. */
const settle = <T,>(value: T): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(value), isMockMode ? 120 : 0));

/** Every mock payload that the backend would source gets the same block. */
function withSource<T extends object>(payload: T): T & { dataSource: DataSource } {
  return { ...payload, dataSource: MOCK_DATA_SOURCE };
}

function walletRegion(wallet: WalletAddress): string | null {
  return walletsFixture.verified.find((w) => w.wallet === wallet)?.region ?? null;
}

function computeStats(entries: LedgerEntry[]): ResaleStats {
  const sales = entries.filter((e) => e.kind === "sale" && e.priceLamports != null);
  const prices = sales.map((e) => e.priceLamports as number);
  const markups = sales.map((e) => e.markupBps as number);
  const holders = new Set<string>();
  for (const e of entries) {
    if (e.fromWallet) holders.add(e.fromWallet);
    if (e.toWallet) holders.add(e.toWallet);
  }
  return {
    saleCount: sales.length,
    transferCount: entries.filter((e) => e.kind === "sale" || e.kind === "transfer").length,
    avgMarkupBps: markups.length ? Math.round(markups.reduce((a, b) => a + b, 0) / markups.length) : null,
    peakPriceLamports: prices.length ? Math.max(...prices) : null,
    lastPriceLamports: prices.length ? prices[prices.length - 1] : null,
    totalVolumeLamports: prices.reduce((a, b) => a + b, 0),
    uniqueWallets: holders.size,
  };
}

function median(values: number[]): number | null {
  if (!values.length) return null;
  const s = [...values].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : Math.round((s[mid - 1] + s[mid]) / 2);
}

const MARKUP_BUCKETS: Array<[string, number, number | null]> = [
  ["At or below face", -10_000, 1],
  ["0–25%", 1, 2_500],
  ["25–50%", 2_500, 5_000],
  ["50–100%", 5_000, 10_000],
  ["100–200%", 10_000, 20_000],
  ["Over 200%", 20_000, null],
];

function buildAnalytics(event: Event): EventAnalytics {
  const ticketIds = new Set(MOCK_TICKETS.filter((t) => t.eventId === event.id).map((t) => t.id));
  const eventTickets = MOCK_TICKETS.filter((t) => ticketIds.has(t.id));
  const entries = MOCK_LEDGER_SOURCED.filter((e) => ticketIds.has(e.ticketId));
  const sales = entries.filter((e) => e.kind === "sale" && e.priceLamports != null);

  // Group sales by day for the price curve.
  const byDay = new Map<string, { total: number; count: number; markups: number[] }>();
  for (const s of sales) {
    const day = s.occurredAt.slice(0, 10);
    const slot = byDay.get(day) ?? { total: 0, count: 0, markups: [] };
    slot.total += s.priceLamports as number;
    slot.count += 1;
    // Each sale's markup is already relative to its own ticket's face value.
    if (s.markupBps != null) slot.markups.push(s.markupBps);
    byDay.set(day, slot);
  }
  const priceSeries: PricePoint[] = [...byDay.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, { total, count, markups }]) => ({
      date,
      avgPriceLamports: Math.round(total / count),
      saleCount: count,
      avgMarkupBps: markups.length
        ? Math.round(markups.reduce((a, b) => a + b, 0) / markups.length)
        : null,
    }));

  const markups = sales.map((s) => s.markupBps as number);
  const markupDistribution: MarkupBucket[] = MARKUP_BUCKETS.map(([label, fromBps, toBps]) => ({
    label,
    fromBps,
    toBps,
    count: markups.filter((m) => m >= fromBps && (toBps == null || m < toBps)).length,
  }));

  // Destination roll-up: current holders, flagged by how they acquired.
  const holdings = new Map<string, { count: number; secondary: boolean }>();
  for (const t of eventTickets) {
    const slot = holdings.get(t.ownerWallet) ?? { count: 0, secondary: false };
    slot.count += 1;
    if (t.ownerWallet !== t.issuedToWallet) slot.secondary = true;
    holdings.set(t.ownerWallet, slot);
  }
  const topDestinations: DestinationRow[] = [...holdings.entries()]
    .map(([wallet, { count, secondary }]) => ({
      wallet,
      ticketCount: count,
      region: walletRegion(wallet),
      acquiredOnSecondary: secondary,
    }))
    .sort((a, b) => b.ticketCount - a.ticketCount)
    .slice(0, 12);

  const resoldIds = new Set(sales.map((s) => s.ticketId));
  const faceValues = event.tiers.map((t) => t.faceValueLamports);

  return {
    eventId: event.id,
    faceValueLamports: faceValues.length ? Math.min(...faceValues) : 0,
    totalVolumeLamports: sales.reduce((a, s) => a + (s.priceLamports as number), 0),
    saleCount: sales.length,
    avgMarkupBps: markups.length ? Math.round(markups.reduce((a, b) => a + b, 0) / markups.length) : null,
    medianResalePriceLamports: median(sales.map((s) => s.priceLamports as number)),
    resoldShare: eventTickets.length ? resoldIds.size / eventTickets.length : 0,
    uniqueHolders: holdings.size,
    priceSeries,
    markupDistribution,
    topDestinations,
    dataSource: MOCK_DATA_SOURCE,
    analyticsNote:
      "Bundled fixtures: avgMarkupBps is the mean of per-sale markups, each against its own ticket's face value.",
  };
}

function mockVerification(wallet: WalletAddress): WalletVerification {
  // A fixture row that says a wallet was verified is a row somebody typed, not a
  // signature anybody checked, and this build has no key, no server and no cluster
  // to check one against. So the answer is never `verified: true` here, and the flag
  // says why in the same machine vocabulary the backend uses for its own refusals.
  // The fixture's own `verified` list still supplies a region, which is a fixture
  // fact about a wallet and not a claim that anything was checked.
  return {
    wallet,
    verified: false,
    verifiedAt: null,
    method: null,
    canPurchase: false,
    canReceiveTransfer: false,
    flags: [MOCK_UNVERIFIED_FLAG],
    dataSource: MOCK_DATA_SOURCE,
  };
}

/**
 * A health payload for a mode with no server. Every answer that would come from
 * a cluster says no, and `reason` says why: there is nothing here to ask.
 */
function mockHealth(): Health {
  return {
    service: "ticketing-frontend (bundled fixtures)",
    version: "0.1.0",
    status: "ok",
    now: new Date().toISOString(),
    dataSource: MOCK_DATA_SOURCE,
    chain: {
      programDeployed: false,
      askedCluster: false,
      rpcEnabled: false,
      programId: null,
      cluster: CLUSTER,
      reason: "mock_mode",
      detail:
        "No backend is configured, so this process asked no cluster and read no artefact. Nothing here is a deployment claim.",
      // The path the backend's own report uses, kept so the shape matches.
      designDoc: "docs/ON-CHAIN-DESIGN.md",
      recorded: null,
    },
    pricingModel: {
      available: false,
      modelVersion: null,
      reason: "mock_mode",
      kind: null,
      fitted: null,
      note: "Mock mode reads no pricing engine, so there is no model to describe.",
    },
    contract: {
      source: "API_CONTRACT.md",
      endpointsInContract: 9,
      endpointsImplemented: 0,
      routesImplemented: 0,
      map: "No backend is configured.",
    },
  };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export async function getEvents(query: EventQuery = {}): Promise<Page<Event>> {
  if (!isMockMode) return request<Page<Event>>(`/api/events${buildQuery({ ...query })}`);

  let items = MOCK_EVENTS;
  if (query.status) items = items.filter((e) => e.status === query.status);
  if (query.city) items = items.filter((e) => e.city === query.city);
  if (query.q) {
    const needle = query.q.toLowerCase();
    items = items.filter(
      (e) => e.name.toLowerCase().includes(needle) || e.venue.toLowerCase().includes(needle),
    );
  }
  items = [...items].sort((a, b) => a.startsAt.localeCompare(b.startsAt));
  return settle(withSource(paginate(items, query.cursor, query.limit ?? 50)));
}

export async function getEvent(idOrSlug: string): Promise<Event> {
  if (!isMockMode) return request<Event>(`/api/events/${encodeURIComponent(idOrSlug)}`);

  const event = MOCK_EVENTS.find((e) => e.id === idOrSlug || e.slug === idOrSlug);
  if (!event) {
    throw new ApiError(
      `Event ${idOrSlug} not found`,
      404,
      "not_found",
      `/api/events/${idOrSlug}`,
    );
  }
  return settle(withSource(event));
}

export async function getTickets(query: TicketQuery = {}): Promise<Page<Ticket>> {
  if (!isMockMode) return request<Page<Ticket>>(`/api/tickets${buildQuery({ ...query })}`);

  let items = MOCK_TICKETS;
  if (query.eventId) items = items.filter((t) => t.eventId === query.eventId);
  if (query.ownerWallet) items = items.filter((t) => t.ownerWallet === query.ownerWallet);
  if (query.status) items = items.filter((t) => t.status === query.status);
  return settle(withSource(paginate(items, query.cursor, query.limit ?? 50)));
}

export async function getTicket(ticketId: string): Promise<Ticket> {
  if (!isMockMode) return request<Ticket>(`/api/tickets/${encodeURIComponent(ticketId)}`);

  const ticket = MOCK_TICKETS.find((t) => t.id === ticketId || t.mintAddress === ticketId);
  if (!ticket) {
    throw new ApiError(
      `Ticket ${ticketId} not found`,
      404,
      "not_found",
      `/api/tickets/${ticketId}`,
    );
  }
  return settle(withSource(ticket));
}

/** Price history + full custody trail for one ticket. */
export async function getResaleHistory(ticketId: string): Promise<ResaleHistory> {
  if (!isMockMode) {
    return request<ResaleHistory>(`/api/tickets/${encodeURIComponent(ticketId)}/resale-history`);
  }

  const ticket = MOCK_TICKETS.find((t) => t.id === ticketId);
  if (!ticket) {
    throw new ApiError(
      `Ticket ${ticketId} not found`,
      404,
      "not_found",
      `/api/tickets/${ticketId}`,
    );
  }
  const entries = MOCK_LEDGER_SOURCED.filter((e) => e.ticketId === ticketId).sort((a, b) =>
    a.occurredAt.localeCompare(b.occurredAt),
  );
  return settle(
    withSource({
      ticketId,
      faceValueLamports: ticket.faceValueLamports,
      entries,
      stats: computeStats(entries),
    }),
  );
}

export async function getWalletVerification(wallet: WalletAddress): Promise<WalletVerification> {
  if (!isMockMode) {
    return request<WalletVerification>(`/api/wallets/${encodeURIComponent(wallet)}/verification`);
  }
  return settle(mockVerification(wallet));
}

/** Step 1 of verification: ask the backend for a nonce to sign. */
export async function startWalletVerification(
  wallet: WalletAddress,
): Promise<ChallengeResponse> {
  if (!isMockMode) {
    return request<ChallengeResponse>(
      `/api/wallets/${encodeURIComponent(wallet)}/verification/challenge`,
      { method: "POST" },
    );
  }
  return settle(
    withSource({
      nonce: `mock-nonce-${Math.random().toString(36).slice(2, 10)}`,
      expiresAt: new Date(Date.now() + 5 * 60_000).toISOString(),
    }),
  );
}

/** Step 2: submit the signed nonce. Backend verifies against the pubkey. */
export async function completeWalletVerification(args: {
  wallet: WalletAddress;
  nonce: string;
  /** base58-encoded detached signature over `verificationMessage(wallet, nonce)`. */
  signature: string;
}): Promise<WalletVerification> {
  if (!isMockMode) {
    return request<WalletVerification>(
      `/api/wallets/${encodeURIComponent(args.wallet)}/verification`,
      { method: "POST", body: JSON.stringify({ nonce: args.nonce, signature: args.signature }) },
    );
  }
  return settle({
    ...mockVerification(args.wallet),
    // No signature is checked in mock mode, because there is no key here to check
    // one against. This branch used to answer `verified: true` and the clock's own
    // instant to whichever payload arrived, and the screen printed a sentence
    // claiming a backend had recorded it. On a public deployment anyone can put the
    // screen in that state, so the only true answer is that this build verifies no
    // wallet at all.
    verified: false,
    verifiedAt: null,
    method: null,
    canPurchase: false,
    canReceiveTransfer: false,
    flags: [MOCK_UNVERIFIED_FLAG],
  });
}

/** Organizer analytics roll-up for one event. */
export async function getEventAnalytics(eventId: string): Promise<EventAnalytics> {
  if (!isMockMode) {
    return request<EventAnalytics>(`/api/events/${encodeURIComponent(eventId)}/analytics`);
  }
  const event = MOCK_EVENTS.find((e) => e.id === eventId);
  if (!event) {
    throw new ApiError(
      `Event ${eventId} not found`,
      404,
      "not_found",
      `/api/events/${eventId}`,
    );
  }
  return settle(buildAnalytics(event));
}

/**
 * GET /health: what the server is, where its data came from, and what it has
 * actually checked. In mock mode this answers for the fixtures and claims
 * nothing about a chain.
 */
export async function getHealth(): Promise<Health> {
  if (!isMockMode) return request<Health>("/health");
  return settle(mockHealth());
}

/**
 * GET /devnet-record.json: the artefact file the server itself loaded.
 *
 * Not a contract endpoint, so it is not in API_CONTRACT.md and no component
 * treats it as one. It carries `loaded: false` when there is no file to read,
 * which is a state a page prints rather than an error to throw: a screen that
 * says "no record" is a better answer than a screen that dies.
 */
export async function getDevnetRecord(): Promise<DevnetRecord> {
  if (!isMockMode) return request<DevnetRecord>("/devnet-record.json");
  // This build has no backend, so the record it prints travels inside the build:
  // `tools/site_records.py` copies `records/devnet-artefacts.json` into `data/`
  // byte for byte, and its `--check` proves the copy is still that record. It is a
  // recorded verification and not a live read, which is why the pages that print
  // it say no cluster was asked.
  return settle({
    source: "records/devnet-artefacts.json",
    loaded: true,
    record: devnetArtefact as DevnetArtefact,
    note:
      "Bundled with the build by tools/site_records.py: this is the record a verified run " +
      "wrote, copied from the repository, not a read of any cluster.",
  });
}

/**
 * GET /guidance.json: the engine's refusals for one event, as sentences, with
 * the count beside them.
 *
 * Bundled fixtures carry no guidance payload, and inventing one would be a
 * screenshot of a refusal nobody computed. Mock mode therefore raises the same
 * typed error a missing backend raises, and the caller prints that instead of a
 * number.
 */
export async function getGuidance(
  query: { event?: string; tier?: string; mode?: string } = {},
): Promise<Guidance> {
  if (isMockMode) {
    throw new ApiError(
      "This build reads its bundled fixtures, so there is no refusal list to read.",
      503,
      "no_backend",
      "/guidance.json",
    );
  }
  return request<Guidance>(`/guidance.json${buildQuery(query)}`);
}

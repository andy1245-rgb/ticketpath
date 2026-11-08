/**
 * Wire types shared with the backend.
 *
 * This file is the contract. Every field here is what the API is expected to
 * return; see API_CONTRACT.md for the endpoint-by-endpoint mapping. Money is
 * always an integer count of lamports (never a float, never a formatted
 * string) and every timestamp is an ISO-8601 UTC string.
 */

export type SolanaCluster = "devnet" | "testnet" | "mainnet-beta" | "localnet";

/** 32-byte base58 public key. Kept as a branded-ish alias for readability. */
export type WalletAddress = string;

export type EventStatus =
  | "draft"
  | "on_sale"
  | "sold_out"
  | "completed"
  | "cancelled";

export type TicketStatus = "valid" | "listed" | "redeemed" | "revoked";

/**
 * Every row in a ticket's provenance trail. `issue` is the original mint,
 * `redeem` is scan-in at the door; the two that carry resale data are `sale`
 * (money changed hands) and `transfer` (custody moved, price may be null).
 */
export type LedgerEntryKind = "issue" | "sale" | "transfer" | "redeem" | "revoke";

/**
 * Where a payload came from. Every response the backend serves carries one: the
 * page envelopes, the single-record reads, analytics, resale history, wallet
 * verification and the challenge.
 *
 * `mode` stays a plain string on purpose. The backend has already used more
 * than one word here (`synthetic-fixture`, `in-memory-verification`), and a
 * closed union would turn the next honest label into a type error.
 */
export interface DataSource {
  mode: string;
  /** True when nothing in the payload was collected from the real world. */
  synthetic: boolean;
  /** The backend's own sentence. Rendered unparaphrased when synthetic. */
  label: string;
  note: string;
}

/** One statute or regulation behind an event's resale policy. */
export interface LawBasis {
  /** Region code the row applies to, e.g. "CA-ON". */
  jurisdiction: string;
  citation: string;
  url: string;
  /** Evidence grade the backend assigns the row: "A" through "E". */
  confidence: string;
  /** e.g. "in_force", "not_yet_in_force". */
  status: string;
}

/**
 * The ceiling the contract would actually hold, which is not necessarily the
 * event's own `resalePriceCapBps`: the law and the platform both cap, in
 * different bases, and the stricter one wins. `bindingRule` says which produced
 * the number, so a product decision is never attributed to a law.
 */
export interface EnforcedCap {
  enforcedBaseLamports: number;
  enforcedCapBps: number;
  enforcedCeilingLamports: number;
  bindingRule: "law" | "platform";
  /** The organiser's configured cap, which may be null on an uncapped event. */
  platformCapBps: number | null;
}

/**
 * Per-tier ceiling. The cap is a multiple of each tier's own face value, so an
 * event-wide number is wrong the moment the tiers differ.
 *
 * One caveat from the live payload: a tier with no ceiling at all arrives as
 * `{ tierId, enforcedCap: null }` rather than these fields. Callers read
 * `enforcedCapByTier` defensively, never assuming `enforcedCeilingLamports` is
 * there.
 */
export interface EnforcedCapTier extends EnforcedCap {
  tierId: string;
}

export interface Organizer {
  id: string;
  name: string;
  walletAddress: WalletAddress;
  verified: boolean;
}

export interface TicketTier {
  id: string;
  name: string;
  faceValueLamports: number;
  totalSupply: number;
  issuedCount: number;
}

export interface Event {
  id: string;
  slug: string;
  name: string;
  description: string;
  venue: string;
  city: string;
  /** ISO-8601 UTC. */
  startsAt: string;
  endsAt: string | null;
  imageUrl: string | null;
  organizer: Organizer;
  status: EventStatus;
  tiers: TicketTier[];
  totalSupply: number;
  issuedCount: number;
  /** Whether holders may transfer at all. */
  resaleEnabled: boolean;
  /**
   * Hard ceiling on resale price as basis points over face value.
   * 2500 = resale capped at +25%. `null` means uncapped (still tracked).
   */
  resalePriceCapBps: number | null;
  /** Transfers only permitted to wallets that passed verification. */
  requiresVerifiedWallet: boolean;

  // -- additive fields the live backend serves and API_CONTRACT.md omits --

  /** ISO region code the law table resolves against, or null when none applies. */
  jurisdiction?: string | null;
  /** The resolved policy kind, e.g. "capped". Null when it was not computed. */
  resalePolicy?: string | null;
  /** Why the policy resolved that way, e.g. "law_caps_bps". */
  resalePolicyReason?: string | null;
  lawTableVersion?: string | null;
  /** The date the law table was resolved against, YYYY-MM-DD. */
  lawAsOf?: string | null;
  lawBasis?: LawBasis[];
  /** Null when the tiers disagree or no ceiling could be resolved. */
  enforcedCap?: EnforcedCap | null;
  enforcedCapByTier?: EnforcedCapTier[];
}

export interface Ticket {
  id: string;
  eventId: string;
  tierId: string;
  /** SPL mint address of the wallet-bound token. */
  mintAddress: string;
  /** Human-facing serial, e.g. "GA-0142". */
  serial: string;
  ownerWallet: WalletAddress;
  /** The wallet this ticket was originally issued to. */
  issuedToWallet: WalletAddress;
  faceValueLamports: number;
  /** Price of the most recent `sale` entry, or null if never resold. */
  lastSalePriceLamports: number | null;
  /** Count of `sale` + `transfer` entries. Face-value issue does not count. */
  transferCount: number;
  status: TicketStatus;
  /** On-chain transfer restriction is currently enforced for this mint. */
  transferRestricted: boolean;
  issuedAt: string;
  redeemedAt: string | null;
  /** Present on a single-ticket read; the envelope carries it on a list. */
  dataSource?: DataSource;
}

export interface LedgerEntry {
  id: string;
  ticketId: string;
  kind: LedgerEntryKind;
  fromWallet: WalletAddress | null;
  toWallet: WalletAddress | null;
  /** Null for non-monetary transfers (gifts, reissues, redemptions). */
  priceLamports: number | null;
  /** Basis points over face value. Null when priceLamports is null. */
  markupBps: number | null;
  /** Solana transaction signature, for explorer deep-links. */
  signature: string | null;
  slot: number | null;
  occurredAt: string;
}

export interface ResaleStats {
  saleCount: number;
  transferCount: number;
  /** Mean markup over face value across all `sale` entries, in basis points. */
  avgMarkupBps: number | null;
  peakPriceLamports: number | null;
  lastPriceLamports: number | null;
  /** Sum of every sale price — the "how much is this ticket churning" figure. */
  totalVolumeLamports: number;
  /** Distinct wallets that have ever held this ticket. */
  uniqueWallets: number;
}

/** Response of `getResaleHistory(ticketId)`. */
export interface ResaleHistory {
  ticketId: string;
  faceValueLamports: number;
  /** Chronological, oldest first. Includes non-sale entries for the trail. */
  entries: LedgerEntry[];
  stats: ResaleStats;
  dataSource?: DataSource;
  /** One sentence from the backend about why signature and slot are empty. */
  custodyNote?: string;
}

export type VerificationMethod = "wallet_signature" | "identity" | null;

export interface WalletVerification {
  wallet: WalletAddress;
  verified: boolean;
  verifiedAt: string | null;
  method: VerificationMethod;
  /** Gates the buy flow. */
  canPurchase: boolean;
  /** Gates being a transfer destination on restricted events. */
  canReceiveTransfer: boolean;
  /** Machine-readable reasons when a capability is false. */
  flags: string[];
  dataSource?: DataSource;
}

/** Response of `startWalletVerification(wallet)`. */
export interface ChallengeResponse {
  /** 32 hex characters, single use, bound to the wallet that asked. */
  nonce: string;
  expiresAt: string;
  dataSource?: DataSource;
}

/** One point on an event's resale price curve. */
export interface PricePoint {
  /** ISO-8601 calendar date, YYYY-MM-DD. Bucketed in UTC. */
  date: string;
  avgPriceLamports: number;
  saleCount: number;
  /**
   * Mean markup across that day's sales, each measured against *its own
   * ticket's* face value. Must not be re-derived from avgPriceLamports and an
   * event-level face value: on a multi-tier event those are different numbers
   * and the result is badly overstated.
   */
  avgMarkupBps: number | null;
}

export interface MarkupBucket {
  label: string;
  /** Inclusive lower bound in basis points. */
  fromBps: number;
  /** Exclusive upper bound; null means open-ended. */
  toBps: number | null;
  count: number;
}

/** Where tickets ended up — the core data-collection output. */
export interface DestinationRow {
  wallet: WalletAddress;
  ticketCount: number;
  /** Non-null only when the wallet voluntarily attached a region. */
  region: string | null;
  /** True if this wallet acquired via resale rather than primary issue. */
  acquiredOnSecondary: boolean;
}

export interface EventAnalytics {
  eventId: string;
  /** Lowest tier face value — the "from" price, not a single event-wide face. */
  faceValueLamports: number;
  totalVolumeLamports: number;
  saleCount: number;
  avgMarkupBps: number | null;
  medianResalePriceLamports: number | null;
  /** Share of issued tickets that have been resold at least once, 0–1. */
  resoldShare: number;
  uniqueHolders: number;
  priceSeries: PricePoint[];
  markupDistribution: MarkupBucket[];
  topDestinations: DestinationRow[];
  dataSource?: DataSource;
  /** How the backend says avgMarkupBps was measured. Printed, never paraphrased. */
  analyticsNote?: string;
}

/** Cursor-paginated list envelope used by the collection endpoints. */
export interface Page<T> {
  items: T[];
  nextCursor: string | null;
  dataSource?: DataSource;
}

export interface EventQuery {
  status?: EventStatus;
  city?: string;
  /** Free-text match against name and venue. */
  q?: string;
  cursor?: string;
  limit?: number;
}

export interface TicketQuery {
  eventId?: string;
  ownerWallet?: WalletAddress;
  status?: TicketStatus;
  cursor?: string;
  limit?: number;
}

/** GET /health — the liveness and honesty surface. */
export interface Health {
  service: string;
  version: string;
  status: string;
  /** ISO-8601 UTC. */
  now: string;
  dataSource: DataSource;
  chain: ChainStatus;
  pricingModel: PricingModelStatus;
  contract: ContractStatus;
}

/**
 * What the server was told, what a verified artefact records, and what it
 * actually asked. `programDeployed` is false whenever the server did not query a
 * cluster, which is not the same claim as "nothing is deployed" — `reason` and
 * `askedCluster` are what make that distinction readable.
 */
export interface ChainStatus {
  programDeployed: boolean;
  /** False means the server asked no cluster at all. */
  askedCluster: boolean;
  rpcEnabled: boolean;
  programId: string | null;
  cluster: string;
  /** e.g. "rpc_disabled". */
  reason: string;
  detail: string;
  designDoc: string;
  /** Null when no verified artefact exists to quote. */
  recorded: RecordedProgram | null;
}

/** A program id a file records. Carries no deployment claim. */
export interface RecordedProgram {
  programId: string;
  cluster: string | null;
  mint: string | null;
  /** The file it came from, so it cannot be mistaken for a read. */
  source: string;
  checkedAt: string | null;
  checkerVersion: string | null;
}

/**
 * `available` means something sits behind the engine seam. It never means a
 * model was fitted: `kind` and `fitted` answer that, and every one of them is
 * null when no model is registered.
 */
export interface PricingModelStatus {
  available: boolean;
  modelVersion: string | null;
  reason: string;
  kind: string | null;
  fitted: boolean | null;
  note: string | null;
}

/** How much of the documented contract the server says it implements. */
export interface ContractStatus {
  source: string;
  endpointsInContract: number;
  endpointsImplemented: number;
  routesImplemented: number;
  map: string;
}

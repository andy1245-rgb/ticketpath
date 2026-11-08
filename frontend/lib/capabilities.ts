/**
 * What this build can and cannot do, in one place.
 *
 * Every entry is false because the backend does not serve it. Section 6.1 of
 * the brief: a false capability renders one Unavailable panel naming what is
 * missing, which endpoint would fill it, and what the screen does show instead.
 * Nothing here is a silent disabled control and nothing here fakes a success.
 */

export type CapabilityKey =
  | "purchase"
  | "listings"
  | "doorCode"
  | "eventCreation"
  | "transfers"
  | "refunds"
  | "auth";

export interface Capability {
  /** Always false in this build. */
  readonly available: false;
  /** The thing the backend does not do. */
  readonly missing: string;
  /** The endpoint that would fill it, in contract form. */
  readonly endpoint: string;
  /** What the screen does show instead of the missing control. */
  readonly shows: string;
}

export const capabilities: Readonly<Record<CapabilityKey, Capability>> = {
  purchase: {
    available: false,
    missing: "A checkout, payment, fee and settlement endpoint. There is none, and no fee field in any record.",
    endpoint: "POST /api/tickets/:ticketId/purchase (not in the contract)",
    shows:
      "The ticket's face value, its enforced cap, whether the event requires a verified wallet, and the wallet verification result.",
  },
  listings: {
    available: false,
    missing:
      "A marketplace. Nothing creates a listing, no ticket ever reaches status listed, and there is no endpoint to browse or buy one.",
    endpoint: "GET /api/listings, POST /api/listings (not in the contract)",
    shows:
      "The resale rule for a single ticket, and the price the contract would accept against its face value and cap.",
  },
  doorCode: {
    available: false,
    missing:
      "A door code, a QR format and an offline verification path. No endpoint issues one and no code format exists.",
    endpoint: "GET /api/tickets/:ticketId/door-code (not in the contract)",
    shows:
      "The ticket's serial, status, redemption time and current owner, read from the fields that do exist.",
  },
  eventCreation: {
    available: false,
    missing:
      "Event creation and ticket issuance. There is no endpoint, and the resale cap is immutable once the record is initialised.",
    endpoint: "POST /api/events (not in the contract)",
    shows:
      "The cap rule as the contract applies it, and the fact that the cap is fixed at record initialisation.",
  },
  transfers: {
    available: false,
    missing: "A transfer endpoint. Custody moves are fixture rows only.",
    endpoint: "POST /api/tickets/:ticketId/transfer (not in the contract)",
    shows: "The full custody trail, so every past move is readable even though a new one cannot be made.",
  },
  refunds: {
    available: false,
    missing: "A refund or revoke endpoint. The program has no redeem or revoke instruction either.",
    endpoint: "POST /api/tickets/:ticketId/refund (not in the contract)",
    shows: "The ticket's status and any redemption already recorded in the ledger.",
  },
  auth: {
    available: false,
    missing:
      "Any account, session or authorization layer. The only check the backend performs is an Ed25519 signature over a nonce.",
    endpoint: "POST /api/session (not in the contract)",
    shows:
      "Wallet signature verification, its frozen message, the flags it returns, and the cluster the server reports.",
  },
};

export function cap(key: CapabilityKey): Capability {
  return capabilities[key];
}

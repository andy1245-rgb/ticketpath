import assert from "node:assert/strict";
import test from "node:test";
import { buyerSummary, ceilingFor, defaultEvent, evaluateListing, SOL, type Ticket } from "./demoState.ts";

const ticket: Ticket = { id: "t1", serial: "DMO-0001", tier: "GA", hops: [{ kind: "issue", priceLamports: SOL, wallet: "w", at: "2026-01-01T00:00:00.000Z" }] };
const now = Date.parse("2026-01-01T00:10:00.000Z");

test("the demo opens with the 25 percent cap in force", () => {
  const c = ceilingFor(defaultEvent());
  assert.equal(c.capBps, 2500);
  assert.equal(c.closed, null);
});

test("banned, frozen and per-ticket max refuse before the cap", () => {
  const base = defaultEvent();
  assert.equal(evaluateListing({ event: { ...base, resaleMode: "banned" }, ticket, priceLamports: SOL, nowMs: now }).ok, false);
  const frozen = { ...base, ticketOverrides: { "DMO-0001": { frozen: true, maxLamports: null } } };
  const f = evaluateListing({ event: frozen, ticket, priceLamports: SOL, nowMs: now });
  assert.equal(!f.ok && f.code, "TICKET_FROZEN");
  const capped = { ...base, ticketOverrides: { "DMO-0001": { frozen: false, maxLamports: 1.1 * SOL } } };
  const m = evaluateListing({ event: capped, ticket, priceLamports: 1.2 * SOL, nowMs: now });
  assert.equal(!m.ok && m.code, "TICKET_MAX_EXCEEDED");
  assert.equal(evaluateListing({ event: capped, ticket, priceLamports: 1.1 * SOL, nowMs: now }).ok, true);
});

test("the summary names the ban", () => {
  const e = { ...defaultEvent(), resaleMode: "banned" as const };
  assert.match(buyerSummary(e, ceilingFor(e))[0], /banned/);
});

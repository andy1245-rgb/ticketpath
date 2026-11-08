import assert from "node:assert/strict";
import { test } from "node:test";

import {
  formatBpsPercent,
  formatLamports,
  formatMarkup,
  formatPercent,
  formatSol,
  shortAddress,
  signatureLabel,
} from "./format.ts";
import type { LedgerEntry } from "./types.ts";

test("lamports format as integers, and as SOL only at the edge", () => {
  // Raw figures stay exact: grouping, no decimal, no rounding.
  assert.equal(formatLamports(1_250_000_001), "1,250,000,001");
  assert.equal(formatLamports(0), "0");
  assert.equal(formatLamports(null), "—");

  assert.equal(formatSol(1_250_000_000), "1.25 SOL");
  assert.equal(formatSol(900_000_000), "0.9 SOL", "trailing zeros are trimmed, not padded to nine");
  assert.equal(formatSol(150_000_000), "0.15 SOL");
  assert.equal(formatSol(1_250_000_000, { withUnit: false }), "1.25");
  assert.equal(formatSol(null), "—");

  assert.equal(formatPercent(0.6428571428571429), "64%");
  assert.equal(formatPercent(null), "—");
  assert.equal(formatBpsPercent(1800), "18%");
  assert.equal(formatBpsPercent(2500), "25%");
  assert.equal(formatBpsPercent(null), "—");
});

test("markup basis points round the way the figure is shown", () => {
  assert.equal(formatMarkup(2500), "+25%");
  assert.equal(formatMarkup(850), "+8.5%");
  // 3650 bps is 36.5%, and the helper drops the decimal once the figure is
  // above 10%, so the shown number is 37 — the rounded one, not the truncated.
  assert.equal(formatMarkup(3650), "+37%");
  assert.equal(formatMarkup(-1000), "-10%");
  assert.equal(formatMarkup(0), "0.0%");
  assert.equal(formatMarkup(null), "—");
});

test("a null signature is a row with no on-chain counterpart", () => {
  const entry: LedgerEntry = {
    id: "led_0001",
    ticketId: "tkt_syn_0001",
    kind: "sale",
    fromWallet: "SYNuGoRh6b1q2MEeZvESSfycRY5dGWMbV5ya79A1fCH",
    toWallet: "SYNFL8KnV6ew2apUbQ3SFGcwA5JZ4Mqq7hU3DSU1nFt",
    priceLamports: 1_180_000_000,
    markupBps: 1800,
    signature: null,
    slot: null,
    occurredAt: "2026-10-05T18:00:00.000Z",
  };

  assert.equal(entry.signature, null, "the contract has to represent a row with no transaction");
  assert.equal(signatureLabel(entry.signature), "Not on chain");
  assert.equal(signatureLabel(undefined), "Not on chain");
  assert.equal(signatureLabel(""), "Not on chain");
  assert.equal(
    signatureLabel("4EjLt3UAXcHzQ1MU4nt1vQbp8boLBH7k2VTqpJfiwtVA1RbtCsvET6cS1wHeBUxE4GjTmfM7m6kSYf5invrBLGkE"),
    "4EjLt3UAXcHzQ1MU4nt1vQbp8boLBH7k2VTqpJfiwtVA1RbtCsvET6cS1wHeBUxE4GjTmfM7m6kSYf5invrBLGkE",
    "a real signature is shown as itself; the caller decides where to link it",
  );
});

test("shortAddress truncates the middle and leaves what is already short", () => {
  const wallet = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU";
  assert.equal(shortAddress(wallet), "7xKX…gAsU");
  assert.equal(shortAddress(wallet, 6, 6), "7xKXtg…osgAsU");
  assert.equal(shortAddress("abc"), "abc", "nothing to truncate");
  assert.equal(shortAddress(null), "—");
  assert.equal(shortAddress(undefined), "—");
});

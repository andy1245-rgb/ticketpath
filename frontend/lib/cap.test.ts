import assert from "node:assert/strict";
import { test } from "node:test";

import {
  capCeilingLamports,
  isWithinCap,
  markupBpsFromPrice,
  maxResaleLamports,
} from "./cap.ts";

const FACE = 1_000_000_000; // 1 SOL
const CAP_BPS = 2_500; // +25%
const CEILING = 1_250_000_000;

test("the cap predicate admits the ceiling and refuses one lamport more", () => {
  // price * 10000 <= face * (10000 + capBps), on the boundary itself.
  assert.equal(isWithinCap(CEILING, FACE, CAP_BPS), true);
  assert.equal(isWithinCap(CEILING + 1, FACE, CAP_BPS), false);
  assert.equal(isWithinCap(CEILING - 1, FACE, CAP_BPS), true);
  assert.equal(capCeilingLamports(FACE, CAP_BPS), CEILING);
});

test("a cap of zero admits the face and nothing above it", () => {
  assert.equal(isWithinCap(FACE, FACE, 0), true);
  assert.equal(isWithinCap(FACE + 1, FACE, 0), false);
  assert.equal(capCeilingLamports(FACE, 0), FACE, "a zero cap is a ceiling at face value");
  assert.equal(
    isWithinCap(FACE, FACE, 0),
    true,
    "resalePriceCapBps null on the wire is not the same as 0 and never reaches this call",
  );
});

test("the ceiling is floored to whole lamports, never rounded up", () => {
  // 0.9 SOL at +15% is 1.035 SOL exactly.
  assert.equal(capCeilingLamports(900_000_000, 1_500), 1_035_000_000);
  // 1 lamport at +1 bp is 1.0001 of a lamport, which the chain cannot admit.
  assert.equal(capCeilingLamports(1, 1), 1);
});

test("the most a buyer may pay prefers the enforced ceiling over the platform cap", () => {
  assert.equal(maxResaleLamports({ faceValueLamports: FACE, resalePriceCapBps: CAP_BPS }), CEILING);
  assert.equal(maxResaleLamports({ faceValueLamports: FACE, resalePriceCapBps: null }), null);
  assert.equal(
    maxResaleLamports({
      faceValueLamports: FACE,
      resalePriceCapBps: CAP_BPS,
      enforcedCapCeilingLamports: FACE,
    }),
    FACE,
    "a law that caps at face wins over the platform's wider number",
  );
});

test("markup rounds to the nearest basis point", () => {
  assert.equal(markupBpsFromPrice(CEILING, FACE), CAP_BPS);
  assert.equal(markupBpsFromPrice(FACE, FACE), 0);
  assert.equal(markupBpsFromPrice(FACE + 5_000_000, FACE), 50);
  // 0.5 bp rounds up, 0.4999 bp rounds down.
  assert.equal(markupBpsFromPrice(FACE + 50_000, FACE), 1);
  assert.equal(markupBpsFromPrice(FACE + 49_999, FACE), 0);
  assert.equal(markupBpsFromPrice(900_000_000, FACE), -1_000);
  assert.equal(markupBpsFromPrice(FACE, 0), 0, "no face value means no markup to compute");
});

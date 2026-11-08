/**
 * The resale cap, as arithmetic and nothing else.
 *
 * The contract's predicate is `price * 10000 <= face * (10000 + capBps)`, and
 * that is exactly what `isWithinCap` evaluates. It is written with integer
 * arithmetic only: at 1e9 lamports a float would start losing single lamports,
 * and the boundary case is the whole point of the rule.
 *
 * Where the backend reports an `enforcedCap` (the jurisdiction gate and the
 * platform cap, tightened to the lower of the two), that record wins over the
 * ticket's own `resalePriceCapBps`, because the enforced ceiling is what the
 * contract admits against.
 */

export function capCeilingLamports(faceValueLamports: number, capBps: number): number {
  return Math.floor((faceValueLamports * (10_000 + capBps)) / 10_000);
}

/** True when the contract would admit this price for this face and cap. */
export function isWithinCap(priceLamports: number, faceValueLamports: number, capBps: number): boolean {
  return priceLamports * 10_000 <= faceValueLamports * (10_000 + capBps);
}

/** The most a buyer may pay, in lamports. Uncapped means the face is unbounded. */
export function maxResaleLamports(args: {
  faceValueLamports: number;
  resalePriceCapBps: number | null;
  enforcedCapCeilingLamports?: number | null;
}): number | null {
  const { faceValueLamports, resalePriceCapBps, enforcedCapCeilingLamports } = args;
  if (typeof enforcedCapCeilingLamports === "number") return enforcedCapCeilingLamports;
  if (resalePriceCapBps == null) return null;
  return capCeilingLamports(faceValueLamports, resalePriceCapBps);
}

/** Lamports back to bps over a face value, rounded to the nearest bp. */
export function markupBpsFromPrice(priceLamports: number, faceValueLamports: number): number {
  if (faceValueLamports <= 0) return 0;
  return Math.round(((priceLamports - faceValueLamports) * 10_000) / faceValueLamports);
}

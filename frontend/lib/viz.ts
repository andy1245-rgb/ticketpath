/** Small scale/geometry helpers shared by the inline-SVG charts. */

export interface Scale {
  (value: number): number;
  domain: [number, number];
  range: [number, number];
}

export function linearScale(domain: [number, number], range: [number, number]): Scale {
  const [d0, d1] = domain;
  const [r0, r1] = range;
  const span = d1 - d0 || 1;
  const fn = ((value: number) => r0 + ((value - d0) / span) * (r1 - r0)) as Scale;
  fn.domain = domain;
  fn.range = range;
  return fn;
}

/**
 * Round a domain out to clean tick values. Axis ticks carry the values we did
 * not directly label, so they need to land on readable numbers.
 */
export function niceTicks(min: number, max: number, count = 4): number[] {
  if (!Number.isFinite(min) || !Number.isFinite(max) || min === max) {
    return [min || 0];
  }
  const span = max - min;
  const rawStep = span / count;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  // Standard nice-number thresholds. Rounding only *down* to 1/2/5 overshoots
  // the requested tick count badly — a raw step of 3.3 became 2, doubling the
  // gridlines. Round to the nearest of 1/2/5/10 instead.
  const step =
    (normalized < 1.5 ? 1 : normalized < 3 ? 2 : normalized < 7 ? 5 : 10) * magnitude;

  const start = Math.floor(min / step) * step;
  const end = Math.ceil(max / step) * step;
  const ticks: number[] = [];
  // Accumulate with a guard: floating-point step addition can overshoot.
  for (let v = start, i = 0; v <= end + step / 2 && i < 40; v += step, i++) {
    ticks.push(Number(v.toFixed(10)));
  }
  return ticks;
}

/** Straight-segment path. Monotone splines misstate sparse sale data. */
export function linePath(points: Array<{ x: number; y: number }>): string {
  if (!points.length) return "";
  return points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
}

/** Closed path for the area wash beneath a line. */
export function areaPath(points: Array<{ x: number; y: number }>, baseY: number): string {
  if (!points.length) return "";
  const first = points[0];
  const last = points[points.length - 1];
  return `${linePath(points)} L${last.x.toFixed(2)},${baseY.toFixed(2)} L${first.x.toFixed(2)},${baseY.toFixed(2)} Z`;
}

/** Index of the point whose x is nearest to `x`. Drives the crosshair. */
export function nearestIndex(xs: number[], x: number): number {
  let best = 0;
  let bestDist = Infinity;
  for (let i = 0; i < xs.length; i++) {
    const d = Math.abs(xs[i] - x);
    if (d < bestDist) {
      bestDist = d;
      best = i;
    }
  }
  return best;
}

/**
 * Advance width of a mono string, in pixels.
 *
 * Geist Mono sets every glyph at 0.6em, so nine characters at 12px occupy 65px.
 * The y-axis margin is measured from this instead of guessed: all three label
 * right edges have to land on one line, and the widest label decides where the
 * plot starts.
 */
export function monoWidth(text: string, fontSizePx: number): number {
  return text.length * fontSizePx * 0.6;
}

/**
 * Evenly spaced indices including both ends, at most `max` of them.
 *
 * The charts thin their x labels with this rather than dropping every other
 * one, so the first and last point are always named. Rounding can repeat an
 * index on a very short series; the duplicates go.
 */
export function labelIndices(count: number, max: number): number[] {
  if (count <= 0) return [];
  const kept = Math.max(1, Math.min(count, Math.floor(max)));
  if (kept === 1) return [0];
  const out: number[] = [];
  for (let k = 0; k < kept; k++) out.push(Math.round((k * (count - 1)) / (kept - 1)));
  return [...new Set(out)];
}

/**
 * Drop labels that would overprint each other.
 *
 * A 12px line needs about 15px of vertical room. When the face value and the
 * last sale are a few lamports apart they map to the same pixel row, and two
 * numbers on one row are unreadable. Items are grouped by proximity and the
 * lowest `priority` number in each group survives, so the caller states which
 * level matters rather than relying on draw order.
 */
export function keepNonColliding<T extends { y: number; priority: number }>(
  items: T[],
  minGap: number,
): T[] {
  const sorted = [...items].sort((a, b) => a.y - b.y || a.priority - b.priority);
  const kept: T[] = [];
  let cluster: T[] = [];

  const flush = () => {
    if (!cluster.length) return;
    kept.push(cluster.reduce((best, item) => (item.priority < best.priority ? item : best)));
    cluster = [];
  };

  for (const item of sorted) {
    if (cluster.length && item.y - cluster[cluster.length - 1].y >= minGap) flush();
    cluster.push(item);
  }
  flush();

  return kept.sort((a, b) => a.y - b.y);
}

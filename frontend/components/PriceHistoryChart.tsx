"use client";

import type * as React from "react";
import { useMemo } from "react";
import { useMeasure } from "./useMeasure";
import { Chip } from "./ui";
import { formatDate, formatSol } from "@/lib/format";
import {
  areaPath,
  keepNonColliding,
  labelIndices,
  linePath,
  linearScale,
  monoWidth,
} from "@/lib/viz";

/*
 * One price chart, two sizes. Every rule here comes from brief 4.9: the only
 * numbers on the y axis are levels the data actually has (face, last sale,
 * cap), the cap is a warning-coloured dash with its chip above it, and a
 * single sale draws a flat line across the plot rather than a lone dot.
 *
 * The ticket size is measured against the card in the export: 104px of header
 * above the plot, an 84px plot, 16px of x labels under the baseline and 16px
 * to the card's bottom edge, which is 220px exactly. So 84 is the plot band
 * and the x labels get their own 16px band beneath it; the component's svg is
 * the sum of the two and never draws a card or a border of its own.
 */

const PLOT_HEIGHT = { ticket: 84, page: 200 } as const;
/** One 12px line of x labels under the baseline, plus its descenders. */
const X_LABEL_BAND = 16;
/**
 * Room above the data band for the cap chip. The chip's bottom edge sits 6px
 * above the cap rule and the rule is normally the highest level on the chart,
 * so without this the chip would hang outside the svg and over the card.
 */
const CAP_BAND = 40;
/** Without a cap there is no chip, so the top level only needs half a label. */
const TOP_INSET = 8;
/** Keep the lowest level off the baseline so the line is not mistaken for it. */
const BASELINE_INSET = 4;
const Y_LABEL_SIZE = 12;
const Y_LABEL_GAP = 8;
/** A 12px line needs about this much room before two labels overprint. */
const Y_LABEL_MIN_GAP = 15;
const RIGHT_INSET = 4;
const MIN_PLOT_WIDTH = 120;
const CHIP_GAP = 6;
/** Minimum horizontal room between two x labels, at 12px mono. */
const X_LABEL_ROOM = 96;

/** A level the axis names. Lower `priority` wins when two collide. */
interface Level {
  value: number;
  priority: number;
}

/**
 * ISO dates arrive from the series key; anything else (a caller's "now") is
 * already display text and is printed as given.
 */
function axisText(label: string): string {
  return /^\d{4}-\d{2}-\d{2}$/.test(label) ? formatDate(label) : label;
}

export function PriceHistoryChart(props: {
  points: Array<{ label: string; priceLamports: number | null }>;
  faceValueLamports: number;
  capCeilingLamports: number | null;
  lastSaleLamports: number | null;
  variant?: "ticket" | "page";
  className?: string;
}): React.ReactElement {
  const {
    points,
    faceValueLamports,
    capCeilingLamports,
    lastSaleLamports,
    variant = "ticket",
    className = "",
  } = props;

  // The server-first paint uses this width; a ResizeObserver corrects it once
  // the browser has a real box, so the chart is never blank before hydration.
  const [wrapRef, measured] = useMeasure<HTMLDivElement>(variant === "ticket" ? 380 : 720);
  const vbWidth = Math.max(MIN_PLOT_WIDTH, measured);

  const plotHeight = PLOT_HEIGHT[variant];
  const svgHeight = plotHeight + X_LABEL_BAND;

  const levels = useMemo<Level[]>(() => {
    const raw: Level[] = [
      // Face is the reference the whole page reads against, so it is named
      // even when a sale sits on exactly the same lamports.
      { value: faceValueLamports, priority: 2 },
    ];
    if (lastSaleLamports != null) raw.push({ value: lastSaleLamports, priority: 0 });
    if (capCeilingLamports != null) raw.push({ value: capCeilingLamports, priority: 1 });

    // The same level named twice is one label, the higher-priority one.
    const byValue = new Map<number, Level>();
    for (const level of raw) {
      const seen = byValue.get(level.value);
      if (!seen || level.priority < seen.priority) byValue.set(level.value, level);
    }
    return [...byValue.values()];
  }, [faceValueLamports, lastSaleLamports, capCeilingLamports]);

  const layout = useMemo(() => {
    const prices = points
      .map((p) => p.priceLamports)
      .filter((p): p is number => p != null);

    // The domain has to contain every real level and every point, because a
    // rule drawn outside the plot would read as a value the data does not have.
    const values = [
      ...prices,
      faceValueLamports,
      ...(lastSaleLamports != null ? [lastSaleLamports] : []),
      ...(capCeilingLamports != null ? [capCeilingLamports] : []),
    ];
    let low = Math.min(...values);
    let high = Math.max(...values);
    if (high === low) {
      // One flat level still needs a span to sit in the middle of.
      const pad = Math.max(1, Math.abs(low) * 0.05);
      low -= pad;
      high += pad;
    }

    const labelWidth = Math.ceil(
      Math.max(0, ...levels.map((level) => monoWidth(formatSol(level.value), Y_LABEL_SIZE))),
    );
    const left = labelWidth + Y_LABEL_GAP;
    const plotWidth = Math.max(MIN_PLOT_WIDTH, vbWidth - left - RIGHT_INSET);

    // The data band gives up the top of the plot to the cap chip and a few
    // pixels at the bottom so the lowest level never lands on the baseline.
    const dataTop = capCeilingLamports != null ? CAP_BAND : TOP_INSET;
    const dataBottom = plotHeight - BASELINE_INSET;
    const y = linearScale([low, high], [dataBottom, dataTop]);

    const xAt = (index: number): number =>
      points.length <= 1 ? left : left + (index / (points.length - 1)) * plotWidth;

    const priced = points
      .map((p, index) => ({ index, value: p.priceLamports }))
      .filter((p): p is { index: number; value: number } => p.value != null)
      .map((p) => ({ x: xAt(p.index), y: y(p.value) }));

    // Consecutive priced points form one run; a null breaks the line instead
    // of being bridged, because a bridge would invent a sale that never happened.
    const runs: Array<Array<{ x: number; y: number }>> = [];
    let run: Array<{ x: number; y: number }> = [];
    for (let index = 0; index < points.length; index++) {
      const price = points[index].priceLamports;
      if (price == null) {
        if (run.length) runs.push(run);
        run = [];
      } else {
        run.push({ x: xAt(index), y: y(price) });
      }
    }
    if (run.length) runs.push(run);

    const labelled = keepNonColliding(
      levels.map((level) => ({ ...level, y: y(level.value) })),
      Y_LABEL_MIN_GAP,
    );

    return {
      y,
      xAt,
      left,
      plotWidth,
      plotRight: left + plotWidth,
      baseline: plotHeight,
      faceY: y(faceValueLamports),
      capY: capCeilingLamports != null ? y(capCeilingLamports) : null,
      priced,
      runs,
      labelled,
    };
  }, [
    points,
    levels,
    faceValueLamports,
    capCeilingLamports,
    lastSaleLamports,
    vbWidth,
    plotHeight,
  ]);

  const { left, plotWidth, plotRight, baseline, faceY, capY, priced, runs, labelled } = layout;

  // One sale is a flat line at that price, spanning the plot. It is not a ramp
  // from zero and not a dot: a single point has no trend, only a level.
  const flat = priced.length === 1 ? { ...priced[0], x1: left, x2: plotRight } : null;

  const ariaLabel = useMemo(() => {
    const parts = [`face ${formatSol(faceValueLamports)}`];
    if (lastSaleLamports != null) parts.push(`last sale ${formatSol(lastSaleLamports)}`);
    else if (priced.length) parts.push("last sale not recorded");
    else parts.push("no sales recorded");
    parts.push(capCeilingLamports == null ? "uncapped" : `cap ${formatSol(capCeilingLamports)}`);
    return `Price history: ${parts.join(", ")}.`;
  }, [faceValueLamports, lastSaleLamports, capCeilingLamports, priced.length]);

  // Thin the x labels by their measured extent, not just by a target count.
  // Evenly spaced indices can still land two labels closer than a label is
  // wide; the newest one wins those collisions because it names the last price.
  const xLabelCount = Math.max(1, Math.floor(plotWidth / X_LABEL_ROOM));
  const xLabels: Array<{
    index: number;
    x: number;
    anchor: "start" | "middle" | "end";
    text: string;
    left: number;
    right: number;
  }> = [];
  for (const index of labelIndices(points.length, xLabelCount)) {
    const text = axisText(points[index].label);
    const width = monoWidth(text, Y_LABEL_SIZE);
    const x = layout.xAt(index);
    const anchor: "start" | "middle" | "end" =
      index === 0 ? "start" : index === points.length - 1 ? "end" : "middle";
    const left = anchor === "start" ? x : anchor === "end" ? x - width : x - width / 2;
    const candidate = { index, x, anchor, text, left, right: left + width };
    const previous = xLabels[xLabels.length - 1];
    if (previous && candidate.left < previous.right + 8) {
      if (index === points.length - 1) {
        while (xLabels.length && xLabels[xLabels.length - 1].right > candidate.left - 8) {
          xLabels.pop();
        }
        xLabels.push(candidate);
      }
      continue;
    }
    xLabels.push(candidate);
  }

  return (
    <div ref={wrapRef} className={`relative ${className}`}>
      <svg
        width="100%"
        height={svgHeight}
        viewBox={`0 0 ${vbWidth} ${svgHeight}`}
        preserveAspectRatio="none"
        role="img"
        aria-label={ariaLabel}
        className="block"
      >
        {/* The x axis. One hairline, sitting exactly on the plot's bottom edge. */}
        <line
          x1={left}
          x2={plotRight}
          y1={baseline}
          y2={baseline}
          stroke="var(--line)"
          strokeWidth="1"
          shapeRendering="crispEdges"
        />

        {/* Face value is an annotation, so it is a hairline and a stated level,
            never an accent mark: the accent belongs to the series. */}
        <line x1={left} x2={plotRight} y1={faceY} y2={faceY} stroke="var(--line)" strokeWidth="1" />

        {flat ? (
          <path
            d={areaPath(
              [
                { x: flat.x1, y: flat.y },
                { x: flat.x2, y: flat.y },
              ],
              baseline,
            )}
            fill="var(--accent)"
            fillOpacity={0.1}
          />
        ) : (
          runs.map((run, i) =>
            run.length > 1 ? (
              <path
                key={i}
                d={areaPath(run, baseline)}
                fill="var(--accent)"
                fillOpacity={0.1}
              />
            ) : null,
          )
        )}

        {/* The cap, and only the cap, is warning-coloured and dashed. */}
        {capY != null && (
          <line
            x1={left}
            x2={plotRight}
            y1={capY}
            y2={capY}
            stroke="var(--warning)"
            strokeWidth="1"
            strokeDasharray="4 4"
          />
        )}

        {flat ? (
          <line
            x1={flat.x1}
            x2={flat.x2}
            y1={flat.y}
            y2={flat.y}
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            className="text-accent"
          />
        ) : (
          runs.map((run, i) =>
            run.length > 1 ? (
              <path
                key={i}
                d={linePath(run)}
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-accent"
              />
            ) : (
              // An isolated priced point in a longer series is still a sale;
              // it gets a mark at its own value rather than a made-up segment.
              <circle
                key={i}
                cx={run[0].x}
                cy={run[0].y}
                r={2.5}
                fill="var(--accent)"
              />
            ),
          )
        )}

        {/* Y labels: real levels only, right-aligned, right edges on one line
            8px to the left of the plot. */}
        {labelled.map((level, i) => (
          <text
            key={`${i}-${level.value}`}
            x={left - Y_LABEL_GAP}
            y={level.y}
            textAnchor="end"
            dominantBaseline="middle"
            fontSize={Y_LABEL_SIZE}
            className="figure"
            fill="var(--muted)"
          >
            {formatSol(level.value)}
          </text>
        ))}

        {/* X labels sit under the baseline. The first is flush with the plot's
            left edge and the last with its right, so neither overhangs. */}
        {xLabels.map((label) => (
          <text
            key={`${label.index}-${label.text}`}
            x={label.x}
            y={baseline + 12}
            textAnchor={label.anchor}
            fontSize={Y_LABEL_SIZE}
            className="figure"
            fill="var(--muted)"
          >
            {label.text}
          </text>
        ))}
      </svg>

      {/* Chip is the product's one chip shape, so the cap label is a Chip in a
          positioned wrapper rather than a second pill built here. Its right
          edge is on the plot's right edge and its bottom edge 6px above the
          dashed rule, as the export measures it. */}
      {capCeilingLamports != null && capY != null && (
        <span
          className="absolute"
          style={{ right: RIGHT_INSET, bottom: svgHeight - capY + CHIP_GAP }}
        >
          <Chip tone="warning">Cap {formatSol(capCeilingLamports)}</Chip>
        </span>
      )}
    </div>
  );
}

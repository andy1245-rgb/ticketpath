import Link from "next/link";
import type { ReactNode } from "react";
import type { Capability } from "@/lib/capabilities";

/* ---------------------------------------------------------------------------
 * The shared vocabulary. Every screen is built from these, so a chip, a panel
 * and a pill mean the same thing everywhere and no screen invents a shape.
 * ------------------------------------------------------------------------ */

type PillVariant = "primary" | "secondary" | "quiet";
type PillSize = "md" | "sm";

const PILL_VARIANT: Record<PillVariant, string> = {
  primary: "bg-accent text-on-accent border border-accent hover:bg-accent-press hover:border-accent-press",
  secondary: "bg-surface text-ink border border-control hover:border-ink",
  quiet: "bg-transparent text-ink border border-transparent hover:text-accent",
};

const PILL_SIZE: Record<PillSize, string> = {
  md: "h-12 px-6 t-meta",
  sm: "h-10 px-5 t-meta",
};

interface PillProps {
  children: ReactNode;
  href?: string;
  variant?: PillVariant;
  size?: PillSize;
  className?: string;
  ariaLabel?: string;
  title?: string;
}

/**
 * A navigation pill is always an anchor; anything else is a button that
 * declares its own type, so nothing inside a form can submit by accident.
 */
export function Pill({ children, href, variant = "secondary", size = "md", className = "", ariaLabel, title }: PillProps) {
  const cls = `u-transition inline-flex items-center justify-center gap-2 rounded-pill font-medium ${PILL_VARIANT[variant]} ${PILL_SIZE[size]} ${className}`;
  if (href) {
    return (
      <Link href={href} className={cls} aria-label={ariaLabel} title={title}>
        {children}
      </Link>
    );
  }
  return (
    <button type="button" className={cls} aria-label={ariaLabel} title={title}>
      {children}
    </button>
  );
}

type ChipTone = "neutral" | "warning" | "positive" | "danger" | "accent";

const CHIP_TONE: Record<ChipTone, string> = {
  neutral: "border-line text-muted",
  warning: "border-warning text-warning",
  positive: "border-positive text-positive",
  danger: "border-danger text-danger",
  accent: "border-accent text-accent",
};

export function Chip({ children, tone = "neutral", className = "" }: { children: ReactNode; tone?: ChipTone; className?: string }) {
  return (
    <span
      className={`inline-flex items-center rounded-pill border bg-inset px-3 py-1 t-micro-caps ${CHIP_TONE[tone]} ${className}`}
    >
      {children}
    </span>
  );
}

/** A raised surface: the header, the ticket card, the three feature cards. */
export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-card border p-6 border-control bg-surface shadow-card ${className}`}>{children}</div>
  );
}

/** A flat grouping inside the page, one step up from the paper. */
export function Panel({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`rounded-panel border border-line bg-surface p-6 ${className}`}>{children}</div>;
}

/** A hairline rule. The product uses four on the landing screen and no more. */
export function Rule({ className = "" }: { className?: string }) {
  return <div aria-hidden="true" className={`h-px w-full bg-line ${className}`} />;
}

/**
 * The perforation is a drawn dash, never the browser's own dashed border: 4px on,
 * 4px off, measured
 * against the card's own 380px so the dash geometry is exact at desktop.
 */
export function Perforation({ width = 380, className = "" }: { width?: number; className?: string }) {
  return (
    <svg
      width="100%"
      height="1"
      viewBox={`0 0 ${width} 1`}
      preserveAspectRatio="none"
      aria-hidden="true"
      focusable="false"
      className={`block ${className}`}
    >
      <line x1="0" y1="0.5" x2={width} y2="0.5" stroke="var(--line)" strokeWidth="1" strokeDasharray="4 4" />
    </svg>
  );
}

/** What a screen shows while its data is in flight. */
export function Skeleton({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`} role="status" aria-label="Loading">
      {Array.from({ length: lines }).map((_, i) => (
        <div
          key={i}
          className="h-3 rounded-pill bg-inset"
          style={{ width: `${[92, 78, 64, 84, 70][i % 5]}%` }}
        />
      ))}
      <span className="sr-only">Loading</span>
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-panel border border-line bg-surface p-6">
      <p className="t-meta text-ink">{title}</p>
      <p className="t-body mt-2 text-muted">{body}</p>
    </div>
  );
}

/**
 * One panel for every capability this build does not have. It names what is
 * missing, the endpoint that would fill it, and what the screen shows instead.
 * The caller decides the heading level so no page skips a step.
 */
export function Unavailable({
  title,
  capability,
  level = 2,
}: {
  title: string;
  capability: Capability;
  level?: 2 | 3;
}) {
  const Tag = level === 2 ? "h2" : "h3";
  return (
    <section className="rounded-panel border border-line bg-surface p-6">
      <p className="t-micro-caps text-muted">Unavailable</p>
      <Tag className="h-section mt-2">
        <span aria-hidden="true" className="text-muted">
          {"\u2014 "}
        </span>
        {title}
      </Tag>
      <dl className="mt-6 space-y-4">
        <div>
          <dt className="t-micro-caps text-muted">What is missing</dt>
          <dd className="t-body mt-1 text-ink">{capability.missing}</dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">Endpoint that would fill it</dt>
          <dd className="figure t-meta mt-1 text-ink">{capability.endpoint}</dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">What this screen shows instead</dt>
          <dd className="t-body mt-1 text-muted">{capability.shows}</dd>
        </div>
      </dl>
    </section>
  );
}

/**
 * The backend's own sentence, printed once per page and never paraphrased
 * (brief 5.8). Only rendered when the payload says the data is synthetic.
 */
export function DataSourceNote({
  dataSource,
}: {
  dataSource?: { synthetic: boolean; label: string } | null;
}) {
  if (!dataSource?.synthetic) return null;
  return (
    <p className="t-micro text-muted">
      <span className="figure">dataSource</span> {dataSource.label}
    </p>
  );
}

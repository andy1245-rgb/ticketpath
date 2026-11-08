/**
 * One figure with its label and, optionally, the note that says what the figure
 * counts. Flat: a single hairline above it, no surface, no shadow. The ticket
 * card and the header are the only raised things in the product.
 */
export function StatTile({
  label,
  value,
  note,
  mono = true,
  className = "",
  hint,
  delta,
}: {
  label: string;
  value: string;
  note?: string;
  /** Figures are mono by default; set false when the value is prose. */
  mono?: boolean;
  className?: string;
  /** @deprecated The previous note prop. Kept for the pages still passing it. */
  hint?: string;
  /** @deprecated The previous delta prop; its text falls back to the note. */
  delta?: { text: string; direction: "up" | "down" | "flat"; upIsGood?: boolean };
  /** @deprecated The previous sparkline series. Nothing draws it now. */
  trend?: number[];
}): React.ReactElement {
  const noteText = note ?? delta?.text ?? hint ?? null;

  return (
    <div className={`border-t border-line pt-4 ${className}`}>
      <p className="t-micro-caps text-muted">{label}</p>
      <p
        className={`${mono ? "figure text-[32px] leading-[38px]" : "h-section"} mt-2 font-semibold text-ink`}
      >
        {value}
      </p>
      {noteText && <p className="t-micro mt-1 text-muted">{noteText}</p>}
    </div>
  );
}

/**
 * The four-up row the stat tiles sit in. Exported beside the tile because a
 * grid of them is the only way the surface uses one.
 */
export function StatRow({ children }: { children: React.ReactNode }): React.ReactElement {
  return <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">{children}</div>;
}

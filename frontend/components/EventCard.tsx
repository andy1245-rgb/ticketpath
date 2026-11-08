import Link from "next/link";
import type { Event, EventStatus } from "@/lib/types";
import { formatBpsPercent, formatCompact, formatDate } from "@/lib/format";
import { Chip, Rule } from "./ui";

/**
 * The backend serves an enforced cap beside the event's own policy: the
 * jurisdiction gate and the platform cap, tightened to the lower of the two.
 * lib/types.ts does not carry it yet, so it is declared here and read
 * structurally. Nothing is defaulted: no field means no row is shown, never a
 * number this file made up.
 */
interface EnforcedCap {
  enforcedCapBps: number;
  enforcedCeilingLamports: number;
  bindingRule: "law" | "platform";
}

type EventWithEnforcedCap = Event & { enforcedCap?: EnforcedCap | null };

/**
 * Status is a tone from the shared palette, and never the warning colour: that
 * one belongs to the cap alone, here and on every other surface.
 */
const STATUS: Record<EventStatus, { label: string; tone: "neutral" | "positive" | "accent" | "danger" }> = {
  draft: { label: "Draft", tone: "neutral" },
  on_sale: { label: "On sale", tone: "positive" },
  sold_out: { label: "Sold out", tone: "accent" },
  completed: { label: "Completed", tone: "neutral" },
  cancelled: { label: "Cancelled", tone: "danger" },
};

/**
 * The cap as a sentence, not a badge: an enforced ceiling names which rule
 * binds it, an event with no cap says so, and the event's own policy is the
 * last resort.
 */
function capLabel(event: Event, enforced: EnforcedCap | null): string {
  if (enforced) {
    const percent = formatBpsPercent(enforced.enforcedCapBps);
    return enforced.bindingRule === "law" ? `Cap by law ${percent}` : `Cap ${percent}`;
  }
  if (event.resalePriceCapBps == null) return "Uncapped";
  return `Cap ${formatBpsPercent(event.resalePriceCapBps)}`;
}

/**
 * One row of a browse list. The whole card is the link, so there is no second
 * control competing with it for the click, and nothing inside it is focusable.
 * imageUrl is null for every event in this build, so there is no image and no
 * empty box standing in for one.
 */
export function EventCard({ event, className = "" }: { event: Event; className?: string }): React.ReactElement {
  const status = STATUS[event.status];
  const enforced = (event as EventWithEnforcedCap).enforcedCap ?? null;

  return (
    <Link
      href={`/events/${event.slug}`}
      className={`u-transition block rounded-card border border-control bg-surface p-6 hover:border-accent ${className}`}
    >
      <div className="flex items-start justify-between gap-4">
        <p className="h-event line-clamp-2 text-ink">{event.name}</p>
        <Chip tone={status.tone} className="shrink-0">
          {status.label}
        </Chip>
      </div>

      <p className="t-meta mt-1 text-muted">
        {event.venue} · {event.city}
      </p>

      <Rule className="my-4" />

      <dl className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
        <div>
          <dt className="t-micro-caps text-muted">Date</dt>
          <dd className="figure t-meta mt-1 text-ink">{formatDate(event.startsAt)}</dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">Issued</dt>
          <dd className="figure t-meta mt-1 text-ink">
            {formatCompact(event.issuedCount)} of {formatCompact(event.totalSupply)}
          </dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">Resale cap</dt>
          <dd className="t-meta mt-1 text-ink">{capLabel(event, enforced)}</dd>
        </div>
      </dl>
    </Link>
  );
}

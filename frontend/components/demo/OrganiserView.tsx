"use client";

import { Card, Chip, Rule } from "@/components/ui";
import {
  bpsLabel,
  LAW_PROVENANCE,
  lawReasonSentence,
  regionRow,
  sol,
  SOL,
  type Ceiling,
  type EventConfig,
  type ResaleMode,
} from "@/lib/demoState";
import { REGIONS } from "@/lib/demoRegions";

const MODES: { value: ResaleMode; label: string; note: string }[] = [
  { value: "open", label: "Open", note: "Listing at or under the cap is admitted." },
  {
    value: "monitored",
    label: "Monitored",
    note: "Same ceiling; every listing is flagged for the organizer to review.",
  },
  { value: "banned", label: "BANNED", note: "No listing is accepted, at any price." },
];

type Props = {
  event: EventConfig;
  ceiling: Ceiling;
  onChange: (patch: Partial<EventConfig>) => void;
};

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1">
      <span className="t-meta text-muted">{label}</span>
      {children}
    </label>
  );
}

const INPUT =
  "h-11 rounded-card border border-line bg-inset px-3 t-body text-ink";

export function OrganiserView({ event, ceiling, onChange }: Props) {
  const row = regionRow(event.region);

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
      <section aria-labelledby="organiser-title" className="grid gap-6">
        <div>
          <h2 id="organiser-title" className="h-section text-ink">
            Organiser
          </h2>
          <p className="t-deck mt-2 max-w-[62ch] text-muted">
            These are the fields the event record carries. Change one and the buyer side changes
            with it: the ceiling, the refusal, and what the listing form will accept.
          </p>
        </div>

        <Card>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Event name">
              <input
                className={INPUT}
                value={event.name}
                onChange={(e) => onChange({ name: e.target.value })}
              />
            </Field>
            <Field label="Face price, SOL">
              <input
                className={INPUT}
                inputMode="decimal"
                value={event.faceLamports / SOL}
                onChange={(e) => {
                  const sol0 = Number(e.target.value);
                  if (Number.isFinite(sol0)) onChange({ faceLamports: Math.round(sol0 * SOL) });
                }}
              />
            </Field>
            <Field label="Platform cap, bps over face">
              <input
                className={INPUT}
                inputMode="numeric"
                value={event.capBps}
                onChange={(e) => {
                  const bps = Number(e.target.value);
                  if (Number.isFinite(bps)) onChange({ capBps: Math.max(0, Math.min(10_000, Math.round(bps))) });
                }}
              />
            </Field>
            <Field label="Manual override, bps (blank = cap above)">
              <input
                className={INPUT}
                inputMode="numeric"
                value={event.overrideCapBps ?? ""}
                onChange={(e) => {
                  const raw = e.target.value.trim();
                  if (raw === "") return onChange({ overrideCapBps: null });
                  const bps = Number(raw);
                  if (Number.isFinite(bps)) {
                    onChange({ overrideCapBps: Math.max(0, Math.min(10_000, Math.round(bps))) });
                  }
                }}
              />
            </Field>
            <Field label="Region (geo-lock)">
              <select
                className={INPUT}
                value={event.region}
                onChange={(e) => onChange({ region: e.target.value })}
              >
                {REGIONS.map((r) => (
                  <option key={r.jurisdiction} value={r.jurisdiction}>
                    {r.jurisdiction} · {r.resalePolicy}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Artist fee, bps of the resale price">
              <input
                className={INPUT}
                inputMode="numeric"
                value={event.artistFee.bps}
                onChange={(e) => {
                  const bps = Number(e.target.value);
                  if (Number.isFinite(bps)) {
                    onChange({
                      artistFee: { ...event.artistFee, bps: Math.max(0, Math.min(10_000, Math.round(bps))) },
                    });
                  }
                }}
              />
            </Field>
          </div>

          <Rule className="my-4" />

          <p className="t-meta text-muted">Resale mode</p>
          <div className="mt-2 flex flex-wrap gap-2">
            {MODES.map((mode) => {
              const active = event.resaleMode === mode.value;
              return (
                <button
                  key={mode.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onChange({ resaleMode: mode.value })}
                  className={`u-transition inline-flex h-11 items-center rounded-pill border px-5 t-meta ${
                    active
                      ? "border-ink bg-ink text-on-accent"
                      : "border-line bg-surface text-ink hover:border-ink"
                  }`}
                >
                  {mode.label}
                </button>
              );
            })}
          </div>
          <p className="t-meta mt-2 text-muted">
            {MODES.find((m) => m.value === event.resaleMode)?.note}
          </p>

          <Rule className="my-4" />

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={event.artistFee.on}
                onChange={(e) => onChange({ artistFee: { ...event.artistFee, on: e.target.checked } })}
                className="mt-1 h-4 w-4"
              />
              <span>
                <span className="t-body block text-ink">Artist fee on every resale</span>
                <span className="t-meta block text-muted">
                  {bpsLabel(event.artistFee.bps)} of the sale price to the artist wallet. The rate is
                  an event setting; the module ships no default.
                </span>
              </span>
            </label>
            <label className="flex items-start gap-3">
              <input
                type="checkbox"
                checked={event.flipTax}
                onChange={(e) => onChange({ flipTax: e.target.checked })}
                className="mt-1 h-4 w-4"
              />
              <span>
                <span className="t-body block text-ink">Flip tax, 15% falling to 0 over 30 days</span>
                <span className="t-meta block text-muted">
                  Full rate under an hour, linear down to zero at 30 days, floored. Paid by the
                  seller on the sale price.
                </span>
              </span>
            </label>
          </div>
        </Card>
      </section>

      <aside className="grid gap-6 self-start" aria-labelledby="rule-result">
        <h2 id="rule-result" className="h-section text-ink">
          Rule result
        </h2>
        <Card>
          <div className="flex flex-wrap items-center gap-2">
            <Chip>{row.resalePolicy}</Chip>
            <Chip>{ceiling.binding} binds</Chip>
          </div>
          <p className="t-body mt-3 text-ink">{lawReasonSentence(row)}</p>
          <Rule className="my-3" />
          <dl className="grid gap-2">
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Jurisdiction</dt>
              <dd className="t-body text-ink">{row.jurisdiction}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Reason code</dt>
              <dd className="t-meta text-ink">{row.lawReason}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Law cap</dt>
              <dd className="t-body text-ink">{bpsLabel(row.resaleCapBps)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Platform cap</dt>
              <dd className="t-body u-num text-ink">{bpsLabel(ceiling.platformBps)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Ceiling enforced</dt>
              <dd className="t-body u-num text-ink">{sol(ceiling.ceilingLamports)}</dd>
            </div>
            <div className="flex justify-between gap-4">
              <dt className="t-meta text-muted">Cap admitted</dt>
              <dd className="t-body u-num text-ink">{bpsLabel(ceiling.capBps)} over face</dd>
            </div>
          </dl>
          <Rule className="my-3" />
          <p className="t-meta text-muted">
            {row.instrumentKind} · confidence {row.confidence}
          </p>
          <p className="t-meta mt-1 text-muted">{row.citation}</p>
          <p className="t-meta mt-2 text-muted">
            Table {LAW_PROVENANCE.version} ({LAW_PROVENANCE.asOf}), sha256{" "}
            {LAW_PROVENANCE.sha256.slice(0, 12)}… Read by the repository&apos;s resolver for this
            event&apos;s face and platform cap.
          </p>
        </Card>

        <Card>
          <p className="t-meta text-muted">What the buyer side allows now</p>
          <p className="t-body mt-2 text-ink">
            {ceiling.closed
              ? ceiling.closed.reason
              : `A listing is admitted up to ${sol(ceiling.ceilingLamports)}. One lamport above that is refused with 6010 E_CAP_EXCEEDED.`}
          </p>
        </Card>
      </aside>
    </div>
  );
}

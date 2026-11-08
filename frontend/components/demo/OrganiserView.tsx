"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Card, Chip, Rule } from "@/components/ui";
import { StatTile } from "@/components/StatTile";
import {
  bpsLabel,
  buyerSummary,
  LAW_PROVENANCE,
  lawReasonSentence,
  regionRow,
  sol,
  SOL,
  type Ceiling,
  type EventConfig,
  type ResaleMode,
  type TicketOverride,
} from "@/lib/demoState";
import { REGIONS } from "@/lib/demoRegions";
import { RESALE_MODE_LABEL } from "@/lib/resaleMode";

const MODES: { value: ResaleMode; note: string }[] = [
  { value: "open", note: "A listing at or under the ceiling is admitted." },
  {
    value: "monitored",
    note: "Same ceiling. The listing is marked monitored in the record; nothing in this build keeps a review queue, so nothing is flagged for you to review.",
  },
  { value: "banned", note: "No listing is accepted, at any price." },
];

type Props = {
  event: EventConfig;
  ceiling: Ceiling;
  onChange: (patch: Partial<EventConfig>) => void;
};

function Field({ label, htmlFor, children }: { label: string; htmlFor: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="t-meta text-muted" htmlFor={htmlFor}>
        {label}
      </label>
      {children}
    </div>
  );
}

const INPUT = "h-11 rounded-card border border-line bg-inset px-3 t-body text-ink";

/**
 * A basis-point field that holds what was typed and commits only a value it can
 * justify. `Number("") === 0`, so a cleared field used to write a 0 bps cap; here
 * an empty field never commits, and a number outside 0–10 000 is clamped and the
 * clamp is printed rather than applied in silence.
 */
function BpsField({
  id,
  label,
  value,
  onCommit,
  onClear,
  hint,
  max = 10_000,
}: {
  id: string;
  label: string;
  value: number | null;
  onCommit: (bps: number) => void;
  onClear?: () => void;
  hint?: string;
  max?: number;
}) {
  const [draft, setDraft] = useState(value == null ? "" : String(value));
  const [note, setNote] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement | null>(null);
  const noteId = `${id}-note`;

  useEffect(() => {
    if (document.activeElement !== ref.current) setDraft(value == null ? "" : String(value));
  }, [value]);

  function commit() {
    const raw = draft.trim();
    if (raw === "") {
      if (onClear) {
        onClear();
        setNote(null);
      } else {
        setDraft(value == null ? "" : String(value));
        setNote("A cap needs a number. The value is unchanged.");
      }
      return;
    }
    const parsed = Number(raw);
    if (!Number.isFinite(parsed)) {
      setDraft(value == null ? "" : String(value));
      setNote("Not a number. The value is unchanged.");
      return;
    }
    const clamped = Math.max(0, Math.min(max, Math.round(parsed)));
    setDraft(String(clamped));
    setNote(clamped !== Math.round(parsed) ? `Held to the allowed 0–${max} range.` : null);
    onCommit(clamped);
  }

  return (
    <Field label={label} htmlFor={id}>
      <input
        id={id}
        ref={ref}
        className={INPUT}
        inputMode="numeric"
        value={draft}
        aria-describedby={note ? noteId : undefined}
        onChange={(e) => {
          setDraft(e.target.value);
          setNote(null);
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            commit();
          }
          if (e.key === "Escape") setDraft(value == null ? "" : String(value));
        }}
      />
      {note ? (
        <p id={noteId} className="t-micro text-danger">
          {note}
        </p>
      ) : (
        hint && <p className="t-micro text-muted">{hint}</p>
      )}
    </Field>
  );
}

/** The face price holds its raw text, so `0.` survives a keystroke. */
function SolField({ id, label, value, onCommit }: { id: string; label: string; value: number; onCommit: (lamports: number) => void }) {
  const [draft, setDraft] = useState(String(value / SOL));
  const [note, setNote] = useState<string | null>(null);
  const ref = useRef<HTMLInputElement | null>(null);
  const noteId = `${id}-note`;

  useEffect(() => {
    if (document.activeElement !== ref.current) setDraft(String(value / SOL));
  }, [value]);

  function commit() {
    const parsed = Number(draft.trim());
    if (draft.trim() === "" || !Number.isFinite(parsed) || parsed < 0) {
      setDraft(String(value / SOL));
      setNote("Enter an amount in SOL, 0 or more. The value is unchanged.");
      return;
    }
    const lamports = Math.round(parsed * SOL);
    setDraft(String(lamports / SOL));
    setNote(null);
    onCommit(lamports);
  }

  return (
    <Field label={label} htmlFor={id}>
      <input
        id={id}
        ref={ref}
        className={INPUT}
        inputMode="decimal"
        value={draft}
        aria-describedby={note ? noteId : undefined}
        onChange={(e) => {
          setDraft(e.target.value);
          setNote(null);
        }}
        onBlur={commit}
        onKeyDown={(e) => {
          if (e.key === "Enter") {
            e.preventDefault();
            commit();
          }
        }}
      />
      {note ? (
        <p id={noteId} className="t-micro text-danger">
          {note}
        </p>
      ) : (
        <p className="t-micro text-muted">1 SOL = 1 000 000 000 lamports</p>
      )}
    </Field>
  );
}

function TicketOverrides({ event, onChange }: { event: EventConfig; onChange: Props["onChange"] }) {
  const id = useId();
  const [serial, setSerial] = useState("");
  const [max, setMax] = useState("");
  const [note, setNote] = useState<string | null>(null);
  const overrides = event.ticketOverrides ?? {};

  function put(key: string, value: TicketOverride | null) {
    const next = { ...overrides };
    if (value) next[key] = value;
    else delete next[key];
    onChange({ ticketOverrides: next });
  }

  function add(frozen: boolean) {
    const key = serial.trim().toUpperCase();
    if (!key) {
      setNote("Enter a ticket serial, for example DMO-0001 (shown on the buyer side).");
      return;
    }
    const parsed = max.trim() === "" ? null : Number(max);
    if (parsed != null && (!Number.isFinite(parsed) || parsed <= 0)) {
      setNote("The maximum is an amount in SOL above 0, or blank for none.");
      return;
    }
    setNote(null);
    put(key, { frozen, maxLamports: parsed == null ? null : Math.round(parsed * SOL) });
  }

  return (
    <Card>
      <h3 className="h-section text-ink">Manual overrides, per ticket</h3>
      <p className="t-meta mt-2 text-muted">
        Freeze one ticket&apos;s resale or set a maximum for it. Applied by this demo on top of the
        event ceiling and never above it; app policy, not a chain rule.
      </p>
      <div className="mt-4 flex flex-wrap items-end gap-3">
        <Field label="Ticket serial" htmlFor={`${id}-serial`}>
          <input id={`${id}-serial`} className={`${INPUT} w-36`} value={serial} onChange={(e) => setSerial(e.target.value)} placeholder="DMO-0001" />
        </Field>
        <Field label="Max price, SOL (optional)" htmlFor={`${id}-max`}>
          <input id={`${id}-max`} className={`${INPUT} w-40`} inputMode="decimal" value={max} onChange={(e) => setMax(e.target.value)} />
        </Field>
        <button type="button" onClick={() => add(true)} className="u-transition inline-flex h-11 items-center rounded-pill border border-ink bg-ink px-5 t-meta text-on-accent">
          Freeze resale
        </button>
        <button type="button" onClick={() => add(false)} className="u-transition inline-flex h-11 items-center rounded-pill border border-line bg-surface px-5 t-meta text-ink hover:border-ink">
          Set max only
        </button>
      </div>
      {note && <p className="t-micro mt-2 text-danger">{note}</p>}
      {Object.keys(overrides).length === 0 ? (
        <p className="t-meta mt-4 text-muted">No overrides set.</p>
      ) : (
        <ul className="mt-4 grid gap-2">
          {Object.entries(overrides).map(([key, o]) => (
            <li key={key} className="flex flex-wrap items-center justify-between gap-3 border-t border-line pt-2">
              <span className="t-body text-ink">
                {key}: {o.frozen ? "resale frozen" : "not frozen"}
                {o.maxLamports != null ? `, max ${sol(o.maxLamports)}` : ""}
              </span>
              <button type="button" onClick={() => put(key, null)} className="t-meta min-h-11 text-muted underline-offset-4 hover:text-ink hover:underline">
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </Card>
  );
}

export function OrganiserView({ event, ceiling, onChange }: Props) {
  const row = regionRow(event.region);
  const ids = useId();
  const modeLabelId = `${ids}-resale-mode`;

  const lawCapText = row.resaleCapBps == null ? "none in law (see reason code)" : bpsLabel(row.resaleCapBps);
  const overrideOverLaw = event.overrideCapBps != null && ceiling.lawBps != null && event.overrideCapBps > ceiling.lawBps;
  const feePerSol = event.artistFee.on ? Math.floor((SOL * event.artistFee.bps) / 10_000) : 0;
  const taxFullRate = event.flipTax ? Math.floor((SOL * 1_500) / 10_000) : 0;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_420px]">
      <section aria-labelledby="organiser-title" className="grid gap-6">
        <div>
          <h2 id="organiser-title" className="h-section text-ink">
            Organiser
          </h2>
          <p className="t-deck mt-2 max-w-[62ch] text-muted">
            These are the fields the event record carries. Changing one changes the ceiling, the
            refusal and what the listing form will accept. What it cannot change is the chain: the
            cap is fixed when the record is initialised, so the two cap fields here are a what-if.
          </p>
        </div>

        <Card>
          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Event name" htmlFor={`${ids}-name`}>
              <input
                id={`${ids}-name`}
                className={INPUT}
                value={event.name}
                onChange={(e) => onChange({ name: e.target.value })}
              />
            </Field>
            <Field label="Venue" htmlFor={`${ids}-venue`}>
              <input
                id={`${ids}-venue`}
                className={INPUT}
                value={event.venue}
                onChange={(e) => onChange({ venue: e.target.value })}
              />
            </Field>
            <Field label="Starts at" htmlFor={`${ids}-starts`}>
              <input
                id={`${ids}-starts`}
                type="datetime-local"
                className={INPUT}
                value={event.startsAt.slice(0, 16)}
                onChange={(e) => {
                  const at = new Date(e.target.value);
                  if (!Number.isNaN(at.getTime())) onChange({ startsAt: at.toISOString() });
                }}
              />
            </Field>
            <SolField
              id={`${ids}-face`}
              label="Face price, SOL"
              value={event.faceLamports}
              onCommit={(faceLamports) => onChange({ faceLamports })}
            />

            <BpsField
              id={`${ids}-cap`}
              label="Platform cap, bps over face (what-if)"
              value={event.capBps}
              onCommit={(capBps) => onChange({ capBps })}
              hint={`${bpsLabel(event.capBps)} over face · on chain this is fixed at creation`}
            />
            <BpsField
              id={`${ids}-override`}
              label="Organiser cap override, bps (what-if)"
              value={event.overrideCapBps}
              onCommit={(overrideCapBps) => onChange({ overrideCapBps })}
              onClear={() => onChange({ overrideCapBps: null })}
              hint="blank = use the platform cap · 0-10000 · a setting at creation, not a control after it"
            />
            {overrideOverLaw && (
              <p className="t-meta text-danger sm:col-span-2">
                Above the ceiling the law sets for {event.region}: {bpsLabel(ceiling.lawBps)} is what binds here,
                so this override does not raise the price anyone can list at.
              </p>
            )}

            <Field label="Jurisdiction (whose resale law applies)" htmlFor={`${ids}-region`}>
              <select
                id={`${ids}-region`}
                className={INPUT}
                value={event.region}
                onChange={(e) => onChange({ region: e.target.value })}
              >
                {REGIONS.map((r) => (
                  <option key={r.jurisdiction} value={r.jurisdiction}>
                    {r.jurisdiction} · {r.resalePolicy}
                    {r.resalePolicy === "capped" && r.resaleCapBps != null ? ` · law ${bpsLabel(r.resaleCapBps)}` : ""}
                  </option>
                ))}
              </select>
              <p className="t-micro text-muted">
                This picks the law whose cap applies to the price. It does not gate who may buy, and no
                wallet or location is read anywhere in this demo.
              </p>
            </Field>
            <BpsField
              id={`${ids}-fee`}
              label="Artist fee, bps of the resale price"
              value={event.artistFee.bps}
              onCommit={(bps) => onChange({ artistFee: { ...event.artistFee, bps } })}
              hint={`${bpsLabel(event.artistFee.bps)} of the sale price · ${sol(feePerSol)} per 1.0000 SOL resale`}
            />
          </div>

          <Rule className="my-4" />

          <p className="t-meta text-muted" id={modeLabelId}>
            Resale mode
          </p>
          <div role="group" aria-labelledby={modeLabelId} className="mt-2 flex flex-wrap gap-2">
            {MODES.map((mode) => {
              const active = event.resaleMode === mode.value;
              return (
                <button
                  key={mode.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => onChange({ resaleMode: mode.value })}
                  className={`u-transition inline-flex h-11 items-center rounded-pill border px-5 t-meta ${
                    active ? "border-ink bg-ink text-on-accent" : "border-line bg-surface text-ink hover:border-ink"
                  }`}
                >
                  {RESALE_MODE_LABEL[mode.value]}
                </button>
              );
            })}
          </div>
          <p className="t-meta mt-2 text-muted">{MODES.find((m) => m.value === event.resaleMode)?.note}</p>

          <Rule className="my-4" />

          <div className="grid gap-3 sm:grid-cols-2">
            <label className="flex min-h-11 items-start gap-3 py-1">
              <input
                type="checkbox"
                checked={event.artistFee.on}
                onChange={(e) => onChange({ artistFee: { ...event.artistFee, on: e.target.checked } })}
                className="mt-0.5 h-5 w-5"
              />
              <span>
                <span className="t-body block text-ink">Artist fee on every resale</span>
                <span className="t-meta block text-muted">
                  {bpsLabel(event.artistFee.bps)} of the sale price, deducted from what the seller
                  receives. Ships off at 5.00%: change the rate or leave it off.
                </span>
                <span className="t-micro mt-1 block text-muted">
                  Artist wallet: set when the event is created and not editable here. This record
                  carries no wallet field, so there is none to show.
                </span>
              </span>
            </label>
            <label className="flex min-h-11 items-start gap-3 py-1">
              <input
                type="checkbox"
                checked={event.flipTax}
                onChange={(e) => onChange({ flipTax: e.target.checked })}
                className="mt-0.5 h-5 w-5"
              />
              <span>
                <span className="t-body block text-ink">Flip tax, 15% falling to 0 over 30 days</span>
                <span className="t-meta block text-muted">
                  Full rate under an hour, linear down to zero at 30 days, floored. Paid by the
                  seller on the sale price, in the same transaction as the fee.
                </span>
                <span className="t-micro mt-1 block text-muted">
                  The rate and the window are the module&apos;s (1500 bps, 3600 s to 2 592 000 s of
                  hold); this switch is the only event setting.
                </span>
              </span>
            </label>
          </div>

          <p className="t-micro mt-4 text-muted">
            Every edit here is stored in this browser only and nothing is written to a chain, so
            changing these fields proves nothing about an on-chain record.
          </p>
        </Card>

        <TicketOverrides event={event} onChange={onChange} />
      </section>

      <aside className="grid gap-6 self-start" aria-labelledby="rule-result">
        <h2 id="rule-result" className="h-section text-ink">
          Rule result
        </h2>

        <div aria-live="polite" className="grid gap-6">
          <Card>
            <div className="flex flex-wrap items-center gap-2">
              <Chip>{row.resalePolicy}</Chip>
              <Chip tone={ceiling.closed ? "danger" : "neutral"}>
                {ceiling.closed ? ceiling.closed.code : `${ceiling.binding} binds`}
              </Chip>
            </div>
            <p className="t-body mt-3 text-ink">
              {ceiling.closed ? ceiling.closed.reason : lawReasonSentence(row)}
            </p>
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
                <dt className="t-meta text-muted">Price cap in law</dt>
                <dd className="t-meta text-ink">{lawCapText}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="t-meta text-muted">Platform cap (this event)</dt>
                <dd className="t-body u-num text-ink">{bpsLabel(event.capBps)}</dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="t-meta text-muted">Organiser override</dt>
                <dd className="t-body u-num text-ink">
                  {event.overrideCapBps == null ? "none" : bpsLabel(event.overrideCapBps)}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="t-meta text-muted">Ceiling enforced</dt>
                <dd className="t-body u-num text-ink">
                  {ceiling.closed ? "\u2014" : sol(ceiling.ceilingLamports)}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="t-meta text-muted">Cap admitted</dt>
                <dd className="t-body u-num text-ink">
                  {ceiling.closed ? "\u2014" : `${bpsLabel(ceiling.capBps)} over face`}
                </dd>
              </div>
            </dl>
            <Rule className="my-3" />
            <p className="t-meta text-muted">
              {row.instrumentKind} · confidence {row.confidence} · {RESALE_MODE_LABEL[event.resaleMode]} resale
            </p>
            <p className="t-meta mt-1 text-muted">{row.citation}</p>
            <p className="t-meta mt-2 text-muted">
              Table {LAW_PROVENANCE.version} ({LAW_PROVENANCE.asOf}), sha256{" "}
              {LAW_PROVENANCE.sha256.slice(0, 12)}… Read by the repository&apos;s resolver for this
              event&apos;s face and platform cap.
            </p>
          </Card>

          <Card>
            <p className="t-meta text-muted">What the buyer will be allowed to do now</p>
            <ul className="t-body mt-2 grid list-disc gap-2 pl-5 text-ink">
              {buyerSummary(event, ceiling).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
            <p className="t-micro mt-3 text-muted">
              Simulated in this browser. The deployed devnet program enforces the cap only. The
              fee and flip tax ride the sale in this app, and the ban, freeze and region rule are
              app policy plus the region table.
            </p>
          </Card>
          <Card>
            <div className="grid gap-4 sm:grid-cols-2">
              <StatTile
                label="Artist fee per 1 SOL resale"
                value={event.artistFee.on ? sol(feePerSol) : "off"}
                note={event.artistFee.on ? `${bpsLabel(event.artistFee.bps)} of the sale price` : "No fee is taken"}
              />
              <StatTile
                label="Flip tax at full rate"
                value={event.flipTax ? sol(taxFullRate) : "off"}
                note={event.flipTax ? "Per 1.0000 SOL resale inside the first hour" : "No tax is taken"}
              />
            </div>
            <p className="t-micro mt-3 text-muted">
              Both are deducted from the seller&apos;s proceeds on a 1.0000 SOL resale, not added to
              what the buyer pays.
            </p>
          </Card>
        </div>
      </aside>
    </div>
  );
}

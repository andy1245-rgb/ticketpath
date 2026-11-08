import { Panel } from "@/components/ui";

/**
 * The shape of an event record, drawn as fields and not submitted.
 *
 * One component, used by both the create screen and the edit screen, so the two
 * cannot drift. Every control is disabled on purpose: there is no endpoint
 * behind this form (inventory row 40) and `InitializeRecord` takes the cap at
 * creation, with no instruction that changes it afterwards.
 */

const LABEL = "t-micro-caps block text-muted";

const INPUT =
  "t-body mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink disabled:bg-inset disabled:text-muted";

export function TextField({
  label,
  hint,
  type = "text",
  inputMode,
  defaultValue,
}: {
  label: string;
  hint?: string;
  type?: "text" | "datetime-local";
  inputMode?: "numeric";
  defaultValue?: string;
}) {
  return (
    <label className="block">
      <span className={LABEL}>{label}</span>
      <input
        type={type}
        inputMode={inputMode}
        className={INPUT}
        defaultValue={defaultValue}
        disabled
      />
      {hint && <span className="t-micro mt-1 block text-muted">{hint}</span>}
    </label>
  );
}

/** A disabled pill, drawn as the choice a real form would offer. */
function ModeOption({ label, note, active }: { label: string; note: string; active?: boolean }) {
  return (
    <span
      className={`inline-flex flex-col gap-1 rounded-panel border px-4 py-3 ${
        active ? "border-ink bg-inset" : "border-line bg-surface"
      }`}
    >
      <span className="t-meta text-ink">{label}</span>
      <span className="t-micro text-muted">{note}</span>
    </span>
  );
}

const TIER_ROWS = ["Floor GA", "Lower bowl", "Upper bowl"];

export function EventRecordFields() {
  return (
    <>
      <section aria-labelledby="record">
        <h2 id="record" className="h-section">
          The record
        </h2>
        <fieldset disabled className="mt-6 grid gap-6 sm:grid-cols-2">
          <legend className="sr-only">Event record fields</legend>
          <TextField label="Event name" />
          <TextField label="Venue" />
          <TextField label="City" />
          <TextField label="Starts at" type="datetime-local" />
        </fieldset>
      </section>

      <section className="mt-12" aria-labelledby="tiers">
        <h2 id="tiers" className="h-section">
          Tiers
        </h2>
        <p className="t-meta mt-2 max-w-3xl text-muted">
          One row per tier: three are drawn here and the record carries a list. The cap is a
          multiple of the face value of each tier, so a single event-wide ceiling would be wrong the
          moment two tiers differ.
        </p>
        {TIER_ROWS.map((placeholder, row) => (
          <fieldset disabled key={placeholder} className="mt-4 grid gap-6 sm:grid-cols-3">
            <legend className="t-micro-caps text-muted">Tier {row + 1}</legend>
            <TextField label="Tier name" />
            <TextField label="Face value (lamports)" inputMode="numeric" />
            <TextField label="Supply" inputMode="numeric" />
          </fieldset>
        ))}
        <fieldset disabled className="mt-4">
          <button
            type="button"
            className="u-transition inline-flex h-11 items-center rounded-pill border border-control bg-surface px-5 t-meta text-ink disabled:text-muted"
          >
            Add another tier
          </button>
        </fieldset>
      </section>

      <section className="mt-12" aria-labelledby="resale">
        <h2 id="resale" className="h-section">
          Resale
        </h2>

        <p className="t-micro-caps mt-6 text-muted" id="resale-mode-label">
          Resale mode
        </p>
        <div role="group" aria-labelledby="resale-mode-label" className="mt-3 grid gap-3 sm:grid-cols-3">
          <ModeOption label="Open" note="A listing at or under the ceiling is admitted." active />
          <ModeOption label="Monitored" note="Same ceiling; the listing is marked monitored in the record." />
          <ModeOption label="Banned" note="No listing is accepted, at any price." />
        </div>
        <p className="t-micro mt-2 text-muted">
          Monitored changes the record&apos;s label and nothing else in this build: no review queue
          exists, so nothing is flagged.
        </p>

        <fieldset disabled className="mt-8 grid gap-6 sm:grid-cols-2">
          <legend className="sr-only">Resale cap and jurisdiction</legend>
          <TextField label="Cap (basis points over face)" inputMode="numeric" />
          <label className="block">
            <span className={LABEL}>Jurisdiction (whose resale law applies)</span>
            <select className={`${INPUT} disabled:text-muted`} disabled>
              <option value="">Resolved at initialisation</option>
            </select>
            <span className="t-micro mt-1 block text-muted">
              This picks the law whose cap applies to the price. It is not a geo-fence: no buyer
              location is read and no wallet is refused for being elsewhere.
            </span>
          </label>
        </fieldset>

        <Panel className="mt-6 max-w-3xl">
          <p className="t-micro-caps text-muted">The rule these fields set</p>
          <p className="figure t-meta mt-2 text-ink">
            {"price * 10000 <= face * (10000 + cap_bps)"}
          </p>
          <ul className="t-body mt-4 space-y-2 text-muted">
            <li>The cap is immutable once the record is initialised. No instruction changes it.</li>
            <li>The jurisdiction gate can only tighten the cap, never loosen it.</li>
            <li>
              Where the jurisdiction resolves to a 0 bps cap, the ceiling equals face and any markup
              is refused.
            </li>
          </ul>
        </Panel>
      </section>

      <section className="mt-12" aria-labelledby="fees">
        <h2 id="fees" className="h-section">
          Artist fee and flip tax
        </h2>
        <p className="t-meta mt-2 max-w-3xl text-muted">
          Both are seller-paid legs in the same transaction as the resale: they are deducted from
          what the seller receives, not added to what the buyer pays.
        </p>

        <fieldset disabled className="mt-6 grid gap-6 sm:grid-cols-2">
          <legend className="sr-only">Artist fee</legend>
          <TextField
            label="Artist fee (basis points of the resale price)"
            inputMode="numeric"
            hint="0 disables the leg. The fee is paid to the wallet below."
          />
          <TextField
            label="Artist wallet (set at creation, not editable here)"
            hint="No wallet field exists in the event contract, so this row names the gap rather than a value."
          />
          <div className="sm:col-span-2 flex flex-wrap gap-3">
            <ModeOption label="Artist fee on every resale" note="A switch at creation, like the cap." />
            <ModeOption
              label="Flip tax, 15% falling to 0 over 30 days"
              note="Full rate under an hour, linear to zero at 30 days, floored. Fixed by the module, not an event setting."
              active
            />
          </div>
        </fieldset>

        <fieldset disabled className="mt-8 max-w-md">
          <legend className="sr-only">Organiser cap override</legend>
          <TextField
            label="Organiser cap override (basis points, blank = cap above)"
            inputMode="numeric"
            hint="A setting at creation, not a control after it: the on-chain cap cannot be changed."
          />
        </fieldset>
      </section>
    </>
  );
}

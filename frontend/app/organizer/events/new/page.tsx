import { Panel, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";

export const metadata = { title: "Create an event" };

/**
 * The shape of an event record, drawn as fields and not submitted.
 *
 * Nothing on this screen calls the backend and there is no endpoint behind the
 * form (inventory row 40): `InitializeRecord` takes the cap at creation and no
 * instruction changes it afterwards. The fields are disabled together with the
 * Unavailable panel rather than standing alone, because a lone dead input reads
 * as a bug in the screen.
 */

const LABEL = "t-micro-caps block text-muted";

const INPUT =
  "t-body mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink disabled:bg-inset disabled:text-muted";

function TextField({
  label,
  type = "text",
  inputMode,
}: {
  label: string;
  type?: "text" | "datetime-local";
  inputMode?: "numeric";
}) {
  return (
    <label className="block">
      <span className={LABEL}>{label}</span>
      <input type={type} inputMode={inputMode} className={INPUT} disabled />
    </label>
  );
}

export default function NewEventPage() {
  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">Create an event</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          The fields an event record is initialised from, with the resale cap beside them. Nothing
          here submits: there is no endpoint behind the form.
        </p>
      </header>

      <form className="mt-12">
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
            One row per tier. The cap is a multiple of the face value of each tier, so a single
            event-wide ceiling would be wrong the moment two tiers differ.
          </p>
          <fieldset disabled className="mt-6 grid gap-6 sm:grid-cols-3">
            <legend className="sr-only">Tier one</legend>
            <TextField label="Tier name" />
            <TextField label="Face value (lamports)" inputMode="numeric" />
            <TextField label="Supply" inputMode="numeric" />
          </fieldset>
        </section>

        <section className="mt-12" aria-labelledby="cap">
          <h2 id="cap" className="h-section">
            Resale cap
          </h2>
          <fieldset disabled className="mt-6 max-w-sm">
            <legend className="sr-only">Resale cap</legend>
            <TextField label="Cap (basis points over face)" inputMode="numeric" />
          </fieldset>

          <Panel className="mt-6 max-w-3xl">
            <p className="t-micro-caps text-muted">The rule this field sets</p>
            <p className="figure t-meta mt-2 text-ink">
              {"price * 10000 <= face * (10000 + cap_bps)"}
            </p>
            <ul className="t-body mt-4 space-y-2 text-muted">
              <li>The cap is immutable once the record is initialised. No instruction changes it.</li>
              <li>The jurisdiction gate can only tighten the cap, never loosen it.</li>
            </ul>
          </Panel>
        </section>

        <div className="mt-12">
          <Unavailable
            capability={capabilities.eventCreation}
            title="Create this event"
          />
          <p className="t-body mt-4 max-w-3xl text-muted">
            Ticket issuance has no endpoint either, so even a record that existed could not produce
            a ticket.
          </p>
        </div>
      </form>
    </div>
  );
}

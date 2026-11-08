import { notFound } from "next/navigation";
import { ApiError, getEvent, getTicket } from "@/lib/api";
import { capabilities } from "@/lib/capabilities";
import type { Capability } from "@/lib/capabilities";
import type { Event, Ticket, TicketStatus } from "@/lib/types";
import { AddressPill } from "@/components/AddressPill";
import { Chip, DataSourceNote, Panel, Unavailable } from "@/components/ui";
import { formatDateTime } from "@/lib/format";

export const metadata = { title: "Door" };

/**
 * The door screen reads real fields and stops there. It does not admit anyone,
 * because nothing in the backend makes an admission decision, and it does not
 * mint a code, because no code format exists (brief 6.2 /door, 5.10).
 */

const STATUS_LABEL: Record<TicketStatus, string> = {
  valid: "Valid",
  listed: "Listed",
  redeemed: "Redeemed",
  revoked: "Revoked",
};

type Tone = "positive" | "neutral" | "danger";

/**
 * The state of this ticket at the door, derived only from `status` and
 * `redeemedAt`:
 *
 *   revoked                                  -> danger, "Revoked"
 *   redeemed, or redeemedAt set              -> neutral, "Already redeemed"
 *   valid and redeemedAt null                -> positive, "Valid, not redeemed"
 *   anything else (listed)                   -> neutral, the status word
 *
 * The label states the fields. It is not an admission decision, because the
 * backend does not make one.
 */
function doorState(ticket: Ticket): { label: string; tone: Tone } {
  if (ticket.status === "revoked") return { label: "Revoked", tone: "danger" };
  if (ticket.status === "redeemed" || ticket.redeemedAt !== null) {
    return { label: "Already redeemed", tone: "neutral" };
  }
  if (ticket.status === "valid") return { label: "Valid, not redeemed", tone: "positive" };
  return { label: STATUS_LABEL[ticket.status], tone: "neutral" };
}

/**
 * Redeem is missing for a different reason than the scanner: there is no write
 * path at all, and the program has no redeem instruction. The panel says both
 * rather than reusing the door-code entry, whose gap is the code format.
 */
const REDEEM: Capability = {
  available: false,
  missing:
    "A redeem endpoint, and a redeem instruction in the program. Neither exists: redemption is recorded as a fixture ledger row and nothing can write one.",
  endpoint: "None. The contract has no redeem endpoint and the program has no redeem instruction.",
  shows:
    "The ticket's own redemption field and any redeem row already in its ledger, read and never written.",
};

/** The ticket id lives in `?ticket=`; a repeated parameter takes the first. */
function firstValue(value: string | string[] | undefined): string | null {
  const raw = Array.isArray(value) ? value[0] : value;
  const trimmed = raw?.trim() ?? "";
  return trimmed === "" ? null : trimmed;
}

/** One hairline row. */
function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-line py-3">
      <dt className="t-micro-caps text-muted">{label}</dt>
      <dd className="t-meta min-w-0 text-ink">{children}</dd>
    </div>
  );
}

/** The lookup. A native GET form, so it works before hydration and without JS. */
function TicketLookupForm({ defaultValue }: { defaultValue?: string }) {
  return (
    <Panel>
      <form action="/door" method="get">
        <label htmlFor="ticket" className="t-micro-caps block text-muted">
          Ticket id or mint address
        </label>
        <div className="mt-3 flex flex-col gap-3 sm:flex-row">
          <input
            id="ticket"
            name="ticket"
            type="text"
            required
            autoComplete="off"
            spellCheck={false}
            defaultValue={defaultValue ?? ""}
            className="figure t-meta h-12 w-full rounded-input border border-control bg-surface px-4 text-ink"
          />
          <button
            type="submit"
            className="u-transition inline-flex h-12 shrink-0 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta font-medium text-on-accent hover:border-accent-press hover:bg-accent-press"
          >
            Look up
          </button>
        </div>
      </form>
    </Panel>
  );
}

type Lookup =
  | { kind: "failed"; message: string; code: string }
  | { kind: "found"; ticket: Ticket; event: Event | null };

/**
 * getTicket takes an id or a mint address. A 404 is the not-found page; any
 * other API failure is shown here with the backend's own message and code,
 * because a door needs to know why a lookup failed.
 */
async function lookup(id: string): Promise<Lookup> {
  try {
    const ticket = await getTicket(id);
    const event = await getEvent(ticket.eventId).catch((error: unknown) => {
      // A ticket whose event cannot be read still has a record worth showing.
      if (error instanceof ApiError && error.status === 404) return null;
      throw error;
    });
    return { kind: "found", ticket, event };
  } catch (error) {
    if (error instanceof ApiError) {
      if (error.status === 404) notFound();
      return { kind: "failed", message: error.message, code: error.code };
    }
    throw error;
  }
}

/**
 * Static export has no request to read a query string from. `force-static`
 * tells Next to render this route once at build time with an empty
 * `searchParams`, which is the default (unfiltered) view. Filter links still
 * work as URLs; the values they carry are simply not read by the export.
 */
export const dynamic = "force-static";

export default async function DoorPage({
  searchParams,
}: {
  searchParams: Promise<{ ticket?: string | string[] }>;
}) {
  const { ticket: ticketParam } = await searchParams;
  const ticketId = firstValue(ticketParam);
  const result = ticketId === null ? null : await lookup(ticketId);

  const failed = result !== null && result.kind === "failed" ? result : null;
  const found = result !== null && result.kind === "found" ? result : null;

  const state = found === null ? null : doorState(found.ticket);
  const tier =
    found === null
      ? null
      : (found.event?.tiers.find((row) => row.id === found.ticket.tierId) ?? null);

  return (
    <div className="box py-12">
      <h1 className="h-section">Door</h1>

      {result === null ? (
        // No id: the form and nothing else. No pretend scan, no sample ticket.
        <div className="mt-8 max-w-2xl">
          <TicketLookupForm />
        </div>
      ) : (
        <div className="mt-12 space-y-12">
          {failed !== null && (
            <section>
              <h2 className="h-section">The lookup failed</h2>
              <Panel className="mt-6">
                <p className="t-body text-ink">{failed.message}</p>
                <p className="figure t-micro mt-2 text-muted">code {failed.code}</p>
                <p className="t-meta mt-4 text-muted">
                  Nothing was read, so there is nothing to show for this id.
                </p>
              </Panel>
            </section>
          )}

          {found !== null && state !== null && (
            <section>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <h2 className="h-section">
                  Ticket <span className="figure">{found.ticket.serial}</span>
                </h2>
                <Chip tone={state.tone}>{state.label}</Chip>
              </div>

              <dl className="mt-6 border-t border-line">
                <Row label="Serial">
                  <span className="figure">{found.ticket.serial}</span>
                </Row>
                <Row label="Status">{STATUS_LABEL[found.ticket.status]}</Row>
                <Row label="Redeemed">
                  {found.ticket.redeemedAt === null ? (
                    "Not redeemed"
                  ) : (
                    <span className="figure">{formatDateTime(found.ticket.redeemedAt)}</span>
                  )}
                </Row>
                <Row label="Owner">
                  <AddressPill address={found.ticket.ownerWallet} label="current owner" />
                </Row>
                <Row label="Event">{found.event?.name ?? "—"}</Row>
                <Row label="Tier">{tier?.name ?? "—"}</Row>
              </dl>

              {!found.event && (
                <p className="t-meta mt-3 text-muted">
                  The event this ticket belongs to could not be read.
                </p>
              )}

              <div className="mt-4">
                <DataSourceNote dataSource={found.ticket.dataSource} />
              </div>
            </section>
          )}

          <Unavailable title="Redeem at the door" capability={REDEEM} />

          <Unavailable title="Scanner" capability={capabilities.doorCode} />

          <section>
            <h2 className="h-section">Check another ticket</h2>
            <div className="mt-6 max-w-2xl">
              <TicketLookupForm defaultValue={ticketId ?? undefined} />
            </div>
          </section>
        </div>
      )}
    </div>
  );
}

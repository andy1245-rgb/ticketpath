import { ApiError, getEvent, getTicket, getTickets } from "@/lib/api";
import type { Event, Ticket } from "@/lib/types";
import { DataSourceNote, Panel } from "@/components/ui";
import { formatDateTime, formatSol } from "@/lib/format";
import { ListClient } from "./ListClient";

export const metadata = { title: "List a ticket" };

/**
 * One ticket's resale price, against the cap that ticket's tier actually
 * carries. The ticket and its event are read here, on the server; the price
 * field is the only client-side part because the cap check has to answer on
 * every keystroke.
 *
 * A failed read is rendered on this screen with the backend's own message and
 * code, because the message is the diagnosable part and the error boundary
 * would throw it away.
 */
/**
 * Static export: every ticket URL is enumerated at build time from lib/api,
 * because there is no server to resolve /tickets/<id> on demand.
 */
export async function generateStaticParams(): Promise<Array<{ ticketId: string }>> {
  const { items } = await getTickets({ limit: 1000 });
  return items.map((ticket) => ({ ticketId: ticket.id }));
}

/** With no server, any other ticket id is a 404 the host serves. */
export const dynamicParams = false;

export default async function ListTicketPage({
  params,
}: {
  params: Promise<{ ticketId: string }>;
}) {
  const { ticketId } = await params;

  let ticket: Ticket | null = null;
  let event: Event | null = null;
  let failure: ApiError | null = null;

  try {
    ticket = await getTicket(ticketId);
    event = await getEvent(ticket.eventId);
  } catch (error) {
    if (error instanceof ApiError) failure = error;
    else throw error;
  }

  if (failure !== null || ticket === null || event === null) {
    return (
      <div className="box pt-16">
        <header>
          <h1 className="h-display">List for resale</h1>
        </header>

        <div className="mt-12">
          <Panel className="max-w-3xl">
            <p className="t-micro-caps text-muted">Error</p>
            <h2 className="h-section mt-2">This ticket could not be read</h2>
            <dl className="mt-6 space-y-4">
              <div>
                <dt className="t-micro-caps text-muted">Message</dt>
                <dd className="t-body mt-1 text-ink">
                  {failure?.message ?? "The ticket or its event came back empty."}
                </dd>
              </div>
              <div>
                <dt className="t-micro-caps text-muted">Code</dt>
                <dd className="figure t-meta mt-1 text-ink">{failure?.code ?? "no_code"}</dd>
              </div>
              {failure !== null && (
                <div>
                  <dt className="t-micro-caps text-muted">Path</dt>
                  <dd className="figure t-meta mt-1 text-ink">{failure.path}</dd>
                </div>
              )}
            </dl>
          </Panel>
        </div>
      </div>
    );
  }

  return (
    <div className="box pt-16">
      <header>
        <h1 className="h-display">List for resale</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          {event.name} · serial <span className="figure">{ticket.serial}</span> · face{" "}
          <span className="figure">{formatSol(ticket.faceValueLamports)}</span>
        </p>
        <p className="t-meta mt-2 text-muted">
          Starts {formatDateTime(event.startsAt)} at {event.venue}, {event.city}.
        </p>
      </header>

      <ListClient ticket={ticket} event={event} />

      <div className="mt-12">
        <DataSourceNote dataSource={ticket.dataSource} />
      </div>
    </div>
  );
}

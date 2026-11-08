import Link from "next/link";
import { notFound } from "next/navigation";
import { ApiError, getEvent, getEvents } from "@/lib/api";
import { Panel, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";
import { EventRecordFields } from "@/components/organizer/EventRecordFields";
import { formatDateTime } from "@/lib/format";

export const metadata = { title: "Edit an event" };

/** One page per event in the fixture set, so the export has a real URL to serve. */
export async function generateStaticParams(): Promise<Array<{ id: string }>> {
  const { items } = await getEvents({ limit: 1000 });
  return items.map((event) => ({ id: event.id }));
}

/** With no server, any other id is a 404 the host serves, not a page to render. */
export const dynamicParams = false;

/**
 * The edit screen, which did not exist: the organiser surface offered a create
 * form and no way to change an event afterwards. The fields are the create
 * form's own component, disabled for the same reason, with the one thing an
 * editor must be told first: the cap cannot be changed after initialisation.
 */
export default async function EditEventPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;

  let event;
  try {
    event = await getEvent(id);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  return (
    <div className="box pt-16">
      <header>
        <p className="t-micro-caps text-muted">
          <Link href="/organizer" className="underline-offset-4 hover:underline">
            Organisers
          </Link>
          {" / "}
          <Link href="/organizer/events" className="underline-offset-4 hover:underline">
            Your events
          </Link>
          {" / "}
          <span>Edit</span>
        </p>
        <h1 className="h-display mt-3">Edit {event.name}</h1>
        <p className="t-meta mt-4 text-muted">
          {event.venue}, {event.city} · starts {formatDateTime(event.startsAt)} · id{" "}
          <span className="figure">{event.id}</span>
        </p>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          The same fields the record was initialised from. Nothing here submits, and one field could
          not change even with an endpoint behind it: the resale cap is fixed when the record is
          initialised, and no instruction raises or lowers it.
        </p>
      </header>

      <div className="mt-8 max-w-3xl">
        <Unavailable capability={capabilities.eventCreation} title="Save changes to this event" />
        <Panel className="mt-4">
          <p className="t-micro-caps text-muted">What an editor could and could not change</p>
          <ul className="t-body mt-3 space-y-2 text-muted">
            <li>The name, venue, start time and tier list are record fields with no write path.</li>
            <li>
              The cap and the organiser override are set once, at initialisation. An edit screen that
              offered them as live controls would contradict the rule the rest of this product
              states.
            </li>
            <li>
              The jurisdiction can only tighten the cap. A record initialised under a 0 bps
              jurisdiction stays at a ceiling of face value.
            </li>
          </ul>
        </Panel>
      </div>

      <form className="mt-12">
        <EventRecordFields />
      </form>
    </div>
  );
}

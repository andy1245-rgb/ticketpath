import Link from "next/link";
import { Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";
import { EventRecordFields } from "@/components/organizer/EventRecordFields";

export const metadata = { title: "Create an event" };

/**
 * The shape of an event record, drawn as fields and not submitted.
 *
 * The Unavailable panel sits directly under the header rather than after the
 * fields: on a phone the fields are two screens tall, and a visitor who met five
 * dead controls before any explanation would read the screen as broken.
 *
 * The fields themselves are shared with the edit screen, because a create form
 * and an edit form for the same record must not drift apart.
 */
export default function NewEventPage() {
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
          <span>Create</span>
        </p>
        <h1 className="h-display mt-3">Create an event</h1>
        <p className="t-deck mt-6 max-w-3xl text-ink">
          Every field an event record is initialised from, including the resale mode, the
          jurisdiction, the artist fee and the flip tax. Nothing here submits: there is no endpoint
          behind the form.
        </p>
      </header>

      <div className="mt-8 max-w-3xl">
        <Unavailable capability={capabilities.eventCreation} title="Create this event" />
        <p className="t-body mt-4 text-muted">
          Ticket issuance has no endpoint either, so even a record that existed could not produce a
          ticket.
        </p>
      </div>

      <form className="mt-12">
        <EventRecordFields />
      </form>
    </div>
  );
}

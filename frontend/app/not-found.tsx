import type { Metadata } from "next";
import Link from "next/link";
import { Pill } from "@/components/ui";

/** A 404 gets its own title, so the tab does not read like the marketing page. */
export const metadata: Metadata = { title: "Page not found" };

const ROUTES = [
  { href: "/events", label: "Events" },
  { href: "/my-tickets", label: "My tickets" },
  { href: "/rules", label: "How the cap works" },
  { href: "/demo", label: "Live demo" },
];

/**
 * One heading, one sentence, two ways on. The single `Back to events` pill left
 * a reader who mistyped `/my-tickets` or `/rules` with no route-aware recovery,
 * and under the static export this page is what a wrong URL lands on, so it
 * also names the four screens a reader most often wants.
 */
export default function NotFound(): React.ReactElement {
  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-2xl">
        <h1 className="h-display text-ink">Page not found</h1>
        <p className="t-deck mt-4 text-muted">
          The address you asked for does not exist. These pages do:
        </p>
        <div className="mt-6 flex flex-wrap gap-x-6 gap-y-3">
          {ROUTES.map((route) => (
            <Link
              key={route.href}
              href={route.href}
              className="u-transition t-meta text-ink underline decoration-1 underline-offset-4 hover:text-accent"
            >
              {route.label}
            </Link>
          ))}
        </div>
        <div className="mt-8 flex flex-wrap items-center gap-3">
          <Pill href="/events" variant="primary">
            Back to events
          </Pill>
          <Pill href="/" variant="secondary">
            Home
          </Pill>
        </div>
      </div>
    </div>
  );
}

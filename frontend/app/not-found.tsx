import Link from "next/link";

/** One heading, one sentence, one way back. Nothing here guesses what was meant. */
export default function NotFound(): React.ReactElement {
  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-2xl">
        <h1 className="h-display text-ink">Page not found</h1>
        <p className="t-deck mt-4 text-muted">The address you asked for does not exist.</p>
        <Link
          href="/events"
          className="u-transition mt-8 inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
        >
          Back to events
        </Link>
      </div>
    </div>
  );
}

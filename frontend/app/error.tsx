"use client";

import { useEffect } from "react";

/**
 * The route-level error boundary. It stays a client component because that is
 * what a boundary is, and it keeps its reset: a failed read is usually a backend
 * that was not up, so retrying is the useful action and a reload is not.
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}): React.ReactElement {
  useEffect(() => {
    // The digest is the only handle Next gives on a server-side failure, and the
    // console line is what makes a failing backend call diagnosable at all.
    console.error(error);
  }, [error]);

  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-2xl">
        <p className="t-micro-caps text-danger">Error</p>
        <h1 className="h-display mt-3 text-ink">Something went wrong</h1>
        {/* A visitor reads this page. The build's configuration is the console
            line's business, and the digest below is the only handle that ties
            the two together. */}
        <p className="t-deck mt-4 text-muted">
          We could not load this data. Try again, or browse the events list.
        </p>
        {error.digest && (
          <p className="t-micro mt-4 text-muted">
            Digest <span className="figure">{error.digest}</span>
          </p>
        )}
        <button
          type="button"
          onClick={reset}
          className="u-transition mt-8 inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
        >
          Try again
        </button>
      </div>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { shortAddress } from "@/lib/format";

/**
 * An address is the primary identifier all over this app, so it gets one
 * component: truncated in the mono face, on the inset surface, with a copy
 * control that is a real button with a real 44px target.
 *
 * The full address stays in the title attribute, so it is never only reachable
 * by copying it.
 */
export function AddressPill({
  address,
  label = "wallet",
  className = "",
}: {
  address: string;
  label?: string;
  className?: string;
  /**
   * The previous version could link the address to the explorer. This build
   * reaches the chain through SignatureRef and the mint, so the pill is text
   * and a copy button, and the prop is accepted and does nothing.
   */
  link?: boolean;
}): React.ReactElement {
  const [status, setStatus] = useState<"idle" | "copied" | "unavailable">("idle");
  const reset = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (reset.current) clearTimeout(reset.current);
    };
  }, []);

  async function copy(): Promise<void> {
    if (reset.current) clearTimeout(reset.current);
    try {
      // Undefined on an insecure origin or in a browser that withholds the
      // API; the throw is caught below and the button says so, out loud.
      await navigator.clipboard.writeText(address);
      setStatus("copied");
      reset.current = setTimeout(() => setStatus("idle"), 2000);
    } catch {
      setStatus("unavailable");
    }
  }

  const name = status === "copied" ? "Copied" : `Copy ${label} address`;

  return (
    <span
      className={`inline-flex min-h-6 items-center gap-1 rounded-pill bg-inset pr-0 pl-3 ${className}`}
    >
      <span className="figure t-meta text-ink" title={address}>
        {shortAddress(address)}
      </span>

      {/* 44x44 whatever the glyph, and the negative block margin stops the
          target from stretching the pill to the button's height. */}
      <button
        type="button"
        onClick={() => {
          void copy();
        }}
        aria-label={name}
        className="u-transition -my-2 inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-pill text-muted hover:text-ink"
      >
        {status === "copied" ? (
          <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
            <path
              d="m4.5 10.5 3.5 3.5 7.5-8"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true" focusable="false">
            <rect
              x="7.5"
              y="7.5"
              width="9"
              height="9"
              rx="2"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            />
            <path
              d="M12.5 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v5.5a2 2 0 0 0 2 2h2"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        )}
      </button>

      {/* The button's name changes on success; this line is what a screen
          reader hears when the clipboard is not there at all. */}
      <span aria-live="polite" className="sr-only">
        {status === "unavailable" ? "Clipboard unavailable in this browser." : ""}
      </span>
    </span>
  );
}

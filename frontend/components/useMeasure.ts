"use client";

import { useEffect, useRef, useState, type RefObject } from "react";

/**
 * Observe an element's content-box width.
 *
 * Charts need the real pixel width rather than a fixed viewBox: scaling a
 * fixed viewBox to fit the container scales the *text* with it, so the same
 * chart in a half-width column renders unreadable 7px labels. Measuring lets
 * one viewBox unit stay one CSS pixel, which keeps type at its stated size.
 */
export function useMeasure<T extends HTMLElement>(
  fallback = 640,
): [RefObject<T | null>, number] {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(fallback);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const observer = new ResizeObserver((entries) => {
      const next = entries[0]?.contentRect.width;
      if (next && next > 0) setWidth(next);
    });
    observer.observe(el);
    setWidth(el.getBoundingClientRect().width || fallback);

    return () => observer.disconnect();
  }, [fallback]);

  return [ref, width];
}

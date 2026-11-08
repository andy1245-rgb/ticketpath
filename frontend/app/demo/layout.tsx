import type { Metadata } from "next";

/**
 * `app/demo/page.tsx` is a client component, so it cannot export `metadata`.
 * This file exists only to give the route its own tab title: the demo used to
 * inherit `SeatPass · Tickets on Solana` and was indistinguishable from home in
 * a row of tabs.
 */
export const metadata: Metadata = {
  title: "Live demo",
  description:
    "Both sides of a resale, simulated in this browser: buy a ticket, try to flip it, and watch the cap predicate decide.",
};

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return children;
}

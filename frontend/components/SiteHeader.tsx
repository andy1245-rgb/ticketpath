"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { RoleToggle } from "@/components/RoleToggle";

/**
 * The five pages a reader uses, plus the buyer's own screen. `/my-tickets` and
 * `/door` shipped as routes that nothing linked to, so both could only be
 * reached by typing the path: the buyer's holdings after "the ticket lands in a
 * wallet", and the organiser's scan-and-redeem screen.
 *
 * "organizer" is spelled one way here, in the footer, in the role toggle and on
 * `/organizer`. It used to be three spellings across four files, which reads as
 * two products.
 */
const NAV = [
  { href: "/events", label: "Events" },
  { href: "/demo", label: "Live demo" },
  { href: "/rules#enforcement-today", label: "Proof on devnet" },
  { href: "/pricing", label: "Pricing and data" },
  { href: "/organizer", label: "For organizers" },
];

/** Reachable from the menu below xl and from the footer; not in the bar. */
const MORE = [
  { href: "/my-tickets", label: "My tickets" },
  { href: "/door", label: "Door" },
  { href: "/rules", label: "How the cap works" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/events") return pathname === "/events" || pathname.startsWith("/events/");
  if (href === "/my-tickets")
    return pathname === "/my-tickets" || pathname.startsWith("/tickets/");
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLinks({ pathname }: { pathname: string }) {
  return (
    <>
      {NAV.map((item) => {
        const active = isActive(pathname, item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            aria-current={active ? "page" : undefined}
            className={`u-transition inline-flex h-11 shrink-0 items-center border-b-2 pt-px t-meta ${
              active ? "border-ink text-ink" : "border-transparent text-muted hover:text-ink"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </>
  );
}

/**
 * One header at every width: wordmark on the left edge, the right cluster on the
 * right edge, the navigation centred on the content box at the desktop
 * breakpoint and on its own wrapping row below it. Opaque surface and one
 * hairline, no blur, no avatar, no tab bar.
 *
 * The Buyer / Organizer toggle is in the header on every route except `/demo`,
 * which renders its own. Here it writes the browser-local role and moves to
 * `/events` or `/organizer`; it is a view switch in a simulated demo, not a
 * sign-in. The Browse events pill is hidden below `sm` so the 360px row fits.
 *
 * One navigation landmark, not two. The desktop row and the mobile row used to
 * be separate `<nav aria-label="Primary">` elements hidden at different
 * breakpoints, which doubles every link in the tree for anything that ignores
 * `display:none`.
 */
export function SiteHeader() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  useEffect(() => setOpen(false), [pathname]);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface shadow-card">
      <div className="box">
        <div className="flex h-16 items-center gap-4">
          <Link
            href="/"
            className="u-transition shrink-0 text-ink hover:text-accent xl:mr-8"
            aria-label="SeatPass, home"
          >
            <span className="text-[14px] font-semibold tracking-[0.08em]">SEATPASS</span>
          </Link>

          <nav aria-label="Primary" className="hidden min-w-0 items-center gap-6 xl:flex">
            <NavLinks pathname={pathname} />
          </nav>

          <div className="ml-auto flex shrink-0 items-center gap-3">
            {pathname !== "/demo" && pathname !== "/demo/" ? <RoleToggle navigate /> : null}
            <Link
              href="/events"
              className="u-transition hidden h-10 items-center justify-center rounded-pill border border-accent bg-accent px-5 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press md:inline-flex xl:ml-3"
            >
              Browse events
            </Link>
            <button
              type="button"
              aria-expanded={open}
              aria-controls="site-menu"
              onClick={() => setOpen((v) => !v)}
              className="u-transition inline-flex h-10 items-center rounded-pill border border-line px-4 t-meta text-ink hover:border-ink xl:hidden"
            >
              {open ? "Close" : "Menu"}
            </button>
          </div>
        </div>

        {open ? (
          <nav id="site-menu" aria-label="Menu" className="flex flex-wrap gap-x-6 gap-y-1 border-t border-line py-3 xl:hidden">
            {[...NAV, ...MORE].map((item) => (
              <Link
                key={item.href}
                href={item.href}
                aria-current={isActive(pathname, item.href) ? "page" : undefined}
                className="u-transition inline-flex h-11 items-center t-meta text-ink hover:text-accent"
              >
                {item.label}
              </Link>
            ))}
            <Link href="/account" className="u-transition inline-flex h-11 items-center t-meta text-ink hover:text-accent">
              Account
            </Link>
          </nav>
        ) : null}
      </div>
    </header>
  );
}

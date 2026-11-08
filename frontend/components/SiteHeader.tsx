"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/events", label: "Events" },
  { href: "/organizer", label: "For organizers" },
  { href: "/rules", label: "How the cap works" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/events") return pathname === "/events" || pathname.startsWith("/events/");
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
            className={`u-transition inline-flex h-11 items-center border-b-2 pt-px t-meta ${
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
 * One header at every width: 1fr auto 1fr so the navigation's centre sits on
 * the content box's centre (x=720 at 1440), wordmark on the left edge at 120
 * and the right cluster on 1320. Opaque surface and one hairline, no blur, no
 * avatar, no tab bar.
 */
export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface shadow-card">
      <div className="box">
        <div className="grid h-16 grid-cols-[1fr_auto_1fr] items-center">
          <Link
            href="/"
            className="u-transition justify-self-start text-ink hover:text-accent"
            aria-label="SeatPass, home"
          >
            <span className="text-[14px] font-semibold tracking-[0.08em]">SEATPASS</span>
          </Link>

          <nav aria-label="Primary" className="hidden justify-center gap-8 lg:flex">
            <NavLinks pathname={pathname} />
          </nav>

          <div className="col-start-3 flex items-center justify-end gap-3">
            <Link
              href="/account"
              className="u-transition hidden items-center t-body text-ink hover:text-accent sm:inline-flex"
            >
              Sign in
            </Link>
            <Link
              href="/events"
              className="u-transition inline-flex h-10 items-center justify-center rounded-pill border border-accent bg-accent px-5 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
            >
              Browse events
            </Link>
          </div>
        </div>

        {/* Below the breakpoint the navigation drops to its own row, in the gutter. */}
        <nav aria-label="Primary" className="-mt-1 flex gap-6 overflow-x-auto pb-3 lg:hidden">
          <NavLinks pathname={pathname} />
        </nav>
      </div>
    </header>
  );
}

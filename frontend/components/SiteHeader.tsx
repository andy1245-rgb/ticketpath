"use client";

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
  { href: "/my-tickets", label: "My tickets" },
  { href: "/organizer", label: "For organizers" },
  { href: "/rules", label: "How the cap works" },
  { href: "/rules#enforcement-today", label: "Proof on devnet" },
  { href: "/pricing", label: "Pricing and data" },
  { href: "/door", label: "Door" },
  { href: "/demo", label: "Live demo" },
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

  return (
    <header className="sticky top-0 z-20 border-b border-line bg-surface shadow-card">
      <div className="box">
        <div className="grid h-16 grid-cols-[auto_1fr_auto] items-center gap-3">
          <Link
            href="/"
            className="u-transition justify-self-start text-ink hover:text-accent"
            aria-label="SeatPass, home"
          >
            <span className="text-[14px] font-semibold tracking-[0.08em]">SEATPASS</span>
          </Link>

          <nav aria-label="Primary" className="hidden justify-center min-w-0 gap-4 lg:flex">
            <NavLinks pathname={pathname} />
          </nav>

          <div className="col-start-3 flex items-center justify-end gap-3">
            {pathname !== "/demo" && pathname !== "/demo/" ? <RoleToggle navigate /> : null}
            <Link
              href="/account"
              className="u-transition hidden items-center t-body text-ink hover:text-accent 2xl:inline-flex"
            >
              Account
            </Link>
            <Link
              href="/events"
              className="u-transition hidden h-10 items-center justify-center rounded-pill border border-accent bg-accent px-5 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press sm:inline-flex"
            >
              Browse events
            </Link>
          </div>
        </div>

        {/* Below the breakpoint the navigation drops to its own row and wraps
            onto a second line rather than scrolling sideways with no hint. */}
        <nav aria-label="Primary, mobile" className="-mt-1 flex flex-wrap gap-x-6 pb-2 lg:hidden">
          <NavLinks pathname={pathname} />
        </nav>
      </div>
    </header>
  );
}

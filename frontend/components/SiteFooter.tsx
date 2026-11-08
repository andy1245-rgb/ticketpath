import Link from "next/link";

const LINKS = [
  { href: "/events", label: "All events" },
  { href: "/organizer", label: "Organizer guide" },
  { href: "/rules", label: "Resale rules" },
  { href: "/rules#security", label: "Security model" },
];

/**
 * No rule of its own: the page's fourth hairline sits above the proof band and
 * the footer's top edge sits 96 under it.
 */
export function SiteFooter() {
  return (
    <footer className="box pb-16">
      <div className="flex flex-col gap-6 pt-16 sm:flex-row sm:items-center sm:justify-between">
        <Link href="/" className="u-transition text-ink hover:text-accent">
          <span className="text-[14px] font-semibold tracking-[0.08em]">SEATPASS</span>
        </Link>
        <nav aria-label="Footer" className="flex flex-wrap gap-x-6 gap-y-3">
          {LINKS.map((link) => (
            <Link key={link.href} href={link.href} className="u-transition t-meta text-muted hover:text-ink">
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
      <p className="t-micro mt-6 text-muted">Built at the Solana x MLH hackathon.</p>
    </footer>
  );
}

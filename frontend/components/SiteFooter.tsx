import Link from "next/link";

/**
 * Every route in the README's table is reachable by click from here or from the
 * header. `/verify` had no link anywhere in the shell: it was reachable only
 * from a failed checkout, on another page that nothing linked to.
 */
const LINKS = [
  { href: "/events", label: "All events" },
  { href: "/organizer", label: "Organizer guide" },
  { href: "/rules", label: "Resale rules" },
  { href: "/rules#security", label: "Security model" },
  { href: "/verify", label: "Verify your wallet" },
  { href: "/demo", label: "Live demo" },
  { href: "/pricing", label: "The pricing engine" },
  { href: "/about", label: "About" },
];

/** The public repository: the research record and the proof are all in it. */
const REPO_URL = "https://github.com/andy1245-rgb/ticketpath";

/**
 * No rule of its own: the page's fourth hairline sits above the proof band and
 * the footer's top edge sits 96 under it.
 *
 * The three footnotes are the questions a reader asks in the first thirty
 * seconds, and none of them had an answer in the shell before: is this live
 * (no, devnet, and no cluster is read), is this data real (no, it is the
 * bundled fixtures, and the label says so), and does the seller keep the
 * ceiling (no, the artist fee and the flip tax are seller-paid legs in the same
 * transaction).
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
      <p className="t-micro mt-6 text-muted">
        Devnet only. No real money moves on this build, and no cluster is read at build time.
      </p>
      <p className="t-micro mt-2 text-muted">
        The events, tickets and prices on these screens are the bundled fixtures, labelled
        where they appear. Nothing here is a measurement of a live market.
      </p>
      <p className="t-micro mt-2 text-muted">
        Resale proceeds are net of the artist fee and the flip tax, both paid by the seller.
      </p>
      <p className="t-micro mt-6 text-muted">
        Built for a Solana hackathon.{" "}
        <a
          href={REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="u-transition underline decoration-1 underline-offset-2 hover:text-ink"
        >
          Source and research record
        </a>
        .
      </p>
    </footer>
  );
}

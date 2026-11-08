import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "About SeatPass",
  description: "What SeatPass is, and what in this build is real and what is simulated.",
};

export default function AboutPage() {
  return (
    <div className="box py-16">
      <h1 className="h-section">About SeatPass</h1>
      <p className="t-body mt-4 max-w-[70ch]">
        SeatPass is a ticketing design where the resale price cap is a property of the ticket
        itself: a transfer above the ceiling is refused by a Solana program instead of by a
        policy page. This website is a front end and a browser simulation of that design.
      </p>

      <h2 className="h-section mt-12">Real</h2>
      <ul className="t-body mt-3 max-w-[70ch] list-disc pl-6 text-muted">
        <li>
          A cap program (v1) is deployed on Solana devnet. Its record holds one resale admitted
          at exactly the ceiling and one lamport higher refused with <code>6010 E_CAP_EXCEEDED</code>.
          The signatures and slots are on <Link href="/rules/" className="underline">/rules</Link>.
        </li>
        <li>
          The cap predicate the demo runs, <code>price * 10000 &lt;= face * (10000 + cap_bps)</code>,
          is the one the program checks.
        </li>
        <li>
          A six-agent run against a local validator, recorded in the repository, is shown on{" "}
          <Link href="/pricing/" className="underline">/pricing</Link>, apart from the larger dry-run swarms.
        </li>
      </ul>

      <h2 className="h-section mt-12">Simulated or not built</h2>
      <ul className="t-body mt-3 max-w-[70ch] list-disc pl-6 text-muted">
        <li>There is no backend on this site. Events, tickets and prices are bundled synthetic fixtures.</li>
        <li>
          <Link href="/demo/" className="underline">The live demo</Link> keeps its state in this browser only. No wallet, no
          money, no chain call.
        </li>
        <li>
          Region geo-lock, resale bans, freezes, the artist fee and the flip tax are app policy
          in the demo. The deployed v1 program enforces only the cap.
        </li>
        <li>Checkout, listing, transfer, refund and door codes are not wired to anything.</li>
      </ul>
    </div>
  );
}

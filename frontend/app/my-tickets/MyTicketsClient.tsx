"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useWallet } from "@solana/wallet-adapter-react";
import { ApiError, getEvents, getTickets, getWalletVerification } from "@/lib/api";
import type { DataSource, Event, Ticket, TicketStatus, WalletVerification } from "@/lib/types";
import { AddressPill } from "@/components/AddressPill";
import { WalletButton } from "@/components/WalletButton";
import { Chip, DataSourceNote, Panel, Pill, Skeleton } from "@/components/ui";
import { formatDateTime, formatSol } from "@/lib/format";

/**
 * Holdings, and the one screen in the product that cannot be a server
 * component: the wallet only exists in the browser.
 *
 * Nothing here auto-connects. If no wallet is connected the page says so and
 * offers the connect control, because a fabricated connected state would show
 * a stranger's fixtures as if they were the visitor's tickets.
 */

/** A ticket's status as the shared chip. Warning stays reserved for the cap. */
const STATUS: Record<
  TicketStatus,
  { label: string; tone: "positive" | "neutral" | "accent" | "danger" }
> = {
  valid: { label: "Valid", tone: "positive" },
  listed: { label: "Listed", tone: "accent" },
  redeemed: { label: "Redeemed", tone: "neutral" },
  revoked: { label: "Revoked", tone: "danger" },
};

/** One wallet's answer: its tickets, the events behind them, its verification. */
interface WalletData {
  tickets: Ticket[];
  events: Map<string, Event>;
  verification: WalletVerification;
  dataSource: DataSource | undefined;
}

type Load =
  | { phase: "loading" }
  | { phase: "ready"; data: WalletData }
  | { phase: "failed"; message: string; code: string };

const PRIMARY_BUTTON =
  "u-transition inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta font-medium text-on-accent hover:border-accent-press hover:bg-accent-press";

export function MyTicketsClient() {
  const { publicKey } = useWallet();
  const wallet = publicKey?.toBase58() ?? null;

  const [attempt, setAttempt] = useState(0);
  const [load, setLoad] = useState<Load>({ phase: "loading" });

  useEffect(() => {
    if (wallet === null) {
      // No wallet, no request. The screen shows the connect state instead.
      setLoad({ phase: "loading" });
      return;
    }

    let cancelled = false;
    setLoad({ phase: "loading" });

    void (async () => {
      try {
        const [ticketPage, eventPage, verification] = await Promise.all([
          getTickets({ ownerWallet: wallet, limit: 100 }),
          getEvents({ limit: 100 }),
          getWalletVerification(wallet),
        ]);
        if (cancelled) return;
        setLoad({
          phase: "ready",
          data: {
            tickets: ticketPage.items,
            events: new Map(eventPage.items.map((event) => [event.id, event])),
            verification,
            dataSource: ticketPage.dataSource,
          },
        });
      } catch (error) {
        if (cancelled) return;
        setLoad({
          phase: "failed",
          message: error instanceof Error ? error.message : "The request failed.",
          code: error instanceof ApiError ? error.code : "unknown_error",
        });
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [wallet, attempt]);

  return (
    <div className="box py-12">
      <header>
        <h1 className="h-section">My tickets</h1>
        <p className="t-body mt-2 max-w-2xl text-muted">
          Tickets are bound to the wallet that holds them, so this page reads the wallet you
          connect.
        </p>
      </header>

      {wallet === null ? (
        <Panel className="mt-12">
          <p className="t-body text-ink">Connect a wallet to see the tickets it holds.</p>
          <div className="mt-4">
            <WalletButton />
          </div>
        </Panel>
      ) : (
        <>
          {load.phase === "ready" && (
            <div className="mt-6">
              <DataSourceNote dataSource={load.data.dataSource} />
            </div>
          )}

          <section className="mt-12">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="h-section">Wallet</h2>
              <AddressPill address={wallet} label="connected wallet" />
              {load.phase === "ready" && (
                <Chip tone={load.data.verification.verified ? "positive" : "neutral"}>
                  {load.data.verification.verified ? "Verified" : "Not verified"}
                </Chip>
              )}
            </div>

            {load.phase === "ready" && (
              <Panel className="mt-6">
                <dl className="grid gap-x-8 gap-y-3 sm:grid-cols-3">
                  <div>
                    <dt className="t-micro-caps text-muted">Verified</dt>
                    <dd className="t-meta mt-1 text-ink">
                      {load.data.verification.verified ? "Yes" : "No"}
                    </dd>
                  </div>
                  <div>
                    <dt className="t-micro-caps text-muted">Verified at</dt>
                    <dd className="figure t-meta mt-1 text-ink">
                      {formatDateTime(load.data.verification.verifiedAt)}
                    </dd>
                  </div>
                  <div>
                    <dt className="t-micro-caps text-muted">Method</dt>
                    <dd className="t-meta mt-1 text-ink">
                      {load.data.verification.method === null
                        ? "—"
                        : load.data.verification.method === "wallet_signature"
                          ? "Wallet signature"
                          : "Identity"}
                    </dd>
                  </div>
                </dl>

                {load.data.verification.flags.length > 0 && (
                  <ul className="mt-4 flex flex-wrap gap-2">
                    {load.data.verification.flags.map((flag) => (
                      <li key={flag}>
                        <Chip tone="neutral">{flag}</Chip>
                      </li>
                    ))}
                  </ul>
                )}

                {!load.data.verification.verified && (
                  <p className="t-meta mt-4 text-muted">
                    Holding a ticket does not require verification.{" "}
                    <Link
                      href="/verify"
                      className="u-transition text-ink underline decoration-1 underline-offset-2 hover:text-accent"
                    >
                      Verify this wallet
                    </Link>
                    .
                  </p>
                )}
              </Panel>
            )}
          </section>

          <section className="mt-12">
            <h2 className="h-section">Holdings</h2>

            {load.phase === "loading" ? (
              <div className="mt-6">
                <Skeleton lines={4} />
              </div>
            ) : load.phase === "failed" ? (
              <Panel className="mt-6">
                <p className="t-body text-ink">{load.message}</p>
                <p className="figure t-micro mt-2 text-muted">code {load.code}</p>
                <button
                  type="button"
                  onClick={() => setAttempt((count) => count + 1)}
                  className={`${PRIMARY_BUTTON} mt-4`}
                >
                  Try again
                </button>
              </Panel>
            ) : load.data.tickets.length === 0 ? (
              <Panel className="mt-6">
                <p className="t-body text-ink">This wallet holds no tickets.</p>
                <p className="t-meta mt-2 text-muted">
                  Tickets issued to or transferred to this wallet appear here.
                </p>
                <div className="mt-4">
                  <Pill href="/events" variant="secondary" size="sm">
                    Browse events
                  </Pill>
                </div>
              </Panel>
            ) : (
              <div className="mt-6 overflow-x-auto rounded-panel border border-line">
                <table className="w-full border-collapse">
                  <caption className="sr-only">
                    Tickets held by this wallet: serial, event, tier, face value, status, and a link
                    to each ticket&rsquo;s record.
                  </caption>
                  <thead>
                    <tr className="border-b border-line">
                      <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-left text-muted">
                        Serial
                      </th>
                      <th scope="col" className="t-micro-caps px-6 py-3 text-left text-muted">
                        Event
                      </th>
                      <th scope="col" className="t-micro-caps px-6 py-3 text-left text-muted">
                        Tier
                      </th>
                      <th scope="col" className="t-micro-caps whitespace-nowrap px-6 py-3 text-right text-muted">
                        Face value
                      </th>
                      <th scope="col" className="t-micro-caps px-6 py-3 text-left text-muted">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {load.data.tickets.map((ticket) => {
                      const event = load.data.events.get(ticket.eventId) ?? null;
                      const tier = event?.tiers.find((row) => row.id === ticket.tierId) ?? null;
                      const status = STATUS[ticket.status];

                      return (
                        <tr key={ticket.id} className="border-b border-line last:border-b-0">
                          <th scope="row" className="whitespace-nowrap px-6 py-3 text-left">
                            <Link
                              href={`/tickets/${ticket.id}`}
                              className="u-transition figure t-meta text-ink underline decoration-1 underline-offset-2 hover:text-accent"
                            >
                              {ticket.serial}
                            </Link>
                          </th>
                          <td className="t-meta px-6 py-3 text-ink">{event?.name ?? "—"}</td>
                          <td className="t-meta px-6 py-3 text-muted">{tier?.name ?? "—"}</td>
                          <td className="figure t-meta whitespace-nowrap px-6 py-3 text-right text-ink">
                            {formatSol(ticket.faceValueLamports)}
                          </td>
                          <td className="px-6 py-3">
                            <Chip tone={status.tone}>{status.label}</Chip>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}
    </div>
  );
}

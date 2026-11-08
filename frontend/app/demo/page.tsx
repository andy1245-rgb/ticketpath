"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, Chip, Rule } from "@/components/ui";
import { BuyerView } from "@/components/demo/BuyerView";
import { OrganiserView } from "@/components/demo/OrganiserView";
import { RoleToggle } from "@/components/RoleToggle";
import { getRole, subscribeRole, type Role } from "@/lib/roleStore";
import artefact from "@/data/devnet-artefacts.json";
import { shortAddress } from "@/lib/format";
import {
  applyListing,
  ceilingFor,
  defaultState,
  evaluateListing,
  lawReasonSentence,
  loadState,
  mintTicket,
  saveState,
  sol,
  type DemoState,
  type EventConfig,
  type ListingOutcome,
} from "@/lib/demoState";

/**
 * The recorded devnet legs, read from `data/devnet-artefacts.json` at build
 * time. It used to be five hand-typed constants, which is a copy that can drift
 * from the record it claims to quote without anything failing: the file is the
 * source, so the file is what is read.
 */
const ACCEPTED = artefact.transfers.acceptedAtCap;
const REFUSED = artefact.transfers.refusedOverCap;

/**
 * The buyer journey as five labelled steps. The current step is derived from
 * the demo store, not stored. The wallet step is a stand-in: the demo issues a
 * synthetic address and connects nothing.
 */
function JourneyStepper({
  role,
  ticketCount,
  resold,
  refused,
}: {
  role: Role;
  ticketCount: number;
  resold: boolean;
  refused: boolean;
}) {
  const steps = [
    { n: 1, label: "Wallet", note: "SIMULATED: synthetic address, nothing connects" },
    { n: 2, label: "Buy", note: "Mint a demo ticket at face" },
    { n: 3, label: "Receipt", note: "Fee, flip tax and cap arithmetic" },
    { n: 4, label: "Resell", note: refused ? "Refused above the cap (6010)" : "Try at, then over, the cap" },
    { n: 5, label: "History", note: "Hops on the ticket, and in My tickets" },
  ];
  const current = ticketCount === 0 ? 2 : resold ? 5 : refused ? 4 : 3;
  return (
    <nav aria-label="Buyer journey" className="mt-6">
      <ol className="grid gap-2 sm:grid-cols-5">
        {steps.map((step) => {
          const done = role === "buyer" && step.n < current;
          const active = role === "buyer" && step.n === current;
          return (
            <li
              key={step.n}
              aria-current={active ? "step" : undefined}
              className={`rounded-md border px-3 py-2 ${active ? "border-accent bg-surface" : "border-line"}`}
            >
              <p className={`t-micro-caps ${active ? "text-accent" : "text-muted"}`}>
                {step.n}. {step.label}
                {done ? " (done)" : ""}
              </p>
              <p className="t-micro mt-1 text-muted">{step.note}</p>
            </li>
          );
        })}
      </ol>
      <p className="t-micro mt-3 text-muted">
        What this demo simulates: wallet, payment and settlement run in this browser against a
        transcription of the rules. Only the cap predicate is enforced on chain, by the v1 program
        on devnet. Fee and flip tax are paid by the seller in the sale in this app; region rules and
        bans are app policy. See{" "}
        <Link href="/my-tickets" className="text-accent underline underline-offset-2">
          My tickets
        </Link>{" "}
        for what you hold.
      </p>
    </nav>
  );
}

export default function DemoPage() {
  const [mounted, setMounted] = useState(false);
  const [role, setLocalRole] = useState<Role>("buyer");
  const [state, setState] = useState<DemoState>(defaultState);
  const [outcome, setOutcome] = useState<
    { ticketId: string; priceLamports: number; result: ListingOutcome } | null
  >(null);

  useEffect(() => {
    setMounted(true);
    setLocalRole(getRole());
    setState(loadState());
    return subscribeRole(setLocalRole);
  }, []);

  useEffect(() => {
    if (mounted) saveState(state);
  }, [mounted, state]);

  const ceiling = useMemo(() => ceilingFor(state.event), [state.event]);
  const lawSentence = useMemo(() => lawReasonSentence(ceiling.row), [ceiling.row]);

  function buy() {
    setOutcome(null);
    setState((current) => mintTicket(current, Date.now()));
  }

  function list(ticketId: string, priceLamports: number) {
    const ticket = state.tickets.find((t) => t.id === ticketId);
    if (!ticket) return;
    const now = Date.now();
    const result = evaluateListing({ event: state.event, ticket, priceLamports, nowMs: now });
    setOutcome({ ticketId, priceLamports, result });
    if (result.ok) setState((current) => applyListing(current, ticketId, priceLamports, now));
  }

  function patchEvent(patch: Partial<EventConfig>) {
    setOutcome(null);
    setState((current) => ({ ...current, event: { ...current.event, ...patch } }));
  }

  function reset() {
    setOutcome(null);
    setState((current) => ({ ...current, tickets: [] }));
  }

  function resetEvent() {
    setOutcome(null);
    setState(defaultState());
  }

  if (!mounted) {
    return (
      <div className="box py-16">
        <p className="t-body text-muted" role="status">
          Loading the demo state from this browser… This page is a simulation that runs in your
          browser; it needs JavaScript and localStorage, and nothing is sent anywhere.
        </p>
        <noscript>
          <p className="t-body mt-2 text-ink">JavaScript is required for the demo. See /rules for the written proof.</p>
        </noscript>
      </div>
    );
  }

  return (
    <div className="box py-10">
      <header className="flex flex-wrap items-start justify-between gap-6">
        <div>
          <p className="t-micro-caps text-muted">Live demo</p>
          <h1 className="h-display mt-2 text-ink">SeatPass, both sides of the resale</h1>
          <p className="t-deck mt-3 max-w-[70ch] text-muted">
            Buy a ticket, try to flip it, and watch the cap decide. Then switch to the organiser
            and change the event underneath the buyer: the face price, the cap, the resale mode,
            the jurisdiction (a policy table, not enforced on chain), the artist fee and the flip tax. Every
            number here is computed in this browser by a transcription of the repository&rsquo;s
            rules, not by the chain.
          </p>
        </div>
        <div className="grid justify-items-end gap-3">
          <RoleToggle />
          <button
            type="button"
            onClick={reset}
            className="u-transition t-meta text-muted underline-offset-4 hover:text-ink hover:underline"
          >
            Reset demo: clear my tickets
          </button>
          <button
            type="button"
            onClick={resetEvent}
            className="u-transition t-meta text-muted underline-offset-4 hover:text-ink hover:underline"
          >
            Reset the event to defaults
          </button>
        </div>
      </header>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <Chip>SIMULATED DEMO IN YOUR BROWSER</Chip>
        <p className="t-meta text-muted">
          Nothing here is on chain and nothing leaves this tab. State is in{" "}
          <span className="text-ink">localStorage</span>, so a reload keeps your tickets.
        </p>
      </div>

      <JourneyStepper
        role={role}
        ticketCount={state.tickets.length}
        resold={state.tickets.some((t) => t.hops.length > 1)}
        refused={outcome !== null && !outcome.result.ok}
      />

      <Rule className="my-8" />

      {role === "buyer" ? (
        <BuyerView
          state={state}
          closed={ceiling.closed}
          capBps={ceiling.capBps}
          ceilingLamports={ceiling.ceilingLamports}
          binding={ceiling.binding}
          lawSentence={lawSentence}
          outcome={outcome}
          onBuy={buy}
          onList={list}
        />
      ) : (
        <OrganiserView event={state.event} ceiling={ceiling} onChange={patchEvent} />
      )}

      <Rule className="my-10" />

      <Card>
        <h2 className="h-section text-ink">The refusal is the real code</h2>
        <p className="t-body mt-3 max-w-[76ch] text-muted">
          This page simulates the environment. The cap is the one rule the chain enforces, and only in v1; the artist fee and flip tax here are a browser transcription that v1 does not carry, and region and hold-clock rules belong to the v2 program, not v1. The v1 cap program is deployed on
          Solana devnet, and its record carries both legs: one resale at exactly the ceiling that
          was admitted, and one lamport higher that the program refused.
        </p>
        <dl className="mt-4 grid gap-2">
          <div>
            <dt className="t-micro-caps text-muted">program v1</dt>
            <dd className="mt-1">
              <a
                href={artefact.explorer.program}
                target="_blank"
                rel="noopener noreferrer"
                title={artefact.programId}
                className="figure t-meta u-transition text-accent underline underline-offset-2 hover:text-accent-press"
              >
                {shortAddress(artefact.programId, 8, 8)}
              </a>
            </dd>
          </div>
          <div>
            <dt className="t-micro-caps text-muted">program v2 (region and hold-clock rules; recorded legs are v1)</dt>
            <dd className="figure t-meta mt-1 text-ink break-all">Bebo55oe4VRmzYKoaHMH72bg4zLFKvLpnLRc5Nh9jPmF</dd>
          </div>
          <div>
            <dt className="t-micro-caps text-muted">the two legs</dt>
            <dd className="figure t-meta mt-1 text-ink">
              admitted {sol(ACCEPTED.priceLamports)} in{" "}
              <a
                href={ACCEPTED.explorer}
                target="_blank"
                rel="noopener noreferrer"
                title={ACCEPTED.signature}
                className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
              >
                {shortAddress(ACCEPTED.signature ?? null, 8, 8)}
              </a>{" "}
              (slot {ACCEPTED.slot?.toLocaleString("en-US") ?? "—"})
            </dd>
          </div>
          <div>
            <dt className="t-micro-caps text-muted">the refusal</dt>
            <dd className="figure t-meta mt-1 text-ink">
              refused {sol(REFUSED.priceLamports)} with{" "}
              <code className="rounded bg-inset px-1 py-0.5">{REFUSED.error}</code> in{" "}
              <a
                href={REFUSED.explorer}
                target="_blank"
                rel="noopener noreferrer"
                title={REFUSED.signature}
                className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
              >
                {shortAddress(REFUSED.signature ?? null, 8, 8)}
              </a>{" "}
              (slot {REFUSED.slot?.toLocaleString("en-US") ?? "—"})
            </dd>
          </div>
        </dl>
        <p className="t-body mt-4 text-muted">
          Both signatures open the transaction on the Solana explorer, so the refusal can be read
          from the cluster rather than from this page.
        </p>
        <p className="t-body mt-4">
          <Link
            href="/rules#enforcement-today"
            className="text-accent underline-offset-4 hover:underline"
          >
            The recorded devnet proof is on the rules page
          </Link>
        </p>
      </Card>
    </div>
  );
}

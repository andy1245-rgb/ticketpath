"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { Card, Chip, Rule } from "@/components/ui";
import { BuyerView } from "@/components/demo/BuyerView";
import { OrganiserView } from "@/components/demo/OrganiserView";
import { RoleToggle } from "@/components/RoleToggle";
import { getRole, subscribeRole, type Role } from "@/lib/roleStore";
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

/** The recorded devnet leg that was refused, from `records/devnet-artefacts.json`. */
const DEVNET_PROOF = {
  programId: "5EJ1GU3M4vn1vGCataH3sfMjQEMnom5Q3sDHJDhs4eva",
  acceptedLamports: 1_250_000_000,
  refusedLamports: 1_250_000_001,
  error: "custom program error: 0x177a (6010 E_CAP_EXCEEDED)",
  slot: 519_846_008,
};

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

  if (!mounted) {
    return (
      <div className="box py-16">
        <p className="t-body text-muted">Loading the demo state from this browser…</p>
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
            the jurisdiction, the artist fee and the flip tax. Every number here is computed in
            this browser from the same rules the repository ships.
          </p>
        </div>
        <div className="grid justify-items-end gap-3">
          <RoleToggle />
          <button
            type="button"
            onClick={reset}
            className="u-transition t-meta text-muted underline-offset-4 hover:text-ink hover:underline"
          >
            Clear tickets
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

      <Rule className="my-8" />

      {role === "buyer" ? (
        <BuyerView
          state={state}

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
          This page simulates the environment, not the rule. The cap program is deployed on solana
          devnet, and its record carries both legs: one resale at exactly the ceiling that was
          admitted, and one lamport higher that the program refused.
        </p>
        <div className="mt-4 grid gap-2">
          <p className="t-meta text-muted">program {DEVNET_PROOF.programId}</p>
          <p className="t-meta text-muted">
            admitted {sol(DEVNET_PROOF.acceptedLamports)} · refused{" "}
            {sol(DEVNET_PROOF.refusedLamports)} with {DEVNET_PROOF.error} · slot{" "}
            {DEVNET_PROOF.slot}
          </p>
        </div>
        <p className="t-body mt-4">
          <Link href="/rules" className="text-accent underline-offset-4 hover:underline">
            The recorded devnet proof is on the rules page
          </Link>
        </p>
      </Card>
    </div>
  );
}

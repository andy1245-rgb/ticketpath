"use client";

import { useState } from "react";
import { Card, Chip, Perforation, Rule } from "@/components/ui";
import {
  bpsLabel,
  sol,
  type DemoState,
  type ListingOutcome,
} from "@/lib/demoState";

type Props = {
  state: DemoState;
  capBps: number;
  ceilingLamports: number;
  binding: "law" | "platform";
  lawSentence: string;
  outcome: { ticketId: string; priceLamports: number; result: ListingOutcome } | null;
  onBuy: () => void;
  onList: (ticketId: string, priceLamports: number) => void;
};

function PriceInput({ ticketId, onList }: { ticketId: string; onList: (id: string, lamports: number) => void }) {
  const [value, setValue] = useState("1.3");
  return (
    <form
      className="flex flex-wrap items-end gap-2"
      onSubmit={(event) => {
        event.preventDefault();
        const parsed = Number(value);
        onList(ticketId, Number.isFinite(parsed) ? Math.round(parsed * 1_000_000_000) : 0);
      }}
    >
      <label className="flex flex-col gap-1">
        <span className="t-meta text-muted">Your resale price, SOL</span>
        <input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          inputMode="decimal"
          className="h-11 w-36 rounded-card border border-line bg-inset px-3 t-body text-ink"
        />
      </label>
      <button
        type="submit"
        className="u-transition inline-flex h-11 items-center rounded-pill border border-accent bg-accent px-5 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
      >
        List it
      </button>
    </form>
  );
}

export function BuyerView(props: Props) {
  const { state, capBps, ceilingLamports, binding, lawSentence, outcome, onBuy, onList } = props;
  const { event, tickets } = state;

  return (
    <div className="grid gap-8 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section aria-labelledby="buyer-title" className="grid gap-6">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <h2 id="buyer-title" className="h-section text-ink">
              Buyer
            </h2>
            <p className="t-deck mt-2 max-w-[62ch] text-muted">
              Buy at face, then try to resell it. The price you type is checked against the same
              predicate the contract evaluates, in this browser, before any hop is recorded.
            </p>
          </div>
          <button
            type="button"
            onClick={onBuy}
            className="u-transition inline-flex h-11 items-center rounded-pill border border-accent bg-accent px-5 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
          >
            Buy a ticket at {sol(event.faceLamports)}
          </button>
        </div>

        {tickets.length === 0 ? (
          <Card>
            <p className="t-body text-ink">No tickets yet.</p>
            <p className="t-body mt-2 text-muted">
              Buy one and it is issued to the demo wallet at the face price, with one custody hop.
              Nothing leaves this browser and no money moves.
            </p>
          </Card>
        ) : null}

        {tickets.map((ticket) => (
          <Card key={ticket.id}>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="t-meta text-muted">Ticket {ticket.serial}</p>
                <p className="t-body mt-1 text-ink">
                  {ticket.tier} · face {sol(event.faceLamports)}
                </p>
              </div>
              <Chip>{ticket.hops.length} hop{ticket.hops.length === 1 ? "" : "s"}</Chip>
            </div>

            <Rule className="my-4" />

            <div className="flex flex-wrap items-end justify-between gap-4">
              <PriceInput ticketId={ticket.id} onList={onList} />
              <p className="t-meta text-muted">
                Ceiling {sol(ceilingLamports)} ({bpsLabel(capBps)} over face, {binding} binds)
              </p>
            </div>

            <Rule className="my-4" />

            <h3 className="t-meta text-muted">Custody hops</h3>
            <table className="mt-2 w-full text-left">
              <thead>
                <tr className="t-meta text-muted">
                  <th className="py-1 font-medium">#</th>
                  <th className="py-1 font-medium">Price</th>
                  <th className="py-1 font-medium">Wallet</th>
                  <th className="py-1 font-medium">Time</th>
                </tr>
              </thead>
              <tbody>
                {ticket.hops.map((hop, index) => (
                  <tr key={`${ticket.id}-${index}`} className="border-t border-line">
                    <td className="py-2 t-body text-muted">{index + 1}</td>
                    <td className="py-2 t-body u-num text-ink">{sol(hop.priceLamports)}</td>
                    <td className="py-2 t-meta text-muted">
                      {hop.wallet.slice(0, 6)}…{hop.wallet.slice(-4)}
                    </td>
                    <td className="py-2 t-meta text-muted">{hop.at.replace("T", " ").slice(0, 19)}Z</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="t-meta mt-3 text-muted">
              Every hop is a price, a wallet and an instant. On the platform each one is a ledger
              entry; here it is a row in your own browser.
            </p>
          </Card>
        ))}
      </section>

      <aside className="grid gap-6 self-start" aria-labelledby="rule-title">
        <h2 id="rule-title" className="h-section text-ink">
          What the rule said
        </h2>
        <Card>
          <p className="t-meta text-muted">Face</p>
          <p className="t-body u-num text-ink">{sol(event.faceLamports)}</p>
          <Rule className="my-3" />
          <p className="t-meta text-muted">Cap admitted</p>
          <p className="t-body u-num text-ink">{bpsLabel(capBps)} over face</p>
          <p className="t-meta mt-1 text-muted">{binding} binds · {event.region}</p>
          <p className="t-body mt-3 text-muted">{lawSentence}</p>
          <Rule className="my-3" />
          <p className="t-meta text-muted">Resale mode</p>
          <p className="t-body text-ink">{event.resaleMode}</p>
        </Card>

        {outcome && !outcome.result.ok ? (
          <Card>
            <Chip>Refused</Chip>
            <p className="h-section mt-3 text-ink">{outcome.result.title}</p>
            <p className="t-meta mt-2 break-words text-muted">{outcome.result.detail}</p>
            <p className="t-body mt-3 text-muted">
              Computed in this browser from the same predicate the contract runs. The code is the
              one the devnet program returned for the same breach.
            </p>
          </Card>
        ) : null}

        {outcome && outcome.result.ok ? (
          <Card>
            <Chip>Admitted</Chip>
            <p className="h-section mt-3 text-ink">Listed at {sol(outcome.priceLamports)}</p>
            <p className="t-body mt-2 text-muted">
              Flip tax at this hold: {bpsLabel(outcome.result.taxBps)} ={" "}
              {sol(outcome.result.taxLamports)}. Artist fee: {sol(outcome.result.feeLamports)}.
            </p>
            <Perforation className="my-4" width={300} />
            <p className="t-meta text-muted">
              Tax and fee are computed and shown, not charged. No money moves in a demo.
            </p>
          </Card>
        ) : null}
      </aside>
    </div>
  );
}

"use client";

import { useEffect, useRef, useState } from "react";
import { Card, Chip, Perforation, Rule } from "@/components/ui";
import {
  bpsLabel,
  buyerSummary,
  ceilingFor,
  sol,
  SOL,
  type DemoState,
  type ListingOutcome,
} from "@/lib/demoState";

type Outcome = { ticketId: string; priceLamports: number; result: ListingOutcome };

type Props = {
  state: DemoState;
  /** Set when resale cannot be listed at any price (BANNED, or an unresolved region law). */
  closed: { code: string; reason: string } | null;
  capBps: number;
  ceilingLamports: number;
  binding: "law" | "platform";
  lawSentence: string;
  outcome: Outcome | null;
  onBuy: () => void;
  onList: (ticketId: string, priceLamports: number) => void;
};

function PriceInput({
  ticketId,
  ceilingLamports,
  onList,
}: {
  ticketId: string;
  ceilingLamports: number;
  onList: (id: string, lamports: number) => void;
}) {
  // The form opens at the ceiling, not above it. At a 1 SOL face and the platform's
  // 2500 bps the ceiling is 1.25 SOL, so a prefilled 1.3 refuses the first click and the
  // admitted path is never seen. At the ceiling the first click demonstrates admission
  // and the refusal is the deliberate second click.
  //
  // `String(lamports / SOL)` keeps the prefill round-tripping through `Math.round` below,
  // which is what the predicate reads. The display formatter rounds (to 4 dp here), and a
  // rounded-up prefill would open one lamport above the ceiling it is supposed to sit on.
  const [value, setValue] = useState(() => String(ceilingLamports / SOL));
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

/**
 * The verdict card, rendered once above the grid for phones and once in the aside for
 * desktop. It holds no ids, because the same card appears twice in the tree and the
 * aside's `aria-labelledby` must stay unique.
 */
function OutcomeCard({ outcome, state }: { outcome: Outcome; state: DemoState }) {
  if (outcome.result.ok) {
    return (
      <Card>
        <Chip>Admitted</Chip>
        <p className="h-section mt-3 text-ink">Listed at {sol(outcome.priceLamports)}</p>
        <dl className="t-body mt-3 grid grid-cols-[1fr_auto] gap-x-4 gap-y-1">
          <dt className="text-muted">Sale price</dt>
          <dd className="u-num text-ink">{sol(outcome.priceLamports)}</dd>
          <dt className="text-muted">Flip tax at this hold ({bpsLabel(outcome.result.taxBps)}), seller-paid</dt>
          <dd className="u-num text-ink">- {sol(outcome.result.taxLamports)}</dd>
          <dt className="text-muted">Artist fee, seller-paid</dt>
          <dd className="u-num text-ink">
            {state.event.artistFee.on ? `- ${sol(outcome.result.feeLamports)}` : "off"}
          </dd>
          <dt className="text-ink">Seller receives</dt>
          <dd className="u-num text-ink">
            {sol(outcome.priceLamports - outcome.result.taxLamports - outcome.result.feeLamports)}
          </dd>
        </dl>
        <p className="t-meta mt-2 text-muted">
          Cap check passed: {outcome.priceLamports} x 10000 = {outcome.priceLamports * 10_000} is at
          most {state.event.faceLamports} x (10000 + {outcome.result.ceiling.capBps}) ={" "}
          {state.event.faceLamports * (10_000 + outcome.result.ceiling.capBps)}. The tax (15 percent
          falling to 0 over 30 days) and the fee are lamport legs in the same transaction.
        </p>
        <Perforation className="my-4" width={300} />
        <p className="t-meta text-muted">
          Tax and fee are computed and shown, not charged. No money moves in a demo.
        </p>
      </Card>
    );
  }

  // Only a cap breach is the code the devnet program returned. BAD_PRICE, LAW_UNRESOLVED
  // and RESALE_DISABLED are refused by this page before any cap arithmetic runs, so the
  // chain never saw them and they must not borrow 6010's provenance.
  const capBreach = outcome.result.code === "E_CAP_EXCEEDED";

  return (
    <Card className="refusal-card">
      <Chip>Refused</Chip>
      <p className="h-section mt-3 text-ink">{outcome.result.title}</p>
      <p className="refusal-card__eq figure t-meta mt-3 break-words text-ink">{outcome.result.detail}</p>
      {capBreach ? (
        <p className="t-meta mt-3 text-muted">
          Same rule as the program: computed in this browser from the same predicate the contract
          runs. The code is the one the devnet program returned for the same breach.
        </p>
      ) : (
        <p className="t-body mt-3 text-muted">
          This is refused before any arithmetic; the chain was never asked.
        </p>
      )}
    </Card>
  );
}

export function BuyerView(props: Props) {
  const { state, closed, capBps, ceilingLamports, binding, lawSentence, outcome, onBuy, onList } = props;
  const { event, tickets } = state;
  const mobileOutcome = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!outcome) return;
    // On a phone the listing form sits below the fold. Bring the verdict it just produced
    // into view instead of leaving it above the viewport. The desktop copy lives in the
    // aside, and this block is `display: none` at that width, so the call does nothing there.
    mobileOutcome.current?.scrollIntoView({ block: "nearest", behavior: "smooth" });
  }, [outcome]);

  return (
    <div>
      {outcome ? (
        <div ref={mobileOutcome} aria-live="polite" className="scroll-mt-20 lg:hidden">
          <div className="mb-8">
            <OutcomeCard outcome={outcome} state={state} />
          </div>
        </div>
      ) : null}

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
            <Card key={ticket.id} className="ticket-card">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="t-micro-caps text-muted">{event.name}</p>
                  <p className="h-section mt-1 text-ink">
                    {ticket.tier} <span className="figure text-muted">{ticket.serial}</span>
                  </p>
                  <p className="t-meta mt-1 text-muted">
                    Face <span className="figure text-ink">{sol(event.faceLamports)}</span>
                  </p>
                </div>
                <Chip>
                  {ticket.hops.length > 1 ? "RESOLD" : "ISSUED"} · {ticket.hops.length} hop
                  {ticket.hops.length === 1 ? "" : "s"}
                </Chip>
              </div>

              <Perforation className="my-4" width={300} />

              <Rule className="my-4" />

              {event.ticketOverrides?.[ticket.serial]?.frozen ? (
                <div className="mb-4" role="status">
                  <Chip>TICKET FROZEN</Chip>
                  <p className="t-body mt-2 text-ink">
                    The organiser froze resale of ticket {ticket.serial}. Any listing will be refused
                    (TICKET_FROZEN), whatever the price. App policy in this demo, not a chain rule.
                  </p>
                </div>
              ) : event.ticketOverrides?.[ticket.serial]?.maxLamports != null ? (
                <p className="t-meta mb-4 text-muted" role="status">
                  Organiser maximum for ticket {ticket.serial}:{" "}
                  {sol(event.ticketOverrides[ticket.serial].maxLamports as number)}. A higher price is
                  refused (TICKET_MAX_EXCEEDED), even below the cap. App policy, not a chain rule.
                </p>
              ) : null}
              {closed ? (
                <div className="mb-4" role="status">
                  <Chip>{closed.code === "RESALE_DISABLED" ? "RESALE BANNED" : "RESALE LOCKED"}</Chip>
                  <p className="t-body mt-2 text-ink">
                    {closed.code === "RESALE_DISABLED"
                      ? "You cannot list this ticket: the organiser set resale to BANNED for this event. This is a policy switch, not a price cap, so no price would be accepted."
                      : `You cannot list this ticket: the region rule here is unresolved or forbids resale (${closed.reason}) This is a jurisdiction lock, not a price cap.`}
                  </p>
                </div>
              ) : null}
              <div className="flex flex-wrap items-end justify-between gap-4">
                <PriceInput
                  ticketId={ticket.id}
                  ceilingLamports={ceilingLamports}
                  onList={onList}
                />
                <p className="t-meta text-muted">
                  Ceiling {sol(ceilingLamports)} ({bpsLabel(capBps)} over face, {binding} binds)
                </p>
              </div>

              <Rule className="my-4" />

              <h3 className="t-meta text-muted">Custody hops</h3>
              <ol className="hop-timeline mt-3">
                {ticket.hops.map((hop, index) => (
                  <li key={`${ticket.id}-${index}`} className="hop-timeline__item">
                    <span className="hop-timeline__dot" aria-hidden="true" />
                    <div className="flex flex-wrap items-baseline justify-between gap-x-4">
                      <span className="t-body u-num text-ink">
                        {index + 1}. {sol(hop.priceLamports)}
                      </span>
                      <span className="t-meta text-muted">
                        {hop.at.replace("T", " ").slice(0, 19)}Z
                      </span>
                    </div>
                    <p className="figure t-meta text-muted">
                      to {hop.wallet.slice(0, 6)}…{hop.wallet.slice(-4)}
                    </p>
                  </li>
                ))}
              </ol>
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
            <p className="t-meta text-muted">What you can do on this event</p>
            <ul className="t-body mt-2 grid gap-2 text-ink">
              {buyerSummary(event, ceilingFor(event)).map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </Card>
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
            <p className="t-body text-ink">{event.resaleMode.toUpperCase()}</p>
          </Card>

          {outcome ? (
            <div className="hidden lg:block">
              <OutcomeCard outcome={outcome} state={state} />
            </div>
          ) : null}
        </aside>
      </div>
    </div>
  );
}

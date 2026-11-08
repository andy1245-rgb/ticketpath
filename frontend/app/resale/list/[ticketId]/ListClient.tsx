"use client";

import { useId, useState } from "react";
import { Chip, Panel, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";
import { isWithinCap, maxResaleLamports } from "@/lib/cap";
import { LAMPORTS_PER_SOL, formatLamports, formatSol } from "@/lib/format";
import type { Event, Ticket } from "@/lib/types";

/**
 * The price field. It is the only piece of this screen that has to be live, so
 * it is the only piece that is a client component: the ticket and its event
 * arrive already read from the server.
 *
 * Lamports are the unit the contract counts in, so the integer is what the
 * state holds and what every comparison uses. The string is the input's own
 * text and nothing else; it is converted once per keystroke and rounded to a
 * whole lamport, so no float ever reaches `isWithinCap`.
 */

/** A decimal SOL string to whole lamports, or null while it is not one yet. */
function lamportsFromSol(text: string): number | null {
  const trimmed = text.trim();
  if (trimmed === "" || trimmed === "." || !/^\d*\.?\d*$/.test(trimmed)) return null;
  const sol = Number(trimmed);
  if (!Number.isFinite(sol) || sol < 0) return null;
  // One multiplication and one rounding: 1e9 lamports to the SOL.
  return Math.round(sol * LAMPORTS_PER_SOL);
}

interface PriceState {
  /** The input's text, exactly as typed. */
  sol: string;
  /** The same price as a whole number of lamports, or null when unreadable. */
  lamports: number | null;
}

export function ListClient({ ticket, event }: { ticket: Ticket; event: Event }) {
  const [price, setPrice] = useState<PriceState>({ sol: "", lamports: null });

  const baseId = useId();
  const priceId = `${baseId}-price`;
  const capId = `${baseId}-cap`;
  const warnId = `${baseId}-warn`;

  /*
   * The ceiling, in the order the record sources it:
   *   1. the event's resolved enforced cap (law tightened against the platform
   *      cap) — the number the contract would actually admit against;
   *   2. the matching `enforcedCapByTier` row, because the cap is a multiple of
   *      each tier's own face value, not of a single event-wide face;
   *   3. the ticket's own rule from lib/cap.ts, which returns null when the
   *      event sets no cap at all.
   * A null from every source means uncapped, and the field says so.
   */
  const tierCap = event.enforcedCapByTier?.find((row) => row.tierId === ticket.tierId) ?? null;
  const ceilingLamports: number | null =
    event.enforcedCap?.enforcedCeilingLamports ??
    tierCap?.enforcedCeilingLamports ??
    maxResaleLamports({
      faceValueLamports: ticket.faceValueLamports,
      resalePriceCapBps: event.resalePriceCapBps,
    });

  /*
   * `isWithinCap` wants basis points, so the ceiling is expressed in bps over
   * this ticket's own face. Rounded up, so the ceiling itself always passes the
   * predicate; the exact integer ceiling is checked beside it, which is what
   * stops a price a few lamports over from slipping through on the rounding.
   */
  const capBps =
    ceilingLamports == null || ticket.faceValueLamports <= 0
      ? null
      : Math.ceil(
          ((ceilingLamports - ticket.faceValueLamports) * 10_000) / ticket.faceValueLamports,
        );

  const { lamports } = price;
  const overCeiling =
    ceilingLamports != null && lamports != null && lamports > ceilingLamports;
  const outsideCap =
    capBps != null &&
    lamports != null &&
    !isWithinCap(lamports, ticket.faceValueLamports, capBps);
  const overCap = overCeiling || outsideCap;

  return (
    <div className="mt-12">
      <section aria-labelledby={`${baseId}-set-price`}>
        <h2 id={`${baseId}-set-price`} className="h-section">
          Set the price
        </h2>

        <Panel className="mt-6 max-w-xl">
          {overCap && (
            <div id={warnId} className="mb-4 flex flex-wrap items-center gap-3">
              <Chip tone="warning">Above the cap</Chip>
              <p className="t-meta text-ink">
                The contract would refuse <span className="figure">{formatSol(lamports)}</span>. The
                ceiling for this ticket is{" "}
                <span className="figure">{formatSol(ceilingLamports)}</span>{" "}
                <span className="figure">({formatLamports(ceilingLamports)} lamports)</span>.
              </p>
            </div>
          )}

          <label htmlFor={priceId} className="t-micro-caps block text-muted">
            Price (SOL)
          </label>
          <input
            id={priceId}
            type="text"
            inputMode="decimal"
            autoComplete="off"
            spellCheck={false}
            value={price.sol}
            onChange={(changeEvent) =>
              setPrice({
                sol: changeEvent.target.value,
                lamports: lamportsFromSol(changeEvent.target.value),
              })
            }
            aria-describedby={overCap ? `${capId} ${warnId}` : capId}
            aria-invalid={overCap || undefined}
            className="figure t-body mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink"
          />

          <div id={capId} className="t-meta mt-3 text-muted">
            <p>
              Face value <span className="figure text-ink">{formatSol(ticket.faceValueLamports)}</span>.
            </p>
            {ceilingLamports == null ? (
              <p className="mt-1">
                Uncapped. This event sets no resale cap, so this field draws no cap rule and the
                ceiling does not apply.
              </p>
            ) : (
              <p className="mt-1">
                Ceiling <span className="figure text-ink">{formatSol(ceilingLamports)}</span>, which
                is exactly{" "}
                <span className="figure text-ink">
                  {formatLamports(ceilingLamports)} lamports
                </span>
                . The contract admits a price only when{" "}
                <span className="figure">price * 10000 &lt;= face * (10000 + cap_bps)</span>, and
                this ceiling is the enforced cap for this ticket.
              </p>
            )}
          </div>
        </Panel>
      </section>

      <div className="mt-12">
        <Unavailable capability={capabilities.listings} title="List this ticket" />
        <p className="t-body mt-4 max-w-3xl text-muted">
          {overCap
            ? "This price is over the cap, so the contract would refuse it. It would not leave this screen anyway: there is no endpoint behind this field and no success state is drawn."
            : "This price is checked against the rule as it is typed. It would not leave this screen: there is no endpoint behind this field and no success state is drawn."}
        </p>
      </div>
    </div>
  );
}

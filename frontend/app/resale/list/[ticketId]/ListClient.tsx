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

/**
 * The largest price this screen is willing to answer for.
 *
 * `isWithinCap` evaluates `price * 10000`, and above `Number.MAX_SAFE_INTEGER /
 * 10_000` lamports that multiplication stops being exact in a double: the digit
 * a comparison turns on is gone, and an absurd price can read as inside the cap.
 * Below this bound every integer in the product is exact, so the predicate's
 * answer is the contract's answer. The floor keeps the bound an integer, so the
 * comparison itself needs no rounding.
 */
const MAX_CHECKABLE_LAMPORTS = Math.floor(Number.MAX_SAFE_INTEGER / 10_000);

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

  /*
   * Three ways the field can fail to answer, and each one is visible.
   *
   * `unreadable` is text that is not a decimal amount at all (`abc`, `1..2`,
   * `.`): lamportsFromSol returned null, and before this the screen simply
   * rendered nothing while the field looked accepted.
   *
   * `tooLarge` is a number so big the cap arithmetic stops being exact, so no
   * answer here would be the contract's answer and none is offered.
   *
   * `checkableLamports` is what the cap predicate is actually run on, and it is
   * null in both of the above cases so neither can reach `isWithinCap`.
   */
  const unreadable = price.sol !== "" && lamports === null;
  const tooLarge = lamports !== null && lamports > MAX_CHECKABLE_LAMPORTS;
  const checkableLamports =
    lamports !== null && lamports <= MAX_CHECKABLE_LAMPORTS ? lamports : null;

  const overCeiling =
    ceilingLamports != null && checkableLamports != null && checkableLamports > ceilingLamports;
  const outsideCap =
    capBps != null &&
    checkableLamports != null &&
    !isWithinCap(checkableLamports, ticket.faceValueLamports, capBps);
  const overCap = overCeiling || outsideCap;
  const hasMessage = unreadable || tooLarge || overCap;

  return (
    <div className="mt-12">
      <section aria-labelledby={`${baseId}-set-price`}>
        <h2 id={`${baseId}-set-price`} className="h-section">
          Set the price
        </h2>

        <Panel className="mt-6 max-w-xl">
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
            aria-describedby={hasMessage ? `${capId} ${warnId}` : capId}
            aria-invalid={hasMessage || undefined}
            className="figure t-body mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink"
          />

          {/*
           * The messages sit below the field they describe, inside one live
           * region that is announced politely as it changes, and the region
           * holds its height whether or not a message is in it: a warning that
           * appeared above the input moved the field down the moment a typed
           * price crossed the ceiling, which is how a form eats a keystroke.
           * Each sentence is written to fit the reservation at this width, so a
           * message changes nothing about where the field sits.
           */}
          <div id={warnId} role="status" aria-live="polite" className="min-h-[6rem] pt-3">
            {unreadable && (
              <div className="flex flex-wrap items-center gap-3">
                <Chip tone="warning">Not a price</Chip>
                <p className="t-meta text-ink">
                  This field takes a decimal amount of SOL, so{" "}
                  <span className="figure">{price.sol}</span> is not a price and has not been
                  checked against the cap.
                </p>
              </div>
            )}

            {tooLarge && lamports !== null && (
              <div className="flex flex-wrap items-center gap-3">
                <Chip tone="warning">Too large to check</Chip>
                <p className="t-meta text-ink">
                  Above <span className="figure">{formatLamports(MAX_CHECKABLE_LAMPORTS)}</span>{" "}
                  lamports the cap check&apos;s multiplication by 10,000 stops being exact, so{" "}
                  <span className="figure">{formatLamports(lamports)}</span> is refused rather than
                  read as within the cap.
                </p>
              </div>
            )}

            {overCap && checkableLamports !== null && (
              <div className="flex flex-wrap items-center gap-3">
                <Chip tone="warning">Above the cap</Chip>
                <p className="t-meta text-ink">
                  The contract would refuse{" "}
                  <span className="figure">{formatSol(checkableLamports)}</span>, and the program
                  returns 6010 E_CAP_EXCEEDED. The ceiling for this ticket is{" "}
                  <span className="figure">{formatSol(ceilingLamports)}</span>{" "}
                  <span className="figure">({formatLamports(ceilingLamports)} lamports)</span>.
                </p>
              </div>
            )}
          </div>

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
            : tooLarge
              ? "This price is too large for the cap check to answer, so the screen does not claim it would pass. It would not leave this screen anyway: there is no endpoint behind this field."
              : unreadable
                ? "No price has been read, so no cap check has run. Nothing leaves this screen either way: there is no endpoint behind this field and no success state is drawn."
                : "This price is checked against the rule as it is typed. It would not leave this screen: there is no endpoint behind this field and no success state is drawn."}
        </p>

        {/* Seller economics. The two legs that would leave the same transaction
            are the artist fee and the flip tax, and neither exists on any record
            this screen reads, so no number is printed beside them. */}
        <div className="mt-6 max-w-3xl">
          <p className="t-micro-caps text-muted">What the seller receives</p>
          <p className="t-meta mt-1 text-muted">
            No fee field in any record, so this screen cannot say what a sale at a given price pays
            out: neither this ticket nor its event carries an artist fee or a flip tax, and no rate
            is invented here to stand in for one. The demo&apos;s organiser controls simulate both
            in the browser (a 15% flip tax falling to zero over 30 days), and no record stores a
            lamport of it.
          </p>
        </div>
      </div>
    </div>
  );
}

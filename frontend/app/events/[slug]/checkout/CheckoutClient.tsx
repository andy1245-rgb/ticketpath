"use client";

import { useEffect, useId, useState } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletButton } from "@/components/WalletButton";
import { Chip, Panel, Pill, Skeleton, Unavailable } from "@/components/ui";
import { ApiError, getWalletVerification } from "@/lib/api";
import { capabilities } from "@/lib/capabilities";
import { formatDateTime, formatSol } from "@/lib/format";
import type { TicketTier, WalletVerification } from "@/lib/types";

/**
 * The wallet half of checkout. It is a client component for one reason: the
 * connected wallet only exists in the browser. It reads the verification
 * result through lib/api like every server page does — no component fetches.
 *
 * Four states, and none of them is a success:
 *   NW  no wallet connected -> the connect control and one sentence
 *   UV  connected, verified false -> the flags array verbatim and /verify
 *   UN  the payment step -> the order summary, then one Unavailable panel; no
 *       control in it is live
 *   ER  the verification read failed -> its message and code, as returned
 *
 * The summary is a picture of what an order would contain, not an order: the
 * controls are inert because the endpoint that would take them does not exist,
 * and the text beneath them names it.
 */

/**
 * The quantity the summary prices. It is a fixed 1 because the input is
 * disabled: nothing on this screen can change the order, so the total is the
 * selected tier's face value times one and the arithmetic is shown beside it
 * rather than implied.
 */
const QUANTITY = 1;

type VerificationRead =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; verification: WalletVerification }
  | { kind: "error"; message: string; code: string };

export function CheckoutClient({
  requiresVerifiedWallet,
  tiers,
  venue,
  city,
  startsAt,
}: {
  requiresVerifiedWallet: boolean;
  /** Every tier on the event, read on the server and passed down as they are. */
  tiers: TicketTier[];
  /** The recap in the payment step: where and when the ticket is for. */
  venue: string;
  city: string;
  startsAt: string;
}): React.ReactElement {
  const { publicKey } = useWallet();
  const wallet = publicKey?.toBase58() ?? null;
  const [read, setRead] = useState<VerificationRead>({ kind: "idle" });

  const summaryId = useId();
  const tierFieldId = `${summaryId}-tier`;
  const quantityFieldId = `${summaryId}-quantity`;
  const whyId = `${summaryId}-why`;

  /*
   * The selected tier is the lowest one, which is also the "From" figure at the
   * top of the page: the select is disabled, so the selection cannot move, and
   * a disabled control that opened on a different tier would be a lie about
   * which price the total was computed from.
   */
  const selectedTier = tiers.reduce<TicketTier | null>(
    (lowest, tier) =>
      lowest === null || tier.faceValueLamports < lowest.faceValueLamports ? tier : lowest,
    null,
  );
  const totalLamports = selectedTier === null ? null : selectedTier.faceValueLamports * QUANTITY;

  useEffect(() => {
    if (wallet === null) {
      setRead({ kind: "idle" });
      return;
    }

    // A wallet switch mid-flight must not land its answer on the new wallet.
    let active = true;
    setRead({ kind: "loading" });

    getWalletVerification(wallet).then(
      (verification) => {
        if (active) setRead({ kind: "ready", verification });
      },
      (error: unknown) => {
        if (!active) return;
        setRead({
          kind: "error",
          message:
            error instanceof Error && error.message
              ? error.message
              : "The verification read failed.",
          code: error instanceof ApiError ? error.code : "unexpected_error",
        });
      },
    );

    return () => {
      active = false;
    };
  }, [wallet]);

  /** Everything the verification read has to say, once a wallet is connected. */
  function verificationResult(): React.ReactElement {
    if (read.kind === "idle" || read.kind === "loading") {
      return <Skeleton lines={2} />;
    }

    if (read.kind === "error") {
      return (
        <Panel>
          <p className="t-meta text-ink">The verification read failed.</p>
          <dl className="mt-4 space-y-4">
            <div>
              <dt className="t-micro-caps text-muted">Message</dt>
              <dd className="t-body mt-1 text-ink">{read.message}</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Code</dt>
              <dd className="figure t-meta mt-1 text-ink">{read.code}</dd>
            </div>
          </dl>
        </Panel>
      );
    }

    const verification = read.verification;

    if (verification.verified) {
      return (
        <Panel>
          <p className="t-body text-ink">This wallet is verified.</p>
          <dl className="mt-4 grid gap-4 sm:grid-cols-3">
            <div>
              <dt className="t-micro-caps text-muted">Verified at</dt>
              <dd className="figure t-meta mt-1 text-ink">{formatDateTime(verification.verifiedAt)}</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Method</dt>
              <dd className="figure t-meta mt-1 text-ink">{verification.method ?? "Not recorded"}</dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">flags</dt>
              <dd className="figure t-meta mt-1 text-ink">{JSON.stringify(verification.flags)}</dd>
            </div>
          </dl>
        </Panel>
      );
    }

    return (
      <Panel>
        <p className="t-body text-ink">This wallet is not verified.</p>
        <p className="t-meta mt-2 text-muted">
          {requiresVerifiedWallet
            ? "This event requires a verified wallet, and this one has not passed verification."
            : "This event does not require a verified wallet, but the verification read still returns false for this one."}
        </p>
        <dl className="mt-6">
          <dt className="t-micro-caps text-muted">flags</dt>
          <dd className="figure t-meta mt-1 text-ink">{JSON.stringify(verification.flags)}</dd>
        </dl>
        <div className="mt-6">
          <Pill href="/verify" variant="primary">
            Verify this wallet
          </Pill>
        </div>
      </Panel>
    );
  }

  return (
    <>
      <section aria-labelledby="wallet-heading">
        <h2 id="wallet-heading" className="h-section">
          Wallet verification
        </h2>

        <div className="mt-6">
          <WalletButton />
        </div>

        {wallet === null ? (
          <p className="t-body mt-4 text-ink">A wallet is required to continue.</p>
        ) : (
          <div className="mt-6">{verificationResult()}</div>
        )}
      </section>

      {/* The payment step: what an order would consist of, then the panel that
          says why none can be placed. The tier and quantity fields are the only
          controls and both are disabled, because a control that accepted a value
          would promise an endpoint that is not in the contract. */}
      <section className="mt-12" aria-label="Payment">
        <h3 className="h-section">What an order would contain</h3>

        <Panel className="mt-6">
          <div className="flex flex-wrap items-center gap-3">
            <Chip>Not an order</Chip>
            <p className="t-meta text-muted">
              Nothing on this panel can be submitted, and no number on it is a quote.
            </p>
          </div>

          <dl className="mt-6 grid gap-4 sm:grid-cols-2">
            <div>
              <dt className="t-micro-caps text-muted">Venue</dt>
              <dd className="t-meta mt-1 text-ink">
                {venue}, {city}
              </dd>
            </div>
            <div>
              <dt className="t-micro-caps text-muted">Starts</dt>
              <dd className="figure t-meta mt-1 text-ink">{formatDateTime(startsAt)}</dd>
            </div>
          </dl>

          <div className="mt-8 grid gap-6 sm:grid-cols-2">
            <div>
              <label htmlFor={tierFieldId} className="t-micro-caps block text-muted">
                Tier
              </label>
              <select
                id={tierFieldId}
                disabled
                defaultValue={selectedTier?.id ?? ""}
                aria-describedby={whyId}
                className="figure t-meta mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink disabled:cursor-not-allowed disabled:bg-inset disabled:text-muted"
              >
                {tiers.length === 0 ? (
                  <option value="">No tier in this record</option>
                ) : (
                  tiers.map((tier) => (
                    <option key={tier.id} value={tier.id}>
                      {tier.name} at {formatSol(tier.faceValueLamports)}
                    </option>
                  ))
                )}
              </select>
            </div>

            <div>
              <label htmlFor={quantityFieldId} className="t-micro-caps block text-muted">
                Quantity
              </label>
              <input
                id={quantityFieldId}
                type="number"
                min={1}
                value={QUANTITY}
                readOnly
                disabled
                aria-describedby={whyId}
                className="figure t-meta mt-2 h-12 w-full rounded-input border border-control bg-surface px-3 text-ink disabled:cursor-not-allowed disabled:bg-inset disabled:text-muted"
              />
            </div>
          </div>

          <p id={whyId} className="t-meta mt-3 max-w-3xl text-muted">
            Both controls are disabled because the contract has no purchase endpoint (
            <span className="figure">POST /api/tickets/:ticketId/purchase</span> is not in it),
            so there is nothing that would take a tier or a quantity from this screen.
          </p>

          <div className="mt-8">
            <p className="t-micro-caps text-muted">One ticket of each tier, at quantity 1</p>
            <dl className="mt-3 border-t border-line">
              {tiers.length === 0 ? (
                <div className="border-b border-line py-3">
                  <dt className="t-meta text-muted">No tier in this record</dt>
                </div>
              ) : (
                tiers.map((tier) => (
                  <div
                    key={tier.id}
                    className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1 border-b border-line py-3"
                  >
                    <dt className="t-meta text-ink">{tier.name}</dt>
                    <dd className="figure t-meta text-ink">
                      {formatSol(tier.faceValueLamports)}{" "}
                      <span className="t-micro text-muted">at quantity 1</span>
                    </dd>
                  </div>
                ))
              )}
            </dl>
          </div>

          <dl className="mt-6 border-t border-line pt-4">
            <div className="flex flex-wrap items-baseline justify-between gap-x-6 gap-y-1">
              <dt className="t-body text-ink">Total</dt>
              <dd className="figure t-body text-ink">{formatSol(totalLamports)}</dd>
            </div>
          </dl>
          <p className="t-micro mt-2 max-w-3xl text-muted">
            {selectedTier === null
              ? "No tier in this record, so there is no total to compute."
              : `Face value of ${selectedTier.name}, the selected tier, times quantity ${QUANTITY}.`}
          </p>

          <p className="t-meta mt-6 max-w-3xl text-muted">
            No fee field exists in any record: the event, the ticket and the ledger carry no buyer
            fee, no artist fee and no flip tax, so none is priced into this total. The demo&apos;s
            organiser controls simulate an artist fee and a flip tax in the browser, and no record
            stores either.
          </p>

          <div className="mt-6">
            <p className="t-micro-caps text-muted">After you pay</p>
            <p className="t-meta mt-1 max-w-3xl text-muted">
              Nothing. There is no payment step, no issuance step and no custody change behind this
              screen, so no money moves and no ticket reaches a wallet. The tickets this build shows
              come from its record; none of them was sold here.
            </p>
          </div>

          {/* The tier links elsewhere on the site carry a ?tier= id. Checkout is
              a fixed page with no server behind it, so it cannot read that id,
              and it says so rather than quietly showing a different tier. */}
          <p className="t-micro mt-6 max-w-3xl text-muted">
            The address can carry a tier id (<span className="figure">?tier=</span> then the id),
            but this page is built ahead of time and cannot read it, so the summary always shows
            the event&apos;s lowest tier.
          </p>
        </Panel>

        <div className="mt-12">
          <Unavailable capability={capabilities.purchase} title="Pay for this ticket" />
        </div>
      </section>
    </>
  );
}

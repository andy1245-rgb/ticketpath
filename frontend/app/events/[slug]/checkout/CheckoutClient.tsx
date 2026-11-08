"use client";

import { useEffect, useState } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { WalletButton } from "@/components/WalletButton";
import { Panel, Pill, Skeleton, Unavailable } from "@/components/ui";
import { ApiError, getWalletVerification } from "@/lib/api";
import { capabilities } from "@/lib/capabilities";
import { formatDateTime } from "@/lib/format";
import type { WalletVerification } from "@/lib/types";

/**
 * The wallet half of checkout. It is a client component for one reason: the
 * connected wallet only exists in the browser. It reads the verification
 * result through lib/api like every server page does — no component fetches.
 *
 * Four states, and none of them is a success:
 *   NW  no wallet connected -> the connect control and one sentence
 *   UV  connected, verified false -> the flags array verbatim and /verify
 *   UN  the payment step -> one Unavailable panel, never a disabled button
 *   ER  the verification read failed -> its message and code, as returned
 */

type VerificationRead =
  | { kind: "idle" }
  | { kind: "loading" }
  | { kind: "ready"; verification: WalletVerification }
  | { kind: "error"; message: string; code: string };

export function CheckoutClient({
  requiresVerifiedWallet,
}: {
  requiresVerifiedWallet: boolean;
}): React.ReactElement {
  const { publicKey } = useWallet();
  const wallet = publicKey?.toBase58() ?? null;
  const [read, setRead] = useState<VerificationRead>({ kind: "idle" });

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

      {/* The payment step is the Unavailable panel and nothing else: there is
          no purchase endpoint, so there is no control to sit here disabled. */}
      <section className="mt-12" aria-label="Payment">
        <Unavailable capability={capabilities.purchase} title="Pay for this ticket" />
      </section>
    </>
  );
}

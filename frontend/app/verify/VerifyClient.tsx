"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useWallet } from "@solana/wallet-adapter-react";
import {
  ApiError,
  completeWalletVerification,
  getWalletVerification,
  isMockMode,
  startWalletVerification,
} from "@/lib/api";
import type { WalletVerification } from "@/lib/types";
import { AddressPill } from "@/components/AddressPill";
import { WalletButton } from "@/components/WalletButton";
import { Chip, DataSourceNote, Skeleton } from "@/components/ui";
import { CLUSTER, toBase58, verificationMessage } from "@/lib/solana";
import { formatDateTime } from "@/lib/format";

/**
 * A nonce of the right shape, for the preview only: 32 hex characters, single
 * use, good for 300 seconds. The fixed lines and the cluster in the preview are
 * the bytes the wallet is asked to sign.
 */
const PLACEHOLDER_NONCE = "0123456789abcdef0123456789abcdef";

/** Anything that went wrong, reduced to what the panel prints. */
interface Failure {
  message: string;
  code: string;
  note: string;
}

/**
 * A failure keeps the backend's own message and code when there is one. A
 * wallet failure never has a backend code, and a request that never reached the
 * backend has no error body to quote, so both are labelled as what they are.
 *
 * `origin` is passed in by the call site: only the caller knows whether the
 * throw came from the wallet or from the seam.
 */
function toFailure(error: unknown, origin: "backend" | "wallet"): Failure {
  if (error instanceof ApiError) {
    return {
      message: error.message,
      code: error.code,
      note: "Read from the backend's {message, status, code} error body.",
    };
  }
  const message =
    error instanceof Error && error.message.trim() !== ""
      ? error.message
      : "The call failed without a message.";
  if (origin === "wallet") {
    if (/reject|denied|cancel|refus|declin/i.test(message)) {
      return {
        message:
          "The signature request was declined in the wallet. Nothing was sent to the backend.",
        code: "wallet_rejected",
        note: "Raised by the wallet in this browser. Nothing was sent to the backend.",
      };
    }
    return {
      message,
      code: "wallet_error",
      note: "Raised by the wallet in this browser. Nothing was sent to the backend.",
    };
  }
  return {
    message,
    code: "network_error",
    note: "The request to the backend failed before it answered, so there is no error body to quote.",
  };
}

function FailurePanel({ title, failure }: { title: string; failure: Failure }): React.ReactElement {
  return (
    <div role="alert" className="rounded-panel border border-danger bg-surface p-6">
      <Chip tone="danger">Failed</Chip>
      <h3 className="h-event mt-3 text-ink">{title}</h3>
      <dl className="mt-4 space-y-3">
        <div>
          <dt className="t-micro-caps text-muted">Message</dt>
          <dd className="t-body mt-1 text-ink">{failure.message}</dd>
        </div>
        <div>
          <dt className="t-micro-caps text-muted">Code</dt>
          <dd className="figure t-meta mt-1 text-ink">{failure.code}</dd>
        </div>
      </dl>
      <p className="t-micro mt-4 text-muted">{failure.note}</p>
    </div>
  );
}

function methodLabel(method: WalletVerification["method"]): string {
  if (method === "wallet_signature") return "Wallet signature";
  if (method === "identity") return "Identity document";
  return "None recorded";
}

/**
 * /verify: the same three calls as /account, on a screen of its own, for people
 * who were sent here by a transfer that wanted a verified destination.
 *
 * A success is only ever the record the backend returned. Nothing here reports
 * that a signature was accepted on the strength of the wallet's own reply.
 */
export function VerifyClient(): React.ReactElement {
  const { publicKey, signMessage } = useWallet();
  const wallet = publicKey?.toBase58() ?? null;

  const [verification, setVerification] = useState<WalletVerification | null>(null);
  const [readFailure, setReadFailure] = useState<Failure | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyFailure, setVerifyFailure] = useState<Failure | null>(null);

  // No separate loading flag: "no record and no failure" is the read in flight,
  // and a second flag would only let the two disagree for a frame.
  useEffect(() => {
    if (!wallet) {
      setVerification(null);
      setReadFailure(null);
      return;
    }
    let cancelled = false;
    setVerification(null);
    setReadFailure(null);
    setVerifyFailure(null);
    getWalletVerification(wallet)
      .then((result) => {
        if (cancelled) return;
        setVerification(result);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        setReadFailure(toFailure(error, "backend"));
      });
    return () => {
      cancelled = true;
    };
  }, [wallet]);

  /** Nonce from the backend, signature from the wallet, both back to the backend. */
  const verify = useCallback(async () => {
    if (!wallet) return;
    setVerifyFailure(null);
    if (!signMessage) {
      setVerifyFailure({
        message: "This wallet does not support signing a message. Try Phantom or Solflare.",
        code: "wallet_no_signing",
        note: "Raised by this page: the connected wallet exposes no message signing.",
      });
      return;
    }
    setVerifying(true);
    try {
      const challenge = await startWalletVerification(wallet);

      // Wrapped on its own so a declined prompt is reported as the wallet's
      // answer rather than as a backend failure.
      let signed: Uint8Array;
      try {
        signed = await signMessage(
          new TextEncoder().encode(verificationMessage(wallet, challenge.nonce)),
        );
      } catch (error) {
        setVerifyFailure(toFailure(error, "wallet"));
        return;
      }

      const result = await completeWalletVerification({
        wallet,
        nonce: challenge.nonce,
        signature: toBase58(signed),
      });
      setVerification(result);
      setReadFailure(null);
    } catch (error) {
      setVerifyFailure(toFailure(error, "backend"));
    } finally {
      setVerifying(false);
    }
  }, [wallet, signMessage]);

  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-3xl">
        <h1 className="h-display text-ink">Verify your wallet</h1>
        <p className="t-deck mt-4 text-muted">
          An event can require a verified wallet, and the contract only issues to, or accepts a
          transfer into, a wallet that has passed the signature check. No issuance and no transfer
          endpoint exists in this build, so nothing here is gated on it. The check, where it runs,
          proves you hold the key and moves no funds.
        </p>
        {isMockMode && (
          <p className="t-meta mt-4 text-muted">
            This deployment is a static build and has no backend, so it runs no signature check:
            nothing on this site can make a wallet a verified one. The screen says so below once a
            wallet is connected.
          </p>
        )}

        <section className="mt-12">
          <h2 className="h-section text-ink">Status</h2>

          {!wallet ? (
            <div className="mt-6 rounded-panel border border-line bg-surface p-6">
              <p className="t-body text-muted">Connect the wallet you want to verify.</p>
              <WalletButton className="mt-6" />
            </div>
          ) : readFailure ? (
            <div className="mt-6">
              <FailurePanel title="The verification read failed" failure={readFailure} />
            </div>
          ) : verification ? (
            <>
              <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
                <AddressPill address={wallet} />
                <Chip tone={verification.verified ? "positive" : "neutral"}>
                  {verification.verified ? "Verified" : "Not verified"}
                </Chip>
              </div>

              <dl className="mt-6 grid gap-x-6 gap-y-6 sm:grid-cols-2">
                  <div>
                    <dt className="t-micro-caps text-muted">Verified at</dt>
                    <dd className="figure t-meta mt-1 text-ink">
                      {formatDateTime(verification.verifiedAt)}
                    </dd>
                  </div>
                  <div>
                    <dt className="t-micro-caps text-muted">Method</dt>
                    <dd className="mt-1 flex flex-wrap items-baseline gap-x-3 gap-y-1">
                      <span className="t-meta text-ink">{methodLabel(verification.method)}</span>
                      <span className="figure t-micro text-muted">
                        {verification.method ?? "null"}
                      </span>
                    </dd>
                  </div>
                  <div>
                    <dt className="t-micro-caps text-muted">Can receive a transfer</dt>
                    <dd className="t-meta mt-1 text-ink">
                      {verification.canReceiveTransfer ? "Yes" : "No"}
                    </dd>
                  </div>
                  <div>
                    <dt className="t-micro-caps text-muted">Cluster this front end targets</dt>
                    <dd className="figure t-meta mt-1 text-ink">{CLUSTER}</dd>
                  </div>
                  <div className="sm:col-span-2">
                    <dt className="t-micro-caps text-muted">Flags</dt>
                    <dd className="mt-2">
                      {verification.flags.length === 0 ? (
                        <p className="t-meta text-ink">
                          Empty. No flag came back with this record.
                        </p>
                      ) : (
                        <>
                          <ul className="space-y-2">
                            {verification.flags.map((flag) => (
                              <li key={flag} className="figure t-meta text-ink">
                                {flag}
                              </li>
                            ))}
                          </ul>
                          <p className="t-micro mt-2 text-muted">
                            {isMockMode
                              ? "Printed verbatim. These are this build's own strings: no backend was asked, so none of them came from one."
                              : "Printed verbatim. These are the backend's own machine strings."}
                          </p>
                        </>
                      )}
                    </dd>
                  </div>
                </dl>

              <div className="mt-8">
                {/* The exact bytes the wallet is asked to sign, printed before the
                    wallet is asked. The nonce here is a stand-in of the right
                    shape; the one the backend issues takes its place at the
                    wallet, and the fixed lines and the cluster are the same. */}
                <p className="t-micro-caps text-muted">The message you sign</p>
                <pre className="figure t-meta mt-2 whitespace-pre-wrap break-words rounded-panel border border-line bg-inset p-6 text-ink">
                  {verificationMessage(wallet, PLACEHOLDER_NONCE)}
                </pre>
                <p className="t-micro mt-2 text-muted">
                  The nonce above is a stand-in of the right shape. The one this flow signs is the
                  single-use value the backend issues for this wallet, and everything else in the
                  message is fixed, including the cluster line.
                </p>
                <button
                  type="button"
                  onClick={() => {
                    void verify();
                  }}
                  disabled={verifying || isMockMode}
                  aria-busy={verifying}
                  className="mt-6 u-transition inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press disabled:opacity-60"
                >
                  {isMockMode
                    ? "Signing disabled: this deployment has no backend"
                    : verifying
                      ? "Waiting for the wallet"
                      : verification.verified
                        ? "Verify again"
                        : "Sign to verify"}
                </button>
                <p role="status" aria-live="polite" className="t-micro mt-2 text-muted">
                  {verifying ? "Waiting for the wallet to sign." : ""}
                </p>

                {verification.verified && !isMockMode && (
                  <p className="t-meta mt-4 text-ink">
                    The backend recorded this wallet as verified
                    {verification.verifiedAt ? ` at ${formatDateTime(verification.verifiedAt)}` : ""}.
                  </p>
                )}

                {isMockMode && (
                  <p className="t-meta mt-4 text-ink">
                    This deployment verifies nothing. The wallet signs the message and the
                    signature goes nowhere: there is no backend behind this site to check it
                    against, so no wallet is recorded as verified here and nothing is gated on it.
                  </p>
                )}

                <p className="t-micro mt-3 text-muted">
                  The exact message the wallet signs, and the full record beside it, are on{" "}
                  <Link
                    href="/account"
                    className="u-transition text-accent underline underline-offset-2 hover:text-accent-press"
                  >
                    your account page
                  </Link>
                  .
                </p>
              </div>

              {verifyFailure && (
                <div className="mt-6">
                  <FailurePanel title="Verification did not complete" failure={verifyFailure} />
                </div>
              )}
            </>
          ) : (
            // No record and no failure: the read is in flight.
            <div className="mt-6">
              <Skeleton lines={4} />
            </div>
          )}
        </section>

        <section className="mt-16">
          <h2 className="h-section text-ink">What gets recorded</h2>
          {isMockMode ? (
            <p className="t-body mt-4 text-muted">
              Nothing, on this deployment. A backend records your public key and the time it
              checked the signature, and this site has no backend: the signature your wallet makes
              here is checked nowhere, so no verification is recorded and no wallet becomes a
              verified one. What a backend would record is the list below.
            </p>
          ) : null}
          <ul className="t-body mt-4 space-y-3 text-muted">
            <li>Your public key and the time you verified.</li>
            <li>Every ticket issued to or transferred into this wallet, with the price paid.</li>
            <li>
              Nothing else. The signature proves key ownership. It is not a transaction and cannot
              move tokens.
            </li>
          </ul>
        </section>

        <div className="mt-8">
          <DataSourceNote dataSource={verification?.dataSource} />
        </div>
      </div>
    </div>
  );
}

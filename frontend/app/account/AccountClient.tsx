"use client";

import { useCallback, useEffect, useState } from "react";
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
import { Chip, DataSourceNote, Skeleton, Unavailable } from "@/components/ui";
import { capabilities } from "@/lib/capabilities";
import { CLUSTER, toBase58, verificationMessage } from "@/lib/solana";
import { formatDateTime } from "@/lib/format";

/**
 * A nonce stands in for the one the backend issues: 32 hex characters, single
 * use, good for 300 seconds. The preview below is the exact string the wallet is
 * asked to sign, built by the same function the flow itself uses.
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
 * backend has no error body to quote, so both are labelled as what they are
 * instead of being dressed in a code the backend never sent.
 *
 * `origin` is passed in by the call site rather than sniffed here: only the
 * caller knows whether the throw came from the wallet or from the seam.
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
 * /account: the wallet, the verification record the backend holds for it, and
 * the message behind the signature. Nothing is auto-connected: the screen has no
 * wallet until a visitor picks one, and every value below is either the backend's
 * response or this front end's own configuration.
 */
export function AccountClient(): React.ReactElement {
  const { publicKey, signMessage } = useWallet();
  const wallet = publicKey?.toBase58() ?? null;

  const [verification, setVerification] = useState<WalletVerification | null>(null);
  const [readFailure, setReadFailure] = useState<Failure | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verifyFailure, setVerifyFailure] = useState<Failure | null>(null);

  // The verification read: re-run only when the connected wallet changes. There
  // is no separate loading flag, because "no record and no failure" is exactly
  // the read in flight, and a second flag would only let the two disagree.
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

  /**
   * The three calls, in order: a nonce from the backend, a signature from the
   * wallet over the frozen message, then the nonce and signature back to the
   * backend. The only value that ever becomes the record is the one the third
   * call returns.
   */
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

      // The signature is wrapped on its own so a declined prompt is reported as
      // the wallet's answer, not as a backend failure.
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

  const preview = verificationMessage(wallet ?? "", PLACEHOLDER_NONCE);

  return (
    <div className="box pt-16 pb-24">
      <div className="max-w-3xl">
        <h1 className="h-display text-ink">Account</h1>
        <p className="t-deck mt-4 text-muted">
          There is no account here. A wallet is known to this deployment only by the signature it
          can produce, so what follows is the record that signature leaves and the exact string
          behind it.
        </p>

        {!wallet ? (
          <section className="mt-12 rounded-panel border border-line bg-surface p-6">
            <h2 className="h-section text-ink">Wallet</h2>
            <p className="t-body mt-2 text-muted">
              Connect a wallet to read what this deployment holds about it.
            </p>
            <WalletButton className="mt-6" />
          </section>
        ) : (
          <>
            <section className="mt-12">
              <div className="flex flex-wrap items-center justify-between gap-4">
                <h2 className="h-section text-ink">Wallet</h2>
                <AddressPill address={wallet} />
              </div>
              <dl className="mt-6 space-y-4">
                <div>
                  <dt className="t-micro-caps text-muted">Cluster this front end targets</dt>
                  <dd className="figure t-meta mt-1 text-ink">{CLUSTER}</dd>
                </div>
              </dl>
            </section>

            <section className="mt-12">
              <h2 className="h-section text-ink">Verification</h2>

              {readFailure ? (
                <div className="mt-6">
                  <FailurePanel title="The verification read failed" failure={readFailure} />
                </div>
              ) : verification ? (
                <>
                  <dl className="mt-6 grid gap-x-6 gap-y-6 sm:grid-cols-2">
                    <div>
                      <dt className="t-micro-caps text-muted">Verified</dt>
                      <dd className="mt-2">
                        <Chip tone={verification.verified ? "positive" : "neutral"}>
                          {verification.verified ? "Yes" : "No"}
                        </Chip>
                      </dd>
                    </div>
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
                      <dt className="t-micro-caps text-muted">Can purchase</dt>
                      <dd className="t-meta mt-1 text-ink">
                        {verification.canPurchase ? "Yes" : "No"}
                      </dd>
                    </div>
                    <div>
                      <dt className="t-micro-caps text-muted">Can receive a transfer</dt>
                      <dd className="t-meta mt-1 text-ink">
                        {verification.canReceiveTransfer ? "Yes" : "No"}
                      </dd>
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
                    <button
                      type="button"
                      onClick={() => {
                        void verify();
                      }}
                      disabled={verifying || isMockMode}
                      aria-busy={verifying}
                      className="u-transition inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press disabled:opacity-60"
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
                    <p className="t-micro mt-3 text-muted">
                      {isMockMode
                        ? "Signing is a request to prove you hold the key, and this deployment cannot answer it: the signature is made in your wallet and checked nowhere. It is not a transaction and it moves no funds."
                        : "Signing proves you hold the key. It is not a transaction and it moves no funds."}
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

            <section className="mt-12">
              <h2 className="h-section text-ink">The message you sign</h2>
              <p className="t-body mt-2 text-muted">
                {isMockMode
                  ? "A backend rebuilds this message byte for byte to check the signature, and this deployment has no backend: the string below is printed so you can read exactly what the wallet would be asked to sign."
                  : "The backend rebuilds this message byte for byte to check the signature. Changing it invalidates every nonce already in flight."}
              </p>
              <pre className="figure t-meta mt-4 whitespace-pre-wrap break-words rounded-panel border border-line bg-inset p-6 text-ink">
                {preview}
              </pre>
              <p className="t-micro mt-3 text-muted">
                The nonce above is a placeholder. A real one is 32 hex characters, bound to this
                wallet, valid once, and expires after 300 seconds.
              </p>
            </section>
          </>
        )}

        <div className="mt-16">
          <Unavailable capability={capabilities.auth} title="Sign in to an account" />
        </div>

        <div className="mt-8">
          <DataSourceNote dataSource={verification?.dataSource} />
        </div>
      </div>
    </div>
  );
}

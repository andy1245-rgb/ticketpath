"use client";

import { useEffect, useState } from "react";
import { useWallet } from "@solana/wallet-adapter-react";
import { useWalletModal } from "@solana/wallet-adapter-react-ui";
import { shortAddress } from "@/lib/format";

/**
 * Connection and verification entry point.
 *
 * Three states, and the unwalletled one is a real state rather than a dead
 * button: every current wallet registers itself through the Wallet Standard, so
 * an empty adapter list means nothing in this browser can connect, and the
 * button says so underneath instead of failing on click. No blurred panel, no
 * avatar circle, no tab bar.
 *
 * 0.15.40's context is `useWallet()`; it carries the connection, the connected
 * key and the detected adapters in one hook, there is no `useWalletConnection`
 * export in this version.
 */
export function WalletButton({ className = "" }: { className?: string }): React.ReactElement {
  const { connected, publicKey, disconnect, disconnecting, select, wallets } = useWallet();
  const { setVisible } = useWalletModal();
  const [failed, setFailed] = useState(false);
  // Wallet discovery happens in the browser, so the server has no way to know
  // whether an extension is installed. Rendering the answer on the server and
  // again on the client is a hydration mismatch, so the line
  // waits one paint and only then states what was actually detected.
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (connected && publicKey) {
    return (
      <div className={`flex flex-wrap items-center gap-3 ${className}`}>
        <span className="figure t-meta text-ink">{shortAddress(publicKey.toBase58())}</span>
        <button
          type="button"
          disabled={disconnecting}
          onClick={() => {
            setFailed(false);
            // A rejected disconnect leaves the wallet connected; saying so is
            // better than swallowing it and leaving a button that did nothing.
            disconnect().catch(() => setFailed(true));
          }}
          className="u-transition inline-flex min-h-6 items-center t-meta text-muted underline underline-offset-2 hover:text-ink"
        >
          Disconnect
        </button>
        {failed && (
          <p className="t-micro basis-full text-danger">The wallet did not disconnect. Try again.</p>
        )}
      </div>
    );
  }

  return (
    <div className={`flex flex-col items-start gap-2 ${className}`}>
      <button
        type="button"
        onClick={() => {
          select(null);
          setVisible(true);
        }}
        className="u-transition inline-flex h-12 items-center justify-center rounded-pill border border-accent bg-accent px-6 t-meta text-on-accent hover:border-accent-press hover:bg-accent-press"
      >
        Connect wallet
      </button>
      {mounted && wallets.length === 0 && (
        <p className="t-micro text-muted">No Solana wallet extension detected in this browser.</p>
      )}
    </div>
  );
}

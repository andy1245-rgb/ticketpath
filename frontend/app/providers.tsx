"use client";

import { useMemo, type ReactNode } from "react";
import { ConnectionProvider, WalletProvider } from "@solana/wallet-adapter-react";
import { WalletModalProvider } from "@solana/wallet-adapter-react-ui";
import { rpcEndpoint } from "@/lib/solana";

import "@solana/wallet-adapter-react-ui/styles.css";

/**
 * Phantom, Solflare, Backpack and every other current wallet register
 * themselves through the Wallet Standard, which wallet-adapter discovers
 * automatically. Passing an empty adapter list keeps the legacy
 * @solana/wallet-adapter-wallets grab-bag (and its Ledger/WalletConnect
 * transitive tree) out of the bundle entirely.
 */
export function SolanaProviders({ children }: { children: ReactNode }) {
  const endpoint = useMemo(() => rpcEndpoint(), []);

  return (
    <ConnectionProvider endpoint={endpoint}>
      <WalletProvider wallets={[]} autoConnect>
        <WalletModalProvider>{children}</WalletModalProvider>
      </WalletProvider>
    </ConnectionProvider>
  );
}

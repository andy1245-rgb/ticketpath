import type { SolanaCluster, WalletAddress } from "./types";

export const CLUSTER: SolanaCluster =
  (process.env.NEXT_PUBLIC_SOLANA_CLUSTER as SolanaCluster | undefined) ?? "devnet";

const DEFAULT_RPC: Record<SolanaCluster, string> = {
  devnet: "https://api.devnet.solana.com",
  testnet: "https://api.testnet.solana.com",
  "mainnet-beta": "https://api.mainnet-beta.solana.com",
  localnet: "http://127.0.0.1:8899",
};

export function rpcEndpoint(cluster: SolanaCluster = CLUSTER): string {
  return process.env.NEXT_PUBLIC_SOLANA_RPC_URL || DEFAULT_RPC[cluster];
}

/** Deep-link a transaction signature into Solana Explorer on the right cluster. */
export function explorerTxUrl(signature: string, cluster: SolanaCluster = CLUSTER): string {
  const suffix = cluster === "mainnet-beta" ? "" : `?cluster=${cluster}`;
  return `https://explorer.solana.com/tx/${signature}${suffix}`;
}

export function explorerAddressUrl(address: string, cluster: SolanaCluster = CLUSTER): string {
  const suffix = cluster === "mainnet-beta" ? "" : `?cluster=${cluster}`;
  return `https://explorer.solana.com/address/${address}${suffix}`;
}

/**
 * The message a wallet signs to prove ownership during verification. The
 * backend must rebuild this byte-for-byte to check the signature, so the
 * format is frozen: changing it invalidates every in-flight nonce.
 */
export function verificationMessage(wallet: WalletAddress, nonce: string): string {
  return [
    "Verify wallet ownership for ticket issuance.",
    "",
    `Wallet: ${wallet}`,
    `Nonce: ${nonce}`,
    `Cluster: ${CLUSTER}`,
  ].join("\n");
}

/** Cheap shape check so we can validate pasted addresses without web3.js. */
const BASE58 = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;

export function isLikelyWalletAddress(value: string): boolean {
  return BASE58.test(value.trim());
}

/**
 * The program address, and only if it was configured. There is deliberately no
 * default: an invented address renders as fact on a page about on-chain
 * enforcement. Unset means the strip says "Program not deployed yet" and the
 * explorer controls stay disabled (brief 5.5).
 */
export const PROGRAM_ID: string | null = process.env.NEXT_PUBLIC_PROGRAM_ID?.trim() || null;

export function explorerProgramUrl(cluster: SolanaCluster = CLUSTER): string | null {
  if (!PROGRAM_ID) return null;
  return explorerAddressUrl(PROGRAM_ID, cluster);
}

const B58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz";

/**
 * Base58-encode a signature for transport. Written out rather than pulling in
 * `bs58`, which is only a transitive dependency of web3.js here — depending on
 * it directly would break the first time that tree is reshuffled.
 */
export function toBase58(bytes: Uint8Array): string {
  if (bytes.length === 0) return "";

  // Count and strip leading zero bytes; each becomes a leading '1'.
  let zeros = 0;
  while (zeros < bytes.length && bytes[zeros] === 0) zeros++;

  const digits: number[] = [];
  for (let i = zeros; i < bytes.length; i++) {
    let carry = bytes[i];
    for (let j = 0; j < digits.length; j++) {
      carry += digits[j] << 8;
      digits[j] = carry % 58;
      carry = (carry / 58) | 0;
    }
    while (carry > 0) {
      digits.push(carry % 58);
      carry = (carry / 58) | 0;
    }
  }

  let out = "1".repeat(zeros);
  for (let i = digits.length - 1; i >= 0; i--) out += B58_ALPHABET[digits[i]];
  return out;
}

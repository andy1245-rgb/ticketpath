import assert from "node:assert/strict";
import { test } from "node:test";

import {
  CLUSTER,
  explorerAddressUrl,
  explorerTxUrl,
  verificationMessage,
} from "./solana.ts";

test("the verification message is frozen, byte for byte, with no trailing newline", () => {
  const wallet = "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU";
  const nonce = "0123456789abcdef0123456789abcdef";

  // Four fixed lines and the configured cluster. The backend rebuilds this same
  // string to check the signature, so the shape here is the contract.
  const expected = [
    "Verify wallet ownership for ticket issuance.",
    "",
    `Wallet: ${wallet}`,
    `Nonce: ${nonce}`,
    `Cluster: ${CLUSTER}`,
  ].join("\n");

  const message = verificationMessage(wallet, nonce);

  assert.equal(message, expected);
  assert.equal(message.endsWith("\n"), false, "a trailing newline invalidates every signature");
  assert.equal(message.includes("\r"), false, "UTF-8 with \\n joins, never CRLF");
  assert.equal(message.split("\n").length, 5);
  assert.equal(message.trim(), message, "no leading or trailing whitespace of any kind");
  assert.equal(
    message.startsWith("Verify wallet ownership for ticket issuance.\n\nWallet: "),
    true,
  );
  assert.equal(message.includes(wallet), true);
  assert.equal(message.includes(nonce), true);
});

test("explorer links carry the cluster unless it is mainnet-beta", () => {
  const signature = "4EjLt3UAXcHzQ1MU4nt1vQbp8boLBH7k2VTqpJfiwtVA1RbtCsvET6cS1wHeBUxE4GjTmfM7m6kSYf5invrBLGkE";

  assert.equal(
    explorerTxUrl(signature, "mainnet-beta"),
    `https://explorer.solana.com/tx/${signature}`,
    "mainnet-beta is the explorer's default, so the suffix is absent",
  );
  assert.equal(
    explorerTxUrl(signature, "devnet"),
    `https://explorer.solana.com/tx/${signature}?cluster=devnet`,
  );
  assert.equal(
    explorerTxUrl(signature, "testnet"),
    `https://explorer.solana.com/tx/${signature}?cluster=testnet`,
  );
  assert.equal(
    explorerTxUrl(signature, "localnet"),
    `https://explorer.solana.com/tx/${signature}?cluster=localnet`,
  );

  const address = "SYN1EkWc6HA2sY3n2QENB329vug7vkJ5mxBTjKN1pcR";
  assert.equal(
    explorerAddressUrl(address, "mainnet-beta"),
    `https://explorer.solana.com/address/${address}`,
  );
  assert.equal(
    explorerAddressUrl(address, "devnet"),
    `https://explorer.solana.com/address/${address}?cluster=devnet`,
  );
});

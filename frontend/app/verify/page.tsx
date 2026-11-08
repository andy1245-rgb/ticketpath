import type { Metadata } from "next";
import { VerifyClient } from "./VerifyClient";

export const metadata: Metadata = {
  title: "Verify your wallet",
  description:
    "Sign a frozen message to prove you hold the key. Verification is a signature, never a transaction.",
};

export default function VerifyPage() {
  return <VerifyClient />;
}

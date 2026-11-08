import type { Metadata } from "next";
import { AccountClient } from "./AccountClient";

export const metadata: Metadata = {
  title: "Account",
  description:
    "The wallet, the verification record the backend returned for it, and the exact message it has to sign.",
};

/**
 * A shell, because everything below it needs the wallet: this screen is the one
 * place a connection is read, and it is read in the browser.
 */
export default function AccountPage() {
  return <AccountClient />;
}

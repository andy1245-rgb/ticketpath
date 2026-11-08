import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { SolanaProviders } from "./providers";
import { SiteHeader } from "@/components/SiteHeader";
import { SiteFooter } from "@/components/SiteFooter";
import "./globals.css";

/**
 * next/font downloads both faces at build time and serves them from our own
 * origin, so no request leaves for Google at runtime. The `variable` names are
 * what app/theme.css puts behind the literal family names in the stacks.
 */
const geist = Geist({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist",
  display: "swap",
  fallback: ["ui-sans-serif", "system-ui", "Segoe UI", "sans-serif"],
});

const geistMono = Geist_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-geist-mono",
  display: "swap",
  fallback: ["ui-monospace", "SF Mono", "Menlo", "monospace"],
});

export const metadata: Metadata = {
  title: "SeatPass · Tickets on Solana",
  description:
    "Wallet-bound event tickets on Solana, with the resale cap, the price paid and every owner the ticket has ever had, recorded against the ticket itself.",
};

/** The viewport sets the width, the initial scale, and nothing that blocks zoom. */
export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable}`}>
      <body>
        <SolanaProviders>
          <a href="#main" className="skip-link">
            Skip to content
          </a>
          <SiteHeader />
          <main id="main" tabIndex={-1}>
            {children}
          </main>
          <SiteFooter />
        </SolanaProviders>
      </body>
    </html>
  );
}

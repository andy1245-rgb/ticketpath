import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Static export: `next build` writes a plain `out/` directory of HTML, JS and
  // assets that any static host can serve. No Node process at runtime.
  output: "export",
  // The export has no image optimisation server, so every <Image> must be
  // served as-is. No next/image is used today; this keeps it true if one is added.
  images: { unoptimized: true },
  reactStrictMode: true,
  // @solana/web3.js and the wallet adapters reach for Node builtins that the
  // browser bundle does not need. Stub them rather than shipping polyfills.
  webpack: (config) => {
    config.resolve.fallback = { ...config.resolve.fallback, fs: false, net: false, tls: false };
    return config;
  },
};

export default nextConfig;

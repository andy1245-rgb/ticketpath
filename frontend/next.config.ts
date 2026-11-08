import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // @solana/web3.js and the wallet adapters reach for Node builtins that the
  // browser bundle does not need. Stub them rather than shipping polyfills.
  webpack: (config) => {
    config.resolve.fallback = { ...config.resolve.fallback, fs: false, net: false, tls: false };
    return config;
  },
};

export default nextConfig;

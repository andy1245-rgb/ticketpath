// Flat config for ESLint 9. eslint-config-next 15 still ships the eslintrc
// shape, so FlatCompat adapts it; that is the arrangement Next documents for
// this major. `npm run lint` is `eslint .`, not the deprecated `next lint`.
import { dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { FlatCompat } from "@eslint/eslintrc";

const baseDirectory = dirname(fileURLToPath(import.meta.url));
const compat = new FlatCompat({ baseDirectory });

const config = [
  {
    ignores: [
      ".next/**",
      "node_modules/**",
      "out/**",
      "next-env.d.ts",
      "lib/mock/**",
      "tools/build-copy.sh",
    ],
  },
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    // Tools are CommonJS scripts run by node directly, not part of the bundle.
    files: ["tools/**/*.cjs", "tools/**/*.mjs"],
    languageOptions: {
      sourceType: "commonjs",
      globals: { require: "readonly", module: "writable", process: "readonly", __dirname: "readonly", console: "readonly" },
    },
    rules: { "@typescript-eslint/no-require-imports": "off" },
  },
];

export default config;

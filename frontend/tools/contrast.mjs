// WCAG 2.1 relative-luminance contrast for every text pair the design system
// declares. Run: node tools/contrast.mjs
const hex = (h) => {
  const n = h.replace("#", "");
  return [0, 2, 4].map((i) => parseInt(n.slice(i, i + 2), 16) / 255);
};
const lin = (c) => (c <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4);
const lum = (h) => {
  const [r, g, b] = hex(h).map(lin);
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
const ratio = (a, b) => {
  const [x, y] = [lum(a), lum(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
};

const pairs = [
  ["light ink / canvas", "#14161A", "#F8F6F2"],
  ["light ink / surface", "#14161A", "#FFFFFF"],
  ["light muted / canvas", "#5F636B", "#F8F6F2"],
  ["light muted / surface", "#5F636B", "#FFFFFF"],
  ["light muted / inset", "#5F636B", "#F1EDE6"],
  ["light on-accent / accent", "#FFFFFF", "#4F2BEA"],
  ["light on-accent / accent-press", "#FFFFFF", "#3F1FCC"],
  ["light accent / canvas", "#4F2BEA", "#F8F6F2"],
  ["light accent / surface", "#4F2BEA", "#FFFFFF"],
  ["light warning / surface", "#8A4B00", "#FFFFFF"],
  ["light warning / canvas", "#8A4B00", "#F8F6F2"],
  ["light positive / surface", "#1A6B45", "#FFFFFF"],
  ["light danger / surface", "#A81E14", "#FFFFFF"],
  ["light ink / inset", "#14161A", "#F1EDE6"],
  ["dark ink / canvas", "#F3F1EC", "#0E0F12"],
  ["dark ink / surface", "#F3F1EC", "#16181D"],
  ["dark muted / canvas", "#A8A49B", "#0E0F12"],
  ["dark muted / surface", "#A8A49B", "#16181D"],
  ["dark muted / inset", "#A8A49B", "#1E2126"],
  ["dark on-accent / accent", "#14161A", "#9F86FF"],
  ["dark on-accent / accent-press", "#14161A", "#B49BFF"],
  ["dark accent / canvas", "#9F86FF", "#0E0F12"],
  ["dark accent / surface", "#9F86FF", "#16181D"],
  ["dark warning / canvas", "#E0A05A", "#0E0F12"],
  ["dark warning / surface", "#E0A05A", "#16181D"],
  ["dark positive / canvas", "#5FD3A0", "#0E0F12"],
  ["dark danger / canvas", "#FF8A80", "#0E0F12"],
  ["dark ink / inset", "#F3F1EC", "#1E2126"],
];

let fail = 0;
for (const [label, fg, bg] of pairs) {
  const r = ratio(fg, bg);
  const ok = r >= 4.5;
  if (!ok) fail++;
  console.log(`${ok ? "PASS" : "FAIL"} ${r.toFixed(2)}:1  ${label}`);
}
console.log(`\n${pairs.length} pairs, ${fail} below 4.5:1`);
process.exit(fail ? 1 : 0);

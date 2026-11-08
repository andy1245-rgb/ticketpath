#!/usr/bin/env node
/**
 * The headless render check from brief 8.4, plus the structural sweeps that
 * sections 8.5 and 8.8 ask for.
 *
 * Runs against a build served on :3010. Uses a Chromium and a playwright-core
 * that are already on the machine, both named by environment variable, so no
 * browser download and no entry in package.json:
 *
 *   SEATPASS_PLAYWRIGHT_CORE  a playwright-core install to require
 *                             (default: the package name, if it is installed)
 *   SEATPASS_CHROME           a Chrome/Chromium binary to launch
 *                             (default: whatever playwright resolves)
 *
 *   node tools/verify-landing.cjs [baseUrl]
 *
 * Prints every number it measured and exits non-zero if any assertion fails.
 */
const path = require("node:path");
const fs = require("node:fs");

const PLAYWRIGHT = process.env.SEATPASS_PLAYWRIGHT_CORE || "playwright-core";
const CHROME = process.env.SEATPASS_CHROME || "";

const { chromium } = require(PLAYWRIGHT);

const BASE = process.argv[2] || "http://127.0.0.1:3010";
const ROOT = path.resolve(__dirname, "..");

const failures = [];
const pass = (label, ok, detail) => {
  const line = `${ok ? "PASS" : "FAIL"}  ${label}${detail == null ? "" : `  ${detail}`}`;
  console.log(line);
  if (!ok) failures.push(line);
};

/** The first on-sale event and first ticket in the bundled fixtures, for routes. */
function fixtureRoutes() {
  const events = JSON.parse(fs.readFileSync(path.join(ROOT, "lib/mock/events.json"), "utf8"));
  const tickets = JSON.parse(fs.readFileSync(path.join(ROOT, "lib/mock/tickets.json"), "utf8"));
  const featured = events.find((e) => e.status === "on_sale") ?? events[0];
  const ticket = tickets[0];
  return {
    slug: featured.slug,
    ticketId: ticket.id,
  };
}

const ROUTES = (slug, ticketId) => [
  "/",
  "/events",
  `/events/${slug}`,
  `/events/${slug}/checkout`,
  `/tickets/${ticketId}`,
  "/my-tickets",
  `/door?ticket=${ticketId}`,
  "/organizer",
  "/organizer/events/new",
  "/resale",
  `/resale/list/${ticketId}`,
  "/account",
  "/pricing",
  "/rules",
  "/verify",
];

const ALLOWED_RADII = new Set(["0px", "8px", "12px", "16px", "9999px"]);
const ACCENT = "rgb(79, 43, 234)";

async function metrics(page) {
  return page.evaluate(() => {
    const withText = [...document.querySelectorAll("*")].filter(
      (el) => el.children.length === 0 && el.textContent.trim().length > 0,
    );
    const sizes = withText.map((el) => parseFloat(getComputedStyle(el).fontSize));
    const radii = [...document.querySelectorAll("*")].map(
      (el) => getComputedStyle(el).borderRadius,
    );
    const headings = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => h.tagName);
    const svgs = [...document.querySelectorAll("svg")].map((s) => ({
      role: s.getAttribute("role"),
      hidden: s.getAttribute("aria-hidden"),
      label: s.getAttribute("aria-label"),
      focusable: s.getAttribute("focusable"),
    }));
    const controls = [...document.querySelectorAll("a,button,input,select,textarea")];
    const unnamed = controls
      .filter((el) => {
        const text = (el.textContent || "").trim();
        const name =
          el.getAttribute("aria-label") ||
          el.getAttribute("title") ||
          text ||
          (el.labels && el.labels[0] && el.labels[0].textContent) ||
          el.getAttribute("placeholder");
        return !name || !String(name).trim();
      })
      .map((el) => el.tagName + "." + (el.className || "").toString().slice(0, 40));
    const weights = withText.map((el) => parseInt(getComputedStyle(el).fontWeight, 10));
    return {
      title: document.title,
      scrollWidth: document.documentElement.scrollWidth,
      innerWidth: window.innerWidth,
      h1: document.querySelector("h1")
        ? {
            size: getComputedStyle(document.querySelector("h1")).fontSize,
            line: getComputedStyle(document.querySelector("h1")).lineHeight,
          }
        : null,
      h1Count: document.querySelectorAll("h1").length,
      headings,
      bodyBg: getComputedStyle(document.body).backgroundColor,
      bodyColor: getComputedStyle(document.body).color,
      mutedColor: (() => {
        const el = [...document.querySelectorAll("p")].find((p) =>
          getComputedStyle(p).color === "rgb(95, 99, 107)",
        );
        return el ? getComputedStyle(el).color : null;
      })(),
      radii: [...new Set(radii)],
      minFontSize: sizes.length ? Math.min(...sizes) : null,
      maxWeight: weights.length ? Math.max(...weights) : null,
      monoFigure: (() => {
        const el = document.querySelector(".figure");
        return el
          ? { family: getComputedStyle(el).fontFamily, text: el.textContent.trim().slice(0, 24) }
          : null;
      })(),
      geistMonoLoaded: document.fonts.check('600 32px "Geist Mono"'),
      svgs,
      unnamedCount: unnamed.length,
      unnamedSample: unnamed.slice(0, 3),
    };
  });
}

async function tabStops(page, count) {
  const stops = [];
  await page.evaluate(() => document.body.focus());
  for (let i = 0; i < count; i++) {
    await page.keyboard.press("Tab");
    const stop = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el || el === document.body) return null;
      const cs = getComputedStyle(el);
      return {
        tag: el.tagName,
        name: (el.getAttribute("aria-label") || el.textContent || "").trim().slice(0, 40),
        width: cs.outlineWidth,
        offset: cs.outlineOffset,
        color: cs.outlineColor,
      };
    });
    if (stop) stops.push(stop);
  }
  return stops;
}

(async () => {
  const { slug, ticketId } = fixtureRoutes();
  console.log(`base ${BASE}`);
  console.log(`fixtures: slug=${slug} ticket=${ticketId}\n`);

  const browser = await chromium.launch(CHROME ? { executablePath: CHROME } : {});
  const consoleErrors = [];
  const failedRequests = [];

  const newPage = async (viewport) => {
    const page = await browser.newPage({ viewport });
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(`${page.url()} :: ${msg.text()}`);
    });
    page.on("pageerror", (err) => consoleErrors.push(`${page.url()} :: ${err.message}`));
    page.on("requestfailed", (req) =>
      failedRequests.push(`${page.url()} :: ${req.url()} :: ${req.failure()?.errorText}`),
    );
    return page;
  };

  // ---- The landing page, three widths, every number 8.4 names ---------------
  for (const width of [1440, 390, 320]) {
    const page = await newPage({ width, height: 1000 });
    await page.goto(`${BASE}/`, { waitUntil: "load", timeout: 60000 });
    await page.waitForTimeout(700);
    await page.evaluate(() => document.fonts.ready);
    const m = await metrics(page);

    console.log(`\n== / at ${width} ==`);
    pass(`scrollWidth == innerWidth`, m.scrollWidth === m.innerWidth, `${m.scrollWidth} / ${m.innerWidth}`);
    const want = width === 1440 ? { size: "64px", line: "64px" } : { size: "32px", line: "38px" };
    pass(
      `h1 ${want.size}/${want.line}`,
      m.h1 && m.h1.size === want.size && m.h1.line === want.line,
      m.h1 ? `${m.h1.size} / ${m.h1.line}` : "no h1",
    );
    pass(`exactly one h1`, m.h1Count === 1, String(m.h1Count));
    pass(
      `price figure family contains "Geist Mono"`,
      !!m.monoFigure && m.monoFigure.family.includes("Geist Mono"),
      m.monoFigure ? m.monoFigure.family.slice(0, 80) : "no .figure",
    );
    pass(`document.fonts.check('600 32px "Geist Mono"')`, m.geistMonoLoaded === true);
    pass(`body background rgb(248,246,242)`, m.bodyBg === "rgb(248, 246, 242)", m.bodyBg);
    pass(`body color rgb(20,22,26)`, m.bodyColor === "rgb(20, 22, 26)", m.bodyColor);
    pass(`a muted paragraph rgb(95,99,107)`, m.mutedColor === "rgb(95, 99, 107)", String(m.mutedColor));
    const badRadii = m.radii.filter((r) => !ALLOWED_RADII.has(r));
    pass(`border-radius set is a subset of 0/8/12/16/9999`, badRadii.length === 0, `saw ${m.radii.join(", ")}`);
    pass(`minimum computed font-size with text is >= 12px`, m.minFontSize >= 12, `${m.minFontSize}px`);
    pass(`no weight over 600`, m.maxWeight <= 600, `${m.maxWeight}`);
    pass(`title is exactly "SeatPass · Tickets on Solana"`, m.title === "SeatPass · Tickets on Solana", JSON.stringify(m.title));
    pass(`every svg has a role or aria-hidden`, m.svgs.every((s) => s.role || s.hidden === "true"), `${m.svgs.length} svgs`);
    pass(`every control has a name`, m.unnamedCount === 0, m.unnamedSample.join(" | "));

    if (width === 1440) {
      const stops = await tabStops(page, 24);
      const bad = stops.filter(
        (s) => s.width !== "2px" || s.offset !== "2px" || s.color !== ACCENT,
      );
      console.log(`tab stops inspected: ${stops.length}`);
      console.log(`first stop: ${stops[0]?.tag} "${stops[0]?.name}"`);
      pass(
        `every tab stop has a 2px accent outline at 2px offset`,
        bad.length === 0,
        bad.length ? JSON.stringify(bad.slice(0, 2)) : `${stops.length} stops ok`,
      );
      pass(
        `skip link is the first tab stop`,
        /skip/i.test(stops[0]?.name || ""),
        stops[0]?.name,
      );
    }
    await page.close();
  }

  // ---- Every route: overflow, headings, sizes, names, title ---------------
  console.log(`\n== all ${ROUTES(slug, ticketId).length} routes at 1440 and 390 ==`);
  for (const width of [1440, 390]) {
    for (const route of ROUTES(slug, ticketId)) {
      const page = await newPage({ width, height: 900 });
      try {
        const res = await page.goto(`${BASE}${route}`, { waitUntil: "load", timeout: 60000 });
        await page.waitForTimeout(450);
        const m = await metrics(page);
        const overflow = await page.evaluate(() => {
          const bad = [];
          for (const el of document.querySelectorAll("*")) {
            const cs = getComputedStyle(el);
            // Hidden, clipped and scrollable containers are clipping on
            // purpose: an sr-only caption or a scrolling strip is not an
            // overflow bug, and SVG text has no client-box semantics at all.
            if (cs.overflowX !== "visible" && cs.overflowX !== "initial") continue;
            if (cs.clipPath && cs.clipPath !== "none") continue;
            if (el.closest("svg")) continue;
            if (el.closest("[class*='sr-only']")) continue;
            if (el.scrollWidth > el.clientWidth + 1 && el.clientWidth > 0) {
              bad.push(`${el.tagName}.${String(el.className).slice(0, 30)} ${el.scrollWidth}>${el.clientWidth}`);
            }
          }
          return bad;
        });
        const ok =
          res.status() < 400 &&
          m.scrollWidth === m.innerWidth &&
          m.h1Count === 1 &&
          m.minFontSize >= 12 &&
          m.maxWeight <= 600 &&
          m.radii.every((r) => ALLOWED_RADII.has(r)) &&
          m.unnamedCount === 0 &&
          overflow.length === 0;
        pass(
          `${width} ${route}`,
          ok,
          `http ${res.status()} scroll ${m.scrollWidth}/${m.innerWidth} h1 ${m.h1Count} minfs ${m.minFontSize} maxw ${m.maxWeight} overflow ${overflow.length}`,
        );
        if (overflow.length) console.log(`   overflow: ${overflow.slice(0, 3).join(" | ")}`);
      } catch (err) {
        pass(`${width} ${route}`, false, err.message);
      }
      await page.close();
    }
  }

  await browser.close();

  console.log(`\n== console and network ==`);
  pass(`no console errors`, consoleErrors.length === 0, `${consoleErrors.length}`);
  consoleErrors.slice(0, 5).forEach((e) => console.log(`   ${e}`));
  pass(`no failed requests`, failedRequests.length === 0, `${failedRequests.length}`);
  failedRequests.slice(0, 5).forEach((e) => console.log(`   ${e}`));

  console.log(`\n${failures.length ? `${failures.length} FAILURES` : "ALL CHECKS PASSED"}`);
  process.exit(failures.length ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(2);
});

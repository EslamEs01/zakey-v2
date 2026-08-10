// Find what makes a page wider than its viewport.
//
//   node scripts/find_overflow.mjs <path> [width]
//
// Reports every element whose right edge (or left, in RTL) crosses the viewport
// boundary, innermost first — the innermost offender is usually the cause and
// the ancestors are just carrying it.
import { chromium } from "@playwright/test";

const BASE = process.env.ZAKEY_BASE || "http://127.0.0.1:8000";
const PATHNAME = process.argv[2] || "/account/";
const WIDTH = Number(process.argv[3] || 390);
const EMAIL = process.env.ZAKEY_EMAIL || "admin@zakey.test";
const PASSWORD = process.env.ZAKEY_PASSWORD || "ZakeyDev!2026";

const browser = await chromium.launch({ channel: "chrome" });
const context = await browser.newContext({
  viewport: { width: WIDTH, height: 900 },
  locale: "ar-EG",
});
const page = await context.newPage();

await page.goto(`${BASE}/account/`, { waitUntil: "networkidle" });
if (await page.locator("#login-email").count()) {
  await page.fill("#login-email", EMAIL);
  await page.fill("#login-password", PASSWORD);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('form[data-login-form] button[type="submit"]'),
  ]);
}
await page.goto(`${BASE}${PATHNAME}`, { waitUntil: "networkidle" });

const report = await page.evaluate((viewportWidth) => {
  const doc = document.documentElement;
  const out = {
    scrollWidth: doc.scrollWidth,
    clientWidth: doc.clientWidth,
    offenders: [],
  };
  for (const el of document.querySelectorAll("body *")) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 && r.height === 0) continue;
    const overflowsRight = Math.round(r.right) > viewportWidth + 1;
    const overflowsLeft = Math.round(r.left) < -1;
    if (!overflowsRight && !overflowsLeft) continue;
    out.offenders.push({
      tag: el.tagName.toLowerCase(),
      cls: (el.getAttribute("class") || "").slice(0, 60),
      left: Math.round(r.left),
      right: Math.round(r.right),
      width: Math.round(r.width),
      depth: (() => { let d = 0, n = el; while ((n = n.parentElement)) d++; return d; })(),
    });
  }
  out.offenders.sort((a, b) => b.depth - a.depth);
  return out;
}, WIDTH);

console.log(`${PATHNAME} @ ${WIDTH}px — scrollWidth ${report.scrollWidth}, clientWidth ${report.clientWidth}`);
console.log(`offenders: ${report.offenders.length} (innermost first)`);
for (const o of report.offenders.slice(0, 12)) {
  console.log(`  depth=${o.depth} <${o.tag} class="${o.cls}"> left=${o.left} right=${o.right} w=${o.width}`);
}

await browser.close();

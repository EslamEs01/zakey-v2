// Capture the account surfaces for design review.
//
// `/account/` is the *customer* page and `/admin/` is the staff back office —
// they are different applications behind different sessions. A superuser signing
// in at the storefront gets the customer view, which is correct and is the usual
// source of "I asked for an admin and got a normal user".
//
//   node scripts/capture_account.mjs [outdir]
import { chromium } from "@playwright/test";
import { mkdirSync } from "node:fs";

const BASE = process.env.ZAKEY_BASE || "http://127.0.0.1:8000";
const EMAIL = process.env.ZAKEY_EMAIL || "admin@zakey.test";
const PASSWORD = process.env.ZAKEY_PASSWORD || "ZakeyDev!2026";
const OUT = process.argv[2] || ".design-review";
mkdirSync(OUT, { recursive: true });

const VIEWPORTS = [
  { name: "1440", width: 1440, height: 1200 },
  { name: "390", width: 390, height: 1200 },
];

const browser = await chromium.launch({ channel: "chrome" });

for (const vp of VIEWPORTS) {
  const context = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    locale: "ar-EG",
    colorScheme: "light",
  });
  const page = await context.newPage();

  // Signed-out first.
  await page.goto(`${BASE}/account/`, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${OUT}/account-signed-out-${vp.name}.png`, fullPage: true });

  // Then sign in through the storefront's own form.
  await page.fill("#login-email", EMAIL);
  await page.fill("#login-password", PASSWORD);
  await Promise.all([
    page.waitForLoadState("networkidle"),
    page.click('form[data-login-form] button[type="submit"]'),
  ]);
  await page.goto(`${BASE}/account/`, { waitUntil: "networkidle" });
  await page.screenshot({ path: `${OUT}/account-signed-in-${vp.name}.png`, fullPage: true });

  const mode = await page.getAttribute(".account-page", "data-account-mode");
  const heading = await page.textContent("h1").catch(() => "");
  console.log(`${vp.name}: data-account-mode=${mode} h1=${heading?.trim()}`);

  // Every tab, so the whole surface is reviewable.
  for (const tab of ["orders", "wishlist", "addresses", "payment", "settings"]) {
    await page.goto(`${BASE}/account/?tab=${tab}`, { waitUntil: "networkidle" });
    await page.screenshot({ path: `${OUT}/account-${tab}-${vp.name}.png`, fullPage: true });
  }

  await context.close();
}

await browser.close();
console.log(`captured into ${OUT}/`);

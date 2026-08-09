import { test, expect } from "@playwright/test";

// 13 public routes from storefront/urls.py. Slug routes use fixed fixture slugs.
const ROUTES = [
  { id: "home", path: "/" },
  { id: "shop", path: "/shop/" },
  { id: "collection", path: "/collections/fingerprint-locks/" },
  { id: "search", path: "/search/" },
  { id: "product", path: "/products/zakey-apex-pro/" },
  { id: "cart", path: "/cart/" },
  { id: "checkout", path: "/checkout/" },
  { id: "wishlist", path: "/wishlist/" },
  { id: "account", path: "/account/" },
  { id: "about", path: "/about/" },
  { id: "contact", path: "/contact/" },
  { id: "error-404", path: "/errors/404/", expectedStatus: 404 },
  { id: "error-500", path: "/errors/500/", expectedStatus: 500 },
];

async function settleForScreenshot(page) {
  // Force eager loading so full-page captures do not depend on scroll/lazy state.
  await page.locator("img").evaluateAll(async (images) => {
    for (const image of images) image.loading = "eager";
    await Promise.all(images.map((image) => image.complete
      ? Promise.resolve()
      : new Promise((resolve) => {
        image.addEventListener("load", resolve, { once: true });
        image.addEventListener("error", resolve, { once: true });
      })));
  });
  // Deterministic typography before capture.
  await page.evaluate(() => document.fonts.ready);
}

for (const route of ROUTES) {
  test(`${route.id}`, async ({ page }) => {
    const response = await page.goto(route.path, { waitUntil: "networkidle" });
    expect(response, "route produced no response").not.toBeNull();
    expect(response.status()).toBe(route.expectedStatus ?? 200);
    await expect(page.locator("main")).toBeVisible();
    await settleForScreenshot(page);
    await expect(page).toHaveScreenshot(`${route.id}.png`, {
      fullPage: true,
      animations: "disabled",
      maxDiffPixelRatio: 0.01,
      timeout: 60_000,
    });
  });
}

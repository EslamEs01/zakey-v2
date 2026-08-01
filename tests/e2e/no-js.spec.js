import { test, expect } from "@playwright/test";

const routes = ["/", "/shop/", "/search/?q=قفل", "/products/zakey-apex-pro/", "/cart/", "/checkout/", "/wishlist/", "/account/", "/about/", "/contact/"];

for (const route of routes) {
  test(`no-js ${route}`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response.status()).toBe(200);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("main h1").first()).toBeVisible();
    await expect(page.locator(".noscript-note")).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

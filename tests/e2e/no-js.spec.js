import { test, expect } from "@playwright/test";

/**
 * The no-JavaScript guarantee (T-1607/T-1905, FR-136).
 *
 * This project runs with `javaScriptEnabled: false` (playwright.config.js), so
 * nothing under static/src/js executes here. "Useful without JavaScript" is not
 * "returns 200": the prototype's cart, wishlist and checkout returned 200 too
 * and then rendered an empty shell that only a script could fill.
 *
 * So the assertions below go past the status line. Every page must present its
 * heading and real content; the catalogue must be browsable through ordinary
 * links; and — the part that actually decides the requirement — a customer with
 * scripting off must be able to put a product in the basket, change its
 * quantity, watch a server-computed total follow along, and empty it again.
 * Every one of those steps is a native form submit.
 */

const routes = ["/", "/shop/", "/search/?q=قفل", "/products/zakey-apex-pro/", "/cart/", "/checkout/", "/wishlist/", "/account/", "/about/", "/contact/"];

for (const route of routes) {
  test(`no-js ${route}`, async ({ page }) => {
    const response = await page.goto(route);
    expect(response.status()).toBe(200);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("main h1").first()).toBeVisible();
    await expect(page.locator(".noscript-note")).toBeVisible();
    // The site is navigable: the header menu is markup, not a script.
    expect(await page.locator("header a[href]").count()).toBeGreaterThan(0);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(overflow).toBeLessThanOrEqual(1);
  });
}

test("no-js the catalogue is browsable and sortable", async ({ page }) => {
  await page.goto("/shop/");

  const cards = page.locator("[data-product-card]");
  expect(await cards.count()).toBeGreaterThan(0);

  // Sorting is a GET form with a real submit control, not a change listener.
  // The control is `sr-only`: sighted users get the script's change handler,
  // everyone else gets a focusable button, so this activates it by keyboard.
  await page.selectOption("#catalogue-sort", "price-asc");
  await page.locator("[data-sort-form] button[type='submit']").press("Enter");
  await expect(page).toHaveURL(/sort=price-asc/);
  expect(await page.locator("[data-product-card]").count()).toBeGreaterThan(0);

  // A card is a link, so the product page is one click away.
  await page.locator("[data-product-card] a[href*='/products/']").first().click();
  await expect(page).toHaveURL(/\/products\//);
  await expect(page.locator("main h1").first()).toBeVisible();
});

test("no-js a product can be bought, adjusted and removed", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");

  await page.locator("form[data-add-to-cart-form] [data-add-product]").click();
  await page.goto("/cart/");

  const lines = page.locator("[data-cart-line]");
  await expect(lines).toHaveCount(1);
  await expect(page.locator("[data-cart-name]").first()).not.toBeEmpty();
  await expect(page.locator("[data-cart-quantity]").first()).toHaveText("1");

  // Totals are rendered by the server: with no script running, a number is
  // only on this page because the server put it there.
  const total = page.locator("[data-cart-total]");
  await expect(total).toBeVisible();
  const singleUnit = await total.textContent();
  expect(singleUnit).toMatch(/\d/);

  await page.locator("[data-cart-increase]").first().click();
  await expect(page.locator("[data-cart-quantity]").first()).toHaveText("2");
  expect(await total.textContent()).not.toBe(singleUnit);

  await page.locator("[data-cart-remove]").first().click();
  await expect(page.locator("[data-cart-empty]")).toBeVisible();
});

test("no-js checkout is one complete form with a submit control", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("form[data-add-to-cart-form] [data-add-product]").click();
  await page.goto("/checkout/");

  // The step machinery is progressive enhancement; without it every panel is
  // in the document and visible, so the whole order can be filled in at once.
  const panels = page.locator("[data-checkout-panel]");
  await expect(panels).toHaveCount(3);
  for (let index = 0; index < 3; index += 1) {
    await expect(panels.nth(index)).toBeVisible();
  }

  await expect(page.locator("form[data-checkout-form]")).toHaveAttribute("method", /post/i);
  await expect(page.locator("[data-checkout-final]")).toBeVisible();
  await expect(page.locator("[data-checkout-total]")).toBeVisible();
});

test("no-js an account can still be signed in to", async ({ page }) => {
  await page.goto("/account/");

  const login = page.locator("form[data-login-form]");
  await expect(login).toHaveAttribute("method", /post/i);
  await expect(login.locator("input[name='email']")).toBeVisible();
  await expect(login.locator("input[name='password']")).toBeVisible();
  await expect(login.locator("button[type='submit']")).toBeVisible();
});

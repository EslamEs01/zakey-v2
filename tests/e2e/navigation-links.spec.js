import { test, expect } from "@playwright/test";

const LINK_SOURCES = [
  { route: "/", selector: "header a, footer a, #mobile-menu a" },
  { route: "/shop/", selector: ".filter-sidebar a, #filter-dialog a" },
  { route: "/account/?state=signed-in", selector: ".account-side a" },
];
const PATH_PREFIX = (process.env.ZAKEY_E2E_PATH_PREFIX || "").replace(/\/$/, "");

function sitePath(route) {
  return `${PATH_PREFIX}${route}` || "/";
}

function internalLinks(hrefs, origin) {
  return [...new Set(hrefs)]
    .map((href) => new URL(href, origin))
    .filter((url) => url.origin === origin);
}

for (const source of LINK_SOURCES) {
  test(`all navigation links work from ${source.route}`, async ({ page, request }) => {
    await page.goto(sitePath(source.route), { waitUntil: "networkidle" });
    const origin = new URL(page.url()).origin;
    const hrefs = await page.locator(source.selector).evaluateAll((links) => links.map((link) => link.getAttribute("href")));
    expect(hrefs.length, `${source.selector} did not find any links`).toBeGreaterThan(0);
    expect(hrefs, "navigation contains an empty or placeholder link").not.toContain(null);
    expect(hrefs, "navigation contains an empty or placeholder link").not.toContain("");
    expect(hrefs, "navigation contains a placeholder fragment").not.toContain("#");

    for (const url of internalLinks(hrefs, origin)) {
      if (PATH_PREFIX) expect(url.pathname, `${url.href} escapes the project base path`).toMatch(new RegExp(`^${PATH_PREFIX}(?:/|$)`));
      const response = await request.get(url.href);
      expect(response.status(), `${url.href} did not resolve successfully`).toBeLessThan(400);
      if (url.hash) {
        await page.goto(url.href, { waitUntil: "domcontentloaded" });
        await expect(page.locator(url.hash), `${url.href} points to a missing section`).toHaveCount(1);
      }
    }
  });
}

test("category filter updates catalogue results", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  const mobileFilters = page.viewportSize().width <= 820;
  if (mobileFilters) await page.locator("[data-filter-open]").click();
  const filters = page.locator(`${mobileFilters ? "#filter-dialog" : ".filter-sidebar"} [data-catalogue-form]`);
  await filters.locator("input[name='category'][value='fingerprint']").check();
  await Promise.all([
    page.waitForURL(/category=fingerprint/),
    filters.getByRole("button", { name: "تطبيق الفلاتر" }).click(),
  ]);
  await expect(page.locator("[data-product-card]")).toHaveCount(3);
  await expect(page.locator("[data-result-count]")).toHaveText("3");
});

test("price sorting puts the lowest-priced product first", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator("[data-sort-form] select").selectOption("price-asc");
  await page.waitForURL(/sort=price-asc/);
  await expect(page.locator("[data-product-card] h3").first()).toContainText("جسر زاكي ميني");
});

test("pagination shows the second catalogue page", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator(".pagination a").getByText("2", { exact: true }).click();
  await expect(page.locator("[data-product-card]")).toHaveCount(3);
});

test("search renders a genuine no-results state", async ({ page }) => {
  await page.goto(sitePath("/search/?q=نتيجة-غير-موجودة"), { waitUntil: "networkidle" });
  await expect(page.locator(".state-panel")).toContainText("لا توجد نتائج");
  await expect(page.locator("[data-result-count]")).toHaveText("0");
});

test("available filter includes limited stock and excludes unavailable products", async ({ page }) => {
  await page.goto(sitePath("/shop/?availability=available"), { waitUntil: "networkidle" });
  await expect(page.locator("[data-product-id='product-elite']")).toHaveCount(1);
  await expect(page.locator("[data-product-id='product-orbit']")).toHaveCount(1);
  await expect(page.locator("[data-product-id='product-core']")).toHaveCount(0);
});

test("removing a collection preserves unrelated filters", async ({ page }) => {
  await page.goto(sitePath("/collections/smart-door-locks/?priceMin=3000&availability=available&page=2"), { waitUntil: "networkidle" });
  await page.locator("[data-filter-remove='collection']").click();
  await page.waitForURL((url) => url.pathname === sitePath("/shop/") && url.searchParams.get("priceMin") === "3000");
  expect(new URL(page.url()).searchParams.get("availability")).toBe("available");
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
});

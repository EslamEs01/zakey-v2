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

test("catalogue query controls produce real results", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  const filters = page.locator(".filter-sidebar [data-catalogue-form]");
  await filters.locator("input[name='category'][value='fingerprint']").check();
  await Promise.all([
    page.waitForURL(/category=fingerprint/),
    filters.getByRole("button", { name: "تطبيق الفلاتر" }).click(),
  ]);
  await expect(page.locator("[data-product-card]")).toHaveCount(3);
  await expect(page.locator("[data-result-count]")).toHaveText("3");

  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator("[data-sort-form] select").selectOption("price-asc");
  await page.waitForURL(/sort=price-asc/);
  await expect(page.locator("[data-product-card] h3").first()).toContainText("جسر زاكي ميني");

  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator(".pagination a").getByText("2", { exact: true }).click();
  await expect(page.locator("[data-product-card]")).toHaveCount(3);

  await page.goto(sitePath("/search/?q=نتيجة-غير-موجودة"), { waitUntil: "networkidle" });
  await expect(page.locator(".state-panel")).toContainText("لا توجد نتائج");
  await expect(page.locator("[data-result-count]")).toHaveText("0");
});

import { test, expect } from "@playwright/test";

const LINK_SOURCES = [
  { route: "/", selector: "header a, footer a, #mobile-menu a" },
  { route: "/shop/", selector: ".filter-sidebar a, #filter-dialog a" },
  { route: "/cart/", selector: "main a" },
];
const PATH_PREFIX = (process.env.ZAKEY_E2E_PATH_PREFIX || "").replace(/\/$/, "");

// `npm run test:pages` serves a *static export* — one pre-rendered HTML file per
// route, with no Django behind it. Query strings therefore do nothing there:
// `/shop/?category=fingerprint` returns the same bytes as `/shop/`, and there is
// no session, so no signed-in state exists at all.
//
// Filtering, sorting, pagination, search and the account journey are all
// server-rendered (T-1602). Asserting them against a snapshot asserts something
// the artifact cannot do by construction, so those tests are registered only
// when a server is present. They are *not* skipped — in static mode they are
// never collected, so the run reports no phantom skips — and they still run in
// full against the live server via `npm run test:e2e`.
//
// What the static export CAN prove is asserted below instead: every link
// resolves, nothing escapes the base path, and the exported pages carry their
// real catalogue content.
const STATIC_EXPORT = Boolean(PATH_PREFIX);

function sitePath(route) {
  return `${PATH_PREFIX}${route}` || "/";
}

/** Register a test that needs a live server. */
function serverTest(name, fn) {
  if (!STATIC_EXPORT) test(name, fn);
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

serverTest("category filter updates catalogue results", async ({ page }) => {
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

serverTest("price sorting puts the lowest-priced product first", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator("[data-sort-form] select").selectOption("price-asc");
  await page.waitForURL(/sort=price-asc/);
  await expect(page.locator("[data-product-card] h3").first()).toContainText("جسر زاكي ميني");
});

serverTest("pagination shows the second catalogue page", async ({ page }) => {
  await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
  await page.locator(".pagination a").getByText("2", { exact: true }).click();
  await expect(page.locator("[data-product-card]")).toHaveCount(3);
});

serverTest("search renders a genuine no-results state", async ({ page }) => {
  await page.goto(sitePath("/search/?q=نتيجة-غير-موجودة"), { waitUntil: "networkidle" });
  await expect(page.locator(".state-panel")).toContainText("لا توجد نتائج");
  await expect(page.locator("[data-result-count]")).toHaveText("0");
});

serverTest("available filter includes limited stock and excludes unavailable products", async ({ page }) => {
  await page.goto(sitePath("/shop/?availability=available"), { waitUntil: "networkidle" });
  await expect(page.locator("[data-product-id='product-elite']")).toHaveCount(1);
  await expect(page.locator("[data-product-id='product-orbit']")).toHaveCount(1);
  await expect(page.locator("[data-product-id='product-core']")).toHaveCount(0);
});

serverTest("removing a collection preserves unrelated filters", async ({ page }) => {
  await page.goto(sitePath("/collections/smart-door-locks/?priceMin=3000&availability=available&page=2"), { waitUntil: "networkidle" });
  await page.locator("[data-filter-remove='collection']").click();
  await page.waitForURL((url) => url.pathname === sitePath("/shop/") && url.searchParams.get("priceMin") === "3000");
  expect(new URL(page.url()).searchParams.get("availability")).toBe("available");
  expect(new URL(page.url()).searchParams.has("page")).toBe(false);
});


serverTest("signed-in account navigation links all resolve", async ({ page, request }) => {
  const stamp = Date.now();
  await page.goto(sitePath("/account/"));
  await page.locator("[data-register-form] [name='full_name']").fill("ندى إبراهيم");
  await page.locator("[data-register-form] [name='email']").fill(`nav${stamp}@e2e.zakey.invalid`);
  await page.locator("[data-register-form] [name='mobile']").fill("01012345678");
  await page.locator("[data-register-form] [name='password']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] [name='password_confirm']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] button[type='submit']").click();

  const hrefs = await page
    .locator(".account-nav a")
    .evaluateAll((links) => links.map((link) => link.getAttribute("href")));
  expect(hrefs.length, "signed-in account navigation has no links").toBeGreaterThan(0);
  expect(hrefs, "account navigation contains a placeholder link").not.toContain("#");

  const origin = new URL(page.url()).origin;
  for (const url of internalLinks(hrefs, origin)) {
    const response = await request.get(url.href);
    expect(response.status(), `${url.href} did not resolve`).toBeLessThan(400);
  }
});


// ---------------------------------------------------------------------------
// Static-export coverage — what a server-less snapshot can genuinely prove
// ---------------------------------------------------------------------------

if (STATIC_EXPORT) {
  test("the exported catalogue page carries real product content", async ({ page }) => {
    await page.goto(sitePath("/shop/"), { waitUntil: "networkidle" });
    const cards = page.locator("[data-product-card]");
    await expect(cards, "the exported shop page rendered no products").not.toHaveCount(0);
    // The export must contain the real catalogue, not an empty shell that a
    // client-side script would have had to populate.
    await expect(page.locator("[data-product-card] h3").first()).not.toBeEmpty();
  });

  test("the exported pages contain no unrendered template syntax", async ({ page }) => {
    for (const route of ["/", "/shop/", "/cart/", "/contact/", "/account/"]) {
      await page.goto(sitePath(route), { waitUntil: "domcontentloaded" });
      const text = await page.locator("body").innerText();
      expect(text, `${route} leaked template syntax`).not.toMatch(/\{\{|\{%/);
    }
  });

  test("every exported asset reference resolves under the base path", async ({ page, request }) => {
    await page.goto(sitePath("/"), { waitUntil: "networkidle" });
    const origin = new URL(page.url()).origin;
    const srcs = await page
      .locator("img[src], script[src], link[rel='stylesheet'][href]")
      .evaluateAll((nodes) =>
        nodes.map((n) => n.getAttribute("src") || n.getAttribute("href")),
      );
    expect(srcs.length, "the exported page references no assets at all").toBeGreaterThan(0);
    for (const url of internalLinks(srcs.filter(Boolean), origin)) {
      expect(url.pathname, `${url.href} escapes the project base path`).toMatch(
        new RegExp(`^${PATH_PREFIX}(?:/|$)`),
      );
      const response = await request.get(url.href);
      expect(response.status(), `${url.href} did not resolve`).toBeLessThan(400);
    }
  });
}

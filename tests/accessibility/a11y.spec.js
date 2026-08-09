import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

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

for (const route of ROUTES) {
  test(`${route.id}`, async ({ page }) => {
    const response = await page.goto(route.path, { waitUntil: "networkidle" });
    expect(response, "route produced no response").not.toBeNull();
    expect(response.status()).toBe(route.expectedStatus ?? 200);
    await expect(page.locator("main")).toBeVisible();
    const axe = await new AxeBuilder({ page }).analyze();
    const material = axe.violations
      .filter((violation) => ["critical", "serious"].includes(violation.impact))
      .map(({ id, impact, description, nodes }) => ({
        id,
        impact,
        description,
        targets: nodes.map((node) => node.target),
      }));
    expect(material, "critical or serious axe violations").toEqual([]);
  });
}

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { mkdir, writeFile } from "node:fs/promises";
import { readFileSync } from "node:fs";
import path from "node:path";

const root = process.cwd();
const matrix = JSON.parse(readFileSync(path.join(root, "specs/003-zakey-frontend-reference-build/contracts/qa-matrix.json"), "utf8"));
const fixture = JSON.parse(readFileSync(path.join(root, "storefront/fixtures/frontend-fixtures.json"), "utf8"));
const screenshotDirectory = path.join(root, "specs/003-zakey-frontend-reference-build/qa/implementation-screenshots");
const htmlDirectory = path.join(root, "specs/003-zakey-frontend-reference-build/qa/rendered-html");
const htmlOnly = process.env.ZAKEY_HTML_ONLY === "1";

function storageEnvelope(setup = {}) {
  const populatedCart = fixture.prototypeCarts.find((state) => state.id === "cart-populated");
  const populatedWishlist = fixture.prototypeWishlists.find((state) => state.id === "wishlist-populated");
  const useCart = setup.fixture === "populated-cart";
  const useWishlist = setup.fixture === "populated-wishlist";
  return {
    version: 1,
    cart: {
      items: useCart ? populatedCart.lineItems.map(({ productId, quantity, finishId }) => ({ productId, quantity, finishId: finishId || "default" })) : [],
      coupon: "",
    },
    wishlist: { productIds: useWishlist ? populatedWishlist.productIds : [] },
    account: { mode: "signed-out", tab: "orders" },
  };
}

async function performAction(page, action) {
  const actions = {
    "open-mobile-menu": async () => {
      await page.locator("#mobile-menu").evaluate((dialog) => dialog.showModal());
      await expect(page.locator("#mobile-menu")).toHaveAttribute("open", "");
    },
    "open-search": async () => {
      await page.locator("[data-search-trigger]").click();
      await expect(page.locator("#header-search")).toBeVisible();
      await expect(page.locator("#global-search")).toBeFocused();
    },
    "open-products-menu": async () => {
      if (page.viewportSize().width <= 820) {
        await page.locator("#mobile-menu").evaluate((dialog) => dialog.showModal());
        await page.locator("#mobile-menu details").evaluate((details) => { details.open = true; });
        await expect(page.locator("#mobile-menu details")).toHaveAttribute("open", "");
      } else {
        await page.locator("[data-products-menu-trigger]").click();
        await expect(page.locator("[data-products-menu-trigger]")).toHaveAttribute("aria-expanded", "true");
        await expect(page.locator("#products-menu")).toBeVisible();
      }
    },
    "hover-first-product-card": async () => page.locator("[data-product-card]").first().hover(),
    "keyboard-focus-first-primary-action": async () => {
      await page.locator(".hero-actions .btn").first().focus();
      await expect(page.locator(".hero-actions .btn").first()).toBeFocused();
    },
    "submit-empty-newsletter": async () => {
      await page.locator("[data-prototype-form='newsletter'] button[type='submit']").click();
      await expect(page.locator("#newsletter-error")).toBeVisible();
    },
    "open-filter-drawer": async () => {
      await page.locator("#filter-dialog").evaluate((dialog) => dialog.showModal());
      await expect(page.locator("#filter-dialog")).toHaveAttribute("open", "");
    },
    "select-second-thumbnail": async () => {
      await page.locator("[data-gallery-image]").nth(1).click();
      await expect(page.locator("[data-gallery-image]").nth(1)).toHaveAttribute("aria-pressed", "true");
    },
    "open-first-faq": async () => {
      await page.locator("#panel-faq details").first().evaluate((details) => { details.open = true; });
      await expect(page.locator("#panel-faq details").first()).toHaveAttribute("open", "");
    },
    "toggle-wishlist": async () => {
      await page.locator("[data-product-id] [data-wishlist-toggle]").first().click();
      await expect(page.locator("[data-product-id] [data-wishlist-toggle]").first()).toHaveAttribute("aria-pressed", "true");
    },
    "submit-empty-shipping": async () => {
      await page.locator("[data-checkout-next]").click();
      await expect(page.locator("[data-error-summary]")).toBeVisible();
    },
    "submit-empty-contact": async () => {
      await page.locator("[data-contact-submit]").click();
      await expect(page.locator("#contact-name-error")).toBeVisible();
    },
  };
  const execute = actions[action];
  expect(execute, `QA matrix contains unknown action: ${action}`).toBeDefined();
  await execute();
}

function isExpectedErrorRouteMessage(message, routeId) {
  if (!["404", "5xx"].includes(routeId)) return false;
  const expectedStatus = routeId === "404" ? "404" : "500";
  return message.includes("Failed to load resource") && message.includes(expectedStatus);
}

async function assertNamedState(page, state) {
  const checks = {
    "search-no-results": [".state-panel", /لا توجد نتائج/],
    "shop-no-filtered-results": [".state-panel", /لا توجد منتجات/],
    "catalogue-loading": [".catalogue-results", /./],
    "catalogue-error": [".state-panel", /تعذّر/],
    "product-unavailable": [".availability--off", /غير متاح/],
    "cart-empty": ["[data-cart-empty]", /سلتك|السلة/],
    "wishlist-empty": ["[data-wishlist-empty]", /المفضلة/],
    "account-signed-out": ["[data-account-signed-out]", /تسجيل|حساب/],
  };
  const check = checks[state.id];
  if (check) await expect(page.locator(check[0])).toContainText(check[1]);
}

for (const state of matrix.states) {
  test(`${state.id}`, async ({ page }, testInfo) => {
    const width = Number(testInfo.project.name.replace("chrome-", ""));
    const consoleErrors = [];
    const pageErrors = [];
    const failedAssets = [];
    page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
    page.on("pageerror", (error) => pageErrors.push(error.message));
    page.on("response", (response) => {
      if (response.status() >= 400 && /\/static\//.test(response.url())) failedAssets.push(`${response.status()} ${response.url()}`);
    });
    await page.addInitScript((envelope) => localStorage.setItem("zakey:prototype:v1", JSON.stringify(envelope)), storageEnvelope(state.setup));
    if (state.setup.reducedMotion === "reduce") await page.emulateMedia({ reducedMotion: "reduce" });
    const response = await page.goto(state.route, { waitUntil: htmlOnly ? "domcontentloaded" : "networkidle" });
    expect(response, "route produced no response").not.toBeNull();
    if (state.routeId === "404") expect(response.status()).toBe(404);
    else if (state.routeId === "5xx") expect(response.status()).toBe(500);
    else expect(response.status()).toBe(200);
    for (const action of state.setup.actions || []) await performAction(page, action);
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("main")).toBeVisible();
    await expect(page.locator("h1").first()).toBeVisible();
    await expect(page.locator("body")).not.toContainText(/Lorem Ipsum|\{\{|%\}/);
    await assertNamedState(page, state);
    if (!htmlOnly) {
      await page.locator("img").evaluateAll(async (images) => {
        for (const image of images) image.loading = "eager";
        await Promise.all(images.map((image) => image.complete
          ? Promise.resolve()
          : new Promise((resolve) => {
            image.addEventListener("load", resolve, { once: true });
            image.addEventListener("error", resolve, { once: true });
          })));
      });
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, "horizontal overflow").toBeLessThanOrEqual(1);
      const brokenImages = await page.locator("img").evaluateAll((images) => images.filter((image) => !image.complete || image.naturalWidth === 0).map((image) => image.getAttribute("src")));
      expect(brokenImages, "broken images").toEqual([]);
      const emptyLinks = await page.locator("a").evaluateAll((links) => links.filter((link) => !link.getAttribute("href") || link.getAttribute("href") === "#").map((link) => link.outerHTML));
      expect(emptyLinks, "empty anchors").toEqual([]);
      const axe = await new AxeBuilder({ page }).analyze();
      const material = axe.violations.filter((violation) => ["critical", "serious"].includes(violation.impact));
      expect(material, "critical or serious axe violations").toEqual([]);
      await mkdir(screenshotDirectory, { recursive: true });
      await page.screenshot({ path: path.join(screenshotDirectory, `${state.routeId}__${state.id}__${width}.png`), fullPage: true, animations: "disabled", timeout: 120_000 });
    }
    await mkdir(htmlDirectory, { recursive: true });
    await writeFile(path.join(htmlDirectory, `${state.routeId}__${state.id}__${width}.html`), await page.content(), "utf8");
    expect(
      consoleErrors.filter((message) => !isExpectedErrorRouteMessage(message, state.routeId)),
      "browser console errors",
    ).toEqual([]);
    expect(pageErrors, "browser page errors").toEqual([]);
    expect(failedAssets, "failed local assets").toEqual([]);
  });
}

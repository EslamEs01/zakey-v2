import { test, expect } from "@playwright/test";


test("search and responsive navigation use their visible controls", async ({ page }) => {
  await page.goto("/");
  const searchTrigger = page.locator("[data-search-trigger]");
  await searchTrigger.click();
  await expect(page.locator("#global-search")).toBeFocused();
  await page.locator("#global-search").fill("أبيكس");
  await page.locator("#header-search button[type='submit']").click();
  await expect(page).toHaveURL(/\/search\/\?q=/);
  await expect(page.locator("h1")).toContainText("نتائج البحث");

  await page.goto("/");
  if (page.viewportSize().width <= 820) {
    const menuTrigger = page.locator("[data-mobile-menu-trigger]");
    await menuTrigger.click();
    await expect(page.locator("#mobile-menu")).toHaveAttribute("open", "");
    await page.locator("#mobile-menu [data-dialog-close]").click();
    await expect(page.locator("#mobile-menu")).not.toHaveAttribute("open", "");
    await expect(menuTrigger).toBeFocused();
  } else {
    const productsTrigger = page.locator("[data-products-menu-trigger]");
    await productsTrigger.click();
    await expect(productsTrigger).toHaveAttribute("aria-expanded", "true");
    await page.keyboard.press("Escape");
    await expect(productsTrigger).toHaveAttribute("aria-expanded", "false");
  }
});

test("catalogue filters, chips, sorting, and pagination change results", async ({ page }) => {
  await page.goto("/shop/");
  let filterForm;
  if (page.viewportSize().width <= 820) {
    const filterTrigger = page.locator("[data-filter-open]");
    await filterTrigger.click();
    await page.keyboard.press("Escape");
    await expect(page.locator("#filter-dialog")).not.toHaveAttribute("open", "");
    await expect(filterTrigger).toBeFocused();
    await filterTrigger.click();
    filterForm = page.locator("#filter-dialog [data-catalogue-form]");
  } else {
    filterForm = page.locator(".filter-sidebar [data-catalogue-form]");
  }
  await filterForm.locator("input[name='category'][value='fingerprint']").check();
  await filterForm.locator("button[type='submit']").click();
  await expect(page).toHaveURL(/category=fingerprint/);
  await expect(page.locator(".active-filters")).toContainText("أقفال بالبصمة");
  await page.locator("[data-filter-remove='category']").click();
  await expect(page).not.toHaveURL(/category=fingerprint/);

  await page.goto("/shop/");
  await page.locator("#catalogue-sort").selectOption("price-desc");
  await expect(page).toHaveURL(/sort=price-desc/);
  await page.getByRole("link", { name: "2", exact: true }).click();
  await expect(page).toHaveURL(/page=2/);
});

test("product controls synchronize gallery, tabs, wishlist, quantity, and cart", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-gallery-image]").nth(1).click();
  await expect(page.locator("[data-gallery-image]").nth(1)).toHaveAttribute("aria-pressed", "true");
  await page.locator("#tab-specifications").click();
  await expect(page.locator("#panel-specifications")).toBeVisible();
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator("#tab-downloads")).toHaveAttribute("aria-selected", "true");
  await page.locator("[data-quantity-plus]").click();
  await expect(page.locator("[data-quantity]")).toHaveValue("2");
  await page.locator("[data-wishlist-toggle]").first().click();
  await expect(page.locator("[data-wishlist-toggle]").first()).toHaveAttribute("aria-pressed", "true");
  await page.locator("[data-add-product]").click();
  await page.locator("[data-cart-link]").click();
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);
  await expect(page.locator("[data-cart-quantity]")).toHaveText("2");
});

test("cart quantity, coupon, and removal controls update observable state", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-add-product]").click();
  await page.goto("/cart/");
  await page.locator("[data-cart-increase]").click();
  await expect(page.locator("[data-cart-quantity]")).toHaveText("2");
  await page.locator("#coupon-code").fill("ZAKEYDEMO");
  await page.locator("[data-coupon-submit]").click();
  await expect(page.locator("[data-coupon-status]")).toContainText("تم تطبيق");
  await page.locator("[data-cart-remove]").click();
  await expect(page.locator("[data-cart-empty]")).toBeVisible();
});

test("checkout validates Egypt fields and ends in an unavailable prototype state", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-buy-product]").click();
  await expect(page).toHaveURL(/\/checkout\/$/);
  const form = page.locator("[data-shipping-form]");
  await form.locator("[name='fullName']").fill("أحمد محمود");
  await form.locator("[name='email']").fill("ahmed@example.com");
  await form.locator("[name='mobile']").fill("01012345678");
  await form.locator("[name='governorate']").selectOption("cairo");
  await form.locator("[name='city']").fill("القاهرة");
  await form.locator("[name='street']").fill("١٢ شارع النصر، مدينة نصر");
  await form.locator("[name='building']").fill("١٢");
  await form.locator("[data-shipping-option='shipping-standard']").click();
  await form.locator("[name='acknowledgement']").check();
  await form.locator("[data-checkout-next]").click();
  await expect(page.locator("[data-checkout-panel='payment']")).toBeVisible();
  await page.locator(".checkout-choice--payment").first().click();
  await page.locator("[data-payment-form] button[type='submit']").click();
  await expect(page.locator("[data-checkout-panel='review']")).toBeVisible();
  await page.locator("[data-checkout-final]").click();
  await expect(page.locator("[data-final-state]")).toContainText("غير متاح");
  await expect(page.locator("[data-final-state]")).toContainText("لم يتم إنشاء طلب");
});

test("account tabs and signed-out recovery remain explicit prototype navigation", async ({ page }) => {
  await page.goto("/account/?state=signed-in&tab=orders");
  await page.locator("[data-account-tab-id='addresses']").click();
  await expect(page.locator("[data-account-tab-id='addresses']")).toHaveAttribute("aria-selected", "true");
  await expect(page.locator("[data-account-panel-id='addresses']")).toBeVisible();
  await page.locator("[data-account-tab-id='settings']").click();
  await expect(page.locator("[data-account-panel-id='settings']")).toBeVisible();
  await page.locator(".account-signout").click();
  await expect(page).toHaveURL(/state=signed-out/);
  await expect(page.locator("[data-account-signed-out]")).toBeVisible();
});

test("error pages expose working recovery destinations", async ({ page }) => {
  const response = await page.goto("/errors/404/");
  expect(response.status()).toBe(404);
  await page.locator("main a[href='/shop/']").first().click();
  await expect(page).toHaveURL(/\/shop\/$/);
  const serverResponse = await page.goto("/errors/500/");
  expect(serverResponse.status()).toBe(500);
  await page.locator("main a[href='/']").first().click();
  await expect(page).toHaveURL(/\/$/);
});

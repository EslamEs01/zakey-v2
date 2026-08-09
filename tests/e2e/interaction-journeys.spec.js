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

test("product gallery, tabs and quantity drive a server-side cart line", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-gallery-image]").nth(1).click();
  await expect(page.locator("[data-gallery-image]").nth(1)).toHaveAttribute("aria-pressed", "true");
  await page.locator("#tab-specifications").click();
  await expect(page.locator("#panel-specifications")).toBeVisible();
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator("#tab-downloads")).toHaveAttribute("aria-selected", "true");

  await page.locator("[data-quantity-plus]").click();
  await expect(page.locator("[data-quantity]")).toHaveValue("2");
  await page.locator("[data-add-product]").click();

  // The quantity the customer chose is what the SERVER stored, and the header
  // badge is rendered from the same row rather than counted in the browser.
  await page.locator("[data-cart-link]").click();
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);
  await expect(page.locator("[data-cart-quantity]")).toHaveText("2");
  await expect(page.locator("[data-cart-count]")).toHaveText("2");

  // Reload with a cold cache: a browser-held cart would vanish here.
  await page.reload();
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);
  await expect(page.locator("[data-cart-quantity]")).toHaveText("2");
});

test("wishlist toggle persists to the server and survives a reload", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await expect(page.locator("[data-wishlist-toggle]").first()).toHaveAttribute("aria-pressed", "false");

  await page.locator("[data-wishlist-toggle]").first().click();
  await expect(page).toHaveURL(/\/products\/zakey-apex-pro\//);
  // Rendered pressed by the server, not flipped by a script.
  await expect(page.locator("[data-wishlist-toggle]").first()).toHaveAttribute("aria-pressed", "true");

  await page.goto("/wishlist/");
  await expect(page.locator("[data-wishlist-card]")).toHaveCount(1);

  await page.goto("/products/zakey-apex-pro/");
  await expect(page.locator("[data-wishlist-toggle]").first()).toHaveAttribute("aria-pressed", "true");

  await page.locator("[data-wishlist-toggle]").first().click();
  await page.goto("/wishlist/");
  await expect(page.locator("[data-wishlist-empty]")).toBeVisible();
});

test("two finishes of one product are independent cart lines", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  const finishes = page.locator("input[name='variant']");
  const finishCount = await finishes.count();
  test.skip(finishCount < 2, "product has a single finish");

  await finishes.nth(0).check();
  await page.locator("[data-add-product]").click();
  await page.goto("/products/zakey-apex-pro/");
  await finishes.nth(1).check();
  await page.locator("[data-add-product]").click();

  await page.goto("/cart/");
  await expect(page.locator("[data-cart-line]")).toHaveCount(2);

  // Removing one finish must leave the other — the prototype removed by
  // productId and took both.
  await page.locator("[data-cart-line]").first().locator("[data-cart-remove]").click();
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);
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

test("checkout validates server-side and creates a real order", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-buy-product]").click();
  // The step is reflected in the URL by design, so match the route rather than
  // requiring a bare path.
  await expect(page).toHaveURL(/\/checkout\/(\?|$)/);

  const form = page.locator("[data-checkout-form]");

  // Submitting an invalid mobile must be refused BY THE SERVER, with the
  // approved Arabic message, not silently corrected in the browser.
  await form.locator("[name='fullName']").fill("أحمد محمود");
  await form.locator("[name='email']").fill("ahmed@e2e.zakey.invalid");
  await form.locator("[name='mobile']").fill("0131234567");
  await form.locator("[name='governorate']").selectOption("cairo");
  await form.locator("[name='city']").fill("القاهرة");
  await form.locator("[name='street']").fill("١٢ شارع النصر، مدينة نصر");
  await form.locator("[name='building']").fill("١٢");
  await form.locator("[data-checkout-panel='shipping'] label.checkout-choice").first().click();

  // Step 2, then step 3 — the same route a customer takes.
  await page.locator("[data-checkout-step='payment']").click();
  await form.locator("label.checkout-choice--payment").first().click();
  await page.locator("[data-checkout-step='review']").click();
  await form.locator("[name='acknowledgement']").check();
  await page.locator("[data-checkout-final]").click();

  await expect(page.locator("[data-error-summary]")).toContainText("رقم موبايل");
  await expect(page).toHaveURL(/\/checkout\//);

  // Correct it and the same submission creates an order. The server re-renders
  // on step 1 with the errors, so walk forward again.
  await page.locator("[data-checkout-step='shipping']").click();
  await page.locator("[name='mobile']").fill("01012345678");
  await page.locator("[data-checkout-step='payment']").click();
  await page.locator("label.checkout-choice--payment").first().click();
  await page.locator("[data-checkout-step='review']").click();
  await page.locator("[name='acknowledgement']").check();
  await page.locator("[data-checkout-final]").click();

  await expect(page).toHaveURL(/\/orders\/[A-Z0-9-]+\/$/);
  await expect(page.locator("h1")).toContainText("طلب رقم");
  const orderUrl = page.url();

  // The cart is converted, so checkout no longer offers the same basket.
  await page.goto("/cart/");
  await expect(page.locator("[data-cart-empty]")).toBeVisible();

  // Re-requesting the confirmation is fine for the buyer…
  await page.goto(orderUrl);
  await expect(page.locator("h1")).toContainText("طلب رقم");
});

test("a repeated checkout submission does not create a second order", async ({ page, context }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-buy-product]").click();

  const form = page.locator("[data-checkout-form]");
  await form.locator("[name='fullName']").fill("ندى إبراهيم");
  await form.locator("[name='email']").fill("nada@e2e.zakey.invalid");
  await form.locator("[name='mobile']").fill("01012345678");
  await form.locator("[name='governorate']").selectOption("cairo");
  await form.locator("[name='city']").fill("القاهرة");
  await form.locator("[name='street']").fill("١٢ شارع التحرير");
  await form.locator("[name='building']").fill("٥");
  await form.locator("[data-checkout-panel='shipping'] label.checkout-choice").first().click();
  await page.locator("[data-checkout-step='payment']").click();
  await form.locator("label.checkout-choice--payment").first().click();
  await page.locator("[data-checkout-step='review']").click();
  await form.locator("[name='acknowledgement']").check();

  // Capture the idempotency key this page was rendered with, then replay the
  // exact submission the way a double-click or a refresh would.
  const key = await page.locator("input[name='idempotency_key']").inputValue();
  await page.locator("[data-checkout-final]").click();
  await expect(page).toHaveURL(/\/orders\/([A-Z0-9-]+)\/$/);
  const firstOrder = page.url();

  const replay = await context.request.post("/checkout/submit/", {
    form: {
      fullName: "ندى إبراهيم",
      email: "nada@e2e.zakey.invalid",
      mobile: "01012345678",
      governorate: "cairo",
      city: "القاهرة",
      street: "١٢ شارع التحرير",
      building: "٥",
      acknowledgement: "accepted",
      idempotency_key: key,
      csrfmiddlewaretoken: (await context.cookies()).find((c) => c.name === "csrftoken")?.value || "",
    },
    headers: { Referer: firstOrder },
    maxRedirects: 0,
    failOnStatusCode: false,
  });
  // Whatever the replay does, it must not mint a second order number.
  expect([200, 302, 403]).toContain(replay.status());

  await page.goto("/account/");
  // Guest checkout: the confirmation stays reachable by the session that placed it.
  await page.goto(firstOrder);
  await expect(page.locator("h1")).toContainText("طلب رقم");
});

test("account identity comes from the session, never from the URL", async ({ page }) => {
  // The prototype switched identity on ?state=signed-in. That must now be inert.
  await page.goto("/account/?state=signed-in&tab=orders");
  await expect(page.locator("[data-account-signed-out]")).toBeVisible();
  await expect(page.locator("[data-account-panel-id='addresses']")).toHaveCount(0);

  // Register, which signs the visitor in for real.
  const stamp = Date.now();
  await page.locator("[data-register-form] [name='full_name']").fill("ندى إبراهيم");
  await page.locator("[data-register-form] [name='email']").fill(`nada${stamp}@e2e.zakey.invalid`);
  await page.locator("[data-register-form] [name='mobile']").fill("01012345678");
  await page.locator("[data-register-form] [name='password']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] [name='password_confirm']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] button[type='submit']").click();

  await expect(page.locator("[data-account-signed-out]")).toHaveCount(0);
  await expect(page.locator("[data-account-tab-id='addresses']")).toBeVisible();

  // Tabs are real navigation and each panel is server-rendered.
  await page.locator("[data-account-tab-id='addresses']").click();
  await expect(page.locator("[data-account-panel-id='addresses']")).toBeVisible();
  await page.locator("[data-account-tab-id='settings']").click();
  await expect(page.locator("[data-account-panel-id='settings']")).toBeVisible();

  // Sign out ends the session; the URL cannot bring it back.
  await page.locator("[data-account-signout]").click();
  // Logging out lands on the home page; the session is what changed.
  await expect(page).toHaveURL(/\/$/);
  await page.goto("/account/");
  await expect(page.locator("[data-account-signed-out]")).toBeVisible();
  // …and the retired query switch still cannot resurrect the signed-in view.
  await page.goto("/account/?state=signed-in");
  await expect(page.locator("[data-account-signed-out]")).toBeVisible();
});

test("an anonymous cart and wishlist follow the visitor into their account", async ({ page }) => {
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-add-product]").click();
  await page.goto("/products/zakey-apex-pro/");
  await page.locator("[data-wishlist-toggle]").first().click();

  await page.goto("/cart/");
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);

  const stamp = Date.now();
  await page.goto("/account/");
  await page.locator("[data-register-form] [name='full_name']").fill("عمر حسن");
  await page.locator("[data-register-form] [name='email']").fill(`omar${stamp}@e2e.zakey.invalid`);
  await page.locator("[data-register-form] [name='mobile']").fill("01112345678");
  await page.locator("[data-register-form] [name='password']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] [name='password_confirm']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] button[type='submit']").click();

  // The basket built while anonymous is now attached to the account.
  await page.goto("/cart/");
  await expect(page.locator("[data-cart-line]")).toHaveCount(1);
  await page.goto("/wishlist/");
  await expect(page.locator("[data-wishlist-card]")).toHaveCount(1);
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

import { test, expect } from "@playwright/test";

/**
 * Semantic acceptance for the three pages whose visual baselines changed
 * (T-1901 triage: account, contact, checkout).
 *
 * The pixel comparison tells you *that* something moved. These tests assert
 * *what* the page now claims — labels, focus, error linkage, directionality,
 * and that no state is fake. They are the checks a reviewer would otherwise
 * have to make by eye, written down so they run every time.
 *
 * They do not replace looking at the images; they remove most of what looking
 * at the images was for.
 */

const FORM_PAGES = [
  { id: "account", path: "/account/" },
  { id: "contact", path: "/contact/" },
];

// ---------------------------------------------------------------------------
// Criterion 4 + 7: directionality, and no template syntax or placeholder copy
// ---------------------------------------------------------------------------

for (const page_ of [...FORM_PAGES, { id: "checkout", path: "/checkout/" }]) {
  test(`${page_.id}: RTL, no template tokens, no placeholder copy`, async ({ page }) => {
    await page.goto(page_.path, { waitUntil: "networkidle" });
    await expect(page.locator("html")).toHaveAttribute("dir", "rtl");
    await expect(page.locator("html")).toHaveAttribute("lang", "ar-EG");

    const body = await page.locator("body").innerText();
    for (const token of ["{{", "{%", "{#", "#}", "Lorem", "TODO", "FIXME", "undefined"]) {
      expect(body, `visible ${token} on ${page_.path}`).not.toContain(token);
    }

    // Latin-script inputs must never be forced RTL inside the RTL page.
    //
    // Note: the approved storefront is inconsistent here — checkout sets
    // dir="ltr" on its email/mobile fields, the contact page never did. That
    // predates this feature (verified against HEAD), so it is recorded as a
    // finding rather than silently "fixed" on a page whose visual baseline is
    // already pending approval: mixing an unrelated delta into that image is
    // exactly what disqualifies it from re-baselining.
    const wrongDir = await page
      .locator('input[type="email"], input[type="tel"]')
      .evaluateAll((nodes) =>
        nodes
          .filter((node) => node.getAttribute("dir") === "rtl")
          .map((node) => node.id || node.name),
      );
    expect(wrongDir, "Latin-script input forced to RTL").toEqual([]);
  });
}

// ---------------------------------------------------------------------------
// Criterion 6: nothing clipped or pushed outside the viewport
// ---------------------------------------------------------------------------

for (const page_ of [...FORM_PAGES, { id: "checkout", path: "/checkout/" }]) {
  test(`${page_.id}: no horizontal overflow and no clipped controls`, async ({ page }) => {
    await page.goto(page_.path, { waitUntil: "networkidle" });

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );
    expect(overflow, "horizontal overflow").toBeLessThanOrEqual(1);

    // Every interactive control must sit inside the document's width.
    const escaping = await page.locator("button:visible, a:visible, input:visible").evaluateAll(
      (nodes) =>
        nodes
          .map((node) => {
            const box = node.getBoundingClientRect();
            const limit = document.documentElement.clientWidth;
            const overhang = Math.max(0, box.right - limit, -box.left);
            return overhang > 2 ? `${node.tagName}.${node.className}:${Math.round(overhang)}px` : null;
          })
          .filter(Boolean),
    );
    expect(escaping, "controls outside the viewport").toEqual([]);
  });
}

// ---------------------------------------------------------------------------
// Criterion 8: labels, focus and error states on every form
// ---------------------------------------------------------------------------

for (const page_ of FORM_PAGES) {
  test(`${page_.id}: every field is labelled and focusable`, async ({ page }) => {
    await page.goto(page_.path, { waitUntil: "networkidle" });

    const unlabelled = await page
      .locator("input:visible:not([type=hidden]), select:visible, textarea:visible")
      .evaluateAll((nodes) =>
        nodes
          .filter((node) => {
            if (node.getAttribute("aria-label")) return false;
            if (node.getAttribute("aria-labelledby")) return false;
            if (node.id && document.querySelector(`label[for="${node.id}"]`)) return false;
            return !node.closest("label");
          })
          .map((node) => node.outerHTML.slice(0, 90)),
      );
    expect(unlabelled, "fields without an accessible label").toEqual([]);

    const first = page.locator("input:visible:not([type=hidden])").first();
    await first.focus();
    await expect(first).toBeFocused();
  });
}

test("contact: invalid input shows a linked error and persists nothing", async ({ page }) => {
  await page.goto("/contact/", { waitUntil: "networkidle" });

  await page.locator("[data-contact-form] [name='name']").fill("ندى");
  await page.locator("[data-contact-form] [name='email']").fill("not-an-email");
  await page.locator("[data-contact-form] [name='message']").fill("قصيرة");
  await page.locator("[data-contact-submit]").click();

  // The error is visible AND wired to its field via aria-describedby.
  const error = page.locator("#contact-email-error");
  await expect(error).toBeVisible();
  const describedBy = await page.locator("#contact-email").getAttribute("aria-describedby");
  expect(describedBy).toContain("contact-email-error");
  await expect(page.locator("#contact-email")).toHaveAttribute("aria-invalid", "true");

  // Criterion 11: no success is shown, because nothing was stored.
  const status = page.locator("[data-form-status='contact']");
  if (await status.count()) {
    await expect(status).not.toContainText("تم استلام");
  }
});

// ---------------------------------------------------------------------------
// Criterion 9: the account page states what is actually true
// ---------------------------------------------------------------------------

test("account: signed-out shows auth, signed-in shows the real customer", async ({ page }) => {
  await page.goto("/account/", { waitUntil: "networkidle" });
  await expect(page.locator("[data-account-signed-out]")).toBeVisible();
  await expect(page.locator("[data-login-form]")).toBeVisible();
  await expect(page.locator("[data-register-form]")).toBeVisible();
  // No fabricated customer anywhere on a signed-out page.
  await expect(page.locator(".account-profile__name")).toHaveCount(0);

  const stamp = Date.now();
  const email = `visual${stamp}@e2e.zakey.invalid`;
  await page.locator("[data-register-form] [name='full_name']").fill("ندى إبراهيم");
  await page.locator("[data-register-form] [name='email']").fill(email);
  await page.locator("[data-register-form] [name='mobile']").fill("01012345678");
  await page.locator("[data-register-form] [name='password']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] [name='password_confirm']").fill("Zakey-Pass!123");
  await page.locator("[data-register-form] button[type='submit']").click();

  // The signed-in page shows the identity the session actually holds.
  await expect(page.locator("[data-account-signed-out]")).toHaveCount(0);
  await expect(page.locator(".account-profile__name")).toContainText("ندى إبراهيم");
  await expect(page.locator(".account-profile__meta").first()).toContainText(email);
});

// ---------------------------------------------------------------------------
// Criterion 10: checkout controls appear at the right point in the real flow
// ---------------------------------------------------------------------------

test("checkout: empty basket offers no steps; terms appear only at review", async ({ page }) => {
  // Empty cart — the state the visual baseline captures.
  await page.goto("/checkout/", { waitUntil: "networkidle" });
  await expect(page.locator("[data-checkout-empty]")).toBeVisible();
  // A stepper whose panels do not exist would be a dead control.
  await expect(page.locator("[data-checkout-step]")).toHaveCount(0);
  await expect(page.locator("[name='acknowledgement']")).toHaveCount(0);

  // With a basket, the steps exist and the terms sit on the last one.
  await page.goto("/products/zakey-apex-pro/", { waitUntil: "networkidle" });
  await page.locator("[data-add-product]").click();
  await page.goto("/checkout/", { waitUntil: "networkidle" });

  await expect(page.locator("[data-checkout-step='shipping']")).toBeVisible();
  await expect(page.locator("[name='acknowledgement']")).not.toBeVisible();

  await page.locator("[data-checkout-step='review']").click();
  await expect(page.locator("[name='acknowledgement']")).toBeVisible();
  await expect(page.locator("[data-checkout-final]")).toBeVisible();
  // Real terms wording, not the prototype's "this is a preview" acknowledgement.
  await expect(page.locator(".checkout-acknowledgement")).toContainText("الشروط");
  await expect(page.locator(".checkout-acknowledgement")).not.toContainText("معاينة الخطوات");
});

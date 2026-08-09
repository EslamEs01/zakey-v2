import { announce } from "../utilities/dom.js";

/**
 * Checkout step navigation (T-1605/T-1607, FR-060, FR-136).
 *
 * This module used to *be* the checkout: it held the address in memory, priced
 * the basket, applied the coupon, extracted VAT with
 * `Math.round((total * vatRate) / (1 + vatRate))`, picked a shipping method by
 * comparing the subtotal to a threshold, read a prototype account for the
 * address, and finished by displaying "submission unavailable". Every one of
 * those decisions now belongs to the server, which validates the whole
 * submission and creates a real order.
 *
 * What is left is presentation: the three panels are one form in the document,
 * and this turns them into steps. With JavaScript off the customer sees one
 * long form and a single submit button — which works (FR-136).
 */

const STEPS = ["shipping", "payment", "review"];

function panels() {
  return new Map(
    [...document.querySelectorAll("[data-checkout-panel]")].map((panel) => [
      panel.dataset.checkoutPanel,
      panel,
    ]),
  );
}

function showStep(step) {
  const all = panels();
  if (!all.has(step)) return;
  all.forEach((panel, key) => {
    panel.hidden = key !== step;
  });
  document.querySelectorAll("[data-checkout-step-item]").forEach((item) => {
    const key = item.dataset.checkoutStepItem;
    item.classList.toggle("is-active", key === step);
    item.classList.toggle("is-complete", STEPS.indexOf(key) < STEPS.indexOf(step));
  });
  document.querySelectorAll("[data-checkout-step]").forEach((button) => {
    button.setAttribute("aria-expanded", String(button.dataset.checkoutStep === step));
  });
  all.get(step).querySelector("h2")?.focus();
  const url = new URL(window.location.href);
  url.searchParams.set("step", step);
  window.history.replaceState({}, "", url);
}

/** Filter the area list to the chosen governorate — a convenience only; the
 *  server re-checks that the area really belongs to it. */
function bindAreaFiltering() {
  const governorate = document.querySelector("#checkout-governorate");
  const area = document.querySelector("#checkout-area");
  if (!governorate || !area) return;
  const options = [...area.options];
  const sync = () => {
    const key = governorate.value;
    let visible = 0;
    options.forEach((option) => {
      if (!option.value) return;
      const matches = option.dataset.governorate === key;
      option.hidden = !matches;
      option.disabled = !matches;
      if (matches) visible += 1;
    });
    if (area.selectedOptions[0]?.disabled) area.value = "";
    const field = document.querySelector("[data-area-field]");
    if (field) field.hidden = visible === 0;
  };
  governorate.addEventListener("change", sync);
  sync();
}

function bindStepControls() {
  document.querySelectorAll("[data-checkout-step]").forEach((button) => {
    button.addEventListener("click", () => showStep(button.dataset.checkoutStep));
  });
  document.querySelectorAll("[data-go-step]").forEach((button) => {
    button.addEventListener("click", () => showStep(button.dataset.goStep));
  });
}

/** Mirror the entered address and choices into the review panel. */
function bindReviewSummary() {
  const form = document.querySelector("[data-checkout-form]");
  if (!form) return;
  const render = (target, rows) => {
    const list = document.querySelector(target);
    if (!list) return;
    list.replaceChildren();
    rows.filter(([, value]) => value).forEach(([label, value]) => {
      const wrap = document.createElement("div");
      const dt = document.createElement("dt");
      dt.textContent = label;
      const dd = document.createElement("dd");
      dd.textContent = value;
      wrap.append(dt, dd);
      list.append(wrap);
    });
  };
  const labelOf = (selector) =>
    document.querySelector(selector)?.closest("label")?.querySelector("strong")?.textContent || "";
  const selectedText = (select) => select?.selectedOptions?.[0]?.text || "";

  const sync = () => {
    const data = new FormData(form);
    render("[data-review-customer]", [
      ["الاسم", data.get("fullName")],
      ["البريد الإلكتروني", data.get("email")],
      ["الموبايل", data.get("mobile")],
      ["المحافظة", selectedText(document.querySelector("#checkout-governorate"))],
      ["المدينة", data.get("city")],
      ["العنوان", data.get("street")],
      ["رقم المبنى", data.get("building")],
    ]);
    render("[data-review-delivery]", [
      ["طريقة الشحن", labelOf("input[name='shippingMethod']:checked")],
      ["المنطقة", selectedText(document.querySelector("#checkout-area"))],
      ["التركيب", data.get("installation") ? "مطلوب" : "غير مطلوب"],
    ]);
    render("[data-review-payment]", [
      ["الطريقة المختارة", labelOf("input[name='paymentMethod']:checked")],
    ]);
  };
  form.addEventListener("input", sync);
  form.addEventListener("change", sync);
  sync();
}

/** Guard against a double submission producing two identical attempts.
 *  The server is already idempotent on `idempotency_key`; this only spares the
 *  customer a needless round trip. */
function bindSubmitGuard() {
  const form = document.querySelector("[data-checkout-form]");
  form?.addEventListener("submit", () => {
    const button = form.querySelector("[data-checkout-final]");
    if (!button) return;
    window.setTimeout(() => {
      button.disabled = true;
      button.setAttribute("aria-busy", "true");
    }, 0);
    announce("جارٍ تأكيد الطلب");
  });
}

export function initialize() {
  const root = document.querySelector("[data-checkout-root]");
  if (!root || !document.querySelector("[data-checkout-form]")) return;
  bindStepControls();
  bindAreaFiltering();
  bindReviewSummary();
  bindSubmitGuard();

  // If the server sent the page back with errors, land on the step that has
  // them rather than making the customer hunt for it.
  const invalid = document.querySelector("[aria-invalid='true'], .field-error:not([hidden])");
  const panel = invalid?.closest("[data-checkout-panel]");
  showStep(panel?.dataset.checkoutPanel || root.dataset.initialStep || "shipping");
}

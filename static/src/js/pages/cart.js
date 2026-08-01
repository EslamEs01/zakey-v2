import { announce, setBusy } from "../utilities/dom.js";

let restoreCartFocus = false;

function currency(amount, fixture) {
  const digits = new Intl.NumberFormat(fixture.site.locale, { maximumFractionDigits: 0 }).format(amount);
  return `${digits} ${fixture.site.currency.label}`;
}

function productLookup(fixture) {
  return new Map(fixture.products.map((product) => [product.id, product]));
}

function categoryLabel(product, fixture) {
  return fixture.categories.find((category) => category.id === product.categoryId)?.name || "منتج ZAKEY";
}

function finishLabel(product, finishId) {
  return product.finishes.find((finish) => finish.id === finishId)?.label || "الخيار الافتراضي";
}

function assignProductLinks(lineElement, product) {
  const href = `/products/${encodeURIComponent(product.slug)}/`;
  lineElement.querySelectorAll("[data-cart-product-link]").forEach((link) => { link.href = href; });
}

function assignLineControls(lineElement, line, product) {
  const decrease = lineElement.querySelector("[data-cart-decrease]");
  const increase = lineElement.querySelector("[data-cart-increase]");
  decrease.disabled = line.quantity <= 1;
  increase.disabled = line.quantity >= 9;
  decrease.setAttribute("aria-label", `تقليل كمية ${product.name}`);
  increase.setAttribute("aria-label", `زيادة كمية ${product.name}`);
  lineElement.querySelector("[data-cart-remove]").setAttribute("aria-label", `إزالة ${product.name} من السلة`);
}

function cartLine(template, line, product, fixture) {
  const element = template.content.firstElementChild.cloneNode(true);
  element.dataset.productId = product.id;
  const image = element.querySelector("[data-cart-image]");
  image.src = product.images[0].path;
  image.alt = product.images[0].alt;
  element.querySelector("[data-cart-category]").textContent = categoryLabel(product, fixture);
  element.querySelector("[data-cart-name]").textContent = product.name;
  element.querySelector("[data-cart-finish]").textContent = `اللون: ${finishLabel(product, line.finishId)}`;
  element.querySelector("[data-cart-quantity]").textContent = String(line.quantity);
  element.querySelector("[data-cart-line-price]").textContent = currency(product.price * line.quantity, fixture);
  assignProductLinks(element, product);
  assignLineControls(element, line, product);
  return element;
}

function cartTotals(lines, products, fixture, couponCode) {
  const subtotal = lines.reduce((sum, line) => sum + (products.get(line.productId)?.price || 0) * line.quantity, 0);
  const coupon = fixture.site.couponPrototype;
  const discount = couponCode === coupon.acceptedCode ? Math.round(subtotal * coupon.discountRate) : 0;
  const total = subtotal - discount;
  const vat = Math.round((total * fixture.site.vatRate) / (1 + fixture.site.vatRate));
  const threshold = fixture.site.freeShippingThreshold;
  return { subtotal, discount, total, vat, freeShipping: subtotal >= threshold, remaining: Math.max(0, threshold - subtotal) };
}

function renderSummary(root, totals, fixture) {
  root.querySelector("[data-cart-subtotal]").textContent = currency(totals.subtotal, fixture);
  root.querySelector("[data-cart-discount]").textContent = `− ${currency(totals.discount, fixture)}`;
  root.querySelector("[data-cart-discount-row]").hidden = totals.discount === 0;
  root.querySelector("[data-cart-vat]").textContent = currency(totals.vat, fixture);
  root.querySelector("[data-cart-total]").textContent = currency(totals.total, fixture);
  root.querySelector("[data-cart-shipping]").textContent = totals.freeShipping ? "مجاني" : "يُحدد في الدفع";
  root.querySelector("[data-shipping-message]").textContent = totals.freeShipping
    ? "طلبك مؤهل لواجهة الشحن المجاني."
    : `أضف ${currency(totals.remaining, fixture)} للوصول إلى الشحن المجاني.`;
}

function visibleCartLines(store, fixture) {
  const products = productLookup(fixture);
  const lines = store.snapshot().cart.items.filter((line) => products.has(line.productId));
  return { lines, products };
}

function renderCart(root, store, fixture) {
  const { lines, products } = visibleCartLines(store, fixture);
  const populated = root.querySelector("[data-cart-populated]");
  root.querySelector("[data-cart-loading]").hidden = true;
  root.querySelector("[data-cart-empty]").hidden = lines.length > 0;
  populated.hidden = lines.length === 0;
  const container = root.querySelector("[data-cart-lines]");
  container.replaceChildren(...lines.map((line) => cartLine(document.querySelector("#cart-line-template"), line, products.get(line.productId), fixture)));
  const totals = cartTotals(lines, products, fixture, store.snapshot().cart.coupon);
  renderSummary(root, totals, fixture);
  root.setAttribute("aria-busy", "false");
  if (restoreCartFocus) window.requestAnimationFrame(() => document.querySelector("#cart-heading")?.focus());
  restoreCartFocus = false;
}

function changeQuantity(store, productId, delta) {
  const line = store.snapshot().cart.items.find((entry) => entry.productId === productId);
  if (!line) return;
  const quantity = Math.min(9, Math.max(1, line.quantity + delta));
  store.updateQuantity(productId, quantity);
  announce(`أصبحت الكمية ${quantity}`);
}

function cartAction(event, store) {
  const button = event.target.closest("button");
  const line = button?.closest("[data-cart-line]");
  if (!button || !line) return;
  const productId = line.dataset.productId;
  if (button.matches("[data-cart-increase]")) changeQuantity(store, productId, 1);
  if (button.matches("[data-cart-decrease]")) changeQuantity(store, productId, -1);
  if (button.matches("[data-cart-remove]")) {
    restoreCartFocus = true;
    store.removeFromCart(productId);
    announce("تمت إزالة المنتج من السلة");
  }
}

function setCouponStatus(form, state, message) {
  const status = form.querySelector("[data-coupon-status]");
  status.dataset.state = state;
  status.textContent = message;
  if (state === "rejected") form.elements.coupon.setAttribute("aria-invalid", "true");
  else form.elements.coupon.removeAttribute("aria-invalid");
}

function commitCoupon(store, form, fixture, code) {
  const coupon = fixture.site.couponPrototype;
  const accepted = code === coupon.acceptedCode;
  store.setCoupon(accepted ? code : "");
  setCouponStatus(form, accepted ? "accepted" : "rejected", accepted ? coupon.acceptedLabel : coupon.rejectedLabel);
  announce(accepted ? "تم تطبيق الخصم التجريبي" : "كود الخصم غير صالح");
}

function applyCoupon(event, store, fixture) {
  event.preventDefault();
  const form = event.currentTarget;
  const button = form.querySelector("[data-coupon-submit]");
  const code = form.elements.coupon.value.trim().toUpperCase();
  if (!code) {
    store.setCoupon("");
    setCouponStatus(form, "idle", "أدخل كودًا لمعاينة النتيجة.");
    return;
  }
  setBusy(button, true, "جارٍ التحقق…");
  setCouponStatus(form, "loading", "جارٍ التحقق محليًا من الكود التجريبي…");
  window.setTimeout(() => { commitCoupon(store, form, fixture, code); setBusy(button, false); }, 350);
}

function applyQaState(form, store, fixture) {
  const state = document.body.dataset.state;
  const button = form.querySelector("[data-coupon-submit]");
  if (state === "coupon-accepted") {
    const code = fixture.site.couponPrototype.acceptedCode;
    form.elements.coupon.value = code;
    store.setCoupon(code);
    setCouponStatus(form, "accepted", fixture.site.couponPrototype.acceptedLabel);
  } else if (state === "coupon-rejected") {
    form.elements.coupon.value = "غير-صالح";
    setCouponStatus(form, "rejected", fixture.site.couponPrototype.rejectedLabel);
  } else if (state === "coupon-loading") {
    setBusy(button, true, "جارٍ التحقق…");
    setCouponStatus(form, "loading", "جارٍ التحقق محليًا من الكود التجريبي…");
  } else if (state === "coupon-error") {
    setCouponStatus(form, "rejected", "تعذّر فحص الكود محليًا. صحّحه ثم أعد المحاولة.");
    button.textContent = "إعادة المحاولة";
  }
}

function restoreCoupon(form, store, fixture) {
  const code = store.snapshot().cart.coupon;
  if (code !== fixture.site.couponPrototype.acceptedCode) return;
  form.elements.coupon.value = code;
  setCouponStatus(form, "accepted", fixture.site.couponPrototype.acceptedLabel);
}

export function initialize(store, fixture) {
  const root = document.querySelector("[data-cart-root]");
  if (!root) return;
  const couponForm = root.querySelector("[data-coupon-form]");
  root.addEventListener("click", (event) => cartAction(event, store));
  couponForm.addEventListener("submit", (event) => applyCoupon(event, store, fixture));
  document.addEventListener("zakey:cart-change", () => renderCart(root, store, fixture));
  restoreCoupon(couponForm, store, fixture);
  renderCart(root, store, fixture);
  applyQaState(couponForm, store, fixture);
}

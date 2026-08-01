import { announce } from "../utilities/dom.js";

let restoreWishlistFocus = false;

function currency(amount, fixture) {
  const digits = new Intl.NumberFormat(fixture.site.locale, { maximumFractionDigits: 0 }).format(amount);
  return `${digits} ${fixture.site.currency.label}`;
}

function categoryLabel(product, fixture) {
  return fixture.categories.find((category) => category.id === product.categoryId)?.name || "منتج ZAKEY";
}

function assignProductLinks(card, product) {
  const href = `/products/${encodeURIComponent(product.slug)}/`;
  card.querySelectorAll("[data-wishlist-product-link]").forEach((link) => { link.href = href; });
}

function assignAvailability(card, product) {
  const status = card.querySelector("[data-wishlist-availability]");
  const unavailable = product.availability === "unavailable";
  status.textContent = unavailable ? "غير متاح" : product.availability === "limited" ? "كمية محدودة" : "متاح";
  status.classList.toggle("is-unavailable", unavailable);
  const addButton = card.querySelector("[data-wishlist-add-cart]");
  addButton.disabled = unavailable;
  addButton.setAttribute("aria-label", unavailable ? `${product.name} غير متاح للإضافة` : `إضافة ${product.name} إلى السلة`);
}

function wishlistCard(template, product, fixture) {
  const card = template.content.firstElementChild.cloneNode(true);
  card.dataset.productId = product.id;
  const image = card.querySelector("[data-wishlist-image]");
  image.src = product.images[0].path;
  image.alt = product.images[0].alt;
  card.querySelector("[data-wishlist-category]").textContent = categoryLabel(product, fixture);
  card.querySelector("[data-wishlist-name]").textContent = product.name;
  card.querySelector("[data-wishlist-description]").textContent = product.shortDescription;
  card.querySelector("[data-wishlist-price]").textContent = currency(product.price, fixture);
  card.querySelector("[data-wishlist-remove]").setAttribute("aria-label", `إزالة ${product.name} من المفضلة`);
  assignProductLinks(card, product);
  assignAvailability(card, product);
  return card;
}

function savedProducts(store, fixture) {
  const products = new Map(fixture.products.map((product) => [product.id, product]));
  return store.snapshot().wishlist.productIds.map((productId) => products.get(productId)).filter(Boolean);
}

function renderWishlist(root, store, fixture) {
  const products = savedProducts(store, fixture);
  root.querySelector("[data-wishlist-loading]").hidden = true;
  root.querySelector("[data-wishlist-empty]").hidden = products.length > 0;
  root.querySelector("[data-wishlist-populated]").hidden = products.length === 0;
  root.querySelector("[data-wishlist-total]").textContent = String(products.length);
  const template = document.querySelector("#wishlist-card-template");
  root.querySelector("[data-wishlist-grid]").replaceChildren(...products.map((product) => wishlistCard(template, product, fixture)));
  root.setAttribute("aria-busy", "false");
  if (restoreWishlistFocus) window.requestAnimationFrame(() => document.querySelector("#wishlist-heading")?.focus());
  restoreWishlistFocus = false;
}

function addWishlistProductToCart(store, fixture, productId) {
  const product = fixture.products.find((entry) => entry.id === productId);
  const finishId = product?.finishes[0]?.id || "default";
  if (store.addToCart(productId, 1, finishId)) announce("تمت إضافة المنتج إلى السلة التجريبية");
  else announce("هذا المنتج غير متاح للإضافة إلى السلة");
}

function wishlistAction(event, store, fixture) {
  const button = event.target.closest("button");
  const card = button?.closest("[data-wishlist-card]");
  if (!button || !card) return;
  if (button.matches("[data-wishlist-add-cart]")) addWishlistProductToCart(store, fixture, card.dataset.productId);
  if (button.matches("[data-wishlist-remove]")) {
    restoreWishlistFocus = true;
    store.toggleWishlist(card.dataset.productId);
    announce("تمت إزالة المنتج من المفضلة");
  }
}

export function initialize(store, fixture) {
  const root = document.querySelector("[data-wishlist-root]");
  if (!root) return;
  root.addEventListener("click", (event) => wishlistAction(event, store, fixture));
  document.addEventListener("zakey:wishlist-change", () => renderWishlist(root, store, fixture));
  renderWishlist(root, store, fixture);
}

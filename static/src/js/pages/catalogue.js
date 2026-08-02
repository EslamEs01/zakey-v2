import { announce } from "../utilities/dom.js";
import { openDialog } from "../components/dialog.js";

const PAGE_SIZE = 6;
const SORT_OPTIONS = new Set(["featured", "price-asc", "price-desc", "name"]);
const AVAILABILITY_OPTIONS = new Set(["available", "unavailable"]);

function integerParam(params, key) {
  const parsed = Number.parseInt(params.get(key) || "", 10);
  return Number.isFinite(parsed) ? Math.max(0, parsed) : null;
}

function collectionSlug() {
  if (document.body.dataset.page !== "collection") return null;
  const segments = window.location.pathname.split("/").filter(Boolean);
  return segments.at(-1) || null;
}

function catalogueCriteria(fixture) {
  const params = new URLSearchParams(window.location.search);
  const knownCategories = new Set(fixture.categories.map((category) => category.slug));
  const knownFeatures = new Set(fixture.products.flatMap((product) => product.features.map((feature) => feature.key)));
  const features = params.getAll("feature").filter((feature) => knownFeatures.has(feature));
  const category = params.get("category");
  const availability = params.get("availability");
  const sort = params.get("sort");
  let priceMin = integerParam(params, "priceMin");
  let priceMax = integerParam(params, "priceMax");
  if (priceMin !== null && priceMax !== null && priceMin > priceMax) [priceMin, priceMax] = [priceMax, priceMin];
  return {
    q: (params.get("q") || "").trim().replace(/\s+/g, " "),
    category: knownCategories.has(category) ? category : null,
    features,
    priceMin,
    priceMax,
    availability: AVAILABILITY_OPTIONS.has(availability) ? availability : null,
    sort: SORT_OPTIONS.has(sort) ? sort : "featured",
    page: Math.max(1, Number.parseInt(params.get("page") || "1", 10) || 1),
    collection: collectionSlug(),
  };
}

function matchesCriteria(product, criteria, fixture) {
  const category = fixture.categories.find((entry) => entry.slug === criteria.category);
  const collection = fixture.collections.find((entry) => entry.slug === criteria.collection);
  const searchable = `${product.name} ${product.shortDescription || ""}`.toLocaleLowerCase("ar-EG");
  if (collection && !collection.productIds.includes(product.id)) return false;
  if (category && product.categoryId !== category.id) return false;
  if (criteria.q && !searchable.includes(criteria.q.toLocaleLowerCase("ar-EG"))) return false;
  if (criteria.priceMin !== null && product.price < criteria.priceMin) return false;
  if (criteria.priceMax !== null && product.price > criteria.priceMax) return false;
  if (criteria.availability === "available" && !["available", "limited"].includes(product.availability)) return false;
  if (criteria.availability === "unavailable" && product.availability !== "unavailable") return false;
  const productFeatures = new Set(product.features.map((feature) => feature.key));
  return criteria.features.every((feature) => productFeatures.has(feature));
}

function sortedProducts(products, sort) {
  const ordered = [...products];
  if (sort === "price-asc") ordered.sort((left, right) => left.price - right.price);
  if (sort === "price-desc") ordered.sort((left, right) => right.price - left.price);
  if (sort === "name") ordered.sort((left, right) => left.name.localeCompare(right.name, "ar"));
  return ordered;
}

function productCard(productId) {
  const template = document.querySelector(`[data-catalogue-product-template="${productId}"]`);
  return template?.content.firstElementChild?.cloneNode(true) || null;
}

function pagination(pageCount, currentPage) {
  if (pageCount <= 1) return null;
  const navigation = document.createElement("nav");
  navigation.className = "pagination";
  navigation.setAttribute("aria-label", "صفحات النتائج");
  for (let page = 1; page <= pageCount; page += 1) navigation.append(paginationLink(page, currentPage));
  return navigation;
}

function paginationLink(page, currentPage) {
  const link = document.createElement("a");
  const url = new URL(window.location.href);
  url.searchParams.set("page", String(page));
  link.href = url;
  link.textContent = String(page);
  if (page === currentPage) link.setAttribute("aria-current", "page");
  return link;
}

function emptyState(criteria) {
  const state = document.createElement("div");
  state.className = "state-panel";
  const heading = criteria.q ? "لا توجد نتائج لهذا البحث" : "لا توجد منتجات بهذه الفلاتر";
  state.innerHTML = `<div><h2>${heading}</h2><p>جرّب عبارة أقصر أو امسح بعض الاختيارات.</p><a class="btn btn--primary" href="/shop/">عرض كل المنتجات</a></div>`;
  return state;
}

function renderResults(products, criteria) {
  const results = document.querySelector(".catalogue-results");
  if (!results) return;
  const pageCount = Math.max(1, Math.ceil(products.length / PAGE_SIZE));
  const page = Math.min(criteria.page, pageCount);
  const pageProducts = products.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);
  const grid = document.createElement("div");
  grid.className = "catalogue-grid";
  for (const product of pageProducts) {
    const card = productCard(product.id);
    if (card) grid.append(card);
  }
  results.replaceChildren(pageProducts.length ? grid : emptyState(criteria));
  const pages = pagination(pageCount, page);
  if (pages) results.append(pages);
  document.querySelector("[data-result-count]").textContent = String(products.length);
  document.dispatchEvent(new CustomEvent("zakey:wishlist-change"));
}

function filterLabels(criteria, fixture) {
  const labels = [];
  const category = fixture.categories.find((entry) => entry.slug === criteria.category);
  const collection = fixture.collections.find((entry) => entry.slug === criteria.collection);
  if (category) labels.push({ key: "category", value: category.slug, label: category.name });
  if (collection) labels.push({ key: "collection", value: collection.slug, label: collection.name });
  if (criteria.priceMin !== null) labels.push({ key: "priceMin", value: String(criteria.priceMin), label: `من ${criteria.priceMin} ج.م` });
  if (criteria.priceMax !== null) labels.push({ key: "priceMax", value: String(criteria.priceMax), label: `حتى ${criteria.priceMax} ج.م` });
  for (const key of criteria.features) {
    const feature = fixture.products.flatMap((product) => product.features).find((entry) => entry.key === key);
    if (feature) labels.push({ key: "feature", value: key, label: feature.label });
  }
  if (criteria.availability) labels.push({ key: "availability", value: criteria.availability, label: criteria.availability === "available" ? "متاح الآن" : "غير متاح" });
  return labels;
}

function clearUrl(criteria) {
  const shopPath = document.querySelector("[data-active-filters]")?.dataset.shopUrl || window.location.pathname;
  const url = new URL(criteria.collection ? shopPath : window.location.href, window.location.origin);
  url.search = "";
  if (document.body.dataset.page === "search" && criteria.q) url.searchParams.set("q", criteria.q);
  return url;
}

function renderActiveFilters(criteria, fixture) {
  const container = document.querySelector("[data-active-filters]");
  if (!container) return;
  const labels = filterLabels(criteria, fixture);
  container.replaceChildren();
  container.hidden = labels.length === 0;
  if (!labels.length) return;
  const prefix = document.createElement("span");
  prefix.textContent = "محدد:";
  container.append(prefix, ...labels.map(filterButton));
  const clear = document.createElement("a");
  clear.href = clearUrl(criteria);
  clear.textContent = "مسح الكل";
  container.append(clear);
}

function filterButton(filter) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = "filter-chip";
  button.dataset.filterRemove = filter.key;
  button.dataset.filterValue = filter.value;
  button.textContent = `${filter.label} ×`;
  return button;
}

function syncForms(criteria) {
  document.querySelectorAll("[data-catalogue-form]").forEach((form) => {
    form.querySelectorAll("input[name='category']").forEach((input) => { input.checked = input.value === criteria.category; });
    form.querySelectorAll("input[name='availability']").forEach((input) => { input.checked = input.value === criteria.availability; });
    form.querySelectorAll("input[name='feature']").forEach((input) => { input.checked = criteria.features.includes(input.value); });
    form.elements.priceMin.value = criteria.priceMin ?? "";
    form.elements.priceMax.value = criteria.priceMax ?? "";
    const query = form.elements.q;
    if (query) query.value = criteria.q;
    form.querySelector(".filter-heading a").href = clearUrl(criteria);
  });
  const sort = document.querySelector("[data-sort-form] select");
  if (sort) sort.value = criteria.sort;
}

function removeFilter(button) {
  if (button.dataset.filterRemove === "collection") {
    const shopPath = document.querySelector("[data-active-filters]")?.dataset.shopUrl || "/shop/";
    const url = new URL(shopPath, window.location.origin);
    url.search = window.location.search;
    url.searchParams.delete("page");
    window.location.assign(url);
    return;
  }
  const url = new URL(window.location.href);
  const key = button.dataset.filterRemove;
  if (key === "feature") {
    const keep = url.searchParams.getAll(key).filter((value) => value !== button.dataset.filterValue);
    url.searchParams.delete(key);
    keep.forEach((value) => url.searchParams.append(key, value));
  } else url.searchParams.delete(key);
  url.searchParams.delete("page");
  window.location.assign(url);
}

function bindCatalogueControls() {
  document.querySelector("[data-active-filters]")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-remove]");
    if (button) removeFilter(button);
  });
  document.querySelector("[data-sort-form] select")?.addEventListener("change", (event) => {
    const url = new URL(window.location.href);
    url.searchParams.set("sort", event.currentTarget.value);
    url.searchParams.delete("page");
    window.location.assign(url);
  });
}

function updateSearchHeading(criteria) {
  if (document.body.dataset.page !== "search") return;
  const description = document.querySelector("[data-catalogue-description]");
  if (description) description.textContent = criteria.q ? `نتائج البحث عن “${criteria.q}”` : "اكتب اسم منتج أو ميزة للبحث في مجموعة ZAKEY.";
  document.title = criteria.q ? `نتائج البحث عن ${criteria.q} | ZAKEY` : "البحث | ZAKEY";
}

function initializeFilterDialog() {
  const dialog = document.querySelector("#filter-dialog");
  const trigger = document.querySelector("[data-filter-open]");
  if (!trigger) return;
  trigger.id ||= "filter-dialog-trigger";
  trigger.addEventListener("click", () => openDialog(dialog, trigger));
}

export function initialize(_store, fixture) {
  initializeFilterDialog();
  bindCatalogueControls();
  document.querySelector("[data-retry-catalogue]")?.addEventListener("click", () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("qa");
    announce("جارٍ إعادة تحميل النتائج");
    window.location.assign(url);
  });
  if (["loading", "recoverable-error", "error"].includes(document.body.dataset.state)) return;
  const criteria = catalogueCriteria(fixture);
  const matches = fixture.products.filter((product) => matchesCriteria(product, criteria, fixture));
  syncForms(criteria);
  renderActiveFilters(criteria, fixture);
  renderResults(sortedProducts(matches, criteria.sort), criteria);
  updateSearchHeading(criteria);
}

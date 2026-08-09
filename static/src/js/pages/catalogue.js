import { announce } from "../utilities/dom.js";
import { openDialog } from "../components/dialog.js";

/**
 * Catalogue page behaviour — presentation and navigation only (T-1607, FR-133).
 *
 * This module used to re-implement the whole catalogue in the browser: it read
 * the product fixture, filtered, sorted and paginated it, then REPLACED the
 * server-rendered grid with its own. Two independent implementations of one
 * business rule is one too many, and the browser's copy was authoritative for
 * what the customer saw.
 *
 * The server now filters, sorts and paginates (apps.catalog.selectors) and
 * renders the result. What is left here is the part that genuinely belongs to
 * the client: opening the filter drawer, and turning the sort control and the
 * filter chips into ordinary navigation. Every one of those is a link or a form
 * submit underneath, so the page works with JavaScript disabled (FR-136).
 */

function clearUrl() {
  const shopPath = document.querySelector("[data-active-filters]")?.dataset.shopUrl || window.location.pathname;
  const isCollection = document.body.dataset.page === "collection";
  const url = new URL(isCollection ? shopPath : window.location.pathname, window.location.origin);
  const query = new URLSearchParams(window.location.search).get("q");
  if (document.body.dataset.page === "search" && query) url.searchParams.set("q", query);
  return url;
}

function removeFilter(button) {
  const key = button.dataset.filterRemove;
  if (key === "collection") {
    const shopPath = document.querySelector("[data-active-filters]")?.dataset.shopUrl || "/shop/";
    const url = new URL(shopPath, window.location.origin);
    url.search = window.location.search;
    url.searchParams.delete("page");
    window.location.assign(url);
    return;
  }
  const url = new URL(window.location.href);
  if (key === "feature") {
    const keep = url.searchParams.getAll(key).filter((value) => value !== button.dataset.filterValue);
    url.searchParams.delete(key);
    keep.forEach((value) => url.searchParams.append(key, value));
  } else {
    url.searchParams.delete(key);
  }
  url.searchParams.delete("page");
  window.location.assign(url);
}

function bindCatalogueControls() {
  document.querySelector("[data-active-filters]")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-filter-remove]");
    if (button) removeFilter(button);
  });
  // Submitting the sort form does the same thing without JavaScript; this only
  // saves the customer a click.
  document.querySelector("[data-sort-form] select")?.addEventListener("change", (event) => {
    const url = new URL(window.location.href);
    url.searchParams.set("sort", event.currentTarget.value);
    url.searchParams.delete("page");
    window.location.assign(url);
  });
  const clear = document.querySelector(".filter-heading a");
  if (clear) clear.href = clearUrl();
}

function initializeFilterDialog() {
  const dialog = document.querySelector("#filter-dialog");
  const trigger = document.querySelector("[data-filter-open]");
  if (!trigger) return;
  trigger.id ||= "filter-dialog-trigger";
  trigger.addEventListener("click", () => openDialog(dialog, trigger));
}

export function initialize() {
  initializeFilterDialog();
  bindCatalogueControls();
  document.querySelector("[data-retry-catalogue]")?.addEventListener("click", () => {
    const url = new URL(window.location.href);
    url.searchParams.delete("qa");
    announce("جارٍ إعادة تحميل النتائج");
    window.location.assign(url);
  });
}

import { closeDialog, openDialog } from "./dialog.js";

export function initializeHeader(store) {
  const searchPanel = document.querySelector("#header-search");
  const searchTrigger = document.querySelector("[data-search-trigger]");
  const searchInput = searchPanel?.querySelector("input");
  const closeSearch = () => {
    if (!searchPanel) return;
    searchPanel.hidden = true;
    searchTrigger?.setAttribute("aria-expanded", "false");
    searchTrigger?.focus();
  };
  searchTrigger?.addEventListener("click", () => {
    const opening = searchPanel.hidden;
    searchPanel.hidden = !opening;
    searchTrigger.setAttribute("aria-expanded", String(opening));
    if (opening) searchInput?.focus();
  });
  document.querySelector("[data-search-close]")?.addEventListener("click", closeSearch);

  const menuTrigger = document.querySelector("[data-products-menu-trigger]");
  const menu = document.querySelector("#products-menu");
  const closeProducts = () => { if (menu) menu.hidden = true; menuTrigger?.setAttribute("aria-expanded", "false"); };
  menuTrigger?.addEventListener("click", () => {
    const opening = menu.hidden;
    menu.hidden = !opening;
    menuTrigger.setAttribute("aria-expanded", String(opening));
  });
  document.addEventListener("click", (event) => {
    if (menu && !menu.hidden && !event.target.closest(".nav-menu-wrap")) closeProducts();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && searchPanel && !searchPanel.hidden) closeSearch();
    if (event.key === "Escape" && menu && !menu.hidden) { closeProducts(); menuTrigger?.focus(); }
  });

  const mobileTrigger = document.querySelector("[data-mobile-menu-trigger]");
  const mobileDialog = document.querySelector("#mobile-menu");
  if (mobileTrigger && !mobileTrigger.id) mobileTrigger.id = "mobile-menu-trigger";
  mobileTrigger?.addEventListener("click", () => openDialog(mobileDialog, mobileTrigger));
  mobileDialog?.querySelectorAll("a").forEach((link) => link.addEventListener("click", () => closeDialog(mobileDialog)));

  const updateCounts = () => {
    updateCount("cart", store.cartCount());
    updateCount("wishlist", store.wishlistCount());
  };
  document.addEventListener("zakey:cart-change", updateCounts);
  document.addEventListener("zakey:wishlist-change", updateCounts);
  updateCounts();
}

function updateCount(kind, count) {
  const badge = document.querySelector(`[data-${kind}-count]`);
  const link = document.querySelector(`[data-${kind}-link]`);
  if (badge) { badge.textContent = String(count); badge.hidden = count === 0; }
  if (link) {
    const label = kind === "cart" ? "سلة التسوق" : "المفضلة";
    link.setAttribute("aria-label", `${label}، ${count} عناصر`);
  }
}

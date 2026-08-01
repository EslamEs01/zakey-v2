import { announce } from "../utilities/dom.js";

export function initializeWishlistControls(store) {
  const sync = () => {
    const saved = new Set(store.snapshot().wishlist.productIds);
    document.querySelectorAll("[data-wishlist-toggle]").forEach((button) => {
      const active = saved.has(button.dataset.wishlistToggle);
      button.setAttribute("aria-pressed", String(active));
      button.classList.toggle("is-active", active);
    });
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-wishlist-toggle]");
    if (!button) return;
    const added = store.toggleWishlist(button.dataset.wishlistToggle);
    announce(added ? "تمت الإضافة إلى المفضلة" : "تمت الإزالة من المفضلة");
  });
  document.addEventListener("zakey:wishlist-change", sync);
  sync();
}

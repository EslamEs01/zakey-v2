import { announce } from "../utilities/dom.js";

function quantityValue() {
  const input = document.querySelector("[data-quantity]");
  return Math.min(9, Math.max(1, Number.parseInt(input?.value, 10) || 1));
}

export function initialize(store) {
  const root = document.querySelector("[data-product-id]");
  if (!root) return;
  const productId = root.dataset.productId;
  const quantity = document.querySelector("[data-quantity]");
  document.querySelector("[data-quantity-minus]")?.addEventListener("click", () => { quantity.value = Math.max(1, quantityValue() - 1); });
  document.querySelector("[data-quantity-plus]")?.addEventListener("click", () => { quantity.value = Math.min(9, quantityValue() + 1); });
  quantity?.addEventListener("change", () => { quantity.value = quantityValue(); });
  const add = () => {
    const finishId = document.querySelector("input[name='finish']:checked")?.value || "default";
    if (store.addToCart(productId, quantityValue(), finishId)) announce("تمت إضافة المنتج إلى السلة التجريبية");
    else announce("هذا المنتج غير متاح حاليًا");
  };
  document.querySelector("[data-add-product]")?.addEventListener("click", add);
  document.querySelector("[data-buy-product]")?.addEventListener("click", () => { add(); window.location.assign("/checkout/"); });
  document.querySelectorAll("[data-gallery-image]").forEach((button) => button.addEventListener("click", () => {
    const main = document.querySelector("[data-gallery-main]");
    main.src = button.dataset.galleryImage;
    main.alt = button.dataset.galleryAlt;
    document.querySelectorAll("[data-gallery-image]").forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
    announce(`تم عرض ${button.dataset.galleryAlt}`);
  }));
  initializeTabs();
  document.querySelector("[data-share-product]")?.addEventListener("click", async () => {
    try {
      if (navigator.share) await navigator.share({ title: document.title, url: window.location.href });
      else { await navigator.clipboard.writeText(window.location.href); announce("تم نسخ رابط المنتج"); }
    } catch (error) {
      if (error.name !== "AbortError") announce("تعذرت المشاركة؛ يمكنك نسخ الرابط من شريط العنوان");
    }
  });
}

function initializeTabs() {
  const tabs = [...document.querySelectorAll("[role='tab']")];
  const select = (tab) => {
    tabs.forEach((item) => {
      const active = item === tab;
      item.setAttribute("aria-selected", String(active));
      item.tabIndex = active ? 0 : -1;
      document.getElementById(item.getAttribute("aria-controls")).hidden = !active;
    });
    tab.focus();
  };
  tabs.forEach((tab, index) => {
    tab.addEventListener("click", () => select(tab));
    tab.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1 : (index + (event.key === "ArrowLeft" ? 1 : -1) + tabs.length) % tabs.length;
      select(tabs[next]);
    });
  });
  const requested = new URLSearchParams(window.location.search).get("tab");
  const requestedTab = tabs.find((tab) => tab.id === `tab-${requested}`);
  if (requestedTab) select(requestedTab);
}

import { announce } from "../utilities/dom.js";

/**
 * Product page behaviour (T-1603/T-1607).
 *
 * Adding to the cart is a real form POST now, so this module no longer decides
 * whether a product is purchasable or what ends up in the basket — the server
 * does, against live stock. What remains is presentation: the quantity stepper,
 * the gallery, the tab strip and sharing. Every one of them degrades cleanly:
 * the quantity input is a plain number field, the gallery thumbnails start on a
 * real image, and the tab panels are all in the document.
 */

function quantityInput() {
  return document.querySelector("[data-quantity]");
}

function clampedQuantity() {
  const input = quantityInput();
  const max = Number.parseInt(input?.max, 10) || 9;
  return Math.min(max, Math.max(1, Number.parseInt(input?.value, 10) || 1));
}

function initializeQuantityStepper() {
  const input = quantityInput();
  if (!input) return;
  document.querySelector("[data-quantity-minus]")?.addEventListener("click", () => {
    input.value = Math.max(1, clampedQuantity() - 1);
  });
  document.querySelector("[data-quantity-plus]")?.addEventListener("click", () => {
    const max = Number.parseInt(input.max, 10) || 9;
    input.value = Math.min(max, clampedQuantity() + 1);
  });
  input.addEventListener("change", () => {
    input.value = clampedQuantity();
  });
}

function initializeGallery() {
  document.querySelectorAll("[data-gallery-image]").forEach((button) =>
    button.addEventListener("click", () => {
      const main = document.querySelector("[data-gallery-main]");
      if (!main) return;
      main.src = button.dataset.galleryImage;
      main.alt = button.dataset.galleryAlt;
      document
        .querySelectorAll("[data-gallery-image]")
        .forEach((item) => item.setAttribute("aria-pressed", String(item === button)));
      announce(`تم عرض ${button.dataset.galleryAlt}`);
    }),
  );
}

function initializeShare() {
  document.querySelector("[data-share-product]")?.addEventListener("click", async () => {
    try {
      if (navigator.share) await navigator.share({ title: document.title, url: window.location.href });
      else {
        await navigator.clipboard.writeText(window.location.href);
        announce("تم نسخ رابط المنتج");
      }
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
      const next =
        event.key === "Home"
          ? 0
          : event.key === "End"
            ? tabs.length - 1
            : (index + (event.key === "ArrowLeft" ? 1 : -1) + tabs.length) % tabs.length;
      select(tabs[next]);
    });
  });
  const requested = new URLSearchParams(window.location.search).get("tab");
  const requestedTab = tabs.find((tab) => tab.id === `tab-${requested}`);
  if (requestedTab) select(requestedTab);
}

export function initialize() {
  if (!document.querySelector("[data-product-id]")) return;
  initializeQuantityStepper();
  initializeGallery();
  initializeTabs();
  initializeShare();
}

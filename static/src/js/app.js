import { initializeDialogs } from "./components/dialog.js";
import { initializeForms } from "./components/forms.js";
import { initializeHeader } from "./components/header.js";

/**
 * Storefront bootstrap (T-1604/T-1607, FR-133, FR-136).
 *
 * There is no client-side store any more. The prototype kept a `PrototypeStore`
 * over `localStorage` holding the cart, the wishlist and the signed-in flag,
 * and every page module read and wrote it — which made the browser the database
 * and the customer the administrator of their own prices.
 *
 * Cart, wishlist and account state now live in the database and arrive rendered.
 * What is left in this file is genuine client-side behaviour: dialogs, the
 * header menus, and per-page progressive enhancement.
 *
 * `#zakey-fixture` still exists but now carries only presentation settings
 * (currency, locale, max line quantity) — nothing a script could price with.
 */

const settingsElement = document.querySelector("#zakey-fixture");
const settings = settingsElement ? JSON.parse(settingsElement.textContent) : {};

initializeDialogs();
initializeHeader();
initializeForms();
initializePage();

async function initializePage() {
  const page = document.body.dataset.page;
  const modules = {
    shop: "./pages/catalogue.js",
    collection: "./pages/catalogue.js",
    search: "./pages/catalogue.js",
    product: "./pages/product.js",
    checkout: "./pages/checkout.js",
    account: "./pages/account.js",
    contact: "./pages/contact.js",
    home: "./pages/home.js",
  };
  if (!modules[page]) return;
  const module = await import(modules[page]);
  module.initialize?.(settings);
}

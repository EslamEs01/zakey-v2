import { initializeDialogs } from "./components/dialog.js";
import { initializePrototypeForms } from "./components/forms.js";
import { initializeHeader } from "./components/header.js";
import { initializeWishlistControls } from "./components/wishlist.js";
import { StorageAdapter } from "./state/storage-adapter.js";
import { PrototypeStore } from "./state/store.js";

const fixtureElement = document.querySelector("#zakey-fixture");
const fixture = fixtureElement ? JSON.parse(fixtureElement.textContent) : null;

if (fixture) {
  const emptyCart = fixture.prototypeCarts?.find((state) => state.id === "cart-empty");
  const emptyWishlist = fixture.prototypeWishlists?.find((state) => state.id === "wishlist-empty");
  const defaults = {
    cart: {
      items: (emptyCart?.lineItems || []).map((item) => ({
        productId: item.productId,
        quantity: item.quantity,
        finishId: item.finishId || "default",
      })),
      coupon: emptyCart?.coupon?.code || "",
    },
    wishlist: { productIds: [...(emptyWishlist?.productIds || [])] },
    account: { mode: "signed-out", tab: "orders" },
  };
  const store = new PrototypeStore(fixture, new StorageAdapter(defaults));
  window.ZakeyPrototype = Object.freeze({ store, reset: () => store.reset() });
  initializeDialogs();
  initializeHeader(store);
  initializePrototypeForms();
  initializeWishlistControls(store);
  initializePage(store);
}

async function initializePage(store) {
  const page = document.body.dataset.page;
  const modules = {
    shop: "./pages/catalogue.js",
    collection: "./pages/catalogue.js",
    search: "./pages/catalogue.js",
    product: "./pages/product.js",
    cart: "./pages/cart.js",
    wishlist: "./pages/wishlist.js",
    checkout: "./pages/checkout.js",
    account: "./pages/account.js",
    contact: "./pages/contact.js",
    home: "./pages/home.js",
  };
  if (!modules[page]) return;
  const module = await import(modules[page]);
  module.initialize?.(store, fixture);
}

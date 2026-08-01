const STORAGE_KEY = "zakey:prototype:v1";
const VERSION = 1;

function safeEnvelope(value, defaults) {
  if (!value || value.version !== VERSION) return structuredClone(defaults);
  return {
    version: VERSION,
    cart: sanitizeCart(value.cart, defaults.cart),
    wishlist: sanitizeWishlist(value.wishlist, defaults.wishlist),
    account: sanitizeAccount(value.account, defaults.account),
  };
}

function sanitizeCart(cart, fallback) {
  if (!cart || !Array.isArray(cart.items)) return structuredClone(fallback);
  return {
    items: cart.items
      .filter((item) => typeof item.productId === "string")
      .map((item) => ({
        productId: item.productId,
        finishId: typeof item.finishId === "string" ? item.finishId : "default",
        quantity: Math.min(9, Math.max(1, Number.parseInt(item.quantity, 10) || 1)),
      })),
    coupon: typeof cart.coupon === "string" ? cart.coupon : "",
  };
}

function sanitizeWishlist(wishlist, fallback) {
  if (!wishlist || !Array.isArray(wishlist.productIds)) return structuredClone(fallback);
  return { productIds: [...new Set(wishlist.productIds.filter((id) => typeof id === "string"))] };
}

function sanitizeAccount(account, fallback) {
  if (!account || !["signed-out", "signed-in"].includes(account.mode)) return structuredClone(fallback);
  return { mode: account.mode, tab: typeof account.tab === "string" ? account.tab : "orders" };
}

export class StorageAdapter {
  constructor(defaults) {
    this.defaults = { version: VERSION, ...structuredClone(defaults) };
    this.available = true;
  }

  read() {
    try {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      return safeEnvelope(raw ? JSON.parse(raw) : null, this.defaults);
    } catch {
      this.available = false;
      return structuredClone(this.defaults);
    }
  }

  write(envelope) {
    try {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(safeEnvelope(envelope, this.defaults)));
      this.available = true;
      return true;
    } catch {
      this.available = false;
      return false;
    }
  }

  reset() {
    try {
      window.localStorage.removeItem(STORAGE_KEY);
      this.available = true;
    } catch {
      this.available = false;
    }
    return structuredClone(this.defaults);
  }
}

export { STORAGE_KEY };

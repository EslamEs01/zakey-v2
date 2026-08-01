export class PrototypeStore extends EventTarget {
  constructor(fixture, adapter) {
    super();
    this.fixture = fixture;
    this.adapter = adapter;
    this.state = adapter.read();
  }

  snapshot() {
    return structuredClone(this.state);
  }

  cartCount() {
    return this.state.cart.items.reduce((count, item) => count + item.quantity, 0);
  }

  wishlistCount() {
    return this.state.wishlist.productIds.length;
  }

  addToCart(productId, quantity = 1, finishId = "default") {
    const product = this.fixture.products.find((item) => item.id === productId);
    if (!product || product.availability === "unavailable") return false;
    const current = this.state.cart.items.find(
      (item) => item.productId === productId && item.finishId === finishId,
    );
    if (current) current.quantity = Math.min(9, current.quantity + quantity);
    else this.state.cart.items.push({ productId, quantity: Math.min(9, Math.max(1, quantity)), finishId });
    this.commit("cart-change");
    return true;
  }

  updateQuantity(productId, quantity) {
    const item = this.state.cart.items.find((entry) => entry.productId === productId);
    if (!item) return;
    item.quantity = Math.min(9, Math.max(1, Number.parseInt(quantity, 10) || 1));
    this.commit("cart-change");
  }

  removeFromCart(productId) {
    this.state.cart.items = this.state.cart.items.filter((item) => item.productId !== productId);
    this.commit("cart-change");
  }

  setCoupon(code = "") {
    this.state.cart.coupon = typeof code === "string" ? code : "";
    this.commit("cart-change");
  }

  toggleWishlist(productId) {
    const ids = this.state.wishlist.productIds;
    const index = ids.indexOf(productId);
    if (index >= 0) ids.splice(index, 1);
    else ids.push(productId);
    this.commit("wishlist-change");
    return index < 0;
  }

  setAccountState(changes = {}) {
    const mode = ["signed-out", "signed-in"].includes(changes.mode) ? changes.mode : this.state.account.mode;
    const tab = typeof changes.tab === "string" ? changes.tab : this.state.account.tab;
    if (mode === this.state.account.mode && tab === this.state.account.tab) return;
    this.state.account = { mode, tab };
    this.commit("account-state-change");
  }

  reset() {
    this.state = this.adapter.reset();
    this.emit("cart-change");
    this.emit("wishlist-change");
    this.emit("account-state-change");
  }

  commit(type) {
    const stored = this.adapter.write(this.state);
    this.emit(type);
    if (!stored) this.emit("prototype-status", { status: "error", message: "تعذر حفظ الحالة محلياً، لكن يمكنك متابعة العرض." });
  }

  emit(type, detail = {}) {
    const payload = { ...detail, state: this.snapshot(), cartCount: this.cartCount(), wishlistCount: this.wishlistCount() };
    this.dispatchEvent(new CustomEvent(`zakey:${type}`, { detail: payload }));
    document.dispatchEvent(new CustomEvent(`zakey:${type}`, { detail: payload }));
  }
}

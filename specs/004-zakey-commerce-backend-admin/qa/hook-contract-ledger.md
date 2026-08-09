# T-1609 — data-* hook contract ledger

Baseline (T-0104): **139** hooks · current inventory: **148** hooks.

`frontend-contract.md` §5 treats the hooks as behavioural API and requires a
recorded reason for any change; T-1609's acceptance is *zero unintended*
renames. Enforced by `tests/test_hook_contract.py`, which fails on an
undeclared disappearance, a retired prototype hook returning to a runtime
template, or a script querying a hook no template renders.

A line-number move inside the same template is **not** a semantic relocation:
same file, same component, same element, same interaction, same consumers.

| status | count |
|---|---|
| retained (same template) | 131 |
| relocated (different template) | 0 |
| retired (declared) | 8 |
| **missing regression** | **0** |

## Per-hook status

| hook | status | detail |
|---|---|---|
| `data-account-demo-form` | retired | prototype behaviour removed by the server-backed implementation |
| `data-account-mode` | retained | same template(s); line numbers only |
| `data-account-panel` | retained | same template(s); line numbers only |
| `data-account-panel-id` | retained | same template(s); line numbers only |
| `data-account-panels` | retained | same template(s); line numbers only |
| `data-account-settings` | retained | same template(s); line numbers only |
| `data-account-settings-submit` | retained | same template(s); line numbers only |
| `data-account-signed-out` | retained | same template(s); line numbers only |
| `data-account-status` | retained | same template(s); line numbers only |
| `data-account-tab` | retained | same template(s); line numbers only |
| `data-account-tab-id` | retained | same template(s); line numbers only |
| `data-account-tabs` | retained | same template(s); line numbers only |
| `data-account-unavailable` | retired | prototype behaviour removed by the server-backed implementation |
| `data-account-wishlist-empty` | retained | same template(s); line numbers only |
| `data-account-wishlist-items` | retained | same template(s); line numbers only |
| `data-account-wishlist-list` | retained | same template(s); line numbers only |
| `data-account-wishlist-summary` | retained | same template(s); line numbers only |
| `data-active-filters` | retained | same template(s); line numbers only |
| `data-add-product` | retained | same template(s); line numbers only |
| `data-area-field` | retained | same template(s); line numbers only |
| `data-buy-product` | retained | same template(s); line numbers only |
| `data-cart-category` | retained | same template(s); line numbers only |
| `data-cart-count` | retained | same template(s); line numbers only |
| `data-cart-decrease` | retained | same template(s); line numbers only |
| `data-cart-discount` | retained | same template(s); line numbers only |
| `data-cart-discount-row` | retained | same template(s); line numbers only |
| `data-cart-empty` | retained | same template(s); line numbers only |
| `data-cart-finish` | retained | same template(s); line numbers only |
| `data-cart-image` | retained | same template(s); line numbers only |
| `data-cart-increase` | retained | same template(s); line numbers only |
| `data-cart-line` | retained | same template(s); line numbers only |
| `data-cart-line-price` | retained | same template(s); line numbers only |
| `data-cart-lines` | retained | same template(s); line numbers only |
| `data-cart-link` | retained | same template(s); line numbers only |
| `data-cart-loading` | retired | prototype behaviour removed by the server-backed implementation |
| `data-cart-name` | retained | same template(s); line numbers only |
| `data-cart-populated` | retained | same template(s); line numbers only |
| `data-cart-product-link` | retained | same template(s); line numbers only |
| `data-cart-quantity` | retained | same template(s); line numbers only |
| `data-cart-remove` | retained | same template(s); line numbers only |
| `data-cart-root` | retained | same template(s); line numbers only |
| `data-cart-shipping` | retained | same template(s); line numbers only |
| `data-cart-subtotal` | retained | same template(s); line numbers only |
| `data-cart-total` | retained | same template(s); line numbers only |
| `data-cart-vat` | retained | same template(s); line numbers only |
| `data-catalogue-description` | retained | same template(s); line numbers only |
| `data-catalogue-form` | retained | same template(s); line numbers only |
| `data-catalogue-product-library` | retired | prototype behaviour removed by the server-backed implementation |
| `data-catalogue-product-template` | retired | prototype behaviour removed by the server-backed implementation |
| `data-checkout-discount` | retained | same template(s); line numbers only |
| `data-checkout-discount-row` | retained | same template(s); line numbers only |
| `data-checkout-empty` | retained | same template(s); line numbers only |
| `data-checkout-final` | retained | same template(s); line numbers only |
| `data-checkout-layout` | retained | same template(s); line numbers only |
| `data-checkout-line-image` | retained | same template(s); line numbers only |
| `data-checkout-line-meta` | retained | same template(s); line numbers only |
| `data-checkout-line-name` | retained | same template(s); line numbers only |
| `data-checkout-line-price` | retained | same template(s); line numbers only |
| `data-checkout-lines` | retained | same template(s); line numbers only |
| `data-checkout-loading` | retired | prototype behaviour removed by the server-backed implementation |
| `data-checkout-next` | retained | same template(s); line numbers only |
| `data-checkout-panel` | retained | same template(s); line numbers only |
| `data-checkout-root` | retained | same template(s); line numbers only |
| `data-checkout-shipping` | retained | same template(s); line numbers only |
| `data-checkout-shipping-note` | retained | same template(s); line numbers only |
| `data-checkout-step` | retained | same template(s); line numbers only |
| `data-checkout-step-item` | retained | same template(s); line numbers only |
| `data-checkout-subtotal` | retained | same template(s); line numbers only |
| `data-checkout-total` | retained | same template(s); line numbers only |
| `data-checkout-vat` | retained | same template(s); line numbers only |
| `data-contact-form` | retained | same template(s); line numbers only |
| `data-contact-retry` | retained | same template(s); line numbers only |
| `data-contact-submit` | retained | same template(s); line numbers only |
| `data-coupon-form` | retained | same template(s); line numbers only |
| `data-coupon-status` | retained | same template(s); line numbers only |
| `data-coupon-submit` | retained | same template(s); line numbers only |
| `data-dialog-close` | retained | same template(s); line numbers only |
| `data-error-summary` | retained | same template(s); line numbers only |
| `data-error-summary-list` | retained | same template(s); line numbers only |
| `data-filter-open` | retained | same template(s); line numbers only |
| `data-filter-remove` | retained | same template(s); line numbers only |
| `data-filter-value` | retained | same template(s); line numbers only |
| `data-final-state` | retained | same template(s); line numbers only |
| `data-form-status` | retained | same template(s); line numbers only |
| `data-gallery-alt` | retained | same template(s); line numbers only |
| `data-gallery-image` | retained | same template(s); line numbers only |
| `data-gallery-main` | retained | same template(s); line numbers only |
| `data-go-step` | retained | same template(s); line numbers only |
| `data-initial-step` | retained | same template(s); line numbers only |
| `data-installation-fieldset` | retained | same template(s); line numbers only |
| `data-mobile-menu-trigger` | retained | same template(s); line numbers only |
| `data-page` | retained | same template(s); line numbers only |
| `data-payment-error` | retained | same template(s); line numbers only |
| `data-payment-form` | retained | same template(s); line numbers only |
| `data-product-card` | retained | same template(s); line numbers only |
| `data-product-gallery` | retained | same template(s); line numbers only |
| `data-product-id` | retained | same template(s); line numbers only |
| `data-products-menu-trigger` | retained | same template(s); line numbers only |
| `data-prototype-form` | retired | prototype behaviour removed by the server-backed implementation |
| `data-qa-state` | retained | same template(s); line numbers only |
| `data-quantity` | retained | same template(s); line numbers only |
| `data-quantity-minus` | retained | same template(s); line numbers only |
| `data-quantity-plus` | retained | same template(s); line numbers only |
| `data-result-count` | retained | same template(s); line numbers only |
| `data-retry-catalogue` | retained | same template(s); line numbers only |
| `data-review-customer` | retained | same template(s); line numbers only |
| `data-review-delivery` | retained | same template(s); line numbers only |
| `data-review-payment` | retained | same template(s); line numbers only |
| `data-search-close` | retained | same template(s); line numbers only |
| `data-search-trigger` | retained | same template(s); line numbers only |
| `data-share-product` | retained | same template(s); line numbers only |
| `data-shipping-error` | retained | same template(s); line numbers only |
| `data-shipping-form` | retained | same template(s); line numbers only |
| `data-shipping-message` | retained | same template(s); line numbers only |
| `data-shipping-option` | retained | same template(s); line numbers only |
| `data-shipping-options` | retained | same template(s); line numbers only |
| `data-shop-url` | retained | same template(s); line numbers only |
| `data-sort-form` | retained | same template(s); line numbers only |
| `data-state` | retained | same template(s); line numbers only |
| `data-to-payment` | retained | same template(s); line numbers only |
| `data-wishlist-add-cart` | retained | same template(s); line numbers only |
| `data-wishlist-availability` | retained | same template(s); line numbers only |
| `data-wishlist-card` | retained | same template(s); line numbers only |
| `data-wishlist-category` | retained | same template(s); line numbers only |
| `data-wishlist-count` | retained | same template(s); line numbers only |
| `data-wishlist-description` | retained | same template(s); line numbers only |
| `data-wishlist-empty` | retained | same template(s); line numbers only |
| `data-wishlist-grid` | retained | same template(s); line numbers only |
| `data-wishlist-image` | retained | same template(s); line numbers only |
| `data-wishlist-link` | retained | same template(s); line numbers only |
| `data-wishlist-loading` | retired | prototype behaviour removed by the server-backed implementation |
| `data-wishlist-name` | retained | same template(s); line numbers only |
| `data-wishlist-populated` | retained | same template(s); line numbers only |
| `data-wishlist-price` | retained | same template(s); line numbers only |
| `data-wishlist-product-link` | retained | same template(s); line numbers only |
| `data-wishlist-remove` | retained | same template(s); line numbers only |
| `data-wishlist-root` | retained | same template(s); line numbers only |
| `data-wishlist-toggle` | retained | same template(s); line numbers only |
| `data-wishlist-total` | retained | same template(s); line numbers only |

## Hooks added by the backend integration (17)

New controls the approved server-backed behaviour introduced (real forms,
variant identity, order lines). Additions are permitted by §5's
"add non-visual attributes for a11y/testing/JS hooks".

- `data-account-address` — templates/pages/account.html
- `data-account-order` — templates/pages/account.html
- `data-account-signout` — templates/pages/account.html
- `data-add-to-cart-form` — templates/pages/product_detail.html
- `data-cart-quantity-form` — templates/pages/cart.html
- `data-cart-unavailable` — templates/pages/cart.html
- `data-checkout-form` — templates/pages/checkout.html
- `data-finish-id` — templates/pages/product_detail.html
- `data-governorate` — templates/pages/checkout.html
- `data-login-form` — templates/pages/account.html
- `data-newsletter-form` — templates/components/newsletter.html
- `data-order-line` — templates/pages/order_confirmation.html
- `data-order-lines` — templates/pages/order_confirmation.html
- `data-register-form` — templates/pages/account.html
- `data-requires-area` — templates/pages/checkout.html
- `data-same-day` — templates/pages/checkout.html
- `data-variant-id` — templates/pages/cart.html

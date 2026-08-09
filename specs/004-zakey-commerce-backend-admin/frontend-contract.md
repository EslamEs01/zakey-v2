# Frontend Contract (Protected)

**Feature**: 004-zakey-commerce-backend-admin
**Status**: Binding. The backend is designed around this contract; this contract is not redesigned around the backend.

This document states exactly what the storefront renders and collects today, so the backend can replace the data source without changing a pixel or a URL. Everything here is extracted from the working tree at `98237d7`.

---

## 1. Money and localisation contract

| Rule | Value | Evidence |
|---|---|---|
| Currency code | `EGP` | `site.currency.code` |
| Currency label rendered | `ج.م` | `site.currency.label` |
| Decimal places displayed | **0** | `site.currency.decimalPlaces`; `Intl.NumberFormat(..., {maximumFractionDigits: 0})` at `pages/cart.js:6`, `pages/checkout.js:11`, `pages/wishlist.js:6` |
| VAT rate | `0.14` | `site.vatRate` |
| Free-shipping threshold | `1500` | `site.freeShippingThreshold`; also `shippingOptions[shipping-free].eligibility.minimumSubtotal = 1500` |
| Locale / direction | `ar-EG` / `rtl` | `site.locale`, `site.direction` |
| Product price type | **integer** EGP, range 2190–7490 | `products[].price`; enforced `fixture_provider.py:84` |
| `compareAtPrice` | present on every product, `null` in the sample data | `products[].compareAtPrice` |

### 1.1 VAT is INCLUSIVE — decided by evidence, not preference

```js
// static/src/js/pages/cart.js:58   (identical at pages/checkout.js:35)
const vat = Math.round((total * fixture.site.vatRate) / (1 + fixture.site.vatRate));
```

The formula `total × rate ÷ (1 + rate)` **extracts** VAT from a gross figure. If catalogue prices were VAT-exclusive the code would compute `subtotal × rate` and add it. It does not, and the VAT line never increases the total.

**Binding decision**: catalogue prices are **VAT-inclusive**. The VAT line is an informational breakdown of a gross amount ("of which VAT"), never an addition. The backend MUST preserve this. Reversing it would raise every displayed price by 14% and break the visual contract.

### 1.2 Totals formula rendered today

```js
subtotal = Σ (product.price × line.quantity)          // cart.js:54, checkout.js:26-29
discount = code === "ZAKEYDEMO" ? round(subtotal × 0.05) : 0   // cart.js:56, checkout.js:31-33
total    = subtotal − discount                         // cart.js:57, checkout.js:34
vat      = round(total × 0.14 / 1.14)                  // cart.js:58, checkout.js:35  (informational)
freeShipping = subtotal >= 1500                        // cart.js:59-60
```

> ⚠️ **Contract gap — the single most important integration risk in this feature.**
> The prototype total is `subtotal − discount`. **Shipping and installation are never added to it.** Shipping renders as a text label only (`"مجاني"` / `"يُحدد في الدفع"`, `cart.js:75`), and `shippingOptions` carry **no price field at all** — only `label`, `description`, `prototypeNotice`, `eligibility`, `icon`.
>
> A real backend must charge for shipping and installation, so the grand total will gain rows the prototype never displayed. This is a genuine, unavoidable change to rendered numbers. It is handled as a **planned, bounded integration change** (FR-041, FR-062, T-0803, T-1004) that adds rows inside the *existing* summary component using the existing markup pattern and Arabic label style. It does not restyle, reorder or restructure the summary. Shipping and installation prices are introduced as **new backend-owned data**, not recovered from the fixture, because the fixture does not contain them.

### 1.3 Rounding policy (backend)

Store money as `Decimal`. Never use `float`. Compute VAT as `gross × Decimal("14") / Decimal("114")`, quantized `ROUND_HALF_UP` to 2 decimal places for storage. Quantize to **0 decimal places** for display, matching `maximumFractionDigits: 0`. Line total = `unit_price × quantity` quantized before summing, so displayed rows always sum to the displayed subtotal.

---

## 2. Data contract by entity

### Product (9 records, 22 fields, all present on every record)

| Field | Type | Notes |
|---|---|---|
| `id` | str | e.g. `product-apex-pro` — stable identity, must be preserved |
| `slug` | str | e.g. `zakey-apex-pro` — **URL contract**, must be preserved |
| `name` | str (ar) | |
| `shortDescription` | str (ar) | searched together with `name` |
| `categoryId` | str | FK → category |
| `collectionIds` | list[str] | M2M → collections |
| `price` | int | VAT-inclusive EGP |
| `compareAtPrice` | int\|null | strike-through price |
| `badge` | str\|null | 7 distinct Arabic values in sample |
| `rating` | int | 1–5 |
| `reviewCount` | int | |
| `availability` | enum | `available` \| `limited` \| `unavailable` |
| `images` | list[{id, path, width, height, alt}] | **ordered**; `images[0]` is the primary (`fixture_provider.py:267`) |
| `finishes` | list[{id, label, swatch}] | **the variant axis**; `finishes[0]` is default (`fixture_provider.py:268`) |
| `features` | list[{key, label, description}] | `key` drives catalogue facet filtering |
| `specificationGroups` | list[{id, label, items:[{label,value}]}] | |
| `downloads` | list[{id, label, path, format, prototypeNotice}] | local PDFs |
| `reviewIds` | list[str] | 1:1 with reviews in sample |
| `faqIds` | list[str] | |
| `relatedProductIds` | list[str] | must exclude self (`fixture_provider.py:92-94`) |
| `instalmentMessage` | str (ar) | |
| `serviceFlags` | {sameDaySupported, installationSupported} | bool pair |

**Every product has ≥1 image and ≥1 finish** — `get_product` indexes `[0]` on both without a guard, so this is a hard invariant the backend must enforce.

### Category (4) / Collection (6)

Category: `id`, `slug`, `name`, `description`, `kind`, `image{path,width,height,alt}`.
Slugs: `fingerprint`, `keypad`, `smart-handle`, `accessories`.

Collection: `id`, `slug`, `name`, `description`, `productIds` (**ordered**), `promotion{eyebrow, tone}`.
Slugs: `best-sellers`, `featured`, `fingerprint-locks`, `security-accessories`, `smart-door-locks`, `smart-home-solutions`.

Verified: all 5 `/collections/<slug>/` references inside the fixture resolve to real collection slugs — **no dangling links**. All 6 slugs are part of the URL contract.

Home-page placement is derived from collection membership, not a flag: best-sellers = `collection-best`, featured = `collection-featured`, both sliced `[:4]` (`views.py:17-18`).

### Review (9) / FAQ (8)

Review: `id`, `productId`, `customerName`, `rating` (1–5), `quote`, `placement` (list, e.g. `["product","home"]`), `prototypeAttribution`.
Home testimonials = reviews with `"home"` in `placement`, sliced `[:3]` (`views.py:19`).

FAQ: `id`, `question`, `answer`, `page`, `productIds`.

### Governorate (27) / ServiceArea (14)

Governorate: `key`, label. Keys: `alexandria, aswan, asyut, beheira, beni-suef, cairo, dakahlia, damietta, faiyum, gharbia, giza, ismailia, kafr-el-sheikh, luxor, matrouh, minya, monufia, new-valley, north-sinai, port-said, qalyubia, qena, red-sea, sharqia, sohag, south-sinai, suez`. Exactly 27 enforced at `fixture_provider.py:74-75`.

Area: `key`, `governorateKey`, `label`, `sameDayEligible`, `installationEligible`.

- `sameDayAreaKeys` (8): `cairo-nasr-city, cairo-heliopolis, cairo-new-cairo, cairo-maadi, giza-dokki, giza-mohandessin, giza-sheikh-zayed, giza-october`
- `installationGovernorateKeys` (3): `cairo, giza, alexandria`

### ShippingOption (3) — labels only, no prices

| id | label | eligibility |
|---|---|---|
| `shipping-standard` | شحن قياسي | `{scope: all-governorates}` |
| `shipping-free` | شحن مجاني | `{scope: all-governorates, minimumSubtotal: 1500}` |
| `shipping-same-day` | توصيل في اليوم نفسه | `{scope: configured-areas, areaKeys: [8 keys]}` |

### PaymentOption (6) — display-only, zero integrations

`payment-cod`, `payment-instapay`, `payment-vodafone-cash`, `payment-etisalat-cash`, `payment-cashu`, `payment-installments`. Every one carries a `prototypeNotice` explicitly stating there is no provider connection. **No provider SDK, credential, endpoint or webhook exists anywhere in the repository.**

### Prototype account / cart / wishlist

Signed-in demo identity: name, email, phone, profile image, 1 address (`{id, label, governorateKey, areaKey, street, building}`), 2 order-history rows (`{id, referenceLabel, displayDate, productIds, displayTotal, statusLabel}`). These are **inert display rows**, not orders.

Cart states (6): `cart-empty`, `cart-populated`, `cart-coupon-loading`, `cart-coupon-accepted`, `cart-coupon-rejected`, `cart-coupon-recoverable-error`. Line shape: `{productId, quantity, finishId}`.

---

## 3. Client state contract

Single `localStorage` key: **`zakey:prototype:v1`** (`state/storage-adapter.js:1`), envelope `{version:1, cart, wishlist, account}`.

| Rule | Value | Evidence |
|---|---|---|
| Quantity bounds | **1–9** | `storage-adapter.js:22`, `store.js:27,28,36`, `product.js:5,14`, `cart.js:99` |
| Cart line identity | `productId` + `finishId` on **add** | `store.js:24-26` |
| Cart line identity | `productId` **only** on update/remove | `store.js:34,41` ⚠️ |
| Unavailable products | cannot be added | `store.js:23` |
| Wishlist | unique `productId` set | `storage-adapter.js:28` |
| Account | `{mode: signed-out\|signed-in, tab}` | `storage-adapter.js:31-35` |

> ⚠️ **Prototype defect, do not port.** `addToCart` keys a line by `(productId, finishId)`, but `updateQuantity` and `removeFromCart` match on `productId` alone. Two finishes of one product therefore cannot be independently updated or removed. The backend cart MUST key lines by `(product, variant)` consistently — see FR-030 and T-0703.

Custom events (`zakey:` prefix): `cart-change`, `wishlist-change`, `catalogue-change`, `prototype-status`, `account-state-change`.

**No `fetch` or `XMLHttpRequest` exists in any module.**

---

## 4. Interaction contract

| Interaction | Today | Backend target |
|---|---|---|
| Search | GET `?q=`, server-filtered | Unchanged; query the DB |
| Filter / sort / page | GET params, server-filtered, page size 6 | Unchanged; query the DB |
| Catalogue re-render | `catalogue.js` mirrors server logic client-side | Server-rendered stays authoritative |
| Gallery | `images[0]` default, thumbnails swap | Unchanged |
| Finish selection | radio `name="finish"` | Becomes variant selection |
| Add to cart | `store.addToCart`, localStorage | POST → server cart |
| Quantity ± | clamp 1–9, localStorage | POST → server, re-validated |
| Remove | localStorage | POST → server |
| Wishlist toggle | localStorage | POST → server (session or account) |
| Coupon | compares to `ZAKEYDEMO`, 5%, 350 ms fake delay | POST → server validation |
| Checkout step 1 | client validation, then step 2 | POST → server validation, same messages |
| Checkout step 2 | requires a `paymentMethod` radio | POST → server |
| Checkout step 3 | shows "submission unavailable" | POST → real order creation |
| Governorate → area | filters `areas` by `governorateKey` | Server-provided, same shape |
| Same-day eligibility | `sameDayAreaKeys.includes(areaKey)` | Server rule |
| Installation eligibility | `installationGovernorateKeys.includes(governorate)` | Server rule |
| Free shipping | `subtotal >= 1500` | Server rule |
| Account | `?state=` / `?tab=` demo switch | Real auth session |

### Validation rules to preserve exactly

From `pages/checkout.js:145-158` and `utilities/dom.js:31-39`:

| Field | Rule | Arabic message (must be preserved) |
|---|---|---|
| `fullName` | ≥2 chars **and** contains an Arabic letter `[؀-ۿ]` | اكتب الاسم بالكامل بالعربية. |
| `email` | `/^[^\s@]+@[^\s@]+\.[^\s@]+$/` | اكتب بريدًا إلكترونيًا صحيحًا، مثل name@example.com. |
| `mobile` | `/^01[0125]\d{8}$/` after normalising `+20`/`20` prefix **and** Arabic-Indic digits | اكتب رقم موبايل مصريًا صحيحًا من 11 رقمًا. |
| `governorate` | required | اختر المحافظة. |
| `city` | ≥2 chars | اكتب اسم المدينة أو المركز. |
| `street` | ≥4 chars | اكتب اسم الشارع والعنوان التفصيلي. |
| `building` | required | اكتب رقم المبنى. |
| `shippingMethod` | required | اختر طريقة الشحن. |
| `acknowledgement` | required | أكد فهمك أن هذه واجهة تجريبية. |

Egyptian mobile normalisation (`dom.js:31-37`): strip non-digits except `+`; `+20…` → `0…`; `20…` (12 chars) → `0…`; then match `^01[0125]\d{8}$`. The backend validator MUST reproduce this, including Arabic-Indic digit folding (`checkout.js:139-143`).

The `acknowledgement` checkbox exists because submission is non-functional. Once real orders exist it becomes a terms acceptance — a label change inside the existing control, recorded as an approved integration change (FR-063).

---

## 5. Protected surface — the do-not-change list

Unchanged by this feature: all 13 URLs and route names; page structure and section order; Arabic content and RTL; colours, typography, spacing, the 12-column grid, 8px spacing, 12px radii; every component (`product_card`, `catalogue_filters`, `newsletter`, `icon`, header, footer); gallery, filters, search, cart, wishlist, checkout, account UI; drawers, tabs, accordions, dialogs; animations and reduced-motion; focus management, live regions, keyboard nav; responsive behaviour at 1440/1024/768/390; the Tailwind architecture; the no-SPA, no-framework rule.

Permitted integration changes (and only these): swap fixture calls for QuerySets/services behind the same context keys; add `method="post"` + `{% csrf_token %}` + hidden ids to existing forms; replace hardcoded hrefs with `{% url %}`; replace `localStorage` reads through an isolated adapter; render real auth/order state into existing regions; put validation messages into the existing `.field-error` / `[data-error-summary]` regions; add non-visual attributes for a11y/testing/JS hooks; **add shipping and installation rows to the existing summary component (§1.2)**.

The 139 `data-*` hooks are behavioural API. Renaming any of them is a breaking change requiring a matching JS edit and a visual-regression pass.

---

## 6. Enforcement

Every task in `tasks.md` that touches `templates/` or `static/` carries a mandatory visual-regression gate at 1440/1024/768/390 plus zero-console-error, no-horizontal-overflow, RTL-intact and axe-clean checks. See `contracts/frontend-preservation-boundary.md` for the gate definition and `test-strategy.md` §7 for how it runs.

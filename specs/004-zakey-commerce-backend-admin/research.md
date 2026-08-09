# Research and Architecture Decisions

**Feature**: 004-zakey-commerce-backend-admin
**Decision owner**: Claude. Evidence gathering: Kimi + deterministic extraction.

Each decision records what the repository actually shows, the options considered, the decision, and what would change it.

---

## 1. VAT: inclusive or exclusive? — **RESOLVED BY CODE**

**Evidence**: `static/src/js/pages/cart.js:58` and `pages/checkout.js:35`:
```js
const vat = Math.round((total * fixture.site.vatRate) / (1 + fixture.site.vatRate));
```

`total × r ÷ (1+r)` is the extraction formula. VAT-exclusive pricing would compute `subtotal × r` and add it. The VAT line never increases the total anywhere in the codebase.

**Decision**: prices are **VAT-inclusive**; VAT is an informational breakdown of a gross amount.
**Why it matters**: reversing this would raise every displayed price by 14% and break the approved visual contract.
**Would change if**: the business states catalogue prices are net — which would be a pricing change requiring re-approval of the storefront, not a backend decision.

---

## 2. Where do shipping and installation costs come from? — **GAP, ESCALATED**

**Evidence**: `shippingOptions` contain `id`, `label`, `description`, `prototypeNotice`, `eligibility`, `icon` — **no price field**. `serviceEligibility` has no fee. The rendered total is `subtotal − discount` only; shipping renders as the text `"مجاني"` or `"يُحدد في الدفع"` (`cart.js:75`).

**Decision**: model `ShippingRate` (per method × zone) and `InstallationService.fee` as staff-configurable, seeded with **clearly-labelled development placeholders**. Adding shipping and installation rows to the order total is an approved bounded integration change (FR-041, FR-062).
**Escalated**: real commercial rates are business input required **before launch, not before implementation** (ASM-004, ASM-005). Implementation is unblocked because the values are configuration, not architecture.
**Rejected**: inventing plausible rates and seeding them silently — that would put invented commercial claims in front of customers.

---

## 3. Application structure

**Considered**: (a) one `store` app; (b) the 15 apps named in the brief; (c) evidence-driven consolidation.

**Decision — 12 apps**:

`core`, `accounts`, `catalog`, `inventory`, `cart`, `shipping`, `promotions`, `orders`, `payments`, `reviews`, `content`, `audit`.

**Merged, with reasons**:

| Proposed | Outcome | Reason |
|---|---|---|
| `wishlist` | → `cart` | Same lifecycle, same session/customer ownership, same merge-on-login logic. A separate app would duplicate all of it for two small models. |
| `checkout` | → `orders` | Checkout has no persistent model of its own; it is the order-creation service. A separate app would only hold a service module that mutates another app's models. |
| `notifications` | → `core` | Launch scope is Django SMTP email only. A dedicated app is justified when a provider, templates and queues arrive — recorded as deferred. |

**Kept separate**: `inventory` from `catalog` (different write patterns, different locking, different permissions); `payments` from `orders` (provider boundary must not leak into order logic); `audit` standalone (append-only, no dependencies).

**Would change if**: notifications gain a provider and templates → promote to its own app.

---

## 4. Service layer

**Decision**: services for money, stock and state transitions only — `orders.services.create_order`, `inventory.services.reserve/release/fulfill`, `promotions.services.apply_coupon`, `payments.services.*`, `cart.services.merge_cart`. Read paths use thin selectors (`catalog.selectors.published_products`). Simple CRUD stays in models and admin.

**Rejected**: a service class for every model (ceremony without benefit), and business logic in views (untestable, and the storefront already proved rules scattered across layers drift).

---

## 5. Variants — what is the axis?

**Evidence**: every product has a `finishes` array (`{id, label, swatch}`); the cart line stores `finishId`; the product page has `<input name="finish" type="radio">`; `fixture_provider.py:268` defaults to `finishes[0]`. No other option dimension exists.

**Decision**: `ProductVariant` with a single finish axis. Price and SKU live on the variant. Products with one finish get one default variant, so the model is uniform and no code branches on "has variants".
**Would change if**: a second axis (size, keyway) appears → add an option/value model; the variant table already supports it.

---

## 6. Infrastructure deliberately excluded

| Technology | Decision | Condition that would introduce it |
|---|---|---|
| **Celery + Redis** | Excluded | Only async needs are email and reservation sweeping. Email → `send_mail` synchronously; sweeping → cron management command. Introduce when email volume blocks requests or scheduled work exceeds cron. |
| **Redis cache** | Excluded | Catalogue is 9 products. Caching stock, prices or permissions without an invalidation strategy is actively dangerous (§8). Introduce with a written invalidation plan when catalogue reaches thousands of SKUs. |
| **DRF / GraphQL** | Excluded | Storefront is server-rendered; zero `fetch` calls exist. Cart and checkout POST to Django views returning redirects or rendered fragments. Introduce for a mobile app — explicitly out of scope. |
| **Elasticsearch** | Excluded | Search is `name` + `shortDescription` over 9 products. PostgreSQL `ILIKE` now; `pg_trgm` + GIN when the catalogue grows; Elasticsearch only for faceted search at scale. |
| **HTMX / Alpine** | Excluded | Would replace the approved native-JS architecture and violate the constitution. |

Adding any of these without a verified requirement is scope expansion.

---

## 7. Cart storage

**Decision**: database-backed for both anonymous (keyed by `session_key`) and authenticated (keyed by `customer`).
**Rejected**: session-serialised carts (invisible to admin, unqueryable for abandoned-cart reporting, no FK integrity); cookie carts (size limits, tamperable — and FR-034 requires the server to own totals anyway).
**Merge**: on login, sum quantities per `(variant)`, clamp to available stock and to 9, keep the account cart's coupon if still valid.

---

## 8. Caching

**Decision**: no caching of stock, prices, cart, permissions or order state — full stop. Template-fragment caching is permitted **only** for static content (footer, navigation, static pages) with explicit invalidation on save.
**Reason**: a stale stock or price cache causes overselling or mispricing, which is a financial defect, not a performance trade-off.

---

## 9. Delegation findings (Kimi)

**Batch 1** (route, fixture, JS, forms inventories): all four invocations reached the 25-minute wall clock and were killed at exit 124 before writing their reports. Kimi's reasoning was demonstrably sound — its transcript independently derived the correct fixture section counts, correctly concluded that no view computes totals, and correctly identified the 1:1 product↔review mapping, all of which Claude verified independently. The failure was scope and output strategy, not capability.

**Claude's corrections**:
1. Narrowed each assignment to a named, short file list.
2. Required the output file to be written **early and appended to**, never composed only at the end.
3. Raised the budget to 50 minutes.
4. Moved all mechanical extraction (form fields, `data-*` hooks, fixture schema, line numbers) to deterministic scripts — faster than an LLM and not subject to hallucination.

**Batch 2** with those corrections produced files immediately and successfully.

**Carried into `tasks.md`**: Kimi assignments are bounded to ≤3 files with explicit acceptance criteria and test commands; evidence that can be computed is computed, not narrated.

---

## 10. Deferred ideas (recorded, NOT in scope)

Multi-warehouse inventory; abandoned-cart recovery email; product Q&A; bundles and kits; gift cards; store credit; loyalty points; subscriptions; multi-currency; Arabic/English bilingual storefront; live gateway integration (Paymob, Fawry, Stripe); SMS notifications; ERP/accounting export; advanced faceted search; product recommendations; A/B testing; customer segmentation; warehouse barcode scanning.

These are recorded so they are not lost. **None may enter this feature's scope.**

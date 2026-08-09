# Fixture-to-Database Migration Map

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-120 – FR-124.

Source: `storefront/fixtures/frontend-fixtures.json` (58,562 bytes, `schemaVersion: 1`).
Target: models in `data-model.md`.
Executor: `python manage.py seed_demo`.

**Preservation rule**: every `id`, `slug`, Arabic string, image path and price transfers **unchanged**. Ids become `legacy_id` so the command is idempotent and so seeded rows can be matched on re-run.

---

## 1. Section-by-section mapping

| Fixture section | Records | Target model(s) | Match key |
|---|---|---|---|
| `meta` | 3 keys | — (validation only) | — |
| `site` | 15 keys | `core.SiteSetting` (singleton) | pk=1 |
| `navigation` | 4 keys | `content.NavigationItem` | `(group, position)` |
| `categories` | 4 | `catalog.Category` | `slug` |
| `collections` | 6 | `catalog.Collection` + `CollectionProduct` | `slug` |
| `products` | 9 | `catalog.Product` + `ProductVariant` + `ProductImage` + `ProductFeature` + `SpecificationGroup`/`Item` + `ProductDocument` + `ProductRelation` | `slug` |
| `reviews` | 9 | `reviews.Review` | `legacy_id` |
| `faqs` | 8 | `content.FAQ` | `legacy_id` |
| `partners` | 4 | `content.Partner` | `name` |
| `team` | 4 | `content.StaticPage` (About) | — |
| `governorates` | 27 | `shipping.Governorate` | `key` |
| `serviceEligibility.areas` | 14 | `shipping.ServiceArea` | `key` |
| `shippingOptions` | 3 | `shipping.ShippingMethod` (+ placeholder `ShippingRate`) | `code` |
| `paymentOptions` | 6 | `payments.PaymentMethod` | `code` |
| `prototypeAccounts` | 2 | **NOT SEEDED** (see §4) | — |
| `prototypeCarts` | 6 | **NOT SEEDED** | — |
| `prototypeWishlists` | 2 | **NOT SEEDED** | — |

---

## 2. Field-level mapping

### `site` → `core.SiteSetting`

| Fixture | Field | Value |
|---|---|---|
| `site.vatRate` | `vat_rate` | `0.14` → `Decimal("0.1400")` |
| `site.freeShippingThreshold` | `free_shipping_threshold` | `1500` → `Decimal("1500.00")` |
| `site.currency.code` / `.label` / `.decimalPlaces` | `currency_code` / `currency_label` / `currency_decimal_places` | `EGP` / `ج.م` / `0` |
| `site.announcement`, `.contact`, `.footer`, `.newsletter` | corresponding text fields | verbatim |
| `site.couponPrototype` | `promotions.Coupon` | **development only** (§4) |

### `products[]` → `catalog.*`

| Fixture field | Target |
|---|---|
| `id` | `Product.legacy_id` |
| `slug` | `Product.slug` — **URL contract, must not change** |
| `name`, `shortDescription` | `Product.name`, `.short_description` |
| `categoryId` | `Product.category` (via `Category.legacy_id`) |
| `collectionIds[]` | `CollectionProduct` rows, position = index |
| `price` | `ProductVariant.price` (`Decimal(str(price))`) |
| `compareAtPrice` | `ProductVariant.compare_at_price` (null-safe) |
| `badge` | `Product.badge` |
| `rating`, `reviewCount` | `Product.rating_average`, `.review_count` (recomputed after reviews load) |
| `availability` | **not stored** — derived from seeded stock (§3) |
| `images[]` | `ProductImage` — `id`→`legacy_id`, `path`→`legacy_path`, `alt`, `width`, `height`, position = index |
| `finishes[]` | `ProductVariant` — `id`→`finish_id`, `label`→`finish_label`, `swatch`→`swatch_hex`, position = index, `is_default` on index 0 |
| `features[]` | `ProductFeature` — `key`, `label`, `description`, position |
| `specificationGroups[]` | `SpecificationGroup` + nested `SpecificationItem` |
| `downloads[]` | `ProductDocument` |
| `reviewIds[]` | resolved in pass 2 |
| `faqIds[]` | `FAQ` M2M in pass 2 |
| `relatedProductIds[]` | `ProductRelation` in pass 2 |
| `instalmentMessage` | `Product.instalment_message` |
| `serviceFlags.sameDaySupported` / `.installationSupported` | `Product.same_day_supported` / `.installation_supported` |

**SKU generation**: `ZK-{product.slug.upper()}-{finish_id.split('-')[-1].upper()}` → e.g. `ZK-ZAKEY-APEX-PRO-OBSIDIAN`. Deterministic, so re-running produces the same SKU (INV-008).

**Price ownership**: the fixture holds one price per product; each finish inherits it. Per-finish pricing becomes possible immediately because price lives on the variant (FR-017).

### `shippingOptions[]` → `shipping.*`

| Fixture | Target | Note |
|---|---|---|
| `id` | `ShippingMethod.code` | `shipping-standard`, `shipping-free`, `shipping-same-day` |
| `label`, `description`, `icon` | matching fields | verbatim |
| `eligibility.minimumSubtotal` | `ShippingRate.free_over` | 1500 for `shipping-free` |
| `eligibility.areaKeys` | `requires_area_eligibility=True` + `ServiceArea.same_day_eligible` | 8 areas |
| **(absent)** | `ShippingRate.price` | ⚠️ **development placeholder** — ASM-004 |

### `paymentOptions[]` → `payments.PaymentMethod`

All 6 seeded with `is_active=True`, `is_integrated=False`. `payment-cod` additionally gets an operational handler. The others render exactly as today with their existing notices (FR-072).

---

## 3. Derived seed data (not in the fixture)

| Data | Rule |
|---|---|
| `StockItem` | From `availability`: `available` → 25 on hand; `limited` → 3; `unavailable` → 0. Reproduces the exact catalogue filter behaviour of `fixture_provider.py:183-190`, where `available` matches both `available` and `limited`. |
| `ShippingRate.price` | ⚠️ Development placeholder, labelled as such |
| `InstallationService.fee` | ⚠️ Development placeholder, labelled as such |
| Staff groups | The 9 roles from `permissions-matrix.md` |
| `Coupon` `ZAKEYDEMO` | 5%, **development environments only** |

---

## 4. Explicitly NOT migrated

| Fixture data | Reason |
|---|---|
| `prototypeAccounts` | Demo identity with a fake email/phone. Seeding it would create a fake customer indistinguishable from a real one. Dev-only optional flag `--with-demo-customer`. |
| `orderHistory` rows | **Inert display content, not orders** (ASM-007). They have no line items, no payment, no address and no status machine. Seeding them would fabricate revenue. |
| `prototypeCarts` / `prototypeWishlists` | QA state fixtures for the browser prototype, not customer data. |
| `ZAKEYDEMO` in production | Not a real commercial offer (ASM-006). |

This is the single most important rule in this document: **the prototype's demonstration commerce state must never become production data.**

---

## 5. Command contract

```
python manage.py seed_demo [--force] [--with-demo-customer] [--dry-run]
```

- **Idempotent**: matches on `slug` / `key` / `code` / `legacy_id`; updates in place; never duplicates (FR-121).
- **Ordered**: settings → geography → shipping → payment → categories → collections → products (pass 1) → reviews → FAQs → cross-references (pass 2) → stock → groups.
- **Atomic per section**, so one bad section cannot half-write.
- **Refuses** to run when `Order.objects.exists()` unless `--force` (FR-122).
- **Never** runs automatically; not in migrations, not in deploy.
- **Reports** created / updated / skipped / failed per model, and exits non-zero on any failure.
- `--dry-run` reports without writing.

## 6. Verification

| Check | Assertion |
|---|---|
| Slug preservation | All 9 product, 6 collection, 4 category slugs resolve (SC-011) |
| Governorates | Exactly 27, keys match the fixture set |
| Idempotency | Two runs → identical row counts, zero duplicates (SC-010) |
| Referential integrity | Every related-product, review and FAQ reference resolves |
| Prices | Every seeded variant price equals the fixture price exactly |
| Images | Every `legacy_path` resolves to a file on disk |
| Availability parity | Catalogue filtered by `availability=available` returns the same product ids as the fixture provider does today |
| No fake orders | `Order.objects.count() == 0` after seeding |

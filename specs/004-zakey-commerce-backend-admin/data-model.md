# Data Model

**Feature**: 004-zakey-commerce-backend-admin

Money is `DecimalField(max_digits=12, decimal_places=2)` everywhere. `Decimal` only — never `float` (INV-012). All customer-facing text is Arabic. Every model carries `created_at` / `updated_at` unless stated. Field names map to the frontend contract in `fixture-migration-map.md`.

---

## `core`

**SiteSetting** (singleton) — `vat_rate` Decimal(5,4) default `0.1400`; `free_shipping_threshold` Decimal default `1500.00`; `currency_code` `EGP`; `currency_label` `ج.م`; `currency_decimal_places` int default `0`; `order_number_prefix` default `ZK`; `cart_ttl_days` default 30; `reservation_ttl_minutes` default 60; `low_stock_threshold` default 5; `max_line_quantity` default 9; announcement, contact, social and prototype-notice text.
*Enforced singleton (pk=1). Source of every commerce constant (FR-005).*

**TimeStampedModel**, **SoftArchivableModel** (`status`, `archived_at`) — abstract bases.
**MoneyField** — helper enforcing quantization (FR-043).

---

## `accounts`

**User** — Django `AbstractUser` subclass, `USERNAME_FIELD = "email"`, `email` unique, `is_staff`, `is_active`.

**CustomerProfile** — `user` O2O; `full_name`; `phone` (normalised `01[0125]XXXXXXXX`, unique among verified); `phone_verified` bool; `email_verified` bool; `accepts_marketing` bool; `avatar` image.
*Constraint*: `UniqueConstraint(phone, condition=Q(phone_verified=True))`.

**Address** — `customer` FK; `label`; `full_name`; `phone`; `governorate` FK; `area` FK null; `city`; `street`; `building`; `landmark` null; `is_default` bool.
*Constraint*: `UniqueConstraint(customer, condition=Q(is_default=True))` — exactly one default (INV-014).

---

## `catalog`

**Category** — `parent` FK self null; `slug` unique; `name`; `description`; `image`; `kind`; `position`; `status`; `seo_title`; `seo_description`.
*Seeds*: `fingerprint`, `keypad`, `smart-handle`, `accessories`.

**Brand** — `slug` unique; `name`; `logo`.

**Collection** — `slug` unique; `name`; `description`; `promotion_eyebrow`; `promotion_tone`; `position`; `status`; M2M to Product **through** `CollectionProduct` (`position`) to preserve fixture ordering.
*Seeds*: `best-sellers`, `featured`, `fingerprint-locks`, `security-accessories`, `smart-door-locks`, `smart-home-solutions`.

**Product** — `slug` unique (INV-009); `name`; `short_description`; `description`; `category` FK PROTECT; `brand` FK null; `badge` null; `status` (`draft`/`published`/`archived`); `published_at`; `instalment_message`; `same_day_supported` bool; `installation_supported` bool; `seo_title`; `seo_description`; `rating_average` Decimal(3,2) system-maintained; `review_count` int system-maintained; `position`.
*Derived*: `display_price` = default variant price; `availability` ∈ {`available`,`limited`,`unavailable`} derived from stock (FR-018).
*Constraint*: `CheckConstraint` that a published product has ≥1 variant and ≥1 image (validated in service + admin; FR-015).

**ProductVariant** — `product` FK CASCADE; `sku` **unique globally** (INV-008); `finish_id` (preserves fixture `finishes[].id`); `finish_label`; `swatch_hex`; `price` Decimal (VAT-inclusive, FR-017); `compare_at_price` Decimal null; `position`; `is_default` bool; `is_active` bool.
*Constraints*: `UniqueConstraint(sku)`; `UniqueConstraint(product, condition=Q(is_default=True))`; `CheckConstraint(price > 0)`; `CheckConstraint(compare_at_price IS NULL OR compare_at_price > price)`.

**ProductImage** — `product` FK; `image`; `alt` (required, Arabic); `width`; `height`; `position`; `legacy_path` (fixture path for seed idempotency).
*Ordering*: `position` — `position=0` is primary.

**ProductFeature** — `product` FK; `key` (drives catalogue facets); `label`; `description`; `position`.
*Index on `key`.*

**SpecificationGroup** — `product` FK; `label`; `position`.
**SpecificationItem** — `group` FK; `label`; `value`; `position`.

**ProductDocument** — `product` FK; `label`; `file`; `format`; `position`.

**ProductRelation** — `from_product` FK; `to_product` FK; `position`.
*Constraints*: `UniqueConstraint(from_product, to_product)`; `CheckConstraint(from_product != to_product)`.

---

## `inventory`

**StockItem** — `variant` O2O PROTECT; `on_hand` int; `reserved` int; `low_stock_threshold` int null (falls back to SiteSetting).
*Derived*: `available = on_hand − reserved`.
*Constraints*: `CheckConstraint(on_hand >= 0)`; `CheckConstraint(reserved >= 0)`; `CheckConstraint(reserved <= on_hand)` — this last one is what makes overselling structurally impossible (INV-001).

**StockMovement** (append-only) — `stock_item` FK PROTECT; `delta` int; `reason` enum (`purchase`,`reserve`,`release`,`fulfill`,`return`,`adjust`,`damaged`,`lost`,`correction`); `on_hand_before`; `on_hand_after`; `reserved_before`; `reserved_after`; `order` FK null; `actor` FK null; `note`; `created_at`.
*No update/delete permitted, including for superusers (FR-105).*

**StockReservation** — `stock_item` FK; `order` FK null; `cart` FK null; `quantity`; `expires_at`; `state` (`active`,`released`,`consumed`,`expired`).
*Index on `(state, expires_at)` for the sweeper (FR-024).*

---

## `shipping`

**Governorate** — `key` unique (27 fixture keys); `name_ar`; `position`; `is_active`.
**ServiceArea** — `key` unique; `governorate` FK; `name_ar`; `same_day_eligible` bool; `installation_eligible` bool; `is_active`.
**ShippingZone** — `name`; M2M Governorate; `position`.
**ShippingMethod** — `code` unique (`shipping-standard`, `shipping-free`, `shipping-same-day`); `label`; `description`; `icon`; `is_active`; `position`; `requires_area_eligibility` bool.
**ShippingRate** — `method` FK; `zone` FK; `price` Decimal; `free_over` Decimal null; `estimated_delivery_text`; `is_active`.
*Constraint*: `UniqueConstraint(method, zone)`.
> ⚠️ Rates are seeded with clearly-labelled **development placeholders** — real commercial values are business input (ASM-004).

**InstallationService** — `name`; `fee` Decimal; M2M Governorate (eligible: `cairo`,`giza`,`alexandria`); `is_active`.
> ⚠️ Fee is a development placeholder (ASM-005).

---

## `cart`

**Cart** — `customer` FK null; `session_key` null; `status` (`active`,`merged`,`converted`,`abandoned`); `coupon` FK null; `expires_at`.
*Constraint*: `UniqueConstraint(customer, condition=Q(status="active"))`; `UniqueConstraint(session_key, condition=Q(status="active"))`.

**CartLine** — `cart` FK; `variant` FK PROTECT; `quantity` int.
*Constraints*: `UniqueConstraint(cart, variant)` — **this is FR-030**, the fix for the prototype defect; `CheckConstraint(1 <= quantity <= 9)`.
*No price stored* — always recomputed from the variant (FR-034).

**Wishlist** — `customer` FK null; `session_key` null.
**WishlistItem** — `wishlist` FK; `product` FK.
*Constraint*: `UniqueConstraint(wishlist, product)`.

---

## `promotions`

**Coupon** — `code` unique **uppercase** (FR-085); `discount_type` (`percentage`,`fixed`); `value` Decimal; `max_discount` Decimal null; `starts_at`; `ends_at`; `usage_limit` int null; `per_customer_limit` int null; `minimum_subtotal` Decimal null; M2M Product; M2M Category; `is_active`; `times_used` int.
*Constraints*: `CheckConstraint(value > 0)`; `CheckConstraint(ends_at IS NULL OR ends_at > starts_at)`; `CheckConstraint(times_used <= usage_limit)` when limit set (INV-005).

**CouponRedemption** — `coupon` FK PROTECT; `order` FK; `customer` FK null; `amount` Decimal; `created_at`.
*Constraint*: `UniqueConstraint(coupon, order)`.

---

## `orders`

**Order** — `number` unique (INV-007); `customer` FK null (guest allowed, ASM-002); `email`; `phone`; `status`; `payment_status`; `fulfillment_status`; `idempotency_key` **unique** (INV-002); `subtotal`; `discount_total`; `coupon_code` (snapshot string); `shipping_method_label` (snapshot); `shipping_total`; `installation_requested` bool; `installation_total`; `vat_amount`; `grand_total`; `terms_accepted_at` (FR-063); `placed_at`; `cancelled_at`; `notes`.
*Constraints*: `UniqueConstraint(number)`; `UniqueConstraint(idempotency_key)`; `CheckConstraint(grand_total >= 0)`.
*All monetary fields are immutable snapshots (INV-003).*

**OrderLine** — `order` FK PROTECT; `variant` FK **SET_NULL** (so archived products never orphan history); snapshots: `product_name`, `variant_label`, `sku`, `unit_price`, `quantity`, `line_total`, `product_slug`, `image_path`.
*Snapshots are read-only after creation (FR-105, INV-003).*

**OrderAddress** — `order` O2O; full snapshot of `full_name`, `phone`, `governorate_key`, `governorate_name`, `area_key`, `area_name`, `city`, `street`, `building`, `landmark`.
*Snapshot, not FK — FR-067.*

**OrderEvent** (append-only) — `order` FK; `event_type`; `from_status`; `to_status`; `actor` FK null; `note`; `request_id`; `created_at`.

**OrderNote** — `order` FK; `author` FK; `body`; `is_customer_visible` bool.

---

## `payments`

**PaymentMethod** — `code` unique (`payment-cod`, `payment-instapay`, `payment-vodafone-cash`, `payment-etisalat-cash`, `payment-cashu`, `payment-installments`); `label`; `description`; `icon`; `is_active`; `is_integrated` bool (**all False at launch**, FR-071/072); `position`.

**Payment** — `order` FK PROTECT; `method` FK PROTECT; `amount` Decimal; `currency` default `EGP`; `state` (`pending`,`authorised`,`captured`,`failed`,`cancelled`,`refunded`,`partially_refunded`); `provider_reference` null; `idempotency_key` unique null; `captured_at`; `failed_reason`.
*Constraint*: `CheckConstraint(amount > 0)`.

**PaymentEvent** (append-only) — `payment` FK; `event_type`; `provider_event_id` **unique** (kills webhook replay, FR-074); `payload_digest` (hash only, never raw card data, FR-077); `created_at`.

**Refund** — `payment` FK PROTECT; `amount` Decimal; `reason`; `state` (`pending`,`completed`,`failed`); `actor` FK; `provider_reference` null; `created_at`.
*Constraint*: `CheckConstraint(amount > 0)` plus a service-level locked check that `Σ completed refunds ≤ captured` (INV-004, FR-075).

---

## `reviews`

**Review** — `product` FK; `customer` FK null; `author_name`; `rating` int 1–5; `title`; `body`; `status` (`pending`,`approved`,`rejected`); `is_verified_purchase` bool; `staff_response`; `placement` (list, preserves fixture `["product","home"]`); `created_at`; `moderated_by`; `moderated_at`.
*Constraints*: `CheckConstraint(1 <= rating <= 5)`; `UniqueConstraint(product, customer)` where customer not null (FR-093).

---

## `content`

**HomeSection** — `key`; `heading`; `body`; `position`; `is_active`.
**Banner** — `title`; `image`; `link`; `position`; `is_active`; window dates.
**Partner** — `name`; `logo`; `position`.
**Testimonial** — sourced from approved `Review` where `"home" in placement`.
**FAQ** — `question`; `answer`; `page`; M2M Product; `position`; `is_active`.
**StaticPage** — `slug` unique; `title`; `body`; `seo_title`; `seo_description`; `is_published`.
**NavigationItem** — `parent` FK self null; `label`; `href` or named route; `icon`; `position`; `group` (`primary`,`utility`,`footer`).
**NewsletterSubscription** — `email` unique; `source`; `confirmed`; `created_at`.
**ContactMessage** — `name`; `email`; `phone`; `subject`; `message`; `status`; `created_at`; `ip_hash`.

---

## `audit`

**AuditLog** (append-only, immutable) — `actor` FK null; `action`; `content_type` FK; `object_id`; `object_repr`; `changes` JSON (before/after, redacted); `request_id`; `ip_hash`; `created_at`.
*No update or delete path exists in code or admin (FR-114, INV-013).*

---

## Index plan

| Table | Index | Why |
|---|---|---|
| `Product` | `(status, published_at)` | Catalogue listing |
| `Product` | `slug` unique | Detail route |
| `Product` | `(category, status)` | Category filter |
| `ProductFeature` | `key` | Facet filter |
| `ProductVariant` | `sku` unique | Lookup + INV-008 |
| `CollectionProduct` | `(collection, position)` | Ordered collection |
| `StockItem` | `variant` unique | Reservation lock |
| `StockMovement` | `(stock_item, -created_at)` | Ledger view |
| `StockReservation` | `(state, expires_at)` | Sweeper |
| `Order` | `number` unique | Lookup |
| `Order` | `idempotency_key` unique | INV-002 |
| `Order` | `(status, -placed_at)` | Admin + dashboard |
| `Order` | `(customer, -placed_at)` | Account history |
| `OrderLine` | `order` | Detail join |
| `Payment` | `(order, state)` | Reconciliation |
| `PaymentEvent` | `provider_event_id` unique | Replay defence |
| `Coupon` | `code` unique | Apply |
| `CouponRedemption` | `(coupon, order)` unique | INV-005 |
| `Review` | `(product, status)` | Public list |
| `AuditLog` | `(content_type, object_id, -created_at)` | Object history |

## Deletion policy

`PROTECT` on anything an order references (variant via `OrderLine` uses `SET_NULL` plus snapshots so history survives archival). Products, variants, categories and collections are **archived**, never deleted, once ordered (FR-014, FR-109). `StockMovement`, `PaymentEvent`, `OrderEvent` and `AuditLog` have no delete path at all.

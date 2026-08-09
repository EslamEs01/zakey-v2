# Jazzmin Administration Model Matrix

**Feature**: 004-zakey-commerce-backend-admin
Implements FR-100 – FR-109.

Jazzmin themes the **staff admin only**. It is never loaded by, linked from, or allowed to influence the public storefront (FR-100). `jazzmin` precedes `django.contrib.admin` in `INSTALLED_APPS`; nothing else about the storefront changes.

---

## 1. Menu grouping (FR-103)

```
Dashboard
Catalogue   → Products · Variants · Categories · Collections · Brands · Media
Inventory   → Stock · Movements · Reservations · Low stock
Orders      → Orders · Events · Notes
Customers   → Customers · Addresses
Payments    → Payments · Refunds · Methods
Shipping    → Zones · Methods · Rates · Governorates · Areas · Installation
Promotions  → Coupons · Redemptions
Reviews     → Pending · All
Content     → Site settings · Home · Banners · FAQs · Pages · Navigation · Newsletter · Messages
Reports     → Sales · Inventory · Coupons
Settings    → Site settings · Staff · Groups
Audit       → Audit log
```

Menu visibility follows permissions but **never substitutes for them** (FR-111).

---

## 2. Dashboard (FR-101, FR-102)

| Widget | Query | Bound |
|---|---|---|
| Orders today | `count(placed_at__date=today)` | index `(status, -placed_at)` |
| Pending orders | `count(status="pending")` | indexed |
| Awaiting fulfilment | `count(status__in=["confirmed","processing"])` | indexed |
| Paid today | `sum(grand_total)` where paid today | indexed, date-bounded |
| Sales 7 / 30 days | aggregate, date-bounded | indexed |
| Low stock | `available <= threshold`, **limit 10** | indexed |
| Out of stock | `available = 0`, **limit 10** | indexed |
| Pending reviews | `count(status="pending")` | indexed |
| Recent customers | last 5 | indexed |
| Recent payment failures | last 5 | indexed |
| Recent stock movements | last 10 | indexed |

**Rules**: every widget is date-bounded or `LIMIT`-capped; no widget scans a full table; the whole dashboard is capped at a documented query budget asserted by `test_dashboard_query_budget`. No widget shows a metric it cannot compute exactly — misleading figures are worse than absent ones.

---

## 3. Per-model administration

### `ProductAdmin` ★ primary catalogue workflow

- **list_display**: thumbnail, name, category, display price, availability badge, stock, status, updated
- **list_filter**: status, category, collection, brand, availability, `same_day_supported`, `installation_supported`
- **search_fields**: `name`, `slug`, `short_description`, `variants__sku`
- **ordering**: `-updated_at` · **date_hierarchy**: `published_at`
- **prepopulated_fields**: `slug` from `name` · **autocomplete**: category, brand · **filter_horizontal**: collections
- **readonly**: `rating_average`, `review_count`, `created_at`, `updated_at` (system-maintained, FR-094)
- **inlines**: `ProductVariantInline`, `ProductImageInline` (sortable), `ProductFeatureInline`, `SpecificationGroupInline`, `ProductDocumentInline`, `ProductRelationInline` — one screen creates a complete product (FR-108)
- **fieldsets**: Identity · Classification · Content · Service flags · SEO · Publication
- **actions**: publish, unpublish, archive, duplicate, export CSV
- **queryset**: `select_related("category","brand").prefetch_related("images","variants__stock_item")` (FR-106)
- **delete**: blocked when ordered → archive offered (FR-109)

### `ProductVariantAdmin`
list: SKU, product, finish, price, compare-at, stock, default, active · filter: active, default, product status · search: SKU, product name · readonly: created/updated · **price changes write an `AuditLog`** (FR-113)

### `StockItemAdmin`
list: SKU, product, on-hand, reserved, **available (computed)**, threshold, status badge · filter: low-stock, out-of-stock · search: SKU, product · **readonly: `on_hand`, `reserved`** — never free-typed · action: `adjust_stock` (intermediate page requiring delta + reason, FR-021/022) · inline: last 10 movements (read-only)

### `StockMovementAdmin` *(append-only)*
list: created, SKU, delta, reason, before→after, actor, order · filter: reason, date · date_hierarchy: `created_at` · **`has_add/change/delete_permission` all return False** (FR-105)

### `OrderAdmin` ★ primary fulfilment workflow
- **list_display**: number, customer, status badge, payment status, fulfilment status, grand total, placed
- **list_filter**: status, payment status, fulfilment status, shipping method, installation, governorate, placed date
- **search**: number, email, phone, customer name, line SKU · **date_hierarchy**: `placed_at` · **ordering**: `-placed_at`
- **readonly**: **everything financial** — number, subtotal, discount, VAT, shipping total, installation total, grand total, idempotency key, all snapshots (FR-105, INV-003)
- **editable**: internal notes, tracking number, staff-visible fields only
- **inlines**: `OrderLineInline` (**fully read-only**), `OrderEventInline` (read-only), `OrderNoteInline` (add-only)
- **actions**: confirm, mark processing, mark shipped, mark delivered, cancel, record payment, issue refund, export — each validates the transition (`order-state-machine.md`) and reports per-object outcomes (FR-107)
- **queryset**: `select_related("customer","address").prefetch_related("lines","events")`
- **delete**: disabled entirely — orders are cancelled, never deleted

### `PaymentAdmin`
list: order, method, amount, state, reference, captured · filter: state, method, date · readonly: amount, reference, state, `captured_at` · actions: capture, cancel, refund (Finance only) · inline: `PaymentEventInline` read-only

### `RefundAdmin`
list: payment, order, amount, state, actor, created · readonly after creation · **`clean()` rejects amounts exceeding captured minus refunded** (INV-004) with the service enforcing it under a row lock

### `CouponAdmin`
list: code, type, value, used/limit, window, active · filter: type, active, dates · readonly: `times_used` · actions: activate, deactivate, duplicate · inline: redemptions (read-only) · `clean()` validates window and percentage cap

### `ReviewAdmin`
list: product, author, rating, status, verified purchase, created · filter: status, rating, verified, date · actions: approve, reject (both write `AuditLog` and recompute product aggregates) · readonly: `is_verified_purchase`, aggregates

### `CustomerProfileAdmin`
list: name, email, **masked phone**, verified flags, orders count, joined · filter: verified, date joined · search: name, email, phone · readonly: `created_at`, aggregates · inlines: addresses, recent orders (read-only) · **full contact requires `accounts.view_full_contact`** (FR-112) · no password field; reset only by email flow

### `ShippingRateAdmin` / `ShippingMethodAdmin` / `ShippingZoneAdmin`
Standard CRUD, `list_editable` on `price` and `is_active`, `UniqueConstraint(method, zone)` surfaced as a friendly validation error. Rates carry a visible "development placeholder" marker until real values are set (ASM-004).

### `SiteSettingAdmin`
Singleton: add disabled once one exists, delete disabled, changes audited. Grouped fieldsets: Commerce (VAT, threshold, currency), Cart, Inventory, Contact, Announcement, Notices.

### `AuditLogAdmin` *(immutable)*
list: created, actor, action, object, request id · filter: action, content type, date · search: `object_repr`, actor · **all add/change/delete permissions return False**, including for superusers (FR-114)

### Content admins
`HomeSection`, `Banner`, `Partner`, `FAQ`, `StaticPage`, `NavigationItem`: standard CRUD with `position` ordering and `is_active` toggles. `NewsletterSubscription` and `ContactMessage` are view + export + status only; no editing of submitted content.

---

## 4. Cross-cutting rules

| Rule | Applies to |
|---|---|
| Read-only after creation | order lines, all order money, payment events, stock movements, audit log, coupon redemptions |
| `select_related`/`prefetch_related` on every changelist | all (FR-106) |
| Query-count assertion in tests | all changelists (NFR-003) |
| Bulk actions validate per object and report outcomes | all (FR-107) |
| Autocomplete over raw dropdowns for FKs > 20 rows | products, customers, orders, variants |
| `raw_id_fields` for order and payment FKs | movements, refunds, redemptions |
| Delete blocked when order-referenced; archive offered | products, variants, categories, collections |
| Every mutating action writes `AuditLog` | orders, payments, refunds, stock, prices, coupons, permissions |
| CSV export | orders, products, stock, customers, coupons — financial columns gated to Finance |

---

## 5. Import/export

`django-import-export` on Product, ProductVariant, StockItem and Coupon. Imports are **dry-run first with a diff preview**, transactional, validated by the same model rules, and audited. Orders, payments and refunds are **export-only** — importing financial records would bypass every invariant in `inventory-integrity.md`.

---

## 6. Verification

- `tests/admin/test_admin_registration.py` — every model in `data-model.md` is registered exactly once
- `tests/admin/test_admin_readonly.py` — every field marked read-only above rejects modification
- `tests/admin/test_admin_query_budget.py` — each changelist stays under budget
- `tests/admin/test_admin_actions.py` — each action validates, reports per object, and audits
- `tests/admin/test_permissions_matrix.py` — the full role × model × operation grid (`permissions-matrix.md` §5)

# Feature Specification: ZAKEY Commerce Backend and Staff Administration

**Feature Branch**: `004-zakey-commerce-backend-admin`
**Created**: 2026-08-04
**Status**: Draft — planning complete, implementation not started
**Base**: `98237d7`, branched from `003-zakey-frontend-reference-build`
**Input**: Design a production-grade Django e-commerce backend around the completed, approved ZAKEY v2 storefront, plus a professional Jazzmin staff administration console.

---

## Context

Specification 003 delivered a complete, approved, Arabic-first RTL storefront: 13 routes, 18 templates, 16 native JS modules, and a validated demonstration fixture. It has **no database, no authentication, no persistence and no server-side mutation** (`current-state-inventory.md` §1).

This feature adds the commerce backend beneath that storefront and the internal console used to operate it. The storefront's appearance, URLs, Arabic content, RTL behaviour and interactions are a **protected contract** (`frontend-contract.md`, `contracts/frontend-preservation-boundary.md`). The backend is designed around the frontend.

---

## User Scenarios & Testing

### User Story 1 — A customer buys a lock and receives a real order (Priority: P1)

A customer browses the catalogue, opens a product, picks a finish, adds it to the cart, applies a coupon, enters an Egyptian address, chooses shipping and optional installation, selects cash on delivery, and places the order. Stock is reserved, an order number is issued, and the order appears in staff administration and in the customer's account.

**Why this priority**: This is the product. Without it there is no store. Every other story is either an input to it or an operation on its output.

**Independent Test**: With only catalogue, inventory, cart, checkout and orders implemented, a tester can complete a purchase end-to-end against PostgreSQL and see one order, one immutable line snapshot, and one stock movement.

**Acceptance Scenarios**:

1. **Given** a published product with 3 units in stock, **When** the customer orders 2, **Then** an order is created with status `pending`, available stock becomes 1, and one `RESERVE` movement is recorded.
2. **Given** a cart whose product went out of stock after it was added, **When** the customer submits checkout, **Then** no order is created, the cart is preserved, and the customer sees an Arabic message naming the affected line.
3. **Given** a submitted checkout, **When** the customer double-clicks submit or replays the request, **Then** exactly one order exists.
4. **Given** a browser-supplied price of 1 EGP for a 7,490 EGP product, **When** checkout is submitted, **Then** the server ignores it and charges 7,490 EGP.
5. **Given** an order is placed, **When** staff opens it in administration, **Then** the line, address, price, VAT, discount, shipping and installation snapshots match what the customer saw.

---

### User Story 2 — Staff run the store from one console (Priority: P1)

A store manager signs into the Jazzmin console, sees today's orders, pending fulfilment and low stock on the dashboard, opens an order, records a payment, moves it through valid statuses, adds a tracking number, and adjusts inventory with a reason.

**Why this priority**: An order that cannot be operated is not a sale. Fulfilment is co-critical with checkout.

**Independent Test**: Seed orders, sign in as each role, and verify allowed and denied actions server-side.

**Acceptance Scenarios**:

1. **Given** a `pending` order, **When** staff set it to `delivered` directly, **Then** the transition is rejected and the allowed next states are shown.
2. **Given** a Catalogue Manager account, **When** they open Orders, **Then** access is denied by Django permissions, not merely hidden from the menu.
3. **Given** a stock adjustment of −5 with reason `damaged`, **When** it is saved, **Then** a movement row records actor, reason, delta, before and after.
4. **Given** an order line, **When** staff try to edit its price, **Then** the field is read-only.

---

### User Story 3 — Customers own their account and history (Priority: P2)

A customer registers with an Egyptian mobile, verifies by email, signs in, saves addresses, sees order history, and keeps a wishlist across devices. An anonymous cart and wishlist merge into the account on sign-in.

**Why this priority**: Checkout works for guests (the storefront never gates it), so accounts raise retention rather than enabling the sale.

**Independent Test**: Register, add items anonymously, sign in, confirm the merge, and confirm another customer's order returns 404.

**Acceptance Scenarios**:

1. **Given** an anonymous cart with 2 lines and an account cart with 1 different line, **When** the customer signs in, **Then** the cart holds 3 lines with quantities clamped to available stock.
2. **Given** customer A signed in, **When** they request customer B's order URL, **Then** the response is 404 (not 403, which would confirm existence).
3. **Given** `01012345678`, `+201012345678` and `٠١٠١٢٣٤٥٦٧٨`, **When** each is submitted, **Then** all normalise to `01012345678`.

---

### User Story 4 — Staff manage the catalogue and storefront content (Priority: P2)

A catalogue manager creates a product with finishes, images, features, specifications and downloads, assigns categories and collections, publishes it, and edits home-page and FAQ content — all without a developer.

**Why this priority**: Needed for the store to evolve, but the P1 stories can ship against seeded catalogue data.

**Independent Test**: Create and publish a product through the admin only, then confirm it appears in the catalogue with correct filters and detail rendering.

**Acceptance Scenarios**:

1. **Given** a new product, **When** it is saved as `draft`, **Then** it is absent from the storefront and reachable in the admin.
2. **Given** a product with a duplicate slug, **When** it is saved, **Then** validation fails naming the conflict.
3. **Given** a product with reordered images, **When** the detail page renders, **Then** the new first image is the primary.

---

### User Story 5 — Payments and refunds are recorded and reconcilable (Priority: P3)

Finance records a cash-on-delivery collection or a manual transfer against an order, issues a partial refund, and reconciles payment state against order state.

**Why this priority**: Launch payment is cash on delivery and manual methods (the storefront has no provider integration). Gateway integration is a separate, later, credential-gated increment.

**Independent Test**: Record a payment, issue a partial refund, verify refund cannot exceed captured amount and that both are audited.

**Acceptance Scenarios**:

1. **Given** a 5,000 EGP paid order, **When** a 6,000 EGP refund is attempted, **Then** it is rejected.
2. **Given** the same provider callback delivered twice, **When** both are processed, **Then** one payment event exists.

---

### Edge Cases

- Cart holds a product later archived, unpublished, deleted or price-changed.
- Two customers race for the last unit.
- Two customers race for a coupon's final use.
- Coupon expires between cart and submit.
- Cart subtotal crosses the 1,500 EGP free-shipping threshold after a coupon is applied.
- Selected same-day area stops being eligible before submit.
- Installation selected, then the address changes to an ineligible governorate.
- Payment callback arrives for a cancelled order.
- Refund requested for an unpaid order.
- Staff edit an order while a customer cancels it.
- Seed command run twice, or run against a database that already holds real orders.
- Uploaded product image is a decompression bomb, an SVG with script, or mislabelled MIME.
- `localStorage` holds a cart referencing products that no longer exist.

---

## Requirements

### Foundation and configuration

- **FR-001**: Settings MUST split into `base` / `development` / `production` / `test`, with all secrets from environment variables and no hardcoded `SECRET_KEY`.
- **FR-002**: PostgreSQL MUST be the production and test database. SQLite MUST NOT be used to validate transaction, locking or concurrency behaviour.
- **FR-003**: `django.contrib.auth`, `contenttypes`, `sessions`, `messages`, `admin` and `staticfiles` MUST be installed, with `SessionMiddleware`, `AuthenticationMiddleware`, `CsrfViewMiddleware` and `MessageMiddleware` enabled.
- **FR-004**: Production MUST set `DEBUG=False`, `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS=DENY`, and explicit `ALLOWED_HOSTS`.
- **FR-005**: Commerce constants (VAT rate, free-shipping threshold, currency, order-number prefix, cart TTL, reservation TTL) MUST live in one configurable settings/model source, never duplicated in views, templates or JS.
- **FR-006**: A `/healthz` endpoint MUST report database connectivity without leaking configuration.
- **FR-007**: Structured logging MUST be configured with redaction of passwords, tokens, full phone numbers and addresses.

### Catalogue

- **FR-010**: The system MUST model Category (self-nesting), Brand, Collection, Product, ProductVariant, ProductImage, ProductFeature, SpecificationGroup, SpecificationItem, ProductDocument and ProductRelation.
- **FR-011**: Product slug MUST be unique and stable; all 9 existing product slugs, 6 collection slugs and 4 category slugs MUST be preserved exactly (`frontend-contract.md` §2).
- **FR-012**: Variant SKU MUST be unique across the catalogue, enforced by a database constraint.
- **FR-013**: Products MUST have publication state `draft` / `published` / `archived`; only `published` is visible on the storefront.
- **FR-014**: Products MUST NOT be hard-deleted once referenced by an order line; they MUST be archived.
- **FR-015**: Every product MUST have at least one image and at least one variant; the first ordered image is primary and the first variant is default.
- **FR-016**: Image and variant ordering MUST be explicit and staff-controllable.
- **FR-017**: Price MUST be owned by the variant, with the product exposing a derived display price; `compareAtPrice` MUST be optional and, when set, greater than price.
- **FR-018**: Availability MUST be **derived from inventory**, not stored free-hand, and MUST map to the existing `available` / `limited` / `unavailable` values the storefront filters on.
- **FR-019**: Products MUST carry SEO title/description, feature keys used by catalogue facets, `instalmentMessage`, and `sameDaySupported` / `installationSupported` service flags.

### Inventory

- **FR-020**: Stock MUST be tracked per variant as `on_hand` and `reserved`, with `available = on_hand − reserved`.
- **FR-021**: Every stock change MUST write an append-only `StockMovement` row recording delta, reason, actor, before, after, and related order where applicable.
- **FR-022**: Reasons MUST be enumerated: `purchase`, `reserve`, `release`, `fulfill`, `return`, `adjust`, `damaged`, `lost`, `correction`.
- **FR-023**: Checkout MUST reserve stock inside the order-creation transaction using `SELECT … FOR UPDATE` on the stock rows.
- **FR-024**: Reservations MUST expire after a configurable TTL and be released by an idempotent management command.
- **FR-025**: Reservations MUST be released on cancellation, payment failure or expiry, and converted to a deduction on fulfilment.
- **FR-026**: `available` MUST never go negative; overselling MUST be impossible under concurrent checkout.
- **FR-027**: A configurable low-stock threshold MUST drive an admin warning and dashboard list.
- **FR-028**: Returned stock MUST require an explicit staff decision (restock vs. write-off), never automatic.
- **FR-029**: Inventory integrity MUST NOT depend on JavaScript, admin form validation or application-level checks alone.

### Cart and wishlist

- **FR-030**: Cart lines MUST be keyed by `(cart, variant)` consistently for add, update and remove — correcting the prototype defect at `store.js:34,41` (`frontend-contract.md` §3).
- **FR-031**: Anonymous customers MUST get a session-bound cart; authenticated customers a persistent cart.
- **FR-032**: On sign-in, the anonymous cart MUST merge into the account cart, summing quantities and clamping to available stock and the per-line maximum.
- **FR-033**: Quantity MUST be bounded 1–9 server-side, matching the existing UI bound.
- **FR-034**: All money MUST be recomputed server-side on every cart read and mutation. Prices, VAT, discounts, shipping and totals from the browser MUST be ignored entirely.
- **FR-035**: Lines whose variant became unpublished, archived or unavailable MUST be flagged and excluded from totals without silently vanishing.
- **FR-036**: Price changes since a line was added MUST be applied at the current price and surfaced to the customer before submission.
- **FR-037**: Wishlists MUST persist for authenticated customers and merge from session on sign-in; unavailable products may stay saved but cannot be purchased.
- **FR-038**: Carts MUST expire after a configurable TTL and be cleaned by an idempotent command.
- **FR-039**: Every cart and wishlist mutation MUST be POST, CSRF-protected, and authorised against the requesting session or user.

### Pricing, tax and shipping

- **FR-040**: Catalogue prices are **VAT-inclusive**. VAT MUST be computed as an extraction, `gross × 14 ÷ 114`, never as an addition — preserving `cart.js:58` (`frontend-contract.md` §1.1).
- **FR-041**: Shipping cost MUST be added to the order total and rendered as a new row in the existing summary component, because the prototype total omits it and `shippingOptions` carry no price (`frontend-contract.md` §1.2). This is an approved, bounded integration change.
- **FR-042**: All money MUST use `Decimal`; binary floating point MUST NOT be used for any monetary value.
- **FR-043**: Rounding MUST be `ROUND_HALF_UP`, quantized to 2 decimals for storage and 0 decimals for display, with line totals quantized before summing.
- **FR-044**: The 27 Egyptian governorates MUST be modelled with the exact existing keys; service areas MUST carry governorate, label, same-day and installation eligibility.
- **FR-045**: Shipping zones and rates MUST be staff-configurable per governorate/zone, never hardcoded in views or templates.
- **FR-046**: Free shipping MUST apply at a configurable threshold, currently 1,500 EGP, evaluated on the discounted subtotal.
- **FR-047**: Same-day delivery MUST be offered only for the configured eligible areas (8 today) and only where staff have enabled it.
- **FR-048**: Installation MUST be offered only where the governorate is eligible (Cairo, Giza, Alexandria today) **and** every cart line supports installation.
- **FR-049**: Estimated delivery text MUST be configurable per shipping method and zone.

### Customers and authentication

- **FR-050**: Authentication MUST use `django.contrib.auth` with email as the login identifier.
- **FR-051**: Egyptian mobile numbers MUST be validated and normalised exactly as the storefront does: strip separators, `+20`/`20` → `0`, fold Arabic-Indic digits, then match `^01[0125]\d{8}$` (`frontend-contract.md` §4).
- **FR-052**: Email MUST be unique. Phone MUST be unique among verified customers.
- **FR-053**: Registration MUST require email confirmation before the account is fully active; checkout MUST remain available to guests.
- **FR-054**: Password reset MUST use single-use, time-limited, rate-limited tokens.
- **FR-055**: Customers MUST manage multiple addresses with exactly one default, each carrying governorate, area, city, street, building and optional landmark.
- **FR-056**: Every customer-owned object MUST be filtered by owner in the queryset; unauthorised access MUST return 404.
- **FR-057**: Staff administration MUST NOT be reachable through customer account pages, and `is_staff` MUST never be settable from the storefront.
- **FR-058**: Login MUST be rate-limited per IP and per account with progressive lockout.
- **FR-059**: A guest who later registers with the same email MUST be able to have prior guest orders associated by staff, with an audit record.

### Checkout and orders

- **FR-060**: Checkout MUST validate every field server-side, reproducing the existing rules and the exact Arabic messages (`frontend-contract.md` §4).
- **FR-061**: Order creation MUST be a single atomic transaction covering validation, stock reservation, coupon consumption, order write and event write; any failure MUST roll back completely.
- **FR-062**: Installation fee MUST be added to the order total and shown as a row in the existing summary, on the same basis as FR-041.
- **FR-063**: The `acknowledgement` checkbox MUST become a terms-acceptance control, keeping the same control, position and styling, with the label updated and the acceptance recorded on the order.
- **FR-064**: Every checkout submission MUST carry an idempotency key; a replay MUST return the original order rather than creating a second.
- **FR-065**: Order numbers MUST be human-readable, unique under concurrency, and MUST NOT be sequential in a way that leaks volume.
- **FR-066**: Orders MUST store immutable snapshots: line (product name, variant, SKU, unit price, quantity, line total), address, customer contact, VAT, discount, coupon code, shipping method and cost, installation and cost, and grand total.
- **FR-067**: Order history MUST remain accurate after catalogue, price or address records later change.
- **FR-068**: Order status transitions MUST follow the explicit matrix in `order-state-machine.md`; invalid, backward and post-terminal transitions MUST be rejected server-side.
- **FR-069**: Every status change MUST write an `OrderEvent` with actor, from-state, to-state, timestamp and optional note; staff notes and customer-visible notes MUST be distinct.

### Payments and refunds

- **FR-070**: Payment architecture MUST be provider-neutral: `PaymentMethod` (config), `Payment` (attempt), `PaymentEvent` (append-only), `Refund`.
- **FR-071**: Launch payment methods are **cash on delivery and manual/offline methods only**. No provider integration may be claimed; none exists in the repository.
- **FR-072**: The 6 existing payment options MUST render exactly as today, each marked available or coming-soon; disabling one MUST NOT alter the layout.
- **FR-073**: Payments MUST record amount, currency, method, provider reference, and state `pending` / `authorised` / `captured` / `failed` / `cancelled` / `refunded` / `partially_refunded`.
- **FR-074**: Any future webhook MUST verify signature, reject replays by event id, and be idempotent.
- **FR-075**: Refunds MUST NOT exceed captured minus already-refunded, enforced by a database constraint plus a locked service check.
- **FR-076**: Payment and order state MUST be reconcilable by a management command that reports divergence without mutating data.
- **FR-077**: Card numbers, CVV and full PAN MUST NEVER be stored, logged or transmitted to this system.
- **FR-078**: Provider credentials MUST come from environment variables and never appear in code, fixtures, logs or the admin.
- **FR-079**: Real provider integration MUST be a separately identifiable task requiring credentials, official documentation and provider test mode.

### Promotions

- **FR-080**: Coupons MUST support fixed and percentage discounts with a maximum-discount cap for percentages.
- **FR-081**: Coupons MUST support validity window, total usage limit, per-customer limit, minimum basket amount, and product/category restrictions.
- **FR-082**: Coupon eligibility MUST be evaluated server-side at apply time and re-evaluated at order creation.
- **FR-083**: Usage MUST be recorded per order and per customer, incremented inside the order transaction under a row lock.
- **FR-084**: Coupons MUST NOT stack; one coupon per order.
- **FR-085**: Coupon codes MUST be case-insensitive on input, stored uppercase, matching the existing `.toUpperCase()` behaviour at `cart.js:141`.
- **FR-086**: An exhausted or expired coupon MUST fail closed with the existing Arabic rejection message.

### Reviews

- **FR-090**: Reviews MUST carry rating 1–5, title, body, author, product and creation time.
- **FR-091**: Reviews MUST require moderation with state `pending` / `approved` / `rejected`; only approved reviews are public.
- **FR-092**: Reviews MUST be flagged verified-purchase when the author has a delivered order containing the product.
- **FR-093**: One review per customer per product, enforced by a database constraint.
- **FR-094**: Aggregate rating and review count MUST be maintained by the system, never hand-edited.
- **FR-095**: Review submission MUST be rate-limited and escaped on output.

### Content

- **FR-096**: Site settings, announcement bar, hero, home sections, banners, partners, testimonials, FAQs, contact details, social links, static pages and SEO metadata MUST be staff-manageable.
- **FR-097**: Navigation structure MUST be staff-manageable while preserving the existing route contract.
- **FR-098**: Newsletter and contact submissions MUST be stored with timestamp, source and anti-spam protection.
- **FR-099**: Purely presentational labels MUST NOT be made database-driven without a stated business reason; component and layout boundaries stay fixed.

### Administration

- **FR-100**: Jazzmin MUST theme the staff admin only and MUST NOT affect the public storefront in any way.
- **FR-101**: The dashboard MUST show orders today, pending orders, paid orders, orders needing action, sales totals, low stock, out of stock, pending reviews, recent customers, recent payment failures and recent stock movements.
- **FR-102**: Every dashboard widget MUST be bounded — indexed, date-limited and count-capped — with no unbounded table scans.
- **FR-103**: The menu MUST be grouped: Dashboard, Catalogue, Inventory, Orders, Customers, Payments, Shipping, Promotions, Reviews, Content, Reports, Settings, Audit.
- **FR-104**: Every model admin MUST declare list columns, search, filters, ordering, read-only fields, autocomplete/raw-id, fieldsets, inlines and actions per `admin-model-matrix.md`.
- **FR-105**: Order lines, payment events, stock movements and audit records MUST be read-only in the admin; changes happen only through explicit, validated actions.
- **FR-106**: Admin list views MUST use `select_related` / `prefetch_related` and MUST NOT exceed a documented query budget.
- **FR-107**: Bulk actions MUST validate every selected object and report per-object outcomes rather than failing silently.
- **FR-108**: Product creation MUST support variants, images, features, specifications and documents as inlines in one screen.
- **FR-109**: Deleting a model referenced by an order MUST be blocked with a clear message; archiving MUST be offered instead.

### Permissions and audit

- **FR-110**: Nine roles MUST exist as Django groups: Super Administrator, Store Manager, Catalogue Manager, Inventory Manager, Order Fulfilment, Customer Service, Finance, Content Manager, Read-only Auditor.
- **FR-111**: Permissions MUST be enforced server-side in querysets, `has_*_permission` and action handlers — never by hiding menu links alone.
- **FR-112**: Financial fields and full customer contact details MUST be restricted to roles that require them.
- **FR-113**: Every staff mutation of an order, payment, refund, stock level, price, coupon or permission MUST write an audit record with actor, object, action, before, after, timestamp and request id.
- **FR-114**: Audit records MUST be append-only and immutable, including for superusers.
- **FR-115**: Staff login, logout, failed login and permission denial MUST be logged.

### Fixture migration and seed

- **FR-120**: An idempotent `seed_demo` command MUST import the existing fixture into the database preserving every id, slug, image path, Arabic string and price.
- **FR-121**: Rerunning `seed_demo` MUST NOT duplicate records; it MUST report created, updated, skipped and failed counts.
- **FR-122**: `seed_demo` MUST refuse to run when real orders exist unless explicitly forced, and MUST NEVER run automatically in production.
- **FR-123**: Demo content MUST be distinguishable from production content.
- **FR-124**: Fixture-to-model mapping MUST follow `fixture-migration-map.md` exactly.

### Storefront integration

- **FR-130**: Views MUST swap fixture calls for services/QuerySets **behind the same context keys**, so templates change as little as possible.
- **FR-131**: Every existing route, route name and URL MUST continue to resolve identically.
- **FR-132**: `localStorage` cart and wishlist behaviour MUST be replaced through an isolated adapter, keeping `zakey:prototype:v1` handling as a one-time migration path.
- **FR-133**: Business rules MUST be removed from JavaScript once the server owns them; JS keeps presentation and progressive enhancement only.
- **FR-134**: Forms MUST gain `method="post"`, `{% csrf_token %}` and hidden identifiers without visual change.
- **FR-135**: Integration MUST proceed in reversible batches, each independently verifiable and revertible.
- **FR-136**: Server-rendered pages MUST remain useful without JavaScript, preserving the existing no-JS guarantee.

### Non-functional requirements

- **NFR-001**: Catalogue list p95 < 300 ms and product detail p95 < 400 ms at seed scale, excluding network.
- **NFR-002**: Catalogue list MUST issue a bounded, asserted query count with no N+1 across products, images, categories or variants.
- **NFR-003**: Admin changelists MUST stay under a documented query budget, asserted in tests.
- **NFR-004**: Order creation MUST complete within 2 s p95 under 20 concurrent checkouts.
- **NFR-005**: Concurrency-sensitive behaviour MUST be verified on PostgreSQL; SQLite results are not acceptable evidence.
- **NFR-006**: Zero known critical or high vulnerabilities in dependencies at handoff.
- **NFR-007**: No critical or serious axe violation may be introduced.
- **NFR-008**: Visual regression at 1440/1024/768/390 MUST show no unintended drift.
- **NFR-009**: Zero console errors and no horizontal overflow on every route at every viewport.
- **NFR-010**: All customer-facing strings MUST be Arabic and RTL-correct.
- **NFR-011**: Migrations MUST be forward-only, reversible where feasible, and MUST NOT lock large tables unnecessarily.
- **NFR-012**: Structured logs MUST redact personal data; no secret may appear in any log.
- **NFR-013**: Test coverage of services, models and permissions ≥ 85%, with 100% of state-machine transitions exercised.
- **NFR-014**: Every task MUST be independently reviewable, with Kimi as executor and Claude as reviewer.

---

## Key Entities

**Catalogue** — Category, Brand, Collection, Product, ProductVariant, ProductImage, ProductFeature, SpecificationGroup, SpecificationItem, ProductDocument, ProductRelation.
**Inventory** — StockItem, StockMovement, StockReservation.
**Accounts** — User, CustomerProfile, Address.
**Cart** — Cart, CartLine, Wishlist, WishlistItem.
**Geography & shipping** — Governorate, ServiceArea, ShippingZone, ShippingMethod, ShippingRate, InstallationService.
**Orders** — Order, OrderLine, OrderAddress, OrderEvent, OrderNote.
**Payments** — PaymentMethod, Payment, PaymentEvent, Refund.
**Promotions** — Coupon, CouponRedemption.
**Reviews** — Review.
**Content** — SiteSetting, HomeSection, Banner, Partner, Testimonial, FAQ, StaticPage, NavigationItem, NewsletterSubscription, ContactMessage.
**Audit** — AuditLog.

Full field-level definition in `data-model.md`.

---

## Success Criteria

- **SC-001**: A customer completes a purchase end-to-end on PostgreSQL and one order, one immutable line snapshot and one stock movement exist.
- **SC-002**: 20 concurrent checkouts against 1 unit produce exactly 1 order and 19 clean failures, with `available` never negative.
- **SC-003**: Replaying a checkout submission 10 times produces exactly 1 order.
- **SC-004**: 20 concurrent redemptions of a coupon limited to 5 uses produce exactly 5 redemptions.
- **SC-005**: Every invalid order-state transition in the matrix is rejected, with 100% of transitions covered by tests.
- **SC-006**: Each of the 9 roles passes an allow/deny matrix test enforced server-side.
- **SC-007**: A customer requesting another customer's order receives 404 in every case.
- **SC-008**: Visual regression at all 4 viewports shows no unintended drift across all 13 routes.
- **SC-009**: All 13 routes resolve with identical names and URLs after integration.
- **SC-010**: `seed_demo` run twice yields identical row counts and reports zero duplicates.
- **SC-011**: All 9 product slugs, 6 collection slugs and 4 category slugs resolve exactly as before.
- **SC-012**: Catalogue list issues a bounded, asserted query count.
- **SC-013**: A refund exceeding captured amount is rejected at both service and database level.
- **SC-014**: Every FR traces to at least one task and one test in `traceability.md`.
- **SC-015**: Staff complete order → payment → fulfilment without leaving the console.

---

## Out of Scope

Mobile app; SPA rewrite; frontend redesign; second public theme; multi-vendor marketplace; multi-currency; international tax or shipping; AI recommendations; live chat; loyalty points; subscriptions; ERP integration; live payment-provider integration in the initial increment; production deployment; VPS access. Deferred ideas are recorded in `research.md` §10 and MUST NOT expand this scope.

---

## Assumptions

- **ASM-001**: Catalogue prices are VAT-inclusive — **derived from code**, not assumed (`frontend-contract.md` §1.1).
- **ASM-002**: Guest checkout is permitted, because the storefront checkout never gates on authentication.
- **ASM-003**: Launch payment is cash on delivery plus manual methods; the other 5 options render as coming-soon until integrated.
- **ASM-004**: ⚠️ **Shipping rates do not exist anywhere in the repository.** `shippingOptions` carry no price field. Rates are therefore modelled as staff-configurable per zone and seeded with clearly-labelled development placeholders. **Real commercial rates are business input required before launch** — not before implementation.
- **ASM-005**: ⚠️ **The installation fee likewise does not exist in the repository** and is handled identically to ASM-004.
- **ASM-006**: `ZAKEYDEMO` (5%) is demonstration data, not a real commercial offer, and seeds only in development.
- **ASM-007**: Prototype order-history rows are inert display content and MUST NOT be seeded as real orders.
- **ASM-008**: Egyptian Arabic is the only customer-facing language; no i18n framework is added.
- **ASM-009**: Email delivery uses SMTP configured by environment; no transactional-email provider is introduced.
- **ASM-010**: Single warehouse; no multi-location inventory.

---

## Dependencies

- Django 5.2.16 (already pinned), PostgreSQL 16+, Pillow, `django-jazzmin`, `psycopg[binary]`, `django-environ` or equivalent, `pytest` + `pytest-django`, `factory_boy`, `django-import-export` (admin CSV), a rate-limiting library.
- **Deliberately excluded from the initial increment**: Celery, Redis, Django REST Framework, GraphQL, Elasticsearch. Justification and the conditions that would introduce each are in `research.md` §6.
- Existing frontend build (`npm run build`) and QA gates (`npm run qa`) must continue to pass unchanged.

---

## Business Invariants

- **INV-001**: `available = on_hand − reserved` and `available ≥ 0`, always.
- **INV-002**: One confirmed order per idempotency key.
- **INV-003**: Order line snapshots never change after creation.
- **INV-004**: `Σ refunds ≤ Σ captured` per order.
- **INV-005**: Coupon redemptions never exceed the configured limit.
- **INV-006**: Order status only moves along an allowed edge.
- **INV-007**: Order number is globally unique.
- **INV-008**: Variant SKU is globally unique.
- **INV-009**: Product and collection slugs are unique and stable.
- **INV-010**: A customer only ever reads their own orders, addresses, carts and wishlists.
- **INV-011**: VAT is extracted from gross, never added.
- **INV-012**: No monetary value is ever computed in binary floating point.
- **INV-013**: Audit records are append-only.
- **INV-014**: Exactly one default address per customer.

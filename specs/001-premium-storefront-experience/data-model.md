# Data Model: ZAKEY Premium Public Storefront Experience

**Feature**: `001-premium-storefront-experience`
**Date**: 2026-07-31
**Constitution**: v1.1.0

## Reading this document

Entities are grouped by **ownership**, because ownership is what determines lifetime, mutability,
and who may change them. Mixing these up is how a temporary catalogue becomes a shadow production
database.

| Tier | Meaning | Mutable at runtime? | Survives Feature 002? |
| --- | --- | --- | --- |
| **A — Temporary verified catalogue** | Frozen read models loaded from governed JSON at boot | No | Replaced by Tier D |
| **B — Session-owned state** | Per-visitor state in the server-side session | Yes, via services | Shape versioned; carried forward |
| **C — Persistent Feature 001 entities** | The only Django models in this feature | Yes, via forms | Yes |
| **D — Future production entities** | Named here for boundary clarity; **not built in Feature 001** | — | Feature 002 |

### Exact accounting (verified against the headings in this document, 2026-08-01)

| Category | Count | Members |
| --- | --- | --- |
| **Temporary verified-catalogue representations (Tier A)** | **11** | A1 `Product`, A2 `ProductImage`, A3 `Category`, A4 `Collection`, A5 `AccessMethod`, A6 `VerifiedPrice`/`PriceAvailability`, A7 `Provenance`, A8 `SpecValue`, A9 `AssetManifest`, A10 `HomepageRole`, A11 `InformationalContent` |
| **Domain / read-model entities** | **8** | A1, A2, A3, A4, A5, A6, A7, A8 (the product-facing subset of Tier A; A9–A11 are asset/derivation/content records) |
| **Session-owned state objects (Tier B)** | **7** | B1 `Cart`, B2 `CartLine`, B3 `Wishlist`, B4 `CheckoutInformation`, B5 `ResolvedLine`, B6 `Totals`, B7 `OrderReview` — of which B1–B4 are **stored** and B5–B7 are **derived, never stored** |
| **Persistent Feature 001 entities (Tier C)** | **2** | C1 `Enquiry` (the only Django model), C2 `ValidationErrorDetail` (transient) |
| **Validation / error objects** | **1** | C2 `ValidationErrorDetail` |
| **Future Feature 002/003 persistent entities (Tier D — named, NOT built)** | **4** | `CatalogProduct` + taxonomy, `Order`/`OrderLine`/`OrderStatus`, `InventoryBalance`/`InventoryReservation`, `Customer`/`CustomerAddress`/auth |
| **Total distinct planned entities and state objects** | **24** | 11 + 7 + 2 + 4 |

*(The "domain / read-model entities" row is a labelled subset of Tier A, not an addition — it is
listed because the readiness brief asked for that figure separately. The total is 11 + 7 + 2 + 4.)*

### Required-coverage check

| Required by the planning brief | Covered by | Present |
| --- | --- | --- |
| Product read model | A1 | ✅ |
| Product media | A2 | ✅ |
| Category | A3 | ✅ |
| Collection | A4 | ✅ |
| Verified price availability | A6 | ✅ |
| Product-content provenance | A7 (+ A8 per-value page citations) | ✅ |
| Cart | B1 | ✅ |
| Cart line | B2 | ✅ |
| Wishlist | B3 | ✅ |
| Checkout-information state | B4 | ✅ |
| Validated order-review state | B7 | ✅ |
| Validation errors | C2 | ✅ |
| Enquiry-only product behaviour | dedicated section below | ✅ |

**13 of 13 covered. Zero gaps.**

---

## Tier A — Temporary verified catalogue read models

All Tier A types are **frozen dataclasses**. They have no setters, no save method, no manager, and
no relationship to the ORM. They are constructed once at boot by the loader and are thereafter
immutable for the process lifetime.

### A1. `Product` — product read model

Sourced from `curated-launch-catalog.v2.json` (identity, taxonomy, provenance), joined with
`product-media-register.v2.json` (media) and `product-source-register.v1.json` (specification
values).

| Field | Type | Source | Notes |
| --- | --- | --- | --- |
| `launch_id` | `str` | catalog | stable internal key, e.g. `launch-lezn-a06` |
| `slug` | `str` | derived | URL identity, derived deterministically from `public_display_name`; unique; asserted stable at boot |
| `display_name` | `str` | catalog `public_display_name` | e.g. *Lezn A06 Smart Lock* |
| `summary` | `str` | catalog `public_summary` | always the mechanical form *"Lezn {MODEL} smart lock."* |
| `product_type` | `str` | catalog `public_product_type` | constant *Smart Lock* across all 21 |
| `supplier_brand` | `str` | catalog | **non-optional** — *Lezn* on all 21 |
| `supplier_relationship` | `str` | catalog | **non-optional** — `supplier-branded_not-zakey-manufactured` |
| `source_model_code` | `str` | catalog | e.g. `A06` |
| `category` | `Category` | catalog `approved_category` | exactly one, always present |
| `collections` | `tuple[Collection, ...]` | catalog `approved_collections` | **may be empty — 9 of 21 have none** |
| `access_methods` | `tuple[AccessMethod, ...]` | catalog `approved_use_cases` | 3–6 per product |
| `homepage_role` | `str \| None` | catalog `homepage_roles` | exactly one per product; see A10 |
| `media` | `tuple[ProductImage, ...]` | media register join | ordered by `sort_order`; 1–2 per product |
| `specifications` | `Mapping[str, SpecValue]` | source register join | allowlisted fields only; absent when unpopulated |
| `price` | `VerifiedPrice \| None` | catalog | **`None` for all 21 today** |
| `provenance` | `Provenance` | catalog | see A7 |
| `commerce_mode` | `str` | catalog | `quote_only` on all 21 |
| `public_actions` | `frozenset[str]` | catalog | `{request_price, request_quote, contact}` on all 21 |

**Validation at load (fail-closed, application refuses to start):**

1. Schema validation against the governed v2 schema — 40 required keys, `additionalProperties: false`.
2. **Price acceptance discriminates on provenance, not presence.** A price carrying verified
   provenance is **accepted normally and MUST NOT cause a failure**; a price without verified
   provenance is fatal (FC-3). **Today no launch product has any price value at all** — all 21 carry
   `retail_price: null`, `currency: null`, and `source_price_raw/_min/_max/_currency: null`; the only
   non-null price field is the label `source_price_kind: "supplier_reference"`. **The Feature 001
   launch catalogue is therefore enquiry-only, and there are exactly three governed source
   registers.** A verified-price artifact does not exist; it is specified as a controlled future
   extension in `contracts/catalog-provider.md`.
3. `discount`, `stock`, `warranty`, `delivery_time`, `installation_sla`, `compatibility`,
   `market_country`, `tax`, `shipping`, `urgency_claim`, `popularity_claim` MUST be null;
   `certifications` and `payment_methods` MUST be empty. Any value is a fabricated claim (CI-6, CI-7).
4. `supplier_brand` and `supplier_relationship` MUST be non-empty (FR-111).
5. Every `media_assignment.media_asset_id` MUST resolve to an asset whose
   `publication_status == "approved_curated_launch_public"`.
6. Every `source_record_id` MUST resolve in the source register.
7. Slugs MUST be unique across products, categories, and collections.
8. File digests MUST match the recorded SHA-256 for all three registers.

### A2. `ProductImage` — product media read model

Joined from `product-media-register.v2.json`. **The catalogue itself carries no image metadata** —
only pointers — so this join is mandatory.

| Field | Type | Source |
| --- | --- | --- |
| `asset_id` | `str` | register `asset_id`, pattern `media-\d{3}` |
| `roles` | `frozenset[str]` | assignment `roles` ⊆ `{card, detail, homepage_slider}` |
| `sort_order` | `int` | assignment; ≥ 1 |
| `source_sha256` | `str` | register `sha256` — provenance of the original |
| `source_width` / `source_height` | `int` | register `dimensions` |
| `has_alpha` | `bool` | register `alpha.channel_present` |
| `rendition_square_400` / `_800` | `str` | build output path (card) |
| `rendition_detail_800` / `_1600` | `str` | build output path (detail) |
| `alt_text` | `str` | **derived** (R-017) |
| `alt_derivation` | `str` | `generated_from_verified_identity_fields` — records that alt text is derived, not authored |

**Normalisation invariant.** Every rendition is square (1:1), contained on `#EEF0F5`, never cropped,
stretched, or upscaled (CI-11, RF-4). Source ratios span 0.54–1.33, so normalisation is what makes a
consistent card grid possible at all.

### A3. `Category`

`slug`, `name`. Exactly 3: `face-recognition-locks` (7 products), `palm-vein-locks` /
*Palm Vein & Face Locks* (13), `handle-locks` / *Handle & Waterproof Locks* (1).
Relationship: one category → many products; each product → exactly one category.

### A4. `Collection`

`slug`, `name`. Exactly 6: AI Series (1), Aurora Series (3), Knight Series (3), Mirror Series (2),
Touch Screen Series (2), Handle Waterproof Series (1) — **12 of 21 products; 9 have none**.
Relationship: many-to-many, optional. Templates must render the series row only when present
(FR-031, edge case "product with no assigned series").

### A5. `AccessMethod`

`slug`, `name`. Exactly 6: App Control (21), Card & NFC Access (21), Fingerprint Unlock (21),
Face Unlock (20), Video Intercom (20), Palm Vein Unlock (13). Used as the third discovery facet.

**Note for facet UX:** three facets apply to all 21 products, so filtering by them alone never
narrows the set. `FacetCounts` (C-CATALOG) surfaces this honestly rather than implying a filter did
something it did not.

### A6. `VerifiedPrice` and `PriceAvailability`

```
VerifiedPrice { amount_minor: int, currency: str, source_ref: str }
PriceAvailability = VERIFIED_PRICE | PRICE_ON_REQUEST
```

`amount_minor` is an **integer in minor units**. Floats are prohibited — they introduce
representation error into totals. `Product.price is None` ⇒ `PRICE_ON_REQUEST` ⇒ **enquiry-only**,
which is the state of **all 21 products today**. No default, estimate, or zero-fill is permitted
(FR-034, CI-5).

**Enquiry-only consequences, stated once:** an enquiry-only product contributes **no line total**;
its presence in a cart sets `Totals.computable = False`, which suppresses the cart total *and* the
order-review total entirely; a mixed cart shows per-line totals for priced lines only and **no
overall monetary total**. A price is never read from the browser and never stored in the session —
it exists only in the provider and is resolved server-side at render time (FR-098, FR-099, SC-040).

### A7. `Provenance` — product-content provenance

| Field | Source |
| --- | --- |
| `source_record_id` | `lezn.p04.a06.1` |
| `source_document` | `Lezn图册.pdf` |
| `source_document_sha256` | 64-hex digest |
| `source_page_pdf` | integer page number |
| `identity_grounding` | `catalogue_page_and_high_confidence_media_match` |
| `media_rights_status` | `human_authorized_selected_launch_use` |
| `launch_publication_status` | `human_approved_quote_only_launch` |

Carried on every product so any displayed fact can be traced to a page of a checksummed supplier
document. Not all of it is rendered; all of it is retained (CI-13).

### A8. `SpecValue` — specification value with page citation

```
SpecValue { raw_value: str, source_page_pdf: int, normalized_value: str | None }
```

Only the five allowlisted fields may be published: `source_product_family`, `material`,
`finishes_colours`, `power_supply`, `unlock_methods`. Values come from the source register, e.g.
material *"Aviation aluminum"*, power supply *"4200mAh lithium battery"*, unlock methods *Face, Tuya
App, NFC, Fingerprint, Card, Password, Key*.

**The source register carries many more fields** — dimensions, weight, battery, mortise, operating
temperature, printed certifications, supplier name, and `source_price_*` values. **None of these is
on the allowlist and none may be published** (FR-035). The loader reads only allowlisted keys, so
an unlisted field cannot reach a template even by accident.

### A9. `AssetManifest`

Records, per rendition: source asset id, source SHA-256, output path, output bytes, dimensions,
encoder settings, derived alt text and its derivation marker, and rights status. Satisfies CI-13 and
feeds the PB-1/PB-3 page-weight checks.

### A10. `HomepageRole`

Verified values, each product carrying exactly one: `featured_products_slider` (6),
`highlighted_products` (8), `product_discovery_cards` (7).

Feature 001 renders the single featured rail required by FR-011 from `featured_products_slider`.
The other two roles are loaded and available but drive no additional rail, because FR-011 ratifies
exactly one. Recorded here so Feature 002 need not re-derive them.

### A11. `InformationalContent`

Verified Tier-G copy for About, FAQ, and the value band (R-018), stored as structured content in one
place, not inline in templates (FR-071, FR-072). Fields: `key`, `title`, `body_blocks`,
`source_note` (records Tier-G provenance).

---

## Tier B — Session-owned state

Server-side only. The client holds an opaque cookie. See `contracts/session-state.md`.

### B1. `Cart`

```
{"v": 1, "lines": [CartLine, ...]}
```
Max 50 distinct lines. Versioned; a `v` mismatch discards rather than migrates.

### B2. `CartLine`

```
{"sku": <product slug>, "qty": <int 1..99>}
```
**Two fields only.** No price, no name, no image, no total — storing any of those would create a
second source of truth for money (FR-099, R-012).

### B3. `Wishlist`

```
{"v": 1, "skus": [<product slug>, ...]}
```
Max 100 entries, order preserved, duplicates collapsed.

### B4. `CheckoutInformation`

```
{"v": 1, "fields": {...}, "validated": bool}
```
Contact and delivery fields only (`contracts/checkout-and-enquiry.md`). **No payment field exists in
this structure or anywhere else in the system.** `validated` gates access to the review state.

### B5. `ResolvedLine` (derived, never stored)

`{product: Product, qty: int, line_total: Money | None}` — produced by
`CatalogProvider.resolve_lines()` at render time. `line_total` is `None` when the product is
price-on-request.

### B6. `Totals` (derived, never stored)

`{computable: bool, subtotal: Money | None, unpriced_count: int, currency: str | None}`.
`computable` is `False` if **any** line lacks a verified price; `subtotal` is then `None` and no
figure may be rendered (FR-098, SC-040). Since all 21 products are price-on-request today,
`computable` is `False` for every non-empty cart at launch — the price-on-request path is the live
path, and the priced path is implemented and tested against fixtures.

### B7. `OrderReview` (derived, never stored)

`{lines, totals, information, computable, disclosure_key, actions, cart_digest}`.

`actions` is exactly `[EDIT_CART, EDIT_INFORMATION, SEND_ENQUIRY]`. There is no order-placing
member. `cart_digest` detects mid-checkout cart changes (FR-110). **This is the terminal state of
Feature 001** — it produces no record and mutates nothing.

---

## Tier C — Persistent Feature 001 entities

The **only** Django models in this feature.

### C1. `Enquiry`

| Field | Type | Notes |
| --- | --- | --- |
| `reference` | `UUID` | internal identifier. **Never labelled or presented as an order number** (FR-109) |
| `full_name`, `email`, `phone` | char | validated server-side |
| `address_*`, `city`, `region`, `postal_code`, `country` | char | optional except where the form requires |
| `message` | text | ≤ 2000 |
| `source` | choice | `PRODUCT \| CART \| REVIEW \| CONTACT` |
| `lines_snapshot` | JSON | `[{sku, qty, display_name, supplier_brand}]` at submission time |
| `created_at` | datetime | |

`lines_snapshot` records **identity, not money** — no price or total is stored, because none is
verified. Success is shown only after this row commits (FR-052, R-016).

### C2. `ValidationErrorDetail` (transient, not persisted)

`{field, code, message_key, params}` — modelled explicitly because FR-056/FR-057 require
field-level messages programmatically associated with their fields, a form-level summary, and focus
movement to the first invalid field. `message_key` is an i18n key, never a rendered string (FR-078).

---

## Tier D — Future production entities (named, NOT built)

Declared solely to make the Feature 001 / 002 boundary explicit. **No model, migration, admin, or
table for any of these exists in Feature 001.**

| Entity | Owner | Why deferred |
| --- | --- | --- |
| `CatalogProduct` + taxonomy tables | Feature 002 | Replaces Tier A via `DatabaseCatalogProvider` |
| `Order`, `OrderLine`, `OrderStatus` | Feature 002 | Feature 001 stops at review and creates no order (FR-109) |
| `InventoryBalance`, `InventoryReservation` | Feature 002 | No stock fact is verified |
| `Customer`, `CustomerAddress`, auth | Feature 003 | No accounts or authentication in Feature 001 |

**Deferred values, explicitly.** Retail price, currency, discount, stock, warranty, delivery time,
installation SLA, certifications, compatibility, market country, tax, and shipping are `null` or
empty in the governed dataset on all 21 products. They are **not modelled, not defaulted, and not
displayed** in Feature 001. Each becomes available only when a verified value is supplied.

---

## Enquiry-only product behaviour

Because every product is `PRICE_ON_REQUEST` today, this is the live behaviour, not an edge case:

| Surface | Behaviour |
| --- | --- |
| Product card | Price-on-request statement; no figure |
| Product detail | Price-on-request statement, *Request price* action, *Add to cart* action |
| Cart line | Product and quantity; no line total |
| Cart summary | No monetary total; price-on-request statement; enquiry offered (FR-098) |
| Checkout review | No total; the same statement; enquiry is the only submitting action |
| Enquiry | Carries product identity and quantity; no monetary commitment |

When Feature 002 supplies verified prices, `computable` flips to `True` and the already-implemented
priced path activates with no template change.

---

## State transitions

**Cart line:** `absent → present(qty)` via `add`; `present(qty) → present(qty')` via `update`
(1–99); `present → absent` via `remove` or silent stale-drop. Invalid quantity leaves state
unchanged and returns a field error — it never silently removes a line.

**Checkout:** `empty-cart → (blocked)`; `cart populated → information` ; `information →
validated=True → review`; `review → enquiry submitted → confirmation`. Review is unreachable unless
`validated is True` **and** the cart is non-empty **and** `cart_digest` matches. Session expiry
returns the visitor to a valid state and creates no partial artifact.

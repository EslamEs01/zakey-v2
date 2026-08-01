# Reference-Fidelity Matrix — Specification 002

**Feature**: `002-egypt-premium-storefront`
**Constitution**: v2.0.1 — Principles I, XIII.8, XIX
**Reference**: `https://remote-fried-86528699.figma.site/`, inspected 2026-08-01 in a real browser
**Evidence**: `reference-screenshots/` (35 verified captures) + `visual-reference-inventory.md`

## Legend

| Grounding class | Meaning |
| --- | --- |
| **DIRECT** | The exact corresponding reference page/state was inspected at the listed widths. Fidelity is reproduction. |
| **ADAPTATION** | No direct reference equivalent exists at that width or at all. Composition is derived from *named* inspected components. **Not a reproduction claim.** |

A page is never marked DIRECT for a width whose evidence was not captured (Constitution XIX.9).

---

## 1. Pages

### 1.1 Home

| Field | Value |
| --- | --- |
| Reference state | Landing page, full scroll |
| Evidence | `home-1440.png`, `home-1024.png`, `home-768.png`, `home-390.png` |
| Viewport coverage | **1440 ✅ · 1024 ✅ · 768 ✅ · 390 ✅** |
| Grounding | **DIRECT** at all four widths |
| Preserved | 14-band order and background rhythm (`#FFFFFF` ↔ `#F8F9FB` with two full-bleed `#0D1B3D` bands); hero 792px navy; container 1344/928/fluid; grid 4/4/2/1 for products, 4/4/2/2 for categories, 3/3/2/1 for propositions; h1 72→60→48px, h2 36px constant; category imagery 4:5, product imagery 1:1; restrained shadows |
| Egyptian / RTL adaptation | Full RTL mirroring; Cairo typography; `ج.م` pricing; Arabic headline and section titles; announcement bar carries the 1,500 EGP threshold and no invented discount code |
| Justified deviations | D-01, D-02, D-03, D-04, D-08, D-11, D-12, D-14 |
| Requirement IDs | FR-001–FR-015, FR-016–FR-032, FR-097–FR-102, FR-119–FR-132 |
| Acceptance method | Screenshot comparison against `home-<width>.png` at all four widths; band-order assertion; overflow assertion; token audit |

### 1.2 Shop / catalog

| Field | Value |
| --- | --- |
| Reference state | "All Products" |
| Evidence | `shop-1440.png`, `shop-1024.png` (via header "Shop") and `catalog-via-view-{1440,1024,768,390}.png` (via a product "View" control). DOM `h1` = "All Products" at all four widths; the 1440/1024 pairs are byte-identical, proving both routes reach the same page |
| Viewport coverage | **1440 ✅ · 1024 ✅ · 768 ✅ · 390 ✅** |
| Grounding | **DIRECT** at all four widths |
| Measured | docH 2574 / 2942 / 3360 / 6004; **horizontal overflow present at 390** (RD-05) |
| Preserved | Sidebar + results split; filter groups (category with counts, price range, rating); "Clear All Filters"; result count; sort control; card grid 3→2→1; pagination `1 2 3 … 8` |
| Egyptian / RTL adaptation | Sidebar mirrors to the inline-start side; approved category vocabulary only; price filter renders only when a verified price exists (FR-037); Arabic filter and sort labels |
| Justified deviations | D-01, D-04, D-05, D-07 (**overflow at 390 corrected**), D-12, D-13 |
| Requirement IDs | FR-033–FR-048, FR-049–FR-056 |
| Acceptance method | Comparison against `shop-{1440,1024}.png` and `catalog-via-view-{768,390}.png`; zero-overflow assertion at all four widths (the reference's own 390 overflow must not be reproduced) |

### 1.3 Product details

| Field | Value |
| --- | --- |
| Reference state | **None — does not exist.** Activating any product "View" control routes to the catalog (identical docH 2574 @1440 and identical control set incl. "Clear All Filters") |
| Evidence | `catalog-via-view-{1440,1024,768,390}.png` — evidence **of the absence**: DOM `h1` = "All Products" at every width, and byte-identical to `shop-*.png` at 1440/1024 |
| Viewport coverage | n/a |
| Grounding | **ADAPTATION** at all widths |
| Adaptation basis | Composed from inspected components: the catalog product card (imagery ratio 1:1, badge, category label, name, price block), the catalog two-region split (sidebar + content) reused as gallery + information, the contact page's form anatomy for the enquiry form, and the shared shell |
| Preserved | Container widths, grid gaps, type scale, token palette, card price-block anatomy, 1:1 product imagery |
| Egyptian / RTL adaptation | Gallery on the inline-start side; `ج.م` price block; quote-only variant replaces cart actions (BR-010); approved specification fields only |
| Justified deviations | D-01, D-02, D-04, D-05, D-08, D-11, D-12 |
| Requirement IDs | FR-057–FR-070, FR-049–FR-056 |
| Acceptance method | Component-level comparison against the card and form evidence; full state matrix (§10 of `spec.md`); overflow assertion |

### 1.4 Cart

| Field | Value |
| --- | --- |
| Reference state | Cart route — **empty state only** |
| Evidence | `cart-1440/1024/768/390.png`; `cart-filled-*.png` prove no populated state exists |
| Viewport coverage | Empty state **1440 ✅ · 1024 ✅ · 768 ✅ · 390 ✅**; populated state ❌ everywhere |
| Grounding | **DIRECT** for the empty state · **ADAPTATION** for the populated state |
| Adaptation basis | Line-item rows composed from the catalog card's image/name/price anatomy; totals panel composed from the checkout summary pattern; shared shell and footer |
| Preserved | Empty-state composition (heading, supporting line, primary action), container widths, footer 5-column/48px |
| Egyptian / RTL adaptation | `ج.م` totals; VAT 14% line; free-shipping progress toward 1,500 EGP; Arabic quantity and removal controls |
| Justified deviations | D-01, D-03, D-04, D-05, D-12 |
| Requirement IDs | FR-071–FR-080, BR-003–BR-008 |
| Acceptance method | Empty state compared against `cart-<width>.png`; populated state verified against BR-008 identity and §10 state matrix |

### 1.5 Checkout

| Field | Value |
| --- | --- |
| Reference state | **None — no checkout journey exists** |
| Evidence | Absence established while probing from cart (no checkout control present) |
| Grounding | **ADAPTATION** at all widths |
| Adaptation basis | Form anatomy from the inspected contact form (label/field/select/textarea rhythm, two-column field pairing at ≥1024, single column below); summary panel from the cart totals composition; shared shell |
| Preserved | Field rhythm and grouping, container widths, button anatomy, token palette |
| Egyptian / RTL adaptation | All 27 governorates; Egyptian mobile validation; detailed address + landmark; configuration-driven same-day delivery and installation; honest payment-method states; `ج.م` summary |
| Justified deviations | D-01, D-03, D-04, D-05, D-15 |
| Requirement IDs | FR-081–FR-096, BR-005–BR-016 |
| Acceptance method | Journey test cart → checkout → review → confirmation with total-identity assertion; duplicate-submit assertion; unavailable-integration assertion |

### 1.6 My Account

| Field | Value |
| --- | --- |
| Reference state | Account route — signed-in stub with **fabricated** identity and order history; **no login/registration** |
| Evidence | `account-1440.png`, `account-1024.png`, `account-768.png` |
| Viewport coverage | **1440 ✅ · 1024 ✅ · 768 ✅ · 390 ❌** |
| Grounding | **DIRECT** for the account-shell structure · **ADAPTATION** for authentication surfaces and for 390 |
| Adaptation basis | Sign-in/registration forms composed from the inspected contact form anatomy; 390 layout derived from the verified home 390 stacking behaviour |
| Preserved | Side-navigation + panel split, section grouping, container widths |
| Egyptian / RTL adaptation | Side navigation mirrors to the inline-start side; Arabic labels and errors |
| **Content rejected** | "John Smith", "john@example.com", "Premium Member", and all four fabricated orders (RD-11) — replaced by real identity and an honest empty order history |
| Justified deviations | D-01, D-04, D-05, D-11 |
| Requirement IDs | FR-103–FR-107 |
| Acceptance method | Structure compared against `account-<width>.png`; empty-history assertion; return-to-destination journey test |

### 1.7 About

| Field | Value |
| --- | --- |
| Reference state | About route |
| Evidence | `about-1440.png`, `about-1024.png` |
| Viewport coverage | **1440 ✅ · 1024 ✅ · 768 ❌ · 390 ❌** |
| Grounding | **DIRECT** at 1440/1024 · **ADAPTATION** at 768/390 |
| Adaptation basis | Home's verified 768/390 stacking of multi-column bands |
| Preserved | Eyebrow + two-line heading composition, band rhythm, 4-column supporting grid, container widths |
| **Content rejected** | "Since 2018", "500K+ Homes Protected", "47 Countries Served", "28 Industry Awards", "4.9★" (RD-10) |
| Justified deviations | D-01, D-02, D-11 |
| Requirement IDs | FR-108 |
| Acceptance method | Comparison at 1440/1024; **capture required at 768/390 before implementation**; content-provenance audit |

### 1.8 Contact

| Field | Value |
| --- | --- |
| Reference state | Contact route |
| Evidence | `contact-1440.png`, `contact-1024.png` |
| Viewport coverage | **1440 ✅ · 1024 ✅ · 768 ❌ · 390 ❌** |
| Grounding | **DIRECT** at 1440/1024 · **ADAPTATION** at 768/390 |
| Adaptation basis | Home's verified 768/390 stacking |
| Preserved | Three info cards (3-column, 32px gap), two-column form pairing (582px region, 20px gap), FAQ block, container widths |
| Egyptian / RTL adaptation | Hotline `19919` and New Cairo replace the US phone and Singapore address (D-15); Arabic field labels; Egyptian phone validation |
| **Content rejected** | "+1 (800) 929-5390", "12 Innovation Drive, Singapore 138668", "Response within 2 hours", the FAQ's 30-day returns / 50+ cities / 5-year warranty claims, and "Start Live Chat" (RD-12, RD-16) |
| Justified deviations | D-01, D-04, D-05, D-09, D-15 |
| Requirement IDs | FR-109, FR-110, FR-115 |
| Acceptance method | Comparison at 1440/1024; **capture required at 768/390**; every visible control exercised |

### 1.9 Search results · Wishlist · 404 · 5xx

| Field | Value |
| --- | --- |
| Reference state | Search: inline expanding bar (`search-*.png`). Wishlist: **inert control** (`wishlist-*.png`). 404/5xx: none |
| Grounding | Search trigger **DIRECT**; results page, wishlist page and error pages **ADAPTATION** |
| Adaptation basis | Results page reuses the catalog results region; wishlist reuses the catalog grid plus the cart empty-state composition; error pages reuse the cart empty-state composition |
| Justified deviations | D-09 (inert wishlist corrected to a working destination or hidden) |
| Requirement IDs | FR-006, FR-007, FR-045, FR-080, FR-139 |

---

## 2. Shared components

| Component | Reference evidence | Viewports | Grounding | Preserved | Adaptation / deviation | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- |
| C-01 Announcement bar | `home-*` all widths | 1440·1024·768·390 | DIRECT | 40px height; 60px wrap at 390; full-bleed | Content replaced (D-03); dismissible | FR-001 |
| C-02 Header shell | `home-*` all widths | all | DIRECT | 73px, sticky, `#FFFFFF`, above content | RTL mirroring (D-01) | FR-002 |
| C-03 Logo | `home-*` | all | DIRECT | Lockup position and scale | Verified ZAKEY asset replaces reference mark | FR-003 |
| C-04 Primary navigation | `home-1440/1024` | 1440·1024 | DIRECT | Inline order and spacing | Real URLs (D-10); Arabic labels | FR-004, FR-015 |
| C-05 Products dropdown | `products-menu-1440/1024` | 1440·1024 | DIRECT | 4 entries, 190×40 | Approved categories only (D-13); keyboard operable | FR-004 |
| C-06 Mobile nav panel | `menu-open-1024/768/390` | 1024·768·390 | DIRECT (structure) | Trigger position, collapse threshold ≤1024 | **Focus trap added** (D-06) | FR-005, FR-124 |
| C-07 Search | `search-*` | all | DIRECT | Inline expansion, +62px | Accessible name and label added (D-04, D-05) | FR-006, FR-122, FR-125 |
| C-08 Wishlist control | `wishlist-*` | 1440·1024·768 | DIRECT (defect) | Icon slot position | **Made functional or hidden** (D-09) | FR-007 |
| C-09 Cart control + count | `home-*`, `cart-*` | all | DIRECT | Icon slot, count affordance | Count only when non-zero; accessible name | FR-008, FR-077 |
| C-10 Account control | `account-*` | 1440·1024·768 | DIRECT | Icon slot | Guest/authenticated routing | FR-009 |
| C-11 Skip link | none | — | ADAPTATION | — | Added for accessibility | FR-010 |
| C-12 Product card | `shop-1440/1024`, `home-*` | 1440·1024 (+home at all) | DIRECT | 1:1 imagery, badge, category label, name, price block, action | Quote-only variant (D-12); missing-image state (D-08) | FR-049–FR-056 |
| C-13 Price block | `shop-1440/1024` | 1440·1024 | DIRECT | was/now composition | `ج.م` (D-03); renders only when verified | FR-050, FR-051, BR-001 |
| C-14 Availability badge | `shop-*` | 1440·1024 | DIRECT | Badge position | Only when verified (BR-012) | FR-053 |
| C-15 Button | `home-*`, `shop-*` | all | DIRECT | Sizes (111×40, 219×58, 156×58, 66×36), weight | Visible focus state added (D-04) | FR-121 |
| C-16 Form field | `contact-1440/1024` | 1440·1024 | DIRECT | Field rhythm, 2-column pairing | Labels + linked errors added (D-05) | FR-125, FR-126 |
| C-17 Governorate selector | none | — | ADAPTATION | Select anatomy from the contact Subject select | All 27 governorates | FR-083 |
| C-18 Quantity control | none | — | ADAPTATION | Button + field anatomy from inspected controls | Min/max, server validation | FR-073 |
| C-19 Filter group | `shop-1440/1024` | 1440·1024 | DIRECT | Group headings, radios with counts, range slider | Approved facets only; labels added | FR-034–FR-037 |
| C-20 Filter drawer | 390 "Filters" trigger observed | 390 | ADAPTATION | Trigger placement | Focus-trapped drawer added (D-06) | FR-046 |
| C-21 Sort control | `shop-1440/1024` | 1440·1024 | DIRECT | Select placement | Accessible label added | FR-040 |
| C-22 Pagination | `shop-1440/1024` | 1440·1024 | DIRECT | `1 2 3 … 8` pattern | Current page non-interactive; focus moves to results | FR-047 |
| C-23 Result count | `shop-1440/1024` | 1440·1024 | DIRECT | "8 products" placement | Truthful count (FR-038) | FR-038 |
| C-24 Empty state | `cart-*` | all | DIRECT | Heading + line + action | Reused for catalog/search/wishlist/orders | FR-044, FR-045, FR-075 |
| C-25 Error state | none | — | ADAPTATION | Empty-state composition | Recoverable, claims no success | FR-137–FR-139 |
| C-26 Live region | none | — | ADAPTATION | — | Added for accessibility | FR-127 |
| C-27 Dialog / drawer | `menu-open-*` | 1024·768·390 | DIRECT (structure) | Panel behaviour | Dialog semantics + focus trap added (D-06) | FR-124 |
| C-28 Gallery | none | — | ADAPTATION | Product imagery ratio 1:1 from card evidence | Keyboard-operable selection | FR-057 |
| C-29 Accordion / tabs | `contact-*` FAQ | 1440·1024 | DIRECT | Grouped-detail composition | Keyboard operable; verified content only | FR-063, FR-068 |
| C-30 Newsletter form | `home-*` | all | DIRECT | Field 317×50 + button 119×50 | Label added (D-05) | FR-014 |
| C-31 Footer | `home-*`, `cart-*` | all | DIRECT | 5 columns, 48px gap; legal row | Unverified destinations removed (D-09, RD-17) | FR-012, FR-013 |
| C-32 Breadcrumb | none | — | ADAPTATION | — | Added for orientation | FR-015 |

---

## 3. Coverage summary

| Page | 1440 | 1024 | 768 | 390 | Class |
| --- | --- | --- | --- | --- | --- |
| Home | ✅ | ✅ | ✅ | ✅ | DIRECT |
| Shop / catalog | ✅ | ✅ | ✅ | ✅ | DIRECT |
| Product details | — | — | — | — | ADAPTATION (absent from reference) |
| Cart (empty) | ✅ | ✅ | ✅ | ✅ | DIRECT |
| Cart (populated) | — | — | — | — | ADAPTATION (absent) |
| Checkout | — | — | — | — | ADAPTATION (absent) |
| My Account | ✅ | ✅ | ✅ | ⬜ | DIRECT / ADAPTATION |
| About | ✅ | ✅ | ⬜ | ⬜ | DIRECT / ADAPTATION |
| Contact | ✅ | ✅ | ⬜ | ⬜ | DIRECT / ADAPTATION |
| Shared shell | ✅ | ✅ | ✅ | ✅ | DIRECT |

✅ = evidence captured · ⬜ = **gap declared** (RP-07); capture required before implementing that
page · — = no reference equivalent exists.

**Zero pages are marked DIRECT for a width without its own evidence.**

---

## 4. Reference-defect corrections carried into requirements

| Defect | Correction | Requirement |
| --- | --- | --- |
| RD-01 LTR/English document | `lang="ar"`, `dir="rtl"` | FR-097 |
| RD-02 No accessible names on icon controls | Arabic accessible names on all controls | FR-122 |
| RD-03 Unlabelled inputs | Programmatic labels + linked errors | FR-125, FR-126 |
| RD-04 Mobile menu without focus trap | Focus-trapped, Escape-dismissible, focus returned | FR-124 |
| RD-05 Horizontal overflow at 390 (catalog) | Zero unintended overflow at all four widths | FR-048, SC-003 |
| RD-06 Broken images | Verified media register + missing-image state | FR-055 |
| RD-07 Stock photography reused | Verified ZAKEY product media only | FR-055, §11 |
| RD-08 Inert wishlist | Functional destination or hidden | FR-007 |
| RD-09 No URLs | Real, shareable, deep-linkable URLs | FR-015, FR-041 |
| RD-10 Fabricated statistics | Data-driven or omitted | FR-018, FR-108, FR-111 |
| RD-11 Fabricated account identity/orders | Real identity; honest empty history | FR-106 |
| RD-12 US/Singapore contact data, USD | Hotline `19919`, New Cairo, `ج.م` | FR-099, FR-109 |
| RD-13 Invented discount and threshold | 1,500 EGP threshold; no invented code | BR-006, FR-111 |
| RD-14 Invented category counts/vocabulary | Approved categories; computed counts | FR-019, FR-020, FR-034 |
| RD-15 Fabricated ZAKEY-branded product names | Verified `public_display_name`; no manufacture implied | FR-059 |
| RD-16 "Start Live Chat" with no capability | Excluded from scope | §22 |
| RD-17 Dead footer destinations | Omitted entirely | FR-013 |

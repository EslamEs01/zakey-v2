# Content and Asset Provenance Register — Specification 002

**Feature**: `002-egypt-premium-storefront`
**Created**: 2026-08-01
**Constitution**: ZAKEY v2 Premium Egyptian Storefront Constitution v2.0.1
**Governs**: Principle V (Content and Asset Integrity), Principle XX.9–XX.10, Principle XXI

This register is the authoritative record of what ZAKEY v2 may and may not present as production
fact. Every production asset and material business claim MUST appear here with a verification
status (Constitution V.2). Anything not listed as **VERIFIED** MUST NOT render in production
(Constitution V.4).

## 1. Sources inspected

| Source | Access | Date | Result |
| --- | --- | --- | --- |
| `/media/mekky/work/backend/zakey.v1` (legacy) | Read-only Git + filesystem inspection. No file created, modified, moved, or deleted. No migration, cache, or dependency operation performed. | 2026-08-01 | HEAD `5fdd81d`, working tree clean before and after |
| `https://remote-fried-86528699.figma.site/` | Real browser (Chromium 148), 4 viewports | 2026-08-01 | HTTP 200. See `visual-reference-inventory.md` |

**Legacy read-only proof**: only `git log`, `grep`, `ls`, `find`, and `JSON.parse` reads were
issued against the legacy path. The legacy repository remains on branch
`015-admin-dashboard-operations` with a clean working tree.

## 2. VERIFIED — approved for production use

### 2.1 Brand assets

| Asset | Legacy source path | Type | Proposed ZAKEY v2 use | Eligibility |
| --- | --- | --- | --- | --- |
| ZAKEY logo (navy) | `static/brand/blue-logo.png` | PNG | Header logo on light surfaces | Production |
| ZAKEY logo (white) | `static/brand/white-logo.png` | PNG | Footer / navy-surface logo | Production |
| ZAKEY logo (navy, icons set) | `static/icons/zakey-logo-blue.png` | PNG | Alternate/compact lockup | Production |
| ZAKEY logo (white, icons set) | `static/icons/zakey-logo-white.png` | PNG | Alternate/compact lockup | Production |
| Favicon | `static/brand/favicon.svg` | SVG | Browser favicon | Production |
| Apple touch icon | `static/brand/apple-touch-icon.png` | PNG | iOS home-screen icon | Production |
| ZAKEY logo master | `reference-imports/spec-012/白底图/ZAKEY LOGO2.png` | PNG | Source master for regeneration | Production (source) |
| ZAKEY logo (white, vector) | `reference-imports/spec-012/ZAKEY LOGO WHITE.pdf` | PDF | Source master for regeneration | Production (source) |

### 2.2 Product media

| Fact | Value |
| --- | --- |
| Register | `specs/012-smart-storefront-commerce/data/product-media-register.v2.json` |
| Registered assets | **49** (`assets[]`), each with `sha256`, byte size, format, and pixel dimensions |
| Source container | `reference-imports/spec-012/白底图` (white-background product photography) |
| Files present on disk | 50 files in that directory |
| Evidence class | `supplied_product_media_candidate` |
| Example | `media-001` → `1.png`, PNG, 508,039 bytes, 1280px wide, sha256 `f183ef72…a757161` |
| Assignment model | Products reference media by `media_asset_id` with `roles` (`card`, `detail`, `homepage_slider`) and `sort_order` |

**Production rule**: product imagery MUST be sourced from this register by `media_asset_id`.
Aspect ratio and quality MUST be preserved (Constitution V.7). A product whose required media
role is unassigned MUST render the missing-image state (FR-062), never a substitute product's
photo.

### 2.3 Curated product catalogue

| Fact | Value |
| --- | --- |
| Dataset | `specs/012-smart-storefront-commerce/data/curated-launch-catalog.v2.json` |
| Class | `curated_launch_catalogue` |
| Generated | 2026-07-21 |
| Human decision | `eslam-2026-07-21-public-completeness-v1` |
| Approved products | **21** |
| Supplier brand | `Lezn` |
| Supplier relationship | `supplier-branded_not-zakey-manufactured` |
| Identity grounding | `catalogue_page_and_high_confidence_media_match` |
| Traceability per product | `source_document` + `source_document_sha256` + `source_page_pdf` + `source_model_code` |

**Approved categories** (exhaustive, from `approved_category.slug`):

| Category slug | Name | Approved products |
| --- | --- | --- |
| `palm-vein-locks` | Palm Vein Locks | 13 |
| `face-recognition-locks` | Face Recognition Locks | 7 |
| `handle-locks` | Handle Locks | 1 |

**Approved product names** (`public_display_name`, first 20 of 21): Lezn A06, Lezn R02, Lezn MR6,
Lezn W08, Lezn R01, Lezn R03, Lezn M17, Lezn M20, Lezn M30, Lezn Tuya-02, Lezn K11, Lezn M15,
Lezn M15 max, Lezn M18 max, Lezn MR8, Lezn R05, Lezn R06, Lezn R09, Lezn R15, Lezn W06 — each
suffixed "Smart Lock".

**Approved use-case facets** (verified filter vocabulary): `face-unlock`, `fingerprint-unlock`,
`app-control`, `card-and-nfc`, `video-intercom`.

**Approved collections**: e.g. `ai-series`; plus `collection_keys: ["launch-catalogue"]`.

**Approved specification fields only**: `source_product_family`, `material`, `finishes_colours`,
`power_supply`, `unlock_methods`. **No other specification field may be displayed** (FR-058).

**Facet sources for catalogue filters** (added 2026-08-01, COR-003). Filter options are derived
from — and limited to — the distinct values actually present in these verified fields. Nothing is
added, renamed, or inferred:

| Filter | Verified source | Requirement |
| --- | --- | --- |
| Category | `approved_category.slug` — the three approved categories | FR-034 |
| Use-case | `approved_use_cases` — the five approved facets | FR-035 |
| **Access method** | **`unlock_methods`** (or its approved equivalent) | **FR-149** |
| **Verified feature** | The approved specification fields above, where a field yields a discrete, evidence-backed facet | **FR-148** |
| Availability | Verified availability data only | FR-036, BR-012 |
| Price | Rendered **only** when at least one in-scope product carries a verified price — today none do | FR-037 |

A facet whose verified source yields zero values is **omitted entirely**, never rendered empty
(FR-150). No capability or compatibility may be invented to populate a filter.

**Public identifiers** (added 2026-08-01, COR-006). `source_model_code` is the verified public
identifier per product record. It may be displayed on product details under FR-156. Internal
identifiers — `launch_id`, `source_record_id`, `media_asset_id`, `source_document_sha256` — are
**never** customer-facing.

### 2.4 Verified commerce posture — the decisive finding

Every one of the 21 approved products carries:

```
"commerce_mode":  "quote_only"
"public_actions": ["request_price", "request_quote", …]
"retail_price":   null
"currency":       null
"discount":       null
"stock":          null
"warranty":       null
```

Confirmed mechanically: `retail_price` occurs 21 times in v2 and **21 of 21 are `null`**; in v1,
10 of 10 are `null`. `commerce_mode` is `quote_only` for 21 of 21.

Corroborated by the legacy repository's own statements:

- `product-source-register.v1.json` → `register_policy`: *"Supplier evidence only. Every record
  is unapproved and unpublished; source USD prices are supplier references and cannot populate
  storefront retail offers."* (209 supplier records across 3 catalogue PDFs, each sha256-pinned:
  `Lezn图册.pdf` 27, `fengshen Product Catalog_20241015.pdf` 115, `Rarlux` 67.)
- `apps/commerce/management/commands/_demo_store_data.py` → *"the repository's own retail-price
  firewall … price is null and … supplier figures may never populate a Retail Offer. The price
  ladder below is therefore **owner-authorised demo data, not evidence**."*
- `specs/014-storefront-commerce-paymob/plan.md` → *"The quote-only path is the **WORKING
  production behaviour**."*

**Consequence for Specification 002**: quote-only is the verified default. The priced commerce
journey (cart, VAT, free-shipping threshold, checkout totals) is fully specified but is
**conditional on a verified price existing for that product** (BR-010, FR-040). See §4.1.

### 2.5 Verified locale/currency posture

| Fact | Legacy source | Use |
| --- | --- | --- |
| `DEFAULT_CURRENCY_CODE = "EGP"` | `apps/commerce/management/commands/activate_commerce.py` | Corroborates EGP as the storefront currency |
| EGP exponent = 2 | `apps/products/tests/test_product_detail_storefront.py`, `test_card_purchasable_controls.py` | Currency has 2 decimal places; supports Decimal-safe rounding rule BR-007 |

## 3. USER-AUTHORIZED — permitted, provenance = this instruction

These are **not** derived from the legacy repository. They are authorized directly by the user in
the Specification 002 instruction (2026-08-01) and are recorded as such per Constitution XX.16.

| Value | Provenance | Storage rule |
| --- | --- | --- |
| Hotline `19919` | User-authorized, 2026-08-01. **Not present anywhere in the legacy repository** (verified by grep). | Centrally configurable; never a template literal (FR-093) |
| Contact location "New Cairo" | User-authorized, 2026-08-01. In legacy only inside demo/seed/backup fixtures (`scripts/seed_phase04.py`, `apps/commerce/management/commands/_demo_store_data.py`, `media/spec011-local-development-backups/…`) — i.e. demonstration data, not verified production truth. | Centrally configurable. **No more precise address may be invented** (FR-094) |
| Egyptian VAT 14% | User-authorized business rule | Centralized calculation (BR-005) |
| Free-shipping threshold 1,500 EGP | User-authorized business rule | Centralized calculation (BR-006) |
| Payment methods presented (COD, Vodafone Cash, e& Cash/Etisalat Cash, CashU, InstaPay, 6/12-month card installments) | User-authorized presentation list | Presentation only; availability configuration-driven (FR-084) |
| Same-day delivery, Greater Cairo | User-authorized | Configuration-driven; hidden when disabled (FR-078) |
| Installation service, Greater Cairo + Alexandria | User-authorized | Configuration-driven; hidden when disabled (FR-079) |

## 4. UNVERIFIED — MUST NOT appear as production fact

### 4.1 Prices

| Claim | Status | Required behaviour |
| --- | --- | --- |
| Retail price range **2,190–7,490 EGP** | **UNVERIFIED — no source found.** Exhaustive search of the legacy repository for `2190`, `7490`, `2,190`, `7,490` as values returned only an SVG polygon coordinate and a sha256 substring. Neither is a price. | Planning-range hint only (Constitution XX.10). MUST NOT be displayed, seeded into production, or used to compute any displayed total. May appear only inside an isolated development fixture (FR-100) |
| Supplier USD figures (209 records) | Supplier reference only; explicitly barred by the source register's own policy | MUST NOT populate any retail offer or be converted to EGP for display |
| Any per-product retail price | **Absent from the approved catalogue (21/21 null)** | Product renders the quote-only state until a verified price is supplied (FR-040) |

### 4.2 Content invented by the visual reference

The published reference is a design prototype whose copy is **US-market placeholder content**. The
following appear in the reference and are **prohibited** in ZAKEY v2 production (Constitution V.3):

| Reference content | Why prohibited |
| --- | --- |
| "500K+ Homes Protected" | Invented customer total |
| "99.9% Uptime Guarantee" | Invented service guarantee |
| "4.9★ Average Rating" | Invented rating |
| "5-Year Warranty" | Invented warranty; approved catalogue has `warranty: null` |
| "30-Day Returns" | Invented returns promise |
| "24/7 Support" | Invented service promise |
| "Award-Winning Design" | Invented award |
| "Free shipping on orders over $299" | Wrong currency and wrong threshold; ZAKEY uses 1,500 EGP |
| "Use code ZAKEY10 for 10% off" | Invented discount claim |
| "12 Products / 8 Products / 6 Products / 14 Products" category counts | Invented counts; must be derived from real catalogue data |
| "Trusted by Homeowners" testimonials | Invented reviews; must be data-driven or hidden (V.9) |
| Product names "ZAKEY Apex Pro", "ZAKEY Luxe Series", "ZAKEY Slim Touch", "ZAKEY Connect X", "ZAKEY Guardian", "ZAKEY Nexus Elite", "ZAKEY Entry Plus", "ZAKEY Vault Pro" | **Fabricated.** Verified evidence shows products are Lezn-branded and `supplier-branded_not-zakey-manufactured`. Presenting them as ZAKEY-manufactured products would be a false origin claim |
| Category names "Deadbolts", "Padlocks", "Accessories", "Smart Home Kits" | Not in the approved category vocabulary (only palm-vein, face-recognition, handle locks) |
| Footer destinations "Careers", "Press", "Partners", "Blog", "Help Center", "Installation", "Warranty", "Returns" | No verified content exists behind them; must be omitted or route to real content (FR-013) |
| Unsplash stock photography (`photo-1558618666…`, `photo-1586023492125…`, `photo-1558618047…`) | Not ZAKEY product media; 3 stock images reused across 16 slots. Must be replaced from the verified media register |

### 4.3 Delivery and payment providers

| Name | Status | Required behaviour |
| --- | --- | --- |
| Aramex | User-supplied name only. **No verified partnership evidence.** | MUST NOT be presented as an official ZAKEY partner (Constitution XXI.6). May appear only as a neutral, configuration-driven carrier option once an integration genuinely exists |
| EgyptAir | Same | Same |
| EDEX | Same | Same |
| Paymob (legacy integration target) | Legacy spec-014 states credentials are an operator action; no live credentials exist | Any card/wallet path renders the honest integration-ready or unavailable state (FR-088) |

## 5. Development-only fixtures

Permitted only under Constitution V.10–V.11 and FR-100:

- MUST be stored, named, and loaded separately from production content.
- MUST be identifiable as demonstration data at the data layer.
- MUST be impossible to publish accidentally (enforced by configuration or an explicit guard, covered by a test — FR-101).
- MUST NOT appear in normal production output.
- The 2,190–7,490 EGP range and any demo price ladder are permitted **only** inside such a fixture.

## 6. Prohibited vocabulary in visible production UI

Per Constitution V.5 and FR-102, visible production surfaces MUST NOT contain: `demo`,
`placeholder`, `Figma`, `lorem ipsum`, internal notes, or development instructions — in copy, alt
text, titles, ARIA labels, user-visible filenames, or metadata.

## 7. Open provenance risks

| # | Risk | Handling in Specification 002 |
| --- | --- | --- |
| PR-01 | No verified retail price exists for any product | Quote-only is the specified default; the priced journey activates per-product only when a verified price exists (BR-010) |
| PR-02 | Products are supplier-branded (Lezn), not ZAKEY-manufactured | Specification forbids implying ZAKEY manufacture; product naming follows `public_display_name` (FR-055) |
| PR-03 | Reference testimonials/partners have no verified counterpart | Reviews and Brand Partners sections are data-driven and hidden entirely when unverified (FR-025, FR-027) |
| PR-04 | Hotline and location are user-authorized, not independently verified | Recorded as user-authorized provenance; centrally configurable; no further precision invented |
| PR-05 | 49 media assets vs 21 approved products — role coverage unconfirmed per product | Missing-media state specified (FR-062); coverage confirmation deferred to planning, not assumed |

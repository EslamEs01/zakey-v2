# Targeted Visual Grounding Inventory — Specification 002

**Feature**: `002-egypt-premium-storefront`
**Gate**: Constitution v2.0.1, Principle XIX (Targeted Visual Grounding Gate)
**Reference**: `https://remote-fried-86528699.figma.site/`
**Inspected**: 2026-08-01, real browser (Chromium 148.0.7778.97), viewports 1440 / 1024 / 768 / 390
**Evidence**: 35 verified full-page screenshots — see `reference-screenshots/MANIFEST.md`

This document records **observed facts only**. ZAKEY adaptations are recorded separately in
`reference-fidelity-matrix.md` (Constitution XIX.4, XIX.6).

## 0. Reference-wide observations

| Property | Observed value |
| --- | --- |
| Document title | "Premium E-commerce Website UI" |
| `<html lang>` | `en` |
| `<html dir>` | **absent** (LTR by default) |
| Heading typeface | **Poppins**, weight 700 |
| Body typeface | Inter / system UI stack |
| Routing | Client-side SPA. Navigation is `<button>`-driven; **there are no internal `<a href>` URLs**. The only anchor on the page points to figma.com. |
| Currency in copy | **USD** throughout (`$389`, `$299`, `$249`, `$459`, `$0–$600`) |
| Money-shaped strings on home | `$299`, `$389` |

## 1. Ratified design tokens — confirmation status

Every core token ratified in Constitution v2.0.1 was **observed in the live reference**:

| Ratified token | Value | Observed as | Census (home @1440) |
| --- | --- | --- | --- |
| Primary navy | `#0D1B3D` | `rgb(13, 27, 61)` | 56 text uses, 25 background uses |
| Accent gold | `#C9A227` | `rgb(201, 162, 39)` | 178 text uses, 12 background uses |
| Main background | `#F8F9FB` | `rgb(248, 249, 251)` | 12 background uses |
| White | `#FFFFFF` | `rgb(255, 255, 255)` | 30 background uses, 88 text uses |
| Primary text | `#1F2937` | `rgb(31, 41, 55)` | 272 text uses (most frequent) |
| Secondary text | `#6B7280` | `rgb(107, 114, 128)` | 44 text uses |
| Subtle surface | `#EEF0F5` | `rgb(238, 240, 245)` | 13 background uses |

**Shadows**: overwhelmingly `none` (28 of the top entries are fully transparent); one faint
`rgba(0,0,0,0.3) 0 0 0.5px` entry. The reference is genuinely shadow-restrained, consistent with
the ratified "soft and restrained" rule.

### 1.1 GOVERNANCE FINDING — corner radius mismatch

| Radius | Occurrences (home @1440) |
| --- | --- |
| **16px** | **65** ← dominant |
| pill / fully rounded | 15 |
| **12px** | **11** |
| 24px | 5 |
| 10px | 4 |

The Constitution ratifies **12px** as the *Primary corner radius*. The reference's dominant radius
is **16px**. Per the v2.0.1 re-verification rule, a ratified value that grounding contradicts is a
**defect report requiring an amendment — never a unilateral substitution**. This is raised as
open question **OQ-01**; Specification 002 continues to require the ratified 12px until the
Constitution is amended.

## 2. Shared shell — observed anatomy

| Element | 1440 | 1024 | 768 | 390 |
| --- | --- | --- | --- | --- |
| Announcement bar height | 40px | 40px | 40px | **60px** (text wraps to 2 lines) |
| Header height | 73px | 73px | 73px | 73px |
| Header position | `sticky`, `z-index: 50`, `background: #FFFFFF` | same | same | same |
| Content container width | **1344px** (48px gutters) | **928px** (48px gutters) | fluid, 720px inner (24px gutters) | fluid, 342px inner (24px gutters) |
| Primary navigation | Inline: Home · Shop · About · Contact · Products▾ | **Hamburger** | Hamburger | Hamburger |
| Header icon controls | search, account, wishlist, cart (4 × 40×40) | 4 | 4 | **2 only — search, cart** (account and wishlist removed) |
| Header CTA | "Shop Now" (111×40) | present | present | present |

**Header order (LTR)**: logo → nav links → `search` `account` `wishlist` `cart` → "Shop Now".

**Announcement bar copy**: "★ Free shipping on orders over $299 — Use code ZAKEY10 for 10% off".

**Mobile navigation**: opening the hamburger **expands the header inline** (document height grows
by 205px at both 768 and 390). It is **not** an overlay drawer: zero elements with
`position: fixed` larger than 120×120, and `document.querySelectorAll('[role=dialog],[aria-modal=true]').length === 0`.

**Products dropdown**: 4 entries, each 190×40, revealed under the "Products" trigger (chevron
`m6 9 6 6 6-6`).

**Footer**: 5-column grid, 48px gap. Columns observed — *Products* (Smart Locks, Deadbolts,
Padlocks, Accessories, Smart Home Kits); *Company* (About Us, Careers, Press, Partners, Blog);
*Support* (Help Center, Installation, Warranty, Returns, Contact Us); 4 social icon buttons
(36×36); legal row (Privacy Policy, Terms of Service, Cookie Policy). Copyright line:
"© 2025 ZAKEY Technologies. All rights reserved."

## 3. Home page — verified band order and geometry (@1440)

Measured top offsets and background colours, in document order:

| # | Band | Top | Height | Background | Heading |
| --- | --- | --- | --- | --- | --- |
| 1 | Announcement bar | 0 | 40 | — | — |
| 2 | Header | 40 | 73 | `#FFFFFF` | — |
| 3 | **Hero** | 113 | 792 | `#0D1B3D` | "Security Reimagined." |
| 4 | Trust strip | 905 | 69 | `#FFFFFF` | — |
| 5 | **Shop by Category** | 974 | 686 | `#F8F9FB` | "Shop by Category" |
| 6 | **Best Sellers** | 1660 | 758 | `#FFFFFF` | "Best Sellers" |
| 7 | Product spotlight | 2418 | 617 | `#0D1B3D` | "The ZAKEY Nexus Elite" |
| 8 | **Featured Products** | 3034 | 758 | `#F8F9FB` | "Featured Products" |
| 9 | **Why Choose ZAKEY?** | 3792 | 886 | `#FFFFFF` | "Why Choose ZAKEY?" |
| 10 | **Smart-home solutions** | 4678 | 800 | `#F8F9FB` | "Works With Your Smart Home" |
| 11 | **Customer reviews** | 5478 | 577 | `#0D1B3D` | "Trusted by Homeowners" |
| 12 | **Brand partners strip** | 6055 | 217 | `#FFFFFF` | (no heading) |
| 13 | **Newsletter** | 6272 | 518 | `#F8F9FB` | "Get Exclusive Updates" |
| 14 | Footer | 6790 | 405 | — | — |

Background rhythm alternates `#FFFFFF` → `#F8F9FB` with two full-bleed `#0D1B3D` bands (hero,
spotlight) and one navy reviews band.

### 3.1 Typography scale (measured)

| Element | 1440 | 1024 | 768 | 390 |
| --- | --- | --- | --- | --- |
| `h1` | 72px / 79.2px / 700 | 60px / 66px / 700 | 48px / 52.8px / 700 | 48px / 52.8px / 700 |
| `h2` | 36px / 40px / 700 | 36px / 40px | 36px / 40px | 36px / 40px |
| `h3` | 18px / 22.5px / 700 | 18px / 22.5px | 18px / 22.5px | 18px / 22.5px |

All headings render in **Poppins 700**. `h2` and `h3` do not scale down; only `h1` does.

### 3.2 Grid behaviour (columns × gap)

| Section | 1440 | 1024 | 768 | 390 |
| --- | --- | --- | --- | --- |
| Hero split | 2 × 64px | 2 × 64px | 1 × 64px | 1 × 64px |
| Shop by Category (4 items) | **4 × 24px** | **4 × 24px** | 2 × 24px | 2 × 24px |
| Best Sellers (4 items) | 4 × 24px | 4 × 24px | 2 × 24px | **1 × 24px** |
| Featured Products (4 items) | 4 × 24px | 4 × 24px | 2 × 24px | **1 × 24px** |
| Why Choose (6 items) | 3 × 32px | 3 × 32px | 2 × 32px | 1 × 32px |
| Stats block (4 items) | 2 × 16px | 2 × 16px | 2 × 16px | 2 × 16px |
| Footer | 5 × 48px | 5 × 48px | — | — |

Notable: the product grid stays at **4 columns down to 1024px**, collapses to 2 at 768, and to a
single column at 390. Category cards keep **2 columns even at 390px**.

### 3.3 Image ratios (intrinsic → displayed)

| Role | Intrinsic | Displayed @1440 | Ratio |
| --- | --- | --- | --- |
| Hero product | 500×500 | 382×382 | 1:1 |
| Category card | 400×500 | 318×398 | **4:5** |
| Product card | 400×400 | 316×316 | **1:1** |
| Spotlight | 800×600 | 720×617 | 4:3 |
| Smart-home | 600×600 | 640×640 | 1:1 |

**Defect**: 4 of the 16 home images have `naturalWidth === 0` — **broken images** (Padlocks
category, ZAKEY Slim Touch, ZAKEY Nexus Elite ×2). All 16 images resolve to only **3 distinct
Unsplash stock photographs**, reused across every slot.

## 4. Catalog page ("All Products") — observed

Reached from the header "Shop" entry **and** from any product card's "View" control.

| Property | Observed |
| --- | --- |
| Page title / subtitle | "All Products" / "Explore our complete collection of smart security solutions" |
| Layout @1440 | Sidebar + 3-column product grid (grid width 1024, gap 24px) |
| Layout @1024 | Sidebar + **2-column** grid (grid width 608, gap 24px) |
| Layout @390 | **1 column**, and **horizontal overflow present** |
| Filter groups | **Category** (radio inputs with counts: Smart Lock (5), Deadbolt (2), Padlock (1), one empty (0)); **Price Range** (`input[type=range]`, `$0`–`$600`); **Minimum Rating** |
| Filter reset | "Clear All Filters" |
| Result count | "8 products" |
| Sort control | `<select>`: Featured · Price: Low to High · Price: High to Low · Top Rated |
| Pagination | `1 2 3 … 8` |
| Card anatomy | badge ("Best Seller" / "Premium") · category label ("SMART LOCK") · product name · review count ("(312)") · price ("$389") · compare-at price ("$459") · "View" control · icon control |
| Mobile filter affordance | "Filters" control present at 390 |

## 5. Cart — observed

| Property | Observed |
| --- | --- |
| Heading | "Shopping Cart (0 items)" |
| Body | "Your cart is empty" / "Discover our premium smart lock collection" / "Shop Now" |
| Line items | **None** |
| Totals / subtotal / VAT / shipping | **None** |
| Checkout control | **None** |
| After activating "Add to Cart" | Cart still reports 0 items — `cart-filled-*` captures are indistinguishable from the empty state |

**Conclusion**: the reference cart is an empty-state mock only. There is **no populated cart, no
totals block, and no checkout journey** in the reference.

## 6. Account — observed

| Property | Observed |
| --- | --- |
| State | Permanently signed-in stub |
| Identity shown | "John Smith" / "john@example.com" / "Premium Member" — fabricated |
| Account navigation | My Orders · Wishlist · Addresses · Payment Methods · Account Settings · Sign Out |
| Order history | 4 fabricated orders (`#ZK-20250112` $389.00 Delivered; `#ZK-20241228` $299.00 In Transit; `#ZK-20241115` $469.00; `#ZK-20240930` $199.00) |
| Login / registration form | **Absent** |

## 7. Search and wishlist — observed

| Control | Behaviour |
| --- | --- |
| Search | Expands an **inline** search bar; document height grows 7195 → 7257 (+62px). Input placeholder "Search products, categories…". No modal, no dialog role. |
| Wishlist | **Inert.** Activating it produces no observable change (document height unchanged at 7195, no panel, no route change). A dead control. |

## 8. Contact — observed

| Property | Observed |
| --- | --- |
| Heading | "GET IN TOUCH" / "We'd Love to Hear From You" |
| Contact cards | **"Call Us +1 (800) 929-5390, Mon–Fri 8am–8pm EST"**; **"Email Us support@zakey.com, Response within 2 hours"**; **"Visit Us 12 Innovation Drive, Singapore 138668, By appointment only"** |
| Form fields | First Name · Last Name · email · Subject (`<select>`: Product Inquiry, Technical Support, Order Status, Warranty Claim, Partnership) · message `<textarea>` |
| Form submit | "Send Message" |
| FAQ | "30-day no-questions-asked returns" · "Professional installation available in 50+ cities" · "full 5-year warranty" |
| Extra control | "Start Live Chat" (no backing implementation observable) |

All contact details are **US/Singapore placeholder data**, unusable for an Egyptian storefront.

## 9. About — observed

Heading "OUR STORY" / "Built on Trust, Driven by Innovation". Body claims: "Since 2018", plus a
statistics block — **"500K+ Homes Protected", "47 Countries Served", "28 Industry Awards",
"4.9★"**.

## 10. Reference defects register

Each entry states the observed defect and the Constitution clause that authorises a correction
(Constitution I.4 / XIX.7 permit correction **only** for usability, accessibility, RTL
correctness, responsiveness, content truth, or an Egyptian-market requirement).

| ID | Defect observed | Evidence | Correction basis |
| --- | --- | --- | --- |
| RD-01 | `lang="en"`, no `dir` attribute | DOM inspection, all viewports | RTL correctness + Egyptian market |
| RD-02 | **Every header control has no accessible name** — search, account, wishlist and cart are icon-only with `aria-label` absent | 4/4 icon buttons `aria=(NONE)` | Accessibility (WCAG 4.1.2) |
| RD-03 | Form inputs unlabelled — newsletter email, search field, all 5 contact fields, price-range slider, sort select all report `aria=NONE, labelled=false` | DOM inspection | Accessibility (WCAG 1.3.1, 3.3.2) |
| RD-04 | Mobile menu is an inline expansion with **no dialog role and no focus trap** | `dialogs=0`, no fixed panel, +205px height | Accessibility (WCAG 2.4.3) |
| RD-05 | **Horizontal overflow on the catalog page at 390px** | `scrollWidth > clientWidth` at 390 | Responsiveness (Constitution VII.4) |
| RD-06 | **4 of 16 home images are broken** (`naturalWidth === 0`) | Image census | Usability + content truth |
| RD-07 | Only 3 distinct stock photographs reused across 16 image slots; none are ZAKEY product media | Image `src` census | Content truth |
| RD-08 | **Wishlist control is inert** (dead control) | No observable change on activation | Usability (Constitution VI.2) |
| RD-09 | Navigation uses `<button>` with no URLs — no deep links, no history, no shareable state | Zero internal anchors | Usability + Constitution VI.5 |
| RD-10 | Fabricated credibility claims: 500K+ homes, 99.9% uptime, 4.9★, 28 awards, 47 countries, 5-year warranty, 30-day returns, 24/7 support, award-winning design, "Since 2018" | Home + About text | Content truth (Constitution V.3) |
| RD-11 | Fabricated account identity and order history ("John Smith", 4 fake orders) | Account page | Content truth |
| RD-12 | US/Singapore contact data and USD pricing throughout | Contact page, all prices | Egyptian-market requirement |
| RD-13 | Invented discount claim "Use code ZAKEY10 for 10% off" and "$299" free-shipping threshold | Announcement bar | Content truth + Egyptian market |
| RD-14 | Invented category counts (12/8/6/14 Products) and category vocabulary (Deadbolts, Padlocks, Accessories, Smart Home Kits) not in the approved catalogue | Category cards | Content truth |
| RD-15 | Fabricated ZAKEY-branded product names implying ZAKEY manufacture | Product cards | Content truth — verified evidence says `supplier-branded_not-zakey-manufactured` |
| RD-16 | "Start Live Chat" control with no backing capability | Contact page | Usability (Constitution VI.2) |
| RD-17 | Footer destinations (Careers, Press, Partners, Blog, Help Center, Installation, Warranty, Returns) with no verified content behind them | Footer | Usability + content truth |

## 11. Structural absences in the reference

| Required ZAKEY page | Present in reference? | Consequence |
| --- | --- | --- |
| Home | ✅ Yes, complete | Direct grounding |
| Shop / catalog | ✅ Yes | Direct grounding at all four widths (1440, 1024, 768, 390) |
| **Product details** | ❌ **No** — "View" routes to catalog | Evidence-based adaptation required |
| **Cart (populated)** | ❌ Empty state only | Evidence-based adaptation required |
| **Checkout** | ❌ **No** | Evidence-based adaptation required |
| **Login / registration** | ❌ **No** — account is a signed-in stub | Evidence-based adaptation required |
| My Account | ⚠️ Stub with fabricated data | Structure grounded; content rejected |
| About | ✅ Yes | Structure grounded; claims rejected |
| Contact | ✅ Yes | Structure grounded; data rejected |

## 12. Grounding gate status

| Constitution XIX rule | Status |
| --- | --- |
| XIX.1 real browser inspection of the exact page/state | ✅ Chromium 148; 35 verified captures retained from 43 taken, 8 deleted as unverifiable |
| XIX.2 desktop, tablet, mobile behaviour incl. interactive states | ✅ menu-open, search, wishlist, cart, account, products-menu captured |
| XIX.3 evidence at 1440 / 1024 / 768 / 390 | ✅ for Home and the shared shell; ✅ for Home, the shared shell and the Catalog; ⚠️ partial for About/Contact (1440, 1024) and Account (no 390) — declared in MANIFEST |
| XIX.4 record section order, anatomy, widths, grid, typography, spacing, colour, radii, shadows, image ratios, states, responsive transformations | ✅ §§1–9 |
| XIX.5 map each planned page/component to inspected evidence | ✅ `reference-fidelity-matrix.md` |
| XIX.6 document deviations with justification | ✅ `reference-fidelity-matrix.md` |
| XIX.7 correct reference defects only on the six permitted grounds | ✅ §10, each with a stated basis |
| XIX.8 no runtime reference code copied | ✅ Only rendered geometry, colour, and text were measured. No source was extracted or reused |
| XIX.10 evidence recorded with inspection date | ✅ 2026-08-01 throughout |

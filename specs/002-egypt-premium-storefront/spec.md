# Feature Specification: ZAKEY v2 Premium Egyptian Storefront

**Feature Branch**: `002-egypt-premium-storefront`
**Feature Number**: `002`
**Created**: 2026-08-01
**Status**: Draft — ready for planning
**Constitution**: ZAKEY v2 Premium Egyptian Storefront Constitution **v2.0.1**
**Active lead agent**: Claude Code (Constitution Principle XVI.1–XVI.2)
**Input**: Clean-room rebuild of the ZAKEY public storefront as a premium Arabic-first Egyptian e-commerce experience for smart door locks and verified smart-home products.

---

## 1. Purpose and Product Outcome *(mandatory)*

### 1.1 Problem statement

ZAKEY has no public storefront that an Egyptian customer can actually use. The previous
implementation was rejected by the client. The legacy platform's verified product data exists but
is not presented in any customer-facing experience that is Arabic-first, RTL-correct, priced in
Egyptian pounds, or truthful about what ZAKEY can and cannot currently deliver.

Two failure modes must not recur:

1. **A storefront that looks premium but lies** — inventing ratings, warranties, awards, customer
   totals, prices, and partnerships to fill a template.
2. **A storefront that is English-first with Arabic bolted on** — LTR geometry, foreign currency,
   and address forms that do not match how Egyptians actually receive deliveries.

### 1.2 Product outcome

When this feature ships, an Egyptian customer can, entirely in Egyptian Arabic and in a
right-to-left interface:

- browse the verified ZAKEY smart-lock catalogue by category, use-case, and availability;
- open a product and read only facts that trace to a verified source;
- for a product with a verified price: add it to a cart, see subtotal, VAT, shipping and grand
  total computed identically everywhere, and complete a checkout that produces a **real order
  draft**;
- for a product without a verified price (the verified state of all 21 approved products today):
  request a price or quote through an honest, working path — never a fake "buy" button;
- register, sign in, and see a truthful account area with an honest empty order history;
- reach ZAKEY through a working contact form and the published hotline.

### 1.3 Where this feature stops

This feature delivers the **customer-facing storefront and an order-draft/enquiry milestone**. It
does not deliver settled payment, carrier integration, an admin console, or order fulfilment. Those
boundaries are enumerated in §22.

---

## 2. Authoritative Sources and Evidence *(mandatory)*

| Source | Method of inspection | Date | Result |
| --- | --- | --- | --- |
| `https://remote-fried-86528699.figma.site/` | Real browser (Chromium 148.0.7778.97), 4 viewports, 35 verified full-page captures + DOM geometry measurement | 2026-08-01 | HTTP 200. **Visual authority.** Full record in `visual-reference-inventory.md`; evidence list in `reference-screenshots/MANIFEST.md` |
| `/media/mekky/work/backend/zakey.v1` (legacy) | Read-only Git/filesystem inspection. Nothing created, modified, moved, or deleted | 2026-08-01 | HEAD `5fdd81d`. **Content and asset authority.** Full record in `content-asset-provenance.md` |
| Constitution v2.0.1 | Direct read | 2026-08-01 | Binding governance. Compliance mapped in §23 |
| Specification 002 instruction (user) | Direct | 2026-08-01 | **Business and localization authority** for Egyptian market rules, hotline, and location |

### 2.1 Source conflicts and their resolution

| Conflict | Resolution | Authority |
| --- | --- | --- |
| Reference shows ZAKEY-branded products (Apex Pro, Nexus Elite…). Legacy evidence shows products are **Lezn-branded**, `supplier-branded_not-zakey-manufactured` | Legacy wins. Product naming follows `public_display_name`. ZAKEY manufacture MUST NOT be implied | Constitution V.3 |
| Reference prices products in USD. Legacy approved catalogue has `retail_price: null` for **21 of 21** products, `commerce_mode: "quote_only"` | Legacy wins. Quote-only is the default; the priced journey is conditional (BR-010) | Constitution V.4, XX.10 |
| Reference typeface is Poppins. Constitution ratifies **Cairo** as primary | Constitution wins — a ratified, recorded deviation | Constitution, Typography deviation note |
| Reference is `lang="en"`, LTR | Constitution wins — `ar-EG`, RTL primary | Constitution XX.2 |
| Reference free-shipping threshold `$299`; instruction says **1,500 EGP** | Instruction wins | Constitution XX.7 |
| Instruction cites an approximate range of 2,190–7,490 EGP. **No source for it exists in the legacy repository** (verified by exhaustive search) | Treated as an unverified planning hint. MUST NOT be displayed or used in any computed total | Constitution XX.10 |

---

## 3. Targeted Visual Grounding Evidence *(mandatory for UI work)*

Full record: `visual-reference-inventory.md`. Per-surface mapping: `reference-fidelity-matrix.md`.

| Surface | Reference state inspected | Date | Widths captured | Key observations |
| --- | --- | --- | --- | --- |
| Shared shell | Header/announcement/footer on every route | 2026-08-01 | 1440, 1024, 768, 390 | Announcement 40px (60px @390); header 73px sticky white z-50; container 1344/928/fluid; nav collapses to hamburger at ≤1024; only search+cart icons at 390; footer 5-col/48px |
| Home | Landing page, full scroll | 2026-08-01 | 1440, 1024, 768, 390 | 14 bands; verified order and background rhythm (inventory §3); h1 72→60→48px; product grid 4/4/2/1 |
| Catalog | "All Products" | 2026-08-01 | 1440, 1024, 768, 390 | Sidebar filters, sort select, 8 cards, pagination 1‑2‑3‑…‑8; grid 3/2/1; docH 2574/2942/3360/6004; **horizontal overflow measured at 390** |
| Cart | Cart route | 2026-08-01 | 1440, 1024, 768, 390 | **Empty state only** — no line items, no totals, no checkout |
| Account | Account route | 2026-08-01 | 1440, 1024, 768 | Signed-in stub, fabricated identity and orders, **no login/registration** |
| Search | Search control activated | 2026-08-01 | 1440, 1024, 768, 390 | Inline expanding bar (+62px), not a modal |
| Wishlist | Wishlist control activated | 2026-08-01 | 1440, 1024, 768 | **Inert — dead control** |
| Mobile nav | Hamburger activated | 2026-08-01 | 1024, 768, 390 | Inline header expansion (+205px), **no dialog role, no focus trap** |
| Products menu | Dropdown activated | 2026-08-01 | 1440, 1024 | 4 entries, 190×40 |
| About | About route | 2026-08-01 | 1440, 1024 | Fabricated statistics block |
| Contact | Contact route | 2026-08-01 | 1440, 1024 | US/Singapore contact data; 5-field form, all unlabelled; invented FAQ claims |
| Product details | **Sought and not found** | 2026-08-01 | 1440, 1024, 768, 390 | "View" routes to the catalog. **No product-details page exists in the reference** |
| Checkout | **Sought and not found** | 2026-08-01 | — | No checkout journey exists in the reference |

### 3.2 Declared evidence gaps

Recorded rather than hidden (Constitution XIX.9 — a surface is grounded only by its own evidence):

1. **About and Contact** are grounded at **1440 and 1024 only**; **My Account** at 1440/1024/768.
   Their remaining-width requirements are derived from the home page's verified transformations at
   those widths (same shell, same grid system) and are marked **evidence-based adaptation** in the
   matrix. Captures produced under those labels during the grounding pass were proven by content
   hash and DOM heading to be a different page, and were deleted rather than retained under a
   misleading name.
2. Product details, Checkout and Login/Registration have **no reference equivalent**. They are
   specified as compositions of inspected components and marked **evidence-based adaptation**.
3. Hover/active/disabled pseudo-states were not captured; their requirements derive from ratified
   tokens and Principle VIII contrast rules, not from reference grounding.

### 3.3 Deviations from the reference

| # | Reference behaviour | ZAKEY v2 behaviour | Category | Basis |
| --- | --- | --- | --- | --- |
| D-01 | `lang="en"`, LTR | `lang="ar"`, `dir="rtl"`, mirrored layout | Defect correction | RTL / Egyptian market |
| D-02 | Poppins headings | Cairo primary; Poppins for Latin content only | Ratified deviation | Constitution XX.3 |
| D-03 | USD prices, `$299` threshold, "ZAKEY10" code | `ج.م`, 1,500 EGP threshold, no invented code | Defect correction | Content truth + Egyptian market |
| D-04 | Icon controls with no accessible name | Every control has an accessible name in Arabic | Defect correction | Accessibility |
| D-05 | Unlabelled form inputs | Every input programmatically labelled with errors linked | Defect correction | Accessibility |
| D-06 | Mobile menu = inline expansion, no focus trap | Focus-trapped, dismissible panel returning focus to its trigger | Defect correction | Accessibility |
| D-07 | Horizontal overflow at 390 on catalog | Zero unintended overflow at all four widths | Defect correction | Responsiveness |
| D-08 | Broken images; 3 stock photos reused | Verified ZAKEY media register; explicit missing-image state | Defect correction | Content truth |
| D-09 | Inert wishlist; "Start Live Chat"; dead footer destinations | Every visible control works or is honestly unavailable | Defect correction | Usability |
| D-10 | Button-based navigation, no URLs | Real, shareable, deep-linkable URLs with browser history | Defect correction | Usability |
| D-11 | Fabricated stats, warranty, awards, reviews, partners, account identity | Data-driven or hidden entirely | Defect correction | Content truth |
| D-12 | "Buy"-shaped controls on unpriced products | Quote-only products expose Request Price / Request Quote | Defect correction | Content truth |
| D-13 | Category vocabulary (Deadbolts, Padlocks, Accessories, Smart Home Kits) | Approved vocabulary only: Palm Vein Locks, Face Recognition Locks, Handle Locks | Defect correction | Content truth |
| D-14 | Reference dominant radius 16px | Ratified 12px retained pending amendment | Governance | Constitution II.1 + re-verification rule (see OQ-01) |
| D-15 | Contact: US phone, Singapore address | Hotline `19919`, New Cairo | Defect correction | Egyptian market |

**Identity preserved**: band order and rhythm, navy/gold/white/off-white palette, alternating
section backgrounds, two full-bleed navy bands, 12-column desktop grid at 1344px, 8px spacing
system, restrained shadows, 4:5 category imagery, 1:1 product imagery, heading weight and scale
relationships, and the premium minimal character. No new visual identity is introduced.

---

## 4. Clarifications

No clarification session was required. Every question that could have been material was already
settled by the Specification 002 instruction, Constitution v2.0.1, the browser grounding pass, or
the legacy provenance register. Two items are recorded as open questions in §17.5 — neither blocks
planning, and both have a specified default behaviour.

---

## 5. User Scenarios & Testing *(mandatory)*

### 5.1 Actors

| Actor | Description |
| --- | --- |
| **Guest customer** | Egyptian visitor, unauthenticated. Can browse, search, filter, wishlist (session), cart, and request a quote |
| **Registered customer** | Authenticated. Adds a persistent account area and saved details |
| **Content operator** | Supplies verified catalogue, media, prices, and configuration. Not a UI actor in this feature; their data governs what renders |
| **Assistive-technology user** | Uses keyboard-only navigation and/or a screen reader in Arabic RTL |

---

### User Story 1 — Discover the catalogue in Arabic (Priority: P1) 🎯 MVP

A guest lands on the storefront, immediately understands what ZAKEY sells, browses by category,
and reaches a product page — entirely in Egyptian Arabic, right-to-left.

**Why this priority**: Without a truthful, navigable Arabic catalogue there is no storefront.
Every other story depends on it.

**Independent Test**: Load the home page at each of the four ratified widths; confirm `lang="ar"`
and `dir="rtl"`; navigate to a category, then to a product; confirm every rendered fact traces to
the provenance register.

**Acceptance Scenarios**:

1. **Given** a guest opens the home page, **When** the page renders, **Then** the document declares `lang="ar"` and `dir="rtl"`, all interface copy is Egyptian Arabic, and the section order matches the ratified band order (FR-016).
2. **Given** the home page at 390px, **When** the guest scrolls the full page, **Then** the document scroll width never exceeds the viewport width (SC-003).
3. **Given** a guest activates a category card, **When** the catalog opens, **Then** only approved categories are offered — Palm Vein Locks, Face Recognition Locks, Handle Locks (FR-034) — and the result count reflects the actual number of matching products (FR-038).
4. **Given** a product has no verified media in the required role, **When** its card renders, **Then** the defined missing-image state appears and no other product's photograph is substituted (FR-055).
5. **Given** a guest opens a product, **When** the page renders, **Then** every specification shown comes from the approved field list, and any unverified attribute is absent rather than blank-labelled (FR-058, FR-060).

---

### User Story 2 — Request a price for a quote-only product (Priority: P1)

A guest finds a product that has no verified retail price and completes an honest enquiry instead
of a fake purchase.

**Why this priority**: This is the **verified current state of all 21 approved products**. Without
it the storefront either lies or is unusable.

**Independent Test**: With a product whose retail price is unset, confirm no Add-to-Cart control
renders, a Request Price control does render, and submitting it persists a real enquiry.

**Acceptance Scenarios**:

1. **Given** a product with no verified price, **When** its card or detail page renders, **Then** no price, no Add to Cart, and no Buy Now appear; a Request Price / Request Quote control appears instead (FR-050, FR-061).
2. **Given** a guest submits an enquiry with a valid Egyptian mobile number, **When** submission succeeds, **Then** a persisted enquiry record exists and the confirmation states only what actually happened (FR-064).
3. **Given** a guest submits an enquiry with an invalid phone number, **When** the form is submitted, **Then** submission is rejected server-side, the error is programmatically associated with the field, and all other entered values are preserved (FR-065, FR-137).
4. **Given** the enquiry service is unavailable, **When** the guest submits, **Then** a recoverable error state appears, no success is claimed, and the entered data is preserved for retry (FR-066).

---

### User Story 3 — Filter, sort and share catalogue results (Priority: P2)

A guest narrows the catalogue by category, use-case and availability, sorts the results, moves
through pages, and shares the resulting URL with someone else who sees the same results.

**Why this priority**: A catalogue that cannot be narrowed or linked is not usable for a
considered purchase.

**Independent Test**: Apply two filters and a sort, paginate, copy the URL, open it in a clean
session, and confirm identical state and results.

**Acceptance Scenarios**:

1. **Given** filters and a sort are applied, **When** the URL is copied and opened in a new session, **Then** the same filters, sort, page and results are restored (FR-041).
2. **Given** a filter is applied, **When** a second filter is applied, **Then** the first is retained and the result count updates (FR-039).
3. **Given** filters are applied, **When** the guest removes one filter, **Then** only that filter is cleared and search text, sort and other filters survive (FR-042).
4. **Given** filters produce no matches, **When** results render, **Then** the no-result state appears with the active criteria stated and a working way to clear them — never an empty grid (FR-045).
5. **Given** the catalog at 390px, **When** the guest opens filters, **Then** filters present in a focus-trapped panel that returns focus to its trigger on dismissal (FR-046, FR-124).

---

### User Story 4 — Buy a priced product end-to-end (Priority: P2)

For a product that has a verified price and is configured purchasable, a customer adds it to the
cart, reviews truthful totals, and completes checkout to produce a real order draft.

**Why this priority**: This is the commercial goal, but it is **conditional** — it activates per
product only when verified pricing exists.

**Independent Test**: With one product carrying a verified price, complete cart → checkout → order
draft, and confirm every monetary figure is identical across cart, checkout, review and
confirmation.

**Acceptance Scenarios**:

1. **Given** a purchasable product, **When** it is added to the cart, **Then** the cart count updates and the item persists across a page reload in the same session (FR-071, FR-076).
2. **Given** a cart with a subtotal below 1,500 EGP, **When** totals render, **Then** a shipping charge applies and the remaining amount to reach free shipping is stated (BR-006, FR-074).
3. **Given** a cart with a subtotal of at least 1,500 EGP, **When** totals render, **Then** shipping is zero and free shipping is stated (BR-006).
4. **Given** any cart, **When** totals render, **Then** VAT is 14% of the taxable base, and subtotal − discount + shipping + VAT equals the grand total exactly, with no rounding drift (BR-005, BR-007, BR-008).
5. **Given** a cart quantity is set to zero or a non-numeric value, **When** submitted, **Then** the change is rejected server-side with a field-linked error and the previous quantity is retained (FR-073).
6. **Given** an item becomes unavailable while in the cart, **When** the cart is next rendered, **Then** the item is marked unavailable, excluded from totals, and checkout is blocked with a stated reason (FR-078).
7. **Given** a completed checkout, **When** the confirmation renders, **Then** it states an order draft was recorded and does **not** claim payment was received or delivery scheduled (FR-092).
8. **Given** the customer submits checkout twice rapidly, **When** the second submission arrives, **Then** exactly one order draft exists (FR-091).

---

### User Story 5 — Provide a complete Egyptian delivery address (Priority: P2)

A customer supplies a delivery address that an Egyptian courier can actually use.

**Independent Test**: Complete the address step selecting several governorates; confirm all 27 are
offered and the landmark field is captured.

**Acceptance Scenarios**:

1. **Given** the address step, **When** the governorate list opens, **Then** all **27** Egyptian governorates are available (FR-083).
2. **Given** a customer enters a phone number, **When** it is not a valid Egyptian mobile number, **Then** it is rejected server-side with a field-linked Arabic error (FR-084).
3. **Given** a governorate outside Greater Cairo is selected, **When** delivery options render, **Then** same-day delivery is not offered (FR-086).
4. **Given** installation service is disabled by configuration, **When** the delivery step renders, **Then** no installation option appears anywhere (FR-087).
5. **Given** the address step, **When** it renders, **Then** detailed address and landmark fields are present, and landmark guidance is written in natural Egyptian Arabic (FR-085).

---

### User Story 6 — See honest payment options (Priority: P2)

A customer sees which payment methods are genuinely available and is never told a payment
succeeded when it did not.

**Independent Test**: With no gateway credentials configured, confirm every external method renders
as unavailable/integration-ready and cannot be completed.

**Acceptance Scenarios**:

1. **Given** payment presentation renders, **When** a method has no configured, verified integration, **Then** it appears in an explicit unavailable or integration-ready state and cannot be selected to completion (FR-089).
2. **Given** any payment surface, **When** it renders, **Then** no field collects a card number, CVV/CVC, PIN, or magnetic-stripe data (FR-090, BR-013).
3. **Given** installment presentation is enabled, **When** 6- and 12-month options render, **Then** each derives from the same authoritative product price used everywhere else, and no bank arrangement is implied (FR-088, BR-011).
4. **Given** Cash on Delivery is configured available, **When** the customer selects it and completes checkout, **Then** the confirmation states an order draft was recorded, with no claim of settlement (FR-092, BR-015).

---

### User Story 7 — Register, sign in, and manage the account (Priority: P3)

A customer creates an account, signs in, sees a truthful account area, and returns to whatever they
were doing.

**Independent Test**: Register, sign out, attempt a member-only action as a guest, sign in, and
confirm return to the intended destination with an honest empty order history.

**Acceptance Scenarios**:

1. **Given** a guest attempts a member-only action, **When** authentication is required, **Then** after signing in they return to the exact intended destination (FR-105).
2. **Given** a newly registered customer with no orders, **When** order history renders, **Then** an honest empty state appears — no invented orders, statuses, or membership tiers (FR-106).
3. **Given** invalid sign-in credentials, **When** submitted, **Then** the error does not reveal whether the account exists (FR-104, FR-140).
4. **Given** a signed-in customer signs out, **When** sign-out completes, **Then** the session is terminated and member-only surfaces are no longer reachable (FR-107).

---

### User Story 8 — Contact ZAKEY (Priority: P3)

A customer reaches ZAKEY through a working form and the published hotline.

**Independent Test**: Submit the contact form and confirm a persisted record plus an announced,
truthful confirmation; confirm the hotline and location come from configuration.

**Acceptance Scenarios**:

1. **Given** the Contact page, **When** it renders, **Then** the hotline `19919` and the New Cairo location come from central configuration, and no more precise address is shown (FR-109).
2. **Given** a valid contact submission, **When** it succeeds, **Then** a persisted record exists and the confirmation is announced to assistive technology (FR-110, FR-127).
3. **Given** an abusive or automated submission pattern, **When** detected, **Then** the submission is rejected without revealing the detection rule (FR-115).

---

### Edge Cases *(mandatory)*

| # | Condition | Required behaviour |
| --- | --- | --- |
| EC-01 | Catalogue is empty or unavailable | Catalog renders its empty state with a working route home. Never a blank page (FR-044) |
| EC-02 | Product media missing for a required role | Defined missing-image state; no substitute photo (FR-055) |
| EC-03 | Product price removed while in a cart | Item becomes non-purchasable, is excluded from totals, and checkout is blocked with a stated reason (FR-078) |
| EC-04 | Price changes between cart and checkout | The change is surfaced explicitly and must be acknowledged before the order draft is created (FR-079) |
| EC-05 | Session expires mid-checkout | Entered data is preserved where safe; the customer is returned to the correct step with a recoverable message (FR-141) |
| EC-06 | Guest reloads mid-checkout | Progress is restored; no duplicate draft is created (FR-091) |
| EC-07 | Enquiry/contact backend unavailable | Recoverable error; no success claimed; input preserved (FR-066, FR-138) |
| EC-08 | All reviews unverified | Reviews section does not render at all (FR-026) |
| EC-09 | No verified partner logos | Brand-partners strip does not render at all (FR-028) |
| EC-10 | Configuration disables same-day delivery or installation | Those options are absent everywhere, including summaries (FR-086, FR-087) |
| EC-11 | Long Arabic product names | Names wrap without clipping or horizontal overflow at all four widths (SC-003) |
| EC-12 | Latin model codes inside Arabic text | Rendered in correct bidirectional order with no reversed characters (FR-101) |
| EC-13 | Zero search results | No-result state with active query stated and a working reset (FR-045) |
| EC-14 | Reduced-motion preference set | Non-essential motion is suppressed (FR-128) |
| EC-15 | Quantity exceeds a configured per-order maximum | Rejected server-side with a field-linked error stating the limit (FR-073) |

---

## 6. Page Inventory *(mandatory for UI work)*

| # | Surface | Decision | Basis / owner |
| --- | --- | --- | --- |
| 1 | Home | In scope | Required minimum scope; grounded at 4 widths |
| 2 | Shop / catalog | In scope | Required; grounded 1440/1024 |
| 3 | Product details | In scope | Required; **evidence-based adaptation** (no reference equivalent) |
| 4 | Cart | In scope | Required; empty state grounded, populated state adaptation |
| 5 | Checkout (information + review + confirmation) | In scope | Required; adaptation |
| 6 | My Account (register, sign in, sign out, profile, orders) | In scope | Required; stub grounded, auth surfaces adaptation |
| 7 | About | In scope | Required; grounded 1440/1024 |
| 8 | Contact | In scope | Required; grounded 1440/1024 |
| 9 | Search results | In scope | Utility route required for the discovery journey |
| 10 | Wishlist | In scope | The shell exposes the control; a control must work (Constitution VI.2) |
| 11 | Not-found (404) | In scope | Recoverable error state |
| 12 | Server-error (5xx) | In scope | Recoverable error state |
| 13 | Careers, Press, Blog, Help Center, Warranty, Returns, Partners | **Excluded** | No verified content exists (`content-asset-provenance.md` §4.2). The footer MUST NOT link to them (FR-013) |
| 14 | Blog / editorial | **Excluded** | Not required; would invent content |
| 15 | Order tracking | **Deferred** | Requires fulfilment integration — future specification |
| 16 | Payment settlement | **Deferred** | Requires verified gateway credentials — future specification |

---

## 7. Shared Component Inventory *(mandatory for UI work)*

| # | Family | Purpose | States |
| --- | --- | --- | --- |
| C-01 | Announcement bar | Single configurable message | present, absent (unconfigured), 1-line, 2-line wrap |
| C-02 | Header shell | Sticky 73px shell | default, scrolled, mobile-collapsed |
| C-03 | Logo | Verified brand mark | navy-on-light, white-on-navy |
| C-04 | Primary navigation | Category and page destinations | default, hover, focus, current |
| C-05 | Products dropdown | Category menu | closed, open, keyboard-open, focus-managed |
| C-06 | Mobile navigation panel | Full nav at ≤1024 | closed, open, focus-trapped, dismissing |
| C-07 | Search | Catalogue search | closed, open, typing, submitting, no-result |
| C-08 | Wishlist control | Save for later | inactive, active, busy, unavailable |
| C-09 | Cart control + count | Cart entry point | empty (no count), populated, busy |
| C-10 | Account control | Auth entry point | guest, authenticated |
| C-11 | Skip link | Bypass navigation | visually hidden, focused |
| C-12 | Product card | Catalogue unit | priced, quote-only, unavailable, missing-image, loading, hover, focus |
| C-13 | Price block | Money presentation | priced, quote-only, was/now (verified only), installment |
| C-14 | Availability badge | Truthful availability | available, unavailable, unknown-hidden |
| C-15 | Button | Actions | primary, secondary, quiet, hover, focus, active, disabled, busy |
| C-16 | Form field | Input | default, focus, filled, invalid, disabled, described-by-error |
| C-17 | Governorate selector | All 27 governorates | default, focus, invalid |
| C-18 | Quantity control | Cart quantity | default, at-min, at-max, invalid, busy |
| C-19 | Filter group | Catalogue narrowing | collapsed, expanded, applied, cleared |
| C-20 | Filter drawer | Mobile filters | closed, open, focus-trapped |
| C-21 | Sort control | Result ordering | default, changed |
| C-22 | Pagination | Result paging | first, middle, last, single-page |
| C-23 | Result count | Result feedback | count, zero |
| C-24 | Empty state | No content | catalog, cart, wishlist, orders, search |
| C-25 | Error state | Recoverable failure | validation, service, not-found |
| C-26 | Status / live region | Dynamic announcements | polite, assertive, success, error |
| C-27 | Dialog / drawer | Overlay surfaces | open, focus-trapped, dismissing |
| C-28 | Gallery | Product imagery | single, multiple, selected, loading, failed |
| C-29 | Accordion / tabs | Grouped detail | collapsed, expanded, keyboard-operated |
| C-30 | Newsletter form | Subscription | default, invalid, submitting, success, failure |
| C-31 | Footer | Site-wide destinations | full, reduced |
| C-32 | Breadcrumb | Location context | present, root |

---

## 8. Interaction and Control Inventory *(mandatory for UI work)*

Every visible control, its trigger, and its behaviour. **No control may render without defined
behaviour** (Constitution VI.1–VI.3, VI.12).

| Control | Trigger | Defined behaviour | If unavailable, how it is honestly shown |
| --- | --- | --- | --- |
| Logo | Activate | Navigate to home | n/a |
| Nav destination | Activate | Navigate to a real URL | Omitted entirely if no verified content |
| Products dropdown | Activate / arrow keys | Open menu; Escape closes and returns focus | n/a |
| Mobile menu toggle | Activate | Open focus-trapped panel; Escape closes, focus returns | n/a |
| Search | Activate | Open input; submit runs a catalogue search | Disabled with a stated reason if search is unavailable |
| Wishlist (header) | Activate | Navigate to wishlist | Hidden if wishlist is disabled — never inert |
| Wishlist (card / detail) | Activate | Toggle saved state; announce the result | Busy state during the operation |
| Cart (header) | Activate | Navigate to cart; shows a count only when non-zero | n/a |
| Account | Activate | Guest → sign-in; authenticated → account | n/a |
| Skip link | Tab from page start | Move focus to main content | n/a |
| Category card | Activate | Open catalog filtered to that category | n/a |
| Product card / "View" | Activate | Open that product's detail page | n/a |
| Add to Cart | Activate | Add item; update count; announce | **Not rendered** for quote-only products |
| Buy Now | Activate | Add item and go to checkout | **Not rendered** for quote-only products |
| Request Price / Quote | Activate | Open the enquiry form for that product | Rendered **instead of** cart actions when unpriced |
| Quantity − / + / field | Activate / type | Change quantity within limits; revalidate totals | Disabled at min/max with a stated reason |
| Remove item | Activate | Remove line; recompute totals; announce | n/a |
| Filter option | Activate | Apply filter; update URL, count and results | Disabled with count 0 when no matches exist |
| Clear all filters | Activate | Remove all filters; retain search text | Disabled when nothing is applied |
| Remove one filter | Activate | Remove only that filter | n/a |
| Sort | Change | Re-order results; update URL | n/a |
| Pagination | Activate | Change page; update URL; move focus to results | Current page is non-interactive |
| Gallery thumbnail | Activate / arrow keys | Change the main image; announce | Failed image shows the failure state |
| Accordion / tab | Activate / arrow keys | Expand/collapse or switch panel | Omitted when it has no verified content |
| Download | Activate | Download a verified document | **Omitted** when no verified document exists |
| Delivery method | Select | Update delivery choice and totals | Omitted when configuration disables it |
| Installation option | Select | Update the order draft and totals | Omitted when configuration disables it |
| Payment method | Select | Record the chosen method | Shown as unavailable / integration-ready; not completable |
| Place order | Activate | Validate, create exactly one order draft, go to confirmation | Disabled with a stated reason when the cart is invalid |
| Contact / newsletter submit | Activate | Validate, persist, confirm | Recoverable error on failure |
| Sign in / Register / Sign out | Activate | Perform the auth action and return the customer | Field-linked errors on failure |
| Social links (footer) | Activate | Open a verified ZAKEY profile | **Omitted** when no verified profile exists |

**Prohibited**: `href="#"`, dead icons, inert buttons, decorative elements presented as
interactive, fake success, and unexplained disabled controls (FR-011).

---

## 9. Responsive-State Inventory *(mandatory for UI work)*

Derived from measured reference transformations (inventory §3.2). Container: 1344px at 1440,
928px at 1024, fluid with 24px gutters below.

| Surface | 1440px | 1024px | 768px | 390px |
| --- | --- | --- | --- | --- |
| Shell | Inline nav; 4 icon controls; announcement 1 line | **Hamburger**; 4 icon controls | Hamburger; 4 icon controls | Hamburger; **search + cart only**; announcement may wrap to 2 lines |
| Home hero | 2-column split, 64px gap; h1 72px | 2-column, 64px; h1 60px | Single column; h1 48px | Single column; h1 48px |
| Categories | 4 columns, 24px | 4 columns, 24px | 2 columns, 24px | **2 columns**, 24px |
| Best sellers / Featured | 4 columns, 24px | 4 columns, 24px | 2 columns, 24px | **1 column**, 24px |
| Why Choose (6 items) | 3 columns, 32px | 3 columns, 32px | 2 columns, 32px | 1 column, 32px |
| Reviews | Multi-column | Multi-column | 2 columns | 1 column, swipeable without page overflow |
| Newsletter | Inline field + button | Inline | Inline | Stacked, full-width |
| Footer | 5 columns, 48px | 5 columns, 48px | 2 columns | 1 column, collapsible groups |
| Catalog | Persistent sidebar + 3-column grid | Sidebar + **2-column** grid | Filter trigger + 2-column grid | **Filter drawer** + 1 column, **zero overflow** |
| Product details | Gallery + info, 2 columns | 2 columns | Stacked, gallery first | Stacked; thumbnails scroll within bounds |
| Cart | Line items + sticky summary | Same | Summary below items | Stacked; totals reachable without horizontal scroll |
| Checkout | Form + sticky summary | Same | Summary collapses above the form | Single column; summary expandable |
| Account | Side nav + panel | Side nav + panel | Stacked | Stacked; nav collapses |
| Contact | 3 info cards + 2-column form | 3 cards + form | 2 columns | 1 column |

Every row is subject to SC-003 (zero unintended horizontal overflow) and FR-132 (no clipped or
unreachable control).

---

## 10. Loading, Empty, Error, Disabled, and Success States *(mandatory for UI work)*

| Surface | Loading | Empty | Error | Disabled | Success |
| --- | --- | --- | --- | --- | --- |
| Home sections | Skeleton within the section's own footprint | Section omitted entirely when its data is unverified | Section omitted; the rest of the page renders | n/a | n/a |
| Catalog | Result-region skeleton; controls stay operable | "No products available" + route home | Recoverable error + retry; filters preserved | Filters with zero matches | Results announced with count |
| Search | Busy indicator on the field | No-result state naming the query + reset | Recoverable error | Submit disabled while empty | Count announced |
| Product details | Gallery + info skeleton | n/a (404 when absent) | Recoverable error + route to catalog | Cart actions disabled when unavailable | Add-to-cart confirmation announced |
| Cart | Busy row during change | "Your cart is empty" + route to catalog | Field-linked or recoverable error | Checkout disabled with a stated reason | Change announced; totals updated |
| Wishlist | Busy toggle | Empty state + route to catalog | Recoverable error | n/a | Toggle announced |
| Checkout | Busy submit; form locked | n/a (blocked when the cart is empty) | Field-linked validation + recoverable service errors | Place-order disabled with a stated reason | Confirmation states exactly what was recorded |
| Account | Busy submit | Honest empty order history | Field-linked auth errors | n/a | Sign-in/out announced |
| Contact / newsletter | Busy submit | n/a | Field-linked + recoverable | Submit disabled while invalid | Confirmation announced |

A success state MUST NOT appear unless the operation actually succeeded (Constitution VI.4).

---

## 11. Content and Asset Integrity *(mandatory)*

Full register: `content-asset-provenance.md`.

| Asset or claim | Source | Verified | If unverified |
| --- | --- | --- | --- |
| ZAKEY logos | `static/brand/*`, `static/icons/*`, `reference-imports/spec-012/*` | ✅ | n/a |
| Product media | `product-media-register.v2.json` (49 assets, sha256-pinned) | ✅ | Missing-image state |
| Product names | `curated-launch-catalog.v2.json` `public_display_name` | ✅ | Product not published |
| Categories | Palm Vein Locks, Face Recognition Locks, Handle Locks | ✅ | No other category renders |
| Use-case facets | face-unlock, fingerprint-unlock, app-control, card-and-nfc, video-intercom | ✅ | No other facet renders |
| Specification fields | `source_product_family`, `material`, `finishes_colours`, `power_supply`, `unlock_methods` | ✅ | No other field renders |
| Retail prices | **21/21 `null`**, `commerce_mode: quote_only` | ❌ | Quote-only state (BR-010) |
| 2,190–7,490 EGP | **No source found** | ❌ | Never displayed; development fixture only |
| Ratings, reviews, review counts | none | ❌ | Sections hidden entirely |
| Warranty, stock, awards, certifications, customer totals, uptime, partnerships, media coverage, delivery promises, discount claims | none | ❌ | Never rendered |
| Hotline `19919`, New Cairo | User-authorized 2026-08-01 | ✅ (user) | Centrally configured; no further precision invented |
| Aramex, EgyptAir, EDEX | User-supplied names only | ❌ as partners | Never presented as official partners |

- **FR-111**: Production MUST NOT publish any unverified certification, award, customer total, review total, rating, warranty term, stock level, scarcity message, delivery promise, partnership, media coverage, product specification, compatibility claim, installation claim, or discount claim.
- **FR-112**: Development-only content MUST be isolated from production, identified in data provenance, impossible to publish accidentally, and absent from normal production output.
- **FR-113**: Visible production UI MUST NOT contain `demo`, `placeholder`, `Figma`, `lorem ipsum`, internal notes, or development instructions — in copy, alt text, titles, ARIA labels, user-visible filenames, or metadata.

---

## 12. Arabic-First and Egyptian Market Requirements *(mandatory)*

| Requirement | How this specification satisfies it |
| --- | --- |
| Arabic-first copy natural for Egypt (XX.1) | FR-102 |
| `ar-EG`, RTL, `lang="ar"`, `dir="rtl"` (XX.2) | FR-097 |
| Cairo primary; Poppins for Latin only (XX.3) | FR-098 |
| Centralized `ج.م` formatting (XX.4) | FR-099, BR-001 |
| Consistent number formatting (XX.5) | FR-100, BR-002 |
| VAT 14% via the shared routine (XX.6) | BR-005 |
| 1,500 EGP free-shipping threshold (XX.7) | BR-006 |
| Centralized decimal-safe money (XX.8) | BR-007 |
| Data-driven prices (XX.9) | BR-009 |
| No unverified price as production fact (XX.10) | BR-010, FR-050 |
| All 27 governorates (XX.11) | FR-083 |
| Server-side Egyptian phone validation (XX.12) | FR-084 |
| Detailed address + landmark (XX.13) | FR-085 |
| Configuration-driven same-day delivery, Greater Cairo (XX.14) | FR-086 |
| Configuration-driven installation, Greater Cairo + Alexandria (XX.15) | FR-087 |
| Centrally configurable hotline `19919` + New Cairo (XX.16) | FR-109 |

---

## 13. Payment and Integration Honesty *(mandatory)*

| Integration / method | Status today | Adapter boundary | Honest presentation |
| --- | --- | --- | --- |
| Cash on Delivery | Available when configured | Internal | Selectable; confirmation states an order draft was recorded |
| Vodafone Cash | **No verified integration** | External adapter | Unavailable / integration-ready; not completable |
| e& Cash / Etisalat Cash | **No verified integration** | External adapter | Unavailable / integration-ready |
| CashU | **No verified integration** | External adapter | Unavailable / integration-ready |
| InstaPay transfer | **No verified integration** | External adapter | Unavailable / integration-ready |
| Card installments 6 / 12 months | **Presentation only** | External adapter | Indicative amounts from the authoritative price; no bank arrangement implied |
| Aramex / EgyptAir / EDEX | **No verified partnership** | External adapter | Never shown as official partners |

External providers are reached only through configuration-driven adapter boundaries; provider
specifics never leak into pages or the shared calculation routine (BR-014).

---

## 14. Reference-Fidelity Requirements *(mandatory)*

Full mapping: `reference-fidelity-matrix.md`.

**FR-114**: Every implemented page and shared component MUST be compared against its own grounding
evidence for the same page, state and width (Constitution XIII.8).

- **Pages compared**: Home, Catalog, Product details, Cart, Checkout, Account, About, Contact, plus the shared shell.
- **Widths compared**: 1440, 1024, 768, 390.
- **Acceptance threshold**: a surface passes when, at every ratified width — (a) section order and composition match the matrix entry; (b) container width, grid column count and gap match the measured values in §9 or a recorded deviation; (c) every colour, radius, shadow and type step resolves from the ratified token source; (d) each declared deviation in §3.3 is present and correct; (e) no undeclared visual difference from the evidence remains.
- **Review method**: two documented visual critique-and-correction passes, each recording what was observed and what changed (Constitution XIII.3).

---

## 15. Accessibility Requirements *(mandatory)*

Baseline: **WCAG 2.2 Level AA**. No critical or serious violation may be accepted (FR-129).

| ID | Requirement |
| --- | --- |
| FR-119 | Semantic HTML with one `h1` per page and a correct, gap-free heading order |
| FR-120 | Every interactive element is keyboard-operable; no keyboard trap outside intentional dialogs |
| FR-121 | Every focusable element has a visible focus indicator meeting ≥3:1 against its background |
| FR-122 | Every control has an accessible name in Arabic — explicitly including the icon-only search, account, wishlist and cart controls (corrects RD-02) |
| FR-123 | Text contrast ≥4.5:1 (≥3:1 for large text); meaningful non-text elements ≥3:1. Accent gold `#C9A227` MUST NOT be used for normal-size text on `#FFFFFF` or `#F8F9FB` |
| FR-124 | Dialogs, drawers and the mobile navigation trap focus while open, close on Escape, and return focus to the invoking control |
| FR-125 | Every form field has a programmatically associated label; a placeholder is never the only label (corrects RD-03) |
| FR-126 | Validation errors are programmatically associated with their field and stated in Arabic |
| FR-127 | Dynamic changes — cart count, filter results, status messages, submissions — are announced via an appropriate live region |
| FR-128 | Reduced-motion preferences suppress non-essential motion |
| FR-129 | Automated axe checks plus a manual keyboard pass; zero unresolved critical or serious violations |
| FR-130 | Images carry meaningful Arabic alternative text; decorative images are exposed as decorative |
| FR-131 | Reading order and focus order are correct in RTL for sighted keyboard and screen-reader users |
| FR-132 | Interactive targets ≥24×24 CSS px; ≥44×44 for primary mobile commerce actions |

---

## 16. Performance Budgets *(mandatory)*

| ID | Budget | Target | Measured how |
| --- | --- | --- | --- |
| NFR-001 | Page weight (home, compressed) | ≤ 1,200 KB transferred | Production-mode network trace at 1440px, cold cache |
| NFR-002 | JavaScript payload (any page, compressed) | ≤ 150 KB | Production-mode network trace |
| NFR-003 | Layout stability | Cumulative layout shift ≤ 0.10 | Lab measurement at 1440 and 390 |
| NFR-004 | Largest contentful paint | ≤ 2.5 s on a mid-tier mobile profile | Lab measurement at 390px |
| NFR-005 | Third-party origins in production | **Zero** | Network trace shows no third-party origin |
| NFR-006 | Browser console errors | **Zero**, or each individually justified here | Automatic capture during end-to-end verification |
| NFR-007 | Image delivery | Every catalogue/product image declares intrinsic dimensions or an aspect-ratio reservation | DOM inspection |
| NFR-008 | Font delivery | Cairo self-hosted; no invisible-text period | Network trace + visual check |
| NFR-009 | Budget precedence | No budget may be met by weakening accessibility, content truth, or usability | Review at acceptance |
| NFR-010 | Consistency | Totals and availability rendered on any surface are internally consistent within a request; no surface shows a stale total after a successful change | End-to-end assertion |

---

## 17. Requirements *(mandatory)*

### 17.1 Business rules

| ID | Rule |
| --- | --- |
| BR-001 | All money is displayed in Egyptian pounds using the visible form `ج.م`, produced by exactly one centralized formatter |
| BR-002 | Number formatting is decided once and applied through the same centralized layer on every surface |
| BR-003 | Subtotal = Σ(unit price × quantity) over purchasable line items only |
| BR-004 | A discount, when present, derives from a verified configured source; no invented discount may be shown |
| BR-005 | VAT = 14% of the taxable base, applied by one shared, tested routine |
| BR-006 | Shipping is free when the subtotal is ≥ **1,500 EGP**; otherwise the configured shipping charge applies. The shortfall to free shipping is stated when applicable |
| BR-007 | All monetary values use a decimal representation with explicit, centralized rounding. Binary floating point is prohibited for money |
| BR-008 | Grand total = subtotal − discount + shipping + VAT. This identity MUST hold exactly on cart, checkout, review and confirmation |
| BR-009 | Prices are data-driven; no price may be hard-coded in a page |
| BR-010 | A product is **purchasable** only when it has a verified retail price **and** is configured purchasable. Otherwise it is **quote-only**: no price, no cart action; Request Price / Request Quote instead. *Verified today: 21 of 21 approved products are quote-only* |
| BR-011 | Installment amounts derive from the same authoritative price as every other surface |
| BR-012 | Availability shown to customers derives from verified data; when availability is unknown it is not asserted |
| BR-013 | Raw card data is never collected, transmitted, logged, or stored |
| BR-014 | Provider credentials and availability come from validated environment configuration, behind adapter boundaries |
| BR-015 | An order draft is a record of intent, never a claim of payment or fulfilment |
| BR-016 | Same-day delivery and installation are configuration-driven and are absent everywhere when disabled |

### 17.2 Functional requirements

**Shared shell**

- **FR-001**: The announcement bar renders only when a message is configured, is dismissible per session, and never obscures the header.
- **FR-002**: The header is sticky, 73px tall, `#FFFFFF`, and remains above page content at every width.
- **FR-003**: The verified ZAKEY logo renders navy on light surfaces and white on navy surfaces, and routes to home.
- **FR-004**: Primary navigation exposes Home, Shop, About and Contact plus a category menu, each as a real URL.
- **FR-005**: At ≤1024px navigation collapses into a menu control that opens a focus-trapped panel.
- **FR-006**: Search opens an input that submits to a search-results URL.
- **FR-007**: The wishlist control navigates to the wishlist, or is hidden when wishlist is disabled — never inert.
- **FR-008**: The cart control navigates to the cart and displays an item count only when non-zero.
- **FR-009**: The account control routes guests to sign-in and authenticated customers to their account.
- **FR-010**: A skip link is the first focusable element and moves focus to main content.
- **FR-011**: No `href="#"`, dead icon, inert button, decorative element presented as interactive, fake success state, or unexplained disabled control exists in the accepted interface.
- **FR-012**: The footer exposes only destinations with verified content, plus the newsletter and configured contact information.
- **FR-013**: Footer destinations with no verified content (Careers, Press, Blog, Help Center, Warranty, Returns, Partners) are omitted entirely.
- **FR-014**: The newsletter accepts an email address, validates it server-side, and reports truthful success or failure.
- **FR-015**: Every internal destination uses a named route lookup; hardcoded internal paths are prohibited.

**Home**

- **FR-016**: Home renders in this exact order: Announcement Bar, Header, Hero, Shop by Category, Best Sellers, Featured Products, Why Choose ZAKEY, Smart Home Solutions, Customer Reviews, Brand Partners, Newsletter, Footer.
- **FR-017**: The hero presents a verified premium ZAKEY smart-lock image from the media register, with an Arabic headline and subheadline and at least one working primary action.
- **FR-018**: The hero MUST NOT display invented statistics (homes protected, uptime, ratings, awards).
- **FR-019**: Shop by Category renders only approved categories, each routing to the catalog pre-filtered to that category.
- **FR-020**: Category counts, when shown, are computed from real catalogue data; otherwise omitted.
- **FR-021**: Best Sellers renders only from a verified, configured selection; if none exists the section is omitted.
- **FR-022**: Featured Products renders only from a verified, configured selection; if none exists the section is omitted.
- **FR-023**: Why Choose ZAKEY presents only truthful, product-relevant propositions with no invented certification, award, or guarantee.
- **FR-024**: Smart Home Solutions presents only verified compatibility and capability claims.
- **FR-025**: Customer Reviews is data-driven; each review traces to a verified source.
- **FR-026**: When no verified review exists, the Customer Reviews section does not render at all.
- **FR-027**: Brand Partners is data-driven; each logo traces to a verified, authorized relationship.
- **FR-028**: When no verified partner exists, the Brand Partners section does not render at all.
- **FR-029**: Every home section defines its loading, empty and unavailable behaviour per §10.
- **FR-030**: Home renders per §9 at all four ratified widths with zero unintended horizontal overflow.
- **FR-031**: Every home image preserves its source aspect ratio (4:5 category, 1:1 product) and is never stretched or degraded.
- **FR-032**: No home section may render a control that leads nowhere.

**Catalog**

- **FR-033**: The catalog lists published products with a truthful result count.
- **FR-034**: Category filters offer only approved categories.
- **FR-035**: Use-case filters offer only the approved facet vocabulary.
- **FR-036**: Availability filters reflect verified availability only.
- **FR-037**: A price filter renders **only** when at least one product in scope has a verified price; otherwise it is omitted.
- **FR-038**: The result count always matches the number of results actually rendered under the active criteria.
- **FR-039**: Filters combine additively; applying one never silently discards another.
- **FR-040**: Search text, filters, sort and pagination combine without any one silently discarding another.
- **FR-041**: The complete result state — search text, filters, sort, page — is encoded in a shareable URL that restores identically in a clean session.
- **FR-042**: An individual filter can be removed without affecting the rest of the state.
- **FR-043**: Clear-all removes every filter while retaining search text, and is disabled when nothing is applied.
- **FR-044**: When the catalogue is empty or unavailable, an empty state renders with a working route onward.
- **FR-045**: When criteria match nothing, a no-result state states the active criteria and offers a working reset.
- **FR-046**: At ≤768px filters present in a focus-trapped drawer that returns focus to its trigger on dismissal.
- **FR-047**: Pagination exposes the current page non-interactively and moves focus to the results region on change.
- **FR-048**: The catalog exhibits **zero** horizontal overflow at all four widths (corrects RD-05).

**Product card**

- **FR-049**: A single card contract is used everywhere a product appears.
- **FR-050**: A priced product shows its price; a quote-only product shows no price and exposes Request Price instead of cart actions.
- **FR-051**: A was/now price renders only when both values are verified.
- **FR-052**: Installment presentation renders only when configured and derives from the authoritative price.
- **FR-053**: Availability renders only when verified.
- **FR-054**: The card exposes the wishlist state and routes to the product's detail page.
- **FR-055**: When required media is missing, the defined missing-image state renders; no other product's image is substituted.
- **FR-056**: The card defines hover, focus, loading and error behaviour, and its responsive anatomy per §9.

**Product details**

- **FR-057**: The gallery presents verified media with keyboard-operable selection and defined loading and failure states.
- **FR-058**: Only the approved specification fields render; no other field is displayed.
- **FR-059**: Product identity uses the verified `public_display_name`; ZAKEY manufacture is never implied for supplier-branded products.
- **FR-060**: An unverified attribute is absent, not rendered as an empty or placeholder value.
- **FR-061**: Priced products expose quantity, Add to Cart and Buy Now; quote-only products expose Request Price / Request Quote.
- **FR-062**: Downloads render only when a verified document exists.
- **FR-063**: Reviews and FAQ render only from verified data; otherwise they are omitted.
- **FR-064**: Submitting an enquiry persists a real record and confirms only what actually happened.
- **FR-065**: Enquiry validation is server-side with field-linked Arabic errors and preserved input.
- **FR-066**: When the enquiry service fails, a recoverable error renders, no success is claimed, and input is preserved.
- **FR-067**: Related products come from verified catalogue relationships, or the section is omitted.
- **FR-068**: Tabs and accordions are keyboard-operable and expose their expanded state.
- **FR-069**: A product that does not exist returns the not-found state with a route to the catalog.
- **FR-070**: The page defines its loading, unavailable and incomplete-content states.

**Cart and wishlist**

- **FR-071**: Adding a purchasable product updates the cart and the header count, and announces the change.
- **FR-072**: Removing a line recomputes totals immediately and announces the change.
- **FR-073**: Quantity changes are validated server-side against configured minimum and maximum; invalid values are rejected with a field-linked error and the previous value retained.
- **FR-074**: The cart displays subtotal, discount (when verified), shipping, VAT and grand total per BR-003–BR-008, and states the shortfall to free shipping when applicable.
- **FR-075**: The cart empty state renders with a working route to the catalog.
- **FR-076**: Cart contents persist across reloads within a session.
- **FR-077**: The header cart count matches the cart contents at all times.
- **FR-078**: An item that becomes unavailable is marked, excluded from totals, and blocks checkout with a stated reason.
- **FR-079**: A price change between cart and checkout is surfaced explicitly and must be acknowledged before an order draft is created.
- **FR-080**: Wishlist supports adding, removing, an empty state, a count where displayed, and moving an item to the cart when that item is purchasable.

**Checkout**

- **FR-081**: Checkout collects customer name and contact details with server-side validation.
- **FR-082**: An email address is collected where required by the chosen contact or delivery path.
- **FR-083**: The governorate selector offers **all 27** Egyptian governorates.
- **FR-084**: Egyptian mobile numbers are validated server-side; invalid values are rejected with a field-linked Arabic error.
- **FR-085**: Detailed address and landmark fields are collected, with Arabic guidance.
- **FR-086**: Same-day delivery in Greater Cairo is offered only when configuration enables it and the address is eligible; eligibility feedback is honest.
- **FR-087**: Installation service in Greater Cairo and Alexandria is offered only when configuration enables it; otherwise it is absent everywhere.
- **FR-088**: Installment presentation derives from the authoritative price.
- **FR-089**: Unconfigured payment methods render as unavailable or integration-ready and cannot be completed.
- **FR-090**: No raw card data is collected, transmitted, logged, or stored.
- **FR-091**: Duplicate submission produces exactly one order draft.
- **FR-092**: Confirmation states only what actually happened and claims no settlement, carrier booking, or delivery date.
- **FR-093**: An order summary is presented for review before submission, with every figure consistent with the cart.
- **FR-094**: Validation failures return the customer to the offending field with all other input preserved.
- **FR-095**: Checkout is blocked with a stated reason when the cart is empty or contains a non-purchasable item.
- **FR-096**: The order draft is persisted and retrievable by reference for follow-up.

**Localization**

- **FR-097**: The document declares `lang="ar"` and `dir="rtl"`.
- **FR-098**: Cairo is the primary typeface; Poppins is used only for Latin content.
- **FR-099**: All money renders via the single centralized `ج.م` formatter (BR-001).
- **FR-100**: All numbers render via the single centralized formatter (BR-002).
- **FR-101**: Mixed Arabic/Latin strings (for example model codes "A06", "MR6") render in correct bidirectional order at every width.
- **FR-102**: All customer copy is natural Egyptian Arabic; machine-literal phrasing that reads as translated is a defect.

**Account**

- **FR-103**: Registration validates input server-side and reports field-linked Arabic errors.
- **FR-104**: Sign-in errors do not reveal whether an account exists.
- **FR-105**: After authenticating, the customer returns to the exact intended destination.
- **FR-106**: Order history renders an honest empty state; no order, status, or membership tier is invented.
- **FR-107**: Sign-out terminates the session and makes member-only surfaces unreachable.

**About and Contact**

- **FR-108**: About presents only verified, product-relevant content; no invented history, awards, certifications, staff or customer numbers.
- **FR-109**: Contact presents hotline `19919` and the New Cairo location from central configuration, with no invented precision.
- **FR-110**: The contact form collects name, contact detail, subject and message; validates server-side; persists a real record; and confirms truthfully.
- **FR-115**: Abuse and automated-submission mitigation applies to every public form without revealing the detection rule.

**Content integrity** — FR-111, FR-112, FR-113 (see §11). **Reference fidelity** — FR-114 (see §14).
**Accessibility** — FR-119–FR-132 (see §15).

**Security, privacy, failure and recovery**

- **FR-116**: Every state-changing request is CSRF-protected.
- **FR-117**: All input is validated server-side; client-side validation is assistance only.
- **FR-118**: Output is escaped; untrusted content is never rendered unescaped.
- **FR-133**: Redirect targets are validated against an allowlist.
- **FR-134**: Secrets and credentials come from validated environment configuration; none are committed.
- **FR-135**: Personal data is never exposed through URLs, enumerable identifiers, or error output.
- **FR-136**: Logs never contain passwords, payment credentials, session secrets, or unnecessary personal data.
- **FR-137**: Every validation failure is recoverable with input preserved.
- **FR-138**: Every service failure renders a recoverable state that claims no success.
- **FR-139**: A not-found state offers a working route onward.
- **FR-140**: Authentication errors are uniform and non-enumerating.
- **FR-141**: Session expiry mid-journey preserves safe data and returns the customer to the correct step.
- **FR-142**: No failure path may present a success state.

### 17.3 Key entities

| Entity | Represents |
| --- | --- |
| Product | A verified catalogue item: display name, summary, type, category, use-case facets, approved specification fields, media assignments, commerce mode, optional verified price, availability |
| Category | One of three approved categories |
| Media asset | A registered, sha256-pinned image with role and sort order |
| Cart / cart line | A session-scoped intent to purchase priced products |
| Wishlist entry | A saved product reference |
| Order draft | A persisted record of intent: customer, address, delivery choice, chosen payment method, line items, computed totals, reference |
| Enquiry | A persisted price/quote request against a product |
| Contact message | A persisted general enquiry |
| Customer account | Authenticated identity with profile and saved details |
| Governorate | One of 27 Egyptian governorates |
| Storefront configuration | Hotline, location, delivery/installation availability, payment-method availability, shipping charge, VAT rate, free-shipping threshold |

### 17.4 Non-functional requirements

See §16 (NFR-001 – NFR-010).

### 17.5 Open questions

Neither blocks planning; both carry a specified default.

- **OQ-01 (governance)**: The reference's dominant corner radius is **16px** (65 occurrences) while
  the Constitution ratifies **12px** (11 occurrences observed). Under the v2.0.1 re-verification
  rule this is a defect report requiring an amendment, not a unilateral change.
  **Default until amended**: the ratified 12px is used.
- **OQ-02 (content)**: No verified retail price exists for any approved product.
  **Default**: the entire catalogue operates quote-only (BR-010); the priced journey is fully
  specified and activates per product the moment a verified price is supplied.

---

## 18. Success Criteria *(mandatory)*

| ID | Criterion |
| --- | --- |
| SC-001 | A guest can go from the home page to a product detail page in no more than 3 interactions at every ratified width |
| SC-002 | 100% of rendered business facts trace to an entry in `content-asset-provenance.md` marked VERIFIED or USER-AUTHORIZED |
| SC-003 | Zero unintended horizontal overflow at 1440, 1024, 768 and 390 on every in-scope page and material state |
| SC-004 | Zero unresolved critical or serious accessibility violations across all in-scope pages and interactive states |
| SC-005 | 100% of visible controls perform their defined action or are visibly and honestly unavailable; zero dead controls |
| SC-006 | Zero occurrences of `href="#"` in the accepted interface |
| SC-007 | The grand-total identity (BR-008) holds on cart, checkout, review and confirmation for every tested basket |
| SC-008 | VAT equals 14% of the taxable base in 100% of tested baskets |
| SC-009 | Free shipping applies in 100% of baskets with subtotal ≥ 1,500 EGP and in none below it |
| SC-010 | 100% of monetary values render through the single `ج.م` formatter; zero surfaces format money independently |
| SC-011 | All 27 Egyptian governorates are selectable |
| SC-012 | 100% of invalid Egyptian mobile numbers are rejected server-side with a field-linked error |
| SC-013 | Every in-scope page declares `lang="ar"` and `dir="rtl"` |
| SC-014 | A keyboard-only user can complete the discovery, enquiry, cart and checkout journeys without a pointer |
| SC-015 | Every dialog, drawer and mobile menu traps focus and returns it to its trigger on dismissal |
| SC-016 | Zero unexpected browser-console errors, or each individually justified in §16 |
| SC-017 | A copied catalogue URL restores identical filters, sort, page and results in a clean session in 100% of tested combinations |
| SC-018 | Zero products without a verified price display a price or a cart action |
| SC-019 | Zero payment methods without verified credentials can be completed |
| SC-020 | Duplicate checkout submission produces exactly one order draft in 100% of tested attempts |
| SC-021 | Zero occurrences of `demo`, `placeholder`, `Figma`, or `lorem ipsum` in visible production output |
| SC-022 | Every in-scope page has inspected screenshots at all four ratified widths, with recorded observations |

---

## 19. Assumptions *(mandatory)*

1. The reference remains the approved visual authority; the client rejected the previous implementation, not the reference (recorded 2026-08-01 in Constitution v2.0.1).
2. Verified content at launch is the 21-product curated catalogue with three approved categories.
3. All products are quote-only until a verified price is supplied; the priced journey is dormant, not absent.
4. Hotline `19919` and the New Cairo location are user-authorized; no more precise address exists.
5. Reviews, ratings and partner relationships have no verified source at launch and therefore do not render.
6. Same-day delivery, installation, and every external payment method default to unavailable until configuration and verified credentials exist.
7. "Order draft" is the commercial milestone; settlement and fulfilment are out of scope.
8. Arabic copy is authored or reviewed by an Egyptian Arabic speaker; machine-literal phrasing is a defect, not an acceptable default.
9. The 2,190–7,490 EGP figure is a planning hint with no verified source and is never displayed.
10. Product media coverage per role is confirmed during planning, not assumed here.

---

## 20. Dependencies *(mandatory)*

| Dependency | Blocked if unavailable |
| --- | --- |
| Curated catalogue + media register (legacy, read-only) | No catalogue can render |
| Verified ZAKEY logo assets | The shell cannot render brand identity |
| Cairo font files, self-hosted | Arabic typography cannot meet the ratified token |
| Egyptian Arabic copy authoring/review | Copy quality cannot meet FR-102 |
| Storefront configuration (hotline, location, VAT, threshold, shipping charge, availability flags) | Money rules and contact surfaces cannot render truthfully |
| Verified retail prices | The priced journey stays dormant; quote-only continues |
| Verified payment credentials | All external methods stay unavailable/integration-ready |
| Verified review/partner data | Those sections stay hidden |

---

## 21. Repository Readiness Preconditions *(mandatory)*

| # | Finding | Verified | Severity | Resolve before |
| --- | --- | --- | --- | --- |
| RP-01 | Branch `002-egypt-premium-storefront` is current | ✅ 2026-08-01 | Info | — |
| RP-02 | Constitution is v2.0.1 with no open blocker | ✅ | Info | — |
| RP-03 | Automatic Spec Kit Git hooks are disabled (`auto_execute_hooks: false`; all 18 entries `enabled: false`) | ✅ | Info | — |
| RP-04 | `.specify/feature.json` targets only `specs/002-egypt-premium-storefront` | ✅ | Info | — |
| RP-05 | No Feature 001 artifact exists in the working tree | ✅ | Info | — |
| RP-06 | Legacy repository remains read-only and unmodified | ✅ | Blocking if violated | Any legacy access |
| RP-07 | About and Contact lack 768/390 grounding evidence; My Account lacks 390 | ✅ (declared) | Medium | Implementation of those pages — capture before building them |
| RP-08 | Corner-radius conflict OQ-01 unresolved | ✅ | Medium | Global token definition during planning |

---

## 22. Explicit Out of Scope *(mandatory)*

| Capability | Owning future specification |
| --- | --- |
| Payment settlement / gateway execution | Future payment-integration specification |
| Carrier integration, live rates, tracking | Future logistics specification |
| Admin console / catalogue management UI | Future admin specification |
| Order fulfilment, invoicing, returns processing | Future operations specification |
| Loyalty, membership tiers, promotions engine | Not planned |
| Multi-language / language selector | Not approved (Constitution IV.9) |
| Dark mode | Prohibited (Constitution II.10) |
| Blog, careers, press, editorial | Excluded — would require invented content |
| Live chat | Excluded — no backing capability (corrects RD-16) |
| Product comparison, advanced merchandising | Not planned |
| Customer-visible stock counts | Excluded — no verified stock data |

None of these may render a control in the accepted interface (Constitution VI.2).

---

## 23. Constitution Compliance *(mandatory)*

| Principle | How this specification complies |
| --- | --- |
| I Reference-led fidelity | §3, §14; deviations in §3.3 each carry a permitted basis |
| II Brand system | Ratified tokens confirmed present in the live reference (inventory §1); §9 geometry; OQ-01 raised rather than resolved unilaterally |
| III Technical foundation | No stack choice made beyond ratified constraints; NFR-005 forbids third-party origins |
| IV Clean-room architecture | Clean-room rebuild; no legacy frontend reused; §7 defines single-definition shared components |
| IV.9 Arabic-first RTL | FR-097, FR-101, FR-131; no language selector |
| V Content and asset integrity | §11, `content-asset-provenance.md`, FR-111–FR-113 |
| VI Functional completeness | §8; FR-011; BR-010; FR-092 |
| VII Responsive design | §9; FR-048; SC-003; decisions made here, not deferred to CSS |
| VIII Accessibility | §15; SC-004, SC-014, SC-015 |
| IX Performance | §16 budgets set before implementation |
| X Security and privacy | FR-116–FR-118, FR-133–FR-136 |
| XI Specification-first | This document precedes planning; §22 bounds scope; open questions carry defaults |
| XII Test-first acceptance | Every FR/BR is observable; §18 criteria are measurable |
| XIII Visual QA | §14 requires two documented critique passes and comparison against §3 evidence |
| XIV Code quality | Not prescribed here; deferred to planning as required |
| XV Git safety | No Git write performed; §21 records the state |
| XVI Lead-agent governance | Active lead named in the header |
| XVII LeanCTX and context discipline | All decisions and evidence written into these artifacts, not left in conversation |
| XVIII Definition of Done | §18 plus the requirements checklist make all twenty conditions reachable |
| XIX Visual grounding gate | §3, `visual-reference-inventory.md`, `reference-fidelity-matrix.md`; gaps declared, not hidden |
| XX Egyptian market | §12; BR-001–BR-011; FR-083–FR-087 |
| XXI Payment and integration honesty | §13; FR-088–FR-092; BR-013–BR-015 |

---

## 24. Requirement-to-Success-Criterion Traceability *(mandatory)*

| Requirements | Mapped to |
| --- | --- |
| FR-001–FR-015 (shell) | SC-001, SC-005, SC-006, SC-013, SC-014, SC-022 |
| FR-016–FR-032 (home) | SC-001, SC-002, SC-003, SC-005, SC-022 |
| FR-033–FR-048 (catalog) | SC-001, SC-003, SC-005, SC-017, SC-022 |
| FR-049–FR-056 (product card) | SC-002, SC-005, SC-018 |
| FR-057–FR-070 (product details) | SC-001, SC-002, SC-005, SC-018 |
| FR-071–FR-080 (cart / wishlist) | SC-007, SC-008, SC-009, SC-010, SC-014 |
| FR-081–FR-096 (checkout) | SC-007–SC-012, SC-014, SC-019, SC-020 |
| FR-097–FR-102 (localization) | SC-010, SC-011, SC-013 |
| FR-103–FR-107 (account) | SC-005, SC-014 |
| FR-108–FR-110, FR-115 (about / contact / abuse) | SC-002, SC-005 |
| FR-111–FR-113 (content integrity) | SC-002, SC-018, SC-021 |
| FR-114 (reference fidelity) | SC-022 |
| FR-116–FR-118, FR-133–FR-142 (security, failure, recovery) | SC-005, SC-016, SC-019, SC-020 |
| FR-119–FR-132 (accessibility) | SC-003, SC-004, SC-014, SC-015 |
| BR-001–BR-016 | SC-007–SC-011, SC-018, SC-019 |
| NFR-001–NFR-010 | SC-003, SC-016 |

**Coverage**: 142 functional requirements (FR-001–FR-142), 16 business rules (BR-001–BR-016) and 10
non-functional requirements (NFR-001–NFR-010) — **all mapped**. 22 success criteria
(SC-001–SC-022), **all reachable** from at least one requirement. Zero unmapped requirements.

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
6. **Given** a product card renders, **When** the design calls for a category label, **Then** the verified approved category is shown; where category data is unavailable the label is hidden rather than filled with placeholder text, and no invented category is ever substituted (FR-155).
7. **Given** a product whose verified evidence contains an approved public model code, **When** the detail page renders, **Then** that identifier is displayed, and a Latin code inside Arabic text renders in correct bidirectional order at all four widths (FR-156, FR-101).
8. **Given** a product with no verified public identifier, **When** the detail page renders, **Then** the identifier field is omitted entirely — not rendered blank, and never populated from an internal identifier (FR-156).

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
6. **Given** the catalog, **When** the filter panel renders, **Then** it offers verified-feature and access-method facets whose options are exactly the distinct verified values present in the catalogue, and any facet with zero verified values is omitted entirely rather than shown empty (FR-148, FR-149, FR-150).
7. **Given** a guest applies an access-method filter, **When** results render, **Then** every returned product carries that value in its verified `unlock_methods` evidence, and the option set contains nothing that is not present in that evidence (FR-149, SC-027).
8. **Given** no search query is active, **When** the catalog loads, **Then** the deterministic default order applies; repeating the identical request returns the identical order, including across page boundaries (FR-151, FR-152, SC-028).
9. **Given** a result set containing both priced and quote-only products, **When** the guest sorts by price ascending, **Then** priced products order by price, quote-only products appear after them in a clearly labelled non-priced group retaining Request Price, and no quote-only product displays or is ordered by an implied price (FR-153, SC-028).
10. **Given** the active result set contains no product with a verified price, **When** the sort control renders, **Then** price ascending and descending are not offered (FR-151).
11. **Given** a guest sorts and filters, **When** the URL is copied and opened in a clean session, **Then** the same sort, filters, search text and page are restored (FR-154, SC-017).

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
9. **Given** Example A (subtotal 1,200.00, shipping 60.00 taxable, no discount), **When** totals render, **Then** taxable base is 1,260.00, VAT is 176.40, grand total is **1,436.40**, and a 300.00 shortfall to free shipping is stated — identically on Cart, Checkout, Review and Confirmation (FR-143, FR-144, SC-023).
10. **Given** Example B (subtotal exactly 1,500.00), **When** totals render, **Then** free shipping applies, shipping is 0.00, VAT is 210.00 and grand total is **1,710.00** — proving the threshold is inclusive (BR-006, SC-024).
11. **Given** Example C (subtotal 1,607.77, verified discount 200.00), **When** totals render, **Then** free shipping is retained even though the post-discount amount 1,407.77 is below the threshold, the taxable base is 1,407.77, VAT rounds once from 197.0878 to **197.09**, and grand total is **1,604.86** (BR-006, BR-017, BR-018, SC-024, SC-025).
12. **Given** any basket, **When** a surface renders totals, **Then** it renders the computed result without recomputing, and no intermediate value is rounded before VAT (BR-018, BR-019, FR-143).

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
6. **Given** the address step, **When** it renders, **Then** a **city or area** field distinct from the governorate is present and required, and the governorate list shows exactly the 27 §12.1 values with those exact Arabic labels (FR-145, FR-146, SC-026).
7. **Given** a customer selects الدقهلية, **When** they enter المنصورة as city/area, **Then** the value is accepted naturally without being forced into a Cairo-centric list, and المنصورة never appears in the governorate register (FR-145, §12.1).
8. **Given** a customer in any governorate outside Greater Cairo and Alexandria, **When** the address step renders, **Then** they can still submit a valid city/area and are not treated as unserviceable at the address step (FR-145).
9. **Given** configuration cannot determine eligibility for the submitted governorate and city/area, **When** delivery options render, **Then** the option is not offered and no delivery promise is made — eligibility is never inferred from the governorate alone (FR-147).
10. **Given** a submission fails validation on any address field, **When** errors render, **Then** each error is programmatically linked to its field in Arabic and every other entered value is preserved (FR-094, FR-126, FR-137).

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
5. **Given** an authenticated customer opens their profile, **When** it renders, **Then** their basic profile information is shown and the approved fields are editable; saving a valid change persists it and reports truthful success (FR-157).
6. **Given** an authenticated customer submits an invalid profile change, **When** it is rejected server-side, **Then** the error is field-linked in Arabic, every other entered value is preserved, and no success is claimed (FR-157, FR-137).
7. **Given** a customer has approved saved contact or address details, **When** they return to checkout, **Then** those details are available for reuse, are editable and removable by their owner, and are never pre-filled from another customer's data (FR-158).
8. **Given** an authenticated customer manipulates an identifier in a URL or request, **When** the target belongs to another customer, **Then** no other customer's data is exposed and the response does not reveal whether the target exists (FR-159, FR-135).

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
| Feature filter option | Activate | Apply a verified-feature facet; update URL, count and results | Facet omitted entirely when it has zero verified values (FR-150) |
| Access-method filter option | Activate | Apply an `unlock_methods` facet value | Facet omitted when the catalogue holds no verified value |
| Sort option | Select | Apply one of the FR-151 sorts; update URL; preserve search and filters | Price sorts not offered when no result has a verified price |
| Governorate selector | Select | Set the governorate from the 27-value register | Never omitted; no governorate is disabled |
| City / area field | Type | Capture the locality in free Arabic text | Required; field-linked Arabic error when empty or invalid |
| Profile field | Type / save | Update an approved profile field; persist and confirm truthfully | Disabled with a stated reason when the field is not owner-editable |
| Saved detail (use / edit / remove) | Activate | Reuse, edit, or remove the customer's own saved contact or address | Absent when the customer has no approved saved details |

**Prohibited**: `href="#"`, dead icons, inert buttons, decorative elements presented as
interactive, fake success, and unexplained disabled controls (FR-011).

---

## 9. Responsive-State Inventory *(mandatory for UI work)*

Derived from measured reference transformations (inventory §3.2). Container: 1344px at 1440,
928px at 1024, fluid with 24px gutters below.

Grounding class per row: **D** = DIRECT (own evidence at that width), **A** = ADAPTATION (composed
from the named inspected components — see `reference-fidelity-matrix.md`). No row claims DIRECT for
a width without its own evidence.

### 9.1 Shared shell and overlays

| Surface / state | 1440px | 1024px | 768px | 390px | Class |
| --- | --- | --- | --- | --- | --- |
| Header shell | 73px sticky; inline nav; 4 icon controls; container 1344 | 73px sticky; **hamburger**; 4 icons; container 928 | 73px sticky; hamburger; 4 icons; fluid 720 | 73px sticky; hamburger; **search + cart only**; fluid 342 | D |
| Announcement bar | 40px, 1 line | 40px, 1 line | 40px, 1 line | **60px**, wraps to 2 lines | D |
| Mobile navigation panel | Not rendered | Full-width panel below header, focus-trapped, Escape closes, focus returns | Same | Same | D (structure) / A (focus trap) |
| Filter drawer | Not rendered — persistent sidebar | Not rendered — persistent sidebar | Edge-anchored drawer over content, focus-trapped | Full-width drawer, focus-trapped, sticky Apply/Clear footer | A |
| Dialogs / drawers | Centred, max-width 640, backdrop | Centred, max-width 640 | Inset 24px | Full-bleed sheet, ≥44px close target | A |
| Search input / open state | Inline expanding bar in header, full container width | Same | Same | Full-width row **below** the header; results list stacks | D |
| Footer | 5 columns, 48px gap | 5 columns, 48px gap | 2 columns | 1 column, collapsible groups | D |

### 9.2 Home sections

| Section | 1440px | 1024px | 768px | 390px | Class |
| --- | --- | --- | --- | --- | --- |
| Hero | 2-column split, 64px gap; h1 72/79.2px | 2-column, 64px; h1 60/66px | Single column; h1 48/52.8px | Single column; h1 48/52.8px | D |
| Shop by Category | 4 cols, 24px; image 4:5 | 4 cols, 24px | 2 cols, 24px | **2 cols**, 24px | D |
| Best Sellers | 4 cols, 24px; image 1:1 | 4 cols, 24px | 2 cols, 24px | **1 col**, 24px | D |
| Featured Products | 4 cols, 24px | 4 cols, 24px | 2 cols, 24px | 1 col, 24px | D |
| Why Choose ZAKEY (6) | 3 cols, 32px | 3 cols, 32px | 2 cols, 32px | 1 col, 32px | D |
| **Smart Home Solutions** | 2-column split (media + claims), 64px gap; media 1:1 | 2-column, 64px | Single column, media first | Single column, media first, full-bleed width | D |
| Customer Reviews | Multi-column band on navy | Multi-column | 2 cols | 1 col, horizontally swipeable **within** bounds — no page overflow | D |
| Brand Partners | Single horizontal strip | Single strip | Wrapped rows | 1–2 marks per row, wrapped | D |
| Newsletter | Inline field 317×50 + button 119×50 | Inline | Inline | Stacked, both full-width, ≥44px targets | D |

### 9.3 Catalogue and product

| Surface / state | 1440px | 1024px | 768px | 390px | Class |
| --- | --- | --- | --- | --- | --- |
| Catalog results | Persistent sidebar + **3-col** grid, 24px | Sidebar + **2-col** grid, 24px | Filter trigger + 2-col grid | Filter drawer + **1 col**; **zero overflow** (corrects RD-05) | D |
| Catalog zero-result | Sidebar retained; message occupies the results region | Same | Full-width message below trigger | Full-width message; drawer trigger stays reachable | A |
| Product gallery | Main image + vertical thumbnail rail beside it | Same | Main image + horizontal thumbnail row beneath | Main image full-bleed + horizontal thumbnails scrolling **within** bounds | A |
| Product details | Gallery + info, 2 cols | 2 cols | Stacked, gallery first | Stacked; actions reachable without horizontal scroll | A |
| Product card | 316×316 image, badge, name, category, price/quote block | Same | Same anatomy, 2-up | Same anatomy, 1-up, ≥44px primary action | D |

### 9.4 Commerce and account

| Surface / state | 1440px | 1024px | 768px | 390px | Class |
| --- | --- | --- | --- | --- | --- |
| Cart — empty | Centred message + primary action within container | Same | Same | Same, full-width action | D |
| Cart — populated | Line items + **sticky** summary column | Same | Summary below items | Stacked; totals reachable without horizontal scroll | A |
| Wishlist — empty | Centred message + route to catalog | Same | Same | Same | A |
| Wishlist — populated | 3-col grid, 24px | 2-col grid | 2-col grid | 1 col | A |
| Checkout — information | Form + sticky summary | Same | Summary collapses above the form | Single column; summary expandable, collapsed by default | A |
| Checkout — review | Two columns: entered details + totals | Same | Stacked, details first | Stacked; every figure visible without horizontal scroll | A |
| Checkout — validation | Errors inline; page scrolls to first invalid field | Same | Same | Same; error text never truncated | A |
| Checkout — confirmation | Centred confirmation + reference + summary | Same | Same | Single column; reference selectable | A |
| Account — sign in / register | Centred single-column form, max-width 480 | Same | Same | Full-width form, ≥44px submit | A |
| Account — profile | Side nav + panel | Side nav + panel | Stacked, nav above | Stacked; nav collapses to a list | A |
| Account — empty orders | Side nav + centred empty state | Same | Stacked | Stacked, full-width | A |

### 9.5 Content and error surfaces

| Surface / state | 1440px | 1024px | 768px | 390px | Class |
| --- | --- | --- | --- | --- | --- |
| About | Eyebrow + 2-line heading; 4-col supporting grid | 4-col grid | 2 cols | 1 col | D (1440/1024) · A (768/390) |
| Contact | 3 info cards, 32px + 2-col form, 20px | 3 cards + form | 2 cols | 1 col; hotline is a ≥44px tap target | D (1440/1024) · A (768/390) |
| Search results | Results region matches catalog grid, 3 cols | 2 cols | 2 cols | 1 col | A |
| 404 | Centred message + route onward within container | Same | Same | Full-width, action ≥44px | A |
| 5xx recoverable | Centred message + retry action | Same | Same | Full-width, retry ≥44px | A |

Every row is subject to SC-003 (zero unintended horizontal overflow) and FR-132 (no clipped or
unreachable control). No row may be satisfied by "responsive", "stacked as needed", or
"mobile-friendly" — each states a concrete observable transformation.

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
| Search results | Busy indicator on the results region | No-result state naming the query + working reset | Recoverable error + retry; query preserved | n/a | Result count announced |
| Not found (404) | n/a | The state itself | Route onward always works | n/a | n/a |
| Server error (5xx) | n/a | n/a | Recoverable message + retry; claims no success | Retry disabled while in flight | n/a |
| Product gallery | Placeholder occupying the image's reserved ratio | n/a — a product always has ≥1 verified image or the missing-image state | Failed image shows the failure state, never a substitute | Thumbnail disabled while its image fails | Selection announced |

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
| City or area field, distinct from governorate (COR-002) | FR-145 |
| Canonical 27-governorate register | FR-146, §12.1 |
| Honest, configuration-driven eligibility | FR-147 |

### 12.1 Canonical Egyptian governorate register

Exactly these 27 values, with these exact Arabic labels, in this order (FR-146). No governorate may
be added, removed, renamed, or transliterated.

| # | المحافظة | # | المحافظة | # | المحافظة |
| --- | --- | --- | --- | --- | --- |
| 1 | القاهرة | 10 | المنوفية | 19 | دمياط |
| 2 | الجيزة | 11 | المنيا | 20 | الشرقية |
| 3 | الإسكندرية | 12 | القليوبية | 21 | جنوب سيناء |
| 4 | الدقهلية | 13 | الوادي الجديد | 22 | كفر الشيخ |
| 5 | البحر الأحمر | 14 | السويس | 23 | مطروح |
| 6 | البحيرة | 15 | أسوان | 24 | الأقصر |
| 7 | الفيوم | 16 | أسيوط | 25 | قنا |
| 8 | الغربية | 17 | بني سويف | 26 | شمال سيناء |
| 9 | الإسماعيلية | 18 | بورسعيد | 27 | سوهاج |

**Locality handling** (requirements level — no eligibility is asserted here):

| Rule | Behaviour |
| --- | --- |
| Greater Cairo | القاهرة and الجيزة **may** participate in configuration-driven Greater Cairo same-day-delivery eligibility. Participation is decided by configuration, never by the governorate value alone (FR-147, BR-016) |
| Installation | الإسكندرية **may** participate in configuration-driven installation eligibility, alongside Greater Cairo. Same constraint (FR-147) |
| Mansoura | المنصورة is accepted naturally as a **city/area** value within الدقهلية. It is not a governorate and never appears in the governorate register |
| Every other governorate | The customer enters their own city/area freely in the FR-145 field. No customer is forced into a Cairo-centric list, and no governorate is treated as unserviceable at the address step |
| Honesty | Where configuration cannot determine eligibility for the given governorate + city/area, the option is **not offered**. Eligibility is never inferred dishonestly from the governorate alone (FR-147) |

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

### 14.1 Visual-integrity review criteria (FR-160–FR-163)

Each criterion is observable and is checked in **both** critique passes against the §3 grounding
evidence, the §17.2.1 section purposes, the ratified token set, and the §9 responsive rows.

| # | Observable condition | Method | Fails if |
| --- | --- | --- | --- |
| VI-1 | No dark-themed surface | Sample the computed background of every full-bleed band at all four widths | Any band resolves to a dark theme outside a ratified navy `#0D1B3D` brand surface present in the evidence |
| VI-2 | Navy band is a brand surface, not a theme | Compare each navy band's position and extent to the matrix row for that page | A navy band appears where the evidence shows none, or its foreground leaves the ratified palette |
| VI-3 | No generic AI-style or stock imagery | Every rendered image resolves to a `media_asset_id` in the verified media register | Any image has no register entry |
| VI-4 | No oversized empty area | For each content region, measure vertical whitespace against rendered content height at the same width | Whitespace exceeds 2× content height |
| VI-5 | No unjustified gradient | Enumerate every gradient in the built stylesheet | Any gradient other than the ratified navy stops or the single gold stop |
| VI-6 | No glassmorphism | Search computed styles for backdrop blur behind translucent surfaces | Any occurrence |
| VI-7 | No repetitive filler | Compare each section's layout signature and data source against §17.2.1 | Two sections share layout and purpose without distinct verified data |
| VI-8 | Restrained motion | Record duration, iteration count and trigger of every animation | Any animation > 400 ms, infinite iteration, or fires without user intent |
| VI-9 | Reduced motion respected | Re-run with `prefers-reduced-motion: reduce` | Any non-essential motion still runs |
| VI-10 | No length-padding section | Every rendered section maps to a §17.2.1 purpose with a non-empty data source | A section renders with no purpose or no verified data |

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
| BR-003 | **Merchandise subtotal** = Σ(verified unit price × valid quantity) over purchasable line items only. Quote-only, unavailable and invalid lines contribute exactly `0` and are excluded from the sum |
| BR-004 | A **verified discount**, when present, derives from a verified configured source and is subtracted **after** the BR-003 merchandise subtotal. No invented discount may be shown |
| BR-005 | VAT = **14%** of the **taxable base** defined in BR-017, applied by one shared, tested routine |
| BR-006 | **Free-shipping eligibility is assessed against the BR-003 merchandise subtotal** — before any discount and before VAT. Shipping is free when that subtotal is **≥ 1,500 EGP**; otherwise the configured shipping charge applies and the shortfall to the threshold is stated. A verified discount that lowers the post-discount amount below 1,500 EGP **does not** withdraw an eligibility already earned on the merchandise subtotal |
| BR-007 | All monetary values use a decimal representation. Binary floating point is prohibited for money at every layer |
| BR-008 | **Grand total = merchandise subtotal − verified discount + shipping + VAT.** This identity MUST hold exactly on Cart, Checkout, Review and Confirmation |
| BR-009 | Prices are data-driven; no price may be hard-coded in a page |
| BR-010 | A product is **purchasable** only when it has a verified retail price **and** is configured purchasable. Otherwise it is **quote-only**: no price, no cart action; Request Price / Request Quote instead. *Verified today: 21 of 21 approved products are quote-only* |
| BR-011 | Installment amounts derive from the same authoritative price as every other surface |
| BR-012 | Availability shown to customers derives from verified data; when availability is unknown it is not asserted |
| BR-013 | Raw card data is never collected, transmitted, logged, or stored |
| BR-014 | Provider credentials and availability come from validated environment configuration, behind adapter boundaries |
| BR-015 | An order draft is a record of intent, never a claim of payment or fulfilment |
| BR-016 | Same-day delivery and installation are configuration-driven and are absent everywhere when disabled |
| BR-017 | **Taxable base = merchandise subtotal (BR-003) − verified discount (BR-004) + taxable shipping.** Shipping enters the taxable base only when configuration marks it taxable; when configuration marks it non-taxable it is excluded from the base but is still added to the grand total under BR-008 |
| BR-018 | **Rounding happens exactly once.** Line extensions and the merchandise subtotal are carried at full decimal precision; VAT is computed on the taxable base and **rounded once** to 2 decimal places using the project's single centralized decimal rule (half-up). No intermediate value is rounded, and no surface re-rounds a value it received |
| BR-019 | Cart, Checkout, Review and Confirmation MUST render **identical formatted values** for the same basket. A surface renders the computed result; it never recomputes independently |

#### 17.1.1 Authoritative calculation contract

The order of operations is fixed and is the only permitted sequence:

1. **Line extension** — verified unit price × valid quantity, full precision (BR-003).
2. **Merchandise subtotal** — sum of line extensions over purchasable lines only (BR-003).
3. **Free-shipping eligibility** — evaluated against the merchandise subtotal from step 2 (BR-006).
4. **Verified discount** — subtracted from the merchandise subtotal (BR-004).
5. **Shipping** — `0` when eligible, otherwise the configured charge (BR-006).
6. **Taxable base** — subtotal − discount + taxable shipping (BR-017).
7. **VAT** — 14% of the taxable base, **rounded once** to 2 dp, half-up (BR-005, BR-018).
8. **Grand total** — subtotal − discount + shipping + VAT (BR-008).

#### 17.1.2 Worked calculation examples

> **These are specification calculation examples only.** The amounts are illustrative figures
> chosen to exercise the contract's boundaries. They are **not** ZAKEY product prices, are not
> verified retail evidence, and MUST NOT be seeded, displayed, or treated as production facts
> (Constitution XX.10, BR-009, FR-111). The configured shipping charge shown as `60.00 ج.م` is
> likewise an example value, not a ratified rate.

**Example A — below the free-shipping threshold**

| Step | Value |
| --- | --- |
| Line: 1 × 1,200.00 | 1,200.00 |
| Merchandise subtotal (BR-003) | **1,200.00** |
| Free-shipping check: 1,200.00 < 1,500.00 | not eligible |
| Shortfall stated to customer | 300.00 |
| Verified discount | 0.00 |
| Shipping (configured, taxable) | 60.00 |
| Taxable base (BR-017): 1,200.00 − 0.00 + 60.00 | **1,260.00** |
| VAT: 14% × 1,260.00 = 176.40 → round once | **176.40** |
| **Grand total**: 1,200.00 − 0.00 + 60.00 + 176.40 | **1,436.40** |

**Example B — exactly at the 1,500 EGP threshold**

| Step | Value |
| --- | --- |
| Line: 2 × 750.00 | 1,500.00 |
| Merchandise subtotal (BR-003) | **1,500.00** |
| Free-shipping check: 1,500.00 ≥ 1,500.00 | **eligible** — the threshold is inclusive |
| Verified discount | 0.00 |
| Shipping | 0.00 |
| Taxable base: 1,500.00 − 0.00 + 0.00 | **1,500.00** |
| VAT: 14% × 1,500.00 = 210.00 → round once | **210.00** |
| **Grand total**: 1,500.00 − 0.00 + 0.00 + 210.00 | **1,710.00** |

**Example C — above the threshold, with a verified discount and a rounding case**

| Step | Value |
| --- | --- |
| Line: 1 × 1,607.77 | 1,607.77 |
| Merchandise subtotal (BR-003) | **1,607.77** |
| Free-shipping check: 1,607.77 ≥ 1,500.00 | **eligible** |
| Verified discount | 200.00 |
| Post-discount amount: 1,407.77 (< 1,500.00) | eligibility **retained** — BR-006 assesses the merchandise subtotal, not the post-discount amount |
| Shipping | 0.00 |
| Taxable base: 1,607.77 − 200.00 + 0.00 | **1,407.77** |
| VAT: 14% × 1,407.77 = 197.0878 → **rounded once**, half-up, 2 dp | **197.09** |
| **Grand total**: 1,607.77 − 200.00 + 0.00 + 197.09 | **1,604.86** |

Example C is the rounding and eligibility regression case: an implementation that re-rounds an
intermediate value, or that re-tests free-shipping eligibility after the discount, produces a
different grand total and fails FR-143.

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

**Monetary calculation (COR-001)**

- **FR-143**: Cart, Checkout, Review and Confirmation MUST reproduce the §17.1.1 order of operations exactly, and MUST reproduce the §17.1.2 worked examples to the cent. Any surface that re-rounds an intermediate value, or re-evaluates free-shipping eligibility after the discount, fails this requirement.
- **FR-144**: When a basket is below the free-shipping threshold, the shortfall to 1,500 EGP is stated to the customer; at or above the threshold, free shipping is stated. The threshold is inclusive at exactly 1,500.00.

**Egyptian address (COR-002)**

- **FR-145**: Checkout collects a **city or area** field distinct from the governorate. It is required, validated server-side, and accepts free Arabic text so a customer in any governorate can describe their locality without being forced into a Cairo-centric list.
- **FR-146**: The governorate selector offers exactly the canonical 27 governorates in §12.1, rendered with those exact Arabic labels.
- **FR-147**: Delivery and installation eligibility MUST be derived from configuration, never inferred from the governorate alone where the configuration requires finer detail. Where eligibility cannot be determined honestly, the option is not offered and no promise is made.

**Catalogue filters (COR-003)**

- **FR-148**: The catalog offers **verified-feature filters** built only from evidence-backed product facets. A facet with no verified values is not rendered. No capability or compatibility may be invented to populate a filter.
- **FR-149**: The catalog offers **access-method filters** derived from the verified `unlock_methods` evidence (or its approved equivalent field). Options are exactly the distinct verified values present in the catalogue — nothing is added, renamed, or inferred.
- **FR-150**: A filter facet that becomes unavailable, or that resolves to zero verified values, is omitted entirely rather than rendered empty or disabled without explanation.

**Sorting (COR-004)**

- **FR-151**: The catalog supports exactly this sort set, and no other: (a) **default catalogue order** — a deterministic, stable order applied when no sort is chosen; (b) **search relevance** — offered and selected by default only while a search query is active; (c) **product name, Arabic A→Z and Z→A** — ordered using Arabic collation; (d) **price ascending / descending** — offered **only** when the active result set contains at least one product with a verified price. "Newest", "popular", "best rated" and "best selling" are **not** offered: no verified data supports them.
- **FR-152**: Every sort is **deterministic and stable**: ties are broken by a fixed secondary key so identical inputs always yield identical ordering across requests and pages.
- **FR-153**: When price sorting is active in a mixed result set, quote-only products MUST NOT be presented as priced and MUST NOT be assigned an implied price for ordering. They are grouped after priced results in a clearly labelled, non-priced group, retaining their Request Price action.
- **FR-154**: The active sort is encoded in the shareable URL, restores identically in a clean session, and preserves search text and every active filter.

**Product card (COR-005)**

- **FR-155**: Every product card renders the verified `public_display_name` and, where the design calls for a category label, the verified approved category. It MUST NOT substitute an invented category, and when category data is unavailable it hides the label rather than rendering placeholder text.

**Product details (COR-006)**

- **FR-156**: Product details display verified public identifiers — an approved model code or SKU — **only** when present in verified evidence. Internal identifiers are never exposed as customer-facing facts, no identifier is generated, and when no verified public value exists the identifier field is omitted entirely rather than rendered blank. Latin identifiers inside Arabic text render in correct bidirectional order at every width.

**Account (COR-007)**

- **FR-157**: An authenticated customer can view their basic profile information and update the approved profile fields, with server-side validation, field-linked Arabic errors, preserved input on failure, and truthful success or recoverable-failure feedback.
- **FR-158**: Saved contact and address details are stored and reused only where approved, are editable and removable by their owner, and are never pre-filled from another customer's data.
- **FR-159**: Account surfaces MUST NOT expose any other customer's data through identifiers, enumeration, URLs, or error output; an unauthenticated request to a member-only surface returns safely to the intended journey after authentication without leaking whether the target exists.

**Visual integrity (COR-010)**

- **FR-160**: The customer theme is **light only**. No page, section, component or state renders a dark theme. A ratified full-bleed navy `#0D1B3D` band is a brand surface, not a theme switch: it is permitted only where the grounding evidence shows one, and its foreground tokens stay within the ratified palette.
- **FR-161**: The interface MUST NOT contain: generic AI-style or stock-illustrative imagery in place of verified product media; a content region whose vertical whitespace exceeds twice its rendered content height at the same width; a gradient other than the ratified navy or single gold stop recorded in the Constitution; glassmorphism (background blur behind translucent surfaces); two or more sections repeating the same layout and purpose without distinct verified data; or animation that runs longer than 400 ms, loops indefinitely, or triggers without user intent.
- **FR-162**: `prefers-reduced-motion` suppresses all non-essential motion, including carousel autoplay, parallax and entrance animation.
- **FR-163**: Every rendered section MUST serve a purpose declared in §17.2.1. A section that exists only to increase page length, or whose data source is empty, is removed rather than filled with generic content.

#### 17.2.1 Home section contracts (FR-163)

The Home page renders exactly these twelve sections, in this order (FR-016). Each row is binding.
Sections 5, 9 and 10 render **only** when verified data exists and are omitted entirely otherwise —
they are never filled with generic content.

| # | Section | Purpose | Required data | Visible-content rules | Interaction | Empty / unavailable | Responsive (§9) | Verification | Acceptance |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | Announcement Bar | Carry one configured, truthful message | Configured message string | No invented discount, code, or threshold other than 1,500 EGP | Dismissible per session | Not rendered when unconfigured | 1 line ≥768; may wrap to 2 lines at 390 | Message is configuration, not copy in a page | FR-001, US1-1 |
| 2 | Header | Persistent navigation and commerce entry | Nav destinations, cart count | Only destinations with verified content | Nav, search, wishlist, cart, account; menu at ≤1024 | n/a — always renders | Inline nav 1440; hamburger ≤1024; search+cart only at 390 | Destinations resolve to real URLs | FR-002–FR-011, FR-015 |
| 3 | Hero | State what ZAKEY sells and route into the catalogue | One verified smart-lock image from the media register; Arabic headline | **No** invented statistics — no homes-protected, uptime, rating, or award | ≥1 working primary action | Image falls back to the missing-image state, never a stock substitute | 2-col split 1440/1024; single column 768/390; h1 72→60→48px | Image cites a `media_asset_id` | FR-017, FR-018, FR-031 |
| 4 | Shop by Category | Route to the three approved categories | Approved categories; counts computed from real data | Only approved categories; counts omitted if not computable | Card activates a pre-filtered catalog | Section omitted if no category has products | 4 cols 1440/1024; 2 cols 768; **2 cols 390** | Category vocabulary matches the register | FR-019, FR-020, US1-3 |
| 5 | Best Sellers | Surface a verified curated selection | Verified configured selection | Cards follow the FR-049 contract | Card → product details | **Omitted entirely when no verified selection exists** | 4/4/2/1 cols, 24px gap | Selection is configuration-backed | FR-021, FR-049–FR-056 |
| 6 | Featured Products | Surface a second verified curated selection | Verified configured selection | Same card contract; must differ from §5 or one is removed (FR-161) | Card → product details | Omitted entirely when unverified | 4/4/2/1 cols, 24px gap | Selection is configuration-backed | FR-022, FR-161 |
| 7 | Why Choose ZAKEY | State truthful product-relevant propositions | Curated proposition list | No invented certification, award, warranty or guarantee | Static; no dead controls | Omitted when no proposition is verified | 3 cols 1440/1024; 2 cols 768; 1 col 390; 32px gap | Each proposition traces to provenance | FR-023, FR-111 |
| 8 | Smart Home Solutions | Show verified compatibility and capability | Verified compatibility claims | Only verified integrations; no logo implies partnership | Optional route to filtered catalog | Omitted when no verified claim exists | 2-col split 1440/1024; single column 768/390; 64px gap | Claims trace to provenance | FR-024, FR-027 |
| 9 | Customer Reviews | Present verified customer feedback | Verified review records | Data-driven only; no invented rating or count | Optional pagination/carousel obeying FR-162 | **Omitted entirely — no placeholder, no zero-state** | Multi-col 1440/1024; 2 cols 768; 1 col 390 swipeable without page overflow | Each review traces to a verified source | FR-025, FR-026, EC-08 |
| 10 | Brand Partners | Show authorized partner marks | Verified authorized relationships | No logo without verified authorization | Static | **Omitted entirely** | Strip 1440/1024; wrapped rows 768; 1–2 per row 390 | Authorization recorded in provenance | FR-027, FR-028, EC-09 |
| 11 | Newsletter | Collect an email subscription | — | Truthful success/failure only | Labelled field + submit | Failure is recoverable; no fake success | Inline ≥768; stacked full-width 390 | — | FR-014, FR-125 |
| 12 | Footer | Site-wide verified destinations and contact | Verified destinations; configured hotline and location | Unverified destinations omitted (FR-013) | Links, social only when verified | Groups collapse rather than render empty | 5 cols 1440/1024; 2 cols 768; 1 col collapsible 390 | Hotline/location from configuration | FR-012, FR-013, FR-109 |

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
| SC-023 | The three §17.1.2 worked examples reproduce to the cent on Cart, Checkout, Review and Confirmation — grand totals 1,436.40 / 1,710.00 / 1,604.86 — in 100% of runs |
| SC-024 | Free shipping applies at a merchandise subtotal of exactly 1,500.00 and at every value above it, and at no value below it, including when a verified discount lowers the post-discount amount below the threshold |
| SC-025 | VAT is rounded exactly once, half-up, to 2 decimal places; Example C yields 197.09 and never 197.08 or a re-rounded variant |
| SC-026 | All 27 governorates render with the exact §12.1 Arabic labels; a customer in any governorate can submit a valid city/area value |
| SC-027 | 100% of catalogue filter options — category, use-case, feature, access-method, availability, price — derive from verified evidence; zero invented options render |
| SC-028 | Every offered sort is deterministic and stable across repeated requests, and zero quote-only products are presented as priced under any sort |
| SC-029 | Zero dark-themed surfaces, zero unjustified gradients, zero glassmorphism, zero indefinitely-looping or unintended animation, and zero sections rendered without a §17.2.1 purpose |

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
| FR-143–FR-144 (monetary calculation) | SC-007, SC-008, SC-009, SC-023, SC-024, SC-025 |
| FR-145–FR-147 (Egyptian address) | SC-011, SC-012, SC-026 |
| FR-148–FR-150 (catalogue filters) | SC-002, SC-017, SC-027 |
| FR-151–FR-154 (sorting) | SC-017, SC-018, SC-028 |
| FR-155 (product-card category) | SC-002, SC-005 |
| FR-156 (product identifiers) | SC-002, SC-013 |
| FR-157–FR-159 (account profile and isolation) | SC-005, SC-014 |
| FR-160–FR-163 (visual integrity) | SC-022, SC-029 |
| BR-001–BR-019 | SC-007–SC-011, SC-018, SC-019, SC-023, SC-024, SC-025 |
| NFR-001–NFR-010 | SC-003, SC-016 |

**Coverage** (recomputed 2026-08-01 after the COR-001…COR-012 correction pass): **163** functional
requirements (FR-001–FR-163), **19** business rules (BR-001–BR-019) and **10** non-functional
requirements (NFR-001–NFR-010) — **all mapped**. **29** success criteria (SC-001–SC-029), **all
reachable** from at least one requirement. Zero unmapped requirements; zero duplicate identifiers;
zero gaps in any sequence.

**Scenario coverage**: 8 user stories, each independently testable with a stated Independent Test;
**60** numbered acceptance scenarios; **15** edge cases. Every requirement added in this pass
(FR-143–FR-163, BR-017–BR-019, SC-023–SC-029) is bound to at least one acceptance scenario:

| Added requirement | Acceptance scenario |
| --- | --- |
| FR-143, FR-144, BR-017–BR-019 | US4-9, US4-10, US4-11, US4-12 |
| FR-145, FR-146, FR-147 | US5-6, US5-7, US5-8, US5-9, US5-10 |
| FR-148, FR-149, FR-150 | US3-6, US3-7 |
| FR-151, FR-152, FR-153, FR-154 | US3-8, US3-9, US3-10, US3-11 |
| FR-155 | US1-6 |
| FR-156 | US1-7, US1-8 |
| FR-157, FR-158, FR-159 | US7-5, US7-6, US7-7, US7-8 |
| FR-160–FR-163 | §14.1 VI-1…VI-10, verified in both critique passes |
| SC-023–SC-025 | US4-9…US4-12 |
| SC-026 | US5-6, US5-7 |
| SC-027 | US3-6, US3-7 |
| SC-028 | US3-8, US3-9 |
| SC-029 | §14.1 VI-1…VI-10 |

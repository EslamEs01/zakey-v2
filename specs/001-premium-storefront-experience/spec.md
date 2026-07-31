# Feature Specification: ZAKEY Premium Public Storefront Experience

**Feature Branch**: `001-premium-storefront-experience`
**Feature Number**: `001`
**Created**: 2026-07-31
**Status**: Draft — 3 clarifications outstanding
**Constitution**: ZAKEY Premium Smart Lock Storefront Constitution v1.0.0 (ratified 2026-07-31)
**Input**: User description: "Create the first complete feature specification for the new ZAKEY platform — the complete, coherent public storefront frontend covering the shared visual system, public product-discovery experience, public informational pages, responsive behavior, interactions, accessibility, content integrity, and the boundaries between this frontend specification and future commerce/backend specifications."

---

## 1. Purpose and Product Outcome

ZAKEY needs one coherent public storefront that presents its smart-lock range with the premium,
modern, minimal, elegant, trustworthy, technical, product-focused character established by the
approved visual reference — and that tells the truth about every product it shows.

**Product outcome.** A visitor arriving with no prior knowledge of ZAKEY can, within a single
session and without an account:

1. understand what ZAKEY offers and who it is for,
2. browse the complete verified product range,
3. narrow that range by category, series, and access method,
4. search for a specific model,
5. inspect an individual product's verified imagery and verified attributes,
6. save products of interest for the duration of their visit,
7. start a genuine commercial conversation about those products,
8. read ZAKEY's public informational content,

on a phone, a tablet, or a desktop, using a mouse, a keyboard, or a screen reader, without ever
encountering a control that does nothing, a claim ZAKEY cannot substantiate, or a success message
for something that did not happen.

**What this feature is not.** It is not the commerce engine. It does not persist a catalog in a
database, does not create accounts, does not take payment, and does not create orders. Those are
named and deferred in [§19 Explicit Out of Scope](#19-explicit-out-of-scope). This specification
defines the public experience and the seam at which the future commerce work attaches.

**Why the boundary sits here.** The only verified ZAKEY product data available to this project is
governed as *quote-only* and explicitly creates no price, stock, warranty, delivery, certification,
or popularity fact (see [§2.3](#23-legacy-repository-evidence)). Constitution Principle VI.8
requires commerce prices to originate from authoritative data, and Principle V.4 requires any
untraceable claim to be removed. A priced cart-and-checkout storefront therefore cannot be built
truthfully today. The storefront specified here is complete and independently valuable without
one, and is shaped so that one can be added later without rewriting its public templates.

---

## 2. Authoritative Sources and Evidence

Constitution Principle I makes the visual reference the primary **visual** authority. Principle V
makes verified legacy content the primary **content** authority. Where the two conflict on a matter
of fact, Principle V wins; where they conflict on a matter of appearance, Principle I wins. Every
such conflict found during inspection is recorded below and resolved explicitly.

### 2.1 Inspection method

| Source | Method | Date | Result |
| --- | --- | --- | --- |
| Visual reference | HTTP fetch of the published site, its site manifest (`_index.json`), and its published component bundle; structural and textual extraction only | 2026-07-31 | Inspected successfully |
| Legacy repository | Read-only filesystem inspection and text search | 2026-07-31 | Inspected successfully |

No Figma runtime code was copied, retained, or adapted. Inspection recorded observable structure,
observable copy, and observable ordering only. Constitution Principle III.2 prohibits copied Figma
runtime code in the implementation; that prohibition is carried into
[FR-071](#content-source-and-architecture-fr-071-to-fr-078) and [§20](#20-constitution-compliance).

### 2.2 Visual reference evidence

**Reference**: `https://remote-fried-86528699.figma.site/`
**Declared purpose** (reference metadata, verbatim): "Offers a sleek, premium e-commerce platform
for smart door locks, enabling users to explore, compare, and purchase luxury smart security
products with ease."

**Structural finding — the reference is a single-route prototype.** The reference's site manifest
maps exactly one URL (`/`) and renders the entire experience from one code component. It has no
routing, no distinct page URLs, no server rendering, and no persistence. Its "pages" are
client-side view states. The following view states were observed: `home`, `shop`, `product`,
`cart`, `checkout`, `account`, `orders`, `wishlist`, `about`, `contact`, `faq`, `search`.

**Consequence.** The reference cannot be treated as evidence for URL structure, navigation
addressing, or page-level behavior. It is evidence for *composition, hierarchy, density, rhythm,
component language, and section order*. This specification supplies the routing and page-level
behavior the reference lacks.

**Observed section order (homepage), in reference source order:**

| # | Reference section | Eyebrow / heading (verbatim) |
| --- | --- | --- |
| 1 | Announcement bar | promotional coupon code |
| 2 | Header | wordmark, navigation, primary call to action |
| 3 | Hero | "Introducing ZAKEY Apex Pro 2025" / headline ending "Reimagined." / two calls to action / supporting badges |
| 4 | Category showcase | "Browse" / "Shop by Category" |
| 5 | Product rail A | "Top Picks" / "Best Sellers" |
| 6 | Product rail B | "Curated" / "Featured Products" |
| 7 | Value proposition | "Our Promise" / "Why Choose ZAKEY?" |
| 8 | Ecosystem / series showcase | "Ecosystem" / "Explore the Ecosystem" |
| 9 | Testimonials | "Testimonials" / "Trusted by Homeowners" / "4.9" / "(2,847 reviews)" |
| 10 | Press / trust logos | "As Seen In & Trusted By" |
| 11 | Newsletter | "Stay Informed" / "Get Exclusive Updates" / "Subscribe" |
| 12 | Footer | link groups + copyright line |

**Observed footer link groups (verbatim):**

- Products — "Smart Locks", "Deadbolts", "Padlocks", "Accessories", "Smart Home Kits"
- Company — "About Us", "Careers", "Press", "Partners", "Blog"
- Support — "Help Center", "Installation", "Warranty", "Returns", "Contact Us"

**Observed listing controls:** a filter panel titled "Filters" containing "Category", "Price
Range", and "Minimum Rating"; a "Clear All Filters" control; and a sort control offering
"Featured", "Price: Low to High", "Price: High to Low", "Top Rated".

**Observed product-detail controls:** breadcrumb ("Home" › "Shop"), rating summary with a "Read
all" link, "Quantity:" stepper, "Buy Now", verified-purchase review list, and a "You May Also
Like" related rail.

**Observed cart / checkout:** empty state ("Your cart is empty" / "Discover our premium smart lock
collection" / "Shop Now"); coupon field with "Apply"; order summary ("Subtotal", "Shipping",
"Tax (8%)", "Total"); "Proceed to Checkout"; a three-step checkout — "Shipping Information",
"Payment Information" (fields "Cardholder Name", "Card Number", "Expiry Date", "CVV"), "Review
Your Order" — ending at "Place Order".

**Observed typography and color evidence.** The reference applies the accent value `#C9A227` — the
ratified ZAKEY accent gold — as a **text** color for the hero eyebrow on a light background.

**Reference defects recorded under Constitution Principle I.4** (these MUST NOT be reproduced):

| # | Defect | Evidence | Required correction |
| --- | --- | --- | --- |
| RD-1 | Accent gold used as text on a light background | hero eyebrow rendered in `#C9A227` | Constitution II.7 measures this at ≈2.4:1, failing the 4.5:1 text threshold. Reproduce the eyebrow's *placement, size, weight, and letter-spacing*; render it in a token colour meeting 4.5:1. |
| RD-2 | Fabricated product identities | "ZAKEY Apex Pro", "ZAKEY Nexus Elite", "ZAKEY Vault Pro", "ZAKEY Guardian", "ZAKEY Slim Touch", "ZAKEY Entry Plus", "ZAKEY Connect X", "ZAKEY Luxe Series" | No such products exist in verified evidence. Replace with the 21 verified catalog products (§2.3). |
| RD-3 | Fabricated prices | "$389", "$629" | The verified catalog sets `retail_price: null` and `currency: null` for every product. Remove price display; see FR-034. |
| RD-4 | Fabricated ratings and reviews | "4.9", "(2,847 reviews)", "✓ Verified Purchase", named reviewers | Constitution V.3 forbids invented review counts, ratings, and customer reviews. Remove the ratings, review list, "Read all", and "Minimum Rating" filter. |
| RD-5 | Fabricated awards and press | "Red Dot Design Award 2025", "As Seen In & Trusted By", named publications | Constitution V.3 forbids invented awards and media coverage. Remove the section and the badge. |
| RD-6 | Fabricated scale and trust claims | "trusted by over 500,000 homes worldwide", "Homes Protected", "Countries Served", "Uptime Guarantee", "Industry Awards" | Constitution V.3 forbids invented customer numbers. Remove. |
| RD-7 | Fabricated specifications and guarantees | "Stores up to 100 fingerprints with 0.3-second recognition speed and 99.9% accuracy", "IP65 Weather Resistant", "UL, CE, FCC, RoHS", "All ZAKEY products include a full 5-year warranty.", "Free Shipping", "Tax (8%)" | Constitution V.3 forbids invented specifications, certifications, warranties, and delivery promises. Display only the verified specification fields named in §2.3. |
| RD-8 | Fabricated people | named executives, named testimonial authors, "The Team Behind ZAKEY" | Constitution V.3. Remove the leadership and testimonial sections unless verified biographies are supplied. |
| RD-9 | Card-data collection | "Cardholder Name", "Card Number", "Expiry Date", "CVV" | Constitution VI.9 forbids frontend payment simulations from requesting card details. These fields MUST NOT exist in this feature under any circumstances. |
| RD-10 | Unsuitable hero image | reference hero image does not clearly depict a smart door lock | Constitution I.5 — preserve the hero *composition*; replace the image with a verified ZAKEY smart-lock image (FR-030). |
| RD-11 | Popularity-derived merchandising | "Best Sellers" / "Top Picks" rail, "Top Rated" sort option | The verified catalog explicitly creates no popularity fact. Merge the two homepage product rails into one verified "Featured Products" rail (FR-011); remove the "Top Rated" sort. |
| RD-12 | Unverified promotional announcement | announcement bar carrying a coupon code | No verified ZAKEY promotion exists. See FR-002 — the bar renders only when verified announcement content exists. |

### 2.3 Legacy repository evidence

**Path resolution.** The constitution records the verified legacy repository as
`/media/mekky/work/backend/zakey.v1` and carries an open TODO because the originally requested path
was `/media/mekky/work/backend/zakey`. Verified on 2026-07-31: `/media/mekky/work/backend/zakey`
**does not exist**; `/media/mekky/work/backend/zakey.v1` **exists** and is the genuine legacy ZAKEY
Django project (Django apps `products`, `commerce`, `core`, `pages`, `solutions`, `partners`,
`projects`, `leads`, `blog`; `config/`, `static/`, `media/`, `locale/`, `specs/`,
`reference-imports/`). Only one candidate exists, so no clarification marker is spent on it; the
constitution's TODO nonetheless requires the user's explicit confirmation and is recorded as
[RRP-1](#18-repository-readiness-preconditions).

**Read-only compliance.** Inspection used read-only operations only. `db.sqlite3` was deliberately
**not opened**, because opening a SQLite database can create `-wal`/`-shm`/journal files inside the
legacy working tree and would violate Constitution Principle IV.2. Legacy working tree verified
clean before and after inspection (`git status --porcelain` → 0 lines; HEAD `5fdd81d`).

**Verified catalog.** `specs/012-smart-storefront-commerce/data/curated-launch-catalog.v2.json`
(schema 1.0.0, generated 2026-07-21) is a governed, human-authorized dataset. Its stated policy,
verbatim:

> "These exact supplier-branded products and their high-confidence media assignments are
> human-authorized for quote-only public launch in development, staging, and production. No other
> source product or media asset is approved by this manifest. It creates no retail price, currency,
> discount, stock, warranty, delivery, installation, certification, compatibility, market, tax,
> shipping, payment, urgency, or popularity fact."

| Verified fact | Value |
| --- | --- |
| Products | 21 |
| Supplier brand | Lezn (all 21) |
| Supplier relationship | `supplier-branded_not-zakey-manufactured` |
| Commerce mode | `quote_only` (all 21) |
| Retail price / currency | `null` (all 21) |
| Permitted public actions | `request_price`, `request_quote`, `contact` |
| Media assets | 25, with declared roles (`card`, `detail`, `homepage_slider`) and sort order |
| Homepage roles | `featured_products_slider` |
| Approved specification fields | `source_product_family`, `material`, `finishes_colours`, `power_supply`, `unlock_methods` |

**Verified product names** (public display names): Lezn A06, R01, R02, R03, R05, R06, R09, R15,
M15, M15 max, M17, M18 max, M20, M30, MR6, MR8, K11, W06, W08, W12, Tuya-02 — each suffixed
"Smart Lock".

**Verified taxonomy:**

- Categories (3): Face Recognition Locks (7 products), Palm Vein & Face Locks (13), Handle &
  Waterproof Locks (1).
- Collections / series (6): AI Series, Aurora Series, Knight Series, Mirror Series, Touch Screen
  Series, Handle Waterproof Series.
- Access-method facets (6): Fingerprint Unlock, Card & NFC Access, App Control, Video Intercom,
  Face Unlock, Palm Vein Unlock.

**Verified brand assets:** `static/brand/blue-logo.png`, `static/brand/white-logo.png`,
`static/icons/zakey-logo-blue.png`, `static/icons/zakey-logo-white.png`. Product imagery:
`reference-imports/spec-012/` holds source model photography on white
(A-06, M15, M15 max, M17, M18, M18 max, M20, M30, R01, R03, R15, TTS-06, TTS-07, TUYA-02, W12,
K2, LE-D6, and others).

**Verified editorial voice.** Legacy public copy is deliberately conservative and self-limiting —
for example it labels scenario content "An illustrative scenario, not a delivered project", and
carries the FAQ entry "Are the products Zakey-manufactured?". This voice is the model for
storefront copy (FR-064).

**Legacy content gaps found (these are why RRP-2 and CL-3 exist):**

- Contact details in legacy templates are placeholders (`+1 (000) 000-0000`, `+201234567890`). No
  verified ZAKEY phone number, email address, or postal address was found.
- Privacy and Terms templates exist (18.3 KB / 16.0 KB) but render their body from database-backed
  content; no verified legal text is present in the repository.

### 2.4 Reference-versus-legacy conflicts and their resolution

| # | Reference says | Verified evidence says | Resolution |
| --- | --- | --- | --- |
| CF-1 | Priced D2C storefront with cart, checkout, payment, tax | `commerce_mode: quote_only`, `retail_price: null`, permitted actions are request price / request quote / contact | Storefront is quote-led. Cart, checkout, payment, and orders deferred. **See [CL-1](#3-clarifications).** |
| CF-2 | ZAKEY-branded invented products | 21 Lezn supplier-branded products, explicitly not ZAKEY-manufactured | Use verified names (FR-029). Supplier relationship stated honestly where relevant (FR-067). |
| CF-3 | Ratings, reviews, awards, press, scale claims | Catalog creates no popularity fact; no verified reviews or awards exist | Removed (RD-4, RD-5, RD-6). |
| CF-4 | Rich specification claims | Five approved specification fields only | Display approved fields only, per product, only where populated (FR-035). |
| CF-5 | Persistent account area, saved cards, addresses, order history | No verified accounts; authentication out of scope | Deferred to Feature 003 (§19). |
| CF-6 | Product comparison implied in reference metadata copy | No comparison view, control, or state exists anywhere in the reference bundle; no legacy comparison feature | **Excluded.** Not built on metadata prose alone. |
| CF-7 | Newsletter subscription with "Subscribe" success | No subscription storage or email delivery in scope | Newsletter deferred; Constitution VI.4 forbids a fake success state. Section replaced (FR-012). |

---

## 3. Clarifications

Exactly three material ambiguities remain. Each would change scope, data behavior, or user
experience depending on how it is answered. Each records the default this specification currently
assumes, so the specification is actionable as written.

> **[NEEDS CLARIFICATION: CL-1 — Commerce model]** The visual reference is a fully priced
> cart-and-checkout storefront; the only verified ZAKEY product data is governed `quote_only` with
> `retail_price: null` and permitted public actions `request_price` / `request_quote` / `contact`.
> Should Feature 001 deliver **(A)** the quote-led storefront the verified data supports — product
> discovery plus quote and enquiry actions, with cart, checkout, payment, and orders deferred to
> Feature 002 — or **(B)** a priced cart-and-checkout storefront, which would require the user to
> supply verified retail prices, currency, tax treatment, and shipping terms before implementation
> can begin? *Assumed default: **(A)**.* Answering (B) adds three pages, five component families,
> and a dependency on verified pricing; it does not change the visual direction.

> **[NEEDS CLARIFICATION: CL-2 — Quote and enquiry submission]** For the quote request, product
> enquiry, and contact forms, does Feature 001 **(A)** end at a validated, reviewable summary that
> hands the visitor a verified way to reach ZAKEY, storing nothing and promising no reply;
> **(B)** persist submissions to a real store and confirm success only after that store confirms
> the write; or **(C)** persist and notify ZAKEY by email or messaging? Constitution VI.4 forbids
> showing success unless the operation actually succeeded, so this choice determines what the
> confirmation may say. *Assumed default: **(B)** — persist to a real store; success is shown only
> on a confirmed write; no delivery, reply-time, or follow-up promise is made.* Notification
> delivery is out of scope in all three answers.

> **[NEEDS CLARIFICATION: CL-3 — Verified contact details and legal text]** No verified ZAKEY phone
> number, email address, postal address, privacy policy text, or terms text was found; legacy
> contact values are placeholders. Will the user supply verified contact details and verified legal
> text for this feature, or should the Contact page render only the enquiry form (no contact
> details block) and the Privacy and Terms pages plus their footer links be removed entirely?
> *Assumed default: the storefront ships with the enquiry form only, and any surface with no
> verified content is removed together with every link that points at it — never rendered as a dead
> link and never filled with drafted text.*

Resolved without spending a marker, on evidence:

- **Legacy path** — `/media/mekky/work/backend/zakey` does not exist; `zakey.v1` is the only
  candidate. User confirmation is still required by the constitution's own TODO ([RRP-1](#18-repository-readiness-preconditions)).
- **Product comparison** — excluded; no supporting evidence in reference or legacy (CF-6).
- **Wishlist** — included as visit-scoped "Saved products"; present in the reference and compatible
  with a quote-led model (US4, FR-042).

---

## 4. User Scenarios & Testing *(mandatory)*

Stories are ordered by importance. Each is independently testable and independently valuable: if
only US1 shipped, ZAKEY would have a working premium storefront.

### User Story 1 - Understand ZAKEY and enter the range (Priority: P1)

A visitor who has never heard of ZAKEY lands on the homepage. Within one screen they understand
that ZAKEY supplies premium smart door locks; scrolling, they meet the product categories, a
selection of featured products, what ZAKEY stands behind, and the product series — then reach a
footer that tells them where everything else lives. Any of those sections takes them into the
range.

**Why this priority**: This is the storefront's first impression and the entry point to every other
journey. It carries the premium character the whole feature exists to establish.

**Independent Test**: Load the homepage at all four verification widths with no prior session; walk
every section in order; follow every link. Delivers a complete, navigable brand and range
introduction with no dead control and no unverifiable claim.

**Acceptance Scenarios**:

1. **Given** a first-time visitor at 1440px, **When** the homepage loads, **Then** the header, hero
   headline, hero supporting copy, and both hero calls to action are visible without scrolling, and
   the hero image is a verified ZAKEY smart-lock image.
2. **Given** the homepage, **When** the visitor scrolls to the end, **Then** they encounter, in
   order: category showcase, featured products, value proposition, series showcase, enquiry call to
   action, footer.
3. **Given** the homepage, **When** every link and button is activated in turn, **Then** each
   resolves to a real page or performs a defined action; none is inert and none targets `#`.
4. **Given** the homepage, **When** its copy is audited against §2.3, **Then** no rating, review
   count, award, press mention, certification, warranty, delivery promise, customer count, price,
   or stock figure appears.
5. **Given** the homepage at 390px, **When** it is measured, **Then** document scroll width does not
   exceed viewport width, and the mobile navigation is reachable and operable.

---

### User Story 2 - Browse and narrow the range (Priority: P1)

A visitor who knows they want a smart lock opens the full range, narrows it by category, series,
and access method, sorts it, moves through pages of results, and clears their filters to start
again — on desktop and on a phone.

**Why this priority**: Product discovery is the storefront's core job. Without it the range is a
flat list.

**Independent Test**: From the listing page, apply each filter family alone and in combination,
sort, paginate, and clear; repeat at 390px using the mobile filter surface. Delivers complete
product-discovery value on its own.

**Acceptance Scenarios**:

1. **Given** the listing page, **When** it loads unfiltered, **Then** every verified product is
   reachable through pagination, and the result count is stated.
2. **Given** the listing page, **When** a category filter is applied, **Then** only products in that
   category are shown, the count updates, the applied filter is visibly indicated, and the URL
   reflects the filtered state so it can be shared and reloaded.
3. **Given** two filter families applied together, **When** results are shown, **Then** products
   satisfy both, and each applied filter can be removed individually.
4. **Given** a filter combination with no matches, **When** results are shown, **Then** a no-results
   state explains that no products match and offers a control that clears the filters.
5. **Given** filters applied, **When** "clear all" is activated, **Then** every filter resets, the
   full range returns, and the URL returns to the unfiltered address.
6. **Given** a visitor at 390px, **When** they open filters, **Then** filters appear in a surface
   designed for that width, focus is trapped inside it, Escape closes it, and closing returns focus
   to the control that opened it.
7. **Given** any sort option, **When** it is selected, **Then** ordering changes accordingly, the
   selection persists across pagination, and the sort is expressed in the URL.

---

### User Story 3 - Inspect one product in depth (Priority: P1)

A visitor opens a product, studies its imagery from several angles, reads its verified attributes,
understands honestly what ZAKEY can and cannot tell them about it, and sees related products.

**Why this priority**: The product page is where a discovery journey converts into intent. It is
also where content-integrity failures do the most damage.

**Independent Test**: Open each verified product; exercise the gallery; audit displayed attributes
against the approved specification fields. Delivers complete product-inspection value on its own.

**Acceptance Scenarios**:

1. **Given** a product page, **When** it loads, **Then** it shows the verified display name, its
   verified imagery, its category, its series where one is assigned, and its access methods.
2. **Given** a product with multiple images, **When** the gallery is operated by pointer, keyboard,
   and touch, **Then** the main image changes, the active thumbnail is indicated, and the image
   region does not change size between images.
3. **Given** a product page, **When** its attribute table is audited, **Then** it contains only
   approved specification fields, and a field with no verified value is omitted rather than shown
   empty or filled with a placeholder.
4. **Given** a product page, **When** the availability and pricing area is inspected, **Then** it
   states honestly that pricing is provided on request and offers the quote action — with no
   figure, no "from" price, no stock count, and no urgency claim.
5. **Given** a product page, **When** related products are shown, **Then** each shares that
   product's category or series, and the product being viewed is not among them.

---

### User Story 4 - Save products across the visit (Priority: P2)

A visitor collecting candidates saves products as they browse, sees a running count in the header,
reviews the saved set on its own page, removes items, and carries the set into a quote request.

**Why this priority**: It makes a multi-product enquiry practical, which is the natural shape of a
quote-led smart-lock purchase. It is not required for the storefront to be useful.

**Independent Test**: Save and unsave from listing, product, and saved-products surfaces; reload;
empty the list. Delivers a working shortlist on its own.

**Acceptance Scenarios**:

1. **Given** any product card or product page, **When** the save control is activated, **Then** the
   control reflects the saved state, the header count increases, and the change survives navigation
   and reload within the visit.
2. **Given** a saved product, **When** the control is activated again, **Then** the product is
   removed and the count decreases.
3. **Given** no saved products, **When** the saved-products page is opened, **Then** an empty state
   explains what saving does and links into the range.
4. **Given** saved products, **When** a quote request is started from that page, **Then** the
   request begins pre-populated with exactly those products.
5. **Given** the saved-products page, **When** a visitor reads it, **Then** nothing describes the
   set as an order, a cart, a reservation, or a held item.

---

### User Story 5 - Search for a specific model (Priority: P2)

A visitor who knows a model code searches for it from any page and reaches it directly.

**Why this priority**: Model-code search is how returning and trade visitors navigate a technical
catalog. Browsing already covers the range, so this is an accelerator.

**Independent Test**: Search from several pages for a full name, a partial model code, a category
name, and a term with no matches.

**Acceptance Scenarios**:

1. **Given** any page, **When** search is opened, **Then** it is reachable by keyboard, is labelled,
   and receives focus on opening.
2. **Given** a query matching verified products, **When** it is submitted, **Then** matching
   products are listed with the query echoed and the result count stated.
3. **Given** a query matching nothing, **When** it is submitted, **Then** a no-results state
   explains that nothing matched and offers a route back into the full range.
4. **Given** an empty or whitespace-only query, **When** it is submitted, **Then** the storefront
   does not error and does not present a results page implying a search occurred.
5. **Given** a results page, **When** its address is copied and reloaded, **Then** the same results
   are shown.

---

### User Story 6 - Start a commercial conversation (Priority: P2)

A visitor requests a quote for one or several products, or sends a general enquiry, supplying their
details and being told plainly what will happen next.

**Why this priority**: This is the storefront's conversion point under a quote-led model, and it
completes US4. It depends on CL-2.

**Independent Test**: Submit each form empty, with invalid values, and with valid values, by
keyboard and at 390px.

**Acceptance Scenarios**:

1. **Given** a quote request form, **When** it is submitted empty, **Then** submission is refused,
   each invalid field is individually described, the message is programmatically associated with
   its field, and focus moves to the first invalid field.
2. **Given** a form with an invalid email address, **When** it is submitted, **Then** the email
   field is identified specifically rather than the form being rejected as a whole.
3. **Given** a valid submission, **When** it is sent, **Then** the control enters a busy state, the
   form cannot be double-submitted, and a confirmation appears **only after** the underlying
   operation reports success.
4. **Given** the underlying operation fails, **When** the response returns, **Then** an honest
   failure state is shown, the visitor's entered values are preserved, and no confirmation appears.
5. **Given** any form in this feature, **When** its fields are enumerated, **Then** none collects a
   card number, expiry date, security code, PIN, or any payment credential.
6. **Given** a confirmation, **When** its wording is audited, **Then** it makes no promise about
   reply time, delivery, price, or availability that is not verified.

---

### User Story 7 - Read ZAKEY's public information (Priority: P3)

A visitor reads about ZAKEY, finds answers to common questions, and reaches the informational pages
from any page in the storefront.

**Why this priority**: It supports trust and completes the navigation architecture, but no product
journey depends on it.

**Independent Test**: Reach every informational page from header and footer, at every width.

**Acceptance Scenarios**:

1. **Given** any storefront page, **When** the footer is used, **Then** every informational page in
   scope is reachable, and no footer link points at a page that does not exist.
2. **Given** the About page, **When** its claims are audited, **Then** each traces to verified
   evidence, including how ZAKEY describes its relationship to the products it supplies.
3. **Given** the FAQ, **When** a question is activated by keyboard, **Then** its answer expands, the
   control's expanded state is exposed assistively, and activating it again collapses it.
4. **Given** an informational page at 768px, **When** it is read, **Then** line length stays
   readable and no section leaves an oversized empty region.

---

### Edge Cases

- **Product with a single image** — the gallery renders without thumbnails or controls rather than
  showing a disabled carousel.
- **Product with no assigned series** — the series row is omitted, not rendered empty.
- **Category containing exactly one product** (Handle & Waterproof Locks) — the listing renders a
  correct single-item grid without a stretched card or a collapsed layout.
- **Filter combination that is valid but empty** — no-results state, filters preserved and
  individually removable.
- **Pagination beyond the last page** — the storefront returns a defined response rather than an
  unhandled error; the visitor is returned to a valid page.
- **Unknown category, series, or product address** — the custom 404 page, with working navigation.
- **Search query containing markup or script syntax** — echoed escaped; never rendered as markup.
- **Very long search query or filter value** — handled without layout overflow at any width.
- **A verified image missing at build or request time** — a reserved, correctly proportioned
  placeholder region with meaningful alternative text; never a broken-image icon, never a stretched
  image, and never a file whose visible name reveals internal terminology.
- **Saved-products set containing a product later removed from the catalog** — the entry is dropped
  silently and the count corrects itself; no error and no reference to a missing product.
- **Form submitted twice rapidly** — exactly one operation occurs.
- **JavaScript unavailable or failed** — navigation, product discovery, product pages, and
  informational content remain usable; controls that genuinely require scripting are not rendered
  as inert.
- **Reduced-motion preference set** — transitions and any autoplaying movement are suppressed.
- **Very large text scaling (200%)** — no clipped text and no lost control at any width.
- **Server error during a request** — the custom 500 page, with no stack trace and no internal
  detail exposed.

---

## 5. Page Inventory

All 25 candidate surfaces were evaluated. **In scope: 17. Deferred: 7. Excluded: 1.** One
evidence-backed surface (Quote request) is added because the verified catalog names
`request_quote` as a permitted public action.

| # | Surface | Decision | Basis / owning future specification |
| --- | --- | --- | --- |
| 1 | Homepage | **In scope** | Reference §2.2; primary entry point |
| 2 | All-products listing | **In scope** | Reference "All Products"; 21 verified products |
| 3 | Category listing | **In scope** | 3 verified categories |
| 4 | Collection (series) listing | **In scope** | 6 verified collections |
| 5 | Search and search results | **In scope** | Reference search; US5 |
| 6 | Product detail | **In scope** | 21 verified products |
| 7 | Product gallery and media states | **In scope** | 25 verified media assets with declared roles |
| 8 | Cart | **Deferred** | Feature 002 — Commerce Foundation. No verified price; CF-1, CL-1 |
| 9 | Checkout / order review | **Deferred** | Feature 002. Constitution VI.9 forbids the reference's card fields (RD-9) |
| 10 | Order success / confirmation | **Deferred** | Feature 002. Constitution VI.4 forbids a success state with no underlying order |
| 11 | Saved products (wishlist) | **In scope** | Reference wishlist; visit-scoped; US4 |
| 12 | Product comparison | **Excluded** | No reference or legacy evidence (CF-6) |
| 13 | About ZAKEY | **In scope** | Reference About; verified legacy copy |
| 14 | Contact | **In scope** | Reference Contact; `contact` is a permitted public action. Contact-details block subject to CL-3 |
| 15 | FAQ | **In scope** | Reference FAQ; verified legacy FAQ content |
| 16 | Shipping information | **Deferred** | Feature 002. Catalog creates no delivery fact |
| 17 | Returns information | **Deferred** | Feature 002. Catalog creates no returns fact |
| 18 | Warranty information | **Deferred** | Feature 002. Catalog creates no warranty fact |
| 19 | Privacy policy | **In scope, conditional** | Required where enquiry data is collected. Content must be verified ZAKEY legal text; if unavailable, page **and** its links are removed (CL-3) |
| 20 | Terms and conditions | **In scope, conditional** | Same condition as #19 (CL-3) |
| 21 | Empty states | **In scope** | Cross-cutting; §10 |
| 22 | Loading states | **In scope** | Cross-cutting; §10 |
| 23 | Validation and error states | **In scope** | Cross-cutting; §10 |
| 24 | Custom 404 | **In scope** | Constitution VI.7 |
| 25 | Custom 500 | **In scope** | Constitution VI.7 |
| + | Quote request | **In scope** | Verified `public_actions: request_price, request_quote`; legacy "Request a quote". Subject to CL-2 |

Deferred account surfaces observed in the reference — account overview, order history, saved
addresses, saved payment methods, sign-in and registration — are deferred to **Feature 003 —
Customer Accounts**. The newsletter section is deferred to **Feature 004 — Marketing and
Notifications** (CF-7).

---

## 6. Shared Component Inventory

**34 component families.** Each is defined once and reused; Constitution IV.4 forbids duplicating a
shared component between pages.

| # | Family | Purpose | States |
| --- | --- | --- | --- |
| C-01 | Announcement bar | Site-wide verified message | present (verified content) / absent; dismissed persists for the visit |
| C-02 | Desktop header | Wordmark, primary navigation, search entry, saved-products entry, primary action | default, scrolled/condensed, current-section, focus-within |
| C-03 | Mobile navigation | Full navigation at narrow widths | closed, opening, open, closing; focus trapped; Escape closes |
| C-04 | Search interface | Query entry and submission from any page | closed, open, empty, typing, submitting, submitted |
| C-05 | Breadcrumbs | Ancestry on listing, category, series, product, informational pages | default, current (non-link), truncated at narrow widths |
| C-06 | Hero | Homepage primary composition | default; reduced-motion |
| C-07 | Section heading | Eyebrow + heading + optional supporting copy + optional action | with/without eyebrow, with/without action |
| C-08 | Category card | Entry to a category | default, hover, focus-visible, pressed |
| C-09 | Collection card | Entry to a series | default, hover, focus-visible, pressed |
| C-10 | Product card | Product in any grid or rail | default, hover, focus-visible, saved, image-loading, image-unavailable |
| C-11 | Price presentation | Honest pricing statement | quote-only (the only state in this feature) |
| C-12 | Availability presentation | Honest availability statement | enquiry-based (the only state in this feature) |
| C-13 | Product badge | Verified attribute marker only | category, series, access method. **No** popularity, discount, award, or certification badge |
| C-14 | Button | Primary, secondary, tertiary, icon-only | default, hover, focus-visible, active, disabled, busy |
| C-15 | Link | Inline and standalone | default, hover, focus-visible, visited, current |
| C-16 | Form field | Text, email, telephone, textarea, select, checkbox | default, focus, filled, invalid, disabled, read-only |
| C-17 | Validation message | Field-level and form-level errors | field error, form summary, success |
| C-18 | Filter panel | Category, series, access-method filters | expanded, collapsed, applied, empty result, drawer (narrow widths) |
| C-19 | Applied-filter chips | Show and individually remove active filters | present, absent, removable |
| C-20 | Sort control | Result ordering | closed, open, selected |
| C-21 | Pagination | Movement through results | first, middle, last, single page, disabled edges |
| C-22 | Gallery controls | Product media navigation | single image, multiple images, active thumbnail, keyboard-operated |
| C-23 | Quantity control | Quantity for a quote line | minimum, typical, maximum, invalid input |
| C-24 | Save (wishlist) control | Save/unsave a product | unsaved, saved, busy, unavailable |
| C-25 | Quote request surface | Review and submit a multi-product request | empty, populated, validating, submitting, submitted, failed |
| C-26 | Dialog | Modal interaction | closed, open, focus-trapped, Escape-dismissed |
| C-27 | Drawer | Off-canvas surface (mobile nav, filters) | closed, open, focus-trapped, Escape-dismissed |
| C-28 | Toast notification | Transient confirmation of a completed action | enter, visible, dismissed, reduced-motion, assistively announced |
| C-29 | Enquiry call-to-action band | Homepage conversion band replacing the newsletter (CF-7) | default |
| C-30 | Informational content section | Prose, question-and-answer, contact blocks | default, expanded/collapsed (FAQ) |
| C-31 | Footer | Site-wide navigation and legal links | default; links render only for pages that exist |
| C-32 | Loading state | Deferred content and in-flight actions | skeleton (reserved dimensions), busy control |
| C-33 | Empty state | No content to show | listing, search, saved products |
| C-34 | Error state | Something failed | field, form, page-level, 404, 500 |

Removed relative to the reference, with cause: rating presentation and review list (RD-4); press
and award badges (RD-5); testimonial card (RD-4/RD-8); newsletter subscription form (CF-7); cart
drawer, coupon field, order summary, shipping-method selector, and every payment field (CF-1,
RD-9).

---

## 7. Interaction and Control Inventory

Constitution VI.1–VI.3: every control below has defined behavior, and no control ships without one.

| Control | Trigger | Defined behavior |
| --- | --- | --- |
| Wordmark | click / Enter | Navigates to homepage |
| Primary navigation item | click / Enter | Navigates; current item marked as current |
| Mobile menu open | click / Enter / Space | Opens drawer, moves focus in, traps focus |
| Mobile menu close | click / Escape / overlay click | Closes drawer, returns focus to opener |
| Search open | click / Enter | Reveals search, focuses the input |
| Search submit | Enter / click | Navigates to results for the query |
| Search clear | click / Escape | Clears input, keeps focus |
| Breadcrumb ancestor | click / Enter | Navigates to that ancestor |
| Hero primary action | click / Enter | Navigates to the full range |
| Hero secondary action | click / Enter | Navigates to the About page |
| Category / collection card | click / Enter | Navigates to that listing |
| Product card body | click / Enter | Navigates to that product |
| Product card save control | click / Enter / Space | Toggles saved state; count updates; state announced |
| Filter option | click / Space | Applies or removes that filter; results and URL update |
| Filter chip remove | click / Enter | Removes that one filter |
| Clear all filters | click / Enter | Removes every filter; returns to unfiltered address |
| Mobile filter open / close | click / Escape | Opens or closes the filter drawer with focus management |
| Sort option | selection | Reorders results; persists across pagination; reflected in URL |
| Pagination page / prev / next | click / Enter | Moves to that page; edge controls disabled at edges |
| Gallery thumbnail | click / Enter / arrow keys | Changes main image; marks active thumbnail |
| Gallery prev / next | click / Enter / arrow keys | Steps through images |
| Quantity increase / decrease / entry | click / Enter / typing | Adjusts within bounds; rejects invalid input with a message |
| Add to quote request | click / Enter | Adds the product to the request; confirms via toast |
| Remove from quote request | click / Enter | Removes the line; totals of line count update |
| Quote request submit | click / Enter | Validates, submits, enters busy state, confirms only on success |
| Contact form submit | click / Enter | As above |
| FAQ question | click / Enter / Space | Expands or collapses its answer; expanded state exposed |
| Toast dismiss | click / Escape / timeout | Removes the toast |
| Skip to content | Tab from page start, Enter | Moves focus to the main landmark |
| Footer link | click / Enter | Navigates to an existing page |

No control in this feature targets `#`. No control renders without one of the behaviors above.

---

## 8. Responsive-State Inventory

Constitution VII.1 fixes four verification widths. Each receives a deliberate layout decision;
Constitution VII.2 forbids treating narrow layouts as stacked desktop columns.

| Surface | 1440px (desktop) | 1024px (tablet) | 768px (transition) | 390px (mobile) |
| --- | --- | --- | --- | --- |
| Header | Full horizontal navigation, inline search | Full navigation, condensed spacing, search as icon | Navigation collapses to menu control; search icon retained | Menu control, wordmark, saved-products count; search opens full-width |
| Hero | Two columns, text left, image right | Two columns, reduced image share | Single column, image below text, retained aspect ratio | Single column, shortened headline treatment, full-width stacked actions |
| Category showcase | 3 across | 3 across, tighter gutters | 2 across | 1 across, or horizontal scroll rail with visible affordance |
| Product grid | 4 across | 3 across | 2 across | 1 across |
| Product rail | 4 visible, paged | 3 visible, paged | 2 visible, scroll-snap | 1.2 visible, scroll-snap with edge peek |
| Listing + filters | Persistent filter sidebar beside results | Persistent sidebar, narrowed | Filters collapse to a top control opening a drawer | Filter and sort as a sticky bar opening a full-height drawer |
| Product detail | Gallery left, information right, sticky action area | Gallery left, information right, non-sticky | Gallery above information | Gallery full-bleed with swipe; action area pinned to the bottom |
| Gallery | Thumbnail column beside main image | Thumbnail column, narrowed | Thumbnail row below main image | Swipeable main image with position indicator |
| Saved products | Grid, 3 across | Grid, 3 across | Grid, 2 across | List rows, 1 across |
| Quote request | Two columns: lines and summary | Two columns, narrowed summary | Single column, summary above submit | Single column, submit pinned to the bottom |
| Forms | Multi-column field groups | Multi-column where pairs fit | Single column | Single column, full-width fields and controls |
| Informational pages | Constrained measure with side navigation where present | Constrained measure | Single column | Single column, reduced section padding |
| Footer | 4 columns | 3 columns | 2 columns | 1 column, groups collapsible |

At every width and on every in-scope surface: no horizontal overflow, no clipped text, no header
collision, no overlapping floating controls, no tablet dead zone, no oversized empty region, stable
image dimensions, readable cards, usable filters, usable gallery, usable forms, reachable
navigation, and touch targets meeting §13.

---

## 9. Loading, Empty, Error, Disabled, and Success States

| Surface | Loading | Empty | Error | Disabled | Success |
| --- | --- | --- | --- | --- | --- |
| Product listing | Skeleton cards at final card dimensions | "No products match these filters" + clear-filters control | Retrievable failure message; filters preserved | Pagination edges at first/last page | n/a |
| Search results | Skeleton results; query echoed | "No results for <query>" + route into full range | Failure message; query preserved | n/a | n/a |
| Product detail | Reserved gallery and content regions | n/a (missing product → 404) | Failure message with a route back to the listing | Gallery controls absent for single-image products | n/a |
| Gallery | Reserved image box at the declared ratio | n/a | Proportioned placeholder + meaningful alternative text | Prev/next absent for single image | n/a |
| Saved products | Skeleton rows | "You have not saved any products yet" + route into range | Failure message; existing set preserved | n/a | Toast on save/remove |
| Quote request | Busy submit control; form locked | "No products in this request yet" + route into range | Field-level and form-level errors; entered values preserved | Submit disabled while busy | Confirmation only after the operation succeeds (CL-2) |
| Contact form | Busy submit control | n/a | Field-level and form-level errors; values preserved | Submit disabled while busy | Confirmation only after the operation succeeds (CL-2) |
| FAQ | n/a | n/a | n/a | n/a | n/a |
| Any page | n/a | n/a | Custom 404 and custom 500, both with working navigation and no internal detail | n/a | n/a |

Rules that apply to every row: a loading state reserves the final dimensions of what it replaces, so
nothing shifts when content arrives; a disabled control states why it is disabled where the reason
is not obvious; a success state appears only after the underlying operation reports success
(Constitution VI.4); an error state preserves the visitor's input and offers a next action.

---

## 10. Content and Asset Integrity

- **CI-1** Every visible claim traces to §2.3 verified evidence or is removed.
- **CI-2** Product names are the verified public display names. Invented names (RD-2) are forbidden.
- **CI-3** Product imagery comes from the 25 verified media assets, used in their declared roles.
- **CI-4** Only the five approved specification fields may be displayed, and only where populated.
- **CI-5** No price, currency, discount, stock figure, tax rate, or delivery term appears.
- **CI-6** No rating, review, review count, award, certification, press mention, partnership,
  customer count, sales figure, or trust badge appears.
- **CI-7** No warranty, guarantee, installation promise, or reply-time promise appears unless
  verified and supplied.
- **CI-8** ZAKEY's relationship to supplier-branded products is stated honestly wherever product
  origin could otherwise be misread.
- **CI-9** No visible text, alternative text, title, ARIA label, filename, or metadata contains
  "demo", "placeholder", "sample", "lorem", "Figma", "Jazzmin", "Spec Kit", "fixture", "agent", or
  any other internal development term.
- **CI-10** No placeholder image remains in an accepted build.
- **CI-11** Product images preserve their true aspect ratio — never stretched, squashed, or
  visibly degraded.
- **CI-12** Every image conveying meaning has alternative text naming what it shows; decorative
  images are marked decorative.
- **CI-13** Asset source, ownership, and licensing assumptions are recorded in an asset manifest
  produced during planning, including the supplier-branded status of product photography.
- **CI-14** Legacy content is reused where it is verified and relevant, copied out under the
  read-only constraint of Constitution IV.2.
- **CI-15** Where verified content for an in-scope surface does not exist, that surface and every
  link to it are removed together — never left as a dead link, and never filled with drafted text.

---

## 11. Reference-Fidelity Requirements

**Method.** Fidelity is reviewed by side-by-side comparison of the implementation against the
reference at 1440px, 1024px, 768px, and 390px, on the homepage, the listing page, and the product
page, plus one informational page for design-system consistency. Screenshots are captured at each
width and **inspected**, with observations recorded in the verification artifact — Constitution
XIII.6 states that capturing screenshots without inspecting them is not visual QA.

**Acceptance is structural, not pixel-level.** The reference is a prototype containing twelve
recorded defects (§2.2) that must not be reproduced. A comparison passes when all of the following
hold at every compared width:

- **RF-1 Visual hierarchy** — on each compared page the same element carries primary emphasis as in
  the reference, and the reading order of eyebrow → heading → supporting copy → action is preserved.
- **RF-2 Section order and rhythm** — retained sections appear in reference order; vertical rhythm
  between sections follows one spacing scale in multiples of 8px, matching the reference's density
  impression rather than an arbitrary value.
- **RF-3 Layout density** — the number of products per row at each width matches §8, and content
  measure stays within the reference's range rather than becoming noticeably sparser or denser.
- **RF-4 Product-card proportions** — every product card shares one media aspect ratio and one
  internal spacing pattern across every surface that renders one.
- **RF-5 Component language** — a component looks and behaves identically wherever it appears;
  divergence between two instances of the same component is a defect (Constitution XIII.5).
- **RF-6 Media ratios** — declared image ratios are stable across breakpoints; no image changes
  shape between widths.
- **RF-7 Navigation coherence** — the navigation model is consistent across every page; no page
  introduces a navigation pattern the rest of the storefront does not use.
- **RF-8 Premium character** — restrained palette, generous whitespace, restrained shadows, one
  typographic voice. Judged at the two visual critique passes required by Constitution XIII.3, not
  by implementer self-assessment.
- **RF-9 Hero composition** — the reference hero's structure is preserved; its image is replaced per
  RD-10; its eyebrow colour is corrected per RD-1.
- **RF-10 Documented deviations** — every deviation from the reference is either listed in the
  §2.2 defect table or recorded, with justification, in the plan. An undocumented deviation is a
  defect (Constitution XIII.7).
- **RF-11 Removed sections leave no scar** — where a fabricated section was removed (RD-4, RD-5,
  RD-6, RD-8, CF-7), the surrounding rhythm is re-closed; no oversized empty region remains.

---

## 12. Accessibility Requirements

Target: **WCAG 2.2 Level AA**. Every item is measurable.

- **A-1** Each page exposes one `main` landmark, plus banner, navigation, and contentinfo landmarks.
- **A-2** Each page has exactly one first-level heading; heading levels descend without skipping.
- **A-3** Every interactive control is reachable and operable by keyboard alone, in a tab order
  matching visual order.
- **A-4** Every focusable control shows a visible focus indicator meeting 3:1 contrast against its
  adjacent background.
- **A-5** A skip-to-content control is the first focusable element and moves focus to `main`.
- **A-6** Every icon-only control has a non-visual accessible name describing its action.
- **A-7** Every form field has a programmatically associated visible label. Placeholder text is
  never the only label.
- **A-8** Every validation message is programmatically associated with its field, and the field is
  marked invalid.
- **A-9** Text meets 4.5:1 contrast (3:1 for large text). Accent gold is never used for text,
  meaningful icons, or any element with a non-text contrast requirement on `#FFFFFF` or `#F8F9FB`
  (Constitution II.7).
- **A-10** Meaningful non-text elements, including control boundaries and focus indicators, meet 3:1.
- **A-11** Interactive targets are at least 24×24 CSS pixels; primary mobile actions are at least
  44×44.
- **A-12** Menus and disclosure controls expose expanded/collapsed state assistively.
- **A-13** Drawers and dialogs trap focus while open, close on Escape, and return focus to the
  control that opened them.
- **A-14** Content changes that occur without navigation — save toggles, filter results, toasts —
  are announced assistively without stealing focus.
- **A-15** Reduced-motion preference suppresses transitions, parallax, and any autoplaying movement.
- **A-16** Every meaningful image has alternative text describing what it shows; decorative images
  are hidden from assistive technology.
- **A-17** Each page declares its language and text direction on the root element.
- **A-18** Page titles are unique and describe the page.
- **A-19** Content remains usable and unclipped at 200% text scaling at every verification width.
- **A-20** Verification requires **both** an automated axe run with zero violations at the
  documented conformance level **and** a manual keyboard pass covering tab order, focus visibility,
  focus trapping, and dismissal. Constitution VIII.6: an automated pass alone is not verification.

---

## 13. Performance Budgets

Budgets are set before implementation (Constitution IX.7) and are measured on a production-mode
build. "Page weight" means total transferred bytes for an uncached first load, excluding
video.

| Budget | Target | Measured how |
| --- | --- | --- |
| PB-1 Page weight — homepage | ≤ 1,200 KB | Production build, uncached load |
| PB-2 Page weight — listing page | ≤ 1,000 KB | As above |
| PB-3 Page weight — product page | ≤ 1,200 KB | As above |
| PB-4 Page weight — informational page | ≤ 600 KB | As above |
| PB-5 JavaScript payload, shared | ≤ 100 KB compressed | Build output |
| PB-6 JavaScript payload, per page above shared | ≤ 30 KB compressed | Build output |
| PB-7 CSS payload | ≤ 80 KB compressed | Build output |
| PB-8 Largest Contentful Paint | ≤ 2.5 s | Production-like local run, mid-tier device profile |
| PB-9 Cumulative Layout Shift | ≤ 0.05 | As above |
| PB-10 Interaction to Next Paint | ≤ 200 ms | As above |
| PB-11 Console errors | 0 unexpected, on every in-scope page | Captured automatically during end-to-end verification |
| PB-12 Broken internal links | 0 | Automated internal link crawl |
| PB-13 Runtime third-party origins | 0 | Network trace of a production-mode load |
| PB-14 Media dimension reservation | 100% of images declare intrinsic dimensions or an aspect-ratio reservation | Automated template and DOM audit |
| PB-15 Below-the-fold images lazily loaded | 100%; above-the-fold hero image eagerly loaded | Automated DOM audit |
| PB-16 Fonts | Self-hosted, subset, with a font-display strategy that never hides text | Network trace + computed style check |
| PB-17 Production asset build | Succeeds with no error and no unresolved asset reference | Build command exit status |

No budget may be met by weakening accessibility, removing required content, or degrading visual
quality (Constitution IX.8).

---

## 14. Requirements *(mandatory)*

### Functional Requirements

#### Navigation and information architecture (FR-001 to FR-012)

- **FR-001**: The storefront MUST present one navigation architecture, identical in structure and
  behavior on every in-scope page.
- **FR-002**: The announcement bar MUST render only when verified announcement content exists in the
  centralized content source; when absent, every page MUST lay out correctly without it.
- **FR-003**: The header MUST provide the wordmark linking to the homepage, primary navigation to
  the product range and informational pages, a search entry point, and a saved-products entry point
  showing the current count.
- **FR-004**: At widths where the full navigation does not fit, the storefront MUST provide a
  dedicated mobile navigation surface — not a horizontally scrolling or truncated desktop bar.
- **FR-005**: The mobile navigation MUST open and close by pointer and keyboard, trap focus while
  open, close on Escape, and return focus to the control that opened it.
- **FR-006**: Search MUST be reachable from every in-scope page.
- **FR-007**: Breadcrumbs MUST appear on listing, category, collection, product, and informational
  pages, MUST reflect real ancestry, and MUST render the current page as non-interactive text.
- **FR-008**: The navigation item corresponding to the current section MUST be visibly marked and
  programmatically exposed as current.
- **FR-009**: Every navigation control MUST be operable by keyboard, in an order matching its visual
  order.
- **FR-010**: Every internal link MUST resolve to an existing page. No control may target `#` and no
  control may render without defined behavior.
- **FR-011**: The homepage MUST present, in order: hero, category showcase, featured products,
  value proposition, series showcase, enquiry call to action, footer — a single featured-products
  rail sourced from the verified `featured_products_slider` role (RD-11).
- **FR-012**: The footer MUST group links by purpose, MUST render a link only for a page that
  exists in this feature, and MUST NOT reproduce reference footer entries for surfaces that are
  deferred or excluded.

#### Product discovery (FR-013 to FR-028)

- **FR-013**: The listing page MUST make every verified product reachable and MUST state the number
  of results.
- **FR-014**: Category listing pages MUST exist for each of the three verified categories.
- **FR-015**: Collection listing pages MUST exist for each of the six verified collections.
- **FR-016**: Filtering MUST be offered by category, by collection, and by access method — the three
  facets for which verified data exists.
- **FR-017**: Price-range and minimum-rating filters MUST NOT be offered, because no verified price
  or rating data exists (RD-3, RD-4).
- **FR-018**: Filters MUST be combinable; results MUST satisfy every applied filter.
- **FR-019**: Every applied filter MUST be individually visible and individually removable.
- **FR-020**: A control MUST clear all filters at once and return the listing to its unfiltered
  state and address.
- **FR-021**: Filter, sort, and pagination state MUST be expressed in the page address so a result
  set can be shared and reloaded to the same state.
- **FR-022**: Sorting MUST offer only orderings derivable from verified data — featured order, name
  ascending, name descending. Popularity- and price-based sorts MUST NOT be offered (RD-3, RD-11).
- **FR-023**: Results MUST be paginated, with page controls disabled at the first and last page and
  the current page indicated.
- **FR-024**: When no products match, the storefront MUST show a no-results state that explains the
  outcome and offers a control that clears the filters.
- **FR-025**: At narrow widths, filters MUST be presented in a dedicated surface with focus
  management and Escape dismissal — not as a long list pushing results off-screen.
- **FR-026**: Search MUST match against verified product display names, model codes, categories, and
  collections; results MUST echo the query and state the result count.
- **FR-027**: A search with no matches MUST show a no-results state offering a route into the full
  range; an empty or whitespace-only query MUST NOT produce an error or a results page implying a
  search occurred.
- **FR-028**: Product cards MUST present identical structure and proportions wherever they appear —
  listing, category, collection, search results, related products, and homepage rails.

#### Product presentation (FR-029 to FR-041)

- **FR-029**: Products MUST be presented under their verified public display names only.
- **FR-030**: Product imagery MUST come from the verified media assets, used in their declared roles;
  the homepage hero image MUST be a verified ZAKEY smart-lock image (Constitution I.5, RD-10).
- **FR-031**: A product page MUST present name, imagery, category, collection where assigned, and
  access methods.
- **FR-032**: Product galleries MUST support multiple images with pointer, keyboard, and touch
  operation, MUST indicate the active image, and MUST NOT change the media region's dimensions
  between images.
- **FR-033**: A product with a single image MUST render without gallery navigation, rather than with
  disabled controls.
- **FR-034**: Pricing MUST be presented as a single consistent quote-only statement on every surface
  that references price, with no figure, no "from" price, and no currency (CI-5, CL-1).
- **FR-035**: Technical information MUST be limited to the five approved specification fields, and a
  field with no verified value MUST be omitted rather than shown empty.
- **FR-036**: Availability MUST be presented honestly as enquiry-based, with no stock count, no
  "in stock" claim, and no urgency signal.
- **FR-037**: Related products MUST share the viewed product's category or collection and MUST NOT
  include the viewed product.
- **FR-038**: Product badges MUST convey verified attributes only — category, collection, access
  method. Popularity, discount, award, and certification badges MUST NOT exist.
- **FR-039**: Product information MUST follow one hierarchy on every product page: identity, media,
  key attributes, action, detailed attributes, related products.
- **FR-040**: Where product origin could be misread, the storefront MUST state ZAKEY's relationship
  to supplier-branded products honestly (CI-8).
- **FR-041**: An unavailable product image MUST render a correctly proportioned placeholder region
  with meaningful alternative text — never a broken-image icon and never a distorted image.

#### Saved products and quote-led interactions (FR-042 to FR-053)

- **FR-042**: Visitors MUST be able to save and unsave products from product cards and product pages,
  with the control reflecting current state.
- **FR-043**: The saved-products count MUST be shown in the header and MUST stay accurate across
  navigation and reload within the visit.
- **FR-044**: The saved-products page MUST list saved products, allow removal, and offer a route into
  a quote request.
- **FR-045**: Saved products MUST persist for the duration of the visit without requiring an account.
- **FR-046**: No saved-products surface may describe the set as an order, a cart, a reservation, a
  held item, or anything implying a commercial commitment.
- **FR-047**: A saved entry whose product no longer exists MUST be dropped silently, with the count
  corrected and no error shown.
- **FR-048**: Visitors MUST be able to request a quote for one product from its product page and for
  several products from the saved-products page.
- **FR-049**: The quote request MUST show which products it covers and allow lines to be removed
  before submission.
- **FR-050**: The quote request MUST NOT display or compute a monetary total, subtotal, tax, or
  shipping amount.
- **FR-051**: No surface in this feature may request, transmit, log, or store a card number, expiry
  date, security code, PIN, or any payment credential (Constitution VI.9, RD-9).
- **FR-052**: A quote-request confirmation MUST appear only after the underlying operation reports
  success, and MUST NOT promise a reply time, price, availability, or delivery unless verified
  (Constitution VI.4; CL-2).
- **FR-053**: Every rendered commerce-facing control MUST have real defined behavior; any control
  whose behavior belongs to a deferred feature MUST NOT be rendered.

#### Forms (FR-054 to FR-063)

- **FR-054**: Every form field MUST have a visible, programmatically associated label; a placeholder
  MUST NOT serve as the only label.
- **FR-055**: Every state-changing form MUST be validated server-side; client-side validation is
  assistance only (Constitution X.5).
- **FR-056**: Invalid submissions MUST produce field-level messages, programmatically associated
  with their fields, plus a form-level summary when more than one field is invalid.
- **FR-057**: On an invalid submission, focus MUST move to the first invalid field and the visitor's
  entered values MUST be preserved.
- **FR-058**: Submit controls MUST enter a busy state during submission and MUST prevent duplicate
  submission.
- **FR-059**: A success state MUST appear only after the underlying operation reports success.
- **FR-060**: A failed submission MUST show an honest failure message, preserve entered values, and
  offer a retry.
- **FR-061**: Every form MUST be fully completable by keyboard alone.
- **FR-062**: Every form MUST be usable at 390px, with full-width fields, no horizontal overflow, and
  controls meeting the touch-target requirement.
- **FR-063**: Forms MUST NOT state a destination, recipient, reply time, or delivery promise that is
  not verified.

#### Informational content (FR-064 to FR-070)

- **FR-064**: All visible copy MUST be truthful, product-relevant, and written in the conservative
  voice evidenced in the legacy content.
- **FR-065**: Verified legacy content MUST be reused where it is relevant and accurate.
- **FR-066**: Any claim not traceable to verified evidence MUST be removed or rewritten
  conservatively.
- **FR-067**: The About page MUST describe ZAKEY truthfully, including its relationship to the
  supplier-branded products it offers.
- **FR-068**: The Contact page MUST offer a working enquiry form; it MUST show contact details only
  where those details are verified (CL-3).
- **FR-069**: The FAQ MUST present question-and-answer content that is individually expandable,
  keyboard-operable, and assistively labelled with its expanded state.
- **FR-070**: Privacy and Terms pages MUST render verified ZAKEY legal text or MUST be removed
  together with every link that points at them (CI-15, CL-3).

#### Content source and architecture (FR-071 to FR-078)

- **FR-071**: All temporary storefront data MUST be served from exactly one centralized structured
  source or adapter (Constitution IV.7).
- **FR-072**: No product, category, collection, or business record may be independently hardcoded in
  a template; two templates needing the same record MUST read it from the one source
  (Constitution IV.8).
- **FR-073**: The centralized source MUST be replaceable by database-backed content without
  rewriting public templates.
- **FR-074**: The specification MUST remain technology-agnostic about the eventual persistence
  mechanism; the seam, not the storage engine, is what this feature fixes.
- **FR-075**: Shared components MUST have exactly one implementation reused across pages
  (Constitution IV.4).
- **FR-076**: Design tokens MUST come from one source of truth matching the ratified values exactly;
  no template or script may introduce a competing colour, type size, spacing value, radius, shadow,
  or breakpoint (Constitution II.2, II.3).
- **FR-077**: Internal navigation MUST resolve through named route lookups rather than hardcoded
  paths (Constitution VI.5).
- **FR-078**: The architecture MUST support later localization and right-to-left layout —
  externalized strings and direction-aware layout primitives — without exposing a language selector
  or a right-to-left interface in this feature (Constitution IV.9).

#### Cross-cutting states (FR-079 to FR-090)

- **FR-079**: Every deferred-content region MUST show a loading state that reserves the final
  dimensions of the content it replaces.
- **FR-080**: Every reachable empty state MUST explain the situation and offer a next action.
- **FR-081**: Every reachable error state MUST explain the failure without exposing internal detail
  and MUST offer a next action.
- **FR-082**: Every disabled control MUST be visibly and programmatically disabled, with the reason
  stated where it is not self-evident.
- **FR-083**: Transient confirmations MUST be announced assistively without moving focus.
- **FR-084**: The storefront MUST provide a custom 404 page with working navigation and no internal
  detail.
- **FR-085**: The storefront MUST provide a custom 500 page with working navigation, no stack trace,
  and no internal detail.
- **FR-086**: Requests for unknown categories, collections, or products MUST reach the custom 404
  page rather than an unhandled error.
- **FR-087**: Visitor-supplied text echoed back to the page MUST be escaped and never rendered as
  markup (Constitution X.6).
- **FR-088**: Pagination beyond the last page MUST return a defined response and return the visitor
  to a valid page.
- **FR-089**: Core navigation, product discovery, product detail, and informational content MUST
  remain usable when JavaScript is unavailable; controls that genuinely require scripting MUST NOT
  render as inert.
- **FR-090**: Every page MUST render correctly with the announcement bar both present and absent,
  and with the saved-products set both empty and populated.

### Non-Functional Requirements

#### Visual fidelity and design system (NFR-001 to NFR-006)

- **NFR-001**: The storefront MUST satisfy RF-1 through RF-11 at 1440px, 1024px, 768px, and 390px.
- **NFR-002**: Every page MUST belong to one ZAKEY design system; page-specific visual identities are
  forbidden (Constitution I.7).
- **NFR-003**: Implemented token values MUST match the ratified table exactly: primary navy
  `#0D1B3D`, accent gold `#C9A227`, background `#F8F9FB`, white `#FFFFFF`, primary text `#1F2937`,
  Poppins self-hosted, 8px base spacing unit, 12px primary radius, 1440px desktop reference,
  12-column desktop grid, restrained shadows.
- **NFR-004**: Spacing MUST be a multiple of 8px unless a deliberate optical correction is recorded
  in the plan (Constitution II.6).
- **NFR-005**: The storefront MUST NOT introduce dark mode, accidental dark-theme sections, excessive
  gradients or glassmorphism, random decorative elements, arbitrary spacing, oversized empty areas,
  repetitive promotional sections, or excessive animation (Constitution II.5).
- **NFR-006**: Repeated components MUST be compared across pages for dimensions, spacing, colour,
  typography, focus state, responsive behavior, and interaction behavior; divergence is a defect.

#### Responsive (NFR-007 to NFR-013)

- **NFR-007**: Every in-scope page and shared component MUST be designed and verified at all four
  widths.
- **NFR-008**: Each width MUST receive a deliberate layout decision per §8; stacking desktop columns
  is not sufficient.
- **NFR-009**: Document scroll width MUST NOT exceed viewport width at any of the four widths,
  verified programmatically (Constitution VII.4).
- **NFR-010**: No clipped text, header collision, floating-control overlap, tablet dead zone, or
  oversized empty region at any of the four widths.
- **NFR-011**: Image dimensions MUST be stable across breakpoints; declared ratios MUST NOT change.
- **NFR-012**: Mobile navigation, filters, gallery, forms, and the quote-request surface MUST each
  have dedicated responsive behavior.
- **NFR-013**: Content MUST remain usable and unclipped at 200% text scaling at every width.

#### Accessibility (NFR-014 to NFR-024)

- **NFR-014**: A-1 through A-19 MUST hold on every in-scope page.
- **NFR-015**: An automated axe run MUST report zero violations at the documented conformance level
  on every in-scope page and on each interactive surface in its open state.
- **NFR-016**: A manual keyboard inspection MUST cover tab order, focus visibility, focus trapping,
  and dismissal on every interactive surface, with observations recorded.
- **NFR-017**: Accent gold MUST NOT be used for text, meaningful icons, or elements bearing a
  non-text contrast requirement on `#FFFFFF` or `#F8F9FB`.
- **NFR-018**: Interactive targets MUST meet 24×24 CSS pixels minimum; primary mobile actions 44×44.
- **NFR-019**: Drawers and dialogs MUST trap focus, close on Escape, and restore focus to the opener.
- **NFR-020**: Reduced-motion preference MUST suppress transitions and autoplaying movement.
- **NFR-021**: Every meaningful image MUST have descriptive alternative text; decorative images MUST
  be hidden assistively.
- **NFR-022**: Every page MUST declare language and text direction.
- **NFR-023**: Page titles MUST be unique and descriptive.
- **NFR-024**: Dynamic content changes MUST be announced assistively without stealing focus.

#### Performance (NFR-025 to NFR-033)

- **NFR-025**: PB-1 through PB-4 page-weight budgets MUST be met.
- **NFR-026**: PB-5 through PB-7 asset budgets MUST be met.
- **NFR-027**: PB-8 through PB-10 Core Web Vitals targets MUST be met on a production-like run.
- **NFR-028**: Zero unexpected console errors on every in-scope page, captured automatically.
- **NFR-029**: Zero broken internal links, verified by an automated crawl.
- **NFR-030**: Every image MUST declare intrinsic dimensions or an aspect-ratio reservation.
- **NFR-031**: Below-the-fold imagery MUST be lazily loaded; the hero image eagerly loaded.
- **NFR-032**: Fonts and icons MUST be served locally; no runtime third-party origin may appear in a
  production-mode network trace.
- **NFR-033**: The production asset build MUST succeed with no error and no unresolved asset
  reference.

#### Architecture and quality (NFR-034 to NFR-038)

- **NFR-034**: Temporary storefront data MUST be isolated behind one adapter, replaceable without
  template changes.
- **NFR-035**: JavaScript MUST be organized as focused modules; a single oversized script or
  stylesheet MUST NOT become the architecture (Constitution IV.6).
- **NFR-036**: No legacy frontend implementation, template, stylesheet, script, or design system may
  be copied into this repository (Constitution IV.1).
- **NFR-037**: No Figma runtime code may be copied or adapted (Constitution III.2).
- **NFR-038**: The legacy repository MUST remain unmodified throughout implementation and
  verification (Constitution IV.2).

#### Security and privacy (NFR-039 to NFR-042)

- **NFR-039**: Every state-changing request MUST carry active cross-site request forgery protection
  (Constitution X.4).
- **NFR-040**: All visitor-supplied data MUST be validated server-side (Constitution X.5).
- **NFR-041**: No payment credential may be requested, transmitted, logged, or stored
  (Constitution VI.9).
- **NFR-042**: Logs MUST NOT contain personal information beyond what the feature requires, and
  never a credential (Constitution X.9).

### Key Entities

- **Product** — a verified item ZAKEY offers. Attributes: public display name, summary, product
  type, supplier brand, supplier relationship, category, collections, access methods, media
  assignments with roles and order, approved specification fields, commerce mode, permitted public
  actions. Carries no price, stock, rating, or warranty value.
- **Category** — a verified grouping by lock technology. Attributes: name, slug. Relationship: one
  category has many products; a product has exactly one category.
- **Collection (series)** — a verified product family. Attributes: name, slug. Relationship: many to
  many with products; a product may have none.
- **Access method** — a verified unlock capability used as a discovery facet. Attributes: name, slug.
  Relationship: many to many with products.
- **Media asset** — a verified image. Attributes: identifier, roles, sort order, intrinsic
  dimensions, alternative text. Relationship: many to many with products through role-carrying
  assignments.
- **Saved-products set** — the visitor's visit-scoped shortlist. Attributes: product references,
  time added. Not an order and not a commitment.
- **Quote request** — a visitor's expression of interest. Attributes: contact details, message,
  requested product lines with quantities, submission state. Carries no monetary value.
- **Enquiry** — a general contact submission. Attributes: contact details, subject, message,
  submission state.
- **Announcement** — optional verified site-wide message. Attributes: message text, optional link.

---

## 15. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 17 in-scope surfaces render at all four verification widths with no unhandled
  error.
- **SC-002**: 100% of the 21 verified products are reachable from the listing page by browsing
  alone.
- **SC-003**: 100% of interactive controls in the §7 inventory perform their defined behavior; zero
  inert controls and zero controls targeting `#`, verified by an automated control audit plus manual
  inspection.
- **SC-004**: Zero broken internal links across every in-scope page, verified by an automated crawl.
- **SC-005**: Every shared component family in §6 is implemented once and reused; zero duplicated
  implementations, verified by inspection during code review.
- **SC-006**: Repeated components render identically across pages on the compared attributes; zero
  divergences recorded at the second visual critique pass.
- **SC-007**: Reference-fidelity comparison passes RF-1 through RF-11 on the homepage, listing page,
  product page, and one informational page at all four widths, with inspected-screenshot
  observations recorded for each.
- **SC-008**: Document scroll width does not exceed viewport width on any in-scope page at 1440px,
  1024px, 768px, or 390px — zero failures across the programmatic check.
- **SC-009**: Zero instances of clipped text, header collision, floating-control overlap, tablet
  dead zone, or oversized empty region at any verification width.
- **SC-010**: Every in-scope page passes an automated axe run with zero violations at the documented
  conformance level.
- **SC-011**: A manual keyboard pass completes every in-scope journey — browse, filter, search,
  inspect a product, save, request a quote, submit contact — using the keyboard alone, with
  observations recorded.
- **SC-012**: 100% of focusable controls show a visible focus indicator meeting 3:1 contrast.
- **SC-013**: 100% of interactive targets meet 24×24 CSS pixels; 100% of primary mobile actions meet
  44×44.
- **SC-014**: Zero uses of accent gold as text, as a meaningful icon, or on any element bearing a
  non-text contrast requirement over `#FFFFFF` or `#F8F9FB`.
- **SC-015**: Filtering by any single facet returns only products carrying that facet — 100%
  precision across all 15 verified facet values.
- **SC-016**: Filter, sort, and pagination state reloads to an identical result set from its address
  in 100% of tested combinations.
- **SC-017**: A search for each verified model code returns that product within the first page of
  results in 100% of cases.
- **SC-018**: No-results states appear for zero-match filter combinations and zero-match searches in
  100% of tested cases, each offering a working recovery control.
- **SC-019**: A content audit of every visible string finds zero prices, currencies, discounts,
  stock figures, ratings, review counts, awards, certifications, press mentions, customer counts,
  warranty claims, or delivery promises.
- **SC-020**: A content audit finds zero occurrences of internal terminology in visible copy,
  alternative text, titles, ARIA labels, visible filenames, or metadata.
- **SC-021**: 100% of displayed product names, images, and specification fields match the verified
  catalog; zero invented product identities.
- **SC-022**: Zero fields anywhere in the feature collect a card number, expiry date, security code,
  or PIN.
- **SC-023**: Every success state in the feature is preceded by a confirmed successful underlying
  operation; zero success states appear on a failed or absent operation, verified by fault
  injection.
- **SC-024**: Every form rejects an invalid submission server-side with field-level messages
  programmatically associated with their fields — 100% of tested invalid cases.
- **SC-025**: Zero unexpected console errors on any in-scope page, captured automatically during
  end-to-end verification.
- **SC-026**: Page-weight budgets PB-1 through PB-4 and asset budgets PB-5 through PB-7 are met on a
  production build.
- **SC-027**: Core Web Vitals targets PB-8 through PB-10 are met on a production-like run.
- **SC-028**: 100% of images declare intrinsic dimensions or an aspect-ratio reservation; 100% of
  below-the-fold images are lazily loaded.
- **SC-029**: A production-mode network trace shows zero third-party origins.
- **SC-030**: The production asset build succeeds with no error and no unresolved asset reference.
- **SC-031**: All temporary storefront data is served from exactly one adapter; zero product,
  category, collection, or business records are hardcoded in templates, verified by search.
- **SC-032**: The legacy repository is byte-identical before and after the feature, verified by a
  clean status check and an unchanged HEAD.
- **SC-033**: Every deferred capability in §19 has zero rendered controls in the accepted interface,
  verified by the §7 control audit.
- **SC-034**: Every requirement in §14 maps to at least one success criterion or acceptance scenario
  in §21, with zero unmapped requirements.

---

## 16. Assumptions

1. `/media/mekky/work/backend/zakey.v1` is the genuine legacy ZAKEY project; the originally
   requested `/media/mekky/work/backend/zakey` does not exist. User confirmation is still required
   by the constitution's own TODO (RRP-1).
2. The verified launch catalog (21 products, 3 categories, 6 collections, 6 access methods, 25 media
   assets) is the complete approved product set for this feature. No other product or media asset is
   approved.
3. The quote-led model (CL-1 default A) governs this specification. If the user answers (B), cart,
   checkout, and confirmation return to scope and verified pricing becomes a hard dependency.
4. Quote and enquiry submissions persist to a real store and confirm only on a confirmed write
   (CL-2 default B). Email and messaging delivery are out of scope regardless.
5. Product comparison is excluded — no reference or legacy evidence supports it (CF-6).
6. Saved products are visit-scoped and require no account; they are not an order or a reservation.
7. Where verified content for a surface does not exist, the surface and its links are removed
   together rather than filled with drafted text (CI-15).
8. Currency, tax, and shipping are absent from this feature entirely, because no verified values
   exist.
9. Visitors are anonymous. No account, sign-in, or persistent profile exists in this feature.
10. Storefront content is presented in English in this feature; the architecture stays ready for
    later localization and right-to-left layout, with no language selector exposed
    (Constitution IV.9).
11. The reference's single-route prototype nature means it supplies no URL structure; this feature
    defines its own addressing.
12. Reference defects RD-1 through RD-12 are defects, not requirements, and are corrected as
    recorded.
13. The reference is a stable artifact for the duration of this feature; if it changes materially,
    §2.2 must be re-inspected and this specification amended.

---

## 17. Dependencies

1. **Ratified constitution v1.0.0** — governs every requirement here.
2. **Verified legacy catalog** — `specs/012-smart-storefront-commerce/data/curated-launch-catalog.v2.json`
   in the legacy repository, read-only.
3. **Verified brand assets** — ZAKEY logo files in the legacy repository's `static/brand/` and
   `static/icons/`, read-only.
4. **Verified product imagery** — legacy `reference-imports/spec-012/`, read-only. Images must be
   assessed for resolution and cropping suitability during planning.
5. **Verified hero image** — a high-quality ZAKEY smart-lock image satisfying Constitution I.5. If
   none of the verified imagery is suitable at hero scale, this becomes an implementation blocker to
   raise, not a reason to ship the reference's unsuitable image.
6. **Verified contact details** — required before the Contact page renders a contact block (CL-3).
7. **Verified legal text** — required before Privacy and Terms pages ship (CL-3, FR-070).
8. **Verified announcement content** — required before the announcement bar renders (FR-002).
9. **Approved stack** — as recorded in the constitution's Canonical Project Facts. Selection and
   configuration belong to `/speckit-plan`, not to this specification.
10. **Repository readiness** — the blockers in §18 must be resolved before implementation.

---

## 18. Repository Readiness Preconditions

These are verified repository-hygiene and governance findings, **not** storefront product
requirements. Each was independently confirmed locally on 2026-07-31 on branch `main` at HEAD
`0bff29e`. None was fixed during this invocation, as instructed.

| # | Finding | Verified | Severity | Must be resolved before |
| --- | --- | --- | --- | --- |
| RRP-1 | The constitution carries an open TODO requiring the user to confirm that `zakey.v1` is the authoritative legacy repository. Confirmed locally: `/media/mekky/work/backend/zakey` does not exist; `zakey.v1` exists and is the genuine Django project (HEAD `5fdd81d`) | Yes | **Blocker** | Any asset or content extraction |
| RRP-2 | No `.gitignore` exists at the repository root | Yes — `ls` reports no such file | **Blocker** | First implementation commit. Constitution XV.6 requires ignore coverage for secrets, databases, media, test recordings, screenshots, dependency caches, and build artifacts |
| RRP-3 | `node_modules/` is tracked in Git — 4,571 files | Yes — `git ls-files node_modules \| wc -l` → 4571 | **Blocker** | First implementation commit. Compounds RRP-2 |
| RRP-4 | `.specify/init-options.json` and `.specify/integration.json` both declare Kimi as the integration and default integration, while Claude Spec Kit skills are installed and in use | Yes — both files read | **Blocker** | `/speckit-plan`. Constitution XVI.1 makes Claude Code the project owner; the recorded configuration contradicts the governing principle |
| RRP-5 | `spec-template.md` lacks the out-of-scope section, UI inventory, performance budgets, and reference-fidelity method the constitution requires — this specification supplied all four manually | Yes — template read in full | High | Next specification, so the gap is not re-created |
| RRP-6 | `plan-template.md`'s Constitution Check is a bare placeholder with no per-principle gate table | Yes — recorded in the constitution's sync-impact report and confirmed by file listing | **Blocker** | `/speckit-plan`. Constitution XI.4 requires an explicit per-principle check |
| RRP-7 | `tasks-template.md` states tests are optional unless requested, contradicting Constitution XII, and lacks visual-QA and accessibility task categories | Yes — recorded in the sync-impact report | **Blocker** | `/speckit-tasks` |
| RRP-8 | `checklist-template.md` is not aligned with the fifteen conditions of Constitution XVIII | Yes — template read in full | High | `/speckit-checklist` |
| RRP-9 | `README.md` is empty (0 bytes) and `main.py` is a generated Hello World entry point; no Django project exists | Yes — `wc -c` → 0; file read | Medium | Acceptance. Constitution XVIII.12 requires current documentation |
| RRP-10 | No verified ZAKEY contact details or legal text exist in either repository; legacy contact values are placeholders (`+1 (000) 000-0000`, `+201234567890`) | Yes — text search of legacy templates and configuration | **Blocker for the affected surfaces only** | Contact-details block, Privacy page, Terms page (CL-3) |

Ten findings recorded; seven are blockers, one is a scoped blocker, two are lower severity.

---

## 19. Explicit Out of Scope

Each item below is deferred, with the future specification that owns it named. Constitution VI.2
means none of these may render a control in the accepted interface.

| Capability | Owning future specification |
| --- | --- |
| Production product database and catalog management | Feature 002 — Commerce Foundation |
| Cart, checkout, order review, order confirmation | Feature 002 — Commerce Foundation |
| Production inventory management | Feature 002 — Commerce Foundation |
| Retail pricing, currency, tax, discounts | Feature 002 — Commerce Foundation |
| Shipping, returns, and warranty information pages | Feature 002 — Commerce Foundation |
| Shipping-provider integration | Feature 002 — Commerce Foundation |
| Tax integration | Feature 002 — Commerce Foundation |
| Payment gateway integration and any card collection | Feature 002 — Commerce Foundation |
| Production order management | Feature 002 — Commerce Foundation |
| Persistent customer accounts, authentication, order history, saved addresses | Feature 003 — Customer Accounts |
| Email and messaging notification delivery | Feature 004 — Marketing and Notifications |
| Newsletter subscription | Feature 004 — Marketing and Notifications |
| Django Admin customization | Feature 005 — Merchant Administration |
| Merchant CMS capabilities | Feature 005 — Merchant Administration |
| Staff roles and permissions | Feature 005 — Merchant Administration |
| Landing-page template management | Feature 005 — Merchant Administration |
| Analytics integration | Feature 006 — Analytics and Measurement |
| Deployment and production infrastructure | Feature 007 — Deployment and Operations |
| Multilingual content population, visible language switcher, visible right-to-left interface | Feature 008 — Localization |
| Affiliate features | Feature 009 — Partner and Affiliate Programme |
| Product comparison | Excluded — no supporting evidence (CF-6) |

**Explicitly retained, not deferred**: architecture readiness for later localization and
right-to-left layout (FR-078). The capability is deferred; the readiness is required now.

---

## 20. Constitution Compliance

| Principle | How this specification complies |
| --- | --- |
| I. Reference-Led Visual Fidelity | §2.2 records reference evidence and twelve defects; §11 defines RF-1–RF-11 with named pages, widths, and acceptance method; RD-10 preserves the hero composition and replaces its image |
| II. Permanent ZAKEY Brand System | NFR-003 fixes the ratified tokens; NFR-004 the 8px rhythm; FR-076 the single token source; NFR-017 and A-9 enforce the accent-gold restriction, correcting reference defect RD-1 |
| III. Approved Technical Foundation | NFR-032 forbids runtime third-party origins; PB-13 measures it; NFR-037 forbids copied Figma runtime code; stack selection is deferred to `/speckit-plan` |
| IV. Clean-Room Architecture | NFR-036 forbids copying legacy frontend code; NFR-038 and SC-032 hold the legacy repository read-only; FR-071–FR-075 mandate one data adapter and one implementation per component; FR-078 preserves localization readiness |
| V. Content and Asset Integrity | §10 CI-1–CI-15; RD-2–RD-8 remove every fabricated claim in the reference; SC-019–SC-021 measure it |
| VI. Functional Completeness | §7 gives every control defined behavior; FR-010 forbids dead controls and `#`; FR-052 and FR-059 forbid fake success; FR-051 forbids card data; FR-053 removes controls belonging to deferred features; FR-077 requires named route lookups |
| VII. Responsive Design | §8 gives every surface a deliberate layout at all four widths; NFR-007–NFR-013; SC-008 and SC-009 measure it |
| VIII. Accessibility | §12 A-1–A-20; NFR-014–NFR-024; SC-010–SC-014; A-20 requires both automated axe and a manual keyboard pass |
| IX. Performance and Frontend Quality | §13 PB-1–PB-17 set before implementation; NFR-025–NFR-033; SC-025–SC-030 |
| X. Security, Privacy, and Data Safety | NFR-039–NFR-042; FR-055 server-side validation; FR-087 escaping; FR-051 no payment credentials |
| XI. Specification-First Development | This document precedes planning; §19 states what is out of scope; §3 records three material ambiguities for `/speckit-clarify`; §21 gives traceability |
| XII. Test-First Acceptance | §15 defines 34 measurable criteria before implementation; SC-023 requires fault injection; verification methods are named per budget and per criterion |
| XIII. Visual QA and Consistency | §5–§9 supply the page, component, interaction, responsive, and state inventories; §11 requires inspected screenshots at three widths minimum and two critique passes; NFR-006 and SC-006 make cross-page divergence a defect |
| XIV. Code Quality | Deferred to `/speckit-plan` and `/speckit-tasks` by nature; NFR-035 constrains the JavaScript architecture at the specification level |
| XV. Git and Repository Safety | A separate local numeric branch was created; no commit, push, pull request, merge, remote change, or history rewrite occurred; §18 records ignore-policy blockers RRP-2 and RRP-3 without fixing them |
| XVI. Claude Code Governance | Specification authored and owned by Claude Opus; no delegation occurred; RRP-4 records the contradicting integration configuration |
| XVII. LeanCtx and Context Discipline | Inspection was targeted and evidence-driven; all evidence, decisions, and blockers are written into this artifact rather than left in conversation |
| XVIII. Definition of Done | §15 plus §21 make every requirement traceable to a criterion; §21 records known blockers truthfully; the fifteen conditions govern acceptance of the implementation, not of this specification |

---

## 21. Requirement-to-Success-Criterion Traceability

Every functional and non-functional requirement maps to at least one success criterion (SC) or
acceptance scenario (US*n*.*m*). Zero requirements are unmapped.

| Requirements | Mapped to |
| --- | --- |
| FR-001, FR-003, FR-008 | SC-001, SC-003, US1.3 |
| FR-002, FR-090 | SC-001, SC-003 |
| FR-004, FR-005 | SC-001, SC-011, US1.5 |
| FR-006 | SC-017, US5.1 |
| FR-007 | SC-001, US2.1, US3.1 |
| FR-009 | SC-011, SC-012 |
| FR-010, FR-012 | SC-003, SC-004, US1.3, US7.1 |
| FR-011 | SC-007, US1.2 |
| FR-013, FR-014, FR-015 | SC-001, SC-002, US2.1 |
| FR-016, FR-018 | SC-015, US2.2, US2.3 |
| FR-017, FR-022 | SC-019, SC-003 |
| FR-019, FR-020 | SC-018, US2.3, US2.5 |
| FR-021 | SC-016, US2.2, US2.7, US5.5 |
| FR-023, FR-088 | SC-001, SC-016 |
| FR-024, FR-027 | SC-018, US2.4, US5.3, US5.4 |
| FR-025 | SC-009, SC-011, US2.6 |
| FR-026 | SC-017, US5.2 |
| FR-028 | SC-006, SC-007 |
| FR-029, FR-030, FR-035, FR-038 | SC-021, SC-019, US3.1, US3.3 |
| FR-031, FR-039 | SC-001, US3.1 |
| FR-032, FR-033 | SC-011, US3.2 |
| FR-034, FR-036 | SC-019, US3.4 |
| FR-037 | SC-001, US3.5 |
| FR-040 | SC-019, US7.2 |
| FR-041 | SC-028, SC-020 |
| FR-042, FR-043, FR-045 | SC-003, US4.1, US4.2 |
| FR-044 | SC-001, US4.3, US4.4 |
| FR-046, FR-050 | SC-019, US4.5 |
| FR-047 | SC-003, US4.* (edge case) |
| FR-048, FR-049 | SC-001, US4.4, US6.* |
| FR-051 | SC-022, US6.5 |
| FR-052, FR-059 | SC-023, US6.3, US6.6 |
| FR-053 | SC-003, SC-033 |
| FR-054 | SC-010, SC-024, US6.1 |
| FR-055, FR-056 | SC-024, US6.1, US6.2 |
| FR-057, FR-060 | SC-024, US6.4 |
| FR-058 | SC-023, US6.3 |
| FR-061 | SC-011 |
| FR-062 | SC-008, SC-013 |
| FR-063, FR-064, FR-065, FR-066 | SC-019, SC-020 |
| FR-067 | SC-019, US7.2 |
| FR-068, FR-070 | SC-004, SC-019, US7.1 |
| FR-069 | SC-010, SC-011, US7.3 |
| FR-071, FR-072, FR-073, FR-074 | SC-031 |
| FR-075 | SC-005, SC-006 |
| FR-076 | SC-007, SC-014 |
| FR-077 | SC-004 |
| FR-078 | SC-001 (architecture readiness reviewed at plan gate) |
| FR-079 | SC-027 (layout stability), SC-028 |
| FR-080, FR-081 | SC-018, SC-001 |
| FR-082 | SC-003, SC-010 |
| FR-083 | SC-010, SC-011 |
| FR-084, FR-085, FR-086 | SC-001, SC-004 |
| FR-087 | SC-019 (content audit), edge case |
| FR-089 | SC-003, SC-025 |
| NFR-001, NFR-002 | SC-007 |
| NFR-003, NFR-004, NFR-005 | SC-007, SC-014 |
| NFR-006 | SC-006 |
| NFR-007, NFR-008 | SC-001, SC-007, SC-009 |
| NFR-009 | SC-008 |
| NFR-010 | SC-009 |
| NFR-011 | SC-007, SC-028 |
| NFR-012 | SC-009, SC-011 |
| NFR-013 | SC-009 |
| NFR-014 | SC-010, SC-011 |
| NFR-015 | SC-010 |
| NFR-016 | SC-011 |
| NFR-017 | SC-014 |
| NFR-018 | SC-013 |
| NFR-019, NFR-020, NFR-024 | SC-010, SC-011 |
| NFR-021 | SC-020, SC-010 |
| NFR-022, NFR-023 | SC-010 |
| NFR-025, NFR-026 | SC-026 |
| NFR-027 | SC-027 |
| NFR-028 | SC-025 |
| NFR-029 | SC-004 |
| NFR-030, NFR-031 | SC-028 |
| NFR-032 | SC-029 |
| NFR-033 | SC-030 |
| NFR-034 | SC-031 |
| NFR-035 | SC-026, SC-031 |
| NFR-036, NFR-037 | SC-031, SC-032 |
| NFR-038 | SC-032 |
| NFR-039, NFR-040 | SC-024 |
| NFR-041 | SC-022 |
| NFR-042 | SC-022 |

**Coverage**: 90 functional requirements and 42 non-functional requirements — 132 total — all mapped.
34 success criteria, all reachable from at least one requirement.

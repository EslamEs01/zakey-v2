# Feature Specification: ZAKEY Premium Public Storefront Experience

**Feature Branch**: `001-premium-storefront-experience`
**Feature Number**: `001`
**Created**: 2026-07-31
**Last clarified**: 2026-07-31
**Status**: Clarified — 0 clarifications outstanding
**Constitution**: ZAKEY Premium Smart Lock Storefront Constitution v1.1.0 (ratified 2026-07-31, amended 2026-07-31)
**Input**: User description: "Create the first complete feature specification for the new ZAKEY platform — the complete, coherent public storefront frontend covering the shared visual system, public product-discovery experience, public informational pages, responsive behavior, interactions, accessibility, content integrity, and the boundaries between this frontend specification and future commerce/backend specifications."

---

## 1. Purpose and Product Outcome

ZAKEY is a **premium retailer** of smart door locks and smart-home access products. It needs one
coherent public storefront that presents the range it sells with the premium, modern, minimal,
elegant, trustworthy, technical character established by the approved visual reference — and that
tells the truth about every product it shows, including who made it.

**Product outcome.** A visitor arriving with no prior knowledge of ZAKEY can, within a single
session and without an account:

1. understand what ZAKEY offers and who it is for,
2. browse the complete verified product range,
3. narrow that range by category, series, and access method,
4. search for a specific model,
5. inspect an individual product's verified imagery, verified attributes, and true supplier
   attribution,
6. save products of interest to a wishlist that survives their whole visit,
7. add products to a cart that survives their whole visit,
8. supply their contact and delivery information through checkout,
9. reach a validated order-review state that truthfully shows what they selected and what ZAKEY
   can and cannot yet confirm,
10. start a genuine commercial conversation from that state,
11. read ZAKEY's public informational content,

on a phone, a tablet, or a desktop, using a mouse, a keyboard, or a screen reader, without ever
encountering a control that does nothing, a claim ZAKEY cannot substantiate, or a success message
for something that did not happen.

**Where this feature stops.** Checkout ends at a **validated order-review state**. Feature 001 does
not create a production order, does not claim an order was submitted, does not show an order-success
state, does not collect card details, does not simulate payment, does not integrate a payment
gateway, and does not persist customer accounts. Those belong to Feature 002 and Feature 003, named
in [§19 Explicit Out of Scope](#19-explicit-out-of-scope).

**Why the boundary sits exactly there.** The cart, the wishlist, checkout information collection,
and order review are all genuinely buildable and genuinely useful today — they hold real state for
the visitor's session and every control in them does a real thing. Order *creation* is not: it
requires persistent catalog, inventory, customer, and order records that Feature 002 owns, and
payment requires a gateway that Feature 002 integrates. Constitution VI.4 forbids showing a success
state for an operation that did not occur, so Feature 001 renders no control that claims to place an
order.

**Why prices behave the way they do.** Every product in the authoritative catalog currently carries
`retail_price: null` (see [§2.3](#23-legacy-repository-evidence)). Constitution VI.8 requires
commerce totals to originate from authoritative data and V.4 requires untraceable claims to be
removed, so this storefront never invents a price. A product with a verified sellable price shows it
and contributes to totals; a product without one is shown honestly as priced on request and produces
no monetary total. The storefront is built so that supplying verified prices later turns the
existing surfaces on without redesigning them.

---

## 2. Authoritative Sources and Evidence

Constitution Principle I makes the visual reference the primary **visual** authority — for visual
direction, composition, hierarchy, spacing, and interaction character. It is **not** an authority on
product facts, business claims, routing, or application architecture. Principle V makes verified
legacy content the primary **content** authority. Where the two conflict on a matter of fact,
Principle V wins; where they conflict on a matter of appearance, Principle I wins, except where the
reference is itself defective. Every such conflict found during inspection is recorded below and
resolved explicitly.

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

**Consequence.** This tells us what the reference *contains*, not how ZAKEY must be addressed. The
reference is evidence for *composition, hierarchy, density, rhythm, component language, and section
order*. It carries **no authority over routing or application architecture**: ZAKEY defines its own
stable public destinations (FR-091, FR-092).

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

**Verified reference palette (extracted 2026-07-31, corrected and completed 2026-07-31).** Every
colour literal in the reference's published bundle was extracted with the utility role it is
applied through and its occurrence count, then contrast-tested. This is the observable palette, not
an interpretation of it. It is ratified in full by Constitution v1.1.0 and is the binding colour
authority for this feature (§11.1). **Zero colour decisions remain open.**

**Provenance rule applied.** The designed palette is every colour the reference author chose
explicitly — every arbitrary-value literal (`text-[#...]`, `border-[rgba(...)]`, and so on).
Colours inherited from unprefixed framework utility classes are not designed choices and are not
ratified, with the single exception of `#FFFFFF`, which is unambiguous and independently ratified.

**Core brand tokens (5)**

| Value | Occurrences | Observable roles |
| --- | --- | --- |
| `#0D1B3D` | 173 | text 125, background 40, gradient from 3 / via 2 / to 2, border 1 |
| `#C9A227` | 136 | text 54, background 40, border 28, icon fill 10, form accent 3, gradient from 1 |
| `#F8F9FB` | 55 | background 55 |
| `#FFFFFF` | 117 | text 68, background 39, border 9, placeholder 1 (named utility) |
| `#1F2937` | 22 | text 22 |

**Reference-derived support tokens (13)**

| Value | Occurrences | Observable roles |
| --- | --- | --- |
| `#6B7280` | 64 | text 63, placeholder 1 |
| `#EEF0F5` | 13 | background 12, text 1 |
| `#E0B62E` | 6 | background 6 (gold hover) |
| `#9CA3AF` | 1 | placeholder text 1 |
| `#1A3060` | 3 | background 2, gradient from 1 |
| `#1A2F5A` | 3 | background 2, gradient from 1 |
| `#2A4070` | 1 | background 1 |
| `#162D5E` | 1 | background 1 |
| `rgba(13,27,61,0.06)` | 30 | border 29, divide 1 |
| `rgba(13,27,61,0.08)` | 13 | border 13 |
| `rgba(13,27,61,0.10)` | 18 | border 18, including form fields |
| `rgba(13,27,61,0.15)` | 11 | border 10, background 1 |
| `rgba(13,27,61,0.20)` | 1 | border 1 |

**Total governed palette: 18 values — 5 core brand tokens, 13 reference-derived support tokens.**
Both classifications are binding. Support tokens are official parts of the approved visual system,
not optional suggestions.

**Correction of the earlier seven-versus-eight discrepancy.** An earlier revision of this
specification tabulated twelve values but then enumerated only seven as non-ratified, silently
omitting `#9CA3AF`. That was an enumeration error, not a judgement that the colour was invalid.
`#9CA3AF` is genuinely used — the bundle applies it as `placeholder-[#9CA3AF]` on a form input,
alongside `text-[#1F2937]`, `border-[rgba(13,27,61,0.1)]` and `focus:border-[#C9A227]`. It is
retained and ratified. With `#FFFFFF` and the five navy-alpha values now also captured, the correct
non-core count is **13**, not seven or eight.

**Colours found in the bundle but deliberately NOT ratified.** Each was checked against its
observable role; none is a designed brand colour, and each belongs to content this specification
removes or defers:

| Value / class | Observed use | Why excluded |
| --- | --- | --- |
| `gray-200` | empty-star fill in the rating component, paired with `fill-[#C9A227]` | Ratings are fabricated and removed (RD-4). Framework default, not a designed choice |
| `gray-900`, `blue-600`, `blue-900`, `green-700`, `red-600` | brand chips for "Apple HomeKit", "Google Home", "Amazon Alexa", "Z-Wave", "IFTTT" | Third-party brand colours carrying unverified compatibility claims, removed (RD-7) |
| `green-500`, `green-600`, `green-100/700` | stock indicator dots, "✓ Verified Purchase", "FREE" shipping, order-status badges | Stock claims (FR-036), fabricated reviews (RD-4), delivery promises (RD-7), and deferred order history (Feature 003) |
| `blue-100`, `blue-700` | order-status badges | Deferred to Feature 003 |
| `red-500` | "Sale" badge; also the hover state of the cart-line remove control | The Sale badge is a fabricated discount (RD-7). The remove-control hover is in scope, but the value is an unprefixed framework default whose rendered hex cannot be verified from the bundle. No destructive colour is invented — the error and destructive roles are served from the ratified palette, or by the CID-8 last-resort procedure with recorded contrast evidence |
| `transparent`, `current`, `inherit` | gradient terminators and resets | Not colours |

Three findings bind the implementation:

1. **All five ratified core tokens are confirmed present at their exact ratified values.** Four
   appear as hex literals; `#FFFFFF` appears 117 times through named utilities. The ratified
   palette and the reference do not conflict.
2. **The thirteen support values are now ratified in Constitution v1.1.0**, each with its
   observable role, permitted semantic uses, and measured contrast limitation. Nothing is left for
   `/speckit-plan` to approve — the plan documents implementation mapping and token naming only.
3. **Dark navy sections and gradients are authorized because they are observed.** `#0D1B3D` is a
   full background 40 times and navy gradient stops appear. These are the brand primary, not black
   and not an accidental dark theme. Constitution II.5 forbids *black or near-black* full-bleed
   sections and *excessive* gradients; it does not forbid the reference's own navy sections or its
   restrained gradients. Anything beyond those observed remains prohibited (FR-115).

**Reference defects recorded under Constitution Principle I.4** (these MUST NOT be reproduced, and
MUST NOT be preserved for the sake of pixel similarity):

| # | Defect | Evidence | Required correction |
| --- | --- | --- | --- |
| RD-1 | Accent gold used as text on a light background | hero eyebrow rendered in `#C9A227` | Constitution II.7 measures this at ≈2.4:1, failing the 4.5:1 text threshold. Reproduce the eyebrow's *placement, size, weight, and letter-spacing*; render it in a token colour meeting 4.5:1. |
| RD-2 | Fabricated product identities | "ZAKEY Apex Pro", "ZAKEY Nexus Elite", "ZAKEY Vault Pro", "ZAKEY Guardian", "ZAKEY Slim Touch", "ZAKEY Entry Plus", "ZAKEY Connect X", "ZAKEY Luxe Series" | No such products exist in verified evidence. Replace with the 21 verified catalog products under their real supplier names (§2.3, FR-111, FR-112). |
| RD-3 | Fabricated prices | "$389", "$629" | The verified catalog sets `retail_price: null` and `currency: null` for every product. A price may be shown only when it is a verified sellable price (FR-034). |
| RD-4 | Fabricated ratings and reviews | "4.9", "(2,847 reviews)", "✓ Verified Purchase", named reviewers | Constitution V.3 forbids invented review counts, ratings, and customer reviews. Remove the ratings, review list, "Read all", and "Minimum Rating" filter. |
| RD-5 | Fabricated awards and press | "Red Dot Design Award 2025", "As Seen In & Trusted By", named publications | Constitution V.3 forbids invented awards and media coverage. Remove the section and the badge. |
| RD-6 | Fabricated scale and trust claims | "trusted by over 500,000 homes worldwide", "Homes Protected", "Countries Served", "Uptime Guarantee", "Industry Awards" | Constitution V.3 forbids invented customer numbers. Remove. |
| RD-7 | Fabricated specifications and guarantees | "Stores up to 100 fingerprints with 0.3-second recognition speed and 99.9% accuracy", "IP65 Weather Resistant", "UL, CE, FCC, RoHS", "All ZAKEY products include a full 5-year warranty.", "Free Shipping", "Tax (8%)" | Constitution V.3 forbids invented specifications, certifications, warranties, delivery promises, and tax values. Display only the verified specification fields named in §2.3. |
| RD-8 | Fabricated people | named executives, named testimonial authors, "The Team Behind ZAKEY" | Constitution V.3. Remove the leadership and testimonial sections unless verified biographies are supplied. |
| RD-9 | Card-data collection | "Cardholder Name", "Card Number", "Expiry Date", "CVV" | Constitution VI.9 forbids frontend payment simulations from requesting card details. These fields MUST NOT exist in this feature under any circumstances (FR-051, FR-105). |
| RD-10 | Unsuitable hero image | reference hero image does not clearly depict a smart door lock | Constitution I.5 — preserve the hero *composition*; replace the image with a verified ZAKEY smart-lock image (FR-030). |
| RD-11 | Popularity-derived merchandising | "Best Sellers" / "Top Picks" rail, "Top Rated" sort option | The verified catalog explicitly creates no popularity fact. Merge the two homepage product rails into one verified "Featured Products" rail (FR-011); remove the "Top Rated" sort. |
| RD-12 | Unverified promotional announcement | announcement bar carrying a coupon code | No verified ZAKEY promotion exists. See FR-002 — the bar renders only when verified announcement content exists. |
| RD-13 | Placeholder text below contrast threshold | `placeholder-[#9CA3AF]` on a form input | Measures 2.54:1 on white and 2.41:1 on `#F8F9FB`, failing WCAG 2.2 AA. The reference is internally inconsistent here — it applies `placeholder-[#6B7280]` elsewhere, which measures 4.83:1 and passes. Placeholder text MUST use `#6B7280`; `#9CA3AF` stays ratified but is restricted to non-text roles (FR-120). The correction comes from the reference's own palette; no colour is invented. |

**Accessible substitution rule.** Where correcting a defect requires departing from the reference —
most directly RD-1's colour correction — the substitution is permitted and required, and MUST
preserve the approved premium visual identity: same placement, same proportion, same typographic
character, same restraint. Accessibility corrections take precedence over reference similarity
(RF-12).

### 2.3 Legacy repository evidence

**Path resolution.** The constitution records the verified legacy repository as
`/media/mekky/work/backend/zakey.v1` and carries an open TODO because the originally requested path
was `/media/mekky/work/backend/zakey`. Verified on 2026-07-31: `/media/mekky/work/backend/zakey`
**does not exist**; `/media/mekky/work/backend/zakey.v1` **exists** and is the genuine legacy ZAKEY
Django project (Django apps `products`, `commerce`, `core`, `pages`, `solutions`, `partners`,
`projects`, `leads`, `blog`; `config/`, `static/`, `media/`, `locale/`, `specs/`,
`reference-imports/`). It is confirmed as the authoritative initial product-content source for this
feature. The constitution's own TODO still requires the user's explicit confirmation as a governance
act, recorded as [RRP-1](#18-repository-readiness-preconditions).

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
"Smart Lock". These names are used exactly as recorded; renaming or rebranding is forbidden
(FR-112).

**ZAKEY's role.** ZAKEY is the retailer and the storefront experience. The products it lists are
supplier-branded and explicitly **not ZAKEY-manufactured**. The storefront presents them under
their real supplier attribution and never implies ZAKEY manufactured them (FR-111).

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

**Legacy content gaps found (these are why RRP-10 exists):**

- Contact details in legacy templates are placeholders (`+1 (000) 000-0000`, `+201234567890`). No
  verified ZAKEY phone number, email address, or postal address was found.
- Privacy and Terms templates exist (18.3 KB / 16.0 KB) but render their body from database-backed
  content; no verified legal text is present in the repository.

### 2.4 Reference-versus-legacy conflicts and their resolution

| # | Reference says | Verified evidence says | Resolution |
| --- | --- | --- | --- |
| CF-1 | Priced D2C storefront with cart, checkout, payment, tax, and order placement | `commerce_mode: quote_only`, `retail_price: null`, permitted actions are request price / request quote / contact | Cart, wishlist, checkout information collection, and order review are in scope and genuinely session-backed. Prices and monetary totals appear only where verified (FR-034, FR-098). Order creation, payment, and order confirmation are deferred to Feature 002. |
| CF-2 | ZAKEY-branded invented products | 21 Lezn supplier-branded products, explicitly not ZAKEY-manufactured | Use verified names and real supplier attribution (FR-029, FR-111, FR-112). ZAKEY is presented as the retailer. |
| CF-3 | Ratings, reviews, awards, press, scale claims | Catalog creates no popularity fact; no verified reviews or awards exist | Removed (RD-4, RD-5, RD-6). |
| CF-4 | Rich specification claims | Five approved specification fields only | Display approved fields only, per product, only where populated (FR-035). |
| CF-5 | Persistent account area, saved cards, addresses, order history | No verified accounts; authentication out of scope | Deferred to Feature 003 (§19). |
| CF-6 | Product comparison implied in reference metadata copy | No comparison view, control, or state exists anywhere in the reference bundle; no legacy comparison feature | **Deferred** to Feature 010 — Product Comparison. No comparison control is added on unverified evidence, and none of the approved user stories requires one. |
| CF-7 | Newsletter subscription with "Subscribe" success | No subscription storage or email delivery in scope | Newsletter deferred to Feature 004; Constitution VI.4 forbids a fake success state. Section replaced (FR-012). |
| CF-8 | Single client-side route for the whole experience | — | The reference is not a routing authority. ZAKEY defines stable, meaningful, shareable public destinations (FR-091, FR-092). |

---

## 3. Clarifications

### Session 2026-07-31

- **Q: CL-1 — Commerce model: is Feature 001 a quote-led storefront with cart and checkout deferred, or a priced cart-and-checkout storefront?** → **A:** Neither extreme. Feature 001 delivers the complete public storefront experience **including** a genuinely functional session-backed cart, a genuinely functional session-backed wishlist, checkout-information collection, and a validated order-review state. Cart and wishlist survive normal navigation for the active session. Checkout stops at the order-review state: Feature 001 creates no production order, claims no order submission, shows no order-success state, collects no card information, simulates no payment, integrates no payment gateway, and persists no customer account. Prices are never invented — a product without a verified sellable price is shown as priced on request and produces no monetary total. Persistent catalog, inventory, customers, production orders, payment, fulfilment, and administration are deferred to Feature 002.
- **Q: CL-2 — Quote and enquiry submission: validated summary only, persist to a real store, or persist and notify?** → **A:** Persist to a real store. Every state-changing submission in this feature — the enquiry/quote request reachable from the order-review state, from a product page, and from the Contact page — performs a real underlying operation and confirms success only after that operation reports success. No confirmation may describe an order as placed, paid, reserved, or shipped. Notification delivery (email, messaging) remains out of scope.
- **Q: CL-3 — Verified contact details and legal text: supply them, or remove the affected surfaces?** → **A:** Unavailable business facts are never invented. The Contact page ships with the working enquiry form; a contact-details block renders only where the details are verified. The Privacy and Terms pages render verified ZAKEY legal text or are removed together with every link that points at them. No surface is left as a dead link and none is filled with drafted text.
- **Q: Decision 3 — Are wishlist and product comparison in scope?** → **A:** Wishlist is in scope with real session-backed behavior. Product comparison is deferred to Feature 010 — Product Comparison; no approved user story requires it, and no comparison control is added merely because an unverified source contained one.
- **Q: Decisions 4 and 5 — Does the reference govern routing, and how are its defects treated?** → **A:** The reference is the visual authority only — its single client-side route places no constraint on ZAKEY's architecture, and Feature 001 defines stable, meaningful public destinations. All documented reference defects (thirteen as of the readiness correction) MUST NOT be reproduced, and MUST NOT be preserved for pixel similarity. Accessible substitutions may depart slightly from the reference while preserving the approved premium visual identity.

**Resolved on evidence, without a marker:** the legacy repository path (only `zakey.v1` exists, now
confirmed as the authoritative product-content source) and the absence of any comparison capability
in either authoritative source.

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
   resolves to a real destination or performs a defined action; none is inert and none targets `#`.
4. **Given** the homepage, **When** its copy is audited against §2.3, **Then** no rating, review
   count, award, press mention, certification, warranty, delivery promise, customer count, tax
   value, stock figure, or unverified price appears.
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
   category are shown, the count updates, the applied filter is visibly indicated, and the
   destination address reflects the filtered state so it can be shared and reloaded.
3. **Given** two filter families applied together, **When** results are shown, **Then** products
   satisfy both, and each applied filter can be removed individually.
4. **Given** a filter combination with no matches, **When** results are shown, **Then** a no-results
   state explains that no products match and offers a control that clears the filters.
5. **Given** filters applied, **When** "clear all" is activated, **Then** every filter resets, the
   full range returns, and the address returns to the unfiltered destination.
6. **Given** a visitor at 390px, **When** they open filters, **Then** filters appear in a surface
   designed for that width, focus is trapped inside it, Escape closes it, and closing returns focus
   to the control that opened it.
7. **Given** any sort option, **When** it is selected, **Then** ordering changes accordingly, the
   selection persists across pagination, and the sort is expressed in the destination address.
8. **Given** the listing page at 1440px, 1024px, 768px, and 390px in turn, **When** results are
   shown, **Then** product cards render 4, 4, 2, and 2 across respectively, the document never
   scrolls horizontally, product media keeps its 1:1 ratio, and each card's supplier attribution and
   price-or-price-on-request statement remain fully visible at every width.

---

### User Story 3 - Inspect one product in depth (Priority: P1)

A visitor opens a product, studies its imagery from several angles, reads its verified attributes,
sees who actually makes it, understands honestly what ZAKEY can and cannot yet tell them about
price, and sees related products.

**Why this priority**: The product page is where a discovery journey converts into intent. It is
also where content-integrity failures do the most damage.

**Independent Test**: Open each verified product; exercise the gallery; audit displayed attributes
and attribution against the approved catalog. Delivers complete product-inspection value on its own.

**Acceptance Scenarios**:

1. **Given** a product page, **When** it loads, **Then** it shows the verified display name, its
   verified imagery, its real supplier attribution, its category, its series where one is assigned,
   and its access methods.
2. **Given** a product with multiple images, **When** the gallery is operated by pointer, keyboard,
   and touch, **Then** the main image changes, the active thumbnail is indicated, and the image
   region does not change size between images.
3. **Given** a product page, **When** its attribute table is audited, **Then** it contains only
   approved specification fields, and a field with no verified value is omitted rather than shown
   empty or filled with a placeholder.
4. **Given** a product with no verified sellable price, **When** the pricing area is inspected,
   **Then** it states honestly that pricing is provided on request and offers the enquiry action —
   with no figure, no "from" price, no stock count, and no urgency claim.
5. **Given** a product page, **When** the visitor reads how the product is described, **Then**
   ZAKEY is presented as the retailer and the product's real manufacturer or supplier is named; the
   page never implies ZAKEY manufactured it.
6. **Given** a product page, **When** related products are shown, **Then** each shares that
   product's category or series, and the product being viewed is not among them.

---

### User Story 4 - Collect products across the visit (Priority: P1)

A visitor collecting candidates saves products to a wishlist and adds products to a cart as they
browse, sees running counts in the header, reviews and edits both collections on their own pages,
and finds both intact after moving around the site and reloading.

**Why this priority**: Cart and wishlist are the storefront's state-holding surfaces. They are what
turn browsing into an intent that survives the visit, and they feed checkout.

**Independent Test**: Add, change, and remove from both collections across listing, product, cart,
and wishlist surfaces; navigate widely; reload; empty both. Delivers a working shortlist and a
working cart on its own.

**Acceptance Scenarios**:

1. **Given** any product card or product page, **When** the wishlist control is activated, **Then**
   the control reflects the saved state, the header wishlist count increases, and the change
   survives navigation and reload within the session.
2. **Given** a product page, **When** a quantity is chosen and the product is added to the cart,
   **Then** the header cart count increases, a confirmation appears, and the cart contains that
   product at that quantity.
3. **Given** items in the cart, **When** the visitor navigates across several pages and reloads,
   **Then** the cart still contains exactly the same lines and quantities.
4. **Given** the cart page, **When** a line quantity is changed or a line is removed, **Then** the
   cart, the header count, and any computable totals update immediately and consistently.
5. **Given** a cart containing only products with no verified sellable price, **When** the cart is
   viewed, **Then** no overall monetary total is presented, the cart states that pricing for those
   items is provided on request, and the enquiry action is offered.
6. **Given** an empty cart or an empty wishlist, **When** the page is opened, **Then** an empty
   state explains what it does and links into the range.
7. **Given** either collection, **When** a visitor reads it, **Then** nothing describes it as an
   order, a reservation, a held item, or a completed purchase.

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

### User Story 6 - Supply details and reach a truthful order review (Priority: P2)

A visitor with a cart proceeds to checkout, supplies their contact and delivery information, is
corrected when they get something wrong, and arrives at an order-review state that shows exactly
what they selected, exactly what they entered, and states plainly that no order has been placed and
no payment has been taken. From there they can send a real enquiry.

**Why this priority**: This completes the storefront's conversion path and is the surface where a
dishonest success state would do the most damage.

**Independent Test**: Run checkout from a populated cart — empty submission, invalid submission,
valid submission, backward navigation, and the terminal enquiry — by keyboard and at 390px.

**Acceptance Scenarios**:

1. **Given** a populated cart, **When** checkout is started, **Then** the visitor is asked for
   contact and delivery information across clearly indicated steps, with progress visible.
2. **Given** a checkout step submitted empty, **When** it is submitted, **Then** submission is
   refused server-side, each invalid field is individually described, the message is
   programmatically associated with its field, and focus moves to the first invalid field.
3. **Given** a checkout step with an invalid email address, **When** it is submitted, **Then** the
   email field is identified specifically rather than the step being rejected as a whole.
4. **Given** a completed step, **When** the visitor navigates backwards, **Then** their previously
   entered values are intact and editable.
5. **Given** all information validated, **When** the order-review state is reached, **Then** it
   shows the cart lines with quantities, the entered contact and delivery information, any
   computable monetary totals, and a plain statement that no order has been placed and no payment
   has been taken.
6. **Given** the order-review state, **When** its controls are enumerated, **Then** none claims to
   place an order, complete a purchase, or take a payment; the available actions are correcting the
   information, editing the cart, and sending an enquiry.
7. **Given** checkout in any state, **When** its fields are enumerated, **Then** none collects a
   card number, expiry date, security code, PIN, or any payment credential, and no payment step or
   payment-method selector exists.
8. **Given** a valid enquiry submission, **When** it is sent, **Then** the control enters a busy
   state, the form cannot be double-submitted, and a confirmation appears **only after** the
   underlying operation reports success — worded as an enquiry received, never as an order placed.
9. **Given** the underlying operation fails, **When** the response returns, **Then** an honest
   failure state is shown, the visitor's entered values are preserved, and no confirmation appears.

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
   evidence, including ZAKEY's role as retailer and its relationship to the supplier-branded
   products it offers.
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
- **Unknown category, series, or product destination** — the custom 404 page, with working
  navigation.
- **Search query containing markup or script syntax** — echoed escaped; never rendered as markup.
- **Very long search query or filter value** — handled without layout overflow at any width.
- **A verified image missing at build or request time** — a reserved, correctly proportioned
  placeholder region with meaningful alternative text; never a broken-image icon, never a stretched
  image, and never a file whose visible name reveals internal terminology.
- **Cart or wishlist entry whose product is later removed from the catalog** — the entry is dropped
  silently, the count corrects itself, and any totals recompute; no error and no reference to a
  missing product.
- **Cart mixing priced and unpriced products** — line totals appear only for priced lines; no
  overall monetary total is presented; the cart states that pricing for the remaining items is
  provided on request.
- **Quantity set to zero or a non-numeric value** — rejected with a field-level message; the line is
  not silently removed and no total is computed from an invalid quantity.
- **Checkout started from an empty cart** — the visitor is returned to the cart's empty state rather
  than into a checkout that cannot be completed.
- **Cart emptied in another tab during checkout** — the order-review state refuses to present stale
  contents and returns the visitor to the cart with an explanation.
- **Session expiry mid-checkout** — the visitor is told plainly that their session ended and is
  returned to a valid state; no partial order artifact is created.
- **Form submitted twice rapidly** — exactly one operation occurs.
- **JavaScript unavailable or failed** — navigation, product discovery, product pages, cart,
  checkout, and informational content remain usable; controls that genuinely require scripting are
  not rendered as inert.
- **Reduced-motion preference set** — transitions and any autoplaying movement are suppressed.
- **Very large text scaling (200%)** — no clipped text and no lost control at any width.
- **Server error during a request** — the custom 500 page, with no stack trace and no internal
  detail exposed.

---

## 5. Page Inventory

All 25 candidate surfaces were evaluated, plus one evidence-backed addition (the enquiry/quote
request, named in the verified catalog's `public_actions`). **In scope: 21. Deferred: 5.
Excluded: 0.**

| # | Surface | Decision | Basis / owning future specification |
| --- | --- | --- | --- |
| 1 | Homepage | **In scope** | Reference §2.2; primary entry point |
| 2 | All-products listing | **In scope** | Reference "All Products"; 21 verified products |
| 3 | Category listing | **In scope** | 3 verified categories |
| 4 | Collection (series) listing | **In scope** | 6 verified collections |
| 5 | Search and search results | **In scope** | Reference search; US5 |
| 6 | Product detail | **In scope** | 21 verified products |
| 7 | Product gallery and media states | **In scope** | 25 verified media assets with declared roles |
| 8 | Cart | **In scope** | Session-backed and genuinely functional; survives navigation and reload (US4, FR-093–FR-102) |
| 9 | Checkout information and order review | **In scope** | Information collection plus a validated order-review state. No payment step, no card fields, no order creation (US6, FR-103–FR-110) |
| 10 | Order success / confirmation | **Deferred** | Feature 002 — Commerce Foundation. Constitution VI.4 forbids a success state with no underlying order |
| 11 | Wishlist (saved products) | **In scope** | Session-backed and genuinely functional (US4) |
| 12 | Product comparison | **Deferred** | Feature 010 — Product Comparison. No approved user story requires it; no verified evidence supports one (CF-6) |
| 13 | About ZAKEY | **In scope** | Reference About; verified legacy copy |
| 14 | Contact | **In scope** | Reference Contact; `contact` is a permitted public action. Contact-details block renders only where verified |
| 15 | FAQ | **In scope** | Reference FAQ; verified legacy FAQ content |
| 16 | Shipping information | **Deferred** | Feature 002. Catalog creates no delivery fact |
| 17 | Returns information | **Deferred** | Feature 002. Catalog creates no returns fact |
| 18 | Warranty information | **Deferred** | Feature 002. Catalog creates no warranty fact |
| 19 | Privacy policy | **In scope, conditional** | Required where enquiry and checkout data is collected. Content must be verified ZAKEY legal text; if unavailable, page **and** its links are removed |
| 20 | Terms and conditions | **In scope, conditional** | Same condition as #19 |
| 21 | Empty states | **In scope** | Cross-cutting; §9 |
| 22 | Loading states | **In scope** | Cross-cutting; §9 |
| 23 | Validation and error states | **In scope** | Cross-cutting; §9 |
| 24 | Custom 404 | **In scope** | Constitution VI.7 |
| 25 | Custom 500 | **In scope** | Constitution VI.7 |
| + | Enquiry / quote request | **In scope** | Verified `public_actions: request_price, request_quote, contact`; reachable from product page, cart, order review, and Contact |

Deferred account surfaces observed in the reference — account overview, order history, saved
addresses, saved payment methods, sign-in and registration — are deferred to **Feature 003 —
Customer Accounts**. The newsletter section is deferred to **Feature 004 — Marketing and
Notifications** (CF-7).

---

## 6. Shared Component Inventory

**38 component families.** Each is defined once and reused; Constitution IV.4 forbids duplicating a
shared component between pages.

| # | Family | Purpose | States |
| --- | --- | --- | --- |
| C-01 | Announcement bar | Site-wide verified message | present (verified content) / absent; dismissed persists for the session |
| C-02 | Desktop header | Wordmark, primary navigation, search entry, wishlist entry, cart entry | default, scrolled/condensed, current-section, focus-within |
| C-03 | Mobile navigation | Full navigation at narrow widths | closed, opening, open, closing; focus trapped; Escape closes |
| C-04 | Search interface | Query entry and submission from any page | closed, open, empty, typing, submitting, submitted |
| C-05 | Breadcrumbs | Ancestry on listing, category, series, product, informational pages | default, current (non-link), truncated at narrow widths |
| C-06 | Hero | Homepage primary composition | default; reduced-motion |
| C-07 | Section heading | Eyebrow + heading + optional supporting copy + optional action | with/without eyebrow, with/without action |
| C-08 | Category card | Entry to a category | default, hover, focus-visible, pressed |
| C-09 | Collection card | Entry to a series | default, hover, focus-visible, pressed |
| C-10 | Product card | Product in any grid or rail | default, hover, focus-visible, wishlisted, in-cart, image-loading, image-unavailable |
| C-11 | Price presentation | Honest pricing statement | **verified price** (figure + currency) / **price on request** (no figure) |
| C-12 | Availability presentation | Honest availability statement | enquiry-based (the only state in this feature) |
| C-13 | Product badge | Verified attribute marker only | category, series, access method, supplier attribution. **No** popularity, discount, award, or certification badge |
| C-14 | Button | Primary, secondary, tertiary, icon-only | default, hover, focus-visible, active, disabled, busy |
| C-15 | Link | Inline and standalone | default, hover, focus-visible, visited, current |
| C-16 | Form field | Text, email, telephone, textarea, select, checkbox | default, focus, filled, invalid, disabled, read-only |
| C-17 | Validation message | Field-level and form-level errors | field error, form summary, success |
| C-18 | Filter panel | Category, series, access-method filters | expanded, collapsed, applied, empty result, drawer (narrow widths) |
| C-19 | Applied-filter chips | Show and individually remove active filters | present, absent, removable |
| C-20 | Sort control | Result ordering | closed, open, selected |
| C-21 | Pagination | Movement through results | first, middle, last, single page, disabled edges |
| C-22 | Gallery controls | Product media navigation | single image, multiple images, active thumbnail, keyboard-operated |
| C-23 | Quantity control | Quantity on a product page and on a cart line | minimum, typical, maximum, invalid input, busy |
| C-24 | Wishlist control | Save/unsave a product | unsaved, saved, busy, unavailable |
| C-25 | Enquiry / quote request surface | Review and submit a real enquiry covering one or more products | empty, populated, validating, submitting, submitted, failed |
| C-26 | Dialog | Modal interaction | closed, open, focus-trapped, Escape-dismissed |
| C-27 | Drawer | Off-canvas surface (mobile nav, filters, cart drawer) | closed, open, focus-trapped, Escape-dismissed |
| C-28 | Toast notification | Transient confirmation of a completed action | enter, visible, dismissed, reduced-motion, assistively announced |
| C-29 | Enquiry call-to-action band | Homepage conversion band replacing the newsletter (CF-7) | default |
| C-30 | Informational content section | Prose, question-and-answer, contact blocks | default, expanded/collapsed (FAQ) |
| C-31 | Footer | Site-wide navigation and legal links | default; links render only for pages that exist |
| C-32 | Loading state | Deferred content and in-flight actions | skeleton (reserved dimensions), busy control |
| C-33 | Empty state | No content to show | listing, search, cart, wishlist |
| C-34 | Error state | Something failed | field, form, page-level, 404, 500 |
| C-35 | Cart line | One product line in the cart | priced, price-on-request, quantity-editing, removing, unavailable |
| C-36 | Cart summary | Line count and any computable totals | fully priced, partially priced, unpriced (no monetary total), empty |
| C-37 | Checkout step indicator | Progress through checkout | current step, completed step, upcoming step; backward navigation available |
| C-38 | Order-review summary | Final truthful review of lines and entered information | complete, correctable, stale-cart, submitting enquiry |

Removed relative to the reference, with cause: rating presentation and review list (RD-4); press
and award badges (RD-5); testimonial card (RD-4/RD-8); newsletter subscription form (CF-7); coupon
field (no verified promotion, RD-12); tax line (RD-7); shipping-method selector (no verified
delivery fact, RD-7); every payment field, payment step, and payment-method selector (RD-9); and the
"Place Order" control (CF-1 — no underlying order operation exists in Feature 001).

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
| Product card wishlist control | click / Enter / Space | Toggles wishlist state; count updates; state announced |
| Filter option | click / Space | Applies or removes that filter; results and address update |
| Filter chip remove | click / Enter | Removes that one filter |
| Clear all filters | click / Enter | Removes every filter; returns to unfiltered destination |
| Mobile filter open / close | click / Escape | Opens or closes the filter drawer with focus management |
| Sort option | selection | Reorders results; persists across pagination; reflected in the address |
| Pagination page / prev / next | click / Enter | Moves to that page; edge controls disabled at edges |
| Gallery thumbnail | click / Enter / arrow keys | Changes main image; marks active thumbnail |
| Gallery prev / next | click / Enter / arrow keys | Steps through images |
| Product quantity increase / decrease / entry | click / Enter / typing | Adjusts within bounds; rejects invalid input with a message |
| Add to cart | click / Enter | Adds the product at the chosen quantity to the session cart; header count updates; confirms via toast |
| Open cart | click / Enter | Opens the cart surface |
| Cart line quantity change | click / Enter / typing | Updates that line; cart, header count, and computable totals update |
| Cart line remove | click / Enter | Removes that line; counts and computable totals update |
| Continue shopping | click / Enter | Returns to the range |
| Proceed to checkout | click / Enter | Starts checkout from the current cart; refused with an explanation if the cart is empty |
| Checkout continue | click / Enter | Validates the current step server-side; advances only when valid |
| Checkout back | click / Enter | Returns to the previous step with entered values intact |
| Edit cart from review | click / Enter | Returns to the cart with entered information preserved |
| Edit information from review | click / Enter | Returns to the relevant checkout step |
| Send enquiry (from order review, product page, or Contact) | click / Enter | Validates, submits, enters busy state, and confirms **only** on a confirmed successful underlying operation; never claims an order |
| FAQ question | click / Enter / Space | Expands or collapses its answer; expanded state exposed |
| Toast dismiss | click / Escape / timeout | Removes the toast |
| Skip to content | Tab from page start, Enter | Moves focus to the main landmark |
| Footer link | click / Enter | Navigates to an existing page |

No control in this feature targets `#`. No control renders without one of the behaviors above. No
control claims to place an order, complete a purchase, or take a payment.

---

## 8. Responsive-State Inventory

Constitution VII.1 fixes four verification widths. Each receives a deliberate layout decision;
Constitution VII.2 forbids treating narrow layouts as stacked desktop columns.

| Surface | 1440px (desktop) | 1024px (tablet) | 768px (transition) | 390px (mobile) |
| --- | --- | --- | --- | --- |
| Header | Full horizontal navigation, inline search | Full navigation, condensed spacing, search as icon | Navigation collapses to menu control; search icon retained | Menu control, wordmark, wishlist and cart counts; search opens full-width |
| Hero | Two columns, text left, image right | Two columns, reduced image share | Single column, image below text, retained aspect ratio | Single column, shortened headline treatment, full-width stacked actions |
| Category showcase | 3 across | 3 across, tighter gutters | 2 across | 1 across, or horizontal scroll rail with visible affordance |
| Product grid | **4 across** | **4 across** | **2 across** | **2 across** (see §8.1) |
| Product rail | 4 visible, paged | 3 visible, paged | 2 visible, scroll-snap | 1.2 visible, scroll-snap with edge peek |
| Listing + filters | Persistent filter sidebar beside results | Persistent sidebar, narrowed | Filters collapse to a top control opening a drawer | Filter and sort as a sticky bar opening a full-height drawer |
| Product detail | Gallery left, information right, sticky action area | Gallery left, information right, non-sticky | Gallery above information | Gallery full-bleed with swipe; add-to-cart pinned to the bottom |
| Gallery | Thumbnail column beside main image | Thumbnail column, narrowed | Thumbnail row below main image | Swipeable main image with position indicator |
| Wishlist | Grid, 3 across | Grid, 3 across | Grid, 2 across | List rows, 1 across |
| Cart | Lines left, summary sticky right | Lines left, summary right, non-sticky | Single column, summary below lines | Single-column line cards with inline quantity; summary and primary action pinned to the bottom |
| Checkout | Form left, cart summary sticky right | Form left, summary right | Single column, collapsible summary above form | Single column, one step per screen, step indicator condensed, primary action pinned to the bottom |
| Order review | Two columns: lines and entered information | Two columns, narrowed | Single column, grouped sections | Single column, collapsible sections, action pinned to the bottom |
| Forms | Multi-column field groups | Multi-column where pairs fit | Single column | Single column, full-width fields and controls |
| Informational pages | Constrained measure with side navigation where present | Constrained measure | Single column | Single column, reduced section padding |
| Footer | 4 columns | 3 columns | 2 columns | 1 column, groups collapsible |

At every width and on every in-scope surface: no horizontal overflow, no clipped text, no header
collision, no overlapping floating controls, no tablet dead zone, no oversized empty region, stable
image dimensions, readable cards, usable filters, usable gallery, usable forms, usable cart and
checkout surfaces, reachable navigation, and touch targets meeting §12.

### 8.1 Product-card grid responsive matrix — authoritative decision

**Status: authoritative decision, recorded 2026-08-01, superseding the earlier 4/3/2/1 values in the
row above and closing DEV-1.** The approved reference is authoritative for responsive storefront
behavior **at every acceptance width, not only at 390px**. The reference renders product-card grids
`grid grid-cols-2 lg:grid-cols-4`, whose `lg:` breakpoint is 1024px — that is **4 across at both
1440px and 1024px, and 2 across at both 768px and 390px**.

**Governed acceptance matrix for product-card listing grids:**

| Width | Columns |
| --- | --- |
| 1440px | **4** |
| 1024px | **4** |
| 768px | **2** |
| 390px | **2** |
| below 390px | may degrade safely to **1** where required to prevent overflow |

**Scope — what this applies to.** Only **product-card listing grids**: the all-products listing,
category listings, collection listings, search results, and the related-products grid.

**Scope — what this explicitly does NOT apply to.** Two columns are **not** required, and MUST NOT be
imposed, for: forms and form-field groups; checkout fields; the checkout information and order-review
layouts; informational pages; dialogs; drawers; the filter panel; the cart line list; the wishlist
list-row presentation; product rails (which remain scroll-snap with edge peek); or the category
showcase, whose tiles keep their distinct `4:5` ratio.

Mandatory conditions — these apply at **every** width in the matrix, not only at 390px:

- **CG-1 No horizontal overflow.** Document scroll width MUST NOT exceed viewport width at 1440px,
  1024px, 768px, or 390px. Verified programmatically (NFR-009, SC-008).
- **CG-2 Preserved media ratio.** Product media remains **1:1 square** on the subtle surface token,
  contained and never cropped, stretched, or upscaled. The category tile's `4:5` ratio is unchanged
  (NFR-011, CI-11).
- **CG-3 Compliant touch targets.** Every interactive element inside the card — card link, wishlist
  control, add-to-cart — meets at least 24×24 CSS pixels, and the primary commerce action meets
  44×44. Reducing column width MUST NOT be achieved by shrinking targets below these thresholds
  (A-11, NFR-018, SC-013).
- **CG-4 Controlled wrapping and truncation.** The product name wraps to a maximum of two lines and
  truncates with an ellipsis beyond that, with the full name remaining available to assistive
  technology. The supplier attribution line and the price-or-price-on-request statement MUST remain
  fully visible and MUST NOT be truncated, hidden, or dropped to fit — attribution and price honesty
  outrank density (FR-111, FR-034).
- **CG-5 Readable minimums.** Card body text remains at the ratified type scale with no reduction
  below 12px, and gutters remain on the spacing scale so the two columns stay visually separated.
- **CG-6 No clipped content.** No text, badge, or control may be clipped, overlapped, or rendered
  outside its card at any width in the matrix.
- **CG-7 Graceful narrow behavior.** Below 390px the grid MAY degrade to one column where required
  to prevent overflow; 390px is the ratified verification width, not the minimum supported width.

**Acceptance.** The product-card grid MUST be inspected at **all four required widths — 1440px,
1024px, 768px, and 390px** — in **both** required visual critique passes (Constitution XIII.3),
against the reference, checking the column count for that width plus CG-1 through CG-7 (SC-051).

---

## 9. Loading, Empty, Error, Disabled, and Success States

| Surface | Loading | Empty | Error | Disabled | Success |
| --- | --- | --- | --- | --- | --- |
| Product listing | Skeleton cards at final card dimensions | "No products match these filters" + clear-filters control | Retrievable failure message; filters preserved | Pagination edges at first/last page | n/a |
| Search results | Skeleton results; query echoed | "No results for <query>" + route into full range | Failure message; query preserved | n/a | n/a |
| Product detail | Reserved gallery and content regions | n/a (missing product → 404) | Failure message with a route back to the listing | Gallery controls absent for single-image products | Toast on add to cart / wishlist |
| Gallery | Reserved image box at the declared ratio | n/a | Proportioned placeholder + meaningful alternative text | Prev/next absent for single image | n/a |
| Wishlist | Skeleton rows | "You have not saved any products yet" + route into range | Failure message; existing set preserved | n/a | Toast on save/remove |
| Cart | Skeleton lines at final dimensions | "Your cart is empty" + route into range | Failure message; cart contents preserved | Checkout control disabled while the cart is empty, with the reason stated | Toast on quantity change and removal |
| Cart summary | Reserved totals region | n/a | Failure message | n/a | n/a — where any line lacks a verified price, no monetary total is shown and the price-on-request statement appears instead |
| Checkout step | Busy continue control; step locked | n/a — checkout is refused from an empty cart | Field-level and form-level errors; entered values preserved | Continue disabled while busy | Advance to the next step only after server-side validation passes |
| Order review | Reserved summary regions | n/a | Stale-cart state returns the visitor to the cart with an explanation | Enquiry control disabled while busy | Enquiry confirmation only after the operation succeeds — worded as an enquiry received, never as an order placed |
| Enquiry / contact form | Busy submit control | n/a | Field-level and form-level errors; values preserved | Submit disabled while busy | Confirmation only after the operation succeeds |
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
- **CI-5** No **invented** price, currency, discount, stock figure, tax rate, or delivery term
  appears anywhere. A monetary figure may appear only when it is a verified sellable price for that
  product, or a total computed solely from such prices.
- **CI-6** No rating, review, review count, award, certification, press mention, partnership,
  customer count, sales figure, or trust badge appears.
- **CI-7** No warranty, guarantee, installation promise, or reply-time promise appears unless
  verified and supplied.
- **CI-8** ZAKEY is presented as the **retailer**. Every product's real manufacturer or supplier
  attribution is retained and shown; no product is presented as ZAKEY-manufactured.
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
- **CI-15** Where verified content for a surface does not exist, that surface and every link to it
  are removed together — never left as a dead link, and never filled with drafted text.
- **CI-16** Synthetic or example prices may exist **only** inside isolated automated tests. They
  MUST NOT appear in accepted production-facing content, in screenshots used as evidence, in
  fixtures, or in seeded storefront data.
- **CI-17** No surface may describe the cart, the wishlist, or the order-review state as an order, a
  reservation, a held item, a payment, or a completed purchase.

---

## 11. Reference-Fidelity Requirements

**Method.** Fidelity is reviewed by side-by-side comparison of the implementation against the
reference at 1440px, 1024px, 768px, and 390px, on the homepage, the listing page, the product page,
and the cart, plus one informational page for design-system consistency. Screenshots are captured at
each width and **inspected**, with observations recorded in the verification artifact — Constitution
XIII.6 states that capturing screenshots without inspecting them is not visual QA.

**Acceptance is structural, not pixel-level.** The reference is a prototype containing thirteen
recorded defects (§2.2) that must not be reproduced. A comparison passes when all of the following
hold at every compared width:

- **RF-1 Visual hierarchy** — on each compared page the same element carries primary emphasis as in
  the reference, and the reading order of eyebrow → heading → supporting copy → action is preserved.
- **RF-2 Section order and rhythm** — retained sections appear in reference order; vertical rhythm
  between sections follows one spacing scale in multiples of 8px, matching the reference's density
  impression rather than an arbitrary value.
- **RF-3 Layout density** — the number of products per row at each width matches §8 and the §8.1
  matrix exactly (4 / 4 / 2 / 2 at 1440 / 1024 / 768 / 390, as the reference does), and content
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
- **RF-11 Removed sections leave no scar** — where a fabricated section or control was removed
  (RD-4, RD-5, RD-6, RD-8, RD-9, RD-12, CF-7), the surrounding rhythm is re-closed; no oversized
  empty region remains.
- **RF-12 Accessibility overrides similarity** — where a reference defect conflicts with §12, the
  accessible substitution wins. The substitution preserves placement, proportion, typographic
  character, and restraint, so the approved premium identity survives the correction. A reference
  defect is never reproduced to improve similarity scores.

### 11.1 Color Identity — binding authoritative decision

**Status: authoritative user decision, recorded 2026-07-31. This is not a clarification and is
not open to reinterpretation during planning or implementation.**

The visual reference is the **binding authority for the storefront's color palette and visual
identity**, not merely an inspiration for it. The accepted implementation MUST preserve the same
observable reference colors, the same premium gold character, the same light-background character,
the same neutral and dark support colors, the same intended visual hierarchy, and the same
restrained, luxurious color usage across **every included page and component** — not the homepage
alone.

"Similar to", "inspired by", and an independently redesigned palette are **not acceptable
outcomes**. A palette that merely evokes the reference is a failed implementation, not a variant.

- **CID-1 Exact values, extracted and approved.** The exact observable color values have been
  extracted, classified, contrast-tested, and **ratified in full** by Constitution v1.1.0 — 18
  values: 5 core brand tokens and 13 reference-derived support tokens, each with its observable
  role, permitted semantic uses, and measured contrast limitation (§2.2). Both classifications are
  binding; support tokens are not optional suggestions. **No palette decision remains open.**
  `/speckit-plan` MUST NOT reconsider, substitute, re-approve, or extend the approved colors — its
  remaining color work is implementation mapping and CSS token naming only.
- **CID-2 One token authority.** Every documented value MUST be implemented through exactly one
  centralized set of shared design tokens. No template, component, stylesheet, or script may carry
  a literal color value. A color that cannot be resolved to a token is a defect.
- **CID-3 Complete role coverage.** The same approved tokens MUST govern the announcement bar,
  header, navigation, mobile navigation, hero, section headings, cards, category and collection
  surfaces, product surfaces, prices, badges, buttons, links, form fields, validation messages,
  filters, sorting, pagination, gallery controls, quantity controls, wishlist controls, cart
  surfaces, checkout surfaces, order review, dialogs, drawers, toasts, informational pages, loading
  states, empty states, error states, 404, 500, and the footer.
- **CID-4 No palette drift.** The palette on an internal public page MUST be identical to the
  palette on the homepage. Page-specific color systems are forbidden. A gold shade that differs
  between two surfaces, a card background that differs between two grids, or a button color that
  differs between two pages is a defect, not a variation.
- **CID-5 Nothing added.** The interface MUST NOT introduce a brand color, gradient, dark section,
  card color, or button color that is not present in the extracted reference palette and its
  documented roles. The navy sections and restrained gradients observed in the reference are
  authorized precisely because they are observed; anything beyond them is not. Black or near-black
  full-bleed sections that read as an unintended dark theme remain forbidden by Constitution II.5.

#### Accessibility reconciliation

Exact visual identity does **not** authorize inaccessible text. These two requirements are
reconciled by changing a color's **semantic role**, never by redesigning the palette.

- **CID-6 Gold is restricted by role, not replaced.** `#C9A227` measures approximately 2.4:1 on
  `#FFFFFF` and on `#F8F9FB`, failing both the 4.5:1 text threshold and the 3:1 non-text threshold.
  It MUST NOT be used for normal-sized text on a light background. It remains fully available, at
  its exact value, for decorative accents, borders, icon fills on compliant backgrounds, large text
  that measures compliant, and as a background with a compliant foreground. On primary navy
  `#0D1B3D` it measures approximately 6.9:1 and is compliant.
- **CID-7 Substitute from the existing palette first.** Where the reference uses gold for normal
  text on a light background (RD-1, the hero eyebrow), the correction MUST use an existing
  reference neutral — `#1F2937` or `#0D1B3D` — while preserving the element's placement, size,
  weight, letter-spacing, and prominence. Inventing a replacement gold is forbidden.
- **CID-8 A new shade is a last resort with a paper trail.** If an accessibility role genuinely
  cannot be satisfied by any documented reference value, the additional shade MUST: state why the
  existing palette cannot satisfy the role; be derived from the approved visual family; record its
  exact value; record measured contrast evidence for every pairing it is used in; be restricted to
  that one accessibility role; and preserve the overall reference identity. Accessibility
  correction MUST NOT become a route to redesigning the palette.

#### How color fidelity is verified

Color comparison against the reference is performed at **1440px, 1024px, 768px, and 390px**, on
every included page, and is a required element of **both** visual critique passes (Constitution
XIII.3). Each pass records, per page and per width, whether any rendered color deviates from its
documented token and whether any surface has drifted from the homepage palette. Contrast is
verified for every token pairing actually in use.

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
- **A-11** Interactive targets are at least 24×24 CSS pixels; primary mobile actions — add to cart,
  proceed to checkout, continue, and send enquiry — are at least 44×44.
- **A-12** Menus and disclosure controls expose expanded/collapsed state assistively.
- **A-13** Drawers and dialogs, including the cart drawer, trap focus while open, close on Escape,
  and return focus to the control that opened them.
- **A-14** Content changes that occur without navigation — wishlist toggles, cart updates, filter
  results, toasts — are announced assistively without stealing focus.
- **A-15** Reduced-motion preference suppresses transitions, parallax, and any autoplaying movement.
- **A-16** Every meaningful image has alternative text describing what it shows; decorative images
  are hidden from assistive technology.
- **A-17** Each page declares its language and text direction on the root element.
- **A-18** Page titles are unique and describe the page.
- **A-19** Content remains usable and unclipped at 200% text scaling at every verification width.
- **A-20** Checkout step progress is exposed assistively, not by visual styling alone.
- **A-21** Verification requires **both** an automated axe run with zero violations at the
  documented conformance level **and** a manual keyboard pass covering tab order, focus visibility,
  focus trapping, and dismissal. Constitution VIII.6: an automated pass alone is not verification.

---

## 13. Performance Budgets

Budgets are set before implementation (Constitution IX.7) and are measured on a production-mode
build. "Page weight" means total transferred bytes for an uncached first load, excluding video.

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
| PB-18 Page weight — cart, checkout, order review | ≤ 900 KB each | Production build, uncached load |
| PB-19 Cart and wishlist state update | Reflected in the interface within 200 ms of a confirmed update | Production-like local run |

No budget may be met by weakening accessibility, removing required content, or degrading visual
quality (Constitution IX.8).

---

## 14. Requirements *(mandatory)*

### Functional Requirements

#### Navigation, destinations, and information architecture (FR-001 to FR-012, FR-091 to FR-092)

- **FR-001**: The storefront MUST present one navigation architecture, identical in structure and
  behavior on every in-scope page.
- **FR-002**: The announcement bar MUST render only when verified announcement content exists in the
  centralized content source; when absent, every page MUST lay out correctly without it.
- **FR-003**: The header MUST provide the wordmark linking to the homepage, primary navigation to
  the product range and informational pages, a search entry point, a wishlist entry point showing
  the current count, and a cart entry point showing the current line count.
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
- **FR-010**: Every internal link MUST resolve to an existing destination. No control may target `#`
  and no control may render without defined behavior.
- **FR-011**: The homepage MUST present, in order: hero, category showcase, featured products,
  value proposition, series showcase, enquiry call to action, footer — a single featured-products
  rail sourced from the verified `featured_products_slider` role (RD-11).
- **FR-012**: The footer MUST group links by purpose, MUST render a link only for a page that
  exists in this feature, and MUST NOT reproduce reference footer entries for surfaces that are
  deferred.
- **FR-091**: Every in-scope surface MUST have a stable, meaningful public destination. The
  reference's single client-side route places no constraint on ZAKEY's destinations or architecture;
  the reference is the visual authority, not the routing authority.
- **FR-092**: Every destination MUST be shareable and MUST reload to the same content, including
  filtered, sorted, and paginated listing states and search results.

#### Product discovery (FR-013 to FR-028, FR-121)

- **FR-013**: The listing page MUST make every verified product reachable and MUST state the number
  of results.
- **FR-014**: Category listing pages MUST exist for each of the three verified categories.
- **FR-015**: Collection listing pages MUST exist for each of the six verified collections.
- **FR-016**: Filtering MUST be offered by category, by collection, and by access method — the three
  facets for which verified data exists.
- **FR-017**: A price-range filter MUST NOT be offered while the catalog carries no verified prices,
  and a minimum-rating filter MUST NOT be offered at all, because no verified rating data exists and
  none may be invented (RD-3, RD-4). A price filter becomes available only once verified prices
  exist for the catalog.
- **FR-018**: Filters MUST be combinable; results MUST satisfy every applied filter.
- **FR-019**: Every applied filter MUST be individually visible and individually removable.
- **FR-020**: A control MUST clear all filters at once and return the listing to its unfiltered
  state and destination.
- **FR-021**: Filter, sort, and pagination state MUST be expressed in the destination address so a
  result set can be shared and reloaded to the same state.
- **FR-022**: Sorting MUST offer only orderings derivable from verified data — featured order, name
  ascending, name descending. Popularity-based sorts MUST NOT be offered at all (RD-11); price-based
  sorts MUST NOT be offered while the catalog carries no verified prices (RD-3).
- **FR-023**: Results MUST be paginated, with page controls disabled at the first and last page and
  the current page indicated.
- **FR-024**: When no products match, the storefront MUST show a no-results state that explains the
  outcome and offers a control that clears the filters.
- **FR-025**: At narrow widths, filters MUST be presented in a dedicated surface with focus
  management and Escape dismissal — not as a long list pushing results off-screen.
- **FR-026**: Search MUST match against verified product display names, model codes, supplier
  attribution, categories, and collections; results MUST echo the query and state the result count.
- **FR-027**: A search with no matches MUST show a no-results state offering a route into the full
  range; an empty or whitespace-only query MUST NOT produce an error or a results page implying a
  search occurred.
- **FR-028**: Product cards MUST present identical structure and proportions wherever they appear —
  listing, category, collection, search results, related products, wishlist, and homepage rails.
- **FR-121**: Product-card listing grids — all-products, category, collection, search results, and
  related products — MUST follow the §8.1 responsive matrix, preserving the approved reference's
  grid behavior at every acceptance width: **4 columns at 1440px, 4 at 1024px, 2 at 768px, 2 at
  390px**, degrading to 1 below 390px only where required to prevent overflow. They MUST satisfy
  conditions CG-1 through CG-7 of §8.1 at every one of those widths: no horizontal overflow; 1:1
  product media contained and never cropped or stretched; touch targets ≥24×24 with the primary
  commerce action ≥44×44; product name wrapping to at most two lines with accessible full text;
  supplier attribution and the price-or-price-on-request statement never truncated or hidden; body
  text no smaller than 12px; no clipped or overlapping content; and degradation to one column below
  390px rather than overflow. Two columns MUST NOT be imposed on forms, checkout fields,
  informational layouts, dialogs, drawers, filter panels, cart lines, the wishlist list-row
  presentation, product rails, or category tiles.

#### Product presentation and product truth (FR-029 to FR-041, FR-111 to FR-113)

- **FR-029**: Products MUST be presented under their verified public display names only.
- **FR-030**: Product imagery MUST come from the verified media assets, used in their declared roles;
  the homepage hero image MUST be a verified ZAKEY smart-lock image (Constitution I.5, RD-10).
- **FR-031**: A product page MUST present name, imagery, supplier attribution, category, collection
  where assigned, and access methods.
- **FR-032**: Product galleries MUST support multiple images with pointer, keyboard, and touch
  operation, MUST indicate the active image, and MUST NOT change the media region's dimensions
  between images.
- **FR-033**: A product with a single image MUST render without gallery navigation, rather than with
  disabled controls.
- **FR-034**: A monetary price MUST be shown for a product only when that product carries a verified
  sellable price. A product without one MUST show a consistent price-on-request statement on every
  surface that references its price, with no figure, no "from" price, and no currency.
- **FR-035**: Technical information MUST be limited to the five approved specification fields, and a
  field with no verified value MUST be omitted rather than shown empty.
- **FR-036**: Availability MUST be presented honestly as enquiry-based, with no stock count, no
  "in stock" claim, and no urgency signal.
- **FR-037**: Related products MUST share the viewed product's category or collection and MUST NOT
  include the viewed product.
- **FR-038**: Product badges MUST convey verified attributes only — category, collection, access
  method, supplier attribution. Popularity, discount, award, and certification badges MUST NOT exist.
- **FR-039**: Product information MUST follow one hierarchy on every product page: identity,
  attribution, media, key attributes, action, detailed attributes, related products.
- **FR-040**: Wherever product origin could be misread, the storefront MUST state ZAKEY's role as
  retailer and the product's real supplier explicitly (CI-8).
- **FR-041**: An unavailable product image MUST render a correctly proportioned placeholder region
  with meaningful alternative text — never a broken-image icon and never a distorted image.
- **FR-111**: Every product MUST retain and display its real manufacturer or supplier attribution.
  ZAKEY MUST be presented as the retailer and MUST NOT be presented, implied, or styled as the
  manufacturer of a supplier-branded product.
- **FR-112**: Verified product names, images, specifications, categories, and collections MUST be
  preserved exactly as recorded in the authoritative catalog. Renaming, rebranding, paraphrasing a
  specification, or reassigning a product's taxonomy is forbidden.
- **FR-113**: Synthetic or example prices MAY exist only inside isolated automated tests. They MUST
  NOT appear in accepted production-facing content, in evidence screenshots, in fixtures, or in
  seeded storefront data.

#### Color identity and design tokens (FR-114 to FR-120)

- **FR-114**: The accepted interface MUST use only colors from the 18-value palette ratified in
  Constitution v1.1.0 and documented in §2.2, each in its permitted semantic role. All 13
  reference-derived support tokens — `#6B7280`, `#EEF0F5`, `#E0B62E`, `#9CA3AF`, the four navy
  tints, and the five navy-alpha values — are binding and MUST be carried into the token source
  rather than dropped, approximated, or substituted. Not every token must appear on every page;
  every color that does appear MUST come from this palette and retain its defined semantic role
  (CID-1).
- **FR-115**: The interface MUST NOT introduce any additional brand color, gradient, dark-section
  treatment, card color, or button color beyond those observed in the reference. Black or
  near-black full-bleed sections that read as an unintended dark theme are forbidden (CID-5).
- **FR-116**: Every rendered color MUST resolve to exactly one centralized set of shared design
  tokens. No template, component, stylesheet, or script may contain a literal color value (CID-2).
- **FR-117**: The same approved token set MUST govern every surface listed in CID-3. Page-specific
  color systems, divergent gold shades, divergent card colors, and divergent button colors between
  pages are defects, not variations (CID-3, CID-4).
- **FR-118**: Accent gold `#C9A227` MUST NOT be used for normal-sized text on a light background.
  Its exact value MUST be preserved and its role changed — decorative accents, borders, icon fills
  on compliant backgrounds, compliant large text, or as a background with a compliant foreground.
  Where the reference uses gold for normal text, the correction MUST use an existing reference
  neutral (`#1F2937` or `#0D1B3D`), preserving placement, size, weight, letter-spacing, and
  prominence. A replacement gold MUST NOT be invented (CID-6, CID-7, RD-1).
- **FR-119**: Any additional accessibility-specific shade MUST be a documented last resort — with a
  stated reason the existing palette cannot satisfy the role, derivation from the approved visual
  family, its exact value, measured contrast evidence for every pairing, and restriction to that
  one accessibility role. Accessibility correction MUST NOT be used to redesign the palette
  (CID-8).
- **FR-120**: Placeholder text MUST use `#6B7280` (4.83:1 on white, 4.59:1 on `#F8F9FB`).
  `#9CA3AF` MUST NOT be used as text of any size, including placeholder text, because it measures
  2.54:1 on white and 2.41:1 on `#F8F9FB`; it remains available for non-text roles only. This
  correction is taken from the reference's own alternate placeholder usage, not invented (RD-13).

#### Wishlist (FR-042 to FR-047)

- **FR-042**: Visitors MUST be able to add and remove products from the wishlist from product cards
  and product pages, with the control reflecting current state.
- **FR-043**: The wishlist count MUST be shown in the header and MUST stay accurate across
  navigation and reload within the session.
- **FR-044**: The wishlist page MUST list saved products, allow removal, allow moving a product to
  the cart, and offer a route into an enquiry.
- **FR-045**: The wishlist MUST be genuinely session-backed: its contents MUST survive normal
  navigation and reload for the duration of the active session, without requiring an account.
- **FR-046**: No wishlist surface may describe the set as an order, a cart, a reservation, a held
  item, or anything implying a commercial commitment.
- **FR-047**: A wishlist entry whose product no longer exists MUST be dropped silently, with the
  count corrected and no error shown.

#### Enquiry and quote request (FR-048 to FR-053)

- **FR-048**: Visitors MUST be able to send an enquiry covering one product from its product page,
  and an enquiry covering the current cart from the cart and from the order-review state.
- **FR-049**: The enquiry surface MUST show which products it covers and allow lines to be removed
  before submission.
- **FR-050**: The enquiry surface MUST present monetary totals only where every covered line carries
  a verified price; otherwise it MUST present no monetary total and MUST state that pricing for the
  affected items is provided on request.
- **FR-051**: No surface in this feature may request, transmit, log, or store a card number, expiry
  date, security code, PIN, or any payment credential (Constitution VI.9, RD-9).
- **FR-052**: An enquiry confirmation MUST appear only after the underlying operation reports
  success, MUST be worded as an enquiry received, and MUST NOT promise a reply time, price,
  availability, or delivery unless verified, nor describe an order as placed, paid, reserved, or
  shipped.
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
- **FR-067**: The About page MUST describe ZAKEY truthfully as a premium retailer, including its
  relationship to the supplier-branded products it offers.
- **FR-068**: The Contact page MUST offer a working enquiry form; it MUST show contact details only
  where those details are verified.
- **FR-069**: The FAQ MUST present question-and-answer content that is individually expandable,
  keyboard-operable, and assistively labelled with its expanded state.
- **FR-070**: Privacy and Terms pages MUST render verified ZAKEY legal text or MUST be removed
  together with every link that points at them (CI-15).

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
- **FR-089**: Core navigation, product discovery, product detail, cart, checkout, and informational
  content MUST remain usable when JavaScript is unavailable; controls that genuinely require
  scripting MUST NOT render as inert.
- **FR-090**: Every page MUST render correctly with the announcement bar both present and absent,
  and with the cart and wishlist both empty and populated.

#### Cart (FR-093 to FR-102)

- **FR-093**: Visitors MUST be able to add a product to the cart at a chosen quantity from the
  product page.
- **FR-094**: The cart MUST be genuinely session-backed: its lines and quantities MUST survive
  normal navigation and reload for the duration of the active session, without requiring an account.
- **FR-095**: Each cart line MUST show the product, its supplier attribution, its verified price
  where one exists, its quantity, and its line total where one is computable.
- **FR-096**: Visitors MUST be able to change a line's quantity and remove a line, with the cart,
  the header count, and any computable totals updating consistently and immediately.
- **FR-097**: The header MUST show the current cart line count, accurate across navigation and
  reload.
- **FR-098**: Monetary totals MUST be computed only from verified prices. Where any line in the cart
  lacks a verified price, the cart MUST NOT present an overall monetary total, MUST state that
  pricing for those items is provided on request, and MUST offer the enquiry action.
- **FR-099**: Every monetary total in this feature MUST be produced by one shared calculation
  routine; two surfaces MUST NOT compute the same total differently (Constitution VI.8).
- **FR-100**: An empty cart MUST show an empty state that explains it and offers a route into the
  range, and the proceed-to-checkout control MUST be disabled with its reason stated.
- **FR-101**: A cart line whose product no longer exists MUST be removed silently, with counts and
  any totals corrected and no error shown.
- **FR-102**: No cart surface may describe its contents as an order, a reservation, a held item, a
  payment, or a completed purchase.

#### Checkout and order review (FR-103 to FR-110)

- **FR-103**: Checkout MUST collect the visitor's contact and delivery information across clearly
  indicated steps, MUST show progress, and MUST allow backward navigation without losing entered
  values.
- **FR-104**: Every checkout step MUST be validated server-side, and the order-review state MUST be
  reachable only after all collected information has passed that validation.
- **FR-105**: Checkout MUST NOT present a payment step, a payment-method selector, a card-entry
  field, a saved-card option, or any simulated payment outcome.
- **FR-106**: The order-review state MUST show the cart lines with quantities, the entered contact
  and delivery information, and any computable monetary totals, and MUST allow the visitor to return
  and correct the cart and every entered value.
- **FR-107**: The order-review state MUST state plainly that no order has been placed and no payment
  has been taken.
- **FR-108**: The only submitting action available from the order-review state MUST be an enquiry
  that performs a real underlying operation. Feature 001 MUST NOT render any control that claims to
  place an order, complete a purchase, or take a payment.
- **FR-109**: Feature 001 MUST NOT create a production order record, MUST NOT issue an identifier
  presented to the visitor as an order number, and MUST NOT produce any artifact a visitor would
  reasonably read as a completed purchase.
- **FR-110**: If the cart changes or empties between entering checkout and reaching order review,
  the order-review state MUST refuse to present stale contents and MUST return the visitor to the
  cart with an explanation.

### Non-Functional Requirements

#### Visual fidelity and design system (NFR-001 to NFR-006)

- **NFR-001**: The storefront MUST satisfy RF-1 through RF-12 at 1440px, 1024px, 768px, and 390px.
- **NFR-002**: Every page MUST belong to one ZAKEY design system; page-specific visual identities are
  forbidden (Constitution I.7).
- **NFR-003**: Implemented token values MUST match the ratified tables in Constitution v1.1.0
  exactly — the 5 core brand tokens (primary navy `#0D1B3D`, accent gold `#C9A227`, background
  `#F8F9FB`, white `#FFFFFF`, primary text `#1F2937`), all 13 reference-derived support tokens, and
  the non-colour tokens (Poppins self-hosted, 8px base spacing unit, 12px primary radius, 1440px
  desktop reference, 12-column desktop grid, restrained shadows built from the navy-alpha tokens).
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
- **NFR-008**: Each width MUST receive a deliberate layout decision per §8 and the §8.1 matrix;
  stacking desktop columns is not sufficient, and neither is collapsing every grid to one column at
  mobile — the product-card grid is deliberately 4 / 4 / 2 / 2 across the four acceptance widths.
- **NFR-009**: Document scroll width MUST NOT exceed viewport width at any of the four widths,
  verified programmatically (Constitution VII.4).
- **NFR-010**: No clipped text, header collision, floating-control overlap, tablet dead zone, or
  oversized empty region at any of the four widths.
- **NFR-011**: Image dimensions MUST be stable across breakpoints; declared ratios MUST NOT change.
- **NFR-012**: Mobile navigation, filters, gallery, forms, cart, and checkout MUST each have
  dedicated responsive behavior.
- **NFR-013**: Content MUST remain usable and unclipped at 200% text scaling at every width.

#### Accessibility (NFR-014 to NFR-024)

- **NFR-014**: A-1 through A-20 MUST hold on every in-scope page.
- **NFR-015**: An automated axe run MUST report zero violations at the documented conformance level
  on every in-scope page and on each interactive surface in its open state, including the cart
  drawer and every checkout step.
- **NFR-016**: A manual keyboard inspection MUST cover tab order, focus visibility, focus trapping,
  and dismissal on every interactive surface, including the full cart-to-order-review journey.
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

- **NFR-025**: PB-1 through PB-4 and PB-18 page-weight budgets MUST be met.
- **NFR-026**: PB-5 through PB-7 asset budgets MUST be met.
- **NFR-027**: PB-8 through PB-10 Core Web Vitals targets MUST be met on a production-like run, and
  PB-19 state-update responsiveness MUST be met for cart and wishlist.
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

#### Security and privacy (NFR-039 to NFR-043)

- **NFR-039**: Every state-changing request MUST carry active cross-site request forgery protection
  (Constitution X.4).
- **NFR-040**: All visitor-supplied data MUST be validated server-side (Constitution X.5).
- **NFR-041**: No payment credential may be requested, transmitted, logged, or stored
  (Constitution VI.9).
- **NFR-042**: Logs MUST NOT contain personal information beyond what the feature requires, and
  never a credential (Constitution X.9).
- **NFR-043**: Contact and delivery information collected at checkout MUST be held only for the
  purpose of the enquiry the visitor submits, MUST NOT be exposed to another session, and MUST NOT
  be used to create a persistent customer account in this feature.

#### Color identity (NFR-044 to NFR-046)

- **NFR-044**: The exact reference color values and their role assignments MUST be documented
  before implementation begins, re-verified against the live reference during planning, and
  recorded as the palette of record (CID-1).
- **NFR-045**: Exactly one centralized token authority MUST define every color used by the
  storefront; zero literal color values may appear outside it (CID-2).
- **NFR-046**: Cross-page palette consistency MUST be inspected at 1440px, 1024px, 768px, and
  390px on every included page, and color comparison MUST be performed in both required visual
  critique passes, with per-page and per-width observations recorded (CID-4, Constitution XIII.3).

### Key Entities

- **Product** — a verified item ZAKEY sells. Attributes: public display name, summary, product type,
  supplier brand, supplier relationship, category, collections, access methods, media assignments
  with roles and order, approved specification fields, commerce mode, permitted public actions,
  verified sellable price where one exists. Carries no stock, rating, or warranty value.
- **Category** — a verified grouping by lock technology. Attributes: name, slug. Relationship: one
  category has many products; a product has exactly one category.
- **Collection (series)** — a verified product family. Attributes: name, slug. Relationship: many to
  many with products; a product may have none.
- **Access method** — a verified unlock capability used as a discovery facet. Attributes: name, slug.
  Relationship: many to many with products.
- **Media asset** — a verified image. Attributes: identifier, roles, sort order, intrinsic
  dimensions, alternative text. Relationship: many to many with products through role-carrying
  assignments.
- **Wishlist** — the visitor's session-scoped shortlist. Attributes: product references, time added.
  Not an order and not a commitment.
- **Cart** — the visitor's session-scoped selection. Attributes: lines, each with a product
  reference and a quantity; derived line totals and overall total, computable only where every
  referenced product carries a verified price. Not an order, not a reservation, not a payment.
- **Checkout information** — contact and delivery details supplied by the visitor during checkout.
  Attributes: name, contact details, delivery address fields, validation state. Session-scoped;
  never a persistent customer account. Contains no payment credential.
- **Order review** — the terminal validated state of checkout. Attributes: a snapshot of the cart
  lines, the validated checkout information, computable totals, and an explicit statement that no
  order has been placed and no payment taken. Produces no order record.
- **Enquiry** — a visitor's submitted request. Attributes: contact details, message, covered product
  lines with quantities, submission state. Carries no monetary commitment and is never presented as
  an order.
- **Announcement** — optional verified site-wide message. Attributes: message text, optional link.

---

## 15. Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 21 in-scope surfaces render at all four verification widths with no unhandled
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
- **SC-007**: Reference-fidelity comparison passes RF-1 through RF-12 on the homepage, listing page,
  product page, cart, and one informational page at all four widths, with inspected-screenshot
  observations recorded for each.
- **SC-008**: Document scroll width does not exceed viewport width on any in-scope page at 1440px,
  1024px, 768px, or 390px — zero failures across the programmatic check.
- **SC-009**: Zero instances of clipped text, header collision, floating-control overlap, tablet
  dead zone, or oversized empty region at any verification width.
- **SC-010**: Every in-scope page passes an automated axe run with zero violations at the documented
  conformance level.
- **SC-011**: A manual keyboard pass completes every in-scope journey — browse, filter, search,
  inspect a product, wishlist, add to cart, edit the cart, complete checkout to order review, and
  send an enquiry — using the keyboard alone, with observations recorded.
- **SC-012**: 100% of focusable controls show a visible focus indicator meeting 3:1 contrast.
- **SC-013**: 100% of interactive targets meet 24×24 CSS pixels; 100% of primary mobile actions meet
  44×44.
- **SC-014**: Zero uses of accent gold as text, as a meaningful icon, or on any element bearing a
  non-text contrast requirement over `#FFFFFF` or `#F8F9FB`.
- **SC-015**: Filtering by any single facet returns only products carrying that facet — 100%
  precision across all 15 verified facet values.
- **SC-016**: Filter, sort, and pagination state reloads to an identical result set from its
  destination address in 100% of tested combinations.
- **SC-017**: A search for each verified model code returns that product within the first page of
  results in 100% of cases.
- **SC-018**: No-results states appear for zero-match filter combinations and zero-match searches in
  100% of tested cases, each offering a working recovery control.
- **SC-019**: A content audit of every visible string finds zero **unverified** prices and zero
  currencies, discounts, stock figures, ratings, review counts, awards, certifications, press
  mentions, customer counts, tax values, warranty claims, or delivery promises.
- **SC-020**: A content audit finds zero occurrences of internal terminology in visible copy,
  alternative text, titles, ARIA labels, visible filenames, or metadata.
- **SC-021**: 100% of displayed product names, images, and specification fields match the verified
  catalog exactly; zero invented, renamed, or rebranded product identities.
- **SC-022**: Zero fields anywhere in the feature collect a card number, expiry date, security code,
  or PIN.
- **SC-023**: Every success state in the feature is preceded by a confirmed successful underlying
  operation; zero success states appear on a failed or absent operation, verified by fault
  injection.
- **SC-024**: Every form and every checkout step rejects an invalid submission server-side with
  field-level messages programmatically associated with their fields — 100% of tested invalid cases.
- **SC-025**: Zero unexpected console errors on any in-scope page, captured automatically during
  end-to-end verification.
- **SC-026**: Page-weight budgets PB-1 through PB-4 and PB-18, and asset budgets PB-5 through PB-7,
  are met on a production build.
- **SC-027**: Core Web Vitals targets PB-8 through PB-10 and the state-update target PB-19 are met on
  a production-like run.
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
- **SC-035**: Cart contents survive at least 5 page transitions and a full reload within a session
  with identical lines and quantities — 100% of tested cases.
- **SC-036**: Wishlist contents survive the same navigation and reload sequence unchanged — 100% of
  tested cases.
- **SC-037**: The order-review state is reachable only after every collected checkout field has
  passed server-side validation; 100% of invalid checkout submissions are rejected server-side.
- **SC-038**: Zero controls anywhere in the accepted interface claim to place an order, complete a
  purchase, confirm a payment, or issue an order number, verified by the §7 control audit and a
  visible-copy audit.
- **SC-039**: Zero payment steps, payment-method selectors, saved-card options, and simulated
  payment outcomes exist anywhere in the feature.
- **SC-040**: 100% of displayed monetary totals derive solely from verified prices and are produced
  by one shared calculation routine; zero monetary totals are presented for a cart or enquiry
  containing a line without a verified price.
- **SC-041**: 100% of products display their real supplier attribution; zero products are presented,
  implied, or styled as ZAKEY-manufactured.
- **SC-042**: Zero synthetic or example prices appear in production-facing content, evidence
  screenshots, fixtures, or seeded storefront data.
- **SC-043**: 100% of in-scope surfaces have a stable destination that can be shared and reloaded to
  the same content.
- **SC-044**: Zero order records, order identifiers presented as orders, or purchase-completion
  artifacts are created by Feature 001, verified by inspecting stored state after a complete
  checkout-to-enquiry journey.
- **SC-045**: The exact reference color values and their role assignments are documented before
  implementation begins — 100% of palette roles covered, with zero roles left to implementer
  discretion.
- **SC-046**: 100% of rendered colors across every included page resolve to the centralized token
  authority; zero literal color values exist in templates, components, stylesheets, or scripts,
  verified by an automated source audit.
- **SC-047**: Zero colors, gradients, dark-section treatments, card colors, or button colors appear
  that are not present in the documented reference palette; zero black or near-black full-bleed
  sections that read as an unintended dark theme.
- **SC-048**: The palette is identical across every included page — zero divergent gold shades,
  card colors, or button colors between the homepage and any internal public page, verified at
  1440px, 1024px, 768px, and 390px.
- **SC-049**: Color comparison against the reference is performed and recorded in both required
  visual critique passes, with per-page and per-width observations.
- **SC-050**: Every token pairing actually in use passes its WCAG 2.2 AA contrast threshold — zero
  failures; zero uses of `#C9A227` as normal-sized text on a light background; and zero uses of
  `#9CA3AF` as text of any size, including placeholder text, which uses `#6B7280` instead.
- **SC-051**: Every product-card listing grid renders the §8.1 column count at each acceptance width
  — **4 at 1440px, 4 at 1024px, 2 at 768px, 2 at 390px** — with zero horizontal overflow, zero
  clipped or overlapping content, 100% of product media at the 1:1 ratio, 100% of interactive targets
  meeting 24×24 (44×44 for the primary commerce action), and supplier attribution and the
  price-or-price-on-request statement fully visible on every card at every width — inspected and
  recorded at **all four widths** in **both** required visual critique passes.

---

## 16. Assumptions

1. `/media/mekky/work/backend/zakey.v1` is the genuine legacy ZAKEY project and the authoritative
   initial product-content source; the originally requested `/media/mekky/work/backend/zakey` does
   not exist. Governance confirmation of this substitution is still recorded as RRP-1.
2. The verified launch catalog (21 products, 3 categories, 6 collections, 6 access methods, 25 media
   assets) is the complete approved product set for this feature. No other product or media asset is
   approved.
3. ZAKEY is the retailer, not the manufacturer, of the products in this catalog. All 21 are
   supplier-branded (Lezn) and are presented as such.
4. No product in the current catalog carries a verified sellable price, so no monetary total will be
   presented at launch. The storefront's pricing and totalling surfaces are nonetheless built and
   tested so that supplying verified prices later activates them without redesign.
5. Cart, wishlist, and checkout information are session-scoped and require no account. They are
   never an order, a reservation, or a payment.
6. Checkout terminates at the validated order-review state. The only submitting action from there is
   a real enquiry; Feature 001 creates no order.
7. Product comparison is deferred to Feature 010 and renders no control in this feature.
8. Where verified content for a surface does not exist, the surface and its links are removed
   together rather than filled with drafted text (CI-15).
9. Currency, tax, shipping charges, and delivery terms are absent from this feature entirely,
   because no verified values exist.
10. Visitors are anonymous. No account, sign-in, or persistent profile exists in this feature.
11. Storefront content is presented in English in this feature; the architecture stays ready for
    later localization and right-to-left layout, with no language selector exposed
    (Constitution IV.9).
12. The visual reference governs appearance only. Its single client-side route, its routing model,
    and its architecture place no constraint on ZAKEY's destinations or implementation.
13. Reference defects RD-1 through RD-13 are defects, not requirements, and are corrected as
    recorded; accessibility corrections take precedence over reference similarity.
14. The reference is a stable artifact for the duration of this feature; if it changes materially,
    §2.2 must be re-inspected and this specification amended.

---

## 17. Dependencies

1. **Ratified constitution v1.1.0** — governs every requirement here. v1.0.1 closed the legacy-path
   TODO, confirming `/media/mekky/work/backend/zakey.v1` as the authoritative initial
   product-content source. v1.1.0 ratified the complete 18-value colour system, so no palette
   dependency remains open.
2. **Verified legacy catalog** — `specs/012-smart-storefront-commerce/data/curated-launch-catalog.v2.json`
   in the legacy repository, read-only. Confirmed as the authoritative initial product-content
   source.
3. **Verified brand assets** — ZAKEY logo files in the legacy repository's `static/brand/` and
   `static/icons/`, read-only.
4. **Verified product imagery** — legacy `reference-imports/spec-012/`, read-only. Images must be
   assessed for resolution and cropping suitability during planning.
5. **Verified hero image** — a high-quality ZAKEY smart-lock image satisfying Constitution I.5. If
   none of the verified imagery is suitable at hero scale, this becomes an implementation blocker to
   raise, not a reason to ship the reference's unsuitable image.
6. **Verified sellable prices** — required before any monetary figure or total is displayed. Absent
   today; owned by Feature 002. Their absence does not block this feature, because the
   price-on-request behavior is fully specified.
7. **Verified contact details** — required before the Contact page renders a contact-details block.
8. **Verified legal text** — required before Privacy and Terms pages ship (FR-070).
9. **Verified announcement content** — required before the announcement bar renders (FR-002).
10. **Approved stack** — as recorded in the constitution's Canonical Project Facts. Selection and
    configuration belong to `/speckit-plan`, not to this specification.
11. **Repository readiness** — the blockers in §18 must be resolved before implementation.

---

## 18. Repository Readiness Preconditions

These are verified repository-hygiene and governance findings, **not** storefront product
requirements. Each was independently confirmed locally on 2026-07-31 during `/speckit-specify`,
then remediated or re-verified during the pre-planning readiness pass of the same day. The
historical finding is preserved alongside its outcome so the record stays auditable.

**Status summary: 9 of 10 CLOSED. 1 OPEN (scoped, non-blocking for planning and task generation).
Zero planning blockers remain. Zero task-generation blockers remain.**

| # | Original finding | Remediation / current status | Verification evidence | Status | Remaining owner |
| --- | --- | --- | --- | --- | --- |
| RRP-1 | Constitution carried an open `TODO(LEGACY_REPO_PATH_CONFIRMATION)`; the instruction named `/media/mekky/work/backend/zakey`, which does not exist | User confirmed `/media/mekky/work/backend/zakey.v1` as the verified legacy project and authoritative initial product-content source. Constitution amended to v1.0.1: the TODO moved to a "Resolved items" record, the Canonical Project Facts note now states the confirmation inline, and the sync-impact report records the PATCH rationale | `.specify/memory/constitution.md` — "Deferred items / TODOs: (none open)"; version footer reads 1.1.0 (v1.0.1 made this change, v1.1.0 superseded it); legacy HEAD `5fdd81d`, `git status --porcelain` → 0 lines | **CLOSED** | — |
| RRP-2 | No `.gitignore` at the repository root | Created a stack-specific ignore policy covering Python bytecode and caches, virtual environments, environment files and secrets, SQLite databases with their journal/WAL sidecars, `staticfiles/`, `node_modules/` and package caches, pytest/ruff/mypy caches, coverage output, Playwright results and reports, temporary screenshots and recordings, logs, and editor/OS artifacts. Lockfiles, manifests, migrations, fixtures, `specs/**`, and `static/**` are explicitly NOT ignored | `.gitignore` present at repository root; `git check-ignore -v node_modules/` → `.gitignore:80:node_modules/` | **CLOSED** | — |
| RRP-3 | `node_modules/` tracked in Git — 4,571 files | Removed from the Git index only, after `.gitignore` was in place. The local directory was not touched: `git rm -r --cached node_modules` | `git ls-files node_modules \| wc -l` → `0`; staged deletions → `4571`; local directory still present with 36 top-level entries; lockfiles and manifests unmodified | **CLOSED** — staged, awaiting the user's commit | User (commit) |
| RRP-4 | `.specify/init-options.json` and `.specify/integration.json` declared Kimi as integration and default integration while Claude Spec Kit skills were installed and in use, contradicting Constitution XVI.1 | Both files corrected to declare Claude Code as the integration and workflow owner, using the repository's existing schema and the installed `claude.manifest.json` conventions. `installed_integrations` now accurately lists the three integrations with manifests on disk (claude, codex, kimi). Kimi and Codex assets were left on disk but hold no authority | `.specify/integration.json` → `"integration": "claude"`, `"default_integration": "claude"`; `.specify/init-options.json` → `"ai": "claude"`, `"integration": "claude"`, `"context_file": "CLAUDE.md"`; both parse as valid JSON | **CLOSED** | — |
| RRP-5 | `spec-template.md` lacked out-of-scope, UI inventory, performance budgets, and reference-fidelity method | Template rebuilt around all 21 constitution-required sections with applicability rules, so a future specification cannot silently omit a mandatory gate. Kept generic — no Feature 001 product content was hardcoded | `.specify/templates/spec-template.md`; sync-impact report marks it `✅ aligned` | **CLOSED** | — |
| RRP-6 | `plan-template.md` Constitution Check was a bare placeholder | Replaced with a per-principle gate table for I–XVIII requiring cited evidence per principle, an initial gate and a post-design re-check, a blocking-violations register that must be empty before Phase 0, and a per-dependency assessment table satisfying Principle III.4 | `.specify/templates/plan-template.md`; sync-impact report marks it `✅ aligned` | **CLOSED** | — |
| RRP-7 | `tasks-template.md` declared tests optional, contradicting Principle XII, and lacked visual-QA and accessibility categories | The "Tests are OPTIONAL" instruction was removed and replaced with an applicability rule requiring explicit justification for any exclusion. Added "Phase V: Verification" covering Django system checks, unit/integration/model/service/form/view/permission/template-rendering tests, JavaScript behavior tests, Playwright, axe, manual keyboard inspection, broken-link and console-error checks, responsive-overflow checks, production asset build, screenshot capture **and** inspection, two visual critique passes, guard skills, documentation verification, and exact final verification commands and results | `.specify/templates/tasks-template.md`; zero occurrences of "OPTIONAL" or "if requested" remain; sync-impact report marks it `✅ aligned` | **CLOSED** | — |
| RRP-8 | `checklist-template.md` not aligned with the fifteen conditions of Principle XVIII | Added a required "Definition of Done" section carrying all fifteen conditions as DOD01–DOD15, with an instruction that they must not be deleted and that a non-applicable condition must state its reason | `.specify/templates/checklist-template.md`; sync-impact report marks it `✅ aligned` | **CLOSED** | — |
| RRP-9 | `README.md` empty (0 bytes); `main.py` a generated Hello World; no Django project exists | Unchanged and correct for this stage — no application implementation is authorized before planning. Documentation currency is a Definition-of-Done condition (XVIII.12) enforced at acceptance, not a planning prerequisite. `main.py` will be superseded when the Django project is created under `/speckit-plan` and `/speckit-implement` | `README.md` → 0 bytes; `main.py` unchanged; repository contains no Django project | **OPEN — non-blocking** | Implementation phase (XVIII.12) |
| RRP-10 | No verified ZAKEY contact details or legal text in either repository; legacy contact values are placeholders | Unchanged as a finding, but no longer a blocker: the specification resolves it by rule rather than by data. CI-15 and FR-070 require that any surface without verified content is removed together with every link to it, so the storefront can ship truthfully without these facts. If the user supplies verified details and legal text, the Contact details block, Privacy page, and Terms page activate without redesign | `specs/001-premium-storefront-experience/spec.md` CI-15, FR-068, FR-070; legacy placeholders `+1 (000) 000-0000`, `+201234567890` unchanged | **CLOSED as a blocker** — content dependency remains open by design | User (optional content supply) |

**Blocker reconciliation by original severity.**

- **Full blockers (6): RRP-1, RRP-2, RRP-3, RRP-4, RRP-6, RRP-7 — all CLOSED by remediation.**
  These included every blocker for `/speckit-plan` (RRP-1, RRP-4, RRP-6), every blocker for
  `/speckit-tasks` (RRP-7), and both first-commit blockers (RRP-2, RRP-3).
- **Scoped blocker (1): RRP-10 — blocking aspect CLOSED.** The specification resolves it by rule
  (CI-15) rather than by data, so no surface can ship as a dead link or with drafted text.
- **High (2): RRP-5, RRP-8 — both CLOSED by template alignment.**
- **Medium (1): RRP-9 — OPEN, non-blocking.** Documentation currency is an acceptance-stage
  Definition-of-Done condition (XVIII.12), not a planning prerequisite.

Nine of ten closed. **Zero blockers remain for `/speckit-plan` or `/speckit-tasks`, and zero
colour-governance decisions remain open** — Constitution v1.1.0 ratifies the complete 18-value
palette, so the plan performs implementation mapping and token naming only. The
specification's earlier summary line described this set as "seven blockers"; the accurate
original classification was six full blockers plus one scoped blocker, and that count is
corrected here.

---

## 19. Explicit Out of Scope

Each item below is deferred, with the future specification that owns it named. Constitution VI.2
means none of these may render a control in the accepted interface.

| Capability | Owning future specification |
| --- | --- |
| Production product database and catalog management | Feature 002 — Commerce Foundation |
| Production order creation, order records, and order numbers | Feature 002 — Commerce Foundation |
| Order success / order confirmation state | Feature 002 — Commerce Foundation |
| Production inventory management | Feature 002 — Commerce Foundation |
| Retail pricing, currency, tax, and discounts | Feature 002 — Commerce Foundation |
| Shipping charges, delivery terms, returns, and warranty information pages | Feature 002 — Commerce Foundation |
| Shipping-provider integration | Feature 002 — Commerce Foundation |
| Tax integration | Feature 002 — Commerce Foundation |
| Payment gateway integration, payment steps, and any card collection | Feature 002 — Commerce Foundation |
| Fulfilment | Feature 002 — Commerce Foundation |
| Persistent customer accounts, authentication, order history, saved addresses, saved payment methods | Feature 003 — Customer Accounts |
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
| Product comparison | Feature 010 — Product Comparison |

**Explicitly retained, not deferred**: architecture readiness for later localization and
right-to-left layout (FR-078). The capability is deferred; the readiness is required now.

**Feature 001 / Feature 002 boundary, stated plainly.** Feature 001 owns everything a visitor can do
without a persistent commercial record: browsing, discovery, product inspection, a session cart, a
session wishlist, checkout information collection, a validated order review, and a real enquiry.
Feature 002 owns everything that requires one: the persistent catalog, prices, inventory, orders,
payment, and fulfilment. The seam is the order-review state — Feature 001 renders it truthfully and
stops; Feature 002 later attaches order creation and payment behind it.

---

## 20. Constitution Compliance

| Principle | How this specification complies |
| --- | --- |
| I. Reference-Led Visual Fidelity | §2.2 records reference evidence, the fully ratified 18-value palette, and thirteen defects; §11 defines RF-1–RF-12 with named pages, widths, and acceptance method; §11.1 makes the reference the binding color authority; RD-10 preserves the hero composition and replaces its image; RF-12 makes accessibility outrank similarity |
| II. Permanent ZAKEY Brand System | NFR-003 fixes the ratified tokens; Constitution v1.1.0 ratifies the complete 18-value system — 5 core brand tokens and 13 reference-derived support tokens, each with observable role, permitted uses, and measured contrast; NFR-004 the 8px rhythm; FR-076, FR-116, and NFR-045 mandate one token authority with zero literal colours; FR-114 makes every support token binding; FR-115 forbids unauthorized colours, gradients, and dark sections; FR-117 forbids palette drift; FR-118, NFR-017, and A-9 enforce the accent-gold role restriction, correcting RD-1 without inventing a replacement gold; FR-120 corrects RD-13 using the reference's own `#6B7280`; FR-119 bounds any last-resort accessibility shade. **Zero palette decisions remain open for `/speckit-plan`** |
| III. Approved Technical Foundation | NFR-032 forbids runtime third-party origins; PB-13 measures it; NFR-037 forbids copied Figma runtime code; stack selection is deferred to `/speckit-plan` |
| IV. Clean-Room Architecture | NFR-036 forbids copying legacy frontend code; NFR-038 and SC-032 hold the legacy repository read-only; FR-071–FR-075 mandate one data adapter and one implementation per component; FR-078 preserves localization readiness |
| V. Content and Asset Integrity | §10 CI-1–CI-17; RD-2–RD-8 remove every fabricated claim in the reference; FR-111–FR-113 protect product truth, supplier attribution, and price honesty; SC-019–SC-021, SC-041, SC-042 measure it |
| VI. Functional Completeness | §7 gives every control defined behavior; FR-010 forbids dead controls and `#`; FR-052, FR-059, FR-108, FR-109 forbid fake success and any order claim; FR-051 and FR-105 forbid card data and payment steps; FR-099 requires one shared totalling routine; FR-053 removes controls belonging to deferred features; FR-077 requires named route lookups |
| VII. Responsive Design | §8 gives every surface, including cart and checkout, a deliberate layout at all four widths; NFR-007–NFR-013; SC-008 and SC-009 measure it |
| VIII. Accessibility | §12 A-1–A-21; NFR-014–NFR-024; SC-010–SC-014; A-21 requires both automated axe and a manual keyboard pass across the full cart-to-review journey |
| IX. Performance and Frontend Quality | §13 PB-1–PB-19 set before implementation; NFR-025–NFR-033; SC-025–SC-030 |
| X. Security, Privacy, and Data Safety | NFR-039–NFR-043; FR-055 and FR-104 server-side validation; FR-087 escaping; FR-051 no payment credentials; NFR-043 bounds the use of checkout information |
| XI. Specification-First Development | This document precedes planning; §19 states what is out of scope and draws the 001/002 boundary explicitly; §3 records the resolved clarifications; §21 gives traceability |
| XII. Test-First Acceptance | §15 defines 44 measurable criteria before implementation; SC-023 requires fault injection and SC-044 requires stored-state inspection; verification methods are named per budget and per criterion |
| XIII. Visual QA and Consistency | §5–§9 supply the page, component, interaction, responsive, and state inventories; §11 requires inspected screenshots and two critique passes; NFR-006 and SC-006 make cross-page divergence a defect |
| XIV. Code Quality | Deferred to `/speckit-plan` and `/speckit-tasks` by nature; NFR-035 constrains the JavaScript architecture at the specification level |
| XV. Git and Repository Safety | A separate local numeric branch is in use; no commit, push, pull request, merge, remote change, or history rewrite was performed by this workflow; §18 records ignore-policy blockers RRP-2 and RRP-3 without fixing them |
| XVI. Claude Code Governance | Specification authored and owned by Claude Opus; no delegation occurred; RRP-4 records the contradicting integration configuration |
| XVII. LeanCtx and Context Discipline | Inspection was targeted and evidence-driven; all evidence, decisions, and blockers are written into this artifact rather than left in conversation |
| XVIII. Definition of Done | §15 plus §21 make every requirement traceable to a criterion; §18 records known blockers truthfully; the fifteen conditions govern acceptance of the implementation, not of this specification |

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
| FR-091, FR-092 | SC-043, SC-016, US2.2, US5.5 |
| FR-013, FR-014, FR-015 | SC-001, SC-002, US2.1 |
| FR-016, FR-018 | SC-015, US2.2, US2.3 |
| FR-017, FR-022 | SC-019, SC-003 |
| FR-019, FR-020 | SC-018, US2.3, US2.5 |
| FR-021 | SC-016, SC-043, US2.2, US2.7 |
| FR-023, FR-088 | SC-001, SC-016 |
| FR-024, FR-027 | SC-018, US2.4, US5.3, US5.4 |
| FR-025 | SC-009, SC-011, US2.6 |
| FR-026 | SC-017, US5.2 |
| FR-028 | SC-006, SC-007 |
| FR-121 | SC-051, SC-008, SC-013, US2.8 |
| FR-029, FR-030, FR-035, FR-038 | SC-021, SC-019, US3.1, US3.3 |
| FR-031, FR-039 | SC-001, US3.1 |
| FR-032, FR-033 | SC-011, US3.2 |
| FR-034 | SC-019, SC-040, US3.4 |
| FR-036 | SC-019, US3.4 |
| FR-037 | SC-001, US3.6 |
| FR-040 | SC-041, US3.5, US7.2 |
| FR-041 | SC-028, SC-020 |
| FR-111, FR-112 | SC-021, SC-041, US3.5 |
| FR-113 | SC-042 |
| FR-042, FR-043 | SC-003, US4.1 |
| FR-044 | SC-001, US4.6 |
| FR-045 | SC-036, US4.1 |
| FR-046, FR-102 | SC-038, US4.7 |
| FR-047, FR-101 | SC-003, edge cases |
| FR-048, FR-049 | SC-001, US4.5, US6.8 |
| FR-050 | SC-040, US4.5 |
| FR-051 | SC-022, SC-039, US6.7 |
| FR-052, FR-059 | SC-023, SC-038, US6.8, US6.9 |
| FR-053 | SC-003, SC-033 |
| FR-054 | SC-010, SC-024, US6.2 |
| FR-055, FR-056 | SC-024, US6.2, US6.3 |
| FR-057, FR-060 | SC-024, US6.9 |
| FR-058 | SC-023, US6.8 |
| FR-061 | SC-011 |
| FR-062 | SC-008, SC-013 |
| FR-063, FR-064, FR-065, FR-066 | SC-019, SC-020 |
| FR-067 | SC-041, US7.2 |
| FR-068, FR-070 | SC-004, SC-019, US7.1 |
| FR-069 | SC-010, SC-011, US7.3 |
| FR-071, FR-072, FR-073, FR-074 | SC-031 |
| FR-075 | SC-005, SC-006 |
| FR-076 | SC-007, SC-014 |
| FR-077 | SC-004 |
| FR-078 | SC-001 (architecture readiness reviewed at plan gate) |
| FR-079 | SC-027, SC-028 |
| FR-080, FR-081 | SC-018, SC-001 |
| FR-082 | SC-003, SC-010 |
| FR-083 | SC-010, SC-011 |
| FR-084, FR-085, FR-086 | SC-001, SC-004 |
| FR-087 | SC-019, edge cases |
| FR-089 | SC-003, SC-025 |
| FR-093 | SC-035, US4.2 |
| FR-094 | SC-035, US4.3 |
| FR-095 | SC-040, US4.2 |
| FR-096 | SC-035, US4.4 |
| FR-097 | SC-035, US4.2 |
| FR-098 | SC-040, US4.5 |
| FR-099 | SC-040 |
| FR-100 | SC-018, US4.6 |
| FR-103 | SC-011, US6.1, US6.4 |
| FR-104 | SC-037, SC-024, US6.2 |
| FR-105 | SC-039, SC-022, US6.7 |
| FR-106 | SC-011, US6.5 |
| FR-107 | SC-038, US6.5 |
| FR-108 | SC-038, SC-044, US6.6, US6.8 |
| FR-109 | SC-044, SC-038 |
| FR-110 | SC-035, edge cases |
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
| NFR-039, NFR-040 | SC-024, SC-037 |
| NFR-041 | SC-022, SC-039 |
| NFR-042, NFR-043 | SC-022, SC-044 |
| FR-114 | SC-045, SC-046, SC-047 |
| FR-115 | SC-047, SC-049 |
| FR-116 | SC-046 |
| FR-117 | SC-048, SC-049 |
| FR-118 | SC-050, SC-014 |
| FR-119 | SC-050, SC-045 |
| FR-120 | SC-050, SC-010 |
| NFR-044 | SC-045 |
| NFR-045 | SC-046 |
| NFR-046 | SC-048, SC-049 |

**Coverage**: 121 functional requirements and 46 non-functional requirements — 167 total — all
mapped. 51 success criteria, all reachable from at least one requirement.

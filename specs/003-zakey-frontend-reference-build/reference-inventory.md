# Live Reference Inventory — ZAKEY Frontend Reference Build

**Feature**: `003-zakey-frontend-reference-build`
**Reference**: <https://remote-fried-86528699.figma.site/>
**Inspected**: 2026-08-01 with Google Chrome 150 through the Chrome DevTools Protocol
**Required widths**: 1440px, 1024px, 768px, 390px
**Status**: Reference inspection gate passed

## Authority and inspection method

The live reference is the binding visual authority. It is a stateful single-page
prototype: all screen transitions render at the root URL, so an unchanged URL does
not mean that a secondary screen is absent. The inventory records the visible state
reached through the reference controls and maps that state to the explicit ZAKEY v2
route the implementation will expose.

Codex personally opened the reference, followed its navigation, exercised search,
mobile navigation, product, cart, checkout, account, filter and tab controls, and
reviewed full-page captures at each required width. The Figma Make attribution
overlay visible in evidence is tooling chrome and is not part of the design.

## Discovered screen states and implementation routes

| Reference state | How it was reached | ZAKEY v2 route | Evidence at 1440/1024/768/390 |
|---|---|---|---|
| Home | Initial state / Home | `/` | Yes / Yes / Yes / Yes |
| Shop | Shop navigation | `/shop/` | Yes / Yes / Yes / Yes |
| Search open | Header search icon | `/search/?q=` presentation | Yes / Yes / Yes / Yes |
| Product details | Shop → first View | `/products/zakey-apex-pro/` | Yes / Yes / Yes / Yes |
| Empty cart | Header cart icon | `/cart/?state=empty` | Yes / Yes / Yes / Yes |
| Populated cart | Product → Add to Cart → cart icon | `/cart/` | Yes / Yes / Yes / Yes |
| Checkout: Shipping | Populated cart → Proceed to Checkout | `/checkout/` | Yes / Yes / Yes / Yes |
| Checkout: Payment | Shipping → Continue to Payment | `/checkout/?step=payment` prototype state | Yes / — / — / Yes |
| Signed-in account | Header account icon | `/account/?state=signed-in` | Yes / Yes / Yes / Yes |
| Account wishlist empty | Account → Wishlist | `/account/?tab=wishlist` | Yes / — / — / — |
| About | About navigation | `/about/` | Yes / Yes / Yes / Yes |
| Contact | Contact navigation | `/contact/` | Yes / Yes / Yes / Yes |
| Mobile menu open | Menu button at 390 | shared dialog state | — / — / — / Yes |
| Shop filter open | Shop → Filters at 390 | shared drawer state | — / — / — / Yes |
| Product specifications | Product → Specifications | product tab state | Yes / — / — / — |
| Product FAQ | Product → FAQ | product tab/accordion state | — / — / — / Yes |

The reference does not provide dedicated 404, 5xx, category, search-results,
standalone wishlist, signed-out account, or contact-result screens. Those required
screens must extend the same shared composition and component grammar. Typing a
query into the expanded reference search field did not transition to results.

## Navigation structure

Desktop navigation order is Home, Shop, About, Contact, Products, followed by
search, account, wishlist, cart and a Shop Now CTA. Products displays a chevron,
but hover and click did not expose a usable submenu. At 768px the text navigation
and Shop Now CTA collapse; the icon group adds a menu control. At 390px the visible
header controls are search, cart and menu. The open mobile menu contains Home,
Shop, About and Contact.

The implementation will preserve this hierarchy in RTL order, add accessible names,
and make the Products menu, mobile menu and all routes functional.

## Shared page frame

1. Announcement bar in navy with centered offer text and a gold emphasis token.
2. White header with navy logo mark, primary navigation and 40px icon controls.
3. Page-specific main content on `#F8F9FB` or white surfaces.
4. Navy footer with a brand column, Products, Company and Support link groups,
   social controls, a divider, copyright and legal links.

The announcement bar is approximately 40px high through 768px and wraps to about
60px at 390px. The header is approximately 73px. Desktop page gutters are 48px;
768px and 390px use 24px gutters. The desktop content system behaves as a 12-column
grid with roughly 24px gaps.

## Home inventory

Exact reference order:

1. Announcement bar
2. Header/navigation
3. Split premium hero
4. Five-benefit trust strip
5. Shop by Category
6. Best Sellers
7. ZAKEY Nexus Elite promotional band
8. Featured Products
9. Why Choose ZAKEY
10. Works With Your Smart Home
11. Customer testimonials
12. Partner/press strip
13. Newsletter
14. Footer

The hero uses a navy split field with headline and CTAs on one side and a product
composition with status/price chips on the other. It is dense rather than empty:
the text, trust metrics, product image and controls occupy the first screen. Hero
height is about 880px through 1024px and about 1188–1200px once stacked. Category
cards use four columns through 1024px and two columns at 768px and 390px. Product
cards use four columns through 1024px, two at 768px and one at 390px.

## Shop inventory

Section order:

1. Breadcrumb and navy page-intro band
2. Filter/sidebar and results-toolbar shell
3. Product grid
4. Pagination
5. Footer

At 1440px the filter content is about 238px and products begin around x=389 in the
LTR source. The grid is three columns at 1440px, two at 1024px and 768px, and one at
390px. Sidebar filtering remains visible through 1024px and becomes a Filters
control at 768px. The toolbar combines product count, sort select and grid/list
buttons. Product cards use near-square media, a type eyebrow, title, rating, price,
optional prior price/badge and a compact View button.

The captured 390px filter-open state expands the desktop sidebar in-flow and causes
a 748px document width; it is an obvious reference defect. ZAKEY v2 must instead
use a modal RTL drawer with focus containment, Escape-to-close and no overflow.

## Product-details inventory

Section order:

1. Breadcrumb
2. Two-column gallery and product summary
3. Thumbnail rail
4. Trust benefits
5. Features / Specifications / Downloads / Reviews / FAQ panel
6. You May Also Like product grid
7. Footer

The 1440px page places the gallery and summary in approximately equal columns.
The main image is square with four square thumbnails. The summary contains badge,
name, rating, price, finish choices, quantity, stock, Buy Now, Add to Cart, wishlist
and three benefit items. At 768px and 390px the gallery stacks before the summary.
Buy Now and Add to Cart remain paired. Related products are four columns through
1024px and two columns at 768px and 390px.

Specifications are presented as a two-column key/value table. FAQ is a stack of
five disclosure rows. At 390px, the reference tab row clips later tabs; ZAKEY v2
must use a keyboard-accessible horizontally scrollable or wrapping tablist without
hiding controls.

## Cart inventory

The empty state uses the Shopping Cart heading, a large centered white panel,
muted cart icon, short message and Shop Now CTA. The populated state uses a line
item and coupon region beside an order-summary card at desktop/1024. At 768px and
below the summary stacks after the items. The reference line item includes product
media, category, title, finish, quantity and price; the summary includes subtotal,
shipping, tax, total and two CTAs.

The reference mobile populated cart clips Apply, prices and summary buttons beyond
390px. ZAKEY v2 must reflow these controls and keep the document width at the
viewport width.

## Checkout inventory

The checkout uses a centered three-step indicator: Shipping, Payment, Review. On
desktop and 1024px, the form is the primary column and Order Summary is the
secondary column. At 768px and 390px the summary stacks below the form.

Shipping contains paired names, email, phone, street, unit/city, postal/state,
country, shipping radios and Continue to Payment. Payment contains three method
tabs, cardholder, card number, expiry/CVV, Back and Review Order. The written ZAKEY
requirements replace the US fields and payment labels with Egyptian governorate,
area, mobile, shipping, installation and prototype payment data while retaining
the reference structure. No real order or paid-success state will be created.

## Account and wishlist inventory

The signed-in account uses a profile card and vertical navigation beside a large
content panel. Navigation items are My Orders, Wishlist, Addresses, Payment Methods,
Account Settings and Sign Out. At 768px and 390px the profile, navigation and content
stack. My Orders uses simple rows with product, prototype identifier/date, price and
status badge. The Wishlist account tab contains a centered empty state and Explore
Products CTA. Required populated wishlist and signed-out states will extend the same
cards and spacing.

## About inventory

Section order:

1. Image-backed navy story hero
2. Four achievement/stat cards
3. Mission copy and image split
4. Four-person leadership grid
5. Footer

The hero centers a gold eyebrow, large two-line heading and supporting copy. The
mission is split through 1024px and stacks at 768px. Stats and team use four columns
through 1024px and two columns at 768px/390px. Arabic names and ZAKEY-specific copy
will replace the reference’s English demonstration names.

## Contact inventory

Section order:

1. Navy contact hero
2. Three contact-method cards
3. Message form beside FAQ and live-chat cards
4. Footer

The three contact cards become a single column at 768px. The form and FAQ/chat split
also stack at 768px. First and last name remain paired in the 390px reference; the
implementation may stack fields when Arabic labels or validation require more room.
The reference has no submission/validation result; ZAKEY v2 will implement intentional
prototype validation, loading and recoverable result states without sending data.

## Visual system measurements

| Token or pattern | Reference evidence | ZAKEY v2 interpretation |
|---|---|---|
| Primary navy | `#0D1B3D` | Primary text, CTAs, hero/footer bands |
| Accent gold | `#C9A227` | Active labels, badges and deliberate primary accents |
| Page background | `#F8F9FB` | Global light page canvas |
| Main text | `#1F2937` | Body and product copy |
| Muted text | approximately `#6B7280` | Supporting copy |
| Surfaces | white / very light gray | Cards, forms and panels |
| Radius | mainly 12–16px | Governed 12px system; pill only for chips/status |
| Shadow | subtle, low-blur gray | Restrained elevation only |
| Desktop gutters | approximately 48px | max-width container with 48px minimum gutters |
| Tablet/mobile gutters | approximately 24px | 24px, reduced only for very narrow controls |
| Grid gap | approximately 24px | 8px spacing increments |
| Icon controls | 40×40px | minimum 44×44px touch target where space permits |
| Product media | near 1:1 | consistent square media shell |

The reference’s dominant Latin display face is Poppins. The Arabic implementation
uses Cairo as the primary family and limits Poppins to appropriate Latin tokens.
Observed hero headings are about 72/79px at 1440, 60/66px at 1024 and 48/53px at
768/390; Arabic sizes may be optically adjusted to prevent clipping while preserving
hierarchy. Section headings are about 36/40px in the source.

## Responsive transformation rules

| Pattern | 1440 | 1024 | 768 | 390 |
|---|---|---|---|---|
| Header nav | Full | Full | Icon/menu | Reduced icon/menu |
| Hero | Split | Split | Stacked | Stacked, CTAs vertical |
| Category grid | 4 | 4 | 2 | 2 |
| Home product grid | 4 | 4 | 2 | 1 |
| Shop product grid | 3 | 2 | 2 | 1 |
| Shop filters | Sidebar | Sidebar | Drawer trigger | Drawer trigger |
| Product detail | 2 columns | 2 columns | Stacked | Stacked |
| Related products | 4 | 4 | 2 | 2 |
| Cart/checkout | Split | Split | Stacked | Stacked |
| Account | Split | Split | Stacked | Stacked |
| About stats/team | 4 | 4 | 2 | 2 |
| Contact cards | 3 | 3 | 1 | 1 |
| Footer | 4 grouped columns | 4 | 2×2 | stacked groups |

## Interaction-state evidence

- Search expands to a full container-width field under the header and pushes main
  content down; the source does not produce results after a typed query.
- Mobile menu opens below the header and swaps the menu icon for close.
- Shop Filters opens, but the source drawer behavior overflows at 390px.
- Product gallery thumbnails, quantity, finish, Buy Now, Add to Cart, wishlist and
  tab controls are visible; Specifications and FAQ were directly captured.
- Add to Cart updates the header count and creates the populated cart state.
- Cart proceeds to Checkout; Shipping proceeds to Payment.
- Account navigation switches My Orders to the empty Wishlist panel.
- Hover/focus/loading/error states are not visually specified in the source and must
  be derived from its colors, radii and density with WCAG-compliant focus treatment.

## Reference defects and intentional corrections

1. English/LTR/USD/US checkout content is replaced by Arabic RTL and Egyptian data.
2. Broken remote product/category images are replaced by consistent local assets.
3. Figma Make attribution chrome is excluded.
4. Unlabelled icon buttons receive accessible names.
5. Inaccessible Products submenu becomes a functional accessible menu.
6. The clipped 390px newsletter layout is corrected.
7. The overflowing 390px shop filter, populated cart and product tab states are
   corrected without changing the larger-screen composition.
8. Touch targets and visible focus are strengthened where the reference is deficient.

These corrections are required by localisation, accessibility or obvious usability
defects; they do not authorize a different design system.

## Evidence inventory

The repository contains 53 PNG captures and 53 matching measurement/state JSON
files under `reference-evidence/`. The core ten-state matrix covers Home, Shop,
About, Contact, Search open, Account, Empty Cart, Populated Cart, Product and
Checkout Shipping at all four required widths. Additional evidence covers mobile
menu, mobile filter-open, Specifications, FAQ, Checkout Payment, account Wishlist,
Products-menu probing and typed-search probing.

`newsletter-invalid-390` records an attempted source interaction but is not accepted
as proof of a validation state because the prototype did not expose a reliable result.
The absence is documented rather than inferred.

## Inspection gate decision

The reference was accessible and inspected sufficiently to specify its page grammar,
shared components, layout, responsive behavior and key interactive states. The gate
is therefore passed. Specification and planning may proceed; implementation remains
blocked until the specification, checklist, plan, contracts, tasks and analysis are
complete.

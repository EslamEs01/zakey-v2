# Feature Specification: ZAKEY Frontend Reference Build

**Feature Branch**: `003-zakey-frontend-reference-build`
**Created**: 2026-08-01
**Status**: Ready for implementation
**Input**: Build and fully verify the Arabic-first frontend-only ZAKEY v2 smart-lock
commerce reference experience before any backend feature begins.

## Context and Scope

ZAKEY needs a complete, cohesive frontend reference build that stakeholders can inspect across
desktop, tablet, and mobile before approving any backend work. The live design reference at
`https://remote-fried-86528699.figma.site/` is the binding visual authority. The feature covers
the presentation, prototype content, local interaction states, validation behavior, responsive
transformations, accessibility, and visual evidence for every customer-facing page.

The mandatory reference inspection gate passed on 2026-08-01. Codex personally inspected the
stateful reference in Chrome, reviewed its screen states and interactions, captured the core
ten-state matrix at all four required widths plus important interaction states, and approved
`reference-inventory.md` before finalizing this specification.

The experience represents a premium Egyptian smart-lock brand. It is Arabic-first, fully RTL,
Light Mode only, and localized for Egyptian customers. Catalogue, account, cart, wishlist, and
checkout content are explicit development fixtures. No state represents a real customer record,
order, provider transaction, inventory source, or production integration.

### In Scope

- A shared announcement bar, header, navigation, search, page shell, newsletter, and footer.
- Home, Shop, Category/Collection, Search Results, Product Details, Cart, Checkout, Wishlist,
  My Account, About, Contact, 404, and 5xx pages.
- A consistent visual system and reference-faithful responsive layouts at 1440px, 1024px, 768px,
  and 390px.
- Working frontend navigation, menus, search, filters, sorting, pagination, galleries, tabs,
  accordions, cart, wishlist, checkout steps, account states, forms, errors, and recovery states.
- Isolated prototype catalogue and commerce state used only to render and exercise the frontend.
- Functional, accessibility, responsive, console, HTML, and two-pass visual verification evidence.

### Out of Scope

- Database models, migrations, persistence, admin screens, business services, or APIs.
- Real authentication, customer accounts, enquiries, orders, checkout submission, payments,
  instalments, inventory, product management, shipping providers, email, or SMS.
- Provider claims, fake payment success, real order confirmation, production deployment, or
  production data access.
- Dark Mode, a separate application identity, or backend planning and implementation.

## Clarifications

### Session 2026-08-01

- **Visual authority**: Resolved from direct browser evidence. The live reference governs visual
  composition; the written brief governs Arabic RTL, Egyptian localisation, accessibility and
  the explicit frontend-only boundary.
- **Reference routing**: Resolved from interaction evidence. Secondary experiences are SPA screen
  states at the unchanged root URL; ZAKEY v2 exposes explicit, progressively enhanced Django URLs.
- **Reference gaps**: Resolved by the stated decision priority. Required pages and states absent
  from the reference extend its shared shell and component grammar without inventing a competing
  design system.
- **Prototype completion**: Resolved by scope. Contact/newsletter may show an intentional unsent
  validation result; checkout ends at review with an unavailable-submission explanation and never
  creates an order or payment success.
- **Persistence**: Resolved by scope. A dedicated replaceable browser-storage adapter may retain
  cart, wishlist and account-demo preferences; it is not backend or customer persistence.

No material ambiguity remains that requires a user question before planning.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover ZAKEY and its products (Priority: P1)

As an Egyptian customer, I want a premium Arabic landing experience that quickly communicates
what ZAKEY sells and why its smart-lock products are trustworthy, so I can start shopping with
confidence.

**Why this priority**: The shared shell and home page establish the approved visual direction for
every later page and provide the strongest above-the-fold review surface.

**Independent Test**: Open Home at each required viewport and use the shared navigation, hero,
categories, product collections, trust content, solutions, reviews, partners, newsletter, and
footer without encountering a dead control or an unrelated section.

**Acceptance Scenarios**:

1. **Given** the default Home state, **When** the customer scans above the fold, **Then** the brand,
   product category, principal call to action, and key reassurance are visible without a tall empty
   hero.
2. **Given** any required viewport, **When** the customer moves through the page, **Then** the 14
   mandated sections retain the reference order, a coherent density, and usable controls.
3. **Given** a keyboard or touch user, **When** the customer opens shared navigation or submits the
   newsletter form, **Then** focus, validation, dismissal, and recovery are clear and operable.

---

### User Story 2 - Browse, search, filter, sort, and page products (Priority: P1)

As a customer comparing locks, I want catalogue and search tools that work against realistic
prototype products, so I can narrow the selection and understand when no products match.

**Why this priority**: Product discovery is the primary commerce journey and must be convincing
before product, cart, or checkout states can be reviewed.

**Independent Test**: Use Shop and Search Results to apply and remove filters, sort results,
paginate, clear all criteria, open the mobile filter drawer, and deliberately reach both filtered
and search zero-result states.

**Acceptance Scenarios**:

1. **Given** the populated Shop, **When** the customer applies category, price, feature, or
   availability criteria, **Then** the product count, active chips, grid, and available pages update
   from the same prototype catalogue.
2. **Given** active filters, **When** the customer removes one chip or clears all, **Then** the
   remaining controls and product set reflect the resulting criteria.
3. **Given** a query with no matches or mutually exclusive filters, **When** results update,
   **Then** a distinct Arabic zero state offers a working recovery action.
4. **Given** a mobile viewport, **When** the filter drawer opens and closes, **Then** its focus,
   backdrop, controls, applied values, and dismissal remain accessible.

---

### User Story 3 - Evaluate a product in detail (Priority: P1)

As a customer considering a specific smart lock, I want imagery, pricing, features,
specifications, documents, reviews, FAQs, availability, and purchase controls in one coherent
page, so I can decide whether it fits my door and household.

**Why this priority**: The detail page carries the densest product information and interaction
states and is essential to approving the design system.

**Independent Test**: Use the product gallery, thumbnails, quantity selector, wishlist, share,
Add to Cart, Buy Now, information tabs, FAQ accordions, and related products for both available and
unavailable fixtures.

**Acceptance Scenarios**:

1. **Given** an available product, **When** the customer changes the gallery selection or quantity,
   **Then** the selected image, accessible name, quantity, price context, and action state remain
   synchronized.
2. **Given** product information sections, **When** the customer changes a tab or expands an FAQ,
   **Then** keyboard focus and expanded/selected semantics follow the visible content.
3. **Given** an unavailable product, **When** the customer reaches the purchase area, **Then** the
   page explains unavailability and disables purchase actions without hiding product information.
4. **Given** a Buy Now action, **When** the product is available, **Then** the item enters the local
   prototype cart and the customer reaches the checkout UI without any real submission.

---

### User Story 4 - Manage wishlist and cart states (Priority: P2)

As a customer, I want to save products and adjust a local cart, so I can compare choices and see a
credible order summary before checkout.

**Why this priority**: These states connect product discovery to checkout while remaining safely
within a frontend prototype boundary.

**Independent Test**: Add and remove wishlist and cart products, change quantities, enter valid and
invalid coupon prototypes, observe recalculated totals, and recover from empty states.

**Acceptance Scenarios**:

1. **Given** a product card or detail page, **When** the customer toggles wishlist or cart state,
   **Then** the relevant count, icon state, destination page, and persistent local prototype state
   agree.
2. **Given** a populated cart, **When** quantity changes or a line is removed, **Then** subtotal,
   VAT presentation, shipping threshold message, and total update immediately.
3. **Given** an empty wishlist or cart, **When** the page opens, **Then** it presents a purposeful
   Arabic empty state and a working route back to catalogue discovery.
4. **Given** the coupon control, **When** the customer applies an accepted or rejected prototype
   code, **Then** the UI clearly identifies the non-production result and offers recovery.

---

### User Story 5 - Review a localized checkout prototype (Priority: P2)

As an Egyptian customer, I want a clear, validated checkout interface with local address,
delivery, installation, and payment choices, so I can review the intended journey without placing
an order or making a payment.

**Why this priority**: Checkout must establish user confidence and localization while making the
frontend-only boundary unmistakable.

**Independent Test**: Move through checkout steps, trigger and correct Arabic field errors, choose
governorates and applicable service options, inspect payment methods, and reach the final review
state without any success or order confirmation.

**Acceptance Scenarios**:

1. **Given** incomplete customer or address fields, **When** the customer advances, **Then** focus
   moves to linked Arabic errors and the current step remains active.
2. **Given** any governorate, **When** delivery and installation options are evaluated, **Then**
   same-day delivery appears only for configured Greater Cairo areas and installation appears only
   for Greater Cairo and Alexandria.
3. **Given** a valid local form, **When** the customer reaches payment and review, **Then** all
   listed methods are described as prototype choices and no action claims integration or success.
4. **Given** the final review state, **When** the customer attempts to finish, **Then** the UI
   explains that order submission is intentionally unavailable and offers a safe return action.

---

### User Story 6 - Use account, company, support, and recovery pages (Priority: P3)

As a visitor or prototype account holder, I want coherent account, company, contact, and error
pages, so every public destination feels complete and I can recover from invalid or failed routes.

**Why this priority**: These pages complete the customer-facing system and prevent disconnected
or placeholder-looking destinations.

**Independent Test**: Switch signed-out and signed-in account prototypes, move between account
tabs, validate the Contact form, review About content, open 404 and 5xx pages, and use every
recovery action.

**Acceptance Scenarios**:

1. **Given** My Account, **When** the customer switches prototype identity and tabs, **Then** the
   visible navigation and content match signed-out or signed-in state without real authentication.
2. **Given** Contact, **When** invalid Egyptian contact details are submitted, **Then** labelled
   Arabic errors identify every problem and valid input reaches an intentional unsent prototype
   state.
3. **Given** a 404 or 5xx page, **When** the customer uses recovery controls, **Then** a valid public
   destination opens and the shared shell remains intact.

---

### User Story 7 - Use the storefront accessibly across devices (Priority: P1)

As a keyboard, screen-reader, touch, or reduced-motion user, I want the complete storefront to
remain understandable and operable at each target width, so my access method does not block any
frontend journey.

**Why this priority**: Accessibility and responsive behavior are release gates, not optional polish.

**Independent Test**: Exercise every page and material state at 1440px, 1024px, 768px, and 390px
with keyboard, automated accessibility checks, reduced motion, and horizontal-overflow detection.

**Acceptance Scenarios**:

1. **Given** any page at a target width, **When** the customer traverses landmarks and controls,
   **Then** reading order, headings, focus, labels, touch targets, and RTL layout remain logical.
2. **Given** a drawer, dialog, tab set, accordion, form error, or loading state, **When** it becomes
   active, **Then** assistive state, focus movement, dismissal, and recovery are exposed correctly.
3. **Given** reduced-motion preference, **When** an interaction changes state, **Then** essential
   feedback remains while non-essential animation is suppressed.

### Edge Cases

- Empty, whitespace-only, Arabic, Latin, mixed-script, and unmatched search queries.
- No active filters, one active filter, many active filters, and filters that remove every result.
- Pagination after filtering reduces the number of available pages below the current page.
- Product quantity at minimum, maximum prototype limit, and attempts beyond each boundary.
- Available and unavailable products reached from cards, search, related products, and direct URLs.
- Empty and populated cart or wishlist restored after navigation or reload.
- Accepted, rejected, repeated, and cleared coupon prototype states.
- Invalid, partial, and corrected Arabic names, email addresses, Egyptian mobile numbers, postal
  details, and address fields.
- All 27 governorates, including areas outside same-day and installation eligibility.
- Missing fixture image or document metadata produces a usable fallback rather than a broken token.
- Share capability unavailable in the browser provides a recoverable copy-link state.
- Loading and recoverable-error demonstrations do not trap focus or fabricate completion.
- 404 and 5xx recovery links remain valid at all viewports.

## Requirements *(mandatory)*

### Functional Requirements

#### Shared experience and visual authority

- **FR-001**: The experience MUST provide the 13 minimum customer-facing pages—Home, Shop,
  Category/Collection, Search Results, Product Details, Cart, Checkout, Wishlist, My Account,
  About, Contact, 404, and 5xx—and valid public navigation between them.
- **FR-002**: Every page MUST share one announcement bar, header, navigation system, search entry,
  wishlist/account/cart actions, page shell, newsletter treatment where appropriate, and footer.
- **FR-002A**: The Products navigation control MUST expose an accessible menu containing the
  product categories/collections from the centralized fixture source, support keyboard and pointer
  operation on desktop, appear as an expandable group in the mobile menu, and restore focus when
  dismissed.
- **FR-003**: The live approved reference MUST govern section order, hierarchy, density, grid,
  spacing, typography, imagery, header, hero, cards, controls, responsive transformations, and
  interaction language.
- **FR-004**: The visual identity MUST use the approved navy, gold, background, surface, and text
  colors, an 8px spacing rhythm, governed 12px radii, restrained shadows, and intentional whitespace.
- **FR-005**: The experience MUST be Light Mode only; dark navy MAY appear only in controlled brand
  bands and the design MUST NOT introduce black sections, glassmorphism, random gradients, glow,
  excessive animation, or disconnected component styles.
- **FR-006**: All icons MUST have a consistent intentional visual style, accessible labels where
  needed, and no placeholder glyphs or missing assets.
- **FR-007**: All public links and visible controls MUST have a working destination or intentional
  local state transition; empty anchors and dead buttons are prohibited.
- **FR-008**: Default, hover, focus, active, disabled, loading, empty, validation-error, and
  recoverable-error states MUST be visually distinguishable where relevant.
- **FR-009**: The storefront MUST not expose template tokens, filler text, developer-facing design
  labels, broken images, clipped Arabic, missing icons, or horizontal page overflow.

#### Home

- **FR-010**: Home MUST present the exact inspected order: Announcement Bar, Header, Premium Hero,
  five-benefit trust strip, Shop by Category, Best Sellers, Nexus-style controlled promotional
  band, Featured Products, Why Choose ZAKEY, Smart Home Solutions, Customer Reviews, Brand
  Partners, Newsletter, and Footer.
- **FR-011**: At the 1200px browser-review height used for reference capture, the Home first
  viewport MUST show a clear brand proposition, product imagery, principal action, and reassurance;
  the hero MUST remain compositionally dense and MUST NOT add unused vertical space merely to fill
  a viewport. Stacked tablet/mobile content MAY extend beyond one viewport as the reference does.
- **FR-012**: Category cards MUST identify distinct smart-lock groupings and lead to the matching
  catalogue state.
- **FR-013**: Best Sellers and Featured Products MUST use the same reusable product-card language
  as Shop and Search Results.
- **FR-014**: Why Choose ZAKEY MUST communicate concise service or product benefits without adding
  unrelated filler sections.
- **FR-015**: Smart Home Solutions MUST connect relevant products and domestic use cases while
  preserving the approved reference composition.
- **FR-016**: Customer Reviews MUST use Arabic prototype names and clearly remain development
  content rather than verified production testimony.
- **FR-017**: Brand Partners MUST present consistent partner marks with alternative text and safe
  image fallbacks.
- **FR-018**: Newsletter MUST validate an email address in Arabic, expose loading, success,
  validation-error, and recoverable-error prototype states, and state that no email is sent.

#### Shop and search

- **FR-019**: Shop MUST provide desktop sidebar filters and an accessible mobile filter drawer.
- **FR-020**: Catalogue criteria MUST include useful combinations of category, price, product
  feature, and availability based on the prototype catalogue.
- **FR-021**: Active criteria MUST be represented as individually removable chips with a working
  clear-all action.
- **FR-022**: Sorting MUST provide relevant default, price ascending, price descending, and name
  choices and MUST reorder only the currently matching products.
- **FR-023**: Pagination MUST update after filtering, sorting, or searching, keep the current page
  valid, and provide accessible previous, next, and page controls.
- **FR-024**: Product-grid columns MUST transform deliberately for desktop, tablet, and mobile
  without narrowing cards below usable content width.
- **FR-025**: Shop MUST distinguish populated, no-filtered-results, loading, and recoverable-error
  states and provide a working recovery action for each non-default state.
- **FR-026**: Search Results MUST display the query and count, use the same filtering, sorting,
  pagination, and card behavior as Shop, and distinguish no-search-results from no-filtered-results.
- **FR-026A**: Category/Collection MUST reuse the Shop result system with the selected collection
  pre-applied, an Arabic collection heading, active filter chip, valid canonical route, and the
  same populated, empty, loading, error, sorting and pagination behavior.

#### Product details

- **FR-027**: Product Details MUST provide a large gallery, selectable thumbnails, meaningful
  alternative text, and a visible selected-image state.
- **FR-028**: Product Details MUST show product name, Egyptian pound price, 14% VAT presentation,
  prototype instalment context, availability, concise features, and delivery threshold messaging.
- **FR-029**: Product information MUST provide accessible sections for features, specifications,
  downloads, reviews, FAQs, and related products.
- **FR-030**: Product tabs and accordions MUST expose selected or expanded state and work by
  keyboard, pointer, and touch.
- **FR-031**: Quantity controls MUST enforce a minimum of 1 and a prototype maximum of 9 and MUST
  expose disabled boundaries.
- **FR-032**: Add to Cart, Buy Now, wishlist, and share MUST update or report intentional local
  prototype state; unavailable products MUST disable purchase actions.
- **FR-033**: Downloads MUST be presented as labelled prototype document actions and MUST NOT imply
  a verified production manual or certification.
- **FR-034**: Related products MUST link to valid product details and MUST not include the current
  product.

#### Wishlist and cart

- **FR-035**: Wishlist state MUST be shared across product cards and Product Details and MUST
  support populated and empty presentations.
- **FR-036**: Cart state MUST be shared across product cards, Product Details, Cart, and Checkout
  and MUST support populated and empty presentations.
- **FR-037**: Cart MUST support quantity changes from 1 through 9, line removal, and return-to-shop
  recovery.
- **FR-038**: Cart totals MUST present subtotal, 14% VAT context, shipping threshold status, any
  prototype coupon adjustment, and total using Egyptian pound formatting.
- **FR-039**: Cart MUST provide accepted, rejected, loading, cleared, and recoverable coupon UI
  states without claiming a real promotion service.
- **FR-040**: Cart and wishlist counts in the shared header MUST reflect the current local prototype
  state after every relevant action and reload.

#### Checkout

- **FR-041**: Checkout MUST provide exactly three ordered steps with visible current, complete and
  unavailable states: (1) Shipping, containing customer, address, delivery and eligible installation
  fields; (2) Payment, containing non-integrated prototype method selection; and (3) Review,
  containing the editable summary and intentionally unavailable final submission.
- **FR-042**: Checkout MUST validate required Arabic name, email, Egyptian mobile, governorate,
  city or area, street address, building, and acknowledgement fields before advancing.
- **FR-043**: Every invalid checkout field MUST have an Arabic message linked to the field, invalid
  state, and predictable focus movement.
- **FR-044**: Governorate choices MUST contain the canonical 27 Egyptian governorates exactly once.
- **FR-045**: Same-day messaging MUST be driven by the Service Eligibility fixture and appear only
  for the configured prototype areas—New Cairo, Nasr City, Heliopolis, Maadi, Downtown Cairo,
  Dokki and Mohandessin. Installation MUST be offered only when the selected governorate is Cairo,
  Giza or Alexandria. All other selections MUST show the standard-delivery/no-installation state.
- **FR-046**: Payment choices MAY include local wallets, InstaPay, CashU where applicable, cash on
  delivery, and Egyptian bank-card instalments, but every option MUST be labelled as a frontend
  prototype with no provider integration.
- **FR-047**: Checkout review MUST summarize customer, delivery, installation, payment, and cart
  choices and allow the customer to return to the relevant editable step.
- **FR-048**: The final checkout action MUST explain that submission is unavailable, MUST NOT create
  a fake order or payment success, and MUST provide safe navigation back to Cart or Shop.

#### Account, company, support, and errors

- **FR-049**: My Account MUST provide signed-out and signed-in prototype states and visibly label
  them as non-authenticated development demonstrations.
- **FR-050**: Signed-in account navigation MUST preserve the inspected hierarchy—My Orders,
  Wishlist, Addresses, Payment Methods, Account Settings and Sign Out—with accessible selection,
  coherent prototype content and explicit non-integrated/unavailable treatment where a backend
  would otherwise be required. Account Settings MAY contain locally validated profile fields.
- **FR-051**: About MUST communicate ZAKEY's purpose, Egyptian-market context, product approach,
  and Arabic prototype team content without unsupported operational claims.
- **FR-052**: Contact MUST provide labelled name, Egyptian mobile, email, subject, and message
  fields with Arabic validation, loading, intentional-unsent, and recoverable-error states.
- **FR-053**: Contact details, footer links, and social actions MUST use valid destinations or
  explicitly labelled prototype actions.
- **FR-054**: The 404 page MUST explain the missing destination in Arabic and provide working Home,
  Shop, and Search recovery actions.
- **FR-055**: The 5xx page MUST explain a temporary recoverable problem in Arabic and provide
  working retry, Home, and Contact recovery actions without claiming a real server incident.

#### Localization, accessibility, and responsive behavior

- **FR-056**: All customer-facing copy and layout MUST be Arabic-first and RTL; Latin brand or
  technical terms MAY use a suitable Latin typeface without reversing surrounding reading order.
- **FR-057**: Prices MUST use `ج.م`, remain within the prototype range of 2,190–7,490 EGP, and use
  a consistent number and tax presentation.
- **FR-058**: Free-shipping messaging MUST use the 1,500 EGP threshold and MUST update with the
  prototype cart subtotal.
- **FR-059**: Forms requiring a phone number MUST accept domestic Egyptian mobile numbers beginning
  `010`, `011`, `012` or `015` with 11 digits, and the equivalent `+20` form after removing spaces
  and separators and normalizing the country code. Other lengths or prefixes MUST be rejected with
  Arabic guidance.
- **FR-060**: All pages MUST provide semantic landmarks, logical heading order, keyboard access,
  visible focus, labelled controls, alternative text, sufficient contrast, no keyboard traps,
  logical RTL order, and 44×44 CSS-pixel minimum pointer targets for standalone controls. Inline
  text links MAY follow their text bounds only when line height and surrounding spacing prevent
  adjacent-target collisions.
- **FR-061**: Drawers and dialogs MUST identify their name and state, move focus on open, contain
  focus while active, support Escape dismissal where safe, and restore focus on close.
- **FR-062**: Tabs and accordions MUST expose accessible roles, names, selected/expanded states,
  keyboard behavior, and visible focus.
- **FR-063**: Motion MUST be subtle and purposeful, and non-essential transitions MUST be removed
  when the customer requests reduced motion.
- **FR-064**: Every required page and material state MUST remain usable without horizontal page
  overflow at 1440px, 1024px, 768px, and 390px.

#### Prototype data and completion evidence

- **FR-065**: Site settings, categories, collections, products, prices, product images, features,
  specifications, reviews, partners, FAQs, shipping options, payment labels, account states, cart
  states, wishlist states, and related fixture content MUST originate from one isolated
  development source.
- **FR-066**: The fixture boundary MUST enable later replacement with persistent catalogue and
  customer data without rewriting page structure or interaction contracts.
- **FR-067**: Fixture content MUST be realistic and internally consistent but MUST NOT be described
  as verified production content.
- **FR-068**: Every required page default state and every material state named by the frontend-state
  contract and QA interaction matrix MUST be captured at 1440px, 1024px, 768px and 390px, with an
  inventory linking each screenshot to route, width, state, reference evidence and review pass.
- **FR-069**: Visual pass one MUST evaluate and correct reference fidelity, composition, section
  order, grid, density, responsive transformation, header, hero, cards, and footer.
- **FR-070**: Visual pass two MUST evaluate and correct typography, RTL alignment, Arabic wrapping,
  spacing, icon alignment, imagery, contrast, interaction polish, empty and form states, and final
  premium quality.
- **FR-071**: Completion evidence MUST include functional, accessibility, console, link, HTML,
  build, responsive, screenshot, and guard results with no unresolved material failure.
- **FR-072**: Without JavaScript, every public route MUST still render its primary content,
  landmarks, product/detail data and valid links; GET-based search/category navigation and native
  form validation/fallback messaging MUST remain understandable. JavaScript MAY enhance filtering,
  drawers, tabs and local prototype state, but MUST NOT be required to discover core content or
  recover to Home/Shop.

### Key Entities

- **Category Fixture**: A stable identifier, Arabic name, description, visual asset, and catalogue
  route criteria for a product grouping.
- **Product Fixture**: A stable identifier and slug, Arabic name, category, price, availability,
  imagery, features, specifications, downloads, reviews, FAQs, and related-product identifiers.
- **Partner Fixture**: An Arabic or brand name, mark, alternative text, and safe destination state.
- **Review Fixture**: Arabic customer name, rating, concise prototype review, and product or Home
  placement.
- **FAQ Fixture**: A stable identifier, Arabic question and answer, and applicable page or product.
- **Cart State**: Product identifiers, quantities, coupon state, subtotal, VAT context, shipping
  threshold state, and total, stored only for the local prototype.
- **Wishlist State**: A unique set of product identifiers stored only for the local prototype.
- **Checkout State**: Current step, validated customer and address fields, delivery and installation
  eligibility, selected prototype payment option, and review state; never an order.
- **Account State**: Signed-out or signed-in prototype identity and current tab with no real user.
- **UI State**: Drawer, dialog, loading, validation, recoverable error, empty, and unavailable states
  required to demonstrate interactions accessibly.
- **Service Eligibility Fixture**: Stable normalized governorate and area keys governing same-day
  messaging and installation visibility, separate from display labels and never described as a
  real provider service area.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 13 minimum required pages and all required Home sections are reachable through
  valid storefront routes, with zero empty anchors, dead visible controls, broken public links,
  template tokens, or Lorem Ipsum occurrences. Error routes are directly testable and their
  recovery controls return to valid public navigation; they need not appear in the primary menu.
- **SC-002**: At 1440px, 1024px, 768px, and 390px, every required page has zero horizontal page
  overflow and no clipped Arabic text, missing essential content, or unusable control.
- **SC-003**: A customer can search, apply and clear filters, sort, paginate, reach both catalogue
  zero states, and recover using only visible controls in under 3 minutes.
- **SC-004**: A customer can operate the gallery, quantity, wishlist, Add to Cart, Buy Now, tabs,
  accordions, share fallback, and related-product navigation without a dead state.
- **SC-005**: A customer can populate and empty wishlist and cart, update quantities, exercise both
  coupon outcomes, and observe consistent header counts and totals across navigation and reload.
- **SC-006**: A customer can complete all checkout validation steps and reach the final prototype
  review in under 4 minutes, while no interaction creates or claims an order or payment.
- **SC-007**: Every invalid newsletter, contact, account-settings, and checkout form state identifies the
  problem in Arabic, programmatically links the message to the field, and moves focus predictably.
- **SC-008**: All keyboard journeys complete without a trap; drawers, dialogs, tabs, accordions,
  menus, and error recovery expose correct focus and state semantics.
- **SC-009**: Automated accessibility review reports zero critical and zero serious violations on
  every page and material state selected for the final matrix.
- **SC-010**: All pages pass the selected HTML conformance check and produce zero uncaught browser
  exceptions or unexpected console errors during automated journeys.
- **SC-011**: The final screenshot inventory contains all 52 required default page/viewport
  combinations and every contracted material interaction, empty, validation, loading and
  recoverable-error state at all four widths; the responsive verification matrix has no blank cell.
- **SC-012**: Two documented visual-review passes have zero unresolved material findings after the
  recorded fixes and screenshot recapture. A material finding is any wrong section/order,
  breakpoint/grid, missing content/control, horizontal overflow, clipping, unreadable contrast,
  inaccessible state, inconsistent shared component, or repeated spacing/proportion deviation
  greater than one 8px spacing unit from the approved reference interpretation.
- **SC-013**: Product prices all fall within 2,190–7,490 EGP, use `ج.م`, present 14% VAT context,
  and use the 1,500 EGP free-shipping threshold consistently.
- **SC-014**: Checkout exposes each canonical Egyptian governorate exactly once, accepts valid
  Egyptian mobile formats, and restricts same-day and installation messaging to the specified areas.
- **SC-015**: One fixture source accounts for 100% of site settings, category, collection, product,
  price, image, feature, specification, review, partner, FAQ, service eligibility, shipping option,
  payment label, account, cart, wishlist and checkout prototype content used by pages and
  interaction code.
- **SC-016**: Final production-code, test-code, and documentation guard passes have no unresolved
  material finding.
- **SC-017**: With JavaScript disabled, all 13 public pages render their primary content and valid
  recovery/navigation links, direct product/category routes remain usable, and a search GET request
  produces a server-rendered populated or no-results page without a browser exception.

## Assumptions

- The live reference is available during visual research; if a specific reference interaction is
  not exposed, the closest consistent pattern elsewhere in that same reference governs it.
- Prototype state may be retained in the customer's browser solely to demonstrate navigation and
  reload behavior; it is not customer persistence and can be reset safely.
- Product photography, partner marks, names, reviews, manuals, and technical values created for
  this feature are demonstrative assets and not verified commercial claims.
- The account's signed-in state is a clearly labelled visual prototype and never authenticates a
  visitor.
- Contact and newsletter success means only that frontend validation reached an intentional unsent
  demonstration state.
- Payment, delivery, installation, coupon, and instalment choices are frontend representations
  with no provider connection.
- The Category/Collection route is an explicit user-required extension of the reference Shop
  grammar; it is not evidence that the reference exposed a separate category screen.
- Backend architecture, data ownership, real authentication, commerce rules, and production
  operations will be specified only after explicit frontend approval.

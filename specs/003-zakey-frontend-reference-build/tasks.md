# Tasks: ZAKEY Frontend Reference Build

**Input**: Specification 003 design package
**Prerequisites**: approved reference inventory, spec, plan, research, data model and contracts
**Boundary**: frontend-only; no model, migration, admin, API, auth, order/payment integration,
deployment or Git publication task is authorized

## Phase 1: Setup

- [x] T001 Create the presentation-only Django file structure in `config/`, `storefront/`,
  `templates/`, `static/` and `tests/` exactly as defined in `plan.md`.
- [x] T002 Create `pyproject.toml` and lock Django 5.2 LTS with no database/business dependencies.
- [x] T003 Create `package.json` and lock Tailwind, local fonts/icons, Playwright, axe and
  html-validate at the researched direct versions.
- [x] T004 Configure presentation-only Django settings and direct URL composition in
  `config/settings.py` and `config/urls.py` without database, auth, session, admin or model setup.
- [x] T005 Configure Tailwind input/output and local asset/font/icon copying in
  `static/src/css/app.css` and package scripts.
- [x] T006 Configure Playwright local-Chrome, no-JavaScript projects at all four widths and the
  deterministic Django `webServer` lifecycle in `playwright.config.js`.
- [x] T007 Configure rendered matrix HTML validation, native JS syntax checks and QA-matrix
  completeness enforcement in `.htmlvalidate.json` and `scripts/`.
- [x] T008 Install dependencies, produce lockfiles and record successful tool versions in
  `specs/003-zakey-frontend-reference-build/qa/build-results.md`.

## Phase 2: Foundational design and data system

- [x] T009 Implement the complete demonstration fixture root in
  `storefront/fixtures/frontend-fixtures.json`, including all 27 governorates and every contracted
  settings/catalogue/content/service/payment/account/cart/wishlist field.
- [x] T010 Implement the exact typed fixture-adapter shapes, normalization, stable sorting,
  validation and server/client parity cases in `storefront/fixture_provider.py` and tests with no
  database/network access.
- [x] T011 [P] Create Django fixture and route tests in `tests/test_fixture_provider.py` and
  `tests/test_routes.py` for the presentation shell and frontend boundary.
- [x] T012 Implement direct presentation views/GET catalogue normalization in `storefront/views.py`
  and routes in `storefront/urls.py`.
- [x] T013 Establish Cairo/Poppins typography, ZAKEY color, spacing, radius, shadow, container and
  responsive tokens in `static/src/css/app.css`.
- [x] T014 Implement the semantic shared document shell in `templates/base.html` with skip link,
  landmarks, safe fixture JSON, live region and no-script notice.
- [x] T015 Implement shared announcement/header/search/navigation/product-menu templates in
  `templates/partials/header.html` and related `templates/components/` files.
- [x] T016 Implement the shared reference-faithful footer/newsletter templates in
  `templates/partials/footer.html` and `templates/components/newsletter.html`.
- [x] T017 Implement reusable button, icon, breadcrumb, product-card, section-heading, status,
  form-control, empty/error and order-summary components under `templates/components/`.
- [x] T018 Implement shared responsive/reference-specific component styles in
  `static/src/css/reference.css`, including focus-visible and reduced-motion behavior.
- [x] T019 Implement the versioned store and sole localStorage boundary in
  `static/src/js/state/store.js` and `static/src/js/state/storage-adapter.js`.
- [x] T020 Implement shared menu, drawer/dialog, search, status, reset and form utilities under
  `static/src/js/components/` and `static/src/js/utilities/`.

## Phase 3: User Story 1 — Discover ZAKEY (P1)

**Independent test**: Home reproduces the 14-section reference composition and shared navigation,
newsletter and footer work at all four widths.

- [x] T021 [US1] Add Home render/shared-shell assertions to `tests/test_routes.py`.
- [x] T022 [US1] Add Home navigation/newsletter/mobile-menu states to the executable matrix and
  `tests/e2e/site-integrity.spec.js`.
- [x] T023 [US1] Implement the 14-section Arabic Home composition in `templates/pages/home.html`
  using only shared components and fixture contexts.
- [x] T024 [US1] Implement Home newsletter validation/loading/unsent/error and mobile menu behavior
  in `static/src/js/pages/home.js` and shared modules.
- [x] T025 [US1] Verify Home independently at 1440/1024/768/390 and record the first structural
  comparison in `specs/003-zakey-frontend-reference-build/qa/visual-comparison-findings.md`.

## Phase 4: User Story 2 — Browse, search and filter products (P1)

**Independent test**: Shop, collection and search support GET fallback plus enhanced filters,
sorting, pagination, chips, drawers and populated/empty/loading/error states.

- [x] T026 [US2] Add GET filter/search/collection/pagination tests to
  `tests/test_fixture_provider.py` and `tests/test_routes.py`.
- [x] T027 [US2] Add discovery interaction and mobile drawer states to
  `tests/e2e/site-integrity.spec.js`.
- [x] T028 [US2] Implement reference-faithful catalogue intro, toolbar, filters, chips, grid,
  pagination and state components in `templates/pages/shop.html` and `templates/components/`.
- [x] T029 [US2] Implement `/collections/<slug>/` and `/search/` compositions using the same
  catalogue component system.
- [x] T030 [US2] Implement normalized filtering/sorting/pagination/query state in
  `static/src/js/pages/catalogue.js` without duplicating fixture product records.
- [x] T031 [US2] Implement the accessible RTL mobile filter drawer with focus containment,
  Escape/backdrop dismissal and trigger restoration.
- [x] T032 [US2] Implement distinct no-search/no-filter/loading/recoverable-error states and working
  recovery actions.
- [x] T033 [US2] Verify direct/no-JavaScript discovery URLs and the four-width discovery matrix.

## Phase 5: User Story 3 — Evaluate a product (P1)

**Independent test**: Product details support gallery, quantity, availability, tabs, FAQ,
prototype downloads/reviews, related items, cart/wishlist/share and unavailable state.

- [x] T034 [US3] Add Product render/invalid-slug/unavailable route coverage to
  `tests/test_routes.py` and the QA matrix.
- [x] T035 [US3] Add gallery/tab/accordion/quantity/cart/wishlist/share states to
  `tests/e2e/site-integrity.spec.js`.
- [x] T036 [US3] Implement the product gallery and summary composition in
  `templates/pages/product_detail.html` and reusable gallery/purchase components.
- [x] T037 [US3] Implement feature, specification, download, review and FAQ tab panels with semantic
  server-rendered content.
- [x] T038 [US3] Implement gallery, finish, quantity, tab and accordion modules in
  `static/src/js/pages/product.js` with accessible keyboard behavior.
- [x] T039 [US3] Connect Add to Cart, Buy Now, wishlist and share fallback to normalized prototype
  state without any real submission.
- [x] T040 [US3] Implement disabled/unavailable product treatment and related-product navigation.
- [x] T041 [US3] Verify Product default/alternate/tab/FAQ/unavailable/saved states at all widths.

## Phase 6: User Story 4 — Manage wishlist and cart (P2)

**Independent test**: Wishlist/cart persist only through the adapter, synchronize counts, recalculate
totals and expose every required empty, coupon, loading and recovery state.

- [x] T042 [US4] Add cart/wishlist/totals/storage-state browser coverage to the QA matrix and
  `tests/e2e/site-integrity.spec.js`.
- [x] T043 [US4] Implement standalone Wishlist populated/empty compositions in
  `templates/pages/wishlist.html`.
- [x] T044 [US4] Implement populated/empty Cart, line-item, coupon and summary compositions in
  `templates/pages/cart.html`.
- [x] T045 [US4] Implement synchronized wishlist/cart controllers in
  `static/src/js/pages/wishlist.js` and `static/src/js/pages/cart.js`.
- [x] T046 [US4] Implement quantity/removal/subtotal/VAT/shipping-threshold/total calculations from
  fixture settings.
- [x] T047 [US4] Implement accepted/rejected/loading/cleared/recoverable coupon prototype states.
- [x] T048 [US4] Verify state restoration, corrupted-storage recovery and prototype reset behavior.
- [x] T049 [US4] Verify all Cart/Wishlist material states at all four widths with no source-style
  mobile clipping.

## Phase 7: User Story 5 — Localized checkout prototype (P2)

**Independent test**: Shipping, Payment and Review validate Egyptian inputs and eligibility, retain
editable prototype choices and end without creating/claiming an order or payment.

- [x] T050 [US5] Add checkout route/fixture/governorate tests to `tests/test_fixture_provider.py`
  and `tests/test_routes.py`.
- [x] T051 [US5] Add validation/eligibility/payment/review/no-submission states to the QA matrix
  and `tests/e2e/site-integrity.spec.js`.
- [x] T052 [US5] Implement the three-step Checkout and sticky/stacked order summary in
  `templates/pages/checkout.html` and checkout components.
- [x] T053 [US5] Implement Arabic linked validation/error summary and Egyptian phone normalization
  in `static/src/js/pages/checkout.js` and validation utilities.
- [x] T054 [US5] Implement all-governorate/area updates, exact same-day area eligibility and
  Cairo/Giza/Alexandria installation eligibility.
- [x] T055 [US5] Implement non-integrated Egyptian payment-choice UI, disabled/loading states and
  editable Review summary.
- [x] T056 [US5] Implement the final unavailable-submission explanation and safe Cart/Shop recovery,
  with no success/order identifier.
- [x] T057 [US5] Verify all checkout material states at all four widths and capture Arabic errors.

## Phase 8: User Story 6 — Account, company, contact and errors (P3)

**Independent test**: Signed-out/signed-in account, six reference-aligned tabs, About, Contact,
404 and 5xx are coherent, validated and recoverable.

- [x] T058 [US6] Add account/contact/about/error render coverage to `tests/test_routes.py`.
- [x] T059 [US6] Add account tabs/forms/contact validation/error recovery states to the QA matrix
  and `tests/e2e/site-integrity.spec.js`.
- [x] T060 [US6] Implement signed-out and reference-aligned signed-in Account compositions in
  `templates/pages/account.html`.
- [x] T061 [US6] Implement account tab selection, settings validation and explicit unavailable
  backend-dependent controls in `static/src/js/pages/account.js`.
- [x] T062 [P] [US6] Implement the reference-faithful localized About page in
  `templates/pages/about.html` using established tokens/components.
- [x] T063 [P] [US6] Implement the localized Contact composition in
  `templates/pages/contact.html` using established form/card components.
- [x] T064 [US6] Implement Contact validation/loading/intentional-unsent/recoverable-error behavior
  in `static/src/js/pages/contact.js`.
- [x] T065 [P] [US6] Implement shared-shell 404 and 5xx pages and direct QA routes in
  `templates/pages/404.html` and `templates/pages/500.html`.
- [x] T066 [US6] Verify all Account/Company/Support/Error material states at all four widths.

## Phase 9: User Story 7 — Accessible responsive storefront (P1 cross-cutting)

- [x] T067 [US7] Add axe coverage for every route/state cell to
  `tests/e2e/site-integrity.spec.js` and fail on any critical or serious finding.
- [x] T068 [US7] Add keyboard/focus/reduced-motion and no-JavaScript responsive assertions in
  `tests/e2e/site-integrity.spec.js` and `tests/e2e/no-js.spec.js`.
- [x] T069 [US7] Read `contracts/qa-matrix.json` and add console/pageerror/asset/link/image/overflow,
  functional, axe and evidence-completeness checks for every route/state/viewport cell in
  `tests/e2e/site-integrity.spec.js`.
- [x] T070 [US7] Add rendered snapshot generation and html-validate coverage for all routes.
- [x] T071 [US7] Remediate semantics, heading order, labels, contrast, focus, status announcements,
  drawers, tabs, accordions, touch targets and reduced motion across the integrated implementation.
- [x] T072 [US7] Verify the 10 server-rendered no-JavaScript shell routes at all four widths and
  record 40/40 results in `specs/003-zakey-frontend-reference-build/qa/progressive-enhancement.md`;
  verify GET catalogue/search behavior separately in Django route tests.
- [x] T073 [US7] Complete keyboard and screen-reader-oriented manual checks in
  `specs/003-zakey-frontend-reference-build/qa/accessibility-results.md`.

## Phase 10: Integrated QA, visual refinement and stop gate

- [x] T074 Run the production frontend build and Django tests; fix every failure.
- [x] T075 Run all Playwright functional journeys; fix every failure without weakening tests.
- [x] T076 Run axe across the route/state matrix; fix until critical=0 and serious=0.
- [x] T077 Run rendered HTML, console, failed-asset, image, link and overflow validation; fix every
  unexpected result.
- [x] T078 Capture all 224 required route/state/width cells from `contracts/qa-matrix.json` under
  `specs/003-zakey-frontend-reference-build/qa/implementation-screenshots/`.
- [x] T079 Create `qa/screenshot-inventory.md`, `qa/browser-route-inventory.md`,
  `qa/interaction-matrix.md` and `qa/responsive-verification-matrix.md` with no blank required cell.
- [x] T080 Complete visual pass one against paired reference captures for composition, order,
  container/grid, density, header, hero, cards, footer and breakpoints.
- [x] T081 Fix every pass-one material finding and recapture affected screenshots.
- [x] T082 Complete visual pass two for Cairo typography, Arabic wrapping, RTL, spacing, imagery,
  icons, borders/shadows, controls, form/empty states, contrast and motion.
- [x] T083 Fix every pass-two material finding and recapture affected screenshots.
- [x] T084 Complete `qa/visual-comparison-findings.md` and `qa/final-verification-report.md`,
  documenting every intentional reference difference and exact evidence.
- [x] T085 Run `clean-code-guard` on the complete production-code diff; fix material findings and
  rerun affected checks.
- [x] T086 Run `test-guard` on the complete test/QA-code diff; fix material findings and rerun tests.
- [x] T087 Run `docs-guard` on the complete Specification 003/documentation diff; fix material
  findings and revalidate traceability.
- [x] T088 Personally review every integrated route/state in Chrome and confirm no backend or
  production artifact exists.
- [x] T089 Validate the documented one-command preview and state-reset instructions.
- [x] T090 Run final `git diff --check`, `git diff --stat`, `git status --short --branch` and record
  exact results without committing or publishing.
- [x] T091 Stop before backend planning and return only the user visual-review decision supported
  by the complete final report.

## Dependencies and execution order

- Setup T001–T008 precedes foundation T009–T020.
- T009–T020 block every story; T017 defines the component standard before delegated templates.
- US1/US2/US3 are P1 visual/product foundations; US4 and US5 consume their state/components.
- US6 may proceed after T017 when file ownership is non-overlapping.
- US7 and integrated QA consume all page stories; guard tasks run only on the complete diff.
- `[P]` tasks touch separate files but must never overlap simultaneous agent writes.

## Implementation strategy

Deliver a single integrated frontend, validating each story independently at its checkpoint. Do not
stop for a routine approval between phases, do not commit, and do not begin backend work. A task is
checked only after its file/output exists and its stated verification passes.

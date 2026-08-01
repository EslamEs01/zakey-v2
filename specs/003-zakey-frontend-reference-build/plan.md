# Implementation Plan: ZAKEY Frontend Reference Build

**Branch**: `003-zakey-frontend-reference-build` | **Date**: 2026-08-01 | **Spec**: [spec.md](spec.md)
**Input**: Frontend-only feature specification and approved [reference inventory](reference-inventory.md)

## Summary

Build a complete Arabic-first, RTL, frontend-only ZAKEY storefront that closely reproduces the
inspected Figma reference through semantic Django Templates, locally compiled Tailwind CSS,
focused custom CSS and native modular JavaScript. A presentation-only Django shell renders 13
public routes from one JSON fixture source. A dedicated browser-storage adapter supplies reversible
cart, wishlist and account demonstration state. No model, migration, admin, API, authentication,
order, provider integration or production action is introduced.

## Technical Context

**Language/Version**: Python 3.12.3; HTML5; CSS; JavaScript ES2022
**Primary Dependencies**: Django 5.2 LTS; Tailwind CSS 4.3.3 and `@tailwindcss/cli` 4.3.3;
`@fontsource/cairo` 5.3.0; `@fontsource/poppins` 5.3.0; `lucide-static` 1.28.0
**Storage**: One read-only JSON fixture; optional `localStorage` only through `storage-adapter.js`
**Testing**: Django `SimpleTestCase`; Playwright 1.62.1 using local Chrome 150;
`@axe-core/playwright` 4.12.1; `html-validate` 11.6.0; `node --check` for native modules
**Target Platform**: Current evergreen browsers; local Linux preview; required viewport widths
1440, 1024, 768 and 390 at a 1200px capture height
**Project Type**: Server-rendered frontend prototype with progressive enhancement
**Performance Goals**: no failed local assets; local imagery only; no layout shift from missing
image dimensions
**Constraints**: frontend-only; no database requirement; no runtime CDN; Light Mode; full RTL;
zero critical/serious axe findings; zero horizontal overflow; no uncaught console error
**Scale/Scope**: 13 routes, shared shell, approximately 8–10 product fixtures, four viewports,
all contracted material states and two browser visual-review passes

## Constitution Check

*GATE: Passed before research and rechecked after design.*

| Principle | Pre-research evidence | Post-design evidence | Result |
|---|---|---|---|
| Frontend approval/scope isolation | Out-of-scope list excludes all backend business work | No model/admin/migration/API directories or tasks; JSON fixture and browser adapter only | Pass |
| Reference fidelity/inspection gate | Codex approved 53 screenshots and 53 geometry records before this plan | Shared frame, grids, states and intentional corrections map to `reference-inventory.md` | Pass |
| Arabic-first accessible responsive | Spec FR-056–FR-064 and SC-002/008/009 | Cairo, RTL templates, semantic component contracts and four-width QA matrix | Pass |
| Replaceable prototype data/progressive enhancement | FR-065–FR-067/072 and SC-015/017 | One JSON source, Python fixture adapter, JS storage adapter and GET fallbacks | Pass |
| Evidence-based quality gates | FR-068–FR-071 and SC-009–SC-016 | Django/Playwright/axe/HTML/build/visual/guard tasks and evidence documents | Pass |

No constitution violation requires a complexity exception.

## Architecture

### Rendering and route boundary

`config/` contains only settings, URL routing and WSGI/ASGI preview entry points. `storefront/`
contains presentation-only views and the fixture adapter. Each URL resolves directly without
client routing. Unknown URLs use the shared 404 template; a deliberate QA route renders the shared
5xx template with a 500 status without throwing a production-like exception.

### Fixture boundary

`storefront/fixtures/frontend-fixtures.json` is the only authored source of settings, catalogue,
media metadata, content, service eligibility and prototype commerce/account defaults.
`fixture_provider.py` validates required keys, calculates presentation-only derived values and
injects page-specific subsets. The complete client-safe subset is serialized once in a JSON script
element for native modules. Templates and modules never redefine product or price objects.

### State boundary

Native modules dispatch `zakey:*` custom events through a small store. The storage adapter is the
only module permitted to touch `localStorage`; it versions/sanitizes cart, wishlist and account-demo
state and can reset to fixture defaults. URL query parameters represent shareable search, filters,
sort, page and explicit QA states. Checkout form values remain session-memory prototype state and
are never submitted to Django.

### Template/component boundary

`base.html` owns the document, fonts, skip link, announcement, header, live-region, main and footer.
Reusable component partials receive fixture/context data and render semantic HTML before scripts
load. Page templates compose those components. The same product card, form-control, empty-state,
status-chip, drawer, tabs/accordion and order-summary patterns are used across routes.

### Styling boundary

Tailwind v4 scans templates and JavaScript at build time. `app.css` defines local font imports,
brand/theme tokens, base RTL typography and reusable component layers. `reference.css` is limited
to shapes or responsive behavior that would be less maintainable as long utility strings. No
runtime CDN, dark-mode branch or second token system is allowed.

### Progressive enhancement

Primary page content, details, breadcrumbs, category links, product links, form labels and error
recovery render server-side. Shop/search/category parameters are supported as GET inputs.
JavaScript enhances instant filtering/sorting/pagination, drawers, tabs, gallery, cart/wishlist,
checkout transitions and prototype validation. With scripts disabled, direct routes and GET search
remain usable and native controls reveal all essential information.

## Project Structure

### Documentation

```text
specs/003-zakey-frontend-reference-build/
├── spec.md
├── reference-inventory.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── traceability.md
├── tasks.md
├── checklists/
├── contracts/
├── reference-evidence/
└── qa/
```

### Source code

```text
manage.py
pyproject.toml
uv.lock
package.json
package-lock.json
scripts/
├── copy-assets.js
├── check-js.js
├── qa-matrix.js
├── validate-qa-matrix.js
└── validate-rendered-html.js
config/
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py
storefront/
├── __init__.py
├── urls.py
├── views.py
├── fixture_provider.py
└── fixtures/frontend-fixtures.json
templates/
├── base.html
├── components/
├── partials/
└── pages/
static/
├── src/
│   ├── css/app.css
│   ├── css/reference.css
│   ├── js/app.js
│   ├── js/components/
│   ├── js/pages/
│   ├── js/state/
│   ├── js/utilities/
│   └── assets/
└── dist/
tests/
├── test_fixture_provider.py
├── test_routes.py
└── e2e/
    ├── interaction-journeys.spec.js
    ├── no-js.spec.js
    └── site-integrity.spec.js
playwright.config.js
.htmlvalidate.json
```

**Structure Decision**: A single presentation project keeps Django rendering, fixtures, templates,
assets and QA visible without implying a backend/frontend service split. No Django app scaffolding
that would create `models.py`, migrations or admin is used.

## Delivery Phases

1. Establish manifests, local toolchain and fixture/state contracts.
2. Implement the shared design tokens, semantic shell, header/navigation/search and footer.
3. Build reusable product, form, feedback, drawer, tab and summary components.
4. Deliver Home and discovery routes using the approved reference composition.
5. Deliver Product, Wishlist, Cart and the three-step Checkout prototype.
6. Deliver Account, About, Contact and error/recovery pages.
7. Complete native interactions and progressive-enhancement fallbacks.
8. Run automated tests, all-state/four-width captures, two visual passes and remediation.
9. Run clean-code, test and documentation guards; rerun affected evidence.

## Delegation Plan

Codex established tokens, base templates, fixture/state contracts and component standards first.
Claude Code then received one bounded, non-overlapping secondary-page batch under the current
master prompt's delegation authorization. The brief named permitted files, reference evidence,
acceptance checks, frontend-only/Git prohibitions and test commands. Codex inspected the complete
diff, corrected the About composition and shared-style/state integration, then ran the integrated
browser and guard suites. The exact review is recorded in `delegation-secondary-pages.md`.

## QA Evidence Plan

- Django page tests verify route/status/template/context and JavaScript-disabled GET fallbacks.
- Playwright no-JavaScript projects verify the 10 server-rendered shell routes for status, RTL,
  first heading, no-script notice and overflow at all four widths. Django tests separately verify
  GET catalogue/search normalization and parity.
- Playwright verifies navigation, filters, search, sorting, pagination, gallery, tabs, accordions,
  wishlist, cart, coupon, checkout, account, drawers, forms, recovery and reset behavior.
- `contracts/qa-matrix.json` is the executable route/state authority. A completeness test expands
  every entry across all four widths and requires its functional assertion, axe scan, rendered HTML
  validation, console/assets/overflow result and screenshot file.
- `html-validate` checks each rendered matrix state; browser listeners fail on uncaught exceptions,
  unexpected console errors, failed local responses, missing images or overflow in every cell.
- Screenshot filenames follow `{route}__{state}__{width}.png`; the matrix maps every file to its
  reference counterpart or explains that the required state was absent from the source.
- Pass one fixes structure, order, grid, density, proportions and breakpoints. Pass two fixes
  typography, RTL, Arabic wrapping, spacing, icons, imagery, controls, forms and contrast.

## Primary build and QA scripts

- `build:assets`: copies only pinned Fontsource files, Lucide SVGs and authored local media into
  `static/dist/`.
- `build:css`: compiles/minifies `static/src/css/app.css` to `static/dist/css/app.css`.
- `build`: runs asset copy then CSS compilation.
- `check:js`: syntax-checks every authored `.js`/`.mjs` file.
- `check:matrix`: validates the 56-state/four-viewport contract.
- `check:evidence`: requires every contracted implementation screenshot.
- `check:html`: validates the 224 browser-rendered HTML documents.
- `check`: runs the build and JavaScript, matrix and rendered-HTML checks.
- `test`: runs Playwright against its managed Django `webServer` using local Chrome.
- `test:no-js`: runs the no-JavaScript Playwright projects at all four widths.
- `screenshots`: runs functional, axe, integrity, HTML-evidence and screenshot checks across the
  complete matrix.

## Complexity Tracking

No constitution exception.

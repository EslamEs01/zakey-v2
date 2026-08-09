# Current-State Inventory

**Feature**: 004-zakey-commerce-backend-admin
**Captured**: 2026-08-04
**Base commit**: `98237d7` (branch `004-zakey-commerce-backend-admin`, branched from `003-zakey-frontend-reference-build`)
**Method**: Deterministic extraction (Python/AST/regex over the working tree) plus targeted source reads. Every claim below is traceable to a path and, where a specific statement is made about code, a line number.

> This document records what **exists today**. It authorizes nothing. It is the baseline against which the backend plan in `plan.md` is measured.

---

## 1. Django project

| Item | Value | Evidence |
|---|---|---|
| Project package | `config` | `config/settings.py` |
| Apps installed | `django.contrib.staticfiles`, `storefront` | `config/settings.py:9` |
| Middleware | `SecurityMiddleware`, `CommonMiddleware` **only** | `config/settings.py:10-13` |
| `DATABASES` | `{}` — **no database configured at all** | `config/settings.py:33` |
| `SECRET_KEY` | Hardcoded literal `"zakey-frontend-preview-only"` | `config/settings.py:6` |
| `DEBUG` | `True` (hardcoded) | `config/settings.py:7` |
| Root URLconf | `config.urls` | `config/settings.py:14` |
| Templates dir | `BASE_DIR / "templates"`, `APP_DIRS=True` | `config/settings.py:17-28` |
| Context processors | `django.template.context_processors.request` only | `config/settings.py:24-26` |
| Language / TZ | `ar-eg` / `Africa/Cairo`, `USE_I18N=True`, `USE_TZ=True` | `config/settings.py:35-38` |
| Static | `STATIC_URL=/static/`, `STATICFILES_DIRS=[BASE_DIR/"static"]` | `config/settings.py:40-41` |
| Python | `>=3.12,<3.13`; single dependency `Django==5.2.16` | `pyproject.toml` |

### Absent by design (verified, not assumed)

`django.contrib.auth`, `django.contrib.contenttypes`, `django.contrib.sessions`, `django.contrib.messages`, `django.contrib.admin` are **all absent** from `INSTALLED_APPS`. `SessionMiddleware`, `AuthenticationMiddleware`, `CsrfViewMiddleware` and `MessageMiddleware` are **all absent** from `MIDDLEWARE`. There are no models, no migrations, no admin classes, no forms, no services, no management commands and no database of any kind.

**Consequence**: the backend feature starts from a genuinely empty domain layer. There is no legacy schema to migrate and no existing model to refactor. Everything in `data-model.md` is new construction.

---

## 2. Public routes

All 13 routes are declared in `storefront/urls.py` under `app_name = "storefront"`. **Every route is GET-only**; no view inspects `request.method`, and no view accepts or processes a POST.

| Name | URL | View | Template | Query params read | Purpose |
|---|---|---|---|---|---|
| `home` | `/` | `views.home:15` | `pages/home.html` | `qa` | Landing page; best-sellers, featured, testimonials |
| `shop` | `/shop/` | `views.shop:31` | `pages/shop.html` | `q`, `category`, `feature`*, `priceMin`, `priceMax`, `availability`, `sort`, `page`, `qa` | Catalogue |
| `collection` | `/collections/<slug>/` | `views.collection:35` | `pages/shop.html` | same as `shop` | Collection-filtered catalogue |
| `search` | `/search/` | `views.search:42` | `pages/shop.html` | same as `shop` | Search results |
| `product` | `/products/<slug>/` | `views.product_detail:46` | `pages/product_detail.html` | `qa` | Product detail |
| `cart` | `/cart/` | `views.cart:53` | `pages/cart.html` | `qa` | Cart shell (contents rendered by JS) |
| `checkout` | `/checkout/` | `views.checkout:57` | `pages/checkout.html` | `step`, `qa` | 3-step checkout shell |
| `wishlist` | `/wishlist/` | `views.wishlist:64` | `pages/wishlist.html` | `qa` | Wishlist shell |
| `account` | `/account/` | `views.account:68` | `pages/account.html` | `state`, `tab`, `qa` | Account prototype |
| `about` | `/about/` | `views.about:77` | `pages/about.html` | `qa` | Static content |
| `contact` | `/contact/` | `views.contact:81` | `pages/contact.html` | `qa` | Contact page |
| `error-404` | `/errors/404/` | `views.not_found_preview:91` | `pages/404.html` | `qa` | QA preview (returns 404 status) |
| `error-500` | `/errors/500/` | `views.server_error_preview:97` | `pages/500.html` | `qa` | QA preview (returns 500 status) |

`*` `feature` repeats (`getlist`), see `storefront/fixture_provider.py:117-120`.

Handlers `handler404` / `handler500` are bound in `config/urls.py:9-10`.

### Allowed query-parameter values (server-normalized)

| Param | Allowed | Normalization | Evidence |
|---|---|---|---|
| `sort` | `featured`, `price-asc`, `price-desc`, `name` | unknown → `featured` | `fixture_provider.py:12,138` |
| `availability` | `available`, `unavailable` | unknown → `None`; `available` matches product state `available` **or** `limited` | `fixture_provider.py:137,183-190` |
| `category` | any category slug | unknown slug → `None` | `fixture_provider.py:131` |
| `collection` | any collection slug | unknown slug → `None` | `fixture_provider.py:133` |
| `priceMin` / `priceMax` | integers ≥ 0 | reversed bounds swapped; clamped to ≥0 | `fixture_provider.py:121-124,134-135` |
| `feature` | any key present on some product | unknown discarded | `fixture_provider.py:112-120,136` |
| `page` | integer ≥ 1 | clamped to `pageCount` after filtering | `fixture_provider.py:127,199-201` |
| `q` | free text | whitespace collapsed; matches `name` + `shortDescription`, case-folded | `fixture_provider.py:129,159-166` |
| `step` (checkout) | `shipping`, `payment`, `review` | unknown → `shipping` | `views.py:58-60` |
| `state` (account) | `signed-out`, `signed-in` | unknown → `signed-out` | `views.py:69-71` |
| `tab` (account) | free string | default `orders` | `views.py:72` |
| `qa` | page/state pair from `qa-matrix.json` | default `default` | `views.py:10` |

**Pagination**: fixed page size **6** (`fixture_provider.py:196`).

### Routes that present a mutation UI but have no server handler

`/cart/` (quantity, remove, coupon), `/checkout/` (shipping, payment, place order), `/wishlist/` (toggle, add to cart), `/account/` (sign-in, settings), `/contact/` (message), and the newsletter component. **Confirmed**: all are client-side only. This is the expected state for Specification 003 and is the primary integration surface for this feature.

---

## 3. Templates

18 HTML templates. `templates/base.html` is the shell; `partials/header.html` and `partials/footer.html` are global; `components/` holds `product_card.html`, `catalogue_filters.html`, `newsletter.html`, `icon.html`; `pages/` holds the 11 page templates plus `404.html` and `500.html`.

**139 distinct `data-*` attribute hooks** are used as the JS binding surface (full list in `frontend-contract.md` §4). These are behavioural contract, not decoration: renaming one breaks a JS module.

**`{% csrf_token %}` appears in zero templates** — verified across all 18 files. Every form that will become a POST endpoint needs a CSRF token added.

---

## 4. Forms and inputs

| Template:line | Purpose | method | action | Server-wired today |
|---|---|---|---|---|
| `partials/header.html:47` | Site search | `get` | `storefront:search` | ✅ yes |
| `components/catalogue_filters.html:1` | Catalogue filters | (default get) | search/collection/shop | ✅ yes |
| `pages/shop.html:20` | Sort | `get` | (self) | ✅ yes |
| `pages/404.html:31` | Error-page search | `get` | `storefront:search` | ✅ yes |
| `pages/account.html:228` | Account settings | `get` | `storefront:account` | ⚠️ GET-as-demo |
| `pages/account.html:274` | Sign-in | `get` | `storefront:account` | ⚠️ GET-as-demo |
| `pages/contact.html:55` | Contact message | `get` | `storefront:contact` | ⚠️ GET-as-demo |
| `components/newsletter.html:5` | Newsletter | — | — | ❌ JS only |
| `pages/cart.html:33` | Coupon | — | — | ❌ JS only |
| `pages/checkout.html:59` | Shipping step | — | — | ❌ JS only |
| `pages/checkout.html:174` | Payment step | — | — | ❌ JS only |

### Field-name inventory (the names the backend must accept verbatim)

- **Checkout shipping** (`pages/checkout.html`): `fullName` (text, required, maxlength 80, L70), `email` (email, required, inputmode email, maxlength 120, L76), `mobile` (tel, required, inputmode tel, maxlength 18, L81), `governorate` (select, required, L93), `city` (text, required, maxlength 80, L103), `areaKey` (select, optional, L108), `street` (textarea, required, maxlength 140, L115), `building` (text, required, maxlength 24, L120), `landmark` (text, optional, maxlength 100, L125), `shippingMethod` (radio, L135), `installation` (checkbox, value `requested`, L150), `acknowledgement` (checkbox, required, L156)
- **Checkout payment**: `paymentMethod` (radio, L180)
- **Cart**: `coupon` (text, maxlength 24, `pages/cart.html:39`)
- **Product**: `finish` (radio, `pages/product_detail.html:24`)
- **Contact**: `name`, `email`, `phone`, `subject` (select), `message` (textarea) — all required; `qa` hidden
- **Newsletter**: `email` (required)
- **Catalogue**: `q`, `category`, `feature`, `priceMin`, `priceMax`, `availability`, `sort`

No input that collects user data lacks a `name` attribute.

---

## 5. Static assets and JavaScript

**16 JS modules, 1,833 lines total**, ES modules, no framework, no bundler, no CDN.

| Module | Lines | Role |
|---|---|---|
| `pages/checkout.js` | 449 | 3-step checkout, validation, totals, eligibility |
| `pages/catalogue.js` | 246 | Client-side catalogue re-render |
| `pages/account.js` | 244 | Account tabs, demo sign-in |
| `pages/cart.js` | 186 | Cart lines, totals, coupon |
| `pages/contact.js` | 151 | Contact form prototype |
| `pages/wishlist.js` | 88 | Wishlist grid |
| `state/store.js` | 85 | `PrototypeStore` (EventTarget) |
| `state/storage-adapter.js` | 76 | `localStorage` envelope |
| `pages/product.js` | 64 | Gallery, finish, quantity |
| `components/header.js` | 60 | Menu, search, counters |
| `app.js` | 52 | Bootstrap + dynamic page module import |
| `utilities/dom.js` | 40 | `announce`, `setBusy`, validators |
| `components/dialog.js` | 38 | Focus-trap dialogs |
| `components/forms.js` | 31 | Prototype form status |
| `components/wishlist.js` | 20 | Wishlist toggles |
| `pages/home.js` | 3 | No-op |

**Zero `fetch` / `XMLHttpRequest` calls exist** — the frontend never contacts a server beyond page loads.

CSS: 7 hand-authored files under `static/src/css/`, compiled by Tailwind 4.3.3 CLI into `static/dist/css/app.css`. Assets: 9 product image pairs, 4 category images, 9 demo PDFs, payment/shipping SVG icons, brand marks, partner and team images — all local, no remote URLs.

---

## 6. Fixture layer

`storefront/fixtures/frontend-fixtures.json` — 58,562 bytes, `schemaVersion: 1`, `fixtureStatus: "demonstration"`.

| Section | Records | Section | Records |
|---|---|---|---|
| `meta` | 3 keys | `governorates` | **27** |
| `site` | 15 keys | `serviceEligibility` | 3 keys (14 areas) |
| `navigation` | 4 keys | `shippingOptions` | 3 |
| `categories` | 4 | `paymentOptions` | 6 |
| `collections` | 6 | `prototypeAccounts` | 2 |
| `products` | 9 | `prototypeCarts` | 6 |
| `reviews` | 9 | `prototypeWishlists` | 2 |
| `faqs` | 8 | `partners` / `team` | 4 / 4 |

`storefront/fixture_provider.py` (298 lines) loads and **validates** this file at import, enforcing: required sections (L43-61), `fixtureStatus == "demonstration"` (L65), unique ids/slugs (L68-73), exactly 27 governorates (L74-75), price range 2190–7490 (L84), local-only asset paths (L37-39, L86-87), referential integrity for reviews/FAQs/related products (L88-94).

`get_client_fixture()` (L280-289) serialises **14 of the 17 sections** into the page for the JS layer — this is how the browser gets all catalogue and commerce data today. Excluded: `navigation`, `partners`, `team`.

---

## 7. Tests and QA

| Path | Framework | Scope |
|---|---|---|
| `tests/test_routes.py` | Django `TestCase` | Route status/template assertions |
| `tests/test_fixture_provider.py` | Django `TestCase` | Fixture contract + catalogue logic |
| `tests/test_static_export.py` | Django `TestCase` | Static-export correctness |
| `tests/e2e/interaction-journeys.spec.js` | Playwright 1.62.1 | 7 user journeys incl. full checkout flow |
| `tests/e2e/navigation-links.spec.js` | Playwright | Link crawl + catalogue behaviour vs. live DOM |
| `tests/e2e/no-js.spec.js` | Playwright (`javaScriptEnabled:false`) | 10 routes: 200, RTL, visible `h1`, overflow ≤1px |
| `tests/e2e/site-integrity.spec.js` | Playwright + `@axe-core/playwright` | Per-state QA matrix: status, RTL, overflow, broken images, **axe critical/serious = 0**, console errors, screenshots |
| `tests/accessibility/` | — | ⚠️ **EMPTY DIRECTORY** |
| `tests/visual/` | — | ⚠️ **EMPTY DIRECTORY** |
| `tests/helpers/` | — | ⚠️ **EMPTY DIRECTORY** |

Run via `uv run python manage.py test` and `npm run qa` (which chains build → check:js → check:matrix → test → check:html → check:evidence → test:pages).

Playwright declares **8 projects** — `chrome-{1440,1024,768,390}` and `no-js-{1440,1024,768,390}` — from `VIEWPORT_WIDTHS = [1440, 1024, 768, 390]` (`playwright.config.js:6`), height 1200, locale `ar-EG`, timezone `Africa/Cairo`.

### ⚠️ Three findings that change the backend plan

**1. There is no visual-regression framework.** `tests/visual/` is empty. `site-integrity.spec.js` *captures* screenshots as evidence artifacts but **never diffs them against a baseline**. The preservation gate this feature depends on must therefore be **built**, not extended (T-0102). `npm run test:a11y` points at the empty `tests/accessibility/` and today runs **zero tests**; the real axe coverage lives inside `site-integrity.spec.js:152-154`.

**2. `FrontendBoundaryTests` will fail by design.** `tests/test_fixture_provider.py:213-238` asserts that the database engine is `django.db.backends.dummy` with an empty `NAME`, that `admin`/`auth`/`contenttypes`/`sessions`/`messages` are **absent** from `INSTALLED_APPS`, that `SessionMiddleware` is absent, and that `storefront.models`, `storefront.admin` and `storefront/migrations/` do not exist. Every one of those assertions is deliberately inverted by this feature. This test is a **frontend-phase boundary guard, not a regression test** — it must be retired and replaced with a route/rendering contract test in the same task that enables the auth stack (T-0203a). Any task claiming "all existing tests pass unchanged" after Phase 2 is wrong.

**3. CI does not run on this branch.** `.github/workflows/pages.yml:3-8` triggers only on `main` and `003-zakey-frontend-reference-build`, with `workflow_dispatch`. There is no `pull_request` trigger and no `004-*` branch. CI must be extended before it can gate any backend work (T-0207).

**Absent**: pytest, pytest-django, factory_boy/model-bakery, coverage tooling, any database-backed test, any concurrency test, any PostgreSQL service, any screenshot-diff baseline. The backend feature must add all of these.

---

## 8. Git state at capture

```
Branch: 004-zakey-commerce-backend-admin (created from 003 at 98237d7)
HEAD:   98237d7 Refine catalogue regressions and homepage claims
Status: clean except untracked specs/004-zakey-commerce-backend-admin/
Remotes: origin -> github.com/EslamEs01/zakey-v2 (unchanged)
```

Local branches `001-premium-storefront-experience`, `002-egypt-premium-storefront`, `003-zakey-frontend-reference-build`, `main` are untouched. `specs/` contained only `003-…` before this feature, confirming **004** as the next unused number.

---

## 9. Executor and reviewer record

| Assignment | Executor | Outcome | Claude's verification |
|---|---|---|---|
| A1 route/view inventory | Kimi | **Timed out** (exit 124, 25 min) — analysis correct in transcript, report never written | Re-derived deterministically by Claude from `urls.py`/`views.py`; §2 above |
| A2 fixture contract | Kimi | **Timed out** (exit 124) — transcript shows correct section counts and correct conclusion that views compute no totals | Re-derived by Claude via JSON introspection; §6 above and `frontend-contract.md` |
| A3 JS state | Kimi | **Stalled then timed out** — no usable output | Read in full by Claude; §5 above and `frontend-contract.md` §3 |
| A4 forms inventory | Kimi | **Timed out** (exit 124) | Re-derived deterministically by Claude via regex over all 18 templates; §4 above |
| B1 JS business rules (secondary modules) | Kimi | Re-issued with narrowed scope, incremental-write instruction, 50-min budget | See §10 |
| B2 tests/deps inventory | Kimi | Re-issued with narrowed scope and 50-min budget | See §10 |

**Claude's finding on delegation**: the first four assignments were scoped too broadly for a single Kimi invocation. Kimi's *reasoning* was sound — its transcript independently reached the same section counts, the same "views compute no totals" conclusion, and the same 1:1 review/product mapping Claude verified — but every run exhausted its wall clock at the report-writing step. Corrective action taken: narrow the file set per assignment, require the output file to be written early and appended to, and raise the budget. Mechanical extraction (form fields, `data-*` hooks, fixture schema) was moved to deterministic scripts, which are both faster and not subject to hallucination. This division is carried into `tasks.md`: Kimi executes bounded implementation with tests; deterministic evidence is produced by scripts, not prose.

## 10. Kimi batch 2 results

Recorded in `research.md` §9 once the run completes; findings that change any decision are reflected in the affected artifact and noted in the traceability record.

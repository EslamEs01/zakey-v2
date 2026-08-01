# Quickstart: ZAKEY Premium Public Storefront Experience

**Feature**: `001-premium-storefront-experience`
**Date**: 2026-07-31
**Status**: **PLANNED COMMANDS ONLY.**

> **Nothing in this file has been executed.** No environment was created, no migration applied, no
> test run, no asset built, no screenshot captured during planning. Every command below is an
> instruction for the implementation phase. No result, pass, or failure is claimed anywhere in this
> document, because none has been observed.
>
> Constitution XII.6 requires reported results to be the exact commands executed and their exact
> outcomes. When these commands are run, their real output is recorded in the verification artifact —
> not here.

---

## 0. Prerequisites (already verified present)

| Tool | Version | Verified |
| --- | --- | --- |
| Python | 3.12.3 | yes |
| Django | 5.2.16 | yes |
| pytest / pytest-django | 9.1.1 / present | yes |
| django-environ, whitenoise, Pillow | present | yes |
| Node packages: tailwindcss, @tailwindcss/cli | 4.3.3 | yes |
| @playwright/test | 1.62.1 | yes |
| @axe-core/playwright | 4.12.1 | yes |
| @fontsource/poppins | 5.3.0 | yes |
| lucide | 1.28.0 | yes |

**Do not install or upgrade anything.** If a command fails for a missing package, stop and raise it —
adding a dependency requires a Constitution III.4 assessment, not an ad-hoc install.

Playwright browser binaries are the one likely gap; installing a browser runtime is not a project
dependency change:

```bash
npx playwright install chromium
```

---

## 1. Environment setup

```bash
cd /media/mekky/work/backend/zakey-v2

# Python environment (already present at .venv)
.venv/bin/python --version

# Environment variables — .env is gitignored; .env.example is committed
cp .env.example .env
# Required keys, validated at startup by django-environ (startup fails loudly if absent):
#   DJANGO_SECRET_KEY, DJANGO_DEBUG, DJANGO_ALLOWED_HOSTS, DATABASE_URL
#   DATABASE_URL for local dev: sqlite:///db.sqlite3

.venv/bin/python manage.py migrate          # contrib + sessions + Enquiry only
```

---

## 2. Asset build

```bash
# CSS — Tailwind v4 CLI, single stylesheet, token authority
npx @tailwindcss/cli \
  -i storefront/static/src/css/app.css \
  -o storefront/static/css/app.css --minify

# Fonts — copy the 4 verified Poppins woff2 weights into static/fonts/
python tools/build_fonts.py

# Icons — build the SVG sprite from lucide (only icons actually used)
python tools/build_icon_sprite.py

# Product imagery — normalise to square on --color-subtle, emit WebP renditions,
# derive alt text, write the asset manifest. Never crops, stretches, or upscales.
python tools/build_product_images.py

# Static collection (production storage, hashed + compressed)
.venv/bin/python manage.py collectstatic --noinput
```

---

## 3. Run locally

```bash
.venv/bin/python manage.py runserver
# Production-mode check (used for all performance measurement):
DJANGO_DEBUG=False .venv/bin/python manage.py runserver --insecure
```

---

## 4. Django system checks

```bash
.venv/bin/python manage.py check
.venv/bin/python manage.py check --deploy      # production settings
.venv/bin/python manage.py makemigrations --check --dry-run   # fails if a migration is missing
```

---

## 5. Python tests

```bash
.venv/bin/python -m pytest                                   # everything
.venv/bin/python -m pytest tests/contract/ -v                # catalog provider contract suite
.venv/bin/python -m pytest tests/unit/test_loader.py -v      # 3-register join, digest pinning, fail-closed
.venv/bin/python -m pytest tests/unit/test_cart_service.py tests/unit/test_wishlist_service.py -v
.venv/bin/python -m pytest tests/unit/test_viewmodels.py -v  # price_display/price_on_request invariants
.venv/bin/python -m pytest tests/views/ -v                   # status codes, redirects, gating
.venv/bin/python -m pytest tests/templates/ -v               # rendering against the FAKE provider
.venv/bin/python -m pytest tests/unit/test_enquiry_faults.py -v   # fault injection → no confirmation
.venv/bin/python -m pytest --cov=storefront --cov-report=term-missing
```

**The contract suite is the Feature 002 gate.** It must pass unchanged against
`DatabaseCatalogProvider` before the provider swap.

---

## 6. End-to-end, JavaScript behaviour, and no-JS

```bash
npx playwright test                                    # full suite
npx playwright test tests/e2e/user-stories/            # one spec per user story Independent Test
npx playwright test tests/e2e/session-persistence.spec.ts   # 5 navigations + reload (SC-035, SC-036)
npx playwright test tests/e2e/gallery.spec.ts tests/e2e/filters.spec.ts tests/e2e/nav.spec.ts
npx playwright test tests/e2e/no-js.spec.ts            # javaScriptEnabled: false — full journey
npx playwright test --headed --project=chromium        # observe a run
```

---

## 7. Accessibility

```bash
# Automated: every in-scope page + every interactive surface in its OPEN state
npx playwright test tests/e2e/axe.spec.ts

# Open-state coverage: mobile nav, filter drawer, dialog, each checkout step
npx playwright test tests/e2e/axe-open-states.spec.ts
```

**Manual keyboard inspection is required and cannot be scripted** (Constitution VIII.6). Walk the
full journey — browse → filter → search → product → wishlist → cart → checkout → review → enquiry —
using only the keyboard, and record for each surface: tab order matches visual order; focus is
visible at every stop; focus is trapped in drawers/dialogs; Escape dismisses and returns focus to
the opener; no keyboard trap. Record observations in the verification artifact.

---

## 8. Audits

```bash
python tools/audit_colors_source.py       # no hex/rgb/hsl/oklch outside tokens.css; no -[#…]
python tools/audit_compiled_css.py        # COMPILED production CSS: extracts + NORMALISES every
                                          # colour value and asserts membership of the ratified 18,
                                          # permitted keywords, verified gradients, or recorded
                                          # alpha derivatives. Fails on #ff0000 / #123456 / default
                                          # palette values / unauthorised alpha / unauthorised
                                          # gradients EVEN THOUGH Tailwind compiles them.
                                          # Must run AFTER the production build.
python tools/audit_boundary.py            # templates/JS never touch catalog/data or the loader
python tools/audit_template_attrs.py      # templates use only C-VIEWMODEL attributes
python tools/audit_content_integrity.py   # no price/rating/award/stock/warranty/contact placeholders
python tools/audit_escaping.py            # no unjustified |safe / autoescape off

npx playwright test tests/audits/rendered-colors.spec.ts   # computed colours ∈ ratified 18; page-vs-home drift
npx playwright test tests/audits/contrast.spec.ts          # every observed pairing vs its threshold
npx playwright test tests/audits/console-errors.spec.ts    # zero unexpected console errors
npx playwright test tests/audits/broken-links.spec.ts      # zero broken internal links
npx playwright test tests/audits/responsive-overflow.spec.ts   # scrollWidth ≤ viewport at 1440/1024/768/390
npx playwright test tests/audits/product-grid-columns.spec.ts  # §8.1 matrix on every product-card
                                                               # listing grid: 4 @1440, 4 @1024,
                                                               # 2 @768, 2 @390 (SC-051)
npx playwright test tests/audits/third-party-origins.spec.ts   # zero third-party origins
npx playwright test tests/audits/order-artifacts.spec.ts       # zero order records/numbers after a full journey
```

---

## 9. Performance

```bash
# Production-mode build first
DJANGO_DEBUG=False .venv/bin/python manage.py collectstatic --noinput
npx @tailwindcss/cli -i storefront/static/src/css/app.css -o storefront/static/css/app.css --minify

npx playwright test tests/audits/page-weight.spec.ts    # PB-1..PB-4, PB-18
npx playwright test tests/audits/web-vitals.spec.ts     # PB-8 LCP, PB-9 CLS, PB-10 INP
python tools/report_asset_budgets.py                    # PB-5 JS shared, PB-6 per page, PB-7 CSS
```

Measurement conditions, applied identically every run: `DEBUG=False`, compiled+minified assets,
WhiteNoise manifest storage, Playwright Chromium, CPU throttle 4×, Fast-3G for cold runs, cleared
cache/storage for cold and a warm second navigation. Both cold and warm results are recorded.

---

## 10. Screenshots and visual QA

```bash
npx playwright test tests/e2e/screenshots.spec.ts       # 1440 / 1024 / 768 / 390, all pages + states
```

Captures: homepage; listing (unfiltered, filtered, no-results); category; collection; search
(results, no-results); product detail (multi-image, single-image); cart (populated, empty); checkout
information (clean, invalid); order review; wishlist (populated, empty); About; Contact; FAQ; 404;
500 — plus mobile nav open, filter drawer open, dialog open, toast visible, focus-visible per control
family, loading skeletons, and reduced-motion.

**Then inspect them.** Capturing is not QA (Constitution XIII.6). For each screenshot record: colour
accuracy against the token table, palette drift versus the homepage, spacing rhythm and hierarchy,
card proportions, typography character, overflow/clipping, and focus visibility. Two full
critique-and-correction passes are required (Constitution XIII.3).

**Both passes MUST additionally inspect the product-card grid at ALL FOUR widths** against the
reference, confirming the §8.1 matrix — **4 columns at 1440px, 4 at 1024px, 2 at 768px, 2 at 390px**
— plus CG-1…CG-7 at each width: no horizontal overflow; 1:1 media preserved; targets ≥24×24 (44×44
primary); name wrapping to at most two lines; supplier attribution and the price-or-price-on-request
statement fully visible and never truncated; body text ≥12px; nothing clipped or overlapping
(SC-051).

---

## 11. Code-quality guards

```bash
.venv/bin/ruff check .
.venv/bin/ruff format --check .
npx prettier --check "**/*.{css,js,html}"
```

Then run the `clean-code-guard`, `test-guard`, and `docs-guard` skills and resolve or explicitly
justify every finding (Constitution XIV.10).

---

## 12. Full verification sequence

```bash
.venv/bin/python manage.py check && \
.venv/bin/python manage.py check --deploy && \
.venv/bin/python manage.py makemigrations --check --dry-run && \
.venv/bin/python -m pytest && \
npx @tailwindcss/cli -i storefront/static/src/css/app.css -o storefront/static/css/app.css --minify && \
.venv/bin/python manage.py collectstatic --noinput && \
python tools/audit_colors_source.py && \
python tools/audit_compiled_css.py && \
python tools/audit_boundary.py && \
python tools/audit_template_attrs.py && \
python tools/audit_content_integrity.py && \
python tools/audit_escaping.py && \
npx playwright test && \
.venv/bin/ruff check . && \
npx prettier --check "**/*.{css,js,html}"
```

Record the exact command, exit status, and output of each step. Then complete the manual keyboard
pass, the two visual critique passes, and the fifteen Definition-of-Done conditions.

**Report "implemented" and "verified" as two separate facts** (Constitution XII.5). Do not report a
command as passing unless it was run and observed to pass.

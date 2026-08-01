# Implementation Plan: ZAKEY Premium Public Storefront Experience

**Branch**: `001-premium-storefront-experience` | **Date**: 2026-07-31 | **Spec**: [spec.md](./spec.md)
**Constitution**: v1.1.0 | **Input**: Feature specification at `/specs/001-premium-storefront-experience/spec.md`
**Companion artifacts**: [research.md](./research.md) · [data-model.md](./data-model.md) · [contracts/](./contracts/) · [quickstart.md](./quickstart.md) · [traceability.md](./traceability.md)

## Summary

A server-rendered Django storefront presenting 21 verified, supplier-branded (Lezn) smart locks with
their true attribution, behind a replaceable catalogue provider port. Session-backed cart and
wishlist, checkout information collection, and a validated order-review state that terminates in a
real enquiry — never in an order. One Tailwind v4 token authority carrying the ratified 18-value
palette, enforced at build time. Zero fabricated claims: no price, stock, rating, warranty, or
delivery figure exists in the governed dataset, so none can reach a page.

---

## 1. Technical Context

| Aspect | Decision | Evidence |
| --- | --- | --- |
| **Language/Version** | Python 3.12.3 | verified in environment |
| **Framework** | Django 5.2.16, server-rendered templates | verified installed |
| **Storage (Feature 001)** | SQLite dev DB for Django infrastructure only (sessions, contrib, one `Enquiry` model). **Catalogue is not in the database.** PostgreSQL-ready via `DATABASE_URL` | R-005 |
| **Catalogue source** | Three checksum-pinned governed JSON registers → frozen dataclasses in memory | R-001 |
| **CSS** | Tailwind CSS 4.3.3, CSS-first `@theme`, compiled locally by `@tailwindcss/cli` | R-003, R-007 |
| **JavaScript** | Native ES modules, no framework, no bundler | R-007 |
| **Fonts** | Self-hosted Poppins woff2 400/500/600/700 from `@fontsource/poppins@5.3.0` | R-008 |
| **Icons** | Build-time SVG sprite from `lucide@1.28.0`; no runtime icon JS | R-009 |
| **Static serving** | WhiteNoise, `CompressedManifestStaticFilesStorage` | R-007 |
| **Testing** | pytest 9.1.1 + pytest-django; Playwright 1.62.1; `@axe-core/playwright` 4.12.1 | R-015 |
| **Target platform** | Modern evergreen browsers; **full function without JavaScript** | R-014 |
| **Project type** | Web application, single Django project | — |
| **Performance goals** | Spec §13 PB-1…PB-19, unchanged | §9 below |
| **Constraints** | No new dependency, no SPA, no CDN, no payment, no order creation | invocation + Constitution III |
| **Scale** | 21 products, 3 categories, 6 collections, 6 access methods, 25 media assets | verified |

**No NEEDS CLARIFICATION remains.** All 19 research items are decided with evidence.

---

## 2. Architecture Boundaries

```text
┌──────────────────────────────────────────────────────────────────────┐
│ PRESENTATION            templates/ · static/src/js · static/src/css  │
│   sees ONLY view models (C-VIEWMODEL). Cannot name a data source.    │
├──────────────────────────────────────────────────────────────────────┤
│ VIEW / ASSEMBLY         views, forms, view-model builders            │
│   depends on the CatalogProvider PORT, never a concrete adapter      │
├──────────────────────────────────────────────────────────────────────┤
│ DOMAIN SERVICES     CartService · WishlistService · CheckoutService  │
│   session-owned state; money resolved via the port, never stored     │
├──────────────────────────────────────────────────────────────────────┤
│ CATALOG PORT (C-CATALOG)                                             │
│   ┌── StaticCatalogProvider  (Feature 001) ──┐                       │
│   └── DatabaseCatalogProvider (Feature 002) ─┘  ← swap point         │
├──────────────────────────────────────────────────────────────────────┤
│ DATA           3 governed JSON registers (read-only, digest-pinned)  │
│                + Django session store + one Enquiry table            │
└──────────────────────────────────────────────────────────────────────┘
```

**The two insulation layers.** The port replaces the *data source*; the view models replace the
*template coupling*. Both are required — a port alone still leaves templates shaped by provider
types. Together they make the Feature 002 swap a configuration change.

**Dependency rule.** Arrows point downward only. Presentation never reaches past the view layer;
the view layer never imports a concrete provider; services never import templates. Enforced by the
boundary audit (§11).

---

## 3. Application Structure

```text
config/                        # Django project
  settings/{base,dev,prod}.py  # django-environ; fail loudly on missing required vars
  urls.py · wsgi.py · asgi.py

storefront/                    # single Django app — the public storefront
  catalog/
    ports.py                   # CatalogProvider ABC, ProductQuery, SortOption
    providers/static_provider.py
    loader.py                  # validates + joins the 3 registers; fails closed
    models_read.py             # frozen dataclasses (Tier A)
    data/                      # the 3 governed JSON registers + digests
  cart/services.py             # CartService, WishlistService
  checkout/{forms,services}.py # CheckoutService, OrderReviewBuilder
  enquiry/{models,forms}.py    # the ONLY Django domain model
  content/                     # verified Tier-G informational content
  viewmodels/                  # view-model builders (C-VIEWMODEL)
  views/                       # home, catalog, cart, wishlist, checkout, enquiry, pages, errors
  templatetags/                # presentation-only helpers
  urls/                        # namespaced route modules

templates/
  base.html
  layout/{header,footer,announcement,mobile_nav,skip_link}.html
  components/                  # ONE partial per component family (C-01…C-38)
  pages/                       # page templates; composition only
  errors/{404,500,403_csrf}.html

static/
  src/css/{tokens.css,app.css} # tokens.css = the single token authority
  src/js/{cart,wishlist,filters,gallery,nav,toast}.js
  fonts/ · img/products/ · icons/sprite.svg

tests/{unit,contract,views,templates,e2e,audits}/
tools/                         # build-time asset + audit scripts
```

**One app, not many.** With 21 products and one bounded context, splitting into `products`,
`cart`, `checkout` apps would add import ceremony without a seam that matters. The seams that
matter — the catalogue port and the view models — are explicit inside `storefront/`. Feature 002
may split apps when persistent domains justify it.

---

## 4. Design-Token Authority

`static/src/css/tokens.css` is the **only** place a colour, type size, radius, or spacing value is
defined. It opens with a colour-namespace reset so unauthorised colour utilities do not compile
(R-003) — verified against installed Tailwind 4.3.3.

```css
@import "tailwindcss";

@theme {
  --color-*: initial;            /* every default Tailwind colour utility is removed */

  /* ── Core brand tokens (5) ─────────────────────────────── */
  --color-navy:            #0D1B3D;
  --color-gold:            #C9A227;
  --color-canvas:          #F8F9FB;
  --color-surface:         #FFFFFF;
  --color-ink:             #1F2937;

  /* ── Reference-derived support tokens (13) ─────────────── */
  --color-muted:               #6B7280;
  --color-subtle:              #EEF0F5;
  --color-gold-hover:          #E0B62E;
  --color-placeholder-nontext: #9CA3AF;   /* NON-TEXT ONLY — see below */
  --color-navy-raised:         #1A3060;
  --color-navy-hover:          #1A2F5A;
  --color-navy-tint:           #2A4070;
  --color-navy-deep:           #162D5E;
  --color-line-06:             rgba(13, 27, 61, 0.06);
  --color-line-08:             rgba(13, 27, 61, 0.08);
  --color-line-10:             rgba(13, 27, 61, 0.10);
  --color-line-15:             rgba(13, 27, 61, 0.15);
  --color-line-20:             rgba(13, 27, 61, 0.20);

  --font-sans: "Poppins", ui-sans-serif, system-ui, sans-serif;
  --radius-control: 0.75rem;   /* 12px */
  --radius-card:    1rem;      /* 16px */
  --radius-media:   1.5rem;    /* 24px */
}
```

**Total: 18 governed colour values — 5 core + 13 support.**

### How the enforcement actually works (proven, 2026-08-01)

Tailwind v4 declares its built-in palette as `@theme default { --color-red-500: oklch(…) … }`
theme variables. `--color-*: initial` **clears that entire namespace**, so the default colours are
not merely overridden — they cease to exist, and no utility can be generated from them.

An isolated probe was compiled with the repository's own installed `tailwindcss@4.3.3` CLI from a
scratch directory **outside the repository**, installing nothing and modifying no dependency or
lockfile. Measured result (7,711-byte output):

| Class | Example utilities | Compiled? |
| --- | --- | --- |
| Default Tailwind colours | `bg-red-500`, `text-gray-200`, `bg-green-500`, `text-blue-700`, `bg-gray-900`, `border-slate-300` | **No — 0 occurrences** |
| Built-in palette values | any `oklch(…)` | **No — 0 occurrences** |
| Governed tokens | `.bg-navy`, `.text-gold`, `.border-line-10`, `.bg-subtle`, `.text-muted`, `.bg-gold-hover` | **Yes** |
| Non-colour utilities | `.flex`, `.grid`, `.p-4`, `.rounded-xl`, `.shadow-sm` | **Yes — unaffected** |
| Arbitrary literals | `.bg-[#ff0000]`, `.text-[#123456]` | **Yes — still compile** |

**There is no contradiction between "the default palette is gone" and "arbitrary literals compile".**
They are different mechanisms:

1. **Named off-palette colours are unrepresentable** — the reset deletes them from the theme, so
   `bg-red-500` produces no CSS at all.
2. **Literal off-palette colours are still expressible** via arbitrary values, and are therefore
   closed by a *separate* control: the source-colour audit, which fails the build on any hex,
   `rgb(`, `hsl(`, `oklch(` literal outside `tokens.css`, and on any `-[#…]` arbitrary colour value.

Together these give complete coverage: mechanism 1 removes the accident, mechanism 2 removes the
deliberate bypass. Component colours are consumed **only** through semantic token utilities
(`bg-navy`, `text-muted`), never as literals.

### Required two-layer palette-drift verification

The probe proves that name-based checking alone is **insufficient**: `bg-[#ff0000]` and
`text-[#123456]` compile successfully despite the reset. Checking only for default Tailwind colour
names and `oklch(` would pass a build containing pure red. Both layers below are therefore
mandatory.

**Layer 1 — source audit** (`tools/audit_colors_source.py`). Scans templates, CSS, JavaScript, and
relevant configuration, excluding only `tokens.css`, and **fails the build** on any of:

| Pattern | Example |
| --- | --- |
| Arbitrary colour utility | `bg-[#ff0000]`, `text-[rgb(1,2,3)]`, `border-[hsl(…)]` |
| Raw hexadecimal | `#ff0000`, `#f00`, `#ff0000cc` |
| `rgb()` / `rgba()` | `rgba(255,0,0,0.5)` |
| `hsl()` / `hsla()` | `hsl(0 100% 50%)` |
| `oklch()` / `oklab()` / `color()` | any occurrence |
| Inline colour style | `style="color:…"`, `style="background:…"` |
| Unauthorised gradient | any `from-`/`via-`/`to-` pairing not in the verified list |
| Page-specific colour declaration | a colour defined anywhere other than `tokens.css` |

**Layer 2 — compiled-CSS audit** (`tools/audit_compiled_css.py`). Parses the **built production
stylesheet**, extracts **every** colour value from every declaration, **normalises** them to a
canonical form (lowercase hex; `rgb()`/`rgba()`/`hsl()`/`oklch()` converted; shorthand expanded;
alpha preserved), and asserts each normalised value is a member of exactly one of:

1. the **ratified 18** governed values;
2. an explicitly permitted keyword — `transparent`, `currentColor`, `inherit`, `initial`, `unset` —
   permitted only because they carry no colour of their own;
3. a documented **verified gradient** combination composed solely of ratified values;
4. a documented **alpha derivative** of a ratified value, from the recorded opacity-modifier list.

Anything else fails the build.

**This audit fails on `#ff0000`, on `#123456`, on any default Tailwind palette value, on an
unauthorised alpha such as `rgba(13,27,61,0.42)`, and on an unauthorised gradient — even though
Tailwind compiled them successfully.** That is the point: compilation success is not authorisation.

**Contract for both scripts:** exit `0` with a summary line on success; exit non-zero on the first
violation, printing file, line, the offending value, and its normalised form. Both run in the
verification sequence and in the Definition-of-Done gate. Layer 2 runs **after** the production
build, so it can never be satisfied by a stale artifact.

*(No production CSS and no audit script is created during planning — this is the contract they must
satisfy when implemented.)*

### Semantic roles and permitted pairings

Every role below is a **measured observation from the reference**, not an assignment chosen here.
Contrast figures are computed from sRGB relative luminance.

| Token | Verified reference role | Permitted uses | Contrast limitation |
| --- | --- | --- | --- |
| `navy` | text ×125, bg ×40, gradient stops, border ×1 | body/heading text on light; full-bleed sections; borders; gradient stops | 16.92:1 on surface, 16.06:1 on canvas |
| `gold` | text ×54, bg ×40, border ×28, icon fill ×10, form accent ×3 | decorative accents, borders, icon fill on compliant bg, bg with compliant fg, **large** compliant text | **2.42:1 on surface, 2.30:1 on canvas — NEVER normal text there.** 6.99:1 on navy ✓ |
| `canvas` | page bg ×55 | page/section backgrounds | background role only |
| `surface` | text ×68, bg ×39, border ×9 | cards, surfaces, text on navy | 16.92:1 on navy |
| `ink` | text ×22 | body text on light surfaces | 14.68:1 / 13.93:1 |
| `muted` | text ×63, **placeholder ×1** | secondary text, **placeholder text**, resting destructive control | **4.83:1 / 4.59:1 — passes AA text** |
| `subtle` | **image-frame bg ×12**, text ×1, hover bg | image frames, dividers, inactive chips; text only on navy (14.84:1) | not text on light |
| `gold-hover` | bg ×6 (`hover:bg-[#e0b62e]`) | hover state of gold surfaces only | 8.78:1 on navy |
| `placeholder-nontext` | `placeholder-[#9CA3AF]` ×1 | **non-text only** | **2.54:1 / 2.41:1 — FAILS. Never text of any size** |
| `navy-raised` | decorative block bg, gradient stop | elevated navy surfaces, gradient stops | gold on it 5.31:1 ✓ |
| `navy-hover` | `hover:bg-[#1A2F5A]` | hover on navy surfaces | white on it 13.14:1 ✓ |
| `navy-tint` | bg ×1 | elevated navy surfaces | verify per pairing |
| `navy-deep` | `hover:bg-[#162d5e]` | hover on navy surfaces | verify per pairing |
| `line-06` | card borders ×29, divide ×1 | card/hairline borders | non-text |
| `line-08` | header + section borders ×13 | structural borders | non-text |
| `line-10` | **form-field borders ×18** | input borders | non-text; ≥3:1 where it bounds a control |
| `line-15` | secondary-button borders ×10, bg ×1 | stronger borders, overlays | non-text |
| `line-20` | border ×1 | strongest hairline | non-text |

### The two hard colour rules

- **`gold` is never normal-sized text on `surface` or `canvas`.** Where the reference does this (the
  hero eyebrow, RD-1), the eyebrow keeps its exact placement, size, weight, and `tracking-widest`
  letter-spacing, and its colour becomes `ink` or `navy`. No replacement gold is invented (FR-118,
  CID-6, CID-7).
- **`placeholder-nontext` is never text of any size, including placeholder text.** Placeholder text
  uses `muted` (FR-120, RD-13). The reference itself uses `placeholder-[#6B7280]` elsewhere, so the
  correction comes from the reference's own palette.

### Verified gradients — the only ones permitted

`from-navy via-navy to-navy`, `from-navy-raised`, `from-navy-hover`, `from-gold`, and
`to-transparent`. Any other gradient is unauthorised (FR-115, CID-5).

**Opacity modifiers** (`bg-gold/15`, `border-gold/30`, `text-surface/60`) are permitted because they
derive from a ratified token and appear in the reference. They are not new colours.

### Measured design system (from reference inspection)

| Aspect | Value |
| --- | --- |
| Container | `max-w-[1440px] mx-auto px-6 lg:px-12` — 24px gutters, 48px ≥1024px |
| Header | 72px tall, `sticky top-0 z-50`, `shadow-sm`, `border-b line-08` |
| Sticky offset | `top-[88px]` (72 + 16) for sidebar and summary panels |
| Section rhythm | `py-20` = **80px** dominant; 64/96/48px variants. **No responsive section padding in the reference** |
| Type scale in use | 10, 12, 14, 16, 18, 20, 24, 30, 36, 48, 60, 72 px — 14px carries ~50% of typed elements |
| Weights | 400, 500, 600, 700 — exactly the four self-hosted Poppins weights |
| Eyebrow | `text-sm font-semibold uppercase tracking-widest` |
| Hero headline | 48 → 60 (lg) → 72 (xl), `font-bold`, `leading-[1.1]` |
| Section heading | `text-4xl font-bold` (36px) |
| Radii | 12px controls (×68), 16px cards (×35), 24px large media (×6), pill badges (×19) |
| Elevation | Flat: `shadow-sm` + 1px `line-06` border; elevation only on hover and overlays |
| Product media | `aspect-square` on `subtle`; category tiles `aspect-[4/5]` |
| Breakpoints used | `lg:` ×58, `sm:` ×6, `md:` ×5, `xl:` ×2, `2xl:` ×0 |

---

## 5. Template and Component Strategy

One partial per component family (C-01…C-38), included everywhere it appears. No component is
duplicated between pages (Constitution IV.4, SC-005).

```text
templates/components/
  product_card.html · product_price.html · product_badge.html · gallery.html
  category_card.html · collection_card.html · section_heading.html · hero.html
  button.html · link.html · form_field.html · validation_message.html
  filter_panel.html · filter_chips.html · sort_control.html · pagination.html
  quantity_control.html · wishlist_button.html · cart_line.html · cart_summary.html
  checkout_steps.html · order_review_summary.html · enquiry_form.html
  drawer.html · dialog.html · toast.html · breadcrumbs.html
  empty_state.html · error_state.html · loading_skeleton.html
  announcement_bar.html · newsletter_cta.html · info_section.html
```

Every component receives a **view model**, never a raw object. `product_card.html` renders a
`ProductCardVM` identically on the homepage rail, listing, category, collection, search results,
wishlist, and related rail — which is what makes RF-4 and SC-006 achievable.

**Rendering the two price states.** The card branches on `price_on_request`, a pre-decided boolean.
It performs no arithmetic and has no access to a price object, so it cannot render a partial,
zeroed, or currency-less figure.

---

## 6. Routing Architecture

Stable semantic paths, resolved exclusively through named URLs (`{% url %}`); slugs from the
verified catalogue. The reference's single client-side route places no constraint here (CF-8,
FR-091). Full table in R-006.

`/` · `/products/` · `/products/<slug>/` · `/categories/<slug>/` · `/collections/<slug>/` ·
`/search/` · `/cart/` · `/wishlist/` · `/checkout/information/` · `/checkout/review/` · `/enquiry/` ·
`/about/` · `/contact/` · `/faq/` · `/privacy/` · `/terms/`

Filter, sort, and pagination state lives in the **query string** — shareable and reload-identical
(FR-021, FR-092, SC-016, SC-043).

---

## 7. Session-State Architecture

Per `contracts/session-state.md` and R-012:

- Django DB-backed sessions; opaque `HttpOnly`, `SameSite=Lax`, `Secure`-in-production cookie.
- Session stores **`{sku, qty}` pairs and validated form fields only** — never price, total, name,
  or image.
- Totals computed **only** by `CatalogProvider.resolve_lines()` at render time (FR-099). One
  routine; two surfaces cannot disagree.
- Quantity clamped server-side 1–99; unknown skus dropped silently on read, rejected on write.
- Versioned (`v`); mismatch discards rather than migrates.
- All mutations POST + CSRF + 303 redirect. Reload cannot re-submit.

**Why this satisfies "the browser is not the authority".** The client holds no cart payload at all —
not even a signed one. A tampered cookie yields an invalid session, not a modified cart. Because
prices are never stored, there is no price for an attacker to forge.

---

## 8. Search, Filter, Sort Flow

```text
GET /products/?category=…&collection=…&access=…&sort=…&page=…&q=…
      │
      ▼
ProductQuery (validated; unknown facet values dropped, not errored)
      │
      ▼
CatalogProvider.list_products()   ← filtering lives INSIDE the provider
      │
      ▼
ProductPage + FacetCounts  →  view models  →  templates
```

- Facets: OR within a family, AND across families (FR-018).
- Sort: featured, name A–Z, name Z–A. **Price and popularity sorts have no enum member**, so they
  cannot be requested (FR-017, FR-022).
- Pagination 12/page; beyond-last clamps rather than errors (FR-088).
- No-results state offers clear-filters (FR-024); an empty query does not imply a search occurred
  (FR-027).

Filtering inside the provider is what lets Feature 002 reimplement it as SQL without touching a view.

---

## 9. Accessibility Strategy

Target WCAG 2.2 AA. Spec §12 A-1…A-21 are the acceptance criteria.

**The reference cannot be copied here — it must be exceeded.** Inspection found:

| Reference finding | Requirement | Plan |
| --- | --- | --- |
| `focus:outline-none` ×16 with **no** `focus-visible:` and **zero** `ring-*` | A-4: visible focus ≥3:1 | Never remove an outline without replacing it. Global `:focus-visible` ring using `navy` on light and `gold` on navy, both ≥3:1 |
| **Zero** `motion-reduce` / `prefers-reduced-motion` | A-15 | Global `@media (prefers-reduced-motion: reduce)` disabling transitions, the `scale-105` image hover, and `animate-pulse` |
| **Zero** `aria-*` attributes in the entire bundle | A-6, A-12, A-14 | Accessible names on every icon-only control; `aria-expanded`/`aria-controls` on disclosures; `aria-live="polite"` for cart/wishlist/filter updates |
| No `fixed` positioning; no focus trap | A-13 | Drawer/dialog with focus trap, Escape dismissal, focus restoration to opener |

Additional measures: one `<main>` plus banner/nav/contentinfo landmarks; one `<h1>` per page with
non-skipping levels; skip link as first focusable element; explicit `<label>` for every field with
`aria-describedby` error wiring; 24×24 minimum targets and 44×44 for add-to-cart,
proceed-to-checkout, continue, and send-enquiry; `lang` and `dir` on `<html>`; unique descriptive
`<title>`; usable at 200% zoom.

**Verification: both automated and manual.** axe on every in-scope page *and* on each interactive
surface in its open state (drawer, dialog, filter panel, every checkout step), plus a manual keyboard
pass over the full browse → cart → checkout → review → enquiry journey. An axe pass alone is not
accessibility verification (Constitution VIII.6).

---

## 10. Performance Strategy

**Every specification budget is preserved unchanged.** PB-1…PB-19 are carried verbatim; none is
weakened to suit an architectural choice.

| Concern | Approach |
| --- | --- |
| Measurement environment | Production-mode build (`DEBUG=False`, compiled+minified assets, WhiteNoise manifest), local server, Playwright Chromium, CPU throttle 4×, Fast-3G network for cold runs |
| Representative pages | Homepage, listing, product detail, cart, checkout review, one informational page |
| Cold vs warm | Cold = cleared cache/storage; warm = second navigation with warm HTTP cache. Both recorded |
| Page weight | PB-1 ≤1200 KB home, PB-2 ≤1000 KB listing, PB-3 ≤1200 KB product, PB-4 ≤600 KB info, PB-18 ≤900 KB cart/checkout/review |
| Images | Build-time WebP q82 m6, square-normalised, `srcset` 400/800 cards and 800/1600 detail, intrinsic `width`/`height` always emitted, hero eager + `fetchpriority=high`, all others lazy |
| CSS | One compiled sheet ≤80 KB compressed (PB-7). The namespace reset removes the entire unused default palette, materially shrinking output |
| JavaScript | ≤100 KB shared (PB-5), ≤30 KB per page (PB-6). Six small modules, `type="module" defer` |
| Fonts | 4 self-hosted woff2, latin subset, `font-display: swap`, preload the two above-the-fold weights (PB-16) |
| Caching | Hashed assets immutable 1 year; HTML `no-cache` because counts are session-dependent |
| Layout stability | CLS ≤0.05 via reserved media dimensions and skeletons matching final dimensions |
| Third-party origins | **Zero** (PB-13), enforced by CSP and a network-trace assertion |
| Regression thresholds | Any budget exceeded fails verification; a >10% regression between runs is investigated before acceptance |

---

## 11. Security and Data-Safety Controls

| Threat | Control |
| --- | --- |
| Session manipulation | Server-side sessions; opaque cookie; `HttpOnly`, `SameSite=Lax`, `Secure` in prod; key cycled on privilege-relevant transitions |
| Invalid product identifiers | Every sku resolved through the port; unknown ⇒ rejected on write, dropped silently on read |
| Stale cart entries | Re-resolved every render; withdrawn products removed, counts corrected, no error |
| **Forged prices** | Price is never accepted from a request and never stored in a session. It exists only in the provider. There is no input surface to forge |
| **Client-side total tampering** | Totals computed server-side in one routine at render time; the client receives a rendered string, never a computable value |
| CSRF | Django CSRF active on every state-changing request; custom 403 template |
| Session fixation | `cycle_key()` on transitions |
| Unsafe redirects | `next` validated against an allow-list of **named routes**; arbitrary URLs are unrepresentable |
| Form validation | Server-side is the enforcement boundary; client-side is assistance only |
| Output escaping | Autoescape on; `\|safe`/`mark_safe` prohibited for visitor or catalogue values; build fails on unjustified use |
| Legacy content safety | Assets copied at build time, digest-verified, re-encoded; no legacy code executed; no runtime path into the legacy repo |
| Secrets | `django-environ`, validated at startup, fail loudly when missing; none committed |
| Logs | No credentials, no unnecessary personal data |
| Deterministic review totals | Order review recomputes from the provider; nothing read back from the session |

**Boundary audit.** An automated check fails the build if `catalog/data/`, the loader, or any
provider-internal symbol is referenced from `templates/`, `static/src/js/`, or a context processor.

---

## 12. Testing Strategy

| Layer | Tool | Coverage |
| --- | --- | --- |
| Provider contract | pytest | One suite run against **every** adapter. `DatabaseCatalogProvider` must pass the identical suite in Feature 002 |
| Loader | pytest | Schema validation, three-register join, digest pinning, fail-closed on non-null price / unapproved asset / missing source record |
| Services | pytest | Cart, wishlist, checkout, resolution; quantity clamping; stale drops; version mismatch |
| Forms | pytest | Server-side validation, field errors, first-invalid-field, value preservation |
| Views | pytest-django | Status codes, redirects, 404/405/403, review-state gating |
| Templates | pytest-django | Rendering against a **fake provider**, proving provider-agnosticism |
| View models | pytest | `price_display is None` whenever `price_on_request`; `supplier_line` never empty; image dimensions always present |
| E2E + JS behaviour | Playwright | Every user story's Independent Test; cart/wishlist persistence across 5 navigations + reload; drawer/gallery/filters |
| No-JavaScript | Playwright (JS disabled) | Full browse → cart → checkout → review → enquiry journey |
| Accessibility | axe + manual | Every page and every open interactive surface; manual keyboard pass |
| Audits | Playwright + scripts | Source colour, rendered colour, contrast, boundary, template-attribute, content integrity, console errors, broken links, responsive overflow |
| Fault injection | pytest | Enquiry write failure ⇒ no confirmation (SC-023) |
| Stored-state inspection | pytest | After a full journey: zero order records, zero order numbers (SC-044) |
| Build | CLI | Production asset build succeeds with no unresolved reference |

**Test-first.** Provider contract, loader validation, service, and form tests are written and failing
before their implementation (Constitution XII).

---

## 13. Visual QA Strategy

**Two complete critique-and-correction passes** over all affected pages (Constitution XIII.3), not
the homepage alone.

Screenshots at **1440 / 1024 / 768 / 390** for: homepage, listing (unfiltered, filtered,
no-results), category, collection, search (results, no-results), product detail (multi-image,
single-image), cart (populated, empty), checkout information (clean, invalid), order review,
wishlist (populated, empty), About, Contact, FAQ, 404, 500 — plus **state** captures for mobile nav
open, filter drawer open, dialog open, toast visible, focus-visible on each control family, loading
skeletons, and reduced-motion.

Each pass records, per page and per width: colour accuracy against the token table, palette drift
versus the homepage, spacing rhythm and hierarchy, product-card proportions, typography character,
navigation coherence, overflow and clipping, keyboard interaction, focus visibility, console errors,
and broken navigation.

**Screenshots are inspected, and the observations are written down.** Capturing without inspecting
is not visual QA (Constitution XIII.6, SC-007).

**Acceptance is not "similar to" the reference.** It is: equivalent hierarchy, density, and rhythm;
identical component language across pages; colours resolving to the ratified 18; and the thirteen
documented reference defects **absent**.

### Deviation Ledger (Constitution I.2 / RF-10) — consolidated, 2026-08-01

Every divergence between the implementation and the approved reference is recorded here with its
source conflict, decision, authority, consequence, verification, and final status. **No deviation is
ambiguous and none is deferred to task generation.**

---

**DEV-1 — Product-card grid responsive matrix (all four widths)** · **Status: DECISION CLOSED —
specification corrected (2026-08-01)**

| Field | Value |
| --- | --- |
| Source conflict | Spec §8 originally ratified **4 / 3 / 2 / 1** across 1440 / 1024 / 768 / 390. The reference renders `grid grid-cols-2 lg:grid-cols-4`, whose `lg:` breakpoint is 1024px — i.e. **4 / 4 / 2 / 2**. The conflict existed at **two** widths (1024px and 390px), not one |
| Affected artifacts | spec §8 row, spec §8.1 matrix, FR-121, SC-051, US2.8, NFR-008, RF-3, plan §4 and §13, research R-020, quickstart audit + visual-QA, traceability |
| Decision | **Preserve the reference at every acceptance width**: 4 at 1440px, 4 at 1024px, 2 at 768px, 2 at 390px; may degrade to 1 below 390px only to prevent overflow. Applies to product-card listing grids only |
| Authority | The established authority already requires preserving the reference's responsive visual behaviour (Constitution I.1, spec §11 RF-3). The specification has been corrected to match, so this is **no longer a spec-vs-reference conflict at any width** |
| Implementation consequence | Listing/category/collection/search/related grids follow the matrix under CG-1…CG-7 **at every width**: no overflow; 1:1 media preserved; targets ≥24×24 (44×44 primary); name wraps to 2 lines with accessible full text; **attribution and price statement never truncated**; body text ≥12px. **Not** applied to forms, checkout fields, informational layouts, dialogs, drawers, filter panels, cart lines, wishlist rows, product rails, or category tiles (`4:5` retained) |
| Verification | Grid-column audit at all four widths + SC-008 overflow audit + SC-013 target audit + US2.8; inspected at **all four widths** in **both** visual critique passes |
| Decision status | **CLOSED — specification corrected.** No responsive decision remains open at any width |
| Implementation status | Pending — implementation has not started |

*A single identifier is retained deliberately: this is the same product-grid conflict recorded at
DEV-1, now resolved across all four widths. Creating a second identifier would record one conflict
twice.*

---

**DEV-2 — Pinned bottom action bars at 390px** · **Status: DECISION CLOSED — accepted improvement;
implementation pending**

*(Omitted from the previous final report; recorded in full here.)*

| Field | Value |
| --- | --- |
| Source conflict | Spec §8 requires the add-to-cart / primary action pinned to the bottom at 390px on product detail, cart, and checkout. The reference uses **no `fixed` positioning anywhere** — 0 occurrences — so it has no pinned bar and no fixed mobile CTA |
| Affected artifacts | spec §8 rows (product detail, cart, checkout), plan §5 components, A-11 |
| Decision | **Add** pinned bottom action bars at 390px on those three surfaces |
| Authority | Ratified spec §8 (authority order 2, above the reference at 3). Constitution I.2 permits a creative improvement that demonstrably improves usability, recorded with its reason |
| Implementation consequence | A pinned container at narrow widths only; must not overlap content (spec §8 "no floating-control overlap"), must reserve its own height so nothing is obscured, must not trap focus, and must meet the 44×44 primary-action target |
| Verification | Responsive e2e at 390px asserting no overlap and no obscured content; target-size audit; manual keyboard pass confirming reachability; inspected in both critique passes |
| Decision status | **CLOSED — accepted improvement.** Recorded permanently under Constitution I.2; not a defect and not revisitable at task generation |
| Implementation status | Pending — implementation has not started |

---

**DEV-3 — Visible focus indicators** · **Status: DECISION CLOSED — rejected reference defect;
corrective implementation pending**

| Field | Value |
| --- | --- |
| Source defect | Reference applies `focus:outline-none` **16 times** with **zero** `focus-visible:` and **zero** `ring-*` utilities. Focus is signalled only by a border-colour change |
| Affected artifacts | plan §4 tokens, §9 accessibility, A-4, NFR-017, SC-012 |
| Decision | **Reject the reference behaviour.** Never remove an outline without replacing it. Global `:focus-visible` ring — `navy` on light surfaces, `gold` on navy — both ≥3:1 |
| Authority | Constitution I.4 (a reference defect MUST NOT be reproduced) + spec A-4 |
| Implementation consequence | A focus-ring utility applied globally; no component may set `outline-none` without an accompanying visible indicator |
| Verification | Focus-indicator contrast audit (SC-012); axe; manual keyboard pass recording focus visibility at every stop |
| Decision status | **CLOSED — permanently rejected reference defect.** Never to be reproduced; not revisitable at task generation |
| Implementation status | Corrective implementation pending — implementation has not started |

---

**DEV-4 — Reduced-motion support** · **Status: DECISION CLOSED — rejected reference defect;
corrective implementation pending**

| Field | Value |
| --- | --- |
| Source defect | `motion-reduce`, `motion-safe`, and `prefers-reduced-motion` all return **0 occurrences** in the reference bundle. No reduced-motion handling of any kind exists |
| Affected artifacts | plan §9, A-15, NFR-020 |
| Decision | **Reject the omission.** Global `@media (prefers-reduced-motion: reduce)` suppressing transitions, the `group-hover:scale-105` image zoom, and `animate-pulse` |
| Authority | Constitution I.4 + spec A-15 |
| Implementation consequence | One media block in `tokens.css`/base styles; components need no individual handling |
| Verification | Playwright run with reduced-motion emulation asserting suppressed animation; reduced-motion screenshot captured and inspected |
| Decision status | **CLOSED — permanently rejected reference defect.** Never to be reproduced |
| Implementation status | Corrective implementation pending — implementation has not started |

---

**DEV-5 — ARIA names, states, and live regions** · **Status: DECISION CLOSED — rejected reference
defect; corrective implementation pending**

| Field | Value |
| --- | --- |
| Source defect | The reference bundle contains **zero `aria-*` attributes**. Icon-only controls have no accessible name; disclosures expose no state; dynamic updates announce nothing |
| Affected artifacts | plan §9, A-6, A-12, A-14, NFR-024 |
| Decision | **Reject the omission.** Accessible names on every icon-only control; `aria-expanded`/`aria-controls` on disclosures; `aria-live="polite"` for cart, wishlist, and filter updates |
| Authority | Constitution I.4 + spec A-6, A-12, A-14 |
| Implementation consequence | Component-level attributes carried by the shared partials, so each is authored once |
| Verification | axe on every page and every open interactive surface; manual keyboard and screen-reader spot check; SC-010, SC-011 |
| Decision status | **CLOSED — permanently rejected reference defect.** Never to be reproduced |
| Implementation status | Corrective implementation pending — implementation has not started |

---

**DEV-6 — Responsive section padding below 768px** · **Status: DECISION CLOSED — accepted
improvement; implementation pending**

*(Omitted from the previous final report; recorded in full here.)*

| Field | Value |
| --- | --- |
| Source conflict | The reference uses a flat `py-20` (80px) vertical section rhythm at **every** width — it contains **no responsive section padding at all** (no `md:py-*` or `lg:py-*`). At 390px an 80px band consumes ~20% of the viewport height |
| Affected artifacts | plan §4 measured design system, spec §8, RF-2 (section rhythm) |
| Decision | **Permit** reduced section padding below 768px, on the ratified spacing scale |
| Authority | Constitution I.2 — a creative improvement that demonstrably improves usability, recorded with its reason. Spec §8 requires a deliberate layout decision per width, which a flat value is not |
| Implementation consequence | Section padding becomes a responsive token step rather than a constant. **The desktop rhythm at 1440/1024 is unchanged**, so RF-2's density comparison against the reference is unaffected at the widths where it is judged |
| Verification | RF-2 rhythm comparison at all four widths in both critique passes; visual QA confirms density character is preserved, not thinned |
| Decision status | **CLOSED — accepted improvement.** Recorded permanently under Constitution I.2 |
| Implementation status | Pending — implementation has not started |

---

### Ledger summary

**Every deviation decision is CLOSED.** Implementation remains pending for all of them, because
implementation has not started. Decision status and implementation status are two different facts,
and are reported separately here so neither is mistaken for the other.

| Deviation | Kind | **Decision status** | Implementation status |
| --- | --- | --- | --- |
| DEV-1 | Spec-vs-reference conflict, product-grid matrix | **CLOSED — specification corrected** | Pending |
| DEV-2 | Accepted improvement over the reference | **CLOSED — accepted improvement** | Pending |
| DEV-3 | **Rejected reference accessibility defect** | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-4 | **Rejected reference accessibility defect** | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-5 | **Rejected reference accessibility defect** | **CLOSED — rejected reference defect** | Corrective implementation pending |
| DEV-6 | Accepted improvement over the reference | **CLOSED — accepted improvement** | Pending |

**Zero deviation decisions remain open. Zero are deferred to task generation.**

**DEV-3, DEV-4, and DEV-5 are reference deficiencies, not behaviour to reproduce.** They sit
alongside the catalogued defects RD-1…RD-13 and are governed by the same rule: Constitution I.4
forbids reproducing a reference defect. They require no specification amendment, because A-4, A-15,
A-6, A-12, and A-14 already mandate the correct behaviour.

**The previously recorded 1024px divergence is now resolved.** An earlier revision noted that the
spec specified 3-across at 1024px while the reference renders 4-across. That divergence has been
closed by correcting the specification to the reference's matrix (4 / 4 / 2 / 2), and is folded into
DEV-1 rather than carried as a separate identifier. **No residual responsive divergence remains at
any acceptance width.**

---

## 14. Implementation Phases

| Phase | Content | Gate |
| --- | --- | --- |
| **P0 Foundation** | Django project, settings, env validation, SQLite, WhiteNoise, base URLs, custom 404/500/403 | `manage.py check` clean |
| **P1 Token authority + shell** | `tokens.css` with the namespace reset and 18 values, fonts, icon sprite, base template, header/footer/announcement/skip link | Colour-source audit passes; no default utility compiles |
| **P2 Catalogue** | Copy + digest-pin the 3 registers, loader with fail-closed validation, read models, port, static provider, contract suite | Contract suite green; fail-closed proven |
| **P3 Assets** | Image normalisation to square on `subtle`, WebP renditions, derived alt text, asset manifest | Manifest complete; no upscaling; ratios uniform |
| **P4 Discovery** | Home, listing, category, collection, search, filters, sort, pagination, product card | Facet precision; URL round-trip |
| **P5 Product detail** | Gallery, specifications, attribution, related, price-on-request, add-to-cart | Single-image path renders no controls |
| **P6 Session state** | Cart, wishlist, services, counts, drawer, persistence | 5-navigation + reload persistence |
| **P7 Checkout** | Information steps, validation, review state, digest guard, disclosure | Review unreachable unless validated |
| **P8 Enquiry** | `Enquiry` model + migration, forms, submission, confirmation | Success only after commit; fault injection |
| **P9 Informational** | About, Contact, FAQ; Privacy/Terms only if verified text is supplied, else removed with their links | Zero dead links |
| **P10 Accessibility + performance** | Focus rings, reduced motion, ARIA, budgets, lazy loading | axe zero; budgets met |
| **P11 Verification** | Full Phase V of the tasks template | All checks recorded with exact commands and results |
| **P12 Visual QA** | Two critique-and-correction passes | Observations recorded per page per width |

---

## 15. Migration Path to Feature 002

| Step | Action | Cost |
| --- | --- | --- |
| 1 | Add `psycopg`, point `DATABASE_URL` at PostgreSQL | Dependency assessment under III.4 |
| 2 | Model the catalogue from the Tier A read-model field names | New app |
| 3 | Implement `DatabaseCatalogProvider` | Must pass the **existing** contract suite |
| 4 | One-time import of the governed registers | Management command |
| 5 | Flip `ZAKEY_CATALOG_PROVIDER`; delete the static adapter and its data | **One setting** |
| 6 | Supply verified prices | `Totals.computable` flips to `True`; priced surfaces activate |
| 7 | Attach order creation **after** the review state | Review is the seam |

**Unchanged in Feature 002:** every template, route, view model, component, token, and the cart,
wishlist, checkout, and review flows.

---

## 16. Constitution Check — Initial Gate (before Phase 0)

| # | Principle / gate area | Status | Evidence |
| --- | --- | --- | --- |
| I | Reference-led visual fidelity | **Pass** | §13 names pages, widths, threshold, method; RD-1…RD-13 corrected; DEV-1…DEV-6 documented |
| II | Design-token authority | **Pass** | §4 — one `tokens.css`, 18 values, namespace reset makes drift non-compiling |
| III | Approved technical foundation | **Pass** | §1 — zero new dependencies; no SPA, no CDN |
| IV | Architecture boundaries | **Pass** | §2, §3, §5 — layered; one component per family; six focused JS modules |
| IV.7–IV.8 | Shared data authority | **Pass** | C-CATALOG single port; no template hardcodes a record |
| IV.9 | Localization / RTL readiness | **Pass** | i18n `message_key` throughout; logical properties; no language selector |
| V | Content and asset truth | **Pass** | R-001 fail-closed validation; R-017 derived alt marked as derived; R-018 Tier-G recorded; asset manifest |
| VI | Functional completeness | **Pass** | C-HTTP progressive enhancement; no dead controls; one totalling routine; no payment fields; no order action |
| VII | Responsive behavior | **Pass** | Spec §8 layouts; overflow assertion at 4 widths |
| VIII | Accessibility | **Pass** | §9 — automated **and** manual; reference deficiencies explicitly exceeded |
| IX | Performance budgets | **Pass** | §10 — all budgets preserved, none weakened |
| X | Security and data safety | **Pass** | §11 — full threat table |
| XI | Specification-first | **Pass** | No requirement redefined; boundary respected; traceability.md |
| XII | Test strategy | **Pass** | §12 — categories named; exclusions justified in §17 |
| XIII | Visual QA | **Pass** | §13 — two passes, inspected screenshots, cross-page comparison |
| XIV | Code quality | **Pass** | Guard skills scheduled in P11; migrations reviewed |
| XV | Git safety | **Pass** | Branch in use; no Git operation performed by planning; ignore policy in place |
| XVI | Claude governance | **Pass** | Opus is lead; two bounded read-only agents used; all artifacts written by the lead |
| XVII | LeanCtx / context discipline | **Pass** | Targeted inspection; all evidence written into artifacts |
| — | Implementation boundaries | **Pass** | §15 + spec §19 |
| XVIII | Definition of Done | **Pass** | All fifteen conditions reachable via P11–P12 |

**Blocking violations: none.**

## 16b. Constitution Check — Post-Design Re-check (after Phase 1)

Re-run after `research.md`, `data-model.md`, and `contracts/` were complete. Design work changed
five things; each was re-checked.

| Change introduced by design | Principle at risk | Re-check outcome |
| --- | --- | --- |
| Catalogue is **three** registers, not one (R-001) | IV.7 "exactly one adapter" | **Pass** — still one adapter and one port. The three files are inputs to one loader, not three data paths. Templates see no change |
| One Django model (`Enquiry`) introduced | VI.4, XI.9 boundary | **Pass** — required by CL-2 ("persist to a real store; success only on confirmed write"). It is not an order, account, or inventory record; §15 keeps it inside the boundary |
| Product ratio corrected 4:5 → **1:1** (R-010) | I, RF-4, RF-6 | **Pass** — corrected *toward* the reference, which uses `aspect-square` for all product media. The earlier draft was the deviation |
| Reference lacks focus rings, reduced motion, ARIA | VIII | **Pass with documented deviations** DEV-3/4/5 — the reference is exceeded, not copied. Principle I.4 requires defects not be reproduced |
| Spec §8 and the reference disagree on the 390px grid | I vs XI | **Pass with DEV-1** — authority order puts the clarified specification above the reference; recorded under RF-10 |

**Blocking violations after design: none.**

### Blocking Violations

| Violation | Principle | Why it blocks | Resolution or approved exception |
| --- | --- | --- | --- |
| *(none)* | — | — | — |

### Dependency Assessment (Constitution III.4)

**No new dependency is introduced by this plan.** Every tool is already installed and
version-verified (§1). `psycopg` is deliberately deferred to Feature 002, where it will require its
own III.4 assessment.

---

## 17. Complexity Tracking

| Item | Why needed | Simpler alternative rejected because |
| --- | --- | --- |
| Two insulation layers (port **and** view models) | Templates must survive the Feature 002 swap unchanged | A port alone still lets provider types shape templates, so the swap would still reshape every template |
| Three-register loader | The catalogue carries no image metadata and no specification values | Loading only the catalogue yields products with no images and no specifications |
| Build-time image normalisation | Source ratios span 0.54–1.33 and reach 7.4 MB | Serving sources as-is breaks RF-4, NFR-011, and every page-weight budget |
| Colour-namespace reset | Palette governance is binding, not advisory | Review-only enforcement is the control the user explicitly rejected |

### Justified test exclusions (Constitution XII.2)

| Excluded | Justification |
| --- | --- |
| Permission tests | No authentication or authorisation exists in Feature 001 (deferred to Feature 003) |
| Model tests beyond `Enquiry` | `Enquiry` is the only model; catalogue read models are covered by loader and contract tests |
| Separate JS unit runner | No JS test runner is installed and adding one is a forbidden dependency change; Playwright covers the same behaviour in a real browser, which is stronger evidence |
| Lighthouse CI | Not installed; PB-8/9/10 measured via Playwright performance APIs with the method recorded |

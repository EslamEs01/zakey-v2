# Phase 0 Research: ZAKEY Premium Public Storefront Experience

**Feature**: `001-premium-storefront-experience`
**Date**: 2026-07-31
**Constitution**: v1.1.0
**Status**: All technical unknowns resolved — zero open placeholders

Every decision below was verified against the actual installed toolchain in this repository or
against the authoritative sources named in the specification. Where a claim could not be verified,
it is stated as unverified rather than asserted.

**Verification baseline captured 2026-07-31:**

| Component | Installed version | How verified |
| --- | --- | --- |
| Python | 3.12.3 | `.venv/bin/python --version` |
| Django | 5.2.16 | `import django; django.get_version()` |
| django-environ, whitenoise, Pillow | present | import check |
| pytest / pytest-django | 9.1.1 / present | import check |
| Tailwind CSS + `@tailwindcss/cli` | 4.3.3 | `node -p require(...).version` |
| Playwright | 1.62.1 | as above |
| `@axe-core/playwright` | 4.12.1 | as above |
| `@fontsource/poppins` | 5.3.0 (woff2 400/500/600/700 latin present) | file listing |
| lucide | 1.28.0 | as above |
| Prettier | 3.9.6 | as above |
| psycopg | **ABSENT** | `import psycopg` → ModuleNotFoundError |

---

## R-001 — Temporary verified-content representation

**Decision.** A **versioned, checksum-pinned snapshot of three governed JSON registers**, copied out
of the legacy repository into `storefront/catalog/data/`, loaded exactly once at application startup
by a validating loader into **frozen dataclass read models**. Never a Django model, never a fixture,
never a migration, never touched by a template.

**Correction — the dataset is three files, not one.** Deep inspection established that the catalogue
alone is insufficient:

| File | Size | Role |
| --- | --- | --- |
| `curated-launch-catalog.v2.json` | 53 KB | 21 products; identity, taxonomy, provenance, commerce mode, media *pointers*, and the specification-field *allowlist* |
| `product-media-register.v2.json` | 100 KB | 49 asset definitions (25 approved for launch): `original_path`, `sha256`, `format`, `mime_type`, `dimensions.width_px/height_px`, `alpha`, `rights_status`, `publication_status` |
| `product-source-register.v1.json` | 706 KB | 209 source records keyed by `source_record_id`; holds the **values** for the five allowlisted specification fields, each as `{raw_value, normalized_value, source_page_pdf}` |

The catalogue carries **no image metadata and no specification values** — only `media_assignments`
(`{media_asset_id, roles[card|detail|homepage_slider], sort_order}`) and
`approved_source_specification_fields` (field *names* only). A loader reading just the catalogue
would render products with no images and no specifications. The loader therefore **joins all three
registers at boot** and fails closed if a referenced `media_asset_id` or `source_record_id` is
missing, or if an asset is not `publication_status: approved_curated_launch_public`.

**Verified structural facts.** Each product object has exactly 40 keys, all present on all 21
products, with `additionalProperties: false`. The schema types `retail_price` and `currency` as
`"type": "null"`, and caps `certifications`/`payment_methods` at `maxItems: 0` — so a non-null price
is not merely absent, it is **schema-invalid**. `discount`, `stock`, `warranty`, `delivery_time`,
`installation_sla`, `compatibility`, `market_country`, `tax`, `shipping`, `urgency_claim`, and
`popularity_claim` are likewise null on all 21. Publishing any such claim would require corrupting
the governed dataset, which the boot-time schema validation rejects.

**Rationale.**
- *Uses only verified legacy data* — it is a byte-for-byte copy of the governed dataset, with its
  SHA-256 recorded in an asset manifest so drift is detectable.
- *Preserves identity and provenance* — every field including `supplier_brand`,
  `supplier_relationship`, `source_document`, `source_model_code`, and `identity_grounding` is
  carried through into the read model, so provenance cannot be lost in transit (FR-111, FR-112).
- *Prohibits invented claims structurally* — the loader **rejects at boot** any product carrying a
  price **without verified provenance**. Inventing a price crashes the application rather than
  reaching a page. **A properly provenanced verified price is accepted normally and never causes a
  failure** — the rule discriminates on provenance, not on presence. The complete fail-closed list is
  FC-1…FC-9 in `contracts/catalog-provider.md`.
- *Current price state, measured 2026-08-01* — **no launch product has any price value.** All 21
  carry `retail_price: null`, `currency: null`, and `source_price_raw/_min/_max/_currency: null`; the
  sole non-null price field is the label `source_price_kind: "supplier_reference"`. Elsewhere in the
  source register 88 of 209 records do carry USD amounts, all classified `supplier_reference` and
  none belonging to a launch product — and `source_price_*` is not on the publish allowlist in any
  case. **The launch catalogue is enquiry-only, and the governed source inventory is exactly three
  artifacts.** No verified-price artifact exists; one is specified only as a controlled future
  extension.
- *Deterministic and testable* — a static file with a pinned digest yields identical read models on
  every run, so tests and screenshots are reproducible.
- *Not a shadow production database* — it is read-only, in-memory, has no writer, no admin, no
  migration, and no query language. Nothing can mutate it at runtime.
- *Replaceable in Feature 002* — it sits behind the `CatalogProvider` port (R-002); swapping in a
  database-backed adapter changes one factory binding.
- *Separate from presentation* — templates receive view-model dataclasses, never the JSON.

**Alternatives considered and rejected.**

| Alternative | Rejected because |
| --- | --- |
| Django models + fixtures loaded into the dev database | Becomes exactly the "shadow production database" the specification forbids. It also invites Feature 002's schema decisions to be made early and badly, and makes the catalogue mutable through the admin. |
| Python module of literal dataclasses | Hardcodes catalogue content into source code, making provenance and diffing against the governed dataset far harder, and tempting hand-edits that break verifiability. |
| Reading the legacy JSON directly from `/media/mekky/work/backend/zakey.v1/...` at runtime | Couples this repository's runtime to an external read-only repository, breaks clean-room self-containment (Constitution IV), and would fail in any environment where the legacy checkout is absent. |
| Django `fixtures/` + `loaddata` | Same shadow-database objection, plus fixture format loses the provenance fields that are not model fields. |
| SQLite file shipped as data | A database by another name; mutable, opaque to review, and not diffable. |

**Impact on Feature 001.** Catalogue reads are O(1) dictionary lookups from memory — no query
budget, no N+1 risk, and page-weight budgets are unaffected by data access.

**Impact on Feature 002 readiness.** The dataset's field names become the read-model field names,
which become the eventual model field names. Feature 002 writes a `DatabaseCatalogProvider`
satisfying the same port, migrates the JSON into models once, and deletes the static provider. No
template, route, view, or contract changes.

---

## R-002 — Catalog provider boundary

**Decision.** A **port-and-adapter boundary**: an abstract `CatalogProvider` interface declaring
every read operation the storefront needs, with `StaticCatalogProvider` as the Feature 001 adapter
and a future `DatabaseCatalogProvider` as the Feature 002 adapter. Views depend on the interface
only, resolved through a single factory reading one Django setting
(`ZAKEY_CATALOG_PROVIDER`). The full contract is specified in `contracts/catalog-provider.md`.

**Rationale.** Constitution IV.7 requires exactly one documented adapter for temporary storefront
data, and the specification requires the source to be replaceable without rewriting public
templates. A port with a settings-driven factory makes the swap a one-line configuration change and
makes "did a template reach past the boundary?" a mechanically checkable question.

**Alternatives considered and rejected.**

| Alternative | Rejected because |
| --- | --- |
| Module-level functions imported directly by views | No seam to substitute in Feature 002 or in tests; every view would import the concrete implementation. |
| Django model managers from the start | Requires the production catalogue database in Feature 001, which the direction explicitly forbids. |
| Template context processors exposing raw catalogue data | Puts data access in the template layer, the exact coupling the specification prohibits. |
| A generic repository with a query-builder API | Over-engineered; a query language leaks storage semantics into callers and makes the Feature 002 swap harder, not easier. |

**Impact on Feature 001.** Every view is testable against an in-memory fake provider with three
products, making view and template tests fast and independent of the real dataset.

**Impact on Feature 002 readiness.** The port is the migration contract. Feature 002 is complete for
catalogue purposes when `DatabaseCatalogProvider` passes the same contract test suite.

---

## R-003 — Design-token authority and palette enforcement

**Decision.** **Tailwind CSS v4 CSS-first theming**, with one file —
`storefront/static/src/css/tokens.css` — as the single token authority, opening with a **full
colour-namespace reset**:

```css
@import "tailwindcss";

@theme {
  --color-*: initial;   /* removes EVERY default Tailwind colour utility */
  /* the 18 governed values are then declared here, and only here */
}
```

**Rationale — this converts palette governance from a review promise into a build-time guarantee.**
Tailwind v4 declares its default palette as `@theme default { --color-red-500: … }` theme
variables. Resetting the `--color-*` namespace deletes them, so `bg-red-500`, `text-gray-200`,
`bg-green-500`, `bg-blue-900` and every other unauthorised colour utility **compile to nothing**.
An implementer cannot accidentally introduce an off-palette colour through a utility class; the
class simply does not exist. This directly enforces CID-2, CID-5, FR-115, and FR-116.

**Verified, not assumed.** Confirmed against the installed Tailwind 4.3.3: `node_modules/
tailwindcss/index.css` opens `@theme default { … --color-red-500: oklch(…) … }`, and the compiler
dist exports a `clearNamespace` symbol implementing the `--namespace-*: initial` reset. A
`tailwind.config.js` is absent, confirming v4 CSS-first configuration is the correct surface.

**Empirically proven, not asserted — probe run 2026-08-01.** An isolated probe was compiled with the
repository's own installed `tailwindcss@4.3.3` CLI, from a scratch directory **outside the
repository**, installing nothing and touching no dependency or lockfile. Input: the reset plus the 18
governed values; content: a file exercising default utilities, governed utilities, arbitrary
literals, and non-colour utilities.

Result — compiled output 7,711 bytes:

| Probe class | Utilities tested | Compiled? |
| --- | --- | --- |
| Default Tailwind colours | `bg-red-500`, `text-gray-200`, `bg-green-500`, `text-blue-700`, `bg-gray-900`, `border-slate-300` | **No — 0 occurrences of any** |
| Default palette values | any `oklch(…)` from the built-in theme | **No — 0 occurrences** |
| Governed tokens | `.bg-navy`, `.text-gold`, `.border-line-10`, `.bg-subtle`, `.text-muted`, `.bg-gold-hover` | **Yes — all six emitted** |
| Non-colour utilities | `.flex`, `.grid`, `.p-4`, `.rounded-xl`, `.shadow-sm` | **Yes — unaffected by the reset** |
| Arbitrary literals | `.bg-[#ff0000]`, `.text-[#123456]` | **Yes — these still compile** |

Only the theme variables for tokens actually used were emitted, confirming the reset replaced the
namespace rather than merely shadowing it.

**Residual gap, now measured rather than assumed.** The reset does **not** stop an arbitrary value
(`bg-[#ff0000]`, proven above) or a raw `style="color:…"`. This is precisely why the source-colour
audit (R-011, control 2) is a genuine requirement and not belt-and-braces: it is the only control
that closes the arbitrary-literal path. The two controls are complementary — the reset makes named
off-palette colours **unrepresentable**, and the audit makes literal off-palette colours
**detectable**.

**Alternatives considered and rejected.**

| Alternative | Rejected because |
| --- | --- |
| Tailwind v3 `tailwind.config.js` theme | Not the installed version; would require a downgrade, i.e. a dependency change, which is forbidden. |
| Keep Tailwind defaults and rely on code review to catch off-palette colours | Review is the weakest possible control for a rule the user has made binding. The whole point of CID-5 is that drift must be impossible, not merely discouraged. |
| Hand-written CSS custom properties without Tailwind | Discards the utility ergonomics the reference itself is built on and makes reference fidelity harder to achieve and to compare. |
| CSS-in-JS or runtime theming | Adds runtime JavaScript for something that is a build-time constant, and breaks the no-CDN/no-runtime-dependency constraints. |

**Impact on Feature 001.** Palette drift is largely unrepresentable. Contrast pairings are
declarable once, in one file, and audited once.

**Impact on Feature 002 readiness.** New commerce surfaces inherit the same token authority; no
palette work is repeated.

---

## R-004 — Session state backend

**Decision.** Django's **database-backed session engine**
(`django.contrib.sessions.backends.db`), storing in the session **only** product identifiers,
quantities, and validated form input — **never prices, never totals, never product names**. The
client holds nothing but an opaque, `HttpOnly`, `SameSite=Lax`, `Secure`-in-production session
cookie.

**Rationale.** The security requirement is explicit: the browser must not be the authority for
price, product identity, totals, or validation. A database session keeps all state server-side and
gives the client no readable or forgeable payload. Prices and totals are recomputed on every render
from the catalogue provider, so a stale or tampered session can never produce a wrong total — at
worst it references a product that no longer exists, which is handled by the stale-line rule
(FR-101).

**Alternatives considered and rejected.**

| Alternative | Rejected because |
| --- | --- |
| `signed_cookies` backend | Puts cart contents in the client. The payload is signed (tamper-evident) but **base64, not encrypted** — product identities and quantities become client-readable, and the browser becomes the carrier of record for cart state. Also capped near 4 KB, which a multi-line cart with address data can approach. Rejected on the security requirement, not on capacity. |
| `cache` backend (locmem/Redis) | Sessions evaporate on restart or eviction, so "cart survives navigation and reload" (FR-094, SC-035) would be flaky rather than guaranteed. Redis would also be a new dependency. |
| `cached_db` | Sound in production, but adds a cache dependency for no Feature 001 benefit. Recorded as the natural Feature 002/007 upgrade path. |
| Client-side storage (`localStorage`) for cart | Makes the browser the authority for product identity and quantity — directly prohibited — and breaks server-rendered progressive enhancement. |

**Impact on Feature 001.** Requires a database for Django infrastructure only (sessions, contrib
migrations). See R-005. Session writes happen only on mutation, so read-heavy browsing does not
touch the session store.

**Impact on Feature 002 readiness.** When real orders arrive, the session cart is the input to order
creation; the session schema versioning rule (`ZAKEY_CART_SCHEMA_VERSION`, R-012) lets Feature 002
change the shape without stranding live sessions.

---

## R-005 — Database posture in Feature 001

**Decision.** **SQLite for local development** (gitignored), configured through
`django-environ`'s `DATABASE_URL` so PostgreSQL is a configuration change, not a code change. The
**catalogue is not in the database at all**. The only tables are Django's own contrib tables —
sessions, content types, and (unused but migrated) auth scaffolding.

**Rationale.** The direction requires "PostgreSQL-ready domain boundaries without requiring the
production catalog database in Feature 001". Sessions need durable storage (R-004); the catalogue
does not. `psycopg` is verified **absent** from the environment, and installing it would violate the
no-dependency-change constraint — so PostgreSQL readiness in Feature 001 means *settings and domain
boundaries are ready*, not *PostgreSQL is running*.

**Explicitly recorded for Feature 002:** adding `psycopg[binary]` is a Feature 002 dependency
decision, to be assessed under Constitution III.4 at that time. Feature 001 does not add it.

**Alternatives considered and rejected.**

| Alternative | Rejected because |
| --- | --- |
| Require PostgreSQL in Feature 001 | Needs a dependency install (forbidden here) and a running service for a feature that stores no domain data. |
| No database at all (cookie sessions) | Rejected in R-004 on security grounds. |
| SQLite committed to the repository | Databases must not be committed (Constitution XV.6); `.gitignore` already excludes `db.sqlite3` and its `-wal`/`-shm`/journal sidecars. |

---

## R-006 — Routing architecture

**Decision.** **Stable, semantic, human-meaningful paths** resolved exclusively through named
Django URLs (`{% url %}`), with slugs from the verified catalogue. The reference's single
client-side route places no constraint here (CF-8, FR-091).

| Route name | Path | Notes |
| --- | --- | --- |
| `home` | `/` | |
| `catalog:product_list` | `/products/` | filters, sort, page via query string |
| `catalog:category_detail` | `/categories/<slug:slug>/` | 3 verified categories |
| `catalog:collection_detail` | `/collections/<slug:slug>/` | 6 verified collections |
| `catalog:product_detail` | `/products/<slug:slug>/` | 21 verified products |
| `catalog:search` | `/search/` | `?q=` |
| `cart:detail` | `/cart/` | |
| `cart:add` / `update` / `remove` | `/cart/add/` etc. | POST only |
| `wishlist:detail` | `/wishlist/` | |
| `wishlist:toggle` | `/wishlist/toggle/` | POST only |
| `checkout:information` | `/checkout/information/` | |
| `checkout:review` | `/checkout/review/` | terminal validated state |
| `enquiry:create` | `/enquiry/` | POST; the only state-changing terminal action |
| `pages:about` / `contact` / `faq` | `/about/`, `/contact/`, `/faq/` | |
| `pages:privacy` / `terms` | `/privacy/`, `/terms/` | rendered only when verified legal text exists (FR-070) |

Filter, sort, and pagination state lives in the **query string**, satisfying FR-021, FR-092, SC-016
and SC-043 — a filtered listing is shareable and reloads identically.

**Rationale.** Semantic paths are stable public contracts; slugs from verified data avoid inventing
identifiers; query-string state is inherently shareable and requires no JavaScript.

**Alternatives considered and rejected.** ID-based paths (`/products/17/`) — opaque, unfriendly, and
leak internal ordering. Hash-based or client-routed URLs — copy the reference's prototype
limitation and break no-JavaScript operation. Session-stored filter state — makes a listing
unshareable, failing SC-016 and SC-043 outright.

---

## R-007 — Frontend asset pipeline

**Decision.** **Tailwind v4 CLI compiles a single stylesheet**; **native ES modules** provide
behaviour; **WhiteNoise with a manifest storage** serves hashed static files. No bundler, no
framework, no CDN.

- CSS: `npx @tailwindcss/cli -i storefront/static/src/css/app.css -o storefront/static/css/app.css --minify`
- JS: hand-authored ES modules under `storefront/static/src/js/`, loaded with `<script type="module" defer>`, one small module per behaviour (`cart.js`, `wishlist.js`, `filters.js`, `gallery.js`, `nav.js`, `toast.js`). No transpilation step is required for the browser baseline.
- Static files: `whitenoise.storage.CompressedManifestStaticFilesStorage` gives hashing, far-future caching, and gzip/brotli precompression.

**Rationale.** Constitution III forbids CDNs and SPA frameworks and requires locally compiled
production assets. The reference's interactions — drawer, filter panel, gallery, quantity stepper,
toast — are all small, local DOM behaviours that need no framework. Keeping modules separate and
page-scoped is what makes the ≤30 KB per-page JavaScript budget (PB-6) achievable.

**Alternatives considered and rejected.** Vite/webpack — a build system for a problem we do not
have; native modules are already the deliverable format. Alpine/HTMX — new runtime dependencies that
Constitution III does not approve. Inline `<script>` blocks — defeat CSP, caching, and testability.
A single `app.js` — violates Constitution IV.6 and blows the per-page budget.

---

## R-008 — Fonts

**Decision.** Self-host **Poppins woff2** at weights **400, 500, 600, 700** (latin subset) copied
from the verified `@fontsource/poppins@5.3.0` package into `storefront/static/fonts/`, declared with
`@font-face … font-display: swap` and preloaded for the two weights used above the fold.

**Rationale.** Constitution III.5 requires self-hosted fonts from repository files or the build;
PB-16 requires a `font-display` strategy that never hides text. `swap` guarantees text is never
invisible. Four weights cover the reference's observed weight range while keeping payload small.

**Alternatives considered and rejected.** Google Fonts CDN — prohibited (III.2), and would appear as
a third-party origin in the PB-13 network trace. Variable font — not what `@fontsource/poppins`
ships for this family here; adopting one would be an unverified substitution. Loading all nine
weights — unnecessary payload against PB-1.

---

## R-009 — Icons

**Decision.** A **build-time SVG sprite** generated from the installed `lucide@1.28.0` package,
containing only the icons actually used, inlined as `<svg><use href="#icon-…"></svg>`. Zero icon
JavaScript at runtime.

**Rationale.** Constitution's approved stack permits "local SVG icons or locally installed Lucide
icons". The reference uses Lucide, so glyph shapes match without invention. A sprite avoids shipping
the Lucide runtime and keeps icons in the CSS/HTML layer where `currentColor` inherits the governed
palette — which matters because icon colour must obey the same token rules (FR-117).

**Alternatives considered and rejected.** `lucide` runtime JS replacing DOM nodes — adds runtime
cost and causes layout shift against PB-9. Icon font — poor accessibility semantics and a11y
tooling noise. Per-icon inline SVG duplicated in templates — repeats markup, defeating IV.4.

---

## R-010 — Product imagery strategy

**Decision.** Verified product images are copied from the legacy repository into
`storefront/static/img/products/`, converted at **build time** to WebP with explicit
`width`/`height` attributes, and served through a `<picture>` element with a responsive `srcset`.
Above-the-fold hero imagery is `loading="eager"` with `fetchpriority="high"`; every other image is
`loading="lazy"` and `decoding="async"`.

**Rationale.** PB-14 requires 100 % dimension reservation and PB-15 requires below-fold lazy
loading; NFR-011 requires stable ratios across breakpoints. Declaring intrinsic dimensions is what
keeps CLS ≤ 0.05 (PB-9). Aspect ratio is preserved by the source images being product shots on
white, which the specification requires not to be stretched or cropped incorrectly (CI-11).

**Measured source reality — and why normalisation is mandatory.** The 25 approved assets were
measured. They are **transparent-background RGBA PNGs with wildly inconsistent aspect ratios and
very large payloads**:

| Asset | Pixels | Aspect (W/H) | Bytes |
| --- | --- | --- | --- |
| `A-06 白色把手.png` (media-003) | 1280 × 2355 | 0.54 | 1.24 MB |
| `R02.png` (media-031) | 3680 × 5520 | 0.67 | 4.54 MB |
| `MR6.png` (media-028) | 1128 × 1280 | 0.88 | 0.67 MB |
| `W08.png` (media-048) | 2048 × 2048 | 1.00 | 1.57 MB |
| `K11.png` (media-007) | 1706 × 1279 | 1.33 | 0.18 MB |
| `W08 2.png` (media-047) | 3680 × 4176 | 0.88 | **7.39 MB** |

Aspect ratios span **0.54 to 1.33** — a 2.5× range. Serving these as-is would violate RF-4
(consistent product-card proportions), NFR-011 (stable image dimensions), and PB-1/PB-3 (a single
unoptimised image exceeds the whole page-weight budget).

**Normalisation rule — ratio corrected against the reference.** Every product image is composited at
build time **contained** inside a fixed **1:1 square** box on the **`#EEF0F5`** token background —
never cropped, never stretched, never upscaled beyond native resolution (CI-11). Transparency is
flattened onto that token so every card surface is uniform.

**This ratio is measured from the reference, not chosen.** Inspection of the reference bundle shows
product media frames are `aspect-square` on a `bg-[#EEF0F5]` placeholder in all three product
contexts — card frame (`relative overflow-hidden bg-[#EEF0F5] aspect-square`), product-detail main
image (`relative rounded-3xl overflow-hidden aspect-square bg-[#EEF0F5]`), and detail thumbnails.
Only **category tiles** use `aspect-[4/5]` portrait (`aspect-[4/5] bg-[#EEF0F5]`). An earlier draft
of this document proposed 4:5 for products; that was wrong and is corrected here.

This also resolves a subtlety: the reference applies `object-cover` to product images, which would
**crop** a non-square source. Because normalisation already produces a square, `object-cover` is a
no-op at render time and no product is ever cropped — satisfying CI-11 while matching the
reference's markup exactly.

**This follows verified legacy precedent, not invention.** The legacy repository's
`compose_marketing_image()` performs exactly this operation — contain, never crop/stretch/upscale,
onto a soft white wash, output WebP quality 82 method 6. Adopting the same approach keeps ZAKEY's
product presentation consistent with previously approved output.

**Derived render widths.** Card renders at 1× ≈ 400 px and detail at 1× ≈ 800 px, from the grid
definitions in §8 of the specification; `srcset` emits 400/800 for cards and 800/1600 for detail.
The smallest approved native asset is `K11.png` at 1706 × 1279, so the 800 px card and 1600 px
detail variants never upscale. Output is WebP (quality 82, method 6 — the verified legacy encoder
settings), with a PNG fallback only where transparency against a non-token background is required
(it is not, after normalisation). Final byte sizes are recorded in the asset manifest at build time
and checked against PB-1 and PB-3.

**Alternatives considered and rejected.** Runtime image processing (e.g. an image proxy or
`sorl-thumbnail`) — new dependency plus per-request cost. Shipping original PNGs unconverted —
inflates page weight against PB-1/PB-3. CSS `background-image` for product shots — loses `alt` text
and breaks CI-12.

---

## R-011 — Palette-drift and content-integrity auditing

**Decision.** Four automated gates, run in verification:

1. **Namespace reset** (R-003) — unauthorised colour utilities do not compile.
2. **Source colour audit** — a check that fails on any hex, `rgb(`, `hsl(`, or `oklch(` literal
   appearing in templates, JavaScript, or CSS **outside** `tokens.css`; and on any Tailwind
   arbitrary colour value `-[#…]`. Enforces CID-2, FR-116, SC-046.
3. **Rendered-colour audit** — a Playwright pass collecting every computed `color`,
   `background-color`, `border-color`, and `fill` on every in-scope page at all four widths,
   asserting each resolves to a value in the ratified 18, and diffing internal pages against the
   homepage to catch drift. Enforces FR-117, SC-047, SC-048.
4. **Contrast audit** — every token pairing actually observed in the rendered audit is contrast-
   checked against its WCAG threshold, with `#C9A227`-as-normal-text-on-light and `#9CA3AF`-as-text
   assertions called out explicitly. Enforces FR-118, FR-120, SC-050.

**Rationale.** SC-046 through SC-050 are stated as measurable, so they need mechanisms, not
intentions. Auditing *rendered* colour rather than source catches drift introduced through
inheritance and specificity, which a source grep cannot see.

**Alternatives considered and rejected.** Visual regression pixel-diffing as the primary colour
control — brittle against legitimate content changes and unable to say *which* colour is wrong.
Manual review only — the control the user explicitly rejected.

---

## R-012 — Session data shape and integrity

**Decision.** The session stores a **versioned, minimal, identifier-only** structure:

```
session["zakey_cart"]     = {"v": 1, "lines": [{"sku": "<slug>", "qty": <int 1..99>}]}
session["zakey_wishlist"] = {"v": 1, "skus": ["<slug>", …]}
session["zakey_checkout"] = {"v": 1, "fields": {…validated values…}, "validated": <bool>}
```

Rules: no price, total, name, or image ever enters the session; quantity is clamped server-side to
1–99; unknown slugs are dropped silently on read (FR-101, FR-047); a `v` mismatch discards the
structure rather than migrating it blindly; every mutation is POST-only with CSRF and returns a
redirect (POST/Redirect/GET) so reload cannot re-submit.

**Rationale.** Directly implements "the browser must not be the authority for price, product
identity, totals, or validation". Totals are derived, never stored, so client-side tampering has no
surface to attack. Versioning prevents Feature 002 shape changes from crashing live sessions.

**Alternatives considered and rejected.** Storing denormalised product data in the session for
render speed — creates a second source of truth for price and name, exactly the forgery vector the
security section names. Storing computed totals — same objection, and would let a stale total
survive a catalogue change.

---

## R-013 — Search, filter, and sort implementation

**Decision.** In-memory filtering over the loaded read models, executed **inside the provider**, not
in views or templates. Search matches case-insensitively and accent-insensitively across display
name, model code, supplier brand, category name, and collection name (FR-026). Filters are
multi-select within a facet (OR) and combined across facets (AND) (FR-018). Sort offers featured,
name A–Z, name Z–A only — no price or popularity sort exists while no verified price or popularity
data exists (FR-017, FR-022). Pagination is server-side, 12 per page.

**Rationale.** 21 products make in-memory operations trivially fast and perfectly deterministic. The
provider owning query semantics is what lets Feature 002 reimplement them as database queries
without touching a single view or template.

**Alternatives considered and rejected.** A search engine (Whoosh, Meilisearch, Postgres FTS) —
disproportionate for 21 products and a new dependency. Client-side filtering — breaks
no-JavaScript operation, shareable URLs, and server-authoritative results.

---

## R-014 — Progressive enhancement baseline

**Decision.** Every in-scope journey — browse, filter, sort, paginate, search, view a product, add
to cart, change quantity, remove, wishlist, complete checkout to order review, submit an enquiry —
**works with JavaScript disabled**, using plain forms and links. JavaScript then upgrades:
drawer/dialog behaviour, the gallery, toasts, and optimistic count updates. Controls that genuinely
require scripting are rendered by scripting, so nothing inert ever appears (FR-089).

**Rationale.** FR-089 requires it, and it is also the cheapest route to the accessibility and
performance targets: server-rendered HTML with progressive layers has no hydration cost and no
inert-control failure mode.

**Alternatives considered and rejected.** JavaScript-required interactions — violates FR-089 and
risks dead controls under script failure. `<noscript>` fallbacks duplicating markup — two code paths
to keep consistent, contradicting IV.4.

---

## R-015 — Testing and verification tooling

**Decision.** `pytest` + `pytest-django` for Python (unit, provider contract, view, form, template
rendering); Playwright 1.62.1 for end-to-end, responsive-overflow, console-error, broken-link, and
screenshot capture; `@axe-core/playwright` 4.12.1 for accessibility; Playwright also drives the
rendered-colour and contrast audits (R-011). JavaScript module behaviour is covered through
Playwright rather than a separate unit runner, because no JS test runner is installed and adding one
would be a dependency change.

**Rationale.** Every tool named is already installed and verified; nothing new is required. The
specification's verification categories map onto exactly these runners.

**Alternatives considered and rejected.** Vitest/Jest for JS units — a dependency addition,
forbidden here; Playwright already exercises the same behaviours in a real browser, which is
stronger evidence. Selenium — superseded, and Playwright is installed. Lighthouse CI — attractive
for Core Web Vitals, but not installed; PB-8/PB-9/PB-10 are therefore measured through Playwright's
performance APIs and recorded, with the measurement method stated rather than a tool implied.

---

## R-016 — Enquiry persistence

**Decision.** A single Django model, `Enquiry`, with its own migration, storing contact details,
message, and a JSON snapshot of the requested product lines. This is **the only** persistent domain
model in Feature 001. Submission succeeds only after the row commits; the confirmation is worded as
an enquiry received and never as an order (FR-052, FR-108, FR-109).

**Rationale.** CL-2 resolved to "persist to a real store; success only on a confirmed write".
Constitution VI.4 forbids a success state without a real operation. An enquiry record is not an
order, not a customer account, and not inventory, so it stays inside the Feature 001 boundary.

**Alternatives considered and rejected.** Logging to a file — not a durable store; "success" would
be a claim about a log write, not a record. Emailing without persisting — email delivery is out of
scope, and a send failure would strand the enquiry. Session-only "submission" — a fake success
state, explicitly forbidden.

---

## R-017 — Alternative text for product imagery

**Decision.** Alt text is **derived deterministically** from verified fields at build time:
`"{public_display_name}, {public_product_type} — product view {n} of {total}"`, e.g. *"Lezn A06
Smart Lock, Smart Lock — product view 1 of 2"*. Where a media asset's
`variant_finish_relationship` records a verified finish, it is appended. Alt text is stored in the
asset manifest, not hand-written per page, and never contains internal terminology (CI-9).

**Rationale.** Inspection confirmed **no alt text exists in any of the three registers** — no `alt`,
`caption`, `description`, or `aria` key appears in any spec-012 data file. CI-12 nonetheless
requires meaningful alternative text on every meaningful image. Deriving it from verified identity
fields is truthful (it states exactly what the image shows) and cannot drift from the product,
because it is generated from the same record that selects the image.

**Recorded honestly:** this alt text is *derived*, not *verified prose*. The asset manifest marks it
`derivation: "generated_from_verified_identity_fields"` so a later reviewer is not misled into
thinking a human wrote it. Legacy precedent exists — its importer generates
`f"{product.name} product view"` — so this is consistent with prior approved behaviour, slightly
enriched for screen-reader usefulness.

**Alternatives considered and rejected.** Hand-authoring 25 descriptions — unverifiable prose about
products nobody on this project has handled, risking invented detail (CI-1). Empty or decorative alt
— product images are meaningful content, so hiding them from assistive technology fails CI-12.
Reusing the filename — filenames are Chinese-language source paths (`A-06 白色把手.png`) and would
leak internal source structure into a user-visible surface.

---

## R-018 — Verified business content for informational pages

**Decision.** Reuse the legacy **Tier-G** content set as the basis for About, FAQ, and the
value-proposition band, carried across verbatim where it fits and conservatively trimmed where it
does not. Specifically: the About body, the 10 FAQ entries, the five self-descriptive trust
statements, the brand name, and the tagline.

**Verified content confirmed available.** Legacy `apps/core/seed_data.py` carries content written
under an explicit governance rule — *"a sentence may not assert an outcome, a credential, a named
customer, a location, a percentage, a count, a warranty, an SLA, or a compatibility guarantee"*.
Directly usable examples:

- *"Zakey publishes a catalogue of smart door locks and access-control hardware… Products are
  supplied under their manufacturer's own brand, and every product page names that brand and the
  exact model."*
- FAQ: *"Are the products Zakey-manufactured?" → "No. Products are supplied under their
  manufacturer's own brand, and each product page names that brand and model."*
- FAQ: *"Why are prices not shown on the product pages?" → "The catalogue is quote-only. Pricing
  depends on the configuration and quantity you need, so it is confirmed per enquiry rather than
  listed."*
- Trust statement: *"Every product page names its manufacturer and exact model. Nothing is rebadged
  and nothing is presented as Zakey-made."*

These map exactly onto FR-040, FR-067, FR-034, and CI-8 — the storefront's hardest content
requirements already have approved wording.

**Two constraints recorded, not glossed.**

1. **This is Tier-G, not client-verified.** The legacy module states plainly that *"Zakey has no
   Tier-V copy yet"*. The content is safe because it makes no claims, not because a client signed
   it off. Feature 001 ships it on that basis and records it as such.
2. **Brand casing differs.** Legacy renders the brand as **"Zakey"**; this project's specification
   and constitution use **"ZAKEY"**. Feature 001 follows the constitution ("ZAKEY") for the brand
   mark and normalises quoted legacy copy accordingly, which is a casing change only and alters no
   claim.

**Explicitly not reusable.** Legacy records a deleted-fabrication list — *"200+ Projects
Delivered"*, *"5+ Years of Expertise"*, *"5 Countries Served"*, *"24-Mo Hardware Warranty"*,
*"20–35% Energy Savings"*, a founding story, and four fictional team disciplines — plus seven
superseded FAQ answers inventing Zigbee/Matter support and a two-year GCC warranty. None of it may
be reused (RD-6, RD-7, RD-8).

---

## R-019 — Contact facts: domain verified, mailboxes not

**Decision.** Ship the Contact page with the working enquiry form and **no contact-details block**,
per FR-068 and CI-15. Do not render a phone number, email address, or postal address.

**Evidence.** Every legacy contact value is a deliberate placeholder: phone
`+20 100 000 0000` / `+201000000000` (an all-zeros pattern chosen, per the legacy comment, *"so that
a preview visitor who taps 'call' cannot reach a real person by accident"*), emails at the
unverified `@zakey.shop`, and `address_line` left **deliberately empty** with the note that *"a
fabricated business address is a fabricated business fact"*. All five social URLs are likewise
empty.

**One genuine finding.** The domain **`zakey.shop` is verified real** — the legacy deploy contract
test asserts a live TLS certificate at `/etc/letsencrypt/live/zakey.shop/` and
`server_name zakey.shop www.zakey.shop`. The *domain* is therefore established; **no mailbox at it
is**. Feature 001 may use the domain for canonical URLs and metadata, and still must not publish an
email address.

**Precedent adopted.** Legacy carries `test_contact_facts_provenance.py`, which blanks settings and
asserts across 13 public URLs that no page emits `mailto:`, `tel:`, `wa.me`, a placeholder number,
or a fabricated address. Feature 001 adopts the same guard as part of its content audit (SC-019,
SC-020).

---

## Resolved: zero remaining unknowns

Every Technical Context item is decided above with evidence. Two items are explicitly recorded as
*measurements to be taken during implementation* rather than unknowns to be guessed — the responsive
`srcset` widths derived from measured render sizes (R-010), and the Core Web Vitals figures
themselves (R-015). Both have a stated method; neither is an open decision.

# Research: ZAKEY Frontend Reference Build

## R1 — Rendering shell

**Decision**: Django 5.2 LTS with direct presentation views and no installed business apps,
database configuration, models, migrations, admin, authentication or sessions.

**Rationale**: Django Templates provide inheritance, include-based reuse, localization-safe HTML
and a straightforward future adapter boundary while remaining server-rendered and progressively
enhanced.

**Alternatives rejected**: Static duplicated HTML would weaken shared-component consistency;
React/Vue/SPA frameworks violate the required stack and progressive-enhancement goal.

## R2 — Fixture source

**Decision**: One UTF-8 JSON fixture loaded by a small Python presentation adapter and serialized
for client use.

**Rationale**: JSON is language-neutral, diffable and replaceable. One authored record prevents
template/JavaScript drift while the adapter creates a clear future database handoff.

**Alternatives rejected**: Per-template constants and separate Python/JavaScript fixtures duplicate
prices and product state; Django models are explicitly out of scope.

## R3 — Local prototype state

**Decision**: Versioned `localStorage` behind one storage adapter for cart, wishlist and account
demo preference; transient UI state stays in memory or query parameters.

**Rationale**: It demonstrates reload consistency without server/customer persistence and is easy
to reset or replace.

**Alternatives rejected**: Direct component access to `localStorage` couples UI to persistence;
cookies/sessions imply a server boundary not needed here.

## R4 — Styling and fonts

**Decision**: Tailwind CSS 4.3.3 compiled locally, a focused component stylesheet, local
`@fontsource/cairo` and `@fontsource/poppins`, and `lucide-static` icons copied into local assets.

**Rationale**: This supplies the required local build, consistent tokens and no runtime network
dependency. Cairo owns Arabic; Poppins is restricted to Latin brand/technical tokens.

**Alternatives rejected**: Tailwind CDN and remote Google Fonts violate no-CDN operation;
Bootstrap or a component framework would compete with the reference grammar.

## R5 — Images

**Decision**: Use locally stored, optimized demonstration product/lifestyle imagery with explicit
dimensions and Arabic alternative text. Generate or curate a small coherent set before page work.

**Rationale**: The source reference contains broken remote images. Local assets prevent runtime
failure and support faithful image ratios without claiming real catalogue photography.

**Alternatives rejected**: Hotlinking the reference is brittle and unauthorized as a dependency;
generic placeholder blocks fail the premium bar.

## R6 — Search/filter progressive enhancement

**Decision**: Django views accept `q`, `category`, `collection`, price, feature, availability,
`sort` and `page` GET values; native JS applies the same rules instantly from the embedded fixture.

**Rationale**: Direct links and no-JavaScript navigation stay useful, while the prototype still
feels responsive.

**Alternatives rejected**: Client-only routing breaks direct routes; a backend API is out of scope.

## R7 — QA stack

**Decision**: Django `SimpleTestCase`, Playwright 1.62.1 with installed Chrome 150,
`@axe-core/playwright` 4.12.1, `html-validate` 11.6.0 and Node syntax checking.

**Rationale**: These tools cover render contracts, real-browser interaction, accessibility,
rendered markup and native module syntax with the smallest justified dependency set.

**Alternatives rejected**: Downloading a second browser adds no required coverage; a heavy JS
test framework duplicates Playwright for this prototype.

## R8 — Visual comparison

**Decision**: Pair each implementation capture with the same-width source reference and review
against a named structural/polish rubric. Use image diffs as diagnostic evidence, not a rigid pixel
threshold, because Arabic RTL and fixed source defects require intentional differences.

**Rationale**: Direct browser comparison honors the binding source while keeping localisation and
accessibility corrections explainable.

## R9 — Egyptian validation and service eligibility

**Decision**: Normalize separators and `+20` to a domestic 11-digit mobile number; accept only
010/011/012/015. Store all 27 governorates and area-specific service flags in the fixture. Same-day
areas and installation governorates are the exact lists in FR-045.

**Rationale**: Central deterministic rules make UI, tests and future backend handoff consistent.

## R10 — Dependency versions verified 2026-08-01

- Django 5.2.16 LTS
- Tailwind CSS / CLI 4.3.3
- Fontsource Cairo / Poppins 5.3.0
- lucide-static 1.28.0
- Playwright 1.62.1
- axe Playwright 4.12.1
- html-validate 11.6.0

Only these direct dependencies are planned. Lockfiles record transitive dependencies.

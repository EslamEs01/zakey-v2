# Delegated frontend batch: secondary pages

Implement only the bounded secondary-page batch for the active frontend-only feature.

## Authority and evidence

- Repository: `/media/mekky/work/backend/zakey-v2`
- Branch: `003-zakey-frontend-reference-build`
- Read `specs/003-zakey-frontend-reference-build/reference-inventory.md`, `spec.md`, `plan.md`, the two frontend contracts, `storefront/fixtures/frontend-fixtures.json`, `templates/base.html`, current shared partials/components, and current source CSS/JS before editing.
- The captured reference evidence under `specs/003-zakey-frontend-reference-build/reference-evidence/` is binding. Preserve the established navy/gold Arabic RTL system and shared component conventions; do not invent another design system.

## Exact permitted writes

- `templates/pages/about.html`
- `templates/pages/contact.html`
- `templates/pages/account.html`
- `templates/pages/404.html`
- `templates/pages/500.html`
- `static/src/js/pages/contact.js`
- `static/src/js/pages/account.js`
- `static/src/css/secondary-pages.css`

Do not edit any other file. Do not install dependencies. Do not invoke another agent. Do not run Git write commands. Do not commit, push, open a PR, deploy, or access production.

## Acceptance criteria

- Django templates extend `base.html`, use existing fixture/context data, semantic landmarks/headings, local static paths and shared components.
- About follows the inspected reference composition: premium intro, trust/story split, values, team; responsive desktop split to mobile stack.
- Contact follows reference composition: three contact-method cards, form plus FAQ/chat column, Arabic validation with field-linked errors, live status, no fake network submission.
- Account contains signed-out and signed-in prototype states; signed-in includes profile and tabs for orders, wishlist, addresses, payment methods and settings. Native JS provides accessible tab semantics and updates only through the provided store adapter.
- Error pages share the site chrome and provide working recovery links; 404 and 5xx are visually distinct, concise and accessible.
- All forms/buttons/links function without `href="#"`; no remote dependencies, Lorem Ipsum, visible template tokens or backend behavior.
- CSS is scoped to these pages, handles 1440/1024/768/390, minimum 44px touch targets, RTL wrapping, visible focus inherited from shared CSS, and reduced motion.
- JS is modular, defensive and produces no console errors.
- Keep everything presentation-only. No models, migrations, admin, persistence, authentication, APIs, orders, payments, shipping integrations, or backend business logic.

## Verification

Run syntax/static checks available without changing dependencies. Report exact files changed, checks run, and any limitations. Completion claims are provisional until Codex reviews the complete diff and browser output.

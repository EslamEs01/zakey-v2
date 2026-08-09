# Visual regression tests

`visual-regression.spec.js` full-page screenshots each of the 13 public routes
(see `storefront/urls.py`) and diffs them against committed baselines via
Playwright `toHaveScreenshot()` (`maxDiffPixelRatio: 0.01`, animations disabled,
fonts/images settled before capture).

Baselines live in `tests/visual/visual-regression.spec.js-snapshots/` and are
viewport-scoped: each chrome project (`chrome-1440/1024/768/390` from
`playwright.config.js`) produces its own 13 baselines per run.

Commands:

- `npm run test:visual` — compare against baselines (all projects).
- `npm run test:visual:update` — regenerate baselines after an intentional visual change.

Any page change beyond the diff threshold fails the matched test; inspect
`test-results/` (or the Playwright report) for the visual diff.

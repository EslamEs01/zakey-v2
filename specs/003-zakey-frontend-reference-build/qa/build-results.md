# Build and Test Results

**Date**: 2026-08-01
**Status**: Pass

## Toolchain

- Node v22.22.2
- npm 10.9.7
- uv 0.11.9
- Python 3.12.3
- Django 5.2.16
- Google Chrome 150.0.7871.114

## Final commands

| Command | Exact result |
|---|---|
| npm run build | Pass; copied 9 fonts and 42 icons; Tailwind CSS 4.3.3 completed |
| npm run check:js | Pass; JavaScript syntax check passed for 25 files |
| npm run check:matrix | Pass; QA matrix complete: 56 states × 4 widths |
| npm run check:html | Pass; rendered HTML validation passed for 224 QA cells |
| npm run check:evidence | Pass; QA matrix complete: 56 states × 4 widths |
| uv run python manage.py check | Pass; no issues, 0 silenced |
| uv run python manage.py test | Pass; 14 tests in 0.274s |
| Playwright site-integrity, four projects | Pass; 224 tests in 15.5m |
| Playwright HTML-only regeneration | Pass; 224 tests in 5.2m |
| npm run test:no-js | Pass; 40 tests in 52.1s |
| interaction-journeys, four projects | Pass; 28 tests in 1.6m |

The browser runs used the locally installed Chrome channel. No CDN, database,
production provider or external runtime service is needed for preview.

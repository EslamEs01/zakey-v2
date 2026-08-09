# Baseline 004 — Pre-Implementation Contract Freeze

Recorded at 2026-08-05T02:29Z (UTC). Environment: PostgreSQL dev cluster at
`127.0.0.1:5433` (db=zakey, user=zakey), running via `scripts/dev-db.sh start`
(cluster was already up). All Django/pytest commands run with:

```
DJANGO_SETTINGS_MODULE=config.settings DJANGO_ENV=development DATABASE_URL=postgres://zakey@127.0.0.1:5433/zakey
```

## Identity

| Item | Value |
| --- | --- |
| git HEAD | `98237d7587f358dfd9067b3fff0fe355976c507f` |
| Branch | `004-zakey-commerce-backend-admin` |

## Baseline command results

| Check | Command | Result | Evidence (tail) |
| --- | --- | --- | --- |
| Asset build | `npm run build` | PASS | `Copied 9 fonts and 42 icons.` / `≈ tailwindcss v4.3.3` / `Done in 232ms` |
| Django system check | `uv run python manage.py check` (env above, `DJANGO_ENV=development`) | PASS | `System check identified no issues (0 silenced).` |
| Full Python test suite | `uv run pytest -q` | PASS | `152 passed in 30.61s` |

## Pytest collection summary (`uv run pytest --collect-only -q`)

Totals line: `152 tests collected in 0.13s`

| Suite | Tests collected | Provenance |
| --- | --- | --- |
| `apps/cart/tests/test_cart_identity.py` | 12 | Added on this branch |
| `apps/core/tests/test_money.py` | 15 | Added on this branch |
| `apps/inventory/tests/test_stock_constraints.py` | 13 | Added on this branch |
| `apps/orders/tests/test_transitions.py` | 82 | Added on this branch |
| `tests/concurrency/test_races.py` | 8 | Added on this branch |
| `tests/test_fixture_provider.py` | 17 | Pre-existing (modified on this branch) |
| `tests/test_routes.py` | 2 | Pre-existing |
| `tests/test_static_export.py` | 3 | Pre-existing |
| **Total collected** | **152** | — |

The full-run totals line is `152 passed in 30.61s` (no failures, no skips, no
xfails): all 152 collected tests pass as the pre-implementation baseline.

JavaScript-side suites (Playwright) live under `tests/e2e`, `tests/visual`,
`tests/accessibility` and are run separately; Playwright visual baselines are
recorded in `baseline-visual-manifest.md` (see T-0102b). Prior to this freeze,
chrome-1440 visual baselines already existed; the other three viewport
baseline sets are being generated under T-0102b.

## Scope notes

- No template/static/storefront/config files were modified while recording
  this baseline (those trees are read-only for the contract-freeze tasks).
- No `[x]` checkboxes ticked by the implementer; no commits were created.

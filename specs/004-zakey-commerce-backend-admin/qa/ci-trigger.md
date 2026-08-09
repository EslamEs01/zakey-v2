# T-0207 — CI trigger, PostgreSQL service, concurrency job

Local equivalent of the CI defined in `.github/workflows/pages.yml`.

## CI triggers

- `push` to `main`, `003-zakey-frontend-reference-build`, `004-zakey-commerce-backend-admin`, `004-*`
- `pull_request`
- `workflow_dispatch`

Pages export/upload/deploy steps are guarded to `main` / `003-*`; the `deploy`
job itself runs only on `push` to `refs/heads/main`. All jobs run against a
`postgres:16` service container wired via `DATABASE_URL=postgres://zakey:zakey@127.0.0.1:5432/zakey`.

## Local equivalent commands

Database (disposable loopback-only cluster at 127.0.0.1:5433, see `.env.example`):

```bash
scripts/dev-db.sh start   # stop with: scripts/dev-db.sh stop
export DATABASE_URL=postgres://zakey@127.0.0.1:5433/zakey
```

CI `build` job, step for step:

```bash
uv sync --frozen                    # Install uv + python deps
npm ci                              # Set up Node.js 22 + npm deps
npx playwright install --with-deps chrome
npm run build                       # = npm run build:assets && npm run build:css
npm run check:js
uv run python manage.py test        # Django unit tests (against PostgreSQL)
npm run export:pages                # _site export (main/003 only in CI)
npm run test:pages                  # exported Pages navigation/catalogue check (main/003 only)
```

CI `concurrency` job (PostgreSQL-only; SQLite is refused by `conftest.py`):

```bash
uv sync --frozen
uv run pytest -q tests/concurrency
```

Full local QA gate (superset of CI; from `package.json`):

```bash
npm run qa   # build, check:js, check:matrix, playwright test, check:html,
             # check:evidence, test:pages
# extras:
npm run check:html
npm run test:visual      # playwright test ./tests/visual
```

Notes:

- Local `DATABASE_URL` uses the passwordless trust-auth cluster on port `5433`;
  CI uses `zakey:zakey` on port `5432`. Both are PostgreSQL 16.
- `manage.py` sets `DJANGO_SETTINGS_MODULE=config.settings`; pytest reads it
  from `pyproject.toml`. No extra env needed beyond `DATABASE_URL`.

# Quickstart

**Feature**: 004-zakey-commerce-backend-admin

> Describes the environment **after** implementation. None of this exists yet — this feature is in planning.

---

## Prerequisites

Python 3.12 · PostgreSQL 16+ · Node 22.22+ / npm 10.9+ · `uv` · Docker (optional, for local PostgreSQL)

## Setup

```bash
git clone https://github.com/EslamEs01/zakey-v2.git
cd zakey-v2
git checkout 004-zakey-commerce-backend-admin

uv sync                 # Python deps
npm ci                  # Node deps
npm run build           # Tailwind + assets

cp .env.example .env     # then edit — see below
docker compose up -d db  # or use an existing PostgreSQL

uv run python manage.py migrate
uv run python manage.py setup_roles       # the 9 staff groups
uv run python manage.py seed_demo         # demo catalogue (dev only)
uv run python manage.py createsuperuser
uv run python manage.py runserver 127.0.0.1:8000
```

Storefront: <http://127.0.0.1:8000/> · Admin: <http://127.0.0.1:8000/admin/>

## Environment

```bash
DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_SECRET_KEY=<generate>          # never commit
DJANGO_DEBUG=True                     # False in production
DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgres://zakey:zakey@localhost:5432/zakey
EMAIL_HOST=... EMAIL_PORT=... EMAIL_HOST_USER=... EMAIL_HOST_PASSWORD=...
```

## Tests

```bash
uv run pytest                                   # everything
uv run pytest tests/unit tests/integration      # fast
uv run pytest tests/concurrency                 # PostgreSQL ONLY — see below
uv run pytest tests/admin tests/security
uv run python manage.py test                    # legacy Django suites (kept)
npm run qa                                      # frontend gates
npm run test:a11y                               # accessibility
uv run pytest tests/visual                      # visual regression
```

> **`tests/concurrency` requires PostgreSQL.** SQLite silently ignores `SELECT … FOR UPDATE`, so a green SQLite run proves nothing about locking. The suite fails loudly if the backend is not PostgreSQL (NFR-005).

## Management commands

| Command | Purpose |
|---|---|
| `setup_roles` | Create/refresh the 9 staff groups (idempotent) |
| `seed_demo [--dry-run] [--force] [--with-demo-customer]` | Import fixture catalogue; refuses when real orders exist |
| `release_expired_reservations` | Release expired stock reservations (idempotent) |
| `expire_carts` | Expire carts past TTL |
| `reconcile_payments [--since]` | Report payment/order divergence; mutates nothing |
| `verify_stock_integrity` | Report reservation drift; mutates nothing |

## Staff roles

Super Administrator · Store Manager · Catalogue Manager · Inventory Manager · Order Fulfilment · Customer Service · Finance · Content Manager · Read-only Auditor.
Assign via Admin → Settings → Staff. Full grid in `permissions-matrix.md`.

## Common tasks

**Add a product** — Admin → Catalogue → Products → Add. Fill identity, add ≥1 variant (SKU + price) and ≥1 image, then set status `published`.

**Adjust stock** — Admin → Inventory → Stock → select → *Adjust stock*. Delta and reason are mandatory; levels are never typed directly.

**Process an order** — Admin → Orders → open → use the transition actions. Only valid transitions are offered.

**Issue a refund** — Admin → Payments → open payment → *Issue refund*. Cannot exceed captured minus already-refunded.

## Troubleshooting

| Symptom | Cause |
|---|---|
| `relation does not exist` | Run `migrate` |
| Concurrency tests pass suspiciously fast | You are on SQLite — switch to PostgreSQL |
| `seed_demo` refuses | Real orders exist; use `--force` only if you are certain |
| Visual regression fails | A template or CSS change leaked — check the diff, do **not** re-baseline |
| Admin looks unstyled | Run `collectstatic` |

## Architecture at a glance

```
storefront/   presentation — views, templates, static  (routes NEVER change)
apps/         domain — core accounts catalog inventory cart shipping
              promotions orders payments reviews content audit
config/       settings/{base,development,production,test}
tests/        unit integration concurrency admin security seed e2e a11y visual
```

Read next: `plan.md` for architecture, `data-model.md` for schema, `tasks.md` for the work breakdown, and `contracts/frontend-preservation-boundary.md` **before touching any template**.

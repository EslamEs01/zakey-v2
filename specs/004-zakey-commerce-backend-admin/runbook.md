# ZAKEY v2 — deployment runbook (T-2001, T-2004)

**No deployment has been performed.** This document describes the procedure; it
does not record an execution of it. Nothing in this repository has been pushed,
deployed, or pointed at production infrastructure.

---

## 1. Required environment variables

The application refuses to start without these. There are no defaults for
anything security-relevant — a missing secret must stop a deploy, not silently
fall back to a development value.

| Variable | Required | Notes |
|---|---|---|
| `DJANGO_SETTINGS_MODULE` | yes | `config.settings.production` |
| `DJANGO_SECRET_KEY` | yes | ≥50 chars, unique per environment. Never reuse the dev key. |
| `DJANGO_ALLOWED_HOSTS` | yes | Comma-separated. No wildcard in production. |
| `DATABASE_URL` | yes | PostgreSQL 16. SQLite is refused (see `conftest.py`). |
| `DJANGO_LOG_LEVEL` | no | Defaults to `INFO`. |
| `EMAIL_HOST` / `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `EMAIL_PORT` | yes | Confirmation and password-reset mail (FR-053, FR-054). |
| `DEFAULT_FROM_EMAIL` | yes | |
| `CSRF_TRUSTED_ORIGINS` | yes | Scheme + host, e.g. `https://zakey.example`. |

`.env.example` lists these with safe placeholder values. It contains **no real
secrets** and is the only env file in version control.

## 2. Deploy sequence

Every step stops on failure (`set -euo pipefail`). A half-applied deploy is
worse than a refused one.

```bash
set -euo pipefail

# 0. Refuse to run against an unconfigured environment.
: "${DJANGO_SECRET_KEY:?DJANGO_SECRET_KEY is required}"
: "${DATABASE_URL:?DATABASE_URL is required}"
: "${DJANGO_ALLOWED_HOSTS:?DJANGO_ALLOWED_HOSTS is required}"

cd /srv/zakey                      # explicit ZAKEY-only path; never a shared root

uv sync --frozen --no-dev          # exact lockfile, no dev dependencies

uv run python manage.py check --deploy --fail-level WARNING
uv run python manage.py migrate --noinput
uv run python manage.py collectstatic --noinput
uv run python manage.py setup_roles          # idempotent; reconciles the 9 roles

# Verify before switching traffic.
uv run python manage.py verify_stock_integrity
uv run python manage.py reconcile_payments
```

**Never run `seed_demo` in production.** It exists for local development and
carries demo data flagged `is_demo=True`. The deploy sequence above does not
invoke it, and nothing else should.

## 3. First-run only

```bash
uv run python manage.py createsuperuser        # interactive; not in automation
```

Then, in the admin, assign each staff member exactly one of the nine roles.
A staff account with no role can reach the admin and see nothing, which is the
correct default — access is granted deliberately, never inherited.

## 4. Rollback

Rollback is **code-first**: redeploy the previous revision and leave the
database alone. Migrations in this project are additive, so an older revision
runs against a newer schema.

A migration that cannot be rolled forward safely must be reverted deliberately,
with a restore from backup, not with `migrate <app> <previous>` — reversing a
data migration loses whatever it wrote.

```bash
# 1. Redeploy previous revision (code only).
# 2. Confirm health (section 6).
# 3. Only if the schema must also go back: restore from backup (section 5).
```

## 5. Backup and restore

```bash
# Backup — run before every deploy that includes a migration.
pg_dump --format=custom --no-owner "$DATABASE_URL" > "zakey-$(date -u +%Y%m%dT%H%M%SZ).dump"

# Restore — into a scratch database first, never straight over production.
createdb zakey_restore_check
pg_restore --no-owner --dbname=zakey_restore_check zakey-<stamp>.dump
```

A backup that has never been restored is a hypothesis. The restore path above
must be rehearsed into `zakey_restore_check` and the row counts compared against
production before the backup is trusted (T-2002, T-2003).

## 6. Health and monitoring (T-2004)

| Check | Command | Healthy result |
|---|---|---|
| App responds | `curl -fsS https://<host>/` | HTTP 200 |
| Database reachable | `manage.py check --database default` | no issues |
| Migrations applied | `manage.py migrate --check` | exit 0 |
| Stock ledger consistent | `manage.py verify_stock_integrity` | exit 0, "No stock drift found" |
| Payments reconciled | `manage.py reconcile_payments` | exit 0, "No divergence found" |

Both verification commands **report and never repair**, and both exit non-zero
on a finding, so a scheduled run fails loudly instead of scrolling past.

Suggested schedule:

```
*/15 * * * *  manage.py release_expired_reservations
0    * * * *  manage.py reconcile_payments
30   3 * * *  manage.py verify_stock_integrity
0    4 * * 0  manage.py purge_expired_data --apply
```

`purge_expired_data` is dry-run by default; the `--apply` above is deliberate
and is the only scheduled destructive job. It never touches orders, payments,
refunds or the audit log.

## 7. What this deploy must never do

- Touch any other hosted project, database, or service on the host.
- Seed demo data.
- Carry a secret in the repository, the image, or a log line.
- Run with `DEBUG=True`.
- Point at a database it did not create or was not explicitly given.

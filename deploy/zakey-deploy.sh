#!/usr/bin/env bash
# ZAKEY deploy (T-2001) and rollback (T-2003). Locally validatable with
# ZAKEY_DRY_RUN=1; performs no privileged operation in dry-run mode.
#
# NOT EXECUTED against any server from this repository.
set -Eeuo pipefail

readonly ZAKEY_ROOT="${ZAKEY_ROOT:-/srv/zakey}"
readonly ZAKEY_SERVICE="${ZAKEY_SERVICE:-zakey-web}"
readonly DRY_RUN="${ZAKEY_DRY_RUN:-0}"
readonly ACTION="${1:-deploy}"

die() { echo "zakey-deploy: $*" >&2; exit 1; }
step() { echo "==> $*"; }

require_env() {
  local name="$1"
  [ -n "${!name:-}" ] || die "$name is required but unset"
}

validate_environment() {
  step "validating environment"
  require_env DJANGO_SECRET_KEY
  require_env DJANGO_ALLOWED_HOSTS
  require_env DATABASE_URL
  require_env CSRF_TRUSTED_ORIGINS

  # Reject values that are obviously placeholders. A deploy that succeeds with
  # the example secret is worse than one that refuses.
  case "$DJANGO_SECRET_KEY" in
    *PLACEHOLDER*|*changeme*|*CHANGEME*|django-insecure-*)
      die "DJANGO_SECRET_KEY is a placeholder" ;;
  esac
  [ "${#DJANGO_SECRET_KEY}" -ge 50 ] || die "DJANGO_SECRET_KEY is shorter than 50 characters"
  case "$DJANGO_ALLOWED_HOSTS" in
    *PLACEHOLDER*|*example.com*|\*) die "DJANGO_ALLOWED_HOSTS is a placeholder or wildcard" ;;
  esac
  case "$DATABASE_URL" in
    postgres*|postgresql*) : ;;
    *) die "DATABASE_URL must be a PostgreSQL URL (SQLite is refused)" ;;
  esac
  case "$DATABASE_URL" in
    *zakey*) : ;;
    *) die "DATABASE_URL does not name a zakey database; refusing" ;;
  esac
  [ "${DEBUG:-0}" != "1" ] || die "DEBUG=1 must never be set in production"
  echo "    environment OK"
}

run() {
  if [ "$DRY_RUN" = "1" ]; then echo "    [dry-run] $*"; else "$@"; fi
}

deploy() {
  validate_environment
  [ "$DRY_RUN" = "1" ] || cd "$ZAKEY_ROOT" || die "cannot enter ${ZAKEY_ROOT}"

  step "installing locked dependencies"
  run uv sync --frozen --no-dev

  step "django checks"
  run uv run python manage.py check --deploy --fail-level WARNING

  step "database migrations"
  run uv run python manage.py migrate --noinput

  step "static files"
  run uv run python manage.py collectstatic --noinput

  step "reconciling the nine staff roles"
  run uv run python manage.py setup_roles

  # seed_demo is NEVER invoked here. It refuses when real orders exist, but the
  # deploy path must not call it at all.
  step "integrity verification"
  run uv run python manage.py verify_stock_integrity
  run uv run python manage.py reconcile_payments

  step "restarting ${ZAKEY_SERVICE}"
  run systemctl restart "${ZAKEY_SERVICE}"

  step "health check"
  run curl -fsS --max-time 10 http://127.0.0.1:8001/healthz/

  echo "zakey-deploy: deploy complete"
}

# Rollback is code-first. Migrations here are additive, so an older revision runs
# against a newer schema. A schema that must also go back requires a restore from
# backup — reversing a data migration loses what it wrote.
rollback() {
  local revision="${2:-}"
  [ -n "$revision" ] || die "usage: zakey-deploy.sh rollback <git-revision>"
  validate_environment
  # The operator runs this from wherever they happen to stand. Without entering
  # the release root, `uv sync` and `collectstatic` below would silently operate
  # on whatever project that shell is sitting in. (Found by the T-2003 rehearsal.)
  [ "$DRY_RUN" = "1" ] || cd "$ZAKEY_ROOT" || die "cannot enter ${ZAKEY_ROOT}"

  step "rolling back application code to ${revision}"
  run git -C "$ZAKEY_ROOT" checkout --detach "$revision"
  run uv sync --frozen --no-dev
  run uv run python manage.py collectstatic --noinput
  run systemctl restart "${ZAKEY_SERVICE}"

  step "health check"
  run curl -fsS --max-time 10 http://127.0.0.1:8001/healthz/

  echo "zakey-deploy: rolled back to ${revision}"
  echo "NOTE: the database was NOT rolled back. If the schema must also revert,"
  echo "      restore from backup and re-run the restore drill."
}

case "$ACTION" in
  deploy)   deploy ;;
  rollback) rollback "$@" ;;
  validate) validate_environment ;;
  *) die "unknown action: ${ACTION} (deploy|rollback|validate)" ;;
esac

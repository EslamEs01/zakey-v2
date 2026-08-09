#!/usr/bin/env bash
# ZAKEY restore drill (T-2002). Restores a dump into a SCRATCH database and
# compares row counts against the source. Never writes to production.
#
# This is the half of the backup procedure that actually proves anything. A dump
# that has never been restored is a hypothesis about a file.
set -Eeuo pipefail

readonly DUMP="${1:-}"
readonly SCRATCH_DB="${ZAKEY_SCRATCH_DB:-zakey_restore_check}"
readonly DRY_RUN="${ZAKEY_DRY_RUN:-0}"

die() { echo "zakey-restore-drill: $*" >&2; exit 1; }

[ -n "$DUMP" ] || die "usage: zakey-restore-drill.sh <dump-file>"
[ -n "${DATABASE_URL:-}" ] || die "DATABASE_URL is required but unset"

# The scratch database must be unmistakably a scratch database. Restoring over a
# live one is the single worst thing this script could do.
case "$SCRATCH_DB" in
  *restore_check*|*scratch*) : ;;
  *) die "refusing: ZAKEY_SCRATCH_DB=${SCRATCH_DB} is not named as a scratch database" ;;
esac
case "$DATABASE_URL" in
  *"/${SCRATCH_DB}"*) die "refusing: DATABASE_URL points at the scratch database" ;;
esac

if [ "$DRY_RUN" = "1" ]; then
  echo "zakey-restore-drill: DRY RUN"
  echo "  dump       : ${DUMP}"
  echo "  scratch db : ${SCRATCH_DB}"
  echo "  source     : (DATABASE_URL, not printed)"
  for tool in pg_restore psql createdb dropdb; do
    command -v "$tool" >/dev/null 2>&1 || echo "  WARNING: ${tool} not on PATH"
  done
  exit 0
fi

[ -f "$DUMP" ] || die "dump not found: ${DUMP}"
for tool in pg_restore psql createdb dropdb; do
  command -v "$tool" >/dev/null 2>&1 || die "${tool} not found on PATH"
done

cleanup() { dropdb --if-exists "$SCRATCH_DB" >/dev/null 2>&1 || true; }
trap cleanup EXIT

dropdb --if-exists "$SCRATCH_DB"
createdb "$SCRATCH_DB"
pg_restore --no-owner --no-privileges --dbname="$SCRATCH_DB" "$DUMP"

# Compare the tables whose loss would be unrecoverable. A restore that "works"
# but drops order history is a failed restore.
readonly TABLES="orders_order orders_orderline payments_payment payments_refund audit_auditlog catalog_product"
failures=0
for table in $TABLES; do
  src="$(psql "$DATABASE_URL" -tAc "SELECT count(*) FROM ${table}" 2>/dev/null || echo ERR)"
  dst="$(psql -d "$SCRATCH_DB" -tAc "SELECT count(*) FROM ${table}" 2>/dev/null || echo ERR)"
  if [ "$src" = "$dst" ] && [ "$src" != "ERR" ]; then
    echo "  OK   ${table}: ${src}"
  else
    echo "  FAIL ${table}: source=${src} restored=${dst}" >&2
    failures=$((failures + 1))
  fi
done

[ "$failures" -eq 0 ] || die "${failures} table(s) did not match; the backup is NOT proven"
echo "zakey-restore-drill: restore verified against ${DUMP}"

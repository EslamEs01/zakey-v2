#!/usr/bin/env bash
# ZAKEY database backup (T-2002). Safe to run locally with ZAKEY_DRY_RUN=1.
#
# A backup that has never been restored is a hypothesis. `zakey-restore-drill.sh`
# is the other half of this pair and must be run against the dump this produces.
set -Eeuo pipefail

readonly ZAKEY_ROOT="${ZAKEY_ROOT:-/srv/zakey}"
readonly ZAKEY_BACKUP_DIR="${ZAKEY_BACKUP_DIR:-/var/backups/zakey}"
readonly DRY_RUN="${ZAKEY_DRY_RUN:-0}"

die() { echo "zakey-backup: $*" >&2; exit 1; }

require_env() {
  local name="$1"
  [ -n "${!name:-}" ] || die "$name is required but unset"
}

# Every required value is validated before anything runs. A backup that silently
# targets the wrong database is worse than no backup.
require_env DATABASE_URL

case "$DATABASE_URL" in
  *zakey*) : ;;
  *) die "DATABASE_URL does not name a zakey database; refusing to touch it" ;;
esac

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
target="${ZAKEY_BACKUP_DIR}/zakey-${stamp}.dump"

if [ "$DRY_RUN" = "1" ]; then
  echo "zakey-backup: DRY RUN"
  echo "  would write : ${target}"
  echo "  root        : ${ZAKEY_ROOT}"
  command -v pg_dump >/dev/null 2>&1 || echo "  WARNING: pg_dump not on PATH"
  exit 0
fi

[ -d "$ZAKEY_BACKUP_DIR" ] || die "backup directory ${ZAKEY_BACKUP_DIR} does not exist"
command -v pg_dump >/dev/null 2>&1 || die "pg_dump not found on PATH"

umask 077   # the dump contains customer data; nobody else may read it
pg_dump --format=custom --no-owner --no-privileges --file="$target" "$DATABASE_URL"

# A zero-byte or unreadable dump must fail loudly, not sit in the directory
# looking like a backup.
[ -s "$target" ] || die "pg_dump produced an empty file: ${target}"
pg_restore --list "$target" >/dev/null || die "dump is not readable by pg_restore: ${target}"

echo "zakey-backup: wrote ${target} ($(stat -c%s "$target") bytes, verified readable)"

# Retain 14 dumps. Deletion is scoped to this directory and to the ZAKEY naming
# pattern, so it can never remove another project's backups.
find "$ZAKEY_BACKUP_DIR" -maxdepth 1 -name 'zakey-*.dump' -type f -printf '%T@ %p\n' \
  | sort -rn | tail -n +15 | cut -d' ' -f2- | while read -r old; do
      echo "zakey-backup: pruning $(basename "$old")"
      rm -f -- "$old"
    done

#!/usr/bin/env bash
# FR-002 local developer database bring-up for ZAKEY v2.
#
# The approved plan expects PostgreSQL on 127.0.0.1:5433 (see .env.example) but
# deliberately left the *local* server bring-up as a developer-side task. This
# helper creates and starts a DISPOSABLE, per-developer PostgreSQL cluster inside
# the repository at .pgdev/ (git-ignored) bound to loopback only, using trust
# authentication so the sanctioned passwordless DATABASE_URL works out of the box.
#
# HARD BOUNDARIES (do not weaken):
#   * listens on 127.0.0.1 only — never on an external interface;
#   * trust auth is acceptable ONLY because this cluster is local and disposable;
#   * intended solely for development and tests; NOT for any shared or remote host;
#   * the directory .pgdev/ is git-ignored and must never be committed.
#
# Usage:
#   scripts/dev-db.sh start    # create (if needed) and start the cluster
#   scripts/dev-db.sh stop     # stop the cluster
#   scripts/dev-db.sh status   # report status
set -euo pipefail

PG_BIN_DIR="${ZAKEY_PG_BIN_DIR:-/usr/lib/postgresql/16/bin}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PGDEV="$ROOT/.pgdev"
DATA="$PGDEV/data"
SOCKET="$PGDEV/sock"
LOG="$PGDEV/postgres.log"
PORT="${ZAKEY_PG_PORT:-5433}"
ROLE="${ZAKEY_PG_ROLE:-zakey}"
DB="${ZAKEY_PG_DB:-zakey}"
export PATH="$PG_BIN_DIR:$PATH"

case "${1:-start}" in
  start)
    mkdir -p "$DATA" "$SOCKET"
    if [ ! -f "$DATA/PG_VERSION" ]; then
      initdb -D "$DATA" -U "$ROLE" --auth=trust --encoding=UTF8 --locale=C
    fi
    # Idempotent, loopback-only tuning. Append only if not already present.
    grep -q "^port=$PORT" "$DATA/postgresql.conf" 2>/dev/null || cat >>"$DATA/postgresql.conf" <<EOF
listen_addresses='127.0.0.1'
port=$PORT
unix_socket_directories='$SOCKET'
EOF
    if pg_ctl -D "$DATA" status >/dev/null 2>&1; then
      echo "PostgreSQL dev cluster already running (port $PORT)"
    else
      pg_ctl -D "$DATA" -l "$LOG" -o "-p $PORT" -w -t 20 start
    fi
    # Create the expected database if absent (idempotent).
    psql -h "$SOCKET" -p "$PORT" -U "$ROLE" -d postgres -tAc \
      "SELECT 1 FROM pg_database WHERE datname='$DB'" | grep -q 1 \
      || createdb -h "$SOCKET" -p "$PORT" -U "$ROLE" "$DB"
    echo "Ready: postgres://$ROLE@127.0.0.1:$PORT/$DB"
    ;;
  stop)
    pg_ctl -D "$DATA" -m fast stop
    ;;
  status)
    pg_ctl -D "$DATA" status
    ;;
  *)
    echo "usage: $0 {start|stop|status}" >&2; exit 2;;
esac

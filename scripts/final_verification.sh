#!/usr/bin/env bash
# Final serialized verification for ZAKEY v2 (T-1806 / T-1901 / T-1906 / T-2006).
#
# Serial on purpose. Two of this repository's assertions are wall-clock budgets
# (`test_home_p95`, the login timing-equalisation test), and PostgreSQL test
# databases and Playwright browsers both contend badly. An overlapping run
# produces failures that are about the machine rather than the code, which is the
# worst kind of red: it looks like a defect and is not.
#
#   bash scripts/final_verification.sh 2>&1 | tee final-verification.log
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PORT=8012                       # 8000 is held by an unrelated project on this host
DB_HOST=127.0.0.1; DB_PORT=5433
export PGHOST=$DB_HOST PGPORT=$DB_PORT PGUSER=zakey
export ZAKEY_E2E_BASE_URL="http://127.0.0.1:${PORT}"
export ZAKEY_E2E_SERVER_COMMAND="uv run python manage.py runserver 127.0.0.1:${PORT} --noreload"

FAILED=0
step() { printf '\n\n════ %s ════\n' "$*"; }
report() { # report <label> <exit-code>
  if [ "$2" -eq 0 ]; then printf '  RESULT: %s — exit 0 ✓\n' "$1"
  else printf '  RESULT: %s — exit %s ✗\n' "$1" "$2"; FAILED=$((FAILED+1)); fi
}

step "1. tasks.md mechanical reconciliation"
uv run python scripts/verify_task_ledger.py
report "task ledger" $?

step "2. git status --short --branch"
git status --short --branch
report "git status" 0

step "3. git diff --check"
git diff --check
report "git diff --check" $?

step "4. git diff --stat"
git diff --stat | tail -30
report "git diff --stat" 0

step "5. django check"
uv run python manage.py check
report "manage.py check" $?

step "6. production check --deploy"
DJANGO_SECRET_KEY="$(head -c 48 /dev/urandom | base64 | tr -d '\n=+/' | head -c 60)" \
DJANGO_ALLOWED_HOSTS="shop.zakey.example.eg" \
CSRF_TRUSTED_ORIGINS="https://shop.zakey.example.eg" \
DEFAULT_FROM_EMAIL="no-reply@zakey.example.eg" \
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_launch" \
  uv run python manage.py check --deploy --settings=config.settings.production
report "check --deploy (production)" $?

step "7. makemigrations --check"
uv run python manage.py makemigrations --check --dry-run
report "makemigrations --check" $?

step "8. migration plan"
uv run python manage.py migrate --plan 2>&1 | tail -12
report "migrate --plan" 0

step "9. clean PostgreSQL migration (fresh database)"
dropdb --if-exists zakey_verify >/dev/null 2>&1
createdb zakey_verify
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_verify" \
  uv run python manage.py migrate --noinput 2>&1 | tail -4
report "clean migrate" $?

step "10. first development seed"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_verify" \
  uv run python manage.py seed_demo 2>&1 | grep -E "^TOTAL|WARNING|ERROR" | head -4
report "seed_demo (first)" $?

step "11. repeated idempotent development seed"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_verify" \
  uv run python manage.py seed_demo 2>&1 | grep -E "^TOTAL" | head -2
report "seed_demo (repeat)" $?

step "12. commercial launch policy on the freshly seeded database"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_verify" \
  uv run python manage.py apply_launch_policy 2>&1 | tail -7
report "apply_launch_policy" $?

step "13. focused tests added during this work"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_focus" uv run pytest \
  tests/security/test_launch_policy.py \
  tests/security/test_refund_cap_database.py \
  tests/concurrency/test_refund_cap_and_release_races.py \
  apps/orders/tests/test_payment_failure_release.py \
  tests/integration/test_noscript_notice.py \
  tests/deployment/test_rollback_rehearsal.py \
  -p no:randomly -q --no-header -rN
report "focused tests" $?

step "14. complete isolated Django suite"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_full" uv run pytest \
  -p no:randomly -q --no-header -rN
report "full Django suite" $?

step "15. PostgreSQL concurrency suite"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_conc" uv run pytest \
  tests/concurrency -p no:randomly -q --no-header -rN
report "concurrency suite" $?

step "16. inventory + payment transition matrix"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_tx" uv run pytest \
  apps/orders/tests/test_transitions.py apps/payments/tests/test_payment_transitions.py \
  apps/inventory -p no:randomly -q --no-header -rN
report "transition matrix" $?

step "17. refund integrity"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_ref" uv run pytest \
  tests/security/test_refund_cap_database.py apps/payments/tests/test_payments.py \
  -p no:randomly -q --no-header -rN
report "refund integrity" $?

step "18. traceability gate, twice"
M=specs/004-zakey-commerce-backend-admin/traceability.md
uv run python scripts/traceability.py --check --quiet; e1=$?; h1=$(md5sum "$M" | cut -d' ' -f1)
uv run python scripts/traceability.py --check --quiet; e2=$?; h2=$(md5sum "$M" | cut -d' ' -f1)
echo "  run1 exit=$e1 md5=$h1"
echo "  run2 exit=$e2 md5=$h2"
if [ "$e1" -eq 0 ] && [ "$e2" -eq 0 ] && [ "$h1" = "$h2" ]; then
  echo "  deterministic, byte-identical"; report "traceability x2" 0
else report "traceability x2" 1; fi

step "19. traceability node collectibility"
uv run python scripts/verify_traceability_nodes.py | tail -2
report "node collectibility" $?

step "20. deployment-script validation"
for s in deploy/zakey-deploy.sh deploy/zakey-backup.sh deploy/zakey-restore-drill.sh; do
  bash -n "$s" && echo "  syntax ok: $s"
done
report "deploy script syntax" $?

step "21. backup / restore / rollback rehearsal"
DATABASE_URL="postgres://zakey@${DB_HOST}:${DB_PORT}/zakey_dep" uv run pytest \
  tests/deployment/test_rollback_rehearsal.py tests/security/test_deployment_artifacts.py \
  -p no:randomly -q --no-header -rN
report "deployment + rollback rehearsal" $?

step "22. complete visual matrix"
npx playwright test ./tests/visual --reporter=line 2>&1 | grep -vE "^\[WebServer\]" | tail -4
report "visual matrix" $?

printf '\n\n════ SUMMARY ════\n'
if [ "$FAILED" -eq 0 ]; then echo "ALL VERIFICATION STEPS PASSED"; else echo "${FAILED} STEP(S) FAILED"; fi

for db in zakey_verify zakey_focus zakey_full zakey_conc zakey_tx zakey_ref zakey_dep; do
  dropdb --if-exists "$db" >/dev/null 2>&1
  dropdb --if-exists "test_${db}" >/dev/null 2>&1
done
echo "scratch databases dropped"

#!/usr/bin/env bash
# Prove `npm run qa` is repeatable (T-1906).
#
# Waits for an in-flight run 1 if one exists, then performs run 2 from the same
# reset state and diffs the two failure sets. The gate is repeatable only if the
# two runs agree exactly — a gate whose result depends on how many times it has
# been run before is not a gate.
set -u

SP="${1:?scratchpad path required}"
cd /media/mekky/work/backend/zakey-v2

echo "=== waiting for any in-flight run 1 ==="
while pgrep -f "ZAKEY_QA_RUN=1" >/dev/null 2>&1; do sleep 30; done

summarise() {   # $1 = log file, $2 = label
  local log="$1" label="$2"
  echo "--- ${label} totals ---"
  grep -E "^[[:space:]]+[0-9]+ (passed|failed|flaky|skipped)" "$log" | tail -5
  grep -E "^[[:space:]]+[0-9]+\) " "$log" \
    | sed 's/^ *[0-9]*) *//' | sed 's/ *─*$//' | sort
}

echo "=== RUN 1 RESULT ==="
summarise "$SP/qa_run1.txt" "run 1"
summarise "$SP/qa_run1.txt" "run 1" | grep -E "^\[chrome|^\[no-js" > "$SP/fail1.txt" || true
grep -E "^[[:space:]]+[0-9]+\) " "$SP/qa_run1.txt" \
  | sed 's/^ *[0-9]*) *//' | sed 's/ *─*$//' | sort > "$SP/fail1.txt"
echo "run1 failure count: $(wc -l < "$SP/fail1.txt")"

echo
echo "=== inventory state after run 1 ==="
npm run reset:dev 2>&1 | tail -3

echo
echo "=== RUN 2 starting ==="
ZAKEY_QA_RUN=2 npm run qa > "$SP/qa_run2.txt" 2>&1
echo "run 2 exit=$?"

echo "=== RUN 2 RESULT ==="
summarise "$SP/qa_run2.txt" "run 2"
grep -E "^[[:space:]]+[0-9]+\) " "$SP/qa_run2.txt" \
  | sed 's/^ *[0-9]*) *//' | sed 's/ *─*$//' | sort > "$SP/fail2.txt"
echo "run2 failure count: $(wc -l < "$SP/fail2.txt")"

echo
echo "=== REPEATABILITY COMPARISON ==="
if diff -u "$SP/fail1.txt" "$SP/fail2.txt" > "$SP/fail_diff.txt"; then
  echo "IDENTICAL: both runs produced the same failure set"
else
  echo "DIVERGED between runs:"
  cat "$SP/fail_diff.txt"
fi

echo
echo "=== inventory determinism ==="
npm run reset:dev 2>&1 | tail -3

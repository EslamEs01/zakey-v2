#!/usr/bin/env bash
# T-1901 visual review driver.
#
# Claude's own image channel is disabled in this session, so each comparison is
# opened through the Codex CLI's image input, which genuinely renders the PNG.
# One invocation per comparison, all three images attached in the order
# EXPECTED, ACTUAL, DIFF. Output is written per comparison so the review can be
# read, quoted and re-run without re-inspecting everything.
#
# Usage: bash scripts/visual_review.sh [output-dir]
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT="${1:-$ROOT/.visual-review}"
RESULTS="$ROOT/specs/003-zakey-frontend-reference-build/qa/playwright-results"
SNAPS="$ROOT/tests/visual/visual-regression.spec.js-snapshots"

mkdir -p "$OUT"

COMPARISONS=(
  "account 1440"
  "account 1024"
  "account 768"
  "account 390"
  "checkout 1024"
  "checkout 768"
  "checkout 390"
)

read -r -d '' PROMPT <<'EOF'
Three PNGs of the same page are attached, in this order:
  1. EXPECTED  — the approved baseline snapshot
  2. ACTUAL    — what the storefront renders today
  3. DIFF      — Playwright's pixel diff (differing pixels highlighted)

This is an Arabic, right-to-left e-commerce storefront (ZAKEY, smart locks, EGP).

Report ONLY what you can actually see in the images. Never guess. If something is
not legible, say "not legible".

Answer each numbered point:

1. EXPECTED: list every card / section / heading top to bottom, Arabic text plus
   an English gloss.
2. ACTUAL: the same list.
3. The precise difference: what was added, removed, moved or resized.
4. DIFF: which bands/regions are highlighted, and roughly at what vertical
   positions.
5. Arabic rendering: any garbled, reversed, clipped, overlapping or
   wrongly-shaped Arabic? Are ligatures and diacritics intact?
6. Direction: any RTL/LTR error — mirrored punctuation, Latin runs reordered,
   numbers on the wrong side, misaligned edges?
7. Typography: font family/size/weight/line-height differences between EXPECTED
   and ACTUAL, anywhere on the page.
8. Spacing and alignment: padding, margins, gutters, grid alignment, vertical
   rhythm — any drift beyond the changed block?
9. Colour, borders, shadows, icons: any change?
10. Responsive/layout integrity: anything clipped, overflowing, overlapping,
    cut off at an edge, or horizontally scrolling?
11. Authentication/page state: is this signed-in or signed-out? Does anything
    show a customer name, order, or address that a signed-out page must not?
12. Commerce values: any prices, VAT, totals, shipping, installation or stock
    figures visible? Quote them exactly from BOTH images and say whether they
    agree.
13. Forms: validation messages, error states, checkout step progression — any
    difference? Any control that looks broken or unlabelled?
14. Junk: any visible debug output, placeholder, Lorem, TODO, undefined, NaN,
    {{ }}, {% %}, or a fake success message?

Then finish with EXACTLY these two lines and nothing after them:

CLASSIFICATION: <one of: genuine product regression | correct intentional production change | unstable capture | defective baseline>
JUSTIFICATION: <one sentence naming the specific visual evidence>
EOF

for entry in "${COMPARISONS[@]}"; do
  set -- $entry
  route="$1"; width="$2"
  dir="$RESULTS/visual-visual-regression-${route}-chrome-${width}"
  expected="$SNAPS/${route}-chrome-${width}-linux.png"
  actual="$dir/${route}-actual.png"
  diff="$dir/${route}-diff.png"
  target="$OUT/${route}-${width}.md"

  for f in "$expected" "$actual" "$diff"; do
    if [ ! -f "$f" ]; then echo "MISSING: $f" | tee "$target"; continue 2; fi
  done

  echo "=== reviewing ${route} @ ${width} ==="
  {
    echo "# ${route} @ ${width}"
    echo
    echo "expected: ${expected#$ROOT/}"
    echo "actual:   ${actual#$ROOT/}"
    echo "diff:     ${diff#$ROOT/}"
    echo
  } > "$target"

  printf '%s\n' "$PROMPT" | timeout 900 codex exec \
      --skip-git-repo-check --sandbox read-only \
      -i "$expected" -i "$actual" -i "$diff" 2>&1 \
    | sed -n '/^1\./,$p' >> "$target"

  echo "  -> ${target#$ROOT/}"
done

echo
echo "=== classifications ==="
grep -H "^CLASSIFICATION:" "$OUT"/*.md 2>/dev/null | sed "s|$OUT/||"

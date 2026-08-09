#!/usr/bin/env bash
# Final T-1901 review of the four `account` comparisons.
#
# Images are read from `.visual-review/images/`, copied there under
# viewport-qualified names. That matters: Playwright writes every viewport's
# actual to the same `account-actual.png` basename inside a per-viewport
# directory, so a flat copy silently overwrites, and a review can end up
# comparing a 1024 baseline against a 768 render without either side noticing.
#
# Codex runs with its MCP servers disabled and is told not to use tools: given
# the chance it goes looking for the file on disk instead of describing the
# image that is already attached.
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMG="$ROOT/.visual-review/images"
OUT="$ROOT/.visual-review"

read -r -d '' PROMPT <<'EOF'
Three images are ATTACHED, in order: (1) EXPECTED baseline, (2) ACTUAL current
render, (3) Playwright DIFF. Do NOT use any tool and do NOT read any file.
Answer only from the attached images.

This is the ZAKEY Arabic, right-to-left storefront. The page is the SIGNED-OUT
account page. Report only what you can see; say "not legible" when unsure.

1. EXPECTED: every card/section top to bottom, Arabic plus English gloss.
2. ACTUAL: the same list.
3. Exactly what changed: added, removed, moved, resized.
4. Do the ACTUAL cards have a white surface, a border, rounded corners and
   internal padding, consistent with each other?
5. Arabic rendering: garbled, reversed, clipped, overlapping or mis-shaped text?
   Ligatures intact?
6. Direction: any RTL/LTR fault — mirrored punctuation, reordered Latin runs,
   numbers on the wrong side, misaligned edges?
7. Typography: any family/size/weight/line-height difference in the parts that
   both images share (header, hero, footer)?
8. Spacing and alignment outside the changed block: any drift in header, hero or
   footer?
9. Colour, borders, shadows, icons: any change in shared areas?
10. Clipping, overflow, overlap, or anything cut off at an edge?
11. Auth state: is ACTUAL signed-out? Does it show any customer name, address,
    order or other personal data it must not?
12. Commerce values: quote any price, VAT, total, shipping or stock text in each
    image and say whether they agree.
13. Forms: is every field visibly labelled? Any broken, unlabelled or
    overlapping control? Any error state shown?
14. Junk: any visible template syntax, {# #}, {% %}, {{ }}, placeholder, Lorem,
    TODO, undefined, NaN, or fake success message?
15. Does ACTUAL look like a finished, production-quality page?

Finish with EXACTLY these two lines:
CLASSIFICATION: <genuine product regression | correct intentional production change | unstable capture | defective baseline>
JUSTIFICATION: <one sentence citing the specific visual evidence>
EOF

for w in 1440 1024 768 390; do
  target="$OUT/final-account-${w}.md"
  echo "=== account @ ${w} ==="
  { echo "# account @ ${w} — final review"; echo; } > "$target"
  printf '%s\n' "$PROMPT" | timeout 900 codex exec \
      --skip-git-repo-check --sandbox read-only -c 'mcp_servers={}' \
      -i "$IMG/account-${w}-expected.png" \
      -i "$IMG/account-${w}-actual.png" \
      -i "$IMG/account-${w}-diff.png" 2>&1 \
    | sed -n '/^codex$/,$p' | grep -v '^codex$' >> "$target"
  echo "  -> ${target#$ROOT/}"
done

echo
grep -H "^CLASSIFICATION:" "$OUT"/final-account-*.md | sed "s|$OUT/||"

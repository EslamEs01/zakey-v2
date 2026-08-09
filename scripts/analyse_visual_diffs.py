"""Localise visual-regression differences without being able to view images.

This is **not** a substitute for looking at the screenshots. It is what can be
established mechanically: where on the page the differences are, whether the
page changed height, and whether the differing rows form one contiguous band
(consistent with an inserted block) or are smeared through the whole page
(consistent with a typography, spacing or colour regression).

That distinction is the useful one. An added form or an added total row moves
everything below it and leaves everything above it untouched. A changed font or
a changed palette perturbs every band including the header and footer.
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

RESULTS = Path("specs/003-zakey-frontend-reference-build/qa/playwright-results")


def bands(rows: list[int], gap: int = 12) -> list[tuple[int, int]]:
    """Collapse differing row indices into contiguous (start, end) bands."""
    out: list[tuple[int, int]] = []
    for row in rows:
        if out and row - out[-1][1] <= gap:
            out[-1] = (out[-1][0], row)
        else:
            out.append((row, row))
    return out


def analyse(directory: Path) -> None:
    name = directory.name.replace("visual-visual-regression-", "")
    expected = next(directory.glob("*-expected.png"), None)
    actual = next(directory.glob("*-actual.png"), None)
    diff = next(directory.glob("*-diff.png"), None)
    if not (expected and actual and diff):
        return

    with Image.open(expected) as exp, Image.open(actual) as act:
        exp_size, act_size = exp.size, act.size

    with Image.open(diff) as image:
        rgb = image.convert("RGB")
        width, height = rgb.size
        pixels = rgb.load()
        differing_rows = []
        per_row = {}
        for y in range(height):
            count = 0
            for x in range(0, width, 2):  # every 2nd column: bands, not exact counts
                r, g, b = pixels[x, y]
                # Playwright paints differences in saturated red/magenta.
                if r > 150 and g < 110 and b < 110:
                    count += 1
            if count:
                differing_rows.append(y)
                per_row[y] = count

    print(f"\n=== {name} ===")
    print(f"  baseline {exp_size[0]}x{exp_size[1]}   actual {act_size[0]}x{act_size[1]}", end="")
    if exp_size[1] != act_size[1]:
        print(f"   HEIGHT CHANGED by {act_size[1] - exp_size[1]:+d}px")
    else:
        print("   height unchanged")

    if not differing_rows:
        print("  no red pixels detected in the diff mask")
        return

    grouped = bands(differing_rows)
    first, last = differing_rows[0], differing_rows[-1]
    print(f"  differing rows: {len(differing_rows)} of {height}  "
          f"(first y={first}, last y={last})")
    print(f"  clean above y={first}, clean below y={last}")
    print(f"  bands ({len(grouped)}):")
    for start, end in grouped[:12]:
        peak = max(per_row[y] for y in range(start, end + 1) if y in per_row)
        print(f"     y {start:5d}-{end:5d}  ({end - start + 1:5d}px tall, peak {peak} cols)")
    if len(grouped) > 12:
        print(f"     ... and {len(grouped) - 12} more bands")

    header_dirty = first < 200
    coverage = (last - first) / height if height else 0
    verdict = []
    if header_dirty:
        verdict.append("HEADER AFFECTED — inconsistent with a below-the-fold insertion")
    else:
        verdict.append(f"header clean (first difference at y={first})")
    if coverage > 0.8 and len(grouped) > 6:
        verdict.append("differences smeared through the page — check typography/spacing")
    print("  signal: " + "; ".join(verdict))


def main() -> int:
    targets = sorted(d for d in RESULTS.iterdir() if d.is_dir() and any(d.glob("*-diff.png")))
    if not targets:
        print("no failing visual results found")
        return 0
    print(f"analysing {len(targets)} failing comparison(s)")
    for directory in targets:
        analyse(directory)
    return 0


if __name__ == "__main__":
    sys.exit(main())

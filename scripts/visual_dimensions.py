"""Report expected/actual dimensions and pixel delta for the visual comparisons.

Dimensions and pixel counts are *not* a substitute for looking at the images —
`qa/visual-approval-ledger.md` §1 is the standing proof of that. This exists only
to attach a measured number to a judgement already made by eye, and to show
whether a fix moved the page height in the direction the eye expected.

    uv run python scripts/visual_dimensions.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "specs/003-zakey-frontend-reference-build/qa/playwright-results"
SNAPS = ROOT / "tests/visual/visual-regression.spec.js-snapshots"

COMPARISONS = [
    ("account", 1440), ("account", 1024), ("account", 768), ("account", 390),
    ("checkout", 1024), ("checkout", 768), ("checkout", 390),
]


def main() -> int:
    print(f"{'comparison':<18} {'expected':>12} {'actual':>12} {'Δheight':>9} {'diff px':>10} {'ratio':>7}")
    for route, width in COMPARISONS:
        expected = SNAPS / f"{route}-chrome-{width}-linux.png"
        directory = RESULTS / f"visual-visual-regression-{route}-chrome-{width}"
        actual = directory / f"{route}-actual.png"

        name = f"{route}@{width}"
        if not expected.exists() or not actual.exists():
            print(f"{name:<18} {'(missing)':>12}")
            continue

        with Image.open(expected) as exp, Image.open(actual) as act:
            e_size, a_size = exp.size, act.size
            delta = a_size[1] - e_size[1]
            if e_size == a_size:
                diff = ImageChops.difference(exp.convert("RGB"), act.convert("RGB"))
                changed = sum(1 for px in diff.getdata() if px != (0, 0, 0))
                ratio = changed / (e_size[0] * e_size[1])
                print(
                    f"{name:<18} {f'{e_size[0]}x{e_size[1]}':>12} {f'{a_size[0]}x{a_size[1]}':>12} "
                    f"{delta:>+9} {changed:>10,} {ratio:>7.4f}"
                )
            else:
                print(
                    f"{name:<18} {f'{e_size[0]}x{e_size[1]}':>12} {f'{a_size[0]}x{a_size[1]}':>12} "
                    f"{delta:>+9} {'size differs':>10} {'—':>7}"
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

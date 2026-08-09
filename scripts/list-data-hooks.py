#!/usr/bin/env python3
"""Record a deterministic inventory of ``data-*`` attribute hooks (task T-0104).

Scans ``templates/`` and ``static/src`` for ``data-*`` attributes and emits a
sorted JSON inventory mapping each attribute name to the sorted list of files
that reference it. Output is identical across reruns: files are walked in sorted
order, locations are collected into a set then sorted, and JSON is serialized
with ``sort_keys`` so dict ordering never leaks filesystem ordering.

Used by T-1601+ to prove no frontend hook was renamed (frontend-contract §5).

Usage:
    python scripts/list-data-hooks.py                    # print JSON to stdout
    python scripts/list-data-hooks.py -o path/to/out.json  # write to a file
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from pathlib import Path

# Repository root = parent of this script's ``scripts/`` directory.
REPO_ROOT = Path(__file__).resolve().parent.parent

# Directories (relative to the repo root) that hold frontend markup/behaviour.
SCAN_DIRS = ("templates", "static/src")

# File extensions to scan. Binary/static assets (images, fonts, pdf) are skipped.
SCAN_SUFFIXES = {".html", ".htm", ".js", ".css", ".svg"}

# Historical count recorded in the plan/frontend-contract (section 5). The
# baseline is NOT forced to this value; the actual count is reported against it.
HISTORICAL_COUNT = 139

# Matches ``data-<name>`` tokens. ``data`` itself is not a valid hook name, so
# the attribute must carry at least one more character after the ``data-``
# prefix. This intentionally matches hook *references* in JS/CSS (e.g. inside
# querySelector("[data-...]")) as well as real HTML attributes, because a rename
# on either side of the contract is breaking.
DATA_ATTR_RE = re.compile(r"data-[A-Za-z0-9_-]+")


def _iter_files():
    """Yield scannable files under each scan dir in deterministic (sorted) order."""
    for scan_dir in SCAN_DIRS:
        root = REPO_ROOT / scan_dir
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.suffix.lower() in SCAN_SUFFIXES:
                yield path


def _line_numbers(text: str, needle: str):
    """Return 1-based line numbers where ``needle`` occurs, in file order."""
    lines = []
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            lines.append(index)
    return lines


def collect_inventory():
    """Build ``{attribute: [locations...]}`` and occurrence/file totals."""
    attributes = {}
    matched_files = set()
    scanned_files = 0
    total_occurrences = 0

    for path in _iter_files():
        scanned_files += 1
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            # Never let a single unreadable file break determinism of the rest.
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        # Unique attribute names present in this file, in file order.
        seen_in_file = []
        for match in DATA_ATTR_RE.finditer(text):
            total_occurrences += 1
            name = match.group(0)
            if name not in attributes and name not in seen_in_file:
                seen_in_file.append(name)
        if not seen_in_file:
            continue
        matched_files.add(rel)
        for name in seen_in_file:
            locations = attributes.setdefault(name, set())
            for line in _line_numbers(text, name):
                locations.add(f"{rel}:{line}")

    # Convert location sets to sorted lists for stable, readable output.
    attributes = {name: sorted(locs) for name, locs in attributes.items()}
    return attributes, scanned_files, len(matched_files), total_occurrences


def build_report():
    attributes, scanned_files, matched_files, total_occurrences = collect_inventory()
    unique_attributes = len(attributes)
    return {
        "generated_by": "scripts/list-data-hooks.py",
        "generated_at": datetime.date.today().isoformat(),
        "scan_dirs": list(SCAN_DIRS),
        "scan_suffixes": sorted(SCAN_SUFFIXES),
        "historical_count": HISTORICAL_COUNT,
        "actual_unique_attributes": unique_attributes,
        "total_occurrences": total_occurrences,
        "scanned_files": scanned_files,
        "matched_files": matched_files,
        "note": (
            f"actual vs {HISTORICAL_COUNT}: inventoried {unique_attributes} unique "
            f"data-* attributes ({total_occurrences} occurrences) across templates/ "
            f"and static/src; the plan's historical {HISTORICAL_COUNT} records "
            f"hook occurrences, and the actual unique-attribute count is "
            f"{unique_attributes} (not forced to {HISTORICAL_COUNT})."
        ),
        "attributes": attributes,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "-o",
        "--output",
        help="Write the JSON inventory to this path instead of stdout.",
    )
    args = parser.parse_args(argv)

    report = build_report()
    payload = json.dumps(report, indent=2, sort_keys=True) + "\n"

    if args.output:
        out_path = Path(args.output)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload, encoding="utf-8")
        print(f"wrote {out_path} ({report['actual_unique_attributes']} unique data-* attributes)")
    else:
        sys.stdout.write(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

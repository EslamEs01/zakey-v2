"""Mechanically reconcile `tasks.md` (T-1806, SC-014).

A ledger is only as good as the arithmetic behind it, and "143/143" typed into a
report is not arithmetic. This counts the checkboxes, and — more usefully —
checks the things a count alone hides: a task id written twice, a gap in the
numbering, a malformed line that no counter sees at all.

Exit 0 when the ledger is complete and internally consistent.

    uv run python scripts/verify_task_ledger.py
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ROOT / "specs" / "004-zakey-commerce-backend-admin" / "tasks.md"

TASK_LINE = re.compile(r"^\s*- \[([ x])\] \*\*(T-\d{4}[a-z]?)\*\*")
#: Any line that looks like it meant to be a task but is not shaped like one.
SUSPECT = re.compile(r"^\s*-\s*\[.?\]\s*\*?\*?T-\d")


def main() -> int:
    text = TASKS.read_text(encoding="utf-8")
    checked: list[str] = []
    unchecked: list[str] = []
    malformed: list[str] = []

    for number, line in enumerate(text.splitlines(), start=1):
        match = TASK_LINE.match(line)
        if match:
            (checked if match.group(1) == "x" else unchecked).append(match.group(2))
        elif SUSPECT.match(line):
            malformed.append(f"line {number}: {line.strip()[:70]}")

    ids = checked + unchecked
    total = len(ids)
    duplicates = sorted(t for t, n in Counter(ids).items() if n > 1)

    # Numbering runs T-<phase><seq>; a missing id inside a phase's own run is a
    # gap worth reporting, but phases are not contiguous with each other, so the
    # check is per phase prefix.
    by_phase: dict[str, list[int]] = {}
    for task in ids:
        digits = task[2:6]
        by_phase.setdefault(digits[:2], []).append(int(digits[2:]))
    gaps: list[str] = []
    for phase, seqs in sorted(by_phase.items()):
        present = sorted(set(seqs))
        for expected in range(1, max(present) + 1):
            if expected not in present:
                gaps.append(f"T-{phase}{expected:02d}")

    print(f"total tasks      : {total}")
    print(f"checked          : {len(checked)}")
    print(f"unchecked        : {len(unchecked)}")
    print(f"duplicate ids    : {len(duplicates)}{' — ' + ', '.join(duplicates) if duplicates else ''}")
    print(f"missing ids      : {len(gaps)}{' — ' + ', '.join(gaps) if gaps else ''}")
    print(f"malformed lines  : {len(malformed)}")
    for line in malformed:
        print(f"  {line}")
    if unchecked:
        print("\nstill open:")
        for task in unchecked:
            print(f"  {task}")

    ok = not unchecked and not duplicates and not gaps and not malformed
    print("\nLEDGER: " + (f"{len(checked)}/{total} COMPLETE" if ok else "INCOMPLETE"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

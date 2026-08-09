"""Turn traceability gaps into a verifiable worklist (T-1806, SC-014).

For every requirement with no test naming it, report the task that claims it and
any test path that task's own text names. Where a task says *Tests*: `<path>`,
the mapping is stated by the specification itself, so annotating that file with
the requirement ID records a fact rather than a guess.

Gaps with no named test path are listed separately: those need a human to say
which test covers them, and inventing an answer would make the matrix worse than
empty.
"""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "specs" / "004-zakey-commerce-backend-admin"
TASKS = SPEC_DIR / "tasks.md"
SPEC = SPEC_DIR / "spec.md"

REQ = re.compile(r"\b((?:FR|NFR|INV|SC|ASM)-\d{3})\b")
TASK_LINE = re.compile(r"^\s*- \[([ x])\] \*\*(T-\d{4}[a-z]?)\*\*(.*)$")
PATH_RE = re.compile(r"`([^`]*?(?:tests?/[^`]*?|_test\.py|\.spec\.js))`")


def main() -> None:
    tasks = {}
    for line in TASKS.read_text(encoding="utf-8").splitlines():
        m = TASK_LINE.match(line)
        if m:
            _, tid, rest = m.groups()
            tasks[tid] = rest

    # Requirements already named by some test file.
    named = set()
    for root in (ROOT / "tests", ROOT / "apps"):
        for pattern in ("test_*.py", "*.spec.js"):
            for path in root.rglob(pattern):
                named |= set(REQ.findall(path.read_text(encoding="utf-8", errors="ignore")))

    # Requirements defined by the spec.
    defined = []
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s+\*\*((?:FR|NFR|INV|SC|ASM)-\d{3})\*\*", line)
        if m and m.group(1) not in defined:
            defined.append(m.group(1))

    actionable, needs_human = [], []
    for req in defined:
        if req in named:
            continue
        owners = [tid for tid, text in tasks.items() if req in REQ.findall(text)]
        paths = sorted({p for tid in owners for p in PATH_RE.findall(tasks[tid])})
        existing = [p for p in paths if (ROOT / p).exists()]
        if existing:
            actionable.append((req, owners, existing))
        else:
            needs_human.append((req, owners, paths))

    print(f"gaps needing annotation: {len(actionable) + len(needs_human)}")
    print(f"\n== {len(actionable)} with a spec-named test file that exists ==")
    for req, owners, paths in actionable:
        print(f"  {req:8s} {','.join(owners):22s} -> {', '.join(paths)}")
    print(f"\n== {len(needs_human)} with no existing spec-named test file ==")
    for req, owners, paths in needs_human:
        hint = f" (spec names {paths}, absent)" if paths else ""
        print(f"  {req:8s} {','.join(owners) or 'NO TASK'}{hint}")


if __name__ == "__main__":
    main()

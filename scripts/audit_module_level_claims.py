"""Find requirement IDs claimed at module level, and how much they overstate.

A module docstring naming `FR-105, FR-107, FR-114` gives *every* test in that
file to *all three*. When the file genuinely is about one requirement that is
fine and even useful. When it covers several, each one inherits the others'
tests, and the matrix says "26 tests prove FR-105" while most of them prove
something else. The count is inflated and the sampled evidence can name a test
that has nothing to do with the requirement.

This reports every module-level claim alongside the narrower claims that already
exist in the same file, so a module-level ID that is fully covered by class- or
function-level annotations can be dropped without losing the mapping.

    uv run python scripts/audit_module_level_claims.py
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQ_RE = re.compile(r"\b((?:FR|NFR|INV|SC|ASM)-\d{3})\b")
TEST_ROOTS = ("tests", "apps")


def _narrow_claims(tree: ast.AST) -> tuple[set[str], int]:
    """Requirement IDs named below module level, and the file's test count."""
    narrow: set[str] = set()
    count = 0

    def walk(node):
        nonlocal count
        for child in node.body:
            if isinstance(child, ast.ClassDef):
                narrow.update(REQ_RE.findall(ast.get_docstring(child) or ""))
                walk(child)
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if child.name.startswith("test"):
                    count += 1
                    narrow.update(REQ_RE.findall(ast.get_docstring(child) or ""))

    walk(tree)
    return narrow, count


def main() -> int:
    rows = []
    for root in TEST_ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("test_*.py")):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:
                continue
            module_reqs = set(REQ_RE.findall(ast.get_docstring(tree) or ""))
            if not module_reqs:
                continue
            narrow, count = _narrow_claims(tree)
            rows.append((str(path.relative_to(ROOT)), sorted(module_reqs), narrow, count))

    print(f"{len(rows)} file(s) claim a requirement at module level\n")
    risky = 0
    for rel, module_reqs, narrow, count in rows:
        flag = "  " if len(module_reqs) < 2 else "!!"
        if len(module_reqs) >= 2:
            risky += 1
        print(f"{flag} {rel}  ({count} tests)")
        print(f"     module-level : {', '.join(module_reqs)}")
        redundant = [r for r in module_reqs if r in narrow]
        if redundant:
            print(f"     also claimed narrower (droppable): {', '.join(redundant)}")
        only_module = [r for r in module_reqs if r not in narrow]
        if only_module:
            print(f"     ONLY at module level: {', '.join(only_module)}")
        print()

    print(f"{risky} file(s) claim 2+ requirements at module level — each inflates the others.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

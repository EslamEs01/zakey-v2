"""List test node IDs (optionally filtered) to support traceability mapping."""
from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def walk(node, rel, prefix, out):
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            walk(child, rel, prefix + [child.name], out)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child.name.startswith("test"):
                out.append("::".join([rel, *prefix, child.name]))


def main() -> int:
    patterns = [p.lower() for p in sys.argv[1:]]
    for root in ("tests", "apps"):
        base = ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("test_*.py")):
            rel = str(path.relative_to(ROOT))
            if patterns and not any(p in rel.lower() for p in patterns):
                continue
            nodes: list[str] = []
            walk(ast.parse(path.read_text(encoding="utf-8")), rel, [], nodes)
            for node in nodes:
                print(node)
    return 0


if __name__ == "__main__":
    sys.exit(main())

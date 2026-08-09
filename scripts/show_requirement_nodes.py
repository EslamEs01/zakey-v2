"""Print every test node the matrix credits with proving a requirement.

`traceability.md` shows only the first two nodes per row, which is right for a
readable matrix and useless when the question is "did the tests I just wrote
actually land against the requirement they name?".

    uv run python scripts/show_requirement_nodes.py FR-025 FR-075 FR-136
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _traceability():
    spec = importlib.util.spec_from_file_location(
        "_traceability", ROOT / "scripts" / "traceability.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    wanted = [arg.upper() for arg in sys.argv[1:]]
    if not wanted:
        print(__doc__)
        return 2

    traceability = _traceability()
    evidence = traceability.parse_test_evidence()
    known = traceability.known_test_nodes()

    exit_code = 0
    for requirement in wanted:
        nodes = sorted(evidence.get(requirement, ()))
        print(f"\n{requirement} — {len(nodes)} node(s)")
        if not nodes:
            print("  (nothing proves it)")
            exit_code = 1
            continue
        for node in nodes:
            marker = " " if node in known else "  <-- STALE, not in the tree"
            print(f"  {node}{marker}")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())

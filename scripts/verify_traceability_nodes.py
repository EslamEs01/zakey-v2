"""Prove every traceability mapping points at a node pytest can actually run.

`scripts/traceability.py` derives node IDs from its own AST walk. That catches a
mapping to a deleted test, but not a subtler failure: a node the AST can see and
pytest cannot. A test method on a class pytest does not collect (no `Test`
prefix), a file outside `python_files`, or a class with an `__init__` all look
perfectly valid to an AST walk and are silently never executed. A matrix full of
uncollectible node IDs is exactly as useless as a matrix full of missing ones —
and considerably more convincing.

So this asks pytest itself, via `--collect-only`, and compares.

    uv run python scripts/verify_traceability_nodes.py

Exit 0 when every Python node ID in the matrix is collectible. Playwright
`*.spec.js` evidence is reported separately: pytest cannot collect it, so it is
checked for file existence instead.
"""

from __future__ import annotations

import importlib.util
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

#: `test_x[param-1]` and `test_x` are the same node for mapping purposes; the
#: AST cannot know the parameters and does not need to.
PARAM_RE = re.compile(r"\[.*\]$")


def _load_traceability():
    spec = importlib.util.spec_from_file_location(
        "_traceability", ROOT / "scripts" / "traceability.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collected_nodes() -> set[str]:
    """Every node ID pytest reports it would run."""
    # Node IDs need *exactly one* `-q`: none prints a tree, two collapses to a
    # per-file count. `pyproject.toml` already supplies one via `addopts`, so
    # clear addopts and pass it explicitly rather than silently ending up at -qq.
    done = subprocess.run(
        [
            sys.executable, "-m", "pytest", "--collect-only", "-q",
            "-o", "addopts=--strict-markers",
            "-p", "no:cacheprovider",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if done.returncode not in (0, 5):  # 5 == no tests collected
        print(done.stdout[-4000:], file=sys.stderr)
        print(done.stderr[-4000:], file=sys.stderr)
        raise SystemExit("pytest --collect-only failed; cannot verify node IDs")

    nodes: set[str] = set()
    for line in done.stdout.splitlines():
        line = line.strip()
        if "::" not in line or line.startswith(("<", "=", "ERROR", "FAILED")):
            continue
        nodes.add(PARAM_RE.sub("", line))

    # An empty set would mark every mapping uncollectible, which reads as a
    # catastrophe and is almost always a parsing bug instead. Refuse to guess.
    if not nodes:
        print(done.stdout[-2000:], file=sys.stderr)
        raise SystemExit("collected no node IDs; the --collect-only output format changed")
    return nodes


def main() -> int:
    traceability = _load_traceability()
    evidence = traceability.parse_test_evidence()

    mapped: set[str] = set()
    for nodes in evidence.values():
        mapped |= nodes

    js_nodes = {n for n in mapped if n.endswith(".spec.js")}
    py_nodes = mapped - js_nodes

    collected = collected_nodes()
    uncollectible = sorted(py_nodes - collected)
    missing_js = sorted(n for n in js_nodes if not (ROOT / n).exists())

    print(f"mapped python nodes : {len(py_nodes)}")
    print(f"pytest collected    : {len(collected)}")
    print(f"playwright specs    : {len(js_nodes)}")

    if uncollectible:
        print(f"\n{len(uncollectible)} node id(s) pytest cannot collect:")
        for node in uncollectible:
            print(f"  {node}")
    if missing_js:
        print(f"\n{len(missing_js)} playwright spec(s) that do not exist:")
        for node in missing_js:
            print(f"  {node}")

    if uncollectible or missing_js:
        return 1
    print("\nevery traceability node id is collectible")
    return 0


if __name__ == "__main__":
    sys.exit(main())

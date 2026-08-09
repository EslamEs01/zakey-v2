"""Requirement → task → test traceability (T-1806, SC-014).

Everything here is derived from the repository, never hand-maintained:

* **Requirements** come from ``spec.md`` definition lines.
* **Task claims** come from ``tasks.md`` — both task lines (``- [x] **T-1234**
  … → FR-001``) and *section headings*, because some requirements are satisfied
  by the structure of a phase rather than by one task. ``FR-135`` ("integration
  MUST proceed in reversible batches") is claimed by the Phase 16 heading, and a
  parser that only reads task lines reports it as an orphan that isn't one.
* **Test evidence** comes from an AST walk of the test tree, attributing a
  requirement to the *exact test node* whose docstring names it — module,
  class or function. Function-level attribution is what makes the map say
  "``tests/x.py::TestY::test_z`` proves FR-001" rather than "some test in
  ``tests/x.py`` mentions FR-001".

``--check`` turns it into a gate: non-zero exit if any FR lacks a task claim or
test evidence, if a mapped node no longer exists, or if an unknown/malformed
requirement ID is referenced anywhere.

Output is sorted throughout, so two consecutive runs are byte-identical.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC_DIR = ROOT / "specs" / "004-zakey-commerce-backend-admin"
SPEC = SPEC_DIR / "spec.md"
TASKS = SPEC_DIR / "tasks.md"
OUTPUT = SPEC_DIR / "traceability.md"
TEST_ROOTS = ("tests", "apps")

REQ_RE = re.compile(r"\b((?:FR|NFR|INV|SC|ASM)-\d{3})\b")
FR_RE = re.compile(r"\bFR-\d{3}\b")
TASK_RE = re.compile(r"\bT-\d{4}[a-z]?\b")
TASK_LINE_RE = re.compile(r"^\s*- \[([ x])\] \*\*(T-\d{4}[a-z]?)\*\*(.*)$")
HEADING_RE = re.compile(r"^(#{2,6})\s+(.*)$")
DEFINITION_RE = re.compile(r"^\s*-\s+\*\*((?:FR|NFR|INV|SC|ASM)-\d{3})\*\*")

#: Requirements satisfied by process or documentation rather than by an
#: executable test. Each names the artifact that evidences it. Kept explicit and
#: tiny — this is not a place to park requirements that are merely inconvenient.
PROCESS_REQUIREMENTS = {
    "FR-135": "specs/004-zakey-commerce-backend-admin/rollout-and-rollback.md",
}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


def parse_requirements(text: str) -> list[str]:
    """Requirement IDs in the order the specification defines them."""
    out: list[str] = []
    for line in text.splitlines():
        match = DEFINITION_RE.match(line)
        if match and match.group(1) not in out:
            out.append(match.group(1))
    return out


def parse_task_claims(text: str) -> dict[str, set[str]]:
    """requirement -> {task ids}, from task lines *and* section headings.

    A heading claim attaches to every task beneath it, up to the next heading of
    the same or higher level. That mirrors how the document reads: the heading
    states a property of the whole phase.
    """
    claims: dict[str, set[str]] = {}
    heading_stack: list[tuple[int, set[str]]] = []
    pending_headings: set[str] = set()

    for line in text.splitlines():
        heading = HEADING_RE.match(line)
        if heading:
            level = len(heading.group(1))
            while heading_stack and heading_stack[-1][0] >= level:
                heading_stack.pop()
            heading_stack.append((level, set(REQ_RE.findall(heading.group(2)))))
            pending_headings = {r for _, rs in heading_stack for r in rs}
            continue

        task = TASK_LINE_RE.match(line)
        if task:
            task_id = task.group(2)
            for req in set(REQ_RE.findall(task.group(3))) | pending_headings:
                claims.setdefault(req, set()).add(task_id)
            continue

        # A bold line inside a phase body may also carry a claim (e.g. the
        # "Six independently revertible batches (→ FR-135)" note).
        if "→" in line or "->" in line:
            for req in REQ_RE.findall(line):
                claims.setdefault(req, set()).add(_nearest_task(heading_stack))
    return {k: {v for v in vs if v} for k, vs in claims.items()}


def _nearest_task(heading_stack) -> str:
    """Structural claims are attributed to the phase, not to a task id."""
    return "«phase»"


def parse_test_evidence() -> dict[str, set[str]]:
    """requirement -> {exact test node ids}, from docstrings, via AST.

    **The narrowest claim wins.** A module docstring naming a requirement speaks
    for the whole file, which is right when the file is about that one thing and
    wrong the moment it covers several: every test would be attributed to every
    requirement the header lists, so a 26-test admin file claiming five
    requirements would report "26 tests prove FR-105" and cite a bulk-action
    test as the evidence. Inflated counts and mis-sampled evidence are how a
    matrix stops describing the repository while still looking thorough.

    So a module-level claim applies only to requirements that no class or
    function inside that same file claims for itself. Nothing loses its mapping:
    a requirement claimed narrowly keeps its own nodes, and one claimed only at
    module level still covers the file.
    """
    evidence: dict[str, set[str]] = {}

    for root in TEST_ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("test_*.py")):
            rel = str(path.relative_to(ROOT))
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue

            nodes: list[tuple[str, set[str]]] = []
            _walk(tree, rel, [], set(), nodes)

            for node_id, reqs in nodes:
                for req in reqs:
                    evidence.setdefault(req, set()).add(node_id)

            narrow = {req for _, reqs in nodes for req in reqs}
            module_reqs = set(REQ_RE.findall(ast.get_docstring(tree) or ""))
            for req in sorted(module_reqs - narrow):
                for node_id, _ in nodes:
                    evidence.setdefault(req, set()).add(node_id)

        # Playwright specs carry no AST we can walk; attribute at file level and
        # say so, rather than pretending to a precision we do not have.
        for path in sorted(base.rglob("*.spec.js")):
            rel = str(path.relative_to(ROOT))
            for req in REQ_RE.findall(path.read_text(encoding="utf-8", errors="ignore")):
                evidence.setdefault(req, set()).add(rel)

    return evidence


def _walk(node, rel: str, prefix: list[str], inherited: set[str], out: list) -> None:
    """Collect ``(node id, requirements claimed at or above it below module level)``.

    ``inherited`` starts empty rather than at the module's claims, so the caller
    can tell a requirement the file merely lists in its header from one a class
    or function names for itself.
    """
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            reqs = inherited | set(REQ_RE.findall(ast.get_docstring(child) or ""))
            _walk(child, rel, prefix + [child.name], reqs, out)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not child.name.startswith("test"):
                continue
            reqs = inherited | set(REQ_RE.findall(ast.get_docstring(child) or ""))
            out.append(("::".join([rel, *prefix, child.name]), reqs))


def known_test_nodes() -> set[str]:
    """Every node id the AST can see, used to detect stale mappings."""
    nodes: set[str] = set()
    for root in TEST_ROOTS:
        base = ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("test_*.py")):
            rel = str(path.relative_to(ROOT))
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except SyntaxError:  # pragma: no cover
                continue
            _collect_nodes(tree, rel, [], nodes)
        for path in sorted(base.rglob("*.spec.js")):
            nodes.add(str(path.relative_to(ROOT)))
    return nodes


def _collect_nodes(node, rel: str, prefix: list[str], out: set[str]) -> None:
    for child in node.body:
        if isinstance(child, ast.ClassDef):
            _collect_nodes(child, rel, prefix + [child.name], out)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if child.name.startswith("test"):
                out.add("::".join([rel, *prefix, child.name]))


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------


def build() -> tuple[str, list[str]]:
    spec_text = SPEC.read_text(encoding="utf-8")
    tasks_text = TASKS.read_text(encoding="utf-8")

    requirements = parse_requirements(spec_text)
    claims = parse_task_claims(tasks_text)
    evidence = parse_test_evidence()
    nodes = known_test_nodes()

    frs = [r for r in requirements if r.startswith("FR-")]
    problems: list[str] = []

    # Unknown / malformed references anywhere.
    defined = set(requirements)
    for source, referenced in (("tasks.md", set(claims)), ("tests", set(evidence))):
        for req in sorted(referenced - defined):
            problems.append(f"{req}: referenced in {source} but not defined in spec.md")

    # Stale mappings.
    for req, mapped in sorted(evidence.items()):
        for node in sorted(mapped - nodes):
            problems.append(f"{req}: mapped to a node that no longer exists — {node}")

    rows = []
    for req in frs:
        owning = sorted(claims.get(req, ()))
        proving = sorted(evidence.get(req, ()))
        process = PROCESS_REQUIREMENTS.get(req)

        if not owning:
            problems.append(f"{req}: no task claims it")
        if not proving and not process:
            problems.append(f"{req}: no test proves it")

        if process and not proving:
            status, shown = "📄", process
        elif proving:
            status = "✅"
            shown = ", ".join(proving[:2]) + (f" (+{len(proving) - 2})" if len(proving) > 2 else "")
        else:
            status = "❌"
            shown = "—"
        rows.append(f"| {req} | {status} | {', '.join(owning) or '—'} | {len(proving)} | {shown} |")

    lines = [
        "# Traceability — requirement → task → test (T-1806, SC-014)",
        "",
        "Generated by `scripts/traceability.py`. Do not edit by hand.",
        "Regenerate, or the matrix stops describing the repository.",
        "",
        "`✅` a test names the requirement · `📄` satisfied by a process artifact ·",
        "`❌` no evidence.",
        "",
        f"Functional requirements: **{len(frs)}** · "
        f"with a task claim: **{sum(1 for r in frs if claims.get(r))}** · "
        f"with test evidence: **{sum(1 for r in frs if evidence.get(r))}** · "
        f"problems: **{len(problems)}**",
        "",
        "| Requirement | Status | Task(s) | Tests | Evidence |",
        "|---|---|---|---|---|",
        *rows,
    ]
    if problems:
        lines += ["", "## Problems", ""] + [f"- {p}" for p in sorted(set(problems))]

    return "\n".join(lines) + "\n", sorted(set(problems))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="Exit non-zero on any problem.")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    matrix, problems = build()
    OUTPUT.write_text(matrix, encoding="utf-8")
    if not args.quiet:
        print(f"wrote {OUTPUT.relative_to(ROOT)} ({len(problems)} problem(s))")
        for problem in problems[:25]:
            print(f"  {problem}")
        if len(problems) > 25:
            print(f"  ... and {len(problems) - 25} more")
    return 1 if (args.check and problems) else 0


if __name__ == "__main__":
    sys.exit(main())

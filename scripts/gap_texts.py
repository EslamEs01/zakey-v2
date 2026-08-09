"""Print the literal text of every FR that currently lacks test evidence."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = ROOT / "specs/004-zakey-commerce-backend-admin/spec.md"
MATRIX = ROOT / "specs/004-zakey-commerce-backend-admin/traceability.md"


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/traceability.py"), "--quiet"], check=False)
    gaps = re.findall(r"^- (FR-\d{3}): no test proves it$", MATRIX.read_text(encoding="utf-8"), re.M)

    texts = {}
    for line in SPEC.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*-\s+\*\*(FR-\d{3})\*\*:\s*(.*)$", line)
        if m:
            texts[m.group(1)] = re.sub(r"[`*]", "", m.group(2))

    start, end = 0, len(gaps)
    if len(sys.argv) > 2:
        start, end = int(sys.argv[1]), int(sys.argv[2])
    for fr in gaps[start:end]:
        print(f"{fr}| {texts.get(fr, '??')}")
    print(f"--- {len(gaps)} gaps total, showing {start}:{end} ---")
    return 0


if __name__ == "__main__":
    sys.exit(main())

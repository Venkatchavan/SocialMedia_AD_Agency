"""scripts.check_linecount — Fail if any .py file exceeds 250 lines."""

from __future__ import annotations

import sys
from pathlib import Path


def check_linecount(root: Path, max_lines: int = 250) -> list[tuple[str, int]]:
    """Return list of (filepath, line_count) for files exceeding max_lines."""
    violations: list[tuple[str, int]] = []
    for py_file in root.rglob("*.py"):
        lines = py_file.read_text(encoding="utf-8", errors="replace").splitlines()
        if len(lines) > max_lines:
            violations.append((str(py_file.relative_to(root)), len(lines)))
    return violations


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    max_lines = 250
    violations = check_linecount(root, max_lines)

    if violations:
        print(f"FAIL: {len(violations)} file(s) exceed {max_lines} lines:\n")
        for path, count in sorted(violations, key=lambda x: -x[1]):
            print(f"  {path}: {count} lines")
        sys.exit(1)
    else:
        print(f"PASS: All .py files are ≤{max_lines} lines.")
        sys.exit(0)


if __name__ == "__main__":
    main()

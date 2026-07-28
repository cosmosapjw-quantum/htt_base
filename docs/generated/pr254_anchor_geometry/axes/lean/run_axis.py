#!/usr/bin/env python3
"""Parent-owned clean-tree runner for the independent PR-254 Lean axis.

The proof source and compile-gated ``axis_program`` are copied byte-for-byte
from the blind Lean assignment. A clean checkout has the pinned mathlib source
but not its precompiled ``.olean`` cache, so this runner prepares that cache
before invoking the unchanged axis program. Only the axis JSON is written to
stdout; bootstrap diagnostics remain on stderr.
"""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


AXIS_DIR = Path(__file__).resolve().parent
MATHLIB_OLEAN = (
    AXIS_DIR
    / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib.olean"
)


def _run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        cwd=AXIS_DIR,
        capture_output=True,
        text=True,
        check=False,
    )


def main() -> int:
    if not MATHLIB_OLEAN.is_file():
        cache = _run(["lake", "exe", "cache", "get"])
        sys.stderr.write(cache.stdout)
        sys.stderr.write(cache.stderr)
        if cache.returncode != 0:
            return cache.returncode
    axis = _run([str(AXIS_DIR / "axis_program")])
    sys.stdout.write(axis.stdout)
    sys.stderr.write(axis.stderr)
    return axis.returncode


if __name__ == "__main__":
    raise SystemExit(main())

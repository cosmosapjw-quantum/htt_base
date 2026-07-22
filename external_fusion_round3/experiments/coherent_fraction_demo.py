#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.identified import coherent_fraction_interval  # noqa: E402


def main() -> int:
    cases = {}
    for r in (0.48, 0.60, 0.75, 0.90):
        try:
            iv = coherent_fraction_interval(r)
            cases[str(r)] = {"status": "FEASIBLE", "interval": iv}
        except ValueError as exc:
            cases[str(r)] = {"status": "EMPTY", "error": str(exc)}
    print(json.dumps({"status": "PASS", "cases": cases}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

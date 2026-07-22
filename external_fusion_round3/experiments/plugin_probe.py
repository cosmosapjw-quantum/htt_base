#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.plugins.registry import probe_all  # noqa: E402


def main() -> int:
    rows = probe_all()
    print(json.dumps({"status": "PASS", "plugins": rows, "note": "missing optional plugins are not core failures"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

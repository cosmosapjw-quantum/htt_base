#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.discrimination import summarize_simulation  # noqa: E402
from htt_ext.lowell.shells import simulate_shell_poles  # noqa: E402
from htt_ext.types import ShellGrid, SourceModel  # noqa: E402


def main() -> int:
    grid = ShellGrid.from_redshifts([0.02, 0.08, 0.2, 0.45, 0.8, 1.3, 2.0])
    out = {}
    for model in SourceModel:
        sim = simulate_shell_poles(grid, model=model, seed=20260722)
        out[model.value] = summarize_simulation(sim).as_dict()
    payload = {"status": "PASS", "grid": list(grid.redshifts), "models": out}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

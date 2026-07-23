#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.discrimination import summarize_simulation  # noqa: E402
from htt_ext.lowell.shells import simulate_shell_poles  # noqa: E402
from htt_ext.types import ShellGrid, SourceModel  # noqa: E402


def main() -> int:
    coarse = ShellGrid.from_redshifts([0.03, 0.15, 0.45, 0.9, 1.6])
    fine = ShellGrid.from_redshifts([0.02, 0.06, 0.12, 0.22, 0.4, 0.65, 1.0, 1.4, 2.0])
    shifts = []
    for seed in range(20263000, 20263040):
        a = np.asarray(summarize_simulation(simulate_shell_poles(coarse, model=SourceModel.GLOBAL_COHERENT, seed=seed)).features)
        b = np.asarray(summarize_simulation(simulate_shell_poles(fine, model=SourceModel.GLOBAL_COHERENT, seed=seed)).features)
        scale = np.maximum(np.abs(a), 1.0)
        shifts.append(float(np.linalg.norm((a - b) / scale) / np.sqrt(a.size)))
    q95 = float(np.quantile(shifts, 0.95))
    status = "PASS_REFERENCE_STABLE" if q95 < 0.50 else "EXPECTED_BLOCK_PHYSICAL_KERNEL_REQUIRED"
    print(json.dumps({"status": status, "n_seeds": len(shifts), "relative_rms_shift_median": float(np.median(shifts)), "relative_rms_shift_q95": q95, "note": "reference-DGP gate only; physical shell kernels require CAMB/CLASS validation"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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


def mean_feature(model: SourceModel, amp_scale: float, seeds=range(20262000, 20262030)) -> np.ndarray:
    grid = ShellGrid.from_redshifts([0.02, 0.08, 0.2, 0.45, 0.8, 1.3, 2.0])
    values = []
    for seed in seeds:
        sim = simulate_shell_poles(
            grid,
            model=model,
            seed=seed,
            coherent_amplitudes={1: 2.2 * amp_scale, 2: 1.2 * amp_scale, 3: 0.7 * amp_scale},
            observer_boost_amplitudes={1: 5.0 * amp_scale, 2: 0.7 * amp_scale, 3: 0.25 * amp_scale},
        )
        values.append(summarize_simulation(sim).features)
    return np.mean(np.asarray(values), axis=0)


def main() -> int:
    eps = 0.08
    models = [SourceModel.LOCAL_BOOST, SourceModel.GLOBAL_COHERENT, SourceModel.LOCAL_STRUCTURE]
    cols = []
    for model in models:
        plus = mean_feature(model, 1 + eps)
        minus = mean_feature(model, 1 - eps)
        cols.append((plus - minus) / (2 * eps))
    r = np.column_stack(cols)
    s = np.linalg.svd(r, compute_uv=False)
    tol = max(s) * 1e-6
    rank = int(np.sum(s > tol))
    status = "PASS" if rank >= 2 else "FAIL"
    print(json.dumps({"status": status, "response_shape": list(r.shape), "singular_values": s.tolist(), "rank_at_relative_1e-6": rank, "columns": [m.value for m in models]}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

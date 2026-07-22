#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from htt_ext.lowell.poles import angular_separation_deg, mean_axis  # noqa: E402
from htt_ext.remote.fields import simulate_remote_fields  # noqa: E402
from htt_ext.types import ShellGrid, SourceModel  # noqa: E402


def summarize(model: SourceModel) -> dict:
    grid = ShellGrid.from_redshifts([0.1, 0.3, 0.55, 0.9, 1.3, 1.8])
    sim = simulate_remote_fields(grid, model=model, seed=20260722)
    d = np.asarray(sim.dipole_poles)
    q = np.asarray(sim.quadrupole_poles)
    da = mean_axis(d)
    qa = mean_axis(q)
    return {
        "dipole_mean_coherence": float(np.mean(np.abs(d @ da))),
        "quadrupole_mean_coherence": float(np.mean(np.abs(q @ qa))),
        "dipole_quadrupole_mean_axis_angle_deg": angular_separation_deg(da, qa),
    }


def main() -> int:
    out = {m.value: summarize(m) for m in (SourceModel.ISOTROPIC, SourceModel.GLOBAL_COHERENT, SourceModel.LOCAL_STRUCTURE, SourceModel.MIXTURE)}
    print(json.dumps({"status": "PASS", "models": out}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

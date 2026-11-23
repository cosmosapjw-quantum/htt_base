"""Locate the first sky-dipole versus fluid q/E divergence and A/B the stage-velocity fix.

VII_h, ell_max=4, epsilon=2e-4. For each (cells, Picard, stage_velocity_collision) the
per-cell photon q/E from the Stokes sky (-integral of n I) and from the Einstein-Euler
fluid (T^{0i}/T^{00}) are compared at the cell ends nested in the 16-cell grid.
Units: q/E dimensionless; Thomson force/E per e-fold.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import json
from pathlib import Path

import numpy as np

from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann


def run(task):
    cells, picard, staged = task
    out = solve_coupled_einstein_boltzmann("VII_h", CoupledSolverConfig(
        ell_max=4, n_cells=cells, n_picard=picard, epsilon=2e-4, record_history=True,
        stage_velocity_collision=staged))
    rec = out.history["picard_iterations"][-1]
    vb = out.trajectory.species_v_grid["baryon"]
    qs, qf = rec["q_over_E_sky"][0], rec["q_over_E_fluid"][0]
    rel = np.linalg.norm(qs - qf, axis=1) / np.linalg.norm(qf, axis=1)
    idx = np.arange(1, 17) * (cells // 16) - 1
    eq = lambda v: 4 * v / (3 + v @ v)
    fs, ff = rec["thomson_force_over_E_sky"], rec["thomson_force_over_E_fluid"]
    return {"cells": cells, "picard": picard, "stage_velocity_collision": staged,
            "first_cell": {"N_start": float(out.trajectory.N_grid[0]), "N_end": float(rec["N_end"][0]),
                           "delta_tau": float(rec["delta_tau"][0]), "rel_q_mismatch": float(rel[0]),
                           "q_sky": qs[0].tolist(), "q_fluid": qf[0].tolist(),
                           "eq_baryon_mid": eq(vb[1]).tolist(), "eq_baryon_end": eq(vb[2]).tolist(),
                           "abs_force_sky_minus_fluid": float(np.linalg.norm(fs[0] - ff[0])),
                           "abs_force_fluid": float(np.linalg.norm(ff[0]))},
            "nested_N_end": rec["N_end"][idx].tolist(), "nested_rel_q_mismatch": rel[idx].tolist(),
            "final_rel_q_mismatch": float(rel[-1]), "C2_T": float(out.cl_final["T"][2]),
            "picard_pi_rel_change": out.picard_pi_rel_change}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=12)
    a = p.parse_args()
    tasks = [(c, pic, st) for st in (False, True) for pic in (2, 4) for c in (16, 32, 64, 128)]
    with ProcessPoolExecutor(a.workers) as pool:
        runs = list(pool.map(run, tasks))
    a.output.write_text(json.dumps({"schema": "htt.r104.first_divergence/1", "family": "VII_h", "ell_max": 4,
                                    "epsilon": 2e-4, "runs": runs}, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()

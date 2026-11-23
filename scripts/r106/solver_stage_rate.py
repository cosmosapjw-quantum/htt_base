"""A/B convergence of the R106 photon-cell scheme against R105.

R106 = stage-time Thomson rate rescaled to the exact substep depth, |Delta ln r| <= 0.25
substep bound and adaptive Picard (picard_rtol 1e-6, n_picard 4 as minimum); R105 =
substep-average rate with exactly 4 Picard sweeps.

VI_-1/9 with R105 settings (epsilon 2e-4, ell 4, 16 GL rings, Picard 4, 2 minimum substeps,
f_nu 0): signed sky-minus-fluid photon q/E at the 48-cell common endpoints for cells
48/96/192/384 (768 at cap 0.25) and caps 1/0.5/0.25, fitted per cell count as
e = A cap^2 + B on the signed component parallel to the fluid q/E. FLRW null and
VII_h/IX quadrupoles are run with the R106 path. Units: q/E dimensionless; C_ell in
dimensionless bolometric (Delta T/T)^2.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import time

import numpy as np

from bass.transport import coupled_einstein_boltzmann as coupled
from scripts.r105.common_time_moments import nested_samples
from scripts.r105.native_optical_refinement import angular_basis

CAPS = (1.0, 0.5, 0.25)


def run(task):
    family, cells, cap, staged = task
    cfg = coupled.CoupledSolverConfig(n_cells=cells, ell_max=4, n_picard=4, max_substep_depth=cap,
                                      epsilon=0.0 if family == "FLRW" else 2e-4, substeps_per_cell=2,
                                      record_history=True, stage_rate_collision=staged,
                                      picard_rtol=1e-6 if staged else None)
    t0 = time.perf_counter()
    out = coupled.solve_coupled_einstein_boltzmann(family, cfg, lie_op=angular_basis(4, 16))
    wall = time.perf_counter() - t0
    h = out.history["picard_iterations"][-1]
    rec = {"family": family, "n_cells": cells, "cap": cap, "stage_rate_collision": staged, "wall_s": wall,
           "maxrss_kB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "max_hamiltonian": out.max_hamiltonian_residual, "max_codazzi": out.max_codazzi_residual,
           "max_stokes_reality": out.max_stokes_reality_err, "picard_pi_rel_change": out.picard_pi_rel_change,
           "total_substeps": int(np.sum(h["photon_substeps"])),
           "C2": {ch: float(out.cl_final[ch][2]) for ch in "TEB"},
           "max_abs_sky_q_over_E": float(np.max(np.abs(h["q_over_E_sky"][0]))),
           "max_abs_fluid_q_over_E": float(np.max(np.abs(h["q_over_E_fluid"][0]))),
           "max_abs_pi_sky_minus_fluid": float(np.max(np.abs(h["pi_over_E_sky"][0] - h["pi_over_E_fluid"][0]))),
           "picard_iterations_used": out.picard_iterations_used,
           "picard_pi_local_rel_change": out.picard_pi_local_rel_change}
    if family != "FLRW" and cells % 48 == 0:
        common = h["N_end"][cells // 48 - 1::cells // 48]
        samples = nested_samples(common, h["N_end"], h["q_over_E_sky"][0], h["q_over_E_fluid"][0])
        rel = np.array([s["relative_norm"] for s in samples])
        par = [float(np.dot(s["sky_minus_fluid"], s["fluid"]) / np.linalg.norm(s["fluid"]) ** 2) for s in samples[:2]]
        rec.update(first_two_ln_a=common[:2].tolist(), first_two_relative=rel[:2].tolist(),
                   first_two_signed_parallel=par, first_two_sky_minus_fluid=[s["sky_minus_fluid"] for s in samples[:2]],
                   max_common_relative=float(rel.max()), argmax_common_ln_a=float(common[int(rel.argmax())]),
                   final_relative=float(rel[-1]), median_common_relative=float(np.median(rel)))
    return rec


def tasks():
    out = []
    for staged in (True, False):
        for cap in CAPS:
            for cells in (48, 96, 192, 384):
                out.append(("VI_-1/9", cells, cap, staged))
        out.append(("VI_-1/9", 768, 0.25, staged))
    out.append(("FLRW", 96, 1.0, True))
    for fam in ("VII_h", "IX"):
        for cap in (1.0, 0.25):
            for cells in (96, 192, 384):
                out.append((fam, cells, cap, True))
    return sorted(out, key=lambda t: -t[1] / t[2])


def fit(records):
    table = {}
    for staged in (True, False):
        for cells in (48, 96, 192, 384):
            rows = {r["cap"]: r for r in records if r["family"] == "VI_-1/9" and r["n_cells"] == cells
                    and r["stage_rate_collision"] == staged}
            if set(CAPS) <= set(rows):
                out = {}
                for i in range(2):
                    e1, e2 = rows[1.0]["first_two_signed_parallel"][i], rows[0.5]["first_two_signed_parallel"][i]
                    a = (e1 - e2) / (1.0 - 0.25)
                    b = e1 - a
                    out[f"endpoint_{i}"] = {"A": a, "B": b, "predicted_cap_0.25": a * 0.0625 + b,
                                            "measured_cap_0.25": rows[0.25]["first_two_signed_parallel"][i]}
                table[f"{'R106' if staged else 'R105'}_{cells}"] = out
    return table


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(a.workers, max_tasks_per_child=1) as pool:
        records = list(pool.map(run, tasks()))
    solver = Path(coupled.__file__)
    result = {"schema": "htt.r106.solver_stage_rate/1",
              "git_head": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip(),
              "solver_sha256": hashlib.sha256(solver.read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "settings": {"epsilon": 2e-4, "ell_max": 4, "gl_rings": 16, "n_picard": 4, "min_substeps": 2, "f_nu": 0.0},
              "elapsed_s": time.perf_counter() - t0, "workers": a.workers, "runs": records,
              "cap_fit_signed_parallel": fit(records),
              "classification": "numerical convergence; no physical attribution",
              "units": {"q_over_E": "dimensionless", "C2": "dimensionless bolometric (Delta T/T)^2"}}
    a.output.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()

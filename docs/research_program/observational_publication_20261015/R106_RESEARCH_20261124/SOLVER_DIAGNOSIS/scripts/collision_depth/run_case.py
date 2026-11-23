"""R106 H1 probe: one VI_-1/9 coupled solve at fixed cells and max_substep_depth (config only).

Runs the UNMODIFIED repo solver (bass.transport.coupled_einstein_boltzmann at the
checked-out revision) with the R105 common-time settings, changing only
``max_substep_depth``. Per-substep optical depths of the final Picard sweep are
recomputed afterwards from the returned final recombination history with the
solver's own ``_optical_substeps`` (no wrapper, no monkeypatch).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
from time import perf_counter

import numpy as np

from bass.transport import coupled_einstein_boltzmann as coupled
from scripts.r105.native_optical_refinement import angular_basis
from scripts.r105.solver_axes import identity

FAMILY = "VI_-1/9"
COARSE = 48
ROOT = Path(coupled.__file__).resolve().parents[3]


def parse_cap(text):
    return None if text.lower() == "none" else float(text)


def git(*args):
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()
    except Exception as err:  # provenance only
        return f"unavailable: {err}"


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cells", type=int, required=True)
    p.add_argument("--cap", type=parse_cap, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if a.cells % COARSE:
        raise SystemExit("cells must be a multiple of 48 for exact common endpoints")
    cfg = coupled.CoupledSolverConfig(
        n_cells=a.cells, ell_max=4, n_picard=4, max_substep_depth=a.cap,
        epsilon=2e-4, substeps_per_cell=2, record_history=True,
    )
    t0 = perf_counter()
    out = coupled.solve_coupled_einstein_boltzmann(FAMILY, cfg, lie_op=angular_basis(4, 16))
    wall = perf_counter() - t0

    iters = out.history["picard_iterations"]
    h = iters[-1]
    stride = a.cells // COARSE
    common_idx = [stride - 1, 2 * stride - 1]

    # Exact per-substep depths of the final sweep (same opacity object as the final Picard
    # photon sweep: recomb_hist.opacity_history() of the last iteration).
    opacity = out.recombination.opacity_history()
    N_eval = np.asarray(out.trajectory.N_grid)
    sub_max, sub_min, sub_n = [], [], []
    for cell in range(a.cells):
        if float(h["delta_tau"][cell]) > 0.0:
            _, d = coupled._optical_substeps(opacity, float(N_eval[2 * cell]), float(N_eval[2 * cell + 2]),
                                             cfg.substeps_per_cell, cfg.max_substep_depth)
            sub_max.append(float(np.max(d)))
            sub_min.append(float(np.min(d)))
            sub_n.append(int(len(d)))
        else:
            sub_max.append(0.0)
            sub_min.append(0.0)
            sub_n.append(int(cfg.substeps_per_cell))
    substep_count_matches_history = bool(np.array_equal(np.asarray(sub_n), np.asarray(h["photon_substeps"])))

    per_iter = []
    for k, it in enumerate(iters):
        per_iter.append({
            "picard": k,
            "common": [{"ln_a": float(it["N_end"][i]), "cell_index": int(i),
                        "q_sky": it["q_over_E_sky"][0, i].tolist(),
                        "q_fluid": it["q_over_E_fluid"][0, i].tolist()} for i in common_idx],
        })

    sha = identity()
    sha["sha256"][Path(__file__).name] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    payload = {
        "schema": "htt.r106.collision_depth.case.1",
        "family": FAMILY,
        "config": {"n_cells": a.cells, "ell_max": 4, "gl_rings": 16, "n_picard": 4, "epsilon": 2e-4,
                   "substeps_per_cell": 2, "max_substep_depth": a.cap, "massless_neutrino_fraction": 0.0,
                   "stage_velocity_collision": cfg.stage_velocity_collision,
                   "include_moving_correction": cfg.include_moving_correction},
        "git_head": git("rev-parse", "HEAD"),
        "solver_file_clean_vs_head": git("diff", "--quiet", "HEAD", "--",
                                         "htt/bass/transport/coupled_einstein_boltzmann.py") == "",
        "solver_module_file": str(Path(coupled.__file__).resolve()),
        "provenance": sha,
        "wall_s_solve": wall,
        "worker_peak_RSS_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "final": {
            "N_end": h["N_end"].tolist(),
            "delta_tau": h["delta_tau"].tolist(),
            "photon_substeps": h["photon_substeps"].tolist(),
            "substep_depth_max": sub_max,
            "substep_depth_min": sub_min,
            "substep_count_matches_history": substep_count_matches_history,
            "hamiltonian": h["hamiltonian"].tolist(),
            "codazzi": h["codazzi"].tolist(),
            "q_over_E_sky": h["q_over_E_sky"][0].tolist(),
            "q_over_E_fluid": h["q_over_E_fluid"][0].tolist(),
            "pi_over_E_sky_common": [h["pi_over_E_sky"][0, i].tolist() for i in common_idx],
            "pi_over_E_fluid_common": [h["pi_over_E_fluid"][0, i].tolist() for i in common_idx],
            "thomson_force_over_E_sky": h["thomson_force_over_E_sky"].tolist(),
            "thomson_force_over_E_fluid": h["thomson_force_over_E_fluid"].tolist(),
        },
        "picard_common": per_iter,
        "C2": {ch: float(out.cl_final[ch][2]) for ch in ("T", "E", "B", "V")},
        "max_hamiltonian": float(out.max_hamiltonian_residual),
        "max_codazzi": float(out.max_codazzi_residual),
        "max_jacobi": float(out.max_jacobi_residual),
        "max_stokes_reality_err": float(out.max_stokes_reality_err),
        "picard_pi_rel_change": float(out.picard_pi_rel_change),
        "total_optical_depth": float(out.total_optical_depth),
        "env": {k: os.getenv(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                                          "PYTHONPATH")},
        "argv": sys.argv,
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    tmp = a.output.with_suffix(".tmp")
    tmp.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")
    tmp.replace(a.output)
    q = np.asarray(h["q_over_E_sky"][0]) - np.asarray(h["q_over_E_fluid"][0])
    rel = np.linalg.norm(q, axis=1) / np.linalg.norm(np.asarray(h["q_over_E_fluid"][0]), axis=1)
    print(f"cells={a.cells} cap={a.cap} wall={wall:.1f}s rel_first={rel[common_idx[0]]:.6e} "
          f"rel_second={rel[common_idx[1]]:.6e} substeps={int(np.sum(sub_n))} match={substep_count_matches_history}")


if __name__ == "__main__":
    main()

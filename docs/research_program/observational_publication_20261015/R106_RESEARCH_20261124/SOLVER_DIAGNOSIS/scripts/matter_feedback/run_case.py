"""R106 H3 matter-feedback case runner (VI_-1/9, R105 common-time protocol).

One solver run per process. Loads either the unmodified repo solver or the
matter-feedback variant copy (variants/coupled_matter_feedback_variant.py),
then records the final-Picard photon sky-vs-fluid q/E at the first two
48-cell common endpoints, the worst cell, constraints, C_2 and per-Picard
first-common residuals.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
VARIANT = HERE / "variants" / "coupled_matter_feedback_variant.py"

from bass.transport import coupled_einstein_boltzmann as repo_solver  # noqa: E402
from scripts.r105.native_optical_refinement import angular_basis  # noqa: E402
from scripts.r105.common_time_moments import nested_samples  # noqa: E402

FAMILY = "VI_-1/9"
COARSE = 48


def load_variant():
    name = "r106_matter_feedback_variant"
    spec = importlib.util.spec_from_file_location(name, VARIANT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    mod.HYREC_REF_CSV = repo_solver.HYREC_REF_CSV
    return mod


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def common_endpoints(n_start):
    # 48-cell endpoints exactly as the solver forms them.
    return np.linspace(n_start, 0.0, 2 * COARSE + 1, dtype=np.float64)[2::2]


def sample_iteration(hist, common):
    edges = hist["N_end"]
    sky = hist["q_over_E_sky"][0]
    fluid = hist["q_over_E_fluid"][0]
    samples = nested_samples(common, edges, sky, fluid)
    return samples


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--label", required=True)
    ap.add_argument("--solver", choices=("repo", "variant"), required=True)
    ap.add_argument("--n-cells", type=int, required=True)
    ap.add_argument("--n-picard", type=int, default=4)
    ap.add_argument("--max-depth", type=float, default=1.0)
    ap.add_argument("--pi-einstein-euler", type=int, default=1)
    ap.add_argument("--pi-thomson", type=int, default=1)
    ap.add_argument("--midpoint-pi", choices=("average", "half_cell"), default="average")
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()

    if a.solver == "repo":
        mod = repo_solver
        switches = None
    else:
        mod = load_variant()
        mod.PI_FEEDBACK_EINSTEIN_EULER = bool(a.pi_einstein_euler)
        mod.PI_FEEDBACK_THOMSON = bool(a.pi_thomson)
        mod.MIDPOINT_PI = a.midpoint_pi
        switches = {"PI_FEEDBACK_EINSTEIN_EULER": mod.PI_FEEDBACK_EINSTEIN_EULER,
                    "PI_FEEDBACK_THOMSON": mod.PI_FEEDBACK_THOMSON, "MIDPOINT_PI": mod.MIDPOINT_PI}

    cfg = mod.CoupledSolverConfig(n_cells=a.n_cells, ell_max=4, n_picard=a.n_picard,
                                  max_substep_depth=a.max_depth, epsilon=2e-4, substeps_per_cell=2,
                                  record_history=True)
    t0 = time.perf_counter()
    res = mod.solve_coupled_einstein_boltzmann(FAMILY, cfg, lie_op=angular_basis(4, 16))
    wall = time.perf_counter() - t0
    iters = res.history["picard_iterations"]
    hist = iters[-1]
    n_start = -math.log1p(cfg.z_initial)
    common = common_endpoints(n_start)
    samples = sample_iteration(hist, common)
    stride = a.n_cells // COARSE

    sky = hist["q_over_E_sky"][0]
    fluid = hist["q_over_E_fluid"][0]
    err = np.linalg.norm(sky - fluid, axis=1)
    scale = np.linalg.norm(fluid, axis=1)
    rel = np.divide(err, scale, out=np.full_like(err, np.nan), where=scale > 0)
    worst = int(np.nanargmax(rel))

    def cellinfo(i):
        return {"cell_index": i, "ln_a": float(hist["N_end"][i]), "delta_tau": float(hist["delta_tau"][i]),
                "photon_substeps": int(hist["photon_substeps"][i]), "relative_norm": float(rel[i]),
                "sky_minus_fluid": (sky[i] - fluid[i]).tolist(),
                "pi_over_E_sky": hist["pi_over_E_sky"][0][i].tolist(),
                "pi_over_E_fluid": hist["pi_over_E_fluid"][0][i].tolist(),
                "hamiltonian": float(hist["hamiltonian"][i]), "codazzi": float(hist["codazzi"][i])}

    first_idx = stride - 1
    # Baryon velocity at the first common endpoint (N_eval index 2*cell+2) for the
    # tight-coupling equilibrium q/E = (1+1/3) v + (pi/E).v + O(v^2) diagnostics.
    vb_first = np.asarray(res.trajectory.species_v_grid["baryon"][2 * first_idx + 2])
    assert res.trajectory.N_grid[2 * first_idx + 2] == common[0]
    pi_sky_f = np.asarray(hist["pi_over_E_sky"][0][first_idx])
    pi_fl_f = np.asarray(hist["pi_over_E_fluid"][0][first_idx])
    equilibrium = {"v_b": vb_first.tolist(), "four_thirds_v_b": (4 / 3 * vb_first).tolist(),
                   "pi_sky_dot_v_b": (pi_sky_f @ vb_first).tolist(),
                   "pi_fluid_dot_v_b": (pi_fl_f @ vb_first).tolist(),
                   "sky_minus_eq_sky": (sky[first_idx] - 4 / 3 * vb_first - pi_sky_f @ vb_first).tolist(),
                   "fluid_minus_eq_fluid": (fluid[first_idx] - 4 / 3 * vb_first - pi_fl_f @ vb_first).tolist()}
    per_picard = []
    for k, h in enumerate(iters):
        s = sample_iteration(h, common)
        per_picard.append({"iteration": k, "first_relative": s[0]["relative_norm"],
                           "first_sky_minus_fluid": s[0]["sky_minus_fluid"],
                           "first_sky": s[0]["sky"], "first_fluid": s[0]["fluid"],
                           "second_relative": s[1]["relative_norm"],
                           "pi_over_E_sky_first": h["pi_over_E_sky"][0][first_idx].tolist(),
                           "pi_over_E_fluid_first": h["pi_over_E_fluid"][0][first_idx].tolist()})

    out = {
        "schema": "htt.r106.matter_feedback_case.1",
        "label": a.label, "solver": a.solver, "family": FAMILY,
        "config": {"n_cells": a.n_cells, "ell_max": 4, "gl_rings": 16, "n_picard": a.n_picard,
                   "max_substep_depth": a.max_depth, "epsilon": 2e-4, "substeps_per_cell": 2,
                   "massless_neutrino_fraction": 0.0, "variant_switches": switches},
        "sha256": {"repo_solver": sha(repo_solver.__file__), "variant_solver": sha(VARIANT),
                   "run_case.py": sha(__file__), "solver_loaded": sha(mod.__file__)},
        "solver_file": str(mod.__file__),
        "first_common": {"ln_a": float(common[0]), **samples[0],
                         "pi_over_E_sky": hist["pi_over_E_sky"][0][first_idx].tolist(),
                         "pi_over_E_fluid": hist["pi_over_E_fluid"][0][first_idx].tolist(),
                         "thomson_force_over_E_sky": hist["thomson_force_over_E_sky"][first_idx].tolist(),
                         "thomson_force_over_E_fluid": hist["thomson_force_over_E_fluid"][first_idx].tolist(),
                         "delta_tau": float(hist["delta_tau"][first_idx]),
                         "photon_substeps": int(hist["photon_substeps"][first_idx])},
        "first_common_tight_coupling": equilibrium,
        "second_common": {"ln_a": float(common[1]), **samples[1]},
        "common_relative_all48": [s["relative_norm"] for s in samples],
        "worst_cell": cellinfo(worst),
        "native_first_cell": cellinfo(0),
        "per_picard": per_picard,
        "max_hamiltonian": float(res.max_hamiltonian_residual),
        "max_codazzi": float(res.max_codazzi_residual),
        "max_jacobi": float(res.max_jacobi_residual),
        "max_stokes_reality": float(res.max_stokes_reality_err),
        "picard_pi_rel_change": float(res.picard_pi_rel_change),
        "C2": {k: float(res.cl_final[k][2]) for k in ("T", "E", "B")},
        "total_optical_depth": float(res.total_optical_depth),
        "wall_s": wall,
        "env": {k: os.environ.get(k) for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
                                               "PYTHONDONTWRITEBYTECODE")},
    }
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    np.savez_compressed(a.output.with_suffix(".npz"), N_end=hist["N_end"], delta_tau=hist["delta_tau"],
                        photon_substeps=hist["photon_substeps"], q_sky=sky, q_fluid=fluid,
                        pi_sky=hist["pi_over_E_sky"][0], pi_fluid=hist["pi_over_E_fluid"][0],
                        hamiltonian=hist["hamiltonian"], codazzi=hist["codazzi"])
    print(f"{a.label}: first_rel={samples[0]['relative_norm']:.6e} second_rel={samples[1]['relative_norm']:.6e} "
          f"worst={worst} rel={rel[worst]:.3e} wall={wall:.1f}s")


if __name__ == "__main__":
    main()

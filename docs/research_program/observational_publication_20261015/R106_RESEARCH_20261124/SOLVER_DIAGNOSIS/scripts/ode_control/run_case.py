"""One H5 control run: repo R105 solver or the read-only-instrumented variant with chosen Radau tolerances.

Settings are the R105 common-time measurement (scripts/r105/common_time_moments.py):
VI_-1/9, epsilon 2e-4, ell_max 4, GL rings 16, n_picard 4, substeps_per_cell 2, max_substep_depth 1.0, f_nu 0.
Writes <output>.npz (full final-Picard history arrays) and <output>.json (summary + identity).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
import scipy

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
VARIANT = HERE / "coupled_h5_variant.py"

from bass.transport import coupled_einstein_boltzmann as repo_solver  # noqa: E402
from scripts.r105.native_optical_refinement import angular_basis  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_variant():
    name = "h5_coupled_variant_mod"
    spec = importlib.util.spec_from_file_location(name, VARIANT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses need the module registered before exec
    spec.loader.exec_module(mod)
    mod.HYREC_REF_CSV = repo_solver.HYREC_REF_CSV
    return mod


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--solver", choices=("repo", "variant"), required=True)
    ap.add_argument("--cells", type=int, required=True)
    ap.add_argument("--rtol", type=float, default=1e-10)
    ap.add_argument("--atol", type=float, default=1e-13)
    ap.add_argument("--family", default="VI_-1/9")
    ap.add_argument("--epsilon", type=float, default=2e-4)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    if args.solver == "repo":
        if (args.rtol, args.atol) != (1e-10, 1e-13):
            ap.error("the repo solver has hard-coded rtol 1e-10 / atol 1e-13")
        mod = repo_solver
    else:
        mod = load_variant()
        mod.RADAU_RTOL = float(args.rtol)
        mod.RADAU_ATOL = float(args.atol)

    cfg = mod.CoupledSolverConfig(
        n_cells=args.cells, ell_max=4, n_picard=4, max_substep_depth=1.0,
        epsilon=args.epsilon, substeps_per_cell=2, record_history=True,
        massless_neutrino_fraction=0.0,
    )
    t0 = time.perf_counter()
    res = mod.solve_coupled_einstein_boltzmann(args.family, cfg, lie_op=angular_basis(4, 16))
    wall = time.perf_counter() - t0
    hist = res.history["picard_iterations"][-1]
    arrays = {k: np.asarray(v) for k, v in hist.items()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    np.savez(args.output.with_suffix(".npz"), **arrays)
    summary = {
        "schema": "htt.r106.h5_ode_control.run.1",
        "solver": args.solver, "family": args.family, "epsilon": args.epsilon, "n_cells": args.cells,
        "rtol": args.rtol, "atol": args.atol, "ell_max": 4, "gl_rings": 16, "n_picard": 4,
        "substeps_per_cell": 2, "max_substep_depth": 1.0, "massless_neutrino_fraction": 0.0,
        "solve_wall_s": wall,
        "C2": {ch: float(res.cl_final[ch][2]) for ch in ("T", "E", "B")},
        "max_hamiltonian": float(res.max_hamiltonian_residual),
        "max_codazzi": float(res.max_codazzi_residual),
        "max_jacobi": float(res.max_jacobi_residual),
        "max_stokes_reality": float(res.max_stokes_reality_err),
        "max_four_force_orthog_error": float(res.max_four_force_orthog_error),
        "picard_pi_rel_change": float(res.picard_pi_rel_change),
        "total_optical_depth": float(res.total_optical_depth),
        "n_rhs_evals_final_picard": int(res.trajectory.n_rhs_evals),
        "final_state_sha256": hashlib.sha256(np.ascontiguousarray(res.final_state).tobytes()).hexdigest(),
        "history_sha256": {k: hashlib.sha256(np.ascontiguousarray(v).tobytes()).hexdigest() for k, v in arrays.items()},
        "identity": {
            "solver_file": str(Path(mod.__file__)), "solver_sha256": sha(Path(mod.__file__)),
            "repo_solver_sha256": sha(Path(repo_solver.__file__)),
            "hyrec_csv": str(repo_solver.HYREC_REF_CSV), "hyrec_csv_sha256": sha(repo_solver.HYREC_REF_CSV),
            "run_case_sha256": sha(Path(__file__)),
            "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
            "OPENBLAS_NUM_THREADS": os.getenv("OPENBLAS_NUM_THREADS"), "pid": os.getpid(),
        },
        "ru_maxrss_kB_self": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.with_suffix(".json").write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("solver", "n_cells", "rtol", "atol", "solve_wall_s", "C2")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

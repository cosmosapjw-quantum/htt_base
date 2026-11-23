"""One-axis refinement of the coupled solver with sky-dipole versus fluid q/E per species.

Each run starts from the same VII_h, VI_-1/9 or IX initial data. Exactly one of
(time cells, Picard sweeps, ell_max, Gauss-Legendre rings) changes relative to the
baseline. ``--reference-solver`` loads a frozen solver file (for example the R103
source written by ``git show``) so the time-cell axis can be compared before/after.

Units: q/E and pi/E are dimensionless normal-frame ratios; Thomson force/E is per
e-fold (d ln a); C_ell are dimensionless (Delta T/T)^2 of the bolometric brightness.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import resource
import subprocess
import time

import numpy as np
import scipy

FAMILIES = ("VII_h", "VI_-1/9", "IX")
BASE = {"cells": 48, "picard": 3, "ell": 6, "ngl": 16}
AXES = {"cells": (24, 48, 96, 192), "picard": (2, 3, 4, 6), "ell": (4, 6, 8, 10), "ngl": (10, 16, 24, 32)}
COARSE_CELLS = 24  # every swept time grid nests the 24-cell edges


def neutrino_fraction(n_eff):
    per = (7.0 / 8.0) * (4.0 / 11.0) ** (4.0 / 3.0) * float(n_eff)
    return per / (1.0 + per)


def _solver(reference):
    if reference is None:
        from bass.transport import coupled_einstein_boltzmann as mod
        return mod
    import sys
    name = "r104_reference_solver"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, reference)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod  # dataclasses resolve their defining module
        spec.loader.exec_module(mod)
        # The frozen copy lives outside the tree; bind its fixture to this checkout.
        from bass.transport import coupled_einstein_boltzmann as live
        mod.HYREC_REF_CSV = live.HYREC_REF_CSV
    return sys.modules[name]


def _sky_ratio(state, op):
    from bass.transport.general_lie_stokes import vector_to_stokes_maps
    sky = vector_to_stokes_maps(np.asarray(state), op.idx, L=op.L, n_gl_theta=op.n_gl_theta)
    n = op._grid[2].reshape(-1, 3)
    w = op._grid[3].ravel() * (1.0 + 4.0 * sky[..., 0].ravel())
    k4 = np.column_stack([np.ones(len(n)), -n])
    t = np.einsum("n,ni,nj->ij", w, k4, k4)
    return t / t[0, 0]


def run(task):
    if len(task) == 7:  # (..., base override)
        BASE.update(task[6])
        task = task[:6]
    try:
        return _run(task)
    except Exception as exc:  # keep the other runs; record the failing input
        return {"family": task[0], "axis": task[1], "value": task[2], "solver": "R103_reference" if task[5] else "R104",
                "error": f"{type(exc).__name__}: {exc}"}


def _run(task):
    family, axis, value, epsilon, f_nu, reference = task
    params = dict(BASE)
    if axis in AXES:
        params[axis] = value
    mod = _solver(reference)
    from bass.background.geometry import pstf_rank2
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator
    op = GeneralLieStokesOperator(params["ell"], n_gl_theta=max(params["ngl"], params["ell"] + 4))
    kwargs = dict(ell_max=params["ell"], n_cells=params["cells"], n_picard=params["picard"], epsilon=epsilon,
                  massless_neutrino_fraction=f_nu)
    has_history = "record_history" in mod.CoupledSolverConfig.__dataclass_fields__
    if has_history:
        kwargs["record_history"] = True
    t0 = time.perf_counter()
    out = mod.solve_coupled_einstein_boltzmann(family, mod.CoupledSolverConfig(**kwargs), lie_op=op)
    wall = time.perf_counter() - t0
    rec = {"family": family, "axis": axis, "value": value, "params": params, "epsilon": epsilon,
           "massless_neutrino_fraction": f_nu, "solver": "R103_reference" if reference else "R104",
           "n_gl_theta_used": op.n_gl_theta,
           "wall_s": wall, "maxrss_kB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "max_hamiltonian": out.max_hamiltonian_residual, "max_codazzi": out.max_codazzi_residual,
           "max_jacobi": out.max_jacobi_residual, "picard_pi_rel_change": out.picard_pi_rel_change,
           "tau_anchor": out.total_optical_depth,
           "cl": {ch: out.cl_final[ch][: params["ell"] + 1].tolist() for ch in ("T", "E", "B", "V")}}
    traj = out.trajectory
    species = [s.species for s in traj.species_specs]
    final = {}
    states = {"radiation": out.final_state, "neutrino": out.neutrino_final_state}
    for name in ("radiation", "neutrino"):
        if name in species and states[name] is not None:
            sky = _sky_ratio(states[name], op)
            v = traj.species_v_grid[name][-1]
            final[name] = {"q_over_E_sky": sky[0, 1:].tolist(),
                           "q_over_E_fluid": (4.0 * v / (3.0 + v @ v)).tolist(),
                           "pi_over_E_sky": pstf_rank2(sky[1:, 1:]).tolist()}
    rec["final_species"] = final
    if has_history:
        hist = out.history["picard_iterations"][-1]
        stride = params["cells"] // COARSE_CELLS if params["cells"] % COARSE_CELLS == 0 else None
        per = {}
        for slot, name in enumerate(out.history["radiation_species"]):
            qs, qf = hist["q_over_E_sky"][slot], hist["q_over_E_fluid"][slot]
            rel = np.linalg.norm(qs - qf, axis=1) / np.maximum(np.linalg.norm(qf, axis=1), 1e-300)
            first = int(np.argmax(rel > 1e-3)) if np.any(rel > 1e-3) else None
            entry = {"max_rel_q_mismatch": float(rel.max()), "final_rel_q_mismatch": float(rel[-1]),
                     "first_cell_rel_gt_1e-3": first,
                     "first_cell_N_end": None if first is None else float(hist["N_end"][first]),
                     "final_pi_over_E_sky": hist["pi_over_E_sky"][slot][-1].tolist(),
                     "final_pi_over_E_fluid": hist["pi_over_E_fluid"][slot][-1].tolist()}
            if stride:
                idx = np.arange(1, COARSE_CELLS + 1) * stride - 1
                entry["nested_N_end"] = hist["N_end"][idx].tolist()
                entry["nested_rel_q_mismatch"] = rel[idx].tolist()
                entry["nested_q_over_E_sky"] = qs[idx].tolist()
                entry["nested_q_over_E_fluid"] = qf[idx].tolist()
            per[name] = entry
        fs, ff = hist["thomson_force_over_E_sky"], hist["thomson_force_over_E_fluid"]
        rec["history"] = {"species": per,
                          "max_abs_force_sum_baryon_fluid_plus_photon_sky": float(np.max(np.linalg.norm(fs - ff, axis=1))),
                          "max_abs_force_fluid": float(np.max(np.linalg.norm(ff, axis=1))),
                          "max_hamiltonian_cell_end": float(hist["hamiltonian"].max()),
                          "max_codazzi_cell_end": float(hist["codazzi"].max())}
    return rec


def tasks(epsilon, reference, n_eff):
    out = []
    for fam in FAMILIES:
        out.append((fam, "baseline", None, epsilon, 0.0, None))
        for axis, values in AXES.items():
            for v in values:
                if v != BASE[axis]:
                    out.append((fam, axis, v, epsilon, 0.0, None))
        out.append((fam, "neutrino", n_eff, epsilon, neutrino_fraction(n_eff), None))
        if reference:
            for v in AXES["cells"]:
                out.append((fam, "cells", v, epsilon, 0.0, str(reference)))
    # Longest jobs first keeps the pool busy.
    return sorted(out, key=lambda t: -(t[2] if t[1] in ("cells", "ell") and t[2] else 0))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--workers", type=int, default=8)
    p.add_argument("--epsilon", type=float, default=2e-4)
    p.add_argument("--n-eff", type=float, default=3.044)
    p.add_argument("--reference-solver", type=Path)
    p.add_argument("--cells-only", type=int, nargs="+", help="supplementary time-cell axis at --base-picard")
    p.add_argument("--base-picard", type=int, default=BASE["picard"])
    a = p.parse_args()
    ref = a.reference_solver.resolve() if a.reference_solver else None
    if a.cells_only:
        BASE["picard"] = a.base_picard
        todo = [(fam, "cells", c, a.epsilon, 0.0, None, {"picard": a.base_picard})
                for c in sorted(a.cells_only, reverse=True) for fam in FAMILIES]
    else:
        todo = tasks(a.epsilon, ref, a.n_eff)
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        runs = list(pool.map(run, todo))
    head = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    solver_path = Path(__file__).resolve().parents[2] / "htt/bass/transport/coupled_einstein_boltzmann.py"
    result = {"schema": "htt.r104.solver_axis_sweep/1", "git_head_before_commit": head,
              "solver_sha256": hashlib.sha256(solver_path.read_bytes()).hexdigest(),
              "reference_solver_sha256": hashlib.sha256(ref.read_bytes()).hexdigest() if ref else None,
              "baseline": BASE, "axes": AXES, "families": FAMILIES, "epsilon": a.epsilon,
              "units": {"q_over_E": "dimensionless T^{0i}/T^{00}", "force_over_E": "per e-fold",
                        "cl": "dimensionless bolometric (Delta T/T)^2"},
              "python": platform.python_version(), "numpy": np.__version__, "scipy": scipy.__version__,
              "OPENBLAS_NUM_THREADS": os.getenv("OPENBLAS_NUM_THREADS"), "workers": a.workers,
              "elapsed_s": time.perf_counter() - t0, "runs": runs,
              "physical_Pi": None, "Bianchi_family_attribution": None}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()

"""Choose the R106 photon-collision scheme: pure damping, analytic ramp and full-solver closure.

Schemes: R105 (substep-average rate) and R106 (stage-time rate rescaled to the exact
substep depth) with |Delta ln r| substep bounds None/0.5/0.25/0.125, all at depth cap 1.
(a) pure Thomson damping of an ell=3 temperature mode (zero geometry, v=0) through a
captured VI_-1/9 48-cell opacity history against exp(-tau); (b) the analytic tight-
coupling ramp a' = R(u)(beta - a); (c) VI_-1/9 coupled runs (R105 settings) at 48/96/192
cells: sky-minus-fluid photon q/E over all 48-cell common endpoints and C_ell (ell 2,3)
against an R106 384-cell cap-0.25 reference. Units: transmission ratios and q/E are
dimensionless; C_ell is dimensionless bolometric (Delta T/T)^2.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import math
from pathlib import Path
import pickle
import time

import numpy as np
from scipy.special import exp1

from bass.recombination.opacity_history import OpacityHistory
from bass.transport import coupled_einstein_boltzmann as cb
from bass.transport.general_lie_stokes import GeneralLieStokesOperator, LieGeometry
from scripts.r105.common_time_moments import nested_samples
from scripts.r105.native_optical_refinement import angular_basis

ZERO = LieGeometry(np.zeros((3, 3)), np.zeros(3), np.zeros((3, 3)))
SCHEMES = {"R105": (False, None), "R106_lr_none": (True, None), "R106_lr0.5": (True, 0.5),
           "R106_lr0.25": (True, 0.25), "R106_lr0.125": (True, 0.125)}


def pure_damping(opacity_pkl):
    d = pickle.load(open(opacity_pkl, "rb"))
    opacity = OpacityHistory(d["opacity_N"], d["opacity_rate"])
    op = GeneralLieStokesOperator(4, n_gl_theta=16)
    i3 = op.idx["T"][3, 0]
    out = {}
    for name, (staged, lr) in SCHEMES.items():
        rows, nsub = [], 0
        for n0, n1 in d["cells"]:
            edges, depths = cb._optical_substeps(opacity, n0, n1, 2, 1.0, lr if staged else None)
            y0 = np.zeros(op.dim, complex)
            y0[i3] = 1.0
            y = cb._advance_moving_photon_cell(op, y0, n1 - n0, ZERO, np.zeros(op.dim, complex), depths,
                                               lambda u: np.zeros(3), sub_edges=edges,
                                               opacity_rate_at=cb._stage_opacity_rate(opacity, n0, n1) if staged else None)
            rows.append((float(np.sum(depths)), float(y[i3].real)))
            nsub += len(depths)
        tau = np.array([r[0] for r in rows])
        trans = np.array([r[1] for r in rows])
        tau_obs = np.cumsum(tau[::-1])[::-1]
        cum = {}
        for start in (2.0, 0.5, 0.1):
            i = int(np.argmax(tau_obs < start))
            cum[f"from_tau_obs_lt_{start}"] = float(np.sum(np.log(np.abs(trans[i:]))) + np.sum(tau[i:]))
        visible = tau > 1e-7
        out[name] = {"total_substeps": nsub, "cumulative_dlnT": cum,
                     "max_abs_cell_rel_error_tau_lt_1": float(np.max(np.abs(trans[visible & (tau < 1)] / np.exp(-tau[visible & (tau < 1)]) - 1)))}
    return {"opacity_pickle_sha256": hashlib.sha256(Path(opacity_pkl).read_bytes()).hexdigest(), "schemes": out}


def ramp():
    op = GeneralLieStokesOperator(2, n_gl_theta=8)
    out = {}
    for label, r0, k in (("first_endpoint_analogue", 0.3 * 98.4 * math.exp(1.65), 1.65),
                         ("second_endpoint_analogue", 0.3 * 29.46 * math.exp(2.88), 2.88)):
        nodes = np.linspace(0, 1, 4001)
        opacity = OpacityHistory(nodes, r0 * np.exp(-k * nodes))
        w1, w0 = (r0 / k) * math.exp(-k), r0 / k
        vf = 1e-8
        exact = vf * (1 - math.exp(-(w0 - w1)) * math.exp(w0) / k * (exp1(w1) - exp1(w0)))
        for name, (staged, lr) in SCHEMES.items():
            errs = []
            for cap in (1.0, 0.5, 0.25):
                edges, depths = cb._optical_substeps(opacity, 0., 1., 2, cap, lr if staged else None)
                st = cb._advance_moving_photon_cell(op, np.zeros(op.dim, complex), 1., ZERO, np.zeros(op.dim, complex),
                                                    depths, lambda u: np.array([0, 0, vf * u]), sub_edges=edges,
                                                    opacity_rate_at=cb._stage_opacity_rate(opacity, 0., 1.) if staged else None)
                meas = -st[op.idx["T"][1, 0]].real / math.sqrt(4 * math.pi / 3)
                errs.append((meas - exact) / (exact - vf))
            out[f"{label}|{name}"] = errs
    return out


def solve(task):
    name, cells, cap = task
    staged, lr = SCHEMES[name]
    cfg = cb.CoupledSolverConfig(n_cells=cells, ell_max=4, n_picard=4, max_substep_depth=cap, epsilon=2e-4,
                                 substeps_per_cell=2, record_history=True, stage_rate_collision=staged,
                                 max_substep_log_rate=lr)
    t0 = time.perf_counter()
    out = cb.solve_coupled_einstein_boltzmann("VI_-1/9", cfg, lie_op=angular_basis(4, 16))
    h = out.history["picard_iterations"][-1]
    common = h["N_end"][cells // 48 - 1::cells // 48]
    s = nested_samples(common, h["N_end"], h["q_over_E_sky"][0], h["q_over_E_fluid"][0])
    rel = np.array([x["relative_norm"] for x in s])
    return {"scheme": name, "n_cells": cells, "cap": cap, "wall_s": time.perf_counter() - t0,
            "total_substeps": int(np.sum(h["photon_substeps"])), "first_two_relative": rel[:2].tolist(),
            "max_relative_common_2_47": float(rel[2:].max()), "median_relative_common_2_47": float(np.median(rel[2:])),
            "C_ell": {ch: out.cl_final[ch][2:4].tolist() for ch in "TEB"},
            "max_hamiltonian": out.max_hamiltonian_residual, "max_codazzi": out.max_codazzi_residual}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--opacity-pickle", type=Path, required=True)
    p.add_argument("--workers", type=int, default=10)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    tasks = [("R106_lr0.25", 384, 0.25)] + [(n, c, 1.0) for c in (192, 96, 48) for n in SCHEMES]
    with ProcessPoolExecutor(a.workers, max_tasks_per_child=1) as pool:
        runs = list(pool.map(solve, tasks))
    ref = runs[0]
    for r in runs[1:]:
        r["C_ell_rel_error_vs_ref"] = {ch: [x / y - 1 for x, y in zip(r["C_ell"][ch], ref["C_ell"][ch])] for ch in "TEB"}
    result = {"schema": "htt.r106.solver_scheme_select/1",
              "solver_sha256": hashlib.sha256(Path(cb.__file__).read_bytes()).hexdigest(),
              "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "pure_damping": pure_damping(a.opacity_pickle), "analytic_ramp_err_over_slip_caps_1_0.5_0.25": ramp(),
              "reference": {k: ref[k] for k in ("scheme", "n_cells", "cap", "C_ell")}, "runs": runs[1:],
              "classification": "numerical convergence; no physical attribution"}
    a.output.write_text(json.dumps(result, indent=1, allow_nan=False) + "\n")


if __name__ == "__main__":
    main()

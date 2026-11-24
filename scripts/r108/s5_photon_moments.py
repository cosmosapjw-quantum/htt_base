"""R108 S5 (SQ-PHOTON-FLUX): photon q/E and pi/E at the 48 R105 common times from three estimators.

VI_-1/9, epsilon 2e-4, ell_max 4, 16 Gauss-Legendre rings, f_nu 0, minimum 2 substeps per
cell (the R105 SOLVER_COMMON_TIMES.json case) with the R106/R108 solver path (stage-rate
collisions, depth cap 0.25, |Delta ln rate| <= 0.25, adaptive Picard from 4 sweeps,
optical-substep source nodes).  Cells 48/96/192/384; the 48 common times are the cell
ends of the 48-cell grid (shared exactly by every multiple of 48).

At each common time three photon moment estimates in the solver normal frame:
  hierarchy  sky_energy_momentum_ratios of the native Stokes state (recorded by the solver),
  fluid      T^{0i}/T^{00} and pstf(T^{ij})/T^{00} of the Einstein-Euler photon fluid,
  LoS        line of sight to a normal observer at that time (history_window), on a
             24-ring Gauss-Legendre sphere projected to ell <= 4, then the same moment map.
Reported: signed vectors, |LoS - hierarchy| and |LoS - fluid| relative to |fluid q|, and
their change with cells.  Units: dimensionless ratios.  No attribution.

Usage: PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m scripts.r108.s5_photon_moments --workers 4
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from scripts.r108.common import OUT_DIR, REPO, maxrss_mb, solver_identity, write_json

COMMON = REPO / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/SOLVER_COMMON_TIMES.json"
CELLS = (48, 96, 192, 384)


def run(cells: int) -> dict:
    from bass.background.geometry import pstf_rank2
    from bass.transport.coupled_einstein_boltzmann import (CoupledSolverConfig, sky_energy_momentum_ratios,
                                                           solve_coupled_einstein_boltzmann)
    from bass.transport.general_bianchi_transfer import gl_sphere_grid
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator, stokes_maps_to_vector
    from bass.transport.hybrid_los_transfer import history_from_coupled_result, history_window, los_sky

    common = json.loads(COMMON.read_text())
    op = GeneralLieStokesOperator(4, n_gl_theta=16)
    cfg = CoupledSolverConfig(n_cells=cells, ell_max=4, n_picard=4, epsilon=float(common["epsilon"]),
                              max_substep_depth=0.25, substeps_per_cell=int(common["min_substeps"]),
                              massless_neutrino_fraction=float(common["neutrino_fraction"]), record_history=True)
    t0 = time.perf_counter()
    res = solve_coupled_einstein_boltzmann(common["family"], cfg, lie_op=op)
    solve_s = time.perf_counter() - t0
    rec = res.history["picard_iterations"][-1]
    slot = list(res.history["radiation_species"]).index("radiation")  # photon species label in the solver
    hist = history_from_coupled_result(res, op=op)
    _, _, d, _ = gl_sphere_grid(24)
    dirs = d.reshape(-1, 3)
    opo = GeneralLieStokesOperator(4, n_gl_theta=16)
    step = cells // 48
    rows = []
    for j, ce in enumerate(common["common_endpoints"]):
        cell = (j + 1) * step - 1
        n_c = float(rec["N_end"][cell])
        if abs(n_c - float(ce["ln_a"])) > 1e-9:
            raise ValueError(f"common time {j} mismatch: {n_c} vs {ce['ln_a']}")
        node = int(np.argmin(np.abs(hist.N - n_c)))
        if abs(hist.N[node] - n_c) > 1e-12:
            raise ValueError("common time is not a history node")
        q_h = np.asarray(rec["q_over_E_sky"][slot, cell])
        q_f = np.asarray(rec["q_over_E_fluid"][slot, cell])
        p_h = np.asarray(rec["pi_over_E_sky"][slot, cell])
        p_f = np.asarray(rec["pi_over_E_fluid"][slot, cell])
        if node == 0:
            continue
        sky = los_sky(history_window(hist, node), dirs, max_step=0.02)
        vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), opo.idx, opo.dim, L=4, n_gl_theta=24)
        t_los = sky_energy_momentum_ratios(vec, opo)
        q_l, p_l = t_los[0, 1:], pstf_rank2(t_los[1:, 1:])
        qn = float(np.linalg.norm(q_f))
        pn = float(np.linalg.norm(p_f))
        rows.append({"j": j, "ln_a": n_c, "cell": cell, "node": node, "delta_tau_cell": float(rec["delta_tau"][cell]),
                     "q_hierarchy": q_h.tolist(), "q_fluid": q_f.tolist(), "q_los": q_l.tolist(),
                     "pi_hierarchy": p_h.tolist(), "pi_fluid": p_f.tolist(), "pi_los": p_l.tolist(),
                     "rel_q_los_minus_hierarchy": float(np.linalg.norm(q_l - q_h)) / qn if qn else None,
                     "rel_q_los_minus_fluid": float(np.linalg.norm(q_l - q_f)) / qn if qn else None,
                     "rel_q_hierarchy_minus_fluid": float(np.linalg.norm(q_h - q_f)) / qn if qn else None,
                     "rel_pi_los_minus_hierarchy": float(np.linalg.norm(p_l - p_h)) / pn if pn else None,
                     "rel_pi_los_minus_fluid": float(np.linalg.norm(p_l - p_f)) / pn if pn else None,
                     "rel_pi_hierarchy_minus_fluid": float(np.linalg.norm(p_h - p_f)) / pn if pn else None})
    return {"n_cells": cells, "solve_seconds": solve_s, "wall_seconds": time.perf_counter() - t0,
            "maxrss_MB": maxrss_mb(), "picard_iterations_used": res.picard_iterations_used,
            "max_hamiltonian": res.max_hamiltonian_residual, "max_codazzi": res.max_codazzi_residual,
            "n_source_nodes": int(hist.N.size), "n_substep_nodes": hist.provenance.get("n_substep_nodes"),
            "rows": rows}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--output", default=str(OUT_DIR / "SOLVER" / "S5_PHOTON_MOMENTS.json"))
    args = ap.parse_args()
    identity = solver_identity()
    t0 = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        runs = sorted(ex.map(run, CELLS[::-1]), key=lambda r: r["n_cells"])
    keys = ("rel_q_los_minus_hierarchy", "rel_q_los_minus_fluid", "rel_q_hierarchy_minus_fluid",
            "rel_pi_los_minus_hierarchy", "rel_pi_los_minus_fluid", "rel_pi_hierarchy_minus_fluid")
    summary = {}
    for r in runs:
        s = {}
        for k in keys:
            v = np.array([row[k] for row in r["rows"] if row[k] is not None])
            s[k] = {"max": float(v.max()), "median": float(np.median(v)), "first": float(v[0]), "last": float(v[-1]),
                    "argmax_ln_a": float(r["rows"][int(np.argmax([row[k] or 0 for row in r["rows"]]))]["ln_a"])}
        summary[str(r["n_cells"])] = s
    write_json(args.output, {"schema": "htt.r108.s5_photon_moments.1", "common_times_source": str(COMMON.relative_to(REPO)),
                             "family": "VI_-1/9", "epsilon": 2e-4, "ell_max": 4, "identity": identity,
                             "wall_seconds": time.perf_counter() - t0, "summary": summary, "runs": runs,
                             "units": "dimensionless q/E and pi/E in the solver normal frame",
                             "claim": "numerical comparison of three photon-moment estimators; no attribution"})


if __name__ == "__main__":
    main()

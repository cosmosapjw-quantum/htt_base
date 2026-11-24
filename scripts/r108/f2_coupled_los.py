"""R108 F2: coupled solver -> recorded history -> line of sight versus the native observer state.

VII_h (handedness +1), ell_max 6, epsilon 2e-4 (the R107 test case), cells 48/96/192/384,
substep depth cap 1.0 (solver default, the R107 test) and 0.25 (R106 production).  For each
run the line-of-sight sky is evaluated on a Gauss-Legendre sphere and projected to the
native harmonics; reported per (channel, ell): max_m |LoS - native| / max_m |native| and the
least-squares scale <native, LoS> / <native, native>.  Three LoS quadrature settings
separate the ray/sphere discretisation from the solver discretisation, and two source
node sets are compared: cell ends only (R107) and cell ends plus the optical substeps
recorded near the observer (R108 default, history_substep_tau_max = 40).

Units: native quarter-intensity increments (T channel (I/Ibar - 1)/4), dimensionless.
Numerical evidence only; no physical attribution.

Usage: PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m scripts.r108.f2_coupled_los --workers 8
"""

from __future__ import annotations

import argparse
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from scripts.r108.common import OUT_DIR, maxrss_mb, solver_identity, write_json

CELLS = (48, 96, 192, 384)
CAPS = (1.0, 0.25)
LOS_SETTINGS = ((24, 0.02), (32, 0.02), (24, 0.01))
MODES = (("T", 0), ("T", 1), ("T", 2), ("T", 3), ("E", 2), ("B", 2), ("E", 3), ("B", 3))
L_OUT = 4


def compare(op, native_state, opo, vec) -> dict:
    out = {}
    for ch, ell in MODES:
        if (ell, 0) not in op.idx[ch] or (ell, 0) not in opo.idx[ch]:
            continue
        nat = np.array([native_state[op.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
        los = np.array([vec[opo.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
        peak = float(np.max(np.abs(nat)))
        entry = {"max_abs_native": peak, "max_abs_los": float(np.max(np.abs(los))),
                 "max_abs_diff": float(np.max(np.abs(los - nat)))}
        if peak > 0.0:
            entry["max_rel_diff"] = entry["max_abs_diff"] / peak
            scale = np.vdot(nat, los) / np.vdot(nat, nat)
            entry["ls_scale"] = [float(scale.real), float(scale.imag)]
            entry["shape_residual_rel"] = float(np.max(np.abs(los - scale.real * nat)) / peak)
        out[f"{ch}{ell}"] = entry
    return out


def run(task) -> dict:
    cells, cap = task
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    from bass.transport.general_bianchi_transfer import gl_sphere_grid
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator, stokes_maps_to_vector
    from bass.transport.hybrid_los_transfer import history_from_coupled_result, los_sky

    op = GeneralLieStokesOperator(6)
    cfg = CoupledSolverConfig(n_cells=cells, ell_max=6, epsilon=2e-4, record_history=True, max_substep_depth=cap)
    t0 = time.perf_counter()
    res = solve_coupled_einstein_boltzmann("VII_h", cfg, lie_op=op)
    solve_s = time.perf_counter() - t0
    hists = {mode: history_from_coupled_result(res, op=op, substep_nodes=(mode == "substeps"))
             for mode in ("cell_ends", "substeps")}
    rec = {"n_cells": cells, "max_substep_depth": cap, "solve_seconds": solve_s,
           "picard_iterations_used": res.picard_iterations_used,
           "picard_pi_local_rel_change": res.picard_pi_local_rel_change,
           "max_hamiltonian": res.max_hamiltonian_residual, "max_codazzi": res.max_codazzi_residual,
           "total_optical_depth": res.total_optical_depth,
           "n_nodes": {m: int(h.N.size) for m, h in hists.items()},
           "N_start": float(hists["cell_ends"].N[0]), "los": {}}
    for (n_gl, step), mode in [(s_, m_) for s_ in LOS_SETTINGS for m_ in hists]:
        hist = hists[mode]
        _, _, d, _ = gl_sphere_grid(n_gl)
        t1 = time.perf_counter()
        sky = los_sky(hist, d.reshape(-1, 3), max_step=step)
        opo = GeneralLieStokesOperator(L_OUT)
        vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), opo.idx, opo.dim, L=L_OUT,
                                    n_gl_theta=n_gl)
        rec["los"][f"{mode}_gl{n_gl}_step{step}"] = {
            "seconds": time.perf_counter() - t1, "source_ell_max": sky.diagnostics["source_ell_max"],
            "max_source_truncation": sky.diagnostics["max_source_truncation"],
            "initial_state_weight_max": sky.diagnostics["initial_state_weight_max"],
            "modes": compare(op, res.final_state, opo, vec)}
    rec["maxrss_MB"] = maxrss_mb()
    return rec


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--output", default=str(OUT_DIR / "F2_COUPLED_LOS.json"))
    args = ap.parse_args()
    tasks = [(c, cap) for cap in CAPS for c in CELLS]
    t0 = time.perf_counter()
    identity = solver_identity()  # captured before any run: the code the workers import
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        runs = list(ex.map(run, sorted(tasks, key=lambda t: -t[0] / t[1])))
    runs.sort(key=lambda r: (r["max_substep_depth"], r["n_cells"]))
    summary = {}
    for mode in ("cell_ends", "substeps"):
        for cap in CAPS:
            sub = [r for r in runs if r["max_substep_depth"] == cap]
            key = f"{mode}_gl24_step0.02"
            summary[f"{mode}_cap{cap}"] = {r["n_cells"]: {m: r["los"][key]["modes"][m].get("max_rel_diff")
                                                          for m in ("T1", "T2", "E2", "B2")} for r in sub}
    ref = summary["substeps_cap1.0"].get(192, {})
    bound = {m: (3.0 * ref[m] if ref.get(m) is not None else None) for m in ("T1", "T2", "E2", "B2")}
    write_json(args.output, {
        "schema": "htt.r108.f2_coupled_los.1", "family": "VII_h", "handedness": 1, "ell_max": 6,
        "epsilon": 2e-4, "units": "native quarter-intensity increments (dimensionless)",
        "identity": identity, "wall_seconds": time.perf_counter() - t0, "runs": runs,
        "summary_max_rel_diff_gl24_step0.02": summary,
        "proposed_test_bound_3x_192_cells_cap1_substeps": bound,
        "claim": "numerical comparison only; no physical attribution"})


if __name__ == "__main__":
    main()

"""Judge confirmatory run: repo solver vs stage-time-rate variant, R105 common_time_moments settings."""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, math, resource, sys
from pathlib import Path
from time import perf_counter
import numpy as np
import bass.transport.coupled_einstein_boltzmann as repo_mod
from scripts.r105.native_optical_refinement import angular_basis

HERE = Path(__file__).resolve().parent
VARIANT = HERE / "variant" / "coupled_stage_rate.py"

def load_variant():
    spec = importlib.util.spec_from_file_location("htt_r106_judge_stage_rate", VARIANT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    mod.HYREC_REF_CSV = repo_mod.HYREC_REF_CSV
    return mod

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--impl", choices=["repo", "variant"], required=True)
    p.add_argument("--mode", default="frozen", choices=["frozen", "stage", "stage_norm"])
    p.add_argument("--family", default="VI_-1/9")
    p.add_argument("--cells", type=int, required=True)
    p.add_argument("--cap", type=float, default=1.0)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    mod = repo_mod if a.impl == "repo" else load_variant()
    if a.impl == "variant":
        mod.RATE_MODE = a.mode
    cfg = mod.CoupledSolverConfig(n_cells=a.cells, ell_max=4, n_picard=4, max_substep_depth=a.cap,
                                  epsilon=2e-4, substeps_per_cell=2, record_history=True)
    t0 = perf_counter()
    out = mod.solve_coupled_einstein_boltzmann(a.family, cfg, lie_op=angular_basis(4, 16))
    wall = perf_counter() - t0
    h = out.history["picard_iterations"][-1]
    stride = a.cells // 48
    ci = [stride - 1, 2 * stride - 1]
    qs, qf = np.asarray(h["q_over_E_sky"][0]), np.asarray(h["q_over_E_fluid"][0])
    d = qs - qf
    nf = np.linalg.norm(qf, axis=1)
    with np.errstate(divide="ignore", invalid="ignore"):
        rel = np.where(nf > 0, np.linalg.norm(d, axis=1) / nf, np.nan)
    def ep(i):
        par = float(d[i] @ qf[i] / (qf[i] @ qf[i])) if nf[i] > 0 else None
        perp = float(np.linalg.norm(d[i] - (par or 0.0) * qf[i]) / nf[i]) if nf[i] > 0 else None
        return {"cell": int(i), "ln_a": float(h["N_end"][i]), "sky_minus_fluid": d[i].tolist(),
                "q_fluid": qf[i].tolist(), "relative": None if not np.isfinite(rel[i]) else float(rel[i]),
                "parallel_over_q": par, "perp_over_q": perp, "delta_tau_cell": float(h["delta_tau"][i]),
                "photon_substeps": int(h["photon_substeps"][i]),
                "pi_over_E_sky": np.asarray(h["pi_over_E_sky"][0, i]).tolist(),
                "pi_over_E_fluid": np.asarray(h["pi_over_E_fluid"][0, i]).tolist()}
    w = int(np.nanargmax(rel)) if np.any(np.isfinite(rel)) else 0
    src = Path(mod.__file__).read_bytes()
    res = {"impl": a.impl, "mode": a.mode if a.impl == "variant" else "repo", "family": a.family,
           "cells": a.cells, "cap": a.cap, "solver_sha256": hashlib.sha256(src).hexdigest(),
           "first": ep(ci[0]), "second": ep(ci[1]),
           "worst": {"cell": w, "ln_a": float(h["N_end"][w]), "relative": None if not np.isfinite(rel[w]) else float(rel[w]),
                     "delta_tau": float(h["delta_tau"][w]), "photon_substeps": int(h["photon_substeps"][w])},
           "max_abs_sky_q": float(np.max(np.abs(qs))), "max_abs_fluid_q": float(np.max(np.abs(qf))),
           "max_hamiltonian": float(out.max_hamiltonian_residual), "max_codazzi": float(out.max_codazzi_residual),
           "stokes_reality": float(out.max_stokes_reality_err),
           "C2": {c: float(out.cl_final[c][2]) for c in ("T", "E", "B")},
           "total_substeps": int(np.sum(h["photon_substeps"])), "wall_solve_s": wall,
           "maxrss_kB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
           "q_sky_all": qs.tolist(), "q_fluid_all": qf.tolist()}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(res, indent=1, default=lambda x: None))
    f = res["first"]; s = res["second"]
    print(f"{a.impl}/{res['mode']} {a.family} cells={a.cells} cap={a.cap} first={f['relative']} second={s['relative']} "
          f"par1={f['parallel_over_q']} worst={res['worst']} C2={res['C2']} wall={wall:.1f}s")

if __name__ == "__main__":
    main()

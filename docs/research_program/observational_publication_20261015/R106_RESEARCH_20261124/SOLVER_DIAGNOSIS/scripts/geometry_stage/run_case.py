"""R106 H2 (geometry/shear-source stage timing) single-case runner.

Runs either the UNMODIFIED repo solver (bass.transport.coupled_einstein_boltzmann at R105
b234bb0e0) or the local variant copy ``coupled_geometry_stage.py`` with the R105
common-time settings (VI_-1/9, epsilon 2e-4, ell_max 4, GL rings 16, n_picard 4,
2 minimum substeps). Writes <out>.json (summary) and <out>.npz (per-cell history).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import resource
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
VARIANT_PATH = HERE / "coupled_geometry_stage.py"
COARSE = 48


def load_variant():
    name = "htt_r106_h2_coupled_geometry_stage"
    if name in sys.modules:
        return sys.modules[name]
    from bass.transport import coupled_einstein_boltzmann as live
    spec = importlib.util.spec_from_file_location(name, VARIANT_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # dataclasses resolve the module through sys.modules
    spec.loader.exec_module(mod)
    mod.HYREC_REF_CSV = live.HYREC_REF_CSV
    return mod


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--impl", choices=("repo", "variant"), required=True)
    p.add_argument("--family", default="VI_-1/9")
    p.add_argument("--cells", type=int, required=True)
    p.add_argument("--depth", default="1.0", help="max_substep_depth or 'none'")
    p.add_argument("--timing", default="midpoint", choices=("midpoint", "midpoint_dense", "stage"))
    p.add_argument("--epsilon", type=float, default=2e-4)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    depth = None if a.depth.lower() == "none" else float(a.depth)

    from bass.transport import coupled_einstein_boltzmann as live
    from scripts.r105.native_optical_refinement import angular_basis

    if a.impl == "repo":
        if a.timing != "midpoint":
            p.error("the repo solver only has midpoint geometry timing")
        mod = live
        extra = {}
    else:
        mod = load_variant()
        extra = {"geometry_timing": a.timing}
    cfg = mod.CoupledSolverConfig(n_cells=a.cells, ell_max=4, n_picard=4, max_substep_depth=depth,
                                  epsilon=a.epsilon, substeps_per_cell=2, record_history=True, **extra)
    t0 = time.perf_counter()
    res = mod.solve_coupled_einstein_boltzmann(a.family, cfg, lie_op=angular_basis(4, 16))
    wall = time.perf_counter() - t0
    hist_all = res.history["picard_iterations"]
    h = hist_all[-1]
    N_end = np.asarray(h["N_end"])
    qs = np.asarray(h["q_over_E_sky"][0])
    qf = np.asarray(h["q_over_E_fluid"][0])
    ps = np.asarray(h["pi_over_E_sky"][0])
    pf = np.asarray(h["pi_over_E_fluid"][0])
    diff = qs - qf
    absn = np.linalg.norm(diff, axis=1)
    scale = np.linalg.norm(qf, axis=1)
    rel = np.divide(absn, scale, out=np.full_like(absn, np.nan), where=scale > 0)

    stride, rem = divmod(a.cells, COARSE)
    common = []
    if not rem and stride:
        for k in (1, 2):
            i = k * stride - 1
            common.append({
                "coarse_endpoint": k, "cell_index": int(i), "ln_a": float(N_end[i]),
                "sky": qs[i].tolist(), "fluid": qf[i].tolist(), "sky_minus_fluid": diff[i].tolist(),
                "absolute_norm": float(absn[i]), "relative_norm": None if not scale[i] > 0 else float(rel[i]),
                "signed_ratio_componentwise": (diff[i] / qf[i]).tolist() if np.all(qf[i] != 0) else None,
                "delta_tau_cell": float(h["delta_tau"][i]), "photon_substeps_cell": int(h["photon_substeps"][i]),
                "pi_over_E_sky": ps[i].tolist(), "pi_over_E_fluid": pf[i].tolist(),
                "hamiltonian": float(h["hamiltonian"][i]), "codazzi": float(h["codazzi"][i]),
                "thomson_force_over_E_sky": np.asarray(h["thomson_force_over_E_sky"][i]).tolist(),
                "thomson_force_over_E_fluid": np.asarray(h["thomson_force_over_E_fluid"][i]).tolist(),
            })
        all_common_idx = np.arange(1, COARSE + 1) * stride - 1
        common_rel = [None if not math.isfinite(x) else float(x) for x in rel[all_common_idx]]
        common_ln_a = N_end[all_common_idx].tolist()
    else:
        common_rel = common_ln_a = None
    valid = np.isfinite(rel)
    if valid.any():
        w = int(np.nanargmax(np.where(valid, rel, -1.0)))
        worst_kind = "relative"
    else:
        w = int(np.argmax(absn))
        worst_kind = "absolute (fluid q/E is zero everywhere)"
    worst = {"kind": worst_kind, "cell_index": w, "ln_a": float(N_end[w]),
             "relative_norm": None if not valid[w] else float(rel[w]), "absolute_norm": float(absn[w]),
             "sky_minus_fluid": diff[w].tolist(), "fluid": qf[w].tolist(),
             "delta_tau_cell": float(h["delta_tau"][w]), "photon_substeps_cell": int(h["photon_substeps"][w])}
    # Picard history of the first common endpoint (convergence of the outer iteration)
    picard_first = []
    if common:
        i = common[0]["cell_index"]
        for it in hist_all:
            d = np.asarray(it["q_over_E_sky"][0][i]) - np.asarray(it["q_over_E_fluid"][0][i])
            picard_first.append({"sky_minus_fluid": d.tolist(),
                                 "relative_norm": float(np.linalg.norm(d) / np.linalg.norm(it["q_over_E_fluid"][0][i]))
                                 if np.linalg.norm(it["q_over_E_fluid"][0][i]) > 0 else None})
    out = {
        "schema": "htt.r106.h2_geometry_stage.case.1",
        "impl": a.impl, "family": a.family, "n_cells": a.cells, "max_substep_depth": depth,
        "geometry_timing": a.timing, "epsilon": a.epsilon, "ell_max": 4, "gl_rings": 16, "n_picard": 4,
        "min_substeps": 2, "massless_neutrino_fraction": 0.0,
        "solver_file": str(Path(mod.__file__).resolve()), "solver_sha256": sha(mod.__file__),
        "wall_s_solve": wall, "peak_rss_kB_self": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "first_two_common": common, "common_relative_all48": common_rel, "common_ln_a_all48": common_ln_a,
        "worst_cell": worst, "picard_first_common": picard_first,
        "max_relative_all_cells": None if not valid.any() else float(np.nanmax(rel)),
        "final_relative": None if not valid[-1] else float(rel[-1]),
        "total_photon_substeps": int(np.sum(h["photon_substeps"])),
        "C2": {ch: float(res.cl_final[ch][2]) for ch in ("T", "E", "B")},
        "max_hamiltonian": float(res.max_hamiltonian_residual), "max_codazzi": float(res.max_codazzi_residual),
        "max_jacobi": float(res.max_jacobi_residual), "max_stokes_reality": float(res.max_stokes_reality_err),
        "max_four_force_orthog_error": float(res.max_four_force_orthog_error),
        "picard_pi_rel_change": float(res.picard_pi_rel_change),
        "total_optical_depth": float(res.total_optical_depth),
        "max_abs_fluid_q_over_E": float(np.max(np.abs(qf))), "max_abs_sky_q_over_E": float(np.max(np.abs(qs))),
        "max_abs_final_state": float(np.max(np.abs(res.final_state))),
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    Path(str(a.out) + ".json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    np.savez_compressed(str(a.out) + ".npz", N_end=N_end, q_sky=qs, q_fluid=qf, pi_sky=ps, pi_fluid=pf,
                        delta_tau=np.asarray(h["delta_tau"]), photon_substeps=np.asarray(h["photon_substeps"]),
                        hamiltonian=np.asarray(h["hamiltonian"]), codazzi=np.asarray(h["codazzi"]),
                        final_state=res.final_state)
    fc = common[0] if common else None
    print(f"{a.impl}/{a.timing}/{a.family}/N{a.cells}/d{depth}: first_rel="
          f"{None if fc is None else fc['relative_norm']} worst={worst['relative_norm']}@{w} wall={wall:.1f}s")


if __name__ == "__main__":
    main()

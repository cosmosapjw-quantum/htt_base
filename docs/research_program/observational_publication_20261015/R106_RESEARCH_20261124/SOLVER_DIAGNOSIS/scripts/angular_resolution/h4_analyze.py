"""Summarize R106 H4 angular-resolution runs at exactly shared 48-cell endpoints."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from scripts.r105.common_time_moments import nested_samples

LEVELS = (48, 96, 192)


def richardson(e48, e96, e192):
    d1, d2 = e96 - e48, e192 - e96
    if d2 == 0.0:
        return {"r": None, "limit": e192, "note": "no change 96->192"}
    r = d1 / d2
    limit = e192 + d2 / (r - 1.0) if r != 1.0 else None
    return {"r": r, "limit": limit, "observed_order_log2_r": float(np.log2(r)) if r > 0 else None}


def per_run(r, common):
    edges = np.asarray(r["N_end"]); sky = np.asarray(r["q_sky"]); fl = np.asarray(r["q_fluid"])
    samples = nested_samples(common, edges, sky, fl)
    err = np.linalg.norm(sky - fl, axis=1); scale = np.linalg.norm(fl, axis=1)
    rel = np.divide(err, scale, out=np.full_like(err, np.nan), where=scale > 0)
    worst = int(np.nanargmax(rel)) if np.isfinite(rel).any() else int(np.argmax(err))
    out = {
        "n_cells": r["n_cells"], "ell_max": r["ell_max"], "gl_rings": r["gl_rings"],
        "moving_kernel_rings": r["moving_kernel_rings"], "solver": r["solver"],
        "common": [],
        "worst_relative_all_cells": {
            "cell_index": worst, "ln_a": float(edges[worst]), "relative_norm": float(rel[worst]),
            "absolute_norm": float(err[worst]), "delta_tau_cell": float(r["delta_tau"][worst]),
            "photon_substeps": int(r["photon_substeps"][worst]),
        },
        "max_hamiltonian": r["max_hamiltonian"], "max_codazzi": r["max_codazzi"],
        "max_jacobi": r["max_jacobi"], "max_stokes_reality": r["max_stokes_reality"],
        "picard_pi_rel_change": r["picard_pi_rel_change"], "C2": r["C2"],
        "total_photon_substeps": int(np.sum(r["photon_substeps"])), "wall_s": r["wall_s"],
        "worker_maxrss_kB": r["worker_maxrss_kB"],
    }
    for k in (0, 1):
        s = samples[k]
        idx = s["cell_index"]
        f = np.asarray(s["fluid"]); d = np.asarray(s["sky_minus_fluid"])
        par = float(d @ f / (f @ f))
        perp = d - par * f
        out["common"].append({
            "ln_a": float(common[k]), "cell_index": idx, "sky": s["sky"], "fluid": s["fluid"],
            "sky_minus_fluid": s["sky_minus_fluid"], "relative_norm": s["relative_norm"],
            "absolute_norm": s["absolute_norm"],
            "parallel_fraction_of_fluid": par, "perp_relative_norm": float(np.linalg.norm(perp) / np.linalg.norm(f)),
            "pi_over_E_sky": r["pi_sky"][idx], "pi_over_E_fluid": r["pi_fluid"][idx],
            "pi_sky_minus_fluid_frobenius": float(np.linalg.norm(np.asarray(r["pi_sky"][idx]) - np.asarray(r["pi_fluid"][idx]))),
            "thomson_over_E_sky": r["thomson_sky"][idx], "thomson_over_E_fluid": r["thomson_fluid"][idx],
            "delta_tau_cell": float(r["delta_tau"][idx]), "photon_substeps": int(r["photon_substeps"][idx]),
        })
    return out


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw", nargs="+", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    runs, raw_sha = [], {}
    for path in a.raw:
        data = json.loads(path.read_text())
        raw_sha[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        runs.extend(data["runs"])
    groups = {}
    for r in runs:
        if r["family"] != "VI_-1/9":
            continue
        groups.setdefault(r["label"], {})[r["n_cells"]] = r
    summary = {"schema": "htt.r106.h4_angular.summary.1", "raw_sha256": raw_sha,
               "analysis_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               "groups": {}, "flrw": []}
    for label, by_n in groups.items():
        if not all(n in by_n for n in LEVELS):
            continue
        common = np.asarray(by_n[48]["N_end"])
        rows = {n: per_run(by_n[n], common) for n in LEVELS}
        g = {"runs": rows}
        for k, name in ((0, "first_common"), (1, "second_common")):
            e = [rows[n]["common"][k]["relative_norm"] for n in LEVELS]
            vec = np.array([rows[n]["common"][k]["sky_minus_fluid"] for n in LEVELS])
            g[name] = {
                "ln_a": float(common[k]), "relative_norm_by_n": dict(zip(map(str, LEVELS), e)),
                "trend_96_to_192": e[2] - e[1], "reduced_96_to_192": e[2] < e[1],
                "richardson_relative": richardson(*e),
                "richardson_signed_components": [richardson(*vec[:, i]) for i in range(3)],
            }
        summary["groups"][label] = g
    ctrl = summary["groups"].get("control_l4_r16")
    if ctrl:
        for label, g in summary["groups"].items():
            g["vs_control"] = {}
            for n in LEVELS:
                c0 = ctrl["runs"][n]["common"][0]; x0 = g["runs"][n]["common"][0]
                g["vs_control"][str(n)] = {
                    "first_rel_minus_control": x0["relative_norm"] - c0["relative_norm"],
                    "sky_change_norm": float(np.linalg.norm(np.subtract(x0["sky"], c0["sky"]))),
                    "fluid_change_norm": float(np.linalg.norm(np.subtract(x0["fluid"], c0["fluid"]))),
                    "residual_change_norm": float(np.linalg.norm(np.subtract(x0["sky_minus_fluid"], c0["sky_minus_fluid"]))),
                    "C2T_rel_change": g["runs"][n]["C2"]["T"] / ctrl["runs"][n]["C2"]["T"] - 1,
                    "C2E_rel_change": g["runs"][n]["C2"]["E"] / ctrl["runs"][n]["C2"]["E"] - 1,
                    "C2B_rel_change": g["runs"][n]["C2"]["B"] / ctrl["runs"][n]["C2"]["B"] - 1,
                }
    for r in runs:
        if r["family"] == "FLRW":
            summary["flrw"].append({
                "label": r["label"], "n_cells": r["n_cells"], "solver": r["solver"],
                "max_abs_q_sky": float(np.max(np.abs(r["q_sky"]))),
                "max_abs_q_fluid": float(np.max(np.abs(r["q_fluid"]))),
                "max_abs_pi_sky": float(np.max(np.abs(r["pi_sky"]))),
                "C2": r["C2"], "max_hamiltonian": r["max_hamiltonian"], "max_codazzi": r["max_codazzi"],
                "max_stokes_reality": r["max_stokes_reality"], "wall_s": r["wall_s"],
            })
    a.output.write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    for label, g in summary["groups"].items():
        f, s = g["first_common"], g["second_common"]
        print(f"{label:28s} first {[f'{v:.6e}' for v in f['relative_norm_by_n'].values()]} "
              f"R r={f['richardson_relative']['r']} lim={f['richardson_relative']['limit']}")
        print(f"{'':28s} second {[f'{v:.6e}' for v in s['relative_norm_by_n'].values()]} "
              f"R r={s['richardson_relative']['r']} lim={s['richardson_relative']['limit']}")


if __name__ == "__main__":
    main()

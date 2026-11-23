"""Aggregate the R106 H1 collision-substep-depth grid (VI_-1/9, R105 common-time settings)."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from scripts.r105.common_time_moments import nested_samples

W = Path(__file__).resolve().parent
R105 = Path("docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/SOLVER_COMMON_TIMES.json")
CELLS = (48, 96, 192)


def load_runs():
    runs = {}
    for f in sorted((W / "runs").glob("c*_cap*.json")):
        d = json.loads(f.read_text())
        cap = d["config"]["max_substep_depth"]
        t = (W / "logs" / (f.stem + ".time")).read_text().split()
        d["_time_cmd"] = {"wall_s": float(t[0]), "peak_rss_kB": int(t[2])}
        d["_file"] = str(f)
        d["_sha256"] = hashlib.sha256(f.read_bytes()).hexdigest()
        runs[(d["config"]["n_cells"], cap)] = d
    return runs


def run_summary(d):
    fin = d["final"]
    edges = np.asarray(fin["N_end"])
    sky = np.asarray(fin["q_over_E_sky"])
    flu = np.asarray(fin["q_over_E_fluid"])
    n = len(edges)
    stride = n // 48
    common = edges[stride - 1::stride]
    s = nested_samples(common, edges, sky, flu)
    diff = sky - flu
    rel = np.linalg.norm(diff, axis=1) / np.linalg.norm(flu, axis=1)
    w = int(np.argmax(rel))
    out = {"n_cells": n, "max_substep_depth": d["config"]["max_substep_depth"]}
    for label, k in (("first", 0), ("second", 1)):
        smp = s[k]
        qf = np.asarray(smp["fluid"])
        dv = np.asarray(smp["sky_minus_fluid"])
        qhat = qf / np.linalg.norm(qf)
        out[label] = {
            "ln_a": float(common[k]), "cell_index": smp["cell_index"],
            "sky_minus_fluid": smp["sky_minus_fluid"], "relative_norm": smp["relative_norm"],
            "absolute_norm": smp["absolute_norm"],
            "signed_parallel_relative": float(dv @ qhat / np.linalg.norm(qf)),
            "perp_relative": float(np.linalg.norm(dv - (dv @ qhat) * qhat) / np.linalg.norm(qf)),
            "delta_tau_cell": fin["delta_tau"][smp["cell_index"]],
            "photon_substeps_cell": fin["photon_substeps"][smp["cell_index"]],
            "substep_depth_max_cell": fin["substep_depth_max"][smp["cell_index"]],
            "substep_depth_min_cell": fin["substep_depth_min"][smp["cell_index"]],
        }
    out["first"]["pi_over_E_sky"] = fin["pi_over_E_sky_common"][0]
    out["first"]["pi_over_E_fluid"] = fin["pi_over_E_fluid_common"][0]
    out["worst"] = {"cell_index": w, "ln_a": float(edges[w]), "relative_norm": float(rel[w]),
                    "delta_tau": fin["delta_tau"][w], "photon_substeps": fin["photon_substeps"][w],
                    "substep_depth_max": fin["substep_depth_max"][w]}
    pc = d["picard_common"]
    out["picard_first_common"] = [{
        "picard": it["picard"],
        "relative_norm": float(np.linalg.norm(np.subtract(it["common"][0]["q_sky"], it["common"][0]["q_fluid"]))
                               / np.linalg.norm(it["common"][0]["q_fluid"])),
        "q_sky_change_vs_final_rel": float(np.linalg.norm(np.subtract(it["common"][0]["q_sky"], pc[-1]["common"][0]["q_sky"]))
                                           / np.linalg.norm(pc[-1]["common"][0]["q_fluid"])),
        "q_fluid_change_vs_final_rel": float(np.linalg.norm(np.subtract(it["common"][0]["q_fluid"], pc[-1]["common"][0]["q_fluid"]))
                                             / np.linalg.norm(pc[-1]["common"][0]["q_fluid"])),
    } for it in pc]
    out["total_photon_substeps_final_sweep"] = int(np.sum(fin["photon_substeps"]))
    out["max_substep_depth_realized"] = float(np.max(fin["substep_depth_max"]))
    out["substep_count_matches_history"] = fin["substep_count_matches_history"]
    out["max_hamiltonian"] = d["max_hamiltonian"]
    out["max_codazzi"] = d["max_codazzi"]
    out["max_jacobi"] = d["max_jacobi"]
    out["max_stokes_reality_err"] = d["max_stokes_reality_err"]
    out["picard_pi_rel_change"] = d["picard_pi_rel_change"]
    out["C2"] = {k: d["C2"][k] for k in ("T", "E", "B")}
    out["wall_s_solve"] = d["wall_s_solve"]
    out["command_wall_s"] = d["_time_cmd"]["wall_s"]
    out["command_peak_rss_kB"] = d["_time_cmd"]["peak_rss_kB"]
    out["solver_file_clean_vs_head"] = d["solver_file_clean_vs_head"]
    out["git_head"] = d["git_head"]
    out["case_json"] = d["_file"]
    out["case_json_sha256"] = d["_sha256"]
    return out, common, sky, flu


def richardson(e48, e96, e192):
    num, den = e96 - e48, e192 - e96
    if den == 0 or num == 0:
        return {"r": None, "order": None, "limit": None}
    r = num / den
    lim = e192 + den / (r - 1.0) if r != 1.0 else None
    return {"r": r, "order": math.log2(r) if r > 0 else None, "limit": lim}


def cap_extrap(caps, vals):
    """Successive cap-halving differences; order p = log2(D_k/D_{k+1}); limit from finest triple."""
    order = sorted(range(len(caps)), key=lambda i: -caps[i])
    c = [caps[i] for i in order]
    v = [vals[i] for i in order]
    diffs = [v[i] - v[i + 1] for i in range(len(v) - 1)]
    orders = []
    for i in range(len(diffs) - 1):
        ratio = diffs[i] / diffs[i + 1] if diffs[i + 1] else None
        orders.append(math.log2(ratio) if ratio and ratio > 0 else None)
    lim = None
    if len(diffs) >= 2 and diffs[-1] and diffs[-2]:
        ratio = diffs[-2] / diffs[-1]
        if ratio > 1:
            lim = v[-1] - diffs[-1] / (ratio - 1.0)
    return {"caps": c, "values": v, "halving_differences": diffs, "observed_orders": orders,
            "limit_cap_to_zero_from_finest_triple": lim}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, default=W / "COLLISION_DEPTH_H1.json")
    a = p.parse_args()
    runs = load_runs()
    summ, raw = {}, {}
    for key, d in sorted(runs.items(), key=lambda kv: (kv[0][1] is None, -(kv[0][1] or 0), kv[0][0])):
        s, common, sky, flu = run_summary(d)
        summ[f"c{key[0]}_cap{key[1]}"] = s
        raw[key] = (common, sky, flu)

    # Bitwise reproduction of R105 at cap 1.0.
    ref = json.loads(R105.read_text())
    repro = {}
    for n in CELLS:
        key = (n, 1.0)
        if key not in raw:
            continue
        common, sky, flu = raw[key]
        stride = n // 48
        idx = np.arange(1, 49) * stride - 1
        rs = np.array([row["by_n_cells"][str(n)]["sky"] for row in ref["common_endpoints"]])
        rf = np.array([row["by_n_cells"][str(n)]["fluid"] for row in ref["common_endpoints"]])
        rr = np.array([row["by_n_cells"][str(n)]["relative_norm"] for row in ref["common_endpoints"]])
        mine_rel = np.linalg.norm(sky[idx] - flu[idx], axis=1) / np.linalg.norm(flu[idx], axis=1)
        repro[str(n)] = {"max_abs_sky_diff": float(np.max(np.abs(sky[idx] - rs))),
                         "max_abs_fluid_diff": float(np.max(np.abs(flu[idx] - rf))),
                         "max_rel_norm_diff": float(np.max(np.abs(mine_rel - rr))),
                         "bitwise_equal": bool(np.array_equal(sky[idx], rs) and np.array_equal(flu[idx], rf)),
                         "common_ln_a_equal": bool(np.array_equal(common, [r["ln_a"] for r in ref["common_endpoints"]]))}

    caps = sorted({k[1] for k in runs}, reverse=True)
    tables, rich_cells, cap_dep = {}, {}, {}
    for label in ("first", "second"):
        for metric in ("relative_norm", "signed_parallel_relative"):
            tab = {str(c): {str(n): summ[f"c{n}_cap{c}"][label][metric] for n in CELLS if f"c{n}_cap{c}" in summ}
                   for c in caps}
            tables[f"{label}_{metric}"] = tab
            rich_cells[f"{label}_{metric}"] = {
                str(c): richardson(*[tab[str(c)][str(n)] for n in CELLS])
                for c in caps if all(str(n) in tab[str(c)] for n in CELLS)}
            shared = [c for c in caps if all(str(n) in tab[str(c)] for n in CELLS)]
            cap_dep[f"{label}_{metric}"] = {
                str(n): cap_extrap(shared, [tab[str(c)][str(n)] for c in shared]) for n in CELLS}
            cap_dep[f"{label}_{metric}"]["all_caps_by_cells"] = {
                str(n): cap_extrap([c for c in caps if str(n) in tab[str(c)]],
                                   [tab[str(c)][str(n)] for c in caps if str(n) in tab[str(c)]])
                for n in CELLS}
            cap_dep[f"{label}_{metric}"]["shared_caps"] = shared
            # double limit: cap->0 at each n, then cells Richardson on the cap->0 limits
            lims = [cap_dep[f"{label}_{metric}"][str(n)]["limit_cap_to_zero_from_finest_triple"] for n in CELLS]
            if all(x is not None for x in lims):
                cap_dep[f"{label}_{metric}"]["cells_richardson_of_cap0_limits"] = richardson(*lims)
            # cells-limit at each cap, then cap extrapolation of those limits
            cl = [rich_cells[f"{label}_{metric}"].get(str(c), {}).get("limit") for c in shared]
            if all(x is not None for x in cl):
                cap_dep[f"{label}_{metric}"]["cap_extrap_of_cells_limits"] = cap_extrap(shared, cl)

    payload = {
        "schema": "htt.r106.collision_depth_h1.1",
        "hypothesis": "H1: with max_substep_depth capped, e-fold cell refinement does not refine opaque-era "
                      "scattering substeps; a fixed-cap SDIRK collision error sets the nonzero cells->inf limit "
                      "of the first-common sky-fluid q/E residual.",
        "family": "VI_-1/9", "epsilon": 2e-4, "ell_max": 4, "gl_rings": 16, "n_picard": 4,
        "substeps_per_cell": 2, "massless_neutrino_fraction": 0.0,
        "change": "config only: max_substep_depth in {1.0 (R105 control), 0.5, 0.25, 0.125}; unmodified repo solver",
        "r105_reproduction_cap1": repro,
        "tables": tables,
        "richardson_in_cells_at_fixed_cap": rich_cells,
        "cap_dependence_at_fixed_cells": cap_dep,
        "runs": summ,
        "analysis_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "run_case_sha256": hashlib.sha256((W / "run_case.py").read_bytes()).hexdigest(),
        "r105_reference_sha256": hashlib.sha256(R105.read_bytes()).hexdigest(),
    }
    a.output.write_text(json.dumps(payload, indent=1, allow_nan=False) + "\n")
    for label in ("first", "second"):
        print(f"== {label} common endpoint relative |sky-fluid|/|fluid| ==")
        print("cap      " + "  ".join(f"{n:>13d}" for n in CELLS) + "   r_cells     limit")
        for c in caps:
            row = tables[f"{label}_relative_norm"][str(c)]
            rc = rich_cells[f"{label}_relative_norm"].get(str(c), {})
            print(f"{c!s:8s} " + "  ".join(f"{row.get(str(n), float('nan')):13.6e}" for n in CELLS)
                  + f"   {rc.get('r') or float('nan'):8.4f}  {rc.get('limit') or float('nan'):.6e}")
    print("repro", json.dumps(repro))


if __name__ == "__main__":
    main()

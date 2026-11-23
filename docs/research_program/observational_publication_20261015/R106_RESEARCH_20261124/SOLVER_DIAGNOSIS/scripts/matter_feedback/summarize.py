"""Collect R106 H3 matter-feedback runs into MATTER_FEEDBACK_SUMMARY.json."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
R105_FIRST = {48: 3.1935484771574664e-06, 96: 3.539700455541186e-06, 192: 3.6292782170005017e-06}
R105_SECOND = {48: 4.936623490941116e-05, 96: 4.984600386296121e-05, 192: 4.991118148921352e-05}


def richardson(e):
    """r=(e96-e48)/(e192-e96); limit=e_f+(e_f-e_m)/(r-1); also with (96,192,384) when present."""
    out = {}
    for a, b, c in ((48, 96, 192), (96, 192, 384), (192, 384, 768), (384, 768, 1536)):
        if all(k in e for k in (a, b, c)):
            d1, d2 = e[b] - e[a], e[c] - e[b]
            r = d1 / d2 if d2 else math.inf
            lim = e[c] + d2 / (r - 1) if (math.isfinite(r) and r != 1) else None
            out[f"{a}_{b}_{c}"] = {"r": r, "observed_order_log2_r": math.log2(r) if r > 0 else None,
                                   "limit": lim}
    return out


def timing(label):
    t = HERE / "logs" / f"{label}.time"
    if not t.exists():
        return None
    last = t.read_text().strip().splitlines()[-1].split()
    return {"wall_s": float(last[0]), "peak_rss_kB": int(last[2])}


def main():
    runs = {}
    for p in sorted((HERE / "runs").glob("*.json")):
        d = json.loads(p.read_text())
        runs[d["label"]] = d
    groups = {}
    for label, d in runs.items():
        g = label.rsplit("_", 1)[0]
        groups.setdefault(g, {})[d["config"]["n_cells"]] = d
    ctrl = groups.get("ctrl", {})
    table = {}
    for g, by_n in sorted(groups.items()):
        rows = {}
        for n, d in sorted(by_n.items()):
            fc, sc = d["first_common"], d["second_common"]
            row = {
                "label": d["label"], "solver": d["solver"], "config": d["config"],
                "first_common_ln_a": fc["ln_a"], "first_relative": fc["relative_norm"],
                "first_sky_minus_fluid": fc["sky_minus_fluid"], "first_cell_index": fc["cell_index"],
                "first_cell_delta_tau": fc["delta_tau"], "first_cell_photon_substeps": fc["photon_substeps"],
                "first_cell_depth_per_substep": fc["delta_tau"] / fc["photon_substeps"],
                "first_pi_over_E_sky": fc["pi_over_E_sky"], "first_pi_over_E_fluid": fc["pi_over_E_fluid"],
                "first_tight_coupling": d.get("first_common_tight_coupling"),
                "second_common_ln_a": sc["ln_a"], "second_relative": sc["relative_norm"],
                "second_sky_minus_fluid": sc["sky_minus_fluid"],
                "worst_cell": d["worst_cell"],
                "max_hamiltonian": d["max_hamiltonian"], "max_codazzi": d["max_codazzi"],
                "max_stokes_reality": d["max_stokes_reality"], "picard_pi_rel_change": d["picard_pi_rel_change"],
                "C2": d["C2"], "solver_wall_s": d["wall_s"], "process": timing(d["label"]),
                "per_picard_first_relative": [it["first_relative"] for it in d["per_picard"]],
                "per_picard_first_sky_minus_fluid": [it["first_sky_minus_fluid"] for it in d["per_picard"]],
                "sha256": d["sha256"],
            }
            if n in ctrl and g != "ctrl":
                c = ctrl[n]
                row["first_signed_change_vs_ctrl"] = (np.asarray(fc["sky_minus_fluid"])
                                                      - np.asarray(c["first_common"]["sky_minus_fluid"])).tolist()
                row["first_sky_change_vs_ctrl"] = (np.asarray(fc["sky"]) - np.asarray(c["first_common"]["sky"])).tolist()
                row["first_fluid_change_vs_ctrl"] = (np.asarray(fc["fluid"])
                                                     - np.asarray(c["first_common"]["fluid"])).tolist()
                row["second_signed_change_vs_ctrl"] = (np.asarray(sc["sky_minus_fluid"])
                                                       - np.asarray(c["second_common"]["sky_minus_fluid"])).tolist()
                row["C2_relative_change_vs_ctrl"] = {k: d["C2"][k] / c["C2"][k] - 1 for k in d["C2"]}
            if g == "ctrl" and n in R105_FIRST:
                row["r105_first_relative"] = R105_FIRST[n]
                row["r105_second_relative"] = R105_SECOND[n]
                row["r105_first_abs_diff"] = abs(fc["relative_norm"] - R105_FIRST[n])
                row["r105_second_abs_diff"] = abs(sc["relative_norm"] - R105_SECOND[n])
            rows[n] = row
        first = {n: r["first_relative"] for n, r in rows.items()}
        second = {n: r["second_relative"] for n, r in rows.items()}
        table[g] = {"by_n_cells": rows, "richardson_first": richardson(first),
                    "richardson_second": richardson(second),
                    "first_trend_96_to_192": (first[192] - first[96]) if (96 in first and 192 in first) else None}
    variant = HERE / "variants" / "coupled_matter_feedback_variant.py"
    out = {
        "schema": "htt.r106.matter_feedback_summary.1",
        "hypothesis": "H3 matter feedback: previous-Picard pi/E (cubic spline, midpoint = mean of ends) in the "
                      "fluid vs current sky pi/E",
        "family": "VI_-1/9", "epsilon": 2e-4, "ell_max": 4, "gl_rings": 16, "substeps_per_cell": 2,
        "max_substep_depth": 1.0, "massless_neutrino_fraction": 0.0,
        "variant_file": str(variant),
        "variant_sha256": hashlib.sha256(variant.read_bytes()).hexdigest(),
        "variant_diff_sha256": hashlib.sha256((HERE / "variants" / "coupled_matter_feedback_variant.diff")
                                              .read_bytes()).hexdigest(),
        "groups": table,
    }
    repo = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
    out["input_sha256"] = {str(f): hashlib.sha256((repo / f).read_bytes()).hexdigest() for f in (
        "htt/bass/transport/coupled_einstein_boltzmann.py", "scripts/r105/common_time_moments.py",
        "scripts/r105/native_optical_refinement.py", "htt/bass/transport/moving_collision_stage.py",
        "htt/bass/transport/general_lie_stokes.py", "htt/bass/collision/moving_thomson.py",
        "htt/bass/recombination/fixtures/recombination_ref_planck2018.csv",
        "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/SOLVER_COMMON_TIMES.json")}
    out["work_sha256"] = {f: hashlib.sha256((HERE / f).read_bytes()).hexdigest() for f in (
        "run_case.py", "run_task.sh", "summarize.py", "substep_geometry.py")}
    sg = HERE / "SUBSTEP_GEOMETRY_PICARD0.json"
    if sg.exists():
        g = json.loads(sg.read_text())
        out["last_substep_before_common_endpoint_picard0"] = {
            n: {k: {"n_substeps": v["n_substeps"], "last_depth": v["last_depth"], "last_dN": v["last_dN"],
                    "dlnrate_dN_at_end": v["dlnrate_dN_at_end"]} for k, v in rows.items()} for n, rows in g.items()}
    out["commands_tsv"] = str(HERE / "logs" / "commands.tsv")
    (HERE / "MATTER_FEEDBACK_SUMMARY.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    for g, t in table.items():
        print(g)
        for n, r in t["by_n_cells"].items():
            print(f"  {n:4d} first={r['first_relative']:.6e} second={r['second_relative']:.6e} "
                  f"worst={r['worst_cell']['cell_index']}@{r['worst_cell']['ln_a']:.4f} rel={r['worst_cell']['relative_norm']:.3e} "
                  f"depth/sub={r['first_cell_depth_per_substep']:.4f} ham={r['max_hamiltonian']:.2e} "
                  f"cod={r['max_codazzi']:.2e} C2T={r['C2']['T']:.10e}")
        print("   richardson first", t["richardson_first"])


if __name__ == "__main__":
    main()

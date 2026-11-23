"""Summarise the R106 H2 geometry/shear-stage-timing A/B runs into SUMMARY_H2.json."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
RUNS = HERE / "runs"
R105_FIRST = {48: 3.1935484771574664e-06, 96: 3.539700455541186e-06, 192: 3.6292782170005017e-06}
R105_SECOND = {48: 4.936623490941116e-05, 96: 4.984600386296121e-05, 192: 4.991118148921352e-05}


def load(label):
    j = RUNS / f"{label}.json"
    if not j.exists():
        return None
    out = json.loads(j.read_text())
    out["_npz"] = dict(np.load(RUNS / f"{label}.npz"))
    t = HERE / "logs" / f"{label}.time"
    out["_time"] = t.read_text().strip().splitlines()[-1] if t.exists() else None
    return out


def richardson(e):
    e48, e96, e192 = e
    d1, d2 = e96 - e48, e192 - e96
    if d2 == 0:
        return {"r": None, "order": None, "limit": e192}
    r = d1 / d2
    lim = e192 + d2 / (r - 1.0) if r != 1.0 else None
    order = math.log2(r) if r > 0 else None
    return {"r": r, "order": order, "limit": lim}


def series(prefix, depth, levels=(48, 96, 192, 384)):
    rows = {}
    for n in levels:
        r = load(f"{prefix}_N{n}_d{depth}")
        if r is not None:
            rows[n] = r
    return rows


def describe(rows):
    out = {}
    for n, r in rows.items():
        c = r["first_two_common"]
        out[str(n)] = {
            "first_ln_a": c[0]["ln_a"], "first_relative": c[0]["relative_norm"],
            "first_sky_minus_fluid": c[0]["sky_minus_fluid"],
            "first_signed_ratio_componentwise": c[0]["signed_ratio_componentwise"],
            "second_ln_a": c[1]["ln_a"], "second_relative": c[1]["relative_norm"],
            "second_sky_minus_fluid": c[1]["sky_minus_fluid"],
            "first_pi_over_E_sky": c[0]["pi_over_E_sky"], "first_pi_over_E_fluid": c[0]["pi_over_E_fluid"],
            "first_cell_delta_tau": c[0]["delta_tau_cell"], "first_cell_substeps": c[0]["photon_substeps_cell"],
            "worst_cell": r["worst_cell"], "final_relative": r["final_relative"],
            "max_hamiltonian": r["max_hamiltonian"], "max_codazzi": r["max_codazzi"],
            "max_jacobi": r["max_jacobi"], "max_stokes_reality": r["max_stokes_reality"],
            "C2": r["C2"], "picard_pi_rel_change": r["picard_pi_rel_change"],
            "picard_first_common": r["picard_first_common"],
            "total_photon_substeps": r["total_photon_substeps"],
            "wall_s_solve": r["wall_s_solve"], "time_log": r["_time"], "solver_sha256": r["solver_sha256"],
        }
    for n, r in rows.items():
        o = out[str(n)]
        for k, name in ((0, "first"), (1, "second")):
            c = r["first_two_common"][k]
            q = np.asarray(c["fluid"]); d = np.asarray(c["sky_minus_fluid"]); qn = float(np.linalg.norm(q))
            par = float(d @ q) / qn
            o[f"{name}_parallel_over_absq"] = par / qn
            o[f"{name}_perp_over_absq"] = float(np.linalg.norm(d - par * q / qn)) / qn
        pf = r["picard_first_common"]
        o["picard_last_change_first_relative"] = abs(pf[-1]["relative_norm"] - pf[-2]["relative_norm"])
        ps = np.asarray(r["first_two_common"][0]["pi_over_E_sky"])
        o["first_pi_over_E_sky_frobenius"] = float(np.linalg.norm(ps))
    for key in ("first_relative", "second_relative", "first_pi_over_E_sky_frobenius"):
        vals = [out[str(n)][key] for n in (48, 96, 192) if str(n) in out]
        if len(vals) == 3:
            out[f"richardson_{key}_48_96_192"] = richardson(vals)
        vals = [out[str(n)][key] for n in (96, 192, 384) if str(n) in out]
        if len(vals) == 3:
            out[f"richardson_{key}_96_192_384"] = richardson(vals)
    return out


def ab(var_rows, ref_rows):
    """Signed variant-minus-control differences at the common endpoints (same n_cells)."""
    out = {}
    for n in sorted(set(var_rows) & set(ref_rows)):
        v, r = var_rows[n], ref_rows[n]
        d = {}
        for k, name in ((0, "first"), (1, "second")):
            cv, cr = v["first_two_common"][k], r["first_two_common"][k]
            assert cv["ln_a"] == cr["ln_a"]
            d[name] = {
                "ln_a": cv["ln_a"],
                "delta_sky": (np.subtract(cv["sky"], cr["sky"])).tolist(),
                "delta_fluid": (np.subtract(cv["fluid"], cr["fluid"])).tolist(),
                "delta_sky_minus_fluid": (np.subtract(cv["sky_minus_fluid"], cr["sky_minus_fluid"])).tolist(),
                "delta_relative": cv["relative_norm"] - cr["relative_norm"],
                "delta_relative_over_control": (cv["relative_norm"] - cr["relative_norm"]) / cr["relative_norm"],
            }
        qs_v, qs_r = v["_npz"]["q_sky"], r["_npz"]["q_sky"]
        qf_v, qf_r = v["_npz"]["q_fluid"], r["_npz"]["q_fluid"]
        scale = np.linalg.norm(qf_r, axis=1)
        d["max_over_cells_rel_delta_sky"] = float(np.max(np.linalg.norm(qs_v - qs_r, axis=1) / scale))
        d["max_over_cells_rel_delta_fluid"] = float(np.max(np.linalg.norm(qf_v - qf_r, axis=1) / scale))
        rv = np.linalg.norm(qs_v - qf_v, axis=1) / np.linalg.norm(qf_v, axis=1)
        rr = np.linalg.norm(qs_r - qf_r, axis=1) / scale
        d["n_cells_residual_reduced"] = int(np.sum(rv < rr))
        d["n_cells"] = int(len(rv))
        d["max_over_cells_relative_variant"] = float(rv.max())
        d["max_over_cells_relative_control"] = float(rr.max())
        d["C2_relative_change"] = {ch: v["C2"][ch] / r["C2"][ch] - 1.0 for ch in ("T", "E", "B")}
        out[str(n)] = d
    return out


def main():
    summary = {"schema": "htt.r106.h2_geometry_stage.summary.1",
               "family": "VI_-1/9", "epsilon": 2e-4, "ell_max": 4, "gl_rings": 16, "n_picard": 4,
               "min_substeps": 2, "massless_neutrino_fraction": 0.0,
               "sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in sorted(HERE.glob("*.py")) + [HERE / "variant.diff", HERE / "run_one.sh"]}}
    repo1, stage1 = series("repo", 1), series("stage", 1)
    repo05, stage05 = series("repo", 0.5), series("stage", 0.5)
    summary["reproduction_R105"] = {str(n): {"first_now": repo1[n]["first_two_common"][0]["relative_norm"],
                                             "first_R105": R105_FIRST[n],
                                             "second_now": repo1[n]["first_two_common"][1]["relative_norm"],
                                             "second_R105": R105_SECOND[n]}
                                    for n in (48, 96, 192) if n in repo1}
    summary["series"] = {"repo_depth1": describe(repo1), "stage_depth1": describe(stage1),
                         "repo_depth0.5": describe(repo05), "stage_depth0.5": describe(stage05)}
    summary["ab_stage_minus_repo_depth1"] = ab(stage1, repo1)
    summary["ab_stage_minus_repo_depth0.5"] = ab(stage05, repo05)
    summary["ab_repo_depth0.5_minus_depth1"] = ab(repo05, repo1)
    summary["ab_stage_depth0.5_minus_repo_depth1"] = ab(stage05, repo1)
    ctrl = {}
    base = load("repo_N48_d1")
    for lab in ("varmid_N48_d1", "vardense_N48_d1"):
        v = load(lab)
        if v is None or base is None:
            continue
        ctrl[lab] = {
            "bit_identical_q_sky": bool(np.array_equal(v["_npz"]["q_sky"], base["_npz"]["q_sky"])),
            "bit_identical_q_fluid": bool(np.array_equal(v["_npz"]["q_fluid"], base["_npz"]["q_fluid"])),
            "bit_identical_final_state": bool(np.array_equal(v["_npz"]["final_state"], base["_npz"]["final_state"])),
            "max_rel_delta_q_sky": float(np.max(np.linalg.norm(v["_npz"]["q_sky"] - base["_npz"]["q_sky"], axis=1)
                                                / np.linalg.norm(base["_npz"]["q_fluid"], axis=1))),
            "first_relative": v["first_two_common"][0]["relative_norm"],
            "first_relative_minus_repo": v["first_two_common"][0]["relative_norm"]
            - base["first_two_common"][0]["relative_norm"],
            "time_log": v["_time"],
        }
    summary["controls_48"] = ctrl
    flrw = {}
    for lab in ("flrw_repo_N48_d1", "flrw_stage_N48_d1"):
        v = load(lab)
        if v is None:
            continue
        flrw[lab] = {"max_abs_fluid_q_over_E": v["max_abs_fluid_q_over_E"],
                     "max_abs_sky_q_over_E": v["max_abs_sky_q_over_E"],
                     "max_abs_final_state": v["max_abs_final_state"], "C2": v["C2"],
                     "max_hamiltonian": v["max_hamiltonian"], "max_codazzi": v["max_codazzi"],
                     "max_stokes_reality": v["max_stokes_reality"], "time_log": v["_time"]}
    summary["flrw_null"] = flrw
    (HERE / "SUMMARY_H2.json").write_text(json.dumps(summary, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("reproduction_R105", "controls_48", "flrw_null")}, indent=1))


if __name__ == "__main__":
    main()

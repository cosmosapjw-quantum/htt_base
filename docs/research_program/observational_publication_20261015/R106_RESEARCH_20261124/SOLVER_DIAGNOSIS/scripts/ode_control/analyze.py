"""Collect H5 ODE-control runs into H5_ODE_CONTROL.json (no solver calls)."""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np

from scripts.r105.common_time_moments import nested_samples

W = Path(__file__).resolve().parent
RUNS, LOGS = W / "runs", W / "logs"
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
R105_REF = {48: 3.1935484771574664e-06, 96: 3.539700455541186e-06, 192: 3.6292782170005017e-06}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(label):
    p = RUNS / f"{label}.npz"
    if not p.exists():
        return None
    h = dict(np.load(p))
    js = json.loads((RUNS / f"{label}.json").read_text())
    return h, js


def timing(label):
    t = (LOGS / f"{label}.time").read_text().strip().splitlines()[-1].split()
    return {"command": (LOGS / f"{label}.cmd").read_text().strip(),
            "return_code": int((LOGS / f"{label}.rc").read_text().strip()),
            "wall_s": float(t[0]), "maxrss_kB": int(t[2])}


def richardson(e1, e2, e3):
    d1, d2 = e2 - e1, e3 - e2
    if d2 == 0:
        return {"r": None, "limit": e3}
    r = d1 / d2
    return {"r": r, "limit": e3 + d2 / (r - 1.0) if r != 1 else None,
            "order_log2_r": float(np.log2(r)) if r > 0 else None}


def common_rows(common, h, key_sky="q_over_E_sky", key_fluid="q_over_E_fluid", sky=None, fluid=None):
    sky = h[key_sky][0] if sky is None else sky
    fluid = h[key_fluid][0] if fluid is None else fluid
    return nested_samples(common, h["N_end"], sky, fluid)[:2]


def run_report(label, h, js, common):
    qs, qf = h["q_over_E_sky"][0], h["q_over_E_fluid"][0]
    rel = np.linalg.norm(qs - qf, axis=1) / np.linalg.norm(qf, axis=1)
    worst = int(np.argmax(rel))
    rows = common_rows(common, h)
    i0 = rows[0]["cell_index"]
    out = {
        "label": label, "n_cells": int(len(h["N_end"])),
        "config": {k: js.get(k) for k in ("family", "epsilon", "rtol", "atol")} | {
            "ell_max": 4, "gl_rings": 16, "n_picard": 4, "substeps_per_cell": 2, "max_substep_depth": 1.0,
            "massless_neutrino_fraction": 0.0, "solver": js.get("solver", "stash_variant")},
        "first_common": {"ln_a": float(common[0]), **rows[0]},
        "second_common": {"ln_a": float(common[1]), **rows[1]},
        "first_common_cell": {"delta_tau": float(h["delta_tau"][i0]), "photon_substeps": int(h["photon_substeps"][i0]),
                              "mean_substep_depth": float(h["delta_tau"][i0] / h["photon_substeps"][i0]),
                              "pi_over_E_sky": h["pi_over_E_sky"][0, i0].tolist(),
                              "pi_over_E_fluid": h["pi_over_E_fluid"][0, i0].tolist()},
        "worst_cell": {"cell_index": worst, "ln_a": float(h["N_end"][worst]), "relative_norm": float(rel[worst]),
                       "delta_tau": float(h["delta_tau"][worst]), "photon_substeps": int(h["photon_substeps"][worst]),
                       "sky_minus_fluid": (qs[worst] - qf[worst]).tolist()},
        "max_hamiltonian": js["max_hamiltonian"], "max_codazzi": js["max_codazzi"],
        "max_stokes_reality": js["max_stokes_reality"], "C2": js["C2"], "solve_wall_s": js["solve_wall_s"],
        "final_state_sha256": js["final_state_sha256"],
    }
    try:
        out["process"] = timing(label)
    except FileNotFoundError:
        pass
    return out


def slip_block(h, idx):
    vb = h["v_b_end"][idx]
    req = 4.0 * vb / (3.0 + vb @ vb)
    qf, qs = h["q_over_E_fluid"][0, idx], h["q_over_E_sky"][0, idx]
    sf, ss = qf - req, qs - req
    res = qs - qf
    rate = float(h["rate_fn_end"][idx])
    G = h["drgamma_dN_full"][idx] - h["drgamma_dN_thomson"][idx]
    v2 = float(vb @ vb)
    J = 4.0 / (3.0 + v2) * np.eye(3) - 8.0 * np.outer(vb, vb) / (3.0 + v2) ** 2
    dreq = J @ h["dvb_dN"][idx]
    spred = (G - dreq) / rate
    return {
        "cell_index": int(idx), "ln_a": float(h["N_end"][idx]), "rate_per_efold": rate,
        "rate_grid_minus_fn": float(h["rate_grid_end"][idx] - rate),
        "v_b": vb.tolist(), "r_eq_4v_over_3_plus_v2": req.tolist(),
        "slip_fluid": sf.tolist(), "slip_sky": ss.tolist(), "slip_fluid_norm": float(np.linalg.norm(sf)),
        "slip_fluid_over_q_fluid": float(np.linalg.norm(sf) / np.linalg.norm(qf)),
        "residual_sky_minus_fluid": res.tolist(),
        "residual_over_slip_norm": float(np.linalg.norm(res) / np.linalg.norm(sf)),
        "residual_dot_slip_over_slip2": float(res @ sf / (sf @ sf)),
        "cos_residual_slip": float(res @ sf / (np.linalg.norm(res) * np.linalg.norm(sf))),
        "thomson_part_over_minus_rate": (-h["drgamma_dN_thomson"][idx] / rate).tolist(),
        "G_nonthomson": G.tolist(), "dreq_dN": dreq.tolist(),
        "tca0_slip_pred": spred.tolist(),
        "slip_fluid_over_tca0_pred_dot": float(sf @ spred / (spred @ spred)),
    }


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO, text=True).strip()
    reps, runs = {}, {}
    for fam in ("repo", "varbase", "vartight", "mimic"):
        for n in (48, 96, 192, 384):
            got = load(f"{fam}_c{n}")
            if got:
                runs[(fam, n)] = got
    common = runs[("repo", 48)][0]["N_end"]
    for (fam, n), (h, js) in runs.items():
        reps[f"{fam}_c{n}"] = run_report(f"{fam}_c{n}", h, js, common)

    # bit identity checks
    ident = {}
    for fam in ("varbase", "mimic"):
        for n in (48, 96, 192):
            if (fam, n) in runs and ("repo", n) in runs:
                h, js = runs[(fam, n)]
                r, rj = runs[("repo", n)]
                ident[f"{fam}_c{n}_vs_repo"] = {
                    "all_repo_history_arrays_equal": all(np.array_equal(h[k], r[k]) for k in r),
                    "final_state_sha_equal": js["final_state_sha256"] == rj["final_state_sha256"],
                    "C2_equal": js["C2"] == rj["C2"]}

    # R105 reproduction
    repro = {n: {"this_run": reps[f"repo_c{n}"]["first_common"]["relative_norm"], "R105_json": R105_REF[n],
                 "equal": reps[f"repo_c{n}"]["first_common"]["relative_norm"] == R105_REF[n]}
             for n in (48, 96, 192)}

    # (a) tolerance
    tol = {}
    for n in (48, 96, 192):
        hb, _ = runs[("varbase", n)]
        ht, _ = runs[("vartight", n)]
        rb, rt = common_rows(common, hb), common_rows(common, ht)
        tol[n] = {}
        for k, name in enumerate(("first_common", "second_common")):
            ib = rb[k]["cell_index"]
            dq_fluid = ht["q_over_E_fluid"][0, ib] - hb["q_over_E_fluid"][0, ib]
            dq_sky = ht["q_over_E_sky"][0, ib] - hb["q_over_E_sky"][0, ib]
            tol[n][name] = {
                "rel_base": rb[k]["relative_norm"], "rel_tight": rt[k]["relative_norm"],
                "rel_change_fraction": (rt[k]["relative_norm"] - rb[k]["relative_norm"]) / rb[k]["relative_norm"],
                "signed_base": rb[k]["sky_minus_fluid"], "signed_tight": rt[k]["sky_minus_fluid"],
                "fluid_qE_tight_minus_base": dq_fluid.tolist(), "sky_qE_tight_minus_base": dq_sky.tolist(),
                "fluid_change_over_residual": float(np.linalg.norm(dq_fluid) / rb[k]["absolute_norm"]),
            }

    # (b) dense vs grid
    dense = {}
    for (fam, n), (h, _) in runs.items():
        if "q_over_E_fluid_dense" in h:
            dense[f"{fam}_c{n}"] = {
                "max_abs_y_dense_minus_grid_all_cells": float(h["y_dense_minus_grid_absmax"].max()),
                "max_rel_y_dense_minus_grid_all_cells": float(h["y_dense_minus_grid_relmax"].max()),
                "max_abs_qE_dense_minus_recorded": float(np.abs(h["q_over_E_fluid_dense"][0] - h["q_over_E_fluid"][0]).max()),
                "max_abs_r_raw_minus_recorded": float(np.abs(h["r_raw_fluid"][0] - h["q_over_E_fluid"][0]).max()),
                "max_abs_rate_grid_minus_fn": float(np.abs(h["rate_grid_end"] - h["rate_fn_end"]).max()),
            }

    # (c) slip
    slip = {}
    for (fam, n), (h, _) in runs.items():
        if "v_b_end" not in h:
            continue
        rows = common_rows(common, h)
        slip[f"{fam}_c{n}"] = {nm: slip_block(h, rows[k]["cell_index"])
                               for k, nm in enumerate(("first_common", "second_common"))}
        # residual/slip over tight-coupled cells (rate > 10 per e-fold)
        vb = h["v_b_end"]
        req = 4.0 * vb / (3.0 + np.sum(vb * vb, 1))[:, None]
        sf = h["q_over_E_fluid"][0] - req
        res = h["q_over_E_sky"][0] - h["q_over_E_fluid"][0]
        proj = np.einsum("ij,ij->i", res, sf) / np.einsum("ij,ij->i", sf, sf)
        tc = h["rate_fn_end"] > 10.0
        slip[f"{fam}_c{n}"]["tight_cells_rate_gt_10"] = {
            "n": int(tc.sum()), "residual_dot_slip_over_slip2": proj[tc].tolist(),
            "rate": h["rate_fn_end"][tc].tolist(),
            "mean_substep_depth": (h["delta_tau"][tc] / h["photon_substeps"][tc]).tolist()}

    # mimic
    mim = {}
    for n in (48, 96, 192, 384):
        if ("mimic", n) not in runs:
            continue
        h, js = runs[("mimic", n)]
        qs, qf = h["q_over_E_sky"][0], h["q_over_E_fluid"][0]
        rows = common_rows(common, h)
        d = {}
        for key in sorted(k for k in h if k.startswith("mimic_") and not k.endswith("_nsub")):
            m = h[key]
            mf = nested_samples(common, h["N_end"], m, qf)[:2]
            sm = nested_samples(common, h["N_end"], qs, m)[:2]
            d[key] = {nm: {"mimic_minus_fluid": mf[k]["sky_minus_fluid"], "mimic_minus_fluid_rel": mf[k]["relative_norm"],
                           "sky_minus_mimic": sm[k]["sky_minus_fluid"],
                           "sky_minus_mimic_rel_to_fluid": sm[k]["absolute_norm"] / np.linalg.norm(qf[rows[k]["cell_index"]]),
                           "fraction_of_residual_explained": 1.0 - sm[k]["absolute_norm"] / rows[k]["absolute_norm"]}
                      for k, nm in enumerate(("first_common", "second_common"))}
            d[key]["nsub_matches_history"] = bool(np.array_equal(h[key + "_nsub"], h["photon_substeps"])) if "cap1.0" in key else None
            d[key]["meta"] = js["mimic"][key]
            # Prediction for the sky residual at this cap, assuming the sky-minus-mimic (model) part
            # measured at cap 1.0 with the same geometry option is cap-independent.
            geom = key.rsplit("_", 1)[1]
            ref = h[f"mimic_cap1.0_{geom}"]
            pred = (qs - ref) + (m - qf)
            pr = nested_samples(common, h["N_end"], qf + pred, qf)[:2]
            d[key]["predicted_sky_residual_at_this_cap"] = {
                nm: {"signed": pr[k]["sky_minus_fluid"], "relative_norm": pr[k]["relative_norm"]}
                for k, nm in enumerate(("first_common", "second_common"))}
            # per-cell over the whole run
            rel_mf = np.linalg.norm(m - qf, axis=1) / np.linalg.norm(qf, axis=1)
            rel_sm = np.linalg.norm(qs - m, axis=1) / np.linalg.norm(qf, axis=1)
            d[key]["max_rel_mimic_minus_fluid"] = float(rel_mf.max())
            d[key]["max_rel_sky_minus_mimic"] = float(rel_sm.max())
            d[key]["argmax_rel_sky_minus_mimic"] = int(rel_sm.argmax())
        mim[n] = d

    # Richardson on first-common relative norm
    rich = {}
    for fam in ("repo", "varbase", "vartight"):
        e = [reps[f"{fam}_c{n}"]["first_common"]["relative_norm"] for n in (48, 96, 192)]
        e2 = [reps[f"{fam}_c{n}"]["second_common"]["relative_norm"] for n in (48, 96, 192)]
        rich[fam] = {"first_common_e48_96_192": e, "first": richardson(*e),
                     "second_common_e48_96_192": e2, "second": richardson(*e2),
                     "first_96_to_192_change": e[2] - e[1]}
    if all(("mimic", n) in runs for n in (96, 192, 384)):
        e = [reps[f"mimic_c{n}"]["first_common"]["relative_norm"] for n in (96, 192, 384)]
        e2 = [reps[f"mimic_c{n}"]["second_common"]["relative_norm"] for n in (96, 192, 384)]
        rich["stash_variant_96_192_384"] = {"first_common_e96_192_384": e, "first": richardson(*e),
                                            "second_common_e96_192_384": e2, "second": richardson(*e2)}
    for cap in ("cap1.0_mid", "cap0.5_mid", "cap0.25_mid"):
        key = f"mimic_{cap}"
        ns = [n for n in (48, 96, 192, 384) if n in mim]
        if len(ns) >= 3:
            vals = [mim[n][key]["first_common"]["mimic_minus_fluid_rel"] for n in ns]
            rich[f"mimic_minus_fluid_{cap}"] = {"levels": ns, "first_common_rel": vals,
                                                "first_48_96_192": richardson(*vals[:3])}

    files = {p.name: sha(p) for p in sorted(W.glob("*.py")) + sorted(W.glob("*.sh")) + sorted(W.glob("*.diff"))}
    payload = {
        "schema": "htt.r106.h5_ode_control.1", "repo_head": head,
        "repo_solver_sha256": sha(REPO / "htt/bass/transport/coupled_einstein_boltzmann.py"),
        "hyrec_csv_sha256": sha(REPO / "htt/bass/recombination/fixtures/recombination_ref_planck2018.csv"),
        "work_files_sha256": files,
        "common_endpoints_ln_a": [float(common[0]), float(common[1])],
        "r105_reproduction": repro, "bit_identity": ident,
        "runs": reps, "tolerance_control_a": tol, "dense_vs_grid_b": dense, "slip_c": slip,
        "sdirk_mimic_c": mim, "richardson": rich,
    }
    (W / "H5_ODE_CONTROL.json").write_text(json.dumps(payload, indent=1, allow_nan=False, default=float) + "\n")
    print("saved", W / "H5_ODE_CONTROL.json")


if __name__ == "__main__":
    main()

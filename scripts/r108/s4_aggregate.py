"""R108 lane s4: aggregate the BJS VII_h comparator runs into SOLVER/S4_BJS_COMPARATOR.json.

Purpose: collect the per-Omega_0 production files written by ``scripts.r108.s4_bjs_comparator`` (work dir
~/Downloads/htt_r108/s4), evaluate the handoff S4 acceptance (one template variant reaches sky correlation
>= 0.99 in every case), summarise handedness, amplitude ratio, rotation, residuals, linearity and the
pre-registered Doppler diagnostic, and compare the convergence maps (ray step, geometry grid, ODE tolerance)
with the production map of the same case.  After the R108 review (findings S4-1..S4-7) it also writes
- the measured Doppler-component fraction of every case (from the saved maps);
- the variant comparison (residual_rms_relative and amplitude ratio of both variants, with and without the
  Doppler factors and with Richardson) as a secondary, post-acceptance diagnostic with no pre-stated threshold
  and no verdict;
- the independent global-optimality check of every fit and the full-sky spline validation
  (``scripts.r108.s4_posthoc_checks`` sidecars);
- per-run provenance (script, sources, map sha256) and this aggregator's own sha256 and command line;
- the receipts (sha256) of the two quoted papers.
Inputs: --runs (production JSON files), --convergence, --richardson, --posthoc (sidecar JSON files), maps (npz)
in the work dir, --lit-receipts/--lit-check (s4_lit_fetch outputs).  Output: --output JSON.  Units:
dimensionless; angles in degrees where the key says so, radians where it says rad.
No randomness.  Claim ceiling: numerical evidence only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

from scripts.r108.common import git_state, sha256_file, write_json
from scripts.r108.s4_bjs_comparator import euler_determined, map_paths, stable_compensating_tilt_velocity

REPO = Path(__file__).resolve().parents[2]
WORK = Path.home() / "Downloads/htt_r108/s4"
LIT = WORK / "lit_receipted"
ACCEPT = 0.99
MAP_LABELS = ("protocol", "doppler_diagnostic", "protocol_richardson", "doppler_richardson")
TILT_SRC = "htt/bass/background/tilted_bianchi_state.py"
PREFIX_FORM = "v_mag = 0.5 * (-r + math.sqrt(r * r + 4.0))"
STABLE_FORM = "v_mag = 2.0 / (r + math.sqrt(r * r + 4.0))"


def _mtime(p) -> str:
    return dt.datetime.fromtimestamp(Path(p).stat().st_mtime, dt.timezone.utc).isoformat()


def _main_map(c: dict, run: dict) -> tuple[Path, str]:
    """Main-map file of a case: the recorded ``map_files`` entry, else the legacy (pre-review) tag."""
    if "map_files" in c:
        return Path(c["map_files"]["main"]["path"]), "map_files recorded in the run"
    bg = c["background"]
    p = map_paths(c["omega0"], c["x"], c["sigma0"], c["nside"], c["max_step"], c["M"], bg["rtol"], bg["atol"],
                  richardson=False)["main"]
    return p, "legacy tag (no richardson flag in the tag; shared by production and --richardson runs)"


def _best(fits: dict, label: str, var: str) -> dict:
    fp, fm = fits[f"{label}|{var}|+1"], fits[f"{label}|{var}|-1"]
    f = fp if fp["corr"] >= fm["corr"] else fm
    return {"best_kappa": f["kappa"], "corr": f["corr"],
            "residual_rms_relative": f["residual_rms_relative"],
            "amp_ratio": f["amp_over_sigma_perp_times_sqrt2"]}


def _git_blob_sha(rel: str) -> tuple[str | None, str]:
    r = subprocess.run(["git", "-C", str(REPO), "show", f"HEAD:{rel}"], capture_output=True)
    if r.returncode != 0:
        return None, ""
    return hashlib.sha256(r.stdout).hexdigest(), r.stdout.decode()


def repo_solve_note(cases: list[dict], run_sha: str | None) -> dict:
    """Review S4-5c: what ``repo_solve_compensating_tilt_velocity_rel_error`` refers to, re-measured now."""
    from bass.background.convention_bridge import exact_momentum_divergence
    from bass.background.tilted_bianchi_state import solve_compensating_tilt_velocity
    from bass.transport.bjs_bianchi_vii_h import BJSParameters, bjs_lie_geometry_today

    head_sha, head_text = _git_blob_sha(TILT_SRC)
    now_text = (REPO / TILT_SRC).read_text()
    rows = []
    for c in cases:
        st = c["state"]
        a, n = bjs_lie_geometry_today(BJSParameters(omega0=c["omega0"], x=c["x"]))
        q = -exact_momentum_divergence(np.asarray(st["sigma_ab"]), a, n, a_sign=1)
        eps = st["dust_eps_hat"]
        v_stable = stable_compensating_tilt_velocity(q, eps_hat=eps, p_hat=0.0)
        v = np.asarray(st["dust_v"], dtype=np.float64)  # the reference the run used
        qn = float(np.linalg.norm(q))
        r = float(eps + 0.0) / qn
        v_prefix = (0.5 * (-r + math.sqrt(r * r + 4.0)) / qn) * q  # the HEAD-blob difference form, verbatim
        v_now = solve_compensating_tilt_velocity(q, eps_hat=eps, p_hat=0.0)
        rows.append({"omega0": c["omega0"], "x": c["x"],
                     "recorded_rel_error": st["repo_solve_compensating_tilt_velocity_rel_error"],
                     "prefix_form_rel_error_recomputed": float(np.linalg.norm(v_prefix - v) / np.linalg.norm(v)),
                     "current_tree_rel_error": float(np.linalg.norm(v_now - v) / np.linalg.norm(v)),
                     "stable_root_rel_diff_to_recorded_dust_v": float(np.linalg.norm(v_stable - v) / np.linalg.norm(v))})
    return {
        "field": "cases[].state.repo_solve_compensating_tilt_velocity_rel_error",
        "refers_to": f"{TILT_SRC} at run time, sha256 {run_sha} (difference form v = (-r + sqrt(r^2 + 4))/2)",
        "run_time_sha_equals_git_head_blob": head_sha == run_sha, "git_head_blob_sha256": head_sha,
        "git_head_blob_has_difference_form": PREFIX_FORM in head_text,
        "current_tree_sha256": sha256_file(REPO / TILT_SRC), "current_tree_has_stable_form": STABLE_FORM in now_text,
        "note": ("the recorded values (0.7%-36%) describe the pre-fix repository function used by the runs; the "
                 "working tree now evaluates the stable root, so a rerun with it records ~1e-16 "
                 "(current_tree_rel_error below).  The S4 states never used the repository root: they use "
                 "stable_compensating_tilt_velocity of the comparator."),
        "per_case": rows,
        "max_recorded": max(x["recorded_rel_error"] for x in rows),
        "min_recorded": min(x["recorded_rel_error"] for x in rows),
        "max_abs_recomputed_minus_recorded": max(abs(x["prefix_form_rel_error_recomputed"] - x["recorded_rel_error"])
                                                 for x in rows),
        "max_current_tree_rel_error": max(x["current_tree_rel_error"] for x in rows),
    }


def literature(receipts: Path, check: Path) -> dict:
    loc = {
        "template": "McEwen et al. 2006, MNRAS 369, 1858, appendix A eqs. A1-A12; incoming-photon angles below A3",
        "vorticity": "McEwen et al. 2006 eq. A2",
        "mode_and_shear_components": "Pontzen & Challinor 2007, MNRAS 380, 1387, sec. 5.1 (sigma_ij = 0 except "
                                     "sigma_12, sigma_13 ~ e^{-3 alpha}) and sec. 5.3 (sigma_12 = sigma_13 'for "
                                     "compatibility with previous studies')",
        "doppler_terms": "Pontzen & Challinor 2007 sec. 5.7, eq. 67 (shear-to-Doppler ratio ~30 for a common tilt)",
    }
    if receipts.exists():
        recs = [json.loads(line) for line in receipts.read_text().splitlines() if line.strip()]
        loc["pdf_receipts"] = {r["name"]: {k: r.get(k) for k in (
            "citation", "url", "final_url", "content_disposition", "bytes", "sha256", "fetched_at_utc")}
            | {"receipt_file": str(receipts),
               "earlier_unreceipted_copy_identical": r["earlier_unreceipted_copy"]["identical_to_this_fetch"]}
            for r in recs}
    else:
        loc["pdf_receipts"] = None
    if check.exists():
        ck = json.loads(check.read_text())
        loc["quoted_phrase_check"] = {p["name"]: {"phrases_found": p["phrases"], "not_checked": p["not_checked"],
                                                  "match_rule": p["match_rule"]} for p in ck["papers"]}
        loc["quoted_phrase_check_file"] = {"path": str(check), "sha256": sha256_file(check)}
    return loc


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--convergence", nargs="*", default=[])
    ap.add_argument("--richardson", nargs="*", default=[],
                    help="runs made with --richardson (fits to 2 M(sigma) - M(2 sigma)/2; post-hoc diagnostic)")
    ap.add_argument("--posthoc", nargs="*", default=[], help="s4_posthoc_checks sidecar JSON files")
    ap.add_argument("--lit-receipts", type=Path, default=LIT / "RECEIPTS.jsonl")
    ap.add_argument("--lit-check", type=Path, default=LIT / "LIT_PHRASE_CHECK.json")
    ap.add_argument("--output", required=True)
    a = ap.parse_args(argv)
    run_files = {p: json.loads(Path(p).read_text()) for p in [*a.runs, *a.richardson, *a.convergence]}
    runs = [run_files[p] for p in a.runs]
    cases = [(c, r, p) for p, r in zip(a.runs, runs) for c in r["cases"]]
    cases.sort(key=lambda t: (t[0]["omega0"], t[0]["x"]))
    rich_cases = {(c["omega0"], c["x"]): (c, run_files[p], p) for p in a.richardson for c in run_files[p]["cases"]}
    variants = sorted({v["variant"] for c, _, _ in cases for v in c["fits"].values()})

    # post-hoc sidecars: (run file, omega0, x) -> case block
    post, post_files = {}, {}
    for pf in a.posthoc:
        d = json.loads(Path(pf).read_text())
        post_files[pf] = {"sha256": sha256_file(pf), "summary": d.get("summary"), "sources_sha256": d["sources_sha256"],
                          "argv": d["argv"], "git_head": d["git"].get("head")}
        for rr in d["runs"]:
            for cc in rr["cases"]:
                post[(Path(rr["file"]).name, cc["omega0"], cc["x"])] = (cc, rr["sha256"])

    def post_fit(run_path: str, c: dict, key: str) -> dict | None:
        hit = post.get((Path(run_path).name, c["omega0"], c["x"]))
        if hit is None:
            return None
        cc, run_sha = hit
        f = cc["fits"][key]
        g = f["global_check"]
        return {"corr_check_max_minus_corr_best": g["corr_check_max_minus_corr_best"], "passes": g["passes"],
                "tol": g["tol"], "n_checks": g["n_checks"], "n_checks_in_fit_basin": g["n_checks_in_fit_basin"],
                "best_check_corr_outside_fit_basin": g["best_check_corr_outside_fit_basin"],
                "n_check_grid_local_maxima": g["n_check_grid_local_maxima"],
                "reproduction_corr_abs_diff": f["reproduction"]["corr_abs_diff"],
                "run_file_sha256_checked": run_sha == sha256_file(run_path)}

    rows = []
    for c, run, rpath in cases:
        st = c["state"]
        mpath, naming = _main_map(c, run)
        mz = np.load(mpath)
        y, yd = mz["dTT"], mz["dTT_doppler"]
        row = {"omega0": c["omega0"], "x": c["x"], "h": st["h"], "sigma0_perp": c["sigma0"], "run_file": rpath,
               "map_npz": str(mpath), "los_rms_dTT": c["los"]["rms_dTT"], "los_max_abs_dTT": c["los"]["max_abs_dTT"],
               "los_seconds": c["los"]["los_seconds"], "case_seconds": c["case_seconds"],
               "background": {k: c["background"][k] for k in (
                   "max_hamiltonian_residual_rel", "max_codazzi_residual_rel", "max_jacobi_residual",
                   "max_abs_Omega_minus_open_dust", "max_Sigma2", "max_abs_friedmann_closure",
                   "max_rel_a_axis_minus_open_dust", "max_rel_n_transverse_minus_open_dust", "max_rel_h_drift",
                   "max_rel_sigma_perp_e3N_drift", "max_rel_dust_speed_eN_drift", "max_sigma_other_over_sigma_perp",
                   "max_a_perp_over_sigma_perp", "max_n_offdiag_over_sigma_perp", "max_abs_n33_over_H",
                   "sigma_over_H_at_N_E", "Omega_at_N_E", "n_rhs_evals", "wall_s")},
               "state": {k: st[k] for k in (
                   "H_minus_1", "constraints_admissible", "constraint_normalized_residuals", "dust_speed",
                   "speed_closed_form", "dust_vorticity_over_H", "A2_omega_over_sigma",
                   "template_C1_dipole_amplitude_per_unit_sigma", "repo_solve_compensating_tilt_velocity_rel_error")},
               "linearity": c.get("linearity"), "fits": {}}
        row["state"]["repo_solve_compensating_tilt_velocity_rel_error_note"] = (
            "pre-fix repository function (see repo_solve_compensating_tilt_velocity_note); not used by the states")
        row["state"]["vorticity_ratio_to_A2_with_sigmaBJS_eq_sigma_perp"] = st["dust_vorticity_over_H"] / (
            st["A2_omega_over_sigma"] * c["sigma0"])
        row["state"]["vorticity_ratio_to_A2_with_sigmaBJS_eq_sigma_perp_over_sqrt2"] = st["dust_vorticity_over_H"] / (
            st["A2_omega_over_sigma"] * c["sigma0"] / math.sqrt(2.0))
        row["state"]["dust_speed_over_speed_closed_form"] = st["dust_speed"] / st["speed_closed_form"]
        row["identity_checks"] = {
            "observer_speed_over_template_C1_dipole_with_sigmaBJS_eq_sigma_perp_over_sqrt2": (
                st["dust_speed"] / (st["template_C1_dipole_amplitude_per_unit_sigma"] * c["sigma0"] / math.sqrt(2.0))),
            "label": ("IDENTITY_CHECK, not a measurement: C1 sqrt((1 + 3 sqrt h)^2 + (3 sqrt h - 1)^2) / sqrt(2) = "
                      "sqrt(1/x^2 + 9 (1 - Omega_0)) / (3 Omega_0) with h = (1 - Omega_0) x^2, i.e. the template "
                      "observer dipole equals speed_closed_form algebraically; the measured content is "
                      "state.dust_speed_over_speed_closed_form")}
        row["doppler_components"] = {k: c["los"][k] for k in ("observer_doppler_rms", "emitter_doppler_rms",
                                                               "doppler_map_rms", "los_vs_trace_max_abs")}
        row["doppler_component_fraction"] = {
            "rel_rms_doppler_minus_protocol_over_protocol": float(np.std(yd - y) / np.std(y)),
            "rel_rms_doppler_minus_protocol_over_doppler_map": float(np.std(yd - y) / np.std(yd))}
        prod_mtime = Path(rpath).stat().st_mtime
        sharing = [p for (om, xx), (rc, rr, p) in rich_cases.items()
                   if om == c["omega0"] and xx == c["x"] and "map_files" not in rc and naming.startswith("legacy")]
        row["map_provenance"] = {
            "path": str(mpath), "sha256": sha256_file(mpath), "bytes": mpath.stat().st_size,
            "mtime_utc": _mtime(mpath), "naming": naming, "run_json_mtime_utc": _mtime(rpath),
            "map_written_after_run_json": mpath.stat().st_mtime > prod_mtime,
            "legacy_tag_shared_with_richardson_runs": sharing,
            "richardson_run_json_mtime_utc": [_mtime(p) for p in sharing],
            "content_check_vs_run_json": {
                "rms_dTT_rel_diff": float(np.std(y) / c["los"]["rms_dTT"] - 1.0),
                "max_abs_dTT_rel_diff": float(np.max(np.abs(y)) / c["los"]["max_abs_dTT"] - 1.0),
                "doppler_map_rms_rel_diff": float(np.std(yd) / c["los"]["doppler_map_rms"] - 1.0)},
        }
        for key, f in c["fits"].items():
            fr = {k: f[k] for k in (
                "corr", "amp", "amp_over_sigma_perp", "amp_over_sigma_perp_times_sqrt2", "residual_rms",
                "residual_rms_relative", "map_rms", "axis", "euler_zyz_active_rad", "rotation_matrix",
                "template_axis_angle_to_plus_z_deg", "template_axis_angle_to_minus_z_deg",
                "rotation_angle_from_identity_deg", "corr_spline", "spline_vs_exact_max_abs", "grid_max_corr_coarse",
                "grid_argmax_corr_full", "n_grid_local_maxima", "best_other_basin_corr", "fit_seconds")}
            fr["kappa"] = f["kappa"]
            fr["n_starts_used"] = len(f["starts"])
            fr["euler_determined"] = euler_determined(np.asarray(f["rotation_matrix"]))
            fr["refined_start_corrs"] = [s["corr"] for s in f["starts"]]
            fr["spline_validation_first_4096_ring_pixels"] = f["spline_validation"]
            fr["global_check"] = post_fit(rpath, c, key)
            row["fits"][key] = fr
        hit = post.get((Path(rpath).name, c["omega0"], c["x"]))
        row["spline_validation_full_sky"] = hit[0]["spline_validation_full_sky"] if hit else None
        row["map_provenance"]["fit_reproduction_max_corr_abs_diff"] = (
            max(f["reproduction"]["corr_abs_diff"] for f in hit[0]["fits"].values()) if hit else None)
        rows.append(row)

    def table(label: str, rows) -> dict:
        out = {}
        for var in variants:
            per_case = []
            for r in rows:
                cp, cm = r["fits"][f"{label}|{var}|+1"]["corr"], r["fits"][f"{label}|{var}|-1"]["corr"]
                per_case.append({"omega0": r["omega0"], "x": r["x"], "corr_kappa_plus": cp, "corr_kappa_minus": cm,
                                 "best_kappa": 1 if cp >= cm else -1, "best_corr": max(cp, cm)})
            fixed = {k: min(pc[f"corr_kappa_{'plus' if k == 1 else 'minus'}"] for pc in per_case) for k in (1, -1)}
            out[var] = {"per_case": per_case, "min_best_corr": min(pc["best_corr"] for pc in per_case),
                        "min_corr_fixed_kappa": {"+1": fixed[1], "-1": fixed[-1]},
                        "passes_best_kappa": all(pc["best_corr"] >= ACCEPT for pc in per_case),
                        "passes_fixed_kappa": {"+1": fixed[1] >= ACCEPT, "-1": fixed[-1] >= ACCEPT},
                        "best_kappa_consistent": len({pc["best_kappa"] for pc in per_case}) == 1}
        return out

    protocol = table("protocol", rows)
    doppler = table("doppler_diagnostic", rows)
    passing = [v for v in variants if protocol[v]["passes_best_kappa"]]
    conv = []
    for p in a.convergence:
        for c in run_files[p]["cases"]:
            ref, rrun, _ = [t for t in cases if t[0]["omega0"] == c["omega0"] and t[0]["x"] == c["x"]][0]
            ref_map = _main_map(ref, rrun)[0]
            new_map = _main_map(c, run_files[p])[0]
            y_ref = np.load(ref_map)["dTT"]
            y_new = np.load(new_map)["dTT"]
            d = y_new - y_ref
            conv.append({"omega0": c["omega0"], "x": c["x"], "file": p, "max_step": c["max_step"], "M": c["M"],
                         "rtol": c["background"]["rtol"], "atol": c["background"]["atol"],
                         "ref": {"max_step": ref["max_step"], "M": ref["M"], "rtol": ref["background"]["rtol"],
                                 "atol": ref["background"]["atol"]},
                         "map_npz": {"path": str(new_map), "sha256": sha256_file(new_map)},
                         "ref_map_npz": {"path": str(ref_map), "sha256": sha256_file(ref_map)},
                         "rel_rms_map_change": float(np.sqrt(np.mean(d ** 2)) / np.sqrt(np.mean(y_ref ** 2))),
                         "rel_max_map_change": float(np.max(np.abs(d)) / np.max(np.abs(y_ref))),
                         "corr_with_ref": float(np.corrcoef(y_new, y_ref)[0, 1])})
    lin = [r["linearity"] for r in rows if r.get("linearity")]
    rich_rows = []
    for (om, xx), (c, rr, p) in sorted(rich_cases.items()):
        row = {"omega0": om, "x": xx, "file": p, "richardson": c.get("richardson"), "fits": {}}
        if "map_files" in c:
            row["map_files"] = c["map_files"]
        else:
            lp = _main_map(c, rr)[0]
            lin_p = lp.with_name(lp.stem + "_richardson.npz")
            row["map_files"] = {"richardson": {"path": str(lin_p), "sha256": sha256_file(lin_p),
                                               "mtime_utc": _mtime(lin_p)},
                                "main": {"path": str(lp), "naming": "legacy tag shared with the production run"}}
        for key, f in c["fits"].items():
            row["fits"][key] = {k: f[k] for k in (
                "corr", "amp_over_sigma_perp", "amp_over_sigma_perp_times_sqrt2", "residual_rms_relative",
                "template_axis_angle_to_minus_z_deg", "euler_zyz_active_rad", "best_other_basin_corr")}
            row["fits"][key]["kappa"] = f["kappa"]
            row["fits"][key]["euler_determined"] = euler_determined(np.asarray(f["rotation_matrix"]))
            row["fits"][key]["global_check"] = post_fit(p, c, key)
        rich_rows.append(row)
    richardson = ({"definition": "fits to 2 M(sigma0) - M(2 sigma0)/2 (second order in sigma removed); post-hoc "
                                 "diagnostic added after the production fits, not the acceptance",
                   "protocol": table("protocol_richardson", rich_rows),
                   "doppler": table("doppler_richardson", rich_rows), "cases": rich_rows}
                  if rich_rows else None)

    # ---- variant comparison (review S4-1/S4-2): numbers only, no threshold, no verdict
    vd_cases = []
    for r in rows:
        rr = [x for x in rich_rows if x["omega0"] == r["omega0"] and x["x"] == r["x"]]
        by_map = {}
        for label in MAP_LABELS:
            src = r["fits"] if label in ("protocol", "doppler_diagnostic") else (rr[0]["fits"] if rr else None)
            if src is None:
                continue
            by_map[label] = {var: _best(src, label, var) for var in variants}
        vd_cases.append({"omega0": r["omega0"], "x": r["x"],
                         "doppler_component_fraction": r["doppler_component_fraction"][
                             "rel_rms_doppler_minus_protocol_over_protocol"], "by_map": by_map})
    ranges = {}
    for label in MAP_LABELS:
        for var in variants:
            vals = [vc["by_map"][label][var] for vc in vd_cases if label in vc["by_map"]]
            if vals:
                ranges.setdefault(label, {})[var] = {
                    k: [min(v[k] for v in vals), max(v[k] for v in vals)]
                    for k in ("corr", "residual_rms_relative", "amp_ratio")}
    fracs = [vc["doppler_component_fraction"] for vc in vd_cases]
    variant_comparison = {
        "label": "SECONDARY_POST_ACCEPTANCE_DIAGNOSTIC",
        "pre_stated_threshold": None, "verdict": None,
        "variants_passing_acceptance_protocol": passing,
        "variants_with_best_kappa_corr_ge_0p99_doppler_diagnostic": [v for v in variants
                                                                      if doppler[v]["passes_best_kappa"]],
        "statement": ("No rule for 'agrees' on residual_rms_relative or on the amplitude ratio was stated before the "
                      "runs; the numbers below are reported as measured, without a variant verdict.  The "
                      "pre-registered acceptance is acceptance.protocol; the two lists above give the variants that "
                      "reach best-kappa corr >= 0.99 on the protocol and on the Doppler diagnostic maps."),
        "map_definitions": {
            "protocol": "redshift between normal observers (the acceptance map)",
            "doppler_diagnostic": "protocol map times the exact Doppler factors of the evolved dust at N = 0 and N_E",
            "protocol_richardson": "2 M(sigma0) - M(2 sigma0)/2 of the protocol map (post-hoc)",
            "doppler_richardson": "2 M(sigma0) - M(2 sigma0)/2 of the Doppler diagnostic map (post-hoc)"},
        "amp_ratio_definition": ("amp_over_sigma_perp_times_sqrt2 = fitted template (sigma/H)_0 / (sigma_perp/sqrt 2); "
                                 "1 when sigma_BJS = sigma_13 = sigma_23 = sigma_perp/sqrt 2"),
        "selection": "per case, map and variant the handedness with the larger corr (best_kappa)",
        "doppler_component_fraction_definition": "rms(dTT_doppler - dTT) / rms(dTT) on the saved nside-64 maps",
        "doppler_component_fraction_range": [min(fracs), max(fracs)],
        "per_case": vd_cases, "ranges": ranges,
    }

    # ---- global optimality (review S4-3)
    allg = [f["global_check"] for r in rows for f in r["fits"].values()] + \
           [f["global_check"] for r in rich_rows for f in r["fits"].values()]
    have = [g for g in allg if g is not None]
    global_opt = {
        "method": ("scripts.r108.s4_posthoc_checks on the saved maps: global_check of s4_bjs_comparator (finer axis "
                   "grid HEALPix nside 32 on the nside-32 map, up to 8 of its local maxima refined by Nelder-Mead on "
                   "the nside-64 map, plus 8 seeded random restarts), max(corr_check) - corr_best per fit"),
        "tol": have[0]["tol"] if have else None,
        "n_fits": len(allg), "n_fits_checked": len(have),
        "max_corr_check_minus_corr_best": max(g["corr_check_max_minus_corr_best"] for g in have) if have else None,
        "all_pass": all(g["passes"] for g in have) if have and len(have) == len(allg) else False,
        "min_n_checks_in_fit_basin": min(g["n_checks_in_fit_basin"] for g in have) if have else None,
        "max_reproduction_corr_abs_diff": max(g["reproduction_corr_abs_diff"] for g in have) if have else None,
        "all_run_file_sha256_checked": all(g["run_file_sha256_checked"] for g in have) if have else None,
        "sidecars": post_files,
        "note_on_run_field": ("the run files carry global_check_refined_ge_grid, which is true by construction (the "
                              "grid argmax is a grid local maximum and Nelder-Mead returns no worse than its start); "
                              "it is not carried into this summary"),
    }

    # ---- provenance (review S4-5)
    run_prov = []
    for p, d in run_files.items():
        run_prov.append({"file": p, "sha256": sha256_file(p), "mtime_utc": _mtime(p),
                         "role": ("production" if p in a.runs else "richardson" if p in a.richardson else
                                  "convergence"),
                         "git_head": d["git"].get("head"), "argv": d["argv"], "command": d.get("command"),
                         "sources_sha256": d["sources_sha256"],
                         "comparator_script_sha256": d["sources_sha256"].get("scripts/r108/s4_bjs_comparator.py")})
    now_src = {s: sha256_file(REPO / s) for s in next(iter(run_files.values()))["sources_sha256"]}
    changed = sorted({s for r in run_prov for s, h in r["sources_sha256"].items() if now_src.get(s) != h})
    me = Path(__file__).resolve()
    tilt_sha = {r["sources_sha256"].get(TILT_SRC) for r in run_prov}
    payload = {
        "schema": "htt.r108.s4_bjs_comparator_summary/2",
        "node": "R108 handoff S4 / R107 THEORY_FOUNDATIONS TF4 (independent BJS VII_h comparator)",
        "claim_ceiling": "numerical comparison of the exact-characteristic line of sight with the published BJS "
                         "template; no family attribution, likelihood or calibrated p",
        "claim_class": "NUMERICAL",
        "writer": {"script": str(me.relative_to(REPO)), "sha256": sha256_file(me), "argv": sys.argv,
                   "python": sys.executable, "written_utc": dt.datetime.now(dt.timezone.utc).isoformat()},
        "protocol": {
            "cases": "open dust (Omega_Lambda = Omega_r = 0), Omega_0 in {0.3, 0.5, 0.7}, x in {0.62, 1.0}, z_E = 1100",
            "state": "N = 0, H = 1; a/H = sqrt(1 - Omega_0) e_z, n/H = diag(1/x, 1/x, 0) (bjs_lie_geometry_today); "
                     "shear sigma_13 = sigma_23 = sigma_perp/sqrt(2) only; dust tilt from the exact momentum "
                     "constraint; construct_admissible_tilted_state (tol 1e-11)",
            "sigma_convention": "sigma^2 = (1/2) sigma_ab sigma^ab = sigma_13^2 + sigma_23^2 = sigma_perp^2 "
                                "(repository); amp_over_sigma_perp = fitted template (sigma/H)_0 / sigma_perp",
            "evolution": "evolve_general_tilted_bianchi DOP853, N = 0 -> N_E(1 + 2/M) with N_E on the grid",
            "line_of_sight": "los_sky, one optically thick shell at N_E (nodes N_E - 1e-3, N_E, 0; delta_tau 1e6, 0), "
                             "zero source increment, beta = None (normal observers), healpix_directions(64); "
                             "dT/T = (1 + 4T)^(1/4) - 1, monopole removed",
            "fit": "amplitude + SO(3) (active zyz, R = Rz(alpha) Ry(beta) Rz(gamma), map = amp S(R^-1 n)) of "
                   "bjs_temperature_sky; global grid over the template axis (HEALPix nside 16 on the nside-32 "
                   "map) with closed-form roll/amplitude, Nelder-Mead from up to 8 of the best grid local maxima "
                   "(the grids had 2-4; fits[].n_starts_used) on the nside-64 map, final correlation with the exact "
                   "template",
            "euler_angles": ("every fit has beta within ~2e-5 of pi, where only alpha - gamma is determined; "
                             "fits[].euler_determined gives that combination whenever |sin beta| < 1e-3"),
            "spline_validation": ("run files: first 4096 ring pixels of the rotated frame (a polar cap), kept as "
                                  "fits[].spline_validation_first_4096_ring_pixels; full sky: "
                                  "cases[].spline_validation_full_sky (post-hoc)"),
            "acceptance": "one variant reaches sky correlation >= 0.99 in every case (handoff S4)",
            "doppler_diagnostic": "pre-registered secondary map (not the acceptance): protocol redshift times the "
                                  "exact Doppler factors of the evolved dust velocity at the observer (N = 0) and at "
                                  "the emitter (N_E, ray direction from trace_rays)",
        },
        "acceptance": {"threshold": ACCEPT, "variants_passing_best_kappa": passing, "passed": bool(passing),
                       "protocol": protocol},
        "doppler_diagnostic": doppler,
        "doppler_diagnostic_note": ("passes_* in doppler_diagnostic apply the acceptance threshold 0.99 for "
                                    "comparison only; the diagnostic is not part of the acceptance"),
        "variant_comparison": variant_comparison,
        "global_optimality": global_opt,
        "linearity_summary": {"max_rel_rms_deviation": max(l["rel_rms_deviation"] for l in lin),
                              "max_rel_max_deviation": max(l["rel_max_deviation"] for l in lin),
                              "max_ratio_to_max_abs_dTT": max(l["rel_rms_deviation_over_max_abs_dTT"] for l in lin)}
        if lin else None,
        "convergence": conv,
        "richardson_diagnostic": richardson,
        "cases": rows,
        "repo_solve_compensating_tilt_velocity_note": repo_solve_note(
            [t[0] for t in cases], tilt_sha.pop() if len(tilt_sha) == 1 else None),
        "provenance": {
            "runs": run_prov,
            "current_tree_sources_sha256": now_src,
            "sources_changed_since_runs": changed,
            "sources_changed_note": ("the runs were made with the source hashes in runs[].sources_sha256; the "
                                     "listed files differ in the working tree now (the maps are not regenerated "
                                     "here; the post-hoc checks use only the saved maps and the unchanged "
                                     "bjs_bianchi_vii_h.py)"),
            "production_map_overwrite_note": (
                "before the review the --richardson runs wrote their main map under the production tag (no richardson "
                "flag in the tag), so the production map files were last written by the richardson runs "
                "(cases[].map_provenance: map_written_after_run_json, legacy_tag_shared_with_richardson_runs).  Their "
                "content equals the production runs' own record: content_check_vs_run_json (rms, max, Doppler rms) "
                "and fit_reproduction_max_corr_abs_diff (the recorded full-map correlation recomputed at every "
                "recorded axis).  The comparator now tags the main map of a richardson run with '_richrun'."),
        },
        "inputs": {p: sha256_file(p) for p in [*a.runs, *a.convergence, *a.richardson, *a.posthoc]},
        "git": git_state(),
        "literature_locators": literature(a.lit_receipts, a.lit_check),
    }
    write_json(a.output, payload)
    print(json.dumps({"passed": bool(passing), "variants_passing": passing,
                      "protocol_min_best_corr": {v: protocol[v]["min_best_corr"] for v in variants},
                      "doppler_min_best_corr": {v: doppler[v]["min_best_corr"] for v in variants},
                      "doppler_component_fraction_range": variant_comparison["doppler_component_fraction_range"],
                      "global_check_max_excess": global_opt["max_corr_check_minus_corr_best"],
                      "global_check_all_pass": global_opt["all_pass"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Build the R54 contract, state files, reports and local-agent prompt from executed results.

Every number that appears in a generated document is read from RESULTS/*.json at build
time (function ``numbers``); nothing numerical is typed by hand below. Re-run after any
re-execution of scripts/r54/run_r54_*.py:

    python scripts/r54/build_r54_contract.py build
    python scripts/r54/build_r54_contract.py mutation-receipt   # proves the declared gates bite
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / "docs/research_program/observational_publication_20261015"
R54 = PUB / "R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
RES = R54 / "RESULTS"
REL = "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116"
DATE = "2026-11-16"
BRANCH = "research/r54-tensor-frame-tomography-20261116"
BASE = "research/r50-observed-convergence-20261115"
LOCAL = "/mnt/extdrive/workdir"
TESTS = "PYTHONPATH=htt/src:htt:. python -m pytest tests/r54 -q"
MOD = "htt/htt/htt/infer"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jdump(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def g3(x: float) -> str:
    return f"{float(x):.3g}"


#: numbers that depend on pseudo-random draws; compared across machines only when the numpy version matches
MONTE_CARLO_KEYS = ("eiv_frac_lo", "eiv_frac_hi", "xb_dip_p", "xb_quad_p", "xb_joint_p", "xb_sky_frac", "xb_best_angle", "xb_pole_gain",
                    "g_tail_sky", "g_tail_angle", "g_tail_best", "inj_step_A", "inj_flow_A", "inj_step_med", "inj_flow_med", "inj_none_gain_rate",
                    "m_tail_sky", "s_tail_sky", "sc_tail_scan", "sc_tail_max", "sc_null_near_pole", "inj_obs_step_A", "inj_obs_flow_A",
                    "inj_obs_step_lock", "inj_step_lock", "inj_none_lock", "injm_obs_step_A", "injm_obs_flow_A", "injm_obs_step_lock",
                    "injm_step_A", "injm_flow_A", "x_class", "x_class_mono", "x_class_split", "x_class_robust", "h_c3_decision")


def numbers_l05(x: dict) -> dict:
    """Numbers of the catalogue-level CF4 analysis (RESULTS/R54_L05_CF4_EXACT.json)."""
    lin, log, cm, sp = x["linear_R36"], x["log_distance"], x["common_mode"]["white_plus_exact_body"], x["zero_point_split"]
    hl, hb, hg, hw = lin["headline"], lin["same_estimator_null"]["headline_bias_subtracted"], log["headline"], log["headline_white_only"]
    pd, tails, tt = log["pole_decomposition"], log["axis_locking_null"]["tails"], log["tilt_transport"]
    steps, hm = sp["hemisphere_step_by_method"]["white_plus_exact_body"], sp["method_monopoles_only"]["headline"]
    inj, injm = x["injections"]["pooled"]["cases"], x["injections"]["method_monopoles_marginalised"]["cases"]
    obs, dec, sc = x["injections"]["pooled"]["observed_size"], x["decision"], sp["hemisphere_step_scan"]
    ws, wsm = log["window_subsets"], sp["method_monopoles_only"]["window_subsets"]
    wi, wo = "inner_windows_z0.025_z0.04", "outer_windows_z0.06_z0.08"
    outer = {m: v["z_at_or_above_0.055"] for m, v in x["setup"]["composition_north_south"].items()}
    sens = {(s["body"], s["sigma_star_km_s"]): s for s in log["body_sensitivity"]}
    ratio_d = [v for row in lin["exact_over_ideal_sd"]["dipole_xyz"] for v in row]
    ratio_q = lin["exact_over_ideal_sd"]["quadrupole_mean"]
    frac = lin["same_estimator_null"]["pole_dipole_fraction_explained_by_bias"]
    jk = [v["pole_dipole_fraction"] for v in x["jackknife"].values()]
    va = log["analysis_exact_body"]["dipole"]["V_plus_A"]
    out = {
        "x_sigma_v": x["setup"]["sigma_v_1d_linear_km_s"], "x_n_groups": x["setup"]["n_groups"],
        "x_parity_op": x["parity"]["operator_max_abs_diff"], "x_parity_theta": x["parity"]["theta_max_abs_diff_vs_R36_result"],
        "x_ratio_dip_lo": min(ratio_d), "x_ratio_dip_hi": max(ratio_d), "x_ratio_quad_lo": min(ratio_q), "x_ratio_quad_hi": max(ratio_q),
        "xl_dip_p": hl["dipole_null_p"], "xl_quad_p": hl["quadrupole_null_p"], "xl_joint_p": hl["joint_null_p"], "xl_pole_gain": hl["pole_gain"],
        "xl_sky_frac": hl["sky_fraction"], "xl_best_angle": hl["best_axis_angle_to_pole_deg"],
        "eiv_frac_lo": min(frac), "eiv_frac_hi": max(frac),
        "xb_dip_p": hb["dipole_null_p"], "xb_quad_p": hb["quadrupole_null_p"], "xb_joint_p": hb["joint_null_p"], "xb_sky_frac": hb["sky_fraction"],
        "xb_best_angle": hb["best_axis_angle_to_pole_deg"], "xb_pole_gain": hb["pole_gain"],
        "g_H_lo": min(log["H_window_km_s_Mpc"]), "g_H_hi": max(log["H_window_km_s_Mpc"]),
        "g_dip_chi2": hg["dipole_null_chi2"], "g_dip_p": hg["dipole_null_p"], "g_quad_chi2": hg["quadrupole_null_chi2"], "g_quad_p": hg["quadrupole_null_p"],
        "g_joint_chi2": hg["joint_null_chi2"], "g_joint_p": hg["joint_null_p"],
        "g_chi2_V": hg["chi2_V"], "g_chi2_A": hg["chi2_A"], "g_chi2_VA": hg["chi2_V_plus_A"],
        "g_A_pct": hg["A_percent"], "g_A_mag": hg["A_equivalent_mag"], "g_A_angle": hg["A_angle_to_pole_deg"], "g_A_wald_p": hg["A_wald_p"],
        "g_Apar": pd["A_only"]["parallel"], "g_Apar_sd": pd["A_only"]["parallel_sd"], "g_Apar_z": pd["A_only"]["parallel_z_score"],
        "g_Aperp_p": pd["A_only"]["perpendicular_p_value"],
        "g_V_km_s": hg["V_only_km_s"], "g_V_l": hg["V_only_l_b_deg"][0], "g_V_b": hg["V_only_l_b_deg"][1], "g_V_watkins": hg["V_only_angle_to_watkins_deg"],
        "gw_V_km_s": hw["V_only_km_s"], "gw_V_watkins": hw["V_only_angle_to_watkins_deg"], "gw_dip_p": hw["dipole_null_p"],
        "g_V_after_A": hg["V_wald_after_A"], "g_A_after_V": hg["A_wald_after_V"],
        "g_VA_V_amp": va["V_amplitude_km_s"], "g_VA_V_cmb": va["angle_V_to_cmb_apex_deg"],
        "g_pole_gain": hg["pole_gain"], "g_gal_gain": hg["reference_axis_gains"]["galactic_pole"], "g_best_gain": hg["best_axis_gain"],
        "g_best_angle": hg["best_axis_angle_to_pole_deg"], "g_best_l": hg["best_axis_l_b_deg"][0], "g_best_b": hg["best_axis_l_b_deg"][1],
        "g_sky_frac": hg["sky_fraction"],
        "g_tail_sky": tails["sky_fraction_at_most_observed"], "g_tail_angle": tails["best_axis_angle_at_most_observed"],
        "g_tail_best": tails["best_gain_at_least_observed"], "g_tail_pole": tails["gain_pole_chi2_2dof"],
        "g_quad_wald": hg["quadrupole_constant_wald_5dof"], "g_quad_wald_p": hg["quadrupole_constant_wald_p"],
        "g_quad_pct": hg["quadrupole_constant_percent"], "g_quad_axis": hg["quadrupole_axis_angle_to_pole_deg"],
        "g_joint_p_x2": sens[("linear x2", 250.0)]["joint_null_p"], "g_joint_p_damped": sens[("damped x1", 250.0)]["joint_null_p"],
        "tt_V_p": tt["V_only"]["V_wald_p_value"], "tt_close_p": tt["V_only"]["tilt_closure_p_value"],
        "tt_close_p_A": tt["V_with_constant_dipole_marginalised"]["tilt_closure_p_value"],
        "cm_cons_p": cm["common_dipole"]["consistency_p_value"], "cm_wald_p": cm["common_dipole"]["wald_p_value"],
        "cmw_cons_p": x["common_mode"]["white"]["common_dipole"]["consistency_p_value"],
        "s_dip_p": sp["headline"]["dipole_null_p"], "s_quad_p": sp["headline"]["quadrupole_null_p"], "s_joint_p": sp["headline"]["joint_null_p"],
        "s_pole_gain": sp["headline"]["pole_gain"], "s_A_pct": sp["headline"]["A_percent"], "s_quad_wald_p": sp["headline"]["quadrupole_constant_wald_p"],
        "s_quad_axis": sp["headline"]["quadrupole_axis_angle_to_pole_deg"],
        "m_dip_p": hm["dipole_null_p"], "m_quad_p": hm["quadrupole_null_p"], "m_joint_p": hm["joint_null_p"], "m_chi2_V": hm["chi2_V"], "m_chi2_A": hm["chi2_A"],
        "st_common": steps["common_step"], "st_common_sd": steps["common_step_sd"], "st_common_p": steps["common_wald_p_value"],
        "st_cons_p": steps["consistency_p_value"], "st_mag": steps["common_delta_mu_north_minus_south_mag"], "st_mag_sd": steps["common_delta_mu_sd_mag"],
        "stw_common_p": sp["hemisphere_step_by_method"]["white"]["common_wald_p_value"],
        "jk_lo": min(jk), "jk_hi": max(jk),
        "inj_step_A": inj["hemisphere_zero_point_step"]["fraction_A_law_preferred"], "inj_flow_A": inj["bulk_flow"]["fraction_A_law_preferred"],
        "inj_step_gain": inj["hemisphere_zero_point_step"]["noise_free_pole_gain"], "inj_flow_gain": inj["bulk_flow"]["noise_free_pole_gain"],
        "inj_step_med": inj["hemisphere_zero_point_step"]["median_chi2_V_minus_chi2_A"], "inj_flow_med": inj["bulk_flow"]["median_chi2_V_minus_chi2_A"],
        "inj_none_gain_rate": inj["none"]["fraction_pole_gain_above_threshold"],
        "x_class": dec["class"], "x_class_mono": dec["class_by_nuisance_variant"]["method_monopoles_marginalised"],
        "x_class_split": dec["class_by_nuisance_variant"]["method_x_hemisphere_steps_marginalised"], "x_class_robust": dec["robust_class"],
        "x_n_null": log["axis_locking_null"]["n_null_draws"],
        "m_tail_sky": sp["method_monopoles_only"]["axis_locking_null"]["tails"]["sky_fraction_at_most_observed"],
        "s_tail_sky": sp["axis_locking_null"]["tails"]["sky_fraction_at_most_observed"],
        "m_pole_gain": hm["pole_gain"], "m_sky_frac": hm["sky_fraction"], "s_sky_frac": sp["headline"]["sky_fraction"],
        "wi_dip_p": ws[wi]["dipole"]["p_value"], "wi_quad_p": ws[wi]["quadrupole"]["p_value"], "wi_joint_p": ws[wi]["joint"]["p_value"],
        "wo_dip_p": ws[wo]["dipole"]["p_value"], "wo_quad_p": ws[wo]["quadrupole"]["p_value"], "wo_joint_p": ws[wo]["joint"]["p_value"],
        "mwi_joint_p": wsm[wi]["joint"]["p_value"], "mwo_joint_p": wsm[wo]["joint"]["p_value"],
        "outer_FP_north_frac": outer["FP"][0] / sum(outer["FP"]), "outer_FP_frac": sum(outer["FP"]) / sum(sum(v) for v in outer.values()),
        "sc_n_axes": sc["n_axes"], "sc_pole_z": sc["pole"]["z_score"], "sc_pole_rank": sc["pole"]["rank_by_abs_z"],
        "sc_best_z": sc["best_axis"]["z_score"], "sc_best_angle": sc["best_axis"]["angle_to_pole_deg"],
        "sc_tail_single": sc["tails"]["pole_single_axis_two_sided"], "sc_tail_scan": sc["tails"]["scan_max_at_least_pole_value"],
        "sc_tail_max": sc["tails"]["scan_max_at_least_observed_max"], "sc_null_near_pole": sc["tails"]["null_fraction_best_axis_within_10deg_of_pole"],
        "sc_var_ratio": sc["variance_ratio_best_single_family_to_common_at_pole"],
        "inj_obs_step_mag": obs["step_mag"], "inj_obs_flow": obs["flow_km_s"],
        "inj_step_mag": x["injections"]["pooled"]["step_mag"], "inj_flow": x["injections"]["pooled"]["flow_km_s"],
        "gain_thr": x["injections"]["pooled"]["gain_threshold"], "sc_n_obj": sc["n_objects"],
        "inj_obs_step_A": inj["hemisphere_step_observed_size"]["fraction_A_law_preferred"],
        "inj_obs_flow_A": inj["bulk_flow_observed_size"]["fraction_A_law_preferred"],
        "inj_obs_step_lock": inj["hemisphere_step_observed_size"]["fraction_pole_locked_flag"],
        "inj_step_lock": inj["hemisphere_zero_point_step"]["fraction_pole_locked_flag"], "inj_none_lock": inj["none"]["fraction_pole_locked_flag"],
        "injm_step_A": injm["hemisphere_zero_point_step"]["fraction_A_law_preferred"], "injm_flow_A": injm["bulk_flow"]["fraction_A_law_preferred"],
        "injm_obs_step_A": injm["hemisphere_step_observed_size"]["fraction_A_law_preferred"],
        "injm_obs_flow_A": injm["bulk_flow_observed_size"]["fraction_A_law_preferred"],
        "injm_obs_step_lock": injm["hemisphere_step_observed_size"]["fraction_pole_locked_flag"],
    }
    # H-C3 is promoted only if the two depth laws are told apart at the observed-size amplitudes on both operators (rule written before that run was read)
    rates = [(out[f"inj{t}_obs_step_A"], out[f"inj{t}_obs_flow_A"]) for t in ("", "m")]
    out["h_c3_decision"] = "PROMOTE" if all(a >= 0.9 and b <= 0.1 for a, b in rates) else "HOLD"
    for m in ("FP", "OTHER", "SN", "TF"):
        out[f"st_{m}"], out[f"st_{m}_sd"] = steps["per_method"][m]["step"], steps["per_method"][m]["sd"]
        out[f"cm_{m}_p"], out[f"cmw_{m}_p"] = cm["per_method"][m]["p_value"], x["common_mode"]["white"]["per_method"][m]["p_value"]
    return out


def numbers(l1: dict | None = None, l5: dict | None = None, l05: dict | None = None) -> dict:
    """Flat register of every number that may appear in a generated document.

    The arguments default to the committed result files; tests pass recomputed blocks
    to prove that the committed numbers are reproducible (tests/r54/test_r54_results_binding.py).
    """
    l1 = json.loads((RES / "R54_L1_TYPE1_TE.json").read_text()) if l1 is None else l1
    l5 = json.loads((RES / "R54_L5_LOWZ_FRAMES.json").read_text()) if l5 is None else l5
    l05 = json.loads((RES / "R54_L05_CF4_EXACT.json").read_text()) if l05 is None else l05
    h, d = l1["history"], l1["data"]
    pf, pn = h["perfect_fluid"], h["photon_neutrino_stress"]
    res, phys, physf = d["results"], d["physics_primary"]["present_shear_over_H"], d["physics_B_null_floor"]["present_shear_over_H"]
    lc, lm, cnt = l5["cf4"]["analysis"]["MEAS_PLUS_LCDM"], l5["cf4"]["analysis"]["MEAS"], l5["count_dipoles"]
    lock, ref = lc["axis_locking"], lc["axis_locking"]["delta_chi2_at_reference_axes"]
    sweep = sorted(pn["neutrino_decoupling_initial_condition_sweep"], key=lambda s: s["z_init"])     # full sweep, no cut
    first = sweep[0]["Sigma_T_per_unit_initial_shear"]
    flip = next((i for i, s in enumerate(sweep) if s["Sigma_T_per_unit_initial_shear"] * first < 0), len(sweep))
    pre = sweep[:flip]                                                                               # before Sigma_T changes sign
    no = pn["normal_ordering_minimal_masses"]
    late = {row["z_max"]: row for row in d["late_time_shear_bounds"]["primary"]}
    late_f = {row["z_max"]: row for row in d["late_time_shear_bounds"]["B_null_floor"]}
    sens = {row["z_max"]: row for row in h["late_time_sensitivity"]}
    t_only = d["t_only_r51_reproduction"]
    n = {
        "r_E_pf": pf["r_E"], "I_T": pf["Sigma_T_over_s0"], "I_ratio": pf["Sigma_T_over_I_hist"], "I_sharp": pf["r51_sharp_last_scattering_I_hist"],
        "reion_share": pf["reionization_share_of_r_E"], "K_E_max": h["kernel_extrema"]["K_E_max"],
        "r_E_photon": h["photon_stress"]["r_E"], "s0_photon": h["photon_stress"]["s_today_over_Sigma_T"],
        "c_T": pn["massless"]["s_today_coefficients"]["c_T"], "c_E": pn["massless"]["s_today_coefficients"]["c_E"],
        "c_T_m": no["s_today_coefficients"]["c_T"], "c_E_m": no["s_today_coefficients"]["c_E"],
        "nu_m2": pn["neutrino_masses_eV"][1], "nu_m3": pn["neutrino_masses_eV"][2],
        "sweep_n": len(sweep), "sweep_z_lo": sweep[0]["z_init"], "sweep_z_hi": sweep[-1]["z_init"],
        "sweep_flips": flip < len(sweep), "sweep_z_pre": pre[-1]["z_init"], "sweep_z_flip": sweep[min(flip, len(sweep) - 1)]["z_init"],
        "sweep_T_pre": pre[-1]["T_nu_MeV"], "sweep_T_flip": sweep[min(flip, len(sweep) - 1)]["T_nu_MeV"],
        "rE_lo": min(s["r_E"] for s in pre), "rE_hi": max(s["r_E"] for s in pre),
        "rE_all_lo": min(s["r_E"] for s in sweep), "rE_all_hi": max(s["r_E"] for s in sweep),
        "s0r_lo": min(s["s_today_over_Sigma_T"] for s in sweep), "s0r_hi": max(s["s_today_over_Sigma_T"] for s in sweep),
        "primary": d["primary_carrier"], "B_p": d["null_gates"]["B_l2"]["p_value"], "B_p_comm": d["null_gates"]["commander_B_l2"]["p_value"],
        "E_p": d["null_gates"]["E_l2"]["p_value"], "B_rms_obs": d["null_gates"]["B_l2"]["observed_rms_uK"],
        "B_rms_ffp": d["null_gates"]["B_l2"]["ffp10_rms_uK"], "B_gate_pass": d["B_null_gate"]["pass"],
        "sdT": sum(res["primary"]["sd_T"]) / 5, "sdE": sum(res["primary"]["sd_E"]) / 5, "wald_all_p": res["primary"]["wald_all"]["p_value"],
        "wald_all_stat": res["primary"]["wald_all"]["statistic"], "wald_all_law": res["primary"]["wald_all"]["law"], "infl_primary": res["primary"]["inflation_sd"],
        "SigT_max": res["primary"]["Sigma_T_frobenius_range_95"]["norm_max"], "SigE_max": res["primary"]["Sigma_E_frobenius_range_95"]["norm_max"],
        "SigE_max_floor": res["B_null_floor"]["Sigma_E_frobenius_range_95"]["norm_max"],
        "SigE_max_comm": res["commander_cross_pipeline"]["Sigma_E_frobenius_range_95"]["norm_max"],
        "s0_pf_T": phys["perfect_fluid_T_only"]["frobenius_range_95"]["norm_max"],
        "s0_pf_TE": phys["perfect_fluid_T_plus_E"]["frobenius_range_95"]["norm_max"],
        "s0_pf_TE_floor": physf["perfect_fluid_T_plus_E"]["frobenius_range_95"]["norm_max"],
        "s0_as": phys["photon_neutrino_stress_two_mode"]["frobenius_range_95"]["norm_max"],
        "s0_as_floor": physf["photon_neutrino_stress_two_mode"]["frobenius_range_95"]["norm_max"],
        "s0_as_no": phys["photon_neutrino_stress_two_mode_normal_ordering"]["frobenius_range_95"]["norm_max"],
        "late_I_T": sens[0.2]["I_T_constant"], "late_I_E": sens[0.2]["I_E_constant"],
        "late_T_const": late[0.2]["constant_sign_bound_from_T"], "late_T_rms": late[0.2]["sign_changing_rms_bound_from_T"],
        "late_E_rms": late[0.2]["sign_changing_rms_bound_from_E"], "late_E_rms_floor": late_f[0.2]["sign_changing_rms_bound_from_E"],
        "late_E_rms_z05": late[0.5]["sign_changing_rms_bound_from_E"], "late_E_rms_z2": late[2.0]["sign_changing_rms_bound_from_E"],
        "dir_T": d["five_views"]["F"]["Sigma_T_directional"]["max_abs_directional_bound"],
        "dir_E": d["five_views"]["F"]["Sigma_E_directional"]["max_abs_directional_bound"],
        "pi_loo": t_only["Pi_loo"]["p_value"], "loo_ratio": sum(t_only["loo_sd_over_plugin_sd"]) / 5, "infl": t_only["inflation_sd_analytic"],
        "pf_transport_p": d["physics_primary"]["transport_perfect_fluid"]["p_value"],
        "dip_chi2": lc["dipole"]["null"]["statistic"], "dip_p": lc["dipole"]["null"]["p_value"],
        "chi2_V": lc["dipole"]["models"]["V_constant_velocity"]["chi2"], "chi2_A": lc["dipole"]["models"]["A_constant_dH"]["chi2"],
        "A_pct": lc["dipole"]["A_only"]["percent_of_H"], "A_mag": lc["dipole"]["A_only"]["equivalent_mag"],
        "A_angle": lc["dipole"]["A_only"]["angle_to_equatorial_pole_axis_deg"], "A_wald_p": lc["dipole"]["A_only"]["wald_p_value"],
        "VA_V_wald": lc["dipole"]["V_plus_A"]["V_wald_3dof"], "VA_A_wald": lc["dipole"]["V_plus_A"]["A_wald_3dof"],
        "quad_chi2": lc["quadrupole"]["null"]["statistic"], "quad_p": lc["quadrupole"]["null"]["p_value"],
        "quad_angle": lc["quadrupole"]["constant_tensor"]["principal_axis_angle_to_equatorial_pole_deg"],
        "quad_pct": lc["quadrupole"]["constant_tensor"]["percent_of_H"],
        "lock_pole": ref["equatorial_pole"], "lock_gal": ref["galactic_pole"], "lock_sgp": ref["supergalactic_pole"],
        "lock_cmb": ref["cmb_dipole_axis"], "lock_ecl": ref["ecliptic_pole"], "lock_null": lock["null_chi2"],
        "lock_best": lock["best_axis"]["delta_chi2"], "lock_angle": lock["best_axis"]["angle_to_equatorial_pole_axis_deg"],
        "lock_frac": lock["sky_fraction_of_axes_with_gain_at_least_equatorial_pole"], "lock_ngrid": lock["n_grid_axes"],
        "lock_dip": lock["equatorial_pole_fit"]["dH_dipole_km_s_Mpc"], "lock_dip_sd": lock["equatorial_pole_fit"]["dH_dipole_sd"],
        "lock_dip_pct": lock["equatorial_pole_fit"]["dH_dipole_percent_of_H"], "lock_dip_mag": lock["equatorial_pole_fit"]["dipole_equivalent_mag"],
        "lock_quad": lock["equatorial_pole_fit"]["axisymmetric_quadrupole_km_s_Mpc"], "lock_quad_sd": lock["equatorial_pole_fit"]["quadrupole_sd"],
        "lock_resid_p": lock["equatorial_pole_fit"]["residual_p_value"],
        "V_l": lm["dipole"]["V_only"]["direction_l_b_deg"][0], "V_b": lm["dipole"]["V_only"]["direction_l_b_deg"][1],
        "V_amp": lm["dipole"]["V_only"]["amplitude_km_s"], "V_watkins": lm["dipole"]["V_only"]["angle_to_watkins_2023_deg"],
        "quaia_p": cnt["Quaia_G20"]["excess_test"]["p_value"], "nvss_p": cnt["NVSS"]["excess_test"]["p_value"],
        "common_p": cnt["common_excess_velocity"]["wald_p_value"],
        "count_power": cnt["power_against_doubled_dipole"]["power_at_alpha_0p05"],
        "count_power_01": cnt["power_against_doubled_dipole"]["power_at_alpha_0p01"],
    }
    if n["late_T_rms"] != "inf":
        raise SystemExit("the T functional is expected to be blind to the sign-changing late-time construction; re-derive the text if this changes")
    n["n_sims"] = int(d["inputs"]["n_sims"])
    n.update(numbers_l05(l05))
    n.update(numbers_local())
    check_text_premises(n)
    return n


LOCAL_RESULT_FILES = {"R54-L01": "R54_L01_RESULT.json", "R54-L04": "R54_L04_RESULT.json", "R54-L02": "R54_L02_RESULT.json",
                      "R54-L03": "R54_L03_RESULT.json", "R54-L06": "R54_L06_JOINT.json", "R54-L07": "R54_L07_BENCHMARK.json"}
LOCAL_ORDER = ("R54-L01", "R54-L04", "R54-L02", "R54-L03", "R54-L06", "R54-L07", "R54-L08")


def local_result(nid: str) -> dict | None:
    path = RES / LOCAL_RESULT_FILES.get(nid, "-")
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None


def node_status(nid: str) -> str:
    """Status of a local node derived from its committed outputs (never typed): a BLOCKER note, the result status and its acceptance table."""
    if (R54 / f"BLOCKER_{nid}.md").is_file():
        return "FAILED_ACCEPTANCE"
    if nid == "R54-L08":
        return "DONE_SCOPED_C0" if (R54 / "FINAL_DECISION_R57.md").is_file() else "PENDING_LOCAL"
    r = local_result(nid)
    if r is None:
        return "PENDING_LOCAL"
    if r.get("status") != "DONE_SCOPED_C0":
        return str(r.get("status"))
    acc = r.get("acceptance", {})
    return "DONE_SCOPED_C0" if acc and all(v["pass"] for v in acc.values()) else "FAILED_ACCEPTANCE"


def numbers_local() -> dict:
    """Numbers of the executed local nodes (only the nodes whose result file exists)."""
    out: dict = {}
    x = local_result("R54-L01")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        lc, b, opt, rc = x["loo_calibration"], x["b_null_empirical"], x["optional_legs"], x["results_calibrated"]
        hm, pd = opt["half_mission"], opt["pipeline_dispersion"]
        out.update({
            "l01_ident": x["covariance_identity_rel"], "l01_edev": x["e_response"]["e_dev"], "l01_eflag": x["e_response"]["flag"],
            "l01_JB": x["e_response"]["norm_B_rows_rel"], "l01_cov95_lo": min(lc["coverage_95"]), "l01_cov95_hi": max(lc["coverage_95"]),
            "l01_cov68_lo": min(lc["coverage_68"]), "l01_cov68_hi": max(lc["coverage_68"]), "l01_cov95_pool": lc["coverage_95_pooled"],
            "l01_cov68_pool": lc["coverage_68_pooled"], "l01_calibrated": "CALIBRATED" if lc["calibrated"] else "SUPERSEDED",
            "l01_q95_lo": min(lc["empirical_quantile_inflation_95"]), "l01_q95_hi": max(lc["empirical_quantile_inflation_95"]),
            "l01_wald_cov95": lc["wald_coverage_hotelling"]["coverage_95"],
            "l01_Wall_p": lc["tails"]["W_all"]["p_value"], "l01_WT_p": lc["tails"]["W_T"]["p_value"], "l01_WE_p": lc["tails"]["W_E"]["p_value"],
            "l01_B_p": b["SMICA"]["p_value"], "l01_B_p_comm": b["Commander"]["p_value"], "l01_B_hot": b["hotelling_reference"]["p_value"],
            "l01_B_pass": bool(b["pass"]), "l01_pi_t": x["t_only"]["Pi_loo"]["p_value"],
            "l01_hm_status": hm["status"], "l01_pd_status": pd["status"],
            "l01_E_status": rc["E_lane_status"], "l01_primary": rc["primary_carrier"],
            "l01_sdT": sum(rc["primary"]["sd_T"]) / 5, "l01_sdE": sum(rc["primary"]["sd_E"]) / 5})
        if hm["status"] == "DONE_SCOPED_C0":
            out.update({"l01_hm_E2": hm["E2_rms_uK"], "l01_hm_B2": hm["B2_rms_uK"], "l01_noise_E2": hm["ffp10_noise_E2_rms_uK"],
                        "l01_noise_B2": hm["ffp10_noise_B2_rms_uK"]})
        if pd["status"] == "DONE_SCOPED_C0":
            out.update({"l01_B_p_" + k.lower(): v["p_value"] for k, v in pd["B2_tail_by_pipeline"].items()})
            out.update({"l01_disp_E2": pd["E2_dispersion_variance_uK2"] ** 0.5, "l01_disp_B2": pd["B2_dispersion_variance_uK2"] ** 0.5})
    x = local_result("R54-L04")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        st, sw = x["survey_steps"]["white_plus_exact_body"], x["survey_steps"]["white"]
        off = x["survey_offsets"]["white_plus_exact_body"]
        lv, cl = x["nuisance_variants"]["local"], x["nuisance_variants"]["classes"]
        dec = x["decision"]
        no6 = x["leave_6dfgs_proxy_out"]
        ut = x["survey_table"]["unpooled"]
        out.update({
            "l04_cov": x["label_join"]["label_join_coverage"], "l04_n_sdss": ut["FP_SDSS"]["n"], "l04_n_notsdss": ut["FP_NOT_SDSS"]["n"],
            "l04_n_mixed": ut["FP_MIXED"]["n"], "l04_fn_sdss": ut["FP_SDSS"]["fraction_north"], "l04_fn_notsdss": ut["FP_NOT_SDSS"]["fraction_north"],
            "l04_step_surveys": ", ".join(st["per_survey"]), "l04_common": st["common_step"], "l04_common_sd": st["common_step_sd"],
            "l04_common_z": st["common_z"], "l04_common_mag": st["common_delta_mu_north_minus_south_mag"], "l04_cons_p": st["consistency_p_value"],
            "l04_common_white_z": sw["common_z"], "l04_z_tf": st["per_survey"]["TF_ALL"]["z_score"], "l04_z_sn": st["per_survey"]["SN_ALL"]["z_score"],
            "l04_z_fp": st["per_survey"]["FP_SDSS"]["z_score"], "l04_z_other": st["per_survey"]["OTHER_ALL"]["z_score"],
            "l04_off_mag": off["FP_NOT_SDSS-FP_SDSS"]["delta_mu_mag"], "l04_off_sd": off["FP_NOT_SDSS-FP_SDSS"]["delta_mu_sd_mag"],
            "l04_off_z": off["FP_NOT_SDSS-FP_SDSS"]["z_score"],
            "l04_ls_joint_p": lv["log_survey"]["headline"]["joint_null_p"], "l04_ls_quad_p": lv["log_survey"]["headline"]["quadrupole_constant_wald_p"],
            "l04_ls_dip_p": lv["log_survey"]["headline"]["dipole_null_p"],
            "l04_rad_p": lv["log_mono_radial"]["headline"]["joint_null_p"], "l04_gal_p": lv["log_mono_galactic"]["headline"]["joint_null_p"],
            "l04_err_p": lv["log_mono_error"]["headline"]["joint_null_p"],
            "l04_ls_tail": lv["log_survey"]["locking_tail"], "l04_rad_tail": lv["log_mono_radial"]["locking_tail"],
            "l04_gal_tail": lv["log_mono_galactic"]["locking_tail"], "l04_err_tail": lv["log_mono_error"]["locking_tail"],
            "l04_cls_survey": cl["log_survey"], "l04_cls_radial": cl["log_mono_radial"], "l04_cls_galactic": cl["log_mono_galactic"],
            "l04_cls_error": cl["log_mono_error"], "l04_robust": dec["robust_class"], "l04_step_class": dec["step_class"],
            "l04_no6_joint_p": no6["headline"]["joint_null_p"], "l04_no6_dip_p": no6["headline"]["dipole_null_p"],
            "l04_no6_outer_p": no6["window_subsets"]["outer_windows_z0.06_z0.08"]["joint"]["p_value"],
            **{f"l04_stab_{k}": v["common_step"] for k, v in x["stability"]["splits"].items()},
            **{f"l04_stab_z_{k}": v["common_z"] for k, v in x["stability"]["splits"].items()}})
    x = local_result("R54-L02")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        tt, ct, et, ae, bn = x["t_analytic_covariance_test"], x["cross_experiment_T"], x["e_lane_table"], x["adopted_e_covariance"], x["b_null_adopted"]
        out.update({
            "l02_lrt": tt["lrt"]["statistic"], "l02_lrt_dof": tt["lrt"]["dof"], "l02_lrt_p": tt["lrt"]["p_value"],
            "l02_diag": tt["lrt"]["max_abs_diag_ratio_minus_1"], "l02_trunc": tt["truncation_check_ell_le_20_max_rel_diff"],
            "l02_adopt": "ADOPTED" if tt["adopted"] else "NOT_ADOPTED", "l02_t_reason": tt["reason"],
            "l02_shift_wmap": ct["experiments"]["WMAP9_ILC"]["max_abs_shift_sd"], "l02_shift_cg": ct["experiments"]["Cosmoglobe_DR1"]["max_abs_shift_sd"],
            "l02_shift_bp": ct["experiments"]["BeyondPlanck_v2"]["max_abs_shift_sd"], "l02_t_lane": ct["status"],
            "l02_fsky_t": ct["f_sky"]["union_T"], "l02_fsky_p": ct["f_sky"]["union_P"],
            "l02_cg_E": et["Cosmoglobe_DR1"]["Sigma_E_frobenius"], "l02_bp_E": et["BeyondPlanck_v2_posterior"]["Sigma_E_frobenius_posterior_mean"],
            "l02_wm_E": et["WMAP9_V"]["Sigma_E_frobenius"], "l02_bp_n": et["BeyondPlanck_v2_posterior"]["n_samples"],
            "l02_pr4_diff_p": et["PR4_frequency_cache"]["difference_test"]["p_value"],
            "l02_floor": ae["floor_uK2"], **{f"l02_floor_{k}": v for k, v in ae["components_uK2"].items()},
            **{f"l02_bnull_{k}": v["p_value"] for k, v in bn.items()},
            "l02_families": ", ".join(x["passing_families"]) or "none", "l02_e_status": x["e_lane_status"]})
    x = local_result("R54-L03")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        ex, vn, cp, cm = x["excess_tests"], x["velocity_null"], x["competitors"], x["common_excess"]
        out.update({
            "l03_repro": x["receipt_reproduction"]["max_abs_D_icrs_difference"],
            "l03_body_q": x["clustering_body"]["mock_sd_axis"]["Quaia_G20"], "l03_body_n": x["clustering_body"]["mock_sd_axis"]["NVSS"],
            "l03_bias_q": max(abs(v) for v in vn["Quaia_G20"]["bias_over_sd"]), "l03_bias_n": max(abs(v) for v in vn["NVSS"]["bias_over_sd"]),
            "l03_sd_q": max(vn["Quaia_G20"]["sd"]), "l03_sd_n": max(vn["NVSS"]["sd"]),
            "l03_p_q": ex["Quaia_G20"]["chi2"]["p_value"], "l03_p_n": ex["NVSS"]["chi2"]["p_value"],
            "l03_pi_q": ex["Quaia_G20"]["Pi_mock"]["p_value"], "l03_pi_n": ex["NVSS"]["Pi_mock"]["p_value"],
            "l03_v_q": ex["Quaia_G20"]["implied_excess_velocity_km_s"], "l03_v_n": ex["NVSS"]["implied_excess_velocity_km_s"],
            "l03_common_p": cm["wald"]["p_value"], "l03_common_cons_p": cm["consistency"]["p_value"],
            "l03_w_D": cp["Wagenveld2023_NVSS_Poisson"]["owned"]["D"], "l03_w_pub": cp["Wagenveld2023_NVSS_Poisson"]["published"]["D"],
            "l03_w_N": cp["Wagenveld2023_NVSS_Poisson"]["owned"]["n_sources_in_pixels"], "l03_w_Npub": cp["Wagenveld2023_NVSS_Poisson"]["published"]["n_sources"],
            "l03_w_status": cp["Wagenveld2023_NVSS_Poisson"]["status"], "l03_w_dz": cp["Wagenveld2023_NVSS_Poisson"]["amplitude_difference_in_published_sd"],
            "l03_m_D": cp["Mittal2024_Quaia_Poisson"]["owned"]["D"], "l03_m_pub": cp["Mittal2024_Quaia_Poisson"]["published"]["D"],
            "l03_m_status": cp["Mittal2024_Quaia_Poisson"]["status"], "l03_m_dz": cp["Mittal2024_Quaia_Poisson"]["amplitude_difference_in_published_sd"],
            "l03_excess_decision": x["decision"]["excess"]})
    x = local_result("R54-L06")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        tp, ts, cl, idn = x["transport_table"]["polar_vector"], x["transport_table"]["stf2"], x["transport_table"]["tilt_closure"], x["identification"]
        for i, h in enumerate(tp):
            out.update({f"l06_p{i}_chi2": h["chi2"], f"l06_p{i}_dof": h["dof"], f"l06_p{i}_p": h["p_value"], f"l06_p{i}_name": h["hypothesis"]})
        for i, h in enumerate(ts):
            out.update({f"l06_s{i}_chi2": h["chi2"], f"l06_s{i}_dof": h["dof"], f"l06_s{i}_p": h["p_value"], f"l06_s{i}_name": h["hypothesis"]})
        out.update({"l06_np": len(tp), "l06_ns": len(ts), "l06_closure_p": cl["tail"]["p_value"], "l06_closure_chi2": cl["tail"]["statistic"],
                    "l06_closure_prelim_p": cl["preliminary_receipt_closure_p_R54_L05"],
                    "l06_rank_p": idn["polar_vector_V_w_free"]["rank"], "l06_dim_p": idn["polar_vector_V_w_free"]["dim"],
                    "l06_rank_s": idn["stf2_perfect_fluid"]["rank"], "l06_rank_s_stress": idn["stf2_with_radiation_stress"]["rank"],
                    "l06_dim_s": idn["stf2_perfect_fluid"]["dim"], "l06_s0_max": x["blocks"]["stf2"]["s0_frobenius_range_95"][1]})
    x = local_result("R54-L07")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        out.update({f"l07_n_{k.lower()}": v for k, v in x["score_counts"].items()})
        out.update({f"l07_{k}_status": v["status"] for k, v in x["targets"].items()})
        out.update({f"l07_{k}_score": v["score"] for k, v in x["targets"].items()})
        ev = x["evidence_verification"]
        out.update({"l07_ev_verified": sum(1 for v in ev.values() if v["status"] == "VERIFIED"), "l07_ev_checked": len(ev),
                    "l07_ev_open": ", ".join(k for k, v in ev.items() if v["status"] != "VERIFIED")})
    return out


def check_text_premises(n: dict) -> None:
    """Qualitative words in the templates are true only under these conditions on the bound numbers (R54-IR-06).
    A regenerated result that breaks one stops the build instead of printing a stale qualifier."""
    premises = {
        "sweep interval contains the 3.12 MeV decoupling estimate (E49)": (not n["sweep_flips"]) or n["sweep_T_pre"] <= 3.12 <= n["sweep_T_flip"],
        "B ell=2 null gate fails ('B-null gate 실패')": n["B_p"] < 0.01,
        "E ell=2 null gate passes ('E ell=2는 통과')": n["E_p"] >= 0.01,
        "depth laws not told apart at the observed sizes (H-C3 HOLD)": n["h_c3_decision"] == "HOLD",
        "35970 groups typed in the templates": n["x_n_groups"] == 35970,
        "FFP10 N=300 typed in the templates": n["n_sims"] == 300,
        "quadrupole axis moves by tens of degrees under the zero-point split": abs(n["s_quad_axis"] - n["g_quad_axis"]) >= 20.0,
    }
    failed = [k for k, ok in premises.items() if not ok]
    if failed:
        raise SystemExit("template premise no longer holds; re-derive the text: " + "; ".join(failed))


# --------------------------------------------------------------------------- evidence
V = "VERIFIED_WEBSEARCH_2026-11-16"
P = "PRIOR_LEDGER_R50_R53_NOT_REVERIFIED"
M = "FROM_MEMORY_UNVERIFIED_IDENTIFIER"
EVIDENCE = [
    ("E01", "Saadeh, Feeney, Pontzen, Peiris, McEwen 2016, PRL 117, 131302", "arXiv:1605.07178", V, "Bianchi limits from Planck T+pol with perfect-fluid content; (sigma_V/H)_0 < 4.7e-11, regular tensor mode < 1.0e-6 (95%)"),
    ("E02", "Saadeh et al. 2016, MNRAS 462, 1802", "arXiv:1604.01024", V, "framework for general Bianchi tests; energy content modelled as perfect fluids"),
    ("E03", "Pontzen & Challinor 2007, MNRAS 380, 1387", "arXiv:0706.2075", V, "CMB polarization in Bianchi models; shear after matter-radiation equality generates large polarization"),
    ("E04", "Pontzen 2009, PRD 79, 103518", "arXiv:0901.2122", V, "full freedom of Bianchi CMB patterns"),
    ("E05", "Adamek, Durrer, Fenu, Vonlanthen 2011, JCAP 06, 017", "arXiv:1102.5235", V,
     "free-streaming relativistic particles in Bianchi I develop an anisotropic pressure that isotropizes; CMB temperature limits on a homogeneous magnetic field are invalid for neutrino masses below the decoupling temperature"),
    ("E06", "Barrow & Maartens 1999, PRD 59, 043502", "arXiv:astro-ph/9808268", V, "anisotropic stress dominates shear evolution of almost-FLRW models"),
    ("E07", "Barrow 1997, PRD 55, 7451", "arXiv:gr-qc/9701038", V, "limits on slightly skew stresses"),
    ("E08", "Hu & White 1997, PRD 56, 596", "arXiv:astro-ph/9702170", M, "total-angular-momentum Boltzmann hierarchy; P = (Theta_2 - sqrt6 E_2)/10 (coefficients re-derived and SymPy-sealed in R54)"),
    ("E09", "Stiskalek, Desmond, Lavaux 2026, MNRAS 546 (No evidence for local H0 anisotropy from Tully-Fisher or supernova distances)", "arXiv:2509.14997", V,
     "CF4 TF W1 zero-point dipole 0.087 +- 0.019 mag = 4.1 +- 0.9 % in H; Pantheon+ 0.049 +- 0.013 mag; degenerate with an H0 dipole; with a radially varying velocity dipole the result is consistent with LCDM flows"),
    ("E10", "Watkins et al. 2023, MNRAS 524, 1885", "arXiv:2302.02028", V, "CF4 bulk flow 419 +- 36 km/s at 200 h^-1 Mpc toward (l,b) = (298, -8)"),
    ("E11", "Whitford, Howlett, Davis 2023, MNRAS 526, 3051", "arXiv:2306.11269", V, "CF4 bulk-flow estimators; zero-point offsets explored"),
    ("E12", "Hoffman et al. 2024", "arXiv:2311.01340", V, "CF4 reconstruction; 230 +- 136 km/s at 300 h^-1 Mpc"),
    ("E13", "Watkins & Feldman 2025", "arXiv:2512.03168", V, "CF4 bulk flow dominated by sources beyond 200 h^-1 Mpc"),
    ("E14", "Tully et al. 2023 (Cosmicflows-4)", "arXiv:2209.11238", V, "6dFGSv bulk-flow bias toward the south celestial pole and its recalibration"),
    ("E15", "Springob et al. 2014 (6dFGSv)", "arXiv:1409.6161", V, "hemispheric survey: FP zero point degenerate with a polar dipole"),
    ("E16", "Kalbouneh et al. 2026, JCAP 03, 084", "arXiv:2510.02510", V, "CF4 expansion-rate multipoles, axis (l,b) = (295, 5), read as covariant cosmography"),
    ("E17", "Maartens, Santiago, Clarkson, Kalbouneh, Marinoni 2024, JCAP 09, 070", "arXiv:2312.09875", V, "covariant cosmography; boost transformation of Hubble multipoles"),
    ("E18", "Heinesen 2021, JCAP 05, 008", "arXiv:2010.06534", P, "multipole decomposition of the general luminosity-distance Hubble law"),
    ("E19", "Secrest et al. 2025, Rev. Mod. Phys. 97, 041001", "arXiv:2505.23526", V, "cosmic dipole anomaly exceeds 5 sigma in independent radio and quasar samples"),
    ("E20", "von Hausegger et al. 2026, MNRAS 546", "arXiv:2510.23769", V, "CatWISE2020 clustering and its impact on dipole inference"),
    ("E21", "Ferreira & Marra 2024", "arXiv:2403.14580", V, "tomographic redshift dipole: 196 +92 -79 km/s, consistent with the CMB dipole at 2 sigma"),
    ("E22", "Ferreira & Quartin 2021, PRL 127, 101301", "arXiv:2011.08385", V, "aberration+Doppler: v = 300 +111 -93 km/s toward (276 +- 33, 51 +- 19); intrinsic dipole < 3.7 mK (95%)"),
    ("E23", "Mittal, Oayda, Lewis 2024", "arXiv:2311.14938", M, "Quaia dipole consistent with the CMB dipole"),
    ("E24", "Wagenveld, Kloeckner, Schwarz 2023", "arXiv:2305.15335", M, "NVSS+RACS dipole excess (identifier from memory)"),
    ("E25", "Marcori, Pitrou, Uzan, Pereira 2018, PRD 98, 023517", "arXiv:1805.12121", V, "direction and redshift drift for general observers; Bianchi I"),
    ("E26", "Schwartzman, Mascarenhas, Taylor 2008, Ann. Stat. 36, 2886", "arXiv:0901.3290", V, "inference for eigenstructure of Gaussian symmetric matrices"),
    ("E27", "Ganesan & Chingangbam 2017, JCAP 06, 023", "arXiv:1608.07452", V, "tensor Minkowski functionals on the CMB"),
    ("E28", "Samal, Saha, Jain, Ralston 2008, MNRAS 385, 1718", "arXiv:0708.2816", V, "power tensor: matrix-valued statistic per multipole"),
    ("E29", "Sellentin & Heavens 2016", "arXiv:1511.05969", P, "t-type likelihood for simulated covariance"),
    ("E30", "Percival et al. 2022", "arXiv:2108.10402", P, "credible-interval matching with sample covariance"),
    ("E31", "Maartens, Ellis, Stoeger 1995, PRD 51, 1525", "arXiv:astro-ph/9501016", M, "limits on anisotropy and inhomogeneity from CMB multipoles"),
    ("E32", "Planck 2018 results VII (isotropy and statistics)", "arXiv:1906.02552", M, "low-ell polarization of component-separated maps carries residual systematics (identifier from memory)"),
    ("E33", "Boubel, Colless, Said, Staveley-Smith 2024, Testing anisotropic Hubble expansion", "arXiv:2412.14607", V,
     "CF4 Tully-Fisher: H0 dipole equivalent to a 3% variation (2.10 +- 0.53 km/s/Mpc, 3.9 sigma), only weakly favoured over constant H0 plus a LCDM-consistent bulk motion"),
    ("E34", "Salzano et al. 2026, Phys. Dark Univ. 53, 102382", "arXiv:2512.02526", V,
     "dipolar anisotropy of local H0 from CF4 depends on the statistical form of the Hubble relation, on sample consistency and on the velocity treatment"),
    ("E35", "Wang et al. 2026, MNRAS 548", "doi:10.1093/mnras/stag677", P, "CF4 peculiar-velocity correlation function; survey covariance is non-trivial and sampling anisotropic (Loop8 record)"),
    ("E36", "Gorski 1988, ApJ 332, L7", "no arXiv identifier", M, "velocity correlation tensor of a potential flow: Psi_perp, Psi_par (re-derived and tested in R54-EQ-30/31)"),
    ("E37", "Strauss & Willick 1995, Phys. Rep. 261, 271", "arXiv:astro-ph/9502079", M, "Malmquist bias; redshift-space (Method II) versus distance-space inference"),
    ("E38", "Davis et al. 2011, ApJ 741, 67", "arXiv:1012.2912", M, "peculiar velocity changes the observed luminosity distance by (1 + u/c)^2 (used in R54-EQ-33)"),
    ("E39", "Hui & Greene 2006, PRD 73, 123526", "arXiv:astro-ph/0512159", M, "correlated luminosity-distance fluctuations from peculiar velocities"),
    ("E40", "Koda et al. 2014, MNRAS 445, 4267", "arXiv:1312.1022", M, "sinc damping of the velocity power spectrum (damped-body variant)"),
    ("E41", "Watkins & Feldman 2015, MNRAS 450, 1868", "arXiv:1411.6665", M, "log-distance based velocity estimator that avoids the log-normal distance bias"),
    ("E42", "Sorrenti, Durrer, Kunz 2023, JCAP 11, 054", "arXiv:2212.10328", M, "Pantheon+ dipole differing from the CMB dipole in direction"),
    ("E43", "Nusser & Tully 2026, Cosmicflows-4 and the cosmological consistency of large-scale motions", "arXiv:2608.14265", V,
     "log-distance radial-velocity estimator in radial bins on CF4 and its constituent catalogues; TFR and 6dFGS favour larger dipoles than SDSS and SN; removing 6dFGS reduces the upper-bin dipole deviation to 1.56 sigma"),
    ("E44", "How isotropic is dark energy? (Bianchi I with time-dependent anisotropic stress), PRD 2026", "arXiv:2601.22351", V,
     "the temperature quadrupole is a line-of-sight integral of the shear while large-angle polarization is weighted by the visibility function"),
    ("E46", "Basko & Polnarev 1980, MNRAS 191, 207", "doi:10.1093/mnras/191.2.207", V,
     "first-order solution of polarized radiative transfer in a spatially flat homogeneous anisotropic universe; the polarization degree depends strongly on recombination and reheating (prior form of R54-EQ-01 to R54-EQ-04)"),
    ("E47", "Keating, Timbie, Polnarev, Steinberger 1997 preprint, accepted by ApJ (Large Angular Scale Polarization of the CMB and the Feasibility of its Detection)", "arXiv:astro-ph/9710087", V,
     "expected large-angle polarization in several cosmological scenarios; cites E46 (author list corrected against the arXiv record)"),
    ("E48", "Negroponte & Silk 1980, PRL 44, 1433 (authors from memory; journal record and abstract seen)", "doi:10.1103/PhysRevLett.44.1433", M,
     "computed polarization in spatially flat homogeneous anisotropic universes; sensitive to the ionization history"),
    ("E49", "Dolgov 2002, Neutrinos in cosmology (Phys. Rep.)", "arXiv:hep-ph/0202122", V,
     "rate-versus-expansion estimate of the decoupling temperatures: 1.87 MeV for electron neutrinos and 3.12 MeV for muon and tau neutrinos"),
]
EVIDENCE_ROWS = [dict(zip(("id", "source", "identifier", "verification", "claim_used"), e)) for e in EVIDENCE]


def _apply_l07_evidence(rows: list[dict]) -> list[dict]:
    """R54-L07 step 3: rows verified from the primary source become VERIFIED; the others keep their status and gain the check note."""
    path = RES / "R54_L07_BENCHMARK.json"
    if not path.is_file():
        return rows
    checks = json.loads(path.read_text(encoding="utf-8")).get("evidence_verification", {})
    out = []
    for r in rows:
        c = checks.get(r["id"])
        if c is None:
            out.append(r)
        elif c["status"] == "VERIFIED":
            out.append({**r, "verification": V, "claim_used": r["claim_used"] + f" [R54-L07: {c['note']}]"})
        else:
            out.append({**r, "claim_used": r["claim_used"] + f" [R54-L07 {c['status']}: {c['note']}]"})
    return out


EVIDENCE_ROWS = _apply_l07_evidence(EVIDENCE_ROWS)


def sweep_text(n: dict) -> str:
    if n["sweep_flips"]:
        return (f"Sigma_T per unit initial shear changes sign between an assumed free-streaming onset at z_i = {g3(n['sweep_z_pre'])} (T_nu = {n['sweep_T_pre']:.1f} MeV) "
                f"and {g3(n['sweep_z_flip'])} ({n['sweep_T_flip']:.1f} MeV), an interval that contains the decoupling estimate of 3.12 MeV for muon and tau neutrinos (E49; 1.87 MeV for electron neutrinos) "
                f"(r_E from {n['rE_lo']:.3f} to {n['rE_hi']:.3f} before the sign change, {n['rE_all_lo']:.3f} to {n['rE_all_hi']:.3f} over all {n['sweep_n']} points)")
    return f"r_E spans [{n['rE_all_lo']:.3f}, {n['rE_all_hi']:.3f}] over the {n['sweep_n']} sweep points without a sign change of Sigma_T"


def tails_text(n: dict) -> str:
    return f"pooled {g3(n['g_tail_sky'])}, method monopoles {g3(n['m_tail_sky'])}, method x hemisphere steps {g3(n['s_tail_sky'])}"


def hypotheses(n: dict) -> list[dict]:
    """Cloud hypotheses with the executed local results appended; a decision changes only where a node's decision check says so."""
    hyps = hypotheses_cloud(n)
    by = {h["id"]: h for h in hyps}

    def add(hid: str, result: str, nxt: str | None = None, decision: str | None = None) -> None:
        by[hid]["executed_result"] += "; " + result
        if nxt is not None:
            by[hid]["next_action"] = nxt
        if decision is not None:
            by[hid]["decision"] = decision

    if "l01_edev" in n:
        add("H-L1a", f"R54-L01: masked E response e_dev = {g3(n['l01_edev'])} ({n['l01_eflag']})", "R54-L07 literature check (B09)")
        add("H-L1c", f"R54-L01 empirical LOO B ell=2 tail {g3(n['l01_B_p'])} (SMICA), {g3(n['l01_B_p_comm'])} (Commander); E lane {n['l01_E_status']}",
            "R54-L02 cross-experiment E lane")
    if "l03_repro" in n:
        add("H-L2a", f"R54-L03 calibrated excess tails {g3(n['l03_p_q'])} (Quaia), {g3(n['l03_p_n'])} (NVSS); {n['l03_excess_decision']}",
            "R54-L06 tilt closure with the R54-L03 count covariance")
    if "l02_e_status" in n:
        add("H-L1c", f"R54-L02 adopted-covariance B ell=2 null passes in: {n['l02_families']}; E lane {n['l02_e_status']}", "R54-L06 (T lane; E lane as recorded)")
    l07 = local_result("R54-L07")
    if l07 is not None:
        for hid, chk in l07["novelty_checks"].items():
            by[hid]["dimensions"]["novelty"] = chk["novelty"] + "; nearest prior art: " + "; ".join(chk["nearest_prior_art"])
    for hid, d in local_hypothesis_decisions().items():
        add(hid, d["result"], d["next"], d["decision"])
    return hyps


def local_hypothesis_decisions() -> dict:
    """Decisions fixed by the decision checks of executed local nodes (R54-L04 onwards)."""
    out = {}
    x = local_result("R54-L04")
    if x is not None and x.get("status") == "DONE_SCOPED_C0":
        dec = x["decision"]
        for hid, d in dec["hypotheses"].items():
            out[hid] = {"decision": d, "result": f"R54-L04 decision check: {d} (step class {dec['step_class']}; robust class {dec['robust_class']})",
                        "next": "R54-L06 joint tomography" if d == "HOLD" else "none (rejected by the R54-L04 decision check)"}
    return out


def hypotheses_cloud(n: dict) -> list[dict]:
    def h(i, lane, text, decision, ev, val, nov, tst, rob, risk, kill, result, nxt):
        return {"id": i, "lane": lane, "statement": text, "decision": decision,
                "dimensions": {"evidence": ev, "validity": val, "novelty": nov, "testability": tst, "robustness": rob, "risk": risk},
                "kill_criterion": kill, "executed_result": result, "next_action": nxt}

    def pc(key: str) -> str:
        return f"{100 * n[key]:.0f}%"
    return [
        h("H-C1", "CORE", "The five views are a reporting convention on one precision-form carrier: Q and F are polar duals (R54-EQ-21) and no view adds information to the likelihood.",
          "PROMOTE", "module + unit tests", "exact convex duality; 2-D enumeration to 1e-8", "NONE claimed (standard convex analysis)",
          "HIGH", "exact", "presenting a reporting layer as a statistic", "a view that changes a GLS estimate",
          "tests/r54 pass; ties GLS by construction (R53 theorem retained); the F view is UNAVAILABLE on both low-redshift lanes because an axis scan is not a support functional",
          "use as the reporting layer of every lane; no novelty claim"),
        h("H-C2", "CORE", "A tensorized carrier gains statistical power over the exact likelihood.", "REJECT", "R53 benchmark", "contradicted by sufficiency",
          "none", "done", "n/a", "false-gain claim", "n/a", "R53: Fisher-distance ratio 1.0000, coverage tie", "never claim gain; claim typed interpretation only"),
        h("H-C3", "CORE", "Irreducible-carrier transport with the full cross-depth covariance tells a 1/d (velocity) law from a constant (zero-point or acceleration) law on the real CF4 footprint.",
          n["h_c3_decision"], "injections on the real footprint with exact-body noise, pooled and method-monopole operators", "exact GLS; synthetic recovery test",
          "LOW, pending R54-L07", "HIGH",
          f"constant law preferred for an injected step / an injected flow: {pc('inj_step_A')} / {pc('inj_flow_A')} at {n['inj_step_mag']:.2f} mag and {n['inj_flow']:.0f} km/s; "
          f"{pc('inj_obs_step_A')} / {pc('inj_obs_flow_A')} at the observed sizes ({n['inj_obs_step_mag']:.3f} mag, {n['inj_obs_flow']:.0f} km/s); "
          f"method-monopole operator at the observed sizes {pc('injm_obs_step_A')} / {pc('injm_obs_flow_A')}",
          "the observed-size amplitudes are data-derived; on data the outcome depends on inter-method zero points",
          "at the observed sizes the constant law is preferred in fewer than 90% of step draws or more than 10% of flow draws on either operator (rule written before the observed-size run was read; not committed beforehand)",
          f"pooled chi2(A)={g3(n['g_chi2_A'])}/9 vs chi2(V)={g3(n['g_chi2_V'])}/9; after method monopoles {g3(n['m_chi2_A'])} vs {g3(n['m_chi2_V'])}", "R54-L04"),
        h("H-L1a", "L1", "Re-derivation: the T and E quadrupoles measure two ionization-fixed linear functionals of the shear history, Sigma_T = int K_T s dN and Sigma_E = int K_E s dN, with closed-form kernels (R54-EQ-03).",
          "PROMOTE", "derivation + SymPy seal + ODE agreement inside the unit-test tolerance", "first order, k = 0, type I",
          "NONE claimed: the first-order polarized transfer in a flat anisotropic universe was solved in E46 (see also E48, E47); E03 and E44 separate the line-of-sight temperature integral from the visibility-weighted polarization source",
          "HIGH", "kernel exact; history-model free", "none at this order", "an order-unity term missing from the k = 0 Thomson system",
          f"r_E(perfect fluid)={n['r_E_pf']:.4f}; reionization share {100*n['reion_share']:.0f}%", "R54-L01 masked E response"),
        h("H-L1b", "L1", "The conversion of (Sigma_T, Sigma_E) to a present-day shear is not robust: it depends on the radiation anisotropic-stress history, on the neutrino masses and on the initial state, so a perfect-fluid bound cannot be quoted without its model label.",
          "PROMOTE", "ODE with photon and neutrino stress (massless and minimal normal ordering with the exact collisionless stress weight R54-EQ-06); analytic radiation-era oscillator test",
          "linear; the statement is qualitative and every number is an illustration",
          "LOW, partly checked: E05 shows that free-streaming neutrinos invalidate CMB temperature limits in the magnetic Bianchi I case and E06, E07 give the modified shear decay under collisionless stresses; full check in R54-L07",
          "HIGH",
          f"s0/Sigma_T changes sign with photon stress ({g3(n['s0_photon'])}); (c_T, c_E) = ({g3(n['c_T'])}, {g3(n['c_E'])}) massless and ({g3(n['c_T_m'])}, {g3(n['c_E_m'])}) for minimal normal ordering; {sweep_text(n)}",
          "quoting an illustration number as a limit", "a prior paper that already gives stress-corrected Bianchi-I shear limits from CMB T+E",
          f"95% illustration values of |s0|: {g3(n['s0_pf_TE'])} (perfect fluid, T+E), {g3(n['s0_as'])} (massless two-mode family), {g3(n['s0_as_no'])} (minimal normal ordering)",
          "R54-L07 literature check"),
        h("H-L1c", "L1", "PR3 component-separated ell = 2 polarization can be used at face value.", "REJECT",
          "B-null gate on committed carrier", "Hotelling law with N = 300", "n/a", "done", "holds for SMICA and Commander",
          "E-lane overclaim", "n/a", f"B ell=2 tail p={g3(n['B_p'])} (SMICA), {g3(n['B_p_comm'])} (Commander); observed rms {n['B_rms_obs']:.2f} vs FFP10 {n['B_rms_ffp']:.2f} uK", "E lane stays DIAGNOSTIC until R54-L01/L02"),
        h("H-L1d", "L1", "Octupole or higher morphology constrains type-I parameters.", "REJECT", "first-order response is pure ell = 2", "exact at first order",
          "n/a", "done", "exact", "none", "n/a", "ell >= 3 modes enter only through covariance", "family comparison beyond type I remains blocked on a source-bound transfer"),
        h("H-L2a", "L2", "The owned count dipoles (Quaia G<20, NVSS; receipt estimator) exceed the kinematic expectation.", "HOLD",
          "committed receipt", "per-axis sd includes mask and declination systematics; no clustering body", "n/a", "LOW with this estimator",
          f"power against a dipole twice the kinematic one: {n['count_power']:.2f} at the 5% level", "reading a non-detection as evidence against the published anomaly",
          "the calibrated estimators of R54-L03, with power of at least 0.8 against the published excess, give p >= 0.01",
          f"excess tails p={n['quaia_p']:.2f} (Quaia), {n['nvss_p']:.2f} (NVSS); common excess p={n['common_p']:.2f}; no decision at this power", "R54-L03: clustering body, same-estimator null, competitor estimators"),
        h("H-L2b", "L2", "A linear clustering dipole body (R54-EQ-32) and a same-estimator velocity null change the significance of count-dipole excesses on the owned catalogues.", "HOLD",
          "not executed in the cloud session (needs catalogue N(z), selection maps and bias models)", "linear theory; bias from cited primary sources only", "LOW (E20 addresses clustering for CatWISE2020)",
          "HIGH", "bracketed by two N(z) and two bias models", "bias taken from memory", "the body is below 10% of the shot term for every owned catalogue and cut",
          "no number yet", "R54-L03"),
        h("H-L2c", "L2", "The R52 counts-versus-CF4 frame inconsistency is a statement about cosmic frames.", "REOPEN",
          "R52 result + R54-L05 exact CF4 carrier", "R52 used the biased linear CF4 estimator without a cosmic body", "n/a", "HIGH",
          "count side has no clustering body yet", "mis-attribution", "the closure test rejects at p < 0.01 once the count side is calibrated",
          f"tilt closure V_CF4 + c beta_excess = 0: p={g3(n['tt_close_p'])} (V only), {g3(n['tt_close_p_A'])} (constant dipole marginalised); count side preliminary", "R54-L03, R54-L06"),
        h("H-L3a", "L3", "Vorticity is not identified by any owned first-order observable; identification needs a dynamical-versus-kinematic frame tie or a family-specific transfer.",
          "PROMOTE", "inherited from R52 (rank 14/17; parity and frame-definition argument); no new R54 computation", "first order; structural", "NONE claimed (inherited identifiability statement)", "MEDIUM", "structural", "none",
          "an owned observable with a non-degenerate axial-vector column", "no column added in R54", "state as an identifiability result"),
        h("H-L3b", "L3", "A constant fractional-H dipole is a gauge direction of a single distance-indicator sample (it equals a zero-point dipole).",
          "PROMOTE", "inherited R52 column identity; E09 states the same degeneracy", "exact for one sample; several indicators only test for a common mode", "NONE claimed (inherited; stated in E09)", "HIGH",
          "structural", "none", "n/a",
          f"per-family hemisphere steps are mutually consistent (p={g3(n['st_cons_p'])}), as are the per-method dipoles (p={g3(n['cm_cons_p'])}); the common dipole itself has Wald p={g3(n['cm_wald_p'])}", "R54-L04, R54-L06"),
        h("H-L3c", "L3", "Any type-I shear compatible with the CMB functionals is far below low-redshift sensitivity, so low-z STF2 signals are local or systematic within type I.",
          "REJECT", "late-time sensitivity of the two kernels (RESULTS/R54_L1_TYPE1_TE.json:data.late_time_shear_bounds)",
          "counterexample inside type I: late-time anisotropic stress with a sign-changing shear (E44)", "n/a", "done", "n/a", "a family restriction read as a general statement", "n/a",
          f"for a shear confined to z < 0.2 the T functional bounds a constant-sign history at {g3(n['late_T_const'])} and is blind to a sign-changing one; the E functional bounds its rms at {g3(n['late_E_rms'])} "
          f"(diagnostic lane; {g3(n['late_E_rms_floor'])} with the B-null floor), above the CF4 quadrupole of {n['g_quad_pct']:.1f}% of H", "replaced by H-L3d"),
        h("H-L3d", "L3", "Without late-time anisotropic stress (perfect fluid or radiation-sourced stress histories) the type-I present shear allowed by the CMB functionals is orders of magnitude below low-redshift sensitivity; with late-time stress no such statement holds.",
          "PROMOTE", "three computed stress histories + late-time kernel sensitivity", "type I; the three computed histories are not a class theorem; the E lane is diagnostic",
          "LOW (E44 treats late-time anisotropic stress in Bianchi I)", "HIGH",
          f"|s0| <= {g3(n['s0_as'])} (massless two-mode) and {g3(n['s0_as_no'])} (minimal normal ordering) against a CF4 quadrupole of {n['g_quad_pct']:.1f}% of H", "dropping the condition",
          "a radiation-sourced history whose present shear reaches the percent level under the measured functionals",
          f"late-time rms bound from E: {g3(n['late_E_rms'])} (z < 0.2), {g3(n['late_E_rms_z05'])} (z < 0.5), {g3(n['late_E_rms_z2'])} (z < 2)", "R54-L06 quotes the condition with every use"),
        h("H-L4a", "L4", "Classification at carrier level is the orbit type of the measured tensor (isotropic, axisymmetric, triaxial) by STF invariants; Bianchi-family identification stays blocked without a transfer atlas.",
          "HOLD", "stf2_invariants and the axisymmetry statistic (unit tests only)", "exact invariants; no null calibration of the invariants on an owned carrier", "LOW (E26 gives the statistical theory)",
          "MEDIUM", "eigen-axes of a marginal tensor are unstable (the axis moves under the zero-point split)", "family overclaim",
          "the calibrated invariants cannot tell axisymmetric from triaxial at the measured noise",
          f"CF4 constant quadrupole {n['g_quad_pct']:.1f}% of H, principal axis {n['g_quad_axis']:.1f} deg from the equatorial pole (log estimator, exact body); family identification blocked", "R54-L04, R54-L06"),
        h("H-L5a", "L5", "Conditional on linear theory without a selection model or a calibration covariance, the pooled CF4 window multipoles exceed the LCDM body.", "HOLD",
          "catalogue-level log-distance estimator + exact pair-sum body over 35970 groups", "linear theory, redshift-space positions, no selection model, no calibration covariance",
          "LOW, pending R54-L07 (published bulk-flow tension E10-E13; E35 computes the CF4 velocity correlation; E43 uses the same estimator class)", "HIGH",
          f"joint null p: pooled {g3(n['g_joint_p'])}, method monopoles {g3(n['m_joint_p'])}, method x hemisphere steps {g3(n['s_joint_p'])}; damped body {g3(n['g_joint_p_damped'])}; body x2 {g3(n['g_joint_p_x2'])}",
          "the excess is strongest in the two outer windows, where the sample is northern FP",
          "survey-resolved zero points, a radial slope or a distance-error term bring the joint null above 0.01 (R54-L04)",
          f"inner windows joint p={g3(n['wi_joint_p'])} (dipole {g3(n['wi_dip_p'])}), outer windows joint p={g3(n['wo_joint_p'])} (dipole {g3(n['wo_dip_p'])}); "
          f"FP is {pc('outer_FP_frac')} of the groups at z >= 0.055 and {pc('outer_FP_north_frac')} of that FP sample is northern", "R54-L04"),
        h("H-L5f", "L5", "The R36/H03 linear-in-distance estimator carries a deterministic same-estimator bias (errors in variables plus the cosmographic trend) that mimics survey-locked multipoles.",
          "PROMOTE", "same-estimator mock with the operator rebuilt per draw; analytic exp(+s^2/2) check in the unit test", "exact for Gaussian distance-modulus errors",
          "LOW (the log-normal distance bias is known, E41; E43 uses a log-distance estimator on CF4); new for this project's R36, H03 and R52 products", "done",
          f"bias carries {100*n['eiv_frac_lo']:.0f}-{100*n['eiv_frac_hi']:.0f}% of the pole dipole; quadrupole null p {g3(n['xl_quad_p'])} -> {g3(n['xb_quad_p'])}; sky fraction {g3(n['xl_sky_frac'])} -> {g3(n['xb_sky_frac'])}",
          "none", "n/a", "R36 operator reproduced from the committed source rows; log estimator unbiased in the unit test",
          "use R54-EQ-34 everywhere; CF4 numbers of R36, H03 and R52 are superseded"),
        h("H-L5g", "L5", "The CF4 dipole excess is a hemisphere step of equal size in all four indicator families (a common mode rather than a single-survey calibration term).", "HOLD",
          "per-method hemisphere steps with the exact cross-covariance; hemisphere-split axis scan with the exact body", "linear body; hemisphere is a proxy for survey labels; the sign(dec) axis was chosen after the first pass",
          "LOW, pending R54-L07: E43 fits per-catalogue dipoles with a log-distance estimator and finds larger dipoles for TFR and 6dFGS than for SDSS and SN; E09 and E33 find the TF dipole compatible with LCDM flows; specific here is the exact cross-covariance between families",
          "HIGH",
          f"consistency p={g3(n['st_cons_p'])}; single-axis tail {g3(n['st_common_p'])}; tail of the scan maximum over {n['sc_n_axes']} split axes {g3(n['sc_tail_scan'])}; the pole ranks {n['sc_pole_rank']} of {n['sc_n_axes']}; jackknife pole dipole {100*n['jk_lo']:.1f}% to {100*n['jk_hi']:.1f}%",
          f"equal steps can have different causes (a 6dFGS versus SDSS zero point inside FP, local flows in the shallow TF and SN samples); the four estimates share the body (variance of the best single family / variance of the common step = {n['sc_var_ratio']:.2f}); "
          "the step (z < 0.055) and the window excess (outer windows) are different measurements",
          "survey-resolved zero points absorb the step (R54-L04)",
          f"common step {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}% of H; common-dipole Wald p={g3(n['cm_wald_p'])}", "R54-L04"),
        h("H-L5c", "L5", "The CF4 dipole-plus-quadrupole pattern is locked to the equatorial pole.", "HOLD",
          "exact body, unbiased estimator, null law drawn from the exact body under three zero-point nuisance models", "same grid statistic for data and null draws; the answer depends on the nuisance model",
          "n/a", "MEDIUM", f"calibrated sky-fraction tail: {tails_text(n)}",
          f"the pole_locked flag fires in {pc('inj_obs_step_lock')} of draws for an injected hemisphere step of the observed size ({pc('inj_none_lock')} without injection), so a tail above 0.01 does not exclude locking",
          "survey-resolved zero points (R54-L04) put the tail on one side of 0.01 for every nuisance model",
          f"first pass (ideal-sky body, linear estimator): {n['lock_angle']:.1f} deg, sky fraction {n['lock_frac']:.4f}; after the estimator bias is subtracted the sky fraction is {g3(n['xb_sky_frac'])}; "
          f"class by nuisance model: {n['x_class']} / {n['x_class_mono']} / {n['x_class_split']}", "R54-L04"),
        h("H-L5h", "L5", "A depth-independent fractional quadrupole remains after the method/hemisphere split.", "HOLD",
          "constant-tensor fit of the four windows", "a posteriori statistic; selection and footprint systematics are not modelled", "n/a", "HIGH",
          f"Wald p={g3(n['g_quad_wald_p'])} pooled and {g3(n['s_quad_wald_p'])} after the split, but the 20-dof null has p={g3(n['g_quad_p'])}",
          "reading a footprint systematic as shear", "survey-resolved monopoles remove it (R54-L04)", f"{n['g_quad_pct']:.1f}% of H", "R54-L04"),
        h("H-L5e", "L5", "A physical direction-dependent Hubble factor is detected in CF4.", "REJECT",
          "structural degeneracy (H-L3b) and the dependence of the excess on the zero-point nuisance model", "a constant dipole is a gauge direction of distance-indicator data", "n/a", "done", "n/a", "detection-claim wording", "n/a",
          f"joint null p from {g3(n['g_joint_p'])} (pooled) to {g3(n['s_joint_p'])} (method x hemisphere steps marginalised); class {n['x_class_robust']}", "do not claim"),
        h("H-L6a", "L6", "Depth laws separate an observer boost or bulk flow (1/d), a zero-point or acceleration term (constant) and the LCDM stochastic body.",
          "HOLD", "CF4 execution with the exact body", "linear", "LOW", "HIGH", "not robust to inter-method zero points", "none",
          "survey-resolved zero points leave no preference (R54-L04)",
          f"delta chi2 (V - A) = {g3(n['g_chi2_V']-n['g_chi2_A'])} pooled, {g3(n['m_chi2_V']-n['m_chi2_A'])} after method monopoles", "R54-L04, R54-L06"),
        h("H-L6b", "L6", "A single global tilt explains both the CF4 flow and a count-dipole excess.", "HOLD",
          "R52 + R54-L05 closure test", "linear; the count side is the receipt estimator", "n/a", "LOW until R54-L03",
          f"count-side power against a doubled dipole is {n['count_power']:.2f}", "rejecting on an underpowered count side",
          "the closure test rejects at p < 0.01 once the count side is calibrated (R54-L03)",
          f"velocity term after the constant term: Wald {g3(n['g_V_after_A'])}/3; closure p={g3(n['tt_close_p'])} / {g3(n['tt_close_p_A'])} (preliminary)", "R54-L03, R54-L06"),
        h("H-L6c", "L6", "Map-level aberration and Doppler-modulation estimators on owned CMB maps separate the observer boost from an intrinsic dipole inside this programme.", "HOLD",
          "published result E22 only", "requires a high-ell estimator with simulated mode-coupling corrections that is not part of the owned products", "none (E22 did it)", "LOW inside the stop rule",
          "n/a", "scope growth", "n/a", "not executed; E21 and E22 enter R54-L06 as published anchors with their covariance", "no new estimator; anchors only"),
    ]

EQUATIONS = {
    "R54-EQ-01": "dTheta/dN = -s - kappa[(9/10)Theta + (sqrt6/10)Ecal]",
    "R54-EQ-02": "dEcal/dN = -kappa[(sqrt6/10)Theta + (4/10)Ecal]; kappa = n_e sigma_T c/H = dtau/dln(1+z)",
    "R54-EQ-03": "K_T(tau) = (6 e^-tau + e^(-3tau/10))/7 ; K_E(tau) = (sqrt6/7)(e^(-3tau/10) - e^-tau)",
    "R54-EQ-04": "Sigma_T = -Theta(0) = int K_T(tau(N)) s(N) dN ; Sigma_E = +Ecal(0) = int K_E(tau(N)) s(N) dN ; a^T_2m <-> -T0 n.Sigma_T.n ; a^E_2m <-> -T0 n.Sigma_E.n",
    "R54-EQ-05": "ds/dN = -(3 + dlnH/dN) s + (8/5)[Omega_gamma(N) Theta + Omega_nu(N) Ncal] ; dNcal/dN = -s",
    "R54-EQ-06": "massive collisionless species, k = 0, first order: pi_ij = -(2/15) beta_ij Kcal, beta_ij = int s_ij dN, Kcal = 4 pi int dp f0 p^4 (4p^2 + 5m^2)/E^3 ; W(mu) = Kcal/(4 rho_massless), mu = m a/T_nu0, W(0) = 1 ; the neutrino term of R54-EQ-05 is multiplied by the species mean of W",
    "R54-EQ-10": "u_lm(r) = 4 pi f H0 i^l int d^3k/(2pi)^3 (delta_k/k) j_l'(kr) Y*_lm(k)",
    "R54-EQ-11": "C_l^{ww'} = (2/pi)(f H0)^2 int dk P(k) I_l^w(k) I_l^{w'}(k) ; I_l^w(k) = int dr Wcal_w(r) j_l'(kr)",
    "R54-EQ-12": "Var(H) = C_0/(4pi) ; Cov(D_i) = (3/(4pi)) C_1 ; Cov(q_a) = (15/(8pi)) C_2",
    "R54-EQ-20": "Theta_c = {theta: (theta-m)^T F (theta-m) <= c^2}, F m = t ; Q_min/max = min/max of p_K0 over Theta_c ; Q_max = inf if F singular",
    "R54-EQ-21": "Q_min = sup_v [-h_Theta(-v)]_+/h_K0(v) ; Q_max = sup_v h_Theta(v)/h_K0(v) ; h_K0(v) = sqrt(v^T B v)",
    "R54-EQ-22": "Pi = P[stat >= stat_obs | named law]",
    "R54-EQ-23": "chi2_transport = min_x (y - (tau (x) I)x)^T C^-1 (y - (tau (x) I)x), dof = d(K-1)",
    "R54-EQ-30": "Psi_perp(r) = (f H0)^2/(2 pi^2) int dk P(k) j_1(kr)/(kr) ; Psi_par(r) = (f H0)^2/(2 pi^2) int dk P(k) [j_0(kr) - 2 j_1(kr)/(kr)]",
    "R54-EQ-31": "C_uu(i,j) = Psi_perp(r_ij)(n_i.n_j) + [Psi_par(r_ij) - Psi_perp(r_ij)](n_i.rhat_ij)(n_j.rhat_ij) ; r_ij = |d_i n_i - d_j n_j|",
    "R54-EQ-32": "C_1 = (2/pi) int dk k^2 P(k) [int dchi W(chi) b(z) D(z) j_1(k chi)]^2 ; Var(d_i) = (3/(4pi)) C_1 for delta(n) = d.n",
    "R54-EQ-33": "flat LCDM: chi_hat(z) = int_0^z dz'/E ; y(z) = c (1+z) chi_hat = H0 d_L(z) [km/s] ; g(z) = [(1+z)/(E chi_hat) - 1]/c = d ln(y/d_L,obs)/du",
    "R54-EQ-34": "eta_i = ln[y(z_i)/d_i] = h + delta.n_i + n_i.kappa.n_i + g(z_i) u_i - s_i eps_i ; s_i = (ln10/5) e_mu,i ; weights W(z_i)/tau_i^2, tau_i^2 = s_i^2 + (sigma_* g_i)^2",
    "R54-EQ-35": "R36 linear estimator: c z_i = d_i (H + D.n_i + n_i.q.n_i), weights W(z_i)/hypot(250, 70 (ln10/5) d_i e_mu,i)^2 ; biased by errors in d_i (exp(+s^2/2) for homogeneous errors)",
    "R54-EQ-36": "Delta mu = -(5/ln10) Delta eta ; hemisphere step s: Delta mu(north - south) = -(5/ln10) 2 s",
    "R54-EQ-37": "exact body of an operator O acting on eta: O diag(g) C_uu diag(g) O^T with C_uu of R54-EQ-31 at redshift-space positions r_i = (c/H_fid) chi_hat(z_i)",
    "R54-EQ-38": "global-tilt closure across depths: V_CF4 + c beta_excess(counts) = 0 with beta_excess = D/c_EB - beta_CMB",
}

CONVENTIONS = {
    "metric_signature": "(-,+,+,+)",
    "sky_direction": "n = unit vector from observer to source; photon propagation direction is -n",
    "time_variable": "N = ln a, a = 1 today; s = sigma/H is dimensionless",
    "stf5_basis": f"{MOD}/r54_tensor_five_view.py::STF5_BASIS, order [(xx-yy)/sqrt2, (xx+yy-2zz)/sqrt6, xy, xz, yz], Frobenius norm 1 each",
    "cmb_vector": "135 = T45 | E45 | B45; ell = 2..6 inside each field; labels in observed_carrier.npz:mode_labels; index of T_2_0 is 0, E_2_0 is 45, B_2_0 is 90",
    "cmb_sign": "dT/T(n) = -n.Sigma_T.n ; healpy E coefficients carry -T0 n.Sigma_E.n with the same packing as T (R54-EQ-04)",
    "cf4_vector": "36 = 4 windows x [H, D_x, D_y, D_z, STF5]; km/s/Mpc; ICRS J2000; redshift z_CMB; windows z = 0.025, 0.04, 0.06, 0.08 (R36 linear estimator; superseded for inference by cf4_log_vector)",
    "cf4_log_vector": "36 = 4 windows x [h, delta_x, delta_y, delta_z, kappa_1..5]; h = ln H; delta and kappa are fractions of the apparent Hubble rate; stored with its white and exact-body covariance in RESULTS/R54_L05_CF4_EXACT.json:log_distance.carrier",
    "cf4_sign": "delta points toward higher apparent Hubble rate; Delta mu = -(5/ln10) delta.n; hemisphere step s > 0 means a higher rate in the north",
    "cf4_catalogue": "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz: z_CMB, dmzp, e_dmzp, n_J2000 (N,3), method_family in {FP, OTHER, SN, TF}, group_id; N = 35970; 0.01 <= z <= 0.1",
    "units": {"cmb_modes": "uK_CMB", "Sigma": "dimensionless", "apparent_H": "km/s/Mpc", "velocity": "km/s", "distance": "Mpc (no h)",
              "k": "1/Mpc", "P": "Mpc^3", "count_dipole": "dimensionless amplitude of delta(n) = d.n"},
    "rotation": "x_gal = R_I2G @ x_icrs with R_I2G defined once in scripts/r54/run_r54_lowz_frames.py; never retype the matrix",
    "precision_form": "-2 ln L = theta^T F theta - 2 t^T theta + const; a singular F is reported, never regularized; no unstated prior",
    "confidence_level": 0.95,
    "seed": 20261116,
    "json": "UTF-8, indent=1, sort_keys=True; +-inf as strings 'inf'/'-inf'; NaN as null",
    "provenance_keys": ["script", "script_sha256", "inputs_sha256", "python", "numpy", "scipy"],
    "status_vocabulary": ["DONE_SCOPED_C0", "PENDING_LOCAL", "BLOCKED_MISSING_INPUT", "FAILED_ACCEPTANCE", "SKIPPED_OPTIONAL"],
    "claim_tier": "C0 for every R54/R55/R56 output; promotion only through PR-R57 with an independent decision-gate reviewer",
    "forbidden_phrases_in_reports": ["we detect", "evidence for anisotropy", "rules out FLRW", "discovery", "confirms the dipole anomaly"],
    "data_policy": "no downloads; inputs are resolved from HTT_SIX_LOOP_INTEGRATED_20261109/DATA_INVENTORY.json; a missing input sets BLOCKED_MISSING_INPUT",
    "paths": {"local_root": LOCAL, "raw_root": LOCAL + "/raw", "r54_dir": REL, "results_dir": REL + "/RESULTS", "modules": MOD, "tests": "tests/r54"},
}


def local_nodes(n: dict) -> list[dict]:
    return [
        {"id": "R54-L01", "card": "PR-R55-LOCAL-CALIBRATION", "title": "Calibrate the T+E type-I estimator on the 300 FFP10 realisations", "depends": ["R54-L1"], "priority": 1,
         "inputs": [
             {"path": LOCAL + "/r49_chains/ffp10_300_debiased_135.npz", "role": "300 FFP10 SMICA debiased 135-vectors",
              "identity_check": "sample covariance (ddof=1) equals observed_carrier.npz:S_ffp10_300_135x135_uK2 to rtol 1e-10; reuse the loader of scripts/r53/run_r53_benchmark.py, do not guess key names"},
             {"path": "maps and mask exactly as read by scripts/r51/run_r51_pr3_lowell.py", "role": "masked estimator for the E response"},
             {"path": LOCAL + "/raw/planck_pr3_smica_hm", "role": "half-mission SMICA maps (optional leg)"},
             {"path": LOCAL + "/raw/planck_pr3_component_maps*", "role": "Commander / NILC / SEVEM maps (optional leg)"}],
         "steps": [
             "1. Load the cache; assert shape (300,135) and the covariance identity. On failure stop with BLOCKED_MISSING_INPUT.",
             "2. Masked E response. For k = 0..4 build a_lm with a^E_2m equal to the ideal T pattern of STF basis k (invert the real packing used for response_J_ideal_135x5_uK[0:5,k]), a^T = a^B = 0; synthesize Q,U at the NSIDE and beam of the R51 script; run the same masked debiased estimator; stack J_E (135x5).",
             "3. Compute e_dev = max|J_E[45:50] - J_ideal[0:5]| / max|J_ideal[0:5]| and the norms of J_E in T and B rows. If e_dev < 2e-3 keep the ideal response, else use J_E and set flag E_RESPONSE_MASKED_USED.",
             "4. Leave-one-out calibration on carrier TE_l2 (rows 0:5 and 45:50). For i in 0..299: S_i = covariance of the other 299; theta_i = (J^T S_i^-1 J)^-1 J^T S_i^-1 sims[i]; W_i = theta_i^T (J^T S_i^-1 J) theta_i. Record sd(theta_i)/mean plug-in sd per parameter, coverage of plug-in sd x finite_mc_sd_inflation(299,10,10) at 68% and 95%, and the empirical tails of the observed W_all, W_T, W_E.",
             "5. B-null with an empirical law: T2_B(ell=2) of every LOO realisation against S_i; empirical tail of the observed value.",
             "6. Optional legs (skip with SKIPPED_OPTIONAL if inputs are absent): half-mission difference vector (HM1-HM2)/2 and its E2/B2 rms; Commander/NILC/SEVEM E2/B2 dispersion.",
             "7. Re-run scripts/r54/run_r54_cmb_type1.py logic with the calibrated law (add a CLI flag --sims PATH; default behaviour unchanged) and write RESULTS/R54_L01_RESULT.json."],
         "outputs": [{"path": REL + "/RESULTS/R54_L01_RESULT.json", "schema": "htt.r54.l01_te_calibration/1",
                      "required_keys": ["e_response", "loo_calibration", "b_null_empirical", "results_calibrated", "provenance"]}],
         "acceptance": [
             {"metric": "covariance_identity_rel", "op": "<=", "value": 1e-10},
             {"metric": "t_only_pi_loo", "op": "within", "value": [n["pi_loo"] - 0.004, n["pi_loo"] + 0.004]}],
         "decision_checks": [
             {"check": "LOO coverage of the nominal 95% interval lies in [0.912, 0.988] and of the 68% interval in [0.60, 0.76] (binomial 3 sigma, N = 300)",
              "if_true": "the T+E intervals of R54-L1 are CALIBRATED",
              "if_false": "replace the analytic inflation by the empirical LOO quantiles and mark the R54-L1 intervals SUPERSEDED; the carrier is not changed"},
             {"check": "e_dev < 2e-3", "if_true": "keep the ideal E response",
              "if_false": "use the masked response J_E; if e_dev >= 0.05 mark every E-lane number of R54-L1 INVALID"},
             {"check": "empirical B ell=2 null tail >= 0.01", "if_true": "the E lane may become CLAIMABLE subject to R54-L02", "if_false": "the E lane stays DIAGNOSTIC"}],
         "kill": ["tuning the carrier or a threshold after seeing the coverage", "using sims[i] inside its own covariance"],
         "mutation_gates": ["MG-L01", "MG-L02"], "runtime_budget": "30 min CPU"},
        {"id": "R54-L02", "card": "PR-R55-LOCAL-CALIBRATION", "title": "PR4 bypass: covariance triangulation without NPIPE simulations", "depends": ["R54-L01"], "priority": 2,
         "inputs": [{"path": LOCAL + "/raw/wmap_9yr", "role": "WMAP9 maps"}, {"path": LOCAL + "/raw/cosmoglobe_dr1", "role": "Cosmoglobe DR1"},
                    {"path": LOCAL + "/raw/beyondplanck_v2", "role": "BeyondPlanck v2"}, {"path": LOCAL + "/raw/planck_npipe_pr4", "role": "PR4 maps (no simulations held)"}],
         "steps": [
             "1. T-lane analytic covariance. Push unit harmonic maps a_lm (ell = 2..ell_cut of the R51 working resolution) through the R51 estimator to get R (45 x n_modes); C_th = R diag(C_ell^TT b_ell^2 p_ell^2) R^T with C_ell from data/camb_ref_planck2018.npz. Add the FFP10 noise-only covariance if available, else state that noise is neglected.",
             "2. Test C_th against the FFP10 sample covariance S_T45: M = C_th^-1 S; LRT = 299 [tr M - ln det M - 45] against chi2 with 45*46/2 dof; also report max|diag(S)/diag(C_th) - 1|.",
             "3. If p >= 0.01 and the diagonal ratio is within 0.25, adopt C_th for the T lane (no finite-MC inflation) and recompute Sigma_T; otherwise keep FFP10 and record the reason.",
             "4. Cross-experiment T: same estimator on WMAP9 ILC, Cosmoglobe DR1 and BeyondPlanck CMB maps (union mask); report Sigma_T differences from SMICA in units of the T sd.",
             "5. E-lane alternatives: Sigma_E and the B ell=2 null from (a) Cosmoglobe/BeyondPlanck products with their own uncertainty products, (b) WMAP9 low-resolution Q,U with its noise covariance, (c) PR4 maps with a split-difference noise estimate. A split difference is one realisation: use it for difference tests only, never as a null distribution.",
             "6. Adopted E covariance: S_FFP10 + diag(floor), floor = max(B-null floor of R54-L1, half-mission floor, pipeline-dispersion variance, cross-experiment dispersion variance).",
             "7. E-lane status: CLAIMABLE only if the B ell=2 null passes (p >= 0.01) with the adopted covariance on at least two independent pipelines or experiments; else DIAGNOSTIC. Write RESULTS/R54_L02_RESULT.json."],
         "outputs": [{"path": REL + "/RESULTS/R54_L02_RESULT.json", "schema": "htt.r54.l02_pr4_bypass/1",
                      "required_keys": ["t_analytic_covariance_test", "cross_experiment_T", "e_lane_table", "adopted_e_covariance", "e_lane_status", "provenance"]}],
         "acceptance": [{"metric": "e_lane_status", "op": "in", "value": ["CLAIMABLE", "DIAGNOSTIC"]},
                        {"metric": "pr4_simulations_used", "op": "==", "value": False}],
         "decision_checks": [
             {"check": "the analytic T covariance passes the LRT at p >= 0.01 and its diagonal ratios lie within 0.25 of 1",
              "if_true": "adopt C_th for the T lane (no finite-MC inflation)", "if_false": "keep FFP10 with the calibrated inflation and record the reason"},
             {"check": "max |Sigma_T shift| between SMICA and every other experiment <= 0.5 sd", "if_true": "the T lane is PIPELINE_STABLE",
              "if_false": "the T lane is PIPELINE_DEPENDENT; quote the envelope over experiments"},
             {"check": "the B ell=2 null passes (p >= 0.01) with the adopted covariance on at least two independent pipelines or experiments",
              "if_true": "E lane CLAIMABLE", "if_false": "E lane DIAGNOSTIC; the manuscript quotes the T lane only"}],
         "kill": ["PR4 simulations requested or downloaded: forbidden", "a single split difference used as a null law: invalid"],
         "mutation_gates": ["MG-L03"], "runtime_budget": "2 h CPU"},
        {"id": "R54-L03", "card": "PR-R55-LOCAL-CALIBRATION", "title": "Count-dipole body, same-estimator velocity null and competitor estimators", "depends": ["R54-L5"], "priority": 3,
         "inputs": [{"path": LOCAL + "/raw/Quaia", "role": "Quaia G20.0/G20.5 catalogues, randoms, selection maps"}, {"path": LOCAL + "/raw (NVSS, RACS)", "role": "radio catalogues as in the L2 receipt"},
                    {"path": LOCAL + "/raw/1075476.csv.gz and 27936.parquet", "role": "identify content first; if CatWISE2020 AGN enable the Secrest replication, else record the identity"}],
         "steps": [
             "1. Re-run HTT_SIX_LOOP_INTEGRATED_20261109/L2_real_dipoles.py and confirm the receipt numbers (D_icrs to 1e-4).",
             "2. Clustering body (R54-EQ-32) per catalogue: Quaia N(z) from catalogue redshifts and a published quasar bias model cited from its primary source; NVSS with two bracketing N(z) models cited from primary sources, constant bias 1.6 and 2.0; z_min cuts 0, 0.01, 0.03. Full j_1 integral, no Limber. Report Var(d_i) = (3/(4 pi)) C_1 next to the shot term.",
             "3. Same-estimator velocity null: 500 Poisson mocks on the expectation map times (1 + d_kin.n + d_clust.n), d_clust ~ N(0, body); run the identical estimator and latitude-cut sweep; store bias and covariance of the estimate.",
             "4. Excess test per catalogue and for the common excess with the calibrated covariance; five views (Q with the body, Pi with the mock law).",
             "5. Competitor estimators on the owned catalogues (R54-L07 targets): quasar and radio estimators as specified in ADVERSARIAL_BENCHMARK_SPEC.json; if a mask or cut is not reproducible from the paper text set NOT_REPRODUCIBLE_FROM_TEXT with the reason."],
         "outputs": [{"path": REL + "/RESULTS/R54_L03_RESULT.json", "schema": "htt.r54.l03_count_dipoles/1",
                      "required_keys": ["receipt_reproduction", "clustering_body", "velocity_null", "excess_tests", "five_views", "provenance"]}],
         "acceptance": [{"metric": "receipt_reproduction_max_abs", "op": "<=", "value": 1e-4},
                        {"metric": "mask_hash_of_mocks_equals_mask_hash_of_data", "op": "==", "value": True}],
         "decision_checks": [
             {"check": "mock-recovered kinematic amplitude bias <= 0.2 sd", "if_true": "the estimator is used as is",
              "if_false": "subtract the mock bias, inflate the covariance by the mock scatter and state both"},
             {"check": "the excess test with the calibrated covariance has p >= 0.01 for every owned catalogue", "if_true": "H-L2a stays REJECTED for the owned estimators",
              "if_false": "report the excess with its law; H-L2a is REOPENED"},
             {"check": "at least one competitor estimator is REPRODUCED on an owned catalogue", "if_true": "score benchmark target B05",
              "if_false": "B05 is NOT_REPRODUCIBLE_FROM_TEXT; no comparison claim"}],
         "kill": ["bias parameters taken from memory without a cited primary source: mark UNVERIFIED and use the two-model bracket",
                  "mock null built with a different mask or estimator than the data: invalid"],
         "mutation_gates": ["MG-L04"], "runtime_budget": "3 h CPU"},
        {"id": "R54-L04", "card": "PR-R55-LOCAL-CALIBRATION", "title": "CF4 survey-resolved zero points: is the common hemisphere step a survey calibration term?", "depends": ["R54-L05"], "priority": 1,
         "inputs": [{"path": "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz", "role": "35970 groups (committed)",
                     "sha256": "86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c"},
                    {"path": LOCAL + "/raw/cf4 and " + LOCAL + "/raw/cf4_full", "role": "raw CF4 tables; Table 3 and Table 4 hashes are in docs/research_program/cf4_schur_loop8_20261015/inputs/loop6_result.json",
                     "identity_check": "sha256 of the group table equals source_table3_sha256 or source_table4_sha256 of loop6_result.json; if no file matches stop with BLOCKED_MISSING_INPUT"},
                    {"path": REL + "/RESULTS/R54_L05_CF4_EXACT.json and R54_L05_COSMIC_COV.npz", "role": "exact-body results and cached covariance of the cloud run"}],
         "steps": [
             "1. Re-run scripts/r54/run_r54_cf4_exact.py; it must reproduce the committed JSON (tests/r54/test_r54_results_binding.py). Do not change its constants.",
             "2. From the raw CF4 tables build one survey label per group, joined on group_id (never on row order): for FP the source sample (6dFGSv, SDSS, other), for TF the source sample or band, for SN the compilation. Write the label array next to the catalogue as RESULTS/R54_L04_SURVEY_LABELS.npz with keys group_id, survey. Groups without a unique label get the label of their family plus '_MIXED'.",
             "3. Tabulate per survey: count, fraction north, median z, median e_dmzp. Surveys with fewer than 200 groups in 0.01 <= z < 0.055 are pooled into '<family>_REST'.",
             "4. Add to run_r54_cf4_exact.build_operators (new operator names, existing ones unchanged) the rows: (a) 'survey_step': model eta = redshift-bin monopoles + s * sign(dec) fitted per survey that has at least 100 groups in each hemisphere; (b) 'log_survey': the four-window fit with one monopole column per survey as nuisance; (c) 'survey_offsets': model eta = redshift-bin monopoles of the family + one offset per survey of that family (reference = largest survey), rows = the offsets.",
             "5. Add three more window-fit operators, each equal to 'log_mono' (monopole offsets of FP, SN, TF) plus one nuisance column: 'log_mono_radial' with column z_i (a radial slope of eta inside each window); 'log_mono_galactic' with column |sin b_i|, b from lz.R_I2G (never retype the matrix); 'log_mono_error' with column s_i^2 = ((ln10/5) e_dmzp,i)^2 (homogeneous Malmquist-type term). Fix this list before any of them is run.",
             "6. Recompute the pair sum (the cache key changes; about 12 minutes on 2 cores) and report, with white and with white + exact body errors: every survey offset in mag (R54-EQ-36), every survey step, the consistency chi2 of the steps. Add the leave-6dFGS-out version of the window fit (benchmark target B08).",
             "7. For each of 'log_survey', 'log_mono_radial', 'log_mono_galactic', 'log_mono_error': the headline block of the cloud run, window_subset_nulls, locking_null with 4000 draws (random streams np.random.default_rng([20261116, 11]) to [20261116, 14] in this order) and the class from the classify function of the cloud script. Store them as nuisance_variants next to the three cloud variants.",
             "8. Stability: repeat step 6 for e_dmzp terciles and for the two halves of the redshift range 0.01-0.055; report the common step in each.",
             "9. Write RESULTS/R54_L04_RESULT.json and evaluate decision_checks. Do not edit the decision of the cloud run; append the L04 decision."],
         "outputs": [{"path": REL + "/RESULTS/R54_L04_RESULT.json", "schema": "htt.r54.l04_cf4_survey_split/1",
                      "required_keys": ["survey_table", "survey_offsets", "survey_steps", "log_survey_headline", "nuisance_variants", "stability", "decision", "provenance"]}],
         "acceptance": [{"metric": "cloud_json_reproduced", "op": "==", "value": True},
                        {"metric": "label_join_coverage", "op": ">=", "value": 0.99, "note": "fraction of the 35970 group_id values found in the raw table"}],
         "decision_checks": [
             {"check": "common step after survey monopoles has |z| < 2 (white + exact body)", "if_true": "class SURVEY_ZERO_POINT: the common step of H-L5g is an inter-survey calibration term; H-L5g is REJECTED as a common-mode statement",
              "if_false": "go to the next check"},
             {"check": "single-survey all-sky samples (largest TF survey, SN) each keep a step with |z| >= 2 and agree in sign", "if_true": "class COMMON_MODE_NOT_SURVEY_SPECIFIC: quote the LCDM-body tail of the common step; no physical interpretation",
              "if_false": "class UNRESOLVED"},
             {"check": "the constant quadrupole of 'log_survey' has Wald p >= 0.01", "if_true": "H-L5h is REJECTED (survey monopoles remove it)", "if_false": "H-L5h stays HOLD"},
             {"check": "the joint null of 'log_survey' has p >= 0.01", "if_true": "H-L5a is REJECTED as an excess over the body (survey zero points remove it)",
              "if_false": "H-L5a stays HOLD; quote the conditional statement together with the nuisance table"},
             {"check": "the class is identical for pooled, log_mono, log_survey, log_mono_radial, log_mono_galactic and log_mono_error", "if_true": "quote that class as robust to the listed nuisance models",
              "if_false": "the robust class stays DEPENDS_ON_ZERO_POINT_NUISANCE_MODEL; the manuscript quotes the table and no class; H-L5c stays HOLD"}],
         "kill": ["survey labels joined by row order", "a survey pooled or split after looking at its step", "a nuisance column added or dropped after looking at its effect"],
         "mutation_gates": ["MG-L05", "MG-L06"], "runtime_budget": "2 h CPU"},
        {"id": "R54-L06", "card": "PR-R56-JOINT-BENCHMARK", "title": "Joint frame tomography L(theta | a_lm, z, n, counts)", "depends": ["R54-L01", "R54-L02", "R54-L03", "R54-L04"], "priority": 4,
         "inputs": [{"path": "RESULTS of R54-L01, L02, L03, L04", "role": "calibrated carriers"},
                    {"path": REL + "/RESULTS/R54_L05_CF4_EXACT.json:log_distance.carrier", "role": "CF4 log-distance carrier: theta (36), white and exact-body covariance, velocity response (36x3)"},
                    {"path": LOCAL + "/raw/PantheonPlus", "role": "SN distances and covariance (optional leg)"}],
         "steps": [
             "1. Assemble one precision-form carrier per irreducible block with typed coordinates. Polar vector: beta_RO, V_w per depth, A_cal,p per distance sample. STF2: Sigma_T, Sigma_E, q_w per depth, q_cal,p per sample. Axial vector: omega has no column and is reported as unidentified.",
             "2. Add probes by adding (F, t); profile nuisance with r54_tensor_five_view.profiled_precision; never invert a singular block.",
             "3. Transport hypotheses on the same data and covariance: LCDM body only; one global tilt V_w = V for all depths; type-I shear with perfect-fluid and with stress histories; zero-point terms. Report residual chi2, dof and delta chi2 for each. Repeat the tilt closure of R54-EQ-38 with the count covariance of R54-L03 in place of the receipt errors.",
             "4. Five views per block with fv.five_view_record; identification table from fv.identify with the scale vector stated.",
             "5. Write RESULTS/R54_L06_JOINT.json and one table for the manuscript."],
         "outputs": [{"path": REL + "/RESULTS/R54_L06_JOINT.json", "schema": "htt.r54.l06_joint/1",
                      "required_keys": ["blocks", "identification", "transport_table", "five_views", "provenance"]}],
         "acceptance": [{"metric": "all_views_validated_by_five_view_record", "op": "==", "value": True}, {"metric": "unidentified_directions_reported", "op": "==", "value": True}],
         "kill": ["a prior added to make a block invertible without being named as a body"], "mutation_gates": ["MG-L07"], "runtime_budget": "1 h CPU"},
        {"id": "R54-L07", "card": "PR-R56-JOINT-BENCHMARK", "title": "Adversarial benchmark against published methods", "depends": ["R54-L03", "R54-L04"], "priority": 4,
         "inputs": [{"path": REL + "/ADVERSARIAL_BENCHMARK_SPEC.json", "role": "targets, tolerances and scoring"}],
         "steps": ["1. For each target with owned-data overlap reproduce the published headline number under the published assumptions; record REPRODUCED, NOT_REPRODUCED or NOT_REPRODUCIBLE_FROM_TEXT with the measured value.",
                   "2. Re-run under the common R54 assumptions (declared body, named law, typed frame) and fill the scoring fields of the spec.",
                   "3. Resolve every evidence row whose verification is not VERIFIED by reading the primary source; correct identifiers in state/EVIDENCE_LEDGER.md through the builder.",
                   "4. Novelty check for H-L1b and H-L5g: search the primary literature for prior stress-corrected Bianchi-I CMB shear limits and for a cross-indicator common-mode test of the CF4 hemisphere asymmetry with a catalogue-level LCDM covariance; record the nearest prior art and set the novelty field of both hypotheses."],
         "outputs": [{"path": REL + "/RESULTS/R54_L07_BENCHMARK.json", "schema": "htt.r54.l07_benchmark/1", "required_keys": ["targets", "scores", "novelty_checks", "provenance"]}],
         "acceptance": [{"metric": "targets_with_status", "op": "==", "value": "all"}], "kill": ["scoring a tie as a win"], "mutation_gates": [], "runtime_budget": "1 day"},
        {"id": "R54-L08", "card": "PR-R57-MANUSCRIPT-DECISION", "title": "Manuscript decision with an independent decision-gate reviewer", "depends": ["R54-L06", "R54-L07"], "priority": 5,
         "inputs": [{"path": "all R54 results", "role": "claim table"}],
         "steps": ["1. Update R53/MANUSCRIPT_CLAIM_TABLE.md with rows for the R54 statements that survived calibration.",
                   "2. Ask an independent reviewer for promote/hold/reject on evidence, validity, novelty, testability, robustness and risk separately.",
                   "3. Choose one: bounded note extended by the T+E functionals and the CF4 catalogue-level diagnostics (estimator bias, exact body, cross-indicator common mode), or no paper. No further audit-only loop."],
         "outputs": [{"path": REL + "/FINAL_DECISION_R57.md", "schema": "markdown", "required_keys": []}],
         "acceptance": [{"metric": "decision", "op": "in", "value": ["BOUNDED_NOTE_EXTENDED", "NO_PAPER"]}], "kill": ["opening another research loop instead of deciding"],
         "mutation_gates": [], "runtime_budget": "half day"},
    ]


CLOUD_GATES = [
    ("MG-01", MOD + "/r54_type1_thomson.py", "return (6.0 * e1 + e2) / 7.0, SQRT6 * (e2 - e1) / 7.0", "return (6.0 * e1 + e2) / 7.0, SQRT6 * (e1 - e2) / 7.0",
     "tests/r54/test_r54_modules.py::test_eq03_kernel_shape", "E kernel sign flipped"),
    ("MG-02", MOD + "/r54_type1_thomson.py", "            kt, ke = thomson_kernels(hist.tau(n))", "            kt, ke = (1.0 if n > -math.log(1090.94) else 0.0), thomson_kernels(hist.tau(n))[1]",
     "tests/r54/test_r54_modules.py::test_eq04_kernel_form_equals_ode_form_for_perfect_fluid", "sharp last scattering instead of the T kernel"),
    ("MG-03", MOD + "/r54_tensor_five_view.py", "def chi2_null_tail(stat: float, dof: int, law: str) -> dict:\n    if not law.strip():", "def chi2_null_tail(stat: float, dof: int, law: str) -> dict:\n    if False:",
     "tests/r54/test_r54_modules.py::test_eq22_named_laws_and_calibration", "tail accepted without a law name"),
    ("MG-04", MOD + "/r54_tensor_five_view.py", "    if not is_identified(f, v, scale):\n        return (-math.inf, math.inf)", "    if False:\n        return (-math.inf, math.inf)",
     "tests/r54/test_r54_modules.py::test_eq20_singular_precision_and_hard_case", "unidentified direction silently bounded"),
    ("MG-05", MOD + "/r54_type1_thomson.py", "    use_nu = stress == STRESS_PHOTON_NEUTRINO", "    use_nu = False",
     "tests/r54/test_r54_modules.py::test_eq05_radiation_era_oscillator_matches_analytic_solution", "neutrino anisotropic stress dropped"),
    ("MG-06", MOD + "/r54_lcdm_body.py", "1: 3.0 / (4.0 * math.pi)", "1: 1.0 / (4.0 * math.pi)",
     "tests/r54/test_r54_modules.py::test_eq11_point_window_recovers_velocity_dispersion", "wrong dipole Cartesian factor"),
    ("MG-07", MOD + "/r54_lcdm_body.py", "                    out[9 * a + j, 9 * b + j] = c[a, b]", "                    out[9 * a + j, 9 * b + j] = c[a, b] if a == b else 0.0",
     "tests/r54/test_r54_modules.py::test_eq11_eq12_stacked_body_structure", "cross-depth covariance dropped"),
    ("MG-08", MOD + "/r54_tensor_five_view.py", '        if status == AVAILABLE and name in ("Q", "F") and not str(v.get("body", "")).strip():', "        if False:",
     "tests/r54/test_r54_modules.py::test_five_view_record_fails_closed", "Q or F accepted without a declared body"),
    ("MG-09", MOD + "/r54_tensor_five_view.py", "    return np.kron(tau[:, None], np.eye(dim))", "    return np.kron(np.eye(dim), tau[:, None])",
     "tests/r54/test_r54_modules.py::test_eq23_transport_recovers_law", "transport design mis-ordered"),
    ("MG-10", MOD + "/r54_type1_thomson.py", "-k * (SQRT6 / 10.0 * th + 0.4 * ec), -s]", "-k * (SQRT6 / 10.0 * th + 1.0 * ec), -s]",
     "tests/r54/test_r54_modules.py::test_eq04_kernel_form_equals_ode_form_for_perfect_fluid", "wrong E self-coupling in the ODE"),
    ("MG-11", MOD + "/r54_tensor_five_view.py", "        w_min = lam * ap * nu / (1.0 + lam * ap)", "        w_min = nu",
     "tests/r54/test_r54_modules.py::test_eq20_gauge_range_exact_in_two_dimensions", "Q_min replaced by the centre gauge"),
    ("MG-12", MOD + "/r54_tensor_five_view.py", "return math.sqrt(n * (n - 1.0) / (m * (m - 1.0)))", "return math.sqrt(n * (n - 1.0) / (m * m))",
     "tests/r54/test_r54_modules.py::test_eq22_named_laws_and_calibration", "finite-MC inflation truncated"),
    ("MG-14", MOD + "/r54_lcdm_body.py", "mm = (ri - rj * cos) * (ri * cos - rj) / safe**2", "mm = 0.0 * cos",
     "tests/r54/test_r54_modules.py::test_eq31_pair_sum_equals_dense_and_harmonic_forms", "anisotropic term of the velocity correlation tensor dropped"),
    ("MG-15", MOD + "/r54_lcdm_body.py", "par[a:a + 64] = norm * ((j0 - 2.0 * j1x) @ weight)", "par[a:a + 64] = norm * ((j0 - 1.0 * j1x) @ weight)",
     "tests/r54/test_r54_modules.py::test_eq30_velocity_correlation_limits_and_identity", "wrong Psi_par kernel"),
    ("MG-16", MOD + "/r54_lcdm_body.py", '"g_per_km_s": ((1.0 + z) / (e_z * chi_hat) - 1.0) / c}', '"g_per_km_s": ((1.0 + z) / (e_z * chi_hat) + 1.0) / c}',
     "tests/r54/test_r54_modules.py::test_eq33_distance_factors_low_redshift_limits", "sign of the luminosity-distance velocity term"),
    ("MG-17", MOD + "/r54_distance_estimators.py", 'return {"eta": np.log(fac["y_km_s"] / distance_mpc(mu)), "g_per_km_s": fac["g_per_km_s"],',
     'return {"eta": np.log(C_KM_S * np.asarray(z, float) / distance_mpc(mu)), "g_per_km_s": fac["g_per_km_s"],',
     "tests/r54/test_r54_modules.py::test_eq34_log_estimator_is_unbiased_and_eq35_linear_estimator_is_not", "cosmographic factor dropped (c z instead of H0 d_L)"),
    ("MG-18", MOD + "/r54_distance_estimators.py", "sigma = np.hypot(sigma_star, h_sigma * LN10_OVER_5 * d * np.asarray(e_mu, float))",
     "sigma = np.hypot(sigma_star, h_sigma * LN10_OVER_5 * np.asarray(e_mu, float))",
     "tests/r54/test_r54_modules.py::test_eq35_r36_operator_is_reproduced_from_the_committed_source", "R36 weight law altered"),
    ("MG-19", MOD + "/r54_distance_estimators.py", "    if diag.min() <= 0 or np.linalg.cond(r) > cond_limit:", "    if False:",
     "tests/r54/test_r54_modules.py::test_wls_operator_identity_and_fail_closed", "rank-deficient design accepted"),
    ("MG-20", MOD + "/r54_type1_thomson.py", "(4.0 * xx * xx + 5.0 * mm * mm)", "(4.0 * xx * xx + 4.0 * mm * mm)",
     "tests/r54/test_r54_modules.py::test_eq06_massive_neutrino_stress_weight", "wrong non-relativistic limit of the collisionless stress weight"),
    # gates added after the independent diff review (R54-IR-01, IR-02, IR-03, IR-05): sign, frame and cache conventions of the run scripts
    ("MG-29", MOD + "/r54_tensor_five_view.py", "    fs = d[:, None] * _sym(f, \"precision\") * d[None, :]", "    fs = _sym(f, \"precision\")",
     "tests/r54/test_r54_modules.py::test_eq21_support_interval_in_scaled_coordinates", "support interval computed in unscaled coordinates (R54-IR-08)"),
    ("MG-21", "scripts/r54/run_r54_cf4_exact.py", "    s, cs = v + b, cv + np.diag(sb**2)", "    s, cs = v - b, cv + np.diag(sb**2)",
     "tests/r54/test_r54_conventions.py::test_mg21_eq38_tilt_closure_vanishes_for_one_frame_offset", "sign of the global-tilt closure (R54-EQ-38)"),
    ("MG-22", "scripts/r54/run_r54_cf4_exact.py", '"delta_mu_north_minus_south_mag": float(-2.0 * theta[i] / de.LN10_OVER_5),',
     '"delta_mu_north_minus_south_mag": float(2.0 * theta[i] / de.LN10_OVER_5),',
     "tests/r54/test_r54_conventions.py::test_mg22_eq36_north_modulus_offset_gives_negative_step_and_positive_delta_mu", "sign of the hemisphere-step magnitude (R54-EQ-36)"),
    ("MG-23", "scripts/r54/run_r54_lowz_frames.py", "    g = R_I2G @ (np.asarray(v, float) / np.linalg.norm(v))", "    g = R_I2G.T @ (np.asarray(v, float) / np.linalg.norm(v))",
     "tests/r54/test_r54_conventions.py::test_mg23_icrs_to_galactic_rotation", "ICRS to Galactic rotation transposed"),
    ("MG-24", "scripts/r54/run_r54_cf4_exact.py", "        return float((1 + np.sum(null[k] <= obs[k])) / (n_draw + 1))", "        return float((1 + np.sum(null[k] >= obs[k])) / (n_draw + 1))",
     "tests/r54/test_r54_conventions.py::test_mg24_axis_locking_tail_is_small_for_a_pole_aligned_signal", "direction of the axis-locking tail"),
    ("MG-25", "scripts/r54/run_r54_cmb_type1.py", "    j_e[e2, :] = j_ideal[t2, :]", "    j_e[e2, :] = -j_ideal[t2, :]",
     "tests/r54/test_r54_conventions.py::test_mg25_eq04_ideal_e_response_has_the_sign_of_the_t_response", "sign of the ideal E response (R54-EQ-04)"),
    ("MG-26", "scripts/r54/run_r54_cf4_exact.py", "    return np.array(_digest(stack))", "    return np.array(_digest(np.sort(stack, axis=0)))",
     "tests/r54/test_r54_conventions.py::test_mg26_pair_sum_cache_key_changes_under_row_permutation_and_positions", "pair-sum cache key blind to a row permutation"),
    ("MG-27", "scripts/r54/run_r54_cmb_type1.py", "    theta_re = -th.history_functionals(s_of_n, _ShiftedDepth(hist, n_re), n_start, n_re)[\"Sigma_T\"]",
     "    theta_re = -th.history_functionals(s_of_n, hist, n_start, n_re)[\"Sigma_T\"]",
     "tests/r54/test_r54_conventions.py::test_mg27_reionization_only_e_equals_the_propagated_quadrupole", "reionization quadrupole attenuated to today instead of to z = 50"),
    ("MG-28", "scripts/r54/run_r54_lowz_frames.py", 'return 5.0 * math.log10(1.0 + abs(a) / h_fit) if estimator == "linear" else abs(a) * 5.0 / math.log(10.0)',
     'return 5.0 * math.log10(1.0 + abs(a) / h_fit) if True else abs(a) * 5.0 / math.log(10.0)',
     "tests/r54/test_r54_conventions.py::test_mg28_eq36_log_estimator_magnitude_map", "linear-estimator magnitude map applied to the log estimator"),
]
#: files whose content the mutation receipt certifies; the binding test fails when they change without a new receipt
RECEIPT_SOURCES = (MOD + "/r54_type1_thomson.py", MOD + "/r54_lcdm_body.py", MOD + "/r54_tensor_five_view.py",
                   MOD + "/r54_distance_estimators.py", "tests/r54/test_r54_modules.py",
                   "scripts/r54/run_r54_cf4_exact.py", "scripts/r54/run_r54_lowz_frames.py", "scripts/r54/run_r54_cmb_type1.py",
                   "tests/r54/test_r54_conventions.py", MOD + "/r54_calibration.py", "tests/r54/test_r54_calibration.py",
                   MOD + "/r54_survey.py", "tests/r54/test_r54_survey.py", MOD + "/r54_counts.py", "tests/r54/test_r54_counts.py",
                   MOD + "/r54_pr4_bypass.py", "tests/r54/test_r54_pr4_bypass.py")
LOCAL_GATES = [
    ("MG-L01", "R54-L01", "permute the 300 simulation rows relative to nothing (control) and permute the 135 columns of the simulations only", "covariance identity check of step 1 must fail for the column permutation and pass for the row permutation"),
    ("MG-L02", "R54-L01", "use sims[i] inside its own covariance (no leave-one-out)", "coverage_95 test must leave the acceptance band on a synthetic Gaussian set with N = 60, p = 10"),
    ("MG-L03", "R54-L02", "use a single split-difference vector as the null distribution", "unit test asserting that the E-lane null object refuses n_realisations < 30"),
    ("MG-L04", "R54-L03", "run the mock null with a different latitude cut than the data", "test comparing the mask hash of data and mocks must fail"),
    ("MG-L05", "R54-L04", "join the survey labels by row order after shuffling the raw table", "test asserting that label[group_id] is invariant under a permutation of the raw rows must fail"),
    ("MG-L06", "R54-L04", "fit the survey step without the redshift-bin monopoles", "synthetic catalogue with a monopole trend and unequal hemisphere depths: the test detects the spurious step"),
    ("MG-L07", "R54-L06", "add 1e-6 * I to a singular block before inversion", "identification table must still report the null directions; test compares rank before and after"),
]


#: local gates implemented with their node: (file, pattern, mutation, test that must fail)
LOCAL_GATE_MUTATIONS = {
    "MG-L01": (MOD + "/r54_calibration.py", "    return float(np.max(np.abs(s - s_ref)) / np.max(np.abs(s_ref)))",
               "    return float(np.max(np.abs(np.sort(np.diag(s)) - np.sort(np.diag(s_ref)))) / np.max(np.abs(s_ref)))",
               "tests/r54/test_r54_calibration.py::test_mg_l01_covariance_identity_detects_column_but_not_row_permutation"),
    "MG-L02": (MOD + "/r54_calibration.py", "        s_i = np.cov(np.delete(sims, i, axis=0).T, ddof=1) if leave_one_out else full",
               "        s_i = full",
               "tests/r54/test_r54_calibration.py::test_mg_l02_leave_one_out_obeys_the_hotelling_law_and_self_inclusion_does_not"),
    "MG-L03": (MOD + "/r54_calibration.py", "        if v.size < MIN_NULL_REALISATIONS:", "        if False:",
               "tests/r54/test_r54_calibration.py::test_mg_l03_empirical_null_refuses_a_single_split_difference"),
    "MG-L04": (MOD + "/r54_counts.py", "    return hashlib.sha256(np.packbits(np.asarray(used, bool)).tobytes()).hexdigest()",
               "    return hashlib.sha256(np.packbits(np.ones_like(np.asarray(used, bool))).tobytes()).hexdigest()",
               "tests/r54/test_r54_counts.py::test_mg_l04_mask_hash_distinguishes_latitude_cuts"),
    "MG-L05": (MOD + "/r54_survey.py", '    for pgc, grp, fp in zip(gal["pgc"].tolist(), gal["group"].tolist(), gal["has_fp"].tolist()):',
               '    for pgc, grp, fp in zip(gal["pgc"].tolist(), sorted(gal["group"].tolist()), gal["has_fp"].tolist()):',
               "tests/r54/test_r54_survey.py::test_mg_l05_labels_are_joined_on_identifiers_not_on_row_order"),
    "MG-L06": (MOD + "/r54_survey.py", "    mono = np.column_stack([(zbin == b).astype(float) for b in range(len(z_bins) - 1) if np.any(sel & (zbin == b))])\n    step = ",
               "    mono = np.ones((z.size, 1))\n    step = ",
               "tests/r54/test_r54_survey.py::test_mg_l06_survey_step_needs_the_redshift_monopoles"),
}


def implemented_gates() -> list[tuple]:
    """Every gate with a source mutation: cloud gates and the local gates implemented so far (id, file, old, new, test, meaning)."""
    local = [(gid, *LOCAL_GATE_MUTATIONS[gid][:3], LOCAL_GATE_MUTATIONS[gid][3], m) for gid, _, m, _ in LOCAL_GATES if gid in LOCAL_GATE_MUTATIONS]
    return list(CLOUD_GATES) + local


def gates_doc() -> dict:
    return {"schema": "htt.r54.mutation_gates/1", "rule": "a gate is valid only if the named test fails under the mutation and passes without it; receipts are in MUTATION_GATE_RECEIPT.json",
            "cloud_gates": [{"id": i, "file": f, "replace": a, "with": b, "must_fail": t, "meaning": m, "status": "IMPLEMENTED"} for i, f, a, b, t, m in CLOUD_GATES]
            + [{"id": "MG-13", "file": "any committed input of RESULTS/*.json", "replace": "one byte", "with": "another byte",
                "must_fail": "tests/r54/test_r54_results_binding.py::test_inputs_are_the_committed_ones", "meaning": "result/input drift", "status": "IMPLEMENTED"}],
            "local_gates": [{"id": i, "node": nd, "mutation": m, "detection_to_implement": t, "status": "TO_IMPLEMENT_WITH_NODE"} if i not in LOCAL_GATE_MUTATIONS else
                            {"id": i, "node": nd, "mutation": m, "detection": t, "status": "IMPLEMENTED", "file": LOCAL_GATE_MUTATIONS[i][0],
                             "replace": LOCAL_GATE_MUTATIONS[i][1], "with": LOCAL_GATE_MUTATIONS[i][2], "must_fail": LOCAL_GATE_MUTATIONS[i][3]}
                            for i, nd, m, t in LOCAL_GATES]}


def self_audit_doc() -> dict:
    return {"schema": "htt.r54.self_audit/1", "run": "before every commit and at node close; answer each item with PASS, FAIL or N/A plus the file and key that proves it",
            "control_questions": [
                {"q": "Row index of E_2_0 and B_2_0 in the 135-vector?", "a": [45, 90], "source": "LOCAL_AGENT_CONTRACT.json:conventions.cmb_vector"},
                {"q": "Sign relation between the E and T STF tensors of one type-I shear history?", "a": "same sign (R54-EQ-04)", "source": "r54_type1_thomson.py docstring"},
                {"q": "Is a singular precision matrix regularized?", "a": "never", "source": "LOCAL_AGENT_CONTRACT.json:conventions.precision_form"},
                {"q": "Which law of the CF4 dipole decays as 1/d?", "a": "V (constant velocity)", "source": "scripts/r54/run_r54_lowz_frames.py docstring"},
                {"q": "May PR4 simulations be downloaded?", "a": "no", "source": "PR4_BYPASS_CONTRACT.json"},
                {"q": "Which CF4 estimator is used for inference and why?", "a": "the log-distance ratio (R54-EQ-34); the linear-in-distance estimator is biased by errors in the regressor",
                 "source": "htt/htt/htt/infer/r54_distance_estimators.py docstring"},
                {"q": "Is the CF4 pattern locked to the equatorial pole?", "a": "undecided: the calibrated tail depends on the zero-point nuisance model; neither 'locked' nor 'not locked' may be stated",
                 "source": "RESULTS/R54_L05_CF4_EXACT.json:decision.locking_tail_by_nuisance_variant"},
                {"q": "May the single-axis tail of the hemisphere step be quoted alone?", "a": "no; the sign(dec) axis was chosen after the first pass, so the tail of the scan maximum is quoted with it",
                 "source": "RESULTS/R54_L05_CF4_EXACT.json:zero_point_split.hemisphere_step_scan"},
                {"q": "Does the CMB temperature functional bound a late-time shear whose sign changes?", "a": "no (the bound is infinite); only the diagnostic E lane bounds its rms",
                 "source": "RESULTS/R54_L1_TYPE1_TE.json:data.late_time_shear_bounds"},
                {"q": "What separates acceptance from decision_checks in a node?", "a": "acceptance must hold or the node stops; decision_checks are evaluated once and only select a recorded branch",
                 "source": "LOCAL_AGENT_RESTART_PROMPT.txt"}],
            "items": [
                {"id": "A01", "check": "every number in a report is generated by build_r54_contract.py from RESULTS/*.json", "fail_action": "delete the hand-typed number and rebuild"},
                {"id": "A02", "check": "sha256 of every input equals the value recorded in the result provenance", "fail_action": "stop; BLOCKED_MISSING_INPUT or re-run"},
                {"id": "A03", "check": "every carrier names frame, epoch type and units; mixed frames only through a declared transport", "fail_action": "stop and fix typing"},
                {"id": "A04", "check": "every tail probability names its law; no sigma conversion unless the law is exactly Gaussian or chi-square", "fail_action": "remove the number"},
                {"id": "A05", "check": "claim tier C0; none of conventions.forbidden_phrases_in_reports appears", "fail_action": "rewrite as a bounded statement"},
                {"id": "A06", "check": "no download, no PR4 simulation, no native Bianchi solver, no new science node", "fail_action": "revert"},
                {"id": "A07", "check": "citations: only evidence rows marked VERIFIED are stated as fact; others carry their status", "fail_action": "verify from the primary source or mark"},
                {"id": "A08", "check": "edits stay inside the node file allowlist of RESEARCH_DAG.json", "fail_action": "revert the outside edit"},
                {"id": "A09", "check": "acceptance failed twice: a BLOCKER note is written and thresholds are untouched", "fail_action": "stop the node"},
                {"id": "A10", "check": "analysis choices equal the contract; deviations are listed in DEVIATIONS.json before outputs are read", "fail_action": "record or revert"},
                {"id": "A11", "check": "plausibility ranges: sd(Sigma_T) in [5e-6, 2e-5]; sd(Sigma_E) in [3e-8, 3e-7]; LCDM bulk sd per axis in [50, 200] km/s; r_E(perfect fluid) in [0.070, 0.072]; linear sigma_v,1D in [290, 330] km/s; exact/ideal body sd ratio in [0.8, 2.5]; apparent H of the log estimator in [70, 80] km/s/Mpc", "fail_action": "treat as a bug, not as a result"},
                {"id": "A12", "check": "mutation gates of the node were run and each named test failed under its mutation", "fail_action": "the node is not complete"},
                {"id": "A13", "check": "negative and null results are written to state/NEGATIVE_RESULTS.md through the builder", "fail_action": "add them"},
                {"id": "A14", "check": "every analysis choice made after looking at data is listed in the forking-path register of THEORY_LOOPS.md and its tail is reported with the scan or variant correction", "fail_action": "add the entry or remove the statement"},
                {"id": "A15", "check": "a decision that depends on a nuisance model is reported per model; no single class is quoted when the models disagree", "fail_action": "replace the class by the table"}],
            "end_of_node_report": ["node id and status", "commands run with exit codes", "result file path and sha256", "acceptance table", "mutation receipts", "deviations", "open risks"]}


def _l07_target(tid: str) -> dict:
    x = local_result("R54-L07")
    return {} if x is None else x["targets"].get(tid, {})


def benchmark_doc(n: dict) -> dict:
    def t(i, ev, claim, overlap, target, tol, htt, expected, node):
        return {"id": i, "evidence": ev, "published_claim": claim, "owned_data_overlap": overlap, "replication_target": target, "tolerance": tol,
                "htt_counterpart": htt, "expected_outcome_before_running": expected, "node": node,
                "status": _l07_target(i).get("status", "PENDING_LOCAL"), "score": _l07_target(i).get("score")}
    return {"schema": "htt.r54.adversarial_benchmark/1",
            "scoring": {"WIN": "HTT statement is calibrated where the competitor's is not, or reaches a tighter calibrated bound on the same data and assumptions",
                        "TIE": "same information; differences within stated uncertainty (expected for any sufficient-statistic comparison)",
                        "LOSS": "competitor is tighter or better calibrated on the same data", "NOT_COMPARABLE": "different data or model class; say so",
                        "rule": "a TIE is never reported as a WIN; a WIN needs the competitor replicated first"},
            "method_baselines": ["exact Gaussian likelihood / GLS (tie by sufficiency, R53)", "Sellentin-Heavens t-law (E29)", "Percival matching (E30)",
                                 "eigenstructure LRT for symmetric matrices (E26)", "support-function partial-identification intervals"],
            "targets": [
                t("B01", ["E01", "E02", "E03"], "perfect-fluid Bianchi shear limits from Planck T+pol", "PR3 low-ell carrier (ell = 2 of T,E)", "order of magnitude of the decaying-mode limit", "factor 10",
                  f"perfect-fluid T+E |sigma/H|_0 <= {g3(n['s0_pf_TE'])}; stress family {g3(n['s0_as'])}", "HTT weaker than E01 on the perfect-fluid model (less data); HTT adds the stress-model dependence", "R54-L07"),
                t("B02", ["E09", "E33", "E34"], "CF4 zero-point dipole 4.1 +- 0.9 % (TF W1)", "CF4 groups (four method families; no band label in the committed file)",
                  "constant-dipole amplitude on the TF family", "2 published sd",
                  f"all families, exact body: {n['g_A_pct']:.1f}% ({n['g_A_mag']:.3f} mag), Wald p={g3(n['g_A_wald_p'])}; the TF family alone has p={g3(n['cm_TF_p'])} once the LCDM body is included",
                  "TIE on amplitude; HTT adds the exact body, the per-family comparison and the estimator-bias statement", "R54-L04"),
                t("B03", ["E10", "E11", "E12", "E13", "E35"], "CF4 bulk flow 419 +- 36 km/s at 200 h^-1 Mpc toward (298,-8)", "CF4 groups", "bulk-only direction and amplitude", "direction 20 deg; amplitude 2 sd",
                  f"bulk-only law with white errors: {n['gw_V_km_s']:.0f} km/s, {n['gw_V_watkins']:.0f} deg from E10; with the exact body {n['g_V_km_s']:.0f} km/s toward ({n['g_V_l']:.0f},{n['g_V_b']:.0f})",
                  f"direction reproduced with white errors; with the exact body the fitted hemisphere step has a single-axis tail of {g3(n['st_common_p'])} and a scan-corrected tail of {g3(n['sc_tail_scan'])}", "R54-L04"),
                t("B04", ["E16", "E17", "E18"], "CF4 expansion-rate multipoles with a common axis read as covariant cosmography", "CF4 groups", "their dipole/quadrupole axis", "20 deg",
                  f"best template axis ({n['g_best_l']:.0f},{n['g_best_b']:.0f}); calibrated locking tail by zero-point nuisance model: {tails_text(n)}",
                  "HTT assigns no physical direction: the answer depends on the zero-point nuisance model", "R54-L07"),
                t("B05", ["E19", "E20", "E23", "E24"], "count-dipole excess above 5 sigma", "Quaia, NVSS, RACS (CatWISE only if the unidentified file is that catalogue)", "published amplitude per catalogue", "1.5 published sd",
                  f"receipt estimator: no excess at its systematics budget (p={n['quaia_p']:.2f}, {n['nvss_p']:.2f})", "HTT estimator weaker; competitor estimators decide", "R54-L03"),
                t("B06", ["E21", "E22"], "kinematic velocity from redshift tomography and from aberration", "none owned at map level for aberration", "use as published anchors only", "n/a",
                  "enter R54-L06 as anchors with their published covariance", "NOT_COMPARABLE", "R54-L06"),
                t("B07", ["E25"], "proper-motion signatures of anisotropic expansion", "Gaia CRF3 Gram matrix", "none", "n/a", "L3 conditional statement H-L3d", "NOT_COMPARABLE without a systematics model", "R54-L06"),
                t("B09", ["E46", "E47", "E48", "E03"], "first-order polarized transfer in a flat anisotropic universe (temperature and polarization quadrupoles)", "none needed (analytic)",
                  "the two kernels of R54-EQ-03 and r_E for the same ionization history", "kernel identity; r_E within 5%",
                  f"r_E(perfect fluid) = {n['r_E_pf']:.4f}; kernels SymPy-sealed", "TIE (re-derivation); H-L1a claims no novelty", "R54-L07"),
                t("B08", ["E43"], "CF4 dipoles per constituent catalogue with a log-distance estimator: TFR and 6dFGS larger than SDSS and SN; removing 6dFGS lowers the upper-bin deviation to 1.56 sigma",
                  "CF4 groups plus the raw tables for survey labels", "per-survey hemisphere step or dipole and the leave-6dFGS-out result", "2 published sd",
                  f"family level: steps mutually consistent (p={g3(n['st_cons_p'])}), {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}% of H (scan-corrected tail {g3(n['sc_tail_scan'])}); the survey level is not resolved in the committed file",
                  "TIE expected (same estimator class); HTT adds the pair-sum cross-covariance between catalogues", "R54-L04"),
            ]}


def pr4_doc(n: dict) -> dict:
    return {"schema": "htt.r54.pr4_bypass/1", "rule": "PR4/NPIPE is never a blocker. Its 600 simulations are not owned and must not be requested.",
            "what_pr4_would_add": ["lower large-scale polarization systematics", "an independent simulated null"],
            "legs": [
                {"id": "B1", "name": "analytic signal covariance for the T lane", "why": "ell <= 6 temperature is signal dominated; its covariance is a known linear image of C_ell", "node": "R54-L02", "status": "PENDING_LOCAL"},
                {"id": "B2", "name": "cross-pipeline dispersion (SMICA, Commander, NILC, SEVEM)", "node": "R54-L01", "status": "PENDING_LOCAL",
                 "cloud_evidence": f"Commander E-lane bound {g3(n['SigE_max_comm'])} vs SMICA {g3(n['SigE_max'])}"},
                {"id": "B3", "name": "cross-experiment products (WMAP9, Cosmoglobe DR1, BeyondPlanck v2)", "node": "R54-L02", "status": "PENDING_LOCAL"},
                {"id": "B4", "name": "split differences (PR3 half-mission; PR4 detector splits) as noise realisations for difference tests", "node": "R54-L01/L02", "status": "PENDING_LOCAL"},
                {"id": "B5", "name": "B-null-calibrated systematics floor", "node": "R54-L1", "status": "DONE_SCOPED_C0",
                 "cloud_evidence": f"B ell=2 null p={g3(n['B_p'])}; with the floor the E-lane bound is {g3(n['SigE_max_floor'])}"}],
            "decision_rule": "E-lane covariance = FFP10 + max floor over B2, B4, B5 and B3 dispersion. E-lane statements are CLAIMABLE only if the B ell=2 null passes at p >= 0.01 on two independent pipelines or experiments; otherwise DIAGNOSTIC and the manuscript quotes the T lane.",
            "not_bypassed": "any statement that needs the NPIPE end-to-end simulation law is out of scope and is not made"}


def tracked_subdirs(base: Path) -> list[str]:
    """Git-tracked first-level directories of ``base`` except this one (stable across machines); falls back to the file system."""
    rel = base.relative_to(ROOT)
    try:
        run = subprocess.run(["git", "ls-files", "-z", str(rel)], cwd=ROOT, capture_output=True, text=True, check=True)
        parts = [Path(f).relative_to(rel).parts for f in run.stdout.split("\0") if f]
        names = {p[0] for p in parts if len(p) > 1}
    except (OSError, subprocess.CalledProcessError, ValueError):
        names = {p.name for p in base.iterdir() if p.is_dir()}
    return sorted(names - {R54.name})


def history_doc() -> dict:
    idx = json.loads((R54 / "HISTORY_PR_INDEX.json").read_text())
    dirs = tracked_subdirs(PUB)
    return {"schema": "htt.r54.history_audit/1", "date": DATE,
            "coverage_statement": "Machine inventory is exhaustive at the metadata level (all pull requests; all directories of the observational publication tree). Documents were read selectively; the list below is the complete set read in this session. Anything not listed was inventoried, not read.",
            "pull_requests": {"count": idx["count"], "state_counts": idx["state_counts"], "by_month": idx["by_month"], "lane_keyword_counts": idx["lane_keyword_counts"], "index_file": REL + "/HISTORY_PR_INDEX.json"},
            "observational_tree": {"n_directories": len(dirs), "directories": dirs},
            "read_in_this_session": [
                "AGENTS.md", "CLAUDE.md", "htt/htt/AGENTS.md", "docs/codex_handoff/pr_backlog.yaml (policy, R50-R53 cards)", "docs/codex_handoff/pr_status.yaml (head, notes)",
                "R50_OBSERVED_CONVERGENCE_20261115: SCIENTIFIC_REPORT_KO.md, R51/R51_REPORT_KO.md, R52/R52_REPORT_KO.md, R53/FINAL_DECISION.md, R53/MANUSCRIPT_CLAIM_TABLE.md, HISTORY_REUSE.md, RESEARCH_DAG.json, LOCAL_AGENT_RESTART_PROMPT.txt, R52/R52_JOINT_RESULT.json (structure), R51/observed_carrier.npz",
                "OBSERVATIONAL_CONVERGENCE_R39_20261107/VECTOR_TENSOR_X_FRAMEWORK.md (first sections)", "HTT_SIX_LOOP_INTEGRATED_20261109: DATA_INVENTORY.json, COUNT_DIPOLES_REAL_RECEIPT.json",
                "OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products: R36-01-CF4-OPERATOR (RESULT.json, export_operator.py, audit_backup/derived/A_RAW_36x35970.npz), R36-02-CF4-CORRELATED (RESULT, CONTROLS, MANIFEST, STATUS)",
                "docs/research_program/cf4_schur_loop8_20261015: README_KO.md, inputs/loop6_result.json (head), inputs/selected_source_observables.npz",
                MOD + "/r51_source_bound_response.py", MOD + "/r52_joint_identification.py (conventions, design functions)",
                "scripts/r49/run_r49_cmb_and_multiprobe_lanes.py (estimator), scripts/r51, scripts/r52, scripts/r53 (inputs and factors)",
                "htt/src/common/htt_five_variable_state.py and typefree_functionals.py (public surface)", "htt/bass/collision/thomson_pstf.py (header)"],
            "reinterpretations": [
                {"legacy": "R49 conflation of integrated shear with sigma/H0 (repaired in R51)", "r54": "epoch typing made explicit: the measured objects are the kernel functionals Sigma_T, Sigma_E"},
                {"legacy": "R51 history operator I_hist with sharp last scattering and perfect fluid", "r54": "kernel functional is 0.9157 I_hist; perfect fluid is one member of a stress-dependent family"},
                {"legacy": "R52 five views UNAVAILABLE on the joint carrier", "r54": "bodies and laws declared; views AVAILABLE for the CMB and CF4 lanes"},
                {"legacy": "R52 'A is column-identical to a CF4 calibration dipole'", "r54": "several indicators test for a common mode: the per-family hemisphere steps are mutually consistent with the exact body, but the split axis was chosen after the first pass (scan-corrected tail in RESULTS) and pole locking is undecided"},
                {"legacy": "R52 counts-versus-CF4 frame inconsistency", "r54": "reopened: R52 used the biased linear CF4 estimator without a cosmic body; the closure test of R54-EQ-38 is preliminary"},
                {"legacy": "R36-02 conditional correlated covariance (k bands 0.005-0.05 h/Mpc)", "r54": "replaced by the exact pair-sum body over the full k range at catalogue level (R54-L05, executed)"},
                {"legacy": "H03 four-method gauge", "r54": "reused as the method-monopole and method x hemisphere split of R54-L05"},
                {"legacy": "Loop8 (2026-10-15) CF4 mu-residual Schur analysis: HOLD because the released data give no cosmic velocity covariance", "r54": "linear LCDM pair-sum covariance attached to the log-distance estimator (R54-EQ-34/37)"},
                {"legacy": "R36-01 operator recorded as an external artifact path", "r54": "the committed audit backup A_RAW_36x35970.npz and the committed source rows carry the bound hashes, so the lane runs without the data drive"},
                {"legacy": "R36/H03 linear-in-distance apparent-Hubble estimator", "r54": "shown to be biased by errors in variables and the cosmographic trend; superseded by the log-distance estimator"},
                {"legacy": "MES ceilings of September (premise-conditioned)", "r54": "not used as a body; the LCDM cosmic-variance body and the null-law ellipsoid replace unsourced anchors"},
                {"legacy": "PR4 half-ring probe (R49 L1)", "r54": "PR4 demoted to an optional cross-check by PR4_BYPASS_CONTRACT.json"}]}


def dag_doc(n: dict) -> dict:
    cloud = [
        {"id": "R54-00", "title": "History audit and referee verdict", "status": "DONE_SCOPED_C0", "outputs": ["HISTORY_AUDIT.json", "HISTORY_PR_INDEX.json", "R54_REPORT_KO.md"]},
        {"id": "R54-CORE", "title": "Tensor five-view calculus in precision form", "status": "DONE_SCOPED_C0", "outputs": [MOD + "/r54_tensor_five_view.py", "tests/r54/test_r54_modules.py"]},
        {"id": "R54-L1", "title": "Type-I shear-history functionals from T+E (covers L1 and the CMB side of L3, L4)", "status": "DONE_SCOPED_C0",
         "outputs": [MOD + "/r54_type1_thomson.py", "scripts/r54/run_r54_cmb_type1.py", REL + "/RESULTS/R54_L1_TYPE1_TE.json"]},
        {"id": "R54-L5", "title": "Low-redshift frames on committed multipoles: ideal-sky body, count-dipole excess (its CF4 statements are superseded by R54-L05)", "status": "DONE_SCOPED_C0",
         "outputs": [MOD + "/r54_lcdm_body.py", "scripts/r54/run_r54_lowz_frames.py", REL + "/RESULTS/R54_L5_LOWZ_FRAMES.json"]},
        {"id": "R54-L05", "title": "CF4 at catalogue level: unbiased log-distance estimator, exact LCDM pair-sum body, axis-locking and hemisphere-step nulls under three zero-point nuisance models (covers L2, L3, L5, L6 at low z)",
         "status": "DONE_SCOPED_C0",
         "outputs": [MOD + "/r54_distance_estimators.py", "scripts/r54/run_r54_cf4_exact.py", REL + "/RESULTS/R54_L05_CF4_EXACT.json", REL + "/RESULTS/R54_L05_COSMIC_COV.npz",
                     REL + "/RESULTS/R54_L05_STEP_SCAN_COV.npz"]},
        {"id": "R54-REVIEW", "title": "Independent adversarial review (complete, findings resolved or deferred); the diff review was interrupted and is handed to the local session",
         "status": "DONE_SCOPED_C0", "outputs": [REL + "/INDEPENDENT_REVIEW.json"]},
    ]
    loc = [{k: v for k, v in nd.items() if k in ("id", "card", "title", "depends", "priority", "runtime_budget")} | {"status": node_status(nd["id"])} for nd in local_nodes(n)]
    return {"schema": "htt.r54.research_dag/1", "date": DATE, "branch": BRANCH, "base": BASE, "claim_tier_ceiling": "C0",
            "canonical_cards": {"PR-R54-TENSOR-FRAME-TOMOGRAPHY": [c["id"] for c in cloud], "PR-R55-LOCAL-CALIBRATION": ["R54-L01", "R54-L02", "R54-L03", "R54-L04"],
                                "PR-R56-JOINT-BENCHMARK": ["R54-L06", "R54-L07"], "PR-R57-MANUSCRIPT-DECISION": ["R54-L08"]},
            "execution_order_local": ["R54-L01", "R54-L04", "R54-L02", "R54-L03", "R54-L06", "R54-L07", "R54-L08"],
            "cloud_nodes": cloud, "local_nodes": loc,
            "file_allowlist_local": [REL, MOD + "/r54_*.py", "scripts/r54", "tests/r54", "docs/codex_handoff/pr_status.yaml", "machine_readable/pr_status.yaml"],
            "not_opened": {"Gaia CRF3 tensor systematics": "optional in the plan; not opened and without a node id",
                           "map-level aberration estimator": "H-L6c is HOLD; published anchors only"},
            "local_file_allowlist_note": "R54-L04 may add operator names to scripts/r54/run_r54_cf4_exact.py; existing operators, constants and the decision block stay unchanged",
            "stop_rule": "PR-R57 ends the programme with a manuscript decision. No audit-only successor node may be opened."}


def contract_doc(n: dict) -> dict:
    committed = ["docs/research_program/observational_publication_20261015/R50_OBSERVED_CONVERGENCE_20261115/R51/observed_carrier.npz",
                 "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/RESULT.json",
                 "docs/research_program/observational_publication_20261015/HTT_SIX_LOOP_INTEGRATED_20261109/COUNT_DIPOLES_REAL_RECEIPT.json",
                 "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz",
                 "docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-01-CF4-OPERATOR/audit_backup/derived/A_RAW_36x35970.npz",
                 "tests/fixtures/r54/planck18_tau_history.csv", "tests/fixtures/r54/planck18_linear_pk_z0.csv"]
    return {"schema": "htt.r54.local_agent_contract/1", "date": DATE, "branch": BRANCH, "base": BASE, "tests": TESTS,
            "read_order": ["LOCAL_AGENT_RESTART_PROMPT.txt", "LOCAL_AGENT_CONTRACT.json", "RESEARCH_DAG.json", "SELF_AUDIT_PROTOCOL.json", "MUTATION_GATES.json",
                           "PR4_BYPASS_CONTRACT.json", "ADVERSARIAL_BENCHMARK_SPEC.json", "THEORY_LOOPS.md", "state/"],
            "conventions": CONVENTIONS, "equations": EQUATIONS, "pending_independent_review": pending_review_doc(),
            "committed_inputs_sha256": {p: sha(ROOT / p) for p in committed},
            "module_api": {
                "r54_type1_thomson": ["thomson_kernels(tau)", "thomson_propagator(tau)", "planck18_background()", "OpticalDepthHistory(z, tau, e2_of_n)", "history_functionals(s_of_n, hist, n_start, n_end)", "solve_type1_history(bg, hist, stress, z_init, ...)",
                                      "massive_stress_weight(mu)", "neutrino_stress_scale(masses_ev, t_cmb_k)"],
                "r54_lcdm_body": ["gaussian_window(r_center, sigma_r, norm)", "harmonic_cosmic_cov(ell, k, pk, windows, f, h0)", "stacked_window_body(k, pk, windows, f, h0)", "point_velocity_dispersion_1d(k, pk, f, h0)",
                                  "velocity_correlation(k, pk, f, h0, r, n_k, damping_mpc)", "radial_velocity_covariance_product(op, nhat, r, r_grid, tables, chunk)", "flat_lcdm_distance_factors(z, omega_m)"],
                "r54_distance_estimators": ["multipole_basis(nhat)", "wls_operator(design, weights)", "gaussian_window_weights(z, centers, width)", "distance_mpc(mu)",
                                            "r36_linear_window_operator(mu, e_mu, z, nhat, centers)", "log_distance_ratio(mu, z, omega_m)", "log_noise_variance(e_mu, g, sigma_star)",
                                            "log_window_operator(tau2, z, nhat, centers, width, nuisance, select)", "white_covariance(op, variance)", "magnitude_equivalent(delta_eta)"],
                "scripts/r54/run_r54_cf4_exact.py": ["compute()", "build_operators(cat, a_raw, tau2, survey)", "survey_operators(cat, tau2, survey, mono_nuisance, dec, in_range)",
                                                     "classify(joint_p, removed, tail)", "tilt_closure(v, cv, b, sb)", "cosmic_covariances(stack, labels, n, r)", "common_mode(theta, white, body)",
                                                     "hemisphere_steps(theta, white, body)", "locking_null(theta, cov, rng, n_draw)", "window_subset_nulls(theta, cov)",
                                                     "step_scan(cat, eta, g, tau2, r, rng, reference)", "injections(...)", "tilt_transport(theta, cov, an)"],
                MOD + "/r54_calibration.py": ["covariance_identity_rel(sims, s_ref)", "loo_replicates(sims, j, blocks, leave_one_out)", "coverage(theta, sd, inflation, level)",
                                              "wald_coverage(rep, level)", "hotelling_quantile(level, p_dim, n_dof)", "binomial_band(level, n, n_sd)",
                                              "empirical_quantile_inflation(theta, sd, level)", "EmpiricalNull(values, law)"],
                MOD + "/r54_survey.py": ["galaxy_table(lines)", "survey_labels(group_id, family, gal, sdss_pgc)", "join_coverage(group_id, table_group_ids)",
                                         "pool_small(labels, family, in_range, min_count)", "survey_step_operator(z, nvec, tau2, select, z_bins)",
                                         "survey_offset_operator(z, tau2, labels, family_sel, reference, others, z_bins)"],
                MOD + "/r54_counts.py": ["growth_factor(z, omega_m)", "ho_nz(z, z_star, alpha)", "comoving_distance(z, omega_m, h0)",
                                         "dipole_clustering_cl1(k, pk, z, dndz, bias, omega_m, h0, z_min)", "dipole_axis_variance(cl1)",
                                         "poisson_dipole_fit(counts, expect, nvec)", "mask_hash(used)"],
                MOD + "/r54_pr4_bypass.py": ["mode_tuples(lmax, lmin)", "pack(alm, lmax_alm, modes)", "unit_alm(lmax_alm, ell, m, tag)",
                                             "t_response_matrix(mask, nside, ell_cut, k_inv, out_modes)", "analytic_covariance(r, ells, cl, noise)",
                                             "wishart_lrt(c_model, s_sample, n_dof)", "eb_operator(mask_pol, nside, lmax)", "extract_eb(q, u, mask_pol, k_inv)",
                                             "quadratic_form(x, cov)", "posterior_zero_tail(samples)"],
                "scripts/r54/run_r54_l02_pr4_bypass.py": ["compute()", "floor_null(vec_obs, null_vecs, cov, floor, rng, law)"],
                "scripts/r54/run_r54_l03_counts.py": ["compute()", "clustering_body(q)", "mocks(l2, data, body_sd, d_kin, hashes_data, rng)",
                                                      "competitor_wagenveld(nv)", "competitor_mittal(q)"],
                "scripts/r54/run_r54_l01_te_calibration.py": ["run(sims_path)", "masked_e_response(r51, lanes, op, beam_pixwin, j_ideal)"],
                "scripts/r54/run_r54_l04_cf4_survey.py": ["compute()", "step_summary(theta, white, body, names)", "offset_summary(theta, white, body, names)", "decide(st, hls, classes)"],
                "r54_tensor_five_view": ["identify(F, scale)", "profiled_precision(F, keep)", "EllipsoidBody(name, shape_matrix)", "gauge_range(F, t, body, c2)", "support_interval(F, t, v, c)",
                                         "support_utilization(F, t, body, v, c)", "hotelling_null_tail", "empirical_upper_tail", "gls_fit", "transport_design", "compare_transport_models", "stf2_invariants", "axisymmetry_statistic", "five_view_record"]},
            "coding_rules": [
                "Add code only in " + MOD + "/r54_*.py, scripts/r54 and tests/r54. Reuse the listed API; do not re-implement it.",
                "Every script writes one JSON under RESULTS/ with schema, node, claim_tier, provenance and limitations, then calls no plotting unless asked.",
                "Every new function gets a test that names the equation or gate it protects.",
                "Fail closed: raise on shape, unit, frame or identity mismatch. Never catch an exception to continue.",
                "After each node: run the tests, run the node's mutation gates, run `python scripts/r54/build_r54_contract.py build`, commit with the card id as prefix, push without force."],
            "nodes": local_nodes(n)}


# --------------------------------------------------------------------------- markdown
def state_files(n: dict, hyps: list[dict]) -> dict[str, str]:
    ev = "\n".join(f"| {e['id']} | {e['source']} | {e['identifier']} | {e['verification']} | {e['claim_used']} |" for e in EVIDENCE_ROWS)
    hy = []
    for h in hyps:
        d = h["dimensions"]
        hy.append(f"### {h['id']} ({h['lane']}) - {h['decision']}\n\n{h['statement']}\n\n- evidence: {d['evidence']}\n- validity: {d['validity']}\n- novelty: {d['novelty']}\n"
                  f"- testability: {d['testability']}\n- robustness: {d['robustness']}\n- risk: {d['risk']}\n- kill criterion: {h['kill_criterion']}\n"
                  f"- executed result: {h['executed_result']}\n- next action: {h['next_action']}\n")
    dec = "\n".join(f"| {h['id']} | {h['lane']} | {h['decision']} | {h['executed_result']} | {h['next_action']} |" for h in hyps)
    neg = "\n".join(f"- **{h['id']}** ({h['lane']}): {h['statement']} Result: {h['executed_result']}." for h in hyps if h["decision"] in ("REJECT", "REOPEN"))
    state = f"""# R54 research state ({DATE})

Version: R54.1. Branch `{BRANCH}` on base `{BASE}`. Claim ceiling C0.

## Central question

Can the tensorized five-view layer make calibrated, frame- and epoch-typed statements about
(sigma_ab, omega_a, A_a, beta_a) from data already owned, and does any statement exceed what the
nearest published method gives?

## Active assumptions

- First order in the departure; type I for the CMB lane; linear LCDM for the low-redshift body.
- Two neutrino-stress variants: massless, and minimal normal ordering with the exact collisionless stress weight (R54-EQ-06).
  The present-shear map differs between them and depends on the initial state, so its numbers are illustrations.
- CF4 is analysed at catalogue level (35970 committed groups) with the log-distance estimator and the exact linear LCDM pair-sum body;
  no selection function and no calibration covariance between objects. Zero-point nuisance is modelled in three ways
  (pooled, method monopoles, method x hemisphere steps) and no model is preferred a priori.

## What changed in R54

- Views: all five are available on the CMB lane; on the low-redshift lanes x, Q, Pi and G_F are available and F is UNAVAILABLE
  (an axis scan is not a support functional). R52 had Q, F and Pi unavailable.
- CMB: two history functionals with closed-form kernels (a re-derivation of E46); r_E(perfect fluid) = {n['r_E_pf']:.4f}; Sigma_T = {n['I_ratio']:.4f} x the R51 sharp operator.
- CMB: the present-shear map is model-labelled: {g3(n['s0_pf_TE'])} (perfect fluid, T+E), {g3(n['s0_as'])} (massless stress family), {g3(n['s0_as_no'])} (minimal normal ordering).
- CMB: the T functional is blind to a late-time shear whose sign changes; the E functional bounds its rms at {g3(n['late_E_rms'])} for z < 0.2 (diagnostic lane).
- CMB: PR3 ell = 2 B-mode null fails (p = {g3(n['B_p'])}); the E lane is diagnostic.
- CF4, corrected inside this loop: the R36 linear estimator is biased ({100*n['eiv_frac_lo']:.0f}-{100*n['eiv_frac_hi']:.0f}% of its pole dipole) and the
  ideal-sky body is too small (exact/ideal sd up to {n['x_ratio_dip_hi']:.2f} for the dipole, {n['x_ratio_quad_hi']:.2f} for the quadrupole).
- CF4 with the log-distance estimator and the exact body, by zero-point nuisance model (pooled / method monopoles / method x hemisphere steps):
  joint null p = {g3(n['g_joint_p'])} / {g3(n['m_joint_p'])} / {g3(n['s_joint_p'])}; calibrated locking tail = {g3(n['g_tail_sky'])} / {g3(n['m_tail_sky'])} / {g3(n['s_tail_sky'])};
  class = {n['x_class']} / {n['x_class_mono']} / {n['x_class_split']}; robust class {n['x_class_robust']}.
  Neither "locked to the equatorial pole" nor "not locked" is stated.
- CF4 hemisphere step (z < 0.055): {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}% of H, consistent between FP, TF, SN and OTHER (p = {g3(n['st_cons_p'])});
  single-axis tail {g3(n['st_common_p'])}, tail of the scan maximum over {n['sc_n_axes']} split axes {g3(n['sc_tail_scan'])}. Its reading as a common mode is on HOLD
  (the four estimates share the body; E43 reports survey-level differences).
- Counts: the receipt estimator has power {n['count_power']:.2f} against a doubled dipole, so its non-detection decides nothing; tilt closure with CF4 is preliminary (p = {g3(n['tt_close_p'])}).

## Blockers

None for the cloud nodes. Local nodes need the data drive; PR4 simulations are not needed (PR4_BYPASS_CONTRACT.json).

## Local nodes

{chr(10).join(f"- {nid}: {node_status(nid)}" for nid in LOCAL_ORDER)}

## Next minimal action

{next((nid for nid in LOCAL_ORDER if node_status(nid) == "PENDING_LOCAL"), "none: the programme has a manuscript decision")}, then the remaining nodes in the order above.
"""
    return {
        "RESEARCH_STATE.md": state,
        "EVIDENCE_LEDGER.md": f"# R54 evidence ledger ({DATE})\n\nVerification values: `{V}` (identifier and claim seen in a search result this session), `{P}`, `{M}`.\nRows not marked VERIFIED must be checked from the primary source in R54-L07 before they are cited as fact.\n\n| id | source | identifier | verification | claim used |\n|---|---|---|---|---|\n{ev}\n",
        "HYPOTHESIS_GRAPH.md": f"# R54 hypothesis graph ({DATE})\n\nDecisions are per dimension; there is no aggregate score.\n\n" + "\n".join(hy),
        "DECISION_LOG.md": f"# R54 decision log ({DATE})\n\n| id | lane | decision | executed result | next action |\n|---|---|---|---|---|\n{dec}\n",
        "NEGATIVE_RESULTS.md": f"# R54 negative and reopened results ({DATE})\n\nRejected and reopened hypotheses are retained on purpose. A REJECT entry is not re-tested without new data or a new model; HOLD entries are open and are listed in DECISION_LOG.md.\n\n{neg}\n- **R53 (retained)**: the tensor carrier ties the exact likelihood and the optimal score; it does not beat them.\n"
                               f"- **Withdrawn inside R54, twice**: (1) the first pass (committed R36 multipoles, ideal-sky body, linear estimator) gave a pattern axis {n['lock_angle']:.1f} deg from the "
                               f"equatorial pole with sky fraction {n['lock_frac']:.4f} and nulls of {g3(n['dip_p'])} and {g3(n['quad_p'])}; the catalogue-level run showed the estimator bias and the too-small ideal-sky body. "
                               f"(2) The opposite statement of the second pass, 'not locked to the pole', was withdrawn after the independent review: the calibrated tail is {tails_text(n)} under the three "
                               f"zero-point nuisance models and the flag has low power ({100*n['inj_obs_step_lock']:.0f}% for a step of the observed size). The question is open (H-L5c HOLD).\n"
                               f"- **Per-method dipoles with white errors** (p down to {g3(n['cmw_TF_p'])} for TF) are not evidence: with the exact body every family has p >= {g3(min(n['cm_FP_p'], n['cm_OTHER_p'], n['cm_SN_p'], n['cm_TF_p']))}.\n"
                               f"- **'The dipole excess is absorbed by method x hemisphere steps'** is not evidence either: that nuisance model removes the hemisphere direction by construction.\n"
                               f"- **Finite-MC inflation**: the R53 expression is conservative; the exact Wishart ratio is sqrt[n(n-1)/((n-p+k)(n-p+k-1))] and equals 1 for p = k (analytic {n['infl']:.4f} against leave-one-out {n['loo_ratio']:.4f} for the T-only carrier).\n",
    }


REVIEW_SCOPE = [MOD + "/r54_tensor_five_view.py", MOD + "/r54_type1_thomson.py", MOD + "/r54_lcdm_body.py", MOD + "/r54_distance_estimators.py",
                "scripts/r54/run_r54_cmb_type1.py", "scripts/r54/run_r54_lowz_frames.py", "scripts/r54/run_r54_cf4_exact.py", "scripts/r54/build_r54_contract.py",
                "tests/r54/test_r54_modules.py", "tests/r54/test_r54_results_binding.py"]


def review_record() -> dict:
    path = R54 / "INDEPENDENT_REVIEW.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {"reviewers": [], "incomplete_reviews": []}


def pending_review_doc() -> dict:
    """Review work that the cloud session could not finish; empty status when every started review returned a report."""
    open_items = review_record().get("incomplete_reviews", [])
    if not open_items:
        return {"status": "NONE"}
    return {"status": "PENDING_LOCAL", "interrupted": [{"role": r["role"], "reason": r["reason"]} for r in open_items],
            "when": "before the first edit of any node",
            "reviewer": "an agent or a person that did not write the R54 code; read and run only, no edits",
            "scope": REVIEW_SCOPE,
            "checks": ["each function against the equation it names (R54-EQ ids) and against conventions (signs, units, frames, row order)",
                       "silent failure paths, caught exceptions, and stale caches (model_key and operator fingerprint of both pair-sum caches)",
                       "random streams: one stream per block, seed 20261116, no draw reused between data and null",
                       "tests that would still pass if the function under test were wrong (compare with MUTATION_GATES.json and propose a gate for each gap)",
                       "numbers in generated documents that are typed instead of read from RESULTS/*.json",
                       "statements in generated documents that are stronger than the decision recorded in state/HYPOTHESES.json"],
            "report_format": "one line per finding: id | severity (critical, major, minor) | file:line | defect | concrete failure scenario | suggested fix; then one verdict",
            "record": "append the reviewer with every finding and its resolution to INDEPENDENT_REVIEW.json:reviewers, delete the matching entry of incomplete_reviews, then run the tests and the builder",
            "rule": "a critical finding blocks every node until it is FIXED; a finding is never resolved by weakening a test"}


def review_section_ko() -> str:
    """Section generated from INDEPENDENT_REVIEW.json (written after the independent reviews; never typed into the report)."""
    rec = review_record()
    if not rec["reviewers"] and not rec.get("incomplete_reviews"):
        return "\n## 6. 독립 심사\n\n기록 없음 (INDEPENDENT_REVIEW.json 미작성).\n"
    lines = ["", "## 6. 독립 심사", "", f"작성자와 분리된 심사 중 보고서를 받은 것 {len(rec['reviewers'])}건, 중단된 것 {len(rec.get('incomplete_reviews', []))}건. 상세는 `INDEPENDENT_REVIEW.json`.", ""]
    for r in rec["reviewers"]:
        c = {s: sum(1 for f in r["findings"] if f["severity"] == s) for s in ("critical", "major", "minor")}
        fixed = sum(1 for f in r["findings"] if f["resolution_status"] == "FIXED")
        deferred = sorted({f["deferred_to"] for f in r["findings"] if f["resolution_status"] == "DEFERRED"})
        lines.append(f"- {r['role']}: 판정 {r['verdict']}; critical {c['critical']}, major {c['major']}, minor {c['minor']}; "
                     f"수정 {fixed}건, 로컬 노드로 이관 {len(r['findings']) - fixed}건" + (f" ({', '.join(deferred)})." if deferred else "."))
    for r in rec.get("incomplete_reviews", []):
        lines.append(f"- {r['role']}: 중단. 보고서를 받지 못했다(심사 agent가 계정 사용 한도에서 멈춤). 발견 사항 0건이 아니라 심사 미완료다. "
                     "로컬 세션이 첫 편집 전에 수행한다(`LOCAL_AGENT_CONTRACT.json`의 pending_independent_review).")
    return "\n".join(lines) + "\n"


def sweep_text_ko(n: dict) -> str:
    if n["sweep_flips"]:
        return (f"자유 흐름 시작을 z_i = {g3(n['sweep_z_pre'])} (T_nu = {n['sweep_T_pre']:.1f} MeV)와 {g3(n['sweep_z_flip'])} ({n['sweep_T_flip']:.1f} MeV) 사이에 두면 초기 shear 단위당 Sigma_T의 부호가 바뀐다. "
                f"이 구간은 뮤온·타우 중성미자의 분리 온도 추정 3.12 MeV(E49; 전자 중성미자 1.87 MeV)를 포함한다 "
                f"(부호 변화 전 r_E = {n['rE_lo']:.3f}~{n['rE_hi']:.3f}, 전체 {n['sweep_n']}점에서 {n['rE_all_lo']:.3f}~{n['rE_all_hi']:.3f})")
    return f"전체 {n['sweep_n']}점에서 r_E = {n['rE_all_lo']:.3f}~{n['rE_all_hi']:.3f}이고 Sigma_T의 부호는 유지된다"


def report_ko(n: dict) -> str:
    return report_ko_cloud(n) + local_section_ko(n)


def local_section_ko(n: dict) -> str:
    """Section 7: executed local nodes; every number from RESULTS/R54_L0*_*.json."""
    rows = "\n".join(f"| {nid} | {node_status(nid)} |" for nid in LOCAL_ORDER)
    text = f"""
## 7. 로컬 노드 (R54-L01..L08)

| 노드 | 상태 |
|---|---|
{rows}
"""
    if "l01_edev" in n:
        hm = (f"- half-mission 차 (HM1-HM2)/2 (한 실현, 차이 검정 전용): E2 rms {n['l01_hm_E2']:.3f}, B2 rms {n['l01_hm_B2']:.3f} uK; "
              f"FFP10 잡음 E2 {n['l01_noise_E2']:.3f}, B2 {n['l01_noise_B2']:.3f} uK.\n") if "l01_hm_E2" in n else "- half-mission 다리: SKIPPED_OPTIONAL.\n"
        pdl = (f"- 파이프라인 4종(SMICA, Commander, NILC, SEVEM) B ell=2 경험적 꼬리: {g3(n['l01_B_p_smica'])}, {g3(n['l01_B_p_commander'])}, "
               f"{g3(n['l01_B_p_nilc'])}, {g3(n['l01_B_p_sevem'])}; 파이프라인 간 분산의 rms: E2 {n['l01_disp_E2']:.3f}, B2 {n['l01_disp_B2']:.3f} uK.\n") \
            if "l01_B_p_nilc" in n else "- 파이프라인 분산 다리: SKIPPED_OPTIONAL.\n"
        text += f"""
### 7.1 R54-L01 T+E 추정량 보정 (FFP10 {n['n_sims']}개)

- 캐시 공분산 항등성: 상대 차 {g3(n['l01_ident'])}. T-only LOO Pi = {n['l01_pi_t']:.4f} (R51 재현).
- 마스크 E 응답: e_dev = {g3(n['l01_edev'])} → {n['l01_eflag']}; J_E의 B 행 크기 {g3(n['l01_JB'])} (상대).
- LOO 보정(TE_l2, 매개변수 10개, 각 실현의 공분산은 나머지 299개): 95% 포함률 {n['l01_cov95_lo']:.3f}~{n['l01_cov95_hi']:.3f} (합산 {n['l01_cov95_pool']:.3f}),
  68% 포함률 {n['l01_cov68_lo']:.3f}~{n['l01_cov68_hi']:.3f} (합산 {n['l01_cov68_pool']:.3f}). 판정: R54-L1 구간은 {n['l01_calibrated']}
  (경험적 95% 분위 팽창 {n['l01_q95_lo']:.3f}~{n['l01_q95_hi']:.3f}). 결합 Wald의 Hotelling 95% 포함률 {n['l01_wald_cov95']:.3f}.
- 경험적 LOO 법칙의 관측 꼬리: W_all {n['l01_Wall_p']:.3f}, W_T {n['l01_WT_p']:.3f}, W_E {n['l01_WE_p']:.3f}.
- B ell=2 null, 경험적 LOO 법칙: SMICA {g3(n['l01_B_p'])}, Commander {g3(n['l01_B_p_comm'])} (같은 통계량의 Hotelling 꼬리는 {g3(n['l01_B_hot'])}).
  기준 0.01 → E lane {n['l01_E_status']}.
{hm}{pdl}- 보정 법칙의 주 carrier {n['l01_primary']}: 평균 sd(Sigma_T) = {g3(n['l01_sdT'])}, sd(Sigma_E) = {g3(n['l01_sdE'])}.
"""
    if "l04_common" in n:
        text += f"""
### 7.2 R54-L04 CF4 측량별 영점

- 측량 라벨: 원본 CF4 표에는 측량 열이 없다. FP는 보유한 SDSS FP 카탈로그의 PGC로 나눴다(DV-L04-1): FP_SDSS {n['l04_n_sdss']} group(북쪽 비율 {n['l04_fn_sdss']:.2f}),
  FP_NOT_SDSS {n['l04_n_notsdss']} (북쪽 비율 {n['l04_fn_notsdss']:.2f}; 6dFGSv를 다른 비-SDSS FP와 식별자로 구분할 수 없음), FP_MIXED {n['l04_n_mixed']}. TF·SN·OTHER는 계열 단위 라벨이다(DV-L04-2). group_id 결합률 {n['l04_cov']:.4f}.
- FP 측량 영점: FP_NOT_SDSS - FP_SDSS = {n['l04_off_mag']:.3f} +- {n['l04_off_sd']:.3f} mag (white + exact body, z = {n['l04_off_z']:.2f}). 두 표본은 반구가 거의 겹치지 않으므로 이 영점과 FP의 반구 계단은 사실상 퇴화한다.
- 측량별 반구 계단(0.01 <= z < 0.055, 반구마다 100 group 이상인 측량: {n['l04_step_surveys']}): 공통 계단 {100*n['l04_common']:.2f} +- {100*n['l04_common_sd']:.2f}% of H
  (z = {n['l04_common_z']:.2f}; white만 쓰면 z = {n['l04_common_white_z']:.1f}), Delta mu(N-S) = {n['l04_common_mag']:.3f} mag, 측량 간 일관성 p = {n['l04_cons_p']:.3f}.
  단일 측량 z: TF {n['l04_z_tf']:.2f}, SN {n['l04_z_sn']:.2f}, FP_SDSS {n['l04_z_fp']:.2f}, OTHER {n['l04_z_other']:.2f}. 분할 축 sign(dec)는 사후 선택이므로 이 z는 단일 축 값이고, R54-L05의 축 스캔 보정 꼬리({g3(n['sc_tail_scan'])})와 함께만 인용한다.
- 결정(한 번 평가): 계단 분류 {n['l04_step_class']} (공통 계단 |z| >= 2이므로 측량 영점만으로 설명되지 않고, TF 단독 |z| < 2이므로 공통 모드로도 확정되지 않음).
- log_survey(측량 monopole을 nuisance로): 결합 null p = {g3(n['l04_ls_joint_p'])}, 쌍극 null p = {g3(n['l04_ls_dip_p'])}, 상수 사중극 Wald p = {g3(n['l04_ls_quad_p'])}.
  계약의 결정 규칙에 따라 H-L5a(본체 초과)는 REJECT, H-L5h(상수 사중극)는 HOLD.
- nuisance 모형별 분류(결합 null p / 잠금 꼬리): log_survey {n['l04_cls_survey']} ({g3(n['l04_ls_joint_p'])} / {g3(n['l04_ls_tail'])}), log_mono_radial {n['l04_cls_radial']} ({g3(n['l04_rad_p'])} / {g3(n['l04_rad_tail'])}),
  log_mono_galactic {n['l04_cls_galactic']} ({g3(n['l04_gal_p'])} / {g3(n['l04_gal_tail'])}), log_mono_error {n['l04_cls_error']} ({g3(n['l04_err_p'])} / {g3(n['l04_err_tail'])}); 클라우드의 pooled {n['x_class']}, log_mono {n['x_class_mono']}.
  분류가 모형마다 다르므로 robust class는 {n['l04_robust']}이고 표만 인용한다(H-L5c HOLD).
- 6dFGS 대리 제외(FP_NOT_SDSS, FP_MIXED 제거, method monopole): 결합 null p = {g3(n['l04_no6_joint_p'])}, 쌍극 p = {g3(n['l04_no6_dip_p'])}, 바깥 창 결합 p = {g3(n['l04_no6_outer_p'])}.
- 안정성(공통 계단, % of H / z): e_dmzp 3분위 {100*n['l04_stab_e_tercile_1']:.2f} / {n['l04_stab_z_e_tercile_1']:.2f}, {100*n['l04_stab_e_tercile_2']:.2f} / {n['l04_stab_z_e_tercile_2']:.2f}, {100*n['l04_stab_e_tercile_3']:.2f} / {n['l04_stab_z_e_tercile_3']:.2f};
  적색편이 반쪽 {100*n['l04_stab_z_low_half']:.2f} / {n['l04_stab_z_z_low_half']:.2f}, {100*n['l04_stab_z_high_half']:.2f} / {n['l04_stab_z_z_high_half']:.2f}. 분할마다 계단에 들어간 측량이 다르다(R54_L04_RESULT.json:stability).
"""
    if "l02_lrt" in n:
        bn = ", ".join(f"{k.replace('l02_bnull_', '')} {g3(v)}" for k, v in n.items() if k.startswith("l02_bnull_"))
        text += f"""
### 7.3 R54-L02 PR4 우회 (NPIPE 시뮬레이션 미사용)

- 해석적 T 공분산(ell' <= 30, R51 마스크 결합 + FFP10 잡음): FFP10 표본 공분산에 대한 Wishart LRT {n['l02_lrt']:.1f} / {n['l02_lrt_dof']} dof, p = {g3(n['l02_lrt_p'])};
  최대 |diag 비 - 1| = {n['l02_diag']:.3f}; ell' <= 20 절단과의 최대 상대 차 {g3(n['l02_trunc'])}. 판정 {n['l02_adopt']}: {n['l02_t_reason']}.
- 실험 간 T (합집합 마스크, f_sky {n['l02_fsky_t']:.3f}): SMICA 대비 Sigma_T 최대 이동(T sd 단위) WMAP9 ILC {n['l02_shift_wmap']:.2f}, Cosmoglobe {n['l02_shift_cg']:.2f}, BeyondPlanck {n['l02_shift_bp']:.2f} → {n['l02_t_lane']}.
- E lane 대안: |Sigma_E|_F (ideal 응답 기준) Cosmoglobe {g3(n['l02_cg_E'])}, BeyondPlanck 사후 평균 {g3(n['l02_bp_E'])} ({n['l02_bp_n']} 표본), WMAP9 V {g3(n['l02_wm_E'])};
  PR4 주파수 캐시와 SMICA의 차이 검정 p = {g3(n['l02_pr4_diff_p'])} (분할 차 하나는 null 법칙이 아니므로 차이 검정에만 쓴다).
- 채택 E 공분산: FFP10 + ell = 2 E/B 대각 floor {g3(n['l02_floor'])} uK^2 (R54-L1 B-null {g3(n['l02_floor_R54-L1_B_null_floor_ell2'])}, half-mission {g3(n['l02_floor_half_mission'])},
  파이프라인 분산 {g3(n['l02_floor_pipeline_dispersion'])}, 실험 간 분산 {g3(n['l02_floor_cross_experiment_dispersion'])} 중 최대).
- 채택 공분산의 B ell=2 null 꼬리: {bn}. 통과한 자료 계열: {n['l02_families']} → E lane {n['l02_e_status']} (규칙: 서로 다른 두 계열 이상, DV-L02-9).
- 주의: floor는 FFP10 B2 분산의 {n['l02_floor'] / n['B_rms_ffp'] ** 2:.1f}배이고, 가장 큰 성분(실험 간 분산)은 같은 E2/B2 자료에서 계산된다. 통과는 오차 확대의 결과이며
  채택 공분산에서 E lane 한계는 그만큼 약하다(R54-L08 심사에 넘기는 위험).
"""
    if "l03_repro" in n:
        text += f"""
### 7.4 R54-L03 계수 쌍극: 군집 본체, 같은 추정량 속도 null, 경쟁 추정량

- receipt 재현: D_icrs 최대 차 {g3(n['l03_repro'])} (receipt는 1e-4 단위 반올림).
- 군집 본체(R54-EQ-32, 정확한 j_1; 편향·N(z) 매개변수는 UNVERIFIED 괄호): 축당 sd Quaia {g3(n['l03_body_q'])}, NVSS {g3(n['l03_body_n'])} (괄호 최대, z_min = 0).
- 같은 추정량 mock (Poisson + 군집, 각 500개, 데이터와 같은 마스크): 최대 |편향|/sd Quaia {n['l03_bias_q']:.3f}, NVSS {n['l03_bias_n']:.3f} → 추정량을 그대로 사용; 축당 최대 sd Quaia {g3(n['l03_sd_q'])}, NVSS {g3(n['l03_sd_n'])}.
- 초과 검정(보정 공분산 = mock 공분산 + receipt 계통): Quaia p = {g3(n['l03_p_q'])}, NVSS p = {g3(n['l03_p_n'])}; 계통 항이 없는 mock 경험적 꼬리는 Quaia {g3(n['l03_pi_q'])}, NVSS {g3(n['l03_pi_n'])}.
  공통 초과 Wald p = {g3(n['l03_common_p'])}, 두 목록의 일관성 p = {g3(n['l03_common_cons_p'])}. 결정: {n['l03_excess_decision']}.
- 경쟁 추정량(보유 목록에서 재현): Wagenveld et al. 2023 NVSS Poisson D = {g3(n['l03_w_D'])} (공개 {g3(n['l03_w_pub'])}; 차이 {n['l03_w_dz']:.2f} 공개 sd; 사용 원천 {n['l03_w_N']:.0f} 대 공개 {n['l03_w_Npub']}) → {n['l03_w_status']};
  Mittal et al. 2024 Quaia Poisson (|b| > 40) D = {g3(n['l03_m_D'])} (공개 {g3(n['l03_m_pub'])}; 차이 {n['l03_m_dz']:.2f} 공개 sd) → {n['l03_m_status']}.
"""
    if "l06_np" in n:
        rows_p = "\n".join(f"| {n[f'l06_p{i}_name']} | {n[f'l06_p{i}_chi2']:.1f} | {n[f'l06_p{i}_dof']} | {g3(n[f'l06_p{i}_p'])} |" for i in range(n["l06_np"]))
        rows_s = "\n".join(f"| {n[f'l06_s{i}_name']} | {n[f'l06_s{i}_chi2']:.1f} | {n[f'l06_s{i}_dof']} | {g3(n[f'l06_s{i}_p'])} |" for i in range(n["l06_ns"]))
        text += f"""
### 7.5 R54-L06 결합 frame tomography (정밀도 형태)

- 식별: polar 블록(V_w 4깊이, A_cal, beta_ex) rank {n['l06_rank_p']} / {n['l06_dim_p']} (깊이별 V_w와 A_cal이 퇴화); STF2 블록 rank {n['l06_rank_s']} / {n['l06_dim_s']} (완전유체 지도),
  복사 응력 가설에서는 rank {n['l06_rank_s_stress']} / {n['l06_dim_s']} (E lane 없이 CMB가 s0를 고정하지 않음); 축 벡터 omega는 열이 없어 미식별.
- 전역 tilt 폐합(R54-EQ-38, R54-L03 계수 공분산): chi2 {n['l06_closure_chi2']:.2f} / 3, p = {g3(n['l06_closure_p'])} (R54-L05의 예비값 {g3(n['l06_closure_prelim_p'])}).
- 완전유체 s0의 Frobenius 95% 상한 {g3(n['l06_s0_max'])} (CMB T + CF4 사중극, 보정 사중극 q_cal 자유).

| polar 블록 수송 가설 | chi2 | dof | p |
|---|---|---|---|
{rows_p}

| STF2 블록 수송 가설 | chi2 | dof | p |
|---|---|---|---|
{rows_s}
"""
    if "l07_n_tie" in n:
        tg = ", ".join(f"{t} {n[f'l07_{t}_status']}/{n[f'l07_{t}_score']}" for t in ("B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B09"))
        text += f"""
### 7.6 R54-L07 적대적 벤치마크

- 목표별 상태/점수: {tg}.
- 점수 합계: WIN {n['l07_n_win']}, TIE {n['l07_n_tie']}, LOSS {n['l07_n_loss']}, NOT_COMPARABLE {n['l07_n_not_comparable']}. TIE를 WIN으로 세지 않는다.
- 증거 검증: 미검증 {n['l07_ev_checked']}행 중 {n['l07_ev_verified']}행을 일차 자료로 확인; 남은 행 {n['l07_ev_open']} (상태를 달고 인용).
- 신규성(H-L1b, H-L5g): state/HYPOTHESIS_GRAPH.md의 novelty 항목(가장 가까운 선행연구 포함).
"""
    return text


def report_ko_cloud(n: dict) -> str:
    def pc(key: str) -> str:
        return f"{100 * n[key]:.0f}%"
    return f"""# R54 보고서 — 심사, 이론 루프, 실행 결과 ({DATE})

브랜치 `{BRANCH}` (base `{BASE}`). 주장 상한 C0. 이 문서의 모든 수치는 `RESULTS/*.json`에서 생성된다.

## 1. 심사 결과 (출판가능성)

**권고: Major revision. 현재 상태로는 R53의 "bounded note"가 맞고, 방법론+발견 논문은 성립하지 않는다.**
R54에서 방어 가능한 내용은 세 가지다: (i) 모델 라벨이 붙은 CMB 범함수 한계와 그 모델 의존성, (ii) CF4 추정량 편향과 카탈로그 수준 LCDM body, (iii) zero-point 모형 의존성을 그대로 보고하는 진단표.
로컬 보정(R54-L01, R54-L04)을 통과하면 bounded note를 확장한 JCAP/PRD급 관측-방법 논문 한 편은 방어 가능하다. 새 물리 검출 주장은 없다.

강점
- 프레임·epoch 타입을 강제하는 선형-가우스 carrier 계층. R49의 Sigma 대 sigma/H0 혼동 같은 오류를 타입 오류로 만든다.
- 유한 MC 공분산 법칙의 held-out 보정(R51-R53)과 음성 결과의 보존.
- 식별 불가능 방향(omega, A)을 prior로 덮지 않고 보고한다.

치명적 약점
1. R52 관측 결합에서 5변수 중 Q, F, Pi가 UNAVAILABLE이었다. R54에서 CMB lane은 다섯 뷰가 모두 채워졌다. 저적색편이 lane은 x, Q, Pi, G_F만 채워지고 F는 UNAVAILABLE로 남는다(축 스캔은 support 범함수가 아니다).
2. 5변수 뷰는 정보를 더하지 않는다(R53 정리: exact likelihood와 tie). 보고 규약이지 새 통계량이 아니다. 기여는 타입화된 보고, 식별성, transport 검정에 한정된다.
3. R51의 조건부 (sigma/H)_0 한계는 perfect-fluid 가정에 묶여 있었다. 복사 비등방 stress, 중성미자 질량, 초기 상태에 따라 부호와 크기가 바뀐다(2.1).
4. PR3 저-ell 편광은 B-모드 null을 통과하지 못한다. E lane은 진단용이다.
5. CF4 lane의 추정량(거리에 선형)이 편향돼 있었고 공분산에 우주 속도장 항이 없었다. 둘을 고친 뒤의 결론은 zero-point nuisance 모형에 따라 달라진다(2.3). 선택 함수와 보정 공분산은 모형에 없다.
6. Type I 밖의 Bianchi family는 source-bound transfer가 없어 평가 불가다.
7. 선행연구와 겹친다: kernel 계(E46), CF4 zero-point dipole(E09, E33), 카탈로그별 log-distance dipole(E43), CF4 팽창률 다중극(E16), dipole anomaly 종설(E19).
8. 분석 선택 일부가 사후적이다(반구 분할 축, 공통 적색편이 구간, 판정 규칙). `THEORY_LOOPS.md`의 forking-path 목록에 기록했고 스캔 보정 꼬리를 함께 보고한다.

수정 우선순위
1. R54-L01: T+E 추정량 LOO 보정과 masked E 응답.
2. R54-L04: CF4 survey별 zero-point 분리와 nuisance 변형(반경 기울기, 은하 위도, 거리 오차항). 분류가 모형에 무관해지는지 판정한다.
3. R54-L02: PR4 없이 편광 공분산 삼각검증.
4. R54-L03: count dipole clustering body와 동일 추정량 null.
5. R54-L06/L07: 결합 프레임 단층과 적대적 벤치마크, 그 뒤 R54-L08 결정.

## 2. 여기서 실행한 결과

### 2.1 CMB: type-I shear history의 두 범함수 (R54-L1)

- 닫힌형 kernel: K_T = (6e^-tau + e^(-3tau/10))/7, K_E = (sqrt6/7)(e^(-3tau/10) - e^-tau). SymPy 봉인, ODE와 단위시험 허용오차 안에서 일치. E46(Basko & Polnarev 1980)이 푼 계의 재유도이며 새 결과로 주장하지 않는다.
- T와 E 사중극은 shear history의 서로 다른 선형 범함수 Sigma_T, Sigma_E를 잰다. kernel은 이온화 history만으로 정해지고 shear 동역학과 무관하다.
- Perfect fluid: Sigma_T/s0 = {n['I_T']:.0f} (R51 sharp 연산자 {n['I_sharp']:.0f}의 {n['I_ratio']:.4f}배), r_E = Sigma_E/Sigma_T = {n['r_E_pf']:.4f}. E의 {100*n['reion_share']:.0f}%가 재이온화 산란 몫이다.
- 복사 비등방 stress: 광자만 넣어도 부호가 뒤집힌다(s0/Sigma_T = {g3(n['s0_photon'])}). 광자+중성미자 2-모드 족에서는 s0 = c_T Sigma_T + c_E Sigma_E이고, 무질량이면 (c_T, c_E) = ({g3(n['c_T'])}, {g3(n['c_E'])}), 최소 정상 질량순서(0, {n['nu_m2']}, {n['nu_m3']} eV; R54-EQ-06의 무충돌 stress 가중)이면 ({g3(n['c_T_m'])}, {g3(n['c_E_m'])})다.
- 초기 상태 sweep(중성미자 분리 시점 z_i = {g3(n['sweep_z_lo'])}~{g3(n['sweep_z_hi'])}): {sweep_text_ko(n)}. 초기 상태에 따라 T 범함수 자체가 0을 지난다.
- 데이터(커밋된 PR3 carrier, FFP10 N=300, 주 carrier {n['primary']}): sd(Sigma_T) = {g3(n['sdT'])}, sd(Sigma_E) = {g3(n['sdE'])}; 전체 Wald 통계량 {n['wald_all_stat']:.2f}, p = {n['wald_all_p']:.2f} ({n['wald_all_law']}). 검출 없음.
- 95% 한계(Frobenius): |Sigma_T| <= {g3(n['SigT_max'])}, |Sigma_E| <= {g3(n['SigE_max'])} (B-null floor {g3(n['SigE_max_floor'])}, Commander {g3(n['SigE_max_comm'])}).
- 방향별 동시 95%: |n.Sigma_T.n| <= {g3(n['dir_T'])}. 재결합 이후 방향별 누적 팽창 차이의 상한이다.
- 현재 shear |sigma/H|_0의 95% 예시값: perfect fluid T만 {g3(n['s0_pf_T'])}; perfect fluid T+E {g3(n['s0_pf_TE'])}; 무질량 2-모드 족 {g3(n['s0_as'])}; 최소 정상 질량순서 {g3(n['s0_as_no'])}. 한계가 아니라 모델 의존성의 예시이며 모델 라벨 없이 인용할 수 없다.
- 후기 shear: z < 0.2에 국한된 shear에 대해 T 범함수는 부호가 일정한 history는 제한하지만(한계 {g3(n['late_T_const'])}) 부호가 바뀌는 history에는 감도가 없다. 그 rms에 대한 E 범함수의 한계는 {g3(n['late_E_rms'])}(B-null floor {g3(n['late_E_rms_floor'])})뿐이다(진단 lane). z < 0.5면 {g3(n['late_E_rms_z05'])}, z < 2면 {g3(n['late_E_rms_z2'])}. 후기 비등방 stress가 있으면 "CMB가 저적색편이 shear를 배제한다"는 문장은 성립하지 않는다(H-L3c 기각, 조건부 진술 H-L3d).
- B-null gate 실패: SMICA p = {g3(n['B_p'])}, Commander p = {g3(n['B_p_comm'])} (관측 rms {n['B_rms_obs']:.2f} 대 FFP10 {n['B_rms_ffp']:.2f} uK). E ell=2는 통과(p = {n['E_p']:.2f}). E lane 수치는 진단용이다.
- R51 재현: T45 LOO tail {n['pi_loo']:.3f}; LOO sd/plug-in sd = {n['loo_ratio']:.4f}, 정확한 Wishart 식 {n['infl']:.4f}. R53의 식은 이보다 약간 커서 보수적이었다. p = k인 주 carrier는 보정 계수가 {n['infl_primary']:.0f}이고 꼬리는 Hotelling 법칙이다.

### 2.2 저적색편이 1차: 커밋된 R36 multipole + ideal-sky body (R54-L5) — CF4 부분은 2.3으로 대체됨

- Ideal-sky body null: dipole p = {g3(n['dip_p'])}, quadrupole p = {g3(n['quad_p'])}; 템플릿 최적 축이 적도 극에서 {n['lock_angle']:.1f}도, 하늘 비율 {n['lock_frac']:.4f}.
- 이 1차 결과는 "적도 극 고정"으로 읽혔으나 추정량 편향과 과소한 body 위에 서 있었다. 2.3에서 다시 쟀다.
- Count dipole(커밋된 receipt): 운동학적 기대 대비 초과 tail p = {n['quaia_p']:.2f} (Quaia), {n['nvss_p']:.2f} (NVSS); 공통 초과 p = {n['common_p']:.2f}. 그러나 이 추정량이 운동학적 dipole의 2배인 dipole을 5% 수준에서 잡을 확률은 {n['count_power']:.2f}이다. 판정 불가이며(H-L2a HOLD) 공개된 anomaly의 반증이 아니다.

### 2.3 저적색편이 2차: CF4 카탈로그 수준 분석 (R54-L05, 커밋된 35970 group으로 여기서 실행)

저장소에 CF4 source 행과 R36 연산자 백업이 커밋돼 있어(해시 일치) 로컬 드라이브 없이 실행했다. R36 연산자는 source에서 {g3(n['x_parity_op'])} 오차로 재구성된다.

교정 1 — 추정량. R36/H03 추정량은 c z를 잡음 있는 거리 d에 선형 회귀한다. 같은 추정량 null(FLRW 거리 + 거리지수 오차 + 250 km/s)에서 이 추정량은 스스로 다중극을 만든다.
- 편향이 극 방향 dipole의 {100*n['eiv_frac_lo']:.0f}-{100*n['eiv_frac_hi']:.0f}%를 차지한다. 편향을 빼면 quadrupole null p와 극 하늘 비율이 바뀐다(p: {g3(n['xl_quad_p'])} → {g3(n['xb_quad_p'])}; 하늘 비율: {g3(n['xl_sky_frac'])} → {g3(n['xb_sky_frac'])}).
- 대체 추정량: eta = ln[H0 d_L(z)/d]를 [1, n, STF5]에 가중 회귀(R54-EQ-34). 거리지수에 선형이라 가우스 오차에서 불편이다(단위 시험으로 확인). 창별 H = {n['g_H_lo']:.1f}-{n['g_H_hi']:.1f} km/s/Mpc.

교정 2 — body. 35970^2 쌍 전체에 대한 선형 LCDM 속도 상관 pair-sum(R54-EQ-30/31/37; sigma_v = {n['x_sigma_v']:.0f} km/s).
- Exact/ideal 표준편차 비: dipole {n['x_ratio_dip_lo']:.2f}-{n['x_ratio_dip_hi']:.2f}, quadrupole {n['x_ratio_quad_lo']:.2f}-{n['x_ratio_quad_hi']:.2f}. Ideal-sky body는 과소였다.

교정 후 결과 (log 추정량 + exact body). 조건: 선형 이론, 선택 함수 없음, 보정 공분산 없음.

Zero-point nuisance 모형별 요약. 세 모형 중 어느 것도 선험적으로 우선하지 않는다.

| nuisance 모형 | dipole null p | quadrupole null p | joint null p | 극 이득 | 극 고정 꼬리 | 규칙상 분류 |
|---|---|---|---|---|---|---|
| pooled (없음) | {g3(n['g_dip_p'])} | {g3(n['g_quad_p'])} | {g3(n['g_joint_p'])} | {n['g_pole_gain']:.1f} | {g3(n['g_tail_sky'])} | {n['x_class']} |
| 방법별 monopole | {g3(n['m_dip_p'])} | {g3(n['m_quad_p'])} | {g3(n['m_joint_p'])} | {n['m_pole_gain']:.1f} | {g3(n['m_tail_sky'])} | {n['x_class_mono']} |
| 방법 x 반구 계단 | {g3(n['s_dip_p'])} | {g3(n['s_quad_p'])} | {g3(n['s_joint_p'])} | {n['s_pole_gain']:.1f} | {g3(n['s_tail_sky'])} | {n['x_class_split']} |

- 종합 분류: {n['x_class_robust']}. 극 고정 꼬리는 exact body에서 뽑은 null {n['x_n_null']}회로 보정한 하늘 비율 꼬리다.
- "방법 x 반구 계단" 모형은 반구 방향 자체를 nuisance로 빼므로 dipole 초과가 사라지는 것은 거의 자동이다. 증거로 쓰지 않는다.
- pooled null의 chi2: dipole {n['g_dip_chi2']:.1f}/12, quadrupole {n['g_quad_chi2']:.1f}/20, 합 {n['g_joint_chi2']:.1f}/32. Damped body p = {g3(n['g_joint_p_damped'])}; body를 2배로 하면 p = {g3(n['g_joint_p_x2'])}.
- 창별 분해(pooled): 안쪽 두 창(z = 0.025, 0.04) joint p = {g3(n['wi_joint_p'])} (dipole {g3(n['wi_dip_p'])}, quadrupole {g3(n['wi_quad_p'])}); 바깥 두 창(z = 0.06, 0.08) joint p = {g3(n['wo_joint_p'])} (dipole {g3(n['wo_dip_p'])}, quadrupole {g3(n['wo_quad_p'])}). 방법별 monopole 모형에서는 {g3(n['mwi_joint_p'])}와 {g3(n['mwo_joint_p'])}. z >= 0.055 표본은 FP가 {pc('outer_FP_frac')}이고 그 FP의 {pc('outer_FP_north_frac')}가 북반구다. 바깥 창의 dipole은 사실상 북쪽 FP와 나머지의 비교다.
- 극 고정 판정의 검정력: 관측 크기({n['inj_obs_step_mag']:.3f} mag)의 반구 계단을 주입해도 pole_locked 판정이 켜지는 비율은 {pc('inj_obs_step_lock')}뿐이다(주입 없음 {pc('inj_none_lock')}). 꼬리가 0.01보다 크다는 것이 "고정 아님"을 뜻하지 않는다. "고정"도 "고정 아님"도 주장하지 않는다(H-L5c HOLD).
- 축(pooled): 적도 극 이득 {n['g_pole_gain']:.1f}, 은하 극 {n['g_gal_gain']:.1f}, 최적 축 (l,b) = ({n['g_best_l']:.0f}, {n['g_best_b']:.0f})로 적도 극에서 {n['g_best_angle']:.0f}도.
- 깊이 법칙: pooled에서 상수 분율 dipole chi2 = {n['g_chi2_A']:.1f}/9, 속도 법칙 chi2 = {n['g_chi2_V']:.1f}/9. 방법별 monopole을 주변화하면 차이가 사라진다({n['m_chi2_A']:.1f} 대 {n['m_chi2_V']:.1f}).
- 상수 dipole(pooled): H의 {n['g_A_pct']:.1f}% ({n['g_A_mag']:.3f} mag), 극 축에서 {n['g_A_angle']:.0f}도; 극 평행 성분 {100*n['g_Apar']:.2f} +- {100*n['g_Apar_sd']:.2f}% (북쪽이 낮다), 수직 성분 p = {g3(n['g_Aperp_p'])}.
- 지표별 dipole (z = 0.01-0.055): white 오차로는 p가 {g3(n['cmw_TF_p'])}(TF)까지 내려가지만 exact body를 넣으면 FP {g3(n['cm_FP_p'])}, TF {g3(n['cm_TF_p'])}, SN {g3(n['cm_SN_p'])}, OTHER {g3(n['cm_OTHER_p'])}. 네 family는 하나의 공통 벡터와 양립하지만(일치 p = {g3(n['cm_cons_p'])}) 그 공통 dipole 자체는 유의하지 않다(Wald p = {g3(n['cm_wald_p'])}).
- 방법별 반구 계단 s (eta = z-bin monopole + s sign(dec)), exact body 오차: FP {100*n['st_FP']:.2f} +- {100*n['st_FP_sd']:.2f}%, TF {100*n['st_TF']:.2f} +- {100*n['st_TF_sd']:.2f}%, SN {100*n['st_SN']:.2f} +- {100*n['st_SN_sd']:.2f}%, OTHER {100*n['st_OTHER']:.2f} +- {100*n['st_OTHER_sd']:.2f}%. 공통 계단 {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}%, 일치 p = {g3(n['st_cons_p'])}. 등가 거리지수 차 (북-남) {n['st_mag']:.3f} +- {n['st_mag_sd']:.3f} mag.
- 반구 분할 축 스캔(exact body, z < 0.055의 {n['sc_n_obj']}개, 축 {n['sc_n_axes']}개): sign(dec) 축은 1차 분석 뒤에 골랐으므로 단일 축 꼬리({g3(n['st_common_p'])})만 인용할 수 없다. 스캔 최대값의 꼬리 = {g3(n['sc_tail_scan'])}. 천구 극은 {n['sc_n_axes']}개 축 중 |z| 순위 {n['sc_pole_rank']}위이고, null에서 최적 축이 극 10도 안에 올 확률 = {g3(n['sc_null_near_pole'])}. 네 family 추정은 body를 공유한다(최량 단일 family 분산 / 공통 계단 분산 = {n['sc_var_ratio']:.2f}; 독립이면 4).
- 계단(z < 0.055)과 창 초과(바깥 창이 더 강함)는 서로 다른 측정이다. 하나가 다른 것을 설명한다고 쓰지 않는다.
- 선행연구 대조: E43(Nusser & Tully 2026)은 log-distance 추정량으로 구성 카탈로그별 dipole을 재서 TFR과 6dFGS가 SDSS와 SN보다 크다고 보고했다. Family 수준에서 계단 크기가 같은 것은 서로 다른 원인(FP 안의 6dFGS 대 SDSS zero-point, 얕은 TF/SN 표본의 국소 유동)의 일치일 수 있다. "공통모드" 해석은 보류(H-L5g HOLD)이고 수치만 보고한다.
- 상수 quadrupole: H의 {n['g_quad_pct']:.1f}%, Wald p = {g3(n['g_quad_wald_p'])}(방법 x 반구 계단 모형 {g3(n['s_quad_wald_p'])}). 사후 통계량이며 주축이 모형에 따라 바뀐다. 보류.
- Jackknife(적도대, 북극관, 남극관 제외): 극 dipole {100*n['jk_lo']:.1f}% ~ {100*n['jk_hi']:.1f}%.
- 주입 시험(실제 footprint, exact body 잡음; 상수 법칙 선호 비율, 계단 주입 / 유동 주입): {n['inj_step_mag']:.2f} mag와 {n['inj_flow']:.0f} km/s에서 {pc('inj_step_A')} / {pc('inj_flow_A')}; 관측 크기({n['inj_obs_step_mag']:.3f} mag, {n['inj_obs_flow']:.0f} km/s)에서 {pc('inj_obs_step_A')} / {pc('inj_obs_flow_A')}; 방법 monopole 연산자는 관측 크기에서 {pc('injm_obs_step_A')} / {pc('injm_obs_flow_A')}. 관측 크기에서는 두 법칙이 결과를 보기 전에 정한 기준(90% / 10%)만큼 갈리지 않는다(H-C3 {n['h_c3_decision']}).
- Bulk-only 벤치마크: white 오차면 {n['gw_V_km_s']:.0f} km/s, E10 방향에서 {n['gw_V_watkins']:.0f}도(재현). Exact body면 {n['g_V_km_s']:.0f} km/s, (l,b) = ({n['g_V_l']:.0f}, {n['g_V_b']:.0f}).
- Global tilt 닫힘 시험(R54-EQ-38, 예비): V_CF4 + c beta_excess = 0의 p = {g3(n['tt_close_p'])} (V만), {g3(n['tt_close_p_A'])} (상수 dipole 주변화). Count 쪽 검정력이 낮아 예비 수치다(H-L6b HOLD).
- 판정 규칙의 지위: 규칙과 임계값은 exact-body 수치를 보기 전에 코드에 넣었으나 커밋하지 않았으므로 사전 등록이 아니다. 물리적 방향 의존 Hubble 인자나 A_a의 검출이 아니다. 상수 dipole은 거리 zero-point dipole과 분리되지 않는다(H-L3b). 남은 질문은 survey 수준 zero-point와 nuisance 변형에서 분류가 하나로 모이는가이고 R54-L04가 답한다.

## 3. 주제별 결정

| 주제 | 결정 | 근거 |
|---|---|---|
| 핵심 계층 | PROMOTE (H-C1 보고 규약), REJECT (H-C2 검정력 이득), {n['h_c3_decision']} (H-C3 깊이 법칙 분리) | 2.3, state/HYPOTHESIS_GRAPH.md |
| 저-ell 형태와 물리량 | PROMOTE (H-L1a 범함수 재유도, H-L1b 모델 의존성), REJECT (H-L1c 편광 액면 사용, H-L1d ell>=3의 type-I 해석) | 2.1 |
| Dipole anomaly | HOLD (H-L2a 검정력 부족, H-L2b clustering body), REOPEN (H-L2c counts 대 CF4 프레임) | 2.2, 2.3 |
| Beyond-FLRW 운동학 측정 | PROMOTE (H-L3a, H-L3b: R52에서 승계한 구조적 식별성 진술; H-L3d: 조건부), REJECT (H-L3c: 조건 없는 진술) | 2.1, state/HYPOTHESIS_GRAPH.md |
| 비등방성 분류 | HOLD (H-L4a: 불변량의 null 보정 없음; family 식별은 차단 유지) | state/HYPOTHESIS_GRAPH.md |
| 방향·적색편이 의존 Hubble | REJECT (H-L5e 물리적 검출), PROMOTE (H-L5f 추정량 편향), HOLD (H-L5a body 초과, H-L5c 극 고정, H-L5g 공통 계단, H-L5h 상수 quadrupole) | 2.3 |
| Local boost 대 global tilt | HOLD (H-L6a 깊이 법칙, H-L6b 단일 global tilt, H-L6c map 수준 aberration) | 2.3 |

## 4. 텐서화 5변수의 역할

x는 부호 있는 precision-form carrier (F, t), Q는 선언된 body의 gauge 범위, F는 방향별 support 비, Pi는 이름 붙은 법칙의 tail, G_F는 깊이 간 transport와 지표 간 transport(공통 벡터) 검정이다.
Q와 F는 극 쌍대(R54-EQ-21)로 연결된다. 어떤 뷰도 likelihood에 정보를 더하지 않는다. 기여는 (i) 프레임·epoch 타입 강제, (ii) 특이 Fisher의 비식별 방향 보고, (iii) transport 법칙 비교다.
F 뷰는 매개변수 공간에 선언된 볼록 body가 있어야 한다. CMB lane에서만 AVAILABLE이고, 저적색편이 lane의 축 스캔은 Pi 아래에 기록한다.

## 5. 한계

선형 이론 body(선택 함수와 지표 간 보정 공분산 없음), survey 라벨 대신 반구 proxy, zero-point nuisance 모형 의존, 사후 선택(forking-path 목록), 이상 E 응답, 현재 shear 사상의 모델 의존, type I 한정. 각 항목의 해소 노드는 `RESEARCH_DAG.json`에 있다.
""" + review_section_ko()


def theory_md(n: dict) -> str:
    eq = "\n".join(f"- **{k}**: `{v}`" for k, v in EQUATIONS.items())

    def pc(key: str) -> str:
        return f"{100 * n[key]:.0f}%"
    return f"""# R54 theory loops ({DATE})

All numbers below are generated from `RESULTS/*.json`. Decisions and review dimensions are in `state/HYPOTHESIS_GRAPH.md`.
The decisions in this file are the ones that stand after the independent review (`INDEPENDENT_REVIEW.json`).

## Equation register

{eq}

## CORE: tensorized five views on a precision-form carrier

A probe contributes a carrier (F, t) in typed coordinates. Independent probes add; nuisance is profiled by a Schur
complement; the null space of F is reported. With a declared body K0 = {{theta^T B^-1 theta <= 1}}:

- **Proposition (polar duality, R54-EQ-21).** For the confidence set Theta_c of R54-EQ-20,
  Q_min = sup_v [-h_Theta(-v)]_+ / h_K0(v) and Q_max = sup_v h_Theta(v) / h_K0(v).
  Proof sketch: p_K0 is the support function of the polar body K0^o = {{v : h_K0(v) <= 1}}, so
  max_Theta p_K0 = max_Theta max_(v in K0^o) v.theta = max_(v in K0^o) h_Theta(v); the minimum follows from the
  separating hyperplane at the touching point of Theta_c and Q_min K0. Checked by exact enumeration in two
  dimensions to 1e-8 and at the touching point in the tests.
- If F is singular, Q_max = +infinity and F_upper = +infinity along unidentified directions. This is a result, not a failure.
- G_F is a GLS test of y_k = tau_k x with the full cross-depth covariance; dof = d(K-1).
- None of the views changes a GLS estimate. The R53 tie with the exact likelihood stands.
- The F view needs a declared convex body in parameter space. It is AVAILABLE on the CMB lane only; the axis scans of the
  low-redshift lanes are template statistics and are recorded under Pi.
- Finite-MC law: for a sample covariance with n = N - 1 degrees of freedom the GLS estimate has true sd / plug-in sd =
  sqrt[n(n-1)/((n-p+k)(n-p+k-1))], which is 1 for a square carrier (p = k), where the Wald statistic follows the Hotelling law.

The five views are a reporting convention (H-C1); no novelty is claimed for them.

Prior work applied: support functions for partially identified sets (econometrics), eigenstructure inference for
symmetric-matrix data (E26), matrix-valued multipole statistics (E28), tensor Minkowski functionals (E27). The last
two motivated the STF invariant layer; they are not used as estimators here.

## Loop L1: low-ell morphology and physical observables

Contract: which linear functionals of the kinematic history does the ell = 2 temperature and polarization measure?
Derivation: at k = 0 the Thomson hierarchy closes on (Theta, Ecal) with collision matrix M (eigenvalues 1, 3/10);
the propagator is exp(-M tau) and gives R54-EQ-03/04. Thomson scattering of an unpolarized quadrupole gives
Q + iU = -(sqrt6/10) sum a^T_2m 2Y_2m per unit depth, so the healpy E tensor has the sign of the T tensor.
Shear dynamics: sigma_dot + 3H sigma = 8 pi G pi with pi = (8/15) rho Theta for free-streaming radiation gives R54-EQ-05;
a collisionless species of mass m carries the stress weight W(mu) of R54-EQ-06 (W = 1 massless, stress -> -2 P beta_ij when non-relativistic).
Prior art: the first-order polarized transfer in a spatially flat anisotropic universe was solved in E46 (see also E48 and E47);
R54-EQ-01 to R54-EQ-04 are a re-derivation in the present conventions.

Results: r_E(perfect fluid) = {n['r_E_pf']:.4f}; K_E peaks at {n['K_E_max']:.4f}; with photon stress s0/Sigma_T = {g3(n['s0_photon'])};
in the two-mode family s0 = c_T Sigma_T + c_E Sigma_E with (c_T, c_E) = ({g3(n['c_T'])}, {g3(n['c_E'])}) for massless neutrinos and
({g3(n['c_T_m'])}, {g3(n['c_E_m'])}) for minimal normal ordering. Initial-state sweep over z_i from {g3(n['sweep_z_lo'])} to {g3(n['sweep_z_hi'])}:
{sweep_text(n)}; s0/Sigma_T spans [{g3(n['s0r_lo'])}, {g3(n['s0r_hi'])}].
Late-time sensitivity (shear confined to z < 0.2): int K_T dN = {g3(n['late_I_T'])} and int K_E dN = {g3(n['late_I_E'])}; a sign-changing history
with Sigma_T = 0 is bounded only through E, at an rms of {g3(n['late_E_rms'])} (diagnostic lane).

Adversarial points recorded: (a) the kernel result is a re-derivation (E46); (b) the stress dependence is established physics in the
magnetic case (E05) and its novelty for shear limits is unverified; (c) the present-shear numbers are illustrations: they move by a factor
of about two between the two neutrino-mass variants and Sigma_T changes sign in the initial-state sweep; (d) the two-mode family has free
initial data, so T and E tensors need not be collinear; (e) late-time anisotropic stress evades the T functional (E44).

Decision: PROMOTE H-L1a (re-derivation), H-L1b (qualitative statement); REJECT H-L1c, H-L1d.

## Loop L2: dipole anomaly

Frame algebra (R52, retained): CMB dipole = beta_MO - beta_RM; counts = c_EB beta_MO; distances respond to the observer
velocity relative to each shell. The owned receipt estimator shows no excess (p = {n['quaia_p']:.2f}, {n['nvss_p']:.2f}; common excess
p = {n['common_p']:.2f}), but its power against a dipole twice the kinematic one is {n['count_power']:.2f} at the 5% level, so the non-detection
decides nothing. The published anomaly (E19) rests on CatWISE-type samples and dedicated estimators; the fair comparison is to
run those estimators on the owned catalogues with a clustering body (R54-EQ-32) and a same-estimator null (R54-L03).

Decision: HOLD H-L2a (underpowered), H-L2b; REOPEN the R52 frame inconsistency (H-L2c).

## Loop L3: beyond-FLRW kinematic quantities

Identifiability by irreducible block and parity at first order (inherited from R52, no new computation): STF2 (sigma) is identified by
the CMB functionals and by low-z quadrupoles; the axial vector (omega) has no column in any owned observable once the reference frame
rotation is free; a constant polar dH dipole (A) is a gauge direction of one distance-indicator sample.
Transport inside type I. Without late-time anisotropic stress the present shear allowed by the CMB functionals is
|s0| <= {g3(n['s0_as'])} (massless two-mode) or {g3(n['s0_as_no'])} (minimal normal ordering), against a CF4 quadrupole of {n['g_quad_pct']:.1f}% of H.
With late-time stress this does not hold: for a shear confined to z < 0.2 the T functional bounds a constant-sign history at
{g3(n['late_T_const'])} and is blind to a sign-changing one, and the E functional bounds its rms at {g3(n['late_E_rms'])}
({g3(n['late_E_rms_z05'])} for z < 0.5, {g3(n['late_E_rms_z2'])} for z < 2), above the CF4 value.
Several distance indicators do not identify A either, but they test whether a dipole is common to them (Loop L5, item 4).

Decision: PROMOTE H-L3a, H-L3b (inherited structural statements) and H-L3d (conditional statement); REJECT H-L3c (unconditional statement).

## Loop L4: anisotropy evaluation and classification

Carrier-level classification is the orbit type of the measured STF tensor under rotations: amplitude, shape
(sqrt6 tr M^3 / (tr M^2)^(3/2) in [-1,1]) and frame, with an axisymmetry statistic. Family-level identification of
Bianchi types needs source-bound transfers beyond type I and stays blocked (AGENTS boundary 1 and 7).
Executed (log estimator, exact body): the constant CF4 quadrupole is {n['g_quad_pct']:.1f}% of H with its principal axis {n['g_quad_axis']:.1f} deg from the
equatorial pole; the axis moves by tens of degrees under the zero-point split, so eigen-axes of a marginal tensor are not reported as directions.
The invariants have no null calibration on an owned carrier yet.

Decision: HOLD H-L4a.

## Loop L5: redshift- and direction-dependent Hubble factor

First pass (R54-L5, superseded for CF4). Model per window: cz = d (H_w + D_w.n + n.q_w.n) on the committed R36 multipoles with the
ideal-sky body R54-EQ-11/12. It gave nulls of {g3(n['dip_p'])} and {g3(n['quad_p'])} and a template axis {n['lock_angle']:.1f} deg from the equatorial
pole (sky fraction {n['lock_frac']:.4f}). The adversarial points recorded against it were: ideal-sky body; working covariance without
calibration terms; mode coupling of a monopole depth trend into survey-aligned multipoles. All three were then tested.

Second pass (R54-L05, catalogue level, executed on the 35970 committed groups).

1. Estimator. With c z = H d and d = D exp(s eps) the weighted regression of c z on d is biased; for homogeneous errors and
   weights ~ 1/d^2 the fitted rate is H exp(+s^2/2) (R54-EQ-35, checked by Monte Carlo in the unit test). With errors that differ
   between surveys the bias is direction dependent. The same-estimator null of the R36 operator shows that the bias carries
   {100*n['eiv_frac_lo']:.0f}-{100*n['eiv_frac_hi']:.0f}% of its pole dipole and, once subtracted, moves the quadrupole null from {g3(n['xl_quad_p'])} to {g3(n['xb_quad_p'])}
   and the pole sky fraction from {g3(n['xl_sky_frac'])} to {g3(n['xb_sky_frac'])}. The replacement is the log-distance ratio eta = ln[H0 d_L(z)/d] (R54-EQ-34),
   linear in the noisy distance modulus, with the exact velocity response g(z) of R54-EQ-33.
2. Body. O diag(g) C_uu diag(g) O^T with the linear velocity correlation tensor (R54-EQ-30/31/37), accumulated over all pairs.
   The pair-sum routine equals the dense 3-vector form to 1e-9 and the ideal-sky harmonic form to 2% on a full shell (unit test).
   Exact/ideal sd ratios on CF4: dipole {n['x_ratio_dip_lo']:.2f}-{n['x_ratio_dip_hi']:.2f}, quadrupole {n['x_ratio_quad_lo']:.2f}-{n['x_ratio_quad_hi']:.2f}.
3. Results by zero-point nuisance model (pooled / method monopoles / method x hemisphere steps). Joint null p:
   {g3(n['g_joint_p'])} / {g3(n['m_joint_p'])} / {g3(n['s_joint_p'])} (pooled with the body doubled: {g3(n['g_joint_p_x2'])}). Calibrated locking tail of the two-parameter axis
   template ({n['x_n_null']} null draws from the exact body): {g3(n['g_tail_sky'])} / {g3(n['m_tail_sky'])} / {g3(n['s_tail_sky'])}. Class under the coded rule:
   {n['x_class']} / {n['x_class_mono']} / {n['x_class_split']}; robust class {n['x_class_robust']}.
   The third model removes the hemisphere direction by construction, so its dipole null is not evidence.
   Window split (pooled): inner windows joint p = {g3(n['wi_joint_p'])}, outer windows {g3(n['wo_joint_p'])}; at z >= 0.055 the sample is {pc('outer_FP_frac')} FP,
   {pc('outer_FP_north_frac')} of it northern, so the outer dipoles compare northern FP with the rest.
   Power of the pole_locked flag for an injected hemisphere step of the observed size: {pc('inj_obs_step_lock')} ({pc('inj_none_lock')} without injection).
4. Indicator transport (a G_F view across distance indicators instead of depths). A physical dipole and a flow are common to all
   indicators; a calibration term of one indicator is not. Per-method hemisphere steps: FP {100*n['st_FP']:.2f}, TF {100*n['st_TF']:.2f}, SN {100*n['st_SN']:.2f},
   OTHER {100*n['st_OTHER']:.2f} (% of H), consistency p = {g3(n['st_cons_p'])}, common step {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}%;
   with white errors the same step would have p = {g3(n['stw_common_p'])}. The common dipole vector of the four families has Wald p = {g3(n['cm_wald_p'])}.
5. Look-elsewhere correction of the step. The sign(dec) split was chosen after the first pass. Scan over {n['sc_n_axes']} split axes with the exact
   body ({n['sc_n_obj']} groups at z < 0.055): single-axis tail {g3(n['st_common_p'])}; tail of the scan maximum {g3(n['sc_tail_scan'])}; the celestial pole ranks
   {n['sc_pole_rank']} of {n['sc_n_axes']} by |z|; under the null the best axis lies within 10 deg of the pole in a fraction {g3(n['sc_null_near_pole'])} of draws.
   The four family estimates share the body: variance of the best single family / variance of the common step = {n['sc_var_ratio']:.2f} (4 if independent).
   The step (z < 0.055) and the window excess (stronger in the outer windows) are different measurements.

Adversarial points that remain: no selection function and no calibration covariance; hemisphere is a proxy for survey; indicators share
a calibration chain; the constant-quadrupole Wald statistic is a posteriori; every entry of the forking-path register below.

Prior art checked in this session: E43 applies a log-distance estimator to CF4 and its constituent catalogues and reports larger
dipoles for TFR and 6dFGS than for SDSS and SN; E09 and E33 find the Tully-Fisher dipole compatible with LCDM flows once radial
freedom is allowed. Equal steps at family level may therefore have different causes, and the common-mode reading stays on HOLD.

Decision: PROMOTE H-L5f; HOLD H-L5a, H-L5c, H-L5g, H-L5h; REJECT H-L5e.

## Loop L6: local boost versus global tilt

Depth laws: observer boost or coherent flow gives D proportional to 1/d; a zero-point or acceleration term is constant;
a global tilt is a constant velocity at every depth including the count-dipole shells; LCDM flows are a zero-mean body
with strong cross-depth correlation. On CF4 with the exact body the pooled fit prefers the constant term (chi2 {n['g_chi2_A']:.1f} against {n['g_chi2_V']:.1f}),
but the preference disappears when method monopoles are marginalised ({n['m_chi2_A']:.1f} against {n['m_chi2_V']:.1f}).
Injections on the real footprint (constant law preferred for an injected step / an injected flow): {pc('inj_step_A')} / {pc('inj_flow_A')} at
{n['inj_step_mag']:.2f} mag and {n['inj_flow']:.0f} km/s, and {pc('inj_obs_step_A')} / {pc('inj_obs_flow_A')} at the observed sizes
({n['inj_obs_step_mag']:.3f} mag, {n['inj_obs_flow']:.0f} km/s); with the method-monopole operator {pc('injm_obs_step_A')} / {pc('injm_obs_flow_A')}.
At the observed sizes the laws are not told apart at the 90% / 10% level written down before that run was read (H-C3 {n['h_c3_decision']}).
Tilt closure (R54-EQ-38): one matter-radiation frame offset at all depths requires V_CF4 = -c beta_excess(counts); the test gives
p = {g3(n['tt_close_p'])} (V only) and {g3(n['tt_close_p_A'])} (constant dipole marginalised), preliminary because the count side has no clustering body
and low power. The velocity term fitted next to the constant term is {n['g_VA_V_amp']:.0f} km/s, {n['g_VA_V_cmb']:.0f} deg from the CMB apex, Wald {g3(n['g_V_after_A'])}/3.
Published anchors for the joint node: E21, E22.

Decision: HOLD H-L6a, H-L6b, H-L6c.

## Forking-path register

Analysis choices that were made, or could have been made, after looking at data. Each entry states what is reported to compensate.

| id | choice | status | what is reported |
|---|---|---|---|
| FP-01 | sign(dec) as the hemisphere-split axis | chosen after the first pass located the pole on the same data | tail of the scan maximum over {n['sc_n_axes']} axes next to the single-axis tail |
| FP-02 | redshift range 0.01-0.055 of the per-family tests | fixed after tabulating coverage by method and hemisphere, before the body was attached | stability over the two halves of the range is a step of R54-L04 |
| FP-03 | decision rule and thresholds of the CF4 class | coded before the exact-body numbers were read, not committed beforehand | not called pre-specified; class per nuisance model and the first-draft rule are both in the result file |
| FP-04 | threshold of the 'removed by split' flag | pole gain after the split is {n['s_pole_gain']:.2f} against the threshold {n['gain_thr']:.2f} | the near miss is stated; the class is reported per model instead of relying on the flag |
| FP-05 | two-parameter axis template and reference axes | inherited from the first pass | null law drawn with the identical grid statistic |
| FP-06 | cut z_i <= 1e10 on the neutrino-decoupling sweep in the report builder | removed after the independent review | the full sweep, including the sign change of Sigma_T |
| FP-07 | constant-quadrupole Wald statistic | a posteriori | H-L5h on HOLD; the 20-dof null is quoted with it |
| FP-08 | injection amplitudes | the first amplitudes were not matched to the data | observed-size injections added; their amplitudes are data-derived and labelled so |
| FP-09 | nuisance model of the locking test | first run on the pooled operator only | three nuisance models; R54-L04 adds four more that are fixed in the contract before they are run |
| FP-10 | primary CMB carrier | fixed by the B-null gate rule before the intervals were computed | no change |
| FP-11 | number of null draws and random streams | raised from 2000 to {n['x_n_null']} draws with one stream per block after the review; seed unchanged | precision only |
| FP-12 | scan grid ({n['sc_n_axes']} axes, minimum 50 objects per family and side) | fixed in the script before the scan was run | no change |
"""


def task_status_lines() -> str:
    return "\n".join(f"  [{node_status(nid)}] {nid}" for nid in LOCAL_ORDER)


def prompt_txt(n: dict) -> str:
    return f"""ROLE
You are the local coding agent for repository cosmosapjw-quantum/htt_base. Work only on branch
{BRANCH} (base {BASE}). Follow AGENTS.md. Claim ceiling is C0.
Setup: git fetch origin && git checkout {BRANCH} && git pull --ff-only

READ FIRST (in this order, all under {REL}/)
1. LOCAL_AGENT_CONTRACT.json   conventions, equations, module API, node specifications
2. RESEARCH_DAG.json           node order, cards, file allowlist, stop rule
3. SELF_AUDIT_PROTOCOL.json    control questions and the audit you run before every commit
4. MUTATION_GATES.json         gates you must keep green and the local gates you must implement
5. PR4_BYPASS_CONTRACT.json    PR4 is never a blocker
6. ADVERSARIAL_BENCHMARK_SPEC.json, THEORY_LOOPS.md, state/*.md, R54_REPORT_KO.md

BEFORE ANY EDIT
- Answer every control question of SELF_AUDIT_PROTOCOL.json from the files. If an answer differs, re-read; do not proceed.
- Run: {TESTS}
  Expected: all pass. Then run: python scripts/r54/build_r54_contract.py mutation-receipt   (every gate must report KILLED).
- Confirm committed_inputs_sha256 of the contract against the working tree.
- Independent diff review: {'one review of the cloud code was interrupted before it reported. Before the first edit, have a reviewer that did not write the code review the files of LOCAL_AGENT_CONTRACT.json:pending_independent_review.scope, record every finding as specified there, and fix critical findings first.' if pending_review_doc()['status'] == 'PENDING_LOCAL' else 'complete (INDEPENDENT_REVIEW.json).'}

WHAT IS ALREADY DONE (do not redo)
- CMB lane: closed-form T and E history kernels (re-derivation of E46, no novelty claim); r_E(perfect fluid) = {n['r_E_pf']:.4f}; the present-shear
  map is model-labelled ({g3(n['s0_pf_TE'])} perfect fluid T+E; {g3(n['s0_as'])} massless stress family; {g3(n['s0_as_no'])} minimal normal ordering) and its
  numbers are illustrations; the T functional does not bound a late-time shear whose sign changes; PR3 B ell=2 null fails
  (p = {g3(n['B_p'])}), so the E lane is DIAGNOSTIC.
- CF4 lane (catalogue level, 35970 committed groups; scripts/r54/run_r54_cf4_exact.py): the R36 linear estimator is biased and is
  replaced by the log-distance estimator (R54-EQ-34); the exact LCDM pair-sum body is cached in RESULTS/R54_L05_COSMIC_COV.npz.
  By zero-point nuisance model (pooled / method monopoles / method x hemisphere steps):
    joint null p   {g3(n['g_joint_p'])} / {g3(n['m_joint_p'])} / {g3(n['s_joint_p'])}
    locking tail   {g3(n['g_tail_sky'])} / {g3(n['m_tail_sky'])} / {g3(n['s_tail_sky'])}
    class          {n['x_class']} / {n['x_class_mono']} / {n['x_class_split']}
  Robust class: {n['x_class_robust']}. State neither "locked to the equatorial pole" nor "not locked"; both were withdrawn.
  Hemisphere step (z < 0.055), consistent between FP, TF, SN, OTHER: {100*n['st_common']:.2f} +- {100*n['st_common_sd']:.2f}% of H; single-axis tail {g3(n['st_common_p'])},
  scan-corrected tail {g3(n['sc_tail_scan'])}; never quote the single-axis tail alone. Its reading as a common mode is on HOLD.
- Counts: the receipt estimator has power {n['count_power']:.2f} against a doubled dipole; its non-detection decides nothing.
- Independent review: INDEPENDENT_REVIEW.json lists every finding and its resolution. Do not re-promote a hypothesis that the review moved to HOLD
  unless the decision_checks of the node that owns it say so.

YOUR TASKS (execute in this order; one node = one commit series; status from the committed outputs)
{task_status_lines()}
  R54-L01  calibrate the T+E estimator on the 300 FFP10 vectors; masked E response
  R54-L04  CF4 survey-resolved zero points from the raw CF4 tables: is the common hemisphere step a survey calibration term?
  R54-L02  PR4 bypass: analytic T covariance, cross-pipeline and cross-experiment E lane
  R54-L03  count-dipole clustering body, same-estimator velocity null, competitor estimators
  R54-L06  joint frame tomography in precision form with five views per irreducible block
  R54-L07  adversarial benchmark, evidence verification, novelty checks
  R54-L08  manuscript decision with an independent reviewer; then stop
Each node's inputs, numbered steps, output schema, acceptance predicates, decision checks, kill criteria and mutation gates are in
LOCAL_AGENT_CONTRACT.json under nodes[]. Implement exactly those steps. Do not add analyses.
"acceptance" entries must hold or the node stops. "decision_checks" entries are data-dependent: evaluate them once, record the
branch taken, and never change a threshold, a carrier, a redshift range or a sample definition after seeing the outcome.

HARD RULES
- Data: use only committed files and files already on {LOCAL}. No downloads. A missing input sets the node to BLOCKED_MISSING_INPUT.
- PR4: no simulations, no dependency. Use the bypass legs.
- Code: only {MOD}/r54_*.py, scripts/r54, tests/r54. Reuse the module API; do not re-implement it.
- Linear algebra: precision form; never regularize a singular matrix; never add a prior that is not a named body.
- Statistics: every tail names its law; no sigma conversions; a single split difference is never a null distribution.
- Forking paths: an axis, a redshift range, a nuisance column or a threshold chosen after looking at data goes into the forking-path register of
  THEORY_LOOPS.md (through the builder) and its tail is reported with the scan or variant correction. A decision that depends on a nuisance model is
  reported per model.
- Frames and units: as in conventions; never retype the rotation matrix; distances in Mpc without h.
- Reports: numbers come only from RESULTS/*.json through `python scripts/r54/build_r54_contract.py build`. Never type a number into a document.
- Language: no phrase from conventions.forbidden_phrases_in_reports.
- Failure: if an acceptance predicate fails twice, write {REL}/BLOCKER_<node>.md with the evidence and stop that node. Do not tune thresholds or carriers.
- Git: commit prefix = card id (PR-R55-LOCAL-CALIBRATION, PR-R56-JOINT-BENCHMARK, PR-R57-MANUSCRIPT-DECISION); push without force; never merge to main.

AFTER EACH NODE
1. {TESTS}
2. implement and run the node's local mutation gates; each named test must fail under its mutation
3. python scripts/r54/build_r54_contract.py build
4. run the SELF_AUDIT_PROTOCOL items A01-A15 and paste the PASS/FAIL table in the commit body
5. move the card in docs/codex_handoff/pr_status.yaml only when every node of the card is complete; then
   python scripts/codex_harness/sync_pr_dag_mirrors.py --write

END-OF-NODE REPORT (exact fields)
node id and status | commands with exit codes | result file and sha256 | acceptance table | mutation receipts | deviations | open risks

STOP CONDITION
R54-L08 ends the programme with BOUNDED_NOTE_EXTENDED or NO_PAPER. Do not open another research loop.
"""


def readme_md() -> str:
    return f"""# R54 tensor frame tomography ({DATE})

Branch `{BRANCH}` on `{BASE}`. Claim ceiling C0. Authority order: `AGENTS.md`, canonical DAG in
`docs/codex_handoff/pr_backlog.yaml`, then this directory.

| file | role |
|---|---|
| `R54_REPORT_KO.md` | referee verdict, executed results, decisions (Korean) |
| `THEORY_LOOPS.md` | equation register, core calculus, six theory loops |
| `RESULTS/R54_L1_TYPE1_TE.json` | CMB T+E type-I history functionals (executed) |
| `RESULTS/R54_L5_LOWZ_FRAMES.json` | first pass on committed R36 multipoles with the ideal-sky body; count-dipole excess (executed; CF4 part superseded) |
| `RESULTS/R54_L05_CF4_EXACT.json` | CF4 at catalogue level: log-distance estimator, exact LCDM body, nulls under three zero-point nuisance models, hemisphere-step scan (executed) |
| `RESULTS/R54_L05_COSMIC_COV.npz` | cached pair-sum covariance O C_uu O^T (linear and damped) with row labels |
| `RESULTS/R54_L05_STEP_SCAN_COV.npz` | cached pair-sum covariance of the per-family hemisphere steps over the split-axis grid |
| `RESEARCH_DAG.json` | cloud and local nodes, cards, order, stop rule |
| `LOCAL_AGENT_CONTRACT.json` | conventions, equations, API, node specifications |
| `MUTATION_GATES.json`, `MUTATION_GATE_RECEIPT.json` | declared gates and proof that they bite |
| `SELF_AUDIT_PROTOCOL.json` | anti-drift audit for the local agent |
| `ADVERSARIAL_BENCHMARK_SPEC.json` | published targets, tolerances, scoring |
| `PR4_BYPASS_CONTRACT.json` | why and how PR4 is not a blocker |
| `HISTORY_AUDIT.json`, `HISTORY_PR_INDEX.json` | inventory, read coverage, reinterpretations |
| `state/` | research state, evidence ledger, hypothesis graph, decision log, negative results |
| `LOCAL_AGENT_RESTART_PROMPT.txt` | prompt for the local agent |
| `INDEPENDENT_REVIEW.json` | independent review record |

Rebuild: `python scripts/r54/run_r54_cmb_type1.py && python scripts/r54/run_r54_lowz_frames.py && python scripts/r54/run_r54_cf4_exact.py && python scripts/r54/build_r54_contract.py build`
(the CF4 run reads the two cached pair sums; on 2 cores a cache miss costs about 12 minutes for the main sum and under 2 minutes for the scan).
Tests: `{TESTS}`.
"""


def build() -> None:
    n = numbers()
    hyps = hypotheses(n)
    jdump(R54 / "RESEARCH_DAG.json", dag_doc(n))
    jdump(R54 / "LOCAL_AGENT_CONTRACT.json", contract_doc(n))
    jdump(R54 / "MUTATION_GATES.json", gates_doc())
    jdump(R54 / "SELF_AUDIT_PROTOCOL.json", self_audit_doc())
    jdump(R54 / "ADVERSARIAL_BENCHMARK_SPEC.json", benchmark_doc(n))
    jdump(R54 / "PR4_BYPASS_CONTRACT.json", pr4_doc(n))
    jdump(R54 / "HISTORY_AUDIT.json", history_doc())
    jdump(R54 / "state/HYPOTHESES.json", {"schema": "htt.r54.hypotheses/1", "hypotheses": hyps, "evidence": EVIDENCE_ROWS, "bound_numbers": n})
    for name, text in state_files(n, hyps).items():
        (R54 / "state" / name).write_text(text, encoding="utf-8")
    (R54 / "R54_REPORT_KO.md").write_text(report_ko(n), encoding="utf-8")
    (R54 / "THEORY_LOOPS.md").write_text(theory_md(n), encoding="utf-8")
    (R54 / "LOCAL_AGENT_RESTART_PROMPT.txt").write_text(prompt_txt(n), encoding="utf-8")
    (R54 / "README.md").write_text(readme_md(), encoding="utf-8")
    print(f"built {REL}: {len(hyps)} hypotheses, {len(local_nodes(n))} local nodes, {len(CLOUD_GATES) + 1} cloud gates")


def mutation_receipt() -> None:
    env = dict(os.environ, PYTHONPATH="htt/src:htt:.")
    rows = []
    for gid, rel, old, new, test, meaning in implemented_gates():
        path = ROOT / rel
        original = path.read_text(encoding="utf-8")
        if original.count(old) != 1:
            rows.append({"id": gid, "status": "INVALID_GATE", "reason": f"pattern occurs {original.count(old)} times"})
            continue
        try:
            path.write_text(original.replace(old, new), encoding="utf-8")
            run = subprocess.run([sys.executable, "-m", "pytest", test, "-q", "-x", "-p", "no:cacheprovider"], cwd=ROOT, env=env, capture_output=True, text=True)
        finally:
            path.write_text(original, encoding="utf-8")
        rows.append({"id": gid, "file": rel, "test": test, "meaning": meaning, "pytest_exit_code": run.returncode,
                     "status": "KILLED" if run.returncode == 1 else "SURVIVED_OR_ERROR"})
        print(gid, rows[-1]["status"])
    clean = subprocess.run([sys.executable, "-m", "pytest", "tests/r54/test_r54_modules.py", "tests/r54/test_r54_conventions.py", "tests/r54/test_r54_calibration.py",
                            "tests/r54/test_r54_survey.py", "tests/r54/test_r54_counts.py", "tests/r54/test_r54_pr4_bypass.py",
                            "-q", "-p", "no:cacheprovider"],
                           cwd=ROOT, env=env, capture_output=True, text=True)
    jdump(R54 / "MUTATION_GATE_RECEIPT.json", {"schema": "htt.r54.mutation_receipt/1", "date": DATE, "unmutated_suite_exit_code": clean.returncode,
                                               "sources_sha256": {rel: sha(ROOT / rel) for rel in RECEIPT_SOURCES},
                                               "all_killed": all(r["status"] == "KILLED" for r in rows) and clean.returncode == 0, "gates": rows})
    if clean.returncode != 0 or not all(r["status"] == "KILLED" for r in rows):
        raise SystemExit("mutation receipt: at least one gate survived or the clean suite failed")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("command", choices=("build", "mutation-receipt"))
    args = ap.parse_args()
    build() if args.command == "build" else mutation_receipt()


if __name__ == "__main__":
    main()

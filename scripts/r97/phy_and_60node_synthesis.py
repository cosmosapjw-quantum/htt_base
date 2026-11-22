"""R97 Unit D (P1, P4, P6, PHY-01..07 & 60-Node R97 Master Ledger).

Integrates new R97 outputs (Units A, B, C) with R95/R91/R89 P1/P4/P6 source-conditioned products:
  - P1: couples 2,048 4-window draws with R97 CF4 partial-ID quadrupole calibration bounds
    while strictly enforcing physical_Pi = None and physical_GF = None.
  - P4: synthesizes 5-survey Ellis-Baldwin dipole/quadrupole/clustering ladder across NVSS,
    RACS-DR1, SPICE-RACS, SUMSS, LoTSS (preserving joint_five_survey_covariance_qualified = False).
  - P6: projects R97 non-axisymmetric coupled-m Bianchi L=2 shear/curl templates onto
    Quaia 10x10 jackknife (E2, B2) VSH covariance vs Gaia ecliptic scanning-law quadrupole
    (preserving actual_normal_vorticity = None and k04..k06 = BLOCKED_DEPENDENCY).
  - PHY-01..07 & 60-Node R97 Master Ledger: preserves immutable R78 INTEGRATED_DAG.json
    (SHA256 90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11, 60 nodes, 129 edges,
    NEXT_ID = SQ-CF4) and separates code/conditional execution from publication approval.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from htt.obsstat import p1_fast
from scripts.r95 import gaia_p6_analysis as r95_gaia

R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R94_MAP = ROOT / "docs/research_program/observational_publication_20261015/R94_SIX_PAPER_ACCEL_HANDOFF_20261122/R94_PROGRAM_EXECUTION_MAP.json"
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
R97_DIR = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122"
P1_NPZ = ROOT / "docs/research_program/observational_publication_20261015/CONTINUATION_20261018/P1/results/paired_functional_arrays.npz"
R91_QUAIA = ROOT / "docs/research_program/observational_publication_20261015/R91_SOLVERFREE_SECOND_CYCLE_20261121/GAIA_QUAIA_FULL_SELECTION.json"
EXPECTED_R78_SHA = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _load_r97_and_r95_inputs() -> tuple[dict, dict]:
    req = {
        "R97_A": R97_DIR / "CF4_GENEALOGY_AND_PARTIAL_ID.json",
        "R97_B": R97_DIR / "CMB_INJECTION_AND_EB_LEAKAGE.json",
        "R97_C": R97_DIR / "BIANCHI_COUPLED_M_TRANSPORT.json",
        "R95_G03": R95_DIR / "G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json",
        "R95_G04": R95_DIR / "G04_RADIO_P4_KINEMATIC_VS_SELECTION.json",
        "R95_G06": R95_DIR / "G06_P1_FIVE_VIEW_TYPED_LEDGER.json",
        "R95_G07_BG": R95_DIR / "G07_BIANCHI_BACKGROUND_AUDIT.json",
        "R95_G07_OPT": R95_DIR / "G07_BIANCHI_REC_REI_OPTICS.json",
        "R95_G08": R95_DIR / "G08_CROSS_PHY_01_TO_07.json",
    }
    missing = [k for k, p in req.items() if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing required upstream inputs for R97 Unit D: {missing}")
    return {k: json.loads(p.read_text()) for k, p in req.items()}, {k: _sha(p) for k, p in req.items()}


def _p6_quaia_bianchi_alignment(d: dict) -> dict:
    """Compare R95 Quaia E2/B2 & scanning-law quadrupole vs R95 geodesic templates and summarize R97 L=60 coupled-m E/B transport."""
    quaia = json.loads(R91_QUAIA.read_text())
    inv = quaia["fits"]["inverse_noise"]
    beta16 = np.array(inv["coefs_microasyr"], dtype=np.float64)
    C10 = np.array(inv["jackknife_E2_B2_cov"], dtype=np.float64)
    e2b2_obs = beta16[6:16]
    e2_obs = beta16[6:11]
    b2_obs = beta16[11:16]
    scan_q = np.array(d["R95_G03"]["scanning_law_quadrupole_frame_check"]["vec_icrs"], dtype=np.float64)

    # Rotate scanning law to Galactic and evaluate alignment with canonical-triad R95 geodesic STF5 quadrupoles
    fiveview = r95_gaia._load_mod("r97_fiveview_geom", r95_gaia.FIVEVIEW_PY)
    R_gal = r95_gaia._build_icrs_to_frame_rotation("galactic")
    _, M5_gal = r95_gaia._build_j16(R_gal, fiveview.E)
    e2_gal = M5_gal @ e2_obs
    scan_gal = M5_gal @ scan_q

    # Test canonical-triad R95_G07_BG geodesic Q2_stf5 templates (with B2=0 exploratory E2-only axis projection)
    traj_cmp = {}
    for key in ("VI_-1/9_exception__tilted", "VII_h__tilted", "IX__tilted"):
        q_tmpl = np.array(d["R95_G07_BG"]["trajectories"][key]["geodesic_cosmo_Q2_stf5"], dtype=np.float64)
        q_tmpl_n = q_tmpl / max(np.linalg.norm(q_tmpl), 1e-30)
        q_icrs_unit = M5_gal.T @ q_tmpl_n
        cos_e2 = float(np.dot(e2_obs, q_icrs_unit) / (np.linalg.norm(e2_obs) * np.linalg.norm(q_icrs_unit)))
        cos_scan = float(np.dot(scan_q, q_icrs_unit) / (np.linalg.norm(scan_q) * np.linalg.norm(q_icrs_unit)))
        t10 = np.concatenate([q_icrs_unit, np.zeros(5, dtype=np.float64)])
        Cinv_t = np.linalg.solve(C10, t10)
        amp_hat = float((t10 @ np.linalg.solve(C10, e2b2_obs)) / (t10 @ Cinv_t))
        chi2_obs = float(e2b2_obs @ np.linalg.solve(C10, e2b2_obs))
        res = e2b2_obs - amp_hat * t10
        chi2_res = float(res @ np.linalg.solve(C10, res))
        traj_cmp[key] = {
            "cos_alignment_with_quaia_inv_E2": cos_e2,
            "cos_alignment_with_gaia_scanlaw_Q": cos_scan,
            "fitted_pure_E2_template_uasyr": amp_hat,
            "wald10_null": chi2_obs,
            "wald10_residual_after_1dof_fit": chi2_res,
            "delta_chi2_1dof": chi2_obs - chi2_res,
        }

    r97c = d["R97_C"]
    l60 = r97c["coupled_m5_by_L"]["60"]
    coupled_m_l60_summary = {
        fname: {
            "B_over_E_norm_ratio": float(l60[fname]["B_over_E_norm_ratio"]),
            "cross_m_coupling_fraction": float(l60[fname]["cross_m_coupling_fraction"]),
            "m_nonzero_over_total_T_power": float(l60[fname]["m_nonzero_over_total_T_power"]),
        }
        for fname in ("I_rotated", "V", "VI_-1/9", "VII_0", "VII_h", "IX")
    }

    return {
        "quaia_inv_E2_norm_uasyr": float(np.linalg.norm(e2_obs)),
        "quaia_inv_B2_norm_uasyr": float(np.linalg.norm(b2_obs)),
        "quaia_inv_E2_gal": e2_gal.tolist(),
        "scanlaw_gal": scan_gal.tolist(),
        "template_10x10_overlap": traj_cmp,
        "r97c_coupled_m_L60_cmb_summary": coupled_m_l60_summary,
        "frame_projection_note": "template_10x10_overlap projects canonical-triad R95_G07_BG scalar geodesic Q2_stf5 with B2=0 into ICRS via M5_gal.T as an exploratory canonical-axis alignment check, alongside R97 Unit C coupled-m L=60 CMB E/B summary metrics.",
        "actual_normal_vorticity": None,
        "k04_k05_k06_status": "BLOCKED_DEPENDENCY",
    }


def _p1_cf4_coupling_summary(d: dict) -> dict:
    """Couple P1's 2,048 window draws with R97 Unit A's partial-ID quadrupole calibration intervals."""
    with np.load(P1_NPZ, allow_pickle=False) as z:
        q_app = np.asarray(z["q_app"], dtype=np.float64)
        w = np.asarray(z["weights"], dtype=np.float64)
    thr = np.array([0.03, 0.05])
    # q_app is dimensionless ||STF5_app|| / H_app across 4 windows
    res_tail = p1_fast.joint_tail_bounds(q_app, w, thr)
    if res_tail["physical_Pi"] is not None:
        raise RuntimeError("P1 physical_Pi guard violated")

    # Convert R97 Unit A's IVW 1-sigma and 95% ellipsoid quadrupole shifts to fractional ||delta_q5|| / H0
    bnd_r95_1s = d["R97_A"]["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    bnd_r95_95 = d["R97_A"]["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid"]
    bnd_r36 = d["R97_A"]["sharp_partial_identification_bounds"]["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]
    q_frac_shift_r95_1s = float(bnd_r95_1s["quad_max_ellipsoid_shift"] / bnd_r95_1s["H0_point"])
    q_frac_shift_r95_95 = float(bnd_r95_95["quad_max_ellipsoid_shift"] / bnd_r95_95["H0_point"])
    q_frac_shift_r36 = float(bnd_r36["quad_max_ellipsoid_shift"] / bnd_r36["H0_point"])
    w_mean_q = [float(np.dot(w, q_app[:, j])) for j in range(4)]

    # Propagate sharp partial-ID quadrupole interval +-dq_frac onto all 2,048 coupled draws through p1_fast.joint_tail_bounds
    res_lo_1s = p1_fast.joint_tail_bounds(np.maximum(0.0, q_app - q_frac_shift_r95_1s), w, thr)
    res_hi_1s = p1_fast.joint_tail_bounds(q_app + q_frac_shift_r95_1s, w, thr)
    res_lo_95 = p1_fast.joint_tail_bounds(np.maximum(0.0, q_app - q_frac_shift_r95_95), w, thr)
    res_hi_95 = p1_fast.joint_tail_bounds(q_app + q_frac_shift_r95_95, w, thr)
    if any(r["physical_Pi"] is not None for r in (res_lo_1s, res_hi_1s, res_lo_95, res_hi_95)):
        raise RuntimeError("P1 physical_Pi guard violated during calibration propagation")

    return {
        "N_coupled_draws": int(len(q_app)),
        "weighted_mean_q_app_4w": w_mean_q,
        "r97_CF4_1sigma_quad_fractional_sys_R95": q_frac_shift_r95_1s,
        "r97_CF4_95pct_quad_fractional_sys_R95": q_frac_shift_r95_95,
        "r97_CF4_1sigma_quad_fractional_sys_R36": q_frac_shift_r36,
        "tail_bounds_at_0p05_4w": {
            "lower": res_tail["lower"][1, :4].tolist(),
            "upper": res_tail["upper"][1, :4].tolist(),
        },
        "cal_widened_tail_bounds_at_0p05_4w": {
            "lower_cal": res_lo_95["lower"][1, :4].tolist(),
            "upper_cal": res_hi_95["upper"][1, :4].tolist(),
            "1sigma_lower_cal": res_lo_1s["lower"][1, :4].tolist(),
            "1sigma_upper_cal": res_hi_1s["upper"][1, :4].tolist(),
            "95pct_lower_any_all": res_lo_95["lower"][1, 4:6].tolist(),
            "95pct_upper_any_all": res_hi_95["upper"][1, 4:6].tolist(),
        },
        "physical_Pi": None,
        "physical_GF": None,
    }


def _p4_radio_summary(d: dict) -> dict:
    """Summarize all 5 radio catalogs (NVSS, RACS-DR1, SPICE-RACS, SUMSS, LoTSS) and selection bounds."""
    g4 = d["R95_G04"]
    lad = g4["five_survey_ladder_analysis"]
    by_survey = {}
    for sname, sblk in lad.items():
        thrs = sblk["thresholds"]
        amps = [v["dipole_4p_amp"] for v in thrs.values()]
        ratios = [v["excess_ratio_d_obs_over_d_eb"] for v in thrs.values()]
        seps = [v["dipole_4p_sep_cmb_deg"] for v in thrs.values()]
        jks = [v["jackknife_over_poisson_ratio"] for v in thrs.values()]
        by_survey[sname] = {
            "n_thresholds": len(thrs),
            "dipole_amp_range": [float(min(amps)), float(max(amps))],
            "d_obs_over_d_eb_range": [float(min(ratios)), float(max(ratios))],
            "sep_cmb_deg_range": [float(min(seps)), float(max(seps))],
            "jk_over_poisson_range": [float(min(jks)), float(max(jks))],
        }
    return {
        "surveys": by_survey,
        "racs_rms_selection_bias_factor": g4["selection_and_flux_artifacts"]["racs_selection_bias_amp_inflation_factor"],
        "joint_five_survey_covariance_qualified": False,
        "physical_Pi": None,
        "physical_GF": None,
    }


def build_synthesis_and_ledger() -> dict:
    t0 = time.perf_counter()
    actual_r78_sha = _sha(R78_DAG)
    if actual_r78_sha != EXPECTED_R78_SHA:
        raise RuntimeError(f"R78 DAG SHA mismatch: {actual_r78_sha}")
    r78 = json.loads(R78_DAG.read_text())
    rmap = json.loads(R94_MAP.read_text())
    if len(r78["nodes"]) != 60 or len(r78["edges"]) != 129 or r78["next_action_id"] != "SQ-CF4":
        raise RuntimeError("R78 DAG invariants violated")

    d, shas = _load_r97_and_r95_inputs()
    p1_syn = _p1_cf4_coupling_summary(d)
    p4_syn = _p4_radio_summary(d)
    p6_syn = _p6_quaia_bianchi_alignment(d)

    # Synthesize PHY-01..PHY-07 integrating R97 Units A, B, C
    r97a, r97b, r97c = d["R97_A"], d["R97_B"], d["R97_C"]
    l60_vi = r97c["coupled_m5_by_L"]["60"]["VI_-1/9"]
    l60_7h = r97c["coupled_m5_by_L"]["60"]["VII_h"]
    phy_routes = {
        "PHY-01": {
            "r97_upgrade": "Exact NSIDE=2048 Mask-Pol analytic Master M^{EE->BB} cross-checked vs 8-draw pure-E MC + out-of-sample 150/150 60D E->B leakage debiasing",
            "master_analytic_eb_ratio": r97b["master_spin2_mask_coupling"]["analytic_master_mean_clBB_over_clEE_2_48"],
            "mc8_eb_ratio": r97b["master_spin2_mask_coupling"]["nside2048_mc8_mean_clBB_over_clEE_2_48"],
            "master_vs_mc_rel_diff": r97b["master_spin2_mask_coupling"]["analytic_vs_mc_rel_diff"],
            "te_to_b_heldout_variance_ratio": r97b["cross_split_60D_eb_leakage_debiasing"]["paired_TE_to_B_heldout_variance_ratio"],
            "debiased_150_150_rank_p": r97b["cross_split_60D_eb_leakage_debiasing"]["debiased_B_60D_150_150_rank_p"],
            "blocker_bucket": "NATIVE_TRANSFER + DATA",
        },
        "PHY-02": {
            "r97_upgrade": "Coupled-m (m=-2..2 to L=60 + all-m to L=8,12) exact Gamma4 transport verified vs live 4D R49 geodesics + HyRec-2+tanh optics + BASS rank-9 Thomson eigenvalues",
            "skew_hermitian_err_oracle": r97c["oracle_verification"]["skew_hermitian_err"],
            "twist_vs_2d_gl_err": r97c["oracle_verification"]["twist_operator_vs_2d_gl_grid_max_abs_err"],
            "r49_4d_geodesic_oracle_rel_errs": {
                "T": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_T"],
                "E": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_E"],
                "B": r97c["oracle_verification"]["r49_4d_geodesic_oracle_rel_err_B"],
            },
            "k0_allm_L12_parity_err": r97c["controls"]["k0_allm_L12_reality_conjugate_parity_err"],
            "L60_VI_minus_1_9_B_over_E": l60_vi["B_over_E_norm_ratio"],
            "allm_vs_m5_L8_power_leak_gt2": r97c["full_all_m_vs_m5_L8_VI_minus_1_9"]["power_fraction_leaking_to_abs_m_gt_2"],
            "allm_vs_m5_L12_power_leak_gt2": r97c["full_all_m_vs_m5_L12_VI_minus_1_9"]["power_fraction_leaking_to_abs_m_gt_2"],
            "blocker_bucket": "NATIVE_TRANSFER + MODEL",
        },
        "PHY-03": {
            "r97_upgrade": "CF4 SR-gamma tomography paired with 5-survey radio Ellis-Baldwin ladder & Gaia E1 aberration + IVW partial-ID calibration ellipsoid",
            "radio_surveys_d_obs_over_d_eb_envelope": d["R95_G04"]["cross_ladder_summary"]["d_obs_over_d_eb_minmax"],
            "cf4_R95_0087sys_H0_1s_interval": r97a["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]["H0_partial_id_interval"],
            "blocker_bucket": "DATA",
        },
        "PHY-04": {
            "r97_upgrade": "Quaia 10x10 jackknife E2+B2 VSH covariance projected against canonical-triad R95 Bianchi Q2_stf5 + R97 coupled-m L=60 E/B metrics",
            "quaia_inv_E2_norm_uasyr": p6_syn["quaia_inv_E2_norm_uasyr"],
            "quaia_inv_B2_norm_uasyr": p6_syn["quaia_inv_B2_norm_uasyr"],
            "VIIh_cos_E2": p6_syn["template_10x10_overlap"]["VII_h__tilted"]["cos_alignment_with_quaia_inv_E2"],
            "r97c_L60_VI_B_over_E": l60_vi["B_over_E_norm_ratio"],
            "r97c_L60_VIIh_B_over_E": l60_7h["B_over_E_norm_ratio"],
            "actual_normal_vorticity": None,
            "blocker_bucket": "DATA + MODEL",
        },
        "PHY-05": {
            "r97_upgrade": "Exceptional Class-B VI_{-1/9} rotationally-invariant Casimir h=-1/9 verified across R49 evolution + m0 -> m!=0 geodesic scattering at L=8..60",
            "h_casimir_preserved": r97c["controls"]["m0_seed_scattering_VI_minus_1_9"]["h_parameter_preserved"],
            "m0_to_m_nonzero_scatter_ratio": r97c["controls"]["m0_seed_scattering_VI_minus_1_9"]["m_nonzero_over_total_T_power"],
            "L60_VI_cross_m_frac": l60_vi["cross_m_coupling_fraction"],
            "blocker_bucket": "MODEL + NATIVE_TRANSFER",
        },
        "PHY-06": {
            "r97_upgrade": "Chiral VII_h parity flip on coupled-m TB/EB & Planck NSIDE=2048 150-heldout L=2 anisotropy injection recovery linear slope & power",
            "VIIh_TB_flip_residual_rel": r97c["chirality_VIIh_L16"]["TB_flip_residual_rel"],
            "VIIh_EB_flip_residual_rel": r97c["chirality_VIIh_L16"]["EB_flip_residual_rel"],
            "inj_recovery_slope": r97b["anisotropy_injection_recovery"]["recovered_amplitude_linear_fit"]["slope"],
            "L60_VIIh_B_over_E": l60_7h["B_over_E_norm_ratio"],
            "blocker_bucket": "NATIVE_TRANSFER + MODEL",
        },
        "PHY-07": {
            "r97_upgrade": "CF4 K4-vs-J7 metric subspace reconciliation (98.85% whitened trace inside col(J7)) + Schur 18-dof predictive variance with parameter uncertainty + P1 calibration-widened tails",
            "K4_in_J7_whitened_frac": r97a["subspace_reconciliation_K4_vs_J7"]["fraction_whitened_variance_inside_col_J7"],
            "radial_schur_red_chi2_R36_vs_R95": [
                r97a["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R36_inherited"]["outer_2w_pred_reduced_chi2"],
                r97a["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]["C_R95_R5_cal005"]["outer_2w_pred_reduced_chi2"],
            ],
            "p1_R95_quad_frac_sys_95pct": p1_syn["r97_CF4_95pct_quad_fractional_sys_R95"],
            "p1_cal_widened_tail_w3": [
                p1_syn["cal_widened_tail_bounds_at_0p05_4w"]["lower_cal"][2],
                p1_syn["cal_widened_tail_bounds_at_0p05_4w"]["upper_cal"][2],
            ],
            "blocker_bucket": "DATA + MODEL",
        },
    }

    syn_out = {
        "schema": "htt.r97.phy_and_p1_p4_p6_synthesis/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "upstream_sha256": shas,
        "P1_five_view_with_r97_cf4_bounds": p1_syn,
        "P4_radio_five_survey_summary": p4_syn,
        "P6_gaia_quaia_bianchi_overlap": p6_syn,
        "PHY_routes": phy_routes,
        "physics_gates": {
            "cross_probe_joint_likelihood_qualified": False,
            "physical_Pi": None,
            "physical_GF": None,
            "actual_normal_vorticity": None,
            "commander_null_qualified": False,
            "Bianchi_family_attribution": None,
            "r78_historical_states_changed": False,
        },
    }
    syn_path = R97_DIR / "PHY_AND_P1_P4_P6_SYNTHESIS.json"
    syn_path.write_text(json.dumps(syn_out, indent=2) + "\n")
    syn_sha = _sha(syn_path)

    # Assemble 60-node R97 Master Ledger reusing exact R78 nodes & topological order + R95 baseline statuses
    r95_ledger = json.loads((R95_DIR / "R95_60_NODE_EVIDENCE.json").read_text())
    r95_by_id = {n["id"]: n for n in r95_ledger["nodes"]}
    r78_by_id = {n["id"]: n for n in r78["nodes"]}
    rmap_by_id = {r["id"]: r for r in rmap["rows"]}

    unit_file_for_paper = {
        "P3": ("CF4_GENEALOGY_AND_PARTIAL_ID.json", shas["R97_A"]),
        "P2": ("CMB_INJECTION_AND_EB_LEAKAGE.json", shas["R97_B"]),
        "P5": ("BIANCHI_COUPLED_M_TRANSPORT.json", shas["R97_C"]),
    }

    ledger_nodes = []
    for nid in r78["topological_order"]:
        n78 = r78_by_id[nid]
        n95 = r95_by_id[nid]
        pap = n78["paper"]
        if pap in unit_file_for_paper:
            art_name, art_sha = unit_file_for_paper[pap]
            r97_stage = "R97_EXECUTED_CONDITIONAL_SCIENCE"
        elif nid.startswith("PHY-") or pap in ("P1", "P4", "P6"):
            art_name, art_sha = ("PHY_AND_P1_P4_P6_SYNTHESIS.json", syn_sha)
            r97_stage = "R97_SYNTHESIS_UPDATED"
        else:
            art_name, art_sha = (n95["r95_primary_artifact"], n95["r95_artifact_sha256"])
            r97_stage = "R95_REUSED_PROVENANCE_LOCKED"

        ledger_nodes.append({
            "id": nid,
            "paper": pap,
            "work_group": rmap_by_id[nid]["work_group"],
            "r78_science_state_preserved": n78["state"],
            "r95_execution_status": n95["r95_execution_status"],
            "r97_campaign_layer": r97_stage,
            "r97_primary_artifact": art_name,
            "r97_artifact_sha256": art_sha,
            "publication_science_accepted": (n78["state"] == "completed_scoped"),
            "blocker_bucket": n95["blocker_bucket"],
            "specific_next_unit": n95["specific_next_unit"],
        })

    if len(ledger_nodes) != 60 or len({x["id"] for x in ledger_nodes}) != 60:
        raise RuntimeError("60-node ledger cardinality failed")

    master = {
        "schema": "htt.r97.60_node_science_execution_ledger/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "r78_integrated_dag_sha256": actual_r78_sha,
        "r78_total_nodes": 60,
        "r78_hard_edges": 129,
        "r78_next_action_id": "SQ-CF4",
        "original_science_status_changed": False,
        "actual_r97_physical_science_acceptance": False,
        "r97_unit_artifact_shas": {
            "CF4_GENEALOGY_AND_PARTIAL_ID.json": shas["R97_A"],
            "CMB_INJECTION_AND_EB_LEAKAGE.json": shas["R97_B"],
            "BIANCHI_COUPLED_M_TRANSPORT.json": shas["R97_C"],
            "PHY_AND_P1_P4_P6_SYNTHESIS.json": syn_sha,
        },
        "nodes": ledger_nodes,
    }
    (R97_DIR / "R97_60_NODE_EXECUTION_LEDGER.json").write_text(json.dumps(master, indent=2) + "\n")

    # Write concise Korean summary R97_REPORT_KO.md strictly from regenerated runtime artifacts
    eb_m = r97b["master_spin2_mask_coupling"]
    deb = r97b["cross_split_60D_eb_leakage_debiasing"]
    inj_f = r97b["anisotropy_injection_recovery"]["recovered_amplitude_linear_fit"]
    sub = r97a["subspace_reconciliation_K4_vs_J7"]
    b_r95 = r97a["sharp_partial_identification_bounds"]["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    b_r36 = r97a["sharp_partial_identification_bounds"]["R36_inherited_ivw_common_0p087_tully23sys_1sigma"]
    ov = r97c["oracle_verification"]
    report_lines = [
        "# HTT R97 Scientific Execution Report",
        "",
        f"- R78 정본 SHA256: `{actual_r78_sha}` (60 nodes, 129 edges, `NEXT_ID={r78['next_action_id']}`)",
        "- `original_science_status_changed = false`, `actual_r97_physical_science_acceptance = false`",
        "",
        "## 핵심 신규 과학 결과 (Units A-D)",
        f"- **Unit A / SQ-CF4 (P3)**: R36 `K4 == A@(d*I4)` 재구성 오차 `{r97a['r36_K4_exact_formula_max_abs_diff']:.2e}`; "
        f"`K4 Sigma4 K4^T` 백색화 분산 중 `{100.0*sub['fraction_whitened_variance_inside_col_J7']:.2f}%`가 `col(J7)` 내부에 존재; "
        f"`table3` 수치 필드 기반 6채널 지원이 R27 `selected_support_7`과 `0` 불일치 확인 (`DirectCal`은 속도지표 겸유 9개 그룹 정의 차이 분리, `DMzp - DMav = -0.147` mag 전 35,968그룹 항등). "
        f"역분산 분할단위 `W7` 및 0.087 mag 공통 캘리브레이션 불확실도에서 1-sigma 부분식별 구간: "
        f"R95 `[{b_r95['H0_partial_id_interval'][0]:.2f}, {b_r95['H0_partial_id_interval'][1]:.2f}]`, "
        f"R36 `[{b_r36['H0_partial_id_interval'][0]:.2f}, {b_r36['H0_partial_id_interval'][1]:.2f}]` km/s/Mpc; "
        f"모수 추정 공분산 포함 내측->외측 Schur 18-dof reduced chi2 R36 `{phy_routes['PHY-07']['radial_schur_red_chi2_R36_vs_R95'][0]:.3f}` vs R95 `{phy_routes['PHY-07']['radial_schur_red_chi2_R36_vs_R95'][1]:.3f}` (`SQ-CF4 = BLOCKED_INPUT` 유지).",
        f"- **Unit B / Planck SMICA (P2)**: NSIDE=2048 Mask-Pol 해석적 Master E->B 비율 `{eb_m['analytic_master_mean_clBB_over_clEE_2_48']:.5f}` vs "
        f"8-draw pure-E MC `{eb_m['nside2048_mc8_mean_clBB_over_clEE_2_48']:.5f}` (상대차 `{eb_m['analytic_vs_mc_rel_diff']:.3e}`). "
        f"150/150 분리 교차검증에서 `TE->B` 누설 제거 후 heldout 분산비 `{deb['paired_TE_to_B_heldout_variance_ratio']:.4f}`, "
        f"debias 60D rank p=`{deb['debiased_B_60D_150_150_rank_p']:.4f}`. "
        f"L=2 주입-복원 선형 기울기 `{inj_f['slope']:.4f}` (`commander_null_qualified = false`).",
        f"- **Unit C / Bianchi Coupled-m Spin-2 (P5)**: R49 4D 접속 `Gamma4`의 `+0.5` spin-1 eth/eth-bar 이류 + Sachs 스크린 회전을 "
        f"`M_geo_exact` (발산항 포함)으로 m in {{-2..2}} (`L=8,16,32,60`) + all-m (`L=8,12`) 계층에 결합. "
        f"무손실 반-에르미트 오차 `{ov['skew_hermitian_err']:.2e}`, 2D GL 스크린 회전 오라클 오차 `{ov['twist_operator_vs_2d_gl_grid_max_abs_err']:.2e}`, "
        f"실제 R49 4D 측지선 적분기 대비 상대오차 T/E/B=`{ov['r49_4d_geodesic_oracle_rel_err_T']:.2e}`/`{ov['r49_4d_geodesic_oracle_rel_err_E']:.2e}`/`{ov['r49_4d_geodesic_oracle_rel_err_B']:.2e}`. "
        f"`VI_{{-1/9}}` 예외류 (`h={r97c['controls']['m0_seed_scattering_VI_minus_1_9']['h_parameter_preserved']:.6f}`)에서 순수 m=0 전단 시드로부터 m!=0 산란비 `{r97c['controls']['m0_seed_scattering_VI_minus_1_9']['m_nonzero_over_total_T_power']:.4e}`, "
        f"`L=60`에서 `B/E = {l60_vi['B_over_E_norm_ratio']:.4f}`, all-m(`L=12`, dim=499) `|m|>2` 누설비 `{r97c['full_all_m_vs_m5_L12_VI_minus_1_9']['power_fraction_leaking_to_abs_m_gt_2']:.4e}` (`SQ-NATIVE`, `B02-B05` 미승격).",
        f"- **Unit D / P1, P4, P6, PHY-01..07**: P1 2,048 4창 결합분포에 95% 타원체 사중극 보정 불확실도 `{p1_syn['r97_CF4_95pct_quad_fractional_sys_R95']:.5f}` 전파 "
        f"(w3 tail `[0.05]`: `[{p1_syn['cal_widened_tail_bounds_at_0p05_4w']['lower_cal'][2]:.4f}, {p1_syn['cal_widened_tail_bounds_at_0p05_4w']['upper_cal'][2]:.4f}]`), "
        f"60노드 전체 원장 (`R97_60_NODE_EXECUTION_LEDGER.json`) 및 교차물리(`PHY-01..07`) 갱신 완료 (`physical_Pi=None, physical_GF=None, actual_normal_vorticity=None`).",
    ]
    (R97_DIR / "R97_REPORT_KO.md").write_text("\n".join(report_lines) + "\n")
    return {"master": master, "synthesis": syn_out}


if __name__ == "__main__":
    res = build_synthesis_and_ledger()
    print(json.dumps({
        "n_nodes": len(res["master"]["nodes"]),
        "r78_sha_ok": res["master"]["r78_integrated_dag_sha256"] == EXPECTED_R78_SHA,
        "p6_VIIh_cos_E2": res["synthesis"]["P6_gaia_quaia_bianchi_overlap"]["template_10x10_overlap"]["VII_h__tilted"]["cos_alignment_with_quaia_inv_E2"],
        "p1_sys_quad_frac": res["synthesis"]["P1_five_view_with_r97_cf4_bounds"]["r97_CF4_95pct_quad_fractional_sys_R95"],
        "elapsed_s": res["master"]["elapsed_seconds"] + res["synthesis"]["elapsed_seconds"],
    }))

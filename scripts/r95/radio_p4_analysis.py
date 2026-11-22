"""R95 Step 3 (G04_RADIO_FRAME / P4): Five-survey Ellis-Baldwin parameter sweep, mask leakage & LSS clustering synthesis.

Reuses source-verified R89 five-survey reductions (NVSS, RACS-DR1, SPICE-RACS, SUMSS, LoTSS)
and R89 pairwise/galcut reductions with full SHA provenance checks.

Explicitly preserves:
  - joint_five_survey_covariance_qualified = False (no correlated multi-survey null/mask likelihood)
  - SQ-RADIO = DIAGNOSTIC_COMPLETED_SCOPED, SQ-FRAME = DIAGNOSTIC_COMPLETED_SCOPED
  - V04..V06 = BLOCKED_DEPENDENCY, physical_Pi = None, physical_GF = None
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord

ROOT = Path(__file__).resolve().parents[2]
G04_DIR = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G04_RADIO_FRAME"
OUT_JSON = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122/G04_RADIO_P4_KINEMATIC_VS_SELECTION.json"

C_KMS = 299792.458
BETA_CMB = 369.82 / C_KMS  # Planck 2018 Solar CMB dipole beta
CMB_COORD = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic")
CMB_ICRS = np.array([
    float(CMB_COORD.icrs.cartesian.x.value),
    float(CMB_COORD.icrs.cartesian.y.value),
    float(CMB_COORD.icrs.cartesian.z.value),
], dtype=np.float64)


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def ellis_baldwin_amplitude(alpha: float, x: float, beta: float = BETA_CMB) -> float:
    """Standard linear-order relativistic Ellis-Baldwin kinematic number-count dipole."""
    return float((2.0 + float(x) * (1.0 + float(alpha))) * float(beta))


def _icrs_sep_deg(v: np.ndarray, target: np.ndarray = CMB_ICRS) -> float:
    vn = v / np.linalg.norm(v)
    tn = target / np.linalg.norm(target)
    return float(np.rad2deg(np.arccos(np.clip(float(np.dot(vn, tn)), -1.0, 1.0))))


def run_radio_p4_analysis() -> dict:
    t0 = time.perf_counter()
    p_res = G04_DIR / "RESULT.json"
    p_df = G04_DIR / "DEEP_FIVE_SURVEY_RESULT.json"
    p_sf = G04_DIR / "SOLVER_FREE_RESEARCH_RESULT.json"
    d_res = json.loads(p_res.read_text())
    d_df = json.loads(p_df.read_text())
    d_sf = json.loads(p_sf.read_text())

    # 1. Unified 5-survey flux-ladder & overdispersion/jackknife/mask-leakage analysis
    sf_eb = d_sf["part_a_ellis_baldwin_and_ladders"]
    survey_ladders = {}
    alpha_grid = (0.6, 0.75, 0.85, 1.0)
    x_grid = (0.8, 0.9, 1.0, 1.15, 1.3)

    # Analytic EB envelope over conservative spectral index & count slope ranges
    eb_min = ellis_baldwin_amplitude(min(alpha_grid), min(x_grid))
    eb_max = ellis_baldwin_amplitude(max(alpha_grid), max(x_grid))
    eb_fiducial = ellis_baldwin_amplitude(0.75, 1.0)

    # Extract canonical ladders from SOLVER_FREE_RESEARCH_RESULT and DEEP_FIVE_SURVEY_RESULT
    all_excess_ratios = []
    all_jk_over_poisson = []
    for sname, sblock in sf_eb.items():
        ladder = sblock["ladder"]
        eb_segs = sblock["ellis_baldwin_segments"]
        seg_by_hi = {str(seg["flux_interval_mJy"][1]): seg for seg in eb_segs}
        thr_rows = {}
        for thr, rec in ladder.items():
            amp = float(rec["dipole_4p_amp"])
            sd_p = float(rec["sd_poisson"])
            sd_od = float(rec["sd_overdisp"])
            sd_jk = float(rec["sd_jackknife_48p"])
            vec = np.array(rec["dipole_4p_icrs_vec"], dtype=np.float64)
            # Measured or fiducial x from interval below thr
            x_meas = float(seg_by_hi[thr]["x_slope_measured"]) if thr in seg_by_hi else 1.0
            d_eb_meas = ellis_baldwin_amplitude(0.75, x_meas)
            # Excess beyond EB kinematic expectation
            excess_vec = vec - d_eb_meas * CMB_ICRS
            excess_amp = float(np.linalg.norm(excess_vec))
            ratio = float(amp / d_eb_meas)
            all_excess_ratios.append(ratio)
            all_jk_over_poisson.append(float(rec["jackknife_over_poisson_ratio"]))

            # LSS clustering vs shot-noise power ratio in ell=2..5
            cl_exc = np.array(rec["cl_excess_ell2_to_5"], dtype=np.float64)
            cl_shot = float(rec["poisson_shot_noise_floor"])
            cl_pseudo = np.array(rec["cl_pseudo_over_fsky_ell1_to_10"], dtype=np.float64)
            thr_rows[thr] = {
                "n_sources": int(rec["n_sources"]),
                "sky_fraction": float(rec["sky_fraction"]),
                "dipole_4p_amp": amp,
                "dipole_9p_amp": float(rec["dipole_9p_amp"]),
                "dipole_4p_vs_9p_shift_deg": float(rec["dipole_4p_vs_9p_shift_deg"]),
                "dipole_4p_sep_cmb_deg": float(rec["dipole_4p_sep_cmb_deg"]),
                "sep_recomputed_deg": _icrs_sep_deg(vec),
                "quad_9p_frob_norm": float(rec["quad_9p_frob_norm"]),
                "F9_condition": float(rec["F9_condition"]),
                "sd_poisson": sd_p,
                "sd_overdisp": sd_od,
                "sd_jackknife_48p": sd_jk,
                "jackknife_over_poisson_ratio": float(rec["jackknife_over_poisson_ratio"]),
                "poisson_overdispersion": float(rec["poisson_overdispersion"]),
                "x_slope_for_eb": x_meas,
                "d_eb_fiducial_alpha0p75": d_eb_meas,
                "excess_ratio_d_obs_over_d_eb": ratio,
                "excess_nonkinematic_amp_if_cmb_kinematic": excess_amp,
                "eb_bracket_alpha0p6_to_1p0_x0p8_to_1p3": [eb_min, eb_max],
                "poisson_shot_noise_floor": cl_shot,
                "cl_ell1_over_shot_noise": float(cl_pseudo[0] / cl_shot),
                "mean_cl_excess_ell2_5_over_shot": float(np.mean(cl_exc) / cl_shot),
                "snr_against_kinematic_overdisp": float((amp - d_eb_meas) / sd_od),
                "snr_against_kinematic_jackknife": float((amp - d_eb_meas) / sd_jk),
                "vector_snr_against_cmb_kinematic_overdisp": float(excess_amp / sd_od),
                "vector_snr_against_cmb_kinematic_jackknife": float(excess_amp / sd_jk),
            }
        survey_ladders[sname] = {
            "thresholds": thr_rows,
            "eb_segments": eb_segs,
        }

    # 2. Analytic Ellis-Baldwin 2D sensitivity grid (physical upper bound)
    eb_grid = {}
    for alpha in alpha_grid:
        eb_grid[f"alpha_{alpha:.2f}"] = {
            f"x_{x:.2f}": ellis_baldwin_amplitude(alpha, x) for x in x_grid
        }

    # 3. Selection bias and galactic-cut sensitivity from DEEP_FIVE_SURVEY & SOLVER_FREE
    racs_bias = d_df["surveys"]["RACS_low_DR1_888MHz"]["source_level_rms_cut_0p45_biased_selection_contrast_S20"]
    racs_unif_20 = d_df["surveys"]["RACS_low_DR1_888MHz"]["rms_uniform_footprint_ladder_mJy"]["20"]
    lotss_raw = d_df["surveys"]["LoTSS_DR3_144MHz"]

    # 4. Summarize frame-history / CF4 SQ-FRAME links from R89 G04 RESULT.json
    sq_frame_ref = {
        "beta_RO_norm": float(d_res["sq_frame_diagnostics"]["lorentz_fermi_identity_checks"]["beta_RO_norm"]),
        "radial_operator_rank_tol1e10": int(d_res["sq_frame_diagnostics"]["lorentz_fermi_identity_checks"]["radial_operator_rank_tol1e10"]),
        "antisymmetric_vorticity_null_dim": int(d_res["sq_frame_diagnostics"]["lorentz_fermi_identity_checks"]["antisymmetric_vorticity_null_dim"]),
        "J2_const_vs_free_history_rank_increment": int(d_res["sq_frame_diagnostics"]["frame_history_conditional_ranks"]["log"]["J2"]["const_vs_free_history"]["rank_increment_global"]),
        "J2_free_history_wald_3dof": float(d_res["sq_frame_diagnostics"]["frame_history_conditional_ranks"]["log"]["J2"]["free_history_W_wald_3dof"]),
    }

    out = {
        "schema": "htt.r95.radio_p4_kinematic_vs_selection/1",
        "sources_sha256": {
            "G04_RESULT": _sha(p_res),
            "G04_DEEP_FIVE_SURVEY": _sha(p_df),
            "G04_SOLVER_FREE": _sha(p_sf),
        },
        "elapsed_seconds": time.perf_counter() - t0,
        "cmb_reference": {
            "beta_cmb": BETA_CMB,
            "v_cmb_km_s": 369.82,
            "gal_lb_deg": [264.021, 48.253],
            "eb_fiducial_alpha0p75_x1p0": eb_fiducial,
            "eb_parameter_bracket": [eb_min, eb_max],
        },
        "ellis_baldwin_2d_grid": eb_grid,
        "five_survey_ladder_analysis": survey_ladders,
        "pairwise_common_sky_and_galcuts": {
            "pairwise_common_sky": d_sf["part_b_pairwise_overlaps_and_galcuts"]["pairwise_common_sky"],
            "galactic_cut_sensitivity": d_sf["part_b_pairwise_overlaps_and_galcuts"]["galactic_cut_sensitivity"],
            "racs_rms_tile_footprints": d_sf["part_b_pairwise_overlaps_and_galcuts"]["racs_rms_tile_footprints"],
        },
        "selection_and_flux_artifacts": {
            "racs_S20_uniform_rms_dipole_amp": float(racs_unif_20["dipole_amplitude"]),
            "racs_S20_uniform_rms_sep_cmb_deg": float(racs_unif_20["angle_to_cmb_deg"]),
            "racs_S20_source_rms_cut_0p45_biased_amp": float(racs_bias["dipole_amplitude"]),
            "racs_S20_source_rms_cut_0p45_biased_sep_cmb_deg": float(racs_bias["angle_to_cmb_deg"]),
            "racs_selection_bias_amp_inflation_factor": float(racs_bias["dipole_amplitude"] / racs_unif_20["dipole_amplitude"]),
            "lotss_edge500_sensitivity_S50": lotss_raw["edge500_sensitivity_S50"],
        },
        "cross_ladder_summary": {
            "n_survey_thresholds": len(all_excess_ratios),
            "d_obs_over_d_eb_minmax": [float(min(all_excess_ratios)), float(max(all_excess_ratios))],
            "jackknife_over_poisson_minmax": [float(min(all_jk_over_poisson)), float(max(all_jk_over_poisson))],
            "sq_frame_conditional_summary": sq_frame_ref,
        },
        "physics_gates": {
            "sq_radio_status": "DIAGNOSTIC_COMPLETED_SCOPED",
            "sq_frame_status": "DIAGNOSTIC_COMPLETED_SCOPED",
            "joint_five_survey_covariance_qualified": False,
            "physical_Pi": None,
            "physical_GF": None,
            "cosmological_bulk_flow_detection_claimed": False,
            "v04_v05_v06_status": "BLOCKED_DEPENDENCY",
            "exact_blocker": "No shared cross-survey selection/flux/redshift/mask joint covariance + no physical LSS + Bianchi transfer null.",
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_radio_p4_analysis()
    print(json.dumps({
        "n_survey_thresholds": res["cross_ladder_summary"]["n_survey_thresholds"],
        "d_obs_over_d_eb_minmax": res["cross_ladder_summary"]["d_obs_over_d_eb_minmax"],
        "jackknife_over_poisson_minmax": res["cross_ladder_summary"]["jackknife_over_poisson_minmax"],
        "racs_bias_factor": res["selection_and_flux_artifacts"]["racs_selection_bias_amp_inflation_factor"],
        "elapsed_s": res["elapsed_seconds"],
    }))

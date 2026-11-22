"""R95 Step 4/5 (G08_OPTICAL_PHY / PHY-01..07): Exact cross-probe synthesis from R95 source-conditioned artifacts.

Consumes verified R95 outputs G02..G07 (plus R89 G08 cross-probe dipole table) with SHA256 checks
and attaches source-conditioned cross-route evidence to PHY-01..PHY-07 without promoting
cross-probe joint likelihood or SQ-CROSS-COV.
"""
from __future__ import annotations

import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
R89_G08 = ROOT / "docs/research_program/observational_publication_20261015/R89_EIGHT_ANALYSIS_HANDOFF_20261121/runs/G08_OPTICAL_PHY/CROSSPROBE_SYNTHESIS_RESULT.json"
OUT_JSON = R95_DIR / "G08_CROSS_PHY_01_TO_07.json"


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def run_cross_phy_synthesis() -> dict:
    t0 = time.perf_counter()
    req = {
        "G02": R95_DIR / "G02_SQ_CF4_SYNTHESIS.json",
        "G03": R95_DIR / "G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json",
        "G04": R95_DIR / "G04_RADIO_P4_KINEMATIC_VS_SELECTION.json",
        "G05": R95_DIR / "G05_PLANCK_FULLRES_TEB_RESULT.json",
        "G06": R95_DIR / "G06_P1_FIVE_VIEW_TYPED_LEDGER.json",
        "G07_BG": R95_DIR / "G07_BIANCHI_BACKGROUND_AUDIT.json",
        "G07_OPT": R95_DIR / "G07_BIANCHI_REC_REI_OPTICS.json",
        "G07_POL": R95_DIR / "G07_BIANCHI_POLARIZED_HIERARCHY.json",
        "R89_G08": R89_G08,
    }
    missing = [k for k, p in req.items() if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"Required upstream R95 outputs missing for PHY synthesis: {missing}")

    d = {k: json.loads(p.read_text()) for k, p in req.items()}
    shas = {k: _sha(p) for k, p in req.items()}

    # PHY-01: Mask hemisphere shear leakage exactness + Type V j0*chi0 nonzero mask interaction
    g4_nvss20 = d["G04"]["five_survey_ladder_analysis"]["NVSS"]["thresholds"]["20"]
    g5_mask = d["G05"]["mask_and_beam_checks"]
    v_tilted = d["G07_BG"]["trajectories"]["V__tilted"]
    v_orth = d["G07_BG"]["trajectories"]["V__orthogonal"]
    phy01 = {
        "title": "Hemisphere/mask E->B & dipole-quadrupole leakage vs Type V j0*chi0 flux/shape bridge",
        "planck_mask_fsky_I_P": [g5_mask["f_sky_I"], g5_mask["f_sky_P"]],
        "planck_pure_E_to_B_mask_leak_mean": g5_mask["pure_E_synthetic_mask_leakage_clBB_over_clEE_mean_2_48"],
        "nvss_S20_4p_vs_9p_dipole_shift_deg": g4_nvss20["dipole_4p_vs_9p_shift_deg"],
        "bianchi_V_tilted_vs_orth_geodesic_TT_l2": [v_tilted["geodesic_cl_TT_l2"], v_orth["geodesic_cl_TT_l2"]],
        "blocker_bucket": "NATIVE_TRANSFER + DATA (requires masked all-m Bianchi atlas & physical E/B mask transfer covariance)",
    }

    # PHY-02: Photon moment covariance PSD + Einstein normal-flux ellipsoid
    pol_or = d["G07_POL"]["physics_oracles"]
    g7_max = d["G07_BG"]["global_constraint_maxima"]
    opt_hy = d["G07_OPT"]["hyrec2_plus_tanh_reionization"]
    phy02 = {
        "title": "Basis-free Thomson rank-9 collision PSD + DEC/WEC conformal normal-flux & HyRec-2+tanh visibility",
        "max_thomson_energy_rel_err": pol_or["max_thomson_energy_rel_err"],
        "max_screen_transversality_leak": pol_or["max_screen_transversality_leak"],
        "min_polarized_transverse_J_eig": pol_or["min_polarized_J_eigenvalue"],
        "max_hamiltonian_rel_across_17_evol": g7_max["max_hamiltonian_residual_rel"],
        "min_dec_margin_across_17_evol": min(rec["min_dec_margin"] for rec in d["G07_BG"]["trajectories"].values()),
        "physical_z_visibility_peak": opt_hy["z_visibility_peak"],
        "physical_tau_reion": opt_hy["tau_reion_z0_to_30"],
        "blocker_bucket": "DATA + MODEL (SQ-PHOTON-FLUX physical CMB higher moments + anisotropic reionization missing)",
    }

    # PHY-03: Common beta => Q_count = A(3+beta^2) S_gamma/4 & d = k(3+beta^2) m/4
    beta_cmb = d["G04"]["cmb_reference"]["beta_cmb"]
    boost_factor = 1.0 + (beta_cmb ** 2) / 3.0  # (3 + beta^2)/3 normalization relative to linear beta
    q_rel_quad_from_cmb_beta = 0.75 * (beta_cmb ** 2)  # pure kinematic O(beta^2) quadrupole weight
    phy03 = {
        "title": "Common Solar/CMB boost beta vector across Planck, Radio Ellis-Baldwin, Gaia E1 aberration & CF4 SR gamma",
        "beta_cmb": beta_cmb,
        "exact_3plusbeta2_over3": boost_factor,
        "kinematic_beta2_quadrupole_scale": q_rel_quad_from_cmb_beta,
        "radio_d_obs_over_d_eb_range": d["G04"]["cross_ladder_summary"]["d_obs_over_d_eb_minmax"],
        "gaia_quality_E1_amp_uasyr": d["G03"]["gaia_and_vlba_subsets_transformed"]["gaia_quality_1p20M"]["E1"]["norm_uasyr"],
        "gaia_quality_E1_gal_lb_deg": d["G03"]["gaia_and_vlba_subsets_transformed"]["gaia_quality_1p20M"]["E1"]["gal_lb_deg"],
        "gaia_quality_scanlaw_deproj_E1_amp_uasyr": d["G03"]["gaia_and_vlba_subsets_transformed"]["gaia_quality_scanlaw_deproj_1p20M"]["E1"]["norm_uasyr"],
        "gaia_quality_scanlaw_deproj_E1_gal_lb_deg": d["G03"]["gaia_and_vlba_subsets_transformed"]["gaia_quality_scanlaw_deproj_1p20M"]["E1"]["gal_lb_deg"],
        "cf4_sr_gamma_H0_shift_z040": d["G02"]["sr_gamma_doppler_tomography_4w"]["z_0.040"]["H0_shift_SR_minus_no_gamma"],
        "blocker_bucket": "DATA (matched LSS clustering null in radio & AGN/quasar chromatic selection calibration)",
    }

    # PHY-04: V_B = -c n x N n; B2 vs local shear E2 + spin-vorticity B1 degeneracy
    q_inv = d["G03"]["quaia_weighting_models_transformed"]["inverse_noise"]
    g7_vi = d["G07_BG"]["trajectories"]["IX__tilted"]
    phy04 = {
        "title": "Gaia VSH B2 vs E2 orthogonality, B1=Omega_frame-omega_cosmic degeneracy & Bianchi IX vorticity",
        "quaia_inv_E2_norm_uasyr": q_inv["E2"]["norm_uasyr"],
        "quaia_inv_B2_norm_uasyr": q_inv["B2"]["norm_uasyr"],
        "quaia_inv_wald10_jk": q_inv["jk_10x10_E2B2_wald10"],
        "gaia_scanlaw_ecl_m0_frac": d["G03"]["scanning_law_quadrupole_frame_check"]["ecliptic_m0_axisymmetric_energy_fraction"],
        "quaia_inv_E2_ecl_m0_frac": q_inv["E2"]["ecliptic_m0_axisymmetric_fraction"],
        "bianchi_IX_tilted_photon_vorticity": g7_vi["photon_congruence_vorticity_norm"],
        "actual_normal_vorticity": None,
        "blocker_bucket": "DATA + MODEL (no external quasar systematic null & radial-free B1 vorticity degeneracy)",
    }

    # PHY-05: Exceptional VI_{-1/9} rank M2 left flux null + CF4 J2 carrier reference
    vi_exc = d["G07_BG"]["trajectories"]["VI_-1/9_exception__tilted"]
    vi_rk4 = d["G07_BG"]["vi_minus_1_9_rk4_convergence"]
    phy05 = {
        "title": "Exceptional Class-B VI_{-1/9} (h=-1/9, N=diag(0,1,-4)) dynamics, BASS-HTT Codazzi & RK4 convergence",
        "vi_exc_max_jacobi": vi_exc["max_jacobi_residual"],
        "vi_exc_max_hamiltonian_rel": vi_exc["max_hamiltonian_residual_rel"],
        "vi_exc_max_codazzi_rel": vi_exc["max_codazzi_residual_rel"],
        "vi_exc_max_bass_htt_codazzi_diff": vi_exc["max_bass_htt_codazzi_diff"],
        "vi_exc_rk4_ratio_48_to_96_to_192": [
            vi_rk4["null_err_ratio_48_over_96"],
            vi_rk4["null_err_ratio_96_over_192"],
        ],
        "vi_exc_geodesic_cl2_TT_EE_BB": [
            vi_exc["geodesic_cl_TT_l2"],
            vi_exc["geodesic_cl_EE_l2"],
            vi_exc["geodesic_cl_BB_l2"],
        ],
        "r62_cf4_log_15d_null_chi2": d["G07_BG"]["r62_cf4_carrier_reference"]["chi2_null_15d"],
        "blocker_bucket": "MODEL + NATIVE_TRANSFER (SQ-LIE-FLUX normal-frame rho/j/pi closure & all-m Boltzmann)",
    }

    # PHY-06: Commutator [D, sigma] != 0 eigenframe rotation, Wigner angle & chirality mirror
    g7_7h = d["G07_BG"]["trajectories"]["VII_h__tilted"]
    q2_cosmo = np.array(g7_7h["geodesic_cosmo_Q2_stf5"])
    q2_obs = np.array(g7_7h["geodesic_obs_Q2_stf5"])
    cos_align_7h = float(np.dot(q2_cosmo, q2_obs) / (np.linalg.norm(q2_cosmo) * np.linalg.norm(q2_obs)))
    phy06 = {
        "title": "Helical/frame commutator [D, sigma] eigenframe rotation, Class-B mirror parity & Planck E/B BiPoSH",
        "bianchi_VIIh_wigner_rad_obs_rad": g7_7h["wigner_rad_obs_angle_rad"],
        "bianchi_VIIh_cosmo_vs_obs_Q2_cosine": cos_align_7h,
        "vii_h_mirror_chirality_TT_TB_EB": [
            pol_or["handedness_chirality_checks"]["VII_h_mirror_P_sigma"]["TT_rel_diff"],
            pol_or["handedness_chirality_checks"]["VII_h_mirror_P_sigma"]["TB_flip_residual_rel"],
            pol_or["handedness_chirality_checks"]["VII_h_mirror_P_sigma"]["EB_flip_residual_rel"],
        ],
        "planck_fullres_smica_20D_p300_T_E_B": [
            d["G05"]["biposh_L2_summary"]["T"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
            d["G05"]["biposh_L2_summary"]["E"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
            d["G05"]["biposh_L2_summary"]["B"]["global_20D_smica_n2048_unique_noise_300"]["rank_p"],
        ],
        "blocker_bucket": "NATIVE_TRANSFER + MODEL (full-sky inhomogeneous Bianchi phase/eigenframe template likelihood)",
    }

    # PHY-07: Radius variation rank-12 vs rank-9 + CF4 joint PV/calibration + finite-z Sachs d_L
    sqf = d["G04"]["cross_ladder_summary"]["sq_frame_conditional_summary"]
    r5_0 = d["G02"]["joint_pv_plus_calibration_grid"]["R5"]["sig_cal_0.00"]
    r5_005 = d["G02"]["joint_pv_plus_calibration_grid"]["R5"]["sig_cal_0.05"]
    phy07 = {
        "title": "Radial-operator rank-6/antisymmetric-null-3, CF4 joint PV+calibration & finite-z geodesic vs z->0 STF",
        "sq_frame_radial_operator_rank_tol1e10": sqf["radial_operator_rank_tol1e10"],
        "sq_frame_antisymmetric_vorticity_null_dim": sqf["antisymmetric_vorticity_null_dim"],
        "sq_frame_J2_rank_increment_global": sqf["J2_const_vs_free_history_rank_increment"],
        "cf4_R5_cal000_vs_cal005_H0_sd": [r5_0["H0_sd"], r5_005["H0_sd"]],
        "p1_manski_unknown0p25_W3_interval": [
            d["G06"]["manski_unknown_mass_stress"]["unknown_frac_0.25"]["at_0p05"]["W3_lower"],
            d["G06"]["manski_unknown_mass_stress"]["unknown_frac_0.25"]["at_0p05"]["W3_upper"],
        ],
        "blocker_bucket": "DATA + MODEL (SQ-CF4 pre-intercalibration MCMC + SQ-OPTICAL finite-z Sachs drift observable)",
    }

    out = {
        "schema": "htt.r95.cross_phy_01_to_07_synthesis/1",
        "elapsed_seconds": time.perf_counter() - t0,
        "upstream_sha256": shas,
        "cross_probe_dipole_reference_count": len(d["R89_G08"]["cross_probe_dipole_alignment_galactic"]["probes"]),
        "PHY_routes": {
            "PHY-01": phy01,
            "PHY-02": phy02,
            "PHY-03": phy03,
            "PHY-04": phy04,
            "PHY-05": phy05,
            "PHY-06": phy06,
            "PHY-07": phy07,
        },
        "physics_gates": {
            "cross_probe_joint_likelihood_qualified": False,
            "sq_cross_cov_status": "BLOCKED_DEPENDENCY",
            "physical_Pi": None,
            "physical_GF": None,
            "r78_historical_phy_states_changed": False,
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n")
    return out


if __name__ == "__main__":
    res = run_cross_phy_synthesis()
    print(json.dumps({
        "n_phy": len(res["PHY_routes"]),
        "phy05_rk4": res["PHY_routes"]["PHY-05"]["vi_exc_rk4_ratio_48_to_96_to_192"],
        "phy06_p300_TEB": res["PHY_routes"]["PHY-06"]["planck_fullres_smica_20D_p300_T_E_B"],
        "phy07_H0_sd": res["PHY_routes"]["PHY-07"]["cf4_R5_cal000_vs_cal005_H0_sd"],
        "elapsed_s": res["elapsed_seconds"],
    }))

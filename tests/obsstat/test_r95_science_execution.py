"""R95 scientific execution, live physics-oracle, SHA provenance & claim-firewall suite."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import numpy as np

from scripts.r95 import bianchi_polarized_hierarchy as pol_mod
from scripts.r95 import gaia_p6_analysis as gaia_mod
from scripts.r95 import radio_p4_analysis as radio_mod

ROOT = Path(__file__).resolve().parents[2]
R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R95_DIR = ROOT / "docs/research_program/observational_publication_20261015/R95_LOCAL_EXECUTION_20261122"
EXPECTED_R78_SHA = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"

FORBIDDEN_CLAIMS = (
    "Bianchi geometry detected",
    "Bianchi family identified",
    "model-independent truth certificate",
    "MIO posterior",
    "TSC full solver",
    "Teff full polarisation closure",
    "external transfer validated as native",
)


def _load(name: str) -> dict:
    p = R95_DIR / name
    assert p.is_file(), f"Missing R95 artifact: {p}"
    return json.loads(p.read_text())


def _file_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_r78_ssot_immutability_master_ledger_and_report_firewall():
    assert _file_sha256(R78_DAG) == EXPECTED_R78_SHA
    r78 = json.loads(R78_DAG.read_text())
    assert len(r78["nodes"]) == 60
    assert len(r78["edges"]) == 129
    assert r78["next_action_id"] == "SQ-CF4"

    m = _load("R95_60_NODE_EVIDENCE.json")
    assert m["r78_integrated_dag_sha256"] == EXPECTED_R78_SHA
    assert m["r78_total_nodes"] == 60
    assert m["r78_hard_edges"] == 129
    assert m["r78_next_action_id"] == "SQ-CF4"
    assert m["original_science_status_changed"] is False
    assert m["actual_r95_physical_science_acceptance"] is False

    # Verify every recorded SHA on disk
    art_map = {
        "FFP10_PILOT": "FFP10_LINEAR_PILOT_PARITY.json",
        "G02": "G02_SQ_CF4_SYNTHESIS.json",
        "G03": "G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json",
        "G04": "G04_RADIO_P4_KINEMATIC_VS_SELECTION.json",
        "G05": "G05_PLANCK_FULLRES_TEB_RESULT.json",
        "G06": "G06_P1_FIVE_VIEW_TYPED_LEDGER.json",
        "G07_BG": "G07_BIANCHI_BACKGROUND_AUDIT.json",
        "G07_OPT": "G07_BIANCHI_REC_REI_OPTICS.json",
        "G07_POL": "G07_BIANCHI_POLARIZED_HIERARCHY.json",
        "G08": "G08_CROSS_PHY_01_TO_07.json",
    }
    for key, fname in art_map.items():
        assert m["artifact_shas"][key] == _file_sha256(R95_DIR / fname)

    ids = [n["id"] for n in m["nodes"]]
    assert len(ids) == 60 and len(set(ids)) == 60
    by_id = {n["id"]: n for n in m["nodes"]}
    assert "PHYSICAL_BLOCKED_INPUT_PRESERVED" in by_id["SQ-CF4"]["r95_execution_status"]
    assert "K02" in by_id and "CF4" in str(by_id["K02"]["numerical_and_physical_summary"])

    rep = (R95_DIR / "R95_REPORT_KO.md").read_text()
    assert "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11" in rep
    assert "original_science_status_changed = false" in rep
    for bad in FORBIDDEN_CLAIMS:
        assert bad not in rep


def test_g02_sq_cf4_synthesis_and_blockers():
    d = _load("G02_SQ_CF4_SYNTHESIS.json")
    assert d["parity_r36_theta_max_abs_diff"] < 1e-11
    assert d["k02_backend_receipt"]["original_source_count"] == 35970
    assert d["k02_backend_receipt"]["source_certified"] is True
    r5 = d["joint_pv_plus_calibration_grid"]["R5"]
    assert r5["sig_cal_0.05"]["H0_sd"] > r5["sig_cal_0.00"]["H0_sd"]
    # Verify z_CMB was NOT double-subtracted in SR tomography
    theta_z025 = d["sr_gamma_doppler_tomography_4w"]["z_0.025"]["theta_SR_zCMB"]
    assert abs(theta_z025[0] - 75.168) < 0.05 and theta_z025[1] < 0.0
    assert d["publication_grade_physical_acceptance"] is False
    assert "BLOCKED_INPUT" in d["blocker_triage"]["SQ-CF4"]


def test_g03_gaia_live_so3_rotation_and_vorticity_gate():
    R_gal = gaia_mod._build_icrs_to_frame_rotation("galactic")
    assert np.max(np.abs(R_gal.T @ R_gal - np.eye(3))) < 1e-13
    E = gaia_mod._load_mod("r95_test_5v", gaia_mod.FIVEVIEW_PY).E
    M5 = gaia_mod._build_stf5_rotation(R_gal, E)
    assert np.max(np.abs(M5.T @ M5 - np.eye(5))) < 1e-13

    d = _load("G03_GAIA_P6_SYSTEMATICS_AND_FRAME.json")
    assert d["so3_tangent_equivariance_max_abs_err"]["galactic"] < 1e-12
    assert d["so3_tangent_equivariance_max_abs_err"]["ecliptic"] < 1e-12
    assert d["scanning_law_quadrupole_frame_check"]["ecliptic_m0_axisymmetric_energy_fraction"] > 0.99
    for wname, rec in d["quaia_weighting_models_transformed"].items():
        assert rec["jk_10x10_min_eig"] > 0.0, f"Non-PSD jackknife covariance in {wname}"
        assert rec["jk_10x10_E2B2_wald10"] > 0.0
    gates = d["physics_gates"]
    assert gates["sq_gaia_status"] == "DIAGNOSTIC_COMPLETED_SCOPED"
    assert gates["actual_normal_vorticity"] is None
    assert gates["physical_Pi"] is None
    assert gates["physical_GF"] is None


def test_g04_radio_live_ellis_baldwin_and_joint_cov_gate():
    assert abs(radio_mod.ellis_baldwin_amplitude(0.75, 1.0, beta=0.001) - 0.00375) < 1e-15
    d = _load("G04_RADIO_P4_KINEMATIC_VS_SELECTION.json")
    beta = d["cmb_reference"]["beta_cmb"]
    assert abs(d["ellis_baldwin_2d_grid"]["alpha_0.75"]["x_1.00"] - 3.75 * beta) < 1e-14
    assert d["cross_ladder_summary"]["n_survey_thresholds"] == 19
    gates = d["physics_gates"]
    assert gates["joint_five_survey_covariance_qualified"] is False
    assert gates["physical_Pi"] is None
    assert gates["physical_GF"] is None
    assert gates["v04_v05_v06_status"] == "BLOCKED_DEPENDENCY"


def test_g05_planck_fullres_999_300_and_pilot_parity():
    pilot = _load("FFP10_LINEAR_PILOT_PARITY.json")
    assert pilot["parity_pass"] is True
    for ch in ("T", "E", "B"):
        assert pilot["parity_by_channel_complex64"][ch]["max_abs"] < 1e-6

    d = _load("G05_PLANCK_FULLRES_TEB_RESULT.json")
    assert d["sample_counts"]["cmb_ids"] == 999
    assert d["sample_counts"]["missing_cmb_id"] == 970
    assert d["sample_counts"]["unique_noise_primary_N"] == 300
    assert d["sample_counts"]["recycled_noise_secondary_N"] == 999
    assert d["mask_and_beam_checks"]["pure_E_synthetic_n_draws"] == 10
    for ch in ("T", "E", "B"):
        assert d["gaunt_cpp_vs_numpy_parity_max_abs"][ch] < 1e-10
        assert d["biposh_L2_summary"][ch]["global_20D_smica_n2048_unique_noise_300"]["MC_N"] == 300
        assert d["biposh_L2_summary"][ch]["global_20D_smica_n2048_recycled_noise_999"]["MC_N"] == 999
    gates = d["physics_gates"]
    assert gates["smica_unique_noise_primary_N"] == 300
    assert gates["commander_null_qualified"] is False
    assert gates["bianchi_family_identified"] is False
    assert gates["native_boltzmann_likelihood_completed"] is False
    assert gates["physical_Pi"] is None
    assert gates["physical_GF"] is None


def test_g06_p1_manski_strict_monotonicity_and_negative_controls():
    d = _load("G06_P1_FIVE_VIEW_TYPED_LEDGER.json")
    assert d["sample_count"] == 2048
    low_prev = 2.0
    up_prev = -1.0
    for frac in ("unknown_frac_0.00", "unknown_frac_0.05", "unknown_frac_0.15", "unknown_frac_0.25"):
        at5 = d["manski_unknown_mass_stress"][frac]["at_0p05"]
        assert at5["W3_lower"] <= at5["W3_upper"]
        assert at5["W3_lower"] <= low_prev + 1e-12
        assert at5["W3_upper"] >= up_prev - 1e-12
        low_prev, up_prev = at5["W3_lower"], at5["W3_upper"]
    for pname, entry in d["five_view_typed_ledger_P1_to_P6"].items():
        assert entry["Pi"] is None, f"{pname} must keep physical Pi=None"
        assert entry["G_F"] is None, f"{pname} must keep physical G_F=None"
    neg = d["negative_controls"]
    assert neg["all_unknown_width_1"] is True
    assert neg["all_unknown_physical_Pi_is_None"] is True
    assert neg["full_draw_physical_Pi_is_None"] is True
    assert neg["full_draw_physical_GF_is_None"] is True
    assert d["publication_grade_physical_Pi_promoted"] is False


def test_g07_bianchi_physics_oracles_and_live_hierarchy():
    # Live check of scalable harmonic hierarchy conformal solver
    vis = pol_mod._prepare_physical_visibility_timeline()
    h16 = pol_mod.solve_scalable_harmonic_hierarchy(ell_max=16, k_eff_Mpc_inv=0.002, boundary="radiation_impedance", vis_tl=vis)
    assert h16["state_dim_per_m"] == 32 and abs(h16["E2_over_Theta2"]) > 1e-4

    bg = _load("G07_BIANCHI_BACKGROUND_AUDIT.json")
    assert bg["stf5_quadrupole_roundtrip_maxabs"] < 1e-12
    assert bg["fournodavlos_2026_benchmark"]["passed"] is True
    gmax = bg["global_constraint_maxima"]
    assert gmax["n_evolutions"] == 17
    assert gmax["max_jacobi_residual"] < 1e-12
    assert gmax["max_hamiltonian_residual_rel"] < 1e-9
    assert gmax["max_codazzi_residual_rel"] < 1e-9
    assert gmax["max_bass_htt_signed_codazzi_diff"] < 1e-14
    rk4 = bg["vi_minus_1_9_rk4_convergence"]
    assert 12.0 < rk4["null_err_ratio_48_over_96"] < 20.0
    assert 12.0 < rk4["null_err_ratio_96_over_192"] < 20.0

    opt = _load("G07_BIANCHI_REC_REI_OPTICS.json")
    hy = opt["hyrec2_plus_tanh_reionization"]
    assert 1080.0 < hy["z_visibility_peak"] < 1100.0
    assert 0.045 < hy["tau_reion_z0_to_30"] < 0.065
    assert hy["visibility_normalization_abs_error"] < 1e-3
    # Verify exact 1/6 Omega_sigma factor in BASS Peebles H(z)
    pb = opt["bianchi_anisotropic_peebles_sensitivity"]["1e-02"]
    assert abs(pb["omega_sigma0"] - (1e-4 / 6.0)) < 1e-12
    assert opt["rec_and_rei_provenance"]["REI_full_cmb_electron_history_qualified"] is False

    pol = _load("G07_BIANCHI_POLARIZED_HIERARCHY.json")
    po = pol["physics_oracles"]
    assert po["all_oracles_passed"] is True
    assert po["max_thomson_energy_rel_err"] < 1e-12
    assert po["max_screen_transversality_leak"] < 1e-11
    assert po["min_polarized_J_eigenvalue"] > 0.0
    assert po["handedness_chirality_checks"]["VII_h_mirror_P_sigma"]["TB_flip_residual_rel"] < 1e-6
    assert po["handedness_chirality_checks"]["IX"]["EB_flip_residual_rel"] < 1e-6
    assert pol["scalable_2lplus1_hierarchy"]["radiation_impedance_L60_dims"]["executed_m0_TE_dim"] == 120
    assert pol["scalable_2lplus1_hierarchy"]["convergence_to_L96"]["radiation_impedance"]["L=60"]["rel_diff_cl_TT_ell_le_16"] < 1e-7
    assert pol["publication_gates"]["SQ_NATIVE_and_B02_to_B05_promoted"] is False


def test_g08_cross_phy_01_to_07_and_gates():
    d = _load("G08_CROSS_PHY_01_TO_07.json")
    assert set(d["PHY_routes"].keys()) == {f"PHY-0{k}" for k in range(1, 8)}
    gates = d["physics_gates"]
    assert gates["cross_probe_joint_likelihood_qualified"] is False
    assert gates["physical_Pi"] is None
    assert gates["physical_GF"] is None
    assert gates["r78_historical_phy_states_changed"] is False

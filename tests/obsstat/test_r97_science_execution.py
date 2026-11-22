"""R97 science execution verification suite across Units A-D (P1-P6, PHY-01..07).

Verifies exact mathematical identities, oracles, source-SHA provenance, and
non-promotion / claim-firewall invariants without mutating R78-R96 authorities.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest
from sympy.physics.wigner import wigner_3j

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "htt"), str(ROOT / "htt/src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.r97 import bianchi_coupled_m_transport as r97c
from scripts.r97 import cmb_injection_and_eb_leakage as r97b

R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R97_DIR = ROOT / "docs/research_program/observational_publication_20261015/R97_SCIENCE_EXECUTION_20261122"
EXPECTED_R78_SHA = "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"


def _load(name: str) -> dict:
    return json.loads((R97_DIR / name).read_text())


def test_r78_authority_immutable_and_r97_ledger_aligned():
    assert sha256(R78_DAG.read_bytes()).hexdigest() == EXPECTED_R78_SHA
    dag = json.loads(R78_DAG.read_text())
    led = _load("R97_60_NODE_EXECUTION_LEDGER.json")
    assert len(dag["nodes"]) == 60 and len(dag["edges"]) == 129
    assert dag["next_action_id"] == "SQ-CF4"
    assert led["r78_integrated_dag_sha256"] == EXPECTED_R78_SHA
    assert not led["original_science_status_changed"]
    assert not led["actual_r97_physical_science_acceptance"]
    dag_by_id = {n["id"]: n for n in dag["nodes"]}
    assert {n["id"] for n in led["nodes"]} == set(dag_by_id.keys())
    for fname, expected_sha in led["r97_unit_artifact_shas"].items():
        assert len(expected_sha) == 64
        assert sha256((R97_DIR / fname).read_bytes()).hexdigest() == expected_sha
    assert set(led["r97_unit_artifact_shas"].keys()) == {
        "CF4_GENEALOGY_AND_PARTIAL_ID.json",
        "CMB_INJECTION_AND_EB_LEAKAGE.json",
        "BIANCHI_COUPLED_M_TRANSPORT.json",
        "PHY_AND_P1_P4_P6_SYNTHESIS.json",
    }
    for n in led["nodes"]:
        h = n["r97_artifact_sha256"]
        assert isinstance(h, str) and len(h) == 64
        int(h, 16)
        assert n["r78_science_state_preserved"] == dag_by_id[n["id"]]["state"]


def test_unit_a_cf4_genealogy_subspace_and_partial_id():
    a = _load("CF4_GENEALOGY_AND_PARTIAL_ID.json")
    assert a["r36_K4_exact_formula_max_abs_diff"] < 1e-12
    assert a["r36_theta_parity_max_abs_diff"] < 1e-11
    gen = a["cf4_genealogy"]
    assert gen["N_selected_groups"] == 35970
    assert all(gen["numeric_DM_vs_R27_S7_mismatches"][k] == 0 for k in ("SNIa", "FP", "TFR", "SBFm", "SBFir", "SNII"))
    assert gen["numeric_DM_vs_R27_S7_mismatches"]["DirectCal"] == 9
    assert gen["table3_DMzp_minus_DMav_min_max"][0] == pytest.approx(-0.147, abs=1e-6)
    assert gen["table3_DMzp_minus_DMav_min_max"][1] == pytest.approx(-0.147, abs=1e-6)
    assert gen["table2_comparison"]["table2_total_galaxies"] == 55877

    sub = a["subspace_reconciliation_K4_vs_J7"]
    assert sub["K4_rank"] == 4 and sub["J7_rank"] == 7
    assert 0.95 < sub["fraction_whitened_variance_inside_col_J7"] <= 1.0

    bounds = a["sharp_partial_identification_bounds"]
    req_keys = (
        "R95_R5_ivw_overlap_only_plus_0p02cal_1sigma",
        "R95_R5_ivw_overlap_plus_0p05cal_1sigma",
        "R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma",
        "R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid",
        "R36_inherited_ivw_common_0p087_tully23sys_1sigma",
    )
    for k in req_keys:
        assert k in bounds

    b02 = bounds["R95_R5_ivw_overlap_only_plus_0p02cal_1sigma"]
    b05 = bounds["R95_R5_ivw_overlap_plus_0p05cal_1sigma"]
    b087 = bounds["R95_R5_ivw_overlap_plus_0p087_tully23sys_1sigma"]
    b087_95 = bounds["R95_R5_ivw_overlap_plus_0p087_tully23sys_95pct_ellipsoid"]

    assert 0.5 < b02["H0_partial_id_halfwidth"] < b05["H0_partial_id_halfwidth"] < b087["H0_partial_id_halfwidth"] < b087_95["H0_partial_id_halfwidth"]
    assert b02["dipole_max_ellipsoid_shift"] == pytest.approx(b05["dipole_max_ellipsoid_shift"], abs=1e-11)
    assert b05["dipole_max_ellipsoid_shift"] == pytest.approx(b087["dipole_max_ellipsoid_shift"], abs=1e-11)
    assert b02["quad_max_ellipsoid_shift"] == pytest.approx(b05["quad_max_ellipsoid_shift"], abs=1e-11)
    assert b05["quad_max_ellipsoid_shift"] == pytest.approx(b087["quad_max_ellipsoid_shift"], abs=1e-11)
    assert b087["dipole_max_ellipsoid_shift"] < b087_95["dipole_max_ellipsoid_shift"]
    assert b087["quad_max_ellipsoid_shift"] < b087_95["quad_max_ellipsoid_shift"]

    for row in bounds.values():
        assert row["gls_substitution_parity_err"] < 1e-11
        lo, hi = row["H0_partial_id_interval"]
        assert lo < row["H0_point"] < hi

    schur = a["disjoint_partition_consistency"]["radial_inner_to_outer_schur_18dof"]
    r95_rc2 = schur["C_R95_R5_cal005"]["outer_2w_pred_reduced_chi2"]
    r36_rc2 = schur["C_R36_inherited"]["outer_2w_pred_reduced_chi2"]
    assert 1.5 < r95_rc2 < r36_rc2 < 5.0

    assert a["physics_gates"]["sq_cf4_status"] == "BLOCKED_INPUT"
    assert not a["physics_gates"]["publication_ready"]
    assert a["physics_gates"]["full_S_PV_and_calibration"] is None


def test_unit_b_cmb_master_eb_and_injection_recovery():
    for l1, l2, l3 in ((10, 14, 6), (24, 30, 12), (48, 48, 96), (35, 42, 15)):
        assert abs(r97b._racah_w3j(l1, l2, l3, 2, -2, 0) - float(wigner_3j(l1, l2, l3, 2, -2, 0))) < 1e-13

    b = _load("CMB_INJECTION_AND_EB_LEAKAGE.json")
    mc = b["master_spin2_mask_coupling"]
    assert mc["wigner3j_sympy_oracle_err"] < 1e-12
    assert mc["analytic_vs_mc_rel_diff"] < 0.15

    deb = b["cross_split_60D_eb_leakage_debiasing"]
    assert 0.9 < deb["paired_TE_to_B_heldout_variance_ratio"] < 1.0
    assert 0.9 < deb["sig_only_999_E_to_B_heldout_variance_ratio"] < 1.0

    inj = b["anisotropy_injection_recovery"]
    slope = inj["recovered_amplitude_linear_fit"]["slope"]
    assert 0.85 < slope < 1.05
    sw = inj["coherent_additive_L2_sweep_150_heldout"]
    assert sw["A_6.00"]["by_shrinkage"]["0.2"]["power_at_p95"] > sw["A_0.00"]["by_shrinkage"]["0.2"]["power_at_p95"]

    mm = inj["nside2048_multiplicative_modulation_eps0p25"]
    assert 30.0 < mm["mean_score_unmodulated"] < 160.0
    assert mm["mean_score_modulated"] > mm["mean_score_unmodulated"]

    pg = b["physics_gates"]
    assert pg["commander_null_qualified"] is False
    assert pg["Bianchi_family_attribution"] is None
    assert pg["physical_Pi"] is None and pg["physical_GF"] is None


def test_unit_c_bianchi_coupled_m_oracles_and_controls():
    c = _load("BIANCHI_COUPLED_M_TRANSPORT.json")
    ov = c["oracle_verification"]
    assert ov["twist_operator_vs_2d_gl_grid_max_abs_err"] < 1e-12
    assert ov["geo_operator_reality_conjugate_parity_err"] < 1e-12
    assert ov["skew_hermitian_err"] < 1e-12
    assert ov["r49_4d_geodesic_oracle_rel_err_T"] < 1e-8
    assert ov["r49_4d_geodesic_oracle_rel_err_E"] < 1e-8
    assert ov["r49_4d_geodesic_oracle_rel_err_B"] < 1e-8

    # Live run of full-all-m L=6 angular quadrature + 4D geodesic ray oracle
    live_ov = r97c.verify_angular_quadrature_oracle()
    assert live_ov["twist_operator_vs_2d_gl_grid_max_abs_err"] < 1e-12
    assert live_ov["geo_operator_reality_conjugate_parity_err"] < 1e-12
    assert live_ov["skew_hermitian_err"] < 1e-12
    assert live_ov["r49_4d_geodesic_oracle_rel_err_T"] < 1e-8
    assert live_ov["r49_4d_geodesic_oracle_rel_err_E"] < 1e-8
    assert live_ov["r49_4d_geodesic_oracle_rel_err_B"] < 1e-8

    ctrl = c["controls"]
    assert ctrl["FLRW_all_mode_norm"] < 1e-20
    assert ctrl["Bianchi_I_axisym_m_nonzero_ratio"] < 1e-20
    assert ctrl["Bianchi_I_axisym_total_B_power"] < 1e-20
    assert ctrl["k0_allm_L12_reality_conjugate_parity_err"] < 1e-12
    assert ctrl["m0_seed_scattering_VI_minus_1_9"]["h_parameter_preserved"] == pytest.approx(-1.0 / 9.0, abs=1e-10)
    assert ctrl["m0_seed_scattering_VI_minus_1_9"]["m_nonzero_over_total_T_power"] > 0.05

    chi = c["chirality_VIIh_L16"]
    assert chi["TT_rel_diff"] < 1e-10
    assert chi["TB_flip_residual_rel"] < 1e-10
    assert chi["EB_flip_residual_rel"] < 1e-10

    allm8 = c["full_all_m_vs_m5_L8_VI_minus_1_9"]
    allm12 = c["full_all_m_vs_m5_L12_VI_minus_1_9"]
    assert allm8["all_m_dim"] == 235 and allm8["m5_dim"] == 109
    assert allm8["power_fraction_leaking_to_abs_m_gt_2"] < 1e-2
    assert allm12["all_m_dim"] == 499 and allm12["m5_dim"] == 169
    assert allm12["power_fraction_leaking_to_abs_m_gt_2"] < 1e-2
    assert max(c["L32_vs_L60_B_over_E_rel_diff"].values()) < 0.02

    assert c["coupled_m5_by_L"]["60"]["VI_-1/9"]["state_dim"] == 889
    assert not c["physics_gates"]["full_all_m_boltzmann_closure"]
    assert not c["physics_gates"]["SQ_NATIVE_and_B02_to_B05_promoted"]


def test_unit_d_cross_phy_synthesis_and_gates():
    syn = _load("PHY_AND_P1_P4_P6_SYNTHESIS.json")
    assert set(syn["PHY_routes"].keys()) == {f"PHY-{i:02d}" for i in range(1, 8)}
    p1 = syn["P1_five_view_with_r97_cf4_bounds"]
    assert p1["physical_Pi"] is None
    assert p1["physical_GF"] is None
    cal_b = p1["cal_widened_tail_bounds_at_0p05_4w"]
    nom_b = p1["tail_bounds_at_0p05_4w"]
    for j in range(4):
        assert cal_b["lower_cal"][j] <= nom_b["lower"][j] <= cal_b["upper_cal"][j]
        assert cal_b["lower_cal"][j] < cal_b["upper_cal"][j]
    assert not syn["P4_radio_five_survey_summary"]["joint_five_survey_covariance_qualified"]
    assert syn["P6_gaia_quaia_bianchi_overlap"]["actual_normal_vorticity"] is None
    assert syn["physics_gates"]["Bianchi_family_attribution"] is None
    assert not syn["physics_gates"]["cross_probe_joint_likelihood_qualified"]

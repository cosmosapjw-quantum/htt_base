"""R91 actual-source second cycle: science identities and analytic/covariance tests."""
from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np
import pytest
from scipy.io import FortranFile
from scripts.r91 import run_second_cycle as r91
from scripts.r91 import cf4_legacy_pv_requalification as cf4
from scripts.r91 import pliklite_baseline as plik
from scripts.r91 import planck_cl_morphology as cl
from scripts.r91 import gaia_quaia_full as gaia

@pytest.fixture(scope="module")
def outputs():
    return {name:json.loads((r91.R91/name).read_text()) for name in (
      "FILE_SCAN_SUMMARY.json","SOURCE_DISCOVERY.json",
      "CF4_EXISTING_PV_REQUALIFIED.json","PLIKLITE_BASELINE.json",
      "PLANCK_C2_MORPHOLOGY.json","GAIA_QUAIA_FULL_SELECTION.json",
      "R90_REUSED_PROVENANCE.json","WORK_DAG_OVERLAY.json",
      "BLOCKER_RECONCILIATION.json","R1_C1_TO_R10_C10_EVIDENCE.json"
    )}

def test_private_deep_scan_all_files_exhaustive_metadata(outputs):
    c=outputs["FILE_SCAN_SUMMARY.json"]
    assert c["files_scanned"]==349040
    assert c["metadata_errors"]==0
    assert c["roots"]["Downloads"]["files"]==8534
    assert c["roots"]["workdir"]["files"]==340506
    assert c["roots"]["Downloads"]["directories"]==806
    assert c["roots"]["workdir"]["directories"]==40488
    assert c["files_tagged_candidate"]==16635

def test_private_filename_index_not_published():
    import gzip
    c=json.loads(r91.CENSUS.read_text())
    private=Path(c["private_archive"])
    assert private.parent==Path.home()/"Downloads/htt_r91_local_inventory"
    assert private.exists() and private.stat().st_size>1_000_000
    with gzip.open(private,"rt") as f:
        first=json.loads(f.readline())
    assert first["root"] in ("Downloads","workdir")
    assert not (r91.R91/private.name).exists()
    assert not (r91.ROOT/private.name).exists()

def test_original_R78_authority_and_60_partition_preserved(outputs):
    dag,old=r91.baseline()
    assert r91.sha(r91.R78)==r91.EXPECTED_R78
    assert len(dag["nodes"])==60 and len(dag["edges"])==129
    assert len(old)==60
    j=outputs["WORK_DAG_OVERLAY.json"]
    assert len(j["items"])==60
    assert not j["historical_60_science_complete"]
    assert j["science_Next_ID"]=="SQ-CF4"
    assert not any(v["original_R78_science_state_mutated"] for v in j["items"])
    assert not any(v["publication_acceptance_promoted"] for v in j["items"])

def test_all_six_and_all_seven_cross_phy_preserved(outputs):
    x=outputs["WORK_DAG_OVERLAY.json"]
    assert set(x["papers"])==set(r91.PAPERS)
    assert set(x["cross_seven_PHY"])==r91.PHY
    assert set(x["solver_dependent_original_ids"])==r91.TRANSFER
    assert {y["id"] for y in x["items"]}=={v["id"] for v in json.loads(r91.R78.read_text())["nodes"]}

def test_every_new_evidence_reference_points_to_existing_source(outputs):
    x=outputs["WORK_DAG_OVERLAY.json"]
    for row in x["items"]:
        for ref in row["r91_new_evidence_refs"]:
            name=ref.split("#")[0]
            assert (r91.R91/name).is_file(),ref

def test_R36_formal_qual_scope_not_full_physics(outputs):
    c=outputs["CF4_EXISTING_PV_REQUALIFIED.json"]
    assert c["historical_R36_product_status"]=="FORMALLY_QUALIFIED_SCOPED_CONDITIONAL_PRODUCT"
    assert c["n_same_CF4_selected_groups"]==35970
    assert c["PV_modes"]["pv_source_all_radii_shape"]==[108,108]
    assert c["physics_scope"]["partial_S_PV"]=="KNOWN_CONDITIONAL_SOURCE_MODELED"
    assert c["physics_scope"]["full_S_PV"]!="PASS"
    assert c["physics_scope"]["original_SQ_CF4"]=="BLOCKED_INPUT"
    assert c["R89_H03_raw_theta_max_abs_diff"]<1e-9

def test_R36_Fourier_gram_and_full_cross_windows(outputs):
    c=outputs["CF4_EXISTING_PV_REQUALIFIED.json"]["PV_modes"]
    assert c["PV_factor_checks"]["band1_R5"]["relative_frobenius_error"]<5e-8
    assert c["PV_factor_checks"]["band2_R5"]["relative_frobenius_error"]<5e-8
    assert c["R5_PV_min_eigen"]>0
    assert c["cross_over_diagonal_frob_norm"]>.5
    assert c["R5_PV_trace_units_km_s_Mpc_squared"]==pytest.approx(17.0583503226,abs=1e-9)

def test_R36_conditional_chi2_independent_gls_agrees(outputs):
    c=outputs["CF4_EXISTING_PV_REQUALIFIED.json"]
    assert c["R36_refitted_shared_nine_chi2"]==pytest.approx(c["R36_historical_shared_nine_chi2"],abs=1e-9)
    assert c["R36_refitted_shared_nine_chi2"]==pytest.approx(80.1376902394,abs=1e-8)

def test_R27_seven_method_quotient_not_upstream(outputs):
    r=outputs["CF4_EXISTING_PV_REQUALIFIED.json"]["R27_source_conditional_calibration_factor"]
    assert len(r["channels"])==7 and r["n_group_ids"]==35970
    assert r["factor_rows"]==35019
    assert "NOT upstream MCMC" in r["identified"]

def test_post_intercalibration_gauge_nonidentifiable():
    rng=np.random.default_rng(733)
    M=rng.normal(size=(20,7))
    raw=rng.normal(size=20)
    delta=rng.normal(size=7)
    eta=rng.normal(size=7)
    np.testing.assert_allclose(raw+M@delta,raw-M@eta+M@(delta+eta),atol=1e-14)

def test_pliklite_official_613_data_and_fixed_theory(outputs):
    z=outputs["PLIKLITE_BASELINE.json"]
    assert z["bands"]["tt"]["n_bins"]==215
    assert z["bands"]["te"]["n_bins"]==199
    assert z["bands"]["ee"]["n_bins"]==199
    assert z["bands"]["total"]["n_bins"]==613
    assert z["bands"]["total"]["chi2"]==pytest.approx(585.474565887,abs=1e-7)
    assert z["CAMB_boltzmann_executed"] is False
    assert z["cmb_morphology_information"]=="ABSENT_C_ELL_MARGINAL_ONLY"

def test_pliklite_cov_binary_real_SPD():
    with FortranFile(plik.DATA/"c_matrix_plik_v22.dat") as f:
        raw=f.read_reals(np.float64).reshape(613,613)
    C=np.tril(raw)+np.tril(raw,-1).T
    assert np.max(np.abs(C-C.T))<1e-15
    assert np.linalg.cholesky(C).shape==(613,613)

def test_pliklite_analytic_one_scalar_calibration_profile(outputs):
    d=outputs["PLIKLITE_BASELINE.json"]
    prof=d["bands"]["conditional_fixed_theory_calibration_profile"]
    assert prof["A_planck_MLE"]==pytest.approx(1.0008328706681575,abs=1e-9)
    assert prof["chi2_profile_min"]<=d["bands"]["total"]["chi2"]
    # direct independent result at profiled amplitude
    res=plik.compute(prof["A_planck_MLE"])
    assert res["bands"]["total"]["chi2"]==pytest.approx(prof["chi2_profile_min"],abs=2e-7)
    assert prof["chi2_improvement_A1_to_MLE"]>0

def test_pliklite_TT_TE_EE_marginals_are_not_additive_to_full_chi2(outputs):
    j=outputs["PLIKLITE_BASELINE.json"]["bands"]
    s=sum(j[q]["marginal_block_chi2"] for q in ("tt","te","ee"))
    assert abs(s-j["total"]["chi2"])>1e-2

def test_planck_equal_C2_distinct_SO3_orbits(outputs):
    d=outputs["PLANCK_C2_MORPHOLOGY.json"]
    qa=d["examples"]["axisymmetric_eigenvalue"]
    qb=d["examples"]["zero_eigenvalue_biaxial"]
    assert qa["signed_shape_chi"]==pytest.approx(1.,abs=1e-14)
    assert qb["signed_shape_chi"]==pytest.approx(0.,abs=1e-14)
    assert qa["C2_analytical_K2"]==pytest.approx(qb["C2_analytical_K2"],rel=1e-14)
    assert d["max_rel_c2_numerical_error"]<1e-10
    assert not d["observed_family_identification"]

def test_planck_C2_equal_at_multiple_pixelizations():
    p32=cl.analyze(32)
    p64=cl.analyze(64)
    assert p32["source_observed_PR3_Commander_master_C2_K2"]==p64["source_observed_PR3_Commander_master_C2_K2"]
    assert p32["max_rel_c2_numerical_error"]<1e-10
    assert p64["max_rel_c2_numerical_error"]<1e-10

def test_gaia_all_clean_634233_source_and_48_patch(outputs):
    g=outputs["GAIA_QUAIA_FULL_SELECTION.json"]
    assert g["source_total"]==692154
    assert g["n_clean_full_source"]==634233
    assert g["n_active_jackknife_patches"]==48
    assert g["same_quaia_G20_source_selection_exact"]
    assert g["strong_claims"]["source_corrected_cosmic_shear"] is False

def test_gaia_selection_multiplication_is_not_ipw(outputs):
    g=outputs["GAIA_QUAIA_FULL_SELECTION.json"]
    fit=g["fits"]
    assert set(fit)==set(gaia.MODES)
    base=fit["inverse_noise"]["mode_amplitudes_microasyr"]["E2"]
    assert base==pytest.approx(6.41269030667,abs=1e-5)
    assert 0<fit["multiply_selection_s"]["delta_vs_inverse_noise_mode_norm_microasyr"]["E2"]<2
    assert fit["ipw_floor_0p20"]["delta_vs_inverse_noise_mode_norm_microasyr"]["E2"]>1
    assert "NOT inverse propensity" in g["source_weighting_models"]["multiply_selection_s"]

def test_gaia_robust_covariances_present_and_symmetric(outputs):
    g=outputs["GAIA_QUAIA_FULL_SELECTION.json"]
    for z in g["fits"].values():
        assert z["n_sky_patches"]==48
        c=np.asarray(z["jackknife_E2_B2_cov"])
        np.testing.assert_allclose(c,c.T,atol=1e-10)
        assert c.shape==(10,10)
        assert np.linalg.eigvalsh(c).min()>-1e-8

def test_data_discovery_reuses_qualified_source_no_PR4_bulk(outputs):
    z=outputs["SOURCE_DISCOVERY.json"]
    x={y["name"]:y for y in z["rows"]}
    assert x["legacy_CF4_R36_partial_PV"]["status"]=="EXISTS_CONTENT_VERIFIED"
    assert x["Planck_2018_pliklite_data"]["status"]=="EXISTS_CONTENT_VERIFIED"
    assert x["Planck_2018_lowE_native"]["status"]=="EXISTS_CONTENT_VERIFIED"
    assert "NOT AniCLASS" in x["CLASS40GHz_instrument_response_not_Bianchi_solver"]["role"]
    assert z["downloaded_bytes_this_run"]==0
    assert z["no_full_PR4_requested"] and z["no_extdrive_writes"]

def test_reused_provenance_unchanged(outputs):
    for k,row in outputs["R90_REUSED_PROVENANCE.json"].items():
        assert r91.sha(Path(row["path"]))==row["sha256"]

def test_r91_twenty_stages_scoped_not_60science_PASS(outputs):
    t=outputs["R1_C1_TO_R10_C10_EVIDENCE.json"]
    assert [x["id"] for x in t["theory"]]==[f"R{i}" for i in range(1,11)]
    assert [x["id"] for x in t["coding"]]==[f"C{i}" for i in range(1,11)]
    assert t["native_subagent"].startswith("NOT_RUN")
    assert not t["full_60_science_completed"]

def test_blockers_still_not_assumed_resolved(outputs):
    d=outputs["BLOCKER_RECONCILIATION.json"]
    assert d["SQ_CF4"]["original_science_gate"]=="BLOCKED_INPUT"
    assert d["P2"]["original_L03_gate"]=="BLOCKED_INPUT"
    assert d["P6"]["original_K03_gate"].startswith("BLOCKED")
    assert d["remaining_native_transfer_bundles"]==2

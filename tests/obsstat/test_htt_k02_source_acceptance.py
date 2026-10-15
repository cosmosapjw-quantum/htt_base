"""Real CF4 35,970 K02 source response family and scientific-scope admission."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
RESULT=PUB/"results/K02_cf4_transfer_uncertain_v1"
SOURCE=ROOT/"docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"


def data():
    return json.loads((RESULT/"result.json").read_text())


def test_real_CF4_35970_four_source_kernels_and_original_schur_regression():
    x=data()
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==x["source_CF4_group_npz_sha256"]
    assert x["source_CF4_groups"]==35970
    assert x["one_source_catalogue_realizations"]==1
    assert x["source_methods"]==["FP","OTHER","SN","TF"]
    assert x["physical_identification_ranks"]["CF4_apparent_STF_given_fixed_kernel_and_standard_nuisance"]==5
    assert len(x["actual_sky_source_matched_response_families"])==4
    assert x["exact_old_CF4_schur_regression"]["apparent_STF_5vector_maxabs"]<1e-12
    assert x["exact_old_CF4_schur_regression"]["5x5_working_covariance_maxabs"]<1e-12
    for case in x["actual_sky_source_matched_response_families"].values():
        assert case["source_schur_apparent_rank"]==5
        assert case["nuisance_rank"]==14
        assert len(case["source_scoped_STF_gamma_dimensionless"])==5
        assert len(case["relative_information_eigenvalues"])==5
        assert all(0<y<=1+1e-10 for y in case["relative_information_eigenvalues"])
        assert case["transfer_shape_not_physical"].startswith("NOT_CALIBRATED")


def test_model_radial_shape_effects_and_stf_orientation():
    a=data()["actual_sky_source_matched_response_families"]
    assert a["unit_angular_endpoint"]["apparent_frobenius_5norm"]==pytest.approx(
        .03325774236166816,rel=1e-13)
    assert a["linear_z_over_0p05"]["apparent_frobenius_5norm"]==pytest.approx(
        .031390148516744376,rel=1e-13)
    assert a["reciprocal_0p05_over_z"]["apparent_frobenius_5norm"]==pytest.approx(
        .016006705964997755,rel=1e-13)
    assert a["reciprocal_0p05_over_z"]["source_STF_to_baseline_direction_cosine"]==pytest.approx(
        .8877476202356417,rel=1e-13)
    assert a["early_late_1plusz"]["source_STF_to_baseline_direction_cosine"]>.9999
    assert a["linear_z_over_0p05"]["relative_information_eigenvalues"][0]<.2
    assert a["reciprocal_0p05_over_z"]["relative_information_eigenvalues"][0]>.7


def test_unrestricted_gain_refit_has_no_physical_Sigma_amplitude_bound():
    x=data()
    ref=x["actual_sky_source_matched_response_families"]["unit_angular_endpoint"]["apparent_frobenius_5norm"]
    g=x["unknown_physical_transfer_overall_gain"]
    assert g["gain_lambda_allowed"]=="ANY_POSITIVE_UNCALIBRATED"
    assert g["physical_Sigma_amplitude_identified_interval"]=="UNBOUNDED_FROM_THIS_INPUT_MODEL"
    asserts=[.1,1.,10.]
    assert [c["declared_unverified_transfer_gain"] for c in g["same_actual_group_data_recomputed_gain_tests"]]==asserts
    for e in g["same_actual_group_data_recomputed_gain_tests"]:
        assert e["source_refitted_apparent_STF_frobenius_norm"]==pytest.approx(ref/e["declared_unverified_transfer_gain"],rel=1e-12)
        assert e["maxabs_gamma_scaling_identity"]<1e-12
        assert e["maxabs_covariance_scaling_identity"]<1e-11
        assert e["maxabs_relative_information_identity"]<1e-12


def test_actual_source_method_quadrupole_worstcase_nuisance_eliminates_global_STF():
    x=data()["method_specific_angular_STF_calibration_nuisance_counterexample"]
    assert x["source_method_order"]==["FP","OTHER","SN","TF"]
    assert x["source_method_nuisance_rank"]==20
    assert x["global_STF_identified_rank_if_unrestricted_method_STF_allowed"]==0
    assert x["number_unidentified_global_STF_columns"]==5
    assert x["relative_projected_global_STF_norm"]<1e-13
    assert x["source_exact_B_minus_sum_Bm_maxabs"]==0
    assert len(x["source_STF_mag_per_method_gain_5x20_matrix"])==5
    assert x["common_source_invariance_maxabs"]<1e-12
    assert x["physical_source_occurrence"].startswith("NOT_MEASURED")
    assert x["hypothetical_common_method_quadrupole_alias_gamma_frobenius_norm"]==pytest.approx(.03/(5/np.log(10)),rel=1e-12)


def test_K02_real_source_injection_exact_and_k01_optical_boundary_preserved():
    d=data()
    assert d["conditional_STF_source_injection"]["source_gamma_shift_observed_plus_injection_maxabs"]<5e-13
    assert d["source_K01_local_photon_rule"].startswith("-d ln E/dt_u")
    assert d["physical_identification_ranks"]["one_event_omega3_direct_radial"]==0
    assert d["physical_identification_ranks"]["physical_sigma_amplitude"].startswith("UNBOUNDED")
    assert d["legacy_statistical_program"]["omega_A_beta"].startswith("UNKNOWN")
    assert d["Planck_CF4_joint_likelihood"].startswith("NOT_PRODUCED")
    assert d["actual_Cosmological_shear_vorticity_accel_beta_measurement"]=="NONE"
    assert d["scientific_Journal_submission"]=="NOT_READY_TO_SUBMIT"
    with np.load(RESULT/"cf4_transfer_conditional_stf.npz",allow_pickle=False) as x:
        assert x["source_group_ids"].shape==(35970,)
        assert x["conditional_five_STF"].shape==(4,5)
        assert x["conditional_source_cov"].shape==(4,5,5)
        assert x["relative_information_eigenvalues"].shape==(4,5)
        assert x["method_angular_calibration_alias"].shape==(5,20)


def test_DAG_K02_scope_complete_but_real_physical_likelihood_absent():
    doc=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    tasks={x["id"]:x for x in doc["nodes"]}
    assert tasks["K01"]["state"]=="completed_scoped"
    assert tasks["K02"]["state"]=="completed_scoped"
    assert tasks["K03"]["external_missing"]
    assert tasks["K04"]["external_missing"]
    assert tasks["K05"]["state"]=="pending"
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in doc["papers"])

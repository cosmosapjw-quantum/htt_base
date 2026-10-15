"""Actual source K1-FFP10 and Planck mask high-l Schur acceptance tests."""
import json
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
V1=PUB/"results/L01_schur_999cmb_300noise_v1"
V2=PUB/"results/L01_schur_999cmb_300noise_v2"


def current():
    return json.loads((V2/"result.json").read_text())


def test_real_ffp10_999_and_300_source_ids_and_exact_pixel_contract():
    z=current()
    assert z["actual_CMB_physical_sky_count"]==1
    assert z["FFP_CMB_unique_source_realizations"]==999
    assert z["FFP_noise_unique_source_realizations"]==300
    assert z["FFP_CMB_noise_source_unique_id_paired"]==300
    assert z["source_simulation_pairing_status"].startswith("EXACT_IDENTICAL")
    assert z["source_mask_selected_pixel_count"]==26846
    assert len(set(z["FFP_CMB_source_ids"]))==999
    assert len(set(z["FFP_noise_source_ids"]))==300
    assert z["FFP_CMB_source_ids"][:300]==z["FFP_noise_source_ids"]
    assert z["real_harmonic_ellmax_fitted"]==[5,8,10,12]
    assert len(z["native_temperature_mask"])==3


def test_same_data_source_output_real_999plus300_schur_precision():
    z=current()
    s=z["source_geometry"]
    assert s["restricted_columns"]==36 and s["high_columns"]==133
    assert .02<s["profile_information_min"]<.03
    assert .60<s["profile_information_median"]<.70
    assert s["full_design_condition"]<30
    assert s["low_ell2to3_high_nuisance_norm"]==1.6586530089000684
    assert all(err<1e-12 for err in z["Schur_identity_relative_residual_by_bank"].values())
    assert z["nominal_isotropic_beam_pixel_scenario"]["scope"].startswith("DECLARED_NOMINAL")


def test_actual_legacy_teff_morphology_shift_and_separate_source_groups():
    z=current()
    a=z["source_summaries"]["observed_single_sky"]
    assert a["5"]["features"]["s3"]["absolute"]["median"]<0
    assert a["12"]["features"]["s3"]["absolute"]["median"]>0
    assert a["12"]["features"]["s3"]["paired_minus_lmax5"]["median"]>0.5
    assert a["12"]["features"]["k4"]["paired_minus_lmax5"]["median"]>.20
    assert z["independent_CF4_actual_source_context"]["no_joint_likelihood_with_planck"] is True
    assert z["independent_CF4_actual_source_context"]["no_physical_shear_from_CF4_window"] is True
    assert z["legacy_MES_kinematical_x_F_Pi_Q_Gf"]=="NOT_IDENTIFIED_FROM_CMB_MODEL_F4_OR_MASK_RESPONSE"
    assert z["Planck_p_value"]=="NOT_ADMITTED"
    assert z["P2_L01_scientific_state"].startswith("PENDING")
    assert z["P4_V02_scientific_state"]=="WAITING_ON_L01"


def test_source_cohort_RMS_shift_and_retrospective_abs_rank_not_anomaly_p():
    z=current()
    x=z["source_summaries"]
    c=x["FFP_CMB_signal_only"]["12"]["features"]["s3"]["paired_minus_lmax5"]
    assert c["rms"]>0.25
    assert c["n"]==999
    assert x["FFP_noise_only"]["12"]["features"]["s3"]["paired_minus_lmax5"]["rms"]>.30
    assert x["FFP_same_id_CMB_plus_noise"]["12"]["features"]["k4"]["paired_minus_lmax5"]["rms"]>.30
    q=z["retrospective_observed_lmax5_to12_delta_abs_ranks_NOT_P"]
    assert 0<q["s3"]["cohort_descriptive_conditioned_abs_rank"]["signal_999"]["descriptive_fraction_abs_ge"]<.5
    assert 0<q["k4"]["cohort_descriptive_conditioned_abs_rank"]["signal_999"]["descriptive_fraction_abs_ge"]<.7
    for stat in ("s3","k4"):
        for key in ("signal_999","noise_300","paired_signal_plus_noise_300"):
            assert q[stat]["cohort_descriptive_conditioned_abs_rank"][key]["source_null_p"].startswith("NOT_ADMITTED")


def test_full_v1_vs_v2_same_scientific_outcomes_and_saved_arrays():
    first=json.loads((V1/"result.json").read_text())
    second=current()
    for key in ("runtime_elapsed_seconds","runtime_peak_RSS_KiB"):
        first.pop(key,None)
        second.pop(key,None)
    second.pop("source_simulation_pairing_status")
    second.pop("retrospective_observed_lmax5_to12_delta_abs_ranks_NOT_P")
    assert first==second
    with np.load(V1/"source_lowell_nested_999plus300.npz",allow_pickle=False) as a:
        with np.load(V2/"source_lowell_nested_999plus300.npz",allow_pickle=False) as b:
            assert a.files==b.files
            for key in a.files:
                np.testing.assert_array_equal(a[key],b[key])
            assert a["cmb_l12_36"].shape==(999,36)
            assert a["noise_l12_36"].shape==(300,36)
            assert a["paired_l12_36"].shape==(300,36)


def test_scientific_l01_l03_and_p4_v02_not_artificially_admitted():
    doc=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    nodes={i["id"]:i for i in doc["nodes"]}
    assert nodes["L01"]["state"]=="pending"
    assert nodes["L03"]["external_missing"]
    assert nodes["V02"]["state"]=="pending"
    assert nodes["V01"]["state"]=="completed_scoped"
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in doc["papers"])

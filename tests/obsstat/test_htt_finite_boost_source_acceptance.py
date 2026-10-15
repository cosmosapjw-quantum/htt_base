"""Real Planck PR3 and CF4 source finite frame injection-scoped acceptance."""
import json
import math
from pathlib import Path
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
RESULT=ROOT/"docs/research_program/observational_publication_20261015/results/V01_planck_cf4_finite_boost_v3/result.json"
PUB=ROOT/"docs/research_program/observational_publication_20261015"


def real_source():
    return json.loads(RESULT.read_text())


def test_nine_same_sky_exact_real_harmonic_source_boost_decomposition():
    x=real_source()
    assert len(x["actual_same_sky_source_processing_by_product"])==9
    assert x["one_actual_CMB_sky_with_processing_products"]==9
    assert x["physical_claim"]=="EVENT_LOCAL_OBSERVER_BOOST_AND_CONDITIONAL_SAME_SOURCE_PIPELINE_ONLY_NOT_GLOBAL_TILT"
    common_difference=None
    for name,z in x["actual_same_sky_source_processing_by_product"].items():
        assert len(z["source_baseline_ell2_5_real_microK"])==12
        assert len(z["boosted_source_ell2_5_real_microK"])==12
        assert z["l2_source_delta_norm_microK"]<.2
        assert z["l3_source_delta_norm_microK"]<.2
        diff=(np.asarray(z["boosted_source_with_kinetic_monopole_ell2_5_real_microK"])-
              np.asarray(z["boosted_source_ell2_5_real_microK"]))
        np.testing.assert_allclose(
            diff[:5],
            x["finite_kinematic_monopole_to_observer"]["projected_l2_real_microK"],
            atol=1e-10)
        # The boosted T0 monopole also makes an O(beta^3) octupole, NOT zero.
        assert np.linalg.norm(diff[5:])<.02
        if common_difference is None:
            common_difference=diff
        else:
            np.testing.assert_allclose(diff,common_difference,atol=3e-14)


def test_measured_Planck_dipole_source_is_not_intrinsic_radiation_eps1():
    x=real_source()
    p=x["local_dipole_parameter_source"]
    assert p["amplitude_microK"]==3362.08
    assert p["galactic_longitude_deg"]==264.021
    assert p["galactic_latitude_deg"]==48.253
    assert p["amplitude_is_first_order_velocity_reference"] is True
    d=x["finite_kinematic_monopole_to_observer"]
    assert d["projected_dipole_norm_microK"]==pytest.approx(3362.08,abs=.01)
    assert d["dipole_axis_dot_source_Galactic"]==pytest.approx(1.,abs=1e-12)
    assert d["analytic_l2_STF_maxabs_residual_microK"]<2e-5
    assert x["observed_lowell_source_status"].startswith("Already observed/dipole-subtracted")


def test_source_Legacy_teff_exact_kinematic_monopole_is_not_physical_x():
    x=real_source()
    ff=x["exact_legacy_F4_of_local_boosted_pure_monopole"]
    b=x["counterfactual_beta_OR_velocity_fraction"]
    assert ff["deltaF4"]==pytest.approx(4*b*b/(3*(1-b*b)),rel=1e-14)
    assert ff["deltaF4"]==pytest.approx(2.0289413113238506e-6,rel=1e-14)
    assert x["actual_same_sky_source_processing_by_product"]["SMICA_FULL"]["baseline_legacy_f4_l2l3_source_conditional"]<3e-10
    assert x["CMB_plus_CF4_joint_posterior"]=="NOT_CONSTRUCTED"
    assert x["global_tilt_history_source_response"].startswith("ABSENT")


def test_frame_relative_velocity_rank_nullspace_does_not_claim_global_no_go():
    x=real_source()
    a=x["one_event_local_global_velocity_identifiability"]
    assert a["rank"]==3 and a["nullspace_dimension"]==3
    assert a["nullspace_residual_maxabs"]<1e-13
    np.testing.assert_allclose(a["singular_values"],[np.sqrt(2)]*3,atol=3e-6)
    assert "one event" in a["assumptions"]
    assert "global" not in a["physics"].lower()
    r=x["frame_triad_source_contract"]
    assert r["source_scalar_rel_speed"]==pytest.approx(
        x["counterfactual_beta_OR_velocity_fraction"],rel=1e-13)
    assert r["beta_RM_R_in_matter_M_tetrad"]==[0,0,0]


def test_real_CF4_source_frame_projection_is_only_counterfactual():
    x=real_source()
    y=x["CF4_J2000_hypothetical_observer_bulk_projection"]
    assert y["source_CF4_group_count"]==35970
    assert len(y["delta_logH_by_window_if_false_uncorrected_observer_velocity"])==7
    assert len(y["predeclared_windows"])==7
    assert "NO_DOUBLE_APPLICATION" in y["semantic_status"]
    assert x["CF4_cartesian_frame"].startswith("ICRS J2000")
    assert x["SMICA_cartesian_frame"].startswith("GALACTIC")
    raw=PUB/"results/H01_actual_cf4_v1/result.json"
    a=json.loads(raw.read_text())
    v=np.asarray(y["hypothetical_J2000_bulk_velocity_km_s"])
    response=np.asarray(a["fit"]["bulk_response_per_km_s"])
    np.testing.assert_allclose(response@v,
        y["delta_logH_by_window_if_false_uncorrected_observer_velocity"],atol=1e-15)


def test_unmodified_publication_gate_prevents_physical_tilt_posterior_promotion():
    x=real_source()
    assert x["CMB_instrument_noise_beam_high_l_observation_likelihood"]=="NOT_CONSTRUCTED"
    assert x["CF4_physical_velocity_selection_likelihood"]=="NOT_CONSTRUCTED"
    assert x["manuscript_ready"]=="NO"
    dag=json.loads((PUB/"PUBLICATION_DAG.json").read_text())
    tasks={n["id"]:n for n in dag["nodes"]}
    assert tasks["V01"]["state"]=="completed_scoped"
    assert tasks["V03"]["external_missing"]
    assert tasks["V02"]["state"]=="pending"
    assert all(p["publication_status"]=="NOT_READY_TO_SUBMIT" for p in dag["papers"])

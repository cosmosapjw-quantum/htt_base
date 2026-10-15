"""Source FFP10 simulation HTT partial pushforward and sharp corner checks."""
import hashlib,json
from pathlib import Path
import numpy as np
import pytest
from obsstat.s02_ffp_source_partial_pushforward import (
    SourceSimulationPartialError,source_mes_box,scalar_mes_regression,
    pi_box_strict,descriptive_summary
)
from obsstat.publication_functionals import finite_functional_image

ROOT=Path(__file__).resolve().parents[2]
PUB=ROOT/"docs/research_program/observational_publication_20261015"
R=PUB/"results/S02_ffp999_empirical_partial_v1"

def test_multipole_scalar_vs_vector_geodesic_MES_c1c2_only():
    e=np.array([[1.0e-5,2.0e-5],[2.0e-5,3.0e-5],[1e-7,5e-5]])
    b=source_mes_box(e,[101,102,103])
    assert scalar_mes_regression(e)["maxabs"]<2e-22
    np.testing.assert_allclose(b["U_sigma"],
        1.5*(3*e[:,0]+3*e[:,1]/7)**2,rtol=2e-15)
    np.testing.assert_allclose(b["U_omega"],1.5*(2*e[:,0]/15)**2)
    assert b["source_status"].endswith("NOT_COSMOLOGICAL_POSTERIOR")

def test_weighted_strict_tails_are_exact_math_box_not_data_p():
    a=np.array([[1e-5,2e-5],[4e-5,1e-5]])
    b=source_mes_box(a,[1,2],weights=np.array([.3,.7]))
    lo=b["q_low"]
    assert lo[0]!=lo[1]
    t=np.sort(np.array([min(lo)-.01,(lo[0]+lo[1])/2,0.,.5,1.]))
    p=pi_box_strict(b,t)
    assert p["lower"][0]==pytest.approx(1)
    assert p["upper"][0]==pytest.approx(1)
    assert p["upper"][-1]==0
    assert np.any((p["lower"]>0)&(p["lower"]<1))
    assert np.all(p["full_Q_lower"]==0)
    assert np.all(p["full_Q_upper"]==1)
    assert p["corner_witness_maxabs"]<1e-13

def test_bad_weights_duplicate_sources_and_invalid_thresholds_rejected():
    e=np.array([[1e-5,2e-5],[1e-5,1e-5]])
    with pytest.raises(SourceSimulationPartialError):
        source_mes_box(e,[1,1])
    with pytest.raises(SourceSimulationPartialError):
        source_mes_box(e,[1,2],weights=[.5,.4])
    with pytest.raises(SourceSimulationPartialError):
        source_mes_box(np.array([[0.,0.]]),[1])
    b=source_mes_box(e,[1,2])
    with pytest.raises(SourceSimulationPartialError):
        pi_box_strict(b,[0.,0.,1.])

def test_real_source_999_CMB_and_300_paired_FFP10_ids_and_exact_law():
    with np.load(R/"ffp10_mes_conditional_pi_source.npz",allow_pickle=False) as z:
        assert len(set(map(int,z["cmb_ids"])))==999
        np.testing.assert_array_equal(z["cmb_ids"][:300],z["noise_ids"])
        e=z["eps_masked"];epspair=z["eps_paired"]
        assert e.shape==(999,2) and epspair.shape==(300,2)
        b=source_mes_box(e,z["cmb_ids"])
        np.testing.assert_array_equal(b["U_sigma"],z["masked_USigma"])
        np.testing.assert_array_equal(b["U_omega"],z["masked_UOmega"])
        np.testing.assert_array_equal(b["q_low"],z["masked_Q_box_low"])
        tail=pi_box_strict(b,z["thresholds"])
        np.testing.assert_allclose(tail["lower"],z["masked_pi_box_lower"],atol=2e-14)
        np.testing.assert_allclose(tail["upper"],z["masked_pi_box_upper"],atol=2e-14)

def test_real_result_preserves_100_percent_unknown_physically_signed_sectors():
    a=json.loads((R/"result.json").read_text())
    assert a["simulated_CMB_distinct_ids_count"]==999
    assert a["observed_actual_CMB_sky_count"]==1
    assert a["source_paired_signal_noise_cmb_ids_equal"] is True
    assert a["processing_products_are_independent_latent_observations"] is False
    v=a["registered_original_HTT_partial_functions_on_same_999_simulations"]
    assert v["missing_mass"]=={"x_C":1.,"Q":1.,"F":1.}
    assert all(row["unconditional_outer_interval"]==[0.,1.]
       for row in v["Pi_Q_at_predeclared_thresholds"])
    assert v["G_F_generic_unknown_depth_F_outer"]["point_identified"] is False
    assert v["G_F_generic_unknown_depth_F_outer"]["outer_interval"]==[.05,20.]
    assert a["physical_full_Pi_Q_at_any_finite_threshold"]==[0.,1.]
    assert a["physical_shear_vorticity_curvature_tilt_posterior"]=="ABSENT"
    assert a["actual_CF4_apparent_STF_used_as_physical_shear"] is False

def test_earlier_observed_sky_processing_algebra_has_separate_ownership():
    a=json.loads((R/"result.json").read_text())
    previous=PUB/"results/S02_real_planck_typed_partial_v1/result.json"
    assert hashlib.sha256(previous.read_bytes()).hexdigest()==a["previous_observed_one_sky_S02_sha256"]
    old=json.loads(previous.read_text())
    assert old["source_sky_realization_count"]==1
    assert old["source_processing_product_count"]==9
    assert old["processing_product_weights_or_Bayesian_probability"]=="NOT_ASSIGNED"

"""Exact normalized finite l2+l3 Teff quartic moments and source chart tests."""
import numpy as np
import pytest
from obsstat.legacy_teff_octupole_exact import (
    TeffOctupoleError,moment_delta_l23,
)
from obsstat.legacy_teff_tensor_observation_bridge import (
    legacy_f4_exact_increment,
    masked_planck_quadrupole_to_temperature_stf,
    T0_MICROK,
)


def test_ell2_only_octupole_extension_recovers_exact_original_tensor_F4():
    rng=np.random.default_rng(1)
    a=np.zeros((14,12))
    a[:,:5]=rng.normal(size=(14,5))*12.
    got=moment_delta_l23(a)
    S=masked_planck_quadrupole_to_temperature_stf(a[:,:5])
    expect=legacy_f4_exact_increment(np.zeros((14,3)),S)["delta_F4"]
    np.testing.assert_allclose(got["deltaF4"],expect,rtol=3e-13,atol=4e-24)
    np.testing.assert_allclose(got["variance"],got["quad_variance_analytic"],rtol=3e-13)
    assert np.max(abs(got["deltaF4_morphology_coupling"]))<2e-25


def test_pure_l3_has_no_cubic_moment_by_angular_parity():
    a=np.zeros((3,12))
    a[0,5]=11.;a[1,7]=21.;a[2,6:12]=np.linspace(-13,7,6)
    got=moment_delta_l23(a)
    assert max(abs(got["cubic"]))<5e-25
    np.testing.assert_allclose(got["variance"],got["octupole_variance_analytic"],
                               rtol=3e-13,atol=1e-22)
    assert np.all(got["deltaF4"]>0)


def test_mixed_l2_l3_coupling_is_not_independent_evidence():
    a=np.zeros((1,12))
    a[0,:5]=[17.,4.,-7.,3.,9.]
    a[0,5:12]=[-8.,12.,-5.,3.,6.,2.,10.]
    q=moment_delta_l23(a)
    assert abs(float(q["deltaF4_morphology_coupling"][0]))>1e-20
    assert q["deltaF4"][0] > 0
    assert q["deltaF4"][0]==pytest.approx(
        q["deltaF4_quad_only"][0]+q["deltaF4_oct_only"][0]+
        q["deltaF4_morphology_coupling"][0],abs=2e-25)


def test_independent_gauss_and_phi_order_refinement():
    rng=np.random.default_rng(27)
    a=rng.normal(size=(9,12))*19.
    q=moment_delta_l23(a,n_mu=16,n_phi=32)
    ref=moment_delta_l23(a,n_mu=24,n_phi=48)
    for name in ("deltaF4","variance","cubic","quartic","deltaF4_quad_only",
                 "deltaF4_oct_only"):
        np.testing.assert_allclose(q[name],ref[name],rtol=1e-11,atol=3e-24)


def test_input_chart_rejects_false_multipole_layout():
    with pytest.raises(TeffOctupoleError):
        moment_delta_l23(np.zeros((3,11)))
    with pytest.raises(TeffOctupoleError):
        moment_delta_l23(np.ones((2,12))*np.inf)
    with pytest.raises(TeffOctupoleError):
        moment_delta_l23(np.zeros((1,12)),n_mu=5,n_phi=16)



def test_power_shape_decomposition_exact_c_l_and_jensen():
    from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
    rng=np.random.default_rng(45)
    x=rng.normal(size=(15,12))*21
    q=quartic_power_shape_decomposition(x)
    m=moment_delta_l23(x)
    np.testing.assert_allclose(q["source_bandpower_variance"],
                               (x*x).sum(axis=1)/(4*np.pi*T0_MICROK**2),
                               rtol=2e-14,atol=1e-24)
    np.testing.assert_allclose(q["power_only_6variance"]+
                               q["shape_excess_4cubic_plus_quartic"],
                               m["deltaF4"],rtol=2e-13,atol=2e-24)
    assert np.all(q["normalized_kurtosis"]>=1.0)
    assert q["source_notes"]["physical_null_p"]=="WITHHELD"


def test_power_shape_scaling_and_parity():
    from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
    rng=np.random.default_rng(139)
    x=rng.normal(size=(8,12))*7.
    q=quartic_power_shape_decomposition(x)
    r=quartic_power_shape_decomposition(3*x)
    negative=quartic_power_shape_decomposition(-x)
    np.testing.assert_allclose(q["normalized_skewness"],r["normalized_skewness"],rtol=2e-13,atol=2e-12)
    np.testing.assert_allclose(q["normalized_kurtosis"],r["normalized_kurtosis"],rtol=2e-13,atol=1e-12)
    np.testing.assert_allclose(q["normalized_skewness"],-negative["normalized_skewness"],rtol=2e-13,atol=2e-12)
    np.testing.assert_allclose(q["normalized_kurtosis"],negative["normalized_kurtosis"],rtol=2e-13,atol=1e-12)
    np.testing.assert_allclose(r["source_bandpower_variance"],9*q["source_bandpower_variance"],rtol=2e-13)


def test_shape_undefined_when_temperature_modes_zero():
    from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition
    x=np.zeros((1,12))
    q=quartic_power_shape_decomposition(x)
    assert q["deltaF4"][0]==0
    assert np.isnan(q["normalized_kurtosis"][0])
    assert np.isnan(q["normalized_skewness"][0])



def test_exact_parity_removes_all_odd_octupole_factors():
    from obsstat.legacy_teff_octupole_exact import parity_exact_l2_l3_mixed_contribution
    rng=np.random.default_rng(420)
    x=rng.normal(size=(4,12))*21.
    q=parity_exact_l2_l3_mixed_contribution(x)
    ref=moment_delta_l23(x)
    np.testing.assert_allclose(q["combined_F4_cross"],
        ref["deltaF4_morphology_coupling"],atol=2e-22,rtol=5e-8)
    for name,v in q["forbidden_parity_odd_moments"].items():
        assert np.max(np.abs(v))<1e-19,(name,v)
    assert q["difference_vs_direct_bandlimited"]<2e-22


def test_parity_analytic_cross_moment_refinement():
    from obsstat.legacy_teff_octupole_exact import parity_exact_l2_l3_mixed_contribution
    rng=np.random.default_rng(300)
    a=rng.normal(size=(2,12))*15
    x=parity_exact_l2_l3_mixed_contribution(a,n_mu=16,n_phi=32)
    y=parity_exact_l2_l3_mixed_contribution(a,n_mu=24,n_phi=48)
    np.testing.assert_allclose(x["combined_F4_cross"],
        y["combined_F4_cross"],atol=3e-22,rtol=1e-8)

"""Gaussian fixed-multipole-power angular-shape conditional null tests."""
import numpy as np
import pytest
from obsstat.teff_phase_conditioned_null import (
    PhaseConditionalDomainError,per_ell_radii,
    theoretical_uniform_phase_moments,phase_chunks_at_fixed_power,
    conditional_shape_null,source_rescale_phase_preserving,
    descriptive_source_rank
)
from obsstat.legacy_teff_octupole_exact import quartic_power_shape_decomposition


def reference():
    return np.array([12.,-3.,7.,4.,-8.,-11.,2.,7.,-6.,3.,5.,9.])


def test_pure_multipole_ideal_conditional_kurtosis_exact():
    a=reference()
    just2=a.copy();just2[5:]=0.
    just3=a.copy();just3[:5]=0.
    assert theoretical_uniform_phase_moments(just2)["theoretical_conditional_mean_k4"]==pytest.approx(15/7,rel=1e-14)
    assert theoretical_uniform_phase_moments(just3)["theoretical_conditional_mean_k4"]==pytest.approx(7/3,rel=1e-14)
    u=float(np.dot(a[:5],a[:5]));v=float(np.dot(a[5:],a[5:]))
    exact=3*((5/7)*u*u+(7/9)*v*v+2*u*v)/(u+v)**2
    x=theoretical_uniform_phase_moments(a)
    assert x["theoretical_conditional_mean_s3"]==0
    assert x["theoretical_conditional_mean_k4"]==pytest.approx(exact,rel=1e-15)
    assert sum((x["variance_fraction_l2"],x["variance_fraction_l3"]))==pytest.approx(1.)


def test_phase_draws_have_exact_fixed_norm_and_independent_band_directions():
    a=reference()
    chunks=list(phase_chunks_at_fixed_power(a,n_draws=257,seed=17,chunk_size=40))
    x=np.vstack(chunks)
    assert x.shape==(257,12)
    np.testing.assert_allclose(np.linalg.norm(x[:,:5],axis=1),
        np.linalg.norm(a[:5]),rtol=3e-15)
    np.testing.assert_allclose(np.linalg.norm(x[:,5:],axis=1),
        np.linalg.norm(a[5:]),rtol=3e-15)
    y=np.vstack(list(phase_chunks_at_fixed_power(a,n_draws=257,seed=17,chunk_size=40)))
    np.testing.assert_array_equal(x,y)
    assert len(np.unique(x,axis=0))==257


def test_conditional_kurtosis_monte_carlo_matches_independent_analytic_formula():
    a=reference()
    q=conditional_shape_null(a,n_draws=8192,seed=1812,chunk_size=256)
    assert len(q["s3"])==len(q["k4"])==8192
    assert abs(np.mean(q["s3"]))<.04
    assert abs(np.mean(q["k4"])-
               q["theory"]["theoretical_conditional_mean_k4"])<.05
    assert np.min(q["k4"])>=1-1e-10


def test_phase_null_scale_invariance_under_fixed_positive_scaling():
    x=reference()
    y=conditional_shape_null(x,n_draws=300,seed=24,chunk_size=60)
    z=conditional_shape_null(5*x,n_draws=300,seed=24,chunk_size=60)
    np.testing.assert_allclose(y["s3"],z["s3"],atol=2e-12,rtol=5e-14)
    np.testing.assert_allclose(y["k4"],z["k4"],atol=2e-12,rtol=5e-14)
    assert y["theory"]["theoretical_conditional_mean_k4"]==pytest.approx(
        z["theory"]["theoretical_conditional_mean_k4"])


def test_ffp_source_phase_reweighting_preserves_original_direction():
    rng=np.random.default_rng(42)
    x=rng.normal(size=(21,12))
    a=reference()
    z=source_rescale_phase_preserving(x,a)
    np.testing.assert_allclose(np.linalg.norm(z[:,:5],axis=1),
                              np.linalg.norm(a[:5]),rtol=2e-15)
    np.testing.assert_allclose(np.linalg.norm(z[:,5:],axis=1),
                              np.linalg.norm(a[5:]),rtol=2e-15)
    for low,high in ((0,5),(5,12)):
        orig=x[:,low:high]
        new=z[:,low:high]
        # Same phase orientation for every source row.
        align=np.sum(orig*new,axis=1)/(np.linalg.norm(orig,axis=1)*np.linalg.norm(new,axis=1))
        np.testing.assert_allclose(align,1,atol=4e-15)
    s=quartic_power_shape_decomposition(z)
    assert np.all(np.isfinite(s["normalized_skewness"]))


def test_degenerate_band_and_invalid_source_input():
    x=reference()
    x[:5]=0
    a=np.vstack(list(phase_chunks_at_fixed_power(x,n_draws=40,seed=10)))
    assert np.all(a[:,:5]==0)
    with pytest.raises(PhaseConditionalDomainError):
        theoretical_uniform_phase_moments(np.zeros(12))
    with pytest.raises(PhaseConditionalDomainError):
        list(phase_chunks_at_fixed_power(x,n_draws=0,seed=3))
    with pytest.raises(PhaseConditionalDomainError):
        list(phase_chunks_at_fixed_power(x,n_draws=3,seed=-1))
    with pytest.raises(PhaseConditionalDomainError):
        source_rescale_phase_preserving(np.zeros((3,12)),reference())
    with pytest.raises(PhaseConditionalDomainError):
        per_ell_radii(np.zeros(16))


def test_descriptive_rank_firewall_never_calls_anomaly_pvalue():
    r=descriptive_source_rank(.4,np.array([-1.,0.,.1,.2,.5]),centre=0.)
    assert r["less_or_equal_fraction"]==pytest.approx(.8)
    assert r["greater_or_equal_fraction"]==pytest.approx(.2)
    assert r["absolute_distance_from_centre_fraction_ge"]==pytest.approx(.4)
    assert r["finite_rank_minimum_if_exchangeable_only"]==pytest.approx(1/6)
    assert r["physical_null_p_value"].startswith("NOT_ADMITTED")

"""Scope: SAG tensor normalization, mask response, source image conventions."""
import math
import numpy as np
import pytest
from obsstat.mes_eps_measurement_bridge import (
    T0_MICROK, pstf_norm_factor, eps_from_retained, eps_from_real_multipole,
    geodesic_algebraic_sector_ceiling, fixed_ols_operator,
    fit_rows_of_simulated_maps, eps_arrays, gaussian_beam_l,
    EpsilonBridgeError, nested_children_coverage_to_ring,
)


def test_exact_sag_15_17_quadrupole_octupole_factors():
    assert pstf_norm_factor(2) == pytest.approx(5 * np.sqrt(3/(2*np.pi))/2, rel=1e-14)
    assert pstf_norm_factor(3) == pytest.approx(7 * np.sqrt(5/(2*np.pi))/2, rel=1e-14)
    for ell in (2,3):
        a=np.arange(1,2*ell+2,dtype=float)
        c=np.dot(a,a)/(2*ell+1)
        q=eps_from_real_multipole(a,ell)
        sag=(2*ell+1)*math.factorial(2*ell)/(2**ell*math.factorial(ell)**2)*np.dot(a,a)/(4*np.pi*T0_MICROK**2)
        assert q["SAG_eq17_covariant_rms_tensor_norm"]**2 == pytest.approx(sag,rel=5e-15)
        assert q["C_ell_microK2"] == pytest.approx(c)


def test_real_harmonic_orthogonal_rotation_invariance():
    rng=np.random.default_rng(9)
    v=rng.normal(size=32)
    transformed=v.copy()
    for ell,sl in ((2,slice(0,5)),(3,slice(5,12))):
        u,_=np.linalg.qr(rng.normal(size=(2*ell+1,2*ell+1)))
        transformed[sl]=u@v[sl]
    a=eps_from_retained(v);b=eps_from_retained(transformed)
    for ell in ("2","3"):
        assert a[ell]["SAG_eq17_covariant_rms_tensor_norm"] == pytest.approx(b[ell]["SAG_eq17_covariant_rms_tensor_norm"],rel=1e-14)


def test_source_legacy_normalization_is_not_covariant_sag_norm():
    a=np.zeros(32);a[:5]=[8.,-12.,18.,15.,2.];a[5:12]=[5.,2.,-8.,13.,-11.,4.,3.]
    q=eps_from_retained(a)
    assert q["2"]["SAG_eq17_covariant_rms_tensor_norm"] > q["2"]["sqrtCl_over_T0"]
    assert q["3"]["SAG_eq17_covariant_rms_tensor_norm"] > q["3"]["sqrtCl_over_T0"]
    s=geodesic_algebraic_sector_ceiling(
        q["2"]["SAG_eq17_covariant_rms_tensor_norm"],
        q["3"]["SAG_eq17_covariant_rms_tensor_norm"])
    assert s["Sigma2_anchor_only_if_conditions_met"] > 0
    assert s["derivative_condition"] == "UNVERIFIED_C1_C2"
    assert s["observer_residual_dipole"] == "ASSUMED_FOR_ALGEBRA_ONLY"


def test_operator_identity_and_alias_from_unmodeled_high_modes():
    rng=np.random.default_rng(302)
    x=rng.normal(size=(200,8)); mask=rng.uniform(size=200)>.27
    r,info=fixed_ols_operator(x,mask)
    np.testing.assert_allclose(r@x[mask],np.eye(8),atol=1e-13)
    b=rng.normal(size=8)
    data=np.tile(x@b,(3,1))
    fit=fit_rows_of_simulated_maps(data,mask,r)
    np.testing.assert_allclose(fit,np.tile(b,(3,1)),atol=1e-13)
    full_more=rng.normal(size=(200,4))
    assert np.linalg.norm(r@full_more[mask]) > 0
    assert info["selected_n"]==int(mask.sum())


def test_eps_array_batch_equal_scalar_and_full_harmonic():
    rng=np.random.default_rng(13);a=rng.normal(size=(20,32))
    expected=np.array([[eps_from_retained(v)[k]["SAG_eq17_covariant_rms_tensor_norm"]
                        for k in ("2","3")] for v in a])
    np.testing.assert_allclose(eps_arrays(a),expected,rtol=1e-14)
    full=np.column_stack([rng.normal(size=(20,4)),a])
    np.testing.assert_allclose(eps_arrays(full),expected,rtol=1e-14)
    np.testing.assert_allclose(eps_arrays(a[:,:12]),expected,rtol=1e-14)


def test_bounded_illustrative_beam_and_input_rejection():
    assert 0 < gaussian_beam_l(3,10) < gaussian_beam_l(3,5) < 1
    assert gaussian_beam_l(2,10) > gaussian_beam_l(3,10)
    with pytest.raises(EpsilonBridgeError):
        eps_from_retained(np.zeros(5))
    with pytest.raises(EpsilonBridgeError):
        pstf_norm_factor(2.5)
    with pytest.raises(EpsilonBridgeError):
        geodesic_algebraic_sector_ceiling(-1,0)
    with pytest.raises(EpsilonBridgeError):
        gaussian_beam_l(2,0)
    with pytest.raises(EpsilonBridgeError):
        fixed_ols_operator(np.ones((30,3)),np.ones(30,bool))



def test_nested_mask_parent_reordered_into_ring_frame():
    import healpy as hp
    nside_in, nside_out = 8, 2
    f = np.zeros(hp.nside2npix(nside_in), bool)
    target_nested = 3
    count = (nside_in // nside_out) ** 2
    f[target_nested*count:(target_nested+1)*count] = True
    coarse = nested_children_coverage_to_ring(f,nside_in=nside_in,nside_out=nside_out)
    assert np.count_nonzero(coarse) == 1
    assert coarse[hp.nest2ring(nside_out,target_nested)] == pytest.approx(1)
    assert hp.nest2ring(nside_out,target_nested) != target_nested
    with pytest.raises(EpsilonBridgeError):
        nested_children_coverage_to_ring(f.astype(float),nside_in=nside_in,nside_out=nside_out)

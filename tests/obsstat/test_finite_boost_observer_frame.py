"""Exact Lorentz scalar/aberration/blackbody finite observer bridge tests."""
import numpy as np
import pytest
from obsstat.finite_boost_observer_frame import (
    C_KM_S,FrameBoostError,checked_beta,gamma_beta,
    minkowski_norm,lorentz_to_moving,lorentz_to_parent,
    photon_normal_to_moving,photon_moving_to_normal,
    boosted_sky_temperature,relative_velocity_of_A_measured_in_B,
    four_velocity,frame_triad,legacy_rapidity_and_velocity_fraction,
    galactic_dipole_unit_vector
)


def test_one_axis_photon_aberration_and_doppler_exact():
    b=.3
    dirs=np.array([[0.,0.,1.],[0.,0.,-1.],[1.,0.,0.]])
    result,D=photon_normal_to_moving(dirs,[0.,0.,b])
    exact=(dirs[:,2]-b)/(1-b*dirs[:,2])
    np.testing.assert_allclose(result[:,2],exact,atol=3e-15)
    np.testing.assert_allclose(D,gamma_beta([0,0,b])*(1-b*dirs[:,2]),atol=3e-15)
    recovered,inverseD=photon_moving_to_normal(result,[0,0,b])
    np.testing.assert_allclose(recovered,dirs,atol=4e-15)
    np.testing.assert_allclose(inverseD,D,atol=2e-15)


def test_Minkowski_metric_invariant_all_four_vector_types():
    rng=np.random.default_rng(16)
    p=rng.normal(size=(40,4))
    beta=np.array([.23,-.11,.08])
    q=lorentz_to_moving(p,beta)
    np.testing.assert_allclose(minkowski_norm(q),minkowski_norm(p),atol=3e-15,rtol=1e-14)
    np.testing.assert_allclose(lorentz_to_parent(q,beta),p,atol=5e-15)
    zero=lorentz_to_moving(p,[0,0,0])
    np.testing.assert_array_equal(zero,p)


def test_isotropic_blackbody_exact_plus_dipole_and_quadrupole():
    T0=2.72548e6
    b=.00123
    directions=np.array([[0.,0.,1.],[0.,0.,-1.],[1.,0.,0.]])
    T,sky_source,D=boosted_sky_temperature(
         directions,[0.,0.,b],
         source_temperature=lambda n:np.full(len(n),T0))
    mu=directions[:,2]
    exact=T0*np.sqrt(1-b*b)/(1-b*mu)
    np.testing.assert_allclose(T,exact,rtol=1e-14,atol=1e-9)
    assert T[0]>T[1] and T[0]>T0 and T[1]<T0
    expected_diff=2*T0*b/(np.sqrt(1-b*b))
    assert T[0]-T[1]==pytest.approx(expected_diff,rel=1e-6)
    # motion along photon propagation sees source energy RED-shifted:
    _,Dprop=photon_normal_to_moving([[0.,0.,1.]],[0.,0.,b])
    assert Dprop[0]<1


def test_noncollinear_frame_triad_velocity_is_observer_tetrad_relative():
    r=[.31,.02,.05];m=[0.,0.,0.];o=[.03,.19,.04]
    q=frame_triad(r,m,o)
    RO=q["beta_RO_R_in_observer_O_tetrad"]
    OR=q["beta_OR_O_in_radiation_R_tetrad"]
    np.testing.assert_allclose(np.linalg.norm(RO),np.linalg.norm(OR),atol=2e-15)
    assert q["gamma_RO_invariant"]==pytest.approx(
        gamma_beta(RO),rel=1e-14)
    assert q["rapidity_R_observer_O"]==pytest.approx(np.arctanh(np.linalg.norm(RO)),rel=5e-14)
    assert q["frame_coordinate_statement"].endswith("Wigner rotations")
    assert np.linalg.norm(RO+OR)>1e-6  # relative speeds equal, coordinates differ by Wigner rotation
    np.testing.assert_allclose(q["beta_RM_R_in_matter_M_tetrad"],r,atol=5e-15)
    np.testing.assert_allclose(q["beta_MO_M_in_observer_O_tetrad"],-np.array(o),atol=5e-15)


def test_collinear_triad_and_rapidity_not_speed_fraction():
    r=np.array([.0,.0,.22])
    o=np.array([.0,.0,-.16])
    q=frame_triad(r,[0,0,0],o)
    scalar=(r[2]-o[2])/(1-r[2]*o[2])
    assert q["beta_RO_R_in_observer_O_tetrad"][2]==pytest.approx(scalar,rel=4e-15)
    np.testing.assert_allclose(q["beta_OR_O_in_radiation_R_tetrad"],
        -q["beta_RO_R_in_observer_O_tetrad"],atol=3e-15)
    rho=legacy_rapidity_and_velocity_fraction(q["beta_RO_R_in_observer_O_tetrad"])
    assert np.tanh(rho["rapidity_rho"])==pytest.approx(rho["velocity_fraction"])
    assert np.sinh(rho["rapidity_rho"]) != pytest.approx(rho["velocity_fraction"],rel=1e-4)


def test_nonphysical_gamma_overflow_and_frame_mix_refused():
    with pytest.raises(FrameBoostError):
        checked_beta([.8,.8,0])
    with pytest.raises(FrameBoostError):
        checked_beta([np.nan,0,0])
    with pytest.raises(FrameBoostError):
        lorentz_to_moving(np.zeros((2,5)),[0,0,.1])
    with pytest.raises(FrameBoostError):
        photon_normal_to_moving(np.array([[0,0,.7]]),[0,0,.1])
    with pytest.raises(FrameBoostError):
        boosted_sky_temperature(np.array([[0,0,1.]]),[0,0,.1],
           lambda n:np.array([-20.]))


def test_Planck_reference_dipole_axis_and_zero_relative_vector():
    axis=galactic_dipole_unit_vector(264.021,48.253)
    assert np.linalg.norm(axis)==pytest.approx(1.,abs=1e-15)
    q=frame_triad(np.zeros(3),np.zeros(3),np.zeros(3))
    assert q["source_scalar_rel_speed"]==0
    assert q["gamma_RO_invariant"]==pytest.approx(1.)
    assert q["rapidity_R_observer_O"]==pytest.approx(0.)



def test_one_event_frame_rank_and_three_mode_nullspace_exact_linearization():
    from obsstat.finite_boost_observer_frame import one_event_frame_rank
    z=one_event_frame_rank([0,0,0],[0,0,0])
    assert z["rank"]==3 and z["nullspace_dimension"]==3
    np.testing.assert_allclose(
        z["jacobian_beta_R_then_beta_O"],
        np.column_stack((-np.eye(3),np.eye(3))),atol=5e-12)
    np.testing.assert_allclose(
        z["singular_values"],np.sqrt(2)*np.ones(3),rtol=1e-11)
    x=one_event_frame_rank([.2,-.1,.06],[.03,.14,-.02],step=2e-6)
    assert x["rank"]==3 and x["nullspace_dimension"]==3
    assert x["nullspace_residual_maxabs"]<1e-12
    assert x["physics"].endswith("two 3-vectors")



def test_kinematic_monopole_exact_legacy_Teff_F4_against_independent_angular_integral():
    from obsstat.finite_boost_observer_frame import kinematic_monopole_f4
    mu,weights=np.polynomial.legendre.leggauss(160)
    for b in (0.,.00123357353567,.1,.3):
        exact=kinematic_monopole_f4([0,0,b])
        direct=float(np.dot(weights,(np.sqrt(1-b*b)/(1-b*mu))**4)/2)
        assert exact["F4"]==pytest.approx(direct,rel=1e-13,abs=2e-14)
        assert exact["deltaF4"]==pytest.approx(
            (4*b*b)/(3*(1-b*b)),rel=1e-13,abs=1e-16)
    assert kinematic_monopole_f4([0,0,0])["deltaF4"]==0

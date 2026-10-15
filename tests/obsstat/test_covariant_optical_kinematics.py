"""Covariant 1+3 photon drift: metric, parity, acceleration, omega and units."""
import numpy as np
import pytest

from obsstat.covariant_optical_kinematics import (
    OpticalKinematicsError,nabla_u,optical_rate,optical_design,
    angular_rank,sigma_over_H,acceleration_vs_boost_dipole_span,
    euclidean_jet_limit,
)
from obsstat.htt_kinematic_radial_identification import (
    antisymmetric_basis,MPC_KM
)


def dirs(n=120,seed=4):
    rng=np.random.default_rng(seed)
    n=rng.normal(size=(n,3))
    return n/np.linalg.norm(n,axis=1)[:,None]


def test_tetrad_metric_decomposition_and_optical_sign():
    theta=240./MPC_KM
    s=np.diag([2.,-1.,-1.])/MPC_KM
    a=np.array([3.,4.,5.])/MPC_KM
    w=np.einsum("k,kij->ij",np.array([7.,8.,9.])/MPC_KM,
                antisymmetric_basis())
    C=nabla_u(theta,s,w,a)
    np.testing.assert_allclose(C[0,1:],a)
    assert C[:,0].tolist()==[0.]*4
    np.testing.assert_allclose(C[1:,1:],
        (theta/3)*np.eye(3)+s+w)
    n=np.array([[1.,0,0],[-1.,0,0],[0.,0,1.]])
    p=optical_rate(n,theta_s_inv=theta,sigma_s_inv=s,
                     omega_s_inv=w,accel_s_inv=a)
    q=p["negative_dlnE_dt_u_s_inv"]*MPC_KM
    np.testing.assert_allclose(q,[80+2-3,80+2+3,80-1-5],atol=3e-14)
    assert p["look_is_minus_propagation"] is True
    assert p["scope"].startswith("EXACT_ONE_EVENT")


def test_omega_is_instantaneously_null_for_large_nonzero_three_vector():
    n=dirs(200)
    w=np.einsum("k,kij->ij",np.array([12.,-5.,9.])/MPC_KM,
                antisymmetric_basis())
    t=optical_rate(n,theta_s_inv=0.,sigma_s_inv=np.zeros((3,3)),
        omega_s_inv=w,accel_s_inv=[0,0,0])
    assert max(abs(t["negative_dlnE_dt_u_s_inv"]))<5e-34
    X=optical_design(n)
    assert np.max(abs(X[:,9:]))==0
    a=angular_rank(n)
    assert a["rank_H_A3_sigma5"]==9
    assert a["omega_nullity"]==3
    assert a["rank_omega3"]==0


def test_orthogonal_frame_rotation_preserves_photon_rate_and_shear_norm():
    rng=np.random.default_rng(99)
    q,_=np.linalg.qr(rng.normal(size=(3,3)))
    if np.linalg.det(q)<0:q[:,0]*=-1
    n=dirs(160)
    h=60./MPC_KM
    sigma=np.diag([6.,-3.,-3.])/MPC_KM
    a=np.array([1.,-2.,4.])/MPC_KM
    w=np.einsum("k,kij->ij",[.5,-1.,3.],antisymmetric_basis())/MPC_KM
    p=optical_rate(n,theta_s_inv=3*h,sigma_s_inv=sigma,
                   omega_s_inv=w,accel_s_inv=a)
    r=optical_rate(n@q.T,theta_s_inv=3*h,
                   sigma_s_inv=q@sigma@q.T,
                   omega_s_inv=q@w@q.T,
                   accel_s_inv=q@a)
    np.testing.assert_allclose(p["negative_dlnE_dt_u_s_inv"],
                               r["negative_dlnE_dt_u_s_inv"],atol=2e-33)
    assert sigma_over_H(sigma,h)==pytest.approx(
           sigma_over_H(q@sigma@q.T,h),rel=3e-14)
    assert sigma_over_H(sigma,h)==pytest.approx(
           np.sqrt(.5*(36+9+9))/60,rel=1e-14)


def test_true_acceleration_dipole_sign_separate_from_boost_beta():
    n=dirs()
    a=np.array([1.5,-2.,.3])/MPC_KM
    t=optical_rate(n,theta_s_inv=0.,sigma_s_inv=np.zeros((3,3)),
                   omega_s_inv=np.zeros((3,3)),accel_s_inv=a)
    np.testing.assert_allclose(
        t["negative_dlnE_dt_u_s_inv"],-n@a,rtol=2e-14,atol=2e-33)
    z=acceleration_vs_boost_dipole_span(n)
    assert z["rank"]==3 and z["angular_nullity"]==3
    assert z["A_units"]=="s^-1" and z["beta_units"]=="dimensionless"
    assert z["physical_equivalence"].startswith("NOT_ESTABLISHED")


def test_earlier_nonrelativistic_local_jet_limit_without_physical_CF4_claim():
    grad=np.array([[80.,4.,7.],[1.,90.,-3.],[-4.,5.,70.]])
    data=euclidean_jet_limit(dirs(),grad)
    assert data["maxabs_error_s_inv"]<1e-31
    np.testing.assert_allclose(data["source_rate_s_inv"],
                               data["jet_angular_limit_s_inv"],
                               atol=3e-33,rtol=3e-15)
    assert data["physical_CF4_Hubble_equivalence"]=="NOT_ESTABLISHED"


def test_input_domain_guards_and_expansion_H_normalization():
    n=dirs()
    with pytest.raises(OpticalKinematicsError):
        optical_rate(n,theta_s_inv=3.,sigma_s_inv=np.eye(3),
                     omega_s_inv=np.zeros((3,3)),accel_s_inv=np.zeros(3))
    with pytest.raises(OpticalKinematicsError):
        optical_rate(n,theta_s_inv=3.,sigma_s_inv=np.zeros((3,3)),
                     omega_s_inv=np.eye(3),accel_s_inv=np.zeros(3))
    with pytest.raises(OpticalKinematicsError):
        optical_rate(np.ones((5,3)),theta_s_inv=3.,sigma_s_inv=np.zeros((3,3)),
                     omega_s_inv=np.zeros((3,3)),accel_s_inv=np.zeros(3))
    with pytest.raises(OpticalKinematicsError):
        sigma_over_H(np.zeros((3,3)),0.)
    with pytest.raises(OpticalKinematicsError):
        angular_rank(dirs(5))

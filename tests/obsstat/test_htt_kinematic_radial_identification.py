import numpy as np
import pytest
from obsstat.htt_kinematic_radial_identification import (
    MPC_KM,RadialKinematicsError,split_local_velocity_gradient,
    radial_velocity_jet,radial_design_rank,antisymmetric_basis
)


def _directions(n=70):
    rng=np.random.default_rng(25); a=rng.normal(size=(n,3))
    return a/np.linalg.norm(a,axis=1)[:,None]


def test_exact_local_gradient_reconstruction_and_units():
    G=np.array([[80.,4.,7.],[1.,90.,-3.],[-4.,5.,70.]])
    obj=split_local_velocity_gradient(G)
    assert obj["H_jet_km_s_Mpc"]==pytest.approx(80.)
    assert obj["Theta_s_inv"]==pytest.approx(240/MPC_KM)
    assert abs(np.trace(obj["sigma_km_s_Mpc"]))<1e-13
    assert obj["roundtrip_maxabs"]<1e-13
    np.testing.assert_allclose(obj["omega_tensor_km_s_Mpc"],-obj["omega_tensor_km_s_Mpc"].T)


def test_rotation_solid_body_pseudovector_and_radial_blind():
    w=np.array([1.,-2.,3.])
    tensor=np.einsum("a,aij->ij",w,antisymmetric_basis())
    result=split_local_velocity_gradient(tensor)
    np.testing.assert_allclose(result["omega_pseudovector_km_s_Mpc"],w)
    n=_directions()
    assert np.max(abs(radial_velocity_jet(n,tensor)))<2e-15
    assert result["Theta_km_s_Mpc"]==pytest.approx(0.)


def test_covariant_under_constant_orthogonal_frame_rotation():
    n=_directions();rng=np.random.default_rng(4)
    g=rng.normal(size=(3,3))
    r,_=np.linalg.qr(rng.normal(size=(3,3)))
    rot=r@g@r.T
    np.testing.assert_allclose(radial_velocity_jet(n,g),radial_velocity_jet(n@r.T,rot),atol=3e-15)
    original=split_local_velocity_gradient(g); shifted=split_local_velocity_gradient(rot)
    np.testing.assert_allclose(shifted["sigma_km_s_Mpc"],r@original["sigma_km_s_Mpc"]@r.T,atol=2e-15)


def test_actual_geometry_has_stf_five_rank_and_omega_three_null_modes():
    n=_directions(300)
    result=radial_design_rank(n)
    assert result["stf5_rank"]==5
    assert result["omega_3_mode_rank"]==0
    assert result["vorticity_design_frobenius_residual"]<1e-14


def test_invalid_source_jet_and_nonunit_sky_refused():
    with pytest.raises(RadialKinematicsError):
        split_local_velocity_gradient(np.ones((4,4)))
    with pytest.raises(RadialKinematicsError):
        radial_velocity_jet(np.ones((30,3)),np.eye(3))
    with pytest.raises(RadialKinematicsError):
        radial_design_rank(_directions(4))

"""Focused contract falsifiers for the instantaneous geometry consumer."""
import numpy as np
import pytest

from geometry_image import B, E, TOL, class_a_ric, derivatives, frame, joint, svec, unsvec


def test_matched_scalar_does_not_fix_tensor_and_flat_presentation():
    ii = np.diag([1., 0, 0]); vii = np.diag([0., 2, 1])
    a = np.zeros(3); s = np.diag([.1, -.05, -.05]); e = 4697/400
    one = frame(ii,a,2.,s,e,a)
    two = frame(vii,a,2.,s,e,a)
    assert abs(one["scalar"]-two["scalar"]) <= TOL
    assert np.linalg.norm(one["ricci"]-two["ricci"]) > 1
    for n in (np.zeros((3,3)),np.diag([0.,1,1])):
        assert np.array_equal(frame(n,a,2.,np.zeros((3,3)),12.,a)["riemann"], np.zeros((3,3,3,3)))


def test_invalid_jacobi_is_rejected_at_tiny_si_scale():
    n = np.diag([1.,.7,1.1]); a = np.array([.3,0,0])
    with pytest.raises(ValueError,match="INVALID_JACOBI"):
        frame(n,a,2.,np.zeros((3,3)),12.,np.zeros(3))
    valid = frame(np.diag([0.,.7,1.1]),a,2.,np.zeros((3,3)),12.,np.zeros(3))
    assert np.isclose(valid["ricci"][1,2],-.12)


def test_codazzi_signed_flux_and_adm_identity():
    a = np.array([.4,0,0]); s = np.diag([.2,-.1,-.1])
    got = frame(np.zeros((3,3)),a,2.,s,11.,np.zeros(3))
    assert np.isclose(got["momentum"][0],6*.4*.1)
    assert np.linalg.norm(got["momentum"]-got["codazzi"]) <= TOL
    assert abs(got["adm_residual"]-2*got["hamiltonian_residual"]) <= TOL


def test_quadratic_hessian_recovers_direct_map_and_complex_step():
    z = np.r_[svec(np.diag([0.,2,1])),2.,[.1/np.sqrt(2),.15/np.sqrt(6),0,0,0]]
    j,h = derivatives(z)
    delta = np.arange(12)*.001
    direct = joint(z+delta)
    exact = joint(z)+j@delta+.5*np.einsum("i,kij,j->k",delta,h,delta)
    assert np.linalg.norm(direct-exact) <= TOL*np.linalg.norm(direct)
    assert np.isclose(np.linalg.norm(unsvec(z[:6])),np.linalg.norm(z[:6]))
    assert len(B)==5 and E[0,1,2]==1

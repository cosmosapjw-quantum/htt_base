import numpy as np
import pytest
from publication_frame_kinematics import (gamma,relative_beta,rapidity,relative_gamma_from_rest_frame_vectors,rapidity_between,source_frame_packet,STF,radial_gradient,radial_operator,antisymmetric_from_pseudovector,velocity_from_beta,C_SI)


def sphere(n=250):
    k=np.arange(n); z=1-2*(k+0.5)/n;phi=(np.pi*(3-np.sqrt(5)))*k
    return np.stack([np.sqrt(1-z*z)*np.cos(phi),np.sqrt(1-z*z)*np.sin(phi),z],axis=-1)


def test_lorentz_collinear():
    for a,b in [(0,0.2),(0.1,-0.12),(0.9,0.8)]:
        c=relative_beta([a,0,0],[b,0,0]);assert np.allclose(c,[(a-b)/(1-a*b),0,0],atol=2e-14)


def test_lorentz_noncoplanar_invariant():
    rs=np.random.default_rng(1562)
    for _ in range(300):
        o=rs.normal(size=3);o*=rs.uniform(0,0.95)/np.linalg.norm(o)
        m=rs.normal(size=3);m*=rs.uniform(0,0.95)/np.linalg.norm(m)
        bm=relative_beta(o,m)
        assert np.isclose(gamma(bm),relative_gamma_from_rest_frame_vectors(o,m),rtol=1e-13)
        assert np.isclose(rapidity(bm),rapidity_between(o,m),rtol=1e-13,atol=1e-11)


def test_frame_identity():
    assert np.allclose(relative_beta([.3,0,.1],[.3,0,.1]),0)
    assert source_frame_packet([.01,.02,0],[.02,0,.01],[100,40,-50])['B_W_is_tilt'] is False


def test_velocity_c():
    assert np.allclose(velocity_from_beta([0.01,0,0]),[C_SI*.01,0,0])


def test_reject_superluminal():
    with pytest.raises(ValueError):relative_beta([1,0,0],[0,0,0])
    with pytest.raises(ValueError):source_frame_packet([0,0,0],[0,0,0],[np.nan,0,0])


def test_stf_projection():
    a=STF(np.arange(9).reshape(3,3));assert np.allclose(a,a.T) and np.isclose(np.trace(a),0)


def test_radial_vorticity_exact_null():
    dirs=sphere();omega=antisymmetric_from_pseudovector([0.2,-.6,.3]);assert np.max(abs(np.einsum('ni,ij,nj->n',dirs,omega,dirs)))<2e-16


def test_radial_operator_rank_and_null():
    dirs=sphere();a=radial_operator(dirs)
    assert np.linalg.matrix_rank(a,tol=1e-10)==6
    for w in np.eye(3): assert np.linalg.norm(a@antisymmetric_from_pseudovector(w).reshape(9))<2e-14


def test_isotropy_and_shear_only():
    dirs=sphere();H=71.;S=STF([[.3,.4,.1],[.4,-.1,.2],[.1,.2,.7]]);W=antisymmetric_from_pseudovector([9,3,-2]);J=H*np.eye(3)+S+W
    vals=np.array([radial_gradient(n,J) for n in dirs]);expect=H+np.einsum('ni,ij,nj->n',dirs,S,dirs)
    assert np.max(abs(vals-expect))<4e-14


def test_rotation_covariance():
    rng=np.random.default_rng(1);A=rng.normal(size=(3,3));Q,_=np.linalg.qr(A);Q[:,0]*=np.sign(np.linalg.det(Q));J=rng.normal(size=(3,3));n=sphere(1)[0]
    assert np.isclose(radial_gradient(n,J),radial_gradient(Q@n,Q@J@Q.T))


def test_direction_failclosed():
    with pytest.raises(ValueError):radial_operator([[2,0,0]])
    with pytest.raises(ValueError):radial_gradient([2,0,0],np.eye(3))

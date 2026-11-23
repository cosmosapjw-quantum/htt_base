"""Independent metric-distance and branch tests for the infinitesimal R99 beam."""
import numpy as np
import pytest
from scipy.integrate import quad

from scripts.r99 import optical
from bass.transport.finite_redshift_optics import OpticalHistory, finite_redshift_beams
from bass.recombination.reionization import SEC_PER_MPC


def metric(case, beta=None):
    # Choose c/H_* = 1 Mpc. All exact distances below are in Mpc.
    N = np.linspace(-1.5, 0., 401)
    ones = np.ones(len(N))
    s, A, n = np.zeros((len(N),3,3)), np.zeros((len(N),3)), np.zeros((len(N),3,3))
    H = ones
    if case == "milne":
        H = np.exp(-N)
        A = H[:, None]*np.array([.6,.8,0.])
    if case == "kasner":
        q = np.array([-2.,3.,6.])/7
        H = np.exp(-3*N)/3
        s = H[:,None,None]*np.diag(3*q-1)
    if case == "closed":
        n = 2*np.exp(-N)[:,None,None]*np.eye(3)
    if beta is not None:
        beta = np.broadcast_to(beta, A.shape)
    return OpticalHistory(N, H, s, A, n, h_reference_si=1/SEC_PER_MPC, emitter_beta=beta)


def run(h, sky, z, **kw):
    return finite_redshift_beams(h, sky, z, n_min=-1.49, sky_frame="observed", **kw)


def test_flat_vertex_direction_angular_units_and_distance():
    z = np.array([0., .01, .5, 1.2])
    exact = z/(1+z)
    b = run(metric("flat"), optical.DIRECTIONS[:6], z)
    np.testing.assert_allclose(b.angular_distance_mpc, np.tile(exact, (6,1)), atol=2e-12)
    np.testing.assert_allclose(b.signed_area_mpc2, np.tile(exact**2,(6,1)), atol=2e-12)
    np.testing.assert_array_equal(b.parity, np.tile([0,1,1,1],(6,1)))
    assert np.max(abs(b.redshift-z)) < 2e-13


def test_tiny_measured_redshift_is_distinct_from_vertex():
    z = 1e-15
    b = run(metric("flat"), [[0, 0, 1]], [0., z])
    assert b.parity.tolist() == [[0, 1]]
    assert b.emission_N[0, 1] < 0.
    np.testing.assert_allclose(b.redshift[0, 1], z, atol=0, rtol=2e-13)
    np.testing.assert_allclose(b.angular_distance_mpc[0, 1], z/(1+z), atol=0, rtol=2e-13)
    # Translating the arbitrary zero of N to 2 makes this smaller event
    # unrepresentable in binary64. It must not become the vertex.
    N = np.linspace(1., 2., 5)
    shape = (len(N), 3, 3)
    h = OpticalHistory(N, np.ones_like(N), np.zeros(shape), np.zeros((len(N), 3)),
                       np.zeros(shape), h_reference_si=1/SEC_PER_MPC)
    with pytest.raises(ValueError, match="unresolvable redshift event"):
        finite_redshift_beams(h, [[0, 0, 1]], [1e-18], n_min=1., sky_frame="normal")


def test_milne_noncommuting_spatial_frame():
    b = run(metric("milne"), [[0,0,1]], [1.])
    assert b.angular_distance_mpc[0,0] == pytest.approx(.375, rel=3e-10)
    assert b.max_normalized_connector_tangency < 2e-12


def test_kasner_directional_killing_integrals():
    q = np.array([-2.,3.,6.])/7
    te = .5
    z = te**(-q[2])-1
    J = [te**q[i] * quad(lambda t: t**(q[2]-2*q[i]),te,1)[0] for i in (0,1)]
    b = run(metric("kasner"), [[0,0,1]], [z])
    assert b.emission_N[0,0] == pytest.approx(np.log(te)/3, abs=3e-12)
    assert b.angular_distance_mpc[0,0] == pytest.approx(np.sqrt(np.prod(J)), rel=5e-10)


def test_closed_curvature_and_unresolved_conjugate_event():
    h = metric("closed")
    z = np.array([.1, 1., 3.])
    b = run(h, [[0,0,1]], z)
    np.testing.assert_allclose(b.angular_distance_mpc[0], np.sin(z)/(1+z), atol=8e-11)
    with pytest.raises(ValueError, match="singular beam"):
        run(h, [[0,0,1]], [np.pi])


def test_oblique_observer_and_emitter_boost_at_fixed_measured_redshift():
    bob = np.array([.08,-.03,.04])
    bem = np.array([-.02,.04,.015])
    nobs = optical.DIRECTIONS[3:6]
    z = np.array([.3,.9])
    b = run(metric("flat", bem), nobs, z, observer_beta=bob)
    # Inverse boost of energy and photon momentum from observer components.
    go = 1/np.sqrt(1-bob@bob)
    do = 1/(go*(1-nobs@bob))
    pn = (-nobs + (go - (go-1)*(nobs@bob)/(bob@bob))[:,None]*bob)*do[:,None]
    de = (1-pn@bem)/np.sqrt(1-bem@bem)
    zv = (1+z)*do[:,None]/de[:,None]-1
    exact = do[:,None]*zv/(1+zv)
    np.testing.assert_allclose(b.angular_distance_mpc,exact,rtol=3e-11)
    np.testing.assert_allclose(b.normal_sky,-pn,atol=3e-15)
    normal = finite_redshift_beams(metric("flat",bem), -pn, z, n_min=-1.49,
                                   sky_frame="normal", observer_beta=bob)
    np.testing.assert_allclose(normal.angular_distance_mpc,b.angular_distance_mpc,atol=1e-13)


def test_domain_uncertified_branch_and_superluminal_inputs():
    sky = [[0,0,1]]
    with pytest.raises(ValueError, match="outside sampled"):
        run(metric("flat"), sky, [7.])
    with pytest.raises(ValueError, match="uncertified redshift branch"):
        run(metric("kasner"), [[1,0,0]], [.1])
    with pytest.raises(ValueError, match="e-fold domain"):
        finite_redshift_beams(metric("flat"), sky, [.1], n_min=-2.,sky_frame="normal")
    with pytest.raises(ValueError, match="emitter velocity"):
        metric("flat", [1.,0,0])
    with pytest.raises(ValueError, match="observer velocity"):
        run(metric("flat"), sky, [.1],observer_beta=[2,0,0])


def test_late_r49_connection_to_physical_length():
    h = optical.make_history("VI_h", 111)
    b = run(h, optical.DIRECTIONS[2:4], [.025,.5])
    assert np.all(b.parity==1) and b.monotone_redshift_margin>0
    assert np.all(b.angular_distance_mpc[:,1]>1000)
    assert np.ptp(b.angular_distance_mpc[:,1]) > 1e-5
    assert b.max_null_error < 1e-11

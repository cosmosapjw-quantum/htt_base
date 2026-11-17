"""Independent small-domain tests; no R58 file or observed pilot is required."""
import numpy as np
import pytest
from htt.htt.infer.r61_mixed_invariant import mixed_shear_range, standard_stf_basis


def generic_input():
    """Fixed SPD correlated covariance with nonzero beta–kappa cross blocks."""
    h = np.array([.0013, -.0008, .0004, .012, -.018, .004, .007, -.006])
    L = np.eye(8)
    L[1, 0] = .15
    L[2, 1] = -.12
    L[3:, :3] = np.array([[.20, -.10, .05], [-.15, .18, -.06],
                          [.10, .07, -.14], [.04, -.11, .16], [-.09, .05, .12]])
    L[5, 3] = .13
    L[7, 4] = -.17
    scales = np.r_[np.array([.0002, .00023, .00018]),
                   np.array([.003, .004, .0028, .0035, .0032])]
    C = scales[:, None] * (L @ L.T) * scales[None, :]
    return h, C, standard_stf_basis()


def assert_witness(result, h, C, E, cutoff, rho):
    for i, key in enumerate(('minimum_witness', 'maximum_witness')):
        w = result[key]
        beta, kappa, Q = np.array(w['beta']), np.array(w['kappa']), np.array(w['Qcal'])
        dz = np.r_[beta, kappa] - h
        assert dz @ np.linalg.solve(C, dz) <= cutoff + 1e-10
        assert np.linalg.norm(Q, 'fro') <= np.sqrt(15 / 2) * rho + 1e-13
        np.testing.assert_allclose(Q, Q.T, atol=1e-13, rtol=0)
        assert abs(np.trace(Q)) < 1e-13
        phi = float(beta @ (np.einsum('a,aij->ij', kappa, E) - Q) @ beta)
        assert phi == pytest.approx(result['feasible_range'][i], abs=1e-18)


def test_zero_cutoff_hand_calculation_and_calibration_witness():
    h, C, E = generic_input()
    rho = .002
    r = mixed_shear_range(h, C, E, 0, rho=rho)
    K = np.einsum('a,aij->ij', h[3:], E)
    center_phi = float(h[:3] @ K @ h[:3])
    shift = np.sqrt(5) * rho * float(h[:3] @ h[:3])
    np.testing.assert_allclose(r['outer_range'], [center_phi-shift, center_phi+shift],
                               atol=1e-20, rtol=0)
    assert r['max_gap'] == 0
    assert_witness(r, h, C, E, 0, rho)


@pytest.mark.parametrize('rho', [0., .003])
def test_zero_center_isotropic_against_independent_radial_solution(rho):
    sb, sk, cutoff = .001, .01, 3.
    h = np.zeros(8)
    C = np.diag(np.r_[np.full(3, sb**2), np.full(5, sk**2)])
    E = standard_stf_basis()
    a, b = np.sqrt(5)*rho, np.sqrt(2/3)*sk
    y = (np.sqrt(a*a+3*b*b*cutoff)-a)/(3*b)
    exact = sb**2*(cutoff-y*y)*(b*y+a)
    r = mixed_shear_range(h, C, E, cutoff, rho=rho, atol=5e-10, max_nodes=10000)
    assert r['minimum_bracket'][0]-1e-18 <= -exact <= r['minimum_bracket'][1]+1e-18
    assert r['maximum_bracket'][0]-1e-18 <= exact <= r['maximum_bracket'][1]+1e-18
    np.testing.assert_allclose(r['feasible_range'], [-exact, exact], atol=5e-16, rtol=0)
    # A degenerate optimum manifold may hit the cap; it must report that honestly.
    if r['max_gap'] > 5e-10 + r['roundoff_guard_per_bound']:
        assert r['status'] == 'NODE_CAP' and not r['converged']
    else:
        assert r['status'] == 'TOLERANCE_MET' and r['converged']
    assert_witness(r, h, C, E, cutoff, rho)


def test_joint_rotation_covariance_and_conditional_lift():
    h, C, E = generic_input()
    cutoff, rho = 7., .002
    angle = .61
    zrot = np.array([[np.cos(angle), -np.sin(angle), 0],
                     [np.sin(angle), np.cos(angle), 0], [0, 0, 1.]])
    angle = -.47
    yrot = np.array([[np.cos(angle), 0, np.sin(angle)], [0, 1., 0],
                     [-np.sin(angle), 0, np.cos(angle)]])
    rot = zrot @ yrot
    rotated_basis = np.einsum('ij,ajk,lk->ail', rot, E, rot)
    D5 = np.einsum('aij,bij->ab', E, rotated_basis)
    T = np.zeros((8, 8))
    T[:3, :3], T[3:, 3:] = rot, D5
    r = mixed_shear_range(h, C, E, cutoff, rho=rho, atol=1e-10, max_nodes=10000)
    rr = mixed_shear_range(T@h, T@C@T.T, E, cutoff, rho=rho, atol=1e-10, max_nodes=10000)
    assert r['converged'] and rr['converged']
    np.testing.assert_allclose(r['feasible_range'], rr['feasible_range'], atol=2e-13, rtol=0)
    for key in ('minimum_bracket', 'maximum_bracket'):
        assert max(r[key][0], rr[key][0]) <= min(r[key][1], rr[key][1]) + 2e-14
    assert_witness(r, h, C, E, cutoff, rho)
    assert_witness(rr, T@h, T@C@T.T, E, cutoff, rho)
    # Independently verify the conditional kappa formula, including cross terms.
    R = np.linalg.solve(C[:3, :3], C[:3, 3:]).T
    D = C[3:, 3:] - R@C[:3, 3:]
    for sign, key in ((-1, 'minimum_witness'), (1, 'maximum_witness')):
        w = r[key]
        beta, kappa = np.array(w['beta']), np.array(w['kappa'])
        db = beta-h[:3]
        rb2 = float(db@np.linalg.solve(C[:3, :3], db))
        v = np.einsum('i,aij,j->a', beta, E, beta)
        expected = h[3:] + R@db + sign*np.sqrt(max(cutoff-rb2, 0)/(v@D@v))*(D@v)
        np.testing.assert_allclose(kappa, expected, rtol=2e-12, atol=2e-14)


def test_node_cap_preserves_enclosure_and_does_not_claim_convergence():
    h, C, E = generic_input()
    r = mixed_shear_range(h, C, E, 7., rho=.002, atol=1e-15, max_nodes=0)
    assert r['status'] == 'NODE_CAP' and not r['converged']
    assert r['max_gap'] > 1e-15
    # Explicit feasible points independent of the optimizer's returned witnesses.
    L = np.linalg.cholesky(C)
    for i in range(8):
        for sign in (-1, 1):
            z = h + sign*np.sqrt(7)*L[:, i]
            beta, kappa = z[:3], z[3:]
            phi = float(beta@np.einsum('a,aij->ij', kappa, E)@beta)
            cal = np.sqrt(5)*.002*float(beta@beta)
            assert r['outer_range'][0] <= phi-cal
            assert phi+cal <= r['outer_range'][1]
    assert_witness(r, h, C, E, 7., .002)


@pytest.mark.parametrize('change', ['rho', 'cutoff', 'atol', 'max_nodes', 'basis', 'covariance'])
def test_invalid_inputs_are_rejected(change):
    h, C, E = generic_input()
    kwargs = dict(center8=h, cov8=C, stf_basis=E, cutoff=7.)
    kwargs.update({'rho': {'rho': -1}, 'cutoff': {'cutoff': -1},
                   'atol': {'atol': 0}, 'max_nodes': {'max_nodes': -1},
                   'basis': {'stf_basis': E*2}, 'covariance': {'cov8': -C}}[change])
    with pytest.raises((ValueError, np.linalg.LinAlgError)):
        mixed_shear_range(**kwargs)

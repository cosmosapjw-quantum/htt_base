"""Independent finite controls for the R25 angular-pair operator."""

import numpy as np

from compute import STF, accumulate, covariance, designs, geometry, pair_terms


def fixture():
    ra = np.array([3., 42., 119., 201., 294., 327.])
    dec = np.array([-39., 21., 72., -12., 44., -61.])
    n, E = geometry(ra, dec)
    X, B = designs(n, E)
    y = np.array([[1., 2.], [-2., .5], [.7, -1.1], [4., 1.], [-.3, 2.], [1.3, -.7]])
    C = np.array([[[2. + .1*i, .2], [.2, 1. + .2*i]] for i in range(len(n))])
    return n, E, X, B, y, C


def test_geometry_stf_and_independent_field_oracles():
    n, E, X, B, y, _ = fixture()
    assert np.max(np.abs(np.linalg.norm(n, axis=1)-1)) < 1e-12
    assert np.max(np.abs(np.einsum("nka,nk->na", E, n))) < 1e-12
    assert np.max(np.abs(np.einsum("nka,nkb->nab", E, E)-np.eye(2))) < 1e-12
    assert np.max(np.abs(np.einsum("kij,lij->kl", STF, STF)-np.eye(5))) < 1e-12
    assert np.max(np.abs(np.trace(STF, axis1=1, axis2=2))) < 1e-12
    i, js = 0, np.arange(1, len(n))
    li, lj, a, _, c, _, _ = pair_terms(n, E, X, y, i, js)
    assert np.max(np.abs(li @ B[i] + np.einsum("na,nak->nk", lj, B[js]))) < 1e-12
    # These field formulas do not call the pair-design implementation.
    E1 = (1-c)[:, None] * (n[i] + n[js])
    E2 = np.stack([2*np.einsum("i,ij,j->", n[i], S, n[j])
                   - ci*(n[i]@S@n[i] + n[j]@S@n[j])
                   for S in STF for j, ci in zip(js, c)]).reshape(5, len(js)).T
    B2 = np.stack([np.cross(n[i], n[j])@S@(n[j]-n[i])
                   for S in STF for j in js]).reshape(5, len(js)).T
    np.testing.assert_allclose(a[:, :3], E1, atol=1e-12)
    np.testing.assert_allclose(a[:, 3:8], E2, atol=1e-12)
    np.testing.assert_allclose(a[:, 8:], B2, atol=1e-12)


def test_accumulation_shared_covariance_and_permutations():
    n, E, X, B, y, C = fixture()
    H, D, d, counts, _, _ = accumulate(n, E, X, y)
    assert counts.sum() == 15
    np.testing.assert_allclose(d.reshape(-1), H.reshape(-1, 12) @ y.reshape(-1), atol=1e-12)
    np.testing.assert_allclose(D.reshape(-1, 13), H.reshape(-1, 12) @ X.reshape(-1, 13), atol=1e-12)
    np.testing.assert_allclose(H.reshape(-1, 12) @ B.reshape(-1, 3), 0, atol=1e-12)
    Cd = covariance(H, C)
    sigma = np.zeros((12, 12))
    for i in range(6):
        sigma[2*i:2*i+2, 2*i:2*i+2] = C[i]
    np.testing.assert_allclose(Cd, H.reshape(-1, 12) @ sigma @ H.reshape(-1, 12).T, atol=1e-11)
    p = np.array([4, 1, 5, 0, 3, 2])
    Hp, Dp, dp, cp, _, _ = accumulate(n[p], E[p], X[p], y[p])
    np.testing.assert_allclose(dp, d, atol=1e-12)
    np.testing.assert_allclose(Dp, D, atol=1e-12)
    np.testing.assert_allclose(Hp.reshape(-1, 6, 2)[:, np.argsort(p)], H.reshape(-1, 6, 2), atol=1e-12)
    np.testing.assert_array_equal(cp, counts)


def test_duplicate_pair_means_and_response_not_coefficient():
    n, E, X, _, y, _ = fixture()
    single = [(0, np.array([1]))]
    twice = [(0, np.array([1, 1]))]
    lhs = accumulate(n, E, X, y, pair_list=single)
    rhs = accumulate(n, E, X, y, pair_list=twice)
    for k in range(3):
        np.testing.assert_allclose(lhs[k], rhs[k], atol=1e-12)
    np.testing.assert_array_equal(rhs[3], 2*lhs[3])
    n2 = np.array([[1., 0., 0.], [0., 1., 0.]])
    E2 = np.array([[[0., 0.], [1., 0.], [0., 1.]], [[-1., 0.], [0., 0.], [0., 1.]]])
    X2, _ = designs(n2, E2)
    _, D2, _, _, _, _ = accumulate(n2, E2, X2, np.zeros((2, 2)))
    # The first E1 pair response has two nonzero components: it is not beta.
    assert np.count_nonzero(np.abs(D2[:, :, 0]) > 1e-12) >= 2


def test_rotation_angle_invariance_and_unidentified_modes():
    n, E, X, _, y, _ = fixture()
    angle = .37
    R = np.array([[np.cos(angle), -np.sin(angle), 0], [np.sin(angle), np.cos(angle), 0], [0, 0, 1]])
    nr, Er = n @ R.T, np.einsum("ab,nbc->nac", R, E)
    Xr, _ = designs(nr, Er)
    for ni, Ei, Xi in ((n, E, X), (nr, Er, Xr)):
        _, _, _, k, _, theta, bins = pair_terms(ni, Ei, Xi, y, 0, np.arange(1, 6))
        if ni is n:
            expected = (k, theta, bins)
        else:
            np.testing.assert_allclose(k, expected[0], atol=1e-12)
            np.testing.assert_allclose(theta, expected[1], atol=1e-12)
            np.testing.assert_array_equal(bins, expected[2])
    assert np.linalg.eigvalsh(np.diag([1., 1e-14]))[0] > 0
    M = np.array([[1., 1.], [0., 1e-13]])
    np.testing.assert_allclose(M @ np.array([-1e13, 1e13]), [0., 1.])
    assert np.linalg.matrix_rank(np.array([[1., 0.]])) == 1

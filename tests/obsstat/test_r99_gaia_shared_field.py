"""Independent invariants for the R99 shared-field construction."""
import numpy as np
import pytest
from scripts.r99.gaia_shared_field import (
    patch_response, chord_kernel, covariance_from_response,
    joint_covariance, supported_subspace,
)


def normals(seed=14, patches=5, dim=4):
    rng = np.random.default_rng(seed)
    a = rng.normal(size=(patches, dim+2, dim))
    return np.einsum("pki,pkj->pij", a, a)+np.eye(dim)[None]


def test_constant_field_reproduces_known_linear_design_and_cancels():
    ja = patch_response(normals(14), 2)
    jb = patch_response(normals(27), 2)
    e = np.eye(4)[:, :2]
    np.testing.assert_allclose(ja.sum(axis=0), e, atol=4e-16)
    np.testing.assert_allclose(jb.sum(axis=0), e, atol=4e-16)
    np.testing.assert_allclose((ja-jb).sum(axis=0), 0, atol=5e-16)


def test_direct_rhs_perturbation_not_response_reimplementation():
    f = normals()
    j = patch_response(f, 2)
    g = np.array([[.4,2.],[-1.2,.7],[3.,-1.],[.1,.3],[1.3,-.2]])
    beta = np.array([1.,3.,-1.,2.])
    # Create independent pseudo-observation RHS using native 4D patch models.
    full = np.zeros((5,4))
    full[:, :2] = g
    rhs = np.array([f[p]@(beta+full[p]) for p in range(5)]).sum(axis=0)
    solved = np.linalg.solve(f.sum(axis=0), rhs)-beta
    predicted = np.einsum("pdr,pr->d", j, g)
    np.testing.assert_allclose(solved, predicted, atol=9e-16)


def test_kernel_psd_and_rigid_sky_rotation():
    rng = np.random.default_rng(42)
    n = rng.normal(size=(5,3))
    n /= np.linalg.norm(n, axis=1)[:,None]
    rotation, _ = np.linalg.qr(rng.normal(size=(3,3)))
    k = chord_kernel(n, 35.)
    np.testing.assert_allclose(k, chord_kernel(n@rotation, 35.), atol=2e-15)
    assert np.linalg.eigvalsh(k)[0] >= -2e-15
    np.testing.assert_allclose(np.diag(k), 1., atol=2e-15)


def test_direct_random_field_covariance():
    rng = np.random.default_rng(703)
    j = patch_response(normals(15, patches=3), 2)
    k = np.array([[1.,.4,.2],[.4,1.,.1],[.2,.1,1.]])
    expected = covariance_from_response(j, k)
    chol = np.linalg.cholesky(np.kron(k, np.eye(2)))
    field = rng.normal(size=(40000,6))@chol.T
    coefficient = np.array([sum(j[p]@x[2*p:2*p+2] for p in range(3)) for x in field])
    observed = np.cov(coefficient, rowvar=False)
    assert np.linalg.norm(observed-expected)/np.linalg.norm(expected) < .025


def test_joint_covariance_contains_shared_cross_terms():
    j = np.stack([patch_response(normals(1,patches=3),2),
                  patch_response(normals(2,patches=3),2)])
    k = np.array([[1.,.6,.3],[.6,1.,.4],[.3,.4,1.]])
    c = joint_covariance(j,k)
    direct = covariance_from_response(j[0]-j[1],k)
    np.testing.assert_allclose(direct,c[:4,:4]+c[4:,4:]-c[:4,4:]-c[4:,:4],atol=3e-16)
    assert np.linalg.eigvalsh(c)[0] >= -2e-15


def test_projected_quadratic_does_not_erase_unsupported_component():
    r = supported_subspace(np.array([2.,3.,7.]), np.diag([4.,9.,0.]))
    assert r["rank"] == 2
    assert r["supported_quadratic_form"] == pytest.approx(2.)
    assert r["unsupported_component_norm_microasyr"] == pytest.approx(7.)
    assert r["unsupported_squared_norm_fraction"] == pytest.approx(49/62)
    assert r["calibrated_p"] is None


@pytest.mark.parametrize("angle", [0., -1., 181., np.nan])
def test_invalid_angular_scale(angle):
    with pytest.raises(ValueError):
        chord_kernel(np.eye(3), angle)


def test_materially_indefinite_covariance_rejected():
    with pytest.raises(ValueError):
        covariance_from_response(np.ones((2,2,1)), np.array([[1.,2.],[2.,1.]]))
    with pytest.raises(ValueError):
        supported_subspace(np.ones(2), np.diag([1.,-.1]))


def test_singular_design_rejected():
    with pytest.raises(ValueError):
        patch_response(np.zeros((3,4,4)),2)


def test_supported_subspace_is_invariant_under_unit_rescaling():
    y = np.array([1., 2., 5.])
    c = np.diag([1., 2., 0.])
    baseline = supported_subspace(y, c)
    for scale in (1e-21, 1., 1e21):
        r = supported_subspace(scale*y, scale**2*c)
        assert r["rank"] == 2
        assert r["supported_quadratic_form"] == pytest.approx(baseline["supported_quadratic_form"])
        assert r["unsupported_squared_norm_fraction"] == pytest.approx(baseline["unsupported_squared_norm_fraction"])
    zero = supported_subspace(y, np.zeros((3,3)))
    assert zero["rank"] == 0
    assert zero["supported_quadratic_form"] == 0
    assert zero["unsupported_squared_norm_fraction"] == 1

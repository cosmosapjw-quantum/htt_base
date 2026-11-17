"""Analytic and independent-coordinate tests for R62 tensor-class witnesses."""
import numpy as np
import pytest
from scipy import optimize
from scipy.spatial.transform import Rotation

try:
    from htt.htt.infer import r62_tensor_classes as m
except ModuleNotFoundError:
    import r62_tensor_classes as m


def dense_covariance(n, seed=92):
    a = np.random.default_rng(seed).normal(size=(n, n))
    return a@a.T/n + .4*np.eye(n)


def fit(h, v, cutoff=.01, **kw):
    options = dict(n_starts=5, grid_size=18, max_nfev=120)
    options.update(kw)
    return m.classify_tensor_series(h, v, cutoff, **options)


def test_basis_normalization_and_active_rotation_covariance():
    e = m.stf_basis()
    np.testing.assert_allclose(np.einsum('aij,bij->ab', e, e), np.eye(5), atol=4e-16)
    np.testing.assert_allclose(np.trace(e, axis1=1, axis2=2), 0, atol=1e-16)
    r = Rotation.from_rotvec([.43, -.21, .7]).as_matrix()
    d = m.stf_rotation_matrix(r)
    np.testing.assert_allclose(d.T@d, np.eye(5), atol=8e-16)
    h = np.arange(15.)/7 - .9
    v = dense_covariance(15)
    rotated = m.rotate_tensor_series(h, v, r)
    actual_tensors = m.coefficients_to_tensors(rotated['mean'].reshape(-1, 5))
    expected_tensors = np.array([r@x@r.T for x in m.coefficients_to_tensors(h.reshape(-1, 5))])
    np.testing.assert_allclose(actual_tensors, expected_tensors, atol=2e-15)
    np.testing.assert_allclose(m.tensors_to_coefficients(actual_tensors).ravel(), rotated['mean'], atol=1e-15)
    assert rotated['mean']@np.linalg.solve(rotated['covariance'], rotated['mean']) == pytest.approx(h@np.linalg.solve(v, h), rel=2e-15)


def test_shared_frame_exact_hand_case_and_general_shape_svd_distance():
    h = np.array([[1., 2., 0, 0, 0], [-2., .5, 0, 0, 0]]).ravel()
    out = fit(h, np.eye(10), cutoff=1e-7)
    assert out['classes']['SHARED_FRAME']['status'] == 'INTERSECTS'
    assert out['classes']['SHARED_FRAME']['objective'] < 1e-24
    singular = np.linalg.svd(h.reshape(-1, 5), compute_uv=False)
    expected = np.sum(singular[1:]**2)
    general = out['classes']['SHARED_GENERAL_SHAPE']
    assert general['objective'] == pytest.approx(expected, abs=2e-10)
    assert general['status'] == 'UNRESOLVED'
    assert 'upper bound' in general['objective_guarantee']
    # Pairwise commutativity permits different diagonal shapes.
    assert np.linalg.matrix_rank(np.array(out['classes']['SHARED_FRAME']['witness']).reshape(2, 5)) == 2


def test_single_tensor_spectral_distance_formulas():
    eigenvalues = np.array([-1.2, -.2, 1.4])
    r = Rotation.from_rotvec([.8, -.3, .9]).as_matrix()
    h = m.tensors_to_coefficients(r@np.diag(eigenvalues)@r.T)
    out = fit(h, np.eye(5), cutoff=1e-8)
    norm2 = eigenvalues@eigenvalues
    axis_expected = norm2 - 1.5*max(eigenvalues**2)
    zero_expected = norm2 - .5*(max(eigenvalues)-min(eigenvalues))**2
    assert out['classes']['SHARED_AXIS']['objective'] == pytest.approx(axis_expected, abs=1e-10)
    assert out['classes']['SHARED_ZERO_EIGENVALUE_SHAPE']['objective'] == pytest.approx(zero_expected, abs=1e-10)
    assert out['classes']['SHARED_FRAME']['objective'] < 1e-25
    assert out['classes']['SHARED_GENERAL_SHAPE']['objective'] < 1e-25


@pytest.mark.parametrize('kind', ['axis', 'zero', 'general'])
def test_exact_signed_shapes_with_zero_and_repeated_eigenvalue_strata(kind):
    r = Rotation.from_rotvec([.37, .2, -.71]).as_matrix()
    if kind == 'axis':
        u = r[:, 2]
        shape = m.tensors_to_coefficients(np.sqrt(1.5)*(np.outer(u, u)-np.eye(3)/3))
        expected = 'SHARED_AXIS'
    elif kind == 'zero':
        shape = m.tensors_to_coefficients(r@np.diag([1., -1., 0.])@r.T/np.sqrt(2.))
        expected = 'SHARED_ZERO_EIGENVALUE_SHAPE'
    else:
        shape = np.array([1., -.3, .2, -.6, .1]); shape /= np.linalg.norm(shape)
        expected = 'SHARED_GENERAL_SHAPE'
    h = np.outer([1.2, -2.3, 0.], shape).ravel()
    out = fit(h, dense_covariance(15), cutoff=1e-12)
    for name in (expected, 'SHARED_GENERAL_SHAPE', 'SHARED_FRAME'):
        answer = out['classes'][name]
        assert answer['status'] == 'INTERSECTS'
        assert answer['objective'] < 1e-22
        assert max(answer['diagnostics']['commutator_norms']) < 1e-14


def test_zero_is_in_every_class_and_has_no_identified_axis():
    out = fit(np.zeros(20), dense_covariance(20), cutoff=0, n_starts=1, grid_size=0)
    for result in out['classes'].values():
        assert result['status'] == 'INTERSECTS'
        assert result['objective'] == 0
        np.testing.assert_array_equal(result['witness'], np.zeros(20))
    # Parameters are reconstruction gauges; a zero-amplitude axis is not data.
    assert out['classes']['SHARED_AXIS']['amplitudes'] == [[0.]]*4


def test_full_covariance_gls_against_independent_normal_equations():
    h = np.array([.4, -.7, .3, 1.2, -.6, -.1, .9, .2, -.4, .8])
    v = dense_covariance(10, 784)
    u = np.array([2., -1., .5]); u /= np.linalg.norm(u)
    shape = m.tensors_to_coefficients(np.sqrt(1.5)*(np.outer(u, u)-np.eye(3)/3))
    design = np.kron(np.eye(2), shape[:, None])
    precision_design = np.linalg.solve(v, design)
    independent_amplitudes = np.linalg.solve(design.T@precision_design, precision_design.T@h)
    answer = m.profile_fixed_orientation(h, v, 'SHARED_AXIS', u)
    np.testing.assert_allclose(answer['amplitudes'].ravel(), independent_amplitudes, rtol=2e-14, atol=1e-15)
    residual = design@independent_amplitudes-h
    assert answer['objective'] == pytest.approx(residual@np.linalg.solve(v, residual), rel=2e-15)
    diagonal_answer = m.profile_fixed_orientation(h, np.diag(np.diag(v)), 'SHARED_AXIS', u)
    assert abs(answer['objective']-diagonal_answer['objective']) > .1


def test_joint_parameter_refit_with_same_dense_covariance():
    # Independently parameterize axis by spherical angles and fit all signed
    # amplitudes simultaneously; do not reuse the variable-projection routine.
    theta, phi = .9, -.6
    u = np.array([np.sin(theta)*np.cos(phi), np.sin(theta)*np.sin(phi), np.cos(theta)])
    shape = m.tensors_to_coefficients(np.sqrt(1.5)*(np.outer(u, u)-np.eye(3)/3))
    h = np.outer([1.3, -.7], shape).ravel()+np.random.default_rng(37).normal(scale=.06, size=10)
    v = dense_covariance(10, 12)
    chol = np.linalg.cholesky(v)
    basis = m.stf_basis()
    def independent_residual(x):
        direction = [np.sin(x[0])*np.cos(x[1]), np.sin(x[0])*np.sin(x[1]), np.cos(x[0])]
        t = np.sqrt(1.5)*(np.outer(direction, direction)-np.eye(3)/3)
        s = np.array([np.sum(e*t) for e in basis])
        return np.linalg.solve(chol, np.outer(x[2:], s).ravel()-h)
    direct = optimize.least_squares(independent_residual, [.7, -.4, 1., -1.],
        ftol=1e-12, xtol=1e-12, gtol=1e-12, max_nfev=180)
    assert direct.success
    answer = fit(h, v)['classes']['SHARED_AXIS']
    assert answer['objective'] == pytest.approx(direct.fun@direct.fun, abs=2e-11)


def test_rotated_refit_and_permuted_tensor_series_preserve_objectives():
    shape = np.array([.6, -.2, .3, .4, -.1]); shape /= np.linalg.norm(shape)
    h = np.outer([1.1, -.8], shape).ravel()+np.random.default_rng(71).normal(scale=.03, size=10)
    v = dense_covariance(10)
    r = Rotation.from_rotvec([.37, -.28, 1.4]).as_matrix()
    rotated = m.rotate_tensor_series(h, v, r)
    original = fit(h, v, n_starts=7, grid_size=28)
    alternate = fit(rotated['mean'], rotated['covariance'], n_starts=7, grid_size=28)
    order = np.r_[np.arange(5, 10), np.arange(5)]
    permuted = fit(h[order], v[np.ix_(order, order)], n_starts=7, grid_size=28)
    for name in m.CLASS_NAMES:
        expected = original['classes'][name]['objective']
        assert alternate['classes'][name]['objective'] == pytest.approx(expected, abs=2e-8)
        assert permuted['classes'][name]['objective'] == pytest.approx(expected, abs=2e-8)
        candidate = np.asarray(alternate['classes'][name]['witness'])
        residual = candidate-rotated['mean']
        assert alternate['classes'][name]['objective'] == pytest.approx(residual@np.linalg.solve(rotated['covariance'], residual), abs=2e-13)


def test_axis_sign_and_eigenframe_permutation_are_gauges():
    h = np.arange(15.)/9-.7
    v = dense_covariance(15)
    u = np.array([.4, -.7, .2])
    positive = m.profile_fixed_orientation(h, v, 'SHARED_AXIS', u)
    negative = m.profile_fixed_orientation(h, v, 'SHARED_AXIS', -u)
    np.testing.assert_array_equal(positive['witness'], negative['witness'])
    r = Rotation.from_rotvec([.8, .2, -.4]).as_matrix()
    permuted = r[:, [2, 0, 1]]
    first = m.profile_fixed_orientation(h, v, 'SHARED_FRAME', r)
    second = m.profile_fixed_orientation(h, v, 'SHARED_FRAME', permuted)
    np.testing.assert_allclose(first['witness'], second['witness'], atol=2e-15)


def test_common_offset_cancellation_full_covariance_and_quotient_class():
    shape = np.array([1., 0, 0, 0, 0])
    common = np.array([0., 0, .8, -.2, .1])
    h = (common+np.outer([-.4, .7, 1.8], shape)).ravel()
    v = dense_covariance(15)
    result = m.common_offset_contrast(h, v)
    expected_op = np.kron(np.array([[-1., 1, 0], [-1., 0, 1]]), np.eye(5))
    np.testing.assert_array_equal(result['operator'], expected_op)
    np.testing.assert_allclose(result['mean'], np.outer([1.1, 2.2], shape).ravel(), atol=1e-15)
    np.testing.assert_allclose(result['covariance'], expected_op@v@expected_op.T, atol=1e-15)
    offset = np.kron(np.ones(3), [.7, -.3, 1.2, -.9, .2])
    shifted = m.common_offset_contrast(h+offset, v)
    np.testing.assert_allclose(shifted['mean'], result['mean'], atol=3e-16)
    shared_noise = np.kron(np.ones((3, 3)), dense_covariance(5))
    noisy = m.common_offset_contrast(h, v+shared_noise)
    np.testing.assert_allclose(noisy['covariance'], result['covariance'], atol=2e-15)
    assert max(m.tensor_series_diagnostics(h)['commutator_norms']) > .5
    quotient_fit = fit(result['mean'], result['covariance'], cutoff=1e-10)
    assert quotient_fit['classes']['SHARED_ZERO_EIGENVALUE_SHAPE']['status'] == 'INTERSECTS'
    assert quotient_fit['classes']['SHARED_FRAME']['status'] == 'INTERSECTS'


def test_quadratic_commutator_forms_match_direct_matrix_multiplication():
    rng = np.random.default_rng(906)
    for k in (1, 2, 4):
        q = rng.normal(size=5*k)
        tensors = m.coefficients_to_tensors(q.reshape(k, 5))
        forms = m.commutator_quadratic_matrices(k)
        assert len(forms) == 3*k*(k-1)//2
        for form in forms:
            i, j = form['pair']; a, b = form['component']
            np.testing.assert_array_equal(form['matrix'], form['matrix'].T)
            assert q@form['matrix']@q == pytest.approx((tensors[i]@tensors[j]-tensors[j]@tensors[i])[a, b], abs=9e-16)


def conservative_quadratic_enclosure(h, v, matrix, *, cutoff):
    # Independent non-sharp bound: |q(h+Au)-q(h)| <= 2||A.T M h||+||A.T M A||.
    a = np.sqrt(cutoff)*np.linalg.cholesky(v)
    center = h@matrix@h
    radius = 2*np.linalg.norm(a.T@matrix@h)+np.linalg.norm(a.T@matrix@a, 2)
    return dict(lower=float(center-radius), upper=float(center+radius),
                guarantee='analytic triangle/spectral norm enclosure')


def test_only_sound_necessary_enclosure_can_exclude_nonlinear_classes():
    h = np.array([[1., 0, 0, 0, 0], [0., 0, 1., 0, 0]]).ravel()
    v = 1e-8*np.eye(10)
    unsupported = fit(h, v, cutoff=1., n_starts=1, grid_size=0, max_nfev=2)
    for name in m.CLASS_NAMES[1:]:
        assert unsupported['classes'][name]['status'] == 'UNRESOLVED'
    supported = fit(h, v, cutoff=1., n_starts=1, grid_size=0, max_nfev=2,
                    commutator_solver=conservative_quadratic_enclosure)
    assert all(x['status'] == 'EXCLUDED' for x in supported['classes'].values())
    assert supported['commutator_enclosures']['excludes_commuting_class']


def test_failed_optimizer_and_failed_enclosure_do_not_become_exclusion(monkeypatch):
    def failed(*args, **kw):
        raise RuntimeError('deliberately simulated optimizer/solver failure')
    monkeypatch.setattr(m.optimize, 'least_squares', failed)
    h = np.array([[1., 0, 0, 0, 0], [0., 0, 1., 0, 0]]).ravel()
    out = fit(h, np.eye(10), cutoff=1e-8, n_starts=2, grid_size=0,
              commutator_solver=failed)
    for name in m.CLASS_NAMES[1:]:
        answer = out['classes'][name]
        assert answer['status'] == 'UNRESOLVED'
        assert answer['witness_verified']
        assert answer['optimization']['converged_starts'] == 0
        assert len(answer['optimization']['runs']) == 2
    assert not out['commutator_enclosures']['excludes_commuting_class']
    assert all(x['status'] == 'UNRESOLVED' for x in out['commutator_enclosures']['ranges'])


def test_enclosure_witness_contradiction_is_an_error():
    def invalid(*args, **kw):
        return dict(lower=1., upper=2.)
    with pytest.raises(ArithmeticError, match='contradicts'):
        fit(np.zeros(10), np.eye(10), commutator_solver=invalid, n_starts=0, grid_size=0)


def test_r61_solver_adapter_if_repository_runtime_available():
    r61 = pytest.importorskip('htt.htt.infer.r61_kinematic_images')
    np.testing.assert_array_equal(m.stf_basis(), r61.stf_basis())
    h = np.array([[1., 0, 0, 0, 0], [0., 0, 1., 0, 0]]).ravel()
    answer = m.commutator_ellipsoid_enclosures(h, 1e-8*np.eye(10), cutoff=1.,
        range_solver=r61.quadratic_ellipsoid_range)
    assert answer['excludes_commuting_class']
    for item in answer['ranges']:
        assert item['status'] == 'COMPUTED'
        result = item['enclosure']
        assert result['lower'] <= result['feasible_lower'] <= result['feasible_upper'] <= result['upper']


@pytest.mark.parametrize('h,v,cutoff', [
    ([], np.eye(1), 1.),
    (np.zeros(6), np.eye(6), 1.),
    (np.zeros(5), np.eye(4), 1.),
    (np.zeros(5), np.zeros((5, 5)), 1.),
    (np.zeros(5), -np.eye(5), 1.),
    (np.ones(5)*np.nan, np.eye(5), 1.),
    (np.zeros(5), np.eye(5), -1.),
    (np.zeros(5), np.eye(5), np.inf),
    (np.zeros(25), np.eye(25), 1.),
])
def test_invalid_carriers_fail_explicitly(h, v, cutoff):
    with pytest.raises(ValueError):
        fit(h, v, cutoff)


def test_invalid_shapes_rotation_covariance_and_budget():
    v = np.eye(5); v[0, 1] = .1
    with pytest.raises(ValueError, match='symmetric'):
        fit(np.zeros(5), v)
    with pytest.raises(ValueError, match='SO'):
        m.stf_rotation_matrix(np.diag([1., 1., -1.]))
    with pytest.raises(ValueError):
        m.profile_fixed_orientation(np.zeros(5), np.eye(5), 'SHARED_AXIS', np.zeros(3))
    with pytest.raises(ValueError):
        m.common_offset_operator(1)
    with pytest.raises(ValueError):
        fit(np.zeros(5), np.eye(5), n_starts=True)
    with pytest.raises(ValueError):
        fit(np.zeros(5), np.eye(5), max_nfev=0)
    with pytest.raises(ValueError, match='positive cutoff'):
        fit(np.zeros(5), np.eye(5), cutoff=0, commutator_solver=conservative_quadratic_enclosure)

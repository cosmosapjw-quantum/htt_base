from dataclasses import replace
import numpy as np
import pytest
from common.depth_path import DepthRepresentation
from common.r9_product import ProductIntake, SharedStateEmbedding
from common.r7_contracts import ScopeKey, UnavailableLaw
from htt.infer.r7_gaussian_law import JointObservationLaw
from htt.infer.r9_depth_law import embed_product, depth_law, depth_diagnostic, full_past_innovations


def fixture(c=None, y=None, nuisance=False):
    c = np.eye(3) if c is None else np.array(c, float)
    y = np.array([1., 2., 3.] if y is None else y)
    ids = ('z0', 'z1', 'z2')
    law = JointObservationLaw(ScopeKey('test', 'law', 'model', ('source',), method_config_id='fixed'),
        y, ids, ('mu',), ('K',), lambda t, e: np.full(3, t[0]+(e[0] if nuisance else 0.)), c,
        {'source_ids': ['source'], 'selection_law': 'fixed', 'covariance_source': 'known', 'mean_definition': 'common mu'},
        'real', lambda t, e: True, jacobian_theta=lambda t, e: np.ones((3, 1)),
        jacobian_eta=lambda t, e: np.ones((3, 1)) if nuisance else np.empty((3, 0)),
        shared_latent_ids=('zero_point',) if nuisance else ())
    intake = ProductIntake('test', 'r1', ('source',), ids, ('K',)*3, 'frame', 'epoch',
                          'fixed', 'fixed', 'group', 'calibration', 'mask', 'known', ids, 'KNOWN_GAUSSIAN')
    p = DepthRepresentation((1, 1, 1), (np.ones((1, 1)),)*2, ids, 'fixed')
    return law, intake, p


def test_full_law_initial_level_response_and_likelihood_parity():
    law, intake, p = fixture()
    path = depth_law(law, intake, p)
    np.testing.assert_array_equal(path.observed, [1, 1, 1])
    np.testing.assert_array_equal(path.mean([7], None), [7, 0, 0])
    np.testing.assert_array_equal(path.jacobian_theta([7], None), [[1], [0], [0]])
    np.testing.assert_array_equal(path.covariance, [[1, -1, 0], [-1, 2, -1], [0, -1, 2]])
    for mu in (-10, 0, 3, 20):
        assert path.loglik([mu]) == pytest.approx(law.loglik([mu]), abs=1e-10)
    with pytest.raises(ValueError, match='erase'):
        depth_law(law, intake, p, view='CONTRASTS_ONLY')
    d = depth_diagnostic(law, intake, p, [7])
    np.testing.assert_array_equal(d['covariance'], [[2, -1], [-1, 2]])
    assert d['probability'] is None and not d['independent_likelihood']


@pytest.mark.parametrize('rho', [-.8, 0., .8])
def test_cross_block_signs(rho):
    law, intake, p = fixture([[1, rho, 0], [rho, 1, 0], [0, 0, 1]])
    d = depth_diagnostic(law, intake, p, [0])
    np.testing.assert_allclose(d['covariance'], [[2-2*rho, rho-1], [rho-1, 2]], atol=1e-10)


def test_duplicate_support_and_unknown_covariance_are_distinct():
    law, intake, p = fixture(np.ones((3, 3)), [2, 2, 2])
    d = depth_diagnostic(law, intake, p, [0])
    assert d['rank'] == 0 and d['quadratic'] == 0
    law = replace(law, observed=[2., 3., 2.])
    d = depth_diagnostic(law, intake, p, [0])
    assert d['status'] == 'OUTSIDE_DETERMINISTIC_SUPPORT' and d['quadratic'] is None
    assert isinstance(depth_law(law, replace(intake, covariance_source=None), p), UnavailableLaw)


def test_fitted_covariance_transport_and_identity_refusals():
    law, intake, p = fixture()
    assert isinstance(depth_law(law, intake, replace(p, transport_policy='FITTED_REQUIRES_JOINT_LAW')), UnavailableLaw)
    assert isinstance(depth_law(law, replace(intake, law_kind='ESTIMATED_REQUIRES_CALIBRATION'), p), UnavailableLaw)
    with pytest.raises(ValueError, match='mismatch'):
        depth_law(law, replace(intake, source_ids=('other-release',)), p)
    with pytest.raises(ValueError, match='order'):
        depth_law(law, intake, replace(p, feature_ids=('z1', 'z0', 'z2')))
    with pytest.raises(ValueError, match='rows'):
        replace(intake, covariance_row_ids=('z1', 'z0', 'z2'))


def test_full_past_is_not_previous_block_regression():
    law, intake, p = fixture([[1, .5, .5], [.5, 1, .5], [.5, .5, 1]])
    innovations = full_past_innovations(law, intake, p, [0])
    np.testing.assert_allclose(innovations[1]['gain'], [[1/3, 1/3]], atol=1e-10)
    np.testing.assert_allclose(innovations[1]['covariance'], [[2/3]], atol=1e-10)
    assert innovations[1]['past_blocks'] == 2


def test_innovations_check_original_support_before_conditioning():
    law, intake, _ = fixture(np.diag([1., 0., 1.]), [1., 1e-16, 0.])
    p = DepthRepresentation((2, 1), (np.zeros((1, 2)),), law.measurement_ids, 'fixed')
    with pytest.raises(ValueError, match='support'):
        full_past_innovations(law, intake, p, [0.])


def test_shared_nuisance_is_a_real_common_coordinate():
    law, intake, p = fixture(nuisance=True)
    embedding = SharedStateEmbedding('state', ('mu', 'zero_point'), ('K', 'K'),
        ('OBSERVABLE', 'SHARED_NUISANCE'), 'frame', 'epoch', ('mu',), ('K',),
        ('zero_point',), ('K',), [[1, 0]], [[0, 1]])
    bound = embed_product(law, intake, embedding)
    np.testing.assert_array_equal(bound.mean([2, 3], None), [5, 5, 5])
    np.testing.assert_array_equal(bound.jacobian_theta([2, 3], None), np.ones((3, 2)))
    path = depth_law(bound, intake, p)
    np.testing.assert_array_equal(path.jacobian_theta([2, 3], None), [[1, 1], [0, 0], [0, 0]])
    legacy = replace(law, jacobian_eta=lambda t, e: np.empty((3, 0)))
    with pytest.raises(ValueError, match='shape'):
        embed_product(legacy, intake, embedding).jacobian_theta([2, 3], None)
    with pytest.raises(ValueError, match='frame'):
        embed_product(law, intake, replace(embedding, frame='different'))
    with pytest.raises(ValueError, match='unit'):
        replace(embedding, state_units=('mK', 'K'))


def test_production_covariance_replays_frozen_tail_counterexample():
    from scipy.stats import chi2
    law, intake, p = fixture()
    d = depth_diagnostic(law, intake, p, [0])
    draws = np.random.default_rng(20260912).standard_normal((100000, 3))
    residuals = draws @ p.H.T
    full = np.einsum('ni,ij,nj->n', residuals, np.linalg.inv(d['covariance']), residuals)
    dropped = np.sum(residuals**2/np.diag(d['covariance']), axis=1)
    threshold = chi2.ppf(.95, 2)
    assert abs(np.mean(full > threshold)-.05) <= .005
    assert np.mean(dropped > threshold) > .055

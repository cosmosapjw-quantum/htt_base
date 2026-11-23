"""Independent conditional-density identities for shared-field mark holdout."""
import numpy as np
import unittest
from numpy.testing import assert_allclose
from scipy.stats import norm

from htt.infer.cf4_predictive_response import selected_probit_holdout


class TestSharedFieldHoldout(unittest.TestCase):
    def test_direct_finite_field_enumeration(self):
        p = np.array([.65, .35])
        mu = np.array([[-.1, .3, .8, -.5], [.9, -.2, -.4, .1]])
        y = np.array([.3, np.nan, .7, np.nan])
        sig = np.array([.3, .5, .9, .4])
        a, b = np.array([.1, -.2, .6, 0]), -.8
        tr = np.array([True, True, False, False])
        ans = selected_probit_holdout(y, mu, sig, a, b, p, included=np.isfinite(y), train=tr)
        # Enumerate the two generative models by independent CDF/PDF products.
        train_joint, test_joint, test_pattern = [], [], []
        for u in mu:
            prob = norm.cdf((a + b*u)/np.sqrt(1. + (b*sig)**2))
            mark0 = norm.pdf(y[0], u[0], sig[0])*norm.cdf(a[0] + b*y[0])
            mark2 = norm.pdf(y[2], u[2], sig[2])*norm.cdf(a[2] + b*y[2])
            train_joint.append(mark0*(1. - prob[1]))
            test_joint.append(mark2*(1. - prob[3]))
            test_pattern.append(prob[2]*(1. - prob[3]))
        post = p * train_joint
        post /= post.sum()
        assert_allclose(np.exp(ans["train_field_log_weights"]), post, atol=1.e-14)
        assert_allclose(ans['shared_log_density'], np.log(np.dot(post, test_joint)/np.dot(post, test_pattern)), atol=1.e-14)
        assert_allclose(ans['fresh_log_density'], np.log(np.dot(p, test_joint)/np.dot(p, test_pattern)), atol=1.e-14)
        assert abs(ans['shared_log_density'] - ans['fresh_log_density']) > 1e-4


    def test_opposing_extreme_blocks_preserve_training_log_support(self):
        # Each field fits exactly one block. In exp space one training weight is 0,
        # yet the test joint receives equal contributions from the two histories.
        y = np.array([0., 50.])
        mu = np.array([[0., 0.], [50., 50.]])
        ans = selected_probit_holdout(y, mu, 1., 0., 0., [.5, .5],
                                      included=np.ones(2, bool), train=np.array([True, False]))
        assert_allclose(np.min(ans['train_field_log_weights']), -1250., atol=1.e-11)
        assert_allclose(ans['shared_log_density'], norm.logpdf(50.) + np.log(2.), atol=1.e-11)


    def test_no_test_marks_given_pattern(self):
        y = np.array([.2, np.nan, np.nan])
        mu = np.array([[1., 2., 0.], [0., 0., 5.]])
        ans = selected_probit_holdout(y, mu, 1., -1., .5, [.3, .7],
                                      included=np.isfinite(y), train=np.array([True, False, False]))
        assert_allclose(ans["shared_minus_zero"], 0., atol=1.e-14)


    def test_invalid_train_partitions(self):
        for train in ([0, 1], [True, True], [False, False], [True]):
            with np.testing.assert_raises_regex(ValueError, 'partition'):
                selected_probit_holdout([.1, .2], [[0., 1.]], 1., .3, 1., [1.],
                                        included=[True, True], train=train)

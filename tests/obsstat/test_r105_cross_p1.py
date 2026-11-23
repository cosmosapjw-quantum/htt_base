import itertools
import unittest

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import xlogy

from scripts.r105.cross_routes import missing_support, normal_direction_coverage, radio_axis
from scripts.r105.p1_ordering import tie_law


class TestRelativeEntropy(unittest.TestCase):
    def test_exact_tie_vs_scalar_optimization(self):
        counts=[1099,939,10]
        prob=np.array(counts)/sum(counts)
        def brute(a):
            q=np.array([a,1-2*a,a])
            return np.sum(xlogy(q,q/prob))
        fitted=minimize_scalar(brute,bounds=(0,.5),method='bounded', options={'xatol':1.e-14})
        sol=tie_law(counts)
        self.assertAlmostEqual(fitted.fun,sol['KL_nats_to_tie'],places=12)
        np.testing.assert_allclose(sol['tie_law_minus_zero_plus'],[fitted.x,1-2*fitted.x,fitted.x],atol=5e-8)
        self.assertTrue(sol['strict_reversal_feasible'])

    def test_missing_original_support_and_nearly_equal_mass(self):
        self.assertFalse(tie_law([2,0,0])['feasible_tie'])
        self.assertEqual(tie_law([1,4,0])['tie_law_minus_zero_plus'],[0,1,0])
        self.assertAlmostEqual(tie_law([1,4,0])['KL_nats_to_tie'],-np.log(.8))
        self.assertFalse(tie_law([0,3,2])['strict_reversal_feasible'])
        self.assertGreater(tie_law([1,3,1+1e-10])['KL_nats_to_tie'],0)


class TestSourceBounds(unittest.TestCase):
    def test_independent_and_coherent_extreme_points(self):
        n=np.eye(3)
        w=np.array([[1.2,-2.,3.],[-.7,.08,1.5]])
        box,coh=missing_support(w,n)
        corners=np.array(list(itertools.product([-1,1],repeat=3)))
        np.testing.assert_allclose((w@corners.T).max(1),box)
        for row,radius in zip(w,coh):
            b=(row@n)/np.linalg.norm(row@n)
            self.assertAlmostEqual(row@(n@b),radius)
        self.assertTrue(np.all(coh<=box))

    def test_radial_window_constant_on_shell_and_row_invariance(self):
        rng=np.random.default_rng(170)
        n=rng.normal(size=(90,3));n/=np.linalg.norm(n,axis=1)[:,None]
        c=normal_direction_coverage(n,np.full(len(n),250.))
        np.testing.assert_allclose(c['retained_fraction_extremes'],[0,0],atol=1e-14)
        r=np.linspace(40,400,len(n))
        obs=normal_direction_coverage(n,r)
        q=np.linalg.qr(rng.normal(size=(3,3)))[0]
        rotated=normal_direction_coverage(n@q,r)
        np.testing.assert_allclose(obs['canonical_correlations'],rotated['canonical_correlations'],rtol=1e-13)
        self.assertGreater(min(obs['retained_fraction_extremes']),0.)

    def test_radio_axis_projection_matches_residual_contrast(self):
        c=np.array([[2.,.32],[.32,1.]])
        d=np.array([.2,-1.4]); a=np.array([.9,.23]); z=np.array([-a[1],a[0]])
        report=radio_axis(d,c,a)
        self.assertAlmostEqual(report['profiled_wald'],(z@d)**2/(z@c@z))
        self.assertAlmostEqual(report['GLS_orthogonality_abs'],0.)

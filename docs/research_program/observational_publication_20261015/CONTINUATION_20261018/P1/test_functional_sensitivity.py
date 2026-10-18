"""Local selected-subset falsifiers; not primary-checkout validation."""
import unittest
from pathlib import Path
import numpy as np
from scipy.optimize import linprog
import functional_sensitivity as f
from h03_tomography import STF


class FunctionalSensitivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source, cls.theta, cls.cov = f.read_statistics(f.ROOT/'source/H03_SOURCE_TOMOGRAPHY.json')
        cls.draws = f.joint_draws(cls.theta, cls.cov)
        cls.a = f.ratio(cls.draws)

    def test_summary_identity_and_coupling(self):
        self.assertEqual(self.draws.shape,(2048,4,9))
        np.testing.assert_allclose((self.draws[:1024]+self.draws[1024:])/2,
                                   np.broadcast_to(self.theta,(1024,4,9)),atol=3e-14,rtol=0)
        self.assertEqual(np.full(2048,1/2048).sum(),1.)
        self.assertGreater(np.max(np.abs(self.cov[:9,9:])),0.01)

    def test_exact_archived_event_counts(self):
        c = f.lower_certificates(self.draws,.02,3.,[.2]*4)
        self.assertEqual(c['rectangular_lower_count'],85)
        self.assertEqual(c['coherent_pairwise_lower_count'],1094)
        self.assertEqual(int(np.sum((self.a>.05).any(axis=1))),1235)
        self.assertEqual(list(np.sum(self.a>.05,axis=0)),[0,136,1225,11])

    def test_signed_negative_values_survive_anchor(self):
        signed = self.draws[:,:,4] / self.draws[:,:,0]
        score = f.anchored_score(signed,.05)
        np.testing.assert_array_equal(score<0,signed<0)
        self.assertGreater(int((score<0).sum()),6000)
        with self.assertRaises(ValueError): f.anchored_score(signed,0)

    def test_stf_norm_is_the_original_frobenius_norm(self):
        np.testing.assert_allclose(np.einsum('aij,bij->ab',STF,STF),np.eye(5),atol=3e-16,rtol=0)
        tensor=np.einsum('nja,akl->njkl',self.draws[:,:,4:9],STF)
        np.testing.assert_allclose(np.linalg.norm(tensor,axis=(-2,-1))/self.draws[:,:,0],self.a,atol=3e-17,rtol=1e-15)

    def test_zero_versus_missing_and_floor_ties(self):
        finite = f.floor_depth(np.array([[0.,.1,0.,.2]]),.05,.5)
        np.testing.assert_allclose(finite,[[4.,1.,8.]])
        with self.assertRaises(ValueError): f.floor_depth(np.array([[np.nan,.1,0.,.2]]),.05,.5)
        saturated = f.floor_depth(self.a,.05,1.5)
        np.testing.assert_array_equal(saturated,np.ones_like(saturated))
        self.assertEqual(int((saturated>1).sum()),0)

    def test_anchor_floor_product_identity(self):
        one = f.floor_depth(self.a,.05,.5)
        two = f.floor_depth(self.a,.1,.25)
        np.testing.assert_allclose(one,two,atol=0,rtol=0)
        self.assertGreater(np.max(np.abs(one-f.floor_depth(self.a,.1,.5))),.5)

    def test_shared_draw_permutation_preserves_joint_event(self):
        perm = np.random.default_rng(817).permutation(len(self.a))
        self.assertEqual(int((self.a>.05).any(axis=1).sum()),int((self.a[perm]>.05).any(axis=1).sum()))
        marginal = (self.a>.05).mean(axis=0)
        self.assertGreater(abs(1-np.prod(1-marginal)-(self.a>.05).any(axis=1).mean()),.02)

    def test_density_bounds_against_independent_linear_program(self):
        # Direct optimization over individual nonuniform source masses.
        p = np.array([.05,.15,.3,.5])
        for gamma in [1.,1.25,2.,4.,20.]:
            for yes,missing in [([0],[2]),([0,1],[]),([],[0,1,2,3]),([0,1,2,3],[])]:
                known = np.zeros(4);known[yes]=1
                possible = known.copy();possible[missing]=1
                lo = linprog(known,A_eq=np.ones((1,4)),b_eq=[1.],bounds=list(zip(p/gamma,p*gamma)),method='highs')
                hi = linprog(-possible,A_eq=np.ones((1,4)),b_eq=[1.],bounds=list(zip(p/gamma,p*gamma)),method='highs')
                self.assertTrue(lo.success and hi.success)
                analytical = f.density_envelope(float(p@known),float(p[missing].sum()),gamma)
                np.testing.assert_allclose(analytical,[lo.fun,-hi.fun],atol=2e-14,rtol=0)

    def test_density_monotonic_and_endpoints(self):
        prev=[.3,.8]
        for gamma in [1.,1.1,1.25,2.,4.,20.]:
            bounds=f.density_envelope(.3,.5,gamma)
            self.assertLessEqual(bounds[0],prev[0]);self.assertGreaterEqual(bounds[1],prev[1]);prev=bounds
            self.assertEqual(f.density_envelope(0,1,gamma),[0.,1.])
        self.assertEqual(f.density_envelope(0,0,3),[0.,0.])
        self.assertEqual(f.density_envelope(1,0,3),[1.,1.])
        with self.assertRaises(ValueError): f.density_envelope(.7,.5,2)

    def test_physical_unknown_mass_not_renormalized(self):
        partial=f.physical_partial(2048,self.source['source_SHA256'])
        for key in ['Q','F','G_F']:
            ans=partial.exceedance(key,[0,.5,1])
            self.assertEqual(ans['unknown_mass'],1.)
            self.assertEqual(ans['known_mass'],0.)
            self.assertEqual(ans['lower'],[0.,0.,0.]);self.assertEqual(ans['upper'],[1.,1.,1.])
        self.assertEqual(partial.exceedance('Q',[.5])['unmeasured_defined_mass'],1.)
        self.assertEqual(partial.exceedance('F',[.5])['domain_uncertified_mass'],1.)

    def test_strict_weighted_tie_and_unknown_example(self):
        reasons={'F':'domain_uncertified','G_F':'domain_uncertified'}
        ds=[f.PartialDraw('a',.2,'one','0'*64,q=-.8,missing_reasons=reasons),
            f.PartialDraw('b',.3,'one','0'*64,q=.5,missing_reasons=reasons),
            f.PartialDraw('c',.5,'one','0'*64,missing_reasons={**reasons,'Q':'unmeasured_defined'})]
        ans=f.PartialMeasure(tuple(ds)).exceedance('Q',[.2,.5])
        self.assertEqual(ans['lower'],[.3,0.]);self.assertEqual(ans['upper'],[.8,.5])

    def test_actual_alternative_fit_not_promoted_to_draw_law(self):
        north=np.array([r['theta9'] for r in self.source['north_weighted_same_sky_sensitivity']])
        change=f.ratio(north)/f.ratio(self.theta)-1
        self.assertLess(change[-1],-.16)
        self.assertGreater(change[1],.08)
        families=f.selection_fit_bounds(self.source,self.theta)
        self.assertEqual(len(families),4)
        for fam in families:
            for row in fam['windows']:
                self.assertLessEqual(*row['ratio_outer'])


if __name__=='__main__':unittest.main(verbosity=2)

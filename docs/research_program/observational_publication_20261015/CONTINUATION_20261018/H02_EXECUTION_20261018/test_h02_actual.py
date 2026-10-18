"""Independent estimator/box/null controls; no physical selection qualification."""
import unittest
from pathlib import Path
import sys
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
from h02_actual import fit_profiled, minimum_delta, intervals, coupled_box, geometry, SOURCE


class ActualCentersTests(unittest.TestCase):
    def setUp(self):
        rng=np.random.default_rng(20261018)
        self.n=rng.normal(size=(120,3));self.n/=np.linalg.norm(self.n,axis=1)[:,None]
        self.x=geometry.shape8(self.n)
        self.sigma=rng.uniform(.1,.6,len(self.x))
        self.y=rng.normal(size=len(self.x))
        self.kernel=rng.uniform(.01,1,len(self.x))

    def test_profiled_matches_full_intercept_svd_and_covariance(self):
        fit,a=fit_profiled(self.x,self.y,self.sigma,self.kernel)
        design=np.column_stack((np.ones(len(self.x)),self.x))
        sqrtw=np.sqrt(self.kernel)/self.sigma
        expected=np.linalg.lstsq(sqrtw[:,None]*design,sqrtw*self.y,rcond=None)[0]
        amap_full=np.linalg.pinv(sqrtw[:,None]*design)*sqrtw
        expected_cov=(amap_full*self.sigma**2)@amap_full.T
        np.testing.assert_allclose(fit['coefficients_mag'],expected[1:],atol=2e-14,rtol=1e-12)
        np.testing.assert_allclose(a,amap_full[1:],atol=2e-14,rtol=1e-12)
        np.testing.assert_allclose(fit['working_covariance'],expected_cov[1:,1:],atol=2e-14,rtol=1e-12)

    def test_kernel_covariance_is_not_naive_inverse_gram(self):
        fit,_=fit_profiled(self.x,self.y,self.sigma,self.kernel)
        self.assertGreater(np.linalg.norm(np.array(fit['working_covariance'])-np.linalg.inv(fit['gram'])),.001)
        base,_=fit_profiled(self.x,self.y,self.sigma)
        np.testing.assert_allclose(base['working_covariance'],np.linalg.inv(base['gram']),atol=2e-14)

    def test_global_zero_point_profiles_out(self):
        first,_=fit_profiled(self.x,self.y,self.sigma,self.kernel)
        shifted,_=fit_profiled(self.x,self.y-.147,self.sigma,self.kernel)
        np.testing.assert_allclose(first['coefficients_mag'],shifted['coefficients_mag'],atol=2e-14)

    def test_shared_angular_calibration_shift_is_not_removed(self):
        eta=np.arange(8)*.01
        for kernel in (None,self.kernel):
            first,_=fit_profiled(self.x,self.y,self.sigma,kernel)
            shifted,_=fit_profiled(self.x,self.y+self.x@eta,self.sigma,kernel)
            np.testing.assert_allclose(np.array(shifted['coefficients_mag'])-first['coefficients_mag'],eta,atol=2e-14)

    def test_overlapping_windows_cross_covariance_direct_map(self):
        _,a=fit_profiled(self.x,self.y,self.sigma,self.kernel)
        _,b=fit_profiled(self.x,self.y,self.sigma,1-self.kernel/2)
        joint=np.concatenate((a,b),axis=0)*self.sigma
        cov=joint@joint.T
        np.testing.assert_allclose(cov[:8,8:],(a*self.sigma**2)@b.T,atol=2e-14)
        self.assertGreater(np.max(np.abs(cov[:8,8:])),.0001)
        self.assertGreater(np.linalg.eigvalsh(cov).min(),-1e-12)

    def test_noiseless_isotropic_source_has_zero_spurious_shape(self):
        fit,_=fit_profiled(self.x,np.full(len(self.x),3.25),self.sigma,self.kernel)
        np.testing.assert_allclose(fit['coefficients_mag'],0.,atol=1e-14)

    def test_error_scale_and_lognormal_bias_control(self):
        # This exact Gaussian modulus moment illustrates why changing to
        # linear distance without correction does not preserve the mean.
        k=np.log(10)/5
        nodes,weights=np.polynomial.hermite.hermgauss(32)
        quadrature=np.exp(np.sqrt(2)*k*self.sigma[:,None]*nodes)@weights/np.sqrt(np.pi)
        np.testing.assert_allclose(quadrature,np.exp(.5*(k*self.sigma)**2),rtol=2e-14)
        np.testing.assert_array_less(1.,quadrature)
        fit,_=fit_profiled(self.x,self.y,self.sigma)
        scaled,_=fit_profiled(self.x,self.y,2*self.sigma)
        np.testing.assert_allclose(fit['coefficients_mag'],scaled['coefficients_mag'],atol=2e-14)
        np.testing.assert_allclose(np.array(fit['working_covariance'])*4,scaled['working_covariance'],atol=2e-14)

    def test_minimum_delta_threshold_and_unequal_radii(self):
        b=np.array([-.1,.1,.02,.04]);q=np.array([.01,.03,.02,.04])
        delta=minimum_delta(b,q)
        self.assertAlmostEqual(delta,.08)
        self.assertAlmostEqual(max(b-q-delta),min(b+q+delta))
        self.assertGreater(max(b-q-(delta-1e-5)),min(b+q+(delta-1e-5)))

    def test_union_budget_counts_every_window_and_contrast(self):
        block={'coefficients_mag':[0.]*8,'working_covariance':np.eye(8).tolist()}
        fake={w:{m:block for m in geometry.LABELS} for w in ('all','w1','w2','w3','w4')}
        result=intervals(fake,deltas=(0.,))
        self.assertEqual(result['simultaneous_comparisons'],160)
        self.assertEqual(len(result['rows']),80)
        self.assertTrue(all(not r['empty'] for r in result['rows']))

    def test_coupled_calibration_rejects_individually_compatible_windows(self):
        b=np.array([[0.,0.],[0.,1.]])
        q=np.full_like(b,.01)
        # Each individual window has finite delta; their method differences
        # cannot be explained by one constant method calibration vector.
        self.assertAlmostEqual(minimum_delta(b[1],q[1]),.49)
        self.assertFalse(coupled_box(b,q)['feasible'])
        self.assertFalse(coupled_box(b,q,10.)['feasible'])

    def test_coupled_projection_and_minimum_recover_constructed_witness(self):
        b=np.array([[.1,-.1],[.3,.1]])
        q=np.full_like(b,.02)
        result=coupled_box(b,q)
        self.assertTrue(result['feasible'])
        self.assertAlmostEqual(result['minimum_delta_mag'],.08)
        projected=coupled_box(b,q,.1)
        np.testing.assert_allclose(projected['projections'],[[-.02,.02],[.18,.22]],atol=1e-12)

    def test_reject_invalid_and_rank_deficient(self):
        for bad in (np.zeros_like(self.sigma),np.full_like(self.sigma,np.nan)):
            with self.assertRaises(ValueError):fit_profiled(self.x,self.y,bad)
        with self.assertRaises(ValueError):fit_profiled(np.ones_like(self.x),self.y,self.sigma)
        with self.assertRaises(ValueError):minimum_delta([0,1],[.1,-.1])

    @unittest.skipUnless(SOURCE.exists(),'local immutable observed rows unavailable')
    def test_original_source_identity_and_family(self):
        n,m,s,z=geometry.read_source(SOURCE)
        self.assertEqual(n.shape,(35970,3))
        self.assertEqual(set(m),set(geometry.LABELS))


if __name__=='__main__':unittest.main()

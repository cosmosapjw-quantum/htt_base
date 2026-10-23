"""Focused falsifiers; no raw-catalogue or solver campaign."""
import itertools
import unittest
import numpy as np
from numpy.testing import assert_allclose
import acceleration_channel as ac


class AccelerationChannelTests(unittest.TestCase):
    def setUp(self):
        self.g, self.cov = ac.load_summary()

    def test_source_covariance_and_units(self):
        self.assertTrue(np.all(np.linalg.eigvalsh(self.cov) > 0))
        assert_allclose(np.sqrt(np.diag(self.cov)), [.41,.35,.36], atol=1e-15)
        self.assertAlmostEqual(ac.UAS_YR_TO_M_S2, 4.60566e-11, delta=5e-17)
        self.assertAlmostEqual(np.linalg.norm(self.g)*ac.UAS_YR_TO_M_S2, 2.32e-10, delta=1e-12)

    def test_response_matches_aberration_derivative(self):
        for ra, dec in [(0.,0.),(1.2,.4),(5.,-1.1)]:
            n, d = ac.sky_basis(ra, dec)
            assert_allclose(d@ac.cartesian_response(n), d, atol=1e-15)
            assert_allclose(d.T@d, ac.cartesian_response(n), atol=1e-15)
            v = np.array([.003,-.002,.001])
            h = 1e-4
            def aberr(beta): return beta - np.dot(beta,n)*n
            numeric = (aberr(v+h*self.g)-aberr(v-h*self.g))/(2*h)
            assert_allclose(d@numeric, d@self.g, atol=1e-13)

    def test_apex_null_equatorial_sign_and_rank(self):
        apex = self.g/np.linalg.norm(self.g)
        assert_allclose(ac.cartesian_response(apex)@self.g, np.zeros(3), atol=3e-15)
        assert_allclose(ac.tangent_response(0,0)@self.g, [self.g[1],self.g[2]])
        stacked = np.vstack([ac.tangent_response(0,0),ac.tangent_response(np.pi/2,0)])
        self.assertEqual(np.linalg.matrix_rank(stacked),3)

    def test_electric_dipole_divergence_and_curl(self):
        h = 1e-5
        for ra,dec in [(1.2,.4),(5.,-1.1)]:
            def f(a,d): return ac.tangent_response(a,d)@self.g
            da = (f(ra+h,dec)-f(ra-h,dec))/(2*h)
            dd_cos = (np.cos(dec+h)*f(ra,dec+h)-np.cos(dec-h)*f(ra,dec-h))/(2*h)
            div = (da[0]+dd_cos[1])/np.cos(dec)
            curl = (da[1]-dd_cos[0])/np.cos(dec)
            n,_ = ac.sky_basis(ra,dec)
            self.assertAlmostEqual(div,-2*self.g@n,delta=2e-9)
            self.assertAlmostEqual(curl,0.,delta=2e-9)

    def test_rotation_field_covariance_and_likelihood(self):
        r = ac.ICRS_TO_GAL
        assert_allclose(r@r.T,np.eye(3),atol=3e-15)
        n,_ = ac.sky_basis(1.7,-.3)
        assert_allclose(ac.cartesian_response(r@n)@r@self.g,r@ac.cartesian_response(n)@self.g,atol=3e-15)
        point = np.array([.3,-3.8,-3.2])
        self.assertAlmostEqual(ac.quadratic(point,self.g,self.cov),ac.quadratic(r@point,r@self.g,r@self.cov@r.T),places=12)
        self.assertAlmostEqual(ac.gaussian_loglike(point,self.g,self.cov),ac.gaussian_loglike(r@point,r@self.g,r@self.cov@r.T),places=12)

    def test_cross_sky_mean_covariance_psd(self):
        points = [(0.,0.),(1.,.3),(2.,-.5)]
        ds = np.vstack([ac.tangent_response(a,d) for a,d in points])
        joint = ds@self.cov@ds.T
        self.assertGreater(np.linalg.eigvalsh(joint).min(),-1e-14)
        self.assertEqual(np.linalg.matrix_rank(joint),3)
        assert_allclose(ac.cross_prediction_covariance(*points[0],*points[1],self.cov),joint[:2,2:4])

    def test_published_galactic_rounding_envelope(self):
        # Both sets of Table2 sigmas were rounded independently. A naive exact
        # equality test fails; propagate the declared printed precision instead.
        r = ac.ICRS_TO_GAL
        for i,target in enumerate([5.04,-.10,-.29]):
            max_rounding = .005*np.sum(np.abs(r[i]))+.005
            self.assertLess(abs((r@self.g)[i]-target),max_rounding)
        sigma = np.sqrt(np.diag(self.cov))
        sigmas, corrs = [], []
        for signs in itertools.product([-1,1],repeat=6):
            sd = sigma + .005*np.array(signs[:3])
            xy,xz,yz = np.array([.001,-.094,-.025])+.0005*np.array(signs[3:])
            c = np.array([[1,xy,xz],[xy,1,yz],[xz,yz,1]])*np.outer(sd,sd)
            gc = r@c@r.T; gs = np.sqrt(np.diag(gc))
            sigmas.append(gs); corrs.append(gc/np.outer(gs,gs))
        for i,target in enumerate([.35,.36,.41]):
            self.assertLessEqual(np.min(sigmas,axis=0)[i],target+.005)
            self.assertGreaterEqual(np.max(sigmas,axis=0)[i],target-.005)
        # Correlations DO NOT reconcile. Preserve the source qualification
        # failure explicitly rather than weakening the parity tolerance.
        audit = ac.published_frame_covariance_audit()
        self.assertEqual(audit['status'],'FAIL_PRINTED_FRAME_COVARIANCE_PARITY')
        self.assertLess(audit['global_upper_rho_XY'],audit['published_lower_rho_XY'])

    def test_ellipsoid_bias_threshold_kkt(self):
        r2 = ac.chi2.ppf(.95,3)
        b = ac.smallest_additive_bias_to_include_zero(self.g,self.cov,r2)
        self.assertAlmostEqual(ac.quadratic(b,self.g,self.cov),r2,places=11)
        # KKT: b is parallel to C^-1(mean-b), verifies convex optimum.
        score = np.linalg.solve(self.cov,self.g-b)
        self.assertLess(np.linalg.norm(np.cross(b,score)),1e-11)
        self.assertGreater(b@score,0.)
        self.assertGreater(ac.quadratic(.999*b,self.g,self.cov),r2)

    def test_unrestricted_cosmic_local_degeneracy(self):
        d = np.column_stack([np.eye(3),np.eye(3)])
        null = np.vstack([np.eye(3),-np.eye(3)])
        assert_allclose(d@null, np.zeros((3,3)))
        self.assertEqual(np.linalg.matrix_rank(d),3)
        for k in [np.zeros(3),np.array([10.,-20.,30.])]:
            b = self.g-k
            self.assertLess(ac.quadratic(k+b,self.g,self.cov),1e-25)


if __name__ == "__main__":
    unittest.main(verbosity=2)

"""Narrow independent tests of the declared Gaussian division algebra."""
import unittest
import numpy as np
from numpy.testing import assert_allclose
import importlib.util
from pathlib import Path
sp=importlib.util.spec_from_file_location('uprior',Path(__file__).resolve().parents[2]/'scripts/run_solver_free_union_prior.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
transform,identity_check=m.transform,m.identity_check


class GaussianDivisionTests(unittest.TestCase):
    def setUp(self):
        rng = np.random.default_rng(221014)
        a = rng.normal(size=(22,22))
        self.p = a.T @ a + 3*np.eye(22)
        self.ref = np.linspace(36.,46.,22)
        self.mu = self.ref + rng.normal(scale=.12,size=22)

    def test_independent_logpdf_identity(self):
        for lam in (0.,.5,1.):
            check = identity_check(self.mu,self.p,self.ref,lam)
            self.assertEqual(check['status'],'PASS')

    def test_zero_removal_recovers_original(self):
        mu,p,constant = transform(self.mu,self.p,self.ref,0.)
        assert_allclose(mu,self.mu,rtol=0,atol=1e-13)
        assert_allclose(p,self.p,rtol=0,atol=0)
        self.assertLess(abs(constant),1e-12)

    def test_full_removal_information_vector(self):
        mu,p,_ = transform(self.mu,self.p,self.ref,1.)
        assert_allclose(p,self.p-np.eye(22),rtol=0,atol=0)
        assert_allclose(p@(mu-self.ref),self.p@(self.mu-self.ref),rtol=0,atol=1e-11)

    def test_rejects_non_spd_removed_precision(self):
        with self.assertRaises(np.linalg.LinAlgError):
            transform(self.mu,.5*np.eye(22),self.ref,1.)

    def test_rejects_invalid_lambda_and_asymmetry(self):
        for lam in (-.1,1.1,float('nan')):
            with self.assertRaises(ValueError):
                transform(self.mu,self.p,self.ref,lam)
        p=self.p.copy(); p[0,1]+=.1
        with self.assertRaises(ValueError):
            transform(self.mu,p,self.ref,.5)


if __name__=='__main__':
    unittest.main()

import unittest
import numpy as np
from bass.observer.congruence_ssot import (
    CongruenceFirstJet, decompose_first_jet, compose_rapidity_vectors,
)

class CongruenceTests(unittest.TestCase):
    def test_minkowski_inertial(self):
        g = np.diag([-1.,1.,1.,1.])
        k = decompose_first_jet(CongruenceFirstJet(g, np.zeros((4,4,4)), np.array([1.,0,0,0]), np.zeros((4,4))))
        self.assertAlmostEqual(k.theta, 0.0, places=13)
        self.assertLess(np.linalg.norm(k.acceleration_cov), 1e-13)
        self.assertLess(np.linalg.norm(k.shear_cov), 1e-13)
        self.assertLess(np.linalg.norm(k.vorticity_cov), 1e-13)

    def test_flat_flrw_limit(self):
        a, H = 1.7, 0.23
        g = np.diag([-1.,a*a,a*a,a*a])
        dg = np.zeros((4,4,4)); dg[0,1,1]=dg[0,2,2]=dg[0,3,3]=2*a*a*H
        k = decompose_first_jet(CongruenceFirstJet(g,dg,np.array([1.,0,0,0]),np.zeros((4,4))))
        self.assertAlmostEqual(k.theta, 3*H, places=12)
        self.assertLess(np.linalg.norm(k.shear_cov), 1e-12)
        self.assertLess(np.linalg.norm(k.acceleration_cov), 1e-12)

    def test_noncollinear_boost_is_lorentz(self):
        out = compose_rapidity_vectors(np.array([0.2,0,0]), np.array([0,0.15,0]))
        self.assertLess(out['lorentz_error'], 1e-12)
        self.assertFalse(np.allclose(out['rapidity_vector'], np.array([0.2,0.15,0]), atol=1e-4))

    def test_incomplete_normalization_fails(self):
        g=np.diag([-1.,1.,1.,1.])
        with self.assertRaises(ValueError):
            decompose_first_jet(CongruenceFirstJet(g,np.zeros((4,4,4)),np.array([2.,0,0,0]),np.zeros((4,4))))

if __name__ == '__main__': unittest.main()

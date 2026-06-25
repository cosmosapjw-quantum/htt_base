import unittest
import numpy as np
from bass.background.bi_continuation import (
    SpeciesPrimitive, tilt_moments, realizability_margin,
    abstract_antipodal_pair_decomposition, BIState, integrate,
    constraint_residuals, dust_flrw_exact,
)

class BianchiTests(unittest.TestCase):
    def test_counterstream_codazzi(self):
        s=(SpeciesPrimitive(0.4,0.0,np.array([0.2,0,0])), SpeciesPrimitive(0.4,0.0,np.array([-0.2,0,0])))
        m=tilt_moments(s,H=1.0)
        self.assertLess(np.linalg.norm(m.J),1e-14)
        self.assertGreater(m.Omega_tilt,0)
        self.assertGreaterEqual(realizability_margin(m.K),-1e-14)

    def test_scalar_non_sufficiency(self):
        v=np.sqrt(0.04)
        pair=(SpeciesPrimitive(0.3,0,np.array([v,0,0])), SpeciesPrimitive(0.3,0,np.array([-v,0,0])))
        six=[]
        for e in np.eye(3):
            six += [SpeciesPrimitive(0.1,0,v*e), SpeciesPrimitive(0.1,0,-v*e)]
        m1=tilt_moments(pair,1.0); m2=tilt_moments(tuple(six),1.0)
        self.assertAlmostEqual(m1.Omega_tilt,m2.Omega_tilt,places=12)
        self.assertGreater(np.linalg.norm(m1.Pi),1e-4)
        self.assertLess(np.linalg.norm(m2.Pi),1e-13)

    def test_psd_pair_decomposition(self):
        K=np.diag([0.02,0.03,0.05])
        pairs=abstract_antipodal_pair_decomposition(K)
        rec=sum((p['weight']*np.outer(p['directions'][0],p['directions'][0]) for p in pairs),np.zeros((3,3)))
        self.assertTrue(np.allclose(rec,K))
        self.assertEqual(len(pairs),3)

    def test_dust_flrw_limit(self):
        H0=0.8; rho0=3*H0*H0
        state=BIState(1.0,H0,np.zeros((3,3)),(SpeciesPrimitive(rho0,0.0,np.zeros(3)),))
        t=np.linspace(0,0.4,401)
        hist=integrate(state,t)
        a_exact,H_exact=dust_flrw_exact(t,H0)
        self.assertLess(max(abs(s.a-a) for s,a in zip(hist,a_exact)),2e-9)
        self.assertLess(max(abs(s.H-h) for s,h in zip(hist,H_exact)),2e-9)
        self.assertLess(max(abs(constraint_residuals(s)['gauss']) for s in hist),2e-8)

    def test_pi_ablation_changes_shear(self):
        pair=(SpeciesPrimitive(0.6,0,np.array([0.18,0,0])), SpeciesPrimitive(0.6,0,np.array([-0.18,0,0])))
        p=tilt_moments(pair,1.0).total_projection
        sigma0=np.zeros((3,3))
        rho_mu=p.mu
        H=np.sqrt(rho_mu/3.0)
        state=BIState(1.0,H,sigma0,pair)
        t=np.linspace(0,0.08,81)
        full=integrate(state,t,include_anisotropic_stress=True)[-1]
        ablated=integrate(state,t,include_anisotropic_stress=False)[-1]
        self.assertGreater(np.linalg.norm(full.sigma-ablated.sigma),1e-5)

if __name__ == '__main__': unittest.main()

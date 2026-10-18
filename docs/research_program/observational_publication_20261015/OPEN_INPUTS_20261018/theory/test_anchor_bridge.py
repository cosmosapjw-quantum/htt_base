"""Independent falsifiers of finite anchor construction; no physical null claim."""
import unittest
import numpy as np
from anchor_bridge import design,directions,nullspace,quotient,target_radius,augment,method_bias_design,method_uncertainty_outer

class AnchorTests(unittest.TestCase):
    def test_six_source_gauge_witness(self):
        a=design(directions()); z=a[:,[0,4,5,6,7,8]]; d=a[:,1:4]
        w=-np.linalg.solve(z,d)
        for v in [np.array([1.,2.,3.]),np.array([-.04,.07,.02])]:
            np.testing.assert_allclose(z@(w@v)+d@v,0,atol=2e-14)
        self.assertLess(np.linalg.norm(quotient(d,z)),1e-13)
        self.assertTrue(np.isinf(target_radius(a,np.eye(9)[1])))

    def test_bounded_target_endpoint_attains_radius(self):
        a=design(directions()); extra,_,_=augment(a); a9=design(np.vstack([directions(),extra]))
        ell=np.eye(9)[1]; radius=.01
        # SVD formula independent of production least-squares target map.
        u,s,vh=np.linalg.svd(a9,full_matrices=False)
        gram_inv=(vh.T/s**2)@vh
        gain=np.sqrt(ell@gram_inv@ell)
        endpoint=radius*(gram_inv@ell)/gain
        self.assertAlmostEqual(np.linalg.norm(a9@endpoint),radius,places=12)
        self.assertAlmostEqual(ell@endpoint,target_radius(a9,ell,radius),places=12)

    def test_feasible_nonzero_residual_budget(self):
        a=np.array([[1.,0.],[0.,2.],[0.,0.]])
        b=np.array([2.,4.,.3]); radius=.5; center=np.linalg.lstsq(a,b,rcond=None)[0]
        width=np.sqrt(radius**2-.3**2)*target_radius(a,np.array([0.,1.]))
        self.assertAlmostEqual(width,.2)
        for sign in [-1,1]:
            p=center+np.array([0.,sign*width])
            self.assertAlmostEqual(np.linalg.norm(a@p-b),radius)

    def test_dipole_only_centered_schur_matches_full(self):
        n=directions(); w=np.arange(1.,7.); a=np.column_stack([np.ones(6),n])
        nc=n-np.average(n,axis=0,weights=w)
        full=np.linalg.inv(a.T@(w[:,None]*a))[1:,1:]
        fwl=np.linalg.inv(nc.T@(w[:,None]*nc))
        np.testing.assert_allclose(full,fwl,rtol=2e-13,atol=2e-13)

    def test_prospective_volume_identity(self):
        a=design(directions()); extra,_,volume=augment(a); k=nullspace(a)
        a9=np.vstack([a,design(extra)])
        lhs=np.linalg.det(a9)**2
        rhs=np.linalg.det(a@a.T)*np.linalg.det(design(extra)@k)**2
        self.assertAlmostEqual(lhs/rhs,1,places=11)
        self.assertAlmostEqual(abs(np.linalg.det(design(extra)@k)),volume,places=12)
        self.assertEqual(np.linalg.matrix_rank(a9),9)

    def test_rotation_keeps_rank_and_quotient(self):
        n=directions(); r=np.array([[0.,1.,0.],[-1.,0.,0.],[0.,0.,1.]])
        a=design(n@r.T); z=a[:,[0,4,5,6,7,8]]
        self.assertEqual(np.linalg.matrix_rank(a),6)
        self.assertEqual(np.linalg.matrix_rank(z),6)
        self.assertLess(np.linalg.norm(quotient(a[:,1:4],z)),1e-13)

    def test_duplicate_and_equatorial_counterexamples(self):
        a=design(np.repeat([[1.,0.,0.]],9,axis=0))
        self.assertEqual(np.linalg.matrix_rank(a),1)
        phi=np.linspace(0,2*np.pi,12,endpoint=False)
        equator=design(np.column_stack([np.cos(phi),np.sin(phi),0*phi]))
        self.assertEqual(np.linalg.matrix_rank(equator),5)
        self.assertTrue(np.isinf(target_radius(equator,np.eye(9)[3])))

    def test_stf_basis_normalization(self):
        q=np.array([.1,-.2,.3,-.4,.5]); n=directions()
        tensor=np.array([[q[0],q[2],q[3]],[q[2],q[1],q[4]],[q[3],q[4],-q[0]-q[1]]])
        np.testing.assert_allclose(design(n)[:,4:]@q,np.einsum('ni,ij,nj->n',n,tensor,n),atol=1e-15)
        self.assertEqual(np.trace(tensor),0.)

    def test_antipodal_six_rows_identify_dipole_with_free_even_nuisance(self):
        axes=np.array([[1.,0.,0.],[1.,1.,0.],[1.,1.,1.]])
        axes/=np.linalg.norm(axes,axis=1)[:,None]
        n=np.vstack([axes,-axes]); a=design(n); z=a[:,[0,4,5,6,7,8]]
        self.assertEqual(np.linalg.matrix_rank(a)-np.linalg.matrix_rank(z),3)
        p=np.array([2.,.03,-.04,.07,.2,-.1,.5,-.3,.4])
        y=a@p
        recovered=np.linalg.solve(axes,(y[:3]-y[3:])/2)
        np.testing.assert_allclose(recovered,p[1:4],atol=1e-15)
        self.assertTrue(np.isfinite(target_radius(a,np.eye(9)[1])))
        self.assertEqual(np.linalg.matrix_rank(a),6) # all9coefficients remain unidentified

    def test_single_method_calibration_floor_and_explicit_alias(self):
        a=design(directions()); extra,_,_=augment(a)
        n=np.vstack([directions(),extra]); a=design(n)
        g=method_bias_design(n,['m']*9); ell=np.eye(9)[1]; delta=.02
        self.assertAlmostEqual(method_uncertainty_outer(a,ell,g,delta),delta,places=12)
        p=np.zeros(9); p[1]=delta; gamma=np.zeros(8); gamma[0]=-delta
        np.testing.assert_allclose(a@p+g@gamma,0,atol=1e-15)

    def test_raw_anchor_false_positive_and_known_gamma_correction(self):
        s_x=.010; eta=.015; gamma=-.015; delta=.020
        self.assertLessEqual(abs(gamma),delta)
        raw_anchor=eta+gamma
        self.assertEqual(raw_anchor,0.)
        naive_theta=s_x-raw_anchor
        corrected_eta=raw_anchor-gamma
        correct_theta=s_x-corrected_eta
        self.assertGreater(naive_theta,0.)
        self.assertAlmostEqual(correct_theta,-.005)
        self.assertAlmostEqual(corrected_eta,eta)

    def test_uncertain_method_outer_bound_attained_without_residual_restriction(self):
        a=design(directions()); extra,_,_=augment(a)
        n=np.vstack([directions(),extra]); a=design(n)
        g=method_bias_design(n,['m1']*4+['m2']*5)
        ell=np.eye(9)[1]; delta=np.linspace(.001,.016,16); radius=.003
        w=np.linalg.solve(a.T,ell)
        gamma=delta*np.sign(g.T@w); noise=radius*w/np.linalg.norm(w)
        p_hat=np.linalg.solve(a,g@gamma+noise)
        bound=method_uncertainty_outer(a,ell,g,delta,radius)
        self.assertAlmostEqual(ell@p_hat,bound,places=12)

if __name__=='__main__': unittest.main(verbosity=2)

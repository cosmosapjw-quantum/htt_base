import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.linalg import eigh
from scipy.optimize import linprog

sys.path.insert(0,str(Path(__file__).resolve().parent))
import calibration_obstruction as c


class CalibrationObstructionTests(unittest.TestCase):
    def test_original_measure_and_missing_physics(self):
        _, draws, weights, ids, physical = c.load_existing()
        self.assertEqual(draws.shape,(2048,4,9))
        self.assertEqual(len(set(ids)),2048)
        self.assertEqual(weights.sum(),1.)
        self.assertTrue(np.array_equal(weights,np.full(2048,1/2048)))
        self.assertTrue(all(np.isnan(v).all() for v in physical.values()))
        self.assertTrue(np.any(draws[:,:,4:9]<0))

    def test_source_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'bad.json'; p.write_text('{}')
            with self.assertRaisesRegex(ValueError,'identity mismatch'):
                c.checked_read(p,c.SOURCE_SHA)

    def test_isotropic_and_analytic_axisymmetric(self):
        rho,h = c.erasure_radius(np.eye(3)*70)
        self.assertEqual(rho,0.);self.assertEqual(h,70.)
        rho,h = c.erasure_radius(np.diag([68.,68.,74.]))
        self.assertAlmostEqual(rho,2.5*np.log10(74/68),14)
        self.assertAlmostEqual(h,np.sqrt(68*74),12)

    def test_erasure_witness_and_smaller_radius_impossible(self):
        m=np.array([[72.,1.,-2.],[1.,68.,.5],[-2.,.5,70.]])
        rho,h=c.erasure_radius(m)
        e,v=np.linalg.eigh(m)
        # Exact eigenvectors attain both ends; all other directions are between.
        delta=5*np.log10(e/h)
        self.assertAlmostEqual(delta[0],-rho,13)
        self.assertAlmostEqual(delta[-1],rho,13)
        self.assertGreater(5*np.log10(e[-1]/e[0]),2*(rho-1e-5))
        n=np.random.default_rng(8).normal(size=(300,3)); n/=np.linalg.norm(n,axis=1)[:,None]
        h_app=np.einsum('ni,ij,nj->n',n,m,n)
        correction=5*np.log10(h_app/h)
        self.assertTrue(np.max(np.abs(correction))<=rho+1e-13)
        np.testing.assert_allclose(h_app*10**(-correction/5),h,rtol=2e-15)

    def test_orthogonal_rotation_and_scale(self):
        rng=np.random.default_rng(64); a=rng.normal(size=(4,3,3))
        m=a@a.swapaxes(-1,-2)+np.eye(3)*4
        o=np.linalg.qr(rng.normal(size=(3,3)))[0]
        rotated=o@m@o.T
        np.testing.assert_allclose(c.erasure_radius(rotated)[0],c.erasure_radius(m)[0],atol=2e-14,rtol=0)
        scales=np.array([2.,.5,3.,.1])
        original=c.common_calibration_radius(c.directed_contrast(m))[0]
        transformed=c.common_calibration_radius(c.directed_contrast(rotated*scales[:,None,None]))[0]
        self.assertAlmostEqual(original,transformed,13)

    def test_generalized_eigen_extrema_have_witness_directions(self):
        rng=np.random.default_rng(9);a=rng.normal(size=(4,3,3));m=a@a.swapaxes(-1,-2)+np.eye(3)*5
        d=c.directed_contrast(m)
        for i,j in c.PAIRS:
            ev,vec=eigh(m[i],m[j]); n=vec[:,-1]/np.linalg.norm(vec[:,-1])
            ratio=n@m[i]@n/(n@m[j]@n)
            self.assertAlmostEqual(5*np.log10(ratio),d[i,j],13)
            self.assertAlmostEqual(5*np.log10(ev[0]),-d[j,i],13)

    def test_common_shape_is_erased_by_shared_calibration(self):
        shape=np.diag([.9,1.,1.1]);m=np.array([shape*s for s in [65.,70.,75.,80.]])
        self.assertTrue((c.erasure_radius(m)[0]>.1).all())
        eta,_,_,_,_=c.common_calibration_radius(c.directed_contrast(m))
        self.assertLess(abs(eta),1e-14)

    def test_cycle_minimax_matches_independent_linear_program(self):
        rng=np.random.default_rng(410)
        # LP includes no self-loop rows and fixes c0=0; cycle solver does neither.
        _,draws,*_=c.load_existing()
        matrices=list(c.even_matrices(draws[rng.choice(2048,20,replace=False)]))
        for _ in range(20):
            a=rng.normal(size=(4,3,3));matrices.append(a@a.swapaxes(-1,-2)+np.eye(3)*3)
        for m in matrices:
            d=c.directed_contrast(m);eta,lower,pot,_,violation=c.common_calibration_radius(d)
            rows=[];b=[]
            for j in range(4):
                for k in range(4):
                    if j==k:continue
                    row=np.zeros(5);row[j]=-1;row[k]=1;row[4]=-2
                    rows.append(row);b.append(-d[j,k])
            lp=linprog([0,0,0,0,1],A_ub=rows,b_ub=b,bounds=[(0,0),(None,None),(None,None),(None,None),(0,None)],method='highs')
            self.assertTrue(lp.success)
            self.assertAlmostEqual(eta,lp.fun,10)
            self.assertGreaterEqual(eta+2e-13,lower)
            self.assertLessEqual(violation,2e-12)
            # Construct common angular g pointwise and check all four residuals.
            n=rng.normal(size=(500,3));n/=np.linalg.norm(n,axis=1)[:,None]
            E=5*np.log10(np.einsum('ni,wij,nj->wn',n,m,n))-pot[:,None]
            g=(E.max(axis=0)+E.min(axis=0))/2
            self.assertLessEqual(np.max(np.abs(E-g)),eta+1e-12)

    def test_strict_tail_ties_and_weight_rejection(self):
        result=c.finite_tail([.01,.02,.03],[.25,.5,.25],[.02])
        self.assertEqual(result,[{'threshold_mag':.02,'strict_mass':.25,'tie_mass':.5}])
        with self.assertRaises(ValueError):c.finite_tail([1.,2.],[.25,.25],[1.])

    def test_invalid_domains_fail_closed(self):
        for m in [np.diag([0.,1.,2.]),np.diag([-1.,1.,2.]),np.full((3,3),np.nan)]:
            with self.assertRaises(ValueError):c.erasure_radius(m)
        with self.assertRaises(ValueError):c.even_matrices(np.zeros((4,9)))
        with self.assertRaises(ValueError):c.erasure_radius(np.array([[1.,1.,0.],[0.,1.,0.],[0.,0.,1.]]))

    def test_signed_vorticity_blind_witness(self):
        s=np.diag([2.,-1.,-1.]);o=np.array([[0.,3.,0.],[-3.,0.,0.],[0.,0.,0.]])
        rng=np.random.default_rng(88);n=rng.normal(size=(100,3))
        np.testing.assert_allclose(np.einsum('ni,ij,nj->n',n,o,n),0.,atol=1e-14)
        self.assertGreater(c.signed_kinematic_comparator(s,70.,np.zeros((3,3))),0)
        self.assertLess(c.signed_kinematic_comparator(s,70.,o),0)
        np.testing.assert_allclose(np.einsum('ni,ij,nj->n',n,s+o,n),np.einsum('ni,ij,nj->n',n,s,n),atol=2e-14)

    def test_generated_arrays_preserve_source_and_all_joint_witnesses(self):
        _,draws,weights,ids,physical=c.load_existing()
        with np.load(c.ROOT/'results/calibration_obstruction_arrays.npz',allow_pickle=False) as result:
            np.testing.assert_array_equal(result['sample_id'],ids)
            np.testing.assert_array_equal(result['weights'],weights)
            np.testing.assert_array_equal(result['original_joint_draws'],draws)
            np.testing.assert_array_equal(result['original_q_app'],np.linalg.norm(draws[:,:,4:9],axis=2)/draws[:,:,0])
            for name in physical:np.testing.assert_array_equal(result[name],physical[name])
            D=result['directed_contrast_mag'];eta=result['common_residual_radius_mag'];pot=result['window_constant_witness_mag']
            residual=D-(pot[:,:,None]-pot[:,None,:])-2*eta[:,None,None]
            self.assertLessEqual(float(np.max(residual)),2e-12)
            r=json.loads((c.ROOT/'results/S02_CALIBRATION_OBSTRUCTION.json').read_text())
            self.assertEqual(r['physical_unknown_mass'],dict.fromkeys(['x_C','Q','F','G_F'],1.))
            self.assertEqual(r['runtime_identity']['review'],'PENDING_PARENT_INDEPENDENT_REVIEW')


if __name__=='__main__': unittest.main(verbosity=2)

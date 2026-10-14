"""Portable falsifiers: run python -m unittest discover -s PATH -p 'test_*.py'."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import numpy as np

SCRIPT=Path(__file__).resolve().parents[2]/'scripts/run_solver_free_gaia_geometry.py'
spec=importlib.util.spec_from_file_location('gaia_geometry',SCRIPT)
g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.rng=np.random.default_rng(64021)
        self.m=self.rng.normal(size=(6,7,2))
        self.k=self.rng.normal(size=(6,14))
        self.v=self.k@self.k.T
        self.ids=np.arange(7,dtype=np.int64)

    def test_disk_attaining_witness_and_zero_blocks(self):
        m=self.m.copy();m[:,2,:]=0
        u=self.rng.normal(size=6);bbar=.01
        b=g.disk_witness(m,u,bbar)
        self.assertTrue(np.all(np.linalg.norm(b,axis=1)<=bbar+1e-16))
        self.assertTrue(np.array_equal(b[2],np.zeros(2)))
        scalar=sum(float(u@m[:,i,:]@b[i]) for i in range(7))
        expected=bbar*sum(float(np.linalg.norm(m[:,i,:].T@u)) for i in range(7))
        self.assertAlmostEqual(scalar,expected,places=14)
        self.assertAlmostEqual(g.disk_support(m,u,bbar)[0],scalar,places=14)
        # Sampled feasible points can never exceed the analytical support.
        for _ in range(200):
            points=self.rng.normal(size=(7,2));points/=np.linalg.norm(points,axis=1)[:,None]
            points*=self.rng.uniform(0,bbar,size=(7,1))
            self.assertLessEqual(sum(float(u@m[:,i,:]@points[i]) for i in range(7)),expected+1e-13)

    def test_disk_invariant_under_rotations_and_box_is_different(self):
        u=self.rng.normal(size=(20,6))
        check=g.rotation_checks(self.m,u,.01,self.rng)
        self.assertLess(check['support_max_abs_mas_year'],1e-13)
        self.assertLess(check['witness_shift_max_abs_mas_year'],1e-13)
        self.assertGreater(check['box_changed_max_abs_microas_year'],.01)
        disk=g.disk_support(self.m,u,.01);box=g.box_support(self.m,u,.01)
        self.assertTrue(np.all(disk<=box+1e-13))
        self.assertTrue(np.all(box<=np.sqrt(2)*disk+1e-13))

    def test_exact_ellipsoid_image_and_kernel_minimum_norm(self):
        l=np.linalg.cholesky(self.v)
        for _ in range(30):
            w=self.rng.normal(size=6);delta=l@w
            z=g.ellipsoid_witness(self.k,self.v,delta)
            np.testing.assert_allclose(self.k@z,delta,rtol=1e-12,atol=1e-12)
            self.assertAlmostEqual(np.linalg.norm(z),np.linalg.norm(w),places=12)
            # Adding a kernel component cannot lower the norm of this preimage.
            a=self.rng.normal(size=14)
            null=a-self.k.T@np.linalg.solve(self.v,self.k@a)
            self.assertGreaterEqual(np.linalg.norm(z+null),np.linalg.norm(z)-1e-12)

    def test_simultaneous_minkowski_geometry_and_sharp_radius(self):
        q=np.sqrt(g.chi2_6_quantile(.95));rho=2.
        self.assertAlmostEqual(q*q,12.591587243743977,places=11)
        self.assertAlmostEqual(g.chi2_6_cdf(q*q),.95,places=14)
        noise=self.rng.normal(size=(1000,6));noise/=np.linalg.norm(noise,axis=1)[:,None]
        bias=self.rng.normal(size=(1000,6));bias/=np.linalg.norm(bias,axis=1)[:,None]
        self.assertTrue(np.all(np.linalg.norm(q*noise+rho*bias,axis=1)<=q+rho+1e-13))
        # Aligned boundary vectors attain q+rho, so no smaller universal ball
        # can contain the Minkowski sum.
        aligned=np.array([1.,0,0,0,0,0])
        self.assertAlmostEqual(np.linalg.norm(q*aligned+rho*aligned),q+rho,places=14)
        for norm in [0.,1.,q+rho]:
            total=norm*aligned
            self.assertLessEqual(np.linalg.norm(q/(q+rho)*total),q+1e-13)
            self.assertLessEqual(np.linalg.norm(rho/(q+rho)*total),rho+1e-13)

    def test_covariance_and_shape_fail_closed(self):
        g.validate_operator(self.m,self.k,self.v,self.ids)
        bad=self.v.copy();bad[0,0]=-1
        for m,k,v,ids in [(self.m,self.k,bad,self.ids),(self.m[:5],self.k,self.v,self.ids),
                          (self.m,self.k,self.v,np.zeros(7,dtype=int)),
                          (self.m,self.k[:,:-1],self.v,self.ids),
                          (self.m,self.k,self.v*2,self.ids)]:
            with self.assertRaises(ValueError):g.validate_operator(m,k,v,ids)
        badm=self.m.copy();badm[0,0,0]=np.nan
        with self.assertRaises(ValueError):g.validate_operator(badm,self.k,self.v,self.ids)
        with self.assertRaises(ValueError):g.disk_support(self.m,np.eye(6),-.1)
        with self.assertRaises(ValueError):g.disk_support(self.m,np.eye(6),float('nan'))

    def test_fixed_law_mc_is_sanity_check_with_known_bias(self):
        q=np.sqrt(g.chi2_6_quantile(.95))
        rows=g.coverage_stress(20000,2811,q,[0.,1.,2.,4.])['rows']
        se=np.sqrt(.95*.05/20000)
        self.assertLess(abs(rows[0]['expanded_q_plus_rho_region_coverage']-.95),5*se)
        for row in rows:
            self.assertGreaterEqual(row['expanded_q_plus_rho_region_coverage'],.95-5*se)
        self.assertLess(rows[-1]['unexpanded_q_region_coverage'],.3)
        with self.assertRaises(ValueError):g.coverage_stress(50001,1,q,[1.])

    def test_portable_input_identity_and_no_repository_import(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);ip=p/'operator.npz';bp=p/'baseline.json'
            np.savez(ip,M=self.m,K=self.k,covariance=self.v,source_id=self.ids)
            bp.write_text(json.dumps({'coefficient_order':g.NAMES,'coefficients_mas_year':[0.]*6,
                'units':'coefficients/supports mas/year internally; displayed widths microas/year',
                'sampling_covariance_mas2_year2':self.v.tolist(),
                'source':{'source_release':'synthetic','source_rows_csv_sha256':'synthetic'}}))
            args=g.parser().parse_args(['--input',str(ip),'--baseline',str(bp),'--output',str(p/'result'),
                '--expected-input-sha',g.sha256(ip),'--expected-baseline-sha',g.sha256(bp),'--no-plots','--mc-reps','0'])
            result=g.run(args)
            self.assertTrue((p/'result/result.json').exists())
            self.assertTrue(all(result['simultaneous_gaussian']['zero_contained_at_each_rho']))
            args.output=p/'bad';args.expected_input_sha='0'*64
            with self.assertRaises(ValueError):g.run(args)
            self.assertFalse(args.output.exists())


if __name__=='__main__':unittest.main()

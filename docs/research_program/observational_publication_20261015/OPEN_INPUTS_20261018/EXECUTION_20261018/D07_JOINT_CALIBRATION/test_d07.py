import unittest
import numpy as np
from d07 import shape8,rank_info,quotient,symmetric_whitener,layout,build_angular_design,targets,valid_host_coordinates,METHODS,HERE,D03,Campaign,source


class TestD07(unittest.TestCase):
    def test_reviewed_D03_candidate_files_unchanged(self):
        import json
        manifest=json.loads((D03/'CANDIDATE.json').read_text())
        self.assertEqual(manifest['candidate_digest_sha256'],'c326fc79b4cfd255d4655cb47b27a4b399403179c3342ac30ae7113c80dcc388')
        for name,info in manifest['files'].items():
            self.assertEqual(source.sha(D03/name),info['sha256'])

    def test_actual_source_row_binding_and_no_imputation(self):
        with np.load(HERE/'D07_DESIGN_WITNESSES.npz',allow_pickle=False) as f:
            self.assertEqual(len(f['a_row_index']),559);self.assertEqual(len(f['c_all77_row_index']),77);self.assertEqual(len(f['c_supported_row_index']),75)
            self.assertEqual(len(f['calibrator_named_host_labels']),37)
            np.testing.assert_array_equal(f['calibrator_named_host_incidence'].sum(axis=1),np.ones(75))
            p=np.genfromtxt(source.PANTHEON/'Pantheon_SH0ES.dat',names=True,dtype=None,encoding='utf8')
            raw=np.loadtxt(source.PANTHEON/'Pantheon_SH0ES_STAT_SYS.cov');C=raw[1:].reshape(1701,1701);C=(C+C.T)/2
            ai=f['a_row_index'];ci=f['c_supported_row_index']
            np.testing.assert_array_equal(f['Pantheon_a_subblock'],C[np.ix_(ai,ai)])
            np.testing.assert_array_equal(f['Pantheon_c_subblock'],C[np.ix_(ci,ci)])
            np.testing.assert_allclose(f['a_mag'],f['pooled_DMzp_mag']-p['MU_SH0ES'][ai],rtol=0,atol=0)
            np.testing.assert_allclose(f['c_supported_mag'],p['MU_SH0ES'][ci]-p['CEPH_DIST'][ci],rtol=0,atol=0)
            excluded=set(map(int,f['c_all77_row_index']))-set(map(int,ci))
            self.assertEqual({str(p['CID'][i]) for i in excluded},{'2005df_ANU','2008fv_comb'})
            np.testing.assert_allclose(f['Xg'],shape8(f['group_direction']),rtol=0,atol=0)
            np.testing.assert_allclose(f['Xh'],shape8(f['calibrator_host_direction']),rtol=0,atol=0)

    def test_all97_actual_endpoint_witnesses_independently(self):
        import time,json
        with np.load(HERE/'D07_DESIGN_WITNESSES.npz',allow_pickle=False) as f:d={k:f[k].copy() for k in f.files}
        sl,size=layout(d['Za'].shape[1],d['Zc'].shape[1]);campaign=Campaign(d,sl,time.monotonic())
        self.assertEqual(d['LP_endpoint_witnesses'].shape,(97,size))
        for witness in d['LP_endpoint_witnesses']:campaign.verify(witness,float(witness[sl['t']]))
        self.assertEqual(campaign.calls,0)
        r=json.loads((HERE/'LP_RAW.json').read_text());self.assertEqual(r['calls_started'],97)
        self.assertTrue(all(x['state']=='FINITE' for x in r['runs']))

    def test_actual_gauge_and_targets_remain_invariant(self):
        with np.load(HERE/'D07_DESIGN_WITNESSES.npz',allow_pickle=False) as f:
            for label in ['H02_design','pair_design','calibrator_design','target_zeta','target_psi','target_chi']:
                np.testing.assert_allclose(f[label]@f['gauge_witnesses'],0,atol=1e-12)

    def test_original_raw_equatorial_basis(self):
        np.testing.assert_array_equal(shape8(np.eye(3)),[[1,0,0,1,0,0,0,0],[0,1,0,0,1,0,0,0],[0,0,1,-1,-1,0,0,0]])

    def test_invalid_host_is_unknown_not_substituted(self):
        base={'has_host':'1','host':'N1','RA_host':'20','Dec_host':'30'}
        self.assertTrue(valid_host_coordinates(base))
        for value in ['','nan','-999','360']:
            self.assertFalse(valid_host_coordinates({**base,'RA_host':value}))

    def test_redundant_nuisance_explicit_nullspace(self):
        N=np.column_stack([np.ones(12),np.arange(12)<6,np.arange(12)>=6])
        info,_,null=rank_info(N)
        self.assertEqual(info['rank'],2);self.assertEqual(info['ranks_0p1_1_10'],[2,2,2])
        np.testing.assert_allclose(N@null,0,atol=1e-14)

    def test_principal_whitener_permutation_infinity_norm(self):
        rng=np.random.default_rng(3);A=rng.normal(size=(9,9));C=A@A.T+np.eye(9);r=rng.normal(size=9);p=np.array([8,1,5,3,2,4,6,7,0])
        W,_=symmetric_whitener(C);Wp,_=symmetric_whitener(C[np.ix_(p,p)])
        np.testing.assert_allclose(Wp@r[p],(W@r)[p],atol=1e-13)
        self.assertAlmostEqual(np.max(np.abs(Wp@r[p])),np.max(np.abs(W@r)),12)

    def test_gauge_predictions_and_invariants_cancel(self):
        rng=np.random.default_rng(8);n=rng.normal(size=(28,3));n/=np.linalg.norm(n,axis=1)[:,None]
        X=shape8(n);N=np.ones((28,1));f=np.array(METHODS*7)
        H,Da,Dc,G,sl=build_angular_design(X,X,f,N,N)
        for A in [H,Da,Dc]:np.testing.assert_allclose(A@G,0,atol=1e-14)
        for R in targets(sl,H.shape[1]):np.testing.assert_allclose(R@G,0,atol=1e-14)
        self.assertEqual(G.shape[1],8)

    def test_shared_gamma_not_per_window(self):
        X=shape8(np.eye(3));N=np.ones((3,1));H,Da,Dc,G,sl=build_angular_design(X,X,np.array(['FP','TF','SN']),N,N)
        self.assertEqual(sl['gamma'].stop-sl['gamma'].start,32)
        np.testing.assert_array_equal(H[0,sl['gamma']],H[32,sl['gamma']])

    def test_quotient_removes_only_scalar_offsets(self):
        rng=np.random.default_rng(10);A=rng.normal(size=(15,8));N=np.column_stack([np.ones(15),np.ones(15)])
        projected,info=quotient(A,N)
        np.testing.assert_allclose(projected.mean(axis=0),0,atol=1e-14)
        self.assertEqual(info['rank'],1)


if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from d03 import schema, aliases, choose_metadata, direction, covariance_family, gls, sealed


class TestD03(unittest.TestCase):
    def test_actual_full_matrix_order_graph_and_selected_subblocks(self):
        from d03 import HERE,PANTHEON
        import csv
        rows=np.genfromtxt(PANTHEON/'Pantheon_SH0ES.dat',names=True,dtype=None,encoding='utf-8')
        raw=np.loadtxt(PANTHEON/'Pantheon_SH0ES_STAT_SYS.cov')
        n=int(raw[0]);C=raw[1:].reshape(n,n);S=(C+C.T)/2
        with (HERE/'results/OBJECT_GRAPH.csv').open() as stream:
            graph=list(csv.DictReader(stream))
        self.assertEqual(len(graph),n)
        self.assertEqual([int(g['row_index']) for g in graph],list(range(n)))
        self.assertEqual([g['CID_literal'] for g in graph],list(rows['CID']))
        self.assertEqual(n,1701);self.assertEqual(len(set(rows['CID'])),1543)
        self.assertGreater(np.max(np.abs(C-C.T)),1e-10)
        for mode in ['host_SN','group_SN','group_TF_else_SN']:
            with np.load(HERE/'results'/(mode+'.npz'),allow_pickle=False) as f:
                idx=f['row_index']
                np.testing.assert_array_equal(f['P_full_covariance_subblock'],S[np.ix_(idx,idx)])
                self.assertEqual(len(idx),len(set(idx)))
                np.testing.assert_array_equal(f['B_CF4_incidence'].sum(axis=1),np.ones(len(idx)))
                self.assertTrue(np.all(f['CF4_sigma']>0))

    def test_source_schema_exact_ranges(self):
        s=schema('Byte-by-byte Description of file: t.dat\n 1- 7 I7 --- PGC ID\n 9 F1.0 mag DM value\nNote (1): text','t.dat')
        self.assertEqual(s,{'PGC':(0,7,'I'),'DM':(8,9,'F')})

    def test_alias_keeps_leading_zero_and_literal_ids(self):
        records=[dict(SNID='00012',IAUC='2000ab',RA='12',Dec='3',host='N1',RA_host='12',Dec_host='3')]
        a=aliases(records)
        self.assertIn('00012',a);self.assertNotIn('12',a)
        r,status=choose_metadata('2000ab',direction(12,3),a)
        self.assertEqual(status,'alias_and_sky');self.assertEqual(r['SNID'],'00012')

    def test_alias_wrong_sky_fails_closed(self):
        r=dict(SNID='abc',IAUC='',RA='12',Dec='3',host='N1',RA_host='12',Dec_host='3')
        self.assertEqual(choose_metadata('abc',direction(13,3),aliases([r]))[1],'alias_sky_disagreement')

    def test_ambiguous_alias_host_retained(self):
        a=dict(SNID='a',IAUC='x',RA='12',Dec='3',host='N1',RA_host='12',Dec_host='3')
        b={**a,'SNID':'b','host':'N2'}
        self.assertEqual(choose_metadata('x',direction(12,3),aliases([a,b]))[1],'ambiguous_alias_host')

    def test_psd_family_against_explicit_joint(self):
        P=np.array([[1,.2,.1],[.2,2,.3],[.1,.3,1.]])
        B=np.array([[1,0],[1,0],[0,1.]])
        sigma=np.array([.3,.4]);Lp=np.linalg.cholesky(P);U=B/np.linalg.norm(B,2)
        for rho in [-1,-.75,0,.75,1]:
            V,info=covariance_family(P,B,sigma,rho)
            X=rho*(Lp@U)*sigma
            J=np.block([[P,X],[X.T,np.diag(sigma**2)]])
            D=np.column_stack([np.eye(3),-B])
            np.testing.assert_allclose(V,D@J@D.T,atol=1e-14)
            self.assertGreaterEqual(np.linalg.eigvalsh(J).min(),-1e-12)
            self.assertLessEqual(info['U_spectral_norm'],1+1e-12)

    def test_rho_outside_psd_design_rejected(self):
        with self.assertRaises(ValueError):covariance_family(np.eye(2),np.eye(2),np.ones(2),1.01)

    def test_repeated_source_error_is_shared(self):
        B=np.array([[1.],[1.]])
        V,_=covariance_family(np.eye(2),B,np.array([.5]),0)
        np.testing.assert_allclose(V,[[1.25,.25],[.25,1.25]])

    def test_rank_deficient_nuisance_quotient(self):
        z=np.arange(8.);N=np.column_stack([np.ones(8),z<4,z>=4,np.ones(8)])
        T=np.sin(z)[:,None];y=2*T[:,0]+N@np.array([.1,.2,.4,.1])
        fit,res=gls(y,np.eye(8),N,T)
        self.assertEqual(fit['nuisance_rank'],2)
        self.assertEqual(len(fit['nuisance_nullspace_basis']),2)
        np.testing.assert_allclose(fit['beta_direction_depth'],[2],atol=1e-12)
        np.testing.assert_allclose(res,0,atol=1e-12)

    def test_covariance_subblock_order_and_permutation(self):
        rng=np.random.default_rng(10);A=rng.normal(size=(12,12));C=A@A.T+np.eye(12)
        idx=np.array([9,0,7,2,5,3]);P=C[np.ix_(idx,idx)]
        self.assertEqual(P[0,1],C[9,0]);N=np.ones((6,1));T=np.arange(6.)[:,None];y=rng.normal(size=6)
        a,_=gls(y,P,N,T);perm=np.array([4,0,2,1,5,3]);b,_=gls(y[perm],P[np.ix_(perm,perm)],N[perm],T[perm])
        np.testing.assert_allclose(a['beta_direction_depth'],b['beta_direction_depth'],atol=1e-12)

    def test_hash_change_class1_rejected(self):
        from pathlib import Path
        with self.assertRaisesRegex(ValueError,'immutable source mismatch'):sealed(Path(__file__),'0'*64)


if __name__=='__main__':unittest.main()

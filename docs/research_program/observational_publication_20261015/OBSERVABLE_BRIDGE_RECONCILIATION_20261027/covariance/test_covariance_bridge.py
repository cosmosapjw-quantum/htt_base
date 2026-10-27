import numpy as np
import unittest
from covariance_bridge import gls_svd,transport_covariance


def _check_transport_matches_dense_and_cross_window():
    rng=np.random.default_rng(2701); A=rng.normal(size=(12,97));D=rng.uniform(.1,2,97)
    V=rng.normal(size=(97,4));K=rng.normal(size=(12,3));R=rng.normal(size=(3,3));S=R@R.T
    own={'independent':['measurement_noise'],'correlated':['correlated_PV'],'calibration':['method_zero_points']}
    expected=A@(np.diag(D)+V@V.T)@A.T+K@S@K.T
    for block in [1,13,4096]:
        got=transport_covariance(A,D,V,K,S,ownership=own,block_size=block)
        np.testing.assert_allclose(got['total'],expected,rtol=3e-13,atol=2e-12)
        np.testing.assert_allclose(got['total'][:3,3:6],expected[:3,3:6],rtol=3e-13,atol=2e-12)
        assert np.linalg.norm(got['total'][:3,3:6])>1
        assert np.linalg.eigvalsh(got['total']).min()>0


def _check_low_rank_and_exact_zero():
    rng=np.random.default_rng(2702);A=rng.normal(size=(9,51));V=rng.normal(size=(51,2))
    r=transport_covariance(A,np.zeros(51),V,ownership={'independent':['exact_zero'],'correlated':['rank_two']})
    assert np.linalg.matrix_rank(r['total'])==2
    assert np.linalg.eigvalsh(r['total']).min()>-1e-10
    z=transport_covariance(A,np.zeros(51),ownership={'independent':['exact_zero']})
    np.testing.assert_array_equal(z['total'],np.zeros((9,9)))


def _check_invalid_uncertainty_contract(case):
    A=np.eye(3);D=np.ones(3);V=np.ones((3,1));K=None;S=None;block=4096
    own={'independent':['measurement'],'correlated':['PV']}
    if case=='negative':D[0]=-1
    if case=='duplicate':own['correlated']=['measurement']
    if case=='missing_owner':own.pop('correlated')
    if case=='nonsymmetric':K=np.eye(3);S=np.eye(3);S[0,1]=.1;own['calibration']=['cal']
    if case=='negative_sigma':K=np.eye(3);S=np.diag([1.,1.,-1.]);own['calibration']=['cal']
    if case=='nan':V[0,0]=np.nan
    if case=='bad_block':block=0
    with unittest.TestCase().assertRaises(ValueError):transport_covariance(A,D,V,K,S,ownership=own,block_size=block)


def _check_gls_unit_rescaling_and_reference():
    rng=np.random.default_rng(2703);X=rng.normal(size=(15,4));r=rng.normal(size=(15,15));C=r@r.T+np.eye(15)
    y=rng.normal(size=15);got=gls_svd(y,X,C)
    expected=np.linalg.solve(X.T@np.linalg.solve(C,X),X.T@np.linalg.solve(C,y))
    np.testing.assert_allclose(got['beta'],expected,rtol=1e-12,atol=1e-12)
    factors=np.array([1e-6,1e3,7,1e7]);rescaled=gls_svd(y,X*factors,C)
    np.testing.assert_allclose(got['fitted_mean'],rescaled['fitted_mean'],rtol=1e-12,atol=1e-12)
    np.testing.assert_allclose(got['beta'],rescaled['beta']*factors,rtol=1e-12,atol=1e-12)
    assert np.isclose(got['scaled_condition'],rescaled['scaled_condition'],rtol=1e-12)


def _check_gls_rank_deficiency_and_zero_column():
    x=np.arange(8.)[:,None];X=np.column_stack([x,x,np.zeros_like(x)]);y=np.arange(8.)**2
    r=gls_svd(y,X,np.eye(8))
    assert r['rank']==1 and r['residual_dof']==7 and not r['parameters_identified']
    assert r['beta'] is None and r['beta_covariance'] is None
    np.testing.assert_allclose(X.T@(y-r['fitted_mean']),0,atol=1e-10)


def _check_gls_covariance_scale():
    X=np.column_stack([np.ones(9),np.arange(9)]);y=np.arange(9)**2
    a=gls_svd(y,X,np.eye(9));b=gls_svd(y,X,3*np.eye(9))
    assert np.isclose(a['statistic']/3,b['statistic'])
    np.testing.assert_allclose(a['beta'],b['beta'],atol=1e-12)


def _check_gls_rejects_invalid_covariance(C):
    with unittest.TestCase().assertRaises(ValueError):gls_svd(np.ones(3),np.ones((3,1)),C)


class BridgeTests(unittest.TestCase):
    def test_dense(self):_check_transport_matches_dense_and_cross_window()
    def test_rank(self):_check_low_rank_and_exact_zero()
    def test_invalid_uncertainty(self):
        for case in ['negative','duplicate','missing_owner','nonsymmetric','negative_sigma','nan','bad_block']:
            with self.subTest(case=case):_check_invalid_uncertainty_contract(case)
    def test_rescaling(self):_check_gls_unit_rescaling_and_reference()
    def test_gls_rank(self):_check_gls_rank_deficiency_and_zero_column()
    def test_cov_scale(self):_check_gls_covariance_scale()
    def test_same_operator_observer_bulk_degeneracy(self):
        rng=np.random.default_rng(2704)
        n=rng.normal(size=(31,3));n/=np.linalg.norm(n,axis=1)[:,None]
        A=rng.normal(size=(12,31));R=A@n
        result=gls_svd(rng.normal(size=12),np.column_stack([R,-R]),np.eye(12))
        self.assertEqual(result['rank'],3)
        self.assertFalse(result['parameters_identified'])
        np.testing.assert_allclose(np.column_stack([R,-R])@np.r_[np.ones(3),np.ones(3)],0,atol=1e-13)
    def test_bad_covariance(self):
        for C in [np.diag([1,1,0]),np.diag([1,1,-1]),np.array([[1,.1,0],[0,1,0],[0,0,1]])]:
            with self.subTest(C=C.tolist()):_check_gls_rejects_invalid_covariance(C)

if __name__=='__main__':unittest.main(verbosity=2)

import numpy as np
import k02_source_identification as k
from pathlib import Path
from scipy.linalg import svdvals
import pytest
SRC=Path(__file__).resolve().parent.parent/'source/h03/htt_six_paper_h03/inputs/selected_source_observables.npz'

def test_sha():
 c=k.load(SRC);assert len(c['group_id'])==35970
 with pytest.raises(ValueError,match='SHA'):k.load(SRC,sha='0'*64)

def test_basis():
 A=k.STF.reshape(5,9);assert np.allclose(A@A.T,np.eye(5));assert np.max(np.abs(np.trace(k.STF,axis1=1,axis2=2)))<1e-14

def test_gauge_and_real_source_rank():
 d=k.load(SRC);_,X,_,M=k.features(d);np.testing.assert_allclose(X[:,0],M.sum(axis=1),rtol=0,atol=1e-10)
 c=k.source_window(d,.040);assert c['condition_R']<300; assert len(c['shape8'])==8

def test_covariance():
 d=k.load(SRC);w=k.source_window(d,.040);assert np.linalg.eigvalsh(w['cov12'])[0]>-1e-10

def test_optical_stf_sign():
 n=np.array([1.,0.,0.]);S=np.diag([2.,-1.,-1.]);assert k.optical_leading_direction(12,np.array([3.,0.,0.]),S,n)==3

def test_optical_rotation_and_trace():
 n=np.array([1.,0.,0.]);S=np.diag([2.,-1.,-1.]);theta=12.;a=np.array([3.,0.,0.]);U=np.array([[0.,-1,0],[1,0,0],[0,0,1]]);r=k.optical_leading_direction(theta,a,S,n)
 assert abs(k.optical_leading_direction(theta,U@a,U@S@U.T,U@n)-r)<1e-12
 with pytest.raises(ValueError,match='STF'):k.optical_leading_direction(theta,a,S+np.eye(3),n)

def test_group_deletion_stable_rank():
 cols=k.load(SRC)
 for meth in k.METHODS:
  m=cols['method_family']!=meth
  d=10**((cols['dmzp'][m]-25)/5);n=cols['n_J2000'][m]
  W=np.column_stack([np.ones(len(n)),n,np.einsum('ni,aij,nj->na',n,k.STF,n,optimize=True)])
  assert np.linalg.matrix_rank(W.T@W,tol=1e-6)==9

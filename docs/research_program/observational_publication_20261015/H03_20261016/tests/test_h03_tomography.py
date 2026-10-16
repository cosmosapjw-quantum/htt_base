import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import numpy as np
import pytest
from h03_tomography import STF,stf_features,velocity_design,fit,joint_covariance,window,quadrupole_matrix,patch_id,working_sigma,proxy_distance,source_response

def fixture(seed=117,n=512):
 r=np.random.default_rng(seed)
 nv=r.normal(size=(n,3));nv/=np.linalg.norm(nv,axis=1)[:,None]
 d=r.uniform(40,300,size=n);X=velocity_design(d,nv)
 return r,nv,d,X

def test_stf_exact():
 np.testing.assert_allclose([np.trace(x) for x in STF],0,atol=1e-15)
 np.testing.assert_allclose(np.einsum('aij,bij->ab',STF,STF),np.eye(5),atol=1e-15)
 r,n,d,X=fixture();q=r.normal(size=5)
 np.testing.assert_allclose(stf_features(n)@q,np.einsum('ni,ij,nj->n',n,quadrupole_matrix(q),n),atol=1e-14)

def test_exact_simulated_injection_and_independent_qr():
 r,n,d,X=fixture();theta=r.normal(size=9);y=X@theta;w=r.uniform(.01,3,size=len(d))
 o=fit(X,y,w)
 np.testing.assert_allclose(o['theta'],theta,atol=1e-13,rtol=0)
 np.testing.assert_allclose(o['theta'],np.linalg.lstsq(X*np.sqrt(w)[:,None],y*np.sqrt(w),rcond=None)[0],atol=1e-13)
 assert o['identity']<1e-13

def test_joint_covariance_contracted_against_direct():
 r,n,d,X=fixture(n=250);sig=r.uniform(2,8,size=len(d));t=np.zeros(len(d));A=[]
 for x in [.035,.08]:
  w=window(r.uniform(.02,.11,size=len(d)),sig,x,.025)
  A.append(fit(X,t,w)['A'])
 U=np.concatenate(A,axis=0)
 C,R=joint_covariance(U,sig)
 np.testing.assert_allclose(C,U@np.diag(sig**2)@U.T,atol=1e-11,rtol=1e-12)
 assert np.linalg.eigvalsh(C).min()>-1e-9
 assert np.max(np.abs(R))<=1+1e-11

def test_shared_windows_not_independent():
 r,n,d,X=fixture(n=260);y=np.zeros(len(d));s=np.ones(len(d))
 a=fit(X,y,np.ones(len(d)))['A'];C,R=joint_covariance(np.vstack([a,a]),s)
 np.testing.assert_allclose(C[:9,:9],C[:9,9:],atol=1e-15)
 np.testing.assert_allclose(np.diag(R[:9,9:]),1,atol=1e-14)

def test_bulk_dipole_constant_distance_degenerate_broad_depth_recovers():
 _,n,d,X=fixture();a=np.column_stack([n*150,n*150]);assert np.linalg.matrix_rank(a)==3
 b=np.column_stack([d[:,None]*n,n*150]);assert np.linalg.matrix_rank(b)==6
 o=fit(X,np.zeros(len(d)),np.ones(len(d)));resp=source_response(o,n,d)
 assert resp['expansion_dipole_identity_max']<2e-13

def test_antipodal_full_sky_no_false_modes():
 r,n,d,X=fixture(n=256);n=np.vstack([n,-n]);d=np.r_[d,d];X=velocity_design(d,n)
 theta=np.r_[70.,np.zeros(8)]
 est=fit(X,X@theta,np.ones(len(d)))['theta']
 np.testing.assert_allclose(est,theta,atol=1e-12,rtol=0)

def test_window_and_bad_cases():
 r,n,d,X=fixture();sig=working_sigma(d,np.ones(len(d))*.4)
 assert (window(np.ones(len(d))*.05,sig,.05) > 0).all()
 with pytest.raises(ValueError):window(np.ones(len(d))*.05,sig,.05,alpha=1)
 with pytest.raises(ValueError):fit(X,np.zeros(len(d)),np.zeros(len(d)))
 with pytest.raises(ValueError):fit(np.c_[np.ones(len(d)),np.zeros((len(d),8))],np.zeros(len(d)),np.ones(len(d)))
 with pytest.raises(ValueError):proxy_distance(np.array([np.nan]))

def test_patch_ids_12_stable():
 _,n,d,X=fixture();ids=patch_id(n)
 assert np.all((ids>=0)&(ids<12))
 assert len(np.unique(ids))==12

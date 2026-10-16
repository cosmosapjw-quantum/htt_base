import pytest, numpy as np
import external_preconditions as m

def test_radial_rank_6_nonradial_rank_9():
 rng=np.random.default_rng(7);N=rng.normal(size=(64,3));N/=np.linalg.norm(N,axis=1)[:,None]
 r,t=m.radial_and_transverse_operators(N)
 assert np.linalg.matrix_rank(r,tol=1e-11)==6
 assert np.linalg.matrix_rank(np.vstack([r,t.reshape(-1,9)]),tol=1e-11)==9

def test_radial_vorticity_null_but_transverse_nonzero():
 rng=np.random.default_rng(7);N=rng.normal(size=(20,3));N/=np.linalg.norm(N,axis=1)[:,None]
 r,t=m.radial_and_transverse_operators(N)
 J=np.array([[0,2,-3],[-2,0,4],[3,-4,0]],float)
 assert np.max(np.abs(r@J.ravel()))<1e-13
 assert np.max(np.abs(t.reshape(-1,9)@J.ravel()))>1

def test_isotropic_expansion_transverse_zero():
 rng=np.random.default_rng(5);N=rng.normal(size=(14,3));N/=np.linalg.norm(N,axis=1)[:,None]
 r,t=m.radial_and_transverse_operators(N)
 assert np.allclose(r@np.eye(3).ravel(),np.ones(len(N)),atol=1e-12)
 assert np.max(np.abs(t.reshape(-1,9)@np.eye(3).ravel()))<1e-12

def test_only_endpoint_boost_vs_constant_history_is_degenerate():
 t=np.linspace(0,1,300)
 g=np.exp(-.5*((t[:,None]-np.array([.25,.75])[None,:])/.1)**2).T
 g/=np.trapezoid(g,t,axis=1)[:,None]
 mat=m.visibility_history_design(g,t,np.vstack([np.ones_like(t),t]))
 # beta_obs and history const duplicate; history slope separable with two windows
 assert np.linalg.matrix_rank(mat,tol=1e-10)==2
 assert np.allclose(mat[:,0],mat[:,1])
 assert abs(mat[0,2]-mat[1,2])>.3

def test_identical_history_kernel_rank_one():
 t=np.linspace(0,1,301);g=np.ones((3,len(t)));basis=np.vstack([np.ones(len(t)),t]);mat=m.visibility_history_design(g,t,basis)
 assert np.linalg.matrix_rank(mat,tol=1e-10)==1

def test_method_cov_psd_and_correlated():
 d=np.array([30.,40.,50.,60.]);method=['A','A','B','B']
 c=m.common_method_calibration_covariance(d,method,np.array([[4,1],[1,9]],float))
 assert np.linalg.eigvalsh(c)[0]>-1e-12
 assert c[0,1]!=0 and c[0,2]!=0
 with pytest.raises(ValueError,match='PSD'):m.common_method_calibration_covariance(d,method,np.diag([1.,-1.]))

def test_same_sky_processing_correlated():
 a,s,noise=m.simple_null_mixture(50000,.7)
 assert np.corrcoef(a,rowvar=False)[0,1]>.66
 # different processing channels are not distinct cosmological skies
 assert s.shape==(50000,1)

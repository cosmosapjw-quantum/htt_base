from pathlib import Path
import json, hashlib, numpy as np
from scipy.integrate import quad_vec
from scipy.special import ndtr, ndtri
from scripts.r99 import cf4_source_law as cf, gaia_shared_field as ga
class D:
    H0=70
    @staticmethod
    def distance_integral(z,order):return z
z=.002; sr=300/cf.C; cap=np.log1p(z)/sr; prob=ndtr(cap)
def I(t):
    rr=cap-t
    w=np.exp(-rr*rr/2)/np.sqrt(2*np.pi)/prob
    X=ndtri(ndtr(rr)/prob); f=np.log(z/np.expm1(sr*t))-sr*rr
    return w*np.array([f,f*X,f*(X**2-1)/np.sqrt(2),f*f])
raw=quad_vec(I,1e-12,cap+11,epsabs=3e-12,epsrel=3e-12)[0]
raw[3]-=raw[0]**2+raw[1]**2
pred=cf.hermite_moments(D,np.array([z]),np.array([300.]),48)[2,0]
print('CF4 reference',raw,'maxabs GH48',max(abs(raw-pred))); assert np.allclose(raw,pred,atol=1e-7)
src=ga.R98/'GAIA_FULL_SHARED_PATCH.json'; r=json.loads(src.read_text()); cache=Path(r['joint_160d_patch_covariance']['cache_path'])
with np.load(cache) as d:
    X=d['leave']; V=np.linalg.svd(X-X.mean(axis=0),full_matrices=False); ss=V[1]; use=ss>ss[0]*1e-5; V=V[2][use]; y=np.concatenate([r['fits'][str(k)]['coefs_microasyr'] for k in d['names']]); q=np.sum(((V@y)/ss[use])**2)*48/47
    rr=y-V.T@(V@y); norm=np.linalg.norm(rr); print('Gaia SVD independent',use.sum(),q,norm,rr@rr/(y@y))
    orig=ga.supported_subspace(y,d['cov']); assert np.isclose(q,orig['supported_quadratic_form']) and np.isclose(norm,orig['unsupported_component_norm_microasyr'])
for n in ['CF4_RESULTS.json','GAIA_SHARED_FIELD_RESULTS.json','GAIA_SHARED_FIELD_COVARIANCES.npz','OPTICAL_RESULTS.json']:
    f=ga.OUT/n; print(n,hashlib.sha256(f.read_bytes()).hexdigest())
for path in ['scripts/r99/cf4_source_law.py','htt/bass/transport/finite_redshift_optics.py','scripts/r99/optical.py','scripts/r99/gaia_shared_field.py']:
    print(path,hashlib.sha256(Path(path).read_bytes()).hexdigest())

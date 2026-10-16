"""P3/H03: source-conditioned CF4 redshift/sky-window STF tomography.

Fits only a fixed-weight *apparent* working expansion proxy cz ~ d*(H + D.n + n.Q.n).
The input covariance below is conditional diagonal working noise; empirical CF4 method
and selection covariance, velocity flow, physical geometry, and inference are absent.
"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
from scipy.linalg import qr, solve_triangular, svdvals

SOURCE_SHA256 = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
C_KM_S = 299792.458
MU_FACTOR = np.log(10.)/5.
CENTERS = (.025, .04, .06, .08)
WIDTH = .012
METHODS = ('FP', 'OTHER', 'SN', 'TF')
# Five real Cartesian STF tensors, orthonormal in Frobenius inner product.
STF = np.array([
 [[1,0,0],[0,-1,0],[0,0,0]],
 [[1,0,0],[0,1,0],[0,0,-2]],
 [[0,1,0],[1,0,0],[0,0,0]],
 [[0,0,1],[0,0,0],[1,0,0]],
 [[0,0,0],[0,0,1],[0,1,0]]
 ], dtype=float)
STF /= np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]

@dataclass(frozen=True)
class Input:
    z: np.ndarray
    mu: np.ndarray
    e_mu: np.ndarray
    n: np.ndarray
    method: np.ndarray
    ids: np.ndarray


def digest(path:Path)->str:
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()


def source(path:Path,expected_sha:str=SOURCE_SHA256)->Input:
    if digest(path)!=expected_sha:raise ValueError('CF4 source SHA256 mismatch')
    with np.load(path,allow_pickle=False) as npz:
        keys=('z_CMB','dmzp','e_dmzp','n_J2000','method_family','group_id')
        if any(k not in npz.files for k in keys):raise ValueError('missing authenticated CF4 fields')
        z,mu,err,n,method,ids=[npz[k].copy() for k in keys]
    if (len(z)!=35970 or mu.shape!=z.shape or err.shape!=z.shape or
        n.shape!=(len(z),3) or len(method)!=len(z) or len(ids)!=len(z) or
        len(np.unique(ids))!=len(z) or not np.isfinite(z).all() or
        not np.isfinite(mu).all() or not np.isfinite(err).all() or
        not np.isfinite(n).all() or not np.allclose(np.sum(n*n,axis=1),1,rtol=0,atol=5e-12) or
        np.any(z<=0) or np.any(z>=.2) or np.any(err<=0) or np.any(mu<20) or
        np.any(mu>60) or any(m not in METHODS for m in np.unique(method))):
        raise ValueError('CF4 35970-cohort/geometry validation failed')
    return Input(z,mu,err,n,method,ids)


def proxy_distance(mu:np.ndarray)->np.ndarray:
    m=np.asarray(mu,float)
    if not np.isfinite(m).all() or np.any(m<20) or np.any(m>60):raise ValueError('unphysical working modulus')
    return 10.**((m-25.)/5.)


def working_sigma(d:np.ndarray,e:np.ndarray,h_ref=70.,pec_km_s=250.)->np.ndarray:
    d=np.asarray(d,float);e=np.asarray(e,float)
    if d.shape!=e.shape or not np.isfinite(d).all() or not np.isfinite(e).all() or np.any(d<=0) or np.any(e<=0) or h_ref<=0 or pec_km_s<=0:raise ValueError('invalid assumed noise law')
    return np.hypot(pec_km_s,MU_FACTOR*h_ref*d*e)


def stf_features(n:np.ndarray)->np.ndarray:
    n=np.asarray(n,float)
    if n.ndim!=2 or n.shape[1]!=3 or not np.isfinite(n).all() or not np.allclose(np.sum(n*n,axis=1),1,atol=5e-12,rtol=0):raise ValueError('unit vectors required')
    return np.einsum('ni,aij,nj->na',n,STF,n,optimize=True)


def velocity_design(d:np.ndarray,n:np.ndarray)->np.ndarray:
    d=np.asarray(d,float);n=np.asarray(n,float)
    if d.shape!=(len(n),) or np.any(d<=0) or not np.isfinite(d).all():raise ValueError('invalid distance geometry')
    return np.column_stack((np.ones(len(n)),n,stf_features(n)))*d[:,None]


def window(z:np.ndarray,sig:np.ndarray,center:float,bandwidth:float=WIDTH,
           n:np.ndarray|None=None,alpha:float=0.,active:np.ndarray|None=None)->np.ndarray:
    z=np.asarray(z,float);sig=np.asarray(sig,float)
    if (z.shape!=sig.shape or not np.isfinite(z).all() or not np.isfinite(sig).all() or np.any(sig<=0)
        or not np.isfinite(center) or not 0<center<.2 or not 0<bandwidth<.2 or not np.isfinite(alpha) or abs(alpha)>=1):raise ValueError('invalid window contract')
    k=np.exp(-.5*((z-center)/bandwidth)**2)/sig**2
    if alpha:
        if n is None or n.shape!=(len(z),3):raise ValueError('directional weighting needs directions')
        k*=1+alpha*n[:,2]
    if active is not None:
        active=np.asarray(active)
        if active.shape!=z.shape or active.dtype.kind!='b':raise ValueError('active support must be boolean')
        k=np.where(active,k,0.)
    if np.count_nonzero(k)<10 or not np.isfinite(k).all() or np.any(k<0):raise ValueError('empty/invalid window')
    return k


def fit(X:np.ndarray,y:np.ndarray,w:np.ndarray,cond_limit:float=1e9, influence:bool=True)->dict:
    X=np.asarray(X,float);y=np.asarray(y,float);w=np.asarray(w,float)
    if X.ndim!=2 or X.shape[1]!=9 or y.shape!=(len(X),) or w.shape!=y.shape or not np.isfinite(X).all() or not np.isfinite(y).all() or not np.isfinite(w).all() or np.any(w<0) or np.count_nonzero(w)<=9:raise ValueError('invalid nine-parameter fit')
    s=np.sqrt(w); Z=s[:,None]*X
    q,r=qr(Z,mode='economic',check_finite=False)
    vals=svdvals(r); cond=float(vals[0]/vals[-1]) if vals[-1]>0 else np.inf
    if not np.isfinite(cond) or cond>cond_limit:raise ValueError('rank or design condition gate')
    theta=solve_triangular(r,q.T@(s*y),check_finite=False)
    left=solve_triangular(r,q.T,check_finite=False)*s[None,:] if influence else None
    ident=float(np.max(np.abs(left@X-np.eye(9)))) if influence else float(np.max(np.abs(solve_triangular(r,q.T@Z,check_finite=False)-np.eye(9))))
    if ident>1e-9:raise ArithmeticError('WLS identity failure')
    return {'theta':theta,'A':left,'cond':cond,'identity':ident,
            'nactive':int(np.count_nonzero(w)),
            'chi2_proxy':float(np.dot(w,(y-X@theta)**2)),
            'weighted_n_eff':float(np.sum(w)**2/np.dot(w,w)),
            'weighted_distance_n_eff':float(np.sum(w*X[:,0]**2)**2/np.dot(w*X[:,0]**2,w*X[:,0]**2))}


def joint_covariance(A:np.ndarray,sig:np.ndarray)->tuple[np.ndarray,np.ndarray]:
    A=np.asarray(A,float);sig=np.asarray(sig,float)
    if A.ndim!=2 or sig.shape!=(A.shape[1],) or not np.isfinite(A).all() or not np.isfinite(sig).all() or np.any(sig<=0):raise ValueError('invalid conditional linear map and diagonal sigma')
    U=A*sig[None,:];C=U@U.T
    C=(C+C.T)/2
    s=np.sqrt(np.diag(C));
    if np.any(s<=0):raise ValueError('non-positive variance')
    corr=C/s[:,None]/s[None,:]
    if np.linalg.eigvalsh(C).min()<-1e-10*max(1,np.linalg.norm(C,2)):raise ValueError('non-PSD covariance')
    return C,corr


def quadrupole_matrix(q:np.ndarray)->np.ndarray:
    q=np.asarray(q,float)
    if q.shape!=(5,) or not np.isfinite(q).all():raise ValueError('five STF coefficients required')
    return np.einsum('a,aij->ij',q,STF)


def patch_id(n:np.ndarray, azbins:int=6)->np.ndarray:
    n=np.asarray(n,float)
    if n.ndim!=2 or n.shape[1]!=3:raise ValueError('directions required')
    phi=np.mod(np.arctan2(n[:,1],n[:,0]),2*np.pi)
    return (n[:,2]>=0).astype(int)*azbins+np.minimum(azbins-1,np.floor(azbins*phi/(2*np.pi)).astype(int))


def source_response(fit_obj:dict,n:np.ndarray,d:np.ndarray)->dict:
    """Response of fitted parameters to bulk velocity at fixed source distances.
    A@n has dimension 1/Mpc. D operator A@(d*n) is exactly the fitted dipole
    injection, and does not assert cosmological source velocity transfer.
    """
    A=fit_obj['A'];X=velocity_design(d,n)
    raw=A@n
    injected=A@X
    return {'bulk_response_inverse_mpc':raw,
            'expansion_dipole_identity_max':float(np.max(np.abs(injected[:,1:4]-np.eye(9)[:,1:4])))}

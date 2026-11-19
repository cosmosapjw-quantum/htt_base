"""R79 source-qualified, optional native survey math for R78 SQ-01..SQ-10.

Pure numerical preparation. No physical source identification, no Bianchi
native low-ell solver and no astrophysical null/PTE. Historical R60-R78
executables, results and user datasets remain untouched.
"""
from __future__ import annotations

import ctypes
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.linalg import cho_factor,cho_solve
from scripts.r68.fiveview_geometry import E,stf_matrix


def _array(x,name,ndim=None,shape_tail=None):
    z=np.asarray(x,dtype=np.float64)
    if ndim is not None and z.ndim!=ndim:
        raise ValueError(f"{name} must have {ndim} dimensions")
    if shape_tail is not None and z.shape[-len(shape_tail):]!=shape_tail:
        raise ValueError(f"{name} ending shape must be {shape_tail}")
    if not np.all(np.isfinite(z)):
        raise ValueError(f"{name} must be finite")
    return np.ascontiguousarray(z,dtype=np.float64)


def _unit_directions(dirs):
    n=_array(dirs,"directions",2,(3,))
    if len(n)==0 or np.any(np.abs(np.sum(n*n,axis=1)-1)>2e-10):
        raise ValueError("nonempty unit source directions required")
    return n


@lru_cache(maxsize=8)
def _library(path):
    path=Path(path)
    if not path.is_file():
        raise ValueError("explicit native shared library missing")
    return ctypes.CDLL(str(path.resolve()))


def accumulate_gaia(B,mu,e1,e2,rho,*,native_lib=None,threads=1):
    """Real source 2x2 correlated astrometric Gaussian Fisher, score and chi2.

    B[N,2,P] physical tangent templates, mu[N,2], e1/e2 positive errors,
    |rho|<1 correlation; returns (P,P) Fisher, P score, scalar chi2.
    The optional source-compiled C++ function is an explicit opt-in.
    """
    B=_array(B,"B",3)
    if B.shape[1]!=2 or B.shape[2]<1 or B.shape[2]>32:
        raise ValueError("B must be (N,2,1..32)")
    mu=_array(mu,"mu",2)
    n,p=B.shape[0],B.shape[2]
    if n<1 or mu.shape!=(n,2):
        raise ValueError("Gaia observation count or shape mismatch")
    e1,e2,rho=(_array(z,name,1) for z,name in
               ((e1,"e1"),(e2,"e2"),(rho,"rho")))
    if any(z.shape!=(n,) for z in (e1,e2,rho)):
        raise ValueError("per-source Gaia covariance dimensions mismatch")
    if np.any(e1<=0) or np.any(e2<=0) or np.any(np.abs(rho)>=1):
        raise ValueError("non-SPD per-source astrometric covariance")
    if not isinstance(threads,int) or threads<1 or threads>64:
        raise ValueError("threads must be integer 1..64")
    if native_lib is not None:
        lib=_library(str(native_lib))
        fn=lib.htt_vsh_normal_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,ctypes.c_int32,fp,fp,fp,fp,fp,
                     ctypes.c_int32,fp,fp,fp]
        fn.restype=ctypes.c_int
        F=np.empty((p,p),np.float64)
        score=np.empty(p,np.float64)
        chi=np.empty(1,np.float64)
        rc=fn(n,p,B,mu,e1,e2,rho,threads,F,score,chi)
        if rc:
            raise RuntimeError(f"C++ Gaia source kernel failed, code {rc}")
        if not np.all(np.isfinite(F)) or not np.all(np.isfinite(score)) or not np.isfinite(chi[0]):
            raise FloatingPointError("native Gaia accumulation nonfinite")
        return F,score,float(chi[0])
    inv=1.0/(1-rho*rho)
    w00=inv/(e1*e1);w11=inv/(e2*e2);w01=-rho*inv/(e1*e2)
    v0=w00*mu[:,0]+w01*mu[:,1]
    v1=w01*mu[:,0]+w11*mu[:,1]
    b0,b1=B[:,0,:],B[:,1,:]
    score=np.einsum("ni,n->i",b0,v0)+np.einsum("ni,n->i",b1,v1)
    F=np.einsum("ni,nj,n->ij",b0,b0,w00)+np.einsum("ni,nj,n->ij",b1,b1,w11)
    F+=np.einsum("ni,nj,n->ij",b0,b1,w01)+np.einsum("ni,nj,n->ij",b1,b0,w01)
    chi=float(np.sum(mu[:,0]*v0+mu[:,1]*v1))
    if not np.all(np.isfinite(F)) or not np.all(np.isfinite(score)) or not np.isfinite(chi):
        raise FloatingPointError("source covariance accumulation overflow")
    return F,score,chi


def hemisphere_moments(directions,axis,weights=None,*,native_lib=None):
    """Normalized weighted hemisphere m and M, plus weight totals/counts.

    Negative dot belongs to hemisphere 0; exactly zero also belongs to 0.
    """
    n=_unit_directions(directions)
    p=_array(axis,"axis",1)
    if p.shape!=(3,) or abs(np.linalg.norm(p)-1)>2e-10:
        raise ValueError("unit hemisphere axis required")
    w=np.ones(len(n)) if weights is None else _array(weights,"weights",1)
    if w.shape!=(len(n),) or np.any(w<0) or not np.any(w>0):
        raise ValueError("nonnegative nonzero source weights required")
    labels=(n@p>0)
    counts=np.bincount(labels.astype(np.int64),minlength=2)
    if any(counts==0):
        raise ValueError("both hemispheres require sources")
    if native_lib is not None:
        lib=_library(str(native_lib))
        fn=lib.htt_hemisphere_moments_v1
        fp=np.ctypeslib.ndpointer(dtype=np.float64,flags="C_CONTIGUOUS")
        fn.argtypes=[ctypes.c_int64,fp,fp,fp,fp,ctypes.POINTER(ctypes.c_int)]
        fn.restype=None
        raw=np.zeros(20,dtype=np.float64)
        status=ctypes.c_int(-999)
        fn(len(n),n,w,p,raw,ctypes.byref(status))
        if status.value:
            raise RuntimeError(f"Fortran source mask kernel error {status.value}")
        raw=raw.reshape(2,10)
        sumw=raw[:,0]
        moments=raw[:,1:4]
        second=np.zeros((2,3,3))
        second[:,0,0]=raw[:,4]
        second[:,0,1]=second[:,1,0]=raw[:,5]
        second[:,0,2]=second[:,2,0]=raw[:,6]
        second[:,1,1]=raw[:,7]
        second[:,1,2]=second[:,2,1]=raw[:,8]
        second[:,2,2]=raw[:,9]
    else:
        sumw=np.bincount(labels.astype(np.int64),weights=w,minlength=2)
        moments=np.zeros((2,3))
        second=np.zeros((2,3,3))
        for h in (0,1):
            mask=labels if h else ~labels
            rows=n[mask];wh=w[mask]
            moments[h]=np.einsum("n,ni->i",wh,rows)
            second[h]=np.einsum("n,ni,nj->ij",wh,rows,rows)
    if np.any(sumw<=0) or not np.all(np.isfinite(second)):
        raise ValueError("empty weight hemisphere or nonfinite result")
    return {"weights":sumw,"means":moments/sumw[:,None],
            "second":second/sumw[:,None,None],"counts":counts}


def ring_softmax_occupancy(logw,rings,event,ring_totals,*,directions=None,k=1.0):
    """Stable conditional source F and beta-score under fixed ring counts.

    The derivative requires source directions. Ring i's count is ring_totals[i].
    This is selection-score geometry, not physical time or velocity detection.
    """
    logs=_array(logw,"logw",1)
    rings=np.asarray(rings)
    e=np.asarray(event,dtype=bool)
    totals=_array(ring_totals,"ring_totals",1)
    n=len(logs)
    if n<1 or rings.shape!=(n,) or e.shape!=(n,) or totals.size<1:
        raise ValueError("ring source shapes mismatch")
    if not np.issubdtype(rings.dtype,np.integer) or np.any(rings<0) or np.any(rings>=len(totals)):
        raise ValueError("ring IDs must index totals exactly")
    if np.any(totals<0) or totals.sum()<=0 or not np.isfinite(k):
        raise ValueError("ring total or response invalid")
    dirs=None if directions is None else _array(directions,"directions",2,(3,))
    if dirs is not None and len(dirs)!=n:
        raise ValueError("ring directions mismatch")
    order=np.argsort(rings,kind="stable")
    ids=rings[order]
    start=np.r_[0,np.flatnonzero(np.diff(ids))+1]
    end=np.r_[start[1:],n]
    occ=0.
    grad=np.zeros(3)
    seen=np.zeros(len(totals),bool)
    for st,ed in zip(start,end):
        rid=int(ids[st]);seen[rid]=True
        weight=totals[rid]/np.sum(totals)
        if weight==0:continue
        indices=order[st:ed]
        local=logs[indices]
        eprime=np.exp(local-local.max());prob=eprime/eprime.sum()
        f=float(np.dot(prob,e[indices]))
        occ+=weight*f
        if dirs is not None:
            nv=dirs[indices]
            grad+=float(k)*weight*(np.einsum("n,n,ni->i",prob,e[indices],nv)-f*(prob@nv))
    if np.any((totals>0)&(~seen)):
        raise ValueError("positive ring total without observed source")
    return {"F":float(occ),"dF_dbeta":grad if dirs is not None else None}


def rotate_stf(x,R):
    v=_array(x,"signed STF5")
    if v.shape[-1]!=5:raise ValueError("five STF coordinates required")
    R=_array(R,"SO3 R",2,(3,3))
    if abs(np.linalg.det(R)-1)>5e-11 or np.linalg.norm(R@R.T-np.eye(3))>5e-11:
        raise ValueError("proper orthogonal SO(3) frame required")
    S=stf_matrix(v)
    Sr=np.einsum("ia,...ab,jb->...ij",R,S,R)
    return np.einsum("...ij,aij->...a",Sr,E)


def confidence_support(mean,C,rows,*,cutoff):
    m=_array(mean,"mean",1)
    C=_array(C,"joint source covariance",2)
    rows=_array(rows,"affine source rows",2)
    d=len(m)
    if C.shape!=(d,d) or rows.shape[1]!=d or cutoff<=0 or not np.isfinite(cutoff):
        raise ValueError("confidence ellipsoid source dimensions/cutoff")
    if np.linalg.norm(C-C.T)>1e-11*max(1.,np.linalg.norm(C)):
        raise ValueError("source covariance not symmetric")
    np.linalg.cholesky(C)
    center=rows@m
    r2=np.einsum("ni,ij,nj->n",rows,C,rows)
    half=np.sqrt(cutoff*np.maximum(r2,0.))
    return center-half,center+half


class OnlineCovariance:
    """Stable finite Gaussian simulation moments; simulation identity external."""
    def __init__(self,dimension):
        if not isinstance(dimension,int) or dimension<1:raise ValueError("positive dimension")
        self.dimension=dimension
        self.count=0
        self.mean=np.zeros(dimension)
        self._M2=np.zeros((dimension,dimension))

    def update(self,rows):
        x=_array(rows,"MC rows",2)
        if x.shape[1]!=self.dimension:raise ValueError("MC feature count mismatch")
        n=len(x)
        if not n:return
        mean=x.mean(axis=0)
        centered=x-mean
        M2=centered.T@centered
        if not self.count:
            self.count=n;self.mean=mean;self._M2=M2
            return
        delta=mean-self.mean
        count=self.count+n
        self._M2+=M2+np.outer(delta,delta)*(self.count*n/count)
        self.mean+=delta*(n/count)
        self.count=count

    def covariance(self):
        if self.count<2:raise ValueError("sample covariance needs >=2 realizations")
        return self._M2/(self.count-1)


def photon_feasibility(S,*,f=None,tol=1e-11):
    """PSD moment feasibility, with required flux-missing unknown status."""
    S=_array(S,"photon STF",2,(3,3))
    if np.linalg.norm(S-S.T)>tol*max(1.,np.linalg.norm(S)) or abs(np.trace(S))>tol*max(1.,np.linalg.norm(S)):
        raise ValueError("photon normalized stress must be STF")
    P=np.eye(3)/3+S
    eig=np.linalg.eigvalsh(P)
    result={"pressure_eig":eig,"pressure_PSD":bool(eig[0]>=-tol),
            "flux_missing":f is None,"admissible":None}
    if f is not None:
        f=_array(f,"normal photon flux",1)
        if f.shape!=(3,):raise ValueError("3-vector photon flux required")
        cov_eig=np.linalg.eigvalsh(P-np.outer(f,f))
        result["admissible"]=bool(eig[0]>=-tol and cov_eig[0]>=-tol)
        result["moment_covariance_min_eig"]=float(cov_eig[0])
    return result


def codazzi_map(a,N):
    """General oriented Bianchi linear Lie-Codazzi map 5 signed -> 3 flux.

    Dimensionless a=c spatial-a/H and N=c spatial-N/H; Na=0 by Jacobi.
    """
    a=_array(a,"Lie a",1)
    N=_array(N,"Lie N",2,(3,3))
    if a.shape!=(3,):raise ValueError("Lie a vector 3 required")
    scale=max(1.,np.linalg.norm(N),np.linalg.norm(a))
    if np.linalg.norm(N-N.T)>1e-11*scale or np.linalg.norm(N@a)>1e-11*scale:
        raise ValueError("symmetric Lie N and Jacobi Na=0 required")
    eps=np.zeros((3,3,3))
    for i,j,k in ((0,1,2),(1,2,0),(2,0,1)):eps[i,j,k]=1;eps[i,k,j]=-1
    # E[a,j,l] signed/orthonormal tracefree tensor
    result=-3*np.einsum("aij,j->ai",E,a)+np.einsum("ijk,ajl,lk->ai",eps,E,N)
    return result.T


def sachs_rhs(state,tidal):
    """Sachs Jacobi fixed-affine 2x2 first-order ODE, no finite-z solver."""
    y=_array(state,"Jacobi state",1)
    T=_array(tidal,"screen optical tidal",2,(2,2))
    if y.shape!=(8,) or np.linalg.norm(T-T.T)>1e-11*max(1.,np.linalg.norm(T)):
        raise ValueError("state of two 2x2 matrices and symmetric tidal matrix")
    J=y[:4].reshape(2,2);K=y[4:].reshape(2,2)
    return np.r_[K.ravel(),(-T@J).ravel()]


def schur_covariance(C,block_dim):
    """Schur C22 - C21 C11^-1 C12, correlated Gaussian source."""
    C=_array(C,"joint source covariance",2)
    if C.shape[0]!=C.shape[1] or not 0<block_dim<len(C):
        raise ValueError("joint covariance and split invalid")
    if np.linalg.norm(C-C.T)>1e-11*max(1.,np.linalg.norm(C)):
        raise ValueError("joint covariance not symmetric")
    np.linalg.cholesky(C)
    x,y=C[:block_dim,:block_dim],C[:block_dim,block_dim:]
    cf=cho_factor(x,lower=True,check_finite=False)
    S=C[block_dim:,block_dim:]-y.T@cho_solve(cf,y,check_finite=False)
    return .5*(S+S.T)


def radial_design(r_mpc,directions,*,reference_mpc=100.):
    """Phenomenological 1/r dipole leverage, not source-qualified H_D(z,n)."""
    r=_array(r_mpc,"positive radius",1)
    n=_unit_directions(directions)
    if len(r)!=len(n) or np.any(r<=0) or reference_mpc<=0 or not np.isfinite(reference_mpc):
        raise ValueError("source distance, frame or reference radius mismatch")
    q=np.einsum("ni,aij,nj->na",n,E,n)
    return np.column_stack([np.ones(len(r)),n,q,(reference_mpc/r)[:,None]*n])

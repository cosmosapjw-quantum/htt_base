"""Seven bounded mathematical admission prerequisites; never an observational validation."""
from __future__ import annotations
import math
import numpy as np
from scipy.special import log_ndtr

C_SI=299792458.0

def partial_interval(x_known:float, unknown_lower:float|None, unknown_upper:float|None):
    """Minkowski sum; None denotes unconstrained infinity, not zero."""
    if not math.isfinite(x_known):raise ValueError('x_known finite required')
    lo=float('-inf') if unknown_lower is None else x_known+unknown_lower
    hi=float('inf') if unknown_upper is None else x_known+unknown_upper
    if lo>hi:raise ValueError('empty physical bound')
    return lo,hi


def exceedance_bounds(weights, values, t):
    """Sharp *mathematical* outer bounds for an unrestricted unknown event.

    Values=None mean that a draw's event is unknown, not that physical model is
    defined there. No default values or renormalization. Original weights sum 1.
    """
    w=np.asarray(weights,dtype=float)
    if w.ndim!=1 or len(w)!=len(values) or len(w)==0 or not np.all(np.isfinite(w)) or np.any(w<0):raise ValueError('bad weights')
    if abs(float(np.sum(w))-1)>1e-12:raise ValueError('weights must sum to one')
    if not np.isfinite(t):raise ValueError('threshold must be finite')
    for v in values:
        if v is not None and not np.isfinite(v):raise ValueError('nonfinite defined value')
    known_above=float(sum(p for p,v in zip(w,values) if v is not None and v>t))
    missing=float(sum(p for p,v in zip(w,values) if v is None))
    return known_above,known_above+missing,missing


def logdiffexp(A,B):
    """Stable log(exp(A)-exp(B)) for A>B."""
    if not A>B:raise ValueError('expected A > B')
    return A+math.log(-math.expm1(B-A))


def selected_normal_loglike(y,mu,sigma,low=None,high=None):
    """Y|low<Y<high, Y~Normal(mu,sigma); fixed selected-count likelihood."""
    if sigma<=0 or not np.isfinite([y,mu,sigma]).all():raise ValueError('invalid normal')
    if low is not None and y<=low:raise ValueError('outside selected support')
    if high is not None and y>=high:raise ValueError('outside selected support')
    if low is not None and high is not None and not low<high:raise ValueError('empty selection')
    a=(low-mu)/sigma if low is not None else -np.inf
    b=(high-mu)/sigma if high is not None else np.inf
    if a==-np.inf and b==np.inf: log_Z=0.0
    elif a==-np.inf:log_Z=float(log_ndtr(b))
    elif b==np.inf:log_Z=float(log_ndtr(-a))
    elif a>0:log_Z=logdiffexp(float(log_ndtr(-a)),float(log_ndtr(-b)))
    else:log_Z=logdiffexp(float(log_ndtr(b)),float(log_ndtr(a)))
    return -0.5*((y-mu)/sigma)**2-math.log(sigma)-0.5*math.log(2*math.pi)-log_Z


def truncated_gaussian_mean_positive(mu=0.0,sigma=1.0):
    from scipy.special import ndtr
    a=(0-mu)/sigma
    return mu+sigma*math.exp(-a*a/2)/math.sqrt(2*math.pi)/(1-ndtr(a))


def witness_L03_same_sky(Nsky=80,Nmethods=4,seed=11):
    rng=np.random.default_rng(seed)
    latent=rng.normal(size=(Nsky,1))
    noised=rng.normal(scale=0.3,size=(Nsky,Nmethods))
    observed=latent+noised
    corr=np.corrcoef(observed,rowvar=False)
    return corr,float(np.mean(corr[np.triu_indices(Nmethods,1)]))


def history_design(z1=0.25,z2=1.1):
    """c_i=b_obs+b_mat0+b_mat1*<z>_i; two channels cannot identify three sources."""
    F=np.array([[1.,1.,z1],[1.,1.,z2]])
    return F, np.linalg.svd(F,compute_uv=False)


def sky_directions(n=160,seed=27):
    rng=np.random.default_rng(seed)
    x=rng.normal(size=(n,3));return x/np.linalg.norm(x,axis=1)[:,None]


def symmetric_stf5(n):
    nx,ny,nz=n.T
    return np.column_stack([nx*nx-nz*nz,ny*ny-nz*nz,2*nx*ny,2*nx*nz,2*ny*nz])


def radial_tangential_joint(n):
    """9 gradient coefficients; c-dependent physical conversion is NOT asserted.

    T(n)=(I-nn^T) G n. Unknown proper-motion frame spin adds three
    columns that exactly duplicate the antisymmetric part of G.
    """
    N=len(n); nr=np.zeros((N,9)); trans=np.zeros((N,3,9)); skew=np.zeros((N,3,3))
    E=np.eye(3)
    for i,x in enumerate(n):
        P=E-np.outer(x,x)
        for a in range(3):
            for b in range(3):
                j=3*a+b
                D=np.zeros((3,3));D[a,b]=1
                nr[i,j]=x@D@x
                trans[i,:,j]=P@D@x
        for j in range(3):skew[i,:,j]=np.cross(E[j],x)
    # Stack each 3-vector's projected entries (rank two per object) plus the radial.
    A=np.concatenate([nr,trans.reshape(N*3,9)],axis=0)
    frame=np.concatenate([np.zeros((N,3)),skew.reshape(N*3,3)],axis=0)
    return A,np.column_stack((A,frame)),nr


def jacobi_majorant(K,s):
    """If ||R(s)|| <= K (affine s in length units), ||D-sI|| <= sinh(sqrt(K)s)/sqrt(K)-s."""
    if K<0 or s<0:raise ValueError('nonnegative K,s')
    x=s*math.sqrt(K)
    return s*(math.sinh(x)/x-1) if x>1e-9 else s*x*x/6


def physical_bianchi_registry():
    types=['I','II','III','IV','V','VI_0','VI_h','VII_0','VII_h','VIII','IX']
    nearly=['I','V','VII_0','VII_h','IX']
    return {'canonical_11':types,'aniCLASS_near_FLRW':nearly,'exceptional':'VI_-1/9 is within VI_h branch','full_all_m_complete':False}

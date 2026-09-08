"""Full STF SO(3) distance intervals and complete, symmetric score pools."""
from __future__ import annotations
from dataclasses import dataclass
from itertools import product
from functools import lru_cache
from fractions import Fraction
import math
import numpy as np
from scipy.optimize import minimize
from scipy.spatial.transform import Rotation
from common.r7_contracts import finite_array, content_id


@dataclass(frozen=True)
class RotationCover:
    rotations: np.ndarray
    radius: float | None
    cover_id: str
    proof: str | None
    evaluation_error_factor: float | None


@lru_cache(maxsize=3)
def rational_quaternion_cover(resolution=1):
    """Cover S3 by the eight faces of a cube, identifying q and -q.

    Set one maximal positive quaternion component to 1 and round the other
    three in [-1,1] with step 1/m. Pre-normalization error <=sqrt(3)/(2m),
    normalization is 2-Lipschitz here. Rotation angle <=pi times quaternion
    chord length, giving delta <=pi sqrt(3)/m, capped by pi. Rational matrix
    entries avoid dependence on trigonometric grid evaluation. 355/113>pi and
    7/4>sqrt(3) give an outward rational covering bound.
    """
    if not isinstance(resolution,int) or not 1<=resolution<=100: raise ValueError("cover resolution must be an integer in [1,100]")
    m=resolution;matrices=[];seen=set()
    for axis in range(4):
        for rest in product(range(-m,m+1),repeat=3):
            q=list(rest);q.insert(axis,m);key=tuple(q)
            if key in seen or tuple(-v for v in q) in seen: continue
            seen.add(key)
            w,x,y,z=q;s=w*w+x*x+y*y+z*z
            matrices.append(np.array([[s-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                [2*(x*y+z*w),s-2*(x*x+z*z),2*(y*z-x*w)],
                [2*(x*z-y*w),2*(y*z+x*w),s-2*(x*x+y*y)]],dtype=float)/s)
    array=np.array(matrices);array.setflags(write=False)
    radius=float(Fraction(355,113)*min(Fraction(1),Fraction(7,4*m)))
    return RotationCover(array,np.nextafter(radius,np.inf),
        f"RATIONAL_QUATERNION_CUBE_{m}","cube-rounding normalization/chord bound; outward IEEE intervals",0.)


@dataclass(frozen=True)
class DistanceInterval:
    lower: float
    upper: float
    numerical_status: str
    convention_id: str
    error_identity: str
    evaluation_error: float
    rotation_witness: np.ndarray


def _tensors(Q,O):
    q=finite_array(Q,shape=(3,3));o=finite_array(O,shape=(3,3,3))
    scale=max(np.linalg.norm(q),np.linalg.norm(o))
    tolerance=64*np.finfo(float).eps*scale
    if np.max(abs(q-q.T))>tolerance or abs(np.trace(q))>3*tolerance:
        raise ValueError("Q must be symmetric trace-free")
    if any(np.max(abs(o-o.transpose(p)))>tolerance for p in ((1,0,2),(2,1,0))): raise ValueError("O must be symmetric")
    if np.linalg.norm(np.einsum('iik->k',o))>3*tolerance: raise ValueError("O must be trace-free")
    return q,o


def _rotate(q,o,r):
    return r@q@r.T,np.einsum('ia,jb,kc,abc->ijk',r,r,r,o)


def _add(a,b): return np.nextafter(a[0]+b[0],-np.inf),np.nextafter(a[1]+b[1],np.inf)


def _mul(a,b):
    products=np.array([a[0]*b[0],a[0]*b[1],a[1]*b[0],a[1]*b[1]])
    return np.nextafter(products.min(axis=0),-np.inf),np.nextafter(products.max(axis=0),np.inf)


def _norm_interval(a):
    lo,hi=a
    low_abs=np.where((lo<=0)&(hi>=0),0.,np.minimum(abs(lo),abs(hi)))
    high_abs=np.maximum(abs(lo),abs(hi))
    squares=(np.maximum(0.,np.nextafter(low_abs**2,-np.inf)),np.nextafter(high_abs**2,np.inf))
    lower=np.zeros(lo.shape[0]);upper=lower.copy()
    for j in range(lo.shape[1]):
        lower=np.maximum(0.,np.nextafter(lower+squares[0][:,j],-np.inf))
        upper=np.nextafter(upper+squares[1][:,j],np.inf)
    return np.maximum(0.,np.nextafter(np.sqrt(lower),-np.inf)),np.nextafter(np.sqrt(upper),np.inf)


def _distance_intervals(q,o,p,t,rs,q0,o0):
    """Outward evaluation for exact rotations enclosed by each matrix +/- one ulp.

    The registered cube matrices are correctly rounded ratios of exact integers.
    Local candidates are rational quaternion matrices, rounded only at the last
    conversion. Every product, sum, division, square and square root is enclosed.
    IEEE-754 binary64 gradual underflow and correctly rounded scalar operations
    are the explicit arithmetic assumptions; no empirical error factor is used.
    """
    rl=np.nextafter(rs,-np.inf);rh=np.nextafter(rs,np.inf)
    qlo=np.zeros((len(rs),3,3));qhi=qlo.copy()
    olo=np.zeros((len(rs),3,3,3));ohi=olo.copy()
    for a,b in product(range(3),repeat=2):
        term=_mul((rl[:,:,a,None],rh[:,:,a,None]),(rl[:,None,:,b],rh[:,None,:,b]))
        qlo,qhi=_add((qlo,qhi),_mul(term,(p[a,b],p[a,b])))
    for a,b,c in product(range(3),repeat=3):
        term=_mul((rl[:,:,a,None,None],rh[:,:,a,None,None]),(rl[:,None,:,b,None],rh[:,None,:,b,None]))
        term=_mul(term,(rl[:,None,None,:,c],rh[:,None,None,:,c]))
        olo,ohi=_add((olo,ohi),_mul(term,(t[a,b,c],t[a,b,c])))
    dl=np.concatenate(((q-qhi).reshape(len(rs),9)/q0,(o-ohi).reshape(len(rs),27)/o0),axis=1)
    dh=np.concatenate(((q-qlo).reshape(len(rs),9)/q0,(o-olo).reshape(len(rs),27)/o0),axis=1)
    # Subtraction then division each need their own outward rounding.
    dl=np.concatenate((np.nextafter(q-qhi,-np.inf).reshape(len(rs),9)/q0,
                       np.nextafter(o-ohi,-np.inf).reshape(len(rs),27)/o0),axis=1)
    dh=np.concatenate((np.nextafter(q-qlo,np.inf).reshape(len(rs),9)/q0,
                       np.nextafter(o-olo,np.inf).reshape(len(rs),27)/o0),axis=1)
    return _norm_interval((np.nextafter(dl,-np.inf),np.nextafter(dh,np.inf)))


def _rational_rotation(r):
    x,y,z,w=[Fraction(float(v)) for v in Rotation.from_matrix(r).as_quat()]
    s=w*w+x*x+y*y+z*z
    return np.array([[float(v/s) for v in row] for row in (
        (s-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)),
        (2*(x*y+z*w),s-2*(x*x+z*z),2*(y*z-x*w)),
        (2*(x*z-y*w),2*(y*z+x*w),s-2*(x*x+y*y)))])


def orbit_distance_bounds(Q,O,Qp,Op,q0,o0,rotation_cover) -> DistanceInterval:
    q,o=_tensors(Q,O);p,t=_tensors(Qp,Op)
    if not all(math.isfinite(s) and s>0 for s in (q0,o0)): raise ValueError("positive finite fixed scales")
    convention=content_id({"group":"SO(3)","tensor_metric":"FROBENIUS","q0_K":q0,"o0_K":o0})
    if np.array_equal(q,p) and np.array_equal(o,t):
        return DistanceInterval(0.,0.,"CERTIFIED",convention,"EXACT_IDENTITY_ROTATION",0.,np.eye(3))
    cover=rotation_cover
    if not isinstance(cover,RotationCover) or not len(cover.rotations): raise ValueError("nonempty typed rotation cover")
    rs=finite_array(cover.rotations,ndim=3)
    if rs.shape[1:]!=(3,3) or not np.allclose(rs@rs.transpose(0,2,1),np.eye(3),atol=1e-12,rtol=0) or np.any(np.linalg.det(rs)<0):
        raise ValueError("only proper rotations are allowed")
    def distance(r):
        pr,ot=_rotate(p,t,r)
        return float(np.hypot(np.linalg.norm(q-pr)/q0,np.linalg.norm(o-ot)/o0))
    distances=np.array([distance(r) for r in rs]);idx=int(np.argmin(distances))
    grid=float(distances[idx]);best=grid;witness=rs[idx]
    # Eigenframes and local fits improve only the feasible upper bound.
    _,vq=np.linalg.eigh(q);_,vp=np.linalg.eigh(p)
    starts=[witness]
    for signs in product((-1.,1.),repeat=3):
        r=vq@np.diag(signs)@vp.T
        if np.linalg.det(r)>0: starts.append(r)
    for start in starts:
        fit=minimize(lambda v:distance(Rotation.from_rotvec(v).as_matrix()),
            Rotation.from_matrix(start).as_rotvec(),method="Powell",options={"maxiter":150,"xtol":1e-10,"ftol":1e-12})
        r=Rotation.from_rotvec(fit.x).as_matrix();value=distance(r)
        if math.isfinite(value) and value<best: best=value;witness=r
    certified=False
    try:
        reference=rational_quaternion_cover(int(cover.cover_id.removeprefix("RATIONAL_QUATERNION_CUBE_")))
        certified=np.array_equal(rs,reference.rotations) and cover.radius==reference.radius
    except (ValueError,TypeError): pass
    witness=_rational_rotation(witness)
    witness_lo,witness_hi=_distance_intervals(q,o,p,t,witness[None,:,:],q0,o0)
    upper=float(witness_hi[0]);error=float(witness_hi[0]-witness_lo[0])
    lower=0.
    if certified:
        grid_lo,grid_hi=_distance_intervals(q,o,p,t,rs,q0,o0)
        if float(grid_hi.min())<upper:
            upper=float(grid_hi.min());witness=rs[int(np.argmin(grid_hi))]
        # Enclose both signs before norm; multiplication and division are separately rounded.
        pl=np.nextafter(np.nextafter(2*p.ravel(),-np.inf)/q0,-np.inf)
        ph=np.nextafter(np.nextafter(2*p.ravel(),np.inf)/q0,np.inf)
        tl=np.nextafter(np.nextafter(3*t.ravel(),-np.inf)/o0,-np.inf)
        th=np.nextafter(np.nextafter(3*t.ravel(),np.inf)/o0,np.inf)
        lipschitz=_norm_interval((np.concatenate((pl,tl))[None,:],np.concatenate((ph,th))[None,:]))[1][0]
        lower=max(0.,float(np.nextafter(grid_lo.min()-np.nextafter(lipschitz*cover.radius,np.inf),-np.inf)))
        error=max(error,float(np.max(grid_hi-grid_lo)))
    return DistanceInterval(lower,upper,"CERTIFIED_IEEE_INTERVAL" if certified else "DIAGNOSTIC_APPROXIMATION",
        convention,content_id({"cover":cover.cover_id,"proof":cover.proof,"factor":cover.evaluation_error_factor}),error,witness)


@dataclass(frozen=True)
class ScorePool:
    sample_ids: tuple[str,...]
    scores: tuple[float | None,...]
    score_intervals: tuple[tuple[float,float],...]
    row_status: tuple[str,...]
    k: int
    q0: float
    o0: float
    tolerance: float
    method_id: str


def orbit_pool_scores(records,k,q0,o0,tolerance) -> ScorePool:
    records=tuple(records);n=len(records)-1
    if n<1 or k!=math.ceil(math.sqrt(n)): raise ValueError("registered k=ceil(sqrt(N)) for N other pool rows")
    if q0!=1e-5 or o0!=1e-5: raise ValueError("scale changes require a separately registered sensitivity method")
    if not math.isfinite(tolerance) or tolerance<0: raise ValueError("invalid score tolerance")
    ids=tuple(r.sample_id for r in records)
    if len(set(ids))!=len(ids): raise ValueError("sample IDs must be unique even when rows tie")
    if len({r.frame for r in records})!=1: raise ValueError("one declared frame convention required")
    for record in records: _tensors(record.Q,record.O)
    low=np.full((n+1,n+1),np.inf);high=low.copy()
    cover=rational_quaternion_cover(1)
    method_id="R7_T1_KNN_IDENTITY_THEN_CUBE1_LIMIT1024"
    if n*(n+1)//2>1024:
        # Fixed, pre-observation resource policy: when the complete symmetric
        # pair set exceeds 1024, use an interval-enclosed identity upper bound
        # and zero lower bound for every pair. This still computes a valid SO(3)
        # interval for every row, but generally refuses exact ranks. No row or
        # favorable observed comparison receives a privileged refinement.
        vectors=np.array([np.concatenate((r.Q.ravel()/q0,r.O.ravel()/o0)) for r in records])
        a=vectors[:,None,:];b=vectors[None,:,:]
        lo=np.nextafter(np.nextafter(a,-np.inf)-np.nextafter(b,np.inf),-np.inf)
        hi=np.nextafter(np.nextafter(a,np.inf)-np.nextafter(b,-np.inf),np.inf)
        high=_norm_interval((lo.reshape(-1,36),hi.reshape(-1,36)))[1].reshape(n+1,n+1)
        low=np.zeros_like(high)
        for i in range(n+1):
            for j in range(i):
                if np.array_equal(records[i].Q,records[j].Q) and np.array_equal(records[i].O,records[j].O):high[i,j]=high[j,i]=0.
        np.fill_diagonal(low,np.inf);np.fill_diagonal(high,np.inf)
        lows=np.sort(low,axis=1)[:,k-1];highs=np.sort(high,axis=1)[:,k-1]
        resolved=np.isfinite(highs)&((highs-lows)<=tolerance)
        return ScorePool(ids,tuple(float(h) if ok else None for h,ok in zip(highs,resolved)),tuple(zip(lows.tolist(),highs.tolist())),
            tuple("RESOLVED_INTERVAL" if ok else "NUMERICALLY_UNRESOLVED" for ok in resolved),k,q0,o0,tolerance,method_id)
    for i in range(n+1):
        for j in range(i):
            # Canonical ID orientation fixes the numerical procedure under row permutation.
            a,b=sorted((records[i],records[j]),key=lambda r:r.sample_id)
            try:
                d=orbit_distance_bounds(a.Q,a.O,b.Q,b.O,q0,o0,cover)
                low[i,j]=low[j,i]=d.lower;high[i,j]=high[j,i]=d.upper
            except (ValueError,ArithmeticError):
                low[i,j]=low[j,i]=0.;high[i,j]=high[j,i]=np.inf
    lows=np.sort(low,axis=1)[:,k-1];highs=np.sort(high,axis=1)[:,k-1]
    resolved=np.isfinite(highs)&((highs-lows)<=tolerance)
    return ScorePool(ids,tuple(float(h) if ok else None for h,ok in zip(highs,resolved)),
        tuple(zip(lows.tolist(),highs.tolist())),tuple("RESOLVED_INTERVAL" if ok else "NUMERICALLY_UNRESOLVED" for ok in resolved),
        k,q0,o0,tolerance,method_id)

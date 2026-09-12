"""Exact-dyadic tensor metric enclosures with rational quaternion cells.

Arithmetic is rational except square-root enclosures on a 128/256/512-bit
dyadic grid. SymPy isolates the exact cubic roots, retaining multiplicities.
Certificates concern the computed statistic, not sky measurement uncertainty.
"""
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import heapq
import itertools
import math
import numpy as np
import sympy as sp
from common.r8_contracts import Bound

SCALE=F(1,100000)
METHOD='R8_SO3_INTERVAL_KNN_V1'

def _f(x):
    if isinstance(x,(F,int,np.integer,sp.Rational)):return F(x)
    x=float(x)
    if not math.isfinite(x):raise ValueError('nonfinite tensor input')
    return F(x)

def _sqrt(x,precision=128):
    x=_f(x)
    if x<0:raise ValueError('negative square root')
    denominator=1<<precision
    n=math.isqrt((x.numerator<<(2*precision))//x.denominator)
    lo=F(n,denominator)
    return lo,lo if lo*lo==x else F(n+1,denominator)

def _tensor_key(X):
    q,o=(np.asarray(v,dtype=float) for v in X)
    if q.shape!=(3,3) or o.shape!=(3,3,3) or not np.isfinite(q).all() or not np.isfinite(o).all():
        raise ValueError('finite full Q(3,3),O(3,3,3) required')
    if not np.array_equal(q,q.T):raise ValueError('Q must be symmetric')
    for p in itertools.permutations(range(3)):
        if not np.array_equal(o,o.transpose(p)):raise ValueError('O must be symmetric')
    # Finite extraction rounding is recorded, never projected away. The orbit
    # inequalities apply also to these exact symmetric computed coordinates.
    # Scale before summing/norms so finite large coordinates cannot overflow
    # the extraction-domain guard into an infinite tolerance.
    tol=64*np.finfo(float).eps
    qscale=float(np.max(np.abs(q)));oscale=float(np.max(np.abs(o)))
    qs=q/qscale if qscale else q
    os=o/oscale if oscale else o
    if abs(np.trace(qs))>tol*np.linalg.norm(qs) or np.linalg.norm(np.einsum('iik->k',os))>tol*np.linalg.norm(os):
        raise ValueError('input is outside the declared STF extraction rounding envelope')
    return tuple(map(_f,np.r_[q.ravel(),o.ravel()]))

def _arrays(key):return np.array(key[:9],object).reshape(3,3),np.array(key[9:],object).reshape(3,3,3)

def _hash(key):return hashlib.sha256(str(key).encode()).hexdigest()

def _eigen_intervals(matrix,bits):
    poly=sp.Matrix(matrix.tolist()).charpoly().as_poly()
    values=[]
    for (a,b),multiplicity in poly.intervals(eps=sp.Rational(1,1<<bits)):
        values.extend([(F(a),F(b))]*multiplicity)
    if len(values)!=3:raise ValueError('exact symmetric cubic did not isolate three real roots')
    return tuple(values)

@lru_cache(maxsize=4096)
def _spectra(key,bits):
    q,o=_arrays(key);a=o.reshape(3,9)
    eigq=_eigen_intervals(q,bits);eigo=_eigen_intervals(a@a.T,bits)
    singular=tuple((_sqrt(max(F(0),lo),bits)[0],_sqrt(max(F(0),hi),bits)[1]) for lo,hi in eigo)
    return eigq,singular

def _identity_squared(a,b):return sum((x-y)**2 for x,y in zip(a,b))/SCALE**2

def _invariant(a,b,bits):
    ax=_spectra(a,bits);bx=_spectra(b,bits)
    squared=F(0)
    for group in range(2):
        for (lo,hi),(lop,hip) in zip(ax[group],bx[group]):
            gap=max(F(0),lo-hip,lop-hi)
            squared+=gap*gap/SCALE**2
    return _sqrt(squared,bits)[0]

def invariant_lower(X,Y,precision=128):
    if precision not in (128,256,512):raise ValueError('registered precision must be 128/256/512 bits')
    a=_tensor_key(X);b=_tensor_key(Y)
    lo=_invariant(a,b,precision);hi=_sqrt(_identity_squared(a,b),precision)[1]
    return Bound(lo,hi,{'method':METHOD,'target':tuple(sorted((_hash(a),_hash(b)))),
        'precision':precision,'arithmetic':'EXACT_RATIONAL_WITH_OUTWARD_DYADIC_ROOTS',
        'scope':'COMPUTED_STATISTIC_ONLY','upper_witness':'IDENTITY_SO3'})

def chart_rotation(chart,center):
    if chart not in range(4) or len(center)!=3:raise ValueError('four quaternion charts')
    q=[];j=0
    for i in range(4):
        if i==chart:q.append(F(1))
        else:q.append(_f(center[j]));j+=1
    w,x,y,z=q;d=sum(t*t for t in q)
    return np.array([[w*w+x*x-y*y-z*z,2*(x*y-w*z),2*(x*z+w*y)],
        [2*(x*y+w*z),w*w-x*x+y*y-z*z,2*(y*z-w*x)],
        [2*(x*z-w*y),2*(y*z+w*x),w*w-x*x-y*y+z*z]],dtype=object)/d

def cell_radius(cell,precision=128):
    endpoints=[tuple(map(_f,c)) for c in cell]
    if len(endpoints)!=3 or any(not -1<=lo<=hi<=1 for lo,hi in endpoints):raise ValueError('invalid quaternion cell')
    radius2=sum(((hi-lo)/2)**2 for lo,hi in endpoints)
    minnorm2=1+sum((0 if lo<=0<=hi else min(abs(lo),abs(hi)))**2 for lo,hi in endpoints)
    # 22/7 bounds pi from above; retaining the uncapped radius is also valid.
    return min(F(22,7),_sqrt(4*radius2/minnorm2,precision)[1])

def _rotation_value(a,b,r,bits):
    q,o=_arrays(a);qp,op=_arrays(b)
    qr=r@qp@r.T
    # Three small exact contractions, avoiding 27x27 Cartesian expansion.
    t=np.empty_like(op);u=np.empty_like(op);v=np.empty_like(op)
    for i,j,k in np.ndindex(3,3,3):t[i,j,k]=sum(r[i,l]*op[l,j,k] for l in range(3))
    for i,j,k in np.ndindex(3,3,3):u[i,j,k]=sum(r[j,l]*t[i,l,k] for l in range(3))
    for i,j,k in np.ndindex(3,3,3):v[i,j,k]=sum(r[k,l]*u[i,j,l] for l in range(3))
    square=(sum(x*x for x in (q-qr).flat)+sum(x*x for x in (o-v).flat))/SCALE**2
    return _sqrt(square,bits)

def _lipschitz(a,b,bits):
    q=min(sum(x*x for x in a[:9]),sum(x*x for x in b[:9]))
    o=min(sum(x*x for x in a[9:]),sum(x*x for x in b[9:]))
    return _sqrt((4*q+9*o)/SCALE**2,bits)[1]

def feasible_upper(X, Y, precision=128):
    """Local search proposes an SO(3) witness; exact arithmetic certifies it.

    Optimizer convergence has no lower-bound or statistical authority. Rounding
    a homogeneous quaternion gives another exact proper rotation, so even a
    poor or unfinished optimization supplies a valid feasible upper bound.
    """
    from scipy.optimize import minimize
    from scipy.spatial.transform import Rotation
    a = _tensor_key(X); b = _tensor_key(Y)
    qa, oa = (np.asarray(v, float) for v in _arrays(a))
    qb, ob = (np.asarray(v, float) for v in _arrays(b))
    _, va = np.linalg.eigh(qa); _, vb = np.linalg.eigh(qb)
    starts = [np.eye(3)]
    for signs in itertools.product((-1., 1.), repeat=3):
        r = va @ np.diag(signs) @ vb.T
        if np.linalg.det(r) > 0: starts.append(r)
    def value(v):
        r = Rotation.from_rotvec(v).as_matrix()
        dq = qa-r@qb@r.T
        do = oa-np.einsum('ia,jb,kc,abc->ijk',r,r,r,ob)
        return (np.sum(dq*dq)+np.sum(do*do))*1e10
    start = min(starts, key=lambda r:value(Rotation.from_matrix(r).as_rotvec()))
    v0 = Rotation.from_matrix(start).as_rotvec()
    opt = minimize(value, v0, method='BFGS', options={'maxiter':40, 'gtol':1e-8})
    v = opt.x if np.isfinite(opt.x).all() and value(opt.x) < value(v0) else v0
    xyzw = Rotation.from_rotvec(v).as_quat(); q = np.r_[xyzw[3],xyzw[:3]]
    chart = int(np.argmax(abs(q)))
    center = tuple(F(float(q[j]/q[chart])).limit_denominator(1000000) for j in range(4) if j!=chart)
    rotation = chart_rotation(chart,center)
    lo, hi = _rotation_value(a,b,rotation,precision)
    return Bound(lo,hi,{'scope':'FEASIBLE_VALUE_ONLY','chart':chart,'center':center,
                       'optimizer_success':bool(opt.success),'proper_rotation':'EXACT_RATIONAL_QUATERNION'})


def refine_pair(X,Y,prior,budget):
    if type(budget) is not int or budget<0:raise ValueError('nonnegative integer split budget required')
    a=_tensor_key(X);b=_tensor_key(Y)
    if _hash(a)>_hash(b):a,b=b,a
    target=(_hash(a),_hash(b));bits=128
    if prior is not None:
        if (prior.certificate.get('target')!=target or prior.certificate.get('method')!=METHOD
                or prior.certificate.get('arithmetic')!='EXACT_RATIONAL_WITH_OUTWARD_DYADIC_ROOTS'):
            raise ValueError('prior belongs to another exact pair/method')
        if budget==0:return prior
        lower,upper=prior.lo,prior.hi
    else:
        initial=invariant_lower(_arrays(a),_arrays(b),bits);lower,upper=initial.lo,initial.hi
        witness=feasible_upper(_arrays(a),_arrays(b),bits)
        upper=min(upper,witness.hi)
    inv=_invariant(a,b,bits);L=_lipschitz(a,b,bits)
    cells=[];counter=0
    def add(chart,cell):
        nonlocal upper,counter
        center=tuple((lo+hi)/2 for lo,hi in cell)
        fc,uc=_rotation_value(a,b,chart_rotation(chart,center),bits)
        upper=min(upper,uc)
        bound=max(F(0),inv,fc-L*cell_radius(cell,bits))
        if bound<upper:heapq.heappush(cells,(bound,chart,cell,counter));counter+=1
    if prior is not None and 'cells' in prior.certificate:
        for bound,chart,cell,_ in prior.certificate['cells']:
            if bound<upper:heapq.heappush(cells,(bound,chart,cell,counter));counter+=1
    else:
        for chart in range(4):add(chart,((F(-1),F(1)),)*3)
    splits=0
    while cells and splits<budget:
        bound,chart,cell,_=heapq.heappop(cells)
        if bound>=upper:continue
        axis=max(range(3),key=lambda i:(cell[i][1]-cell[i][0],-i))
        lo,hi=cell[axis];mid=(lo+hi)/2
        for part in ((lo,mid),(mid,hi)):
            child=list(cell);child[axis]=part;add(chart,tuple(child))
        splits+=1
    lower=max(lower,min(upper,cells[0][0]) if cells else upper)
    certificate={'method':METHOD,'target':target,'precision':bits,
        'arithmetic':'EXACT_RATIONAL_WITH_OUTWARD_DYADIC_ROOTS','scope':'COMPUTED_STATISTIC_ONLY',
        'cells':tuple(cells),'splits':splits+(prior.certificate.get('splits',0) if prior else 0)}
    return Bound(lower,upper,certificate)

from dataclasses import dataclass

@dataclass
class PairPool:
    """Complete fixed-target pair enclosure bank; no inference authority."""
    rows: tuple
    sample_ids: tuple
    bounds: np.ndarray
    target_hash: str
    pairs: dict
    splits: int=0
    arithmetic: str='EXACT_ROOT_ISOLATION_AND_IEEE754_OUTWARD_OPERATIONS'


def _float_out(x,direction):
    y=float(x)
    if not math.isfinite(y):raise ValueError('overflow in numeric enclosure')
    return np.nextafter(y,direction) if (F(y)>x if direction<0 else F(y)<x) else y


def initialize_pool(rows,sample_ids):
    """All pairs, cached exact spectra per row and outward basic operations.

    IEEE754 binary64 round-to-nearest basic operations/sqrt are assumed. Each
    basic arithmetic operation is expanded one ulp; exact dyadic reference
    enclosures are used to verify this implementation on the registered pairs.
    """
    rows=tuple(rows);ids=tuple(sample_ids);m=len(rows)
    if m<2 or len(ids)!=m or len(set(ids))!=m:raise ValueError('at least two unique ordered row IDs required')
    keys=tuple(_tensor_key(row) for row in rows)
    spectra=[]
    for key in keys:
        qs,os=_spectra(key,128)
        spectra.append([(_float_out(lo,-np.inf),_float_out(hi,np.inf)) for lo,hi in qs+os])
    spectra=np.asarray(spectra);lower2=np.zeros((m,m));upper2=np.zeros((m,m))
    down=lambda x:np.maximum(0,np.nextafter(x,-np.inf))
    up=lambda x:np.nextafter(x,np.inf)
    for c in range(6):
        gap=np.maximum(0,np.maximum(np.nextafter(spectra[:,c,0,None]-spectra[None,:,c,1],-np.inf),
                                    np.nextafter(spectra[None,:,c,0]-spectra[:,c,1,None],-np.inf)))
        gap=down(gap*100000.)
        lower2=down(lower2+down(gap*gap))
    coordinates=np.asarray(keys,dtype=float)
    for c in range(36):
        # abs of a rounded difference is enclosed after one outward ulp.
        gap=up(np.abs(coordinates[:,c,None]-coordinates[None,:,c]))
        gap=up(gap*100000.)
        upper2=up(upper2+up(gap*gap))
    bounds=np.stack([down(np.sqrt(lower2)),up(np.sqrt(upper2))],axis=-1)
    for i in range(m):bounds[i,i]=0
    if not np.isfinite(bounds).all():raise ValueError('pool arithmetic overflow')
    target=hashlib.sha256(str((METHOD,SCALE,ids,tuple(map(_hash,keys)))).encode()).hexdigest()
    # Snapshot arrays so external mutation cannot silently change the target.
    snapshots=[]
    for key in keys:
        q,o=_arrays(key)
        q.setflags(write=False);o.setflags(write=False);snapshots.append((q,o))
    return PairPool(tuple(snapshots),ids,bounds,target,{})


def refine_pool(pool,observed=0,split_budget=1000000,seconds=60.):
    """One checkpoint of fixed-statistic refinement; preserves every row.

    The order prioritizes kth-relevant pairs for ambiguous reference/observed
    comparisons, then the smallest current lower bound and stable row IDs.
    No score or p-value is computed here; that belongs to HTT.
    """
    import time
    if not isinstance(pool,PairPool) or type(split_budget) is not int or not 0<=split_budget<=1000000:
        raise ValueError('registered per-checkpoint split budget required')
    if not 0<=seconds<=60:raise ValueError('checkpoint must be at most 60 seconds')
    m=len(pool.rows);k=math.ceil(math.sqrt(m-1))
    if not 0<=observed<m:raise ValueError('observed row outside fixed pool')
    start=time.monotonic();used=0
    while used<split_budget and time.monotonic()-start<seconds:
        masked=pool.bounds.copy();masked[np.arange(m),np.arange(m)]=np.inf
        scores=np.partition(masked,k-1,axis=1)[:,k-1,:]
        obs=scores[observed]
        ambiguous=[i for i,(lo,hi) in enumerate(scores) if i!=observed and hi>=obs[0] and lo<obs[1]]
        if not ambiguous:break
        candidates=set()
        for i in [observed,*ambiguous]:
            lo,hi=scores[i]
            for j in range(m):
                a,b=pool.bounds[i,j]
                if i!=j and a<=hi and b>=lo and a<b:candidates.add(tuple(sorted((i,j))))
        if not candidates:break
        # Round-robin split counts prevent broad invariant ties starving pairs.
        i,j=min(candidates,key=lambda ij:(pool.pairs.get(ij,Bound(0,0)).certificate.get('splits',0),
            pool.bounds[ij][0],pool.sample_ids[ij[0]],pool.sample_ids[ij[1]]))
        prior=pool.pairs.get((i,j));chunk=min(8,split_budget-used)
        bound=refine_pair(pool.rows[i],pool.rows[j],prior,chunk)
        before=prior.certificate.get('splits',0) if prior else 0
        consumed=bound.certificate['splits']-before
        pool.pairs[(i,j)]=bound
        lo=max(pool.bounds[i,j,0],_float_out(bound.lo,-np.inf))
        hi=min(pool.bounds[i,j,1],_float_out(bound.hi,np.inf))
        pool.bounds[i,j]=pool.bounds[j,i]=(lo,hi)
        used+=consumed;pool.splits+=consumed
        if consumed==0 and lo<hi:break
    return {'target_hash':pool.target_hash,'new_splits':used,'total_splits':pool.splits,
            'elapsed_seconds':time.monotonic()-start,'all_rows_retained':len(pool.sample_ids),
            'stopping_reason':'CHECKPOINT_RESOURCE_OR_ORDER_RESOLUTION','inferential_eligibility':False}


def _checkpoint_encode(value):
    if isinstance(value,F):return {'fraction':[value.numerator,value.denominator]}
    if isinstance(value,tuple):return {'tuple':[_checkpoint_encode(v) for v in value]}
    if isinstance(value,list):return [_checkpoint_encode(v) for v in value]
    if isinstance(value,dict):return {k:_checkpoint_encode(v) for k,v in value.items()}
    return value


def _checkpoint_decode(value):
    if isinstance(value,list):return [_checkpoint_decode(v) for v in value]
    if isinstance(value,dict):
        if set(value)=={'fraction'}:return F(*value['fraction'])
        if set(value)=={'tuple'}:return tuple(_checkpoint_decode(v) for v in value['tuple'])
        return {k:_checkpoint_decode(v) for k,v in value.items()}
    return value


def restore_pool(rows, sample_ids, bounds, expected_target, splits=0):
    """Import a trusted saved enclosure bank without repeating root isolation.

    Legacy banks lack search trees. Preserve their bounds and cumulative work;
    newly visited pairs start new trees. Never call this a recovered old tree.
    """
    keys=tuple(_tensor_key(row) for row in rows);ids=tuple(sample_ids);m=len(keys)
    if m<2 or len(ids)!=m or len(set(ids))!=m:raise ValueError('invalid pool rows')
    target=hashlib.sha256(str((METHOD,SCALE,ids,tuple(map(_hash,keys)))).encode()).hexdigest()
    if target!=expected_target:raise ValueError('checkpoint target mismatch')
    bank=np.array(bounds,float,copy=True)
    if (bank.shape!=(m,m,2) or not np.isfinite(bank).all() or np.any(bank[:,:,0]<0)
        or np.any(bank[:,:,0]>bank[:,:,1]) or not np.array_equal(bank,bank.transpose(1,0,2))
        or np.any(bank[np.arange(m),np.arange(m)]!=0)):
        raise ValueError('invalid checkpoint enclosure bank')
    snapshots=[]
    for key in keys:
        q,o=_arrays(key);q.setflags(write=False);o.setflags(write=False);snapshots.append((q,o))
    return PairPool(tuple(snapshots),ids,bank,target,{},int(splits))


def save_pool(pool, path, accounting=None):
    """Persist exact pair trees and numeric bank as an atomic bound checkpoint."""
    import json
    from pathlib import Path
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    data=path.with_suffix('.npz');temporary=data.with_suffix('.npz.tmp')
    with temporary.open('wb') as stream:
        np.savez_compressed(stream,Q=np.asarray([r[0] for r in pool.rows],float),
                            O=np.asarray([r[1] for r in pool.rows],float),
                            bounds=pool.bounds,sample_ids=pool.sample_ids)
    temporary.replace(data)
    metadata={'schema':'R8_PAIR_POOL_V2','method':METHOD,'target_hash':pool.target_hash,
              'data_file':data.name,'data_sha256':hashlib.sha256(data.read_bytes()).hexdigest(),
              'splits':pool.splits,'accounting':accounting or {},
              'pairs':[[list(ij),_checkpoint_encode((b.lo,b.hi,b.certificate))] for ij,b in sorted(pool.pairs.items())]}
    temporary=path.with_suffix('.json.tmp');temporary.write_text(json.dumps(metadata,indent=2)+'\n');temporary.replace(path)


def load_pool(path):
    import json
    from pathlib import Path
    path=Path(path);metadata=json.loads(path.read_text())
    if metadata['schema']!='R8_PAIR_POOL_V2' or metadata['method']!=METHOD:raise ValueError('checkpoint method mismatch')
    data=path.parent/metadata['data_file']
    if hashlib.sha256(data.read_bytes()).hexdigest()!=metadata['data_sha256']:raise ValueError('checkpoint bank bytes changed')
    with np.load(data,allow_pickle=False) as z:
        pool=restore_pool(zip(z['Q'],z['O']),tuple(z['sample_ids'].tolist()),z['bounds'],metadata['target_hash'],metadata['splits'])
    for ij,encoded in metadata['pairs']:
        lo,hi,certificate=_checkpoint_decode(encoded);i,j=ij
        target=tuple(sorted((_hash(_tensor_key(pool.rows[i])),_hash(_tensor_key(pool.rows[j])))))
        if certificate['target']!=target or certificate['method']!=METHOD:raise ValueError('checkpoint pair target mismatch')
        pool.pairs[(i,j)]=Bound(lo,hi,certificate)
    return pool,metadata['accounting']

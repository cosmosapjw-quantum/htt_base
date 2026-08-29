"""Bounded carrier-domain method-power primitives for PMG-WU-008.

The input convention is (a_l0, Re a_l1, Im a_l1, ..., Re a_ll,
Im a_ll), NOT sqrt(2)-rescaled real coefficients. In this convention
integral T_l^2 dOmega = a_l0^2 + 2 sum_{m>0}|a_lm|^2.
These analytic templates are not physical shear or Bianchi templates.
"""
from __future__ import annotations
from dataclasses import dataclass
from functools import lru_cache
import hashlib
import math
from typing import Sequence
import numpy as np
from scipy.special import sph_harm_y

LEGACY = 'LEGACY_ABSOLUTE_MEDIAN_V1'
ECDF = 'LOO_ECDF_MIDRANK_V1'
COMBINERS = (
    'MIN_LOCAL_P_V1',
    'EXACT_INTEGER_FISHER_PRODUCT_FINITE_POOL_V1',
)
AMPLITUDES = (0., .25, .5, 1., 2., 4., 8.)
ORIENTATION_SEED = 'PMG-WU-008:20260829'
ORIENTATION_COUNT = 32
CALIBRATION_COUNT = 200
TEMPLATE_SEEDS = (
    ('Q_AXIAL', (1,0,0,0,0), (0,0,0,0,0,0,0)),
    ('O_PLANAR', (0,0,0,0,0), (0,0,0,0,0,1,0)),
    ('MIX_AXIAL', (1,0,0,0,0), (1,0,0,0,0,0,0)),
    ('MIX_PLANAR', (0,0,0,1,0), (0,0,0,0,0,1,0)),
    ('MIX_GENERIC', (1,2,-1,1,3), (2,-1,3,1,-2,2,1)),
)


def metric(ell: int) -> np.ndarray:
    if type(ell) is not int or not 2 <= ell <= 5:
        raise ValueError('only registered ell=2..5 blocks are supported')
    return np.array([1.] + [2.]*(2*ell))


def _finite(value: object, *, ndim: int | None = None) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind not in 'iuf' or raw.dtype.kind == 'b':
        raise ValueError('finite real numeric array required')
    out = np.asarray(raw, dtype=np.float64)
    if (ndim is not None and out.ndim != ndim) or not np.all(np.isfinite(out)):
        raise ValueError('finite numeric array with registered dimension required')
    return out


def harmonic_energy(components: object) -> float:
    x = _finite(components, ndim=1)
    if x.shape != (32,):
        raise ValueError('a complete 32-component harmonic carrier is required')
    weights = np.concatenate([metric(ell) for ell in range(2,6)])
    return float(np.dot(weights, x*x))


@dataclass(frozen=True)
class AlgebraicHarmonicTemplate:
    template_id: str
    coefficients: np.ndarray
    domain: str = 'POST_ESTIMATOR_CARRIER_NOT_PHYSICAL'

    def __post_init__(self) -> None:
        x = _finite(self.coefficients, ndim=1)
        if x.shape != (32,) or np.any(x[12:] != 0):
            raise ValueError('template must have only ell2/ell3 support in length32')
        if self.domain != 'POST_ESTIMATOR_CARRIER_NOT_PHYSICAL':
            raise ValueError('algebraic template cannot acquire a physical label')
        if not isinstance(self.template_id,str) or not self.template_id:
            raise ValueError('template ID required')
        if not math.isclose(harmonic_energy(x), 1., rel_tol=0., abs_tol=5e-14):
            raise ValueError('template must have unit harmonic energy')
        # Immutable bytes, not only setflags(False): writeability cannot be re-enabled.
        sealed = np.frombuffer(x.astype('<f8').tobytes(), dtype='<f8')
        object.__setattr__(self,'coefficients',sealed)


def template_bank() -> tuple[AlgebraicHarmonicTemplate,...]:
    output=[]
    for name,q,o in TEMPLATE_SEEDS:
        blocks=[np.array(q,dtype=float),np.array(o,dtype=float)]
        nonzero=sum(bool(np.any(b)) for b in blocks)
        result=np.zeros(32)
        for ell,block,start in zip((2,3),blocks,(0,5),strict=True):
            energy=float(np.dot(metric(ell),block*block))
            if energy:
                result[start:start+len(block)]=block/math.sqrt(nonzero*energy)
        output.append(AlgebraicHarmonicTemplate(name,result))
    return tuple(output)


def _proper_rotation(value: object) -> np.ndarray:
    r=_finite(value,ndim=2)
    if r.shape!=(3,3) or not np.allclose(r@r.T,np.eye(3),rtol=0,atol=5e-13) or not math.isclose(float(np.linalg.det(r)),1.,rel_tol=0,abs_tol=5e-13):
        raise ValueError('proper SO(3) rotation required; no reflection or rescaling')
    return r


def orientation_uniforms() -> np.ndarray:
    out=np.empty((ORIENTATION_COUNT,3))
    for i in range(ORIENTATION_COUNT):
        for j in range(3):
            message=f'{ORIENTATION_SEED}:{i}:{j}'.encode('ascii')
            integer=int.from_bytes(hashlib.sha256(message).digest()[:8],'big') >> 12
            out[i,j]=(integer+.5)/(2**52)
    return out


def orientation_bank() -> np.ndarray:
    """Fixed 32-point pseudorandom equal-weight SO(3) cubature, not an exact design.

    Three hash-derived open-unit-interval coordinates parameterize a uniform
    unit quaternion. The 16/32 prefix discrepancy is reported, not claimed to
    certify Haar-integral convergence.
    """
    output=[]
    for u,v,w in orientation_uniforms():
        x=math.sqrt(1-u)*math.sin(2*math.pi*v)
        y=math.sqrt(1-u)*math.cos(2*math.pi*v)
        z=math.sqrt(u)*math.sin(2*math.pi*w)
        t=math.sqrt(u)*math.cos(2*math.pi*w)
        r=np.array([
            [1-2*(y*y+z*z),2*(x*y-z*t),2*(x*z+y*t)],
            [2*(x*y+z*t),1-2*(x*x+z*z),2*(y*z-x*t)],
            [2*(x*z-y*t),2*(y*z+x*t),1-2*(x*x+y*y)],
        ])
        output.append(_proper_rotation(r))
    return np.asarray(output)


def real_basis(ell: int, directions: object) -> np.ndarray:
    points=_finite(directions,ndim=2)
    if points.shape[1:]!=(3,) or not np.allclose(np.linalg.norm(points,axis=1),1.,atol=1e-12,rtol=0):
        raise ValueError('unit Cartesian directions required')
    theta=np.arccos(np.clip(points[:,2],-1,1));phi=np.arctan2(points[:,1],points[:,0])%(2*math.pi)
    cols=[sph_harm_y(ell,0,theta,phi).real]
    for m in range(1,ell+1):
        y=sph_harm_y(ell,m,theta,phi)
        cols.extend((2*y.real,-2*y.imag))
    return np.column_stack(cols)


@lru_cache(maxsize=4)
def _sphere_rule(ell: int) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    # Products of two l<=3 harmonics are integrated with ample polynomial/
    # Fourier order. This quadrature is only a basis-rotation construction.
    z,w=np.polynomial.legendre.leggauss(8)
    phi=2*math.pi*np.arange(16)/16
    points=np.stack((np.sqrt(1-z*z)[:,None]*np.cos(phi),np.sqrt(1-z*z)[:,None]*np.sin(phi),np.broadcast_to(z[:,None],(8,16))),axis=-1).reshape(-1,3)
    weights=np.repeat(w,16)*(2*math.pi/16)
    return points,weights,real_basis(ell,points)


def rotation_matrix(ell: int, rotation: object) -> np.ndarray:
    if ell not in (2,3):
        raise ValueError('template rotation supports exactly ell=2,3')
    r=_proper_rotation(rotation)
    points,weights,basis=_sphere_rule(ell)
    # Active rotation: f_R(n)=f(R^-1 n); row directions transform n @ R.
    d=(basis.T@(weights[:,None]*real_basis(ell,points@r)))/metric(ell)[:,None]
    g=np.diag(metric(ell))
    if not np.allclose(d.T@g@d,g,rtol=0,atol=5e-13):
        raise ValueError('harmonic rotation failed the weighted metric invariant')
    return d


def rotate_template(template: AlgebraicHarmonicTemplate, rotation: object) -> np.ndarray:
    if type(template) is not AlgebraicHarmonicTemplate:
        raise TypeError('only exact algebraic template type is accepted')
    r=_proper_rotation(rotation)
    out=np.zeros(32)
    out[:5]=rotation_matrix(2,r)@template.coefficients[:5]
    out[5:12]=rotation_matrix(3,r)@template.coefficients[5:12]
    return out


def inject(rows: object, template: AlgebraicHarmonicTemplate, rotation: object, amplitude: float, scale_rms: float) -> np.ndarray:
    x=_finite(rows,ndim=2)
    if x.shape[1:]!=(32,):raise ValueError('injection is harmonic-level, never feature-level')
    if isinstance(amplitude,bool) or not math.isfinite(amplitude) or amplitude<0:
        raise ValueError('amplitude must be finite and nonnegative')
    if isinstance(scale_rms,bool) or not math.isfinite(scale_rms) or scale_rms<=0:
        raise ValueError('positive reference-only RMS required')
    if type(template) is not AlgebraicHarmonicTemplate:raise TypeError('exact template type required')
    _proper_rotation(rotation)
    if amplitude==0:return x.copy()
    delta=amplitude*scale_rms*math.sqrt(4*math.pi)*rotate_template(template,rotation)
    out=x.copy();out[:,:12]+=delta[:12]
    if not np.all(np.isfinite(out)):raise ValueError('injection overflow')
    return out


def reference_scale(reference_carriers: object) -> float:
    x=_finite(reference_carriers,ndim=2)
    if x.shape!=(CALIBRATION_COUNT,32):raise ValueError('exact 200 calibration carriers required')
    g=np.r_[metric(2),metric(3)]
    scale=float(np.median(np.sqrt(np.sum(x[:,:12]**2*g,axis=1)/(4*math.pi))))
    if not math.isfinite(scale) or scale<=0:raise ValueError('nonpositive reference RMS')
    return scale


def split_indices(source_ids: Sequence[str], arm: str) -> tuple[np.ndarray,np.ndarray]:
    if arm=='paired300':expected=tuple(f'{i:05d}' for i in range(300))
    elif arm=='cmbonly999':expected=tuple(f'{i:05d}' for i in range(1000) if i!=970)
    else:raise ValueError('unknown noise/null arm')
    if tuple(source_ids)!=expected:raise ValueError('exact null inventory/order required; no observation allowed')
    return np.arange(200),np.arange(200,len(expected))


def _tie_positions(x: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    """Return number below, last tied index, inverse sort, and sorted values."""
    n=x.shape[1]
    order=np.argsort(x,axis=1,kind='stable');s=np.take_along_axis(x,order,axis=1)
    pos=np.broadcast_to(np.arange(n)[None,:,None],x.shape)
    firstchange=np.ones(x.shape,dtype=bool);firstchange[:,1:]=s[:,1:]!=s[:,:-1]
    lastchange=np.ones(x.shape,dtype=bool);lastchange[:,:-1]=s[:,:-1]!=s[:,1:]
    first=np.maximum.accumulate(np.where(firstchange,pos,0),axis=1)
    last=np.minimum.accumulate(np.where(lastchange,pos,n-1)[:,::-1],axis=1)[:,::-1]
    lo=np.empty_like(order);hi=np.empty_like(order);inverse=np.empty_like(order)
    np.put_along_axis(lo,order,first,axis=1);np.put_along_axis(hi,order,last,axis=1)
    np.put_along_axis(inverse,order,pos,axis=1)
    return lo,hi,inverse,s


def local_numerators(pools: object, tails: Sequence[str], reducer: str) -> np.ndarray:
    x=_finite(pools,ndim=3)
    b,n,p=x.shape
    if b<1 or n<2 or p<1:raise ValueError('nonempty batches with at least two rows required')
    if len(tails)!=p or any(t not in ('two-sided','upper','lower') for t in tails):raise ValueError('registered tail per coordinate required')
    if reducer not in (LEGACY,ECDF):raise ValueError('unknown reducer')
    lo,hi,pos,s=_tie_positions(x)
    if reducer==ECDF:
        twice=lo+hi  # 2*less + equal_including_self - 1
        score=np.empty(x.shape,dtype=np.int64)
        for j,tail in enumerate(tails):
            score[:,:,j]=abs(twice[:,:,j]-(n-1)) if tail=='two-sided' else twice[:,:,j] if tail=='upper' else 2*(n-1)-twice[:,:,j]
    else:
        k0=(n-2)//2;k1=(n-1)//2
        v0=np.take_along_axis(s,k0+(pos<=k0),axis=1)
        v1=np.take_along_axis(s,k1+(pos<=k1),axis=1)
        median=(v0+v1)/2
        score=np.empty_like(x)
        for j,tail in enumerate(tails):
            score[:,:,j]=abs(x[:,:,j]-median[:,:,j]) if tail=='two-sided' else x[:,:,j] if tail=='upper' else -x[:,:,j]
    if not np.all(np.isfinite(score)):raise ValueError('score arithmetic overflow')
    below,_,_,_=_tie_positions(score)
    return n-below


def family_numerators(local_counts: object, query_index: int) -> np.ndarray:
    """Return min-p and finite-calibrated Fisher-product outer counts.

    Products are arbitrary precision integers. No chi-square approximation,
    coordinate independence assumption, floating log tie test, or N+1 fudge.
    """
    k=np.asarray(local_counts)
    if k.ndim!=3 or k.dtype.kind not in 'iu' or k.shape[1]<2 or k.shape[2]<1:
        raise ValueError('3D integral local counts required')
    n=k.shape[1]
    if type(query_index) is not int or not 0<=query_index<n or np.any(k<1) or np.any(k>n):
        raise ValueError('query index or local count outside finite pool')
    mins=k.min(axis=2)
    products=np.prod(k.astype(object),axis=2)
    return np.column_stack((np.sum(mins<=mins[:,query_index,None],axis=1),np.sum(products<=products[:,query_index,None],axis=1))).astype(np.int64)


def score_queries(reference: object, queries: object, tails: Sequence[str], reducer: str) -> np.ndarray:
    ref=_finite(reference,ndim=2);q=_finite(queries,ndim=2)
    if ref.shape[1]!=q.shape[1] or ref.shape[0]<1:raise ValueError('reference/query dimensions differ')
    pools=np.concatenate((q[:,None,:],np.broadcast_to(ref,(len(q),*ref.shape))),axis=1)
    return family_numerators(local_numerators(pools,tails,reducer),0)


def _wilson(k: int,n: int) -> tuple[float,float]:
    z=1.959963984540054;p=k/n;den=1+z*z/n
    center=(p+z*z/(2*n))/den
    half=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return max(0.,center-half),min(1.,center+half)


def summarize_decisions(decisions: object) -> dict[str,object]:
    x=np.asarray(decisions,dtype=float)
    if x.ndim!=2 or x.shape[0]<2 or x.shape[1]<1 or np.any(~(np.isnan(x)|(x==0)|(x==1))):
        raise ValueError('sky x orientation decisions must be 0,1,or typed-absence NaN')
    missing=np.isnan(x);low=np.where(missing,0.,x);high=np.where(missing,1.,x)
    n,r=x.shape;per_sky=low.mean(axis=1);complete=not bool(missing.any())
    per_orientation=[]
    for j in range(r):
        valid=~missing[:,j];k=int(np.nansum(x[:,j]));nv=int(valid.sum())
        per_orientation.append({'rejections':k,'undefined':n-nv,'denominator':n,
            'power':k/n if nv==n else None,
            'wilson95':list(_wilson(k,n)) if nv==n else None})
    return {
        'independent_sky_count':n,'orientation_count':r,'total_sky_orientation_trials':n*r,
        'undefined_trials':int(missing.sum()),'power':float(x.mean()) if complete else None,
        'power_lower':float(low.mean()),'power_upper':float(high.mean()),
        'conditional_sky_se':float(np.std(per_sky,ddof=1)/math.sqrt(n)) if complete else None,
        'orientation_prefix_difference':float(low[:,:r//2].mean()-low.mean()) if complete and r>1 else None,
        'per_orientation':per_orientation,
        'uncertainty_scope':'conditional on this fixed calibration set and iid simulation skies; rotations and amplitudes are paired, not independent trials',
    }


def threshold_crossings(amplitudes: Sequence[float], powers: Sequence[float|None], target: float) -> dict[str,object]:
    a=np.asarray(amplitudes,dtype=float)
    if len(a)!=len(powers) or len(a)<2 or np.any(np.diff(a)<=0) or not 0<target<1:
        raise ValueError('ordered amplitude grid and interior power target required')
    if any(p is None for p in powers):return {'status':'UNRESOLVED_TYPED_ABSENCE','crossings':[],'monotonic_non_decreasing':None}
    p=np.asarray(powers,dtype=float)
    if np.any(~np.isfinite(p)) or np.any((p<0)|(p>1)):raise ValueError('invalid power')
    cross=[]
    for i in range(1,len(a)):
        if (p[i-1]<target<=p[i]) or (p[i-1]>=target>p[i]):
            cross.append({'amplitude_bracket':[float(a[i-1]),float(a[i])],'direction':'up' if p[i]>=target else 'down'})
    return {'status':'GRID_CROSSINGS' if cross else 'ALREADY_ABOVE_AT_ZERO' if p[0]>=target else 'NOT_REACHED_ON_GRID',
        'target_power':target,'crossings':cross,'monotonic_non_decreasing':bool(np.all(np.diff(p)>=0)),
        'interpolation_or_extrapolation_performed':False}


def evaluate_cell(reference_features: dict[str,np.ndarray], baseline_carriers: object,
                  template: AlgebraicHarmonicTemplate, amplitude: float, scale_rms: float,
                  extractor, family_tails: dict[str,tuple[str,...]], *, batch_size: int=32
                  ) -> tuple[np.ndarray,list[dict[str,object]]]:
    """Evaluate one predeclared template/amplitude cell, never observed data.

    extractor(row) returns (feature mapping, typed absence mapping). Unhandled
    exceptions abort; an absent registered statistic is retained as -1 and
    contributes bounds rather than being silently removed from the denominator.
    """
    base=_finite(baseline_carriers,ndim=2)
    if base.shape[1:]!=(32,) or len(base)<2:raise ValueError('held-out harmonic skies required')
    families=tuple(family_tails)
    if set(reference_features)!=set(families) or type(batch_size) is not int or batch_size<1:
        raise ValueError('registered reference/family/batch contract required')
    ref={f:_finite(reference_features[f],ndim=2) for f in families}
    nref=len(ref[families[0]])
    if any(ref[f].shape!=(nref,len(family_tails[f])) for f in families):
        raise ValueError('reference feature shapes differ')
    rotations=orientation_bank()[:1] if amplitude==0 else orientation_bank()
    ranks=np.full((len(base),len(rotations),len(families),2,2),-1,dtype=np.int32)
    absent=[]
    for r_index,rotation in enumerate(rotations):
        injected=inject(base,template,rotation,amplitude,scale_rms)
        for start in range(0,len(base),batch_size):
            end=min(start+batch_size,len(base));values={f:[] for f in families};positions={f:[] for f in families}
            for i in range(start,end):
                row_features,row_absence=extractor(injected[i])
                if set(row_features)|set(row_absence)!=set(families) or set(row_features)&set(row_absence):
                    raise ValueError('extractor must assign each family exactly once')
                for f in families:
                    if f in row_absence:
                        absent.append({'trial_index':i,'orientation_index':r_index,'family':f,'reason':str(row_absence[f])})
                    else:
                        value=_finite(row_features[f],ndim=1)
                        if value.shape!=(len(family_tails[f]),):raise ValueError('extracted feature dimension drift')
                        values[f].append(value);positions[f].append(i)
            for f_index,f in enumerate(families):
                if not positions[f]:continue
                for red_index,reducer in enumerate((LEGACY,ECDF)):
                    ranks[positions[f],r_index,f_index,red_index,:]=score_queries(ref[f],np.asarray(values[f]),family_tails[f],reducer)
    return ranks,absent

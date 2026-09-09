"""Amplitude-preserving rank2/3 multipole vectors and reconstruction error.

Floating null-cone roots propose a representation. The exact dyadic norm of
its returned tensor's discrepancy bounds the conversion; root failure never
replaces or removes the original tensor. This is not a root-isolation proof.
"""
from __future__ import annotations
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import permutations,product,combinations_with_replacement
import hashlib
import math
import numpy as np
from common.r8_contracts import Bound

METHOD='R8_FULL_MV_NULL_CONE_V1'


@dataclass(frozen=True)
class MVResult:
    amplitude: float | None
    vectors: np.ndarray | None
    l: int
    reconstruction_enclosure: Bound | None
    status: str
    original_tensor: np.ndarray
    certificate: dict


def mv_to_tensor(amplitude,vectors,l):
    if l not in (2,3):raise ValueError('only STF rank2 and rank3 supported')
    amplitude=float(amplitude)
    if amplitude==0 and vectors is None:return np.zeros((3,)*l)
    v=np.asarray(vectors,dtype=float)
    if not math.isfinite(amplitude) or v.shape!=(l,3) or not np.isfinite(v).all():
        raise ValueError('finite amplitude and l three-vectors required')
    if not np.allclose(np.linalg.norm(v,axis=1),1.,atol=1e-12,rtol=0):
        raise ValueError('unit vectors required; normalization must preserve amplitude explicitly')
    raw=np.ones((3,)*l)
    for i in range(l):
        shape=[1]*l;shape[i]=3;raw*=v[i].reshape(shape)
    sym=sum(raw.transpose(order) for order in permutations(range(l)))/math.factorial(l)
    # Assign each symmetric orbit from one stored value: downstream tensors
    # require bitwise index symmetry, not only an allclose witness.
    for indices in combinations_with_replacement(range(3),l):
        value=sym[indices]
        for index in set(permutations(indices)):sym[index]=value
    if l==2:sym-=np.eye(3)*np.trace(sym)/3
    else:
        trace=np.einsum('iik->k',sym);eye=np.eye(3)
        sym-=(np.einsum('ij,k->ijk',eye,trace)+np.einsum('ik,j->ijk',eye,trace)+np.einsum('jk,i->ijk',eye,trace))/5
    for indices in combinations_with_replacement(range(3),l):
        value=sym[indices]
        for index in set(permutations(indices)):sym[index]=value
    result=amplitude*sym
    if not np.isfinite(result).all():raise ValueError('tensor reconstruction overflow')
    return result


def _error_bound(t,restored):
    # Bound the actual returned arrays, not a residual evaluated in float.
    squared=sum((F(float(x))-F(float(y)))**2 for x,y in zip(t.flat,restored.flat))
    denominator=1<<256
    n=math.isqrt((squared.numerator<<512)//squared.denominator)
    lo=F(n,denominator);hi=lo if lo*lo==squared else F(n+1,denominator)
    return Bound(lo,hi,{'kind':'EXACT_DYADIC_RECONSTRUCTION_FROBENIUS','squared':str(squared),
        'input_sha256':hashlib.sha256(np.asarray(t,dtype='<f8').tobytes()).hexdigest(),
        'returned_tensor_sha256':hashlib.sha256(np.asarray(restored,dtype='<f8').tobytes()).hexdigest(),
        'scope':'finite represented arrays; not a root isolation or measurement uncertainty certificate'})


def _rotate(t,r,l):
    return np.einsum('ia,jb,ab->ij',r,r,t) if l==2 else np.einsum('ia,jb,kc,abc->ijk',r,r,r,t)


def _polynomial(t,l):
    n=(np.array([1,0,-1],complex),np.array([1j,0,1j]),np.array([0,2,0],complex))
    c=np.zeros(2*l+1,complex)
    for indices in product(range(3),repeat=l):
        term=np.array([1.],complex)
        for i in indices:term=np.convolve(term,n[i])
        c+=t[indices]*term
    return c


def _stereo(z):
    # Scale the homogeneous formula to avoid overflow for a large finite root.
    a=max(1.,abs(z));x=z.real/a;y=z.imag/a;w=1/a;den=x*x+y*y+w*w
    return np.array([2*x*w,2*y*w,x*x+y*y-w*w])/den


def tensor_to_mv(tensor,l):
    if l not in (2,3):raise ValueError('only STF rank2 and rank3 supported')
    t=np.array(tensor,dtype=float,copy=True)
    if t.shape!=(3,)*l or not np.isfinite(t).all():raise ValueError('finite rank-l Cartesian tensor required')
    scale=float(np.max(abs(t)))
    cert={'method_id':METHOD,'root_method':'floating polynomial roots plus antipodal pairing',
          'root_isolation':'NOT_CERTIFIED','multiple_root_policy':'refuse close repeated roots; original tensor retained',
          'stf_input_tolerance_relative':1e-10,'root_pair_tolerance':1e-6,'root_separation_floor':1e-4}
    def refusal(status):return MVResult(None,None,l,None,status,t,dict(cert))
    if scale==0:return MVResult(0.,None,l,Bound(F(0),F(0),{'kind':'EXACT_ZERO'}),'ZERO_AMPLITUDE_DIRECTIONS_UNIDENTIFIED',t,cert)
    scaled=t/scale
    if any(np.max(abs(scaled-scaled.transpose(p)))>1e-10 for p in permutations(range(l))) or np.max(abs(np.trace(scaled,axis1=0,axis2=1)))>1e-10:
        raise ValueError('STF tensor required within declared input tolerance')
    # Choose among fixed proper frames for a well-sized leading coefficient.
    # No observed-dependent statistic choice: every successful conversion is
    # checked against the unchanged original tensor.
    frames=[np.eye(3),np.roll(np.eye(3),1,axis=0),np.roll(np.eye(3),2,axis=0),
        np.array([[-2,2,1],[2,1,2],[1,2,-2]],float)/3]
    options=[(_polynomial(_rotate(scaled,r,l),l),r) for r in frames]
    c,r=max(options,key=lambda cr:abs(cr[0][-1]))
    if abs(c[-1])<=1e-12*np.max(abs(c)):return refusal('POLYNOMIAL_CHART_UNRESOLVED')
    try:roots=np.polynomial.polynomial.polyroots(c)
    except np.linalg.LinAlgError:return refusal('ROOT_SOLVER_UNRESOLVED')
    if len(roots)!=2*l or not np.isfinite(roots).all():return refusal('ROOT_SOLVER_UNRESOLVED')
    axes=np.array([_stereo(z) for z in roots])
    separation=min(np.linalg.norm(axes[i]-axes[j]) for i in range(2*l) for j in range(i))
    cert['minimum_root_chord_separation']=float(separation)
    if separation<1e-4:return refusal('MULTIPLE_ROOT_UNRESOLVED')
    remaining=list(range(2*l));vectors=[];pair_errors=[]
    while remaining:
        i=remaining.pop(0);j=min(remaining,key=lambda j:np.linalg.norm(axes[i]+axes[j]))
        error=float(np.linalg.norm(axes[i]+axes[j]));pair_errors.append(error)
        if error>1e-6:return refusal('ANTIPODAL_PAIR_UNRESOLVED')
        remaining.remove(j);v=axes[i]-axes[j];v/=np.linalg.norm(v);v=r.T@v;v/=np.linalg.norm(v)
        if v[np.argmax(abs(v))]<0:v=-v
        vectors.append(v)
    vectors=np.array(sorted(vectors,key=lambda v:tuple(v)))
    unit=mv_to_tensor(1.,vectors,l)
    amplitude=float(np.sum(scaled*unit)/np.sum(unit*unit))*scale
    if not math.isfinite(amplitude):return refusal('RECONSTRUCTION_UNRESOLVED')
    try:restored=mv_to_tensor(amplitude,vectors,l)
    except ValueError:return refusal('RECONSTRUCTION_UNRESOLVED')
    enclosure=_error_bound(t,restored)
    cert.update(maximum_pair_error=max(pair_errors),reconstruction_relative_error_upper=float(enclosure.hi)/scale)
    if float(enclosure.hi)/scale>1e-8:return refusal('RECONSTRUCTION_UNRESOLVED')
    return MVResult(amplitude,vectors,l,enclosure,'RECONSTRUCTED_WITH_ERROR_BOUND',t,cert)

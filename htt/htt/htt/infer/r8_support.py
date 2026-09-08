"""Structural factor Gaussian support; no rank inferred from floating zeros."""
from dataclasses import dataclass
from fractions import Fraction
import math
import numpy as np
import sympy as sp
from common.r8_contracts import RegionMembership as R

def rational(value):
    if isinstance(value,(sp.Rational,Fraction,int,np.integer)):return sp.Rational(value)
    value=float(value)
    if not math.isfinite(value):raise ValueError('nonfinite exact coordinate')
    return sp.Rational(value)

def exact_matrix(value):
    a=np.asarray(value,dtype=object)
    if a.ndim!=2:raise ValueError('matrix required')
    return sp.ImmutableMatrix(a.shape[0],a.shape[1],[rational(v) for v in a.flat])

@dataclass(frozen=True)
class SupportLaw:
    B:sp.ImmutableMatrix
    V:sp.ImmutableMatrix
    left_inverse:sp.ImmutableMatrix
    precision:sp.ImmutableMatrix
    provenance:dict
    semantics:str
    rank:int

def factor_support(B,V,provenance):
    b=exact_matrix(B);v=exact_matrix(V);k=b.cols
    if b.rows<1 or k>b.rows or b.rank()!=k or v.shape!=(k,k) or v!=v.T:
        raise ValueError('full-column-rank B and symmetric reduced V required')
    if any(v[:i,:i].det()<=0 for i in range(1,k+1)):
        raise ValueError('reduced covariance must be positive definite')
    if not isinstance(provenance,dict) or not provenance.get('source'):
        raise ValueError('actual structural factor provenance required')
    semantics=provenance.get('semantics')
    if semantics not in {'EXACT_STRUCTURAL','ROUNDED_UNCERTAIN'}:
        raise ValueError('support/rounding semantics required')
    left=(b.T*b).inv()*b.T if k else sp.zeros(0,b.rows)
    return SupportLaw(b,v,sp.ImmutableMatrix(left),sp.ImmutableMatrix(v.inv()) if k else v,
                      dict(provenance),semantics,k)

def _residual(law,r):
    x=np.asarray(r,dtype=object)
    if x.shape!=(law.B.rows,):raise ValueError('ordered residual dimensions disagree')
    return sp.ImmutableMatrix([rational(t) for t in x])

def contains_residual(law,r):
    x=_residual(law,r)
    if law.semantics!='EXACT_STRUCTURAL':return R.UNRESOLVED
    return R.ACCEPT if law.B*(law.left_inverse*x)==x else R.REJECT

def reduced_quadratic(law,r):
    membership=contains_residual(law,r)
    if membership==R.UNRESOLVED:raise ValueError('support unresolved; no exact quadratic')
    if membership==R.REJECT:return math.inf
    z=law.left_inverse*_residual(law,r)
    return Fraction((z.T*law.precision*z)[0]) if law.rank else Fraction(0)

def log_density(law,r):
    """Normalized density on range(B) with induced Hausdorff measure."""
    q=reduced_quadratic(law,r)
    if not math.isfinite(q):return -math.inf
    if not law.rank:return 0.
    return -.5*(law.rank*math.log(2*math.pi)+float(sp.log(law.V.det()))
                +float(sp.log((law.B.T*law.B).det()))+float(q))

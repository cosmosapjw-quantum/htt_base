"""Inclusive interval ranks for one fixed permutation-equivariant statistic."""
from dataclasses import dataclass
from fractions import Fraction
import math
import numpy as np
from common.r8_contracts import exact_alpha

@dataclass(frozen=True)
class RankEnvelope:
    M:int
    k:int
    alpha:Fraction
    certain:int
    possible:int
    p_lower:Fraction
    p_upper:Fraction
    decision:str
    score_bounds:tuple
    exact_target_hash:str|None=None
    law_admission_status:str='UNQUALIFIED_RANK_DIAGNOSTIC'
    pair_bound_receipt:object=None

def _endpoints(value):
    a,b=(value.lo,value.hi) if hasattr(value,'lo') else value
    if not math.isfinite(a) or not math.isfinite(b) or not 0<=a<=b:
        raise ValueError('all scores require finite nonnegative enclosures; no rows may be dropped')
    return a,b

def rank_from_score_bounds(bounds,observed,alpha):
    exact_alpha(alpha)
    scores=tuple(_endpoints(b) for b in bounds);m=len(scores)
    if m<2 or type(observed) is not int or not 0<=observed<m:
        raise ValueError('invalid pool or observed index')
    low,high=scores[observed]
    certain=sum(a>=high for i,(a,b) in enumerate(scores) if i!=observed)
    possible=sum(b>=low for i,(a,b) in enumerate(scores) if i!=observed)
    pl=Fraction(1+certain,m);pu=Fraction(1+possible,m)
    decision='REJECT' if pu<=alpha else 'NON_REJECT' if pl>alpha else 'UNRESOLVED'
    return RankEnvelope(m,math.isqrt(m-1)+(math.isqrt(m-1)**2<m-1),alpha,certain,possible,pl,pu,decision,scores)

def rank_envelope(pair_bounds,observed,k,alpha):
    m=len(pair_bounds)
    expected=math.isqrt(m-1)+(math.isqrt(m-1)**2<m-1) if m>=2 else 0
    if type(k) is not int or k!=expected:raise ValueError('k must equal ceil(sqrt(M-1))')
    rows=[]
    for i,row in enumerate(pair_bounds):
        if len(row)!=m:raise ValueError('square pair matrix required')
        lower=[];upper=[]
        for j,value in enumerate(row):
            a,b=_endpoints(value)
            if i==j:
                if a!=0 or b!=0:raise ValueError('diagonal must be exact zero')
                continue
            if (a,b)!=_endpoints(pair_bounds[j][i]):raise ValueError('symmetric pair enclosures required')
            lower.append(a);upper.append(b)
        rows.append((sorted(lower)[k-1],sorted(upper)[k-1]))
    return rank_from_score_bounds(rows,observed,alpha)

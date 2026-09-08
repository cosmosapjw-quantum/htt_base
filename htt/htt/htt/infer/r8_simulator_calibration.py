"""Known candidate-law simulator ranks; toy admission cannot qualify a product."""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np

class SamplingUnavailable(RuntimeError):pass

@dataclass(frozen=True)
class ToyLocationLaw:
    kind: str
    observed: float
    domain: tuple=(-1.,0.,1.)
    def __post_init__(self):
        if self.kind not in ('student5','mixture','selected_normal') or not np.isfinite(self.observed):
            raise ValueError('registered finite toy family required')
        if tuple(self.domain)!=(-1.,0.,1.):raise ValueError('registered candidate grid is fixed')
    def contains(self,x):return x in self.domain
    def sample(self,x,size,rng):
        if not self.contains(x):raise ValueError('candidate outside registered domain')
        if self.kind=='student5':return x+rng.standard_t(5,size=size)
        if self.kind=='mixture':return x+rng.normal(size=size)*np.where(rng.uniform(size=size)<.1,3.,1.)
        values=np.empty(size);pending=np.arange(size)
        for _ in range(100000):
            if not len(pending):return values
            z=rng.normal(size=len(pending));take=rng.uniform(size=len(pending))<(1+np.tanh(z))/2
            values[pending[take]]=x+z[take];pending=pending[~take]
        raise SamplingUnavailable('100000 proposals per row exhausted; no failed draw retained')

@dataclass(frozen=True)
class AbsoluteResidual:
    method_id: str='R8_ABSOLUTE_RESIDUAL_TOY_V1'
    def __call__(self,rows,x):return np.abs(rows-x)

@dataclass(frozen=True)
class RankResult:
    status: str
    pvalue: Fraction | None
    row_scores: tuple
    N: int
    seed: int
    candidate: float
    conditioning: str='KNOWN_TOY_LOCATION_LAW_ON_FIXED_THREE_POINT_GRID'
    empirical_eligible: bool=False


def candidate_rank(law,x,N,seed,procedure):
    if type(N) is not int or N<1:raise ValueError('positive fixed simulator count required')
    if not isinstance(law,ToyLocationLaw) or type(procedure) is not AbsoluteResidual:
        raise ValueError('new law/procedure needs its own symmetry and normalization validation')
    if not np.isfinite(x):raise ValueError('nonfinite candidate')
    if not law.contains(x):return RankResult('UNRESOLVED_DOMAIN',None,(),N,seed,x)
    try:sim=law.sample(x,N,np.random.default_rng(seed))
    except SamplingUnavailable:return RankResult('INPUT_UNAVAILABLE',None,(),N,seed,x)
    rows=np.r_[law.observed,sim];scores=np.asarray(procedure(rows,x))
    if scores.shape!=(N+1,) or not np.isfinite(scores).all():raise ValueError('complete finite row scores required')
    p=Fraction(1+int(np.count_nonzero(scores[1:]>=scores[0])),N+1)
    return RankResult('EXACT_SIMULATOR_RANK_WITHIN_TOY_LAW',p,tuple(scores.tolist()),N,seed,x)

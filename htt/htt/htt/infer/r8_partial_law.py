"""J1/J2 partial-law acceptance, retaining the fixed missing-scope budget."""
from dataclasses import dataclass
from fractions import Fraction
import numpy as np
from scipy.special import ndtri
from common.r8_contracts import RegionMembership as R,exact_alpha
from htt.infer.r8_support import rational

@dataclass(frozen=True)
class GaussianMarginal:
    observed:float
    mean:object
    variance:float
    provenance:str
    def accept(self,x,alpha):
        exact_alpha(alpha);mu=float(self.mean(x))
        if not np.isfinite(mu):return R.UNRESOLVED
        try:lo,hi=normal_critical_square(alpha)
        except QuantileUnresolved:return R.UNRESOLVED
        q=(Fraction(self.observed)-Fraction(mu))**2/Fraction(self.variance)
        if q<=lo:return R.ACCEPT
        if q>hi:return R.REJECT
        return R.UNRESOLVED

def gaussian_marginal(observed,mean,variance,provenance):
    if not callable(mean) or not provenance or not np.isfinite([observed,variance]).all() or variance<=0:
        raise ValueError('known positive variance, mean function and actual marginal provenance required')
    return GaussianMarginal(float(observed),mean,float(variance),str(provenance))

def marginal_acceptance(blocks,x,allocation):
    if not allocation or set(blocks)-set(allocation):raise ValueError('fixed allocation must cover every block')
    for a in allocation.values():exact_alpha(a)
    if sum(allocation.values())>1:raise ValueError('total error budget exceeds one')
    answers=[block.accept(x,allocation[name]) for name,block in blocks.items() if block is not None]
    if R.REJECT in answers:return R.REJECT
    if any(v not in {R.ACCEPT,R.REJECT,R.UNRESOLVED} for v in answers):raise ValueError('invalid membership')
    return R.UNRESOLVED if R.UNRESOLVED in answers else R.ACCEPT

def moment_acceptance(y,mu,v,alpha):
    """Requires E[Y]=mu and actual variance upper bounds; assumes no copula."""
    exact_alpha(alpha)
    yy=np.asarray(y,dtype=object);mm=np.asarray(mu,dtype=object);vv=np.asarray(v,dtype=object)
    if yy.ndim!=1 or yy.shape!=mm.shape or yy.shape!=vv.shape or not len(yy):raise ValueError('ordered nonempty vectors required')
    terms=[]
    for a,b,c in zip(yy,mm,vv):
        a,b,c=map(rational,(a,b,c))
        if c<0:raise ValueError('variance bounds cannot be negative')
        if c==0:
            if a!=b:return R.REJECT
        else:terms.append((a-b)**2/c)
    return R.ACCEPT if sum(terms)<=len(terms)/alpha else R.REJECT

def require_joint_gaussian(provenance):
    if provenance.get('joint_sampling_family')!='EXPLICIT_JOINT_GAUSSIAN' or not provenance.get('joint_law_source'):
        raise ValueError('Gaussian marginals/covariance do not establish a joint Gaussian law')
    return True

# Exact scalar Gaussian quantile bracketing. The floating quantile is only a
# starting guess; alternating-series inequalities certify both endpoints.
from functools import lru_cache
import math

class QuantileUnresolved(ArithmeticError):pass

@lru_cache(maxsize=1)
def _normalizer_bounds():
    def atan_bounds(inverse):
        total=Fraction(0)
        for n in range(180):
            total+=Fraction((-1)**n,(2*n+1)*inverse**(2*n+1))
        remainder=Fraction(1,(361)*inverse**361)
        return total,total+remainder  # even term count ends on a negative term
    a,b=atan_bounds(5);c,d=atan_bounds(239)
    pi_lo,pi_hi=16*a-4*d,16*b-4*c
    def sqrt_bound(x,upper):
        den=1<<160;n=math.isqrt((x.numerator<<320)//x.denominator)
        return Fraction(n+int(upper and Fraction(n,den)**2!=x),den)
    return sqrt_bound(2*pi_lo,False),sqrt_bound(2*pi_hi,True)


def _normal_cdf_bounds(x):
    x=Fraction(x)
    if x<0:
        lo,hi=_normal_cdf_bounds(-x);return 1-hi,1-lo
    term=x;total=term
    for n in range(1,4096):
        next_term=-term*x*x*Fraction(2*n-1,2*n*(2*n+1))
        if abs(next_term)<Fraction(1,1<<160) and n>x*x/2:
            lo,hi=sorted((total,total+next_term));a,b=_normalizer_bounds()
            return Fraction(1,2)+lo/b,Fraction(1,2)+hi/a
        total+=next_term;term=next_term
    raise QuantileUnresolved('Gaussian series budget exhausted')

@lru_cache(maxsize=128)
def normal_critical_square(alpha):
    exact_alpha(alpha);guess=float(ndtri(1-float(alpha)/2))
    if not math.isfinite(guess):raise QuantileUnresolved('quantile not finite at initial precision')
    radius=max(math.ulp(guess)*2,math.ulp(1.))
    target=1-alpha/2
    for _ in range(64):
        lo=Fraction(max(0.,guess-radius));hi=Fraction(guess+radius)
        if _normal_cdf_bounds(lo)[1]<=target<=_normal_cdf_bounds(hi)[0]:return lo*lo,hi*hi
        radius*=2
    raise QuantileUnresolved('quantile bracket unresolved')


def _sqrt_rational_bounds(x):
    x=Fraction(x);d=1<<160;n=math.isqrt((x.numerator<<320)//x.denominator)
    lo=Fraction(n,d);return lo,lo if lo*lo==x else Fraction(n+1,d)


def _exp_negative_bounds(x):
    x=Fraction(x);term=Fraction(1);total=term
    for n in range(1,4096):
        next_term=-term*x/n
        if abs(next_term)<Fraction(1,1<<160) and n>x:
            return tuple(sorted((total,total+next_term)))
        total+=next_term;term=next_term
    raise QuantileUnresolved('exponential enclosure budget exhausted')


def _chi_cdf_bounds(t,rank):
    """Integer-shape incomplete-gamma recurrence with rational enclosures."""
    t=Fraction(t);x=t/2;elo,ehi=_exp_negative_bounds(x)
    if rank%2==0:
        # F_{2n}(t)=1-exp(-x)*sum_{j=0}^{n-1} x^j/j!.
        total=term=Fraction(1)
        for j in range(1,rank//2):term*=x/j;total+=term
        return 1-ehi*total,1-elo*total
    a,b=_sqrt_rational_bounds(t)
    flo,fhi=2*_normal_cdf_bounds(a)[0]-1,2*_normal_cdf_bounds(b)[1]-1
    # F_{k+2}=F_k-exp(-x)*x^(k/2)/Gamma(k/2+1).
    # For k=1 this term is sqrt(2/pi)*sqrt(t)*exp(-x).
    nlo,nhi=_normalizer_bounds();glo=2*a*elo/nhi;ghi=2*b*ehi/nlo
    for k in range(1,rank,2):
        flo-=ghi;fhi-=glo
        factor=x/Fraction(k+2,2);glo*=factor;ghi*=factor
    return flo,fhi

@lru_cache(maxsize=128)
def chi_critical_bounds(alpha,rank):
    exact_alpha(alpha)
    if type(rank) is not int or not 0<=rank<=256:raise QuantileUnresolved('rank exceeds exact-quantile resource domain')
    if rank==0:return Fraction(0),Fraction(0)
    if rank==1:return normal_critical_square(alpha)
    from scipy.stats import chi2
    guess=float(chi2.ppf(1-float(alpha),rank))
    if not math.isfinite(guess):raise QuantileUnresolved('nonfinite quantile starting guess')
    radius=max(2*math.ulp(guess),math.ulp(1.));target=1-alpha
    for _ in range(64):
        lo=Fraction(max(0.,guess-radius));hi=Fraction(guess+radius)
        if _chi_cdf_bounds(lo,rank)[1]<=target<=_chi_cdf_bounds(hi,rank)[0]:return lo,hi
        radius*=2
    raise QuantileUnresolved('chi-square bracket unresolved')

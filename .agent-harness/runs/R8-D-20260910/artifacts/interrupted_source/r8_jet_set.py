"""P1/P2 deterministic jet-set images; no inferred covariance or sky law."""
from dataclasses import dataclass
from fractions import Fraction as F
import math
import numpy as np
from .r8_contracts import Bound


def rational(x):
    if isinstance(x,(F,int,np.integer)):return F(x)
    if isinstance(x,str):return F(x)
    value=float(x)
    if not math.isfinite(value):raise ValueError('finite exact/dyadic input required')
    return F(value)


def array(x):
    a=np.asarray(x,dtype=object)
    return np.array([rational(v) for v in a.flat],dtype=object).reshape(a.shape)


def sqrt_bounds(x):
    x=rational(x)
    if x<0:raise ValueError('nonnegative squared norm required')
    d=1<<256;n=math.isqrt((x.numerator<<512)//x.denominator);lo=F(n,d)
    return lo,lo if lo*lo==x else F(n+1,d)


@dataclass(frozen=True)
class JetDomain:
    domain_id:str
    frame:str
    K:object
    assumptions:tuple[str,...]
    def __post_init__(self):
        k=array(self.K)
        if k.ndim!=2 or k.shape[0]!=8 or not self.domain_id or not self.frame or not self.assumptions:
            raise ValueError('named eight-output normalized tensor map and premises required')
        k.setflags(write=False);object.__setattr__(self,'K',k)


@dataclass(frozen=True)
class TensorImage:
    central_prediction:np.ndarray
    factor:np.ndarray
    rho:object
    remainder_rate_radii:tuple
    theta:object
    domain:JetDomain
    status:str
    j0:np.ndarray
    L:np.ndarray


def p1_operator(theta):
    """j=(dot q[5], STF Dd[5], div o[5], dot Cout[3], Cout[3], E[3]).

    Orthonormal STF/antisymmetric coordinates, outward convention, normalized
    brightness derivatives, first order ABOUT FLRW; Theta=3H>0. dot q includes
    the derivative of Q/Tbar. Return (sigma/Theta,omega/Theta), in that order.
    """
    t=rational(theta)
    if t<=0:raise ValueError('positive Theta required')
    k=np.full((8,24),F(0),dtype=object)
    for i in range(5):k[i,i]=-1/t;k[i,5+i]=1/t;k[i,10+i]=F(3,7)/t
    for i in range(3):k[5+i,15+i]=3/t**2;k[5+i,18+i]=1/t;k[5+i,21+i]=-F(6,5)/t**2
    return k


def jet_image(j0,L,rho,remainder,theta,domain):
    if not isinstance(domain,JetDomain):raise TypeError('typed JetDomain required')
    j=array(j0);l=array(L)
    if j.ndim!=1 or l.ndim!=2 or len(j)!=domain.K.shape[1] or l.shape[0]!=len(j):raise ValueError('ordered jet/map dimensions differ')
    r=math.inf if rho==math.inf else rational(rho)
    if r<0:raise ValueError('nonnegative deterministic radius required')
    rem=tuple(rational(v) for v in remainder)
    if len(rem)!=2 or any(v<0 for v in rem):raise ValueError('two nonnegative rate remainder radii required')
    status='EXACT_DECLARED_MINKOWSKI_IMAGE'
    if isinstance(theta,(tuple,list)):
        t=tuple(rational(v) for v in theta)
        if len(t)!=2 or not 0<t[0]<=t[1]:raise ValueError('positive ordered Theta domain required')
        status='PARAMETERIZED_THETA_UNRESOLVED'
    else:
        t=rational(theta)
        if t<=0:raise ValueError('positive Theta required')
    center=domain.K@j;factor=domain.K@l
    for a in (j,l,center,factor):a.setflags(write=False)
    return TensorImage(center,factor,r,rem,t,domain,status,j,l)


def support(image,a):
    if not isinstance(image,TensorImage):raise TypeError('typed joint TensorImage required')
    a=array(a)
    if a.shape!=(8,):raise ValueError('five shear plus three vorticity coefficients required')
    if image.status!='EXACT_DECLARED_MINKOWSKI_IMAGE':
        return Bound(-math.inf,math.inf,{'status':'OUTER_RANGE_UNRESOLVED','reason':image.status})
    center=sum(a*image.central_prediction);direction=image.factor.T@a;norm2=sum(direction*direction)
    cert={'status':'EXACT_DECLARED_SET_SUPPORT_ENCLOSURE','domain_id':image.domain.domain_id,
          'arithmetic':'EXACT_RATIONAL_WITH_OUTWARD_256_BIT_SQUARE_ROOTS','theta':str(image.theta),
          'scope':'deterministic ellipsoid plus two independent rate remainder balls; not covariance or observed confidence'}
    if image.rho==math.inf and norm2:
        return Bound(math.inf,math.inf,{**cert,'status':'UNBOUNDED_SUPPORT_LOCAL_DOMAIN'})
    lo=hi=center
    terms=[(image.rho if norm2 else F(0),norm2),
           (image.remainder_rate_radii[0]/image.theta,sum(a[:5]*a[:5])),
           (image.remainder_rate_radii[1]/image.theta,sum(a[5:]*a[5:]))]
    for coefficient,squared in terms:
        if coefficient==0:continue
        lower,upper=sqrt_bounds(squared);lo+=coefficient*lower;hi+=coefficient*upper
    return Bound(lo,hi,cert)

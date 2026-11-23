"""Shared, source-traceable research primitives; no production HTT modification.

These routines consolidate the repeated mathematical operations needed by the
catalogued DP/MZ, moment and interval studies. See CORE_PROVENANCE.json for the
legacy anchors. They are scoped to finite matrices and finite probability laws.
"""
from __future__ import annotations
from itertools import product
import numpy as np
from scipy.linalg import expm


def legendre_streaming(lmax: int, omega: float = 1.0, normalized: bool = False):
    """Free streaming only: I'_l=omega*(l I_(l-1)-(l+1)I_(l+1))/(2l+1).

    Hard boundary I_(lmax+1)=0. omega has inverse-clock units.
    normalized=True acts on sqrt(2l+1)*I_l, hence returns a skew matrix.
    """
    if not isinstance(lmax, (int,np.integer)) or lmax<0 or not np.isfinite(omega):
        raise ValueError('finite omega and nonnegative integer lmax required')
    a=np.zeros((lmax+1,lmax+1))
    for l in range(lmax):
        a[l,l+1]=-omega*(l+1)/(2*l+1)
        a[l+1,l]=omega*(l+1)/(2*l+3)
    if normalized:
        s=np.sqrt(2*np.arange(lmax+1)+1)
        a=s[:,None]*a/s[None,:]
    return a


def partition_generator(generator, resolved):
    """Partition one fixed generator; never rebuild coefficients at a new cutoff."""
    g=np.asarray(generator)
    if g.ndim!=2 or g.shape[0]!=g.shape[1]:raise ValueError('square generator required')
    raw=np.asarray(resolved)
    if raw.ndim!=1 or not np.isfinite(raw).all() or np.any(raw!=np.floor(raw)) or not np.isfinite(g).all():raise ValueError('finite matrix and integer 1-D resolved indices required')
    r=np.asarray(raw,dtype=int)
    if len(set(r))!=len(r) or np.any(r<0) or np.any(r>=len(g)):raise ValueError('invalid resolved indices')
    h=np.array([i for i in range(len(g)) if i not in set(r)],dtype=int)
    return tuple(g[np.ix_(i,j)] for i,j in ((r,r),(r,h),(h,r),(h,h)))


def memory_kernel(B,D,C,lag):
    """Exact constant-block kernel B exp(D*lag) C, with the declared clock."""
    if lag<0:raise ValueError('causal lag must be nonnegative')
    return np.asarray(B)@expm(np.asarray(D)*lag)@np.asarray(C)


def schur_resolvent(A,B,C,D,z):
    """Resolved block of (z I-G)^-1 for one fixed block generator."""
    A,B,C,D=map(np.asarray,(A,B,C,D))
    return np.linalg.inv(z*np.eye(len(A))-A-B@np.linalg.solve(z*np.eye(len(D))-D,C))


def normalized_tilt(probability,potential,step):
    p=np.asarray(probability,float);v=np.asarray(potential,float)
    if p.ndim!=1 or p.shape!=v.shape or not np.isfinite(p).all() or np.any(p<0) or not np.isclose(p.sum(),1) or not np.isfinite(v).all() or not np.isfinite(step):
        raise ValueError('finite potential and normalized nonnegative probability required')
    logw=np.full_like(p,-np.inf);nz=p>0;logw[nz]=np.log(p[nz])+step*v[nz]
    w=np.exp(logw-np.max(logw));return w/w.sum()


def score_projection(probability,statistics,potential,rcond=1e-12):
    """Fisher projection of a centered potential onto retained moment scores.

    Finite strictly positive law. The normalization row is implicit in centering.
    Columns are variance-standardized before a numerical pseudoinverse. Modes
    below rcond on the correlation matrix are discarded, not regularized. The
    formal exact-span theorem applies only when no true supported mode is lost.
    """
    p=np.asarray(probability,float);T=np.asarray(statistics,float);v=np.asarray(potential,float)
    if T.ndim==1:T=T[:,None]
    if p.ndim!=1 or T.ndim!=2 or not len(p) or np.any(p<=0) or not np.isclose(p.sum(),1) or T.shape[0]!=len(p) or v.shape!=p.shape or not all(np.isfinite(x).all() for x in (p,T,v)) or not np.isfinite(rcond) or rcond<0:
        raise ValueError('positive normalized finite law and matching arrays required')
    Tc=T-p@T;vc=v-p@v
    fisher=Tc.T@(p[:,None]*Tc);cross=Tc.T@(p*vc)
    scales=np.sqrt(np.maximum(np.diag(fisher),0));active=scales>0
    beta=np.zeros(T.shape[1]);rank=0;singular_values=np.array([])
    if np.any(active):
        corr=fisher[np.ix_(active,active)]/scales[active,None]/scales[None,active]
        singular_values=np.linalg.svd(corr,compute_uv=False)
        rank=int(np.count_nonzero(singular_values>rcond*singular_values[0]))
        beta[active]=(np.linalg.pinv(corr,rcond=rcond)@(cross[active]/scales[active]))/scales[active]
    residual=vc-Tc@beta
    return {'fisher':fisher,'cross':cross,'beta':beta,'residual':residual,
            'residual_variance':float(p@(residual**2)),
            'moment_orthogonality':Tc.T@(p*residual),'mean_residual':float(p@residual),
            'numerical_rank':rank,'rcond':rcond,'standardization_scales':scales,
            'correlation_singular_values':singular_values}


def joint_fractional_interval(num_reach,den_reach,shared_bounds=(),c_num=(),c_den=()):
    """Exact extrema over a finite affine box, strictly positive denominator.

    Unlike the legacy two-pair implementation, all four independent reachable
    endpoint combinations are considered, including negative numerators.
    Complexity O(2**k * k). Caller should use LP for large-dimensional polytopes.
    """
    pairs=[num_reach,den_reach,*shared_bounds]
    if any(len(v)!=2 or not np.isfinite(v).all() or v[0]>v[1] for v in map(np.asarray,pairs)):
        raise ValueError('finite ordered interval endpoints required')
    cn=np.asarray(c_num,float);cd=np.asarray(c_den,float)
    if cn.ndim!=1 or cd.ndim!=1 or len(cn)!=len(shared_bounds) or len(cd)!=len(shared_bounds):
        raise ValueError('coefficient/bounds mismatch')
    if not np.isfinite(cn).all() or not np.isfinite(cd).all():raise ValueError('finite coefficients required')
    grids=[(lo,hi) if hi>lo else (lo,) for lo,hi in shared_bounds]
    values=[]
    for x in product(*grids):
        dn=float(cn@np.asarray(x));dd=float(cd@np.asarray(x))
        if den_reach[0]+dd<=0:raise ValueError('denominator not strictly positive on box')
        values.extend((n+dn)/(d+dd) for n in num_reach for d in den_reach)
    return min(values),max(values)


def gaussian_covariance_score(y,covariance,derivative):
    """Derivative of log N(y;0,C(alpha)); no claim that this is a selected law."""
    y=np.asarray(y,float);C=np.asarray(covariance,float);Cp=np.asarray(derivative,float)
    if y.ndim!=1 or C.shape!=(len(y),len(y)) or Cp.shape!=C.shape or not all(np.isfinite(x).all() for x in (y,C,Cp)) or not np.allclose(C,C.T) or not np.allclose(Cp,Cp.T):
        raise ValueError('finite real vector and symmetric matching covariance matrices required')
    # Cholesky validates positive definiteness; solves avoid a stored inverse.
    np.linalg.cholesky(C)
    v=np.linalg.solve(C,y)
    return float(.5*(v@Cp@v-np.trace(np.linalg.solve(C,Cp))))


def tca_quadrupole_from_declared_equation(source_t,source_e,gamma):
    """Solve exactly the two equations documented in legacy PR13AF.

    This checks that declared matrix convention only, not a complete physical
    derivation of the Thomson operator in every convention.
    """
    if not np.isfinite(gamma) or gamma<=0:raise ValueError('positive finite gamma required')
    M=np.array([[-.9,-np.sqrt(6)/10],[-3/(5*np.sqrt(6)),-.4]])
    return np.linalg.solve(M,-np.array([source_t,source_e],complex)/gamma)


def optical_depth_to_endpoint(eta,gamma):
    """Positive trapezoid optical depth integral_eta^eta_end gamma d eta.

    eta strictly increases, gamma>=0. gamma carries inverse-eta units.
    """
    eta=np.asarray(eta,float);gamma=np.asarray(gamma,float)
    if eta.ndim!=1 or len(eta)==0 or gamma.shape!=eta.shape or not np.isfinite(eta).all() or not np.isfinite(gamma).all():
        raise ValueError('finite matching nonempty one-dimensional arrays required')
    if np.any(np.diff(eta)<=0) or np.any(gamma<0):raise ValueError('increasing eta and nonnegative opacity required')
    increments=.5*(gamma[:-1]+gamma[1:])*np.diff(eta)
    return np.r_[np.cumsum(increments[::-1])[::-1],0.]


def exchangeable_global_rank(oriented_scores, observed_index=0):
    """Permutation-equivariant min-local-rank calibration on ALL rows.

    One row is the observation, all others are null realizations. Higher input
    is more extreme. Validity REQUIRES exchangeable rows and one shared,
    permutation-equivariant upstream procedure; it does not create that law.
    If two-sided centering is estimated, it must treat all rows symmetrically
    (or use a separately fixed center). Cost O(P*n*log(n)), memory O(n*P).
    """
    scores=np.asarray(oriented_scores,float)
    if scores.ndim!=2 or scores.shape[0]<2 or scores.shape[1]<1 or not np.isfinite(scores).all():
        raise ValueError('finite (n>=2, P>=1) score array required')
    n,p=scores.shape
    if not 0<=observed_index<n:raise ValueError('invalid observed row')
    local=np.empty_like(scores)
    for j in range(p):
        local[:,j]=(n-np.searchsorted(np.sort(scores[:,j]),scores[:,j],side='left'))/n
    extreme=np.min(local,axis=1)
    return {'local_p':local[observed_index],
            'global_p':float(np.count_nonzero(extreme<=extreme[observed_index])/n),
            'row_min_local_p':extreme}


def conditional_bin_information(rates,rate_derivatives,total_count):
    """Multinomial shape Fisher information conditional on the baseline count.

    rates are positive relative bin rates, derivative rows match the bins.
    N is a fixed count or the declared expected count when comparing to a
    Poisson information matrix after amplitude profiling.
    """
    r=np.asarray(rates,float);dr=np.asarray(rate_derivatives,float)
    if dr.ndim==1:dr=dr[:,None]
    if r.ndim!=1 or dr.shape[0]!=len(r) or np.any(r<=0) or not np.isfinite(r).all() or not np.isfinite(dr).all() or not np.isfinite(total_count) or total_count<0:
        raise ValueError('positive finite rates, derivatives and nonnegative count required')
    pi=r/r.sum();dpi=(dr-pi[:,None]*dr.sum(axis=0))/r.sum()
    return total_count*(dpi.T@(dpi/pi[:,None]))


def legendre_power_coefficients(coefficients, power: int):
    """Coefficients of (sum_l c_l P_l(mu))**power, without physical closure.

    Standard unnormalised Legendre P_l; real dimensionless coefficients.
    No angular/grid truncation. Multiplication is exact polynomial algebra
    up to floating-point roundoff; degree <= power*(len(c)-1).
    """
    from numpy.polynomial.legendre import legmul
    c=np.asarray(coefficients,dtype=float)
    if c.ndim!=1 or not len(c) or not np.all(np.isfinite(c)):
        raise ValueError('finite nonempty 1-D coefficients required')
    if not isinstance(power,(int,np.integer)) or power<0:
        raise ValueError('nonnegative integer power required')
    result=np.array([1.0])
    for _ in range(power): result=legmul(result,c)
    return result


def legendre_tail_mean_square(coefficients, retained_lmax: int):
    """(1/2) integral[-1,1] |sum_{l>L} c_l P_l|^2 dmu.

    Standard Legendre coefficients, not (2l+1)-weighted brightness moments.
    """
    c=np.asarray(coefficients,dtype=complex)
    if c.ndim!=1 or not np.all(np.isfinite(c)) or not isinstance(retained_lmax,(int,np.integer)) or retained_lmax<0:
        raise ValueError('finite 1-D coefficients and nonnegative L required')
    ell=np.arange(len(c));keep=ell>retained_lmax
    return float(np.sum(np.abs(c[keep])**2/(2*ell[keep]+1)))

"""Finite research primitives consolidated from attachment-derived constructions.

Column populations; rates use one declared clock. These are research adapters,
not replacements for native HyRec or the current cosmological generator.
"""
from __future__ import annotations
from math import factorial
import numpy as np
from scipy.linalg import expm, solve


def _transient_matrix(q):
    q = np.asarray(q, dtype=float)
    if q.ndim != 2 or q.shape[0] != q.shape[1] or not np.isfinite(q).all():
        raise ValueError('finite square transient matrix required')
    if np.max(np.linalg.eigvals(q).real) >= 0:
        raise ValueError('hidden block must be Hurwitz; retain zero modes')
    return q


def schur_memory_coefficients(generator, retained, atol=1e-11):
    """L0, first memory mass M and physical mass row for finite Markov L.

    Exact resolvent: zI-A-B(zI-D)^-1 C.
    Low-frequency expansion: zM-L0+O(z^2). M^-1 L0 need not be Metzler.
    """
    l = np.asarray(generator, dtype=float)
    if l.ndim != 2 or l.shape[0] != l.shape[1] or not np.isfinite(l).all():
        raise ValueError('finite square generator required')
    if not 0 < retained < len(l):
        raise ValueError('nonempty retained and hidden blocks required')
    scale = max(1., np.max(np.abs(l)))
    off = l.copy(); np.fill_diagonal(off, 0)
    if np.min(off) < -atol*scale or np.max(np.abs(l.sum(axis=0))) > atol*scale:
        raise ValueError('column-conservative Metzler generator required')
    a, b = l[:retained, :retained], l[:retained, retained:]
    c, d = l[retained:, :retained], _transient_matrix(l[retained:, retained:])
    dc = solve(d, c); ddc = solve(d, dc)
    l0 = a-b@dc
    mass = np.eye(retained)+b@ddc
    physical_mass = np.ones(retained)-np.ones(len(d))@dc
    return dict(A=a, B=b, C=c, D=d, L0=l0, M=mass,
                physical_mass=physical_mass, memory_first_moment=b@ddc)


def phase_type_moments(q, line_rate, injection, nmax=3):
    """n! ell(-Q)^(-n-1)p, with units time^n times line yield.

    Q is a fixed transient column generator, ell a nonnegative reward rate,
    and p a nonnegative injection. The caller specifies its normalization.
    """
    q,ell,p = _phase_type_inputs(q,line_rate,injection)
    if not isinstance(nmax,int) or nmax<0:raise ValueError('nonnegative integer moment order required')
    v=p;out=[]
    for n in range(nmax+1):
        v=solve(-q,v);out.append(factorial(n)*float(ell@v))
    return np.array(out)


def _phase_type_inputs(q,line_rate,injection):
    q = _transient_matrix(q); ell=np.asarray(line_rate,float); p=np.asarray(injection,float)
    if ell.shape!=(len(q),) or p.shape!=(len(q),):
        raise ValueError('one line rate and injection weight per transient state required')
    off=q.copy();np.fill_diagonal(off,0)
    if np.min(off)<-1e-13 or np.max(q.sum(axis=0))>1e-12:
        raise ValueError('substochastic column generator required')
    if np.min(ell)<0 or np.min(p)<0 or not np.isfinite(ell).all() or not np.isfinite(p).all():
        raise ValueError('finite positive line rate and injection required')
    return q,ell,p


def phase_type_bin(q, line_rate, injection, lower, upper, birth=0.):
    """Finite-bin line yield; augmented exponential avoids inverse subtraction."""
    q,ell,p=_phase_type_inputs(q,line_rate,injection)
    if not np.isfinite([lower,upper,birth]).all():raise ValueError('finite endpoints and birth time required')
    if upper < lower:raise ValueError('ordered observation interval required')
    lo=max(0.,lower-birth);hi=max(0.,upper-birth)
    if hi==lo:return 0.
    n=len(q);aug=np.zeros((n+1,n+1));aug[:n,:n]=q;aug[:n,n]=p
    return float(ell@expm(q*lo)@expm(aug*(hi-lo))[:n,n])


def moment_direction(q, line_rate, injection, dq, dline, dinjection, n=1):
    """Full directional derivative of the nth line-delay moment."""
    q=_transient_matrix(q);h=solve(-q,np.eye(len(q)))
    ell=np.asarray(line_rate,float);p=np.asarray(injection,float)
    dh=h@np.asarray(dq,float)@h
    power=np.linalg.matrix_power(h,n+1)
    dpower=sum((np.linalg.matrix_power(h,j)@dh@np.linalg.matrix_power(h,n-j)
                for j in range(n+1)),start=np.zeros_like(h))
    return factorial(n)*float(np.asarray(dline)@power@p + ell@dpower@p + ell@power@np.asarray(dinjection))


def gram_connection(basis, dbasis):
    """Square invertible passive basis: G=V†V, Gamma=V^-1 V'.

    A rectangular moving subspace also has complement leakage and must use
    a different construction; silently dropping that leakage is not allowed.
    """
    v=np.asarray(basis);dv=np.asarray(dbasis)
    if v.ndim!=2 or v.shape[0]!=v.shape[1] or dv.shape!=v.shape:
        raise ValueError('square full-frame basis and same-shaped derivative required')
    g=v.conj().T@v; dg=dv.conj().T@v+v.conj().T@dv
    return g,solve(v,dv),dg


def stf_orthonormal_basis():
    """Frobenius-orthonormal 3x3 real STF basis; not the five research views."""
    b=np.zeros((5,3,3));b[0]=np.diag([2,-1,-1])/np.sqrt(6);b[1]=np.diag([0,1,-1])/np.sqrt(2)
    for i,(j,k) in enumerate(((0,1),(0,2),(1,2)),2):b[i,j,k]=b[i,k,j]=1/np.sqrt(2)
    return b


def lie_jacobi_vector(n, a):
    """Symmetric Bianchi structure matrix convention: Jacobi residual N a."""
    n=np.asarray(n,float);a=np.asarray(a,float)
    if n.shape!=(3,3) or a.shape!=(3,) or not np.allclose(n,n.T):
        raise ValueError('symmetric 3x3 N and 3-vector a required')
    return n@a


def stimulated_axis_law(mu, eta, anisotropy):
    """Normalized dP/dmu for 1+f, f=eta(1+a mu), mu in [-1,1]."""
    mu=np.asarray(mu,float)
    if eta<0 or abs(anisotropy)>1 or np.any(abs(mu)>1):
        raise ValueError('eta>=0, |a|<=1 and |mu|<=1 required')
    return (1+eta*(1+anisotropy*mu))/(2*(1+eta))


def stimulated_axis_response(eta, anisotropy):
    if eta<0 or abs(anisotropy)>1:raise ValueError('positive occupation domain required')
    mean=eta*anisotropy/(3*(1+eta))
    return dict(normalization=1+eta,mean=mean,variance=1/3-mean**2,
                dmean_deta=anisotropy/(3*(1+eta)**2))


def opacity_per_clock(ne, sigma, c, clock_rate, dne=0., dsigma=0., dclock=0.):
    """Positive n_e sigma c / (ds/dt), plus complete fixed-s derivative.

    For N=ln a, clock_rate=physical H, and result is dimensionless. This
    scalar rest-frame expression is not a replacement for the full tilted
    electron-current contraction along a photon ray.
    """
    if min(ne,sigma,c,clock_rate)<=0:raise ValueError('positive density, cross section, speed and clock required')
    value=ne*sigma*c/clock_rate
    return value,value*(dne/ne+dsigma/sigma-dclock/clock_rate)


def fold_bin_mass(epsilon, rate=.3):
    """Pushforward z=t²-eps, density rate exp[-rate(t+1)], t∈[-1,1].

    Mass in z<=0. eps has units of dimensionless z here; for 0<eps<1,
    response is 2 exp(-rate) sinh(rate sqrt(eps)), hence Holder 1/2.
    """
    if not np.isfinite([epsilon,rate]).all() or epsilon<0 or epsilon>1 or rate<=0:
        raise ValueError('finite 0<=epsilon<=1, rate>0 required')
    width=np.sqrt(epsilon)
    return np.exp(-rate*(1-width))*(-np.expm1(-2*rate*width))


def positive_matrix_moments(nodes, amplitudes, weights, degree=2):
    """Kp=sum w x^p v v† for an actual supplied positive finite measure."""
    x=np.asarray(nodes,float);v=np.asarray(amplitudes);w=np.asarray(weights,float)
    if x.ndim!=1 or v.ndim!=2 or v.shape[0]!=len(x) or w.shape!=x.shape:
        raise ValueError('aligned nodes, amplitudes and weights required')
    if np.any(x<0) or np.any(x>1) or np.any(w<0):raise ValueError('positive measure on [0,1] required')
    return np.array([np.einsum('n,ni,nj->ij',w*x**p,v,v.conj()) for p in range(degree+1)])


def spectral_response(nodes, amplitudes, weights, detector, response):
    """Integrate response against the detector contraction of vv† measure."""
    v=np.asarray(amplitudes);e=np.asarray(detector);w=np.asarray(weights)
    if v.ndim!=2 or e.shape!=(v.shape[1],v.shape[1]) or not np.isfinite(e).all():
        raise ValueError('finite detector on the supplied source space required')
    if not np.allclose(e,e.conj().T,rtol=0,atol=1e-13):
        raise ValueError('detector must be Hermitian; imaginary response is not discarded')
    ev=np.linalg.eigvalsh(e)
    if ev.min() < -1e-13 or ev.max() > 1+1e-13:
        raise ValueError('detector effect must satisfy 0<=E<=I')
    scalar=np.einsum('ni,ij,nj->n',v.conj(),e,v).real
    return float(np.dot(w*scalar,np.asarray(response(np.asarray(nodes)))))

"""R66: signed low-ell radiation-stress images and a declared DQ quotient.

All sky vectors are Galactic look directions, photon propagation is -n,
metric (-,+,+,+). Temperatures use microkelvin unless a name says otherwise.
This module defines post-release estimators. It does not calibrate Commander
component separation, infer matter shear, or declare a cosmological anomaly.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import numpy as np
from scipy import linalg, special, stats
from scipy.constants import c, hbar, k as k_B

from .r54_tensor_five_view import STF5_BASIS, stf5_to_matrix, matrix_to_stf5
from .r58_mixed_tensor_likelihood import fit_linear

T0_K = 2.72548
T0_UK = T0_K * 1e6
RHO0_SI = math.pi**2 * k_B**4 * T0_K**4 / (15 * hbar**3 * c**3)
STRESS_PER_UK = 8 / (15 * T0_UK)  # pi_lin/rho0 per microkelvin
PHYSICAL_OUTER_RADIUS = math.sqrt(2 / 3)
ADMISSIBLE_INNER_RADIUS = 1 / math.sqrt(6)


def _finite(a, shape=None):
    a = np.asarray(a, dtype=float)
    if not np.isfinite(a).all() or (shape is not None and a.shape != shape):
        raise ValueError("nonfinite array or wrong shape")
    return a


def direction(l_deg: float, b_deg: float) -> np.ndarray:
    l, b = np.deg2rad([l_deg, b_deg])
    return np.array([np.cos(b)*np.cos(l), np.cos(b)*np.sin(l), np.sin(b)])


DIPOLE_DIRECTION = direction(264.021, 48.253)
BETA = 3362.08 / T0_UK
DQ_UK = T0_UK * BETA**2 * np.einsum(
    "i,aij,j->a", DIPOLE_DIRECTION, STF5_BASIS, DIPOLE_DIRECTION)


def harmonic_design(n: np.ndarray, lmax: int = 6) -> tuple[np.ndarray, list[str]]:
    """Columns 1,nx,ny,nz, five STF quadratics, then orthonormal real Y_lm.

    For l>=3: Y_l0, sqrt2 Re Y_lm, sqrt2 Im Y_lm. Real coefficient
    convention is therefore a_lm=(d_cos-i d_sin)/sqrt2. The first nine
    columns are physical polynomial coordinates, not normalized harmonics.
    """
    n = _finite(n)
    if n.ndim != 2 or n.shape[1] != 3 or lmax < 2:
        raise ValueError("unit directions and lmax>=2 required")
    if not np.allclose(np.linalg.norm(n, axis=1), 1, atol=1e-12):
        raise ValueError("directions must have unit length")
    cols = [np.ones(len(n)), *n.T]
    cols.extend(np.einsum("ni,aij,nj->na", n, STF5_BASIS, n).T)
    labels = ["monopole", "dipole_x", "dipole_y", "dipole_z",
              "Q_xx-yy", "Q_xx+yy-2zz", "Q_xy", "Q_xz", "Q_yz"]
    theta, phi = np.arccos(np.clip(n[:, 2], -1, 1)), np.arctan2(n[:, 1], n[:, 0])
    for ell in range(3, lmax+1):
        cols.append(special.sph_harm_y(ell, 0, theta, phi).real)
        labels.append(f"T_{ell}_0")
        for m in range(1, ell+1):
            y = special.sph_harm_y(ell, m, theta, phi)
            cols.extend([math.sqrt(2)*y.real, math.sqrt(2)*y.imag])
            labels.extend([f"T_{ell}_{m}r", f"T_{ell}_{m}i"])
    return np.column_stack(cols), labels


@dataclass(frozen=True)
class Estimator:
    matrix: np.ndarray
    retained: np.ndarray
    condition: float
    labels: tuple[str, ...]

    def extract(self, coarse_map: np.ndarray) -> np.ndarray:
        data = _finite(np.asarray(coarse_map)[self.retained])
        return self.matrix @ data


def estimator(design: np.ndarray, retained: np.ndarray, labels) -> Estimator:
    h = _finite(design)[np.asarray(retained, bool)]
    if h.shape[0] <= h.shape[1]:
        raise ValueError("insufficient retained pixels")
    q, r = np.linalg.qr(h, mode="reduced")
    condition = float(np.linalg.cond(r))
    if not np.isfinite(condition) or condition > 1e8:
        raise ValueError("unsupported or ill-conditioned finite estimator")
    e = linalg.solve_triangular(r, q.T)
    return Estimator(e, np.asarray(retained, bool), condition, tuple(labels))


def quotient_basis(template: np.ndarray) -> np.ndarray:
    """Orthonormal coordinates for the complement of a nonzero measured template."""
    b = _finite(template)
    if b.ndim != 1 or np.linalg.norm(b) == 0:
        raise ValueError("nonzero one-dimensional nuisance template required")
    return linalg.null_space(b[None, :])


def profile_precision(cov: np.ndarray, template: np.ndarray) -> np.ndarray:
    """Gaussian precision after profiling a single unknown template amplitude."""
    cov, b = _finite(cov), _finite(template)
    if b.ndim!=1 or cov.shape!=(len(b),len(b)) or np.linalg.norm(b)==0 or not np.allclose(cov,cov.T):
        raise ValueError("symmetric covariance and nonzero compatible template required")
    ci = linalg.cho_solve(linalg.cho_factor(cov, lower=True), np.eye(len(b)))
    cb = ci @ b
    return ci - np.outer(cb, cb) / (b @ cb)


@dataclass(frozen=True)
class ConditionalReference:
    """Conditional Gaussian predictive law, covariance estimated from N skies.

    The population mean is specified zero, not estimated from the MC sample.
    S=X^T X/N and NS~Wishart(C,N) for iid Gaussian rows. The observed sky
    is assumed independent of these rows under the SAME processed population.
    Actual Commander source matching is a separate, unresolved qualification.
    This is a stochastic-background reference, not measurement-only error.
    """
    covariance: np.ndarray
    n: int
    p: int

    def __post_init__(self):
        s=_finite(self.covariance,(self.p,self.p))
        if self.p<1 or self.n<=self.p or not np.allclose(s,s.T):
            raise ValueError("N>p and symmetric positive covariance required")
        np.linalg.cholesky(s)

    @classmethod
    def from_draws(cls, draws):
        x = _finite(draws)
        if x.ndim != 2 or len(x) <= x.shape[1]:
            raise ValueError("N must exceed the carrier dimension")
        if not np.any(x):
            raise ValueError("all-zero carrier is not a reference population")
        s = x.T @ x / len(x)
        np.linalg.cholesky(s)
        return cls(s, len(x), x.shape[1])

    @property
    def df(self):
        return self.n - self.p + 1

    def q2(self, residual):
        r = _finite(residual, (self.p,))
        return float(r @ np.linalg.solve(self.covariance, r))

    def tail(self, residual):
        q2 = self.q2(residual)
        f = self.df * q2 / (self.p * self.n)
        return {"q2": q2, "F": f, "df1": self.p, "df2": self.df,
                "lower": float(stats.f.cdf(f, self.p, self.df)),
                "upper": float(stats.f.sf(f, self.p, self.df)),
                "status": "CONDITIONAL_GAUSSIAN_PROCESSED_REFERENCE"}

    def logpdf(self, residual):
        """Jeffreys-covariance predictive density, a multivariate t in residual."""
        shape = self.n / self.df * self.covariance
        return float(stats.multivariate_t.logpdf(residual, loc=np.zeros(self.p),
                                                shape=shape, df=self.df))

    def radius2(self, coverage=.95):
        if not 0 < coverage < 1:
            raise ValueError("coverage must lie strictly between zero and one")
        return float(self.p*self.n/self.df * stats.f.ppf(coverage, self.p, self.df))


@dataclass(frozen=True)
class KnownGaussianReference:
    """Exact law within an explicitly declared model with known covariance."""
    covariance: np.ndarray

    def __post_init__(self):
        s=_finite(self.covariance)
        if s.ndim!=2 or s.shape[0]!=s.shape[1] or not np.allclose(s,s.T):
            raise ValueError("symmetric square covariance required")
        np.linalg.cholesky(s)

    @property
    def p(self):return len(self.covariance)

    def q2(self,residual):
        x=_finite(residual,(self.p,))
        return float(x@np.linalg.solve(self.covariance,x))

    def tail(self,residual):
        q=self.q2(residual)
        return {"q2":q,"df":self.p,"lower":float(stats.chi2.cdf(q,self.p)),
                "upper":float(stats.chi2.sf(q,self.p)),"status":"EXACT_IN_DECLARED_IDEAL_GAUSSIAN_MODEL"}

    def logpdf(self,residual):
        return float(stats.multivariate_normal.logpdf(residual,cov=self.covariance))

    def radius2(self,coverage=.95):
        if not 0<coverage<1:raise ValueError("coverage must lie between zero and one")
        return float(stats.chi2.ppf(coverage,self.p))


def angular_logpdf(direction,scatter):
    """ACG density on the directed sphere; zero-mean elliptical laws only.

    A positive common unknown unit cancels. This is an angular predictive
    density, not a frequentist PTE and not a mean-parameter likelihood after
    replacing direction with a parameter-dependent residual direction.
    """
    x=_finite(direction);s=_finite(scatter,(len(x),len(x)))
    if x.ndim!=1 or np.linalg.norm(x)==0 or not np.allclose(s,s.T):
        raise ValueError("nonzero vector and positive symmetric scatter required")
    np.linalg.cholesky(s);u=x/np.linalg.norm(x);p=len(x)
    area_log=math.log(2)+p/2*math.log(math.pi)-special.gammaln(p/2)
    return float(-area_log-.5*np.linalg.slogdet(s)[1]-p/2*np.log(u@np.linalg.solve(s,u)))


def occupation_of_inner_body(center, shape, radius2,
                             body_radius=ADMISSIBLE_INNER_RADIUS):
    """Volume occupancy of an ellipsoid in a declared admissible radiation body.

    Uniform Lebesgue measure in the retained STF subspace. The reference body
    is the inscribed ball, NOT the full positive-radiation cone and NOT a
    prior/posterior probability. The contained case has an exact volume ratio.
    A noncontained intersection is deliberately not estimated by this function.
    """
    m, s = _finite(center), _finite(shape)
    eig = np.linalg.eigvalsh(s)
    if s.shape != (len(m), len(m)) or eig[0] <= 0 or radius2 <= 0 or body_radius <= 0:
        raise ValueError("positive ellipsoid and body required")
    max_norm_bound = np.linalg.norm(m) + math.sqrt(radius2*eig[-1])
    if max_norm_bound > body_radius:
        return {"status": "INTERSECTION_NOT_COMPUTED", "max_norm_bound": max_norm_bound}
    log_ratio = len(m)/2*math.log(radius2) + .5*np.linalg.slogdet(s)[1] - len(m)*math.log(body_radius)
    unit_volume = math.pi**(len(m)/2)/special.gamma(len(m)/2+1)
    denominator = unit_volume*body_radius**len(m)
    return {"status": "CONDITIONAL_VOLUME_OCCUPANCY", "F": math.exp(log_ratio),
            "log_F": log_ratio, "dimension": len(m), "body_radius": body_radius,
            "numerator_volume": math.exp(log_ratio)*denominator,
            "denominator_volume": denominator,
            "max_norm_bound": max_norm_bound,
            "measure": "uniform Lebesgue volume on the declared retained STF subspace",
            "support": "certified admissible inscribed radiation-stress ball",
            "interpretation": "ellipsoid volume fraction; not probability of a cosmology"}


def five_views(q_uk, draws_uk, template_uk=DQ_UK, *, known_covariance_uk2=None):
    """Retain full signed data, quotient, reference covariance and all definitions."""
    q = _finite(q_uk, (5,))
    draws = _finite(draws_uk)
    if draws.ndim != 2 or draws.shape[1] != 5:
        raise ValueError("draws must have shape (N,5)")
    u = quotient_basis(template_uk)
    x = STRESS_PER_UK * (u.T @ q)
    samples = STRESS_PER_UK * (draws @ u)
    if known_covariance_uk2 is None:
        ref = ConditionalReference.from_draws(samples)
        full = ConditionalReference.from_draws(STRESS_PER_UK * draws)
        covariance_definition="X.T@X/N, not sample-centered"
    else:
        cov=_finite(known_covariance_uk2,(5,5))
        ref=KnownGaussianReference(STRESS_PER_UK**2*(u.T@cov@u))
        full=KnownGaussianReference(STRESS_PER_UK**2*cov)
        covariance_definition="analytically propagated ideal Gaussian covariance; MC rows validate only"
    r2 = ref.radius2()
    occupancy=occupation_of_inner_body(x,ref.covariance,r2)
    occupancy.update({"target":"conditional mean-stress linear-proxy ellipsoid",
                      "exact_realized_sky_physical_F":"UNAVAILABLE_WITHOUT_SPECTRAL_AND_MISSING_MODE_COMPLETION"})
    return {"x": {"full_stf_uK": q.tolist(), "quotient_stf5_uK": (u @ (u.T @ q)).tolist(),
                   "quotient4_pi_linear_over_rho0": x.tolist(),
                   "quotient4_pi_linear_Pa": (x*RHO0_SI).tolist(),
                   "U_5x4": u.tolist(), "covariance4": ref.covariance.tolist(),
                   "physical_target": "linearized realized quadrupole-sector radiation stress",
                   "likelihood_target": "deterministic mean stress plus stochastic processed CMB background",
                   "unidentified": "one scalar amplitude along the declared post-release DQ template"},
            "Q": {"value": float(np.linalg.norm(x)/PHYSICAL_OUTER_RADIUS),
                  "denominator": PHYSICAL_OUTER_RADIUS,
                  "meaning": "linear proxy normalized by exact pi/rho positivity outer bound",
                  "status": "LINEAR_PROXY_REQUIRES_SPECTRAL_AND_REMAINDER_QUALIFICATION"},
            "Pi": {"quotient": ref.tail(x), "full5": full.tail(STRESS_PER_UK*q),
                   "reference_rows": len(draws), "known_population_mean": "zero",
                   "covariance_definition": covariance_definition,
                   "warning": "No measurement-error likelihood or unconditional cosmological PTE"},
            "F": occupancy,
            "G_F": {"status": "NOT_APPLICABLE", "reason": "one last-scattering sky; no depth-resolved F law"},
            "conditional_logpdf_zero_mean": ref.logpdf(x), "radius2_95": r2,
            "five_views_add_information": False}


def paired_operator_weights(training: np.ndarray, design: np.ndarray):
    """Learn a unit-response GLS map on training MC only; retain shared-sky C.

    Calibration must use separate held-out rows. R58 supplies the conventional
    GLS geometry; none of its fixed-covariance p-values is reused here.
    This is not a new optimality result or guaranteed variance improvement.
    """
    x,j=_finite(training),_finite(design)
    if x.ndim!=2 or j.ndim!=2 or x.shape[1]!=j.shape[0] or len(x)<=x.shape[1]:
        raise ValueError("sufficient paired training rows and compatible design required")
    s=x.T@x/len(x)
    if np.linalg.cond(s)>1e12:
        raise ValueError("paired covariance is numerically unresolved; no automatic regularization")
    fit=fit_linear(np.zeros(x.shape[1]),s,j)
    if fit['rank']!=j.shape[1]:raise ValueError("physical mean target is unidentified")
    w=fit['covariance']@np.linalg.solve(s,j).T
    if not np.allclose(w@j,np.eye(j.shape[1]),rtol=1e-10,atol=1e-10):
        raise ValueError("unit physical response failed")
    return w,s


def power_tensor_quadrupole(q_uk):
    """Conventional l=2 power tensor on the SAME signed input (Aluri–Patel Eq2).

    This is a method comparison, not reproduction of their inpainted map/null.
    Its invariance under q -> -q makes it insufficient for signed mean stress.
    """
    q=_finite(q_uk,(5,));k=math.sqrt(8*math.pi/15)
    d=k*np.array([-q[1],-q[3],-q[4],q[0],q[2]])
    positive=[complex(d[0]),(d[1]-1j*d[2])/math.sqrt(2),(d[3]-1j*d[4])/math.sqrt(2)]
    a=np.array([positive[2].conjugate(),-positive[1].conjugate(),*positive])
    m=np.arange(-2,3);jp=np.zeros((5,5),complex)
    for col in range(4):jp[col+1,col]=math.sqrt(6-m[col]*(m[col]+1))
    j=[(jp+jp.T.conj())/2,(jp-jp.T.conj())/(2j),np.diag(m)]
    tensor=np.array([[(a.conj()@ji@jj@a).real/30 for jj in j] for ji in j])
    tensor=(tensor+tensor.T)/2
    eig=np.linalg.eigvalsh(tensor);trace=float(np.trace(tensor))
    if trace==0:return {'tensor_uK2':tensor,'eigenvalues_uK2':eig,'C2_uK2':trace,'entropy':None}
    frac=np.maximum(eig/trace,0);nz=frac>0
    return {'tensor_uK2':tensor,'eigenvalues_uK2':eig,'C2_uK2':trace,
            'entropy':float(-np.sum(frac[nz]*np.log(frac[nz])))}


def nonlinear_remainder(theta, weights):
    """Exact retained-sky T^4 nonlinear term and a deterministic norm bound.

    This is NOT a bound on unknown foregrounds, missing multipoles or unknown
    spectral distortions. Those require a separately supplied completion bound.
    """
    t, w = _finite(theta), _finite(weights)
    if t.shape != w.shape or np.any(w < 0) or not np.isclose(w.sum(), 1) or np.any(1+t <= 0):
        raise ValueError("positive temperature and normalized positive measure required")
    rem = 6*t*t + 4*t**3 + t**4
    bound = math.sqrt(2/3) * float(w @ np.abs(rem))
    cubic_bound = math.sqrt(2/3) * float(w @ (4*np.abs(t)**3 + t**4))
    return {"norm_bound_nonlinear_over_rho0": bound,
            "norm_bound_after_quadratic_over_rho0": cubic_bound,
            "max_abs_theta_retained": float(np.max(abs(t)))}


def missing_mode_bound(low_sup: float, missing_sup: float, missing_l2: float,
                       missing_is_orthogonal_to_ell2: bool = True) -> float:
    """A full-sky stress remainder bound when ||h||inf and rms(h) are supplied.

    |(1+l+h)^4-(1+l)^4-4h| <=
       4*((1+e)^3-1)|h| + 6*(1+e)^2*h^2
       + 4*(1+e)*|h|^3 + h^4, for |l|<=e.
    The 4h stress integral vanishes only for full-sky ell2-orthogonal h.
    """
    e, a, r = map(float, (low_sup, missing_sup, missing_l2))
    if min(e, a, r) < 0 or not np.isfinite([e,a,r]).all() or r > a:
        raise ValueError("finite 0<=rms(h)<=sup(h) bounds required")
    bound = 4*((1+e)**3-1)*r + (6*(1+e)**2+4*(1+e)*a+a*a)*r*r
    if not missing_is_orthogonal_to_ell2:
        bound += 4*r
    return math.sqrt(2/3)*bound

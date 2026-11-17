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

    @classmethod
    def from_draws(cls, draws):
        x = _finite(draws)
        if x.ndim != 2 or len(x) <= x.shape[1]:
            raise ValueError("N must exceed the carrier dimension")
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
    return {"status": "CONDITIONAL_VOLUME_OCCUPANCY", "F": math.exp(log_ratio),
            "log_F": log_ratio, "dimension": len(m), "body_radius": body_radius,
            "max_norm_bound": max_norm_bound,
            "measure": "uniform Lebesgue volume on the declared retained STF subspace",
            "support": "certified admissible inscribed radiation-stress ball",
            "interpretation": "ellipsoid volume fraction; not probability of a cosmology"}


def five_views(q_uk, draws_uk, template_uk=DQ_UK):
    """Retain full signed data, quotient, reference covariance and all definitions."""
    q = _finite(q_uk, (5,))
    draws = _finite(draws_uk)
    if draws.ndim != 2 or draws.shape[1] != 5:
        raise ValueError("draws must have shape (N,5)")
    u = quotient_basis(template_uk)
    x = STRESS_PER_UK * (u.T @ q)
    samples = STRESS_PER_UK * (draws @ u)
    ref = ConditionalReference.from_draws(samples)
    full = ConditionalReference.from_draws(STRESS_PER_UK * draws)
    r2 = ref.radius2()
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
                   "covariance_definition": "X.T@X/N, not sample-centered",
                   "warning": "No measurement-error likelihood or unconditional cosmological PTE"},
            "F": occupation_of_inner_body(x, ref.covariance, r2),
            "G_F": {"status": "NOT_APPLICABLE", "reason": "one last-scattering sky; no depth-resolved F law"},
            "conditional_logpdf_zero_mean": ref.logpdf(x), "radius2_95": r2,
            "five_views_add_information": False}


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

"""R54 tensorized five-view calculus for signed linear-Gaussian carriers in precision form.

A carrier is the pair (F, t): precision (Fisher) matrix and score vector of
    -2 ln L(theta) = theta^T F theta - 2 t^T theta + const.
F may be singular. Its null space is the set of unidentified directions; it is
reported and never regularized by an unstated prior.

Views (all derived from the same carrier; none adds information to it):

x    the signed carrier itself (F, t) with typed coordinates;
Q    gauge p_K0(theta) = inf{r > 0 : theta in r K0} of a DECLARED body K0, and its
     range [Q_min, Q_max] over the confidence set (R54-EQ-20);
F    directional support utilization h_Theta(v) / h_K0(v) (R54-EQ-21);
Pi   exceedance / tail probability under an explicitly NAMED law (R54-EQ-22);
G_F  transport of one irreducible carrier across depths: a GLS test of
     y_k = tau_k x + noise with the full cross-depth covariance (R54-EQ-23).

R54-EQ-20  Theta_c = {theta : (theta - m)^T F (theta - m) <= c^2},  F m = t.
           Q_min = min_{Theta_c} p_K0,  Q_max = max_{Theta_c} p_K0 (= +inf if F is singular).
R54-EQ-21  h_S(v) = sup_{theta in S} v.theta;  h_K0(v) = sqrt(v^T B v) for K0 = {theta^T B^-1 theta <= 1}.
           Duality (polar bodies):  Q_min = sup_v [-h_Theta(-v)]_+ / h_K0(v),  Q_max = sup_v h_Theta(v) / h_K0(v).
R54-EQ-22  Pi = P[stat >= stat_obs | named law]; a law name is mandatory.
R54-EQ-23  chi2_transport = min_x (y - (tau (x) I) x)^T C^-1 (y - (tau (x) I) x), dof = d (K - 1).

Finite-sample (posterior-draw) five-variable records remain owned by
``htt/src/common/htt_five_variable_state.py`` and ``typefree_functionals.py``;
this module only adds closed forms for the linear-Gaussian carrier.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np
from scipy import optimize, stats

_S2, _S6 = 1.0 / math.sqrt(2.0), 1.0 / math.sqrt(6.0)
#: Orthonormal STF5 basis, ordering identical to r52_joint_identification.STF_BASIS.
STF5_BASIS = np.array([
    [[_S2, 0, 0], [0, -_S2, 0], [0, 0, 0]],
    [[_S6, 0, 0], [0, _S6, 0], [0, 0, -2 * _S6]],
    [[0, _S2, 0], [_S2, 0, 0], [0, 0, 0]],
    [[0, 0, _S2], [0, 0, 0], [_S2, 0, 0]],
    [[0, 0, 0], [0, 0, _S2], [0, _S2, 0]],
])
VIEW_NAMES = ("x", "Q", "F", "Pi", "G_F")
AVAILABLE, UNAVAILABLE = "AVAILABLE", "UNAVAILABLE"


def _sym(a: np.ndarray, name: str) -> np.ndarray:
    a = np.asarray(a, float)
    if a.ndim != 2 or a.shape[0] != a.shape[1] or not np.isfinite(a).all():
        raise ValueError(f"{name} must be a finite square matrix")
    if not np.allclose(a, a.T, rtol=1e-9, atol=1e-12 * max(1.0, float(np.abs(a).max()))):
        raise ValueError(f"{name} must be symmetric")
    return 0.5 * (a + a.T)


# ----------------------------------------------------------------- STF tensors
def stf5_to_matrix(q: np.ndarray) -> np.ndarray:
    q = np.asarray(q, float)
    if q.shape != (5,):
        raise ValueError("STF5 vector must have shape (5,)")
    return np.einsum("k,kij->ij", q, STF5_BASIS)


def matrix_to_stf5(m: np.ndarray) -> np.ndarray:
    m = _sym(m, "tensor")
    if m.shape != (3, 3) or abs(np.trace(m)) > 1e-10 * max(1.0, float(np.abs(m).max())):
        raise ValueError("tensor must be 3x3 symmetric trace-free")
    return np.einsum("kij,ij->k", STF5_BASIS, m)


def quadratic_direction(n: np.ndarray) -> np.ndarray:
    """v_k = n^T e_k n, so that n^T M n = q . v for M = stf5_to_matrix(q); |v|^2 = 2/3."""
    n = np.asarray(n, float)
    n = n / np.linalg.norm(n)
    return np.einsum("i,kij,j->k", n, STF5_BASIS, n)


def axisymmetric_stf5(n: np.ndarray) -> np.ndarray:
    """Unit-norm STF5 coordinates of sqrt(3/2) (n n^T - I/3)."""
    return math.sqrt(1.5) * quadratic_direction(n)


def stf2_invariants(q: np.ndarray) -> dict:
    """Rotation invariants and eigenframe of a rank-2 STF tensor.

    shape = sqrt6 tr(M^3) / tr(M^2)^{3/2} in [-1, 1]: +1 one distinguished positive
    axis (prolate), -1 one distinguished negative axis (oblate), 0 maximally triaxial.
    """
    m = stf5_to_matrix(q)
    w, v = np.linalg.eigh(m)
    norm2 = float(np.sum(w**2))
    shape = float("nan") if norm2 == 0 else float(np.clip(math.sqrt(6.0) * np.sum(w**3) / norm2**1.5, -1.0, 1.0))
    k = int(np.argmax(np.abs(w)))
    return {"eigenvalues": w.tolist(), "frobenius_norm": math.sqrt(norm2), "shape": shape,
            "principal_axis": v[:, k].tolist(), "principal_eigenvalue": float(w[k])}


def fibonacci_sphere(n: int) -> np.ndarray:
    """n quasi-uniform unit vectors (deterministic)."""
    if n < 4:
        raise ValueError("need at least 4 directions")
    i = np.arange(n) + 0.5
    z = 1.0 - 2.0 * i / n
    phi = math.pi * (1.0 + math.sqrt(5.0)) * i
    r = np.sqrt(1.0 - z**2)
    return np.column_stack([r * np.cos(phi), r * np.sin(phi), z])


# ------------------------------------------------------------- identification
@dataclass(frozen=True)
class Identification:
    rank: int
    dim: int
    eigenvalues_scaled: tuple[float, ...]
    range_basis: np.ndarray      # columns, original coordinates
    null_basis: np.ndarray       # columns, original coordinates (unidentified directions)


def identify(f: np.ndarray, scale: np.ndarray | None = None, rtol: float = 1e-10) -> Identification:
    """Scaled-eigenvalue rank of a precision matrix; ``scale`` are typical parameter sizes."""
    f = _sym(f, "precision")
    d = np.ones(f.shape[0]) if scale is None else np.asarray(scale, float)
    if d.shape != (f.shape[0],) or (d <= 0).any():
        raise ValueError("scale must be positive with one entry per parameter")
    w, v = np.linalg.eigh(d[:, None] * f * d[None, :])
    if w[-1] <= 0:
        raise ValueError("precision matrix carries no information")
    if w[0] < -1e-8 * w[-1]:
        raise ValueError("precision matrix is not positive semi-definite")
    pos = w > rtol * w[-1]
    # theta = D phi: a null direction in phi maps to D v; a range covector maps to D^-1 v
    null = d[:, None] * v[:, ~pos]
    rng = v[:, pos] / d[:, None]
    null = null / np.linalg.norm(null, axis=0, keepdims=True) if null.size else null
    return Identification(int(pos.sum()), f.shape[0], tuple(float(x) for x in w), rng, null)


def is_identified(f: np.ndarray, v: np.ndarray, scale: np.ndarray | None = None, rtol: float = 1e-8) -> bool:
    """True iff the linear functional v.theta is fixed by the carrier (v orthogonal to null(F))."""
    ident = identify(f, scale)
    v = np.asarray(v, float)
    if ident.null_basis.size == 0:
        return True
    return bool(np.linalg.norm(ident.null_basis.T @ v) <= rtol * np.linalg.norm(v))


def profiled_precision(f: np.ndarray, keep: Sequence[int]) -> np.ndarray:
    """Schur complement F_kk - F_kr F_rr^+ F_rk: information on ``keep`` after profiling the rest."""
    f = _sym(f, "precision")
    keep = list(keep)
    rest = [i for i in range(f.shape[0]) if i not in keep]
    if not rest:
        return f[np.ix_(keep, keep)]
    frr = f[np.ix_(rest, rest)]
    return f[np.ix_(keep, keep)] - f[np.ix_(keep, rest)] @ np.linalg.pinv(frr, rcond=1e-12, hermitian=True) @ f[np.ix_(rest, keep)]


def carrier_mean(f: np.ndarray, t: np.ndarray, rtol: float = 1e-8) -> np.ndarray:
    """Minimum-norm solution of F m = t; raises if t has a component outside range(F)."""
    f = _sym(f, "precision")
    t = np.asarray(t, float)
    m = np.linalg.pinv(f, rcond=1e-12, hermitian=True) @ t
    if np.linalg.norm(f @ m - t) > rtol * max(np.linalg.norm(t), 1e-300):
        raise ValueError("score vector is inconsistent with the precision matrix")
    return m


# ------------------------------------------------------------------- body, Q
@dataclass(frozen=True)
class EllipsoidBody:
    """K0 = {theta : theta^T B^-1 theta <= 1}; ``name`` states the physical declaration."""

    name: str
    shape_matrix: np.ndarray

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("a body must be declared by name")
        b = _sym(self.shape_matrix, "body shape matrix")
        if np.linalg.eigvalsh(b)[0] <= 0:
            raise ValueError("body shape matrix must be positive definite")

    @classmethod
    def from_covariance(cls, name: str, cov: np.ndarray, level: float = 0.95) -> "EllipsoidBody":
        cov = _sym(cov, "covariance")
        return cls(name, stats.chi2.ppf(level, cov.shape[0]) * cov)

    def gauge(self, theta: np.ndarray) -> float:
        th = np.asarray(theta, float)
        return float(math.sqrt(max(th @ np.linalg.solve(self.shape_matrix, th), 0.0)))

    def support(self, v: np.ndarray) -> float:
        v = np.asarray(v, float)
        return float(math.sqrt(max(v @ self.shape_matrix @ v, 0.0)))


def gauge_range(f: np.ndarray, t: np.ndarray, body: EllipsoidBody, c2: float, rtol: float = 1e-10) -> dict:
    """[Q_min, Q_max] of the body gauge over Theta_c (R54-EQ-20). Singular F gives Q_max = inf."""
    f = _sym(f, "precision")
    t = np.asarray(t, float)
    if c2 < 0:
        raise ValueError("c2 must be non-negative")
    low = np.linalg.cholesky(_sym(body.shape_matrix, "body shape matrix"))
    a_mat = low.T @ f @ low
    a, vec = np.linalg.eigh(0.5 * (a_mat + a_mat.T))
    rhs = vec.T @ (low.T @ t)
    pos = a > rtol * a[-1]
    if np.linalg.norm(rhs[~pos]) > 1e-8 * max(np.linalg.norm(rhs), 1e-300):
        raise ValueError("score vector is inconsistent with the precision matrix")
    ap, nu = a[pos], rhs[pos] / a[pos]
    g0 = float(np.sum(ap * nu**2))                     # Mahalanobis^2 of the origin
    # ---- minimum (convex): w_i = lam a_i nu_i / (1 + lam a_i)
    if g0 <= c2:
        q_min, w_min = 0.0, np.zeros_like(nu)
    else:
        def g(lam: float) -> float:
            return float(np.sum(ap * nu**2 / (1.0 + lam * ap) ** 2)) - c2
        hi = 1.0 / ap.max()
        while g(hi) > 0:
            hi *= 2.0
        lam = optimize.brentq(g, 0.0, hi, xtol=1e-300, rtol=1e-14, maxiter=500)
        w_min = lam * ap * nu / (1.0 + lam * ap)
        q_min = float(np.linalg.norm(w_min))
    theta_min = low @ (vec[:, pos] @ w_min)
    # ---- maximum (trust-region on the boundary): w_i = lam a_i nu_i / (lam a_i - 1), lam > 1/a_min
    if (~pos).any():
        q_max = math.inf
    elif c2 == 0:
        q_max = float(np.linalg.norm(nu))
    else:
        a_min = ap.min()
        soft = ap > a_min * (1.0 + 1e-10)
        hard_free = bool(np.all(np.abs(nu[~soft]) <= 1e-12 * max(np.linalg.norm(nu), 1e-300)))
        h_lim = float(np.sum(ap[soft] * nu[soft] ** 2 / (ap[soft] / a_min - 1.0) ** 2)) if soft.any() else 0.0
        if hard_free and h_lim <= c2:                    # hard case: slack goes along the weakest axis
            w = np.zeros_like(nu)
            w[soft] = (ap[soft] / a_min) * nu[soft] / (ap[soft] / a_min - 1.0)
            q_max = float(math.sqrt(np.sum(w**2) + (c2 - h_lim) / a_min))
        else:
            def h(lam: float) -> float:
                return float(np.sum(ap * nu**2 / (lam * ap - 1.0) ** 2)) - c2
            lo = (1.0 / a_min) * (1.0 + 1e-13)
            while h(lo) < 0:                             # nu on the weakest axis is tiny but non-zero
                lo = 1.0 / a_min + (lo - 1.0 / a_min) * 1e-3
                if lo - 1.0 / a_min < 1e-300:
                    break
            hi = 2.0 / a_min
            while h(hi) > 0:
                hi *= 2.0
            lam = optimize.brentq(h, lo, hi, xtol=1e-300, rtol=1e-14, maxiter=500)
            q_max = float(np.linalg.norm(lam * ap * nu / (lam * ap - 1.0)))
    return {"body": body.name, "c2": float(c2), "Q_min": q_min, "Q_max": q_max,
            "Q_center": float(np.linalg.norm(nu)) if pos.all() else None,
            "origin_mahalanobis2": g0, "theta_at_Q_min": theta_min.tolist(),
            "unidentified_dimensions": int((~pos).sum())}


# ------------------------------------------------------------------------- F
def support_interval(f: np.ndarray, t: np.ndarray, v: np.ndarray, c: float,
                     scale: np.ndarray | None = None) -> tuple[float, float]:
    """(inf, sup) of v.theta over Theta_c; (-inf, inf) when v.theta is not identified."""
    v = np.asarray(v, float)
    if not is_identified(f, v, scale):
        return (-math.inf, math.inf)
    pinv = np.linalg.pinv(_sym(f, "precision"), rcond=1e-12, hermitian=True)
    centre = float(v @ pinv @ np.asarray(t, float))
    half = c * math.sqrt(max(float(v @ pinv @ v), 0.0))
    return (centre - half, centre + half)


def support_utilization(f: np.ndarray, t: np.ndarray, body: EllipsoidBody, v: np.ndarray, c: float,
                        scale: np.ndarray | None = None) -> dict:
    """F-view (R54-EQ-21) for one dual direction v.

    F_lower > 1: the whole confidence set lies beyond the body along v (certified excess).
    F_upper < 1: the data bound is tighter than the body along v.
    """
    lo, hi = support_interval(f, t, v, c, scale)
    h0 = body.support(v)
    if h0 <= 0:
        raise ValueError("body has zero support along v")
    return {"body": body.name, "F_lower": lo / h0, "F_upper": hi / h0, "identified": math.isfinite(hi)}


# ------------------------------------------------------------------------ Pi
def finite_mc_sd_inflation(n_sims: int, p_data: int, k_par: int) -> float:
    """sd of a GLS estimate built with a sample covariance from N simulations, relative to its plug-in sd.

    With S ~ Wishart_p(n, Sigma)/n, n = N - 1, and theta = (J^T S^-1 J)^-1 J^T S^-1 d:
      Var(theta)              = (n - 1)/(n - p + k - 1) (J^T Sigma^-1 J)^-1          (sampling of S inflates the scatter)
      E[(J^T S^-1 J)^-1]      = (n - p + k)/n          (J^T Sigma^-1 J)^-1          (the plug-in variance is biased low)
    so  true sd / plug-in sd  = sqrt[ n (n - 1) / ((n - p + k)(n - p + k - 1)) ],   equal to 1 for p = k.
    The R53 expression sqrt[(N-1)/(N-p-2) (N-2)/(N-p+k-1)] is conservative (1.166 instead of 1.155 for N=300, p=45, k=5;
    the R51 leave-one-out ratio is 1.155)."""
    n = n_sims - 1.0
    m = n - p_data + k_par
    if k_par > p_data or m - 1.0 <= 0:
        raise ValueError("need k <= p and N > p - k + 2")
    return math.sqrt(n * (n - 1.0) / (m * (m - 1.0)))


def hotelling_null_tail(stat: float, p_dim: int, n_sims: int) -> dict:
    """Tail of y^T S^-1 y for y ~ N(0, Sigma) and S a sample covariance from N simulations."""
    n = n_sims - 1
    if n - p_dim + 1 <= 0:
        raise ValueError("need N > p")
    f_stat = stat * (n - p_dim + 1.0) / (n * p_dim)
    return {"law": f"hotelling_T2(p={p_dim},n={n})", "statistic": float(stat), "p_value": float(stats.f.sf(f_stat, p_dim, n - p_dim + 1))}


def chi2_null_tail(stat: float, dof: int, law: str) -> dict:
    if not law.strip():
        raise ValueError("a law name is mandatory")
    return {"law": law, "statistic": float(stat), "dof": int(dof), "p_value": float(stats.chi2.sf(stat, dof))}


def empirical_upper_tail(obs: float, null_values: np.ndarray, law: str) -> dict:
    """(k+1)/(n+1) with a Clopper-Pearson 95% interval on the underlying tail."""
    if not law.strip():
        raise ValueError("a law name is mandatory")
    x = np.asarray(null_values, float)
    n, k = int(x.size), int(np.sum(x >= obs))
    lo = 0.0 if k == 0 else float(stats.beta.ppf(0.025, k, n - k + 1))
    hi = 1.0 if k == n else float(stats.beta.ppf(0.975, k + 1, n - k))
    return {"law": law, "statistic": float(obs), "n_null": n, "n_exceed": k, "p_value": (k + 1.0) / (n + 1.0),
            "clopper_pearson_95": [lo, hi]}


def gauge_exceedance_gaussian(mean: np.ndarray, cov: np.ndarray, body: EllipsoidBody, eps: float,
                              n_draw: int = 200_000, seed: int = 20261116) -> dict:
    """P[p_K0(theta) > eps] for theta ~ N(mean, cov) (seeded Monte Carlo with binomial error)."""
    cov = _sym(cov, "covariance")
    rng = np.random.default_rng(seed)
    draws = rng.multivariate_normal(np.asarray(mean, float), cov, size=n_draw, method="cholesky")
    binv = np.linalg.inv(body.shape_matrix)
    g2 = np.einsum("ni,ij,nj->n", draws, binv, draws)
    p = float(np.mean(g2 > eps**2))
    return {"law": "gaussian_carrier_posterior_flat_prior", "body": body.name, "eps": float(eps), "p_value": p,
            "mc_se": math.sqrt(max(p * (1 - p), 1e-300) / n_draw), "n_draw": n_draw, "seed": seed}


# ----------------------------------------------------------------------- G_F
def gls_fit(y: np.ndarray, cov: np.ndarray, design: np.ndarray) -> dict:
    """Generalized least squares with a full covariance; chi2 and dof of the residual."""
    y, cov, design = np.asarray(y, float), _sym(cov, "covariance"), np.asarray(design, float)
    if design.ndim != 2 or design.shape[0] != y.size or np.linalg.matrix_rank(design) < design.shape[1]:
        raise ValueError("design must have full column rank and match the data")
    ci = np.linalg.inv(cov)
    fisher = design.T @ ci @ design
    pcov = np.linalg.inv(fisher)
    theta = pcov @ design.T @ ci @ y
    res = y - design @ theta
    chi2 = float(res @ ci @ res)
    dof = int(y.size - design.shape[1])
    return {"theta": theta, "cov": pcov, "chi2": chi2, "dof": dof,
            "p_value": float(stats.chi2.sf(chi2, dof)) if dof > 0 else float("nan"),
            "wald": float(theta @ fisher @ theta)}


def transport_design(tau: Sequence[float], dim: int) -> np.ndarray:
    """Design of y_k = tau_k x for K depths and one irreducible carrier x of dimension ``dim``."""
    tau = np.asarray(tau, float)
    return np.kron(tau[:, None], np.eye(dim))


def compare_transport_models(y: np.ndarray, cov: np.ndarray, designs: Mapping[str, np.ndarray]) -> dict:
    """Residual chi2 of the null and of each named transport law on the same data and covariance."""
    y, cov = np.asarray(y, float), _sym(cov, "covariance")
    null = float(y @ np.linalg.solve(cov, y))
    out = {"null": {"chi2": null, "dof": int(y.size), "p_value": float(stats.chi2.sf(null, y.size))}}
    for name, design in designs.items():
        fit = gls_fit(y, cov, design)
        out[name] = {"chi2": fit["chi2"], "dof": fit["dof"], "p_value": fit["p_value"], "n_par": int(design.shape[1]),
                     "delta_chi2_vs_null": null - fit["chi2"], "theta": fit["theta"].tolist(),
                     "theta_sd": np.sqrt(np.diag(fit["cov"])).tolist()}
    return out


# ------------------------------------------------- STF2 eigen-structure (L4)
def axisymmetry_statistic(q_hat: np.ndarray, f5: np.ndarray, n_grid: int = 600) -> dict:
    """min over axisymmetric tensors a*sqrt(3/2)(nn - I/3) of (q - q_axi)^T F (q - q_axi)."""
    q_hat, f5 = np.asarray(q_hat, float), _sym(f5, "precision")

    def profile(n: np.ndarray) -> tuple[float, float]:
        e = axisymmetric_stf5(n)
        amp = float(e @ f5 @ q_hat) / float(e @ f5 @ e)
        r = q_hat - amp * e
        return float(r @ f5 @ r), amp

    grid = fibonacci_sphere(n_grid)
    vals = np.array([profile(n)[0] for n in grid])
    n0 = grid[int(np.argmin(vals))]
    th0 = [math.acos(float(np.clip(n0[2], -1, 1))), math.atan2(n0[1], n0[0])]

    def obj(x: np.ndarray) -> float:
        return profile(np.array([math.sin(x[0]) * math.cos(x[1]), math.sin(x[0]) * math.sin(x[1]), math.cos(x[0])]))[0]

    sol = optimize.minimize(obj, th0, method="Nelder-Mead", options={"xatol": 1e-9, "fatol": 1e-12, "maxiter": 4000})
    n = np.array([math.sin(sol.x[0]) * math.cos(sol.x[1]), math.sin(sol.x[0]) * math.sin(sol.x[1]), math.cos(sol.x[0])])
    stat, amp = profile(n)
    return {"statistic": stat, "axis": n.tolist(), "amplitude": amp}


def five_view_record(views: Mapping[str, Mapping]) -> dict:
    """Validate and normalise a five-view record.

    Fail-closed rules: every view is present; an AVAILABLE Q or F names its body;
    an AVAILABLE Pi names its law; an UNAVAILABLE view states a reason.
    """
    out: dict = {}
    for name in VIEW_NAMES:
        if name not in views:
            raise ValueError(f"view {name} missing")
        v = dict(views[name])
        status = v.get("status")
        if status not in (AVAILABLE, UNAVAILABLE):
            raise ValueError(f"view {name}: status must be AVAILABLE or UNAVAILABLE")
        if status == UNAVAILABLE and not str(v.get("reason", "")).strip():
            raise ValueError(f"view {name}: UNAVAILABLE requires a reason")
        if status == AVAILABLE and name in ("Q", "F") and not str(v.get("body", "")).strip():
            raise ValueError(f"view {name}: AVAILABLE requires a declared body")
        if status == AVAILABLE and name == "Pi" and not str(v.get("law", "")).strip():
            raise ValueError("view Pi: AVAILABLE requires a named law")
        out[name] = v
    return out

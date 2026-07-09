"""EGS3 Axis E: identified-set reporting for the signed comparator x_C (P26/P31/P35, A8).

Operational resolution of the P1 x P18 tension: the comparator x_C = c^T g,
c = (+1, -1, +1, +1), needs all four components of g = (Sigma^2, W^2, Omega_tilt,
Omega_k_aniso), but the registered scalar/radial response reaches only a rank-2
subspace (W^2 and Omega_k are exact structural nulls of the channel design). The
reportable object is therefore NOT a point value but the identified set

    G(y) = { g : ||y - R g||^2 <= tau,  lower <= g <= upper }

and its image under c^T, the closed interval [x_C^-, x_C^+].

Two-stage tau semantics (P35). A single tau conflates two different degrees of
freedom. Stage 1 uses the m - r residual directions (orthogonal to col(R)) as a
SPECIFICATION TEST at level alpha1: if the residual statistic exceeds the stage-1
threshold the feasible set is EMPTY and the correct report is a misfit/refutation
status, not an interval. Stage 2 places a conditional ellipsoid on the r reachable
directions. The default threshold policy is the original known-covariance chi-square
branch; an explicit estimated-covariance Hotelling/F branch is available when the
covariance is simulation-estimated. alpha2 = 1.0 gives tau2 = 0, i.e. the POPULATION
identified set (no sampling inflation).

Status semantics (A8), in precedence order:
  ``empty``         -- stage-1 misfit, or the stage-2 ellipsoid misses the cone
                       (refutability: the model class is rejected, by design);
  ``unbounded``     -- a null direction with c_j != 0 carries no MES ceiling, so an
                       endpoint is infinite and the honest report is no-result;
  ``ceiling_unfit`` -- max(0, x_C^+)/U_C > 1: the certified-filling ceiling U_C is
                       inconsistent with the feasible set (F > 1 clip);
  ``feasible``      -- a finite sharp interval [x_lo, x_hi] is reported.

Endpoint uncertainty (P35 / Imbens-Manski). The interval endpoints are extrema of a
random set; a CI for the PARAMETER x_C needs the Imbens-Manski critical value C_N
solving Phi(C_N + Delta_hat / max(se)) - Phi(-C_N) = 1 - alpha (Imbens & Manski
2004; Stoye 2009 -- external-context citations). The naive per-endpoint one-sided
z_{1-alpha} construction UNDERCOVERS as the interval width Delta -> 0; the
set-coverage projection construction (z_{1-alpha/2}) is conservative for the
parameter. Both are implemented as explicit foils.

Domain restriction (honest): this module requires the null space of R to be spanned
by ZERO COLUMNS (axis-aligned nulls). That is exactly the registered case -- the
channel design of `egs3_graded_comparator.channel_response_design` has identically
zero W^2 and Omega_k columns -- and anything more general raises NotImplementedError
rather than silently extrapolating.

Domain discipline. Component bounds are signed boxes. Nonnegativity is a branch
choice, not a global theorem: the registered open-curvature branch uses
Omega_k_aniso in [0, U_k], while the all-curvature branch uses [-U_k, U_k].

Claim discipline. Diagnostic-only, synthetic-witness statistics machinery. It is a
SEPARATE DIAGNOSTIC SURFACE: it never touches the bit-identical comparator x_C,
the response design, or the frozen registered low-ell statistic set, and it adds no
new registered statistic. No detection, family/geometry, native-solver, or posterior
claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np
from scipy import optimize, stats

STATUS_FEASIBLE = "feasible"
STATUS_EMPTY = "empty"
STATUS_UNBOUNDED = "unbounded"
STATUS_CEILING_UNFIT = "ceiling_unfit"

__all__ = [
    "STATUS_FEASIBLE", "STATUS_EMPTY", "STATUS_UNBOUNDED", "STATUS_CEILING_UNFIT",
    "TwoStageTau", "two_stage_tau",
    "IdentifiedSetReport", "identified_set_report",
    "curvature_branch_bounds", "signed_curvature_branch_reports",
    "reachable_endpoints_closed_form",
    "im_critical_value", "im_interval", "projection_interval", "endpoint_interval",
    "ImCoverageResult", "im_coverage_experiment",
    "RefutabilityPower", "refutability_power_experiment",
    "toy_design",
]


@dataclass(frozen=True)
class TwoStageTau:
    """The two thresholds of the P35 construction.

    ``known_chi2`` preserves the original API and values. ``estimated_covariance_f``
    applies the finite-simulation Hotelling/F correction separately to each stage.
    """
    m: int
    r: int
    alpha1: float
    alpha2: float
    tau1: float
    tau2: float
    threshold_policy: str = "known_chi2"
    n_sim: int | None = None
    threshold_value: float = math.nan
    df_residual: int = 0
    df_reachable: int = 0


def two_stage_tau(m: int, r: int, *, alpha1: float = 0.05,
                  alpha2: float = 0.05,
                  threshold_policy: str = "known_chi2",
                  n_sim: int | None = None) -> TwoStageTau:
    """tau1 = chi^2_{m-r, 1-alpha1} (stage-1 specification test on the residual
    directions) and tau2 = chi^2_{r, 1-alpha2} (stage-2 conditional reachable
    ellipsoid). alpha2 = 1.0 -> tau2 = 0 -> population identified set.

    With ``threshold_policy="estimated_covariance_f"``, use
    df * (n_sim - 1) / (n_sim - df) * F_{df, n_sim-df, 1-alpha}, which is the
    fail-closed finite-simulation branch requested by the v7 audit.
    """
    m = int(m); r = int(r)
    if not (0 < r < m):
        raise ValueError("need 0 < r < m for the two-stage split")
    if not (0.0 < alpha1 < 1.0) or not (0.0 < alpha2 <= 1.0):
        raise ValueError("alpha1 in (0,1); alpha2 in (0,1]")
    policy = str(threshold_policy)
    df_residual = m - r
    df_reachable = r

    def _estimated_cov_threshold(df: int, alpha: float) -> float:
        if n_sim is None:
            raise ValueError("n_sim is required for estimated_covariance_f")
        n = int(n_sim)
        if n <= df + 1:
            raise ValueError("estimated_covariance_f requires n_sim > df + 1")
        return float(df * (n - 1) / (n - df) * stats.f.ppf(1.0 - alpha, df, n - df))

    if policy == "known_chi2":
        if n_sim is not None:
            raise ValueError("n_sim is only meaningful for estimated_covariance_f")
        tau1 = float(stats.chi2.ppf(1.0 - alpha1, df_residual))
        tau2 = 0.0 if alpha2 == 1.0 else float(stats.chi2.ppf(1.0 - alpha2, df_reachable))
    elif policy == "estimated_covariance_f":
        tau1 = _estimated_cov_threshold(df_residual, alpha1)
        tau2 = 0.0 if alpha2 == 1.0 else _estimated_cov_threshold(df_reachable, alpha2)
    else:
        raise ValueError("threshold_policy must be known_chi2 or estimated_covariance_f")
    return TwoStageTau(m=m, r=r, alpha1=float(alpha1), alpha2=float(alpha2),
                       tau1=tau1, tau2=tau2, threshold_policy=policy,
                       n_sim=None if n_sim is None else int(n_sim),
                       threshold_value=tau1, df_residual=df_residual,
                       df_reachable=df_reachable)


@dataclass(frozen=True)
class IdentifiedSetReport:
    """A8 report: status + interval + provenance of both stages."""
    status: str
    x_lo: float
    x_hi: float
    reachable_lo: float
    reachable_hi: float
    null_lo: float
    null_hi: float
    spec_stat: float
    spec_threshold: float
    spec_pass: bool
    rank: int
    m: int
    F_lo: float | None
    F_hi: float | None
    tau: TwoStageTau
    branch_id: str = "unspecified"
    component_bounds: tuple = ()
    input_modes: tuple = ()
    observational_claim_allowed: bool = False
    threshold_policy: str = "known_chi2"
    n_sim: int | None = None
    df_residual: int = 0
    df_reachable: int = 0


def _split_columns(R: np.ndarray, tol: float) -> tuple[np.ndarray, np.ndarray]:
    """Active (nonzero) vs null (identically zero) column indices."""
    col_norm = np.linalg.norm(R, axis=0)
    active = np.flatnonzero(col_norm > tol)
    null = np.flatnonzero(col_norm <= tol)
    return active, null


def reachable_endpoints_closed_form(A: np.ndarray, y: np.ndarray, c_R: np.ndarray,
                                    tau2: float) -> tuple[float, float]:
    """Cone-free (box-ignored) endpoints of c_R^T g over the reachable ellipsoid
    {g : ||A g - y||^2 <= s1 + tau2}: c_R^T g_hat -/+ sqrt(tau2 c_R^T (A^T A)^{-1} c_R).

    Independent cross-check route for the constrained optimiser (chain-of-code);
    coincides with it whenever the box constraints are inactive."""
    A = np.asarray(A, dtype=float); y = np.asarray(y, dtype=float)
    c_R = np.asarray(c_R, dtype=float)
    gram_inv = np.linalg.inv(A.T @ A)
    g_hat = gram_inv @ (A.T @ y)
    centre = float(c_R @ g_hat)
    half = math.sqrt(max(float(tau2), 0.0) * float(c_R @ gram_inv @ c_R))
    return centre - half, centre + half


def _constrained_extreme(A: np.ndarray, y: np.ndarray, c_R: np.ndarray,
                         level: float, lo: np.ndarray, hi: np.ndarray,
                         x0: np.ndarray, sense: float) -> float:
    """min (sense=+1) / max (sense=-1) of c_R^T g over ellipsoid  box via SLSQP."""
    def objective(g: np.ndarray) -> float:
        return sense * float(c_R @ g)

    def objective_jac(g: np.ndarray) -> np.ndarray:
        return sense * c_R

    def constraint(g: np.ndarray) -> float:
        resid = A @ g - y
        return level - float(resid @ resid)

    def constraint_jac(g: np.ndarray) -> np.ndarray:
        return -2.0 * (A.T @ (A @ np.asarray(g, dtype=float) - y))

    bounds = [(float(l), None if not np.isfinite(u) else float(u))
              for l, u in zip(lo, hi)]
    res = optimize.minimize(
        objective, x0, jac=objective_jac, method="SLSQP", bounds=bounds,
        constraints=[{"type": "ineq", "fun": constraint, "jac": constraint_jac}],
        options={"maxiter": 300, "ftol": 1e-14},
    )
    return sense * float(res.fun)


def identified_set_report(y, R, c, lower, upper, *, alpha1: float = 0.05,
                          alpha2: float = 0.05, ceiling_U: float | None = None,
                          tol: float = 1e-10,
                          threshold_policy: str = "known_chi2",
                          n_sim: int | None = None,
                          branch_id: str = "unspecified",
                          input_modes: tuple | list | None = None,
                          observational_claim_allowed: bool = False
                          ) -> IdentifiedSetReport:
    """Compute the A8 identified-set report for whitened observations y = R g + eps.

    Parameters: y (m,) whitened data; R (m,p) response; c (p,) signed comparator
    coefficients; lower/upper (p,) signed component bounds (np.inf = no ceiling).
    """
    y = np.asarray(y, dtype=float).ravel()
    R = np.asarray(R, dtype=float)
    c = np.asarray(c, dtype=float).ravel()
    lower = np.asarray(lower, dtype=float).ravel()
    upper = np.asarray(upper, dtype=float).ravel()
    m, p = R.shape
    if not (y.shape == (m,) and c.shape == (p,) and lower.shape == (p,)
            and upper.shape == (p,)):
        raise ValueError("shape mismatch between y, R, c, lower, upper")
    if np.any(lower > upper):
        raise ValueError("lower bounds must not exceed upper bounds")

    active, null = _split_columns(R, tol)
    A = R[:, active]
    r = int(np.linalg.matrix_rank(A, tol=tol * max(1.0, float(np.max(np.abs(A))))))
    if r != active.size:
        raise NotImplementedError(
            "identified_set_report requires axis-aligned nulls: the null space of R "
            "must be spanned by zero columns (the registered rank-2 case)")

    tau = two_stage_tau(m, r, alpha1=alpha1, alpha2=alpha2,
                        threshold_policy=threshold_policy, n_sim=n_sim)

    # Stage 1: specification test on the m - r residual directions.
    g_hat, *_ = np.linalg.lstsq(A, y, rcond=None)
    resid = y - A @ g_hat
    s1 = float(resid @ resid)
    spec_pass = s1 <= tau.tau1

    # Null-box contribution to x_C (exact: null columns never touch the data).
    null_lo = 0.0
    null_hi = 0.0
    unbounded = False
    for j in null:
        cj = c[j]
        if cj == 0.0:
            continue
        contrib = sorted((cj * lower[j], cj * upper[j]))
        if not np.isfinite(contrib[0]):
            unbounded = True
        if not np.isfinite(contrib[1]):
            unbounded = True
        null_lo += contrib[0]
        null_hi += contrib[1]

    empty = not spec_pass
    reach_lo = math.nan
    reach_hi = math.nan
    if spec_pass:
        # Stage 2: cone-constrained feasibility on the reachable directions.
        level = s1 + tau.tau2
        lsq = optimize.lsq_linear(A, y, bounds=(lower[active], upper[active]))
        min_cost = float(2.0 * lsq.cost)          # lsq_linear cost = 0.5 ||Ax-b||^2
        if min_cost > level + tol:
            empty = True
        else:
            c_R = c[active]
            x0 = np.asarray(lsq.x, dtype=float)
            reach_lo = _constrained_extreme(A, y, c_R, level, lower[active],
                                            upper[active], x0, sense=+1.0)
            reach_hi = _constrained_extreme(A, y, c_R, level, lower[active],
                                            upper[active], x0, sense=-1.0)

    if empty:
        status = STATUS_EMPTY
        x_lo = math.nan
        x_hi = math.nan
        F_lo = F_hi = None
    else:
        x_lo = reach_lo + null_lo
        x_hi = reach_hi + null_hi
        if unbounded:
            status = STATUS_UNBOUNDED
            F_lo = F_hi = None
        else:
            F_lo = F_hi = None
            status = STATUS_FEASIBLE
            if ceiling_U is not None:
                U = float(ceiling_U)
                if U <= 0.0:
                    raise ValueError("ceiling_U must be positive")
                F_lo = max(0.0, x_lo) / U
                F_hi = max(0.0, x_hi) / U
                if F_hi > 1.0:
                    status = STATUS_CEILING_UNFIT

    return IdentifiedSetReport(
        status=status, x_lo=x_lo, x_hi=x_hi,
        reachable_lo=reach_lo, reachable_hi=reach_hi,
        null_lo=null_lo, null_hi=null_hi,
        spec_stat=s1, spec_threshold=tau.tau1, spec_pass=spec_pass,
        rank=r, m=m, F_lo=F_lo, F_hi=F_hi, tau=tau,
        branch_id=str(branch_id),
        component_bounds=tuple((float(lo), float(hi)) for lo, hi in zip(lower, upper)),
        input_modes=tuple(input_modes or ()),
        observational_claim_allowed=bool(observational_claim_allowed),
        threshold_policy=tau.threshold_policy,
        n_sim=tau.n_sim,
        df_residual=tau.df_residual,
        df_reachable=tau.df_reachable,
    )


def curvature_branch_bounds(lower, upper, *, curvature_index: int = 3,
                            branch: str = "open") -> tuple[np.ndarray, np.ndarray, str]:
    """Return signed curvature branch bounds without mutating the input arrays.

    ``open`` keeps Omega_k_aniso in [0, U_k]. ``all`` permits signed curvature
    [-U_k, U_k]. This is branch metadata for diagnostic identified sets, not a
    family-identification or geometry claim.
    """
    lo = np.asarray(lower, dtype=float).copy()
    hi = np.asarray(upper, dtype=float).copy()
    j = int(curvature_index)
    if not (0 <= j < lo.size):
        raise ValueError("curvature_index out of range")
    u = float(hi[j])
    if not np.isfinite(u) or u < 0.0:
        raise ValueError("curvature upper bound must be finite and nonnegative")
    if branch == "open":
        lo[j] = 0.0
        hi[j] = u
        branch_id = "open_branch[0,Uk]"
    elif branch == "all":
        lo[j] = -u
        hi[j] = u
        branch_id = "all_branch[-Uk,Uk]"
    else:
        raise ValueError("branch must be open or all")
    return lo, hi, branch_id


def signed_curvature_branch_reports(y, R, c, lower, upper, *, curvature_index: int = 3,
                                    branches=("open", "all"), **kwargs
                                    ) -> dict[str, IdentifiedSetReport]:
    """Compute identified-set reports for the requested signed curvature branches."""
    reports: dict[str, IdentifiedSetReport] = {}
    for branch in branches:
        lo, hi, branch_id = curvature_branch_bounds(
            lower, upper, curvature_index=curvature_index, branch=str(branch))
        reports[branch_id] = identified_set_report(
            y, R, c, lo, hi, branch_id=branch_id, **kwargs)
    return reports


# ---------------------------------------------------------------------------
# Imbens-Manski endpoint semantics (P35)
# ---------------------------------------------------------------------------

def im_critical_value(delta_hat: float, se_max: float, alpha: float = 0.05) -> float:
    """C_N solving Phi(C_N + delta_hat/se_max) - Phi(-C_N) = 1 - alpha.

    Interpolates between the one-sided z_{1-alpha} (wide interval, delta >> se) and
    the two-sided z_{1-alpha/2} (point-identified limit, delta = 0)."""
    delta_hat = max(float(delta_hat), 0.0)
    alpha = float(alpha)
    if not (0.0 < alpha < 1.0):
        raise ValueError("alpha in (0,1)")
    if se_max <= 0.0:
        return float(stats.norm.ppf(1.0 - alpha))
    ratio = delta_hat / float(se_max)

    def f(cn: float) -> float:
        return stats.norm.cdf(cn + ratio) - stats.norm.cdf(-cn) - (1.0 - alpha)

    return float(optimize.brentq(f, 0.0, 10.0, xtol=1e-12))


def im_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                alpha: float = 0.05) -> tuple[float, float, float]:
    """Imbens-Manski CI for the PARAMETER: [x_lo - C_N se_lo, x_hi + C_N se_hi]."""
    cn = im_critical_value(x_hi - x_lo, max(float(se_lo), float(se_hi)), alpha)
    return float(x_lo) - cn * float(se_lo), float(x_hi) + cn * float(se_hi), cn


def projection_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                        alpha: float = 0.05) -> tuple[float, float]:
    """Set-coverage projection CI (z_{1-alpha/2} per endpoint): covers the whole
    identified set, hence CONSERVATIVE for the scalar parameter."""
    z = float(stats.norm.ppf(1.0 - alpha / 2.0))
    return float(x_lo) - z * float(se_lo), float(x_hi) + z * float(se_hi)


def endpoint_interval(x_lo: float, x_hi: float, se_lo: float, se_hi: float,
                      alpha: float = 0.05) -> tuple[float, float]:
    """Naive per-endpoint one-sided z_{1-alpha} CI: the UNDERCOVERING foil -- its
    coverage of a boundary point drops to 1 - 2 alpha as the width Delta -> 0."""
    z = float(stats.norm.ppf(1.0 - alpha))
    return float(x_lo) - z * float(se_lo), float(x_hi) + z * float(se_hi)


# ---------------------------------------------------------------------------
# Registered r = 2, m = 6 toy (reproduces the section-10 example [0.11, 0.17])
# ---------------------------------------------------------------------------

def toy_design(m: int = 6, *, curvature_branch: str = "open") -> dict:
    """The registered toy: g = (Sigma2, W2, Omega_tilt, Omega_k); W2 and Omega_k are
    zero columns (structural nulls); truth (0.12, 0, 0.03, 0); MES ceilings
    U_W = 0.04, U_k = 0.02. Population identified interval = [0.11, 0.17]."""
    if m < 4:
        raise ValueError("need m >= 4 for the two-stage toy")
    R = np.zeros((m, 4))
    # two orthogonal reachable channels spread over the m rows
    R[: m // 2, 0] = 1.0                     # Sigma2 rows
    R[m // 2:, 2] = 1.0                      # Omega_tilt rows
    c = np.array([1.0, -1.0, 1.0, 1.0])
    lower = np.zeros(4)
    upper = np.array([np.inf, 0.04, np.inf, 0.02])
    if curvature_branch == "all":
        lower[3] = -upper[3]
    elif curvature_branch != "open":
        raise ValueError("curvature_branch must be open or all")
    g_true = np.array([0.12, 0.0, 0.03, 0.0])
    return {"R": R, "c": c, "lower": lower, "upper": upper, "g_true": g_true}


@dataclass(frozen=True)
class ImCoverageResult:
    n_mc: int
    seed: int
    alpha: float
    delta_over_sigma: float
    coverage_projection: float
    coverage_im: float
    coverage_endpoint: float
    se_binomial: float
    cn_im: float


def im_coverage_experiment(*, n_mc: int = 2000, seed: int = 20260708,
                           alpha: float = 0.05,
                           delta_over_sigma: float = 0.5) -> ImCoverageResult:
    """MC coverage of the three endpoint constructions at a boundary point.

    The r = 2, m = 6 toy: both interval endpoints derive from the SAME reachable
    estimate c_R^T g_hat (perfectly correlated endpoint noise -- exactly the regime
    where the IM equation is tight). Truth = the UPPER population endpoint (worst
    case). delta_over_sigma sets the interval-width-to-endpoint-se ratio; small
    values expose the naive endpoint construction's undercoverage."""
    toy = toy_design()
    A = toy["R"][:, [0, 2]]
    c_R = np.array([1.0, 1.0])
    gram_inv = np.linalg.inv(A.T @ A)
    unit_se = math.sqrt(float(c_R @ gram_inv @ c_R))

    null_lo = -0.04     # c_W * U_W
    null_hi = +0.02     # c_k * U_k
    delta = null_hi - null_lo
    sigma_noise = delta / (float(delta_over_sigma) * unit_se)
    se = sigma_noise * unit_se

    x_pt_true = float(c_R @ toy["g_true"][[0, 2]])
    theta = x_pt_true + null_hi              # upper endpoint = worst case

    rng = np.random.default_rng(seed)
    hits_proj = hits_im = hits_end = 0
    cn = im_critical_value(delta, se, alpha)
    for _ in range(int(n_mc)):
        eps = rng.normal(size=A.shape[0]) * sigma_noise
        g_hat, *_ = np.linalg.lstsq(A, A @ toy["g_true"][[0, 2]] + eps, rcond=None)
        x_pt = float(c_R @ g_hat)
        x_lo = x_pt + null_lo
        x_hi = x_pt + null_hi
        lo, hi = projection_interval(x_lo, x_hi, se, se, alpha)
        hits_proj += int(lo <= theta <= hi)
        lo, hi, _ = im_interval(x_lo, x_hi, se, se, alpha)
        hits_im += int(lo <= theta <= hi)
        lo, hi = endpoint_interval(x_lo, x_hi, se, se, alpha)
        hits_end += int(lo <= theta <= hi)

    n = float(n_mc)
    cov_im = hits_im / n
    se_bin = math.sqrt(max(cov_im * (1.0 - cov_im), 1e-12) / n)
    return ImCoverageResult(
        n_mc=int(n_mc), seed=int(seed), alpha=float(alpha),
        delta_over_sigma=float(delta_over_sigma),
        coverage_projection=hits_proj / n, coverage_im=cov_im,
        coverage_endpoint=hits_end / n, se_binomial=se_bin, cn_im=cn,
    )


@dataclass(frozen=True)
class RefutabilityPower:
    amplitudes: tuple
    empty_rate: tuple
    se: tuple
    alpha1: float
    n_mc: int
    seed: int


def refutability_power_experiment(amplitudes=(0.0, 1.0, 2.0, 3.0, 4.0, 6.0), *,
                                  n_mc: int = 1000, seed: int = 20260708,
                                  alpha1: float = 0.05) -> RefutabilityPower:
    """Empty-set rate under injected misspecification = specification-test power.

    y = R g_true + eps + a u with u a unit vector orthogonal to col(R): the stage-1
    residual statistic is noncentral chi^2_{m-r}(a^2), so the empty rate at a = 0 is
    alpha1 by construction (size) and rises monotonically with a (power). This is
    the refutability FEATURE of the identified-set semantics, not a defect."""
    toy = toy_design()
    R = toy["R"]; g_true = toy["g_true"]
    A = R[:, [0, 2]]
    m = R.shape[0]
    q, _ = np.linalg.qr(A, mode="complete")
    u = q[:, -1]                              # unit vector orthogonal to col(A)
    tau = two_stage_tau(m, 2, alpha1=alpha1, alpha2=0.05)
    proj = A @ np.linalg.inv(A.T @ A) @ A.T
    perp = np.eye(m) - proj

    rng = np.random.default_rng(seed)
    rates = []
    ses = []
    for a in amplitudes:
        n_empty = 0
        for _ in range(int(n_mc)):
            y = A @ g_true[[0, 2]] + rng.normal(size=m) + float(a) * u
            s1 = float(y @ perp @ y)
            n_empty += int(s1 > tau.tau1)
        rate = n_empty / float(n_mc)
        rates.append(rate)
        ses.append(math.sqrt(max(rate * (1.0 - rate), 1e-12) / float(n_mc)))
    return RefutabilityPower(
        amplitudes=tuple(float(a) for a in amplitudes),
        empty_rate=tuple(rates), se=tuple(ses),
        alpha1=float(alpha1), n_mc=int(n_mc), seed=int(seed),
    )

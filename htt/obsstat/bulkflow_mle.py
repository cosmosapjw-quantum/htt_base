"""LR-06D / PR08-002: weighted-Gaussian bulk-flow estimator for a peculiar-velocity catalog.

Model: each group i has a radial peculiar velocity Vpec_i along its line of sight
unit vector n_i, with Gaussian error sigma_i. The bulk flow B (a 3-vector) is the
weighted Gaussian maximum-likelihood (generalized-least-squares) estimator

    A = sum_i n_i n_i^T / sigma_i^2 ,   b = sum_i n_i Vpec_i / sigma_i^2 ,
    B_hat = A^{-1} b ,                  Cov(B_hat) = A^{-1} .

(PR07-006 wording: this is the weighted-Gaussian MLE/GLS under the stated error
model, not a distribution-free minimum-variance estimator; the inverse-Fisher
covariance is *conditional* on that error model and the fixed sigma_star.)

sigma_i combines the distance-modulus velocity error and an intrinsic 1D
dispersion sigma_star added in quadrature. The PR08-002 ``fit_hierarchical_bulk``
extends this to a random-effect / fixed-nuisance design that jointly profiles
sigma_star and method/group offsets; cosmic variance is *not* included and must
come from release-matched forward mocks (PR08-003, BLOCKED_MISSING_RELEASE_MOCK_OWNERSHIP).

This is observer-side feature extraction (OBSSTAT): a kinematic descriptor, not a
model evidence, and not a global-tilt or Bianchi-geometry claim.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np

LN10_OVER_5 = np.log(10.0) / 5.0


@dataclass(frozen=True)
class BulkFlow:
    vector: np.ndarray        # B_hat (km/s), Cartesian
    covariance: np.ndarray    # Cov(B_hat) (km/s)^2
    amplitude: float          # |B_hat| (km/s)
    amplitude_error: float    # 1-sigma on |B|
    n_groups: int
    sigma_star: float

    def as_dict(self) -> dict:
        return {"vector_kms": self.vector.tolist(), "amplitude_kms": self.amplitude,
                "amplitude_error_kms": self.amplitude_error, "n_groups": self.n_groups,
                "sigma_star_kms": self.sigma_star,
                "covariance": self.covariance.tolist()}


def velocity_error(e_dm: np.ndarray, v_cosmo: np.ndarray) -> np.ndarray:
    """Peculiar-velocity error from the distance-modulus uncertainty:
    sigma_v = (ln10/5) * e_DM * V_cosmo (the log-distance-ratio error)."""
    return LN10_OVER_5 * np.asarray(e_dm, dtype=float) * np.abs(np.asarray(v_cosmo, dtype=float))


def estimate_bulk_flow(unit_vectors: np.ndarray, vpec: np.ndarray, sigma: np.ndarray,
                       sigma_star: float = 250.0) -> BulkFlow:
    n = np.asarray(unit_vectors, dtype=float)
    v = np.asarray(vpec, dtype=float)
    s = np.asarray(sigma, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3 or v.shape[0] != n.shape[0]:
        raise ValueError("unit_vectors (N,3), vpec (N,) required")
    w = 1.0 / (s * s + sigma_star * sigma_star)
    A = np.einsum("i,ij,ik->jk", w, n, n)
    b = np.einsum("i,ij->j", w * v, n)
    cov = np.linalg.inv(A)
    B = cov @ b
    amp = float(np.linalg.norm(B))
    # error on amplitude: project covariance onto the B direction.
    if amp > 0:
        u = B / amp
        amp_err = float(np.sqrt(u @ cov @ u))
    else:
        amp_err = float(np.sqrt(np.trace(cov) / 3.0))
    return BulkFlow(B, cov, amp, amp_err, int(n.shape[0]), float(sigma_star))


def fit_sigma_star(unit_vectors: np.ndarray, vpec: np.ndarray, sigma_meas: np.ndarray,
                   grid: np.ndarray | None = None) -> float:
    """Pick sigma_star so the reduced chi^2 of the bulk-flow residual is ~1."""
    if grid is None:
        grid = np.linspace(50.0, 600.0, 56)
    n = np.asarray(unit_vectors, dtype=float)
    v = np.asarray(vpec, dtype=float)
    best, best_obj = float(grid[0]), np.inf
    for ss in grid:
        bf = estimate_bulk_flow(n, v, sigma_meas, sigma_star=ss)
        resid = v - n @ bf.vector
        w = 1.0 / (sigma_meas ** 2 + ss ** 2)
        chi2_red = float(np.sum(w * resid ** 2) / (len(v) - 3))
        if abs(chi2_red - 1.0) < best_obj:
            best_obj, best = abs(chi2_red - 1.0), float(ss)
    return best


def forward_mock_coverage(unit_vectors: np.ndarray, sigma: np.ndarray, b_true: np.ndarray,
                          sigma_star: float, n_mock: int = 400, seed: int = 7) -> dict:
    """Inject b_true, draw noisy mocks with the real geometry+errors, recover, and
    report the 1-sigma coverage of the injected amplitude."""
    n = np.asarray(unit_vectors, dtype=float)
    s = np.asarray(sigma, dtype=float)
    b_true = np.asarray(b_true, dtype=float)
    rng = np.random.default_rng(seed)
    amp_true = float(np.linalg.norm(b_true))
    covered = 0
    recovered = []
    tot = np.sqrt(s ** 2 + sigma_star ** 2)
    for _ in range(n_mock):
        v = n @ b_true + rng.normal(0.0, tot)
        bf = estimate_bulk_flow(n, v, s, sigma_star=sigma_star)
        recovered.append(bf.amplitude)
        if abs(bf.amplitude - amp_true) <= bf.amplitude_error:
            covered += 1
    return {"injected_amplitude_kms": amp_true, "n_mock": int(n_mock),
            "recovered_mean_kms": float(np.mean(recovered)),
            "recovered_std_kms": float(np.std(recovered, ddof=1)),
            "one_sigma_coverage": covered / n_mock}


# ---------------------------------------------------------------------------
# PR08-002: hierarchical weighted-GLS mechanics (random method/group effects +
# fixed nuisance design + profiled sigma_star). Marginal Gaussian model:
#
#   y = N B + W alpha + Z delta + epsilon,
#   delta ~ N(0, T),   epsilon ~ N(0, diag(sigma_meas^2 + sigma_star^2)).
#
# Measurement, mock-calibrated, and cosmic-variance covariance are reported
# *separately*; this standalone path validates mechanics only (no cosmic
# variance / no release-specific Malmquist model).
# ---------------------------------------------------------------------------
from scipy.linalg import cho_factor, cho_solve  # noqa: E402
from scipy.optimize import minimize_scalar  # noqa: E402


@dataclass(frozen=True)
class HierarchicalFit:
    coefficients: np.ndarray
    covariance: np.ndarray       # conditional inverse-Fisher (measurement-model only)
    sigma_star: float
    loglike: float
    bulk: np.ndarray
    bulk_covariance: np.ndarray


def _hier_covariance(measurement_sigma: np.ndarray, sigma_star: float,
                     Z: np.ndarray | None, tau: np.ndarray | None) -> np.ndarray:
    s = np.asarray(measurement_sigma, dtype=float).reshape(-1)
    if sigma_star < 0.0:
        raise ValueError("sigma_star must be nonnegative")
    C = np.diag(s * s + sigma_star * sigma_star)
    if Z is not None:
        z = np.asarray(Z, dtype=float)
        t = np.asarray(tau, dtype=float).reshape(-1)
        if z.shape[1] != t.size:
            raise ValueError("tau must match Z columns")
        C = C + (z * (t * t)[None, :]) @ z.T
    return C


def _profile_fixed_sigma(y: np.ndarray, X: np.ndarray, C: np.ndarray):
    cf = cho_factor(C, lower=True, check_finite=True)
    cinv_x = cho_solve(cf, X)
    cinv_y = cho_solve(cf, y)
    fisher = X.T @ cinv_x
    covariance = np.linalg.inv(fisher)
    beta = covariance @ (X.T @ cinv_y)
    residual = y - X @ beta
    quad = float(residual @ cho_solve(cf, residual))
    logdet = 2.0 * float(np.sum(np.log(np.diag(cf[0]))))
    loglike = -0.5 * (quad + logdet + y.size * np.log(2.0 * np.pi))
    return beta, covariance, loglike


def fit_hierarchical_bulk(y: np.ndarray, directions: np.ndarray, measurement_sigma: np.ndarray, *,
                          fixed_nuisance: np.ndarray | None = None,
                          random_design: np.ndarray | None = None,
                          random_scale: np.ndarray | None = None,
                          sigma_star_bounds: tuple[float, float] = (1e-3, 600.0)) -> HierarchicalFit:
    """Profile sigma_star in the marginal Gaussian likelihood and return the GLS fit.

    Stable marginalization uses the Cholesky factor of the Woodbury-form
    covariance ``diag(sigma_meas^2 + sigma_star^2) + Z T Z^T``.
    """
    y = np.asarray(y, dtype=float).reshape(-1)
    n = np.asarray(directions, dtype=float)
    n = n / np.linalg.norm(n, axis=1)[:, None]
    W = np.empty((y.size, 0)) if fixed_nuisance is None else np.asarray(fixed_nuisance, dtype=float)
    X = np.concatenate([n, W], axis=1)

    def objective(log_sigma: float) -> float:
        sigma = float(np.exp(log_sigma))
        C = _hier_covariance(measurement_sigma, sigma, random_design, random_scale)
        _, _, ll = _profile_fixed_sigma(y, X, C)
        return -ll

    lower, upper = sigma_star_bounds
    result = minimize_scalar(objective, bounds=(np.log(lower), np.log(upper)),
                             method="bounded", options={"xatol": 1e-6})
    if not result.success:
        raise RuntimeError("sigma_star profile optimization failed")
    sigma_star = float(np.exp(result.x))
    C = _hier_covariance(measurement_sigma, sigma_star, random_design, random_scale)
    beta, covariance, loglike = _profile_fixed_sigma(y, X, C)
    return HierarchicalFit(beta, covariance, sigma_star, loglike, beta[:3], covariance[:3, :3])


def _hier_naive_bulk(y: np.ndarray, directions: np.ndarray, measurement_sigma: np.ndarray,
                     sigma_star: float) -> HierarchicalFit:
    y = np.asarray(y, dtype=float)
    n = np.asarray(directions, dtype=float)
    n = n / np.linalg.norm(n, axis=1)[:, None]
    C = _hier_covariance(measurement_sigma, sigma_star, None, None)
    beta, covariance, loglike = _profile_fixed_sigma(y, n, C)
    return HierarchicalFit(beta, covariance, float(sigma_star), loglike, beta, covariance)


def hierarchical_coverage_experiment(*, simulations: int = 160, objects: int = 260,
                                     methods: int = 5, seed: int = 20260625) -> dict:
    """Synthetic mechanics-only coverage test (PR08-002).

    The synthetic catalogue deliberately introduces a method-dependent angular
    selection pattern so that ignoring calibration creates component-specific
    undercoverage in the naive fit, which the random-effect model repairs.
    """
    rng = np.random.default_rng(seed)
    true_bulk = np.array([180.0, -95.0, 70.0])
    true_sigma_star = 145.0
    method_tau = np.linspace(35.0, 70.0, methods)
    cover_naive_68 = np.zeros(3); cover_hier_68 = np.zeros(3)
    cover_naive_95 = np.zeros(3); cover_hier_95 = np.zeros(3)
    sigma_hats = []; biases_naive = []; biases_hier = []
    for _ in range(simulations):
        raw = rng.normal(size=(objects, 3)); raw[:, 2] += 0.35
        directions = raw / np.linalg.norm(raw, axis=1)[:, None]
        depth = np.exp(rng.uniform(np.log(20.0), np.log(220.0), size=objects))
        method_id = rng.integers(0, methods, size=objects)
        Z = np.eye(methods)[method_id]
        depth_basis = ((1.0 / depth) - np.mean(1.0 / depth))[:, None]
        W = np.concatenate([np.ones((objects, 1)), depth_basis], axis=1)
        meas_sigma = rng.uniform(80.0, 180.0, size=objects)
        method_offsets = rng.normal(scale=method_tau)
        fixed = np.array([25.0, 4800.0])
        mean = directions @ true_bulk + W @ fixed + method_offsets[method_id]
        y = mean + rng.normal(scale=np.sqrt(meas_sigma ** 2 + true_sigma_star ** 2))
        naive = _hier_naive_bulk(y, directions, meas_sigma, true_sigma_star)
        hier = fit_hierarchical_bulk(y, directions, meas_sigma, fixed_nuisance=W,
                                     random_design=Z, random_scale=method_tau,
                                     sigma_star_bounds=(20.0, 350.0))
        for fit, c68, c95, store in [(naive, cover_naive_68, cover_naive_95, biases_naive),
                                     (hier, cover_hier_68, cover_hier_95, biases_hier)]:
            se = np.sqrt(np.diag(fit.bulk_covariance)); delta = fit.bulk - true_bulk
            c68 += (np.abs(delta) <= se); c95 += (np.abs(delta) <= 1.96 * se)
            store.append(delta)
        sigma_hats.append(hier.sigma_star)

    def frac(x: np.ndarray) -> list[float]:
        return (x / simulations).tolist()
    return {
        "schema": "htt.pr08_002.k5_hierarchical.coverage.v1",
        "simulations": int(simulations), "objects_per_mock": int(objects),
        "true_bulk_km_s": true_bulk.tolist(), "true_sigma_star_km_s": true_sigma_star,
        "naive_component_coverage_68": frac(cover_naive_68),
        "naive_component_coverage_95": frac(cover_naive_95),
        "hierarchical_component_coverage_68": frac(cover_hier_68),
        "hierarchical_component_coverage_95": frac(cover_hier_95),
        "naive_mean_bias_km_s": np.mean(np.asarray(biases_naive), axis=0).tolist(),
        "hierarchical_mean_bias_km_s": np.mean(np.asarray(biases_hier), axis=0).tolist(),
        "sigma_star_mean_km_s": float(np.mean(sigma_hats)),
        "scope": "mechanics-only synthetic validation; no cosmic variance or release-specific Malmquist model",
    }

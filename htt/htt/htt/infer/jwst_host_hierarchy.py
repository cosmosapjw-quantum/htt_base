"""PR-154 JWST paired-host hierarchy and covariance envelope.

The two authenticated source families are deliberately independent products.
The computational model works with paired method contrasts, which is exactly
the Schur-complement reduction of a latent-host model.  Unknown shared
covariance is represented by a fixed-diagonal PSD uncertainty set; diagonal
independence is a sensitivity point only.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import itertools
import math
from typing import Iterable, Sequence

import numpy as np
from scipy.optimize import brentq
from scipy.special import gammaln, logsumexp, ndtr, roots_genlaguerre
from scipy.stats import chi2


class JWSTHierarchyError(ValueError):
    """Raised when PR-154 inputs or registered numerical gates fail."""


@dataclass(frozen=True)
class HostPair:
    dataset: str
    host: str
    method_a: str
    mu_a_mag: float
    sigma_a_mag: float
    method_b: str
    mu_b_mag: float
    sigma_b_mag: float

    @property
    def delta_mag(self) -> float:
        return self.mu_a_mag - self.mu_b_mag

    @property
    def independence_variance_mag2(self) -> float:
        return self.sigma_a_mag ** 2 + self.sigma_b_mag ** 2


FAMILY_CONTRACTS = {
    "cchp_trgb_jagb": {"n": 7, "method_a": "JAGB", "method_b": "TRGB",
                        "contrast": "JAGB_minus_TRGB_mag"},
    "shoes_jwst_hst": {"n": 13, "method_a": "JWST", "method_b": "HST",
                        "contrast": "JWST_minus_HST_mag"},
}


def validate_pairs(pairs: Sequence[HostPair], dataset: str) -> tuple[HostPair, ...]:
    if dataset not in FAMILY_CONTRACTS:
        raise JWSTHierarchyError(f"unknown source family: {dataset}")
    contract = FAMILY_CONTRACTS[dataset]
    rows = tuple(pairs)
    if len(rows) != contract["n"]:
        raise JWSTHierarchyError(
            f"{dataset} requires exactly {contract['n']} hosts, got {len(rows)}"
        )
    hosts = [row.host for row in rows]
    if len(set(hosts)) != len(hosts):
        raise JWSTHierarchyError(f"duplicate host in {dataset}")
    for row in rows:
        values = (row.mu_a_mag, row.sigma_a_mag, row.mu_b_mag, row.sigma_b_mag)
        if (row.dataset != dataset or row.method_a != contract["method_a"]
                or row.method_b != contract["method_b"]):
            raise JWSTHierarchyError(f"method/sign contract mismatch for {row.host}")
        if not all(math.isfinite(value) for value in values):
            raise JWSTHierarchyError(f"non-finite host row: {row.host}")
        if row.sigma_a_mag <= 0 or row.sigma_b_mag <= 0:
            raise JWSTHierarchyError(f"non-positive uncertainty: {row.host}")
    return rows


def latent_gls_offset(pairs: Sequence[HostPair]) -> float:
    """GLS method contrast from the explicit latent-host design."""
    n = len(pairs)
    design = np.zeros((2 * n, n + 1), dtype=float)
    values = np.empty(2 * n, dtype=float)
    variances = np.empty(2 * n, dtype=float)
    for index, row in enumerate(pairs):
        design[2 * index, index] = 1.0
        design[2 * index + 1, index] = 1.0
        design[2 * index, -1] = 0.5
        design[2 * index + 1, -1] = -0.5
        values[2 * index:2 * index + 2] = (row.mu_a_mag, row.mu_b_mag)
        variances[2 * index:2 * index + 2] = (
            row.sigma_a_mag ** 2, row.sigma_b_mag ** 2
        )
    precision = np.diag(1.0 / variances)
    normal = design.T @ precision @ design
    rhs = design.T @ precision @ values
    solution = np.linalg.solve(normal, rhs)
    return float(solution[-1])


def collapsed_gls_offset(pairs: Sequence[HostPair]) -> float:
    deltas = np.asarray([row.delta_mag for row in pairs])
    variances = np.asarray([row.independence_variance_mag2 for row in pairs])
    weights = 1.0 / variances
    return float(weights @ deltas / weights.sum())


def method_cell_covariance(pairs: Sequence[HostPair], q: float,
                           block: str) -> np.ndarray:
    """Registered fixed-diagonal PSD method-cell covariance slice."""
    if q < 0 or q > 1 or not math.isfinite(q):
        raise JWSTHierarchyError("q must lie in [0,1]")
    n = len(pairs)
    scales = np.asarray(list(itertools.chain.from_iterable(
        (row.sigma_a_mag, row.sigma_b_mag) for row in pairs
    )), dtype=float)
    size = 2 * n
    if block == "global_all_cell_factor":
        base = np.ones((size, size), dtype=float)
    elif block in {"method_block_factor", "authenticated_group_block_factor"}:
        base = np.zeros((size, size), dtype=float)
        even = np.arange(0, size, 2)
        odd = np.arange(1, size, 2)
        base[np.ix_(even, even)] = 1.0
        base[np.ix_(odd, odd)] = 1.0
    else:
        raise JWSTHierarchyError(f"unknown covariance block: {block}")
    correlation = (1.0 - q) * np.eye(size) + q * base
    covariance = scales[:, None] * correlation * scales[None, :]
    validate_psd_covariance(covariance, scales ** 2)
    return covariance


def contrast_matrix(n: int) -> np.ndarray:
    matrix = np.zeros((n, 2 * n), dtype=float)
    for index in range(n):
        matrix[index, 2 * index] = 1.0
        matrix[index, 2 * index + 1] = -1.0
    return matrix


def contrast_covariance(method_covariance: np.ndarray) -> np.ndarray:
    if method_covariance.ndim != 2 or method_covariance.shape[0] != method_covariance.shape[1]:
        raise JWSTHierarchyError("method covariance must be square")
    if method_covariance.shape[0] % 2:
        raise JWSTHierarchyError("method covariance dimension must be even")
    transform = contrast_matrix(method_covariance.shape[0] // 2)
    result = transform @ method_covariance @ transform.T
    validate_psd_covariance(result, np.diag(result), check_diagonal=False)
    return result


def validate_psd_covariance(covariance: np.ndarray, expected_diagonal: np.ndarray,
                            *, check_diagonal: bool = True) -> None:
    covariance = np.asarray(covariance, dtype=float)
    if not np.all(np.isfinite(covariance)):
        raise JWSTHierarchyError("covariance is non-finite")
    if not np.allclose(covariance, covariance.T, rtol=0.0, atol=1e-12):
        raise JWSTHierarchyError("covariance symmetry gate failed")
    if check_diagonal and not np.allclose(
            np.diag(covariance), expected_diagonal, rtol=0.0, atol=1e-12):
        raise JWSTHierarchyError("covariance diagonal gate failed")
    if float(np.linalg.eigvalsh(covariance).min()) < -1e-10:
        raise JWSTHierarchyError("covariance PSD gate failed")


def fixed_diagonal_mean_se_bounds(
        pairs: Sequence[HostPair]) -> dict[str, float | str]:
    cell_lengths = np.asarray([
        sigma / len(pairs) for row in pairs
        for sigma in (row.sigma_a_mag, row.sigma_b_mag)
    ])
    lengths = np.sqrt([row.independence_variance_mag2 for row in pairs]) / len(pairs)
    maximum = float(lengths.sum())
    minimum = float(max(0.0, 2.0 * lengths.max() - lengths.sum()))
    independence = float(np.sqrt(np.square(lengths).sum()))
    full_maximum = float(cell_lengths.sum())
    full_minimum = float(max(
        0.0, 2.0 * cell_lengths.max() - cell_lengths.sum()
    ))
    return {
        "minimum_se_mag": minimum,
        "independence_se_mag": independence,
        "maximum_se_mag": maximum,
        "maximum_over_independence": maximum / independence,
        "scope": "reduced_contrast_diagonal_fixed_to_independence_approximation",
        "analytic_basis": "Gram-vector polygon inequality for fixed-diagonal PSD set",
        "full_method_level_minimum_se_mag": full_minimum,
        "full_method_level_independence_se_mag": independence,
        "full_method_level_maximum_se_mag": full_maximum,
        "full_method_level_maximum_over_independence":
            full_maximum / independence,
        "full_method_level_analytic_basis": (
            "Gram-vector polygon inequality over all reported method-cell marginal variances"
        ),
    }


def _halfnormal_logpdf(values: np.ndarray, scale: float) -> np.ndarray:
    return (math.log(math.sqrt(2.0 / math.pi) / scale)
            - 0.5 * np.square(values / scale))


def _trapezoid_log_weights(size: int, step: float) -> np.ndarray:
    weights = np.full(size, step, dtype=float)
    weights[[0, -1]] *= 0.5
    return np.log(weights)


def _psd_inverse_logdet(matrix: np.ndarray, tolerance: float = 1e-12):
    values, vectors = np.linalg.eigh(matrix)
    if values.min() < -1e-10:
        raise JWSTHierarchyError("negative covariance eigenvalue")
    keep = values > tolerance
    if not np.any(keep):
        raise JWSTHierarchyError("zero-rank covariance")
    inverse = (vectors[:, keep] / values[keep]) @ vectors[:, keep].T
    return inverse, float(np.log(values[keep]).sum()), int(keep.sum()), vectors[:, ~keep]


def _mvn_zero_logpdf(vector: np.ndarray, covariance: np.ndarray) -> float:
    inverse, logdet, rank, null = _psd_inverse_logdet(covariance)
    if null.size and float(np.linalg.norm(null.T @ vector)) > 1e-9:
        return -math.inf
    return float(-0.5 * (rank * math.log(2 * math.pi) + logdet
                         + vector @ inverse @ vector))


def _gaussian_log_components(
        deltas: np.ndarray, covariance: np.ndarray, delta_prior_sd: float,
        tau_scale: float, tau: np.ndarray) -> dict[str, np.ndarray]:
    """Evaluate the analytic Gaussian conditional terms on one tau grid."""
    tau_points = len(tau)
    conditional_mean = np.empty(tau_points)
    conditional_variance = np.empty(tau_points)
    log_density = np.empty(tau_points)
    ones = np.ones(len(deltas))
    for index, value in enumerate(tau):
        current = covariance + value ** 2 * np.eye(len(deltas))
        inverse, _, _, _ = _psd_inverse_logdet(current + 1e-30 * np.eye(len(deltas)))
        precision = float(ones @ inverse @ ones + 1.0 / delta_prior_sd ** 2)
        conditional_variance[index] = 1.0 / precision
        conditional_mean[index] = conditional_variance[index] * float(
            ones @ inverse @ deltas
        )
        marginal = current + delta_prior_sd ** 2 * np.outer(ones, ones)
        log_density[index] = (
            _mvn_zero_logpdf(deltas, marginal)
            + _halfnormal_logpdf(np.asarray([value]), tau_scale)[0]
        )
    return {
        "tau": tau, "mean": conditional_mean,
        "variance": conditional_variance, "log_density": log_density,
    }


def _gaussian_components(
        deltas: np.ndarray, covariance: np.ndarray,
        delta_prior_sd: float, tau_scale: float,
        tau_points: int = 1001, tau_max: float = 0.50,
        validation_tau_max: float = 0.75) -> dict[str, np.ndarray | float]:
    if tau_points < 3 or tau_max <= 0 or validation_tau_max <= tau_max:
        raise JWSTHierarchyError("invalid Gaussian integration grid")
    tau = np.linspace(0.0, tau_max, tau_points)
    step = tau[1] - tau[0]
    validation_points = int(round(validation_tau_max / step)) + 1
    validation_tau = np.linspace(0.0, validation_tau_max, validation_points)
    base = _gaussian_log_components(
        deltas, covariance, delta_prior_sd, tau_scale, tau
    )
    validation = _gaussian_log_components(
        deltas, covariance, delta_prior_sd, tau_scale, validation_tau
    )
    base_log_weight = (
        base["log_density"] + _trapezoid_log_weights(tau_points, step)
    )
    validation_log_weight = (
        validation["log_density"]
        + _trapezoid_log_weights(validation_points, step)
    )
    log_normalizer = float(logsumexp(base_log_weight))
    validation_log_normalizer = float(logsumexp(validation_log_weight))
    log_weight = base_log_weight - log_normalizer
    weight = np.exp(log_weight)
    normalization_relative_error = float(abs(math.expm1(
        log_normalizer - validation_log_normalizer
    )))
    return {"tau": tau, "mean": base["mean"],
            "variance": base["variance"], "weight": weight,
            "log_normalizer": log_normalizer,
            "validation_log_normalizer": validation_log_normalizer,
            "normalization_relative_error": normalization_relative_error,
            "internal_normalization_residual": float(abs(weight.sum() - 1.0)),
            "posterior_upper_tau_edge_mass": float(weight[-1]),
            "tau_grid_maximum_mag": tau_max,
            "tau_grid_points": tau_points,
            "validation_tau_grid_maximum_mag": validation_tau_max,
            "validation_tau_grid_points": validation_points}


def _mixture_quantile(components: dict[str, np.ndarray], probability: float) -> float:
    mean = components["mean"]
    sd = np.sqrt(components["variance"])
    weight = components["weight"]

    def objective(value: float) -> float:
        return float(np.sum(weight * ndtr((value - mean) / sd)) - probability)

    low = float(np.min(mean - 12 * sd) - 1)
    high = float(np.max(mean + 12 * sd) + 1)
    return float(brentq(objective, low, high))


def _weighted_quantile(grid: np.ndarray, weight: np.ndarray,
                       probability: float) -> float:
    cumulative = np.cumsum(weight)
    cumulative /= cumulative[-1]
    return float(np.interp(probability, cumulative, grid))


def gaussian_hierarchical_posterior(
        deltas: Sequence[float], covariance: np.ndarray, *,
        delta_prior_sd: float = 0.30, tau_scale: float = 0.10,
        tau_points: int = 1001, tau_max: float = 0.50,
        validation_tau_max: float = 0.75,
        posterior_edge_mass_max: float = 1e-8,
        normalization_relative_tolerance: float = 1e-8,
        return_components: bool = False) -> dict:
    values = np.asarray(deltas, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    validate_psd_covariance(covariance, np.diag(covariance), check_diagonal=False)
    components = _gaussian_components(values, covariance, delta_prior_sd,
                                      tau_scale, tau_points, tau_max,
                                      validation_tau_max)
    mean = float(np.sum(components["weight"] * components["mean"]))
    variance = float(np.sum(components["weight"] * (
        components["variance"] + np.square(components["mean"] - mean)
    )))
    result = {
        "likelihood": "gaussian_multivariate",
        "delta_posterior_mean_mag": mean,
        "delta_posterior_median_mag": _mixture_quantile(components, 0.5),
        "delta_posterior_sd_mag": math.sqrt(variance),
        "delta_equal_tail_95pct_mag": [
            _mixture_quantile(components, 0.025),
            _mixture_quantile(components, 0.975),
        ],
        "tau_host_posterior_median_mag": _weighted_quantile(
            components["tau"], components["weight"], 0.5
        ),
        "tau_host_equal_tail_95pct_mag": [
            _weighted_quantile(components["tau"], components["weight"], 0.025),
            _weighted_quantile(components["tau"], components["weight"], 0.975),
        ],
        "delta_prior_sd_mag": delta_prior_sd,
        "tau_prior_scale_mag": tau_scale,
        "numerical_diagnostics": {
            key: components[key] for key in (
                "log_normalizer", "validation_log_normalizer",
                "normalization_relative_error",
                "internal_normalization_residual",
                "posterior_upper_tau_edge_mass",
                "tau_grid_maximum_mag", "tau_grid_points",
                "validation_tau_grid_maximum_mag",
                "validation_tau_grid_points",
            )
        },
        "numerical_status": (
            "PASS" if components["posterior_upper_tau_edge_mass"]
            <= posterior_edge_mass_max
            and components["normalization_relative_error"]
            <= normalization_relative_tolerance
            and components["internal_normalization_residual"] <= 1e-12
            else "NUMERICAL_GATE_FAIL"
        ),
    }
    if return_components:
        result["_components"] = components
    return result


def _student_log_posterior_grid(
        values: np.ndarray, covariance: np.ndarray, nu: int,
        delta_grid: np.ndarray, tau_grid: np.ndarray,
        delta_prior_sd: float, tau_scale: float,
        quadrature_points: int) -> np.ndarray:
    """Evaluate Normal-host plus multivariate-t measurement convolution.

    The measurement residual uses the variance-matched scale matrix
    ``S=(nu-2)/nu*C``.  Conditional on the Gamma precision ``lambda``, the
    total residual covariance is ``tau^2 I + S/lambda``; only the measurement
    term, never the Normal host effect, receives the Student-t radial scale.
    """
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if float(eigenvalues.min()) <= 0:
        raise JWSTHierarchyError(
            "Student-t convolution requires positive-definite measurement covariance"
        )
    transformed_data = eigenvectors.T @ values
    transformed_one = eigenvectors.T @ np.ones(len(values))
    shape = nu / 2.0
    nodes, raw_weights = roots_genlaguerre(quadrature_points, shape - 1.0)
    lambdas = nodes / shape
    log_mixture_weights = np.log(raw_weights) - gammaln(shape)
    measurement_eigenvalues = (nu - 2.0) / nu * eigenvalues
    delta_squared = np.square(delta_grid)
    log_grid = np.empty((len(tau_grid), len(delta_grid)), dtype=float)
    normalized_delta_prior = (
        -0.5 * np.square(delta_grid / delta_prior_sd)
        - math.log(delta_prior_sd * math.sqrt(2.0 * math.pi))
    )
    for index, tau in enumerate(tau_grid):
        total = (np.square(tau)
                 + measurement_eigenvalues[None, :] / lambdas[:, None])
        inverse = 1.0 / total
        a = np.sum(np.square(transformed_one)[None, :] * inverse, axis=1)
        b = np.sum(
            (transformed_one * transformed_data)[None, :] * inverse, axis=1
        )
        c = np.sum(np.square(transformed_data)[None, :] * inverse, axis=1)
        logdet = np.log(total).sum(axis=1)
        conditional = (
            -0.5 * (len(values) * math.log(2.0 * math.pi) + logdet)[:, None]
            - 0.5 * (
                a[:, None] * delta_squared[None, :]
                - 2.0 * b[:, None] * delta_grid[None, :]
                + c[:, None]
            )
            + log_mixture_weights[:, None]
        )
        log_grid[index] = (
            logsumexp(conditional, axis=0)
            + normalized_delta_prior
            + _halfnormal_logpdf(np.asarray([tau]), tau_scale)[0]
        )
    return log_grid


def _integrated_grid_log_normalizer(
        log_density: np.ndarray, delta_grid: np.ndarray,
        tau_grid: np.ndarray) -> tuple[float, np.ndarray]:
    log_weight = (
        log_density
        + _trapezoid_log_weights(len(tau_grid), tau_grid[1] - tau_grid[0])[:, None]
        + _trapezoid_log_weights(
            len(delta_grid), delta_grid[1] - delta_grid[0]
        )[None, :]
    )
    normalizer = float(logsumexp(log_weight))
    if not math.isfinite(normalizer):
        raise JWSTHierarchyError("posterior normalization failed")
    return normalizer, np.exp(log_weight - normalizer)


def student_t_hierarchical_posterior(
        deltas: Sequence[float], covariance: np.ndarray, nu: int, *,
        delta_prior_sd: float = 0.30, tau_scale: float = 0.10,
        delta_points: int = 2401, tau_points: int = 501,
        delta_max: float = 0.60, tau_max: float = 0.50,
        validation_delta_max: float = 0.90,
        validation_tau_max: float = 0.75,
        quadrature_points: int = 96,
        validation_quadrature_points: int = 128,
        posterior_edge_mass_max: float = 1e-8,
        normalization_relative_tolerance: float = 1e-8,
        return_grid: bool = False) -> dict:
    if nu <= 2:
        raise JWSTHierarchyError("variance-matched Student-t requires nu>2")
    values = np.asarray(deltas, dtype=float)
    covariance = np.asarray(covariance, dtype=float)
    validate_psd_covariance(covariance, np.diag(covariance), check_diagonal=False)
    if (delta_points < 3 or tau_points < 3 or delta_max <= 0 or tau_max <= 0
            or validation_delta_max <= delta_max
            or validation_tau_max <= tau_max
            or validation_quadrature_points <= quadrature_points):
        raise JWSTHierarchyError("invalid Student-t integration contract")
    delta_grid = np.linspace(-delta_max, delta_max, delta_points)
    tau_grid = np.linspace(0.0, tau_max, tau_points)
    delta_step = delta_grid[1] - delta_grid[0]
    tau_step = tau_grid[1] - tau_grid[0]
    validation_delta_points = int(round(
        2.0 * validation_delta_max / delta_step
    )) + 1
    validation_tau_points = int(round(validation_tau_max / tau_step)) + 1
    validation_delta_grid = np.linspace(
        -validation_delta_max, validation_delta_max, validation_delta_points
    )
    validation_tau_grid = np.linspace(
        0.0, validation_tau_max, validation_tau_points
    )
    log_density = _student_log_posterior_grid(
        values, covariance, nu, delta_grid, tau_grid, delta_prior_sd,
        tau_scale, quadrature_points,
    )
    normalizer, weights = _integrated_grid_log_normalizer(
        log_density, delta_grid, tau_grid
    )
    refined_density = _student_log_posterior_grid(
        values, covariance, nu, delta_grid, tau_grid, delta_prior_sd,
        tau_scale, validation_quadrature_points,
    )
    refined_normalizer, _ = _integrated_grid_log_normalizer(
        refined_density, delta_grid, tau_grid
    )
    validation_density = _student_log_posterior_grid(
        values, covariance, nu, validation_delta_grid, validation_tau_grid,
        delta_prior_sd, tau_scale, validation_quadrature_points,
    )
    validation_normalizer, _ = _integrated_grid_log_normalizer(
        validation_density, validation_delta_grid, validation_tau_grid
    )
    quadrature_relative_error = float(abs(math.expm1(
        normalizer - refined_normalizer
    )))
    domain_relative_error = float(abs(math.expm1(
        refined_normalizer - validation_normalizer
    )))
    normalization_relative_error = max(
        quadrature_relative_error, domain_relative_error
    )
    delta_weight = weights.sum(axis=0)
    tau_weight = weights.sum(axis=1)
    edge_mass = float(
        delta_weight[[0, -1]].sum() + weights[-1, 1:-1].sum()
    )
    mean = float(delta_grid @ delta_weight)
    sd = float(np.sqrt(np.square(delta_grid - mean) @ delta_weight))
    result = {
        "likelihood": f"student_t_measurement_nu{nu}_normal_host_convolution",
        "model_semantics": (
            "u_h~Normal(0,tau_host^2); measurement residual is a "
            "variance-matched multivariate Student-t integrated over its "
            "Gamma precision mixture"
        ),
        "nu": nu,
        "delta_posterior_mean_mag": mean,
        "delta_posterior_median_mag": _weighted_quantile(delta_grid, delta_weight, 0.5),
        "delta_posterior_sd_mag": sd,
        "delta_equal_tail_95pct_mag": [
            _weighted_quantile(delta_grid, delta_weight, 0.025),
            _weighted_quantile(delta_grid, delta_weight, 0.975),
        ],
        "tau_host_posterior_median_mag": _weighted_quantile(tau_grid, tau_weight, 0.5),
        "tau_host_equal_tail_95pct_mag": [
            _weighted_quantile(tau_grid, tau_weight, 0.025),
            _weighted_quantile(tau_grid, tau_weight, 0.975),
        ],
        "numerical_diagnostics": {
            "posterior_union_edge_mass": edge_mass,
            "log_normalizer": normalizer,
            "refined_quadrature_log_normalizer": refined_normalizer,
            "validation_log_normalizer": validation_normalizer,
            "quadrature_relative_error": quadrature_relative_error,
            "domain_relative_error": domain_relative_error,
            "normalization_relative_error": normalization_relative_error,
            "internal_normalization_residual": float(abs(weights.sum() - 1.0)),
            "delta_grid": {"minimum_mag": -delta_max,
                           "maximum_mag": delta_max,
                           "points": delta_points},
            "tau_grid": {"minimum_mag": 0.0, "maximum_mag": tau_max,
                         "points": tau_points},
            "validation_delta_grid": {
                "minimum_mag": -validation_delta_max,
                "maximum_mag": validation_delta_max,
                "points": validation_delta_points,
            },
            "validation_tau_grid": {
                "minimum_mag": 0.0, "maximum_mag": validation_tau_max,
                "points": validation_tau_points,
            },
            "quadrature_points": quadrature_points,
            "validation_quadrature_points": validation_quadrature_points,
        },
        "posterior_edge_mass": edge_mass,
        "numerical_status": (
            "PASS" if edge_mass <= posterior_edge_mass_max
            and normalization_relative_error <= normalization_relative_tolerance
            and abs(weights.sum() - 1.0) <= 1e-12
            else "NUMERICAL_GATE_FAIL"
        ),
        "delta_prior_sd_mag": delta_prior_sd,
        "tau_prior_scale_mag": tau_scale,
    }
    if return_grid:
        result["_grid"] = {"delta": delta_grid, "tau": tau_grid,
                           "weights": weights}
    return result


def sample_gaussian_posterior(components: dict[str, np.ndarray], size: int,
                              rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    indices = rng.choice(len(components["tau"]), size=size,
                         p=components["weight"])
    tau = components["tau"][indices]
    delta = rng.normal(components["mean"][indices],
                       np.sqrt(components["variance"][indices]))
    return delta, tau


def sample_student_t_grid(grid: dict[str, np.ndarray], size: int,
                          rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    flat = grid["weights"].ravel()
    indices = rng.choice(flat.size, size=size, p=flat / flat.sum())
    tau_index, delta_index = np.unravel_index(indices, grid["weights"].shape)
    return grid["delta"][delta_index], grid["tau"][tau_index]


def latent_host_distance_posteriors(
        pairs: Sequence[HostPair], components: dict[str, np.ndarray], *,
        draws: int = 20000, seed: int = 20260722) -> dict:
    """Summarize latent host moduli under the diagonal sensitivity model.

    For each posterior ``(delta, tau)`` draw, the host-specific contrast is
    updated analytically from the paired difference.  The precision-weighted
    common-mode statistic is conditionally independent of that contrast for
    Gaussian method errors, so the latent distance modulus can then be drawn
    without a second fit.
    """
    if draws <= 0:
        raise JWSTHierarchyError("latent-host posterior draws must be positive")
    rng = np.random.default_rng(seed)
    delta, tau = sample_gaussian_posterior(components, draws, rng)
    summaries = []
    for pair in pairs:
        contrast_variance = pair.independence_variance_mag2
        tau_variance = np.square(tau)
        denominator = tau_variance + contrast_variance
        shrinkage = np.divide(
            tau_variance, denominator, out=np.zeros_like(tau_variance),
            where=denominator > 0,
        )
        host_effect_mean = shrinkage * (pair.delta_mag - delta)
        host_effect_sd = np.sqrt(np.divide(
            tau_variance * contrast_variance, denominator,
            out=np.zeros_like(tau_variance), where=denominator > 0,
        ))
        host_contrast = delta + host_effect_mean + rng.normal(
            0.0, host_effect_sd
        )
        weight_a = 1.0 / pair.sigma_a_mag ** 2
        weight_b = 1.0 / pair.sigma_b_mag ** 2
        common_mean = (
            weight_a * (pair.mu_a_mag - 0.5 * host_contrast)
            + weight_b * (pair.mu_b_mag + 0.5 * host_contrast)
        ) / (weight_a + weight_b)
        host_modulus = common_mean + rng.normal(
            0.0, math.sqrt(1.0 / (weight_a + weight_b)), size=draws
        )
        summaries.append({
            "host": pair.host,
            "posterior_mean_distance_modulus_mag": float(host_modulus.mean()),
            "posterior_median_distance_modulus_mag": float(
                np.median(host_modulus)
            ),
            "equal_tail_95pct_distance_modulus_mag": np.quantile(
                host_modulus, [0.025, 0.975]
            ).tolist(),
            "posterior_mean_host_contrast_mag": float(host_contrast.mean()),
        })
    return {
        "status": "NUISANCE_POSTERIOR_SENSITIVITY_ONLY",
        "covariance_role": "independence_sensitivity_only",
        "draws": draws,
        "seed": seed,
        "rows": summaries,
    }


def posterior_predictive_check(
        deltas: Sequence[float], covariance: np.ndarray, posterior: dict,
        *, draws: int, seed: int, nu: int | None = None) -> dict:
    rng = np.random.default_rng(seed)
    if "_components" in posterior:
        delta, tau = sample_gaussian_posterior(posterior["_components"], draws, rng)
    elif "_grid" in posterior:
        delta, tau = sample_student_t_grid(posterior["_grid"], draws, rng)
    else:
        raise JWSTHierarchyError("posterior sampling state absent")
    n = len(deltas)
    replicas = np.empty((draws, n), dtype=float)
    for index in range(draws):
        if nu is None:
            current = covariance + tau[index] ** 2 * np.eye(n)
            residual = rng.multivariate_normal(np.zeros(n), current)
        else:
            host_effect = rng.normal(0.0, tau[index], size=n)
            measurement_scale = (nu - 2.0) / nu * covariance
            measurement_normal = rng.multivariate_normal(
                np.zeros(n), measurement_scale
            )
            measurement = measurement_normal / math.sqrt(
                rng.chisquare(nu) / nu
            )
            residual = host_effect + measurement
        replicas[index] = delta[index] + residual
    observed = np.asarray(deltas, dtype=float)
    functions = {
        "sample_variance": lambda x: np.var(x, axis=-1, ddof=1),
        "sample_max": lambda x: np.max(x, axis=-1),
        "sample_range": lambda x: np.ptp(x, axis=-1),
    }
    results = {}
    status = "PASS"
    for name, function in functions.items():
        observed_value = float(function(observed))
        replica_values = function(replicas)
        right = float((1 + np.sum(replica_values >= observed_value)) / (draws + 1))
        two_sided = min(1.0, 2 * min(right, 1.0 - right + 1.0 / (draws + 1)))
        extreme = right < 0.005 or right > 0.995
        if extreme:
            status = "MODEL_INADEQUATE"
        results[name] = {"observed": observed_value, "right_tail_p": right,
                         "two_sided_p": two_sided, "extreme": extreme}
    return {"status": status, "draws": draws, "seed": seed,
            "frozen_discrepancies": results,
            "meaning": "conditional predictive adequacy only"}


def simulation_based_calibration(
        covariance: np.ndarray, *, simulations: int, posterior_draws: int,
        seed: int, delta_prior_sd: float = 0.30,
        tau_scale: float = 0.10, tau_points: int = 251) -> dict:
    """Calibrate the Gaussian delta posterior under the registered prior.

    The eigensystem and tau-grid precision factors are invariant across SBC
    simulations.  Precomputing them is algebraically identical to repeatedly
    calling :func:`gaussian_hierarchical_posterior`, while avoiding hundreds of
    thousands of duplicate eigendecompositions in the 3000-realization gate.
    """
    rng = np.random.default_rng(seed)
    n = covariance.shape[0]
    covariance = np.asarray(covariance, dtype=float)
    validate_psd_covariance(covariance, np.diag(covariance),
                            check_diagonal=False)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    if float(eigenvalues.min()) <= 1e-14:
        raise JWSTHierarchyError(
            "SBC fast path requires a positive-definite observed covariance"
        )
    tau_grid = np.linspace(0.0, 0.50, tau_points)
    variances = eigenvalues[None, :] + np.square(tau_grid[:, None])
    inverse_eigenvalues = 1.0 / variances
    transformed_one = eigenvectors.T @ np.ones(n)
    one_precision = np.sum(
        np.square(transformed_one)[None, :] * inverse_eigenvalues, axis=1
    )
    conditional_variance = 1.0 / (
        one_precision + 1.0 / delta_prior_sd ** 2
    )
    marginal_logdet = (
        np.log(variances).sum(axis=1)
        + np.log1p(delta_prior_sd ** 2 * one_precision)
    )
    fixed_log_weight = (
        -0.5 * (n * math.log(2 * math.pi) + marginal_logdet)
        + _halfnormal_logpdf(tau_grid, tau_scale)
        + _trapezoid_log_weights(tau_points, tau_grid[1] - tau_grid[0])
    )
    ranks = {"known_good": [], "variance_scale_0.5": [], "variance_scale_2.0": []}
    for _ in range(simulations):
        truth_delta = rng.normal(0.0, delta_prior_sd)
        truth_tau = abs(rng.normal(0.0, tau_scale))
        data = truth_delta + rng.multivariate_normal(
            np.zeros(n), covariance + truth_tau ** 2 * np.eye(n)
        )
        transformed_data = eigenvectors.T @ data
        data_precision = np.sum(
            np.square(transformed_data)[None, :] * inverse_eigenvalues,
            axis=1,
        )
        cross_precision = np.sum(
            (transformed_one * transformed_data)[None, :]
            * inverse_eigenvalues,
            axis=1,
        )
        conditional_mean = conditional_variance * cross_precision
        marginal_quadratic = (
            data_precision
            - delta_prior_sd ** 2 * np.square(cross_precision)
            / (1.0 + delta_prior_sd ** 2 * one_precision)
        )
        log_weight = fixed_log_weight - 0.5 * marginal_quadratic
        log_weight -= logsumexp(log_weight)
        tau_indices = rng.choice(
            tau_points, size=posterior_draws, p=np.exp(log_weight)
        )
        draws = rng.normal(
            conditional_mean[tau_indices],
            np.sqrt(conditional_variance[tau_indices]),
        )
        center = float(np.sum(np.exp(log_weight) * conditional_mean))
        candidates = {
            "known_good": draws,
            "variance_scale_0.5": center + math.sqrt(0.5) * (draws - center),
            "variance_scale_2.0": center + math.sqrt(2.0) * (draws - center),
        }
        for name, values in candidates.items():
            ranks[name].append(int(np.sum(values < truth_delta)))
    reports = {}
    for name, values in ranks.items():
        bins = np.bincount(np.asarray(values) // 3, minlength=7)[:7]
        expected = simulations / 7.0
        statistic = float(np.square(bins - expected).sum() / expected)
        pvalue = float(chi2.sf(statistic, 6))
        reports[name] = {"rank_bins": bins.tolist(), "chi_square": statistic,
                         "dof": 6, "pvalue": pvalue}
    good_pass = reports["known_good"]["pvalue"] > 0.01
    bad_rejected = all(reports[name]["pvalue"] < 0.01
                       for name in ("variance_scale_0.5", "variance_scale_2.0"))
    return {"status": "PASS" if good_pass and bad_rejected else "SBC_FAIL",
            "simulations": simulations, "posterior_draws": posterior_draws,
            "seed": seed, "rank_bins": 7, "pvalue_floor": 0.01,
            "reports": reports, "meaning": "computation calibration only"}


def leave_host_out(pairs: Sequence[HostPair], covariance: np.ndarray,
                   full: dict, *, tau_points: int = 1001) -> dict:
    rows = []
    full_median = full["delta_posterior_median_mag"]
    full_sd = full["delta_posterior_sd_mag"]
    unstable = False
    for index, pair in enumerate(pairs):
        keep = np.arange(len(pairs)) != index
        fit = gaussian_hierarchical_posterior(
            np.asarray([row.delta_mag for row in pairs])[keep],
            covariance[np.ix_(keep, keep)], tau_points=tau_points,
        )
        shift = fit["delta_posterior_median_mag"] - full_median
        row_unstable = abs(shift) > 0.03 or abs(shift) / full_sd > 0.5
        unstable = unstable or row_unstable
        rows.append({"held_out_host": pair.host, "median_mag":
                     fit["delta_posterior_median_mag"], "shift_mag": shift,
                     "standardized_shift_in_full_sd": abs(shift) / full_sd,
                     "unstable": row_unstable})
    return {"unit": "complete_paired_host", "rows": rows,
            "status": "HOST_DELETION_UNSTABLE" if unstable else "PASS",
            "thresholds": {"absolute_shift_mag": 0.03,
                           "standardized_shift_in_full_sd": 0.5}}


def prior_sensitivity(deltas: Sequence[float], covariance: np.ndarray,
                      *, tau_points: int = 1001) -> dict:
    baseline = gaussian_hierarchical_posterior(
        deltas, covariance, tau_points=tau_points
    )
    rows = []
    max_endpoint = 0.0
    max_width_fraction = 0.0
    base_interval = baseline["delta_equal_tail_95pct_mag"]
    base_width = base_interval[1] - base_interval[0]
    for delta_sd in (0.15, 0.30, 0.60):
        for tau_scale in (0.05, 0.10, 0.20):
            result = gaussian_hierarchical_posterior(
                deltas, covariance, delta_prior_sd=delta_sd,
                tau_scale=tau_scale, tau_points=tau_points,
            )
            interval = result["delta_equal_tail_95pct_mag"]
            width = interval[1] - interval[0]
            endpoint = max(abs(interval[0] - base_interval[0]),
                           abs(interval[1] - base_interval[1]))
            width_fraction = abs(width / base_width - 1.0)
            max_endpoint = max(max_endpoint, endpoint)
            max_width_fraction = max(max_width_fraction, width_fraction)
            rows.append({"delta_prior_sd_mag": delta_sd,
                         "tau_prior_scale_mag": tau_scale,
                         "median_mag": result["delta_posterior_median_mag"],
                         "interval_95pct_mag": interval})
    sensitive = max_endpoint > 0.02 or max_width_fraction > 0.25
    return {"rows": rows, "max_endpoint_movement_mag": max_endpoint,
            "max_width_fraction_change": max_width_fraction,
            "status": "PRIOR_SENSITIVE" if sensitive else "PASS"}


def structured_covariance_scan(pairs: Sequence[HostPair], *,
                               tau_points: int = 1001) -> dict:
    deltas = [row.delta_mag for row in pairs]
    rows = []
    blocks = ("global_all_cell_factor", "method_block_factor",
              "authenticated_group_block_factor")
    for block in blocks:
        for q in (0.0, 0.25, 0.50, 0.75, 1.0):
            method = method_cell_covariance(pairs, q, block)
            contrast = contrast_covariance(method)
            fit = gaussian_hierarchical_posterior(
                deltas, contrast, tau_points=tau_points
            )
            rows.append({
                "block": block, "q": q,
                "group_block_status": (
                    "NOT_SEPARATELY_IDENTIFIED_SAME_AS_METHOD_BLOCK"
                    if block == "authenticated_group_block_factor" else None
                ),
                "minimum_contrast_eigenvalue": float(
                    np.linalg.eigvalsh(contrast).min()),
                "median_mag": fit["delta_posterior_median_mag"],
                "sd_mag": fit["delta_posterior_sd_mag"],
                "interval_95pct_mag": fit["delta_equal_tail_95pct_mag"],
                "numerical_status": fit["numerical_status"],
                "numerical_diagnostics": fit["numerical_diagnostics"],
            })
    failed_numerical_rows = [
        {"block": row["block"], "q": row["q"]}
        for row in rows if row["numerical_status"] != "PASS"
    ]
    independence = next(row for row in rows
                        if row["block"] == blocks[0] and row["q"] == 0.0)
    endpoints = [value for row in rows for value in row["interval_95pct_mag"]]
    widths = [row["interval_95pct_mag"][1] - row["interval_95pct_mag"][0]
              for row in rows]
    base_interval = independence["interval_95pct_mag"]
    max_movement = max(
        max(abs(row["interval_95pct_mag"][0] - base_interval[0]),
            abs(row["interval_95pct_mag"][1] - base_interval[1]))
        for row in rows
    )
    base_width = base_interval[1] - base_interval[0]
    return {"rows": rows,
            "numerical_status": (
                "PASS" if not failed_numerical_rows else "NUMERICAL_GATE_FAIL"
            ),
            "failed_numerical_rows": failed_numerical_rows,
            "envelope_interval_endpoints_mag": [min(endpoints), max(endpoints)],
            "maximum_endpoint_movement_from_independence_mag": max_movement,
            "maximum_width_ratio_to_independence": max(widths) / base_width,
            "classification": (
                "NUMERICAL_GATE_FAIL" if failed_numerical_rows else
                "COVARIANCE_STABLE" if max_movement <= 0.02
                and max(widths) / base_width <= 1.25 else "COVARIANCE_CONDITIONAL"
            )}


def analyze_family(pairs: Sequence[HostPair], dataset: str, *,
                   production: bool = True) -> dict:
    rows = validate_pairs(pairs, dataset)
    deltas = np.asarray([row.delta_mag for row in rows])
    independence = np.diag([row.independence_variance_mag2 for row in rows])
    gaussian = gaussian_hierarchical_posterior(
        deltas, independence, tau_points=1001 if production else 101,
        return_components=True,
    )
    latent_hosts = latent_host_distance_posteriors(
        rows, gaussian["_components"],
        draws=20000 if production else 2000, seed=20260722,
    )
    student = {
        str(nu): student_t_hierarchical_posterior(
            deltas, independence, nu,
            delta_points=2401 if production else 401,
            tau_points=501 if production else 101,
            return_grid=True,
        ) for nu in (4, 8)
    }
    ppc = {
        "gaussian": posterior_predictive_check(
            deltas, independence, gaussian,
            draws=5000 if production else 200, seed=20260721,
        ),
        **{
            f"student_t_nu{nu}": posterior_predictive_check(
                deltas, independence, student[str(nu)],
                draws=5000 if production else 200, seed=20260721 + nu, nu=nu,
            ) for nu in (4, 8)
        },
    }
    for result in (gaussian, *student.values()):
        result.pop("_components", None)
        result.pop("_grid", None)
    scan = structured_covariance_scan(
        rows, tau_points=1001 if production else 101
    )
    bounds = fixed_diagonal_mean_se_bounds(rows)
    robust_endpoint = max(
        max(abs(student[str(nu)]["delta_equal_tail_95pct_mag"][i]
                - gaussian["delta_equal_tail_95pct_mag"][i])
            for i in (0, 1)) for nu in (4, 8)
    )
    base_width = (gaussian["delta_equal_tail_95pct_mag"][1]
                  - gaussian["delta_equal_tail_95pct_mag"][0])
    robust_width = max(
        abs((student[str(nu)]["delta_equal_tail_95pct_mag"][1]
             - student[str(nu)]["delta_equal_tail_95pct_mag"][0])
            / base_width - 1.0) for nu in (4, 8)
    )
    numerical_components = {
        "gaussian": gaussian["numerical_status"],
        **{f"student_t_nu{nu}": student[str(nu)]["numerical_status"]
           for nu in (4, 8)},
        "structured_covariance_scan": scan["numerical_status"],
    }
    numerical_status = (
        "PASS" if all(value == "PASS" for value in numerical_components.values())
        else "NUMERICAL_GATE_FAIL"
    )
    terminal_classification = (
        "TOTAL_UNCERTAINTY_NOT_IDENTIFIED" if numerical_status == "PASS"
        else "MODEL_INADEQUATE_NUMERICAL_GATE"
    )
    return {
        "schema": "htt.pr154.observed_family.v1",
        "dataset": dataset,
        "contrast": FAMILY_CONTRACTS[dataset]["contrast"],
        "n_hosts": len(rows),
        "hosts": [row.host for row in rows],
        "observed_host_deltas_mag": deltas.tolist(),
        "unweighted_replay": {
            "mean_delta_mag": float(deltas.mean()),
            "sample_sd_mag": float(deltas.std(ddof=1)),
            "between_host_se_mag": float(deltas.std(ddof=1) / math.sqrt(len(deltas))),
        },
        "latent_pair_collapse_check": {
            "latent_gls_delta_mag": latent_gls_offset(rows),
            "collapsed_gls_delta_mag": collapsed_gls_offset(rows),
            "absolute_difference_mag": abs(latent_gls_offset(rows)
                                           - collapsed_gls_offset(rows)),
            "status": "PASS" if abs(latent_gls_offset(rows)
                                     - collapsed_gls_offset(rows)) <= 1e-4 else "FAIL",
        },
        "group_zero_point_status": "GROUP_ZERO_POINT_NOT_IDENTIFIED",
        "group_zero_point_reason": (
            "one method level per side; no authenticated independent multi-level "
            "calibration-group design"
        ),
        "latent_host_distance_moduli": latent_hosts,
        "independence_sensitivity": {
            "gaussian": gaussian, "student_t": student,
            "primary_total_uncertainty": False,
        },
        "fixed_diagonal_psd_bounds": bounds,
        "structured_covariance_scan": scan,
        "prior_sensitivity": prior_sensitivity(
            deltas, independence, tau_points=1001 if production else 101
        ),
        "leave_host_out": leave_host_out(
            rows, independence, gaussian,
            tau_points=1001 if production else 101,
        ),
        "leave_group_out": {
            "status": "GROUP_ZERO_POINT_NOT_IDENTIFIED",
            "rank_loss_is_not_identified": True,
        },
        "ppc": ppc,
        "robustness": {
            "maximum_gaussian_t_endpoint_movement_mag": robust_endpoint,
            "maximum_gaussian_t_width_fraction_change": robust_width,
            "status": "OUTLIER_SENSITIVE" if robust_endpoint > 0.02
            or robust_width > 0.25 else "PASS",
        },
        "numerical_status": numerical_status,
        "numerical_components": numerical_components,
        "terminal_classification": terminal_classification,
        "terminal_reason": (
            "fixed-diagonal PSD covariance admits a zero lower SE bound and a "
            "maximum more than 1.25 times the independence sensitivity"
            if numerical_status == "PASS" else
            "one or more preregistered posterior integration gates failed"
        ),
    }


def cf4_scenario_grid(pairs: Sequence[HostPair], dataset: str, *,
                      replicates: int = 5000, seed: int = 20260719,
                      coverage_acceptance: tuple[float, float] = (0.93, 0.97),
                      unsafe_absolute_bias_mag: float = 0.01,
                      material_width_gain_fraction: float = 0.10,
                      material_rmse_gain_fraction: float = 0.10,
                      classification_mc_guard_sigma: float = 2.0) -> dict:
    """Scenario-only CF4 overlap stress test; never an observed regression."""
    rows = validate_pairs(pairs, dataset)
    if replicates < 20:
        raise JWSTHierarchyError("CF4 scenario grid requires at least 20 replicates")
    n = len(rows)
    sigma = float(np.median(np.sqrt(
        [row.independence_variance_mag2 for row in rows]
    )))
    output = []
    for overlap, error_rate, reliability, slope, q, nu in itertools.product(
        (0.0, 0.5, 1.0), (0.0, 0.1, 0.25), (0.5, 0.8, 1.0),
        (-0.05, -0.02, 0.0, 0.02, 0.05), (0.0, 0.5, 0.9), (4, 8, math.inf),
    ):
        token = f"{dataset}|{overlap}|{error_rate}|{reliability}|{slope}|{q}|{nu}|{seed}"
        cell_seed = int(hashlib.sha256(token.encode()).hexdigest()[:16], 16)
        rng = np.random.default_rng(cell_seed)
        x_true = rng.normal(size=(replicates, n))
        claimed = int(round(overlap * n))
        x_obs = np.zeros_like(x_true)
        false_mask = np.zeros((replicates, claimed), dtype=bool)
        if claimed:
            x_obs[:, :claimed] = (math.sqrt(reliability) * x_true[:, :claimed]
                                  + math.sqrt(1 - reliability)
                                  * rng.normal(size=(replicates, claimed)))
            false_mask = rng.random((replicates, claimed)) < error_rate
            replacements = rng.normal(size=(replicates, claimed))
            x_obs[:, :claimed] = np.where(
                false_mask, replacements, x_obs[:, :claimed]
            )
        common = rng.normal(size=(replicates, 1))
        independent = rng.normal(size=(replicates, n))
        residual = sigma * (math.sqrt(q) * common
                            + math.sqrt(1 - q) * independent)
        if math.isfinite(nu):
            residual *= math.sqrt((nu - 2) / nu)
            residual /= np.sqrt(rng.chisquare(nu, size=(replicates, 1)) / nu)
        data = slope * x_true + residual
        baseline = data.mean(axis=1)
        mean_x = x_obs.mean(axis=1)
        mean_y = data.mean(axis=1)
        centered_x = x_obs - mean_x[:, None]
        centered_y = data - mean_y[:, None]
        sxx = np.square(centered_x).sum(axis=1)
        sxy = (centered_x * centered_y).sum(axis=1)
        rank_deficient = sxx <= 1e-14
        slope_hat = np.divide(sxy, sxx, out=np.zeros_like(sxy),
                              where=~rank_deficient)
        adjusted = mean_y - slope_hat * mean_x
        if claimed == 0:
            adjusted = baseline.copy()
        split = replicates // 2
        calibration = slice(0, split)
        evaluation = slice(split, replicates)
        evaluation_count = replicates - split
        baseline_abs_cal = np.abs(baseline[calibration])
        adjusted_abs_cal = np.abs(adjusted[calibration])
        baseline_width = float(np.quantile(baseline_abs_cal, 0.95))
        adjusted_width = float(np.quantile(adjusted_abs_cal, 0.95))
        baseline_eval = baseline[evaluation]
        adjusted_eval = adjusted[evaluation]
        baseline_coverage = float(np.mean(np.abs(baseline_eval) <= baseline_width))
        adjusted_coverage = float(np.mean(np.abs(adjusted_eval) <= adjusted_width))
        baseline_coverage_se = math.sqrt(
            baseline_coverage * (1.0 - baseline_coverage) / evaluation_count
        )
        adjusted_coverage_se = math.sqrt(
            adjusted_coverage * (1.0 - adjusted_coverage) / evaluation_count
        )
        baseline_rmse = float(np.sqrt(np.mean(np.square(baseline_eval))))
        adjusted_rmse = float(np.sqrt(np.mean(np.square(adjusted_eval))))
        rmse_gain = float(1.0 - adjusted_rmse / baseline_rmse)
        adjusted_sq = np.square(adjusted_eval)
        baseline_sq = np.square(baseline_eval)
        mean_adjusted_sq = float(adjusted_sq.mean())
        mean_baseline_sq = float(baseline_sq.mean())
        gradient_adjusted = -1.0 / (
            2.0 * math.sqrt(mean_adjusted_sq * mean_baseline_sq)
        )
        gradient_baseline = math.sqrt(mean_adjusted_sq) / (
            2.0 * mean_baseline_sq ** 1.5
        )
        rmse_gain_influence = (
            gradient_adjusted * (adjusted_sq - mean_adjusted_sq)
            + gradient_baseline * (baseline_sq - mean_baseline_sq)
        )
        rmse_gain_se = float(
            rmse_gain_influence.std(ddof=1) / math.sqrt(evaluation_count)
        )
        width_gain = float(1.0 - adjusted_width / baseline_width)
        calibration_probability_se = math.sqrt(0.95 * 0.05 / split)
        lower_probability = max(
            0.5, 0.95 - classification_mc_guard_sigma * calibration_probability_se
        )
        upper_probability = min(
            0.999,
            0.95 + classification_mc_guard_sigma * calibration_probability_se,
        )
        conservative_width_gain = float(
            1.0
            - np.quantile(adjusted_abs_cal, upper_probability)
            / np.quantile(baseline_abs_cal, lower_probability)
        )
        width_gain_mc_se = max(
            0.0,
            (width_gain - conservative_width_gain)
            / classification_mc_guard_sigma,
        )
        bias = float(np.mean(adjusted_eval))
        bias_se = float(adjusted_eval.std(ddof=1) / math.sqrt(evaluation_count))
        coverage_low, coverage_high = coverage_acceptance
        baseline_coverage_safe = (
            baseline_coverage
            - classification_mc_guard_sigma * baseline_coverage_se >= coverage_low
            and baseline_coverage
            + classification_mc_guard_sigma * baseline_coverage_se <= coverage_high
        )
        adjusted_coverage_safe = (
            adjusted_coverage
            - classification_mc_guard_sigma * adjusted_coverage_se >= coverage_low
            and adjusted_coverage
            + classification_mc_guard_sigma * adjusted_coverage_se <= coverage_high
        )
        bias_safe = (
            abs(bias) + classification_mc_guard_sigma * bias_se
            <= unsafe_absolute_bias_mag
        )
        rmse_gain_lower = (
            rmse_gain - classification_mc_guard_sigma * rmse_gain_se
        )
        material = (
            claimed > 0 and slope != 0.0
            and baseline_coverage_safe and adjusted_coverage_safe and bias_safe
            and conservative_width_gain >= material_width_gain_fraction
            and rmse_gain_lower >= material_rmse_gain_fraction
        )
        if material:
            classification = "MATERIAL_GAIN_SCENARIO"
        elif not (baseline_coverage_safe and adjusted_coverage_safe and bias_safe):
            classification = "UNSAFE_OR_MISCALIBRATED_SCENARIO"
        elif (slope != 0.0 and claimed > 0
              and (width_gain >= material_width_gain_fraction
                   or rmse_gain >= material_rmse_gain_fraction)):
            classification = "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"
        else:
            classification = "NO_MATERIAL_GAIN"
        false_count = int(false_mask.sum())
        false_trials = replicates * claimed
        realized_error_rate = (
            false_count / false_trials if false_trials else 0.0
        )
        identity_error_mc_se = (
            math.sqrt(error_rate * (1.0 - error_rate) / false_trials)
            if false_trials else 0.0
        )
        output.append({
            "verified_overlap_fraction": overlap,
            "identity_error_rate": error_rate,
            "auxiliary_reliability": reliability,
            "nuisance_slope_mag": slope,
            "correlated_fraction_q": q,
            "likelihood_nu": "infinity" if not math.isfinite(nu) else int(nu),
            "claimed_host_count": claimed,
            "false_identity_count_mean": (
                false_count / replicates if replicates else 0.0
            ),
            "realized_identity_error_rate": realized_error_rate,
            "identity_error_rate_mc_se": identity_error_mc_se,
            "design_status": (
                "BASELINE_NO_AUXILIARY_DESIGN" if claimed == 0
                else "AUXILIARY_REGRESSION_SCENARIO"
            ),
            "bias_mag": bias,
            "bias_mc_se_mag": bias_se,
            "baseline_bias_mag": float(np.mean(baseline_eval)),
            "baseline_rmse_mag": baseline_rmse,
            "adjusted_rmse_mag": adjusted_rmse,
            "rmse_mag": adjusted_rmse,
            "rmse_gain_fraction": rmse_gain,
            "rmse_gain_mc_se": rmse_gain_se,
            "rmse_gain_lower_guard": rmse_gain_lower,
            "baseline_coverage_95pct": baseline_coverage,
            "baseline_coverage_mc_se": baseline_coverage_se,
            "coverage_95pct": adjusted_coverage,
            "coverage_mc_se": adjusted_coverage_se,
            "baseline_interval_95pct_mag": [-baseline_width, baseline_width],
            "adjusted_interval_95pct_mag": [-adjusted_width, adjusted_width],
            "mean_interval_half_width_mag": adjusted_width,
            "baseline_interval_half_width_mag": baseline_width,
            "width_reduction_fraction": width_gain,
            "width_gain_mc_se": width_gain_mc_se,
            "width_gain_lower_guard": conservative_width_gain,
            "rank_deficient_fraction": float(rank_deficient.mean()),
            "classification": classification,
            "observed_result": False,
        })
    return {
        "schema": "htt.pr154.cf4_scenarios.v1", "dataset": dataset,
        "identity_status": "positional_only_no_verified_observed_overlap",
        "observed_nonzero_overlap_count": 0, "scenario_only": True,
        "replicates_per_cell": replicates, "base_seed": seed,
        "monte_carlo_split": {
            "interval_calibration_draws": replicates // 2,
            "independent_evaluation_draws": replicates - replicates // 2,
        },
        "classification_contract": {
            "coverage_acceptance": list(coverage_acceptance),
            "unsafe_absolute_bias_mag": unsafe_absolute_bias_mag,
            "material_width_gain_fraction": material_width_gain_fraction,
            "material_rmse_gain_fraction": material_rmse_gain_fraction,
            "mc_guard_sigma": classification_mc_guard_sigma,
            "material_requires_nonzero_slope": True,
        },
        "cells": output,
    }


__all__ = [
    "HostPair", "JWSTHierarchyError", "FAMILY_CONTRACTS", "validate_pairs",
    "latent_gls_offset", "collapsed_gls_offset", "method_cell_covariance",
    "contrast_covariance", "fixed_diagonal_mean_se_bounds",
    "gaussian_hierarchical_posterior", "student_t_hierarchical_posterior",
    "posterior_predictive_check", "simulation_based_calibration",
    "latent_host_distance_posteriors",
    "leave_host_out", "prior_sensitivity", "structured_covariance_scan",
    "analyze_family", "cf4_scenario_grid",
]

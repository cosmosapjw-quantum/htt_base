"""Small analytic/synthetic references and known mutants for PR-123.

The references deliberately do not import any mapped production module.  They
are regression mechanics, not replacement estimators or scientific producers.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable

import numpy as np

from .oracle_lab import PropertyResult, content_sha256, make_outcome


def constrained_shell_weights(directions: np.ndarray, shells: np.ndarray, variances: np.ndarray) -> np.ndarray:
    """Direct dense constrained-BLUE reference, returned as (3, nrow)."""
    n_hat, nuisance = np.asarray(directions, float), np.asarray(shells, float)
    inv_var = 1.0 / np.asarray(variances, float)
    design = np.column_stack((n_hat, nuisance))
    gram = design.T @ (inv_var[:, None] * design)
    targets = np.vstack((np.eye(3), np.zeros((nuisance.shape[1], 3))))
    return (inv_var[:, None] * design @ np.linalg.solve(gram, targets)).T


def unconstrained_bulk_weights(
    directions: np.ndarray, variances: np.ndarray
) -> np.ndarray:
    """Known mutant: omit every shell-monopole nuisance constraint."""
    n_hat = np.asarray(directions, float)
    inv_var = 1.0 / np.asarray(variances, float)
    gram = n_hat.T @ (inv_var[:, None] * n_hat)
    return (inv_var[:, None] * n_hat @ np.linalg.solve(gram, np.eye(3))).T


def real_noise_rfft(n: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Independent half-spectrum reference obtained from a real full field."""
    field = rng.standard_normal((n, n, n))
    return field, np.fft.rfftn(field, norm="ortho")


def unconstrained_complex_rfft(n: int, rng: np.random.Generator) -> np.ndarray:
    """Known mutant: independent complex samples on every half-spectrum mode."""
    shape = (n, n, n // 2 + 1)
    return (rng.standard_normal(shape) + 1j * rng.standard_normal(shape)) / np.sqrt(2.0)


def rfft_special_plane_residual(spectrum: np.ndarray, n: int) -> float:
    reverse = np.mod(-np.arange(n), n)
    plane_ids = (0, n // 2) if n % 2 == 0 else (0,)
    residuals = []
    for kz in plane_ids:
        plane = spectrum[:, :, kz]
        conjugate_reverse = np.conj(plane[reverse[:, None], reverse[None, :]])
        residuals.append(float(np.max(np.abs(plane - conjugate_reverse))))
    return max(residuals)


def rfft_parseval_relative_error(field: np.ndarray, spectrum: np.ndarray) -> float:
    weights = np.full(spectrum.shape[-1], 2.0)
    weights[0] = 1.0
    if field.shape[-1] % 2 == 0:
        weights[-1] = 1.0
    lhs = float(np.sum(field * field))
    rhs = float(np.sum(np.abs(spectrum) ** 2 * weights[None, None, :]))
    return abs(lhs - rhs) / max(lhs, np.finfo(float).tiny)


def refit_alpha_residual(counts: np.ndarray, randoms: np.ndarray) -> tuple[float, np.ndarray]:
    alpha = float(np.sum(counts) / np.sum(randoms))
    return alpha, (np.asarray(counts, float) - alpha * randoms) / (alpha * randoms)


def fixed_alpha_residual(
    counts: np.ndarray, randoms: np.ndarray, fixed_alpha: float
) -> np.ndarray:
    return (np.asarray(counts, float) - fixed_alpha * randoms) / (fixed_alpha * randoms)


def heteroscedastic_gls_mean(
    values: np.ndarray, errors: np.ndarray, shared_sigma: float = 0.0
) -> tuple[float, float]:
    y = np.asarray(values, float)
    sigma = np.asarray(errors, float)
    covariance = np.diag(sigma * sigma) + shared_sigma**2 * np.ones((y.size, y.size))
    precision_one = np.linalg.solve(covariance, np.ones(y.size))
    denom = float(np.sum(precision_one))
    return float(precision_one @ y / denom), float(np.sqrt(1.0 / denom))


def uniform_error_mean(values: np.ndarray, errors: np.ndarray) -> tuple[float, float]:
    """Known mutant: discard row-specific host errors."""
    y = np.asarray(values, float)
    common = float(np.mean(np.asarray(errors, float)))
    return float(np.mean(y)), float(common / np.sqrt(y.size))


def pooled_rank_pvalues(scores: np.ndarray) -> np.ndarray:
    values = np.asarray(scores, float).reshape(-1)
    return np.sum(values[None, :] >= values[:, None], axis=1) / values.size


def asymmetric_rank_pvalues(scores: np.ndarray, observation_index: int) -> np.ndarray:
    """Known mutant mirroring observation/null rank asymmetry."""
    values = np.asarray(scores, float).reshape(-1)
    n = values.size
    null_mask = np.arange(n) != int(observation_index)
    nulls = values[null_mask]
    result = np.empty(n, float)
    result[observation_index] = (1.0 + np.sum(nulls >= values[observation_index])) / n
    result[null_mask] = (1.0 + np.sum(nulls[None, :] >= nulls[:, None], axis=1)) / n
    return result


def conjugate_normal_log_bf(n: int, sigma: float, tau: float, ybar: float) -> float:
    ratio = n * tau * tau / (sigma * sigma)
    gain = n * n * tau * tau * ybar * ybar / (
        sigma * sigma * (sigma * sigma + n * tau * tau)
    )
    return float(-0.5 * np.log1p(ratio) + 0.5 * gain)


def fitted_normal_score(n: int, sigma: float, ybar: float) -> float:
    """Known mutant: maximized log-likelihood gain without an Occam factor."""
    return float(n * ybar * ybar / (2.0 * sigma * sigma))


def quadrature_normal_bf(
    n: int, sigma: float, tau: float, ybar: float, *, points: int = 20001
) -> float:
    mu = np.linspace(-8.0 * tau, 8.0 * tau, points)
    prior = np.exp(-0.5 * (mu / tau) ** 2) / (np.sqrt(2.0 * np.pi) * tau)
    likelihood_ratio = np.exp(-0.5 * n * ((ybar - mu) ** 2 - ybar**2) / sigma**2)
    trapz = np.trapz if hasattr(np, "trapz") else np.trapezoid
    return float(trapz(prior * likelihood_ratio, mu))


def conjugate_posterior_parameters(
    n: int, sigma: float, prior_mean: float, prior_variance: float, ybar: float
) -> tuple[float, float]:
    variance = 1.0 / (1.0 / prior_variance + n / sigma**2)
    mean = variance * (prior_mean / prior_variance + n * ybar / sigma**2)
    return float(mean), float(variance)


def conjugate_posterior_predictive_draws(
    mean: float, variance: float, sigma: float, draws: int, rng: np.random.Generator
) -> np.ndarray:
    mu = rng.normal(mean, np.sqrt(variance), size=draws)
    return rng.normal(mu, sigma, size=draws)


def plugin_predictive_draws(
    mean: float, sigma: float, draws: int, rng: np.random.Generator
) -> np.ndarray:
    """Known mutant: replicate only at a fitted posterior mean."""
    return rng.normal(mean, sigma, size=draws)


@dataclass(frozen=True)
class NumericInterval:
    lower: float
    upper: float
    closed: bool = True

    def __post_init__(self) -> None:
        if not np.isfinite(self.lower) or not np.isfinite(self.upper) or self.lower > self.upper:
            raise ValueError("invalid interval")


def _contains(container: NumericInterval, requested: NumericInterval) -> bool:
    lower_ok = requested.lower > container.lower or (
        requested.lower == container.lower and (container.closed or not requested.closed)
    )
    upper_ok = requested.upper < container.upper or (
        requested.upper == container.upper and (container.closed or not requested.closed)
    )
    return bool(lower_ok and upper_ok)


def validated_range_contains(
    requested: NumericInterval,
    callable_range: NumericInterval,
    validated_range: NumericInterval,
    source_sha256: str,
    expected_source_sha256: str,
) -> bool:
    return bool(
        source_sha256 == expected_source_sha256
        and _contains(callable_range, requested)
        and _contains(validated_range, requested)
    )


def callable_range_only_contains(
    requested: NumericInterval, callable_range: NumericInterval
) -> bool:
    """Known mutant: ignore validated-domain provenance."""
    return _contains(callable_range, requested)


def _rng_children(root_seed: int, count: int) -> list[np.random.SeedSequence]:
    return list(np.random.SeedSequence(root_seed).spawn(count))


def _seed_record(
    lane: str,
    replicate: int,
    child: np.random.SeedSequence,
    *,
    role: str,
    root_seed: int,
) -> dict[str, Any]:
    state = child.generate_state(4).tobytes()
    return {
        "lane_id": lane,
        "replicate": replicate,
        "role": role,
        "root_entropy": root_seed,
        "spawn_key": list(child.spawn_key),
        "bit_generator": "PCG64DXSM",
        "stream_hash": hashlib.sha256(state).hexdigest(),
    }


def run_non_k6_reference_cases(
    *, root_seed: int, replicates: int, ppc_draws: int
) -> tuple[list[Any], list[dict[str, Any]]]:
    """Execute the eight non-K6 clean/mutant pairs on frozen streams."""
    outcomes: list[Any] = []
    seed_ledger: list[dict[str, Any]] = []
    children = _rng_children(root_seed, replicates * 6)

    shell_clean: list[float] = []
    uniform_clean: list[float] = []
    shell_permutation: list[float] = []
    shell_mutant: list[float] = []
    for i, child in enumerate(children[:replicates]):
        rng = np.random.Generator(np.random.PCG64DXSM(child))
        directions = rng.normal(size=(24, 3))
        directions /= np.linalg.norm(directions, axis=1)[:, None]
        radius = np.linspace(0.0, 1.0, 24)
        shells = np.column_stack((radius < 0.43, radius > 0.66)).astype(float)
        variances = 0.5 + rng.random(24)
        clean = constrained_shell_weights(directions, shells, variances)
        mutant = unconstrained_bulk_weights(directions, variances)
        permutation = rng.permutation(directions.shape[0])
        permuted = constrained_shell_weights(
            directions[permutation], shells[permutation], variances[permutation]
        )
        restored = np.empty_like(permuted)
        restored[:, permutation] = permuted
        uniform_clean.append(float(np.max(np.abs(clean @ directions - np.eye(3)))))
        shell_clean.append(float(np.max(np.abs(clean @ shells))))
        shell_permutation.append(float(np.max(np.abs(clean - restored))))
        shell_mutant.append(float(np.max(np.abs(mutant @ shells))))
        seed_ledger.append(_seed_record(
            "cf4_constrained_linear_estimator", i, child,
            role="paired_clean_and_mutant", root_seed=root_seed,
        ))
    uniform_clean_max = max(uniform_clean)
    clean_shell_max = max(shell_clean)
    shell_permutation_max = max(shell_permutation)
    mutant_shell_min = min(shell_mutant)
    outcomes.append(make_outcome(
        "shell_monopole_leak",
        "cf4_constrained_linear_estimator",
        (
            PropertyResult("uniform_flow", uniform_clean_max < 1e-11, uniform_clean_max, 1e-11, "W times directions equals identity"),
            PropertyResult("zero_shell_response", clean_shell_max < 1e-11, clean_shell_max, 1e-11, "all registered shell columns"),
            PropertyResult("row_permutation", shell_permutation_max < 1e-11, shell_permutation_max, 1e-11, "paired row permutation executed"),
        ),
        reference_symbol="constrained_shell_weights",
        mutant_symbol="unconstrained_bulk_weights",
        fixture_hash=content_sha256({"rows": 24, "shell_edges": [0.43, 0.66], "replicates": replicates}),
        reference_execution_count=2 * replicates,
        mutant_execution_count=replicates,
        mutant_failed_properties=("zero_shell_response",) if mutant_shell_min > 1e-3 else (),
        metrics={"uniform_flow_max": uniform_clean_max, "clean_shell_max": clean_shell_max, "row_permutation_max": shell_permutation_max, "mutant_shell_min": mutant_shell_min},
    ))

    plane_clean: list[float] = []
    plane_mutant: list[float] = []
    parseval: list[float] = []
    for i, child in enumerate(children[replicates:2 * replicates]):
        rng = np.random.Generator(np.random.PCG64DXSM(child))
        field, clean = real_noise_rfft(12, rng)
        mutant = unconstrained_complex_rfft(12, rng)
        plane_clean.append(rfft_special_plane_residual(clean, 12))
        plane_mutant.append(rfft_special_plane_residual(mutant, 12))
        parseval.append(rfft_parseval_relative_error(field, clean))
        seed_ledger.append(_seed_record(
            "grf_hermitian_generation", i, child,
            role="paired_clean_and_mutant", root_seed=root_seed,
        ))
    clean_plane_passes = sum(value < 1e-11 for value in plane_clean)
    mutant_plane_failures = sum(value > 1e-3 for value in plane_mutant)
    outcomes.append(make_outcome(
        "nonhermitian_rfft_plane",
        "grf_hermitian_generation",
        (
            PropertyResult("special_plane_hermiticity", max(plane_clean) < 1e-11, max(plane_clean), 1e-11, "kz=0 and Nyquist planes"),
            PropertyResult("parseval", max(parseval) < 1e-12, max(parseval), 1e-12, "orthonormal half-spectrum weighting"),
            PropertyResult("multiseed_plane_coverage", clean_plane_passes == replicates and mutant_plane_failures == replicates, f"clean={clean_plane_passes},mutant={mutant_plane_failures}", f"{replicates}/{replicates}", "every frozen clean plane passes and mutant plane violates"),
        ),
        reference_symbol="real_noise_rfft",
        mutant_symbol="unconstrained_complex_rfft",
        fixture_hash=content_sha256({"grid": 12, "planes": [0, 6], "replicates": replicates}),
        reference_execution_count=replicates,
        mutant_execution_count=replicates,
        mutant_failed_properties=("special_plane_hermiticity",) if mutant_plane_failures == replicates else (),
        metrics={"clean_plane_max": max(plane_clean), "mutant_plane_min": min(plane_mutant), "parseval_max": max(parseval)},
    ))

    alpha_clean: list[float] = []
    alpha_mutant: list[float] = []
    alpha_permutation: list[float] = []
    alpha_values: list[float] = []
    for i, child in enumerate(children[2 * replicates:3 * replicates]):
        rng = np.random.Generator(np.random.PCG64DXSM(child))
        randoms = rng.integers(80, 180, size=40).astype(float)
        scale = 0.8 + 0.4 * (i + 1) / replicates
        counts = rng.poisson(scale * randoms)
        alpha, residual = refit_alpha_residual(counts, randoms)
        permutation = rng.permutation(randoms.size)
        perm_alpha, perm_residual = refit_alpha_residual(
            counts[permutation], randoms[permutation]
        )
        restored = np.empty_like(perm_residual)
        restored[permutation] = perm_residual
        alpha_clean.append(abs(float(np.sum(randoms * residual))))
        alpha_permutation.append(max(abs(alpha - perm_alpha), float(np.max(np.abs(residual - restored)))))
        alpha_values.append(alpha)
        alpha_mutant.append(abs(float(np.sum(randoms * fixed_alpha_residual(counts, randoms, 1.0)))))
        if not np.isfinite(alpha) or alpha <= 0:
            alpha_clean[-1] = float("inf")
        seed_ledger.append(_seed_record(
            "desi_per_realization_normalization", i, child,
            role="paired_clean_and_mutant", root_seed=root_seed,
        ))
    shifted_alpha_count = sum(abs(value - 1.0) > 1e-3 for value in alpha_values)
    mutant_alpha_failures = sum(value > 1e-6 for value in alpha_mutant)
    outcomes.append(make_outcome(
        "fixed_alpha_mock",
        "desi_per_realization_normalization",
        (
            PropertyResult("weighted_monopole_zero", max(alpha_clean) < 1e-11, max(alpha_clean), 1e-11, "alpha refit per realization"),
            PropertyResult("pixel_permutation", max(alpha_permutation) < 1e-12, max(alpha_permutation), 1e-12, "paired pixel permutation executed"),
            PropertyResult("multiseed_scale_shift", shifted_alpha_count >= replicates - 1, shifted_alpha_count, f">={replicates - 1}", "refitted alpha follows frozen realization scale shifts"),
        ),
        reference_symbol="refit_alpha_residual",
        mutant_symbol="fixed_alpha_residual",
        fixture_hash=content_sha256({"pixels": 40, "scale_range": [0.8, 1.2], "replicates": replicates}),
        reference_execution_count=2 * replicates,
        mutant_execution_count=replicates,
        mutant_failed_properties=("weighted_monopole_zero",) if mutant_alpha_failures >= replicates - 1 else (),
        metrics={"clean_monopole_max": max(alpha_clean), "pixel_permutation_max": max(alpha_permutation), "shifted_alpha_count": shifted_alpha_count, "mutant_failures": mutant_alpha_failures},
    ))

    errors = np.array([0.12, 0.25, 0.5, 1.1, 1.7])
    fixture_y = np.array([1.7, 0.8, 1.2, -0.4, 2.1])
    clean_a = heteroscedastic_gls_mean(fixture_y, errors)[0]
    clean_b = heteroscedastic_gls_mean(fixture_y, errors[::-1])[0]
    mutant_a = uniform_error_mean(fixture_y, errors)[0]
    mutant_b = uniform_error_mean(fixture_y, errors[::-1])[0]
    coverage = 0
    for i, child in enumerate(children[3 * replicates:4 * replicates]):
        rng = np.random.Generator(np.random.PCG64DXSM(child))
        truth = 0.6
        sample = truth + rng.normal(0.0, errors)
        estimate, se = heteroscedastic_gls_mean(sample, errors)
        coverage += abs(estimate - truth) <= 1.96 * se
        seed_ledger.append(_seed_record(
            "jwst_synthetic_weighting_reference", i, child,
            role="clean_coverage", root_seed=root_seed,
        ))
    huge = errors.copy(); huge[0] = 1e9
    huge_mean = heteroscedastic_gls_mean(fixture_y, huge)[0]
    dropped_mean = heteroscedastic_gls_mean(fixture_y[1:], errors[1:])[0]
    outcomes.append(make_outcome(
        "ignored_host_error",
        "jwst_synthetic_weighting_reference",
        (
            PropertyResult("error_permutation_sensitivity", abs(clean_a - clean_b) > 1e-3, abs(clean_a - clean_b), 1e-3, "errors remain attached to rows"),
            PropertyResult("infinite_error_limit", abs(huge_mean - dropped_mean) < 1e-10, abs(huge_mean - dropped_mean), 1e-10, "infinite variance deletes one host"),
            PropertyResult("multiseed_interval_coverage", 12 <= coverage <= replicates, coverage, "12..16", "95 percent synthetic intervals"),
        ),
        reference_symbol="heteroscedastic_gls_mean",
        mutant_symbol="uniform_error_mean",
        fixture_hash=content_sha256({"errors": errors.tolist(), "values": fixture_y.tolist(), "replicates": replicates}),
        reference_execution_count=replicates + 4,
        mutant_execution_count=2,
        mutant_failed_properties=("error_permutation_sensitivity",) if abs(mutant_a - mutant_b) < 1e-15 and abs(clean_a - clean_b) > 1e-3 else (),
        metrics={"clean_error_permutation_delta": abs(clean_a - clean_b), "mutant_delta": abs(mutant_a - mutant_b), "covered_replicates": coverage},
    ))

    scores = np.array([0.13, 0.71, -0.4, 1.8, 0.02, 0.9])
    clean_ranks = pooled_rank_pvalues(scores)
    rank_grid = np.arange(1, scores.size + 1) / scores.size
    permutation = np.array([3, 0, 5, 2, 1, 4])
    permuted_ranks = pooled_rank_pvalues(scores[permutation])
    restored_ranks = np.empty_like(permuted_ranks)
    restored_ranks[permutation] = permuted_ranks
    label_permutation_error = float(np.max(np.abs(clean_ranks - restored_ranks)))
    mutant_deltas = [
        float(np.max(np.abs(asymmetric_rank_pvalues(scores, i) - clean_ranks)))
        for i in range(scores.size)
    ]
    outcomes.append(make_outcome(
        "asymmetric_global_rank",
        "finite_null_rank_semantics",
        (
            PropertyResult("label_permutation", label_permutation_error < 1e-15, label_permutation_error, 1e-15, "explicit pooled-row relabeling executed"),
            PropertyResult("exact_rank_grid", np.allclose(np.sort(clean_ranks), rank_grid), float(np.max(np.abs(np.sort(clean_ranks) - rank_grid))), 1e-15, "distinct finite ranks"),
            PropertyResult("tied_superuniformity", np.all((pooled_rank_pvalues(np.array([1.0, 1.0, 0.0])) * 3) >= 1), 1, 1, "greater-equal ties are conservative"),
        ),
        reference_symbol="pooled_rank_pvalues",
        mutant_symbol="asymmetric_rank_pvalues",
        fixture_hash=content_sha256({"scores": scores.tolist(), "permutation": permutation.tolist()}),
        reference_execution_count=3,
        mutant_execution_count=scores.size,
        mutant_failed_properties=("label_permutation",) if max(mutant_deltas) > 1.0 / scores.size - 1e-15 else (),
        metrics={"label_permutation_error": label_permutation_error, "mutant_label_delta_max": max(mutant_deltas), "rank_grid": clean_ranks.tolist()},
    ))

    n, sigma, tau, ybar = 8, 1.0, 2.0, 0.3
    log_bf = conjugate_normal_log_bf(n, sigma, tau, ybar)
    narrow_prior_log_bf = conjugate_normal_log_bf(n, sigma, 0.5, ybar)
    fitted = fitted_normal_score(n, sigma, ybar)
    quadrature = quadrature_normal_bf(n, sigma, tau, ybar)
    quadrature_error = abs(np.exp(log_bf) - quadrature)
    outcomes.append(make_outcome(
        "fitted_score_pseudo_bayes_factor",
        "evidence_mechanics_reference",
        (
            PropertyResult("occam_sign_separation", log_bf < 0.0 < fitted, log_bf, "log_bf<0<fitted_score", "normalized prior supplies Occam term"),
            PropertyResult("prior_width_sensitivity", narrow_prior_log_bf != log_bf, abs(narrow_prior_log_bf - log_bf), 0.0, "marginal evidence depends on prior width"),
            PropertyResult("quadrature_agreement", quadrature_error < 2e-5, quadrature_error, 2e-5, "closed form versus direct normalized-prior integration"),
        ),
        reference_symbol="conjugate_normal_log_bf",
        mutant_symbol="fitted_normal_score",
        fixture_hash=content_sha256({"n": n, "sigma": sigma, "tau": tau, "ybar": ybar}),
        reference_execution_count=2,
        mutant_execution_count=1,
        mutant_failed_properties=("occam_sign_separation", "prior_width_sensitivity") if log_bf < 0.0 < fitted else (),
        metrics={"log_bf": log_bf, "fitted_score": fitted, "quadrature_bf": quadrature, "quadrature_error": quadrature_error},
    ))

    mean, variance = conjugate_posterior_parameters(4, 1.0, 0.0, 1.0, 0.4)
    clean_draws: list[np.ndarray] = []
    mutant_draws: list[np.ndarray] = []
    for i in range(replicates):
        clean_child = children[4 * replicates + i]
        mutant_child = children[5 * replicates + i]
        clean_rng = np.random.Generator(np.random.PCG64DXSM(clean_child))
        mutant_rng = np.random.Generator(np.random.PCG64DXSM(mutant_child))
        clean_draws.append(conjugate_posterior_predictive_draws(mean, variance, 1.0, ppc_draws, clean_rng))
        mutant_draws.append(plugin_predictive_draws(mean, 1.0, ppc_draws, mutant_rng))
        seed_ledger.append(_seed_record(
            "posterior_predictive_mechanics_reference", i, clean_child,
            role="clean_posterior_predictive", root_seed=root_seed,
        ))
        seed_ledger.append(_seed_record(
            "posterior_predictive_mechanics_reference", i, mutant_child,
            role="mutant_plugin_predictive", root_seed=root_seed,
        ))
    clean_values = np.concatenate(clean_draws)
    mutant_values = np.concatenate(mutant_draws)
    target_variance = 1.0 + variance
    clean_variance = float(np.var(clean_values, ddof=1))
    mutant_variance = float(np.var(mutant_values, ddof=1))
    relative_error = abs(clean_variance - target_variance) / target_variance
    outcomes.append(make_outcome(
        "plugin_pseudo_ppc",
        "posterior_predictive_mechanics_reference",
        (
            PropertyResult("predictive_mean", abs(float(np.mean(clean_values)) - mean) < 0.03, abs(float(np.mean(clean_values)) - mean), 0.03, "posterior predictive mean"),
            PropertyResult("predictive_variance", relative_error < 0.08, relative_error, 0.08, "variance includes posterior uncertainty"),
            PropertyResult("posterior_variance_limit", variance > 0.0, variance, ">0", "finite posterior uncertainty"),
        ),
        reference_symbol="conjugate_posterior_predictive_draws",
        mutant_symbol="plugin_predictive_draws",
        fixture_hash=content_sha256({"n": 4, "sigma": 1.0, "prior_mean": 0.0, "prior_variance": 1.0, "ybar": 0.4, "replicates": replicates, "draws": ppc_draws}),
        reference_execution_count=replicates,
        mutant_execution_count=replicates,
        mutant_failed_properties=("predictive_variance",) if abs(mutant_variance - target_variance) > 0.08 * target_variance else (),
        metrics={"posterior_mean": mean, "posterior_variance": variance, "target_predictive_variance": target_variance, "clean_predictive_variance": clean_variance, "mutant_predictive_variance": mutant_variance},
    ))

    requested = NumericInterval(2.0, 10.0, True)
    callable_range = NumericInterval(2.0, 3000.0, True)
    validated = NumericInterval(40.0, 763.0, False)
    source_hash = "a" * 64
    clean_allowed = validated_range_contains(requested, callable_range, validated, source_hash, source_hash)
    stale_allowed = validated_range_contains(validated, callable_range, validated, "b" * 64, source_hash)
    mutant_allowed = callable_range_only_contains(requested, callable_range)
    outcomes.append(make_outcome(
        "stale_transfer_range",
        "transfer_consumer_range_containment",
        (
            PropertyResult("validated_subset", not clean_allowed, str(clean_allowed), "False", "requested L=2..10 is outside 40<L<763"),
            PropertyResult("stale_hash_rejection", not stale_allowed, str(stale_allowed), "False", "source digest is bound"),
            PropertyResult("monotone_narrowing", not validated_range_contains(requested, callable_range, NumericInterval(50.0, 700.0, False), source_hash, source_hash), 1, 1, "narrowing cannot authorize an invalid point"),
        ),
        reference_symbol="validated_range_contains",
        mutant_symbol="callable_range_only_contains",
        fixture_hash=content_sha256({"requested": [2.0, 10.0, True], "callable": [2.0, 3000.0, True], "validated": [40.0, 763.0, False], "source_hash": source_hash}),
        reference_execution_count=3,
        mutant_execution_count=1,
        mutant_failed_properties=("validated_subset", "stale_hash_rejection") if mutant_allowed and not clean_allowed else (),
        metrics={"clean_allowed": clean_allowed, "mutant_allowed": mutant_allowed, "stale_allowed": stale_allowed},
    ))
    return outcomes, seed_ledger

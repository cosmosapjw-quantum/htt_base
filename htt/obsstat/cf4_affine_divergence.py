"""PR-176 raw-CF4 affine-divergence channel.

The catalogue radial velocity is fitted to an affine vector field.  Its trace
coefficient ``theta`` is structurally distinct from a rigid translation, a
constant radial monopole, and trace-free shear.  Structural distinction is
not immunity to shared leakage.  This module deliberately does not emit a
q-channel estimate: the signed CF4-window responses and matched joint
covariance required by the frozen PR-176 contract are unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from typing import Mapping, Sequence

import numpy as np
from scipy.linalg import solve_triangular
from scipy.stats import norm

from common.cf4_forward_simulator import (
    SimMeta,
    load_sample_and_meta,
    subsample_with_meta,
)
from common.cf4_velocity_estimators import (
    Cf4Sample,
    _cv_correlation_matrix,
)

__all__ = [
    "AffineDivergenceConfig",
    "AffineDivergenceError",
    "COEFFICIENT_NAMES",
    "analyze_cf4_affine_divergence",
    "build_affine_design",
    "fit_affine_divergence",
    "formula_response_coefficients",
]


COEFFICIENT_NAMES = (
    "Bx",
    "By",
    "Bz",
    "M",
    "theta",
    "Sxx_minus_Szz",
    "Syy_minus_Szz",
    "Sxy",
    "Sxz",
    "Syz",
)


class AffineDivergenceError(ValueError):
    """Raised when the prospectively frozen PR-176 contract fails closed."""


@dataclass(frozen=True)
class AffineDivergenceConfig:
    """Frozen numerical choices for the PR-176 catalogue channel."""

    h0_km_s_mpc: float = 74.6
    sigma_nl_km_s: float = 250.0
    subsample_rows: int = 3000
    subsample_seed: int = 20260718
    radii_mpc: tuple[float, ...] = (75.0, 100.0, 125.0)
    primary_radius_mpc: float = 100.0
    c_km_s: float = 299792.458
    rank_tolerance: float = 1.0e-10
    minimum_singular_value_ratio: float = 1.0e-8
    maximum_standardized_condition_number: float = 1.0e4
    minimum_theta_retained_information: float = 0.05
    exact_injection_tolerance_relative: float = 1.0e-9
    coverage_draws: int = 5000
    coverage_seeds: tuple[int, ...] = (176000, 176001, 176002)
    confidence_level: float = 0.95
    minimum_component_coverage: float = 0.93
    maximum_component_coverage: float = 0.97
    covariance_jitter_kms2: float = 1.0e-6

    def __post_init__(self) -> None:
        if self.h0_km_s_mpc <= 0.0 or self.sigma_nl_km_s < 0.0:
            raise AffineDivergenceError("H0 must be positive and sigma_nl non-negative")
        if self.subsample_rows < 10:
            raise AffineDivergenceError("affine fit requires at least ten candidate rows")
        if len(self.radii_mpc) != 3 or tuple(sorted(self.radii_mpc)) != self.radii_mpc:
            raise AffineDivergenceError("PR-176 requires three increasing radii")
        if self.primary_radius_mpc not in self.radii_mpc:
            raise AffineDivergenceError("primary radius must be one registered radius")
        if len(self.coverage_seeds) != len(self.radii_mpc):
            raise AffineDivergenceError("one coverage seed is required per radius")
        if self.coverage_draws < 1:
            raise AffineDivergenceError("coverage draw count must be positive")
        if not 0.0 < self.minimum_theta_retained_information <= 1.0:
            raise AffineDivergenceError("invalid theta information gate")
        if self.exact_injection_tolerance_relative <= 0.0:
            raise AffineDivergenceError("exact-injection tolerance must be positive")
        if not 0.0 < self.confidence_level < 1.0:
            raise AffineDivergenceError("invalid confidence level")

    def to_dict(self) -> dict[str, object]:
        return {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in self.__dict__.items()
        }


@dataclass(frozen=True)
class PreparedBall:
    radius_mpc: float
    sample: Cf4Sample
    meta: SimMeta
    design: np.ndarray
    covariance: np.ndarray
    selected_row_sha256: str


@dataclass(frozen=True)
class AffineFit:
    radius_mpc: float
    coefficients: np.ndarray | None
    coefficient_covariance: np.ndarray | None
    diagnostics: Mapping[str, object]
    cholesky: np.ndarray
    whitened_design: np.ndarray
    normal_inverse: np.ndarray | None


def _array_sha256(*arrays: np.ndarray) -> str:
    digest = hashlib.sha256()
    for value in arrays:
        array = np.ascontiguousarray(np.asarray(value, dtype="<f8"))
        digest.update(str(array.shape).encode("ascii"))
        digest.update(array.tobytes())
    return digest.hexdigest()


def build_affine_design(direction: np.ndarray, distance_mpc: np.ndarray) -> np.ndarray:
    """Return the frozen translation/monopole/trace/STF design matrix."""

    n = np.asarray(direction, dtype=float)
    d = np.asarray(distance_mpc, dtype=float)
    if n.ndim != 2 or n.shape[1] != 3 or d.shape != (n.shape[0],):
        raise AffineDivergenceError("direction must be (N,3) and distance must be (N,)")
    if not np.all(np.isfinite(n)) or not np.all(np.isfinite(d)) or np.any(d <= 0.0):
        raise AffineDivergenceError("affine design inputs must be finite and positive")
    norm_error = np.max(np.abs(np.linalg.norm(n, axis=1) - 1.0))
    if norm_error > 1.0e-10:
        raise AffineDivergenceError("radial directions are not unit vectors")
    nx, ny, nz = n.T
    return np.column_stack((
        nx,
        ny,
        nz,
        np.ones_like(d),
        d / 3.0,
        d * (2.0 * nx * nx - ny * ny - nz * nz) / 3.0,
        d * (-nx * nx + 2.0 * ny * ny - nz * nz) / 3.0,
        2.0 * d * nx * ny,
        2.0 * d * nx * nz,
        2.0 * d * ny * nz,
    ))


def _subset_sample(sample: Cf4Sample, meta: SimMeta, keep: np.ndarray) -> tuple[Cf4Sample, SimMeta]:
    mask = np.asarray(keep, dtype=bool)
    sub = Cf4Sample(
        n=sample.n[mask],
        v=sample.v[mask],
        w=sample.w[mask],
        sig_v=sample.sig_v[mask],
        pos_hmpc=sample.pos_hmpc[mask],
        sg=sample.sg[mask] if sample.sg is not None else None,
    )
    return sub, SimMeta(
        dist=meta.dist[mask],
        e_dmzp=meta.e_dmzp[mask],
        h0=meta.h0,
    )


def _prepare_ball(sample: Cf4Sample, meta: SimMeta, radius_mpc: float,
                  jitter_kms2: float) -> PreparedBall:
    keep = np.asarray(meta.dist <= radius_mpc, dtype=bool)
    sub, sub_meta = _subset_sample(sample, meta, keep)
    if len(sub.v) < len(COEFFICIENT_NAMES):
        raise AffineDivergenceError(f"radius {radius_mpc:g} Mpc has too few rows")
    design = build_affine_design(sub.n, sub_meta.dist)
    cosmic = _cv_correlation_matrix(sub)
    covariance = cosmic + np.diag(np.square(sub.sig_v))
    covariance = 0.5 * (covariance + covariance.T)
    covariance.flat[:: len(sub.v) + 1] += jitter_kms2
    selected_hash = _array_sha256(sub.n, sub_meta.dist, sub.v, sub.sig_v)
    return PreparedBall(
        radius_mpc=float(radius_mpc),
        sample=sub,
        meta=sub_meta,
        design=design,
        covariance=covariance,
        selected_row_sha256=selected_hash,
    )


def _fit_with_whitening(design: np.ndarray, response: np.ndarray,
                        cholesky: np.ndarray, normal_inverse: np.ndarray) -> np.ndarray:
    x_white = solve_triangular(cholesky, design, lower=True, check_finite=False)
    y_white = solve_triangular(cholesky, response, lower=True, check_finite=False)
    return normal_inverse @ (x_white.T @ y_white)


def fit_affine_divergence(ball: PreparedBall, config: AffineDivergenceConfig) -> AffineFit:
    """Fit one cumulative-radius ball, withholding estimates on failed gates."""

    cholesky = np.linalg.cholesky(ball.covariance)
    x_white = solve_triangular(cholesky, ball.design, lower=True, check_finite=False)
    column_norm = np.linalg.norm(x_white, axis=0)
    if np.any(column_norm <= 0.0):
        raise AffineDivergenceError("zero whitened affine-design column")
    standardized = x_white / column_norm
    singular = np.linalg.svd(standardized, compute_uv=False)
    rank = int(np.sum(singular > config.rank_tolerance * singular[0]))
    ratio = float(singular[-1] / singular[0])
    condition = float(singular[0] / singular[-1]) if singular[-1] > 0.0 else math.inf

    theta_column = x_white[:, 4]
    nuisance = np.delete(x_white, 4, axis=1)
    nuisance_coeff, *_ = np.linalg.lstsq(nuisance, theta_column, rcond=None)
    theta_residual = theta_column - nuisance @ nuisance_coeff
    theta_information = float(
        np.dot(theta_residual, theta_residual) / np.dot(theta_column, theta_column)
    )
    pass_gates = (
        rank == len(COEFFICIENT_NAMES)
        and ratio >= config.minimum_singular_value_ratio
        and condition <= config.maximum_standardized_condition_number
        and theta_information >= config.minimum_theta_retained_information
    )
    diagnostics: dict[str, object] = {
        "rows": int(len(ball.sample.v)),
        "rank": rank,
        "columns": len(COEFFICIENT_NAMES),
        "singular_value_ratio": ratio,
        "standardized_condition_number": condition,
        "theta_retained_information": theta_information,
        "response_gate_pass": bool(pass_gates),
        "selected_row_sha256": ball.selected_row_sha256,
    }
    if not pass_gates:
        return AffineFit(
            radius_mpc=ball.radius_mpc,
            coefficients=None,
            coefficient_covariance=None,
            diagnostics=diagnostics,
            cholesky=cholesky,
            whitened_design=x_white,
            normal_inverse=None,
        )
    normal = x_white.T @ x_white
    normal_inverse = np.linalg.inv(normal)
    y_white = solve_triangular(cholesky, ball.sample.v, lower=True, check_finite=False)
    coefficients = normal_inverse @ (x_white.T @ y_white)
    residual_white = y_white - x_white @ coefficients
    diagnostics["whitened_residual_sum_squares"] = float(residual_white @ residual_white)
    diagnostics["residual_degrees_of_freedom"] = int(len(ball.sample.v) - len(COEFFICIENT_NAMES))
    return AffineFit(
        radius_mpc=ball.radius_mpc,
        coefficients=coefficients,
        coefficient_covariance=normal_inverse,
        diagnostics=diagnostics,
        cholesky=cholesky,
        whitened_design=x_white,
        normal_inverse=normal_inverse,
    )


def formula_response_coefficients(*, h0_km_s_mpc: float, c_km_s: float,
                                  lambda_mpc: float) -> dict[str, float]:
    """Return source-formula coefficients for audit, not calibrated q values."""

    if h0_km_s_mpc <= 0.0 or c_km_s <= 0.0 or lambda_mpc <= 0.0:
        raise AffineDivergenceError("response coefficient inputs must be positive")
    horizon_mpc = c_km_s / h0_km_s_mpc
    scale_ratio_squared = (horizon_mpc / lambda_mpc) ** 2
    return {
        "lambda_h_mpc": float(horizon_mpc),
        "lambda_mpc": float(lambda_mpc),
        "scale_ratio_squared": float(scale_ratio_squared),
        "R_lh_qs1_delta_q_per_theta": float(
            (2.0 / 3.0) * (1.0 + scale_ratio_squared / 6.0) / h0_km_s_mpc
        ),
        "R_lh_qs2_delta_q_per_theta": float(
            scale_ratio_squared / (9.0 * h0_km_s_mpc)
        ),
        "units": "Mpc_s_per_km",
    }


def _wilson_interval(successes: int, draws: int, confidence_level: float) -> tuple[float, float]:
    z = float(norm.ppf(0.5 + confidence_level / 2.0))
    p = successes / draws
    denominator = 1.0 + z * z / draws
    center = (p + z * z / (2.0 * draws)) / denominator
    half = z * math.sqrt(p * (1.0 - p) / draws + z * z / (4.0 * draws * draws)) / denominator
    return float(center - half), float(center + half)


def _relative_gate_error(actual: np.ndarray, expected: np.ndarray) -> float:
    return float(
        np.max(np.abs(np.asarray(actual, dtype=float) - np.asarray(expected, dtype=float)))
        / (1.0 + np.max(np.abs(np.asarray(expected, dtype=float))))
    )


def _exact_channel_injections(ball: PreparedBall, fit: AffineFit,
                              tolerance_relative: float) -> dict[str, object]:
    if fit.normal_inverse is None:
        return {"evaluated": False, "reason": "divergence_response_gate_failed"}
    truths = {
        "translation_only": np.asarray((300.0, -200.0, 100.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        "radial_monopole_only": np.asarray((0.0, 0.0, 0.0, 150.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)),
        "divergence_only": np.asarray((0.0, 0.0, 0.0, 0.0, -4.5, 0.0, 0.0, 0.0, 0.0, 0.0)),
        "trace_free_shear_only": np.asarray((0.0, 0.0, 0.0, 0.0, 0.0, 2.0, -1.0, 0.5, -0.25, 0.75)),
        "combined_affine_channels": np.asarray((120.0, -80.0, 45.0, 30.0, 2.5, 1.5, -0.5, 0.2, -0.3, 0.4)),
    }
    cases: dict[str, object] = {}
    all_pass = True
    for name, truth in truths.items():
        fitted = _fit_with_whitening(
            ball.design,
            ball.design @ truth,
            fit.cholesky,
            fit.normal_inverse,
        )
        scaled_error = _relative_gate_error(fitted, truth)
        passed = scaled_error <= tolerance_relative
        all_pass = all_pass and passed
        cases[name] = {
            "truth": truth.tolist(),
            "fitted": fitted.tolist(),
            "maximum_scaled_error": scaled_error,
            "pass": bool(passed),
        }

    omega = np.asarray((8.0, -5.0, 3.0))
    position = ball.meta.dist[:, None] * ball.sample.n
    rotational_velocity = np.einsum(
        "ij,ij->i", ball.sample.n, np.cross(np.broadcast_to(omega, position.shape), position)
    )
    rotation_fit = _fit_with_whitening(
        ball.design, rotational_velocity, fit.cholesky, fit.normal_inverse
    )
    radial_error = _relative_gate_error(rotational_velocity, np.zeros_like(rotational_velocity))
    fitted_rotation_error = _relative_gate_error(rotation_fit, np.zeros_like(rotation_fit))
    rotation_pass = radial_error <= tolerance_relative and fitted_rotation_error <= tolerance_relative
    cases["antisymmetric_rotation_zero_radial_response"] = {
        "maximum_radial_response_km_s": float(np.max(np.abs(rotational_velocity))),
        "maximum_fitted_coefficient": float(np.max(np.abs(rotation_fit))),
        "maximum_relative_gate_error": max(radial_error, fitted_rotation_error),
        "pass": bool(rotation_pass),
    }
    all_pass = all_pass and rotation_pass

    delta_h = 1.25
    base_fit = _fit_with_whitening(
        ball.design, ball.sample.v, fit.cholesky, fit.normal_inverse
    )
    shifted_fit = _fit_with_whitening(
        ball.design,
        ball.sample.v - delta_h * ball.meta.dist,
        fit.cholesky,
        fit.normal_inverse,
    )
    difference = shifted_fit - base_fit
    expected = np.zeros(len(COEFFICIENT_NAMES))
    expected[4] = -3.0 * delta_h
    alias_error = _relative_gate_error(difference, expected)
    alias_pass = alias_error <= tolerance_relative
    cases["h0_alias"] = {
        "delta_h_km_s_mpc": delta_h,
        "coefficient_difference": difference.tolist(),
        "expected_difference": expected.tolist(),
        "maximum_relative_gate_error": alias_error,
        "pass": bool(alias_pass),
    }
    all_pass = all_pass and alias_pass
    return {
        "evaluated": True,
        "tolerance_relative": tolerance_relative,
        "all_pass": bool(all_pass),
        "cases": cases,
    }


def _coverage_validation(fit: AffineFit, *, draws: int, seed: int,
                         config: AffineDivergenceConfig) -> dict[str, object]:
    if fit.coefficient_covariance is None:
        return {"evaluated": False, "reason": "divergence_response_gate_failed"}
    rng = np.random.Generator(np.random.PCG64(seed))
    chol = np.linalg.cholesky(fit.coefficient_covariance)
    errors = rng.standard_normal((draws, len(COEFFICIENT_NAMES))) @ chol.T
    sd = np.sqrt(np.diag(fit.coefficient_covariance))
    inside = np.abs(errors) <= float(norm.ppf(0.975)) * sd
    components: dict[str, object] = {}
    all_pass = True
    for index, name in enumerate(COEFFICIENT_NAMES):
        successes = int(np.sum(inside[:, index]))
        rate = successes / draws
        interval = _wilson_interval(successes, draws, config.confidence_level)
        passed = (
            config.minimum_component_coverage <= rate <= config.maximum_component_coverage
            and interval[0] <= 0.95 <= interval[1]
        )
        all_pass = all_pass and passed
        components[name] = {
            "successes": successes,
            "coverage_95": float(rate),
            "wilson_95": list(interval),
            "nominal_inside_wilson": bool(interval[0] <= 0.95 <= interval[1]),
            "pass": bool(passed),
        }
    return {
        "evaluated": True,
        "draws": draws,
        "seed": seed,
        "rng": "numpy_PCG64",
        "all_pass": bool(all_pass),
        "components": components,
        "interpretation": (
            "coefficient-space covariance-propagation self-consistency only; "
            "not independent physical-covariance validation"
        ),
    }


def _simultaneous_theta_intervals(fits: Sequence[AffineFit],
                                  confidence_level: float) -> dict[str, object]:
    if any(fit.coefficients is None or fit.coefficient_covariance is None for fit in fits):
        return {"evaluated": False, "reason": "one_or_more_divergence_response_gates_failed"}
    alpha = 1.0 - confidence_level
    z = float(norm.ppf(1.0 - alpha / (2.0 * len(fits))))
    intervals: dict[str, list[float]] = {}
    for fit in fits:
        assert fit.coefficients is not None and fit.coefficient_covariance is not None
        theta = float(fit.coefficients[4])
        se = float(math.sqrt(fit.coefficient_covariance[4, 4]))
        intervals[f"{fit.radius_mpc:g}"] = [theta - z * se, theta + z * se]
    contrasts: list[dict[str, object]] = []
    for left, right in zip(fits[:-1], fits[1:]):
        left_interval = intervals[f"{left.radius_mpc:g}"]
        right_interval = intervals[f"{right.radius_mpc:g}"]
        contrast_interval = [
            left_interval[0] - right_interval[1],
            left_interval[1] - right_interval[0],
        ]
        contrasts.append({
            "left_radius_mpc": left.radius_mpc,
            "right_radius_mpc": right.radius_mpc,
            "theta_left_minus_right_interval": contrast_interval,
            "contains_zero": bool(contrast_interval[0] <= 0.0 <= contrast_interval[1]),
        })
    return {
        "evaluated": True,
        "method": "Bonferroni_marginal_intervals_plus_interval_arithmetic",
        "family_confidence_level": confidence_level,
        "critical_z": z,
        "independence_assumed": False,
        "theta_intervals_by_radius": intervals,
        "nested_radius_contrasts": contrasts,
    }


def analyze_cf4_affine_divergence(groups_path: str, config: AffineDivergenceConfig
                                  ) -> dict[str, object]:
    """Execute the complete frozen divergence-channel measurement."""

    full_sample, full_meta = load_sample_and_meta(
        groups_path,
        h0=config.h0_km_s_mpc,
        sigma_nl=config.sigma_nl_km_s,
    )
    sample, meta = subsample_with_meta(
        full_sample,
        full_meta,
        config.subsample_rows,
        config.subsample_seed,
    )
    balls: list[PreparedBall] = []
    fits: list[AffineFit] = []
    measurements: list[dict[str, object]] = []
    injection_rows: list[dict[str, object]] = []
    for radius, coverage_seed in zip(config.radii_mpc, config.coverage_seeds):
        ball = _prepare_ball(sample, meta, radius, config.covariance_jitter_kms2)
        fit = fit_affine_divergence(ball, config)
        balls.append(ball)
        fits.append(fit)
        if fit.coefficients is None or fit.coefficient_covariance is None:
            coefficient_summary = None
        else:
            sd = np.sqrt(np.diag(fit.coefficient_covariance))
            coefficient_summary = {
                name: {"estimate": float(value), "marginal_sd": float(error)}
                for name, value, error in zip(COEFFICIENT_NAMES, fit.coefficients, sd)
            }
        measurements.append({
            "radius_mpc": radius,
            "lambda_mpc": 2.0 * radius,
            "frame": "published_CF4_CMB_frame_V3k",
            "h0_km_s_mpc": config.h0_km_s_mpc,
            "coefficient_summary": coefficient_summary,
            "diagnostics": dict(fit.diagnostics),
            "formula_response_coefficients_only": formula_response_coefficients(
                h0_km_s_mpc=config.h0_km_s_mpc,
                c_km_s=config.c_km_s,
                lambda_mpc=2.0 * radius,
            ),
            "q_point_estimate": None,
            "q_interval": None,
        })
        exact = _exact_channel_injections(
            ball,
            fit,
            config.exact_injection_tolerance_relative,
        )
        coverage = _coverage_validation(
            fit,
            draws=config.coverage_draws,
            seed=coverage_seed,
            config=config,
        )
        injection_rows.append({
            "radius_mpc": radius,
            "deterministic_exact": exact,
            "covariance_self_consistency": coverage,
        })

    all_response_pass = all(bool(fit.diagnostics["response_gate_pass"]) for fit in fits)
    all_injections_pass = all(
        bool(row["deterministic_exact"].get("all_pass", False))
        and bool(row["covariance_self_consistency"].get("all_pass", False))
        for row in injection_rows
    )
    return {
        "schema": "htt.pr176.affine_divergence_result.v1",
        "config": config.to_dict(),
        "full_catalogue_rows": int(len(full_sample.v)),
        "fixed_subsample_rows": int(len(sample.v)),
        "measurements": measurements,
        "simultaneous_theta_intervals": _simultaneous_theta_intervals(
            fits, config.confidence_level
        ),
        "injection_validation": injection_rows,
        "all_divergence_response_gates_pass": bool(all_response_pass),
        "all_injection_gates_pass": bool(all_injections_pass),
        "theta_is_scalar_without_apex": True,
        "structurally_distinct_not_leakage_immune": True,
        "q_response_authenticated": False,
        "matched_divergence_q_covariance_available": False,
    }

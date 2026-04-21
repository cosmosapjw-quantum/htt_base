"""Trace-source bridge helpers for the VER2 TSC active service."""
from __future__ import annotations

from functools import lru_cache
from typing import Iterable

import numpy as np

from common.contracts import ArtifactManifest, TscSourceBridgeReport, TscChart
from tsc.contracts import validate_tsc_service_labels


def _as_array(values: Iterable[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(values, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    return arr


@lru_cache(maxsize=4)
def _moment_quadrature(order: int) -> tuple[np.ndarray, np.ndarray]:
    nodes, weights = np.polynomial.legendre.leggauss(order)
    t = 0.5 * (nodes + 1.0)
    x = t / (1.0 - t)
    jacobian = 0.5 * weights / (1.0 - t) ** 2
    return x, jacobian


def occupation_moment_order3(
    eta: float | Iterable[float] | np.ndarray,
    xi: int,
    *,
    quadrature_order: int = 128,
) -> float | np.ndarray:
    """Return the order-3 occupation moment factor for the two-field path.

    ``xi`` follows the local TSC convention:

    - ``0``: classical / Maxwell-Boltzmann
    - ``1``: Bose-Einstein
    - ``-1``: Fermi-Dirac

    The returned value is the unnormalized moment integral

    ``I^(3)_xi(eta) = ∫ y^3 / (exp(y - eta) - xi) dy``.
    """

    if xi not in {-1, 0, 1}:
        raise ValueError(f"unsupported xi={xi!r}; expected one of (-1, 0, 1)")

    eta_arr = np.asarray(eta, dtype=float)
    scalar = eta_arr.ndim == 0
    eta_flat = eta_arr.reshape(-1)

    if xi == 1 and np.any(eta_flat > 1e-12):
        raise ValueError(
            "Bose-Einstein eta must remain nonpositive for the TSC source bridge"
        )

    x, quad_weights = _moment_quadrature(quadrature_order)
    exponent = np.clip(x[None, :] - eta_flat[:, None], -700.0, 700.0)
    denominator = np.exp(exponent) - float(xi)
    values = np.sum(quad_weights[None, :] * x[None, :] ** 3 / denominator, axis=1)
    reshaped = values.reshape(eta_arr.shape)
    return float(reshaped) if scalar else reshaped


@lru_cache(maxsize=3)
def _baseline_occupation_moment_order3(xi: int) -> float:
    return float(occupation_moment_order3(0.0, xi))


def occupation_moment_ratio(
    eta: float | Iterable[float] | np.ndarray,
    xi: int,
    *,
    quadrature_order: int = 128,
) -> float | np.ndarray:
    baseline = _baseline_occupation_moment_order3(xi)
    ratio = np.asarray(
        occupation_moment_order3(eta, xi, quadrature_order=quadrature_order),
        dtype=float,
    ) / baseline
    return float(ratio) if ratio.ndim == 0 else ratio


def eta_correction_indicator(
    eta: float | Iterable[float] | np.ndarray,
    xi: int,
    *,
    quadrature_order: int = 128,
) -> float:
    ratio = np.asarray(
        occupation_moment_ratio(eta, xi, quadrature_order=quadrature_order),
        dtype=float,
    )
    return float(np.max(np.abs(ratio - 1.0)))


def intensity_from_theta(
    theta: Iterable[float] | np.ndarray,
    T0: float,
    xi: int,
    eta: Iterable[float] | np.ndarray | None = None,
) -> np.ndarray:
    theta_arr = _as_array(theta)
    base = (T0 ** 4) * theta_arr ** 4
    if eta is None:
        return base
    eta_arr = np.asarray(eta, dtype=float)
    try:
        eta_broadcast = np.broadcast_to(eta_arr, theta_arr.shape)
    except ValueError as exc:
        raise ValueError(
            "eta must be broadcast-compatible with theta for the two-field path"
        ) from exc
    return base * np.asarray(occupation_moment_ratio(eta_broadcast, xi), dtype=float)


def quadrupole_from_intensity(
    intensity_samples: Iterable[float] | np.ndarray,
    directions: Iterable[float] | np.ndarray,
    weights: Iterable[float] | np.ndarray,
) -> float:
    intensity = _as_array(intensity_samples)
    mu = _as_array(directions)
    w = _as_array(weights)
    if intensity.shape != mu.shape or intensity.shape != w.shape:
        raise ValueError(
            "intensity_samples, directions, and weights must share the same shape"
        )
    weight_sum = float(np.sum(w))
    if weight_sum <= 0.0:
        raise ValueError("quadrupole weights must have positive total measure")
    p2 = 0.5 * (3.0 * mu ** 2 - 1.0)
    return float(5.0 * np.sum(w * intensity * p2) / weight_sum)


def thomson_source_from_quadrupole(q2: float, ne: float, sigma_T: float) -> float:
    return float(-(ne * sigma_T * q2) / 10.0)


def source_error_bound(delta_I_norm: float, q2_op_norm: float, ne: float, sigma_T: float) -> float:
    return float(
        abs(delta_I_norm) * abs(q2_op_norm) * abs(ne) * abs(sigma_T) / 10.0
    )


def build_source_bridge_report(
    *,
    chart: TscChart,
    q2_norm: float,
    manifest: ArtifactManifest,
    source_error: float | None,
    dipole_amplitude: float | None = None,
    eta_correction_indicator: float | None = None,
    on_manifold_exact: bool = False,
    linear_bridge_requested: bool = False,
    required_bass_primitives: tuple[str, ...] = (),
    adequacy_ratio_threshold: float = 0.10,
    inadequate_ratio_threshold: float = 1.00,
    dipole_warning_threshold: float = 0.25,
) -> TscSourceBridgeReport:
    labels: list[str] = []
    source_ratio: float | None = None
    if on_manifold_exact:
        labels.append("trace_source_exact_on_manifold")
    if source_error is not None:
        labels.append("trace_source_bound_available")
        source_ratio = abs(source_error) / max(abs(q2_norm), 1.0e-12)
        if source_ratio <= adequacy_ratio_threshold:
            labels.append("source_bound_within_budget")
        elif source_ratio >= inadequate_ratio_threshold:
            labels.append("source_bound_exceeds_budget")
        else:
            labels.append("source_bridge_bound_pending")
    else:
        labels.append("source_bridge_not_applicable")
    if eta_correction_indicator is not None:
        labels.append(
            "eta_correction_small"
            if abs(eta_correction_indicator) < 0.1
            else "eta_correction_not_small"
        )
    if (
        linear_bridge_requested
        and dipole_amplitude is not None
        and abs(dipole_amplitude) >= dipole_warning_threshold
    ):
        labels.append("linear_bridge_underestimates_risk")

    if on_manifold_exact:
        status = "adequate"
    elif source_ratio is None:
        status = "pending" if linear_bridge_requested else "inadequate"
    elif source_ratio <= adequacy_ratio_threshold:
        status = "adequate"
    elif source_ratio >= inadequate_ratio_threshold:
        status = "inadequate"
    elif linear_bridge_requested:
        status = "pending"
    else:
        status = "pending"

    return TscSourceBridgeReport(
        source_name="thomson_trace_quadrupole",
        chart=chart,
        q2_norm=q2_norm,
        source_error_bound=source_error,
        nonlinear_dipole_quartic_correction=None if dipole_amplitude is None else float(dipole_amplitude ** 4),
        eta_correction_indicator=eta_correction_indicator,
        on_manifold_exact=on_manifold_exact,
        source_status=status,  # type: ignore[arg-type]
        required_bass_primitives=required_bass_primitives,
        labels=validate_tsc_service_labels(labels),
        manifest=manifest,
    )


def build_source_bridge_report_from_samples(
    *,
    chart: TscChart,
    theta_samples: Iterable[float] | np.ndarray,
    directions: Iterable[float] | np.ndarray,
    weights: Iterable[float] | np.ndarray,
    manifest: ArtifactManifest,
    T0: float = 1.0,
    xi: int = 0,
    eta: Iterable[float] | np.ndarray | None = None,
    ne: float = 1.0,
    sigma_T: float = 1.0,
    on_manifold_exact: bool = True,
    linear_bridge_requested: bool = False,
    dipole_amplitude: float | None = None,
    source_error: float | None = None,
    q2_op_norm: float | None = None,
    required_bass_primitives: tuple[str, ...] = (),
) -> TscSourceBridgeReport:
    """Build a live source-bridge report directly from sampled angular fields."""
    theta_arr = _as_array(theta_samples)
    mu_arr = _as_array(directions)
    weight_arr = _as_array(weights)
    if theta_arr.shape != mu_arr.shape or theta_arr.shape != weight_arr.shape:
        raise ValueError("theta_samples, directions, and weights must share the same shape")

    eta_arr = None if eta is None else np.asarray(eta, dtype=float)
    intensity = intensity_from_theta(theta_arr, T0=T0, xi=xi, eta=eta_arr)
    q2 = quadrupole_from_intensity(intensity, mu_arr, weight_arr)
    _ = thomson_source_from_quadrupole(q2=q2, ne=ne, sigma_T=sigma_T)

    if source_error is None and q2_op_norm is not None and not on_manifold_exact:
        source_error = source_error_bound(
            float(np.max(np.abs(intensity))),
            q2_op_norm=q2_op_norm,
            ne=ne,
            sigma_T=sigma_T,
        )

    if dipole_amplitude is None and linear_bridge_requested:
        weight_sum = float(np.sum(weight_arr))
        dipole_amplitude = (
            float(np.sum(weight_arr * theta_arr * mu_arr) / weight_sum)
            if weight_sum > 0.0
            else 0.0
        )

    eta_indicator = None
    if eta_arr is not None:
        eta_indicator = float(eta_correction_indicator(eta_arr, xi=xi))

    primitives = required_bass_primitives
    if not primitives:
        inferred = ["theta_samples", "quadrature_weights", "electron_density", "sigma_T"]
        if eta_arr is not None:
            inferred.append("eta_samples")
        primitives = tuple(inferred)

    return build_source_bridge_report(
        chart=chart,
        q2_norm=abs(float(q2)),
        manifest=manifest,
        source_error=source_error,
        dipole_amplitude=None if dipole_amplitude is None else abs(float(dipole_amplitude)),
        eta_correction_indicator=eta_indicator,
        on_manifold_exact=on_manifold_exact,
        linear_bridge_requested=linear_bridge_requested,
        required_bass_primitives=primitives,
    )


__all__ = [
    "build_source_bridge_report",
    "build_source_bridge_report_from_samples",
    "eta_correction_indicator",
    "intensity_from_theta",
    "occupation_moment_order3",
    "occupation_moment_ratio",
    "quadrupole_from_intensity",
    "source_error_bound",
    "thomson_source_from_quadrupole",
]

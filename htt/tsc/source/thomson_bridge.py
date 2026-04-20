"""Skeleton nonlinear Thomson trace-source bridge."""
from __future__ import annotations

from typing import Iterable

import numpy as np

from common.contracts import ArtifactManifest, TscSourceBridgeReport, TscChart


def intensity_from_theta(
    theta: Iterable[float] | np.ndarray,
    T0: float,
    xi: int,
    eta: Iterable[float] | np.ndarray | None = None,
) -> np.ndarray:
    del xi
    theta_arr = np.asarray(theta, dtype=float)
    base = (T0 ** 4) * theta_arr ** 4
    if eta is None:
        return base
    eta_arr = np.asarray(eta, dtype=float)
    return base * np.exp(np.clip(eta_arr, -10.0, 10.0))


def quadrupole_from_intensity(
    intensity_samples: Iterable[float] | np.ndarray,
    directions: Iterable[float] | np.ndarray,
    weights: Iterable[float] | np.ndarray,
) -> float:
    intensity = np.asarray(intensity_samples, dtype=float)
    mu = np.asarray(directions, dtype=float)
    w = np.asarray(weights, dtype=float)
    p2 = 0.5 * (3.0 * mu ** 2 - 1.0)
    return float(np.sum(w * intensity * p2))


def thomson_source_from_quadrupole(q2: float, ne: float, sigma_T: float) -> float:
    return float(ne * sigma_T * q2)


def source_error_bound(delta_I_norm: float, q2_op_norm: float, ne: float, sigma_T: float) -> float:
    return float(abs(delta_I_norm) * abs(q2_op_norm) * abs(ne) * abs(sigma_T))


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
) -> TscSourceBridgeReport:
    labels: list[str] = []
    if on_manifold_exact:
        labels.append("trace_source_exact_on_manifold")
    if source_error is not None:
        labels.append("trace_source_bound_available")
    else:
        labels.append("source_bridge_not_applicable")
    if eta_correction_indicator is not None:
        labels.append(
            "eta_correction_small"
            if abs(eta_correction_indicator) < 0.1
            else "eta_correction_not_small"
        )
    if linear_bridge_requested and dipole_amplitude is not None and abs(dipole_amplitude) >= 0.1:
        labels.append("linear_bridge_underestimates_risk")

    if on_manifold_exact or source_error is not None:
        status = "adequate"
    elif linear_bridge_requested:
        status = "pending"
    else:
        status = "inadequate"

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
        labels=tuple(labels),
        manifest=manifest,
    )


__all__ = [
    "build_source_bridge_report",
    "intensity_from_theta",
    "quadrupole_from_intensity",
    "source_error_bound",
    "thomson_source_from_quadrupole",
]

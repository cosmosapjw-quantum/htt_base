"""VER2 chart-domain checks for active-service TSC outputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from common.contracts import ArtifactManifest, TscDomainReport, TscChart


@dataclass(frozen=True)
class DomainFlag:
    """Small typed status for one chart-domain sub-check."""

    ok: bool
    value: float | None
    reason: str | None = None


def _as_array(values: Iterable[float] | np.ndarray) -> np.ndarray:
    arr = np.asarray(tuple(values) if not isinstance(values, np.ndarray) else values, dtype=float)
    if arr.ndim == 0:
        arr = arr.reshape(1)
    return arr


def check_theta_positive(theta_samples: Iterable[float] | np.ndarray, floor: float = 0.0) -> DomainFlag:
    arr = _as_array(theta_samples)
    theta_min = float(np.min(arr))
    return DomainFlag(ok=theta_min > floor, value=theta_min, reason=None if theta_min > floor else "theta_nonpositive")


def check_be_eta_nonpositive(eta_samples: Iterable[float] | np.ndarray) -> DomainFlag:
    arr = _as_array(eta_samples)
    eta_max = float(np.max(arr))
    return DomainFlag(ok=eta_max <= 0.0, value=eta_max, reason=None if eta_max <= 0.0 else "be_eta_positive")


def check_weight_simplex(weights: Iterable[float] | np.ndarray, atol: float = 1e-8) -> DomainFlag:
    arr = _as_array(weights)
    nonnegative = bool(np.all(arr >= -atol))
    unit_sum = abs(float(np.sum(arr)) - 1.0) <= atol
    ok = nonnegative and unit_sum
    value = float(np.min(arr)) if arr.size else None
    reason = None if ok else "weight_simplex_invalid"
    return DomainFlag(ok=ok, value=value, reason=reason)


def check_jacobian_sigma_min(jacobian_singular_values: Iterable[float] | np.ndarray, floor: float) -> DomainFlag:
    arr = _as_array(jacobian_singular_values)
    sigma_min = float(np.min(arr))
    return DomainFlag(ok=sigma_min >= floor, value=sigma_min, reason=None if sigma_min >= floor else "jacobian_near_singular")


def _valid_status_for_chart(chart: TscChart) -> str:
    return {
        "one_field": "valid_one_field",
        "two_field": "valid_two_field",
        "higher_field": "higher_field_recommended",
        "full_resolved_trace": "full_resolved_trace_required",
    }[chart]


def build_domain_report(
    *,
    chart: TscChart,
    theta_samples: Iterable[float] | np.ndarray,
    manifest: ArtifactManifest,
    eta_samples: Iterable[float] | np.ndarray | None = None,
    weights: Iterable[float] | np.ndarray | None = None,
    jacobian_singular_values: Iterable[float] | np.ndarray | None = None,
    be_case: bool = False,
    sigma_min_floor: float = 1e-8,
) -> TscDomainReport:
    """Build a TSC domain report from sampled chart diagnostics.

    This is intentionally lightweight for the skeleton phase. It enforces the
    documented hard blockers and records the resulting status and margin.
    """

    theta_flag = check_theta_positive(theta_samples)
    eta_flag = (
        check_be_eta_nonpositive(eta_samples)
        if be_case and eta_samples is not None
        else DomainFlag(ok=True, value=None)
    )
    weight_flag = (
        check_weight_simplex(weights) if weights is not None else DomainFlag(ok=True, value=None)
    )
    jac_flag = (
        check_jacobian_sigma_min(jacobian_singular_values, floor=sigma_min_floor)
        if jacobian_singular_values is not None
        else DomainFlag(ok=True, value=None)
    )

    blocking_reasons = tuple(
        reason
        for reason in (theta_flag.reason, eta_flag.reason, weight_flag.reason, jac_flag.reason)
        if reason is not None
    )
    status = "invalid_domain" if blocking_reasons else _valid_status_for_chart(chart)

    margins = [theta_flag.value if theta_flag.value is not None else np.inf]
    if be_case and eta_flag.value is not None:
        margins.append(-eta_flag.value)
    if weight_flag.value is not None:
        margins.append(weight_flag.value)
    if jac_flag.value is not None:
        margins.append(jac_flag.value - sigma_min_floor)
    domain_margin = float(min(margins))

    return TscDomainReport(
        chart=chart,
        theta_min=float(theta_flag.value if theta_flag.value is not None else np.nan),
        eta_max=None if eta_flag.value is None else float(eta_flag.value),
        be_eta_nonpositive=None if not be_case else bool(eta_flag.ok),
        weight_simplex_ok=bool(weight_flag.ok),
        jacobian_sigma_min=None if jac_flag.value is None else float(jac_flag.value),
        domain_margin=domain_margin,
        status=status,  # type: ignore[arg-type]
        blocking_reasons=blocking_reasons,
        manifest=manifest,
    )


def guard_production_domain(report: TscDomainReport) -> None:
    """Reject production use when the chart domain is invalid."""
    if report.status == "invalid_domain":
        raise RuntimeError(
            "TSC production service blocked by invalid chart domain: "
            + ", ".join(report.blocking_reasons or ("unknown_domain_failure",))
        )


__all__ = [
    "DomainFlag",
    "build_domain_report",
    "check_be_eta_nonpositive",
    "check_jacobian_sigma_min",
    "check_theta_positive",
    "check_weight_simplex",
    "guard_production_domain",
]

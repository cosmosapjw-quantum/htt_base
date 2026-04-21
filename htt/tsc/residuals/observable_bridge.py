"""Conditional bridge from collision/state residuals to observable bounds."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from common.contracts import TscDomainReport, TscResidualReport
from tsc.residuals.collision_state_split import collision_side_residual, state_side_residual


ResidualBridgeStatus = Literal[
    "blocked_invalid_domain",
    "blocked_missing_state_residual",
    "blocked_collision_state_mismatch",
    "blocked_jacobian_conditioning",
    "conditional_state_bound",
    "validated_dynamical_bridge",
]


@dataclass(frozen=True)
class TscResidualBridgeReport:
    """Local TSC report that keeps `D_coll`, `D_state`, and `Delta_obs` separate."""

    collision_residual_kind: Literal["D_coll"]
    state_residual_kind: Literal["D_state"]
    observable_residual_kind: Literal["Delta_obs"]
    collision_residual: float | None
    state_residual: float | None
    observable_bound: float | None
    jacobian_sigma_min: float | None
    local_conditioning_constant: float | None
    bridge_status: ResidualBridgeStatus
    warnings: tuple[str, ...]
    dynamical_bridge_required: bool


def build_residual_bridge_report(
    *,
    collision_residual: float | None,
    state_residual: float | None,
    jacobian_sigma_min: float | None,
    sigma_min_floor: float = 1.0e-8,
    local_conditioning_constant: float = 1.0,
    domain_valid: bool = True,
    dynamical_bridge_validated: bool = False,
) -> TscResidualBridgeReport:
    """Build the local observable bridge without collapsing residual types."""
    warnings: list[str] = []
    observable_bound: float | None = None

    if not domain_valid:
        if jacobian_sigma_min is not None and jacobian_sigma_min <= sigma_min_floor:
            bridge_status = "blocked_jacobian_conditioning"
            warnings.append("observable_bridge_blocked_jacobian_conditioning")
        else:
            bridge_status = "blocked_invalid_domain"
            warnings.append("observable_bridge_blocked_invalid_domain")
    elif state_residual is None:
        if collision_residual is not None and abs(collision_residual) > 0.0:
            bridge_status = "blocked_collision_state_mismatch"
            warnings.append("observable_bridge_blocked_collision_state_mismatch")
        else:
            bridge_status = "blocked_missing_state_residual"
            warnings.append("observable_bridge_missing_state_residual")
    elif jacobian_sigma_min is None or jacobian_sigma_min <= sigma_min_floor:
        bridge_status = "blocked_jacobian_conditioning"
        warnings.append("observable_bridge_blocked_jacobian_conditioning")
    else:
        observable_bound = (
            abs(float(local_conditioning_constant))
            * abs(float(state_residual))
            / abs(float(jacobian_sigma_min))
        )
        bridge_status = (
            "validated_dynamical_bridge"
            if dynamical_bridge_validated
            else "conditional_state_bound"
        )
        warnings.append("observable_bridge_conditional")

    return TscResidualBridgeReport(
        collision_residual_kind="D_coll",
        state_residual_kind="D_state",
        observable_residual_kind="Delta_obs",
        collision_residual=(
            None if collision_residual is None else abs(float(collision_residual))
        ),
        state_residual=None if state_residual is None else abs(float(state_residual)),
        observable_bound=None if observable_bound is None else abs(float(observable_bound)),
        jacobian_sigma_min=jacobian_sigma_min,
        local_conditioning_constant=(
            None if observable_bound is None else abs(float(local_conditioning_constant))
        ),
        bridge_status=bridge_status,
        warnings=tuple(dict.fromkeys(warnings)),
        dynamical_bridge_required=bridge_status in {
            "blocked_missing_state_residual",
            "blocked_collision_state_mismatch",
        },
    )


def build_residual_bridge_from_reports(
    *,
    domain_report: TscDomainReport,
    residual_report: TscResidualReport,
    sigma_min_floor: float = 1.0e-8,
    local_conditioning_constant: float = 1.0,
    dynamical_bridge_validated: bool = False,
) -> TscResidualBridgeReport:
    """Build the local observable bridge from existing TSC reports."""
    collision = collision_side_residual(residual_report)
    state = state_side_residual(residual_report)
    return build_residual_bridge_report(
        collision_residual=collision.value,
        state_residual=state.value,
        jacobian_sigma_min=domain_report.jacobian_sigma_min,
        sigma_min_floor=sigma_min_floor,
        local_conditioning_constant=local_conditioning_constant,
        domain_valid=domain_report.status != "invalid_domain",
        dynamical_bridge_validated=dynamical_bridge_validated,
    )


__all__ = [
    "ResidualBridgeStatus",
    "TscResidualBridgeReport",
    "build_residual_bridge_from_reports",
    "build_residual_bridge_report",
]

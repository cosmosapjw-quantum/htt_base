"""Synthetic EGS-rigidity and boost-orbit diagnostics."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_EGS_CAVEAT = (
    "Synthetic BASS geometry-rigidity diagnostic only; not a data-facing "
    "geometry claim, not family identification, and not native solver validation."
)


def _finite_nonnegative(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ValueError(f"{name} must be non-negative finite")
    return number


def _base_payload(obj: object) -> dict[str, Any]:
    return {
        "owner": "BASS",
        "implementation_scope": "bass_py",
        "claim_tier": "diagnostic_only",
        "transfer_source": "none",
        "production_claim_allowed": False,
        "native_solver_result": False,
        "family_identification": False,
        "caveats": [DEFAULT_EGS_CAVEAT],
    }


@dataclass(frozen=True)
class BoostedRadiationOrbit:
    theorem_id: str
    orbit_status: str
    beta: float
    direction_norm: float
    gamma: float
    data_facing_residual_allowed: bool
    systematics_status: str
    mask_status: str
    null_status: str
    raw_data_provenance_status: str
    covariance_status: str
    ppc_loocv_status: str
    prior_sensitivity_status: str
    transfer_provenance_status: str
    native_atlas_status: str
    residual_gate_status: str

    def as_payload(self) -> dict[str, Any]:
        payload = _base_payload(self)
        payload.update(
            {
                "theorem_id": self.theorem_id,
                "orbit_status": self.orbit_status,
                "beta": self.beta,
                "direction_norm": self.direction_norm,
                "gamma": self.gamma,
                "data_facing_residual_allowed": self.data_facing_residual_allowed,
                "systematics_status": self.systematics_status,
                "mask_status": self.mask_status,
                "null_status": self.null_status,
                "raw_data_provenance_status": self.raw_data_provenance_status,
                "covariance_status": self.covariance_status,
                "ppc_loocv_status": self.ppc_loocv_status,
                "prior_sensitivity_status": self.prior_sensitivity_status,
                "transfer_provenance_status": self.transfer_provenance_status,
                "native_atlas_status": self.native_atlas_status,
                "residual_gate_status": self.residual_gate_status,
            }
        )
        return payload


@dataclass(frozen=True)
class SlopeDegeneracyClassification:
    theorem_id: str
    classification: str
    slope_only_source_discrimination_allowed: bool
    slope_difference: float

    def as_payload(self) -> dict[str, Any]:
        payload = _base_payload(self)
        payload.update(
            {
                "theorem_id": self.theorem_id,
                "classification": self.classification,
                "slope_only_source_discrimination_allowed": self.slope_only_source_discrimination_allowed,
                "slope_difference": self.slope_difference,
            }
        )
        return payload


@dataclass(frozen=True)
class AlmostEgsGate:
    theorem_id: str
    egs_status: str
    almost_egs_promotion_allowed: bool
    diagnostic_bound: float | None

    def as_payload(self) -> dict[str, Any]:
        payload = _base_payload(self)
        payload.update(
            {
                "theorem_id": self.theorem_id,
                "egs_status": self.egs_status,
                "almost_egs_promotion_allowed": self.almost_egs_promotion_allowed,
                "diagnostic_bound": self.diagnostic_bound,
            }
        )
        return payload


@dataclass(frozen=True)
class BianchiIExactFlowGate:
    theorem_id: str
    exact_flow_status: str
    exact_flow_use_allowed: bool
    assumptions: tuple[str, ...]

    def as_payload(self) -> dict[str, Any]:
        payload = _base_payload(self)
        payload.update(
            {
                "theorem_id": self.theorem_id,
                "exact_flow_status": self.exact_flow_status,
                "exact_flow_use_allowed": self.exact_flow_use_allowed,
                "assumptions": list(self.assumptions),
            }
        )
        return payload


def boosted_radiation_orbit(
    *,
    beta: float,
    direction_norm: float,
    theorem_id: str,
    systematics_status: str = "not_bound",
    mask_status: str = "not_bound",
    null_status: str = "not_bound",
    raw_data_provenance_status: str = "not_bound",
    covariance_status: str = "not_bound",
    ppc_loocv_status: str = "not_bound",
    prior_sensitivity_status: str = "not_bound",
    transfer_provenance_status: str = "not_bound",
    native_atlas_status: str = "not_bound",
) -> BoostedRadiationOrbit:
    beta_value = _finite_nonnegative(beta, "beta")
    direction = _finite_nonnegative(direction_norm, "direction_norm")
    data_gate_statuses = (
        systematics_status,
        mask_status,
        null_status,
        raw_data_provenance_status,
        covariance_status,
        ppc_loocv_status,
        prior_sensitivity_status,
        transfer_provenance_status,
        native_atlas_status,
    )
    data_ready = all(status == "bound" for status in data_gate_statuses)
    return BoostedRadiationOrbit(
        theorem_id=theorem_id,
        orbit_status="synthetic_boosted_radiation_orbit",
        beta=beta_value,
        direction_norm=direction,
        gamma=math.cosh(beta_value),
        data_facing_residual_allowed=data_ready,
        systematics_status=systematics_status,
        mask_status=mask_status,
        null_status=null_status,
        raw_data_provenance_status=raw_data_provenance_status,
        covariance_status=covariance_status,
        ppc_loocv_status=ppc_loocv_status,
        prior_sensitivity_status=prior_sensitivity_status,
        transfer_provenance_status=transfer_provenance_status,
        native_atlas_status=native_atlas_status,
        residual_gate_status="all_data_residual_gates_bound"
        if data_ready
        else "blocked_observational_residual_provenance_not_bound",
    )


def classify_slope_degeneracy(
    *,
    slope_a: float,
    slope_b: float,
    tolerance: float,
    equation_of_state_w: float,
    theorem_id: str,
) -> SlopeDegeneracyClassification:
    a = float(slope_a)
    b = float(slope_b)
    tol = _finite_nonnegative(tolerance, "tolerance")
    w = float(equation_of_state_w)
    if not all(math.isfinite(value) for value in (a, b, w)):
        raise ValueError("slopes and equation_of_state_w must be finite")
    diff = abs(a - b)
    if abs(w - 1.0) <= max(tol, 1.0e-12):
        status = "blocked_stiff_fluid_singularity"
    elif diff <= tol:
        status = "slope_degenerate"
    else:
        status = "synthetic_slope_distinct"
    return SlopeDegeneracyClassification(
        theorem_id=theorem_id,
        classification=status,
        slope_only_source_discrimination_allowed=False,
        slope_difference=diff,
    )


def almost_egs_promotion_gate(
    *,
    acceleration_bound: float | None,
    temperature_gradient_bound: float | None,
    derivative_bound: float | None,
    weyl_diagnostics_bound: float | None,
    theorem_id: str,
) -> AlmostEgsGate:
    if acceleration_bound is None or temperature_gradient_bound is None:
        return AlmostEgsGate(
            theorem_id=theorem_id,
            egs_status="blocked_acceleration_temp_gradient_missing",
            almost_egs_promotion_allowed=False,
            diagnostic_bound=None,
        )
    if derivative_bound is None or weyl_diagnostics_bound is None:
        return AlmostEgsGate(
            theorem_id=theorem_id,
            egs_status="blocked_derivative_weyl_diagnostics_missing",
            almost_egs_promotion_allowed=False,
            diagnostic_bound=None,
        )
    values = (
        _finite_nonnegative(acceleration_bound, "acceleration_bound"),
        _finite_nonnegative(temperature_gradient_bound, "temperature_gradient_bound"),
        _finite_nonnegative(derivative_bound, "derivative_bound"),
        _finite_nonnegative(weyl_diagnostics_bound, "weyl_diagnostics_bound"),
    )
    return AlmostEgsGate(
        theorem_id=theorem_id,
        egs_status="synthetic_almost_egs_bound",
        almost_egs_promotion_allowed=False,
        diagnostic_bound=sum(values),
    )


def bianchi_i_exact_flow_gate(
    *,
    assumptions: Sequence[str],
    theorem_id: str,
) -> BianchiIExactFlowGate:
    values = tuple(str(item).strip() for item in assumptions)
    required = {"homogeneous_background", "bianchi_i", "diagonal_shear"}
    ready = required <= set(values)
    return BianchiIExactFlowGate(
        theorem_id=theorem_id,
        exact_flow_status="synthetic_bianchi_i_exact_flow_scope" if ready else "blocked_missing_bianchi_i_assumptions",
        exact_flow_use_allowed=ready,
        assumptions=values,
    )

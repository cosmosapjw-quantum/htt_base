"""Typed weak-identification decision for local/global response geometry.

This module separates algebraic direct-sum rank from practical source
separation.  A full-rank response can remain weakly identified when its
registered principal angle or its normalizer-bound relative singular value is
too small.  The result is diagnostic-only and never identifies a physical
source, geometry, or Bianchi family.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Integral, Real
from typing import Sequence


class SourceSeparationError(ValueError):
    """Raised when a weak-identification contract is invalid or inconsistent."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SourceSeparationDecisionStatus(_StringEnum):
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"
    NON_IDENTIFIED = "NON_IDENTIFIED"
    SUM_ONLY = "SUM_ONLY"
    WEAKLY_IDENTIFIED = "WEAKLY_IDENTIFIED"
    SEPARABLE_CANDIDATE = "SEPARABLE_CANDIDATE"


_THRESHOLD_TOKEN = object()
_DECISION_TOKEN = object()
_UNITS = "dimensionless_beta_c_equals_1"
_ALLOWED_USE = (
    "normalizer-bound local/global weak-identification diagnostic",
    "mandatory open-set abstention",
)
_FORBIDDEN_USE = (
    "physical local/global source attribution",
    "point estimate under weak identification",
    "FLRW departure or geometry detection",
    "Bianchi family identification or ranking",
    "native-solver validation",
    "posterior, Bayes factor, p-value, e-value, or evidence term",
)


def _canonical_id(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise SourceSeparationError(f"{name} must be non-empty trimmed text")
    return value


def _identity(value: object, name: str) -> str:
    out = _text(value, name)
    digest = out[7:] if out.startswith("sha256:") else ""
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise SourceSeparationError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise SourceSeparationError(f"{name} must be a finite real number")
    out = float(value)
    if not math.isfinite(out):
        raise SourceSeparationError(f"{name} must be a finite real number")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise SourceSeparationError(f"{name} must be non-negative")
    return out


def _positive_count(value: object, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise SourceSeparationError(f"{name} must be a positive integer")
    out = int(value)
    if out <= 0:
        raise SourceSeparationError(f"{name} must be a positive integer")
    return out


def _rank(value: object, name: str, *, maximum: int) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, Integral):
        raise SourceSeparationError(f"{name} must be an integer rank")
    out = int(value)
    if out < 0 or out > maximum:
        raise SourceSeparationError(f"{name} is outside its declared dimension")
    return out


def _values(
    raw: Sequence[object],
    name: str,
    *,
    maximum: float | None = None,
) -> tuple[float, ...]:
    if isinstance(raw, (str, bytes)) or not isinstance(raw, Sequence):
        raise SourceSeparationError(f"{name} must be a numeric sequence")
    values = tuple(_nonnegative(value, name) for value in raw)
    if maximum is not None and any(value > maximum for value in values):
        raise SourceSeparationError(f"{name} exceeds its allowed range")
    return values


@dataclass(frozen=True)
class WeakIdentificationThresholdContract:
    """Thresholds registered before an open-set observation is evaluated."""

    minimum_principal_angle_radians: float
    minimum_normalizer_bound_relative_joint_singular_value: float
    parameter_coordinate_units: str
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _THRESHOLD_TOKEN:
            raise SourceSeparationError(
                "WeakIdentificationThresholdContract must be factory-derived"
            )
        angle = _nonnegative(
            self.minimum_principal_angle_radians,
            "minimum_principal_angle_radians",
        )
        if angle > math.pi / 2.0:
            raise SourceSeparationError(
                "minimum_principal_angle_radians must not exceed pi/2"
            )
        relative = _nonnegative(
            self.minimum_normalizer_bound_relative_joint_singular_value,
            "minimum_normalizer_bound_relative_joint_singular_value",
        )
        if relative > 1.0:
            raise SourceSeparationError(
                "relative joint singular-value threshold must not exceed one"
            )
        units = _text(self.parameter_coordinate_units, "parameter_coordinate_units")
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise SourceSeparationError("weak-identification claim boundary drifted")
        object.__setattr__(self, "minimum_principal_angle_radians", angle)
        object.__setattr__(
            self,
            "minimum_normalizer_bound_relative_joint_singular_value",
            relative,
        )
        object.__setattr__(self, "parameter_coordinate_units", units)

    @property
    def contract_id(self) -> str:
        return _canonical_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_WEAK_IDENTIFICATION_THRESHOLDS_V1",
            "minimum_principal_angle_radians": self.minimum_principal_angle_radians,
            "minimum_normalizer_bound_relative_joint_singular_value": (
                self.minimum_normalizer_bound_relative_joint_singular_value
            ),
            "parameter_coordinate_units": self.parameter_coordinate_units,
            "comparison_rule": "both_metrics_must_strictly_exceed_thresholds",
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def build_weak_identification_threshold_contract(
    *,
    minimum_principal_angle_radians: float,
    minimum_normalizer_bound_relative_joint_singular_value: float,
    parameter_coordinate_units: str = _UNITS,
) -> WeakIdentificationThresholdContract:
    return WeakIdentificationThresholdContract(
        minimum_principal_angle_radians=minimum_principal_angle_radians,
        minimum_normalizer_bound_relative_joint_singular_value=(
            minimum_normalizer_bound_relative_joint_singular_value
        ),
        parameter_coordinate_units=parameter_coordinate_units,
        _construction_token=_THRESHOLD_TOKEN,
    )


@dataclass(frozen=True)
class SourceSeparationDecision:
    """Content-addressed projection of one source-response geometry report."""

    status: SourceSeparationDecisionStatus
    source_geometry_report_id: str
    covariance_id: str
    nuisance_tangent_id: str
    normalizer_id: str
    normalizer_source_identity: str
    normalizer_coordinate_map_id: str
    parameter_coordinate_units: str
    provider_available: bool
    covariance_supported: bool
    local_parameter_count: int
    global_parameter_count: int
    local_rank: int | None
    global_rank: int | None
    joint_rank: int | None
    principal_angles_radians: tuple[float, ...]
    principal_angles_content_id: str
    joint_singular_values: tuple[float, ...]
    joint_singular_values_content_id: str
    minimum_principal_angle_radians: float | None
    minimum_relative_joint_singular_value: float | None
    threshold_contract: WeakIdentificationThresholdContract
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DECISION_TOKEN:
            raise SourceSeparationError(
                "SourceSeparationDecision must be factory-derived"
            )
        if not isinstance(self.status, SourceSeparationDecisionStatus):
            raise SourceSeparationError("source-separation decision status is invalid")
        for name in (
            "source_geometry_report_id",
            "covariance_id",
            "nuisance_tangent_id",
            "normalizer_coordinate_map_id",
        ):
            _identity(getattr(self, name), name)
        _text(self.normalizer_id, "normalizer_id")
        _text(self.normalizer_source_identity, "normalizer_source_identity")
        _text(self.parameter_coordinate_units, "parameter_coordinate_units")
        if type(self.provider_available) is not bool or type(self.covariance_supported) is not bool:
            raise SourceSeparationError("availability/support flags must be booleans")
        _positive_count(self.local_parameter_count, "local_parameter_count")
        _positive_count(self.global_parameter_count, "global_parameter_count")
        if type(self.threshold_contract) is not WeakIdentificationThresholdContract:
            raise SourceSeparationError("threshold_contract must be factory-derived")
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise SourceSeparationError("source-separation claim boundary drifted")
        if self.principal_angles_content_id != _canonical_id(
            {
                "schema": "COMMON_PRINCIPAL_ANGLES_V1",
                "values": list(self.principal_angles_radians),
            }
        ):
            raise SourceSeparationError("principal-angle content identity drifted")
        if self.joint_singular_values_content_id != _canonical_id(
            {
                "schema": "COMMON_JOINT_SINGULAR_VALUES_V1",
                "values": list(self.joint_singular_values),
            }
        ):
            raise SourceSeparationError("joint singular-value content identity drifted")

    @property
    def decision_id(self) -> str:
        return _canonical_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "schema": "COMMON_SOURCE_SEPARATION_DECISION_V1",
            "status": self.status.value,
            "source_geometry_report_id": self.source_geometry_report_id,
            "covariance_id": self.covariance_id,
            "nuisance_tangent_id": self.nuisance_tangent_id,
            "normalizer_id": self.normalizer_id,
            "normalizer_source_identity": self.normalizer_source_identity,
            "normalizer_coordinate_map_id": self.normalizer_coordinate_map_id,
            "parameter_coordinate_units": self.parameter_coordinate_units,
            "provider_available": self.provider_available,
            "covariance_supported": self.covariance_supported,
            "local_parameter_count": self.local_parameter_count,
            "global_parameter_count": self.global_parameter_count,
            "local_rank": self.local_rank,
            "global_rank": self.global_rank,
            "joint_rank": self.joint_rank,
            "principal_angles_radians": list(self.principal_angles_radians),
            "principal_angles_content_id": self.principal_angles_content_id,
            "joint_singular_values": list(self.joint_singular_values),
            "joint_singular_values_content_id": self.joint_singular_values_content_id,
            "minimum_principal_angle_radians": self.minimum_principal_angle_radians,
            "minimum_relative_joint_singular_value": (
                self.minimum_relative_joint_singular_value
            ),
            "threshold_contract": self.threshold_contract.as_payload(),
            "threshold_contract_id": self.threshold_contract.contract_id,
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def evaluate_source_separation(
    *,
    source_geometry_report_id: str,
    covariance_id: str,
    nuisance_tangent_id: str,
    normalizer_id: str,
    normalizer_source_identity: str,
    normalizer_coordinate_map_id: str,
    parameter_coordinate_units: str,
    provider_available: bool,
    covariance_supported: bool,
    local_parameter_count: int,
    global_parameter_count: int,
    local_rank: int | None,
    global_rank: int | None,
    joint_rank: int | None,
    principal_angles_radians: Sequence[object],
    joint_singular_values: Sequence[object],
    threshold_contract: WeakIdentificationThresholdContract,
) -> SourceSeparationDecision:
    """Evaluate the registered rank/angle/conditioning ladder fail closed."""

    report_id = _identity(source_geometry_report_id, "source_geometry_report_id")
    covariance = _identity(covariance_id, "covariance_id")
    nuisance = _identity(nuisance_tangent_id, "nuisance_tangent_id")
    normalizer = _text(normalizer_id, "normalizer_id")
    normalizer_source = _text(
        normalizer_source_identity, "normalizer_source_identity"
    )
    normalizer_map = _identity(
        normalizer_coordinate_map_id, "normalizer_coordinate_map_id"
    )
    units = _text(parameter_coordinate_units, "parameter_coordinate_units")
    if type(threshold_contract) is not WeakIdentificationThresholdContract:
        raise SourceSeparationError("threshold_contract must be factory-derived")
    if units != threshold_contract.parameter_coordinate_units:
        raise SourceSeparationError(
            "threshold and source geometry parameter-coordinate units differ"
        )
    if type(provider_available) is not bool or type(covariance_supported) is not bool:
        raise SourceSeparationError("availability/support flags must be booleans")
    local_count = _positive_count(local_parameter_count, "local_parameter_count")
    global_count = _positive_count(global_parameter_count, "global_parameter_count")
    local_value = _rank(local_rank, "local_rank", maximum=local_count)
    global_value = _rank(global_rank, "global_rank", maximum=global_count)
    joint_value = _rank(
        joint_rank,
        "joint_rank",
        maximum=local_count + global_count,
    )
    angles = _values(
        principal_angles_radians,
        "principal_angles_radians",
        maximum=math.pi / 2.0,
    )
    singular = _values(joint_singular_values, "joint_singular_values")
    if any(left < right for left, right in zip(singular, singular[1:])):
        raise SourceSeparationError(
            "joint_singular_values must be in non-increasing order"
        )
    if len(singular) > local_count + global_count:
        raise SourceSeparationError(
            "joint singular-value count cannot exceed the total parameter "
            "dimension"
        )
    if not provider_available:
        if covariance_supported:
            raise SourceSeparationError(
                "missing providers cannot have measured covariance support"
            )
        if (
            any(
                value is not None
                for value in (local_value, global_value, joint_value)
            )
            or angles
            or singular
        ):
            raise SourceSeparationError(
                "missing providers must not carry measured geometry values"
            )
        status = SourceSeparationDecisionStatus.MISSING_RESPONSE_PROVIDER
        minimum_angle = None
        relative_singular = None
    else:
        if any(value is None for value in (local_value, global_value, joint_value)):
            raise SourceSeparationError(
                "available providers require complete rank measurements"
            )
        if not singular:
            raise SourceSeparationError(
                "available providers require joint singular values"
            )
        assert joint_value is not None
        if (
            len(singular) < joint_value
            or sum(value > 0.0 for value in singular) < joint_value
        ):
            raise SourceSeparationError(
                "joint singular values do not support the declared joint rank"
            )
        maximum_singular = singular[0]
        relative_singular = (
            0.0 if maximum_singular == 0.0 else singular[-1] / maximum_singular
        )
        minimum_angle = min(angles) if angles else None
        if not covariance_supported:
            status = SourceSeparationDecisionStatus.NON_IDENTIFIED
        elif local_value < local_count or global_value < global_count:
            status = SourceSeparationDecisionStatus.NON_IDENTIFIED
        elif joint_value < local_value + global_value:
            status = SourceSeparationDecisionStatus.SUM_ONLY
        else:
            if minimum_angle is None:
                raise SourceSeparationError(
                    "full component ranks require measured principal angles"
                )
            if len(angles) != min(local_count, global_count):
                raise SourceSeparationError(
                    "principal-angle count does not match the full component ranks"
                )
            if joint_value != local_count + global_count:
                raise SourceSeparationError(
                    "full direct-sum classification requires full joint rank"
                )
            if (
                minimum_angle
                <= threshold_contract.minimum_principal_angle_radians
                or relative_singular
                <= threshold_contract.minimum_normalizer_bound_relative_joint_singular_value
            ):
                status = SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED
            else:
                status = SourceSeparationDecisionStatus.SEPARABLE_CANDIDATE
    angles_id = _canonical_id(
        {"schema": "COMMON_PRINCIPAL_ANGLES_V1", "values": list(angles)}
    )
    singular_id = _canonical_id(
        {"schema": "COMMON_JOINT_SINGULAR_VALUES_V1", "values": list(singular)}
    )
    return SourceSeparationDecision(
        status=status,
        source_geometry_report_id=report_id,
        covariance_id=covariance,
        nuisance_tangent_id=nuisance,
        normalizer_id=normalizer,
        normalizer_source_identity=normalizer_source,
        normalizer_coordinate_map_id=normalizer_map,
        parameter_coordinate_units=units,
        provider_available=provider_available,
        covariance_supported=covariance_supported,
        local_parameter_count=local_count,
        global_parameter_count=global_count,
        local_rank=local_value,
        global_rank=global_value,
        joint_rank=joint_value,
        principal_angles_radians=angles,
        principal_angles_content_id=angles_id,
        joint_singular_values=singular,
        joint_singular_values_content_id=singular_id,
        minimum_principal_angle_radians=minimum_angle,
        minimum_relative_joint_singular_value=relative_singular,
        threshold_contract=threshold_contract,
        _construction_token=_DECISION_TOKEN,
    )


def revalidate_source_separation_decision(
    decision: SourceSeparationDecision,
) -> SourceSeparationDecision:
    if type(decision) is not SourceSeparationDecision:
        raise SourceSeparationError(
            "decision must be an exact SourceSeparationDecision"
        )
    rebuilt = evaluate_source_separation(
        source_geometry_report_id=decision.source_geometry_report_id,
        covariance_id=decision.covariance_id,
        nuisance_tangent_id=decision.nuisance_tangent_id,
        normalizer_id=decision.normalizer_id,
        normalizer_source_identity=decision.normalizer_source_identity,
        normalizer_coordinate_map_id=decision.normalizer_coordinate_map_id,
        parameter_coordinate_units=decision.parameter_coordinate_units,
        provider_available=decision.provider_available,
        covariance_supported=decision.covariance_supported,
        local_parameter_count=decision.local_parameter_count,
        global_parameter_count=decision.global_parameter_count,
        local_rank=decision.local_rank,
        global_rank=decision.global_rank,
        joint_rank=decision.joint_rank,
        principal_angles_radians=decision.principal_angles_radians,
        joint_singular_values=decision.joint_singular_values,
        threshold_contract=decision.threshold_contract,
    )
    if rebuilt != decision:
        raise SourceSeparationError("source-separation decision failed replay")
    return decision


__all__ = [
    "SourceSeparationDecision",
    "SourceSeparationDecisionStatus",
    "SourceSeparationError",
    "WeakIdentificationThresholdContract",
    "build_weak_identification_threshold_contract",
    "evaluate_source_separation",
    "revalidate_source_separation_decision",
]

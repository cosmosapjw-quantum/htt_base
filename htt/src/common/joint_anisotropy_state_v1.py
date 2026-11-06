"""Canonical vector/tensor anisotropy-state contracts for PR-261.

The contracts in this module keep three physically different objects apart:

* :class:`CongruenceKinematics` stores kinematics *of* one declared
  congruence;
* :class:`VelocityFrameBundle` stores velocities *between* the radiation,
  matter, and observer frames; and
* :class:`GeometryState` stores the signed scalar curvature-budget coordinate
  separately from optional anisotropic geometry tensors.

The composition is diagnostic-only and pre-solver.  Missing components are
typed and never replaced by zero.  In particular, a legacy
``DepartureState.beta_a`` is not assigned a radiation/matter/observer role
unless an explicit adapter binding supplies that semantic fact.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
import json
import math
from numbers import Real
from typing import ClassVar, Mapping, Sequence

import numpy as np

from common.enum_compat import StrEnum
from common.orbit_nonlinearity import (
    O3Transform,
    STF5_CARTESIAN_BASIS,
    matrix_to_stf5,
    stf5_to_matrix,
)
from common.statistical_foundations import DepartureState
from common.transfer_registry import (
    TransferFunctionSpec,
    TransferSource,
    TransferValidRange,
)


class JointAnisotropyStateError(ValueError):
    """Raised when a joint-state contract is incomplete or inconsistent."""


class MissingComponentStatus(StrEnum):
    """Fail-closed status for a component that has no numerical value."""

    MISSING = "MISSING"
    ABSTAIN = "ABSTAIN"
    NEEDS_NATIVE = "NEEDS_NATIVE"


class UnitsConvention(StrEnum):
    """Registered normalization branch for congruence kinematics."""

    EXPLICIT_C_THETA_NORMALIZED = "EXPLICIT_C_THETA_NORMALIZED"
    C_EQUALS_ONE_THETA_NORMALIZED = "C_EQUALS_ONE_THETA_NORMALIZED"


class VelocityNormalization(StrEnum):
    """Velocity normalization retained independently of the unit branch."""

    BETA_EQUALS_V_OVER_C = "BETA_EQUALS_V_OVER_C"


class AccelerationNormalization(StrEnum):
    """The two acceleration normalizations that must never mix silently."""

    A_OVER_C_THETA = "A_OVER_C_THETA"
    A_OVER_THETA_C_EQUALS_ONE = "A_OVER_THETA_C_EQUALS_ONE"


class VelocityClosureStatus(StrEnum):
    """First-order velocity-frame closure status."""

    CLOSURE_VERIFIED = "CLOSURE_VERIFIED"
    CLOSURE_MISMATCH = "CLOSURE_MISMATCH"
    SUM_ONLY = "SUM_ONLY"
    MISSING_COMPONENT = "MISSING_COMPONENT"


class GeometryCompleteness(StrEnum):
    """Completeness of the geometry layer, not a geometry verdict."""

    PARTIAL = "PARTIAL"
    COMPLETE_REGISTERED_COMPONENTS = "COMPLETE_REGISTERED_COMPONENTS"


class BetaSemanticRole(StrEnum):
    """Declared meaning of the legacy or direct beta coordinate."""

    DIRECT_STATE = "DIRECT_STATE"
    BETA_RO = "BETA_RO"
    BETA_RM = "BETA_RM"
    BETA_MO = "BETA_MO"
    UNRESOLVED = "UNRESOLVED"


class JointStateSourceKind(StrEnum):
    """How the current typed state was produced."""

    DIRECT = "DIRECT"
    LEGACY_DEPARTURE_ADAPTER = "LEGACY_DEPARTURE_ADAPTER"
    O3_ACTION = "O3_ACTION"
    UNIT_CONVERSION = "UNIT_CONVERSION"


class LegacyAdapterStatus(StrEnum):
    """Outcome of the explicit legacy-state adapter."""

    ADAPTED = "ADAPTED"
    ABSTAIN = "ABSTAIN"


KINEMATICS_PARITY_CONTRACT = (
    "SIGMA_STF2_POLAR;OMEGA_VECTOR_AXIAL;ACCELERATION_VECTOR_POLAR"
)
VELOCITY_PARITY_CONTRACT = (
    "BETA_RO_POLAR;BETA_RM_POLAR;BETA_MO_POLAR"
)
GEOMETRY_PARITY_CONTRACT = (
    "DELTA_OMEGA_K_SCALAR;"
    "SPATIAL_CURVATURE_STF2_POLAR;"
    "ELECTRIC_WEYL_STF2_POLAR;"
    "MAGNETIC_WEYL_STF2_AXIAL;"
    "ANISOTROPIC_STRESS_STF2_POLAR"
)
FIRST_ORDER_VELOCITY_RELATION = (
    "beta_RO = beta_RM + beta_MO + O(beta^2)"
)
PR256_ALLOWED_USE = (
    "first-order velocity-frame closure diagnostic",
    "explicit reporting of unresolved velocity components",
)
PR256_FORBIDDEN_USE = (
    "global-tilt detection",
    "source attribution from closure",
    "reinterpretation of DepartureState.beta_a",
)
JOINT_STATE_CLAIM_CEILING = "diagnostic_only"
JOINT_STATE_ALLOWED_USE = (
    "typed pre-solver state transport",
    "component-aware diagnostic functional input",
    "explicit legacy projection compatibility",
)
JOINT_STATE_FORBIDDEN_USE = (
    "scalar-to-vector or scalar-to-tensor inference",
    "FLRW converse from component zeros",
    "global-tilt or geometry detection",
    "native solver result",
    "Bianchi family identification",
    "posterior, evidence, or truth certificate",
)

_VELOCITY_TOKEN = object()
_LEGACY_ADAPTER_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise JointAnisotropyStateError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = True,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise JointAnisotropyStateError(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not empty_ok and not out:
        raise JointAnisotropyStateError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise JointAnisotropyStateError(f"{name} must not contain duplicates")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise JointAnisotropyStateError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise JointAnisotropyStateError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise JointAnisotropyStateError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise JointAnisotropyStateError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise JointAnisotropyStateError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise JointAnisotropyStateError(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _real(value, name)
    if out <= 0.0:
        raise JointAnisotropyStateError(f"{name} must be positive")
    return out


def _vector(value: object, name: str, *, length: int) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise JointAnisotropyStateError(
            f"{name} must be a length-{length} sequence"
        )
    if len(value) != length:
        raise JointAnisotropyStateError(
            f"{name} must have length {length}, got {len(value)}"
        )
    return tuple(
        _real(item, f"{name}[{index}]")
        for index, item in enumerate(value)
    )


def _enum(value: object, enum_type: type[StrEnum], name: str) -> StrEnum:
    try:
        return value if isinstance(value, enum_type) else enum_type(str(value))
    except ValueError as exc:
        raise JointAnisotropyStateError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


def _exact_keys(
    payload: Mapping[str, object],
    expected: set[str],
    *,
    name: str,
) -> None:
    actual = set(payload)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise JointAnisotropyStateError(
            f"{name} keys mismatch; missing={missing}, extra={extra}"
        )


def _content_id(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _receipt(value: object, name: str) -> str:
    out = _text(value, name)
    digest = out[7:] if out.startswith("sha256:") else ""
    if len(digest) != 64 or any(
        character not in "0123456789abcdef" for character in digest
    ):
        raise JointAnisotropyStateError(
            f"{name} must be a lowercase sha256 receipt identity"
        )
    return out


def _vector_norm(value: tuple[float, ...]) -> float:
    return math.sqrt(sum(component * component for component in value))


@dataclass(frozen=True)
class MissingComponent:
    """Typed absence record used instead of an inferred numerical zero."""

    component: str
    status: MissingComponentStatus | str
    reason: str
    required_for: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "component", _text(self.component, "component"))
        object.__setattr__(
            self,
            "status",
            _enum(self.status, MissingComponentStatus, "status"),
        )
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(
            self,
            "required_for",
            _texts(self.required_for, "required_for"),
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "component": self.component,
            "reason": self.reason,
            "required_for": list(self.required_for),
            "status": self.status.value,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "MissingComponent":
        if not isinstance(payload, Mapping):
            raise JointAnisotropyStateError(
                "missing-component payload must be a mapping"
            )
        _exact_keys(
            payload,
            {"component", "reason", "required_for", "status"},
            name="missing-component payload",
        )
        return cls(
            component=payload["component"],
            status=payload["status"],
            reason=payload["reason"],
            required_for=payload["required_for"],  # type: ignore[arg-type]
        )


VectorOrMissing = tuple[float, ...] | MissingComponent
ScalarOrMissing = float | MissingComponent


def missing_component(
    component: str,
    reason: str,
    *,
    status: MissingComponentStatus = MissingComponentStatus.MISSING,
    required_for: Sequence[str] = (),
) -> MissingComponent:
    """Create an explicit absence record with no numerical placeholder."""

    return MissingComponent(
        component=component,
        status=status,
        reason=reason,
        required_for=tuple(required_for),
    )


def _component(
    value: object,
    name: str,
    *,
    length: int,
) -> VectorOrMissing:
    if type(value) is MissingComponent:
        if value.component != name:
            raise JointAnisotropyStateError(
                f"{name} absence record names {value.component!r}"
            )
        return value
    return _vector(value, name, length=length)


def _component_payload(value: VectorOrMissing) -> object:
    if type(value) is MissingComponent:
        return {"missing": value.to_payload()}
    return list(value)


def _component_from_payload(
    value: object,
    name: str,
    *,
    length: int,
) -> VectorOrMissing:
    if isinstance(value, Mapping):
        _exact_keys(value, {"missing"}, name=f"{name} component payload")
        missing = MissingComponent.from_payload(value["missing"])
        if missing.component != name:
            raise JointAnisotropyStateError(
                f"{name} payload names missing component {missing.component!r}"
            )
        return missing
    return _vector(value, name, length=length)


def _scalar_payload(value: ScalarOrMissing) -> object:
    if type(value) is MissingComponent:
        return {"missing": value.to_payload()}
    return value


@dataclass(frozen=True)
class CongruenceKinematics:
    """STF shear, axial vorticity, and optional polar acceleration."""

    sigma_stf5: tuple[float, ...]
    omega_axial3: tuple[float, ...]
    acceleration_polar3: VectorOrMissing
    frame: str
    congruence_id: str
    epoch_window: str
    averaging_scale: str
    basis: str
    units_convention: UnitsConvention | str
    velocity_normalization: VelocityNormalization | str
    perturbative_order: str
    acceleration_normalization: AccelerationNormalization | str | None
    parity_contract: str = KINEMATICS_PARITY_CONTRACT

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "sigma_stf5",
            _vector(self.sigma_stf5, "sigma_stf5", length=5),
        )
        object.__setattr__(
            self,
            "omega_axial3",
            _vector(self.omega_axial3, "omega_axial3", length=3),
        )
        acceleration = _component(
            self.acceleration_polar3,
            "acceleration_polar3",
            length=3,
        )
        object.__setattr__(self, "acceleration_polar3", acceleration)
        for name in (
            "frame",
            "congruence_id",
            "epoch_window",
            "averaging_scale",
            "basis",
            "perturbative_order",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        units = _enum(
            self.units_convention,
            UnitsConvention,
            "units_convention",
        )
        velocity = _enum(
            self.velocity_normalization,
            VelocityNormalization,
            "velocity_normalization",
        )
        object.__setattr__(self, "units_convention", units)
        object.__setattr__(self, "velocity_normalization", velocity)
        if self.parity_contract != KINEMATICS_PARITY_CONTRACT:
            raise JointAnisotropyStateError(
                "kinematics must retain the registered parity contract"
            )
        if type(acceleration) is MissingComponent:
            if self.acceleration_normalization is not None:
                raise JointAnisotropyStateError(
                    "missing acceleration must not carry a normalization"
                )
        else:
            if self.acceleration_normalization is None:
                raise JointAnisotropyStateError(
                    "available acceleration requires acceleration_normalization"
                )
            normalization = _enum(
                self.acceleration_normalization,
                AccelerationNormalization,
                "acceleration_normalization",
            )
            expected = (
                AccelerationNormalization.A_OVER_C_THETA
                if units is UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
                else AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
            )
            if normalization is not expected:
                raise JointAnisotropyStateError(
                    "acceleration normalization does not match units_convention"
                )
            object.__setattr__(
                self,
                "acceleration_normalization",
                normalization,
            )

    @property
    def content_id(self) -> str:
        return _content_id(self.to_payload())

    def to_payload(self) -> dict[str, object]:
        return {
            "acceleration_normalization": (
                None
                if self.acceleration_normalization is None
                else self.acceleration_normalization.value
            ),
            "acceleration_polar3": _component_payload(
                self.acceleration_polar3
            ),
            "averaging_scale": self.averaging_scale,
            "basis": self.basis,
            "congruence_id": self.congruence_id,
            "epoch_window": self.epoch_window,
            "frame": self.frame,
            "omega_axial3": list(self.omega_axial3),
            "parity_contract": self.parity_contract,
            "perturbative_order": self.perturbative_order,
            "schema": "HTT_CONGRUENCE_KINEMATICS_V1",
            "sigma_stf5": list(self.sigma_stf5),
            "units_convention": self.units_convention.value,
            "velocity_normalization": self.velocity_normalization.value,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "CongruenceKinematics":
        if not isinstance(payload, Mapping):
            raise JointAnisotropyStateError(
                "CongruenceKinematics payload must be a mapping"
            )
        expected = {
            "acceleration_normalization",
            "acceleration_polar3",
            "averaging_scale",
            "basis",
            "congruence_id",
            "epoch_window",
            "frame",
            "omega_axial3",
            "parity_contract",
            "perturbative_order",
            "schema",
            "sigma_stf5",
            "units_convention",
            "velocity_normalization",
        }
        _exact_keys(payload, expected, name="CongruenceKinematics payload")
        if payload["schema"] != "HTT_CONGRUENCE_KINEMATICS_V1":
            raise JointAnisotropyStateError(
                "unknown CongruenceKinematics schema"
            )
        return cls(
            sigma_stf5=payload["sigma_stf5"],  # type: ignore[arg-type]
            omega_axial3=payload["omega_axial3"],  # type: ignore[arg-type]
            acceleration_polar3=_component_from_payload(
                payload["acceleration_polar3"],
                "acceleration_polar3",
                length=3,
            ),
            frame=payload["frame"],  # type: ignore[arg-type]
            congruence_id=payload["congruence_id"],  # type: ignore[arg-type]
            epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
            averaging_scale=payload["averaging_scale"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            units_convention=payload["units_convention"],  # type: ignore[arg-type]
            velocity_normalization=payload["velocity_normalization"],  # type: ignore[arg-type]
            perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
            acceleration_normalization=payload["acceleration_normalization"],  # type: ignore[arg-type]
            parity_contract=payload["parity_contract"],  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class VelocityFrameBundle:
    """Typed PR-256-compatible velocity relation between three frames."""

    beta_RO: VectorOrMissing
    beta_RM: VectorOrMissing
    beta_MO: VectorOrMissing
    coordinate_frame: str
    radiation_frame_id: str
    matter_frame_id: str
    observer_frame_id: str
    basis: str
    epoch_window: str
    averaging_scale: str
    units: str
    parity_contract: str
    perturbative_order: str
    first_order_beta_ceiling: float
    atol: float
    rtol: float
    status: VelocityClosureStatus
    closure_residual: VectorOrMissing
    closure_norm: ScalarOrMissing
    closure_tolerance: ScalarOrMissing
    truncation_remainder_bound: ScalarOrMissing
    source_decomposition_id: str | MissingComponent
    relation: str = FIRST_ORDER_VELOCITY_RELATION
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _VELOCITY_TOKEN:
            raise JointAnisotropyStateError(
                "VelocityFrameBundle must be created by "
                "build_velocity_frame_bundle or from_pr256_velocity_payload"
            )
        for name in (
            "coordinate_frame",
            "radiation_frame_id",
            "matter_frame_id",
            "observer_frame_id",
            "basis",
            "epoch_window",
            "averaging_scale",
            "units",
            "perturbative_order",
        ):
            _text(getattr(self, name), name)
        if len(
            {
                self.radiation_frame_id,
                self.matter_frame_id,
                self.observer_frame_id,
            }
        ) != 3:
            raise JointAnisotropyStateError(
                "radiation, matter, and observer frame identities must be distinct"
            )
        if self.units != "dimensionless_beta_c_equals_1":
            raise JointAnisotropyStateError(
                "velocity units must be dimensionless_beta_c_equals_1"
            )
        if self.parity_contract != VELOCITY_PARITY_CONTRACT:
            raise JointAnisotropyStateError(
                "velocity bundle must retain the registered parity contract"
            )
        if self.perturbative_order != "first_order_small_velocity":
            raise JointAnisotropyStateError(
                "velocity perturbative_order must be first_order_small_velocity"
            )
        if self.relation != FIRST_ORDER_VELOCITY_RELATION:
            raise JointAnisotropyStateError(
                "velocity bundle relation does not match PR-256"
            )
        if not isinstance(self.status, VelocityClosureStatus):
            raise JointAnisotropyStateError(
                "status must be a VelocityClosureStatus"
            )

    @property
    def content_id(self) -> str:
        return _content_id(self.to_payload())

    @property
    def missing_components(self) -> tuple[MissingComponent, ...]:
        return tuple(
            value
            for value in (self.beta_RO, self.beta_RM, self.beta_MO)
            if type(value) is MissingComponent
        )

    def to_payload(self) -> dict[str, object]:
        return {
            "atol": self.atol,
            "averaging_scale": self.averaging_scale,
            "basis": self.basis,
            "beta_MO": _component_payload(self.beta_MO),
            "beta_RM": _component_payload(self.beta_RM),
            "beta_RO": _component_payload(self.beta_RO),
            "closure_norm": _scalar_payload(self.closure_norm),
            "closure_residual": _component_payload(self.closure_residual),
            "closure_tolerance": _scalar_payload(self.closure_tolerance),
            "coordinate_frame": self.coordinate_frame,
            "epoch_window": self.epoch_window,
            "first_order_beta_ceiling": self.first_order_beta_ceiling,
            "matter_frame_id": self.matter_frame_id,
            "observer_frame_id": self.observer_frame_id,
            "parity_contract": self.parity_contract,
            "perturbative_order": self.perturbative_order,
            "radiation_frame_id": self.radiation_frame_id,
            "relation": self.relation,
            "rtol": self.rtol,
            "schema": "HTT_VELOCITY_FRAME_BUNDLE_V1",
            "source_decomposition_id": (
                {"missing": self.source_decomposition_id.to_payload()}
                if type(self.source_decomposition_id) is MissingComponent
                else self.source_decomposition_id
            ),
            "status": self.status.value,
            "truncation_remainder_bound": _scalar_payload(
                self.truncation_remainder_bound
            ),
            "units": self.units,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "VelocityFrameBundle":
        if not isinstance(payload, Mapping):
            raise JointAnisotropyStateError(
                "VelocityFrameBundle payload must be a mapping"
            )
        expected = {
            "atol",
            "averaging_scale",
            "basis",
            "beta_MO",
            "beta_RM",
            "beta_RO",
            "closure_norm",
            "closure_residual",
            "closure_tolerance",
            "coordinate_frame",
            "epoch_window",
            "first_order_beta_ceiling",
            "matter_frame_id",
            "observer_frame_id",
            "parity_contract",
            "perturbative_order",
            "radiation_frame_id",
            "relation",
            "rtol",
            "schema",
            "source_decomposition_id",
            "status",
            "truncation_remainder_bound",
            "units",
        }
        _exact_keys(payload, expected, name="VelocityFrameBundle payload")
        if payload["schema"] != "HTT_VELOCITY_FRAME_BUNDLE_V1":
            raise JointAnisotropyStateError(
                "unknown VelocityFrameBundle schema"
            )
        source_payload = payload["source_decomposition_id"]
        if isinstance(source_payload, Mapping):
            _exact_keys(
                source_payload,
                {"missing"},
                name="source_decomposition_id payload",
            )
            source: str | MissingComponent = MissingComponent.from_payload(
                source_payload["missing"]
            )
        else:
            source = _text(source_payload, "source_decomposition_id")
        built = build_velocity_frame_bundle(
            beta_RO=_component_from_payload(
                payload["beta_RO"], "beta_RO", length=3
            ),
            beta_RM=_component_from_payload(
                payload["beta_RM"], "beta_RM", length=3
            ),
            beta_MO=_component_from_payload(
                payload["beta_MO"], "beta_MO", length=3
            ),
            coordinate_frame=payload["coordinate_frame"],  # type: ignore[arg-type]
            radiation_frame_id=payload["radiation_frame_id"],  # type: ignore[arg-type]
            matter_frame_id=payload["matter_frame_id"],  # type: ignore[arg-type]
            observer_frame_id=payload["observer_frame_id"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
            averaging_scale=payload["averaging_scale"],  # type: ignore[arg-type]
            first_order_beta_ceiling=payload["first_order_beta_ceiling"],  # type: ignore[arg-type]
            units=payload["units"],  # type: ignore[arg-type]
            parity_contract=payload["parity_contract"],  # type: ignore[arg-type]
            perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
            atol=payload["atol"],  # type: ignore[arg-type]
            rtol=payload["rtol"],  # type: ignore[arg-type]
            source_decomposition_id=source,
        )
        if built.to_payload() != dict(payload):
            raise JointAnisotropyStateError(
                "serialized velocity derived fields failed replay"
            )
        return built


def build_velocity_frame_bundle(
    *,
    beta_RO: object,
    beta_RM: object,
    beta_MO: object,
    coordinate_frame: str,
    radiation_frame_id: str,
    matter_frame_id: str,
    observer_frame_id: str,
    basis: str,
    epoch_window: str,
    averaging_scale: str,
    first_order_beta_ceiling: float,
    units: str = "dimensionless_beta_c_equals_1",
    parity_contract: str = VELOCITY_PARITY_CONTRACT,
    perturbative_order: str = "first_order_small_velocity",
    atol: float = 1.0e-15,
    rtol: float = 1.0e-10,
    source_decomposition_id: str | MissingComponent | None = None,
) -> VelocityFrameBundle:
    """Build the PR-256 relation without deriving a missing velocity."""

    vectors = {
        "beta_RO": _component(beta_RO, "beta_RO", length=3),
        "beta_RM": _component(beta_RM, "beta_RM", length=3),
        "beta_MO": _component(beta_MO, "beta_MO", length=3),
    }
    ceiling = _positive(
        first_order_beta_ceiling,
        "first_order_beta_ceiling",
    )
    if ceiling > 0.1:
        raise JointAnisotropyStateError(
            "first_order_beta_ceiling must be at most 0.1"
        )
    absolute = _nonnegative(atol, "atol")
    relative = _nonnegative(rtol, "rtol")
    if absolute == 0.0 and relative == 0.0:
        raise JointAnisotropyStateError("atol and rtol must not both be zero")
    available = {
        name: value
        for name, value in vectors.items()
        if type(value) is not MissingComponent
    }
    norms = {name: _vector_norm(value) for name, value in available.items()}
    expansion_candidates: list[float] = []
    if "beta_RO" in available:
        expansion_candidates.append(norms["beta_RO"])
    if "beta_RM" in available and "beta_MO" in available:
        expansion_candidates.append(norms["beta_RM"] + norms["beta_MO"])
    else:
        for name in ("beta_RM", "beta_MO"):
            if name in available:
                expansion_candidates.append(norms[name])
    if max(expansion_candidates, default=0.0) > ceiling:
        raise JointAnisotropyStateError(
            "velocity components exceed first_order_beta_ceiling"
        )

    all_available = len(available) == 3
    if all_available:
        beta_ro = available["beta_RO"]
        beta_rm = available["beta_RM"]
        beta_mo = available["beta_MO"]
        residual = tuple(
            beta_ro[index] - beta_rm[index] - beta_mo[index]
            for index in range(3)
        )
        closure_norm: ScalarOrMissing = _vector_norm(residual)
        scale = max(
            norms["beta_RO"],
            _vector_norm(
                tuple(
                    beta_rm[index] + beta_mo[index] for index in range(3)
                )
            ),
        )
        remainder: ScalarOrMissing = (
            norms["beta_RM"] + norms["beta_MO"]
        ) ** 2
        tolerance: ScalarOrMissing = absolute + relative * scale + remainder
        status = (
            VelocityClosureStatus.CLOSURE_VERIFIED
            if closure_norm <= tolerance
            else VelocityClosureStatus.CLOSURE_MISMATCH
        )
        closure_residual: VectorOrMissing = residual
    else:
        status = (
            VelocityClosureStatus.SUM_ONLY
            if "beta_RO" in available
            else VelocityClosureStatus.MISSING_COMPONENT
        )
        closure_residual = missing_component(
            "closure_residual",
            "closure requires beta_RO, beta_RM, and beta_MO",
            required_for=("first-order velocity closure",),
        )
        closure_norm = missing_component(
            "closure_norm",
            "closure residual is unavailable",
            required_for=("first-order velocity closure",),
        )
        tolerance = missing_component(
            "closure_tolerance",
            "closure comparison is unavailable",
            required_for=("first-order velocity closure",),
        )
        remainder = missing_component(
            "truncation_remainder_bound",
            "both beta_RM and beta_MO are required",
            required_for=("first-order velocity closure",),
        )

    source: str | MissingComponent
    if source_decomposition_id is None:
        source = missing_component(
            "source_decomposition_id",
            "no upstream velocity-decomposition report was supplied",
        )
    elif type(source_decomposition_id) is MissingComponent:
        if source_decomposition_id.component != "source_decomposition_id":
            raise JointAnisotropyStateError(
                "source_decomposition_id absence record has the wrong component"
            )
        source = source_decomposition_id
    else:
        source = _text(source_decomposition_id, "source_decomposition_id")

    return VelocityFrameBundle(
        beta_RO=vectors["beta_RO"],
        beta_RM=vectors["beta_RM"],
        beta_MO=vectors["beta_MO"],
        coordinate_frame=_text(coordinate_frame, "coordinate_frame"),
        radiation_frame_id=_text(radiation_frame_id, "radiation_frame_id"),
        matter_frame_id=_text(matter_frame_id, "matter_frame_id"),
        observer_frame_id=_text(observer_frame_id, "observer_frame_id"),
        basis=_text(basis, "basis"),
        epoch_window=_text(epoch_window, "epoch_window"),
        averaging_scale=_text(averaging_scale, "averaging_scale"),
        units=_text(units, "units"),
        parity_contract=parity_contract,
        perturbative_order=_text(
            perturbative_order,
            "perturbative_order",
        ),
        first_order_beta_ceiling=ceiling,
        atol=absolute,
        rtol=relative,
        status=status,
        closure_residual=closure_residual,
        closure_norm=closure_norm,
        closure_tolerance=tolerance,
        truncation_remainder_bound=remainder,
        source_decomposition_id=source,
        _construction_token=_VELOCITY_TOKEN,
    )


def from_pr256_velocity_payload(
    payload: object,
    *,
    coordinate_frame: str,
    radiation_frame_id: str,
    matter_frame_id: str,
    observer_frame_id: str,
    averaging_scale: str,
) -> VelocityFrameBundle:
    """Adapt a PR-256 payload without importing HTT into COMMON."""

    if not isinstance(payload, Mapping):
        raise JointAnisotropyStateError(
            "PR-256 velocity payload must be a mapping"
        )
    required = {
        "allowed_use",
        "atol",
        "basis",
        "beta_MO",
        "beta_RM",
        "beta_RO",
        "closure_norm",
        "closure_residual",
        "closure_tolerance",
        "epoch_window",
        "first_order_beta_ceiling",
        "forbidden_use",
        "missing_components",
        "parity",
        "perturbative_order",
        "relation",
        "rtol",
        "status",
        "truncation_remainder_bound",
        "units",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise JointAnisotropyStateError(
            f"PR-256 velocity payload missing fields: {missing}"
        )
    if payload["relation"] != FIRST_ORDER_VELOCITY_RELATION:
        raise JointAnisotropyStateError("PR-256 relation mismatch")
    if tuple(payload["allowed_use"]) != PR256_ALLOWED_USE:  # type: ignore[arg-type]
        raise JointAnisotropyStateError(
            "PR-256 allowed-use claim boundary mismatch"
        )
    if tuple(payload["forbidden_use"]) != PR256_FORBIDDEN_USE:  # type: ignore[arg-type]
        raise JointAnisotropyStateError(
            "PR-256 forbidden-use claim boundary mismatch"
        )

    vectors: dict[str, VectorOrMissing] = {}
    for name in ("beta_RO", "beta_RM", "beta_MO"):
        value = payload[name]
        if value is None:
            vectors[name] = missing_component(
                name,
                "component missing in bound PR-256 decomposition",
                required_for=("joint velocity-frame state",),
            )
        else:
            vectors[name] = _vector(value, name, length=3)
    source_id = _content_id(dict(payload))
    built = build_velocity_frame_bundle(
        beta_RO=vectors["beta_RO"],
        beta_RM=vectors["beta_RM"],
        beta_MO=vectors["beta_MO"],
        coordinate_frame=coordinate_frame,
        radiation_frame_id=radiation_frame_id,
        matter_frame_id=matter_frame_id,
        observer_frame_id=observer_frame_id,
        basis=payload["basis"],  # type: ignore[arg-type]
        epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
        averaging_scale=averaging_scale,
        first_order_beta_ceiling=payload["first_order_beta_ceiling"],  # type: ignore[arg-type]
        units=payload["units"],  # type: ignore[arg-type]
        perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
        atol=payload["atol"],  # type: ignore[arg-type]
        rtol=payload["rtol"],  # type: ignore[arg-type]
        source_decomposition_id=source_id,
    )
    if payload["parity"] != "polar_vector":
        raise JointAnisotropyStateError(
            "PR-256 velocity parity must be polar_vector"
        )
    if payload["status"] != built.status.value:
        raise JointAnisotropyStateError(
            "PR-256 velocity status failed independent replay"
        )
    expected_missing = tuple(
        name
        for name in ("beta_RO", "beta_RM", "beta_MO")
        if type(vectors[name]) is MissingComponent
    )
    if tuple(payload["missing_components"]) != expected_missing:  # type: ignore[arg-type]
        raise JointAnisotropyStateError(
            "PR-256 missing-components declaration failed replay"
        )
    for name, expected in (
        ("closure_residual", built.closure_residual),
        ("closure_norm", built.closure_norm),
        ("closure_tolerance", built.closure_tolerance),
        ("truncation_remainder_bound", built.truncation_remainder_bound),
    ):
        actual = payload[name]
        if type(expected) is MissingComponent:
            if actual is not None:
                raise JointAnisotropyStateError(
                    f"PR-256 {name} must be absent for a partial bundle"
                )
        elif name == "closure_residual":
            if tuple(actual) != expected:  # type: ignore[arg-type]
                raise JointAnisotropyStateError(
                    "PR-256 closure_residual failed replay"
                )
        elif actual != expected:
            raise JointAnisotropyStateError(
                f"PR-256 {name} failed replay"
            )
    return built


def _default_spatial_curvature() -> MissingComponent:
    return missing_component(
        "spatial_curvature_stf5",
        "anisotropic spatial-curvature tensor is unavailable",
        status=MissingComponentStatus.NEEDS_NATIVE,
        required_for=("full geometry layer",),
    )


def _default_electric_weyl() -> MissingComponent:
    return missing_component(
        "electric_weyl_stf5",
        "electric Weyl tensor is unavailable",
        status=MissingComponentStatus.NEEDS_NATIVE,
        required_for=("full geometry layer",),
    )


def _default_magnetic_weyl() -> MissingComponent:
    return missing_component(
        "magnetic_weyl_stf5",
        "magnetic Weyl tensor is unavailable",
        status=MissingComponentStatus.NEEDS_NATIVE,
        required_for=("full geometry layer",),
    )


def _default_anisotropic_stress() -> MissingComponent:
    return missing_component(
        "anisotropic_stress_stf5",
        "anisotropic-stress tensor is unavailable",
        required_for=("full matter-geometry layer",),
    )


@dataclass(frozen=True)
class GeometryState:
    """Scalar curvature-budget coordinate plus optional geometry tensors."""

    delta_omega_k: float
    frame: str
    congruence_id: str
    epoch_window: str
    averaging_scale: str
    basis: str
    units_convention: UnitsConvention | str
    perturbative_order: str
    spatial_curvature_stf5: VectorOrMissing = field(
        default_factory=_default_spatial_curvature
    )
    electric_weyl_stf5: VectorOrMissing = field(
        default_factory=_default_electric_weyl
    )
    magnetic_weyl_stf5: VectorOrMissing = field(
        default_factory=_default_magnetic_weyl
    )
    anisotropic_stress_stf5: VectorOrMissing = field(
        default_factory=_default_anisotropic_stress
    )
    parity_contract: str = GEOMETRY_PARITY_CONTRACT

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "delta_omega_k",
            _real(self.delta_omega_k, "delta_omega_k"),
        )
        for name in (
            "frame",
            "congruence_id",
            "epoch_window",
            "averaging_scale",
            "basis",
            "perturbative_order",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self,
            "units_convention",
            _enum(
                self.units_convention,
                UnitsConvention,
                "units_convention",
            ),
        )
        for name in (
            "spatial_curvature_stf5",
            "electric_weyl_stf5",
            "magnetic_weyl_stf5",
            "anisotropic_stress_stf5",
        ):
            object.__setattr__(
                self,
                name,
                _component(getattr(self, name), name, length=5),
            )
        if self.parity_contract != GEOMETRY_PARITY_CONTRACT:
            raise JointAnisotropyStateError(
                "geometry must retain the registered parity contract"
            )

    @property
    def completeness(self) -> GeometryCompleteness:
        values = (
            self.spatial_curvature_stf5,
            self.electric_weyl_stf5,
            self.magnetic_weyl_stf5,
            self.anisotropic_stress_stf5,
        )
        return (
            GeometryCompleteness.COMPLETE_REGISTERED_COMPONENTS
            if all(type(value) is not MissingComponent for value in values)
            else GeometryCompleteness.PARTIAL
        )

    @property
    def content_id(self) -> str:
        return _content_id(self.to_payload())

    def to_payload(self) -> dict[str, object]:
        return {
            "anisotropic_stress_stf5": _component_payload(
                self.anisotropic_stress_stf5
            ),
            "averaging_scale": self.averaging_scale,
            "basis": self.basis,
            "completeness": self.completeness.value,
            "congruence_id": self.congruence_id,
            "delta_omega_k": self.delta_omega_k,
            "electric_weyl_stf5": _component_payload(
                self.electric_weyl_stf5
            ),
            "epoch_window": self.epoch_window,
            "frame": self.frame,
            "magnetic_weyl_stf5": _component_payload(
                self.magnetic_weyl_stf5
            ),
            "parity_contract": self.parity_contract,
            "perturbative_order": self.perturbative_order,
            "schema": "HTT_GEOMETRY_STATE_V1",
            "spatial_curvature_stf5": _component_payload(
                self.spatial_curvature_stf5
            ),
            "units_convention": self.units_convention.value,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "GeometryState":
        if not isinstance(payload, Mapping):
            raise JointAnisotropyStateError(
                "GeometryState payload must be a mapping"
            )
        expected = {
            "anisotropic_stress_stf5",
            "averaging_scale",
            "basis",
            "completeness",
            "congruence_id",
            "delta_omega_k",
            "electric_weyl_stf5",
            "epoch_window",
            "frame",
            "magnetic_weyl_stf5",
            "parity_contract",
            "perturbative_order",
            "schema",
            "spatial_curvature_stf5",
            "units_convention",
        }
        _exact_keys(payload, expected, name="GeometryState payload")
        if payload["schema"] != "HTT_GEOMETRY_STATE_V1":
            raise JointAnisotropyStateError("unknown GeometryState schema")
        state = cls(
            delta_omega_k=payload["delta_omega_k"],  # type: ignore[arg-type]
            frame=payload["frame"],  # type: ignore[arg-type]
            congruence_id=payload["congruence_id"],  # type: ignore[arg-type]
            epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
            averaging_scale=payload["averaging_scale"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            units_convention=payload["units_convention"],  # type: ignore[arg-type]
            perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
            spatial_curvature_stf5=_component_from_payload(
                payload["spatial_curvature_stf5"],
                "spatial_curvature_stf5",
                length=5,
            ),
            electric_weyl_stf5=_component_from_payload(
                payload["electric_weyl_stf5"],
                "electric_weyl_stf5",
                length=5,
            ),
            magnetic_weyl_stf5=_component_from_payload(
                payload["magnetic_weyl_stf5"],
                "magnetic_weyl_stf5",
                length=5,
            ),
            anisotropic_stress_stf5=_component_from_payload(
                payload["anisotropic_stress_stf5"],
                "anisotropic_stress_stf5",
                length=5,
            ),
            parity_contract=payload["parity_contract"],  # type: ignore[arg-type]
        )
        if state.completeness.value != payload["completeness"]:
            raise JointAnisotropyStateError(
                "serialized geometry completeness failed replay"
            )
        return state


def _transfer_spec_from_metadata(payload: object) -> TransferFunctionSpec:
    if not isinstance(payload, Mapping):
        raise JointAnisotropyStateError(
            "transfer_spec payload must be a mapping"
        )
    required = {
        "calibration_status",
        "caveats",
        "family",
        "normalization",
        "observable_kind",
        "passed_validation_gates",
        "source_ref",
        "transfer_id",
        "transfer_source",
        "valid_range",
        "version",
    }
    _exact_keys(payload, required, name="transfer_spec payload")
    valid = payload["valid_range"]
    if not isinstance(valid, Mapping):
        raise JointAnisotropyStateError("transfer valid_range must be a mapping")
    _exact_keys(
        valid,
        {"ell_max", "ell_min", "k_max", "k_min"},
        name="transfer valid_range",
    )
    return TransferFunctionSpec(
        transfer_id=payload["transfer_id"],  # type: ignore[arg-type]
        source=payload["transfer_source"],  # type: ignore[arg-type]
        family=payload["family"],  # type: ignore[arg-type]
        valid_range=TransferValidRange(
            k_min=valid["k_min"],  # type: ignore[arg-type]
            k_max=valid["k_max"],  # type: ignore[arg-type]
            ell_min=valid["ell_min"],  # type: ignore[arg-type]
            ell_max=valid["ell_max"],  # type: ignore[arg-type]
        ),
        observable_kind=payload["observable_kind"],  # type: ignore[arg-type]
        normalization=payload["normalization"],  # type: ignore[arg-type]
        calibration_status=payload["calibration_status"],  # type: ignore[arg-type]
        caveats=payload["caveats"],  # type: ignore[arg-type]
        source_ref=payload["source_ref"],  # type: ignore[arg-type]
        version=payload["version"],  # type: ignore[arg-type]
        passed_validation_gates=payload["passed_validation_gates"],  # type: ignore[arg-type]
    )


@dataclass(frozen=True)
class JointAnisotropyState:
    """Reference-bound composition of kinematics, velocity, and geometry."""

    congruence_kinematics: CongruenceKinematics
    velocity_frames: VelocityFrameBundle
    geometry_state: GeometryState
    frame: str
    congruence: str
    epoch_window: str
    averaging_scale: str
    basis: str
    units_convention: UnitsConvention | str
    perturbative_order: str
    beta_semantic_role: BetaSemanticRole | str
    transfer_source: TransferSource | str
    transfer_spec: TransferFunctionSpec | None
    source_kind: JointStateSourceKind | str
    source_identity: str

    claim_ceiling: ClassVar[str] = JOINT_STATE_CLAIM_CEILING
    allowed_use: ClassVar[tuple[str, ...]] = JOINT_STATE_ALLOWED_USE
    forbidden_use: ClassVar[tuple[str, ...]] = JOINT_STATE_FORBIDDEN_USE

    def __post_init__(self) -> None:
        if type(self.congruence_kinematics) is not CongruenceKinematics:
            raise JointAnisotropyStateError(
                "congruence_kinematics must be an exact CongruenceKinematics"
            )
        if type(self.velocity_frames) is not VelocityFrameBundle:
            raise JointAnisotropyStateError(
                "velocity_frames must be an exact VelocityFrameBundle"
            )
        if type(self.geometry_state) is not GeometryState:
            raise JointAnisotropyStateError(
                "geometry_state must be an exact GeometryState"
            )
        for name in (
            "frame",
            "congruence",
            "epoch_window",
            "averaging_scale",
            "basis",
            "perturbative_order",
            "source_identity",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        units = _enum(
            self.units_convention,
            UnitsConvention,
            "units_convention",
        )
        beta_role = _enum(
            self.beta_semantic_role,
            BetaSemanticRole,
            "beta_semantic_role",
        )
        source_kind = _enum(
            self.source_kind,
            JointStateSourceKind,
            "source_kind",
        )
        if beta_role is BetaSemanticRole.UNRESOLVED:
            raise JointAnisotropyStateError(
                "JointAnisotropyState cannot carry an unresolved beta role"
            )
        object.__setattr__(self, "units_convention", units)
        object.__setattr__(self, "beta_semantic_role", beta_role)
        object.__setattr__(self, "source_kind", source_kind)

        kinematics = self.congruence_kinematics
        velocity = self.velocity_frames
        geometry = self.geometry_state
        mismatches: list[str] = []
        comparisons = {
            "kinematics.frame": (kinematics.frame, self.frame),
            "velocity.coordinate_frame": (
                velocity.coordinate_frame,
                self.frame,
            ),
            "geometry.frame": (geometry.frame, self.frame),
            "kinematics.congruence_id": (
                kinematics.congruence_id,
                self.congruence,
            ),
            "geometry.congruence_id": (
                geometry.congruence_id,
                self.congruence,
            ),
            "kinematics.epoch_window": (
                kinematics.epoch_window,
                self.epoch_window,
            ),
            "velocity.epoch_window": (
                velocity.epoch_window,
                self.epoch_window,
            ),
            "geometry.epoch_window": (
                geometry.epoch_window,
                self.epoch_window,
            ),
            "kinematics.averaging_scale": (
                kinematics.averaging_scale,
                self.averaging_scale,
            ),
            "velocity.averaging_scale": (
                velocity.averaging_scale,
                self.averaging_scale,
            ),
            "geometry.averaging_scale": (
                geometry.averaging_scale,
                self.averaging_scale,
            ),
            "kinematics.basis": (kinematics.basis, self.basis),
            "velocity.basis": (velocity.basis, self.basis),
            "geometry.basis": (geometry.basis, self.basis),
            "kinematics.units_convention": (
                kinematics.units_convention,
                units,
            ),
            "geometry.units_convention": (
                geometry.units_convention,
                units,
            ),
            "kinematics.perturbative_order": (
                kinematics.perturbative_order,
                self.perturbative_order,
            ),
            "geometry.perturbative_order": (
                geometry.perturbative_order,
                self.perturbative_order,
            ),
        }
        for name, (component_value, joint_value) in comparisons.items():
            if component_value != joint_value:
                mismatches.append(name)
        if mismatches:
            raise JointAnisotropyStateError(
                "joint state metadata mismatch: " + ", ".join(mismatches)
            )

        try:
            transfer_source = (
                self.transfer_source
                if isinstance(self.transfer_source, TransferSource)
                else TransferSource(str(self.transfer_source))
            )
        except ValueError as exc:
            raise JointAnisotropyStateError(
                "transfer_source must use the registered TransferSource vocabulary"
            ) from exc
        if transfer_source is TransferSource.NONE:
            if self.transfer_spec is not None:
                raise JointAnisotropyStateError(
                    "transfer_source=none must not carry TransferFunctionSpec"
                )
        else:
            if type(self.transfer_spec) is not TransferFunctionSpec:
                raise JointAnisotropyStateError(
                    "non-none transfer source requires an exact TransferFunctionSpec"
                )
            if self.transfer_spec.source is not transfer_source:
                raise JointAnisotropyStateError(
                    "transfer source must match TransferFunctionSpec"
                )
        object.__setattr__(self, "transfer_source", transfer_source)

    @property
    def kinematics_ref(self) -> str:
        return self.congruence_kinematics.content_id

    @property
    def velocity_ref(self) -> str:
        return self.velocity_frames.content_id

    @property
    def geometry_ref(self) -> str:
        return self.geometry_state.content_id

    @property
    def content_id(self) -> str:
        return _content_id(self.to_payload())

    def to_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "averaging_scale": self.averaging_scale,
            "basis": self.basis,
            "beta_semantic_role": self.beta_semantic_role.value,
            "claim_ceiling": self.claim_ceiling,
            "congruence": self.congruence,
            "congruence_kinematics": (
                self.congruence_kinematics.to_payload()
            ),
            "epoch_window": self.epoch_window,
            "forbidden_use": list(self.forbidden_use),
            "frame": self.frame,
            "geometry_ref": self.geometry_ref,
            "geometry_state": self.geometry_state.to_payload(),
            "kinematics_ref": self.kinematics_ref,
            "perturbative_order": self.perturbative_order,
            "schema": "HTT_JOINT_ANISOTROPY_STATE_V1",
            "source_identity": self.source_identity,
            "source_kind": self.source_kind.value,
            "transfer_source": self.transfer_source.value,
            "transfer_spec": (
                None
                if self.transfer_spec is None
                else self.transfer_spec.to_metadata()
            ),
            "units_convention": self.units_convention.value,
            "velocity_frames": self.velocity_frames.to_payload(),
            "velocity_ref": self.velocity_ref,
        }

    @classmethod
    def from_payload(cls, payload: object) -> "JointAnisotropyState":
        if not isinstance(payload, Mapping):
            raise JointAnisotropyStateError(
                "JointAnisotropyState payload must be a mapping"
            )
        expected = {
            "allowed_use",
            "averaging_scale",
            "basis",
            "beta_semantic_role",
            "claim_ceiling",
            "congruence",
            "congruence_kinematics",
            "epoch_window",
            "forbidden_use",
            "frame",
            "geometry_ref",
            "geometry_state",
            "kinematics_ref",
            "perturbative_order",
            "schema",
            "source_identity",
            "source_kind",
            "transfer_source",
            "transfer_spec",
            "units_convention",
            "velocity_frames",
            "velocity_ref",
        }
        _exact_keys(payload, expected, name="JointAnisotropyState payload")
        if payload["schema"] != "HTT_JOINT_ANISOTROPY_STATE_V1":
            raise JointAnisotropyStateError(
                "unknown JointAnisotropyState schema"
            )
        if payload["claim_ceiling"] != JOINT_STATE_CLAIM_CEILING:
            raise JointAnisotropyStateError("joint-state claim ceiling drifted")
        if tuple(payload["allowed_use"]) != JOINT_STATE_ALLOWED_USE:  # type: ignore[arg-type]
            raise JointAnisotropyStateError("joint-state allowed-use drifted")
        if tuple(payload["forbidden_use"]) != JOINT_STATE_FORBIDDEN_USE:  # type: ignore[arg-type]
            raise JointAnisotropyStateError("joint-state forbidden-use drifted")
        transfer_payload = payload["transfer_spec"]
        transfer_spec = (
            None
            if transfer_payload is None
            else _transfer_spec_from_metadata(transfer_payload)
        )
        state = cls(
            congruence_kinematics=CongruenceKinematics.from_payload(
                payload["congruence_kinematics"]
            ),
            velocity_frames=VelocityFrameBundle.from_payload(
                payload["velocity_frames"]
            ),
            geometry_state=GeometryState.from_payload(
                payload["geometry_state"]
            ),
            frame=payload["frame"],  # type: ignore[arg-type]
            congruence=payload["congruence"],  # type: ignore[arg-type]
            epoch_window=payload["epoch_window"],  # type: ignore[arg-type]
            averaging_scale=payload["averaging_scale"],  # type: ignore[arg-type]
            basis=payload["basis"],  # type: ignore[arg-type]
            units_convention=payload["units_convention"],  # type: ignore[arg-type]
            perturbative_order=payload["perturbative_order"],  # type: ignore[arg-type]
            beta_semantic_role=payload["beta_semantic_role"],  # type: ignore[arg-type]
            transfer_source=payload["transfer_source"],  # type: ignore[arg-type]
            transfer_spec=transfer_spec,
            source_kind=payload["source_kind"],  # type: ignore[arg-type]
            source_identity=payload["source_identity"],  # type: ignore[arg-type]
        )
        refs = {
            "kinematics_ref": state.kinematics_ref,
            "velocity_ref": state.velocity_ref,
            "geometry_ref": state.geometry_ref,
        }
        for name, expected_ref in refs.items():
            if payload[name] != expected_ref:
                raise JointAnisotropyStateError(
                    f"serialized {name} does not bind component content"
                )
        return state


@dataclass(frozen=True)
class LegacyDepartureBinding:
    """Explicit semantic/convention binding for one legacy state."""

    beta_semantic_role: BetaSemanticRole | str
    source_state_id: str
    semantic_authority_id: str
    assumptions: tuple[str, ...]
    source_basis: str
    source_units: str
    source_parity: str
    sigma_normalization: str
    omega_normalization: str
    beta_normalization: VelocityNormalization | str
    units_convention: UnitsConvention | str
    radiation_frame_id: str
    matter_frame_id: str
    observer_frame_id: str
    first_order_beta_ceiling: float

    def __post_init__(self) -> None:
        role = _enum(
            self.beta_semantic_role,
            BetaSemanticRole,
            "beta_semantic_role",
        )
        if role not in {
            BetaSemanticRole.BETA_RO,
            BetaSemanticRole.BETA_RM,
            BetaSemanticRole.BETA_MO,
        }:
            raise JointAnisotropyStateError(
                "legacy beta binding requires BETA_RO, BETA_RM, or BETA_MO"
            )
        object.__setattr__(self, "beta_semantic_role", role)
        object.__setattr__(
            self,
            "source_state_id",
            _receipt(self.source_state_id, "source_state_id"),
        )
        object.__setattr__(
            self,
            "semantic_authority_id",
            _receipt(self.semantic_authority_id, "semantic_authority_id"),
        )
        object.__setattr__(
            self,
            "assumptions",
            _texts(self.assumptions, "assumptions", empty_ok=False),
        )
        for name in (
            "source_basis",
            "source_units",
            "source_parity",
            "radiation_frame_id",
            "matter_frame_id",
            "observer_frame_id",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.sigma_normalization != "SIGMA_OVER_THETA_STF5":
            raise JointAnisotropyStateError(
                "legacy sigma normalization must be explicitly bound"
            )
        if self.omega_normalization != "OMEGA_OVER_THETA_AXIAL3":
            raise JointAnisotropyStateError(
                "legacy omega normalization must be explicitly bound"
            )
        object.__setattr__(
            self,
            "beta_normalization",
            _enum(
                self.beta_normalization,
                VelocityNormalization,
                "beta_normalization",
            ),
        )
        object.__setattr__(
            self,
            "units_convention",
            _enum(
                self.units_convention,
                UnitsConvention,
                "units_convention",
            ),
        )
        object.__setattr__(
            self,
            "first_order_beta_ceiling",
            _positive(
                self.first_order_beta_ceiling,
                "first_order_beta_ceiling",
            ),
        )
        if self.first_order_beta_ceiling > 0.1:
            raise JointAnisotropyStateError(
                "first_order_beta_ceiling must be at most 0.1"
            )
        if len(
            {
                self.radiation_frame_id,
                self.matter_frame_id,
                self.observer_frame_id,
            }
        ) != 3:
            raise JointAnisotropyStateError(
                "legacy physical frame identities must be distinct"
            )

    @property
    def content_id(self) -> str:
        return _content_id(
            {
                "beta_normalization": self.beta_normalization.value,
                "beta_semantic_role": self.beta_semantic_role.value,
                "first_order_beta_ceiling": self.first_order_beta_ceiling,
                "matter_frame_id": self.matter_frame_id,
                "observer_frame_id": self.observer_frame_id,
                "omega_normalization": self.omega_normalization,
                "radiation_frame_id": self.radiation_frame_id,
                "schema": "HTT_LEGACY_DEPARTURE_BINDING_V1",
                "semantic_authority_id": self.semantic_authority_id,
                "sigma_normalization": self.sigma_normalization,
                "source_state_id": self.source_state_id,
                "source_basis": self.source_basis,
                "source_parity": self.source_parity,
                "source_units": self.source_units,
                "assumptions": list(self.assumptions),
                "units_convention": self.units_convention.value,
            }
        )


@dataclass(frozen=True)
class LegacyDepartureAdapterReport:
    """Fail-closed result of attempting one legacy-state migration."""

    status: LegacyAdapterStatus
    source_state_id: str
    binding_id: str | MissingComponent
    joint_state: JointAnisotropyState | None
    disposition: MissingComponent | None
    preserved_legacy_vector: tuple[float, ...]
    _construction_token: InitVar[object] = None

    allowed_use: ClassVar[tuple[str, ...]] = (
        "legacy value-preservation regression",
        "explicitly bound migration to JointAnisotropyState",
    )
    forbidden_use: ClassVar[tuple[str, ...]] = (
        "implicit beta-role assignment",
        "implicit sector-normalization conversion",
        "legacy state as primary new inference state",
    )

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LEGACY_ADAPTER_TOKEN:
            raise JointAnisotropyStateError(
                "LegacyDepartureAdapterReport must be created by "
                "adapt_legacy_departure_state"
            )
        if not isinstance(self.status, LegacyAdapterStatus):
            raise JointAnisotropyStateError(
                "legacy adapter status must be LegacyAdapterStatus"
            )
        object.__setattr__(
            self,
            "source_state_id",
            _receipt(self.source_state_id, "source_state_id"),
        )
        if type(self.binding_id) is MissingComponent:
            if self.binding_id.component != "legacy_adapter_binding":
                raise JointAnisotropyStateError(
                    "missing binding_id must name legacy_adapter_binding"
                )
        else:
            object.__setattr__(
                self,
                "binding_id",
                _receipt(self.binding_id, "binding_id"),
            )
        object.__setattr__(
            self,
            "preserved_legacy_vector",
            _vector(
                self.preserved_legacy_vector,
                "preserved_legacy_vector",
                length=12,
            ),
        )
        if self.status is LegacyAdapterStatus.ADAPTED:
            if type(self.joint_state) is not JointAnisotropyState:
                raise JointAnisotropyStateError(
                    "ADAPTED report requires a JointAnisotropyState"
                )
            if self.disposition is not None:
                raise JointAnisotropyStateError(
                    "ADAPTED report must not carry an abstention disposition"
                )
            if type(self.binding_id) is MissingComponent:
                raise JointAnisotropyStateError(
                    "ADAPTED report requires an exact binding identity"
                )
        else:
            if self.joint_state is not None:
                raise JointAnisotropyStateError(
                    "ABSTAIN report must not carry a joint state"
                )
            if type(self.disposition) is not MissingComponent:
                raise JointAnisotropyStateError(
                    "ABSTAIN report requires a typed disposition"
                )

    @property
    def content_id(self) -> str:
        return _content_id(self.to_payload())

    def to_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "binding_id": (
                {"missing": self.binding_id.to_payload()}
                if type(self.binding_id) is MissingComponent
                else self.binding_id
            ),
            "disposition": (
                None
                if self.disposition is None
                else self.disposition.to_payload()
            ),
            "forbidden_use": list(self.forbidden_use),
            "joint_state": (
                None if self.joint_state is None else self.joint_state.to_payload()
            ),
            "preserved_legacy_vector": list(self.preserved_legacy_vector),
            "schema": "HTT_LEGACY_DEPARTURE_ADAPTER_REPORT_V1",
            "source_state_id": self.source_state_id,
            "status": self.status.value,
        }


def _departure_payload(state: DepartureState) -> dict[str, object]:
    return {
        "averaging_scale": state.averaging_scale,
        "basis": state.basis,
        "beta_a": list(state.beta_a),
        "congruence": state.congruence,
        "delta_omega_k": state.delta_omega_k,
        "epoch_window": state.epoch_window,
        "frame": state.frame,
        "omega_a": list(state.omega_a),
        "parity": state.parity,
        "perturbative_order": state.perturbative_order,
        "schema": "LEGACY_DEPARTURE_STATE_PR249",
        "sigma_ab": list(state.sigma_ab),
        "units": state.units,
    }


def departure_state_content_id(state: DepartureState) -> str:
    """Return the exact content identity consumed by the legacy adapter."""

    if type(state) is not DepartureState:
        raise TypeError("state must be an exact DepartureState")
    return _content_id(_departure_payload(state))


def adapt_legacy_departure_state(
    state: DepartureState,
    binding: LegacyDepartureBinding | None,
) -> LegacyDepartureAdapterReport:
    """Adapt only when beta semantics and normalizations are explicit."""

    if type(state) is not DepartureState:
        raise TypeError("state must be an exact DepartureState")
    source_id = departure_state_content_id(state)
    preserved = state.vector
    if binding is None:
        disposition = missing_component(
            "legacy_adapter_binding",
            "beta semantic role and normalization binding are absent",
            status=MissingComponentStatus.ABSTAIN,
            required_for=("legacy DepartureState migration",),
        )
        return LegacyDepartureAdapterReport(
            status=LegacyAdapterStatus.ABSTAIN,
            source_state_id=source_id,
            binding_id=disposition,
            joint_state=None,
            disposition=disposition,
            preserved_legacy_vector=preserved,
            _construction_token=_LEGACY_ADAPTER_TOKEN,
        )
    if type(binding) is not LegacyDepartureBinding:
        raise TypeError("binding must be an exact LegacyDepartureBinding")
    mismatches = [
        name
        for name, expected, actual in (
            ("basis", binding.source_basis, state.basis),
            ("units", binding.source_units, state.units),
            ("parity", binding.source_parity, state.parity),
        )
        if expected != actual
    ]
    if binding.source_state_id != source_id:
        mismatches.append("source_state_id")
    if mismatches:
        disposition = missing_component(
            "legacy_adapter_binding",
            "source metadata do not match explicit binding: "
            + ", ".join(mismatches),
            status=MissingComponentStatus.ABSTAIN,
            required_for=("legacy DepartureState migration",),
        )
        return LegacyDepartureAdapterReport(
            status=LegacyAdapterStatus.ABSTAIN,
            source_state_id=source_id,
            binding_id=binding.content_id,
            joint_state=None,
            disposition=disposition,
            preserved_legacy_vector=preserved,
            _construction_token=_LEGACY_ADAPTER_TOKEN,
        )

    acceleration = missing_component(
        "acceleration_polar3",
        "legacy DepartureState has no acceleration component",
        required_for=("acceleration-sensitive functional",),
    )
    kinematics = CongruenceKinematics(
        sigma_stf5=state.sigma_ab,
        omega_axial3=state.omega_a,
        acceleration_polar3=acceleration,
        frame=state.frame,
        congruence_id=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units_convention=binding.units_convention,
        velocity_normalization=binding.beta_normalization,
        perturbative_order=state.perturbative_order,
        acceleration_normalization=None,
    )
    velocity_values: dict[str, VectorOrMissing] = {
        name: missing_component(
            name,
            "legacy DepartureState supplies a different or unresolved velocity role",
            required_for=("complete velocity-frame closure",),
        )
        for name in ("beta_RO", "beta_RM", "beta_MO")
    }
    role_to_name = {
        BetaSemanticRole.BETA_RO: "beta_RO",
        BetaSemanticRole.BETA_RM: "beta_RM",
        BetaSemanticRole.BETA_MO: "beta_MO",
    }
    velocity_values[role_to_name[binding.beta_semantic_role]] = state.beta_a
    velocity = build_velocity_frame_bundle(
        beta_RO=velocity_values["beta_RO"],
        beta_RM=velocity_values["beta_RM"],
        beta_MO=velocity_values["beta_MO"],
        coordinate_frame=state.frame,
        radiation_frame_id=binding.radiation_frame_id,
        matter_frame_id=binding.matter_frame_id,
        observer_frame_id=binding.observer_frame_id,
        basis=state.basis,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        first_order_beta_ceiling=binding.first_order_beta_ceiling,
        source_decomposition_id=missing_component(
            "source_decomposition_id",
            "legacy state predates PR-256 velocity decomposition",
        ),
    )
    geometry = GeometryState(
        delta_omega_k=state.delta_omega_k,
        frame=state.frame,
        congruence_id=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units_convention=binding.units_convention,
        perturbative_order=state.perturbative_order,
    )
    joint = JointAnisotropyState(
        congruence_kinematics=kinematics,
        velocity_frames=velocity,
        geometry_state=geometry,
        frame=state.frame,
        congruence=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units_convention=binding.units_convention,
        perturbative_order=state.perturbative_order,
        beta_semantic_role=binding.beta_semantic_role,
        transfer_source=TransferSource.NONE,
        transfer_spec=None,
        source_kind=JointStateSourceKind.LEGACY_DEPARTURE_ADAPTER,
        source_identity=source_id,
    )
    if state.vector != preserved:
        raise JointAnisotropyStateError("legacy state changed during adaptation")
    return LegacyDepartureAdapterReport(
        status=LegacyAdapterStatus.ADAPTED,
        source_state_id=source_id,
        binding_id=binding.content_id,
        joint_state=joint,
        disposition=None,
        preserved_legacy_vector=preserved,
        _construction_token=_LEGACY_ADAPTER_TOKEN,
    )


def _transform_vector(
    value: VectorOrMissing,
    transform: O3Transform,
    *,
    axial: bool,
) -> VectorOrMissing:
    if type(value) is MissingComponent:
        return value
    matrix = np.asarray(transform.matrix, dtype=float)
    transformed = matrix @ np.asarray(value, dtype=float)
    if axial:
        transformed = transform.determinant * transformed
    return tuple(float(component) for component in transformed)


def _transform_stf(
    value: VectorOrMissing,
    transform: O3Transform,
    *,
    axial: bool,
) -> VectorOrMissing:
    if type(value) is MissingComponent:
        return value
    matrix = np.asarray(transform.matrix, dtype=float)
    transformed = matrix @ stf5_to_matrix(value) @ matrix.T
    if axial:
        transformed = transform.determinant * transformed
    return matrix_to_stf5(transformed)


def apply_o3_action(
    state: JointAnisotropyState,
    transform: O3Transform,
) -> JointAnisotropyState:
    """Apply the registered active O(3) action with explicit parity."""

    if type(state) is not JointAnisotropyState:
        raise TypeError("state must be an exact JointAnisotropyState")
    if type(transform) is not O3Transform:
        raise TypeError("transform must be an exact O3Transform")
    if state.frame != transform.coordinate_frame:
        raise JointAnisotropyStateError(
            "joint state and O(3) transform coordinate frames must match"
        )
    if state.basis != STF5_CARTESIAN_BASIS:
        raise JointAnisotropyStateError(
            "O(3) action requires the registered STF5 Cartesian basis"
        )
    kinematics = state.congruence_kinematics
    transformed_kinematics = CongruenceKinematics(
        sigma_stf5=_transform_stf(
            kinematics.sigma_stf5,
            transform,
            axial=False,
        ),
        omega_axial3=_transform_vector(
            kinematics.omega_axial3,
            transform,
            axial=True,
        ),
        acceleration_polar3=_transform_vector(
            kinematics.acceleration_polar3,
            transform,
            axial=False,
        ),
        frame=kinematics.frame,
        congruence_id=kinematics.congruence_id,
        epoch_window=kinematics.epoch_window,
        averaging_scale=kinematics.averaging_scale,
        basis=kinematics.basis,
        units_convention=kinematics.units_convention,
        velocity_normalization=kinematics.velocity_normalization,
        perturbative_order=kinematics.perturbative_order,
        acceleration_normalization=kinematics.acceleration_normalization,
    )
    velocity = state.velocity_frames
    transformed_velocity = build_velocity_frame_bundle(
        beta_RO=_transform_vector(velocity.beta_RO, transform, axial=False),
        beta_RM=_transform_vector(velocity.beta_RM, transform, axial=False),
        beta_MO=_transform_vector(velocity.beta_MO, transform, axial=False),
        coordinate_frame=velocity.coordinate_frame,
        radiation_frame_id=velocity.radiation_frame_id,
        matter_frame_id=velocity.matter_frame_id,
        observer_frame_id=velocity.observer_frame_id,
        basis=velocity.basis,
        epoch_window=velocity.epoch_window,
        averaging_scale=velocity.averaging_scale,
        first_order_beta_ceiling=velocity.first_order_beta_ceiling,
        units=velocity.units,
        parity_contract=velocity.parity_contract,
        perturbative_order=velocity.perturbative_order,
        atol=velocity.atol,
        rtol=velocity.rtol,
        source_decomposition_id=velocity.source_decomposition_id,
    )
    geometry = state.geometry_state
    transformed_geometry = GeometryState(
        delta_omega_k=geometry.delta_omega_k,
        frame=geometry.frame,
        congruence_id=geometry.congruence_id,
        epoch_window=geometry.epoch_window,
        averaging_scale=geometry.averaging_scale,
        basis=geometry.basis,
        units_convention=geometry.units_convention,
        perturbative_order=geometry.perturbative_order,
        spatial_curvature_stf5=_transform_stf(
            geometry.spatial_curvature_stf5,
            transform,
            axial=False,
        ),
        electric_weyl_stf5=_transform_stf(
            geometry.electric_weyl_stf5,
            transform,
            axial=False,
        ),
        magnetic_weyl_stf5=_transform_stf(
            geometry.magnetic_weyl_stf5,
            transform,
            axial=True,
        ),
        anisotropic_stress_stf5=_transform_stf(
            geometry.anisotropic_stress_stf5,
            transform,
            axial=False,
        ),
    )
    return JointAnisotropyState(
        congruence_kinematics=transformed_kinematics,
        velocity_frames=transformed_velocity,
        geometry_state=transformed_geometry,
        frame=state.frame,
        congruence=state.congruence,
        epoch_window=state.epoch_window,
        averaging_scale=state.averaging_scale,
        basis=state.basis,
        units_convention=state.units_convention,
        perturbative_order=state.perturbative_order,
        beta_semantic_role=state.beta_semantic_role,
        transfer_source=state.transfer_source,
        transfer_spec=state.transfer_spec,
        source_kind=JointStateSourceKind.O3_ACTION,
        source_identity=_content_id(
            {
                "parent_state_id": state.content_id,
                "schema": "HTT_JOINT_STATE_O3_ACTION_V1",
                "transform_id": transform.transform_id,
            }
        ),
    )


def convert_acceleration_units(
    kinematics: CongruenceKinematics,
    target: UnitsConvention | str,
    *,
    c_numeric_in_source_velocity_units: float,
) -> CongruenceKinematics:
    """Convert only the explicitly typed acceleration normalization.

    ``c_numeric_in_source_velocity_units`` is mandatory.  The function does
    not assume a hidden natural-unit convention and does not alter shear or
    vorticity normalization.
    """

    if type(kinematics) is not CongruenceKinematics:
        raise TypeError("kinematics must be an exact CongruenceKinematics")
    target_units = _enum(target, UnitsConvention, "target")
    c_numeric = _positive(
        c_numeric_in_source_velocity_units,
        "c_numeric_in_source_velocity_units",
    )
    if target_units is kinematics.units_convention:
        return kinematics
    acceleration = kinematics.acceleration_polar3
    if type(acceleration) is MissingComponent:
        converted: VectorOrMissing = acceleration
        normalization: AccelerationNormalization | None = None
    elif (
        kinematics.units_convention
        is UnitsConvention.EXPLICIT_C_THETA_NORMALIZED
        and target_units is UnitsConvention.C_EQUALS_ONE_THETA_NORMALIZED
    ):
        converted = tuple(component * c_numeric for component in acceleration)
        normalization = AccelerationNormalization.A_OVER_THETA_C_EQUALS_ONE
    else:
        converted = tuple(component / c_numeric for component in acceleration)
        normalization = AccelerationNormalization.A_OVER_C_THETA
    return CongruenceKinematics(
        sigma_stf5=kinematics.sigma_stf5,
        omega_axial3=kinematics.omega_axial3,
        acceleration_polar3=converted,
        frame=kinematics.frame,
        congruence_id=kinematics.congruence_id,
        epoch_window=kinematics.epoch_window,
        averaging_scale=kinematics.averaging_scale,
        basis=kinematics.basis,
        units_convention=target_units,
        velocity_normalization=kinematics.velocity_normalization,
        perturbative_order=kinematics.perturbative_order,
        acceleration_normalization=normalization,
    )


__all__ = [
    "AccelerationNormalization",
    "BetaSemanticRole",
    "CongruenceKinematics",
    "FIRST_ORDER_VELOCITY_RELATION",
    "GEOMETRY_PARITY_CONTRACT",
    "GeometryCompleteness",
    "GeometryState",
    "JOINT_STATE_CLAIM_CEILING",
    "JointAnisotropyState",
    "JointAnisotropyStateError",
    "JointStateSourceKind",
    "KINEMATICS_PARITY_CONTRACT",
    "LegacyAdapterStatus",
    "LegacyDepartureAdapterReport",
    "LegacyDepartureBinding",
    "MissingComponent",
    "MissingComponentStatus",
    "PR256_ALLOWED_USE",
    "PR256_FORBIDDEN_USE",
    "UnitsConvention",
    "VELOCITY_PARITY_CONTRACT",
    "VelocityClosureStatus",
    "VelocityFrameBundle",
    "VelocityNormalization",
    "adapt_legacy_departure_state",
    "apply_o3_action",
    "build_velocity_frame_bundle",
    "convert_acceleration_units",
    "departure_state_content_id",
    "from_pr256_velocity_payload",
    "missing_component",
]

"""Parity-typed stratified orbit diagnostics for the canonical joint state.

The v3 catalogue extends, but does not replace, the frozen PR-257 v2
catalogue.  It evaluates a Gram--Krylov generator family, separates O(3)
scalars from pseudoscalars, records shear strata and residual stabilizers,
and reports the conditioning and overlap of numerical cyclic-chart
candidates.

All chart and stabilizer conclusions are local diagnostics.  Generic orbit
separation, degree completeness, and global chart completeness remain
``UNPROVEN``.  No object in this module is a native morphology atlas, source
classifier, geometry verdict, likelihood, posterior, evidence term, or
family identifier.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import itertools
import json
import math
from numbers import Integral, Real
from typing import Mapping, Sequence

import numpy as np

from common.joint_anisotropy_state import (
    JointAnisotropyState,
    JointAnisotropyStateError,
    MissingComponent,
    apply_o3_action,
    require_exact_joint_anisotropy_state,
)
from common.orbit_catalogue_v2 import (
    OrbitCatalogueV2Report,
    OrbitCatalogueV2Spec,
    orbit_catalogue_v2,
)
from common.orbit_nonlinearity import (
    DEPARTURE_O3_PARITY,
    DEPARTURE_O3_UNITS,
    O3Transform,
    STF5_CARTESIAN_BASIS,
    VectorParity,
    stf5_to_matrix,
)
from common.statistical_foundations import DepartureState


class OrbitCatalogueV3Error(ValueError):
    """Raised when a v3 orbit contract is malformed or overclaims."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class OrbitActionGroup(_StringEnum):
    O3 = "O3"
    SO3 = "SO3"


class OrbitScalarParity(_StringEnum):
    O3_SCALAR = "O3_SCALAR"
    O3_PSEUDOSCALAR = "O3_PSEUDOSCALAR"


class InvariantAvailability(_StringEnum):
    AVAILABLE = "AVAILABLE"
    MISSING_COMPONENT = "MISSING_COMPONENT"
    FORBIDDEN_DOMAIN = "FORBIDDEN_DOMAIN"


class InvariantAlgebraicForm(_StringEnum):
    POLYNOMIAL = "POLYNOMIAL"
    NORMALIZED_RATIONAL = "NORMALIZED_RATIONAL"


class ShearOrbitStratum(_StringEnum):
    ZERO_SHEAR = "ZERO_SHEAR"
    REPEATED_EIGENVALUE = "REPEATED_EIGENVALUE"
    SIMPLE_SPECTRUM = "SIMPLE_SPECTRUM"
    NUMERICALLY_UNRESOLVED = "NUMERICALLY_UNRESOLVED"


class ShearStabilizer(_StringEnum):
    SO3_FULL = "SO3_FULL"
    O3_FULL = "O3_FULL"
    SO3_AXISYMMETRIC_O2 = "SO3_AXISYMMETRIC_O2"
    O3_AXISYMMETRIC_O2_X_Z2 = "O3_AXISYMMETRIC_O2_X_Z2"
    SO3_SIMPLE_KLEIN_FOUR = "SO3_SIMPLE_KLEIN_FOUR"
    O3_SIMPLE_SIGN_EIGHT = "O3_SIMPLE_SIGN_EIGHT"
    NUMERICALLY_UNRESOLVED = "NUMERICALLY_UNRESOLVED"


class JointStabilizerStatus(_StringEnum):
    NUMERICALLY_TRIVIAL_CANDIDATE = "NUMERICALLY_TRIVIAL_CANDIDATE"
    RESIDUAL_STABILIZER_UNRESOLVED = "RESIDUAL_STABILIZER_UNRESOLVED"


class CyclicChartStatus(_StringEnum):
    NUMERICALLY_CYCLIC_CANDIDATE = "NUMERICALLY_CYCLIC_CANDIDATE"
    WEAKLY_CONDITIONED = "WEAKLY_CONDITIONED"
    NONCYCLIC = "NONCYCLIC"
    MISSING_COMPONENT = "MISSING_COMPONENT"


class ChartCoordinateStatus(_StringEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"


class ChartOverlapStatus(_StringEnum):
    DEFINED_LOCAL_OVERLAP = "DEFINED_LOCAL_OVERLAP"
    SINGULAR_OR_MISSING = "SINGULAR_OR_MISSING"


class CatalogueProofStatus(_StringEnum):
    UNPROVEN = "UNPROVEN"


class OrbitVectorChannel(_StringEnum):
    OMEGA = "omega_axial3"
    ACCELERATION = "acceleration_polar3"
    BETA_RM = "beta_RM"
    BETA_MO = "beta_MO"


class LegacyBetaChannel(_StringEnum):
    BETA_RO = "beta_RO"
    BETA_RM = "beta_RM"
    BETA_MO = "beta_MO"


class LegacyV2AdapterStatus(_StringEnum):
    ADAPTED = "ADAPTED"
    MISSING_COMPONENT = "MISSING_COMPONENT"
    FORBIDDEN_DOMAIN = "FORBIDDEN_DOMAIN"


ORBIT_V3_CLAIM_CEILING = "diagnostic_only"
ORBIT_V3_ALLOWED_USE = (
    "parity-typed orbit morphology compatibility",
    "local cyclic-chart conditioning",
    "shear-stratum and residual-stabilizer diagnostic",
    "explicit-channel v2 compatibility replay",
)
ORBIT_V3_FORBIDDEN_USE = (
    "complete invariant ring",
    "global orbit-separation proof",
    "native morphology atlas or native solver result",
    "source attribution or geometry detection",
    "Bianchi family identification",
    "likelihood, posterior, evidence, or truth certificate",
)
ORBIT_V3_REPRESENTATION = (
    "V2_SIGMA_STF_PLUS_V1_AXIAL_OMEGA_PLUS_V1_POLAR_ACCELERATION_"
    "PLUS_V1_POLAR_BETA_RM_PLUS_V1_POLAR_BETA_MO_PLUS_V0_DELTA_OMEGA_K"
)
ORBIT_V3_GENERIC_SEPARATION_STATUS = CatalogueProofStatus.UNPROVEN
ORBIT_V3_DEGREE_COMPLETENESS_STATUS = CatalogueProofStatus.UNPROVEN
ORBIT_V3_GLOBAL_CHART_COMPLETENESS_STATUS = CatalogueProofStatus.UNPROVEN
ORBIT_V3_VECTOR_CHANNELS = tuple(OrbitVectorChannel)
_SPEC_TOKEN = object()
_REPORT_TOKEN = object()

_VECTOR_PARITY: Mapping[OrbitVectorChannel, VectorParity] = {
    OrbitVectorChannel.OMEGA: VectorParity.AXIAL,
    OrbitVectorChannel.ACCELERATION: VectorParity.POLAR,
    OrbitVectorChannel.BETA_RM: VectorParity.POLAR,
    OrbitVectorChannel.BETA_MO: VectorParity.POLAR,
}


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OrbitCatalogueV3Error(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise OrbitCatalogueV3Error(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise OrbitCatalogueV3Error(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise OrbitCatalogueV3Error(f"{name} must not contain duplicates")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise OrbitCatalogueV3Error(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise OrbitCatalogueV3Error(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise OrbitCatalogueV3Error(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise OrbitCatalogueV3Error(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise OrbitCatalogueV3Error(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise OrbitCatalogueV3Error(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _real(value, name)
    if out <= 0.0:
        raise OrbitCatalogueV3Error(f"{name} must be positive")
    return out


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral):
        raise OrbitCatalogueV3Error(f"{name} must be an integer")
    out = int(value)
    if out < minimum:
        raise OrbitCatalogueV3Error(f"{name} must be at least {minimum}")
    return out


def _enum(value: object, enum_type: type[_StringEnum], name: str) -> _StringEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        raise OrbitCatalogueV3Error(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class OrbitCatalogueV3Spec:
    """Factory-built local-atlas declaration."""

    catalogue_id: str
    action_group: OrbitActionGroup
    stratum_absolute_tolerance: float
    stratum_relative_tolerance: float
    weak_chart_condition_limit: float
    representation: str = ORBIT_V3_REPRESENTATION
    generic_orbit_separation_status: CatalogueProofStatus = (
        ORBIT_V3_GENERIC_SEPARATION_STATUS
    )
    degree_completeness_status: CatalogueProofStatus = (
        ORBIT_V3_DEGREE_COMPLETENESS_STATUS
    )
    global_chart_completeness_status: CatalogueProofStatus = (
        ORBIT_V3_GLOBAL_CHART_COMPLETENESS_STATUS
    )
    claim_ceiling: str = ORBIT_V3_CLAIM_CEILING
    allowed_use: tuple[str, ...] = ORBIT_V3_ALLOWED_USE
    forbidden_use: tuple[str, ...] = ORBIT_V3_FORBIDDEN_USE
    _identity_seal: str = field(init=False, repr=False, compare=False)
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SPEC_TOKEN:
            raise OrbitCatalogueV3Error(
                "OrbitCatalogueV3Spec must be factory-built or replayed"
            )
        _text(self.catalogue_id, "catalogue_id")
        if type(self.action_group) is not OrbitActionGroup:
            raise OrbitCatalogueV3Error(
                "action_group must be an exact OrbitActionGroup"
            )
        absolute = _positive(
            self.stratum_absolute_tolerance,
            "stratum_absolute_tolerance",
        )
        relative = _positive(
            self.stratum_relative_tolerance,
            "stratum_relative_tolerance",
        )
        condition = _positive(
            self.weak_chart_condition_limit,
            "weak_chart_condition_limit",
        )
        if absolute > 1.0e-8 or relative > 1.0e-6:
            raise OrbitCatalogueV3Error(
                "stratum tolerances exceed the registered diagnostic ceiling"
            )
        if condition < 1.0e3:
            raise OrbitCatalogueV3Error(
                "weak_chart_condition_limit must be at least 1e3"
            )
        if self.representation != ORBIT_V3_REPRESENTATION:
            raise OrbitCatalogueV3Error("orbit representation drifted")
        for name in (
            "generic_orbit_separation_status",
            "degree_completeness_status",
            "global_chart_completeness_status",
        ):
            if getattr(self, name) is not CatalogueProofStatus.UNPROVEN:
                raise OrbitCatalogueV3Error(f"{name} must remain UNPROVEN")
        if self.claim_ceiling != ORBIT_V3_CLAIM_CEILING:
            raise OrbitCatalogueV3Error("orbit claim ceiling drifted")
        if tuple(self.allowed_use) != ORBIT_V3_ALLOWED_USE:
            raise OrbitCatalogueV3Error("orbit allowed-use lane drifted")
        if tuple(self.forbidden_use) != ORBIT_V3_FORBIDDEN_USE:
            raise OrbitCatalogueV3Error("orbit forbidden-use lane drifted")
        object.__setattr__(self, "stratum_absolute_tolerance", absolute)
        object.__setattr__(self, "stratum_relative_tolerance", relative)
        object.__setattr__(self, "weak_chart_condition_limit", condition)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "action_group": self.action_group.value,
            "allowed_use": list(self.allowed_use),
            "catalogue_id": self.catalogue_id,
            "claim_ceiling": self.claim_ceiling,
            "degree_completeness_status": (
                self.degree_completeness_status.value
            ),
            "forbidden_use": list(self.forbidden_use),
            "generic_orbit_separation_status": (
                self.generic_orbit_separation_status.value
            ),
            "global_chart_completeness_status": (
                self.global_chart_completeness_status.value
            ),
            "representation": self.representation,
            "schema": "HTT_ORBIT_CATALOGUE_V3_SPEC_V1",
            "stratum_absolute_tolerance_hex": (
                self.stratum_absolute_tolerance.hex()
            ),
            "stratum_relative_tolerance_hex": (
                self.stratum_relative_tolerance.hex()
            ),
            "weak_chart_condition_limit_hex": (
                self.weak_chart_condition_limit.hex()
            ),
        }

    def _assert_sealed(self) -> None:
        if (
            not hasattr(self, "_identity_seal")
            or _sha256_payload(self._payload_unchecked())
            != self._identity_seal
        ):
            raise OrbitCatalogueV3Error(
                "orbit catalogue spec identity drifted after construction"
            )

    @property
    def spec_id(self) -> str:
        self._assert_sealed()
        return self._identity_seal

    def to_payload(self) -> dict[str, object]:
        self._assert_sealed()
        return self._payload_unchecked()

    @classmethod
    def from_payload(cls, payload: object) -> "OrbitCatalogueV3Spec":
        if not isinstance(payload, Mapping):
            raise OrbitCatalogueV3Error("orbit spec payload must be a mapping")
        expected = {
            "action_group",
            "allowed_use",
            "catalogue_id",
            "claim_ceiling",
            "degree_completeness_status",
            "forbidden_use",
            "generic_orbit_separation_status",
            "global_chart_completeness_status",
            "representation",
            "schema",
            "stratum_absolute_tolerance_hex",
            "stratum_relative_tolerance_hex",
            "weak_chart_condition_limit_hex",
        }
        if set(payload) != expected:
            raise OrbitCatalogueV3Error("orbit spec payload keys mismatch")
        if payload["schema"] != "HTT_ORBIT_CATALOGUE_V3_SPEC_V1":
            raise OrbitCatalogueV3Error("unknown orbit spec schema")
        try:
            absolute = float.fromhex(
                str(payload["stratum_absolute_tolerance_hex"])
            )
            relative = float.fromhex(
                str(payload["stratum_relative_tolerance_hex"])
            )
            condition = float.fromhex(
                str(payload["weak_chart_condition_limit_hex"])
            )
        except ValueError as exc:
            raise OrbitCatalogueV3Error(
                "orbit spec tolerance hex is invalid"
            ) from exc
        return cls(
            catalogue_id=payload["catalogue_id"],  # type: ignore[arg-type]
            action_group=_enum(
                payload["action_group"],
                OrbitActionGroup,
                "action_group",
            ),  # type: ignore[arg-type]
            stratum_absolute_tolerance=absolute,
            stratum_relative_tolerance=relative,
            weak_chart_condition_limit=condition,
            representation=payload["representation"],  # type: ignore[arg-type]
            generic_orbit_separation_status=_enum(
                payload["generic_orbit_separation_status"],
                CatalogueProofStatus,
                "generic_orbit_separation_status",
            ),  # type: ignore[arg-type]
            degree_completeness_status=_enum(
                payload["degree_completeness_status"],
                CatalogueProofStatus,
                "degree_completeness_status",
            ),  # type: ignore[arg-type]
            global_chart_completeness_status=_enum(
                payload["global_chart_completeness_status"],
                CatalogueProofStatus,
                "global_chart_completeness_status",
            ),  # type: ignore[arg-type]
            claim_ceiling=payload["claim_ceiling"],  # type: ignore[arg-type]
            allowed_use=tuple(payload["allowed_use"]),  # type: ignore[arg-type]
            forbidden_use=tuple(payload["forbidden_use"]),  # type: ignore[arg-type]
            _construction_token=_SPEC_TOKEN,
        )


def build_orbit_catalogue_v3_spec(
    *,
    catalogue_id: str,
    action_group: OrbitActionGroup | str = OrbitActionGroup.O3,
    stratum_absolute_tolerance: float = 1.0e-12,
    stratum_relative_tolerance: float = 1.0e-10,
    weak_chart_condition_limit: float = 1.0e8,
) -> OrbitCatalogueV3Spec:
    """Build a closed v3 local-atlas declaration."""

    return OrbitCatalogueV3Spec(
        catalogue_id=catalogue_id,
        action_group=_enum(
            action_group,
            OrbitActionGroup,
            "action_group",
        ),  # type: ignore[arg-type]
        stratum_absolute_tolerance=stratum_absolute_tolerance,
        stratum_relative_tolerance=stratum_relative_tolerance,
        weak_chart_condition_limit=weak_chart_condition_limit,
        _construction_token=_SPEC_TOKEN,
    )


@dataclass(frozen=True)
class TypedOrbitInvariant:
    name: str
    value: float | None
    parity: OrbitScalarParity
    homogeneous_degree: int
    algebraic_form: InvariantAlgebraicForm
    source_channels: tuple[str, ...]
    availability: InvariantAvailability
    reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.name, "invariant name")
        if type(self.parity) is not OrbitScalarParity:
            raise OrbitCatalogueV3Error(
                "invariant parity must be an OrbitScalarParity"
            )
        object.__setattr__(
            self,
            "homogeneous_degree",
            _integer(
                self.homogeneous_degree,
                "homogeneous_degree",
                minimum=0,
            ),
        )
        if type(self.algebraic_form) is not InvariantAlgebraicForm:
            raise OrbitCatalogueV3Error(
                "algebraic_form must be an InvariantAlgebraicForm"
            )
        if (
            self.algebraic_form is InvariantAlgebraicForm.POLYNOMIAL
            and self.homogeneous_degree == 0
        ):
            raise OrbitCatalogueV3Error(
                "a nonconstant polynomial generator must have positive degree"
            )
        if (
            self.algebraic_form
            is InvariantAlgebraicForm.NORMALIZED_RATIONAL
            and self.homogeneous_degree != 0
        ):
            raise OrbitCatalogueV3Error(
                "a normalized rational shape coordinate must have degree zero"
            )
        object.__setattr__(
            self,
            "source_channels",
            _texts(self.source_channels, "source_channels"),
        )
        if type(self.availability) is not InvariantAvailability:
            raise OrbitCatalogueV3Error(
                "availability must be an InvariantAvailability"
            )
        if self.availability is InvariantAvailability.AVAILABLE:
            object.__setattr__(self, "value", _real(self.value, "value"))
            if self.reason is not None:
                raise OrbitCatalogueV3Error(
                    "available invariant must not carry a refusal reason"
                )
        else:
            if self.value is not None:
                raise OrbitCatalogueV3Error(
                    "unavailable invariant must not carry a value"
                )
            _text(self.reason, "invariant refusal reason")

    def as_payload(self) -> dict[str, object]:
        return {
            "algebraic_form": self.algebraic_form.value,
            "availability": self.availability.value,
            "homogeneous_degree": self.homogeneous_degree,
            "name": self.name,
            "parity": self.parity.value,
            "reason": self.reason,
            "source_channels": list(self.source_channels),
            "value": self.value,
        }


@dataclass(frozen=True)
class OrbitStratumReport:
    status: ShearOrbitStratum
    eigenvalues: tuple[float, float, float]
    eigenvalue_gaps: tuple[float, float]
    discriminant: float
    exact_zero_shear: bool
    exact_discriminant_zero: bool
    decision_tolerance: float
    local_only: bool = True

    def __post_init__(self) -> None:
        if type(self.status) is not ShearOrbitStratum:
            raise OrbitCatalogueV3Error(
                "stratum status must be a ShearOrbitStratum"
            )
        eigenvalues = tuple(
            _real(value, "eigenvalue") for value in self.eigenvalues
        )
        if len(eigenvalues) != 3 or eigenvalues != tuple(sorted(eigenvalues)):
            raise OrbitCatalogueV3Error(
                "eigenvalues must be three sorted finite values"
            )
        gaps = tuple(
            _nonnegative(value, "eigenvalue_gap")
            for value in self.eigenvalue_gaps
        )
        if len(gaps) != 2:
            raise OrbitCatalogueV3Error("eigenvalue_gaps must have length two")
        if type(self.exact_zero_shear) is not bool:
            raise OrbitCatalogueV3Error("exact_zero_shear must be boolean")
        if type(self.exact_discriminant_zero) is not bool:
            raise OrbitCatalogueV3Error(
                "exact_discriminant_zero must be boolean"
            )
        if self.local_only is not True:
            raise OrbitCatalogueV3Error("orbit stratum must remain local_only")
        object.__setattr__(self, "eigenvalues", eigenvalues)
        object.__setattr__(self, "eigenvalue_gaps", gaps)
        object.__setattr__(
            self,
            "discriminant",
            _nonnegative(self.discriminant, "discriminant"),
        )
        object.__setattr__(
            self,
            "decision_tolerance",
            _positive(self.decision_tolerance, "decision_tolerance"),
        )

    def as_payload(self) -> dict[str, object]:
        return {
            "decision_tolerance": self.decision_tolerance,
            "discriminant": self.discriminant,
            "eigenvalue_gaps": list(self.eigenvalue_gaps),
            "eigenvalues": list(self.eigenvalues),
            "exact_discriminant_zero": self.exact_discriminant_zero,
            "exact_zero_shear": self.exact_zero_shear,
            "local_only": self.local_only,
            "status": self.status.value,
        }


@dataclass(frozen=True)
class CyclicChartReport:
    channel: OrbitVectorChannel
    vector_parity: VectorParity
    status: CyclicChartStatus
    coordinate_status: ChartCoordinateStatus
    coordinates: tuple[TypedOrbitInvariant, ...]
    determinant: float | None
    singular_values: tuple[float, ...]
    rank: int | None
    condition_number: float | None
    reciprocal_condition: float | None
    exact_determinant_zero: bool | None
    reason: str | None
    local_only: bool = True

    def __post_init__(self) -> None:
        if type(self.channel) is not OrbitVectorChannel:
            raise OrbitCatalogueV3Error(
                "chart channel must be an OrbitVectorChannel"
            )
        if self.vector_parity is not _VECTOR_PARITY[self.channel]:
            raise OrbitCatalogueV3Error("chart vector parity drifted")
        if type(self.status) is not CyclicChartStatus:
            raise OrbitCatalogueV3Error(
                "chart status must be a CyclicChartStatus"
            )
        if type(self.coordinate_status) is not ChartCoordinateStatus:
            raise OrbitCatalogueV3Error(
                "coordinate_status must be a ChartCoordinateStatus"
            )
        coordinates = tuple(self.coordinates)
        if (
            len(coordinates) != 14
            or any(type(item) is not TypedOrbitInvariant for item in coordinates)
        ):
            raise OrbitCatalogueV3Error(
                "a canonical cyclic chart must contain 14 typed coordinates"
            )
        coordinate_names = tuple(item.name for item in coordinates)
        if coordinate_names != _chart_coordinate_names(self.channel):
            raise OrbitCatalogueV3Error(
                "cyclic-chart coordinate order drifted"
            )
        complete = all(
            item.availability is InvariantAvailability.AVAILABLE
            for item in coordinates
        )
        expected_coordinate_status = (
            ChartCoordinateStatus.COMPLETE
            if complete
            else ChartCoordinateStatus.PARTIAL
        )
        if self.coordinate_status is not expected_coordinate_status:
            raise OrbitCatalogueV3Error(
                "coordinate_status does not match typed coordinate availability"
            )
        if self.local_only is not True:
            raise OrbitCatalogueV3Error("cyclic chart must remain local_only")
        if self.status is CyclicChartStatus.MISSING_COMPONENT:
            if any(
                value is not None
                for value in (
                    self.determinant,
                    self.rank,
                    self.condition_number,
                    self.reciprocal_condition,
                    self.exact_determinant_zero,
                )
            ) or self.singular_values:
                raise OrbitCatalogueV3Error(
                    "missing chart must not carry numerical fields"
                )
            _text(self.reason, "chart missing reason")
            object.__setattr__(self, "coordinates", coordinates)
            return
        determinant = _real(self.determinant, "chart determinant")
        singular = tuple(
            _nonnegative(value, "chart singular value")
            for value in self.singular_values
        )
        if len(singular) != 3 or singular != tuple(
            sorted(singular, reverse=True)
        ):
            raise OrbitCatalogueV3Error(
                "chart singular values must be length-three descending"
            )
        rank = _integer(self.rank, "chart rank", minimum=0)
        if rank > 3:
            raise OrbitCatalogueV3Error("chart rank must not exceed three")
        reciprocal = _nonnegative(
            self.reciprocal_condition,
            "reciprocal_condition",
        )
        if reciprocal > 1.0:
            raise OrbitCatalogueV3Error(
                "reciprocal_condition must be at most one"
            )
        if type(self.exact_determinant_zero) is not bool:
            raise OrbitCatalogueV3Error(
                "exact_determinant_zero must be boolean"
            )
        if self.reason is not None:
            _text(self.reason, "chart reason")
        if self.status is CyclicChartStatus.NONCYCLIC:
            if (
                rank >= 3
                or reciprocal != 0.0
                or self.condition_number is not None
            ):
                raise OrbitCatalogueV3Error(
                    "noncyclic chart must be rank deficient, have undefined "
                    "condition number, and zero reciprocal condition"
                )
            condition = None
            _text(self.reason, "noncyclic chart reason")
        elif self.status is CyclicChartStatus.WEAKLY_CONDITIONED:
            condition = _positive(
                self.condition_number,
                "condition_number",
            )
            if rank != 3 or reciprocal <= 0.0:
                raise OrbitCatalogueV3Error(
                    "weak chart must be full rank with positive reciprocal condition"
                )
            if condition < 1.0:
                raise OrbitCatalogueV3Error(
                    "full-rank chart condition number must be at least one"
                )
            _text(self.reason, "weak-chart reason")
        else:
            condition = _positive(
                self.condition_number,
                "condition_number",
            )
            if rank != 3 or reciprocal <= 0.0 or self.reason is not None:
                raise OrbitCatalogueV3Error(
                    "cyclic candidate must be full rank and carry no refusal reason"
                )
            if condition < 1.0:
                raise OrbitCatalogueV3Error(
                    "full-rank chart condition number must be at least one"
                )
        if condition is not None and not math.isclose(
            condition * reciprocal,
            1.0,
            rel_tol=1.0e-10,
            abs_tol=1.0e-12,
        ):
            raise OrbitCatalogueV3Error(
                "condition and reciprocal-condition fields are inconsistent"
            )
        if self.exact_determinant_zero is not (determinant == 0.0):
            raise OrbitCatalogueV3Error(
                "exact_determinant_zero does not match the stored determinant"
            )
        object.__setattr__(self, "determinant", determinant)
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "singular_values", singular)
        object.__setattr__(self, "rank", rank)
        object.__setattr__(self, "condition_number", condition)
        object.__setattr__(self, "reciprocal_condition", reciprocal)

    def as_payload(self) -> dict[str, object]:
        return {
            "channel": self.channel.value,
            "condition_number": self.condition_number,
            "coordinate_status": self.coordinate_status.value,
            "coordinates": [item.as_payload() for item in self.coordinates],
            "determinant": self.determinant,
            "exact_determinant_zero": self.exact_determinant_zero,
            "local_only": self.local_only,
            "rank": self.rank,
            "reason": self.reason,
            "reciprocal_condition": self.reciprocal_condition,
            "singular_values": list(self.singular_values),
            "status": self.status.value,
            "vector_parity": self.vector_parity.value,
        }


@dataclass(frozen=True)
class ChartOverlapReport:
    left_channel: OrbitVectorChannel
    right_channel: OrbitVectorChannel
    status: ChartOverlapStatus
    transition_determinant: float | None
    transition_condition_number: float | None
    reason: str | None
    local_only: bool = True

    def __post_init__(self) -> None:
        if (
            type(self.left_channel) is not OrbitVectorChannel
            or type(self.right_channel) is not OrbitVectorChannel
            or self.left_channel.value >= self.right_channel.value
        ):
            raise OrbitCatalogueV3Error(
                "chart overlap channels must be a canonical distinct pair"
            )
        if type(self.status) is not ChartOverlapStatus:
            raise OrbitCatalogueV3Error(
                "overlap status must be a ChartOverlapStatus"
            )
        if self.local_only is not True:
            raise OrbitCatalogueV3Error("chart overlap must remain local_only")
        if self.status is ChartOverlapStatus.DEFINED_LOCAL_OVERLAP:
            object.__setattr__(
                self,
                "transition_determinant",
                _real(
                    self.transition_determinant,
                    "transition_determinant",
                ),
            )
            object.__setattr__(
                self,
                "transition_condition_number",
                _nonnegative(
                    self.transition_condition_number,
                    "transition_condition_number",
                ),
            )
            if self.transition_condition_number < 1.0:
                raise OrbitCatalogueV3Error(
                    "a defined overlap condition number must be at least one"
                )
            if self.transition_determinant == 0.0:
                raise OrbitCatalogueV3Error(
                    "a defined overlap transition must be nonsingular"
                )
            if self.reason is not None:
                raise OrbitCatalogueV3Error(
                    "defined overlap must not carry a reason"
                )
        else:
            if (
                self.transition_determinant is not None
                or self.transition_condition_number is not None
            ):
                raise OrbitCatalogueV3Error(
                    "undefined overlap must not carry numerical values"
                )
            _text(self.reason, "overlap refusal reason")

    def as_payload(self) -> dict[str, object]:
        return {
            "left_channel": self.left_channel.value,
            "local_only": self.local_only,
            "reason": self.reason,
            "right_channel": self.right_channel.value,
            "status": self.status.value,
            "transition_condition_number": (
                self.transition_condition_number
            ),
            "transition_determinant": self.transition_determinant,
        }


@dataclass(frozen=True)
class StabilizerReport:
    shear_stabilizer: ShearStabilizer
    joint_status: JointStabilizerStatus
    selected_chart: OrbitVectorChannel | None
    reasons: tuple[str, ...]
    globally_certified: bool = False

    def __post_init__(self) -> None:
        if type(self.shear_stabilizer) is not ShearStabilizer:
            raise OrbitCatalogueV3Error(
                "shear_stabilizer must use the registered vocabulary"
            )
        if type(self.joint_status) is not JointStabilizerStatus:
            raise OrbitCatalogueV3Error(
                "joint_status must use the registered vocabulary"
            )
        if (
            self.selected_chart is not None
            and type(self.selected_chart) is not OrbitVectorChannel
        ):
            raise OrbitCatalogueV3Error(
                "selected_chart must be an OrbitVectorChannel"
            )
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "stabilizer reasons"),
        )
        if self.globally_certified is not False:
            raise OrbitCatalogueV3Error(
                "numerical stabilizer report cannot be globally certified"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "globally_certified": self.globally_certified,
            "joint_status": self.joint_status.value,
            "reasons": list(self.reasons),
            "selected_chart": (
                None if self.selected_chart is None else self.selected_chart.value
            ),
            "shear_stabilizer": self.shear_stabilizer.value,
        }


@dataclass(frozen=True)
class OrbitCatalogueV3Report:
    spec: OrbitCatalogueV3Spec
    source_state_id: str
    stratum: OrbitStratumReport
    stabilizer: StabilizerReport
    charts: tuple[CyclicChartReport, ...]
    chart_overlaps: tuple[ChartOverlapReport, ...]
    invariants: tuple[TypedOrbitInvariant, ...]
    missing_components: tuple[str, ...]
    transfer_source: str
    claim_ceiling: str = ORBIT_V3_CLAIM_CEILING
    allowed_use: tuple[str, ...] = ORBIT_V3_ALLOWED_USE
    forbidden_use: tuple[str, ...] = ORBIT_V3_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise OrbitCatalogueV3Error(
                "OrbitCatalogueV3Report must be created by orbit_catalogue_v3"
            )
        if type(self.spec) is not OrbitCatalogueV3Spec:
            raise OrbitCatalogueV3Error("spec must be an OrbitCatalogueV3Spec")
        self.spec._assert_sealed()
        _text(self.source_state_id, "source_state_id")
        if type(self.stratum) is not OrbitStratumReport:
            raise OrbitCatalogueV3Error("stratum must be an OrbitStratumReport")
        if type(self.stabilizer) is not StabilizerReport:
            raise OrbitCatalogueV3Error(
                "stabilizer must be a StabilizerReport"
            )
        charts = tuple(self.charts)
        if (
            len(charts) != len(ORBIT_V3_VECTOR_CHANNELS)
            or any(type(chart) is not CyclicChartReport for chart in charts)
            or tuple(chart.channel for chart in charts)
            != ORBIT_V3_VECTOR_CHANNELS
        ):
            raise OrbitCatalogueV3Error(
                "charts must cover the registered vector channels in order"
            )
        overlaps = tuple(self.chart_overlaps)
        expected_overlap_pairs = tuple(
            sorted(
                (
                    min(left, right, key=lambda item: item.value),
                    max(left, right, key=lambda item: item.value),
                )
                for left, right in itertools.combinations(
                    ORBIT_V3_VECTOR_CHANNELS,
                    2,
                )
            )
        )
        if (
            len(overlaps) != len(expected_overlap_pairs)
            or any(type(item) is not ChartOverlapReport for item in overlaps)
            or tuple(
                (item.left_channel, item.right_channel) for item in overlaps
            )
            != expected_overlap_pairs
        ):
            raise OrbitCatalogueV3Error(
                "chart overlaps must cover every canonical channel pair"
            )
        invariants = tuple(self.invariants)
        if any(type(item) is not TypedOrbitInvariant for item in invariants):
            raise OrbitCatalogueV3Error(
                "invariants must be exact TypedOrbitInvariant objects"
            )
        names = tuple(item.name for item in invariants)
        if names != _signature_names():
            raise OrbitCatalogueV3Error(
                "invariant signature does not match the registered generator rule"
            )
        missing_components = _texts(
            self.missing_components,
            "missing_components",
            empty_ok=True,
        )
        expected_missing_components = tuple(
            chart.channel.value
            for chart in charts
            if chart.status is CyclicChartStatus.MISSING_COMPONENT
        )
        if missing_components != expected_missing_components:
            raise OrbitCatalogueV3Error(
                "missing_components must match missing reference channels"
            )
        object.__setattr__(
            self,
            "missing_components",
            missing_components,
        )
        _text(self.transfer_source, "transfer_source")
        if self.claim_ceiling != ORBIT_V3_CLAIM_CEILING:
            raise OrbitCatalogueV3Error("report claim ceiling drifted")
        if tuple(self.allowed_use) != ORBIT_V3_ALLOWED_USE:
            raise OrbitCatalogueV3Error("report allowed-use lane drifted")
        if tuple(self.forbidden_use) != ORBIT_V3_FORBIDDEN_USE:
            raise OrbitCatalogueV3Error("report forbidden-use lane drifted")
        object.__setattr__(self, "charts", charts)
        object.__setattr__(self, "chart_overlaps", overlaps)
        object.__setattr__(self, "invariants", invariants)
        for chart in charts:
            if (
                chart.status is CyclicChartStatus.WEAKLY_CONDITIONED
                and chart.condition_number <= self.spec.weak_chart_condition_limit
            ):
                raise OrbitCatalogueV3Error(
                    "weak chart must exceed the registered condition limit"
                )
            if (
                chart.status
                is CyclicChartStatus.NUMERICALLY_CYCLIC_CANDIDATE
                and chart.condition_number > self.spec.weak_chart_condition_limit
            ):
                raise OrbitCatalogueV3Error(
                    "cyclic candidate exceeds the registered condition limit"
                )
        expected_shear_stabilizer = _shear_stabilizer(
            self.stratum.status,
            self.spec.action_group,
        )
        if self.stabilizer.shear_stabilizer is not expected_shear_stabilizer:
            raise OrbitCatalogueV3Error(
                "shear stabilizer does not match the stratum and action group"
            )
        chart_by_channel = {chart.channel: chart for chart in charts}
        for overlap in overlaps:
            left = chart_by_channel[overlap.left_channel]
            right = chart_by_channel[overlap.right_channel]
            should_be_defined = (
                left.rank == 3
                and right.rank == 3
                and left.coordinate_status is ChartCoordinateStatus.COMPLETE
                and right.coordinate_status is ChartCoordinateStatus.COMPLETE
            )
            if should_be_defined != (
                overlap.status is ChartOverlapStatus.DEFINED_LOCAL_OVERLAP
            ):
                raise OrbitCatalogueV3Error(
                    "chart overlap status does not match chart availability"
                )
        selected = self.stabilizer.selected_chart
        if selected is None:
            if (
                self.stabilizer.joint_status
                is not JointStabilizerStatus.RESIDUAL_STABILIZER_UNRESOLVED
            ):
                raise OrbitCatalogueV3Error(
                    "an unresolved joint stabilizer must not select a chart"
                )
        else:
            selected_report = chart_by_channel[selected]
            if (
                self.stabilizer.joint_status
                is not JointStabilizerStatus.NUMERICALLY_TRIVIAL_CANDIDATE
                or selected_report.status
                is not CyclicChartStatus.NUMERICALLY_CYCLIC_CANDIDATE
                or selected_report.coordinate_status
                is not ChartCoordinateStatus.COMPLETE
            ):
                raise OrbitCatalogueV3Error(
                    "selected stabilizer chart must be complete and well conditioned"
                )

    @property
    def report_id(self) -> str:
        return _sha256_payload(self.as_payload())

    @property
    def invariants_by_name(self) -> dict[str, TypedOrbitInvariant]:
        return {item.name: item for item in self.invariants}

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "chart_overlaps": [
                item.as_payload() for item in self.chart_overlaps
            ],
            "charts": [item.as_payload() for item in self.charts],
            "claim_ceiling": self.claim_ceiling,
            "forbidden_use": list(self.forbidden_use),
            "invariants": [item.as_payload() for item in self.invariants],
            "missing_components": list(self.missing_components),
            "schema": "HTT_ORBIT_CATALOGUE_V3_REPORT_V1",
            "source_state_id": self.source_state_id,
            "spec": self.spec.to_payload(),
            "spec_id": self.spec.spec_id,
            "stabilizer": self.stabilizer.as_payload(),
            "stratum": self.stratum.as_payload(),
            "transfer_source": self.transfer_source,
        }


@dataclass(frozen=True)
class LegacyV2AdapterReport:
    status: LegacyV2AdapterStatus
    beta_channel: LegacyBetaChannel
    source_state_id: str
    v2_report: OrbitCatalogueV2Report | None
    missing_components: tuple[str, ...]
    reason: str | None
    automatic_beta_selection: bool = False
    claim_ceiling: str = ORBIT_V3_CLAIM_CEILING

    def __post_init__(self) -> None:
        if type(self.status) is not LegacyV2AdapterStatus:
            raise OrbitCatalogueV3Error(
                "legacy adapter status must use the registered vocabulary"
            )
        if type(self.beta_channel) is not LegacyBetaChannel:
            raise OrbitCatalogueV3Error(
                "beta_channel must be an exact LegacyBetaChannel"
            )
        _text(self.source_state_id, "source_state_id")
        missing = _texts(
            self.missing_components,
            "missing_components",
            empty_ok=True,
        )
        object.__setattr__(self, "missing_components", missing)
        if self.automatic_beta_selection is not False:
            raise OrbitCatalogueV3Error(
                "legacy beta channel must never be selected automatically"
            )
        if self.claim_ceiling != ORBIT_V3_CLAIM_CEILING:
            raise OrbitCatalogueV3Error("legacy adapter claim ceiling drifted")
        if self.status is LegacyV2AdapterStatus.ADAPTED:
            if type(self.v2_report) is not OrbitCatalogueV2Report:
                raise OrbitCatalogueV3Error(
                    "adapted legacy report requires an exact v2 report"
                )
            if missing or self.reason is not None:
                raise OrbitCatalogueV3Error(
                    "adapted legacy report must not carry refusal evidence"
                )
        else:
            if self.v2_report is not None:
                raise OrbitCatalogueV3Error(
                    "refused legacy adapter must not carry a v2 report"
                )
            _text(self.reason, "legacy adapter refusal reason")

    def as_payload(self) -> dict[str, object]:
        return {
            "automatic_beta_selection": self.automatic_beta_selection,
            "beta_channel": self.beta_channel.value,
            "claim_ceiling": self.claim_ceiling,
            "missing_components": list(self.missing_components),
            "reason": self.reason,
            "schema": "HTT_ORBIT_V3_LEGACY_V2_ADAPTER_V1",
            "source_state_id": self.source_state_id,
            "status": self.status.value,
            "v2_report": (
                None if self.v2_report is None else self.v2_report.as_payload()
            ),
        }


def _checked_state(state: JointAnisotropyState) -> JointAnisotropyState:
    try:
        checked = require_exact_joint_anisotropy_state(state)
    except JointAnisotropyStateError as exc:
        raise OrbitCatalogueV3Error(
            "joint state failed canonical replay"
        ) from exc
    if checked.basis != STF5_CARTESIAN_BASIS:
        raise OrbitCatalogueV3Error(
            "orbit catalogue v3 requires the registered STF5 Cartesian basis"
        )
    return checked


def _checked_spec(spec: OrbitCatalogueV3Spec) -> OrbitCatalogueV3Spec:
    if type(spec) is not OrbitCatalogueV3Spec:
        raise TypeError("spec must be an exact OrbitCatalogueV3Spec")
    try:
        checked = OrbitCatalogueV3Spec.from_payload(spec.to_payload())
    except OrbitCatalogueV3Error as exc:
        raise OrbitCatalogueV3Error(
            "orbit catalogue spec failed canonical replay"
        ) from exc
    if checked != spec or checked.spec_id != spec.spec_id:
        raise OrbitCatalogueV3Error("orbit catalogue spec identity drifted")
    return checked


def apply_orbit_group_action(
    state: JointAnisotropyState,
    transform: O3Transform,
    *,
    group: OrbitActionGroup | str,
) -> JointAnisotropyState:
    """Apply O(3), or the proper-only SO(3) subgroup, to a joint state."""

    checked = _checked_state(state)
    if type(transform) is not O3Transform:
        raise TypeError("transform must be an exact O3Transform")
    resolved = _enum(group, OrbitActionGroup, "group")
    if (
        resolved is OrbitActionGroup.SO3
        and transform.determinant != 1
    ):
        raise OrbitCatalogueV3Error(
            "SO3 action refuses an improper O3 transformation"
        )
    return apply_o3_action(checked, transform)


def _vector_value(
    state: JointAnisotropyState,
    channel: OrbitVectorChannel,
) -> tuple[float, ...] | MissingComponent:
    if channel is OrbitVectorChannel.OMEGA:
        return state.congruence_kinematics.omega_axial3
    if channel is OrbitVectorChannel.ACCELERATION:
        return state.congruence_kinematics.acceleration_polar3
    if channel is OrbitVectorChannel.BETA_RM:
        return state.velocity_frames.beta_RM
    if channel is OrbitVectorChannel.BETA_MO:
        return state.velocity_frames.beta_MO
    raise OrbitCatalogueV3Error(f"unknown vector channel {channel.value}")


def _canonical_channel_pair(
    left: OrbitVectorChannel,
    right: OrbitVectorChannel,
) -> tuple[OrbitVectorChannel, OrbitVectorChannel]:
    order = {channel: index for index, channel in enumerate(ORBIT_V3_VECTOR_CHANNELS)}
    return (left, right) if order[left] <= order[right] else (right, left)


def _gram_name(
    power: int,
    left: OrbitVectorChannel,
    right: OrbitVectorChannel,
) -> str:
    canonical_left, canonical_right = _canonical_channel_pair(left, right)
    return f"G{power}:{canonical_left.value}:{canonical_right.value}"


def _signature_names() -> tuple[str, ...]:
    names = [
        "tr_sigma2",
        "tr_sigma3",
        "delta_omega_k",
        "J_sigma",
    ]
    for left, right in itertools.combinations_with_replacement(
        ORBIT_V3_VECTOR_CHANNELS,
        2,
    ):
        names.extend(_gram_name(power, left, right) for power in range(3))
    names.extend(
        f"K:{channel.value}" for channel in ORBIT_V3_VECTOR_CHANNELS
    )
    names.extend(
        "E:" + ":".join(channel.value for channel in channels)
        for channels in itertools.combinations(ORBIT_V3_VECTOR_CHANNELS, 3)
    )
    return tuple(names)


def _chart_coordinate_names(
    reference: OrbitVectorChannel,
) -> tuple[str, ...]:
    names = ["tr_sigma2", "tr_sigma3"]
    for channel in ORBIT_V3_VECTOR_CHANNELS:
        names.extend(
            _gram_name(power, reference, channel) for power in range(3)
        )
    return tuple(names)


def _shear_stabilizer(
    stratum: ShearOrbitStratum,
    group: OrbitActionGroup,
) -> ShearStabilizer:
    if stratum is ShearOrbitStratum.NUMERICALLY_UNRESOLVED:
        return ShearStabilizer.NUMERICALLY_UNRESOLVED
    return {
        (ShearOrbitStratum.ZERO_SHEAR, OrbitActionGroup.SO3): (
            ShearStabilizer.SO3_FULL
        ),
        (ShearOrbitStratum.ZERO_SHEAR, OrbitActionGroup.O3): (
            ShearStabilizer.O3_FULL
        ),
        (
            ShearOrbitStratum.REPEATED_EIGENVALUE,
            OrbitActionGroup.SO3,
        ): ShearStabilizer.SO3_AXISYMMETRIC_O2,
        (
            ShearOrbitStratum.REPEATED_EIGENVALUE,
            OrbitActionGroup.O3,
        ): ShearStabilizer.O3_AXISYMMETRIC_O2_X_Z2,
        (
            ShearOrbitStratum.SIMPLE_SPECTRUM,
            OrbitActionGroup.SO3,
        ): ShearStabilizer.SO3_SIMPLE_KLEIN_FOUR,
        (
            ShearOrbitStratum.SIMPLE_SPECTRUM,
            OrbitActionGroup.O3,
        ): ShearStabilizer.O3_SIMPLE_SIGN_EIGHT,
    }[(stratum, group)]


def _stratum(
    sigma: np.ndarray,
    spec: OrbitCatalogueV3Spec,
) -> OrbitStratumReport:
    eigenvalues_array = np.linalg.eigvalsh(sigma)
    eigenvalues = tuple(float(value) for value in eigenvalues_array)
    gaps = (
        float(eigenvalues_array[1] - eigenvalues_array[0]),
        float(eigenvalues_array[2] - eigenvalues_array[1]),
    )
    discriminant = float(
        (eigenvalues_array[1] - eigenvalues_array[0]) ** 2
        * (eigenvalues_array[2] - eigenvalues_array[0]) ** 2
        * (eigenvalues_array[2] - eigenvalues_array[1]) ** 2
    )
    exact_zero = bool(np.count_nonzero(sigma) == 0)
    exact_discriminant_zero = bool(discriminant == 0.0)
    scale = max(1.0, float(np.max(np.abs(eigenvalues_array))))
    tolerance = (
        spec.stratum_absolute_tolerance
        + spec.stratum_relative_tolerance * scale
    )
    if exact_zero:
        status = ShearOrbitStratum.ZERO_SHEAR
    elif exact_discriminant_zero:
        status = ShearOrbitStratum.REPEATED_EIGENVALUE
    elif min(gaps) <= tolerance:
        status = ShearOrbitStratum.NUMERICALLY_UNRESOLVED
    else:
        status = ShearOrbitStratum.SIMPLE_SPECTRUM
    return OrbitStratumReport(
        status=status,
        eigenvalues=eigenvalues,  # type: ignore[arg-type]
        eigenvalue_gaps=gaps,
        discriminant=max(0.0, discriminant),
        exact_zero_shear=exact_zero,
        exact_discriminant_zero=exact_discriminant_zero,
        decision_tolerance=tolerance,
    )


def _chart(
    channel: OrbitVectorChannel,
    value: tuple[float, ...] | MissingComponent,
    sigma: np.ndarray,
    spec: OrbitCatalogueV3Spec,
    signature: Mapping[str, TypedOrbitInvariant],
) -> tuple[CyclicChartReport, np.ndarray | None]:
    coordinates = tuple(
        signature[name] for name in _chart_coordinate_names(channel)
    )
    coordinate_status = (
        ChartCoordinateStatus.COMPLETE
        if all(
            item.availability is InvariantAvailability.AVAILABLE
            for item in coordinates
        )
        else ChartCoordinateStatus.PARTIAL
    )
    if type(value) is MissingComponent:
        return (
            CyclicChartReport(
                channel=channel,
                vector_parity=_VECTOR_PARITY[channel],
                status=CyclicChartStatus.MISSING_COMPONENT,
                coordinate_status=coordinate_status,
                coordinates=coordinates,
                determinant=None,
                singular_values=(),
                rank=None,
                condition_number=None,
                reciprocal_condition=None,
                exact_determinant_zero=None,
                reason=value.reason,
            ),
            None,
        )
    vector = np.asarray(value, dtype=float)
    krylov = np.column_stack((vector, sigma @ vector, sigma @ sigma @ vector))
    singular_values = np.linalg.svd(krylov, compute_uv=False)
    tolerance = max(
        spec.stratum_absolute_tolerance,
        64.0
        * np.finfo(float).eps
        * float(singular_values[0] if singular_values.size else 1.0),
    )
    rank = int(np.sum(singular_values > tolerance))
    determinant = float(np.linalg.det(krylov))
    exact_zero = bool(determinant == 0.0)
    if rank < 3:
        status = CyclicChartStatus.NONCYCLIC
        condition = None
        reciprocal = 0.0
        reason = "Krylov matrix is rank deficient"
    else:
        condition = float(singular_values[0] / singular_values[-1])
        reciprocal = float(singular_values[-1] / singular_values[0])
        if condition > spec.weak_chart_condition_limit:
            status = CyclicChartStatus.WEAKLY_CONDITIONED
            reason = "Krylov chart exceeds the registered condition limit"
        else:
            status = CyclicChartStatus.NUMERICALLY_CYCLIC_CANDIDATE
            reason = None
    return (
        CyclicChartReport(
            channel=channel,
            vector_parity=_VECTOR_PARITY[channel],
            status=status,
            coordinate_status=coordinate_status,
            coordinates=coordinates,
            determinant=determinant,
            singular_values=tuple(float(value) for value in singular_values),
            rank=rank,
            condition_number=condition,
            reciprocal_condition=reciprocal,
            exact_determinant_zero=exact_zero,
            reason=reason,
        ),
        krylov,
    )


def _overlaps(
    charts: tuple[CyclicChartReport, ...],
    matrices: Mapping[OrbitVectorChannel, np.ndarray | None],
) -> tuple[ChartOverlapReport, ...]:
    out: list[ChartOverlapReport] = []
    for left, right in itertools.combinations(charts, 2):
        left_matrix = matrices[left.channel]
        right_matrix = matrices[right.channel]
        if (
            left.rank == 3
            and right.rank == 3
            and left.coordinate_status is ChartCoordinateStatus.COMPLETE
            and right.coordinate_status is ChartCoordinateStatus.COMPLETE
        ):
            assert left_matrix is not None and right_matrix is not None
            try:
                transition = np.linalg.solve(left_matrix, right_matrix)
                transition_determinant = float(np.linalg.det(transition))
                transition_condition = float(np.linalg.cond(transition))
            except np.linalg.LinAlgError:
                transition = None
            if (
                transition is not None
                and math.isfinite(transition_determinant)
                and transition_determinant != 0.0
                and math.isfinite(transition_condition)
            ):
                out.append(
                    ChartOverlapReport(
                        left_channel=min(
                            left.channel,
                            right.channel,
                            key=lambda item: item.value,
                        ),
                        right_channel=max(
                            left.channel,
                            right.channel,
                            key=lambda item: item.value,
                        ),
                        status=ChartOverlapStatus.DEFINED_LOCAL_OVERLAP,
                        transition_determinant=transition_determinant,
                        transition_condition_number=transition_condition,
                        reason=None,
                    )
                )
                continue
        out.append(
            ChartOverlapReport(
                left_channel=min(
                    left.channel,
                    right.channel,
                    key=lambda item: item.value,
                ),
                right_channel=max(
                    left.channel,
                    right.channel,
                    key=lambda item: item.value,
                ),
                status=ChartOverlapStatus.SINGULAR_OR_MISSING,
                transition_determinant=None,
                transition_condition_number=None,
                reason=(
                    "one or both local charts are singular, incomplete, "
                    "missing, or numerically unsolved"
                ),
            )
        )
    return tuple(
        sorted(
            out,
            key=lambda item: (
                item.left_channel.value,
                item.right_channel.value,
            ),
        )
    )


def _available_invariant(
    *,
    name: str,
    value: float,
    parity: OrbitScalarParity,
    degree: int,
    source_channels: tuple[str, ...],
    algebraic_form: InvariantAlgebraicForm = (
        InvariantAlgebraicForm.POLYNOMIAL
    ),
) -> TypedOrbitInvariant:
    return TypedOrbitInvariant(
        name=name,
        value=value,
        parity=parity,
        homogeneous_degree=degree,
        algebraic_form=algebraic_form,
        source_channels=source_channels,
        availability=InvariantAvailability.AVAILABLE,
    )


def _missing_invariant(
    *,
    name: str,
    parity: OrbitScalarParity,
    degree: int,
    source_channels: tuple[str, ...],
    reason: str,
    algebraic_form: InvariantAlgebraicForm = (
        InvariantAlgebraicForm.POLYNOMIAL
    ),
) -> TypedOrbitInvariant:
    return TypedOrbitInvariant(
        name=name,
        value=None,
        parity=parity,
        homogeneous_degree=degree,
        algebraic_form=algebraic_form,
        source_channels=source_channels,
        availability=InvariantAvailability.MISSING_COMPONENT,
        reason=reason,
    )


def _pair_parity(
    left: OrbitVectorChannel,
    right: OrbitVectorChannel,
) -> OrbitScalarParity:
    return (
        OrbitScalarParity.O3_PSEUDOSCALAR
        if _VECTOR_PARITY[left] is not _VECTOR_PARITY[right]
        else OrbitScalarParity.O3_SCALAR
    )


def _signature(
    state: JointAnisotropyState,
    sigma: np.ndarray,
    vectors: Mapping[
        OrbitVectorChannel,
        tuple[float, ...] | MissingComponent,
    ],
) -> tuple[TypedOrbitInvariant, ...]:
    sigma2 = sigma @ sigma
    powers = (np.eye(3), sigma, sigma2)
    tr_sigma2 = float(np.trace(sigma2))
    tr_sigma3 = float(np.trace(sigma2 @ sigma))
    out: list[TypedOrbitInvariant] = [
        _available_invariant(
            name="tr_sigma2",
            value=tr_sigma2,
            parity=OrbitScalarParity.O3_SCALAR,
            degree=2,
            source_channels=("sigma_stf5",),
        ),
        _available_invariant(
            name="tr_sigma3",
            value=tr_sigma3,
            parity=OrbitScalarParity.O3_SCALAR,
            degree=3,
            source_channels=("sigma_stf5",),
        ),
        _available_invariant(
            name="delta_omega_k",
            value=state.geometry_state.delta_omega_k,
            parity=OrbitScalarParity.O3_SCALAR,
            degree=1,
            source_channels=("delta_omega_k",),
        ),
    ]
    if tr_sigma2 > 0.0:
        out.append(
            _available_invariant(
                name="J_sigma",
                value=math.sqrt(6.0)
                * tr_sigma3
                / (tr_sigma2 ** 1.5),
                parity=OrbitScalarParity.O3_SCALAR,
                degree=0,
                source_channels=("sigma_stf5",),
                algebraic_form=InvariantAlgebraicForm.NORMALIZED_RATIONAL,
            )
        )
    else:
        out.append(
            _missing_invariant(
                name="J_sigma",
                parity=OrbitScalarParity.O3_SCALAR,
                degree=0,
                source_channels=("sigma_stf5",),
                reason="J_sigma is undefined when tr_sigma2 is zero",
                algebraic_form=InvariantAlgebraicForm.NORMALIZED_RATIONAL,
            )
        )

    for left, right in itertools.combinations_with_replacement(
        ORBIT_V3_VECTOR_CHANNELS,
        2,
    ):
        left_value = vectors[left]
        right_value = vectors[right]
        parity = _pair_parity(left, right)
        missing = tuple(
            value
            for value, item in (
                (left.value, left_value),
                (right.value, right_value),
            )
            if type(item) is MissingComponent
        )
        for power, sigma_power in enumerate(powers):
            name = _gram_name(power, left, right)
            source = tuple(
                dict.fromkeys((left.value, "sigma_stf5", right.value))
            )
            if missing:
                out.append(
                    _missing_invariant(
                        name=name,
                        parity=parity,
                        degree=power + 2,
                        source_channels=source,
                        reason=(
                            "missing vector channel(s): "
                            + ", ".join(sorted(set(missing)))
                        ),
                    )
                )
            else:
                left_array = np.asarray(left_value, dtype=float)
                right_array = np.asarray(right_value, dtype=float)
                out.append(
                    _available_invariant(
                        name=name,
                        value=float(left_array @ sigma_power @ right_array),
                        parity=parity,
                        degree=power + 2,
                        source_channels=source,
                    )
                )

    for channel in ORBIT_V3_VECTOR_CHANNELS:
        value = vectors[channel]
        parity = (
            OrbitScalarParity.O3_SCALAR
            if _VECTOR_PARITY[channel] is VectorParity.AXIAL
            else OrbitScalarParity.O3_PSEUDOSCALAR
        )
        name = f"K:{channel.value}"
        if type(value) is MissingComponent:
            out.append(
                _missing_invariant(
                    name=name,
                    parity=parity,
                    degree=6,
                    source_channels=(channel.value, "sigma_stf5"),
                    reason=value.reason,
                )
            )
        else:
            vector = np.asarray(value, dtype=float)
            out.append(
                _available_invariant(
                    name=name,
                    value=float(
                        np.linalg.det(
                            np.column_stack(
                                (vector, sigma @ vector, sigma2 @ vector)
                            )
                        )
                    ),
                    parity=parity,
                    degree=6,
                    source_channels=(channel.value, "sigma_stf5"),
                )
            )

    for channels in itertools.combinations(ORBIT_V3_VECTOR_CHANNELS, 3):
        missing_channels = tuple(
            channel.value
            for channel in channels
            if type(vectors[channel]) is MissingComponent
        )
        axial_count = sum(
            _VECTOR_PARITY[channel] is VectorParity.AXIAL
            for channel in channels
        )
        parity = (
            OrbitScalarParity.O3_SCALAR
            if (1 + axial_count) % 2 == 0
            else OrbitScalarParity.O3_PSEUDOSCALAR
        )
        name = "E:" + ":".join(channel.value for channel in channels)
        source = tuple(channel.value for channel in channels)
        if missing_channels:
            out.append(
                _missing_invariant(
                    name=name,
                    parity=parity,
                    degree=3,
                    source_channels=source,
                    reason=(
                        "missing vector channel(s): "
                        + ", ".join(missing_channels)
                    ),
                )
            )
        else:
            columns = tuple(
                np.asarray(vectors[channel], dtype=float)
                for channel in channels
            )
            out.append(
                _available_invariant(
                    name=name,
                    value=float(np.linalg.det(np.column_stack(columns))),
                    parity=parity,
                    degree=3,
                    source_channels=source,
                )
            )
    return tuple(out)


def orbit_catalogue_v3(
    state: JointAnisotropyState,
    spec: OrbitCatalogueV3Spec,
) -> OrbitCatalogueV3Report:
    """Evaluate the parity-typed local atlas on one canonical joint state."""

    checked_state = _checked_state(state)
    checked_spec = _checked_spec(spec)
    sigma = stf5_to_matrix(
        checked_state.congruence_kinematics.sigma_stf5
    )
    vectors = {
        channel: _vector_value(checked_state, channel)
        for channel in ORBIT_V3_VECTOR_CHANNELS
    }
    signature = _signature(checked_state, sigma, vectors)
    signature_by_name = {item.name: item for item in signature}
    chart_pairs = tuple(
        _chart(
            channel,
            vectors[channel],
            sigma,
            checked_spec,
            signature_by_name,
        )
        for channel in ORBIT_V3_VECTOR_CHANNELS
    )
    charts = tuple(item[0] for item in chart_pairs)
    matrices = {
        channel: pair[1]
        for channel, pair in zip(
            ORBIT_V3_VECTOR_CHANNELS,
            chart_pairs,
            strict=True,
        )
    }
    candidates = tuple(
        chart
        for chart in charts
        if chart.status
        is CyclicChartStatus.NUMERICALLY_CYCLIC_CANDIDATE
        and chart.coordinate_status is ChartCoordinateStatus.COMPLETE
    )
    selected = (
        None
        if not candidates
        else max(
            candidates,
            key=lambda item: (
                item.reciprocal_condition or 0.0,
                -ORBIT_V3_VECTOR_CHANNELS.index(item.channel),
            ),
        ).channel
    )
    stratum = _stratum(sigma, checked_spec)
    shear_stabilizer = _shear_stabilizer(
        stratum.status,
        checked_spec.action_group,
    )
    stabilizer = StabilizerReport(
        shear_stabilizer=shear_stabilizer,
        joint_status=(
            JointStabilizerStatus.NUMERICALLY_TRIVIAL_CANDIDATE
            if selected is not None
            else JointStabilizerStatus.RESIDUAL_STABILIZER_UNRESOLVED
        ),
        selected_chart=selected,
        reasons=(
            (
                "a well-conditioned local cyclic chart reduces the residual "
                "stabilizer numerically; no global theorem is claimed"
            )
            if selected is not None
            else (
                "no well-conditioned cyclic chart is available; the joint "
                "residual stabilizer is unresolved"
            ),
        ),
    )
    missing = tuple(
        channel.value
        for channel in ORBIT_V3_VECTOR_CHANNELS
        if type(vectors[channel]) is MissingComponent
    )
    return OrbitCatalogueV3Report(
        spec=checked_spec,
        source_state_id=checked_state.content_id,
        stratum=stratum,
        stabilizer=stabilizer,
        charts=charts,
        chart_overlaps=_overlaps(charts, matrices),
        invariants=signature,
        missing_components=missing,
        transfer_source=checked_state.transfer_source.value,
        _construction_token=_REPORT_TOKEN,
    )


def revalidate_orbit_catalogue_v3(
    report: OrbitCatalogueV3Report,
    state: JointAnisotropyState,
) -> OrbitCatalogueV3Report:
    """Recompute a v3 report and reject stale or mutated fields."""

    if type(report) is not OrbitCatalogueV3Report:
        raise OrbitCatalogueV3Error(
            "report must be an exact OrbitCatalogueV3Report"
        )
    rebuilt = orbit_catalogue_v3(state, report.spec)
    if rebuilt.as_payload() != report.as_payload():
        raise OrbitCatalogueV3Error(
            "orbit v3 report does not match its bound state and spec"
        )
    return rebuilt


def _legacy_beta_value(
    state: JointAnisotropyState,
    channel: LegacyBetaChannel,
) -> tuple[float, ...] | MissingComponent:
    if channel is LegacyBetaChannel.BETA_RO:
        return state.velocity_frames.beta_RO
    if channel is LegacyBetaChannel.BETA_RM:
        return state.velocity_frames.beta_RM
    return state.velocity_frames.beta_MO


def adapt_joint_state_to_orbit_catalogue_v2(
    state: JointAnisotropyState,
    *,
    beta_channel: LegacyBetaChannel | str,
    catalogue: OrbitCatalogueV2Spec,
) -> LegacyV2AdapterReport:
    """Replay v2 only after an explicit beta-channel choice."""

    checked = _checked_state(state)
    channel = _enum(
        beta_channel,
        LegacyBetaChannel,
        "beta_channel",
    )
    if type(catalogue) is not OrbitCatalogueV2Spec:
        raise TypeError("catalogue must be an exact OrbitCatalogueV2Spec")
    beta = _legacy_beta_value(checked, channel)  # type: ignore[arg-type]
    if type(beta) is MissingComponent:
        return LegacyV2AdapterReport(
            status=LegacyV2AdapterStatus.MISSING_COMPONENT,
            beta_channel=channel,  # type: ignore[arg-type]
            source_state_id=checked.content_id,
            v2_report=None,
            missing_components=(channel.value,),  # type: ignore[union-attr]
            reason=beta.reason,
        )
    departure = DepartureState(
        sigma_ab=checked.congruence_kinematics.sigma_stf5,
        omega_a=checked.congruence_kinematics.omega_axial3,
        beta_a=beta,
        delta_omega_k=checked.geometry_state.delta_omega_k,
        frame=checked.frame,
        congruence=checked.congruence,
        epoch_window=checked.epoch_window,
        averaging_scale=checked.averaging_scale,
        basis=STF5_CARTESIAN_BASIS,
        units=DEPARTURE_O3_UNITS,
        parity=DEPARTURE_O3_PARITY,
        perturbative_order=checked.perturbative_order,
    )
    return LegacyV2AdapterReport(
        status=LegacyV2AdapterStatus.ADAPTED,
        beta_channel=channel,  # type: ignore[arg-type]
        source_state_id=checked.content_id,
        v2_report=orbit_catalogue_v2(departure, catalogue),
        missing_components=(),
        reason=None,
    )


__all__ = [
    "CatalogueProofStatus",
    "ChartCoordinateStatus",
    "ChartOverlapReport",
    "ChartOverlapStatus",
    "CyclicChartReport",
    "CyclicChartStatus",
    "InvariantAvailability",
    "InvariantAlgebraicForm",
    "JointStabilizerStatus",
    "LegacyBetaChannel",
    "LegacyV2AdapterReport",
    "LegacyV2AdapterStatus",
    "ORBIT_V3_ALLOWED_USE",
    "ORBIT_V3_CLAIM_CEILING",
    "ORBIT_V3_DEGREE_COMPLETENESS_STATUS",
    "ORBIT_V3_FORBIDDEN_USE",
    "ORBIT_V3_GENERIC_SEPARATION_STATUS",
    "ORBIT_V3_GLOBAL_CHART_COMPLETENESS_STATUS",
    "ORBIT_V3_REPRESENTATION",
    "ORBIT_V3_VECTOR_CHANNELS",
    "OrbitActionGroup",
    "OrbitCatalogueV3Error",
    "OrbitCatalogueV3Report",
    "OrbitCatalogueV3Spec",
    "OrbitScalarParity",
    "OrbitStratumReport",
    "OrbitVectorChannel",
    "ShearOrbitStratum",
    "ShearStabilizer",
    "StabilizerReport",
    "TypedOrbitInvariant",
    "adapt_joint_state_to_orbit_catalogue_v2",
    "apply_orbit_group_action",
    "build_orbit_catalogue_v3_spec",
    "orbit_catalogue_v3",
    "revalidate_orbit_catalogue_v3",
]
